# Linux Signals — A Complete, In-Depth Guide
> From Fundamentals to Kernel Internals, with C and Rust Implementations

---

## Table of Contents

1. [What Is a Signal?](#1-what-is-a-signal)
2. [Historical Background](#2-historical-background)
3. [The Signal Lifecycle — Generation, Delivery, Handling](#3-the-signal-lifecycle)
4. [All Standard Linux Signals — Full Reference](#4-all-standard-linux-signals)
5. [Kernel Internals — How Signals Work Inside the Kernel](#5-kernel-internals)
6. [Signal Disposition — What a Process Can Do With a Signal](#6-signal-disposition)
7. [Installing Signal Handlers — `signal()` vs `sigaction()`](#7-installing-signal-handlers)
8. [Signal Masks and Blocking — `sigprocmask()`](#8-signal-masks-and-blocking)
9. [Signal Sets — `sigset_t` API](#9-signal-sets)
10. [Sending Signals — `kill()`, `raise()`, `tgkill()`, `sigqueue()`](#10-sending-signals)
11. [Waiting for Signals — `pause()`, `sigsuspend()`, `sigwaitinfo()`](#11-waiting-for-signals)
12. [Async-Signal-Safety — The Most Dangerous Trap](#12-async-signal-safety)
13. [Real-Time Signals — SIGRTMIN to SIGRTMAX](#13-real-time-signals)
14. [Signal Stacks — `sigaltstack()`](#14-signal-stacks)
15. [`signalfd` — Signals as File Descriptors](#15-signalfd)
16. [Signals in Multithreaded Programs](#16-signals-in-multithreaded-programs)
17. [Signals in Child/Parent Relationships — `fork()`, `exec()`](#17-signals-in-forkexec)
18. [Job Control Signals — SIGSTOP, SIGCONT, SIGTSTP](#18-job-control-signals)
19. [The Self-Pipe Trick — Classic Async-Safe Pattern](#19-the-self-pipe-trick)
20. [Common Real-World Patterns](#20-common-real-world-patterns)
21. [Rust and Signals — Safety, `signal-hook`, and `signalfd`](#21-rust-and-signals)
22. [Debugging Signals — `strace`, `/proc`, `gdb`](#22-debugging-signals)
23. [Security Considerations](#23-security-considerations)
24. [Mental Models and Expert Intuition](#24-mental-models-and-expert-intuition)
25. [Appendix — Quick Reference Tables](#25-appendix)

---

## 1. What Is a Signal?

### Concept

A **signal** is a limited form of **inter-process communication (IPC)** used in Unix/Linux. It is an asynchronous notification sent to a process (or thread) to inform it that a specific event has occurred.

Think of signals as **software interrupts**. Just like a hardware interrupt pauses the CPU to handle a device event, a signal interrupts a running process to handle a software event.

### Key Mental Model

```
Normal Program Execution:
  [instruction 1] → [instruction 2] → [instruction 3] → ...

When a signal arrives:
  [instruction 1] → [instruction 2] ← SIGNAL INTERRUPTS HERE
                                          ↓
                                    [signal handler runs]
                                          ↓
                                    [resume instruction 3]
```

### What signals are NOT

- They are **not** a general-purpose message passing system (use pipes/sockets for that).
- They carry **very little information** — just a signal number (and optionally a small payload for real-time signals).
- They are **asynchronous** — a process cannot predict when a signal will arrive.
- They are **not queued** (except real-time signals) — multiple pending standard signals of the same type collapse into one.

### Analogy

| Real World          | Signals                        |
|---------------------|--------------------------------|
| Phone ring          | SIGINT (Ctrl+C)                |
| Fire alarm          | SIGTERM (graceful shutdown)    |
| Power cut           | SIGKILL (immediate death)      |
| Alarm clock         | SIGALRM (timer expired)        |
| Child crying        | SIGCHLD (child process changed)|

---

## 2. Historical Background

### UNIX Origins

Signals were introduced in **Version 4 Unix (1973)**. The original API was simple but riddled with race conditions:

```c
/* Original (unreliable) signal API — DO NOT USE */
signal(SIGINT, handler);
```

The problem: after the handler ran, the signal disposition was reset to default. You had to **re-install** the handler inside the handler itself — a window existed where a second signal could kill you.

### POSIX Standardization

**POSIX.1 (1988)** introduced `sigaction()`, providing:
- Reliable signal handling (no reset after delivery)
- Signal masking during handler execution
- Extended signal information (`siginfo_t`)

### Linux-Specific Additions

Linux added:
- **Real-time signals** (POSIX.1b, 1993) — queued, carry data
- **`signalfd()`** (Linux 2.6.22, 2007) — synchronous signal handling via file descriptors
- **`pidfd_send_signal()`** (Linux 5.1, 2019) — race-free signal sending via process file descriptors

---

## 3. The Signal Lifecycle

Understanding the full lifecycle is essential for mastering signals.

### Three Stages

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  GENERATION │────▶│   PENDING   │────▶│   DELIVERY   │
│  (signal    │     │  (stored in │     │  (action is  │
│  is created)│     │   kernel)   │     │   taken)     │
└─────────────┘     └─────────────┘     └──────────────┘
```

### Stage 1: Signal Generation

A signal is **generated** (also called "sent" or "raised") when:

| Source             | Mechanism                                        | Example                         |
|--------------------|--------------------------------------------------|---------------------------------|
| Terminal input     | Kernel detects special key                       | Ctrl+C → SIGINT                 |
| Hardware exception | CPU fault trapped by kernel                      | Division by zero → SIGFPE       |
| Another process    | `kill()` syscall                                 | `kill(pid, SIGTERM)`            |
| Kernel             | Timer, resource limit exceeded                   | `alarm()` → SIGALRM             |
| Process itself     | `raise()`, `abort()`                             | `raise(SIGUSR1)`                |

### Stage 2: Signal Pending

Between generation and delivery, a signal is **pending**. The kernel stores this in:
- A **bitmask** called `pending` in `task_struct` (for standard signals)
- A **queue** for real-time signals

A signal may remain pending because:
1. It is **blocked** (in the signal mask)
2. The process is currently **not scheduled** to run
3. The process is in an **uninterruptible sleep** (D state) — signals cannot be delivered here

```
Signal Generated
      │
      ▼
Is signal blocked? ──YES──▶ Signal stays PENDING in bitmask
      │                       (until unblocked)
      NO
      │
      ▼
Is process running/interruptible?
      │
     YES
      │
      ▼
DELIVER signal (take action)
```

### Stage 3: Signal Delivery

Delivery happens when the kernel transitions a process from **kernel mode back to user mode** (e.g., returning from a syscall, or returning from interrupt handling).

At delivery, the kernel checks the pending signal set against the blocked set. For each deliverable signal, it takes the configured **action** (disposition).

```
Kernel returning to userspace
          │
          ▼
   Check pending signals
          │
   ┌──────┴──────┐
   │             │
 None          Some pending
   │             │
   ▼             ▼
 Resume      For each deliverable signal:
 process     ┌─────────────────────────────┐
             │ What is the disposition?    │
             │                             │
             │  DEFAULT ──▶ default action │
             │  IGNORE  ──▶ discard        │
             │  HANDLER ──▶ call function  │
             └─────────────────────────────┘
```

---

## 4. All Standard Linux Signals — Full Reference

### Concept: Signal Numbers

Every signal has a **number** (an integer) and a **symbolic name** (a macro like `SIGINT`). The mapping is defined in `<signal.h>`.

Signal numbers 1–31 are **standard signals** (not queued, not guaranteed to carry data).
Signal numbers 32–64 are **real-time signals** (queued, carry data, no fixed meaning).

### Complete Signal Table

| Signal    | Number | Default Action | Description                                        |
|-----------|--------|----------------|----------------------------------------------------|
| SIGHUP    | 1      | Terminate      | Hangup — terminal disconnected, or daemon reload   |
| SIGINT    | 2      | Terminate      | Interrupt from keyboard (Ctrl+C)                   |
| SIGQUIT   | 3      | Core dump      | Quit from keyboard (Ctrl+\) — generates core dump  |
| SIGILL    | 4      | Core dump      | Illegal CPU instruction                            |
| SIGTRAP   | 5      | Core dump      | Trace/breakpoint trap — used by debuggers          |
| SIGABRT   | 6      | Core dump      | Abort signal from `abort()`                        |
| SIGBUS    | 7      | Core dump      | Bus error — bad memory access alignment            |
| SIGFPE    | 8      | Core dump      | Floating-point / arithmetic exception              |
| SIGKILL   | 9      | Terminate      | **CANNOT be caught or ignored** — kill immediately |
| SIGUSR1   | 10     | Terminate      | User-defined signal 1                              |
| SIGSEGV   | 11     | Core dump      | Segmentation fault — invalid memory access         |
| SIGUSR2   | 12     | Terminate      | User-defined signal 2                              |
| SIGPIPE   | 13     | Terminate      | Write to pipe with no readers                      |
| SIGALRM   | 14     | Terminate      | Timer from `alarm()` expired                       |
| SIGTERM   | 15     | Terminate      | Termination request (graceful shutdown)            |
| SIGSTKFLT | 16     | Terminate      | Stack fault on coprocessor (obsolete)              |
| SIGCHLD   | 17     | Ignore         | Child process stopped, continued, or terminated    |
| SIGCONT   | 18     | Continue       | Continue if stopped                                |
| SIGSTOP   | 19     | Stop           | **CANNOT be caught or ignored** — stop process     |
| SIGTSTP   | 20     | Stop           | Stop typed at terminal (Ctrl+Z)                    |
| SIGTTIN   | 21     | Stop           | Background process attempting terminal read        |
| SIGTTOU   | 22     | Stop           | Background process attempting terminal write       |
| SIGURG    | 23     | Ignore         | Urgent data on socket (OOB data)                   |
| SIGXCPU   | 24     | Core dump      | CPU time limit exceeded (setrlimit)                |
| SIGXFSZ   | 25     | Core dump      | File size limit exceeded                           |
| SIGVTALRM | 26     | Terminate      | Virtual alarm (only counts process CPU time)       |
| SIGPROF   | 27     | Terminate      | Profiling timer expired                            |
| SIGWINCH  | 28     | Ignore         | Terminal window resize                             |
| SIGIO     | 29     | Terminate      | I/O now possible (async I/O)                       |
| SIGPWR    | 30     | Terminate      | Power failure/restart (UPS)                        |
| SIGSYS    | 31     | Core dump      | Bad system call argument                           |

### Default Actions Explained

| Action    | Meaning                                              |
|-----------|------------------------------------------------------|
| Terminate | Process is killed, no core dump                      |
| Core dump | Process is killed, core file written to disk         |
| Stop      | Process execution is suspended                       |
| Continue  | If stopped, resume execution; otherwise, ignore      |
| Ignore    | Signal is silently discarded                         |

### Special Signals — SIGKILL and SIGSTOP

**SIGKILL (9)** and **SIGSTOP (19)** are special — they **cannot be caught, blocked, or ignored**. This is a kernel guarantee. If a process has hung and won't respond to SIGTERM, SIGKILL is the last resort. The kernel directly terminates the process without giving it any chance to run cleanup code.

```
Signal disposition options:
                          ┌─── Catch (custom handler)
                          │
All signals except ───────┼─── Ignore
SIGKILL and SIGSTOP       │
                          └─── Default action

SIGKILL ──────────────────── Default ONLY (immediate kill)
SIGSTOP ──────────────────── Default ONLY (immediate stop)
```

---

## 5. Kernel Internals

### `task_struct` — The Process Descriptor

Every process in Linux is represented by a `task_struct` in the kernel (defined in `include/linux/sched.h`). Signal-related fields:

```c
struct task_struct {
    /* ... many other fields ... */

    /* Signal handlers — shared among threads in a thread group */
    struct signal_struct     *signal;
    struct sighand_struct    *sighand;

    /* Per-thread signal mask (blocked signals) */
    sigset_t                  blocked;

    /* Per-thread real-time signal mask */
    sigset_t                  real_blocked;

    /* Pending signals for THIS thread only */
    struct sigpending         pending;

    /* ... */
};
```

### `signal_struct` — Thread Group Shared State

```c
struct signal_struct {
    /* Pending signals for the ENTIRE thread group */
    struct sigpending    shared_pending;

    /* ... process group, session, job control fields ... */
};
```

### `sigpending` — The Pending Signal Storage

```c
struct sigpending {
    struct list_head  list;    /* Queue for real-time signals */
    sigset_t          signal;  /* Bitmask for standard signals */
};
```

**Key insight**: For standard signals (1–31), the pending set is a **bitmask**. Bit N is set if signal N is pending. If signal N is sent twice while pending, the second one is **silently dropped** — only one instance is ever delivered. This is why standard signals are called "unreliable."

For real-time signals (32–64), a **linked list** is used. Multiple instances are queued and delivered in order.

### `sighand_struct` — Signal Handlers Table

```c
struct sighand_struct {
    spinlock_t          siglock;
    refcount_t          count;
    wait_queue_head_t   signalfd_wqh;
    struct k_sigaction  action[_NSIG]; /* One entry per signal */
};
```

```c
struct k_sigaction {
    struct sigaction sa;
};

struct sigaction {
    __sighandler_t  sa_handler;   /* Handler function pointer */
    unsigned long   sa_flags;     /* Flags (SA_RESTART, etc.) */
    sigset_t        sa_mask;      /* Signals to block during handler */
    /* ... */
};
```

### How the Kernel Delivers a Signal

The kernel function `do_signal()` (arch-specific, e.g., `arch/x86/kernel/signal.c`) is called when returning to user space:

```
Returning to user space (e.g., after syscall)
           │
           ▼
     do_signal()
           │
           ▼
    get_signal() ──── Dequeues the next deliverable signal
           │           from pending sets (checks thread-private
           │           then shared_pending), respects blocked mask
           │
           ▼
   handle_signal()
           │
     ┌─────┴──────────────────────────────┐
     │                                    │
     ▼                                    ▼
 SIG_DFL / SIG_IGN              Custom handler installed
     │                                    │
     ▼                                    ▼
 do_group_exit() /          setup_rt_frame()
 send_signal(), etc.              │
                                  ▼
                         Kernel builds a "signal frame"
                         on user-space STACK:
                         ┌────────────────────┐
                         │ Saved user registers│
                         │ (rip, rsp, rflags,  │
                         │  general registers) │
                         │ siginfo_t           │
                         │ ucontext_t          │
                         │ Return address →    │
                         │  sigreturn trampoline│
                         └────────────────────┘
                                  │
                                  ▼
                         CPU jumps to handler function
```

### The Signal Frame and `sigreturn`

When the kernel sets up a signal frame, it:
1. Saves the entire CPU state (registers) onto the user-space stack
2. Sets up the stack pointer to point to the signal frame
3. Sets the instruction pointer to the signal handler function
4. When the handler returns, execution goes to a small piece of code called the **sigreturn trampoline** (either in the vDSO or on the stack itself)
5. The trampoline calls `rt_sigreturn()` syscall
6. The kernel restores the saved CPU state and resumes normal execution

```
User stack before signal:
  ┌──────────────┐  ← rsp (stack pointer)
  │  normal data │
  └──────────────┘

User stack after kernel sets up signal frame:
  ┌──────────────────────────┐  ← new rsp
  │  rt_sigframe             │
  │  ┌─────────────────────┐ │
  │  │ saved registers     │ │
  │  │ siginfo_t           │ │
  │  │ ucontext_t          │ │
  │  │ sigreturn trampoline│ │
  │  └─────────────────────┘ │
  └──────────────────────────┘
  │  normal data             │
  └──────────────────────────┘

Signal handler executes using this new stack frame.
When it returns → trampoline → rt_sigreturn() → restore registers.
```

### Syscall Restart (SA_RESTART)

When a signal interrupts a **blocking syscall** (like `read()`, `select()`), what happens?

- **Without SA_RESTART**: The syscall returns `-1` with `errno = EINTR`. The programmer must check for this and retry.
- **With SA_RESTART**: The kernel automatically restarts the syscall after the signal handler returns.

Not all syscalls can be restarted. Some (like `nanosleep()`, `select()`) use a special restart mechanism (`ERESTART_RESTARTBLOCK`).

```c
/* Check this pattern in all I/O code! */
ssize_t bytes;
do {
    bytes = read(fd, buf, sizeof(buf));
} while (bytes == -1 && errno == EINTR);
```

---

## 6. Signal Disposition

### Concept: Disposition

The **disposition** of a signal defines what happens when it is delivered. Each signal has an independent disposition.

```
For each signal number (1..NSIG):
  ┌─────────────────────────────────────────┐
  │ Disposition options:                    │
  │                                         │
  │  SIG_DFL ──▶ Default kernel action      │
  │              (terminate/core/stop/etc.) │
  │                                         │
  │  SIG_IGN ──▶ Ignore the signal          │
  │              (kernel discards it)       │
  │                                         │
  │  &handler ─▶ Call this user function    │
  │              (the "signal handler")     │
  └─────────────────────────────────────────┘
```

### Disposition Inheritance

| Event         | Disposition behavior                                           |
|---------------|----------------------------------------------------------------|
| `fork()`      | Child **inherits** parent's dispositions                       |
| `exec()`      | Custom handlers **reset to SIG_DFL**; SIG_IGN is **preserved** |
| `pthread_create()` | New thread **inherits** the creating thread's signal mask |

The `exec()` reset makes sense: after exec, the old handler code no longer exists in memory.

---

## 7. Installing Signal Handlers

### The Old Way: `signal()`

```c
#include <signal.h>

typedef void (*sighandler_t)(int);
sighandler_t signal(int signum, sighandler_t handler);
```

**Problems with `signal()`:**
1. Behavior is **implementation-defined** (some reset the disposition to default after delivery)
2. Does not block other signals during handler execution
3. Cannot retrieve current disposition without changing it
4. Cannot pass additional context to the handler

**Never use `signal()` for new code.** It exists for historical compatibility only.

### The Right Way: `sigaction()`

```c
#include <signal.h>

int sigaction(int signum,
              const struct sigaction *act,
              struct sigaction *oldact);
```

```c
struct sigaction {
    void     (*sa_handler)(int);            /* Simple handler */
    void     (*sa_sigaction)(int,           /* Extended handler */
                              siginfo_t *,
                              void *);
    sigset_t   sa_mask;    /* Signals to block while handler runs */
    int        sa_flags;   /* Behavior flags */
    void     (*sa_restorer)(void); /* Internal use — do not set */
};
```

### `sa_flags` — Behavior Modifiers

| Flag            | Meaning                                                      |
|-----------------|--------------------------------------------------------------|
| `SA_RESTART`    | Automatically restart interrupted syscalls                   |
| `SA_SIGINFO`    | Use `sa_sigaction` (extended handler) instead of `sa_handler`|
| `SA_NOCLDSTOP`  | Don't send SIGCHLD when child is stopped (only on exit)      |
| `SA_NOCLDWAIT`  | Don't create zombie processes for children                   |
| `SA_NODEFER`    | Don't block the signal during its own handler                |
| `SA_RESETHAND`  | Reset disposition to SIG_DFL after first delivery (one-shot) |
| `SA_ONSTACK`    | Use alternate signal stack (see sigaltstack)                 |

### `siginfo_t` — Extended Signal Information

When `SA_SIGINFO` is set, the handler receives a `siginfo_t` struct:

```c
siginfo_t {
    int      si_signo;   /* Signal number */
    int      si_errno;   /* errno value (usually 0) */
    int      si_code;    /* Signal code — WHY was signal sent? */
    pid_t    si_pid;     /* Sending process PID */
    uid_t    si_uid;     /* Real UID of sending process */
    void    *si_addr;    /* Address that caused fault (SIGSEGV, SIGBUS) */
    int      si_status;  /* Exit status or signal (SIGCHLD) */
    long     si_band;    /* Band event for SIGIO */
    union sigval si_value; /* Signal value (real-time signals) */
};
```

`si_code` tells you **why** the signal was sent:

| si_code    | Meaning                                               |
|------------|-------------------------------------------------------|
| SI_USER    | Sent by `kill()` from user space                      |
| SI_KERNEL  | Sent by the kernel                                    |
| SI_QUEUE   | Sent by `sigqueue()`                                  |
| SI_TIMER   | POSIX timer expired                                   |
| CLD_EXITED | Child exited normally (for SIGCHLD)                   |
| CLD_KILLED | Child killed by signal (for SIGCHLD)                  |
| SEGV_MAPERR| Address not mapped to object (for SIGSEGV)            |
| SEGV_ACCERR| Invalid permissions for mapped object (for SIGSEGV)   |
| BUS_ADRALN | Invalid address alignment (for SIGBUS)                |

### C Implementation: Comprehensive `sigaction` Example

```c
/*
 * sigaction_demo.c
 * Demonstrates proper signal handling with sigaction, siginfo_t,
 * signal masking, and SA_RESTART.
 *
 * Compile: gcc -Wall -Wextra -o sigaction_demo sigaction_demo.c
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>

/* Volatile sig_atomic_t is the ONLY type safe to read/write
 * from a signal handler AND from normal code without a race. */
volatile sig_atomic_t g_shutdown_requested = 0;
volatile sig_atomic_t g_reload_requested   = 0;
volatile sig_atomic_t g_usr1_count         = 0;

/*
 * RULE: Signal handlers must ONLY use async-signal-safe functions.
 * Setting a flag and returning is the safest pattern.
 * The main loop polls the flag.
 */
static void sigterm_handler(int signo)
{
    (void)signo; /* suppress unused parameter warning */
    g_shutdown_requested = 1;
}

static void sighup_handler(int signo)
{
    (void)signo;
    g_reload_requested = 1;
}

/*
 * Extended handler using SA_SIGINFO.
 * Receives siginfo_t with details about signal origin.
 */
static void sigusr1_handler(int signo, siginfo_t *info, void *ucontext)
{
    (void)signo;
    (void)ucontext; /* machine context — used for stack unwinding */

    g_usr1_count++;

    /*
     * write() is async-signal-safe. printf() is NOT.
     * We can use write() here because it's in the safe list.
     *
     * But even this is risky in production — prefer setting a flag.
     */
    const char msg[] = "SIGUSR1 received\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);

    /*
     * info->si_pid = PID of the process that sent the signal
     * This is reliable only when si_code == SI_USER or SI_QUEUE
     */
    if (info->si_code == SI_USER) {
        /* Sender was a user-space process via kill() */
        char buf[64];
        int n = snprintf(buf, sizeof(buf),
                         "  Sent by PID: %d, UID: %d\n",
                         (int)info->si_pid, (int)info->si_uid);
        write(STDERR_FILENO, buf, (size_t)n);
    }
}

/*
 * Helper: install a signal handler with proper defaults.
 * - SA_RESTART: restart interrupted syscalls automatically
 * - Blocks the same signal during handler (default behavior)
 */
static int install_handler(int signo,
                            void (*handler)(int, siginfo_t *, void *),
                            int flags)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));

    sa.sa_sigaction = handler;
    sa.sa_flags     = SA_SIGINFO | SA_RESTART | flags;

    /* Block no additional signals during the handler.
     * The signal itself is automatically blocked (unless SA_NODEFER). */
    sigemptyset(&sa.sa_mask);

    if (sigaction(signo, &sa, NULL) == -1) {
        perror("sigaction");
        return -1;
    }
    return 0;
}

/*
 * Simplified helper for handlers that don't need siginfo.
 */
static int install_simple_handler(int signo, void (*handler)(int))
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handler;
    sa.sa_flags   = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    return sigaction(signo, &sa, NULL);
}

int main(void)
{
    printf("PID: %d\n", getpid());
    printf("Send SIGUSR1 to trigger handler, SIGHUP to reload, "
           "SIGTERM/SIGINT to quit.\n");

    /* Install handlers */
    if (install_simple_handler(SIGTERM, sigterm_handler) != 0)
        return 1;
    if (install_simple_handler(SIGINT,  sigterm_handler) != 0)
        return 1;
    if (install_simple_handler(SIGHUP,  sighup_handler)  != 0)
        return 1;
    if (install_handler(SIGUSR1, sigusr1_handler, 0)     != 0)
        return 1;

    /* Main event loop */
    while (!g_shutdown_requested) {
        /*
         * poll flags, do work, then sleep.
         * sleep() is interruptible by signals — that's fine here.
         */
        if (g_reload_requested) {
            g_reload_requested = 0;
            printf("[main] Reloading configuration...\n");
            fflush(stdout);
        }

        if (g_usr1_count > 0) {
            printf("[main] Processed %d SIGUSR1 signals so far.\n",
                   (int)g_usr1_count);
            fflush(stdout);
        }

        sleep(1);
    }

    printf("[main] Shutdown requested. Cleaning up...\n");
    printf("[main] Total SIGUSR1 count: %d\n", (int)g_usr1_count);
    return 0;
}
```

---

## 8. Signal Masks and Blocking

### Concept: Signal Mask

Every thread has a **signal mask** — a bitmask of signals that are currently **blocked**. A blocked signal is not ignored; it is held as **pending** and delivered only when it is unblocked.

```
Signal arrives
      │
      ▼
Is signal in thread's blocked mask?
      │
   YES│                    NO│
      ▼                      ▼
 Mark as PENDING        Deliver immediately
 (stored in sigpending) (or at next kernel→user transition)
      │
      ▼
 Signal stays pending until unblocked
      │
      ▼ (sigprocmask removes from mask)
 Signal delivered
```

### `sigprocmask()`

```c
#include <signal.h>

int sigprocmask(int how, const sigset_t *set, sigset_t *oldset);
```

`how` controls how the mask is modified:

| `how`       | Effect                                                   |
|-------------|----------------------------------------------------------|
| `SIG_BLOCK` | Add `set` to current mask (block more signals)           |
| `SIG_UNBLOCK` | Remove `set` from current mask (unblock signals)       |
| `SIG_SETMASK` | Replace current mask with `set`                        |

`oldset`: if non-NULL, receives the **previous** mask (allows restoring later).

### Pattern: Critical Section

Block signals around code that must not be interrupted by a signal handler:

```c
/*
 * critical_section.c
 * Pattern: block signals during a critical section,
 * then restore the original mask.
 */

#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>

void critical_section_example(void)
{
    sigset_t block_mask, old_mask;

    /* Build a set containing SIGUSR1 and SIGUSR2 */
    sigemptyset(&block_mask);
    sigaddset(&block_mask, SIGUSR1);
    sigaddset(&block_mask, SIGUSR2);

    /* Block them, save old mask */
    sigprocmask(SIG_BLOCK, &block_mask, &old_mask);

    /* --- CRITICAL SECTION BEGIN --- */
    /*
     * While inside here, SIGUSR1 and SIGUSR2 cannot interrupt us.
     * They will be held as pending.
     */
    printf("Inside critical section\n");
    /* update shared data structures, etc. */
    /* --- CRITICAL SECTION END --- */

    /* Restore original mask — pending signals may now be delivered */
    sigprocmask(SIG_SETMASK, &old_mask, NULL);

    /*
     * NOTE: After SIG_SETMASK, if SIGUSR1 was pending,
     * it gets delivered HERE, before the next statement.
     */
}
```

### Thread Signal Masks: `pthread_sigmask()`

In multithreaded programs, use `pthread_sigmask()` instead of `sigprocmask()`. The API is identical but operates on the calling thread's mask:

```c
#include <pthread.h>
#include <signal.h>

int pthread_sigmask(int how, const sigset_t *set, sigset_t *oldset);
```

---

## 9. Signal Sets

### Concept: `sigset_t`

A `sigset_t` is an opaque data type representing a **set of signals** (conceptually a bitmask). Never manipulate it directly — always use the API:

```c
int sigemptyset(sigset_t *set);          /* Initialize empty set */
int sigfillset(sigset_t *set);           /* Initialize full set (all signals) */
int sigaddset(sigset_t *set, int signo); /* Add signal to set */
int sigdelset(sigset_t *set, int signo); /* Remove signal from set */
int sigismember(const sigset_t *set,     /* Test if signal in set */
                int signo);
```

### Inspecting Current Pending Signals

```c
/*
 * pending_check.c
 * Check what signals are currently pending for this process.
 */

#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>

void show_pending_signals(void)
{
    sigset_t pending;
    sigpending(&pending);  /* fills 'pending' with currently pending signals */

    printf("Pending signals: ");
    for (int sig = 1; sig < NSIG; sig++) {
        if (sigismember(&pending, sig)) {
            printf("%d(%s) ", sig, strsignal(sig));
        }
    }
    printf("\n");
}
```

---

## 10. Sending Signals

### `kill()` — Send to Any Process

```c
#include <signal.h>

int kill(pid_t pid, int sig);
```

| `pid` value  | Target                                               |
|--------------|------------------------------------------------------|
| `> 0`        | The specific process with that PID                   |
| `0`          | Every process in the caller's process group          |
| `-1`         | Every process the caller has permission to signal    |
| `< -1`       | Every process in process group `abs(pid)`            |

```c
kill(1234, SIGTERM);   /* Send SIGTERM to PID 1234 */
kill(0, SIGUSR1);      /* Broadcast SIGUSR1 to process group */
kill(getpid(), SIGINT); /* Send to yourself */
```

### `raise()` — Send to Yourself

```c
raise(SIGALRM);  /* equivalent to kill(getpid(), SIGALRM) */
```

### `sigqueue()` — Send with Data (Real-Time Signals)

```c
#include <signal.h>

int sigqueue(pid_t pid, int sig, const union sigval value);

union sigval {
    int   sival_int;   /* Integer value */
    void *sival_ptr;   /* Pointer value (CAUTION: different address spaces!) */
};
```

```c
union sigval val;
val.sival_int = 42;
sigqueue(target_pid, SIGRTMIN, val);

/* Receiver gets val via siginfo_t.si_value */
```

### `tgkill()` — Send to Specific Thread

In a multithreaded process, signal a specific thread:

```c
#include <sys/syscall.h>

int tgkill(int tgid, int tid, int sig);
/* tgid = thread group ID (= main process PID) */
/* tid  = target thread's TID (from gettid()) */
```

```c
syscall(SYS_tgkill, getpid(), gettid(), SIGUSR1);
```

### `pidfd_send_signal()` — Race-Free Signal Sending (Linux 5.1+)

Traditional `kill()` has a TOCTOU (time-of-check-to-time-of-use) race: the PID might be recycled between when you look it up and when you signal it. `pidfd` solves this:

```c
#include <sys/syscall.h>
#include <linux/pidfd.h>

int pidfd = syscall(SYS_pidfd_open, target_pid, 0);
if (pidfd == -1) { perror("pidfd_open"); return; }

syscall(SYS_pidfd_send_signal, pidfd, SIGTERM, NULL, 0);
close(pidfd);
```

A `pidfd` holds a reference to the process struct. Even if the original PID is recycled, the signal goes to the right process (or fails if it exited).

---

## 11. Waiting for Signals

### `pause()` — Wait for Any Signal

```c
#include <unistd.h>

int pause(void); /* Always returns -1 with errno = EINTR */
```

`pause()` suspends the calling process until **any** signal is delivered. After the handler returns, `pause()` returns.

**WARNING**: `pause()` has a classic race condition:

```c
/* BUGGY CODE — DO NOT USE THIS PATTERN */
volatile sig_atomic_t signal_received = 0;

void handler(int sig) { signal_received = 1; }

/* What if the signal arrives HERE, between the check and pause()? */
if (!signal_received) {
    pause(); /* We'd sleep forever if signal already came */
}
```

### `sigsuspend()` — Atomic Mask Replace + Wait

`sigsuspend()` atomically replaces the signal mask AND waits, eliminating the race:

```c
#include <signal.h>

int sigsuspend(const sigset_t *mask);
```

It:
1. **Atomically** replaces the signal mask with `*mask`
2. Suspends until a signal is delivered
3. **Atomically** restores the original mask before returning

```c
/* CORRECT PATTERN */
sigset_t wait_mask, block_mask, old_mask;

sigemptyset(&block_mask);
sigaddset(&block_mask, SIGUSR1);

/* Block SIGUSR1 while checking the flag (prevents race) */
sigprocmask(SIG_BLOCK, &block_mask, &old_mask);

while (!signal_received) {
    /*
     * sigsuspend atomically: unblocks SIGUSR1, waits, re-blocks.
     * If signal arrives between the while check and sigsuspend,
     * it's still pending and will be delivered immediately.
     */
    sigsuspend(&old_mask); /* waits with SIGUSR1 unblocked */
}

sigprocmask(SIG_SETMASK, &old_mask, NULL);
```

### `sigwaitinfo()` / `sigtimedwait()` — Synchronous Signal Reception

```c
#include <signal.h>

int sigwaitinfo(const sigset_t *set, siginfo_t *info);
int sigtimedwait(const sigset_t *set, siginfo_t *info,
                 const struct timespec *timeout);
```

These functions **synchronously** wait for a signal in `set`. The signal must be blocked first (otherwise it would be handled asynchronously):

```c
sigset_t wait_set;
siginfo_t info;

sigemptyset(&wait_set);
sigaddset(&wait_set, SIGUSR1);
sigaddset(&wait_set, SIGUSR2);

/* Block these signals so they aren't delivered asynchronously */
sigprocmask(SIG_BLOCK, &wait_set, NULL);

/* Wait synchronously — no handler needed */
int sig = sigwaitinfo(&wait_set, &info);
if (sig == SIGUSR1) {
    printf("Got SIGUSR1 from PID %d\n", (int)info.si_pid);
}
```

---

## 12. Async-Signal-Safety

### The Most Dangerous Trap in Signal Programming

When a signal handler is invoked, it may interrupt code that is in an **inconsistent state**. For example, if your signal handler calls `malloc()`, and `malloc()` was interrupted mid-execution (with its internal linked list partially modified), you get **heap corruption**.

Functions that are safe to call from signal handlers are called **async-signal-safe**. POSIX maintains a specific list.

### How Unsafe Functions Cause Bugs

```
Thread executing printf():
  1. printf() calls malloc() internally
  2. malloc() acquires its internal lock
  3. malloc() begins modifying free list

   ← SIGNAL INTERRUPTS HERE →

  Signal handler calls printf() again
  → printf() calls malloc() again
  → malloc() tries to acquire the SAME lock
  → DEADLOCK (or worse: heap corruption if lock is not recursive)
```

### Async-Signal-Safe Functions (POSIX list, selected)

```
SAFE to call from signal handlers:
  _Exit()         abort()         accept()
  access()        alarm()         bind()
  clock_gettime() close()         connect()
  dup()           dup2()          execve()
  _exit()         fchmod()        fchown()
  fcntl()         fork()          fstat()
  fsync()         ftruncate()     getegid()
  geteuid()       getgid()        getgroups()
  getpid()        getppid()       getuid()
  kill()          lseek()         lstat()
  mkdir()         open()          pipe()
  poll()          posix_trace_event()
  pselect()       raise()         read()
  readlink()      recv()          recvfrom()
  recvmsg()       rename()        rmdir()
  select()        sem_post()      send()
  sendmsg()       sendto()        setgid()
  setuid()        shutdown()      sigaction()
  sigaddset()     sigdelset()     sigemptyset()
  sigfillset()    sigismember()   signal()
  sigpause()      sigpending()    sigprocmask()
  sigqueue()      sigset()        sigsuspend()
  sleep()         socket()        stat()
  strsignal()     symlink()       sysconf()
  tcdrain()       tcflow()        tcflush()
  tcgetattr()     tcgetpgrp()     tcsendbreak()
  tcsetattr()     tcsetpgrp()     time()
  timer_getoverrun() timer_gettime() timer_settime()
  times()         umask()         uname()
  unlink()        utime()         wait()
  waitpid()       write()

NOT SAFE (incomplete list):
  printf()    fprintf()   sprintf()   snprintf()
  malloc()    free()      calloc()    realloc()
  exit()      atexit()    fopen()     fclose()
  fread()     fwrite()    fflush()    fputs()
  syslog()    openlog()   closelog()
  pthread_mutex_lock()  (any non-recursive mutex)
  strtok()    getenv()    setenv()
  abort()     (safe per POSIX, but has caveats in practice)
```

### The Golden Rule

> **In signal handlers: set a flag. Do the real work in the main loop.**

```c
/* CORRECT PATTERN */
volatile sig_atomic_t flag_usr1 = 0;

void handler(int sig) {
    (void)sig;
    flag_usr1 = 1;  /* Only this. Nothing else. */
}

int main(void) {
    /* ... install handler ... */
    while (1) {
        if (flag_usr1) {
            flag_usr1 = 0;
            do_real_work(); /* Safe to call anything here */
        }
        pause(); /* or sleep, or actual work */
    }
}
```

### Why `volatile sig_atomic_t`?

- `volatile`: tells the compiler not to cache the variable in a register. Forces every access to go through memory, so changes made by the signal handler are visible to the main loop.
- `sig_atomic_t`: guaranteed by POSIX to be read/written atomically with respect to signals. On most architectures, this is just `int`.

---

## 13. Real-Time Signals

### What Makes Them "Real-Time"?

Standard signals (1–31):
- **Not queued**: multiple pending signals of same type collapse to one
- **No ordering guarantee** between different signals
- **No payload**: can't carry data

Real-time signals (SIGRTMIN to SIGRTMAX, at least 32 values):
- **Queued**: multiple instances are all delivered
- **Ordered**: lower-numbered real-time signals have higher priority
- **Payload**: can carry an integer or pointer via `sigqueue()`

```
SIGRTMIN = 34 (on Linux x86-64, check with kill -l)
SIGRTMAX = 64

Note: Do NOT hardcode numbers. Always use SIGRTMIN+N.

Example:
  SIGRTMIN+0 ─── Highest priority real-time signal
  SIGRTMIN+1
  SIGRTMIN+2
  ...
  SIGRTMAX   ─── Lowest priority real-time signal
```

### Real-Time Signal Example in C

```c
/*
 * rt_signals.c
 * Demonstrates real-time signal queuing with payload.
 *
 * Compile: gcc -Wall -o rt_signals rt_signals.c
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>

#define MY_RTSIG (SIGRTMIN + 5)

static volatile sig_atomic_t received_count = 0;
static int received_values[64]; /* Store payloads */

static void rt_handler(int sig, siginfo_t *info, void *ctx)
{
    (void)sig;
    (void)ctx;
    int idx = received_count++;
    if (idx < 64) {
        received_values[idx] = info->si_value.sival_int;
    }
}

int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = rt_handler;
    sa.sa_flags = SA_SIGINFO | SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaction(MY_RTSIG, &sa, NULL);

    /* Block the RT signal, send multiple instances, then unblock */
    sigset_t block, old;
    sigemptyset(&block);
    sigaddset(&block, MY_RTSIG);
    sigprocmask(SIG_BLOCK, &block, &old);

    /* Send 5 signals with different payloads to ourselves */
    for (int i = 0; i < 5; i++) {
        union sigval val;
        val.sival_int = i * 100;
        sigqueue(getpid(), MY_RTSIG, val);
        printf("Queued signal with value %d\n", val.sival_int);
    }

    printf("Unblocking — all 5 should be delivered in order...\n");
    sigprocmask(SIG_SETMASK, &old, NULL);

    /* Small sleep to let signals be delivered */
    struct timespec ts = { .tv_sec = 0, .tv_nsec = 1000000 };
    nanosleep(&ts, NULL);

    printf("Received %d signals:\n", (int)received_count);
    for (int i = 0; i < received_count && i < 64; i++) {
        printf("  [%d] value = %d\n", i, received_values[i]);
    }

    /* With standard signals, you'd only get 1 despite sending 5.
     * With RT signals, you get all 5, in order, with their values. */
    return 0;
}
```

---

## 14. Signal Stacks

### The Problem: Stack Overflow Detection

When a process overflows its stack (e.g., infinite recursion), the kernel sends `SIGSEGV`. But to run the handler, the kernel needs to push a signal frame onto... the stack. If the stack is full, there's no room — the handler can't run!

**Solution**: Use an **alternate signal stack** — a separate region of memory used only for signal handler execution.

### `sigaltstack()`

```c
#include <signal.h>

int sigaltstack(const stack_t *ss, stack_t *old_ss);

typedef struct {
    void  *ss_sp;    /* Base address of stack */
    int    ss_flags; /* Flags (SS_ONSTACK, SS_DISABLE) */
    size_t ss_size;  /* Size of stack */
} stack_t;
```

### C Implementation: Alternate Stack for Stack Overflow

```c
/*
 * sigaltstack_demo.c
 * Set up an alternate signal stack to catch SIGSEGV
 * caused by stack overflow.
 *
 * Compile: gcc -Wall -o sigaltstack_demo sigaltstack_demo.c
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

#define ALT_STACK_SIZE  (64 * 1024) /* 64 KB */

static void sigsegv_handler(int sig, siginfo_t *info, void *ctx)
{
    (void)ctx;
    /* This runs on the alternate stack, not the overflowed one */
    const char msg[] = "SIGSEGV caught on alternate stack!\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
    write(STDERR_FILENO, "Likely stack overflow. Exiting.\n", 32);
    _exit(1); /* _exit is async-signal-safe; exit() is NOT */
}

/* Infinite recursion to trigger stack overflow */
static void overflow(int depth)
{
    char buf[1024]; /* Consume stack space */
    (void)buf;
    overflow(depth + 1);
}

int main(void)
{
    /* 1. Allocate alternate stack */
    void *alt_stack = malloc(ALT_STACK_SIZE);
    if (!alt_stack) {
        perror("malloc");
        return 1;
    }

    /* 2. Register it with the kernel */
    stack_t ss = {
        .ss_sp    = alt_stack,
        .ss_flags = 0,
        .ss_size  = ALT_STACK_SIZE,
    };
    if (sigaltstack(&ss, NULL) == -1) {
        perror("sigaltstack");
        return 1;
    }

    /* 3. Install SIGSEGV handler with SA_ONSTACK flag */
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = sigsegv_handler;
    sa.sa_flags     = SA_SIGINFO | SA_ONSTACK; /* Use alternate stack */
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV, &sa, NULL);

    printf("Triggering stack overflow...\n");
    overflow(0); /* This will overflow and trigger SIGSEGV */

    /* Never reached */
    free(alt_stack);
    return 0;
}
```

---

## 15. `signalfd` — Signals as File Descriptors

### Motivation

Traditional signal handlers run asynchronously, with all the async-signal-safety restrictions. `signalfd` converts signals into **file descriptor events** that can be handled synchronously using `read()`, `select()`, `poll()`, or `epoll`.

This is the modern, clean approach for event-driven programs.

### API

```c
#include <sys/signalfd.h>

int signalfd(int fd, const sigset_t *mask, int flags);
/*
 * fd     = -1 to create new fd, or existing fd to update mask
 * mask   = set of signals to receive via this fd
 * flags  = SFD_NONBLOCK | SFD_CLOEXEC
 */
```

When a signal in `mask` is delivered, it becomes readable on the fd. Read it with:

```c
struct signalfd_siginfo {
    uint32_t ssi_signo;   /* Signal number */
    int32_t  ssi_errno;   /* Error number */
    int32_t  ssi_code;    /* Signal code (si_code) */
    uint32_t ssi_pid;     /* PID of sender */
    uint32_t ssi_uid;     /* Real UID of sender */
    int32_t  ssi_fd;      /* File descriptor (SIGIO) */
    uint32_t ssi_tid;     /* Kernel timer ID (POSIX timers) */
    uint32_t ssi_band;    /* Band event (SIGIO) */
    uint32_t ssi_overrun; /* POSIX timer overrun count */
    uint32_t ssi_trapno;  /* Trap number that caused signal */
    int32_t  ssi_status;  /* Exit status or signal (SIGCHLD) */
    int32_t  ssi_int;     /* Integer sent by sigqueue(2) */
    uint64_t ssi_ptr;     /* Pointer sent by sigqueue(2) */
    uint64_t ssi_utime;   /* User CPU time consumed (SIGCHLD) */
    uint64_t ssi_stime;   /* System CPU time consumed (SIGCHLD) */
    uint64_t ssi_addr;    /* Address that generated signal (hardware) */
    /* ... padding ... */
};
```

### C Implementation: `signalfd` with `epoll`

```c
/*
 * signalfd_epoll.c
 * Modern signal handling using signalfd + epoll.
 * No async signal handlers. No volatile flags. Clean and safe.
 *
 * Compile: gcc -Wall -o signalfd_epoll signalfd_epoll.c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/signalfd.h>
#include <sys/epoll.h>
#include <errno.h>

#define MAX_EVENTS 10

int main(void)
{
    /* Step 1: Build signal mask for signals we want to handle */
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGUSR1);
    sigaddset(&mask, SIGUSR2);

    /*
     * Step 2: BLOCK these signals via normal delivery mechanism.
     * CRITICAL: Must block them BEFORE creating signalfd.
     * If not blocked, they'd be delivered asynchronously AND appear
     * on the fd, causing double handling.
     */
    if (sigprocmask(SIG_BLOCK, &mask, NULL) == -1) {
        perror("sigprocmask");
        return 1;
    }

    /* Step 3: Create signalfd */
    int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);
    if (sfd == -1) {
        perror("signalfd");
        return 1;
    }

    /* Step 4: Create epoll instance */
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd == -1) {
        perror("epoll_create1");
        return 1;
    }

    /* Step 5: Register signalfd with epoll */
    struct epoll_event ev = {
        .events  = EPOLLIN,
        .data.fd = sfd,
    };
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev) == -1) {
        perror("epoll_ctl");
        return 1;
    }

    printf("PID %d running. Send signals to test:\n", getpid());
    printf("  kill -USR1 %d\n", getpid());
    printf("  kill -USR2 %d\n", getpid());
    printf("  Ctrl+C or kill %d  to quit\n", getpid());

    /* Step 6: Event loop */
    struct epoll_event events[MAX_EVENTS];
    int running = 1;

    while (running) {
        int n = epoll_wait(epfd, events, MAX_EVENTS, -1);
        if (n == -1) {
            if (errno == EINTR) continue; /* epoll itself got interrupted */
            perror("epoll_wait");
            break;
        }

        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == sfd) {
                /* Read signal information */
                struct signalfd_siginfo ssi;
                ssize_t bytes = read(sfd, &ssi, sizeof(ssi));
                if (bytes != sizeof(ssi)) {
                    fprintf(stderr, "Unexpected read size from signalfd\n");
                    continue;
                }

                printf("[epoll] Signal %d (%s) from PID %u\n",
                       ssi.ssi_signo,
                       strsignal(ssi.ssi_signo),
                       ssi.ssi_pid);

                switch (ssi.ssi_signo) {
                case SIGINT:
                case SIGTERM:
                    printf("Shutdown requested. Exiting cleanly.\n");
                    running = 0;
                    break;
                case SIGUSR1:
                    printf("SIGUSR1: performing action 1\n");
                    break;
                case SIGUSR2:
                    printf("SIGUSR2: performing action 2\n");
                    break;
                default:
                    printf("Unexpected signal %d\n", ssi.ssi_signo);
                    break;
                }
            }
        }
    }

    close(epfd);
    close(sfd);
    return 0;
}
```

---

## 16. Signals in Multithreaded Programs

### Key Rules

1. **Signal disposition is process-wide**: Installing a handler in one thread installs it for all threads.

2. **Signal mask is per-thread**: Each thread can independently block or unblock signals.

3. **Signal delivery is to a thread**: A signal directed at the process (not a specific thread) is delivered to **one unblocked thread** (the kernel's choice, essentially unpredictable).

4. **Use `pthread_sigmask()`** (not `sigprocmask()`) in threads.

### Recommended Pattern: Dedicated Signal Thread

The cleanest approach in multithreaded programs:

```
┌─────────────────────────────────────────────────────┐
│                  Process                            │
│                                                     │
│  Thread 1 (worker)  ─── ALL signals BLOCKED         │
│  Thread 2 (worker)  ─── ALL signals BLOCKED         │
│  Thread 3 (worker)  ─── ALL signals BLOCKED         │
│                                                     │
│  Signal Thread      ─── signals UNBLOCKED           │
│    Uses sigwaitinfo() to receive signals            │
│    Dispatches to worker threads via                 │
│    condition variables / queues                     │
└─────────────────────────────────────────────────────┘
```

```c
/*
 * multithreaded_signals.c
 * Pattern: dedicated signal-handling thread.
 *
 * Compile: gcc -Wall -o mt_signals multithreaded_signals.c -lpthread
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <pthread.h>
#include <unistd.h>
#include <string.h>

static volatile int g_running = 1;

/* Signal handling thread function */
static void *signal_thread(void *arg)
{
    sigset_t *wait_set = (sigset_t *)arg;
    siginfo_t info;

    while (g_running) {
        int sig = sigwaitinfo(wait_set, &info);
        if (sig == -1) {
            if (errno == EINTR) continue;
            perror("sigwaitinfo");
            break;
        }

        printf("[signal_thread] Received signal %d (%s) from PID %d\n",
               sig, strsignal(sig), (int)info.si_pid);

        switch (sig) {
        case SIGTERM:
        case SIGINT:
            printf("[signal_thread] Shutdown requested.\n");
            g_running = 0;
            break;
        case SIGUSR1:
            printf("[signal_thread] SIGUSR1: custom action.\n");
            break;
        default:
            break;
        }
    }
    return NULL;
}

/* Worker thread */
static void *worker_thread(void *arg)
{
    int id = *(int *)arg;
    printf("[worker %d] started (signals all blocked)\n", id);
    while (g_running) {
        sleep(1);
        printf("[worker %d] tick\n", id);
    }
    printf("[worker %d] exiting\n", id);
    return NULL;
}

int main(void)
{
    /* Build the signal set we want to handle */
    sigset_t sig_set;
    sigemptyset(&sig_set);
    sigaddset(&sig_set, SIGINT);
    sigaddset(&sig_set, SIGTERM);
    sigaddset(&sig_set, SIGUSR1);

    /*
     * Block signals in MAIN THREAD FIRST.
     * New threads inherit the mask of the creating thread.
     * So all threads start with these signals blocked.
     */
    pthread_sigmask(SIG_BLOCK, &sig_set, NULL);

    /* Create worker threads (they inherit the blocked mask) */
    pthread_t workers[3];
    int ids[3] = {1, 2, 3};
    for (int i = 0; i < 3; i++) {
        pthread_create(&workers[i], NULL, worker_thread, &ids[i]);
    }

    /* Create dedicated signal thread */
    pthread_t sig_tid;
    pthread_create(&sig_tid, NULL, signal_thread, &sig_set);

    /* Wait for signal thread to finish */
    pthread_join(sig_tid, NULL);

    /* Wait for workers */
    for (int i = 0; i < 3; i++) {
        pthread_join(workers[i], NULL);
    }

    return 0;
}
```

---

## 17. Signals in fork/exec

### After `fork()`

The child inherits:
- Signal dispositions (handlers and SIG_IGN)
- Signal masks (blocked signals)
- Pending signals are **NOT** inherited (child has empty pending set)

### After `exec()`

- Custom signal handlers are **reset to SIG_DFL** (the handler code is gone after exec)
- Signals set to `SIG_IGN` are **preserved** across exec
- Blocked signal mask is preserved
- Pending signals are preserved

```
Parent                    Child (after fork)
Signal SIGINT = handler   Signal SIGINT = same handler (copy)
Signal SIGUSR1 = SIG_IGN  Signal SIGUSR1 = SIG_IGN
SIGTERM pending = YES     SIGTERM pending = NO (cleared)
Blocked = {SIGUSR2}       Blocked = {SIGUSR2} (inherited)

After child calls exec():
Signal SIGINT = SIG_DFL  (handler reset — code is gone)
Signal SIGUSR1 = SIG_IGN (preserved)
Blocked = {SIGUSR2}      (preserved)
```

### Why This Matters: Shell Command Execution

When a shell runs a command in the background (`cmd &`), it typically sets SIGINT and SIGQUIT to SIG_IGN for the background process. This persists across exec, which is why background processes don't die when you press Ctrl+C.

### SIGCHLD — Monitoring Children

`SIGCHLD` is sent to the parent when a child:
- Exits (normally or via signal)
- Is stopped (`SIGSTOP`, `SIGTSTP`)
- Is continued (`SIGCONT`)

```c
/*
 * sigchld_demo.c
 * Properly handling SIGCHLD to avoid zombie processes.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <string.h>

static void sigchld_handler(int sig)
{
    (void)sig;
    int saved_errno = errno; /* IMPORTANT: save/restore errno */

    int status;
    pid_t pid;

    /*
     * CRITICAL: Loop calling waitpid() with WNOHANG.
     * Multiple children may have exited between handler invocations
     * (signals are not queued).
     */
    while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
        if (WIFEXITED(status)) {
            /* Async-signal-safe way to write info */
            char buf[64];
            int n = snprintf(buf, sizeof(buf),
                             "Child %d exited with status %d\n",
                             (int)pid, WEXITSTATUS(status));
            write(STDOUT_FILENO, buf, (size_t)n);
        } else if (WIFSIGNALED(status)) {
            char buf[64];
            int n = snprintf(buf, sizeof(buf),
                             "Child %d killed by signal %d\n",
                             (int)pid, WTERMSIG(status));
            write(STDOUT_FILENO, buf, (size_t)n);
        }
    }

    errno = saved_errno; /* Restore errno — ESSENTIAL */
}

int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sigchld_handler;
    sa.sa_flags   = SA_RESTART | SA_NOCLDSTOP; /* Only notify on exit */
    sigemptyset(&sa.sa_mask);
    sigaction(SIGCHLD, &sa, NULL);

    /* Spawn some children */
    for (int i = 0; i < 3; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            /* Child */
            sleep(i + 1); /* Exit after 1, 2, 3 seconds */
            exit(i * 10);
        }
        printf("Spawned child PID %d\n", (int)pid);
    }

    /* Parent waits */
    printf("Parent waiting for children...\n");
    while (1) {
        pause();
        /* SIGCHLD handler cleaned up zombies */
    }
    return 0;
}
```

---

## 18. Job Control Signals

### The Job Control Model

```
Terminal (tty)
    │
    │ controls
    │
    ▼
Session Leader (shell)
    │
    ├── Foreground Process Group ──── receives terminal signals
    │       │
    │       ├── Process A
    │       └── Process B
    │
    └── Background Process Groups ── do NOT receive terminal signals
            │
            ├── Process C
            └── Process D
```

| Signal  | Trigger                                  | Default   | Catchable? |
|---------|------------------------------------------|-----------|------------|
| SIGTSTP | Ctrl+Z from terminal                     | Stop      | Yes        |
| SIGSTOP | `kill -STOP` or kernel internal          | Stop      | **NO**     |
| SIGCONT | `kill -CONT` or `fg`/`bg` shell commands | Continue  | Yes        |
| SIGTTIN | Background process reads from terminal   | Stop      | Yes        |
| SIGTTOU | Background process writes to terminal    | Stop      | Yes        |

### Terminal Process Groups

```c
/* Set process group for job control */
setpgid(pid, pgid);   /* Set process pid's group to pgid */
getpgrp();            /* Get current process's group ID */

/* The foreground process group of a terminal */
tcsetpgrp(STDIN_FILENO, pgid); /* Make pgid the foreground group */
tcgetpgrp(STDIN_FILENO);       /* Get current foreground group */
```

---

## 19. The Self-Pipe Trick

### Problem

You need to handle a signal in an event loop that uses `select()` or `poll()`. But signal handlers can't call most functions, and you want to integrate cleanly.

### Solution: Self-Pipe

Create a pipe. The signal handler writes one byte to the write end. The event loop monitors the read end with `select()`/`poll()`.

```
Signal arrives
      │
      ▼
Signal handler:
  write(pipe_write_fd, "x", 1)  ← async-signal-safe
      │
      ▼
pipe_read_fd becomes readable
      │
      ▼
select()/poll() wakes up
      │
      ▼
Main loop reads from pipe, processes the signal event
```

```c
/*
 * self_pipe.c
 * The classic self-pipe trick for signal + select() integration.
 *
 * Compile: gcc -Wall -o self_pipe self_pipe.c
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/select.h>

static int pipe_fds[2]; /* [0] = read end, [1] = write end */

static void make_nonblocking(int fd)
{
    int flags = fcntl(fd, F_GETFL);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static void pipe_signal_handler(int sig)
{
    /*
     * write() is async-signal-safe.
     * Cast sig to char to write the signal number as payload.
     */
    unsigned char byte = (unsigned char)sig;
    ssize_t n;
    do {
        n = write(pipe_fds[1], &byte, 1);
    } while (n == -1 && errno == EINTR);
    /* EAGAIN: pipe is full — that's OK, signal was already noted */
}

int main(void)
{
    /* Create pipe */
    if (pipe(pipe_fds) == -1) {
        perror("pipe");
        return 1;
    }

    /* Make both ends non-blocking */
    make_nonblocking(pipe_fds[0]);
    make_nonblocking(pipe_fds[1]);

    /* Install handlers for signals we care about */
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = pipe_signal_handler;
    sa.sa_flags   = SA_RESTART;
    sigemptyset(&sa.sa_mask);

    sigaction(SIGINT,  &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGUSR1, &sa, NULL);

    printf("PID %d. Send signals or Ctrl+C.\n", getpid());

    fd_set read_fds;
    int max_fd = pipe_fds[0];

    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(pipe_fds[0], &read_fds);
        /* Add other fds here (sockets, files, etc.) */

        int ret = select(max_fd + 1, &read_fds, NULL, NULL, NULL);
        if (ret == -1) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }

        if (FD_ISSET(pipe_fds[0], &read_fds)) {
            /* Drain the pipe — handle all pending signals */
            unsigned char sig_byte;
            while (read(pipe_fds[0], &sig_byte, 1) == 1) {
                printf("[main] Handling signal %d (%s)\n",
                       (int)sig_byte, strsignal((int)sig_byte));

                if (sig_byte == SIGINT || sig_byte == SIGTERM) {
                    printf("[main] Shutting down.\n");
                    close(pipe_fds[0]);
                    close(pipe_fds[1]);
                    return 0;
                }
            }
        }
    }

    close(pipe_fds[0]);
    close(pipe_fds[1]);
    return 0;
}
```

> **Modern alternative**: Use `signalfd()` instead of the self-pipe trick. `signalfd()` is cleaner and is the preferred approach on Linux 2.6.22+.

---

## 20. Common Real-World Patterns

### Pattern 1: Graceful Daemon Shutdown

```
SIGTERM arrives
      │
      ▼
Set g_shutdown = 1
      │
      ▼
Main loop: g_shutdown == 1
      │
      ▼
Close connections
Flush buffers
Write PID file cleanup
Free resources
exit(0)
```

### Pattern 2: Config Reload on SIGHUP

```
SIGHUP arrives
      │
      ▼
Set g_reload = 1
      │
      ▼
Main loop: g_reload == 1
      │
      ▼
Re-read config file
Apply new settings
Reset g_reload = 0
Log "Config reloaded"
Continue operation
```

### Pattern 3: Watchdog with SIGALRM

```c
/*
 * watchdog.c
 * Watchdog timer using SIGALRM.
 * If main operation doesn't complete in time, SIGALRM fires.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <setjmp.h>

static sigjmp_buf alarm_jmp;

static void alarm_handler(int sig)
{
    (void)sig;
    siglongjmp(alarm_jmp, 1); /* Non-local jump out of the timed region */
}

int timed_operation(unsigned int timeout_secs)
{
    struct sigaction sa, old_sa;
    sa.sa_handler = alarm_handler;
    sa.sa_flags   = 0;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGALRM, &sa, &old_sa);

    if (sigsetjmp(alarm_jmp, 1) != 0) {
        /* We got here via SIGALRM — timeout occurred */
        alarm(0); /* Cancel any remaining alarm */
        sigaction(SIGALRM, &old_sa, NULL);
        return -1; /* Timed out */
    }

    alarm(timeout_secs); /* Set timeout */

    /* ---- Do the potentially-long operation here ---- */
    printf("Starting long operation (timeout: %u sec)\n", timeout_secs);
    sleep(10); /* Simulate a slow operation */
    /* ------------------------------------------------ */

    alarm(0); /* Cancel alarm if we finished in time */
    sigaction(SIGALRM, &old_sa, NULL);
    return 0; /* Success */
}

int main(void)
{
    int ret = timed_operation(3);
    if (ret == -1) {
        printf("Operation timed out!\n");
    } else {
        printf("Operation completed successfully.\n");
    }
    return 0;
}
```

---

## 21. Rust and Signals

### The Challenge

Rust's ownership and safety model makes signal handling tricky:
- Signal handlers interrupt arbitrary Rust code, including the allocator
- `async-signal-safe` applies just as strictly
- Rust's standard library provides minimal signal support

### Approach 1: `signal-hook` Crate (Recommended)

`signal-hook` is the community-standard crate for signal handling in Rust. It provides several safe abstractions.

Add to `Cargo.toml`:

```toml
[dependencies]
signal-hook = "0.3"
signal-hook-iterator = "0.2"
```

#### Example: Flag-based handling with `signal-hook`

```rust
// signal_flag.rs
// Uses signal_hook to set an atomic flag when SIGTERM/SIGINT arrives.

use signal_hook::consts::signal::{SIGINT, SIGTERM, SIGUSR1};
use signal_hook::flag as signal_flag;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn main() {
    // Create atomic flags that signal_hook will set to 'true'
    // when the corresponding signal arrives.
    let shutdown = Arc::new(AtomicBool::new(false));
    let reload   = Arc::new(AtomicBool::new(false));

    // Register signals — signal_hook atomically sets the flag
    // using async-signal-safe operations internally.
    signal_flag::register(SIGTERM, Arc::clone(&shutdown))
        .expect("Failed to register SIGTERM");
    signal_flag::register(SIGINT, Arc::clone(&shutdown))
        .expect("Failed to register SIGINT");
    signal_flag::register(SIGUSR1, Arc::clone(&reload))
        .expect("Failed to register SIGUSR1");

    println!("PID: {}", std::process::id());
    println!("Running. Send SIGUSR1 to reload, SIGTERM/Ctrl+C to stop.");

    loop {
        if shutdown.load(Ordering::Relaxed) {
            println!("Shutdown requested. Exiting cleanly.");
            break;
        }

        if reload.swap(false, Ordering::Relaxed) {
            println!("Reload requested. Reloading config...");
            // do_reload_config();
        }

        // Main work here
        thread::sleep(Duration::from_millis(100));
    }
}
```

#### Example: Iterator-based signal handling

```rust
// signal_iterator.rs
// Iterates over incoming signals in a clean, synchronous style.

use signal_hook::consts::signal::{SIGINT, SIGTERM, SIGUSR1, SIGUSR2};
use signal_hook::iterator::Signals;
use std::thread;
use std::time::Duration;

fn main() {
    // Create a Signals iterator that yields signal numbers
    let mut signals = Signals::new([SIGINT, SIGTERM, SIGUSR1, SIGUSR2])
        .expect("Failed to create Signals iterator");

    println!("PID: {}. Waiting for signals...", std::process::id());

    // Spawn a background thread to receive signals
    let handle = thread::spawn(move || {
        for signal in &mut signals {
            println!("Received signal: {}", signal);
            match signal {
                SIGTERM | SIGINT => {
                    println!("Shutting down...");
                    return;
                }
                SIGUSR1 => {
                    println!("SIGUSR1: doing action 1");
                }
                SIGUSR2 => {
                    println!("SIGUSR2: doing action 2");
                }
                _ => {
                    println!("Unknown signal: {}", signal);
                }
            }
        }
    });

    // Simulate main work
    for i in 0..60 {
        thread::sleep(Duration::from_secs(1));
        println!("[main] tick {}", i);
    }

    handle.join().unwrap();
}
```

### Approach 2: `signalfd` in Rust (Low-Level)

For full control, use the `nix` crate which provides safe wrappers around Linux system calls:

```toml
[dependencies]
nix = { version = "0.27", features = ["signal", "poll"] }
```

```rust
// signalfd_rust.rs
// Low-level signalfd usage in Rust using the nix crate.

use nix::sys::signal::{SigSet, Signal};
use nix::sys::signalfd::{signalfd, SfdFlags, SignalFdSigInfo};
use nix::sys::epoll::{epoll_create1, epoll_ctl, epoll_wait,
                      EpollCreateFlags, EpollEvent, EpollFlags, EpollOp};
use std::os::unix::io::RawFd;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Build signal mask
    let mut mask = SigSet::empty();
    mask.add(Signal::SIGINT);
    mask.add(Signal::SIGTERM);
    mask.add(Signal::SIGUSR1);

    // Block these signals from normal delivery
    mask.thread_block()?;

    // Create signalfd
    let sfd: RawFd = signalfd(-1, &mask, SfdFlags::SFD_NONBLOCK | SfdFlags::SFD_CLOEXEC)?;

    // Create epoll
    let epfd = epoll_create1(EpollCreateFlags::EPOLL_CLOEXEC)?;

    // Register signalfd with epoll
    let mut event = EpollEvent::new(EpollFlags::EPOLLIN, sfd as u64);
    epoll_ctl(epfd, EpollOp::EpollCtlAdd, sfd, Some(&mut event))?;

    println!("PID: {}. Waiting for signals via signalfd...",
             std::process::id());

    let mut events = vec![EpollEvent::empty(); 10];
    loop {
        let n = epoll_wait(epfd, &mut events, -1)?;
        for ev in &events[..n] {
            if ev.data() == sfd as u64 {
                // Read signal info
                let mut buf = [0u8; std::mem::size_of::<SignalFdSigInfo>()];
                let bytes = unsafe {
                    nix::unistd::read(sfd, &mut buf)?
                };
                if bytes == std::mem::size_of::<SignalFdSigInfo>() {
                    let info: SignalFdSigInfo = unsafe {
                        std::ptr::read(buf.as_ptr() as *const _)
                    };
                    let sig_num = info.ssi_signo;
                    println!("Signal {} from PID {}", sig_num, info.ssi_pid);

                    if sig_num == Signal::SIGINT as u32
                        || sig_num == Signal::SIGTERM as u32
                    {
                        println!("Shutting down.");
                        nix::unistd::close(sfd)?;
                        nix::unistd::close(epfd)?;
                        return Ok(());
                    }
                }
            }
        }
    }
}
```

### Approach 3: Unsafe Raw Signal Handling in Rust

For special cases where you need the lowest level:

```rust
// raw_signal.rs
// Direct use of libc for signal handling.
// This is UNSAFE and requires careful attention to async-signal safety.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

static SHUTDOWN: AtomicBool = AtomicBool::new(false);

extern "C" fn sigterm_handler(_: libc::c_int) {
    // ONLY async-signal-safe operations here.
    // AtomicBool::store uses an atomic CPU instruction — safe.
    SHUTDOWN.store(true, Ordering::Relaxed);
}

fn main() {
    unsafe {
        // Install SIGTERM handler
        libc::signal(libc::SIGTERM, sigterm_handler as libc::sighandler_t);
        libc::signal(libc::SIGINT,  sigterm_handler as libc::sighandler_t);
    }

    println!("Running. PID: {}", std::process::id());

    while !SHUTDOWN.load(Ordering::Relaxed) {
        std::thread::sleep(std::time::Duration::from_millis(100));
    }

    println!("Exiting cleanly.");
}
```

---

## 22. Debugging Signals

### `strace` — Trace Signal-Related Syscalls

```bash
# Trace all signal-related syscalls for a running process
strace -p <PID> -e trace=signal

# Trace a specific program from start
strace -e trace=signal ./my_program

# Sample output:
# sigaction(SIGINT, {sa_handler=0x401234, sa_mask=[SIGTERM], ...}, NULL) = 0
# rt_sigprocmask(SIG_BLOCK, [USR1 USR2], [], 8) = 0
# pause() = -1 EINTR (Interrupted system call)
```

### `/proc` Filesystem — Inspect Signal State

```bash
# View signal information for process PID
cat /proc/<PID>/status | grep -E "^Sig"

# Output explanation:
# SigPnd: 0000000000000000  ← Pending signals (hex bitmask, thread-private)
# SigBlk: 0000000000010000  ← Blocked signals (bit 16 = SIGUSR1 here)
# SigIgn: 0000000000000000  ← Ignored signals
# SigCgt: 0000000000000002  ← Caught signals (bit 1 = SIGHUP here)

# Decode a signal bitmask:
python3 -c "
mask = 0x0000000000010000
for bit in range(64):
    if mask & (1 << bit):
        print(f'Signal {bit+1}')
"
```

### `/proc/<PID>/status` Fields

| Field  | Meaning                                      |
|--------|----------------------------------------------|
| SigPnd | Thread-private pending signals               |
| ShdPnd | Process-wide shared pending signals          |
| SigBlk | Blocked signal mask                          |
| SigIgn | Signals with SIG_IGN disposition            |
| SigCgt | Signals with custom handler (caught)         |

### GDB — Debug Signal Delivery

```gdb
# List how GDB handles each signal
info signals

# Tell GDB not to stop on SIGUSR1 (let it pass to the program)
handle SIGUSR1 noprint nostop pass

# Tell GDB to stop when SIGTERM is received
handle SIGTERM stop print

# Send a signal to the debugged process
signal SIGUSR1

# Continue after signal
continue
```

### `kill` Command Reference

```bash
kill -l                     # List all signal names and numbers
kill -SIGTERM <PID>         # Send SIGTERM (same as kill -15)
kill -9 <PID>               # Send SIGKILL
kill -SIGUSR1 <PID>         # Send SIGUSR1
kill -0 <PID>               # Check if process exists (no signal sent)
killall -SIGHUP nginx       # Send to all processes named 'nginx'
pkill -SIGUSR1 myapp        # Send by name pattern
```

---

## 23. Security Considerations

### Signal Permission Rules

A process may send a signal to another process only if:
1. The sender has **CAP_KILL** capability, OR
2. The sender's **real or effective UID** matches the target's **real or saved set-user-ID**

Exception: **SIGCONT** can be sent to any process in the same session.

```c
/* Check if you can signal a process without actually sending */
if (kill(target_pid, 0) == 0) {
    printf("Have permission to signal PID %d\n", target_pid);
} else if (errno == EPERM) {
    printf("No permission to signal PID %d\n", target_pid);
} else if (errno == ESRCH) {
    printf("Process %d does not exist\n", target_pid);
}
```

### Signal Injection Attacks

In setuid programs, be careful: a signal can be sent by any process running as the same user. An attacker could:
1. Spam SIGCHLD to trigger `waitpid()` at unexpected times
2. Send SIGALRM to interrupt timed operations
3. Send SIGUSR1/SIGUSR2 if their handlers have side effects

**Defense**: In sensitive setuid programs, block all non-essential signals at startup.

### `SIGPIPE` and Network Programs

Writing to a broken socket/pipe sends SIGPIPE, which terminates the process by default. Always either:
1. Set `SIGPIPE` to `SIG_IGN` and check `write()` return values
2. Use `MSG_NOSIGNAL` flag with `send()`
3. Use `SO_NOSIGPIPE` socket option (BSD, not Linux)

```c
/* Option 1: Ignore SIGPIPE globally */
signal(SIGPIPE, SIG_IGN);

/* Then check write() return */
ssize_t n = write(fd, buf, len);
if (n == -1 && errno == EPIPE) {
    /* Connection broken */
}

/* Option 2: Per-send, suppress SIGPIPE */
ssize_t n = send(sockfd, buf, len, MSG_NOSIGNAL);
```

---

## 24. Mental Models and Expert Intuition

### Mental Model 1: Signals as Interrupts

Think of signals as **hardware interrupts in software**. Just as a keyboard interrupt pauses the CPU to run an ISR (Interrupt Service Routine), a signal pauses a process to run a handler.

The key insight: both hardware interrupts and signal handlers must be **fast, minimal, and safe**. They execute in a restricted environment.

### Mental Model 2: Two Execution Contexts

When a program uses signals, it has **two separate execution contexts**:

```
Context A: Normal code (main loop, functions)
  - Can call any function
  - Can use all data structures
  - Runs at your program's "normal" speed

Context B: Signal handler
  - Can ONLY call async-signal-safe functions
  - Accesses shared data ONLY via atomic types
  - Must be fast (very short execution)
  - Can interrupt Context A at ANY point

Communication from B → A: volatile sig_atomic_t flags
Communication from A → B: signal masks (block/unblock)
```

### Mental Model 3: The Kernel Wrapper Around Your Code

```
Your program runs inside a "kernel envelope":

  ┌────────────────────────────────────┐
  │            KERNEL                  │
  │  ┌──────────────────────────────┐  │
  │  │       Your Process           │  │
  │  │                              │  │
  │  │  normal code executes here   │  │
  │  │                              │  │
  │  └──────────────────────────────┘  │
  │                                    │
  │  The kernel can inject execution   │
  │  into your process at any point    │
  │  (signal delivery)                 │
  └────────────────────────────────────┘
```

### Mental Model 4: The Signal Mask as a Shield

```
  Dangerous signals flying around:
    SIGALRM ~~~~▶  ╔═══════════╗  ~~~~▶  blocked!
    SIGUSR1 ~~~~▶  ║   Signal  ║  ~~~~▶  blocked!
    SIGTERM ~~~~▶  ║   Mask    ║  ────▶  DELIVERED (unblocked)
                   ╚═══════════╝
```

Use the mask to protect critical sections, just like a mutex protects shared data in threading.

### Deliberate Practice: Signal Mastery Progression

```
Level 1: Beginner
  □ Install SIGTERM/SIGINT handlers for graceful shutdown
  □ Understand async-signal-safety rule
  □ Use volatile sig_atomic_t flags

Level 2: Intermediate
  □ Use sigaction() correctly with all flags
  □ Implement SIGCHLD handler with zombie reaping
  □ Use sigprocmask() for critical sections
  □ Implement self-pipe trick

Level 3: Advanced
  □ Use signalfd() with epoll for event-driven programs
  □ Real-time signals with sigqueue()
  □ Thread-safe signal architecture (dedicated signal thread)
  □ Alternate signal stacks for SIGSEGV recovery

Level 4: Expert
  □ Understand kernel signal frame mechanism
  □ Use pidfd for race-free signal sending
  □ Implement signal-based watchdog timers
  □ Debug signal behavior with /proc and strace
```

### Cognitive Principle: Chunking Signal Patterns

Expert programmers don't think signal by signal. They recognize **patterns** (chunks):

- "Daemon lifecycle" pattern → SIGHUP reload + SIGTERM shutdown
- "Zombie prevention" pattern → SIGCHLD + WNOHANG loop
- "Timeout" pattern → SIGALRM + sigjmp
- "Event loop" pattern → signalfd + epoll
- "Thread safety" pattern → block all + dedicated thread + sigwaitinfo

Recognizing which pattern applies is faster than reasoning from first principles each time. Build your pattern library through **deliberate practice** — implement each pattern from scratch, not just read it.

---

## 25. Appendix — Quick Reference Tables

### Async-Signal-Safe Checklist

```
Before writing ANYTHING in a signal handler, ask:
  □ Is this function on the POSIX async-signal-safe list?
  □ Am I using only volatile sig_atomic_t (or atomic ops)?
  □ Am I avoiding all standard library I/O (printf, etc.)?
  □ Am I using write() instead of printf() for output?
  □ Am I saving/restoring errno?
  □ Am I avoiding dynamic memory allocation (malloc/free)?
  □ Am I avoiding any mutex that main code might hold?
```

### Signal Function Quick Reference

| Task                              | Function(s)                          |
|-----------------------------------|--------------------------------------|
| Install handler (modern)          | `sigaction()`                        |
| Install handler (legacy, avoid)   | `signal()`                           |
| Block/unblock signals             | `sigprocmask()` / `pthread_sigmask()`|
| Check pending signals             | `sigpending()`                       |
| Wait for a signal                 | `pause()`, `sigsuspend()`            |
| Wait synchronously                | `sigwaitinfo()`, `sigtimedwait()`    |
| Send to process                   | `kill()`                             |
| Send to self                      | `raise()`                            |
| Send with data                    | `sigqueue()`                         |
| Send to thread                    | `tgkill()`                           |
| Signals as fd events              | `signalfd()`                         |
| Alternate signal stack            | `sigaltstack()`                      |
| Initialize signal set             | `sigemptyset()`, `sigfillset()`      |
| Modify signal set                 | `sigaddset()`, `sigdelset()`         |
| Test signal set                   | `sigismember()`                      |

### Compilation Flags for Signal Code

```bash
# Always compile with:
gcc -Wall -Wextra -D_POSIX_C_SOURCE=200809L -o output source.c

# For real-time signals:
gcc -Wall -Wextra -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -o output source.c

# For signalfd/epoll (Linux-specific):
gcc -Wall -Wextra -D_GNU_SOURCE -o output source.c
```

### Signal Disposition Decision Tree

```
Do you need to handle this signal?
        │
   YES  │         NO
        ▼         ▼
Is it SIGKILL    SIG_IGN
or SIGSTOP? ─YES─▶ (can't catch,
        │           must accept default)
        NO
        ▼
Do you need signal info
(who sent it, why)?
        │
   YES  ▼         NO
   SA_SIGINFO      sa_handler
   sa_sigaction    (simple handler)
        │
        ▼
Do you need to restart
interrupted syscalls?
   YES ──▶ SA_RESTART
   NO  ──▶ Check errno == EINTR in all I/O

Do you need alt stack
(for SIGSEGV/stack overflow)?
   YES ──▶ sigaltstack() + SA_ONSTACK
```

---

## Summary: The 10 Laws of Linux Signals

```
1. SIGKILL and SIGSTOP cannot be caught, blocked, or ignored.
   The kernel enforces this absolutely.

2. Signal handlers must only call async-signal-safe functions.
   Violation causes undefined behavior — use the flag pattern.

3. Use sigaction(), never signal() for new code.
   signal() has undefined behavior across implementations.

4. Always loop waitpid(WNOHANG) in SIGCHLD handlers.
   Multiple children may exit between handler invocations.

5. Save and restore errno in every signal handler.
   Signal handlers can corrupt errno for interrupted syscalls.

6. Use sigsuspend() not pause() when guarding with a flag.
   pause() has an irreducible race condition.

7. Block signals before creating signalfd.
   Otherwise signals are delivered twice.

8. In multithreaded programs, block all signals in main,
   then use a dedicated signal thread with sigwaitinfo().

9. Use volatile sig_atomic_t for flags shared between
   signal handlers and normal code.

10. Prefer signalfd over signal handlers for event loops.
    It enables synchronous, type-safe, composable signal handling.
```

---

*Guide compiled for deep mastery of Linux signals — from userspace patterns to kernel internals. Implemented in C and Rust for maximum precision and systems-level clarity.*

I'll now craft the complete, in-depth guide. This will be a large, multi-section markdown file covering everything from kernel internals to C/Rust implementations.Here is your complete guide — 25 sections, covering every layer from beginner to kernel internals. Here's a map of what's inside:

**Foundational Concepts**
- What signals are, the two-stage lifecycle (generation → pending → delivery), and why they're not general-purpose IPC
- Full table of all 31 standard signals with default actions and trigger conditions

**Kernel Internals (Deep)**
- `task_struct` signal fields, `sigpending` bitmask vs real-time queue, `sighand_struct` handler table
- How `do_signal()` sets up the signal frame on your user-space stack, saves CPU registers, and uses the `sigreturn` trampoline to restore them
- Syscall restart mechanics (`SA_RESTART`, `ERESTART_RESTARTBLOCK`, `EINTR` handling)

**API Mastery**
- `sigaction()` with all flags explained, `siginfo_t` fields and `si_code` table
- `sigprocmask()`, `sigpending()`, `sigsuspend()` (with the classic race explained), `sigwaitinfo()`
- `kill()`, `sigqueue()`, `tgkill()`, `pidfd_send_signal()` (Linux 5.1+ race-free API)

**Advanced Patterns (C + Rust)**
- **Self-pipe trick** — integrate signals with `select()`/`poll()` safely
- **`signalfd` + `epoll`** — modern synchronous signal handling in an event loop
- **Dedicated signal thread** pattern for multithreaded programs
- **Alternate signal stack** — catch `SIGSEGV` from stack overflow
- **Watchdog** with `SIGALRM` + `sigjmp`

**Rust Coverage**
- `signal-hook` crate (atomic flags + iterator approach)
- `nix` crate for `signalfd` in safe Rust
- Raw `libc` unsafe approach for special cases

**Debugging & Security**
- `strace`, `/proc/<PID>/status` bitmask decoding, `gdb` signal control
- Signal permission rules, SIGPIPE in network code, setuid security

The guide ends with **The 10 Laws of Linux Signals** — a condensed mental checklist for production-level work.