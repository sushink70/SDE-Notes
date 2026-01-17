**Summary:** You're requesting foundational OS-level isolation and resource control primitives that underpin containerization, virtualization, and modern cloud workloads. I'll cover cgroups (resource limits), namespaces (isolation boundaries), union filesystems (layered storage), process lifecycle (creation to termination), COW (memory optimization), PCB (kernel metadata), context switching (CPU multiplexing), credentials (identity & capabilities), page tables (virtual memory mapping), IPC (inter-process data exchange), and scheduling (CPU allocation). This knowledge directly applies to container runtimes (containerd, CRI-O), Kubernetes kubelet, sandboxing (gVisor, Firecracker), and threat modeling for workload isolation. Focus is on security implications, performance trade-offs, and production failure modes.

---

## 1. cgroups (Control Groups)

**Purpose:** Hierarchical resource accounting, limiting, and prioritization for process groups. Prevents noisy neighbors, ensures QoS, enforces fair-share or strict caps.

**Architecture (v2 unified hierarchy):**
```
/sys/fs/cgroup (unified cgroup2 mount)
├── cgroup.controllers (available: cpu, memory, io, pids)
├── cgroup.subtree_control (enabled controllers for children)
├── user.slice/
│   └── user-1000.slice/
│       └── session-3.scope/
│           ├── memory.max (hard limit)
│           ├── memory.current (usage)
│           ├── cpu.weight (shares, 1-10000)
│           └── pids.max (process count cap)
└── system.slice/
    └── docker-<container-id>.scope/
```

**Key Controllers:**
- **cpu:** Shares (proportional), quota/period (hard cap, e.g., 50ms/100ms = 50% CPU), `cpu.stat` (throttling counters).
- **memory:** `memory.max` (OOM kill if exceeded), `memory.high` (throttle allocations), `memory.swap.max`, `memory.stat` (cache, RSS, slab).
- **io:** Weight-based or latency-target for block I/O, per-device limits (IOPS, BPS).
- **pids:** Cap on fork bombs, prevents resource exhaustion.

**Security & Threat Model:**
- **Escape risk:** Writable cgroup paths from container → attacker can relax own limits or starve sibling cgroups. Mitigation: mount cgroup2 read-only in container, delegate minimal controllers.
- **DoS via resource exhaustion:** Without limits, one container consumes all memory/CPU. Defense: enforce `memory.max`, `pids.max`, CPU quota in production.
- **Visibility:** `memory.stat`, `cpu.stat` leak info about co-located workloads (side-channel). Mitigation: limit `/proc` visibility, use separate cgroup namespaces.

**Trade-offs:**
- **Overhead:** cgroup2 ~1-3% CPU overhead for accounting; v1 had higher lock contention.
- **OOM behavior:** `memory.max` triggers OOM killer (kills processes in cgroup), unpredictable ordering unless `oom_score_adj` tuned.
- **Cgroup v1 vs v2:** v1 allowed per-controller hierarchies (complex); v2 unified hierarchy (cleaner delegation, better scalability).

**Failure Modes:**
- **Memory leak + no limit:** Node OOM, kernel kills random processes.
- **CPU quota too low:** Application starvation, health check timeouts, cascading failures.
- **Nested cgroups misconfiguration:** Parent limit lower than sum of children → unpredictable throttling.

---

## 2. Namespaces

**Purpose:** Isolate global system resources per process group, creating illusion of dedicated OS instance. Foundation of containers.

**Types (7 in Linux):**
1. **PID:** Separate process ID space; PID 1 inside namespace != host PID 1. Init process reaps zombies.
2. **Mount (mnt):** Private filesystem hierarchy, pivot_root to new root. Hides host mounts.
3. **Network (net):** Isolated network stack (interfaces, routing tables, iptables, sockets). veth pairs connect namespaces.
4. **UTS:** Hostname/domainname isolation (cosmetic, but used for identity).
5. **IPC:** Separate SysV IPC objects (message queues, semaphores, shared memory segments).
6. **User:** UID/GID remapping (UID 0 in namespace != root on host). Enables rootless containers.
7. **Cgroup:** Isolates view of `/proc/<pid>/cgroup`, prevents enumeration of sibling cgroups.

**Architecture (Process in Network Namespace):**
```
Host Network Namespace
├── eth0 (10.0.0.5/24)
└── veth0 (169.254.1.1) <──┐
                            │ veth pair
Container Net Namespace    │
├── eth0 (veth1, 10.244.1.2/24) <──┘
├── lo (127.0.0.1)
└── iptables (isolated rules)
```

