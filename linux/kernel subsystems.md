# Linux Kernel Subsystems — Complete Comprehensive Guide
> "The kernel is not magic. It is pure logic, layered with precision."  
> A world-class reference for systems programmers mastering the Linux kernel.

---

## Table of Contents

1. [Introduction to the Linux Kernel Architecture](#1-introduction)
2. [Process Management Subsystem](#2-process-management)
3. [CPU Scheduling Subsystem](#3-cpu-scheduling)
4. [Memory Management Subsystem](#4-memory-management)
5. [Virtual File System (VFS)](#5-virtual-file-system)
6. [Block I/O Subsystem](#6-block-io)
7. [Network Subsystem](#7-network-subsystem)
8. [Inter-Process Communication (IPC)](#8-ipc)
9. [Interrupt & Exception Handling](#9-interrupt-handling)
10. [System Call Interface](#10-system-calls)
11. [Device Driver Model](#11-device-drivers)
12. [Synchronization Primitives](#12-synchronization)
13. [Security Subsystem (LSM)](#13-security)
14. [Power Management](#14-power-management)
15. [Kernel Debugging & Tracing](#15-debugging-tracing)

---

# 1. Introduction to the Linux Kernel Architecture

## 1.1 What Is the Kernel?

The **kernel** is the core of an operating system. It is the bridge between hardware and user-space software. It manages:
- CPU time allocation (who runs when)
- Memory (who owns what RAM)
- Devices (how data flows to/from hardware)
- Files (how data is stored and retrieved)
- Security (who can do what)

> **Concept — Privilege Levels (Rings):**  
> Modern CPUs have hardware-enforced privilege levels called "rings."  
> - **Ring 0** = Kernel mode (full hardware access, unlimited privilege)  
> - **Ring 3** = User mode (restricted, must ask kernel for resources)  
> When a user program wants to read a file, it cannot do it directly — it makes a **system call**, which crosses the ring boundary into kernel mode.

---

## 1.2 Kernel Architecture: Monolithic vs Microkernel

```
MONOLITHIC KERNEL (Linux)
============================================================
+----------------------------------------------------------+
|                    USER SPACE                            |
|  bash  |  vim  |  nginx  |  python  |  rust binary      |
+----------------------------------------------------------+
          |  System Call Interface (ABI boundary)  |
+----------------------------------------------------------+
|                   KERNEL SPACE                           |
|                                                          |
|  +-------------+  +-------------+  +-----------------+  |
|  |  Process    |  |   Memory    |  |  File System    |  |
|  |  Management |  |  Management |  |  (VFS, ext4...) |  |
|  +-------------+  +-------------+  +-----------------+  |
|  +-------------+  +-------------+  +-----------------+  |
|  |  Network    |  |  IPC        |  |  Device Drivers |  |
|  |  Stack      |  |  (pipes,    |  |  (char, block,  |  |
|  |  (TCP/IP)   |  |   sockets)  |  |   network)      |  |
|  +-------------+  +-------------+  +-----------------+  |
|  +------------------------------------------------------+|
|  |         Synchronization Primitives (locks, RCU)     ||
|  +------------------------------------------------------+|
|  +------------------------------------------------------+|
|  |         Hardware Abstraction Layer (HAL)             ||
|  +------------------------------------------------------+|
+----------------------------------------------------------+
          |           Hardware                    |
+----------------------------------------------------------+
|  CPU  |  RAM  |  NIC  |  Disk  |  USB  |  GPU  |  etc. |
+----------------------------------------------------------+
```

---

## 1.3 Kernel Data Flow — The Big Picture

```
USER PROGRAM
     |
     | (1) Makes system call: read(fd, buf, n)
     v
SYSCALL INTERFACE  <----  architecture-specific entry (x86: syscall instruction)
     |
     | (2) Dispatches to sys_read()
     v
VFS LAYER  (Virtual File System)
     |
     | (3) Resolves file descriptor -> inode -> file operations
     v
FILE SYSTEM (ext4, btrfs, tmpfs...)
     |
     | (4) Translates logical offset -> physical block
     v
BLOCK I/O LAYER
     |
     | (5) I/O scheduler queues request
     v
DEVICE DRIVER
     |
     | (6) Sends DMA request to hardware
     v
PHYSICAL HARDWARE (SSD, HDD, NVMe)
     |
     | (7) IRQ fires when data ready
     v
INTERRUPT HANDLER -> wakes sleeping process
     |
     v
SCHEDULER puts process back on run queue
     |
     v
USER PROGRAM receives data in buffer
```

---

## 1.4 Kernel Source Tree Layout

```
linux/
├── arch/           # Architecture-specific code (x86, arm64, riscv...)
│   └── x86/
│       ├── entry/  # Syscall/interrupt entry points (assembly)
│       ├── mm/     # x86 memory management (paging, TLB)
│       └── kernel/ # x86 CPU management
├── kernel/         # Core subsystem (scheduler, signals, timers)
├── mm/             # Memory management (buddy, slab, vmalloc)
├── fs/             # File systems (VFS, ext4, btrfs, proc, sysfs)
├── net/            # Networking (socket, TCP/IP, netfilter)
├── drivers/        # Device drivers (thousands of files)
├── ipc/            # IPC mechanisms (semaphores, shared mem, msg queues)
├── security/       # LSM, SELinux, AppArmor
├── block/          # Block I/O layer, I/O schedulers
├── include/        # Kernel headers (linux/*, asm/*)
├── init/           # Kernel initialization (main.c, start_kernel)
├── lib/            # Generic utilities (list, rbtree, hash tables)
└── Documentation/  # Kernel documentation
```

---

# 2. Process Management Subsystem

## 2.1 What Is a Process?

A **process** is an instance of a running program. It is the fundamental unit of work in a Unix system.

> **Concept — Process vs Thread vs Task:**  
> - **Process**: Independent execution unit with its own address space, file descriptors, and signal handlers.  
> - **Thread**: Shares address space and file descriptors with its parent process but has its own stack and CPU state.  
> - **Task**: The kernel's internal abstraction for both processes and threads — stored as `struct task_struct`.

The Linux kernel treats processes and threads uniformly through `struct task_struct`.

---

## 2.2 `struct task_struct` — The Heart of Process Management

Every process/thread in Linux is represented by `struct task_struct` (defined in `include/linux/sched.h`). It is enormous (~800+ fields), but here are the critical ones:

```c
/* include/linux/sched.h (simplified for study) */
struct task_struct {
    /*
     * STATE MACHINE
     * A process is always in one of these states.
     */
    volatile long           state;        /* TASK_RUNNING, TASK_INTERRUPTIBLE, etc. */
    int                     exit_state;   /* EXIT_ZOMBIE, EXIT_DEAD */

    /*
     * IDENTITY
     */
    pid_t                   pid;          /* Process ID */
    pid_t                   tgid;         /* Thread Group ID (= pid for main thread) */
    char                    comm[TASK_COMM_LEN]; /* Process name (e.g., "bash") */

    /*
     * RELATIONSHIPS (process tree)
     */
    struct task_struct      *parent;      /* Parent process */
    struct list_head        children;     /* List of child processes */
    struct list_head        sibling;      /* Link in parent's children list */

    /*
     * CREDENTIALS (security)
     */
    kuid_t                  uid, euid;    /* Real/effective user ID */
    kgid_t                  gid, egid;   /* Real/effective group ID */

    /*
     * MEMORY
     */
    struct mm_struct        *mm;          /* Virtual memory descriptor (NULL for kernel threads) */
    struct mm_struct        *active_mm;   /* Active mm (for kernel threads, borrows one) */

    /*
     * SCHEDULING
     */
    int                     prio;         /* Dynamic priority */
    int                     static_prio;  /* Nice-value-based static priority */
    unsigned int            policy;       /* SCHED_NORMAL, SCHED_FIFO, SCHED_RR, etc. */
    struct sched_entity     se;           /* CFS scheduling entity */
    int                     on_cpu;       /* Currently executing on a CPU? */
    int                     on_rq;        /* On the run queue? */

    /*
     * FILE SYSTEM
     */
    struct fs_struct        *fs;          /* Root/current working directory */
    struct files_struct     *files;       /* Open file descriptors table */

    /*
     * SIGNALS
     */
    struct signal_struct    *signal;      /* Shared signal state (for threads) */
    struct sighand_struct   *sighand;     /* Signal handlers */
    sigset_t                blocked;      /* Blocked signals bitmask */
    struct sigpending       pending;      /* Pending signals */

    /*
     * CPU CONTEXT (registers saved on context switch)
     */
    struct thread_struct    thread;       /* Architecture-specific CPU state */

    /*
     * KERNEL STACK
     * Every task has a fixed-size kernel stack (typically 8KB or 16KB).
     */
    void                    *stack;       /* Pointer to kernel stack */
};
```

---

## 2.3 Process States — The State Machine

```
                    PROCESS STATE MACHINE
    ============================================================

         fork()                              exit()
    NEW --------> TASK_RUNNING <---------+---------> EXIT_ZOMBIE
                  (Runnable)             |              |
                     |                  |           wait() by
                  scheduler             |            parent
                  picks it              |              |
                     |                  |              v
                     v                  |           EXIT_DEAD
                  TASK_RUNNING       wake up       (reaped)
                  (On CPU)           signal/
                     |               event
            I/O, sleep,              |
            wait for event           |
                     |               |
                     v               |
            TASK_INTERRUPTIBLE ------+   <-- can be woken by signal
            TASK_UNINTERRUPTIBLE ---+    <-- CANNOT be woken by signal
            (deep sleep, e.g.,           (e.g., waiting for disk I/O)
             waiting for mutex)
                     |
              SIGSTOP received
                     |
                     v
              TASK_STOPPED
                     |
              SIGCONT received
                     |
                     +-----------> back to TASK_RUNNING

    KEY STATE VALUES:
    ---------------------------------------------------------
    TASK_RUNNING         = 0x0000  (runnable or running)
    TASK_INTERRUPTIBLE   = 0x0001  (sleeping, wakes on signal)
    TASK_UNINTERRUPTIBLE = 0x0002  (sleeping, ignores signal)
    __TASK_STOPPED       = 0x0004  (stopped by signal)
    __TASK_TRACED        = 0x0008  (being ptrace'd)
    EXIT_DEAD            = 0x0010  (fully dead)
    EXIT_ZOMBIE          = 0x0020  (dead but not yet reaped)
    TASK_PARKED          = 0x0040  (kthread parked)
    TASK_DEAD            = 0x0080  (dead task, do not schedule)
```

---

## 2.4 Process Creation: `fork()`, `clone()`, `exec()`

### The `fork()` System Call

```
FORK() MECHANICS
==============================================================

Parent Process                          Child Process
+--------------------+                 +--------------------+
| task_struct        |    fork()        | task_struct (copy) |
| pid = 1000         | ------------->   | pid = 1001         |
| mm_struct -------->|                 | mm_struct (COW) -->|
|                    |                 |                    |
| Page Table         |                 | Page Table (copy)  |
|   VA -> PA         |                 |   VA -> PA (same!) |
|   (marked R/O)     |                 |   (marked R/O)     |
+--------------------+                 +--------------------+
         |                                      |
         v                                      v
    Physical Memory Pages (SHARED until one writes)
    +--------------------------------------------------+
    |  Page A  |  Page B  |  Page C  |  Page D  | ... |
    +--------------------------------------------------+
              ^                  ^
              |                  |
    Both parent and child point to same pages (Copy-On-Write)

    When child WRITES to Page B:
    ================================================
    1. CPU triggers page fault (page is read-only)
    2. Kernel allocates NEW page B'
    3. Copies content of Page B -> Page B'
    4. Updates child's page table: VA -> Page B'
    5. Marks both pages writable again
    6. Execution resumes transparently
```

> **Concept — Copy-On-Write (COW):**  
> When `fork()` is called, instead of copying all memory immediately (which would be slow), the kernel marks all pages as read-only and shared. Only when either process writes to a page does the kernel create a private copy. This is COW and makes `fork()` + `exec()` extremely efficient.

### C Implementation: Creating a Process

```c
/*
 * process_create.c
 * Demonstrates fork(), exec(), wait(), and proper zombie reaping.
 *
 * Compile: gcc -O2 -Wall -o process_create process_create.c
 */

#include 
#include 
#include     /* fork, execve, getpid */
#include <sys/wait.h>  /* waitpid, WIFEXITED, WEXITSTATUS */
#include <sys/types.h>
#include 
#include 

/*
 * safe_fork() - Fork with error handling.
 * Returns child PID to parent, 0 to child.
 */
static pid_t safe_fork(void)
{
    pid_t pid = fork();
    if (pid < 0) {
        fprintf(stderr, "fork() failed: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    return pid;
}

/*
 * demonstrate_fork_exec()
 * Classic Unix pattern: fork a child, then exec a new program.
 * This is exactly how your shell works.
 */
static void demonstrate_fork_exec(void)
{
    pid_t child_pid;
    int   status;
    int   exit_code;

    printf("[Parent PID=%d] About to fork...\n", getpid());

    child_pid = safe_fork();

    if (child_pid == 0) {
        /*
         * ============ CHILD PROCESS ============
         * fork() returns 0 in the child.
         * The child has a COPY of parent's address space.
         * We immediately exec() to replace image with /bin/ls.
         */
        printf("[Child  PID=%d] I am the child. Parent is %d\n",
               getpid(), getppid());

        /* execve() replaces current process image with a new program.
         * On success, it does NOT return.
         * argv[0] is conventionally the program name itself. */
        char *argv[] = { "ls", "-la", "/tmp", NULL };
        char *envp[] = { "PATH=/usr/bin:/bin", NULL };

        execve("/bin/ls", argv, envp);

        /* If we reach here, execve() failed */
        fprintf(stderr, "[Child] execve failed: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    /*
     * ============ PARENT PROCESS ============
     * fork() returns child's PID to the parent.
     */
    printf("[Parent PID=%d] Forked child with PID=%d\n",
           getpid(), child_pid);

    /*
     * waitpid() blocks until the child exits.
     * This is CRITICAL — without it, the child becomes a ZOMBIE.
     *
     * A zombie is a process that has exited but whose exit status
     * has not yet been collected by the parent. It consumes a PID
     * and a task_struct entry in the kernel.
     */
    if (waitpid(child_pid, &status, 0) == -1) {
        fprintf(stderr, "waitpid() failed: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    if (WIFEXITED(status)) {
        exit_code = WEXITSTATUS(status);
        printf("[Parent] Child %d exited normally with code %d\n",
               child_pid, exit_code);
    } else if (WIFSIGNALED(status)) {
        printf("[Parent] Child %d was killed by signal %d\n",
               child_pid, WTERMSIG(status));
    }
}

/*
 * demonstrate_vfork()
 * vfork() is a special case: child shares parent's address space
 * (NO copy at all, not even COW). Parent is SUSPENDED until child
 * calls exec() or _exit(). Used in performance-critical paths.
 * Modern code uses posix_spawn() instead.
 */
static void demonstrate_vfork(void)
{
    pid_t pid;

    printf("\n[vfork demo]\n");

    pid = vfork();
    if (pid < 0) {
        perror("vfork");
        return;
    }

    if (pid == 0) {
        /* MUST call _exit(), not exit(), to avoid flushing parent's stdio */
        printf("[vfork child PID=%d] Running\n", getpid());
        _exit(0);
    }

    printf("[vfork parent] Child done, continuing\n");
}

/*
 * demonstrate_clone()
 * clone() is the raw system call beneath both fork() and pthread_create().
 * It allows fine-grained control over what is shared between parent and child.
 */
#define _GNU_SOURCE
#include 

#define STACK_SIZE (1024 * 1024) /* 1 MB stack for new thread */

static int thread_function(void *arg)
{
    printf("[clone thread PID=%d] Arg = %s\n",
           getpid(), (char *)arg);
    return 0;
}

static void demonstrate_clone(void)
{
    char  *stack;
    char  *stack_top;
    pid_t  child_pid;
    int    status;

    printf("\n[clone demo]\n");

    /* Allocate stack for new thread (stacks grow down, so use top) */
    stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc");
        return;
    }
    stack_top = stack + STACK_SIZE;

    /*
     * CLONE_VM    : Share virtual memory (like threads)
     * CLONE_FS    : Share filesystem (cwd, root)
     * CLONE_FILES : Share file descriptor table
     * CLONE_SIGHAND: Share signal handlers
     * SIGCHLD     : Send SIGCHLD to parent on exit (for wait())
     */
    child_pid = clone(
        thread_function,
        stack_top,
        CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | SIGCHLD,
        "hello from clone"
    );

    if (child_pid < 0) {
        perror("clone");
        free(stack);
        return;
    }

    waitpid(child_pid, &status, 0);
    printf("[clone parent] clone-child exited with %d\n",
           WEXITSTATUS(status));
    free(stack);
}

int main(void)
{
    printf("=== Linux Process Creation Demo ===\n\n");
    demonstrate_fork_exec();
    demonstrate_vfork();
    demonstrate_clone();
    return EXIT_SUCCESS;
}
```

### Rust Implementation: Spawning Processes

```rust
// process_management.rs
// Demonstrates process creation and management in Rust.
// Rust's std::process provides safe wrappers around fork/exec/wait.
//
// Run: cargo run

use std::process::{Command, Stdio, Child};
use std::io::{self, Read, Write};

/// spawn_and_wait() - Fork + exec + wait pattern in idiomatic Rust.
/// Rust's Command is the safe, ergonomic API over fork/exec.
fn spawn_and_wait() -> io::Result {
    println!("\n=== Spawn and Wait Demo ===");

    // Command::new() prepares a fork+exec.
    // .args() sets argv[1..] for the child.
    // .stdout(Stdio::piped()) connects child's stdout to a pipe
    //   so the parent can read it.
    let mut child: Child = Command::new("/bin/ls")
        .args(["-la", "/tmp"])
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?;  // This calls fork() + exec() internally

    // Read child's stdout from the pipe.
    // The child's stdout is connected to a pipe; we read from our end.
    let mut output = String::new();
    if let Some(mut stdout) = child.stdout.take() {
        stdout.read_to_string(&mut output)?;
    }

    // wait() collects the exit status, preventing zombies.
    let status = child.wait()?;

    println!("Child exited with: {:?}", status.code());
    println!("First 200 chars of output:\n{}", &output[..output.len().min(200)]);

    Ok(())
}

/// spawn_with_stdin() - Demonstrates bidirectional pipe with child.
fn spawn_with_stdin() -> io::Result {
    println!("\n=== Stdin Pipe Demo ===");

    // Spawn 'cat' with both stdin and stdout piped.
    let mut child = Command::new("/bin/cat")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;

    // Write to child's stdin.
    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(b"Hello from Rust parent!\n")?;
        // stdin dropped here, closing the write end of the pipe.
        // This sends EOF to cat, causing it to exit.
    }

    // Read echo from child's stdout.
    let mut output = String::new();
    if let Some(mut stdout) = child.stdout.take() {
        stdout.read_to_string(&mut output)?;
    }

    child.wait()?;
    println!("Received from child: {}", output.trim());

    Ok(())
}

/// spawn_multiple() - Fork-join pattern: spawn N children, collect all results.
/// This is the kernel-level parallel process model.
fn spawn_multiple() -> io::Result {
    println!("\n=== Fork-Join Pattern ===");

    let commands = vec![
        ("uname", vec!["-r"]),
        ("hostname", vec![]),
        ("id", vec![]),
    ];

    // Spawn all children first (parallel execution begins).
    let children: Vec = commands
        .into_iter()
        .map(|(cmd, args)| {
            let child = Command::new(cmd)
                .args(&args)
                .stdout(Stdio::piped())
                .spawn()
                .expect("spawn failed");
            (cmd.to_string(), child)
        })
        .collect();

    // Now wait for each child (join phase).
    for (name, mut child) in children {
        let mut out = String::new();
        if let Some(mut s) = child.stdout.take() {
            s.read_to_string(&mut out)?;
        }
        child.wait()?;
        println!("{}: {}", name, out.trim());
    }

    Ok(())
}

fn main() -> io::Result {
    println!("=== Rust Process Management Demo ===");
    println!("PID: {}", std::process::id());

    spawn_and_wait()?;
    spawn_with_stdin()?;
    spawn_multiple()?;

    Ok(())
}
```

---

## 2.5 Process Namespaces — The Foundation of Containers

> **Concept — Namespace:**  
> A namespace wraps a global system resource in an abstraction layer, making it appear as if a process has its own isolated instance of that resource.  
> Docker and Kubernetes containers are just processes living in isolated namespaces.

```
LINUX NAMESPACE TYPES
==============================================================

Namespace    | Flag           | What it Isolates
-------------|----------------|----------------------------------
Mount (mnt)  | CLONE_NEWNS    | Mount points, file system tree
UTS          | CLONE_NEWUTS   | Hostname and domain name
IPC          | CLONE_NEWIPC   | SysV IPC, POSIX msg queues
PID          | CLONE_NEWPID   | Process ID numbers (PID 1 in container)
Network (net)| CLONE_NEWNET   | Network interfaces, routes, firewall rules
User         | CLONE_NEWUSER  | User/group IDs (UID/GID mapping)
Cgroup       | CLONE_NEWCGROUP| cgroup root directory (resource limits)
Time         | CLONE_NEWTIME  | Boot and monotonic clocks

NAMESPACE HIERARCHY EXAMPLE:
==============================================================

  [Host Namespace]
  PID=1 (systemd)
  PID=1234 (container runtime)
       |
       | clone(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS)
       |
  [Container Namespace]
  PID=1 (nginx inside container)  <-- sees itself as PID 1
  PID=2 (worker process)
  |
  | From HOST perspective, these are actually PID 5001, 5002
  | The namespace creates an illusion of isolation.
```

```c
/*
 * namespace_demo.c
 * Creates a new PID namespace and runs a shell inside it.
 * The shell sees itself as PID 1.
 *
 * Must run as root (or with CAP_SYS_ADMIN):
 *   sudo ./namespace_demo
 */

#define _GNU_SOURCE
#include 
#include 
#include 
#include <sys/wait.h>
#include <sys/types.h>
#include 
#include 
#include 

#define STACK_SIZE (1024 * 1024)

/*
 * child_main() - This function runs in the new namespace.
 * From its perspective, it is PID 1.
 */
static int child_main(void *arg)
{
    (void)arg;

    printf("[Child in new PID namespace] My PID = %d\n", getpid());
    printf("[Child] Parent PID = %d\n", getppid());

    /*
     * The child sees PID=1 here, even though from the host
     * it has a higher PID number.
     */

    /* Execute a shell inside the namespace */
    char *argv[] = { "/bin/sh", NULL };
    char *envp[] = { "PS1=[container]# ", "PATH=/bin:/usr/bin", NULL };
    execve("/bin/sh", argv, envp);

    fprintf(stderr, "execve failed: %s\n", strerror(errno));
    return EXIT_FAILURE;
}

int main(void)
{
    char  *stack;
    char  *stack_top;
    pid_t  child_pid;

    printf("[Host] My PID = %d\n", getpid());

    stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc");
        return EXIT_FAILURE;
    }
    stack_top = stack + STACK_SIZE;

    /*
     * CLONE_NEWPID: New PID namespace (child becomes PID 1)
     * CLONE_NEWUTS: New hostname namespace
     * SIGCHLD:      Notify parent when child exits
     */
    child_pid = clone(
        child_main,
        stack_top,
        CLONE_NEWPID | CLONE_NEWUTS | SIGCHLD,
        NULL
    );

    if (child_pid < 0) {
        perror("clone (need root/CAP_SYS_ADMIN)");
        free(stack);
        return EXIT_FAILURE;
    }

    printf("[Host] Created container process with host-PID=%d\n", child_pid);

    waitpid(child_pid, NULL, 0);
    printf("[Host] Container exited.\n");

    free(stack);
    return EXIT_SUCCESS;
}
```

---

# 3. CPU Scheduling Subsystem

## 3.1 What Is Scheduling?

The scheduler decides **which process runs on which CPU at what time**. This is one of the most critical and sophisticated components of the kernel.

> **Concept — Preemption:**  
> In a preemptive kernel, the scheduler can forcibly remove a running process from the CPU (preempt it) even if the process has not voluntarily yielded. This ensures low-latency response for high-priority tasks.  
> - **Non-preemptive (cooperative)**: Process runs until it voluntarily yields. Simple but dangerous (one infinite loop freezes the system).  
> - **Preemptive**: Timer interrupt fires, scheduler decides to switch. Used by Linux.

---

## 3.2 Scheduling Classes — The Priority Hierarchy

Linux uses a **modular scheduling class** design. Each class handles a different workload:

```
SCHEDULING CLASS HIERARCHY (highest priority first)
==============================================================

Priority
  ^
  |   [STOP] - stop_sched_class
  |   Used only for per-CPU stop tasks (e.g., migration).
  |   Always runs if runnable. Priority: 0 (max)
  |
  |   [DEADLINE] - dl_sched_class
  |   For tasks with hard real-time deadlines (EDF algorithm).
  |   SCHED_DEADLINE policy.
  |   Example: audio/video codecs with strict timing.
  |
  |   [RT] - rt_sched_class
  |   Real-time tasks (SCHED_FIFO, SCHED_RR).
  |   Priority 1-99. FIFO: run until block/yield.
  |   RR: run for timeslice, then rotate.
  |   Example: kernel drivers, multimedia daemons.
  |
  |   [FAIR] - fair_sched_class  ← 99% of user processes use this
  |   CFS (Completely Fair Scheduler). SCHED_NORMAL, SCHED_BATCH.
  |   Uses red-black tree ordered by virtual runtime.
  |
  v   [IDLE] - idle_sched_class
      Runs the 'idle' process when CPU has nothing to do.
      Executes 'hlt' instruction on x86 to save power.

==============================================================
Key insight: The kernel tries each class in order. If the
higher-priority class has a runnable task, it wins.
```

---

## 3.3 CFS — Completely Fair Scheduler

CFS is the default scheduler for normal processes. Its goal: every process should get an **equal share of CPU time, weighted by priority (nice value)**.

> **Concept — Virtual Runtime (vruntime):**  
> CFS tracks how much CPU time each process has received, adjusted by its weight (priority).  
> `vruntime += actual_runtime * (NICE_0_LOAD / task_weight)`  
> A higher-priority task has higher weight, so it accumulates vruntime **slower** — meaning it stays at the left of the tree and gets picked more often.

```
CFS RED-BLACK TREE (Run Queue per CPU)
==============================================================

Each runnable process is a node in a red-black tree.
The KEY is vruntime (virtual runtime).
CFS always picks the LEFTMOST node (smallest vruntime = least CPU time).

              [40ms vruntime]
             /               \
      [20ms]                 [60ms]
      /    \                 /    \
  [10ms]  [30ms]         [50ms]  [70ms]
     ^
     |
  Next task to run (smallest vruntime)

When a task runs:
1. Its vruntime increases.
2. It may no longer be the leftmost node.
3. Scheduler picks the new leftmost node.

This ensures NO task is starved — all tasks' vruntimes
converge toward the same value over time (hence "fair").

PRIORITY (NICE VALUE) EFFECT:
==============================================================
Nice -20 (highest priority):  weight = 88761  (vruntime grows slowly)
Nice   0 (default):           weight = 1024   (vruntime grows at 1x)
Nice +19 (lowest priority):   weight = 15     (vruntime grows fast)

A nice=-20 task accumulates vruntime ~88x slower than nice=+19,
meaning it gets ~88x more CPU time.
```

---

## 3.4 The Run Queue: `struct rq`

```c
/*
 * kernel/sched/core.c (simplified)
 * Each CPU has its own run queue (struct rq).
 * This avoids locking between CPUs for most operations.
 */
struct rq {
    raw_spinlock_t      lock;           /* Protects this rq */
    unsigned int        nr_running;     /* Number of runnable tasks */
    u64                 clock;          /* Per-CPU clock */
    u64                 clock_task;     /* Clock accounting task time */

    struct cfs_rq       cfs;            /* CFS run queue */
    struct rt_rq        rt;             /* RT run queue */
    struct dl_rq        dl;             /* Deadline run queue */

    struct task_struct  *curr;          /* Currently running task */
    struct task_struct  *idle;          /* Idle task for this CPU */
    struct task_struct  *stop;          /* Highest-priority stop task */

    /* Load balancing */
    unsigned long       cpu_load[5];    /* Load averages (1,4,16,64,256 ticks) */
    struct list_head    cfs_tasks;      /* CFS task list for load balancing */
};

/* CFS run queue */
struct cfs_rq {
    struct load_weight  load;           /* Total weight of all tasks */
    unsigned int        nr_running;     /* Number of CFS tasks */

    u64                 min_vruntime;   /* Minimum vruntime on this rq */

    struct rb_root_cached tasks_timeline; /* Red-black tree of tasks by vruntime */
    struct sched_entity *curr;          /* Currently running CFS entity */
    struct sched_entity *next;          /* Pre-selected next task (wakeup) */
    struct sched_entity *last;          /* Last task that ran (for buddy preemption) */
};
```

---

## 3.5 Context Switch — The Mechanism

```
CONTEXT SWITCH FLOW
==============================================================

CPU is running Process A (pid=1000)
Scheduler decides to switch to Process B (pid=2000)

STEP 1: Save Context of Process A
---------------------------------
  - General purpose registers (rax, rbx, ..., r15)
  - Instruction pointer (rip) — where to resume
  - Stack pointer (rsp)
  - Flags register (rflags)
  - FPU/SSE/AVX state (lazily saved)
  → Stored in: task_struct->thread (struct thread_struct)
  → Also on the kernel stack of Process A

STEP 2: Switch Memory Context (if different processes, not threads)
-------------------------------------------------------------------
  - Load Process B's page table base into CR3 register
  - This flushes the TLB (Translation Lookaside Buffer)!
  - TLB flush is expensive — this is why threads (same mm_struct)
    are cheaper to switch than processes.

  [CR3 = pointer to top-level page table (PGD)]

STEP 3: Restore Context of Process B
-------------------------------------
  - Load rsp (switch to Process B's kernel stack)
  - Pop saved registers from Process B's kernel stack
  - Load rip → CPU jumps to where Process B left off

STEP 4: Return to User Space
-----------------------------
  - sysretq / iret instruction returns to user mode
  - CPU drops privilege level (ring 0 → ring 3)

TIMELINE:
  A runs ... [timer IRQ] ... save A ... switch CR3 ... restore B ... B runs
              |<------------- ~1-10 microseconds ----------------------->|
```

---

## 3.6 Load Balancing — Multi-CPU Scheduling

```
LOAD BALANCING ACROSS CPUS
==============================================================

CPU 0 run queue: [task1, task2, task3, task4, task5]  ← 5 tasks!
CPU 1 run queue: [task6]                               ← only 1!

CFS detects imbalance via:
  load = Σ (task_weight) for all tasks on this CPU

Load balancer runs:
1. Every scheduler tick (tick-driven balancing)
2. When a CPU becomes idle (idle balancing)
3. Via NOHZ_FULL mechanisms for tickless CPUs

Migration:
  CPU 1 (idle) pulls tasks from CPU 0's run queue.
  Task is migrated: removed from CPU 0's rq, added to CPU 1's rq.

  BUT: We must respect CPU affinity (sched_setaffinity).
  Some tasks are pinned to specific CPUs (e.g., IRQ handlers,
  real-time tasks, NUMA-aware tasks).

NUMA-AWARE SCHEDULING:
==============================================================
  NUMA = Non-Uniform Memory Access.
  In multi-socket servers, each CPU socket has local RAM.
  Accessing remote RAM is 2-4x slower than local RAM.

  Node 0 (socket 0)          Node 1 (socket 1)
  CPU 0  CPU 1               CPU 2  CPU 3
  |      |                   |      |
  +--RAM0--+                 +--RAM1--+
       |____________________________|
               QPI/HyperTransport
               (slow cross-NUMA link)

  The scheduler tries to keep tasks on the same NUMA node
  as their memory allocations (NUMA locality).
```

---

# 4. Memory Management Subsystem

## 4.1 Virtual Memory — The Abstraction

Every process has its own **virtual address space** — a private illusion of having the entire address range to itself. The kernel uses page tables to translate virtual addresses to physical addresses.

> **Concept — Page:**  
> Memory is divided into fixed-size chunks called pages (typically 4KB on x86-64).  
> The MMU (Memory Management Unit) hardware translates virtual page numbers to physical frame numbers using page tables.

```
VIRTUAL ADDRESS SPACE LAYOUT (x86-64, 64-bit Linux)
==============================================================

  Address 0xFFFFFFFFFFFFFFFF (top)
  +---------------------------------+
  |  Kernel Space (128 TB)          | ← Only accessible in ring 0
  |  [kernel code, data, vmalloc,   |
  |   direct mapping of all RAM,    |
  |   kernel stacks, modules]       |
  +---------------------------------+
  |  Non-canonical gap              | ← Hardware enforced gap
  |  (hardware does not allow       |   causes #GP if accessed
  |   these addresses)              |
  +---------------------------------+
  |  User Space (128 TB)            | ← Accessible in ring 3
  |                                 |
  |  0x7FFFF... Stack               | ← grows down ↓
  |               ↓                 |
  |                                 |
  |  Memory-Mapped Region           | ← mmap(), shared libs
  |  (shared libraries, mmap files) |
  |               ↑                 |
  |             Heap                | ← grows up ↑ (brk/mmap)
  |  BSS  (uninitialized globals)   |
  |  Data (initialized globals)     |
  |  Text (code — read-only)        | ← 0x400000 typical start
  |  [null guard page]              |
  Address 0x0000000000000000
```

---

## 4.2 Page Tables — 4-Level x86-64 Paging

```
4-LEVEL PAGE TABLE WALK (x86-64)
==============================================================

Virtual Address: 0x00007f1234567890  (48 bits used)

Bit breakdown:
  [63:48] = sign extension (must be 0 for user, 1 for kernel)
  [47:39] = PGD index (9 bits)  → Page Global Directory
  [38:30] = PUD index (9 bits)  → Page Upper Directory
  [29:21] = PMD index (9 bits)  → Page Middle Directory
  [20:12] = PTE index (9 bits)  → Page Table Entry
  [11: 0] = Page offset (12 bits) → offset within 4KB page

CR3 register
    |
    v
+----------+        +----------+        +----------+        +----------+
|  PGD     |------->|  PUD     |------->|  PMD     |------->|  PTE     |
| [PGD idx]|        | [PUD idx]|        | [PMD idx]|        | [PTE idx]|
+----------+        +----------+        +----------+        +----------+
                                                                  |
                                                                  | physical frame number
                                                                  v
                                                        +------------------+
                                                        |  Physical Page   |
                                                        |  (4KB)           |
                                                        |  [offset 0x890]  | ← Final address
                                                        +------------------+

Each PTE contains:
  [51:12] = Physical frame number (up to 52-bit physical addresses)
  [11]    = Dirty bit (page was written)
  [6]     = Accessed bit (page was read or written)
  [5]     = Cache disable
  [4]     = Page Cache Write-Through
  [3]     = PWT (page-level write-through)
  [2]     = U/S (user/supervisor — ring 3 can access?)
  [1]     = R/W (read/write or read-only?)
  [0]     = Present bit (1=valid, 0=page not in RAM → page fault!)
```

---

## 4.3 Physical Memory Management: The Buddy Allocator

> **Concept — Buddy Allocator:**  
> The kernel needs to allocate physical pages efficiently with minimal fragmentation.  
> The buddy system divides all physical memory into blocks of sizes 2^0, 2^1, 2^2, ... 2^10 pages (1 to 1024 pages = 4MB max).  
> When you allocate 3 pages, it rounds up to 4 (next power of 2), takes from the order-2 free list.  
> When freed, it tries to merge with its "buddy" (adjacent block of same size) to form larger blocks.

```
BUDDY ALLOCATOR FREE LISTS
==============================================================

Order 0 (4KB):   [page_A] -> [page_B] -> [page_C] -> ...
Order 1 (8KB):   [page_D, page_E] -> [page_F, page_G] -> ...
Order 2 (16KB):  [page_H..K] -> ...
Order 3 (32KB):  ...
...
Order 10 (4MB):  [page_set] -> ...

ALLOCATION of 12KB (needs order-2 = 16KB):
1. Check order-2 free list → empty
2. Check order-3 free list → found [pages 0-7]
3. Split order-3 into two order-2 blocks:
   - [pages 0-3] → allocated to caller
   - [pages 4-7] → added to order-2 free list

FREEING [pages 0-3] (order-2):
1. Compute buddy address: XOR page_number with (1 << order)
   buddy = 0 XOR 4 = 4  → buddy is [pages 4-7]
2. Is buddy free? YES (we put it there during split)
3. MERGE: [pages 0-7] → order-3 block, add to order-3 free list
```

---

## 4.4 Slab Allocator — Kernel Object Cache

The buddy allocator gives us whole pages. But the kernel constantly allocates and frees small objects like `task_struct`, `inode`, `file`, etc.

> **Concept — Slab Allocator:**  
> The slab allocator pre-allocates pages from the buddy system and divides them into fixed-size slots for specific object types. This provides O(1) allocation/deallocation and dramatically reduces fragmentation for kernel objects.

# Linux Kernel Subsystems: A Complete Deep-Dive Guide
## From Fundamentals to Mastery — For the Top 1%

---

> *"The kernel is not magic — it is the most disciplined piece of engineering humanity has produced. Every line exists for a reason. Learn the reason."*

---

## TABLE OF CONTENTS

```
PART I   — FOUNDATION & ARCHITECTURE
PART II  — PROCESS MANAGEMENT & SCHEDULER
PART III — MEMORY MANAGEMENT
PART IV  — VIRTUAL FILE SYSTEM & STORAGE
PART V   — NETWORK STACK
PART VI  — DEVICE DRIVERS & I/O
PART VII — INTER-PROCESS COMMUNICATION
PART VIII— SYNCHRONIZATION & CONCURRENCY
PART IX  — INTERRUPT & EXCEPTION HANDLING
PART X   — SYSTEM CALLS INTERFACE
PART XI  — SECURITY SUBSYSTEM (LSM)
PART XII — POWER MANAGEMENT
PART XIII— TIME & TIMER SUBSYSTEM
PART XIV — CGROUPS & NAMESPACES
PART XV  — KERNEL DEBUGGING & TRACING
```

---

# PART I — FOUNDATION & ARCHITECTURE

---

## Chapter 1: What IS the Linux Kernel?

### 1.1 Conceptual Definition

Before touching subsystems, you must have a razor-sharp mental model of what a kernel *is*.

**Definition:** The kernel is the **privileged software layer** that mediates between hardware and user programs. It is the only software that runs with complete trust — it can execute any CPU instruction, access any memory address, and control every hardware device.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEM LAYERS MODEL                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           USER SPACE (Ring 3 / Unprivileged)            │   │
│  │                                                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │  bash    │  │ Firefox  │  │  Python  │  ...        │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │   │
│  │       │              │              │                   │   │
│  │  ┌────▼──────────────▼──────────────▼────────────────┐ │   │
│  │  │          C Standard Library (glibc)               │ │   │
│  │  └──────────────────────┬────────────────────────────┘ │   │
│  └─────────────────────────┼───────────────────────────────┘   │
│                    SYSCALL │ BOUNDARY (trap gate)               │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │           KERNEL SPACE (Ring 0 / Privileged)            │   │
│  │                                                         │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │              SYSTEM CALL INTERFACE               │  │   │
│  │  └─────────┬───────────┬───────────┬────────────────┘  │   │
│  │            │           │           │                    │   │
│  │  ┌─────────▼──┐  ┌─────▼───┐  ┌───▼──────┐            │   │
│  │  │  Process   │  │ Memory  │  │   VFS    │  ...       │   │
│  │  │  Manager   │  │ Manager │  │          │            │   │
│  │  └─────────┬──┘  └─────┬───┘  └───┬──────┘            │   │
│  │            │           │           │                    │   │
│  │  ┌─────────▼───────────▼───────────▼──────────────┐    │   │
│  │  │           ARCHITECTURE-DEPENDENT CODE          │    │   │
│  │  └──────────────────────┬─────────────────────────┘    │   │
│  └─────────────────────────┼────────────────────────────── ┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                     HARDWARE                            │   │
│  │  ┌───────┐  ┌──────┐  ┌────────┐  ┌──────────────────┐ │   │
│  │  │  CPU  │  │  RAM │  │  Disk  │  │  Network Card    │ │   │
│  │  └───────┘  └──────┘  └────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Kernel Types — Mental Model

```
KERNEL ARCHITECTURE SPECTRUM
─────────────────────────────────────────────────────────────────

MONOLITHIC                    MICROKERNEL              HYBRID
─────────────────             ────────────────         ──────────────────
All subsystems run            Only essential           Mix: some services
in kernel space               services in kernel       in kernel, some in
                              (IPC, scheduling,        user space
                              basic VM)
                              
Linux is HERE                 Mach, MINIX              macOS (XNU),
                              are HERE                 Windows NT
                              
PROS:                         PROS:                    PROS:
- Fast (no context           - Resilient              - Balance of both
  switch for subsystem       - Clean design
  calls)                     - Easy to debug
- Efficient IPC
  between subsystems

CONS:                         CONS:                    CONS:
- One bug can crash          - Slow IPC               - Complex
  entire system              - Complex context
                               switching
```

### 1.3 CPU Privilege Rings (What "Kernel Space" Really Means)

```
CPU PRIVILEGE RINGS (x86 Architecture)
────────────────────────────────────────────────────────

         ┌──────────────────────────────────┐
         │  Ring 3 (User Mode)              │
         │  - Applications                  │
         │  - Limited instructions          │
         │  - Cannot access I/O directly    │
         │  ┌────────────────────────────┐  │
         │  │  Ring 2 (OS Services)      │  │
         │  │  (rarely used today)       │  │
         │  │  ┌──────────────────────┐  │  │
         │  │  │  Ring 1 (OS Services)│  │  │
         │  │  │  (rarely used today) │  │  │
         │  │  │  ┌────────────────┐  │  │  │
         │  │  │  │  Ring 0        │  │  │  │
         │  │  │  │  (Kernel Mode) │  │  │  │
         │  │  │  │  ALL access    │  │  │  │
         │  │  │  │  ANY instruction│  │  │  │
         │  │  │  └────────────────┘  │  │  │
         │  │  └──────────────────────┘  │  │
         │  └────────────────────────────┘  │
         └──────────────────────────────────┘

KEY INSIGHT: Linux only uses Ring 0 (kernel) and Ring 3 (user).
The CPU enforces the boundary in HARDWARE.
A user process CANNOT read kernel memory — the MMU blocks it.
```

---

## Chapter 2: Kernel Source Tree Architecture

### 2.1 Directory Structure Mental Map

```
linux/
├── arch/          ← CPU-specific code (x86, ARM, RISC-V...)
│   └── x86/
│       ├── kernel/    ← x86 process, interrupt, SMP code
│       ├── mm/        ← x86 memory management
│       └── include/   ← x86 headers
│
├── kernel/        ← CORE: scheduler, signals, timers, irq
│   ├── sched/     ← Completely Fair Scheduler (CFS)
│   ├── irq/       ← Interrupt management
│   ├── locking/   ← Mutex, spinlock, rwlock
│   └── time/      ← Timekeeping, hrtimers
│
├── mm/            ← Memory management subsystem
│   ├── slab.c     ← SLAB allocator
│   ├── vmalloc.c  ← vmalloc
│   ├── mmap.c     ← Memory mapping
│   └── page_alloc.c ← Page frame allocator (buddy system)
│
├── fs/            ← File systems
│   ├── ext4/      ← ext4 filesystem
│   ├── btrfs/     ← Btrfs filesystem
│   ├── proc/      ← /proc virtual FS
│   ├── sysfs/     ← /sys virtual FS
│   └── vfs/       ← Virtual File System layer
│
├── net/           ← Network stack
│   ├── ipv4/      ← TCP/IP v4
│   ├── ipv6/      ← IPv6
│   ├── core/      ← Core networking
│   └── socket.c   ← Socket layer
│
├── drivers/       ← Device drivers (HUGE — 60% of kernel)
│   ├── block/     ← Block device drivers
│   ├── char/      ← Character device drivers
│   ├── net/       ← Network drivers
│   └── gpu/       ← GPU drivers
│
├── ipc/           ← Inter-process communication
│   ├── sem.c      ← Semaphores
│   ├── msg.c      ← Message queues
│   └── shm.c      ← Shared memory
│
├── security/      ← LSM (Linux Security Modules)
│   ├── selinux/   ← SELinux
│   └── apparmor/  ← AppArmor
│
├── block/         ← Block I/O layer
├── lib/           ← Kernel utility library
├── init/          ← Kernel init code (start_kernel)
└── include/       ← Kernel-wide headers
    ├── linux/     ← Most used headers
    └── uapi/      ← User-space API headers
```

### 2.2 Kernel Boot Flow

```
KERNEL BOOT SEQUENCE FLOWCHART
────────────────────────────────────────────────────────────────

[BIOS/UEFI]
     │
     ▼
[Bootloader: GRUB2]
  - Loads kernel image (vmlinuz)
  - Loads initramfs
  - Passes cmdline to kernel
     │
     ▼
[Kernel Entry: arch/x86/boot/compressed/head_64.S]
  - CPU in 32/64-bit mode setup
  - Decompress kernel
     │
     ▼
[arch/x86/kernel/head_64.S]
  - Setup initial page tables
  - Enable paging (MMU on)
  - Setup GDT, IDT
     │
     ▼
[start_kernel() — init/main.c]  ◄── THIS IS WHERE C CODE BEGINS
  │
  ├──► setup_arch()         — CPU/memory topology
  ├──► trap_init()          — Exception handlers (divide by zero, etc.)
  ├──► mm_init()            — Memory management init
  ├──► sched_init()         — Scheduler init
  ├──► irq_init()           — Interrupt controller setup
  ├──► softirq_init()       — Software interrupt setup
  ├──► time_init()          — Timer subsystem
  ├──► ipc_init()           — IPC structures
  ├──► vfs_caches_init()    — VFS hash tables
  └──► rest_init()
           │
           ├──► kernel_thread(kernel_init)  ← spawns PID 1
           └──► cpu_idle_loop()             ← becomes idle task (PID 0)

[kernel_init — PID 1]
  - Mounts root filesystem
  - Starts /sbin/init or systemd
  - execve("/sbin/init")
       │
       ▼
[systemd / init — now in USER SPACE]
  - Starts all system services
  - You see a login prompt
```

---

# PART II — PROCESS MANAGEMENT & SCHEDULER

---

## Chapter 3: Processes and Threads

### 3.1 Core Concepts — What is a Process?

**Definition:** A process is an *instance of a program in execution*. It is the fundamental unit of resource ownership in Linux.

**Key insight for DSA thinkers:** A process is a **node in a tree** (the process tree). Every process except PID 1 has exactly one parent. This is literally a tree data structure maintained by the kernel.

```
WHAT A PROCESS OWNS
───────────────────────────────────────────────────────────────

Process = Container of:
  ┌─────────────────────────────────────────────────────────┐
  │  Virtual Address Space                                  │
  │  ┌──────────┬──────────┬──────────┬────────┬────────┐  │
  │  │  text    │  data    │  heap    │  ...   │ stack  │  │
  │  │ (code)   │(globals) │(malloc'd)│        │(local  │  │
  │  │          │          │          │        │ vars)  │  │
  │  └──────────┴──────────┴──────────┴────────┴────────┘  │
  │                                                         │
  │  File Descriptor Table                                  │
  │  ┌────┬─────────────────────────────────────────────┐  │
  │  │ 0  │ stdin  → /dev/tty                           │  │
  │  │ 1  │ stdout → /dev/tty                           │  │
  │  │ 2  │ stderr → /dev/tty                           │  │
  │  │ 3  │ open("file.txt", ...)                       │  │
  │  └────┴─────────────────────────────────────────────┘  │
  │                                                         │
  │  Signal Handlers Table                                  │
  │  Credentials (UID, GID, capabilities)                   │
  │  CPU registers snapshot (when not running)              │
  │  Accounting info (CPU time, memory used)                │
  └─────────────────────────────────────────────────────────┘
```

### 3.2 task_struct — The Process Descriptor

The most important data structure in the Linux kernel. Every process/thread is represented by a `task_struct`.

```
task_struct (simplified — actual struct has 700+ fields)
──────────────────────────────────────────────────────────────

struct task_struct {
    /* 1. STATE */
    volatile long         state;        // RUNNING, SLEEPING, ZOMBIE...
    int                   exit_state;   // EXIT_ZOMBIE, EXIT_DEAD
    
    /* 2. IDENTITY */
    pid_t                 pid;          // Process ID
    pid_t                 tgid;         // Thread Group ID (= pid for main thread)
    
    /* 3. PROCESS TREE LINKS */
    struct task_struct   *real_parent;  // biological parent
    struct task_struct   *parent;       // adoptive parent (for ptrace)
    struct list_head      children;     // list of my children
    struct list_head      sibling;      // link in parent's children list
    
    /* 4. SCHEDULER DATA */
    unsigned int          policy;       // SCHED_NORMAL, SCHED_FIFO...
    int                   prio;         // dynamic priority
    int                   static_prio;  // nice-based priority
    struct sched_entity   se;           // CFS entity (red-black tree node!)
    
    /* 5. MEMORY */
    struct mm_struct     *mm;           // virtual memory descriptor
    struct mm_struct     *active_mm;    // active memory descriptor
    
    /* 6. FILE SYSTEM */
    struct fs_struct     *fs;           // filesystem info (cwd, root)
    struct files_struct  *files;        // open file descriptors
    
    /* 7. SIGNALS */
    struct signal_struct *signal;       // signal handlers
    sigset_t              blocked;      // blocked signals mask
    
    /* 8. CREDENTIALS */
    const struct cred    *cred;         // UID, GID, capabilities
    
    /* 9. KERNEL STACK */
    void                 *stack;        // pointer to kernel stack
    
    /* 10. CPU CONTEXT */
    struct thread_struct  thread;       // CPU registers when not running
};
```

```
PROCESS TREE VISUALIZATION (DSA: N-ary Tree)
─────────────────────────────────────────────────────────────

         [systemd PID=1]
         /      |       \
        /       |        \
  [sshd]   [cron]    [NetworkMgr]
  PID=100  PID=200    PID=300
    /  \
   /    \
[bash] [bash]
PID=400 PID=401
  |
  |
[vim]
PID=500

Each arrow = parent→child relationship (task_struct.children list)
Each node   = one task_struct in kernel memory
```

### 3.3 Process States — State Machine

```
PROCESS STATE MACHINE
──────────────────────────────────────────────────────────────────

                    ┌─────────────────┐
                    │   TASK_RUNNING  │◄──────────────────┐
                    │  (on run queue  │                    │
                    │   OR on CPU)    │                    │
                    └────────┬────────┘                    │
                             │                             │
              ┌──────────────┼──────────────┐              │
              │ wait for I/O │              │ I/O complete │
              │ or resource  │  preempted   │ or resource  │
              ▼              ▼              │ available    │
   ┌──────────────────┐  ┌──────┐          │              │
   │TASK_INTERRUPTIBLE│  │ CPU  │          │              │
   │   (sleeping,     │  │gives │          │              │
   │    wakes on sig) │  │ away │──────────┘              │
   └──────────────────┘  └──────┘                         │
              │                                            │
              │ signal received                            │
              └────────────────────────────────────────────┘

   ┌────────────────────────┐
   │TASK_UNINTERRUPTIBLE    │  ← sleeping, CANNOT be woken by signal
   │ (waiting for hardware) │    (e.g., disk I/O — kernel must finish)
   └────────────────────────┘

   ┌──────────────────┐        ┌──────────────────┐
   │   EXIT_ZOMBIE    │◄───────│  process calls   │
   │  (dead but entry │  exit()│   exit() or      │
   │   in process     │        │  returns from    │
   │   table remains) │        │   main()         │
   └────────┬─────────┘        └──────────────────┘
            │
            │ parent calls wait()
            ▼
   ┌──────────────────┐
   │    EXIT_DEAD     │  ← task_struct freed, PID recycled
   └──────────────────┘

   ┌──────────────────┐
   │  TASK_STOPPED    │  ← SIGSTOP received (ctrl+Z, debugging)
   └──────────────────┘

   ┌──────────────────┐
   │  TASK_TRACED     │  ← being debugged (ptrace)
   └──────────────────┘
```

### 3.4 Process vs Thread in Linux

**Critical insight:** Linux has NO separate concept of "thread" at the kernel level. Both processes and threads are `task_struct`. The difference is *what they share*.

```
PROCESS vs THREAD RESOURCE SHARING
────────────────────────────────────────────────────────────────

fork() creates a PROCESS:              clone() creates a THREAD:
  ┌─────────────────────┐                ┌─────────────────────┐
  │ Parent task_struct  │                │ Parent task_struct  │
  │  mm_struct ─────────┼─┐             │  mm_struct ─────────┼──┐
  │  files_struct ──────┼─┼─┐           │  files_struct ──────┼──┼─┐
  └─────────────────────┘ │ │           └─────────────────────┘  │ │
                           │ │                                    │ │
  ┌─────────────────────┐ │ │           ┌─────────────────────┐  │ │
  │ Child task_struct   │ │ │           │ Child task_struct   │  │ │
  │  mm_struct ─────────┼─┘ │           │  mm_struct ─────────┼──┘ │
  │  files_struct ──────┼───┘           │  files_struct ──────┼────┘
  └─────────────────────┘               └─────────────────────┘
  
  COPIED (COW):                          SHARED (same pointer):
  - Address space                        - Address space (mm_struct)
  - File descriptors                     - File descriptors
  - Signal handlers                      - Signal handlers
  - PID = new unique value               - TGID = parent's PID
                                         - PID = new unique value

COW = Copy-On-Write: pages shared until one writes, then copied
```

### 3.5 C Implementation — Process Internals Exploration

```c
// kernel/fork.c — simplified conceptual version of copy_process()
// This is how fork() works internally

#include <linux/sched.h>
#include <linux/slab.h>
#include <linux/mm.h>
#include <linux/fs.h>

/*
 * copy_process — allocates and initializes a new task_struct
 * Called by fork(), clone(), vfork()
 *
 * @clone_flags: what to SHARE vs COPY (CLONE_VM, CLONE_FILES, etc.)
 * @stack_start: stack pointer for new thread
 */
static struct task_struct *copy_process(unsigned long clone_flags,
                                         unsigned long stack_start)
{
    struct task_struct *p;
    int retval;

    /* STEP 1: Allocate a new task_struct from the slab cache */
    p = dup_task_struct(current);  // current = pointer to running task
    if (!p)
        return ERR_PTR(-ENOMEM);

    /* STEP 2: Copy or share the memory map */
    if (clone_flags & CLONE_VM) {
        /* THREAD: share the mm_struct, increment reference count */
        atomic_inc(&current->mm->mm_users);
        p->mm = current->mm;
    } else {
        /* PROCESS: copy the address space (COW) */
        retval = copy_mm(clone_flags, p);
        if (retval)
            goto bad_fork_cleanup_task;
    }

    /* STEP 3: Copy or share file descriptors */
    if (clone_flags & CLONE_FILES) {
        /* THREAD: share file table */
        atomic_inc(&current->files->count);
        p->files = current->files;
    } else {
        /* PROCESS: copy file descriptor table */
        retval = copy_files(clone_flags, p);
        if (retval)
            goto bad_fork_cleanup_mm;
    }

    /* STEP 4: Copy signal handlers */
    retval = copy_sighand(clone_flags, p);

    /* STEP 5: Assign a new PID */
    p->pid = alloc_pid(p->nsproxy->pid_ns_for_children);

    /* STEP 6: Setup parent/child links in the process tree */
    p->real_parent = current;
    p->parent      = current;
    list_add_tail(&p->sibling, &current->children);

    /* STEP 7: Initialize scheduler entity */
    sched_fork(clone_flags, p);

    /* STEP 8: Add to global task list (doubly linked list of all tasks) */
    list_add_tail_rcu(&p->tasks, &init_task.tasks);

    return p;

bad_fork_cleanup_mm:
    /* Cleanup on error... */
bad_fork_cleanup_task:
    free_task(p);
    return ERR_PTR(retval);
}
```

```c
// userspace_example.c — Observing fork/exec/wait from user space
// Compile: gcc -O2 -o proc_demo userspace_example.c

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <string.h>

void print_process_info(const char *label)
{
    printf("[%s] PID=%d  PPID=%d  PGID=%d\n",
           label, getpid(), getppid(), getpgrp());
}

int main(void)
{
    pid_t child_pid;
    int   status;

    print_process_info("parent-before-fork");

    /*
     * fork() — creates exact copy of this process
     * Returns: 0 to child, child_pid to parent, -1 on error
     */
    child_pid = fork();

    if (child_pid < 0) {
        perror("fork failed");
        exit(EXIT_FAILURE);
    }

    if (child_pid == 0) {
        /* ---- CHILD PROCESS ---- */
        print_process_info("child-after-fork");

        /*
         * exec() — replaces the process image
         * The child now runs /bin/ls instead of this program
         * The task_struct STAYS, but mm_struct is replaced
         */
        char *args[] = {"/bin/ls", "-la", "/proc/self", NULL};
        execv("/bin/ls", args);

        /* If execv returns, it failed */
        perror("execv failed");
        exit(EXIT_FAILURE);

    } else {
        /* ---- PARENT PROCESS ---- */
        print_process_info("parent-after-fork");
        printf("[parent] waiting for child PID=%d\n", child_pid);

        /*
         * wait() — blocks until child exits
         * Reaps the zombie: frees task_struct, PID
         */
        pid_t reaped = waitpid(child_pid, &status, 0);

        if (WIFEXITED(status)) {
            printf("[parent] child %d exited with code %d\n",
                   reaped, WEXITSTATUS(status));
        } else if (WIFSIGNALED(status)) {
            printf("[parent] child killed by signal %d\n",
                   WTERMSIG(status));
        }
    }

    return 0;
}
```

### 3.6 Rust Implementation — Process Abstraction

```rust
// process_abstraction.rs
// Demonstrates safe Rust wrappers around Linux process primitives
// Run: cargo run

use std::process::{Command, Stdio};
use std::os::unix::process::CommandExt; // Unix-specific extensions

/// Represents a process lifecycle manager
/// Models the fork-exec-wait pattern safely in Rust
struct ProcessManager {
    name: String,
}

impl ProcessManager {
    fn new(name: &str) -> Self {
        Self { name: name.to_string() }
    }

    /// Demonstrates the fork-exec pattern
    /// Rust's std::process::Command uses clone() + exec() internally
    fn spawn_child(&self, program: &str, args: &[&str]) -> std::io::Result<()> {
        println!("[{}] Spawning: {} {:?}", self.name, program, args);

        let mut child = Command::new(program)
            .args(args)
            .stdout(Stdio::piped())  // Capture stdout
            .stderr(Stdio::piped())
            // Unix-specific: run before exec() in child
            .pre_exec(|| {
                // This runs in the forked child, before exec()
                // Equivalent to code between fork() and exec() in C
                println!("  [child pre-exec] PID={}", std::process::id());
                Ok(())
            })
            .spawn()?;

        println!("[{}] Child spawned with PID={}", self.name, child.id());

        // Wait for child — equivalent to waitpid()
        let output = child.wait_with_output()?;

        println!("[{}] Child exited with status: {}", self.name, output.status);
        if !output.stdout.is_empty() {
            println!("[{}] Child stdout: {}",
                     self.name,
                     String::from_utf8_lossy(&output.stdout).trim());
        }

        Ok(())
    }

    /// Demonstrates parallel process spawning and joining
    fn spawn_parallel(&self, count: usize) -> std::io::Result<()> {
        let mut handles = Vec::new();

        for i in 0..count {
            // Each Command::spawn() is a fork+exec
            let child = Command::new("sleep")
                .arg("0.1")
                .spawn()?;
            println!("[{}] Spawned worker {} PID={}", self.name, i, child.id());
            handles.push(child);
        }

        // Collect all children — like waitpid() in a loop
        for (i, mut child) in handles.into_iter().enumerate() {
            let status = child.wait()?;
            println!("[{}] Worker {} done: {}", self.name, i, status);
        }

        Ok(())
    }
}

/// Low-level process info via /proc filesystem
/// The /proc filesystem exposes kernel data structures as files
fn read_process_info(pid: u32) -> std::io::Result<()> {
    let status_path = format!("/proc/{}/status", pid);
    let content = std::fs::read_to_string(&status_path)?;

    println!("\n=== /proc/{}/status (kernel task_struct exposed) ===", pid);
    for line in content.lines().take(15) {
        println!("  {}", line);
    }

    // Read memory maps — shows the process's virtual address space
    let maps_path = format!("/proc/{}/maps", pid);
    if let Ok(maps) = std::fs::read_to_string(&maps_path) {
        println!("\n=== /proc/{}/maps (virtual memory layout) ===", pid);
        for (i, line) in maps.lines().take(8).enumerate() {
            println!("  [{:02}] {}", i, line);
        }
        println!("  ... (truncated)");
    }

    Ok(())
}

fn main() {
    let mgr = ProcessManager::new("main");

    // Show our own process info
    let my_pid = std::process::id();
    println!("=== Current Process ===");
    println!("PID: {}", my_pid);
    println!("PPID: reading from /proc/self/status...");
    let _ = read_process_info(my_pid);

    println!("\n=== Spawning Child ===");
    mgr.spawn_child("echo", &["Hello from child process!"])
       .expect("spawn failed");

    println!("\n=== Parallel Workers ===");
    mgr.spawn_parallel(3).expect("parallel spawn failed");

    println!("\nAll processes complete.");
}
```

---

## Chapter 4: The Linux Scheduler

### 4.1 What is the Scheduler?

**Definition:** The scheduler is the kernel subsystem that decides *which task_struct gets CPU time, and for how long*. It implements **time-sharing** — giving each process the illusion of having the entire CPU.

**Core Problem (DSA Perspective):** Given N processes all wanting CPU time, implement a policy that is:
- **Fair** — no starvation
- **Efficient** — low overhead
- **Responsive** — interactive tasks feel snappy
- **Throughput-maximizing** — batch jobs run fast

```
THE SCHEDULING PROBLEM
──────────────────────────────────────────────────────────────

    Tasks wanting CPU:
    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
    │ T1   │ │ T2   │ │ T3   │ │ T4   │ │ T5   │
    │nice=0│ │nice=5│ │nice=0│ │nice=-5│ │nice=0│
    └──────┘ └──────┘ └──────┘ └──────┘ └──────┘

    CPU: ──[T4]──[T1]──[T3]──[T5]──[T4]──[T1]──[T3]──...

    CHALLENGE: How do you decide this sequence?
    ANSWER: CFS (Completely Fair Scheduler) + Red-Black Tree
```

### 4.2 Scheduler Classes — Layered Design

```
SCHEDULER CLASS HIERARCHY
────────────────────────────────────────────────────────────────

Linux uses a pluggable scheduler class system.
Each class has a priority; highest-priority non-empty class runs.

  PRIORITY
  (high)  ┌─────────────────────────────────────────────────┐
          │  stop_sched_class  — can stop CPUs (migration)  │
          │  (internal only)                                │
          ├─────────────────────────────────────────────────┤
          │  dl_sched_class    — SCHED_DEADLINE             │
          │  Earliest Deadline First (EDF) algorithm        │
          │  Real-time tasks with strict timing guarantees  │
          ├─────────────────────────────────────────────────┤
          │  rt_sched_class    — SCHED_FIFO / SCHED_RR      │
          │  Real-time tasks, priority 1-99                 │
          │  Always preempt SCHED_NORMAL tasks              │
          ├─────────────────────────────────────────────────┤
          │  fair_sched_class  — SCHED_NORMAL / SCHED_BATCH │
          │  CFS: Completely Fair Scheduler                 │
          │  Uses Red-Black Tree                            │
          │  99% of all tasks use this                      │
          ├─────────────────────────────────────────────────┤
  (low)   │  idle_sched_class  — SCHED_IDLE                │
          │  Runs only when NOTHING else wants CPU          │
          │  The "swapper" task (PID 0)                     │
          └─────────────────────────────────────────────────┘
```

### 4.3 CFS — Completely Fair Scheduler (The Heart)

**Core Idea:** CFS tracks how much CPU time each task has received as `vruntime` (virtual runtime). It always runs the task with the *smallest* vruntime — the task that has received the *least* CPU time relative to its weight.

**DSA KEY INSIGHT:** The run queue in CFS is a **Red-Black Tree** keyed by `vruntime`. The "next to run" task is always the **leftmost node** — O(log N) insert/delete, O(1) find-min.

```
CFS RED-BLACK TREE RUN QUEUE
────────────────────────────────────────────────────────────────

Each node = sched_entity (inside task_struct)
Key       = vruntime (nanoseconds of virtual CPU time received)

The task with LOWEST vruntime is LEFTMOST = runs next

              [T3: vruntime=100ms]
             /                    \
    [T1: vruntime=80ms]        [T5: vruntime=140ms]
    /                \
[T4: vruntime=60ms]  [T2: vruntime=90ms]
★
↑ T4 runs next (leftmost = minimum vruntime)

WHEN T4 RUNS:
  - T4's vruntime increases: 60ms → 60ms + (slice / weight)
  - If T4's new vruntime > T3's vruntime, T4 is reinserted on right
  - T1 becomes the new leftmost
  - Result: Fair time distribution!

vruntime formula:
  delta_vruntime = delta_exec_ns × (NICE_0_LOAD / task_weight)
  
  Tasks with HIGH priority (low nice) have HIGH weight
  → Their vruntime grows SLOWER
  → They stay leftmost LONGER
  → They get MORE CPU time
  
  This is genius: priority becomes vruntime growth rate!
```

```
CFS SCHEDULING DECISION FLOWCHART
────────────────────────────────────────────────────────────────

Timer interrupt fires (every ~1ms)
           │
           ▼
   ┌───────────────┐
   │ update_curr() │  ← update vruntime of currently running task
   │ task.vruntime │
   │ += delta × w  │
   └───────┬───────┘
           │
           ▼
   ┌─────────────────────────────────────────┐
   │ Should we preempt?                      │
   │                                         │
   │ if (curr.vruntime - leftmost.vruntime   │
   │     > sched_latency / nr_running)       │
   └──────────────┬──────────────────────────┘
                  │
          ┌───────┴────────┐
          │ YES            │ NO
          ▼                ▼
   ┌─────────────┐  ┌────────────────┐
   │ Set TIF_    │  │ Continue run   │
   │ NEED_RESCHED│  │ current task   │
   │ flag        │  └────────────────┘
   └──────┬──────┘
          │
          ▼
   [next schedule() call]
          │
          ▼
   ┌──────────────────────────────┐
   │ pick_next_task()             │
   │ = __pick_first_entity()      │
   │ = leftmost node of RB tree   │
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ context_switch(prev, next)   │
   │  1. switch_mm(): load new    │
   │     page tables (CR3 on x86) │
   │  2. switch_to(): swap        │
   │     CPU registers            │
   └──────────────────────────────┘
          │
          ▼
   [next task is now running on CPU]
```

### 4.4 Context Switch — The Mechanism

```
CONTEXT SWITCH DETAIL (x86-64)
────────────────────────────────────────────────────────────────

"Switching from Task A to Task B"

STEP 1: Save Task A's CPU state into thread_struct
  ┌─────────────────────────────────────────────┐
  │ task_A.thread.sp  = rsp  (stack pointer)    │
  │ task_A.thread.ip  = rip  (instruction ptr)  │
  │ task_A.thread.r15..r8, rbx, rbp = registers │
  │ FPU/SSE state saved if used                 │
  └─────────────────────────────────────────────┘

STEP 2: Switch address space (if different processes)
  ┌─────────────────────────────────────────────┐
  │ CR3 = task_B.mm.pgd  ← load page table base│
  │ (TLB is flushed or ASID-tagged)             │
  └─────────────────────────────────────────────┘

STEP 3: Restore Task B's CPU state from thread_struct
  ┌─────────────────────────────────────────────┐
  │ rsp  = task_B.thread.sp                     │
  │ rip  = task_B.thread.ip  (jump here!)       │
  │ registers restored                          │
  └─────────────────────────────────────────────┘

CPU now executes Task B. Task A is "frozen" in memory.
Task A will resume from exactly where it was saved.

COST: ~1,000-10,000 ns (cache cold) to ~100ns (cache warm)
This is why goroutines/green threads are faster — they avoid
the kernel context switch overhead!
```

### 4.5 C Implementation — Scheduler Concepts

```c
// scheduler_concepts.c
// Demonstrates scheduler interactions from user space
// Compile: gcc -O2 -o sched_demo scheduler_concepts.c -lpthread

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <sched.h>
#include <time.h>
#include <string.h>
#include <sys/resource.h>

/* ─────────────────────────────────────────────
 * SECTION 1: Reading scheduler information
 * ───────────────────────────────────────────── */

void print_sched_info(pid_t pid)
{
    int policy = sched_getscheduler(pid);
    struct sched_param param;
    sched_getparam(pid, &param);

    const char *policy_name;
    switch (policy) {
        case SCHED_OTHER:  policy_name = "SCHED_OTHER (CFS)"; break;
        case SCHED_FIFO:   policy_name = "SCHED_FIFO (RT)";  break;
        case SCHED_RR:     policy_name = "SCHED_RR (RT)";    break;
        case SCHED_BATCH:  policy_name = "SCHED_BATCH";      break;
        case SCHED_IDLE:   policy_name = "SCHED_IDLE";       break;
        case SCHED_DEADLINE: policy_name = "SCHED_DEADLINE"; break;
        default:           policy_name = "UNKNOWN";
    }

    printf("PID %d: policy=%-24s rt_priority=%d\n",
           pid, policy_name, param.sched_priority);

    /* Read nice value (maps to weight in CFS) */
    int nice_val = getpriority(PRIO_PROCESS, pid);
    printf("PID %d: nice=%d (weight=%s)\n",
           pid, nice_val,
           nice_val < 0 ? "higher (more CPU)" :
           nice_val > 0 ? "lower (less CPU)" :
                          "normal");
}

/* ─────────────────────────────────────────────
 * SECTION 2: CPU affinity — pin task to cores
 * This maps to task_struct.cpus_allowed bitmask
 * ───────────────────────────────────────────── */

void demonstrate_cpu_affinity(void)
{
    cpu_set_t cpuset;
    int num_cpus = sysconf(_SC_NPROCESSORS_ONLN);

    printf("\n=== CPU Affinity ===\n");
    printf("System has %d CPUs online\n", num_cpus);

    /* Get current affinity */
    CPU_ZERO(&cpuset);
    if (sched_getaffinity(0, sizeof(cpu_set_t), &cpuset) == 0) {
        printf("Current CPU affinity mask: ");
        for (int i = 0; i < num_cpus; i++) {
            printf("%d", CPU_ISSET(i, &cpuset) ? 1 : 0);
        }
        printf("\n");
    }

    /* Pin to CPU 0 only */
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == 0) {
        printf("Pinned to CPU 0\n");
    }

    /* Restore all CPUs */
    for (int i = 0; i < num_cpus; i++)
        CPU_SET(i, &cpuset);
    sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
}

/* ─────────────────────────────────────────────
 * SECTION 3: Voluntary yielding
 * ───────────────────────────────────────────── */

void demonstrate_yielding(void)
{
    printf("\n=== Voluntary Yielding ===\n");

    /*
     * sched_yield() moves current task to end of run queue
     * CFS equivalent: vruntime is set to max of all tasks
     * Use case: cooperative spinlocks, batch work
     */
    struct timespec before, after;
    clock_gettime(CLOCK_MONOTONIC, &before);
    sched_yield();
    clock_gettime(CLOCK_MONOTONIC, &after);

    long ns = (after.tv_sec - before.tv_sec) * 1000000000L
              + (after.tv_nsec - before.tv_nsec);
    printf("sched_yield() took ~%ld ns\n", ns);
}

/* ─────────────────────────────────────────────
 * SECTION 4: Real-time scheduling demo
 * (requires CAP_SYS_NICE capability / root)
 * ───────────────────────────────────────────── */

void try_realtime_scheduling(void)
{
    printf("\n=== Real-Time Scheduling ===\n");

    struct sched_param param = { .sched_priority = 1 };

    /*
     * SCHED_FIFO: RT task, no time slice
     * Runs until it blocks or explicitly yields
     * Priority 1-99 (99 = highest)
     */
    if (sched_setscheduler(0, SCHED_FIFO, &param) == 0) {
        printf("Set to SCHED_FIFO priority=1\n");
        /* Reset to normal */
        param.sched_priority = 0;
        sched_setscheduler(0, SCHED_OTHER, &param);
        printf("Reset to SCHED_OTHER\n");
    } else {
        printf("Cannot set SCHED_FIFO (need CAP_SYS_NICE or root)\n");
    }
}

int main(void)
{
    printf("=== Linux Scheduler Demo ===\n\n");

    printf("=== Current Process Scheduling Info ===\n");
    print_sched_info(getpid());

    demonstrate_cpu_affinity();
    demonstrate_yielding();
    try_realtime_scheduling();

    printf("\n=== Reading scheduler stats from /proc ===\n");
    /* /proc/schedstat exposes per-CPU scheduler statistics */
    FILE *f = fopen("/proc/schedstat", "r");
    if (f) {
        char line[256];
        int count = 0;
        while (fgets(line, sizeof(line), f) && count < 5) {
            printf("  %s", line);
            count++;
        }
        fclose(f);
    }

    return 0;
}
```

### 4.6 Rust Implementation — Scheduler Interaction

```rust
// scheduler_rust.rs
// Safe, idiomatic Rust scheduler interaction
// Cargo.toml: nix = "0.27"

use std::time::{Duration, Instant};
use std::thread;

/// Represents scheduling policy options
#[derive(Debug, Clone, Copy)]
enum SchedPolicy {
    Normal,   // SCHED_OTHER — CFS
    Batch,    // SCHED_BATCH — CFS but no preemption preference
    Idle,     // SCHED_IDLE  — lowest priority
    Fifo,     // SCHED_FIFO  — real-time FIFO
    RR,       // SCHED_RR    — real-time round-robin
}

/// Thread workload measurement
/// Demonstrates how scheduler affects execution timing
struct WorkloadTimer {
    name:   String,
    start:  Instant,
    events: Vec<(String, Duration)>,
}

impl WorkloadTimer {
    fn new(name: &str) -> Self {
        Self {
            name:   name.to_string(),
            start:  Instant::now(),
            events: Vec::new(),
        }
    }

    fn checkpoint(&mut self, label: &str) {
        let elapsed = self.start.elapsed();
        self.events.push((label.to_string(), elapsed));
    }

    fn report(&self) {
        println!("\n=== Workload Report: {} ===", self.name);
        for (label, duration) in &self.events {
            println!("  {:30} @ {:>8.3} ms", label, duration.as_secs_f64() * 1000.0);
        }
    }
}

/// Read scheduler vruntime from /proc filesystem
/// This is how you observe the CFS red-black tree key
fn read_sched_info(pid: u32) -> std::io::Result<()> {
    let path = format!("/proc/{}/sched", pid);
    if let Ok(content) = std::fs::read_to_string(&path) {
        println!("\n=== /proc/{}/sched (CFS internal data) ===", pid);
        for line in content.lines().take(20) {
            // Filter to interesting fields
            if line.contains("vruntime") 
                || line.contains("nr_switches")
                || line.contains("nr_voluntary")
                || line.contains("se.load")
                || line.starts_with("comm")
                || line.starts_with("pid")
            {
                println!("  {}", line);
            }
        }
    }
    Ok(())
}

/// Simulate CPU-bound work (stays on CPU — no voluntary sleep)
fn cpu_bound_work(iterations: u64) -> u64 {
    let mut sum: u64 = 0;
    for i in 0..iterations {
        // Prevent optimizer from removing this
        sum = sum.wrapping_add(i.wrapping_mul(i));
    }
    sum
}

/// Simulate I/O-bound work (sleeps — voluntarily gives up CPU)
fn io_bound_work(rounds: u32) {
    for _ in 0..rounds {
        thread::sleep(Duration::from_micros(100));
    }
}

/// Demonstrate how multiple threads share CPU time
fn demonstrate_thread_scheduling() {
    println!("\n=== Parallel Thread Scheduling Demo ===");

    let num_threads = 4;
    let mut handles = Vec::new();

    let start = Instant::now();

    for id in 0..num_threads {
        let handle = thread::Builder::new()
            .name(format!("worker-{}", id))
            .spawn(move || {
                let thread_start = Instant::now();
                let mut timer = WorkloadTimer::new(&format!("Thread-{}", id));

                timer.checkpoint("started");

                // Mix of CPU and I/O work
                let _result = cpu_bound_work(1_000_000);
                timer.checkpoint("cpu-work-done");

                thread::yield_now(); // sched_yield() equivalent
                timer.checkpoint("after-yield");

                io_bound_work(5);
                timer.checkpoint("io-work-done");

                let _result2 = cpu_bound_work(500_000);
                timer.checkpoint("finished");

                let total = thread_start.elapsed();
                timer.report();
                total
            })
            .expect("thread spawn failed");

        handles.push(handle);
    }

    // Join all threads (like waitpid for threads)
    let mut total_durations = Vec::new();
    for handle in handles {
        if let Ok(duration) = handle.join() {
            total_durations.push(duration);
        }
    }

    let wall_time = start.elapsed();

    println!("\n=== Scheduling Summary ===");
    println!("Wall clock time: {:.3} ms", wall_time.as_secs_f64() * 1000.0);
    for (i, d) in total_durations.iter().enumerate() {
        println!("Thread {} total time: {:.3} ms", i, d.as_secs_f64() * 1000.0);
    }

    // If sum_of_thread_times >> wall_clock_time,
    // threads ran in PARALLEL (multiple CPUs)
    let sum: f64 = total_durations.iter()
        .map(|d| d.as_secs_f64() * 1000.0)
        .sum();
    println!("Sum of thread times: {:.3} ms", sum);
    println!("Parallelism factor: {:.2}x", sum / (wall_time.as_secs_f64() * 1000.0));
}

fn main() {
    println!("=== Linux Scheduler — Rust Exploration ===");

    let my_pid = std::process::id();
    println!("My PID: {}", my_pid);

    // Read our own scheduler data
    let _ = read_sched_info(my_pid);

    // Run scheduling demo
    demonstrate_thread_scheduling();

    // Re-read scheduler data to see nr_switches increased
    println!("\n=== After workload — scheduler stats updated ===");
    let _ = read_sched_info(my_pid);
}
```

---

# PART III — MEMORY MANAGEMENT
---

## Chapter 5: Virtual Memory — The Foundation

### 5.1 Why Virtual Memory Exists

**The Core Problem:** Multiple processes all want to use memory simultaneously. Without abstraction:
- Process A writing to address 0x1000 would corrupt Process B
- A process could read kernel secrets
- Memory would fragment into unusable holes

**The Solution:** Virtual Memory — every process gets its own *private* address space. The hardware (MMU) translates virtual → physical transparently.

```
VIRTUAL vs PHYSICAL MEMORY
──────────────────────────────────────────────────────────────────

VIRTUAL ADDRESS SPACE          PHYSICAL MEMORY
(what the process sees)        (actual RAM chips)
                               
Process A:                     ┌─────────────────┐
┌──────────────┐               │  Physical Frame │ ← page frame 0
│  0x00001000  │──────────────►│  (Process A's   │
│  (text)      │               │   text page)    │
├──────────────┤               ├─────────────────┤
│  0x00002000  │──────────┐    │  Physical Frame │ ← page frame 1
│  (data)      │          │    │  (Process B's   │
└──────────────┘          │    │   text page)    │
                          │    ├─────────────────┤
Process B:                └───►│  Physical Frame │ ← page frame 2
┌──────────────┐               │  (Process A's   │
│  0x00001000  │──────────────►│   data page)    │
│  (text)      │               ├─────────────────┤
├──────────────┤               │  Physical Frame │ ← page frame 3
│  0x00002000  │──────────────►│  (Process B's   │
│  (stack)     │               │   stack page)   │
└──────────────┘               └─────────────────┘

KEY INSIGHT:
- Process A's 0x00001000 and Process B's 0x00001000 are DIFFERENT
  physical pages — total isolation!
- Two processes CAN map the same physical page (shared memory,
  shared libraries) by pointing to the same frame
- Virtual address space can be LARGER than physical RAM
  (pages get swapped to disk)
```

### 5.2 Page Tables — The Translation Mechanism

**Definition:** A page table is a data structure that maps virtual page numbers to physical frame numbers. The MMU hardware walks this structure on every memory access.

```
4-LEVEL PAGE TABLE (x86-64, 48-bit virtual addresses)
──────────────────────────────────────────────────────────────────

Virtual Address: 64 bits, but only 48 used:
┌─────────┬─────────┬─────────┬─────────┬─────────────────┐
│  Bits   │ 47..39  │ 38..30  │ 29..21  │ 20..12 │ 11..0  │
│  Name   │  PGD    │  PUD    │  PMD    │  PTE   │ offset │
│  Width  │  9 bits │  9 bits │  9 bits │ 9 bits │12 bits │
│  Range  │ 0..511  │ 0..511  │ 0..511  │ 0..511 │ 0..4095│
└─────────┴─────────┴─────────┴─────────┴────────┴────────┘

TRANSLATION WALK:
                    CR3 register
                        │
                        ▼
               ┌─────────────────┐
               │   PGD Table     │ (Page Global Directory)
               │  [  0  ]        │
               │  [  1  ]        │
               │  [ ... ]        │
               │  [ idx ]────────┼──────────────────┐
               │  [ ... ]        │                  │
               └─────────────────┘                  │
                                                     ▼
                                            ┌─────────────────┐
                                            │   PUD Table     │
                                            │ (Page Upper Dir)│
                                            │  [ idx ]────────┼──┐
                                            └─────────────────┘  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │   PMD Table     │
                                                         │ (Page Middle Dir│
                                                         │  [ idx ]────────┼──┐
                                                         └─────────────────┘  │
                                                                               ▼
                                                                      ┌────────────────┐
                                                                      │   PTE Table    │
                                                                      │ (Page Table    │
                                                                      │  Entry)        │
                                                                      │  [ idx ]───────┼──┐
                                                                      └────────────────┘  │
                                                                                          ▼
                                                                                ┌─────────────────┐
                                                                                │  Physical Frame  │
                                                                                │  base address    │
                                                                                │  + 12-bit offset │
                                                                                │  = Physical Addr │
                                                                                └─────────────────┘

TLB (Translation Lookaside Buffer):
Hardware cache of recent virtual→physical translations.
Hit rate ~99%: most translations found in TLB, no tree walk needed.
Context switch: TLB flushed (or ASID-tagged to avoid flush).
```

### 5.3 Virtual Memory Areas — How Kernel Tracks Segments

**Definition:** A `vm_area_struct` (VMA) describes one contiguous region of a process's virtual address space — its text, data, heap, stack, or a mmap'd file.

```
PROCESS VIRTUAL ADDRESS SPACE LAYOUT (64-bit Linux)
──────────────────────────────────────────────────────────────────

Virtual Address    VMA                   Description
───────────────    ───────────────────   ──────────────────────────
0xFFFFFFFFFFFF     ┌───────────────────┐
(top of stack)     │  KERNEL SPACE     │ Kernel mapped here
                   │  (not accessible  │ (same in all processes,
0xFFFF800000000000 │   from user mode) │  but protected by MMU)
                   ├───────────────────┤
                   │  [huge gap]       │ Non-canonical addresses
                   │  (128 TB)         │ (accessing = SIGSEGV)
                   ├───────────────────┤
0x00007FFF:FFFF    │  STACK            │ vm_area_struct: growsdown
  (grows ↓)        │  (grows down)     │ flags: RW, anonymous
                   │  ↓ ↓ ↓           │
                   │                   │
                   │  [stack guard     │
                   │   pages]          │
                   ├───────────────────┤
                   │  mmap region      │ vm_area_struct per mapping
                   │  (shared libs,    │ e.g., libc.so mapped here
                   │   files,         │ flags: R-X for code
                   │   anonymous mmap) │ flags: RW- for data
                   │  ↑ ↑ ↑           │
                   │  (grows up)       │
                   ├───────────────────┤
                   │  HEAP             │ vm_area_struct
                   │  (grows up ↑)     │ brk pointer marks end
                   │  ↑ ↑ ↑           │ flags: RW, anonymous
                   ├───────────────────┤
                   │  BSS segment      │ vm_area_struct
                   │  (zero-init data) │ uninit global variables
                   ├───────────────────┤
                   │  DATA segment     │ vm_area_struct
                   │  (init globals)   │ initialized globals
                   ├───────────────────┤
0x400000 (typical) │  TEXT segment     │ vm_area_struct
                   │  (code)           │ flags: R-X (read+execute)
                   │                   │ backed by ELF file
0x000000000000     └───────────────────┘

mm_struct has a RED-BLACK TREE of vm_area_structs (keyed by start addr)
for fast VMA lookup on page faults!
```

### 5.4 Page Fault — The Most Important Event in Memory Management

**Definition:** A page fault is a hardware exception (interrupt 14 on x86) triggered when a process accesses a virtual address that either:
1. Has no page table entry (new allocation, lazy loading)
2. Has a present bit = 0 (swapped to disk)
3. Is a permission violation (write to read-only)

```
PAGE FAULT HANDLER FLOWCHART
──────────────────────────────────────────────────────────────────

Process accesses virtual address X
              │
              ▼
     MMU checks page tables
              │
     ┌────────┴────────┐
     │                 │
  Hit in TLB       Not in TLB
     │                 │
     │            Walk page table
     │                 │
     │          ┌──────┴──────┐
     │          │             │
     │       Present       Not Present
     │          │             │
     │    ┌─────┴────┐        │
     │    │          │        │
     │  Perm OK   Perm Fail   │
     │    │          │        │
   Translate  SIGSEGV or   PAGE FAULT EXCEPTION
     │        SIGBUS        (INT 14 / #PF)
     │                          │
     │                          ▼
     │                 do_page_fault() in kernel
     │                          │
     │              ┌───────────┼───────────┐
     │              │           │           │
     │          No VMA        VMA         Protection
     │         for addr       found       violation
     │              │           │           │
     │           SIGSEGV    ┌───┴───┐    ┌──┴──────────┐
     │                      │       │    │             │
     │                  Anonymous  File- Copy-On-Write  Write to
     │                  (heap,     backed              read-only
     │                   stack)   (mmap)               → SIGSEGV
     │                      │       │           │
     │                ┌─────┘   ┌───┘       ┌──┘
     │                │         │           │
     │                ▼         ▼           ▼
     │          Allocate    Read page    Alloc new page
     │          new zero    from disk    copy old data
     │          page        (readahead!) update PTE
     │                │         │           │
     │                └────┬────┘           │
     │                     │                │
     │                     ▼                ▼
     │              Update PTE          Update PTE
     │              Map virtual         Map to new
     │              → physical          physical page
     │                     │
     └─────────────────────┘
                           │
                           ▼
                  Resume process
                  (re-execute faulting instruction)
```

### 5.5 Physical Memory Allocator — Buddy System

**Definition:** The buddy system is the physical page frame allocator. It manages physical RAM as blocks of 2^n pages.

**DSA Insight:** This is a specialized free-list data structure. Blocks are tracked by order (power of 2). Splitting and merging happen in O(log max_order) time.

```
BUDDY SYSTEM ALLOCATOR
──────────────────────────────────────────────────────────────────

Free lists organized by ORDER (2^order pages per block):

order 0: [1 page]  [1 page]  [1 page]  ...   (4KB blocks)
order 1: [2 pages] [2 pages] ...              (8KB blocks)
order 2: [4 pages] [4 pages] ...              (16KB blocks)
order 3: [8 pages] ...                        (32KB blocks)
...
order 10: [1024 pages]                        (4MB blocks)

ALLOCATION of 8 pages (order=3):
─────────────────────────────────

Before:
  order 3: [BLOCK A: pages 0-7]  [BLOCK B: pages 8-15]
  order 4: [BLOCK C: pages 0-15]

Request: alloc_pages(order=3)

1. Check order-3 free list → BLOCK A available → return it!
   
After:
  order 3: [BLOCK B: pages 8-15]    ← BLOCK A removed
  order 4: [BLOCK C: pages 0-15]

SPLITTING (if order-3 list was empty):
─────────────────────────────────────

Before: order-3 empty, order-4 has BLOCK C (pages 0-15)

1. Take BLOCK C from order-4 list
2. Split into two buddies:
   - LEFT  buddy: pages 0-7  (add to order-3 free list)
   - RIGHT buddy: pages 8-15 (add to order-3 free list)
3. Return LEFT buddy for allocation

MERGING (on free):
─────────────────────────────────────

Free pages 0-7 (order-3 block):
1. Calculate buddy address: XOR with (1 << order)
   buddy of page 0 at order 3 = page 0 XOR 8 = page 8
2. Is buddy (page 8) free at order 3? YES
3. Merge: remove both from order-3, create order-4 block (pages 0-15)
4. Repeat: check if this order-4 block has a free buddy...

This is O(log N) merge cascade worst case.
```

### 5.6 SLAB Allocator — Kernel Object Cache

**Problem with buddy system:** It allocates in page multiples (4KB, 8KB...). But the kernel constantly allocates small objects — `task_struct` (~7KB), `inode`, `dentry`, etc. A 256-byte object shouldn't waste a 4KB page.

**Solution:** The SLAB/SLUB allocator creates *object caches* — pre-allocated slabs of same-size objects.

```
SLAB ALLOCATOR ARCHITECTURE
──────────────────────────────────────────────────────────────────

kmem_cache for task_struct (size=7168 bytes):
─────────────────────────────────────────────

   kmem_cache
  ┌────────────────┐
  │ name: "task_   │
  │        struct" │
  │ obj_size: 7168 │
  │ per_cpu_cache  │──────┐
  │ full_slabs ────┼──┐   │
  │ partial_slabs ─┼──┼─┐ │
  │ free_slabs ────┼──┼─┼─┼──┐
  └────────────────┘  │ │ │  │
                      │ │ │  │
  full slab: ◄────────┘ │ │  │
  ┌─────────────────────┐ │  │
  │ [task_1][task_2]... │ │  │
  │ all objects USED    │ │  │
  └─────────────────────┘ │  │
                          │  │
  partial slab: ◄─────────┘  │
  ┌─────────────────────┐    │
  │ [task_5][FREE][task_7]│   │
  │ some free, some used │   │
  └─────────────────────┘    │
                              │
  free slab: ◄────────────────┘
  ┌─────────────────────┐
  │ [FREE][FREE][FREE]  │
  │ all objects FREE    │
  └─────────────────────┘

ALLOCATION:
  1. Check per-CPU cache (no lock needed! fast path)
  2. If empty: grab object from partial slab (with lock)
  3. If no partial: allocate new slab from buddy allocator

PER-CPU CACHE (SLUB optimization):
  Each CPU has its own free list of objects
  kmalloc on CPU 0: pop from CPU 0's cache — NO SPINLOCK
  kfree  on CPU 0: push to CPU 0's cache  — NO SPINLOCK
  This eliminates cache line bouncing between CPUs!
```

### 5.7 Memory Zones

```
MEMORY ZONES (x86-64)
──────────────────────────────────────────────────────────────────

Physical memory divided into zones for different purposes:

Physical Address
0x0000_0000          ┌──────────────────────────────────────┐
                     │  ZONE_DMA (0 - 16MB)                 │
                     │  For legacy ISA DMA devices          │
                     │  that can only address 16-bit bus    │
0x0100_0000          ├──────────────────────────────────────┤
                     │  ZONE_DMA32 (16MB - 4GB)             │
                     │  For 32-bit DMA-capable devices      │
0x1_0000_0000        ├──────────────────────────────────────┤
                     │  ZONE_NORMAL (4GB - ?)               │
                     │  Regular mappable memory             │
                     │  Most allocations come from here     │
                     ├──────────────────────────────────────┤
                     │  ZONE_HIGHMEM (only 32-bit!)         │
                     │  Memory above kernel's direct map    │
                     │  (Not relevant in 64-bit kernels)    │
                     └──────────────────────────────────────┘

NUMA (Non-Uniform Memory Access):
  Multi-socket servers have memory local to each CPU socket
  Accessing local memory: ~100ns
  Accessing remote memory: ~300ns (across QPI/UPI bus)
  
  Kernel tries to allocate memory LOCAL to the running CPU!
```

### 5.8 C Implementation — Memory Management Internals

```c
// memory_management.c
// Exploring Linux memory management from user and kernel perspectives
// Compile: gcc -O2 -o mm_demo memory_management.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <stdint.h>
#include <time.h>

/* ─────────────────────────────────────────────────────────
 * SECTION 1: Virtual Address Space Layout
 * ───────────────────────────────────────────────────────── */

void print_address_layout(void)
{
    printf("=== Virtual Address Space Layout ===\n");

    /* Stack variable — on the stack segment */
    int stack_var = 42;

    /* Static data — in BSS or DATA segment */
    static int bss_var;         // BSS (zero-init)
    static int data_var = 100;  // DATA (init'd)

    /* Heap allocation */
    void *heap_ptr = malloc(1024);

    /* Text segment — address of a function */
    void *text_ptr = (void*)print_address_layout;

    printf("Text  (code):     %p\n", text_ptr);
    printf("Data  (init'd):   %p (value=%d)\n", (void*)&data_var, data_var);
    printf("BSS   (zero-init):%p (value=%d)\n", (void*)&bss_var, bss_var);
    printf("Heap  (malloc):   %p\n", heap_ptr);
    printf("Stack (local var):%p\n", (void*)&stack_var);

    /* 
     * Observe: heap << stack in typical layout
     * They grow toward each other
     */
    uintptr_t heap_addr  = (uintptr_t)heap_ptr;
    uintptr_t stack_addr = (uintptr_t)&stack_var;
    printf("Heap-to-stack distance: %lu MB\n",
           (stack_addr - heap_addr) / (1024*1024));

    free(heap_ptr);
}

/* ─────────────────────────────────────────────────────────
 * SECTION 2: mmap — Memory-Mapped Files
 * mmap() creates a vm_area_struct in the kernel
 * ───────────────────────────────────────────────────────── */

void demonstrate_mmap(void)
{
    printf("\n=== mmap — Memory Mapped I/O ===\n");

    /* Anonymous mmap: like malloc but page-aligned, direct syscall */
    size_t size = 4096 * 4; // 4 pages = 16KB

    void *anon_map = mmap(NULL,             // let kernel choose address
                          size,             // mapping size
                          PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS,
                          -1,              // no file (anonymous)
                          0);

    if (anon_map == MAP_FAILED) {
        perror("anonymous mmap failed");
        return;
    }

    printf("Anonymous mmap at: %p (size=%zu KB)\n",
           anon_map, size / 1024);

    /*
     * KEY INSIGHT: Pages are not allocated yet!
     * The vm_area_struct exists, but physical pages are
     * allocated lazily on first access (page fault)
     *
     * This is the "demand paging" optimization:
     * malloc(1GB) doesn't use 1GB of RAM until you write to it
     */

    /* First write triggers page faults — kernel allocates physical pages */
    printf("Writing to mapped memory (triggers page faults)...\n");
    memset(anon_map, 0xAB, size);

    /* Read back to verify */
    unsigned char *bytes = (unsigned char*)anon_map;
    printf("First byte after write: 0x%02X\n", bytes[0]);

    /* mlock() pins pages in RAM — prevents swapping */
    /* Useful for real-time applications, crypto key storage */
    if (mlock(anon_map, size) == 0) {
        printf("Pages locked in RAM (no swap)\n");
        munlock(anon_map, size);
    }

    /* Advise kernel about access pattern — affects readahead */
    madvise(anon_map, size, MADV_SEQUENTIAL); // read front-to-back
    madvise(anon_map, size, MADV_DONTNEED);   // free these pages

    munmap(anon_map, size);
    printf("Memory unmapped\n");
}

/* ─────────────────────────────────────────────────────────
 * SECTION 3: Transparent Huge Pages observation
 * ───────────────────────────────────────────────────────── */

void demonstrate_huge_pages(void)
{
    printf("\n=== Huge Pages Demo ===\n");

    /*
     * Normal page: 4KB
     * Huge page:   2MB (on x86-64)
     * Gigantic:    1GB
     *
     * Huge pages reduce TLB pressure dramatically:
     * 1GB mapped with 4KB pages: 262144 TLB entries needed
     * 1GB mapped with 2MB pages: 512 TLB entries needed
     */

    size_t huge_size = 2 * 1024 * 1024; // 2MB

    /* MAP_HUGETLB requests huge pages explicitly */
    void *huge_mem = mmap(NULL,
                          huge_size,
                          PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                          -1, 0);

    if (huge_mem == MAP_FAILED) {
        printf("Explicit huge page failed (need /proc/sys/vm/nr_hugepages > 0)\n");
        printf("Transparent Huge Pages (THP) may still apply automatically\n");
    } else {
        printf("Huge page allocated at %p\n", huge_mem);
        memset(huge_mem, 0, huge_size);
        munmap(huge_mem, huge_size);
    }

    /* Read THP stats */
    FILE *f = fopen("/sys/kernel/mm/transparent_hugepage/enabled", "r");
    if (f) {
        char buf[256];
        fgets(buf, sizeof(buf), f);
        printf("THP setting: %s", buf);
        fclose(f);
    }
}

/* ─────────────────────────────────────────────────────────
 * SECTION 4: Memory pressure and OOM
 * ───────────────────────────────────────────────────────── */

void read_memory_stats(void)
{
    printf("\n=== System Memory Statistics ===\n");

    /* /proc/meminfo exposes mm subsystem counters */
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return;

    char line[256];
    int count = 0;
    while (fgets(line, sizeof(line), f) && count < 15) {
        /* Filter key fields */
        if (strncmp(line, "MemTotal", 8) == 0 ||
            strncmp(line, "MemFree", 7) == 0 ||
            strncmp(line, "MemAvailable", 12) == 0 ||
            strncmp(line, "Cached", 6) == 0 ||
            strncmp(line, "Buffers", 7) == 0 ||
            strncmp(line, "SwapTotal", 9) == 0 ||
            strncmp(line, "SwapFree", 8) == 0 ||
            strncmp(line, "HugePages_Total", 15) == 0 ||
            strncmp(line, "PageTables", 10) == 0) {
            printf("  %s", line);
            count++;
        }
    }
    fclose(f);

    /* Read our own process memory usage */
    printf("\n=== Our Process Memory (VmRSS = Resident Set Size) ===\n");
    f = fopen("/proc/self/status", "r");
    if (!f) return;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "Vm", 2) == 0) {
            printf("  %s", line);
        }
    }
    fclose(f);
}

/* ─────────────────────────────────────────────────────────
 * SECTION 5: Stack overflow — demonstrating guard pages
 * (Safe observation only — don't actually overflow!)
 * ───────────────────────────────────────────────────────── */

void read_stack_info(void)
{
    printf("\n=== Stack Information ===\n");

    struct rlimit rl;
    getrlimit(RLIMIT_STACK, &rl);

    if (rl.rlim_cur == RLIM_INFINITY) {
        printf("Stack limit: unlimited\n");
    } else {
        printf("Stack soft limit: %lu KB\n", rl.rlim_cur / 1024);
        printf("Stack hard limit: %lu KB\n", rl.rlim_max / 1024);
    }

    /*
     * Guard page: 1 unmapped page at stack bottom
     * If stack overflows into guard page → SIGSEGV
     * The kernel can detect stack overflow vs random access
     * because the fault address is just below %rsp
     */
    printf("Stack guard page: 1 page (4KB) below stack\n");
    printf("Stack grows downward on x86\n");
}

int main(void)
{
    printf("╔═══════════════════════════════════════════════╗\n");
    printf("║    Linux Memory Management Demonstration      ║\n");
    printf("╚═══════════════════════════════════════════════╝\n\n");

    print_address_layout();
    demonstrate_mmap();
    demonstrate_huge_pages();
    read_memory_stats();
    read_stack_info();

    return 0;
}
```

### 5.9 Rust Implementation — Memory Management

```rust
// memory_management.rs
// Safe and unsafe Rust exploration of Linux memory subsystem

use std::alloc::{alloc, dealloc, Layout};
use std::ptr;
use std::fs;

/// Demonstrates Rust's allocator (sits on top of kernel's brk/mmap)
/// In Rust, the global allocator calls mmap/brk for large allocations
/// and manages smaller ones in user space (jemalloc or system malloc)

fn demonstrate_rust_allocator() {
    println!("=== Rust Allocator (jemalloc/system over kernel mmap) ===");

    // Box<T>: heap allocation, calls global allocator → eventually mmap
    let boxed = Box::new([0u8; 4096]);
    println!("Box<[u8; 4096]> allocated at: {:p}", boxed.as_ref().as_ptr());

    // Vec<T>: dynamic array on heap
    let mut vec = Vec::with_capacity(1000);
    println!("Vec capacity=1000 data ptr: {:p}", vec.as_ptr());
    vec.push(42u64);
    println!("Vec after push, len={}", vec.len());

    // Large allocation: likely goes directly to mmap
    let large = vec![0u8; 1024 * 1024]; // 1MB
    println!("1MB Vec at: {:p}", large.as_ptr());

    // When boxed/vec/large are dropped, memory is returned to allocator
    // The allocator may or may not return it to kernel immediately
    drop(large);
    println!("Large vec dropped (memory returned to allocator)");
}

/// Manual allocation using the allocator API
/// This is closer to how C's malloc works
fn demonstrate_manual_allocation() {
    println!("\n=== Manual Allocation via alloc API ===");

    unsafe {
        // Allocate 64 bytes, 8-byte aligned
        let layout = Layout::from_size_align(64, 8).unwrap();
        let ptr = alloc(layout);

        if ptr.is_null() {
            println!("Allocation failed (OOM)");
            return;
        }

        println!("Manually allocated 64 bytes at: {:p}", ptr);

        // Write to the allocation
        ptr::write_bytes(ptr, 0xCC, 64); // fill with 0xCC (debug pattern)

        // Read back
        let first_byte = ptr::read(ptr);
        println!("First byte (0xCC={}): 0x{:02X}", 0xCCu8, first_byte);

        // Must manually free — no Drop trait here
        dealloc(ptr, layout);
        println!("Manually freed");

        // ptr is now dangling — do NOT access it!
        // Rust normally prevents this at compile time.
        // That's the value of Rust's ownership system!
    }
}

/// Reading memory maps from /proc
/// Directly observes the VMA list of a process
fn read_memory_map() {
    println!("\n=== Process Virtual Memory Map (/proc/self/maps) ===");
    println!("Format: start-end perms offset dev inode path");
    println!("────────────────────────────────────────────────────────");

    match fs::read_to_string("/proc/self/maps") {
        Ok(content) => {
            let lines: Vec<&str> = content.lines().collect();
            println!("Total VMAs: {}", lines.len());
            println!("\nFirst 10 regions:");

            for line in lines.iter().take(10) {
                // Parse the VMA entry
                let parts: Vec<&str> = line.splitn(6, ' ').collect();
                if parts.len() >= 5 {
                    let addr_range = parts[0];
                    let perms      = parts[1];
                    let path       = if parts.len() > 5 { parts[5].trim() } else { "[anonymous]" };

                    println!("  {:25} {} {}", addr_range, perms, path);
                }
            }

            // Show last few (stack and vdso)
            println!("\nLast 5 regions:");
            for line in lines.iter().rev().take(5).collect::<Vec<_>>().iter().rev() {
                let parts: Vec<&str> = line.splitn(6, ' ').collect();
                if parts.len() >= 5 {
                    let addr_range = parts[0];
                    let perms      = parts[1];
                    let path       = if parts.len() > 5 { parts[5].trim() } else { "[anonymous]" };
                    println!("  {:25} {} {}", addr_range, perms, path);
                }
            }
        }
        Err(e) => println!("Could not read maps: {}", e),
    }
}

/// Observe page faults via /proc/self/status
fn measure_page_faults() {
    println!("\n=== Page Fault Measurement ===");

    fn read_page_faults() -> (u64, u64) {
        let content = fs::read_to_string("/proc/self/status").unwrap_or_default();
        let mut minor = 0u64;
        let mut major = 0u64;

        for line in content.lines() {
            // Note: task-level faults in status
            if line.starts_with("VmPeak") || line.starts_with("VmRSS") {
                println!("  {}", line);
            }
        }

        // Read from /proc/self/stat for fault counts
        if let Ok(stat) = fs::read_to_string("/proc/self/stat") {
            let fields: Vec<&str> = stat.split_whitespace().collect();
            if fields.len() > 11 {
                minor = fields[9].parse().unwrap_or(0);
                major = fields[11].parse().unwrap_or(0);
            }
        }

        (minor, major)
    }

    let (min_before, maj_before) = read_page_faults();
    println!("Before allocation - minor faults: {}, major: {}", min_before, maj_before);

    // Allocate and touch 4MB — should trigger many page faults
    let mut big_alloc = vec![0u8; 4 * 1024 * 1024];
    for chunk in big_alloc.chunks_mut(4096) {
        chunk[0] = 1; // Touch each page — forces physical page allocation
    }

    let (min_after, maj_after) = read_page_faults();
    println!("After allocation+touch - minor faults: {}, major: {}", min_after, maj_after);
    println!("New minor faults from our allocation: {}", min_after - min_before);
    println!("(Each fault = kernel allocated one 4KB physical page)");

    // big_alloc is dropped here — memory returned to allocator
}

/// Demonstrate memory layout of Rust data structures
fn demonstrate_memory_layout() {
    println!("\n=== Rust Data Structure Memory Layouts ===");

    // Stack-allocated (no heap involvement)
    let x: u64 = 42;
    let arr: [u32; 4] = [1, 2, 3, 4];

    println!("u64 on stack: addr={:p}, size={}", &x, std::mem::size_of::<u64>());
    println!("[u32; 4] on stack: addr={:p}, size={}", &arr, std::mem::size_of::<[u32; 4]>());

    // Fat pointer: (data_ptr, length) = 16 bytes on stack
    let slice: &[u32] = &arr;
    println!("&[u32] (fat ptr): size={} (ptr+len)", std::mem::size_of::<&[u32]>());

    // Box: just a pointer on stack (8 bytes), data on heap
    let boxed: Box<u64> = Box::new(100);
    println!("Box<u64>: stack size={}, heap data at {:p}",
             std::mem::size_of::<Box<u64>>(), boxed.as_ref() as *const u64);

    // String: (ptr, len, capacity) = 24 bytes on stack
    let s = String::from("hello");
    println!("String: stack size={} (ptr+len+cap), heap data at {:p}",
             std::mem::size_of::<String>(), s.as_ptr());
}

fn main() {
    println!("╔═════════════════════════════════════════════════╗");
    println!("║   Linux Memory Management — Rust Exploration   ║");
    println!("╚═════════════════════════════════════════════════╝\n");

    demonstrate_rust_allocator();
    demonstrate_manual_allocation();
    demonstrate_memory_layout();
    read_memory_map();
    measure_page_faults();
}
```

---

# PART IV — VIRTUAL FILE SYSTEM & STORAGE

---

## Chapter 6: Virtual File System (VFS)

### 6.1 The Abstraction Layer

**Definition:** The VFS (Virtual File System) is a kernel abstraction layer that provides a *uniform interface* to all file systems. Whether you're reading from ext4, btrfs, NFS, or /proc, you call the same `read()` system call.

**DSA Insight:** VFS is a classic **object-oriented polymorphism** implemented in C using function pointer tables (like vtables). Each filesystem registers its own implementations of operations like `open`, `read`, `write`, `lookup`.

```
VFS ARCHITECTURE
──────────────────────────────────────────────────────────────────

User Process
    │
    │ read(fd, buf, count)  ← single unified interface
    ▼
╔═══════════════════════════════════════════════════════════════╗
║                    SYSTEM CALL LAYER                         ║
║                    sys_read()                                ║
╚════════════════════════════╤══════════════════════════════════╝
                             │
╔════════════════════════════▼══════════════════════════════════╗
║                    VFS LAYER                                 ║
║                                                              ║
║  File Descriptor Table → struct file → struct inode          ║
║                                          │                   ║
║                             inode->i_fop->read()  ◄─────┐    ║
║                             (function pointer!)         │    ║
╚═════════════════════════════════════════════════════════╪════╝
                                                          │
        ┌─────────────────┬───────────────┬──────────────┤
        │                 │               │              │
   ┌────▼────┐      ┌─────▼───┐    ┌──────▼──┐   ┌─────▼───┐
   │  ext4   │      │  btrfs  │    │   NFS   │   │  /proc  │
   │ driver  │      │ driver  │    │ driver  │   │ pseudo  │
   │         │      │         │    │ (over   │   │  FS     │
   │ext4_read│      │btrfs_   │    │ network)│   │proc_read│
   └────┬────┘      └─────────┘    └─────────┘   └─────────┘
        │
        ▼
   Block Layer
        │
        ▼
   Disk Hardware
```

### 6.2 VFS Data Structures

```
VFS OBJECT HIERARCHY
──────────────────────────────────────────────────────────────────

SUPERBLOCK (one per mounted filesystem):
  Represents a mounted filesystem instance
  ┌─────────────────────────────────────────────────┐
  │  struct super_block                             │
  │  s_type    → filesystem type (ext4, btrfs...)  │
  │  s_op      → superblock operations (vtable)    │
  │  s_inodes  → list of all inodes on this FS     │
  │  s_blocksize → block size (4096 typically)     │
  └─────────────────────────────────────────────────┘

INODE (one per file/directory/symlink):
  Represents a file's METADATA (not name, not data — just metadata)
  ┌─────────────────────────────────────────────────┐
  │  struct inode                                   │
  │  i_ino     → inode number (unique on this FS)  │
  │  i_mode    → type (file/dir/link) + permissions│
  │  i_uid,i_gid → owner                           │
  │  i_size    → file size in bytes                │
  │  i_atime,mtime,ctime → timestamps              │
  │  i_fop     → file operations (read,write...)   │
  │  i_op      → inode operations (lookup,mkdir...)│
  │  [ext4 private: block map / extent tree]       │
  └─────────────────────────────────────────────────┘

DENTRY (directory entry — name → inode mapping):
  Represents a NAME in the filesystem (path component)
  ┌─────────────────────────────────────────────────┐
  │  struct dentry                                  │
  │  d_name    → filename component ("foo.txt")    │
  │  d_inode   → the inode this name points to     │
  │  d_parent  → parent dentry                     │
  │  d_subdirs → list of children (if directory)   │
  │  d_hash    → in dcache hash table              │
  └─────────────────────────────────────────────────┘
  
  NOTE: dentries are CACHED in the "dcache" (dentry cache)
  Path resolution: /home/alice/file.txt
  = lookup("") → lookup("home") → lookup("alice") → lookup("file.txt")
  = 4 dentry lookups, cached for speed!

FILE (one per open file descriptor):
  Represents one open instance of a file
  ┌─────────────────────────────────────────────────┐
  │  struct file                                    │
  │  f_inode   → the underlying inode              │
  │  f_pos     → current read/write position       │
  │  f_flags   → O_RDONLY, O_WRONLY, O_APPEND...  │
  │  f_op      → file operations (read, write...)  │
  │  f_count   → reference count                   │
  └─────────────────────────────────────────────────┘

RELATIONSHIP:
  fd (integer) → files_struct[] → struct file → struct dentry → struct inode
      3            [0,1,2,3...]                     "foo.txt"       metadata
```

### 6.3 Path Resolution — How /home/alice/foo.txt Gets Found

```
PATH RESOLUTION FLOWCHART: /home/alice/foo.txt
──────────────────────────────────────────────────────────────────

Start: absolute path → begin at root dentry "/"

Step 1: Start at root dentry (d_inode = root inode)
           "/"
           │
           ▼
    [root inode: directory]
    Look up child "home" in dcache:
    ┌──────────────────────────────────────────┐
    │  dcache hash(root_ino, "home") → hit?   │
    └──────────────────────────────────────────┘
           │                  │
         HIT                 MISS
           │                  │
    use cached dentry    call inode->i_op->lookup(root_inode, "home")
                         reads directory from disk
                         creates new dentry, adds to dcache
           │
           ▼
Step 2: At dentry "home", look up "alice"
    Same process: dcache check → hit or disk read

Step 3: At dentry "alice", look up "foo.txt"
    Same process

Step 4: Found dentry for "foo.txt"
    d_inode → inode for foo.txt
    
    Check permissions: inode->i_mode vs current->cred (uid/gid)
    
Step 5: Create struct file:
    f_inode = foo.txt's inode
    f_pos   = 0
    f_op    = inode->i_fop (ext4 file operations)

Step 6: Allocate file descriptor number:
    fd = get_unused_fd()
    current->files->fd_array[fd] = file
    return fd to user

TIME COMPLEXITY:
  Each component: O(1) dcache hit (hash table)
  Cold path: O(1) + disk read per component
  Full path N components: O(N) lookups
```

### 6.4 C Implementation — VFS Operations

```c
// vfs_operations.c
// Demonstrates VFS through system calls, /proc reading, and inotify
// Compile: gcc -O2 -o vfs_demo vfs_operations.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/inotify.h>
#include <sys/vfs.h>
#include <dirent.h>
#include <errno.h>
#include <time.h>

/* ─────────────────────────────────────────────────────────
 * SECTION 1: inode information via stat()
 * stat() queries the inode directly
 * ───────────────────────────────────────────────────────── */

void inspect_inode(const char *path)
{
    struct stat st;

    if (lstat(path, &st) != 0) {  // lstat: don't follow symlinks
        perror(path);
        return;
    }

    printf("\n=== Inode Info for: %s ===\n", path);
    printf("  Inode number:  %lu\n", (unsigned long)st.st_ino);
    printf("  Device:        %lu:%lu\n",
           (unsigned long)(st.st_dev >> 8),
           (unsigned long)(st.st_dev & 0xFF));
    printf("  Hard links:    %lu\n", (unsigned long)st.st_nlink);

    /* File type */
    const char *type;
    if (S_ISREG(st.st_mode))       type = "regular file";
    else if (S_ISDIR(st.st_mode))  type = "directory";
    else if (S_ISLNK(st.st_mode))  type = "symbolic link";
    else if (S_ISBLK(st.st_mode))  type = "block device";
    else if (S_ISCHR(st.st_mode))  type = "char device";
    else if (S_ISFIFO(st.st_mode)) type = "FIFO/pipe";
    else if (S_ISSOCK(st.st_mode)) type = "socket";
    else                           type = "unknown";

    printf("  Type:          %s\n", type);
    printf("  Permissions:   %04o\n", (unsigned)(st.st_mode & 07777));
    printf("  UID/GID:       %u/%u\n", st.st_uid, st.st_gid);
    printf("  Size:          %lld bytes\n", (long long)st.st_size);
    printf("  Block size:    %ld bytes\n", (long)st.st_blksize);
    printf("  Blocks alloc:  %lld (512-byte units)\n",
           (long long)st.st_blocks);

    /* Timestamps */
    char buf[64];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S",
             localtime(&st.st_mtime));
    printf("  Modified:      %s\n", buf);
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S",
             localtime(&st.st_ctime));
    printf("  Changed(meta): %s\n", buf);
}

/* ─────────────────────────────────────────────────────────
 * SECTION 2: Hard links vs Soft links
 * Demonstrates inode sharing (hard link) vs name indirection
 * ───────────────────────────────────────────────────────── */

void demonstrate_links(void)
{
    printf("\n=== Hard Links vs Symbolic Links ===\n");

    const char *original  = "/tmp/vfs_demo_original.txt";
    const char *hardlink  = "/tmp/vfs_demo_hardlink.txt";
    const char *symlink_  = "/tmp/vfs_demo_symlink.txt";

    /* Create original file */
    int fd = open(original, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return; }
    write(fd, "Hello, VFS!\n", 12);
    close(fd);

    /* Hard link: TWO names → SAME inode */
    if (link(original, hardlink) == 0) {
        struct stat st1, st2;
        stat(original, &st1);
        stat(hardlink,  &st2);
        printf("Original inode:  %lu\n", (unsigned long)st1.st_ino);
        printf("Hardlink inode:  %lu\n", (unsigned long)st2.st_ino);
        printf("Same inode? %s\n", st1.st_ino == st2.st_ino ? "YES" : "NO");
        printf("Link count: %lu (two names for same file)\n",
               (unsigned long)st1.st_nlink);

        /*
         * KEY INSIGHT: Deleting original doesn't delete data!
         * unlink() decrements st_nlink. Data deleted only when nlink=0
         * and no process has the file open.
         */
        unlink(original);
        stat(hardlink, &st2);
        printf("After unlink(original): hardlink nlink=%lu (still accessible!)\n",
               (unsigned long)st2.st_nlink);
    }

    /* Symbolic link: name → NAME (just a path string) */
    /* Original is deleted, but let's create for symlink demo */
    fd = open(original, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    write(fd, "Recreated\n", 10);
    close(fd);

    if (symlink(original, symlink_) == 0) {
        struct stat lstat_buf, stat_buf;
        lstat(symlink_, &lstat_buf); // stat the symlink itself
        stat(symlink_,  &stat_buf);  // stat the target file

        printf("\nSymlink inode:   %lu (the symlink itself)\n",
               (unsigned long)lstat_buf.st_ino);
        printf("Target inode:    %lu (the original file)\n",
               (unsigned long)stat_buf.st_ino);
        printf("Symlink size:    %lld (= length of path string!)\n",
               (long long)lstat_buf.st_size);

        char target[256];
        ssize_t len = readlink(symlink_, target, sizeof(target)-1);
        if (len > 0) {
            target[len] = '\0';
            printf("Symlink points to: %s\n", target);
        }
    }

    /* Cleanup */
    unlink(original);
    unlink(hardlink);
    unlink(symlink_);
}

/* ─────────────────────────────────────────────────────────
 * SECTION 3: Directory iteration — reading dentries
 * ───────────────────────────────────────────────────────── */

void iterate_directory(const char *path)
{
    printf("\n=== Directory Entries in %s ===\n", path);

    DIR *dir = opendir(path);
    if (!dir) { perror(path); return; }

    struct dirent *entry;
    int count = 0;

    while ((entry = readdir(dir)) != NULL && count < 15) {
        const char *type;
        switch (entry->d_type) {
            case DT_REG:  type = "FILE"; break;
            case DT_DIR:  type = "DIR";  break;
            case DT_LNK:  type = "LINK"; break;
            case DT_FIFO: type = "PIPE"; break;
            case DT_SOCK: type = "SOCK"; break;
            case DT_CHR:  type = "CHR";  break;
            case DT_BLK:  type = "BLK";  break;
            default:      type = "???";
        }

        printf("  ino=%-8lu type=%-4s name=%s\n",
               (unsigned long)entry->d_ino, type, entry->d_name);
        count++;
    }

    printf("  ... (showing first %d entries)\n", count);
    closedir(dir);
}

/* ─────────────────────────────────────────────────────────
 * SECTION 4: Filesystem stats — superblock info
 * ───────────────────────────────────────────────────────── */

void filesystem_stats(const char *path)
{
    printf("\n=== Filesystem Stats for %s ===\n", path);

    struct statfs fs_stat;
    if (statfs(path, &fs_stat) != 0) {
        perror("statfs");
        return;
    }

    printf("  Block size:    %ld bytes\n", (long)fs_stat.f_bsize);
    printf("  Total blocks:  %lu\n", (unsigned long)fs_stat.f_blocks);
    printf("  Free blocks:   %lu\n", (unsigned long)fs_stat.f_bfree);
    printf("  Avail blocks:  %lu (for non-root)\n",
           (unsigned long)fs_stat.f_bavail);
    printf("  Total inodes:  %lu\n", (unsigned long)fs_stat.f_files);
    printf("  Free inodes:   %lu\n", (unsigned long)fs_stat.f_ffree);

    long total_mb = (long)(fs_stat.f_blocks * fs_stat.f_bsize / (1024*1024));
    long free_mb  = (long)(fs_stat.f_bfree  * fs_stat.f_bsize / (1024*1024));
    printf("  Total size:    %ld MB\n", total_mb);
    printf("  Free space:    %ld MB\n", free_mb);

    /* Filesystem type magic number */
    printf("  FS type magic: 0x%lX", (unsigned long)fs_stat.f_type);
    if (fs_stat.f_type == 0xEF53)       printf(" (ext2/3/4)");
    else if (fs_stat.f_type == 0x9123683E) printf(" (btrfs)");
    else if (fs_stat.f_type == 0x58465342) printf(" (xfs)");
    else if (fs_stat.f_type == 0x6969)  printf(" (NFS)");
    else if (fs_stat.f_type == 0x9FA0)  printf(" (proc)");
    else if (fs_stat.f_type == 0x62656572) printf(" (sysfs)");
    else if (fs_stat.f_type == 0x01021994) printf(" (tmpfs)");
    printf("\n");
}

int main(void)
{
    printf("╔═════════════════════════════════════════╗\n");
    printf("║    VFS Layer — Exploration Tool         ║\n");
    printf("╚═════════════════════════════════════════╝\n");

    /* Inspect interesting VFS objects */
    inspect_inode("/proc/self");     // /proc inode
    inspect_inode("/bin/ls");        // regular file
    inspect_inode("/dev/null");      // char device
    inspect_inode("/tmp");           // directory

    demonstrate_links();
    iterate_directory("/proc/self");
    filesystem_stats("/");
    filesystem_stats("/proc");

    return 0;
}
```

### 6.5 Page Cache — Disk I/O Caching

```
PAGE CACHE ARCHITECTURE
──────────────────────────────────────────────────────────────────

The page cache is the kernel's disk cache.
File data is cached in memory pages after first read.

read(fd, buf, 4096):
  ┌───────────────────────────────────────────────────────────┐
  │ Step 1: Check page cache for this file's page             │
  │         find_get_page(inode->i_mapping, page_index)       │
  └───────────────────────────────────────────────────────────┘
                              │
                   ┌──────────┴──────────┐
                   │                     │
              CACHE HIT              CACHE MISS
                   │                     │
          Return cached data    Allocate new page
          copy to user buf      Issue block I/O
          (fast: no disk I/O)   Wait for disk read
                                Add page to cache
                                copy to user buf
                                
  Second read of same page: ALWAYS cache hit!
  
PAGE CACHE DATA STRUCTURE:
  Per-inode radix tree (now XArray in modern kernels):
  inode->i_mapping->i_pages is an XArray
  Index = page offset (page_index = file_offset / PAGE_SIZE)
  
  File of 1MB = 256 cached pages (4KB each)
  
  XArray: sparse, efficient for large files with holes

WRITE-BACK:
  write() marks page "dirty" → returns immediately to process
  pdflush/kswapd writes dirty pages to disk asynchronously
  
  This is why "echo 3 > /proc/sys/vm/drop_caches" is needed
  to flush the cache — data stays in memory until evicted!

CACHE EVICTION:
  LRU (Least Recently Used) with active/inactive lists
  Memory pressure → reclaim LRU pages
  madvise(MADV_SEQUENTIAL) → move pages to cold list faster
```

---

# PART V — NETWORK STACK

---

## Chapter 7: Linux Network Architecture

### 7.1 The Networking Layers

**The Linux network stack implements TCP/IP — a layered protocol suite where each layer adds a header and passes down.**

```
LINUX NETWORK STACK — TOP TO BOTTOM
──────────────────────────────────────────────────────────────────

User Process:
  send(fd, "Hello", 5, 0)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  SOCKET LAYER (POSIX API)                                   │
│  struct socket → sock → protocol-specific socket (tcp_sock) │
│  AF_INET, SOCK_STREAM = TCP socket                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  TRANSPORT LAYER (L4)                                       │
│  TCP: tcp_sendmsg()                                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ SKB = sk_buff (socket buffer — the central struct)   │   │
│  │ Add TCP header: seq_num, ack_num, window, checksum   │   │
│  │ TCP state machine: ESTABLISHED → sends segment       │   │
│  │ Flow control: TCP window                             │   │
│  │ Congestion control: CUBIC, BBR algorithms            │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  NETWORK LAYER (L3)                                         │
│  IP: ip_output()                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Add IP header: src IP, dst IP, TTL, protocol=6(TCP)  │   │
│  │ Routing: ip_route_output() — find which interface    │   │
│  │ Netfilter hooks: iptables/nftables rules checked     │   │
│  │ Fragmentation if packet > MTU                        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  LINK LAYER (L2)                                            │
│  Ethernet: dev_queue_xmit()                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ARP: resolve IP → MAC address                        │   │
│  │ Add Ethernet header: src MAC, dst MAC, ethertype     │   │
│  │ Queue to net_device TX queue                         │   │
│  │ Traffic control (tc): QDisc, shaping, scheduling     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  DEVICE DRIVER LAYER                                        │
│  NIC driver: ndo_start_xmit()                               │
│  DMA transfer to NIC hardware, NIC sends bits on wire       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 sk_buff — The Core Data Structure

```
SK_BUFF: THE BACKBONE OF LINUX NETWORKING
──────────────────────────────────────────────────────────────────

sk_buff (socket buffer) carries packet data through all layers.
Instead of copying data, layers ADD HEADERS by moving pointers.

Memory layout:
┌──────────────────────────────────────────────────────────────┐
│ sk_buff struct (metadata)                                    │
│   data ──────────────────────────────────────────┐          │
│   head ───────────────────────────────────────┐  │          │
│   tail ─────────────────────────────────────┐ │  │          │
│   end  ───────────────────────────────────┐ │ │  │          │
└──────────────────────────────────────────────────────────────┘
                                            │ │ │  │
Physical memory:                            ▼ │ │  │
┌────────────────────────────────────────────────────────────┐
│  [headroom][ETH_HDR][IP_HDR][TCP_HDR][PAYLOAD    ][tailroom]│
│  ▲                           ▲         ▲          ▲        │
│  head                        data       │          tail     │
│                              (for IP)   │                   │
│                              (after     │                   │
│                               Eth push) │                   │
└────────────────────────────────────────────────────────────┘

ADDING A HEADER (no copy!):
  skb_push(skb, sizeof(tcp_hdr)):
    data -= sizeof(tcp_hdr)
    write TCP header at new data pointer
    
  skb_push(skb, sizeof(ip_hdr)):
    data -= sizeof(ip_hdr)
    write IP header at new data pointer

This is genius: the SAME physical memory is used throughout.
No copying as packet passes down the stack!
Headroom is pre-allocated for exactly this purpose.
```

### 7.3 TCP State Machine

```
TCP STATE MACHINE
──────────────────────────────────────────────────────────────────

CLIENT                                    SERVER
  │                                         │
  │  CLOSED                       CLOSED   │
  │    │                            │       │
  │    │ connect()                  │ bind()│
  │    │                            │ listen│
  │    ▼                            ▼       │
  │  SYN_SENT ──── SYN ──────► LISTEN     │
  │    │                        SYN_RCVD   │
  │    │       ◄── SYN+ACK ────   │        │
  │  ESTABLISHED                  │        │
  │    │         ─── ACK ──────► ESTABLISHED
  │    │                            │       │
  │    │         === DATA FLOWS ===  │      │
  │    │                            │       │
  │    │ close()                    │       │
  │    ▼                            │       │
  │  FIN_WAIT_1 ── FIN ─────────►  │       │
  │    │                        CLOSE_WAIT  │
  │  FIN_WAIT_2                    │        │
  │    │       ◄── FIN ──────── LAST_ACK   │
  │  TIME_WAIT                     │        │
  │    │        ─── ACK ─────────► CLOSED  │
  │    │ (wait 2*MSL = 60s)                 │
  │    ▼                                    │
  │  CLOSED                                 │

TIME_WAIT: Prevents stale packets from previous connection
           being mistaken for new connection data.
           2*MSL = 2 × Maximum Segment Lifetime = ~60 seconds.
           This is why "Address already in use" errors occur!
           Fix: SO_REUSEADDR socket option
```

### 7.4 C Implementation — Raw Socket Network Programming

```c
// network_stack.c
// Low-level socket programming demonstrating kernel network path
// Compile: gcc -O2 -o net_demo network_stack.c

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <signal.h>

#define MAX_EVENTS   64
#define BUFFER_SIZE  4096

/* ─────────────────────────────────────────────────────────
 * Set socket to non-blocking mode
 * The kernel's socket file op sets O_NONBLOCK on the fd
 * ───────────────────────────────────────────────────────── */
static int set_nonblocking(int fd)
{
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

/* ─────────────────────────────────────────────────────────
 * Demonstrate TCP socket options (kernel sk_buff tunables)
 * ───────────────────────────────────────────────────────── */
void demonstrate_socket_options(int sockfd)
{
    /* TCP_NODELAY: disable Nagle's algorithm
     * Nagle batches small writes into one segment.
     * Disable for latency-sensitive apps (gaming, trading) */
    int nodelay = 1;
    setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY,
               &nodelay, sizeof(nodelay));
    printf("  TCP_NODELAY: enabled (no Nagle batching)\n");

    /* SO_REUSEADDR: allow reuse of TIME_WAIT addresses
     * Essential for servers that restart quickly */
    int reuse = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR,
               &reuse, sizeof(reuse));
    printf("  SO_REUSEADDR: enabled\n");

    /* SO_RCVBUF / SO_SNDBUF: TCP buffer sizes
     * Kernel sets aside this much memory per socket
     * For high-throughput: increase to 256KB or more
     * Bandwidth-delay product = throughput × RTT */
    int bufsize = 256 * 1024; // 256KB
    setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
    setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));

    /* Read back actual values (kernel may double them!) */
    int actual_rcv, actual_snd;
    socklen_t len = sizeof(actual_rcv);
    getsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &actual_rcv, &len);
    getsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &actual_snd, &len);
    printf("  SO_RCVBUF: %d bytes (requested %d)\n", actual_rcv, bufsize);
    printf("  SO_SNDBUF: %d bytes (kernel doubled it)\n", actual_snd);

    /* TCP_KEEPALIVE: detect dead connections
     * Kernel sends probe packets on idle connections */
    int keepalive = 1;
    int keepidle  = 60;   // seconds before first probe
    int keepintvl = 10;   // seconds between probes
    int keepcnt   = 3;    // probes before giving up
    setsockopt(sockfd, SOL_SOCKET,  SO_KEEPALIVE,  &keepalive, sizeof(keepalive));
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPIDLE,  &keepidle,  sizeof(keepidle));
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPCNT,   &keepcnt,   sizeof(keepcnt));
    printf("  TCP_KEEPALIVE: enabled\n");
}

/* ─────────────────────────────────────────────────────────
 * Epoll server — non-blocking I/O with kernel event queue
 * epoll is the scalable I/O multiplexer (Linux-specific)
 * Uses kernel's event-driven notification (replaces select/poll)
 * ───────────────────────────────────────────────────────── */
void epoll_server_demo(uint16_t port)
{
    printf("\n=== Epoll Non-Blocking Server Demo ===\n");
    printf("Listening on port %d (connect with: nc localhost %d)\n",
           port, port);

    /* Create listening socket */
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) { perror("socket"); return; }

    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

    printf("\nSocket options:\n");
    demonstrate_socket_options(listen_fd);

    set_nonblocking(listen_fd);

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(port),
        .sin_addr.s_addr = INADDR_ANY,
    };

    if (bind(listen_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind"); close(listen_fd); return;
    }

    /*
     * listen(backlog=128): kernel maintains two queues:
     * 1. SYN queue: incomplete connections (SYN received, SYN+ACK sent)
     *    Size: net.ipv4.tcp_max_syn_backlog
     * 2. Accept queue: complete connections (ACK received)
     *    Size: backlog parameter (here: 128)
     */
    listen(listen_fd, 128);

    /*
     * epoll: kernel-side event queue
     * epoll_create1() returns an fd to a kernel data structure
     * that tracks which fds have events ready
     *
     * INTERNAL: uses red-black tree to store watched fds
     *           and a linked list for ready events
     * Complexity: O(1) for add/modify, O(1) for wait (events ready)
     * vs poll/select: O(N) — scan all fds each call
     */
    int epoll_fd = epoll_create1(EPOLL_CLOEXEC);
    if (epoll_fd < 0) { perror("epoll_create1"); close(listen_fd); return; }

    struct epoll_event ev = {
        .events  = EPOLLIN | EPOLLET,  // edge-triggered!
        .data.fd = listen_fd,
    };
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, listen_fd, &ev);

    printf("\nWaiting for connections (will timeout after 3 seconds)...\n");

    struct epoll_event events[MAX_EVENTS];
    int connected_clients = 0;

    for (int iter = 0; iter < 3; iter++) {
        /* epoll_wait: sleeps until an event fires
         * Kernel wakes us via waitqueue when socket has data
         * timeout=1000ms: return even if no events */
        int nready = epoll_wait(epoll_fd, events, MAX_EVENTS, 1000);

        if (nready == 0) {
            printf("  [%ds] No events (epoll_wait timeout)\n", iter + 1);
            continue;
        }

        for (int i = 0; i < nready; i++) {
            if (events[i].data.fd == listen_fd) {
                /* New connection ready in accept queue */
                struct sockaddr_in client_addr;
                socklen_t clen = sizeof(client_addr);
                int client_fd = accept4(listen_fd,
                                        (struct sockaddr*)&client_addr,
                                        &clen, SOCK_NONBLOCK);
                if (client_fd >= 0) {
                    char client_ip[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &client_addr.sin_addr,
                              client_ip, sizeof(client_ip));
                    printf("  Accepted connection from %s:%d (fd=%d)\n",
                           client_ip, ntohs(client_addr.sin_port), client_fd);

                    struct epoll_event cev = {
                        .events  = EPOLLIN | EPOLLET | EPOLLHUP,
                        .data.fd = client_fd,
                    };
                    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &cev);
                    connected_clients++;
                }
            } else {
                /* Data ready on client socket */
                char buf[BUFFER_SIZE];
                ssize_t n = recv(events[i].data.fd, buf, sizeof(buf)-1, 0);
                if (n > 0) {
                    buf[n] = '\0';
                    printf("  Received %zd bytes: %.50s\n", n, buf);
                    /* Echo back */
                    send(events[i].data.fd, buf, n, 0);
                } else {
                    /* Client disconnected */
                    printf("  Client fd=%d disconnected\n", events[i].data.fd);
                    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, events[i].data.fd, NULL);
                    close(events[i].data.fd);
                }
            }
        }
    }

    printf("Epoll demo complete. Clients seen: %d\n", connected_clients);
    close(epoll_fd);
    close(listen_fd);
}

/* Read network stats from kernel */
void read_network_stats(void)
{
    printf("\n=== Kernel Network Statistics ===\n");
    FILE *f = fopen("/proc/net/sockstat", "r");
    if (f) {
        char line[256];
        printf("Socket statistics (/proc/net/sockstat):\n");
        while (fgets(line, sizeof(line), f))
            printf("  %s", line);
        fclose(f);
    }

    f = fopen("/proc/net/snmp", "r");
    if (f) {
        printf("\nTCP statistics (first 3 lines):\n");
        char line[512];
        int count = 0;
        while (fgets(line, sizeof(line), f) && count < 4) {
            if (strncmp(line, "Tcp:", 4) == 0) {
                printf("  %s", line);
                count++;
            }
        }
        fclose(f);
    }
}

int main(void)
{
    signal(SIGPIPE, SIG_IGN); /* Ignore broken pipe */

    printf("╔═══════════════════════════════════════╗\n");
    printf("║   Linux Network Stack — Deep Dive     ║\n");
    printf("╚═══════════════════════════════════════╝\n\n");

    read_network_stats();
    epoll_server_demo(18888);

    return 0;
}
```

---

# PART VI — DEVICE DRIVERS & I/O

---

## Chapter 8: Device Driver Architecture

### 8.1 Everything is a File

**Core UNIX philosophy:** Every device is accessible through the filesystem as a special file. This unifies the interface — programs read/write devices using the same `open()`/`read()`/`write()` calls as regular files.

```
DEVICE FILE HIERARCHY
──────────────────────────────────────────────────────────────────

/dev/
├── sda           ← SCSI/SATA disk (block device, major=8, minor=0)
├── sda1          ← first partition (major=8, minor=1)
├── sdb           ← second disk (major=8, minor=16)
├── nvme0n1       ← NVMe SSD (major=259, minor=0)
├── tty0          ← terminal (char device, major=4, minor=0)
├── ttyS0         ← serial port (char device, major=4, minor=64)
├── null          ← bit bucket (char device, major=1, minor=3)
├── zero          ← zero source (char device, major=1, minor=5)
├── random        ← random bytes (char device, major=1, minor=8)
├── urandom       ← non-blocking random (char device, major=1, minor=9)
├── mem           ← physical memory access! (char device, major=1, minor=1)
├── kmem          ← kernel virtual memory
├── loop0         ← loopback block device (for mounting images)
├── net/tun       ← TUN/TAP virtual network device
└── mapper/       ← device mapper (LVM, LUKS encryption)

DEVICE NUMBERS:
  MAJOR: identifies the DRIVER (which code handles this device)
  MINOR: identifies the SPECIFIC DEVICE within that driver
  
  ls -la /dev/sda:
  brw-rw---- 1 root disk 8, 0 Jan 1 00:00 /dev/sda
                         ^  ^
                         major=8  minor=0
```

### 8.2 Driver Types

```
DEVICE DRIVER TYPES
──────────────────────────────────────────────────────────────────

CHARACTER DEVICES:
  - Data stream: byte-by-byte access
  - No seek (or seek is meaningless)
  - Examples: serial ports, keyboards, mice, /dev/random
  
  User  → open() → read()/write() → close()
  Driver→ .open  → .read/.write  → .release
  (no block cache: data goes directly to driver)

BLOCK DEVICES:
  - Random access to fixed-size blocks (512B or 4096B)
  - Can seek to any block
  - Cached via page cache
  - Examples: hard disks, SSDs, USB drives
  
  User  → read(fd, ...) → VFS → page cache → block layer → driver → hardware
  (data cached: repeated reads don't hit hardware)
  
NETWORK DEVICES:
  - NOT accessed through /dev
  - Accessed through socket API
  - Have network interface names (eth0, wlan0, lo)
  - Registered with net_device struct

DRIVER FRAMEWORK LAYERS:
  ┌────────────────────────────────────────────────────────────┐
  │ User Space: open("/dev/sda"), read/write                   │
  ├────────────────────────────────────────────────────────────┤
  │ VFS: file operations dispatch                              │
  ├────────────────────────────────────────────────────────────┤
  │ Block Layer: I/O scheduler, merging, reordering            │
  ├────────────────────────────────────────────────────────────┤
  │ SCSI Layer (or NVMe, etc.)                                 │
  ├────────────────────────────────────────────────────────────┤
  │ HBA Driver (e.g., megaraid, ahci, nvme)                    │
  ├────────────────────────────────────────────────────────────┤
  │ Hardware: DMA, IRQ                                         │
  └────────────────────────────────────────────────────────────┘
```

### 8.3 C Implementation — Simple Character Driver

```c
// simple_chardev.c — minimal character device driver
// This is a KERNEL MODULE — runs in kernel space!
// Build with: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
// Load with:  insmod simple_chardev.ko
// Test with:  echo "hello" > /dev/simple_chardev
//             cat /dev/simple_chardev

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Practitioner");
MODULE_DESCRIPTION("Simple character device driver");

#define DEVICE_NAME  "simple_chardev"
#define CLASS_NAME   "simple"
#define BUFFER_SIZE  4096

/* Driver state */
static int          major_number;
static struct class *device_class;
static struct cdev  chardev_cdev;
static char        *kernel_buffer;
static size_t       data_size;
static DEFINE_MUTEX(chardev_mutex);   /* Protects kernel_buffer */

/*
 * open() handler: called when user does open("/dev/simple_chardev")
 * struct inode: represents the device file in VFS
 * struct file:  represents this open instance
 */
static int chardev_open(struct inode *inode, struct file *file)
{
    mutex_lock(&chardev_mutex);
    /* file->private_data can store per-open-instance state */
    file->private_data = NULL;
    mutex_unlock(&chardev_mutex);

    pr_info("simple_chardev: opened (PID %d)\n", current->pid);
    return 0;
}

/*
 * release() handler: called when file descriptor is closed
 */
static int chardev_release(struct inode *inode, struct file *file)
{
    pr_info("simple_chardev: closed\n");
    return 0;
}

/*
 * read() handler: copies data from kernel buffer to user space
 * CRITICAL: must use copy_to_user(), NOT memcpy()!
 * copy_to_user handles:
 *   1. Page faults (user page may not be resident)
 *   2. Permission checks (is this user address writable?)
 *   3. SMAP/SMEP hardware protections
 */
static ssize_t chardev_read(struct file  *file,
                             char __user  *user_buf,
                             size_t        count,
                             loff_t       *offset)
{
    ssize_t bytes_read;

    mutex_lock(&chardev_mutex);

    /* Check how much data remains from current offset */
    if (*offset >= data_size) {
        mutex_unlock(&chardev_mutex);
        return 0;  /* EOF */
    }

    /* Don't read past end of data */
    bytes_read = min(count, data_size - (size_t)*offset);

    /*
     * copy_to_user: safe kernel→user copy
     * Returns: number of bytes NOT copied (0 on success)
     */
    if (copy_to_user(user_buf, kernel_buffer + *offset, bytes_read)) {
        mutex_unlock(&chardev_mutex);
        return -EFAULT;  /* Bad user address */
    }

    *offset += bytes_read;
    mutex_unlock(&chardev_mutex);

    pr_info("simple_chardev: read %zd bytes\n", bytes_read);
    return bytes_read;
}

/*
 * write() handler: copies data from user space to kernel buffer
 */
static ssize_t chardev_write(struct file        *file,
                              const char __user  *user_buf,
                              size_t              count,
                              loff_t             *offset)
{
    mutex_lock(&chardev_mutex);

    if (count > BUFFER_SIZE - 1) {
        mutex_unlock(&chardev_mutex);
        return -ENOSPC;
    }

    /*
     * copy_from_user: safe user→kernel copy
     * NEVER use strcpy/memcpy from user pointers!
     */
    if (copy_from_user(kernel_buffer, user_buf, count)) {
        mutex_unlock(&chardev_mutex);
        return -EFAULT;
    }

    kernel_buffer[count] = '\0';
    data_size = count;

    mutex_unlock(&chardev_mutex);

    pr_info("simple_chardev: wrote %zu bytes: %s\n", count, kernel_buffer);
    return count;
}

/*
 * ioctl() handler: device-specific control operations
 * Allows complex commands beyond read/write
 * Used by: disk controllers, video devices, network interfaces
 */
static long chardev_ioctl(struct file  *file,
                           unsigned int  cmd,
                           unsigned long arg)
{
    switch (cmd) {
    case 0x1001:  /* Custom: get data size */
        if (copy_to_user((size_t __user*)arg, &data_size, sizeof(size_t)))
            return -EFAULT;
        return 0;

    case 0x1002:  /* Custom: clear buffer */
        mutex_lock(&chardev_mutex);
        memset(kernel_buffer, 0, BUFFER_SIZE);
        data_size = 0;
        mutex_unlock(&chardev_mutex);
        return 0;

    default:
        return -ENOTTY;  /* Inappropriate ioctl for device */
    }
}

/*
 * file_operations vtable:
 * This is the "vtable" that VFS calls through.
 * Each function pointer corresponds to a system call.
 */
static const struct file_operations chardev_fops = {
    .owner          = THIS_MODULE,
    .open           = chardev_open,
    .release        = chardev_release,
    .read           = chardev_read,
    .write          = chardev_write,
    .unlocked_ioctl = chardev_ioctl,
    /* Optional: .poll, .mmap, .llseek, .fsync */
};

/* Module initialization — called on insmod */
static int __init chardev_init(void)
{
    /* Allocate kernel buffer from SLAB */
    kernel_buffer = kzalloc(BUFFER_SIZE, GFP_KERNEL);
    if (!kernel_buffer)
        return -ENOMEM;

    /* Dynamically allocate a major number */
    major_number = register_chrdev(0, DEVICE_NAME, &chardev_fops);
    if (major_number < 0) {
        kfree(kernel_buffer);
        return major_number;
    }

    /* Create device class (appears in /sys/class/) */
    device_class = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(device_class)) {
        unregister_chrdev(major_number, DEVICE_NAME);
        kfree(kernel_buffer);
        return PTR_ERR(device_class);
    }

    /* Create the device node in /dev/ automatically (via udev) */
    device_create(device_class, NULL,
                  MKDEV(major_number, 0), NULL, DEVICE_NAME);

    pr_info("simple_chardev: loaded, major=%d\n", major_number);
    pr_info("simple_chardev: created /dev/%s\n", DEVICE_NAME);
    return 0;
}

/* Module cleanup — called on rmmod */
static void __exit chardev_exit(void)
{
    device_destroy(device_class, MKDEV(major_number, 0));
    class_destroy(device_class);
    unregister_chrdev(major_number, DEVICE_NAME);
    kfree(kernel_buffer);
    pr_info("simple_chardev: unloaded\n");
}

module_init(chardev_init);
module_exit(chardev_exit);
```

---

# PART VII — INTER-PROCESS COMMUNICATION (IPC)

---

## Chapter 9: IPC Mechanisms

### 9.1 IPC Overview

**Definition:** IPC (Inter-Process Communication) is any mechanism that allows processes to exchange data or synchronize.

```
IPC MECHANISM COMPARISON
──────────────────────────────────────────────────────────────────

Mechanism        Speed    Persistence  Structured?  Multi-process?
─────────────────────────────────────────────────────────────────
Pipe (anonymous) Fast     None         No           Parent-child only
Named Pipe(FIFO) Fast     FS path      No           Any processes
Unix Domain Sock Very Fast None        Yes          Any processes
TCP Socket       Med      None         Yes          Network-wide
Shared Memory    Fastest  Explicit     Manual       Any processes
Message Queue    Med      Optional     Yes          Any processes
Semaphore        N/A      Optional     N/A          Any processes
Signal           None     None         Limited      Any processes
mmap(file)       Fast     File         Manual       Any processes
─────────────────────────────────────────────────────────────────

RULE OF THUMB:
  Same machine, max speed: Shared Memory + Semaphore
  Structured messages:     Unix Domain Socket or Message Queue
  Network:                 TCP/UDP Socket
  Simple notification:     Signal or Pipe
  Event notification:      eventfd, signalfd
```

### 9.2 Pipes — The Simplest IPC

```
PIPE INTERNALS
──────────────────────────────────────────────────────────────────

pipe(fds) creates:
  - A kernel ring buffer (default 64KB since Linux 2.6.11)
  - Two file descriptors: fds[0]=read end, fds[1]=write end
  - Both are VFS file objects pointing to pipe inode

Parent forks → child inherits fds:

  Parent           Kernel Pipe Buffer         Child
  ┌──────┐         ┌──────────────────┐       ┌──────┐
  │write │─────── ►│  [data bytes...] │──────►│read  │
  │ fd[1]│         │  ring buffer     │       │ fd[0]│
  └──────┘         └──────────────────┘       └──────┘
  
  Shell: ls | grep foo
  Creates pipe, fork ls with stdout→pipe_write,
                     grep with stdin→pipe_read

BLOCKING BEHAVIOR:
  write() blocks if buffer FULL  (reader too slow)
  read()  blocks if buffer EMPTY (writer too slow)
  This provides natural flow control!

SPLICE SYSTEM CALL:
  splice(pipe_fd, NULL, socket_fd, NULL, size, SPLICE_F_MOVE)
  Transfers data from pipe to socket WITHOUT kernel→user→kernel copy
  Zero-copy! Data stays in kernel page cache.
  Used by: nginx, web servers for sendfile-like operations
```

### 9.3 Shared Memory — Fastest IPC

```
SHARED MEMORY MECHANISM
──────────────────────────────────────────────────────────────────

Process A VAS          Physical RAM          Process B VAS
┌──────────────┐                           ┌──────────────┐
│              │       ┌──────────────┐    │              │
│  0x7f00_0000 │──────►│   SHARED     │◄───│  0x7f80_0000 │
│  mmap region │       │   PHYSICAL   │    │  mmap region │
│  (512KB)     │       │   PAGES      │    │  (512KB)     │
│              │       │  (same RAM   │    │              │
│  Private     │       │   frames!)   │    │  Private     │
│  pages...    │       └──────────────┘    │  pages...    │
└──────────────┘                           └──────────────┘

Both processes see the SAME data instantly — no copy!
But: RACE CONDITIONS! Need synchronization (semaphore/mutex)

Two APIs:
  1. POSIX: shm_open() + mmap()     (modern, preferred)
  2. SysV:  shmget() + shmat()      (legacy, still used)
```

### 9.4 C Implementation — Complete IPC Showcase

```c
// ipc_showcase.c
// Demonstrates pipes, shared memory, semaphores, message queues
// Compile: gcc -O2 -o ipc_demo ipc_showcase.c -lpthread -lrt

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <semaphore.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <mqueue.h>
#include <errno.h>
#include <time.h>

/* ─────────────────────────────────────────────────────────
 * DEMO 1: Anonymous Pipe
 * ───────────────────────────────────────────────────────── */

void demo_pipe(void)
{
    printf("\n=== Anonymous Pipe Demo ===\n");

    int pipefd[2];
    if (pipe(pipefd) != 0) { perror("pipe"); return; }

    pid_t pid = fork();
    if (pid == 0) {
        /* Child: writer */
        close(pipefd[0]); // close read end

        const char *messages[] = {
            "Message 1: Hello from child!",
            "Message 2: Pipes are FIFO queues",
            "Message 3: Data buffered in kernel",
        };

        for (int i = 0; i < 3; i++) {
            write(pipefd[1], messages[i], strlen(messages[i]) + 1);
            printf("  [child] wrote: %s\n", messages[i]);
            usleep(100000); // 100ms
        }

        close(pipefd[1]); // EOF signal to reader
        exit(0);

    } else {
        /* Parent: reader */
        close(pipefd[1]); // close write end

        char buf[256];
        ssize_t n;
        while ((n = read(pipefd[0], buf, sizeof(buf))) > 0) {
            printf("  [parent] read: %s\n", buf);
        }
        printf("  [parent] pipe closed (EOF)\n");
        close(pipefd[0]);
        wait(NULL);
    }
}

/* ─────────────────────────────────────────────────────────
 * DEMO 2: POSIX Shared Memory + Semaphore
 * The fastest IPC — zero copies
 * ───────────────────────────────────────────────────────── */

#define SHM_NAME  "/demo_shm"
#define SEM_NAME  "/demo_sem"

typedef struct {
    sem_t  mutex;         /* protects the data */
    sem_t  data_ready;    /* signals new data available */
    int    value;
    char   message[128];
    int    done;
} SharedData;

void demo_shared_memory(void)
{
    printf("\n=== POSIX Shared Memory + Semaphore Demo ===\n");

    /* Create shared memory segment */
    int shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0600);
    if (shm_fd < 0) { perror("shm_open"); return; }

    ftruncate(shm_fd, sizeof(SharedData));

    /* Map into our address space */
    SharedData *shared = mmap(NULL, sizeof(SharedData),
                               PROT_READ | PROT_WRITE,
                               MAP_SHARED, shm_fd, 0);
    close(shm_fd);

    if (shared == MAP_FAILED) { perror("mmap"); return; }

    /* Initialize semaphores IN SHARED MEMORY (pshared=1 → cross-process) */
    sem_init(&shared->mutex,      1, 1); // binary mutex, initial=1
    sem_init(&shared->data_ready, 1, 0); // signaling, initial=0
    shared->done = 0;

    pid_t pid = fork();
    if (pid == 0) {
        /* Child: producer — writes to shared memory */
        for (int i = 0; i < 5; i++) {
            sem_wait(&shared->mutex);            // lock
            shared->value = i * 100;
            snprintf(shared->message, 128, "Item %d from producer", i);
            printf("  [producer] wrote: value=%d msg='%s'\n",
                   shared->value, shared->message);
            sem_post(&shared->mutex);            // unlock
            sem_post(&shared->data_ready);       // signal consumer
            usleep(50000);
        }

        sem_wait(&shared->mutex);
        shared->done = 1;
        sem_post(&shared->mutex);
        sem_post(&shared->data_ready);
        exit(0);

    } else {
        /* Parent: consumer — reads from shared memory */
        while (1) {
            sem_wait(&shared->data_ready);       // wait for signal
            sem_wait(&shared->mutex);            // lock

            if (shared->done) {
                sem_post(&shared->mutex);
                break;
            }

            printf("  [consumer] read:  value=%d msg='%s'\n",
                   shared->value, shared->message);
            sem_post(&shared->mutex);            // unlock
        }

        wait(NULL);
    }

    /* Cleanup */
    sem_destroy(&shared->mutex);
    sem_destroy(&shared->data_ready);
    munmap(shared, sizeof(SharedData));
    shm_unlink(SHM_NAME);
    printf("  Shared memory cleanup complete\n");
}

/* ─────────────────────────────────────────────────────────
 * DEMO 3: POSIX Message Queue
 * Kernel-managed queue — messages have priority
 * ───────────────────────────────────────────────────────── */

#define MQ_NAME "/demo_mq"

void demo_message_queue(void)
{
    printf("\n=== POSIX Message Queue Demo ===\n");

    /* Remove any existing queue */
    mq_unlink(MQ_NAME);

    struct mq_attr attrs = {
        .mq_flags   = 0,
        .mq_maxmsg  = 10,   /* max messages in queue */
        .mq_msgsize = 256,  /* max message size */
    };

    mqd_t mq = mq_open(MQ_NAME, O_CREAT | O_RDWR, 0600, &attrs);
    if (mq == (mqd_t)-1) { perror("mq_open"); return; }

    pid_t pid = fork();
    if (pid == 0) {
        /* Child: sender — sends messages with different priorities */
        struct { int priority; const char *text; } msgs[] = {
            {5, "Low priority message"},
            {9, "HIGH PRIORITY — process first!"},
            {5, "Another low priority"},
            {7, "Medium priority"},
        };

        for (int i = 0; i < 4; i++) {
            /*
             * mq_send(mq, msg, len, priority):
             * Higher priority messages are DEQUEUED FIRST
             * This is a priority queue in the kernel!
             */
            if (mq_send(mq, msgs[i].text, strlen(msgs[i].text)+1,
                        msgs[i].priority) == 0) {
                printf("  [sender] sent (prio=%d): %s\n",
                       msgs[i].priority, msgs[i].text);
            }
        }
        exit(0);
    } else {
        wait(NULL);
        /* Parent: receiver — messages arrive in priority order */
        char buf[256];
        unsigned int priority;
        printf("  [receiver] reading (highest priority first):\n");
        for (int i = 0; i < 4; i++) {
            ssize_t n = mq_receive(mq, buf, sizeof(buf), &priority);
            if (n > 0) {
                printf("  [receiver] got (prio=%u): %s\n", priority, buf);
            }
        }
    }

    mq_close(mq);
    mq_unlink(MQ_NAME);
}

int main(void)
{
    printf("╔═════════════════════════════════════╗\n");
    printf("║   Linux IPC Mechanisms Deep Dive    ║\n");
    printf("╚═════════════════════════════════════╝\n");

    demo_pipe();
    demo_shared_memory();
    demo_message_queue();

    return 0;
}
```

---

# PART VIII — SYNCHRONIZATION & CONCURRENCY

---

## Chapter 10: Kernel Locking Primitives

### 10.1 The Concurrency Problem

**Why locking exists:** Modern CPUs have multiple cores executing simultaneously. If two cores modify the same data structure without coordination, data corruption occurs (race condition).

```
RACE CONDITION EXAMPLE — Counter increment
──────────────────────────────────────────────────────────────────

Shared variable: count = 0

CPU 0 (Thread A):                  CPU 1 (Thread B):
  LOAD  r1, count    (r1=0)
                                     LOAD  r1, count    (r1=0)
  ADD   r1, 1        (r1=1)
                                     ADD   r1, 1        (r1=1)
  STORE count, r1    (count=1)
                                     STORE count, r1    (count=1)

Final: count=1  (WRONG! Should be 2)

This is a RACE CONDITION. The sequence was:
  load, load, add, add, store, store
Instead of:
  load, add, store, load, add, store

Solution: Make the load-modify-store ATOMIC (indivisible)
```

### 10.2 Linux Kernel Locking Primitives

```
LOCKING PRIMITIVE DECISION TREE
──────────────────────────────────────────────────────────────────

Need to protect shared data?
         │
         ▼
Is it a single integer counter? ──YES──► atomic_t / atomic64_t
         │NO                             (hardware atomic ops)
         ▼
Is the critical section very short AND ──YES──► spinlock_t
can interrupt handlers access it?                (busy-wait)
         │NO
         ▼
Can you sleep in the critical section? ──NO───► spinlock_t or
         │YES                                   rwlock_t
         ▼
Multiple readers, rare writers? ──YES──► rwsem (read-write semaphore)
         │NO                             or rw_semaphore
         ▼
Need recursive locking? ──YES──► mutex (or design around it)
         │NO
         ▼
                               ──────► mutex_t
                                       (most common choice)

ADDITIONAL:
  RCU (Read-Copy-Update): for frequently-read, rarely-written data
  Seqlocks: for small frequently-written data (jiffies, time)
  Per-CPU variables: eliminate sharing entirely
```

### 10.3 Spinlock vs Mutex

```
SPINLOCK                           MUTEX
────────────────────────────────────────────────────────────────
spin_lock(lock):                   mutex_lock(mutex):
  while (!try_acquire(lock))         if (lock held):
    ; /* busy spin — wasting CPU */    put self to sleep
                                       schedule() → other tasks run
                                     acquire lock
                                     wake up (lock released)

USE WHEN:                          USE WHEN:
- Critical section < few μs        - Critical section > few μs
- Cannot sleep (interrupt handler) - Can sleep (process context)
- Lock contention rare             - Lock may be held a while

COST OF SPINNING:                  COST OF SLEEPING:
- Burns CPU cycles                 - Context switch overhead (~1μs)
- BUT: no context switch           - But: no CPU wasted while waiting
- Good if you get lock QUICKLY     - Good if lock held a long time

INTERRUPT CONTEXT RULE:
  Interrupt handlers CANNOT sleep (no process context!)
  So interrupt handlers MUST use spinlocks, not mutexes.
  
  If spinlock held in interrupt handler, you MUST also
  disable interrupts on that CPU while holding it:
  spin_lock_irqsave(lock, flags)
```

### 10.4 RCU — Read-Copy-Update

**RCU is the most sophisticated locking mechanism in the Linux kernel.** It allows reads with *zero* overhead (no lock acquired!) while ensuring safe updates.

```
RCU CONCEPT — Hazard Pointers for the Kernel
──────────────────────────────────────────────────────────────────

PROBLEM: A linked list has millions of reads per second.
         A spinlock would be a bottleneck.
         
RCU INSIGHT:
  Reads: NO LOCK — just protect with rcu_read_lock() (disables preemption)
  Writes: Copy, modify copy, atomically swap pointer, then free OLD
          Wait for all readers to finish (quiescent state)

LINKED LIST NODE UPDATE:
                                         
Before:   [head]──►[A]──►[B]──►[C]──►NULL

Writer wants to update [B]:

Step 1: Allocate new node [B2] = copy of [B], with changes
  [head]──►[A]──►[B]──►[C]──►NULL
                 ↕
               [B2] (new, modified)

Step 2: Atomically: A.next = B2  (rcu_assign_pointer)
  [head]──►[A]──►[B2]──►[C]──►NULL
             └──►[B] (old, readers may still see this!)

Step 3: Wait for grace period — all CPUs pass through a quiescent state
  (All readers that could have seen [B] have finished)

Step 4: Free [B] (kfree_rcu or call_rcu)

Reader NEVER needs a lock! If it reads [B], that's fine — [B] is valid
until the grace period. RCU guarantees [B] won't be freed while read.

APPLICATIONS:
  - Process list (rcu_read_lock() when iterating task list)
  - Routing tables (read millions/sec, update rare)
  - Module list
  - Networking subsystem
```

### 10.5 C Implementation — Synchronization Primitives

```c
// synchronization.c
// Demonstrates mutex, spinlock, atomic, RW-lock, and RCU patterns
// Compile: gcc -O2 -o sync_demo synchronization.c -lpthread

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <stdatomic.h>
#include <time.h>

#define THREADS      8
#define ITERATIONS   1000000

/* ─────────────────────────────────────────────────────────
 * DEMO 1: Race condition (no protection) vs mutex vs atomic
 * ───────────────────────────────────────────────────────── */

long long  counter_unsafe  = 0;
long long  counter_mutex   = 0;
atomic_llong counter_atomic = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *increment_unsafe(void *arg)
{
    for (int i = 0; i < ITERATIONS; i++) {
        counter_unsafe++;  /* RACE CONDITION: non-atomic RMW */
    }
    return NULL;
}

void *increment_mutex(void *arg)
{
    for (int i = 0; i < ITERATIONS; i++) {
        pthread_mutex_lock(&mutex);
        counter_mutex++;   /* Protected: safe but slow */
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

void *increment_atomic(void *arg)
{
    for (int i = 0; i < ITERATIONS; i++) {
        atomic_fetch_add(&counter_atomic, 1);  /* Hardware atomic: fast! */
    }
    return NULL;
}

typedef struct {
    void *(*func)(void*);
    const char *name;
    long long *result;
} BenchTask;

void run_benchmark(BenchTask *task)
{
    pthread_t threads[THREADS];
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < THREADS; i++)
        pthread_create(&threads[i], NULL, task->func, NULL);
    for (int i = 0; i < THREADS; i++)
        pthread_join(threads[i], NULL);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double ms = (end.tv_sec - start.tv_sec) * 1000.0
                + (end.tv_nsec - start.tv_nsec) / 1e6;
    long long expected = (long long)THREADS * ITERATIONS;

    printf("  %-15s result=%-12lld expected=%-12lld time=%.1fms %s\n",
           task->name,
           *task->result,
           expected,
           ms,
           (*task->result == expected) ? "[CORRECT]" : "[RACE!]");
}

/* ─────────────────────────────────────────────────────────
 * DEMO 2: Read-Write Lock for reader-writer problem
 * Multiple readers can hold lock simultaneously
 * Writer gets exclusive access
 * ───────────────────────────────────────────────────────── */

typedef struct {
    pthread_rwlock_t lock;
    int data[1024];
    int version;
} SharedTable;

SharedTable table = {
    .lock    = PTHREAD_RWLOCK_INITIALIZER,
    .version = 0,
};

void *reader_thread(void *arg)
{
    int id = (int)(intptr_t)arg;
    for (int i = 0; i < 10; i++) {
        pthread_rwlock_rdlock(&table.lock);  /* Shared read lock */

        /* Multiple readers CAN hold this simultaneously */
        int v = table.version;
        int sum = 0;
        for (int j = 0; j < 10; j++) sum += table.data[j];

        pthread_rwlock_unlock(&table.lock);

        if (i == 0)
            printf("  [reader %d] version=%d sum=%d\n", id, v, sum);
        usleep(100);
    }
    return NULL;
}

void *writer_thread(void *arg)
{
    for (int i = 0; i < 5; i++) {
        pthread_rwlock_wrlock(&table.lock);  /* Exclusive write lock */

        /* Writer has exclusive access — no readers during this */
        table.version++;
        for (int j = 0; j < 10; j++)
            table.data[j] = table.version * (j + 1);

        printf("  [writer] updated to version=%d\n", table.version);
        pthread_rwlock_unlock(&table.lock);

        usleep(500);
    }
    return NULL;
}

/* ─────────────────────────────────────────────────────────
 * DEMO 3: Condition variable — wait/signal pattern
 * Equivalent to kernel's wait_event() / wake_up()
 * ───────────────────────────────────────────────────────── */

typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t  cond;
    int             items_ready;
    int             total_produced;
} Queue;

Queue queue = {
    .mutex          = PTHREAD_MUTEX_INITIALIZER,
    .cond           = PTHREAD_COND_INITIALIZER,
    .items_ready    = 0,
    .total_produced = 0,
};

void *producer(void *arg)
{
    for (int i = 0; i < 10; i++) {
        usleep(50000);  // simulate work

        pthread_mutex_lock(&queue.mutex);
        queue.items_ready++;
        queue.total_produced++;
        printf("  [producer] produced item %d\n", queue.total_produced);

        pthread_cond_signal(&queue.cond);  // Wake ONE waiting consumer
        pthread_mutex_unlock(&queue.mutex);
    }

    pthread_mutex_lock(&queue.mutex);
    queue.items_ready = -1;  // Sentinel: no more items
    pthread_cond_broadcast(&queue.cond);  // Wake ALL consumers
    pthread_mutex_unlock(&queue.mutex);
    return NULL;
}

void *consumer(void *arg)
{
    int id = (int)(intptr_t)arg;
    int consumed = 0;

    while (1) {
        pthread_mutex_lock(&queue.mutex);

        /* pthread_cond_wait: atomically unlock + sleep
         * When woken: re-acquire lock + return
         * ALWAYS check condition in WHILE loop (spurious wakeups!) */
        while (queue.items_ready == 0)
            pthread_cond_wait(&queue.cond, &queue.mutex);

        if (queue.items_ready < 0) {
            pthread_mutex_unlock(&queue.mutex);
            break;
        }

        queue.items_ready--;
        consumed++;
        pthread_mutex_unlock(&queue.mutex);
    }

    printf("  [consumer %d] consumed %d items total\n", id, consumed);
    return NULL;
}

int main(void)
{
    printf("╔══════════════════════════════════════════╗\n");
    printf("║   Linux Kernel Synchronization Patterns  ║\n");
    printf("╚══════════════════════════════════════════╝\n");

    printf("\n=== Counter Benchmark: %d threads × %d iterations ===\n",
           THREADS, ITERATIONS);

    long long unsafe_val  = 0; /* reset before run */
    BenchTask tasks[] = {
        { increment_unsafe, "unsafe",   &counter_unsafe  },
        { increment_mutex,  "mutex",    &counter_mutex   },
        { increment_atomic, "atomic",   (long long*)&counter_atomic },
    };

    for (int i = 0; i < 3; i++) {
        run_benchmark(&tasks[i]);
    }

    printf("\n=== Read-Write Lock Demo ===\n");
    {
        pthread_t readers[4], writer;
        pthread_create(&writer, NULL, writer_thread, NULL);
        for (int i = 0; i < 4; i++)
            pthread_create(&readers[i], NULL, reader_thread, (void*)(intptr_t)i);
        for (int i = 0; i < 4; i++)
            pthread_join(readers[i], NULL);
        pthread_join(writer, NULL);
    }

    printf("\n=== Condition Variable (Producer-Consumer) Demo ===\n");
    {
        pthread_t prod, cons[2];
        pthread_create(&prod, NULL, producer, NULL);
        for (int i = 0; i < 2; i++)
            pthread_create(&cons[i], NULL, consumer, (void*)(intptr_t)i);
        pthread_join(prod, NULL);
        for (int i = 0; i < 2; i++)
            pthread_join(cons[i], NULL);
    }

    return 0;
}
```

---

# PART IX — INTERRUPT & EXCEPTION HANDLING

---

## Chapter 11: Interrupts

### 11.1 What is an Interrupt?

**Definition:** An interrupt is an asynchronous signal from hardware (or software) that causes the CPU to stop executing the current task and run a special handler. This is how hardware communicates urgency.

```
INTERRUPT TYPES
──────────────────────────────────────────────────────────────────

HARDWARE INTERRUPTS (IRQ):
  - Generated by hardware devices
  - Example: NIC receives a packet → triggers IRQ
  - Example: Disk I/O completes → triggers IRQ
  - Example: Timer fires every 1ms → triggers IRQ 0
  - CPU jumps to interrupt handler (Interrupt Service Routine)

SOFTWARE INTERRUPTS / EXCEPTIONS:
  - Generated by CPU itself when executing instruction
  - Example: divide by zero → exception #0 (DE)
  - Example: page fault    → exception #14 (#PF)
  - Example: syscall (INT 0x80 or SYSCALL) → exception #128
  - Example: breakpoint (INT 3) → exception #3

INTER-PROCESSOR INTERRUPTS (IPI):
  - CPU sends interrupt to another CPU
  - Example: TLB shootdown (tell all CPUs to flush TLB entry)
  - Example: scheduler IPI (force re-schedule on another CPU)

INTERRUPT CONTROLLER (APIC on x86):
  Hardware IRQs → APIC → CPU

  External Device
       │IRQ
       ▼
  [IOAPIC] ─── routes to CPUs ───► [Local APIC on CPU 0]
                                    [Local APIC on CPU 1]
                                    [Local APIC on CPU 2]
                                    ...
  
  The IOAPIC routes each IRQ to one or more CPUs.
  The Local APIC delivers the interrupt to its CPU.
  Interrupt affinity (/proc/irq/N/smp_affinity) controls routing.
```

### 11.2 Interrupt Handling Flow

```
INTERRUPT HANDLING FLOWCHART
──────────────────────────────────────────────────────────────────

Hardware raises IRQ line
          │
          ▼
APIC receives interrupt signal
          │
          ▼
CPU finishes current instruction
          │
          ▼
CPU checks interrupt flag (IF in EFLAGS)
          │
     ┌────┴────┐
     │         │
  IF=1 (enabled)  IF=0 (cli'd — disabled)
     │              │
     │           Queue interrupt (pending)
     │              │
     │           Wait for sti/iret
     ▼
CPU automatically:
  1. Saves current SS:RSP (stack pointer) to TSS
  2. Switches to kernel stack
  3. Pushes RFLAGS, CS, RIP onto kernel stack
  4. Clears IF flag (interrupts now disabled!)
  5. Looks up handler in IDT[vector_number]
  6. Jumps to handler
          │
          ▼
[do_IRQ() — common interrupt entry point]
          │
          ▼
[irq_enter() — accounting, NOHZ update]
          │
          ▼
[handle_irq() — calls the registered handler]
          │
          ├── TOP HALF (runs in interrupt context, fast):
          │   - Acknowledge interrupt to hardware
          │   - Minimal critical work
          │   - Schedule BOTTOM HALF for deferred work
          │
          ▼
[irq_exit() — check for pending softirqs]
          │
          ├── BOTTOM HALF (deferred, can run with IRQs enabled):
          │   - Softirqs (most critical: NAPI networking)
          │   - Tasklets (serialized per tasklet)
          │   - Workqueues (in kernel thread context, can sleep)
          │
          ▼
[iret — restore RFLAGS (re-enables IF), CS, RIP]
          │
          ▼
Resume interrupted task
```

### 11.3 Softirqs and Tasklets

```
INTERRUPT CONTEXT DEFERRAL MECHANISMS
──────────────────────────────────────────────────────────────────

TOP HALF              BOTTOM HALF
────────────────      ────────────────────────────────────────────
Runs in hardirq       SOFTIRQ:
context               - Compiled-in, fixed set (10 types)
                      - Can run concurrently on multiple CPUs
IRQ disabled          - NET_TX_SOFTIRQ: transmit network packets
                      - NET_RX_SOFTIRQ: receive (NAPI poll)
CANNOT sleep          - TIMER_SOFTIRQ: run expired timers
                      - BLOCK_SOFTIRQ: block I/O completions
Must be fast          - SCHED_SOFTIRQ: load balancing
                      - HI_SOFTIRQ: tasklets (high priority)
                      - TASKLET_SOFTIRQ: tasklets
                      
                      TASKLET:
                      - Dynamic (can be created by any driver)
                      - Serialized: never runs on 2 CPUs at once
                      - Cannot sleep
                      - Built on HI_SOFTIRQ or TASKLET_SOFTIRQ
                      
                      WORKQUEUE:
                      - Runs in kernel THREAD context (kworker)
                      - CAN SLEEP (best choice when work may block)
                      - Used by: USB, I2C, many drivers
                      - schedule_work() → kworker thread processes it

EXAMPLE: Network Packet Receive
  NIC fires IRQ → top half: acknowledge NIC, schedule NAPI poll
  softirq runs: NAPI poll reads packets from NIC ring buffer
  → builds sk_buff → passes to TCP/IP stack
  This allows reading MANY packets per interrupt (batching)
```

---

# PART X — SYSTEM CALLS INTERFACE

---

## Chapter 12: System Calls

### 12.1 The System Call Boundary

**Definition:** A system call (syscall) is the mechanism by which user processes request kernel services. It is the **only legitimate gateway** from user space to kernel space.

```
SYSTEM CALL MECHANISM (x86-64 SYSCALL instruction)
──────────────────────────────────────────────────────────────────

User Space:                        Kernel Space:
─────────────                      ─────────────────────────────
int fd = open("/etc/passwd", 0)    sys_open(filename, flags, mode)

glibc wrapper:                          ↑
  1. Load syscall number in RAX         │
     (open = syscall #2)            entry_SYSCALL_64():
  2. Load args in RDI,RSI,RDX,R10     1. Swap to kernel stack (MSR LSTAR)
  3. Execute SYSCALL instruction      2. Save all user registers
                                      3. Enable interrupts
     ─── crosses privilege boundary ──►
                                      4. call do_syscall_64(regs)
                                         → sys_call_table[rax](args)
                                         → sys_open(filename,flags,mode)
                                      5. Returns result in RAX
     ◄── crosses privilege boundary ──
  4. Return value in RAX              6. SYSRET: restore user registers
     (negative = error → errno)          jump back to user code

SYSCALL TABLE:
  sys_call_table[0]   = sys_read
  sys_call_table[1]   = sys_write
  sys_call_table[2]   = sys_open
  sys_call_table[3]   = sys_close
  sys_call_table[9]   = sys_mmap
  sys_call_table[56]  = sys_clone
  sys_call_table[57]  = sys_fork
  sys_call_table[59]  = sys_execve
  sys_call_table[60]  = sys_exit
  sys_call_table[231] = sys_exit_group
  sys_call_table[333] = sys_io_uring_setup  (newest async I/O)
  ...
  (Linux 5.x has ~335+ syscalls)
```

### 12.2 io_uring — Modern Asynchronous I/O

```
IO_URING: THE NEXT GENERATION SYSCALL INTERFACE
──────────────────────────────────────────────────────────────────

Traditional I/O: One syscall per operation
  read() → context switch → kernel → return → context switch
  For N operations: N × (2 context switches)

io_uring: Batch operations via shared ring buffers

  User Space                    Kernel Space
  ──────────                    ────────────
  Submission Queue (SQ):        Completion Queue (CQ):
  ┌─────────────────────┐       ┌─────────────────────┐
  │ [op: read, fd=3    ]│       │ [result: 1024 bytes]│
  │ [op: write, fd=4   ]│       │ [result: 0 (ok)    ]│
  │ [op: read, fd=5    ]│       │ [result: -ENOENT   ]│
  │ [op: accept, fd=6  ]│       │ ...                 │
  └─────────────────────┘       └─────────────────────┘
         │                               ▲
         │  Shared memory (no copy!)     │
         └──────────────────────────────►┘

  io_uring_enter(ring_fd, N, 0, 0):
    Submit N operations from SQ
    Kernel processes them ASYNCHRONOUSLY
    Results appear in CQ (poll CQ or wait)
    
  For pure I/O-bound workloads: approach ZERO syscall overhead!
  Used by: databases (PostgreSQL), game engines, web servers
```

### 12.3 Rust Implementation — Direct Syscalls

```rust
// syscall_exploration.rs
// Demonstrates system call patterns in Rust
// Uses nix crate for safe syscall wrappers

use std::fs::{File, OpenOptions};
use std::io::{Read, Write, Seek, SeekFrom};
use std::os::unix::io::AsRawFd;
use std::time::Instant;

/// Demonstrates the read/write syscall path through strace
/// strace shows every syscall a process makes
fn demonstrate_file_syscalls() {
    println!("=== File System Call Path ===");
    println!("(Run under strace -c to see syscall counts)");

    // open() → creates file descriptor → VFS path lookup
    let mut f = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open("/tmp/syscall_demo.txt")
        .expect("open failed");

    let fd = f.as_raw_fd();
    println!("Opened fd={} (backed by struct file in kernel)", fd);

    // write() → sys_write → VFS → fs driver → page cache
    let data = b"Hello from Rust syscall demo\n";
    f.write_all(data).expect("write failed");
    println!("write({}, {} bytes) complete", fd, data.len());

    // fsync() → sys_fsync → flush page cache to disk
    // Guarantees durability (survives power loss after this)
    f.sync_all().expect("fsync failed");
    println!("fsync({}) — data flushed to disk", fd);

    drop(f);  // close() syscall

    // open for reading, read back
    let mut f = File::open("/tmp/syscall_demo.txt").expect("open failed");
    let mut content = String::new();
    f.read_to_string(&mut content).expect("read failed");
    println!("Read back: {:?}", content.trim());

    // lseek() — reposition file offset (O_APPEND bypasses this)
    f.seek(SeekFrom::Start(0)).expect("seek failed");
    println!("lseek(fd, 0, SEEK_SET) — rewound to beginning");

    std::fs::remove_file("/tmp/syscall_demo.txt").ok();
}

/// Measure syscall overhead
fn measure_syscall_overhead() {
    println!("\n=== Syscall Overhead Measurement ===");

    let iterations = 100_000u64;

    // getpid() is one of the cheapest syscalls
    // On Linux with VDSO, it may not even be a real syscall!
    let start = Instant::now();
    for _ in 0..iterations {
        let _pid = std::process::id();
    }
    let elapsed = start.elapsed();
    println!("getpid() × {} = {:.3} ms = {:.0} ns/call",
             iterations,
             elapsed.as_secs_f64() * 1000.0,
             elapsed.as_nanos() as f64 / iterations as f64);

    // VDSO (Virtual Dynamic Shared Object):
    // The kernel maps a read-only page into every process's address space
    // containing implementations of frequently-called "syscalls":
    // gettimeofday(), clock_gettime(), getpid() — NO privilege switch!
    // These read kernel data directly from a shared page.
    // This is why time() is so fast in Linux.

    let start = Instant::now();
    for _ in 0..iterations {
        let _now = Instant::now();
    }
    let elapsed = start.elapsed();
    println!("clock_gettime() × {} = {:.3} ms = {:.0} ns/call (VDSO!)",
             iterations,
             elapsed.as_secs_f64() * 1000.0,
             elapsed.as_nanos() as f64 / iterations as f64);

    // A real syscall with no VDSO — writing to /dev/null
    let null = OpenOptions::new()
        .write(true)
        .open("/dev/null")
        .expect("open /dev/null failed");
    let fd = null.as_raw_fd();

    let start = Instant::now();
    let buf = [0u8; 1];
    for _ in 0..10_000u64 {
        unsafe {
            libc::write(fd, buf.as_ptr() as *const _, 1);
        }
    }
    let elapsed = start.elapsed();
    println!("write(/dev/null, 1) × 10000 = {:.3} ms = {:.0} ns/call (real syscall)",
             elapsed.as_secs_f64() * 1000.0,
             elapsed.as_nanos() as f64 / 10_000.0);
}

fn main() {
    demonstrate_file_syscalls();
    measure_syscall_overhead();
}
```

---

# PART XI — SECURITY SUBSYSTEM (LSM)

---

## Chapter 13: Linux Security Modules

### 13.1 Security Architecture

```
LINUX SECURITY MODEL LAYERS
──────────────────────────────────────────────────────────────────

Layer 1: DAC (Discretionary Access Control) — built-in
  - File permission bits (rwxrwxrwx)
  - Owner UID/GID
  - Process effective UID
  - "Discretionary": owner decides who has access
  
Layer 2: Capabilities — granular root privileges
  - Traditional Unix: root = ALL privileges (0 or ALL)
  - Capabilities split root into 40+ individual privileges:
    CAP_NET_BIND_SERVICE: bind to port < 1024
    CAP_SYS_PTRACE:       attach debugger to any process
    CAP_NET_RAW:          use raw sockets
    CAP_KILL:             send signals to any process
    CAP_SYS_ADMIN:        many powerful operations
  - A process can have SOME root capabilities, not all

Layer 3: LSM (Linux Security Module) — pluggable MAC
  - MAC = Mandatory Access Control
  - Policy enforced by SYSTEM (not owner)
  - Examples:
    SELinux:   type enforcement, multi-level security
    AppArmor:  path-based profiles (simpler than SELinux)
    Seccomp:   restrict which syscalls a process can make
    SMACK:     Simplified Mandatory Access Control Kernel

LSM HOOK MECHANISM:
  At ~300+ security-sensitive points in the kernel, LSM hooks fire:
  
  sys_open("/etc/shadow", O_RDONLY):
    1. DAC check: is process UID allowed by file permissions?
    2. LSM hook: security_inode_permission(inode, MAY_READ)
       → SELinux: does this process type have read permission
                  on this file type?
       → AppArmor: does process profile allow reading this path?
    3. If any check fails → EACCES
```

### 13.2 Seccomp — System Call Filtering

```
SECCOMP: SYSCALL SANDBOXING
──────────────────────────────────────────────────────────────────

seccomp(SECCOMP_SET_MODE_FILTER, filter):
  Installs a BPF (Berkeley Packet Filter) program that runs
  on EVERY syscall made by the process!

BPF program: decides ALLOW or DENY for each syscall
  - Allow: syscall proceeds normally
  - Kill:  process killed immediately (SIGSYS)
  - Errno: syscall returns specific error
  - Trap:  send SIGSYS, debugger handles it
  - Trace: notify ptrace tracer

EXAMPLE FILTER (pseudocode BPF):
  if (syscall == read  || 
      syscall == write ||
      syscall == exit  ) → ALLOW
  else → KILL_PROCESS

USED BY:
  - Chrome/Chromium: renderer processes sandboxed with seccomp
  - Docker: default seccomp profile blocks dangerous syscalls
  - OpenSSH: post-auth process has restrictive seccomp filter
  - systemd: services can have SeccompFilter= in unit files
  - Flatpak, Snap: application sandboxing

CAPABILITIES + SECCOMP = Docker security model:
  Container gets minimal capabilities + syscall filter
  Even if container is compromised, attacker cannot:
  - Load kernel modules (no CAP_SYS_MODULE)
  - Access /dev/mem
  - reboot the system
  - Most privilege escalation exploits blocked!
```

---

# PART XII — POWER MANAGEMENT

---

## Chapter 14: Power Management Subsystem

### 14.1 Power States

```
SYSTEM POWER STATES (ACPI S-states)
──────────────────────────────────────────────────────────────────

S0: Working (full power)
  CPU clocks on, all hardware active

S1: Power On Suspend (rarely used)
  CPU clocks stopped, registers retained
  RAM powered and refreshing

S2: Not common
  CPU off, RAM powered

S3: Suspend to RAM (sleep)
  Most hardware off, RAM keeps power (self-refresh)
  Kernel saves CPU state to RAM
  Resume: ~1-3 seconds
  Triggered by: systemctl suspend

S4: Suspend to Disk (hibernate)
  Kernel image written to swap partition (hibernation image)
  ALL power off (truly off)
  Resume: ~10-30 seconds (read from disk)
  Triggered by: systemctl hibernate

S5: Soft Off (shutdown)
  OS halted, hardware power removed
  (Technically G2/S5 in ACPI)

CPU C-STATES (per-core idle states):
  C0: Active (executing instructions)
  C1: Halt (CPU halted, wakes on interrupt)
  C2: Stop Clock (deeper sleep, longer wake latency)
  C3: Sleep (cache flushed, more power saved)
  C6: Deep Power Down (on modern Intel — core nearly off)
  C10: Modern laptops — very deep sleep, <2mW per core

FREQUENCY SCALING (P-states):
  cpufreq governors control CPU frequency:
  - performance: always max frequency
  - powersave:   always min frequency  
  - schedutil:   frequency based on scheduler utilization (default)
  - ondemand:    legacy; ramp up quickly, decay slowly
```

### 14.2 Runtime PM

```
RUNTIME POWER MANAGEMENT
──────────────────────────────────────────────────────────────────

Devices can be powered off when not in use, even while system runs!

Example: USB device connected but idle:
  
  Device in use:
  ┌──────────────────────────────────────────────────────────┐
  │ rpm_get() → usage_count++ → device stays ON             │
  └──────────────────────────────────────────────────────────┘
  
  No I/O for autosuspend_delay (default 2 seconds):
  ┌──────────────────────────────────────────────────────────┐
  │ rpm_put() → usage_count-- → if count==0: schedule suspend│
  │ driver->runtime_suspend() called                        │
  │ Device enters D3 (off)                                  │
  └──────────────────────────────────────────────────────────┘
  
  New I/O arrives:
  ┌──────────────────────────────────────────────────────────┐
  │ rpm_get() → if device suspended: wake it first           │
  │ driver->runtime_resume() called                         │
  │ Device enters D0 (on)                                   │
  │ I/O proceeds                                            │
  └──────────────────────────────────────────────────────────┘

Power domains:
  Group devices that share power supply.
  Powering off domain powers off entire group at once.
  Device Tree / ACPI describes power domain topology.
```

---

# PART XIII — TIME & TIMER SUBSYSTEM

---

## Chapter 15: Timekeeping

### 15.1 Hardware Time Sources

```
HARDWARE CLOCKS (x86)
──────────────────────────────────────────────────────────────────

CLOCK SOURCE         RESOLUTION   COST      NOTES
───────────────────────────────────────────────────────────────────
RTC (Real Time Clock) 1 second    Very low  Battery-backed, survives power off
PIT (8254 timer)      ~1ms        Interrupt Legacy; fires timer IRQ
TSC (Time Stamp Cntr) 1 cycle    ~1ns      CPU register; rdtsc instruction
HPET                  100ns       Medium    High Precision Event Timer
APIC timer            ~100ns      Medium    Per-CPU; used for preemption

TSC:
  rdtsc reads a 64-bit counter incremented every CPU cycle
  CPU at 3GHz → ~0.33ns per tick
  FASTEST timekeeping: just read a CPU register (no syscall with VDSO!)
  
  Caveat: TSC may not be stable across CPU freq scaling
  Modern Intel/AMD: TSC is invariant (doesn't vary with P-state)
  Used by: CLOCK_MONOTONIC on modern kernels via VDSO

CLOCKSOURCE SELECTION:
  /sys/devices/system/clocksource/clocksource0/current_clocksource
  Kernel ranks clocksources and picks best available.
  On modern x86: tsc is default.
```

### 15.2 Timer Wheel and hrtimers

```
TIMER SUBSYSTEMS
──────────────────────────────────────────────────────────────────

LOW-RESOLUTION TIMERS (timer wheel):
  Used for: kernel timeouts, watchdogs, delayed work
  Resolution: CONFIG_HZ jiffies (100/250/1000 per second)
  
  Timer Wheel data structure:
  ┌─────────────────────────────────────────────────────────┐
  │  256 slots per wheel level × 4 levels                  │
  │  Level 0: 0-255 jiffies   (resolution: 1 jiffy)        │
  │  Level 1: 256-16384       (resolution: 256 jiffies)    │
  │  Level 2: 16K-1M          (resolution: 16K jiffies)    │
  │  Level 3: 1M-1G+          (resolution: 1M jiffies)     │
  │                                                         │
  │  Current time: jiffies = slot in level-0               │
  │  Each jiffy: rotate wheel, fire timers in current slot  │
  └─────────────────────────────────────────────────────────┘
  
  O(1) insert and fire! (hash into wheel by expiry)

HIGH-RESOLUTION TIMERS (hrtimers):
  Used for: nanosleep, itimer, precise scheduling
  Resolution: hardware clock (TSC/HPET) — nanosecond precision
  
  Data structure: RED-BLACK TREE ordered by expiry time
  Closest-expiry timer is leftmost node — O(log N) insert
  CPU programs APIC timer to fire at next hrtimer expiry
  
  clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL)
  → hrtimer_start() → RB tree insert → APIC programmed
  → TSC reaches target → APIC fires → hrtimer_interrupt()
  → wake up sleeping process
```

---

# PART XIV — CGROUPS & NAMESPACES

---

## Chapter 16: Linux Containers Foundation

### 16.1 Namespaces — Isolation

**Definition:** A namespace wraps a global system resource to make it appear as a private copy for processes within that namespace. This is the fundamental mechanism behind Docker containers.

```
LINUX NAMESPACE TYPES
──────────────────────────────────────────────────────────────────

Namespace     Isolates                    Created with
──────────────────────────────────────────────────────────────────
mnt           Mount points, filesystem    unshare(CLONE_NEWNS)
pid           Process IDs                 unshare(CLONE_NEWPID)
net           Network interfaces, routes  unshare(CLONE_NEWNET)
ipc           SysV IPC, POSIX MQ          unshare(CLONE_NEWIPC)
uts           Hostname, NIS domain name   unshare(CLONE_NEWUTS)
user          UIDs and GIDs               unshare(CLONE_NEWUSER)
cgroup        cgroup root                 unshare(CLONE_NEWCGROUP)
time          Boot and monotonic clocks   unshare(CLONE_NEWTIME)

DOCKER CONTAINER = Process in all 8 namespace types simultaneously!

PID NAMESPACE EXAMPLE:
  
  Host namespace:                Container namespace:
  init (PID 1)                   bash (sees itself as PID 1!)
    └── dockerd (PID 234)           └── sleep (PID 2)
          └── container-process        └── ps (PID 3)
                (real PID 890)
                (sees PID 1!)
  
  The container's PID 1 is actually PID 890 on the host.
  The container CANNOT see or signal host processes.

NETWORK NAMESPACE EXAMPLE:
  
  Host:                          Container:
  eth0: 192.168.1.100            eth0: 172.17.0.2 (veth pair)
  lo:   127.0.0.1                lo:   127.0.0.1
  routing table: full            routing table: container-only
  
  Container's eth0 is one end of a veth (virtual ethernet) pair.
  The other end is in the host's network namespace.
  Traffic flows: container→veth pair→bridge→NAT→internet
```

### 16.2 cgroups — Resource Control

**Definition:** Control groups (cgroups) limit, account for, and isolate the resource usage (CPU, memory, disk I/O, network) of a collection of processes.

```
CGROUP HIERARCHY
──────────────────────────────────────────────────────────────────

/sys/fs/cgroup/
├── memory/
│   ├── system.slice/
│   │   └── docker.service/
│   │       └── container-abc123/   ← Docker container
│   │           memory.limit_in_bytes = 512MB
│   │           memory.usage_in_bytes = 234MB
│   └── user.slice/
│       └── user-1000.slice/
│           memory.limit_in_bytes = 4GB
├── cpu/
│   └── container-abc123/
│       cpu.shares = 512            ← relative CPU weight
│       cpu.cfs_quota_us = 50000   ← max 50ms per 100ms period
│       cpu.cfs_period_us = 100000  ← 100ms period = 50% max CPU
└── blkio/
    └── container-abc123/
        blkio.throttle.read_bps_device = 100MB/s

CGROUP CONTROL:
  Move process to cgroup: echo $PID > /sys/fs/cgroup/memory/mygroup/cgroup.procs
  Set memory limit:       echo 512M > /sys/fs/cgroup/memory/mygroup/memory.limit_in_bytes
  
  OOM in cgroup: if container exceeds memory limit:
    → cgroup OOM killer fires
    → kills process WITHIN THE CGROUP (not system-wide!)
    → Container crashes but HOST is safe

CGROUP V2 (unified hierarchy):
  Modern unified design: single hierarchy for all controllers
  /sys/fs/cgroup/ (v2 root)
  Each cgroup has: cpu, memory, io controllers unified
  Much simpler delegation model
```

---

# PART XV — KERNEL DEBUGGING & TRACING

---

## Chapter 17: Debugging & Observability

### 17.1 Tracing Infrastructure

```
LINUX TRACING ECOSYSTEM
──────────────────────────────────────────────────────────────────

INSTRUMENTATION POINTS:
  Tracepoints:    Compile-time static probes
                  TRACE_EVENT() macros in kernel source
                  Low overhead when not active
                  Example: sched_switch, block_rq_insert
  
  Kprobes:        Dynamic probes at ANY kernel instruction
                  Insert breakpoint at runtime
                  No kernel recompilation needed
  
  Uprobes:        Same but for user space binaries
  
  Perf events:    Hardware performance counters
                  cache-misses, branch-mispredictions, IPC
  
  eBPF:           Runs verified programs at any probe point
                  The most powerful and modern approach

TRACING TOOLS:
  ftrace:   Built-in kernel tracer (/sys/kernel/debug/tracing)
            function_graph tracer: see kernel call graph
  perf:     Performance analysis (perf stat, perf record, perf top)
  strace:   Trace syscalls of a process (uses ptrace)
  ltrace:   Trace library calls
  bpftrace: High-level eBPF scripting language
  BCC:      Python + eBPF toolkit (execsnoop, opensnoop, etc.)

READING KERNEL SYMBOLS:
  /proc/kallsyms — all kernel symbols with addresses
  T = text (code), D = data, B = BSS
  Used by: crash dumpers, profilers, eBPF
```

### 17.2 /proc and /sys Virtual Filesystems

```
/PROC VIRTUAL FILESYSTEM
──────────────────────────────────────────────────────────────────

/proc is NOT on disk — it's generated on-the-fly by the kernel.
Each file is a window into kernel data structures.

/proc/cpuinfo          ← CPU topology, features, model name
/proc/meminfo          ← Memory subsystem counters
/proc/version          ← Kernel version string
/proc/cmdline          ← Kernel boot command line
/proc/loadavg          ← 1/5/15 minute load averages
/proc/interrupts        ← Per-CPU IRQ counters
/proc/net/dev           ← Network interface statistics
/proc/sys/              ← Tunable kernel parameters (sysctl)
  vm/swappiness         ← How aggressively to swap (0-200)
  vm/dirty_ratio        ← % memory that can be dirty before writeback
  net/ipv4/tcp_*        ← TCP tuning parameters
  kernel/pid_max        ← Maximum PID value

/proc/PID/             ← Per-process directory
  status               ← Human-readable process info
  maps                 ← Virtual memory areas
  smaps                ← Detailed per-VMA memory stats
  fd/                  ← Open file descriptors
  net/                 ← Process's network namespace
  cgroup               ← cgroup membership
  syscall              ← Current/last syscall
  wchan                ← Where blocked (kernel function name)
  numa_maps            ← NUMA memory allocation

/SYS VIRTUAL FILESYSTEM (sysfs):
  Exposes kernel object model (kobjects, ksets)
  Each kernel object has a directory in /sys
  Attributes are files (read/write → affect kernel)
  
  /sys/block/sda/queue/scheduler    ← I/O scheduler
  /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  /sys/class/net/eth0/speed         ← Network interface speed
  /sys/bus/usb/devices/             ← USB device tree
```

### 17.3 eBPF — Modern Kernel Observability

```
EBPF: THE SUPERPOWER OF LINUX OBSERVABILITY
──────────────────────────────────────────────────────────────────

eBPF = extended Berkeley Packet Filter

Originally: filter network packets in kernel
Today: run ANY verified program at ANY kernel/user probe point

EBPF PROGRAM LIFECYCLE:
  1. Write eBPF program in restricted C
  2. Compile with LLVM to eBPF bytecode
  3. Submit to kernel via bpf() syscall
  4. Kernel VERIFIER checks:
     - No loops (bounded iterations only, since kernel 5.3)
     - No invalid memory access
     - Always terminates
     - No privilege escalation
  5. JIT-compile bytecode to native machine code
  6. Attach to probe point (tracepoint, kprobe, network hook)
  7. Runs at probe point: collect data → maps → user space

EBPF MAPS: shared data structures between eBPF and user space
  Hash map:     key-value store (per-PID counters)
  Array:        fixed-size indexed (per-CPU stats)
  Ring buffer:  event stream (modern preferred)
  Per-CPU:      one entry per CPU (no lock needed!)
  Stack trace:  kernel/user stack traces

EXAMPLE: Count syscalls per process
  Attach to sys_enter tracepoint:
  bpftrace -e 'tracepoint:raw_syscalls:sys_enter 
               { @[comm] = count(); }'

USE CASES:
  Performance profiling: CPU flamegraphs without instrumentation
  Network observability: per-connection latency (Cilium)
  Security:              Falco — detect anomalous syscalls
  Tracing:               Function latency histograms
  Networking:            XDP — packet processing at driver level
  Load balancing:        Cilium replaces iptables with eBPF
```

### 17.4 Rust Implementation — Kernel Observability

```rust
// kernel_observability.rs
// Reading kernel subsystem state through /proc and /sys
// A comprehensive system health monitor

use std::fs;
use std::collections::HashMap;

/// CPU information from /proc/cpuinfo
#[derive(Debug)]
struct CpuInfo {
    model_name: String,
    cpu_count:  usize,
    cpu_mhz:    f64,
    cache_size: String,
    flags:      Vec<String>,
}

fn read_cpu_info() -> CpuInfo {
    let content = fs::read_to_string("/proc/cpuinfo").unwrap_or_default();
    let mut info = CpuInfo {
        model_name: String::new(),
        cpu_count:  0,
        cpu_mhz:    0.0,
        cache_size: String::new(),
        flags:      Vec::new(),
    };

    for line in content.lines() {
        if let Some(val) = line.strip_prefix("processor\t: ") {
            info.cpu_count += 1;
        } else if let Some(val) = line.strip_prefix("model name\t: ") {
            if info.model_name.is_empty() {
                info.model_name = val.to_string();
            }
        } else if let Some(val) = line.strip_prefix("cpu MHz\t\t: ") {
            if info.cpu_mhz == 0.0 {
                info.cpu_mhz = val.parse().unwrap_or(0.0);
            }
        } else if let Some(val) = line.strip_prefix("cache size\t: ") {
            if info.cache_size.is_empty() {
                info.cache_size = val.to_string();
            }
        } else if let Some(val) = line.strip_prefix("flags\t\t: ") {
            if info.flags.is_empty() {
                info.flags = val.split_whitespace()
                    .filter(|f| ["sse4_2", "avx2", "avx512f",
                                 "hypervisor", "nx", "pse", "aes"]
                            .contains(f))
                    .map(String::from)
                    .collect();
            }
        }
    }

    info
}

/// Memory statistics from /proc/meminfo
#[derive(Debug)]
struct MemInfo {
    total_kb:     u64,
    free_kb:      u64,
    available_kb: u64,
    buffers_kb:   u64,
    cached_kb:    u64,
    swap_total_kb: u64,
    swap_free_kb:  u64,
}

fn read_mem_info() -> MemInfo {
    let content = fs::read_to_string("/proc/meminfo").unwrap_or_default();
    let mut map = HashMap::new();

    for line in content.lines() {
        let parts: Vec<&str> = line.splitn(2, ':').collect();
        if parts.len() == 2 {
            let key = parts[0].trim();
            let val = parts[1].trim()
                .split_whitespace()
                .next()
                .and_then(|v| v.parse::<u64>().ok())
                .unwrap_or(0);
            map.insert(key.to_string(), val);
        }
    }

    MemInfo {
        total_kb:     *map.get("MemTotal").unwrap_or(&0),
        free_kb:      *map.get("MemFree").unwrap_or(&0),
        available_kb: *map.get("MemAvailable").unwrap_or(&0),
        buffers_kb:   *map.get("Buffers").unwrap_or(&0),
        cached_kb:    *map.get("Cached").unwrap_or(&0),
        swap_total_kb: *map.get("SwapTotal").unwrap_or(&0),
        swap_free_kb:  *map.get("SwapFree").unwrap_or(&0),
    }
}

/// Per-CPU statistics from /proc/stat
fn read_cpu_stats() -> Vec<HashMap<String, u64>> {
    let content = fs::read_to_string("/proc/stat").unwrap_or_default();
    let mut cpus = Vec::new();

    for line in content.lines() {
        if !line.starts_with("cpu") { break; }

        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 8 { continue; }

        let mut stats = HashMap::new();
        let names = ["user", "nice", "system", "idle",
                     "iowait", "irq", "softirq", "steal"];
        for (i, name) in names.iter().enumerate() {
            stats.insert(name.to_string(),
                         parts[i+1].parse().unwrap_or(0));
        }

        let total: u64 = stats.values().sum();
        let idle = stats["idle"] + stats.get("iowait").copied().unwrap_or(0);
        let used = total - idle;
        let usage_pct = if total > 0 {
            (used * 100) / total
        } else { 0 };

        stats.insert("total".to_string(), total);
        stats.insert("usage_pct".to_string(), usage_pct);
        cpus.push(stats);
    }

    cpus
}

/// IRQ statistics — which devices interrupt the CPU
fn read_interrupt_stats() {
    println!("\n=== IRQ Statistics (/proc/interrupts) ===");
    if let Ok(content) = fs::read_to_string("/proc/interrupts") {
        let lines: Vec<&str> = content.lines().collect();
        // Print header
        if let Some(header) = lines.first() {
            println!("  {}", header);
        }
        // Print first 10 IRQs
        for line in lines.iter().skip(1).take(10) {
            println!("  {}", line);
        }
        println!("  ... ({} total IRQ entries)", lines.len() - 1);
    }
}

/// Block device I/O statistics
fn read_io_stats() {
    println!("\n=== Block I/O Statistics (/proc/diskstats) ===");
    if let Ok(content) = fs::read_to_string("/proc/diskstats") {
        let mut count = 0;
        for line in content.lines() {
            // Only show real disk devices (not partitions or loop devices)
            if line.contains(" sd") || line.contains(" nvme") ||
               line.contains(" vd") || line.contains(" hd") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 14 && count < 5 {
                    println!("  dev={} reads={} writes={} io_ms={}",
                             parts[2], parts[3], parts[7], parts[12]);
                    count += 1;
                }
            }
        }
        if count == 0 {
            println!("  (no block devices found)");
        }
    }
}

/// Kernel scheduler statistics
fn read_scheduler_stats() {
    println!("\n=== Scheduler Statistics (/proc/schedstat) ===");
    if let Ok(content) = fs::read_to_string("/proc/schedstat") {
        for line in content.lines().take(4) {
            println!("  {}", line);
        }
    }
    println!("  Explanation: cpu_N <time_running> <time_waiting> <nr_switches>");
}

fn print_system_overview(cpu: &CpuInfo, mem: &MemInfo, cpu_stats: &[HashMap<String, u64>]) {
    println!("╔═══════════════════════════════════════════════════════╗");
    println!("║           LINUX KERNEL SUBSYSTEM STATUS               ║");
    println!("╚═══════════════════════════════════════════════════════╝");

    println!("\n=== CPU Subsystem ===");
    println!("  Model:      {}", cpu.model_name);
    println!("  Count:      {} logical CPUs", cpu.cpu_count);
    println!("  Speed:      {:.0} MHz", cpu.cpu_mhz);
    println!("  Cache:      {}", cpu.cache_size);
    println!("  Features:   {}", cpu.flags.join(", "));

    if !cpu_stats.is_empty() {
        println!("\n=== CPU Utilization (from boot totals) ===");
        for (i, stats) in cpu_stats.iter().enumerate() {
            if i == 0 {
                println!("  ALL CPUs: {}% utilized", stats.get("usage_pct").unwrap_or(&0));
            } else {
                println!("  CPU {:2}:   {}% utilized (user={}% sys={}%)",
                         i - 1,
                         stats.get("usage_pct").unwrap_or(&0),
                         stats.get("user").unwrap_or(&0),
                         stats.get("system").unwrap_or(&0));
            }
        }
    }

    println!("\n=== Memory Subsystem (mm_struct statistics) ===");
    let total_mb  = mem.total_kb / 1024;
    let avail_mb  = mem.available_kb / 1024;
    let used_mb   = total_mb - (mem.free_kb / 1024);
    let cached_mb = mem.cached_kb / 1024;
    let buf_mb    = mem.buffers_kb / 1024;

    println!("  Total:      {} MB", total_mb);
    println!("  Used:       {} MB ({:.0}%)", used_mb,
             (used_mb as f64 / total_mb as f64) * 100.0);
    println!("  Available:  {} MB (free + reclaimable)", avail_mb);
    println!("  Page Cache: {} MB (disk cache)", cached_mb);
    println!("  Buffers:    {} MB (block device cache)", buf_mb);
    if mem.swap_total_kb > 0 {
        let swap_used = (mem.swap_total_kb - mem.swap_free_kb) / 1024;
        println!("  Swap:       {} MB used / {} MB total",
                 swap_used, mem.swap_total_kb / 1024);
    }
}

fn main() {
    let cpu_info  = read_cpu_info();
    let mem_info  = read_mem_info();
    let cpu_stats = read_cpu_stats();

    print_system_overview(&cpu_info, &mem_info, &cpu_stats);
    read_interrupt_stats();
    read_io_stats();
    read_scheduler_stats();

    println!("\n=== Kernel Version ===");
    if let Ok(v) = fs::read_to_string("/proc/version") {
        println!("  {}", v.trim());
    }

    println!("\n=== Load Average ===");
    if let Ok(load) = fs::read_to_string("/proc/loadavg") {
        let parts: Vec<&str> = load.split_whitespace().collect();
        if parts.len() >= 3 {
            println!("  1min={} 5min={} 15min={}",
                     parts[0], parts[1], parts[2]);
            println!("  (> num_cpus = overloaded, < num_cpus = underloaded)");
        }
    }
}
```

---

# APPENDIX: Mental Models & Learning Strategy

---

## The DSA Connection — Linux Kernel Data Structures Summary

```
KERNEL SUBSYSTEM ↔ DATA STRUCTURE MAPPING
──────────────────────────────────────────────────────────────────

Subsystem           Data Structure          Why
────────────────────────────────────────────────────────────────────
CFS Scheduler       Red-Black Tree          O(log N) insert/delete
                                            O(1) min (leftmost)

Process tree        N-ary tree              Parent/child relationships
                    (linked list + ptrs)

All task list       Doubly linked list      O(1) insert/delete
                    (circular)              O(N) iteration

Page tables         Radix tree (4-level)    Sparse mapping,
                                            O(1) lookup by VA

VMA list            Red-Black Tree          O(log N) VMA lookup
                    + linked list           on page fault

Page cache          XArray (radix tree)     Sparse file pages,
                    keyed by page index     O(1) lookup

Physical memory     Buddy system            O(log N) alloc/free
                    (2^n free lists)        internal fragmentation

Kernel objects      SLAB/SLUB               O(1) fixed-size alloc
(task_struct etc)   (object pools)         

dcache              Hash table              O(1) dentry lookup
                    + LRU list              by (parent, name)

IRQ routing         Radix tree / hash       O(1) IRQ → handler

Network sockets     Hash table              O(1) (local_ip, local_port,
                                            remote_ip, remote_port)

Timer wheel         Hash table (buckets)    O(1) timer insert/fire

hrtimers            Red-Black Tree          O(log N) insert,
                                            O(1) find-next

Kernel modules      Linked list + hash      O(N) search (small N)

cgroups             Tree                    Hierarchical control
────────────────────────────────────────────────────────────────────
```

## Cognitive Principles for Mastery

```
DELIBERATE PRACTICE FRAMEWORK FOR KERNEL MASTERY
──────────────────────────────────────────────────────────────────

PHASE 1 — CONCEPTUAL (you are here):
  Goal:  Build accurate mental models of each subsystem
  Method: Read, visualize, ask "why does this design exist?"
  Test:  Can you explain it to someone else from scratch?

PHASE 2 — OBSERVATIONAL:
  Goal:  See the kernel working in real-time
  Tools: strace, perf, /proc, bpftrace, ftrace
  Task:  Trace a simple program's kernel journey
         strace cat /etc/hostname → watch every syscall

PHASE 3 — EXPERIMENTAL:
  Goal:  Write kernel code and see effects
  Tasks: Write a simple kernel module
         Implement a character device
         Write a /proc entry
         Add a tracepoint

PHASE 4 — EXPERT:
  Goal:  Contribute to kernel or write production drivers
  Path:  Study real subsystem code, read kernel patches,
         submit a bug fix or documentation improvement

KEY COGNITIVE INSIGHT (Chunking):
  A kernel expert doesn't think "64 sequential steps"
  They think in CHUNKS:
  "page fault → VMA check → page alloc → PTE update"
  
  Build your chunks through repetition until each becomes
  a single cognitive unit. Then combine chunks.

FLOW STATE TRIGGERS:
  - Set specific goals: "Today I understand page fault handling"
  - Match difficulty: hard enough to challenge, easy enough to win
  - Immediate feedback: write code, observe with strace/perf
  - Eliminate distraction: single-subsystem focus sessions
```

---

*End of Linux Kernel Subsystems Guide*
*Version 1.0 | C & Rust Implementations | ASCII Visualizations*