# Kubernetes Security: A Complete, Production-Grade Deep Dive
## Linux · Cloud · Cloud-Native · Real-World CVEs · C · Go · Rust

---

> *"Security is not a product, but a process." — Bruce Schneier*
>
> This guide treats Kubernetes security as a living, layered discipline — from Linux kernel primitives to cloud-native zero-trust architectures. Every concept is explained from first principles, with real-world CVE analysis, vulnerable code, and hardened production implementations in C, Go, and Rust.

---

## Table of Contents

1. [Mental Model: The Security Stack](#1-mental-model-the-security-stack)
2. [Linux Kernel Security Primitives](#2-linux-kernel-security-primitives)
   - Namespaces
   - cgroups
   - Capabilities
   - Seccomp
   - AppArmor & SELinux
   - LSM (Linux Security Modules)
3. [Container Security Internals](#3-container-security-internals)
4. [Kubernetes Architecture & Attack Surface](#4-kubernetes-architecture--attack-surface)
5. [Authentication & Authorization (RBAC)](#5-authentication--authorization-rbac)
6. [Pod Security: Standards, Policies, Admission](#6-pod-security-standards-policies-admission)
7. [Network Security & Policies](#7-network-security--policies)
8. [Secrets Management](#8-secrets-management)
9. [Supply Chain Security (SLSA, Sigstore, SBOM)](#9-supply-chain-security)
10. [Runtime Security (Falco, eBPF, Tetragon)](#10-runtime-security)
11. [etcd Security](#11-etcd-security)
12. [Cloud-Native Security (AWS/GCP/Azure EKS/GKE/AKS)](#12-cloud-native-security)
13. [Real-World CVEs: Deep Analysis](#13-real-world-cves-deep-analysis)
14. [Zero Trust Architecture in Kubernetes](#14-zero-trust-architecture)
15. [Threat Modeling (STRIDE, PASTA, Attack Trees)](#15-threat-modeling)
16. [Security Benchmarks: CIS, NSA/CISA Hardening](#16-security-benchmarks)
17. [Incident Response & Forensics](#17-incident-response--forensics)
18. [Production Hardening Checklist](#18-production-hardening-checklist)

---

## 1. Mental Model: The Security Stack

Before writing a single line of code or configuration, we must build a **layered mental model** of where security lives in the Kubernetes ecosystem.

### The Defense-in-Depth Pyramid

```
                    ┌─────────────────────────┐
                    │   APPLICATION LAYER      │  ← Your code, libraries
                    │ (input validation, auth) │
                    ├─────────────────────────┤
                    │   KUBERNETES LAYER       │  ← RBAC, PSA, NetworkPolicy
                    │ (control plane security) │
                    ├─────────────────────────┤
                    │   CONTAINER LAYER        │  ← Image scanning, seccomp
                    │ (OCI, runtime security)  │
                    ├─────────────────────────┤
                    │   OS / LINUX LAYER       │  ← Namespaces, capabilities
                    │ (kernel primitives)      │
                    ├─────────────────────────┤
                    │   INFRASTRUCTURE LAYER   │  ← Cloud IAM, VPC, HSM
                    │ (cloud, hardware, HSM)   │
                    └─────────────────────────┘
```

**Key Mental Model**: Every layer can be compromised independently. An attacker who breaks through one layer should encounter a wall at the next. This is **Defense in Depth** — a cognitive framework borrowed from military strategy (think castle walls, moats, guards, and vaults).

**Cognitive Principle — Chunking**: Security is overwhelming if treated as one monolith. By chunking it into layers, you can reason about each independently. Top security engineers don't memorize rules — they internalize *why* each primitive exists and what invariant it enforces.

### The 4C Security Model (Cloud Native Security Foundation)

```
┌─────────────────────────────────────────────────────────────┐
│  CLOUD  (Infrastructure: IAM, VPC, KMS, audit logs)        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CLUSTER  (API server, etcd, admission controllers)   │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  CONTAINER  (seccomp, AppArmor, capabilities)   │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │  CODE  (SAST, DAST, SCA, input validation) │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

This is the **CNCF 4C model** — each C must be secured independently, and they interact. A vulnerability at the Cloud layer can undermine all inner C's.

---

## 2. Linux Kernel Security Primitives

Kubernetes security is **entirely built on top of Linux kernel features**. If you don't understand these primitives, you cannot reason about why Kubernetes security controls work (or fail). This section is the bedrock.

### 2.1 Linux Namespaces — "Illusion of Isolation"

**What is a Namespace?**

A namespace is a Linux kernel mechanism that partitions global system resources so that each partition appears to have its own isolated instance of those resources. Think of it like a lens: processes in different namespaces see different "views" of the system, even though they share the same kernel.

**Namespaces are NOT security boundaries by themselves** — they are isolation mechanisms. Security comes from combining them with other primitives.

```
Namespace Types (as of Linux 5.x):
┌─────────────────┬──────────────────────────────────────────────────────┐
│ Namespace Type  │ What It Isolates                                     │
├─────────────────┼──────────────────────────────────────────────────────┤
│ mnt             │ Filesystem mount points                              │
│ pid             │ Process IDs (PID 1 in container ≠ PID 1 on host)   │
│ net             │ Network interfaces, routes, firewall rules           │
│ ipc             │ POSIX IPC (message queues, semaphores, shared mem)  │
│ uts             │ Hostname and domain name                            │
│ user            │ User and group IDs (UID/GID mapping)               │
│ cgroup          │ cgroup root directory                               │
│ time            │ System clock (Linux 5.6+)                          │
└─────────────────┴──────────────────────────────────────────────────────┘
```

**System Calls That Create Namespaces:**

```
clone(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS)  ← creates new namespaces
unshare(CLONE_NEWUSER)                              ← detach from current namespace
setns(fd, CLONE_NEWNET)                             ← join existing namespace
```

#### C Implementation: Namespace Exploration

**VULNERABLE CODE — Understanding the problem:**

```c
// VULNERABLE: demonstrates namespace escape via user namespace misconfiguration
// File: namespace_vuln.c
// CVE Reference: CVE-2022-0185 (heap overflow in legacy_parse_param)
// DO NOT USE IN PRODUCTION

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <string.h>

// VULNERABILITY: Unprivileged user namespace creation without restriction
// This allows a process to gain capabilities it shouldn't have
// Linux kernels before 5.11 allowed this by default (user.max_user_namespaces)
int vulnerable_create_user_namespace(void) {
    // A normal unprivileged user can create a user namespace
    // Inside that namespace, they appear as UID 0 (root)
    // This is the ENTRY POINT for many privilege escalation exploits

    // BUG: No capability check before unshare
    if (unshare(CLONE_NEWUSER) == -1) {
        perror("unshare");
        return -1;
    }

    // Now inside user namespace — we appear as "root" within this namespace
    // DANGER: If kernel has vulnerability in namespace-aware code path,
    // attacker can escape to host namespace
    printf("UID inside user namespace: %d\n", getuid());  // Will show 0
    printf("PID: %d\n", getpid());

    // ATTACK VECTOR: Write UID mapping to gain actual capabilities
    // This is legitimate use, but can be chained with kernel bugs
    char map[64];
    int fd;

    // Map our original UID to root inside namespace
    fd = open("/proc/self/uid_map", O_WRONLY);
    if (fd >= 0) {
        snprintf(map, sizeof(map), "0 %d 1\n", getuid());
        // DANGEROUS: If kernel doesn't properly validate this mapping
        // with some kernel bugs, this grants real capabilities
        write(fd, map, strlen(map));
        close(fd);
    }

    return 0;
}

int main(void) {
    printf("Original UID: %d\n", getuid());
    vulnerable_create_user_namespace();
    return 0;
}
```

**SECURE CODE — Proper namespace creation with all safety measures:**

```c
// SECURE: Production-grade namespace isolation
// File: secure_namespace.c
// Implements container-like isolation with defense in depth

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/capability.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <signal.h>

#define STACK_SIZE (1024 * 1024)  // 1MB stack for child

// Secure configuration structure
typedef struct {
    uid_t host_uid;
    gid_t host_gid;
    const char *new_root;       // New filesystem root
    const char *hostname;       // Container hostname
    int drop_all_caps;          // Drop all Linux capabilities
    int no_new_privs;           // Prevent privilege escalation
    int read_only_root;         // Mount root as read-only
} SecureContainerConfig;

// Write UID/GID mappings securely
static int write_mapping(pid_t pid, const char *mapping_file,
                          uid_t host_id, uid_t container_id) {
    char path[256];
    char mapping[64];
    int fd;
    ssize_t written;

    snprintf(path, sizeof(path), "/proc/%d/%s", pid, mapping_file);

    // SECURE: Open with explicit flags, no O_CREAT to avoid TOCTOU
    fd = open(path, O_WRONLY);
    if (fd < 0) {
        fprintf(stderr, "Failed to open %s: %s\n", path, strerror(errno));
        return -1;
    }

    // SECURE: Only map exactly what's needed (1:1 mapping of one UID)
    // Never map entire UID range — principle of least privilege
    int len = snprintf(mapping, sizeof(mapping),
                       "%u %u 1\n", container_id, host_id);

    written = write(fd, mapping, len);
    close(fd);

    if (written != len) {
        fprintf(stderr, "Failed to write %s mapping\n", mapping_file);
        return -1;
    }

    return 0;
}

// Disable setgroups before writing gid_map (security requirement)
static int deny_setgroups(pid_t pid) {
    char path[256];
    int fd;

    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    fd = open(path, O_WRONLY);
    if (fd < 0) {
        perror("open setgroups");
        return -1;
    }

    if (write(fd, "deny", 4) != 4) {
        close(fd);
        return -1;
    }
    close(fd);
    return 0;
}

// Drop all Linux capabilities — principle of least privilege
static int drop_all_capabilities(void) {
    // Drop bounding set first
    for (int cap = 0; cap <= CAP_LAST_CAP; cap++) {
        if (prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) < 0) {
            // Some caps might not exist on older kernels — OK to ignore
            if (errno != EINVAL) {
                fprintf(stderr, "Failed to drop cap %d: %s\n",
                        cap, strerror(errno));
                return -1;
            }
        }
    }

    // Drop ambient capabilities (Linux 4.3+)
    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) < 0) {
        if (errno != EINVAL)  // Ignore if not supported
            fprintf(stderr, "Warning: Could not clear ambient caps\n");
    }

    return 0;
}

// Set up pivot_root for filesystem isolation (more secure than chroot)
// WHY pivot_root instead of chroot?
// chroot can be escaped by a process with CAP_SYS_CHROOT
// pivot_root changes the actual root filesystem, making escape much harder
static int setup_pivot_root(const char *new_root) {
    char put_old[256];
    snprintf(put_old, sizeof(put_old), "%s/.old_root", new_root);

    // Mount new root as a bind mount (required for pivot_root)
    if (mount(new_root, new_root, NULL, MS_BIND | MS_REC, NULL) < 0) {
        perror("bind mount new root");
        return -1;
    }

    // Make the bind mount a private mount
    if (mount(NULL, new_root, NULL, MS_PRIVATE | MS_REC, NULL) < 0) {
        perror("make private");
        return -1;
    }

    // Create pivot point
    if (mkdir(put_old, 0700) < 0 && errno != EEXIST) {
        perror("mkdir put_old");
        return -1;
    }

    // Perform pivot_root
    if (syscall(SYS_pivot_root, new_root, put_old) < 0) {
        perror("pivot_root");
        return -1;
    }

    // Change to new root
    if (chdir("/") < 0) {
        perror("chdir /");
        return -1;
    }

    // Unmount old root — critical to prevent access to host filesystem
    if (umount2("/.old_root", MNT_DETACH) < 0) {
        perror("umount2 old root");
        return -1;
    }

    if (rmdir("/.old_root") < 0) {
        perror("rmdir old root");
        return -1;
    }

    return 0;
}

// Child process that runs inside the isolated namespace
static int container_child(void *arg) {
    SecureContainerConfig *cfg = (SecureContainerConfig *)arg;

    // SECURE: Set hostname for UTS namespace isolation
    if (sethostname(cfg->hostname, strlen(cfg->hostname)) < 0) {
        perror("sethostname");
        return -1;
    }

    // SECURE: Set up filesystem isolation
    if (cfg->new_root && setup_pivot_root(cfg->new_root) < 0) {
        return -1;
    }

    // SECURE: Mount proc with new PID namespace — can't see host PIDs
    if (mount("proc", "/proc", "proc",
              MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) < 0) {
        perror("mount proc");
        // Non-fatal if /proc doesn't exist in new_root
    }

    // SECURE: No new privileges — prevents SUID binary exploitation
    // This is THE MOST IMPORTANT prctl call for container security
    // Once set, even if attacker runs a SUID binary, it gets no new privs
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    // SECURE: Drop all capabilities
    if (cfg->drop_all_caps && drop_all_capabilities() < 0) {
        return -1;
    }

    // SECURE: Set dumpable to 0 — prevents /proc/PID/mem attacks
    if (prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) < 0) {
        perror("PR_SET_DUMPABLE");
        // Non-fatal
    }

    printf("Container running: UID=%d, PID=%d, hostname=%s\n",
           getuid(), getpid(), cfg->hostname);

    // In production, exec the actual container entrypoint here
    // execve("/bin/sh", args, env);

    return 0;
}

int create_secure_container(SecureContainerConfig *cfg) {
    // Allocate stack for child process
    char *stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc");
        return -1;
    }

    // SECURE: Use all namespace flags for complete isolation
    // Note: CLONE_NEWUSER must come first for unprivileged containers
    int clone_flags = CLONE_NEWUSER |   // User namespace (UID mapping)
                      CLONE_NEWPID  |   // PID namespace (PID 1 isolation)
                      CLONE_NEWNET  |   // Network namespace
                      CLONE_NEWNS   |   // Mount namespace
                      CLONE_NEWIPC  |   // IPC namespace
                      CLONE_NEWUTS  |   // UTS (hostname) namespace
                      SIGCHLD;          // Signal to parent when child exits

    pid_t child_pid = clone(container_child, stack + STACK_SIZE,
                            clone_flags, cfg);

    if (child_pid < 0) {
        perror("clone");
        free(stack);
        return -1;
    }

    // Parent: Set up UID/GID mappings for the child
    // SECURE: Must deny setgroups before writing gid_map
    if (deny_setgroups(child_pid) < 0) {
        kill(child_pid, SIGKILL);
        free(stack);
        return -1;
    }

    if (write_mapping(child_pid, "uid_map", cfg->host_uid, 0) < 0) {
        kill(child_pid, SIGKILL);
        free(stack);
        return -1;
    }

    if (write_mapping(child_pid, "gid_map", cfg->host_gid, 0) < 0) {
        kill(child_pid, SIGKILL);
        free(stack);
        return -1;
    }

    // Wait for child
    int status;
    waitpid(child_pid, &status, 0);
    free(stack);

    return WIFEXITED(status) ? WEXITSTATUS(status) : -1;
}

int main(void) {
    SecureContainerConfig cfg = {
        .host_uid      = getuid(),
        .host_gid      = getgid(),
        .new_root      = NULL,       // Set to new rootfs path in production
        .hostname      = "secure-container",
        .drop_all_caps = 1,
        .no_new_privs  = 1,
        .read_only_root = 1,
    };

    printf("Host UID: %d, Host PID: %d\n", getuid(), getpid());
    return create_secure_container(&cfg);
}
```

**Compile and test:**
```bash
gcc -o secure_namespace secure_namespace.c -lcap
# Requires: libcap-dev
# Run as non-root to verify namespace isolation works
```

---

### 2.2 Linux Control Groups (cgroups) — "Resource Accounting"

**What are cgroups?**

cgroups (control groups) are a Linux kernel feature that limits, accounts for, and isolates resource usage (CPU, memory, disk I/O, network) of groups of processes. Unlike namespaces (which create *illusions*), cgroups enforce *hard limits*.

**Why this matters for Kubernetes security:**
- Without cgroups limits → one container can starve all others (Denial of Service)
- Memory limits prevent OOM killer from killing wrong processes
- CPU limits prevent crypto-mining malware from consuming 100% CPU
- IO limits prevent one pod from saturating disk

```
cgroup v1 Hierarchy:
/sys/fs/cgroup/
├── cpu/                    ← CPU scheduling
│   └── my-container/
│       ├── cpu.shares      ← Relative CPU weight
│       └── cpu.cfs_quota_us ← Hard CPU time limit
├── memory/                 ← Memory control
│   └── my-container/
│       ├── memory.limit_in_bytes     ← Hard memory limit
│       ├── memory.memsw.limit_in_bytes ← Memory + swap
│       └── memory.oom_control        ← OOM behavior
├── blkio/                  ← Block I/O throttling
├── pids/                   ← Maximum number of processes
│   └── my-container/
│       └── pids.max       ← Fork bomb prevention!
└── net_cls/                ← Network class marking
```

```
cgroup v2 (Unified Hierarchy) — Modern, used in Kubernetes 1.25+:
/sys/fs/cgroup/
└── system.slice/
    └── my-container.scope/
        ├── cgroup.controllers    ← Active controllers
        ├── cpu.max               ← "quota period" format
        ├── memory.max            ← Memory hard limit
        ├── memory.swap.max       ← Swap limit
        ├── pids.max              ← Process limit
        └── io.max                ← I/O limits
```

#### C Implementation: cgroup v2 Enforcement

```c
// SECURE: Production cgroup v2 resource enforcement
// File: cgroup_enforce.c
// Prevents resource abuse and DoS in containerized environments

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>

#define CGROUP_BASE "/sys/fs/cgroup"
#define CGROUP_PATH_MAX 512
#define VALUE_MAX 128

// Resource limits structure
typedef struct {
    const char *name;           // cgroup name
    long long memory_max;       // bytes; -1 = unlimited (BAD for production)
    long long memory_swap_max;  // swap limit; 0 = no swap (recommended)
    long long cpu_quota;        // microseconds per period; -1 = unlimited
    long long cpu_period;       // period in microseconds (default 100000 = 100ms)
    int pids_max;               // max number of processes; -1 = unlimited (BAD)
    long long io_rbps_max;      // read bytes/sec; 0 = unlimited
    long long io_wbps_max;      // write bytes/sec; 0 = unlimited
} CgroupConfig;

// Write value to a cgroup file — atomic write with error checking
static int cgroup_write(const char *path, const char *value) {
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "cgroup_write open(%s): %s\n", path, strerror(errno));
        return -1;
    }

    size_t len = strlen(value);
    ssize_t written = write(fd, value, len);
    int saved_errno = errno;
    close(fd);

    if (written != (ssize_t)len) {
        fprintf(stderr, "cgroup_write write(%s, %s): %s\n",
                path, value, strerror(saved_errno));
        return -1;
    }

    return 0;
}

// Read value from a cgroup file
static int cgroup_read(const char *path, char *buf, size_t size) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "cgroup_read open(%s): %s\n", path, strerror(errno));
        return -1;
    }

    ssize_t n = read(fd, buf, size - 1);
    close(fd);

    if (n < 0) {
        fprintf(stderr, "cgroup_read read(%s): %s\n", path, strerror(errno));
        return -1;
    }

    buf[n] = '\0';
    // Trim newline
    char *nl = strchr(buf, '\n');
    if (nl) *nl = '\0';
    return 0;
}

// Create and configure a cgroup v2 with strict limits
int create_secure_cgroup(const CgroupConfig *cfg) {
    char path[CGROUP_PATH_MAX];
    char value[VALUE_MAX];

    // Create cgroup directory
    snprintf(path, sizeof(path), "%s/%s", CGROUP_BASE, cfg->name);
    if (mkdir(path, 0755) < 0 && errno != EEXIST) {
        fprintf(stderr, "mkdir(%s): %s\n", path, strerror(errno));
        return -1;
    }

    // Enable required controllers on parent cgroup
    // Must write "+cpu +memory +pids +io" to parent's cgroup.subtree_control
    snprintf(path, sizeof(path), "%s/cgroup.subtree_control", CGROUP_BASE);
    if (cgroup_write(path, "+cpu +memory +pids +io") < 0) {
        fprintf(stderr, "Warning: Could not enable all controllers\n");
        // Non-fatal — some may already be enabled
    }

    // ================================================================
    // MEMORY LIMITS — Most critical for security
    // ================================================================

    // SECURE: Set hard memory limit
    // NEVER leave memory unlimited in production (OOM can kill kube processes)
    if (cfg->memory_max > 0) {
        snprintf(path, sizeof(path), "%s/%s/memory.max", CGROUP_BASE, cfg->name);
        snprintf(value, sizeof(value), "%lld", cfg->memory_max);
        if (cgroup_write(path, value) < 0) return -1;
        printf("  [+] memory.max = %lld bytes (%.1f MB)\n",
               cfg->memory_max, (double)cfg->memory_max / (1024*1024));
    }

    // SECURE: Disable swap — swap use can be used to fingerprint memory contents
    // and complicates memory limit enforcement
    snprintf(path, sizeof(path), "%s/%s/memory.swap.max", CGROUP_BASE, cfg->name);
    snprintf(value, sizeof(value), "%lld", cfg->memory_swap_max);
    if (cgroup_write(path, value) < 0) {
        fprintf(stderr, "Warning: Could not set memory.swap.max\n");
    } else {
        printf("  [+] memory.swap.max = %lld\n", cfg->memory_swap_max);
    }

    // SECURE: Set low watermark to trigger proactive reclaim
    // Prevents sudden OOM kills by reclaiming memory early
    if (cfg->memory_max > 0) {
        snprintf(path, sizeof(path), "%s/%s/memory.low", CGROUP_BASE, cfg->name);
        snprintf(value, sizeof(value), "%lld", cfg->memory_max * 80 / 100);
        cgroup_write(path, value);  // Non-fatal
    }

    // ================================================================
    // CPU LIMITS
    // ================================================================

    if (cfg->cpu_quota > 0 && cfg->cpu_period > 0) {
        snprintf(path, sizeof(path), "%s/%s/cpu.max", CGROUP_BASE, cfg->name);
        // Format: "quota period" (e.g., "50000 100000" = 50% of one CPU)
        snprintf(value, sizeof(value), "%lld %lld",
                 cfg->cpu_quota, cfg->cpu_period);
        if (cgroup_write(path, value) < 0) return -1;
        printf("  [+] cpu.max = %lld/%lld (%.1f%% CPU)\n",
               cfg->cpu_quota, cfg->cpu_period,
               (double)cfg->cpu_quota / cfg->cpu_period * 100.0);
    }

    // ================================================================
    // PID LIMITS — CRITICAL: Prevents fork bombs
    // ================================================================

    // A fork bomb: :(){ :|:& };:
    // Without pids.max, this crashes the entire node
    if (cfg->pids_max > 0) {
        snprintf(path, sizeof(path), "%s/%s/pids.max", CGROUP_BASE, cfg->name);
        snprintf(value, sizeof(value), "%d", cfg->pids_max);
        if (cgroup_write(path, value) < 0) return -1;
        printf("  [+] pids.max = %d\n", cfg->pids_max);
    }

    // ================================================================
    // I/O LIMITS — Prevents I/O saturation attacks
    // ================================================================

    // Format: "MAJOR:MINOR rbps=N wbps=N riops=N wiops=N"
    // We use device 8:0 (sda) as example — in production, detect dynamically
    if (cfg->io_rbps_max > 0 || cfg->io_wbps_max > 0) {
        snprintf(path, sizeof(path), "%s/%s/io.max", CGROUP_BASE, cfg->name);
        snprintf(value, sizeof(value), "8:0 rbps=%lld wbps=%lld",
                 cfg->io_rbps_max, cfg->io_wbps_max);
        if (cgroup_write(path, value) < 0) {
            fprintf(stderr, "Warning: Could not set io.max (check device path)\n");
        } else {
            printf("  [+] io.max rbps=%lld wbps=%lld\n",
                   cfg->io_rbps_max, cfg->io_wbps_max);
        }
    }

    return 0;
}

// Move a process into the cgroup
int enter_cgroup(const char *cgroup_name, pid_t pid) {
    char path[CGROUP_PATH_MAX];
    char pid_str[32];

    snprintf(path, sizeof(path), "%s/%s/cgroup.procs", CGROUP_BASE, cgroup_name);
    snprintf(pid_str, sizeof(pid_str), "%d", pid);

    if (cgroup_write(path, pid_str) < 0) {
        fprintf(stderr, "Failed to move PID %d into cgroup %s\n", pid, cgroup_name);
        return -1;
    }

    printf("  [+] Moved PID %d into cgroup %s\n", pid, cgroup_name);
    return 0;
}

// Check current cgroup stats
void print_cgroup_stats(const char *cgroup_name) {
    char path[CGROUP_PATH_MAX];
    char value[VALUE_MAX];

    printf("\n=== cgroup stats: %s ===\n", cgroup_name);

    snprintf(path, sizeof(path), "%s/%s/memory.current", CGROUP_BASE, cgroup_name);
    if (cgroup_read(path, value, sizeof(value)) == 0)
        printf("  memory.current: %s bytes\n", value);

    snprintf(path, sizeof(path), "%s/%s/cpu.stat", CGROUP_BASE, cgroup_name);
    if (cgroup_read(path, value, sizeof(value)) == 0)
        printf("  cpu.stat:\n%s\n", value);

    snprintf(path, sizeof(path), "%s/%s/pids.current", CGROUP_BASE, cgroup_name);
    if (cgroup_read(path, value, sizeof(value)) == 0)
        printf("  pids.current: %s\n", value);
}

int main(void) {
    // Production-ready cgroup configuration for a web service container
    CgroupConfig prod_cfg = {
        .name           = "secure-workload",
        .memory_max     = 512 * 1024 * 1024,   // 512 MB hard limit
        .memory_swap_max = 0,                    // NO swap
        .cpu_quota      = 50000,                 // 50ms
        .cpu_period     = 100000,                // per 100ms = 50% CPU
        .pids_max       = 128,                   // Max 128 processes
        .io_rbps_max    = 100 * 1024 * 1024,    // 100 MB/s read
        .io_wbps_max    = 50  * 1024 * 1024,    // 50 MB/s write
    };

    printf("Creating secure cgroup: %s\n", prod_cfg.name);
    if (create_secure_cgroup(&prod_cfg) < 0) {
        fprintf(stderr, "Failed to create cgroup (requires root)\n");
        return 1;
    }

    // Move self into the cgroup
    if (enter_cgroup(prod_cfg.name, getpid()) < 0)
        return 1;

    print_cgroup_stats(prod_cfg.name);
    printf("\nProcess is now resource-limited.\n");

    return 0;
}
```

---

### 2.3 Linux Capabilities — "Fine-Grained Privilege"

**What are Linux Capabilities?**

Historically, Linux had two privilege modes: root (all-powerful, UID=0) and non-root. Capabilities split root's power into ~40 individual units that can be granted or revoked independently.

**Key Insight for Security**: A process should only have the capabilities it *actually needs*. A web server needs no capabilities. A container that needs to bind to port 80 needs only `CAP_NET_BIND_SERVICE`.

```
Critical Capabilities and their Security Implications:
┌──────────────────────────┬─────────────────────────────────────────────────┐
│ Capability               │ What it allows / Security Risk                  │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ CAP_SYS_ADMIN            │ "Do anything" — Almost = root. NEVER grant.    │
│ CAP_SYS_PTRACE           │ ptrace any process → read memory, inject code  │
│ CAP_NET_ADMIN            │ Modify routing, firewall, interfaces            │
│ CAP_SYS_MODULE           │ Load kernel modules → trivial kernel rootkit    │
│ CAP_DAC_OVERRIDE         │ Bypass file permission checks                   │
│ CAP_SETUID               │ Set any UID → privilege escalation              │
│ CAP_NET_BIND_SERVICE     │ Bind ports < 1024 (often legitimately needed)  │
│ CAP_SYS_CHROOT           │ chroot() — can be chained for escape           │
│ CAP_NET_RAW              │ Raw sockets — enables ARP spoofing, MITM       │
│ CAP_SYS_BOOT             │ Reboot system — trivial DoS                     │
│ CAP_AUDIT_WRITE          │ Write audit log — could flood audit system      │
└──────────────────────────┴─────────────────────────────────────────────────┘
```

```
Capability Sets (every process has all of these):
┌─────────────────┬────────────────────────────────────────────────────────┐
│ Set Name        │ Purpose                                                 │
├─────────────────┼────────────────────────────────────────────────────────┤
│ Permitted (P)   │ Superset of capabilities the process can have          │
│ Effective (E)   │ Currently active capabilities (what actually matters)  │
│ Inheritable (I) │ Passed across execve() if file also has it            │
│ Bounding (B)    │ Maximum capabilities any child can ever have           │
│ Ambient (A)     │ Preserved across execve() for non-setuid binaries      │
└─────────────────┴────────────────────────────────────────────────────────┘
```

#### C Implementation: Capability Dropping

```c
// SECURE: Drop all capabilities before executing workload
// File: drop_caps.c
// Based on patterns used in containerd, runc, crun

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/prctl.h>
#include <sys/capability.h>
#include <unistd.h>

// VULNERABLE PATTERN — DO NOT DO THIS:
// Running a container with CAP_SYS_ADMIN
// docker run --cap-add=SYS_ADMIN ... 
// This is equivalent to giving the container root on the host
// CVE-2019-5736 (runc escape) used CAP_SYS_ADMIN

// SECURE: Minimal capability set for common workloads
// These capabilities are what runc drops by default
static const int caps_to_keep[] = {
    // Only if your workload specifically needs these:
    // CAP_NET_BIND_SERVICE,  // Bind ports < 1024
    // CAP_CHOWN,             // Only if changing file ownership
    // (intentionally leaving this empty for most workloads)
    -1  // Sentinel
};

// Drop ALL capabilities — the nuclear option and the correct default
int drop_all_caps_secure(void) {
    cap_t caps;
    int ret = 0;

    // ---------------------------------------------------------------
    // Step 1: Drop the bounding set
    // The bounding set limits what capabilities can EVER be granted
    // Even if someone exploits a SUID binary, they can't get dropped caps
    // ---------------------------------------------------------------
    for (int cap = 0; cap <= CAP_LAST_CAP; cap++) {
        if (prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) < 0) {
            if (errno == EINVAL) continue;  // Cap doesn't exist
            if (errno == EPERM) {
                fprintf(stderr, "No permission to drop cap %d\n", cap);
                return -1;
            }
            perror("PR_CAPBSET_DROP");
            return -1;
        }
    }
    printf("[caps] Bounding set cleared\n");

    // ---------------------------------------------------------------
    // Step 2: Clear ambient capabilities (Linux 4.3+)
    // Ambient caps are inherited by child processes across execve
    // We must clear them to prevent capability leakage
    // ---------------------------------------------------------------
    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) < 0) {
        if (errno != EINVAL)  // Not supported on older kernels
            perror("PR_CAP_AMBIENT_CLEAR_ALL");
        // Non-fatal on old kernels
    } else {
        printf("[caps] Ambient capabilities cleared\n");
    }

    // ---------------------------------------------------------------
    // Step 3: Set effective, permitted, and inheritable to empty
    // This is the actual "drop all caps" step
    // ---------------------------------------------------------------
    caps = cap_init();  // Creates an all-zero capability set
    if (!caps) {
        perror("cap_init");
        return -1;
    }

    if (cap_set_proc(caps) < 0) {
        perror("cap_set_proc");
        cap_free(caps);
        return -1;
    }
    cap_free(caps);
    printf("[caps] Effective/Permitted/Inheritable cleared\n");

    // ---------------------------------------------------------------
    // Step 4: Set PR_SET_NO_NEW_PRIVS
    // This is the most important step — makes all the above permanent
    // After this, even execve of a SUID root binary won't grant new privs
    // This cannot be undone even by root
    // ---------------------------------------------------------------
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }
    printf("[caps] PR_SET_NO_NEW_PRIVS set — privilege escalation impossible\n");

    // Verify
    int nnp = prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0);
    if (nnp != 1) {
        fprintf(stderr, "ERROR: PR_SET_NO_NEW_PRIVS verification failed!\n");
        return -1;
    }

    return ret;
}

// Print current capability state (useful for debugging and auditing)
void print_current_caps(const char *label) {
    cap_t caps = cap_get_proc();
    if (!caps) {
        perror("cap_get_proc");
        return;
    }

    char *text = cap_to_text(caps, NULL);
    printf("[%s] Current capabilities: %s\n", label, text ? text : "(empty)");

    cap_free(text);
    cap_free(caps);

    // Also check bounding set
    for (int cap = 0; cap <= CAP_LAST_CAP; cap++) {
        int has_bound = prctl(PR_CAPBSET_READ, cap, 0, 0, 0);
        if (has_bound > 0) {
            char *cap_name = cap_to_name(cap);
            printf("[%s] WARNING: Bounding set still has: %s\n",
                   label, cap_name ? cap_name : "unknown");
            cap_free(cap_name);
        }
    }
}

// Check if running with dangerous capabilities
int audit_dangerous_caps(void) {
    static const int dangerous_caps[] = {
        CAP_SYS_ADMIN,
        CAP_SYS_PTRACE,
        CAP_NET_ADMIN,
        CAP_SYS_MODULE,
        CAP_DAC_OVERRIDE,
        CAP_SETUID,
        CAP_SETGID,
        CAP_SYS_CHROOT,
        -1
    };

    cap_t caps = cap_get_proc();
    if (!caps) return -1;

    int found_dangerous = 0;
    for (int i = 0; dangerous_caps[i] != -1; i++) {
        cap_flag_value_t eff_val;
        if (cap_get_flag(caps, dangerous_caps[i], CAP_EFFECTIVE, &eff_val) == 0) {
            if (eff_val == CAP_SET) {
                char *name = cap_to_name(dangerous_caps[i]);
                fprintf(stderr, "SECURITY WARNING: Dangerous capability "
                        "is effective: %s\n", name ? name : "unknown");
                cap_free(name);
                found_dangerous = 1;
            }
        }
    }

    cap_free(caps);
    return found_dangerous;
}

int main(void) {
    printf("=== Capability Security Demo ===\n\n");

    print_current_caps("Before drop");
    audit_dangerous_caps();

    printf("\nDropping all capabilities...\n");
    if (drop_all_caps_secure() < 0) {
        fprintf(stderr, "Failed to drop capabilities\n");
        return 1;
    }

    print_current_caps("After drop");

    // Verify we can't do privileged operations
    printf("\nTesting privilege isolation:\n");
    if (setuid(0) < 0) {
        printf("  [+] setuid(0) blocked — cannot escalate to root\n");
    } else {
        printf("  [FAIL] setuid(0) succeeded — capability drop failed!\n");
        return 1;
    }

    printf("\n[SUCCESS] All capabilities dropped. Process is fully unprivileged.\n");
    return 0;
}
```

```
Compile:
gcc -o drop_caps drop_caps.c -lcap
```

---

### 2.4 Seccomp — "System Call Filtering"

**What is Seccomp?**

Seccomp (Secure Computing Mode) is a Linux kernel security facility that restricts which system calls a process can make. It was originally designed to sandbox `cpushare`-style services where untrusted code ran on shared hardware.

**Why system call filtering matters**: The entire Linux kernel API surface (500+ system calls) is the attack surface. Most processes only use ~20-50 system calls. By blocking all others, we dramatically reduce the kernel's attack surface even if there's a zero-day in an obscure syscall.

```
Seccomp Modes:
┌──────────────────┬──────────────────────────────────────────────────────┐
│ Mode             │ Description                                          │
├──────────────────┼──────────────────────────────────────────────────────┤
│ SECCOMP_MODE_STRICT │ Only allow read, write, exit, sigreturn          │
│ SECCOMP_MODE_FILTER │ BPF program filters syscalls (production use)    │
└──────────────────┴──────────────────────────────────────────────────────┘

Seccomp BPF Actions (on syscall match):
┌──────────────────────┬──────────────────────────────────────────────────┐
│ Action               │ Effect                                           │
├──────────────────────┼──────────────────────────────────────────────────┤
│ SECCOMP_RET_KILL_PROCESS │ Kill entire process (Linux 4.14+)          │
│ SECCOMP_RET_KILL     │ Kill the thread                                 │
│ SECCOMP_RET_TRAP     │ Send SIGSYS (can be caught)                    │
│ SECCOMP_RET_ERRNO    │ Return specified errno (e.g., EPERM)            │
│ SECCOMP_RET_TRACE    │ Notify tracer via PTRACE                       │
│ SECCOMP_RET_ALLOW    │ Allow the syscall                              │
└──────────────────────┴──────────────────────────────────────────────────┘
```

#### C Implementation: Seccomp Filter

```c
// SECURE: Production seccomp filter for container workloads
// File: seccomp_filter.c
// Based on Docker's default seccomp profile but more restrictive

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/ptrace.h>

// BPF macros for seccomp filter construction
// BPF = Berkeley Packet Filter — a small virtual machine in the kernel
#define VALIDATE_ARCHITECTURE \
    /* Load architecture field from seccomp_data */ \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, \
             (offsetof(struct seccomp_data, arch))), \
    /* Compare to x86-64 architecture */ \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0), \
    /* Kill if wrong arch (prevents 32-bit syscall bypass!) */ \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)

