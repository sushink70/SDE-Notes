# Linux Dynamic Tracing: kprobe, uprobe, and the Complete Ecosystem
## A World-Class Reference for Systems Engineers

---

## Table of Contents

1. [Mental Model: Why Tracing Exists](#1-mental-model-why-tracing-exists)
2. [The Linux Observability Stack (Full Landscape)](#2-the-linux-observability-stack)
3. [Fundamental Concepts You Must Know First](#3-fundamental-concepts-you-must-know-first)
4. [kprobes — Kernel Dynamic Probing](#4-kprobes)
5. [kretprobes — Return Probes](#5-kretprobes)
6. [uprobes — Userspace Dynamic Probing](#6-uprobes)
7. [uretprobes — Userspace Return Probes](#7-uretprobes)
8. [Tracepoints — Static Kernel Instrumentation](#8-tracepoints)
9. [ftrace — Function Tracer](#9-ftrace)
10. [perf_events — Performance Counters](#10-perf_events)
11. [eBPF — Extended Berkeley Packet Filter](#11-ebpf)
12. [SystemTap & DTrace Concepts](#12-systemtap--dtrace)
13. [The Kernel Probe Mechanics (Deep Internals)](#13-kernel-probe-mechanics-deep-internals)
14. [C Implementations](#14-c-implementations)
15. [Rust Implementations](#15-rust-implementations)
16. [Real-World Use Cases & Patterns](#16-real-world-use-cases--patterns)
17. [Performance Overhead Analysis](#17-performance-overhead-analysis)
18. [Security Considerations](#18-security-considerations)
19. [Debugging Probes Themselves](#19-debugging-probes-themselves)
20. [Mental Models & Expert Intuition](#20-mental-models--expert-intuition)

---

## 1. Mental Model: Why Tracing Exists

### The Fundamental Problem

When a program runs, it is a black box. You see inputs and outputs, but not the
internal state transitions. In production systems you cannot attach a debugger
(it would stop the world). You need **non-invasive, zero-downtime observation**.

```
WITHOUT TRACING:
  Program ---[black box]---> Output
  You: "Why is this slow? Why does it crash?"

WITH TRACING:
  Program ---[observable]---> Output
             |          |
          probe1      probe2
             |          |
          data A      data B
```

### The Observer Effect Problem

Every tracing mechanism must answer:
- **When** to observe (trigger condition)
- **What** to observe (registers, stack, memory)
- **How** to observe (safely, with minimal overhead)
- **Where** to store observations (ring buffer, map)

### Two Universes of Tracing

```
┌─────────────────────────────────────────┐
│           USER SPACE (ring 3)           │
│   your program, libraries, glibc        │
│   ↕ uprobes, uretprobes, USDT           │
├─────────────────────────────────────────┤
│       KERNEL SPACE (ring 0)             │
│   syscalls, network stack, scheduler    │
│   ↕ kprobes, kretprobes, tracepoints    │
│   ↕ ftrace, perf_events, eBPF           │
└─────────────────────────────────────────┘
```

---

## 2. The Linux Observability Stack

### Full Landscape Map

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND TOOLS                         │
│  bpftrace  |  bcc  |  perf  |  strace  |  SystemTap    │
└────────────────────────┬────────────────────────────────┘
                         │ uses
┌────────────────────────▼────────────────────────────────┐
│                  PROBE MECHANISMS                        │
│                                                         │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │   kprobes   │  │ uprobes  │  │   tracepoints    │   │
│  │ kretprobes  │  │uretprobes│  │  (static hooks)  │   │
│  └──────┬──────┘  └────┬─────┘  └────────┬─────────┘   │
│         │              │                  │             │
│  ┌──────▼──────────────▼──────────────────▼─────────┐   │
│  │               eBPF Programs                      │   │
│  │  (run safely in kernel, verified by verifier)    │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │              perf_events subsystem               │   │
│  │     Hardware PMU | Software Events | Tracepoints │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                    ftrace                         │  │
│  │  function_graph_tracer | latency tracer | etc.    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Layer Summary

| Mechanism    | Target   | Dynamic? | Overhead | Use Case                    |
|-------------|----------|----------|----------|-----------------------------|
| kprobes     | Kernel   | Yes      | Medium   | Any kernel instruction      |
| kretprobes  | Kernel   | Yes      | Medium   | Kernel function return      |
| uprobes     | User     | Yes      | Higher   | Any userspace instruction   |
| tracepoints | Kernel   | No*      | Low      | Predefined kernel events    |
| ftrace      | Kernel   | Partial  | Low      | Function call tracing       |
| perf_events | Both     | Partial  | Very Low | PMU, HW counters, sampling  |
| eBPF        | Both     | Yes      | Low      | Programmable in-kernel exec |
| USDT        | User     | No*      | Low      | Predefined userspace events |

*Static probes exist at compile time but are "enabled" dynamically at runtime.

---

## 3. Fundamental Concepts You Must Know First

### 3.1 CPU Privilege Rings

Modern CPUs have hardware-enforced privilege levels:

```
Ring 0  ─── Kernel mode: full hardware access, can execute all instructions
Ring 1  ─── (mostly unused in Linux)
Ring 2  ─── (mostly unused in Linux)
Ring 3  ─── User mode: restricted, cannot directly access hardware
```

**Why this matters for probes:**
- kprobes run in Ring 0 — they can read kernel memory, registers, everything
- uprobes use Ring 0 code to observe Ring 3 programs — there's a privilege transition

### 3.2 Interrupts and Exceptions

**Interrupt**: asynchronous signal from hardware (e.g., keyboard, NIC)
**Exception**: synchronous event caused by instruction execution (e.g., divide by zero, page fault, **breakpoint**)

```
CPU executing instruction
        |
        | INT3 instruction encountered (1 byte: 0xCC)
        |
        ▼
CPU saves current state (registers, instruction pointer) on kernel stack
        |
        ▼
CPU jumps to exception handler (registered in IDT - Interrupt Descriptor Table)
        |
        ▼
Handler runs in Ring 0
        |
        ▼
Handler restores state, returns to next instruction
```

**This INT3/breakpoint mechanism is the foundation of kprobes.**

### 3.3 The Instruction Pointer (IP/PC)

The CPU has a special register:
- x86/x86-64: `rip` (64-bit) / `eip` (32-bit)
- ARM64: `pc`
- RISC-V: `pc`

It always points to the **next instruction to execute**. Probes manipulate this
register to redirect execution.

### 3.4 Process Memory Layout

```
High Address
┌──────────────────┐
│   Kernel Space   │  (same physical pages mapped into every process)
├──────────────────┤  ← 0xFFFF800000000000 (x86-64)
│   Stack          │  grows downward ↓
│   ...            │
│   (stack frames) │
├──────────────────┤
│   mmap region    │  shared libs, anonymous mappings
├──────────────────┤
│   Heap           │  grows upward ↑
├──────────────────┤
│   BSS segment    │  uninitialized global/static
├──────────────────┤
│   Data segment   │  initialized global/static
├──────────────────┤
│   Text segment   │  executable code (where uprobes inject)
└──────────────────┘
Low Address (0x400000 typical for executables)
```

### 3.5 Virtual Memory & Page Tables

Each process has its own **virtual address space**. The kernel maps physical
memory to virtual addresses. When a uprobe is installed:
1. The kernel finds the **physical page** backing the virtual address in the target ELF
2. Creates a **copy-on-write** private copy for that process
3. Patches the INT3 into the private copy

This is why uprobes affect all processes running the same binary simultaneously —
the kernel can instrument the same inode's pages.

### 3.6 ELF Format (Essential for uprobes)

**ELF** = Executable and Linkable Format. Every Linux binary/library is ELF.

```
ELF File Structure:
┌─────────────────┐
│   ELF Header    │  magic, arch, entry point
├─────────────────┤
│ Program Headers │  describes segments (loaded into memory)
├─────────────────┤
│   .text         │  machine code (instructions)
├─────────────────┤
│   .data         │  initialized data
├─────────────────┤
│   .bss          │  uninitialized data
├─────────────────┤
│   .symtab       │  symbol table (function names → addresses)
├─────────────────┤
│   .debug_*      │  DWARF debug info (line numbers, variable info)
└─────────────────┘
```

To place a uprobe on `malloc` in `libc.so`, the kernel:
1. Reads the ELF symbol table to find the offset of `malloc`
2. Adds the runtime base address (from `/proc/PID/maps`)
3. Patches that virtual address with INT3

### 3.7 The `/proc` and `/sys` Filesystems

These are **virtual filesystems** — they don't store data on disk. They are
kernel data structures exposed as files.

```
/proc/
  kallsyms          — all kernel symbols with addresses
  kprobes/          — list of active kprobes
  PID/maps          — memory map of process PID
  PID/mem           — raw memory of process

/sys/kernel/debug/  (debugfs, mount with: mount -t debugfs none /sys/kernel/debug)
  tracing/          — ftrace control interface
    kprobe_events   — define kprobe/uprobe events
    uprobe_events   — (same file, different syntax)
    events/         — event directories for tracepoints
    trace           — read the trace ring buffer
    trace_pipe      — streaming trace reader
    available_filter_functions — all traceable kernel functions
```

---

## 4. kprobes

### 4.1 What is a kprobe?

A **kprobe** (kernel probe) is a mechanism that lets you dynamically insert
breakpoints into **any instruction** in the running kernel (with very few
exceptions like kprobes infrastructure itself), and execute a handler function
when that instruction is hit.

**Key insight**: Unlike a debugger, the probed code continues running normally
after the handler. The kernel is not stopped.

### 4.2 How kprobes Work — Step by Step

```
INSTALLATION PHASE:
═══════════════════
1. You specify: "probe at address X in kernel"

2. Kernel saves the original instruction at X
   Original:  [MOV rax, rbx]  (3 bytes, for example)

3. Kernel replaces first byte with INT3 (0xCC):
   Modified:  [INT3][OV rax, rbx]  ← only first byte changed!

4. Kernel stores handler function pointer in kprobe struct

EXECUTION PHASE (every time CPU hits address X):
══════════════════════════════════════════════════
Step 1: CPU fetches instruction at X → sees 0xCC (INT3)
        CPU raises exception #3 (Breakpoint)
        CPU saves registers on kernel stack
        CPU jumps to do_int3() handler

Step 2: do_int3() → kprobe_handler()
        Identifies which kprobe was hit (by checking rip)
        Calls your pre_handler(probe, registers)
        → You can read/modify any register here!

Step 3: Single-step the original instruction:
        a. Restore original bytes temporarily
        b. Set TF (Trap Flag) in EFLAGS to enable single-step mode
        c. Resume execution → CPU executes ONE instruction
        d. CPU raises exception #1 (Debug) after that instruction

Step 4: do_debug() → kprobe_post_handler()
        Calls your post_handler(probe, registers, flags)
        Clears TF flag
        Puts INT3 back
        Resumes normal execution

REMOVAL PHASE:
══════════════
Restore original instruction bytes at X
Free kprobe data structures
```

### 4.3 The kprobe Data Structure (Kernel Source)

```c
// from linux/include/linux/kprobes.h

struct kprobe {
    struct hlist_node hlist;      // for hash table lookup

    /* Location of the probe point */
    kprobe_opcode_t *addr;        // absolute address (can be NULL if symbol_name set)
    const char *symbol_name;      // e.g., "do_sys_open"
    unsigned int offset;          // offset from symbol start

    /* Called before the probed instruction is executed */
    kprobe_pre_handler_t pre_handler;

    /* Called after the single-stepped instruction executes */
    kprobe_post_handler_t post_handler;

    /* Saved copy of the original instruction */
    kprobe_opcode_t opcode;

    /* copy of the original instruction */
    struct arch_specific_insn ainsn;

    u32 flags;  // KPROBE_FLAG_GONE, KPROBE_FLAG_DISABLED, etc.
};
```

### 4.4 Handler Signatures

```c
// pre_handler: called BEFORE the probed instruction
// Returns 0 = normal execution continues
// Returns non-zero = resume from modified address (advanced use)
typedef int (*kprobe_pre_handler_t)(struct kprobe *p, struct pt_regs *regs);

// post_handler: called AFTER the single-stepped instruction
typedef void (*kprobe_post_handler_t)(struct kprobe *p, struct pt_regs *regs,
                                       unsigned long flags);
```

### 4.5 The pt_regs Structure (x86-64)

`pt_regs` is how the kernel saves CPU state when entering kernel mode.
This is what your handler receives:

```c
// arch/x86/include/asm/ptrace.h
struct pt_regs {
    unsigned long r15;   // general purpose registers
    unsigned long r14;
    unsigned long r13;
    unsigned long r12;
    unsigned long rbp;   // base pointer (frame pointer)
    unsigned long rbx;
    unsigned long r11;
    unsigned long r10;
    unsigned long r9;    // function arg 5 (System V ABI)
    unsigned long r8;    // function arg 6
    unsigned long rax;   // return value / syscall number
    unsigned long rcx;   // function arg 4
    unsigned long rdx;   // function arg 3
    unsigned long rsi;   // function arg 2
    unsigned long rdi;   // function arg 1
    unsigned long orig_rax;
    unsigned long rip;   // instruction pointer ← where we are
    unsigned long cs;    // code segment
    unsigned long eflags;// CPU flags (carry, zero, sign, trap, etc.)
    unsigned long rsp;   // stack pointer
    unsigned long ss;    // stack segment
};
```

**System V AMD64 ABI calling convention** (Linux x86-64):
```
Argument 1 → rdi
Argument 2 → rsi
Argument 3 → rdx
Argument 4 → rcx (r10 for syscalls)
Argument 5 → r8
Argument 6 → r9
Return val → rax
Stack      → rsp (arguments 7+ pushed on stack)
```

### 4.6 kprobe Aggregation — Aggregate Probes

If multiple kprobes are placed on the same address, Linux aggregates them:

```
Address X:
  INT3 ← single breakpoint

kprobe_handler():
  Iterates ALL probes registered at X
  Calls each pre_handler in sequence
  Single-steps original instruction once
  Calls each post_handler in sequence
```

### 4.7 Optimized kprobes (jump optimization)

For performance, Linux can replace the INT3 with a **5-byte JMP** to a
trampoline if the target instruction is ≥ 5 bytes and other conditions met:

```
Without optimization:
  INT3 → exception → handler → single-step → continue
  Cost: ~1000+ ns per hit

With jump optimization:
  JMP trampoline → handler → execute copied instruction → JMP back
  Cost: ~100-300 ns per hit (just branch misprediction + function call)
```

Check: `cat /sys/kernel/debug/kprobes/list`
The `[OPTIMIZED]` flag shows if a probe was optimized.

---

## 5. kretprobes

### 5.1 What is a kretprobe?

A **kretprobe** fires when a kernel function **returns**. It lets you:
- Capture the **return value** (in `rax`)
- Measure **latency** (entry time vs return time)
- See the **full function lifecycle**: args on entry + return value on exit

### 5.2 How kretprobes Work

```
TRICK: The return address on the stack is hijacked!

Normal function call:
  CALL func      → pushes return_addr on stack, jumps to func
  func executes
  RET            → pops return_addr, jumps there

kretprobe mechanism:
  kprobe placed on func entry
  
  When func entry fires:
    1. Save the real return_addr from stack
    2. Replace return_addr with trampoline_addr (kretprobe_trampoline)
    3. Store (real_return_addr, instance) in a per-CPU stack
    4. Call your entry_handler (optional)
  
  Function executes normally (using hijacked return address on stack)
  
  When func executes RET:
    → Jumps to kretprobe_trampoline (NOT the original caller!)
  
  kretprobe_trampoline:
    1. Calls your ret_handler (rax = return value!)
    2. Restores real return_addr
    3. Jumps to real_return_addr
```

**Visual:**
```
Caller                  func                   kretprobe_trampoline
  │                       │                            │
  │── CALL func ─────────>│                            │
  │   (push ret_addr)     │                            │
  │                       │ [kprobe fires here]        │
  │                       │ save ret_addr              │
  │                       │ push trampoline on stack   │
  │                       │                            │
  │                       │── (executes normally) ────>│
  │                       │         RET                │ ret_handler called
  │                       │                            │ (sees return value!)
  │<──────────────────────────────────────────────────│
  │   (real return)                                    │
```

### 5.3 kretprobe Data Structure

```c
struct kretprobe {
    struct kprobe kp;               // embedded kprobe (for entry)

    kretprobe_handler_t handler;    // return handler
    kretprobe_handler_t entry_handler; // entry handler (optional)

    int maxactive;  // max simultaneous instances
                    // (for recursive/concurrent functions)
                    // Default: 0 → uses NR_CPUS or 2*NR_CPUS
    int nmissed;    // count of times all instances were busy

    size_t data_size;   // per-instance private data size
    struct hlist_head free_instances;
    raw_spinlock_t lock;
};

struct kretprobe_instance {
    struct hlist_node hlist;
    struct kretprobe *rp;
    kprobe_opcode_t *ret_addr;  // saved return address
    struct task_struct *task;
    void *fp;                   // frame pointer
    char data[];                // your private data (data_size bytes)
};

typedef int (*kretprobe_handler_t)(struct kretprobe_instance *ri,
                                   struct pt_regs *regs);
```

---

## 6. uprobes

### 6.1 What is a uprobe?

A **uprobe** (userspace probe) lets you insert breakpoints into **userspace
processes** — your applications, system libraries (glibc, OpenSSL, etc.) —
without modifying them or restarting them.

Introduced in Linux 3.5 (2012).

### 6.2 How uprobes Work — Deep Mechanics

```
INSTALLATION:
═════════════
1. Specify: binary/library path + file offset
   e.g., /usr/bin/bash at offset 0x12345

2. Kernel opens the inode (file) of the target binary

3. Kernel finds/creates the page containing offset 0x12345

4. Copy-on-write: kernel creates a private copy of that page
   (so other processes reading the same file aren't affected
    until THEY trigger a fault — then they get INT3 too)

5. Kernel patches INT3 (0xCC) at the offset in the private page

6. All processes currently mapping that inode at that offset
   will now hit the INT3 when execution reaches that point

EXECUTION (when a process hits the uprobe):
════════════════════════════════════════════
1. CPU at Ring 3 hits INT3 → CPU raises exception
   CPU transitions to Ring 0 (kernel mode)

2. Kernel's page fault / trap handler identifies this as a uprobe

3. Kernel calls your BPF program OR uprobe handler
   (at this point we're in kernel context, but can read
    the USER process's registers and memory!)

4. To single-step the original instruction:
   a. The original instruction was saved in an "execute out of line" (XOL) slot
      allocated in the user process's address space (the uprobes XOL vma)
   b. The handler patches the XOL slot with the original instruction
      followed by an INT3
   c. Sets the process's rip to the XOL slot
   d. Returns to userspace → process executes the original instruction there

5. Process hits INT3 at XOL slot end
   → kernel fires again, recognizes "post XOL" handler
   → redirects rip back to original_address + instruction_size
   → process continues normally

REMOVAL:
════════
Restore original bytes in the page
If page has no more probes, free the COW copy (pages revert to shared)
```

### 6.3 The XOL (Execute Out of Line) Vma

Every process that has active uprobes gets a special memory region:

```
/proc/PID/maps might show:
7fff80000000-7fff80001000 r-xp 00000000 00:00 0    [uprobes]
```

This is where copied instructions are placed for single-stepping.
It's per-process and kernel-managed.

### 6.4 uprobes vs kprobes — Key Differences

```
┌────────────────────┬────────────────────┬────────────────────┐
│ Aspect             │ kprobes             │ uprobes             │
├────────────────────┼────────────────────┼────────────────────┤
│ Target             │ kernel code        │ userspace code     │
│ Address space      │ kernel virtual     │ per-process virtual │
│ Overhead           │ lower              │ higher             │
│                    │ (no Ring switch)   │ (Ring 3→0→3)       │
│ Memory model       │ single shared      │ per-process COW    │
│ Symbol resolution  │ /proc/kallsyms     │ ELF symtab + DWARF │
│ Multi-process      │ N/A                │ fires for ALL procs │
│                    │                    │ mapping that file   │
│ Libraries          │ N/A                │ YES (libc, etc.)   │
│ JIT code           │ N/A                │ NOT SUPPORTED      │
└────────────────────┴────────────────────┴────────────────────┘
```

### 6.5 USDT — Userspace Statically Defined Tracepoints

**USDT** probes are NOP instructions intentionally placed by developers in
source code at meaningful points. They are like tracepoints but in userspace.

```c
// In application source (using SystemTap SDT macros):
#include <sys/sdt.h>

void process_request(int req_id, const char *url) {
    DTRACE_PROBE2(myapp, request_start, req_id, url);  // NOP normally
    // ... do work ...
    DTRACE_PROBE2(myapp, request_end, req_id, status);
}
```

When compiled, this emits:
1. A NOP instruction at that point in the binary
2. A `.note.stapsdt` ELF section describing the probe:
   - Name, location (offset), argument descriptors

```
readelf -n /usr/lib/x86_64-linux-gnu/libpython3.x.so | grep -A5 stapsdt
  Provider: python
  Name:     function__entry
  Location: 0x000f1234
  Args:     8@%rdi 8@%rsi 4@%rdx
           (arg1=rdi 8bytes, arg2=rsi 8bytes, arg3=rdx 4bytes)
```

When activated, the kernel patches the NOP with INT3 → standard uprobe
mechanism from there.

---

## 7. uretprobes

Same concept as kretprobes but for userspace:

```
uprobe placed at function entry
  → saves caller's return address
  → replaces with trampoline

function returns
  → jumps to trampoline
  → handler fires (can see rax = return value)
  → jumps to real return address
```

**Important caveat**: uretprobes can have issues with functions that:
- Use `longjmp` (bypasses the trampoline)
- Are called via tail-call optimization (TCO)
- Use non-standard calling conventions

---

## 8. Tracepoints

### 8.1 What Are Tracepoints?

Tracepoints are **pre-defined hooks** compiled into the kernel source at
strategically important locations. Unlike kprobes, they are:
- **Stable API**: kernel developers guarantee they won't disappear
- **Lower overhead when inactive**: a single conditional branch (NOP when disabled)
- **Structured**: they have defined argument types/names

### 8.2 How They Work

```c
// In kernel source (e.g., mm/page_alloc.c):
DEFINE_TRACE(mm_page_alloc);

// At the allocation site:
trace_mm_page_alloc(page, order, gfp_flags, migratetype);
```

This compiles to:

```asm
; When tracepoint is DISABLED (default):
NOP NOP NOP NOP NOP    ; 5-byte NOP, essentially zero cost

; When tracepoint is ENABLED:
CALL tracepoint_probe_call  ; calls registered handler
```

The transition from NOP to CALL uses **stop_machine()** — temporarily halts
all CPUs to safely patch the instruction (atomic text modification).

### 8.3 Tracepoint Format Strings

```
cat /sys/kernel/debug/tracing/events/syscalls/sys_enter_openat/format

name: sys_enter_openat
ID: 612
format:
    field:unsigned short common_type;       offset:0;  size:2;
    field:unsigned char common_flags;       offset:2;  size:1;
    field:int __syscall_nr;                 offset:8;  size:4;
    field:int dfd;                          offset:16; size:8;
    field:const char * filename;            offset:24; size:8;
    field:int flags;                        offset:32; size:8;
    field:umode_t mode;                     offset:40; size:8;

print fmt: "dfd: %d, filename: %p, flags: %#lx, mode: %#lx"
```

### 8.4 Browsing Available Tracepoints

```bash
# List all tracepoint categories
ls /sys/kernel/debug/tracing/events/

# Common categories:
# syscalls/      → sys_enter_*, sys_exit_*
# sched/         → sched_switch, sched_wakeup
# mm/            → mm_page_alloc, mm_page_free
# net/           → net_dev_xmit, netif_receive_skb
# block/         → block_rq_insert, block_rq_complete
# irq/           → irq_handler_entry, irq_handler_exit
# skb/           → kfree_skb, consume_skb
# tcp/           → tcp_retransmit_skb
# kmem/          → kmalloc, kfree

# See args for a specific tracepoint:
cat /sys/kernel/debug/tracing/events/sched/sched_switch/format
```

---

## 9. ftrace

### 9.1 What is ftrace?

**ftrace** is the **Function Tracer** — a framework for tracing kernel function
calls. It hooks into the `mcount`/`__fentry__` call that GCC inserts at the
start of every kernel function (when compiled with `-pg -mfentry`).

### 9.2 The mcount/fentry Mechanism

```
Kernel compiled with -pg:
Every kernel function starts with:
  CALL __fentry__   (5 bytes)

When ftrace is inactive:
  These 5 bytes are patched to NOP NOP NOP NOP NOP

When ftrace is active:
  NOP is patched back to CALL __fentry__
  __fentry__ checks registered callbacks and fires them
```

This is different from kprobes — **no INT3**, just a function call or NOP.
This makes ftrace faster than kprobes for function tracing.

### 9.3 ftrace Tracers

```bash
# Available tracers:
cat /sys/kernel/debug/tracing/available_tracers
# blk  function_graph  wakeup_dl  wakeup_rt  wakeup  function  nop

# Enable function tracer:
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace

# Function graph tracer (shows call/return with duration):
echo function_graph > /sys/kernel/debug/tracing/current_tracer
# Output looks like:
#  3) + 63.167 us  |  } /* __do_page_fault */
#  3)               |  filemap_fault() {
#  3)   0.583 us   |      find_lock_page();

# Trace specific function:
echo do_sys_open > /sys/kernel/debug/tracing/set_ftrace_filter
```

### 9.4 Dynamic ftrace — kprobe_events Interface

You can create kprobe/uprobe **events** via ftrace's text interface:

```bash
# Syntax: p[:[GROUP/]EVENT] [MOD:]KSYM[+offs]|MEMADDR [FETCHARGS]
# Syntax: r[MAXACTIVE][:[GROUP/]EVENT] [MOD:]KSYM[+0] [FETCHARGS]

# Create a kprobe event on do_sys_openat2:
echo 'p:myprobes/open do_sys_openat2 filename=+0($si):string flags=%dx:u32' \
  > /sys/kernel/debug/tracing/kprobe_events

# Enable it:
echo 1 > /sys/kernel/debug/tracing/events/myprobes/open/enable

# Read output:
cat /sys/kernel/debug/tracing/trace_pipe

# Create a uprobe event on malloc in libc:
echo 'p:myprobes/malloc /usr/lib/x86_64-linux-gnu/libc.so.6:0x9e210 size=%di:u64' \
  > /sys/kernel/debug/tracing/uprobe_events
```

**Fetch argument syntax** (crucial knowledge):

```
%REG         → register value    (%di, %si, %dx, %cx, %r8, %r9, %ax)
$stack0      → stack[0] (first stack arg)
$stack1      → stack[1]
+OFFSET(REG) → dereference: *(REG + OFFSET)
@ADDR        → global kernel variable at ADDR
@SYMBOL      → global kernel symbol
:TYPE        → cast: u8 u16 u32 u64 s8 s16 s32 s64 string bitfield
```

---

## 10. perf_events

### 10.1 What is perf_events?

**perf_events** is the Linux Performance Events subsystem. It is the most
versatile and widely-used profiling interface.

```
perf_events sources:
┌────────────────┐
│  Hardware PMU  │  CPU cycle counters, cache misses, branch mispredictions
│  (ring 0 hw)   │  → perf_event_type = PERF_TYPE_HARDWARE
├────────────────┤
│ Software events│  context switches, page faults, CPU migrations
│  (kernel)      │  → perf_event_type = PERF_TYPE_SOFTWARE
├────────────────┤
│  Tracepoints   │  any kernel tracepoint as perf event
│                │  → perf_event_type = PERF_TYPE_TRACEPOINT
├────────────────┤
│ kprobes/uprobes│  attached via perf_event_open syscall
│                │  → perf_event_type = PERF_TYPE_PROBE
└────────────────┘
```

### 10.2 The perf_event_open Syscall

```c
#include <linux/perf_event.h>
#include <sys/syscall.h>

int perf_event_open(struct perf_event_attr *attr,
                    pid_t pid,      // -1 = all processes
                    int cpu,        // -1 = all CPUs
                    int group_fd,   // -1 = no group
                    unsigned long flags);
```

The `struct perf_event_attr` is the central configuration:

```c
struct perf_event_attr {
    __u32 type;          // PERF_TYPE_*
    __u32 size;          // sizeof(struct perf_event_attr)
    __u64 config;        // event-specific config
    union {
        __u64 sample_period;  // sample every N events
        __u64 sample_freq;    // sample at N Hz (PERF_FLAG_FD_NO_GROUP)
    };
    __u64 sample_type;   // what to record per sample (IP, TID, TIME, etc.)
    __u64 read_format;
    // ... many bit flags:
    __u64 disabled       :1; // start disabled
    __u64 inherit        :1; // inherit across fork
    __u64 pinned         :1; // pin to CPU (for PMU)
    __u64 exclusive      :1;
    __u64 exclude_user   :1; // don't count userspace
    __u64 exclude_kernel :1; // don't count kernel
    // ...
};
```

---

## 11. eBPF

### 11.1 What is eBPF?

**eBPF** (extended Berkeley Packet Filter) is the most powerful and modern
Linux observability/tracing technology. It allows you to write small programs
that run **safely inside the kernel** without needing kernel modules.

**Mental model**: eBPF is to the kernel what JavaScript is to a browser —
a safe sandbox where you can run arbitrary code.

```
Traditional approach (dangerous):
  Write kernel module → can crash kernel, security risk

eBPF approach (safe):
  Write eBPF program (C-like)
  → compile to eBPF bytecode (LLVM/Clang)
  → load into kernel
  → kernel VERIFIER checks for:
       * no infinite loops
       * no out-of-bounds memory access
       * no unsafe pointer arithmetic
       * bounded execution time
  → if verified: JIT-compile to native machine code
  → attach to probe point
  → runs in kernel when probe fires
```

### 11.2 eBPF Program Lifecycle

```
Developer writes:         bpf_prog.c (restricted C)
                              │
                        clang -target bpf
                              │
                         bytecode.o (ELF with BPF sections)
                              │
                        bpf(BPF_PROG_LOAD, ...)
                              │
                        ┌─────▼──────┐
                        │  VERIFIER  │ → rejects unsafe programs
                        └─────┬──────┘
                              │ verified
                        ┌─────▼──────┐
                        │ JIT Compiler│ → native machine code
                        └─────┬──────┘
                              │
                    perf_event_open / bpf(BPF_RAW_TRACEPOINT_OPEN, ...)
                              │
                        Attached to probe
                              │
                   Runs in kernel on every probe hit
```

### 11.3 eBPF Maps — Kernel↔Userspace Communication

eBPF programs can't write to files or call arbitrary functions. They communicate
via **maps** — shared memory between kernel eBPF programs and userspace.

```
Map types:
┌────────────────────────────┬──────────────────────────────────────┐
│ BPF_MAP_TYPE_HASH          │ Hash table: key→value                │
│ BPF_MAP_TYPE_ARRAY         │ Fixed-size array                     │
│ BPF_MAP_TYPE_RINGBUF       │ Ring buffer (most efficient for events)│
│ BPF_MAP_TYPE_PERF_EVENT_ARRAY│ Per-CPU perf events               │
│ BPF_MAP_TYPE_STACK_TRACE   │ Stack traces                         │
│ BPF_MAP_TYPE_LRU_HASH      │ LRU hash (auto-evicts old entries)   │
│ BPF_MAP_TYPE_PERCPU_HASH   │ Per-CPU hash (no lock needed!)       │
└────────────────────────────┴──────────────────────────────────────┘
```

### 11.4 eBPF Program Types (Probe-relevant)

```c
BPF_PROG_TYPE_KPROBE          // kprobe/kretprobe
BPF_PROG_TYPE_TRACEPOINT      // kernel tracepoints
BPF_PROG_TYPE_PERF_EVENT      // perf events (sampling, PMU)
BPF_PROG_TYPE_RAW_TRACEPOINT  // raw tracepoints (faster, less safe)
BPF_PROG_TYPE_UPROBE          // uprobes (via BPF_LINK)
BPF_PROG_TYPE_LSM             // Linux Security Module hooks
BPF_PROG_TYPE_FENTRY/FEXIT    // ftrace-based (fastest!)
```

### 11.5 bpf_helpers — What eBPF Programs Can Call

```c
// Timing
u64 bpf_ktime_get_ns(void);          // monotonic nanoseconds
u64 bpf_ktime_get_boot_ns(void);

// Process info
u64 bpf_get_current_pid_tgid(void);  // upper 32: tgid, lower 32: pid
u64 bpf_get_current_uid_gid(void);
long bpf_get_current_comm(void *buf, u32 size); // process name

// Memory
long bpf_probe_read_kernel(void *dst, u32 size, const void *src);
long bpf_probe_read_user(void *dst, u32 size, const void *src);
long bpf_probe_read_user_str(void *dst, u32 size, const void *src);
// → All reads may fail (invalid pointer) — must check return value!

// Maps
void *bpf_map_lookup_elem(struct bpf_map *map, const void *key);
long bpf_map_update_elem(struct bpf_map *map, const void *key,
                          const void *value, u64 flags);
long bpf_map_delete_elem(struct bpf_map *map, const void *key);

// Ring buffer (modern)
void *bpf_ringbuf_reserve(struct bpf_map *ringbuf, u64 size, u64 flags);
void bpf_ringbuf_submit(void *data, u64 flags);
void bpf_ringbuf_discard(void *data, u64 flags);

// Tracing output (legacy)
long bpf_perf_event_output(void *ctx, struct bpf_map *map,
                            u64 flags, void *data, u64 size);

// Stack traces
long bpf_get_stackid(void *ctx, struct bpf_map *map, u64 flags);
long bpf_get_stack(void *ctx, void *buf, u32 size, u64 flags);

// Printing (debug only, goes to /sys/kernel/debug/tracing/trace_pipe)
long bpf_trace_printk(const char *fmt, u32 fmt_size, ...);
long bpf_printk(const char *fmt, ...);  // macro wrapper
```

---

## 12. SystemTap & DTrace Concepts

### 12.1 SystemTap

SystemTap is a high-level scripting language for kernel tracing. It compiles
scripts into kernel modules at runtime.

```
SystemTap script (.stp)
    │
  stap compiler
    │
  C kernel module source
    │
  gcc compile
    │
  .ko kernel module
    │
  insmod → runs → collects data
    │
  rmmod on exit
```

**Example script** (conceptual, shows the abstraction level):

```c
// SystemTap script — not a C implementation, just to show the idea
probe kernel.function("do_sys_open") {
    printf("PID %d opened: %s\n", pid(), user_string($filename));
}
```

### 12.2 DTrace Concepts (from Solaris, ported to Linux)

DTrace introduced the **D language** and the concept of:
- **Probes**: identified by `provider:module:function:name`
- **Predicates**: `/condition/` before action block
- **Actions**: what to do when probe fires
- **Aggregations**: built-in statistical summaries (`@hist`, `@count`, `@sum`)

Linux's **bpftrace** is essentially DTrace for Linux.

### 12.3 bpftrace — DTrace-like for Linux

```
# bpftrace "one-liner" examples:

# Trace all open() calls:
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s opened %s\n", comm, str(args->filename)); }'

# Histogram of read() sizes:
bpftrace -e 'tracepoint:syscalls:sys_enter_read { @size = hist(args->count); }'

# Stack trace on kmalloc > 1MB:
bpftrace -e 'kprobe:__kmalloc /arg0 > 1048576/ { @[kstack] = count(); }'

# uprobe on specific binary:
bpftrace -e 'uprobe:/usr/bin/bash:readline { printf("readline called\n"); }'
```

---

## 13. Kernel Probe Mechanics Deep Internals

### 13.1 Text Patching — How the Kernel Modifies Its Own Code

The kernel's text segment is normally **read-only** (WP bit in CR0 register).
To patch instructions, the kernel must:

```c
// Simplified view of kernel text patching:

// 1. Disable write protection:
//    On x86: clear WP bit in CR0 (with preemption/IRQ disabled!)
//    Modern kernels use text_poke_bp() which is safer

// 2. text_poke_bp() algorithm:
//    a. Replace first byte with INT3 (atomic 1-byte write)
//    b. Use IPI (Inter-Processor Interrupt) to sync all CPUs
//    c. Write remaining bytes
//    d. Another IPI to sync
//    e. Replace first byte with final opcode

// This ensures no CPU ever sees a partially-patched instruction
```

### 13.2 Probe Blacklisting — Why Some Addresses Can't Be Probed

```c
// Addresses that CANNOT be kprobed:
// 1. The kprobe infrastructure itself (infinite recursion!)
//    - kprobe_handler(), do_int3(), etc.
// 2. Functions critical during exception handling
// 3. Functions that run with invalid stack (OOPS handlers)
// 4. Notrace functions (__kprobes annotation)

// Marked in kernel source with:
__kprobes void some_critical_function(void) { ... }
// or:
NOKPROBE_SYMBOL(some_critical_function);

// Check if address is safe:
cat /sys/kernel/debug/kprobes/blacklist
```

### 13.3 Probe Hit on SMP (Multi-CPU) Systems

```
CPU 0                     CPU 1
  │                         │
  │                         │── executing near probe address
  │── installs probe         │
  │   (patches INT3)         │
  │                         │── RACES: may have already fetched
  │                         │   original instruction into
  │                         │   decode pipeline / instruction cache
  │                         │
  └── IPI (flush icache) ──>│── flushes instruction cache
                            │── now sees INT3
```

### 13.4 The kprobe Hash Table

```
kprobes are stored in a hash table keyed by probe address:

hash_table[hash(address)] = {
    kprobe_A at 0xffffffffc0001234,
    kprobe_B at 0xffffffffc0009abc,
    ...
}

On INT3 exception:
  1. Get rip from pt_regs
  2. Look up hash_table[hash(rip - 1)]
     (rip-1 because CPU advances rip past INT3)
  3. Find matching kprobe
  4. Call handlers
  
Time complexity: O(1) average for probe dispatch
```

### 13.5 RISC Architecture Considerations (ARM64)

On ARM64, instructions are always 4 bytes (fixed-width). You can't just
replace 1 byte — you replace the whole 4-byte instruction with:
```
BRK #0  (ARM64 breakpoint)
```
Single-stepping is also different — ARM64 uses hardware step-by-step mode
via the MDSCR_EL1 register's SS (software step) bit.

---

## 14. C Implementations

### 14.1 Kernel Module: Basic kprobe

```c
// file: kprobe_example.c
// Build: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
// Load:  sudo insmod kprobe_example.ko
// Unload: sudo rmmod kprobe_example
// Log:   sudo dmesg -w

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ptrace.h>   // struct pt_regs
#include <linux/uaccess.h>  // copy_from_user, probe_kernel_read

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Master");
MODULE_DESCRIPTION("kprobe example on do_sys_openat2");

/* ─────────────────────────────────────────────────
 * Target: do_sys_openat2 — the core 'openat' syscall
 *
 * Prototype (kernel 5.x+):
 *   long do_sys_openat2(int dfd, const char __user *filename,
 *                       struct open_how *how);
 *
 * Arguments (System V AMD64 ABI):
 *   rdi = dfd      (directory file descriptor, AT_FDCWD = -100)
 *   rsi = filename (userspace pointer to filename string)
 *   rdx = how      (struct open_how pointer)
 * ───────────────────────────────────────────────── */

static int pre_handler(struct kprobe *p, struct pt_regs *regs)
{
    /* rsi holds the userspace pointer to the filename string */
    const char __user *filename = (const char __user *)regs->si;
    char buf[256];
    long ret;

    /*
     * CRITICAL: We cannot use strncpy() — the pointer is in USER space.
     * We must use strncpy_from_user() which:
     *   1. Validates the pointer is in user address range
     *   2. Handles page faults safely if the page isn't loaded
     *   3. Returns -EFAULT if the pointer is invalid
     */
    ret = strncpy_from_user(buf, filename, sizeof(buf) - 1);
    if (ret < 0) {
        pr_info("kprobe: could not read filename (ret=%ld)\n", ret);
        return 0;
    }
    buf[ret] = '\0';

    pr_info("kprobe pre:  PID=%-6d COMM=%-16s dfd=%-4ld file=%s\n",
            current->pid,            /* current: pointer to current task */
            current->comm,           /* process name */
            (long)regs->di,          /* rdi = dfd */
            buf);

    return 0; /* 0 = continue normal execution */
}

static void post_handler(struct kprobe *p, struct pt_regs *regs,
                          unsigned long flags)
{
    /* Called AFTER the first instruction of do_sys_openat2 executes */
    /* At this point rip has advanced, registers may have changed */
    /* Typically used for timing (start time was saved in pre_handler) */
}

/* The kprobe structure — statically initialized */
static struct kprobe kp = {
    .symbol_name = "do_sys_openat2",  /* kernel will resolve address */
    .pre_handler  = pre_handler,
    .post_handler = post_handler,
};

static int __init kprobe_init(void)
{
    int ret;

    ret = register_kprobe(&kp);
    if (ret < 0) {
        pr_err("register_kprobe failed: %d\n", ret);
        /*
         * Common failure reasons:
         *   -EINVAL: address blacklisted / invalid
         *   -ENOMEM: no memory for kprobe slot
         *   -ENOENT: symbol not found
         */
        return ret;
    }

    pr_info("kprobe planted at %pS (addr=%px)\n",
            kp.addr, kp.addr);
    /* %pS: kernel pointer formatted as "symbol+offset" */
    /* %px: kernel pointer printed as hex (safe to print) */
    return 0;
}

static void __exit kprobe_exit(void)
{
    unregister_kprobe(&kp);
    pr_info("kprobe removed\n");
}

module_init(kprobe_init);
module_exit(kprobe_exit);
```

---

### 14.2 Kernel Module: kretprobe — Measuring Function Latency

```c
// file: kretprobe_latency.c
// Measures latency of vfs_read() — virtual filesystem read

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>     // ktime_t, ktime_get_ns()
#include <linux/ptrace.h>
#include <linux/hashtable.h>

MODULE_LICENSE("GPL");

/* Per-instance private data stored between entry and return */
struct latency_data {
    u64 entry_time_ns;  /* timestamp when function was entered */
};

/*
 * entry_handler: fires when vfs_read() is ENTERED
 * ri->data points to our per-instance private data
 */
static int entry_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    struct latency_data *data = (struct latency_data *)ri->data;
    data->entry_time_ns = ktime_get_ns();  /* monotonic time in nanoseconds */
    return 0;
}
NOKPROBE_SYMBOL(entry_handler);

/*
 * ret_handler: fires when vfs_read() RETURNS
 * At this point:
 *   regs->ax = return value of vfs_read()
 *   (positive = bytes read, negative = error code)
 */
static int ret_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    struct latency_data *data = (struct latency_data *)ri->data;
    u64 now = ktime_get_ns();
    u64 latency_ns = now - data->entry_time_ns;
    ssize_t retval = (ssize_t)regs_return_value(regs);
    /* regs_return_value(): arch-independent way to get return value */

    if (retval > 0) {
        /* Only log successful reads */
        pr_info("vfs_read: pid=%-6d %-16s retval=%-8zd latency=%llu ns (%llu us)\n",
                current->pid,
                current->comm,
                retval,
                latency_ns,
                latency_ns / 1000);
    }
    return 0;
}
NOKPROBE_SYMBOL(ret_handler);

static struct kretprobe krp = {
    .kp.symbol_name = "vfs_read",
    .entry_handler  = entry_handler,
    .handler        = ret_handler,
    .data_size      = sizeof(struct latency_data),
    /*
     * maxactive: max number of simultaneous instances.
     * If vfs_read can be called from NR_CPUS threads simultaneously,
     * set this to at least NR_CPUS.
     * 0 = kernel uses default (2 * NR_CPUS)
     */
    .maxactive       = 64,
};

static int __init krp_init(void)
{
    int ret = register_kretprobe(&krp);
    if (ret < 0) {
        pr_err("register_kretprobe failed: %d\n", ret);
        return ret;
    }
    pr_info("kretprobe on vfs_read@%px\n", krp.kp.addr);
    return 0;
}

static void __exit krp_exit(void)
{
    unregister_kretprobe(&krp);
    pr_info("kretprobe removed. Missed: %d\n", krp.nmissed);
    /* nmissed: times we couldn't fire because all instances were busy */
}

module_init(krp_init);
module_exit(krp_exit);
```

---

### 14.3 Makefile for Kernel Modules

```makefile
# Makefile

# obj-m: list of modules to build
obj-m += kprobe_example.o
obj-m += kretprobe_latency.o

# KDIR: path to kernel build directory for currently running kernel
KDIR := /lib/modules/$(shell uname -r)/build

# Default target: build
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Load all modules
load:
	sudo insmod kprobe_example.ko
	sudo insmod kretprobe_latency.ko

# Unload all modules
unload:
	sudo rmmod kretprobe_latency
	sudo rmmod kprobe_example

# Watch kernel log
log:
	sudo dmesg -w | grep -E "kprobe|kretprobe|vfs_read"
```

---

### 14.4 C: Using perf_event_open for kprobe via Userspace

```c
// file: perf_kprobe_userspace.c
// Attach a kprobe via perf_event_open (no kernel module needed!)
// Requires: Linux 4.17+, CAP_SYS_ADMIN or CAP_PERFMON

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>

/* ── Step 1: Create a kprobe PMU event via tracefs ── */

/*
 * The "dynamic PMU" approach:
 * 1. Write probe definition to /sys/kernel/debug/tracing/kprobe_events
 *    This creates a new event under /sys/kernel/debug/tracing/events/
 * 2. Read the event's "id" file to get the perf_event config value
 * 3. Open with perf_event_open using PERF_TYPE_TRACEPOINT + that id
 */

static int create_kprobe_event(const char *probe_name,
                                const char *symbol,
                                int *event_id)
{
    char path[256];
    char cmd[512];
    int fd;
    char id_buf[16];
    ssize_t n;

    /* Create the probe event */
    fd = open("/sys/kernel/debug/tracing/kprobe_events", O_WRONLY | O_APPEND);
    if (fd < 0) {
        perror("open kprobe_events");
        return -1;
    }

    /* Format: "p:GROUP/NAME SYMBOL" */
    snprintf(cmd, sizeof(cmd), "p:probe_user/%s %s", probe_name, symbol);
    if (write(fd, cmd, strlen(cmd)) < 0) {
        perror("write kprobe_events");
        close(fd);
        return -1;
    }
    close(fd);

    /* Read the event ID */
    snprintf(path, sizeof(path),
             "/sys/kernel/debug/tracing/events/probe_user/%s/id",
             probe_name);
    fd = open(path, O_RDONLY);
    if (fd < 0) {
        perror("open event id");
        return -1;
    }
    n = read(fd, id_buf, sizeof(id_buf) - 1);
    close(fd);
    if (n <= 0) {
        fprintf(stderr, "failed to read event id\n");
        return -1;
    }
    id_buf[n] = '\0';
    *event_id = atoi(id_buf);
    return 0;
}

static void delete_kprobe_event(const char *probe_name)
{
    int fd;
    char cmd[256];

    fd = open("/sys/kernel/debug/tracing/kprobe_events", O_WRONLY | O_APPEND);
    if (fd < 0) return;

    /* "-:GROUP/NAME" removes the probe */
    snprintf(cmd, sizeof(cmd), "-:probe_user/%s", probe_name);
    write(fd, cmd, strlen(cmd));
    close(fd);
}

/* ── Ring buffer layout for perf events ── */
/*
 * perf_event_open returns an fd.
 * We mmap 1+N pages: first page is struct perf_event_mmap_page (metadata),
 * remaining N pages form a ring buffer of perf_event_header + data records.
 */

struct perf_event_mmap_page; /* forward decl from linux/perf_event.h */

/* Sample record layout for PERF_SAMPLE_RAW */
struct sample_record {
    struct perf_event_header header;
    /* additional fields depend on sample_type */
    __u32 size;
    char data[];  /* raw tracepoint data */
};

int main(void)
{
    int event_id;
    int perf_fd;
    void *mmap_buf;
    const int mmap_pages = 16;  /* ring buffer size: 16 * 4096 bytes */
    const size_t mmap_size = (mmap_pages + 1) * 4096;

    /* ── Step 1: Create kprobe ── */
    printf("[*] Creating kprobe on do_sys_openat2...\n");
    if (create_kprobe_event("my_openat", "do_sys_openat2", &event_id) < 0) {
        fprintf(stderr, "Failed to create kprobe event\n");
        return 1;
    }
    printf("[+] Event ID: %d\n", event_id);

    /* ── Step 2: Open perf event ── */
    struct perf_event_attr attr = {
        .type            = PERF_TYPE_TRACEPOINT,
        .size            = sizeof(attr),
        .config          = (__u64)event_id,  /* the tracepoint ID we just got */
        .sample_period   = 1,       /* sample EVERY event (no skipping) */
        .sample_type     = PERF_SAMPLE_RAW | PERF_SAMPLE_TID | PERF_SAMPLE_TIME,
        .disabled        = 1,       /* start disabled, enable manually */
        .wakeup_events   = 1,       /* wake up reader after 1 event */
    };

    /* pid=-1: all processes; cpu=0: CPU 0 only; group_fd=-1: no group */
    perf_fd = (int)syscall(SYS_perf_event_open, &attr,
                           -1, 0, -1, PERF_FLAG_FD_CLOEXEC);
    if (perf_fd < 0) {
        perror("perf_event_open");
        delete_kprobe_event("my_openat");
        return 1;
    }

    /* ── Step 3: mmap ring buffer ── */
    mmap_buf = mmap(NULL, mmap_size, PROT_READ | PROT_WRITE,
                    MAP_SHARED, perf_fd, 0);
    if (mmap_buf == MAP_FAILED) {
        perror("mmap");
        close(perf_fd);
        delete_kprobe_event("my_openat");
        return 1;
    }

    /* ── Step 4: Enable the probe ── */
    ioctl(perf_fd, PERF_EVENT_IOC_RESET, 0);
    ioctl(perf_fd, PERF_EVENT_IOC_ENABLE, 0);
    printf("[+] Probe enabled. Watching for 5 seconds...\n");

    /*
     * ── Step 5: Read events from ring buffer ──
     *
     * The ring buffer protocol:
     *   metadata_page->data_head: written by kernel (where kernel wrote to)
     *   metadata_page->data_tail: written by us    (where we read to)
     *   data_head > data_tail: unread data available
     */
    struct perf_event_mmap_page *meta =
        (struct perf_event_mmap_page *)mmap_buf;
    char *data_buf = (char *)mmap_buf + 4096;  /* ring buffer starts at page 1 */
    __u64 data_mask = ((__u64)mmap_pages * 4096) - 1;

    time_t deadline = time(NULL) + 5;
    __u64 tail = meta->data_tail;

    while (time(NULL) < deadline) {
        /* Memory barrier: ensure we read data_head after any data */
        __u64 head = __atomic_load_n(&meta->data_head, __ATOMIC_ACQUIRE);

        while (tail < head) {
            /* Read record header from ring buffer (handles wrap-around) */
            struct perf_event_header hdr;
            __u64 offset = tail & data_mask;
            memcpy(&hdr, data_buf + offset, sizeof(hdr));

            if (hdr.type == PERF_RECORD_SAMPLE) {
                printf("  [SAMPLE] size=%u type=%u\n", hdr.size, hdr.type);
                /* In real code: parse TID, TIME, RAW fields here */
            } else if (hdr.type == PERF_RECORD_LOST) {
                printf("  [LOST EVENTS!]\n");
            }

            tail += hdr.size;
        }

        /* Update tail pointer to tell kernel we've consumed these events */
        __atomic_store_n(&meta->data_tail, tail, __ATOMIC_RELEASE);

        usleep(10000);  /* 10ms sleep */
    }

    /* ── Cleanup ── */
    printf("[*] Disabling probe...\n");
    ioctl(perf_fd, PERF_EVENT_IOC_DISABLE, 0);
    munmap(mmap_buf, mmap_size);
    close(perf_fd);
    delete_kprobe_event("my_openat");
    printf("[+] Done.\n");
    return 0;
}
```

**Compile and run:**
```bash
gcc -O2 -o perf_kprobe_userspace perf_kprobe_userspace.c
sudo ./perf_kprobe_userspace
```

---

### 14.5 C: eBPF Program (BPF C) — kprobe with ringbuf

```c
// file: kprobe_bpf.c
// BPF program that runs IN THE KERNEL on each openat2 call
// Compiled with: clang -O2 -target bpf -c kprobe_bpf.c -o kprobe_bpf.o

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <linux/ptrace.h>

/* ── Shared event structure ── */
struct event {
    __u32 pid;
    __u32 tid;
    __u64 timestamp_ns;
    char  comm[16];        /* process name */
    char  filename[256];   /* file being opened */
    __s32 dfd;
};

/* ── BPF Map: Ring Buffer ── */
/*
 * SEC(".maps") places this in a special ELF section.
 * The loader (libbpf) reads this section to create the map.
 */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);  /* 256 KB ring buffer */
} events SEC(".maps");

/*
 * SEC("kprobe/do_sys_openat2"):
 *   Tells libbpf to attach this program as a kprobe on do_sys_openat2
 *
 * BPF_KPROBE macro: sets up correct argument extraction
 *   ctx is the raw pt_regs *, but BPF_KPROBE wraps it cleanly
 */
SEC("kprobe/do_sys_openat2")
int BPF_KPROBE(probe_openat2, int dfd, const char *filename,
               struct open_how *how)
{
    struct event *e;

    /*
     * Reserve space in ring buffer.
     * If ring buffer is full, this returns NULL → we drop the event.
     * BPF_RB_NO_WAKEUP: don't wake reader immediately (batch for efficiency)
     */
    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;  /* drop event, ring buffer full */

    /* Fill event data */
    e->pid = bpf_get_current_pid_tgid() >> 32;   /* upper 32 bits = PID */
    e->tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    e->timestamp_ns = bpf_ktime_get_ns();
    e->dfd = dfd;

    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    /*
     * Read filename from USER space.
     * bpf_probe_read_user_str: reads a null-terminated string from user memory
     * Returns number of bytes read (including null) or negative error.
     * SAFE: if 'filename' is bad pointer, returns -EFAULT without crashing.
     */
    bpf_probe_read_user_str(&e->filename, sizeof(e->filename), filename);

    /* Submit to ring buffer — reader in userspace will wake up */
    bpf_ringbuf_submit(e, 0);

    return 0;
}

/*
 * All BPF programs must have a license declaration.
 * GPL is required for many BPF helper functions.
 */
char _license[] SEC("license") = "GPL";
```

---

### 14.6 C: libbpf Loader — Userspace BPF Program Manager

```c
// file: kprobe_loader.c
// Loads the BPF program, attaches probe, reads events from ring buffer
// Compile: gcc -O2 -o kprobe_loader kprobe_loader.c -lbpf -lelf -lz

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

/* Must match the struct in kprobe_bpf.c */
struct event {
    __u32 pid;
    __u32 tid;
    __u64 timestamp_ns;
    char  comm[16];
    char  filename[256];
    __s32 dfd;
};

static volatile int stop = 0;

static void sig_handler(int sig) { stop = 1; }

/*
 * Ring buffer callback: called by libbpf for each event
 * Return value: 0 = success, negative = error (stops processing)
 */
static int handle_event(void *ctx, void *data, size_t data_sz)
{
    const struct event *e = data;

    printf("%-6u %-6u %-16s dfd=%-4d %s\n",
           e->pid, e->tid, e->comm, e->dfd, e->filename);
    return 0;
}

int main(int argc, char **argv)
{
    struct bpf_object *obj;
    struct bpf_program *prog;
    struct bpf_link *link;
    struct ring_buffer *rb;
    struct bpf_map *map;
    int err;

    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    /* ── Step 1: Open BPF object file ── */
    obj = bpf_object__open_file("kprobe_bpf.o", NULL);
    if (!obj) {
        fprintf(stderr, "Failed to open BPF object: %s\n", strerror(errno));
        return 1;
    }

    /* ── Step 2: Load (verify + JIT) into kernel ── */
    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %d\n", err);
        bpf_object__close(obj);
        return 1;
    }

    /* ── Step 3: Find and attach the kprobe program ── */
    prog = bpf_object__find_program_by_name(obj, "probe_openat2");
    if (!prog) {
        fprintf(stderr, "Program not found\n");
        bpf_object__close(obj);
        return 1;
    }

    /*
     * bpf_program__attach():
     *   libbpf reads the SEC() annotation ("kprobe/do_sys_openat2")
     *   and automatically creates the right kprobe attachment.
     */
    link = bpf_program__attach(prog);
    if (!link) {
        fprintf(stderr, "Failed to attach: %s\n", strerror(errno));
        bpf_object__close(obj);
        return 1;
    }

    /* ── Step 4: Set up ring buffer reader ── */
    map = bpf_object__find_map_by_name(obj, "events");
    if (!map) {
        fprintf(stderr, "Ring buffer map not found\n");
        goto cleanup;
    }

    rb = ring_buffer__new(bpf_map__fd(map), handle_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }

    /* ── Step 5: Poll for events ── */
    printf("%-6s %-6s %-16s %-9s %s\n", "PID", "TID", "COMM", "DFD", "FILE");
    printf("%-6s %-6s %-16s %-9s %s\n",
           "------", "------", "----------------", "---------",
           "--------------------");

    while (!stop) {
        /*
         * ring_buffer__poll():
         *   Blocks for up to timeout_ms milliseconds
         *   Calls handle_event() for each pending event
         *   Returns number of events processed, or negative on error
         */
        err = ring_buffer__poll(rb, 100 /* ms */);
        if (err < 0 && err != -EINTR) {
            fprintf(stderr, "Ring buffer poll error: %d\n", err);
            break;
        }
    }

    ring_buffer__free(rb);

cleanup:
    bpf_link__destroy(link);
    bpf_object__close(obj);
    printf("\nDone.\n");
    return 0;
}
```

---

### 14.7 C: uprobe via tracefs (Shell + C)

```c
// file: uprobe_bash_readline.c
// Traces bash's readline() function via tracefs
// No kernel module, no BPF — pure tracefs interface

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>

#define TRACEFS "/sys/kernel/debug/tracing"

/*
 * To find the offset of readline in bash:
 *   readelf -s /bin/bash | grep readline
 *   objdump -d /bin/bash | grep -A5 "<readline>"
 *
 * Or use:
 *   nm /bin/bash | grep readline
 *
 * For a dynamic symbol in a shared lib:
 *   nm -D /usr/lib/x86_64-linux-gnu/libreadline.so | grep readline
 *   readelf -Ws /usr/lib/x86_64-linux-gnu/libreadline.so
 */

static int write_file(const char *path, const char *content)
{
    int fd = open(path, O_WRONLY | O_APPEND);
    if (fd < 0) {
        fprintf(stderr, "open(%s): %s\n", path, strerror(errno));
        return -1;
    }
    ssize_t n = write(fd, content, strlen(content));
    close(fd);
    if (n < 0) {
        fprintf(stderr, "write(%s, \"%s\"): %s\n", path, content, strerror(errno));
        return -1;
    }
    return 0;
}

static long get_symbol_offset(const char *binary, const char *symbol)
{
    char cmd[512];
    char line[256];
    FILE *fp;
    long offset = -1;

    /* Use nm to get symbol offset */
    snprintf(cmd, sizeof(cmd), "nm -D %s 2>/dev/null | grep ' %s$'", binary, symbol);
    fp = popen(cmd, "r");
    if (!fp) return -1;

    if (fgets(line, sizeof(line), fp)) {
        offset = (long)strtoul(line, NULL, 16);
    }
    pclose(fp);
    return offset;
}

int main(int argc, char **argv)
{
    const char *binary = "/bin/bash";
    const char *symbol = "readline";
    long offset;
    char probe_def[512];
    char enable_path[256];
    char trace_pipe[256];
    FILE *fp;
    char buf[1024];

    /* ── Step 1: Find symbol offset ── */
    offset = get_symbol_offset(binary, symbol);
    if (offset < 0) {
        /* Fallback: readline might be in libreadline */
        binary = "/usr/lib/x86_64-linux-gnu/libreadline.so.8";
        offset = get_symbol_offset(binary, "readline");
    }
    if (offset < 0) {
        fprintf(stderr, "Could not find readline symbol\n");
        return 1;
    }
    printf("[+] Found %s at offset 0x%lx in %s\n", symbol, offset, binary);

    /* ── Step 2: Define uprobe event ──
     *
     * Format: p[:[GROUP/]NAME] PATH:OFFSET [ARGS]
     *   p              = probe (not return probe)
     *   :myprobes/bash_readline = group/name for the event
     *   PATH           = path to the binary/library
     *   OFFSET         = byte offset from file start
     *
     * Return probe format: r:GROUP/NAME PATH:OFFSET
     */
    snprintf(probe_def, sizeof(probe_def),
             "p:myprobes/bash_readline %s:0x%lx",
             binary, offset);

    printf("[+] Writing: %s\n", probe_def);
    if (write_file(TRACEFS "/uprobe_events", probe_def) < 0)
        return 1;

    /* ── Step 3: Enable the event ── */
    snprintf(enable_path, sizeof(enable_path),
             TRACEFS "/events/myprobes/bash_readline/enable");
    if (write_file(enable_path, "1") < 0)
        goto cleanup;

    /* ── Step 4: Enable tracing ── */
    if (write_file(TRACEFS "/tracing_on", "1") < 0)
        goto cleanup;

    /* ── Step 5: Read from trace_pipe ── */
    snprintf(trace_pipe, sizeof(trace_pipe), TRACEFS "/trace_pipe");
    fp = fopen(trace_pipe, "r");
    if (!fp) {
        perror("open trace_pipe");
        goto cleanup;
    }

    printf("[+] Watching for bash readline calls (Ctrl+C to stop)...\n");
    printf("    Start typing in a bash shell!\n\n");

    while (fgets(buf, sizeof(buf), fp)) {
        /* trace_pipe output format:
         *   TASK-PID   [CPU] FLAGS TIMESTAMP: FUNCTION
         *   bash-12345 [002] d... 12345.678901: bash_readline: (0x...)
         */
        if (strstr(buf, "bash_readline"))
            printf("%s", buf);
    }

    fclose(fp);

cleanup:
    /* ── Cleanup: disable and remove probe ── */
    write_file(enable_path, "0");
    write_file(TRACEFS "/uprobe_events", "-:myprobes/bash_readline");
    printf("\n[+] Uprobe removed.\n");
    return 0;
}
```

---

## 15. Rust Implementations

### 15.1 Rust: eBPF with Aya Framework

**Aya** is the premier Rust eBPF library. It implements the entire eBPF
toolchain in pure Rust — no C/LLVM dependency at runtime.

```
Architecture:
┌────────────────────────────────────────┐
│         Userspace (Rust)               │
│   aya crate: load, attach, read maps   │
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│         BPF program (Rust)             │
│   aya-bpf crate: BPF-safe Rust code   │
│   Compiled to BPF bytecode            │
└────────────────────────────────────────┘
```

**Project structure:**
```
kprobe-monitor/
├── Cargo.toml              (workspace)
├── kprobe-monitor/         (userspace binary)
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
├── kprobe-monitor-ebpf/    (BPF program)
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
└── kprobe-monitor-common/  (shared types)
    ├── Cargo.toml
    └── src/
        └── lib.rs
```

---

### 15.2 Common Types (shared between BPF and userspace)

```rust
// kprobe-monitor-common/src/lib.rs
//
// This crate is compiled for BOTH:
//   - native target (userspace) -- for parsing events
//   - bpf target                -- for creating events in kernel
//
// Therefore: no_std + no heap (BPF has no allocator)

#![no_std]

// Repr C: guarantees same memory layout in both compilations
// This is the data structure passed through the ring buffer
#[repr(C)]
#[derive(Clone, Copy)]
pub struct OpenEvent {
    pub pid: u32,
    pub tid: u32,
    pub uid: u32,
    pub timestamp_ns: u64,
    pub comm: [u8; 16],    // process name, null-terminated
    pub filename: [u8; 256], // file path, null-terminated
    pub dfd: i32,
    pub flags: u64,
}

// Required for BPF programs to use this type in maps
// (BPF verifier needs to know the size at compile time)
#[cfg(feature = "user")]
unsafe impl aya::Pod for OpenEvent {}
// Pod = "Plain Old Data" — safe to copy bytes directly
```

---

### 15.3 BPF Program in Rust (aya-bpf)

```rust
// kprobe-monitor-ebpf/src/main.rs
//
// Compiled with:
//   cargo build --target bpfel-unknown-none -Z build-std=core
//
// Notes:
//   - no_std: no standard library (kernel BPF doesn't have one)
//   - no main(): entry points are BPF program functions with #[kprobe]

#![no_std]
#![no_main]

// Panic handler: BPF verifier rejects programs with unreachable panic
// So we provide a minimal one
use aya_bpf::macros::panic;
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

use aya_bpf::{
    helpers::{
        bpf_get_current_comm,
        bpf_get_current_pid_tgid,
        bpf_get_current_uid_gid,
        bpf_ktime_get_ns,
        bpf_probe_read_user_str_bytes,
    },
    macros::{kprobe, map},
    maps::RingBuf,
    programs::ProbeContext,
    BpfContext,
};
use kprobe_monitor_common::OpenEvent;

/*
 * #[map]: tells aya to create this BPF map when the program loads
 * RingBuf: modern ring buffer (Linux 5.8+, preferred over perf_event_array)
 */
#[map]
static EVENTS: RingBuf = RingBuf::with_byte_size(256 * 1024, 0);

/*
 * #[kprobe]: attaches this function as a kprobe
 * The function name "do_sys_openat2" must match an existing kernel symbol.
 * ProbeContext: wraps pt_regs, provides safe accessors.
 */
#[kprobe]
pub fn kprobe_openat2(ctx: ProbeContext) -> u32 {
    match try_kprobe_openat2(&ctx) {
        Ok(()) => 0,
        Err(_) => 1,  // errors are non-fatal — just means event dropped
    }
}

/*
 * We use a Result-returning inner function to enable the ? operator.
 * BPF programs must not panic, so we convert all errors to Result.
 */
fn try_kprobe_openat2(ctx: &ProbeContext) -> Result<(), i64> {
    /*
     * Reserve space in ring buffer.
     * If full: returns None → we return Ok(()) (silently drop event).
     */
    let mut entry = match EVENTS.reserve::<OpenEvent>(0) {
        Some(e) => e,
        None => return Ok(()),
    };

    // Get a mutable reference to the reserved memory
    // SAFETY: ring buffer memory is valid and properly aligned
    let event: &mut OpenEvent = unsafe { entry.assume_init_mut() };

    /*
     * bpf_get_current_pid_tgid() returns a u64:
     *   upper 32 bits = TGID (Thread Group ID = what userspace calls "PID")
     *   lower 32 bits = PID  (what kernel calls "TID" = Thread ID)
     *
     * This naming confusion is a historical Linux artifact.
     * Userspace "PID" == kernel "TGID"
     * Userspace "TID" == kernel "PID"
     */
    let pid_tgid = bpf_get_current_pid_tgid();
    event.pid = (pid_tgid >> 32) as u32;   // userspace PID
    event.tid = (pid_tgid & 0xFFFFFFFF) as u32; // userspace TID

    let uid_gid = bpf_get_current_uid_gid();
    event.uid = (uid_gid & 0xFFFFFFFF) as u32;

    event.timestamp_ns = unsafe { bpf_ktime_get_ns() };

    // Get process name (comm)
    // Returns Result: Ok(bytes_written) or Err
    unsafe {
        bpf_get_current_comm(&mut event.comm as *mut _ as *mut _, 16);
    }

    /*
     * ProbeContext::arg::<T>(N) reads the Nth argument from registers.
     * On x86-64:
     *   arg(0) = rdi = int dfd
     *   arg(1) = rsi = const char __user *filename
     *   arg(2) = rdx = struct open_how *how
     */
    let dfd: i32 = ctx.arg(0).ok_or(1i64)?;
    let filename_ptr: u64 = ctx.arg(1).ok_or(1i64)?;
    let flags: u64 = ctx.arg(2).ok_or(1i64)?;  // simplified

    event.dfd = dfd;
    event.flags = flags;

    /*
     * Read filename from USER address space.
     * bpf_probe_read_user_str_bytes: safe userspace string read
     *   - handles page faults
     *   - returns Err(-EFAULT) for bad pointers
     *   - null-terminates the destination
     */
    let filename_slice = unsafe {
        core::slice::from_raw_parts_mut(
            event.filename.as_mut_ptr(),
            event.filename.len(),
        )
    };
    let _ = unsafe {
        bpf_probe_read_user_str_bytes(
            filename_ptr as *const u8,
            filename_slice,
        )
    };
    // We ignore the error — if we can't read the filename, we still
    // submit the event with an empty/partial filename.

    // Submit event to ring buffer — userspace reader will wake up
    entry.submit(0);
    Ok(())
}
```

---

### 15.4 Userspace Loader in Rust (aya)

```rust
// kprobe-monitor/src/main.rs
//
// [dependencies]
// aya = { version = "0.12", features = ["async_tokio"] }
// aya-log = "0.2"
// kprobe-monitor-common = { path = "../kprobe-monitor-common", features = ["user"] }
// tokio = { version = "1", features = ["full"] }
// log = "0.4"
// env_logger = "0.10"
// anyhow = "1.0"

use anyhow::{Context, Result};
use aya::{
    include_bytes_aligned,
    maps::RingBuf,
    programs::{KProbe, ProgramError},
    Bpf, BpfLoader,
};
use kprobe_monitor_common::OpenEvent;
use log::{error, info, warn};
use std::convert::TryInto;
use tokio::signal;

/*
 * include_bytes_aligned!: reads the compiled BPF .o file at compile time
 * and embeds it directly in the binary as a byte array.
 * Alignment to 32 bytes required by aya's BpfLoader.
 *
 * The path is relative to the workspace root.
 */
static BPF_CODE: &[u8] = include_bytes_aligned!(
    "../../target/bpfel-unknown-none/release/kprobe-monitor-ebpf"
);

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    // Check capabilities
    if !nix::unistd::Uid::effective().is_root() {
        eprintln!("Error: must run as root (or with CAP_BPF + CAP_SYS_ADMIN)");
        std::process::exit(1);
    }

    // ── Step 1: Load BPF object ──
    //
    // BpfLoader handles:
    //   - Parsing the ELF BPF object file
    //   - Creating all maps defined in .maps sections
    //   - Loading and verifying each BPF program
    //   - JIT compiling if enabled
    let mut bpf = BpfLoader::new()
        .load(BPF_CODE)
        .context("Failed to load BPF program")?;

    // ── Step 2: Install aya-log handler ──
    // aya-log intercepts bpf_printk() calls and routes to Rust's log crate
    if let Err(e) = aya_log::BpfLogger::init(&mut bpf) {
        warn!("Failed to initialize BPF logger: {e}");
    }

    // ── Step 3: Get and attach the kprobe program ──
    //
    // The string "kprobe_openat2" must match the function name
    // in the BPF program annotated with #[kprobe]
    let program: &mut KProbe = bpf
        .program_mut("kprobe_openat2")
        .context("Program not found")?
        .try_into()
        .context("Not a KProbe program")?;

    // load(): sends to kernel verifier + JIT compiler
    program.load().context("Failed to load kprobe program")?;

    // attach(fn_name, offset):
    //   fn_name = kernel function to probe
    //   offset = 0 means probe at function entry
    //   offset > 0 means probe at instruction at that offset from function start
    program
        .attach("do_sys_openat2", 0)
        .context("Failed to attach kprobe")?;

    info!("kprobe attached to do_sys_openat2");

    // ── Step 4: Get ring buffer map ──
    let ring_buf = bpf
        .map_mut("EVENTS")
        .context("Map not found")?;

    let mut ring_buf: RingBuf<_> = ring_buf
        .try_into()
        .context("Not a RingBuf")?;

    // ── Step 5: Print header ──
    println!("{:<8} {:<8} {:<8} {:<16} {:<10} {}",
             "PID", "TID", "UID", "COMM", "DFD", "FILENAME");
    println!("{}", "-".repeat(80));

    // ── Step 6: Event loop ──
    loop {
        tokio::select! {
            // Check for Ctrl+C
            _ = signal::ctrl_c() => {
                info!("Received Ctrl+C, exiting");
                break;
            }

            // Poll ring buffer for new events
            // In a real app, use epoll/tokio async fd instead of spin-polling
            _ = tokio::task::yield_now() => {
                // Process all available events in the ring buffer
                while let Some(item) = ring_buf.next() {
                    // item: &[u8] — raw bytes of the event
                    if item.len() < std::mem::size_of::<OpenEvent>() {
                        error!("Short event: {} bytes", item.len());
                        continue;
                    }

                    // SAFETY: we know the BPF program wrote an OpenEvent
                    // and we verified the size above
                    let event: &OpenEvent = unsafe {
                        &*(item.as_ptr() as *const OpenEvent)
                    };

                    // Convert comm (bytes) to string, stopping at null byte
                    let comm = std::str::from_utf8(&event.comm)
                        .unwrap_or("?")
                        .trim_end_matches('\0');

                    // Convert filename bytes to string
                    let filename = std::str::from_utf8(&event.filename)
                        .unwrap_or("?")
                        .trim_end_matches('\0');

                    println!("{:<8} {:<8} {:<8} {:<16} {:<10} {}",
                             event.pid, event.tid, event.uid,
                             comm, event.dfd, filename);
                }

                // Small sleep to avoid spinning CPU
                tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
            }
        }
    }

    // BPF program is automatically detached when `bpf` is dropped
    info!("Done");
    Ok(())
}
```

---

### 15.5 Rust: Low-level kprobe via /sys (no BPF)

```rust
// file: src/tracefs_probe.rs
// Control kprobes/uprobes via tracefs text interface
// Pure safe Rust, no unsafe blocks needed — just file I/O

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

const TRACEFS: &str = "/sys/kernel/debug/tracing";

/// Represents an active kprobe event in tracefs
pub struct KprobeEvent {
    group: String,
    name: String,
}

impl KprobeEvent {
    /// Creates a kprobe event at a kernel symbol.
    ///
    /// # Arguments
    /// - `group`: event group name (e.g., "myprobes")
    /// - `name`: event name (e.g., "open_probe")
    /// - `symbol`: kernel symbol (e.g., "do_sys_openat2")
    /// - `fetch_args`: optional fetch arguments (e.g., "filename=+0(%si):string")
    pub fn new(
        group: &str,
        name: &str,
        symbol: &str,
        fetch_args: Option<&str>,
    ) -> io::Result<Self> {
        // Format: p:[GROUP/]NAME SYMBOL [ARGS...]
        let probe_def = match fetch_args {
            Some(args) => format!("p:{}/{} {} {}", group, name, symbol, args),
            None => format!("p:{}/{} {}", group, name, symbol),
        };

        Self::write_probe_events(&probe_def)?;

        Ok(Self {
            group: group.to_string(),
            name: name.to_string(),
        })
    }

    /// Creates a kretprobe (return probe) event.
    pub fn new_return(
        group: &str,
        name: &str,
        symbol: &str,
        maxactive: Option<usize>,
    ) -> io::Result<Self> {
        // Format: r[MAXACTIVE]:[GROUP/]NAME SYMBOL
        let probe_def = match maxactive {
            Some(max) => format!("r{}:{}/{} {}", max, group, name, symbol),
            None => format!("r:{}/{} {}", group, name, symbol),
        };

        Self::write_probe_events(&probe_def)?;

        Ok(Self {
            group: group.to_string(),
            name: name.to_string(),
        })
    }

    fn write_probe_events(definition: &str) -> io::Result<()> {
        let path = format!("{}/kprobe_events", TRACEFS);
        let mut f = OpenOptions::new().write(true).append(true).open(&path)?;
        writeln!(f, "{}", definition)
    }

    /// Enable this event (start capturing).
    pub fn enable(&self) -> io::Result<()> {
        self.write_enable("1")
    }

    /// Disable this event (stop capturing).
    pub fn disable(&self) -> io::Result<()> {
        self.write_enable("0")
    }

    fn write_enable(&self, val: &str) -> io::Result<()> {
        let path = format!(
            "{}/events/{}/{}/enable",
            TRACEFS, self.group, self.name
        );
        fs::write(&path, val)
    }

    /// Read the event ID (needed for perf_event_open).
    pub fn event_id(&self) -> io::Result<u32> {
        let path = format!(
            "{}/events/{}/{}/id",
            TRACEFS, self.group, self.name
        );
        let content = fs::read_to_string(&path)?;
        content.trim().parse::<u32>().map_err(|e| {
            io::Error::new(io::ErrorKind::InvalidData, e)
        })
    }
}

/// Drop automatically removes the probe when it goes out of scope.
/// RAII: Resource Acquisition Is Initialization.
impl Drop for KprobeEvent {
    fn drop(&mut self) {
        // Suppress errors in drop — best effort cleanup
        let _ = self.disable();

        // Format: -:GROUP/NAME removes the probe
        let removal = format!("-:{}/{}", self.group, self.name);
        if let Ok(path) = std::fs::canonicalize(
            format!("{}/kprobe_events", TRACEFS)
        ) {
            if let Ok(mut f) = OpenOptions::new().write(true).append(true).open(path) {
                let _ = writeln!(f, "{}", removal);
            }
        }
    }
}

/// Global tracing on/off control
pub fn set_tracing_enabled(enabled: bool) -> io::Result<()> {
    let val = if enabled { "1" } else { "0" };
    fs::write(format!("{}/tracing_on", TRACEFS), val)
}

/// Returns an iterator over trace_pipe lines (blocking read)
pub fn trace_pipe_reader() -> io::Result<impl Iterator<Item = io::Result<String>>> {
    let file = File::open(format!("{}/trace_pipe", TRACEFS))?;
    Ok(BufReader::new(file).lines())
}

/// List all active kprobes in the system
pub fn list_active_kprobes() -> io::Result<Vec<String>> {
    let path = format!("{}/kprobes/list", TRACEFS)
        .replace("tracing/kprobes", "kprobes"); // adjust path
    // Actually: /sys/kernel/debug/kprobes/list
    let content = fs::read_to_string("/sys/kernel/debug/kprobes/list")?;
    Ok(content.lines().map(|s| s.to_string()).collect())
}

// ── Main: demonstrate the API ──

fn main() -> io::Result<()> {
    println!("Setting up kprobe via tracefs...");

    // Enable global tracing
    set_tracing_enabled(true)?;

    // Create a kprobe on do_sys_openat2
    // When RAII drops `probe`, it automatically removes itself
    let probe = KprobeEvent::new(
        "rust_probes",          // group
        "track_opens",          // name
        "do_sys_openat2",       // kernel symbol
        Some("dfd=%di:s32 filename=+0(%si):string flags=%dx:u64"),
    )?;

    // Enable the probe
    probe.enable()?;
    println!("Probe enabled. Event ID: {}", probe.event_id()?);
    println!("Watching trace_pipe for 10 seconds...\n");

    // Read from trace_pipe in a separate thread to avoid blocking
    let handle = std::thread::spawn(move || -> io::Result<()> {
        let reader = trace_pipe_reader()?;
        for line in reader.take(100) {  // read at most 100 lines
            match line {
                Ok(l) if l.contains("track_opens") => println!("{}", l),
                Ok(_) => {}
                Err(e) => eprintln!("read error: {}", e),
            }
        }
        Ok(())
    });

    std::thread::sleep(std::time::Duration::from_secs(10));

    // probe is dropped here → automatically removed from kernel
    drop(probe);
    set_tracing_enabled(false)?;

    println!("\nProbe removed (RAII cleanup).");

    // Wait for reader thread
    let _ = handle.join();
    Ok(())
}
```

---

### 15.6 Rust: Reading /proc/kallsyms for Symbol Resolution

```rust
// file: src/kallsyms.rs
// Resolve kernel symbol names to addresses
// Requires root (kallsyms shows real addresses only to root)

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};

/// A parsed entry from /proc/kallsyms
#[derive(Debug, Clone)]
pub struct KernelSymbol {
    pub address: u64,
    pub sym_type: char,
    /// T/t = text (code), D/d = data, B/b = bss, R/r = read-only data
    /// Capital = exported (visible to modules), lowercase = local
    pub name: String,
    pub module: Option<String>, // None = built-in kernel
}

/// Load all symbols from /proc/kallsyms
/// Returns a map from name → symbol
pub fn load_kallsyms() -> std::io::Result<HashMap<String, KernelSymbol>> {
    let file = File::open("/proc/kallsyms")?;
    let reader = BufReader::new(file);
    let mut map = HashMap::new();

    for line in reader.lines() {
        let line = line?;
        // Format: ADDRESS TYPE NAME [MODULE]
        // Example: ffffffff8120abc0 T do_sys_openat2
        // Example: ffffffffc0001234 t my_func [my_module]
        let mut parts = line.split_whitespace();

        let addr_str = match parts.next() { Some(s) => s, None => continue };
        let type_str = match parts.next() { Some(s) => s, None => continue };
        let name     = match parts.next() { Some(s) => s, None => continue };

        let address = u64::from_str_radix(addr_str, 16)
            .unwrap_or(0);

        let sym_type = type_str.chars().next().unwrap_or('?');

        // Module name is optional, format: [module_name]
        let module = parts.next().map(|s| {
            s.trim_start_matches('[').trim_end_matches(']').to_string()
        });

        let sym = KernelSymbol {
            address,
            sym_type,
            name: name.to_string(),
            module,
        };

        map.insert(name.to_string(), sym);
    }

    Ok(map)
}

/// Find the address of a single kernel symbol
pub fn resolve_symbol(name: &str) -> std::io::Result<Option<u64>> {
    let file = File::open("/proc/kallsyms")?;
    let reader = BufReader::new(file);

    for line in reader.lines() {
        let line = line?;
        let mut parts = line.split_whitespace();

        let addr_str = match parts.next() { Some(s) => s, None => continue };
        let _sym_type = parts.next();
        let sym_name  = match parts.next() { Some(s) => s, None => continue };

        if sym_name == name {
            let addr = u64::from_str_radix(addr_str, 16).unwrap_or(0);
            return Ok(Some(addr));
        }
    }
    Ok(None)
}

/// Find all symbols matching a prefix (useful for finding syscall variants)
pub fn find_symbols_with_prefix(prefix: &str) -> std::io::Result<Vec<KernelSymbol>> {
    let file = File::open("/proc/kallsyms")?;
    let reader = BufReader::new(file);
    let mut results = Vec::new();

    for line in reader.lines() {
        let line = line?;
        let mut parts = line.split_whitespace();

        let addr_str  = match parts.next() { Some(s) => s, None => continue };
        let type_str  = match parts.next() { Some(s) => s, None => continue };
        let name      = match parts.next() { Some(s) => s, None => continue };

        if name.starts_with(prefix) {
            let address = u64::from_str_radix(addr_str, 16).unwrap_or(0);
            let sym_type = type_str.chars().next().unwrap_or('?');
            let module = parts.next().map(|s| {
                s.trim_matches(|c| c == '[' || c == ']').to_string()
            });

            results.push(KernelSymbol {
                address,
                sym_type,
                name: name.to_string(),
                module,
            });
        }
    }
    Ok(results)
}

fn main() -> std::io::Result<()> {
    println!("Resolving kernel symbols...\n");

    // Find a specific symbol
    match resolve_symbol("do_sys_openat2")? {
        Some(addr) => println!("do_sys_openat2: 0x{:016x}", addr),
        None       => println!("do_sys_openat2: not found"),
    }

    // Find all TCP-related symbols
    println!("\nTCP symbols:");
    let tcp_syms = find_symbols_with_prefix("tcp_")?;
    for sym in tcp_syms.iter().take(10) {
        println!("  0x{:016x} {} {}{}",
                 sym.address,
                 sym.sym_type,
                 sym.name,
                 sym.module.as_deref().map(|m| format!(" [{}]", m))
                            .unwrap_or_default());
    }
    println!("  ... and {} more", tcp_syms.len().saturating_sub(10));

    Ok(())
}
```

---

## 16. Real-World Use Cases & Patterns

### 16.1 Latency Profiling Pattern

```
Goal: Find which kernel functions take > 1ms

Pattern:
  kretprobe on all vfs_* functions
  entry_handler: save timestamp in hash map (key=pid+cpu)
  ret_handler: compute delta, if > 1ms → record with stack trace

Implementation with eBPF (pseudo):
  BPF_MAP_TYPE_HASH: key={pid,cpu}, value=entry_timestamp
  BPF_MAP_TYPE_RINGBUF: emit {function, duration, stacktrace}

Result: /usr/share/bcc/tools/funclatency, wakeuptime, offcputime
```

### 16.2 Function Argument Capture Pattern

```
Goal: Log all arguments to a security-sensitive function

Pattern:
  kprobe on security_inode_create (file creation audit)
  Read: dir inode, filename, mode
  Correlate with process creds (uid, capabilities)

Tools: bpftrace, bcc's trace.py
```

### 16.3 Error Injection Pattern

```
Goal: Test how your code handles kernel errors

Pattern:
  kprobe on alloc_pages
  pre_handler: if (criteria met) { regs->ax = -ENOMEM; return 1; }
  (return 1 from pre_handler = override, don't execute original instruction)

This lets you simulate OOM conditions without actually running out of memory!
```

### 16.4 Performance Tracing Decision Tree

```
What do you want to trace?
│
├─ A specific known event? (syscall, scheduler event, network)
│   └─ Use TRACEPOINTS (lowest overhead, stable ABI)
│
├─ Any arbitrary kernel function?
│   └─ Use KPROBES
│       ├─ Want return value? → kretprobe
│       └─ Want entry only? → kprobe
│
├─ Userspace application?
│   └─ Use UPROBES
│       ├─ App has USDT probes? → prefer USDT (stable, faster NOP)
│       └─ No USDT? → instrument by offset/symbol
│
├─ ALL function calls in a subsystem?
│   └─ Use FTRACE (function tracer, lower overhead than kprobes)
│
├─ CPU performance counters (cycles, cache misses)?
│   └─ Use PERF_EVENTS with PERF_TYPE_HARDWARE
│
└─ Complex logic in the probe?
    └─ Use EBPF (safe programmability, maps for aggregation)
```

---

## 17. Performance Overhead Analysis

### 17.1 Overhead Comparison

```
Mechanism          | Cold (first hit) | Hot (cached)  | Notes
─────────────────────────────────────────────────────────────
kprobe (INT3)      | ~2000 ns         | ~800-1500 ns  | + cache miss
kprobe (optimized) | ~300 ns          | ~100-300 ns   | jump-based
kretprobe          | ~2x kprobe       | ~2x kprobe    | + stack manip
uprobe             | ~3000-8000 ns    | ~2000-5000 ns | + ring 3→0→3
tracepoint         | ~50 ns           | ~20-50 ns     | NOP when off = 0 ns
ftrace (mcount)    | ~100-500 ns      | ~50-200 ns    | depends on handler
eBPF via kprobe    | similar to kprobe + BPF execution (verifier-bounded)
eBPF via tracepoint| similar to tracepoint + BPF execution
```

### 17.2 Reducing Overhead — Expert Techniques

**1. Filter at probe site (BPF)**
```c
// BAD: wake up userspace for every event, filter there
// Generates millions of ring buffer entries per second

// GOOD: filter inside BPF program (in kernel)
SEC("kprobe/vfs_read")
int probe(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (pid != TARGET_PID) return 0;  // filtered in-kernel, zero userspace cost
    // ... rest of handler
}
```

**2. Use per-CPU maps (no locking)**
```c
// BAD: global hash map (contended spinlock on multi-CPU)
struct { __uint(type, BPF_MAP_TYPE_HASH); ... } global_map;

// GOOD: per-CPU array/hash (each CPU has own copy, no contention)
struct { __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY); ... } percpu_map;
```

**3. Aggregate in-kernel (histogram)**
```c
// BAD: send every latency value to userspace, compute histogram there
// BAD: wastes ring buffer bandwidth

// GOOD: compute histogram in BPF, send periodic snapshots
struct { __uint(type, BPF_MAP_TYPE_HISTOGRAM); ... } latency_hist;
// bpftrace: @hist = hist(latency);
```

**4. Use FENTRY/FEXIT instead of kprobe where possible**
```c
// kprobe: INT3 exception → expensive
// fentry: ftrace hook → CALL instruction replacement → cheaper

SEC("fentry/do_sys_openat2")
int BPF_PROG(fentry_openat, int dfd, const char *filename, struct open_how *how)
{
    // Same as kprobe but faster — no INT3 overhead
}
```

---

## 18. Security Considerations

### 18.1 Required Capabilities

```
CAP_SYS_ADMIN   — traditional all-powerful, needed for:
                  * register_kprobe (kernel module)
                  * /sys/kernel/debug/ access (mount debugfs)

CAP_PERFMON     — Linux 5.8+, specifically for:
                  * perf_event_open with probes
                  * eBPF observability programs

CAP_BPF         — Linux 5.8+, specifically for:
                  * bpf() syscall
                  * Loading eBPF programs/maps

Unprivileged eBPF: requires /proc/sys/kernel/unprivileged_bpf_disabled = 0
                   (often disabled in production — security risk!)
```

### 18.2 Security Risks of Probes

```
Risk 1: Information Disclosure
  kprobes/uprobes can read arbitrary kernel/user memory
  A malicious probe handler could exfiltrate sensitive data
  Mitigation: CAP_SYS_ADMIN/CAP_PERFMON guards

Risk 2: Kernel Panic via Bad Handler
  Kernel module kprobes can crash the kernel
  Mitigation: eBPF verifier prevents unsafe BPF programs
              Kernel modules require signing in Secure Boot

Risk 3: Probe on Security Functions
  Probing security_*(SELinux/AppArmor hooks) could bypass security
  Mitigation: Some functions are in kprobe blacklist

Risk 4: Timing Side-Channel
  Measuring precise timing of crypto operations can leak keys
  Mitigation: Constant-time crypto functions, careful probe placement

Risk 5: TOCTOU via Handler Modification
  Modifying regs in kprobe handler could bypass security checks
  Example: modify filename in do_sys_openat2 pre_handler!
  Mitigation: Auditing, Secure Boot, eBPF restrictions
```

### 18.3 eBPF Verifier — Your Safety Net

```
The verifier enforces:

1. CFG (Control Flow Graph) validity:
   - No unreachable instructions
   - All branches must terminate
   - No backward jumps that could loop forever
     (eBPF has bounded loops since Linux 5.3 — max 1 million iterations)

2. Type safety:
   - Pointer types tracked (kernel ptr vs user ptr vs map value)
   - Cannot pass kernel pointer to bpf_probe_read_user()
   - Cannot dereference unvalidated pointers

3. Stack bounds:
   - Max stack: 512 bytes
   - All stack accesses must be in bounds

4. Helper call validation:
   - Only approved helpers may be called
   - Argument types must match helper signature

5. No infinite loops (before 5.3) or bounded loops (5.3+)

6. Program size: max 1 million instructions (practical limit)
```

---

## 19. Debugging Probes Themselves

### 19.1 Common Failures and Diagnoses

```
Problem: register_kprobe() returns -EINVAL
Cause A: address is in kprobe blacklist
  → cat /sys/kernel/debug/kprobes/blacklist
Cause B: address is not aligned to instruction boundary
  → use symbol_name + offset carefully
Cause C: trying to probe a __kprobes function
  → the function itself is part of kprobe infrastructure

Problem: register_kprobe() returns -ENOENT
Cause: symbol_name not found in kernel symbol table
  → grep "do_sys_open" /proc/kallsyms
  → function may be named differently on this kernel version
  → function may be inlined (no separate symbol)

Problem: kretprobe nmissed is high
Cause: maxactive is too low
  → increase maxactive in kretprobe struct

Problem: uprobe fires but filename is garbage
Cause: reading kernel pointer as user pointer (or vice versa)
  → use strncpy_from_user() not strncpy() for user pointers

Problem: BPF program fails to verify
  → bpf_object__load() will print verifier log with error location
  → common: missing NULL check after map lookup
  → BPF_CORE_READ() instead of direct pointer dereference

Problem: high system load after probing
Cause: probed function is called millions of times per second
  → add pid/comm filter
  → use sampling (fire on every Nth hit using counter in per-CPU map)
```

### 19.2 Useful Diagnostic Commands

```bash
# List all active kprobes and their status:
cat /sys/kernel/debug/kprobes/list
# Format: ADDRESS STATUS SYMBOL+OFFSET [MODULE]
# Status: [OPTIMIZED], [DISABLED], [GONE]

# Check if kprobes are enabled on this kernel:
cat /sys/kernel/debug/kprobes/enabled

# List enabled tracepoints:
find /sys/kernel/debug/tracing/events -name "enable" -exec grep -l "^1$" {} \;

# Check BPF program status:
bpftool prog list
bpftool prog show id <ID>
bpftool map list
bpftool map dump id <MAP_ID>

# Show BPF program's verified instructions (JIT):
bpftool prog dump jited id <ID>
bpftool prog dump xlated id <ID>

# Check if a function is traceable:
grep "^do_sys_openat2$" /sys/kernel/debug/tracing/available_filter_functions

# ftrace function graph for a specific function:
echo do_sys_openat2 > /sys/kernel/debug/tracing/set_graph_function
echo function_graph > /sys/kernel/debug/tracing/current_tracer
cat /sys/kernel/debug/tracing/trace | head -50

# strace to understand syscalls at high level (before using probes):
strace -e trace=openat ls /tmp
```

---

## 20. Mental Models & Expert Intuition

### 20.1 The Probe Placement Mental Model

```
Before placing a probe, always ask:

1. FREQUENCY: How often does this code path execute?
   → High frequency (millions/sec): use sampling, filter aggressively, use ftrace
   → Low frequency (events/sec): any mechanism works

2. STABILITY: Will this symbol exist across kernel versions?
   → Yes: use tracepoints (stable API guarantee)
   → No: use kprobes + symbol_name lookup dynamically

3. CONTEXT: What context does this code run in?
   → Interrupt context: CANNOT sleep, CANNOT use user memory access
   → Process context: CAN sleep (but avoid it), CAN use user memory

4. COMPLETENESS: Do I need entry AND exit?
   → Both: kretprobe (saves you from managing two separate probes)
   → Entry only: kprobe
   → Return only: kretprobe with no entry_handler

5. DATA NEEDED:
   → Function arguments: available in pre_handler via pt_regs
   → Return value: only available in post (kretprobe ret_handler)
   → Execution time: need both entry time (pre) and exit time (ret)
   → Stack trace: use bpf_get_stackid() in eBPF
```

### 20.2 Cognitive Model for Complex Probe Chains

```
Think of probes as an event-driven state machine:

State: per-PID map entry (created on entry probe, deleted on return probe)

kprobe entry fires → create/update state entry
                  {pid: ..., entry_time: ..., arg0: ..., arg1: ...}

kretprobe fires   → read state entry
                  compute derived metrics (latency, etc.)
                  emit to ring buffer
                  delete state entry

This pattern (start state on entry, complete on exit) handles:
- Concurrent calls from different threads (keyed by pid/tid)
- Recursive calls (use a counter in state, not just a timestamp)
- Nested calls (push/pop stack in BPF map)
```

### 20.3 The Four Abstraction Levels

```
Level 1: Raw (hardest, most flexible)
  Direct kernel module with register_kprobe()
  Full C programming, direct pt_regs access
  Can do ANYTHING (including crash kernel)

Level 2: tracefs interface (shell-scriptable)
  echo to /sys/kernel/debug/tracing/kprobe_events
  Fetch argument syntax for structured extraction
  Output via trace_pipe

Level 3: eBPF + libbpf/aya (production-grade)
  Verified safety, portable, CO-RE (Compile Once, Run Everywhere)
  Maps for aggregation, ring buffers for events
  Modern standard for observability tools

Level 4: High-level tools (fastest to use)
  bpftrace, bcc, perf, SystemTap
  One-liners for instant insight
  Build on Level 3 internally

Expert strategy: Know Level 1 deeply → Use Level 4 in practice
Understanding the bottom lets you debug the top when it breaks.
```

### 20.4 Deliberate Practice Path for Mastery

```
Week 1-2: Foundations
  □ Build and load a hello-world kernel module
  □ Write a kprobe module that traces do_sys_openat2
  □ Read pt_regs, understand register conventions
  □ Trace with tracefs (echo commands)

Week 3-4: kretprobes & Timing
  □ Write kretprobe that measures vfs_read latency
  □ Accumulate histograms with atomic operations
  □ Understand per-instance data (data_size)

Week 5-6: eBPF
  □ Write a BPF C program with kprobe + ringbuf
  □ Write the libbpf loader
  □ Add hash map for per-PID statistics
  □ Practice the verifier error → fix cycle

Week 7-8: Rust (Aya)
  □ Port C BPF program to Rust aya-bpf
  □ Write the userspace Aya loader
  □ Handle errors idiomatically (Result everywhere)

Week 9-10: Advanced Patterns
  □ Implement function call graph tracing with eBPF
  □ Write a performance issue detective script in bpftrace
  □ Trace a real performance bug in a real application

Week 11-12: Production Skills
  □ Write probes with proper filtering (avoid high overhead)
  □ Handle probe failures gracefully (nmissed, dropped events)
  □ Understand CO-RE and BTF for kernel-version portability
```

### 20.5 The Expert's First-Principles Checklist

Every time you design a probe-based observability solution:

```
□ What question am I answering? (Latency? Error rate? Resource usage?)
□ What is the best kernel hook for this? (Tracepoint > kprobe when possible)
□ What is the call frequency? (Size ring buffer accordingly)
□ What context does the probe run in? (IRQ vs process context)
□ Do I need userspace data? (Use bpf_probe_read_user*)
□ Do I need kernel data? (Use bpf_probe_read_kernel*)
□ What is my filtering strategy? (In-kernel BPF filtering is free)
□ How do I handle dropped events? (nmissed counter, ring overflow counter)
□ How do I clean up? (RAII in Rust, unregister in C exit handler)
□ What happens if the kernel version changes? (Use BTF/CO-RE, tracepoints)
```

---

## Appendix A: Essential Kernel Source Files

```
linux/kernel/kprobes.c           — kprobe core implementation
linux/arch/x86/kernel/kprobes/   — x86-specific kprobe code
linux/kernel/trace/trace_kprobe.c— tracefs kprobe interface
linux/kernel/trace/bpf_trace.c   — BPF tracing helpers
linux/kernel/events/core.c       — perf_events core
linux/mm/uprobe.c                — uprobe implementation
linux/include/linux/kprobes.h    — kprobe data structures
linux/include/linux/bpf.h        — BPF types and helpers
linux/include/linux/perf_event.h — perf_event_attr and friends
linux/include/uapi/linux/bpf.h   — BPF UAPI (stable interface)
```

## Appendix B: Key Syscall Numbers (x86-64)

```
sys_perf_event_open = 298   (use in C: syscall(SYS_perf_event_open, ...))
sys_bpf             = 321   (use in C: syscall(SYS_bpf, cmd, attr, size))
```

## Appendix C: Cargo.toml Template for Aya Project

```toml
# Workspace Cargo.toml
[workspace]
members = [
    "kprobe-monitor",
    "kprobe-monitor-ebpf",
    "kprobe-monitor-common",
]
resolver = "2"

# kprobe-monitor-common/Cargo.toml
[package]
name = "kprobe-monitor-common"
version = "0.1.0"
edition = "2021"

[features]
user = ["aya"]

[dependencies]
aya = { version = "0.12", optional = true }

# kprobe-monitor-ebpf/Cargo.toml
[package]
name = "kprobe-monitor-ebpf"
version = "0.1.0"
edition = "2021"

[dependencies]
aya-bpf = { version = "0.1" }
aya-log-ebpf = { version = "0.1" }
kprobe-monitor-common = { path = "../kprobe-monitor-common" }

[profile.release]
opt-level = 3   # required for BPF code generation quality

# kprobe-monitor/Cargo.toml
[package]
name = "kprobe-monitor"
version = "0.1.0"
edition = "2021"

[dependencies]
aya           = { version = "0.12", features = ["async_tokio"] }
aya-log       = "0.2"
kprobe-monitor-common = { path = "../kprobe-monitor-common", features = ["user"] }
tokio         = { version = "1", features = ["full"] }
anyhow        = "1.0"
log           = "0.4"
env_logger    = "0.10"
nix           = { version = "0.27", features = ["user"] }
```

---

*This document covers the complete Linux dynamic tracing ecosystem as of kernel 6.x.
The fundamental mechanisms (INT3-based kprobes, uprobe COW patching, tracepoint NOPs)
have been stable since Linux 3.x–5.x. The eBPF landscape evolves rapidly — always
check kernel version requirements for specific features.*

*Master the internals. The tools change; the principles endure.*

Here is your complete deep-dive reference — **3,259 lines / ~104 KB** of dense, structured knowledge. Here is what is covered:

---

**Foundations (Sections 1–3)**
All prerequisite concepts are explained from scratch — CPU privilege rings, interrupts/exceptions, the INT3 breakpoint mechanism, process memory layout, virtual memory and COW pages, the ELF format (essential for uprobes), and the `/proc`/`/sys` virtual filesystems.

**Core Probe Mechanisms (Sections 4–7)**
- **kprobes**: Full INT3 injection cycle, the `pt_regs` structure with every register named, System V ABI calling conventions (which register holds which argument), aggregate probes, and jump-optimization.
- **kretprobes**: The return-address hijacking trick explained step-by-step, `maxactive`/`nmissed` semantics.
- **uprobes**: COW page patching, the XOL (Execute Out of Line) vma, USDT probes and the `.note.stapsdt` ELF section.
- **uretprobes**: caveats with longjmp, tail-call optimization.

**The Broader Ecosystem (Sections 8–12)**
tracepoints (NOP→CALL patching via `stop_machine`), ftrace (`mcount`/`fentry` mechanism, tracers, `kprobe_events` text interface with full fetch-argument syntax), `perf_event_open`, eBPF (verifier, JIT, maps, program types, all `bpf_helper` functions), SystemTap, bpftrace.

**Implementations (Sections 14–15)**
- **C**: Kernel module kprobe, kretprobe latency measurement, Makefile, `perf_event_open` ring buffer reader, BPF C program with ringbuf, libbpf loader, tracefs uprobe from userspace.
- **Rust**: Full Aya project (common types, `aya-bpf` BPF program, userspace loader), tracefs RAII wrapper (probe auto-removes on `Drop`), `/proc/kallsyms` symbol resolver.

**Expert Knowledge (Sections 16–20)**
Probe decision tree, overhead numbers, in-kernel filtering patterns, security risks + eBPF verifier guarantees, diagnostic commands, and a 12-week deliberate practice roadmap.