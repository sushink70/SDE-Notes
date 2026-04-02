# Linux Kernel Security in Cloud and Cloud Native

> A production-oriented guide for engineers who need to understand how Linux kernel security really works, how cloud platforms use it, where the failure modes are, and how to build safer systems in C, Go, and Rust.

---

## How to use this guide

This document is organized from the lowest-level kernel mechanisms upward to cloud-native deployment patterns.

The goal is not to memorize every knob. The goal is to learn the security boundary stack:

1. **Kernel primitives**: credentials, namespaces, cgroups, LSMs, seccomp, capabilities, lockdown, module signing, IMA/EVM, Landlock, no_new_privs.
2. **Kernel engineering reality**: memory safety, concurrency, exploit mitigations, testing, fuzzing, sanitizers, fault injection, Rust in the kernel.
3. **Cloud-native enforcement**: Kubernetes securityContext, Pod Security Standards, user namespaces, RuntimeClass, sandboxed runtimes, admission control, node hardening.
4. **Production code**: how to write kernel-adjacent C, Go cloud policy code, and Rust process isolation code without hand-waving.

---

# 1. Threat model first

A cloud node is not “just another Linux machine.”

It is usually:

- running many tenants with different trust levels,
- carrying secrets, tokens, service accounts, and registry credentials,
- exposed to untrusted container images,
- handling remote code execution via apps, sidecars, jobs, and operators,
- and often managed with declarative control planes that can be accidentally over-permissive.

The kernel is the deepest shared trust anchor on the node. If an attacker gets:

- kernel code execution,
- arbitrary read/write in kernel memory,
- a credential escalation path,
- or a way to bypass the host boundary from a container,

then the entire node and usually all workloads on it are at risk.

In cloud-native environments, the most important boundary is often **not** the VM boundary or the container boundary alone. It is the combination of:

- the container runtime,
- the kernel configuration,
- the LSM policy,
- the seccomp profile,
- the cgroup constraints,
- the user namespace mapping,
- and the admission policy that created the workload.

A secure system is built by stacking these controls so that a bug in one layer does not become a full compromise.

---

# 2. What “Linux kernel security” actually means

Kernel security is not one feature. It is a system.

## 2.1 The kernel must defend against three different classes of problems

### 1. Bugs in the kernel itself
Typical classes:

- use-after-free
- double free
- out-of-bounds read/write
- integer overflow in size calculations
- race conditions
- refcount bugs
- uninitialized memory use
- stale credential / capability checks
- invalid pointer lifetime assumptions

These are the bugs that most commonly become kernel privilege escalations.

### 2. Bugs in userspace that should not become host compromise
Examples:

- a containerized app with RCE
- a tenant escaping a sandbox through a runtime bug
- a compromised sidecar
- a malicious plugin or WASM module
- a CI job running untrusted code

### 3. Misconfiguration
Examples:

- privileged containers
- hostPath mounts
- hostNetwork
- CAP_SYS_ADMIN everywhere
- seccomp disabled
- user namespaces disabled when they could help
- loadable modules not signed
- no kernel lockdown when required
- permissive LSM policy
- writable `/proc` and debugfs exposure on production nodes

Security failures are often configuration failures first, code bugs second.

---

# 3. The Linux kernel security stack

## 3.1 Credentials and identity

The kernel tracks identity through credentials.

Important pieces:

- real UID / GID
- effective UID / GID
- saved IDs
- supplementary groups
- capabilities
- secid / LSM-specific labels
- namespace-relative identity
- file ownership and ACLs

The kernel does not treat “root” as a single magic switch in every context. In practice, root is split into capabilities and policy checks.

That matters because in modern Linux:

- a process can be UID 0 but still lack specific capabilities,
- a process can be privileged inside a user namespace but unprivileged on the host,
- and LSM policy can deny access even when DAC says yes.

## 3.2 Capabilities

Capabilities split root into narrow privileges.

Examples:

- `CAP_NET_ADMIN` for network administration
- `CAP_SYS_ADMIN` as the giant catch-all for many privileged operations
- `CAP_SYS_PTRACE` for inspecting other processes
- `CAP_SYS_MODULE` for kernel module operations
- `CAP_SYS_RAWIO` for very sensitive low-level device access

Production rule: **drop almost everything**. `CAP_SYS_ADMIN` is not a design; it is usually technical debt.

In cloud workloads, you should usually prefer:
- no added capabilities,
- or a tiny, explicit capability set,
- combined with seccomp and LSM restrictions.

## 3.3 Namespaces

Namespaces virtualize global kernel resources.

The important ones for security are:

- **mount namespace**: filesystem view
- **PID namespace**: process tree isolation
- **network namespace**: interfaces, routes, ports, netfilter context
- **UTS namespace**: hostname/domain name
- **IPC namespace**: shared memory, semaphores, message queues
- **user namespace**: UID/GID and capability remapping
- **cgroup namespace**: cgroup view isolation
- **time namespace**: time offsets in specific contexts

Namespaces do not automatically make a sandbox safe. They isolate visibility and some authority, but not all attack surfaces.

Security principle: namespaces are **necessary but not sufficient**.

## 3.4 cgroups

cgroups are resource control, not primarily security control.

