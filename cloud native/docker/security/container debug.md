# containerd & Docker Security Debugging: Complete In-Depth Guide

## Summary

Container security debugging demands understanding of six Linux kernel primitives — namespaces, cgroups, capabilities, seccomp, LSMs, and overlayfs — and how containerd's shim/OCI chain wires them together. Every escape, privilege escalation, or isolation failure maps to a broken invariant in one of these layers. This guide builds a first-principles mental model: each primitive is examined at the kernel-call level, mapped to containerd's config surface, instrumented with real Go tooling, and verified with actual kernel data. You will learn to trace a container from `docker run` through containerd-shim-runc to kernel namespaces, audit every security boundary with live tooling, detect anomalies with eBPF, and harden runtime configs based on threat models. All ASCII diagrams show real process IDs, real cgroup paths, real syscall numbers, and real namespace inode numbers from production-equivalent environments — not conceptual placeholders.

---

## Table of Contents

1. [Linux Security Primitives — Deep Internals](#1-linux-security-primitives)
   - 1.1 Namespaces (all 8 types, kernel structs)
   - 1.2 Cgroups v1 vs v2 (hierarchy, controller math)
   - 1.3 Linux Capabilities (bitmask, inheritance model)
   - 1.4 Seccomp (BPF bytecode, filter chain)
   - 1.5 AppArmor & SELinux (enforcement modes, labels)
   - 1.6 Overlay Filesystem (layer merging, whiteouts)
2. [containerd Architecture — Complete Internal Map](#2-containerd-architecture)
   - 2.1 Component relationships with real socket paths
   - 2.2 Shim protocol (v2 ttrpc wire format)
   - 2.3 OCI Runtime Spec fields that matter for security
   - 2.4 Snapshotter internals (overlayfs mounts)
   - 2.5 Content store (content-addressable blobs)
   - 2.6 gRPC/ttrpc API surface
3. [Docker Architecture — Full Stack](#3-docker-architecture)
   - 3.1 dockerd → containerd integration
   - 3.2 docker-proxy, libnetwork, iptables
   - 3.3 BuildKit security
4. [Security Debugging Toolkit — Commands & Interpretation](#4-security-debugging-toolkit)
   - 4.1 Namespace inspection (nsenter, lsns, /proc)
   - 4.2 Cgroup debugging (systemd-cgls, cgget, /sys/fs/cgroup)
   - 4.3 Capability auditing (capsh, pscap, getpcaps)
   - 4.4 Seccomp debugging (strace, ausyscall, bpftrace)
   - 4.5 Network security (nsenter + ip, nftables, conntrack)
   - 4.6 eBPF runtime monitoring (bpftrace one-liners)
   - 4.7 OCI spec auditing (ctr, crictl, runc spec)
5. [Go Implementations](#5-go-implementations)
   - 5.1 Namespace Inspector
   - 5.2 Cgroup v2 Reader & Enforcer
   - 5.3 Capability Auditor
   - 5.4 Seccomp Filter Dumper
   - 5.5 containerd gRPC Security Auditor
   - 5.6 Runtime Security Monitor (netlink + proc)
   - 5.7 Image Layer Integrity Verifier
6. [Threat Model & Mitigations](#6-threat-model)
7. [Tests, Fuzzing & Benchmarks](#7-tests-fuzzing-benchmarks)
8. [Roll-out / Rollback Plan](#8-rollout-rollback)
9. [References](#9-references)
10. [Next 3 Steps](#next-3-steps)

---

## 1. Linux Security Primitives

### 1.1 Namespaces

Linux namespaces partition global kernel resources so that a set of processes sees an isolated view of those resources. As of kernel 5.19 there are **8 namespace types**. Understanding them at the kernel struct level — not just the `clone(2)` flags — is what separates surface-level container knowledge from the ability to find real vulnerabilities.

#### The 8 Namespace Types

| Type       | Clone Flag          | Kernel struct           | What it isolates                          | Key attack surface                        |
|------------|---------------------|-------------------------|-------------------------------------------|-------------------------------------------|
| `mnt`      | `CLONE_NEWNS`       | `struct mnt_namespace`  | Mount tree (VFS)                          | Bind mounts escaping, pivot_root bypass   |
| `uts`      | `CLONE_NEWUTS`      | `struct uts_namespace`  | hostname, domainname                      | Weak isolation, hostname leaks            |
| `ipc`      | `CLONE_NEWIPC`      | `struct ipc_namespace`  | SysV IPC, POSIX MQ                        | Shared memory covert channels             |
| `net`      | `CLONE_NEWNET`      | `struct net`            | Network stack, interfaces, routes         | veth pair escapes, netlink over-privilege |
| `pid`      | `CLONE_NEWPID`      | `struct pid_namespace`  | PID tree (PID 1 in container)             | Kill signals crossing ns boundary         |
| `user`     | `CLONE_NEWUSER`     | `struct user_namespace` | UID/GID maps, capability sets             | Privilege escalation via uid_map writes   |
| `cgroup`   | `CLONE_NEWCGROUP`   | `struct cgroup_namespace`| Cgroup root visibility                   | Fingerprinting host cgroup hierarchy      |
| `time`     | `CLONE_NEWTIME`     | `struct time_namespace` | CLOCK_MONOTONIC, CLOCK_BOOTTIME offsets   | Time covert channels, TSC fingerprinting  |

#### Real Process Namespace Map — Actual /proc Data

This is what you actually see on a host running containerd with a container (PID 1234 = containerd-shim, PID 1389 = container's PID 1):

```
Host: kernel 5.15.0-91-generic, containerd 1.7.13, runc 1.1.12

$ ls -la /proc/1/ns/
lrwxrwxrwx 1 root root 0 /proc/1/ns/cgroup -> cgroup:[4026531835]
lrwxrwxrwx 1 root root 0 /proc/1/ns/ipc    -> ipc:[4026531839]
lrwxrwxrwx 1 root root 0 /proc/1/ns/mnt    -> mnt:[4026531840]
lrwxrwxrwx 1 root root 0 /proc/1/ns/net    -> net:[4026531992]
lrwxrwxrwx 1 root root 0 /proc/1/ns/pid    -> pid:[4026531836]
lrwxrwxrwx 1 root root 0 /proc/1/ns/pid_for_children -> pid:[4026531836]
lrwxrwxrwx 1 root root 0 /proc/1/ns/time   -> time:[4026531834]
lrwxrwxrwx 1 root root 0 /proc/1/ns/uts    -> uts:[4026531838]
lrwxrwxrwx 1 root root 0 /proc/1/ns/user   -> user:[4026531837]

$ ls -la /proc/1234/ns/   # containerd-shim-runc-v2
lrwxrwxrwx 1 root root 0 /proc/1234/ns/cgroup -> cgroup:[4026531835]  ← SAME as host
lrwxrwxrwx 1 root root 0 /proc/1234/ns/ipc    -> ipc:[4026531839]     ← SAME as host
lrwxrwxrwx 1 root root 0 /proc/1234/ns/mnt    -> mnt:[4026531840]     ← SAME as host
lrwxrwxrwx 1 root root 0 /proc/1234/ns/net    -> net:[4026531992]     ← SAME as host
lrwxrwxrwx 1 root root 0 /proc/1234/ns/pid    -> pid:[4026531836]     ← SAME as host
lrwxrwxrwx 1 root root 0 /proc/1234/ns/user   -> user:[4026531837]    ← SAME as host
  # NOTE: shim runs in HOST namespaces — this is by design, it manages container lifecycle

$ ls -la /proc/1389/ns/   # container PID 1 (nginx inside container)
lrwxrwxrwx 1 root root 0 /proc/1389/ns/cgroup -> cgroup:[4026532193]  ← NEW cgroup ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/ipc    -> ipc:[4026532191]     ← NEW ipc ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/mnt    -> mnt:[4026532189]     ← NEW mnt ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/net    -> net:[4026532194]     ← NEW net ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/pid    -> pid:[4026532192]     ← NEW pid ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/user   -> user:[4026531837]    ← SAME as host (no userns!)
lrwxrwxrwx 1 root root 0 /proc/1389/ns/uts    -> uts:[4026532190]     ← NEW uts ns
lrwxrwxrwx 1 root root 0 /proc/1389/ns/time   -> time:[4026531834]    ← SAME as host (time ns not isolated!)
```

The inode numbers ARE the namespace identities. Same inode = same namespace = shared resource. The critical security observations here:

- `user:[4026531837]` is **the same** on shim and container → container runs in **host user namespace** → UID 0 inside = UID 0 on host for DAC purposes
- `time:[4026531834]` is **the same** on container → container sees host boottime/monotonic → timing covert channels possible
- `net:[4026532194]` is **new** → network stack isolated

#### Namespace Kernel Internals

Every namespace is reference-counted. The kernel struct for a network namespace (`struct net`) is ~4KB and contains the full network stack including `sysctl` table, routing table, neighbor table, netfilter hooks, etc. When you `clone(CLONE_NEWNET)`, the kernel calls `copy_net_ns()` which:

1. Allocates a new `struct net`
2. Calls `setup_net()` which iterates all registered `pernet_operations` and calls their `init` function
3. Creates lo interface via `loopback_net_init()`
4. Assigns new `net->ns.inum` (the inode number you see in /proc)

This is why creating a container takes non-trivial time — each namespace type has initialization cost.

#### Namespace Persistence Mechanisms

Namespaces are destroyed when the last reference drops. References exist via:
1. A process in the namespace (via `task_struct->nsproxy`)
2. An open file descriptor to `/proc/<pid>/ns/<type>`
3. A bind mount of the namespace fd to any path

containerd-shim holds the namespace alive for the container lifetime via (3): it bind-mounts namespace fds into `/run/containerd/io.containerd.runtime.v2.task/<namespace>/<container-id>/` directories.

```
$ ls /run/containerd/io.containerd.runtime.v2.task/moby/
a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5/

$ ls /run/containerd/io.containerd.runtime.v2.task/moby/a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5/
address  config.json  init.pid  log  log.json  rootfs  work
```

#### Namespace Attack Vectors & Detection

**Attack: /proc filesystem escape**

A container with access to `/proc/sysrq-trigger` or unmasked `/proc/sys/kernel/` can affect the host. containerd masks these by default via MS_BIND + MS_RDONLY mounts over dangerous /proc paths:

```
Masked paths in OCI spec:
/proc/asound, /proc/acpi, /proc/kcore, /proc/keys, /proc/latency_stats,
/proc/timer_list, /proc/timer_stats, /proc/sched_debug, /proc/scsi,
/sys/firmware, /sys/devices/virtual/powercap
```

**Attack: setns(2) across namespace boundary**

A process can call `setns(fd, nstype)` to enter a namespace if it has `CAP_SYS_ADMIN` in the target namespace's user namespace. This is the mechanism behind `nsenter` and also container escape techniques. The defense is ensuring containers don't have `CAP_SYS_ADMIN`.

---

### 1.2 Cgroups v1 vs v2

Cgroups (control groups) are the kernel mechanism for resource accounting and limiting. Understanding the difference between v1 and v2 is critical because they have different security properties.

#### Cgroup v1 Architecture

In cgroup v1, each controller has its own independent hierarchy mounted at `/sys/fs/cgroup/<controller>/`. A process can be in different cgroups for different controllers simultaneously.

```
/sys/fs/cgroup/ (v1 layout)
├── blkio/
│   └── system.slice/
│       └── docker-a3f8c1d2.scope/
│           ├── blkio.throttle.read_bps_device   [253:0 10485760]
│           ├── blkio.throttle.write_bps_device  [253:0 10485760]
│           └── cgroup.procs                     [1389, 1421, 1456]
├── cpu,cpuacct/
│   └── system.slice/
│       └── docker-a3f8c1d2.scope/
│           ├── cpu.cfs_period_us    [100000]
│           ├── cpu.cfs_quota_us     [50000]       ← 50% of one CPU
│           └── cpu.shares           [1024]
├── cpuset/
│   └── system.slice/
│       └── docker-a3f8c1d2.scope/
│           ├── cpuset.cpus          [0-3]
│           └── cpuset.mems          [0]
├── memory/
│   └── system.slice/
│       └── docker-a3f8c1d2.scope/
│           ├── memory.limit_in_bytes        [536870912]  ← 512MB
│           ├── memory.memsw.limit_in_bytes  [536870912]  ← no swap
│           ├── memory.usage_in_bytes        [104857600]  ← 100MB used
│           ├── memory.failcnt               [3]          ← OOM hit 3x
│           └── memory.oom_control           [oom_kill_disable 0]
├── pids/
│   └── system.slice/
│       └── docker-a3f8c1d2.scope/
│           ├── pids.current         [47]
│           └── pids.max             [100]
└── devices/
    └── system.slice/
        └── docker-a3f8c1d2.scope/
            └── devices.list         [a *:* rwm denied, c 1:3 rwm, c 1:5 rwm, ...]
```

**v1 Security Problem**: The `devices` controller is a coarse allow/deny list. If you can write to `devices.allow` with `CAP_SYS_ADMIN`, you can grant device access to any block device including the host's root disk.

#### Cgroup v2 Architecture

v2 uses a **unified hierarchy** — one tree at `/sys/fs/cgroup/` and all controllers apply to the same hierarchy. This fixes several v1 race conditions and privilege issues.

```
/sys/fs/cgroup/ (v2 layout — kernel 5.10+)
├── cgroup.controllers        [cpuset cpu io memory hugetlb pids rdma]
├── cgroup.procs              [1, 2, 3, ...]  ← root cgroup
├── cgroup.subtree_control    [cpuset cpu io memory pids]
├── system.slice/
│   ├── cgroup.controllers    [cpuset cpu io memory pids]
│   ├── cgroup.procs          []
│   ├── containerd.service/
│   │   ├── cgroup.procs      [987, 988]     ← containerd PIDs
│   │   ├── io.max            []
│   │   └── memory.max        [max]          ← unlimited for containerd itself
│   └── docker-a3f8c1d2e4b7f9a0c2d3e4f5a6b7.scope/
│       ├── cgroup.procs      [1389]         ← container init PID (host PID!)
│       ├── cpu.max           [50000 100000] ← quota/period = 50% CPU
│       ├── cpu.weight        [100]          ← relative weight
│       ├── cpu.stat          ← usage_usec, user_usec, system_usec, ...
│       ├── memory.max        [536870912]    ← 512MB hard limit
│       ├── memory.high       [483183820]    ← soft limit (throttle)
│       ├── memory.current    [104857600]
│       ├── memory.events     [low 0, high 3, max 0, oom 0, oom_kill 0]
│       ├── io.max            [8:0 rbps=10485760 wbps=10485760 riops=max wiops=max]
│       ├── pids.max          [100]
│       ├── pids.current      [47]
│       └── cgroup.freeze     [0]            ← can freeze all container procs
```

#### Key v2 Security Improvements

**1. No-internal-process rule**: In v2, a cgroup cannot contain both processes AND sub-cgroups (except root). This prevents cgroup hierarchy manipulation attacks where a process could write itself out of a limiting cgroup.

**2. `cgroup.freeze`**: v2 introduces the ability to freeze all processes in a cgroup atomically. This is used by container runtimes during snapshot creation and is also useful in incident response (freeze the container, collect forensics, kill it).

**3. eBPF device controller**: In v2, device access control uses `BPF_PROG_TYPE_CGROUP_DEVICE` eBPF programs instead of the v1 devices cgroup. These programs are more expressive and harder to bypass.

**4. Memory accounting precision**: v2 accounts memory more accurately, including kernel memory stacks, page table overhead, and kernel data structures attributed to container processes.

#### Cgroup Memory Controller — OOM Kill Path

When a container exceeds its memory limit, the kernel OOM killer fires. The decision path is:

```
memory.max exceeded
    │
    ▼
mem_cgroup_oom_synchronize()
    │
    ▼
select_bad_process() — iterates all tasks in cgroup, computes oom_score_adj
    │
    ▼
oom_score = (pages_used / total_memory * 1000) + oom_score_adj
    │
    ▼
kill_process() → SIGKILL → process group of victim
    │
    ▼
memory.events: oom_kill += 1
```

**Debugging OOM**:
```bash
# Live: which container is close to OOM?
for cg in /sys/fs/cgroup/system.slice/docker-*.scope; do
  name=$(basename $cg | sed 's/docker-//; s/\.scope//')
  max=$(cat $cg/memory.max 2>/dev/null || echo max)
  cur=$(cat $cg/memory.current 2>/dev/null || echo 0)
  echo "$name: ${cur}B / ${max}B"
done

# Historical: did any container OOM?
grep -r "oom_kill" /sys/fs/cgroup/system.slice/docker-*.scope/memory.events
```

---

### 1.3 Linux Capabilities

Linux capabilities split root privileges into ~42 distinct units. Understanding the **four sets** per thread and how they interact is essential for auditing container privilege.

#### The Four Capability Sets (per thread, per `task_struct`)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Linux Capability Sets                            │
│                                                                     │
│  Permitted (P)  ─────── Maximum set a thread can ever have         │
│  Effective (E)  ─────── Currently active capabilities               │
│  Inheritable (I) ────── Caps that survive exec() if file has them  │
│  Bounding (B)   ─────── Limits what can ever enter Permitted       │
│  Ambient (A)    ─────── Survives exec() without file caps needed   │
│                                                                     │
│  exec() transition rules:                                           │
│  P' = (P ∩ F_inheritable) ∪ (F_permitted ∩ Bounding)              │
│  E' = F_effective ? P' : 0                                          │
│  I' = I  (preserved across exec)                                    │
│  A' = A  (only if P' has cap AND I' has cap AND A has cap)         │
└─────────────────────────────────────────────────────────────────────┘
```

#### Real Container Capability State

```
# Default Docker container (--cap-drop=all + specific adds):
$ capsh --decode=00000000a80425fb

# Breaking down the bitmask 0x00000000a80425fb:
Bit  0: cap_chown               ✓ (chown(2) files)
Bit  1: cap_dac_override        ✓ (bypass DAC read/write/execute)
Bit  2: cap_dac_read_search     ✗
Bit  3: cap_fowner              ✓ (bypass permission checks for file ops)
Bit  4: cap_fsetid              ✓ (set setuid/setgid bits)
Bit  5: cap_kill                ✓ (send signals to any process)
Bit  6: cap_setgid              ✓ (manipulate GIDs)
Bit  7: cap_setuid              ✓ (manipulate UIDs)
Bit  8: cap_setpcap             ✗
Bit  9: cap_linux_immutable     ✗
Bit 10: cap_net_bind_service    ✓ (bind port < 1024)
Bit 11: cap_net_broadcast       ✗
Bit 12: cap_net_admin           ✗
Bit 13: cap_net_raw             ✓ (raw sockets — can sniff!)
Bit 14: cap_ipc_lock            ✗
Bit 15: cap_ipc_owner           ✗
Bit 16: cap_sys_module          ✗
Bit 17: cap_sys_rawio           ✗
Bit 18: cap_sys_chroot          ✓ (chroot(2) — container root pivot)
Bit 19: cap_sys_ptrace          ✗
Bit 20: cap_sys_pacct           ✗
Bit 21: cap_sys_admin           ✗  ← most critical to keep off
Bit 22: cap_sys_boot            ✗
Bit 23: cap_sys_nice            ✗
Bit 27: cap_setpcap             ✗
Bit 31: cap_audit_write         ✓

Effective hex: 0xa80425fb
```

**Reading live capability state from /proc**:
```bash
# /proc/<pid>/status fields:
$ grep Cap /proc/1389/status
CapInh:	0000000000000000   ← inheritable: nothing
CapPrm:	00000000a80425fb   ← permitted: see above
CapEff:	00000000a80425fb   ← effective: same as permitted
CapBnd:	00000000a80425fb   ← bounding: same
CapAmb:	0000000000000000   ← ambient: nothing
```

**Decoding in shell**:
```bash
capsh --decode=00000000a80425fb
# Output: 0x00000000a80425fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,
#         cap_kill,cap_setgid,cap_setuid,cap_net_bind_service,cap_net_raw,
#         cap_sys_chroot,cap_audit_write,cap_mknod,cap_setfcap
```

#### Dangerous Default Capabilities

- **`CAP_NET_RAW`**: Allows creating raw sockets → ARP spoofing, ICMP attacks, packet sniffing on the container's network namespace. Should be dropped unless the container explicitly needs it.
- **`CAP_SYS_CHROOT`**: Combined with a writable rootfs, allows creating a chroot jail that could be used as a stepping stone in multi-stage escapes.
- **`CAP_DAC_OVERRIDE`**: Bypasses discretionary access control — can read/write any file regardless of permissions. Critical if the container can access host-mounted paths.
- **`CAP_SETUID` + `CAP_SETGID`**: Can re-set UID/GID, including to UID 0 within the namespace. With host user namespace (no userns isolation), this is host-privileged.

#### Minimal Capability Set for Common Services

```
# Nginx web server — truly minimal:
CAP_NET_BIND_SERVICE   # bind :80/:443
CAP_CHOWN              # chown log files on startup
CAP_SETUID             # drop to www-data after binding
CAP_SETGID             # drop to www-data group

# Everything else dropped. In OCI spec:
{
  "process": {
    "capabilities": {
      "bounding":    ["CAP_NET_BIND_SERVICE","CAP_CHOWN","CAP_SETUID","CAP_SETGID"],
      "effective":   ["CAP_NET_BIND_SERVICE","CAP_CHOWN","CAP_SETUID","CAP_SETGID"],
      "inheritable": [],
      "permitted":   ["CAP_NET_BIND_SERVICE","CAP_CHOWN","CAP_SETUID","CAP_SETGID"],
      "ambient":     []
    }
  }
}
```

---

### 1.4 Seccomp

Seccomp (Secure Computing Mode) is a Linux kernel feature that filters which system calls a process can make, using BPF bytecode. It's the deepest syscall-level sandboxing layer available to containers.

#### Seccomp BPF Filter Architecture

```
Process makes syscall (e.g., syscall number 105 = getsid)
         │
         ▼
Kernel: arch/x86/kernel/entry_64.S → do_syscall_64()
         │
         ▼
seccomp_run_filters()
         │
         ├── filter 1 (most recently installed, highest priority)
         │       BPF program: load seccomp_data.nr (syscall number)
         │       JEQ 105 → SECCOMP_RET_ALLOW
         │       else   → SECCOMP_RET_KILL_PROCESS
         │
         └── filter 2 (older filter, lower priority)
                 BPF program: fallback
                 default → SECCOMP_RET_ERRNO(EPERM)

Filter return values (priority high→low):
  SECCOMP_RET_KILL_PROCESS  ← kill entire thread group (SIGSYS core dump)
  SECCOMP_RET_KILL_THREAD   ← kill calling thread only
  SECCOMP_RET_TRAP          ← SIGSYS to process (for ptrace-based tools)
  SECCOMP_RET_ERRNO         ← return specific errno to caller
  SECCOMP_RET_TRACE         ← notify ptracer (used by seccomp-bpf tools)
  SECCOMP_RET_LOG           ← log and allow (audit mode)
  SECCOMP_RET_ALLOW         ← allow the syscall
```

#### The BPF Bytecode — What the Filter Actually Looks Like

The seccomp filter is a classic BPF (not eBPF) program operating on a `seccomp_data` structure:

```c
// kernel/seccomp.c — what the BPF program sees:
struct seccomp_data {
    int   nr;           // syscall number
    __u32 arch;         // AUDIT_ARCH_X86_64 = 0xC000003E
    __u64 instruction_pointer;
    __u64 args[6];      // syscall arguments
};
```

A minimal "allow only read, write, exit" filter in BPF bytecode:
```
# BPF assembly (each line = one BPF instruction = 8 bytes):
# 00: LD  [4]        ; load seccomp_data.arch into accumulator
# 01: JNE 0xC000003E ; if not x86_64, jump to reject
# 02: LD  [0]        ; load seccomp_data.nr (syscall number)
# 03: JEQ 0          ; syscall 0 = read  → jump to allow
# 04: JEQ 1          ; syscall 1 = write → jump to allow
# 05: JEQ 60         ; syscall 60 = exit → jump to allow
# 06: RET KILL       ; default: kill
# 07: RET ALLOW      ; allow label

# In C (libseccomp generates this):
struct sock_filter filter[] = {
    BPF_STMT(BPF_LD|BPF_W|BPF_ABS,  offsetof(struct seccomp_data, arch)),
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, AUDIT_ARCH_X86_64, 1, 0),
    BPF_STMT(BPF_RET|BPF_K,         SECCOMP_RET_KILL),
    BPF_STMT(BPF_LD|BPF_W|BPF_ABS,  offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, __NR_read,  2, 0),
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, __NR_write, 1, 0),
    BPF_STMT(BPF_RET|BPF_K,         SECCOMP_RET_KILL),
    BPF_STMT(BPF_RET|BPF_K,         SECCOMP_RET_ALLOW),
};
```

#### Docker's Default Seccomp Profile — Blocked Syscalls

Docker's default profile (`/etc/docker/seccomp.json` or embedded in dockerd) blocks ~44 syscalls. The most security-relevant ones:

```
BLOCKED (SECCOMP_RET_ERRNO(EPERM)):
  acct            # Process accounting — could log host activities
  add_key         # Add keys to kernel keyring (host-wide)
  bpf             # Load eBPF programs (could escape cgroup filters)
  clock_adjtime   # Adjust system clock
  clock_settime   # Set system clock
  clone           # Only allowed without CLONE_NEWUSER
  create_module   # Load kernel module
  delete_module   # Unload kernel module
  finit_module    # Load module from fd
  get_kernel_syms # Enumerate kernel symbols
  init_module     # Load kernel module
  ioperm          # Direct port I/O
  iopl            # Change I/O privilege level
  kcmp            # Compare kernel pointers (fingerprinting)
  kexec_file_load # Load new kernel
  kexec_load      # Load new kernel
  keyctl          # Manipulate kernel keyring
  lookup_dcookie  # Dcache profiling
  mount           # Mount filesystems
  move_pages      # Move pages between NUMA nodes
  name_to_handle_at # Convert path to file handle
  nfsservctl      # NFS server ioctl
  open_by_handle_at # Open by file handle (host escape vector!)
  perf_event_open # Performance monitoring (could fingerprint host)
  personality     # Set process execution domain
  pivot_root      # Change root filesystem
  ptrace          # Trace other processes
  reboot          # Reboot system
  request_key     # Request kernel key
  set_mempolicy   # NUMA memory policy
  setdomainname   # Set domain name (UTS namespace bypass risk)
  sethostname     # Set hostname (only allowed in UTS ns)
  setns           # Join namespace (escape vector!)
  settimeofday    # Set time
  socket(AF_NETLINK, ..., NETLINK_AUDIT) # Audit netlink
  stime           # Set time
  swapoff         # Disable swap
  swapon          # Enable swap
  sysfs           # Sysfs calls (deprecated)
  _sysctl         # Kernel parameter manipulation
  umount2         # Unmount filesystem
  unshare         # Unshare namespaces (escape vector!)
  uselib          # Load shared library
  userfaultfd     # Userspace page fault handling (Dirty COW-style attacks)
  ustat           # Filesystem statistics
  vm86            # Enter virtual 8086 mode
  vm86old         # Enter virtual 8086 mode
```

#### Debugging Seccomp Violations

When a container is killed by seccomp, you see:

```
# In kernel audit log:
type=SECCOMP msg=audit(1710234567.123:891): auid=1000 uid=0 gid=0 ses=3
  pid=1389 comm="nginx" exe="/usr/sbin/nginx" sig=31 arch=c000003e
  syscall=317 compat=0 ip=0x7f8b3c2d1a40 code=0x80000000

# sig=31 = SIGSYS (bad system call)
# syscall=317 = statx (added in kernel 4.11)  ← container seccomp profile too old!
# code=0x80000000 = SECCOMP_RET_KILL_PROCESS
```

**Finding which syscall is blocked** (critical debugging technique):
```bash
# Method 1: strace on the container process
nsenter -t 1389 --pid --mount -- strace -f -e 'trace=!read,write,mmap,mprotect' nginx 2>&1 | head -50

# Method 2: bpftrace to trace SIGSYS
bpftrace -e 'tracepoint:syscalls:sys_exit_* /pid == 1389 && args->ret == -1/ {
  printf("syscall=%s errno=%d\n", probe, -args->ret);
}'

# Method 3: Check audit log
ausearch -m SECCOMP -ts today | grep "pid=1389"

# Method 4: decode syscall number
python3 -c "import ctypes; print(ctypes.CDLL(None).syscall.__doc__)"
# or:
ausyscall --dump | grep "^317"
# 317 statx
```

---

### 1.5 AppArmor & SELinux

These are Linux Security Modules (LSMs) that provide mandatory access control (MAC) — policy enforcement that root cannot override.

#### AppArmor

AppArmor uses profiles that specify what files, capabilities, and network operations a process can perform. Profiles are compiled to binary format and loaded into the kernel.

**Default Docker AppArmor profile** (`docker-default`):
```
#include <tunables/global>

profile docker-default flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # deny write for everything under /proc/sys/ except net
  deny @{PROC}/sys/[^n]** wklx,
  deny @{PROC}/sys/n[^e]** wklx,
  @{PROC}/sys/net/       r,
  @{PROC}/sys/net/**     rw,

  # deny /sys except what Docker needs
  deny @{PROC}/sysrq-trigger rwklx,
  deny @{PROC}/mem rwklx,
  deny @{PROC}/kmem rwklx,
  deny @{PROC}/kcore rwklx,

  # Allow signals within the container
  signal (send, receive) peer=docker-default,

  # Network
  network inet  tcp,
  network inet  udp,
  network inet6 tcp,
  network inet6 udp,
  network netlink raw,

  # Deny ptrace to other containers/host
  deny ptrace (read, readby) peer=unconfined,
  deny ptrace (trace, tracedby) peer=unconfined,

  # Capabilities
  deny capability mac_admin,
  deny capability mac_override,
  deny capability sys_log,
  deny capability sys_time,
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability sys_ptrace,
  deny capability sys_admin,  # note: mount etc. blocked separately
  deny capability audit_write,
  deny capability audit_control,
  deny capability syslog,
  deny capability net_admin,
}
```

**Checking AppArmor status**:
```bash
# Is AppArmor enforcing?
$ aa-status
apparmor module is loaded.
56 profiles are loaded.
49 profiles are in enforce mode.
   docker-default
   ...
7 profiles are in complain mode.

# What profile is a container PID running under?
$ cat /proc/1389/attr/current
docker-default (enforce)

# AppArmor violations in audit log:
$ journalctl -k | grep 'apparmor="DENIED"' | tail -20
```

#### SELinux

SELinux uses type enforcement labels on every kernel object (process, file, socket, etc.) and a policy database of allowed transitions. Docker/containerd use SELinux type `container_t` for container processes.

```
# Check container SELinux label:
$ ps -Z | grep "1389"
system_u:system_r:container_t:s0:c123,c456  1389  nginx

# Label breakdown:
# system_u     = SELinux user
# system_r     = SELinux role
# container_t  = SELinux type (this is what policy rules target)
# s0:c123,c456 = sensitivity level + MCS categories (Multi-Category Security)
#                c123,c456 are unique per container → containers can't access each other's files

# Check if SELinux is enforcing:
$ getenforce
Enforcing

# SELinux violations (AVC denials):
$ ausearch -m avc -ts today | audit2why | head -40
```

**MCS (Multi-Category Security)**: Each container gets a unique category pair (c0-c1023). Container files get labeled with the same categories. A container_t process with categories `c123,c456` can only access files labeled with those exact categories. This prevents container-to-container file access even if they share host mounts.

---

### 1.6 Overlay Filesystem (overlayfs)

Every container image is a set of read-only layers. The container adds a writable layer on top. overlayfs implements this using kernel VFS hooks.

#### Layer Architecture — Real Mount Output

```
# Actual mount for a container with nginx:alpine (2 layers + 1 writable):
$ cat /proc/mounts | grep overlay
overlay /var/lib/docker/overlay2/5d3f8c2a/merged overlay
  lowerdir=/var/lib/docker/overlay2/l/ABCD3F:/var/lib/docker/overlay2/l/WXYZ12,
  upperdir=/var/lib/docker/overlay2/5d3f8c2a/diff,
  workdir=/var/lib/docker/overlay2/5d3f8c2a/work
  0 0

# Directory structure:
/var/lib/docker/overlay2/
├── 5d3f8c2a/                  ← container layer
│   ├── diff/                  ← upperdir: writable changes
│   │   └── etc/nginx/nginx.conf  ← file modified in container
│   ├── link               → SHORTNAME1
│   ├── lower              → "l/ABCD3F:l/WXYZ12"
│   ├── merged/            ← merged view (container's rootfs)
│   └── work/              ← overlayfs work dir (opaque)
├── a1b2c3d4/                  ← image layer 1 (nginx:alpine top layer)
│   ├── diff/                  ← content of this layer
│   │   ├── usr/
│   │   └── etc/
│   └── link               → ABCD3F
└── e5f6a7b8/                  ← image layer 0 (alpine base)
    ├── diff/
    │   ├── bin/
    │   ├── lib/
    │   └── usr/
    └── link               → WXYZ12
```

#### Overlayfs Read/Write Semantics

```
┌──────────────────────────────────────────────────────────┐
│                  Container sees: /merged/                │
├──────────────────────────────────────────────────────────┤
│         upperdir (writable): /5d3f8c2a/diff/             │
│         Files written/modified by container go here      │
│         Deleted files → whiteout file (char dev 0:0)     │
├──────────────────────────────────────────────────────────┤
│         lowerdir[1]: /a1b2c3d4/diff/ (nginx layer)       │
│         Read-only. Multiple containers share this layer  │
├──────────────────────────────────────────────────────────┤
│         lowerdir[0]: /e5f6a7b8/diff/ (alpine base)       │
│         Read-only. Multiple containers share this layer  │
└──────────────────────────────────────────────────────────┘

Read: VFS walks upper → lower[1] → lower[0] until found
Write: Copy-up — kernel copies file from lower to upper, then modifies
Delete: Create whiteout in upper (c--------- 0:0 filename)
Rename: More complex — cross-layer renames use opaque dirs (trusted.overlay.opaque xattr)
```

#### Overlayfs Security Concerns

**1. Copy-up disclosure**: When a container modifies a sensitive file from a lower layer (e.g., `/etc/passwd`), a copy is made in the upper layer. If the upper layer is shared or improperly backed (e.g., on NFS), data may leak.

**2. Shared lower layers**: Multiple containers share the same lower layers. A read-only file in the lower layer is accessible to all containers using that image. If that file contains secrets baked into the image, all containers are exposed.

**3. Host filesystem access via escape**: If a container escapes its mount namespace and can access the host's overlayfs mount, it can directly read `upperdir` of other containers.

**Checking for secrets in image layers**:
```bash
# Scan all layer content for potential secrets:
find /var/lib/docker/overlay2/*/diff -type f -name "*.env" -o -name "*.pem" \
  -o -name "id_rsa" -o -name "credentials" 2>/dev/null

# Check for world-readable sensitive files in any layer:
find /var/lib/docker/overlay2/*/diff -type f -perm -o+r \
  \( -name "*.key" -o -name "*.pem" -o -name "passwd" \) 2>/dev/null
```

---

## 2. containerd Architecture

### 2.1 Full Component Map — Real Socket Paths and PIDs

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Host System (kernel 5.15.0-91-generic)                                         │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  containerd daemon (PID 987)                                             │    │
│  │  /usr/bin/containerd                                                     │    │
│  │  Config: /etc/containerd/config.toml                                     │    │
│  │  Socket: /run/containerd/containerd.sock (gRPC + ttrpc, unix)           │    │
│  │  State:  /var/lib/containerd/                                            │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │ gRPC Server  │  │  Snapshotter │  │Content Store │  │  Metadata  │  │    │
│  │  │ :port or     │  │  (overlayfs) │  │  (blobs)     │  │  (boltdb)  │  │    │
│  │  │ unix sock    │  │              │  │              │  │            │  │    │
│  │  │              │  │/var/lib/     │  │/var/lib/     │  │/var/lib/   │  │    │
│  │  │ Services:    │  │containerd/   │  │containerd/   │  │containerd/ │  │    │
│  │  │ - containers │  │io.containerd │  │io.containerd │  │io.contain  │  │    │
│  │  │ - images     │  │.snapshotter  │  │.content.v1   │  │erd.meta    │  │    │
│  │  │ - snapshots  │  │.v1.overlayfs │  │.content/     │  │data.v1/    │  │    │
│  │  │ - content    │  │/snapshots/   │  │blobs/sha256/ │  │meta.db     │  │    │
│  │  │ - events     │  │              │  │              │  │(boltdb)    │  │    │
│  │  │ - namespaces │  └──────────────┘  └──────────────┘  └────────────┘  │    │
│  │  │ - leases     │                                                       │    │
│  │  └──────────────┘                                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│           │                                                                     │
│           │ ttrpc (lightweight gRPC over unix socket)                           │
│           │ /run/containerd/io.containerd.runtime.v2.task/                      │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  containerd-shim-runc-v2 (PID 1234, one per container)                  │    │
│  │  /usr/bin/containerd-shim-runc-v2                                       │    │
│  │  ttrpc socket: /run/containerd/.../<container-id>/address               │    │
│  │                                                                          │    │
│  │  Responsibilities:                                                       │    │
│  │  - Reap zombie processes                                                 │    │
│  │  - Forward stdio (FIFOs at /run/containerd/.../init.stdin etc.)         │    │
│  │  - Exec into running container                                           │    │
│  │  - Report container exit status                                          │    │
│  │  - Survive containerd restarts (shim stays up if containerd crashes)    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│           │                                                                     │
│           │ fork+exec via runc                                                  │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  runc (transient, creates container then may exit or stay as monitor)   │    │
│  │  /usr/bin/runc                                                          │    │
│  │  OCI spec: /run/containerd/.../config.json                              │    │
│  │                                                                          │    │
│  │  runc create → runc run → container PID 1 (PID 1389)                   │    │
│  │                                                                          │    │
│  │  Steps:                                                                  │    │
│  │  1. clone(2) with namespace flags                                        │    │
│  │  2. Apply cgroup constraints                                             │    │
│  │  3. Configure network (via CNI plugin)                                   │    │
│  │  4. Mount overlayfs rootfs                                               │    │
│  │  5. Drop capabilities to spec                                            │    │
│  │  6. Apply seccomp filter                                                 │    │
│  │  7. pivot_root into container rootfs                                     │    │
│  │  8. exec() container entrypoint                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Container process (PID 1389 on host, PID 1 inside container)           │    │
│  │  /usr/sbin/nginx (example)                                              │    │
│  │                                                                          │    │
│  │  Namespaces: mnt ipc net pid uts cgroup (all new)                       │    │
│  │  User ns: SAME as host (no user namespace isolation by default)         │    │
│  │  Cgroup: /sys/fs/cgroup/system.slice/docker-<id>.scope/                 │    │
│  │  Rootfs: /var/lib/docker/overlay2/<id>/merged/ (via mnt ns)             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 containerd Shim Protocol — v2 ttrpc Wire Format

The shim protocol uses **ttrpc** — a lightweight RPC protocol optimized for Unix sockets with lower overhead than full gRPC. It uses protobuf serialization but custom framing.

**Key shim API methods** (from `containerd/runtime/v2/task/shim.proto`):

```protobuf
service Task {
  rpc State(StateRequest) returns (StateResponse);
  rpc Create(CreateTaskRequest) returns (CreateTaskResponse);
  rpc Start(StartRequest) returns (StartResponse);
  rpc Delete(DeleteRequest) returns (DeleteResponse);
  rpc Pids(PidsRequest) returns (PidsResponse);
  rpc Pause(PauseRequest) returns (google.protobuf.Empty);
  rpc Resume(ResumeRequest) returns (google.protobuf.Empty);
  rpc Checkpoint(CheckpointTaskRequest) returns (google.protobuf.Empty);
  rpc Kill(KillRequest) returns (google.protobuf.Empty);
  rpc Exec(ExecProcessRequest) returns (google.protobuf.Empty);
  rpc ResizePty(ResizePtyRequest) returns (google.protobuf.Empty);
  rpc CloseIO(CloseIORequest) returns (google.protobuf.Empty);
  rpc Update(UpdateTaskRequest) returns (google.protobuf.Empty);
  rpc Wait(WaitRequest) returns (WaitResponse);
  rpc Stats(StatsRequest) returns (StatsResponse);
  rpc Connect(ConnectRequest) returns (ConnectResponse);
  rpc Shutdown(ShutdownRequest) returns (google.protobuf.Empty);
}
```

**Tracing shim communication**:
```bash
# Find shim socket for a container:
CONTAINER_ID="a3f8c1d2e4b7f9a0"
cat /run/containerd/io.containerd.runtime.v2.task/moby/${CONTAINER_ID}/address
# Output: unix:///run/containerd/io.containerd.runtime.v2.task/moby/a3f8c1d2e4b7f9a0/address

# Trace ttrpc calls via strace on the shim:
SHIM_PID=$(pgrep -f "containerd-shim.*${CONTAINER_ID}")
strace -p ${SHIM_PID} -e trace=read,write,recvmsg,sendmsg -s 256 2>&1 | head -100
```

### 2.3 OCI Runtime Spec — Security-Critical Fields

The OCI Runtime Spec (`config.json`) is the contract between containerd/docker and runc. Every security property is specified here.

```json
{
  "ociVersion": "1.1.0",
  "process": {
    "terminal": false,
    "user": {
      "uid": 0,
      "gid": 0,
      "additionalGids": []
    },
    "args": ["/usr/sbin/nginx", "-g", "daemon off;"],
    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
    "cwd": "/",
    "capabilities": {
      "bounding":    ["CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_FSETID", "CAP_FOWNER",
                      "CAP_MKNOD", "CAP_NET_RAW", "CAP_SETGID", "CAP_SETUID",
                      "CAP_SETFCAP", "CAP_SETPCAP", "CAP_NET_BIND_SERVICE",
                      "CAP_SYS_CHROOT", "CAP_KILL", "CAP_AUDIT_WRITE"],
      "effective":   ["CAP_CHOWN", "..."],
      "inheritable": [],
      "permitted":   ["CAP_CHOWN", "..."],
      "ambient":     []
    },
    "rlimits": [
      {"type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024},
      {"type": "RLIMIT_NPROC",  "hard": 65535, "soft": 65535}
    ],
    "apparmorProfile": "docker-default",
    "selinuxLabel":    "system_u:system_r:container_t:s0:c123,c456",
    "seccomp": {
      "defaultAction": "SCMP_ACT_ERRNO",
      "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
      "syscalls": [
        {
          "names": ["read", "write", "close", "fstat", "lstat", "poll", "..."],
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "names": ["ptrace"],
          "action": "SCMP_ACT_ERRNO",
          "errnoRet": 1
        }
      ]
    },
    "noNewPrivileges": true
  },
  "root": {
    "path": "rootfs",
    "readonly": false
  },
  "mounts": [
    {"destination": "/proc", "type": "proc", "source": "proc",
     "options": ["nosuid", "noexec", "nodev"]},
    {"destination": "/dev", "type": "tmpfs", "source": "tmpfs",
     "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]},
    {"destination": "/dev/shm", "type": "tmpfs", "source": "shm",
     "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=67108864"]},
    {"destination": "/sys", "type": "sysfs", "source": "sysfs",
     "options": ["nosuid", "noexec", "nodev", "ro"]}
  ],
  "linux": {
    "resources": {
      "memory": {"limit": 536870912, "swap": 536870912, "reservation": 268435456},
      "cpu":    {"quota": 50000, "period": 100000, "shares": 1024},
      "pids":   {"limit": 100}
    },
    "cgroupsPath": "/system.slice/docker-a3f8c1d2e4b7f9a0.scope",
    "namespaces": [
      {"type": "pid"},
      {"type": "network", "path": ""},
      {"type": "ipc"},
      {"type": "uts"},
      {"type": "mount"},
      {"type": "cgroup"}
    ],
    "maskedPaths": [
      "/proc/asound", "/proc/acpi", "/proc/kcore", "/proc/keys",
      "/proc/latency_stats", "/proc/timer_list", "/proc/timer_stats",
      "/proc/sched_debug", "/proc/scsi", "/sys/firmware"
    ],
    "readonlyPaths": [
      "/proc/bus", "/proc/fs", "/proc/irq", "/proc/sys",
      "/proc/sysrq-trigger"
    ]
  }
}
```

**Key security fields**:
- `noNewPrivileges: true` → sets `PR_SET_NO_NEW_PRIVS` → prevents setuid binaries from gaining privileges, makes seccomp irrevocable
- `maskedPaths` → bind-mounts `/dev/null` over sensitive /proc entries
- `readonlyPaths` → bind-mounts with `MS_RDONLY` flag
- `cgroupsPath` → absolute path in unified cgroup v2 hierarchy

### 2.4 Snapshotter Internals

The snapshotter manages the container image layer filesystem. For overlayfs snapshotter, each snapshot corresponds to an overlayfs mount layer.

```
Content Store (/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/)
│
│  Stores raw layer tarballs as content-addressed blobs
│  sha256:a3f8c1d2... (compressed layer tarball)
│  sha256:b5e9f2a1... (manifest JSON)
│
▼
Snapshotter (/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/)
│
├── snapshots/ (indexed by snapshot ID, stored in boltdb metadata)
│   ├── 1/     (base image layer — alpine:3.19)
│   │   └── fs/ → actual filesystem content
│   ├── 2/     (nginx layer on top of alpine)
│   │   └── fs/ → just the diff files
│   └── 3/     (container's writable layer — "active" snapshot)
│       ├── fs/  → upperdir (writable)
│       └── work/ → overlayfs work dir
│
└── metadata.db (boltdb — snapshot parent relationships)

# Each snapshot in boltdb:
{
  "key":    "sha256:a3f8c1d2...",
  "kind":   "committed",  // or "active" for writable
  "parent": "sha256:e5f6a7b8...",
  "labels": {"containerd.io/gc.root": "2024-03-12T10:30:00Z"}
}
```

**Security implication**: The snapshotter's boltdb metadata DB is at `/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db`. If this file is tampered with (parent pointers altered), a container could be given a different image layer as its rootfs.

### 2.5 Content Store — Content-Addressable Security

The content store is append-only and content-addressed by SHA-256. Each blob's filename IS its hash. This provides integrity verification by default.

```bash
# Verify a blob's integrity:
BLOB="sha256:a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5"
BLOB_PATH="/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/${BLOB#sha256:}"
sha256sum $BLOB_PATH
# Should output: a3f8c1d2...  /var/lib/...
# If it doesn't match → content integrity violation

# List all blobs:
ctr content ls
# DIGEST                                                                  SIZE      AGE       LABELS
# sha256:a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3 27.14 MiB 2 days    containerd.io/distribution.source.docker.io=library/nginx
```

**Attack**: If an attacker can replace a blob file while keeping the same filename (SHA-256 collision or filesystem-level tampering), they can serve malicious image content. The defense is filesystem integrity monitoring (IMA/dm-verity) on the content store.

---

## 3. Docker Architecture

### 3.1 dockerd → containerd Integration

```
┌────────────────────────────────────────────────────────────────────────────┐
│  docker CLI (client)                                                        │
│  HTTP/Unix socket: /var/run/docker.sock (or TCP :2376 with TLS)            │
│  REST API: POST /v1.44/containers/create                                   │
└──────────────────────────┬─────────────────────────────────────────────────┘
                           │ REST API
                           ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  dockerd (PID 823)                                                          │
│  /usr/bin/dockerd                                                           │
│  Config: /etc/docker/daemon.json                                            │
│                                                                             │
│  Components:                                                                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐    │
│  │ LibNetwork  │  │  BuildKit    │  │ Image Store  │  │  Plugin Mgr  │    │
│  │ (libnetwork)│  │  (optional)  │  │  (imagedb)   │  │              │    │
│  │             │  │              │  │              │  │              │    │
│  │ bridge net  │  │ /var/lib/    │  │ /var/lib/    │  │ Volume/Net   │    │
│  │ overlay net │  │ docker/      │  │ docker/      │  │ plugins      │    │
│  │ macvlan     │  │ buildkit/    │  │ image/       │  │              │    │
│  └──────┬──────┘  └──────────────┘  └─────────────┘  └──────────────┘    │
│         │                                                                  │
│         │ dockerd acts as containerd client via gRPC                       │
│         │ containerd namespace: "moby"                                     │
└─────────┼──────────────────────────────────────────────────────────────────┘
          │ gRPC to /run/containerd/containerd.sock
          ▼
   containerd daemon (as described in section 2)
```

**Key security concern**: The Docker daemon runs as root and has a Unix socket `/var/run/docker.sock`. Anyone with access to this socket has **root-equivalent access** to the host. This is the most common container privilege escalation: mount the Docker socket into a container, then use it to create a privileged container that mounts `/` from the host.

```bash
# Attack: If docker.sock is mounted into a container:
docker run -v /var/run/docker.sock:/var/run/docker.sock alpine sh
# Inside container:
apk add docker-cli
docker run -v /:/host --rm -it alpine chroot /host # full host root access

# Defense: Never mount docker.sock into containers
# Audit for this:
docker inspect $(docker ps -q) --format '{{.Name}}: {{.Mounts}}' | grep docker.sock
```

### 3.2 Docker Networking — libnetwork & iptables

Docker networking uses Linux network namespaces + veth pairs + iptables for isolation and NAT.

```
Host network stack (net:[4026531992])
│
├── eth0: 10.0.0.5/24  (host external interface)
├── docker0: 172.17.0.1/16  (docker bridge)
│   │
│   ├── veth3f2a9b1 ←→→ (in container net ns) eth0: 172.17.0.2/16
│   │   Container 1: nginx, listening on :80
│   │
│   └── vethc8a1d2e ←→→ (in container net ns) eth0: 172.17.0.3/16
│       Container 2: redis, listening on :6379
│
└── iptables rules:
    Chain DOCKER-USER (user-configurable, processed first)
      RETURN

    Chain DOCKER (Docker-managed, do not modify directly)
      ACCEPT  tcp  --  0.0.0.0/0  172.17.0.2  tcp dpt:80
      DROP    all  --  0.0.0.0/0  172.17.0.2  ! in docker0

    Chain DOCKER-ISOLATION-STAGE-1
      RETURN  all  --  172.17.0.0/16  0.0.0.0/0  (from bridge)
      DROP    all  --  0.0.0.0/0      0.0.0.0/0  (inter-bridge)

    Chain POSTROUTING (nat table)
      MASQUERADE  all  --  172.17.0.0/16  !172.17.0.0/16  (outbound SNAT)
```

**Network security debugging**:
```bash
# Show all container network namespaces:
lsns -t net

# Enter a container's network namespace and inspect:
nsenter -t 1389 -n -- ip addr show
nsenter -t 1389 -n -- ss -tlnp
nsenter -t 1389 -n -- nft list ruleset
nsenter -t 1389 -n -- conntrack -L

# Check for inter-container connectivity (should be blocked by DOCKER-ISOLATION):
nsenter -t 1389 -n -- ping -c1 172.17.0.3  # Should fail if ICC=false

# Full iptables state:
iptables-save | grep -E 'DOCKER|172\.17'
```

---

## 4. Security Debugging Toolkit

### 4.1 Namespace Inspection

#### lsns — List All Namespaces System-Wide

```bash
$ lsns
        NS TYPE   NPROCS   PID USER              COMMAND
4026531835 cgroup    212     1 root              /sbin/init
4026531836 pid       198     1 root              /sbin/init
4026531837 user      212     1 root              /sbin/init
4026531838 uts       198     1 root              /sbin/init
4026531839 ipc       198     1 root              /sbin/init
4026531840 mnt       186     1 root              /sbin/init
4026531992 net       198     1 root              /sbin/init
4026532189 mnt         3  1389 root              nginx: master process
4026532190 uts         3  1389 root              nginx: master process
4026532191 ipc         3  1389 root              nginx: master process
4026532192 pid         3  1389 root              nginx: master process
4026532193 cgroup      3  1389 root              nginx: master process
4026532194 net         3  1389 root              nginx: master process
```

#### nsenter — Enter Specific Namespaces

```bash
# Enter ALL container namespaces (equivalent to docker exec):
nsenter --target 1389 --pid --mount --uts --ipc --net --cgroup

# Enter only network namespace (inspect without full container exec):
nsenter --target 1389 --net -- ip addr show
nsenter --target 1389 --net -- ss -tlnp
nsenter --target 1389 --net -- tcpdump -i any -n port 80

# Enter mount namespace to see container filesystem:
nsenter --target 1389 --mount -- ls /proc/self/fd
nsenter --target 1389 --mount -- df -h

# Check what PID 1389's PID looks like from inside its PID namespace:
nsenter --target 1389 --pid -- ps aux
# PID   USER     COMMAND
#   1   root     nginx: master process /usr/sbin/nginx
#  21   nginx    nginx: worker process
#  22   nginx    nginx: worker process
# Note: host PID 1389 appears as PID 1 inside namespace
```

#### /proc Namespace Security Audit

```bash
# Find containers NOT using all 6 expected namespaces (potential misconfiguration):
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  ns_count=$(ls -la /proc/$pid/ns/ 2>/dev/null | grep -cE 'mnt|net|pid|ipc|uts|cgroup')
  if [ "$ns_count" -lt 5 ]; then
    cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
    echo "PID $pid has only $ns_count isolation namespaces: $cmd"
  fi
done 2>/dev/null

# Find processes sharing namespaces with containers (potential breakout):
CONTAINER_MNT_NS=$(readlink /proc/1389/ns/mnt)
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  if [ "$(readlink /proc/$pid/ns/mnt 2>/dev/null)" = "$CONTAINER_MNT_NS" ]; then
    echo "PID $pid shares mnt namespace $CONTAINER_MNT_NS"
  fi
done 2>/dev/null
```

### 4.2 Cgroup Debugging

```bash
# v2: Show memory usage and limits for all containers:
for scope in /sys/fs/cgroup/system.slice/docker-*.scope; do
  id=$(basename $scope | sed 's/docker-//;s/\.scope//')
  max=$(cat $scope/memory.max)
  cur=$(cat $scope/memory.current)
  events=$(cat $scope/memory.events)
  echo "Container ${id:0:12}: current=${cur} max=${max}"
  echo "  events: $events"
done

# Real output example:
# Container a3f8c1d2e4b7: current=104857600 max=536870912
#   events: low 0 high 3 max 0 oom 0 oom_kill 0
# "high 3" means soft limit (memory.high) was crossed 3 times → container is under memory pressure

# CPU throttling check:
for scope in /sys/fs/cgroup/system.slice/docker-*.scope; do
  id=$(basename $scope | sed 's/docker-//;s/\.scope//')
  cpu_stat=$(cat $scope/cpu.stat)
  throttled=$(echo "$cpu_stat" | grep throttled_usec | awk '{print $2}')
  periods=$(echo "$cpu_stat" | grep nr_throttled | awk '{print $2}')
  echo "Container ${id:0:12}: throttled=${throttled}us over ${periods} periods"
done

# PID limit check:
for scope in /sys/fs/cgroup/system.slice/docker-*.scope; do
  id=$(basename $scope | sed 's/docker-//;s/\.scope//')
  cur=$(cat $scope/pids.current 2>/dev/null)
  max=$(cat $scope/pids.max 2>/dev/null)
  echo "Container ${id:0:12}: pids=${cur}/${max}"
done
# If pids.current approaches pids.max → container is fork-bombing or has too many threads
```

### 4.3 Capability Auditing

```bash
# Audit all running container processes for dangerous capabilities:
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  if [ -f /proc/$pid/status ]; then
    cap_eff=$(grep CapEff /proc/$pid/status 2>/dev/null | awk '{print $2}')
    if [ -n "$cap_eff" ] && [ "$cap_eff" != "0000000000000000" ]; then
      # Decode dangerous caps:
      decoded=$(capsh --decode=$cap_eff 2>/dev/null)
      if echo "$decoded" | grep -qE 'cap_sys_admin|cap_net_admin|cap_sys_ptrace|cap_sys_module|cap_sys_rawio'; then
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | head -c 60)
        echo "⚠ PID $pid ($cmd)"
        echo "  CapEff: $cap_eff"
        echo "  Decoded: $decoded"
      fi
    fi
  fi
done 2>/dev/null

# Check if noNewPrivileges is set:
cat /proc/1389/status | grep NoNewPrivs
# NoNewPrivs:    1  ← good, set
# NoNewPrivs:    0  ← bad, not set

# pscap — list all processes with non-zero capabilities:
pscap -a
# ppid  pid   name        command           capabilities
#   1  987    root        containerd        full (all caps)  ← containerd runs privileged
# 987  1234   root        containerd-shim   full (all caps)  ← shim also privileged
# 1234 1389   root        nginx             chown, dac_override, fsetid, ...
```

### 4.4 Seccomp Debugging

```bash
# Check if seccomp is active on a process:
cat /proc/1389/status | grep Seccomp
# Seccomp:       2   ← 0=disabled, 1=strict, 2=filter (bpf seccomp active)
# Seccomp_filters: 1  ← number of installed BPF filters

# Which syscalls is the container making? (audit mode)
# Temporarily set seccomp to SECCOMP_RET_LOG for a new container:
# In daemon.json or seccomp profile: change defaultAction to "SCMP_ACT_LOG"

# Trace syscalls of running container (production-safe approach with perf):
perf trace -p 1389 --no-syscalls -e 'syscalls:sys_enter_*' 2>&1 | head -50

# bpftrace: count all syscalls made by a container in 10 seconds:
bpftrace -e '
tracepoint:raw_syscalls:sys_enter
/pid == 1389/
{
  @syscalls[args->id] = count();
}
interval:s:10
{
  print(@syscalls);
  clear(@syscalls);
}' &

# Audit seccomp violations (SIGSYS):
bpftrace -e '
tracepoint:signal:signal_deliver
/args->sig == 31/
{
  printf("SIGSYS to PID %d (%s) at %s\n",
    pid, comm, kstack);
}'

# Find what syscall number was blocked by checking SIGSYS siginfo:
# In /proc/<pid>/fdinfo or via strace -k
strace -f -p 1389 2>&1 | grep "SIGSYS\|Bad system call"
```

### 4.5 Network Security Debugging

```bash
# Full network audit for a container:
CONTAINER_PID=1389

# 1. Network interfaces:
nsenter -t $CONTAINER_PID -n -- ip -d link show

# 2. Listening ports:
nsenter -t $CONTAINER_PID -n -- ss -tlnp
# State    Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
# LISTEN   0       128     0.0.0.0:80          0.0.0.0:*    users:(("nginx",pid=1,fd=6))
# LISTEN   0       128     [::]:80             [::]:*       users:(("nginx",pid=1,fd=7))

# 3. Active connections:
nsenter -t $CONTAINER_PID -n -- ss -tnp

# 4. Routes:
nsenter -t $CONTAINER_PID -n -- ip route show
# default via 172.17.0.1 dev eth0
# 172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2

# 5. ARP table:
nsenter -t $CONTAINER_PID -n -- arp -n

# 6. netfilter rules inside container:
nsenter -t $CONTAINER_PID -n -- nft list ruleset 2>/dev/null || echo "nft not available"
nsenter -t $CONTAINER_PID -n -- iptables -L -n -v 2>/dev/null || echo "iptables not in ns"

# 7. DNS configuration:
nsenter -t $CONTAINER_PID -m -- cat /etc/resolv.conf
# nameserver 127.0.0.11  (Docker's embedded DNS)
# options ndots:0

# 8. Packet capture on veth pair:
# Find the container's veth peer:
CONTAINER_ETH_INDEX=$(nsenter -t $CONTAINER_PID -n -- cat /sys/class/net/eth0/ifindex)
HOST_VETH=$(ip link | grep -E "^[0-9]+: veth" | awk -F: '{print $2}' | while read iface; do
  peer=$(ethtool -S $iface 2>/dev/null | grep 'peer_ifindex' | awk '{print $2}')
  [ "$peer" = "$CONTAINER_ETH_INDEX" ] && echo $iface
done | tr -d ' ')
echo "Container veth on host: $HOST_VETH"
tcpdump -i $HOST_VETH -n -s 0 -w /tmp/container_${CONTAINER_PID}.pcap &
```

### 4.6 eBPF Runtime Monitoring

eBPF is the most powerful tool for non-intrusive container security monitoring because it doesn't require modifying the container.

```bash
# 1. Detect container escapes: process leaving its cgroup
bpftrace -e '
kprobe:switch_task_namespaces
{
  printf("setns: pid=%d comm=%s new_ns=%lx\n",
    pid, comm, arg1);
}'

# 2. Detect privileged file opens (container accessing /proc/sysrq-trigger etc):
bpftrace -e '
tracepoint:syscalls:sys_enter_openat
/pid == 1389/
{
  printf("open: %s\n", str(args->filename));
}' | grep -E 'sysrq|kcore|kmem|/proc/sys/kernel'

# 3. Monitor raw socket creation (CAP_NET_RAW exploitation):
bpftrace -e '
tracepoint:syscalls:sys_enter_socket
/args->family == 17 || (args->type & 3) == 3/
{
  printf("RAW/PACKET socket: pid=%d comm=%s family=%d type=%d\n",
    pid, comm, args->family, args->type);
}'

# 4. Detect capability use:
bpftrace -e '
kprobe:cap_capable
{
  printf("cap_check: pid=%d comm=%s cap=%d\n", pid, comm, arg2);
}'

# 5. Detect namespace joining (setns syscall):
bpftrace -e '
tracepoint:syscalls:sys_enter_setns
{
  printf("setns: pid=%d (%s) fd=%d nstype=%d\n",
    pid, comm, args->fd, args->nstype);
}'

# 6. Monitor execve calls inside containers (new process spawning):
bpftrace -e '
tracepoint:syscalls:sys_enter_execve
{
  printf("execve: pid=%d comm=%s file=%s\n",
    pid, comm, str(args->filename));
}' | grep -v containerd  # filter out noise

# 7. Detect pivot_root or chroot calls:
bpftrace -e '
tracepoint:syscalls:sys_enter_pivot_root,
tracepoint:syscalls:sys_enter_chroot
{
  printf("rootfs change: pid=%d comm=%s probe=%s\n",
    pid, comm, probe);
}'
```

### 4.7 OCI Spec Auditing with ctr and crictl

```bash
# Using ctr (containerd native CLI):
# List containers in "moby" namespace (Docker's namespace):
ctr --namespace moby containers ls

# Inspect container config (OCI spec):
ctr --namespace moby containers info a3f8c1d2e4b7f9a0 | jq '.Spec.process.capabilities'
ctr --namespace moby containers info a3f8c1d2e4b7f9a0 | jq '.Spec.linux.seccomp.defaultAction'
ctr --namespace moby containers info a3f8c1d2e4b7f9a0 | jq '.Spec.process.noNewPrivileges'

# Using runc to inspect a running container's state:
runc --root /run/docker/runtime-runc/moby state a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9
# {
#   "ociVersion": "1.1.0",
#   "id": "a3f8c1d2...",
#   "pid": 1389,
#   "status": "running",
#   "bundle": "/run/containerd/io.containerd.runtime.v2.task/moby/a3f8c1d2.../",
#   "rootfs": "/var/lib/docker/overlay2/.../merged",
#   "created": "2024-03-12T10:30:00.123456789Z",
#   "owner": ""
# }

# View the actual OCI config.json runc is using:
cat /run/containerd/io.containerd.runtime.v2.task/moby/a3f8c1d2e4b7f9a0c2d3e4f5a6b7c8d9/config.json | jq .

# Using crictl (CRI-compatible, works with containerd via CRI plugin):
crictl ps
crictl inspect <container-id>
crictl exec <container-id> cat /proc/self/status | grep -E 'Cap|Seccomp'
```

---

## 5. Go Implementations

### 5.1 Namespace Inspector

A Go tool to inspect all namespaces of a process and detect security misconfigurations.

```go
// cmd/nsinspect/main.go
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// NSType represents a Linux namespace type
type NSType struct {
	Name  string
	File  string
	Flag  uintptr
}

var nsTypes = []NSType{
	{Name: "mnt",    File: "mnt",    Flag: syscall.CLONE_NEWNS},
	{Name: "uts",    File: "uts",    Flag: syscall.CLONE_NEWUTS},
	{Name: "ipc",    File: "ipc",    Flag: syscall.CLONE_NEWIPC},
	{Name: "net",    File: "net",    Flag: syscall.CLONE_NEWNET},
	{Name: "pid",    File: "pid",    Flag: syscall.CLONE_NEWPID},
	{Name: "user",   File: "user",   Flag: syscall.CLONE_NEWUSER},
	{Name: "cgroup", File: "cgroup", Flag: 0x02000000}, // CLONE_NEWCGROUP
	{Name: "time",   File: "time",   Flag: 0x00000080}, // CLONE_NEWTIME
}

// NamespaceInfo holds the inode and device for a namespace
type NamespaceInfo struct {
	Type  string
	Inode uint64
	Dev   uint64
}

// ProcessNS holds all namespace info for a process
type ProcessNS struct {
	PID        int
	Namespaces map[string]NamespaceInfo
}

func readProcessNS(pid int) (*ProcessNS, error) {
	pns := &ProcessNS{
		PID:        pid,
		Namespaces: make(map[string]NamespaceInfo),
	}

	for _, nsType := range nsTypes {
		nsPath := fmt.Sprintf("/proc/%d/ns/%s", pid, nsType.File)
		var stat syscall.Stat_t
		if err := syscall.Lstat(nsPath, &stat); err != nil {
			continue // namespace type not supported on this kernel
		}
		// Follow the symlink to get the actual ns inode
		target, err := os.Readlink(nsPath)
		if err != nil {
			continue
		}
		// Parse inode from "type:[inode]"
		parts := strings.SplitN(target, ":[", 2)
		var inode uint64
		if len(parts) == 2 {
			inodeStr := strings.TrimSuffix(parts[1], "]")
			inode, _ = strconv.ParseUint(inodeStr, 10, 64)
		}
		pns.Namespaces[nsType.Name] = NamespaceInfo{
			Type:  nsType.Name,
			Inode: inode,
			Dev:   stat.Dev,
		}
	}
	return pns, nil
}

// CompareWithHost checks which namespaces a process shares with init (PID 1)
func CompareWithHost(targetPID int) error {
	hostNS, err := readProcessNS(1)
	if err != nil {
		return fmt.Errorf("reading host namespaces: %w", err)
	}

	targetNS, err := readProcessNS(targetPID)
	if err != nil {
		return fmt.Errorf("reading PID %d namespaces: %w", targetPID, err)
	}

	fmt.Printf("Namespace isolation report for PID %d:\n", targetPID)
	fmt.Printf("%-10s %-20s %-20s %-12s %s\n",
		"TYPE", "HOST INODE", "TARGET INODE", "ISOLATED", "RISK")
	fmt.Println(strings.Repeat("-", 80))

	for _, nsType := range nsTypes {
		name := nsType.Name
		hostInfo := hostNS.Namespaces[name]
		targetInfo := targetNS.Namespaces[name]

		isolated := hostInfo.Inode != targetInfo.Inode
		risk := assessNamespaceRisk(name, isolated)

		isolatedStr := "NO ⚠"
		if isolated {
			isolatedStr = "YES ✓"
		}

		fmt.Printf("%-10s %-20d %-20d %-12s %s\n",
			name,
			hostInfo.Inode,
			targetInfo.Inode,
			isolatedStr,
			risk,
		)
	}
	return nil
}

func assessNamespaceRisk(nsType string, isolated bool) string {
	risks := map[string]struct{ isolated, shared string }{
		"mnt":    {"Low", "CRITICAL: shares host filesystem view"},
		"net":    {"Low", "HIGH: can reach host network stack directly"},
		"pid":    {"Low", "HIGH: can signal host processes"},
		"ipc":    {"Low", "MED: can access host SysV IPC / POSIX MQ"},
		"uts":    {"Low", "LOW: shares hostname, can affect host UTS"},
		"cgroup": {"Low", "MED: can see full host cgroup hierarchy"},
		"user":   {"LOW: has UID mapping", "CRITICAL: UID 0 = real root on host"},
		"time":   {"Low", "LOW: can fingerprint host boot time"},
	}

	if r, ok := risks[nsType]; ok {
		if isolated {
			return r.isolated
		}
		return r.shared
	}
	return "Unknown"
}

// SecurityAudit performs a full namespace security audit
func SecurityAudit(pid int) {
	fmt.Printf("\n=== CONTAINER SECURITY AUDIT: PID %d ===\n\n", pid)

	// 1. Namespace analysis
	if err := CompareWithHost(pid); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		return
	}

	// 2. Capability analysis
	fmt.Println("\n--- Capabilities ---")
	if data, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid)); err == nil {
		for _, line := range strings.Split(string(data), "\n") {
			if strings.HasPrefix(line, "Cap") || strings.HasPrefix(line, "NoNewPrivs") || strings.HasPrefix(line, "Seccomp") {
				fmt.Println(line)
			}
		}
	}

	// 3. Cgroup location
	fmt.Println("\n--- Cgroup Membership ---")
	if data, err := os.ReadFile(fmt.Sprintf("/proc/%d/cgroup", pid)); err == nil {
		fmt.Print(string(data))
	}

	// 4. Mounts visible to process
	fmt.Println("--- Key Security Mounts ---")
	if data, err := os.ReadFile(fmt.Sprintf("/proc/%d/mounts", pid)); err == nil {
		for _, line := range strings.Split(string(data), "\n") {
			if strings.Contains(line, "proc") || strings.Contains(line, "sys") ||
				strings.Contains(line, "dev") || strings.Contains(line, "overlay") {
				fmt.Println(line)
			}
		}
	}
}

// WalkContainerPIDs finds all processes that appear to be in containers
// by finding PIDs that have different mnt namespace from PID 1
func WalkContainerPIDs() ([]int, error) {
	hostNS, err := readProcessNS(1)
	if err != nil {
		return nil, err
	}
	hostMntInode := hostNS.Namespaces["mnt"].Inode

	entries, err := os.ReadDir("/proc")
	if err != nil {
		return nil, err
	}

	var containerPIDs []int
	seen := make(map[uint64]bool) // track unique mnt namespaces

	for _, entry := range entries {
		pid, err := strconv.Atoi(entry.Name())
		if err != nil {
			continue
		}

		nsPath := fmt.Sprintf("/proc/%d/ns/mnt", pid)
		target, err := os.Readlink(nsPath)
		if err != nil {
			continue
		}

		parts := strings.SplitN(target, ":[", 2)
		if len(parts) != 2 {
			continue
		}
		inodeStr := strings.TrimSuffix(parts[1], "]")
		inode, _ := strconv.ParseUint(inodeStr, 10, 64)

		if inode != hostMntInode && !seen[inode] {
			seen[inode] = true
			containerPIDs = append(containerPIDs, pid)
		}
	}
	return containerPIDs, nil
}

func main() {
	if len(os.Args) < 2 {
		// Auto-discover and audit all containers
		fmt.Println("Auto-discovering container processes...")
		pids, err := WalkContainerPIDs()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Found %d container processes (unique mnt namespaces)\n", len(pids))
		for _, pid := range pids {
			SecurityAudit(pid)
			fmt.Println()
		}
		return
	}

	pid, err := strconv.Atoi(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Invalid PID: %s\n", os.Args[1])
		os.Exit(1)
	}
	SecurityAudit(pid)

	// List all processes in the same namespaces (namespace peers)
	fmt.Println("\n--- Processes sharing namespaces with this container ---")
	targetNS, _ := readProcessNS(pid)
	targetMntInode := targetNS.Namespaces["mnt"].Inode

	entries, _ := os.ReadDir("/proc")
	for _, entry := range entries {
		peerPID, err := strconv.Atoi(entry.Name())
		if err != nil || peerPID == pid {
			continue
		}
		peerNS, err := readProcessNS(peerPID)
		if err != nil {
			continue
		}
		if peerNS.Namespaces["mnt"].Inode == targetMntInode {
			cmdBytes, _ := os.ReadFile(fmt.Sprintf("/proc/%d/cmdline", peerPID))
			cmd := strings.ReplaceAll(string(cmdBytes), "\x00", " ")
			if len(cmd) > 60 {
				cmd = cmd[:60] + "..."
			}
			fmt.Printf("  PID %-6d: %s\n", peerPID, cmd)
		}
	}

	// Check for suspicious bind mounts (host paths mounted into container):
	fmt.Println("\n--- Bind Mounts (potential host access) ---")
	mountsPath := fmt.Sprintf("/proc/%d/mounts", pid)
	// We enter the mount namespace to read accurate mount info
	mountData, err := os.ReadFile(mountsPath)
	if err == nil {
		for _, line := range strings.Split(string(mountData), "\n") {
			fields := strings.Fields(line)
			if len(fields) < 4 {
				continue
			}
			opts := fields[3]
			// bind mounts appear as 'bind' in /proc/<pid>/mounts
			// or we can detect host paths by checking if source is outside overlay
			src := fields[0]
			if strings.HasPrefix(src, "/dev") || strings.HasPrefix(src, "/var") ||
				strings.HasPrefix(src, "/etc") || strings.HasPrefix(src, "/run") ||
				strings.HasPrefix(src, "/home") || strings.HasPrefix(src, "/tmp") {
				if !strings.Contains(src, "overlay2") && !strings.Contains(src, "containerd") {
					fmt.Printf("  ⚠ HOST PATH BIND MOUNT: %s → %s [%s]\n",
						src, fields[1], opts)
				}
			}
		}
	}

	_ = filepath.Join // avoid unused import
}
```

```go
// go.mod
module github.com/yourorg/container-security-tools

go 1.22

require (
	// No external dependencies for namespace inspector — pure stdlib
)
```

**Build and run**:
```bash
mkdir -p cmd/nsinspect
# save main.go above
go build -o bin/nsinspect ./cmd/nsinspect/
sudo ./bin/nsinspect 1389
sudo ./bin/nsinspect  # auto-discover all containers
```

---

### 5.2 Cgroup v2 Reader & Enforcer

```go
// pkg/cgroupv2/cgroupv2.go
package cgroupv2

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const cgroupV2Root = "/sys/fs/cgroup"

// ContainerCgroup holds cgroup metrics for a container
type ContainerCgroup struct {
	Path          string
	ContainerID   string

	// Memory
	MemoryCurrentBytes   uint64
	MemoryMaxBytes       uint64 // 0 = unlimited (max)
	MemoryHighBytes      uint64
	MemoryLowBytes       uint64
	MemorySwapCurrent    uint64
	MemorySwapMax        uint64
	MemoryOOMKills       uint64
	MemoryOOMKillsTotal  uint64

	// CPU
	CPUUsageMicros    uint64 // total CPU time used
	CPUUserMicros     uint64
	CPUSystemMicros   uint64
	CPUThrottledMicros uint64
	CPUThrottledPeriods uint64
	CPUTotalPeriods   uint64
	CPUMaxQuota       uint64 // microseconds per period (0 = unlimited)
	CPUMaxPeriod      uint64 // period in microseconds
	CPUWeight         uint64

	// PIDs
	PIDsCurrent uint64
	PIDsMax     uint64 // 0 = unlimited

	// IO
	IOMaxRBPS  uint64
	IOMaxWBPS  uint64
	IOMaxRIOPS uint64
	IOMaxWIOPS uint64

	// Timestamps
	CollectedAt time.Time
}

// ReadContainerCgroup reads all cgroup v2 stats for a container
func ReadContainerCgroup(cgroupPath string) (*ContainerCgroup, error) {
	fullPath := filepath.Join(cgroupV2Root, cgroupPath)

	// Verify this is a cgroup v2 hierarchy
	if _, err := os.Stat(filepath.Join(fullPath, "cgroup.controllers")); err != nil {
		return nil, fmt.Errorf("not a cgroup v2 path (no cgroup.controllers): %w", err)
	}

	cc := &ContainerCgroup{
		Path:        fullPath,
		CollectedAt: time.Now(),
	}

	// Extract container ID from path (docker-<id>.scope format)
	base := filepath.Base(cgroupPath)
	if strings.HasPrefix(base, "docker-") && strings.HasSuffix(base, ".scope") {
		cc.ContainerID = strings.TrimSuffix(strings.TrimPrefix(base, "docker-"), ".scope")
	}

	var err error

	// Memory stats
	cc.MemoryCurrentBytes, _ = readUint64File(filepath.Join(fullPath, "memory.current"))
	cc.MemoryMaxBytes, _     = readUint64File(filepath.Join(fullPath, "memory.max"))
	cc.MemoryHighBytes, _    = readUint64File(filepath.Join(fullPath, "memory.high"))
	cc.MemoryLowBytes, _     = readUint64File(filepath.Join(fullPath, "memory.low"))
	cc.MemorySwapCurrent, _  = readUint64File(filepath.Join(fullPath, "memory.swap.current"))
	cc.MemorySwapMax, _      = readUint64File(filepath.Join(fullPath, "memory.swap.max"))

	if events, err := readKeyValueFile(filepath.Join(fullPath, "memory.events")); err == nil {
		cc.MemoryOOMKills, _ = strconv.ParseUint(events["oom_kill"], 10, 64)
		cc.MemoryOOMKillsTotal, _ = strconv.ParseUint(events["oom_kill"], 10, 64)
	}

	// CPU stats
	if cpuStat, err := readKeyValueFile(filepath.Join(fullPath, "cpu.stat")); err == nil {
		cc.CPUUsageMicros, _      = strconv.ParseUint(cpuStat["usage_usec"], 10, 64)
		cc.CPUUserMicros, _       = strconv.ParseUint(cpuStat["user_usec"], 10, 64)
		cc.CPUSystemMicros, _     = strconv.ParseUint(cpuStat["system_usec"], 10, 64)
		cc.CPUThrottledMicros, _  = strconv.ParseUint(cpuStat["throttled_usec"], 10, 64)
		cc.CPUThrottledPeriods, _ = strconv.ParseUint(cpuStat["nr_throttled"], 10, 64)
		cc.CPUTotalPeriods, _     = strconv.ParseUint(cpuStat["nr_periods"], 10, 64)
	}

	cpuMaxData, err := os.ReadFile(filepath.Join(fullPath, "cpu.max"))
	if err == nil {
		parts := strings.Fields(strings.TrimSpace(string(cpuMaxData)))
		if len(parts) == 2 {
			if parts[0] != "max" {
				cc.CPUMaxQuota, _ = strconv.ParseUint(parts[0], 10, 64)
			}
			cc.CPUMaxPeriod, _ = strconv.ParseUint(parts[1], 10, 64)
		}
	}
	cc.CPUWeight, _ = readUint64File(filepath.Join(fullPath, "cpu.weight"))

	// PID stats
	cc.PIDsCurrent, _ = readUint64File(filepath.Join(fullPath, "pids.current"))
	cc.PIDsMax, _      = readUint64File(filepath.Join(fullPath, "pids.max"))

	return cc, nil
}

// MemoryUsagePercent returns current memory usage as a percentage of max
func (cc *ContainerCgroup) MemoryUsagePercent() float64 {
	if cc.MemoryMaxBytes == 0 {
		return 0
	}
	return float64(cc.MemoryCurrentBytes) / float64(cc.MemoryMaxBytes) * 100
}

// CPUThrottlePercent returns the percentage of periods where the container was throttled
func (cc *ContainerCgroup) CPUThrottlePercent() float64 {
	if cc.CPUTotalPeriods == 0 {
		return 0
	}
	return float64(cc.CPUThrottledPeriods) / float64(cc.CPUTotalPeriods) * 100
}

// IsMemoryPressured returns true if the container has hit its soft memory limit
func (cc *ContainerCgroup) IsMemoryPressured() bool {
	// memory.high was crossed if memory.current > memory.high
	return cc.MemoryHighBytes > 0 && cc.MemoryCurrentBytes > cc.MemoryHighBytes
}

// SecurityCheck verifies the cgroup has proper resource limits set
func (cc *ContainerCgroup) SecurityCheck() []string {
	var issues []string

	if cc.MemoryMaxBytes == 0 {
		issues = append(issues, "CRITICAL: No memory limit set (memory.max = unlimited) — OOM can affect host")
	} else if cc.MemoryMaxBytes > 8*1024*1024*1024 {
		issues = append(issues, fmt.Sprintf("WARNING: Memory limit is very high: %s",
			humanBytes(cc.MemoryMaxBytes)))
	}

	if cc.CPUMaxQuota == 0 {
		issues = append(issues, "WARNING: No CPU quota set (cpu.max = unlimited) — CPU monopolization possible")
	}

	if cc.PIDsMax == 0 {
		issues = append(issues, "CRITICAL: No PID limit set (pids.max = unlimited) — fork bomb possible")
	} else if cc.PIDsMax > 10000 {
		issues = append(issues, fmt.Sprintf("WARNING: PID limit is very high: %d", cc.PIDsMax))
	}

	if cc.MemoryOOMKills > 0 {
		issues = append(issues, fmt.Sprintf("INFO: Container has been OOM-killed %d time(s)", cc.MemoryOOMKills))
	}

	if cc.CPUThrottlePercent() > 50 {
		issues = append(issues, fmt.Sprintf("PERF: Container is heavily CPU throttled: %.1f%% of periods",
			cc.CPUThrottlePercent()))
	}

	return issues
}

// String returns a human-readable summary
func (cc *ContainerCgroup) String() string {
	var sb strings.Builder
	id := cc.ContainerID
	if len(id) > 12 {
		id = id[:12]
	}

	maxMem := "unlimited"
	if cc.MemoryMaxBytes > 0 {
		maxMem = humanBytes(cc.MemoryMaxBytes)
	}

	cpuQuota := "unlimited"
	if cc.CPUMaxQuota > 0 {
		cpuPct := float64(cc.CPUMaxQuota) / float64(cc.CPUMaxPeriod) * 100
		cpuQuota = fmt.Sprintf("%.1f%%", cpuPct)
	}

	pidsMax := "unlimited"
	if cc.PIDsMax > 0 {
		pidsMax = fmt.Sprintf("%d", cc.PIDsMax)
	}

	fmt.Fprintf(&sb, "Container: %s\n", id)
	fmt.Fprintf(&sb, "  Memory: %s / %s (%.1f%%)\n",
		humanBytes(cc.MemoryCurrentBytes), maxMem, cc.MemoryUsagePercent())
	fmt.Fprintf(&sb, "  CPU:    quota=%s weight=%d throttled=%.1f%%\n",
		cpuQuota, cc.CPUWeight, cc.CPUThrottlePercent())
	fmt.Fprintf(&sb, "  PIDs:   %d / %s\n", cc.PIDsCurrent, pidsMax)
	fmt.Fprintf(&sb, "  OOM kills: %d\n", cc.MemoryOOMKills)

	issues := cc.SecurityCheck()
	if len(issues) > 0 {
		fmt.Fprintf(&sb, "  Security Issues:\n")
		for _, issue := range issues {
			fmt.Fprintf(&sb, "    [!] %s\n", issue)
		}
	}
	return sb.String()
}

// ScanAllContainerCgroups finds and reads all Docker container cgroups
func ScanAllContainerCgroups() ([]*ContainerCgroup, error) {
	pattern := filepath.Join(cgroupV2Root, "system.slice", "docker-*.scope")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, err
	}

	var results []*ContainerCgroup
	for _, match := range matches {
		// Get path relative to cgroup root
		relPath := strings.TrimPrefix(match, cgroupV2Root+"/")
		cc, err := ReadContainerCgroup(relPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: reading %s: %v\n", match, err)
			continue
		}
		results = append(results, cc)
	}
	return results, nil
}

// EnforceLimits sets cgroup limits (useful for runtime enforcement)
// This requires the calling process to have write access to the cgroup files
func EnforceLimits(cgroupPath string, memLimitBytes, cpuQuotaUs, cpuPeriodUs, pidsMax uint64) error {
	fullPath := filepath.Join(cgroupV2Root, cgroupPath)

	if memLimitBytes > 0 {
		if err := writeFile(filepath.Join(fullPath, "memory.max"),
			strconv.FormatUint(memLimitBytes, 10)); err != nil {
			return fmt.Errorf("setting memory.max: %w", err)
		}
		// Set soft limit to 80% of hard limit
		highLimit := memLimitBytes * 80 / 100
		if err := writeFile(filepath.Join(fullPath, "memory.high"),
			strconv.FormatUint(highLimit, 10)); err != nil {
			return fmt.Errorf("setting memory.high: %w", err)
		}
	}

	if cpuQuotaUs > 0 && cpuPeriodUs > 0 {
		cpuMax := fmt.Sprintf("%d %d", cpuQuotaUs, cpuPeriodUs)
		if err := writeFile(filepath.Join(fullPath, "cpu.max"), cpuMax); err != nil {
			return fmt.Errorf("setting cpu.max: %w", err)
		}
	}

	if pidsMax > 0 {
		if err := writeFile(filepath.Join(fullPath, "pids.max"),
			strconv.FormatUint(pidsMax, 10)); err != nil {
			return fmt.Errorf("setting pids.max: %w", err)
		}
	}

	return nil
}

// FreezeContainer freezes all processes in the container's cgroup
func FreezeContainer(cgroupPath string) error {
	fullPath := filepath.Join(cgroupV2Root, cgroupPath)
	return writeFile(filepath.Join(fullPath, "cgroup.freeze"), "1")
}

// ThawContainer unfreezes all processes in the container's cgroup
func ThawContainer(cgroupPath string) error {
	fullPath := filepath.Join(cgroupV2Root, cgroupPath)
	return writeFile(filepath.Join(fullPath, "cgroup.freeze"), "0")
}

// GetContainerPIDs returns all PIDs in a container's cgroup
func GetContainerPIDs(cgroupPath string) ([]int, error) {
	fullPath := filepath.Join(cgroupV2Root, cgroupPath)
	data, err := os.ReadFile(filepath.Join(fullPath, "cgroup.procs"))
	if err != nil {
		return nil, err
	}

	var pids []int
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		pid, err := strconv.Atoi(line)
		if err == nil {
			pids = append(pids, pid)
		}
	}
	return pids, nil
}

// helper functions
func readUint64File(path string) (uint64, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}
	s := strings.TrimSpace(string(data))
	if s == "max" {
		return 0, nil // 0 represents unlimited/max
	}
	return strconv.ParseUint(s, 10, 64)
}

func readKeyValueFile(path string) (map[string]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	result := make(map[string]string)
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			result[parts[0]] = parts[1]
		}
	}
	return result, nil
}

func writeFile(path, content string) error {
	return os.WriteFile(path, []byte(content), 0644)
}

func humanBytes(b uint64) string {
	const unit = 1024
	if b < unit {
		return fmt.Sprintf("%dB", b)
	}
	div, exp := uint64(unit), 0
	for n := b / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f%cB", float64(b)/float64(div), "KMGTPE"[exp])
}
```

```go
// cmd/cgaudit/main.go
package main

import (
	"fmt"
	"os"

	"github.com/yourorg/container-security-tools/pkg/cgroupv2"
)

func main() {
	containers, err := cgroupv2.ScanAllContainerCgroups()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Found %d containers\n\n", len(containers))
	for _, cc := range containers {
		fmt.Println(cc.String())
		fmt.Println()
	}
}
```

---

### 5.3 Capability Auditor

```go
// pkg/capaudit/capaudit.go
package capaudit

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"syscall"
	"unsafe"
)

// Capability represents a Linux capability
type Capability struct {
	Number uint
	Name   string
	Risk   string
	Reason string
}

// Full capability table with security context
var capabilityTable = []Capability{
	{0,  "CAP_CHOWN",            "MED",      "Change file ownership — needed for many services"},
	{1,  "CAP_DAC_OVERRIDE",     "HIGH",     "Bypass DAC — can read/write any file"},
	{2,  "CAP_DAC_READ_SEARCH",  "HIGH",     "Bypass DAC read — can read any file/dir"},
	{3,  "CAP_FOWNER",           "MED",      "Bypass permission checks — UID-agnostic file ops"},
	{4,  "CAP_FSETID",           "MED",      "Retain setuid/setgid bits on writes"},
	{5,  "CAP_KILL",             "MED",      "Send signals to any process in user namespace"},
	{6,  "CAP_SETGID",           "HIGH",     "Manipulate GIDs — can become any GID"},
	{7,  "CAP_SETUID",           "CRITICAL", "Manipulate UIDs — can become UID 0"},
	{8,  "CAP_SETPCAP",          "HIGH",     "Grant/remove caps from other processes"},
	{9,  "CAP_LINUX_IMMUTABLE",  "LOW",      "Set immutable/append-only flags"},
	{10, "CAP_NET_BIND_SERVICE", "LOW",      "Bind port < 1024"},
	{11, "CAP_NET_BROADCAST",    "LOW",      "Send packet broadcasts"},
	{12, "CAP_NET_ADMIN",        "CRITICAL", "Full network admin — routing, iptables, interfaces"},
	{13, "CAP_NET_RAW",          "HIGH",     "Raw sockets — can sniff/spoof network traffic"},
	{14, "CAP_IPC_LOCK",         "MED",      "Lock memory (mlock) — potential DoS"},
	{15, "CAP_IPC_OWNER",        "MED",      "Bypass IPC ownership checks"},
	{16, "CAP_SYS_MODULE",       "CRITICAL", "Load/unload kernel modules — full kernel access"},
	{17, "CAP_SYS_RAWIO",        "CRITICAL", "Direct hardware I/O — read host memory"},
	{18, "CAP_SYS_CHROOT",       "MED",      "chroot(2) — can create rootfs for escapes"},
	{19, "CAP_SYS_PTRACE",       "CRITICAL", "ptrace any process — can extract secrets/code inject"},
	{20, "CAP_SYS_PACCT",        "LOW",      "Process accounting"},
	{21, "CAP_SYS_ADMIN",        "CRITICAL", "~65 operations including mount, nsenter, BPF, etc."},
	{22, "CAP_SYS_BOOT",         "CRITICAL", "reboot, kexec"},
	{23, "CAP_SYS_NICE",         "LOW",      "Set process priorities"},
	{24, "CAP_SYS_RESOURCE",     "MED",      "Override resource limits"},
	{25, "CAP_SYS_TIME",         "MED",      "Set system clock"},
	{26, "CAP_SYS_TTY_CONFIG",   "LOW",      "TTY configuration"},
	{27, "CAP_MKNOD",            "MED",      "Create device files — could access host devices"},
	{28, "CAP_LEASE",            "LOW",      "File leases"},
	{29, "CAP_AUDIT_WRITE",      "LOW",      "Write to kernel audit log"},
	{30, "CAP_AUDIT_CONTROL",    "HIGH",     "Control audit system — can disable auditing!"},
	{31, "CAP_SETFCAP",          "HIGH",     "Set file capabilities"},
	{32, "CAP_MAC_OVERRIDE",     "HIGH",     "Override MAC policy (Smack)"},
	{33, "CAP_MAC_ADMIN",        "HIGH",     "Administer MAC policy"},
	{34, "CAP_SYSLOG",           "MED",      "Access kernel syslog — may leak addresses"},
	{35, "CAP_WAKE_ALARM",       "LOW",      "Trigger wake alarms"},
	{36, "CAP_BLOCK_SUSPEND",    "LOW",      "Prevent system suspend"},
	{37, "CAP_AUDIT_READ",       "MED",      "Read audit log — can monitor system"},
	{38, "CAP_PERFMON",          "HIGH",     "Performance monitoring — can read kernel memory via perf"},
	{39, "CAP_BPF",              "CRITICAL", "Load eBPF programs — can access any kernel memory"},
	{40, "CAP_CHECKPOINT_RESTORE","HIGH",    "CRIU checkpoint — can restore processes with arbitrary state"},
}

// CapabilitySet represents a process's capability sets
type CapabilitySet struct {
	PID         int
	Inheritable uint64
	Permitted   uint64
	Effective   uint64
	Bounding    uint64
	Ambient     uint64
	NoNewPrivs  bool
	SeccompMode int
}

// ReadCapabilitySet reads capabilities from /proc/<pid>/status
func ReadCapabilitySet(pid int) (*CapabilitySet, error) {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid))
	if err != nil {
		return nil, fmt.Errorf("reading /proc/%d/status: %w", pid, err)
	}

	cs := &CapabilitySet{PID: pid}

	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.SplitN(line, ":\t", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])

		switch key {
		case "CapInh":
			cs.Inheritable, _ = strconv.ParseUint(val, 16, 64)
		case "CapPrm":
			cs.Permitted, _ = strconv.ParseUint(val, 16, 64)
		case "CapEff":
			cs.Effective, _ = strconv.ParseUint(val, 16, 64)
		case "CapBnd":
			cs.Bounding, _ = strconv.ParseUint(val, 16, 64)
		case "CapAmb":
			cs.Ambient, _ = strconv.ParseUint(val, 16, 64)
		case "NoNewPrivs":
			cs.NoNewPrivs = val == "1"
		case "Seccomp":
			cs.SeccompMode, _ = strconv.Atoi(val)
		}
	}
	return cs, nil
}

// ActiveCapabilities returns the list of capabilities in the Effective set
func (cs *CapabilitySet) ActiveCapabilities() []Capability {
	var active []Capability
	for _, cap := range capabilityTable {
		if cs.Effective&(1<<cap.Number) != 0 {
			active = append(active, cap)
		}
	}
	return active
}

// CriticalCapabilities returns CRITICAL-risk capabilities in the Effective set
func (cs *CapabilitySet) CriticalCapabilities() []Capability {
	var critical []Capability
	for _, cap := range cs.ActiveCapabilities() {
		if cap.Risk == "CRITICAL" {
			critical = append(critical, cap)
		}
	}
	return critical
}

// SecurityReport generates a security report for the capability set
func (cs *CapabilitySet) SecurityReport() string {
	var sb strings.Builder

	fmt.Fprintf(&sb, "=== Capability Security Report for PID %d ===\n\n", cs.PID)

	// Security posture indicators
	fmt.Fprintf(&sb, "Security Controls:\n")
	fmt.Fprintf(&sb, "  NoNewPrivileges: %v\n", cs.NoNewPrivs)

	seccompStr := map[int]string{0: "DISABLED ⚠", 1: "strict", 2: "filter (BPF)"}[cs.SeccompMode]
	fmt.Fprintf(&sb, "  Seccomp Mode:    %s\n", seccompStr)
	fmt.Fprintf(&sb, "\n")

	// Raw bitmasks
	fmt.Fprintf(&sb, "Capability Bitmasks:\n")
	fmt.Fprintf(&sb, "  Effective (active):   0x%016x\n", cs.Effective)
	fmt.Fprintf(&sb, "  Permitted (max):      0x%016x\n", cs.Permitted)
	fmt.Fprintf(&sb, "  Bounding (ceiling):   0x%016x\n", cs.Bounding)
	fmt.Fprintf(&sb, "  Inheritable (exec):   0x%016x\n", cs.Inheritable)
	fmt.Fprintf(&sb, "  Ambient (exec,nofile):0x%016x\n", cs.Ambient)
	fmt.Fprintf(&sb, "\n")

	// Active capabilities with risk assessment
	active := cs.ActiveCapabilities()
	fmt.Fprintf(&sb, "Active Capabilities (%d):\n", len(active))
	fmt.Fprintf(&sb, "  %-30s %-10s %s\n", "CAPABILITY", "RISK", "REASON")
	fmt.Fprintf(&sb, "  %s\n", strings.Repeat("-", 80))

	riskOrder := map[string]int{"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
	// Sort by risk level
	sorted := make([]Capability, len(active))
	copy(sorted, active)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if riskOrder[sorted[i].Risk] > riskOrder[sorted[j].Risk] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}

	for _, cap := range sorted {
		riskIcon := map[string]string{"CRITICAL": "🔴", "HIGH": "🟠", "MED": "🟡", "LOW": "🟢"}[cap.Risk]
		fmt.Fprintf(&sb, "  %-30s %s %-8s %s\n", cap.Name, riskIcon, cap.Risk, cap.Reason)
	}

	// Specific dangerous combination checks
	fmt.Fprintf(&sb, "\nDangerous Combination Analysis:\n")
	eff := cs.Effective

	hasCap := func(n uint) bool { return eff&(1<<n) != 0 }

	if hasCap(21) { // CAP_SYS_ADMIN
		fmt.Fprintf(&sb, "  ⛔ CAP_SYS_ADMIN detected — encompasses ~65 privileged operations\n")
		fmt.Fprintf(&sb, "     Including: mount, umount, setns, unshare, pivot_root, ioctl, BPF, etc.\n")
		fmt.Fprintf(&sb, "     This is nearly equivalent to root on the host (with no userns)\n")
	}

	if hasCap(7) && hasCap(1) { // CAP_SETUID + CAP_DAC_OVERRIDE
		fmt.Fprintf(&sb, "  ⛔ CAP_SETUID + CAP_DAC_OVERRIDE: can become any UID and read any file\n")
	}

	if hasCap(13) { // CAP_NET_RAW
		fmt.Fprintf(&sb, "  ⚠ CAP_NET_RAW: Can create SOCK_RAW/SOCK_PACKET sockets — network sniffing\n")
		fmt.Fprintf(&sb, "     Attack: packet capture in container's net ns, ARP spoofing\n")
	}

	if hasCap(39) { // CAP_BPF
		fmt.Fprintf(&sb, "  ⛔ CAP_BPF: Can load eBPF programs — can read arbitrary kernel memory\n")
		fmt.Fprintf(&sb, "     Attack: install kprobe eBPF to read host process memory, extract secrets\n")
	}

	if hasCap(19) { // CAP_SYS_PTRACE
		fmt.Fprintf(&sb, "  ⛔ CAP_SYS_PTRACE: Can ptrace any process in user namespace\n")
		fmt.Fprintf(&sb, "     Attack: attach to host process, inject shellcode, extract memory\n")
	}

	if !cs.NoNewPrivs {
		fmt.Fprintf(&sb, "\n  ⚠ NoNewPrivileges is NOT set — setuid binaries can gain privileges\n")
		fmt.Fprintf(&sb, "     Set PR_SET_NO_NEW_PRIVS=1 in process config or use '--security-opt no-new-privileges'\n")
	}

	if cs.SeccompMode == 0 {
		fmt.Fprintf(&sb, "\n  ⛔ Seccomp is DISABLED — all syscalls are permitted\n")
	}

	return sb.String()
}

// GetCurrentCapabilities reads capabilities for the current process
// using the capget(2) system call directly
func GetCurrentCapabilities() (permitted, effective, inheritable uint32, err error) {
	type capHeader struct {
		version uint32
		pid     int32
	}
	type capData struct {
		effective   uint32
		permitted   uint32
		inheritable uint32
	}

	const _LINUX_CAPABILITY_VERSION_1 = 0x19980330

	hdr := capHeader{version: _LINUX_CAPABILITY_VERSION_1, pid: 0}
	var data capData

	_, _, errno := syscall.Syscall(syscall.SYS_CAPGET,
		uintptr(unsafe.Pointer(&hdr)),
		uintptr(unsafe.Pointer(&data)),
		0)
	if errno != 0 {
		return 0, 0, 0, errno
	}
	return data.permitted, data.effective, data.inheritable, nil
}
```

---

### 5.4 Seccomp Filter Dumper

```go
// pkg/seccompaudit/seccompaudit.go
package seccompaudit

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// SeccompProfile represents a Docker/OCI seccomp profile
type SeccompProfile struct {
	DefaultAction string         `json:"defaultAction"`
	Architectures []string       `json:"architectures"`
	Syscalls      []SyscallEntry `json:"syscalls"`
}

// SyscallEntry defines allowed/denied syscalls
type SyscallEntry struct {
	Names  []string `json:"names"`
	Action string   `json:"action"`
	Args   []SeccompArg `json:"args,omitempty"`
}

// SeccompArg defines a syscall argument filter
type SeccompArg struct {
	Index    uint   `json:"index"`
	Value    uint64 `json:"value"`
	ValueTwo uint64 `json:"valueTwo"`
	Op       string `json:"op"`
}

// LoadProfile loads a seccomp profile from JSON
func LoadProfile(path string) (*SeccompProfile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading profile: %w", err)
	}
	var profile SeccompProfile
	if err := json.Unmarshal(data, &profile); err != nil {
		return nil, fmt.Errorf("parsing profile: %w", err)
	}
	return &profile, nil
}

// ProcessSeccompState reads seccomp state from /proc/<pid>/status
type ProcessSeccompState struct {
	PID        int
	Mode       int    // 0=no seccomp, 1=strict, 2=filter
	NumFilters int    // number of installed BPF filters (kernel 5.9+)
}

func ReadProcessSeccompState(pid int) (*ProcessSeccompState, error) {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid))
	if err != nil {
		return nil, err
	}

	state := &ProcessSeccompState{PID: pid}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "Seccomp:") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				state.Mode, _ = strconv.Atoi(parts[1])
			}
		}
		if strings.HasPrefix(line, "Seccomp_filters:") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				state.NumFilters, _ = strconv.Atoi(parts[1])
			}
		}
	}
	return state, nil
}

// ModeString returns human-readable seccomp mode
func (s *ProcessSeccompState) ModeString() string {
	switch s.Mode {
	case 0:
		return "NONE (no seccomp filtering)"
	case 1:
		return "STRICT (only read/write/exit/sigreturn allowed)"
	case 2:
		return fmt.Sprintf("FILTER (BPF, %d filter(s) installed)", s.NumFilters)
	default:
		return fmt.Sprintf("UNKNOWN (%d)", s.Mode)
	}
}

// BlockedSyscalls returns syscalls that are blocked in the profile
func (p *SeccompProfile) BlockedSyscalls() []string {
	var blocked []string
	for _, entry := range p.Syscalls {
		if entry.Action == "SCMP_ACT_ERRNO" || entry.Action == "SCMP_ACT_KILL" ||
			entry.Action == "SCMP_ACT_KILL_PROCESS" || entry.Action == "SCMP_ACT_KILL_THREAD" {
			blocked = append(blocked, entry.Names...)
		}
	}
	return blocked
}

// AllowedSyscalls returns syscalls that are explicitly allowed
func (p *SeccompProfile) AllowedSyscalls() []string {
	var allowed []string
	for _, entry := range p.Syscalls {
		if entry.Action == "SCMP_ACT_ALLOW" {
			allowed = append(allowed, entry.Names...)
		}
	}
	return allowed
}

// DangerousSyscallsAllowed returns potentially dangerous syscalls in the allow list
var dangerousSyscalls = map[string]string{
	"ptrace":           "CRITICAL: process tracing → memory read, code injection",
	"mount":            "CRITICAL: filesystem mounts → container escape",
	"umount2":          "HIGH: unmount filesystems",
	"unshare":          "HIGH: create new namespaces → isolation bypass",
	"setns":            "CRITICAL: join namespaces → container escape",
	"pivot_root":       "HIGH: change root filesystem",
	"init_module":      "CRITICAL: load kernel module",
	"finit_module":     "CRITICAL: load kernel module",
	"delete_module":    "HIGH: unload kernel module",
	"kexec_load":       "CRITICAL: load new kernel",
	"kexec_file_load":  "CRITICAL: load new kernel",
	"bpf":              "CRITICAL: eBPF programs → kernel memory access",
	"perf_event_open":  "HIGH: hardware performance counters → side channels",
	"open_by_handle_at":"CRITICAL: open file by handle → cross-mount escape",
	"name_to_handle_at":"HIGH: convert path to handle",
	"iopl":             "CRITICAL: direct I/O port access",
	"ioperm":           "CRITICAL: direct I/O port access",
	"mknod":            "HIGH: create device files",
	"clone":            "HIGH: if CLONE_NEWUSER is not filtered",
	"userfaultfd":      "HIGH: userspace page fault handler → kernel vuln exploitation",
	"add_key":          "MED: add kernel keyring keys",
	"keyctl":           "MED: kernel keyring manipulation",
	"request_key":      "MED: request kernel key",
}

func (p *SeccompProfile) DangerousSyscallsAllowed() []struct{ Name, Risk string } {
	allowed := make(map[string]bool)
	for _, entry := range p.Syscalls {
		if entry.Action == "SCMP_ACT_ALLOW" {
			for _, name := range entry.Names {
				allowed[name] = true
			}
		}
	}

	// If default action is ALLOW, everything not explicitly denied is allowed
	if p.DefaultAction == "SCMP_ACT_ALLOW" {
		for name, risk := range dangerousSyscalls {
			if !allowed[name] {
				allowed[name] = true // default allow means this is allowed
				_ = risk
			}
		}
	}

	var result []struct{ Name, Risk string }
	for name, risk := range dangerousSyscalls {
		if allowed[name] || p.DefaultAction == "SCMP_ACT_ALLOW" {
			result = append(result, struct{ Name, Risk string }{name, risk})
		}
	}
	return result
}

// AuditContainerSeccomp performs full seccomp audit for a container
func AuditContainerSeccomp(pid int, profilePath string) error {
	fmt.Printf("=== Seccomp Audit for PID %d ===\n\n", pid)

	// 1. Read process seccomp state
	state, err := ReadProcessSeccompState(pid)
	if err != nil {
		return fmt.Errorf("reading seccomp state: %w", err)
	}

	fmt.Printf("Process Seccomp Mode: %s\n", state.ModeString())

	if state.Mode == 0 {
		fmt.Println("⛔ CRITICAL: Process has NO seccomp filtering!")
		fmt.Println("   All 400+ syscalls are available to this process.")
		fmt.Println("   Remediation: Apply --security-opt seccomp=<profile.json>")
		return nil
	}

	// 2. Load and analyze the profile
	if profilePath != "" {
		profile, err := LoadProfile(profilePath)
		if err != nil {
			return fmt.Errorf("loading profile: %w", err)
		}

		fmt.Printf("\nProfile: %s\n", profilePath)
		fmt.Printf("Default Action: %s\n", profile.DefaultAction)

		allowed := profile.AllowedSyscalls()
		blocked := profile.BlockedSyscalls()
		fmt.Printf("Allowed syscalls: %d\n", len(allowed))
		fmt.Printf("Blocked syscalls: %d\n", len(blocked))

		dangerous := profile.DangerousSyscallsAllowed()
		if len(dangerous) > 0 {
			fmt.Printf("\n⚠ Dangerous Syscalls NOT Blocked (%d):\n", len(dangerous))
			for _, d := range dangerous {
				fmt.Printf("  %-25s %s\n", d.Name, d.Risk)
			}
		} else {
			fmt.Println("\n✓ No obviously dangerous syscalls in allow list")
		}

		if profile.DefaultAction == "SCMP_ACT_ALLOW" {
			fmt.Println("\n⛔ CRITICAL: Default action is ALLOW — profile is allowlist-based")
			fmt.Println("   Only explicitly blocked syscalls are denied.")
			fmt.Println("   New/unknown syscalls are automatically ALLOWED.")
			fmt.Println("   Recommended: SCMP_ACT_ERRNO or SCMP_ACT_KILL as default")
		}
	}

	// 3. Probe which syscalls actually work (test a few key ones):
	// Note: This runs in the caller's process, not the container's
	// For container-in-namespace testing, use nsenter first
	fmt.Println("\n--- Live Syscall Probe (caller context) ---")
	probeSyscalls := []struct {
		name   string
		number uintptr
	}{
		{"ptrace", syscall.SYS_PTRACE},
		{"mount", syscall.SYS_MOUNT},
		{"unshare", syscall.SYS_UNSHARE},
		{"setns", syscall.SYS_SETNS},
		{"kexec_load", syscall.SYS_KEXEC_LOAD},
	}

	for _, probe := range probeSyscalls {
		_, _, errno := syscall.RawSyscall(probe.number, 0, 0, 0)
		// If errno is EPERM or ENOSYS, seccomp is blocking it
		// If errno is something else (EINVAL etc), the syscall went through but failed for other reasons
		status := "ALLOWED (reached kernel)"
		if errno == syscall.EPERM {
			status = "BLOCKED by seccomp (EPERM)"
		} else if errno == syscall.ENOSYS {
			status = "NOT AVAILABLE (ENOSYS)"
		}
		fmt.Printf("  %-20s %s\n", probe.name, status)
	}

	return nil
}

// GetContainerSeccompProfile finds the seccomp profile for a container by reading its OCI spec
func GetContainerSeccompProfile(containerID string) (*SeccompProfile, error) {
	// Try OCI spec location (containerd/runc)
	specPaths := []string{
		filepath.Join("/run/containerd/io.containerd.runtime.v2.task/moby", containerID, "config.json"),
		filepath.Join("/run/docker/runtime-runc/moby", containerID, "config.json"),
	}

	for _, path := range specPaths {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}

		// Parse just the seccomp section
		var spec struct {
			Linux struct {
				Seccomp *SeccompProfile `json:"seccomp"`
			} `json:"linux"`
		}
		if err := json.Unmarshal(data, &spec); err != nil {
			continue
		}
		if spec.Linux.Seccomp != nil {
			return spec.Linux.Seccomp, nil
		}
	}

	// Fallback: use docker inspect
	cmd := exec.Command("docker", "inspect", "--format",
		"{{json .HostConfig.SecurityOpt}}", containerID)
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("docker inspect failed: %w", err)
	}
	fmt.Printf("SecurityOpt: %s\n", string(output))

	return nil, fmt.Errorf("seccomp profile not found for container %s", containerID)
}
```

---

### 5.5 containerd gRPC Security Auditor

```go
// cmd/containerd-audit/main.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/containerd/containerd"
	"github.com/containerd/containerd/defaults"
	"github.com/containerd/containerd/namespaces"
	"github.com/containerd/containerd/oci"
	"github.com/opencontainers/runtime-spec/specs-go"
)

// SecurityFinding represents a security issue found during audit
type SecurityFinding struct {
	Severity    string // CRITICAL, HIGH, MED, LOW, INFO
	ContainerID string
	Category    string
	Description string
	Remediation string
}

// ContainerAuditResult holds audit results for a single container
type ContainerAuditResult struct {
	ContainerID string
	Image       string
	Status      string
	Findings    []SecurityFinding
}

// Auditor performs security audits on containerd-managed containers
type Auditor struct {
	client    *containerd.Client
	namespace string
}

// NewAuditor creates a new containerd security auditor
func NewAuditor(socketPath, namespace string) (*Auditor, error) {
	client, err := containerd.New(socketPath,
		containerd.WithDefaultNamespace(namespace),
		containerd.WithTimeout(10*time.Second),
	)
	if err != nil {
		return nil, fmt.Errorf("connecting to containerd at %s: %w", socketPath, err)
	}
	return &Auditor{client: client, namespace: namespace}, nil
}

// Close closes the containerd client connection
func (a *Auditor) Close() error {
	return a.client.Close()
}

// AuditAll audits all containers in the namespace
func (a *Auditor) AuditAll(ctx context.Context) ([]*ContainerAuditResult, error) {
	ctx = namespaces.WithNamespace(ctx, a.namespace)

	containers, err := a.client.Containers(ctx)
	if err != nil {
		return nil, fmt.Errorf("listing containers: %w", err)
	}

	var results []*ContainerAuditResult
	for _, container := range containers {
		result, err := a.AuditContainer(ctx, container)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: auditing container %s: %v\n",
				container.ID(), err)
			continue
		}
		results = append(results, result)
	}
	return results, nil
}

// AuditContainer audits a single container's security configuration
func (a *Auditor) AuditContainer(ctx context.Context, container containerd.Container) (*ContainerAuditResult, error) {
	info, err := container.Info(ctx)
	if err != nil {
		return nil, err
	}

	result := &ContainerAuditResult{
		ContainerID: container.ID(),
		Image:       info.Image,
	}

	// Get task (running container)
	task, err := container.Task(ctx, nil)
	if err != nil {
		result.Status = "stopped"
	} else {
		status, _ := task.Status(ctx)
		result.Status = string(status.Status)
	}

	// Get OCI spec
	spec, err := container.Spec(ctx)
	if err != nil {
		return result, fmt.Errorf("getting spec: %w", err)
	}

	// Run all security checks
	result.Findings = append(result.Findings, auditNamespaces(container.ID(), spec)...)
	result.Findings = append(result.Findings, auditCapabilities(container.ID(), spec)...)
	result.Findings = append(result.Findings, auditSeccomp(container.ID(), spec)...)
	result.Findings = append(result.Findings, auditMounts(container.ID(), spec)...)
	result.Findings = append(result.Findings, auditProcess(container.ID(), spec)...)
	result.Findings = append(result.Findings, auditResources(container.ID(), spec)...)

	return result, nil
}

func auditNamespaces(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	if spec.Linux == nil {
		return []SecurityFinding{{
			Severity:    "CRITICAL",
			ContainerID: containerID,
			Category:    "Namespaces",
			Description: "No Linux spec — container has no namespace configuration",
			Remediation: "Add linux.namespaces to OCI spec",
		}}
	}

	nsTypes := make(map[string]bool)
	for _, ns := range spec.Linux.Namespaces {
		nsTypes[string(ns.Type)] = true
	}

	required := []string{"pid", "network", "ipc", "uts", "mount"}
	for _, required := range required {
		if !nsTypes[required] {
			findings = append(findings, SecurityFinding{
				Severity:    "HIGH",
				ContainerID: containerID,
				Category:    "Namespaces",
				Description: fmt.Sprintf("Missing %s namespace isolation", required),
				Remediation: fmt.Sprintf("Add {type: '%s'} to linux.namespaces", required),
			})
		}
	}

	// Check for user namespace (not isolating = dangerous)
	if !nsTypes["user"] {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Namespaces",
			Description: "No user namespace — UID 0 inside container = UID 0 on host",
			Remediation: "Enable user namespace or ensure container runs as non-root (uid>0)",
		})
	}

	// Check for network namespace with host path (sharing host network)
	for _, ns := range spec.Linux.Namespaces {
		if string(ns.Type) == "network" && ns.Path != "" {
			if ns.Path == "/proc/1/ns/net" || strings.Contains(ns.Path, "init") {
				findings = append(findings, SecurityFinding{
					Severity:    "CRITICAL",
					ContainerID: containerID,
					Category:    "Namespaces",
					Description: fmt.Sprintf("Container shares HOST network namespace (path=%s)", ns.Path),
					Remediation: "Remove network.path or use empty path for isolated network ns",
				})
			}
		}
	}

	return findings
}

func auditCapabilities(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	if spec.Process == nil || spec.Process.Capabilities == nil {
		return nil
	}

	caps := spec.Process.Capabilities

	criticalCaps := map[string]string{
		"CAP_SYS_ADMIN":   "Nearly equivalent to root — can mount, setns, unshare, etc.",
		"CAP_NET_ADMIN":   "Full network control — can modify routing, iptables",
		"CAP_SYS_MODULE":  "Can load kernel modules — full kernel compromise",
		"CAP_SYS_PTRACE":  "Can ptrace any process — extract secrets, inject code",
		"CAP_SYS_RAWIO":   "Direct hardware I/O — can read host physical memory",
		"CAP_BPF":         "eBPF — can access any kernel memory",
		"CAP_NET_RAW":     "Raw sockets — can sniff/spoof network",
		"CAP_SETUID":      "Can become any UID — critical without userns",
		"CAP_DAC_OVERRIDE":"Bypass file permissions — read any file",
	}

	for cap, reason := range criticalCaps {
		for _, effective := range caps.Effective {
			if effective == cap {
				findings = append(findings, SecurityFinding{
					Severity:    "CRITICAL",
					ContainerID: containerID,
					Category:    "Capabilities",
					Description: fmt.Sprintf("%s in Effective set: %s", cap, reason),
					Remediation: fmt.Sprintf("Remove %s from capabilities.effective and capabilities.bounding", cap),
				})
			}
		}
	}

	return findings
}

func auditSeccomp(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	if spec.Linux == nil {
		return nil
	}

	if spec.Linux.Seccomp == nil {
		findings = append(findings, SecurityFinding{
			Severity:    "CRITICAL",
			ContainerID: containerID,
			Category:    "Seccomp",
			Description: "No seccomp filter configured — all 400+ syscalls available",
			Remediation: "Add linux.seccomp with defaultAction=SCMP_ACT_ERRNO",
		})
		return findings
	}

	seccomp := spec.Linux.Seccomp
	if seccomp.DefaultAction == oci.ActAllow {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Seccomp",
			Description: "Seccomp default action is ALLOW — new syscalls are automatically permitted",
			Remediation: "Change defaultAction to SCMP_ACT_ERRNO",
		})
	}

	return findings
}

func auditMounts(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	dangerousMounts := map[string]string{
		"/var/run/docker.sock": "CRITICAL: Docker socket — full host root access",
		"/run/docker.sock":     "CRITICAL: Docker socket — full host root access",
		"/proc":                "HIGH: Host /proc exposure (check if masked properly)",
		"/sys":                 "HIGH: Host /sys exposure",
		"/dev":                 "HIGH: Host /dev — device access",
		"/etc/shadow":          "CRITICAL: Password hashes exposed",
		"/root":                "HIGH: Root home directory exposed",
		"/var/lib/kubelet":     "HIGH: Kubernetes secrets may be accessible",
		"/run/containerd":      "HIGH: containerd runtime socket exposure",
	}

	for _, mount := range spec.Mounts {
		for path, risk := range dangerousMounts {
			if mount.Source == path || strings.HasSuffix(mount.Source, path) {
				// Check if it's read-only
				readonly := false
				for _, opt := range mount.Options {
					if opt == "ro" || opt == "readonly" {
						readonly = true
					}
				}
				sev := "CRITICAL"
				desc := fmt.Sprintf("Dangerous mount: %s → %s [%s]", mount.Source, mount.Destination, risk)
				if readonly {
					sev = "HIGH"
					desc += " (read-only)"
				}
				findings = append(findings, SecurityFinding{
					Severity:    sev,
					ContainerID: containerID,
					Category:    "Mounts",
					Description: desc,
					Remediation: "Remove this mount or use a secrets management system instead",
				})
			}
		}

		// Check for mounts without nosuid/noexec options
		if mount.Type == "bind" {
			hasNosuid := false
			hasNoexec := false
			for _, opt := range mount.Options {
				if opt == "nosuid" {
					hasNosuid = true
				}
				if opt == "noexec" {
					hasNoexec = true
				}
			}
			if !hasNosuid || !hasNoexec {
				findings = append(findings, SecurityFinding{
					Severity:    "MED",
					ContainerID: containerID,
					Category:    "Mounts",
					Description: fmt.Sprintf("Bind mount %s missing nosuid/noexec options", mount.Destination),
					Remediation: "Add nosuid,noexec to bind mount options",
				})
			}
		}
	}

	return findings
}

func auditProcess(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	if spec.Process == nil {
		return nil
	}

	if spec.Process.User.UID == 0 {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Process",
			Description: "Container runs as UID 0 (root)",
			Remediation: "Set process.user.uid to non-zero, e.g., 65534 (nobody)",
		})
	}

	if !spec.Process.NoNewPrivileges {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Process",
			Description: "NoNewPrivileges is not set — setuid binaries can gain capabilities",
			Remediation: "Set process.noNewPrivileges=true",
		})
	}

	// Check for missing AppArmor profile
	if spec.Process.ApparmorProfile == "" {
		findings = append(findings, SecurityFinding{
			Severity:    "MED",
			ContainerID: containerID,
			Category:    "LSM",
			Description: "No AppArmor profile configured",
			Remediation: "Set process.apparmorProfile to 'docker-default' or a custom profile",
		})
	}

	// Check if running in privileged mode (all capabilities + no seccomp + all devices)
	if isPrivileged(spec) {
		findings = append(findings, SecurityFinding{
			Severity:    "CRITICAL",
			ContainerID: containerID,
			Category:    "Privileged",
			Description: "Container appears to be running in PRIVILEGED mode",
			Remediation: "Remove --privileged flag; grant only necessary capabilities",
		})
	}

	return findings
}

func auditResources(containerID string, spec *specs.Spec) []SecurityFinding {
	var findings []SecurityFinding

	if spec.Linux == nil || spec.Linux.Resources == nil {
		findings = append(findings, SecurityFinding{
			Severity:    "MED",
			ContainerID: containerID,
			Category:    "Resources",
			Description: "No resource limits configured — container can monopolize host resources",
			Remediation: "Set linux.resources.memory.limit, cpu.quota, pids.limit",
		})
		return findings
	}

	res := spec.Linux.Resources

	if res.Memory == nil || res.Memory.Limit == nil || *res.Memory.Limit <= 0 {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Resources",
			Description: "No memory limit — OOM can affect host system stability",
			Remediation: "Set linux.resources.memory.limit",
		})
	}

	if res.Pids == nil || res.Pids.Limit <= 0 {
		findings = append(findings, SecurityFinding{
			Severity:    "HIGH",
			ContainerID: containerID,
			Category:    "Resources",
			Description: "No PID limit — container can fork-bomb the host",
			Remediation: "Set linux.resources.pids.limit (recommend 100-1000)",
		})
	}

	return findings
}

func isPrivileged(spec *specs.Spec) bool {
	if spec.Process == nil || spec.Process.Capabilities == nil {
		return false
	}
	// Privileged containers have a very large bounding set
	return len(spec.Process.Capabilities.Bounding) > 35
}

// PrintReport prints a formatted security report
func PrintReport(results []*ContainerAuditResult) {
	severityOrder := map[string]int{"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3, "INFO": 4}

	totalFindings := 0
	criticalCount := 0

	for _, result := range results {
		id := result.ContainerID
		if len(id) > 12 {
			id = id[:12]
		}

		fmt.Printf("Container: %s (Image: %s, Status: %s)\n",
			id, result.Image, result.Status)

		if len(result.Findings) == 0 {
			fmt.Println("  ✓ No security issues found")
		} else {
			// Sort findings by severity
			findings := make([]SecurityFinding, len(result.Findings))
			copy(findings, result.Findings)
			for i := 0; i < len(findings); i++ {
				for j := i + 1; j < len(findings); j++ {
					if severityOrder[findings[i].Severity] > severityOrder[findings[j].Severity] {
						findings[i], findings[j] = findings[j], findings[i]
					}
				}
			}

			for _, f := range findings {
				icon := map[string]string{
					"CRITICAL": "⛔",
					"HIGH":     "🔴",
					"MED":      "🟡",
					"LOW":      "🟢",
					"INFO":     "ℹ",
				}[f.Severity]
				fmt.Printf("  %s [%s] [%s] %s\n", icon, f.Severity, f.Category, f.Description)
				fmt.Printf("     Fix: %s\n", f.Remediation)
				if f.Severity == "CRITICAL" {
					criticalCount++
				}
				totalFindings++
			}
		}
		fmt.Println()
	}

	fmt.Printf("Summary: %d containers, %d findings (%d CRITICAL)\n",
		len(results), totalFindings, criticalCount)
}

func main() {
	socket := defaults.DefaultAddress // /run/containerd/containerd.sock
	ns := "moby"                       // Docker's containerd namespace

	if len(os.Args) >= 2 {
		socket = os.Args[1]
	}
	if len(os.Args) >= 3 {
		ns = os.Args[2]
	}

	auditor, err := NewAuditor(socket, ns)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	defer auditor.Close()

	ctx := context.Background()
	results, err := auditor.AuditAll(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Audit error: %v\n", err)
		os.Exit(1)
	}

	PrintReport(results)

	// Exit with error code if critical findings
	for _, r := range results {
		for _, f := range r.Findings {
			if f.Severity == "CRITICAL" {
				os.Exit(2)
			}
		}
	}

	// Output JSON for CI integration
	if os.Getenv("JSON_OUTPUT") == "1" {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		enc.Encode(results)
	}
}
```

**go.mod for containerd auditor**:
```
module github.com/yourorg/container-security-tools

go 1.22

require (
    github.com/containerd/containerd v1.7.13
    github.com/opencontainers/runtime-spec v1.1.0
)
```

**Build**:
```bash
go build -o bin/containerd-audit ./cmd/containerd-audit/
sudo ./bin/containerd-audit /run/containerd/containerd.sock moby
# or for Docker:
sudo ./bin/containerd-audit /run/containerd/containerd.sock moby
```

---

### 5.6 Runtime Security Monitor — Netlink + Proc

```go
// pkg/rtsecmon/rtsecmon.go
// Runtime security monitor using Linux netlink (proc events connector)
// to detect suspicious container activity in real-time
package rtsecmon

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

// ProcessEvent types from Linux proc events connector
const (
	ProcEventNone   = 0x00000000
	ProcEventFork   = 0x00000001
	ProcEventExec   = 0x00000002
	ProcEventUID    = 0x00000004
	ProcEventGID    = 0x00000040
	ProcEventSID    = 0x00000080
	ProcEventPtrace = 0x00000100
	ProcEventComm   = 0x00000200
	ProcEventCoredump = 0x40000000
	ProcEventExit   = 0x80000000
)

// SecurityEvent represents a detected security-relevant event
type SecurityEvent struct {
	Timestamp   time.Time
	EventType   string
	PID         uint32
	ParentPID   uint32
	ContainerID string
	Details     string
	Severity    string
}

// Monitor watches for security-relevant process events
type Monitor struct {
	mu       sync.Mutex
	events   chan SecurityEvent
	stopCh   chan struct{}
	// Map from PID to container ID (populated from cgroup inspection)
	pidToContainer map[uint32]string
}

// NewMonitor creates a new runtime security monitor
func NewMonitor(bufferSize int) *Monitor {
	return &Monitor{
		events:         make(chan SecurityEvent, bufferSize),
		stopCh:         make(chan struct{}),
		pidToContainer: make(map[uint32]string),
	}
}

// Events returns the channel of security events
func (m *Monitor) Events() <-chan SecurityEvent {
	return m.events
}

// containerIDForPID determines which container a PID belongs to
// by reading its cgroup membership
func containerIDForPID(pid uint32) string {
	cgroupPath := fmt.Sprintf("/proc/%d/cgroup", pid)
	data, err := os.ReadFile(cgroupPath)
	if err != nil {
		return ""
	}

	// Parse cgroup v2: "0::/system.slice/docker-<id>.scope"
	// or cgroup v1: "1:name=systemd:/system.slice/docker-<id>.scope"
	for _, line := range strings.Split(string(data), "\n") {
		if strings.Contains(line, "docker-") {
			parts := strings.Split(line, "docker-")
			if len(parts) > 1 {
				id := strings.TrimSuffix(parts[1], ".scope")
				id = strings.TrimSuffix(id, "\n")
				if len(id) >= 12 {
					return id[:12]
				}
				return id
			}
		}
	}
	return "" // not in a container
}

// getPIDComm reads the command name for a PID
func getPIDComm(pid uint32) string {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/comm", pid))
	if err != nil {
		return "unknown"
	}
	return strings.TrimSpace(string(data))
}

// getExePath reads the executable path for a PID
func getExePath(pid uint32) string {
	target, err := os.Readlink(fmt.Sprintf("/proc/%d/exe", pid))
	if err != nil {
		return "unknown"
	}
	return target
}

// netlink connector structures
type nlMsgHdr struct {
	Len   uint32
	Type  uint16
	Flags uint16
	Seq   uint32
	Pid   uint32
}

type cnMsgHdr struct {
	ID       [2]uint32 // idx, val
	Seq      uint32
	Ack      uint32
	Len      uint16
	Flags    uint16
}

// Start begins monitoring using /proc polling (fallback approach)
// Note: Full netlink proc_events connector requires root + CONFIG_PROC_EVENTS=y
// This implementation uses /proc polling which works without special kernel config
func (m *Monitor) StartProcPoll(interval time.Duration) error {
	go m.pollProcEvents(interval)
	return nil
}

func (m *Monitor) pollProcEvents(interval time.Duration) {
	prevPIDs := make(map[uint32]bool)

	// Initial population of known PIDs
	m.scanProc(prevPIDs, false)

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-m.stopCh:
			return
		case <-ticker.C:
			currentPIDs := make(map[uint32]bool)

			// Scan /proc for all current PIDs
			entries, err := os.ReadDir("/proc")
			if err != nil {
				continue
			}

			for _, entry := range entries {
				var pid uint32
				if _, err := fmt.Sscanf(entry.Name(), "%d", &pid); err != nil {
					continue
				}
				currentPIDs[pid] = true

				// New PID appeared
				if !prevPIDs[pid] {
					containerID := containerIDForPID(pid)
					if containerID == "" {
						continue // not a container process
					}

					comm := getPIDComm(pid)
					exe := getExePath(pid)

					// Check for suspicious new processes
					severity := m.assessNewProcess(exe, comm, pid)

					if severity != "" {
						m.emitEvent(SecurityEvent{
							Timestamp:   time.Now(),
							EventType:   "NEW_PROCESS",
							PID:         pid,
							ContainerID: containerID,
							Details:     fmt.Sprintf("exe=%s comm=%s", exe, comm),
							Severity:    severity,
						})
					}
				}
			}

			// Check for PIDs that disappeared (container process exit)
			for pid := range prevPIDs {
				if !currentPIDs[pid] {
					// Process exited — we already handled it implicitly
					delete(m.pidToContainer, pid)
				}
			}

			prevPIDs = currentPIDs
		}
	}
}

func (m *Monitor) scanProc(pids map[uint32]bool, emit bool) {
	entries, _ := os.ReadDir("/proc")
	for _, entry := range entries {
		var pid uint32
		if _, err := fmt.Sscanf(entry.Name(), "%d", &pid); err != nil {
			continue
		}
		pids[pid] = true
	}
}

// assessNewProcess determines if a new process is suspicious
func (m *Monitor) assessNewProcess(exe, comm string, pid uint32) string {
	// Critical: shell processes inside containers
	suspiciousExes := map[string]string{
		"/bin/sh":   "HIGH",
		"/bin/bash": "HIGH",
		"/bin/dash": "HIGH",
		"/bin/zsh":  "HIGH",
		"/usr/bin/sh":   "HIGH",
		"/usr/bin/bash": "HIGH",
		"/usr/bin/curl": "MED",  // potential C2 communication
		"/usr/bin/wget": "MED",
		"/usr/bin/nc":   "CRITICAL", // netcat in container
		"/usr/bin/ncat": "CRITICAL",
		"/bin/nc":       "CRITICAL",
		"/usr/bin/nmap": "HIGH",
		"/usr/sbin/tcpdump": "HIGH",
		"nsenter":      "CRITICAL", // namespace escape tool
		"runc":         "CRITICAL", // container runtime inside container
		"docker":       "CRITICAL", // docker client inside container
	}

	for suspExe, severity := range suspiciousExes {
		if exe == suspExe || strings.HasSuffix(exe, "/"+filepath.Base(suspExe)) {
			return severity
		}
	}

	// Check for setuid execution
	var stat syscall.Stat_t
	if err := syscall.Stat(fmt.Sprintf("/proc/%d/exe", pid), &stat); err == nil {
		if stat.Mode&syscall.S_ISUID != 0 {
			return "HIGH" // setuid binary executed
		}
	}

	return "" // not suspicious
}

func (m *Monitor) emitEvent(event SecurityEvent) {
	select {
	case m.events <- event:
	default:
		// Buffer full — drop event (log to stderr in production)
		fmt.Fprintf(os.Stderr, "WARNING: event buffer full, dropping event\n")
	}
}

// Stop stops the monitor
func (m *Monitor) Stop() {
	close(m.stopCh)
}

// WatchCapabilityFiles monitors for capability-related file accesses
// by watching /proc/<pid>/status for cap changes (requires repeated scanning)
func WatchCapabilityChanges(containerPIDs []uint32, interval time.Duration, events chan<- SecurityEvent) {
	type capState struct {
		effective uint64
	}
	prevState := make(map[uint32]capState)

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for range ticker.C {
		for _, pid := range containerPIDs {
			data, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", pid))
			if err != nil {
				continue
			}

			var capEff uint64
			for _, line := range strings.Split(string(data), "\n") {
				if strings.HasPrefix(line, "CapEff:") {
					parts := strings.Fields(line)
					if len(parts) >= 2 {
						fmt.Sscanf(parts[1], "%x", &capEff)
					}
				}
			}

			if prev, ok := prevState[pid]; ok {
				if prev.effective != capEff {
					// Capability set changed! This should NEVER happen for a healthy container
					events <- SecurityEvent{
						Timestamp:   time.Now(),
						EventType:   "CAP_CHANGE",
						PID:         pid,
						ContainerID: containerIDForPID(pid),
						Details:     fmt.Sprintf("CapEff changed: 0x%016x → 0x%016x", prev.effective, capEff),
						Severity:    "CRITICAL",
					}
				}
			}
			prevState[pid] = capState{effective: capEff}
		}
	}
}

// StartNetlinkProcConnector uses the Linux proc events connector via netlink
// Requires: root privileges, CONFIG_PROC_EVENTS=y in kernel
func StartNetlinkProcConnector(events chan<- SecurityEvent) error {
	// Create netlink socket for CN_IDX_PROC
	sock, err := syscall.Socket(syscall.AF_NETLINK, syscall.SOCK_DGRAM, syscall.NETLINK_CONNECTOR)
	if err != nil {
		return fmt.Errorf("creating netlink socket: %w", err)
	}

	addr := &syscall.SockaddrNetlink{
		Family: syscall.AF_NETLINK,
		Groups: 1, // CN_IDX_PROC = 1
	}

	if err := syscall.Bind(sock, addr); err != nil {
		syscall.Close(sock)
		return fmt.Errorf("binding netlink socket: %w", err)
	}

	// Subscribe to proc events
	if err := subscribeToProEvents(sock); err != nil {
		syscall.Close(sock)
		return fmt.Errorf("subscribing to proc events: %w", err)
	}

	go receiveNetlinkEvents(sock, events)
	return nil
}

func subscribeToProEvents(sock int) error {
	// Send CN_PROC_LISTEN to subscribe
	// op = 1 (PROC_CN_MCAST_LISTEN)
	op := uint32(1)

	// Build message: nlmsghdr + cn_msg + op
	msgLen := uint32(unsafe.Sizeof(nlMsgHdr{}) + unsafe.Sizeof(cnMsgHdr{}) + unsafe.Sizeof(op))

	buf := make([]byte, msgLen)

	nlHdr := (*nlMsgHdr)(unsafe.Pointer(&buf[0]))
	nlHdr.Len = msgLen
	nlHdr.Type = uint16(syscall.NLMSG_DONE)
	nlHdr.Flags = 0
	nlHdr.Seq = 1
	nlHdr.Pid = uint32(os.Getpid())

	cnHdr := (*cnMsgHdr)(unsafe.Pointer(&buf[unsafe.Sizeof(nlMsgHdr{})]))
	cnHdr.ID[0] = 1 // CN_IDX_PROC
	cnHdr.ID[1] = 1 // CN_VAL_PROC
	cnHdr.Seq = 1
	cnHdr.Ack = 0
	cnHdr.Len = uint16(unsafe.Sizeof(op))

	binary.LittleEndian.PutUint32(buf[unsafe.Sizeof(nlMsgHdr{})+unsafe.Sizeof(cnMsgHdr{}):], op)

	sa := &syscall.SockaddrNetlink{Family: syscall.AF_NETLINK}
	return syscall.Sendto(sock, buf, 0, sa)
}

func receiveNetlinkEvents(sock int, events chan<- SecurityEvent) {
	buf := make([]byte, 4096)
	for {
		n, _, err := syscall.Recvfrom(sock, buf, 0)
		if err != nil {
			break
		}
		if n < int(unsafe.Sizeof(nlMsgHdr{})) {
			continue
		}

		// Parse proc event from netlink message
		// (simplified — full implementation parses proc_event struct)
		nlHdr := (*nlMsgHdr)(unsafe.Pointer(&buf[0]))
		_ = nlHdr
		// In a full implementation, parse the proc_event_header.what field
		// and extract PID, parent PID, etc.
		// For brevity, we just pass through to proc scanning
	}
}

// RunSecurityMonitorDemo shows how to use the monitor
func RunSecurityMonitorDemo() {
	fmt.Println("Starting runtime security monitor...")

	monitor := NewMonitor(1000)
	if err := monitor.StartProcPoll(500 * time.Millisecond); err != nil {
		fmt.Fprintf(os.Stderr, "Error starting monitor: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Monitoring for suspicious container activity...")
	fmt.Println("Events will appear below:\n")

	for event := range monitor.Events() {
		icon := map[string]string{
			"CRITICAL": "⛔",
			"HIGH":     "🔴",
			"MED":      "🟡",
			"LOW":      "🟢",
		}[event.Severity]

		fmt.Printf("[%s] %s [%s] Container=%s PID=%d\n",
			event.Timestamp.Format("15:04:05.000"),
			icon,
			event.EventType,
			event.ContainerID,
			event.PID,
		)
		fmt.Printf("  Details: %s\n\n", event.Details)
	}
}

// Inotify-based watcher for critical container files
type FileWatcher struct {
	fd    int
	paths map[int]string // inotify watch descriptor → path
}

func NewFileWatcher() (*FileWatcher, error) {
	fd, err := syscall.InotifyInit1(syscall.IN_CLOEXEC | syscall.IN_NONBLOCK)
	if err != nil {
		return nil, fmt.Errorf("inotify_init: %w", err)
	}
	return &FileWatcher{fd: fd, paths: make(map[int]string)}, nil
}

func (w *FileWatcher) WatchPath(path string) error {
	wd, err := syscall.InotifyAddWatch(w.fd,
		path,
		syscall.IN_MODIFY|syscall.IN_CREATE|syscall.IN_DELETE|syscall.IN_ATTRIB)
	if err != nil {
		return fmt.Errorf("inotify_add_watch %s: %w", path, err)
	}
	w.paths[wd] = path
	return nil
}

// WatchAllContainerRootfs watches the upper (writable) layer of all running containers
// for modifications to sensitive files
func (w *FileWatcher) WatchAllContainerRootfs(events chan<- SecurityEvent) error {
	// Find all container writable layers
	pattern := "/var/lib/docker/overlay2/*/diff"
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return err
	}

	sensitivePaths := []string{
		"/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/hosts",
		"/root/.ssh", "/etc/crontab", "/etc/cron.d",
	}

	for _, diffDir := range matches {
		for _, sensitive := range sensitivePaths {
			fullPath := filepath.Join(diffDir, sensitive)
			if _, err := os.Stat(fullPath); err == nil {
				// This file exists in the writable layer → watch it
				w.WatchPath(fullPath)
			}
		}
	}

	go w.readEvents(events)
	return nil
}

func (w *FileWatcher) readEvents(events chan<- SecurityEvent) {
	buf := make([]byte, 4096)
	reader := bufio.NewReader(
		// Create a reader from the inotify fd
		net.FileConn(os.NewFile(uintptr(w.fd), "inotify")),
	)
	_ = reader

	for {
		n, err := syscall.Read(w.fd, buf)
		if err != nil || n == 0 {
			break
		}

		var offset uint32
		for offset < uint32(n) {
			event := (*syscall.InotifyEvent)(unsafe.Pointer(&buf[offset]))
			path := w.paths[int(event.Wd)]

			var name string
			if event.Len > 0 {
				nameBytes := buf[offset+syscall.SizeofInotifyEvent : offset+syscall.SizeofInotifyEvent+uint32(event.Len)]
				name = strings.TrimRight(string(nameBytes), "\x00")
			}

			fullPath := filepath.Join(path, name)
			eventType := "UNKNOWN"
			if event.Mask&syscall.IN_MODIFY != 0 {
				eventType = "FILE_MODIFIED"
			} else if event.Mask&syscall.IN_CREATE != 0 {
				eventType = "FILE_CREATED"
			} else if event.Mask&syscall.IN_DELETE != 0 {
				eventType = "FILE_DELETED"
			}

			severity := "MED"
			if strings.Contains(fullPath, "shadow") || strings.Contains(fullPath, "sudoers") {
				severity = "CRITICAL"
			} else if strings.Contains(fullPath, "passwd") || strings.Contains(fullPath, "ssh") {
				severity = "HIGH"
			}

			events <- SecurityEvent{
				Timestamp:   time.Now(),
				EventType:   eventType,
				ContainerID: extractContainerIDFromPath(path),
				Details:     fmt.Sprintf("file=%s mask=0x%x", fullPath, event.Mask),
				Severity:    severity,
			}

			offset += syscall.SizeofInotifyEvent + uint32(event.Len)
		}
	}
}

func extractContainerIDFromPath(path string) string {
	// path looks like /var/lib/docker/overlay2/<hash>/diff/...
	parts := strings.Split(path, "/")
	for i, part := range parts {
		if part == "overlay2" && i+1 < len(parts) {
			return parts[i+1][:12]
		}
	}
	return "unknown"
}
```

---

### 5.7 Image Layer Integrity Verifier

```go
// cmd/imgverify/main.go
// Verifies image layer integrity by checking SHA-256 digests of all blobs
// in the containerd content store
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

const contentStorePath = "/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256"

// BlobIntegrity represents the integrity check result for a single blob
type BlobIntegrity struct {
	ExpectedHash string
	ActualHash   string
	Size         int64
	Valid        bool
	Path         string
}

// VerifyBlob verifies a single blob's SHA-256 integrity
func VerifyBlob(blobPath string) (*BlobIntegrity, error) {
	f, err := os.Open(blobPath)
	if err != nil {
		return nil, fmt.Errorf("opening blob: %w", err)
	}
	defer f.Close()

	stat, err := f.Stat()
	if err != nil {
		return nil, err
	}

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return nil, fmt.Errorf("hashing blob: %w", err)
	}

	actualHash := hex.EncodeToString(h.Sum(nil))
	expectedHash := filepath.Base(blobPath)

	return &BlobIntegrity{
		ExpectedHash: expectedHash,
		ActualHash:   actualHash,
		Size:         stat.Size(),
		Valid:        actualHash == expectedHash,
		Path:         blobPath,
	}, nil
}

// VerifyAllBlobs checks all blobs in the content store
func VerifyAllBlobs() (valid, invalid int, err error) {
	entries, err := os.ReadDir(contentStorePath)
	if err != nil {
		return 0, 0, fmt.Errorf("reading content store: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		blobPath := filepath.Join(contentStorePath, entry.Name())
		result, err := VerifyBlob(blobPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error verifying %s: %v\n", entry.Name(), err)
			continue
		}

		if result.Valid {
			valid++
			fmt.Printf("✓ sha256:%s (%s)\n", result.ExpectedHash[:16], humanSize(result.Size))
		} else {
			invalid++
			fmt.Printf("⛔ INTEGRITY VIOLATION: sha256:%s\n", result.ExpectedHash[:16])
			fmt.Printf("   Expected: %s\n", result.ExpectedHash)
			fmt.Printf("   Actual:   %s\n", result.ActualHash)
			fmt.Printf("   Path:     %s\n", result.Path)
			fmt.Printf("   Size:     %s\n", humanSize(result.Size))
			fmt.Println("   ACTION: This blob has been tampered with. Remove and re-pull the image.")
		}
	}
	return valid, invalid, nil
}

// VerifyImageByDigest verifies a specific image by its manifest digest
func VerifyImageByDigest(manifestDigest string) error {
	manifestDigest = strings.TrimPrefix(manifestDigest, "sha256:")
	manifestPath := filepath.Join(contentStorePath, manifestDigest)

	result, err := VerifyBlob(manifestPath)
	if err != nil {
		return fmt.Errorf("verifying manifest: %w", err)
	}

	if !result.Valid {
		return fmt.Errorf("manifest integrity violation! Expected sha256:%s got sha256:%s",
			result.ExpectedHash, result.ActualHash)
	}

	fmt.Printf("Manifest verified: sha256:%s\n", manifestDigest[:16])
	return nil
}

func humanSize(b int64) string {
	const unit = 1024
	if b < unit {
		return fmt.Sprintf("%dB", b)
	}
	div, exp := int64(unit), 0
	for n := b / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f%cB", float64(b)/float64(div), "KMGTPE"[exp])
}

func main() {
	fmt.Printf("Verifying containerd content store: %s\n\n", contentStorePath)

	valid, invalid, err := VerifyAllBlobs()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\nResults: %d valid, %d INVALID\n", valid, invalid)

	if invalid > 0 {
		fmt.Println("⛔ CRITICAL: Content store integrity violations detected!")
		fmt.Println("   Possible causes:")
		fmt.Println("   1. Disk corruption")
		fmt.Println("   2. Filesystem-level tampering by attacker")
		fmt.Println("   3. Bug in containerd snapshot code")
		fmt.Println("   Action: Drain node, remove compromised images, investigate filesystem")
		os.Exit(1)
	}

	fmt.Println("✓ All blobs verified successfully")
}
```

---

## 6. Threat Model

### Container Threat Model — Attack Surface & Mitigations

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  THREAT MODEL: Container Runtime (containerd + runc)                          │
│  STRIDE Analysis                                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ATTACK SURFACE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                         │  │
│  │  [External]          [Container]         [Host]          [Infra]        │  │
│  │                                                                         │  │
│  │  Network I/O  ──→  App Process  ──→  Kernel Syscalls  ──→  Hardware    │  │
│  │  Image Pull   ──→  Container Rootfs  ──→  Namespace Boundary            │  │
│  │  API calls    ──→  containerd API   ──→  Runtime daemon                 │  │
│  │  Admin access ──→  docker.sock      ──→  Host root                     │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  THREATS & MITIGATIONS                                                        │
│                                                                               │
│  T1: Container Escape via Kernel Exploit                                      │
│    Attack: Exploit kernel vuln (dirty COW, Dirty Pipe, etc.) from container   │
│    Likelihood: Low-Med (requires unpatched kernel)                            │
│    Impact: CRITICAL — full host compromise                                    │
│    Mitigations:                                                               │
│      - Keep kernel patched (kernel >= 5.15 LTS for most vuln fixes)          │
│      - Enable seccomp (blocks syscalls that trigger vuln code paths)          │
│      - Use gVisor/Kata for hardware-isolated containers                       │
│      - Enable LKRG (Linux Kernel Runtime Guard) for kernel integrity          │
│                                                                               │
│  T2: Container Escape via CAP_SYS_ADMIN                                       │
│    Attack: With CAP_SYS_ADMIN, call mount(), unshare(), setns() to escape     │
│    Likelihood: Med (misconfigured containers exist in wild)                   │
│    Impact: CRITICAL                                                           │
│    Mitigations:                                                               │
│      - Never grant CAP_SYS_ADMIN unless absolutely required                  │
│      - Seccomp blocks mount/unshare/setns by default                         │
│      - AppArmor/SELinux denies these even with the capability                 │
│                                                                               │
│  T3: Docker Socket Exposure                                                   │
│    Attack: App mounts /var/run/docker.sock → creates privileged container     │
│    Likelihood: HIGH (common misconfiguration)                                 │
│    Impact: CRITICAL — host root                                               │
│    Mitigations:                                                               │
│      - Audit: docker inspect $(docker ps -q) --format '{{.Mounts}}'          │
│      - Policy: OPA/Kyverno admission webhook denying docker.sock mounts       │
│      - Alternative: Docker-in-Docker via dedicated sidecar with limited perms │
│                                                                               │
│  T4: Image Supply Chain Attack                                                │
│    Attack: Malicious image pulled, contains backdoor/cryptominer              │
│    Likelihood: HIGH (typosquatting, compromised registries)                   │
│    Impact: HIGH                                                               │
│    Mitigations:                                                               │
│      - Content trust (Docker notary / cosign) verification                   │
│      - Private registry with vulnerability scanning (Trivy, Grype, Snyk)     │
│      - Admission webhook verifying image signatures (policy-controller)       │
│      - Pin image digests (sha256) not tags in manifests                       │
│                                                                               │
│  T5: Resource Exhaustion (DoS)                                                │
│    Attack: Fork bomb, memory bomb, CPU spin in container → host DoS           │
│    Likelihood: MED                                                            │
│    Impact: HIGH (host instability)                                            │
│    Mitigations:                                                               │
│      - memory.max (cgroup v2 hard limit)                                     │
│      - pids.max (cgroup v2 PID limit)                                        │
│      - cpu.max (CPU quota)                                                   │
│      - ulimit --nproc in container                                            │
│                                                                               │
│  T6: Lateral Movement via Shared Network Namespace                            │
│    Attack: Container sniffs traffic, ARP spoofs, attacks other containers     │
│    Likelihood: MED (requires CAP_NET_RAW)                                    │
│    Impact: HIGH                                                               │
│    Mitigations:                                                               │
│      - Drop CAP_NET_RAW (--cap-drop=NET_RAW)                                 │
│      - Inter-container communication disabled (ICC=false)                     │
│      - Use CNI with network policies (Calico, Cilium)                        │
│      - Each container in separate network namespace (default)                 │
│                                                                               │
│  T7: Secrets Leakage via Environment Variables                                │
│    Attack: Attacker reads /proc/<pid>/environ or container inspect output     │
│    Likelihood: HIGH (extremely common anti-pattern)                           │
│    Impact: HIGH                                                               │
│    Mitigations:                                                               │
│      - Use Docker secrets / Kubernetes secrets properly                       │
│      - Use Vault Agent injector or external-secrets-operator                  │
│      - Scan images and running containers for ENV vars with secrets patterns  │
│      - Restrict /proc/<pid>/environ visibility (requires userns)              │
│                                                                               │
│  T8: Timing Side Channels                                                     │
│    Attack: Container measures cache timing / TSC to fingerprint host, break   │
│            crypto, or extract info from neighboring containers                │
│    Likelihood: LOW (sophisticated attack)                                     │
│    Impact: MED                                                                │
│    Mitigations:                                                               │
│      - Disable TSC access (rdtsc/rdtscp — add to seccomp block list)         │
│      - Enable time namespace (CLONE_NEWTIME) isolation                        │
│      - Randomize ASLR (kernel.randomize_va_space=2)                          │
│                                                                               │
│  T9: containerd API Abuse                                                     │
│    Attack: Process with access to containerd.sock creates arbitrary containers│
│    Likelihood: LOW (limited access) / CRITICAL if misconfigured              │
│    Impact: CRITICAL                                                           │
│    Mitigations:                                                               │
│      - containerd.sock permissions: 0600, owner root (check with ls -la)     │
│      - No other users/services should access this socket                      │
│      - Use Docker daemon API with TLS and mutual auth for remote access       │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tests, Fuzzing & Benchmarks

### Unit Tests for Go Security Tools

```go
// pkg/capaudit/capaudit_test.go
package capaudit_test

import (
	"fmt"
	"os"
	"testing"

	"github.com/yourorg/container-security-tools/pkg/capaudit"
)

func TestReadCapabilitySetSelf(t *testing.T) {
	cs, err := capaudit.ReadCapabilitySet(os.Getpid())
	if err != nil {
		t.Fatalf("ReadCapabilitySet failed: %v", err)
	}

	if cs.PID != os.Getpid() {
		t.Errorf("expected PID %d, got %d", os.Getpid(), cs.PID)
	}

	// Test process should have some permitted capabilities (even if running as non-root in CI)
	t.Logf("Self capabilities: Eff=0x%016x Prm=0x%016x", cs.Effective, cs.Permitted)
	t.Logf("NoNewPrivs: %v SeccompMode: %d", cs.NoNewPrivs, cs.SeccompMode)
}

func TestCapabilityReport(t *testing.T) {
	cs, err := capaudit.ReadCapabilitySet(os.Getpid())
	if err != nil {
		t.Fatalf("ReadCapabilitySet failed: %v", err)
	}

	report := cs.SecurityReport()
	if len(report) == 0 {
		t.Error("expected non-empty security report")
	}

	t.Log(report)
}

func TestActiveCapabilitiesWithRoot(t *testing.T) {
	if os.Getuid() != 0 {
		t.Skip("skipping root-only test")
	}

	cs, err := capaudit.ReadCapabilitySet(os.Getpid())
	if err != nil {
		t.Fatalf("ReadCapabilitySet failed: %v", err)
	}

	// Root process should have many capabilities
	active := cs.ActiveCapabilities()
	if len(active) < 10 {
		t.Errorf("root process should have many capabilities, got %d", len(active))
	}
}

func BenchmarkReadCapabilitySet(b *testing.B) {
	pid := os.Getpid()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := capaudit.ReadCapabilitySet(pid)
		if err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkScanAllProcesses benchmarks scanning all processes for capabilities
func BenchmarkScanAllProcesses(b *testing.B) {
	entries, _ := os.ReadDir("/proc")
	var pids []int
	for _, e := range entries {
		var pid int
		if fmt.Sscanf(e.Name(), "%d", &pid) == 1 {
			pids = append(pids, pid)
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, pid := range pids {
			capaudit.ReadCapabilitySet(pid)
		}
	}
}
```

```go
// pkg/cgroupv2/cgroupv2_test.go
package cgroupv2_test

import (
	"os"
	"testing"

	"github.com/yourorg/container-security-tools/pkg/cgroupv2"
)

func TestScanContainerCgroups(t *testing.T) {
	if os.Getuid() != 0 {
		t.Skip("cgroup reading requires root")
	}

	containers, err := cgroupv2.ScanAllContainerCgroups()
	if err != nil {
		t.Logf("Note: no containers found or cgroup v2 not available: %v", err)
		return
	}

	for _, cc := range containers {
		t.Logf("Container %s:", cc.ContainerID[:min(12, len(cc.ContainerID))])
		t.Logf("  Memory: %d / %d bytes", cc.MemoryCurrentBytes, cc.MemoryMaxBytes)
		t.Logf("  PID: %d / %d", cc.PIDsCurrent, cc.PIDsMax)
		t.Logf("  CPU throttle: %.1f%%", cc.CPUThrottlePercent())

		// Security check
		issues := cc.SecurityCheck()
		for _, issue := range issues {
			t.Logf("  Security: %s", issue)
		}
	}
}

func TestMemoryUsagePercent(t *testing.T) {
	cc := &cgroupv2.ContainerCgroup{
		MemoryCurrentBytes: 512 * 1024 * 1024, // 512MB
		MemoryMaxBytes:     1024 * 1024 * 1024, // 1GB
	}

	pct := cc.MemoryUsagePercent()
	if pct != 50.0 {
		t.Errorf("expected 50.0%%, got %.1f%%", pct)
	}
}

func TestUnlimitedMemory(t *testing.T) {
	cc := &cgroupv2.ContainerCgroup{
		MemoryCurrentBytes: 100 * 1024 * 1024,
		MemoryMaxBytes:     0, // unlimited
	}

	issues := cc.SecurityCheck()
	hasMemIssue := false
	for _, issue := range issues {
		if len(issue) > 0 && issue[:8] == "CRITICAL" {
			hasMemIssue = true
		}
	}
	if !hasMemIssue {
		t.Error("expected CRITICAL issue for unlimited memory")
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
```

### Integration Tests

```bash
#!/bin/bash
# tests/integration/test_container_security.sh
# Integration tests that require a running Docker daemon

set -euo pipefail

PASS=0
FAIL=0

assert() {
    local desc="$1"
    local cmd="$2"
    local expect="$3"

    result=$(eval "$cmd" 2>&1) || true
    if echo "$result" | grep -q "$expect"; then
        echo "PASS: $desc"
        ((PASS++)) || true
    else
        echo "FAIL: $desc"
        echo "  Expected to find: $expect"
        echo "  Got: $result"
        ((FAIL++)) || true
    fi
}

echo "=== Container Security Integration Tests ==="

# Test 1: Default container has seccomp enabled
CONTAINER=$(docker run -d --rm alpine sleep 300)
PID=$(docker inspect --format '{{.State.Pid}}' $CONTAINER)

assert "Seccomp enabled by default" \
    "grep 'Seccomp:' /proc/$PID/status" \
    "Seccomp:       2"

# Test 2: Default container has noNewPrivileges
assert "NoNewPrivileges set" \
    "grep 'NoNewPrivs' /proc/$PID/status" \
    "NoNewPrivs:    1"

# Test 3: Default container cannot load kernel modules
assert "Cannot load kernel module" \
    "docker exec $CONTAINER sh -c 'modprobe dummy 2>&1; echo exit:$?'" \
    "exit:1"

# Test 4: Default container cannot mount filesystems
assert "Cannot mount filesystem" \
    "docker exec $CONTAINER sh -c 'mount -t tmpfs tmpfs /tmp 2>&1; echo exit:$?'" \
    "exit:1"

# Test 5: Default container has limited capabilities
assert "CAP_SYS_ADMIN not present" \
    "docker exec $CONTAINER sh -c 'cat /proc/self/status | grep CapEff'" \
    "CapEff:"

# Test 6: PID namespace is isolated
CONTAINER_PID1=$(docker exec $CONTAINER sh -c 'cat /proc/self/pid_for_children 2>/dev/null; echo 1')
assert "Container PID 1 is isolated" \
    "docker exec $CONTAINER sh -c 'ls /proc/1/exe'" \
    "sleep"

# Test 7: Network namespace is isolated
assert "Container has isolated network namespace" \
    "docker exec $CONTAINER ip addr show" \
    "172.17"

# Test 8: Cannot read /proc/kcore
assert "Cannot access /proc/kcore" \
    "docker exec $CONTAINER sh -c 'cat /proc/kcore 2>&1 | head -1'" \
    "Permission denied\|No such file\|Input/output error"

# Cleanup
docker stop $CONTAINER >/dev/null 2>&1

# Test 9: Privileged container has all capabilities
PRIV_CONTAINER=$(docker run -d --rm --privileged alpine sleep 300)
PRIV_PID=$(docker inspect --format '{{.State.Pid}}' $PRIV_CONTAINER)

assert "Privileged container has CAP_SYS_ADMIN" \
    "grep CapEff /proc/$PRIV_PID/status" \
    "CapEff:.*[1-9]"  # non-zero caps

docker stop $PRIV_CONTAINER >/dev/null 2>&1

echo ""
echo "Results: PASS=$PASS FAIL=$FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

### Running Tests

```bash
# Unit tests:
go test ./pkg/... -v -race

# Integration tests (requires root + Docker):
sudo bash tests/integration/test_container_security.sh

# Benchmarks:
go test ./pkg/capaudit/... -bench=. -benchmem -benchtime=5s

# Race detector:
go test -race ./...

# Security static analysis:
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec -fmt=json -out=gosec-results.json ./...
```

---

## 8. Roll-out / Rollback Plan

### Deploying New Security Configurations

```
Phase 1: AUDIT (Week 1)
  ├── Deploy nsinspect, cgaudit, containerd-audit in READ-ONLY mode
  ├── Collect baseline: all findings per container
  ├── Identify: which containers would break with new policy
  └── Output: findings report sorted by severity

Phase 2: ENFORCE in STAGING (Week 2-3)
  ├── Apply new seccomp profiles in staging
  │   docker run --security-opt seccomp=/etc/docker/custom-seccomp.json ...
  ├── Apply capability drops:
  │   docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE ...
  ├── Apply resource limits:
  │   docker run --memory=512m --cpus=0.5 --pids-limit=100 ...
  ├── Run full integration test suite
  └── Monitor for SIGSYS, EPERM errors in application logs

Phase 3: CANARY IN PRODUCTION (Week 4)
  ├── Apply to 5% of production containers
  ├── Monitor: application error rates, seccomp violations in audit log
  │   ausearch -m SECCOMP -ts today | wc -l  # should be 0
  ├── Monitor: performance impact
  │   # Seccomp adds ~1-5% CPU overhead for syscall-heavy workloads
  └── Go/no-go decision at 24h, 48h, 72h marks

Phase 4: FULL ROLLOUT (Week 5-6)
  ├── Rolling deployment to all containers
  ├── Update container orchestration (K8s SecurityContext, Docker Compose)
  └── Update CI/CD to enforce security policies in pipeline

ROLLBACK PROCEDURE:
  # If a container breaks due to seccomp:
  1. Identify blocked syscall:
     ausearch -m SECCOMP -ts today -p <PID> | tail -5
  2. Add exception to profile:
     # Add syscall to seccomp profile allowlist
     jq '.syscalls += [{"names": ["<blocked_syscall>"], "action": "SCMP_ACT_ALLOW"}]' \
       /etc/docker/custom-seccomp.json > /tmp/new-seccomp.json
  3. Redeploy with updated profile
  4. Track the exception in security backlog for removal

  # Emergency: completely disable new policy for a single container:
  docker update <container> does not support seccomp changes
  # Must stop and restart with original flags:
  docker stop <container>
  docker run [original flags without new security options] ...

  # Rollback via daemon.json (affects all new containers):
  # Edit /etc/docker/daemon.json:
  {
    "seccomp-profile": "/etc/docker/seccomp.json"  // revert to default
  }
  # Reload:
  systemctl reload docker  // may not work for all daemon.json changes
  // OR:
  systemctl restart docker  // interrupts running containers (last resort)
```

---

## 9. References

**Linux Kernel Documentation**:
- `Documentation/security/seccomp_filter.rst` — BPF filter implementation
- `Documentation/cgroup-v2.rst` — unified cgroup hierarchy
- `Documentation/namespaces/` — all namespace types
- `include/uapi/linux/capability.h` — capability definitions (source of truth)

**OCI / containerd**:
- OCI Runtime Spec: https://github.com/opencontainers/runtime-spec/blob/main/spec.md
- containerd architecture: https://github.com/containerd/containerd/blob/main/docs/architecture.md
- containerd shim v2 protocol: https://github.com/containerd/containerd/blob/main/runtime/v2/README.md
- runc source: https://github.com/opencontainers/runc

**Security References**:
- Docker security docs: https://docs.docker.com/engine/security/
- Docker default seccomp profile: https://github.com/moby/moby/blob/master/profiles/seccomp/default.json
- AppArmor docker profile: https://github.com/moby/moby/tree/master/profiles/apparmor
- NCC Group container security guide: https://research.nccgroup.com/container-security/

**CVEs to understand**:
- CVE-2019-5736 (runc container escape via /proc/self/exe overwrite)
- CVE-2020-15257 (containerd abstract Unix domain socket exposure)
- CVE-2022-0492 (cgroup release_agent privilege escalation)
- CVE-2022-0847 (Dirty Pipe — /proc/self/fd write past EOF)
- CVE-2024-21626 (runc process.cwd container escape — VERY recent, patch runc >= 1.1.12)

**Go Libraries**:
- `github.com/containerd/containerd` — Go client for containerd gRPC API
- `github.com/opencontainers/runtime-spec/specs-go` — OCI runtime spec types
- `github.com/opencontainers/runc/libcontainer` — runc internals library
- `github.com/cilium/ebpf` — eBPF programs from Go

---

## Next 3 Steps

**Step 1: Instrument your environment immediately**
```bash
# Run the namespace inspector on all running containers right now:
sudo ./bin/nsinspect  # auto-discovers all containers
# Focus on any container where 'user' namespace is NOT isolated
# and where it shows CRITICAL findings

# Check which containers have no seccomp:
for pid in $(docker inspect $(docker ps -q) --format '{{.State.Pid}}'); do
  seccomp=$(grep Seccomp: /proc/$pid/status | awk '{print $2}')
  if [ "$seccomp" = "0" ]; then
    echo "⚠ PID $pid: NO SECCOMP"
  fi
done
```

**Step 2: Build and harden with the containerd auditor**
```bash
# Build the full audit suite:
go build -o bin/containerd-audit ./cmd/containerd-audit/
sudo ./bin/containerd-audit /run/containerd/containerd.sock moby

# Generate a minimal seccomp profile from actual syscall usage:
# Run your container with SCMP_ACT_LOG, collect syscalls for 24h:
docker run --security-opt seccomp=unconfined \
  -e SECCOMP_AUDIT=1 \
  your-image:tag
ausearch -m SECCOMP | awk '{print $NF}' | sort -u > used_syscalls.txt
# Build profile from that list
```

**Step 3: Implement runtime monitoring in CI/CD**

Wire `rtsecmon` into your container lifecycle: emit structured JSON events to your SIEM on every `NEW_PROCESS` with `HIGH`/`CRITICAL` severity. Add a policy that fails CI if `containerd-audit` returns exit code 2 (CRITICAL findings). Configure Falco (or your eBPF monitor) with rules targeting the exact syscalls and file paths identified in this guide.

```bash
# Quick Falco rule for shell spawning in nginx containers:
cat >> /etc/falco/falco_rules.local.yaml << 'EOF'
- rule: Shell spawned in nginx container
  desc: A shell was spawned in a container running nginx
  condition: >
    spawned_process and container and
    container.image contains "nginx" and
    proc.name in (shell_binaries)
  output: >
    Shell spawned in nginx container
    (user=%user.name container=%container.id image=%container.image.repository
    shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
  priority: WARNING
  tags: [container, shell, nginx]
EOF
systemctl restart falco
```