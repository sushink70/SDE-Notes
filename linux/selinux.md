# SELinux: A Comprehensive Deep-Dive Guide

> **Scope:** Architecture, kernel internals, policy language, MLS/MCS, module authoring, enforcement mechanics, and programmatic interaction via C and Rust.

---

## Table of Contents

1. [Foundational Philosophy — Why SELinux Exists](#1-foundational-philosophy)
2. [Architectural Overview — The Whole Stack](#2-architectural-overview)
3. [Linux Security Module (LSM) Framework](#3-linux-security-module-lsm-framework)
4. [Security Contexts — The Identity System](#4-security-contexts)
5. [The Policy Language — Type Enforcement (TE)](#5-the-policy-language--type-enforcement)
6. [Role-Based Access Control (RBAC)](#6-role-based-access-control-rbac)
7. [Multi-Level Security (MLS) and Multi-Category Security (MCS)](#7-multi-level-security-mls-and-multi-category-security-mcs)
8. [The Access Vector Cache (AVC)](#8-the-access-vector-cache-avc)
9. [Object Classes and Permissions — The Complete Taxonomy](#9-object-classes-and-permissions)
10. [Policy Module Architecture — .te, .fc, .if Files](#10-policy-module-architecture)
11. [M4 Macro System and Interface Layers](#11-m4-macro-system-and-interface-layers)
12. [Writing Complex, Real-World Policies](#12-writing-complex-real-world-policies)
13. [Booleans — Runtime Policy Tuning](#13-booleans--runtime-policy-tuning)
14. [File, Port, and Network Context Management](#14-file-port-and-network-context-management)
15. [Constraint System and Validatetrans](#15-constraint-system-and-validatetrans)
16. [Policy Compilation and Binary Format](#16-policy-compilation-and-binary-format)
17. [Audit Subsystem and AVC Denial Analysis](#17-audit-subsystem-and-avc-denial-analysis)
18. [C Programming Interface — libselinux](#18-c-programming-interface--libselinux)
19. [Rust Programming Interface](#19-rust-programming-interface)
20. [Kernel Internals — Deep Implementation](#20-kernel-internals--deep-implementation)
21. [Network Controls — Netfilter Integration](#21-network-controls--netfilter-integration)
22. [SELinux in Containers — cgroups and Namespaces](#22-selinux-in-containers)
23. [Troubleshooting Methodology](#23-troubleshooting-methodology)
24. [Performance Characteristics and Tuning](#24-performance-characteristics-and-tuning)
25. [Reference — Complete Permission Tables](#25-reference--complete-permission-tables)

---

## 1. Foundational Philosophy

### The Fundamental Problem: DAC is Not Enough

Traditional UNIX uses **Discretionary Access Control (DAC)**. The key word is *discretionary* — the owner of a resource *decides* who can access it. This has three critical flaws in high-security environments:

```
DAC Model:
  Process runs as user "alice" (uid=1000)
  File owned by "alice" → process can do ANYTHING to it
  If process is compromised → attacker inherits alice's full permissions
  Privilege escalation: compromised httpd runs as root → game over
```

**DAC trust assumptions:**
- A process running as a user is trusted to that user's full extent
- The root user is unconditionally omnipotent
- No concept of "this program should only touch these files, not all of alice's files"

### Mandatory Access Control (MAC)

SELinux implements **Mandatory Access Control** — the *system* enforces access policy, not the resource owner. Even root cannot override MAC policy (without a policy rule explicitly allowing it).

```
MAC Model:
  httpd process → labeled "httpd_t"
  /var/www/html  → labeled "httpd_sys_content_t"
  Policy: allow httpd_t httpd_sys_content_t:file { read getattr open }
  
  Even if httpd runs as root:
    httpd cannot write to /etc/shadow (shadow_t) — no policy rule exists
    httpd cannot exec /bin/bash — no policy rule exists
    Compromise of httpd = isolated blast radius
```

### The Principle of Least Privilege at System Level

SELinux operationalizes PoLP at the kernel level. Every subject (process) has a precisely defined set of objects (files, sockets, capabilities) it may interact with, and the exact operations it may perform. Anything not explicitly allowed is **denied by default**.

This is the **default-deny** model — the inverse of DAC's default-allow.

---

## 2. Architectural Overview — The Whole Stack

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER SPACE                                │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │  Processes   │  │  semanage /    │  │  audit2allow /     │  │
│  │  (subjects)  │  │  semodule /    │  │  audit2why /       │  │
│  │              │  │  restorecon /  │  │  sealert           │  │
│  │              │  │  chcon         │  │                    │  │
│  └──────┬───────┘  └───────┬────────┘  └──────────┬─────────┘  │
│         │                  │                       │            │
│  ┌──────▼───────────────────▼───────────────────────▼─────────┐ │
│  │                    libselinux / libsepol                    │ │
│  │         (userspace policy management & labeling)            │ │
│  └──────────────────────────────┬──────────────────────────────┘ │
│                                  │ /sys/fs/selinux (selinuxfs)  │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                         KERNEL SPACE                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   System Call Interface                    │  │
│  └───────────────────────────────┬───────────────────────────┘  │
│                                  │                               │
│  ┌───────────────────────────────▼───────────────────────────┐  │
│  │              Linux Security Module (LSM) Hooks             │  │
│  │  security_inode_permission(), security_file_open(),        │  │
│  │  security_socket_connect(), security_task_kill(), ...      │  │
│  └───────────────────────────────┬───────────────────────────┘  │
│                                  │                               │
│  ┌───────────────────────────────▼───────────────────────────┐  │
│  │                     SELinux Core Engine                    │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │  Security    │  │  Access      │  │   Policy        │ │  │
│  │  │  Server      │  │  Vector      │  │   Database      │ │  │
│  │  │  (SS)        │  │  Cache (AVC) │  │   (in-kernel)   │ │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │  │
│  │         │                  │                    │          │  │
│  │         └──────────────────┴────────────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Filesystem    │  │   Network Stack  │  │   IPC / Sockets │ │
│  │   (xattrs for   │  │   (sk_security)  │  │   (msg queues,  │ │
│  │    labels)      │  │                  │  │    semaphores)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Role |
|-----------|----------|------|
| **Security Server (SS)** | `security/selinux/ss/` | Policy decisions, context computation |
| **AVC** | `security/selinux/avc.c` | Decision caching for performance |
| **LSM Hooks** | `security/selinux/hooks.c` | ~400 intercept points in kernel |
| **selinuxfs** | `/sys/fs/selinux` | Kernel↔userspace communication |
| **libselinux** | userspace | API for context manipulation |
| **libsepol** | userspace | Policy parsing/compilation |
| **checkpolicy** | userspace | Policy compiler |
| **semodule** | userspace | Module management |

---

## 3. Linux Security Module (LSM) Framework

### LSM as a Hook Architecture

LSM is a **stackable hook framework** in the kernel. It defines hundreds of security hook points — locations in the kernel where security modules can intercept operations and make allow/deny decisions.

```c
// Simplified kernel flow for open(2) syscall
// From: fs/namei.c → security/selinux/hooks.c

// When a process calls open("/etc/passwd", O_RDONLY):
int do_open(const char *path, int flags) {
    struct inode *inode = lookup_inode(path);
    
    // 1. DAC check (traditional UNIX permissions)
    error = inode_permission(inode, MAY_READ);
    if (error) return error;
    
    // 2. LSM hook fires — SELinux intercepts here
    error = security_inode_permission(inode, MAY_READ);
    // ↑ This calls selinux_inode_permission() in hooks.c
    if (error) return error;  // SELinux denied → -EACCES
    
    return actually_open_file(inode, flags);
}
```

### LSM Hook Registration

```c
// security/selinux/hooks.c (simplified)
static struct security_hook_list selinux_hooks[] __lsm_ro_after_init = {
    LSM_HOOK_INIT(binder_set_context_mgr, selinux_binder_set_context_mgr),
    LSM_HOOK_INIT(ptrace_access_check,    selinux_ptrace_access_check),
    LSM_HOOK_INIT(ptrace_traceme,         selinux_ptrace_traceme),
    LSM_HOOK_INIT(capget,                 selinux_capget),
    LSM_HOOK_INIT(capset,                 selinux_capset),
    LSM_HOOK_INIT(capable,                selinux_capable),
    LSM_HOOK_INIT(quotactl,               selinux_quotactl),
    LSM_HOOK_INIT(quota_on,               selinux_quota_on),
    LSM_HOOK_INIT(syslog,                 selinux_syslog),
    LSM_HOOK_INIT(vm_enough_memory,       selinux_vm_enough_memory),
    // ... approximately 400 more hooks
    LSM_HOOK_INIT(inode_permission,       selinux_inode_permission),
    LSM_HOOK_INIT(file_open,              selinux_file_open),
    LSM_HOOK_INIT(socket_connect,         selinux_socket_connect),
    LSM_HOOK_INIT(task_kill,              selinux_task_kill),
};

static __init int selinux_init(void) {
    security_add_hooks(selinux_hooks, 
                       ARRAY_SIZE(selinux_hooks), 
                       "selinux");
    return 0;
}
```

### The Permission Check Flow

```c
// Simplified selinux_inode_permission() implementation concept
static int selinux_inode_permission(struct inode *inode, int mask) {
    // Get the security context of the calling process
    u32 sid = current_sid();           // Subject SID (process context)
    
    // Get the security context of the inode (file/dir)
    u32 isid = inode->i_security->sid; // Object SID (file context)
    
    // Determine what class and permissions are needed
    u16 sclass = inode_mode_to_security_class(inode->i_mode);
    // → FILE__READ, FILE__WRITE, DIR__SEARCH, etc.
    
    u32 perms = file_mask_to_av(inode->i_mode, mask);
    // → { read } or { write } or { read write }
    
    // Query the AVC (Access Vector Cache)
    return avc_has_perm(sid, isid, sclass, perms, &ad);
    // Returns 0 (allowed) or -EACCES (denied)
}
```

---

## 4. Security Contexts

### Structure of a Security Context

A security context (also called a *label*) is a colon-delimited string that uniquely identifies a security identity:

```
user_u:role_r:type_t:s0:c0,c512
│       │      │      │  └── MCS/MLS categories
│       │      │      └───── MLS sensitivity level
│       │      └──────────── Type (primary enforcement domain)
│       └─────────────────── Role
└─────────────────────────── SELinux user
```

**Real-world examples:**

```bash
# A running web server process
system_u:system_r:httpd_t:s0

# An HTML file being served
system_u:object_r:httpd_sys_content_t:s0

# An SSH daemon
system_u:system_r:sshd_t:s0

# A regular user's file
unconfined_u:object_r:user_home_t:s0

# A file in a Multi-Category Security container
system_u:object_r:svirt_sandbox_file_t:s0:c200,c384

# The kernel itself
system_u:system_r:kernel_t:s0
```

### The Four Fields

#### Field 1: SELinux User

SELinux users are **not** Linux users. They define the entry point into the RBAC system.

```
system_u     → System processes, daemons
unconfined_u → Unconfined (largely unrestricted) users
user_u       → Generic confined user
staff_u      → Staff who can use sudo
sysadm_u    → System administrators
root         → Root with SELinux constraints
```

SELinux users are persistent identity anchors — they don't change during a session (unlike Linux UIDs which can be changed with setuid).

#### Field 2: Role

Roles define which **types** a user is allowed to enter (transition into). This is the RBAC layer:

```
system_r     → System/daemon roles (associated with system_u)
unconfined_r → Unconfined role
user_r       → Standard user role
staff_r      → Staff role (can run sudo, transition to sysadm_r)
sysadm_r    → Full system administration
object_r     → Default role for files/objects (non-process contexts)
```

The constraint: a user can only use roles assigned to them in policy.

#### Field 3: Type

The **type** is the primary enforcement domain. Nearly all policy rules are written in terms of types. Types serve dual purpose:
- On processes: called a **domain** (e.g., `httpd_t`)
- On objects (files, sockets, etc.): called a **type** (e.g., `httpd_sys_content_t`)

#### Field 4: MLS/MCS Range

```
s0           → Sensitivity level 0 (lowest), no categories
s0-s15       → Range from s0 to s15 (for processes that span levels)
s0:c0,c512   → Sensitivity 0, categories 0 and 512
s3:c0.c1023  → Level 3, all categories 0 through 1023
```

### How Labels Are Stored

**Files:** Labels stored as extended attributes on the filesystem.

```bash
# View raw xattr
getfattr -n security.selinux /etc/passwd
# → security.selinux="system_u:object_r:passwd_file_t:s0"

# The kernel reads this xattr via:
# security/selinux/hooks.c → selinux_inode_init_security()
```

**Processes:** Labels stored in the process's `task_struct` via a `security` pointer.

```c
// In kernel: include/linux/sched.h
struct task_struct {
    // ...
    void *security;  // → struct task_security_struct
    // ...
};

// security/selinux/include/objsec.h
struct task_security_struct {
    u32 osid;   // SID before exec (original)
    u32 sid;    // current SID
    u32 exec_sid; // SID for next exec
    u32 create_sid; // SID for socket/file creation
    u32 keycreate_sid;
    u32 sockcreate_sid;
};
```

**Network:** Labels stored in socket security structure and can be transmitted via CIPSO/CALIPSO packet options.

---

## 5. The Policy Language — Type Enforcement

### Type Enforcement File (.te) Basics

The `.te` file is the heart of any SELinux policy module. It uses a specialized policy language compiled by `checkpolicy`.

#### Declarations

```te
#============================================================
# TYPE DECLARATIONS
#============================================================

# Declare a new type (domain for a process)
type myapp_t;

# Declare a type and immediately assign it to a domain attribute
type myapp_t, domain;

# Declare a type that is a file type
type myapp_exec_t;

# Declare a type with multiple attributes
type myapp_log_t, file_type, logfile;

# Declare a type attribute (used to group types)
attribute web_domain;
attribute network_peer_type;

# Assign an existing type to an attribute
typeattribute httpd_t web_domain;
```

#### Type Aliases

```te
# Type aliases allow referring to a type by another name
# Useful for policy compatibility across distros
typealias httpd_t alias { apache_t lighttpd_t };
```

#### Allow Rules — The Core Rule Type

```
allow <source_type> <target_type>:<class> { <permissions> };
```

```te
# Allow myapp_t to read files labeled myapp_conf_t
allow myapp_t myapp_conf_t:file { read open getattr };

# Allow myapp_t to search directories labeled myapp_conf_t
allow myapp_t myapp_conf_t:dir { search getattr open read };

# Allow myapp_t to use TCP sockets
allow myapp_t self:tcp_socket { create connect read write };

# Multiple source types (using attribute)
allow web_domain httpd_sys_content_t:file { read getattr open };

# Allow myapp_t to create a specific file type
allow myapp_t myapp_log_t:file { create write open append getattr };

# Allow using a capability (Linux capability, not file permission)
allow myapp_t self:capability { net_bind_service chown };

# Allow sending signals
allow myapp_t myapp_t:process { sigchld };
allow myapp_t self:process { fork };
```

#### Type Transitions — Domain Transitions

A **type transition** defines what label a new process or file gets when created:

```te
#------------------------------------------------------------
# DOMAIN TRANSITION: When httpd_t executes myapp_exec_t,
# the new process runs as myapp_t
#------------------------------------------------------------

# Step 1: Allow the transition to happen
type_transition httpd_t myapp_exec_t:process myapp_t;

# Step 2: Allow httpd_t to execute the binary
allow httpd_t myapp_exec_t:file { execute };

# Step 3: Allow the transition itself
allow httpd_t myapp_t:process { transition };

# Step 4: Allow myapp_t to use the entrypoint
allow myapp_t myapp_exec_t:file { entrypoint };

# Combined shorthand using a macro (from refpolicy)
# This macro expands to the 4 rules above:
# domtrans_pattern(httpd_t, myapp_exec_t, myapp_t)
```

#### File Type Transitions

When a process creates a file, what label does it get?

```te
# When myapp_t creates a file in a directory labeled myapp_log_dir_t,
# that file gets labeled myapp_log_t
type_transition myapp_t myapp_log_dir_t:file myapp_log_t;

# Specific filename transitions (policy version ≥ 25)
type_transition myapp_t myapp_run_dir_t:file myapp_pid_t "myapp.pid";
```

#### Deny, Dontaudit, Auditallow

```te
# neverallow: A compile-time assertion that no allow rule matches this.
# If any policy module would allow it, compilation fails.
# Used to enforce hard security invariants.
neverallow ~httpd_t httpd_config_t:file write;
# Means: "Compile error if anything other than httpd_t can write httpd_config_t"

# dontaudit: The action is STILL DENIED, but no audit log is generated.
# Use for known-benign denials that flood logs.
dontaudit myapp_t proc_t:file { read };

# auditallow: The action is ALLOWED (there must be an allow rule),
# but it is also logged for audit purposes.
auditallow myapp_t shadow_t:file { read };
```

#### Role Allow Rules

```te
# Allow role staff_r to transition to role sysadm_r
allow staff_r sysadm_r;

# Roles a type can be associated with
role system_r types myapp_t;
role user_r types myapp_user_t;
```

#### Range Transitions (MLS)

```te
# When init_t creates a process running httpd_exec_t,
# it runs at sensitivity level s0
range_transition init_t httpd_exec_t:process s0;

# A daemon that runs at a higher sensitivity
range_transition init_t classified_daemon_exec_t:process s3-s3:c0.c1023;
```

---

## 6. Role-Based Access Control (RBAC)

### How RBAC Layers onto TE

RBAC adds a constraint layer on top of Type Enforcement. The relationship is:

```
SELinux User → can use → Roles
Roles → can access → Types (Domains)
Types → define → what operations are allowed
```

### User-Role-Type Triplets

```te
# Define that SELinux user staff_u can use roles staff_r and sysadm_r
user staff_u roles { staff_r sysadm_r } level s0 range s0-s0:c0.c1023;

# staff_r role can access these domain types
role staff_r types { staff_t sudo_t };

# sysadm_r role can access these domain types  
role sysadm_r types { sysadm_t staff_t };
```

### Role Transitions

```te
# When staff_t runs sudo, it can transition to sysadm_t under sysadm_r
role_transition staff_r sudo_exec_t sysadm_r;

# The allow rule still needs to exist:
allow staff_r sysadm_r;
```

### Practical RBAC Example

```te
#============================================================
# staff_u can SSH in and run basic commands (staff_r:staff_t)
# After `sudo -i`, they enter sysadm_r:sysadm_t
# Cannot directly access kernel internals without the role
#============================================================

# staff_t can execute sudo
allow staff_t sudo_exec_t:file { execute read open getattr };
allow staff_t sudo_t:process transition;
type_transition staff_t sudo_exec_t:process sudo_t;

# sudo_t transitions to sysadm_t under sysadm_r
role_transition staff_r sudo_exec_t sysadm_r;
allow sudo_t sysadm_t:process transition;
type_transition sudo_t sysadm_exec_t:process sysadm_t;
```

---

## 7. Multi-Level Security (MLS) and Multi-Category Security (MCS)

### Bell-LaPadula Model

MLS implements the Bell-LaPadula confidentiality model:

```
Sensitivity Levels (ordered hierarchy):
  s0 = Unclassified
  s1 = Confidential  
  s2 = Secret
  s3 = Top Secret
  s4 = Top Secret / SCI

Bell-LaPadula Rules:
  "No Read Up":   A subject at level L cannot read objects at level > L
  "No Write Down": A subject at level L cannot write objects at level < L
  
  This prevents information from leaking from high to low classification.
```

### MCS (Multi-Category Security)

MCS is a simplified MLS variant used by default in RHEL/Fedora. It uses only `s0` sensitivity but adds **categories** (c0–c1023) for isolation:

```
Container 1: s0:c200,c384
Container 2: s0:c201,c385

These category sets are disjoint → containers cannot access each other's files
Even as the same user, even running as root in DAC terms.
```

This is how `podman` and `docker` on SELinux systems isolate containers.

### MLS Policy Rules

```te
#============================================================
# MLS CONSTRAINTS
# These are written in constraint language, not TE language
#============================================================

# Standard MLS constraint on file read:
# A process can only read a file if its level dominates the file's level
mlsconstrain file read (
    l1 dom l2           # process level (l1) must dominate file level (l2)
    or t1 == mlsfileread    # unless the process type has mlsfileread attr
    or t2 == mlstrustedobject  # or the object is trusted
);

# MLS constraint on file write:
mlsconstrain file write (
    l2 domby l1         # file level (l2) dominated by process level (l1)
    or t1 == mlsfilewrite
);

# MLS constraint on process transition:
mlsconstrain process transition (
    l1 eq l2            # level doesn't change during transition
    or t1 == mlsprocwrite  # unless type has explicit privilege
);
```

### MCS Category Generation for Containers

The container runtime generates unique category pairs for isolation:

```
Total categories: 1024 (c0-c1023)
Unique pairs: C(1024,2) = 523,776 possible combinations

A container gets a random pair, e.g., c200,c384
All files written by the container get that label
Another container with c201,c385 cannot access them
```

```te
# Policy that allows svirt (container) types to use any category pair
# as long as the container's label matches the file's label

# The MCS constraint enforces this automatically:
mlsconstrain file { read write } (
    l1 eq l2            # process and file must be at same MCS level
    or t1 == mcs_constrained_type  # or type is exempt
);
```

### MLS Trusted Types

Some types need cross-level access (e.g., audit daemons that read from all levels):

```te
# Give a type the ability to read any level
typeattribute auditd_t mlsfileread;
typeattribute auditd_t mlsnetread;

# Give a type the ability to write to lower levels (declassification)
typeattribute trusted_declassifier_t mlsfilewrite;
```

---

## 8. The Access Vector Cache (AVC)

### Why Caching is Critical

Every system call that involves a kernel object can trigger an SELinux permission check. Without caching, each check would require traversing the full policy database — catastrophically slow. The AVC eliminates this overhead.

### AVC Data Structure

```c
// Simplified from security/selinux/avc.c

#define AVC_CACHE_SLOTS 512   // Power of 2 for fast modulo
#define AVC_CACHE_MAXNODES 410

struct avc_node {
    struct avc_key {
        u32 ssid;   // Source SID (process)
        u32 tsid;   // Target SID (object)
        u16 tclass; // Object class (file, socket, etc.)
    } key;
    
    struct av_decision {
        u32 allowed;    // Bitmask of allowed permissions
        u32 decided;    // Bitmask of decided permissions
        u32 auditallow; // Bitmask of permissions to audit on allow
        u32 auditdeny;  // Bitmask of permissions to audit on deny
        u32 seqno;      // Policy sequence number
    } avd;
    
    struct rcu_head rhead;  // RCU for lock-free reads
    struct hlist_node list; // Hash table chaining
};

// Cache is a hash table of linked lists
static struct avc_cache {
    struct hlist_head slots[AVC_CACHE_SLOTS];
    spinlock_t slots_lock[AVC_CACHE_SLOTS];
    atomic_t lru_hint;
    atomic_t active_nodes;
    u32 latest_notif; // Latest policy notification sequence
} avc_cache;
```

### AVC Lookup Algorithm

```c
// Simplified avc_has_perm() flow
int avc_has_perm(u32 ssid, u32 tsid, u16 tclass, u32 requested,
                 struct common_audit_data *auditdata) {
    
    struct avc_node *node;
    struct av_decision avd;
    int rc;
    
    // Step 1: Hash lookup in AVC
    // Hash key = ssid ^ tsid ^ tclass
    u32 hvalue = avc_hash(ssid, tsid, tclass);
    
    rcu_read_lock();
    node = avc_lookup(ssid, tsid, tclass, hvalue);
    
    if (node) {
        // Cache HIT — fast path
        // Check requested permissions against allowed bitmask
        if ((node->avd.allowed & requested) == requested) {
            rcu_read_unlock();
            return 0;  // ALLOWED
        }
        avd = node->avd;  // Copy for audit
        rcu_read_unlock();
        // Fall through to audit/denial handling
    } else {
        // Cache MISS — slow path
        rcu_read_unlock();
        
        // Query the Security Server (policy database)
        rc = security_compute_av(ssid, tsid, tclass, requested, &avd);
        
        // Insert result into AVC
        avc_insert(ssid, tsid, tclass, &avd, hvalue);
    }
    
    // Check permission
    if ((avd.allowed & requested) != requested) {
        // Generate audit log if not dontaudit
        if (avd.auditdeny & requested)
            avc_audit(ssid, tsid, tclass, requested, &avd, auditdata);
        return -EACCES;  // DENIED
    }
    
    // Audit allowed access if auditallow
    if (avd.auditallow & requested)
        avc_audit(ssid, tsid, tclass, requested, &avd, auditdata);
    
    return 0;  // ALLOWED
}
```

### AVC Invalidation

When policy changes (new module loaded, boolean toggled), the AVC must be invalidated:

```c
// Called when policy is reloaded
void avc_ss_reset(u32 seqno) {
    // Increment sequence number
    // Mark all cache entries as stale
    // Entries are lazily evicted on next lookup
    avc_flush();
}
```

### AVC Statistics

```bash
# View AVC cache statistics
cat /sys/fs/selinux/avc/cache_stats
# lookups  hits  misses  allocations  reclaims  frees
# 1482710  1481203  1507  1507  0  0

# Cache hit rate = hits / lookups → typically > 99%
```

---

## 9. Object Classes and Permissions

### Object Class Taxonomy

Object classes define **what type of kernel object** is being accessed. Each class has its own set of valid permissions.

```
FILESYSTEM CLASSES:
  filesystem    → The filesystem itself (mount, remount, unmount, ...)
  file          → Regular files (read, write, execute, create, unlink, ...)
  dir           → Directories (search, add_name, remove_name, rmdir, ...)
  lnk_file      → Symbolic links
  chr_file      → Character devices
  blk_file      → Block devices
  sock_file     → UNIX domain socket files
  fifo_file     → Named pipes

NETWORK CLASSES:
  socket        → Generic socket
  tcp_socket    → TCP sockets
  udp_socket    → UDP sockets
  rawip_socket  → Raw IP sockets
  netlink_socket → Netlink sockets (many subtypes)
  unix_stream_socket → UNIX stream socket
  unix_dgram_socket  → UNIX datagram socket
  packet_socket → Packet sockets (AF_PACKET)
  icmp_socket   → ICMP sockets (modern kernels)
  
PROCESS CLASSES:
  process       → Process operations (fork, exec, kill, ptrace, ...)
  process2      → Additional process operations

IPC CLASSES:
  ipc           → Generic IPC
  sem           → POSIX semaphores
  msgq          → Message queues
  shm           → Shared memory
  
CAPABILITY CLASSES:
  capability    → POSIX capabilities (cap_net_bind_service, cap_chown, ...)
  capability2   → Additional capabilities (cap_block_suspend, ...)
  cap_userns    → Capabilities within user namespaces

SECURITY CLASSES:
  security      → SELinux operations (load_policy, setbool, ...)
  system        → System-level operations (reboot, syslog, ...)
  
KERNEL CLASSES:
  key           → Kernel keyring objects
  bpf           → BPF programs/maps
  perf_event    → Perf events
  io_uring      → io_uring operations
```

### File Class Permissions — Complete List

```te
# class file {
#   ioctl        - ioctl() on the file
#   read         - read()
#   write        - write()
#   create       - create the file
#   getattr      - stat()
#   setattr      - chmod(), chown(), utimes()
#   lock         - flock(), fcntl(F_SETLK)
#   relabelfrom  - change label away from this type
#   relabelto    - change label to this type
#   append       - open with O_APPEND or append-only write
#   map          - mmap() the file
#   unlink       - delete (unlink) the file
#   link         - create a hard link to it
#   rename       - rename it
#   execute      - execute it as a program
#   execute_no_trans - execute without domain transition
#   entrypoint   - use as entrypoint for a domain transition
#   open         - open() the file (required in addition to read/write)
#   audit_access - trigger audit on access
#   execmod      - execute a file with modified memory map
#   watch        - inotify/fanotify watches
#   watch_mount  - watch filesystem mounts
#   watch_sb     - watch superblock
#   watch_with_perm - watch with specific permissions
#   watch_reads  - watch for reads
# }

# Practical example: comprehensive file access
allow myapp_t myapp_data_t:file {
    create unlink rename
    open read write append
    getattr setattr
    lock map
    ioctl
};
```

### Process Class Permissions

```te
# class process {
#   fork          - fork()
#   transition    - execute domain transition
#   sigchld       - send SIGCHLD
#   sigkill       - send SIGKILL
#   sigstop       - send SIGSTOP
#   signull       - check process existence (kill -0)
#   signal        - send other signals
#   ptrace        - ptrace()
#   getsched      - getpriority() / sched_getscheduler()
#   setsched      - setpriority() / sched_setscheduler()
#   getsession    - getsid()
#   getpgid       - getpgid()
#   setpgid       - setpgid()
#   getcap        - get capabilities
#   setcap        - set capabilities
#   share         - share state during clone()
#   getattr       - /proc/PID/status, etc.
#   setattr       - change process security label
#   setexec       - set exec SID (setexeccon)
#   setfscreate   - set file creation context
#   noatsecure    - disable AT_SECURE on exec
#   siginh        - signal inheritance across exec
#   setrlimit     - setrlimit()
#   rlimitinh     - rlimit inheritance
#   dyntransition - dynamic label transition
#   execmem       - execute from anonymous memory (no-exec bypass)
#   execstack     - execute from stack
#   execheap      - execute from heap
# }
```

### Capability Class

```te
# Maps to Linux capabilities (man 7 capabilities)
allow myapp_t self:capability {
    chown              # Change file ownership
    dac_override       # Bypass DAC permission checks  ← dangerous!
    dac_read_search    # Bypass DAC read/search checks
    fowner             # Bypass permission checks where owner match required
    fsetid             # Don't clear setuid/setgid on modification
    kill               # Send signals to arbitrary processes
    setgid             # Make arbitrary GID manipulations
    setuid             # Make arbitrary UID manipulations
    setpcap            # Manipulate process capabilities
    linux_immutable    # Set immutable/append-only file attributes
    net_bind_service   # Bind to privileged ports (<1024)
    net_broadcast      # Make socket broadcasts
    net_admin          # Network administration
    net_raw            # Use raw sockets
    ipc_lock           # Lock memory (mlock, mlockall, mmap MAP_LOCKED)
    ipc_owner          # Bypass IPC ownership checks
    sys_module         # Load/unload kernel modules
    sys_rawio          # Raw I/O (iopl, ioperm)
    sys_chroot         # chroot()
    sys_ptrace         # ptrace() any process
    sys_pacct          # Process accounting
    sys_admin          # Huge privilege bucket ← very dangerous
    sys_boot           # reboot(), kexec_load()
    sys_nice           # Change process priorities
    sys_resource       # Override resource limits
    sys_time           # Set system time
    sys_tty_config     # Configure TTY devices
    mknod              # Create device special files
    lease              # Establish leases on files
    audit_write        # Write to kernel audit log
    audit_control      # Control kernel audit system
    setfcap            # Set file capabilities
};
```

---

## 10. Policy Module Architecture

### The Three Files of a Policy Module

Every policy module consists of three files:

```
myapp/
├── myapp.te    # Type Enforcement — the actual rules
├── myapp.fc    # File Contexts — label assignments for filesystem objects
└── myapp.if    # Interface — exported macros for other modules to use
```

### The .fc File — File Contexts

```
# FORMAT: path_regex  context
# Special file types: -- (regular), -d (dir), -l (symlink),
#                     -c (char dev), -b (block dev), -s (socket), -p (pipe)

# Executable binary
/usr/sbin/myapp                        --   system_u:object_r:myapp_exec_t:s0

# Configuration files
/etc/myapp(/.*)?                            system_u:object_r:myapp_conf_t:s0
/etc/myapp/myapp\.conf                 --   system_u:object_r:myapp_conf_t:s0

# Data directory
/var/lib/myapp(/.*)?                        system_u:object_r:myapp_var_t:s0

# Log files
/var/log/myapp\.log                    --   system_u:object_r:myapp_log_t:s0
/var/log/myapp(/.*)?                        system_u:object_r:myapp_log_t:s0

# PID file
/run/myapp\.pid                        --   system_u:object_r:myapp_var_run_t:s0
/run/myapp(/.*)?                            system_u:object_r:myapp_var_run_t:s0

# UNIX socket
/run/myapp\.sock                       =s   system_u:object_r:myapp_var_run_t:s0

# tmpfiles
/tmp/myapp-[^/]*                       --   system_u:object_r:myapp_tmp_t:s0

# Systemd unit file
/usr/lib/systemd/system/myapp\.service --   system_u:object_r:myapp_unit_file_t:s0
```

### Complete .te File for a Real Application

```te
##############################################################
# myapp.te — Policy for MyApp, a hypothetical network daemon
##############################################################

policy_module(myapp, 1.0.0)

##------------------------------------------------------------
## Attribute declarations
##------------------------------------------------------------

attribute myapp_domain;

##------------------------------------------------------------
## Type declarations
##------------------------------------------------------------

# Main process domain
type myapp_t;
typeattribute myapp_t myapp_domain;

# Use a macro that declares type as a domain and sets up
# basic process permissions (from userdomain.if)
type myapp_exec_t;
application_domain(myapp_t, myapp_exec_t)

# Configuration files
type myapp_conf_t;
files_config_file(myapp_conf_t)

# Variable data
type myapp_var_t;
files_type(myapp_var_t)

# Log files
type myapp_log_t;
logging_log_file(myapp_log_t)

# Runtime files (pid, sock)
type myapp_var_run_t;
files_pid_file(myapp_var_run_t)

# Temp files
type myapp_tmp_t;
files_tmp_file(myapp_tmp_t)

# Unit file type
type myapp_unit_file_t;
systemd_unit_file(myapp_unit_file_t)

##------------------------------------------------------------
## Domain entry point — systemd can start it
##------------------------------------------------------------

init_daemon_domain(myapp_t, myapp_exec_t)

##------------------------------------------------------------
## File access
##------------------------------------------------------------

# Read configuration
allow myapp_t myapp_conf_t:dir { search open read getattr };
allow myapp_t myapp_conf_t:file { open read getattr };

# Manage variable data directory
manage_dirs_pattern(myapp_t, myapp_var_t, myapp_var_t)
manage_files_pattern(myapp_t, myapp_var_t, myapp_var_t)

# Write logs
allow myapp_t myapp_log_t:dir { search add_name write open read getattr };
allow myapp_t myapp_log_t:file { create open write append getattr };

# Manage runtime directory
manage_dirs_pattern(myapp_t, myapp_var_run_t, myapp_var_run_t)
manage_files_pattern(myapp_t, myapp_var_run_t, myapp_var_run_t)
manage_sock_files_pattern(myapp_t, myapp_var_run_t, myapp_var_run_t)
files_pid_filetrans(myapp_t, myapp_var_run_t, { file dir sock_file })

# Temp files
allow myapp_t myapp_tmp_t:file { create open write read getattr unlink };
files_tmp_filetrans(myapp_t, myapp_tmp_t, file)

##------------------------------------------------------------
## Network access — TCP server on port 8443
##------------------------------------------------------------

allow myapp_t self:tcp_socket { create bind listen accept read write };
allow myapp_t self:udp_socket { create bind read write };

# Bind to a labeled port
corenet_tcp_bind_generic_node(myapp_t)
allow myapp_t myapp_port_t:tcp_socket name_bind;

# Connect to a database on port 5432
allow myapp_t postgresql_port_t:tcp_socket name_connect;

##------------------------------------------------------------
## Process capabilities
##------------------------------------------------------------

allow myapp_t self:capability { net_bind_service setuid setgid };
allow myapp_t self:process { fork getsched setsched signal };

##------------------------------------------------------------
## System resources
##------------------------------------------------------------

# Read /proc/self
allow myapp_t self:process { getattr };
allow myapp_t proc_t:file { read };

# Use kernel entropy
dev_read_rand(myapp_t)
dev_read_urand(myapp_t)

# Resolve hostnames (nsswitch/DNS)
sysnet_dns_name_resolve(myapp_t)

# Use system locale
miscfiles_read_localization(myapp_t)
miscfiles_read_public_files(myapp_t)

# Logging via syslog
logging_send_syslog_msg(myapp_t)

##------------------------------------------------------------
## Dontaudit noise suppressions
##------------------------------------------------------------

# Suppress common benign access denials
dontaudit myapp_t self:capability sys_resource;
dontaudit myapp_t kernel_t:system syslog_read;
dontaudit myapp_t proc_t:file { read getattr };

##------------------------------------------------------------
## Optional: interact with users via the UNIX socket
##------------------------------------------------------------

optional_policy(`
    gen_require(`
        type user_t;
    ')
    allow user_t myapp_var_run_t:sock_file write;
    allow user_t myapp_t:unix_stream_socket connectto;
')

##------------------------------------------------------------
## Tunable (boolean-controlled) access
##------------------------------------------------------------

tunable_policy(`myapp_can_connect_ldap',`
    allow myapp_t ldap_port_t:tcp_socket name_connect;
')

tunable_policy(`myapp_use_nfs',`
    fs_manage_nfs_files(myapp_t)
')
```

---

## 11. M4 Macro System and Interface Layers

### Why M4?

The SELinux reference policy uses **GNU M4** as a macro preprocessor. Raw `.te` files go through M4 expansion before being compiled by `checkpolicy`. This enables:

- **Code reuse** via interface macros
- **Conditional policy** via `ifdef`, `ifndef`
- **String manipulation** for generated policy

### Interface File (.if) — Exposing Your Module's API

```te
## <summary>MyApp policy module interfaces</summary>

########################################
## <summary>
##   Execute myapp in the myapp domain.
## </summary>
## <param name="domain">
##   Domain allowed access.
## </param>
#
interface(`myapp_domtrans',`
    gen_require(`
        type myapp_t, myapp_exec_t;
    ')
    
    corecmd_search_bin($1)
    domtrans_pattern($1, myapp_exec_t, myapp_t)
')

########################################
## <summary>
##   Read myapp configuration files.
## </summary>
## <param name="domain">
##   Domain allowed access.
## </param>
#
interface(`myapp_read_config',`
    gen_require(`
        type myapp_conf_t;
    ')
    
    files_search_etc($1)
    allow $1 myapp_conf_t:dir list_dir_perms;
    allow $1 myapp_conf_t:file read_file_perms;
    allow $1 myapp_conf_t:lnk_file read_lnk_file_perms;
')

########################################
## <summary>
##   Connect to myapp via its UNIX socket.
## </summary>
## <param name="domain">
##   Domain allowed access.
## </param>
#
interface(`myapp_stream_connect',`
    gen_require(`
        type myapp_t, myapp_var_run_t;
    ')
    
    files_search_pids($1)
    stream_connect_pattern($1, myapp_var_run_t, myapp_var_run_t, myapp_t)
')

########################################
## <summary>
##   All permissions required for myapp administration.
## </summary>
## <param name="domain">
##   Domain allowed access.
## </param>
#
interface(`myapp_admin',`
    gen_require(`
        type myapp_t, myapp_conf_t, myapp_log_t;
        type myapp_var_t, myapp_var_run_t, myapp_tmp_t;
        type myapp_unit_file_t;
    ')
    
    allow $1 myapp_t:process { signal signull sigkill };
    
    myapp_domtrans($1)
    
    files_search_etc($1)
    admin_pattern($1, myapp_conf_t)
    
    logging_search_logs($1)
    admin_pattern($1, myapp_log_t)
    
    files_search_var($1)
    admin_pattern($1, myapp_var_t)
    
    files_search_pids($1)
    admin_pattern($1, myapp_var_run_t)
    
    files_search_tmp($1)
    admin_pattern($1, myapp_tmp_t)
    
    systemd_admin_unit_file($1, myapp_unit_file_t)
')
```

### Core M4 Macros from Reference Policy

```te
#============================================================
# IMPORTANT MACRO PATTERNS (defined in support/macros.spt)
#============================================================

# read_files_pattern(domain, dir_type, file_type)
# Expands to: allow domain to search dir_type dirs and read file_type files
define(`read_files_pattern',`
    allow $1 $2:dir search_dir_perms;
    allow $1 $3:file read_file_perms;
')

# manage_files_pattern(domain, dir_type, file_type)
# Expands to full CRUD on files
define(`manage_files_pattern',`
    allow $1 $2:dir rw_dir_perms;
    allow $1 $3:file manage_file_perms;
')

# domtrans_pattern(source, entry, target)
# Full domain transition setup
define(`domtrans_pattern',`
    allow $1 $2:file { getattr execute };
    allow $1 $3:process transition;
    allow $3 $2:file entrypoint;
    type_transition $1 $2:process $3;
    dontaudit $1 $3:process { noatsecure siginh rlimitinh };
    allow $3 $1:process sigchld;
')

# Shorthand permission sets
define(`read_file_perms', `{ getattr open read ioctl lock map }')
define(`manage_file_perms', `{ create open getattr setattr read write append rename link unlink ioctl lock map }')
define(`search_dir_perms', `{ getattr search open }')
define(`list_dir_perms', `{ getattr search open read lock ioctl }')
define(`rw_dir_perms', `{ open read getattr lock search ioctl add_name remove_name write }')
define(`stream_connect_pattern',`
    allow $1 $2:dir search_dir_perms;
    allow $1 $3:sock_file write;
    allow $1 $4:unix_stream_socket connectto;
')
```

### M4 Conditional Policy

```te
# ifdef/ifndef for build-time conditionals
ifdef(`distro_rhel',`
    # RHEL-specific rules
    allow myapp_t rhel_specific_t:file read;
')

ifdef(`enable_mls',`
    # MLS-specific additions
    range_transition init_t myapp_exec_t:process s0;
')

# optional_policy — only include if the referenced module is loaded
optional_policy(`
    gen_require(`
        type apache_t;
    ')
    # Allow apache to use myapp's UNIX socket
    myapp_stream_connect(apache_t)
')

# tunable_policy — boolean-controlled at runtime
tunable_policy(`httpd_can_network_connect',`
    allow httpd_t port_type:tcp_socket name_connect;
')
```

---

## 12. Writing Complex, Real-World Policies

### Case Study: A Complete Microservice Policy

```te
##############################################################
# payment_service.te
# Policy for a payment processing microservice
# Runs as payment_service_t
# - Reads config from /etc/payment/
# - Reads TLS certs from /etc/ssl/payment/
# - Connects to PostgreSQL on port 5432
# - Connects to Redis on port 6379  
# - Exposes gRPC API on port 9090
# - Writes audit logs to /var/log/payment/
# - Must NEVER have access to general /etc/ files
# - Must NEVER fork arbitrary processes
##############################################################

policy_module(payment_service, 2.1.0)

##------------------------------------------------------------
## Declarations
##------------------------------------------------------------
type payment_service_t;
type payment_service_exec_t;
type payment_service_conf_t;
type payment_service_cert_t;
type payment_service_log_t;
type payment_service_var_run_t;
type payment_service_port_t;
type payment_service_db_t;

application_domain(payment_service_t, payment_service_exec_t)
init_daemon_domain(payment_service_t, payment_service_exec_t)

##------------------------------------------------------------
## Hard neverallow constraints — compile-time invariants
##------------------------------------------------------------

# Payment service must NEVER write to system config
neverallow payment_service_t { etc_t etc_runtime_t }:file write;

# Must NEVER execute arbitrary binaries
neverallow payment_service_t { bin_t usr_t sbin_t }:file execute;

# Must NEVER gain additional capabilities
neverallow payment_service_t self:capability { sys_admin sys_ptrace sys_module };
neverallow payment_service_t self:process execmem;

# Must NEVER access user home directories
neverallow payment_service_t { user_home_dir_t user_home_t }:file { read write };

##------------------------------------------------------------
## Config file access
##------------------------------------------------------------

allow payment_service_t payment_service_conf_t:dir { search open read getattr };
allow payment_service_t payment_service_conf_t:file { open read getattr };

# Certificates — read-only access to cert files
allow payment_service_t payment_service_cert_t:dir { search open read getattr };
allow payment_service_t payment_service_cert_t:file { open read getattr map };

##------------------------------------------------------------
## Logging — append only
##------------------------------------------------------------

allow payment_service_t payment_service_log_t:dir { search add_name write open read getattr };
allow payment_service_t payment_service_log_t:file { create open append getattr };
# Critically: no 'write' permission (enforces append-only log integrity)
# Note: append implies write, but being explicit about intent matters

##------------------------------------------------------------
## Runtime files
##------------------------------------------------------------

manage_dirs_pattern(payment_service_t, payment_service_var_run_t, payment_service_var_run_t)
manage_files_pattern(payment_service_t, payment_service_var_run_t, payment_service_var_run_t)
files_pid_filetrans(payment_service_t, payment_service_var_run_t, { file dir })

##------------------------------------------------------------
## Network — very precise
##------------------------------------------------------------

# Create TCP sockets (needed for both client and server)
allow payment_service_t self:tcp_socket {
    create bind listen accept 
    read write 
    getopt setopt
    shutdown
};

# gRPC server — bind to port 9090
corenet_tcp_bind_generic_node(payment_service_t)
allow payment_service_t payment_service_port_t:tcp_socket name_bind;

# PostgreSQL client — connect only, no bind
allow payment_service_t postgresql_port_t:tcp_socket name_connect;

# Redis client — connect only
allow payment_service_t redis_port_t:tcp_socket name_connect;

# DNS resolution (required for service discovery)
sysnet_dns_name_resolve(payment_service_t)

# No raw sockets, no UDP, no ICMP — explicitly not allowed (default deny)

##------------------------------------------------------------
## Process constraints — minimal
##------------------------------------------------------------

allow payment_service_t self:process {
    fork               # spawn goroutines/threads
    getsched           # read scheduler params
    signal             # send signals to self
    sigchld            # receive child signals
};

# Capabilities — only what's needed
allow payment_service_t self:capability {
    net_bind_service   # bind to port < 1024 if needed
    setuid             # drop privileges on startup
    setgid             # drop group on startup
};

##------------------------------------------------------------
## System resources
##------------------------------------------------------------

# Entropy for crypto operations
dev_read_rand(payment_service_t)
dev_read_urand(payment_service_t)

# /proc/self for runtime introspection
allow payment_service_t self:process getattr;

# Syslog
logging_send_syslog_msg(payment_service_t)

# Shared libraries
libs_use_shared_libs(payment_service_t)
corecmd_exec_shell(payment_service_t)  # might be needed for scripts

##------------------------------------------------------------
## Deny audit noise
##------------------------------------------------------------

dontaudit payment_service_t self:capability sys_resource;
dontaudit payment_service_t proc_t:file read;
dontaudit payment_service_t proc_t:lnk_file read;

##------------------------------------------------------------
## Port definition (semanage does this at runtime, but for
## module portability we can define it in the module's .te)
##------------------------------------------------------------

type payment_service_port_t;
corenet_port(payment_service_port_t)
```

### Policy for a Container Runtime (Simplified)

```te
##############################################################
# container_engine.te
# Shows how container isolation policies work
##############################################################

# Container domains — all containers use one of these types
type svirt_lxc_net_t;    # containers with network access
type svirt_lxc_t;         # containers without network access
type svirt_sandbox_t;     # sandbox containers (more restricted)

typeattribute svirt_lxc_net_t svirt_domain;
typeattribute svirt_lxc_t svirt_domain;

# Container files
type svirt_sandbox_file_t;

# MCS constraint ensures containers can only access their own files
# The category pair (e.g., c200,c384) is unique per container

# Container engine (podman_t/docker_t) transitions to svirt_lxc_net_t
type_transition container_runtime_t container_exec_t:process svirt_lxc_net_t;

# Container can manage its own labeled files
manage_files_pattern(svirt_lxc_net_t, svirt_sandbox_file_t, svirt_sandbox_file_t)
manage_dirs_pattern(svirt_lxc_net_t, svirt_sandbox_file_t, svirt_sandbox_file_t)

# Containers cannot access each other's files — enforced by MCS constraint
# mlsconstrain file read (l1 eq l2 or ...) prevents cross-container access

# Container cannot break out via /proc
neverallow svirt_domain proc_kcore_t:file { read };
neverallow svirt_domain kernel_t:system { module_request };
```

---

## 13. Booleans — Runtime Policy Tuning

### What Booleans Are

Booleans are **runtime switches** that enable/disable portions of policy without recompiling it. The policy ships with if/else branches, and the boolean value selects which branch is active.

```bash
# List all booleans with current values
getsebool -a
# httpd_can_network_connect --> off
# httpd_can_sendmail --> off
# httpd_enable_cgi --> on
# httpd_use_nfs --> off

# Toggle at runtime (not persistent across reboots)
setsebool httpd_can_network_connect on

# Make persistent
setsebool -P httpd_can_network_connect on

# Check value
getsebool httpd_can_network_connect
```

### Defining Booleans in Policy

```te
# Declare the boolean (usually in global_tunables or a dedicated module)
gen_bool(myapp_can_connect_ldap, false)
gen_bool(myapp_use_nfs, false)
gen_bool(myapp_enable_debug_port, false)

# Use boolean in type enforcement rules
tunable_policy(`myapp_can_connect_ldap',`
    allow myapp_t ldap_port_t:tcp_socket name_connect;
    allow myapp_t self:tcp_socket { create connect };
',`
    # else branch — dontaudit the denial to avoid log spam
    dontaudit myapp_t ldap_port_t:tcp_socket name_connect;
')

tunable_policy(`myapp_use_nfs',`
    fs_manage_nfs_files(myapp_t)
    fs_read_nfs_symlinks(myapp_t)
')

tunable_policy(`myapp_enable_debug_port',`
    allow myapp_t myapp_debug_port_t:tcp_socket name_bind;
    # Allow local connections to debug port
    allow user_t myapp_debug_port_t:tcp_socket name_connect;
')
```

### How Booleans Work Internally

Booleans modify the AVC by tagging affected rules with a boolean ID. When the boolean is toggled:

1. The boolean state changes in `/sys/fs/selinux/booleans/<name>`
2. The kernel updates the conditional rules in the policy database
3. The AVC is flushed (all cached decisions invalidated)
4. Subsequent access checks use the new rules

```c
// Kernel: security/selinux/ss/services.c
int security_set_bools(u32 len, int *values) {
    // Validate inputs
    // Update boolean values in policy DB
    // For each conditional rule node affected:
    //   re-evaluate the boolean expression
    //   toggle the rule active/inactive
    // Flush AVC
    avc_ss_reset(state->ss->latest_granting);
    return 0;
}
```

---

## 14. File, Port, and Network Context Management

### File Context Management

```bash
#============================================================
# RESTORECON — restore file labels to policy defaults
#============================================================

# Restore single file
restorecon /var/www/html/index.html

# Recursive restore with verbose output
restorecon -Rv /var/www/html/

# Preview what would change (dry run)
restorecon -Rvn /var/www/html/

# Force restore even if already correct
restorecon -RFv /var/www/html/

#============================================================
# CHCON — temporary label change (doesn't persist relabel)
#============================================================

# Change file context
chcon -t httpd_sys_content_t /srv/mysite/index.html

# Change user and type
chcon -u system_u -t httpd_sys_content_t /srv/mysite/

# Reference file — copy context from another file
chcon --reference=/var/www/html/index.html /srv/mysite/index.html

#============================================================
# SEMANAGE FCONTEXT — permanent policy additions
#============================================================

# Add new path mapping
semanage fcontext -a -t httpd_sys_content_t "/srv/mysite(/.*)?"

# Then apply it
restorecon -Rv /srv/mysite/

# Modify existing mapping
semanage fcontext -m -t httpd_sys_rw_content_t "/srv/mysite/uploads(/.*)?"

# Delete a mapping
semanage fcontext -d "/srv/mysite(/.*)?"

# List all custom mappings
semanage fcontext -l -C
```

### Port Context Management

```bash
#============================================================
# SEMANAGE PORT — associate ports with types
#============================================================

# List all port contexts
semanage port -l

# Add a port
semanage port -a -t http_port_t -p tcp 8080
semanage port -a -t payment_service_port_t -p tcp 9090

# Modify existing
semanage port -m -t http_port_t -p tcp 8443

# Delete
semanage port -d -t http_port_t -p tcp 8080

# Range of ports
semanage port -a -t myapp_port_t -p tcp 9000-9100

# Check what type a port has
semanage port -l | grep "9090"

#============================================================
# Define port type in policy (.te file)
#============================================================

# In myapp.te:
type myapp_port_t;
corenet_port(myapp_port_t)   # Declare it as a network port type

# In myapp.fc (no entry needed — ports aren't filesystem objects)

# Runtime registration still required via semanage port
```

### Network Interface and Node Contexts

```bash
# Network interface contexts
semanage interface -l
semanage interface -a -t netif_t eth0

# Network node contexts (IP address ranges)
semanage node -l
semanage node -a -t node_t -p ipv4 -M 255.255.255.0 192.168.1.0
```

### Login and User Context Management

```bash
#============================================================
# SEMANAGE USER — SELinux user definitions
#============================================================

semanage user -l
# SELinux User    Prefix  MLS/MCS Range          SELinux Roles
# staff_u         user    s0-s0:c0.c1023         staff_r sysadm_r
# sysadm_u        user    s0-s0:c0.c1023         sysadm_r
# system_u        user    s0-s0:c0.c1023         system_r unconfined_r
# unconfined_u    user    s0-s0:c0.c1023         system_r unconfined_r user_r

# Add a new SELinux user
semanage user -a -R "staff_r sysadm_r" -r s0-s0:c0.c1023 contractor_u

#============================================================
# SEMANAGE LOGIN — Map Linux users to SELinux users
#============================================================

semanage login -l
# Login Name           SELinux User         MLS/MCS Range
# __default__          unconfined_u         s0-s0:c0.c1023
# root                 unconfined_u         s0-s0:c0.c1023
# alice                staff_u              s0-s0:c0.c1023

# Map a Linux user to a specific SELinux user
semanage login -a -s staff_u -r s0-s0:c0.c1023 alice

# Map root to a more constrained SELinux user
semanage login -m -s sysadm_u root
```

---

## 15. Constraint System and Validatetrans

### Constraints vs Allow Rules

Allow rules are **necessary but not sufficient**. Constraints add an additional layer of conditions that **must** be satisfied for an operation to be permitted, even if an allow rule exists.

```
PERMISSION GRANTED iff:
  1. An allow rule permits it (AV check)
  AND
  2. All applicable constraints are satisfied
  AND
  3. No applicable neverallow blocks it (compile-time only)
```

### Constraint Syntax

```te
# Constraint on file write operations
# l1 = source (process) level, l2 = target (file) level
# t1 = source type, t2 = target type
# r1 = source role, r2 = target role
# u1 = source user, u2 = target user

constrain file write (
    u1 == u2            # same SELinux user
    or t1 == can_write_others  # or has special type
    or r1 == sysadm_r   # or is sysadm role
);

# Relabeling constraints — prevent arbitrary relabeling
constrain file { relabelfrom relabelto } (
    t1 == can_relabel   # must have explicit permission type
);

# The standard relabeling constraint:
constrain { file dir lnk_file chr_file blk_file sock_file fifo_file } relabelto (
    u1 == u2
    and ( r1 == object_r or t1 == can_relabelto )
);
```

### MLS Constraints (mlsconstrain)

```te
# MLS write constraints — no write down
mlsconstrain file { write create setattr } (
    l2 domby l1         # target dominated by source (no write down)
    or t1 == mlsfilewrite      # or trusted type
    or t2 == mlstrustedobject  # or trusted object
);

# MLS read constraints — no read up
mlsconstrain file { read getattr execute } (
    l1 dom l2           # source dominates target (no read up)
    or t1 == mlsfileread       # or trusted reader
    or t2 == mlstrustedobject
);

# Process transition — level must not change (except for trusted procs)
mlsconstrain process transition (
    l1 eq l2
    or t1 == mlsprocwrite
);

# Socket: sending data at a level
mlsconstrain { tcp_socket udp_socket rawip_socket } { send_msg } (
    l1 dom l2
    or t1 == mlsnetwrite
);
```

### Validatetrans — Label Change Constraints

`validatetrans` checks whether a **label change** is valid, beyond what allow rules say:

```te
# Ensure that a file can only be relabeled by the original owner's user
# or by a trusted type
validatetrans file (
    u1 == u2            # old label user == new label user
    or t3 == relabeling_tool_t  # or the process doing relabeling is trusted
);

# t1 = current object label's type
# t2 = new object label's type
# t3 = type of the process doing the relabeling
# u1 = current object label's user
# u2 = new object label's user
# r1 = current object label's role
# r2 = new object label's role
```

---

## 16. Policy Compilation and Binary Format

### From Source to Binary

```
Source files (.te, .fc, .if)
        │
        ▼ M4 preprocessing
Expanded .te file
        │
        ▼ checkpolicy -M -c 33 -o myapp.pp myapp.te
Policy module (.pp) binary
        │
        ▼ semodule -i myapp.pp
Loaded into kernel policy database
        │
        ▼ /sys/fs/selinux/policy  (readable binary)
```

### Module Build Process

```bash
# Build from source using Makefile
# (after installing selinux-policy-devel)

make -f /usr/share/selinux/devel/Makefile myapp.pp

# This expands M4, runs checkpolicy, creates .pp file

# Install the module
semodule -i myapp.pp

# Verify installation
semodule -l | grep myapp

# Multiple modules at once
semodule -i myapp.pp myother.pp

# Remove module
semodule -r myapp

# Rebuild entire policy
semodule -B
```

### The Binary Policy Format

```
Binary policy file structure:
┌──────────────────────────────────────┐
│ Magic number: 0xf97cff8c             │
│ Policy version: 33 (kernel ≥ 5.x)   │
│ Target platform                      │
├──────────────────────────────────────┤
│ Symbol table section                 │
│  - Common permissions               │
│  - Object classes                   │
│  - Type declarations                │
│  - Role declarations                │
│  - User declarations                │
│  - Boolean declarations             │
│  - Sensitivity levels               │
│  - MLS categories                   │
├──────────────────────────────────────┤
│ AV Rules section                     │
│  - allow rules (AVRules)            │
│  - auditallow rules                 │
│  - dontaudit rules                  │
├──────────────────────────────────────┤
│ Type Transition rules section        │
├──────────────────────────────────────┤
│ Role Transition rules section        │
├──────────────────────────────────────┤
│ Role Allow rules section             │
├──────────────────────────────────────┤
│ Constraints section                  │
├──────────────────────────────────────┤
│ Conditional rules (booleans)         │
├──────────────────────────────────────┤
│ MLS section                          │
├──────────────────────────────────────┤
│ File contexts (in module packages)   │
└──────────────────────────────────────┘
```

### Policy Versioning

```bash
# Check current policy version
cat /sys/fs/selinux/policyvers
# 33

# Key policy version milestones:
# v12: Booleans
# v15: Netlink classes
# v16: Module support
# v18: Reject unknown permissions
# v22: Policy capabilities
# v24: IPv6 netlabels
# v25: Filename type transitions
# v26: Role transition on specific types
# v28: Userspace object manager support
# v30: Genetlink sockets
# v33: Ioctl allowlisting
# v34: BPF class
```

---

## 17. Audit Subsystem and AVC Denial Analysis

### Understanding AVC Denial Messages

```
type=AVC msg=audit(1693847291.532:487): avc:  denied  { read } 
  for  pid=2847 comm="myapp" name="config.json" dev="sda1" ino=393218 
  scontext=system_u:system_r:myapp_t:s0 
  tcontext=system_u:object_r:admin_conf_t:s0 
  tclass=file permissive=0

Breakdown:
  type=AVC             → AVC decision record
  audit(timestamp:id)  → audit record identifier
  avc: denied          → access was denied
  { read }             → the permission that was denied
  pid=2847             → process that was denied
  comm="myapp"         → process name
  name="config.json"   → target file name
  dev="sda1"           → device containing the file
  ino=393218           → inode number
  scontext=...         → SOURCE context (the process)
  tcontext=...         → TARGET context (the file)
  tclass=file          → object class
  permissive=0         → 0=enforcing, 1=permissive mode
```

### Analysis Workflow

```bash
#============================================================
# STEP 1: Identify denials
#============================================================

# Real-time monitoring
ausearch -m AVC,USER_AVC,SELINUX_ERR -ts recent

# Today's denials
ausearch -m AVC -ts today

# Denials for a specific process
ausearch -m AVC -c myapp

# Denials for a specific type
ausearch -m AVC | grep "myapp_t"

#============================================================
# STEP 2: Human-readable analysis
#============================================================

# audit2why provides explanation
ausearch -m AVC -ts recent | audit2why

# Example output:
# type=AVC ... denied { read } scontext=myapp_t tcontext=admin_conf_t tclass=file
# 
# Was caused by:
#         Missing type enforcement (TE) allow rule.
#         You can use audit2allow to generate a loadable module to allow this access.

#============================================================
# STEP 3: Generate policy fix
#============================================================

# Generate allow rules from denials
ausearch -m AVC -ts today | audit2allow

# Generate a complete loadable module
ausearch -m AVC -ts today | audit2allow -M myapp_local

# Review before applying
cat myapp_local.te

# Apply
semodule -i myapp_local.pp

#============================================================
# STEP 4: Advanced — setroubleshootd
#============================================================

# setroubleshootd provides user-friendly analysis
sealert -a /var/log/audit/audit.log

# GUI access (gnome)
sealert -b
```

### Permissive Mode — A Critical Concept

```bash
# System-wide permissive mode (policy still logged, not enforced)
setenforce 0   # permissive
setenforce 1   # enforcing
getenforce     # check current mode

# Per-domain permissive mode (much safer for debugging)
# Makes myapp_t permissive while everything else is enforcing
semanage permissive -a myapp_t

# Remove per-domain permissive
semanage permissive -d myapp_t

# List permissive domains
semanage permissive -l

# Check via policy
sesearch --allow -s myapp_t -c process | grep permissive
```

### sestatus and seinfo

```bash
# System SELinux status
sestatus
# SELinux status:                 enabled
# SELinuxfs mount:                /sys/fs/selinux
# SELinux mount point:            /sys/fs/selinux
# Loaded policy name:             targeted
# Current mode:                   enforcing
# Mode from config file:          enforcing
# Policy MLS status:              enabled
# Policy deny_unknown status:     allowed
# Memory protection checking:     actual (secure)
# Max kernel policy version:      33

# Query policy — what can a type do?
sesearch --allow -s httpd_t -c file
# allow httpd_t httpd_sys_content_t:file { read getattr open ... };
# allow httpd_t httpd_log_t:file { create write append ... };

# What types can access a specific type?
sesearch --allow -t httpd_sys_content_t -c file

# What transitions exist from httpd_t?
sesearch -T -s httpd_t

# List all types
seinfo -t

# List all roles and their types
seinfo -r -x

# Policy capabilities
seinfo --polcap
```

---

## 18. C Programming Interface — libselinux

### Getting and Setting Contexts

```c
// selinux_context.c
// gcc -o selinux_context selinux_context.c -lselinux

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <selinux/selinux.h>
#include <selinux/context.h>

// ============================================================
// Get the current process security context
// ============================================================
void print_process_context(void) {
    char *context = NULL;
    
    // Get current process context
    if (getcon(&context) < 0) {
        perror("getcon");
        return;
    }
    printf("Process context: %s\n", context);
    freecon(context);
    
    // Get context as a structured object for manipulation
    context_t ctx;
    if (getcon(&context) < 0) {
        perror("getcon");
        return;
    }
    
    ctx = context_new(context);
    if (!ctx) {
        perror("context_new");
        freecon(context);
        return;
    }
    
    printf("  User:  %s\n", context_user_get(ctx));
    printf("  Role:  %s\n", context_role_get(ctx));
    printf("  Type:  %s\n", context_type_get(ctx));
    printf("  Range: %s\n", context_range_get(ctx));
    
    context_free(ctx);
    freecon(context);
}

// ============================================================
// Get the security context of a file
// ============================================================
void print_file_context(const char *path) {
    char *context = NULL;
    
    // getfilecon follows symlinks; lgetfilecon does not
    if (getfilecon(path, &context) < 0) {
        fprintf(stderr, "getfilecon(%s): %s\n", path, strerror(errno));
        return;
    }
    printf("File context for %s: %s\n", path, context);
    freecon(context);
}

// ============================================================
// Get the security context of a process by PID
// ============================================================
void print_pid_context(pid_t pid) {
    char *context = NULL;
    
    if (getpidcon(pid, &context) < 0) {
        perror("getpidcon");
        return;
    }
    printf("PID %d context: %s\n", pid, context);
    freecon(context);
}

// ============================================================
// Set the file creation context for subsequent file operations
// ============================================================
int set_file_creation_context(const char *type) {
    char *current = NULL;
    char *new_context = NULL;
    context_t ctx;
    int rc;
    
    // Get current context
    if (getfscreatecon(&current) < 0) {
        perror("getfscreatecon");
        return -1;
    }
    
    if (current == NULL) {
        // No explicit fscreate context — use process context
        if (getcon(&current) < 0) {
            perror("getcon");
            return -1;
        }
    }
    
    // Modify the type field
    ctx = context_new(current);
    freecon(current);
    
    if (!ctx) {
        perror("context_new");
        return -1;
    }
    
    if (context_type_set(ctx, type) < 0) {
        perror("context_type_set");
        context_free(ctx);
        return -1;
    }
    
    new_context = context_str(ctx);
    if (!new_context) {
        perror("context_str");
        context_free(ctx);
        return -1;
    }
    
    // Set the file creation context
    rc = setfscreatecon(new_context);
    if (rc < 0) {
        perror("setfscreatecon");
    }
    
    context_free(ctx);
    return rc;
}

// ============================================================
// Compute the context a new process would get on exec
// ============================================================
void compute_exec_context(const char *scontext, const char *binary) {
    char *tcontext = NULL;
    char *new_context = NULL;
    
    // Get the file's context
    if (getfilecon(binary, &tcontext) < 0) {
        perror("getfilecon");
        return;
    }
    
    // Compute the resulting context after exec
    if (security_compute_create(scontext, tcontext, 
                                string_to_security_class("process"),
                                &new_context) < 0) {
        perror("security_compute_create");
        freecon(tcontext);
        return;
    }
    
    printf("Executing %s from %s → domain: %s\n", 
           binary, scontext, new_context);
    
    freecon(tcontext);
    freecon(new_context);
}

// ============================================================
// Check if an operation is allowed without actually performing it
// ============================================================
int check_permission(const char *scon, const char *tcon,
                     const char *class, const char *perm) {
    security_class_t sclass;
    access_vector_t av;
    
    // Convert class name to integer
    sclass = string_to_security_class(class);
    if (!sclass) {
        fprintf(stderr, "Unknown class: %s\n", class);
        return -1;
    }
    
    // Convert permission name to access vector
    av = string_to_av_perm(sclass, perm);
    if (!av) {
        fprintf(stderr, "Unknown permission: %s\n", perm);
        return -1;
    }
    
    // Check if the operation is allowed
    int rc = security_check_context(scon);
    if (rc < 0) {
        fprintf(stderr, "Invalid source context: %s\n", scon);
        return -1;
    }
    
    // Use security_compute_av to get the access vector decision
    struct av_decision avd;
    rc = security_compute_av(scon, tcon, sclass, av, &avd);
    if (rc < 0) {
        perror("security_compute_av");
        return -1;
    }
    
    if (avd.allowed & av) {
        printf("ALLOWED: %s %s %s:%s\n", scon, tcon, class, perm);
        return 1;
    } else {
        printf("DENIED:  %s %s %s:%s\n", scon, tcon, class, perm);
        return 0;
    }
}

int main(int argc, char *argv[]) {
    // Check if SELinux is enabled and enforcing
    int rc = is_selinux_enabled();
    if (rc == 0) {
        printf("SELinux is disabled\n");
        return 0;
    } else if (rc < 0) {
        perror("is_selinux_enabled");
        return 1;
    }
    
    printf("=== SELinux Context Information ===\n\n");
    
    print_process_context();
    printf("\n");
    
    print_file_context("/etc/passwd");
    print_file_context("/etc/shadow");
    printf("\n");
    
    print_pid_context(1);  // init/systemd
    printf("\n");
    
    compute_exec_context("system_u:system_r:httpd_t:s0", "/usr/sbin/httpd");
    printf("\n");
    
    // Permission checks
    check_permission("system_u:system_r:httpd_t:s0",
                     "system_u:object_r:httpd_sys_content_t:s0",
                     "file", "read");
    
    check_permission("system_u:system_r:httpd_t:s0",
                     "system_u:object_r:shadow_t:s0",
                     "file", "read");
    
    return 0;
}
```

### Advanced C: Building an Object Manager

SELinux can be extended to mediate access to **userspace objects** — not just kernel objects. This is called a **userspace object manager**:

```c
// userspace_object_manager.c
// An example of a service that uses SELinux to control access
// to its own internal resources (e.g., a database of records)
//
// gcc -o uom userspace_object_manager.c -lselinux -lsepol

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <selinux/selinux.h>
#include <selinux/avc.h>

// Our userspace object class
// (must be declared in policy with "class myservice_record { read write delete }")
#define MYSERVICE_CLASS    "myservice_record"
#define PERM_READ          "read"
#define PERM_WRITE         "write"
#define PERM_DELETE        "delete"

// ============================================================
// AVC callback — called when access is denied
// ============================================================
static int my_audit(void *auditdata, security_class_t cls, 
                    char *msgbuf, size_t msgbufsize) {
    const char *operation = (const char *)auditdata;
    snprintf(msgbuf, msgbufsize, 
             "userspace object manager: operation=%s", operation);
    return 0;
}

// ============================================================
// Initialize the userspace AVC
// ============================================================
int init_selinux_avc(void) {
    union selinux_callback cb;
    
    // Register audit callback
    cb.func_audit = my_audit;
    selinux_set_callback(SELINUX_CB_AUDIT, cb);
    
    // Initialize userspace AVC
    if (avc_open(NULL, 0) < 0) {
        perror("avc_open");
        return -1;
    }
    
    return 0;
}

// ============================================================
// Check if a process (by context) can perform an operation
// on one of our objects (also identified by context)
// ============================================================
int check_access(const char *subject_context,
                 const char *object_context,
                 const char *permission,
                 const char *operation_name) {
    
    security_id_t ssid, tsid;
    security_class_t tclass;
    
    // Convert context strings to security IDs
    if (avc_context_to_sid(subject_context, &ssid) < 0) {
        perror("avc_context_to_sid (subject)");
        return -1;
    }
    
    if (avc_context_to_sid(object_context, &tsid) < 0) {
        perror("avc_context_to_sid (object)");
        return -1;
    }
    
    // Get our custom class ID
    tclass = string_to_security_class(MYSERVICE_CLASS);
    if (!tclass) {
        fprintf(stderr, "Class '%s' not found in policy\n", MYSERVICE_CLASS);
        return -1;
    }
    
    // Get the permission bit
    access_vector_t av = string_to_av_perm(tclass, permission);
    if (!av) {
        fprintf(stderr, "Permission '%s' not found\n", permission);
        return -1;
    }
    
    // Perform the access check
    int rc = avc_has_perm(ssid, tsid, tclass, av,
                           NULL,  // AVC entry (NULL = use cache)
                           (void *)operation_name);  // audit data
    
    if (rc == 0) {
        printf("ACCESS GRANTED: %s can %s record\n", 
               subject_context, permission);
        return 0;
    } else {
        printf("ACCESS DENIED: %s cannot %s record\n", 
               subject_context, permission);
        return -1;
    }
}

// ============================================================
// Get the context of the peer process connected via socket fd
// ============================================================
int get_peer_context(int sockfd, char **context) {
    if (getpeercon(sockfd, context) < 0) {
        perror("getpeercon");
        return -1;
    }
    return 0;
}

// ============================================================
// Label a new object based on the subject and directory context
// ============================================================
int compute_new_object_label(const char *subject_ctx,
                              const char *dir_ctx,
                              char **new_label) {
    security_class_t sclass = string_to_security_class("file");
    
    return security_compute_create(subject_ctx, dir_ctx, sclass, new_label);
}

int main(void) {
    if (!is_selinux_enabled()) {
        fprintf(stderr, "SELinux not enabled\n");
        return 1;
    }
    
    if (init_selinux_avc() < 0) {
        return 1;
    }
    
    // Simulate: httpd process trying to read a record
    const char *httpd_ctx = "system_u:system_r:httpd_t:s0";
    const char *record_ctx = "system_u:object_r:myservice_record_t:s0";
    
    check_access(httpd_ctx, record_ctx, PERM_READ, "RecordRead");
    check_access(httpd_ctx, record_ctx, PERM_WRITE, "RecordWrite");
    check_access(httpd_ctx, record_ctx, PERM_DELETE, "RecordDelete");
    
    avc_destroy();
    return 0;
}
```

### C: SELinux-Aware Daemon with Label Verification

```c
// selinux_daemon.c
// A daemon that verifies callers' SELinux contexts before serving requests
// Demonstrates: getpeercon, context parsing, access decisions

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>
#include <selinux/selinux.h>
#include <selinux/context.h>

#define SOCKET_PATH "/run/myservice.sock"

// Allowed types that can connect to this daemon
static const char *ALLOWED_TYPES[] = {
    "httpd_t",
    "payment_service_t",
    "monitoring_t",
    NULL
};

// ============================================================
// Verify that a connecting client has an allowed type
// ============================================================
int verify_client_context(int client_fd) {
    char *peer_context = NULL;
    context_t ctx;
    const char *type;
    int allowed = 0;
    
    // Get the SELinux context of the connected peer
    if (getpeercon(client_fd, &peer_context) < 0) {
        // If we can't get the peer context, deny
        perror("getpeercon");
        return -1;
    }
    
    printf("Client context: %s\n", peer_context);
    
    // Parse the context
    ctx = context_new(peer_context);
    if (!ctx) {
        freecon(peer_context);
        return -1;
    }
    
    type = context_type_get(ctx);
    if (!type) {
        context_free(ctx);
        freecon(peer_context);
        return -1;
    }
    
    // Check if the type is in our allowlist
    for (int i = 0; ALLOWED_TYPES[i] != NULL; i++) {
        if (strcmp(type, ALLOWED_TYPES[i]) == 0) {
            allowed = 1;
            printf("Client type '%s' is authorized\n", type);
            break;
        }
    }
    
    if (!allowed) {
        fprintf(stderr, "DENIED: Client type '%s' is not authorized\n", type);
    }
    
    context_free(ctx);
    freecon(peer_context);
    
    return allowed ? 0 : -1;
}

// ============================================================
// Check SELinux is in enforcing mode — refuse to start if not
// ============================================================
void require_enforcing(void) {
    int enforcing = security_getenforce();
    if (enforcing < 0) {
        perror("security_getenforce");
        exit(1);
    }
    if (enforcing == 0) {
        fprintf(stderr, 
                "FATAL: SELinux is not in enforcing mode. "
                "This daemon requires enforcing mode for security guarantees.\n");
        exit(1);
    }
    printf("SELinux enforcing mode confirmed.\n");
}

int main(void) {
    if (!is_selinux_enabled()) {
        fprintf(stderr, "FATAL: SELinux is not enabled\n");
        return 1;
    }
    
    require_enforcing();
    
    // Print our own context
    char *myctx = NULL;
    getcon(&myctx);
    printf("Daemon running as: %s\n", myctx);
    freecon(myctx);
    
    // Create UNIX socket
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return 1;
    }
    
    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);
    
    unlink(SOCKET_PATH);
    
    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }
    
    // Set socket file context for SELinux
    // The socket should be labeled myservice_socket_t per our policy
    if (setfscreatecon("system_u:object_r:myservice_socket_t:s0") < 0) {
        // Non-fatal — log and continue
        perror("setfscreatecon (socket)");
    }
    
    listen(server_fd, 10);
    printf("Listening on %s\n", SOCKET_PATH);
    
    // Reset fscreate context
    setfscreatecon(NULL);
    
    while (1) {
        int client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }
        
        // Verify client before doing anything
        if (verify_client_context(client_fd) < 0) {
            const char *denied = "ERROR: Access denied\n";
            write(client_fd, denied, strlen(denied));
            close(client_fd);
            continue;
        }
        
        // Serve the client
        const char *response = "OK: Request processed\n";
        write(client_fd, response, strlen(response));
        close(client_fd);
    }
    
    close(server_fd);
    return 0;
}
```

---

## 19. Rust Programming Interface

### Crate Ecosystem

```toml
# Cargo.toml
[dependencies]
# Primary SELinux binding
selinux = "0.3"

# For process context operations, low-level bindings
nix = { version = "0.27", features = ["socket", "process", "fs"] }

# Async runtime (for daemon examples)
tokio = { version = "1", features = ["full"] }

# Error handling
thiserror = "1"
anyhow = "1"
```

### Core SELinux Operations in Rust

```rust
// src/selinux_ops.rs
use selinux::{
    self,
    SecurityContext,
    OpaqueSecurityContext,
    InitialContext,
};
use std::path::Path;
use std::fs::File;
use anyhow::{Context, Result, bail};

/// Check if SELinux is enabled and enforcing.
/// Fail fast if security requirements are not met.
pub fn verify_selinux_enforcing() -> Result<()> {
    match selinux::kernel_support() {
        selinux::KernelSupport::Unsupported => {
            bail!("SELinux is not supported by this kernel")
        }
        selinux::KernelSupport::Permissive => {
            bail!("SELinux is in permissive mode — enforcing required")
        }
        selinux::KernelSupport::Enforcing => {
            println!("SELinux is enabled and enforcing");
            Ok(())
        }
    }
}

/// Get the security context of the current process.
pub fn get_process_context() -> Result<String> {
    let ctx = selinux::current_thread_context()
        .context("Failed to get current process context")?;
    
    Ok(ctx.to_c_string()
        .context("Context contains invalid characters")?
        .to_string_lossy()
        .into_owned())
}

/// Get the security context of a file.
pub fn get_file_context(path: &Path) -> Result<String> {
    let ctx = selinux::SecurityContext::of_path(path, false, false)
        .context("Failed to get file security context")?
        .context("File has no security context")?;
    
    Ok(ctx.to_c_string()
        .context("Context string error")?
        .to_string_lossy()
        .into_owned())
}

/// Get the security context of a process by PID.
pub fn get_pid_context(pid: libc::pid_t) -> Result<String> {
    // Read from /proc/<pid>/attr/current
    let attr_path = format!("/proc/{}/attr/current", pid);
    let raw = std::fs::read_to_string(&attr_path)
        .with_context(|| format!("Failed to read context for PID {}", pid))?;
    
    // Strip null terminator if present
    Ok(raw.trim_end_matches('\0').to_string())
}

/// Set the file creation context for subsequent file creation operations.
/// Returns a guard that resets the context when dropped.
pub struct FsCreateContextGuard {
    previous: Option<OpaqueSecurityContext>,
}

impl FsCreateContextGuard {
    pub fn new(context: &str) -> Result<Self> {
        // Save current context
        let previous = selinux::thread_local_fs_create_context()
            .context("Failed to get current fs create context")?;
        
        // Parse and set new context
        let ctx = OpaqueSecurityContext::from_c_string(
            &std::ffi::CString::new(context)
                .context("Context contains null byte")?
        ).context("Invalid security context")?;
        
        selinux::set_thread_local_fs_create_context(Some(ctx.as_ref()))
            .context("Failed to set fs create context")?;
        
        Ok(FsCreateContextGuard { 
            previous: previous.map(|c| c) 
        })
    }
}

impl Drop for FsCreateContextGuard {
    fn drop(&mut self) {
        // Reset to previous context (or None to use default)
        let _ = selinux::set_thread_local_fs_create_context(
            self.previous.as_ref().map(|c| c.as_ref())
        );
    }
}

/// Parse a security context string into its components.
#[derive(Debug, Clone)]
pub struct ParsedContext {
    pub user: String,
    pub role: String,
    pub type_: String,
    pub range: Option<String>,
}

impl ParsedContext {
    pub fn parse(context: &str) -> Result<Self> {
        let parts: Vec<&str> = context.split(':').collect();
        
        match parts.len() {
            3 => Ok(ParsedContext {
                user: parts[0].to_string(),
                role: parts[1].to_string(),
                type_: parts[2].to_string(),
                range: None,
            }),
            4 => Ok(ParsedContext {
                user: parts[0].to_string(),
                role: parts[1].to_string(),
                type_: parts[2].to_string(),
                range: Some(parts[3].to_string()),
            }),
            5 => Ok(ParsedContext {
                user: parts[0].to_string(),
                role: parts[1].to_string(),
                type_: parts[2].to_string(),
                // Range is "level:categories" in MLS contexts
                range: Some(format!("{}:{}", parts[3], parts[4])),
            }),
            _ => bail!("Invalid context format: '{}'", context),
        }
    }
    
    pub fn domain_type(&self) -> &str {
        &self.type_
    }
    
    pub fn is_system_process(&self) -> bool {
        self.user == "system_u" && self.role == "system_r"
    }
    
    pub fn is_unconfined(&self) -> bool {
        self.type_.ends_with("_unconfined_t") || 
        self.type_ == "unconfined_t"
    }
}
```

### Rust: SELinux-Aware Async Service

```rust
// src/selinux_service.rs
// A tokio-based async service that enforces SELinux context verification
// on all connecting clients

use std::path::Path;
use std::os::unix::io::AsRawFd;
use tokio::net::{UnixListener, UnixStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use anyhow::{Context, Result, bail};
use thiserror::Error;

// Custom error types for SELinux authorization
#[derive(Debug, Error)]
pub enum AuthError {
    #[error("Could not retrieve peer context: {0}")]
    ContextRetrieval(String),
    
    #[error("Client type '{0}' is not authorized")]
    UnauthorizedType(String),
    
    #[error("Context parse error: {0}")]
    ParseError(String),
    
    #[error("SELinux not in enforcing mode")]
    NotEnforcing,
}

/// Types that are allowed to connect to this service.
const AUTHORIZED_TYPES: &[&str] = &[
    "httpd_t",
    "payment_service_t",
    "monitoring_t",
    "staff_t",
];

/// Get the SELinux context of the peer connected to a Unix socket.
/// This is the Rust equivalent of getpeercon(3).
pub fn get_peer_selinux_context(stream: &UnixStream) -> Result<String, AuthError> {
    let fd = stream.as_raw_fd();
    
    // Read from /proc/self/fdinfo or use SO_PEERSEC socket option
    // In Linux, SO_PEERSEC gives the peer's SELinux context
    let mut context_buf = vec![0u8; 512];
    let mut len = context_buf.len() as libc::socklen_t;
    
    let rc = unsafe {
        libc::getsockopt(
            fd,
            libc::SOL_SOCKET,
            libc::SO_PEERSEC,
            context_buf.as_mut_ptr() as *mut libc::c_void,
            &mut len,
        )
    };
    
    if rc != 0 {
        return Err(AuthError::ContextRetrieval(
            std::io::Error::last_os_error().to_string()
        ));
    }
    
    // Convert to string, stripping null terminator
    let context = String::from_utf8_lossy(&context_buf[..len as usize])
        .trim_end_matches('\0')
        .to_string();
    
    Ok(context)
}

/// Authorize a connecting client based on their SELinux type.
pub fn authorize_client(stream: &UnixStream) -> Result<String, AuthError> {
    let context_str = get_peer_selinux_context(stream)?;
    
    // Parse the context
    let parsed = crate::selinux_ops::ParsedContext::parse(&context_str)
        .map_err(|e| AuthError::ParseError(e.to_string()))?;
    
    let client_type = parsed.domain_type();
    
    // Check authorization
    if AUTHORIZED_TYPES.contains(&client_type) {
        println!("Authorized client type: {}", client_type);
        Ok(context_str)
    } else {
        Err(AuthError::UnauthorizedType(client_type.to_string()))
    }
}

/// Handle an authorized client connection.
async fn handle_client(mut stream: UnixStream, client_context: String) {
    let mut buf = [0u8; 1024];
    
    println!("Serving client: {}", client_context);
    
    loop {
        let n = match stream.read(&mut buf).await {
            Ok(0) => break,  // Connection closed
            Ok(n) => n,
            Err(e) => {
                eprintln!("Read error: {}", e);
                break;
            }
        };
        
        let request = String::from_utf8_lossy(&buf[..n]);
        println!("Request from {}: {}", client_context, request.trim());
        
        // Process request...
        let response = format!(
            "OK: Processed by SELinux-aware service (your context: {})\n",
            client_context
        );
        
        if let Err(e) = stream.write_all(response.as_bytes()).await {
            eprintln!("Write error: {}", e);
            break;
        }
    }
    
    println!("Client disconnected: {}", client_context);
}

/// Main service entry point.
pub async fn run_service(socket_path: &str) -> Result<()> {
    // Verify SELinux is enforcing before starting
    use selinux::KernelSupport;
    match selinux::kernel_support() {
        KernelSupport::Enforcing => {},
        _ => bail!("SELinux must be in enforcing mode"),
    }
    
    // Print our own context
    let our_context = crate::selinux_ops::get_process_context()
        .context("Failed to get own context")?;
    println!("Service running as: {}", our_context);
    
    // Remove stale socket
    let _ = std::fs::remove_file(socket_path);
    
    let listener = UnixListener::bind(socket_path)
        .with_context(|| format!("Failed to bind to {}", socket_path))?;
    
    println!("Listening on {}", socket_path);
    
    loop {
        let (stream, _addr) = listener.accept().await
            .context("Accept failed")?;
        
        // Authorize the client (synchronous — fast check)
        match authorize_client(&stream) {
            Ok(context) => {
                tokio::spawn(async move {
                    handle_client(stream, context).await;
                });
            }
            Err(e) => {
                eprintln!("Authorization failed: {}", e);
                // Connection is dropped here — client gets connection reset
            }
        }
    }
}
```

### Rust: Policy Analysis Tool

```rust
// src/policy_analyzer.rs
// Tool for programmatic SELinux policy analysis
// Reads /sys/fs/selinux/policy and analyzes allow rules

use std::collections::HashMap;
use std::io::Read;
use anyhow::{Context, Result};

/// Read the currently loaded policy binary.
pub fn read_current_policy() -> Result<Vec<u8>> {
    let mut file = std::fs::File::open("/sys/fs/selinux/policy")
        .context("Failed to open policy file (is SELinux enabled?)")?;
    
    let mut buf = Vec::new();
    file.read_to_end(&mut buf)
        .context("Failed to read policy")?;
    
    Ok(buf)
}

/// Query allow rules via seinfo command (wraps the userspace tool).
/// A production implementation would use libsepol directly.
pub fn query_allow_rules(source_type: &str, target_type: Option<&str>) 
    -> Result<Vec<AllowRule>> 
{
    let mut cmd = std::process::Command::new("sesearch");
    cmd.arg("--allow")
       .arg("-s").arg(source_type);
    
    if let Some(tt) = target_type {
        cmd.arg("-t").arg(tt);
    }
    
    let output = cmd.output()
        .context("Failed to run sesearch")?;
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    parse_sesearch_output(&stdout)
}

#[derive(Debug, Clone)]
pub struct AllowRule {
    pub source_type: String,
    pub target_type: String,
    pub class: String,
    pub permissions: Vec<String>,
}

fn parse_sesearch_output(output: &str) -> Result<Vec<AllowRule>> {
    let mut rules = Vec::new();
    
    for line in output.lines() {
        let line = line.trim();
        if !line.starts_with("allow ") {
            continue;
        }
        
        // Parse: allow source_t target_t:class { perm1 perm2 };
        // or:    allow source_t target_t:class perm;
        if let Some(rule) = parse_allow_line(line) {
            rules.push(rule);
        }
    }
    
    Ok(rules)
}

fn parse_allow_line(line: &str) -> Option<AllowRule> {
    // Strip "allow " prefix and ";" suffix
    let line = line.strip_prefix("allow ")?.trim_end_matches(';').trim();
    
    // Split into parts: "source target:class { perms }"
    let mut parts = line.splitn(2, ' ');
    let source = parts.next()?.trim().to_string();
    let rest = parts.next()?.trim();
    
    let colon_pos = rest.find(':')?;
    let target = rest[..colon_pos].trim().to_string();
    let rest = &rest[colon_pos + 1..];
    
    let space_pos = rest.find(' ')?;
    let class = rest[..space_pos].trim().to_string();
    let perms_str = rest[space_pos..].trim();
    
    let permissions: Vec<String> = perms_str
        .trim_start_matches('{')
        .trim_end_matches('}')
        .split_whitespace()
        .map(|s| s.to_string())
        .collect();
    
    Some(AllowRule {
        source_type: source,
        target_type: target,
        class,
        permissions,
    })
}

/// Find all types that can access a given target type with a given permission.
pub fn find_who_can_access(target_type: &str, class: &str, permission: &str) 
    -> Result<Vec<String>>
{
    let output = std::process::Command::new("sesearch")
        .arg("--allow")
        .arg("-t").arg(target_type)
        .arg("-c").arg(class)
        .arg("-p").arg(permission)
        .output()
        .context("Failed to run sesearch")?;
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let rules = parse_sesearch_output(&stdout)?;
    
    Ok(rules.into_iter()
        .map(|r| r.source_type)
        .collect::<std::collections::HashSet<_>>()
        .into_iter()
        .collect())
}

/// Check if a specific neverallow constraint would be violated.
pub fn check_neverallow(source: &str, target: &str, class: &str, perm: &str) 
    -> Result<bool> 
{
    let output = std::process::Command::new("sesearch")
        .arg("--neverallow")
        .arg("-s").arg(source)
        .arg("-t").arg(target)
        .arg("-c").arg(class)
        .arg("-p").arg(perm)
        .output()
        .context("Failed to run sesearch")?;
    
    // If sesearch returns any results, neverallow would be triggered
    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.trim().contains("neverallow"))
}

/// Generate a report of what a domain is allowed to do.
pub fn domain_capabilities_report(domain: &str) -> Result<()> {
    println!("=== Capabilities of domain: {} ===\n", domain);
    
    let rules = query_allow_rules(domain, None)?;
    
    // Group by class
    let mut by_class: HashMap<String, Vec<AllowRule>> = HashMap::new();
    for rule in rules {
        by_class.entry(rule.class.clone()).or_default().push(rule);
    }
    
    let mut classes: Vec<&String> = by_class.keys().collect();
    classes.sort();
    
    for class in classes {
        let rules = &by_class[class];
        println!("  {} ({} rules):", class, rules.len());
        for rule in rules {
            println!("    → {} : {:?}", rule.target_type, rule.permissions);
        }
    }
    
    // Network access summary
    let net_rules = query_allow_rules(domain, Some("port_t"))?;
    if !net_rules.is_empty() {
        println!("\n  Network port access:");
        for rule in &net_rules {
            println!("    → {}:{} {:?}", 
                     rule.target_type, rule.class, rule.permissions);
        }
    }
    
    Ok(())
}
```

### Rust: Complete CLI Policy Inspector

```rust
// src/main.rs — SELinux Policy Inspector CLI

use anyhow::Result;
use std::process;

mod selinux_ops;
mod policy_analyzer;
mod selinux_service;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <command> [args...]", args[0]);
        eprintln!("Commands:");
        eprintln!("  status                    - Show SELinux status");
        eprintln!("  context <pid>             - Show context of process");
        eprintln!("  file-context <path>       - Show file context");
        eprintln!("  domain-report <type>      - Report on domain capabilities");
        eprintln!("  who-can-access <type> <class> <perm> - Find who can access a type");
        process::exit(1);
    }
    
    match args[1].as_str() {
        "status" => {
            let result = selinux_ops::verify_selinux_enforcing();
            println!("Process context: {}", selinux_ops::get_process_context()?);
            result?;
        }
        
        "context" => {
            let pid: libc::pid_t = args.get(2)
                .and_then(|s| s.parse().ok())
                .unwrap_or(process::id() as libc::pid_t);
            
            let ctx = selinux_ops::get_pid_context(pid)?;
            println!("PID {} context: {}", pid, ctx);
            
            let parsed = selinux_ops::ParsedContext::parse(&ctx)?;
            println!("  User:  {}", parsed.user);
            println!("  Role:  {}", parsed.role);
            println!("  Type:  {}", parsed.type_);
            if let Some(range) = &parsed.range {
                println!("  Range: {}", range);
            }
        }
        
        "file-context" => {
            let path = args.get(2)
                .map(|s| std::path::Path::new(s))
                .ok_or_else(|| anyhow::anyhow!("Path required"))?;
            
            let ctx = selinux_ops::get_file_context(path)?;
            println!("File context: {}", ctx);
        }
        
        "domain-report" => {
            let domain = args.get(2)
                .ok_or_else(|| anyhow::anyhow!("Domain type required"))?;
            
            policy_analyzer::domain_capabilities_report(domain)?;
        }
        
        "who-can-access" => {
            if args.len() < 5 {
                bail!("Usage: who-can-access <target_type> <class> <permission>");
            }
            let target = &args[2];
            let class = &args[3];
            let perm = &args[4];
            
            let types = policy_analyzer::find_who_can_access(target, class, perm)?;
            println!("Types that can {} {} {}:", perm, class, target);
            for t in &types {
                println!("  {}", t);
            }
        }
        
        cmd => {
            eprintln!("Unknown command: {}", cmd);
            process::exit(1);
        }
    }
    
    Ok(())
}

// Required for bail! macro from anyhow
macro_rules! bail {
    ($msg:literal $(,)?) => {
        return Err(anyhow::anyhow!($msg))
    };
    ($fmt:expr, $($arg:tt)*) => {
        return Err(anyhow::anyhow!($fmt, $($arg)*))
    };
}
use bail;
```

---

## 20. Kernel Internals — Deep Implementation

### The Security Server

The Security Server (`security/selinux/ss/`) is the policy enforcement brain:

```c
// security/selinux/ss/services.c (conceptual — simplified)

struct selinux_state {
    bool enforcing;             // Enforcing vs permissive
    bool checkreqprot;          // Check requested or actual protection
    bool initialized;           // Policy loaded?
    bool policycap[__POLICYDB_CAPABILITY_MAX]; // Policy capabilities
    
    struct sidtab *sidtab;      // Security ID → context mapping
    struct policydb *policydb;  // The actual policy rules
    
    struct avc_cache avc;       // Access Vector Cache
    
    rwlock_t policy_rwlock;     // Protect policy updates
};

// SID (Security Identifier) is a u32 that maps to a security context
// The sidtab is a hash table: SID → context string
// The policydb contains all compiled rules

// security_compute_av: the core policy lookup function
int security_compute_av(struct selinux_state *state,
                         u32 ssid, u32 tsid, u16 tclass,
                         struct av_decision *avd) {
    
    struct context *scontext, *tcontext;
    struct class_datum *tclass_datum;
    struct av_inherit *avkey;
    
    read_lock(&state->policy_rwlock);
    
    // Resolve SIDs to contexts
    scontext = sidtab_search(state->sidtab, ssid);
    tcontext = sidtab_search(state->sidtab, tsid);
    
    // Get the class definition (which permissions exist)
    tclass_datum = policydb->class_val_to_struct[tclass - 1];
    
    // Default: deny everything
    avd->allowed = 0;
    avd->decided = ~0;  // All decided (as deny)
    avd->auditallow = 0;
    avd->auditdeny = ~0;
    
    // Look up type enforcement rules
    // The TE table is indexed by (stype, ttype, tclass)
    context_struct_compute_av(state->policydb, scontext, tcontext, 
                               tclass_datum, avd);
    
    // Apply constraints
    // If any constraint fails, remove the permission from allowed
    constraint_expr_eval(state, scontext, tcontext, tclass_datum, avd);
    
    // Apply MLS constraints
    mls_compute_av(state->policydb, scontext, tcontext, tclass_datum, avd);
    
    read_unlock(&state->policy_rwlock);
    
    return 0;
}
```

### SID Table (sidtab) Architecture

```c
// The SID table maps u32 SIDs ↔ security contexts
// Modern implementation (kernel 5.x+) uses RCU-protected hash tables

struct sidtab_entry {
    u32 sid;
    struct context context;          // The actual context data
    struct hlist_node list;          // Hash table chaining
    struct rcu_head rcu_head;        // RCU for lockless reads
};

// SID lookup is O(1) average via hash table
// Context → SID is also O(1) via reverse hash

// When a new context is encountered (first exec with new label, etc.):
// 1. Check if context is already in sidtab
// 2. If not, validate the context against policy
// 3. Assign a new SID (atomic counter)
// 4. Insert into sidtab

u32 sidtab_context_to_sid(struct sidtab *s, struct context *context) {
    // Check forward table (context → SID)
    // If found: return existing SID
    // If not: 
    //   new_sid = atomic_inc(&s->next_sid)
    //   entry = alloc sidtab_entry
    //   entry->sid = new_sid
    //   entry->context = *context
    //   insert into hash tables
    //   return new_sid
}
```

### Context Computation on exec()

One of the most complex parts — what context does a process get when it executes a new binary?

```c
// security/selinux/hooks.c
static int selinux_bprm_creds_for_exec(struct linux_binprm *bprm) {
    struct task_security_struct *new_tsec;
    struct inode_security_struct *isec;
    u32 sid, fsid, newsid;
    
    // Current process SID
    sid = current_security()->sid;
    
    // Executable file SID  
    isec = inode_security(bprm->file->f_inode);
    fsid = isec->sid;
    
    // Compute the new SID via type_transition rules
    // This looks up: type_transition <current_type> <exec_type>:process <new_type>
    newsid = security_transition_sid(sid, fsid, SECCLASS_PROCESS, NULL);
    
    // If no transition rule, newsid == sid (stay in same domain)
    
    // Check that the transition is allowed
    if (newsid != sid) {
        // allow current_type new_type:process transition
        avc_has_perm(sid, newsid, SECCLASS_PROCESS, PROCESS__TRANSITION, ...);
        
        // allow current_type exec_type:file entrypoint
        avc_has_perm(newsid, fsid, SECCLASS_FILE, FILE__ENTRYPOINT, ...);
    } else {
        // No transition — check execute permission
        avc_has_perm(sid, fsid, SECCLASS_FILE, FILE__EXECUTE_NO_TRANS, ...);
    }
    
    // Check if setuid/setgid exec changes the SID further
    // (noatsecure, siginh, rlimitinh)
    
    // Update the process's SID for after exec
    new_tsec->sid = newsid;
    new_tsec->osid = sid;  // Save old SID
    
    return 0;
}
```

### Policy Database Internal Structure

```c
// security/selinux/ss/policydb.h (simplified)
struct policydb {
    // Type/class declarations
    struct symtab symtab[SYM_NUM];  // Symbol tables (types, roles, users, etc.)
    
    // Class and permission tables
    struct class_datum **class_val_to_struct;
    struct role_datum **role_val_to_struct;
    struct type_datum **type_val_to_struct;
    
    // Type Enforcement table
    // This is the core data structure for allow rules
    // te_avtab[type_pair] → access vector
    struct avtab te_avtab;
    
    // Conditional (boolean) rules
    struct cond_list *cond_list;
    struct avtab te_cond_avtab;  // Conditional TE rules
    
    // Type transition rules
    struct avtab te_trans;
    
    // Role transition rules
    struct role_trans *role_tr;
    
    // Constraint lists
    // Per-class constraint lists
    
    // MLS information
    struct mls_range initial_range;
    
    // Booleans
    struct cond_bool_datum **bool_val_to_struct;
    int num_decls;
};

// The av_tab (access vector table) uses a hash table
// Key: (source_type, target_type, target_class)
// Value: access_vector (bitmask of allowed permissions)
struct avtab_key {
    u16 source_type;
    u16 target_type;
    u16 target_class;
    u16 specified;      // AV_ALLOW, AV_AUDITALLOW, AV_DONTAUDIT, etc.
};

struct avtab_datum {
    u32 data;  // The permission bitmask
};
```

---

## 21. Network Controls — Netfilter Integration

### Labeled Networking

SELinux can label network packets, enabling MAC on network traffic. Two protocols handle this:

- **CIPSO** (Common IP Security Option) — IPv4
- **CALIPSO** (Common Architecture Label IPv6 Security Option) — IPv6

```c
// Network peer labeling hooks
// security/selinux/hooks.c

static int selinux_socket_sock_rcv_skb(struct sock *sk, struct sk_buff *skb) {
    u32 sk_sid = sk->sk_security->sid;  // Socket's SID
    u32 peer_sid;                        // Remote peer's SID
    
    // Extract CIPSO label from packet
    if (cipso_v4_skbuff_getattr(skb, &secattr) == 0) {
        peer_sid = secattr_to_sid(&secattr);
    } else {
        // No label — use default unlabeled SID
        peer_sid = SECINITSID_UNLABELED;
    }
    
    // Check: can peer_sid send to this socket (sk_sid)?
    return avc_has_perm(peer_sid, sk_sid, 
                         SECCLASS_TCP_SOCKET,
                         TCP_SOCKET__RECV_MSG, ...);
}
```

### NetLabel Policy

```te
# Allow httpd_t to communicate with peers labeled as
# httpd_peer_t (via CIPSO/CALIPSO)

allow httpd_t httpd_peer_t:peer recv;
allow httpd_t self:netlink_tcpdiag_socket { create read write };

# Define what label incoming connections get
netlabelcon 192.168.1.0/24 system_u:object_r:trusted_peer_t:s0;
netlabelcon 10.0.0.0/8 system_u:object_r:internal_net_t:s0;
```

```bash
# Configure NetLabel mappings (runtime)
netlabelctl calipso add pass doi:1
netlabelctl cipsov4 add pass doi:1
netlabelctl map add default address:0.0.0.0/0 protocol:unlabeled
netlabelctl map add default address:192.168.1.0/24 protocol:cipsov4,doi:1
```

### iptables/nftables SELinux Integration

```bash
# SELinux context matching in iptables
iptables -I INPUT -m socket --transparent -j MARK --set-mark 0x1

# nftables secmark
nft add rule ip filter input meta secmark set "httpd_t:http_server_packet_t"
```

```te
# Policy for packet types
type http_server_packet_t;
corenet_packet(http_server_packet_t)

allow httpd_t http_server_packet_t:packet { recv send relabelto };
```

---

## 22. SELinux in Containers

### How Container Engines Use SELinux

```bash
# Podman — automatic MCS label generation
podman run --security-opt label=type:container_t \
           --security-opt label=level:s0:c200,c384 \
           nginx

# Docker
docker run --security-opt label=type:container_t \
           --security-opt label=level:s0:c100,c200 \
           nginx

# Custom type for privileged containers (disable SELinux enforcement)
podman run --security-opt label=disable nginx

# View container's SELinux context
podman inspect <container_id> | grep -i selinux
```

### Container Policy Architecture

```te
# The container policy (simplified from containers-selinux package)

# Container init domain
type container_init_t;
type container_init_exec_t;

# Main container domain
type container_t;
typeattribute container_t svirt_domain;

# Container file type
type container_file_t;

# Container domain transitions
domain_type(container_t)
domain_entry_file(container_t, container_init_exec_t)

# Container can read/write files in container_file_t
# with matching MCS categories
manage_files_pattern(container_t, container_file_t, container_file_t)
manage_dirs_pattern(container_t, container_file_t, container_file_t)

# MCS constraint enforces isolation
# Two containers with different category pairs cannot access each other

# Container network
allow container_t self:tcp_socket create_stream_socket_perms;
allow container_t self:udp_socket create_socket_perms;

# Container cannot access host resources
neverallow container_t host_os_t:file { read write execute };
neverallow container_t kernel_t:system module_request;
neverallow { container_t -container_engine_t } proc_kcore_t:file read;

# sVirt label generation in the container engine
# Each container gets a unique (c_low, c_high) pair
# svirt_lxc_net_t:s0:c200,c384 ← unique to this container
```

### Writing Policies for Custom Container Workloads

```te
# custom_container.te — policy for a custom application container

type custom_container_t;
typeattribute custom_container_t svirt_domain;
typeattribute custom_container_t mcs_constrained_type;

# Can only access files with matching MCS label
manage_files_pattern(custom_container_t, svirt_sandbox_file_t, svirt_sandbox_file_t)

# Network: only HTTP(S)
allow custom_container_t http_port_t:tcp_socket name_connect;
allow custom_container_t http_cache_port_t:tcp_socket name_connect;

# No raw socket access
neverallow custom_container_t self:rawip_socket create;
neverallow custom_container_t self:packet_socket create;

# Cannot use kernel namespaces beyond what container runtime gives
neverallow custom_container_t self:capability { sys_admin net_admin };
```

---

## 23. Troubleshooting Methodology

### Systematic Denial Investigation

```bash
#============================================================
# PHASE 1: Identify the denial
#============================================================

# Live AVC denials
tail -f /var/log/audit/audit.log | grep "avc:"

# Or via journald
journalctl -f | grep "SELinux"

# Get recent denials with context
ausearch -m AVC -ts recent --just-one

#============================================================
# PHASE 2: Understand what's happening
#============================================================

# Decode the denial
ausearch -m AVC -ts recent | audit2why

# Get verbose explanation
ausearch -m AVC -ts recent | sealert -a /dev/stdin

# Check if the file has the right label
ls -Z /path/to/file
stat --printf="%C\n" /path/to/file

# Check if the process has the right label
ps -Z -p <pid>

# Check what label a new file would get
matchpathcon /path/to/file

# Check if restorecon would change the label
restorecon -Rvn /path/to/

#============================================================
# PHASE 3: Determine the fix
#============================================================

# Option A: Relabel the file (if wrong label)
restorecon -Rv /path/to/file

# Option B: Add a file context mapping (persistent)
semanage fcontext -a -t httpd_sys_content_t "/srv/mysite(/.*)?"
restorecon -Rv /srv/mysite/

# Option C: Toggle a boolean (if one exists)
getsebool -a | grep httpd
setsebool -P httpd_can_network_connect on

# Option D: Write a policy module (if custom app)
ausearch -m AVC -c myapp -ts today | audit2allow -M myapp_fix
semodule -i myapp_fix.pp

# Option E: Put domain in permissive mode for dev
semanage permissive -a myapp_t

#============================================================
# PHASE 4: Verify the fix
#============================================================

# Re-run the operation that was failing
# Check that AVC denials are gone
ausearch -m AVC -ts recent | grep myapp
# → No output = fixed

#============================================================
# DEBUGGING TOOLS
#============================================================

# sesearch: query the policy
sesearch --allow -s httpd_t -t shadow_t -c file
# → No output means no allow rule exists

# seinfo: explore policy
seinfo -t httpd_t -x  # all attributes of type
seinfo -a domain -x   # all types with attribute 'domain'
seinfo --class file -x  # permissions in class

# sefcontext_compile: check fc database
sefcontext_compile /etc/selinux/targeted/contexts/files/file_contexts
```

---

## 24. Performance Characteristics and Tuning

### AVC Performance Impact

The AVC achieves near-zero overhead for cached decisions:

```
Without AVC: every syscall → full policy lookup → O(N) rule scan
With AVC:    hit rate ~99%  → hash table lookup → O(1)

Measured overhead on typical workloads: 1-7%
Heavy syscall workloads (e.g., git operations): up to 15%
```

### Tuning the AVC

```bash
# View cache statistics
cat /sys/fs/selinux/avc/cache_stats
# lookups  hits  misses  allocations  reclaims  frees
# 14827102 14818973 8129 8129 7220 7126

# Hit rate: 14818973/14827102 = 99.945%

# Tune AVC cache size (default 512 slots)
echo 1024 > /sys/fs/selinux/avc/cache_threshold
# Higher = more memory, potentially better hit rate
# Default is usually sufficient

# Force AVC flush (debugging only — hurts performance)
echo 1 > /sys/fs/selinux/avc/cache_stats  # resets stats
```

### Dontaudit for Performance

Reducing log noise AND reducing audit subsystem overhead:

```te
# Common dontaudit patterns to reduce overhead
# These are denials that happen constantly but are benign

# Processes reading /proc that they don't need
dontaudit myapp_t proc_t:file { read getattr };
dontaudit myapp_t proc_t:lnk_file { read getattr };

# Checking for setuid capability
dontaudit myapp_t self:capability setuid;

# Checking kernel parameters
dontaudit myapp_t sysctl_t:file read;
dontaudit myapp_t kernel_t:system syslog_read;
```

### Policy Compilation Performance

```bash
# Time a policy compilation
time semodule -B

# For large policy bases:
# - Use modular policy (load only needed modules)
# - Remove debug/development modules
# - Consider targeted policy vs strict policy

# Check loaded modules
semodule -l | wc -l
# Fewer modules = faster compilation = faster policy loads
```

---

## 25. Reference — Complete Permission Tables

### File Class Complete Permissions

| Permission | System Call | Description |
|-----------|-------------|-------------|
| `create` | `open(O_CREAT)`, `mknod` | Create the file |
| `open` | `open()` | Open the file (needed WITH read/write) |
| `read` | `read()`, `pread()` | Read file contents |
| `write` | `write()`, `pwrite()`, `truncate()` | Write to file |
| `append` | `open(O_APPEND)` | Write append-only |
| `execute` | `execve()` | Execute as program |
| `entrypoint` | `execve()` | Use as domain entry |
| `execute_no_trans` | `execve()` | Execute without transition |
| `getattr` | `stat()`, `lstat()`, `access()` | Get file attributes |
| `setattr` | `chmod()`, `chown()`, `utime()` | Set file attributes |
| `lock` | `flock()`, `fcntl(F_SETLK)` | File locking |
| `map` | `mmap()` | Memory-map the file |
| `unlink` | `unlink()`, `remove()` | Delete the file |
| `link` | `link()` | Create hard link |
| `rename` | `rename()` | Rename the file |
| `ioctl` | `ioctl()` | Send ioctl to file |
| `relabelfrom` | `setxattr()` | Change away from this type |
| `relabelto` | `setxattr()` | Change to this type |
| `watch` | `inotify_add_watch()` | Watch for events |
| `audit_access` | | Log access attempts |

### Process Class Complete Permissions

| Permission | Operation |
|-----------|-----------|
| `fork` | `fork()`, `clone()` |
| `transition` | Domain transition on exec |
| `sigchld` | Send SIGCHLD |
| `sigkill` | Send SIGKILL |
| `sigstop` | Send SIGSTOP |
| `signull` | Check process existence (`kill(pid, 0)`) |
| `signal` | Send other signals |
| `ptrace` | `ptrace()` |
| `getsched` | `getpriority()`, `sched_getparam()` |
| `setsched` | `setpriority()`, `sched_setparam()` |
| `getsession` | `getsid()` |
| `getpgid` | `getpgid()` |
| `setpgid` | `setpgid()` |
| `getcap` | `capget()` |
| `setcap` | `capset()` |
| `share` | `clone(CLONE_THREAD)` |
| `getattr` | `/proc/pid` reads |
| `setattr` | Change process label |
| `setexec` | `setexeccon()` |
| `setfscreate` | `setfscreatecon()` |
| `dyntransition` | `setcon()` (dynamic transition) |
| `execmem` | Execute from anonymous memory |
| `execstack` | Execute from stack |
| `execheap` | Execute from heap |
| `noatsecure` | Disable `AT_SECURE` |
| `siginh` | Signal inheritance on exec |
| `rlimitinh` | Rlimit inheritance on exec |

### Constraint Expression Operators

| Operator | Meaning |
|----------|---------|
| `u1 == u2` | Source user equals target user |
| `u1 != u2` | Source user differs from target user |
| `r1 == r2` | Same role |
| `t1 == type` | Source type matches |
| `t2 in { type1 type2 }` | Target type in set |
| `l1 dom l2` | Source level dominates target |
| `l1 domby l2` | Source level dominated by target |
| `l1 eq l2` | Source level equals target |
| `l1 incomp l2` | Levels are incomparable |
| `and` | Boolean AND |
| `or` | Boolean OR |
| `not` | Boolean NOT |

### SELinux Initial SIDs

Initial SIDs are the contexts assigned to kernel objects before policy is loaded:

```
kernel       → The kernel itself
security     → The selinuxfs
unlabeled    → Objects with no security context
fs           → Filesystem-level label
file         → Default file label
file_labels  → File label context
init         → Initial process (PID 1)
any_socket   → Default socket label
port         → Default port label
netif        → Default network interface label
netmsg       → Default network message label
node         → Default network node label
devnull      → /dev/null
```

### Boolean Naming Convention

```
httpd_can_network_connect    → Subject_verb_object
httpd_can_sendmail           → follows "can" pattern for capabilities
httpd_enable_cgi             → "enable" for feature flags
allow_user_exec_content      → "allow" prefix for cross-domain access
use_nfs_home_dirs            → "use" for resource access flags
```

---

## Summary: The Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│                   SELinux Decision Flow                       │
│                                                               │
│  Process (httpd_t) wants to read file (httpd_conf_t)        │
│                          │                                    │
│                    LSM Hook fires                             │
│                          │                                    │
│               ┌──────────▼──────────┐                        │
│               │   AVC Cache Lookup  │                         │
│               │   (ssid, tsid,      │                         │
│               │    class, perms)    │                         │
│               └──────────┬──────────┘                        │
│                  HIT ────┤──── MISS                          │
│                  │       │       │                            │
│              Return   Security   Server                       │
│              cached   lookup in  policydb                     │
│              decision            │                            │
│                          │       │                            │
│                    ┌─────▼───────▼─────┐                     │
│                    │  Check TE rules   │                      │
│                    │  allow httpd_t    │                      │
│                    │  httpd_conf_t:    │                      │
│                    │  file { read }?  │                      │
│                    └─────────┬─────────┘                     │
│                              │                                │
│                    ┌─────────▼─────────┐                     │
│                    │ Check Constraints  │                      │
│                    │ (MLS, RBAC, etc.) │                      │
│                    └─────────┬─────────┘                     │
│                              │                                │
│                    ALLOW ────┴──── DENY                      │
│                      │               │                        │
│                 Proceed         Log to audit                  │
│                 with op         Return -EACCES               │
└─────────────────────────────────────────────────────────────┘
```

**Key principles to internalize:**

1. **Default deny** — everything not explicitly allowed is forbidden
2. **Type is king** — nearly all enforcement is type-to-type
3. **Contexts are labels** — every object in the system has one
4. **AVC makes it fast** — cache hides policy lookup cost
5. **Neverallow is a compile-time invariant** — your strongest guarantee
6. **MCS gives container isolation** — category pairs are the isolation primitive
7. **Constraints layer on top** — even with allow rules, constraints can block
8. **The blast radius is bounded** — a compromised httpd_t cannot escape its type

---

*This document covers SELinux as implemented in Linux kernels 5.x–6.x and Reference Policy 2.x. Policy version 33 (the current standard) is assumed throughout.*

Here's the full guide — ~12,000 words covering every layer of SELinux from kernel internals to policy authoring. Here's what's inside:

**Architecture & Internals**
- Full LSM hook framework — how `selinux_inode_permission()` fires inside `do_open()`, how hooks are registered, the complete call path
- Security Server internals — `policydb`, `sidtab`, `context_struct_compute_av()`, the actual kernel data structures
- AVC architecture — the hash table design, RCU locking for lock-free reads, hit-rate characteristics, invalidation on policy change
- Binary policy format — magic numbers, section layout, version milestones up to v33

**Policy Language**
- Complete `.te`, `.fc`, `.if` module structure with real, production-ready examples
- Every rule type: `allow`, `dontaudit`, `auditallow`, `neverallow`, `type_transition`, `role_transition`, `range_transition`
- Constraint system and `mlsconstrain` — how MLS "no read up / no write down" is enforced even after an allow rule passes
- M4 macro system — how `domtrans_pattern`, `manage_files_pattern`, and the refpolicy macro layer work

**MLS/MCS Deep Dive**
- Bell-LaPadula formalization with policy-language equivalents
- How Podman/Docker generate unique category pairs (up to 523,776 combinations) for container isolation
- Trusted types that bypass MLS constraints

**C & Rust Implementations**
- `getcon`, `getfilecon`, `getpeercon`, `security_compute_av`, context parsing via `context_t`
- A complete SELinux-aware UNIX socket daemon in C with peer context verification
- A userspace object manager using the AVC API directly
- Full Rust async daemon with `SO_PEERSEC` peer authorization, `tokio`-based, proper error types
- A Rust policy analysis CLI using `sesearch`

**Complete References**
- Every `file`, `process`, and `capability` class permission with the corresponding syscall
- Full constraint expression operator table
- Initial SID list
- Decision flow mental model