They matter for security because they can reduce:

- memory exhaustion attacks,
- CPU starvation,
- fork bombs,
- I/O amplification,
- noisy-neighbor effects,
- and some denial-of-service paths.

cgroup v2 is the unified interface. It is the authoritative model for future changes.

In a cloud node, cgroups are part of containment and reliability. They are not a substitute for privilege separation.

## 3.5 LSMs: Linux Security Modules

LSMs are the mechanism used by SELinux, AppArmor, Smack, Yama, Landlock, IPE, LoadPin, SafeSetID, and similar security policy layers.

There are two different ideas here:

- **DAC**: classic Unix permission checks.
- **MAC**: mandatory policy enforced by the kernel regardless of file ownership.

LSMs are where real security policy is enforced.

Important implications:

- LSM order matters.
- Some LSMs are “major” MAC systems.
- Some are “minor” hardening modules.
- You should not assume a node is secure just because one LSM exists in the kernel; it must be enabled and configured properly.

## 3.6 seccomp

seccomp filters system calls.

This is one of the strongest practical boundaries for containerized workloads because the kernel attack surface is often exercised through syscalls.

seccomp is not a language-level sandbox. It is a syscall filter. That means:

- it can block dangerous syscalls,
- it can constrain arguments in BPF-based filters,
- it can reduce exploitability,
- but it does not understand your application semantics.

Best practice:
- use a restrictive profile,
- start from runtime default,
- then tighten for the workload,
- and use `no_new_privs` unless you truly need privileges.

## 3.7 no_new_privs

`no_new_privs` is an important safety bit.

Once set:
- it persists across fork/clone/exec,
- it cannot be unset,
- and `execve()` cannot grant privilege that wasn’t already available.

This is especially important when using seccomp because unprivileged processes typically need `no_new_privs` to install filters safely.

## 3.8 Lockdown, module signing, IMA/EVM, LoadPin

These are part of the trust chain.

- **Module signing**: only signed modules can be loaded, if enforced.
- **Lockdown**: restricts operations that could modify or introspect the running kernel.
- **IMA/EVM**: integrity measurement and verification for files and metadata.
- **LoadPin**: constrains kernel-loaded files to the same filesystem, usually to support verified immutable roots.

In production, these are relevant when:
- you need stronger host integrity,
- you use Secure Boot,
- you want to reduce kernel tampering,
- and you care about supply-chain and boot-chain compromise.

## 3.9 Landlock

Landlock is a stackable LSM for unprivileged sandboxing of ambient rights like filesystem or network access.

Landlock is particularly attractive for application sandboxing because:
- it is designed to be stacked with existing policy,
- it can be applied by non-root applications,
- and it helps reduce blast radius for buggy or untrusted code.

Landlock is not a replacement for SELinux/AppArmor at the host level. It is a useful extra layer.

---

# 4. What happens in real Linux kernel development

Kernel development has learned a hard lesson over decades:

**memory safety bugs and race bugs are the main exploitation surface.**

The kernel community has responded with several classes of defenses.

## 4.1 Prevent classes of bugs, not just individual bugs

Examples:
- use safer allocation helpers
- use reference counting correctly
- avoid manual size math when helpers exist
- reduce ambiguous ownership
- avoid raw pointer lifetime confusion when possible
- make state transitions explicit
- make invalid states unrepresentable

## 4.2 Detect bugs early

Kernel tooling now includes:

- **KASAN**: out-of-bounds and use-after-free detection
- **KCSAN**: race detection
- **KMSAN**: uninitialized memory use
- **UBSAN**: undefined behavior detection
- **KFENCE**: low-overhead heap bug detection suitable for production kernels
- **lockdep**: locking correctness
- **KUnit**: in-kernel unit tests
- **kselftest**: userspace kernel self-tests
- **fault injection**: deliberately fail allocations, I/O, and other operations
- **KCOV**: coverage for fuzzing

The pattern is simple:
- debug kernels use heavier sanitizers,
- production fleets may use low-overhead detectors like KFENCE,
- and CI should catch what production will not.

## 4.3 Rust in the kernel is a memory-safety strategy, not a magic wand

Rust helps reduce classes of memory corruption bugs by making ownership, borrowing, and lifetimes explicit.

That does **not** solve:
- logic bugs,
- privilege bugs,
- unsafe FFI boundaries,
- race bugs involving shared kernel state,
- or malformed trust assumptions.

Rust is best understood as:
- a strong tool to shrink the unsafe surface,
- not a replacement for kernel security engineering.

---

# 5. Kernel hardening checklist for cloud nodes

This section is intentionally operational.

## 5.1 Boot-chain and host integrity

Strong baseline:
- Secure Boot or an equivalent verified boot flow
- signed kernel modules
- restricted module loading
- kernel lockdown when supported and appropriate
- immutable or measured root filesystem
- minimal base image for nodes
- controlled access to `/boot`, initramfs, and module directories

## 5.2 Kernel command-line and sysctl hygiene

Harden carefully:
- avoid permissive debug settings in production,
- restrict unneeded kernel debug interfaces,
- review `/proc/sys/kernel/*`, `/proc/sys/vm/*`, `/proc/sys/net/*`,
- disable features that expand attack surface if not required,
- keep a known-good baseline in configuration management.