**Creation Flow:**
1. `clone(CLONE_NEWPID | CLONE_NEWNET | ...)` → child in new namespaces.
2. `unshare()` → move calling process to new namespace.
3. `setns(fd, CLONE_NEWNET)` → join existing namespace (via `/proc/<pid>/ns/net`).

**Security & Threat Model:**
- **Namespace escape:** Bugs in kernel namespace code (CVE-2022-0492: cgroup v1 release_agent escape). Mitigation: seccomp-bpf to block dangerous syscalls, LSM (AppArmor/SELinux), keep kernel patched.
- **User namespace risks:** UID 0 in user NS has capabilities scoped to that NS, but kernel vulnerabilities (e.g., privilege escalation via `CAP_SYS_ADMIN` in user NS) can break out. Mitigation: disable user namespaces (`kernel.unprivileged_userns_clone=0`) or use nested user NS carefully.
- **PID namespace exhaustion:** Fork bomb inside container can fill PID namespace (default 32k PIDs). Mitigation: `pids.max` in cgroup.
- **Mount namespace leaks:** Shared mount propagation (MS_SHARED) can propagate mounts back to host. Mitigation: use MS_PRIVATE or MS_SLAVE.

**Trade-offs:**
- **Overhead:** Negligible CPU, but network namespaces add veth latency (~50-100ns per hop), iptables/netfilter processing.
- **Debugging:** strace, perf, debuggers must attach via `nsenter` or `/proc/<pid>/ns/*`.
- **Shared kernel:** All namespaces share one kernel; kernel exploit = full host compromise. Alternative: VM-based isolation (Firecracker, gVisor for syscall filtering).

**Failure Modes:**
- **PID namespace leak:** Process in init NS holds FD to pid namespace → NS persists after container exit, leaks resources.
- **Network namespace without veth:** Container isolated but no connectivity; must explicitly create veth pair + bridge.

---

## 3. Union Filesystems (Overlay2, AUFS, VFS)

**Purpose:** Layered, copy-on-write filesystem for container images. Base image read-only, changes in ephemeral upper layer. Saves disk space, accelerates image pulls.

**Architecture (OverlayFS):**
```
Container Root FS (merged view)
├── /bin, /lib, /etc (from lower layers)
├── /tmp, /var (from upper layer, writable)

Layers on Disk:
/var/lib/docker/overlay2/
├── <layer-id1>/diff/  (base OS, e.g., Ubuntu)
├── <layer-id2>/diff/  (application binaries)
├── <layer-id3>/diff/  (config files)
└── <container-id>/
    ├── diff/      (upper: writable layer)
    ├── work/      (OverlayFS internal scratch)
    └── merged/    (union mount point)
```

**Mount (conceptual):**
```
mount -t overlay overlay \
  -o lowerdir=<layer1>:<layer2>:<layer3>,\
     upperdir=<upper>,workdir=<work> \
  <merged>
```

**Copy-on-Write Behavior:**
- **Read:** File in lower layer → served directly (no copy).
- **Modify:** File copied to upper layer (COW), changes isolated.
- **Delete:** Whiteout file (`c 0 0` char device) created in upper, hides lower file.

**Security & Threat Model:**
- **Layer tampering:** Attacker modifies image layer on disk → all containers using that layer compromised. Mitigation: image signing (Docker Content Trust, Notary v2), read-only lower layers, integrity checks (dm-verity).
- **Information leak via layers:** Secrets in intermediate layer (even if deleted in top layer) persist in image. Mitigation: multi-stage builds, never commit secrets to layers.
- **Filesystem vulnerabilities:** OverlayFS bugs (CVE-2021-3732: privilege escalation via crafted xattrs). Mitigation: kernel updates, consider alternatives (ZFS, Btrfs with snapshots).
- **Whiteout bypass:** Incorrect whiteout handling → deleted files visible. Rare but check overlay2 driver version.

**Trade-offs:**
- **Performance:** OverlayFS read ~native speed; writes incur COW penalty (first write to file copies entire file). Large file modifications expensive.
- **Inode exhaustion:** Each layer consumes inodes; many layers → inode pressure on host. Mitigation: limit image layers (< 20-30), use modern FS (XFS with large inode counts).
- **Portability:** OverlayFS Linux-only; macOS/Windows use VMs with bind mounts or osxfs/WSL2 translation layers.