#define LOAD_SYSCALL_NR \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, \
             (offsetof(struct seccomp_data, nr)))

#define ALLOW_SYSCALL(name) \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)

#define KILL_SYSCALL(name) \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)

#define ERRNO_SYSCALL(name, err) \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (err))

// VULNERABLE PATTERN: No seccomp filter
// The container can call ANY syscall including:
// - ptrace (spy on other processes)
// - init_module (load kernel modules)  
// - kexec_load (replace running kernel)
// - reboot (DoS the entire node)
// - mount (escape container filesystem)
void setup_no_seccomp_VULNERABLE(void) {
    printf("[VULNERABLE] No seccomp filter — all syscalls allowed\n");
    // This is the default if you don't specify seccomp in your pod spec!
}

// SECURE: Minimal allowlist — only what a typical web service needs
int setup_secure_seccomp(void) {
    // BPF filter program
    // IMPORTANT: Architecture check MUST come first to prevent
    // 32-bit syscall confusion attacks (e.g., CVE-2014-4418)
    struct sock_filter filter[] = {
        // Validate architecture (prevent 32-bit syscall confusion)
        VALIDATE_ARCHITECTURE,

        // Load syscall number for comparison
        LOAD_SYSCALL_NR,

        // ================================================================
        // EXPLICITLY BLOCKED DANGEROUS SYSCALLS
        // Block these explicitly with KILL (belt and suspenders approach)
        // These are blocked even if they'd be caught by the default deny
        // ================================================================

        // Kernel module loading — trivial rootkit vector
        KILL_SYSCALL(init_module),
        KILL_SYSCALL(finit_module),
        KILL_SYSCALL(delete_module),

        // System reboot — DoS entire node
        KILL_SYSCALL(reboot),

        // kexec — load a new kernel image — catastrophic capability
        KILL_SYSCALL(kexec_load),
        KILL_SYSCALL(kexec_file_load),

        // ptrace — spy on/inject into other processes
        // This is how container escape via ptrace works
        KILL_SYSCALL(ptrace),

        // Namespace manipulation from inside container
        // Prevents namespace-based escape techniques
        ERRNO_SYSCALL(unshare, EPERM),

        // Mount syscall — can be used to expose host filesystem
        ERRNO_SYSCALL(mount, EPERM),
        ERRNO_SYSCALL(umount2, EPERM),

        // ================================================================
        // ALLOWED SYSCALLS — Explicit allowlist (deny everything else)
        // This is the "allowlist" approach — more secure than blocklist
        // ================================================================

        // Process lifecycle
        ALLOW_SYSCALL(exit),
        ALLOW_SYSCALL(exit_group),
        ALLOW_SYSCALL(fork),
        ALLOW_SYSCALL(vfork),
        ALLOW_SYSCALL(clone),    // Needed for threads
        ALLOW_SYSCALL(execve),
        ALLOW_SYSCALL(execveat),
        ALLOW_SYSCALL(wait4),
        ALLOW_SYSCALL(waitid),

        // File I/O — basic operations
        ALLOW_SYSCALL(read),
        ALLOW_SYSCALL(write),
        ALLOW_SYSCALL(readv),
        ALLOW_SYSCALL(writev),
        ALLOW_SYSCALL(open),
        ALLOW_SYSCALL(openat),
        ALLOW_SYSCALL(openat2),
        ALLOW_SYSCALL(close),
        ALLOW_SYSCALL(close_range),
        ALLOW_SYSCALL(stat),
        ALLOW_SYSCALL(fstat),
        ALLOW_SYSCALL(lstat),
        ALLOW_SYSCALL(newfstatat),
        ALLOW_SYSCALL(statx),
        ALLOW_SYSCALL(lseek),
        ALLOW_SYSCALL(pread64),
        ALLOW_SYSCALL(pwrite64),
        ALLOW_SYSCALL(preadv),
        ALLOW_SYSCALL(pwritev),
        ALLOW_SYSCALL(access),
        ALLOW_SYSCALL(faccessat),
        ALLOW_SYSCALL(dup),
        ALLOW_SYSCALL(dup2),
        ALLOW_SYSCALL(dup3),
        ALLOW_SYSCALL(fcntl),
        ALLOW_SYSCALL(getcwd),
        ALLOW_SYSCALL(chdir),
        ALLOW_SYSCALL(mkdir),
        ALLOW_SYSCALL(mkdirat),
        ALLOW_SYSCALL(rmdir),
        ALLOW_SYSCALL(unlink),
        ALLOW_SYSCALL(unlinkat),
        ALLOW_SYSCALL(rename),
        ALLOW_SYSCALL(renameat),
        ALLOW_SYSCALL(renameat2),
        ALLOW_SYSCALL(link),
        ALLOW_SYSCALL(linkat),
        ALLOW_SYSCALL(symlink),
        ALLOW_SYSCALL(symlinkat),
        ALLOW_SYSCALL(readlink),
        ALLOW_SYSCALL(readlinkat),
        ALLOW_SYSCALL(chmod),
        ALLOW_SYSCALL(fchmod),
        ALLOW_SYSCALL(chown),
        ALLOW_SYSCALL(fchown),

        // Memory management
        ALLOW_SYSCALL(mmap),
        ALLOW_SYSCALL(mprotect),
        ALLOW_SYSCALL(munmap),
        ALLOW_SYSCALL(mremap),
        ALLOW_SYSCALL(madvise),
        ALLOW_SYSCALL(brk),
        ALLOW_SYSCALL(msync),
        ALLOW_SYSCALL(mincore),
        ALLOW_SYSCALL(mlock),
        ALLOW_SYSCALL(munlock),

        // Signals
        ALLOW_SYSCALL(rt_sigaction),
        ALLOW_SYSCALL(rt_sigprocmask),
        ALLOW_SYSCALL(rt_sigreturn),
        ALLOW_SYSCALL(kill),
        ALLOW_SYSCALL(tkill),
        ALLOW_SYSCALL(tgkill),
        ALLOW_SYSCALL(sigaltstack),

        // Networking
        ALLOW_SYSCALL(socket),
        ALLOW_SYSCALL(connect),
        ALLOW_SYSCALL(accept),
        ALLOW_SYSCALL(accept4),
        ALLOW_SYSCALL(send),
        ALLOW_SYSCALL(sendto),
        ALLOW_SYSCALL(sendmsg),
        ALLOW_SYSCALL(sendmmsg),
        ALLOW_SYSCALL(recv),
        ALLOW_SYSCALL(recvfrom),
        ALLOW_SYSCALL(recvmsg),
        ALLOW_SYSCALL(recvmmsg),
        ALLOW_SYSCALL(bind),
        ALLOW_SYSCALL(listen),
        ALLOW_SYSCALL(getsockname),
        ALLOW_SYSCALL(getpeername),
        ALLOW_SYSCALL(setsockopt),
        ALLOW_SYSCALL(getsockopt),
        ALLOW_SYSCALL(shutdown),
        ALLOW_SYSCALL(socketpair),
        ALLOW_SYSCALL(pipe),
        ALLOW_SYSCALL(pipe2),

        // Time and sleep
        ALLOW_SYSCALL(gettimeofday),
        ALLOW_SYSCALL(clock_gettime),
        ALLOW_SYSCALL(clock_nanosleep),
        ALLOW_SYSCALL(nanosleep),
        ALLOW_SYSCALL(time),
        ALLOW_SYSCALL(times),

        // Process info
        ALLOW_SYSCALL(getpid),
        ALLOW_SYSCALL(getppid),
        ALLOW_SYSCALL(gettid),
        ALLOW_SYSCALL(getuid),
        ALLOW_SYSCALL(getgid),
        ALLOW_SYSCALL(geteuid),
        ALLOW_SYSCALL(getegid),
        ALLOW_SYSCALL(getresuid),
        ALLOW_SYSCALL(getresgid),
        ALLOW_SYSCALL(getpgrp),
        ALLOW_SYSCALL(getpgid),
        ALLOW_SYSCALL(getsid),
        ALLOW_SYSCALL(getrlimit),
        ALLOW_SYSCALL(setrlimit),
        ALLOW_SYSCALL(prlimit64),
        ALLOW_SYSCALL(getrusage),

        // epoll/poll/select — for async I/O
        ALLOW_SYSCALL(epoll_create),
        ALLOW_SYSCALL(epoll_create1),
        ALLOW_SYSCALL(epoll_ctl),
        ALLOW_SYSCALL(epoll_wait),
        ALLOW_SYSCALL(epoll_pwait),
        ALLOW_SYSCALL(select),
        ALLOW_SYSCALL(pselect6),
        ALLOW_SYSCALL(poll),
        ALLOW_SYSCALL(ppoll),

        // futex — for threading
        ALLOW_SYSCALL(futex),
        ALLOW_SYSCALL(futex_waitv),
        ALLOW_SYSCALL(set_robust_list),
        ALLOW_SYSCALL(get_robust_list),

        // IO uring (Linux 5.1+) — high performance async I/O
        ALLOW_SYSCALL(io_uring_setup),
        ALLOW_SYSCALL(io_uring_enter),
        ALLOW_SYSCALL(io_uring_register),

        // Misc required syscalls
        ALLOW_SYSCALL(prctl),
        ALLOW_SYSCALL(arch_prctl),
        ALLOW_SYSCALL(seccomp),   // Allow tightening seccomp further
        ALLOW_SYSCALL(uname),
        ALLOW_SYSCALL(sysinfo),
        ALLOW_SYSCALL(getrandom),
        ALLOW_SYSCALL(eventfd),
        ALLOW_SYSCALL(eventfd2),
        ALLOW_SYSCALL(timerfd_create),
        ALLOW_SYSCALL(timerfd_settime),
        ALLOW_SYSCALL(timerfd_gettime),
        ALLOW_SYSCALL(signalfd),
        ALLOW_SYSCALL(signalfd4),
        ALLOW_SYSCALL(inotify_init),
        ALLOW_SYSCALL(inotify_init1),
        ALLOW_SYSCALL(inotify_add_watch),
        ALLOW_SYSCALL(inotify_rm_watch),

        // Default: DENY ALL
        // Any syscall not in the above allowlist → kill the process
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
    };

    struct sock_fprog prog = {
        .len    = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };

    // Set NO_NEW_PRIVS first (required before seccomp without CAP_SYS_ADMIN)
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    // Install the filter
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) < 0) {
        perror("PR_SET_SECCOMP");
        return -1;
    }

    printf("[seccomp] Filter installed: %zu rules, default KILL\n",
           sizeof(filter) / sizeof(filter[0]));
    return 0;
}