## 5.3 Restrict kernel attack surface

Examples:
- disable unused filesystems and drivers
- reduce module loading where possible
- avoid exposing debugfs on production nodes
- avoid giving pods access to host PID, IPC, or network namespaces unless required
- keep eBPF and tracing access restricted to trusted operators
- limit access to `/dev` and device plugins
- keep `/proc` and `/sys` access under policy, not habit

## 5.4 Use layered isolation

A strong pod boundary often uses:
- user namespace
- dropped capabilities
- seccomp RuntimeDefault or tighter
- AppArmor or SELinux
- readonly root filesystem
- no host namespace sharing
- no privileged flag
- resource limits and quotas
- sandboxed runtime for high-risk workloads

---

# 6. LSMs in depth

## 6.1 Why LSMs matter

Classic Unix permissions are useful but not sufficient.

They do not express:
- which process may execute which binary,
- which paths a process may read/write/open/rename,
- which network or IPC operations are allowed,
- which actions are permitted after a compromise,
- or how to preserve policy across a complex distributed system.

LSMs fill this gap.

## 6.2 SELinux

SELinux is the strongest widely deployed MAC system in many enterprise Linux distributions.

Key ideas:
- labels on subjects and objects
- policy rules decide allowed accesses
- enforcement can be very strong
- mislabeling or weak policy can break systems
- policy design is as important as feature enablement

SELinux is powerful in multi-tenant or regulated environments where you need deterministic policy enforcement.

Trade-off:
- highest policy power,
- highest complexity,
- strongest need for expert operations.

## 6.3 AppArmor

AppArmor is path-based and usually easier to adopt.

Key ideas:
- profile per program or workload
- path-oriented rules
- simpler operational model than SELinux in many environments
- easier to roll out incrementally

Trade-off:
- easier to deploy and reason about,
- generally less expressive than SELinux labels,
- still extremely useful in containers.

## 6.4 Smack

Smack is label-based MAC, often used in embedded or specific security-sensitive environments.

## 6.5 Yama

Yama collects system-wide hardening controls not covered by core DAC.

It is often relevant for:
- ptrace restrictions,
- process introspection hardening,
- and reducing cross-process abuse.

## 6.6 Landlock

Landlock enables applications to apply additional restrictions to themselves.

Use cases:
- untrusted file processing
- plugin sandboxes
- extension systems
- code execution generated at runtime
- per-request ephemeral sandboxes

Landlock is especially interesting in cloud-native systems that execute user-supplied jobs or AI-generated code.

## 6.7 LoadPin, IPE, and integrity controls

These modules are about reducing trust in mutable or attacker-controlled content.

They matter when:
- you want to ensure kernel-loaded files come from a trusted medium,
- you want policy enforcement based on file integrity,
- or you want a layered trust model anchored in a verified root.

---

# 7. Credentials, capabilities, and real privilege boundaries

The danger with capabilities is not that they are bad. The danger is that they are often used like “mini-root” without enough rigor.

## 7.1 Principles

1. Prefer the smallest authority possible.
2. Prefer temporary authority over permanent authority.
3. Tie privilege to one task, one purpose, one operation.
4. Use user namespaces when the privilege is only needed inside a contained environment.
5. Combine privilege with seccomp and MAC policy.

## 7.2 Why `CAP_SYS_ADMIN` is a smell

`CAP_SYS_ADMIN` covers too much.

If you need it, ask:
- can this be broken into a smaller capability?
- can a helper binary do the privileged operation and then exit?
- can user namespaces make the privilege non-host-facing?
- can a different API avoid the capability entirely?

## 7.3 Process credentials are not just IDs

When a task changes identity, the kernel must update:
- effective permissions,
- ambient capabilities,
- LSM state,
- file creation context,
- and namespace-scoped meaning.

A robust system does not rely on one identity field alone.

---

# 8. seccomp in depth

## 8.1 What seccomp is good at

seccomp is best when you already know the syscall surface of the program.

It helps prevent:
- `mount`
- `ptrace`
- dangerous `ioctl`s
- raw socket usage
- kernel module loading paths
- risky process manipulation
- unexpected filesystem escape primitives
- and large classes of exploit chains that need a syscall you can simply remove

## 8.2 What seccomp is not good at

seccomp is not:
- object-level MAC,
- file-level access control,
- a replacement for namespaces,
- a replacement for capabilities,
- a memory safety mechanism,
- or a policy engine that understands your app.

## 8.3 Production workflow for seccomp

1. Start from a default runtime profile.
2. Observe actual syscalls in staging.
3. Tighten the filter to the minimum viable set.
4. Keep a rollback path for legitimate updates.
5. Test with realistic workloads and error paths.
6. Monitor deny events.

## 8.4 Why `no_new_privs` matters

`no_new_privs` protects the privilege boundary around `execve()`.

In practice:
- set it before filter installation,
- set it in wrappers, launchers, and sandbox runners,
- and do not rely on “we probably won’t exec anything dangerous.”

---

# 9. cgroups v2 in security architecture

cgroups are not access control, but they are security-relevant.

## 9.1 Why they matter