**Alternatives:**
- **Device Mapper (devicemapper):** Block-level COW, slower, deprecated in Docker.
- **Btrfs/ZFS snapshots:** Native COW at FS level, but require dedicated Btrfs/ZFS pool.
- **VFS (legacy):** Full copy per layer, no sharing, simple but wasteful.

**Failure Modes:**
- **Disk full in upper layer:** Container writes fail, application crashes. Mitigation: monitor `/var/lib/docker` space, set container disk quotas (XFS project quotas).
- **Work directory corruption:** OverlayFS work dir corrupted (power loss) → mount fails. Mitigation: recreate work dir, fsck.

---

## 4. Process Lifecycle

**Stages:**
1. **Creation:** Parent calls `fork()` (copy address space) or `clone()` (share resources, create threads/namespaces).
2. **Execution:** `execve()` replaces process image with new binary, resets stack/heap, loads ELF.
3. **Running:** Scheduled by kernel, executes in user mode, switches to kernel mode for syscalls.
4. **Waiting:** Blocked on I/O, lock, or explicitly (`wait()`, `pause()`). State: TASK_INTERRUPTIBLE or TASK_UNINTERRUPTIBLE.
5. **Termination:** `exit()` or signal (SIGTERM, SIGKILL). Kernel releases resources, stores exit status.
6. **Zombie:** Process exited but parent hasn't called `wait()` → PCB remains, PID occupied.
7. **Reaping:** Parent calls `wait()`/`waitpid()` → kernel removes zombie PCB.

**State Diagram:**
```
   fork()
     ↓
  CREATED → READY → RUNNING ⇄ BLOCKED (I/O, lock)
              ↑        ↓
              └─ PREEMPTED (timer interrupt)
                       ↓
                    EXIT → ZOMBIE → [wait()] → DEAD
```

**Security Implications:**
- **TOCTOU (Time-of-Check-Time-of-Use):** Between `fork()` and `execve()`, attacker can race to modify executable. Mitigation: `O_CLOEXEC`, `execveat()` with fd.
- **Zombie accumulation:** Init (PID 1) in container doesn't reap zombies (not written as proper init) → PID exhaustion. Mitigation: use `tini`, `dumb-init`, or systemd in container.
- **exec vulnerabilities:** Execve with unsanitized env vars (`LD_PRELOAD`, `PATH`) → privilege escalation. Mitigation: drop privileges before exec, sanitize env.

**Failure Modes:**
- **Fork bomb:** `while :; do $0 & done` → exponential process creation, PID exhaustion. Defense: `pids.max` in cgroup.
- **Orphan processes:** Parent dies before child → child reparented to init. If init doesn't reap → zombie accumulation.

---

## 5. Copy-on-Write (COW)

**Purpose:** Optimize memory usage by sharing pages until modification. Used in `fork()`, virtual memory, filesystems.

**Mechanism (fork):**
1. Parent calls `fork()` → kernel creates child PCB, copies page tables (not pages).
2. All pages marked read-only, PTEs (page table entries) point to same physical pages.
3. Parent or child writes to page → page fault (write to read-only page).
4. Kernel allocates new physical page, copies content, updates faulting process's PTE.
5. Both processes now have independent copies of that page.

**Architecture:**
```
Before fork():
Parent VA 0x1000 → PTE → Physical Page A (RW)

After fork():
Parent VA 0x1000 → PTE (RO) → Physical Page A
Child  VA 0x1000 → PTE (RO) → Physical Page A

After write to 0x1000 in child:
Parent VA 0x1000 → PTE (RW) → Physical Page A
Child  VA 0x1000 → PTE (RW) → Physical Page B (new copy)
```

**Security & Threat Model:**
- **COW side-channels:** Timing differences between first write (page fault + copy) vs subsequent writes leak information (e.g., which pages were modified). Relevant in SGX, VMs.
- **Meltdown/Spectre implications:** COW pages can be speculatively accessed before permission checks, leaking data. Mitigation: KPTI, retpoline.
- **Double-fetch bugs:** Kernel reads userspace page, page COW'd by another thread, kernel re-reads → inconsistent data. Mitigation: copy_from_user once, validate.

