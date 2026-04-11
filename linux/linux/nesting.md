# Interrupt Nesting — Complete In-Depth Guide
### Linux Driver Design | C · Rust · Go Implementations

---

> *"An interrupt fires with all other interrupts disabled on that CPU (to prevent nesting),
> so the ISR must be fast. It does the minimum necessary and defers the rest."*

---

## Table of Contents

1. [Foundational Vocabulary](#1-foundational-vocabulary)
2. [What Is an Interrupt?](#2-what-is-an-interrupt)
3. [What Is Nesting? (General Concept)](#3-what-is-nesting-general-concept)
4. [Interrupt Nesting — The Hardware Mechanism](#4-interrupt-nesting--the-hardware-mechanism)
5. [Why Linux Disables Interrupts During an ISR](#5-why-linux-disables-interrupts-during-an-isr)
6. [The ISR Contract — Rules of the Fast Path](#6-the-isr-contract--rules-of-the-fast-path)
7. [Top Half vs Bottom Half Architecture](#7-top-half-vs-bottom-half-architecture)
8. [Deferral Mechanism 1 — Softirqs](#8-deferral-mechanism-1--softirqs)
9. [Deferral Mechanism 2 — Tasklets](#9-deferral-mechanism-2--tasklets)
10. [Deferral Mechanism 3 — Workqueues](#10-deferral-mechanism-3--workqueues)
11. [Deferral Mechanism 4 — Threaded IRQs](#11-deferral-mechanism-4--threaded-irqs)
12. [Choosing the Right Deferral: Decision Tree](#12-choosing-the-right-deferral-decision-tree)
13. [Spinlocks and Interrupt Context Locking](#13-spinlocks-and-interrupt-context-locking)
14. [Complete C Implementation](#14-complete-c-implementation)
15. [Complete Rust Implementation (kernel crate style)](#15-complete-rust-implementation-kernel-crate-style)
16. [Complete Go Implementation (simulation/userspace model)](#16-complete-go-implementation-simulationuserspace-model)
17. [Timing and Latency Mental Model](#17-timing-and-latency-mental-model)
18. [Common Bugs and Anti-Patterns](#18-common-bugs-and-anti-patterns)
19. [Expert Mental Models and Cognitive Principles](#19-expert-mental-models-and-cognitive-principles)
20. [Summary Cheat Sheet](#20-summary-cheat-sheet)

---

## 1. Foundational Vocabulary

Before anything else, every term must be crystal clear.
These are the atoms of this topic — understand each one independently first.

| Term | Plain Meaning |
|------|---------------|
| **Interrupt** | A hardware signal that forces the CPU to stop current work and handle an urgent event |
| **ISR** | Interrupt Service Routine — the function that runs when an interrupt fires |
| **IRQ** | Interrupt ReQuest line — the numbered "channel" a device uses to signal the CPU |
| **Nesting** | One interrupt interrupting another interrupt that is already being handled |
| **Preemption** | The act of stopping a running task to run something more urgent |
| **Interrupt context** | A special execution state — not a process, not a thread — pure CPU reaction |
| **Top Half** | The ISR itself — runs immediately, must be fast, minimal work |
| **Bottom Half** | Deferred work scheduled by the top half — runs later when safe |
| **Softirq** | Software interrupt — a very fast deferred mechanism, runs in interrupt context |
| **Tasklet** | A wrapper around softirq — easier to use, still in interrupt context |
| **Workqueue** | Deferred work that runs in kernel thread context (can sleep) |
| **Threaded IRQ** | ISR runs in a dedicated kernel thread — can sleep, priority-controlled |
| **Spinlock** | A lock that busy-waits — CPU spins until lock is free (no sleeping) |
| **Critical Section** | Code that must not be interrupted or run concurrently |
| **APIC** | Advanced Programmable Interrupt Controller — hardware chip managing interrupts |
| **Interrupt Mask** | A CPU flag/register bit that enables or disables interrupts globally |
| **Priority Level** | A numeric rank — higher priority interrupts can preempt lower ones |
| **Deferred** | Postponed — work scheduled to run after the ISR returns |
| **Atomic** | An operation that cannot be split — it either fully happens or doesn't |
| **Reentrancy** | Code that can be safely interrupted and called again before the first call finishes |
| **Context Switch** | CPU saves current state and loads another task's state |
| **Kernel Thread (kthread)** | A thread running in kernel space — has its own stack, can sleep |
| **NMI** | Non-Maskable Interrupt — an interrupt that CANNOT be disabled (hardware faults, watchdog) |

---

## 2. What Is an Interrupt?

### The Fundamental Problem Interrupts Solve

Imagine you are a CPU. You have thousands of tasks to run. A keyboard is connected. How do you know when a key is pressed?

**Option A: Polling** — Every few microseconds, ask the keyboard: "Did anyone press a key?"
This wastes CPU cycles asking a question whose answer is almost always "no."

**Option B: Interrupt** — Tell the keyboard: "When a key is pressed, tap me on the shoulder."
The CPU works on real tasks. When the keyboard taps it (fires an interrupt), the CPU pauses,
handles the key, then resumes exactly where it left off.

```
WITHOUT INTERRUPTS (Polling)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU: [Work] [Check KB] [Work] [Check KB] [Work] [Check KB] ...
                ↑ wasted          ↑ wasted
  99.9% of checks return "nothing happened"

WITH INTERRUPTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPU: [Work...................] [ISR!] [Work continues...]
                                  ↑
                         key pressed HERE, instantly handled
```

### The Interrupt Lifecycle (Step-by-Step)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INTERRUPT LIFECYCLE                                 │
│                                                                         │
│  1. DEVICE FIRES                                                        │
│     Device asserts IRQ line (electrical signal to APIC/PIC)            │
│                          │                                              │
│                          ▼                                              │
│  2. CONTROLLER ROUTES                                                   │
│     APIC receives signal → chooses target CPU → sends interrupt vector  │
│                          │                                              │
│                          ▼                                              │
│  3. CPU SAVES STATE                                                     │
│     CPU finishes current instruction                                    │
│     Pushes: RIP (instruction pointer), RFLAGS, RSP, CS, SS onto stack  │
│     IF flag cleared → interrupts now disabled on this CPU              │
│                          │                                              │
│                          ▼                                              │
│  4. IDT LOOKUP                                                          │
│     Interrupt Descriptor Table[vector] → address of ISR function        │
│                          │                                              │
│                          ▼                                              │
│  5. ISR EXECUTES (Top Half)                                             │
│     Runs fast: acknowledge HW, copy data, schedule bottom half         │
│                          │                                              │
│                          ▼                                              │
│  6. ISR RETURNS (IRET instruction)                                      │
│     CPU restores RFLAGS → IF flag restored → interrupts re-enabled     │
│     Execution resumes at saved RIP — as if nothing happened            │
│                          │                                              │
│                          ▼                                              │
│  7. BOTTOM HALF RUNS                                                    │
│     At a safe point: softirq/tasklet/workqueue processes deferred work  │
└─────────────────────────────────────────────────────────────────────────┘
```

### The CPU State Snapshot

When an interrupt fires, the CPU automatically saves a minimal context:

```
Stack Before Interrupt:          Stack After CPU Saves Context:
┌─────────────────────┐          ┌─────────────────────┐
│   ... user data ... │          │   ... user data ... │
│                     │          │─────────────────────│
│   [current RSP] ────┼──►       │   SS (stack segment)│ ◄── auto-pushed
│                     │          │   RSP (stack ptr)   │ ◄── auto-pushed
└─────────────────────┘          │   RFLAGS (CPU flags)│ ◄── auto-pushed (IF=1 saved here)
                                 │   CS (code segment) │ ◄── auto-pushed
                                 │   RIP (return addr) │ ◄── auto-pushed
                                 │─────────────────────│
                                 │   Error code (maybe)│
                                 └─────────────────────┘
                                 
After RFLAGS is saved, IF (Interrupt Flag) is CLEARED in the live RFLAGS.
This means: interrupts are NOW disabled on this CPU.
IRET instruction restores RFLAGS → IF is restored to 1 → interrupts re-enabled.
```

---

## 3. What Is Nesting? (General Concept)

**Nesting** means: one thing starting inside another thing of the same type, before the outer one finishes.

### Nesting in General Programming

```
Function Nesting (normal, harmless):
┌────────────────────────────────────┐
│ function A() {                     │
│   ...                              │
│   function B() {  ◄── nested call  │
│     ...                            │
│     function C() { ◄── deeper nest │
│     }                              │
│   }                                │
│   ...                              │
│ }                                  │
└────────────────────────────────────┘
Stack grows: A → B → C → (C returns) → B → (B returns) → A
```

### Interrupt Nesting — The Dangerous Case

Without protection, consider:

```
CPU handling IRQ 5 (disk read)...
  PARTWAY THROUGH ISR for IRQ 5...
    IRQ 3 fires (keyboard)...
      CPU starts handling IRQ 3...
        PARTWAY THROUGH ISR for IRQ 3...
          IRQ 5 fires AGAIN (same disk interrupt!)
            ↑ DISASTER: ISR for IRQ 5 re-entered while first instance still running!
```

```
Timeline of nested interrupt chaos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time →  [Normal code] [IRQ5-start] [IRQ3-start] [IRQ5-again!] [CRASH]
                           ↑              ↑              ↑
                     ISR5 running    IRQ3 preempts   ISR5 called again
                                     ISR5            before ISR5 finished!
```

**Problems with nesting:**
1. **Stack overflow** — each interrupt nesting level pushes more data onto the kernel stack
2. **Data corruption** — if ISR uses global/shared state and gets re-entered
3. **Unbounded latency** — high-priority interrupts could starve the CPU
4. **Locking deadlock** — if ISR holds a lock and gets re-entered, it tries to acquire lock it already holds

---

## 4. Interrupt Nesting — The Hardware Mechanism

### The IF Flag (Interrupt Flag) — The Master Switch

On x86/x86-64, the EFLAGS/RFLAGS register has a bit called **IF (Interrupt Flag)**:
- `IF = 1` → CPU accepts hardware interrupts
- `IF = 0` → CPU ignores hardware interrupts (they are masked/pending)

Instructions:
- `CLI` — CLear Interrupt flag — disables interrupts
- `STI` — SeT Interrupt flag — enables interrupts

**When a hardware interrupt fires and the CPU vectors to the ISR:**
The CPU automatically executes the equivalent of `CLI` — setting `IF = 0`.
This is done in hardware, before the first instruction of your ISR runs.

```
RFLAGS register (x86-64, 64-bit):
Bit:  63 ... 22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
     ┌─────────────────────────────────────────────────────────────────────────────┐
     │  0  ...  0  ID VIP VIF AC VM RF  0 NT IOPL OF DF IF TF SF ZF  0 AF  0 PF 1 │
     └─────────────────────────────────────────────────────────────────────────────┘
                                                              ↑
                                                         Bit 9 = IF
                                                         
When interrupt fires:
  1. CPU saves current RFLAGS (with IF=1) onto stack
  2. CPU clears IF in live RFLAGS → IF=0 → no more interrupts on this CPU
  3. Your ISR runs
  4. IRET restores RFLAGS from stack → IF=1 again
```

### ARM Architecture Equivalent

On ARM/ARM64, there is no single IF flag. Instead:
- **CPSR.I bit** (IRQ mask) — set to 1 to disable IRQs
- **CPSR.F bit** (FIQ mask) — set to 1 to disable FIQs (Fast Interrupt Requests)
- On entry to IRQ mode, CPSR.I is automatically set

```
ARM CPSR (Current Program Status Register):
Bit: 31 30 29 28 27 ... 9  8  7  6  5  4  3  2  1  0
    ┌──────────────────────────────────────────────────┐
    │  N  Z  C  V  Q  ...  E  A  I  F  T  M4 M3 M2 M1 M0│
    └──────────────────────────────────────────────────┘
                              ↑  ↑
                         IRQ  |  FIQ
                         mask |  mask
                         (I)  |  (F)
                              |
                    Set to 1 on IRQ entry (auto)
```

### APIC — The Hardware Interrupt Router

Modern systems use the **APIC (Advanced Programmable Interrupt Controller)**:

```
Hardware Devices                    CPU Cores
┌──────────┐                        ┌──────────┐
│  Disk    │──IRQ 14──┐             │  Core 0  │
│ Controller│         │             │  LAPIC   │◄── IRQ delivered here
└──────────┘         ▼             └──────────┘
                  ┌──────┐              ↑
┌──────────┐      │ I/O  │              │ (sent via system bus)
│ Network  │──IRQ 9──►APIC│──────────────┘
│   Card   │      │      │         ┌──────────┐
└──────────┘      │      │         │  Core 1  │
                  │      │─────────►  LAPIC   │
┌──────────┐      │      │         └──────────┘
│ Keyboard │──IRQ 1──►   │
└──────────┘      └──────┘
                  
LAPIC = Local APIC (one per CPU core)
I/O APIC = receives device IRQs, routes to target CPU's LAPIC
```

### Priority Levels and Nesting on x86 (Legacy Mode)

In legacy 8259 PIC mode (old systems), interrupts had hardware priority levels.
Higher-priority ISRs could preempt lower-priority ones → true nesting.

```
8259 PIC Priority (descending):
IRQ 0 → Timer          (highest priority)
IRQ 1 → Keyboard
IRQ 2 → Cascade (8259B)
IRQ 3 → COM2
IRQ 4 → COM1
IRQ 5 → LPT2 / Sound
IRQ 6 → Floppy
IRQ 7 → LPT1
...
IRQ 15 → Secondary IDE (lowest priority)

If ISR for IRQ 7 is running, IRQ 0 (timer) CAN preempt it.
This is NESTING — IRQ 0 ISR runs inside IRQ 7 ISR's stack frame.
```

**Linux's choice:** Linux re-enables interrupts inside ISRs selectively using `IRQF_SHARED` and `local_irq_enable()`, but by default on entry to an ISR, **interrupts are disabled**. Linux largely flattened the nesting model to avoid the complexity.

---

## 5. Why Linux Disables Interrupts During an ISR

Linux made a deliberate architectural decision: **run ISRs with interrupts disabled on the local CPU**.

### Reason 1: Stack Depth Safety

```
Linux kernel stack size: 8KB (32-bit) or 16KB (64-bit) — FIXED, SMALL

Each nested interrupt consumes stack:
┌─────────────┐  ◄── top of 8KB stack
│  User stack │
│   frames    │
├─────────────┤
│  ISR Level 1│  uses ~1-2KB
├─────────────┤
│  ISR Level 2│  uses ~1-2KB
├─────────────┤
│  ISR Level 3│  uses ~1-2KB  ← getting dangerous
├─────────────┤
│  ISR Level 4│  ← STACK OVERFLOW → kernel panic!
└─────────────┘  ◄── bottom of 8KB stack
```

### Reason 2: Simplicity of ISR Code

If interrupts could nest freely, every ISR would need to:
- Be fully reentrant
- Use locks even within its own code
- Handle being interrupted mid-operation

This complexity is a bug farm. By disabling interrupts:
- ISR code is effectively single-threaded on this CPU
- No need for locks within the ISR itself
- Mental model is simple: "nothing can preempt me"

### Reason 3: Hardware Requires ACK Before Re-enable

Most interrupt controllers require the ISR to **acknowledge (ACK)** the interrupt
before the same interrupt can fire again. Linux handles this at the start of the ISR.
Allowing nesting before ACK would cause spurious re-delivery.

### Reason 4: Deterministic Latency for RT Systems

Nesting creates variable-depth interrupt stacks → unpredictable latency.
Flat ISR model means maximum interrupt latency is bounded by the longest ISR.

### The Trade-Off Linux Makes

```
FLAT MODEL (Linux choice):          NESTED MODEL (some RTOSes):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRO: Simple, safe, no stack bomb    PRO: Higher-priority IRQs handled faster
CON: High-priority IRQ must wait    CON: Complex, stack depth unpredictable
     for current ISR to finish           Must handle reentrancy everywhere

Linux's answer to the CON:
  → Use VERY SHORT ISRs (microseconds)
  → Defer work to bottom halves
  → High-priority work completes before lower-priority ISR
```

---

## 6. The ISR Contract — Rules of the Fast Path

An ISR is not a normal function. It lives under a strict contract:

```
┌─────────────────────────────────────────────────────────────────┐
│               THE ISR CONTRACT (Must Follow ALL Rules)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ MUST DO:                                                    │
│    1. Acknowledge the interrupt to the hardware (EOI/ACK)       │
│    2. Copy volatile data from device registers IMMEDIATELY      │
│    3. Wake up a waiting thread OR schedule a bottom half        │
│    4. Return as fast as possible (target: < 5-10 microseconds)  │
│                                                                 │
│  ❌ MUST NOT DO:                                                │
│    1. Sleep or block (NO: mutex_lock, wait_event, msleep)       │
│    2. Call any function that might sleep                        │
│    3. Allocate memory with GFP_KERNEL (may sleep)              │
│       → Use GFP_ATOMIC instead                                  │
│    4. Access user space memory (page faults can sleep)          │
│    5. Acquire a sleeping lock (semaphore, mutex)                │
│    6. Perform I/O that blocks (disk, network in blocking mode)  │
│    7. Do heavy computation (DMA transfers, crypto, parsing)     │
│    8. Spend more than ~100 microseconds total                   │
│                                                                 │
│  ⚠️  CONTEXT RULES:                                            │
│    - in_interrupt() returns true                                │
│    - in_irq() returns true                                      │
│    - current process context is UNDEFINED (could be any task)  │
│    - You are NOT running "as" any particular process            │
│    - Preemption is disabled on this CPU                         │
│    - Interrupts are disabled on this CPU (by default)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Can't the ISR Sleep?

```
SLEEPING requires:
┌────────────────────────────────────────────────────────┐
│  1. Scheduler picks next task                          │
│  2. Context switch to new task                         │
│  3. Current task state saved in task_struct            │
│  4. Eventually, scheduler switches BACK                │
└────────────────────────────────────────────────────────┘

In interrupt context:
  - There is NO current task to save (we're between tasks)
  - Scheduler cannot preempt interrupt context
  - If we sleep: system HANGS — nobody to wake us up
  - Calling schedule() in interrupt context → BUG() kernel panic

Visual:
  [Task A] ──interrupt──► [ISR running on CPU, no "task" context]
     ↑                          │
     │                          │ if ISR calls sleep()...
     │                          ↓
     └──────────── Who do we reschedule??? Task A is frozen!
                  The scheduler has NO WAY to resume.
                  DEADLOCK.
```

### The Memory Allocation Rule

```c
// WRONG — GFP_KERNEL can sleep to wait for memory:
ptr = kmalloc(size, GFP_KERNEL);   // ← NEVER in ISR!

// RIGHT — GFP_ATOMIC never sleeps (fails immediately if no memory):
ptr = kmalloc(size, GFP_ATOMIC);   // ← OK in ISR (but can return NULL)

// GFP_ATOMIC internally:
//   1. Tries to get memory from emergency pool
//   2. If not available: returns NULL immediately
//   3. NEVER waits for memory reclaim
```

---

## 7. Top Half vs Bottom Half Architecture

This is the central design pattern for interrupt handling in Linux.
It solves the core tension: **interrupts must be fast**, but **real work takes time**.

### The Architecture

```
                        HARDWARE INTERRUPT FIRES
                                    │
                                    ▼
            ┌───────────────────────────────────────┐
            │            TOP HALF (ISR)              │
            │  • Runs with interrupts disabled       │
            │  • Must be < 10 microseconds           │
            │  • Steps:                              │
            │    1. ACK hardware interrupt           │
            │    2. Read device status/data          │
            │    3. Clear device interrupt flag      │
            │    4. Schedule bottom half             │
            │    5. Return (IRET)                    │
            └───────────────┬───────────────────────┘
                            │ schedules
                            ▼
            ┌───────────────────────────────────────┐
            │           BOTTOM HALF                 │
            │  Runs when interrupts are re-enabled   │
            │  Types:                               │
            │    ├── Softirq (interrupt context)    │
            │    ├── Tasklet (interrupt context)    │
            │    ├── Workqueue (process context)    │
            │    └── Threaded IRQ (kthread)         │
            └───────────────────────────────────────┘
```

### Concrete Example: Network Card Interrupt

```
Network packet arrives at NIC hardware
              │
              ▼
NIC asserts IRQ 9 on APIC
              │
              ▼
CPU halts current work, saves state
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  TOP HALF (net_rx_action ISR)          ~2 microseconds      │
│                                                             │
│  1. Tell NIC: "I got your interrupt" (write to register)   │
│  2. Read packet length and status from NIC registers        │
│  3. DMA-copy packet data to ring buffer (pre-allocated)     │
│  4. Call napi_schedule() — marks NAPI poll for softirq      │
│  5. Return                                                  │
└─────────────────────────────────────────────────────────────┘
              │
              │ ISR returns, interrupts re-enabled
              ▼
┌─────────────────────────────────────────────────────────────┐
│  BOTTOM HALF (NAPI poll via NET_RX_SOFTIRQ)   ~50-200 µs   │
│                                                             │
│  1. Loop: pull packets from ring buffer                     │
│  2. Allocate sk_buff for each packet                        │
│  3. Parse Ethernet/IP/TCP headers                           │
│  4. Route packet to correct socket                          │
│  5. Wake up application waiting on recv()                   │
└─────────────────────────────────────────────────────────────┘
```

### Why This Split is Genius

```
WITHOUT SPLIT (everything in ISR):
Time: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      [IRQ9 ISR: parse+route+wake app = 200µs]
      ↑ ALL interrupts disabled for 200µs!
      ↑ Timer interrupt delayed → system jitters
      ↑ Keyboard interrupt delayed → input lag
      ↑ Other NICs delayed → packet loss

WITH SPLIT (top half + bottom half):
Time: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      [IRQ9 ISR: 2µs] [other IRQs handled] [softirq: 200µs]
       ↑ fast!                                ↑ safe, interruptible
       interrupts disabled only 2µs!
```

---

## 8. Deferral Mechanism 1 — Softirqs

### What is a Softirq?

A **softirq** (software interrupt) is a kernel mechanism for running deferred work
at a special priority — lower than hardware interrupts, higher than normal processes.

**Key facts:**
- There are exactly **32 softirq slots**, statically defined at compile time
- Currently Linux uses ~10 of them
- They run in **interrupt context** (cannot sleep!)
- They can run **simultaneously on multiple CPUs**
- They are the most performance-critical deferral mechanism

### The Softirq Table

```
Softirq Priority (0 = highest):
┌───┬────────────────────────┬────────────────────────────────┐
│ 0 │ HI_SOFTIRQ             │ High priority tasklets         │
│ 1 │ TIMER_SOFTIRQ          │ Timer callbacks                │
│ 2 │ NET_TX_SOFTIRQ         │ Network transmit               │
│ 3 │ NET_RX_SOFTIRQ         │ Network receive (NAPI)         │
│ 4 │ BLOCK_SOFTIRQ          │ Block device completions       │
│ 5 │ IRQ_POLL_SOFTIRQ       │ Block I/O polling              │
│ 6 │ TASKLET_SOFTIRQ        │ Regular tasklets               │
│ 7 │ SCHED_SOFTIRQ          │ Scheduler                      │
│ 8 │ HRTIMER_SOFTIRQ        │ High-resolution timers         │
│ 9 │ RCU_SOFTIRQ            │ RCU callbacks                  │
└───┴────────────────────────┴────────────────────────────────┘
```

### How Softirqs Work Internally

```
Step 1: ISR calls raise_softirq(NET_RX_SOFTIRQ)
         → Sets bit 3 in per-CPU bitmask: __softirq_pending

Step 2: ISR returns (IRET)
         → Interrupts re-enabled

Step 3: Kernel checks __softirq_pending at:
         a) After returning from interrupt (irq_exit())
         b) When ksoftirqd wakes up
         c) When local_bh_enable() is called

Step 4: __do_softirq() runs:
         → Reads bitmask, calls each pending softirq handler
         → Runs to completion on this CPU

Per-CPU bitmask visualization:
CPU 0: [0][0][0][1][0][0][1][0][0][0]  ← bits 3,6 pending
            ↑                           NET_RX and TASKLET pending
CPU 1: [0][0][0][0][0][0][0][0][0][0]  ← nothing pending
```

### Softirq Execution Flow

```
ISR returns
    │
    ▼
irq_exit()
    │
    ├── in_interrupt()? → YES → return (nested, skip)
    │
    ▼
local_softirq_pending() != 0?
    │
    ├── NO → return to normal execution
    │
    └── YES
         │
         ▼
    __do_softirq()
         │
         ├── Disable bottom halves (bh)
         │
         ├── Loop (max 10 iterations or 2ms budget):
         │     │
         │     ├── Read pending bitmask
         │     ├── Clear bitmask
         │     ├── Enable bottom halves
         │     ├── Call each pending handler
         │     └── Disable bottom halves
         │
         ├── Still pending after budget?
         │     └── YES → wake ksoftirqd kernel thread
         │
         └── Return
```

### ksoftirqd — The Softirq Daemon

When softirqs are too busy (high interrupt load), Linux offloads them to:
`ksoftirqd/0`, `ksoftirqd/1`, ... (one per CPU)

```
┌─────────────────────────────────────────────────────┐
│  ksoftirqd/N kernel thread                          │
│                                                     │
│  while (true) {                                     │
│    if (local_softirq_pending()) {                   │
│      __do_softirq();                                │
│    } else {                                         │
│      schedule(); // sleep until woken               │
│    }                                               │
│  }                                                  │
│                                                     │
│  This thread CAN be scheduled normally              │
│  → high interrupt load won't starve other tasks     │
└─────────────────────────────────────────────────────┘
```

---

## 9. Deferral Mechanism 2 — Tasklets

### What is a Tasklet?

A **tasklet** is a high-level wrapper around softirqs that is:
- Easier to use (no static compile-time slot needed)
- **Serialized** — the same tasklet never runs on two CPUs simultaneously
- Still runs in interrupt context (cannot sleep!)
- Built on `HI_SOFTIRQ` (high priority) or `TASKLET_SOFTIRQ` (normal)

### Tasklet vs Softirq Comparison

```
┌──────────────────────┬────────────────────────┬──────────────────┐
│ Feature              │ Softirq                │ Tasklet          │
├──────────────────────┼────────────────────────┼──────────────────┤
│ Registration         │ Compile-time only      │ Runtime          │
│ Parallel execution   │ YES — multiple CPUs    │ NO — serialized  │
│ Reentrancy concern   │ You handle it          │ Handled for you  │
│ Use case             │ High-perf networking   │ General drivers  │
│ Sleep allowed        │ NO                     │ NO               │
│ Implemented via      │ Direct                 │ Softirq          │
│ Driver usage         │ Rare (core subsystems) │ Common           │
└──────────────────────┴────────────────────────┴──────────────────┘
```

### Tasklet Lifecycle

```
DEFINE:
  DECLARE_TASKLET(my_tasklet, my_tasklet_handler);
      │
      │  Creates struct tasklet_struct:
      │  { next, state, count, func, data }
      │
SCHEDULE (from ISR):
  tasklet_schedule(&my_tasklet);
      │
      │  Sets TASKLET_STATE_SCHED bit
      │  Adds to per-CPU tasklet list
      │  Raises TASKLET_SOFTIRQ
      │
EXECUTE (in softirq context):
  tasklet_action() called by TASKLET_SOFTIRQ handler
      │
      ├── Check TASKLET_STATE_RUN: already running on another CPU?
      │       YES → requeue, try later
      │       NO  → set STATE_RUN, clear STATE_SCHED, call handler
      │
      ▼
  my_tasklet_handler() executes
      │
      ▼
  Clear TASKLET_STATE_RUN
```

### State Machine of a Tasklet

```
         tasklet_schedule()
IDLE ────────────────────────► SCHEDULED
  ▲                                │
  │                    softirq runs│
  │                                ▼
  │    handler done           RUNNING
  └───────────────────────────────┘

  LOCKED STATE:
  If RUNNING on CPU0 and SCHEDULED on CPU1 simultaneously:
    CPU1 sees RUNNING → requeues → waits → runs after CPU0 finishes
    SAME tasklet NEVER runs in parallel on 2 CPUs
```

---

## 10. Deferral Mechanism 3 — Workqueues

### What is a Workqueue?

A **workqueue** defers work to **kernel threads** (kworker threads).
This is fundamentally different from tasklets/softirqs:

- Runs in **process context** (not interrupt context)
- **CAN sleep** (can call mutex_lock, wait_event, msleep, etc.)
- Can allocate memory with `GFP_KERNEL`
- Can do I/O
- Lower performance than tasklets (thread scheduling overhead)
- Safer and more flexible for complex work

### Workqueue Architecture

```
                    ┌────────────────────────────┐
                    │  System Workqueue           │
                    │  (system_wq)                │
                    │                             │
                    │  ┌──────┐ ┌──────┐ ┌──────┐│
                    │  │work_1│ │work_2│ │work_3││
                    │  └──────┘ └──────┘ └──────┘│
                    └────────────┬───────────────┘
                                 │
                    Per-CPU Worker Pools:
                    ┌────────────────────────────┐
                    │  CPU 0 Pool                │
                    │  kworker/0:0               │
                    │  kworker/0:1               │
                    └────────────────────────────┘
                    ┌────────────────────────────┐
                    │  CPU 1 Pool                │
                    │  kworker/1:0               │
                    │  kworker/1:1               │
                    └────────────────────────────┘
```

### Types of Workqueues

```
system_wq              → general-purpose, may be used by many drivers
system_highpri_wq      → high priority works
system_long_wq         → for works that may run for a long time
system_unbound_wq      → not bound to any CPU (better NUMA behavior)
system_freezable_wq    → can be frozen during suspend

Create your own:
  alloc_workqueue("name", flags, max_active)
  
  flags:
    WQ_HIGHPRI         → high priority threads
    WQ_CPU_INTENSIVE   → work is CPU-intensive
    WQ_UNBOUND         → not bound to specific CPU
    WQ_FREEZABLE       → freezes on system suspend
    WQ_MEM_RECLAIM     → for memory reclaim paths
```

### Work Item Lifecycle

```
DEFINE work item:
  DECLARE_WORK(my_work, my_work_handler);
  or:
  INIT_WORK(&my_work, my_work_handler);

SCHEDULE from ISR:
  schedule_work(&my_work);           // on system_wq
  queue_work(my_wq, &my_work);      // on specific wq
  schedule_delayed_work(&my_work, delay); // after delay jiffies

EXECUTION (in kworker thread):
  my_work_handler(struct work_struct *work)
  {
      // CAN SLEEP HERE
      // CAN use GFP_KERNEL
      // CAN acquire mutex
      // CAN do I/O
  }

CANCEL:
  cancel_work_sync(&my_work);    // wait for completion, then cancel
  cancel_delayed_work_sync();    // same for delayed work
```

---

## 11. Deferral Mechanism 4 — Threaded IRQs

### What is a Threaded IRQ?

Introduced in Linux 2.6.30, a **threaded IRQ** splits the ISR into two functions:
1. A **primary handler** (hard IRQ context, very fast — just returns IRQ_WAKE_THREAD)
2. A **thread handler** (runs in a dedicated `irq/N-name` kernel thread — can sleep!)

This is the **modern preferred approach** for most device drivers.

### Architecture

```
Hardware IRQ fires
       │
       ▼
┌──────────────────────────────────────────┐
│  PRIMARY HANDLER (hard IRQ context)      │
│  irq_handler_t handler                  │
│                                          │
│  Must be extremely fast:                 │
│  1. Check: is this my device?           │
│  2. Mask the IRQ (prevent re-fire)      │
│  3. Return IRQ_WAKE_THREAD              │
└──────────────────┬───────────────────────┘
                   │ IRQ_WAKE_THREAD
                   ▼
┌──────────────────────────────────────────┐
│  THREAD HANDLER (irq/47-eth0 kthread)   │
│  irq_handler_t thread_fn                │
│                                          │
│  Runs in process context:               │
│  1. Read and process device data        │
│  2. Communicate with hardware (may I/O) │
│  3. Allocate memory (GFP_KERNEL OK)     │
│  4. Acquire mutex if needed             │
│  5. Return IRQ_HANDLED                  │
└──────────────────────────────────────────┘
```

### Registration

```c
// Old way (non-threaded):
request_irq(irq, handler, flags, name, dev_id);

// New way (threaded):
request_threaded_irq(
    irq,          // IRQ number
    handler,      // primary handler (can be NULL → use default)
    thread_fn,    // thread handler
    flags,        // IRQF_SHARED, etc.
    name,         // device name
    dev_id        // device identifier
);

// Even simpler — NULL primary, only thread:
request_threaded_irq(irq, NULL, my_thread_fn,
                     IRQF_ONESHOT, "my_device", dev);
// IRQF_ONESHOT: keep IRQ disabled until thread handler completes
```

### Threaded IRQ vs Workqueue

```
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Feature              │ Threaded IRQ         │ Workqueue            │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Dedicated thread     │ YES (one per IRQ)    │ Shared pool          │
│ Thread priority      │ Configurable (RT!)   │ Normal by default    │
│ Real-time capable    │ YES (SCHED_FIFO)     │ Harder               │
│ Can sleep            │ YES                  │ YES                  │
│ When to use          │ Device ISR           │ General deferred work│
│ Setup complexity     │ Low                  │ Low                  │
│ Priority control     │ /proc/irq/N/smp_*    │ Per-workqueue flags  │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 12. Choosing the Right Deferral: Decision Tree

```
START: You have work to defer from your ISR
              │
              ▼
   Does the work need to SLEEP?
   (mutex_lock, msleep, wait_event, GFP_KERNEL, I/O)
              │
    ┌─────────┴──────────┐
   YES                   NO
    │                    │
    ▼                    ▼
Is this the     Is the work extremely
actual ISR?     performance critical?
(hardware IRQ)  (networking, storage)
    │                    │
  ┌─┴──┐            ┌────┴────┐
 YES   NO          YES        NO
  │    │            │          │
  ▼    ▼            ▼          ▼
Thread- Work-    Softirq    Tasklet
ed IRQ  queue    (rare:     (common:
                 net/block) most drivers)
  
DECISION SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Need sleep + hardware ISR     → Threaded IRQ
Need sleep + deferred task    → Workqueue
No sleep + ultra-high perf    → Softirq (rarely write yourself)
No sleep + most device drivers→ Tasklet

MODERN RECOMMENDATION (Linux kernel docs, 2024+):
  Prefer Threaded IRQ for almost all new driver work.
  Threaded IRQs make PREEMPT_RT patches work correctly.
  Tasklets are "deprecated in spirit" for new code.
```

---

## 13. Spinlocks and Interrupt Context Locking

### The Locking Problem

```
Scenario: ISR and process both access shared data structure (e.g., ring buffer)

CPU 0: Process context writing to ring buffer
           │
           ▼ (interrupt fires mid-write!)
CPU 0: ISR reads ring buffer → SEES PARTIAL WRITE → DATA CORRUPTION!
```

### Spinlocks — The Interrupt-Safe Lock

A **spinlock** is a lock that does not sleep — it busy-waits (spins in a loop).
It's the ONLY lock type safe for use in interrupt context.

```
SPINLOCK BEHAVIOR:
┌─────────────────────────────────────────────────────┐
│  CPU 0 acquires spinlock:                           │
│    spin_lock(&my_lock)                              │
│    → Atomically set lock bit                        │
│    → If already locked: SPIN (loop checking)        │
│                                                     │
│  CPU 1 tries to acquire same lock:                  │
│    spin_lock(&my_lock)                              │
│    → Lock is taken → CPU 1 SPINS here:              │
│      while (lock_is_held) { /* busy wait */ }       │
│                                                     │
│  CPU 0 releases lock:                               │
│    spin_unlock(&my_lock)                            │
│    → Clears lock bit                                │
│    → CPU 1 stops spinning, acquires lock            │
└─────────────────────────────────────────────────────┘
```

### The Four Spinlock Variants

```
1. spin_lock() / spin_unlock()
   Use when: neither holder nor contender is in interrupt context
   Does NOT disable interrupts

2. spin_lock_bh() / spin_unlock_bh()
   Use when: contender could be a softirq/tasklet (bottom half)
   Disables bottom halves (softirqs, tasklets) on local CPU
   Does NOT disable hardware interrupts

3. spin_lock_irq() / spin_unlock_irq()
   Use when: contender could be a hardware ISR
   Disables all hardware interrupts on local CPU
   WARNING: Assumes interrupts were enabled before — restores to enabled

4. spin_lock_irqsave() / spin_unlock_irqrestore()
   Use when: contender could be hardware ISR, AND interrupts may already be disabled
   Saves RFLAGS (including IF) before disabling → restores exact state
   SAFEST choice when unsure

CODE PATTERN:
  unsigned long flags;
  spin_lock_irqsave(&my_lock, flags);    // save IF, disable interrupts, lock
  // ... critical section ...
  spin_unlock_irqrestore(&my_lock, flags); // unlock, restore IF
```

### When to Use Which Lock

```
┌───────────────────────────────────────────────────────────────────┐
│          LOCKING DECISION TABLE                                   │
├────────────────────────┬──────────────────────────────────────────┤
│  Where is shared data  │  Which lock to use                      │
│  accessed?             │                                          │
├────────────────────────┼──────────────────────────────────────────┤
│  Two process contexts  │  mutex or semaphore (can sleep)         │
│  (no interrupt)        │                                          │
├────────────────────────┼──────────────────────────────────────────┤
│  Process + softirq     │  spin_lock_bh()                         │
├────────────────────────┼──────────────────────────────────────────┤
│  Process + ISR         │  spin_lock_irqsave()                    │
├────────────────────────┼──────────────────────────────────────────┤
│  Softirq + ISR         │  spin_lock_irqsave()                    │
├────────────────────────┼──────────────────────────────────────────┤
│  Two softirqs          │  spin_lock()                            │
│  (same type, diff CPU) │                                          │
├────────────────────────┼──────────────────────────────────────────┤
│  ISR only (no process) │  No lock needed (single CPU, no preempt)│
└────────────────────────┴──────────────────────────────────────────┘
```

---

## 14. Complete C Implementation

This implements a simulated character device driver that demonstrates:
- ISR with top half / bottom half split
- Tasklet for deferred processing
- Workqueue for I/O-bound deferred work
- Threaded IRQ alternative
- Proper locking

```c
// FILE: interrupt_demo_driver.c
// Demonstrates interrupt handling patterns in Linux kernel driver
// Compile as kernel module: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/interrupt.h>    // request_irq, free_irq, IRQ_HANDLED
#include <linux/workqueue.h>    // workqueue, INIT_WORK, schedule_work
#include <linux/spinlock.h>     // spinlock_t, spin_lock_irqsave
#include <linux/slab.h>         // kmalloc, kfree, GFP_ATOMIC
#include <linux/time.h>         // ktime_get
#include <linux/atomic.h>       // atomic_t, atomic_inc
#include <linux/kfifo.h>        // kfifo — kernel FIFO buffer
#include <linux/platform_device.h>

#define DRIVER_NAME     "irq_demo"
#define IRQ_NUMBER      17          // Hypothetical IRQ line
#define RX_BUFFER_SIZE  4096        // Ring buffer size
#define MAX_PACKET_SIZE 256         // Max data per interrupt

// ─────────────────────────────────────────────────────────────
// DATA STRUCTURES
// ─────────────────────────────────────────────────────────────

/**
 * struct irq_demo_dev - Our device's private data
 *
 * This struct lives for the lifetime of the driver.
 * It holds ALL state the ISR and bottom halves need.
 *
 * CRITICAL DESIGN RULE:
 *   Any field touched by BOTH the ISR and a process/thread
 *   MUST be protected by a spinlock (irqsave variant).
 */
struct irq_demo_dev {
    /* Hardware simulation */
    void __iomem    *hw_base;       // Memory-mapped I/O base address
    int              irq;           // IRQ number

    /* Ring buffer for ISR → bottom half communication */
    DECLARE_KFIFO(rx_fifo, u8, RX_BUFFER_SIZE);
    spinlock_t       fifo_lock;     // Protects rx_fifo

    /* Statistics (atomic — no lock needed for simple counters) */
    atomic_t         irq_count;     // Total interrupts received
    atomic_t         dropped_count; // Packets dropped due to full buffer
    atomic_t         processed;     // Packets fully processed

    /* Bottom half: tasklet for fast processing */
    struct tasklet_struct rx_tasklet;

    /* Bottom half: workqueue for slow/sleeping work */
    struct workqueue_struct *slow_wq;
    struct work_struct       slow_work;

    /* Threaded IRQ alternative (not active simultaneously) */
    bool use_threaded_irq;

    /* Per-interrupt data passed ISR → tasklet */
    u8       pending_data[MAX_PACKET_SIZE];
    size_t   pending_len;
    spinlock_t pending_lock;        // Protects pending_data/pending_len
};

static struct irq_demo_dev *g_dev;  // Global device instance

// ─────────────────────────────────────────────────────────────
// BOTTOM HALF: TASKLET HANDLER
// ─────────────────────────────────────────────────────────────

/**
 * rx_tasklet_handler - Fast deferred processing (interrupt context)
 *
 * CONTEXT: Softirq / interrupt context
 * RULES:   Cannot sleep, cannot use GFP_KERNEL, cannot acquire mutex
 *
 * Think of this as "the ISR's assistant" — does everything the ISR
 * wanted to do but couldn't fit in the tight time budget.
 */
static void rx_tasklet_handler(unsigned long data)
{
    struct irq_demo_dev *dev = (struct irq_demo_dev *)data;
    u8 packet[MAX_PACKET_SIZE];
    size_t len;
    unsigned long flags;

    /*
     * Step 1: Retrieve pending data from ISR
     * We use irqsave because the ISR (hardware interrupt) could
     * fire again and write to pending_data while we read it.
     */
    spin_lock_irqsave(&dev->pending_lock, flags);
    len = dev->pending_len;
    if (len > 0) {
        memcpy(packet, dev->pending_data, len);
        dev->pending_len = 0;  // Mark as consumed
    }
    spin_unlock_irqrestore(&dev->pending_lock, flags);

    if (len == 0)
        return;  // Spurious tasklet run

    /*
     * Step 2: Push into FIFO for userspace to read
     * The FIFO is a ring buffer. If full, packet is dropped.
     */
    spin_lock_irqsave(&dev->fifo_lock, flags);
    if (kfifo_avail(&dev->rx_fifo) >= len) {
        kfifo_in(&dev->rx_fifo, packet, len);
        atomic_inc(&dev->processed);
    } else {
        atomic_inc(&dev->dropped_count);
        pr_warn_ratelimited(DRIVER_NAME ": RX FIFO full, dropped %zu bytes\n", len);
    }
    spin_unlock_irqrestore(&dev->fifo_lock, flags);

    /*
     * Step 3: Schedule slow work if packet needs deep processing
     * (e.g., decryption, DMA finalization, logging to storage)
     *
     * We CANNOT do this here (tasklet = no sleep),
     * so we schedule a workqueue item.
     */
    queue_work(dev->slow_wq, &dev->slow_work);
}

// ─────────────────────────────────────────────────────────────
// BOTTOM HALF: WORKQUEUE HANDLER (Process Context — Can Sleep)
// ─────────────────────────────────────────────────────────────

/**
 * slow_work_handler - Sleeping deferred work
 *
 * CONTEXT: kworker kernel thread (process context)
 * RULES:   CAN sleep, CAN use GFP_KERNEL, CAN acquire mutex, CAN do I/O
 *
 * This handles anything that is too slow/risky for interrupt context.
 */
static void slow_work_handler(struct work_struct *work)
{
    struct irq_demo_dev *dev =
        container_of(work, struct irq_demo_dev, slow_work);

    /*
     * container_of() — a crucial Linux kernel macro.
     * Given a pointer to a MEMBER of a struct, get pointer to the CONTAINING struct.
     *
     * How:
     *   container_of(ptr, type, member)
     *   = (type *)((char *)(ptr) - offsetof(type, member))
     *
     * Visual:
     *   struct irq_demo_dev {        ◄── we want pointer to THIS
     *     ...
     *     struct work_struct slow_work; ◄── we have pointer to THIS
     *   };
     */

    /* Simulate slow work: logging, crypto, database write */
    pr_info(DRIVER_NAME ": [workqueue] Processing deferred work, "
            "total processed: %d, dropped: %d\n",
            atomic_read(&dev->processed),
            atomic_read(&dev->dropped_count));

    /*
     * Could do here:
     *   - mutex_lock(&some_mutex)         ← OK, can sleep
     *   - kmalloc(..., GFP_KERNEL)        ← OK, can sleep
     *   - filp_open() / kernel_write()    ← OK, I/O allowed
     *   - msleep(10)                      ← OK, can sleep
     */
}

// ─────────────────────────────────────────────────────────────
// TOP HALF: HARDWARE INTERRUPT SERVICE ROUTINE
// ─────────────────────────────────────────────────────────────

/**
 * irq_demo_isr - The hardware ISR (Top Half)
 *
 * CONTEXT: Hard IRQ context — interrupts disabled on this CPU
 * BUDGET:  < 10 microseconds total
 * RULES:   ABSOLUTELY CANNOT sleep, block, or take a mutex
 *
 * The three jobs of every ISR:
 *   1. Verify this interrupt belongs to MY device
 *   2. Copy volatile hardware data before it's overwritten
 *   3. Schedule a bottom half, return IRQ_HANDLED
 *
 * Return values:
 *   IRQ_HANDLED     → This was my interrupt, I handled it
 *   IRQ_NONE        → Not my interrupt (shared IRQ lines)
 *   IRQ_WAKE_THREAD → Wake thread handler (threaded IRQ only)
 */
static irqreturn_t irq_demo_isr(int irq, void *dev_id)
{
    struct irq_demo_dev *dev = (struct irq_demo_dev *)dev_id;
    u32 hw_status;
    unsigned long flags;

    /*
     * JOB 1: Read hardware status register.
     *
     * readl() does a memory-mapped I/O read from the device.
     * It includes a memory barrier — critical for correctness.
     *
     * Simulated: pretend we read a status register
     */
    hw_status = 0xDEAD0001;  /* In real driver: hw_status = readl(dev->hw_base + STATUS_REG); */

    /* Check if the interrupt came from our device */
    if (!(hw_status & 0x1)) {
        return IRQ_NONE;  /* Not our interrupt — shared IRQ line, someone else's */
    }

    atomic_inc(&dev->irq_count);

    /*
     * JOB 2: Read hardware data IMMEDIATELY.
     *
     * Device registers are volatile — the hardware can overwrite them
     * with the NEXT packet before our bottom half runs.
     * We MUST copy to RAM right now, in this ISR.
     *
     * This is the most critical timing constraint in all of driver design.
     */
    spin_lock_irqsave(&dev->pending_lock, flags);

    dev->pending_len = 8;  /* In real: read DMA length register */
    memset(dev->pending_data, (u8)(hw_status & 0xFF), dev->pending_len);
    /* Real driver: memcpy_fromio(dev->pending_data, dev->hw_base + DATA_REG, len); */

    spin_unlock_irqrestore(&dev->pending_lock, flags);

    /*
     * JOB 3: Acknowledge the interrupt to the hardware.
     *
     * Without ACK, the device will keep the IRQ line asserted.
     * The interrupt will fire AGAIN immediately after we return.
     * This is the "interrupt storm" bug — system becomes unresponsive.
     *
     * Simulated:
     *   writel(0x1, dev->hw_base + ACK_REG);
     */

    /*
     * JOB 4: Schedule bottom half for the real processing work.
     *
     * tasklet_schedule() is safe from interrupt context.
     * It sets a flag — actual execution is deferred.
     * Cost: ~50 nanoseconds.
     */
    tasklet_schedule(&dev->rx_tasklet);

    return IRQ_HANDLED;  /* Tell kernel: "yes, I owned this interrupt" */
}

// ─────────────────────────────────────────────────────────────
// ALTERNATIVE: THREADED ISR
// ─────────────────────────────────────────────────────────────

/**
 * irq_demo_primary_handler - Threaded IRQ primary handler
 *
 * This runs in hard IRQ context — minimal work.
 * Just validate and return IRQ_WAKE_THREAD.
 */
static irqreturn_t irq_demo_primary_handler(int irq, void *dev_id)
{
    struct irq_demo_dev *dev = (struct irq_demo_dev *)dev_id;
    u32 hw_status = 0xDEAD0001;  /* Simulated hardware read */

    if (!(hw_status & 0x1))
        return IRQ_NONE;

    atomic_inc(&dev->irq_count);

    /* Mask the IRQ to prevent re-fire while thread runs */
    /* disable_irq_nosync(irq);  — handled by IRQF_ONESHOT */

    return IRQ_WAKE_THREAD;  /* Wake the thread handler */
}

/**
 * irq_demo_thread_handler - Threaded IRQ thread handler
 *
 * CONTEXT: irq/17-irq_demo kernel thread (process context)
 * CAN SLEEP: YES
 * Can use GFP_KERNEL, mutex, I/O — full process context rights
 */
static irqreturn_t irq_demo_thread_handler(int irq, void *dev_id)
{
    struct irq_demo_dev *dev = (struct irq_demo_dev *)dev_id;

    /*
     * Full processing here — we can sleep, we can do I/O.
     * No tasklet needed — this thread IS the bottom half.
     */

    /* Simulate reading and processing device data */
    u8 data[MAX_PACKET_SIZE];
    size_t len = 8;
    unsigned long flags;

    /* Could do kmalloc with GFP_KERNEL here */
    memset(data, 0xAB, len);

    spin_lock_irqsave(&dev->fifo_lock, flags);
    if (kfifo_avail(&dev->rx_fifo) >= len) {
        kfifo_in(&dev->rx_fifo, data, len);
        atomic_inc(&dev->processed);
    } else {
        atomic_inc(&dev->dropped_count);
    }
    spin_unlock_irqrestore(&dev->fifo_lock, flags);

    /* Can do sleeping work here too */
    /* msleep(1);  ← LEGAL here! Would be ILLEGAL in tasklet ISR */

    return IRQ_HANDLED;
}

// ─────────────────────────────────────────────────────────────
// DRIVER INITIALIZATION
// ─────────────────────────────────────────────────────────────

static int __init irq_demo_init(void)
{
    int ret;

    pr_info(DRIVER_NAME ": Loading interrupt demo driver\n");

    /* Allocate device structure */
    g_dev = kzalloc(sizeof(*g_dev), GFP_KERNEL);
    if (!g_dev)
        return -ENOMEM;

    g_dev->irq = IRQ_NUMBER;

    /* Initialize statistics counters */
    atomic_set(&g_dev->irq_count, 0);
    atomic_set(&g_dev->dropped_count, 0);
    atomic_set(&g_dev->processed, 0);

    /* Initialize spinlocks */
    spin_lock_init(&g_dev->fifo_lock);
    spin_lock_init(&g_dev->pending_lock);

    /* Initialize FIFO */
    INIT_KFIFO(g_dev->rx_fifo);

    /* Initialize tasklet
     * DECLARE_TASKLET alternative at runtime:
     *   tasklet_init(&dev->rx_tasklet, rx_tasklet_handler, (unsigned long)dev);
     */
    tasklet_init(&g_dev->rx_tasklet, rx_tasklet_handler,
                 (unsigned long)g_dev);

    /* Create dedicated workqueue for slow processing */
    g_dev->slow_wq = alloc_workqueue("irq_demo_wq",
                                      WQ_UNBOUND | WQ_HIGHPRI, 0);
    if (!g_dev->slow_wq) {
        ret = -ENOMEM;
        goto err_alloc_wq;
    }

    /* Initialize work item */
    INIT_WORK(&g_dev->slow_work, slow_work_handler);

    /* Register ISR (traditional approach with tasklet) */
    ret = request_irq(
        g_dev->irq,           /* IRQ number */
        irq_demo_isr,         /* ISR function */
        IRQF_SHARED,          /* Allow IRQ line to be shared with other devices */
        DRIVER_NAME,          /* Name appears in /proc/interrupts */
        g_dev                 /* dev_id — must be unique for shared IRQs */
    );
    if (ret) {
        pr_err(DRIVER_NAME ": Failed to request IRQ %d: %d\n", g_dev->irq, ret);
        goto err_request_irq;
    }

    /*
     * ALTERNATIVE: Use threaded IRQ instead:
     *
     * ret = request_threaded_irq(
     *     g_dev->irq,
     *     irq_demo_primary_handler,   // fast primary
     *     irq_demo_thread_handler,    // sleeping thread
     *     IRQF_SHARED | IRQF_ONESHOT, // ONESHOT: keep IRQ disabled until thread done
     *     DRIVER_NAME,
     *     g_dev
     * );
     *
     * IRQF_ONESHOT: The IRQ line is kept disabled until the thread handler
     * returns. Without this, the IRQ could fire AGAIN before the thread
     * finishes handling the first occurrence. Essential for level-triggered IRQs.
     */

    pr_info(DRIVER_NAME ": Driver loaded. IRQ %d registered.\n", g_dev->irq);
    pr_info(DRIVER_NAME ": Check /proc/interrupts for IRQ stats\n");

    return 0;

err_request_irq:
    destroy_workqueue(g_dev->slow_wq);
err_alloc_wq:
    kfree(g_dev);
    return ret;
}

static void __exit irq_demo_exit(void)
{
    pr_info(DRIVER_NAME ": Unloading driver\n");

    /* Order matters! Must mirror init in reverse. */

    /* 1. Free IRQ first — stops new interrupts from firing */
    free_irq(g_dev->irq, g_dev);

    /* 2. Kill tasklet — waits for any running tasklet to finish */
    tasklet_kill(&g_dev->rx_tasklet);

    /* 3. Drain and destroy workqueue — waits for pending work */
    flush_workqueue(g_dev->slow_wq);
    destroy_workqueue(g_dev->slow_wq);

    /* 4. Print final statistics */
    pr_info(DRIVER_NAME ": Final stats — IRQs: %d, Processed: %d, Dropped: %d\n",
            atomic_read(&g_dev->irq_count),
            atomic_read(&g_dev->processed),
            atomic_read(&g_dev->dropped_count));

    /* 5. Free device memory */
    kfree(g_dev);
}

module_init(irq_demo_init);
module_exit(irq_demo_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Interrupt Nesting Guide");
MODULE_DESCRIPTION("Demonstrates interrupt handling: ISR, tasklet, workqueue, threaded IRQ");
MODULE_VERSION("1.0");
```

---

## 15. Complete Rust Implementation (kernel crate style)

```rust
// FILE: interrupt_demo.rs
// Rust kernel module demonstrating interrupt handling
// Uses the linux kernel rust bindings (rust-for-linux)
//
// To build: Part of a kernel module, not standalone binary.
// Requires Linux kernel with CONFIG_RUST=y
//
// This shows the CONCEPTS using Rust's ownership/safety model.
// The kernel crate API is evolving; this follows rust-for-linux conventions.

#![no_std]
// kernel crate provides safe wrappers around kernel C functions
// In a real module: extern crate kernel;
// Here we show the design pattern with comments explaining each binding.

use core::sync::atomic::{AtomicI32, Ordering};

// ─────────────────────────────────────────────────────────────
// CONCEPTUAL TYPES (mirrors kernel crate)
// ─────────────────────────────────────────────────────────────

/// Represents ownership of a registered IRQ.
/// When dropped, automatically calls free_irq().
/// This is RAII — Resource Acquisition Is Initialization.
/// Rust makes it IMPOSSIBLE to forget to free_irq()!
struct IrqRegistration {
    irq_number: u32,
    // In real kernel crate: holds raw IRQ handle
}

impl Drop for IrqRegistration {
    fn drop(&mut self) {
        // Automatically calls free_irq() — cannot be forgotten
        // kernel::irq::free_irq(self.irq_number);
        println!("IRQ {} unregistered (RAII cleanup)", self.irq_number);
    }
}

/// Represents a tasklet — a deferred work item
struct Tasklet {
    // In real kernel crate: tasklet_struct wrapper
    scheduled: core::sync::atomic::AtomicBool,
}

impl Tasklet {
    fn new() -> Self {
        Tasklet {
            scheduled: core::sync::atomic::AtomicBool::new(false),
        }
    }

    /// Schedule this tasklet to run — safe from interrupt context
    fn schedule(&self) {
        // In real kernel: tasklet_schedule(&self.inner)
        self.scheduled.store(true, Ordering::Release);
    }
}

// ─────────────────────────────────────────────────────────────
// DEVICE STATE
// ─────────────────────────────────────────────────────────────

/// Device private data
/// Rust's ownership model enforces many safety rules at compile time.
///
/// KEY INSIGHT:
/// In C, you must MANUALLY ensure shared data is protected.
/// In Rust, the COMPILER rejects unsafe sharing at compile time.
struct IrqDemoDevice {
    irq: u32,

    /// Atomic counters — no lock needed for simple counters.
    /// AtomicI32 is a safe wrapper around atomic_t.
    irq_count: AtomicI32,
    dropped_count: AtomicI32,
    processed_count: AtomicI32,

    /// Tasklet for deferred processing.
    /// In real kernel crate, this would be a kernel::sync::SpinLock<Tasklet>
    rx_tasklet: Tasklet,

    /// Ring buffer (simulated here with a fixed array + indices).
    /// In real kernel: kernel::sync::SpinLock<RingBuffer>
    /// Rust's SpinLock<T> makes it IMPOSSIBLE to access T without holding the lock.
    /// C: You can accidentally forget to lock. Rust: Compiler error if you forget.
    buffer: [u8; 4096],
    buf_head: AtomicI32,
    buf_tail: AtomicI32,
}

impl IrqDemoDevice {
    fn new(irq: u32) -> Self {
        IrqDemoDevice {
            irq,
            irq_count: AtomicI32::new(0),
            dropped_count: AtomicI32::new(0),
            processed_count: AtomicI32::new(0),
            rx_tasklet: Tasklet::new(),
            buffer: [0u8; 4096],
            buf_head: AtomicI32::new(0),
            buf_tail: AtomicI32::new(0),
        }
    }
}

// ─────────────────────────────────────────────────────────────
// ISR HANDLER TRAIT
// ─────────────────────────────────────────────────────────────

/// Trait that an interrupt handler must implement.
/// This mirrors how rust-for-linux defines IRQ handlers:
///   trait Handler { fn handle_irq(data: &T) -> IrqReturn; }
///
/// The trait system prevents mixing up handler types at compile time.
trait IrqHandler {
    type Data;

    /// Called in interrupt context — MUST be fast.
    /// Note: Rust's type system ensures &self borrows are safe here.
    /// No allocation, no sleeping — enforced by not having access to
    /// any type that would enable such operations in interrupt context.
    fn handle_irq(data: &Self::Data) -> IrqReturn;
}

/// Return value of an ISR — equivalent to irqreturn_t
enum IrqReturn {
    Handled,        // IRQ_HANDLED
    None,           // IRQ_NONE
    WakeThread,     // IRQ_WAKE_THREAD (threaded IRQ)
}

// ─────────────────────────────────────────────────────────────
// ISR IMPLEMENTATION
// ─────────────────────────────────────────────────────────────

struct DemoIrqHandler;

impl IrqHandler for DemoIrqHandler {
    type Data = IrqDemoDevice;

    /// TOP HALF — runs in interrupt context
    ///
    /// Rust safety note: In the kernel crate, interrupt context handlers
    /// receive a special "IrqDisabled" token type that proves interrupts
    /// are currently disabled. Functions that require sleep will not compile
    /// because they require a "MaySchedule" token — which cannot be held
    /// simultaneously with "IrqDisabled".
    ///
    /// This is COMPILE-TIME enforcement of the "no sleep in ISR" rule!
    fn handle_irq(dev: &Self::Data) -> IrqReturn {
        // ── Step 1: Read hardware status ──────────────────────────
        // Simulate reading a hardware register
        let hw_status: u32 = 0xDEAD_0001; // real: read_volatile(hw_base + STATUS)

        if hw_status & 0x1 == 0 {
            return IrqReturn::None; // Not our interrupt (shared IRQ)
        }

        // ── Step 2: Increment counter atomically ──────────────────
        // Ordering::Relaxed: We don't need ordering guarantees for a simple counter.
        // Ordering::Release/Acquire: Needed when counter signals data availability.
        dev.irq_count.fetch_add(1, Ordering::Relaxed);

        // ── Step 3: Copy hardware data before it's overwritten ────
        // In real kernel, we'd use a SpinLock<PendingData> here.
        // Rust would ensure we can't access pending_data without the lock.
        // The lock guard is dropped automatically (RAII) when this scope exits.
        //
        // Pseudocode (actual kernel crate syntax):
        //   let guard = dev.pending_lock.lock();
        //   guard.data.copy_from_slice(&hw_data[..len]);
        //   guard.len = len;
        // guard is Drop'd here → lock automatically released

        // ── Step 4: Schedule tasklet for deferred work ───────────
        // tasklet_schedule() is safe from interrupt context.
        dev.rx_tasklet.schedule();

        // ── Step 5: ACK the hardware interrupt ───────────────────
        // Must tell device: "I received your interrupt, you can deassert IRQ line"
        // real: write_volatile(hw_base + ACK_REG, 0x1);

        IrqReturn::Handled
    }
}

// ─────────────────────────────────────────────────────────────
// TASKLET HANDLER
// ─────────────────────────────────────────────────────────────

/// Deferred processing function — still interrupt context, but
/// interrupts ARE re-enabled while this runs (unlike the ISR).
///
/// In rust-for-linux, this would be implemented via a Tasklet<T> type
/// with a run() method that takes &T.
fn rx_tasklet_handler(dev: &IrqDemoDevice) {
    // In real kernel crate:
    //   let data = dev.pending_lock.lock();  // irqsave variant
    //   let packet = data.data[..data.len].to_vec(); // but can't use vec! without alloc
    //   Instead: copy to stack buffer

    // Simulate processing
    let processed = dev.processed_count.fetch_add(1, Ordering::Relaxed);

    // Log every 100 packets (ratelimited in real code)
    if processed % 100 == 0 {
        // In kernel: pr_info!("Processed {} packets\n", processed);
    }

    // Cannot sleep here! Cannot call anything that might sleep.
    // If we need slow work: queue_work()
}

// ─────────────────────────────────────────────────────────────
// WORKQUEUE HANDLER
// ─────────────────────────────────────────────────────────────

/// Slow deferred work — runs in kworker thread.
/// FULL process context: CAN sleep, CAN allocate, CAN do I/O.
///
/// In rust-for-linux:
///   struct MyWork { work: kernel::workqueue::Work<Self>, dev: Arc<IrqDemoDevice> }
///   impl kernel::workqueue::WorkItem for MyWork {
///       fn run(this: Arc<Self>) { ... }
///   }
fn slow_work_handler(dev: &IrqDemoDevice) {
    // We CAN sleep here — this runs in a kernel thread.
    // Example: update statistics in a file (sleeping I/O allowed)

    let irqs = dev.irq_count.load(Ordering::Relaxed);
    let processed = dev.processed_count.load(Ordering::Relaxed);
    let dropped = dev.dropped_count.load(Ordering::Relaxed);

    // In kernel: pr_info!("Stats: IRQs={}, processed={}, dropped={}\n", ...);
    let _ = (irqs, processed, dropped); // suppress unused warnings in userspace demo
}

// ─────────────────────────────────────────────────────────────
// THREADED IRQ IMPLEMENTATION
// ─────────────────────────────────────────────────────────────

/// In rust-for-linux, a threaded IRQ is defined with TWO associated functions.
/// The type system makes it impossible to accidentally call sleep-capable
/// functions in the hard IRQ handler — they require different token types.

trait ThreadedIrqHandler {
    type Data;

    /// Primary handler — hard IRQ context, same rules as handle_irq
    fn handle_irq_primary(data: &Self::Data) -> IrqReturn;

    /// Thread handler — process context, can sleep
    fn handle_irq_thread(data: &Self::Data) -> IrqReturn;
}

struct DemoThreadedHandler;

impl ThreadedIrqHandler for DemoThreadedHandler {
    type Data = IrqDemoDevice;

    fn handle_irq_primary(dev: &Self::Data) -> IrqReturn {
        // Ultra-minimal: just check if our device, return WAKE_THREAD
        let hw_status: u32 = 0xDEAD_0001;
        if hw_status & 0x1 == 0 {
            return IrqReturn::None;
        }
        dev.irq_count.fetch_add(1, Ordering::Relaxed);
        IrqReturn::WakeThread
    }

    fn handle_irq_thread(dev: &Self::Data) -> IrqReturn {
        // FULL process context — CAN SLEEP
        // This is as safe as writing a normal kernel function.

        // Read data, process it, maybe sleep, allocate, etc.
        dev.processed_count.fetch_add(1, Ordering::Relaxed);

        // In real code:
        //   let data = kmalloc_array::<u8>(len, GFP_KERNEL)?;
        //   copy_data_from_device(&data);
        //   submit_to_protocol_stack(data);

        IrqReturn::Handled
    }
}

// ─────────────────────────────────────────────────────────────
// RUST'S KEY SAFETY ADVANTAGES OVER C
// ─────────────────────────────────────────────────────────────

/*
COMPILE-TIME SAFETY IN RUST KERNEL CODE:

1. NO FORGOTTEN FREE_IRQ:
   C:    request_irq(...);
         // Forgot free_irq() in error path? Memory/IRQ leak. Bugs happen.
   Rust: let _irq = request_irq(...)?;  // IrqRegistration struct
         // When _irq goes out of scope: Drop trait calls free_irq() AUTOMATICALLY
         // IMPOSSIBLE to forget.

2. NO UNSYNCHRONIZED ACCESS:
   C:    g_dev->counter++;  // Forgot the lock? Race condition. Silent bug.
   Rust: dev.counter.fetch_add(1, Ordering::Relaxed);  // Must use atomic API
         // or: dev.data.lock().field = value;  // Cannot access without lock
         // Accessing without sync: COMPILE ERROR

3. NO SLEEPING IN ISR (in future kernel crate versions):
   C:    mutex_lock(&m);  // In ISR: compiles, runs, DEADLOCKS at runtime
   Rust: mutex.lock(token);  // Requires MaySchedule token
         // ISR context has IrqDisabled token, NOT MaySchedule
         // COMPILE ERROR if you try to sleep in an ISR

4. NO USE-AFTER-FREE:
   C:    free_irq(dev);  kfree(dev);  // Use dev after this? UAF bug.
   Rust: Ownership rules: once device is dropped, cannot use any reference to it.
         Compiler tracks all borrows. UAF = COMPILE ERROR.
*/

// Userspace simulation main (for testing the concepts)
fn main() {
    println!("=== Interrupt Nesting Demo (Rust Userspace Simulation) ===\n");

    let dev = IrqDemoDevice::new(17);

    println!("Simulating 5 hardware interrupts...\n");

    for i in 0..5 {
        println!("--- Interrupt {} fires ---", i + 1);

        // Simulate ISR (top half)
        println!("  [TOP HALF] ISR executing (interrupts disabled on this CPU)");
        let result = DemoIrqHandler::handle_irq(&dev);
        match result {
            IrqReturn::Handled => println!("  [TOP HALF] Returned IRQ_HANDLED, scheduling tasklet"),
            IrqReturn::None => println!("  [TOP HALF] Returned IRQ_NONE (not our device)"),
            IrqReturn::WakeThread => println!("  [TOP HALF] Returned IRQ_WAKE_THREAD"),
        }

        // Simulate softirq running tasklet (bottom half)
        println!("  [BOTTOM HALF] Tasklet executing (interrupts re-enabled)");
        rx_tasklet_handler(&dev);

        // Simulate workqueue
        println!("  [WORKQUEUE] Slow work executing in kworker thread");
        slow_work_handler(&dev);

        println!("  Stats: IRQs={}, Processed={}",
                 dev.irq_count.load(Ordering::Relaxed),
                 dev.processed_count.load(Ordering::Relaxed));
        println!();
    }

    println!("=== Threaded IRQ simulation ===\n");
    for i in 0..3 {
        println!("--- Threaded Interrupt {} fires ---", i + 1);
        println!("  [PRIMARY HANDLER] Running in hard IRQ context");
        let r = DemoThreadedHandler::handle_irq_primary(&dev);
        match r {
            IrqReturn::WakeThread => {
                println!("  [PRIMARY HANDLER] Waking IRQ thread");
                println!("  [THREAD HANDLER] Running in irq/17-demo kthread (can sleep!)");
                DemoThreadedHandler::handle_irq_thread(&dev);
                println!("  [THREAD HANDLER] Done");
            }
            _ => {}
        }
        println!();
    }

    println!("Final stats:");
    println!("  Total IRQs handled: {}", dev.irq_count.load(Ordering::Relaxed));
    println!("  Packets processed:  {}", dev.processed_count.load(Ordering::Relaxed));
    println!("  Packets dropped:    {}", dev.dropped_count.load(Ordering::Relaxed));

    // dev is dropped here — IrqRegistration::drop() would call free_irq()
    println!("\nDevice dropped — IRQ automatically unregistered (RAII)");
}
```

---

## 16. Complete Go Implementation (simulation/userspace model)

```go
// FILE: interrupt_nesting_sim.go
//
// Go userspace simulation of interrupt handling architecture.
// Models the interrupt system using goroutines and channels.
//
// IMPORTANT: This is a CONCEPTUAL MODEL, not real kernel code.
// Go runs in userspace and cannot register real hardware IRQs.
// But the architectural patterns (top half/bottom half, serialization,
// deferred work, locking) map directly to Go primitives.
//
// MAPPING:
//   Hardware interrupt   → closed channel / signal
//   ISR (top half)       → goroutine with highest priority logic
//   Tasklet              → goroutine scheduled from ISR channel
//   Workqueue            → worker pool goroutines
//   Spinlock             → sync.Mutex (conceptually; Go has no spinlock)
//   Atomic counter       → sync/atomic package
//   Interrupt disable    → sync.Mutex held + no other goroutine can enter
//
// Run: go run interrupt_nesting_sim.go

package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// ─────────────────────────────────────────────────────────────
// CONSTANTS AND TYPES
// ─────────────────────────────────────────────────────────────

const (
	RxBufferSize  = 4096
	MaxPacketSize = 256
	NumWorkers    = 4    // Number of workqueue goroutines
)

// IrqReturn mirrors Linux's irqreturn_t
type IrqReturn int

const (
	IrqNone      IrqReturn = 0 // IRQ_NONE: not our interrupt
	IrqHandled   IrqReturn = 1 // IRQ_HANDLED: we handled it
	IrqWakeThread IrqReturn = 2 // IRQ_WAKE_THREAD: wake thread handler
)

// PendingData represents data copied from hardware in the ISR
type PendingData struct {
	data   [MaxPacketSize]byte
	length int
	seqNum uint64 // Sequence number for ordering verification
}

// WorkItem represents a deferred work unit (workqueue item)
type WorkItem struct {
	packetData []byte
	seqNum     uint64
	timestamp  time.Time
}

// ─────────────────────────────────────────────────────────────
// DEVICE STRUCTURE
// ─────────────────────────────────────────────────────────────

// IrqDemoDevice models a hardware device with interrupt handling.
//
// Go's design notes vs C kernel:
//   - sync.Mutex replaces spinlock (Go doesn't expose spinlocks; they're internal)
//   - chan (channel) replaces the tasklet scheduling mechanism
//   - atomic.Int64 replaces atomic_t
//   - sync.WaitGroup replaces flush_workqueue() pattern
type IrqDemoDevice struct {
	irqNumber int

	// Statistics — atomic for ISR-safe access without locks
	irqCount    atomic.Int64
	droppedCount atomic.Int64
	processedCount atomic.Int64

	// Shared state: ISR writes, tasklet reads
	// Mutex protects this — in kernel, this would be spinlock_irqsave
	pendingMu   sync.Mutex
	pendingData PendingData

	// Ring buffer (using Go channel as concurrent queue)
	// Buffered channel = ring buffer with capacity
	rxFifo chan []byte // Capacity = RxBufferSize / MaxPacketSize

	// Tasklet channel: ISR sends signal, tasklet goroutine receives
	// Buffered to avoid blocking the ISR
	taskletChan chan struct{}

	// Workqueue: channel of work items to process
	workChan chan WorkItem

	// Threaded IRQ: channel to wake thread handler
	threadChan chan struct{}

	// Sequence number for interrupt ordering
	seqCounter atomic.Uint64

	// Control
	ctx    context.Context
	cancel context.CancelFunc
	wg     sync.WaitGroup
}

// NewDevice creates and initializes the device
func NewDevice(irq int) *IrqDemoDevice {
	ctx, cancel := context.WithCancel(context.Background())

	dev := &IrqDemoDevice{
		irqNumber:   irq,
		rxFifo:      make(chan []byte, 64),     // Ring buffer with 64 slots
		taskletChan: make(chan struct{}, 32),    // Tasklet signal queue (buffered!)
		workChan:    make(chan WorkItem, 128),   // Work item queue
		threadChan:  make(chan struct{}, 32),    // Thread wake signal
		ctx:         ctx,
		cancel:      cancel,
	}

	return dev
}

// ─────────────────────────────────────────────────────────────
// ISR: TOP HALF
// ─────────────────────────────────────────────────────────────

// HandleInterrupt simulates the hardware ISR (top half).
//
// TIMING BUDGET: microseconds
// RULES:
//   - No I/O (simulated by: no file operations, no network calls)
//   - No sleep (simulated by: no time.Sleep, no blocking channel ops)
//   - Must schedule bottom half and return immediately
//
// In the Go model:
//   - Non-blocking channel sends model the ISR's "fire and forget" scheduling
//   - select with default avoids blocking (models interrupt-context restrictions)
func (dev *IrqDemoDevice) HandleInterrupt(hwStatus uint32) IrqReturn {
	isrStart := time.Now()

	// ── Step 1: Check if this is our interrupt ────────────────
	if hwStatus&0x1 == 0 {
		return IrqNone // Shared IRQ, not for us
	}

	// ── Step 2: Increment interrupt counter (atomic, no lock) ─
	irqNum := dev.irqCount.Add(1)

	// ── Step 3: Read hardware data IMMEDIATELY ────────────────
	// Critical: must happen before hardware can overwrite registers.
	// Use lock to protect shared pendingData struct.
	// In kernel: spin_lock_irqsave(&dev->pending_lock, flags)
	seq := dev.seqCounter.Add(1)

	dev.pendingMu.Lock()
	dev.pendingData.length = 8
	dev.pendingData.seqNum = seq
	for i := 0; i < 8; i++ {
		dev.pendingData.data[i] = byte(hwStatus & 0xFF)
	}
	dev.pendingMu.Unlock()
	// In kernel: spin_unlock_irqrestore(&dev->pending_lock, flags)

	// ── Step 4: Schedule tasklet (non-blocking!) ──────────────
	// select + default = non-blocking send.
	// If taskletChan is full, we drop (signal coalescing):
	// this is intentional! If tasklet is already scheduled, no need
	// to schedule again — it will process the latest data.
	select {
	case dev.taskletChan <- struct{}{}:
		// Tasklet scheduled
	default:
		// Tasklet already scheduled — that's fine, it'll run soon
	}

	// ── Step 5: ACK hardware interrupt ───────────────────────
	// Simulated: in real hardware: writel(ACK, hw_base+ACK_REG)

	isrDuration := time.Since(isrStart)

	// ISR time monitoring — if ISR takes > 10µs, that's a bug
	if isrDuration > 10*time.Microsecond {
		// In kernel: pr_warn_ratelimited("ISR took too long!")
		fmt.Printf("  ⚠️  ISR #%d took %v (too slow!)\n", irqNum, isrDuration)
	}

	return IrqHandled
}

// ─────────────────────────────────────────────────────────────
// BOTTOM HALF: TASKLET
// ─────────────────────────────────────────────────────────────

// runTasklet runs the tasklet goroutine.
// Models TASKLET_SOFTIRQ behavior:
//   - Runs "soon" after ISR, but not in hard IRQ context
//   - Still relatively fast (no sleeping in real tasklet, but Go goroutine can yield)
//   - Serialized: same tasklet never runs concurrently with itself
//
// Architecture:
//   ISR ──(taskletChan)──► TaskletGoroutine ──(workChan)──► WorkerPool
func (dev *IrqDemoDevice) runTasklet() {
	defer dev.wg.Done()
	fmt.Println("[TASKLET GOROUTINE] Started, waiting for signals...")

	for {
		select {
		case <-dev.ctx.Done():
			fmt.Println("[TASKLET GOROUTINE] Context cancelled, stopping")
			return

		case <-dev.taskletChan:
			// ── Read pending data from ISR ─────────────────────────
			dev.pendingMu.Lock()
			length := dev.pendingData.length
			var packet [MaxPacketSize]byte
			seq := dev.pendingData.seqNum
			if length > 0 {
				copy(packet[:], dev.pendingData.data[:length])
				dev.pendingData.length = 0 // Mark as consumed
			}
			dev.pendingMu.Unlock()

			if length == 0 {
				continue // Spurious wakeup
			}

			// ── Push to FIFO ───────────────────────────────────────
			// Non-blocking send: if FIFO full, drop packet
			data := make([]byte, length)
			copy(data, packet[:length])

			select {
			case dev.rxFifo <- data:
				// Success: packet in FIFO
			default:
				// FIFO full: drop packet
				dev.droppedCount.Add(1)
				fmt.Printf("  [TASKLET] FIFO full! Dropped packet seq=%d\n", seq)
				continue
			}

			// ── Schedule workqueue for slow processing ─────────────
			// Non-blocking: if workChan full, drop work item
			// (stats update is best-effort, not critical path)
			work := WorkItem{
				packetData: data,
				seqNum:     seq,
				timestamp:  time.Now(),
			}
			select {
			case dev.workChan <- work:
				// Work item queued
			default:
				// Work queue full: this is less critical (stats update)
				// In real driver: log a warning, maybe increase queue depth
			}
		}
	}
}

// ─────────────────────────────────────────────────────────────
// BOTTOM HALF: WORKQUEUE WORKERS
// ─────────────────────────────────────────────────────────────

// runWorker simulates a kworker kernel thread.
// CAN "sleep" (blocking channel ops, time.Sleep are fine in Go goroutines).
// Models workqueue behavior: multiple workers process items from a shared queue.
func (dev *IrqDemoDevice) runWorker(workerID int) {
	defer dev.wg.Done()
	fmt.Printf("[WORKER %d] Started\n", workerID)

	for {
		select {
		case <-dev.ctx.Done():
			fmt.Printf("[WORKER %d] Stopping\n", workerID)
			return

		case work, ok := <-dev.workChan:
			if !ok {
				return
			}

			// ── Process work item ─────────────────────────────────
			// In real kernel workqueue: CAN sleep, CAN use GFP_KERNEL
			// Here: simulate variable processing time
			processingTime := time.Duration(rand.Intn(500)+100) * time.Microsecond
			time.Sleep(processingTime) // CAN sleep — this is process context!

			count := dev.processedCount.Add(1)
			latency := time.Since(work.timestamp)

			if count%10 == 0 {
				fmt.Printf("  [WORKER %d] Processed packet seq=%d, latency=%v, total=%d\n",
					workerID, work.seqNum, latency.Round(time.Microsecond), count)
			}
		}
	}
}

// ─────────────────────────────────────────────────────────────
// THREADED IRQ IMPLEMENTATION
// ─────────────────────────────────────────────────────────────

// HandleInterruptThreaded simulates a threaded IRQ primary handler.
// Ultra-minimal: just returns IrqWakeThread.
func (dev *IrqDemoDevice) HandleInterruptThreaded(hwStatus uint32) IrqReturn {
	if hwStatus&0x1 == 0 {
		return IrqNone
	}
	dev.irqCount.Add(1)

	// Non-blocking wake of thread handler
	select {
	case dev.threadChan <- struct{}{}:
	default:
		// Thread already awake, that's fine
	}

	return IrqWakeThread
}

// runThreadHandler simulates the irq/N-name kernel thread.
// This is the thread handler in request_threaded_irq().
// CAN sleep, full process context.
func (dev *IrqDemoDevice) runThreadHandler() {
	defer dev.wg.Done()
	fmt.Println("[THREAD HANDLER] irq/17-demo started")

	for {
		select {
		case <-dev.ctx.Done():
			fmt.Println("[THREAD HANDLER] Stopping")
			return

		case <-dev.threadChan:
			// FULL process context — CAN sleep, CAN allocate, CAN do I/O

			// Simulate: read all pending data from device
			// In real kernel: read DMA buffer, parse protocol, deliver to stack

			// Can sleep here! (time.Sleep models kernel sleep functions)
			time.Sleep(50 * time.Microsecond) // models msleep(1) or wait_for_completion

			// Submit to FIFO
			data := make([]byte, 8)
			for i := range data {
				data[i] = 0xBE // Simulated data
			}

			select {
			case dev.rxFifo <- data:
				dev.processedCount.Add(1)
			default:
				dev.droppedCount.Add(1)
			}
		}
	}
}

// ─────────────────────────────────────────────────────────────
// HARDWARE SIMULATOR
// ─────────────────────────────────────────────────────────────

// simulateHardware generates interrupt signals at a given rate.
// Models the hardware device asserting its IRQ line.
func (dev *IrqDemoDevice) simulateHardware(rate time.Duration, count int, useThreaded bool) {
	defer dev.wg.Done()

	for i := 0; i < count; i++ {
		select {
		case <-dev.ctx.Done():
			return
		case <-time.After(rate):
			hwStatus := uint32(0xDEAD_0001)

			if useThreaded {
				ret := dev.HandleInterruptThreaded(hwStatus)
				_ = ret
			} else {
				ret := dev.HandleInterrupt(hwStatus)
				_ = ret
			}
		}
	}

	fmt.Printf("[HW SIM] Finished generating %d interrupts\n", count)
}

// ─────────────────────────────────────────────────────────────
// START / STOP
// ─────────────────────────────────────────────────────────────

// Start launches all goroutines — models driver initialization
func (dev *IrqDemoDevice) Start(useThreaded bool) {
	fmt.Println("[DRIVER] Starting interrupt handling subsystem...")

	if useThreaded {
		// Threaded IRQ mode: one dedicated thread per IRQ
		dev.wg.Add(1)
		go dev.runThreadHandler()
		fmt.Printf("[DRIVER] Registered threaded IRQ %d\n", dev.irqNumber)
	} else {
		// Traditional mode: tasklet + workqueue
		dev.wg.Add(1)
		go dev.runTasklet()

		for i := 0; i < NumWorkers; i++ {
			dev.wg.Add(1)
			go dev.runWorker(i)
		}
		fmt.Printf("[DRIVER] Registered IRQ %d with tasklet + %d workers\n",
			dev.irqNumber, NumWorkers)
	}
}

// Stop gracefully shuts down — models driver exit cleanup
// Mirrors the ordered teardown in irq_demo_exit():
//   1. free_irq (stop new IRQs) → cancel context
//   2. tasklet_kill → drain taskletChan
//   3. flush_workqueue → drain workChan
func (dev *IrqDemoDevice) Stop() {
	fmt.Println("\n[DRIVER] Shutting down...")

	// Step 1: Signal all goroutines to stop (models free_irq)
	dev.cancel()

	// Step 2: Close work channel so workers see EOF
	close(dev.workChan)

	// Step 3: Wait for all goroutines to finish (models flush_workqueue)
	dev.wg.Wait()

	fmt.Println("[DRIVER] All goroutines stopped")
}

// ─────────────────────────────────────────────────────────────
// MAIN: DEMONSTRATION
// ─────────────────────────────────────────────────────────────

func main() {
	fmt.Println("╔══════════════════════════════════════════════════════════════╗")
	fmt.Println("║     INTERRUPT NESTING — Go Architecture Simulation          ║")
	fmt.Println("╚══════════════════════════════════════════════════════════════╝")
	fmt.Println()

	// ── DEMO 1: Traditional ISR + Tasklet + Workqueue ──────────────────────
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("DEMO 1: Traditional Top Half (ISR) + Tasklet + Workqueue")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	dev1 := NewDevice(17)
	dev1.Start(false) // traditional mode

	// Simulate hardware generating 50 interrupts at 1kHz
	dev1.wg.Add(1)
	go dev1.simulateHardware(1*time.Millisecond, 50, false)

	time.Sleep(200 * time.Millisecond) // Let it run
	dev1.Stop()

	fmt.Println("\n[DEMO 1 RESULTS]")
	fmt.Printf("  Total IRQs:         %d\n", dev1.irqCount.Load())
	fmt.Printf("  Packets processed:  %d\n", dev1.processedCount.Load())
	fmt.Printf("  Packets dropped:    %d\n", dev1.droppedCount.Load())

	fmt.Println()

	// ── DEMO 2: Threaded IRQ ────────────────────────────────────────────────
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("DEMO 2: Threaded IRQ (Primary Handler + Thread Handler)")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	dev2 := NewDevice(18)
	dev2.Start(true) // threaded IRQ mode

	// Simulate hardware generating 30 interrupts at 500Hz
	dev2.wg.Add(1)
	go dev2.simulateHardware(2*time.Millisecond, 30, true)

	time.Sleep(200 * time.Millisecond)
	dev2.Stop()

	fmt.Println("\n[DEMO 2 RESULTS]")
	fmt.Printf("  Total IRQs:         %d\n", dev2.irqCount.Load())
	fmt.Printf("  Packets processed:  %d\n", dev2.processedCount.Load())
	fmt.Printf("  Packets dropped:    %d\n", dev2.droppedCount.Load())

	fmt.Println()

	// ── DEMO 3: Interrupt Storm Simulation ─────────────────────────────────
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("DEMO 3: Interrupt Storm (100kHz rate — FIFO overflow expected)")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	dev3 := NewDevice(19)
	dev3.Start(false)

	// Storm: 200 interrupts in rapid succession
	dev3.wg.Add(1)
	go dev3.simulateHardware(10*time.Microsecond, 200, false)

	time.Sleep(100 * time.Millisecond)
	dev3.Stop()

	fmt.Println("\n[DEMO 3 RESULTS — Stress Test]")
	fmt.Printf("  Total IRQs:         %d\n", dev3.irqCount.Load())
	fmt.Printf("  Packets processed:  %d\n", dev3.processedCount.Load())
	fmt.Printf("  Packets dropped:    %d (overflow — expected!)\n", dev3.droppedCount.Load())

	if dev3.droppedCount.Load() > 0 {
		dropRate := float64(dev3.droppedCount.Load()) / float64(dev3.irqCount.Load()) * 100
		fmt.Printf("  Drop rate: %.1f%% (need deeper buffers or backpressure)\n", dropRate)
	}

	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════╗")
	fmt.Println("║  KEY TAKEAWAYS:                                              ║")
	fmt.Println("║  • Top half (ISR): fast, non-blocking, schedule bottom half ║")
	fmt.Println("║  • Tasklet: interrupt context, no sleep, serialized          ║")
	fmt.Println("║  • Workqueue: process context, CAN sleep, parallel          ║")
	fmt.Println("║  • Threaded IRQ: dedicated thread, CAN sleep, RT-capable   ║")
	fmt.Println("╚══════════════════════════════════════════════════════════════╝")
}
```

---

## 17. Timing and Latency Mental Model

```
INTERRUPT LATENCY BUDGET (x86-64, modern system):

Hardware asserts IRQ line
│
│  ~100 ns   APIC propagation + CPU recognition
▼
CPU saves registers (RFLAGS, RIP, RSP, CS, SS)
│
│  ~50 ns    Automatic hardware state save
▼
IDT lookup + branch to ISR
│
│  ~5-10 µs  TOP HALF execution budget
│             • ACK hardware: ~100 ns (PCI write)
│             • Copy registers: ~200 ns
│             • Schedule tasklet: ~50 ns
▼
ISR returns (IRET), interrupts re-enabled
│
│  ~0-100 µs TASKLET execution (variable, depends on load)
│             • Runs at next irq_exit() or ksoftirqd wakeup
│             • Can be delayed if another softirq is running
▼
Tasklet handler runs
│
│  ~1-5 ms   WORKQUEUE execution (variable)
│             • Scheduled on kworker thread
│             • Depends on scheduler quantum
▼
Work item processed

TOTAL END-TO-END LATENCY:
  Minimal path (no contention): ~10-100 µs
  Typical path:                 ~100 µs - 5 ms
  High-load path:               ~5-50 ms

FOR REAL-TIME SYSTEMS (PREEMPT_RT kernel):
  Use threaded IRQs + SCHED_FIFO
  Achieves: < 100 µs worst-case latency
```

```
INTERRUPT TIMELINE (multiple devices, one CPU):

Time →  0       100µs    200µs    300µs    400µs    500µs
        │        │        │        │        │        │
CPU:    [User]  [IRQ9-ISR][BH9][IRQ5-ISR] [BH5]   [User resumes]
               ↑          ↑   ↑           ↑
             NIC IRQ    BH   Disk IRQ   BH runs
             fires      runs fires      runs
             
Note: ISRs are short (IRQ9-ISR, IRQ5-ISR)
      Bottom halves (BH9, BH5) are longer but interruptible
      User code resumes at normal priority
```

---

## 18. Common Bugs and Anti-Patterns

### Bug 1: Sleeping in Interrupt Context

```
SYMPTOM: Kernel panic "BUG: scheduling while atomic"
         "BUG: sleep function called from invalid context"

CAUSE:
  static irqreturn_t bad_isr(int irq, void *dev_id) {
      mutex_lock(&dev->lock);   // ← WRONG: mutex can sleep!
      msleep(10);               // ← WRONG: explicit sleep!
      kmalloc(size, GFP_KERNEL);// ← WRONG: may sleep for memory!
      ...
  }

FIX:
  Use GFP_ATOMIC for allocation
  Use spinlock_irqsave() for locking
  Defer work to workqueue/threaded IRQ for sleeping operations
```

### Bug 2: Interrupt Storm (Missing ACK)

```
SYMPTOM: System freezes immediately when device starts.
         /proc/interrupts shows millions of interrupts per second.
         CPU at 100%, nothing responds.

CAUSE:
  static irqreturn_t bad_isr(int irq, void *dev_id) {
      process_data();  // Did processing...
      return IRQ_HANDLED;  // ← FORGOT TO ACK HARDWARE!
  }
  
  Without ACK: IRQ line stays asserted → IRQ fires again INSTANTLY
  after IRET → ISR runs → IRQ fires → infinite loop → system dead.

FIX:
  Always ACK the interrupt at the start of the ISR:
    writel(STATUS_ACK, dev->base + STATUS_REG);
  Or use hardware-specific EOI (End Of Interrupt):
    outb(0x20, 0x20);  // 8259 PIC EOI
```

### Bug 3: Using Wrong Spinlock Variant

```
SCENARIO:
  Ring buffer shared between:
    - ISR (hardware interrupt handler)
    - Process context (read() syscall)

WRONG:
  // In process context:
  spin_lock(&ring_lock);         // ← doesn't disable interrupts!
  read_from_ring();
  spin_unlock(&ring_lock);

  // In ISR:
  spin_lock(&ring_lock);         // ← IRQ fires while process holds lock!
  write_to_ring();               // DEADLOCK: process holds lock, ISR spins forever
  spin_unlock(&ring_lock);

CORRECT:
  // In process context:
  spin_lock_irqsave(&ring_lock, flags);
  read_from_ring();
  spin_unlock_irqrestore(&ring_lock, flags);

  // In ISR:
  spin_lock(&ring_lock);  // ISR runs with IRQs already disabled
  write_to_ring();        // Safe: process cannot interrupt us
  spin_unlock(&ring_lock);

WHY: spin_lock_irqsave disables IRQs on local CPU, so the ISR
     cannot preempt the process while it holds the lock.
```

### Bug 4: Tasklet Re-entrance (Forgetting Serialization)

```
CORRECT ASSUMPTION:
  Same tasklet NEVER runs on two CPUs simultaneously.
  Linux's tasklet subsystem guarantees this via TASKLET_STATE_RUN.

WRONG ASSUMPTION:
  "My tasklet can never see stale data" — FALSE.
  The ISR can update pending_data between two tasklet runs.
  The second run may see data from two ISR calls mixed together.

FIX:
  Use a queue/FIFO, not a single pending_data buffer.
  Or: use a generation counter to detect if new data arrived.
```

### Bug 5: Not Calling tasklet_kill() Before Unloading

```
SYMPTOM: Kernel oops after rmmod — "general protection fault"
         Task callback address points to freed module memory.

CAUSE:
  static void __exit my_exit(void) {
      free_irq(dev->irq, dev);  // ISR stopped
      // Forgot: tasklet_kill(&dev->tasklet)!
      kfree(dev);               // Free memory
      // BUT: Tasklet was still scheduled!
      // After kfree, tasklet runs → calls handler → handler reads freed dev
      // BOOM: use-after-free in freed module code
  }

FIX:
  static void __exit my_exit(void) {
      free_irq(dev->irq, dev);
      tasklet_kill(&dev->tasklet);  // Wait for tasklet, cancel if pending
      flush_workqueue(dev->wq);     // Wait for workqueue
      destroy_workqueue(dev->wq);
      kfree(dev);                   // Now safe to free
  }
```

### Bug 6: Interrupt Affinity and SMP Races

```
SMP SCENARIO (Multi-CPU):
  CPU 0 is running ISR for IRQ 17
  CPU 1 is running the tasklet for IRQ 17

  ISR writes pending_data (CPU 0)
  Tasklet reads pending_data (CPU 1)
  
  WITHOUT LOCK: CPU 1 may read partial write from CPU 0!
  (Caches not synchronized, memory ordering not guaranteed)

FIX:
  Always use spinlock (with irqsave) to protect shared data.
  Memory barriers are insufficient alone — use proper locking.
  spinlock_irqsave inherently includes the necessary memory barriers.
```

---

## 19. Expert Mental Models and Cognitive Principles

### Mental Model 1: The ISR as a Military Messenger

```
Imagine an ISR as a military messenger in a war zone:

  RULES FOR THE MESSENGER:
  1. Run in, deliver the message, run out — FAST
  2. Don't stop to analyze or discuss the message
  3. Leave the analysis to the generals (workqueue)
  4. Never sit down to rest (no sleep)
  5. If you can't deliver (FIFO full), report it and leave

  ANALOGY MAPPING:
  Messenger arriving    = Hardware interrupt firing
  Delivering message    = Copying hardware registers to RAM
  "Message received"    = Acknowledging interrupt to hardware
  Leaving quickly       = Short ISR returning
  Generals analyzing    = Workqueue processing
```

### Mental Model 2: The Pipeline Model

```
Think of interrupt handling as a CPU pipeline:

STAGE 1: HARDWARE
  Latency: 100 ns
  Parallelism: 1 (one interrupt at a time per CPU)
  Buffer: IRQ line (edge/level triggered)
  
STAGE 2: TOP HALF (ISR)
  Latency: 1-10 µs
  Parallelism: 1 per CPU (IRQs disabled)
  Buffer: Hardware registers (volatile! must drain immediately)
  
STAGE 3: TASKLET (Bottom Half)
  Latency: 10-500 µs
  Parallelism: 1 instance per CPU at a time (serialized)
  Buffer: Per-CPU tasklet queue
  
STAGE 4: WORKQUEUE
  Latency: 100 µs - 10 ms
  Parallelism: N workers (full parallel)
  Buffer: Work item queue (configurable depth)

BOTTLENECK ANALYSIS:
  If Stage 1 is faster than Stage 2: IRQs lost (ACK too slow)
  If Stage 2 is faster than Stage 3: Data corrupted (overwritten)
  If Stage 3 is faster than Stage 4: OK (queued up, processed later)
```

### Mental Model 3: Interrupt Context as "No Process Zone"

```
Think of the kernel as having two worlds:

PROCESS WORLD (normal operation):
  ┌─────────────────────────────────────────┐
  │  Task A | Task B | Task C | kworker/0  │
  │                                         │
  │  Rules: Can sleep, can block, can I/O  │
  │  Identity: Has current task context     │
  │  Stack: Per-task kernel stack           │
  └─────────────────────────────────────────┘

INTERRUPT WORLD (hardware reaction):
  ┌─────────────────────────────────────────┐
  │  IRQ 9 ISR | Softirq | Tasklet         │
  │                                         │
  │  Rules: CANNOT sleep, no blocking      │
  │  Identity: NO current task (borrowed)  │
  │  Stack: Interrupt stack (shared!)       │
  └─────────────────────────────────────────┘

CROSSING THE BOUNDARY:
  Interrupt → Process: schedule_work(), queue_work()  [allowed]
  Process → Interrupt: local_irq_disable()            [allowed]
  Sleep in Interrupt world:                           [FORBIDDEN]
  Use interrupt-world lock in process world:          [requires irqsave]
```

### Mental Model 4: The "How Long?" Test

```
Before writing ANY code in an ISR, ask:
"How long will this take?"

< 100 ns   → Read register, increment counter: FINE in ISR
100-500 ns → memcpy small buffer: FINE in ISR  
1-5 µs     → ACK interrupt, schedule BH: ACCEPTABLE in ISR
5-10 µs    → Absolute maximum for ISR!
10-100 µs  → Must move to TASKLET
100 µs-1ms → Must move to WORKQUEUE
> 1 ms     → Must move to WORKQUEUE or KTHREAD
Any sleep  → Must move to WORKQUEUE or THREADED IRQ
```

### Cognitive Principles for Mastery

**1. Deliberate Practice — The Two-Phase Learning Loop**
```
Phase 1: STUDY the mechanism (what it is, why it exists)
Phase 2: PREDICT the bug (given code X, what breaks, and why?)

Example practice:
  Given: ISR that calls kmalloc(GFP_KERNEL)
  Predict: When will this deadlock? Under what memory pressure?
  Verify: Read mm/page_alloc.c, trace the GFP_KERNEL path.
  
This builds CAUSAL understanding, not just pattern memorization.
```

**2. Chunking — Build the Mental Map**
```
Don't memorize: "use spin_lock_irqsave when ISR and process share data"

Instead, chunk it into first principles:
  CHUNK 1: ISR runs with interrupts disabled
  CHUNK 2: spin_lock() does NOT disable interrupts
  CHUNK 3: Therefore, ISR can preempt code holding spin_lock()
  CHUNK 4: This creates ABBA deadlock (A=process, B=ISR)
  CHUNK 5: spin_lock_irqsave disables interrupts → prevents CHUNK 3

Now you can DERIVE the rule from understanding, never forget it.
```

**3. The Expert's "Why" Chain**
```
Every design decision in Linux has a "why" chain.
Train yourself to always ask:

"Why can't the ISR sleep?"
→ "Because sleeping requires a scheduler context switch"
  → "Why does that matter?"
    → "Because in interrupt context there is no current task to switch from"
      → "Why is there no current task?"
        → "Because the interrupt preempted the CPU between two arbitrary tasks"
          → "Therefore: the 'current task' pointer is undefined/arbitrary"
            → "Therefore: sleeping is undefined behavior"

When you understand the full chain, you understand the WHOLE system.
```

**4. The Adversarial Mindset**
```
After writing any driver code, become your own adversary:

"What if two CPUs receive this interrupt simultaneously?"
"What if the device fires the interrupt before ACK completes?"
"What if my bottom half is still running when the next IRQ fires?"
"What if the work queue is full when I schedule_work()?"
"What happens if my module unloads while a tasklet is pending?"

Each question reveals a potential race condition or resource leak.
This is how kernel developers think. This is how bugs are prevented.
```

---

## 20. Summary Cheat Sheet

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INTERRUPT NESTING — MASTER REFERENCE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  NESTING DEFINITION:                                                       ║
║  One interrupt interrupting another mid-execution. Linux PREVENTS this    ║
║  by clearing IF (Interrupt Flag) when ISR begins. IRET restores IF.       ║
║                                                                            ║
║  EXECUTION CONTEXTS:                                                       ║
║  ┌──────────────────┬───────────────────┬──────────────────┐              ║
║  │ Hard IRQ Context │ Softirq Context   │ Process Context  │              ║
║  │ (ISR Top Half)   │ (Tasklet/Softirq) │ (Workqueue/Thread│              ║
║  ├──────────────────┼───────────────────┼──────────────────┤              ║
║  │ IRQs: disabled   │ IRQs: enabled     │ IRQs: enabled    │              ║
║  │ Preempt: off     │ Preempt: off      │ Preempt: on/off  │              ║
║  │ Sleep: NEVER     │ Sleep: NEVER      │ Sleep: YES       │              ║
║  │ GFP_KERNEL: NO   │ GFP_KERNEL: NO    │ GFP_KERNEL: YES  │              ║
║  │ Mutex: NO        │ Mutex: NO         │ Mutex: YES       │              ║
║  └──────────────────┴───────────────────┴──────────────────┘              ║
║                                                                            ║
║  DEFERRAL MECHANISMS:                                                      ║
║  Softirq    → Ultra-fast, parallel on CPUs, compile-time, no sleep       ║
║  Tasklet    → Fast, serialized, runtime registration, no sleep            ║
║  Workqueue  → Flexible, can sleep, shared thread pool, GFP_KERNEL OK     ║
║  Threaded   → Dedicated thread per IRQ, can sleep, RT-capable            ║
║                                                                            ║
║  LOCK RULES:                                                               ║
║  Process + Softirq   → spin_lock_bh()                                    ║
║  Process + ISR       → spin_lock_irqsave()                               ║
║  ISR + ISR           → spin_lock() (IRQs already disabled in ISR)        ║
║  Process + Process   → mutex (can sleep)                                  ║
║                                                                            ║
║  ISR RETURN VALUES:                                                        ║
║  IRQ_HANDLED   → We owned and handled this interrupt                     ║
║  IRQ_NONE      → Not our interrupt (shared IRQ line)                     ║
║  IRQ_WAKE_THREAD → Wake threaded handler                                 ║
║                                                                            ║
║  TOP 5 BUGS:                                                               ║
║  1. Sleep in ISR → "BUG: scheduling while atomic"                        ║
║  2. Missing ACK → interrupt storm, system freeze                         ║
║  3. Wrong spinlock variant → deadlock                                     ║
║  4. Forgot tasklet_kill() → use-after-free on rmmod                      ║
║  5. GFP_KERNEL in ISR → may sleep → kernel panic                        ║
║                                                                            ║
║  NMI (Non-Maskable Interrupt):                                             ║
║  Cannot be disabled by CLI. Used for: hardware errors, watchdog, NMI     ║
║  profiling. NMI handler has even stricter rules than regular ISR.         ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

*Guide written for deep kernel understanding — from IF flag to workqueue internals.*
*Practice: Read `/proc/interrupts`, `/proc/softirqs` on a live Linux system.*
*Next steps: Study NAPI (network), block layer BIO, and PREEMPT_RT patch.*

Now I'll craft the full guide. This will be deeply detailed — buckle up.Here is the complete guide — 20 deeply structured sections. Let me walk you through the architecture of this guide so you know how to use it:

---

**What This Guide Covers (and Why in That Order)**

The guide is deliberately sequenced from *atoms → molecules → systems*:

1. **Sections 1–4** establish the physical reality — what happens at the CPU silicon level when an interrupt fires. The IF flag, the APIC, the stack save/restore — this is the hardware contract everything else rests on.

2. **Section 5** answers the central question: *why does Linux choose to disable interrupts during ISRs?* The answer comes from three independent forces — stack safety, code simplicity, and hardware ACK ordering. When you understand *all three reasons simultaneously*, the design feels inevitable.

3. **Sections 6–7** define the ISR contract and introduce the top/bottom half split — the single most important architectural pattern in all of Linux driver design. The network card example makes it concrete.

4. **Sections 8–11** are the four deferral mechanisms. Each one trades off latency, context, and flexibility differently. Section 12 gives you a decision tree so you never have to memorize — you reason to the answer.

5. **Section 13** on spinlocks is where most bugs live. The four variants of spinlock (`spin_lock`, `spin_lock_bh`, `spin_lock_irq`, `spin_lock_irqsave`) each correspond to a precise threat model. The table makes the choice mechanical.

6. **Sections 14–16** are full implementations. The C code is production-style kernel module code. The Rust code shows how ownership and the type system can *enforce* the ISR rules at compile time — this is the future of kernel safety. The Go simulation lets you *run and observe* the architecture without needing a kernel build environment.

7. **Section 18** (bugs) is where the real learning happens. Each bug is a *system failure mode* — knowing these is what separates junior driver writers from senior ones.

---

**The Core Insight to Internalize**

Interrupt nesting is not primarily about *preventing re-entrancy* — that is the symptom. The root cause is that **interrupt context has no identity**. There is no `current` task. There is no owner. There is no place to return to if we block. The entire "no sleep" rule, the entire spinlock discipline, the entire top/bottom half architecture — all of it flows logically from this one fact.

Once that clicks, the rules stop being a list to memorize and become *obvious consequences of physics*.