They limit:
- memory consumption
- CPU consumption
- PIDs/fork rates
- I/O contention
- pressure on host stability

That means cgroups help contain:
- denial of service,
- noisy neighbor problems,
- and some crash amplification scenarios.

## 9.2 Production use

Use:
- CPU quotas and shares for fair scheduling,
- memory limits with realistic headroom,
- pids limits for fork bombs,
- I/O controls where applicable,
- and consistent pressure metrics in observability.

## 9.3 Security caveat

Resource control is not privilege control.

A process with too much permission but low resources is still dangerous.
A process with few resources but full privilege is still dangerous.
You need both.

---

# 10. Kernel module security

Kernel modules are one of the sharpest edges in the system.

## 10.1 Why modules are risky

A module runs in kernel space.
That means:
- any bug is kernel bug severity,
- unsafe memory access becomes host compromise,
- attack surface expands to the module’s interfaces,
- and unsigned or untrusted modules can become the compromise path.

## 10.2 Production rules

- build as much as possible into the base kernel if stability and trust allow it,
- sign modules,
- restrict module loading,
- audit every device and out-of-tree module,
- avoid unnecessary custom kernel code in production nodes,
- keep module interfaces minimal.

## 10.3 What real-world ops teams learn the hard way

Custom drivers, observability modules, and “temporary” debug modules often become permanent.

Every permanent module is a permanent security obligation.

---

# 11. Secure boot, integrity, and chain of trust

## 11.1 Why this matters

If an attacker can modify:
- the kernel image,
- initramfs,
- modules,
- or early boot config,

then many later controls become cosmetic.

## 11.2 What a robust chain looks like

- firmware trust anchor
- bootloader verification
- kernel image verification
- module signature enforcement
- measured or verified root filesystem
- tamper-evident logs
- node attestation where possible

## 11.3 Integrity versus confidentiality lockdown

Lockdown modes generally harden different classes of kernel interfaces.

Production choice depends on:
- whether the node is a workstation, a server, or a regulated environment,
- whether debugging access is needed,
- and whether the kernel should permit introspective features after boot.

---

# 12. Kernel testing and hardening workflow

## 12.1 Build hardening into CI

For kernel or kernel-adjacent code, CI should include:
- `checkpatch`
- sparse / smatch / coccinelle where applicable
- KUnit
- kselftest
- sanitizer builds
- fault injection builds
- fuzzing where possible
- static analysis and compiler warnings as errors for security-sensitive code

## 12.2 Dynamic tools

- KASAN for memory safety bugs
- KCSAN for race conditions
- KMSAN for uninitialized memory
- UBSAN for undefined behavior
- KFENCE for low-overhead production sampling
- lockdep for locking mistakes
- fault injection for error handling paths

## 12.3 Why error-path testing matters

Many bugs are not in the happy path.

They are in:
- partial allocation failures,
- timeouts,
- retries,
- teardown,
- cancellation,
- device removal,
- and racey shutdown sequences.

Security bugs often hide where developers least want to look: cleanup logic.

---

# 13. Rust in the kernel: what it changes

Rust support in the kernel is real, but scoped.

It is used to:
- reduce memory corruption bugs,
- provide safer abstractions over kernel facilities,
- and make unsafe code more explicit and reviewable.

It does not remove the need for:
- kernel review discipline,
- subsystem knowledge,
- lock correctness,
- and careful API design.

## 13.1 What Rust helps with

- ownership and lifetime tracking
- bounds-checked collections
- safer string handling patterns
- explicit unsafe blocks
- stricter abstraction boundaries

## 13.2 What Rust does not help with by itself

- bad auth logic
- insecure defaults
- privileged interface mistakes
- race conditions in shared state
- wrong LSM assumptions
- wrong seccomp assumptions
- policy misconfiguration

## 13.3 Production lesson

Use Rust to make the dangerous parts small and obvious.

Do not use Rust as an excuse to skip threat modeling.

---

# 14. Cloud-native kernel security

Now the stack becomes operational.

Kubernetes and Linux security are inseparable.

## 14.1 SecurityContext is not optional decoration

Kubernetes securityContext can control:
- runAsUser / runAsGroup
- fsGroup
- allowPrivilegeEscalation
- privileged
- readOnlyRootFilesystem
- capabilities
- seccompProfile
- appArmorProfile
- seLinuxOptions
- host namespace sharing settings

These are your first-line policy knobs.

## 14.2 Pod Security Standards

Pod Security Standards define three broad levels:

- Privileged
- Baseline
- Restricted

In a real production cluster, Restricted should be the default target for most workloads, and exceptions should be explicit, audited, and rare.

## 14.3 User namespaces in Kubernetes

User namespaces are a major improvement when available.

They allow:
- root in the container to map to an unprivileged user on the host,
- reduced host impact if a container escapes,
- and less lateral movement across host files/processes.

This is one of the most important recent developments for container isolation.

## 14.4 RuntimeClass and sandboxed runtimes

For high-risk workloads, use runtime isolation beyond standard containers.

Examples:
- gVisor
- Kata Containers

These provide stronger separation than ordinary runc-style container execution.

Use them for:
- untrusted code execution,
- third-party plugins,
- AI-generated tasks,
- multi-tenant compute,
- and jobs with unclear trust.