**Trade-offs:**
- **Memory savings:** Fork of 1GB process only copies page tables (~4MB), not data, until written.
- **Latency:** First write to COW page incurs page fault (~1-10µs), may cause jitter in latency-sensitive apps.
- **THP (Transparent Huge Pages):** 2MB pages reduce TLB misses but COW of 2MB page copies entire 2MB (vs 4KB). Mitigation: disable THP for COW-heavy workloads.

**Alternatives:**
- **vfork():** Child shares address space, parent blocks until exec. Faster but risky (child can corrupt parent).
- **posix_spawn():** No intermediate fork+exec, kernel directly spawns. Used in performance-critical code.

---

## 6. Process Control Block (PCB) / task_struct

**Purpose:** Kernel data structure holding all metadata for a process. Scheduler, memory manager, and signal handling all reference PCB.

**Key Fields (Linux `task_struct`):**
- **Identity:** PID, TGID (thread group ID), parent PID, namespace pointers.
- **State:** TASK_RUNNING, TASK_INTERRUPTIBLE, TASK_UNINTERRUPTIBLE, TASK_STOPPED, TASK_ZOMBIE.
- **Scheduling:** Priority (nice, real-time policy), CPU affinity, vruntime (CFS), timeslice.
- **Memory:** `mm_struct` pointer (page tables, VMA list), RSS, heap/stack bounds.
- **Credentials:** UID, GID, supplementary groups, capabilities, seccomp filter, LSM contexts.
- **File Descriptors:** `files_struct` → fd table → `file` objects.
- **Signals:** Pending signals bitmask, signal handlers (`sigaction`).
- **Namespaces:** Pointers to 7 namespace structs (PID, mnt, net, etc.).
- **Cgroup:** Pointer to cgroup hierarchy.

**Allocation:**
- PCB allocated from kernel slab cache (`task_struct` ~4KB).
- Kernel stack (8KB on x86_64, 16KB on some archs) per process.

**Security Implications:**
- **PCB corruption:** Kernel vulnerability overwrites PCB → privilege escalation, arbitrary code exec. Examples: CVE-2016-5195 (Dirty COW), CVE-2017-5123 (waitid).
- **Credential bypasses:** Bugs in UID/GID checks → unauthorized access. Mitigation: capability-based security (drop unneeded `CAP_*`).
- **Information leak:** `/proc/<pid>/stat`, `/proc/<pid>/maps` expose PCB fields. Mitigation: `hidepid=2` mount option for `/proc`.

**Failure Modes:**
- **Kernel stack overflow:** Deep recursion or large stack variables → overwrite PCB, kernel panic. Mitigation: stack canaries (CONFIG_CC_STACKPROTECTOR), VMAP_STACK.
- **Task struct exhaustion:** Each process consumes memory for PCB + kernel stack; fork bomb can OOM kernel. Defense: `pids.max`.

---

## 7. Context Switching

**Purpose:** Save state of current process, load state of next process. Enables CPU time-sharing among processes.

**Mechanism (high-level):**
1. **Trigger:** Timer interrupt (preemption) or syscall (voluntary, e.g., `read()` blocks).
2. **Save state:** Kernel saves CPU registers (PC, SP, general-purpose regs) to current PCB.
3. **Select next:** Scheduler picks next runnable process (e.g., CFS chooses lowest vruntime).
4. **Load state:** Kernel restores next process's registers from its PCB.
5. **TLB flush:** If page tables differ (different `mm_struct`), flush TLB or use ASID/PCID to avoid full flush.
6. **Resume:** Jump to next process's saved PC, execute in user mode.

**Flow:**
```
Process A (user mode)
  ↓ timer interrupt or syscall
Kernel (save A's regs to A's PCB)
  ↓
Scheduler (pick B)
  ↓
Kernel (load B's regs from B's PCB, switch page tables)
  ↓
Process B (user mode)
```

**Costs:**
- **Direct:** Save/restore registers (~100-1000 cycles), TLB flush (expensive, ~1000-5000 cycles if no PCID).
- **Indirect:** Cache pollution (A's cache lines evicted, B's cache cold), CPU pipeline flush.

**Measurement:** Context switch rate via `/proc/stat` (field `ctxt`). High rate (>10k/sec) → thrashing, scheduler overhead.