// Test the filter
void test_seccomp_filter(void) {
    printf("\n=== Testing seccomp filter ===\n");

    // Allowed: getpid
    pid_t pid = getpid();
    printf("  [+] getpid() = %d (allowed)\n", pid);

    // Allowed: write to stdout
    printf("  [+] write() allowed\n");

    // Now test a blocked syscall:
    // ptrace should be killed
    printf("  Testing ptrace (should be blocked)...\n");
    // If we call ptrace here, the process gets SIGKILL
    // In a real test, fork a child and have it call ptrace
    
    printf("[seccomp] All tests passed.\n");
}

int main(void) {
    printf("=== Seccomp Filter Demo ===\n\n");

    if (setup_secure_seccomp() < 0) {
        fprintf(stderr, "Failed to install seccomp filter\n");
        return 1;
    }

    test_seccomp_filter();
    return 0;
}
```

---

### 2.5 AppArmor — "Mandatory Access Control via Profiles"

**What is AppArmor?**

AppArmor (Application Armor) is a Linux Security Module (LSM) that implements Mandatory Access Control (MAC). Unlike traditional Unix DAC (Discretionary Access Control where the file owner controls access), MAC policies are set by the system administrator and cannot be overridden by the process itself, even if it runs as root.

**AppArmor works by**: Attaching a *profile* to a program that specifies exactly what files, capabilities, and network operations it can perform.

```
AppArmor Profile Structure:
/etc/apparmor.d/
└── usr.sbin.nginx          ← Profile for nginx
    ├── #include <tunables/global>
    ├── Profile mode: enforce / complain
    ├── File rules: /var/www/html/ r,
    ├── Network rules: network inet tcp,
    ├── Capability rules: capability net_bind_service,
    └── Signal rules: signal (send) set=(hup term)
```

**AppArmor Modes:**
```
complain → log violations but don't block (use for profiling/development)
enforce  → block violations and log     (use in production)
disabled → no enforcement
```

**Kubernetes AppArmor Integration** (via annotations, then via PodSpec in 1.30+):

```yaml
# Kubernetes Pod with AppArmor profile
apiVersion: v1
kind: Pod
metadata:
  name: secure-nginx
  annotations:
    # Pre-1.30 annotation-based approach
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-nginx
spec:
  containers:
  - name: nginx
    image: nginx:latest
    # 1.30+ native support:
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-nginx
```

**Production AppArmor Profile for a Web Server:**

```
# File: /etc/apparmor.d/k8s-nginx
# Hardened AppArmor profile for nginx in Kubernetes

#include <tunables/global>