## 14.5 The practical stack for a hardened pod

For a normal application pod:

- non-root user
- no privilege escalation
- drop all capabilities
- seccomp RuntimeDefault or tighter
- AppArmor RuntimeDefault or custom
- read-only root filesystem
- no hostPath unless explicitly required
- no hostNetwork unless explicitly required
- no hostPID or hostIPC
- resource requests and limits
- user namespaces when feasible

For untrusted code execution:

- sandbox runtime
- strict network egress policy
- filesystem isolation
- ephemeral workspace
- no service account token unless required
- tight admission policy
- short-lived jobs
- audit logging and quarantine on policy violations

---

# 15. Real-world vulnerability patterns and what they teach

The exact CVE list changes over time, but the patterns do not.

## 15.1 Memory corruption remains the biggest theme

Common exploit classes:
- use-after-free in object lifetimes
- out-of-bounds write through size miscalculation
- dangling references after teardown
- refcount misuse
- partial initialization leading to info leaks
- type confusion via complicated subsystem interfaces

## 15.2 Concurrency bugs are not second-class bugs

Races can become:
- use-after-free,
- stale authorization,
- double free,
- or inconsistent policy enforcement.

Kernel code is extremely concurrent. If you do not reason about locking and memory ordering, you are guessing.

## 15.3 Privilege bugs are often policy bugs

Examples:
- privilege escalation due to incorrect capability check timing
- missing namespace awareness
- confused deputy through helper interfaces
- ambient authority inherited accidentally across exec or fork
- host-facing filesystem or device access from a container

## 15.4 Why exploit mitigations matter

Even when a bug exists, the exploit should be hard.

Mitigations that matter:
- KASLR-like address randomization
- refcount hardening
- safe unlinking and freelist protections
- seccomp restrictions
- lockdown
- LSM policy
- user namespaces
- hardened slab allocators
- low-overhead detection in production

The goal is not “no bugs.”
The goal is “bugs are difficult to turn into host compromise.”

---

# 16. Secure design principles for kernel-adjacent systems

## 16.1 Default deny

If you do not explicitly need an action, deny it.

This applies to:
- syscalls
- capabilities
- file writes
- network egress
- device access
- kernel module loading
- proc/sys access
- feature flags
- and privileged Kubernetes settings

## 16.2 Minimize interface surface

A big API is a big attack surface.

Prefer:
- small message formats,
- fewer ioctls,
- fewer config knobs,
- fewer privileged endpoints,
- fewer side channels,
- and fewer ways to reach the same state.

## 16.3 Make failure safe

A security failure should be:
- denied,
- logged,
- and not silently downgraded.

Fail open is dangerous unless the business requirement is explicit and accepted.

## 16.4 Validate at boundaries

Validate:
- external input
- kernel-user boundary data
- pod manifests
- image provenance
- device parameters
- kernel command line
- node boot options
- and runtime configuration

Never trust the caller to have already validated.

---

# 17. C implementation: vulnerable and secure kernel-adjacent code

The example below is intentionally simplified but realistic.

The vulnerability class is:
- unbounded copy,
- length confusion,
- and bad ownership/validation.

## 17.1 Vulnerable C example

```c
// bad_example.c
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/fs.h>

struct user_req {
    u32 len;
    char data[64];
};

static long bad_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct user_req req;
    char *buf;

    if (copy_from_user(&req, (void __user *)arg, sizeof(req)))
        return -EFAULT;

    // BUG: trusts user length and allocates without strict bounds.
    buf = kmalloc(req.len, GFP_KERNEL);
    if (!buf)
        return -ENOMEM;

    // BUG: copies fixed structure into variable-sized buffer.
    // If req.len < sizeof(req), this is a heap overflow.
    if (copy_from_user(buf, (void __user *)arg, sizeof(req))) {
        kfree(buf);
        return -EFAULT;
    }

    // BUG: missing cleanup on all paths and unclear ownership.
    kfree(buf);
    return 0;
}
```

### Why this is broken

- user-controlled length is not bounded
- copying `sizeof(req)` into `buf` ignores the allocated size
- `copy_from_user()` is used with inconsistent object sizes
- ownership and cleanup are easy to get wrong
- no validation of semantics, only shape

## 17.2 Secure C example

```c
// good_example.c
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/fs.h>
#include <linux/overflow.h>

#define MAX_DATA 64

struct user_req {
    u32 len;
    char data[MAX_DATA];
};

static long good_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct user_req req;
    char *buf;
    size_t alloc_len;

    if (copy_from_user(&req, (void __user *)arg, sizeof(req)))
        return -EFAULT;

    if (req.len == 0 || req.len > MAX_DATA)
        return -EINVAL;

    alloc_len = array_size(req.len, sizeof(char));
    if (check_mul_overflow((size_t)req.len, sizeof(char), &alloc_len))
        return -EOVERFLOW;

    buf = kzalloc(alloc_len, GFP_KERNEL);
    if (!buf)
        return -ENOMEM;

    if (copy_from_user(buf, (void __user *)arg + offsetof(struct user_req, data),
                       req.len)) {
        kfree(buf);
        return -EFAULT;
    }

    /*
     * Use buf under the assumption that req.len bytes are valid.
     * Do not assume user space sent a NUL terminator.
     */

    kfree(buf);
    return 0;
}
```