**Security & Threat Model:**
- **Spectre v2 (Branch Target Injection):** Attacker process poisons branch predictor, victim process (after context switch) speculatively executes attacker's gadgets, leaks data. Mitigation: retpoline, IBPB (flush branch predictor on context switch), STIBP (isolate sibling HT cores).
- **Lazy FPU restore:** Old CPUs didn't save FPU state on switch → attacker could read victim's FPU registers. Mitigation: XSAVES/XRSTORS (modern CPUs), eager FPU save.
- **TLB poisoning:** Kernel bug allows attacker to insert PTE in victim's TLB during switch → read victim's memory. Rare but catastrophic.

**Trade-offs:**
- **Voluntary vs preemptive:** Voluntary (process yields) → lower overhead, but uncooperative process starves others. Preemptive (timer) → fairness, but interrupt overhead.
- **Thread vs process switch:** Thread switch same `mm_struct` → no TLB flush, cheaper (~50% cost of process switch).

**Optimization:**
- **PCID (Process Context ID):** Tags TLB entries with address space ID → avoid full flush on switch (x86_64).
- **Affinity:** Pin processes to CPUs → hot cache, fewer switches.

**Failure Modes:**
- **High context switch rate:** >50k/sec → CPU saturated by scheduler, low throughput. Cause: too many threads, inefficient I/O (many blocking syscalls).
- **Priority inversion:** High-priority process blocked waiting for low-priority process holding lock → system unresponsive. Mitigation: priority inheritance (RT scheduler).

---

## 8. Process Credentials

**Purpose:** Define identity and privileges (UID, GID, capabilities, LSM labels). Kernel enforces access control based on credentials.

**Components:**
- **Real UID/GID:** UID of user who started process. Immutable after `setuid()` (unless root).
- **Effective UID/GID:** UID used for permission checks. Can differ from real (setuid binaries).
- **Saved UID/GID:** Backup of effective UID, allows unprivileged process to drop privileges and restore later.
- **Filesystem UID/GID:** Linux-specific, used for filesystem ops. Usually equals effective UID.
- **Supplementary GIDs:** Additional group memberships (e.g., `docker` group).
- **Capabilities:** Fine-grained privileges (e.g., `CAP_NET_ADMIN`, `CAP_SYS_ADMIN`). Split from root (UID 0).
- **LSM (SELinux, AppArmor):** Mandatory Access Control labels, overrides DAC (discretionary access control).
- **Seccomp:** Syscall filter, blocks dangerous syscalls per-process.

**Architecture:**
```
task_struct → cred (credentials struct)
              ├── uid, gid (real)
              ├── euid, egid (effective)
              ├── suid, sgid (saved)
              ├── fsuid, fsgid
              ├── cap_effective, cap_permitted, cap_inheritable (bitmasks)
              ├── selinux_context
              └── seccomp_filter
```

**Capability Model:**
- **cap_permitted:** Capabilities process can use (superset).
- **cap_effective:** Currently active capabilities (used for checks).
- **cap_inheritable:** Capabilities preserved across `execve()` (if file has matching inheritable).

**Security & Threat Model:**
- **Capability-based attacks:** Process with `CAP_SYS_ADMIN` (overpowered, ~root) can disable seccomp, load kernel modules, etc. Mitigation: drop `CAP_SYS_ADMIN`, use `CAP_NET_ADMIN`, `CAP_SYS_PTRACE`, etc. only as needed.
- **UID 0 bypass:** Even without capabilities, UID 0 has implicit privileges (e.g., override ownership checks). Mitigation: user namespaces (UID 0 in NS != host root).
- **Setuid binaries:** If setuid binary has vuln (buffer overflow), attacker gains elevated UID. Mitigation: minimize setuid binaries, use capabilities instead (setcap).
- **Ambient capabilities:** Linux 4.3+, ambient caps inherited across `execve()` without requiring file caps. Risk: process accidentally retains caps after exec. Mitigation: drop ambient caps after privilege drop.

**Trade-offs:**
- **Granularity vs complexity:** 40+ capabilities; fine-grained but hard to audit. Alternative: SELinux type enforcement (more expressive).
- **Performance:** Capability checks negligible (<10ns). Seccomp-bpf adds ~1-2µs per syscall.

**Failure Modes:**
- **Privilege drop failure:** Process calls `setuid(non-root)` but forgets to check return value (fails silently on error) → still running as root. Mitigation: always check `setuid()` return.
- **Capability leak:** Library or child process inherits unneeded caps. Mitigation: explicitly drop caps, use `PR_SET_NO_NEW_PRIVS`.

---

## 9. Page Tables