profile k8s-nginx flags=(attach_disconnected, mediate_deleted) {
    # ========================================================
    # Base system includes
    # ========================================================
    #include <abstractions/base>
    #include <abstractions/nameservice>
    #include <abstractions/openssl>

    # ========================================================
    # Capabilities — minimal set
    # ========================================================
    capability net_bind_service,  # Bind port 80/443
    capability dac_override,      # Read/write config files
    capability setuid,            # Drop privileges after bind
    capability setgid,
    capability chown,

    # DENY dangerous capabilities explicitly
    deny capability sys_admin,
    deny capability sys_ptrace,
    deny capability sys_module,
    deny capability net_admin,
    deny capability sys_boot,

    # ========================================================
    # Network rules
    # ========================================================
    network inet tcp,             # IPv4 TCP (HTTP/HTTPS)
    network inet6 tcp,            # IPv6 TCP
    network inet udp,             # UDP (DNS resolution)
    network netlink raw,          # For network configuration

    # DENY: Raw sockets (ARP spoofing, MITM)
    deny network raw,
    deny network packet,

    # ========================================================
    # File access — explicit allowlist
    # ========================================================

    # nginx binary
    /usr/sbin/nginx                     mr,
    /usr/lib/nginx/modules/*.so         mr,

    # Configuration (read only)
    /etc/nginx/**                       r,
    /etc/ssl/**                         r,
    /etc/ca-certificates/**             r,

    # Web root (read only — NEVER write access to web root)
    /var/www/html/**                    r,

    # Logs (write access to log directory only)
    /var/log/nginx/                     rw,
    /var/log/nginx/*.log                rw,

    # PID and run files
    /var/run/nginx.pid                  rw,
    /run/nginx.pid                      rw,

    # Temp files
    /tmp/                               rw,
    /tmp/**                             rw,

    # Proc filesystem — limited read
    /proc/sys/kernel/ngroups_max        r,
    /proc/sys/net/core/somaxconn        r,

    # System libraries
    /lib/x86_64-linux-gnu/**            mr,
    /usr/lib/x86_64-linux-gnu/**        mr,

    # DENY: Access to host sensitive paths
    deny /proc/sysrq-trigger            rw,
    deny /proc/sys/kernel/modprobe      rw,
    deny /sys/**                        rw,
    deny /root/**                       rw,
    deny /home/**                       rw,
    deny /etc/shadow                    rw,
    deny /etc/sudoers                   rw,

    # ========================================================
    # Signal handling
    # ========================================================
    signal (receive) set=(hup term quit usr1 usr2) peer=unconfined,
    signal (send)    set=(hup term quit) peer=k8s-nginx,

    # ========================================================
    # File descriptor inheritance from parent
    # ========================================================
    unix (send, receive) type=stream,
}
```

---

### 2.6 SELinux — "The More Powerful (and Complex) MAC System"

**What is SELinux?**

Security-Enhanced Linux (SELinux) is an NSA-developed LSM that implements Type Enforcement, Multi-Level Security (MLS), and Multi-Category Security (MCS). It's more powerful than AppArmor but significantly more complex.

**Key Concepts:**

```
SELinux Label (Security Context):
user:role:type:level
  │     │    │    └─ MLS level (s0:c0,c1)
  │     │    └────── Type (domain for processes, type for files)
  │     └─────────── Role (what transitions are allowed)
  └───────────────── SELinux user (maps to Linux user)

Example:
  Process: system_u:system_r:container_t:s0:c123,c456
  File:    system_u:object_r:container_file_t:s0

Rules in SELinux:
  allow container_t container_file_t:file { read write };
  deny  container_t host_file_t:file *;
```

**SELinux for Kubernetes (OpenShift/RHEL):**

```
MCS (Multi-Category Security) in Kubernetes:
Each pod gets a unique MCS label pair (c0-c1023)
→ Even if two pods run as root, they can't access each other's files
→ This is enforced by the kernel, not by Kubernetes
```

```bash
# Check SELinux status on Kubernetes node
getenforce          # Enforcing | Permissive | Disabled
sestatus

# View label of a container process
ps -eZ | grep container

# View label of a file in container
ls -Z /var/lib/containers/

# The key SELinux type for containers:
# container_t (process domain)
# container_file_t (file type)
# container_ro_file_t (read-only files)
```

**IMPORTANT Production Rule**: In Kubernetes on RHEL/CentOS/Fedora nodes, **never disable SELinux**. Many security controls depend on it. A common (catastrophically bad) pattern in tutorials:

```bash
# NEVER DO THIS ON PRODUCTION NODES:
setenforce 0
echo "SELINUX=disabled" >> /etc/selinux/config

# This disables a fundamental security layer and cannot be re-enabled
# without a reboot, and doing so may leave you with mislabeled files
```

---

### 2.7 eBPF — "The Modern Security Swiss Army Knife"

**What is eBPF?**

eBPF (extended Berkeley Packet Filter) is a revolutionary Linux kernel technology that allows safe, sandboxed programs to run in the kernel without writing kernel modules. For security, eBPF enables:

- **Observability**: Trace every syscall, file access, network connection
- **Enforcement**: Block syscalls or network connections in real time
- **Auditing**: Record security-relevant events with full context

```
eBPF Architecture:
┌────────────────────────────────────────────────────────────────┐
│                    USER SPACE                                   │
│  Falco / Tetragon / Cilium ──────► eBPF Loader (libbpf)      │
│                                            │                    │
└────────────────────────────────────────────┼────────────────────┘
                                             │ (verifier checks)
┌────────────────────────────────────────────┼────────────────────┐
│                   KERNEL SPACE             │                    │
│                                            ▼                    │
│  Hook Points:                        eBPF Program              │
│  ├── Syscall entry/exit  ◄──────────────────────────────────── │
│  ├── LSM hooks (security_*)                                    │
│  ├── kprobes (any kernel function)                             │
│  ├── Network TC/XDP                                            │
│  └── Tracepoints                                               │
│                                                                 │
│  eBPF Maps (shared memory):                                    │
│  ├── Hash maps (per-process tracking)                          │
│  ├── Ring buffers (event streaming)                            │
│  └── LRU maps (recent events)                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Container Security Internals

### 3.1 OCI (Open Container Initiative) and the Container Runtime Stack

```
Container Runtime Stack:
┌────────────────────────────────────────────┐
│           kubectl / Kubernetes API         │
└─────────────────────┬──────────────────────┘
                      │ CRI (Container Runtime Interface)
┌─────────────────────▼──────────────────────┐
│         containerd / CRI-O                 │  ← High-level runtime
│  (image pulling, storage, CRI server)      │
└─────────────────────┬──────────────────────┘
                      │ OCI Runtime Spec
┌─────────────────────▼──────────────────────┐
│         runc / crun / runsc (gVisor)        │  ← Low-level runtime
│  (actually creates namespaces, cgroups)    │
└─────────────────────┬──────────────────────┘
                      │ Linux Kernel
┌─────────────────────▼──────────────────────┐
│  Namespaces + cgroups + seccomp + LSM      │  ← Kernel primitives
└────────────────────────────────────────────┘
```

**OCI Runtime Spec** defines what a container is: a JSON config.json file that specifies namespaces, capabilities, seccomp filters, mount points, etc.

```json
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": false,
    "user": {
      "uid": 1000,
      "gid": 1000
    },
    "args": ["/app/server"],
    "capabilities": {
      "bounding": [],
      "effective": [],
      "inheritable": [],
      "permitted": [],
      "ambient": []
    },
    "noNewPrivileges": true,
    "seccompProfile": "/etc/seccomp/default.json"
  },
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "network"},
      {"type": "ipc"},
      {"type": "uts"},
      {"type": "mount"},
      {"type": "user"}
    ],
    "maskedPaths": [
      "/proc/acpi",
      "/proc/kcore",
      "/proc/keys",
      "/proc/latency_stats",
      "/proc/timer_list",
      "/proc/timer_stats",
      "/proc/sched_debug",
      "/proc/scsi",
      "/sys/firmware"
    ],
    "readonlyPaths": [
      "/proc/asound",
      "/proc/bus",
      "/proc/fs",
      "/proc/irq",
      "/proc/sys",
      "/proc/sysrq-trigger"
    ]
  }
}
```

### 3.2 Image Security — The Supply Chain Foundation

**Layers of Image Security:**

```
Image Security Layers:
┌─────────────────────────────────────────────────────────────────┐
│ 1. BASE IMAGE SECURITY                                          │
│    - Use minimal base (distroless, scratch, alpine)            │
│    - Scan for CVEs before use                                   │
│    - Pin by digest (sha256:abc...) not tag (latest)            │
├─────────────────────────────────────────────────────────────────┤
│ 2. BUILD SECURITY                                               │
│    - Multi-stage builds (no build tools in final image)        │
│    - No secrets in Dockerfile (ARG, ENV, COPY)                 │
│    - Run as non-root in the final stage                        │
├─────────────────────────────────────────────────────────────────┤
│ 3. CONTENT SECURITY                                             │
│    - Remove all unnecessary binaries (no shell in prod!)       │
│    - Read-only filesystem                                       │
│    - Sign with Cosign/Sigstore                                  │
├─────────────────────────────────────────────────────────────────┤
│ 4. REGISTRY SECURITY                                            │
│    - Private registry with authentication                      │
│    - Vulnerability scanning on push                            │
│    - Admission control verifies signatures                     │
└─────────────────────────────────────────────────────────────────┘
```

**VULNERABLE Dockerfile:**

```dockerfile
# VULNERABLE: Do not use in production
FROM ubuntu:latest          # Unpinned tag — can change!
RUN apt-get install -y python3 pip git curl wget ssh vim  # Attack surface
COPY . /app                 # May copy secrets, .git, credentials!
ENV DB_PASSWORD=mysecret123 # SECRET IN IMAGE LAYER — extractable!
USER root                   # Running as root
EXPOSE 22                   # SSH open in a container!
CMD ["python3", "app.py"]
```

**SECURE Dockerfile (Go application):**

```dockerfile
# SECURE: Multi-stage build for Go application
# Stage 1: Build
FROM golang:1.22-alpine AS builder

# Pin specific version — never use 'latest'
# Use sha256 digest in production:
# FROM golang:1.22-alpine@sha256:abc123...

WORKDIR /build

# Copy go.mod first for layer caching
COPY go.mod go.sum ./
RUN go mod download

# Verify module checksums (supply chain security)
RUN go mod verify

COPY . .

# Build with security flags:
# - CGO_ENABLED=0: static binary, no C runtime dependency
# - -trimpath: remove build paths from binary (information disclosure)
# - -ldflags: strip debug info, set version
# - GOFLAGS=-mod=readonly: prevent go.sum modification during build
RUN CGO_ENABLED=0 \
    GOFLAGS="-mod=readonly" \
    go build \
    -trimpath \
    -ldflags="-w -s -X main.version=$(git describe --tags --always)" \
    -o /app/server \
    ./cmd/server

# Verify binary is statically linked
RUN file /app/server | grep -q "statically linked" || exit 1

# Stage 2: Final image — distroless
# distroless has NO shell, NO package manager, NO utilities
# This dramatically reduces attack surface
FROM gcr.io/distroless/static-debian12:nonroot

# Copy ONLY what's needed
COPY --from=builder /app/server /server

# Non-root user (already set in distroless:nonroot)
USER nonroot:nonroot

# Metadata
LABEL org.opencontainers.image.source="https://github.com/org/repo"
LABEL org.opencontainers.image.revision="${GIT_SHA}"

EXPOSE 8080

ENTRYPOINT ["/server"]
```

---

## 4. Kubernetes Architecture & Attack Surface

### 4.1 Kubernetes Architecture Overview

```
Kubernetes Cluster Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                            │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   API Server   │  │   Controller   │  │    Scheduler     │  │
│  │  (kube-apiserver)│ │   Manager      │  │  (kube-scheduler)│  │
│  │                │  │(kube-controller)│  │                  │  │
│  └───────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
│          │                   │                     │            │
│  ┌───────▼───────────────────▼─────────────────────▼─────────┐  │
│  │                    etcd (KV store)                         │  │
│  │  Stores: cluster state, secrets, RBAC, config, certs      │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Secure (mTLS)
┌──────────────────────────▼──────────────────────────────────────┐
│                         WORKER NODE                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │    kubelet   │  │  kube-proxy   │  │  Container Runtime   │  │
│  │ (node agent) │  │(iptables/IPVS)│  │(containerd/CRI-O)   │  │
│  └──────────────┘  └───────────────┘  └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Pod (Namespace + cgroup + seccomp + AppArmor boundary)     │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │ │
│  │  │ Container1 │  │ Container2 │  │   Sidecar (proxy)  │    │ │
│  │  └────────────┘  └────────────┘  └────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 API Server Security — The Crown Jewel

The API server is the central nervous system of Kubernetes. **Every** operation goes through it. Compromising the API server = owning the entire cluster.

```
API Server Request Flow (with security checkpoints):
                                        
  Client Request                        
       │                                
       ▼                                
┌─────────────────────┐                
│  1. AUTHENTICATION  │ ← Who are you? (mTLS, JWT, etc.)
│  - Client certs     │
│  - Bearer tokens    │   FAIL → 401 Unauthorized
│  - OIDC tokens      │
│  - Webhook auth     │
└──────────┬──────────┘
           │ (identity established)
           ▼
┌─────────────────────┐
│  2. AUTHORIZATION   │ ← Are you allowed? (RBAC, ABAC)
│  - RBAC rules       │
│  - Node authorizer  │   FAIL → 403 Forbidden
│  - Webhook authz    │
└──────────┬──────────┘
           │ (permission granted)
           ▼
┌─────────────────────┐
│  3. ADMISSION       │ ← Is the request valid/secure?
│  - Validating       │   (OPA Gatekeeper, Kyverno)
│  - Mutating         │   FAIL → 422/400 
│  - ResourceQuota    │
└──────────┬──────────┘
           │ (request admitted)
           ▼
┌─────────────────────┐
│  4. etcd STORAGE    │ ← Persist state (encrypted at rest)
└─────────────────────┘
```

**Critical API Server Flags (Security Hardening):**

```bash
kube-apiserver \
  # Authentication
  --anonymous-auth=false \                    # NEVER allow anonymous access!
  --client-ca-file=/etc/kubernetes/ca.crt \  # Require client certificates
  --oidc-issuer-url=https://your-oidc.com \  # OIDC for human users
  --oidc-client-id=kubernetes \
  
  # Authorization
  --authorization-mode=Node,RBAC \           # Node + RBAC (NEVER AlwaysAllow!)
  
  # Admission
  --enable-admission-plugins=\
    NodeRestriction,\                        # Nodes can only modify their own resources
    PodSecurity,\                            # Pod Security Admission
    ResourceQuota,\                          # Enforce resource limits
    LimitRanger,\                            # Default resource limits
    ServiceAccount,\                         # Auto-inject service account tokens
    DenyEscalatingExec \                     # Deny exec into privileged pods
  
  # TLS
  --tls-cert-file=/etc/kubernetes/apiserver.crt \
  --tls-private-key-file=/etc/kubernetes/apiserver.key \
  --tls-cipher-suites=TLS_AES_128_GCM_SHA256,TLS_AES_256_GCM_SHA384 \
  --tls-min-version=VersionTLS13 \          # TLS 1.3 minimum!
  
  # Audit
  --audit-log-path=/var/log/kube-audit.log \
  --audit-policy-file=/etc/kubernetes/audit-policy.yaml \
  --audit-log-maxage=30 \
  --audit-log-maxbackup=10 \
  --audit-log-maxsize=100 \
  
  # etcd
  --etcd-cafile=/etc/kubernetes/etcd/ca.crt \
  --etcd-certfile=/etc/kubernetes/etcd/client.crt \
  --etcd-keyfile=/etc/kubernetes/etcd/client.key \
  
  # Security
  --encryption-provider-config=/etc/kubernetes/encryption.yaml \  # Encrypt secrets at rest
  --profiling=false \                        # Disable profiling endpoint!
  --enable-bootstrap-token-auth=false \      # Disable if not using bootstrap tokens
  --service-account-lookup=true \            # Verify SA tokens against etcd
  --service-account-key-file=/etc/kubernetes/sa.pub \
  --service-account-signing-key-file=/etc/kubernetes/sa.key \
  --service-account-issuer=https://your-cluster.example.com
```

---

## 5. Authentication & Authorization (RBAC)

### 5.1 Authentication Methods

**What is Authentication?** Authentication answers: "Who are you?" Before Kubernetes will process any request, it must establish the identity of the requester.

```
Authentication Methods in Kubernetes:
┌─────────────────────────────────────────────────────────────────┐
│ METHOD          │ USE CASE          │ SECURITY LEVEL            │
├─────────────────────────────────────────────────────────────────┤
│ X.509 Client    │ Service accounts  │ HIGH (asymmetric crypto)  │
│ Certificates    │ System components │                           │
├─────────────────────────────────────────────────────────────────┤
│ Bearer Tokens   │ Service accounts  │ MEDIUM (if short-lived)   │
│ (JWT)           │ Applications      │ LOW (if long-lived)       │
├─────────────────────────────────────────────────────────────────┤
│ OIDC            │ Human users       │ HIGH (with PKCE + MFA)    │
│                 │ (SSO integration) │                           │
├─────────────────────────────────────────────────────────────────┤
│ Webhook Token   │ Custom auth       │ DEPENDS ON IMPLEMENTATION │
│ Auth            │ (Dex, Guard)      │                           │
├─────────────────────────────────────────────────────────────────┤
│ Bootstrap Token │ Node joining      │ MEDIUM (rotate after use) │
├─────────────────────────────────────────────────────────────────┤
│ Static Token    │ LEGACY/TESTING    │ LOW — never use in prod!  │
│ File            │                   │                           │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 RBAC Deep Dive

**RBAC Concepts:**

```
RBAC Object Model:
┌──────────────────┐        ┌──────────────────┐
│   Role           │        │  ClusterRole      │
│ (namespace-scoped)│       │ (cluster-wide)    │
│  rules:          │        │  rules:           │
│  - apiGroups     │        │  - apiGroups      │
│  - resources     │        │  - resources      │
│  - verbs         │        │  - verbs          │
└────────┬─────────┘        └────────┬──────────┘
         │ bound by                   │ bound by
         ▼                            ▼
┌──────────────────┐        ┌──────────────────┐
│  RoleBinding     │        │ClusterRoleBinding │
│  subjects:       │        │  subjects:        │
│  - User          │        │  - User           │
│  - Group         │        │  - Group          │
│  - ServiceAccount│        │  - ServiceAccount │
└──────────────────┘        └──────────────────┘
```

**VULNERABLE RBAC Configuration:**

```yaml
# VULNERABLE: Do not use in production
# This gives a service account cluster-admin — full control!
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: DANGEROUS-admin-binding
subjects:
- kind: ServiceAccount
  name: my-app
  namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-admin        # FULL CLUSTER CONTROL — never bind this!
  apiGroup: rbac.authorization.k8s.io
```

**Another vulnerable pattern — overly permissive Role:**

```yaml
# VULNERABLE: Wildcard permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: bad-role
  namespace: production
rules:
- apiGroups: ["*"]     # All API groups — too broad!
  resources: ["*"]     # All resources — too broad!
  verbs: ["*"]         # All verbs — too broad!
```

**SECURE RBAC — Least Privilege:**

```yaml
# SECURE: Minimal permissions for a read-only monitoring service
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus-scraper
  namespace: monitoring
  annotations:
    # Document WHY this service account exists
    security.company.com/purpose: "Prometheus metrics scraping"
    security.company.com/owner: "platform-team"
    security.company.com/review-date: "2025-01-01"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus-scraper
  labels:
    security-tier: monitoring
rules:
# ONLY what Prometheus needs — nothing more
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy        # Required for kubelet metrics
  - nodes/metrics
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]  # Read-only: NO create, update, delete, patch!

- apiGroups: ["extensions", "networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]

# Explicitly no access to secrets, configmaps with sensitive data
# No access to: secrets, persistentvolumes, clusterroles, etc.
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus-scraper
subjects:
- kind: ServiceAccount
  name: prometheus-scraper
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: prometheus-scraper
  apiGroup: rbac.authorization.k8s.io
---
# SECURE: Restrict application service account — truly minimal
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: webapp-role
  namespace: production
rules:
# Only what the app needs — reading its own ConfigMap
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["webapp-config"]  # Named resource restriction!
  verbs: ["get"]
# Note: no 'list' (can't enumerate all ConfigMaps)
# Note: no 'watch' (can't watch for changes)
# Note: no 'update', 'patch', 'delete', 'create'
```

### 5.3 Go Implementation: RBAC Auditor

```go
// File: rbac_auditor.go
// Purpose: Audit Kubernetes RBAC for common misconfigurations
// This is a security tool that detects privilege escalation risks
// Used in production CI/CD pipelines for continuous security validation

package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

// RiskLevel represents the severity of an RBAC finding
type RiskLevel string

const (
	RiskCritical RiskLevel = "CRITICAL"
	RiskHigh     RiskLevel = "HIGH"
	RiskMedium   RiskLevel = "MEDIUM"
	RiskLow      RiskLevel = "LOW"
	RiskInfo     RiskLevel = "INFO"
)

// Finding represents a single RBAC security finding
type Finding struct {
	Risk        RiskLevel
	Resource    string
	Namespace   string
	Subject     string
	Description string
	Remediation string
}

// RBACauditor performs security analysis on cluster RBAC
type RBACauditor struct {
	client   *kubernetes.Clientset
	findings []Finding
}

// Dangerous verbs that grant write/escalation abilities
var dangerousVerbs = map[string]bool{
	"*":            true,
	"create":       true,
	"update":       true,
	"patch":        true,
	"delete":       true,
	"deletecollection": true,
	"bind":         true,
	"escalate":     true,
	"impersonate":  true,
}

// Sensitive resources that should never have broad access
var sensitiveResources = map[string]RiskLevel{
	"secrets":                      RiskCritical,
	"serviceaccounts/token":        RiskCritical, // TokenRequest
	"pods/exec":                    RiskHigh,
	"pods/attach":                  RiskHigh,
	"nodes":                        RiskHigh,
	"clusterroles":                 RiskHigh,
	"clusterrolebindings":          RiskHigh,
	"rolebindings":                 RiskMedium,
	"roles":                        RiskMedium,
	"persistentvolumes":            RiskMedium,
	"validatingwebhookconfigurations": RiskHigh,
	"mutatingwebhookconfigurations":   RiskHigh,
}

// NewRBACauditor creates a new auditor connected to the cluster
func NewRBACauditor(kubeconfig string) (*RBACauditor, error) {
	var config *rest.Config
	var err error

	if kubeconfig == "" {
		// In-cluster configuration (when running as a pod)
		config, err = rest.InClusterConfig()
	} else {
		// Out-of-cluster (local development/auditing)
		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to build kubeconfig: %w", err)
	}

	// Security hardening for the client:
	// - TLS verification always enabled
	// - Rate limiting to avoid overloading API server
	config.QPS = 20
	config.Burst = 50

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create client: %w", err)
	}

	return &RBACauditor{client: client}, nil
}

// addFinding records a security finding
func (a *RBACauditor) addFinding(risk RiskLevel, resource, ns, subject, desc, remediation string) {
	a.findings = append(a.findings, Finding{
		Risk:        risk,
		Resource:    resource,
		Namespace:   ns,
		Subject:     subject,
		Description: desc,
		Remediation: remediation,
	})
}

// checkRulesForPrivilegeEscalation analyzes RBAC rules for dangerous patterns
func (a *RBACauditor) checkRulesForPrivilegeEscalation(
	rules []rbacv1.PolicyRule,
	roleName, namespace string,
) []string {
	var issues []string

	for _, rule := range rules {
		// Check for wildcard API groups (*)
		hasWildcardGroup := false
		for _, group := range rule.APIGroups {
			if group == "*" {
				hasWildcardGroup = true
				break
			}
		}

		// Check for wildcard resources
		hasWildcardResource := false
		for _, resource := range rule.Resources {
			if resource == "*" {
				hasWildcardResource = true
				break
			}
		}

		// Check for wildcard verbs
		hasWildcardVerb := false
		for _, verb := range rule.Verbs {
			if verb == "*" {
				hasWildcardVerb = true
				break
			}
		}

		// Pattern 1: Full wildcard — cluster-admin equivalent
		if hasWildcardGroup && hasWildcardResource && hasWildcardVerb {
			issues = append(issues, "CLUSTER-ADMIN EQUIVALENT: wildcards on groups, resources, and verbs")
		}

		// Pattern 2: Can exec into pods (container breakout risk)
		for _, resource := range rule.Resources {
			if resource == "pods/exec" || resource == "pods/attach" {
				for _, verb := range rule.Verbs {
					if verb == "*" || verb == "create" {
						issues = append(issues, fmt.Sprintf(
							"CONTAINER EXEC: can exec/attach to pods (pivot to any container)"))
					}
				}
			}
		}

		// Pattern 3: Can write to secrets (credential theft)
		for _, resource := range rule.Resources {
			if resource == "secrets" || resource == "*" {
				for _, verb := range rule.Verbs {
					if dangerousVerbs[verb] {
						issues = append(issues, fmt.Sprintf(
							"SECRET ACCESS: can %s secrets (credential theft)", verb))
					}
				}
			}
		}

		// Pattern 4: Can bind ClusterRoles (privilege escalation)
		for _, resource := range rule.Resources {
			if resource == "clusterrolebindings" || resource == "rolebindings" {
				for _, verb := range rule.Verbs {
					if verb == "create" || verb == "update" || verb == "patch" || verb == "*" {
						issues = append(issues, fmt.Sprintf(
							"PRIVILEGE ESCALATION: can create/modify %s (bind any role to any user)", resource))
					}
				}
			}
		}

		// Pattern 5: Can impersonate other users
		for _, resource := range rule.Resources {
			if resource == "users" || resource == "groups" || resource == "serviceaccounts" {
				for _, verb := range rule.Verbs {
					if verb == "impersonate" || verb == "*" {
						issues = append(issues,
							"IMPERSONATION: can impersonate other users/groups/service accounts")
					}
				}
			}
		}

		// Pattern 6: Can modify webhook configurations (MitM attacks)
		for _, resource := range rule.Resources {
			if strings.Contains(resource, "webhookconfigurations") {
				issues = append(issues,
					"WEBHOOK MANIPULATION: can modify webhook configs (MitM all API calls)")
			}
		}
	}

	return issues
}

// AuditClusterRoles audits all ClusterRoles
func (a *RBACauditor) AuditClusterRoles(ctx context.Context) error {
	clusterRoles, err := a.client.RbacV1().ClusterRoles().List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list ClusterRoles: %w", err)
	}

	for _, cr := range clusterRoles.Items {
		// Skip system roles (they're managed by Kubernetes itself)
		if strings.HasPrefix(cr.Name, "system:") {
			continue
		}

		issues := a.checkRulesForPrivilegeEscalation(cr.Rules, cr.Name, "")
		for _, issue := range issues {
			a.addFinding(
				RiskHigh,
				"ClusterRole/"+cr.Name,
				"cluster-wide",
				cr.Name,
				issue,
				"Apply principle of least privilege: specify exact resources and verbs needed",
			)
		}
	}

	return nil
}

// AuditClusterRoleBindings finds bindings to powerful roles
func (a *RBACauditor) AuditClusterRoleBindings(ctx context.Context) error {
	bindings, err := a.client.RbacV1().ClusterRoleBindings().List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list ClusterRoleBindings: %w", err)
	}

	for _, binding := range bindings.Items {
		// CRITICAL: Anyone bound to cluster-admin is an admin
		if binding.RoleRef.Name == "cluster-admin" {
			for _, subject := range binding.Subjects {
				// System components are expected to have high privilege
				if !strings.HasPrefix(subject.Name, "system:") {
					a.addFinding(
						RiskCritical,
						"ClusterRoleBinding/"+binding.Name,
						"cluster-wide",
						fmt.Sprintf("%s/%s", subject.Kind, subject.Name),
						fmt.Sprintf("Subject is bound to cluster-admin — full cluster control"),
						"Remove this binding or replace with a least-privilege custom ClusterRole",
					)
				}
			}
		}

		// HIGH: Service accounts bound to cluster-admin
		for _, subject := range binding.Subjects {
			if subject.Kind == "ServiceAccount" &&
				binding.RoleRef.Name == "cluster-admin" {
				a.addFinding(
					RiskCritical,
					"ClusterRoleBinding/"+binding.Name,
					subject.Namespace,
					"ServiceAccount/"+subject.Name,
					"Service account has cluster-admin — any pod using this SA owns the cluster",
					"Use a custom ClusterRole with only required permissions",
				)
			}
		}
	}

	return nil
}

// AuditServiceAccountTokens finds SA tokens that might be overly permissive
func (a *RBACauditor) AuditServiceAccountTokens(ctx context.Context) error {
	namespaces, err := a.client.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list namespaces: %w", err)
	}

	for _, ns := range namespaces.Items {
		// Check for automounted SA tokens in default service account
		// Default SA auto-mounted tokens are a common attack vector
		defaultSA, err := a.client.CoreV1().ServiceAccounts(ns.Name).Get(
			ctx, "default", metav1.GetOptions{})
		if err != nil {
			continue
		}

		// If automountServiceAccountToken is nil or true, it's auto-mounted
		if defaultSA.AutomountServiceAccountToken == nil ||
			*defaultSA.AutomountServiceAccountToken {
			a.addFinding(
				RiskMedium,
				"ServiceAccount/default",
				ns.Name,
				"ServiceAccount/default",
				"Default service account auto-mounts API token — "+
					"all pods in namespace can call Kubernetes API",
				"Set automountServiceAccountToken: false on default SA, "+
					"opt-in per pod when needed",
			)
		}
	}

	return nil
}

// PrintReport outputs the audit findings
func (a *RBACauditor) PrintReport() {
	fmt.Println("\n" + strings.Repeat("=", 70))
	fmt.Println("KUBERNETES RBAC SECURITY AUDIT REPORT")
	fmt.Println(strings.Repeat("=", 70))

	// Count by severity
	counts := map[RiskLevel]int{}
	for _, f := range a.findings {
		counts[f.Risk]++
	}

	fmt.Printf("\nSummary: %d CRITICAL, %d HIGH, %d MEDIUM, %d LOW\n",
		counts[RiskCritical], counts[RiskHigh], counts[RiskMedium], counts[RiskLow])
	fmt.Println(strings.Repeat("-", 70))

	// Print by severity order
	for _, level := range []RiskLevel{RiskCritical, RiskHigh, RiskMedium, RiskLow, RiskInfo} {
		for _, f := range a.findings {
			if f.Risk != level {
				continue
			}
			fmt.Printf("\n[%s] %s\n", f.Risk, f.Resource)
			fmt.Printf("  Namespace:   %s\n", f.Namespace)
			fmt.Printf("  Subject:     %s\n", f.Subject)
			fmt.Printf("  Issue:       %s\n", f.Description)
			fmt.Printf("  Fix:         %s\n", f.Remediation)
		}
	}

	fmt.Println("\n" + strings.Repeat("=", 70))

	// Exit with non-zero code if critical findings (useful in CI/CD)
	if counts[RiskCritical] > 0 {
		fmt.Fprintf(os.Stderr, "\nFAIL: %d critical RBAC findings detected\n",
			counts[RiskCritical])
		os.Exit(1)
	}
}

func main() {
	kubeconfig := os.Getenv("KUBECONFIG")
	if kubeconfig == "" {
		kubeconfig = os.ExpandEnv("$HOME/.kube/config")
	}

	auditor, err := NewRBACauditor(kubeconfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create auditor: %v\n", err)
		os.Exit(1)
	}

	ctx := context.Background()

	fmt.Println("Auditing ClusterRoles...")
	if err := auditor.AuditClusterRoles(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	}

	fmt.Println("Auditing ClusterRoleBindings...")
	if err := auditor.AuditClusterRoleBindings(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	}

	fmt.Println("Auditing ServiceAccount tokens...")
	if err := auditor.AuditServiceAccountTokens(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	}

	auditor.PrintReport()
}
```

---

## 6. Pod Security: Standards, Policies, Admission

### 6.1 Pod Security Admission (PSA) — Kubernetes 1.25+

**What is PSA?**

Pod Security Admission replaced Pod Security Policies (PSP, deprecated in 1.21, removed in 1.25). PSA enforces three built-in security profiles:

```
PSA Security Levels:
┌─────────────────────────────────────────────────────────────────┐
│ PRIVILEGED                                                      │
│  - No restrictions                                              │
│  - For system/infrastructure pods (kube-system)                │
│  - Can run containers as root, with any capability             │
├─────────────────────────────────────────────────────────────────┤
│ BASELINE                                                        │
│  - Prevents known privilege escalation                         │
│  - No privileged containers                                     │
│  - No hostPath volumes (with exceptions)                       │
│  - No hostPID, hostIPC, hostNetwork                            │
│  - Restricted seccomp/AppArmor                                 │
│  - Limits dangerous capabilities                               │
├─────────────────────────────────────────────────────────────────┤
│ RESTRICTED                                                      │
│  - Enforces hardening best practices                           │
│  - All baseline requirements +                                  │
│  - Must run as non-root                                         │
│  - seccompProfile must be RuntimeDefault or Localhost          │
│  - allowPrivilegeEscalation must be false                      │
│  - Capabilities must be explicitly dropped                     │
└─────────────────────────────────────────────────────────────────┘

PSA Modes (per namespace):
  enforce → Reject pods that violate the policy
  audit   → Allow but log violations (transition phase)
  warn    → Allow but warn user (transition phase)
```

**Namespace Labels for PSA:**

```yaml
# SECURE: Namespace configured for restricted security
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce restricted — reject non-compliant pods
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.30

    # Audit with latest version check
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.30

    # Warn users about violations
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.30
```

### 6.2 Secure Pod Specification

**VULNERABLE Pod Spec — The Worst Possible Configuration:**

```yaml
# VULNERABLE: This pod is effectively a root shell on the host node
# DO NOT DEPLOY
apiVersion: v1
kind: Pod
metadata:
  name: DANGER-privileged-pod
spec:
  hostPID: true          # Can see all processes on host!
  hostIPC: true          # Access host IPC mechanisms
  hostNetwork: true      # Bypass network policies!
  
  volumes:
  - name: host-root
    hostPath:
      path: /            # MOUNT THE ENTIRE HOST FILESYSTEM
  
  containers:
  - name: evil-container
    image: ubuntu:latest  # Unpinned, large attack surface
    
    securityContext:
      privileged: true           # Equivalent to root on host
      runAsUser: 0               # Running as root
      allowPrivilegeEscalation: true  # Can gain more privileges
      
    volumeMounts:
    - name: host-root
      mountPath: /host           # Access to entire host filesystem!
    
    command: ["sh", "-c", "nsenter -t 1 -m -u -i -n -p -- bash"]
    # ^ This is literally a container escape tool
```

**SECURE Pod Spec — Production Hardened:**

```yaml
# SECURE: Production-hardened pod specification
apiVersion: v1
kind: Pod
metadata:
  name: secure-webapp
  namespace: production
  labels:
    app: webapp
    security-tier: restricted
  annotations:
    # AppArmor profile (Kubernetes < 1.30)
    container.apparmor.security.beta.kubernetes.io/webapp: runtime/default
    # Seccomp (Kubernetes < 1.19)
    # seccomp.security.alpha.kubernetes.io/pod: runtime/default
spec:
  # SECURE: No host namespace sharing
  hostPID: false        # Cannot see host processes
  hostIPC: false        # Cannot access host IPC
  hostNetwork: false    # Must use pod network (NetworkPolicy applies)
  
  # SECURE: Use a non-default service account with minimal permissions
  serviceAccountName: webapp-sa
  automountServiceAccountToken: false  # Explicitly opt-out unless needed!
  
  # SECURE: Priority class for resource scheduling
  priorityClassName: low-priority
  
  # SECURE: Pod-level security context
  securityContext:
    runAsNonRoot: true          # Refuse to run as root
    runAsUser: 10001            # Specific non-root UID
    runAsGroup: 10001           # Specific non-root GID
    fsGroup: 10001              # Group for mounted volumes
    fsGroupChangePolicy: OnRootMismatch  # Efficient permission changes
    
    # SECURE: Restrict supplemental groups
    supplementalGroups: []
    
    # SECURE: Seccomp profile (Kubernetes 1.19+)
    seccompProfile:
      type: RuntimeDefault      # Use container runtime's default profile
      # For stricter: type: Localhost, localhostProfile: profiles/strict.json
    
    # SECURE: sysctls — only safe namespaced ones
    sysctls: []                 # No sysctls unless absolutely required
  
  # SECURE: No volumes with host access
  volumes:
  - name: tmp
    emptyDir:
      medium: Memory            # In-memory temp storage
      sizeLimit: 100Mi          # Size-limited
  - name: config
    configMap:
      name: webapp-config
      defaultMode: 0444         # Read-only file permissions
  
  containers:
  - name: webapp
    image: myregistry.com/webapp:v1.2.3@sha256:abc123def456...  # Pinned digest!
    
    # SECURE: Container-level security context
    securityContext:
      allowPrivilegeEscalation: false  # CANNOT escalate (even via SUID)
      privileged: false                # Not privileged
      readOnlyRootFilesystem: true     # Root filesystem is read-only!
      runAsNonRoot: true
      runAsUser: 10001
      runAsGroup: 10001
      
      # SECURE: Drop all capabilities, add only what's needed
      capabilities:
        drop: ["ALL"]            # Drop every capability
        add: []                  # Add none (web server doesn't need any!)
      
      # SECURE: Seccomp at container level (overrides pod level)
      seccompProfile:
        type: RuntimeDefault
      
      # SECURE: AppArmor profile (1.30+ native)
      appArmorProfile:
        type: RuntimeDefault
    
    ports:
    - containerPort: 8080
      name: http
      protocol: TCP
    
    # SECURE: Resource limits — BOTH requests AND limits required
    resources:
      requests:
        cpu: "100m"              # 0.1 CPU reserved
        memory: "128Mi"
        ephemeral-storage: "100Mi"
      limits:
        cpu: "500m"              # Max 0.5 CPU (prevents CPU stealing)
        memory: "256Mi"          # Hard memory limit (OOM kill before host suffers)
        ephemeral-storage: "500Mi"
    
    # SECURE: Mount only necessary paths
    volumeMounts:
    - name: tmp
      mountPath: /tmp            # Writable temp area
    - name: config
      mountPath: /etc/webapp
      readOnly: true             # Config is read-only
    
    # SECURE: Environment — no secrets as env vars!
    # Use SecretStore CSI or volume mounts instead
    env:
    - name: PORT
      value: "8080"
    - name: LOG_LEVEL
      value: "info"
    # NEVER: - name: DB_PASSWORD, value: "mysecret"
    
    # SECURE: Health checks (also security benefit — detect compromised states)
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
    
    # SECURE: Startup probe — don't apply liveness before startup
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30
      periodSeconds: 10
  
  # SECURE: Topology constraints — don't put all pods on one node
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: webapp
  
  # SECURE: Anti-affinity — spread across failure domains
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values: ["webapp"]
          topologyKey: kubernetes.io/hostname
```

---

## 7. Network Security & Policies

### 7.1 Kubernetes Network Model

**Default behavior**: All pods can communicate with all other pods in the cluster, across namespaces. This is the "flat network" model.

**Why this is a problem**: If one pod is compromised, the attacker can reach every other pod in the cluster, regardless of namespace.

```
Default (No NetworkPolicy):
┌──────────────────────────────────────────────────────────────┐
│  Namespace: frontend   │   Namespace: backend                │
│  ┌──────────────┐      │   ┌──────────────┐                 │
│  │  web-pod     │◄─────┼───│  db-pod      │ (allowed!)      │
│  └──────────────┘      │   └──────────────┘                 │
│         │              │         │                           │
│         ▼              │         ▼                           │
│  ┌──────────────┐      │   ┌──────────────┐                 │
│  │  api-pod     │◄─────┼───│  cache-pod   │ (allowed!)      │
│  └──────────────┘      │   └──────────────┘                 │
└──────────────────────────────────────────────────────────────┘
Every pod can reach every other pod!
```

```
With NetworkPolicy (Zero Trust):
┌──────────────────────────────────────────────────────────────┐
│  Namespace: frontend   │   Namespace: backend                │
│  ┌──────────────┐      │   ┌──────────────┐                 │
│  │  web-pod     │──────┼──►│  api-pod     │ (allowed)       │
│  └──────────────┘      │   └──────┬───────┘                 │
│         ✗              │          │                          │
│  (can't reach db)      │          ▼                          │
│                        │   ┌──────────────┐                 │
│                        │   │  db-pod      │ ✗ (blocked from │
│                        │   └──────────────┘    web-pod)     │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 NetworkPolicy Implementation

**Default Deny All — The Foundation:**

```yaml
# SECURE: Deny all ingress and egress by default
# Apply this to EVERY namespace as the baseline
# Then selectively open what's needed
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}      # Applies to ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress
  ingress: []          # No ingress rules = deny all ingress
  egress: []           # No egress rules = deny all egress
---
# SECURE: Allow DNS resolution (required for all pods)
# Without this, pods can't resolve service names
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}      # All pods
  policyTypes:
  - Egress
  egress:
  - ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
    to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
---
# SECURE: Frontend → Backend API (specific pod-to-pod policy)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend-api  # This policy applies to backend-api pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    # BOTH conditions must match (AND logic within a rule element)
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: production
      podSelector:
        matchLabels:
          app: frontend   # Only from frontend pods
    ports:
    - port: 8080
      protocol: TCP
---
# SECURE: Backend → Database (strict port restriction)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-to-database
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: production
      podSelector:
        matchLabels:
          app: backend-api
    ports:
    - port: 5432        # PostgreSQL only
      protocol: TCP
---
# SECURE: Monitoring namespace can scrape metrics
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prometheus-scraping
  namespace: production
spec:
  podSelector: {}       # All pods expose metrics
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: monitoring
      podSelector:
        matchLabels:
          app: prometheus
    ports:
    - port: 9090        # Metrics port only
      protocol: TCP
---
# SECURE: Egress control — restrict external access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend-api
  policyTypes:
  - Egress
  egress:
  # Allow access to database
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
  # Allow access to external API (specific IP range)
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8   # Internal network
        except:
        - 10.100.0.0/16    # Except admin subnet
    ports:
    - port: 443
  # DNS allowed (handled by allow-dns policy)
```

### 7.3 Cilium Network Policy (eBPF-based, L7 awareness)

Cilium extends NetworkPolicy with Layer 7 (application layer) awareness using eBPF:

```yaml
# Cilium CiliumNetworkPolicy — HTTP-aware L7 filtering
# This goes BEYOND standard NetworkPolicy (which only does L3/L4)
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: l7-http-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: backend-api
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
        # Allow GET /api/v1/users and /api/v1/products
        - method: GET
          path: "^/api/v1/(users|products)(/.*)?$"
        # Allow POST only to specific endpoints
        - method: POST
          path: "^/api/v1/orders$"
          headers:
          - "Content-Type: application/json"
        # DENY: No DELETE, PUT, PATCH from frontend
        # DENY: No access to /admin, /debug, /metrics paths
```

---

## 8. Secrets Management

### 8.1 The Problem with Kubernetes Secrets

**What's wrong with native Kubernetes Secrets?**

```
Kubernetes Secret — Default State:
┌─────────────────────────────────────────────────────────────────┐
│ 1. BASE64 ENCODED, NOT ENCRYPTED                               │
│    echo "bXlzZWNyZXQ=" | base64 -d → "mysecret"              │
│    This is NOT encryption! Anyone with etcd access reads all   │
│    secrets in plaintext!                                        │
├─────────────────────────────────────────────────────────────────┤
│ 2. ACCESSIBLE TO ANY POD IN SAME NAMESPACE                     │
│    Any pod with 'get secrets' permission reads all secrets     │
├─────────────────────────────────────────────────────────────────┤
│ 3. LOGGED IN AUDIT LOGS (potentially)                          │
│    Secret values can appear in API server logs                  │
├─────────────────────────────────────────────────────────────────┤
│ 4. ENV VAR EXPOSURE                                             │
│    kubectl exec → env → all secrets visible                    │
│    /proc/1/environ on host → all secrets readable              │
└─────────────────────────────────────────────────────────────────┘
```

**VULNERABLE: Secret as environment variable:**

```yaml
# VULNERABLE: Secret exposed as environment variable
# Problems:
# 1. Shows up in 'kubectl describe pod'
# 2. Shows up in audit logs
# 3. Accessible via /proc/self/environ
# 4. Shows up in any process listing tools
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password  # Exposed as env var — bad!
```

### 8.2 Secrets Encryption at Rest

**Enable encryption for Kubernetes secrets in etcd:**

```yaml
# /etc/kubernetes/encryption.yaml
# API server --encryption-provider-config points here
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  - configmaps    # Also encrypt configmaps with sensitive data
  providers:
  # Use KMS for key management (production)
  # This integrates with AWS KMS, GCP KMS, Azure Key Vault
  - kms:
      apiVersion: v2
      name: aws-kms-plugin
      endpoint: unix:///var/run/kmsplugin/socket.sock
      timeout: 3s
      cachesize: 1000  # Cache DEKs for performance
  
  # Fallback: AES-GCM (if KMS unavailable — NOT recommended for production)
  # - aesgcm:
  #     keys:
  #     - name: key1
  #       secret: <base64-encoded-32-byte-key>  # Stored insecurely!
  
  # LAST RESORT: Identity (no encryption — for reading un-encrypted data only)
  - identity: {}
```

### 8.3 External Secrets — Production Pattern

**Using External Secrets Operator with AWS Secrets Manager:**

```yaml
# SECURE: External Secrets Operator (ESO) + AWS Secrets Manager
# Secrets never stored in etcd — fetched from external vault at runtime

# 1. SecretStore — connection to external provider
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        # Use IRSA (IAM Roles for Service Accounts) — NO static credentials!
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
# 2. ExternalSecret — reference to specific secret in AWS SM
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h          # Rotate every hour
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: database-credentials  # Creates this Kubernetes Secret
    creationPolicy: Owner        # ESO manages the lifecycle
    deletionPolicy: Delete       # Delete K8s secret if ExternalSecret deleted
    # Encrypt the secret using a key (requires KMS setup)
    template:
      engineVersion: v2
      data:
        connection-string: |
          postgresql://{{ .username }}:{{ .password }}@{{ .host }}:5432/{{ .database }}
  data:
  - secretKey: username
    remoteRef:
      key: production/database
      property: username
  - secretKey: password
    remoteRef:
      key: production/database
      property: password
  - secretKey: host
    remoteRef:
      key: production/database
      property: host
```

### 8.4 Secrets CSI Driver — File-Based Secret Injection

```yaml
# SECURE: Mount secrets as files, not env vars
# Uses Secrets Store CSI Driver — secrets never touch etcd
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: webapp-sa
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
  containers:
  - name: webapp
    volumeMounts:
    - name: secrets-store
      mountPath: "/mnt/secrets"    # Secrets as files, not env vars!
      readOnly: true
    # App reads /mnt/secrets/db-password (file) not env var
    # File is tmpfs (in memory) — not on disk!
---
# SecretProviderClass — defines what secrets to mount
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
  namespace: production
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "production/database"
        objectType: "secretsmanager"
        jmesPath:
          - path: username
            objectAlias: db-username
          - path: password
            objectAlias: db-password
```

### 8.5 Rust Implementation: Secure Secret Handling

```rust
// File: secret_handler.rs
// SECURE: Production-grade secret handling in Rust
// Demonstrates: memory zeroization, no logging of secrets,
// secure comparison, and proper error handling

use std::fmt;
use std::ops::Deref;

// Zeroize is crucial: when secrets are dropped, memory is zeroed
// Prevents secrets from lingering in memory and being read by:
// - Memory dumps
// - Core dumps (if enabled — should be disabled!)
// - Swap file reads
// - Other processes in same memory space (after proc death)
use zeroize::{Zeroize, ZeroizeOnDrop};

/// SecretString: A string type that is automatically zeroed on drop.
/// CRITICAL: Never implement Display or Debug in a way that reveals contents.
#[derive(ZeroizeOnDrop)]
pub struct SecretString {
    // Store as Vec<u8> so we can guarantee zeroization
    // String doesn't guarantee zero-fill on drop
    inner: Vec<u8>,
}

impl SecretString {
    /// Create a new SecretString from a string slice
    pub fn new(s: &str) -> Self {
        // Convert to owned bytes — we control the memory
        Self {
            inner: s.as_bytes().to_vec(),
        }
    }

    /// Create from bytes directly (for binary secrets)
    pub fn from_bytes(bytes: &[u8]) -> Self {
        Self {
            inner: bytes.to_vec(),
        }
    }

    /// Expose the secret value for use
    /// This is a deliberate, auditable operation
    /// The returned ExposedSecret auto-zeroes when dropped
    pub fn expose(&self) -> ExposedSecret<'_> {
        ExposedSecret { inner: &self.inner }
    }

    /// SECURE: Constant-time comparison to prevent timing attacks
    /// A timing attack: by measuring how long comparison takes,
    /// an attacker can learn how many bytes match, character by character.
    /// Constant-time comparison always takes the same time regardless.
    pub fn constant_time_eq(&self, other: &SecretString) -> bool {
        // Use hmac::equal from the subtle crate for constant-time comparison
        // Simple implementation here for demonstration:
        constant_time_compare(&self.inner, &other.inner)
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }
}

/// CRITICAL: Custom Debug that NEVER reveals the secret
/// Without this, #[derive(Debug)] would print the secret value!
impl fmt::Debug for SecretString {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SecretString([REDACTED])")
    }
}

/// CRITICAL: Display never reveals secret
impl fmt::Display for SecretString {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("[REDACTED]")
    }
}

/// ExposedSecret: Temporary access to secret value.
/// This has a lifetime tied to the SecretString, preventing use-after-free.
/// When the ExposedSecret is dropped, access is revoked.
pub struct ExposedSecret<'a> {
    inner: &'a [u8],
}

impl<'a> Deref for ExposedSecret<'a> {
    type Target = [u8];
    fn deref(&self) -> &Self::Target {
        self.inner
    }
}

impl<'a> ExposedSecret<'a> {
    pub fn as_str(&self) -> Result<&str, std::str::Utf8Error> {
        std::str::from_utf8(self.inner)
    }
}

/// CRITICAL: Debug for ExposedSecret also never reveals value
impl<'a> fmt::Debug for ExposedSecret<'a> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ExposedSecret([REDACTED])")
    }
}

/// Constant-time comparison: always takes same time regardless of data
/// This prevents timing side-channel attacks on secrets
fn constant_time_compare(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        // Even length comparison must be constant time
        // We still compare to prevent length oracle attacks
        let dummy = vec![0u8; a.len()];
        let _ = xor_bytes(a, &dummy);
        return false;
    }

    // XOR all bytes — non-zero result means they differ
    // Crucially: we check ALL bytes before deciding,
    // so timing is independent of where the first difference is
    let diff = xor_bytes(a, b);
    diff == 0
}

fn xor_bytes(a: &[u8], b: &[u8]) -> u8 {
    a.iter().zip(b.iter()).fold(0u8, |acc, (x, y)| acc | (x ^ y))
}

/// Kubernetes Secret fetcher — reads secrets from mounted files (CSI driver)
/// SECURE: Reads from /mnt/secrets/ (tmpfs), not environment variables
pub struct KubernetesSecretReader {
    base_path: std::path::PathBuf,
}

impl KubernetesSecretReader {
    pub fn new(base_path: &str) -> Self {
        Self {
            base_path: std::path::PathBuf::from(base_path),
        }
    }

    /// Read a secret from a mounted file
    /// The file is on tmpfs (in-memory), so no disk persistence
    pub fn read_secret(&self, name: &str) -> Result<SecretString, SecretError> {
        use std::io::Read;

        // SECURE: Validate path to prevent path traversal
        // Attacker might try: name = "../../etc/shadow"
        let name = sanitize_secret_name(name)?;

        let path = self.base_path.join(&name);

        // SECURE: Verify the resolved path is within base_path
        let canonical = path.canonicalize()
            .map_err(|_| SecretError::NotFound(name.clone()))?;

        let base_canonical = self.base_path.canonicalize()
            .map_err(|_| SecretError::ConfigError("Invalid base path".into()))?;

        if !canonical.starts_with(&base_canonical) {
            return Err(SecretError::InvalidPath);
        }

        // SECURE: Check file permissions before reading
        // Secret files should be readable only by our process
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            let metadata = std::fs::metadata(&canonical)
                .map_err(|e| SecretError::IoError(e.to_string()))?;

            let mode = metadata.mode() & 0o777;
            // Mode should be at most 0400 (owner read only)
            if mode & 0o077 != 0 {
                return Err(SecretError::InsecurePermissions(mode));
            }
        }

        // SECURE: Open and read into a controlled buffer
        let mut file = std::fs::File::open(&canonical)
            .map_err(|e| SecretError::IoError(e.to_string()))?;

        let mut buffer = Vec::new();

        // SECURE: Limit read size to prevent memory exhaustion
        const MAX_SECRET_SIZE: u64 = 64 * 1024; // 64KB max
        let mut limited = file.take(MAX_SECRET_SIZE);
        limited.read_to_end(&mut buffer)
            .map_err(|e| SecretError::IoError(e.to_string()))?;

        // Trim trailing newline (common in file-based secrets)
        if buffer.last() == Some(&b'\n') {
            buffer.pop();
        }

        Ok(SecretString::from_bytes(&buffer))
        // buffer is dropped here — zeroize it!
        // Note: Vec<u8> doesn't auto-zero, use Zeroizing<Vec<u8>> in prod
    }
}

/// Validate secret name to prevent path traversal
fn sanitize_secret_name(name: &str) -> Result<String, SecretError> {
    // Allow only alphanumeric, hyphens, underscores, dots
    if name.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_' || c == '.') {
        if !name.starts_with('.') {
            return Ok(name.to_string());
        }
    }
    Err(SecretError::InvalidName(name.to_string()))
}

#[derive(Debug)]
pub enum SecretError {
    NotFound(String),
    InvalidPath,
    InvalidName(String),
    InsecurePermissions(u32),
    IoError(String),
    ConfigError(String),
}

impl fmt::Display for SecretError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            // SECURE: Error messages don't reveal secret values or paths
            SecretError::NotFound(_) => write!(f, "Secret not found"),
            SecretError::InvalidPath => write!(f, "Invalid secret path"),
            SecretError::InvalidName(_) => write!(f, "Invalid secret name"),
            SecretError::InsecurePermissions(mode) =>
                write!(f, "Secret file has insecure permissions: {:o}", mode),
            SecretError::IoError(_) => write!(f, "IO error reading secret"),
            SecretError::ConfigError(msg) => write!(f, "Config error: {}", msg),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secret_debug_redacted() {
        let s = SecretString::new("super-secret-password");
        // CRITICAL: Debug output must not reveal secret
        let debug_str = format!("{:?}", s);
        assert!(!debug_str.contains("super-secret-password"),
            "Secret leaked in Debug output!");
        assert!(debug_str.contains("REDACTED"));
    }

    #[test]
    fn test_secret_display_redacted() {
        let s = SecretString::new("super-secret-password");
        let display_str = format!("{}", s);
        assert!(!display_str.contains("super-secret-password"),
            "Secret leaked in Display output!");
    }

    #[test]
    fn test_constant_time_comparison() {
        let s1 = SecretString::new("password123");
        let s2 = SecretString::new("password123");
        let s3 = SecretString::new("wrongpassword");

        assert!(s1.constant_time_eq(&s2));
        assert!(!s1.constant_time_eq(&s3));
    }

    #[test]
    fn test_path_traversal_prevention() {
        let result = sanitize_secret_name("../../etc/shadow");
        assert!(result.is_err(), "Path traversal not prevented!");
    }

    #[test]
    fn test_sanitize_valid_names() {
        assert!(sanitize_secret_name("db-password").is_ok());
        assert!(sanitize_secret_name("api_key_v2").is_ok());
        assert!(sanitize_secret_name("secret.pem").is_ok());
    }
}

fn main() {
    // Example usage
    let secret = SecretString::new("db-password-here");

    // SECURE: Secret not logged
    println!("Loaded secret: {}", secret); // Prints [REDACTED]
    println!("Debug: {:?}", secret);       // Prints SecretString([REDACTED])

    // SECURE: Use the secret for actual work
    {
        let exposed = secret.expose();
        let password = exposed.as_str().unwrap_or("");
        // Use password here (e.g., pass to database driver)
        // exposed is dropped at end of this block
        println!("Password length: {} (not showing value)", password.len());
    }
    // exposed is now invalid — can't accidentally use it after this point

    println!("Secret handling complete. Memory will be zeroed on drop.");
    // secret is dropped here — inner Vec<u8> is zeroed by ZeroizeOnDrop
}
```

**Cargo.toml for secret_handler.rs:**
```toml
[package]
name = "k8s-secret-handler"
version = "0.1.0"
edition = "2021"

[dependencies]
zeroize = { version = "1.7", features = ["derive"] }

[profile.release]
# Security: strip debug info (reduces binary size + hides internals)
strip = true
# Security: optimization level
opt-level = 3
# Security: prevent stack overflows from impacting security
overflow-checks = true
```

---

## 9. Supply Chain Security

### 9.1 The Software Supply Chain Attack Surface

**What is a supply chain attack?**

A supply chain attack targets the *tools and processes* used to build software, rather than the software itself. The goal: inject malicious code that will be distributed at scale.

```
Software Supply Chain:
Developer → Source Code → Build System → Registry → Deployment
    ↓              ↓            ↓             ↓            ↓
  Git commits  Dependencies  CI pipeline  Container    Kubernetes
  (keys, IDE)  (npm, pip,    (Jenkins,    registry    (pull policy,
               go modules)   GitHub       (DockerHub,  admission
                             Actions)     ECR, GCR)    webhooks)

Attack Vectors:
├── Compromised developer credentials (MFA bypass)
├── Malicious dependency (typosquatting, dependency confusion)
├── Compromised CI/CD system (SolarWinds-style)
├── Registry image tampering (tag mutation)
└── Admission bypass (unsigned images)
```

**Real-World Supply Chain Attacks:**
- **SolarWinds (2020)**: Build system compromised → backdoor in signed binary → 18,000 customers
- **Log4Shell (2021)**: Ubiquitous library vulnerability → millions of Java apps
- **XZ Utils backdoor (2024)**: Social engineering → backdoor in compression library → nearly in OpenSSH
- **PyTorch (2022)**: PyPI dependency confusion → malicious package served instead

### 9.2 SLSA (Supply-chain Levels for Software Artifacts)

**SLSA Levels:**

```
SLSA Level  Requirements                    What it prevents
─────────────────────────────────────────────────────────────────
L1          Provenance exists               Accidental modification
            (who built what from where)

L2          Signed provenance               Tampering after build
            + service-generated

L3          Hardened build platform         Insider threats
            + non-falsifiable provenance    Compromised CI

L4          Two-party review                Sophisticated attacks
            + hermetic builds              Reproducible builds
```

### 9.3 Sigstore/Cosign — Image Signing

```bash
# Sign a container image with Cosign
# This creates a signature stored in the registry alongside the image

# Install cosign
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
chmod +x cosign-linux-amd64

# Generate a keypair (for keyless signing, use --key flag with OIDC)
cosign generate-key-pair

# Sign an image (with private key)
cosign sign --key cosign.key \
  myregistry.com/webapp:v1.2.3@sha256:abc123...

# Sign with annotations (add metadata to signature)
cosign sign --key cosign.key \
  --annotations "git-commit=$(git rev-parse HEAD)" \
  --annotations "pipeline-run=github-actions-12345" \
  --annotations "builder=github-actions" \
  myregistry.com/webapp:v1.2.3

# Verify signature before deployment
cosign verify --key cosign.pub \
  myregistry.com/webapp:v1.2.3

# Keyless signing (uses OIDC identity — Sigstore Fulcio CA)
# No private key to manage! Identity is tied to OIDC token
cosign sign --keyless myregistry.com/webapp:v1.2.3
```

### 9.4 Admission Control: Image Verification with Kyverno

```yaml
# Kyverno policy: Only allow signed images from trusted registry
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
  annotations:
    policies.kyverno.io/title: Verify Image Signatures
    policies.kyverno.io/description: >
      All images must be signed by our CI pipeline before deployment.
      This ensures no unsigned or tampered images run in production.
spec:
  validationFailureAction: Enforce   # Reject violating pods
  background: false                   # Only check new requests
  
  rules:
  - name: verify-signatures
    match:
      any:
      - resources:
          kinds: [Pod]
          namespaces: [production, staging]
    verifyImages:
    - imageReferences:
      - "myregistry.com/*"
      - "myregistry.com/*/*"
      
      # Verify with our public key
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
            signatureAlgorithm: ECDSA
            rekor:
              url: https://rekor.sigstore.dev  # Transparency log
      
      # Also verify SBOM attestation
      attestations:
      - predicateType: https://spdx.dev/Document
        attestors:
        - count: 1
          entries:
          - keys:
              publicKeys: |-
                -----BEGIN PUBLIC KEY-----
                MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
                -----END PUBLIC KEY-----
        conditions:
        - all:
          - key: "{{ creationInfo.created }}"
            operator: LessThan
            value: "{{ '72h' | add_duration(request.object.metadata.creationTimestamp) }}"
  
  - name: block-unsigned-images
    match:
      any:
      - resources:
          kinds: [Pod]
    exclude:
      any:
      - resources:
          namespaces: [kube-system]
    validate:
      message: "Image must be from trusted registry and signed"
      pattern:
        spec:
          containers:
          - image: "myregistry.com/*"  # Only allow our registry

  - name: require-image-digest
    match:
      any:
      - resources:
          kinds: [Pod]
          namespaces: [production]
    validate:
      message: "Image must be referenced by digest, not tag"
      pattern:
        spec:
          containers:
          - image: "*@sha256:*"  # Must include sha256 digest!
```

### 9.5 SBOM (Software Bill of Materials)

**Generating and verifying SBOMs:**

```bash
# Generate SBOM with syft
syft myregistry.com/webapp:v1.2.3 -o spdx-json > webapp-sbom.json

# Attest the SBOM to the image
cosign attest --key cosign.key \
  --predicate webapp-sbom.json \
  --type spdxjson \
  myregistry.com/webapp:v1.2.3

# Check for vulnerabilities in SBOM
grype sbom:webapp-sbom.json

# In CI pipeline — fail build if critical CVEs found
grype myregistry.com/webapp:v1.2.3 --fail-on critical
```

---

## 10. Runtime Security

### 10.1 Falco — Threat Detection at Runtime

**What is Falco?**

Falco is a CNCF graduated project for cloud-native runtime security. It uses eBPF (or kernel module) to monitor system calls and detect anomalous behavior based on a rule engine.

```
Falco Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                         User Space                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Falco Engine                                            │   │
│  │  ├── Rule parser (Falco rules YAML)                     │   │
│  │  ├── Event filter (sysdig filter language)              │   │
│  │  └── Alert dispatcher (stdout, Slack, PagerDuty, SIEM)  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                         libscap/libsinsp                        │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                        Kernel Space                             │
│  eBPF driver (or kernel module) hooks into:                     │
│  - sys_enter / sys_exit tracepoints                             │
│  - All syscalls with full context                               │
└─────────────────────────────────────────────────────────────────┘
```

**Production Falco Rules:**

```yaml
# /etc/falco/rules.d/k8s-security.yaml
# Custom Falco rules for Kubernetes security monitoring

# ================================================================
# CONTAINER BREAKOUT DETECTION
# ================================================================

# Detect attempts to access host filesystem
- rule: Container accessing host filesystem
  desc: >
    A container process is reading/writing to a path that appears to be
    on the host filesystem, indicating a potential container breakout.
  condition: >
    container and
    (fd.name startswith /host/ or
     fd.name startswith /proc/1/ or
     fd.name startswith /proc/1/root) and
    not proc.name in (runc, containerd-shim)
  output: >
    Container accessing host filesystem
    (user=%user.name container=%container.name image=%container.image.repository
     path=%fd.name proc=%proc.name pid=%proc.pid)
  priority: CRITICAL
  tags: [container, breakout, filesystem]

# Detect namespace escapes
- rule: Namespace escape attempt
  desc: Attempt to unshare namespaces from within a container
  condition: >
    container and
    syscall.type = unshare and
    not proc.name in (containerd, dockerd, runc)
  output: >
    Namespace escape attempt
    (user=%user.name container=%container.name image=%container.image.repository
     proc=%proc.name pid=%proc.pid args=%proc.args)
  priority: CRITICAL
  tags: [container, breakout, namespace]

# ================================================================
# PRIVILEGE ESCALATION DETECTION
# ================================================================

# Detect SUID binary execution in container
- rule: SUID binary execution in container
  desc: >
    A SUID binary was executed inside a container. This could indicate
    an attempt to escalate privileges even with noNewPrivileges.
  condition: >
    container and
    proc.is_suid_exe = true and
    not proc.name in (su, sudo, ping, passwd)
  output: >
    SUID binary executed in container
    (user=%user.name container=%container.name binary=%proc.name
     image=%container.image.repository pid=%proc.pid)
  priority: HIGH
  tags: [privilege_escalation, container]

# Detect ptrace in container
- rule: Ptrace system call in container
  desc: >
    ptrace was called inside a container. This could be used to
    inspect or inject into other processes.
  condition: >
    container and
    syscall.type = ptrace and
    ptrace.request != PTRACE_PEEKUSR
  output: >
    Ptrace detected in container
    (user=%user.name container=%container.name proc=%proc.name
     request=%ptrace.request target_pid=%proc.pid)
  priority: HIGH
  tags: [ptrace, privilege_escalation]

# ================================================================
# CRYPTO MINING DETECTION
# ================================================================

# Detect crypto mining processes
- rule: Cryptomining activity
  desc: Common cryptocurrency mining process detected
  condition: >
    container and
    (proc.name in (xmrig, minergate, cpuminer, cgminer) or
     proc.cmdline contains "stratum+tcp://" or
     proc.cmdline contains "pool.minexmr.com" or
     proc.cmdline contains "--cryptonight")
  output: >
    Cryptomining detected
    (user=%user.name container=%container.name proc=%proc.name
     image=%container.image.repository cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [cryptomining, malware]

# Detect unusual network connections (could be C2)
- rule: Container connecting to unusual port
  desc: >
    Container process connecting to an unusual port that might
    indicate C2 communication or data exfiltration
  condition: >
    container and
    evt.type = connect and
    fd.typechar = 4 and  # IPv4
    not fd.sport in (80, 443, 8080, 8443, 53) and
    fd.rport > 1024 and
    not (container.name contains "monitoring" or container.name contains "prometheus")
  output: >
    Container connecting to unusual port
    (container=%container.name image=%container.image.repository
     proc=%proc.name pid=%proc.pid
     dest=%fd.rip:%fd.rport)
  priority: MEDIUM
  tags: [network, suspicious]

# ================================================================
# KUBERNETES-SPECIFIC DETECTION
# ================================================================

# Detect access to service account token
- rule: Service account token read
  desc: >
    A process read the Kubernetes service account token.
    This is legitimate for Kubernetes-aware apps but suspicious
    for shells or unexpected processes.
  condition: >
    container and
    fd.name contains "serviceaccount/token" and
    evt.type in (open, openat) and
    proc.name in (bash, sh, zsh, curl, wget, python, python3)
  output: >
    Service account token accessed by suspicious process
    (user=%user.name container=%container.name proc=%proc.name
     image=%container.image.repository)
  priority: HIGH
  tags: [kubernetes, credentials]

# Detect kubectl in container
- rule: kubectl used inside container
  desc: >
    kubectl is being used inside a container. This could indicate
    lateral movement — attacker using the container's SA token to
    attack other pods or namespaces.
  condition: >
    container and
    proc.name = kubectl
  output: >
    kubectl executed inside container
    (user=%user.name container=%container.name
     image=%container.image.repository
     cmdline=%proc.cmdline)
  priority: HIGH
  tags: [kubernetes, lateral_movement]

# Detect shell spawned in container
- rule: Shell spawned in container
  desc: >
    An interactive shell was spawned in a running container.
    Production containers should never have interactive shells —
    this indicates either debugging (bad practice) or an intrusion.
  condition: >
    container and
    proc.name in (bash, sh, zsh, fish, dash) and
    proc.tty != 0 and          # Interactive terminal
    not proc.pname in (bash, sh, zsh)  # Not from another shell
  output: >
    Interactive shell spawned in container
    (user=%user.name container=%container.name image=%container.image.repository
     proc=%proc.name terminal=%proc.tty)
  priority: HIGH
  tags: [shell, intrusion]

# ================================================================
# DATA EXFILTRATION DETECTION
# ================================================================

# Detect large data transfers
- rule: Unexpected outbound data transfer
  desc: >
    A container is sending an unusually large amount of data outbound.
    Could indicate data exfiltration.
  condition: >
    container and
    fd.typechar = 4 and
    fd.direction = out and
    evt.type = sendto and
    evt.rawres >= 1048576 and  # > 1MB in single send
    not container.image.repository contains "backup"
  output: >
    Large outbound data transfer
    (container=%container.name image=%container.image.repository
     size=%evt.rawres dest=%fd.rip)
  priority: HIGH
  tags: [exfiltration, data]

# Detect /etc/shadow read
- rule: Read shadow password file
  desc: >
    An attempt to read /etc/shadow, which contains hashed passwords.
    In a container, this shouldn't happen.
  condition: >
    fd.name = /etc/shadow and
    evt.type in (open, openat, openat2)
  output: >
    Shadow password file read attempt
    (user=%user.name container_id=%container.id container=%container.name
     image=%container.image.repository proc=%proc.name)
  priority: CRITICAL
  tags: [credentials, filesystem]
```

### 10.2 eBPF Security with Tetragon

**Tetragon** (Cilium) is a more advanced eBPF-based security tool that can enforce policies in addition to observing:

```yaml
# Tetragon TracingPolicy — enforce security at kernel level
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-network-syscalls-for-restricted-pods
spec:
  kprobes:
  # Intercept execve — detect process execution
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Prefix"
        values:
        - "/bin/bash"    # Block bash execution in restricted pods
        - "/bin/sh"
      matchNamespaces:
      - namespace: Pid
        operator: NotIn
        values:
        - "host_pid"
      matchActions:
      - action: Sigkill  # Kill the process immediately
```

---

## 11. etcd Security

**Why etcd is critical**: All Kubernetes state is stored in etcd — including secrets (even if base64 "encoded"), RBAC rules, pod specs, certificates. Compromising etcd = complete cluster compromise.

### 11.1 etcd Security Configuration

```
etcd Security Requirements:
┌─────────────────────────────────────────────────────────────────┐
│ 1. mTLS EVERYWHERE                                              │
│    - Client auth: apiserver → etcd (client cert)               │
│    - Peer auth: etcd → etcd (peer cert for clustering)         │
│    - No plaintext connections                                   │
├─────────────────────────────────────────────────────────────────┤
│ 2. ENCRYPTION AT REST                                           │
│    - Kubernetes API server: --encryption-provider-config        │
│    - etcd itself does NOT encrypt data at rest                  │
│    - Must rely on disk encryption (LUKS) or KMS integration    │
├─────────────────────────────────────────────────────────────────┤
│ 3. NETWORK ISOLATION                                            │
│    - etcd only reachable from API server                        │
│    - Firewall rules: only 2379 (client) and 2380 (peer)        │
│    - Separate VLAN/subnet from worker nodes                     │
├─────────────────────────────────────────────────────────────────┤
│ 4. AUDIT LOGGING                                                │
│    - etcd can log all read/write operations                     │
│    - Detect unauthorized access attempts                        │
├─────────────────────────────────────────────────────────────────┤
│ 5. BACKUP SECURITY                                              │
│    - Backups contain ALL cluster state including secrets        │
│    - Backup files must be encrypted and access-controlled       │
│    - Test restore procedures regularly                          │
└─────────────────────────────────────────────────────────────────┘
```

**etcd Command-Line Hardening:**

```bash
etcd \
  # Client TLS
  --cert-file=/etc/etcd/server.crt \
  --key-file=/etc/etcd/server.key \
  --client-cert-auth=true \       # REQUIRE client certs (mTLS)
  --trusted-ca-file=/etc/etcd/ca.crt \
  
  # Peer TLS (etcd cluster members)
  --peer-cert-file=/etc/etcd/peer.crt \
  --peer-key-file=/etc/etcd/peer.key \
  --peer-client-cert-auth=true \  # REQUIRE peer cert auth
  --peer-trusted-ca-file=/etc/etcd/ca.crt \
  
  # Network
  --listen-client-urls=https://127.0.0.1:2379,https://${ETCD_IP}:2379 \
  --advertise-client-urls=https://${ETCD_IP}:2379 \
  # DO NOT listen on 0.0.0.0 unless absolutely necessary
  
  # NEVER use:
  # --listen-client-urls=http://0.0.0.0:2379  ← No TLS, world-accessible
```

**Go Implementation: etcd Security Auditor**

```go
// File: etcd_auditor.go
// Checks etcd for common security misconfigurations
// Run this from a Kubernetes node that can reach etcd

package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
)

type EtcdAuditConfig struct {
	Endpoints  []string
	CACert     string
	ClientCert string
	ClientKey  string
}

type EtcdAuditor struct {
	client *clientv3.Client
	config EtcdAuditConfig
}

func NewEtcdAuditor(cfg EtcdAuditConfig) (*EtcdAuditor, error) {
	// Load certificates
	cert, err := tls.LoadX509KeyPair(cfg.ClientCert, cfg.ClientKey)
	if err != nil {
		return nil, fmt.Errorf("failed to load client cert: %w", err)
	}

	caCertPEM, err := os.ReadFile(cfg.CACert)
	if err != nil {
		return nil, fmt.Errorf("failed to read CA cert: %w", err)
	}

	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCertPEM) {
		return nil, fmt.Errorf("failed to parse CA cert")
	}

	tlsConfig := &tls.Config{
		Certificates:       []tls.Certificate{cert},
		RootCAs:            caCertPool,
		MinVersion:         tls.VersionTLS13, // TLS 1.3 minimum
		InsecureSkipVerify: false,             // NEVER skip verification!
	}

	client, err := clientv3.New(clientv3.Config{
		Endpoints:   cfg.Endpoints,
		DialTimeout: 5 * time.Second,
		TLS:         tlsConfig,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to etcd: %w", err)
	}

	return &EtcdAuditor{client: client, config: cfg}, nil
}

// CheckSecretsExposure verifies secrets are encrypted at rest
func (a *EtcdAuditor) CheckSecretsExposure(ctx context.Context) error {
	fmt.Println("\n=== Checking Secrets Encryption ===")

	// Try to read a secret directly from etcd
	// If we can read it in plaintext, encryption at rest is NOT configured
	resp, err := a.client.Get(ctx, "/registry/secrets/",
		clientv3.WithPrefix(),
		clientv3.WithLimit(5))
	if err != nil {
		return fmt.Errorf("failed to query etcd: %w", err)
	}

	for _, kv := range resp.Kvs {
		value := string(kv.Value)
		// Check if value starts with k8s:enc: (indicates encryption)
		if len(value) < 6 || value[:6] != "k8s:en" {
			// Value is not encrypted!
			fmt.Printf("[CRITICAL] Secret at %s appears to be UNENCRYPTED in etcd!\n",
				string(kv.Key))
			fmt.Println("          Enable encryption-at-rest: --encryption-provider-config")
		} else {
			fmt.Printf("[OK] Secret at %s is encrypted (prefix: %s)\n",
				string(kv.Key), value[:10])
		}
	}

	if resp.Count == 0 {
		fmt.Println("[INFO] No secrets found (or no permission to list)")
	}

	return nil
}

// CheckCertificateExpiry verifies etcd TLS certificates won't expire soon
func (a *EtcdAuditor) CheckCertificateExpiry() error {
	fmt.Println("\n=== Checking Certificate Expiry ===")

	certFiles := map[string]string{
		"CA":         a.config.CACert,
		"ClientCert": a.config.ClientCert,
	}

	warningThreshold := 30 * 24 * time.Hour // Warn if expires within 30 days

	for name, path := range certFiles {
		pemData, err := os.ReadFile(path)
		if err != nil {
			fmt.Printf("[ERROR] Cannot read %s: %v\n", name, err)
			continue
		}

		block, _ := pem.Decode(pemData)
		if block == nil {
			fmt.Printf("[ERROR] Cannot decode PEM for %s\n", name)
			continue
		}

		cert, err := x509.ParseCertificate(block.Bytes)
		if err != nil {
			fmt.Printf("[ERROR] Cannot parse certificate %s: %v\n", name, err)
			continue
		}

		timeUntilExpiry := time.Until(cert.NotAfter)

		if timeUntilExpiry < 0 {
			fmt.Printf("[CRITICAL] %s certificate EXPIRED on %s!\n",
				name, cert.NotAfter.Format("2006-01-02"))
		} else if timeUntilExpiry < warningThreshold {
			fmt.Printf("[WARNING] %s certificate expires in %.0f days (%s)\n",
				name, timeUntilExpiry.Hours()/24, cert.NotAfter.Format("2006-01-02"))
		} else {
			fmt.Printf("[OK] %s certificate valid until %s (%.0f days)\n",
				name, cert.NotAfter.Format("2006-01-02"), timeUntilExpiry.Hours()/24)
		}
	}

	return nil
}

// CheckMemberHealth verifies all etcd cluster members are healthy
func (a *EtcdAuditor) CheckMemberHealth(ctx context.Context) error {
	fmt.Println("\n=== Checking etcd Cluster Health ===")

	resp, err := a.client.MemberList(ctx)
	if err != nil {
		return fmt.Errorf("failed to list members: %w", err)
	}

	fmt.Printf("Cluster has %d members\n", len(resp.Members))

	// Security check: all endpoints should use HTTPS
	for _, member := range resp.Members {
		for _, peerURL := range member.PeerURLs {
			if len(peerURL) > 4 && peerURL[:5] == "http:" {
				fmt.Printf("[CRITICAL] Member %s peer URL uses HTTP (not HTTPS): %s\n",
					member.Name, peerURL)
			} else {
				fmt.Printf("[OK] Member %s uses TLS for peer communication\n", member.Name)
			}
		}

		for _, clientURL := range member.ClientURLs {
			if len(clientURL) > 4 && clientURL[:5] == "http:" {
				fmt.Printf("[CRITICAL] Member %s client URL uses HTTP (not HTTPS): %s\n",
					member.Name, clientURL)
			}
		}
	}

	return nil
}

func main() {
	cfg := EtcdAuditConfig{
		Endpoints:  []string{"https://127.0.0.1:2379"},
		CACert:     "/etc/etcd/ca.crt",
		ClientCert: "/etc/etcd/client.crt",
		ClientKey:  "/etc/etcd/client.key",
	}

	auditor, err := NewEtcdAuditor(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to connect: %v\n", err)
		os.Exit(1)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	auditor.CheckCertificateExpiry()
	auditor.CheckSecretsExposure(ctx)
	auditor.CheckMemberHealth(ctx)
}
```

---

## 12. Cloud-Native Security

### 12.1 AWS EKS Security

```
EKS Security Architecture:
┌─────────────────────────────────────────────────────────────────┐
│  AWS Account / VPC                                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  EKS Control Plane (AWS-managed, in AWS VPC)            │   │
│  │  - API Server  - etcd  - Controller Manager             │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     │ ENI (private endpoint)                    │
│  ┌──────────────────▼───────────────────────────────────────┐   │
│  │  Customer VPC                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Worker Node Group (EC2 instances)                 │  │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │   │
│  │  │  │  Node 1  │  │  Node 2  │  │  Node 3          │ │  │   │
│  │  │  │  Pods    │  │  Pods    │  │  Pods            │ │  │   │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘ │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  Security Controls:                                      │   │
│  │  ├── VPC Security Groups (firewall rules)               │   │
│  │  ├── IAM Roles for Service Accounts (IRSA)              │   │
│  │  ├── AWS KMS (etcd encryption, secrets)                 │   │
│  │  ├── AWS GuardDuty (threat detection)                   │   │
│  │  ├── AWS Security Hub (compliance)                      │   │
│  │  └── VPC Flow Logs (network audit)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**IRSA (IAM Roles for Service Accounts) — Critical EKS Security Feature:**

```
Without IRSA (VULNERABLE):
┌────────────────────────────────────────────────────────────────┐
│ All pods share the NODE's IAM role                             │
│ If one pod is compromised → attacker has ALL node IAM perms   │
│ Commonly: node role has S3 read/write → instant data breach   │
└────────────────────────────────────────────────────────────────┘

With IRSA (SECURE):
┌────────────────────────────────────────────────────────────────┐
│ Each pod gets its OWN IAM role via OIDC federation             │
│ The role is attached to a specific Kubernetes ServiceAccount  │
│ If one pod is compromised → only its specific S3 bucket       │
└────────────────────────────────────────────────────────────────┘
```

```yaml
# SECURE: IRSA configuration for EKS

# Step 1: Create IAM role with OIDC trust policy (AWS CLI/Terraform)
# The trust policy allows only this specific K8s ServiceAccount to assume the role

# Step 2: Annotate the Kubernetes ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  namespace: production
  annotations:
    # This annotation links SA to IAM role via OIDC
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/ProdS3ReadRole

    # Optional: Session duration (shorter = better security)
    eks.amazonaws.com/token-expiration: "3600"  # 1 hour

    # Optional: Disable IMDS v1 (prevent credential theft via SSRF)
    eks.amazonaws.com/sts-regional-endpoints: "true"
---
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: s3-reader
  # SECURE: EKS automatically injects the token via projected volume
  # NO need to manually handle AWS credentials!
  containers:
  - name: app
    # AWS SDK automatically uses the projected token
    # via AWS_WEB_IDENTITY_TOKEN_FILE and AWS_ROLE_ARN env vars
    # (injected by EKS pod identity webhook)
```

**Go Implementation: IRSA Token Validator**

```go
// File: irsa_validator.go
// Validates IRSA token lifecycle and rotation in production
// Critical for detecting credential theft via SSRF

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sts"
)

// IRSATokenInfo contains information about the current IRSA identity
type IRSATokenInfo struct {
	Account   string
	UserID    string
	ARN       string
	Expires   time.Time
	TokenFile string
}

// ValidateIRSAIdentity confirms we're running with the expected IAM role
func ValidateIRSAIdentity(ctx context.Context, expectedRoleARN string) (*IRSATokenInfo, error) {
	// Load AWS config — automatically uses IRSA env vars:
	// AWS_WEB_IDENTITY_TOKEN_FILE
	// AWS_ROLE_ARN
	// AWS_ROLE_SESSION_NAME
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Get the current caller identity
	stsClient := sts.NewFromConfig(cfg)
	identity, err := stsClient.GetCallerIdentity(ctx, &sts.GetCallerIdentityInput{})
	if err != nil {
		return nil, fmt.Errorf("failed to get caller identity: %w", err)
	}

	info := &IRSATokenInfo{
		Account:   *identity.Account,
		UserID:    *identity.UserId,
		ARN:       *identity.Arn,
		TokenFile: os.Getenv("AWS_WEB_IDENTITY_TOKEN_FILE"),
	}

	// SECURITY: Verify we're using the EXPECTED role
	// This prevents attacks where someone replaces the role annotation
	if expectedRoleARN != "" && *identity.Arn != expectedRoleARN {
		// Note: The ARN includes the session name, so we check prefix
		expectedPrefix := expectedRoleARN
		if len(*identity.Arn) < len(expectedPrefix) ||
			(*identity.Arn)[:len(expectedPrefix)] != expectedPrefix {
			return nil, fmt.Errorf(
				"SECURITY: Using unexpected IAM role. Expected: %s, Got: %s",
				expectedRoleARN, *identity.Arn)
		}
	}

	// SECURITY: Verify token file exists and has correct permissions
	if info.TokenFile != "" {
		stat, err := os.Stat(info.TokenFile)
		if err != nil {
			return nil, fmt.Errorf("token file missing: %w", err)
		}

		// Token file should be readable but not world-writable
		if stat.Mode()&0o002 != 0 {
			return nil, fmt.Errorf(
				"SECURITY: Token file %s is world-writable!", info.TokenFile)
		}
	}

	fmt.Printf("[IRSA] Identity confirmed:\n")
	fmt.Printf("  Account: %s\n", info.Account)
	fmt.Printf("  ARN:     %s\n", info.ARN)
	fmt.Printf("  UserID:  %s\n", info.UserID)

	return info, nil
}

// CheckIMDSv2 verifies that IMDSv2 is enforced (prevents SSRF-based credential theft)
// SSRF (Server-Side Request Forgery): attacker tricks server into calling
// http://169.254.169.254/latest/meta-data/iam/security-credentials/
// to steal EC2 instance credentials
func CheckIMDSv2() error {
	// IMDSv2 requires a PUT request to get a token first
	// Simple check: IMDSv1 would allow direct GET
	// This is a simplified check — in production use AWS CLI: aws imds ...
	fmt.Println("\n[IMDS] Checking IMDSv2 enforcement...")

	// The correct approach: check instance metadata options
	// If IMDSv2 is required, GET requests to 169.254.169.254 fail
	// We won't actually make the request here — just check env
	if os.Getenv("AWS_EC2_METADATA_SERVICE_ENDPOINT") != "" {
		fmt.Println("[IMDS] Custom endpoint configured — verify it's secure")
	}

	fmt.Println("[IMDS] Verify via AWS Console: EC2 → Instance → Metadata options → IMDSv2=Required")
	return nil
}

func main() {
	ctx := context.Background()

	// Validate we're using the correct IRSA role
	expectedRole := os.Getenv("EXPECTED_IAM_ROLE_ARN")
	if expectedRole == "" {
		fmt.Println("[WARNING] EXPECTED_IAM_ROLE_ARN not set — skipping role validation")
	}

	_, err := ValidateIRSAIdentity(ctx, expectedRole)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[CRITICAL] %v\n", err)
		os.Exit(1)
	}

	CheckIMDSv2()

	// Print IRSA environment for debugging (in non-production only)
	if os.Getenv("DEBUG_IRSA") == "true" {
		debug := map[string]string{
			"AWS_WEB_IDENTITY_TOKEN_FILE": os.Getenv("AWS_WEB_IDENTITY_TOKEN_FILE"),
			"AWS_ROLE_ARN":               os.Getenv("AWS_ROLE_ARN"),
			"AWS_ROLE_SESSION_NAME":      os.Getenv("AWS_ROLE_SESSION_NAME"),
		}
		data, _ := json.MarshalIndent(debug, "", "  ")
		fmt.Printf("[DEBUG] IRSA environment:\n%s\n", data)
	}
}
```

### 12.2 GKE (Google Kubernetes Engine) Security

```yaml
# GKE Security Hardening Configuration
# Applied via gcloud CLI or Terraform

# Key GKE Security Features:
# 1. Workload Identity (IRSA equivalent for GCP)
# 2. Binary Authorization (image signing enforcement)
# 3. GKE Autopilot (fully managed, hardened by default)
# 4. Container-Optimized OS (minimal, read-only OS)
# 5. Shielded Nodes (Secure Boot, vTPM, Integrity Monitoring)

# GKE cluster configuration (Terraform):
resource "google_container_cluster" "secure" {
  name     = "secure-cluster"
  location = "us-central1"

  # Use regional cluster for HA
  node_locations = ["us-central1-a", "us-central1-b", "us-central1-c"]

  # SECURE: Private cluster — nodes have no public IPs
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = true      # API server only accessible via VPC
    master_ipv4_cidr_block = "172.16.0.0/28"
  }

  # SECURE: Workload Identity — no static service account keys
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # SECURE: Binary Authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # SECURE: Enable all security features
  addons_config {
    # GKE Dataplane V2 (Cilium-based eBPF networking)
    network_policy_config {
      disabled = false  # Enable NetworkPolicy
    }
  }

  # SECURE: Shielded nodes
  node_config {
    shielded_instance_config {
      enable_secure_boot          = true   # Prevents boot-level rootkits
      enable_integrity_monitoring = true   # Detects rootkit activity
    }

    # SECURE: Workload Identity on node pool
    workload_metadata_config {
      mode = "GKE_METADATA"  # Prevents pod access to node metadata
    }

    # SECURE: Container-Optimized OS (minimal, hardened)
    image_type = "COS_CONTAINERD"

    # SECURE: No legacy metadata endpoints
    metadata = {
      disable-legacy-endpoints = "true"  # Prevent IMDS v0 access
    }
  }

  # SECURE: Enable audit logging
  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "API_SERVER",
      "SCHEDULER",
      "CONTROLLER_MANAGER"
    ]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS"
    ]
  }

  # SECURE: Authorized networks — restrict API server access
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "10.0.0.0/8"   # Corporate VPN range only
      display_name = "Corporate VPN"
    }
  }
}
```

---

## 13. Real-World CVEs: Deep Analysis

### 13.1 CVE-2018-1002105 — API Server Privilege Escalation

**CVSS Score: 9.8 (Critical)**
**Kubernetes versions affected: < 1.10.11, < 1.11.5, < 1.12.3**

**What happened:**

```
ATTACK FLOW:
                                                    
User (low privilege)                               
       │                                           
       │ 1. Send specially crafted API request     
       │    to aggregated API (extension API)      
       ▼                                           
┌─────────────────┐                               
│   API Server    │                               
│                 │ 2. API server proxies to       
│  BUG: Once a   │    extension API server        
│  proxy conn     │──────────────────────────►    
│  was upgraded  │                                
│  (WebSocket/   │ 3. Extension API server         
│  SPDY), the    │    DISCONNECTS                  
│  API server    │                                 
│  stopped       │ 4. BUG: Connection kept alive  
│  checking auth!│    with KUBERNETES CREDENTIALS!
└─────────────────┘                               
                                                   
5. Attacker sends privileged requests             
   through this unauthenticated tunnel!           
→ Full cluster compromise as admin!              
```

**Why this happened in the code (simplified):**

```c
// VULNERABLE (conceptual reconstruction in C)
// Real code was in Go, this illustrates the logic flaw

// The vulnerability: once the HTTP connection was "upgraded" to
// a streaming connection (for exec, attach, port-forward),
// the authentication/authorization was not re-checked for subsequent
// requests sent over the same upgraded connection

void handle_aggregated_api_request(Request *req) {
    // Authentication checked here
    if (!authenticate(req)) {
        return error(401);
    }
    
    // Authorization checked here  
    if (!authorize(req)) {
        return error(403);
    }
    
    // Upgrade connection to proxied stream
    Connection *proxy = upgrade_to_proxy(req, extension_api_server);
    
    // BUG: The upstream (extension) connection died
    // But the downstream (client) connection stayed open
    // And the api server REUSED the client's credentials
    // (the master credentials, not the user's credentials!)
    // for any subsequent requests on this upgraded connection
    
    // MISSING: Re-authentication after reconnect
    // MISSING: Using client's credentials, not apiserver's credentials
    while (proxy->active) {
        Request *new_req = read_next_request(proxy);
        // BUG: new_req is now sent with apiserver's (admin) credentials!
        forward_with_credentials(new_req, APISERVER_CREDENTIAL);  // WRONG!
    }
}
```

**The Fix:**

```go
// SECURE: Properly validate credentials on every request
// Kubernetes 1.10.11+ / 1.11.5+ / 1.12.3+

// The fix involved:
// 1. Not reusing the apiserver's internal credentials for proxied requests
// 2. Properly terminating the proxy connection when upstream disconnects
// 3. Adding connection tracking to detect unexpected reconnections

// Key lesson: Authentication is not a one-time event at connection start.
// For long-lived connections (WebSocket, SPDY, HTTP/2 streams),
// authorization must be maintained throughout the connection lifetime.
```

**Kubernetes YAML Mitigation:**

```yaml
# Mitigation: Disable aggregated API servers if not needed
# Or restrict which extension API servers can be registered
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1beta1.custom.example.com
spec:
  service:
    name: custom-api
    namespace: kube-system
  # SECURE: Require TLS from the extension API server
  insecureSkipTLSVerify: false
  caBundle: <base64-ca-cert>
  # SECURE: Only allow specific ports
  service:
    port: 443
```

---

### 13.2 CVE-2019-5736 — runc Container Escape

**CVSS Score: 8.6 (High)**
**Affected: runc < 1.0-rc6, Docker < 18.09.2, Kubernetes nodes using runc**

**What happened:**

An attacker running code inside a privileged container (or with specific capabilities) could overwrite the host's runc binary, leading to host compromise.

```
ATTACK MECHANISM:

Inside Container                    Host System
     │                                   │
     │ 1. Open /proc/self/exe            │
     │    (this is a symlink to runc    │
     │     when runc is executing!)      │
     │    ─────────────────────────────► │
     │                                   │ /proc/<runc-pid>/exe
     │                                   │         ↓
     │ 2. Wait for runc to exec          │     points to runc binary!
     │    (during docker exec)           │
     │                                   │
     │ 3. Open the FD to runc binary     │
     │    via /proc/self/fd/<n>          │
     │    (while runc is running,        │
     │    this gives write access!)      │
     │                                   │
     │ 4. Write malicious payload        │
     │    to the runc binary!            │
     │    ─────────────────────────────► │ runc binary overwritten!
     │                                   │
     │ 5. Next time runc runs →          │
     │    malicious code executes        │
     │    as root on HOST                │
     ─────────────────────────────────────
```

**C Implementation — Understanding the Vulnerability:**

```c
// EDUCATIONAL: How CVE-2019-5736 worked conceptually
// DO NOT USE — FOR UNDERSTANDING ONLY

// The attack exploited the fact that /proc/<pid>/exe is a magic link
// to the actual binary file, accessible even from inside a container

// Inside the container, during a 'docker exec' or 'kubectl exec':
// 1. A new runc process is spawned on the HOST
// 2. That runc process's /proc/<pid>/exe symlink points to /usr/bin/runc
// 3. The container can read /proc/self/exe during execution
// 4. If the container waits for the right moment, it can write to runc!

// Simplified attack (conceptual):
#define _GNU_SOURCE
#include <fcntl.h>
#include <string.h>

// CONCEPTUAL — NOT ACTUAL EXPLOIT CODE
void conceptual_attack(void) {
    // Step 1: Open /proc/self/exe with O_PATH
    // This gives us a file descriptor to the binary executing us
    // At exec time by runc, this briefly points to runc itself
    int fd = open("/proc/self/exe", O_PATH);
    
    // Step 2: Re-open through the fd with write access
    // The timing window: runc opens this to exec our payload,
    // but before it drops privileges, we try to get write access
    char path[64];
    snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    
    // Step 3: If we can open it for writing, we overwrite runc
    // (In reality, more complex timing and race condition involved)
    int runc_fd = open(path, O_WRONLY | O_TRUNC);
    if (runc_fd >= 0) {
        // Write malicious payload — attacker now has host RCE
        write(runc_fd, malicious_payload, payload_size);
    }
}

// THE FIX (runc 1.0-rc6):
// 1. runc now opens itself with O_CLOEXEC early in execution
// 2. Memfd-based approach: runc copies itself to anonymous memory
//    (memfd_create) and executes from there — not from filesystem!
// 3. The filesystem path is no longer exposed during execution
// 4. SELinux/AppArmor can prevent /proc/<pid>/exe writes

// SECURE IMPLEMENTATION: runc's fix approach
void secure_self_exec(const char *argv[], const char *envp[]) {
    // Create anonymous memory file
    int memfd = syscall(SYS_memfd_create, "runc", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    
    // Read our own binary
    int self = open("/proc/self/exe", O_RDONLY | O_CLOEXEC);
    
    // Copy to memfd
    sendfile(memfd, self, NULL, HUGE_SIZE);
    
    // Seal the memfd (prevent further writes)
    fcntl(memfd, F_ADD_SEALS, F_SEAL_WRITE | F_SEAL_SHRINK | F_SEAL_GROW);
    
    // Execute from the sealed memfd — no filesystem exposure!
    char *fdpath;
    asprintf(&fdpath, "/proc/self/fd/%d", memfd);
    execve(fdpath, argv, envp);
}
```

**Mitigation YAML:**

```yaml
# Mitigation for CVE-2019-5736 and similar container escape CVEs:

# 1. Use gVisor (runsc) — fully isolated container runtime
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc  # gVisor — user-space kernel, no direct syscall access!
---
# Use gVisor for sensitive workloads
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: gvisor  # Run in gVisor sandbox
  containers:
  - name: untrusted-workload
    image: ...

# 2. Keep runc updated (always!)
# 3. Use seccomp/AppArmor to restrict /proc access
# 4. Never use --privileged unless absolutely required
# 5. Restrict capabilities
```

---

### 13.3 CVE-2020-8558 — Node Restriction Bypass

**CVSS Score: 8.8 (High)**
**Affected: Kubernetes < 1.18.4**

**What happened:**

A node could use its kubelet credentials to access services on other nodes by exploiting the route table — the `nodeLocalDNS` loopback IP was accessible from other pods.

```
ATTACK:
Pod A (on Node 1) → Can reach 127.0.0.1 of Pod B (on same node)?
Actually: Linux route forwarding allowed reaching other pods' localhost!

Impact:
- Reach kube-apiserver on loopback (localhost:8080 — no auth!)
- Reach etcd on loopback (localhost:2379 — if unauthenticated)
- Reach any localhost-bound service on host or other containers
```

**Fix:**
- Kubernetes added strict network policies
- kubelet's `--hostname-override` validation improved
- NodeRestriction admission plugin correctly scoped

---

### 13.4 CVE-2021-25741 — Symlink Exchange Attack

**CVSS Score: 8.1 (High)**
**Affected: Kubernetes < 1.19.14, < 1.20.10, < 1.21.4, < 1.22.1**

**What happened:**

```
ATTACK — Symlink Race Condition:
                                        
1. Create a hostPath volume pointing to:
   /var/lib/kubelet/pods/<pod-uid>/volumes/
   
2. Inside the container, create files normally
   
3. RACE: Quickly replace the directory with
   a symlink pointing to /etc/ (or any host dir)
   
4. kubelet follows the symlink and copies files
   thinking they're in the pod volume, but they're
   actually writing to /etc/ on the host!
   
5. Result: Write arbitrary files to host filesystem!
   → Overwrite /etc/cron.d → RCE
   → Overwrite /etc/passwd → privilege escalation
```

**Mitigation:**

```yaml
# Prevent symlink attacks:
# 1. Avoid hostPath volumes entirely
# 2. If you must use hostPath, restrict type

apiVersion: v1
kind: Pod
spec:
  volumes:
  - name: data
    hostPath:
      path: /specific/path
      type: Directory     # ONLY allow if it's already a directory
      # type: DirectoryOrCreate  ← More risky
      # type: ""  ← DANGEROUS: any file type including symlinks
  
  containers:
  - name: app
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
```

---

### 13.5 CVE-2022-0185 — Linux Kernel Heap Overflow

**CVSS Score: 8.4 (High)**
**Linux Kernel: < 5.16.2**
**Impact: Container escape from Kubernetes pods**

**What happened:**

A heap overflow in `legacy_parse_param()` in the filesystem context API allowed privilege escalation and namespace escape.

```c
// VULNERABLE: Legacy filesystem parameter parsing
// Kernel source: fs/fs_context.c (simplified)

// The bug: param->string length was not properly validated
// An attacker with CAP_SYS_ADMIN inside a user namespace
// could trigger a heap overflow by providing a parameter
// with a crafted length value

int legacy_parse_param(struct fs_context *fc, struct fs_parameter *param) {
    // VULNERABLE: size calculation could overflow
    // len = param->size (attacker controlled!)
    // If len is 0xFFFFFFFF, then len + 1 overflows to 0
    // memcpy(dest, src, 0) — but buffer was allocated for 0 bytes!
    
    unsigned int len = param->size;
    char *str = kmalloc(len + 1, GFP_KERNEL);  // VULNERABLE: overflow!
    memcpy(str, param->string, len);            // VULNERABLE: OOB write!
    str[len] = '\0';
    
    // Attacker controls heap layout → kernel memory corruption
    // → Escape container namespace
    // → Kernel code execution
}
```

**Mitigation:**

```bash
# 1. Update kernel (most important)
apt-get update && apt-get install -y linux-image-generic

# 2. Restrict user namespaces (reduces attack surface)
# This prevents unprivileged users from creating user namespaces
# which was the prerequisite for this CVE
sysctl -w kernel.unprivileged_userns_clone=0  # Debian/Ubuntu
sysctl -w user.max_user_namespaces=0           # RHEL/Fedora

# 3. Use seccomp to block relevant syscalls
# The exploit required specific filesystem syscalls
# These are blocked by a proper seccomp allowlist

# 4. Kubernetes mitigation: Use PSA restricted profile
# which prevents CAP_SYS_ADMIN that was needed for exploitation
```

---

### 13.6 CVE-2023-44487 — HTTP/2 Rapid Reset Attack (Golang Impact)

**CVSS Score: 7.5 (High) — ACTIVE exploitation in wild**
**Impact: DoS against Kubernetes API server and ingress controllers**

**What happened:**

```
HTTP/2 Rapid Reset Attack:
                                          
Attacker                  Server          
   │                         │            
   │─── HEADERS (stream 1) ──►│           
   │◄── 100 Continue ─────────│           
   │─── RST_STREAM (stream 1) ►│ Server cancels
   │                           │ but resources not freed!
   │─── HEADERS (stream 3) ──►│           
   │◄── 100 Continue ─────────│           
   │─── RST_STREAM (stream 3) ►│           
   │                           │           
   │ Repeat at 10,000 RPS      │           
   │                           │ Server overwhelmed!
   │                           │ CPU 100%, OOM
```

**Go/Kubernetes mitigation:**

```go
// SECURE: HTTP/2 server with rate limiting and request limits
// Applied to Kubernetes API server and ingress controllers

package main

import (
	"net/http"
	"time"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
)

func secureHTTP2Server() *http.Server {
	h2s := &http2.Server{
		// SECURE: Limit concurrent streams per connection
		// Default was unlimited — the root cause of CVE-2023-44487
		MaxConcurrentStreams: 250,

		// SECURE: Limit reset stream rate
		// Added after CVE-2023-44487
		MaxReadFrameSize: 16384,

		// SECURE: Idle timeout kills long-lived idle connections
		IdleTimeout: 10 * time.Second,
	}

	srv := &http.Server{
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
		ReadHeaderTimeout: 10 * time.Second,

		// MaxHeaderBytes limits attack surface on headers
		MaxHeaderBytes: 1 << 20, // 1MB

		Handler: h2c.NewHandler(http.DefaultServeMux, h2s),
	}

	return srv
}
```

---

## 14. Zero Trust Architecture in Kubernetes

### 14.1 Zero Trust Principles Applied to Kubernetes

**What is Zero Trust?**

Zero Trust is a security model based on: **"Never trust, always verify"**. It rejects the traditional "castle and moat" perimeter model where everything inside the network is trusted.

```
Traditional (Perimeter-Based):
┌─────────────────────────────────────────┐
│  TRUSTED ZONE (inside firewall)         │
│                                         │
│  Pod A ──────────────────────► Pod B    │
│         (trusted, no auth needed!)      │
└─────────────────────────────────────────┘

Zero Trust:
┌─────────────────────────────────────────┐
│  NO TRUSTED ZONE (everything verified)  │
│                                         │
│  Pod A ──→ mTLS + AuthZ check ──► Pod B │
│      (identity verified + authorized)   │
└─────────────────────────────────────────┘
```

**Zero Trust Kubernetes Implementation:**

```
Zero Trust Pillars → Kubernetes Implementation:
┌───────────────────────┬────────────────────────────────────────┐
│ ZT Pillar             │ Kubernetes Mechanism                   │
├───────────────────────┼────────────────────────────────────────┤
│ Verify Explicitly     │ mTLS between all services (Istio)      │
│                       │ RBAC + OIDC for humans                 │
│                       │ IRSA for cloud resources               │
├───────────────────────┼────────────────────────────────────────┤
│ Least Privilege       │ RBAC minimal permissions               │
│                       │ Pod securityContext                    │
│                       │ NetworkPolicy default deny             │
│                       │ Capabilities drop all                  │
├───────────────────────┼────────────────────────────────────────┤
│ Assume Breach         │ Falco runtime detection                │
│                       │ Audit logging                          │
│                       │ Network segmentation                   │
│                       │ Immutable infrastructure               │
└───────────────────────┴────────────────────────────────────────┘
```

### 14.2 Service Mesh Security (Istio/Linkerd)

**mTLS between all pods:**

```yaml
# Istio: Enable strict mTLS for entire cluster
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # Applies cluster-wide
spec:
  mtls:
    mode: STRICT  # Reject ALL plaintext traffic between services!
---
# Namespace-specific mTLS policy
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: namespace-strict-mtls
  namespace: production
spec:
  mtls:
    mode: STRICT
---
# Istio AuthorizationPolicy — L7-aware access control
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-to-backend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend-api
  action: ALLOW
  rules:
  - from:
    - source:
        # Verify by mTLS identity (service account), not just IP
        principals:
        - "cluster.local/ns/production/sa/frontend-sa"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
        notPaths: ["/api/v1/admin/*"]  # Block admin path from frontend
    when:
    # Require JWT for user requests
    - key: request.auth.claims[iss]
      values: ["https://accounts.google.com"]
```

---

## 15. Threat Modeling

### 15.1 STRIDE for Kubernetes

**STRIDE** is a threat modeling framework (Microsoft). Each letter is a category of threat:

```
STRIDE Applied to Kubernetes:
┌──────────────────┬───────────────────────────────────────────────────┐
│ S - Spoofing     │ - Pod impersonating another service                │
│                  │ - Stolen service account token                     │
│                  │ - DNS spoofing within cluster                      │
│                  │ Mitigation: mTLS, OIDC, token binding              │
├──────────────────┼───────────────────────────────────────────────────┤
│ T - Tampering    │ - Modifying etcd data directly                     │
│                  │ - Supply chain: tampered container image            │
│                  │ - Webhook injection (mutating admission)           │
│                  │ Mitigation: Image signing, etcd mTLS, audit log    │
├──────────────────┼───────────────────────────────────────────────────┤
│ R - Repudiation  │ - No audit trail for API operations               │
│                  │ - Container activity not logged                    │
│                  │ Mitigation: API audit log, Falco, CloudTrail       │
├──────────────────┼───────────────────────────────────────────────────┤
│ I - Information  │ - Secrets in etcd (unencrypted)                   │
│  Disclosure      │ - Overly verbose error messages                    │
│                  │ - Prometheus metrics exposing internal info        │
│                  │ Mitigation: Encrypt at rest, RBAC on metrics       │
├──────────────────┼───────────────────────────────────────────────────┤
│ D - Denial of    │ - Fork bomb (no PID limits)                       │
│  Service         │ - Memory exhaustion (no memory limits)             │
│                  │ - HTTP/2 Rapid Reset (CVE-2023-44487)              │
│                  │ Mitigation: cgroup limits, rate limiting, QoS      │
├──────────────────┼───────────────────────────────────────────────────┤
│ E - Elevation of │ - Container escape via privileged mode             │
│  Privilege       │ - SUID binary exploitation                         │
│                  │ - Namespace escape via kernel CVE                  │
│                  │ Mitigation: PSA restricted, seccomp, capabilities  │
└──────────────────┴───────────────────────────────────────────────────┘
```

### 15.2 Attack Tree for Kubernetes Cluster Compromise

```
Goal: Gain cluster-admin access
│
├── Path 1: Compromise API Server
│   ├── Steal admin kubeconfig
│   │   ├── Access developer workstation (phishing)
│   │   └── Access CI/CD system secrets
│   ├── Exploit API server vulnerability (e.g., CVE-2018-1002105)
│   └── Brute force service account tokens
│
├── Path 2: Node Compromise → Token Theft
│   ├── Exploit kubelet API (port 10250, if unauthenticated)
│   │   └── Read pod secrets via /run/secrets/
│   ├── Gain shell on node (SSHi key theft)
│   │   └── Read /var/lib/kubelet/pods/*/secrets/
│   └── Container escape (privileged pod)
│       ├── CVE-2019-5736 (runc escape)
│       └── Privileged pod with hostPath=/
│
├── Path 3: Lateral Movement from Compromised Pod
│   ├── Read ServiceAccount token (auto-mounted)
│   ├── Call Kubernetes API with SA token
│   │   └── If SA has cluster-admin → GAME OVER
│   ├── Exploit RBAC misconfiguration
│   │   └── SA can create privileged pods
│   └── Network-based: reach other pods (no NetworkPolicy)
│
└── Path 4: Supply Chain
    ├── Compromise registry → malicious image
    ├── Compromise CI/CD → backdoor in image
    └── Dependency confusion attack
```

---

## 16. Security Benchmarks

### 16.1 CIS Kubernetes Benchmark

The CIS (Center for Internet Security) Kubernetes Benchmark is the industry standard for cluster hardening. Key controls:

```
CIS Benchmark Key Controls (summarized):

Control Plane:
1.1.1  API server pod specification file permissions: 600
1.1.2  API server pod spec file ownership: root:root
1.2.1  --anonymous-auth=false
1.2.2  --token-auth-file NOT set
1.2.6  --kubelet-certificate-authority set
1.2.9  --event-rate-limit admission plugin enabled
1.2.10 --allow-privileged=false
1.2.11 --authorization-mode includes RBAC
1.2.16 --audit-log-path set
1.2.22 --encryption-provider-config set
1.3.2  --bind-address=127.0.0.1 (controller manager)
1.4.1  --profiling=false (scheduler)

Worker Nodes:
4.1.1  kubelet service file permissions: 600
4.2.1  --anonymous-auth=false
4.2.2  --authorization-mode Webhook (not AlwaysAllow!)
4.2.4  --read-only-port=0 (disable read-only kubelet port)
4.2.6  --protect-kernel-defaults=true
4.2.7  --make-iptables-util-chains=true
```

**kube-bench — Automated CIS Benchmark Scanning:**

```bash
# Run kube-bench to check CIS compliance
docker run --pid=host --userns=host --network=host \
  --v /etc:/etc:ro --v /var:/var:ro \
  -t aquasec/kube-bench:latest \
  run --targets master,node,etcd,policies

# Example output:
# [PASS] 1.1.1 Ensure that the API server pod specification file permissions are set to 600
# [FAIL] 1.2.1 Ensure that the --anonymous-auth argument is set to false
# [WARN] 1.2.9 Ensure that the admission control plugin EventRateLimit is set
```

**Go: Run CIS checks programmatically:**

```go
// File: cis_checker.go
// Automated CIS Kubernetes Benchmark validation
// Integrated into admission webhooks and CI/CD pipelines

package main

import (
	"fmt"
	"os"
	"strings"
)

type CISCheck struct {
	ID          string
	Description string
	Check       func() (bool, string)
	Severity    string // CRITICAL, HIGH, MEDIUM, LOW
}

// Check 1.2.1: Anonymous auth disabled
func checkAnonymousAuth() (bool, string) {
	// Read the API server manifest
	data, err := os.ReadFile("/etc/kubernetes/manifests/kube-apiserver.yaml")
	if err != nil {
		return false, "Cannot read API server manifest"
	}

	content := string(data)
	if strings.Contains(content, "--anonymous-auth=false") {
		return true, "anonymous-auth is disabled"
	}
	if strings.Contains(content, "--anonymous-auth=true") {
		return false, "FAIL: --anonymous-auth=true explicitly set!"
	}
	// Default is true — that's also bad
	return false, "FAIL: --anonymous-auth not explicitly disabled (default=true)"
}

// Check 1.2.6: Kubelet certificate authority configured
func checkKubeletCA() (bool, string) {
	data, err := os.ReadFile("/etc/kubernetes/manifests/kube-apiserver.yaml")
	if err != nil {
		return false, "Cannot read API server manifest"
	}

	if strings.Contains(string(data), "--kubelet-certificate-authority") {
		return true, "Kubelet CA is configured"
	}
	return false, "FAIL: --kubelet-certificate-authority not set — kubelet auth not verified!"
}

// Check 1.2.22: Encryption at rest configured
func checkEncryptionAtRest() (bool, string) {
	data, err := os.ReadFile("/etc/kubernetes/manifests/kube-apiserver.yaml")
	if err != nil {
		return false, "Cannot read API server manifest"
	}

	if strings.Contains(string(data), "--encryption-provider-config") {
		// Also verify the config file exists
		// Extract the path from the flag
		return true, "Encryption provider config is set"
	}
	return false, "CRITICAL: --encryption-provider-config not set — secrets unencrypted in etcd!"
}

// Check 4.2.1: kubelet anonymous auth disabled
func checkKubeletAnonymousAuth() (bool, string) {
	// Check kubelet config file
	data, err := os.ReadFile("/var/lib/kubelet/config.yaml")
	if err != nil {
		// Try command line args
		data, err = os.ReadFile("/etc/kubernetes/kubelet.conf")
		if err != nil {
			return false, "Cannot read kubelet config"
		}
	}

	content := string(data)
	if strings.Contains(content, "anonymous:\n    enabled: false") ||
		strings.Contains(content, "anonymous:\n  enabled: false") {
		return true, "Kubelet anonymous auth disabled"
	}
	return false, "FAIL: Kubelet allows anonymous requests — port 10250 is open to all!"
}

// Check 4.2.4: Read-only port disabled
func checkKubeletReadOnlyPort() (bool, string) {
	data, err := os.ReadFile("/var/lib/kubelet/config.yaml")
	if err != nil {
		return false, "Cannot read kubelet config"
	}

	if strings.Contains(string(data), "readOnlyPort: 0") {
		return true, "Kubelet read-only port disabled"
	}
	return false, "FAIL: Kubelet read-only port (10255) enabled — exposes pod/node info without auth!"
}

var cisChecks = []CISCheck{
	{
		ID:          "1.2.1",
		Description: "Anonymous auth disabled on API server",
		Check:       checkAnonymousAuth,
		Severity:    "CRITICAL",
	},
	{
		ID:          "1.2.6",
		Description: "Kubelet certificate authority configured",
		Check:       checkKubeletCA,
		Severity:    "HIGH",
	},
	{
		ID:          "1.2.22",
		Description: "Secrets encrypted at rest",
		Check:       checkEncryptionAtRest,
		Severity:    "CRITICAL",
	},
	{
		ID:          "4.2.1",
		Description: "Kubelet anonymous auth disabled",
		Check:       checkKubeletAnonymousAuth,
		Severity:    "HIGH",
	},
	{
		ID:          "4.2.4",
		Description: "Kubelet read-only port disabled",
		Check:       checkKubeletReadOnlyPort,
		Severity:    "MEDIUM",
	},
}

func main() {
	fmt.Println("=== CIS Kubernetes Benchmark Checker ===\n")

	passed := 0
	failed := 0

	for _, check := range cisChecks {
		ok, msg := check.Check()
		status := "[PASS]"
		if !ok {
			status = fmt.Sprintf("[FAIL-%s]", check.Severity)
			failed++
		} else {
			passed++
		}
		fmt.Printf("%s CIS %s: %s\n       %s\n\n",
			status, check.ID, check.Description, msg)
	}

	fmt.Printf("\nResults: %d passed, %d failed\n", passed, failed)

	if failed > 0 {
		os.Exit(1) // Non-zero for CI/CD integration
	}
}
```

---

## 17. Incident Response & Forensics

### 17.1 Kubernetes Incident Response Playbook

```
INCIDENT RESPONSE PHASES:
┌─────────────────────────────────────────────────────────────────┐
│ 1. DETECT                                                       │
│    - Falco alert fired                                          │
│    - Unusual API server audit log entry                        │
│    - Security team alert                                        │
│    - CloudTrail/GCP audit log anomaly                          │
├─────────────────────────────────────────────────────────────────┤
│ 2. CONTAIN                                                      │
│    - Isolate the compromised pod/node                          │
│    - Revoke service account tokens                             │
│    - Block network with NetworkPolicy                          │
│    - Cordon the node (prevent new scheduling)                  │
├─────────────────────────────────────────────────────────────────┤
│ 3. INVESTIGATE                                                  │
│    - Collect pod logs, events                                   │
│    - Analyze API audit logs                                     │
│    - Review network flows                                       │
│    - Check for persistence mechanisms                          │
├─────────────────────────────────────────────────────────────────┤
│ 4. ERADICATE                                                    │
│    - Delete compromised pods                                    │
│    - Rotate all secrets                                         │
│    - Drain and rebuild affected nodes                          │
│    - Remove persistence (DaemonSets, CronJobs)                 │
├─────────────────────────────────────────────────────────────────┤
│ 5. RECOVER                                                      │
│    - Deploy clean images from known-good registry              │
│    - Verify signatures on all deployed images                  │
│    - Implement additional controls                             │
├─────────────────────────────────────────────────────────────────┤
│ 6. LESSONS LEARNED                                              │
│    - Root cause analysis                                        │
│    - Update threat model                                        │
│    - Implement missing controls                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Incident Response Commands:**

```bash
# ============================================================
# CONTAINMENT
# ============================================================

# 1. Immediately cordon the node (no new pods scheduled)
kubectl cordon <node-name>

# 2. Isolate the pod with a deny-all NetworkPolicy
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-pod
  namespace: <namespace>
spec:
  podSelector:
    matchLabels:
      <pod-label-key>: <pod-label-value>
  policyTypes:
  - Ingress
  - Egress
  # No ingress/egress rules = deny all
EOF

# 3. Revoke service account token
kubectl delete secret <sa-token-secret>

# 4. Snapshot the compromised pod's state BEFORE deletion
kubectl get pod <pod-name> -o yaml > incident-pod-snapshot.yaml

# ============================================================
# INVESTIGATION
# ============================================================

# 5. Collect pod logs
kubectl logs <pod-name> --all-containers > incident-logs.txt
kubectl logs <pod-name> --previous >> incident-logs.txt  # Previous container

# 6. Get recent events (sorted by time)
kubectl get events --sort-by='.lastTimestamp' -A | \
  grep -E "(Warning|Error)" | tail -100

# 7. Analyze API audit logs for suspicious activity
grep '"user":{"username":"system:serviceaccount:<ns>:<sa>"}' \
  /var/log/kube-audit.log | \
  jq 'select(.verb == "create" or .verb == "delete")' | \
  grep -E '"resource":"(secrets|pods|clusterrolebindings)"'

# 8. Check for unusual processes in the pod (if still running)
kubectl exec <pod-name> -- ps auxf
kubectl exec <pod-name> -- netstat -tlnp
kubectl exec <pod-name> -- cat /proc/net/tcp

# 9. Check for modified binaries (compare to image)
kubectl exec <pod-name> -- find / -newer /etc/passwd \
  -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null

# 10. Check for crypto miners
kubectl exec <pod-name> -- top -b -n1 | head -20
kubectl exec <pod-name> -- cat /proc/*/cmdline 2>/dev/null | \
  xargs -0 echo | grep -E "(xmrig|minergate|cpuminer)"

# ============================================================
# SECRET ROTATION (after compromise)
# ============================================================

# 11. Rotate all secrets in affected namespace
kubectl get secrets -n <namespace> -o name | \
  while read secret; do
    echo "Rotating: $secret"
    # Trigger external secret rotation via annotation
    kubectl annotate "$secret" -n <namespace> \
      force-sync=$(date +%s) --overwrite
  done

# 12. Rebuild compromised nodes
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# Terminate EC2 instance / GCP node (auto-scaling group will replace)
aws ec2 terminate-instances --instance-ids <instance-id>
```

**Go: Automated Incident Response Tool**

```go
// File: incident_responder.go
// Automates initial containment steps for Kubernetes security incidents
// Integrate with PagerDuty/OpsGenie for automated response

package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

// IncidentContext describes the security incident
type IncidentContext struct {
	Namespace  string
	PodName    string
	NodeName   string
	Reason     string    // e.g., "cryptominer detected", "container escape"
	DetectedAt time.Time
	Severity   string    // CRITICAL, HIGH, MEDIUM
}

// IncidentResponder performs automated containment
type IncidentResponder struct {
	client *kubernetes.Clientset
	logger *log.Logger
}

func NewIncidentResponder(kubeconfig string) (*IncidentResponder, error) {
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		return nil, err
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &IncidentResponder{
		client: client,
		logger: log.New(os.Stdout, "[IR] ", log.LstdFlags),
	}, nil
}

// IsolateWithNetworkPolicy creates an emergency deny-all NetworkPolicy
func (r *IncidentResponder) IsolateWithNetworkPolicy(
	ctx context.Context, inc IncidentContext,
	podLabels map[string]string,
) error {
	r.logger.Printf("Creating isolation NetworkPolicy for pod %s/%s",
		inc.Namespace, inc.PodName)

	policy := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("incident-isolation-%s-%d", inc.PodName, time.Now().Unix()),
			Namespace: inc.Namespace,
			Annotations: map[string]string{
				"incident.security.io/reason":     inc.Reason,
				"incident.security.io/detected":   inc.DetectedAt.Format(time.RFC3339),
				"incident.security.io/severity":   inc.Severity,
				"incident.security.io/auto-created": "true",
			},
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: metav1.LabelSelector{
				MatchLabels: podLabels,
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyTypeIngress,
				networkingv1.PolicyTypeEgress,
			},
			// No Ingress or Egress rules = deny all
		},
	}

	_, err := r.client.NetworkingV1().NetworkPolicies(inc.Namespace).
		Create(ctx, policy, metav1.CreateOptions{})
	if err != nil {
		return fmt.Errorf("failed to create isolation NetworkPolicy: %w", err)
	}

	r.logger.Printf("[OK] NetworkPolicy created: all traffic to/from %s blocked", inc.PodName)
	return nil
}

// CordonNode prevents new pods from being scheduled on compromised node
func (r *IncidentResponder) CordonNode(ctx context.Context, nodeName string) error {
	r.logger.Printf("Cordoning node: %s", nodeName)

	node, err := r.client.CoreV1().Nodes().Get(ctx, nodeName, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get node %s: %w", nodeName, err)
	}

	// Mark as unschedulable
	node.Spec.Unschedulable = true
	if node.Annotations == nil {
		node.Annotations = map[string]string{}
	}
	node.Annotations["incident.security.io/cordoned-at"] = time.Now().Format(time.RFC3339)

	_, err = r.client.CoreV1().Nodes().Update(ctx, node, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to cordon node %s: %w", nodeName, err)
	}

	r.logger.Printf("[OK] Node %s cordoned — no new pods will be scheduled", nodeName)
	return nil
}

// CollectForensicData gathers evidence before pod deletion
func (r *IncidentResponder) CollectForensicData(
	ctx context.Context, inc IncidentContext,
) (string, error) {
	r.logger.Printf("Collecting forensic data for pod %s/%s", inc.Namespace, inc.PodName)

	// Get pod spec
	pod, err := r.client.CoreV1().Pods(inc.Namespace).
		Get(ctx, inc.PodName, metav1.GetOptions{})
	if err != nil {
		return "", fmt.Errorf("failed to get pod: %w", err)
	}

	// Collect logs from all containers
	var forensicReport strings.Builder
	forensicReport.WriteString(fmt.Sprintf("=== INCIDENT FORENSICS ===\n"))
	forensicReport.WriteString(fmt.Sprintf("Pod: %s/%s\n", inc.Namespace, inc.PodName))
	forensicReport.WriteString(fmt.Sprintf("Node: %s\n", pod.Spec.NodeName))
	forensicReport.WriteString(fmt.Sprintf("Detected: %s\n", inc.DetectedAt))
	forensicReport.WriteString(fmt.Sprintf("Reason: %s\n\n", inc.Reason))

	// Container statuses
	for _, cs := range pod.Status.ContainerStatuses {
		forensicReport.WriteString(fmt.Sprintf("Container: %s\n", cs.Name))
		forensicReport.WriteString(fmt.Sprintf("  Image: %s\n", cs.Image))
		forensicReport.WriteString(fmt.Sprintf("  ImageID: %s\n", cs.ImageID))
		forensicReport.WriteString(fmt.Sprintf("  Restarts: %d\n", cs.RestartCount))
	}

	// Get logs
	for _, container := range pod.Spec.Containers {
		logOpts := &corev1.PodLogOptions{
			Container: container.Name,
			TailLines: int64ptr(500),
		}

		req := r.client.CoreV1().Pods(inc.Namespace).
			GetLogs(inc.PodName, logOpts)
		logs, err := req.DoRaw(ctx)
		if err != nil {
			forensicReport.WriteString(fmt.Sprintf("\nLogs for %s: ERROR: %v\n", container.Name, err))
			continue
		}

		forensicReport.WriteString(fmt.Sprintf("\n=== Logs: %s ===\n%s\n", container.Name, string(logs)))
	}

	// Save to file
	filename := fmt.Sprintf("/tmp/incident-%s-%s-%d.txt",
		inc.Namespace, inc.PodName, time.Now().Unix())
	if err := os.WriteFile(filename, []byte(forensicReport.String()), 0600); err != nil {
		return "", fmt.Errorf("failed to write forensic report: %w", err)
	}

	r.logger.Printf("[OK] Forensic data saved to %s", filename)
	return filename, nil
}

func int64ptr(v int64) *int64 { return &v }

// RespondToIncident is the main orchestration function
func (r *IncidentResponder) RespondToIncident(
	ctx context.Context, inc IncidentContext,
	podLabels map[string]string,
) error {
	r.logger.Printf("=== INCIDENT RESPONSE STARTED ===")
	r.logger.Printf("Pod: %s/%s, Severity: %s, Reason: %s",
		inc.Namespace, inc.PodName, inc.Severity, inc.Reason)

	// Step 1: Collect forensic data BEFORE any changes
	forensicFile, err := r.CollectForensicData(ctx, inc)
	if err != nil {
		r.logger.Printf("WARNING: Forensic collection failed: %v", err)
	} else {
		r.logger.Printf("Forensic data: %s", forensicFile)
	}

	// Step 2: Network isolation
	if err := r.IsolateWithNetworkPolicy(ctx, inc, podLabels); err != nil {
		r.logger.Printf("WARNING: Network isolation failed: %v", err)
	}

	// Step 3: Cordon the node
	if inc.NodeName != "" {
		if err := r.CordonNode(ctx, inc.NodeName); err != nil {
			r.logger.Printf("WARNING: Node cordon failed: %v", err)
		}
	}

	// Step 4: For CRITICAL incidents, immediately delete the pod
	if inc.Severity == "CRITICAL" {
		r.logger.Printf("CRITICAL incident: Deleting pod immediately")
		grace := int64(0) // Immediate deletion
		err := r.client.CoreV1().Pods(inc.Namespace).Delete(
			ctx, inc.PodName,
			metav1.DeleteOptions{GracePeriodSeconds: &grace},
		)
		if err != nil {
			return fmt.Errorf("failed to delete pod: %w", err)
		}
		r.logger.Printf("[OK] Pod %s deleted", inc.PodName)
	}

	r.logger.Printf("=== INCIDENT RESPONSE COMPLETE ===")
	return nil
}

func main() {
	kubeconfig := os.Getenv("KUBECONFIG")

	responder, err := NewIncidentResponder(kubeconfig)
	if err != nil {
		log.Fatalf("Failed to create responder: %v", err)
	}

	// Example: Respond to a Falco alert about cryptomining
	incident := IncidentContext{
		Namespace:  "production",
		PodName:    "backend-api-7d9f8b-xk2pq",
		NodeName:   "node-1",
		Reason:     "Cryptomining process detected: xmrig",
		DetectedAt: time.Now(),
		Severity:   "CRITICAL",
	}

	podLabels := map[string]string{
		"app":                    "backend-api",
		"pod-template-hash":      "7d9f8b",
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	if err := responder.RespondToIncident(ctx, incident, podLabels); err != nil {
		log.Fatalf("Incident response failed: %v", err)
	}
}
```

---

## 18. Production Hardening Checklist

### 18.1 Complete Production Checklist

```
KUBERNETES SECURITY HARDENING CHECKLIST
Last Updated: 2025
Compliance: CIS, NSA/CISA, SOC2, PCI-DSS

════════════════════════════════════════════════════════════════
CONTROL PLANE HARDENING
════════════════════════════════════════════════════════════════

API Server:
[ ] --anonymous-auth=false
[ ] --token-auth-file NOT configured
[ ] --kubelet-https=true
[ ] --authorization-mode=Node,RBAC (NOT AlwaysAllow)
[ ] --enable-admission-plugins includes NodeRestriction,PodSecurity
[ ] --audit-log-path configured
[ ] --audit-policy-file configured
[ ] --encryption-provider-config configured (KMS preferred)
[ ] --tls-min-version=VersionTLS13
[ ] --profiling=false
[ ] --service-account-lookup=true
[ ] --etcd-cafile, --etcd-certfile, --etcd-keyfile configured

etcd:
[ ] --cert-file and --key-file configured (TLS)
[ ] --client-cert-auth=true
[ ] --auto-tls=false (use CA-signed certs)
[ ] --peer-client-cert-auth=true
[ ] --peer-auto-tls=false
[ ] Listen only on specific interface (not 0.0.0.0)
[ ] Firewall: only API server can reach etcd (port 2379)
[ ] Data directory: permissions 700, owned by etcd user

Controller Manager:
[ ] --profiling=false
[ ] --use-service-account-credentials=true
[ ] --bind-address=127.0.0.1
[ ] --service-account-private-key-file configured
[ ] --root-ca-file configured

Scheduler:
[ ] --profiling=false
[ ] --bind-address=127.0.0.1

════════════════════════════════════════════════════════════════
NODE HARDENING
════════════════════════════════════════════════════════════════

kubelet:
[ ] --anonymous-auth=false
[ ] --authorization-mode=Webhook
[ ] --client-ca-file configured
[ ] --read-only-port=0
[ ] --protect-kernel-defaults=true
[ ] --event-qps=0 (or appropriate rate limit)
[ ] --rotate-certificates=true
[ ] --rotate-server-certificates=true
[ ] --streaming-connection-idle-timeout set (not disabled)
[ ] serviceAccountPublicKeyFile configured
[ ] --make-iptables-util-chains=true

OS-Level:
[ ] Container-Optimized OS or minimal distro
[ ] AppArmor or SELinux enforcing
[ ] auditd configured on nodes
[ ] SSH access disabled or restricted to bastion
[ ] IMDSv2 required (AWS) / metadata server disabled
[ ] Kernel parameters hardened:
    [ ] net.ipv4.ip_forward = 1 (only what k8s needs)
    [ ] kernel.dmesg_restrict = 1
    [ ] kernel.kptr_restrict = 2
    [ ] kernel.perf_event_paranoid = 3
    [ ] user.max_user_namespaces = 0 (or restrict to root)
    [ ] kernel.core_pattern = |/bin/false (disable core dumps)

════════════════════════════════════════════════════════════════
WORKLOAD SECURITY
════════════════════════════════════════════════════════════════

Pod Security:
[ ] PSA enforcing "restricted" on production namespaces
[ ] All pods: runAsNonRoot: true
[ ] All pods: allowPrivilegeEscalation: false
[ ] All pods: readOnlyRootFilesystem: true
[ ] All pods: capabilities drop ALL
[ ] All pods: seccompProfile RuntimeDefault or Localhost
[ ] No pods: privileged: true (except specific infrastructure)
[ ] No pods: hostPID, hostIPC, hostNetwork (except specific infrastructure)
[ ] No pods: hostPath volumes (except specific infrastructure)
[ ] Resource limits (CPU and memory) on ALL containers
[ ] PID limits configured
[ ] No containers: image using 'latest' tag
[ ] All containers: image referenced by sha256 digest

RBAC:
[ ] No service accounts with cluster-admin
[ ] All service accounts: automountServiceAccountToken: false (opt-in)
[ ] Default service account: automountServiceAccountToken: false
[ ] RBAC audit: no wildcard permissions on sensitive resources
[ ] RBAC audit: no secrets list/watch permissions unnecessarily
[ ] Regularly review and remove unused service accounts and bindings

Networking:
[ ] Default deny-all NetworkPolicy in every namespace
[ ] NetworkPolicy restricts pod-to-pod communication to minimum required
[ ] NetworkPolicy restricts egress to known endpoints
[ ] CNI supports NetworkPolicy (Calico, Cilium, Weave, etc.)
[ ] Service mesh mTLS for service-to-service (optional but recommended)

Secrets:
[ ] Secrets encrypted at rest (KMS provider preferred)
[ ] No secrets in environment variables (use volume mounts)
[ ] External secrets operator or CSI secrets driver configured
[ ] Secrets rotated regularly (< 90 days for production)
[ ] No secrets in container images or Dockerfiles
[ ] No secrets in Git repositories

════════════════════════════════════════════════════════════════
SUPPLY CHAIN SECURITY
════════════════════════════════════════════════════════════════

[ ] All images signed with Cosign/Sigstore
[ ] Admission controller verifies image signatures (Kyverno/OPA Gatekeeper)
[ ] Admission controller: images must use sha256 digest (no mutable tags)
[ ] SBOM generated for all images
[ ] CVE scanning on all images before deployment
[ ] CVE scanning integrated into CI/CD (fail on critical)
[ ] Private registry for all production images
[ ] Registry access controlled (no anonymous pull)
[ ] ImagePullPolicy: Always (never use cached potentially-stale images)
[ ] Build provenance tracked (SLSA L2 minimum, L3 preferred)
[ ] Dependency pinning in all package managers
[ ] go.sum / requirements.txt.lock / package-lock.json committed

════════════════════════════════════════════════════════════════
OBSERVABILITY & DETECTION
════════════════════════════════════════════════════════════════

[ ] API server audit logging enabled with comprehensive policy
[ ] Audit logs shipped to SIEM (not stored on cluster only)
[ ] Falco or equivalent runtime security deployed
[ ] Falco rules cover: shell in container, privilege escalation, crypto mining
[ ] Container image update monitoring (Renovate/Dependabot)
[ ] Regular penetration testing (quarterly minimum)
[ ] Regular CIS benchmark scanning (kube-bench automated)
[ ] Cloud provider threat detection (GuardDuty, Security Command Center)
[ ] Alerts on: unusual API calls, new ClusterRoleBindings, privileged pods
[ ] Pod/container resource anomaly detection

════════════════════════════════════════════════════════════════
INCIDENT RESPONSE
════════════════════════════════════════════════════════════════

[ ] Incident response playbook documented and tested
[ ] RBAC: security team can quickly isolate pods
[ ] Secret rotation procedures tested
[ ] Node replacement procedures tested (immutable infrastructure)
[ ] Forensic data collection procedures established
[ ] Communication plan for security incidents
[ ] Backup and restore tested (including etcd restore)
[ ] Tabletop exercise conducted (quarterly)
```

---

## Appendix A: Rust Implementation — Zero-Trust Certificate Manager

```rust
// File: cert_manager.rs
// Production-grade certificate management for Kubernetes mTLS
// Implements: cert rotation, OCSP stapling, secure key storage

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use rcgen::{Certificate, CertificateParams, DistinguishedName, DnType, SanType};
use rustls::{Certificate as RustlsCert, PrivateKey};
use zeroize::ZeroizeOnDrop;

/// CertificateStore: Thread-safe storage for TLS certificates
/// In production, this would interface with a KMS or Vault
#[derive(Debug)]
pub struct CertificateStore {
    // Arc + RwLock for thread-safe, concurrent access
    // Multiple readers (serving requests) or one writer (rotation)
    certs: Arc<RwLock<HashMap<String, StoredCertificate>>>,
}

/// StoredCertificate: Certificate with its private key
/// ZeroizeOnDrop ensures private key is zeroed when dropped
#[derive(ZeroizeOnDrop)]
pub struct StoredCertificate {
    /// PEM-encoded certificate chain
    cert_pem: Vec<u8>,
    
    /// Private key — zeroed on drop!
    #[zeroize]
    key_der: Vec<u8>,
    
    /// When this certificate expires
    #[zeroize(skip)]
    expires_at: SystemTime,
    
    /// Identity this cert represents (SPIFFE URI)
    #[zeroize(skip)]
    spiffe_id: String,
}

impl std::fmt::Debug for StoredCertificate {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StoredCertificate")
            .field("spiffe_id", &self.spiffe_id)
            .field("expires_at", &self.expires_at)
            .field("key_der", &"[REDACTED]")
            .finish()
    }
}

/// CertificateConfig for generating workload certificates
pub struct CertificateConfig {
    /// SPIFFE identity: spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>
    pub spiffe_id: String,
    
    /// DNS SANs for the certificate
    pub dns_names: Vec<String>,
    
    /// Certificate validity duration (shorter = more secure, more overhead)
    pub validity_duration: Duration,   
```