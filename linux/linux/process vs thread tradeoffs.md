# Process vs Thread Tradeoffs: A Complete Kernel-Level Guide

> Kernel version context: Linux v6.8+ (unless noted)  
> Architecture focus: x86_64 / ARM64  
> Source references: kernel.org/pub/linux/kernel/

---

## Table of Contents

1. [Kernel Fundamentals: Everything is a Task](#1-kernel-fundamentals-everything-is-a-task)
2. [The `task_struct`: Unified Representation](#2-the-task_struct-unified-representation)
3. [Process Creation: `fork()` Internals](#3-process-creation-fork-internals)
4. [Thread Creation: `clone()` and `pthread_create()`](#4-thread-creation-clone-and-pthread_create)
5. [Memory Model Differences](#5-memory-model-differences)
6. [Scheduler Perspective](#6-scheduler-perspective)
7. [Address Space Layout](#7-address-space-layout)
8. [File Descriptor Table Sharing](#8-file-descriptor-table-sharing)
9. [Signal Handling](#9-signal-handling)
10. [Synchronization Primitives](#10-synchronization-primitives)
11. [IPC Mechanisms](#11-ipc-mechanisms)
12. [Context Switch Cost Analysis](#12-context-switch-cost-analysis)
13. [TLB and Cache Effects](#13-tlb-and-cache-effects)
14. [CPU Affinity and NUMA](#14-cpu-affinity-and-numa)
15. [Security and Isolation](#15-security-and-isolation)
16. [C Implementation](#16-c-implementation)
17. [Go Implementation](#17-go-implementation)
18. [Rust Implementation](#18-rust-implementation)
19. [Benchmarking and Tracing](#19-benchmarking-and-tracing)
20. [Decision Matrix](#20-decision-matrix)

---

## 1. Kernel Fundamentals: Everything is a Task

The Linux kernel makes **no fundamental distinction** between a process and a thread at the scheduler level. Both are represented by `task_struct`. The difference is purely in what resources are **shared** between tasks.

```
POSIX Model                          Linux Kernel Model
─────────────────                    ──────────────────────────────────────
  Process                              task_struct (process/thread group leader)
  ├── Thread 1  ──────────────────►    task_struct (CLONE_VM | CLONE_FS | ...)
  ├── Thread 2  ──────────────────►    task_struct (CLONE_VM | CLONE_FS | ...)
  └── Thread 3  ──────────────────►    task_struct (CLONE_VM | CLONE_FS | ...)

  fork()        ──────────────────►    task_struct (copy-on-write mm_struct)
```

**Key kernel axiom:**  
> A thread is a task that shares `mm_struct`, `files_struct`, `fs_struct`, and `signal_struct` with its creator via `clone(2)` flags. A process is a task with its own copies of these structures.

**Relevant source files:**
- `include/linux/sched.h` — `task_struct` definition
- `kernel/fork.c` — `do_fork()`, `copy_process()`
- `kernel/sched/core.c` — scheduler core
- `fs/exec.c` — `execve()` path

---

## 2. The `task_struct`: Unified Representation

```
include/linux/sched.h
─────────────────────────────────────────────────────────────────────────
struct task_struct {
    /* --- Scheduling state --- */
    unsigned int            __state;         // TASK_RUNNING, TASK_INTERRUPTIBLE...
    int                     prio;            // dynamic priority
    int                     static_prio;     // nice-based static priority
    int                     normal_prio;
    unsigned int            rt_priority;
    struct sched_entity     se;              // CFS entity
    struct sched_rt_entity  rt;              // RT entity

    /* --- Identity --- */
    pid_t                   pid;             // unique task ID (TID in POSIX)
    pid_t                   tgid;            // thread group ID (PID in POSIX)
    struct task_struct      *group_leader;   // points to thread group leader

    /* --- Resource pointers (shared or private) --- */
    struct mm_struct        *mm;             // address space (NULL for kthreads)
    struct mm_struct        *active_mm;      // active address space
    struct files_struct     *files;          // open file descriptors
    struct fs_struct        *fs;             // filesystem context (cwd, root)
    struct signal_struct    *signal;         // shared signal handlers (threads)
    struct sighand_struct   *sighand;        // signal disposition table
    struct nsproxy          *nsproxy;        // namespaces
    struct css_set          *cgroups;        // cgroup membership
    struct thread_struct    thread;          // arch-specific CPU state (registers)

    /* --- Memory management --- */
    struct list_head        mm_tasks;        // tasks sharing this mm
    unsigned long           stack;           // kernel stack pointer

    /* --- Credentials --- */
    const struct cred       *real_cred;
    const struct cred       *cred;

    /* --- Relationships --- */
    struct task_struct      *real_parent;
    struct task_struct      *parent;
    struct list_head        children;
    struct list_head        sibling;
};
```

### PID vs TGID

```
User Space View             Kernel View
────────────────            ─────────────────────────────────────────────
                            task_struct [pid=1000, tgid=1000] ← group_leader
Process PID=1000  ────────► task_struct [pid=1001, tgid=1000] ← thread
  Thread TID=1001           task_struct [pid=1002, tgid=1000] ← thread
  Thread TID=1002
                              getpid()  → tgid = 1000
                              gettid()  → pid  = 1001/1002
```

- `getpid(2)` returns `task->tgid`
- `gettid(2)` returns `task->pid`
- `ps` shows TGID; `/proc/<pid>/task/` shows all threads
- Source: `kernel/sys.c:SYSCALL_DEFINE0(getpid)`, `SYSCALL_DEFINE0(gettid)`

---

## 3. Process Creation: `fork()` Internals

### System Call Path

```
User:    fork()
          │
          ▼
Syscall:  sys_fork()                    [arch/x86/entry/syscalls/syscall_64.tbl]
          │
          ▼
kernel/fork.c:
          kernel_clone(kernel_clone_args{
              .flags = SIGCHLD,
              .exit_signal = SIGCHLD,
          })
          │
          ▼
          copy_process()
          ├── dup_task_struct()         → allocates new task_struct + kernel stack
          ├── copy_creds()              → copies credentials
          ├── copy_mm()                 → COW-duplicates mm_struct
          │     └── dup_mm()
          │           └── dup_mmap()   → copies VMAs, marks PTEs read-only for COW
          ├── copy_files()             → duplicates files_struct (new table, same fds)
          ├── copy_fs()               → duplicates fs_struct (cwd, root)
          ├── copy_sighand()          → duplicates sighand_struct
          ├── copy_signal()           → new signal_struct
          ├── copy_thread()           → arch-specific: sets up return address
          └── pid_ns allocation       → alloc_pid()
```

### Copy-on-Write (COW) for `mm_struct`

```
After fork():

Parent mm_struct             Child mm_struct
──────────────               ──────────────
vm_area_struct               vm_area_struct (duplicated)
  │                            │
  ▼                            ▼
PTE: [phys_addr, RO]  ←──── PTE: [phys_addr, RO]
         │                            │
         └──────────────┬─────────────┘
                        ▼
                   Physical Page
                   (shared, ref_count=2)

On write by either:
  page_fault → do_wp_page() → alloc new page → copy → mark original RW again
```

- Source: `mm/memory.c:do_wp_page()`, `mm/fork.c:dup_mmap()`
- The `vm_area_struct` linked list is fully duplicated; PTE entries are made read-only
- First write triggers a page fault → `do_page_fault()` → COW resolution

### `exec()` after `fork()`

```
execve(path, argv, envp)
    │
    ▼
fs/exec.c: do_execveat_common()
    ├── bprm_mm_init()         → new mm_struct (old mm is dropped)
    ├── load_elf_binary()       → maps segments into new mm
    ├── flush_old_exec()        → tears down old address space
    ├── set_binfmt()
    └── start_thread()         → sets RIP/PC to ELF entry point
```

After `exec()`, the process gets a **completely new address space** — all COW mappings from `fork()` are discarded. This is why the fork-exec pattern is the standard process spawning idiom.

---

## 4. Thread Creation: `clone()` and `pthread_create()`

### `clone()` Flags that Define "Thread-ness"

```
include/uapi/linux/sched.h
──────────────────────────────────────────────────────────────────
Flag                  Meaning when set
────────────────────  ─────────────────────────────────────────────
CLONE_VM              Share mm_struct (address space)
CLONE_FS              Share fs_struct (cwd, umask, root)
CLONE_FILES           Share files_struct (file descriptor table)
CLONE_SIGHAND         Share sighand_struct (signal handlers)
CLONE_THREAD          Same thread group (same TGID)
CLONE_SETTLS          Set TLS descriptor (fs/gs base on x86)
CLONE_PARENT_SETTID   Write TID to parent's user pointer
CLONE_CHILD_CLEARTID  futex-wake on exit (implements join)
CLONE_CHILD_SETTID    Write TID to child's user pointer
```

### `pthread_create()` → `clone()` Call

```
glibc: pthread_create()
    │
    ▼
sysdeps/unix/sysv/linux/pthread_create.c: __pthread_create_2_1()
    │
    ├── allocate_stack()       → mmap() new stack for thread
    │     └── mprotect() guard page at bottom (SIGSEGV on overflow)
    │
    ▼
clone(CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND |
      CLONE_THREAD | CLONE_SYSVSEM | CLONE_SETTLS |
      CLONE_PARENT_SETTID | CLONE_CHILD_CLEARTID | CLONE_CHILD_SETTID,
      new_stack_top, &parent_tid, tls_desc, &child_tid)
    │
    ▼
kernel: copy_process() with above flags
    ├── copy_mm()     → CLONE_VM: mm = parent->mm; atomic_inc(&mm->mm_users)
    ├── copy_files()  → CLONE_FILES: atomic_inc(&files->count)
    ├── copy_fs()     → CLONE_FS: spin_lock; fs->users++
    └── copy_sighand()→ CLONE_SIGHAND: atomic_inc(&sighand->count)
```

**Key insight:** With `CLONE_VM`, `copy_mm()` simply increments `mm->mm_users` and assigns the **same pointer**. No page table duplication occurs. This is why thread creation is faster than `fork()`.

### Thread Stack Layout

```
High Address
┌─────────────────────────────┐ ← mmap base (e.g., 0x7f...)
│   Guard Page (PROT_NONE)    │ ← SIGSEGV trap for stack overflow
│─────────────────────────────│
│                             │
│   Thread Stack              │ ← CLONE_SETTLS points TLS here
│   (grows downward)          │
│                             │
│─────────────────────────────│
│   TLS (Thread Local Storage)│ ← __thread variables, errno, etc.
│   pthread_t descriptor      │ ← struct pthread (glibc internal)
└─────────────────────────────┘ ← mmap base - stack_size
Low Address

Each thread has its own stack; all threads share the same heap/code/data segments.
```

### `vfork()` — Optimized fork-exec

```c
/* kernel/fork.c */
/* vfork = fork with CLONE_VFORK | CLONE_VM flags */
/* Parent BLOCKS until child calls exec() or exit() */
/* Child borrows parent's mm — no COW, no copy at all */
/* Extremely dangerous if child writes to memory */
```

---

## 5. Memory Model Differences

### Process Memory: Isolated `mm_struct`

```
Process A                           Process B
─────────────────────────────       ─────────────────────────────
mm_struct                           mm_struct
├── pgd: PGD_A ──────────┐          ├── pgd: PGD_B ──────────┐
├── mmap (VMA list)       │          ├── mmap (VMA list)       │
│   ├── [0x400000-text]   │          │   ├── [0x400000-text]   │
│   ├── [heap]            │          │   ├── [heap]            │
│   └── [stack]           │          │   └── [stack]           │
├── start_code            │          ├── start_code            │
├── start_data            │          └── ...                   │
└── ...                   │                                    │
                          ▼                                    ▼
                    Physical Memory                    Physical Memory
                    (separate pages)                   (separate pages)

CR3 register points to different PGD on each process → full TLB flush on switch
```

### Thread Memory: Shared `mm_struct`

```
Thread 1          Thread 2          Thread 3
task_struct       task_struct       task_struct
    │                 │                 │
    └─────────────────┴─────────────────┘
                      │
                      ▼
                  mm_struct (shared)
                  ├── pgd: PGD ──────► Page Tables (shared)
                  ├── mm_users = 3    (thread count)
                  ├── mm_count = 1    (struct reference count)
                  └── mmap (VMA list)
                      ├── [text]  ──────────────┐
                      ├── [data]  ──────────────┤──► Same physical pages
                      ├── [heap]  ──────────────┘    for all threads
                      ├── [stack T1] ──────────► Thread 1's private stack
                      ├── [stack T2] ──────────► Thread 2's private stack
                      └── [stack T3] ──────────► Thread 3's private stack

CR3 register is SAME for all threads → no TLB flush on thread switch (same process)
```

### `mm_struct` Reference Counting

```c
/* include/linux/mm_types.h */
struct mm_struct {
    atomic_t        mm_users;   /* How many tasks use this mm? */
    atomic_t        mm_count;   /* Structural reference count */
    /* mm_users drops to 0 → __mmput() frees page tables   */
    /* mm_count drops to 0 → free_mm() frees the struct    */
};
```

- `fork()`:  `dup_mm()` → `mm_users=1`, `mm_count=1` on new mm
- `clone(CLONE_VM)`: `atomic_inc(&mm->mm_users)` → shared mm
- Thread exit: `mmput()` → `atomic_dec_and_test(&mm->mm_users)` → if 0, tear down

### Memory Access Patterns

```
               PROCESS                          THREAD
               ───────                          ──────
Isolation:     Full (separate PGD)              None (shared PGD)
Communication: Requires IPC (pipe/shm/socket)   Direct pointer dereference
Safety:        Crash in A doesn't affect B       Crash (SIGSEGV) kills all threads
Data sharing:  Explicit (mmap MAP_SHARED, shm)   Implicit (global/heap variables)
Sync needed:   For shared-memory IPC only        Always for shared data
False sharing: Not possible across processes     Cache line false sharing possible
```

---

## 6. Scheduler Perspective

### Completely Fair Scheduler (CFS)

Both processes and threads are scheduled identically by CFS. Each `task_struct` has a `sched_entity` (`se`) that is enqueued in a per-CPU red-black tree.

```
Per-CPU Run Queue (struct rq)             kernel/sched/core.c
                                          kernel/sched/fair.c
  cfs_rq (CFS run queue)
  ├── tasks_timeline (rb_root_cached)    ← red-black tree ordered by vruntime
  │   ├── task_struct.se (thread A)
  │   ├── task_struct.se (process B)     ← processes and threads are indistinct
  │   ├── task_struct.se (thread A2)
  │   └── task_struct.se (process C)
  └── min_vruntime                       ← leftmost node's vruntime

Schedule tick → pick_next_task_fair()
    → leftmost task in rb-tree wins
    → vruntime += delta_exec * (NICE_0_LOAD / se.load.weight)
```

### Thread Group Scheduling

```
Task Group (CONFIG_FAIR_GROUP_SCHED=y)
──────────────────────────────────────
/sys/fs/cgroup/cpu/<group>/

Group A (weight=1024)          Group B (weight=512)
├── thread A1 (w=1024)         ├── thread B1 (w=1024)
├── thread A2 (w=1024)         └── thread B2 (w=1024)
└── thread A3 (w=1024)

Group A gets 2x CPU time vs Group B regardless of thread count.
Without group scheduling: Group A gets 3/5 CPU (unfair thread-count advantage).

struct task_group {             /* kernel/sched/sched.h */
    struct cfs_bandwidth    cfs_bandwidth;
    struct sched_entity     **se;    /* one per CPU */
    struct cfs_rq           **cfs_rq;
};
```

### Scheduler Wake-up Latency: Process vs Thread

```
Thread Wake (same mm):                Process Wake (different mm):
──────────────────────                ──────────────────────────────
try_to_wake_up()                      try_to_wake_up()
    │                                     │
    ▼                                     ▼
enqueue_task_fair()               enqueue_task_fair()
    │                                     │
    ▼                                     ▼
context_switch()                  context_switch()
    │                                     │
    ├── switch_mm_irqs_off()          ├── switch_mm_irqs_off()
    │   └── (same pgd? skip CR3)     │   └── load_new_mm_cr3()  ← CR3 reload
    │                                │       → TLB flush (if !PCID)
    ├── switch_to() [registers]      ├── switch_to() [registers]
    └── return                       └── return

Measured overhead difference: ~1-5 μs on modern x86 (PCID reduces gap)
```

**PCID (Process Context Identifiers):** Since Linux v4.14 on x86, `CR4.PCIDE` allows TLB entries to be tagged with a 12-bit PCID, avoiding full TLB flushes on process switches. Source: `arch/x86/mm/tlb.c`.

---

## 7. Address Space Layout

### Process Address Space (64-bit x86)

```
Virtual Address Space (48-bit canonical, x86_64)
0xFFFFFFFFFFFFFFFF ─────────────────────────────
                    [Kernel space - not user accessible]
                    (mapped in all processes, but SMEP/SMAP protect it)
0xFFFF800000000000 ─────────────────────────────
                    [Non-canonical hole]
0x00007FFFFFFFFFFF ─────────────────────────────
                    stack (grows ↓)          ← /proc/PID/maps: [stack]
                    (random base: ASLR)
                    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                    mmap region (grows ↓)   ← libraries, anonymous maps
                    (glibc, libpthread, etc.)
                    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                    heap (grows ↑)           ← brk/mmap allocations
                    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                    BSS segment             ← uninitialized globals
                    Data segment            ← initialized globals
                    Text segment            ← executable code (r-x)
0x0000000000400000 ─────────────────────────────
                    [null guard, not mapped]
0x0000000000000000 ─────────────────────────────
```

### Multi-threaded Process Address Space

```
Virtual Address Space (single mm_struct, 3 threads)
─────────────────────────────────────────────────────────────
0x7fff________  ←── Main thread stack
                    (original stack, set by kernel at exec)
─ ─ ─ ─ ─ ─ ─
0x7ffe________  ←── Thread 2 stack  (pthread_create → mmap)
                    + guard page below
─ ─ ─ ─ ─ ─ ─
0x7ffd________  ←── Thread 3 stack  (pthread_create → mmap)
                    + guard page below
─ ─ ─ ─ ─ ─ ─
0x7f__________  ←── mmap region: libpthread.so, libc.so, etc.
─ ─ ─ ─ ─ ─ ─
[heap]          ←── shared heap (malloc is thread-safe via ptmalloc arenas)
[data/bss]      ←── shared global variables
[text]          ←── shared code
─────────────────────────────────────────────────────────────

Each thread sees the COMPLETE map — there's no separation.
A buffer overflow in Thread 2 can corrupt Thread 3's stack.
```

---

## 8. File Descriptor Table Sharing

```
Process fork():                     Thread clone(CLONE_FILES):
────────────────────────            ──────────────────────────────────────
task A → files_struct A             task A ──┐
  [0]=stdin  refcnt=1               task B ──┤→ files_struct (shared)
  [1]=stdout                        task C ──┘   [0]=stdin  refcnt=3
  [2]=stderr                                     [1]=stdout
                                                 [2]=stderr
task B → files_struct B (copy)
  [0]=stdin  refcnt=1               Any thread calling close(1) closes
  [1]=stdout                        stdout for ALL threads!
  [2]=stderr
                                    files_struct uses spin_lock_t lock
task A closing fd[3] does           + fdtable (RCU-protected on read)
NOT affect task B's fd[3]
```

### `files_struct` internals

```c
/* include/linux/fdtable.h */
struct files_struct {
    atomic_t        count;          /* reference count */
    bool            resize_in_progress;
    struct fdtable __rcu *fdt;      /* RCU-protected pointer to fd table */
    struct fdtable  fdtab;          /* embedded fdtable for small fd counts */
    spinlock_t      file_lock;      /* protects fd array changes */
    unsigned int    next_fd;        /* hint for next_fd allocation */
    /* ... */
};

struct fdtable {
    unsigned int    max_fds;
    struct file __rcu **fd;         /* current fd array */
    unsigned long   *close_on_exec;
    unsigned long   *open_fds;
    unsigned long   *full_fds_bits;
    /* ... */
};
```

**Important:** `dup2(2)`, `close(2)`, `open(2)` all acquire `file_lock`. Under high contention from many threads, this becomes a bottleneck. Solutions: reduce fd sharing, use `O_CLOEXEC`, or use separate fd tables (processes).

---

## 9. Signal Handling

Signal delivery is one of the most complex differences between processes and threads.

```
Signal Delivery Rules (POSIX + Linux):
───────────────────────────────────────────────────────────────────────────
Signal type         Target              Who handles it?
──────────────      ──────────────      ──────────────────────────────────
Process-directed    kill(pid, sig)      Any thread in group (kernel picks)
Thread-directed     tgkill(pid,tid,sig) Specific thread only
                    pthread_kill()
Synchronous fault   SIGSEGV/SIGFPE      The faulting thread (always)
SIGKILL/SIGSTOP     Process-directed    ALL threads (non-catchable)
```

### Signal Data Structures

```
signal_struct (shared across all threads in group)
    include/linux/sched/signal.h
    ├── sigpending shared      ← process-directed pending signals
    ├── rlimit[]               ← resource limits
    ├── tty                    ← controlling terminal
    └── wait_chldexit          ← waitqueue for wait()

sighand_struct (shared: CLONE_SIGHAND)
    ├── action[NSIG]           ← signal disposition (SIG_DFL, SIG_IGN, handler)
    └── siglock (spinlock)     ← protects action[] modifications

task_struct.pending             ← thread-private pending signal queue
task_struct.blocked             ← per-thread signal mask (sigprocmask)
```

### Signal and Thread Interaction

```
Thread Group Leader (pid=tgid=1000)
├── Thread 1 (tid=1001)  blocked={SIGUSR1}
├── Thread 2 (tid=1002)  blocked={}          ← can receive SIGUSR1
└── Thread 3 (tid=1003)  blocked={SIGUSR1}

kill(1000, SIGUSR1) → kernel selects Thread 2 (not blocked, running/waiting)
                    → signal_wake_up(thread2_task, 1)
                    → TIF_SIGPENDING set on thread2

tgkill(1000, 1001, SIGUSR1) → Thread 1 must handle it even though blocked
                             → blocks until Thread 1 unblocks SIGUSR1
```

---

## 10. Synchronization Primitives

### Kernel-Level Primitives (for reference)

```
Primitive          Header                    Use case
─────────────────  ────────────────────────  ─────────────────────────────
spinlock_t         include/linux/spinlock.h  Short critical sections, IRQ safe
mutex              include/linux/mutex.h     Blocking mutex (sleepable)
rwlock_t           include/linux/rwlock.h    Read-write spinlock
rw_semaphore       include/linux/rwsem.h     Read-write semaphore (sleepable)
seqlock_t          include/linux/seqlock.h   Read-mostly, write-occasionally
atomic_t           include/linux/atomic.h    Atomic integers
RCU                include/linux/rcupdate.h  Read-Copy-Update (lockless reads)
```

### Futex: Foundation of Userspace Threading

`pthread_mutex`, `pthread_cond`, `sem_t` are all built on `futex(2)`:

```
Fast path (no contention):
───────────────────────────
pthread_mutex_lock()
    │
    ▼
atomic cmpxchg(futex_word, 0, TID)  ← purely userspace, no syscall
    │
    └── success → mutex acquired, return

Slow path (contention):
────────────────────────
pthread_mutex_lock()
    │
    ▼
atomic cmpxchg fails (already locked)
    │
    ▼
futex(FUTEX_WAIT, futex_addr, expected_val, timeout)
    │  [syscall]
    ▼
kernel/futex/futex.c: futex_wait()
    ├── compute_effective_key()     → hash on (mm, futex_addr) for processes
    │                                  hash on (mm=shared, addr) for threads
    ├── queue_lock(hb)              → lock hash bucket
    ├── futex_wait_queue_me()       → add to waitqueue, set TASK_INTERRUPTIBLE
    └── schedule()                 → yield CPU

Unlock:
pthread_mutex_unlock()
    │
    ▼
atomic store 0 to futex_word
    │
    ▼
futex(FUTEX_WAKE, futex_addr, 1)    ← only if waiters exist
    │
    ▼
kernel: wake up one waiter from hash bucket queue
```

**Cross-process futex:** Processes can share a futex via `mmap(MAP_SHARED)` or `POSIX shared memory`. The kernel identifies cross-process futexes by the physical page address (inode + offset for file-backed, or page frame for anonymous shared).

---

## 11. IPC Mechanisms

### Comparison Table

```
Mechanism         Processes  Threads  Kernel Objects    Overhead    Notes
────────────────  ─────────  ───────  ───────────────   ─────────   ─────────────────────────────
Shared Memory     ✓(mmap)    ✓        none(anon) or     Zero-copy   Sync required; fastest IPC
(MAP_SHARED)                           inode(file)
POSIX shm_open    ✓          ✓        /dev/shm inode    Zero-copy   Named, persistent
Pipes (anon)      ✓(related) ✓        pipe_inode_info   Copy        EOF on last writer close
Named pipes(FIFO) ✓          ✓        inode             Copy        Survives process death
Unix sockets      ✓          ✓        socket+inode      Copy+meta   Full duplex, fd passing
TCP loopback      ✓          ✓        net_device        Copy+stack  Slowest; network stack
POSIX mq          ✓          ✓        mqueue inode      Copy        Priority, blocking
SysV msgq         ✓          ✓        ipc namespace     Copy        Legacy; avoid
eventfd           ✓(related) ✓        eventfd_ctx       Minimal     Counter/signal only
signalfd          ✓          ✓        signalfd_ctx      Minimal     Signal → fd
Direct (heap/global) ✗       ✓        none              Fastest     No kernel involvement
```

### Pipe Internals

```
pipe(fd[2]):
    ├── creates pipe_inode_info
    │     ├── head (write pointer)
    │     ├── tail (read pointer)
    │     └── bufs[PIPE_BUFFERS] (16 × 4KB pages = 64KB default)
    ├── fd[0] → file (FMODE_READ)  → inode
    └── fd[1] → file (FMODE_WRITE) → inode

Write path: pipe_write() → copies user data into pipe pages (or splice)
Read path:  pipe_read()  → copies from pipe pages to user buffer

Kernel source: fs/pipe.c
```

---

## 12. Context Switch Cost Analysis

### What Happens During a Context Switch

```
schedule() called (voluntary or tick-driven preemption)
    │
    ▼
__schedule() [kernel/sched/core.c]
    ├── prev = current task
    ├── next = pick_next_task() → CFS picks lowest vruntime
    │
    ▼
context_switch(rq, prev, next)
    │
    ├── prepare_task_switch(rq, prev, next)
    │
    ├── arch/x86/include/asm/mmu_context.h:
    │   switch_mm_irqs_off(prev->mm, next->mm, next)
    │   │
    │   ├── [Thread switch, same mm] → skip CR3 reload entirely
    │   │
    │   └── [Process switch, diff mm] →
    │         load_new_mm_cr3(next->pgd, tlb_gen)
    │         ├── write_cr3(new_pgd | PCID)   ← only if PCID differs
    │         └── [or] invlpg / full TLB flush  ← without PCID
    │
    ├── switch_to(prev, next, prev)
    │   [arch/x86/include/asm/switch_to.h]
    │   ├── Save: RSP, RBX, RBP, R12-R15 (callee-saved) to prev->thread.sp
    │   ├── Load: RSP from next->thread.sp
    │   ├── WRGSBASE / FS.base → TLS segment (if FSGSBASE)
    │   ├── FPU: lazy or eager save/restore (x87/SSE/AVX state)
    │   │     include/linux/fpu/sched.h: fpregs_restore_userregs()
    │   └── jmp __switch_to (returns as 'next', prev handle in rax)
    │
    └── finish_task_switch(prev)
        └── put_task_stack(prev) if needed
```

### Measured Costs (approximate, x86_64, Linux v6.x)

```
Operation                        Approx Cost
─────────────────────────────    ────────────────────────────────────────────
Thread context switch            ~1-3 μs    (same mm, no TLB flush, PCID)
Process context switch (PCID)    ~2-5 μs    (CR3 write, partial TLB flush)
Process ctx switch (no PCID)     ~5-20 μs   (full TLB flush, cache thrash)
pthread_mutex_lock (uncontended) ~20 ns     (purely userspace cmpxchg)
futex syscall (contended)        ~1-2 μs    (syscall overhead + scheduler)
fork() (small process)           ~50-200 μs (COW setup, alloc_pid, etc.)
fork() (large address space)     ~500 μs+   (VMA duplication cost)
pthread_create()                 ~10-50 μs  (stack mmap, clone syscall)
pipe write/read (4KB)            ~1-3 μs    (copy_from/to_user)
Unix socket send/recv (4KB)      ~3-8 μs    (socket overhead)
```

### FPU State Handling

```
Legacy behavior (CONFIG_X86_EAGER_FPU not set):
    FXSAVE on switch out (if task used FPU)
    CR0.TS set to catch FPU use in next task
    First FPU instruction → #NM fault → fpu_restore_context()

Modern (XSAVE, compacted XSAVES):
    xsaves [rbx]   → only saves modified state components
    xrstors [rbx]  → only restores needed components
    AVX-512 registers (512-bit ZMM) add ~2KB per context!
    arch/x86/kernel/fpu/core.c: fpu__save(), fpu__restore_signal()
```

---

## 13. TLB and Cache Effects

### TLB Miss Cost

```
TLB Hit:          ~1 cycle
L1 TLB Miss:      ~10 cycles  (L2 TLB / page walk)
L2 TLB Miss:      ~100 cycles (memory access for page walk)
Page not present: ~1000+ cycles (page fault handler)

Thread switch advantage:
    Same CR3 → TLB entries from all threads' accesses remain valid
    → Working set of all threads benefits all other threads

Process switch disadvantage (no PCID):
    New CR3 → entire TLB invalidated
    → First accesses after switch all TLB-miss
    → "TLB shootdown" cost: O(VMA count) on context switch
```

### Cache Coherency and False Sharing

```
False sharing example (threads on same cache line):
────────────────────────────────────────────────────
struct counters {
    int cpu0_count;   // offset 0 (bytes 0-3)
    int cpu1_count;   // offset 4 (bytes 4-7)
};
// Both fit in a 64-byte cache line!

CPU 0 writes cpu0_count:  MESI state → Modified on CPU0, Invalid on CPU1
CPU 1 writes cpu1_count:  cache coherency protocol → write-back, invalidate
                          CPU0 re-fetches cache line
                          → 100x slowdown despite touching different variables!

Fix:
struct counters {
    int cpu0_count;
    char __pad[60];   // pad to cache line boundary
    int cpu1_count;
} __attribute__((aligned(64)));
// Or use: __cacheline_aligned_in_smp (include/linux/cache.h)
```

### NUMA Effects

```
NUMA Node 0 (socket 0)          NUMA Node 1 (socket 1)
──────────────────────          ──────────────────────
CPU 0-11                        CPU 12-23
LLC (L3 cache, 16MB)            LLC (L3 cache, 16MB)
RAM: 16GB                       RAM: 16GB
    │                               │
    └───────── QPI/UPI Link ────────┘
               ~40-80ns latency

Process spawned on Node 0:
    Pages allocated on Node 0 (NUMA-local, fast)
    If thread migrates to Node 1:
        Memory access → cross-NUMA → ~2x latency penalty

NUMA-aware thread pinning:
    numa_run_on_node(1);               // restrict to node 1
    set_mempolicy(MPOL_BIND, node1);   // bind memory to node 1
    // Or: numactl --cpunodebind=1 --membind=1 ./app
```

---

## 14. CPU Affinity and NUMA

### `sched_setaffinity(2)` Internals

```
sched_setaffinity(pid, cpumask_t *mask)
    │
    ▼
kernel/sched/core.c: __sched_setaffinity()
    ├── task->cpus_mask = new_mask
    ├── if task running on CPU not in new_mask:
    │     migration_cpu_stop() → kick task off current CPU
    │     → task re-queued on allowed CPU
    └── sched_domains checked for topology-aware placement

Data structures:
    task_struct.cpus_mask      ← allowed CPUs
    task_struct.recent_used_cpu ← cache for wake_up placement
    sched_domain                ← topology: SMT, MC (LLC), NUMA
```

### Thread Pinning Strategy

```
Application with 4 worker threads on 4-core CPU (2 NUMA nodes, 2 cores each):

Strategy 1: All on Node 0 (memory-bound, cache sharing beneficial)
    Thread 0 → CPU 0 (Node 0)
    Thread 1 → CPU 1 (Node 0)
    Threads 2,3 → overflow to Node 1

Strategy 2: Spread for compute (independent workloads)
    Thread 0 → CPU 0 (Node 0)
    Thread 1 → CPU 2 (Node 1)
    Thread 2 → CPU 1 (Node 0)
    Thread 3 → CPU 3 (Node 1)

Strategy 3: SMT-aware (hyperthreading)
    Avoid pairing threads on HT siblings if CPU-bound:
        CPU 0 (physical core 0, HT 0)  ← Thread 0
        CPU 1 (physical core 0, HT 1)  ← avoid if compute-intensive
        CPU 2 (physical core 1, HT 0)  ← Thread 1
        CPU 3 (physical core 1, HT 1)  ← avoid
```

---

## 15. Security and Isolation

### Process Isolation

```
Isolation layer          Process        Thread
────────────────────     ─────────      ──────────────────────────
Address space            Full (mm)      None (shared mm)
File descriptors         Copy           Shared (CLONE_FILES)
Namespaces               Inherited      Inherited (always shared)
Capabilities             Per-task cred  Per-task cred (independent)
Seccomp                  Per-task       Per-task (can differ!)
SELinux context          Per-task       Per-task (can differ)
Signal isolation         Cross-process  Intra-group (same sighand)
Memory protection        SMEP/SMAP      SMEP/SMAP (but shared!)
Fault containment        Process crash  Entire thread group dies
```

### Seccomp and Threads

```c
/* kernel/seccomp.c */
/* Seccomp filter is per-task, NOT per-thread-group */
/* A thread can have STRICTER seccomp than its siblings */

prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog);
/* Only applies to calling thread; others unaffected */

/* To apply to all threads: set before creating them, */
/* or use SECCOMP_FILTER_FLAG_TSYNC to sync to all threads */
seccomp(SECCOMP_SET_MODE_FILTER,
        SECCOMP_FILTER_FLAG_TSYNC, &fprog);
```

### Namespace Isolation (for processes only in practice)

```
Namespace          clone() flag      Scope
─────────────      ──────────────    ─────────────────────────────────────
Mount              CLONE_NEWNS       Filesystem mount points
UTS                CLONE_NEWUTS      hostname, domainname
IPC                CLONE_NEWIPC      SysV IPC, POSIX mq namespace
Network            CLONE_NEWNET      Network interfaces, routes
PID                CLONE_NEWPID      PID numbering (child PID=1)
User               CLONE_NEWUSER     UID/GID mapping
Cgroup             CLONE_NEWCGROUP   cgroup root
Time               CLONE_NEWTIME     CLOCK_REALTIME/BOOTTIME offsets

Threads share their creator's namespaces; cannot have per-thread namespaces.
Namespaces are per-nsproxy, and nsproxy is NOT shared with CLONE_VM alone.

struct nsproxy {              /* include/linux/nsproxy.h */
    atomic_t count;
    struct uts_namespace  *uts_ns;
    struct ipc_namespace  *ipc_ns;
    struct mnt_namespace  *mnt_ns;
    struct pid_namespace  *pid_ns_for_children;
    struct net            *net_ns;
    struct cgroup_namespace *cgroup_ns;
    struct time_namespace  *time_ns;
};
```

### Capability Inheritance

```
/* Both process and thread have independent struct cred */
/* include/linux/cred.h */
struct cred {
    kuid_t  uid, euid, suid, fsuid;
    kgid_t  gid, egid, sgid, fsgid;
    kernel_cap_t cap_inheritable;
    kernel_cap_t cap_permitted;
    kernel_cap_t cap_effective;
    kernel_cap_t cap_bset;        /* capability bounding set */
    kernel_cap_t cap_ambient;
    /* ... */
};
/* Thread can drop capabilities independently: */
/* prctl(PR_SET_SECUREBITS, ...) per thread */
/* But gaining capabilities requires going through exec + setuid */
```

---

## 16. C Implementation

### 16.1 Process Pool (Fork-based Worker Pool)

```c
/* process_pool.c
 * Demonstrates fork-based process pool with pipe IPC
 * Compile: gcc -O2 -o process_pool process_pool.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/prctl.h>
#include <errno.h>
#include <signal.h>

#define NUM_WORKERS 4
#define TASK_SIZE   64

typedef struct {
    int  worker_id;
    int  req_pipe[2];   /* parent→child */
    int  res_pipe[2];   /* child→parent */
    pid_t pid;
} worker_t;

typedef struct {
    char  data[TASK_SIZE];
    int   seq;
    int   terminate;
} task_t;

typedef struct {
    int   seq;
    int   result;
    pid_t worker_pid;
} result_t;

static void worker_main(worker_t *w)
{
    task_t   task;
    result_t res;

    /* Set worker name visible in ps/top */
    prctl(PR_SET_NAME, "pool-worker", 0, 0, 0);

    /* Close unused pipe ends */
    close(w->req_pipe[1]);
    close(w->res_pipe[0]);

    while (1) {
        ssize_t n = read(w->req_pipe[0], &task, sizeof(task));
        if (n <= 0 || task.terminate)
            break;

        /* Simulate work */
        int sum = 0;
        for (int i = 0; i < TASK_SIZE; i++)
            sum += task.data[i];

        res.seq        = task.seq;
        res.result     = sum;
        res.worker_pid = getpid();

        write(w->res_pipe[1], &res, sizeof(res));
    }

    close(w->req_pipe[0]);
    close(w->res_pipe[1]);
    _exit(0);
}

int main(void)
{
    worker_t workers[NUM_WORKERS];

    /* Spawn worker processes */
    for (int i = 0; i < NUM_WORKERS; i++) {
        worker_t *w = &workers[i];
        w->worker_id = i;

        if (pipe(w->req_pipe) < 0 || pipe(w->res_pipe) < 0) {
            perror("pipe");
            exit(1);
        }

        w->pid = fork();
        if (w->pid < 0) {
            perror("fork");
            exit(1);
        }
        if (w->pid == 0) {
            /* Child: become worker */
            worker_main(w);
            /* NOT reached */
        }
        /* Parent: close unused ends */
        close(w->req_pipe[0]);
        close(w->res_pipe[1]);
    }

    /* Dispatch tasks round-robin */
    int num_tasks = 20;
    for (int t = 0; t < num_tasks; t++) {
        worker_t *w = &workers[t % NUM_WORKERS];
        task_t task = { .seq = t, .terminate = 0 };
        memset(task.data, (char)t, TASK_SIZE);
        write(w->req_pipe[1], &task, sizeof(task));
    }

    /* Collect results */
    for (int t = 0; t < num_tasks; t++) {
        worker_t *w = &workers[t % NUM_WORKERS];
        result_t res;
        read(w->res_pipe[0], &res, sizeof(res));
        printf("task[%d]: result=%d from pid=%d\n",
               res.seq, res.result, res.worker_pid);
    }

    /* Terminate workers */
    for (int i = 0; i < NUM_WORKERS; i++) {
        task_t term = { .terminate = 1 };
        write(workers[i].req_pipe[1], &term, sizeof(term));
        close(workers[i].req_pipe[1]);
        close(workers[i].res_pipe[0]);
        waitpid(workers[i].pid, NULL, 0);
    }

    return 0;
}
```

### 16.2 Thread Pool with Work Queue

```c
/* thread_pool.c
 * POSIX thread pool with lock-free-ish work queue using futex
 * Compile: gcc -O2 -pthread -o thread_pool thread_pool.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>
#include <unistd.h>
#include <errno.h>
#include <sched.h>
#include <sys/syscall.h>
#include <linux/futex.h>

#define NUM_THREADS  4
#define QUEUE_SIZE   256

/* ── Cache-line aligned counter (avoid false sharing) ── */
typedef struct {
    atomic_long value;
    char __pad[64 - sizeof(atomic_long)];
} __attribute__((aligned(64))) aligned_counter_t;

/* ── Lock-free SPSC ring buffer per thread ── */
typedef struct {
    void (*fn)(void *arg);
    void *arg;
} task_t;

typedef struct {
    task_t          buf[QUEUE_SIZE];
    atomic_uint     head;          /* consumer reads */
    char            _pad1[64 - sizeof(atomic_uint)];
    atomic_uint     tail;          /* producer writes */
    char            _pad2[64 - sizeof(atomic_uint)];
    atomic_int      futex_word;    /* 0=empty, 1=data available */
} __attribute__((aligned(64))) spsc_queue_t;

static inline int futex_wait(atomic_int *addr, int expected)
{
    return syscall(SYS_futex, addr, FUTEX_WAIT_PRIVATE,
                   expected, NULL, NULL, 0);
}

static inline int futex_wake(atomic_int *addr, int n)
{
    return syscall(SYS_futex, addr, FUTEX_WAKE_PRIVATE,
                   n, NULL, NULL, 0);
}

static int spsc_push(spsc_queue_t *q, void (*fn)(void*), void *arg)
{
    unsigned int tail = atomic_load_explicit(&q->tail, memory_order_relaxed);
    unsigned int head = atomic_load_explicit(&q->head, memory_order_acquire);

    if ((tail - head) >= QUEUE_SIZE)
        return -1;  /* full */

    q->buf[tail & (QUEUE_SIZE - 1)] = (task_t){ fn, arg };
    atomic_store_explicit(&q->tail, tail + 1, memory_order_release);

    /* Wake worker if sleeping */
    if (atomic_exchange_explicit(&q->futex_word, 1, memory_order_release) == 0)
        futex_wake(&q->futex_word, 1);
    return 0;
}

static int spsc_pop(spsc_queue_t *q, task_t *out)
{
    unsigned int head = atomic_load_explicit(&q->head, memory_order_relaxed);
    unsigned int tail = atomic_load_explicit(&q->tail, memory_order_acquire);

    if (head == tail)
        return -1;  /* empty */

    *out = q->buf[head & (QUEUE_SIZE - 1)];
    atomic_store_explicit(&q->head, head + 1, memory_order_release);
    return 0;
}

typedef struct {
    int          id;
    spsc_queue_t queue;
    atomic_int   shutdown;
    aligned_counter_t tasks_done;
    pthread_t    tid;
} worker_ctx_t;

static void *worker_thread(void *arg)
{
    worker_ctx_t *ctx = arg;
    task_t task;
    char name[16];

    snprintf(name, sizeof(name), "pool-%d", ctx->id);
    pthread_setname_np(pthread_self(), name);

    while (!atomic_load_explicit(&ctx->shutdown, memory_order_relaxed)) {
        if (spsc_pop(&ctx->queue, &task) == 0) {
            task.fn(task.arg);
            atomic_fetch_add_explicit(&ctx->tasks_done.value, 1,
                                      memory_order_relaxed);
        } else {
            /* Queue empty — wait on futex */
            atomic_store_explicit(&ctx->queue.futex_word, 0,
                                  memory_order_release);
            futex_wait(&ctx->queue.futex_word, 0);
        }
    }

    /* Drain remaining */
    while (spsc_pop(&ctx->queue, &task) == 0) {
        task.fn(task.arg);
        atomic_fetch_add_explicit(&ctx->tasks_done.value, 1,
                                  memory_order_relaxed);
    }
    return NULL;
}

/* ── Example task function ── */
static void compute_task(void *arg)
{
    long n = (long)arg;
    volatile long sum = 0;
    for (long i = 0; i < n; i++) sum += i;
    (void)sum;
}

int main(void)
{
    worker_ctx_t workers[NUM_THREADS] = {};

    /* Initialize and spawn threads */
    for (int i = 0; i < NUM_THREADS; i++) {
        workers[i].id = i;
        atomic_init(&workers[i].shutdown, 0);
        atomic_init(&workers[i].tasks_done.value, 0);
        atomic_init(&workers[i].queue.head, 0);
        atomic_init(&workers[i].queue.tail, 0);
        atomic_init(&workers[i].queue.futex_word, 0);

        pthread_attr_t attr;
        pthread_attr_init(&attr);

        /* Optional: pin to CPU */
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(i % (int)sysconf(_SC_NPROCESSORS_ONLN), &cpuset);
        pthread_attr_setaffinity_np(&attr, sizeof(cpuset), &cpuset);

        pthread_create(&workers[i].tid, &attr, worker_thread, &workers[i]);
        pthread_attr_destroy(&attr);
    }

    /* Dispatch 1000 tasks */
    for (int t = 0; t < 1000; t++) {
        worker_ctx_t *w = &workers[t % NUM_THREADS];
        while (spsc_push(&w->queue, compute_task, (void*)10000L) < 0)
            sched_yield();  /* back-pressure */
    }

    /* Shutdown */
    for (int i = 0; i < NUM_THREADS; i++) {
        atomic_store(&workers[i].shutdown, 1);
        futex_wake(&workers[i].queue.futex_word, 1);
        pthread_join(workers[i].tid, NULL);
        printf("worker[%d]: completed %ld tasks\n",
               i, atomic_load(&workers[i].tasks_done.value));
    }

    return 0;
}
```

### 16.3 Shared Memory IPC Between Processes

```c
/* shm_ipc.c
 * Demonstrates process IPC via POSIX shared memory + futex
 * Compile: gcc -O2 -lrt -o shm_ipc shm_ipc.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <stdatomic.h>
#include <fcntl.h>

#define BUF_SIZE 4096
#define NUM_MSGS 100

typedef struct {
    atomic_int  producer_futex;   /* 0 = slot free, 1 = data ready */
    atomic_int  consumer_futex;   /* 0 = slot full, 1 = consumed */
    atomic_int  sequence;
    int         len;
    char        buf[BUF_SIZE];
} __attribute__((aligned(64))) shm_channel_t;

static inline void futex_wait_val(atomic_int *f, int val)
{
    while (atomic_load(f) == val)
        syscall(SYS_futex, f, FUTEX_WAIT, val, NULL);
}

static inline void futex_set_wake(atomic_int *f, int val)
{
    atomic_store(f, val);
    syscall(SYS_futex, f, FUTEX_WAKE, 1);
}

int main(void)
{
    /* Allocate shared memory (survives fork) */
    shm_channel_t *ch = mmap(NULL, sizeof(shm_channel_t),
                              PROT_READ | PROT_WRITE,
                              MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (ch == MAP_FAILED) { perror("mmap"); exit(1); }

    memset(ch, 0, sizeof(*ch));
    atomic_init(&ch->producer_futex, 1);  /* producer can write */
    atomic_init(&ch->consumer_futex, 0);
    atomic_init(&ch->sequence, 0);

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); exit(1); }

    if (pid == 0) {
        /* ── Consumer (child) ── */
        for (int i = 0; i < NUM_MSGS; i++) {
            /* Wait for data */
            futex_wait_val(&ch->producer_futex, 1);

            printf("consumer: seq=%d msg='%.*s'\n",
                   atomic_load(&ch->sequence),
                   ch->len, ch->buf);

            /* Signal producer: slot free */
            futex_set_wake(&ch->producer_futex, 1);
        }
        _exit(0);
    }

    /* ── Producer (parent) ── */
    for (int i = 0; i < NUM_MSGS; i++) {
        /* Wait for slot to be free */
        futex_wait_val(&ch->producer_futex, 0);

        ch->len = snprintf(ch->buf, BUF_SIZE, "message-%d", i);
        atomic_store(&ch->sequence, i);

        /* Signal consumer: data ready */
        futex_set_wake(&ch->producer_futex, 0);
    }

    waitpid(pid, NULL, 0);
    munmap(ch, sizeof(shm_channel_t));
    return 0;
}
```

### 16.4 Clone Syscall Direct Usage

```c
/* clone_direct.c
 * Direct clone(2) usage — no glibc threading abstractions
 * Shows exactly what a thread is at the kernel level
 * Compile: gcc -O2 -o clone_direct clone_direct.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sched.h>
#include <string.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <linux/sched.h>
#include <unistd.h>
#include <stdatomic.h>

#define STACK_SIZE (1024 * 1024)  /* 1MB */

typedef struct {
    int          thread_num;
    atomic_int  *shared_counter;  /* shared because CLONE_VM */
} thread_arg_t;

static int thread_fn(void *arg)
{
    thread_arg_t *targ = arg;

    printf("Thread %d: tid=%d, pid=%d, tgid=%d\n",
           targ->thread_num,
           (int)syscall(SYS_gettid),
           (int)getpid(),
           (int)syscall(SYS_gettid));  /* tgid = parent's pid */

    /* Atomic increment on SHARED counter (same mm!) */
    for (int i = 0; i < 1000; i++)
        atomic_fetch_add(targ->shared_counter, 1);

    return 0;
}

int main(void)
{
    atomic_int shared = 0;
    atomic_init(&shared, 0);

#define NUM_THREADS 4
    void         *stacks[NUM_THREADS];
    pid_t         tids[NUM_THREADS];
    thread_arg_t  args[NUM_THREADS];

    /*
     * Clone flags for "POSIX thread" semantics:
     * CLONE_VM       — share address space (the defining trait)
     * CLONE_FS       — share cwd/root/umask
     * CLONE_FILES    — share file descriptor table
     * CLONE_SIGHAND  — share signal handlers
     * CLONE_THREAD   — same thread group (same tgid)
     * CLONE_SYSVSEM  — share System V semaphore undo list
     * CLONE_SETTLS   — (omitted for simplicity)
     * SIGCHLD        — signal parent on exit
     */
    unsigned long thread_flags =
        CLONE_VM | CLONE_FS | CLONE_FILES |
        CLONE_SIGHAND | CLONE_THREAD | CLONE_SYSVSEM;

    for (int i = 0; i < NUM_THREADS; i++) {
        stacks[i] = malloc(STACK_SIZE);
        if (!stacks[i]) { perror("malloc"); exit(1); }

        args[i].thread_num     = i;
        args[i].shared_counter = &shared;

        /* Stack grows down: pass top of stack */
        void *stack_top = (char *)stacks[i] + STACK_SIZE;

        tids[i] = clone(thread_fn, stack_top, thread_flags, &args[i]);
        if (tids[i] < 0) { perror("clone"); exit(1); }
    }

    /* Wait for all threads using waitpid */
    for (int i = 0; i < NUM_THREADS; i++) {
        /* CLONE_THREAD threads cannot be waited with waitpid!  */
        /* glibc uses a futex on CLONE_CHILD_CLEARTID instead.  */
        /* Here we busy-wait for demonstration:                  */
        int status;
        /* Note: CLONE_THREAD means waitpid WILL fail (ECHILD)  */
        /* Real code uses pthread_join() which uses futex wait   */
    }

    /* Simple spin-wait for illustration */
    struct timespec ts = { .tv_sec = 1 };
    nanosleep(&ts, NULL);

    printf("Main: shared counter = %d (expected %d)\n",
           atomic_load(&shared), NUM_THREADS * 1000);

    for (int i = 0; i < NUM_THREADS; i++)
        free(stacks[i]);

    return 0;
}
```

---

## 17. Go Implementation

Go's goroutines are M:N green threads scheduled by the Go runtime on top of OS threads (`GOMAXPROCS` OS threads by default). The runtime uses `clone(2)` for OS threads internally, and implements cooperative + preemptive scheduling (since Go 1.14).

### 17.1 Goroutine vs OS Thread vs Process

```go
// goroutine_vs_osthread.go
// Demonstrates goroutines, OS thread locking, and process spawning
// go build -race -o goroutine_vs_osthread goroutine_vs_osthread.go

package main

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
	"unsafe"
)

// ── 1. Pure Goroutine Communication (channels) ──────────────────────────────

func goroutineWorker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs {
		// Goroutine is suspended here; another goroutine runs on the OS thread
		// The Go runtime parks this goroutine (futex_wait at runtime level)
		result := job * job
		results <- result
	}
}

func goroutinePool() {
	const numWorkers = runtime.GOMAXPROCS(0)
	jobs := make(chan int, 100)
	results := make(chan int, 100)
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go goroutineWorker(i, jobs, results, &wg)
	}

	// Collector goroutine
	go func() {
		wg.Wait()
		close(results)
	}()

	// Dispatch jobs
	for i := 0; i < 1000; i++ {
		jobs <- i
	}
	close(jobs)

	sum := 0
	for r := range results {
		sum += r
	}
	fmt.Printf("Goroutine pool: sum of squares = %d\n", sum)
}

// ── 2. OS Thread Locking (runtime.LockOSThread) ─────────────────────────────
// Required when using syscalls that are per-thread (namespaces, CPU affinity)

func osThreadBoundWork() {
	done := make(chan struct{})
	go func() {
		// Pin this goroutine to a single OS thread
		// Critical for: seccomp, unshare(), setns(), per-thread capabilities
		runtime.LockOSThread()
		defer runtime.UnlockOSThread()
		defer close(done)

		tid := syscall.Gettid()
		pid := os.Getpid()
		fmt.Printf("OS-thread-locked goroutine: tid=%d pid=%d\n", tid, pid)

		// Set CPU affinity for this specific OS thread
		var cpuset [1024 / 64]uintptr // cpuset for 1024 CPUs
		cpuset[0] = 1                 // CPU 0 only
		_, _, errno := syscall.RawSyscall(
			syscall.SYS_SCHED_SETAFFINITY,
			uintptr(0), // 0 = current thread
			uintptr(unsafe.Sizeof(cpuset)),
			uintptr(unsafe.Pointer(&cpuset)),
		)
		if errno != 0 {
			fmt.Printf("sched_setaffinity: %v\n", errno)
		} else {
			fmt.Println("Pinned to CPU 0")
		}
	}()
	<-done
}

// ── 3. Process Spawning (os/exec) ────────────────────────────────────────────
// Each exec.Cmd uses fork()+exec() internally via syscall.forkAndExecInChild

func processPool() {
	type result struct {
		out []byte
		err error
	}
	results := make(chan result, 4)

	tasks := [][]string{
		{"uname", "-r"},
		{"nproc"},
		{"cat", "/proc/meminfo"},
		{"ls", "/proc/self/fd"},
	}

	for _, args := range tasks {
		args := args
		go func() {
			cmd := exec.Command(args[0], args[1:]...)
			// SysProcAttr lets us control clone() flags
			cmd.SysProcAttr = &syscall.SysProcAttr{
				// Cloneflags: syscall.CLONE_NEWPID | syscall.CLONE_NEWNS,
				// Pdeathsig: syscall.SIGKILL,  // kill child if parent dies
				Setpgid: true, // new process group
			}
			out, err := cmd.Output()
			results <- result{out, err}
		}()
	}

	for range tasks {
		r := <-results
		if r.err == nil {
			fmt.Printf("Process output: %s", r.out[:min(len(r.out), 80)])
		}
	}
}

// ── 4. False Sharing Demonstration ───────────────────────────────────────────

type badCounters struct {
	a int64
	b int64 // same cache line as a!
}

type goodCounters struct {
	a    int64
	_pad [56]byte // force separate cache lines (64-byte alignment)
	b    int64
}

func falseShareBenchmark() {
	const iters = 10_000_000

	// Bad: false sharing
	bad := &badCounters{}
	start := time.Now()
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		for i := 0; i < iters; i++ {
			atomic.AddInt64(&bad.a, 1)
		}
	}()
	go func() {
		defer wg.Done()
		for i := 0; i < iters; i++ {
			atomic.AddInt64(&bad.b, 1)
		}
	}()
	wg.Wait()
	badTime := time.Since(start)

	// Good: no false sharing
	good := &goodCounters{}
	start = time.Now()
	wg.Add(2)
	go func() {
		defer wg.Done()
		for i := 0; i < iters; i++ {
			atomic.AddInt64(&good.a, 1)
		}
	}()
	go func() {
		defer wg.Done()
		for i := 0; i < iters; i++ {
			atomic.AddInt64(&good.b, 1)
		}
	}()
	wg.Wait()
	goodTime := time.Since(start)

	fmt.Printf("False sharing:    %v\n", badTime)
	fmt.Printf("No false sharing: %v\n", goodTime)
	fmt.Printf("Speedup: %.2fx\n", float64(badTime)/float64(goodTime))
}

// ── 5. Go Runtime Internals View ─────────────────────────────────────────────
// G (goroutine) → M (OS thread) → P (processor/scheduler context)
//
// G: runtime.g struct; has its own small stack (2-8KB initial, grows)
// M: runtime.m struct; wraps an OS thread (clone'd by runtime)
// P: runtime.p struct; has a local run queue of Gs
//
// G states: _Grunnable, _Grunning, _Gwaiting, _Gsyscall, _Gdead
// On channel block: G moves to _Gwaiting, M runs another G
// On syscall: M enters syscall, P detaches and finds another M or creates one

func showRuntimeStats() {
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)
	fmt.Printf("\nGo Runtime:\n")
	fmt.Printf("  GOMAXPROCS:      %d\n", runtime.GOMAXPROCS(0))
	fmt.Printf("  NumGoroutine:    %d\n", runtime.NumGoroutine())
	fmt.Printf("  NumCPU:          %d\n", runtime.NumCPU())
	fmt.Printf("  HeapAlloc:       %d KB\n", ms.HeapAlloc/1024)
	fmt.Printf("  NumGC:           %d\n", ms.NumGC)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	fmt.Println("=== Goroutine Pool ===")
	goroutinePool()

	fmt.Println("\n=== OS Thread Locking ===")
	osThreadBoundWork()

	fmt.Println("\n=== Process Pool ===")
	processPool()

	fmt.Println("\n=== False Sharing Benchmark ===")
	falseShareBenchmark()

	showRuntimeStats()
}
```

### 17.2 Go Select and Channel Patterns

```go
// channel_patterns.go
// Advanced channel patterns demonstrating process-equivalent isolation
// and thread-equivalent communication

package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ── Pipeline (goroutines as pipeline stages) ─────────────────────────────────
// Equivalent to: process1 | process2 | process3

func generator(ctx context.Context, nums ...int) <-chan int {
	out := make(chan int, len(nums))
	go func() {
		defer close(out)
		for _, n := range nums {
			select {
			case out <- n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for n := range in {
			select {
			case out <- n * n:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

// ── Fan-out/Fan-in (goroutines as worker pool) ───────────────────────────────
// Analogous to a process pool but zero-copy, shared-memory

func fanOut(ctx context.Context, in <-chan int, n int) []<-chan int {
	chans := make([]<-chan int, n)
	for i := range chans {
		chans[i] = square(ctx, in)
	}
	return chans
}

func fanIn(ctx context.Context, cs ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	merged := make(chan int, 100)

	output := func(c <-chan int) {
		defer wg.Done()
		for v := range c {
			select {
			case merged <- v:
			case <-ctx.Done():
				return
			}
		}
	}

	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}

	go func() {
		wg.Wait()
		close(merged)
	}()
	return merged
}

// ── Semaphore via buffered channel ───────────────────────────────────────────
// Controls parallelism without OS-level process limits

type semaphore chan struct{}

func newSemaphore(n int) semaphore { return make(semaphore, n) }
func (s semaphore) Acquire()       { s <- struct{}{} }
func (s semaphore) Release()       { <-s }

// ── Timeout and cancellation ─────────────────────────────────────────────────
// Goroutines don't have OS-level kill; use context

func expensiveOperation(ctx context.Context, id int) (int, error) {
	done := make(chan int, 1)
	go func() {
		// Simulate work
		time.Sleep(time.Duration(id*10) * time.Millisecond)
		done <- id * id
	}()

	select {
	case result := <-done:
		return result, nil
	case <-ctx.Done():
		return 0, ctx.Err()
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	// Pipeline
	nums := generator(ctx, 2, 3, 4, 5, 6, 7, 8, 9)
	out := square(ctx, nums)
	fmt.Print("Pipeline: ")
	for v := range out {
		fmt.Printf("%d ", v)
	}
	fmt.Println()

	// Controlled parallelism
	sem := newSemaphore(3) // max 3 concurrent
	var wg sync.WaitGroup
	ctx2, cancel2 := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel2()

	for i := 0; i < 10; i++ {
		wg.Add(1)
		i := i
		go func() {
			defer wg.Done()
			sem.Acquire()
			defer sem.Release()
			res, err := expensiveOperation(ctx2, i)
			if err != nil {
				fmt.Printf("op[%d]: %v\n", i, err)
			} else {
				fmt.Printf("op[%d] = %d\n", i, res)
			}
		}()
	}
	wg.Wait()
}
```

---

## 18. Rust Implementation

Rust's ownership model provides compile-time guarantees against data races. `Send` and `Sync` traits encode thread-safety at the type level, and `std::process` wraps `fork`/`exec` safely.

### 18.1 Thread Pool with Rayon and Work Stealing

```rust
// thread_pool.rs
// Demonstrates Rust's threading model, Arc/Mutex, channels, and work stealing
// Cargo.toml: [dependencies] rayon = "1.9", crossbeam = "0.8"

use std::sync::{Arc, Mutex, Condvar};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::thread;
use std::collections::VecDeque;
use std::time::{Duration, Instant};

// ── Type-safe shared state ────────────────────────────────────────────────────
// Arc<Mutex<T>>: heap-allocated T, reference-counted (atomic), mutex-protected
// The compiler ENFORCES that T: Send for Arc<Mutex<T>> to be Send
// No data race is possible at runtime if you follow the type system

type Task = Box<dyn FnOnce() + Send + 'static>;

struct WorkQueue {
    tasks:    VecDeque<Task>,
    shutdown: bool,
}

struct ThreadPool {
    workers:  Vec<thread::JoinHandle<()>>,
    queue:    Arc<(Mutex<WorkQueue>, Condvar)>,
    completed: Arc<AtomicU64>,
}

impl ThreadPool {
    fn new(num_threads: usize) -> Self {
        let queue = Arc::new((
            Mutex::new(WorkQueue { tasks: VecDeque::new(), shutdown: false }),
            Condvar::new(),
        ));
        let completed = Arc::new(AtomicU64::new(0));

        let workers = (0..num_threads).map(|id| {
            let queue = Arc::clone(&queue);
            let completed = Arc::clone(&completed);

            thread::Builder::new()
                .name(format!("worker-{}", id))
                .stack_size(2 * 1024 * 1024)  // 2MB stack
                .spawn(move || {
                    let (lock, cvar) = &*queue;
                    loop {
                        // Condvar::wait releases the MutexGuard and sleeps
                        // → maps to futex(FUTEX_WAIT) in glibc
                        let task = {
                            let mut guard = lock.lock().unwrap();
                            loop {
                                if let Some(task) = guard.tasks.pop_front() {
                                    break Some(task);
                                }
                                if guard.shutdown {
                                    break None;
                                }
                                // Park thread until notified
                                guard = cvar.wait(guard).unwrap();
                            }
                        };

                        match task {
                            Some(f) => {
                                f();
                                completed.fetch_add(1, Ordering::Relaxed);
                            }
                            None => break,
                        }
                    }
                })
                .expect("thread spawn failed")
        }).collect();

        ThreadPool { workers, queue, completed }
    }

    fn submit<F>(&self, f: F)
    where F: FnOnce() + Send + 'static
    {
        let (lock, cvar) = &*self.queue;
        lock.lock().unwrap().tasks.push_back(Box::new(f));
        cvar.notify_one();  // → futex(FUTEX_WAKE, 1)
    }

    fn shutdown(self) -> u64 {
        {
            let (lock, cvar) = &*self.queue;
            lock.lock().unwrap().shutdown = true;
            cvar.notify_all();  // Wake all workers
        }
        for w in self.workers {
            w.join().unwrap();
        }
        self.completed.load(Ordering::SeqCst)
    }
}

// ── Cache-aligned counter (no false sharing) ─────────────────────────────────
#[repr(C, align(64))]
struct AlignedCounter {
    value: AtomicU64,
    _pad:  [u8; 64 - std::mem::size_of::<AtomicU64>()],
}

impl AlignedCounter {
    fn new(v: u64) -> Self {
        AlignedCounter { value: AtomicU64::new(v), _pad: [0; 56] }
    }
}

fn false_sharing_demo() {
    const ITERS: u64 = 10_000_000;

    // BAD: both counters likely on same cache line
    let bad = Arc::new([AtomicU64::new(0), AtomicU64::new(0)]);

    let start = Instant::now();
    let bad_clone = bad.clone();
    let t1 = thread::spawn(move || {
        for _ in 0..ITERS { bad_clone[0].fetch_add(1, Ordering::Relaxed); }
    });
    let bad_clone2 = bad.clone();
    let t2 = thread::spawn(move || {
        for _ in 0..ITERS { bad_clone2[1].fetch_add(1, Ordering::Relaxed); }
    });
    t1.join().unwrap(); t2.join().unwrap();
    let bad_time = start.elapsed();

    // GOOD: 64-byte aligned, different cache lines
    let good = Arc::new([AlignedCounter::new(0), AlignedCounter::new(0)]);

    let start = Instant::now();
    let g1 = good.clone();
    let t3 = thread::spawn(move || {
        for _ in 0..ITERS { g1[0].value.fetch_add(1, Ordering::Relaxed); }
    });
    let g2 = good.clone();
    let t4 = thread::spawn(move || {
        for _ in 0..ITERS { g2[1].value.fetch_add(1, Ordering::Relaxed); }
    });
    t3.join().unwrap(); t4.join().unwrap();
    let good_time = start.elapsed();

    println!("False sharing:    {:?}", bad_time);
    println!("No false sharing: {:?}", good_time);
    println!("Speedup: {:.2}x", bad_time.as_secs_f64() / good_time.as_secs_f64());
}

fn main() {
    let pool = ThreadPool::new(4);

    let start = Instant::now();
    for i in 0..1000u64 {
        pool.submit(move || {
            // CPU-bound work
            let _sum: u64 = (0..i).sum();
        });
    }

    let completed = pool.shutdown();
    println!("ThreadPool: completed {} tasks in {:?}", completed, start.elapsed());

    println!("\nFalse Sharing Demo:");
    false_sharing_demo();
}
```

### 18.2 Process Spawning and IPC in Rust

```rust
// process_ipc.rs
// Process spawning, piped IPC, and signal handling in Rust
// No unsafe code needed for standard process operations

use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio, Child};
use std::sync::{Arc, Mutex};
use std::thread;
use std::os::unix::process::CommandExt;  // Unix-specific extensions

// ── Type-safe process pool ────────────────────────────────────────────────────

struct WorkerProcess {
    child:  Child,
    stdin:  std::process::ChildStdin,
    stdout: BufReader<std::process::ChildStdout>,
}

impl WorkerProcess {
    fn spawn(program: &str) -> std::io::Result<Self> {
        let mut child = Command::new(program)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            // Unix-specific: set process group, deathsig, etc.
            .process_group(0)    // new process group
            // .uid(1000)        // drop privileges
            .spawn()?;

        let stdin  = child.stdin.take().unwrap();
        let stdout = BufReader::new(child.stdout.take().unwrap());

        Ok(WorkerProcess { child, stdin, stdout })
    }

    fn send(&mut self, msg: &str) -> std::io::Result<()> {
        writeln!(self.stdin, "{}", msg)
    }

    fn recv(&mut self) -> std::io::Result<String> {
        let mut line = String::new();
        self.stdout.read_line(&mut line)?;
        Ok(line.trim().to_string())
    }
}

impl Drop for WorkerProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

// ── Shared memory between threads (Arc + Mutex) ───────────────────────────────
// Rust's ownership system makes data races impossible:
// - Arc<Mutex<T>> is the safe wrapper for shared mutable state
// - The compiler prevents sharing non-Send types across threads
// - No equivalent of C's "accidentally share a pointer" — won't compile

fn shared_state_demo() {
    // This is the thread-equivalent of shared memory between processes
    // but with compile-time safety guarantees
    let shared: Arc<Mutex<Vec<u64>>> = Arc::new(Mutex::new(Vec::new()));

    let handles: Vec<_> = (0..4).map(|i| {
        let shared = Arc::clone(&shared);
        thread::spawn(move || {
            let result: u64 = (0..1000u64).map(|x| x * x).sum();
            // Lock is scoped — automatically released when guard drops
            shared.lock().unwrap().push(result + i);
        })
    }).collect();

    for h in handles { h.join().unwrap(); }

    let results = shared.lock().unwrap();
    println!("Shared state: {:?}", *results);
}

// ── Scoped threads (no Arc needed, Rust 1.63+) ───────────────────────────────
// thread::scope ensures threads don't outlive the scope
// → can borrow stack variables without Arc

fn scoped_threads_demo() {
    let data = vec![1u64, 2, 3, 4, 5, 6, 7, 8];
    let chunk_size = data.len() / 4;

    thread::scope(|s| {
        let handles: Vec<_> = data
            .chunks(chunk_size)
            .map(|chunk| {
                // No Arc needed — scope guarantees lifetime
                s.spawn(move || chunk.iter().sum::<u64>())
            })
            .collect();

        let total: u64 = handles.into_iter()
            .map(|h| h.join().unwrap())
            .sum();
        println!("Scoped threads sum: {}", total);
    });
    // All threads guaranteed joined here
}

// ── Channel-based message passing ────────────────────────────────────────────
// std::sync::mpsc: multiple producer, single consumer
// crossbeam::channel: multi-producer, multi-consumer (closer to Go channels)

fn channel_demo() {
    use std::sync::mpsc;

    let (tx, rx) = mpsc::channel::<u64>();

    // Multiple producers
    let handles: Vec<_> = (0..4u64).map(|i| {
        let tx = tx.clone();
        thread::spawn(move || {
            for j in 0..250u64 {
                tx.send(i * 1000 + j).unwrap();
            }
        })
    }).collect();

    // Drop original tx so rx closes when all senders drop
    drop(tx);

    for h in handles { h.join().unwrap(); }

    let sum: u64 = rx.iter().sum();
    println!("Channel sum: {}", sum);
}

fn main() {
    println!("=== Shared State Demo ===");
    shared_state_demo();

    println!("\n=== Scoped Threads Demo ===");
    scoped_threads_demo();

    println!("\n=== Channel Demo ===");
    channel_demo();
}
```

### 18.3 Rust `unsafe` for Linux Syscalls (Advanced)

```rust
// linux_syscalls.rs
// Direct syscall access for process/thread operations
// nix crate recommended for production; raw syscalls for learning

#![allow(unused)]
use std::arch::asm;

// ── Raw clone() syscall ───────────────────────────────────────────────────────
// In practice: use nix::unistd::fork() or std::process::Command

#[cfg(target_arch = "x86_64")]
unsafe fn sys_gettid() -> i32 {
    let tid: i32;
    // SYS_gettid = 186 on x86_64
    // Returns task->pid (the thread's unique ID, NOT the TGID)
    asm!(
        "syscall",
        in("rax") 186usize,   // SYS_gettid
        lateout("rax") tid,
        out("rcx") _,
        out("r11") _,
        options(nostack),
    );
    tid
}

#[cfg(target_arch = "x86_64")]
unsafe fn sys_sched_yield() {
    // SYS_sched_yield = 24
    // Voluntarily relinquish CPU → puts current task at end of CFS queue
    asm!(
        "syscall",
        in("rax") 24usize,
        lateout("rax") _,
        out("rcx") _,
        out("r11") _,
        options(nostack),
    );
}

// ── NUMA-aware memory policy (using nix or raw syscall) ──────────────────────
// SYS_set_mempolicy = 238
// SYS_mbind = 237

const MPOL_BIND: i32 = 2;

#[cfg(target_arch = "x86_64")]
unsafe fn pin_memory_to_node(node: u64) -> Result<(), i64> {
    let nodemask: u64 = 1u64 << node;
    let maxnode: u64 = 64;

    let ret: i64;
    // set_mempolicy(MPOL_BIND, &nodemask, maxnode)
    asm!(
        "syscall",
        in("rax") 238usize,               // SYS_set_mempolicy
        in("rdi") MPOL_BIND as usize,
        in("rsi") &nodemask as *const u64 as usize,
        in("rdx") maxnode as usize,
        lateout("rax") ret,
        out("rcx") _,
        out("r11") _,
        options(nostack),
    );
    if ret < 0 { Err(ret) } else { Ok(()) }
}

fn main() {
    unsafe {
        let tid = sys_gettid();
        println!("TID from raw syscall: {}", tid);
        println!("PID from std:         {}", std::process::id());
        // TID == PID for single-threaded programs

        sys_sched_yield();
        println!("After sched_yield (cooperative thread switch)");
    }
}
```

---

## 19. Benchmarking and Tracing

### 19.1 `perf` — Context Switch Profiling

```bash
# Count context switches per second
perf stat -e context-switches,cpu-migrations,cache-misses \
     -p $(pgrep myapp) sleep 5

# Detailed scheduler analysis
perf sched record -p $(pgrep myapp) sleep 10
perf sched latency    # show wakeup latencies per task
perf sched timehist   # timeline of schedule events

# Flame graph of scheduler decisions
perf record -e sched:sched_switch -ag sleep 10
perf script | stackcollapse-perf.pl | flamegraph.pl > sched.svg
```

### 19.2 `ftrace` — Scheduler and Fork Events

```bash
# Enable scheduler tracing
cd /sys/kernel/debug/tracing
echo 1 > tracing_on
echo "sched_switch sched_wakeup sched_migrate_task" > set_event

# Trace fork/clone calls
echo "syscalls:sys_enter_clone syscalls:sys_enter_fork" >> set_event

cat trace_pipe | grep -E "clone|fork|switch"

# Function graph tracer for copy_process
echo function_graph > current_tracer
echo copy_process > set_graph_function
cat trace_pipe | head -100
```

### 19.3 `bpftrace` — Dynamic Tracing

```bash
# Measure clone() latency (thread creation cost)
bpftrace -e '
tracepoint:syscalls:sys_enter_clone {
    @start[tid] = nsecs;
}
tracepoint:syscalls:sys_exit_clone
/ @start[tid] /
{
    @latency_ns = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}
END { print(@latency_ns); }'

# Track TLB flushes per process switch
bpftrace -e '
kprobe:flush_tlb_mm_range {
    @[comm] = count();
}
interval:s:5 { print(@); clear(@); }'

# Futex contention analysis
bpftrace -e '
tracepoint:syscalls:sys_enter_futex
/ args->op == 0 /  /* FUTEX_WAIT */
{
    @waits[comm] = count();
    @start[tid]  = nsecs;
}
tracepoint:syscalls:sys_exit_futex
/ @start[tid] /
{
    @wait_time_us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'
```

### 19.4 `/proc` Inspection

```bash
# See all threads of a process
ls /proc/<pid>/task/

# Per-thread CPU usage
cat /proc/<pid>/task/<tid>/stat

# Voluntary vs involuntary context switches
cat /proc/<pid>/task/<tid>/status | grep ctxt_switches
# voluntary_ctxt_switches:   I/O wait, mutex sleep
# nonvoluntary_ctxt_switches: preempted by scheduler

# Memory maps (VMA layout)
cat /proc/<pid>/maps
cat /proc/<pid>/smaps_rollup   # aggregate memory stats

# Futex hashing distribution
grep futex /proc/lock_stat    # CONFIG_LOCK_STAT=y required

# NUMA memory placement
cat /proc/<pid>/numa_maps
```

### 19.5 Scheduler Tuning Knobs

```bash
# CFS tuning (affects both processes and threads equally)
# /proc/sys/kernel/sched_*

# Minimum granularity (reduce for lower latency)
echo 500000 > /proc/sys/kernel/sched_min_granularity_ns  # 500μs

# Wakeup granularity (preemption on wakeup)
echo 1000000 > /proc/sys/kernel/sched_wakeup_granularity_ns

# Migration cost (how long to keep tasks on same CPU)
echo 500000 > /proc/sys/kernel/sched_migration_cost_ns

# For latency-sensitive: use SCHED_FIFO or SCHED_RR (RT scheduler)
chrt -f 50 ./myapp    # SCHED_FIFO, priority 50
chrt -r 50 ./myapp    # SCHED_RR,   priority 50

# For throughput: use SCHED_BATCH
chrt -b 0 ./myapp

# NUMA balancing (automatic page migration)
echo 0 > /proc/sys/kernel/numa_balancing   # disable for pinned apps
```

---

## 20. Decision Matrix

### When to Use Processes

```
Criterion                    Use Process When...
────────────────────────     ─────────────────────────────────────────────────────
Fault isolation              A crash must NOT kill other workers
                             → e.g., Chrome's renderer/plugin isolation model

Security isolation           Workers must have different UID, capabilities,
                             seccomp policies, or namespaces
                             → sandboxing untrusted code

Memory independence          Workers have entirely different working sets;
                             COW is acceptable; RSS should not accumulate
                             → each worker processes a separate dataset

Legacy code                  Code is not thread-safe and refactoring is infeasible
                             → integrating old C libraries

execve() needed              Worker needs to run a different binary
                             → shell pipelines, job schedulers

Resource accounting          Per-worker cgroup limits (CPU, memory, I/O)
                             → multi-tenant services

Heap fragmentation           Long-running workers that malloc/free heavily;
                             fork() resets allocator state cleanly

Signal handling              Workers need independent signal dispositions
                             → clean SIGTERM per worker
```

### When to Use Threads

```
Criterion                    Use Thread When...
────────────────────────     ─────────────────────────────────────────────────────
Shared data structures       Workers read/write the same in-memory data
                             → e.g., shared cache, connection pool, task queue

Low latency communication    Data passing must be sub-microsecond
                             → zero-copy, pointer passing, not pipes

Low creation overhead        Workers are short-lived or created frequently
                             → request-per-thread servers, async I/O workers

Fine-grained parallelism     Work items are tiny (microseconds); process
                             overhead would dominate

NUMA / cache locality        Workers must share L3 cache on same socket
                             → NUMA-aware computation

File descriptor sharing      Workers serve the same listening socket
                             (SO_REUSEPORT, or accept() from shared fd)

GPU/device sharing           cudaStream_t, io_uring rings shared
                             across workers
```

### Hybrid Architectures

```
Multi-process + Multi-thread (most production systems):

  Master Process
  ├── Process 1 (worker, isolated namespace)
  │   ├── Thread A (network I/O, epoll)
  │   ├── Thread B (CPU compute)
  │   └── Thread C (disk I/O, io_uring)
  ├── Process 2 (worker)
  │   └── (same thread structure)
  └── Process N (worker)

Examples:
  nginx:   1 master + N worker processes, each single-threaded
  Apache:  MPM worker: N processes × M threads
  PostgreSQL: 1 postmaster + N backend processes (historically no threads)
  Chrome:   1 browser process + N renderer processes + N GPU process
  Envoy:    1 process + N worker threads (1 per CPU)
```

### Summary Decision Table

```
Factor                   Process     Thread      Goroutine   Notes
──────────────────────── ─────────── ─────────── ─────────── ──────────────────────
Creation cost            High        Medium      Very low    fork>clone>runtime
Memory overhead          High (COW)  Low (stack) Very low    2KB initial goroutine
Context switch           Medium      Low         Very low    TLB flush main factor
Communication latency    High (IPC)  Low (mutex) Low (chan)  Goroutine = Go chan
Data sharing             Explicit    Implicit    Explicit    Go enforces via chan
Fault isolation          Full        None        None        Panic kills all goros
Security isolation       Full        Partial     None        cred, ns, seccomp
Scalability              100s        1000s       Millions    Go M:N scheduling
Scheduling               Kernel CFS  Kernel CFS  Go runtime  Both fair
TLB behavior             Flush/PCID  No flush    No flush    (threads/goros same mm)
False sharing risk       None        High        High        Pad to 64 bytes
Signal handling          Full POSIX  Complex     N/A         Go uses channels
Namespace support        Full        No          No          unshare() per process
Debug complexity         Lower       Higher      Medium      Race detector in Go/Rust
```

---

## References

### Kernel Source Files
- `kernel/fork.c` — `copy_process()`, `kernel_clone()`
- `kernel/sched/core.c` — `__schedule()`, `context_switch()`
- `kernel/sched/fair.c` — CFS implementation, `pick_next_task_fair()`
- `include/linux/sched.h` — `task_struct`, `sched_entity`
- `include/linux/mm_types.h` — `mm_struct`, `vm_area_struct`
- `include/linux/fdtable.h` — `files_struct`, `fdtable`
- `mm/memory.c` — `do_wp_page()` (COW fault handler)
- `mm/fork.c` — `dup_mmap()`, `dup_mm()`
- `arch/x86/kernel/process_64.c` — `__switch_to()`
- `arch/x86/mm/tlb.c` — TLB management, PCID
- `kernel/futex/futex.c` — futex implementation
- `include/uapi/linux/sched.h` — clone flags
- `fs/pipe.c` — pipe implementation
- `include/linux/nsproxy.h` — namespace proxy

### Documentation
- `Documentation/scheduler/sched-design-CFS.rst`
- `Documentation/scheduler/sched-domains.rst`
- `Documentation/admin-guide/mm/numa_memory_policy.rst`
- `Documentation/core-api/futex.rst`
- `Documentation/security/credentials.rst`

### External References
- LWN: *"Anatomy of a system call"* (series)
- LWN: *"Kernel threads and process groups"*
- LWN: *"The PCID feature"* (v4.14)
- Robert Love, *Linux Kernel Development*, 3rd ed., Ch. 3, 15
- Ulrich Drepper, *"Futexes Are Tricky"*
- Linux man pages: `clone(2)`, `fork(2)`, `futex(2)`, `pthread_create(3)`

Here's a summary of what's covered in the guide:

**Kernel internals (sections 1–9):** Starts from the axiom that Linux has no "thread" primitive — only `task_struct` with varying `clone()` flags. Walks through `copy_process()`, COW via `do_wp_page()`, `mm_struct` reference counting (`mm_users` vs `mm_count`), how `pthread_create()` maps to `clone(CLONE_VM|CLONE_FILES|...)`, and the critical difference in `files_struct` sharing that makes `close()` dangerous across threads.

**Performance internals (sections 10–14):** Futex fast/slow paths with the exact syscall path, CFS scheduling (both process/thread treated identically in the rb-tree), context switch anatomy (`switch_mm_irqs_off()` → CR3 reload only on process switch), PCID behavior since v4.14, TLB miss cost chain, NUMA topology and cache-line false sharing with padding strategies.

**Security (section 15):** Namespace isolation (why threads can't have per-thread namespaces), `seccomp` being per-`task_struct` not per-group, `struct cred` independence, and fault containment differences.

**Implementations:**
- **C**: fork-based process pool with pipe IPC, SPSC lock-free thread pool using raw `futex(2)` syscalls, POSIX shm + futex cross-process channel, and direct `clone(2)` usage showing exactly what flags define a thread.
- **Go**: goroutine pool, `runtime.LockOSThread()` for per-thread syscalls (affinity, seccomp, `setns`), `os/exec` with `SysProcAttr`, false-sharing benchmark, and a note on the G/M/P scheduler model.
- **Rust**: type-safe thread pool using `Arc<Mutex<>>` + `Condvar` (maps to futex), `#[repr(align(64))]` for false-sharing prevention, scoped threads (Rust 1.63+), and raw `asm!` for direct syscalls.

**Tracing (section 19):** Ready-to-run `perf sched`, `ftrace` function graph on `copy_process`, and `bpftrace` one-liners for clone latency, TLB flushes, and futex contention.