**Purpose:** Map virtual addresses (VA) to physical addresses (PA). Enable address space isolation, memory protection, demand paging.

**Structure (x86_64 4-level paging):**
```
Virtual Address (64-bit, 48-bit used):
[PML4 index (9b)] [PDP index (9b)] [PD index (9b)] [PT index (9b)] [Offset (12b)]

Page Table Hierarchy:
CR3 (page table base register)
 ↓
PML4 (512 entries) → PML4E
 ↓
PDP (512 entries)  → PDPE
 ↓
PD (512 entries)   → PDE
 ↓
PT (512 entries)   → PTE → Physical Page (4KB)
```

**Each PTE (64-bit) contains:**
- Physical page frame number (PFN): Bits 12-51 → 4KB-aligned PA.
- Flags: Present (P), Writable (W), User (U), Accessed (A), Dirty (D), NX (No-eXecute), etc.

**Translation (MMU):**
1. CPU issues VA → MMU walks page tables (4 memory accesses in worst case).
2. TLB (Translation Lookaside Buffer) caches VA→PA mappings → hit avoids walk (~99% hit rate).
3. PTE flags checked (e.g., U bit → user can access, W bit → writable).
4. Page fault if PTE not present, not writable (COW), or NX violation.

**Security & Threat Model:**
- **Page table injection:** Attacker overwrites PTE → arbitrary PA access. Mitigation: W^X (write xor execute), SMAP (Supervisor Mode Access Prevention, kernel can't access user pages without explicit flag).
- **Rowhammer:** Bit flips in DRAM corrupt PTEs → privilege escalation (flip U bit → user accesses kernel page). Mitigation: ECC memory, Target Row Refresh (TRR), kernel page table isolation (KPTI).
- **Meltdown:** Speculative execution allows userspace to read kernel PTEs before permission check. Mitigation: KPTI (separate kernel/user page tables, flush on syscall).
- **TLB side-channels:** TLB timing leaks which pages were accessed. Relevant in VMs (cloud), SGX.

**Trade-offs:**
- **Memory overhead:** 4-level paging → ~0.2% of VA space consumed by page tables. 5-level (for 57-bit VA) → more overhead.
- **TLB miss cost:** 4 memory accesses + cache misses → 50-200ns. Huge pages (2MB/1GB) reduce TLB pressure.
- **Huge pages (THP):** 2MB pages → fewer TLB entries, but COW copies 2MB (not 4KB), fragmentation issues.

**Failure Modes:**
- **TLB shootdown storm:** Process unmaps pages on CPU A → must IPI (inter-processor interrupt) all CPUs to flush TLB → expensive. Many processes unmapping → CPU stall.
- **Page table corruption:** Kernel bug writes invalid PTE → page fault in kernel → panic.

---

## 10. Inter-Process Communication (IPC)

**Purpose:** Processes exchange data, synchronize. Essential for microservices, sandboxing, privilege separation.

**Mechanisms:**
1. **Pipes / FIFOs:** Unidirectional byte stream. Pipe (anonymous, `pipe()`), FIFO (named, filesystem). Kernel buffered (~64KB).
2. **Unix Domain Sockets (UDS):** Bidirectional, connection-oriented (SOCK_STREAM) or datagram (SOCK_DGRAM). SCM_RIGHTS passes file descriptors.
3. **Shared Memory:** Fastest IPC. Multiple processes map same physical pages (mmap, shm_open). No kernel involvement for data transfer. Requires synchronization (futex, semaphore).
4. **Message Queues:** Typed messages, priority, blocking/non-blocking (POSIX mq_send/mq_recv, older SysV msgget).
5. **Signals:** Asynchronous notifications (SIGTERM, SIGUSR1). Limited data (signal number). Race-prone.
6. **Semaphores:** Synchronization primitive (mutex, counting). SysV (`semget`) or POSIX (`sem_open`).
7. **Memory-Mapped Files:** File backed shared memory. Persistence, simpler than anonymous shm.
8. **D-Bus:** High-level IPC for system services (Linux desktop, systemd). Method calls, signals, properties.

**Architecture (UDS + Shared Memory):**
```
Process A                 Process B
  ↓                         ↓
UDS (control channel)     UDS
  |                         |
  └─ send FD (SCM_RIGHTS) ─→ recv FD
                             ↓
                        mmap(FD) → Shared Memory Segment
                             ↓
Process A writes        Process B reads (zero-copy)
```

**Security & Threat Model:**
- **TOCTOU in shared memory:** A writes data, B reads, A modifies after B's check → inconsistent state. Mitigation: use futex/mutex, atomic ops.
- **Signal races:** Async signals interrupt syscalls, handlers can corrupt state if not async-signal-safe. Mitigation: signalfd (convert signal to fd), sigprocmask (block signals during critical sections).
- **FD passing attacks:** Malicious process passes FD to sensitive file (e.g., `/etc/shadow`) via SCM_RIGHTS. Mitigation: check creds with `SO_PEERCRED`, LSM hooks.
- **Shared memory leaks:** Process dies without unmapping → segment persists (`ipcs` shows it). Mitigation: use POSIX shm with `shm_unlink()`, auto-cleanup on process exit.
- **D-Bus policy bypass:** Misconfigured policy allows unprivileged process to call privileged method. Mitigation: strict D-Bus policy, least-privilege.

**Trade-offs (Latency & Bandwidth):**
- **Pipes/UDS:** ~1-2µs latency, ~10-20GB/s bandwidth (memory copy).
- **Shared memory:** ~100ns latency (memory access), ~50-100GB/s (limited by memcpy, cache). Zero-copy if properly aligned.
- **Message queues:** Higher overhead (~5-10µs), kernel-managed, persistent.

**Failure Modes:**
- **Pipe deadlock:** Writer blocks when buffer full, reader doesn't read → deadlock. Mitigation: non-blocking I/O, select/poll.
- **Shared memory corruption:** Two processes write same location without lock → race, corrupted data. Mitigation: use futex-based mutexes (glibc pthread_mutex).
- **Signal loss:** Pending signals coalesced (multiple SIGUSRs delivered as one). Mitigation: use signalfd or self-pipe trick.

---

## 11. Scheduling

**Purpose:** Decide which process runs on which CPU, for how long. Goals: fairness, throughput, latency, energy efficiency.

**Linux Scheduler Classes (priority order):**
1. **SCHED_DEADLINE:** Earliest Deadline First (EDF), hard real-time. Process specifies runtime/period (e.g., 10ms/100ms). Kernel guarantees deadline if schedulable.
2. **SCHED_FIFO / SCHED_RR:** Real-time, priority-based. FIFO (runs until blocks), RR (round-robin with timeslice). Priorities 1-99 (higher = more urgent).
3. **SCHED_OTHER (CFS - Completely Fair Scheduler):** Default for normal processes. O(log n) complexity, red-black tree of runnable tasks sorted by vruntime (virtual runtime).
4. **SCHED_BATCH:** Throughput-optimized, longer timeslices, lower preemption.
5. **SCHED_IDLE:** Lowest priority, runs only if no other tasks.

**CFS Internals:**
- **vruntime:** Accumulated CPU time weighted by priority (nice -20 → 1/2 vruntime of nice 0). Task with lowest vruntime picked next.
- **Timeslice:** Dynamic, based on number of tasks and latency target (default ~6ms). More tasks → shorter slices.
- **Load balancing:** Periodic (every tick) and on idle. Migrates tasks across CPUs to balance load, respects CPU affinity.

**Architecture:**
```
Per-CPU Run Queue
├── CFS rb-tree (sorted by vruntime)
│   ├── Task A (vruntime=100ms)
│   ├── Task B (vruntime=105ms)
│   └── Task C (vruntime=110ms)
├── RT queue (FIFO/RR, priority 50)
│   └── Task D
└── DEADLINE queue
    └── Task E (10ms/100ms)

Scheduler picks: Task E (DEADLINE) → Task D (RT) → Task A (CFS, lowest vruntime)
```

**Security & Threat Model:**
- **CPU pinning denial-of-service:** Attacker pins many tasks to one CPU → that CPU overloaded, others idle. Mitigation: limit CPU affinity via cgroup `cpuset.cpus`.
- **Priority escalation:** Process sets RT priority without `CAP_SYS_NICE` → scheduler rejects. Mitigation: limit via `ulimit -e` (RLIMIT_RTPRIO) or cgroup cpu.rt_runtime_us (RT bandwidth cap).
- **Scheduler side-channels:** Cache/TLB state after task switch leaks info about previous task. Relevant in cloud (co-located VMs).

**Trade-offs:**
- **Fairness vs latency:** CFS optimizes fairness (all tasks get proportional CPU over time), but latency-sensitive tasks (interactive) may suffer. Mitigation: lower nice value for latency-sensitive tasks, or use SCHED_DEADLINE.
- **Context switch overhead:** More CPUs, more tasks → higher migration cost. Mitigation: affinity, isolcpus (dedicate CPUs to specific tasks).
- **Real-time guarantees:** SCHED_DEADLINE provides hard deadlines, but requires careful analysis (admission control, EDF schedulability test). Misconfiguration → deadline miss, system instability.

**Failure Modes:**
- **RT throttling:** RT tasks consume >95% CPU (default `sched_rt_runtime_us=950000`, `sched_rt_period_us=1000000`) → kernel throttles RT tasks to prevent starvation of CFS. Result: deadline miss.
- **Load balancer thrashing:** Many short-lived tasks, load balancer constantly migrates → high overhead, cache pollution.
- **Priority inversion (CFS):** High-priority task waits for lock held by low-priority task. CFS doesn't have priority inheritance. Mitigation: use RT scheduler or design lock-free.

---

## Threat Model Summary

**Isolation Boundaries:**
- **Namespaces:** Strongest isolation (separate PID, net, mnt), but shared kernel.
- **cgroups:** Resource limits, not isolation. Attacker can detect/influence sibling cgroups if permissions wrong.
- **User namespaces:** UID 0 in NS != root on host, but kernel vulns can escape. Pair with seccomp, LSM.

**Attack Vectors:**
1. **Kernel exploits:** All containers share kernel; CVE in kernel → full host compromise. Defense: minimal attack surface (seccomp), kernel hardening (KASLR, SMEP, SMAP), keep patched.
2. **Resource exhaustion:** No cgroup limits → DoS. Defense: enforce memory.max, pids.max, cpu.max.
3. **IPC side-channels:** Shared memory, signals leak timing info. Defense: isolate untrusted processes, use separate namespaces.
4. **Credential attacks:** Misconfigured capabilities, setuid → privilege escalation. Defense: drop all caps except required, no setuid in container.

**Defense-in-Depth:**
- Layer 1: Namespaces (isolation)
- Layer 2: cgroups (resource limits)
- Layer 3: Capabilities (privilege restriction)
- Layer 4: Seccomp-bpf (syscall filtering)
- Layer 5: LSM (mandatory access control)
- Layer 6: Userspace sandbox (gVisor, Firecracker for VM-level isolation)

---

## References

1. **Linux Kernel Docs:**
   - cgroups: `Documentation/admin-guide/cgroup-v2.rst` (kernel.org)
   - namespaces: `man 7 namespaces`, `man 2 clone`
   - credentials: `man 7 capabilities`, `Documentation/security/credentials.rst`

2. **Books:**
   - *Linux Kernel Development* (Robert Love): Process model, scheduling, IPC.
   - *Understanding the Linux Kernel* (Bovet & Cesati): Memory management, page tables, context switching.
   - *The Linux Programming Interface* (Michael Kerrisk): Comprehensive IPC, process model.

3. **Papers:**
   - "Analysis of the Linux CPU Scheduler" (CFS internals): research.google/pubs/pub43438/
   - "Meltdown" (page table vulnerabilities): meltdownattack.com

4. **Security:**
   - Seccomp guide: `Documentation/userspace-api/seccomp_filter.rst`
   - Container security best practices: CIS Benchmarks (Docker, Kubernetes)
   - CVE databases: NVD (nvd.nist.gov), Linux kernel CVEs

5. **Tools for verification:**
   - cgroup inspection: `systemd-cgls`, `cat /proc/<pid>/cgroup`
   - namespace inspection: `lsns`, `nsenter -t <pid> -n ip a`
   - context switch rate: `vmstat 1` (cs column), `perf stat`
   - page table inspection: `sudo cat /proc/<pid>/pagemap` (requires root)

---

## Next 3 Steps

1. **Hands-on with namespaces & cgroups:** Use `unshare` to create isolated process (all 7 namespaces), set cgroup limits (memory.max, cpu.max), trigger OOM, observe throttling. Document behavior.
2. **IPC performance testing:** Write benchmark (Go/Rust) comparing UDS, pipes, shared memory latency/throughput under load. Profile with `perf`, correlate with context switch rate.
3. **Container runtime dive:** Study containerd/CRI-O source (how they orchestrate namespaces, cgroups, overlay mounts). Trace syscalls (strace) during container start, map to primitives learned here.