### Why this is better

- bounds are explicit
- overflow is checked
- zeroed allocation reduces accidental information leakage
- input length is validated before use
- copy size matches allocation size
- error paths are explicit

## 17.3 Production-grade kernel C principles

Use:
- `kzalloc()` or equivalent zeroing helpers when appropriate
- `array_size()` / `struct_size()` / overflow helpers
- `refcount_t` for lifetimes when the object is shared
- `mutex` / `spinlock` / RCU with documented invariants
- `WARN_ON()` only for true invariant violations
- clear teardown paths
- strict pointer ownership rules
- sparse/Smatch/Coccinelle/KUnit/fuzzing for review support

Avoid:
- raw open-coded size math
- custom refcounting unless unavoidable
- hidden global state
- “just trust the user” assumptions
- unclear lock ownership
- allocating before validating inputs when validation is cheap

---

# 18. Go implementation: secure cloud-native policy enforcement

Go is common in cloud control planes, admission controllers, operators, and platform services.

The bad pattern is usually:
- trusting manifests too much,
- allowing privileged containers,
- or silently mutating security controls in the wrong direction.

## 18.1 Vulnerable Go example

This example accepts an arbitrary workload spec and does not enforce security policy.

```go
package main

import (
    "encoding/json"
    "net/http"
)

type PodSpec struct {
    Privileged bool     `json:"privileged"`
    HostNetwork bool    `json:"hostNetwork"`
    CapAdd     []string `json:"capAdd"`
    Seccomp    string   `json:"seccomp"`
}

func unsafeHandler(w http.ResponseWriter, r *http.Request) {
    var spec PodSpec
    if err := json.NewDecoder(r.Body).Decode(&spec); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // BUG: no validation.
    // A caller can request privileged=true, hostNetwork=true, CAP_SYS_ADMIN, etc.
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("accepted"))
}

func main() {
    http.HandleFunc("/admit", unsafeHandler)
    _ = http.ListenAndServe(":8080", nil)
}
```

## 18.2 Secure Go example: admission-style validator

This is a simplified policy validator. In a real controller you would wire it into an admission webhook and use Kubernetes API types.

```go
package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "strings"
)

type SecurityContext struct {
    Privileged               bool     `json:"privileged"`
    AllowPrivilegeEscalation  *bool    `json:"allowPrivilegeEscalation"`
    ReadOnlyRootFilesystem    *bool    `json:"readOnlyRootFilesystem"`
    CapAdd                    []string `json:"capAdd"`
    CapDrop                   []string `json:"capDrop"`
    SeccompProfile            string   `json:"seccompProfile"`
    AppArmorProfile           string   `json:"apparmorProfile"`
    HostNetwork               bool     `json:"hostNetwork"`
    HostPID                   bool     `json:"hostPID"`
    HostIPC                   bool     `json:"hostIPC"`
}

func validate(sc SecurityContext) error {
    if sc.Privileged {
        return errors.New("privileged containers are not allowed")
    }
    if sc.HostNetwork || sc.HostPID || sc.HostIPC {
        return errors.New("host namespace sharing is not allowed")
    }
    if sc.AllowPrivilegeEscalation != nil && *sc.AllowPrivilegeEscalation {
        return errors.New("allowPrivilegeEscalation must be false")
    }
    if sc.ReadOnlyRootFilesystem != nil && !*sc.ReadOnlyRootFilesystem {
        return errors.New("readOnlyRootFilesystem must be true")
    }

    for _, cap := range sc.CapAdd {
        if strings.TrimSpace(cap) != "" {
            return fmt.Errorf("adding capabilities is not allowed: %s", cap)
        }
    }

    if len(sc.CapDrop) == 0 {
        return errors.New("capabilities must explicitly drop ALL")
    }

    if !strings.EqualFold(sc.SeccompProfile, "RuntimeDefault") {
        return errors.New("seccompProfile must be RuntimeDefault")
    }
    if !strings.EqualFold(sc.AppArmorProfile, "RuntimeDefault") {
        return errors.New("AppArmor profile must be RuntimeDefault")
    }

    return nil
}

func admitHandler(w http.ResponseWriter, r *http.Request) {
    var sc SecurityContext
    if err := json.NewDecoder(r.Body).Decode(&sc); err != nil {
        http.Error(w, "invalid JSON: "+err.Error(), http.StatusBadRequest)
        return
    }

    if err := validate(sc); err != nil {
        http.Error(w, err.Error(), http.StatusForbidden)
        return
    }

    w.WriteHeader(http.StatusOK)
    _, _ = w.Write([]byte("admitted"))
}

func main() {
    http.HandleFunc("/admit", admitHandler)
    _ = http.ListenAndServe(":8443", nil)
}
```

## 18.3 Production notes for the Go version

In real systems:
- use typed Kubernetes API objects,
- reject unsafe combinations rather than trying to “fix” them silently,
- log denials with enough context for audit,
- use TLS, authn/z, rate limiting, and request size limits,
- keep the webhook itself locked down with a strict PodSecurity profile,
- and make sure the admission controller is not a single point of failure.

