# Linux Kernel: The Complete Deep-Dive Guide
### From Bootloader to Network Subsystem — A Mental Model for Security Researchers

> **Purpose:** Build a solid kernel mental model before diving into the network subsystem.  
> Every concept here maps directly to how packets flow, how sockets work, how the kernel protects (or fails to protect) memory and privilege boundaries.

---

## Table of Contents

1. [The Big Picture — What Is the Kernel?](#1-the-big-picture)
2. [Kernel Architecture — Monolithic Design](#2-kernel-architecture)
3. [Boot Process — From Power-On to PID 1](#3-boot-process)
4. [Kernel Space vs User Space](#4-kernel-space-vs-user-space)
5. [System Calls — The Gateway](#5-system-calls)
6. [Process and Thread Model](#6-process-and-thread-model)
7. [Scheduling — The CPU Allocator](#7-scheduling)
8. [Memory Management](#8-memory-management)
9. [Virtual Memory and the Page Table](#9-virtual-memory-and-the-page-table)
10. [Kernel Data Structures](#10-kernel-data-structures)
11. [Interrupts and IRQ Handling](#11-interrupts-and-irq-handling)
12. [Synchronization Primitives](#12-synchronization-primitives)
13. [The VFS Layer](#13-the-vfs-layer)
14. [Device Drivers and the Driver Model](#14-device-drivers-and-the-driver-model)
15. [Inter-Process Communication](#15-inter-process-communication)
16. [Kernel Modules](#16-kernel-modules)
17. [Security Architecture — LSM, Namespaces, Capabilities](#17-security-architecture)
18. [Network Subsystem — Entry Point](#18-network-subsystem-entry-point)
19. [Rust in the Linux Kernel](#19-rust-in-the-linux-kernel)
20. [Mental Model Summary — Attacker's View](#20-mental-model-summary)

---

## 1. The Big Picture

The Linux kernel is the **core software layer** that sits between hardware and every user application. It is not an application — it has no `main()` you can call. It is the permanent resident of privileged CPU mode.

```
+--------------------------------------------------+
|              USER APPLICATIONS                   |
|  bash  firefox  python  curl  nginx  sshd        |
+------------------+-------------------------------+
                   |  System Call Interface (POSIX)
+------------------v-------------------------------+
|               LINUX KERNEL                       |
|                                                  |
|  +----------+  +---------+  +-----------------+  |
|  | Process  |  | Memory  |  |   File System   |  |
|  | Manager  |  | Manager |  |   (VFS + ext4)  |  |
|  +----------+  +---------+  +-----------------+  |
|  +----------+  +---------+  +-----------------+  |
|  |Scheduler |  |  IPC    |  | Network Stack   |  |
|  |  (CFS)   |  |(pipes,  |  | (TCP/IP, sock)  |  |
|  +----------+  | shmem)  |  +-----------------+  |
|                +---------+                        |
|  +-------------------------------------------+   |
|  |       Device Drivers (thousands)           |   |
|  +-------------------------------------------+   |
+------------------+-------------------------------+
                   |  Hardware Abstraction Layer
+------------------v-------------------------------+
|                 HARDWARE                         |
|  CPU   RAM   NIC   Disk   GPU   USB   PCIe       |
+--------------------------------------------------+
```

### What the kernel is responsible for:

| Responsibility | Description |
|---|---|
| **CPU Multiplexing** | Give each process the illusion of owning the CPU |
| **Memory Isolation** | Each process thinks it has all RAM, but can't see others' |
| **Device Abstraction** | Everything is a file: disks, sockets, pipes, GPUs |
| **Security Enforcement** | Ring 0 enforces what Ring 3 is allowed to do |
| **Networking** | Full TCP/IP stack lives entirely in the kernel |
| **System Call Gate** | Only controlled entry points from user space |

### The kernel is event-driven, not a loop

The kernel doesn't "run" continuously. It is **reactive**:
- Interrupted by hardware (NIC received a packet, timer fired)
- Called by user processes via syscalls
- Called by itself via kernel threads for background work

When no syscall or interrupt is in progress, the CPU executes the **idle task** — a special process that runs `hlt` instruction to power-save.

---

## 2. Kernel Architecture

Linux uses a **monolithic kernel** with **loadable modules**.

```
MONOLITHIC vs MICROKERNEL COMPARISON
======================================

Monolithic (Linux):               Microkernel (Mach/MINIX):
+---------------------+           +---------------------+
|  KERNEL SPACE       |           |  USER SPACE         |
|                     |           |  +----+ +----+      |
|  [sched][mm][net]   |           |  |FS  | |net |      |
|  [vfs][drivers][ipc]|           |  +----+ +----+      |
|                     |           |  +----+ +------+    |
|  ALL in one space   |           |  |drv | |other |    |
|  Direct fn calls    |           |  +----+ +------+    |
+---------------------+           +---------------------+
       |                                   |
+-----v-----------+             +----------v----------+
|   HARDWARE      |             |  TINY KERNEL (IPC)  |
+-----------------+             +---------------------+
                                         |
                               +----------v----------+
                               |      HARDWARE       |
                               +---------------------+

Pros of Monolithic:             Cons of Monolithic:
- Fast (no IPC overhead)        - A bug in driver = kernel panic
- Simpler call paths            - Large attack surface in ring 0
- Mature, optimized             - Harder to hot-replace components
```

### Kernel Source Tree Layout

```
linux/
├── arch/           # Architecture-specific code (x86, arm64, riscv...)
│   └── x86/
│       ├── kernel/ # Core x86 kernel (entry.S, process.c, traps.c)
│       ├── mm/     # x86 memory management (page tables, TLB)
│       └── net/    # x86 network acceleration
├── kernel/         # Core kernel (sched, fork, signal, time, locking)
│   ├── sched/      # Completely Fair Scheduler
│   ├── fork.c      # process/thread creation
│   ├── signal.c    # signal delivery
│   └── sys.c       # generic syscall implementations
├── mm/             # Memory management (vmalloc, slab, mmap, swap)
├── net/            # Network subsystem ← your destination
│   ├── core/       # socket layer, dev.c, skbuff.c
│   ├── ipv4/       # IPv4, TCP, UDP, ICMP
│   ├── ipv6/       # IPv6
│   ├── netfilter/  # iptables/nftables hooks
│   └── packet/     # AF_PACKET sockets
├── fs/             # File systems (ext4, xfs, btrfs, proc, sysfs)
├── drivers/        # Device drivers (net/eth/usb/block/gpu...)
│   └── net/        # NIC drivers (e1000, virtio-net, ixgbe...)
├── include/        # Kernel headers
│   ├── linux/      # Core kernel types (types.h, list.h, skbuff.h)
│   └── net/        # Network headers
├── security/       # LSM (SELinux, AppArmor, BPF LSM)
├── ipc/            # Semaphores, message queues, shared memory
├── init/           # Kernel init (main.c — start_kernel())
└── tools/          # BPF, perf, testing tools
```

---

## 3. Boot Process — From Power-On to PID 1

Understanding boot gives you the mental model of **how the kernel initializes every subsystem**, including the network stack.

```
POWER ON
   |
   v
+------------------+
| BIOS / UEFI      |  Firmware: POST, find bootable device
+------------------+
   |
   v
+------------------+
| GRUB2 / systemd- |  Bootloader: loads vmlinuz + initramfs into RAM
| boot             |  Sets kernel command line (console=, root=, etc.)
+------------------+
   |
   v
+------------------+
| Kernel Decompress|  vmlinuz is compressed (gzip/lzma). Self-extracts.
+------------------+
   |
   v
+------------------+
| arch/x86/boot/   |  16-bit real mode setup → protected mode → long mode
| setup.S          |  (x86_64: enable paging, set up GDT/IDT)
+------------------+
   |
   v
+------------------+
| start_kernel()   |  First C function — init/main.c
| init/main.c      |  
+------------------+
   |
   v  (In order, each subsystem is initialized)
   |
   +---> setup_arch()            # arch-specific: CPU, ACPI, NUMA topology
   +---> mm_init()               # memory allocators (buddy, slab)
   +---> sched_init()            # scheduler: runqueues, CFS init
   +---> rcu_init()              # Read-Copy-Update mechanism
   +---> init_IRQ()              # Interrupt controllers (APIC, PIC)
   +---> softirq_init()          # SoftIRQ / tasklet framework
   +---> time_init()             # timers, clocksource, HPET
   +---> vfs_caches_init()       # VFS: inode cache, dentry cache
   +---> net_namespace_init()    # Network namespace subsystem
   +---> sock_init()             # Socket layer
   +---> proto_init()            # Register TCP, UDP, RAW protocols
   +---> rest_init()
         |
         +---> kernel_thread(kernel_init)   # PID 1 candidate
         +---> cpu_idle()                   # Idle loop forever
               |
               v (kernel_init)
         +---> do_initcalls()    # Call all __initcall functions
         |     |                 # (module init, driver init, net init)
         |     +---> inet_init() # Registers IPv4 family, TCP/UDP/ICMP
         |     +---> [all __init annotated functions in link order]
         |
         +---> run /sbin/init (systemd / PID 1)
               |
               v
         USER SPACE STARTS
```

### The `__init` Annotation

Functions marked `__init` are **freed from memory** after boot completes. This is a key kernel optimization:

```c
// init/main.c
static int __init kernel_init(void *unused)
{
    /*
     * After this point, memory marked __init is released.
     * You'll see "Freeing unused kernel image memory" in dmesg.
     */
    kernel_init_freeable();
    
    if (ramdisk_execute_command) {
        ret = run_init_process(ramdisk_execute_command);
        // ...
    }
    // Eventually execve("/sbin/init", ...) — becomes PID 1
    return 0;
}
```

---

## 4. Kernel Space vs User Space

This is the **most important mental model** for security. Every vulnerability class you hunt has a root cause here.

```
PRIVILEGE RINGS (x86-64)
=========================

         Ring 3 (CPL=3) — USER SPACE
    +-------------------------------------------+
    |  Applications: bash, nginx, python, curl  |
    |  Limited instruction set                  |
    |  Cannot access I/O ports directly         |
    |  Cannot modify page tables                |
    |  Cannot disable interrupts                |
    |  Virtual addresses only (no physical RAM) |
    +-------------------------------------------+
              |         ^
              | syscall  | sysret/sysexit
              v         |
    +-------------------------------------------+
    |  Ring 0 (CPL=0) — KERNEL SPACE           |
    |  Full CPU instruction set                 |
    |  Direct hardware access                   |
    |  Controls page tables for ALL processes   |
    |  Can disable interrupts (cli/sti)         |
    |  Can access any physical memory           |
    |  Sets up protection for Ring 3            |
    +-------------------------------------------+
              |
              v
         HARDWARE (Ring -1 = Hypervisor/VMX)
```

### Memory Layout (x86-64 Linux)

```
VIRTUAL ADDRESS SPACE (48-bit, canonical)
==========================================

0xFFFFFFFFFFFFFFFF  +------------------------+
                    |  Not mapped (non-canon) |
0xFFFF800000000000  +------------------------+
                    |   KERNEL SPACE          |
                    |                         |
                    |  0xFFFF888000000000     |
                    |  Direct mapping of all  |
                    |  physical memory        |
                    |  (page_offset_base)     |
                    |                         |
                    |  0xFFFFFFFF80000000     |
                    |  Kernel text/code       |
                    |  (vmlinux loaded here)  |
                    |                         |
0xFFFF000000000000  +------------------------+
                    |  Non-canonical hole     |
                    |  (causes #GP if accessed)|
0x00007FFFFFFFFFFF  +------------------------+
                    |   USER SPACE            |
                    |                         |
                    |  0x00007FFF....         |
                    |  Stack (grows down)     |
                    |                         |
                    |  mmap region            |
                    |  (shared libs, mmap)    |
                    |                         |
                    |  Heap (grows up)        |
                    |  BSS / data / text      |
0x0000000000400000  |  (ELF loaded here)      |
0x0000000000000000  +------------------------+
                    |  NULL page (unmapped)   |
                    +------------------------+
```

### Why This Matters for Security

- **KASLR** (Kernel Address Space Layout Randomization): randomizes kernel base at boot. Bypassing KASLR (via infoleak) is step 1 in most kernel exploits.
- **SMEP** (Supervisor Mode Execution Prevention): CPU refuses to execute user-space pages in Ring 0. Prevents returning to shellcode in user space.
- **SMAP** (Supervisor Mode Access Prevention): CPU refuses to read/write user-space memory in Ring 0 without explicit `stac/clac` instructions.
- **KPTI** (Kernel Page Table Isolation): kernel and user-space have separate page tables. Mitigates Meltdown (CVE-2017-5754).

---

## 5. System Calls — The Gateway

A **system call** is the only legitimate way for user space to request kernel services. Every socket operation, every `read()`, every `connect()` — it's a syscall.

### How a Syscall Works (x86-64)

```
USER SPACE                          KERNEL SPACE
==========                          ============

1. Setup args in registers:
   rax = syscall number
   rdi = arg1
   rsi = arg2
   rdx = arg3
   r10 = arg4
   r8  = arg5
   r9  = arg6

2. Execute SYSCALL instruction
   ──────────────────────────────────────────────>
                                    3. CPU switches to Ring 0
                                    4. Loads kernel stack (per-CPU)
                                    5. Saves user registers
                                    6. Jumps to entry_SYSCALL_64
                                       (arch/x86/entry/entry_64.S)
                                    
                                    7. Looks up syscall table:
                                       sys_call_table[rax]
                                    
                                    8. Calls: sys_read() / sys_write()
                                       sys_socket() / sys_connect() ...
                                    
                                    9. Checks security (LSM hooks)
                                    
                                   10. Executes kernel logic
                                    
                                   11. Puts return value in rax
   <──────────────────────────────────────────────
12. SYSRET — back to Ring 3
13. Return value in rax
    (negative = errno)
```

### The Syscall Table

```c
// arch/x86/entry/syscalls/syscall_64.tbl (partial)
// nr  abi    name         entry point
0      common read         sys_read
1      common write        sys_write
2      common open         sys_open
3      common close        sys_close
41     common socket       sys_socket
42     common connect      sys_connect
43     common accept       sys_accept
44     common sendto       sys_sendto
45     common recvfrom     sys_recvfrom
49     common bind         sys_bind
50     common listen       sys_listen
```

### C Implementation — How sys_socket() Flows

```c
// net/socket.c
SYSCALL_DEFINE3(socket, int, family, int, type, int, protocol)
{
    return __sys_socket(family, type, protocol);
}

int __sys_socket(int family, int type, int protocol)
{
    int flags;
    struct socket *sock;
    int retval;

    /* SOCK_NONBLOCK and SOCK_CLOEXEC are encoded in 'type' */
    flags = type & ~SOCK_TYPE_MASK;
    type &= SOCK_TYPE_MASK;

    /* Allocate a socket object — this calls the protocol family's
     * create() function, e.g., inet_create() for AF_INET */
    retval = sock_create(family, type, protocol, &sock);
    if (retval < 0)
        return retval;

    /* Allocate a file descriptor visible to user space */
    return sock_map_fd(sock, flags & (O_CLOEXEC | O_NONBLOCK));
}
```

### The `SYSCALL_DEFINE` Macro

```c
// include/linux/syscalls.h
// The macro generates both the function signature and type-safe wrappers
// SYSCALL_DEFINE3 = 3 arguments

#define SYSCALL_DEFINE3(name, ...) \
    SYSCALL_DEFINEx(3, _##name, __VA_ARGS__)

// Expands to:
asmlinkage long sys_socket(int family, int type, int protocol)
{
    // ...
}
```

### Tracing Syscalls (Security-relevant)

```bash
# Trace all syscalls of a process
strace -f -e trace=network curl http://example.com

# Trace with timestamps + call duration
strace -Tf -e trace=network curl http://example.com

# Using BPF — attach to raw_syscalls:sys_enter
bpftrace -e 'tracepoint:syscalls:sys_enter_socket {
    printf("socket() called by PID %d (%s): family=%d\n",
           pid, comm, args->family);
}'
```

---

## 6. Process and Thread Model

### The `task_struct` — The Heart of Process Management

Every process and thread in Linux is represented by a `task_struct`. This is the most important kernel data structure after `sk_buff` (for networking).

```c
// include/linux/sched.h (simplified — real struct has ~400 fields)
struct task_struct {
    /* Run state */
    volatile long           state;      // TASK_RUNNING, TASK_INTERRUPTIBLE, etc.
    void                   *stack;      // Kernel stack pointer
    unsigned int            flags;      // PF_KTHREAD, PF_EXITING, etc.

    /* Scheduling */
    int                     prio;       // Dynamic priority
    int                     static_prio;
    int                     normal_prio;
    unsigned int            rt_priority;
    const struct sched_class *sched_class; // CFS, RT, deadline...
    struct sched_entity     se;         // CFS scheduling entity
    struct sched_rt_entity  rt;         // RT scheduling entity

    /* Process identity */
    pid_t                   pid;        // Thread ID (kernel-internal)
    pid_t                   tgid;       // Thread Group ID = PID from user's view
    struct task_struct     *group_leader; // Points to main thread

    /* Credentials */
    const struct cred      *real_cred;  // Who we actually are
    const struct cred      *cred;       // Who we are acting as (setuid/etc.)

    /* Memory */
    struct mm_struct       *mm;         // Memory map (NULL for kernel threads)
    struct mm_struct       *active_mm;  // Actually active mm

    /* File system */
    struct fs_struct       *fs;         // CWD, root, umask
    struct files_struct    *files;      // Open file descriptor table

    /* Signal handling */
    struct signal_struct   *signal;     // Shared signal state (per thread group)
    struct sighand_struct  *sighand;    // Signal handlers
    sigset_t               blocked;     // Blocked signal mask
    sigset_t               real_blocked;
    struct sigpending       pending;    // Pending private signals

    /* Namespaces */
    struct nsproxy         *nsproxy;    // Net NS, PID NS, Mount NS, UTS NS...

    /* Security */
    void                   *security;  // LSM private data (SELinux, etc.)

    /* Network (used by BPF socket filters) */
    struct sock            *sk_anchor; // BPF socket cookie

    /* Parent/child links */
    struct task_struct     *real_parent;
    struct task_struct     *parent;
    struct list_head        children;
    struct list_head        sibling;

    /* Linked into global task list */
    struct list_head        tasks;      // All tasks: for_each_process()

    /* CPU affinity, NUMA */
    cpumask_t               cpus_mask;
    int                     on_cpu;
    int                     cpu;

    /* Kernel stack end magic for stack overflow detection */
    unsigned long           stack_canary;
};
```

### Process States

```
                     fork()
INITIAL ─────────────────────────> TASK_RUNNING (runnable)
                                         |
                                    CPU available?
                                   /             \
                                 Yes               No
                                  |                |
                              Running          In runqueue
                              on CPU           waiting for CPU
                                  |
                          syscall / I/O wait
                                  |
                                  v
                    TASK_INTERRUPTIBLE        ← Can be woken by signal
                    TASK_UNINTERRUPTIBLE      ← Cannot (D state in ps)
                    TASK_KILLABLE             ← Can be killed (SIGKILL only)
                                  |
                          I/O done / event
                                  |
                                  v
                            TASK_RUNNING (runnable again)
                                  |
                              exit() or signal
                                  |
                                  v
                            TASK_DEAD ──> ZOMBIE (EXIT_ZOMBIE)
                                  |       until parent wait()
                                  v
                            Resources freed
```

### fork(), clone(), execve()

```c
// kernel/fork.c — ALL of fork/vfork/clone go through _do_fork()
long _do_fork(struct kernel_clone_args *args)
{
    struct task_struct *p;
    
    // 1. Allocate and copy the task_struct
    p = copy_process(NULL, 0, NUMA_NO_NODE, args);
    
    // copy_process() calls:
    //   dup_task_struct()    → copy stack, task_struct
    //   copy_creds()         → copy/share credentials
    //   copy_mm()            → copy or share address space
    //   copy_files()         → copy or share file descriptors
    //   copy_sighand()       → copy or share signal handlers
    //   copy_signal()        → copy signal state
    //   copy_namespaces()    → copy or share namespaces
    //   copy_thread_tls()    → arch-specific: set up new stack frame
    
    // 2. Assign PID
    pid = get_task_pid(p, PIDTYPE_PID);
    
    // 3. Wake it up — add to runqueue
    wake_up_new_task(p);
    
    return pid_vnr(pid); // Return child PID to parent
}

// CLONE FLAGS determine what gets shared:
// CLONE_VM      → share memory (threads)
// CLONE_FS      → share filesystem state
// CLONE_FILES   → share file descriptors
// CLONE_SIGHAND → share signal handlers
// CLONE_THREAD  → same thread group (pthread_create uses this)
// CLONE_NEWNET  → new network namespace (containers!)
// CLONE_NEWPID  → new PID namespace
// CLONE_NEWNS   → new mount namespace
```

### Threads vs Processes

```
PROCESS (fork):                    THREAD (pthread_create / clone):
================================   =================================

Parent task_struct                 Main task_struct
   mm_struct (own copy)               mm_struct (SHARED)
   files_struct (own copy)            files_struct (SHARED)
   signal_struct (own)                signal_struct (SHARED)
   pid = 1234                         pid = 1235 (unique kernel PID)
   tgid = 1234                        tgid = 1234 (same thread group)

Child task_struct                  Thread task_struct
   mm_struct (CoW copy)               mm_struct → same pointer!
   files_struct (own copy)            files_struct → same pointer!
   signal_struct (own)                signal_struct → same pointer!
   pid = 1235                         pid = 1236
   tgid = 1235                        tgid = 1234 (group leader)
```

---

## 7. Scheduling — The CPU Allocator

The scheduler decides which task runs on which CPU and for how long.

### The Completely Fair Scheduler (CFS)

CFS is the default scheduler for normal processes. Its core idea: give every task a fair share of CPU time by tracking how much time each has had.

```
CFS CONCEPTUAL MODEL
====================

The "ideal" CPU: every task runs simultaneously, each at (1/N) speed.
CFS approximates this by tracking "virtual runtime" (vruntime):

    vruntime += wall_clock_time * (NICE_0_WEIGHT / task_weight)

Tasks with less vruntime are "behind" and get priority.

RED-BLACK TREE (sorted by vruntime):
=====================================

                   [task E: vruntime=100]
                  /                      \
        [B: vrt=50]                  [H: vrt=200]
       /           \                /
  [A: 30]       [D: 80]       [G: 150]
                                    \
                                 [F: 170]

Next task to run = LEFTMOST node = A (vruntime=30)
After A runs for time slice, its vruntime increases.
It gets reinserted into the tree at new position.
```

### Scheduler Classes (Priority Order)

```c
// kernel/sched/sched.h
// These are checked in order; first class with a runnable task wins:

extern const struct sched_class stop_sched_class;     // Highest: stop_machine
extern const struct sched_class dl_sched_class;       // SCHED_DEADLINE (EDF)
extern const struct sched_class rt_sched_class;       // SCHED_FIFO, SCHED_RR
extern const struct sched_class fair_sched_class;     // SCHED_NORMAL (CFS)
extern const struct sched_class idle_sched_class;     // SCHED_IDLE

// Networking is directly affected by RT scheduling:
// SoftIRQ (NET_RX_SOFTIRQ) runs at process context with elevated priority.
// ksoftirqd kernel thread handles overflow.
```

### Context Switch

```c
// kernel/sched/core.c
static __always_inline struct rq *
context_switch(struct rq *rq, struct task_struct *prev,
               struct task_struct *next, struct rq_flags *rf)
{
    // 1. Switch memory space (if different process — not threads)
    if (!next->mm) {                    // next is a kernel thread
        next->active_mm = prev->active_mm;
        // ...
    } else {
        switch_mm_irqs_off(prev->active_mm, next->mm, next);
        // This updates CR3 register (page table base) on x86
        // CAUSES TLB FLUSH if different address space!
    }
    
    // 2. Switch CPU register state (FPU, GP registers, stack)
    switch_to(prev, next, prev);
    // switch_to() is arch-specific assembly:
    // - Saves prev's rsp (stack pointer)
    // - Restores next's rsp
    // - Returns into next's execution context
    
    return finish_task_switch(prev);
}
```

---

## 8. Memory Management

Memory management is split into several layers. Understanding them is critical for understanding how kernel exploits work (heap overflows, use-after-free, etc.).

```
MEMORY ALLOCATOR HIERARCHY
===========================

Physical RAM
     |
     v
+-------------------+
| BOOTMEM / MEMBLOCK |   Early boot allocator (before buddy is ready)
+-------------------+
     |
     v
+-------------------+
|   BUDDY ALLOCATOR  |   Manages physical pages in power-of-2 blocks
|   (zones: DMA,    |   Alloc: alloc_pages(GFP_KERNEL, order)
|    Normal, High)  |   Free:  free_pages(addr, order)
+-------------------+
     |         |
     v         v
+--------+  +--------+
| SLAB   |  | VMALLOC |
|ALLOCATOR|  |(virtual |
|(kmalloc)|  | contig) |
+--------+  +--------+
     |
     v
+-------------------+
|  KERNEL HEAP API  |
|  kmalloc()        |   < 8KB: from slab cache
|  vmalloc()        |   Large: virtually contiguous
|  kzalloc()        |   kmalloc + zeroed
|  kcalloc()        |   array kmalloc
|  krealloc()       |
|  kfree()          |
+-------------------+
```

### The Buddy Allocator

```
BUDDY SYSTEM — How physical pages are tracked:
==============================================

Memory is divided into pages (4KB on x86).
Pages are grouped into "orders" (power of 2):

order 0: 1 page  (4KB)
order 1: 2 pages (8KB)
order 2: 4 pages (16KB)
...
order 10: 1024 pages (4MB) — MAX_ORDER

Free lists for each order:
free_area[0]: [page][page][page]...   (single free pages)
free_area[1]: [2-page block][2-page block]...
free_area[2]: [4-page block]...

ALLOCATION of order-2 (4 pages):
1. Check free_area[2] → empty
2. Check free_area[3] → found! Split it:
   - Give lower half to caller (4 pages)
   - Put upper half (4 pages) into free_area[2]

FREE of order-2 block at address X:
1. Check if "buddy" block (X XOR (4*PAGE_SIZE)) is also free
2. If yes: merge into order-3, repeat upward
3. If no: add to free_area[2]
```

### The SLAB Allocator (SLUB in modern kernels)

```c
// SLAB/SLUB caches frequently-allocated objects
// to avoid buddy overhead and fragmentation.

// Creating a cache for your own struct:
struct kmem_cache *my_cache;

// At init time:
my_cache = kmem_cache_create(
    "my_object_cache",    // name (appears in /proc/slabinfo)
    sizeof(struct my_obj),// object size
    0,                    // alignment (0 = natural)
    SLAB_HWCACHE_ALIGN,  // flags
    NULL                  // constructor
);

// Allocating:
struct my_obj *obj = kmem_cache_alloc(my_cache, GFP_KERNEL);

// Freeing:
kmem_cache_free(my_cache, obj);

// SECURITY NOTE: SLUB stores free-list pointers INSIDE freed objects.
// Overwriting freed object → control free list → arbitrary alloc location.
// This is the foundation of heap spray / use-after-free kernel exploits.
```

### GFP Flags — What They Mean

```c
GFP_KERNEL      // Normal allocation. May sleep. Used in process context.
GFP_ATOMIC      // Never sleeps. Used in interrupt handlers, softirqs.
                // (Network RX path uses GFP_ATOMIC for sk_buff!)
GFP_NOWAIT      // Don't sleep, but try harder than ATOMIC
GFP_DMA         // Must be in DMA zone (low 16MB on x86)
GFP_HIGHUSER    // User space allocation, can use high memory
GFP_NOIO        // No I/O operations during reclaim (block driver ctx)
GFP_NOFS        // No filesystem operations during reclaim

// These can be combined:
ptr = kmalloc(size, GFP_ATOMIC | __GFP_NOWARN); // Don't warn on failure
```

---

## 9. Virtual Memory and the Page Table

Every process has its own **virtual address space**. The kernel manages a page table that translates virtual → physical addresses.

### 4-Level Page Table (x86-64)

```
48-bit VIRTUAL ADDRESS BREAKDOWN:
===================================

  63      48 47    39 38    30 29    21 20    12 11      0
  +---------+---------+---------+---------+---------+---------+
  |  sign   | PGD idx | PUD idx | PMD idx | PTE idx | offset  |
  | extend  |  9 bits |  9 bits |  9 bits |  9 bits | 12 bits |
  +---------+---------+---------+---------+---------+---------+
      ^          ^         ^         ^         ^         ^
  Must match   [0-511]  [0-511]  [0-511]  [0-511]  byte within
  bit 47                                             4KB page

TRANSLATION WALK:
=================

Virtual Address: 0x00007FFF_DEAD_BEEF

CR3 register → [PGD base physical addr]
                      |
              PGD[idx] → [PUD base]
                              |
                      PUD[idx] → [PMD base]
                                      |
                              PMD[idx] → [PTE base]
                                              |
                                      PTE[idx] → Physical Page Frame
                                                      |
                                              + offset → Physical Byte

If any level's entry is NOT PRESENT → Page Fault (#PF)
Kernel's page fault handler: do_page_fault() → do_user_addr_fault()
```

### The `mm_struct` — Per-Process Memory Descriptor

```c
// include/linux/mm_types.h
struct mm_struct {
    struct maple_tree   mm_mt;      // VMA tree (was rb_tree pre-6.1)
    unsigned long       mmap_base;  // Base of mmap region
    unsigned long       task_size;  // End of user address space
    pgd_t              *pgd;        // Page global directory (CR3 value)
    
    /* Segment boundaries */
    unsigned long       start_code, end_code;   // .text
    unsigned long       start_data, end_data;   // .data
    unsigned long       start_brk, brk;         // Heap
    unsigned long       start_stack;            // Stack start
    unsigned long       arg_start, arg_end;     // argv
    unsigned long       env_start, env_end;     // envp
    
    unsigned long       total_vm;    // Total mapped pages
    unsigned long       locked_vm;   // Pages locked in memory
    unsigned long       pinned_vm;   // Permanently pinned
    unsigned long       data_vm;     // Data + stack pages
    unsigned long       exec_vm;     // Executable pages
    unsigned long       stack_vm;    // Stack pages
    
    /* File-backed mapping tracking */
    struct list_head    mmlist;      // List of all mm_structs
    
    spinlock_t          page_table_lock; // Protects page tables
    struct rw_semaphore mmap_lock;       // Protects VMA list
    
    /* Memory limits (from cgroups / rlimits) */
    unsigned long       def_flags;
};
```

### Virtual Memory Areas (VMAs)

```
PROCESS VIRTUAL MEMORY MAP (as shown by /proc/PID/maps):
=========================================================

Address Range           Perms  File
00400000-00401000       r-xp   /bin/program    ← .text (code)
00600000-00601000       r--p   /bin/program    ← .rodata
00601000-00602000       rw-p   /bin/program    ← .data
00602000-00623000       rw-p   [heap]
7f8a00000000-7f8a1000000 rw-p  [anonymous]     ← mmap alloc
7f8b40000000-7f8b401000 r-xp   /lib/libc.so.6 ← shared lib
7f8b403000-7f8b404000  rw-p   /lib/libc.so.6
7fff0000000-7fff1000000 rw-p  [stack]
ffffffffff600000-fffff.. r-xp  [vsyscall]      ← kernel vsyscall

Each region = one struct vm_area_struct (VMA):

struct vm_area_struct {
    unsigned long   vm_start;       // Start address
    unsigned long   vm_end;         // End address (exclusive)
    unsigned long   vm_flags;       // VM_READ, VM_WRITE, VM_EXEC, VM_SHARED
    pgprot_t        vm_page_prot;   // Page protection bits
    struct file    *vm_file;        // Backing file (NULL = anonymous)
    unsigned long   vm_pgoff;       // Offset in file
    const struct vm_operations_struct *vm_ops; // fault, open, close handlers
    struct mm_struct *vm_mm;        // Owning mm_struct
    struct rb_node  vm_rb;          // In mm->mm_rb tree
};
```

---

## 10. Kernel Data Structures

These are the building blocks. Knowing them lets you read kernel source fluently.

### Doubly-Linked List (`list_head`)

```c
// include/linux/list.h — Used EVERYWHERE in the kernel
// (task list, socket list, network device list, etc.)

struct list_head {
    struct list_head *next, *prev;
};

// Embedding in your struct:
struct my_device {
    int id;
    char name[32];
    struct list_head list;  // ← embedded, not a pointer
};

// Declare and init a list head:
LIST_HEAD(device_list);

// Add to list:
struct my_device *dev = kmalloc(sizeof(*dev), GFP_KERNEL);
list_add(&dev->list, &device_list);       // Add at head
list_add_tail(&dev->list, &device_list);  // Add at tail

// Iterate — note: container_of() magic:
struct my_device *pos;
list_for_each_entry(pos, &device_list, list) {
    printk("device: %s\n", pos->name);
}

// The container_of macro:
// Given a pointer to 'list' member, get pointer to enclosing struct.
#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))
```

### Red-Black Tree (`rb_tree`)

```c
// include/linux/rbtree.h
// Used by: scheduler (CFS), memory manager (VMA tree), packet scheduler

struct rb_node {
    unsigned long rb_parent_color;  // Parent + color packed
    struct rb_node *rb_right;
    struct rb_node *rb_left;
};

struct rb_root {
    struct rb_node *rb_node;
};

// Usage:
struct my_item {
    int key;
    struct rb_node node;
};

struct rb_root my_tree = RB_ROOT;

// Insert:
static void insert_item(struct rb_root *root, struct my_item *item)
{
    struct rb_node **new = &root->rb_node;
    struct rb_node *parent = NULL;
    
    while (*new) {
        struct my_item *this = rb_entry(*new, struct my_item, node);
        parent = *new;
        if (item->key < this->key)
            new = &(*new)->rb_left;
        else if (item->key > this->key)
            new = &(*new)->rb_right;
        else
            return; // duplicate
    }
    rb_link_node(&item->node, parent, new);
    rb_insert_color(&item->node, root);
}
```

### Hash Tables (`hlist`)

```c
// include/linux/hashtable.h
// Used by: PID lookup, socket lookup, routing table

#define DEFINE_HASHTABLE(name, bits) \
    struct hlist_head name[1 << (bits)]

DEFINE_HASHTABLE(pid_hash, 10);  // 1024 buckets

// Network: sockets are found via hash of (src_ip, dst_ip, src_port, dst_port)
// See: net/ipv4/tcp_ipv4.c — inet_ehash_bucket
```

### Per-CPU Variables

```c
// include/linux/percpu.h
// Each CPU gets its own copy — no locking needed!

DEFINE_PER_CPU(long, packet_count);

// Access (must disable preemption):
long count = this_cpu_read(packet_count);
this_cpu_inc(packet_count);
per_cpu(packet_count, cpu_id);

// Network uses this heavily:
// Each CPU has its own softnet_data (RX/TX queues)
// struct softnet_data sd = per_cpu(softnet_data, cpu);
```

---

## 11. Interrupts and IRQ Handling

This is directly relevant to networking — the NIC fires an interrupt when a packet arrives.

```
INTERRUPT HANDLING FLOW
========================

1. NIC receives packet
         |
         v
2. NIC raises IRQ (fires interrupt line)
         |
         v
3. CPU stops current task
   Saves registers on kernel stack
   Looks up IDT (Interrupt Descriptor Table)
         |
         v
4. Calls do_IRQ() → handle_irq() → NIC driver's IRQ handler
   (e.g., e1000_intr() for Intel e1000 NIC)
         |
         v
5. HARDIRQ CONTEXT:
   - Must be fast! Cannot sleep.
   - Driver acknowledges NIC interrupt (clear IRQ)
   - Driver does minimal work:
     • Copies packet from NIC ring buffer to sk_buff
     • Calls netif_rx() or napi_schedule()
   - Schedules SOFTIRQ (NET_RX_SOFTIRQ) for deferred processing
         |
         v
6. Return from interrupt (IRQ re-enabled)
         |
         v
7. SOFTIRQ runs (slightly deferred):
   NET_RX_SOFTIRQ → net_rx_action()
   - Calls NAPI poll function (driver's poll method)
   - Processes packet batch
   - Passes packets up the network stack
         |
         v
8. Eventually: socket buffer → user-space recv()
```

### IRQ vs SoftIRQ vs Tasklet vs Workqueue

```
DEFERRED WORK MECHANISMS (from most urgent to least):
======================================================

HARDIRQ:
  - Context: Hardware interrupt
  - Can sleep: NO
  - Can be preempted: NO (IRQs disabled)
  - Use for: Acknowledge HW, schedule softirq
  - Time budget: Microseconds

SOFTIRQ:
  - Context: Interrupt context (softirq)
  - Can sleep: NO
  - Can be preempted: YES (by hardirqs)
  - Run: On each CPU, after hardirq, or by ksoftirqd thread
  - Fixed set: NET_TX, NET_RX, TIMER, TASKLET, SCHED, HRTIMER, RCU
  - Indexed by: enum softirq_action (net/core: NET_RX_SOFTIRQ = 3)

TASKLET:
  - Built on top of SOFTIRQ (TASKLET_SOFTIRQ)
  - Dynamically allocated
  - Guaranteed: same CPU, not concurrent with self
  - Less performance than raw softirq

WORKQUEUE:
  - Runs in kernel thread context (process context!)
  - CAN SLEEP
  - Used for slow deferred work
  - schedule_work() / queue_work()

Timeline of a packet:
NIC IRQ → [hardirq] → [NET_RX_SOFTIRQ] → [socket layer] → [userspace]
           ~1µs           ~10µs              ~50µs
```

### The `local_irq_save` / `spin_lock_irqsave` Pattern

```c
// When you need to protect data accessed by both
// process context AND interrupt handlers:

unsigned long flags;
spin_lock_irqsave(&my_lock, flags);   // Save IRQ state + disable IRQs + lock
// Critical section — safe from interrupt preemption
spin_unlock_irqrestore(&my_lock, flags); // Restore IRQ state + unlock

// Why not just spin_lock()?
// If an interrupt fires while you hold spin_lock() and the IRQ handler
// also tries to acquire the same lock → DEADLOCK on single CPU.
```

---

## 12. Synchronization Primitives

The kernel is SMP (symmetric multiprocessing) — multiple CPUs run concurrently. Every shared data structure needs protection.

```
LOCK TYPES AND WHEN TO USE THEM:
==================================

+-----------------+--------+----------+----------+-------------------+
| Primitive       | Sleep? | IRQ safe | Perf     | Use Case          |
+-----------------+--------+----------+----------+-------------------+
| spinlock_t      | NO     | with _irq| High     | Short critical sec|
| mutex           | YES    | NO       | Medium   | Long sections     |
| rwlock_t        | NO     | YES      | High     | Many readers      |
| rw_semaphore    | YES    | NO       | Medium   | Long read/write   |
| atomic_t        | NO     | YES      | Highest  | Counters          |
| RCU             | RD: NO | YES      | Highest  | Read-heavy lists  |
|                 | WR: YES|          |          |                   |
| seqlock         | WR: NO | YES      | High     | Mostly reads,     |
|                 | RD: NO |          |          | fast write        |
+-----------------+--------+----------+----------+-------------------+
```

### RCU — Read-Copy-Update

RCU is used extensively in the network stack (routing tables, socket lookup). It's one of the most important concurrency mechanisms in the kernel.

```
RCU CONCEPT:
=============

Rule: Readers never block. Writers copy, modify, then swap.

TIMELINE:
         Reader 1         Reader 2         Writer
         ─────────────    ─────────────    ──────────────────────
         rcu_read_lock()                   
         Read *p = A      rcu_read_lock()  
         (using old A)    Read *p = A      // Allocate new B
         (using old A)    (using old A)    // Copy A → B
         rcu_read_unlock()                 // Modify B  
                          (using old A)    rcu_assign_pointer(p, B)
                          rcu_read_unlock()// p now points to B
                                           synchronize_rcu()
                                           // Wait for ALL readers that
                                           // saw old A to finish
                                           kfree(A) // Safe to free now!

KEY GUARANTEE: 
  Readers ALWAYS see either the old value or the new value.
  Never a partially-updated value.
  No locks needed for readers → zero contention.
```

```c
// RCU in practice — reading a routing table entry:
rcu_read_lock();
struct rtable *rt = rcu_dereference(fib_table->tb_root);
// Use rt safely — guaranteed not to be freed while lock held
ip_route_input(skb, dst, src, tos, in_dev);
rcu_read_unlock();

// RCU write side (routing table update):
struct rtable *new_rt = kmalloc(sizeof(*new_rt), GFP_KERNEL);
memcpy(new_rt, old_rt, sizeof(*old_rt));
new_rt->rt_metric = new_metric;
rcu_assign_pointer(fib_table->tb_root, new_rt);
synchronize_rcu(); // Wait for readers of old_rt
kfree(old_rt);
```

### Atomic Operations

```c
// include/linux/atomic.h
atomic_t refcount = ATOMIC_INIT(1);

atomic_inc(&refcount);           // Atomic increment
atomic_dec(&refcount);           // Atomic decrement
int val = atomic_read(&refcount);
bool zero = atomic_dec_and_test(&refcount); // Dec, test if zero

// Used for: reference counting (socket refcount, skb refcount)
// sk_buff.users is atomic_t — sk_buff shared between layers
```

---

## 13. The VFS Layer

The Virtual File System provides a **unified interface**: everything is a file. Sockets, pipes, devices, proc entries — all accessed via the same open/read/write/close API.

```
VFS ABSTRACTION LAYER:
========================

User: open("/dev/eth0") read(fd) write(fd) close(fd)
      open("/proc/net/tcp") read(fd)
      socket() → same fd interface!
         |
         v
+---------------------+
|    VFS LAYER        |
|  sys_open()         |   Translates path → inode → file operations
|  sys_read()         |   Calls f_op->read()
|  sys_write()        |   Calls f_op->write()
|  sys_ioctl()        |   Calls f_op->unlocked_ioctl()
+---------------------+
    /       |       \
   v        v        v
ext4fs   procfs    sockfs    (different filesystems, same interface)
           |          |
        /proc/net  AF_INET socket
        /proc/pid  AF_UNIX socket

KEY OBJECTS:
  superblock   → Mounted filesystem metadata
  inode        → File metadata (permissions, size, blocks)
  dentry       → Directory entry (name → inode mapping, cached)
  file         → Open file instance (offset, flags, f_op)
```

### VFS Object Relationships

```c
// A socket in VFS:
// socket() syscall → creates socket + inode + file

struct socket {
    socket_state    state;      // SS_CONNECTED, SS_UNCONNECTED...
    short           type;       // SOCK_STREAM, SOCK_DGRAM...
    unsigned long   flags;
    struct sock    *sk;         // The protocol-specific socket (inet_sock)
    const struct proto_ops *ops; // connect, bind, sendmsg, recvmsg...
    struct file    *file;       // Back-pointer to VFS file
    struct fasync_struct *fasync_list; // For async I/O
    wait_queue_head_t wq;       // Wait queue for poll/select/epoll
};

// File operations for sockets:
static const struct file_operations socket_file_ops = {
    .owner      = THIS_MODULE,
    .llseek     = no_llseek,
    .read_iter  = sock_read_iter,
    .write_iter = sock_write_iter,
    .poll       = sock_poll,        // Used by select/poll/epoll
    .unlocked_ioctl = sock_ioctl,
    .mmap       = sock_mmap,
    .release    = sock_close,
    .fasync     = sock_fasync,
    .sendpage   = sock_sendpage,
    .splice_write = generic_splice_sendpage,
    .splice_read  = sock_splice_read,
};
```

---

## 14. Device Drivers and the Driver Model

Device drivers are the kernel's interface to hardware. NIC drivers are what you'll encounter when tracing network packet paths.

```
DRIVER MODEL HIERARCHY:
========================

                    bus_type (pci_bus_type, usb_bus_type)
                         |
              +----------+-----------+
              |                      |
         device                   device_driver
     (struct pci_dev)          (struct pci_driver)
         |                          |
     represents                  implements
     hardware                    .probe()
     device                      .remove()
                                 .id_table[]

MATCHING: kernel iterates devices, finds matching driver via id_table,
          calls driver->probe(). Driver initializes device.

PCI NIC DRIVER EXAMPLE (e1000):
=================================

static struct pci_driver e1000_driver = {
    .name       = "e1000",
    .id_table   = e1000_pci_tbl,    // PCI vendor/device IDs
    .probe      = e1000_probe,       // Called when matching device found
    .remove     = e1000_remove,
    .driver = {
        .pm     = &e1000_pm_ops,
    },
};

// When probe() is called:
static int e1000_probe(struct pci_dev *pdev,
                       const struct pci_device_id *ent)
{
    struct net_device *netdev;
    struct e1000_adapter *adapter;
    
    // 1. Enable PCI device
    pci_enable_device(pdev);
    
    // 2. Request memory regions (BARs)
    pci_request_regions(pdev, e1000_driver_name);
    
    // 3. Allocate net_device (the kernel abstraction for a NIC)
    netdev = alloc_etherdev(sizeof(struct e1000_adapter));
    
    // 4. Fill in net_device_ops (the NIC's operations table)
    netdev->netdev_ops = &e1000_netdev_ops;
    
    // 5. Register with network subsystem
    register_netdev(netdev);  // ← This is where net subsystem meets drivers
}
```

### The `net_device` — Kernel's NIC Abstraction

```c
// include/linux/netdevice.h
struct net_device {
    char            name[IFNAMSIZ];  // "eth0", "lo", "wlan0"
    unsigned long   state;           // __LINK_STATE_START, etc.
    
    struct net_device_ops *netdev_ops; // open, stop, xmit, etc.
    struct ethtool_ops    *ethtool_ops;
    
    unsigned int    flags;           // IFF_UP, IFF_BROADCAST, etc.
    unsigned int    priv_flags;      // IFF_802_1Q_VLAN, etc.
    
    unsigned char   dev_addr[MAX_ADDR_LEN]; // MAC address
    unsigned int    mtu;             // Maximum Transmission Unit
    unsigned short  type;            // ARPHRD_ETHER, etc.
    
    /* TX queue management */
    struct netdev_queue *_tx;        // Array of TX queues
    unsigned int    num_tx_queues;
    
    /* Stats */
    struct net_device_stats stats;   // rx_packets, tx_bytes, errors...
    
    /* Net namespace this device belongs to */
    struct net     *nd_net;          // Pointer to network namespace
    
    /* NAPI (New API) for interrupt coalescing */
    struct list_head napi_list;
};
```

---

## 15. Inter-Process Communication

### Pipes

```c
// Kernel implementation: fs/pipe.c
// A pipe is a ring buffer in kernel memory.
// pipe() syscall → creates two fds (read end, write end)
// Both backed by a pipefs inode

struct pipe_inode_info {
    struct mutex mutex;
    wait_queue_head_t rd_wait, wr_wait;
    unsigned int head;          // Producer index
    unsigned int tail;          // Consumer index
    unsigned int ring_size;     // Number of pages (default: 16 = 64KB)
    struct pipe_buffer *bufs;   // Ring of pipe_buffer structs
    unsigned int readers;
    unsigned int writers;
};
// Security note: Dirty Pipe (CVE-2022-0847) — arbitrary file overwrite
// via pipe page cache splice + overwrite of read-only pages.
```

### UNIX Domain Sockets

```
Used by: DBus, systemd, Docker, X11, SSH agent
Kernel path: net/unix/af_unix.c
Key advantage: Can pass file descriptors between processes (SCM_RIGHTS)
```

### Shared Memory (SHM / mmap)

```c
// Two processes can map the same physical pages
// No kernel involvement after setup

// Process A:
int fd = shm_open("/my_shm", O_CREAT | O_RDWR, 0666);
ftruncate(fd, 4096);
void *ptr = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

// Process B:
int fd = shm_open("/my_shm", O_RDWR, 0666);
void *ptr = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

// Both ptr's map to SAME physical page frame.
// No syscall needed to communicate — direct memory access.
// Need synchronization (futex, semaphore) to avoid races.
```

---

## 16. Kernel Modules

Modules extend the kernel without recompiling or rebooting.

```c
// A minimal kernel module:
// my_module.c

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("You");
MODULE_DESCRIPTION("A minimal kernel module");

static int __init my_module_init(void)
{
    printk(KERN_INFO "my_module: loaded\n");
    // Register with subsystems here:
    // register_netdevice_notifier()
    // proto_register()
    // nf_register_net_hook()  ← netfilter hooks
    return 0;
}

static void __exit my_module_exit(void)
{
    printk(KERN_INFO "my_module: unloaded\n");
    // Unregister everything
}

module_init(my_module_init);
module_exit(my_module_exit);
```

```makefile
# Makefile
obj-m += my_module.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

```bash
# Build and load:
make
sudo insmod my_module.ko
sudo rmmod my_module
dmesg | tail

# Inspect:
lsmod
cat /proc/modules
modinfo my_module.ko
```

### Module Symbol Exports

```c
// Modules can export symbols to other modules:
EXPORT_SYMBOL(my_function);         // Usable by any module
EXPORT_SYMBOL_GPL(my_function);     // Only GPL-licensed modules

// This is how subsystems are extensible:
// net/ipv4/af_inet.c exports proto_register() / proto_unregister()
// Modules (like SCTP, DCCP) call these to register new protocols.
```

---

## 17. Security Architecture — LSM, Namespaces, Capabilities

### Linux Capabilities

```
Traditional Unix: root (UID 0) = all privileges. Binary.
Linux Capabilities: Split root into ~40 fine-grained privileges.

CAP_NET_ADMIN    → Configure network interfaces, routing tables
CAP_NET_RAW      → Use AF_PACKET sockets, raw sockets (needed for ping)
CAP_NET_BIND_SERVICE → Bind to ports < 1024
CAP_SYS_ADMIN    → A huge catch-all (often exploited for privesc)
CAP_SYS_MODULE   → Load/unload kernel modules
CAP_DAC_OVERRIDE → Bypass file permission checks
CAP_SETUID       → Change UID (drop/gain privileges)

// Checking capabilities in kernel code:
if (!capable(CAP_NET_ADMIN))
    return -EPERM;

// For namespaced capabilities:
if (!ns_capable(net->user_ns, CAP_NET_ADMIN))
    return -EPERM;
```

### Linux Security Modules (LSM)

```c
// LSM inserts hooks throughout the kernel at security-relevant points.
// These hooks let SELinux, AppArmor, etc. enforce policy.

// Example hook points (include/linux/security.h):
security_socket_create()    // Before socket()
security_socket_connect()   // Before connect()
security_socket_bind()      // Before bind()
security_socket_sendmsg()   // Before sendmsg()
security_sk_alloc()         // On socket allocation
security_sk_free()          // On socket free

// LSM STACKING (since 5.x): Multiple LSMs can run simultaneously.
// SELinux + BPF LSM + Lockdown simultaneously.

// The hook registration mechanism:
struct security_hook_list {
    struct hlist_node   list;
    struct hlist_head  *head;        // Which hook list
    union security_list_options hook; // The actual function
    const char         *lsm;        // LSM name
};
```

### Linux Namespaces — The Container Primitives

```
NAMESPACE TYPES:
================

NS Type     | Flag           | What it isolates
------------|----------------|----------------------------------
Mount       | CLONE_NEWNS    | Filesystem mount points
PID         | CLONE_NEWPID   | Process IDs (PID 1 in container)
Network     | CLONE_NEWNET   | Network interfaces, routes, sockets
UTS         | CLONE_NEWUTS   | Hostname, domain name
IPC         | CLONE_NEWIPC   | SysV IPC, POSIX message queues
User        | CLONE_NEWUSER  | UID/GID mappings (rootless containers)
Cgroup      | CLONE_NEWCGROUP| cgroup root
Time        | CLONE_NEWTIME  | System clocks

NETWORK NAMESPACE (most relevant for network security):
=======================================================

Each net namespace has its own:
- Loopback device
- Network interfaces (veth pairs connect namespaces)
- Routing table
- Netfilter/iptables rules
- Sockets
- /proc/net/* entries
- IP addresses

struct net {
    refcount_t          passive;
    spinlock_t          rules_mod_lock;
    struct list_head    list;           // All net namespaces
    struct list_head    dev_base_head;  // All net_device in this ns
    struct hlist_head   *dev_name_head; // Device lookup by name
    struct hlist_head   *dev_index_head;// Device lookup by ifindex
    unsigned int        dev_base_seq;
    int                 ifindex;
    
    struct net_device   *loopback_dev;  // lo interface
    
    struct netns_ipv4   ipv4;          // IPv4 routing tables, etc.
    struct netns_ipv6   ipv6;
    struct netns_packet packet;
    struct netns_unix   unx;
    
    struct sock         *rtnl;          // rtnetlink socket
    struct sock         *genl_sock;     // generic netlink socket
    
    struct user_namespace *user_ns;     // Owning user namespace
};
```

---

## 18. Network Subsystem — Entry Point

This section bridges everything above into your target area. Deep-dive comes separately, but here's the architecture.

```
PACKET RX PATH (simplified):
=============================

  NIC Hardware
       |  DMA → RX ring buffer
       |
  [IRQ fired]
       |
  NIC Driver (e.g., ixgbe_msix_clean_rings)
       |  napi_schedule()
       |
  [NET_RX_SOFTIRQ]
       |  net_rx_action() → driver->poll() → napi_gro_receive()
       |
  netif_receive_skb()           ← key function: sk_buff enters stack
       |
  [Protocol handlers registered via dev_add_pack()]
       |  
  ip_rcv()                      ← IPv4 entry point
       |  NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING, ...)
       |
  ip_rcv_finish()
       |  ip_route_input() → routing decision
       |
       +─── Local delivery ──────> ip_local_deliver()
       |                               |
       |                           ip_local_deliver_finish()
       |                               |
       |                         [iptables INPUT chain]
       |                               |
       |                         tcp_v4_rcv() / udp_rcv()
       |                               |
       |                         sock_queue_rcv_skb()
       |                               |
       |                         sk->sk_data_ready()  ← wakes up process
       |                               |
       |                         recv() syscall → copy to userspace
       |
       +─── Forward ─────────────> ip_forward()
                                       |
                                   [iptables FORWARD chain]
                                       |
                                   ip_output()
                                       |
                                   [iptables POSTROUTING]
                                       |
                                   dev_queue_xmit()
                                       |
                                   NIC Driver TX
```

### The `sk_buff` — The Network Packet Object

```c
// include/linux/skbuff.h — MOST IMPORTANT network struct
// Every packet in the kernel is an sk_buff (socket buffer)

struct sk_buff {
    /* First cache line — hot path fields */
    union {
        struct {
            struct sk_buff  *next;
            struct sk_buff  *prev;
            union {
                struct net_device *dev; // Incoming/outgoing device
                unsigned long     dev_scratch;
            };
        };
        struct rb_node  rbnode;
        struct list_head list;
    };
    
    struct sock     *sk;        // Owning socket (NULL for forwarded pkts)
    
    /* Timestamps */
    ktime_t         tstamp;
    
    /* Packet data pointers: */
    unsigned char   *head;      // Start of allocated buffer
    unsigned char   *data;      // Start of current data
    unsigned char   *tail;      // End of current data
    unsigned char   *end;       // End of allocated buffer
    
    //  head ────► [headroom] [===DATA===] [tailroom] ◄── end
    //                        ^           ^
    //                       data        tail
    //
    // headroom: space for protocol headers being added (push)
    // tailroom: space for data being appended (put)
    
    unsigned int    len;        // Total length of data
    unsigned int    data_len;   // Length of paged data
    __u16           mac_len;    // Length of MAC header
    __u16           hdr_len;    // Writable header length of cloned skb
    
    /* Protocol info */
    __be16          protocol;   // ETH_P_IP, ETH_P_IPV6, ETH_P_ARP...
    __u16           transport_header;  // Offset to TCP/UDP header
    __u16           network_header;    // Offset to IP header
    __u16           mac_header;        // Offset to MAC header
    
    /* Checksums */
    __wsum          csum;
    __u8            ip_summed;  // CHECKSUM_NONE/UNNECESSARY/COMPLETE/PARTIAL
    
    /* Fragmentation */
    __u8            frag_list;
    sk_buff_data_t  inner_transport_header;
    
    /* Cloning and reference counting */
    refcount_t      users;      // Reference count
    atomic_t        dataref;    // Data reference count
    
    /* Security / netfilter marks */
    __u32           mark;           // fwmark (used by iptables -j MARK)
    __u32           secmark;        // SELinux security label
    __u32           nfct_reasm;     // netfilter conntrack reassembly
};

// Key sk_buff operations:
skb = alloc_skb(size, GFP_ATOMIC);   // Allocate
skb_reserve(skb, NET_IP_ALIGN);       // Reserve headroom
skb_put(skb, data_len);               // Add data at tail
skb_push(skb, header_len);            // Add header at front
skb_pull(skb, header_len);            // Remove header (advance data ptr)
kfree_skb(skb);                       // Free (decrements refcount)
consume_skb(skb);                     // Free (no drop accounting)
```

### Netfilter Hooks — Where iptables Lives

```
NETFILTER HOOK POINTS (IPv4):
==============================

                  [PREROUTING]
                       |
  ┌────────────────────┼────────────────────────┐
  │                    │                        │
  ▼                    ▼                        │
[LOCAL IN]       [FORWARD]                      │
  │                    │                        │
  ▼                    ▼                        │
Local socket     [POSTROUTING] ◄─── [LOCAL OUT] ┘
                       |
                     Network

Hook registration:
==================

static struct nf_hook_ops my_hook_ops = {
    .hook     = my_hook_fn,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};
nf_register_net_hook(&init_net, &my_hook_ops);

Hook function signature:
========================

static unsigned int my_hook_fn(
    void *priv,
    struct sk_buff *skb,          // The packet
    const struct nf_hook_state *state)
{
    // Inspect/modify skb here
    return NF_ACCEPT;   // NF_DROP, NF_STOLEN, NF_QUEUE, NF_REPEAT
}
```

---

## 19. Rust in the Linux Kernel

Rust was officially merged into the Linux kernel in **v6.1 (December 2022)**. It's now used for writing drivers and subsystem helpers, with the goal of eliminating memory-safety bugs in kernel code.

### Why Rust in the Kernel?

```
C KERNEL BUG CATEGORIES (from CVE analysis):
=============================================
~70% of security vulnerabilities in kernels are memory-safety bugs:
  - Use-After-Free (UAF)
  - Buffer overflows (heap and stack)
  - Double-free
  - Integer overflow → memory miscalculation
  - Null pointer dereference

Rust's ownership model ELIMINATES THESE AT COMPILE TIME:
  - No garbage collector (zero runtime overhead — same as C)
  - Borrow checker enforces memory rules at compile time
  - No dangling pointers possible in safe Rust
  - Option<T> instead of nullable pointers
  - Result<T, E> instead of error-code hell
```

### Rust Kernel Development Setup

```bash
# Building kernel with Rust support:
make LLVM=1 rustavailable    # Check if Rust toolchain is ready

# In Kconfig:
CONFIG_RUST=y

# Required tools:
rustup override set $(scripts/min-tool-version.sh rustc)
rustup component add rust-src
cargo install --locked bindgen-cli
```

### The Rust Kernel Abstractions

The kernel provides safe Rust wrappers over unsafe C primitives.

```rust
// rust/kernel/lib.rs — The kernel crate
// Everything in here wraps unsafe C via FFI

// Basic module skeleton in Rust:
// samples/rust/rust_minimal.rs

use kernel::prelude::*;

module! {
    type: RustMinimal,
    name: "rust_minimal",
    author: "Rust for Linux Contributors",
    description: "Rust minimal sample",
    license: "GPL",
}

struct RustMinimal {
    numbers: Vec<i32>,
}

impl kernel::Module for RustMinimal {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("Rust minimal sample (init)\n");
        let mut numbers = Vec::new();
        numbers.try_push(72)?;  // try_push = fallible allocation
        numbers.try_push(108)?;
        numbers.try_push(200)?;
        Ok(RustMinimal { numbers })
    }
}

impl Drop for RustMinimal {
    fn drop(&mut self) {
        pr_info!("Rust minimal sample (exit)\n");
        pr_info!("Numbers were {:?}\n", self.numbers);
    }
}
```

### Memory Allocation in Rust Kernel Code

```rust
// In C:  kmalloc(size, GFP_KERNEL)
// In Rust: Box::try_new() with KernelAllocator

use kernel::alloc::flags;

// Allocate a Box (heap object):
let my_data = Box::try_new_in(MyStruct::default(), flags::GFP_KERNEL)?;

// Allocate a Vec:
let mut buf: Vec<u8> = Vec::new();
buf.try_extend_from_slice(&[0u8; 1024], flags::GFP_ATOMIC)?;

// The ? operator propagates errors — no more checking if ptr == NULL
// GFP_ATOMIC allocation failure returns Err(ENOMEM) automatically
```

### Rust Locking Primitives

```rust
// rust/kernel/sync/mutex.rs
use kernel::sync::Mutex;

// C: mutex_lock(&my_mutex); /* critical section */ mutex_unlock(&my_mutex);
// Rust: lock is dropped automatically when MutexGuard goes out of scope

let protected_data = Mutex::new(MyData::new());

{
    let mut guard = protected_data.lock();
    guard.value += 1;
    // mutex automatically unlocked here when guard drops
}

// Spinlock:
use kernel::sync::SpinLock;
let spinlock_data = SpinLock::new(0u32);
{
    let mut guard = spinlock_data.lock();
    *guard = 42;
} // Automatically unlocked
```

### Rust + C Interop in the Kernel

```rust
// Calling C kernel functions from Rust (via bindgen-generated bindings):

use kernel::bindings;

unsafe {
    // Call C function directly:
    bindings::netif_carrier_on(netdev.as_ptr());
    
    // Access C struct field:
    let ifindex = (*netdev.as_ptr()).ifindex;
}

// Wrapping unsafe C in safe Rust abstraction:
pub struct NetDevice(NonNull<bindings::net_device>);

impl NetDevice {
    pub fn carrier_on(&self) {
        // SAFETY: self.0 is always a valid net_device pointer
        unsafe { bindings::netif_carrier_on(self.0.as_ptr()) }
    }
    
    pub fn ifindex(&self) -> i32 {
        // SAFETY: net_device is valid, ifindex field is always readable
        unsafe { (*self.0.as_ptr()).ifindex }
    }
}
// Now callers use safe Rust — no unsafe needed at call site
```

### Writing a Rust Network Driver (Structure)

```rust
// A Rust PHY (network PHY chip) driver — first Rust driver merged to mainline
// drivers/net/phy/ax88796b_rust.rs

use kernel::{
    net::phy::{self, DeviceId, Driver, PhyFlags, Registration},
    prelude::*,
};

kernel::module_phy_driver! {
    drivers: [PhyAX88796B],
    device_table: [
        DeviceId::new_with_driver::<PhyAX88796B>()
    ],
    name: "ax88796b_rust_phy",
    author: "ASIX Electronics Corporation",
    description: "Rust ASIX PHY driver",
    license: "GPL",
}

struct PhyAX88796B;

impl Driver for PhyAX88796B {
    const FLAGS: u32 = PhyFlags::IS_INTERNAL.bits();
    const NAME: &'static CStr = c_str!("Asix Electronics AX88796B");
    const PHY_DEVICE_ID: DeviceId = DeviceId::new_with_custom_mask(
        0x003b1841, 0xfffffff0
    );

    fn config_init(dev: &mut phy::Device) -> Result {
        // Configure the PHY chip
        dev.modify_paged_reg(0, 0x12, 0, 0x100)?;
        Ok(())
    }

    fn config_aneg(dev: &mut phy::Device) -> Result {
        // Configure auto-negotiation
        phy::genphy_config_aneg(dev)?;
        Ok(())
    }

    fn read_status(dev: &mut phy::Device) -> Result<u16> {
        phy::genphy_read_status(dev)
    }
}
```

### Rust Error Handling vs C in Kernel Context

```c
// C kernel style (error-prone — easy to forget to check):
int ret;
struct sk_buff *skb;

skb = alloc_skb(size, GFP_KERNEL);
if (!skb)              // Must check manually
    return -ENOMEM;

ret = register_netdev(netdev);
if (ret)               // Must check manually
    goto err_free_skb; // goto chains for cleanup

err_free_skb:
    kfree_skb(skb);
    return ret;
```

```rust
// Rust kernel style (enforced by compiler):
fn setup_network() -> Result {
    let skb = alloc_skb(size, flags::GFP_KERNEL)?; // ? auto-returns error
    
    register_netdev(&netdev)?; // ? auto-returns error
    
    // Cleanup is automatic via Drop trait — no goto chains!
    Ok(())
}
// If any ? returns Err, everything allocated above is automatically freed
// because Rust's ownership/Drop ensures destructors run on scope exit.
```

---

## 20. Mental Model Summary — Attacker's View

Now that you have the full picture, here's how to think like an attacker targeting the kernel or its network subsystem:

```
KERNEL ATTACK SURFACE MAP:
===========================

1. SYSCALL INTERFACE
   ─────────────────
   Every syscall is an entry point.
   socket(), bind(), connect(), sendmsg(), recvmsg(), setsockopt()...
   Target: argument validation bugs, integer overflow on sizes,
           missing capability checks.

2. IOCTL / NETLINK / PROC/SYS
   ───────────────────────────
   ioctl(sockfd, SIOCGIFHWADDR, ...) — network interface control
   Netlink: RTM_NEWROUTE, NLMSG_*, rtnetlink
   /proc/sys/net/ — sysctl
   Target: insufficient privilege checks, out-of-bounds writes
           in parsing code, integer overflows.

3. PACKET PROCESSING PATH
   ────────────────────────
   sk_buff handling from NIC to socket.
   Target: heap overflow in sk_buff data, UAF in async paths,
           race conditions between RX path and socket close.

4. DRIVER INTERFACE
   ─────────────────
   NIC drivers run in kernel space.
   Malicious hardware → malicious DMA → kernel memory corruption.
   (Thunderclap, CVE-2019-18198 etc.)

5. NAMESPACE / CAPABILITY ESCAPES
   ─────────────────────────────────
   Unprivileged user namespaces (enabled by default on Ubuntu):
   Allow CAP_NET_ADMIN within namespace.
   Target: operations that check ns-level caps but affect global state.

6. BPF (eBPF)
   ────────────
   eBPF programs run in kernel. If verifier has a bug:
   → Arbitrary kernel memory read/write.
   Historical: CVE-2021-3490, CVE-2021-4204, CVE-2022-23222.
   BPF verifier bypasses are a top bug class.

ATTACK CHAINS:
==============

INFO LEAK → KASLR BYPASS → CONTROL FLOW HIJACK → PRIVILEGE ESCALATION

Step 1: Info Leak
  kernel pointer in /proc, dmesg, error messages,
  uninitialized heap data returned to userspace.
  Tools: leak via recvmsg() with uninitialized padding,
         BPF map reads, out-of-bounds reads.

Step 2: KASLR Bypass
  Use leaked kernel pointer to calculate kernel base address.
  Now you know where kernel code is mapped.

Step 3: Heap Corruption
  UAF, heap overflow, double-free.
  Target SLUB caches: spray the heap with known objects,
  corrupt free-list pointer → control next kmalloc() result.

Step 4: Control Flow
  Overwrite function pointers (sk->sk_destruct, ops->connect, etc.)
  Overwrite return address (stack overflow — rarer with stack canaries).
  ROP chain → disable SMEP/SMAP → ret2user or ret2kernel.

Step 5: Privilege Escalation
  commit_creds(prepare_kernel_cred(NULL))
  → uid=0, all caps, escape namespace.
```

### Tools for Kernel Security Research

```bash
# Source navigation:
grep -r "SYSCALL_DEFINE" net/socket.c
cscope -Rb && cscope -d          # Cross-reference C source
ctags -R --exclude='.git'         # Tags for vim/emacs

# Dynamic analysis:
sudo dmesg -w                      # Watch kernel messages
sudo bpftrace -l 'kprobe:tcp_*'   # List TCP kprobes
sudo bpftrace -e 'kprobe:tcp_connect { printf("%s\n", comm); }'

# eBPF tracing:
sudo bcc/trace.py 'r::sys_socket "fd=%d", retval'
sudo bcc/funccount.py 'tcp_*'

# Kernel debugging:
QEMU + GDB with kernel debug symbols:
  qemu-system-x86_64 -kernel bzImage -s -S ...
  gdb vmlinux
  (gdb) target remote :1234
  (gdb) break tcp_connect
  (gdb) continue

# Static analysis:
Smatch:  make CHECK="smatch --project=kernel" C=1 net/ipv4/tcp.c
Coccinelle: spatch --sp-file semantic_patch.cocci net/

# Fuzzing:
syzkaller: Go-based kernel fuzzer, generates syscall sequences
           Responsible for 1000s of kernel bug reports.
           https://github.com/google/syzkaller

trinity: Classic syscall fuzzer
AFL++:   Can fuzz kernel via kcov+userfaultfd tricks
```

---

## Appendix: Key Headers to Know

```
include/linux/skbuff.h      — sk_buff (packet buffer)
include/linux/netdevice.h   — net_device (NIC abstraction)
include/linux/socket.h      — socket types, address families
include/linux/tcp.h         — TCP header struct
include/linux/ip.h          — IP header struct
include/linux/sched.h       — task_struct
include/linux/mm_types.h    — mm_struct, vm_area_struct
include/linux/list.h        — doubly linked list
include/linux/rbtree.h      — red-black tree
include/linux/spinlock.h    — spinlock, rwlock
include/linux/mutex.h       — sleeping mutex
include/linux/rcupdate.h    — RCU primitives
include/linux/atomic.h      — atomic operations
include/linux/fs.h          — VFS: file, inode, dentry, super_block
include/linux/net.h         — socket struct
include/linux/in.h          — sockaddr_in
include/uapi/linux/if.h     — ifreq, interface flags
net/sock.h                  — struct sock (protocol-level socket)
net/tcp.h                   — tcp_sock, TCP state machine
net/ip.h                    — IP routing functions
```

## Appendix: Key Source Files for Network Subsystem

```
net/socket.c              — syscall entry (socket, bind, connect...)
net/core/sock.c           — struct sock allocation, options
net/core/skbuff.c         — sk_buff allocation, cloning, management
net/core/dev.c            — netif_receive_skb, dev_queue_xmit
net/core/filter.c         — BPF socket filter / eBPF
net/ipv4/af_inet.c        — AF_INET socket creation, inet_create()
net/ipv4/tcp.c            — TCP send/receive, state machine
net/ipv4/tcp_ipv4.c       — TCP over IPv4, hash tables, lookup
net/ipv4/tcp_input.c      — TCP receive processing
net/ipv4/tcp_output.c     — TCP transmit processing
net/ipv4/udp.c            — UDP implementation
net/ipv4/ip_input.c       — ip_rcv(), IP receive path
net/ipv4/ip_output.c      — ip_output(), IP transmit path
net/ipv4/route.c          — IP routing table
net/netfilter/           — iptables/nftables hooks
drivers/net/              — NIC drivers (e1000.c, virtio_net.c, etc.)
```

---

*This document covers the full kernel mental model needed before deep-diving into the network subsystem. The next step is to trace a packet end-to-end: from `socket()` → `connect()` → `sendmsg()` → `skb allocation` → `ip_output()` → `dev_queue_xmit()` → NIC driver, and reverse for RX. Every security boundary, every lock, every function pointer in that path is a potential vulnerability.*
