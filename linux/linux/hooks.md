# Linux Kernel Hooks — The Complete In-Depth Guide

> *"To master the kernel is to understand the conversation between hardware and software — hooks are how you listen in, and speak back."*

---

## Table of Contents

1. [Mental Model: What Is a Hook?](#1-mental-model-what-is-a-hook)
2. [Linux Kernel Architecture — Where Hooks Live](#2-linux-kernel-architecture-where-hooks-live)
3. [The Taxonomy of Linux Kernel Hooks](#3-the-taxonomy-of-linux-kernel-hooks)
4. [kprobes — Dynamic Kernel Instrumentation](#4-kprobes--dynamic-kernel-instrumentation)
5. [uprobes — Userspace Probing from the Kernel](#5-uprobes--userspace-probing-from-the-kernel)
6. [Tracepoints — Static Instrumentation Points](#6-tracepoints--static-instrumentation-points)
7. [ftrace — The Function Tracer Framework](#7-ftrace--the-function-tracer-framework)
8. [eBPF — The Universal Hook Platform](#8-ebpf--the-universal-hook-platform)
9. [LSM Hooks — Linux Security Module Framework](#9-lsm-hooks--linux-security-module-framework)
10. [Netfilter Hooks — Network Stack Interception](#10-netfilter-hooks--network-stack-interception)
11. [Syscall Hooks — System Call Interception](#11-syscall-hooks--system-call-interception)
12. [Audit Hooks — Kernel Audit Framework](#12-audit-hooks--kernel-audit-framework)
13. [Notification Chains — Internal Kernel Events](#13-notification-chains--internal-kernel-events)
14. [Perf Events & PMU Hooks](#14-perf-events--pmu-hooks)
15. [VFS Hooks — Virtual Filesystem Layer](#15-vfs-hooks--virtual-filesystem-layer)
16. [Module & Livepatch Hooks](#16-module--livepatch-hooks)
17. [Rust in the Linux Kernel — Safe Hook Implementations](#17-rust-in-the-linux-kernel--safe-hook-implementations)
18. [Comparison Matrix & Decision Framework](#18-comparison-matrix--decision-framework)
19. [Real-World Patterns & Architectures](#19-real-world-patterns--architectures)
20. [Security, Pitfalls & Best Practices](#20-security-pitfalls--best-practices)

---

## 1. Mental Model: What Is a Hook?

### The Fundamental Concept

Before everything else — what is a **hook**?

A **hook** is a pre-defined or dynamically inserted **intervention point** in a flow of execution, where external code can be called, control can be transferred, data can be observed, or behavior can be modified — **without altering the original code path's source**.

Think of it this way:

```
Normal Execution:
  A → B → C → D → E

Hooked Execution:
  A → B → [HOOK: your code runs here] → C → D → E
              ↑
      You observe, modify, or intercept
```

### The Three Powers of a Hook

```
┌─────────────────────────────────────────────────────────────┐
│                    HOOK CAPABILITIES                        │
│                                                             │
│  1. OBSERVE    │  Read data without changing behavior       │
│                │  Example: log arguments to open()          │
│                │                                            │
│  2. INTERCEPT  │  Halt execution, return early              │
│                │  Example: block a syscall based on policy  │
│                │                                            │
│  3. MODIFY     │  Change data in-flight                     │
│                │  Example: rewrite a network packet         │
└─────────────────────────────────────────────────────────────┘
```

### Why Hooks Exist in the Kernel

The Linux kernel is a monolithic, compiled binary. You cannot pause it and insert print statements. Hooks solve this by:

- **Observability**: Watch what is happening without recompiling
- **Security enforcement**: Check policies at critical decision points
- **Extensibility**: Let modules add behavior at well-defined points
- **Debugging**: Diagnose production systems without stopping them
- **Performance monitoring**: Measure latency, count events

### The Cognitive Hierarchy — How to Think About Hooks

```
┌────────────────────────────────────────────────┐
│            HOOK ABSTRACTION LAYERS             │
│                                                │
│  HIGH LEVEL  eBPF Programs (safe, portable)    │
│              ↑ you write logic here            │
│  MID LEVEL   kprobes, tracepoints, ftrace      │
│              ↑ kernel machinery                │
│  LOW LEVEL   INT3 breakpoints, text patching   │
│              ↑ CPU instruction manipulation    │
│  METAL       CPU debug registers, PMU          │
└────────────────────────────────────────────────┘
```

When you understand all layers, your mental model becomes: **"Every high-level hook eventually becomes a CPU mechanism."**

---

## 2. Linux Kernel Architecture — Where Hooks Live

### The Kernel's Major Subsystems

To understand where hooks live, you must first understand what the kernel is made of.

```
╔══════════════════════════════════════════════════════════════════╗
║                     LINUX KERNEL INTERNALS                       ║
║                                                                  ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   ║
║  │  USER SPACE  │  │  USER SPACE  │  │    USER SPACE        │   ║
║  │  Process A   │  │  Process B   │  │    Process C         │   ║
║  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   ║
║         │                 │                      │               ║
║  ═══════╪═════════════════╪══════════════════════╪═══════════════║
║         │       SYSTEM CALL INTERFACE            │               ║
║  ═══════╪═════════════════╪══════════════════════╪═══════════════║
║         ↓                 ↓                      ↓               ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │                   KERNEL SPACE                              │ ║
║  │                                                             │ ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ ║
║  │  │   VFS    │ │  Network │ │  Memory  │ │   Process    │  │ ║
║  │  │  Layer   │ │  Stack   │ │  Mgmt    │ │  Scheduler   │  │ ║
║  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │ ║
║  │       │            │            │               │           │ ║
║  │  ┌────┴────────────┴────────────┴───────────────┴────────┐  │ ║
║  │  │           HOOK INSERTION POINTS                       │  │ ║
║  │  │  [kprobe] [tracepoint] [LSM] [netfilter] [ftrace]     │  │ ║
║  │  └───────────────────────────────────────────────────────┘  │ ║
║  │                                                             │ ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ ║
║  │  │  Device  │ │   IPC    │ │  Crypto  │ │   Security   │  │ ║
║  │  │  Drivers │ │  Subsys  │ │  Layer   │ │  (LSM/SEL.)  │  │ ║
║  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                              │                                   ║
║  ══════════════════════════════════════════════════════════════  ║
║                     HARDWARE ABSTRACTION                         ║
║  ══════════════════════════════════════════════════════════════  ║
║         ↓                 ↓                      ↓               ║
║  ┌────────────┐  ┌───────────────┐  ┌──────────────────────┐    ║
║  │    CPU     │  │    Memory     │  │   Network / Storage  │    ║
║  └────────────┘  └───────────────┘  └──────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════╝
```

### The Execution Context — Critical Background

**Every hook runs in a specific execution context.** If you violate context rules, you will get kernel panics or deadlocks.

```
EXECUTION CONTEXTS IN LINUX:

  ┌─────────────────────────────────────────────────────────┐
  │ PROCESS CONTEXT                                         │
  │  - Running on behalf of a user process                 │
  │  - Can sleep, can access user memory                   │
  │  - current pointer is valid                            │
  │  - Example: system calls, read/write handlers          │
  ├─────────────────────────────────────────────────────────┤
  │ INTERRUPT CONTEXT                                       │
  │  - Running in a hardware/software interrupt handler    │
  │  - CANNOT sleep                                        │
  │  - CANNOT access user memory                           │
  │  - Must be very fast                                   │
  │  - Example: IRQ handlers, softirq, tasklets            │
  ├─────────────────────────────────────────────────────────┤
  │ NMI CONTEXT (Non-Maskable Interrupt)                    │
  │  - Even more restricted                                │
  │  - Almost nothing is safe to call                      │
  │  - Used by hardware watchdogs, perf events             │
  └─────────────────────────────────────────────────────────┘
```

**Psychological note**: Before writing a single hook, ask: *"In what context will this hook fire?"* — This single question prevents 80% of hook-related kernel crashes.

---

## 3. The Taxonomy of Linux Kernel Hooks

### Complete Hook Family Tree

```
LINUX KERNEL HOOKS
│
├── DYNAMIC (inserted at runtime, no source change needed)
│   ├── kprobes           → instrument any kernel instruction
│   ├── kretprobes        → instrument function return
│   ├── uprobes           → instrument userspace from kernel
│   └── ftrace function hooks
│
├── STATIC (compiled into kernel, zero-overhead when inactive)
│   ├── tracepoints       → TRACE_EVENT() macro system
│   ├── syscall tracepoints
│   └── perf static tracepoints
│
├── FRAMEWORK HOOKS (structured extension points)
│   ├── LSM hooks         → security decisions
│   ├── netfilter hooks   → network packet processing
│   ├── VFS operations    → filesystem callbacks
│   ├── notification chains → internal kernel events
│   └── audit hooks       → security auditing
│
├── BPF/eBPF (safe, sandboxed programs attached to hooks)
│   ├── kprobe BPF        → attach BPF to kprobe
│   ├── tracepoint BPF    → attach BPF to tracepoint
│   ├── XDP               → eXpress Data Path (network)
│   ├── TC BPF            → traffic control
│   ├── socket BPF        → socket operations
│   ├── cgroup BPF        → cgroup operations
│   ├── LSM BPF           → security enforcement
│   └── fentry/fexit      → function entry/exit (BTF-based)
│
└── LOW-LEVEL / SPECIALIZED
    ├── CPU debug registers (hardware breakpoints)
    ├── PMU (Performance Monitoring Unit) hooks
    ├── livepatch          → hot-patching kernel functions
    └── module init/exit callbacks
```

---

## 4. kprobes — Dynamic Kernel Instrumentation

### Conceptual Foundation

**kprobes** is the most fundamental dynamic instrumentation mechanism in Linux. It allows you to **intercept the execution of almost any kernel instruction** — function entries, exits, or any specific instruction address — without recompiling the kernel.

**Key vocabulary**:
- **probe**: a monitoring point inserted into code
- **pre-handler**: function called *before* the probed instruction executes
- **post-handler**: function called *after* the probed instruction executes
- **INT3**: x86 CPU instruction for "breakpoint trap" (opcode `0xCC`)
- **single-step**: executing one CPU instruction at a time

### How kprobes Works — The Mechanism

This is the most important diagram for understanding kprobes:

```
KPROBE INSERTION MECHANISM (x86_64):

BEFORE KPROBE:                    AFTER KPROBE INSERTION:
                                  
  Kernel Code Memory:               Kernel Code Memory:
  ┌──────────────────┐              ┌──────────────────┐
  │  instruction_1   │              │  instruction_1   │
  │  instruction_2   │ ←─ probe     │  0xCC (INT3)     │ ← original byte saved
  │  instruction_3   │   point      │  instruction_3   │   in kprobe struct
  │  instruction_4   │              │  instruction_4   │
  └──────────────────┘              └──────────────────┘
  
EXECUTION FLOW WHEN INT3 HITS:

  CPU executes → hits 0xCC → CPU raises exception (trap)
       ↓
  kernel trap handler catches it
       ↓
  Is this address a registered kprobe? → YES
       ↓
  [1] Save all CPU registers
       ↓
  [2] Call pre_handler(kp, regs)   ← YOUR CODE RUNS HERE
       ↓
  [3] Restore original instruction into a "slot"
       ↓
  [4] Set CPU to single-step mode (TF flag in EFLAGS)
       ↓
  [5] Execute the original instruction
       ↓
  [6] Single-step trap fires
       ↓
  [7] Call post_handler(kp, regs)  ← YOUR CODE RUNS HERE
       ↓
  [8] Resume normal execution at instruction_3
```

### kprobe Optimization — Jump Optimization

```
OPTIMIZED KPROBE (avoids INT3 overhead for hot paths):

BEFORE:                           AFTER OPTIMIZATION:
  instruction_2  (INT3)            instruction_2  (JMP → trampoline)
                                            ↓
                                   [out-of-line trampoline]
                                     pre_handler()
                                     original_instruction
                                     post_handler()
                                     JMP back
                                   
  Cost: ~2ns vs ~20ns for INT3
```

### kprobe Data Structures

```
struct kprobe {
    /* The address to probe */
    kprobe_opcode_t *addr;     /* kernel virtual address */
    const char      *symbol_name; /* OR use symbol name + offset */
    unsigned int     offset;

    /* Handlers */
    kprobe_pre_handler_t  pre_handler;   /* before instruction */
    kprobe_post_handler_t post_handler;  /* after instruction */

    /* Internal state - kernel manages these */
    kprobe_opcode_t  opcode;        /* saved original byte */
    struct arch_specific_insn ainsn;/* saved instruction copy */
    u32 flags;
};
```

### C Implementation — kprobe on `do_sys_open`

```c
// FILE: my_kprobe.c
// PURPOSE: Intercept every open() system call, log filename and PID

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Master");
MODULE_DESCRIPTION("kprobe demo on do_sys_open");

/*
 * TERM: do_sys_open
 *   The internal kernel function called when open()/openat() syscall
 *   is made. Signature (simplified):
 *     long do_sys_open(int dfd, const char __user *filename,
 *                      int flags, umode_t mode);
 *
 * TERM: __user
 *   Annotation meaning the pointer points to USER SPACE memory.
 *   You cannot dereference it directly in kernel space.
 *   You must use copy_from_user() or strncpy_from_user().
 */

/* Pre-handler: called BEFORE do_sys_open executes */
static int handler_pre(struct kprobe *p, struct pt_regs *regs)
{
    /*
     * TERM: pt_regs
     *   Structure holding all CPU registers at the moment of the probe.
     *   On x86_64:
     *     regs->di = first argument  (rdi register)
     *     regs->si = second argument (rsi register)
     *     regs->dx = third argument  (rdx register)
     *     regs->cx = fourth argument (rcx register)
     *
     * For do_sys_open(dfd, filename, flags, mode):
     *   regs->di = dfd      (int: directory file descriptor)
     *   regs->si = filename (const char __user *: path string)
     *   regs->dx = flags    (int: O_RDONLY, O_WRONLY, etc.)
     *   regs->cx = mode     (umode_t: permissions)
     */

    char fname[256];
    const char __user *filename = (const char __user *)regs->si;

    /* 
     * strncpy_from_user: safely copies string from user space
     * Returns number of bytes copied, or negative on error
     */
    long ret = strncpy_from_user(fname, filename, sizeof(fname) - 1);
    if (ret > 0) {
        fname[ret] = '\0';
        pr_info("kprobe: PID=%d comm=%s opening file: %s flags=0x%lx\n",
                current->pid,      /* current: pointer to current task */
                current->comm,     /* comm: process name (max 15 chars) */
                fname,
                regs->dx);
    }

    /* Return 0 to continue normal execution.
     * Return 1 would skip the probed instruction (dangerous!) */
    return 0;
}

/* Post-handler: called AFTER do_sys_open executes */
static void handler_post(struct kprobe *p, struct pt_regs *regs,
                         unsigned long flags)
{
    /*
     * regs->ax on x86_64 is the return value (rax register).
     * Negative values are error codes (e.g., -ENOENT = -2).
     */
    long retval = (long)regs->ax;
    if (retval >= 0)
        pr_info("kprobe post: open succeeded, fd=%ld\n", retval);
    else
        pr_info("kprobe post: open failed, err=%ld\n", retval);
}

/* Define and initialize the kprobe structure */
static struct kprobe kp = {
    .symbol_name = "do_sys_open",   /* probe by symbol name */
    .pre_handler  = handler_pre,
    .post_handler = handler_post,
};

static int __init kprobe_init(void)
{
    int ret;

    /*
     * register_kprobe:
     *   - Resolves symbol_name to a kernel address
     *   - Saves the original byte at that address
     *   - Writes 0xCC (INT3) at that address
     *   - Registers handlers in a hash table
     *
     * Returns 0 on success, negative errno on failure.
     * Common errors:
     *   -EINVAL: address not probeable (e.g., __kprobes annotated)
     *   -ENOENT: symbol not found
     */
    ret = register_kprobe(&kp);
    if (ret < 0) {
        pr_err("register_kprobe failed: %d\n", ret);
        return ret;
    }

    pr_info("kprobe planted at %p (symbol: %s)\n",
            kp.addr, kp.symbol_name);
    return 0;
}

static void __exit kprobe_exit(void)
{
    /*
     * unregister_kprobe:
     *   - Restores the original byte
     *   - Waits for any in-progress handlers to finish
     *   - Removes from hash table
     */
    unregister_kprobe(&kp);
    pr_info("kprobe removed from %p\n", kp.addr);
}

module_init(kprobe_init);
module_exit(kprobe_exit);
```

### kretprobe — Hooking Function Returns

**kretprobe** is a specialized kprobe that intercepts a function's **return**. It does this by temporarily replacing the return address on the stack with a trampoline.

```
KRETPROBE MECHANISM:

  Function call on stack:
  ┌────────────────────┐
  │  return_address    │ ← normally: where caller continues
  │  saved registers   │
  │  local vars...     │
  └────────────────────┘

  With kretprobe:
  ┌────────────────────┐
  │  TRAMPOLINE addr   │ ← replaced by kretprobe
  │  saved registers   │   (original return addr saved internally)
  │  local vars...     │
  └────────────────────┘
  
  When function returns:
    → jumps to TRAMPOLINE
    → kretprobe handler fires (you get return value!)
    → jumps to original return_address
```

```c
// FILE: my_kretprobe.c
// PURPOSE: Measure how long do_sys_open takes (latency profiling)

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>

MODULE_LICENSE("GPL");

/*
 * TERM: instance_data
 *   Per-invocation private data. Since multiple calls can be
 *   in-flight simultaneously (think: SMP systems with many CPUs),
 *   each kretprobe "instance" gets its own private data slot.
 *
 * TERM: SMP (Symmetric Multi-Processing)
 *   System with multiple CPUs. The kernel runs on all CPUs
 *   simultaneously, so your probe handler can be called from
 *   CPU 0, CPU 1, CPU 2... all at the same time.
 */
struct my_data {
    ktime_t entry_stamp;  /* timestamp when function was entered */
};

/* Entry handler: called when function is entered */
static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    /*
     * ri->data: pointer to our per-instance private data
     * We cast it to our struct and record the current time.
     * ktime_get(): returns monotonic time (nanosecond precision)
     */
    struct my_data *data = (struct my_data *)ri->data;
    data->entry_stamp = ktime_get();
    return 0;
}

/* Return handler: called when function is about to return */
static int ret_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    struct my_data *data = (struct my_data *)ri->data;
    ktime_t now  = ktime_get();
    long retval  = regs_return_value(regs); /* portable way to get retval */
    
    /* ktime_to_ns: converts ktime_t to nanoseconds (int64) */
    s64 latency_ns = ktime_to_ns(ktime_sub(now, data->entry_stamp));

    pr_info("kretprobe: do_sys_open took %lld ns, returned fd=%ld\n",
            latency_ns, retval);
    return 0;
}

static struct kretprobe my_kretprobe = {
    .handler      = ret_handler,
    .entry_handler = entry_handler,
    .data_size    = sizeof(struct my_data),  /* allocate per-instance */
    .maxactive    = 20,  /* max simultaneous in-flight instances */
    .kp = {
        .symbol_name = "do_sys_open",
    },
};

static int __init kretprobe_init(void)
{
    int ret = register_kretprobe(&my_kretprobe);
    if (ret < 0) {
        pr_err("register_kretprobe failed: %d\n", ret);
        return ret;
    }
    pr_info("kretprobe planted at %p\n", my_kretprobe.kp.addr);
    return 0;
}

static void __exit kretprobe_exit(void)
{
    unregister_kretprobe(&my_kretprobe);
    pr_info("kretprobe: missed %d instances (maxactive too small)\n",
            my_kretprobe.nmissed);
}

module_init(kretprobe_init);
module_exit(kretprobe_exit);
```

### kprobe Limitations — Know These Cold

```
CANNOT probe:
  ├── Functions marked __kprobes or NOKPROBE_SYMBOL()
  │     (kernel self-protection: probing probe handlers = deadlock)
  ├── Functions inlined by compiler (no stable address)
  ├── kprobe_exceptions_notify() itself
  └── arch-specific exception handling code

RISKS:
  ├── Handler runs in interrupt context (no sleeping!)
  ├── Recursive probing (probing something called by handler)
  ├── Modifying regs incorrectly → instant kernel panic
  └── Not cleaning up on module exit → permanent corruption
```

---

## 5. uprobes — Userspace Probing from the Kernel

### Concept

**uprobes** (userspace probes) let you instrument **user-space executables and libraries** from kernel space. The key insight: the kernel manages the probe, but the probe point is in a user process's code.

**Use cases**:
- Instrument Python/Ruby/Java internals without modifying them
- Trace MySQL query execution
- Profile application hot paths
- Security: detect if a process calls a suspicious library function

```
UPROBE ARCHITECTURE:

  User Space:                         Kernel Space:
  ┌─────────────────────┐             ┌──────────────────────────┐
  │  /usr/bin/python3   │             │  uprobe subsystem        │
  │                     │             │                          │
  │  ...code...         │             │  inode + offset → probe  │
  │  [0xCC] ←───────────┼─────────────┤  registration            │
  │  ...code...         │    page     │                          │
  └─────────────────────┘    fault    │  handler                 │
                             ↕        │                          │
  Process executes → hits 0xCC        │  eBPF program OR        │
  → page fault → kernel handles       │  kernel module handler   │
  → uprobe handler fires              └──────────────────────────┘
  → resume user process
```

### uprobes vs kprobes

```
┌─────────────────┬────────────────────┬────────────────────┐
│ Feature         │ kprobe             │ uprobe             │
├─────────────────┼────────────────────┼────────────────────┤
│ Target          │ kernel code        │ user-space code    │
│ Mechanism       │ INT3 in kernel mem │ INT3 in user pages │
│ Per-process     │ No (system-wide)   │ Yes (per inode)    │
│ Can sleep?      │ No (irq context)   │ Yes (process ctx)  │
│ Access user mem │ with copy_from_user│ direct (same proc) │
│ Overhead        │ ~100-200ns         │ ~200-500ns         │
└─────────────────┴────────────────────┴────────────────────┘
```

### C Implementation — uprobe via debugfs

```c
// FILE: my_uprobe.c
// PURPOSE: Probe a specific offset in /usr/bin/bash

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/uprobes.h>
#include <linux/fs.h>
#include <linux/namei.h>
#include <linux/path.h>

MODULE_LICENSE("GPL");

/*
 * TERM: inode
 *   A kernel data structure representing a file (not its name, but
 *   the file itself). Multiple filenames can refer to the same inode
 *   (hard links). uprobes use inodes to identify WHICH file to probe.
 *
 * TERM: offset
 *   Byte offset within the ELF binary where we insert the probe.
 *   You find this with: objdump -d /usr/bin/bash | grep <function>
 *   Or: nm -D /usr/bin/bash | grep main
 */

static struct uprobe_consumer my_consumer;

/* Called when the probed instruction is about to execute */
static int uprobe_handler(struct uprobe_consumer *con,
                          struct pt_regs *regs)
{
    pr_info("uprobe fired! PID=%d comm=%s IP=0x%lx\n",
            current->pid,
            current->comm,
            instruction_pointer(regs));
    return 0;
}

/* Called when returning from the probed address (like kretprobe) */
static int uretprobe_handler(struct uprobe_consumer *con,
                              unsigned long func,
                              struct pt_regs *regs)
{
    pr_info("uretprobe: PID=%d returned from 0x%lx, retval=%ld\n",
            current->pid,
            func,
            regs_return_value(regs));
    return 0;
}

static struct uprobe_consumer my_consumer = {
    .handler        = uprobe_handler,
    .ret_handler    = uretprobe_handler,
    /* filter: return true to probe this task, false to skip */
    .filter         = uprobe_filter_ctx_is_pid,
};

static struct inode *target_inode;
static loff_t probe_offset = 0x1234; /* replace with actual offset */

static int __init uprobe_init(void)
{
    struct path path;
    int ret;

    /* Look up the inode for the target binary */
    ret = kern_path("/usr/bin/bash", LOOKUP_FOLLOW, &path);
    if (ret) {
        pr_err("cannot find /usr/bin/bash: %d\n", ret);
        return ret;
    }

    target_inode = igrab(path.dentry->d_inode); /* grab inode reference */
    path_put(&path);

    /*
     * uprobe_register:
     *   - Associates probe_offset in target_inode with our consumer
     *   - When any process mmaps this inode and hits probe_offset,
     *     the handler fires
     */
    ret = uprobe_register(target_inode, probe_offset, &my_consumer);
    if (ret) {
        iput(target_inode);
        pr_err("uprobe_register failed: %d\n", ret);
        return ret;
    }

    pr_info("uprobe registered on /usr/bin/bash at offset 0x%llx\n",
            (unsigned long long)probe_offset);
    return 0;
}

static void __exit uprobe_exit(void)
{
    uprobe_unregister(target_inode, probe_offset, &my_consumer);
    iput(target_inode);
    pr_info("uprobe removed\n");
}

module_init(uprobe_init);
module_exit(uprobe_exit);
```

---

## 6. Tracepoints — Static Instrumentation Points

### Concept

**Tracepoints** are **compile-time hooks** placed by kernel developers at strategically important locations. Unlike kprobes (dynamic), tracepoints have a fixed location agreed upon by kernel developers.

**Key vocabulary**:
- **static**: decided at compile time, not runtime
- **TRACE_EVENT**: the macro that defines a tracepoint
- **overhead**: tracepoints have near-zero overhead when disabled (just a branch check)

### Tracepoint vs kprobe

```
TRACEPOINT:
  - Stable API: won't break between kernel versions
  - Near-zero disabled overhead: just `if (unlikely(tracepoint_enabled))`
  - Has defined argument names and types
  - Cannot probe arbitrary addresses

KPROBE:
  - Can probe ANY instruction
  - Slightly more overhead
  - Can break when kernel internals change
  - More powerful but less stable
```

### How Tracepoints Work

```
TRACEPOINT MECHANISM:

  In kernel source (e.g., mm/filemap.c):
  ┌──────────────────────────────────────────────────┐
  │  void do_page_fault(...)                         │
  │  {                                               │
  │      ...                                         │
  │      trace_page_fault_user(address, regs, error) │
  │      /*          ↑                               │
  │       *  This expands to:                        │
  │       *  if (unlikely(__tracepoint_page_fault_   │
  │       *               user.key.enabled)) {       │
  │       *      [call all registered handlers]      │
  │       *  }                                       │
  │       */                                         │
  │      ...                                         │
  │  }                                               │
  └──────────────────────────────────────────────────┘
  
  DISABLED state: just a predictable branch → effectively FREE
  ENABLED state: calls all registered probe functions
```

### The TRACE_EVENT Macro — Anatomy

```c
/*
 * TRACE_EVENT defines three things at once:
 *   1. The tracepoint itself (trace_<name>() function)
 *   2. A print format for tracefs
 *   3. A binary data format for perf
 *
 * Located in: include/trace/events/<subsystem>.h
 */

TRACE_EVENT(sched_switch,
    /*
     * TP_PROTO: the prototype (arguments) of the tracepoint
     * These are the arguments trace_sched_switch() takes
     */
    TP_PROTO(bool preempt,
             struct task_struct *prev,
             struct task_struct *next),

    /*
     * TP_ARGS: the actual argument names (must match TP_PROTO)
     */
    TP_ARGS(preempt, prev, next),

    /*
     * TP_STRUCT__entry: defines what is saved in the ring buffer
     * Each __field and __array declares a member
     */
    TP_STRUCT__entry(
        __array(  char, prev_comm, TASK_COMM_LEN )
        __field(  pid_t, prev_pid  )
        __field(  int, prev_prio   )
        __field(  long, prev_state )
        __array(  char, next_comm, TASK_COMM_LEN )
        __field(  pid_t, next_pid  )
        __field(  int, next_prio   )
    ),

    /*
     * TP_fast_assign: how to populate the ring buffer entry
     * __entry->field accesses the saved data
     */
    TP_fast_assign(
        memcpy(__entry->next_comm, next->comm, TASK_COMM_LEN);
        __entry->prev_pid  = prev->pid;
        __entry->prev_prio = prev->prio;
        __entry->prev_state = __trace_sched_switch_state(preempt, prev);
        memcpy(__entry->prev_comm, prev->comm, TASK_COMM_LEN);
        __entry->next_pid  = next->pid;
        __entry->next_prio = next->prio;
    ),

    /*
     * TP_printk: human-readable format for tracefs/perf output
     */
    TP_printk("prev_comm=%s prev_pid=%d prev_prio=%d prev_state=%s%s ==> "
              "next_comm=%s next_pid=%d next_prio=%d",
              __entry->prev_comm, __entry->prev_pid, __entry->prev_prio,
              ...)
);
```

### Registering a Handler for a Tracepoint (C)

```c
// FILE: my_tracepoint.c
// PURPOSE: Hook into scheduler switch events

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/tracepoint.h>
#include <linux/sched.h>

MODULE_LICENSE("GPL");

/*
 * TERM: tracepoint_ptr_t
 *   A reference to a specific tracepoint. We get this from
 *   for_each_kernel_tracepoint() or directly if we know the name.
 *
 * IMPORTANT: You must hold a reference to the tracepoint structure
 * for the lifetime of your handler registration.
 */

static struct tracepoint *tp_sched_switch;

/* Our handler - matches TP_PROTO of sched_switch */
static void my_sched_switch_probe(void *data,
                                   bool preempt,
                                   struct task_struct *prev,
                                   struct task_struct *next)
{
    /*
     * This runs in scheduler context - we CANNOT sleep,
     * CANNOT call anything that might schedule.
     */
    if (prev->pid != next->pid) {
        pr_info_ratelimited("SWITCH: %s(%d) → %s(%d)\n",
                prev->comm, prev->pid,
                next->comm, next->pid);
        /*
         * TERM: pr_info_ratelimited
         *   Like pr_info() but rate-limited to avoid flooding logs.
         *   The scheduler fires thousands of times per second.
         */
    }
}

/* Callback used to find our tracepoint */
static void find_tracepoint(struct tracepoint *tp, void *priv)
{
    if (!strcmp(tp->name, "sched_switch"))
        tp_sched_switch = tp;
}

static int __init tp_module_init(void)
{
    int ret;

    /*
     * for_each_kernel_tracepoint:
     *   Iterates over ALL tracepoints registered in the kernel.
     *   Calls our callback for each one.
     *   We use it to find sched_switch by name.
     */
    for_each_kernel_tracepoint(find_tracepoint, NULL);

    if (!tp_sched_switch) {
        pr_err("sched_switch tracepoint not found!\n");
        return -ENOENT;
    }

    /*
     * tracepoint_probe_register:
     *   - Registers our handler with the tracepoint
     *   - Handler will be called every time trace_sched_switch() fires
     *   - data parameter is passed to handler as first arg
     */
    ret = tracepoint_probe_register(tp_sched_switch,
                                     my_sched_switch_probe,
                                     NULL /* data */);
    if (ret) {
        pr_err("Failed to register probe: %d\n", ret);
        return ret;
    }

    pr_info("Registered probe on sched_switch\n");
    return 0;
}

static void __exit tp_module_exit(void)
{
    if (tp_sched_switch) {
        tracepoint_probe_unregister(tp_sched_switch,
                                     my_sched_switch_probe,
                                     NULL);
        /*
         * tracepoint_synchronize_unregister:
         *   CRITICAL: Wait for all in-progress invocations to complete.
         *   Without this, the handler might be called AFTER module unload
         *   → crash because module code is gone.
         */
        tracepoint_synchronize_unregister();
    }
    pr_info("Tracepoint probe removed\n");
}

module_init(tp_module_init);
module_exit(tp_module_exit);
```

### Browsing Tracepoints via tracefs

```bash
# Mount tracefs (usually already mounted)
mount -t tracefs nodev /sys/kernel/tracing

# List all available tracepoints
ls /sys/kernel/tracing/events/

# List events in the scheduler subsystem
ls /sys/kernel/tracing/events/sched/

# Enable a specific tracepoint
echo 1 > /sys/kernel/tracing/events/sched/sched_switch/enable

# Read the trace buffer
cat /sys/kernel/tracing/trace

# Format of each tracepoint (metadata)
cat /sys/kernel/tracing/events/sched/sched_switch/format
```

---

## 7. ftrace — The Function Tracer Framework

### Concept

**ftrace** (function tracer) is a kernel tracing framework built on a technique called **function instrumentation**. The compiler inserts a call at the beginning of every function. ftrace hijacks these calls.

**Key vocabulary**:
- **mcount / __fentry__**: stub function call inserted by GCC/Clang at the start of every function
- **NOP sled**: sequence of NOP (no-operation) instructions that can be patched
- **tracer**: a backend that receives ftrace notifications
- **function graph tracer**: traces both entry and exit, showing call graphs

### ftrace Architecture

```
COMPILE-TIME SETUP (when kernel compiled with CONFIG_FUNCTION_TRACER):

  Every function:
  ┌────────────────────────────────────┐
  │  foo:                              │
  │      call __fentry__    ← inserted │
  │      push %rbp          ← original │
  │      mov %rsp, %rbp                │
  │      ...function body...           │
  │      ret                           │
  └────────────────────────────────────┘

RUNTIME (default - no tracing active):
  __fentry__ → immediately returns (NOP-patched by ftrace)
  Overhead: ~1ns (single NOP)

RUNTIME (tracing enabled):
  __fentry__ → ftrace_caller → [your registered ops] → return
```

### ftrace ops — Registering a Function Hook

```c
// FILE: my_ftrace.c
// PURPOSE: Hook every call to 'vfs_read' using ftrace ops

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/ftrace.h>
#include <linux/kallsyms.h>

MODULE_LICENSE("GPL");

/*
 * TERM: ftrace_ops
 *   The structure you register with ftrace. Contains:
 *   - func: your callback
 *   - flags: control behavior
 *
 * TERM: kallsyms_lookup_name
 *   Looks up a kernel symbol by name and returns its address.
 *   Essential for finding function addresses dynamically.
 *
 * TERM: ip (instruction pointer)
 *   The address of the function being called.
 *   In the ftrace callback, 'ip' is the address of the hooked function.
 *
 * TERM: parent_ip
 *   The address of the CALLER of the hooked function.
 *   Lets you know WHO called the function.
 */

static unsigned long target_addr;

static void my_ftrace_callback(unsigned long ip,
                                unsigned long parent_ip,
                                struct ftrace_ops *ops,
                                struct ftrace_regs *fregs)
{
    /*
     * ftrace_regs: wrapper around pt_regs for ftrace context.
     * Use ftrace_regs_get_argument() to get function args.
     * Use ftrace_regs_get_return_value() for return values.
     */
    pr_info_ratelimited("ftrace: %pS called by %pS\n",
                        (void *)ip,
                        (void *)parent_ip);
    /*
     * %pS: kernel pointer formatting specifier that resolves
     *      the address to a symbol+offset string.
     *      e.g., "vfs_read+0x0/0x130"
     */
}

static struct ftrace_ops my_ops = {
    .func  = my_ftrace_callback,
    /*
     * FTRACE_OPS_FL_SAVE_REGS:
     *   Save all CPU registers before calling our callback.
     *   Needed if you want to read/modify function arguments.
     *   Without this, only ip and parent_ip are reliable.
     *
     * FTRACE_OPS_FL_RECURSION:
     *   Prevent recursive callbacks (our handler calling vfs_read
     *   would call our handler again → infinite loop → stack overflow)
     */
    .flags = FTRACE_OPS_FL_SAVE_REGS | FTRACE_OPS_FL_RECURSION,
};

static int __init ftrace_init(void)
{
    int ret;

    /* Find the address of vfs_read */
    target_addr = kallsyms_lookup_name("vfs_read");
    if (!target_addr) {
        pr_err("Cannot find vfs_read symbol\n");
        return -ENOENT;
    }

    /*
     * ftrace_set_filter_ip:
     *   Tells ftrace to ONLY call our ops when 'target_addr' is entered.
     *   Without this filter, our callback fires on EVERY function call
     *   (extremely expensive).
     *
     *   Parameters:
     *     ops:    our ftrace_ops
     *     ip:     address to add to filter
     *     remove: 0 = add, 1 = remove
     *     reset:  1 = clear existing filter first
     */
    ret = ftrace_set_filter_ip(&my_ops, target_addr, 0, 0);
    if (ret) {
        pr_err("ftrace_set_filter_ip failed: %d\n", ret);
        return ret;
    }

    /*
     * register_ftrace_function:
     *   Activates our ops. From now on, every call to vfs_read
     *   will invoke my_ftrace_callback.
     */
    ret = register_ftrace_function(&my_ops);
    if (ret) {
        pr_err("register_ftrace_function failed: %d\n", ret);
        return ret;
    }

    pr_info("ftrace hook registered on vfs_read at %lx\n", target_addr);
    return 0;
}

static void __exit ftrace_exit(void)
{
    unregister_ftrace_function(&my_ops);
    /*
     * ftrace_set_filter_ip with remove=1:
     *   Clean up the filter. Always clean up to avoid memory leaks.
     */
    ftrace_set_filter_ip(&my_ops, target_addr, 1, 0);
    pr_info("ftrace hook removed\n");
}

module_init(ftrace_init);
module_exit(ftrace_exit);
```

### ftrace-based Function Hooking (Syscall Hijacking Pattern)

This is the **most common pattern** for rootkits and security tools — replacing a kernel function pointer.

```c
// FILE: ftrace_hook.c
// PATTERN: Using ftrace to redirect execution to our function

#include <linux/ftrace.h>
#include <linux/kallsyms.h>
#include <linux/kernel.h>
#include <linux/linkage.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/version.h>

MODULE_LICENSE("GPL");

/*
 * PATTERN EXPLANATION:
 *
 * Goal: Replace vfs_read with our_vfs_read.
 * When code calls vfs_read(), our function runs first.
 * We can then call the original or block it.
 *
 * The trick: We use ftrace to intercept the call,
 * then modify the return address on the stack so execution
 * jumps to OUR function instead.
 *
 *                  caller
 *                    │
 *                    ↓ calls vfs_read
 *           [ftrace intercepts at __fentry__]
 *                    │
 *                    ↓ our ftrace_ops callback
 *           [modify instruction pointer]
 *                    │
 *                    ↓ CPU jumps to our_vfs_read instead!
 *             our_vfs_read() runs
 *                    │
 *                    ↓ we call original_vfs_read if desired
 *            original vfs_read() runs
 */

/* Typedef matching vfs_read's signature */
typedef ssize_t (*vfs_read_t)(struct file *, char __user *,
                               size_t, loff_t *);

static vfs_read_t original_vfs_read;

/* Our replacement function */
static ssize_t our_vfs_read(struct file *file,
                             char __user *buf,
                             size_t count,
                             loff_t *pos)
{
    ssize_t ret;

    pr_info("our_vfs_read: intercepted! file=%s count=%zu\n",
            file->f_path.dentry->d_name.name,
            count);

    /* Call the original function */
    ret = original_vfs_read(file, buf, count, pos);

    pr_info("our_vfs_read: original returned %zd\n", ret);
    return ret;
}

#define HOOK(_name, _hook, _orig)   \
{                                    \
    .name  = (_name),                \
    .function = (_hook),             \
    .original = (_orig),             \
}

struct ftrace_hook {
    const char *name;
    void *function;
    void *original;

    unsigned long address;
    struct ftrace_ops ops;
};

static void notrace hook_ftrace_callback(unsigned long ip,
                                          unsigned long parent_ip,
                                          struct ftrace_ops *ops,
                                          struct ftrace_regs *fregs)
{
    struct ftrace_hook *hook = container_of(ops, struct ftrace_hook, ops);

    /*
     * container_of(ptr, type, member):
     *   Given a pointer to a MEMBER of a struct, derive the pointer
     *   to the CONTAINING struct.
     *   Here: ops is the .ops field of ftrace_hook, so we get ftrace_hook*.
     */

    /* Only redirect if caller is not our function (prevent recursion) */
    if (!within_module(parent_ip, THIS_MODULE)) {
        /*
         * ftrace_regs_get_instruction_pointer / set:
         *   Change where execution will go after ftrace returns.
         *   By setting IP to our function, the CPU will execute
         *   our function instead of the original.
         */
        ftrace_regs_set_instruction_pointer(fregs,
                    (unsigned long)hook->function);
    }
}

static int hook_install(struct ftrace_hook *hook)
{
    int ret;

    hook->address = kallsyms_lookup_name(hook->name);
    if (!hook->address) {
        pr_err("Cannot find %s\n", hook->name);
        return -ENOENT;
    }

    /* Store original function address so our hook can call it */
    *((unsigned long *)hook->original) = hook->address;

    hook->ops.func  = hook_ftrace_callback;
    hook->ops.flags = FTRACE_OPS_FL_SAVE_REGS
                    | FTRACE_OPS_FL_SAVE_REGS_IF_SUPPORTED
                    | FTRACE_OPS_FL_RECURSION;

    ret = ftrace_set_filter_ip(&hook->ops, hook->address, 0, 0);
    if (ret) return ret;

    return register_ftrace_function(&hook->ops);
}

static struct ftrace_hook hooks[] = {
    HOOK("vfs_read", our_vfs_read, &original_vfs_read),
};

static int __init hook_init(void)
{
    return hook_install(&hooks[0]);
}

static void __exit hook_exit(void)
{
    unregister_ftrace_function(&hooks[0].ops);
    /* synchronize: wait for in-progress callbacks */
    synchronize_rcu();
}

module_init(hook_init);
module_exit(hook_exit);
```

---

## 8. eBPF — The Universal Hook Platform

### What is eBPF?

**eBPF** (extended Berkeley Packet Filter) is arguably the most important advancement in Linux observability and security in the past decade. It allows running **sandboxed programs inside the kernel** — programs that are verified to be safe before execution.

**Key vocabulary**:
- **BPF bytecode**: a RISC-like instruction set that eBPF programs are compiled to
- **BPF verifier**: a kernel component that exhaustively checks BPF programs for safety before loading
- **BPF map**: a key-value store shared between BPF programs and userspace
- **BPF helper**: kernel-provided functions that BPF programs can call
- **BTF** (BPF Type Format): debug info embedded in the kernel, enabling CO-RE
- **CO-RE** (Compile Once, Run Everywhere): write BPF once, runs on different kernel versions

### eBPF Architecture — Complete View

```
╔═══════════════════════════════════════════════════════════════════╗
║                     eBPF COMPLETE ARCHITECTURE                    ║
║                                                                   ║
║  USER SPACE                                                       ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  Your Tool (written in C, Go, Rust, Python...)              │  ║
║  │                                                             │  ║
║  │  [Load BPF program] ──── bpf() syscall ──────────────────┐  │  ║
║  │  [Read BPF maps]    ──── bpf() syscall ─────────────────┐│  │  ║
║  └────────────────────────────────────────────────────┬────┼┼──┘  ║
║                                                       │    ││     ║
║  ═════════════════════════════════════════════════════╪════╪╪═══  ║
║                        KERNEL SPACE                   │    ││     ║
║                                                       │    ││     ║
║  ┌──────────────────────────────────────────────────┐ │    ││     ║
║  │               BPF SUBSYSTEM                      │ │    ││     ║
║  │                                                  │ │    ││     ║
║  │  ┌──────────────┐    ┌──────────────────────┐    │←┘    ││     ║
║  │  │  BPF Loader  │    │    BPF Verifier       │    │      ││     ║
║  │  │              │───►│  - bounds checking    │    │      ││     ║
║  │  │  Parse ELF   │    │  - memory safety      │    │      ││     ║
║  │  │  bytecode    │    │  - loop termination   │    │      ││     ║
║  │  └──────────────┘    │  - pointer tracking   │    │      ││     ║
║  │                      └──────────┬────────────┘    │      ││     ║
║  │                                 │ verified         │      ││     ║
║  │                                 ↓                  │      ││     ║
║  │                      ┌──────────────────────┐      │      ││     ║
║  │                      │    JIT Compiler       │      │      ││     ║
║  │                      │  BPF bytecode →       │      │      ││     ║
║  │                      │  native machine code  │      │      ││     ║
║  │                      └──────────┬────────────┘      │      ││     ║
║  │                                 │                   │      ││     ║
║  │  ┌──────────────────────────────┼───────────────┐   │      ││     ║
║  │  │         BPF MAPS (shared storage)            │◄──┼──────┘│     ║
║  │  │  hash_map, array, ringbuf, LRU, percpu...    │   │       │     ║
║  │  └──────────────────────────────────────────────┘   │       │     ║
║  └──────────────────────────────────────────────────────┘       │     ║
║                                                                  │     ║
║  ATTACHMENT POINTS (hooks):                                      │     ║
║  ┌───────────────────────────────────────────────────────────┐   │     ║
║  │                                                           │◄──┘     ║
║  │  kprobe/kretprobe ─── attach BPF to any kernel function  │         ║
║  │  uprobe/uretprobe ─── attach BPF to userspace functions  │         ║
║  │  tracepoints      ─── attach BPF to trace_* calls        │         ║
║  │  fentry/fexit     ─── BTF-based function entry/exit      │         ║
║  │  XDP              ─── eXpress Data Path (NIC driver)     │         ║
║  │  TC ingress/egress─── traffic control hooks              │         ║
║  │  socket filter    ─── filter socket traffic              │         ║
║  │  cgroup/skb       ─── cgroup-level network control       │         ║
║  │  LSM              ─── security enforcement               │         ║
║  │  perf event       ─── CPU/hardware events                │         ║
║  └───────────────────────────────────────────────────────────┘         ║
╚═══════════════════════════════════════════════════════════════════╝
```

### BPF Map Types — The Shared Data Store

```
BPF MAP TYPES:
  
  BPF_MAP_TYPE_HASH          key/value hash table (variable size)
  BPF_MAP_TYPE_ARRAY         integer-indexed array (fixed size)
  BPF_MAP_TYPE_RINGBUF       lock-free ring buffer (kernel → user)
  BPF_MAP_TYPE_PERF_EVENT_ARRAY  perf ring buffer (older)
  BPF_MAP_TYPE_PERCPU_HASH   per-CPU hash (no lock contention)
  BPF_MAP_TYPE_PERCPU_ARRAY  per-CPU array
  BPF_MAP_TYPE_LRU_HASH      hash with LRU eviction
  BPF_MAP_TYPE_STACK_TRACE   stack traces
  BPF_MAP_TYPE_CGROUP_ARRAY  cgroup references
  BPF_MAP_TYPE_PROG_ARRAY    tail call table (jump to other BPF prog)
  BPF_MAP_TYPE_QUEUE         FIFO queue
  BPF_MAP_TYPE_STACK         LIFO stack
  BPF_MAP_TYPE_BLOOM_FILTER  probabilistic membership test
```

### eBPF C Implementation — tracepoint program

```c
// FILE: trace_open.bpf.c
// PURPOSE: eBPF program to trace open() calls with filename
// COMPILED WITH: clang -O2 -g -target bpf -c trace_open.bpf.c

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/types.h>

/*
 * TERM: SEC("...") macro
 *   Places the function into a specific ELF section.
 *   The loader reads section names to know what type of BPF
 *   program this is and where to attach it.
 *
 *   "tp/syscalls/sys_enter_openat" means:
 *     tp         = tracepoint
 *     syscalls   = event category
 *     sys_enter_openat = specific event (openat syscall entry)
 */

/*
 * TERM: __always_inline
 *   Forces the compiler to inline this function.
 *   BPF programs cannot call non-inlined functions (before BPF subprog support).
 */

/* Define our event structure - what we'll send to userspace */
struct event {
    __u32 pid;
    __u32 uid;
    char  comm[16];      /* process name */
    char  filename[256]; /* file being opened */
};

/*
 * TERM: BPF_MAP_DEF or struct { ... } __maps section
 *   Modern BTF-based map definition.
 *   The kernel reads BTF to understand map type/size/key/value.
 */

/* Ring buffer map: kernel → userspace event stream */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);  /* 256KB ring buffer */
} events SEC(".maps");

/*
 * SEC("tp/syscalls/sys_enter_openat"):
 *   Attaches to the tracepoint for openat() syscall entry.
 *   The function receives the tracepoint arguments.
 *
 * struct trace_event_raw_sys_enter:
 *   Auto-generated structure from BTF for the sys_enter tracepoint.
 *   Contains: id (syscall number), args[6] (syscall arguments)
 */
SEC("tp/syscalls/sys_enter_openat")
int trace_openat(struct trace_event_raw_sys_enter *ctx)
{
    struct event *e;
    const char *filename_ptr;

    /*
     * bpf_ringbuf_reserve:
     *   Reserves space in the ring buffer for ONE event.
     *   Returns NULL if ring buffer is full (drop the event).
     *   This is a zero-copy operation: we write directly into
     *   the ring buffer memory.
     */
    e = bpf_ringbuf_reserve(&events, sizeof(struct event), 0);
    if (!e)
        return 0;  /* ring buffer full, drop event */

    /* Populate event fields */
    e->pid = bpf_get_current_pid_tgid() >> 32;  /* upper 32 bits = PID */
    e->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF; /* lower 32 = UID */
    bpf_get_current_comm(e->comm, sizeof(e->comm));

    /*
     * ctx->args[1] = second argument to openat = filename pointer
     *   openat(dirfd, pathname, flags, mode)
     *         arg[0]  arg[1]   arg[2]  arg[3]
     *
     * IMPORTANT: ctx->args[1] is a USER SPACE pointer.
     * We must use bpf_probe_read_user_str() to safely read it.
     * Direct dereference would crash (or be blocked by verifier).
     */
    filename_ptr = (const char *)(unsigned long)ctx->args[1];
    bpf_probe_read_user_str(e->filename, sizeof(e->filename), filename_ptr);

    /*
     * bpf_ringbuf_submit:
     *   Makes the reserved entry visible to userspace consumers.
     *   After this call, e is no longer accessible from BPF side.
     */
    bpf_ringbuf_submit(e, 0);
    return 0;
}

/* Required license declaration - must be GPL for most helpers */
char LICENSE[] SEC("license") = "GPL";
```

```c
// FILE: trace_open_user.c
// PURPOSE: Userspace program to load BPF and read events

#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <bpf/libbpf.h>
#include "trace_open.skel.h"  /* auto-generated by bpftool skeleton */

/*
 * TERM: skeleton
 *   Auto-generated C code that embeds your BPF object file and
 *   provides typed C functions to load/attach/manage it.
 *   Generated by: bpftool gen skeleton trace_open.bpf.o > trace_open.skel.h
 */

struct event {
    unsigned int pid;
    unsigned int uid;
    char comm[16];
    char filename[256];
};

static volatile bool running = true;

/* Ring buffer callback - called for each event */
static int handle_event(void *ctx, void *data, size_t size)
{
    struct event *e = data;
    printf("PID=%-6u UID=%-6u COMM=%-16s FILE=%s\n",
           e->pid, e->uid, e->comm, e->filename);
    return 0;
}

int main(void)
{
    struct trace_open_bpf *skel;
    struct ring_buffer *rb;
    int err;

    /*
     * trace_open_bpf__open_and_load():
     *   1. Opens the embedded BPF object (ELF parsing)
     *   2. Loads all maps into the kernel
     *   3. Verifies all BPF programs
     *   4. JIT compiles all programs
     */
    skel = trace_open_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open/load BPF skeleton\n");
        return 1;
    }

    /*
     * trace_open_bpf__attach():
     *   Attaches all BPF programs to their respective hooks.
     *   For our program: attaches to tracepoint sys_enter_openat.
     */
    err = trace_open_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF: %d\n", err);
        trace_open_bpf__destroy(skel);
        return 1;
    }

    /*
     * ring_buffer__new():
     *   Creates a ring buffer consumer.
     *   Maps the ring buffer memory from kernel → userspace (mmap).
     */
    rb = ring_buffer__new(bpf_map__fd(skel->maps.events),
                          handle_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "Failed to create ring buffer\n");
        trace_open_bpf__destroy(skel);
        return 1;
    }

    printf("Tracing openat() calls... Ctrl+C to stop.\n");

    while (running) {
        /*
         * ring_buffer__poll:
         *   Polls for new events, calls handle_event for each.
         *   Timeout: 100ms (so we can check 'running' flag).
         */
        err = ring_buffer__poll(rb, 100);
        if (err < 0 && err != -EINTR)
            break;
    }

    ring_buffer__free(rb);
    trace_open_bpf__destroy(skel);
    return 0;
}
```

### eBPF Verifier — The Safety Guardian

```
BPF VERIFIER CHECKS:

  ┌─────────────────────────────────────────────────────────┐
  │  1. PROGRAM SIZE: max 1M instructions (increased over   │
  │     kernel versions; was 4096 originally)               │
  │                                                         │
  │  2. NO UNBOUNDED LOOPS: every loop must be bounded      │
  │     (verifier tracks iteration count)                   │
  │                                                         │
  │  3. MEMORY SAFETY:                                      │
  │     - All pointer accesses bounds-checked               │
  │     - No reading uninitialized memory                   │
  │     - Stack depth limited to 512 bytes                  │
  │                                                         │
  │  4. POINTER ARITHMETIC:                                 │
  │     - Tracked with types (PTR_TO_MAP_VALUE, etc.)       │
  │     - Adding integer to pointer: new type computed      │
  │     - NULL pointer never dereferenced                   │
  │                                                         │
  │  5. HELPER CALL SAFETY:                                 │
  │     - Only whitelisted helpers callable                 │
  │     - Return values tracked for NULL checks             │
  │                                                         │
  │  6. RETURN VALUE: must return a valid value             │
  └─────────────────────────────────────────────────────────┘
```

---

## 9. LSM Hooks — Linux Security Module Framework

### Concept

**LSM** (Linux Security Module) is a framework that allows multiple security modules to hook into security-critical kernel operations. **SELinux**, **AppArmor**, **Smack**, **TOMOYO**, and **Yama** are all implemented as LSM modules.

**Key vocabulary**:
- **MAC** (Mandatory Access Control): access control enforced by the kernel, not the user
- **DAC** (Discretionary Access Control): traditional Unix permissions (user-controlled)
- **hook point**: a specific security decision the kernel makes (e.g., "should process X be allowed to read file Y?")
- **security context**: a label attached to processes and objects

### LSM Architecture

```
SECURITY DECISION FLOW:

  Process calls open("/etc/shadow", O_RDONLY)
         │
         ↓
  VFS layer checks:
    1. DAC checks (Unix permissions: uid/gid/mode)
         │ passes
         ↓
    2. LSM hook: security_inode_open()
         │
         ├── SELinux checks policy
         │     └── DENY? → return -EACCES
         │
         ├── AppArmor checks profile
         │     └── DENY? → return -EACCES
         │
         └── all modules allow → open proceeds
         
  HOOK COMPOSITION:
    All registered LSMs are called in order.
    ANY module can deny access.
    If ALL allow, access is granted.
```

### LSM Hook Locations in Kernel Source

```
LSM hooks are defined in: include/linux/lsm_hooks.h
Called from:
  fs/namei.c         → inode hooks (file access)
  kernel/fork.c      → task hooks (process creation)
  net/socket.c       → socket hooks (network)
  ipc/msg.c          → IPC hooks (message queues)
  security/security.c → hook dispatcher
```

### Complete LSM Module Implementation (C)

```c
// FILE: my_lsm.c
// PURPOSE: A simple LSM that logs and potentially blocks file access

#include <linux/lsm_hooks.h>
#include <linux/security.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/dcache.h>
#include <linux/cred.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Master");
MODULE_DESCRIPTION("Demo LSM module");

/*
 * TERM: inode_permission hook
 *   Called every time the kernel is about to check if a process
 *   has permission to access an inode (file, directory, symlink...).
 *
 * Parameters:
 *   inode: the file system object being accessed
 *   mask:  requested access (MAY_READ, MAY_WRITE, MAY_EXEC, MAY_APPEND)
 *
 * Return:
 *   0 to allow, negative errno to deny.
 */
static int my_inode_permission(struct inode *inode, int mask)
{
    struct dentry *dentry;
    char buf[256];
    char *path;

    /*
     * d_find_alias: finds a dentry (directory entry) for this inode.
     * A dentry connects an inode to its filename in a directory tree.
     * Returns NULL if none (unlikely for a living inode).
     */
    dentry = d_find_alias(inode);
    if (!dentry)
        return 0;

    /*
     * dentry_path_raw: builds the full path string into buf.
     * Returns pointer into buf where path starts (may not be buf[0]
     * since it builds from the end).
     */
    path = dentry_path_raw(dentry, buf, sizeof(buf));
    dput(dentry);  /* release dentry reference */

    if (IS_ERR(path))
        return 0;

    /* Example policy: block writes to anything in /etc/ */
    if ((mask & MAY_WRITE) && strnstr(path, "/etc/", 256)) {
        pr_warn("LSM: BLOCKED write to %s by PID=%d comm=%s\n",
                path, current->pid, current->comm);
        return -EACCES;  /* deny with "permission denied" */
    }

    /* Log reads to sensitive files */
    if ((mask & MAY_READ) && strnstr(path, "/etc/shadow", 256)) {
        pr_warn("LSM: ALERT /etc/shadow read attempt by PID=%d comm=%s\n",
                current->pid, current->comm);
        /* Allow but logged */
    }

    return 0;  /* allow */
}

/*
 * TERM: bprm_check_security
 *   Called when the kernel is about to exec() a new binary.
 *   'bprm' = binary parameters (contains path, credentials, etc.)
 *
 * This is the hook used by SELinux/AppArmor to enforce exec policies.
 */
static int my_bprm_check_security(struct linux_binprm *bprm)
{
    pr_info("LSM: exec attempt: %s by PID=%d\n",
            bprm->filename, current->pid);

    /* Block execution of files from /tmp (common attack vector) */
    if (strncmp(bprm->filename, "/tmp/", 5) == 0) {
        pr_warn("LSM: BLOCKED exec from /tmp: %s\n", bprm->filename);
        return -EPERM;
    }

    return 0;
}

/*
 * TERM: socket_connect hook
 *   Called before a socket connect() is completed.
 *   'sock': the socket
 *   'address': destination address (struct sockaddr)
 *   'addrlen': length of address
 */
static int my_socket_connect(struct socket *sock,
                              struct sockaddr *address,
                              int addrlen)
{
    /* Could check destination IP/port here */
    pr_info_ratelimited("LSM: PID=%d comm=%s connecting socket\n",
                        current->pid, current->comm);
    return 0;
}

/*
 * struct security_hook_list:
 *   Each element pairs an LSM hook function with the hook it implements.
 *   The LSM_HOOK_INIT macro fills in the hook structure.
 */
static struct security_hook_list my_hooks[] __lsm_ro_after_init = {
    LSM_HOOK_INIT(inode_permission,  my_inode_permission),
    LSM_HOOK_INIT(bprm_check_security, my_bprm_check_security),
    LSM_HOOK_INIT(socket_connect,    my_socket_connect),
};

/*
 * TERM: __init
 *   Function called once during kernel/module initialization.
 *   Memory used by __init functions is freed after init completes.
 *
 * NOTE: LSMs typically cannot be loaded as modules in production
 * (security_add_hooks is called at boot). This demo simplifies this.
 * Real LSMs use: DEFINE_LSM() macro or CONFIG_LSM_MUTABLE.
 */
static int __init my_lsm_init(void)
{
    /*
     * security_add_hooks:
     *   Registers our hook functions with the LSM framework.
     *   After this, every security decision goes through our hooks.
     */
    security_add_hooks(my_hooks, ARRAY_SIZE(my_hooks), "my_lsm");
    pr_info("my_lsm: initialized, %zu hooks registered\n",
            ARRAY_SIZE(my_hooks));
    return 0;
}

/* Modern LSMs use DEFINE_LSM macro instead of module_init */
/* For loadable module demo: */
module_init(my_lsm_init);
/* Real LSMs: DEFINE_LSM(my_lsm) = { .init = my_lsm_init, .name = "my_lsm" }; */
```

### Complete LSM Hook Reference (Major Categories)

```
TASK/PROCESS HOOKS:
  cred_prepare          → before forking credentials
  task_create           → before fork() creates new task
  task_kill             → before sending signal
  task_setuid           → before setuid()
  bprm_check_security   → before exec()
  bprm_committed_creds  → after exec() credentials committed

FILE/INODE HOOKS:
  inode_permission      → access permission check
  inode_create          → before creating file
  inode_unlink          → before unlinking (deleting) file
  inode_rename          → before rename
  inode_setattr         → before chmod/chown/truncate
  inode_getxattr        → before reading extended attribute
  inode_setxattr        → before writing extended attribute
  file_open             → when file descriptor is opened
  file_permission       → read/write/exec permission on open fd
  file_ioctl            → before ioctl() on file

NETWORK HOOKS:
  socket_create         → before socket() syscall
  socket_connect        → before connect()
  socket_bind           → before bind()
  socket_listen         → before listen()
  socket_accept         → before accept()
  socket_sendmsg        → before send/sendto/sendmsg
  socket_recvmsg        → before recv/recvfrom/recvmsg
  sk_alloc              → new socket kernel object
  inet_conn_request     → incoming TCP SYN

IPC HOOKS:
  msg_queue_msgsnd      → before sending IPC message
  msg_queue_msgrcv      → before receiving IPC message
  shm_shmat             → before shared memory attach

SYSTEM HOOKS:
  capable               → before checking CAP_* capabilities
  settime               → before setting system time
  syslog                → before reading kernel log
  vm_enough_memory      → before memory overcommit
```

---

## 10. Netfilter Hooks — Network Stack Interception

### Concept

**Netfilter** is the Linux kernel's network packet filtering framework. It defines **hook points** in the network stack where external code (modules, eBPF programs) can inspect, modify, drop, or redirect packets.

**iptables**, **nftables**, **conntrack**, and **NAT** are all built on Netfilter hooks.

**Key vocabulary**:
- **packet**: a unit of network data (IP datagram)
- **hook point**: a specific location in the packet processing path
- **verdict**: the decision about what to do with a packet (ACCEPT, DROP, QUEUE, etc.)
- **priority**: order in which multiple handlers at the same hook are called
- **conntrack**: connection tracking — remembering state of ongoing connections

### Netfilter Hook Points

```
PACKET FLOW THROUGH NETFILTER HOOKS:

INCOMING PACKET (from network interface):

  NIC receives packet
       │
       ↓
  [NF_INET_PRE_ROUTING]  ← Hook 0: first chance to see/drop packet
       │                    (before routing decision)
       │
       ↓ routing decision
      ╱╲
     ╱  ╲
    ╱    ╲ Is destination THIS machine?
   ╱      ╲
  YES      NO
   │        │
   ↓        ↓
[NF_INET_ [NF_INET_FORWARD]  ← Hook 2: forwarded packets
 LOCAL_IN]  │                   (for routers/NAT)
 ← Hook 1   │
   │       [NF_INET_POST_ROUTING] ← Hook 4: last hook before
   │         │                      packet leaves machine
   ↓         ↓
  Local     Network Interface → wire
  Process

OUTGOING PACKET (from local process):

  Process calls send()/write()
       │
       ↓
  [NF_INET_LOCAL_OUT]    ← Hook 3: locally generated packets
       │
       ↓ routing decision
       │
  [NF_INET_POST_ROUTING] ← Hook 4: final hook
       │
       ↓
  Network Interface → wire
```

### Verdicts — What To Do With a Packet

```
NF_ACCEPT   → let the packet continue through the stack
NF_DROP     → silently discard the packet
NF_STOLEN   → handler takes ownership, no further processing
NF_QUEUE    → queue packet to userspace (for nfqueue)
NF_REPEAT   → call this hook again
NF_STOP     → stop processing (like ACCEPT but stops all hooks)
```

### C Implementation — Netfilter Hook Module

```c
// FILE: my_netfilter.c
// PURPOSE: Drop all ICMP echo-request (ping) packets

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/in.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Master");
MODULE_DESCRIPTION("Netfilter hook: block ICMP pings");

/*
 * TERM: struct iphdr
 *   The IPv4 header structure. Key fields:
 *   .protocol: which L4 protocol (IPPROTO_TCP=6, IPPROTO_UDP=17,
 *              IPPROTO_ICMP=1)
 *   .saddr: source IP address (network byte order)
 *   .daddr: destination IP address (network byte order)
 *   .ihl: IP header length in 32-bit words (multiply by 4 for bytes)
 *
 * TERM: struct icmphdr
 *   ICMP header. Key field:
 *   .type: ICMP_ECHO=8 (ping request), ICMP_ECHOREPLY=0 (ping reply)
 *
 * TERM: sk_buff (skb)
 *   "Socket buffer" — the kernel's representation of a network packet.
 *   Contains: packet data, metadata, pointers to header regions.
 *   skb->data points to the start of the current header.
 *   ip_hdr(skb): returns pointer to IP header within skb.
 */

/*
 * The hook function:
 *   Called for every packet at our registered hook point.
 *   Must return a netfilter verdict.
 *
 * Parameters:
 *   priv:     our private data (NULL here)
 *   skb:      the packet (socket buffer)
 *   state:    hook state (contains in/out interfaces, hook number)
 */
static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct icmphdr *icmph;

    /* Sanity check: packet must exist */
    if (!skb)
        return NF_ACCEPT;

    /* Get pointer to IP header */
    iph = ip_hdr(skb);
    if (!iph)
        return NF_ACCEPT;

    /* Only care about ICMP */
    if (iph->protocol != IPPROTO_ICMP)
        return NF_ACCEPT;

    /*
     * skb_transport_header:
     *   Returns pointer to transport layer header (ICMP in this case).
     *   The kernel sets this pointer during packet parsing.
     *   ihl * 4 = IP header size in bytes.
     */
    icmph = (struct icmphdr *)(skb_transport_header(skb));

    /* Drop echo requests (pings) */
    if (icmph->type == ICMP_ECHO) {
        /*
         * %pI4: printk format for IPv4 address.
         *   &iph->saddr → "192.168.1.100"
         */
        pr_info("netfilter: DROPPING ping from %pI4 to %pI4\n",
                &iph->saddr, &iph->daddr);
        return NF_DROP;
    }

    /* Allow everything else */
    return NF_ACCEPT;
}

/*
 * struct nf_hook_ops: defines where and how to attach our hook
 */
static struct nf_hook_ops my_nf_ops = {
    .hook     = my_hook_fn,
    /*
     * pf: protocol family
     *   PF_INET  = IPv4
     *   PF_INET6 = IPv6
     *   NFPROTO_NETDEV = device level (XDP-like)
     */
    .pf       = PF_INET,
    /*
     * hooknum: which hook point (NF_INET_PRE_ROUTING = 0, etc.)
     * We use PRE_ROUTING to catch packets before routing decision.
     */
    .hooknum  = NF_INET_PRE_ROUTING,
    /*
     * priority: when multiple handlers are registered for the same hook,
     * lower numbers fire FIRST.
     * NF_IP_PRI_FIRST = INT_MIN (very early)
     * NF_IP_PRI_FILTER = 0 (iptables filter table priority)
     * NF_IP_PRI_NAT_SRC = 100 (SNAT)
     * NF_IP_PRI_LAST = INT_MAX (very late)
     */
    .priority = NF_IP_PRI_FIRST,
};

static int __init nf_module_init(void)
{
    int ret;

    /*
     * nf_register_net_hook:
     *   Registers hook in the NETWORK NAMESPACE.
     *   &init_net: the initial/default network namespace.
     *   (Containers use separate network namespaces.)
     */
    ret = nf_register_net_hook(&init_net, &my_nf_ops);
    if (ret) {
        pr_err("nf_register_net_hook failed: %d\n", ret);
        return ret;
    }

    pr_info("netfilter hook registered: blocking ICMP echo requests\n");
    return 0;
}

static void __exit nf_module_exit(void)
{
    nf_unregister_net_hook(&init_net, &my_nf_ops);
    pr_info("netfilter hook removed\n");
}

module_init(nf_module_init);
module_exit(nf_module_exit);
```

### Advanced: Packet Modification in Netfilter

```c
/*
 * EXAMPLE: Modify destination IP (simple NAT-like behavior)
 * Called from within the hook function.
 */
static unsigned int redirect_hook(void *priv,
                                   struct sk_buff *skb,
                                   const struct nf_hook_state *state)
{
    struct iphdr *iph;
    __be32 new_dst = in_aton("10.0.0.1");  /* new destination */

    iph = ip_hdr(skb);
    if (!iph || iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;

    /* Modify destination IP */
    iph->daddr = new_dst;

    /*
     * ip_send_check: recalculate IP checksum after modification.
     * CRITICAL: if you modify IP header, YOU MUST recalculate checksum.
     * Wrong checksum → packet silently dropped by receiving host.
     */
    ip_send_check(iph);

    /*
     * skb_make_writable: ensure skb data is writable.
     * skbs may share underlying data (copy-on-write).
     * This ensures we have our own copy before modifying.
     */
    if (!skb_make_writable(skb, sizeof(struct iphdr)))
        return NF_DROP;

    return NF_ACCEPT;
}
```

---

## 11. Syscall Hooks — System Call Interception

### Concept

**System calls** are the interface between user space and the kernel. Every time a program calls `open()`, `read()`, `write()`, `fork()`, etc., it goes through the syscall interface.

**Key vocabulary**:
- **syscall table**: an array of function pointers, indexed by syscall number
- **sys_call_table**: the kernel symbol name for this array
- **NR_open**: the syscall number for open (varies by architecture)
- **write-protect**: x86 has a WP bit in CR0 register that prevents kernel from writing to read-only pages

### Syscall Table Architecture

```
SYSCALL FLOW ON x86_64:

  User:  syscall instruction (or int 0x80 on i386)
    │
    │ CPU switches to kernel mode
    ↓
  entry_SYSCALL_64()   ← assembly entry point in entry_64.S
    │
    ↓
  do_syscall_64()
    │
    ↓  rax = syscall number (e.g., rax=0 for read, rax=2 for open)
  sys_call_table[rax]  ← index into function pointer table
    │
    ↓
  sys_openat()         ← actual syscall implementation
    │
    ↓
  returns to user space

SYSCALL TABLE (simplified):
  Index  │ Symbol Name      │ C Function
  ───────┼──────────────────┼────────────────────
    0    │ __NR_read        │ sys_read()
    1    │ __NR_write       │ sys_write()
    2    │ __NR_open        │ sys_open()
    3    │ __NR_close       │ sys_close()
    4    │ __NR_stat        │ sys_stat()
   ...   │ ...              │ ...
   257   │ __NR_openat      │ sys_openat()
   ...   │ ...              │ ...
```

### Syscall Hooking via Table Modification (C)

```c
// FILE: syscall_hook.c
// PURPOSE: Hook the openat() syscall
// WARNING: Modifying sys_call_table is dangerous and may be
//          detected by security tools. Educational purposes only.

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/syscalls.h>
#include <linux/kallsyms.h>
#include <linux/uaccess.h>
#include <asm/paravirt.h>  /* for write_cr0() */

MODULE_LICENSE("GPL");

/* Pointer to the syscall table */
static unsigned long *syscall_table;

/*
 * TERM: sys_call_table
 *   The kernel's array of syscall function pointers.
 *   Type: const syscall_fn_t[] where syscall_fn_t = asmlinkage long (*)()
 *   It is marked __ro_after_init, meaning it's read-only after boot.
 *   To modify it, we must disable CPU write protection temporarily.
 */

/*
 * Type for the original openat function.
 * asmlinkage: calling convention where all args are on the stack.
 *   (vs register-based ABI)
 */
typedef asmlinkage long (*orig_openat_t)(
    const struct pt_regs *regs);

static orig_openat_t original_openat;

/* Our replacement openat handler */
static asmlinkage long hook_openat(const struct pt_regs *regs)
{
    /*
     * On x86_64, syscall arguments are in pt_regs fields:
     *   openat(dirfd, pathname, flags, mode)
     *   regs->di = dirfd    (first arg)
     *   regs->si = pathname (second arg, user pointer)
     *   regs->dx = flags    (third arg)
     *   regs->r10 = mode    (fourth arg, note: not rcx due to syscall ABI)
     */
    char fname[256];
    long ret;
    
    if (strncpy_from_user(fname, (const char __user *)regs->si,
                          sizeof(fname) - 1) > 0) {
        pr_info("syscall hook: PID=%d opening: %s\n",
                current->pid, fname);
    }

    /* Call the original syscall */
    ret = original_openat(regs);
    return ret;
}

/*
 * Disable CPU write protection.
 *
 * TERM: CR0 register
 *   x86 control register. Bit 16 (WP = Write Protect) controls
 *   whether the CPU enforces read-only on page table entries.
 *   WP=0: kernel can write to read-only pages.
 *   WP=1: kernel cannot write to read-only pages (normal).
 *
 * WARNING: Modern kernels use additional protections (PKS, CET)
 *   that make this approach less reliable / more complex.
 */
static inline void disable_write_protect(void)
{
    unsigned long cr0 = read_cr0();
    clear_bit(16, &cr0);  /* clear WP bit */
    write_cr0(cr0);
    /* On modern kernels: use set_memory_rw() instead */
}

static inline void enable_write_protect(void)
{
    unsigned long cr0 = read_cr0();
    set_bit(16, &cr0);    /* set WP bit */
    write_cr0(cr0);
}

static int __init syscall_hook_init(void)
{
    /* Find sys_call_table address */
    syscall_table = (unsigned long *)kallsyms_lookup_name("sys_call_table");
    if (!syscall_table) {
        pr_err("Cannot find sys_call_table\n");
        return -ENOENT;
    }

    pr_info("sys_call_table at %p\n", syscall_table);

    /* Save original handler */
    original_openat = (orig_openat_t)syscall_table[__NR_openat];

    /* Disable write protection and install our hook */
    disable_write_protect();
    syscall_table[__NR_openat] = (unsigned long)hook_openat;
    enable_write_protect();

    /* 
     * CRITICAL: synchronize_rcu() or smp_mb() may be needed
     * to ensure all CPUs see the new pointer before continuing.
     */
    smp_mb(); /* memory barrier: all CPUs see the write */

    pr_info("openat() syscall hooked\n");
    return 0;
}

static void __exit syscall_hook_exit(void)
{
    /* Restore original handler */
    disable_write_protect();
    syscall_table[__NR_openat] = (unsigned long)original_openat;
    enable_write_protect();

    /*
     * synchronize_rcu: ensure no CPU is still in our hook handler
     * before we unload the module (freeing the code memory).
     */
    synchronize_rcu();
    pr_info("openat() syscall restored\n");
}

module_init(syscall_hook_init);
module_exit(syscall_hook_exit);
```

### Modern Alternative: syscall hooking via eBPF

```bash
# Modern, safe approach: use eBPF tracepoints for syscall hooking
# No kernel write protection bypass needed

# Attach to sys_enter_openat tracepoint:
# /sys/kernel/tracing/events/syscalls/sys_enter_openat/

# Or use bpftrace (a high-level eBPF front-end):
bpftrace -e '
  tracepoint:syscalls:sys_enter_openat {
    printf("PID=%d comm=%s file=%s\n",
           pid, comm, str(args->filename));
  }
'
```

---

## 12. Audit Hooks — Kernel Audit Framework

### Concept

The **Linux Audit System** provides a way to track security-relevant events. It records events to a log that can be used for compliance (PCI-DSS, HIPAA) and forensic analysis.

**Key vocabulary**:
- **audit record**: a structured log entry for one event
- **audit rule**: a specification of what to log (which syscall, which file, which user)
- **auditd**: the userspace daemon that receives and stores audit records
- **audit context**: per-task data about the current syscall being audited

```
AUDIT ARCHITECTURE:

  Syscall happens
       │
       ↓
  audit_syscall_entry()   ← records: who, what syscall, arguments
       │
       ↓ (syscall executes)
       │
  audit_syscall_exit()    ← records: return value, final state
       │
       ↓
  [kernel audit buffer]
       │ (netlink socket)
       ↓
  auditd (userspace daemon)
       │
       ↓
  /var/log/audit/audit.log
```

### Audit Hook Integration in C

```c
// FILE: my_audit.c
// PURPOSE: Generate custom audit records from a kernel module

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/audit.h>

MODULE_LICENSE("GPL");

/*
 * TERM: audit_log_start / audit_log_format / audit_log_end
 *   These three functions form the pattern for writing audit records.
 *
 * TERM: ab (audit buffer)
 *   Temporary buffer for building an audit record.
 *   Must be allocated with audit_log_start() and
 *   committed with audit_log_end().
 *
 * TERM: GFP_ATOMIC
 *   Memory allocation flag: don't sleep, use atomic/emergency pool.
 *   Required when calling from interrupt or atomic context.
 *   GFP_KERNEL: can sleep (normal context).
 */
static void emit_audit_record(const char *action, const char *target)
{
    struct audit_buffer *ab;

    /*
     * audit_log_start:
     *   Begins a new audit record.
     *   Parameters:
     *     audit_context(): current task's audit context (or NULL)
     *     GFP_ATOMIC: allocation flags
     *     AUDIT_USER: type of audit record (AUDIT_USER = generic user-defined)
     *
     *   Other types:
     *     AUDIT_SYSCALL: syscall record
     *     AUDIT_PATH: file path record
     *     AUDIT_SOCKETCALL: socket operation
     *
     *   Returns NULL if auditing is disabled or buffer allocation fails.
     */
    ab = audit_log_start(audit_context(), GFP_ATOMIC, AUDIT_USER);
    if (!ab)
        return;

    /*
     * audit_log_format: printf-like formatting into audit buffer.
     * Each field should be: key=value pairs.
     */
    audit_log_format(ab,
                     "action=%s target=%s pid=%d comm=%s",
                     action, target,
                     current->pid, current->comm);

    /*
     * audit_log_end: submit the record to the audit subsystem.
     * After this call, 'ab' is invalid.
     */
    audit_log_end(ab);
}

static int __init audit_demo_init(void)
{
    emit_audit_record("module_load", "my_audit");
    pr_info("Audit demo module loaded\n");
    return 0;
}

static void __exit audit_demo_exit(void)
{
    emit_audit_record("module_unload", "my_audit");
}

module_init(audit_demo_init);
module_exit(audit_demo_exit);
```

---

## 13. Notification Chains — Internal Kernel Events

### Concept

**Notification chains** are a publish-subscribe mechanism *within* the kernel. One subsystem publishes events; any other subsystem can register to receive them.

**Key vocabulary**:
- **notifier block**: a handler registered to receive notifications
- **chain**: a linked list of notifier blocks
- **priority**: higher priority notifiers are called first
- **return value**: notifiers return NOTIFY_OK, NOTIFY_BAD, NOTIFY_STOP, etc.

```
NOTIFICATION CHAIN MECHANISM:

  PUBLISHER (e.g., network subsystem):          SUBSCRIBERS:
                                                  ┌────────────────┐
  call_chain_event(NETDEV_UP, dev)  ─────────────►│ netdev_chain   │
                                                  │                │
                                                  │ handler_1 ◄──┐ │
                                                  │ handler_2 ◄──┤ │
                                                  │ handler_3 ◄──┘ │
                                                  └────────────────┘
                                                  (called in order)
```

### Important Notification Chains in the Kernel

```
CHAIN NAME              │ Events Delivered
────────────────────────┼─────────────────────────────────────
netdev_chain            │ network device up/down/register
inetaddr_chain          │ IPv4 address add/remove
inet6addr_chain         │ IPv6 address add/remove  
reboot_notifier_list    │ system reboot/shutdown
panic_notifier_list     │ kernel panic
cpu_chain               │ CPU hotplug (online/offline)
pm_chain_head           │ power management events
keyboard_notifier_list  │ keyboard input events
task_exit_notifier      │ task (process) exit
die_chain               │ kernel oops/die events
```

### C Implementation — Network Device Notifier

```c
// FILE: netdev_notifier.c
// PURPOSE: Get notified when network interfaces come up/down

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/notifier.h>
#include <linux/netdevice.h>
#include <linux/inetdevice.h>

MODULE_LICENSE("GPL");

/*
 * TERM: net_device
 *   Kernel structure representing a network interface (eth0, lo, etc.)
 *   Key fields:
 *     .name: interface name string ("eth0")
 *     .ifindex: interface index number
 *     .flags: IFF_UP, IFF_RUNNING, etc.
 *     .dev_addr: MAC address
 */

/*
 * Our notifier callback.
 *
 * Parameters:
 *   nb:  pointer to our notifier_block (so we can use container_of)
 *   event: which event occurred
 *   ptr: event-specific data (for netdev: struct net_device *)
 *
 * Return values:
 *   NOTIFY_OK:   event handled, continue calling other notifiers
 *   NOTIFY_DONE: not interested, skip (same as NOTIFY_OK)
 *   NOTIFY_BAD:  event rejected (not always respected)
 *   NOTIFY_STOP: stop calling further notifiers in the chain
 */
static int my_netdev_notifier_call(struct notifier_block *nb,
                                    unsigned long event,
                                    void *ptr)
{
    /*
     * netdev_notifier_info_to_dev:
     *   Extracts the net_device pointer from the notification info.
     *   'ptr' is struct netdev_notifier_info * (or a subtype).
     */
    struct net_device *dev = netdev_notifier_info_to_dev(ptr);

    switch (event) {
    case NETDEV_UP:
        pr_info("netdev: %s came UP (ifindex=%d)\n",
                dev->name, dev->ifindex);
        break;

    case NETDEV_DOWN:
        pr_info("netdev: %s went DOWN\n", dev->name);
        break;

    case NETDEV_REGISTER:
        pr_info("netdev: %s registered\n", dev->name);
        break;

    case NETDEV_UNREGISTER:
        pr_info("netdev: %s unregistered\n", dev->name);
        break;

    case NETDEV_CHANGEADDR:
        pr_info("netdev: %s MAC address changed\n", dev->name);
        break;

    case NETDEV_CHANGEMTU:
        pr_info("netdev: %s MTU changed to %d\n",
                dev->name, dev->mtu);
        break;

    default:
        break;
    }

    return NOTIFY_OK;
}

/* Define our notifier block */
static struct notifier_block my_netdev_nb = {
    .notifier_call = my_netdev_notifier_call,
    .priority = 0,  /* default priority */
};

static int __init notifier_init(void)
{
    int ret;

    /*
     * register_netdevice_notifier:
     *   Adds my_netdev_nb to the netdev notification chain.
     *   Will be called for ALL network interfaces.
     *   NOTE: also immediately called for all currently registered
     *   interfaces with NETDEV_REGISTER event.
     */
    ret = register_netdevice_notifier(&my_netdev_nb);
    if (ret) {
        pr_err("register_netdevice_notifier failed: %d\n", ret);
        return ret;
    }

    pr_info("Network device notifier registered\n");
    return 0;
}

static void __exit notifier_exit(void)
{
    unregister_netdevice_notifier(&my_netdev_nb);
    pr_info("Network device notifier removed\n");
}

module_init(notifier_init);
module_exit(notifier_exit);
```

---

## 14. Perf Events & PMU Hooks

### Concept

**Perf events** provide an interface to **hardware performance counters** (PMU — Performance Monitoring Unit). These are CPU registers that count events like cache misses, branch mispredictions, instructions retired, etc.

**Key vocabulary**:
- **PMU**: Performance Monitoring Unit — hardware in the CPU that counts events
- **hardware counter**: CPU register incremented on specific events (cache miss, etc.)
- **software event**: kernel-counted event (context switch, page fault, etc.)
- **sampling**: instead of counting every event, record a snapshot periodically
- **overflow**: when a counter overflows, triggers an interrupt → kernel records sample

```
PERF EVENT TYPES:

  HARDWARE EVENTS (CPU PMU):
    PERF_COUNT_HW_CPU_CYCLES          → clock cycles
    PERF_COUNT_HW_INSTRUCTIONS        → instructions retired
    PERF_COUNT_HW_CACHE_MISSES        → last-level cache misses
    PERF_COUNT_HW_BRANCH_MISSES       → branch mispredictions
    PERF_COUNT_HW_BUS_CYCLES          → bus cycles

  SOFTWARE EVENTS (kernel):
    PERF_COUNT_SW_CPU_CLOCK           → CPU time
    PERF_COUNT_SW_TASK_CLOCK          → task time
    PERF_COUNT_SW_PAGE_FAULTS         → page faults
    PERF_COUNT_SW_CONTEXT_SWITCHES    → context switches
    PERF_COUNT_SW_CPU_MIGRATIONS      → CPU migrations

  TRACEPOINT EVENTS:
    → any tracepoint (sched_switch, etc.) as a perf event

  RAW EVENTS:
    → raw PMU event codes (vendor-specific)
```

### Perf Event Hook in C

```c
// FILE: perf_hook.c
// PURPOSE: Count cache misses per process using PMU

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");

static struct perf_event *sample_event;
static DEFINE_PER_CPU(u64, overflow_count);  /* per-CPU counter */

/*
 * TERM: perf_event_attr
 *   Describes what to measure. Key fields:
 *   .type: PERF_TYPE_HARDWARE, PERF_TYPE_SOFTWARE, etc.
 *   .config: specific event within the type
 *   .sample_period: generate overflow every N events
 *   .sample_type: what to record on overflow (IP, PID, time, etc.)
 *
 * TERM: overflow callback
 *   Function called when the event counter overflows.
 *   This is how we get notified of events.
 */

static void perf_overflow_handler(struct perf_event *event,
                                   struct perf_sample_data *data,
                                   struct pt_regs *regs)
{
    /*
     * 'data' contains the sample data based on .sample_type:
     *   PERF_SAMPLE_IP: instruction pointer (where the overflow occurred)
     *   PERF_SAMPLE_TID: task ID (PID/TID)
     *   PERF_SAMPLE_TIME: timestamp
     *   PERF_SAMPLE_CALLCHAIN: stack trace
     *
     * 'regs' contains CPU registers at overflow point.
     */

    u64 *count = this_cpu_ptr(&overflow_count);
    (*count)++;

    pr_info_ratelimited("perf overflow: CPU=%d PID=%d IP=%pS count=%llu\n",
                        smp_processor_id(),
                        current->pid,
                        (void *)regs->ip,
                        *count);
}

static int __init perf_hook_init(void)
{
    struct perf_event_attr attr = {
        .type           = PERF_TYPE_HARDWARE,
        .config         = PERF_COUNT_HW_CACHE_MISSES,
        /*
         * sample_period: fire overflow every 1000 cache misses.
         * Too low: too much overhead.
         * Too high: miss important events.
         */
        .sample_period  = 1000,
        .sample_type    = PERF_SAMPLE_IP | PERF_SAMPLE_TID,
        /*
         * exclude_kernel: don't count kernel cache misses.
         * exclude_user:   don't count userspace (we want kernel).
         * We set neither → count both.
         */
        .exclude_kernel = 0,
        .exclude_user   = 0,
        .disabled       = 0,
    };

    /*
     * perf_event_create_kernel_counter:
     *   Creates a perf event in kernel space.
     *
     *   Parameters:
     *     attr:     what to measure
     *     cpu:      -1 for "all CPUs", or specific CPU number
     *     task:     NULL for "all tasks", or specific task_struct
     *     overflow_handler: our callback on overflow
     *     context:  private data passed to handler (NULL here)
     */
    sample_event = perf_event_create_kernel_counter(
            &attr, -1 /* all CPUs */, NULL /* all tasks */,
            perf_overflow_handler, NULL);

    if (IS_ERR(sample_event)) {
        pr_err("perf_event_create_kernel_counter: %ld\n",
               PTR_ERR(sample_event));
        return PTR_ERR(sample_event);
    }

    pr_info("perf event created: counting cache misses\n");
    return 0;
}

static void __exit perf_hook_exit(void)
{
    if (sample_event) {
        /*
         * perf_event_release_kernel:
         *   Disables and destroys the kernel perf event.
         *   Waits for all in-progress callbacks to finish.
         */
        perf_event_release_kernel(sample_event);
    }
    pr_info("perf event removed\n");
}

module_init(perf_hook_init);
module_exit(perf_hook_exit);
```

---

## 15. VFS Hooks — Virtual Filesystem Layer

### Concept

The **VFS** (Virtual Filesystem Switch) is the kernel layer that provides a uniform interface for all filesystems (ext4, xfs, btrfs, tmpfs, procfs...). It does this through **operation tables** — structs of function pointers.

**Key vocabulary**:
- **inode_operations**: table of functions for inode-level operations (create, link, unlink, lookup)
- **file_operations**: table of functions for file descriptor operations (read, write, seek, ioctl)
- **super_operations**: table of functions for filesystem-level operations
- **address_space_operations**: table for page cache operations
- **dentry**: directory entry — connects an inode to a filename

### VFS Operation Tables

```
VFS HOOK POINTS (function pointer tables):

struct file_operations {
    read         → called on read() syscall
    write        → called on write() syscall  
    open         → called on open() syscall
    release      → called on close() (fd released)
    poll         → called on select/poll/epoll
    unlocked_ioctl → called on ioctl()
    mmap         → called on mmap()
    llseek       → called on lseek()
    fsync        → called on fsync()
    splice_read  → called for splice/sendfile
    iterate_shared → called for getdents (readdir)
};

struct inode_operations {
    create   → create a new file
    lookup   → find a file in directory
    link     → create hard link
    unlink   → delete a file
    symlink  → create symbolic link
    mkdir    → create directory
    rmdir    → remove directory
    rename   → rename file/directory
    getattr  → get file attributes (stat)
    setattr  → set file attributes (chmod/chown)
    listxattr → list extended attributes
    get_acl  → get ACL (access control list)
};
```

### Custom Filesystem with VFS Hooks (C)

```c
// FILE: my_fs.c
// PURPOSE: A minimal in-memory filesystem with hooked operations
// This demonstrates VFS hooks by wrapping ext4-like operations

#include <linux/fs.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/pagemap.h>
#include <linux/string.h>

MODULE_LICENSE("GPL");

#define MYFS_MAGIC 0xDEADBEEF

/*
 * Custom file operations: intercept reads
 */
static ssize_t myfs_read(struct file *file,
                          char __user *buf,
                          size_t count,
                          loff_t *ppos)
{
    pr_info("myfs: read called on %s, count=%zu, pos=%lld\n",
            file->f_path.dentry->d_name.name,
            count, *ppos);

    /*
     * In a real interposer/hook scenario, you'd call the original
     * filesystem's read here (or a storage backend).
     * For demo: just return "hello from myfs\n"
     */
    const char *data = "hello from myfs\n";
    size_t len = strlen(data);

    if (*ppos >= len)
        return 0;  /* EOF */

    if (count > len - *ppos)
        count = len - *ppos;

    if (copy_to_user(buf, data + *ppos, count))
        return -EFAULT;

    *ppos += count;
    return count;
}

static int myfs_open(struct inode *inode, struct file *file)
{
    pr_info("myfs: file opened: %s by PID=%d\n",
            file->f_path.dentry->d_name.name,
            current->pid);
    return 0;
}

static const struct file_operations myfs_file_ops = {
    .owner   = THIS_MODULE,
    .open    = myfs_open,
    .read    = myfs_read,
    .llseek  = generic_file_llseek,
};

static const struct inode_operations myfs_inode_ops = {
    /* Using kernel defaults for most — we only intercept what matters */
    .getattr = simple_getattr,
};

/*
 * fill_super: called when filesystem is mounted.
 * Sets up the root inode and dentry.
 */
static int myfs_fill_super(struct super_block *sb, void *data, int silent)
{
    struct inode *root;

    sb->s_magic = MYFS_MAGIC;
    sb->s_op = &simple_super_operations;  /* use generic super ops */

    /* Create root inode */
    root = new_inode(sb);
    if (!root)
        return -ENOMEM;

    root->i_ino  = 1;
    root->i_mode = S_IFDIR | 0755;  /* directory, rwxr-xr-x */
    root->i_op   = &myfs_inode_ops;
    root->i_fop  = &simple_dir_operations;

    /* Create root dentry and link to root inode */
    sb->s_root = d_make_root(root);  /* attach inode to root dentry */
    if (!sb->s_root) {
        iput(root);
        return -ENOMEM;
    }

    pr_info("myfs: mounted\n");
    return 0;
}

static struct dentry *myfs_mount(struct file_system_type *fs_type,
                                  int flags,
                                  const char *dev_name,
                                  void *data)
{
    return mount_nodev(fs_type, flags, data, myfs_fill_super);
}

static struct file_system_type myfs_type = {
    .name    = "myfs",
    .mount   = myfs_mount,
    .kill_sb = kill_anon_super,
    .owner   = THIS_MODULE,
};

static int __init myfs_init(void)
{
    int ret = register_filesystem(&myfs_type);
    if (ret)
        pr_err("register_filesystem failed: %d\n", ret);
    else
        pr_info("myfs registered. Try: mount -t myfs none /mnt/myfs\n");
    return ret;
}

static void __exit myfs_exit(void)
{
    unregister_filesystem(&myfs_type);
    pr_info("myfs unregistered\n");
}

module_init(myfs_init);
module_exit(myfs_exit);
```

---

## 16. Module & Livepatch Hooks

### Kernel Module Lifecycle Hooks

```c
// MODULE NOTIFIER: be notified when any module is loaded/unloaded

#include <linux/module.h>
#include <linux/notifier.h>

static int my_module_notifier(struct notifier_block *nb,
                               unsigned long event,
                               void *data)
{
    struct module *mod = data;  /* the module being loaded/unloaded */

    switch (event) {
    case MODULE_STATE_COMING:
        /*
         * Module is being loaded (init running).
         * mod->name: module name
         * mod->init_size: init section size
         */
        pr_info("module_notifier: %s is LOADING\n", mod->name);
        break;

    case MODULE_STATE_LIVE:
        /* Module fully loaded and active */
        pr_info("module_notifier: %s is NOW LIVE\n", mod->name);
        break;

    case MODULE_STATE_GOING:
        /* Module is being unloaded */
        pr_info("module_notifier: %s is UNLOADING\n", mod->name);
        break;

    case MODULE_STATE_UNFORMED:
        /* Module is being prepared (very early) */
        break;
    }

    return NOTIFY_OK;
}

static struct notifier_block module_nb = {
    .notifier_call = my_module_notifier,
};

/* In init: register_module_notifier(&module_nb); */
/* In exit: unregister_module_notifier(&module_nb); */
```

### Livepatch — Hot-Patching Kernel Functions

```c
// FILE: my_livepatch.c
// PURPOSE: Replace a kernel function at runtime WITHOUT REBOOTING
//
// TERM: livepatch
//   A kernel mechanism to replace functions in a running kernel.
//   Used for security patches without downtime.
//   Based on ftrace + careful consistency model.
//
// TERM: consistency model
//   Ensures all tasks have "transitioned" to use the new function
//   before the old function memory is freed.

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/livepatch.h>

MODULE_LICENSE("GPL");

/*
 * Our replacement for the kernel's cmdline_proc_show function
 * (shows /proc/cmdline).
 *
 * MUST have the same signature as the original!
 */
static int lp_cmdline_proc_show(struct seq_file *m, void *v)
{
    seq_printf(m, "PATCHED_CMDLINE quiet splash\n");
    return 0;
}

/*
 * klp_func: describes one function replacement.
 * klp_object: describes a collection of func replacements in one module.
 * klp_patch: the top-level structure submitted to the livepatch subsystem.
 */
static struct klp_func my_funcs[] = {
    {
        .old_name = "cmdline_proc_show",  /* function to replace */
        .new_func = lp_cmdline_proc_show, /* our replacement */
    },
    {} /* terminator */
};

static struct klp_object my_objs[] = {
    {
        /* NULL name means: patch the vmlinux (core kernel) */
        .name  = NULL,
        .funcs = my_funcs,
    },
    {} /* terminator */
};

static struct klp_patch my_patch = {
    .mod  = THIS_MODULE,
    .objs = my_objs,
};

static int __init livepatch_init(void)
{
    /*
     * klp_enable_patch:
     *   Registers and enables the livepatch.
     *   Uses a consistency model to safely transition all tasks.
     *   May take a few seconds if tasks are in the middle of
     *   the patched function.
     */
    return klp_enable_patch(&my_patch);
}

static void __exit livepatch_exit(void)
{
    /* Livepatch modules cannot normally be unloaded once applied */
    /* Use /sys/kernel/livepatch/<name>/enabled to disable */
}

module_init(livepatch_init);
module_exit(livepatch_exit);

MODULE_INFO(livepatch, "Y");  /* required for livepatch modules */
```

---

## 17. Rust in the Linux Kernel — Safe Hook Implementations

### Background: Rust in Linux

Since Linux 6.1, Rust is an officially supported second language for kernel development. Rust's ownership system prevents entire classes of kernel bugs:
- Use-after-free
- Data races
- Null pointer dereferences
- Buffer overflows

**Key vocabulary**:
- **bindings**: auto-generated Rust wrappers around C kernel APIs
- **`kernel` crate**: the Rust standard library for Linux kernel development
- **`Arc<T>`**: atomic reference-counted pointer (like `Arc` in std, but kernel-appropriate)
- **`Mutex<T>`**: kernel mutex wrapping data (enforces lock-before-access)

### Rust Module Skeleton

```rust
// FILE: my_module.rs
// PURPOSE: Minimal Rust kernel module

// These are always required in kernel Rust modules
#![no_std]          // No standard library (kernel provides its own)
#![feature(allocator_api)]

use kernel::prelude::*;
//
// kernel::prelude::* provides:
//   - pr_info!, pr_err!, pr_warn! macros (like printk)
//   - Result type (kernel version, not std::result::Result)
//   - Error type
//   - Module trait
//   - Box, Vec (kernel heap allocators)

/// MODULE METADATA - required
module! {
    type: MyModule,
    name: "my_rust_module",
    author: "DSA Master",
    description: "Rust kernel module demo",
    license: "GPL",
}

/// The module's state.
/// This struct is created in init() and destroyed in drop().
struct MyModule {
    // put persistent state here
    count: u32,
}

/// Implement the Module trait: required for every kernel module
impl kernel::Module for MyModule {
    /// Called when the module is loaded (equivalent to module_init)
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("Rust module loaded!\n");
        
        // Return Ok(Self { ... }) to signal successful init
        // Return Err(EINVAL) etc. to fail loading
        Ok(MyModule { count: 0 })
    }
}

/// Called when the module is unloaded (equivalent to module_exit)
/// The Drop trait is Rust's destructor mechanism.
impl Drop for MyModule {
    fn drop(&mut self) {
        pr_info!("Rust module unloaded! count was {}\n", self.count);
    }
}
```

### Rust kprobe Implementation

```rust
// FILE: rust_kprobe.rs
// PURPOSE: Rust wrapper around kprobe for safe usage
// NOTE: As of Linux 6.x, kprobe bindings are still being developed.
// This shows the pattern using unsafe FFI where needed.

#![no_std]

use kernel::prelude::*;
use kernel::bindings;  // raw C bindings

module! {
    type: RustKprobeModule,
    name: "rust_kprobe",
    author: "DSA Master",
    description: "Rust kprobe demonstration",
    license: "GPL",
}

// ─────────────────────────────────────────────────────────────
// TERM: extern "C"
//   Tells Rust to use C calling convention for this function.
//   Required when a function will be called from C code
//   (like the kprobe subsystem calling our handlers).
//
// TERM: unsafe
//   Rust block where you bypass safety guarantees.
//   Required when calling C code or doing raw pointer ops.
//   The programmer is responsible for correctness here.
// ─────────────────────────────────────────────────────────────

/// Pre-handler: called before the probed instruction
/// Must be unsafe extern "C" because kprobe calls it from C
unsafe extern "C" fn pre_handler(
    kp: *mut bindings::kprobe,
    regs: *mut bindings::pt_regs,
) -> i32 {
    // SAFETY: regs is valid (guaranteed by kprobe framework)
    // SAFETY: current is always valid in kernel context
    let pid = unsafe { (*bindings::get_current()).pid };
    
    pr_info!("rust kprobe pre_handler: PID={}\n", pid);
    
    // Access instruction pointer from registers
    // SAFETY: regs is valid and ip field always exists
    let ip = unsafe { (*regs).ip };
    pr_info!("  instruction pointer: 0x{:x}\n", ip);
    
    0 // return 0 to continue execution
}

/// Post-handler: called after the probed instruction
unsafe extern "C" fn post_handler(
    kp: *mut bindings::kprobe,
    regs: *mut bindings::pt_regs,
    flags: u64,
) {
    pr_info!("rust kprobe post_handler fired\n");
}

struct RustKprobeModule {
    // Store kprobe in a Box to give it stable address
    // (kprobe needs to stay at a fixed memory location)
    kp: Box<bindings::kprobe>,
}

impl kernel::Module for RustKprobeModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        // SAFETY: zeroed kprobe is valid starting state
        // We fill in required fields below
        let mut kp = Box::try_new(unsafe {
            core::mem::zeroed::<bindings::kprobe>()
        })?;

        // Set symbol_name to "vfs_read\0"
        // SAFETY: symbol_name must point to a valid C string
        //         that lives as long as the kprobe is registered
        kp.symbol_name = b"vfs_read\0".as_ptr() as *const i8;
        kp.pre_handler = Some(pre_handler);
        kp.post_handler = Some(post_handler);

        // Register the kprobe
        // SAFETY: kp is properly initialized, symbol is valid
        let ret = unsafe {
            bindings::register_kprobe(kp.as_mut() as *mut bindings::kprobe)
        };

        if ret != 0 {
            pr_err!("register_kprobe failed: {}\n", ret);
            return Err(kernel::error::from_err_ptr(
                ret as *mut core::ffi::c_void
            ).err().unwrap_or(EINVAL));
        }

        pr_info!("Rust kprobe registered on vfs_read\n");
        Ok(RustKprobeModule { kp })
    }
}

impl Drop for RustKprobeModule {
    fn drop(&mut self) {
        // SAFETY: kp is the same pointer we registered
        unsafe {
            bindings::unregister_kprobe(
                self.kp.as_mut() as *mut bindings::kprobe
            );
        }
        pr_info!("Rust kprobe unregistered\n");
    }
}
```

### Rust Netfilter Hook

```rust
// FILE: rust_netfilter.rs
// PURPOSE: Netfilter hook in Rust
// Using the kernel::net::filter module (available in recent kernel rust bindings)

#![no_std]

use kernel::prelude::*;
use kernel::net::filter::{self, NfHookOps, NfHookState, SkBuff};
use kernel::net::{self, Namespace};

module! {
    type: RustNetfilter,
    name: "rust_netfilter",
    author: "DSA Master",
    description: "Rust netfilter hook",
    license: "GPL",
}

// Netfilter verdict constants
const NF_ACCEPT: u32 = 1;
const NF_DROP: u32 = 0;

/// Our netfilter hook function
///
/// # Safety
/// Called by the kernel netfilter framework with valid pointers.
fn my_hook(
    _priv: *mut core::ffi::c_void,
    skb: *mut bindings::sk_buff,
    state: *const bindings::nf_hook_state,
) -> u32 {
    // SAFETY: skb is valid (guaranteed by netfilter)
    if skb.is_null() {
        return NF_ACCEPT;
    }

    // Get IP header
    // SAFETY: skb->data points to valid network data
    let ip_hdr = unsafe {
        let data_ptr = (*skb).__bindgen_anon_1.__bindgen_anon_1.head
            .add((*skb).network_header as usize);
        &*(data_ptr as *const bindings::iphdr)
    };

    // Check protocol (1 = ICMP)
    if ip_hdr.protocol == 1 {
        // Get ICMP header
        let icmp_hdr_ptr = unsafe {
            let data_ptr = (*skb).__bindgen_anon_1.__bindgen_anon_1.head
                .add((*skb).transport_header as usize);
            &*(data_ptr as *const bindings::icmphdr)
        };

        // Type 8 = ICMP echo request (ping)
        if unsafe { icmp_hdr_ptr.type_ } == 8 {
            pr_info!("rust netfilter: dropping ICMP echo request\n");
            return NF_DROP;
        }
    }

    NF_ACCEPT
}

struct RustNetfilter {
    // nf_hook_ops needs stable address
    ops: Box<bindings::nf_hook_ops>,
}

impl kernel::Module for RustNetfilter {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        // Build the hook ops structure
        let mut ops = Box::try_new(bindings::nf_hook_ops {
            hook: Some(my_hook),
            // SAFETY: init_net is the default network namespace
            // We use the address directly; it's a global kernel variable
            pf: bindings::NFPROTO_IPV4 as u8,
            hooknum: bindings::NF_INET_PRE_ROUTING,
            priority: bindings::NF_IP_PRI_FIRST as i32,
            ..unsafe { core::mem::zeroed() }
        })?;

        // Register hook
        // SAFETY: ops is properly initialized, init_net is valid
        let ret = unsafe {
            bindings::nf_register_net_hook(
                &mut bindings::init_net as *mut bindings::net,
                ops.as_mut() as *mut bindings::nf_hook_ops,
            )
        };

        if ret != 0 {
            pr_err!("nf_register_net_hook failed: {}\n", ret);
            return Err(EINVAL);
        }

        pr_info!("Rust netfilter hook registered\n");
        Ok(RustNetfilter { ops })
    }
}

impl Drop for RustNetfilter {
    fn drop(&mut self) {
        // SAFETY: same ops we registered
        unsafe {
            bindings::nf_unregister_net_hook(
                &mut bindings::init_net as *mut bindings::net,
                self.ops.as_mut() as *mut bindings::nf_hook_ops,
            );
        }
        pr_info!("Rust netfilter hook removed\n");
    }
}
```

### Rust eBPF Programs with Aya

**Aya** is a Rust eBPF library that lets you write both the kernel eBPF program AND the userspace control program in pure Rust.

```rust
// FILE: aya_probe.rs (BPF program - runs in kernel)
// Compiled with: cargo build --target bpfel-unknown-none

#![no_std]
#![no_main]

use aya_bpf::{
    macros::kprobe,
    programs::ProbeContext,
    helpers::bpf_get_current_pid_tgid,
    helpers::bpf_get_current_comm,
};
use aya_log_ebpf::info;

/// This function is the eBPF program.
/// The #[kprobe] macro places it in the kprobe ELF section.
/// "vfs_read" is the function to probe.
#[kprobe(name = "vfs_read")]
pub fn vfs_read_probe(ctx: ProbeContext) -> u32 {
    match try_vfs_read(&ctx) {
        Ok(ret) => ret,
        Err(_) => 0,
    }
}

fn try_vfs_read(ctx: &ProbeContext) -> Result<u32, i64> {
    let pid = bpf_get_current_pid_tgid() >> 32;
    
    // comm: array to hold process name
    let mut comm = [0u8; 16];
    bpf_get_current_comm(&mut comm)?;
    
    // info! macro: sends a log message to the ring buffer
    // (read by the userspace Aya program)
    info!(ctx, "vfs_read called by PID={} comm={}", pid, 
          core::str::from_utf8(&comm).unwrap_or("?"));
    
    Ok(0)
}

/// Required panic handler for no_std
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
```

```rust
// FILE: aya_user.rs (userspace loader - standard Rust)
// Compiled normally with cargo

use aya::{
    include_bytes_aligned,
    programs::{KProbe, ProgramError},
    Bpf,
};
use aya_log::BpfLogger;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    // include_bytes_aligned!: embeds the compiled BPF object at compile time
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/aya_probe"
    ))?;
    
    // Set up log forwarding from BPF → userspace
    BpfLogger::init(&mut bpf)?;
    
    // Get a reference to the kprobe program by name
    let program: &mut KProbe = bpf.program_mut("vfs_read_probe")
        .unwrap()
        .try_into()?;
    
    // Load the program into the kernel (verifier runs here)
    program.load()?;
    
    // Attach the kprobe to vfs_read
    program.attach("vfs_read", 0)?;
    
    println!("Tracing vfs_read... Press Ctrl+C to stop");
    
    // Wait for Ctrl+C
    signal::ctrl_c().await?;
    
    println!("Stopping...");
    Ok(())
}
```

---

## 18. Comparison Matrix & Decision Framework

### Hook Selection Matrix

```
┌──────────────────┬────────┬────────┬───────┬──────┬────────┬────────┐
│ Hook Type        │ Over-  │ Safety │ Stable│ Scope│ Can    │ Ring   │
│                  │ head   │        │  API  │      │ Modify?│ Buffer │
├──────────────────┼────────┼────────┼───────┼──────┼────────┼────────┤
│ kprobe           │ ~200ns │ Medium │  No   │Kernel│  Yes   │  No    │
│ kretprobe        │ ~300ns │ Medium │  No   │Kernel│Ret only│  No    │
│ uprobe           │ ~500ns │ Medium │  No   │ User │  Yes   │  No    │
│ tracepoint       │  ~5ns  │  High  │  Yes  │Kernel│  No    │  Yes   │
│ ftrace           │  ~2ns  │  High  │  Yes  │Kernel│ Risky  │  No    │
│ eBPF kprobe      │ ~300ns │  Max   │  No   │Both  │ Limited│  Yes   │
│ eBPF tracepoint  │  ~50ns │  Max   │  Yes  │Both  │ Limited│  Yes   │
│ eBPF fentry      │  ~50ns │  Max   │  Yes  │Kernel│ Limited│  Yes   │
│ eBPF XDP         │  ~10ns │  Max   │  Yes  │ Net  │  Yes   │  Yes   │
│ LSM hook         │  ~10ns │  High  │  Yes  │Kernel│ Policy │  No    │
│ Netfilter        │  ~50ns │  High  │  Yes  │ Net  │  Yes   │  No    │
│ Syscall table    │  ~5ns  │   Low  │  No   │Kernel│  Yes   │  No    │
│ Notification     │  ~5ns  │  High  │  Yes  │Kernel│  No    │  No    │
│ Livepatch        │   0ns  │  High  │  Yes  │Kernel│  Full  │  No    │
└──────────────────┴────────┴────────┴───────┴──────┴────────┴────────┘
```

### Decision Tree — Which Hook to Use?

```
START: I need to hook the kernel. Which mechanism?
│
├─ Do you need to be SAFE (no crashes, verifier-guaranteed)?
│   └─ YES → Use eBPF
│       ├─ Tracing/observability? → eBPF kprobe or fentry
│       ├─ Network packet processing? → eBPF XDP or TC
│       ├─ Security enforcement? → eBPF LSM
│       └─ Syscall tracing? → eBPF tracepoint
│
├─ Do you need a STABLE API (won't break on kernel update)?
│   └─ YES → Use tracepoints or netfilter or LSM hooks
│       ├─ Network? → Netfilter
│       ├─ Security policy? → LSM
│       └─ Kernel events? → Tracepoints
│
├─ Do you need to instrument ANY arbitrary function?
│   └─ YES → kprobe (or eBPF kprobe for safety)
│
├─ Do you need to instrument USERSPACE from kernel?
│   └─ YES → uprobe (or eBPF uprobe)
│
├─ Do you need ZERO OVERHEAD when inactive?
│   └─ YES → tracepoints (near-zero when disabled)
│
├─ Do you need to MODIFY packet bytes?
│   └─ YES → Netfilter (or eBPF XDP for performance)
│
├─ Do you need to REPLACE a kernel function?
│   └─ YES → livepatch (stable) or ftrace hook (dev)
│
└─ Do you need HARDWARE event counting?
    └─ YES → Perf events / PMU
```

---

## 19. Real-World Patterns & Architectures

### Pattern 1: Observability Stack (like Falco/bpftrace)

```
ARCHITECTURE: Security Observability System

  ┌─────────────────────────────────────────────────────────┐
  │                    USER SPACE                           │
  │                                                         │
  │  ┌──────────────┐  ┌───────────────┐  ┌─────────────┐  │
  │  │  Rule Engine  │  │  Alert System │  │  Dashboard  │  │
  │  │  (Falco-like) │  │  (Slack/PD)   │  │  (Grafana)  │  │
  │  └──────┬────────┘  └───────────────┘  └─────────────┘  │
  │         │                                                │
  │  ┌──────▼──────────────────────────────────────────┐    │
  │  │         Ring Buffer Consumer                    │    │
  │  │  (reads events, applies rules, alerts)          │    │
  │  └──────┬──────────────────────────────────────────┘    │
  └─────────┼───────────────────────────────────────────────┘
            │ mmap (zero-copy)
  ══════════╪══════════════════════════════════════════════
            │
  ┌─────────▼───────────────────────────────────────────────┐
  │                    KERNEL SPACE                         │
  │                                                         │
  │  BPF Ring Buffer                                        │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │  [event][event][event][event]...                 │   │
  │  └──────────────────────────────────────────────────┘   │
  │       ↑          ↑          ↑          ↑                 │
  │  BPF Programs attached to:                               │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
  │  │execve    │ │openat    │ │network   │ │setuid    │   │
  │  │tracepoint│ │kprobe    │ │XDP hook  │ │LSM hook  │   │
  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
  └─────────────────────────────────────────────────────────┘
```

### Pattern 2: Network Acceleration (like Cilium)

```
PACKET PROCESSING PIPELINE (with eBPF acceleration):

  NIC Hardware
       │
       ↓
  [XDP hook] ← eBPF: drop DDoS traffic at wire speed (before sk_buff!)
       │         Can drop millions of packets/sec per core
       ↓
  sk_buff created
       │
       ↓
  [TC ingress hook] ← eBPF: load balancing, policy enforcement
       │
       ↓
  [Netfilter PRE_ROUTING] ← iptables/nftables rules
       │
       ↓
  Routing Decision
       │
  ┌────┴────┐
  │         │
  ▼         ▼
[LOCAL_IN] [FORWARD]
  │         │
  ▼         ▼
[Socket  [Netfilter]
 receive]    │
  │      [TC egress]
  ▼          │
Application  ▼
            NIC → wire
```

### Pattern 3: Syscall Audit Trail

```
AUDIT TRAIL ARCHITECTURE:

  Process makes syscall
       │
       ├─► [kprobe on syscall entry]
       │       Records: args, timestamp, CPU, PID
       │       Writes to: BPF ring buffer
       │
       │ (syscall executes)
       │
       ├─► [kretprobe on syscall exit]
       │       Records: return value, duration
       │       Writes to: BPF ring buffer
       │
       │
  [BPF ring buffer] ──────────────────► [userspace daemon]
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                               [sqlite DB] [syslog] [SIEM]
                               (local)    (remote) (Splunk)
```

---

## 20. Security, Pitfalls & Best Practices

### The Golden Rules of Hook Development

```
RULE 1: CONTEXT AWARENESS
  ┌─────────────────────────────────────────────────────────┐
  │ Before writing ANY hook code, answer:                   │
  │                                                         │
  │ Q: Can my handler sleep?                                │
  │ - Interrupt context: NO (use spinlock, not mutex)       │
  │ - Process context: YES (can use mutex, kmalloc GFP_KERNEL)│
  │                                                         │
  │ Q: Can I access current->mm (user memory)?              │
  │ - Interrupt context: NO                                 │
  │ - Process context: YES (with copy_from_user)            │
  └─────────────────────────────────────────────────────────┘

RULE 2: NEVER DEADLOCK
  - Never take a lock that might already be held at your hook point
  - Don't call functions that take the same lock your caller holds
  - Example: If hooked in scheduler path, don't call schedule()!

RULE 3: ALWAYS CLEAN UP
  - Every register_X() must have matching unregister_X() in exit
  - Use synchronize_rcu() / synchronize_sched() after unregistering
  - Failing to synchronize → use-after-free as module unloads

RULE 4: HANDLE ERRORS
  - Hook registration can fail (symbol not found, already hooked)
  - Always check return values
  - Partial init → unwind what succeeded in error path

RULE 5: RATE LIMIT LOGGING
  - Hook handlers can fire MILLIONS of times per second
  - Using pr_info() in hot path → floods dmesg → performance collapse
  - Always use pr_info_ratelimited() or BPF ring buffer

RULE 6: BEWARE RECURSION
  - Your hook calls function X → if X is also hooked → infinite loop
  - Use FTRACE_OPS_FL_RECURSION flag in ftrace hooks
  - In kprobe handlers: don't call the function you're probing
```

### Common Pitfalls

```
PITFALL 1: Module unload race condition
  WRONG:
    unregister_kprobe(&kp);
    // handler might still be running on another CPU!
    return 0; // module memory freed immediately
    
  RIGHT:
    unregister_kprobe(&kp);
    synchronize_rcu();  // wait for all handlers to finish
    return 0;

PITFALL 2: Wrong memory allocation in interrupt context
  WRONG (in irq/softirq handler):
    char *buf = kmalloc(256, GFP_KERNEL);  // GFP_KERNEL can sleep!
    
  RIGHT:
    char *buf = kmalloc(256, GFP_ATOMIC);  // atomic, never sleeps

PITFALL 3: Accessing user memory from wrong context
  WRONG (in interrupt handler):
    copy_from_user(buf, user_ptr, len);  // will crash or return garbage
    
  RIGHT:
    // Only in process context (syscall handlers, etc.)
    if (!in_interrupt())
        copy_from_user(buf, user_ptr, len);

PITFALL 4: Not checking kprobe symbol existence
  WRONG:
    kp.symbol_name = "some_internal_function";
    register_kprobe(&kp);  // silently fails, kp.addr = NULL
    
  RIGHT:
    ret = register_kprobe(&kp);
    if (ret || !kp.addr) {
        pr_err("kprobe registration failed: %d\n", ret);
        return -ENOENT;
    }

PITFALL 5: Forgetting eBPF map type constraints
  - PERCPU maps: each CPU has own copy (no contention, great for counters)
  - Shared maps: need atomic operations (use __sync_fetch_and_add())
  - Ring buffer: for sending events to userspace (not for control data)
  - Array maps: key must be 0 to max_entries-1 (no arbitrary keys)
```

### Security Considerations

```
SECURITY MODEL FOR HOOKS:

  WHO CAN LOAD A HOOK MODULE?
    → root (CAP_SYS_ADMIN) required for kernel modules
    → CAP_BPF required for eBPF programs (since Linux 5.8)
    → Secure boot: kernel may require signed modules

  DETECTION OF MALICIOUS HOOKS:
    Tools that can detect hook-based rootkits:
    → chkrootkit, rkhunter: check known signatures
    → eBPF iterators: inspect loaded BPF programs
    → /sys/kernel/kprobes/list: see registered kprobes
    → /sys/kernel/tracing/: see active tracers
    → checksec tools: look for syscall table modifications

  HOW ROOTKITS USE HOOKS:
    → Modify sys_call_table to hide files (ls shows nothing)
    → Hook netfilter to hide network connections
    → Hook /proc filesystem to hide processes
    → Use kprobes to steal credentials in-flight
    
  DEFENSES:
    → CONFIG_SECURITY_LOCKDOWN: prevents /dev/mem, raw disk access
    → CONFIG_KALLSYMS: can be disabled to hide symbol addresses
    → CONFIG_DEBUG_RODATA: makes code sections truly read-only
    → Secure Boot + module signing: only signed modules load
    → SELinux/AppArmor: LSM hooks can restrict LSM hook loading
```

---

## Appendix: Build System Setup

### Makefile for Kernel Modules

```makefile
# Makefile for compiling kernel modules

# Module name
obj-m += my_kprobe.o my_netfilter.o my_lsm.o

# Kernel source directory
KDIR ?= /lib/modules/$(shell uname -r)/build

# Build directory
PWD := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Load/unload helpers
load:
	sudo insmod my_kprobe.ko

unload:
	sudo rmmod my_kprobe

test:
	sudo dmesg | tail -20

# Show kprobe registrations
show_kprobes:
	cat /sys/kernel/kprobes/list

# Show loaded BPF programs
show_bpf:
	sudo bpftool prog list

.PHONY: all clean load unload test show_kprobes show_bpf
```

### Cargo.toml for Aya eBPF Project

```toml
# Workspace Cargo.toml for Aya eBPF project structure

[workspace]
members = [
    "my-ebpf",        # BPF kernel programs
    "my-ebpf-common", # shared types between kernel and user
    "my-ebpf-user",   # userspace control program
]

# my-ebpf/Cargo.toml (kernel BPF side)
[package]
name = "my-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-bpf = { version = "0.1" }
aya-log-ebpf = { version = "0.1" }
my-ebpf-common = { path = "../my-ebpf-common" }

# my-ebpf-user/Cargo.toml (userspace side)
[package]
name = "my-ebpf-user"
version = "0.1.0"
edition = "2021"

[dependencies]
aya = { version = "0.12", features = ["async_tokio"] }
aya-log = { version = "0.2" }
tokio = { version = "1", features = ["full"] }
anyhow = "1"
my-ebpf-common = { path = "../my-ebpf-common" }
```

---

## Appendix: Diagnostic Commands Reference

```bash
# ──────────────────────────────────────────────────────
# KPROBES
# ──────────────────────────────────────────────────────

# List all registered kprobes
cat /sys/kernel/kprobes/list

# Check if address is probeable
cat /sys/kernel/kprobes/enabled

# Enable/disable all kprobes globally
echo 1 > /sys/kernel/kprobes/enabled
echo 0 > /sys/kernel/kprobes/enabled

# ──────────────────────────────────────────────────────
# TRACING / TRACEFS
# ──────────────────────────────────────────────────────

# List all tracers
cat /sys/kernel/tracing/available_tracers

# Enable function tracer
echo function > /sys/kernel/tracing/current_tracer

# Enable function graph tracer (shows call graphs)
echo function_graph > /sys/kernel/tracing/current_tracer

# Filter to specific function
echo vfs_read > /sys/kernel/tracing/set_ftrace_filter

# Read the trace
cat /sys/kernel/tracing/trace

# Enable tracepoint
echo 1 > /sys/kernel/tracing/events/sched/sched_switch/enable

# ──────────────────────────────────────────────────────
# eBPF
# ──────────────────────────────────────────────────────

# List all loaded BPF programs
sudo bpftool prog list

# Show BPF maps
sudo bpftool map list

# Dump BPF program bytecode
sudo bpftool prog dump xlated id <ID>

# Show JIT-compiled native code
sudo bpftool prog dump jited id <ID>

# Show BPF program attached to tracepoint
sudo bpftool perf list

# Read BPF map contents
sudo bpftool map dump id <ID>

# ──────────────────────────────────────────────────────
# LSM
# ──────────────────────────────────────────────────────

# Check which LSMs are active
cat /sys/kernel/security/lsm

# Check LSM ordering
cat /proc/sys/kernel/modules_disabled

# ──────────────────────────────────────────────────────
# NETFILTER
# ──────────────────────────────────────────────────────

# List iptables rules (netfilter frontend)
sudo iptables -L -n -v

# List nftables rules
sudo nft list ruleset

# Show netfilter hook statistics
cat /proc/net/ip_tables_names

# ──────────────────────────────────────────────────────
# PERF
# ──────────────────────────────────────────────────────

# List all perf events
perf list

# Trace specific events for 5 seconds
sudo perf stat -e cache-misses,instructions -a sleep 5

# Record and report
sudo perf record -g -a sleep 10
sudo perf report

# ──────────────────────────────────────────────────────
# MODULES
# ──────────────────────────────────────────────────────

# Load a module
sudo insmod my_module.ko

# Unload a module
sudo rmmod my_module

# List loaded modules
lsmod | grep my_

# Check dmesg for module output
sudo dmesg | tail -50

# Check kernel log in real time
sudo dmesg -w
```

---

*This guide represents the complete mental model of Linux kernel hooks — from CPU-level mechanisms to high-level abstractions. Master each layer, and you will have the intuition to choose the right tool for any instrumentation, security, or observability challenge.*

*Remember: every expert was once a beginner who refused to stay there. The kernel is complex — but it is learnable. One hook at a time.*