## 18.4 Why this matters in cloud-native security

Most cluster compromises do not require kernel exploitation first.

They start with:
- an over-permissive pod,
- a stolen service account token,
- a writable host mount,
- or a privileged sidecar.

A policy engine written in Go is only useful if it refuses insecure defaults.

---

# 19. Rust implementation: secure process execution and sandbox preparation

Rust is a good fit for cloud agents, sandbox launchers, sidecar controllers, and privileged helpers that must be small and reviewable.

The dangerous pattern is:
- shelling out with untrusted input,
- inheriting too much environment,
- keeping ambient privilege,
- and forgetting to set a hard boundary before `exec`.

## 19.1 Vulnerable Rust example

```rust
use std::process::Command;

fn run_user_command(cmd: &str) {
    // BUG: calling a shell with user input allows shell injection.
    let status = Command::new("sh")
        .arg("-c")
        .arg(cmd)
        .status()
        .expect("failed to execute");

    println!("status: {:?}", status);
}
```

### Why this is broken

- `sh -c` interprets shell metacharacters
- user input becomes code
- environment and PATH may be attacker-influenced
- privilege and filesystem context are unconstrained

## 19.2 Secure Rust example

This version:
- avoids the shell,
- clears inherited environment,
- sets a controlled working directory,
- and sets `no_new_privs` before exec on Linux.

```rust
use std::ffi::OsStr;
use std::os::unix::process::CommandExt;
use std::process::Command;

fn run_safe_program(program: &str, args: &[&str]) -> std::io::Result<()> {
    let mut cmd = Command::new(program);
    cmd.args(args)
        .env_clear()
        .current_dir("/var/empty")
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::inherit())
        .stderr(std::process::Stdio::inherit());

    unsafe {
        cmd.pre_exec(|| {
            // Set no_new_privs so exec cannot gain privilege.
            let ret = libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
            if ret != 0 {
                return Err(std::io::Error::last_os_error());
            }

            // Drop a permissive umask.
            libc::umask(0o077);

            Ok(())
        });
    }

    let status = cmd.status()?;
    if !status.success() {
        return Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("child exited with status: {status}"),
        ));
    }

    Ok(())
}

fn main() -> std::io::Result<()> {
    run_safe_program("/usr/bin/id", &["-u"])
}
```

## 19.3 Production hardening for the Rust version

In a real sandbox runner:
- use an allowlist of executables, not arbitrary paths,
- pin absolute paths,
- optionally set seccomp before exec,
- drop capabilities,
- set up a dedicated UID/GID,
- chroot or pivot_root only if carefully designed,
- use a private mount namespace,
- consider user namespaces for rootless containment,
- bind mount only the minimum filesystem surfaces,
- and log every launched job with a request ID.

## 19.4 Why Rust helps here

Rust prevents several classes of memory bugs in the launcher itself.

But the dangerous part is still policy:
- which binary to run,
- with what environment,
- under what namespace,
- with what seccomp profile,
- and with what filesystem access.

Rust makes the launcher safer.
It does not make the policy correct by itself.

---

# 20. Cloud-native kernel security patterns that work in production

## 20.1 Baseline policy for ordinary application pods

A sensible default posture:

- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities.drop: ["ALL"]`
- `seccompProfile.type: RuntimeDefault`
- AppArmor `RuntimeDefault`
- no host networking
- no host PID
- no host IPC
- no hostPath unless absolutely required
- resource requests and limits
- no privileged containers

## 20.2 Stronger isolation for untrusted code

Add:
- sandbox runtime (`gVisor` or `Kata`)
- user namespaces
- network policy
- short-lived jobs
- ephemeral workspaces
- no service account token unless the code actually needs it
- separate node pools for risky workloads
- node attestation where available

## 20.3 Policy enforcement layers

Use multiple gates:

1. **Admission control** rejects bad pod specs.
2. **Runtime security context** constrains the process.
3. **Node configuration** prevents escape primitives.
4. **LSM policy** blocks file and process access.
5. **seccomp** reduces syscall surface.
6. **Resource limits** prevent abuse.
7. **Observability** detects policy violations.

If one layer fails, another must still stand.

## 20.4 Secrets handling

Treat secrets as one-time exposure objects.

Rules:
- mount only when needed,
- prefer projected volumes over environment variables where feasible,
- never bake secrets into images,
- rotate secrets,
- audit access,
- and keep secret paths out of broad workspace mounts.

---

# 21. Observability and incident response

Security controls are only useful if you can see them.

## 21.1 What to observe

- denied syscalls
- LSM denials
- capability failures
- seccomp violations
- container escapes or near-escapes
- unexpected module load attempts
- kernel warnings tied to a workload
- memory pressure and OOM events
- suspicious restarts and crash loops
- audit events for privileged operations

## 21.2 What to log

For every security-relevant decision, record:
- workload identity
- image digest
- namespace
- node
- runtime class
- security context summary
- deny reason
- timestamp
- request ID / trace ID
- policy version

## 21.3 Operational response

When a workload trips a security policy:
1. quarantine it,
2. preserve logs,
3. check whether the deny was legitimate,
4. review whether the policy is too loose or too strict,
5. and make sure you are not masking a real attack.

---

# 22. Common anti-patterns

## 22.1 “It runs as non-root, so it is safe”

False.

A non-root process can still:
- exploit kernel bugs,
- abuse a dangerous capability,
- read sensitive mounted data,
- poison neighboring services,
- or exfiltrate secrets.

## 22.2 “We use containers, so kernel security is someone else’s problem”

False.

Containers share the kernel unless you use a stronger sandbox or VM boundary.

## 22.3 “seccomp default is enough”

Usually false.

Default is a start, not the finish.

## 22.4 “We disabled hostPath, so we are done”

False.

Privileged pods, host namespaces, device access, service accounts, and permissive capabilities are all separate risks.

## 22.5 “Rust means memory bugs are impossible”

False.

Rust reduces memory unsafety in Rust code, but:
- FFI boundaries remain unsafe,
- logic bugs remain,
- and policy mistakes remain.

---

# 23. Production deployment architecture

## 23.1 Node pools by trust level

Use separate node pools for:
- general app traffic
- admin workloads
- privileged daemons
- GPU or device-plugin workloads
- untrusted code execution
- sandbox runtimes

Do not mix everything on one pool unless risk is very low.

## 23.2 Immutable node strategy

Prefer immutable or strongly managed nodes:
- declarative OS image
- controlled kernel version
- reproducible configuration
- automatic patching windows
- drift detection
- signed updates where possible

## 23.3 Rollout strategy

Kernel and security policy changes should be:
- staged
- observed
- canaried
- and rollback-capable

A broken LSM policy or seccomp profile can take production down just as effectively as a kernel bug.

---

# 24. What to build if you are engineering a new platform

## 24.1 For a new container platform

Build these first:
- admission policy
- default RuntimeClass
- default seccomp profile
- default AppArmor or SELinux policy
- user namespace support
- resource quotas
- node pool segregation
- audit logging

## 24.2 For a sandboxed code execution platform

Add:
- per-job ephemeral identity
- restricted filesystem
- strong egress controls
- no ambient host access
- no inherited credentials
- no broad service account token
- sandbox runtime selection
- strong garbage collection for job artifacts
- post-run cleanup and replayable logs

## 24.3 For kernel or driver development

Require:
- KUnit tests for core logic
- fuzzing on parsers and IO paths
- sanitizers in CI
- static analysis
- fault injection
- strict review for locking and lifetime changes
- security signoff for new privileged interfaces

---

# 25. Minimal reference implementation checklist

When reviewing a kernel-adjacent or cloud-native security feature, ask:

- Does it run with the minimum privilege?
- Is every capability explicit and justified?
- Are user-supplied lengths validated before allocation and copy?
- Are all `copy_from_user` / `copy_to_user` paths bounded?
- Are namespace boundaries intentional?
- Does the container require host access?
- Is `allowPrivilegeEscalation` false?
- Is seccomp enabled?
- Is the LSM profile enforced?
- Is the node protected by module signing and lockdown when needed?
- Is failure closed?
- Are error paths tested?
- Is the design observable in production?
- Is there a rollback path?

If any answer is “no” and the feature is security-sensitive, stop and fix the design.

---

# 26. Exercises

## 26.1 C exercise
Take a character-device ioctl handler and:
- remove unsafe user length handling,
- replace raw allocation math with overflow helpers,
- add explicit ownership rules,
- and write KUnit tests for success/failure paths.

## 26.2 Go exercise
Write an admission webhook that:
- rejects privileged pods,
- enforces RuntimeDefault seccomp,
- requires read-only root filesystem,
- drops all capabilities,
- and emits structured audit logs.

## 26.3 Rust exercise
Write a sandbox launcher that:
- accepts only allowlisted executables,
- clears the environment,
- sets `no_new_privs`,
- mounts a private filesystem namespace,
- and refuses to run if the configured seccomp profile is missing.

Then test what happens when the child tries:
- to exec `/bin/sh`,
- to open `/proc/1/mem`,
- to create a raw socket,
- or to load a kernel module.

---

# 27. References and further reading

Primary sources used to ground this guide:

- Linux kernel documentation: LSM, seccomp, Landlock, no_new_privs, module signing, cgroups v2, kernel self-protection, KASAN, KCSAN, KMSAN, KFENCE, KUnit, Rust, and kernel testing guides.
- Kubernetes documentation: Security Context, Pod Security Standards, Linux kernel security constraints, AppArmor, SELinux, seccomp, RuntimeClass, and user namespaces.
- Google Cloud / GKE documentation for sandboxing untrusted code with gVisor-based isolation.

The live documentation is the source of truth for exact kernel versions, feature status, and Kubernetes API semantics.

---

# 28. Final mental model

Think of the system as a stack:

- **Hardware trust**
- **Boot trust**
- **Kernel integrity**
- **Kernel policy**
- **Namespace isolation**
- **Capability minimization**
- **Syscall filtering**
- **LSM confinement**
- **Resource containment**
- **Runtime sandboxing**
- **Admission policy**
- **Workload identity**
- **Observability**

A production-grade security design does not rely on one of these.

It makes compromise expensive at every layer.

