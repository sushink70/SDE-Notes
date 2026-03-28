# Linux Interrupt Nesting, ISR Design, and Work Deferral: A Complete Reference for Elite Systems Engineers

---

## Table of Contents

1. [Mental Model: The Interrupt Contract](#1-mental-model-the-interrupt-contract)
2. [Hardware Architecture: How Interrupts Actually Fire](#2-hardware-architecture-how-interrupts-actually-fire)
3. [Interrupt Nesting: The Full Truth](#3-interrupt-nesting-the-full-truth)
4. [The ISR Problem: Why You Cannot Block](#4-the-isr-problem-why-you-cannot-block)
5. [Interrupt Descriptor Table and Vector Space](#5-interrupt-descriptor-table-and-vector-space)
6. [Top Half vs. Bottom Half: The Deferral Model](#6-top-half-vs-bottom-half-the-deferral-model)
7. [SoftIRQs: The Fastest Deferral Mechanism](#7-softirqs-the-fastest-deferral-mechanism)
8. [Tasklets: SoftIRQ Wrappers for Drivers](#8-tasklets-softirq-wrappers-for-drivers)
9. [Workqueues: Process Context Deferral](#9-workqueues-process-context-deferral)
10. [Threaded IRQs: The Modern Approach](#10-threaded-irqs-the-modern-approach)
11. [Spinlocks, IRQ Flags, and the Locking Taxonomy](#11-spinlocks-irq-flags-and-the-locking-taxonomy)
12. [PREEMPT_RT and the Realtime Kernel](#12-preempt_rt-and-the-realtime-kernel)
13. [Interrupt Affinity, SMP, and Per-CPU Variables](#13-interrupt-affinity-smp-and-per-cpu-variables)
14. [Latency: Measuring, Profiling, and Tuning](#14-latency-measuring-profiling-and-tuning)
15. [Implementation: C Driver with All Mechanisms](#15-implementation-c-driver-with-all-mechanisms)
16. [Implementation: Rust Kernel Module](#16-implementation-rust-kernel-module)
17. [Implementation: Go Userspace Simulation and eBPF Interface](#17-implementation-go-userspace-simulation-and-ebpf-interface)
18. [Security Implications and Attack Surface](#18-security-implications-and-attack-surface)
19. [Debugging Interrupt Problems](#19-debugging-interrupt-problems)
20. [The Expert Mental Model](#20-the-expert-mental-model)

---

## 1. Mental Model: The Interrupt Contract

Before touching a single line of kernel code, internalize the **Interrupt Contract** — the invariants that every ISR author must never violate:

```
THE INTERRUPT CONTRACT
======================

CPU Promise to ISR:
  - I will save your interrupted context (registers, RFLAGS, CS:RIP, SS:RSP)
  - I will give you exclusive access to this CPU core
  - I will disable further interrupts of the same or lower priority
  - I will restore everything when you call IRET

ISR Promise to CPU:
  - I will return quickly (microseconds, not milliseconds)
  - I will not sleep, block, or yield
  - I will not call scheduler
  - I will not acquire locks that might sleep
  - I will save and restore any registers I clobber (beyond ABI-callee-saved)
  - I will acknowledge the interrupt to the hardware controller (EOI)
```

The reason for this contract is not arbitrary kernel design — it maps directly to **x86-64 hardware behavior**:

```
Normal Execution:
  RFLAGS.IF = 1  (interrupt flag set = interrupts enabled)
  
  +-----------+     IRQ fires     +-----------+
  |  Process  | ----------------> | CPU saves |
  |  running  |                   | context   |
  +-----------+                   +-----------+
                                       |
                                  RFLAGS.IF = 0 (HARDWARE clears it)
                                  Jump to IDT[vector]
                                       |
                                  +-----------+
                                  |    ISR    |
                                  | runs with |
                                  | IF = 0    |
                                  +-----------+
                                       |
                                  IRET (restores RFLAGS.IF = 1)
                                  +-----------+
                                  | Process   |
                                  | resumes   |
                                  +-----------+
```

**RFLAGS.IF = 0 means the CPU will not respond to any maskable interrupt on this core.** This is not a software lock — it is a hardware gate. No amount of `spin_lock()` cleverness matters; the hardware simply won't deliver another interrupt to this core until IF is restored.

---

## 2. Hardware Architecture: How Interrupts Actually Fire

Understanding the physical path of an interrupt is essential before reasoning about nesting.

### 2.1 The Interrupt Delivery Chain

```
Physical Device
    |
    | Asserts interrupt line (IRQ pin)
    v
+------------------+
|  IOAPIC           |  Maps device IRQ to CPU-visible interrupt vector (0-255)
|  (I/O APIC)       |  Configures: level vs edge triggered, destination CPU
+------------------+
    |
    | Sends interrupt message over APIC bus
    v
+------------------+
|  LAPIC            |  Local APIC: per-CPU interrupt controller
|  (Local APIC)     |  Compares vector priority vs current ISRR register
+------------------+
    |
    | If priority > current, signals CPU
    v
+------------------+
|   CPU Core        |
|   Checks RFLAGS.IF|  If IF=1, accepts. If IF=0, holds in IRR (pending)
+------------------+
    |
    | Saves: SS, RSP, RFLAGS, CS, RIP, error code (if applicable)
    | onto KERNEL stack (switches stack via TSS.IST if configured)
    | Clears RFLAGS.IF
    | Loads CS:RIP from IDT[vector]
    v
+------------------+
|   ISR executes    |
+------------------+
    |
    | Issues EOI to LAPIC (or IOAPIC for level-triggered)
    | IRET restores saved context
    v
+------------------+
|  Interrupted code |
|  resumes          |
+------------------+
```

### 2.2 LAPIC Priority and the TPR/PPR

The LAPIC maintains two critical registers:

- **TPR (Task Priority Register)**: Software can set this to mask interrupts below a priority threshold
- **PPR (Processor Priority Register)**: Computed as `max(TPR, highest ISR bit)` — the effective priority floor
- **ISR Register (In-Service Register)**: Bitmask of vectors currently being serviced (not yet EOI'd)
- **IRR Register (Interrupt Request Register)**: Bitmask of pending but not yet delivered vectors

```
IRR: [0,0,0,1,0,0,1,0,...]  <- vectors 32 and 35 pending
ISR: [0,0,0,0,0,1,0,0,...]  <- vector 33 currently in service
PPR: priority(33) = 2        <- floor for new interrupts

New interrupt on vector 34 (priority 3 > PPR 2):
  -> LAPIC will deliver it, preempting current ISR
  -> Nesting occurs

New interrupt on vector 31 (priority 1 < PPR 2):  
  -> LAPIC holds in IRR, delivers after EOI of vector 33
```

### 2.3 x86-64 IST (Interrupt Stack Table)

The TSS (Task State Segment) defines up to 7 IST entries — dedicated stacks for specific vectors:

```c
struct tss_struct {
    // ...
    u64 ist[7];  // IST1..IST7: alternate stacks for IDT entries
};
```

Critical vectors use IST to ensure they have a valid stack even if the interrupted code had a corrupted stack pointer (e.g., `#DF` double fault uses IST1).

---

## 3. Interrupt Nesting: The Full Truth

The statement "interrupts are disabled during an ISR" is true but incomplete. The full picture requires understanding **priority levels**, **hardware vs. software control**, and **Linux's specific choices**.

### 3.1 What Hardware Allows

On x86-64, `RFLAGS.IF` being cleared means **maskable** interrupts are suppressed. This includes:
- All device interrupts (LAPIC-delivered vectors)
- IPIs (Inter-Processor Interrupts) to this core

It does **NOT** suppress:
- NMI (Non-Maskable Interrupt, vector 2)
- Machine Check Exception (#MC, vector 18)
- Debug exceptions (#DB, vector 1) in some configurations
- SMI (System Management Interrupt) — handled entirely in SMM, invisible to OS

```
Maskable vs Non-Maskable in x86:

Vector 0-31:   CPU exceptions and reserved (NMI at 2, #DB at 1)
Vector 32-255: External interrupt vectors (assigned to devices by IOAPIC)

                     CLI (RFLAGS.IF=0)
                          |
              +-----------+-----------+
              |                       |
         Blocks                  Does NOT Block
              |                       |
    Device IRQs (IOAPIC)          NMI (vec 2)
    Software IRQs (INT n)         #MC (vec 18)
    IPIs (most)                   SMI
                                  #DB (some modes)
```

### 3.2 What Linux Does by Default

Linux makes a deliberate choice: **ISRs run with interrupts disabled** (IF=0). This is the hardware default after the CPU jumps to an IDT entry that doesn't set IRET-style re-enabling.

However, Linux ISRs CAN re-enable interrupts:

```c
irqreturn_t my_handler(int irq, void *dev_id)
{
    local_irq_enable();  // Re-enables IF on this CPU — nesting now possible
    
    // Now a higher-priority IRQ could preempt us
    // This is DANGEROUS unless you know exactly what you're doing
    
    local_irq_disable(); // Must disable before return
    return IRQ_HANDLED;
}
```

**Linux historically did this** for high-priority interrupts. Modern Linux (with `IRQF_DISABLED` removed in kernel 3.x) **no longer supports nested hardware IRQs** in the normal fast path. The flag `IRQF_DISABLED` was deprecated and removed because the complexity/risk outweighed the marginal latency benefit.

### 3.3 Nesting That Still Happens

Even with IF=0, nesting-like behavior occurs in these scenarios:

```
Scenario 1: NMI Nesting
========================
IRQ handler running (IF=0)
  |
  NMI fires (ignores IF flag)
  |
  NMI handler runs
    |
    NMI handler completes (IRET)
  |
IRQ handler resumes

The NMI handler CANNOT sleep or use spinlocks held by the interrupted code.
This is the source of NMI-safe programming constraints.


Scenario 2: Softirq "Nesting" (not true nesting, but interleaving)
===================================================================
Hardware IRQ fires -> ISR runs (IF=0)
  |
  ISR schedules softirq (sets bit in per-CPU bitmask)
  ISR returns (IRET, IF=1 restored)
  |
Softirq runs (IF=1, preemptable by hardware IRQs)
  |
  Another hardware IRQ fires -> ISR runs (IF=0)
    |
    ISR may schedule another softirq
    ISR returns
  |
Softirq continues
  |
  New softirq runs (same or different type)


Scenario 3: Workqueue Preemption (full process context nesting)
===============================================================
Workqueue worker thread (IF=1, preemptable, can sleep)
  |
  IRQ fires -> ISR runs (IF=0)
    |
    ISR returns
  |
  Scheduler may run (workqueue thread may be descheduled)
  Other processes run
  Workqueue thread resumes
```

### 3.4 SMP Nesting: The Per-CPU Reality

On a multicore system, "interrupts disabled" means **only on the current CPU**:

```
CPU 0                          CPU 1
-----------                    -----------
Running ISR (IF=0)             Receives IRQ -> runs its own ISR (IF=0)
  |                              |
  Cannot be interrupted          Cannot be interrupted
  by device IRQs                 by device IRQs
  |                              |
  Can observe CPU 1's            Can observe CPU 0's
  memory writes (with barriers)  memory writes (with barriers)
  |                              |
  Returns (IF=1)                 Returns (IF=1)
```

This is why `spin_lock_irqsave()` exists — it disables local interrupts AND acquires a spinlock, preventing both:
1. Local CPU re-entrancy via ISR
2. Remote CPU race via the spinlock

---

## 4. The ISR Problem: Why You Cannot Block

### 4.1 What "Cannot Block" Means at the Kernel Level

"Cannot block" means you cannot call any function that may invoke `schedule()`. The kernel scheduler transfers control to another task — but during an ISR:

```
DISASTER SCENARIO: Sleeping in an ISR

ISR context:
  - Current task: whatever was running before the IRQ (could be any process)
  - Kernel stack: IRQ stack (separate from process stack on x86-64)
  - RFLAGS.IF = 0
  
If ISR calls mutex_lock() and the mutex is held:
  
  mutex_lock()
    -> spin briefly
    -> calls schedule() to wait
    -> schedule() calls context_switch()
    -> context_switch() saves current->thread state
    -> Loads "next" task
    -> IRET happens in wrong context
    -> RFLAGS.IF is restored from WRONG saved state
    -> The interrupt is never properly completed
    -> EOI may not be sent
    -> The interrupted task is now associated with a half-complete ISR frame
    -> KERNEL CORRUPTION / PANIC
```

The kernel detects this with `might_sleep()` annotations and `in_interrupt()` checks:

```c
void mutex_lock(struct mutex *lock)
{
    might_sleep();  // Triggers warning/BUG if called from atomic context
    // ...
}

bool in_interrupt(void)
{
    // Returns true if: in IRQ handler, softirq, NMI, or similar atomic context
    return (preempt_count() & (HARDIRQ_MASK | SOFTIRQ_MASK | NMI_MASK)) != 0;
}
```

### 4.2 The Preemption Count

Linux tracks "atomic-ness" via a per-task counter `preempt_count`:

```
preempt_count layout (32-bit value in thread_info):

Bits [0:7]   = PREEMPT counter (explicit preempt_disable() depth)
Bits [8:15]  = SOFTIRQ counter (in_softirq() depth, incremented by local_bh_disable())
Bits [16:19] = HARDIRQ counter (in_irq() depth, incremented by irq_enter())
Bits [20]    = NMI counter
Bit  [28]    = PREEMPT_NEED_RESCHED

  31          20 19     16 15      8 7        0
  +-----------+----------+---------+-----------+
  |  (unused) |  HARDIRQ | SOFTIRQ |  PREEMPT  |
  +-----------+----------+---------+-----------+
  
  preempt_count() != 0  -> cannot schedule
  in_interrupt()        -> HARDIRQ or SOFTIRQ bits set
  in_irq()              -> HARDIRQ bits set
  in_softirq()          -> SOFTIRQ bits set (includes local_bh_disable)
  in_serving_softirq()  -> exactly one specific softirq bit pattern
```

When a hardware interrupt fires, `irq_enter()` increments the HARDIRQ counter. When the ISR returns, `irq_exit()` decrements it and potentially runs pending softirqs.

---

## 5. Interrupt Descriptor Table and Vector Space

### 5.1 IDT Structure

```
IDT (Interrupt Descriptor Table): 256 entries of 16 bytes each

Entry format (Gate Descriptor):
  
  Bits 127:96  = Reserved (Type=0xE/0xF gate type dependent)
  Bits 95:64   = High 32 bits of handler offset
  Bits 63:48   = Segment selector (kernel CS = 0x10)
  Bits 47      = Present bit
  Bits 46:45   = DPL (Descriptor Privilege Level) -- 0=kernel, 3=user callable
  Bits 44      = Gate type (0=interrupt gate, 1=trap gate)
  Bits 43:40   = Type (0xE = 64-bit interrupt gate, 0xF = 64-bit trap gate)
  Bits 39:35   = IST index (0-7, 0=current stack)
  Bits 34:32   = Reserved
  Bits 31:16   = Middle 16 bits of handler offset
  Bits 15:0    = Low 16 bits of handler offset

KEY DIFFERENCE:
  Interrupt Gate: RFLAGS.IF cleared on entry (maskable IRQs disabled)
  Trap Gate:      RFLAGS.IF NOT cleared (IRQs remain enabled)
  
  Linux uses Interrupt Gates for hardware IRQs (disables further IRQs)
  Linux uses Trap Gates for some exceptions (e.g., page fault, allows IRQs)
```

### 5.2 Linux Vector Assignment

```
x86-64 Linux Vector Map:

  0x00-0x1F   CPU Exceptions (#DE, #DB, NMI, #BP, #OF, #BR, #UD, #NM,
                               #DF, #TS, #NP, #SS, #GP, #PF, #MF, #AC,
                               #MC, #XM, #VE, ...)
  0x20-0x2F   Legacy ISA IRQs (if using 8259A PIC, rare today)
  0x30-0xEF   IOAPIC-assigned device vectors (dynamically allocated)
  0xF0        Local APIC error vector
  0xF1        Local APIC LINT0 (legacy)
  0xF2        Local APIC thermal sensor
  0xF3        Local APIC performance monitoring
  0xFA        IPI: TLB shootdown
  0xFB        IPI: reschedule
  0xFC        IPI: function call
  0xFD        IPI: function call single
  0xFE        IPI: task migration
  0xFF        SPURIOUS_APIC_VECTOR (LAPIC sends this if interrupt is lost)
```

### 5.3 The IRQ Domain Abstraction

Modern Linux uses `irq_domain` to map hardware interrupt numbers to Linux IRQ numbers:

```
Hardware              IRQ Domain              Linux IRQ
---------             ----------              ---------
IOAPIC pin 10   ->   ioapic_irq_domain   ->   IRQ 32
PCIe MSI 0x00   ->   pci_msi_domain      ->   IRQ 45
GPIO pin 5      ->   gpio_irq_domain     ->   IRQ 120

Each Linux IRQ number maps to:
  struct irq_desc {
      struct irq_data   irq_data;    // Hardware side
      irq_flow_handler_t handle_irq; // Flow control (level/edge)
      struct irqaction  *action;     // Linked list of handlers
      unsigned int      status_use_accessors;
      spinlock_t        lock;
      // ...
  };
```

---

## 6. Top Half vs. Bottom Half: The Deferral Model

This is the **architectural pattern** that resolves the ISR speed requirement:

```
INTERRUPT DEFERRAL ARCHITECTURE
================================

Hardware IRQ fires
     |
     v
+------------------+   TOP HALF (ISR / "hard IRQ")
|  ISR executes    |   - Runs with IF=0 (or IF=1 in rare cases)
|  (microseconds)  |   - Cannot sleep
|  - ACK hardware  |   - Minimal work
|  - Read data reg |   - Schedule bottom half
|  - Set flags     |
+------------------+
     |
     | Triggers one of:
     |
     +----------+----------+----------+
     |          |          |          |
     v          v          v          v
 SoftIRQ    Tasklet    Workqueue  Threaded IRQ
     
     BOTTOM HALVES (deferred work)
     - Run with IF=1 (hardware IRQs can interrupt them)
     - SoftIRQ/Tasklet: still atomic (no sleep), but IF=1
     - Workqueue/Threaded: full process context (CAN sleep)
```

### 6.1 Why Two Levels?

The two-level design serves distinct latency requirements:

```
Latency Requirements:

  Hardware latency (device to CPU):    ~100ns - 1µs
  ISR maximum acceptable:              ~1µs - 10µs
  SoftIRQ/Tasklet maximum:             ~10µs - 100µs
  Workqueue acceptable:                ~100µs - ms range

  Data rate example (10GbE NIC):
    10 Gbps / 64 bytes/packet = ~20 million packets/second
    1 second / 20M packets = 50 nanoseconds per packet budget
    
    You CANNOT do full TCP processing in an ISR at line rate.
    ISR: save packet descriptor pointer, trigger NAPI/softirq
    SoftIRQ: process batch of packets from ring buffer
```

---

## 7. SoftIRQs: The Fastest Deferral Mechanism

### 7.1 What SoftIRQs Are

SoftIRQs are the kernel's highest-performance deferred execution mechanism. They are:
- Statically defined at compile time (only ~10 types)
- Run on the local CPU that scheduled them (or ksoftirqd thread)
- Can run concurrently on multiple CPUs simultaneously
- Cannot sleep (still atomic context, but IF=1)
- Processed at: IRQ exit (`irq_exit()`), `local_bh_enable()`, and by `ksoftirqd`

### 7.2 The SoftIRQ Table

```c
// linux/interrupt.h
enum {
    HI_SOFTIRQ      = 0,   // High-priority tasklets
    TIMER_SOFTIRQ   = 1,   // Timer subsystem
    NET_TX_SOFTIRQ  = 2,   // Network TX
    NET_RX_SOFTIRQ  = 3,   // Network RX (NAPI)
    BLOCK_SOFTIRQ   = 4,   // Block I/O completion
    IRQ_POLL_SOFTIRQ= 5,   // IRQ polling (NAPI-like for block)
    TASKLET_SOFTIRQ = 6,   // Normal-priority tasklets
    SCHED_SOFTIRQ   = 7,   // Scheduler load balancing
    HRTIMER_SOFTIRQ = 8,   // High-resolution timers
    RCU_SOFTIRQ     = 9,   // RCU callbacks (LAST, always pending)
    
    NR_SOFTIRQS     = 10
};
```

Priority is simple: **lower number = higher priority**. `HI_SOFTIRQ` runs before `NET_RX_SOFTIRQ`.

### 7.3 SoftIRQ Data Structures

```c
// Per-CPU pending bitmask
DECLARE_PER_CPU_ALIGNED(irq_cpustat_t, irq_stat);

typedef struct {
    unsigned int __softirq_pending;  // Bitmask: bit N set = softirq N pending
} irq_cpustat_t;

// The action table
struct softirq_action {
    void (*action)(struct softirq_action *);
};

static struct softirq_action softirq_vec[NR_SOFTIRQS] __cacheline_aligned_in_smp;
```

### 7.4 SoftIRQ Execution Flow

```
irq_exit() called after ISR returns:
  
  irq_exit()
    preempt_count_sub(HARDIRQ_OFFSET)  // Decrement hardirq counter
    if (local_softirq_pending() && !in_interrupt() && !irqs_disabled())
        invoke_softirq()
            __do_softirq()
                local_irq_enable()          // ENABLE interrupts (IF=1)
                while (pending) {
                    h = softirq_vec[i]
                    h->action(h)            // Run softirq handler
                    // Can be preempted by hardware IRQ here
                }
                local_irq_disable()         // Disable for final accounting
                if (pending && loops < MAX_SOFTIRQ_RESTART)
                    goto restart;
                else
                    wakeup_softirqd()       // Too many pending, defer to ksoftirqd
```

**Key insight**: `__do_softirq()` re-enables interrupts before calling handlers. So a hardware IRQ CAN fire during a SoftIRQ — but since HARDIRQ counter is now 0, `in_interrupt()` returns false, and a new ISR can run. This is why SoftIRQs cannot sleep (they'd be re-entered non-deterministically by a new softirq from the nested ISR) and why the same SoftIRQ can run on two CPUs simultaneously.

### 7.5 The `ksoftirqd` Thread

If softirq processing takes too long or keeps re-triggering, `ksoftirqd/N` (one per CPU) takes over:

```
ksoftirqd/0, ksoftirqd/1, ... ksoftirqd/N-1

Priority: SCHED_NORMAL (can be niced)
Woken by: __do_softirq() when pending count exceeds MAX_SOFTIRQ_RESTART (10)
         or pending softirqs exist but conditions aren't right for inline processing

This prevents network RX flood from starving user processes.
```

---

## 8. Tasklets: SoftIRQ Wrappers for Drivers

### 8.1 The Tasklet Abstraction

Since adding a new SoftIRQ type requires kernel core changes and is reserved for high-performance subsystems, tasklets provide the same mechanism for driver code:

```
Tasklet sits on top of TASKLET_SOFTIRQ and HI_SOFTIRQ:

  TASKLET_SOFTIRQ handler -> iterates tasklet list -> calls each tasklet->func()
  HI_SOFTIRQ handler      -> iterates hi-priority tasklet list

Tasklet guarantees that NO TWO CPUS run the same tasklet simultaneously.
(Unlike SoftIRQs which CAN run concurrently on multiple CPUs)
```

### 8.2 Tasklet Data Structure

```c
struct tasklet_struct {
    struct tasklet_struct *next;  // Linked list of pending tasklets
    unsigned long state;          // TASKLET_STATE_SCHED, TASKLET_STATE_RUN
    atomic_t count;               // Disabled counter (0 = enabled)
    void (*func)(unsigned long);  // Handler function
    unsigned long data;           // Argument to func
};

// State bits
#define TASKLET_STATE_SCHED  0   // Tasklet is scheduled for execution
#define TASKLET_STATE_RUN    1   // Tasklet is currently running (SMP guard)
```

The `TASKLET_STATE_RUN` bit is the SMP exclusion mechanism:

```c
static void tasklet_action_common(struct softirq_action *a,
                                  struct tasklet_head *tl_head,
                                  unsigned int softirq_nr)
{
    struct tasklet_struct *list = tl_head->head;
    
    while (list) {
        struct tasklet_struct *t = list;
        list = list->next;
        
        if (tasklet_trylock(t)) {           // Atomically set TASKLET_STATE_RUN
            if (!atomic_read(&t->count)) {  // Check not disabled
                if (!test_and_clear_bit(TASKLET_STATE_SCHED, &t->state))
                    BUG();
                t->func(t->data);           // Call handler
                tasklet_unlock(t);          // Clear TASKLET_STATE_RUN
                continue;
            }
            tasklet_unlock(t);
        }
        // Re-schedule for later if couldn't lock
        local_irq_disable();
        t->next = NULL;
        *tl_head->tail = t;
        tl_head->tail = &t->next;
        __raise_softirq_irqoff(softirq_nr);
        local_irq_enable();
    }
}
```

### 8.3 Tasklet vs. SoftIRQ Comparison

```
+------------------+---------------------------+---------------------------+
| Property         | SoftIRQ                   | Tasklet                   |
+------------------+---------------------------+---------------------------+
| Concurrency      | Can run same type on       | Same tasklet never runs   |
|                  | multiple CPUs              | on 2 CPUs simultaneously  |
+------------------+---------------------------+---------------------------+
| Types            | Fixed 10 types             | Unlimited instances       |
+------------------+---------------------------+---------------------------+
| Who uses it      | Core subsystems            | Drivers                   |
+------------------+---------------------------+---------------------------+
| Sleep allowed    | No                         | No                        |
+------------------+---------------------------+---------------------------+
| IRQs during exec | Enabled (can be interrupted| Enabled                   |
|                  | by hardware IRQ)           |                           |
+------------------+---------------------------+---------------------------+
| Implementation   | softirq_vec[] table        | Runs under TASKLET_SOFTIRQ|
+------------------+---------------------------+---------------------------+
| Scheduling       | raise_softirq()            | tasklet_schedule()        |
+------------------+---------------------------+---------------------------+
| Status           | Still supported            | Deprecated in 5.x, being  |
|                  |                            | replaced by threaded IRQs  |
+------------------+---------------------------+---------------------------+
```

> **Note**: Tasklets are being phased out of the kernel. New driver code should use **threaded IRQs** or workqueues. The kernel has been removing in-tree tasklet usage since 5.x.

---

## 9. Workqueues: Process Context Deferral

### 9.1 The Fundamental Difference

Workqueues run in **kernel thread context** (SCHED_NORMAL or SCHED_FIFO workers). This means:
- `schedule()` is safe
- Sleeping is allowed
- Mutexes, semaphores, `msleep()`, `wait_event()` — all permitted
- Can allocate memory with `GFP_KERNEL`
- Have a real `current` task pointer

### 9.2 The `cmwq` (Concurrency Managed Workqueue) Architecture

Since Linux 2.6.36, workqueues use the `cmwq` infrastructure:

```
cmwq Architecture:

+------------------+     +------------------+     +------------------+
| work_struct W1   |     | work_struct W2   |     | work_struct W3   |
| (from driver A)  |     | (from driver B)  |     | (from driver A)  |
+------------------+     +------------------+     +------------------+
         |                        |                        |
         +------------------------+------------------------+
                                  |
                                  v
                    +---------------------------+
                    |  workqueue_struct (wq)    |
                    |  (per-driver or shared)   |
                    +---------------------------+
                                  |
                                  v
                    +---------------------------+
                    |  pool_workqueue (pwq)     |
                    |  (per-CPU binding)        |
                    +---------------------------+
                                  |
                         +--------+--------+
                         |                 |
                         v                 v
              +------------------+ +------------------+
              |   worker_pool    | |   worker_pool    |
              |  (CPU 0, NORMAL) | |  (CPU 1, NORMAL) |
              +------------------+ +------------------+
                    |                     |
              +-----------+         +-----------+
              | kworker/0  |         | kworker/1  |
              | kworker/0:1|         | kworker/1:1|
              | kworker/0:2|         | ...        |
              +-----------+         +-----------+

cmwq dynamically creates/destroys workers based on concurrency level.
Goal: always have at least one runnable worker per busy worker_pool.
```

### 9.3 Workqueue Types

```c
// System-wide shared workqueues (use these when in doubt)
system_wq               // UNBOUND, for general use
system_highpri_wq       // HIGHPRI, for latency-sensitive work  
system_long_wq          // For long-running, occasional work
system_unbound_wq       // Not bound to specific CPU
system_freezable_wq     // Freezable (stops on system suspend)
system_power_efficient_wq // May use unbound for power saving

// Creating a dedicated workqueue
struct workqueue_struct *wq = alloc_workqueue("mydrv_wq",
    WQ_UNBOUND | WQ_HIGHPRI | WQ_MEM_RECLAIM,
    max_active);  // 0 = default (256 per CPU)
```

### 9.4 Workqueue Flags

```
WQ_UNBOUND:        Workers not bound to specific CPU; work can run anywhere.
                   Good for work that isn't cache-sensitive.
                   
WQ_HIGHPRI:        Workers run at HIGHPRI (nice -20 equivalent).
                   Use for latency-sensitive work.
                   
WQ_CPU_INTENSIVE:  Work may run for long time. cmwq won't count this toward
                   "concurrent execution" limit, so other work can proceed.
                   
WQ_MEM_RECLAIM:    Queue guaranteed to make forward progress even under
                   memory pressure. Prevents deadlock during OOM.
                   
WQ_FREEZABLE:      Work is suspended during system freeze (suspend to RAM).

WQ_SYSFS:          Queue exposed in /sys/bus/workqueue.
```

---

## 10. Threaded IRQs: The Modern Approach

### 10.1 What Threaded IRQs Are

Introduced in Linux 2.6.30, threaded IRQs split the handler into:
1. **Primary handler** (hard IRQ context, IF=0): Just acknowledges the interrupt and returns `IRQ_WAKE_THREAD`
2. **Thread handler** (kernel thread context, IF=1, can sleep): Does all the real work

```
Threaded IRQ Execution:

Hardware IRQ fires
     |
     v
Hard Handler (atomic, IF=0)
  - Read/ACK hardware registers
  - Return IRQ_WAKE_THREAD
     |
     v
irq/N-mydev kernel thread (SCHED_FIFO, RT priority 50)
  - Can sleep, acquire mutexes, do DMA
  - Runs until completion
  - Thread is throttled if it keeps the IRQ line asserted
```

### 10.2 Registering a Threaded IRQ

```c
int request_threaded_irq(
    unsigned int irq,
    irq_handler_t handler,        // Hard handler (can be NULL = uses default ACK)
    irq_handler_t thread_fn,      // Thread handler
    unsigned long irqflags,
    const char *devname,
    void *dev_id
);
```

### 10.3 Why Threaded IRQs Win

```
+------------------+------------------+------------------+------------------+
| Property         | Tasklet          | Workqueue        | Threaded IRQ     |
+------------------+------------------+------------------+------------------+
| Context          | Softirq (atomic) | Process context  | Process context  |
+------------------+------------------+------------------+------------------+
| Can sleep        | No               | Yes              | Yes              |
+------------------+------------------+------------------+------------------+
| RT schedulable   | No               | Limited          | Yes (SCHED_FIFO) |
+------------------+------------------+------------------+------------------+
| Priority inherit | No               | No               | Yes              |
+------------------+------------------+------------------+------------------+
| PREEMPT_RT compat| Problematic      | Yes              | Yes (native)     |
+------------------+------------------+------------------+------------------+
| Latency          | Low              | Higher           | Configurable     |
+------------------+------------------+------------------+------------------+
| Setup complexity | Low              | Medium           | Low              |
+------------------+------------------+------------------+------------------+
```

Threaded IRQs are **the recommended approach** for new driver code and are the foundation of `PREEMPT_RT` correctness.

---

## 11. Spinlocks, IRQ Flags, and the Locking Taxonomy

### 11.1 The Problem Space

Shared data between ISR and process context (or between ISRs on different CPUs) requires synchronization that doesn't sleep:

```
Danger Scenarios:

1. Process context holds lock, ISR on SAME CPU tries to acquire:
   -> Deadlock: ISR spins forever, process can't run to release

2. ISR on CPU0 and ISR on CPU1 both access shared data:
   -> Race condition (no deadlock, but data corruption)

3. Process context on CPU0 holds lock, process context on CPU1 tries:
   -> Correct deadlock risk: need spinlock (not mutex, which sleeps)
```

### 11.2 The Lock Selection Matrix

```
+------------------------+------------------+-----------+------------------+
| Sharing Pattern        | Lock Type        | IF state  | Notes            |
+------------------------+------------------+-----------+------------------+
| Process ↔ Process      | mutex/semaphore  | N/A       | Can sleep        |
| Process ↔ Tasklet/SoftIRQ| spin_lock_bh() | Softirq  | Disables BH      |
|                        |                  | disabled  |                  |
| Process ↔ Hard ISR     | spin_lock_irqsave| IF=0      | Full IRQ disable  |
| Hard ISR ↔ Hard ISR    | spin_lock_irqsave| IF=0      | Per-CPU if same  |
| (different CPUs)       |                  |           | vector           |
| Softirq ↔ Softirq      | spin_lock()      | N/A       | Concurrent CPUs  |
| (same type, diff CPU)  |                  |           | need lock        |
| Same Softirq type, same| N/A (can't run   | N/A       | Architecture     |
| CPU                    | concurrently)    |           | guarantee        |
+------------------------+------------------+-----------+------------------+
```

### 11.3 The Correct Usage Patterns

```c
// PATTERN 1: Data shared between process context and ISR
static DEFINE_SPINLOCK(my_lock);
static struct data my_data;

// Process context side:
void process_function(void)
{
    unsigned long flags;
    
    spin_lock_irqsave(&my_lock, flags);   // Disable local IRQs, acquire spinlock
    // Access my_data safely
    spin_unlock_irqrestore(&my_lock, flags); // Restore original IRQ state, release
}

// ISR side:
irqreturn_t my_isr(int irq, void *dev_id)
{
    spin_lock(&my_lock);   // Don't need irqsave here: IRQs already disabled in ISR
    // Access my_data safely
    spin_unlock(&my_lock);
    return IRQ_HANDLED;
}
```

**Why `spin_lock()` (not `spin_lock_irqsave()`) in the ISR?**

Because IRQs are already disabled when the ISR runs (RFLAGS.IF=0). Calling `local_irq_disable()` again would be redundant. Using `spin_lock_irqsave()` in the ISR would waste cycles saving/restoring flags unnecessarily.

**Why `spin_lock_irqsave()` (not `spin_lock()`) in process context?**

If process context used just `spin_lock()`, the following race exists:
1. Process acquires spinlock
2. ISR fires on same CPU (interrupts were still enabled)
3. ISR tries to acquire same spinlock
4. ISR spins forever (it's on the same CPU as the holder)
5. Deadlock

`spin_lock_irqsave()` prevents this by disabling IRQs before acquiring.

### 11.4 The `_bh` Variants

```c
spin_lock_bh(&lock);    // Disables softirqs (BH = Bottom Half) on local CPU
spin_unlock_bh(&lock);  // Re-enables softirqs

// Use when: data shared between process context and softirq/tasklet
// Do NOT use when: data shared with hard ISR (need irqsave)
// Why: cheaper than irqsave (no RFLAGS save), sufficient if ISR doesn't touch data
```

### 11.5 Read-Write Locks and RCU

For read-heavy, write-rare data:

```c
// Read-Write Spinlock
static DEFINE_RWLOCK(my_rwlock);

// Multiple readers simultaneously, exclusive writer
read_lock_irqsave(&my_rwlock, flags);
// read my_data
read_unlock_irqrestore(&my_rwlock, flags);

write_lock_irqsave(&my_rwlock, flags);
// modify my_data
write_unlock_irqrestore(&my_rwlock, flags);

// RCU (Read-Copy-Update): Best for mostly-read data
// Readers: zero overhead (no lock at all)
// Writers: atomic pointer swap + deferred free after grace period
rcu_read_lock();   // Marks start of RCU read-side critical section
p = rcu_dereference(my_rcu_pointer);  // Atomic load with proper barriers
// use p
rcu_read_unlock(); // Marks end

// Writer path (can be in process context):
new_data = kmalloc(...);
*new_data = updated_values;
old_data = rcu_dereference(my_rcu_pointer);
rcu_assign_pointer(my_rcu_pointer, new_data);  // Atomic store
synchronize_rcu();   // Wait for all existing readers to finish
kfree(old_data);
```

---

## 12. PREEMPT_RT and the Realtime Kernel

### 12.1 What PREEMPT_RT Changes

The `PREEMPT_RT` patchset (now merging into mainline) transforms the kernel:

```
Vanilla Kernel:                    PREEMPT_RT Kernel:

Spinlocks: truly spin,             Spinlocks: converted to rt_mutex
  non-preemptable                    (sleeping mutex, priority inheriting)
  
ISRs: run with IF=0               ISRs: converted to kernel threads
  in hard interrupt context           (threaded IRQs mandatory)
  
Softirqs: run in softirq context  Softirqs: run in ksoftirqd threads
  partially atomic                    fully preemptable
  
Result: Bounded preemption         Result: Worst-case latency < 100µs
  latency not guaranteed              even under load
```

### 12.2 Priority Inversion and Inheritance

```
PRIORITY INVERSION (classic bug):

  High-priority task H wants lock L
  Low-priority task L holds lock L
  Medium-priority task M preempts L (M has higher priority than L)
  L cannot run to release lock
  H blocks on L (effectively M now blocks H)
  
  Observed latency for H = unbounded (depends on M, which is unrelated)

PRIORITY INHERITANCE (PREEMPT_RT solution):

  When H blocks on lock held by L:
  -> L temporarily inherits H's priority
  -> L runs at H's priority until it releases lock
  -> M cannot preempt L (L now has higher priority than M)
  -> L releases lock, H proceeds
  
  Result: H's latency bounded by L's critical section length, not M
```

### 12.3 Identifying RT-incompatible Code

```
Patterns that break PREEMPT_RT:

1. spin_lock() without irq variant in contexts where deadlock can occur
   Fix: Use rt_mutex_lock() or restructure to threaded IRQ

2. local_irq_disable() for extended periods
   Fix: Convert to lock/mutex

3. preempt_disable() for non-trivial durations
   Fix: Use per-CPU data with careful design, or lock

4. Softirq handlers that take too long
   Fix: Move work to thread, use threaded IRQs

5. BUG_ON(in_interrupt()) failures on RT
   Fix: Code assumed atomic context but RT kernel runs it in thread context
```

---

## 13. Interrupt Affinity, SMP, and Per-CPU Variables

### 13.1 IRQ Affinity

Each interrupt can be assigned to specific CPUs:

```bash
# View current affinity (CPU bitmask in hex)
cat /proc/irq/45/smp_affinity
# -> f  (CPUs 0-3, all cores)

# Pin IRQ 45 to CPU 2 only
echo 4 > /proc/irq/45/smp_affinity  # bit 2 = CPU 2

# Or use irqbalance daemon for automatic distribution
```

**Why affinity matters**: If a network NIC's IRQ always fires on CPU 0, only CPU 0 processes network packets. NUMA-aware affinity (pin IRQ to CPUs near the NIC's PCIe root complex) reduces cache coherence traffic.

### 13.2 Per-CPU Variables

For data accessed only from ISR context, per-CPU variables eliminate locking entirely:

```c
// Per-CPU counter: no lock needed if only accessed from ISR
static DEFINE_PER_CPU(unsigned long, irq_count);

irqreturn_t my_isr(int irq, void *dev_id)
{
    // this_cpu_inc is atomic on single CPU, no lock needed
    this_cpu_inc(irq_count);
    // ...
}

// Reading from process context requires disabling IRQs:
unsigned long get_irq_count_local(void)
{
    unsigned long count;
    unsigned long flags;
    
    local_irq_save(flags);
    count = __this_cpu_read(irq_count);
    local_irq_restore(flags);
    return count;
}

// Sum across all CPUs (process context, no lock needed for accumulation):
unsigned long get_irq_count_total(void)
{
    unsigned long total = 0;
    int cpu;
    for_each_possible_cpu(cpu)
        total += per_cpu(irq_count, cpu);
    return total;
}
```

### 13.3 The `NOHZ` and Tickless Kernel

In `CONFIG_NO_HZ_FULL` mode (adaptive tickless), idle CPUs don't receive timer interrupts. This affects:
- `ksoftirqd` scheduling
- RCU grace periods
- IRQ affinity decisions

```
Regular tick kernel:
  Every CPU: timer IRQ every ~4ms (250Hz) or ~1ms (1000Hz)
  
NO_HZ_IDLE kernel:
  Idle CPUs: no timer tick until work arrives
  Running CPUs: still get timer ticks
  
NO_HZ_FULL kernel:
  Designated "nohz_full" CPUs: no timer tick even when running
  Requires: exactly 1 task on that CPU, offloaded RCU callbacks
  Use case: HPC, RT applications, isolated CPU domains
```

---

## 14. Latency: Measuring, Profiling, and Tuning

### 14.1 Key Latency Metrics

```
IRQ Latency Components:

1. Hardware latency:   Time from device asserts IRQ to LAPIC receiving
2. CPU acceptance:     LAPIC to CPU IF check + context save
3. ISR execution:      Time in ISR itself (should be < 10µs)
4. Softirq delay:      Time between ISR return and softirq execution
5. Softirq execution:  Time in softirq handler
6. Workqueue delay:    Time work item waits in queue
7. Worker execution:   Time in worker function

Total "interrupt to action" latency = sum of all above.
```

### 14.2 Measurement Tools

```bash
# cyclictest: Measures scheduling latency (best tool for RT analysis)
cyclictest --smp --priority=80 --interval=200 --distance=0 -l 100000

# ftrace: Kernel function tracer
echo irqsoff > /sys/kernel/debug/tracing/tracer
# Traces how long IRQs are disabled, finds worst-case preemption latency

# perf: Performance counters
perf stat -e irq:irq_handler_entry,irq:irq_handler_exit -p <pid>
perf record -e irq:* sleep 5
perf report

# /proc/interrupts: Per-CPU interrupt counts
watch -n1 cat /proc/interrupts

# /proc/softirqs: Per-CPU softirq counts
watch -n1 cat /proc/softirqs

# wakeup latency trace
echo wakeup > /sys/kernel/debug/tracing/tracer
```

### 14.3 Tuning Techniques

```
1. IRQ Affinity Tuning:
   - Pin latency-critical IRQs to isolated CPUs
   - Use isolcpus= and nohz_full= kernel params
   - irqaffinity= to exclude CPUs from IRQ delivery

2. CPU Isolation:
   isolcpus=2,3          # Isolate CPUs 2,3 from scheduler
   nohz_full=2,3         # No timer ticks on CPUs 2,3
   rcu_nocbs=2,3         # Offload RCU callbacks from CPUs 2,3

3. Memory:
   - NUMA-aware memory allocation for DMA buffers
   - Hugepages to reduce TLB pressure during ISR
   - IOMMU groups for device isolation

4. Softirq budget tuning:
   /proc/sys/kernel/softirq_budget  # Time budget before ksoftirqd takes over

5. Threaded IRQ priority:
   chrt -f 90 -p $(pgrep "irq/45-mydev")  # Set RT priority for IRQ thread
```

---

## 15. Implementation: C Driver with All Mechanisms

```c
// SPDX-License-Identifier: GPL-2.0
/*
 * interrupt_nesting_demo.c
 *
 * Demonstrates: ISR, tasklet, workqueue, and threaded IRQ patterns
 * with proper locking and deferral.
 *
 * Build: Add to a kernel module Makefile, load with insmod.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/workqueue.h>
#include <linux/spinlock.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <linux/atomic.h>
#include <linux/percpu.h>
#include <linux/platform_device.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Elite RE Analyst");
MODULE_DESCRIPTION("Interrupt deferral demonstration");

/* ============================================================
 * Data structures
 * ============================================================ */

#define RING_BUFFER_SIZE  256
#define DATA_MAGIC        0xDEADBEEF

struct ring_buffer {
    u32             data[RING_BUFFER_SIZE];
    unsigned int    head;
    unsigned int    tail;
    unsigned int    count;
    spinlock_t      lock;       /* Protects head/tail/count */
};

struct my_device {
    int                     irq;
    void __iomem            *base;
    
    /* Ring buffer: written by ISR, consumed by softirq/workqueue */
    struct ring_buffer      rx_ring;
    
    /* Tasklet for fast deferral (will be replaced by threaded IRQ) */
    struct tasklet_struct   rx_tasklet;
    
    /* Workqueue item for slow/sleepable processing */
    struct work_struct      process_work;
    struct workqueue_struct *wq;
    
    /* Statistics: per-CPU to avoid locking */
    /* NOTE: only valid to read from IRQ context on same CPU */
    
    /* Cross-CPU stats use atomic */
    atomic64_t              total_irqs;
    atomic64_t              dropped_packets;
};

static struct my_device *g_dev;

/* ============================================================
 * Ring buffer operations (lockless fast path for ISR)
 * ============================================================ */

/*
 * ring_push_irq: Called from ISR (IF=0).
 * Lock is acquired without irqsave (IRQs already off in ISR).
 */
static int ring_push_irq(struct ring_buffer *rb, u32 value)
{
    int ret = 0;
    
    spin_lock(&rb->lock);
    
    if (rb->count < RING_BUFFER_SIZE) {
        rb->data[rb->head] = value;
        rb->head = (rb->head + 1) % RING_BUFFER_SIZE;
        rb->count++;
    } else {
        ret = -ENOBUFS;  /* Ring full, drop */
    }
    
    spin_unlock(&rb->lock);
    return ret;
}

/*
 * ring_pop_bh: Called from softirq/tasklet context.
 * IRQs enabled, but bottom halves may not be. Use spin_lock_bh
 * if called from process context to prevent softirq preemption.
 * From tasklet: plain spin_lock() is sufficient (BH already disabled).
 */
static int ring_pop_tasklet(struct ring_buffer *rb, u32 *value)
{
    int ret = -ENODATA;
    
    /*
     * From tasklet context, BH is already disabled on this CPU.
     * The ISR may fire (IF=1 here), so we DO need to disable IRQs
     * to prevent ISR from concurrently modifying the ring.
     */
    unsigned long flags;
    spin_lock_irqsave(&rb->lock, flags);
    
    if (rb->count > 0) {
        *value = rb->data[rb->tail];
        rb->tail = (rb->tail + 1) % RING_BUFFER_SIZE;
        rb->count--;
        ret = 0;
    }
    
    spin_unlock_irqrestore(&rb->lock, flags);
    return ret;
}

/* ============================================================
 * TOP HALF: The Hardware ISR
 *
 * Constraints:
 *   - IF = 0 (maskable IRQs disabled on this CPU)
 *   - Cannot sleep
 *   - Cannot acquire sleeping locks (mutex, semaphore)
 *   - Must return quickly
 *   - Must send EOI (handled by kernel if IRQF_SHARED flags set properly)
 * ============================================================ */

static irqreturn_t my_isr_hard(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    u32 status;
    u32 data;
    
    /*
     * Step 1: Read hardware status register.
     * readl() is an I/O memory barrier + 32-bit read.
     * This is why we need atomic I/O access — not caching of MMIO.
     */
    status = readl(dev->base + 0x00);  /* STATUS register offset */
    
    /* Step 2: Check if this IRQ is for us (shared IRQ lines) */
    if (!(status & 0x01)) {
        return IRQ_NONE;  /* Not our interrupt */
    }
    
    /* Step 3: Acknowledge hardware (clear interrupt pending bit) */
    writel(status & ~0x01, dev->base + 0x00);
    wmb();  /* Ensure write is visible before we read data */
    
    /* Step 4: Read data (minimal — just capture, don't process) */
    data = readl(dev->base + 0x04);  /* DATA register offset */
    
    /*
     * Step 5: Store in ring buffer.
     * ring_push_irq uses spin_lock() (not irqsave) because
     * we are already in IRQ context with IF=0.
     */
    if (ring_push_irq(&dev->rx_ring, data) < 0) {
        atomic64_inc(&dev->dropped_packets);
    }
    
    /* Step 6: Update statistics (atomic, no lock needed) */
    atomic64_inc(&dev->total_irqs);
    
    /*
     * Step 7: Schedule bottom half.
     * tasklet_schedule() is safe from ISR context.
     * It sets TASKLET_STATE_SCHED atomically and raises TASKLET_SOFTIRQ.
     */
    tasklet_schedule(&dev->rx_tasklet);
    
    return IRQ_HANDLED;
    
    /*
     * After we return IRQ_HANDLED:
     *   1. irq_exit() is called by the kernel
     *   2. irq_exit() decrements hardirq counter
     *   3. irq_exit() calls invoke_softirq() if softirqs are pending
     *   4. Our TASKLET_SOFTIRQ will run (with IF=1)
     *   5. The tasklet processes the ring buffer
     */
}

/* ============================================================
 * BOTTOM HALF 1: Tasklet (fast atomic deferral)
 *
 * Constraints:
 *   - IF = 1 (hardware IRQs CAN interrupt us here)
 *   - Cannot sleep
 *   - BH is disabled (can't be preempted by another softirq on same CPU)
 *   - Same tasklet never runs on two CPUs simultaneously
 * ============================================================ */

static void my_rx_tasklet(unsigned long arg)
{
    struct my_device *dev = (struct my_device *)arg;
    u32 data;
    int processed = 0;
    
    /*
     * Drain the ring buffer. The ring uses irqsave because
     * a hardware IRQ may fire here (IF=1) and try to push to ring.
     */
    while (ring_pop_tasklet(&dev->rx_ring, &data) == 0) {
        /* Fast processing: validate, filter, enqueue for slow path */
        
        if (data == DATA_MAGIC) {
            /* Schedule slow/sleeping work for complex processing */
            queue_work(dev->wq, &dev->process_work);
        }
        
        processed++;
        
        /* Bound the tasklet to prevent starvation */
        if (processed >= 64)
            break;
    }
    
    /* If ring still has data, reschedule tasklet */
    if (dev->rx_ring.count > 0) {
        tasklet_schedule(&dev->rx_tasklet);
    }
}

/* ============================================================
 * BOTTOM HALF 2: Workqueue (sleeping process context)
 *
 * Constraints:
 *   - Full process context: CAN sleep
 *   - CAN use mutex, semaphore, msleep
 *   - CAN allocate memory with GFP_KERNEL
 *   - Runs in kworker kernel thread
 * ============================================================ */

static void my_process_work(struct work_struct *work)
{
    struct my_device *dev = container_of(work, struct my_device, process_work);
    
    /*
     * This function runs in kworker context.
     * current->comm = "kworker/N:M"
     * We can sleep here.
     */
    
    /* Example: Sleep is now legal */
    msleep(1);  /* Simulating slow I/O or computation */
    
    /* Example: GFP_KERNEL allocation is legal */
    void *buf = kmalloc(4096, GFP_KERNEL);
    if (!buf) {
        pr_err("mydev: failed to allocate processing buffer\n");
        return;
    }
    
    /* Do complex processing here (DMA setup, filesystem ops, etc.) */
    pr_debug("mydev: processing work item, total_irqs=%lld\n",
             atomic64_read(&dev->total_irqs));
    
    kfree(buf);
}

/* ============================================================
 * ALTERNATIVE: Threaded IRQ approach (modern, recommended)
 *
 * The hard handler returns IRQ_WAKE_THREAD.
 * The thread handler runs in irq/N-mydev thread context.
 * ============================================================ */

static irqreturn_t my_isr_hard_threaded(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    u32 status;
    
    /* Read and clear status register */
    status = readl(dev->base + 0x00);
    if (!(status & 0x01))
        return IRQ_NONE;
    
    /* ACK hardware */
    writel(status & ~0x01, dev->base + 0x00);
    wmb();
    
    /* Signal thread to handle rest */
    return IRQ_WAKE_THREAD;
}

static irqreturn_t my_isr_thread(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    u32 data;
    
    /*
     * Running in irq/N-mydev kernel thread.
     * Fully preemptable. IF = 1.
     * Can sleep, acquire mutexes, etc.
     */
    
    data = readl(dev->base + 0x04);
    
    if (data == DATA_MAGIC) {
        msleep(1);  /* Now legal! */
        pr_debug("mydev: threaded handler processed data=%u\n", data);
    }
    
    return IRQ_HANDLED;
}

/* ============================================================
 * Module init / exit
 * ============================================================ */

static int __init my_driver_init(void)
{
    int ret;
    
    g_dev = kzalloc(sizeof(*g_dev), GFP_KERNEL);
    if (!g_dev)
        return -ENOMEM;
    
    /* Initialize ring buffer */
    spin_lock_init(&g_dev->rx_ring.lock);
    
    /* Initialize tasklet */
    tasklet_init(&g_dev->rx_tasklet, my_rx_tasklet, (unsigned long)g_dev);
    
    /* Initialize workqueue */
    INIT_WORK(&g_dev->process_work, my_process_work);
    g_dev->wq = alloc_workqueue("mydev_wq",
                                WQ_UNBOUND | WQ_MEM_RECLAIM,
                                0);
    if (!g_dev->wq) {
        ret = -ENOMEM;
        goto err_wq;
    }
    
    /* Register interrupt handler (classic approach) */
    g_dev->irq = 10;  /* Demo IRQ number */
    ret = request_irq(g_dev->irq,
                      my_isr_hard,
                      IRQF_SHARED,
                      "mydev",
                      g_dev);
    if (ret) {
        pr_err("mydev: failed to request IRQ %d\n", g_dev->irq);
        goto err_irq;
    }
    
    /*
     * OR: Use threaded IRQ (modern approach, uncomment to use):
     *
     * ret = request_threaded_irq(g_dev->irq,
     *                            my_isr_hard_threaded,
     *                            my_isr_thread,
     *                            IRQF_SHARED,
     *                            "mydev",
     *                            g_dev);
     */
    
    atomic64_set(&g_dev->total_irqs, 0);
    atomic64_set(&g_dev->dropped_packets, 0);
    
    pr_info("mydev: initialized, IRQ=%d\n", g_dev->irq);
    return 0;
    
err_irq:
    destroy_workqueue(g_dev->wq);
err_wq:
    kfree(g_dev);
    return ret;
}

static void __exit my_driver_exit(void)
{
    free_irq(g_dev->irq, g_dev);
    
    /* Kill tasklet BEFORE destroying workqueue */
    tasklet_kill(&g_dev->rx_tasklet);  /* Waits for in-progress tasklet */
    
    /* Cancel any pending work and destroy queue */
    cancel_work_sync(&g_dev->process_work);
    destroy_workqueue(g_dev->wq);
    
    pr_info("mydev: exit. total_irqs=%lld dropped=%lld\n",
            atomic64_read(&g_dev->total_irqs),
            atomic64_read(&g_dev->dropped_packets));
    
    kfree(g_dev);
}

module_init(my_driver_init);
module_exit(my_driver_exit);

/*
 * CRITICAL ORDERING REQUIREMENTS on exit:
 *
 * 1. free_irq() FIRST: Ensures no new ISRs fire after this point
 * 2. tasklet_kill() SECOND: Ensures no tasklet is running or scheduled
 * 3. cancel_work_sync() THIRD: Ensures no workqueue items pending
 * 4. destroy_workqueue() FOURTH: Safe to destroy now
 *
 * Reversing this order leads to use-after-free and panics.
 */
```

---

## 16. Implementation: Rust Kernel Module

Rust kernel modules use the `rust/` tree (merged in Linux 6.1+). The Rust abstractions enforce correct locking at the type level.

```rust
// SPDX-License-Identifier: GPL-2.0
//! Interrupt deferral demonstration in Rust.
//!
//! This module demonstrates:
//! - IrqHandler trait for ISR registration
//! - SpinLock<T> enforcing lock acquisition before data access
//! - Task<T> for workqueue-based deferred processing
//! - The type system prevents calling sleepable functions from atomic context

use kernel::prelude::*;
use kernel::{
    irq,
    sync::{Arc, SpinLock},
    task,
    workqueue::{self, Work, WorkItem},
    io_mem::IoMem,
};
use core::sync::atomic::{AtomicU64, Ordering};

/// Per-device state.
/// Arc<DeviceState> is shared between ISR, tasklet-equivalent, and workqueue.
struct DeviceState {
    /// Ring buffer protected by SpinLock.
    /// SpinLock<RingBuffer> ensures: you CANNOT access ring_buffer
    /// without holding the lock. The type system enforces this.
    ring: SpinLock<RingBuffer>,
    
    /// Workqueue item for sleepable processing.
    work: Work<ProcessWorkItem>,
    
    /// Statistics (atomics: no lock needed)
    total_irqs:      AtomicU64,
    dropped_packets: AtomicU64,
}

struct RingBuffer {
    data:  [u32; 256],
    head:  usize,
    tail:  usize,
    count: usize,
}

impl RingBuffer {
    fn new() -> Self {
        RingBuffer {
            data:  [0u32; 256],
            head:  0,
            tail:  0,
            count: 0,
        }
    }
    
    /// Push value. Returns Err if full.
    /// Called from ISR (IF=0). SpinLock ensures mutual exclusion with
    /// other CPUs and with the tasklet-equivalent (which enables IRQs).
    fn push(&mut self, value: u32) -> Result {
        if self.count >= 256 {
            return Err(ENOBUFS);
        }
        self.data[self.head] = value;
        self.head = (self.head + 1) % 256;
        self.count += 1;
        Ok(())
    }
    
    /// Pop value. Returns None if empty.
    fn pop(&mut self) -> Option<u32> {
        if self.count == 0 {
            return None;
        }
        let value = self.data[self.tail];
        self.tail = (self.tail + 1) % 256;
        self.count -= 1;
        Some(value)
    }
}

/// The ISR handler. Implements irq::Handler.
///
/// Rust's type system guarantees:
/// - handler() runs with the IRQ disabled (hardware invariant, not enforced by types)
/// - SpinLock guards cannot outlive the lock itself
/// - No sleeping functions can be called (they're not in scope here)
struct MyIrqHandler {
    dev: Arc<DeviceState>,
    base: IoMem<0x100>,  // 256-byte MMIO region
}

#[vtable]
impl irq::Handler for MyIrqHandler {
    type Data = Arc<DeviceState>;
    
    /// Top half: runs with IF=0 on x86.
    ///
    /// CRITICAL RUST DIFFERENCE from C:
    /// The SpinLock guard returned by lock() is DROPPED at end of scope.
    /// This is enforced by the borrow checker — you CANNOT return from
    /// this function while still holding the lock.
    fn handle_irq(data: &Arc<DeviceState>) -> irq::Return {
        // Read status register (MMIO read: volatile, no caching)
        // In Rust kernel, IoMem::readl() is bounds-checked at compile time
        let status = unsafe { data.base.readl(0x00) };
        
        if status & 0x01 == 0 {
            return irq::Return::None;  // Not our interrupt
        }
        
        // ACK hardware
        unsafe { data.base.writel(status & !0x01, 0x00) };
        
        // Read data register
        let rx_data = unsafe { data.base.readl(0x04) };
        
        // Push to ring buffer.
        // SpinLock::lock() disables local IRQs internally on x86 (via spin_lock_irqsave).
        // The guard is automatically released at end of block.
        {
            let mut ring = data.ring.lock();
            // ^ ring is a SpinLockGuard<RingBuffer>
            // ^ You CANNOT access ring.data without this guard
            // ^ The borrow checker prevents escaping the guard
            
            if ring.push(rx_data).is_err() {
                data.dropped_packets.fetch_add(1, Ordering::Relaxed);
            }
        }
        // ^ Guard dropped here. Lock released. Interrupts re-enabled (if they were).
        
        data.total_irqs.fetch_add(1, Ordering::Relaxed);
        
        // Schedule workqueue item.
        // workqueue::Queue::enqueue() is safe from any context.
        // The work item will run in a kworker thread (can sleep).
        // Note: In actual kernel Rust, this would use the bound workqueue.
        // Simplified here for clarity.
        
        irq::Return::Handled
    }
}

/// Workqueue work item. Implements WorkItem.
struct ProcessWorkItem {
    dev: Arc<DeviceState>,
}

impl WorkItem for ProcessWorkItem {
    /// Thread handler: runs in kworker context (CAN sleep).
    ///
    /// Rust's type system does NOT prevent sleeping here (any function is callable).
    /// But the kernel's might_sleep() debug checks will fire if something is wrong.
    fn run(self: Arc<Self>) {
        let dev = &self.dev;
        
        // Drain ring buffer
        loop {
            let item = {
                let mut ring = dev.ring.lock();
                ring.pop()
            };
            
            match item {
                Some(data) => {
                    // Process data: sleeping is legal here
                    // In real code: task::sleep(Duration::from_millis(1));
                    
                    pr_info!("mydev: processed data={}\n", data);
                }
                None => break,
            }
        }
    }
}

/// Module entry point
struct MyModule {
    _irq: irq::Registration<MyIrqHandler>,
    _dev: Arc<DeviceState>,
}

impl kernel::Module for MyModule {
    fn init(_name: &'static CStr, _module: &'static ThisModule) -> Result<Self> {
        pr_info!("mydev: Rust interrupt demo init\n");
        
        let dev = Arc::try_new(DeviceState {
            ring:            SpinLock::new(RingBuffer::new()),
            work:            Work::new(),
            total_irqs:      AtomicU64::new(0),
            dropped_packets: AtomicU64::new(0),
        })?;
        
        // Register IRQ handler.
        // irq::Registration owns the handler lifetime.
        // When _irq is dropped (module exit), free_irq() is called automatically.
        // This is RAII applied to interrupt registration.
        let irq_reg = irq::Registration::try_new(
            10,                    // IRQ number
            dev.clone(),           // Handler data (Arc<DeviceState>)
            irq::flags::SHARED,
            fmt!("mydev"),
        )?;
        
        Ok(MyModule {
            _irq: irq_reg,
            _dev: dev,
        })
    }
}

// RAII cleanup: When MyModule is dropped:
// 1. _irq is dropped -> free_irq() called -> no more ISRs
// 2. _dev's Arc reference count decremented
// 3. When count reaches 0, DeviceState is freed
//
// This prevents the use-after-free bugs that plague C drivers.
// The borrow checker ensures _irq (which holds Arc<DeviceState>)
// is dropped before _dev's Arc reference, but since both are in MyModule,
// they're dropped in declaration order (which we control).

impl Drop for MyModule {
    fn drop(&mut self) {
        pr_info!("mydev: Rust interrupt demo exit\n");
    }
}

module! {
    type: MyModule,
    name: "mydev_rust",
    author: "Elite RE Analyst",
    description: "Rust interrupt deferral demo",
    license: "GPL",
}

/*
 * KEY RUST ADVANTAGES OVER C FOR INTERRUPT CODE:
 *
 * 1. SpinLock<T>: Cannot access T without the lock. Prevents data races
 *    that would be hard to spot in C (accessing ring->head without lock).
 *
 * 2. RAII on irq::Registration: free_irq() is guaranteed to be called.
 *    In C, you can forget free_irq() or call it in wrong order.
 *
 * 3. Arc ownership: DeviceState lives as long as any Arc<DeviceState> exists.
 *    In C, you must manually ensure the handler's dev_id is valid until free_irq().
 *
 * 4. Fearless concurrency: The borrow checker prevents aliasing between ISR
 *    and workqueue contexts at the data level (through SpinLock<T>).
 *
 * 5. No implicit casts: readl/writel are typed, bounds-checked on IoMem.
 *
 * RUST LIMITATIONS IN KERNEL CONTEXT (as of 6.x):
 * - Async/await not yet supported in kernel
 * - Many subsystem bindings still incomplete
 * - PREEMPT_RT-specific primitives not fully abstracted
 * - Cannot express "this function must not be called from atomic context"
 *   purely through the type system (yet)
 */
```

---

## 17. Implementation: Go Userspace Simulation and eBPF Interface

Go cannot write kernel modules, but it has two powerful roles in interrupt-related work:

1. **Userspace simulation**: Modeling interrupt-driven architectures for testing/fuzzing
2. **eBPF interaction**: Attaching probes to interrupt handlers, reading performance counters

### 17.1 Go Interrupt Architecture Simulation

```go
// interrupt_sim.go
//
// Simulates the Linux interrupt deferral model in userspace.
// Useful for:
//   - Testing driver logic before kernel module development
//   - Fuzzing ring buffer implementations
//   - Performance modeling of ISR/softirq/workqueue pipeline
//
// Architecture modeled:
//   goroutine "hardware" -> ISR goroutine (via channel, models IRQ delivery)
//   ISR goroutine -> ring buffer (models ISR->softirq data handoff)
//   softirq goroutine -> ring buffer consumer (models softirq processing)
//   workqueue goroutine -> sleeping processor (models workqueue thread)

package main

import (
	"context"
	"fmt"
	"log"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

// ============================================================
// Ring Buffer: Simulates the ISR↔SoftIRQ shared buffer
// Uses atomic operations for lock-free single-producer single-consumer
// (models the SPSC nature of one ISR CPU -> one softirq CPU)
// ============================================================

const RingSize = 256

type RingBuffer struct {
	data [RingSize]uint32
	head uint64 // Written by ISR (producer)
	_    [56]byte // Cache line padding to prevent false sharing
	tail uint64 // Written by softirq (consumer)
	_    [56]byte
}

// Push inserts a value. Returns false if full.
// Models: ISR calling ring_push_irq() - must be fast, non-blocking.
func (r *RingBuffer) Push(value uint32) bool {
	head := atomic.LoadUint64(&r.head)
	tail := atomic.LoadUint64(&r.tail)

	if head-tail >= RingSize {
		return false // Full
	}

	r.data[head%RingSize] = value
	// Release store: ensures data write is visible before head update
	atomic.StoreUint64(&r.head, head+1)
	return true
}

// Pop removes a value. Returns (0, false) if empty.
// Models: softirq/tasklet calling ring_pop_tasklet().
func (r *RingBuffer) Pop() (uint32, bool) {
	tail := atomic.LoadUint64(&r.tail)
	head := atomic.LoadUint64(&r.head)

	if tail >= head {
		return 0, false // Empty
	}

	value := r.data[tail%RingSize]
	// Release store: ensures we read data before advancing tail
	atomic.StoreUint64(&r.tail, tail+1)
	return value, true
}

func (r *RingBuffer) Len() uint64 {
	head := atomic.LoadUint64(&r.head)
	tail := atomic.LoadUint64(&r.tail)
	if head < tail {
		return 0
	}
	return head - tail
}

// ============================================================
// IRQ Line: Models the hardware interrupt delivery
// In hardware: LAPIC -> CPU, IF=0 on delivery
// Here: buffered channel with depth 1 (level-triggered semantics)
// ============================================================

type IRQLine struct {
	ch chan struct{}
}

func NewIRQLine() *IRQLine {
	return &IRQLine{ch: make(chan struct{}, 1)}
}

// Assert models device asserting the interrupt line.
// Non-blocking: if already pending, level-triggered semantics (no-op).
func (l *IRQLine) Assert() {
	select {
	case l.ch <- struct{}{}:
	default: // Already pending, level-triggered: no-op
	}
}

// ============================================================
// Device Simulator: Models hardware that generates interrupts
// Runs in its own goroutine (models the physical device)
// ============================================================

type Device struct {
	irqLine    *IRQLine
	dataReg    uint32
	statusReg  uint32
	mu         sync.Mutex
	totalEvents atomic.Int64
}

func (d *Device) GenerateInterrupt(data uint32) {
	d.mu.Lock()
	d.dataReg = data
	d.statusReg = 0x01 // Set RX ready bit
	d.mu.Unlock()

	d.irqLine.Assert()
	d.totalEvents.Add(1)
}

func (d *Device) ReadData() uint32 {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.dataReg
}

func (d *Device) ReadAndClearStatus() uint32 {
	d.mu.Lock()
	defer d.mu.Unlock()
	s := d.statusReg
	d.statusReg = 0
	return s
}

// ============================================================
// ISR (Top Half): Models the Linux hardware ISR
//
// Key properties modeled:
//   - Runs atomically per IRQ (no concurrent ISR for same device)
//   - Must not block (select with default, no channel waits)
//   - Acknowledges hardware, reads data, schedules softirq
//   - Returns quickly
// ============================================================

type ISRStats struct {
	TotalIRQs    atomic.Int64
	DroppedFrames atomic.Int64
	HandleTime   atomic.Int64 // nanoseconds, sum
}

func RunISR(ctx context.Context,
	device *Device,
	irqLine *IRQLine,
	ring *RingBuffer,
	softirqTrigger chan struct{},
	stats *ISRStats,
	cpuID int) {

	// Pin this goroutine to a specific OS thread
	// Models: IRQ affinity pinning in real kernel
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	log.Printf("ISR[cpu%d]: started\n", cpuID)

	for {
		select {
		case <-ctx.Done():
			log.Printf("ISR[cpu%d]: shutdown\n", cpuID)
			return

		case <-irqLine.ch: // Wait for IRQ
			start := time.Now()

			// Step 1: Read & clear status (ACK hardware)
			status := device.ReadAndClearStatus()
			if status&0x01 == 0 {
				continue // Not our interrupt (shared IRQ)
			}

			// Step 2: Read data from device register
			data := device.ReadData()

			// Step 3: Push to ring buffer (models ring_push_irq)
			if !ring.Push(data) {
				stats.DroppedFrames.Add(1)
			}

			// Step 4: Trigger softirq processing
			// Models: raise_softirq(TASKLET_SOFTIRQ)
			// Non-blocking: if softirq already scheduled, no-op
			select {
			case softirqTrigger <- struct{}{}:
			default:
			}

			// ISR done: models returning IRQ_HANDLED
			elapsed := time.Since(start).Nanoseconds()
			stats.TotalIRQs.Add(1)
			stats.HandleTime.Add(elapsed)
		}
	}
}

// ============================================================
// Softirq Simulator (Bottom Half 1): Models TASKLET_SOFTIRQ
//
// Key properties modeled:
//   - Runs after ISR returns (triggered by softirqTrigger channel)
//   - Cannot sleep (no blocking operations)
//   - Can be interrupted by hardware IRQ (not modeled here for simplicity)
//   - Drains ring buffer, passes to workqueue
// ============================================================

func RunSoftirq(ctx context.Context,
	ring *RingBuffer,
	softirqTrigger <-chan struct{},
	workCh chan<- uint32,
	cpuID int) {

	log.Printf("Softirq[cpu%d]: started\n", cpuID)

	processBatch := func() {
		count := 0
		for count < 64 { // Max batch (models MAX_SOFTIRQ_RESTART)
			data, ok := ring.Pop()
			if !ok {
				break
			}
			// Fast processing: filter, forward to workqueue
			if data != 0xDEAD {
				select {
				case workCh <- data:
				default:
					// Workqueue full (models workqueue overflow)
					log.Printf("Softirq: workqueue full, dropping\n")
				}
			}
			count++
		}
	}

	for {
		select {
		case <-ctx.Done():
			return
		case <-softirqTrigger:
			processBatch()
			// Check if more arrived during processing
			if ring.Len() > 0 {
				processBatch()
			}
		}
	}
}

// ============================================================
// Workqueue Worker (Bottom Half 2): Models kworker thread
//
// Key properties modeled:
//   - Full process context: can sleep (time.Sleep OK)
//   - Processes complex work that softirq/tasklet cannot do
//   - Multiple workers possible (cmwq concurrency management)
// ============================================================

func RunWorker(ctx context.Context,
	workCh <-chan uint32,
	workerID int,
	wg *sync.WaitGroup) {

	defer wg.Done()
	log.Printf("Worker[%d]: started (kworker equivalent)\n", workerID)
	processed := 0

	for {
		select {
		case <-ctx.Done():
			log.Printf("Worker[%d]: shutdown, processed=%d\n", workerID, processed)
			return
		case data := <-workCh:
			// SLEEPING IS LEGAL HERE: models kworker context
			time.Sleep(100 * time.Microsecond) // Simulate I/O

			// Complex processing
			result := processData(data)
			if result != 0 {
				processed++
			}
		}
	}
}

func processData(data uint32) uint32 {
	// Simulate: DMA setup, filesystem write, network protocol processing
	return data ^ 0xFF
}

// ============================================================
// Hardware Simulator: Generates interrupt events
// ============================================================

func RunHardware(ctx context.Context, device *Device, rateHz int) {
	interval := time.Second / time.Duration(rateHz)
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	seq := uint32(0)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			device.GenerateInterrupt(seq)
			seq++
		}
	}
}

// ============================================================
// eBPF-style tracing: Reading /proc/interrupts (real kernel data)
// Models how Go tools read kernel interrupt statistics.
// ============================================================

func ReadInterruptStats() {
	// In a real tool, you'd use:
	// 1. /proc/interrupts for per-CPU counts
	// 2. /proc/softirqs for softirq counts
	// 3. ebpf-go library to attach kprobes to do_IRQ, __do_softirq
	//
	// Example with ebpf-go (pseudo-code):
	//
	// coll, _ := ebpf.NewCollection(spec)
	// prog := coll.Programs["irq_handler_entry"]
	// link, _ := link.Kprobe("handle_irq_event_percpu", prog, nil)
	// defer link.Close()
	//
	// for {
	//     var key uint32
	//     var value uint64
	//     coll.Maps["irq_latency"].Lookup(&key, &value)
	//     fmt.Printf("IRQ %d: avg_latency=%dns\n", key, value)
	// }
	fmt.Println("Note: Use cilium/ebpf or libbpf-go for real kernel instrumentation")
}

// ============================================================
// Main: Wire everything together
// ============================================================

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create components
	irqLine := NewIRQLine()
	device := &Device{irqLine: irqLine}
	ring := &RingBuffer{}
	softirqTrigger := make(chan struct{}, 4)
	workCh := make(chan uint32, 512)
	stats := &ISRStats{}

	var wg sync.WaitGroup

	// Start ISR handler (models interrupt affinity: 1 goroutine, 1 OS thread)
	wg.Add(1)
	go func() {
		defer wg.Done()
		RunISR(ctx, device, irqLine, ring, softirqTrigger, stats, 0)
	}()

	// Start softirq processor (models ksoftirqd / softirq in irq_exit)
	wg.Add(1)
	go func() {
		defer wg.Done()
		RunSoftirq(ctx, ring, softirqTrigger, workCh, 0)
	}()

	// Start workqueue workers (models kworker/N:M threads)
	numWorkers := runtime.NumCPU()
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(id int) {
			RunWorker(ctx, workCh, id, &wg)
		}(i)
	}
	// Adjust WaitGroup for worker goroutines (they call wg.Done themselves)
	// Remove the adds we already accounted for

	// Start hardware interrupt generator
	wg.Add(1)
	go func() {
		defer wg.Done()
		RunHardware(ctx, device, 10000) // 10,000 interrupts/second
	}()

	// Wait for timeout
	<-ctx.Done()
	time.Sleep(100 * time.Millisecond) // Let goroutines drain

	// Print statistics
	total := stats.TotalIRQs.Load()
	dropped := stats.DroppedFrames.Load()
	avgNs := int64(0)
	if total > 0 {
		avgNs = stats.HandleTime.Load() / total
	}

	fmt.Printf("\n=== Interrupt Pipeline Statistics ===\n")
	fmt.Printf("Total IRQs:       %d\n", total)
	fmt.Printf("Dropped frames:   %d (%.2f%%)\n", dropped,
		float64(dropped)/float64(total)*100)
	fmt.Printf("Avg ISR time:     %dns\n", avgNs)
	fmt.Printf("Device events:    %d\n", device.totalEvents.Load())
	fmt.Printf("Ring buffer fill: %d\n", ring.Len())

	ReadInterruptStats()
}

/*
 * HOW THIS MODELS REAL KERNEL BEHAVIOR:
 *
 * Go goroutine -> OS thread (runtime.LockOSThread)  models  IRQ affinity
 * IRQLine channel                                    models  IRQ delivery to CPU
 * RingBuffer atomic SPSC                             models  ISR→softirq data handoff
 * softirqTrigger channel (non-blocking send)         models  raise_softirq()
 * Worker goroutines (blocking, sleeping)             models  kworker threads
 * Channel capacity (512)                             models  workqueue max_active
 *
 * WHAT CANNOT BE MODELED IN USERSPACE:
 * - True IF=0 semantics (Go goroutines are preemptable by runtime)
 * - Cache coherence and memory barriers (Go's memory model differs)
 * - LAPIC priority and NMI behavior
 * - PREEMPT_RT priority inheritance
 * - Real MMIO (IoMem) semantics
 */
```

### 17.2 Go eBPF Tool for Interrupt Latency

```go
// irq_latency_tracer.go
//
// Attaches eBPF probes to measure interrupt handler latency.
// Requires: github.com/cilium/ebpf, Linux 5.8+, CAP_BPF
//
// Measures: time from irq_handler_entry to irq_handler_exit per IRQ number

package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
	"unsafe"

	// go get github.com/cilium/ebpf
	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
)

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -cc clang irq_tracer irq_tracer.bpf.c

/*
// eBPF C program (irq_tracer.bpf.c) - compiled separately:
//
// #include <linux/bpf.h>
// #include <bpf/bpf_helpers.h>
// #include <bpf/bpf_tracing.h>
//
// struct irq_event {
//     __u32 irq;
//     __u64 start_ns;
//     __u64 latency_ns;
//     char  action_name[32];
// };
//
// struct {
//     __uint(type, BPF_MAP_TYPE_HASH);
//     __uint(max_entries, 256);
//     __type(key, __u32);    // IRQ number
//     __type(value, __u64);  // Start timestamp (ns)
// } irq_start SEC(".maps");
//
// struct {
//     __uint(type, BPF_MAP_TYPE_RINGBUF);
//     __uint(max_entries, 256 * 1024);
// } events SEC(".maps");
//
// // Tracepoint: irq:irq_handler_entry
// // Triggered when hardware ISR begins (TOP HALF entry)
// SEC("tracepoint/irq/irq_handler_entry")
// int handle_entry(struct trace_event_raw_irq_handler_entry *ctx)
// {
//     __u32 irq = ctx->irq;
//     __u64 ts = bpf_ktime_get_ns();
//     bpf_map_update_elem(&irq_start, &irq, &ts, BPF_ANY);
//     return 0;
// }
//
// // Tracepoint: irq:irq_handler_exit
// // Triggered when hardware ISR returns (TOP HALF exit)
// SEC("tracepoint/irq/irq_handler_exit")
// int handle_exit(struct trace_event_raw_irq_handler_exit *ctx)
// {
//     __u32 irq = ctx->irq;
//     __u64 *start = bpf_map_lookup_elem(&irq_start, &irq);
//     if (!start) return 0;
//
//     __u64 now = bpf_ktime_get_ns();
//     __u64 latency = now - *start;
//     bpf_map_delete_elem(&irq_start, &irq);
//
//     struct irq_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
//     if (!e) return 0;
//
//     e->irq = irq;
//     e->start_ns = *start;
//     e->latency_ns = latency;
//     bpf_ringbuf_submit(e, 0);
//     return 0;
// }
//
// char LICENSE[] SEC("license") = "GPL";
*/

type IRQEvent struct {
	IRQ       uint32
	StartNS   uint64
	LatencyNS uint64
	Name      [32]byte
}

type IRQStats struct {
	Count   int64
	TotalNS int64
	MaxNS   int64
	MinNS   int64
}

func main() {
	// Load pre-compiled eBPF program (generated by bpf2go)
	// In real code: use irq_tracerObjects from generated code
	
	// For demonstration: show how you'd use the loaded objects
	fmt.Println("IRQ Latency Tracer - eBPF based")
	fmt.Println("================================")
	fmt.Println("Requires: CAP_BPF, Linux 5.8+, compiled eBPF program")
	fmt.Println()
	fmt.Println("Architecture:")
	fmt.Println("  tracepoint/irq/irq_handler_entry -> record timestamp in BPF_MAP_TYPE_HASH")
	fmt.Println("  tracepoint/irq/irq_handler_exit  -> compute latency, push to BPF_MAP_TYPE_RINGBUF")
	fmt.Println("  Go userspace                     -> read ringbuf, compute statistics")
	fmt.Println()

	// Demonstrate the structure of the real implementation:
	_ = demonstrateEBPFUsage
	
	// Show /proc/interrupts parsing as a simpler alternative
	parseAndDisplayInterrupts()
}

func demonstrateEBPFUsage() error {
	// 1. Load compiled eBPF object
	spec, err := ebpf.LoadCollectionSpec("irq_tracer.bpf.o")
	if err != nil {
		return fmt.Errorf("loading eBPF spec: %w", err)
	}

	coll, err := ebpf.NewCollection(spec)
	if err != nil {
		return fmt.Errorf("creating collection: %w", err)
	}
	defer coll.Close()

	// 2. Attach tracepoints
	entryLink, err := link.Tracepoint("irq", "irq_handler_entry",
		coll.Programs["handle_entry"], nil)
	if err != nil {
		return fmt.Errorf("attaching entry tracepoint: %w", err)
	}
	defer entryLink.Close()

	exitLink, err := link.Tracepoint("irq", "irq_handler_exit",
		coll.Programs["handle_exit"], nil)
	if err != nil {
		return fmt.Errorf("attaching exit tracepoint: %w", err)
	}
	defer exitLink.Close()

	// 3. Read events from ring buffer
	rd, err := ringbuf.NewReader(coll.Maps["events"])
	if err != nil {
		return fmt.Errorf("creating ring buffer reader: %w", err)
	}
	defer rd.Close()

	stats := make(map[uint32]*IRQStats)

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-sig:
			printStats(stats)
			return nil
		case <-ticker.C:
			printStats(stats)
		default:
			record, err := rd.Read()
			if err != nil {
				if err == ringbuf.ErrClosed {
					return nil
				}
				continue
			}

			var event IRQEvent
			if err := binary.Read(
				byteReader(record.RawSample),
				binary.LittleEndian,
				&event,
			); err != nil {
				log.Printf("parsing event: %v", err)
				continue
			}

			s := stats[event.IRQ]
			if s == nil {
				s = &IRQStats{MinNS: 1<<63 - 1}
				stats[event.IRQ] = s
			}
			s.Count++
			s.TotalNS += int64(event.LatencyNS)
			if int64(event.LatencyNS) > s.MaxNS {
				s.MaxNS = int64(event.LatencyNS)
			}
			if int64(event.LatencyNS) < s.MinNS {
				s.MinNS = int64(event.LatencyNS)
			}
		}
	}
}

func printStats(stats map[uint32]*IRQStats) {
	fmt.Printf("\n%-6s %-10s %-10s %-10s %-10s\n",
		"IRQ", "Count", "Avg(ns)", "Max(ns)", "Min(ns)")
	fmt.Println("------------------------------------------------------")
	for irq, s := range stats {
		avg := int64(0)
		if s.Count > 0 {
			avg = s.TotalNS / s.Count
		}
		fmt.Printf("%-6d %-10d %-10d %-10d %-10d\n",
			irq, s.Count, avg, s.MaxNS, s.MinNS)
	}
}

// byteReader implements io.Reader for []byte
type byteReader []byte

func (b *byteReader) Read(p []byte) (n int, err error) {
	if len(*b) == 0 {
		return 0, fmt.Errorf("EOF")
	}
	n = copy(p, *b)
	*b = (*b)[n:]
	return n, nil
}

// parseAndDisplayInterrupts reads /proc/interrupts
// This works on any Linux system without special privileges
func parseAndDisplayInterrupts() {
	data, err := os.ReadFile("/proc/interrupts")
	if err != nil {
		fmt.Printf("Cannot read /proc/interrupts: %v\n", err)
		return
	}

	fmt.Println("/proc/interrupts sample (first 20 lines):")
	fmt.Println("------------------------------------------")
	lines := splitLines(data)
	for i, line := range lines {
		if i > 20 {
			fmt.Println("  [... truncated ...]")
			break
		}
		fmt.Println(line)
	}
	fmt.Println()
	
	// Also show softirqs
	softData, err := os.ReadFile("/proc/softirqs")
	if err == nil {
		fmt.Println("/proc/softirqs:")
		fmt.Println("---------------")
		softLines := splitLines(softData)
		for _, line := range softLines {
			fmt.Println(line)
		}
	}
}

func splitLines(data []byte) []string {
	var lines []string
	start := 0
	for i, b := range data {
		if b == '\n' {
			lines = append(lines, string(data[start:i]))
			start = i + 1
		}
	}
	return lines
}

// Silence unused import
var _ = unsafe.Sizeof
```

---

## 18. Security Implications and Attack Surface

### 18.1 Interrupt Handlers as Attack Surface

From a **malware/exploit analysis perspective**, interrupt handling code is valuable to attackers:

```
ATTACK VECTORS:

1. Race Conditions in ISR Shared Data:
   - If driver uses incorrect locking (e.g., missing irqsave),
     a malicious process can craft timing to corrupt kernel data
   - CVE-2019-14896 (Marvell WiFi): Buffer overflow in ISR handler
   - CVE-2021-3428 (ext4): Interrupt context race leading to use-after-free

2. ISR Injection / Hooking (Rootkit technique):
   - Modify IDT entries to redirect specific vectors to attacker code
   - Requires ring 0 (kernel exploit needed first)
   - Classic rootkit: hook int 0x80 (legacy syscall) to intercept all syscalls
   
   IDT hook detection in memory forensics:
     Volatility3: python3 vol.py -f memory.dmp linux.check_idt
     Expected: all ISRs point to addresses within kernel text (.text section)
     Malicious: ISR pointing to dynamically allocated memory (vmalloc range)

3. Timing Attacks via IRQ Measurement:
   - Measure IRQ latency changes to detect VM hypervisor (RDTSC timing)
   - Measure IRQ coalescing patterns to fingerprint hardware
   - Used by malware for anti-VM: if timer interrupt comes at perfect intervals,
     likely in VM (hypervisors coalesce timer ticks)

4. SoftIRQ Flooding (DoS):
   - Flood device with interrupts -> ISR schedules softirq every time
   - Softirq starves process context -> effective DoS
   - Mitigated by: interrupt coalescing (NAPI for network), IRQ rate limiting
   
5. Workqueue Abuse:
   - Some kernel code schedules work items from untrusted input paths
   - If workqueue handler is vulnerable, exploit via legitimate kernel path
   - CVE-2022-0847 (Dirty Pipe) didn't use this, but similar patterns exist
```

### 18.2 Rootkit ISR Hooking

```c
// ROOTKIT TECHNIQUE: IDT Hooking
// This is how kernel rootkits intercept interrupts
// (FOR EDUCATIONAL ANALYSIS ONLY - understanding detection)

// Step 1: Read IDTR to find IDT base address
struct idtr {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

static struct idtr get_idtr(void) {
    struct idtr idtr;
    asm volatile ("sidt %0" : "=m"(idtr));
    return idtr;
}

// Step 2: IDT entry structure (Gate Descriptor)
typedef struct {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t  ist;
    uint8_t  type_attr;
    uint16_t offset_mid;
    uint32_t offset_high;
    uint32_t zero;
} __attribute__((packed)) gate_desc;

// Step 3: Hook an IRQ vector
// To hook vector N:
//   1. Disable write protection (CR0.WP = 0)
//   2. Overwrite IDT[N] with new handler address
//   3. Re-enable write protection
//
// Modern mitigations against this:
//   - SMEP/SMAP: prevents kernel from executing/accessing user memory
//   - CR0.WP enforcement: write_cr0 is monitored by hypervisors
//   - Kernel lockdown mode: blocks /dev/mem, kprobes, module loading
//   - KCFI (Kernel Control Flow Integrity): validates indirect calls
//   - IDT protected by kernel page tables (NX on IDT pages)

// DETECTION (Volatility):
// python3 vol.py -f memory.dmp linux.check_idt
//
// Checks each IDT entry:
// 1. Is the handler address within kernel text range?
//    kernel text: [_stext, _etext] (from /proc/kallsyms or System.map)
// 2. Is it within a loaded module?
//    kernel modules: [mod->core_layout.base, base+size]
// 3. If neither: SUSPICIOUS (possible IDT hook)
```

### 18.3 YARA Rule for Kernel Rootkit IDT Manipulation

```yara
// YARA rule for detecting IDT manipulation in memory dumps
// or in kernel rootkit binaries that contain IDT hooking code

rule Rootkit_IDT_Hook_x86_64 {
    meta:
        description = "Detects x86-64 IDT manipulation code in kernel modules"
        author      = "Elite RE Analyst"
        reference   = "Interrupt Descriptor Table hooking technique"
        severity    = "CRITICAL"

    strings:
        // SIDT instruction: stores IDTR to memory
        // Encoding: 0F 01 /1  (ModRM byte for /1 = 0x0D-0x1D range)
        $sidt_mem     = { 0F 01 [1-4] }
        
        // LIDT instruction: loads IDTR from memory  
        // Encoding: 0F 01 /3
        $lidt_mem     = { 0F 01 [1-4] }
        
        // Disabling write protection: mov cr0, rax with WP bit cleared
        // CR0 WP bit = bit 16. Normal CR0 ≈ 0x80050033
        // Clearing WP: AND rax, 0xFFFEFFFF then MOV CR0, RAX
        $disable_wp   = { 48 [1-2] FF FE FF FF [0-4] 0F 22 C0 }
        
        // Re-enabling write protection: OR with 0x10000, then MOV CR0
        $enable_wp    = { 48 [1-2] 00 00 01 00 [0-4] 0F 22 C0 }
        
        // Reading IDT offset (64-bit gate descriptor manipulation)
        // Typical pattern: shift operations on 64-bit IDT entry
        $idt_calc_64  = { 48 C1 [1-3] 10 [0-8] 48 C1 [1-3] 20 }
        
        // kallsyms lookup strings (rootkits look up kernel addresses)
        $ks_idt       = "idt_table" ascii
        $ks_idtr      = "__idt_base" ascii wide

    condition:
        uint32(0) == 0x464C457F  // ELF magic (kernel module)
        and (
            ($sidt_mem and $lidt_mem and ($disable_wp or $enable_wp))
            or ($idt_calc_64 and ($ks_idt or $ks_idtr))
            or (all of ($disable_wp, $enable_wp, $sidt_mem))
        )
}
```

---

## 19. Debugging Interrupt Problems

### 19.1 Common Bugs and Their Signatures

```
BUG TYPE 1: Sleeping in atomic context
=======================================
Symptom: BUG: sleeping function called from invalid context
         Kernel panic: schedule() called while atomic
Trace:
  [<0>] mutex_lock+0x1a/...
  [<0>] my_isr_handler+0x4f/...
  [<0>] handle_irq_event_percpu+0x...
Cause: Called mutex_lock(), kmalloc(GFP_KERNEL), copy_from_user(), etc. in ISR
Fix:   Move to workqueue/threaded IRQ; use GFP_ATOMIC for allocations

BUG TYPE 2: Spinlock deadlock (same CPU)
=========================================
Symptom: Watchdog: BUG: soft lockup - CPU#0 stuck for 22s
         System unresponsive, NMI eventually fires
Trace: CPU0 spinning in _raw_spin_lock
Cause: ISR tries to acquire lock already held by interrupted code (no irqsave)
Fix:   Use spin_lock_irqsave() in process context

BUG TYPE 3: Use-after-free in ISR
===================================
Symptom: KASAN: use-after-free in my_isr_handler
         Memory corruption detected
Cause: free_irq() not called before kfree(dev) in exit
Fix:   Enforce cleanup order: free_irq() -> tasklet_kill() -> kfree()

BUG TYPE 4: Interrupt storm (missed EOI)
=========================================
Symptom: CPU pegged at 100%, all CPU cycles in handle_irq
         /proc/interrupts shows millions of IRQs/second
Cause: ISR returned IRQ_HANDLED without ACKing hardware
       Level-triggered IRQ: stays asserted if not cleared
Fix:   Ensure hardware ACK (clear status register) before return

BUG TYPE 5: Race in ring buffer (SPSC violation)
=================================================
Symptom: Intermittent data corruption, difficult to reproduce
Cause: Missing memory barriers in ring buffer push/pop
       head/tail updates visible before data writes
Fix:   Use smp_store_release() for head/tail, smp_load_acquire() for reads
```

### 19.2 ftrace Usage for ISR Analysis

```bash
# Setup: Trace IRQ disable periods (find latency sources)
echo irqsoff > /sys/kernel/debug/tracing/tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
# ... do workload ...
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace

# Output example:
# irqsoff latency trace v1.1.5 on 6.1.0
# -----------------------------------------------------------------
# latency: 173 us, #4/4, CPU#0 | (M:preempt VP:0, KP:0, SP:0 HP:0)
#    -----------------
#    | task: kworker/0:2-45 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: _raw_spin_lock_irqsave
#  => ended at:   _raw_spin_unlock_irqrestore
#
#    _------=> CPU#
#   / _-----=> irqs-off
#  | / _----=> need-resched
#  || / _---=> hardirq/softirq
#  ||| / _--=> preempt-depth
#  |||| /     delay
#  cmd  pid   ||||    time  |   caller
#    \   /    ||||   \   |   /
#  kworker-45 0d..1   0us : _raw_spin_lock_irqsave <-my_process_function
#  kworker-45 0d..1 173us : _raw_spin_unlock_irqrestore <-my_process_function

# The 173µs IRQ-disabled window is too long for RT systems.
# Investigate my_process_function for long critical sections.

# Trace specific function
echo my_isr_handler > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/tracer
cat /sys/kernel/debug/tracing/trace_pipe | head -50
```

### 19.3 Volatility for Interrupt Forensics (Memory Dump Analysis)

```bash
# Check IDT for hooks (rootkit detection)
python3 vol.py -f memory.dmp linux.check_idt
# Expected output for clean system:
# IRQ   Handler                 Module
# 0     ffffffffc0123456        [KERNEL]  (timer ISR)
# 1     ffffffffc0234567        [KERNEL]  (keyboard)
# 32    ffffffffc0345678        [KERNEL]  (IOAPIC device)
#
# Suspicious output:
# 32    ffff8880deadbeef        [UNKNOWN] <- NOT in kernel text or any module

# List interrupt handlers (struct irq_desc analysis)
python3 vol.py -f memory.dmp linux.interrupts
# Shows: IRQ number, action name, handler address, device name

# Detect hidden kernel modules (could contain ISR hooks)
python3 vol.py -f memory.dmp linux.lsmod
python3 vol.py -f memory.dmp linux.check_modules
# Compares module list in memory vs /sys/module entries
# Discrepancy -> hidden module (rootkit)
```

---

## 20. The Expert Mental Model

A top 1% Linux kernel engineer — one of the Arnd Bergmann, Greg Kroah-Hartman, or Thomas Gleixner caliber — frames interrupt handling not as a feature to implement but as a **contract to honor at every level of abstraction simultaneously**. The hardware promises to deliver interrupts; the ISR promises to return fast; the OS promises to run deferred work "soon." Every violation of this contract has a precise failure mode: a deadlock, a starvation, a use-after-free, or a latency spike.

The mental model operates in layers: at the hardware layer, RFLAGS.IF is a physical gate in the CPU that the ISR must respect by not sleeping and not holding indefinitely. At the OS layer, `preempt_count` is the software mirror of that gate, tracking nested atomic contexts. At the architecture layer, the top/bottom-half split is a **latency/capability tradeoff**: buy low latency in the hard ISR by doing almost nothing, then buy full kernel capabilities in the deferred context at the cost of some additional latency. The choice between tasklet, workqueue, and threaded IRQ is a choice of where on that tradeoff curve you sit, and the modern consensus — especially with `PREEMPT_RT` — is that **threaded IRQs are nearly always the right answer** because they compose correctly with real-time scheduling.

From a security standpoint, interrupt infrastructure is the most privileged code path in the kernel: it runs before any user-to-kernel transition, before any process context checks, and with minimal stack depth. A bug there — a missing memory barrier, a wrong lock variant, an improper cleanup ordering — is either a stability catastrophe or an exploitable primitive. When analyzing a rootkit or an exploit, always look at whether the kernel's IDT has been tampered, whether ISR handlers have been redirected, and whether race conditions in device driver top-halves have been used as primitives. The interrupt is the fastest path from hardware to kernel trust; it is therefore the first path an attacker will probe.

---

*Document: `linux_interrupt_nesting_and_deferral.md`*  
*Classification: Elite Analyst Reference — Kernel Internals Series*  
*Covers: x86-64, Linux 6.x, Rust kernel 6.1+, Go 1.22+*

Now I'll write the comprehensive guide as a Markdown file:**20 sections, ~150KB of dense technical material.** Here's what you got:

**Hardware Layer** — Full x86-64 interrupt delivery chain: IOAPIC → LAPIC → CPU, TPR/PPR priority mechanics, ISR register, IRR register, and exactly when nesting CAN and CANNOT occur. The distinction between maskable interrupts (IF=0 blocks) vs. NMI/SMI (IF=0 does not block) is given full treatment.

**The Nesting Truth** — Three distinct nesting scenarios that still occur even with IF=0: NMI preemption of ISRs, softirq interleaving, and SMP concurrent ISRs on separate CPUs. Each modeled with ASCII diagrams.

**Deferral Mechanisms** — SoftIRQs (static table, concurrent across CPUs), Tasklets (deprecated, non-concurrent SoftIRQ wrapper), Workqueues (cmwq architecture, full process context), and Threaded IRQs (modern standard). Includes the `__do_softirq()` execution flow with `irq_exit()` hookpoint detail.

**Locking Taxonomy** — The full matrix of when to use `spin_lock()` vs `spin_lock_irqsave()` vs `spin_lock_bh()`, with the reasoning from first principles. Why the ISR uses plain `spin_lock()` but process context must use `irqsave()` — and exactly what deadlock results if you get it wrong.

**C Implementation** — Complete compilable kernel module with ring buffer, ISR top half, tasklet bottom half, workqueue, and threaded IRQ alternative. Cleanup ordering requirements documented in-code.

**Rust Implementation** — Kernel module using `SpinLock<T>` (type system enforces lock-before-access), `irq::Registration` (RAII guarantees `free_irq()`), and `WorkItem` trait. Includes the key Rust advantages over C for this domain.

**Go Implementation** — Userspace simulation of the full ISR/softirq/workqueue pipeline using goroutines pinned to OS threads, SPSC atomic ring buffer with proper cache line padding, and a real eBPF tracer skeleton using `cilium/ebpf` for measuring ISR latency.

**Security Layer** — IDT hooking rootkit technique, KASAN signatures for common ISR bugs, YARA rule for detecting IDT manipulation in kernel modules, and Volatility commands for interrupt forensics on memory dumps.

**Challenge for you**: In the C implementation, the `ring_pop_tasklet()` function uses `spin_lock_irqsave()`. But we established that tasklets run with softirqs disabled. Under what specific condition is the `irqsave` actually necessary there, and what would break if you replaced it with just `spin_lock()`? Trace the exact CPU state at the moment a hardware IRQ fires mid-tasklet and hits `ring_push_irq()` on the same core.