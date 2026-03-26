# Hardirqs, Softirqs & the Linux Interrupt Subsystem
## A Complete, In-Depth Systems Programming Reference

> *"Interrupts are the nervous system of the kernel. Understanding them is understanding how the machine truly breathes."*

---

## Table of Contents

1. [Foundational Mental Model: The Interrupt Problem](#1-foundational-mental-model-the-interrupt-problem)
2. [Hardware Interrupts (hardirq) — Deep Dive](#2-hardware-interrupts-hardirq--deep-dive)
3. [The Interrupt Descriptor Table (IDT)](#3-the-interrupt-descriptor-table-idt)
4. [Top Half / Bottom Half Split — The Core Design Pattern](#4-top-half--bottom-half-split--the-core-design-pattern)
5. [Softirqs — Architecture & Internals](#5-softirqs--architecture--internals)
6. [Tasklets — Softirq Wrappers](#6-tasklets--softirq-wrappers)
7. [Workqueues — Process Context Deferral](#7-workqueues--process-context-deferral)
8. [IRQ Threading (threaded IRQs)](#8-irq-threading-threaded-irqs)
9. [Interrupt Context Rules & Constraints](#9-interrupt-context-rules--constraints)
10. [SMP, CPU Affinity & IRQ Balancing](#10-smp-cpu-affinity--irq-balancing)
11. [NAPI — The Network Polling Model](#11-napi--the-network-polling-model)
12. [IRQ Coalescing & Mitigation](#12-irq-coalescing--mitigation)
13. [Real-Time Linux (PREEMPT_RT) & Interrupts](#13-real-time-linux-preempt_rt--interrupts)
14. [eBPF & Interrupt Observability](#14-ebpf--interrupt-observability)
15. [C Implementation — Complete Examples](#15-c-implementation--complete-examples)
16. [Rust Implementation — Kernel & Userspace](#16-rust-implementation--kernel--userspace)
17. [Debugging, Profiling & Observability Tools](#17-debugging-profiling--observability-tools)
18. [Common Pitfalls & Anti-Patterns](#18-common-pitfalls--anti-patterns)
19. [Performance Engineering Mindset](#19-performance-engineering-mindset)

---

## 1. Foundational Mental Model: The Interrupt Problem

### 1.1 The Core Problem

A CPU executes instructions sequentially. Yet the real world is asynchronous — a NIC receives a packet, a disk completes a read, a timer fires, a keyboard key is pressed. The machine must react to these events *immediately*, without polling (which wastes CPU cycles) and without missing events (which breaks correctness).

The solution is **interrupts**: hardware signals that forcibly divert the CPU from whatever it is doing.

```
Normal execution:          IRQ fires:
                           
  [Instruction N  ]          [Instruction N  ]
  [Instruction N+1]    →     [SAVE CONTEXT   ]  ← CPU stops current work
  [Instruction N+2]          [RUN HANDLER    ]  ← Executes interrupt handler
  [Instruction N+3]          [RESTORE CONTEXT]  ← Returns to Instruction N+1
```

### 1.2 The Tension: Latency vs. Throughput

This is the fundamental interrupt design tension:

| Goal | Requirement |
|---|---|
| **Acknowledge hardware quickly** | Short, fast interrupt handler |
| **Do real work** | Often complex processing needed |
| **Don't block other interrupts** | Can't hold IRQ disabled too long |
| **Use kernel concurrency correctly** | Can't sleep in interrupt context |

The Linux kernel resolves this tension with **deferred work mechanisms**:

```
Hardware Event
    │
    ▼
[hardirq - TOP HALF]    ← Runs with IRQs disabled, must be FAST
    │ schedules deferred work
    ▼
[softirq / tasklet / workqueue - BOTTOM HALF]   ← Deferred, more flexible
    │
    ▼
[Process context / userspace]
```

### 1.3 Interrupt Taxonomy in Linux

```
Interrupt Sources
├── Hardware Interrupts (hardirq)
│   ├── External (I/O devices: NIC, disk, USB, keyboard)
│   ├── Timer (APIC timer, HPET)
│   ├── Inter-Processor Interrupts (IPI)
│   └── Non-Maskable Interrupts (NMI)
│
└── Software Interrupts
    ├── Exceptions (divide by zero, page fault, general protection fault)
    ├── Software-triggered INT instruction (syscalls on x86-32)
    └── softirqs (kernel's deferred work mechanism — NOT the INT instruction)
```

> **Critical Distinction**: The Linux "softirq" mechanism is **not** the x86 `INT` instruction. It is a kernel-level deferred execution framework with its own scheduler. The naming is historical and confusing.

---

## 2. Hardware Interrupts (hardirq) — Deep Dive

### 2.1 Physical Signal Path

```
Device (NIC/disk/timer)
    │
    │ Electrical signal on IRQ line
    ▼
[PIC / APIC]            ← Programmable Interrupt Controller
    │
    │ Delivers interrupt vector to CPU
    ▼
[CPU — checks IF flag]  ← Interrupt Flag in RFLAGS register
    │
    ├── IF=0: Interrupt masked (queued by APIC)
    └── IF=1: CPU accepts interrupt
            │
            ▼
        [Save RFLAGS, CS, RIP onto stack]
        [Look up IDT[vector]]
        [Jump to handler]
```

### 2.2 APIC Architecture (Modern x86)

On SMP systems, each CPU has a **Local APIC (LAPIC)** and devices connect through an **I/O APIC**:

```
Device A ──►┐
Device B ──►│  [I/O APIC]  ──IRQ routing──►  [LAPIC CPU0]
Device C ──►│              ──IRQ routing──►  [LAPIC CPU1]
Device D ──►┘              ──IRQ routing──►  [LAPIC CPU2]

IPI (CPU-to-CPU)  ────────────────────────►  [LAPIC CPU*]
```

The I/O APIC's **Redirection Table** determines which CPU receives which IRQ — this is the basis of IRQ affinity.

### 2.3 IRQ Vector Assignments (x86-64)

| Vector Range | Usage |
|---|---|
| 0x00–0x1F | CPU Exceptions (reserved by Intel) |
| 0x20–0x2F | Legacy PIC IRQs (8259A) |
| 0x30–0xEF | Kernel-assigned device IRQs |
| 0xF0–0xFA | Local APIC vectors (timer, error, etc.) |
| 0xFB–0xFF | IPI vectors (reschedule, TLB flush, etc.) |

### 2.4 What Happens at the CPU Level During a hardirq

**Step-by-step hardware sequence (x86-64):**

1. CPU finishes current instruction (interrupts are *instruction-boundary* events)
2. CPU checks `IF` (Interrupt Flag) in `RFLAGS`
3. CPU atomically:
   - Saves `SS`, `RSP`, `RFLAGS`, `CS`, `RIP` onto the *current* stack
   - Clears `IF` (disabling further interrupts)
   - Clears `TF` (trap flag)
   - Loads new `CS:RIP` from IDT entry
4. Kernel handler runs (with interrupts disabled by default)
5. Handler re-enables interrupts if it wants (IRQF_SHARED, nested IRQs)
6. Handler calls `iret` (Interrupt Return), atomically restoring saved state

### 2.5 Linux's Entry Path for hardirqs

The actual kernel code path (simplified from `arch/x86/kernel/irq.c`):

```c
/* Entry from assembly (irq_entries_start) */
common_interrupt:
    /* Assembly prologue: save all registers */
    call interrupt_entry    /* switch to kernel stack if from userspace */
    
    /* C handler */
    do_IRQ(pt_regs):
        vector = ~regs->orig_ax   /* vector number encoded by assembly */
        irq_enter()               /* track interrupt nesting, disable preemption */
        handle_irq(desc, regs)    /* call registered handler */
        irq_exit()                /* check if softirqs need to run */
    
    /* Assembly epilogue: restore registers, iret */
```

**`irq_enter()` and `irq_exit()` are crucial:**

```c
void irq_enter(void) {
    /* Increment preempt_count interrupt counter */
    preempt_count_add(HARDIRQ_OFFSET);
    /* Account time to hardirq */
}

void irq_exit(void) {
    preempt_count_sub(HARDIRQ_OFFSET);
    /* If not in nested interrupt AND softirqs pending: */
    if (!in_interrupt() && local_softirq_pending())
        invoke_softirq();  /* <-- CRITICAL: this is how softirqs get triggered */
}
```

### 2.6 Registering a hardirq Handler in C

```c
#include <linux/interrupt.h>

/* The IRQ handler signature */
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    
    /* 1. Check if this interrupt is ours (for shared IRQs) */
    if (!(read_status_reg(dev) & MY_IRQ_BIT))
        return IRQ_NONE;   /* Not ours, tell the kernel */
    
    /* 2. Acknowledge the hardware (clear the interrupt) */
    write_ack_reg(dev);
    
    /* 3. Do MINIMAL work — just capture data, schedule bottom half */
    dev->data_ready = true;
    tasklet_schedule(&dev->tasklet);  /* defer real work */
    
    return IRQ_HANDLED;
}

/* Registration */
static int my_device_probe(struct platform_device *pdev)
{
    int irq = platform_get_irq(pdev, 0);
    
    ret = request_irq(
        irq,                /* IRQ number */
        my_irq_handler,     /* Handler function */
        IRQF_SHARED,        /* Flags: shared IRQ line */
        "my_device",        /* Name (shows in /proc/interrupts) */
        dev                 /* Cookie passed to handler */
    );
}

/* Deregistration (MUST be called before device goes away) */
static void my_device_remove(struct platform_device *pdev)
{
    free_irq(irq, dev);
}
```

**`irqreturn_t` values:**

| Return Value | Meaning |
|---|---|
| `IRQ_NONE` | This IRQ was not from our device (shared lines) |
| `IRQ_HANDLED` | We handled it |
| `IRQ_WAKE_THREAD` | Wake the threaded handler (see threaded IRQs) |

### 2.7 Interrupt Flags (IRQF_*)

```c
IRQF_SHARED        /* Multiple devices share this IRQ line */
IRQF_TRIGGER_RISING  /* Edge-triggered: rising edge */
IRQF_TRIGGER_FALLING /* Edge-triggered: falling edge */
IRQF_TRIGGER_HIGH    /* Level-triggered: active high */
IRQF_TRIGGER_LOW     /* Level-triggered: active low */
IRQF_ONESHOT         /* Keep IRQ disabled until threaded handler completes */
IRQF_NO_SUSPEND      /* Don't disable during system suspend */
IRQF_EARLY_RESUME    /* Resume early in the resume sequence */
```

---

## 3. The Interrupt Descriptor Table (IDT)

### 3.1 Structure

The IDT is an array of 256 gate descriptors, loaded into the CPU via the `LIDT` instruction. Each entry is 16 bytes on x86-64:

```c
/* Each IDT entry (gate descriptor) */
struct gate_struct {
    u16 offset_low;     /* Bits 0-15 of handler address */
    u16 segment;        /* Code segment selector */
    u16 bits;           /* Gate type, DPL, present bit */
    u16 offset_middle;  /* Bits 16-31 of handler address */
    u32 offset_high;    /* Bits 32-63 of handler address */
    u32 reserved;
} __attribute__((packed));
```

Gate types:
- **Interrupt Gate**: Clears `IF` on entry (used for hardware IRQs)
- **Trap Gate**: Does NOT clear `IF` (used for exceptions/syscalls)
- **Task Gate**: x86-32 only, hardware task switching (not used by Linux)

### 3.2 Linux IDT Setup

```c
/* arch/x86/kernel/idt.c */

/* Exception handlers (vectors 0-31) */
static const __initconst struct idt_data def_idts[] = {
    INTG(X86_TRAP_DE,   asm_exc_divide_error),    /* #DE: divide by zero */
    INTG(X86_TRAP_NMI,  asm_exc_nmi),             /* NMI */
    INTG(X86_TRAP_PF,   asm_exc_page_fault),       /* #PF: page fault */
    INTG(X86_TRAP_GP,   asm_exc_general_protection), /* #GP */
    /* ... */
};

/* Device IRQ handlers (vectors 32-255) */
/* These are set dynamically by request_irq() */
```

### 3.3 Viewing the IDT from Userspace

```bash
# Not directly accessible, but you can see interrupt activity:
cat /proc/interrupts

# Output:
#            CPU0       CPU1       CPU2       CPU3
#   0:         46          0          0          0  IO-APIC    2-edge      timer
#   8:          0          0          0          1  IO-APIC    8-edge      rtc0
#  16:          0          0          0          0  IO-APIC   16-fasteoi   uhci_hcd:usb3
# NMI:          0          0          0          0  Non-maskable interrupts
# LOC:     123456     234567     345678     456789  Local timer interrupts
# ...
```

---

## 4. Top Half / Bottom Half Split — The Core Design Pattern

### 4.1 The Fundamental Rule

**Top half (hardirq)**: Runs with interrupts disabled (or with only higher-priority IRQs enabled). Must be:
- **Fast** (microseconds, not milliseconds)
- **Non-sleeping** (absolutely cannot call `schedule()`)
- **Minimal** (just acknowledge hardware and schedule deferred work)

**Bottom half**: Deferred work that runs later, with interrupts re-enabled. Can be:
- Slower
- More complex
- Still cannot sleep (softirq/tasklet) OR can sleep (workqueue)

### 4.2 Why This Split Exists

If the top half does too much work:
1. Other interrupts are delayed → increased interrupt latency
2. On level-triggered interrupts: hardware will keep re-asserting the IRQ line
3. The system becomes unresponsive

Real-world example — **Network card receives a packet:**

```
[NIC asserts IRQ]
    │
    ▼ TOP HALF (< 5 microseconds)
    ├── Acknowledge interrupt to NIC
    ├── Quick sanity check
    └── Schedule NAPI poll / softirq
    
    ▼ BOTTOM HALF (softirq — NET_RX_SOFTIRQ)
    ├── DMA-copy packet from ring buffer
    ├── Allocate sk_buff
    ├── Parse Ethernet/IP headers
    ├── Demultiplex to socket
    └── Wake up blocking recv() call
```

### 4.3 The Four Bottom Half Mechanisms

| Mechanism | Context | Can Sleep? | Per-CPU? | Use Case |
|---|---|---|---|---|
| **softirq** | Soft interrupt context | No | Yes (dedicated) | High-freq, performance-critical |
| **tasklet** | Soft interrupt context | No | No (serialized) | General device drivers |
| **workqueue** | Process (kernel thread) | Yes | Configurable | Work needing sleep, filesystem |
| **threaded IRQ** | Kernel thread | Yes | No | Modern driver model |

---

## 5. Softirqs — Architecture & Internals

### 5.1 What is a Softirq?

A softirq is a **statically registered, per-CPU deferred execution mechanism**. Unlike tasklets, softirqs can run **concurrently on multiple CPUs simultaneously** — the same softirq type can execute in parallel on CPU0 and CPU1. This makes them extremely powerful and extremely dangerous (requiring careful concurrency design).

### 5.2 The Statically Defined Softirq Table

Linux defines exactly **10 softirqs** (compile-time, not runtime):

```c
/* include/linux/interrupt.h */
enum {
    HI_SOFTIRQ=0,          /* High-priority tasklets */
    TIMER_SOFTIRQ,         /* Timer wheel processing */
    NET_TX_SOFTIRQ,        /* Network transmission */
    NET_RX_SOFTIRQ,        /* Network reception */
    BLOCK_SOFTIRQ,         /* Block device completion */
    IRQ_POLL_SOFTIRQ,      /* IRQ polling (blk-mq) */
    TASKLET_SOFTIRQ,       /* Normal-priority tasklets */
    SCHED_SOFTIRQ,         /* Scheduler (load balancing) */
    HRTIMER_SOFTIRQ,       /* High-resolution timers */
    RCU_SOFTIRQ,           /* RCU callbacks */
    NR_SOFTIRQS            /* Sentinel: = 10 */
};
```

**Priority matters**: Softirqs are processed in vector order. `HI_SOFTIRQ` (0) runs before `RCU_SOFTIRQ` (9).

### 5.3 The softirq Descriptor

```c
/* kernel/softirq.c */
struct softirq_action {
    void (*action)(struct softirq_action *);
};

static struct softirq_action softirq_vec[NR_SOFTIRQS] __cacheline_aligned_in_smp;
```

### 5.4 The Per-CPU Pending Bitmap

Each CPU has a **32-bit bitmask** of pending softirqs:

```c
/* In the per-CPU area */
DECLARE_PER_CPU(unsigned int, __softirq_pending);

/* Raising a softirq (marking it pending on current CPU) */
static inline void raise_softirq_irqoff(unsigned int nr)
{
    __raise_softirq_irqoff(nr);
    /* If not in interrupt context, wake ksoftirqd */
    if (!in_interrupt())
        wakeup_softirqd();
}

static inline void __raise_softirq_irqoff(unsigned int nr)
{
    or_softirq_pending(1UL << nr);  /* atomic bit set */
}
```

### 5.5 The softirq Execution Engine — `__do_softirq()`

This is the heart of the softirq system:

```c
/* kernel/softirq.c — simplified but accurate */
asmlinkage __visible void __softirq_entry __do_softirq(void)
{
    unsigned long end = jiffies + MAX_SOFTIRQ_TIME;  /* time budget */
    int max_restart = MAX_SOFTIRQ_RESTART;           /* = 10 iterations */
    struct softirq_action *h;
    __u32 pending;
    int softirq_bit;

    /* Disable softirq processing on this CPU (prevent re-entry) */
    __local_bh_disable_ip(_RET_IP_, SOFTIRQ_OFFSET);
    
    /* Capture pending bitmap and clear it atomically */
    pending = local_softirq_pending();
    
restart:
    /* Clear the pending bits we're about to process */
    set_softirq_pending(0);
    
    /* Re-enable hardware interrupts during softirq processing */
    local_irq_enable();

    h = softirq_vec;
    
    while ((softirq_bit = ffs(pending))) {  /* ffs: find first set bit */
        unsigned int vec_nr = softirq_bit - 1;
        
        h += softirq_bit - 1;
        
        /* Account time per softirq type */
        kstat_incr_softirqs_this_cpu(vec_nr);
        
        /* Call the actual handler */
        h->action(h);   /* e.g., net_rx_action, run_timer_softirq */
        
        h++;
        pending >>= softirq_bit;
    }
    
    local_irq_disable();
    
    /* Check if new softirqs became pending while we ran */
    pending = local_softirq_pending();
    if (pending) {
        if (time_before(jiffies, end) && !need_resched() &&
            --max_restart)
            goto restart;  /* Process again if budget allows */
        
        /* Budget exhausted: wake ksoftirqd to handle remainder */
        wakeup_softirqd();
    }
    
    __local_bh_enable(SOFTIRQ_OFFSET);
}
```

**Key insight**: `local_irq_enable()` is called during softirq processing — hardware interrupts are **re-enabled**. This means a hardirq can preempt a softirq. But a softirq will NOT preempt another softirq on the same CPU (SOFTIRQ_OFFSET in preempt_count prevents this).

### 5.6 Where softirqs Are Executed

Softirqs execute in **three places**:

1. **After hardirq completion** — `irq_exit()` calls `invoke_softirq()`
2. **In `ksoftirqd` kernel thread** — when budget is exhausted or in process context
3. **Explicit `local_bh_enable()`** — when bottom-half processing is re-enabled

### 5.7 `ksoftirqd` — The Softirq Daemon

Each CPU has its own `ksoftirqd/N` kernel thread (where N is CPU number):

```bash
$ ps aux | grep ksoftirqd
root         9  0.0  0.0      0     0 ?  S   Mar25   0:00 [ksoftirqd/0]
root        18  0.0  0.0      0     0 ?  S   Mar25   0:00 [ksoftirqd/1]
root        24  0.0  0.0      0     0 ?  S   Mar25   0:00 [ksoftirqd/2]
```

`ksoftirqd` runs as a normal schedulable thread, so it can be preempted by user processes. This is the fairness mechanism — softirqs don't starve user processes.

```c
/* kernel/softirq.c */
static int ksoftirqd_should_run(unsigned int cpu)
{
    return local_softirq_pending();
}

static void run_ksoftirqd(unsigned int cpu)
{
    ksoftirqd_run_begin();
    if (local_softirq_pending()) {
        __do_softirq();
        ksoftirqd_run_end();
        cond_resched();   /* yield to other processes */
        return;
    }
    ksoftirqd_run_end();
}
```

### 5.8 Registering a softirq

**softirqs cannot be registered at runtime** — they are compiled into the kernel:

```c
/* Called once during kernel init */
void open_softirq(int nr, void (*action)(struct softirq_action *))
{
    softirq_vec[nr].action = action;
}

/* Example: network subsystem init */
void __init net_dev_init(void)
{
    open_softirq(NET_TX_SOFTIRQ, net_tx_action);
    open_softirq(NET_RX_SOFTIRQ, net_rx_action);
}
```

### 5.9 Softirq Concurrency Model

```
CPU0                        CPU1
────────────────────────    ────────────────────────
NET_RX_SOFTIRQ running      NET_RX_SOFTIRQ running  ← CONCURRENT! Same type!
    per_cpu(rx_queue, 0)        per_cpu(rx_queue, 1) ← Must use per-CPU data
    or spin_lock needed         or spin_lock needed
```

This is the price of softirq performance: **you must handle concurrent execution yourself**.

---

## 6. Tasklets — Softirq Wrappers

### 6.1 What is a Tasklet?

A tasklet is a **dynamically registerable**, serialized form of deferred work built on top of `HI_SOFTIRQ` and `TASKLET_SOFTIRQ`. Unlike raw softirqs:

- The **same tasklet** never runs concurrently on multiple CPUs
- Multiple **different** tasklets can run concurrently
- Can be registered by drivers at runtime

### 6.2 Tasklet Data Structure

```c
/* include/linux/interrupt.h */
struct tasklet_struct {
    struct tasklet_struct *next;   /* Linked list for per-CPU queue */
    unsigned long state;           /* TASKLET_STATE_SCHED, TASKLET_STATE_RUN */
    atomic_t count;                /* Reference count (disabled if > 0) */
    bool use_callback;             /* Use new callback style? */
    union {
        void (*func)(unsigned long);    /* Old-style: data passed as unsigned long */
        void (*callback)(struct tasklet_struct *); /* New-style (kernel 5.x+) */
    };
    unsigned long data;            /* Argument for old-style func */
};
```

### 6.3 Tasklet States

```
TASKLET_STATE_SCHED (bit 0): Tasklet is scheduled (in the queue)
TASKLET_STATE_RUN   (bit 1): Tasklet is currently running (SMP guard)
```

The `TASKLET_STATE_RUN` bit is the serialization mechanism: before running, the kernel atomically test-and-sets this bit. If already set (running on another CPU), execution is deferred.

### 6.4 Tasklet Implementation Internals

```c
/* kernel/softirq.c — the tasklet softirq handler */
static void tasklet_action(struct softirq_action *a)
{
    struct tasklet_struct *list;
    
    /* Take the per-CPU list atomically */
    local_irq_disable();
    list = __this_cpu_read(tasklet_vec.head);
    __this_cpu_write(tasklet_vec.head, NULL);
    __this_cpu_write(tasklet_vec.tail, &__this_cpu(tasklet_vec).head);
    local_irq_enable();
    
    while (list) {
        struct tasklet_struct *t = list;
        list = list->next;
        
        /* Try to acquire the run lock (SMP serialization) */
        if (tasklet_trylock(t)) {
            /* Not disabled? */
            if (!atomic_read(&t->count)) {
                /* Clear scheduled state */
                if (!test_and_clear_bit(TASKLET_STATE_SCHED, &t->state))
                    BUG();
                
                /* Execute the handler */
                if (t->use_callback)
                    t->callback(t);
                else
                    t->func(t->data);
                
                tasklet_unlock(t);
                continue;
            }
            tasklet_unlock(t);
        }
        
        /* Could not run — re-schedule */
        local_irq_disable();
        t->next = NULL;
        *__this_cpu_read(tasklet_vec.tail) = t;
        __this_cpu_write(tasklet_vec.tail, &t->next);
        __raise_softirq_irqoff(TASKLET_SOFTIRQ);
        local_irq_enable();
    }
}
```

### 6.5 Using Tasklets in C (Complete Example)

```c
#include <linux/interrupt.h>
#include <linux/module.h>

struct my_driver_data {
    struct tasklet_struct rx_tasklet;
    unsigned long rx_count;
    spinlock_t lock;
};

/* New-style tasklet callback (kernel 5.9+) */
static void rx_tasklet_callback(struct tasklet_struct *t)
{
    struct my_driver_data *drv = from_tasklet(drv, t, rx_tasklet);
    
    /* This runs in softirq context — no sleeping! */
    /* But can use spin_lock (NOT spin_lock_irqsave — we're already in BH context) */
    spin_lock_bh(&drv->lock);
    drv->rx_count++;
    spin_unlock_bh(&drv->lock);
    
    /* Process received data... */
    pr_info("Processed RX packet #%lu\n", drv->rx_count);
}

/* Old-style tasklet (still widely used) */
static void tx_tasklet_func(unsigned long data)
{
    struct my_driver_data *drv = (struct my_driver_data *)data;
    /* process TX completion */
}

static int __init my_driver_init(void)
{
    struct my_driver_data *drv = kzalloc(sizeof(*drv), GFP_KERNEL);
    spin_lock_init(&drv->lock);
    
    /* New-style initialization */
    tasklet_setup(&drv->rx_tasklet, rx_tasklet_callback);
    
    /* Old-style initialization */
    /* tasklet_init(&drv->tx_tasklet, tx_tasklet_func, (unsigned long)drv); */
    
    return 0;
}

/* In the hardirq handler: */
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
    struct my_driver_data *drv = dev_id;
    
    /* Minimal top-half work */
    acknowledge_hardware();
    
    /* Schedule bottom half */
    tasklet_schedule(&drv->rx_tasklet);   /* safe to call from any context */
    
    return IRQ_HANDLED;
}

/* Cleanup */
static void my_driver_exit(void)
{
    /* MUST kill tasklet before freeing resources */
    tasklet_kill(&drv->rx_tasklet);  /* waits for running tasklet to complete */
    kfree(drv);
}
```

### 6.6 Tasklet vs Hi-Tasklet

```c
/* High-priority tasklet: runs before TASKLET_SOFTIRQ */
tasklet_hi_schedule(&t);   /* Uses HI_SOFTIRQ vector */

/* Normal tasklet: runs via TASKLET_SOFTIRQ */
tasklet_schedule(&t);      /* Uses TASKLET_SOFTIRQ vector */
```

Use `tasklet_hi_schedule` only when latency is absolutely critical (rare).

### 6.7 Deprecation Notice

> **Important**: Tasklets are being **deprecated** in the Linux kernel (discussion started around 5.x series). The preferred modern approach is **threaded IRQs** or **workqueues**. New code should avoid tasklets where possible.

---

## 7. Workqueues — Process Context Deferral

### 7.1 Why Workqueues?

Softirqs and tasklets cannot sleep. But many operations require sleeping:
- Memory allocation with `GFP_KERNEL`
- Filesystem operations
- Waiting for hardware with timeouts
- Acquiring mutexes

Workqueues execute in **process context** (kernel threads), so they can sleep, be scheduled, and use all process-context primitives.

### 7.2 Architecture: Concurrency-Managed Workqueue (cmwq)

Since kernel 2.6.36, Linux uses the **concurrency-managed workqueue (cmwq)** system:

```
[Workqueue A]                [Workqueue B]
      │                            │
      │                            │
      ▼                            ▼
[Worker Pool — Normal Priority]    [Worker Pool — Highpri]
  [kworker/0:0]                      [kworker/0:0H]
  [kworker/0:1]                      [kworker/1:0H]
  [kworker/1:0]
  [kworker/1:1]
  [kworker/u8:0]  ← unbound workers
```

The kernel dynamically creates/destroys worker threads based on concurrency needs. If all workers are blocked (sleeping), a new one is created.

### 7.3 Work Item

```c
struct work_struct {
    atomic_long_t data;        /* Flags + workqueue pointer */
    struct list_head entry;    /* Queue linkage */
    work_func_t func;          /* The callback */
#ifdef CONFIG_LOCKDEP
    struct lockdep_map lockdep_map;
#endif
};

/* The callback type */
typedef void (*work_func_t)(struct work_struct *work);
```

### 7.4 Workqueue Types

```c
/* 1. System workqueue (shared, most common) */
schedule_work(&my_work);         /* queues on system_wq */

/* 2. System high-priority workqueue */
queue_work(system_highpri_wq, &my_work);

/* 3. System long-running workqueue (work may take a long time) */
queue_work(system_long_wq, &my_work);

/* 4. System unbound workqueue (not bound to specific CPU) */
queue_work(system_unbound_wq, &my_work);

/* 5. Custom workqueue */
struct workqueue_struct *my_wq = alloc_workqueue(
    "my_driver_wq",
    WQ_UNBOUND | WQ_MEM_RECLAIM,  /* flags */
    0                              /* max_active: 0 = default */
);
```

**Workqueue flags:**

| Flag | Meaning |
|---|---|
| `WQ_UNBOUND` | Not bound to a specific CPU |
| `WQ_FREEZABLE` | Freeze during system suspend |
| `WQ_MEM_RECLAIM` | Can be used during memory reclaim |
| `WQ_HIGHPRI` | High-priority workers |
| `WQ_CPU_INTENSIVE` | Long-running, don't count for concurrency |
| `WQ_SYSFS` | Expose via sysfs |

### 7.5 Complete Workqueue Example in C

```c
#include <linux/workqueue.h>
#include <linux/module.h>
#include <linux/delay.h>

struct my_work_data {
    struct work_struct work;    /* Must be first, or use container_of */
    int packet_id;
    u8 *data;
    size_t len;
};

/* Workqueue handler — runs in process context, CAN sleep */
static void process_packet_work(struct work_struct *work)
{
    struct my_work_data *wd = container_of(work, struct my_work_data, work);
    
    /* Can sleep here! */
    if (mutex_lock_interruptible(&global_mutex))
        goto out;
    
    /* Can allocate memory with GFP_KERNEL */
    u8 *buffer = kmalloc(wd->len * 2, GFP_KERNEL);
    
    /* Can do filesystem I/O */
    /* Can wait for hardware */
    msleep(10);  /* Would be illegal in softirq context */
    
    pr_info("Processed packet %d (%zu bytes)\n", wd->packet_id, wd->len);
    
    kfree(buffer);
    mutex_unlock(&global_mutex);
out:
    kfree(wd->data);
    kfree(wd);  /* Free the work struct itself */
}

/* From interrupt handler: schedule work */
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
    struct my_work_data *wd = kmalloc(sizeof(*wd), GFP_ATOMIC);  /* GFP_ATOMIC! */
    if (!wd)
        return IRQ_HANDLED;
    
    wd->packet_id = get_packet_id();
    wd->data = kmalloc(64, GFP_ATOMIC);
    wd->len = 64;
    
    INIT_WORK(&wd->work, process_packet_work);
    
    /* Queue on system workqueue */
    schedule_work(&wd->work);
    
    return IRQ_HANDLED;
}

/* Delayed work */
struct delayed_work my_delayed_work;

static void delayed_handler(struct work_struct *work)
{
    pr_info("Fired after delay\n");
}

static int __init my_init(void)
{
    INIT_DELAYED_WORK(&my_delayed_work, delayed_handler);
    
    /* Schedule to run after 1 second (HZ jiffies) */
    schedule_delayed_work(&my_delayed_work, HZ);
    
    return 0;
}

static void __exit my_exit(void)
{
    /* Cancel and wait for pending work */
    cancel_delayed_work_sync(&my_delayed_work);
}
```

---

## 8. IRQ Threading (Threaded IRQs)

### 8.1 Concept

Threaded IRQs are the **modern preferred approach** for drivers. Instead of splitting into top-half/bottom-half manually, the framework does it:

- **Top half** (`handler`): Runs in hardirq context, does minimal work, returns `IRQ_WAKE_THREAD`
- **Bottom half** (`thread_fn`): Runs in a dedicated kernel thread per IRQ, can sleep

### 8.2 API

```c
int request_threaded_irq(
    unsigned int irq,
    irq_handler_t handler,       /* Primary handler (hardirq context) */
    irq_handler_t thread_fn,     /* Threaded handler (process context) */
    unsigned long irqflags,
    const char *devname,
    void *dev_id
);
```

### 8.3 Complete Threaded IRQ Example

```c
#include <linux/interrupt.h>

/* Primary handler: runs in hardirq context */
static irqreturn_t my_primary_handler(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    
    /* Verify interrupt is ours */
    if (!(read_reg(dev, STATUS) & OUR_IRQ_BIT))
        return IRQ_NONE;
    
    /* Disable interrupt at hardware level (optional, for level-triggered) */
    disable_irq_at_hardware(dev);
    
    /* Tell the kernel to wake our thread */
    return IRQ_WAKE_THREAD;
}

/* Threaded handler: runs in kernel thread context — CAN SLEEP */
static irqreturn_t my_threaded_handler(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    
    /* Full processing with sleep allowed */
    u8 data[256];
    if (wait_for_completion_interruptible_timeout(&dev->ready, HZ) <= 0)
        return IRQ_HANDLED;
    
    /* Allocate memory, do I/O, whatever */
    process_interrupt_data(dev, data);
    
    /* Re-enable interrupt */
    enable_irq_at_hardware(dev);
    
    return IRQ_HANDLED;
}

static int my_probe(struct platform_device *pdev)
{
    int irq = platform_get_irq(pdev, 0);
    
    /* IRQF_ONESHOT: keep IRQ disabled until thread_fn completes */
    return request_threaded_irq(irq,
                                my_primary_handler,
                                my_threaded_handler,
                                IRQF_ONESHOT | IRQF_SHARED,
                                "my_device",
                                dev);
}
```

### 8.4 NULL Primary Handler

If the primary handler is NULL, the kernel provides a default that simply disables the IRQ and wakes the thread:

```c
/* Simplest possible threaded IRQ — primary=NULL means kernel default */
request_threaded_irq(irq, NULL, my_threaded_handler,
                     IRQF_ONESHOT, "my_device", dev);
```

---

## 9. Interrupt Context Rules & Constraints

### 9.1 The `preempt_count` Register

The kernel tracks execution context via a per-CPU **`preempt_count`** variable, which is actually a composite counter:

```
Bit layout of preempt_count:
 
  Bits 31-20: NMI count
  Bits 19-16: Hardirq count (HARDIRQ_OFFSET increments here)
  Bits 15-8:  Softirq count (SOFTIRQ_OFFSET increments here)
  Bits 7-0:   Preemption disable count
```

Macros to query context:

```c
in_irq()          /* in hardirq handler */
in_softirq()      /* in softirq/tasklet (or BH disabled) */
in_interrupt()    /* in_irq() || in_softirq() || in_nmi() */
in_task()         /* running in normal process context */
in_nmi()          /* in NMI handler */
in_serving_softirq()  /* actually executing a softirq (not just BH disabled) */
```

### 9.2 What You CAN and CANNOT Do

```
CONTEXT         | sleep | GFP_KERNEL | spin_lock | mutex | schedule | printk
────────────────┼───────┼────────────┼───────────┼───────┼──────────┼───────
hardirq         |  NO   |     NO     |    YES    |   NO  |    NO    |  YES*
softirq/tasklet |  NO   |     NO     |    YES    |   NO  |    NO    |  YES*
workqueue       |  YES  |    YES     |    YES    |  YES  |   YES    |  YES
threaded IRQ    |  YES  |    YES     |    YES    |  YES  |   YES    |  YES
```

*`printk` is technically safe but can have latency effects.

### 9.3 Memory Allocation in Interrupt Context

```c
/* In hardirq/softirq: MUST use GFP_ATOMIC */
ptr = kmalloc(size, GFP_ATOMIC);   /* Never sleeps, may fail */

/* In process context: can use GFP_KERNEL */
ptr = kmalloc(size, GFP_KERNEL);   /* May sleep, less likely to fail */

/* GFP_ATOMIC characteristics:
   - Uses emergency memory reserves
   - Does not wait for reclaim
   - Higher failure rate under memory pressure
   - ALWAYS check return value! */
```

### 9.4 Locking in Interrupt Context

The critical rule: **if a lock can be acquired in interrupt context, it must be acquired with IRQs disabled everywhere**.

```c
spinlock_t my_lock;

/* From process context, when ISR might also acquire: */
spin_lock_irqsave(&my_lock, flags);    /* disable IRQs + acquire */
/* ... critical section ... */
spin_unlock_irqrestore(&my_lock, flags);  /* release + restore IRQ state */

/* From interrupt context: */
spin_lock(&my_lock);           /* IRQs already disabled in hardirq */
/* ... */
spin_unlock(&my_lock);

/* For softirq context (BH disabled context): */
spin_lock_bh(&my_lock);       /* disable softirqs + acquire */
spin_unlock_bh(&my_lock);

/* WRONG — will deadlock: */
spin_lock(&my_lock);           /* From process context, WITHOUT disabling IRQs */
/* If IRQ fires here and also tries to acquire my_lock: DEADLOCK */
```

### 9.5 The `local_bh_disable()` / `local_bh_enable()` API

These functions disable/enable softirq processing on the local CPU:

```c
local_bh_disable();   /* Increment SOFTIRQ_OFFSET in preempt_count */
/* ... code that cannot be interrupted by softirqs ... */
local_bh_enable();    /* Decrement; if pending softirqs exist, run them */
```

This is used by `spin_lock_bh()` internally:

```c
static inline void spin_lock_bh(spinlock_t *lock)
{
    local_bh_disable();   /* Prevent softirq from preempting us */
    spin_lock(lock);
}
```

---

## 10. SMP, CPU Affinity & IRQ Balancing

### 10.1 IRQ Affinity

Each IRQ can be pinned to a set of CPUs via its affinity mask. This controls which CPUs receive the interrupt:

```bash
# View IRQ affinity
cat /proc/irq/24/smp_affinity        # hexadecimal bitmask
cat /proc/irq/24/smp_affinity_list   # human-readable CPU list

# Pin IRQ 24 to CPUs 0 and 1
echo "03" > /proc/irq/24/smp_affinity        # bitmask: 0b11
echo "0,1" > /proc/irq/24/smp_affinity_list  # list format

# Pin IRQ 24 exclusively to CPU 3
echo "8" > /proc/irq/24/smp_affinity
```

### 10.2 `irqbalance` Daemon

The `irqbalance` daemon automatically distributes IRQs across CPUs based on load. For latency-sensitive applications, you typically **disable irqbalance** and manually set affinity.

```bash
systemctl stop irqbalance
systemctl disable irqbalance
```

### 10.3 IRQ Isolation for RT/Latency

For real-time or high-performance scenarios:

```bash
# Kernel boot parameter: isolate CPU 3 from scheduler
isolcpus=3

# Reserve CPU 3 for IRQs only
# Pin your critical IRQ to CPU 3:
echo "8" > /proc/irq/$NIC_IRQ/smp_affinity

# On isolated CPUs, run your RT task:
taskset -c 3 ./my_rt_application
```

### 10.4 NUMA and IRQ Affinity

On NUMA systems, IRQ affinity matters for memory access:

```c
/* The kernel's NUMA-aware IRQ affinity hint */
int irq_set_affinity_hint(unsigned int irq, const struct cpumask *m);

/* In driver: hint that this IRQ prefers CPUs near its NUMA node */
irq_set_affinity_hint(irq, cpumask_of_node(dev_to_node(dev)));
```

### 10.5 Per-CPU Statistics

```bash
# Per-CPU interrupt counts
watch -n1 cat /proc/interrupts

# Per-CPU softirq counts
cat /proc/softirqs

# Output:
#                     CPU0       CPU1       CPU2       CPU3
#           HI:          1          0          0          0
#        TIMER:     123456     234567     345678     456789
#       NET_TX:          5          3          7          2
#       NET_RX:      98765      87654      76543      65432
#        BLOCK:       1234       2345       3456       4567
#     IRQ_POLL:          0          0          0          0
#      TASKLET:        100        200        150        175
#        SCHED:     500000     600000     550000     450000
#      HRTIMER:       5000       6000       5500       4500
#          RCU:     789012     890123     901234     012345
```

---

## 11. NAPI — The Network Polling Model

### 11.1 The Problem with Pure Interrupt-Driven I/O

At high packet rates (10Gbps+), pure interrupt-driven networking causes **interrupt storms**:
- 10M packets/sec = 10M interrupts/sec
- Each interrupt has overhead: context save/restore, handler invocation, softirq
- CPU spends more time handling interrupts than doing useful work

### 11.2 NAPI Solution: Hybrid Interrupt + Polling

```
Low traffic:           High traffic:
  IRQ → process         IRQ fires → disable IRQ
  IRQ → process         Poll loop (process N packets)
  IRQ → process         Re-enable IRQ when quota exhausted
                        Poll loop again if more packets
```

### 11.3 NAPI Structure

```c
struct napi_struct {
    struct list_head poll_list;   /* Polling list */
    unsigned long state;          /* NAPI_STATE_SCHED, etc. */
    int weight;                   /* Max packets per poll: typically 64 */
    int (*poll)(struct napi_struct *, int);  /* Poll function */
    /* ... */
};
```

### 11.4 Implementing NAPI in a Driver

```c
#include <linux/netdevice.h>

struct my_nic {
    struct net_device *netdev;
    struct napi_struct napi;
    struct sk_buff_head rx_queue;
    /* ... */
};

/* NAPI poll function — called in softirq context */
static int my_nic_poll(struct napi_struct *napi, int budget)
{
    struct my_nic *nic = container_of(napi, struct my_nic, napi);
    int work_done = 0;
    
    /* Process up to 'budget' packets */
    while (work_done < budget) {
        struct sk_buff *skb = receive_next_packet(nic);
        if (!skb)
            break;  /* No more packets in ring buffer */
        
        /* Send up the network stack */
        netif_receive_skb(skb);
        work_done++;
    }
    
    /* If we processed fewer than budget: no more packets */
    if (work_done < budget) {
        /* Disable polling, re-enable interrupts */
        napi_complete_done(napi, work_done);
        enable_irq_at_hardware(nic);
    }
    
    return work_done;
}

/* Interrupt handler — minimal! */
static irqreturn_t my_nic_irq(int irq, void *dev_id)
{
    struct my_nic *nic = dev_id;
    
    /* Disable further interrupts from this NIC */
    disable_irq_at_hardware(nic);
    
    /* Schedule NAPI poll */
    if (napi_schedule_prep(&nic->napi)) {
        __napi_schedule(&nic->napi);  /* Adds to NET_RX_SOFTIRQ */
    }
    
    return IRQ_HANDLED;
}

/* Device initialization */
static int my_nic_probe(struct pci_dev *pdev, ...)
{
    struct my_nic *nic = /* ... */;
    
    /* Register NAPI with weight 64 */
    netif_napi_add(nic->netdev, &nic->napi, my_nic_poll, 64);
    
    /* Enable NAPI */
    napi_enable(&nic->napi);
    
    /* Register IRQ */
    request_irq(pdev->irq, my_nic_irq, IRQF_SHARED, "my_nic", nic);
}
```

### 11.5 NAPI Budget and Fairness

The `weight` (budget) of 64 is a contract:
- Poll function must process at most `budget` items per call
- Returning `budget` signals "there may be more" → kernel calls again
- Returning `< budget` signals "done" → NAPI completes, IRQ re-enabled

The NET_RX_SOFTIRQ processes all scheduled NAPI devices round-robin.

---

## 12. IRQ Coalescing & Mitigation

### 12.1 Hardware Coalescing (Interrupt Moderation)

NICs support coalescing: deliver one interrupt for N packets or after T microseconds:

```bash
# View current coalescing settings
ethtool -c eth0

# Set: interrupt after 50 packets OR 50 microseconds
ethtool -C eth0 rx-usecs 50 rx-frames 50
ethtool -C eth0 tx-usecs 50 tx-frames 50
```

```c
/* Driver-side: implementing coalescing via ethtool ops */
static int my_get_coalesce(struct net_device *dev,
                            struct ethtool_coalesce *ec,
                            struct kernel_ethtool_coalesce *kec,
                            struct netlink_ext_ack *extack)
{
    struct my_nic *nic = netdev_priv(dev);
    ec->rx_coalesce_usecs = nic->rx_coalesce_usecs;
    ec->rx_max_coalesced_frames = nic->rx_max_frames;
    return 0;
}

static int my_set_coalesce(struct net_device *dev,
                            struct ethtool_coalesce *ec, ...)
{
    struct my_nic *nic = netdev_priv(dev);
    nic->rx_coalesce_usecs = ec->rx_coalesce_usecs;
    write_hardware_register(nic, COALESCE_REG, ec->rx_coalesce_usecs);
    return 0;
}
```

### 12.2 Software IRQ Mitigation

```bash
# Set RPS (Receive Packet Steering) — distribute rx processing across CPUs
echo f > /sys/class/net/eth0/queues/rx-0/rps_cpus  # all 4 CPUs

# Set RFS (Receive Flow Steering) — steer flows to CPUs running the app
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 2048 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

---

## 13. Real-Time Linux (PREEMPT_RT) & Interrupts

### 13.1 The RT Problem with Interrupts

Standard Linux hardirq handlers:
- Run with preemption disabled
- Can run for arbitrary time (problematic for RT)
- Introduce **interrupt latency** (worst-case time to respond to a timer event)

### 13.2 PREEMPT_RT Transformation

With `CONFIG_PREEMPT_RT`, most hardirq handlers become **threaded by default**:

```
Standard kernel:          PREEMPT_RT:
  IRQ fires               IRQ fires
  hardirq runs            Minimal hardirq (just wake thread)
  softirq runs            IRQ thread runs (schedulable!)
  done                    done
```

This means:
- IRQ handlers become preemptible
- RT tasks can preempt IRQ handlers
- Worst-case latency is bounded

### 13.3 RT-Safe Locking

Under PREEMPT_RT:
- `spin_lock` becomes a sleeping lock (rt_mutex)
- `spin_lock_irqsave` no longer disables IRQs (not needed)
- `raw_spin_lock` remains a true spinlock (use sparingly)

```c
/* RT-safe: use raw_spin_lock only for truly atomic operations */
raw_spin_lock_irqsave(&my_lock, flags);   /* Actual spinlock, disables IRQs */
raw_spin_unlock_irqrestore(&my_lock, flags);

/* For most cases, regular spin_lock is fine (becomes mutex under RT) */
spin_lock(&my_lock);
spin_unlock(&my_lock);
```

### 13.4 Measuring Interrupt Latency

```bash
# Install rt-tests
apt-get install rt-tests

# Measure interrupt latency with cyclictest
cyclictest --mlockall --smp --priority=80 --interval=200 --distance=0

# Output:
# T: 0 (  PID) I:200 C: 100000 Min:      3 Act:    5 Avg:    6 Max:      45
# T: 1 (  PID) I:200 C: 100000 Min:      4 Act:    4 Avg:    6 Max:      52
```

---

## 14. eBPF & Interrupt Observability

### 14.1 Overview of eBPF for Interrupt Analysis

eBPF (extended Berkeley Packet Filter) allows attaching programs to kernel tracepoints and kprobes without modifying kernel code. For interrupt analysis, you can:

- Measure hardirq handler duration
- Count softirq invocations per type per CPU
- Trace the full path from IRQ to socket delivery
- Detect interrupt storms

### 14.2 Tracepoints for Interrupts

Linux exposes these tracepoints for IRQ analysis:

```
irq:irq_handler_entry   /* hardirq handler starts */
irq:irq_handler_exit    /* hardirq handler completes */
irq:softirq_entry       /* softirq handler starts */
irq:softirq_exit        /* softirq handler completes */
irq:softirq_raise       /* softirq is raised/scheduled */
irq:tasklet_hi_entry    /* hi-priority tasklet starts */
irq:tasklet_hi_exit     /* hi-priority tasklet completes */
irq:tasklet_entry       /* tasklet starts */
irq:tasklet_exit        /* tasklet completes */
```

### 14.3 BPF C Program — Hardirq Latency Histogram

```c
/* hardirq_latency.bpf.c */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* Map: key=irq number, value=start timestamp */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, u32);
    __type(value, u64);
} start_times SEC(".maps");

/* Map: latency histogram (log2 buckets in microseconds) */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 64);
    __type(key, u32);
    __type(value, u64);
} latency_hist SEC(".maps");

/* Fired when hardirq handler starts */
SEC("tracepoint/irq/irq_handler_entry")
int trace_irq_entry(struct trace_event_raw_irq_handler_entry *ctx)
{
    u32 irq = ctx->irq;
    u64 ts = bpf_ktime_get_ns();
    bpf_map_update_elem(&start_times, &irq, &ts, BPF_ANY);
    return 0;
}

/* Fired when hardirq handler exits */
SEC("tracepoint/irq/irq_handler_exit")
int trace_irq_exit(struct trace_event_raw_irq_handler_exit *ctx)
{
    u32 irq = ctx->irq;
    u64 *start = bpf_map_lookup_elem(&start_times, &irq);
    if (!start)
        return 0;
    
    u64 duration_ns = bpf_ktime_get_ns() - *start;
    u64 duration_us = duration_ns / 1000;
    
    /* Log2 bucket */
    u32 bucket = 0;
    u64 v = duration_us;
    while (v > 1 && bucket < 63) {
        v >>= 1;
        bucket++;
    }
    
    u64 *count = bpf_map_lookup_elem(&latency_hist, &bucket);
    if (count)
        __sync_fetch_and_add(count, 1);
    
    bpf_map_delete_elem(&start_times, &irq);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 14.4 BPF C Program — Softirq Duration Tracker

```c
/* softirq_tracker.bpf.c */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

/* Softirq type names for reference:
   0=HI, 1=TIMER, 2=NET_TX, 3=NET_RX, 4=BLOCK,
   5=IRQ_POLL, 6=TASKLET, 7=SCHED, 8=HRTIMER, 9=RCU */

struct softirq_event {
    u32 vec;
    u32 cpu;
    u64 duration_ns;
};

/* Ring buffer for events to userspace */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);  /* 1MB */
} events SEC(".maps");

/* Per-CPU start time */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 10);  /* NR_SOFTIRQS */
    __type(key, u32);
    __type(value, u64);
} softirq_start SEC(".maps");

SEC("tracepoint/irq/softirq_entry")
int trace_softirq_entry(struct trace_event_raw_softirq *ctx)
{
    u32 vec = ctx->vec;
    u64 ts = bpf_ktime_get_ns();
    bpf_map_update_elem(&softirq_start, &vec, &ts, BPF_ANY);
    return 0;
}

SEC("tracepoint/irq/softirq_exit")
int trace_softirq_exit(struct trace_event_raw_softirq *ctx)
{
    u32 vec = ctx->vec;
    u64 *start = bpf_map_lookup_elem(&softirq_start, &vec);
    if (!start || *start == 0)
        return 0;
    
    u64 duration = bpf_ktime_get_ns() - *start;
    *start = 0;
    
    /* Only report long softirqs (> 100 microseconds) */
    if (duration < 100000)
        return 0;
    
    struct softirq_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    e->vec = vec;
    e->cpu = bpf_get_smp_processor_id();
    e->duration_ns = duration;
    
    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 14.5 Using `bpftrace` for Quick Analysis

```bash
# Measure hardirq latency per IRQ number
bpftrace -e '
tracepoint:irq:irq_handler_entry { @start[args->irq] = nsecs; }
tracepoint:irq:irq_handler_exit  {
    $lat = nsecs - @start[args->irq];
    @latency_us = hist($lat / 1000);
    delete(@start[args->irq]);
}'

# Count softirq invocations per type per second
bpftrace -e '
tracepoint:irq:softirq_entry { @[args->vec] = count(); }
interval:s:1 { print(@); clear(@); }'

# Trace the top 10 IRQ handlers by count
bpftrace -e '
tracepoint:irq:irq_handler_entry { @[args->name] = count(); }
END { print(@, 10); }'

# Detect interrupt storms: IRQs > 10000/sec
bpftrace -e '
tracepoint:irq:irq_handler_entry { @count++; }
interval:s:1 {
    if (@count > 10000) { printf("STORM: %d IRQs/sec\n", @count); }
    clear(@count);
}'
```

### 14.6 eBPF with `libbpf` — Userspace Loader (C)

```c
/* loader.c */
#include <stdio.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include "softirq_tracker.skel.h"  /* Auto-generated by bpftool */

static volatile bool running = true;

static void handle_softirq_event(void *ctx, void *data, size_t size)
{
    struct softirq_event *e = data;
    
    static const char *softirq_names[] = {
        "HI", "TIMER", "NET_TX", "NET_RX", "BLOCK",
        "IRQ_POLL", "TASKLET", "SCHED", "HRTIMER", "RCU"
    };
    
    printf("CPU%u: %s softirq took %.3f ms\n",
           e->cpu,
           e->vec < 10 ? softirq_names[e->vec] : "UNKNOWN",
           e->duration_ns / 1e6);
}

int main(void)
{
    struct softirq_tracker_bpf *skel;
    struct ring_buffer *rb;
    int err;
    
    /* Load and verify BPF application */
    skel = softirq_tracker_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open BPF skeleton\n");
        return 1;
    }
    
    /* Attach tracepoints */
    err = softirq_tracker_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach: %d\n", err);
        goto cleanup;
    }
    
    /* Set up ring buffer polling */
    rb = ring_buffer__new(bpf_map__fd(skel->maps.events),
                          handle_softirq_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }
    
    printf("Monitoring softirqs... Ctrl-C to stop\n");
    
    while (running) {
        err = ring_buffer__poll(rb, 100 /* timeout ms */);
        if (err < 0 && err != -EINTR)
            break;
    }
    
    ring_buffer__free(rb);
cleanup:
    softirq_tracker_bpf__destroy(skel);
    return err;
}
```

### 14.7 eBPF for Network Path Tracing

```bash
# Trace the full path from NIC interrupt to TCP socket
# Using BCC's trace tool

bpftrace -e '
/* When packet first enters kernel from NIC */
kprobe:napi_gro_receive { @entry[tid] = nsecs; }

/* When packet is delivered to TCP socket */
kprobe:tcp_rcv_established {
    $delta = nsecs - @entry[tid];
    if (@entry[tid] != 0) {
        @rx_latency_us = hist($delta / 1000);
        delete(@entry[tid]);
    }
}'

# Trace NET_RX softirq execution with stack
bpftrace -e '
tracepoint:irq:softirq_entry /args->vec == 3/ {  /* NET_RX = 3 */
    @[kstack] = count();
}
END { print(@); }'
```

---

## 15. C Implementation — Complete Examples

### 15.1 Complete Kernel Module: Interrupt Simulation & Analysis

```c
/* irq_demo.c — Complete kernel module demonstrating all IRQ concepts */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/workqueue.h>
#include <linux/hrtimer.h>
#include <linux/ktime.h>
#include <linux/smp.h>
#include <linux/percpu.h>
#include <linux/seq_file.h>
#include <linux/proc_fs.h>
#include <linux/atomic.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Systems Programmer");
MODULE_DESCRIPTION("IRQ subsystem demonstration module");

/* ============================================================
 * Per-CPU statistics structure
 * ============================================================ */
struct irq_stats {
    unsigned long hardirq_count;
    unsigned long softirq_count;
    unsigned long workqueue_count;
    unsigned long tasklet_count;
    ktime_t total_hardirq_time;
    ktime_t max_hardirq_time;
};

static DEFINE_PER_CPU(struct irq_stats, cpu_irq_stats);

/* ============================================================
 * Workqueue work item
 * ============================================================ */
struct demo_work {
    struct work_struct work;
    int cpu_origin;
    ktime_t enqueue_time;
};

static struct workqueue_struct *demo_wq;

static void demo_work_handler(struct work_struct *work)
{
    struct demo_work *dw = container_of(work, struct demo_work, work);
    struct irq_stats *stats = this_cpu_ptr(&cpu_irq_stats);
    ktime_t latency;
    
    /* This runs in process context — could sleep here */
    latency = ktime_sub(ktime_get(), dw->enqueue_time);
    
    stats->workqueue_count++;
    
    pr_debug("WorkQueue: cpu=%d origin_cpu=%d latency=%lldns\n",
             smp_processor_id(), dw->cpu_origin,
             ktime_to_ns(latency));
    
    kfree(dw);
}

/* ============================================================
 * Tasklet
 * ============================================================ */
static struct tasklet_struct demo_tasklet;
static atomic_t tasklet_pending = ATOMIC_INIT(0);

static void demo_tasklet_handler(struct tasklet_struct *t)
{
    struct irq_stats *stats = this_cpu_ptr(&cpu_irq_stats);
    struct demo_work *dw;
    
    /* Running in softirq context — no sleeping */
    stats->tasklet_count++;
    atomic_dec(&tasklet_pending);
    
    pr_debug("Tasklet: cpu=%d\n", smp_processor_id());
    
    /* Schedule workqueue from softirq context */
    dw = kmalloc(sizeof(*dw), GFP_ATOMIC);
    if (dw) {
        dw->cpu_origin = smp_processor_id();
        dw->enqueue_time = ktime_get();
        INIT_WORK(&dw->work, demo_work_handler);
        queue_work(demo_wq, &dw->work);
    }
}

/* ============================================================
 * Simulated "softirq" via hrtimer
 * High-resolution timer fires periodically, simulating IRQ
 * ============================================================ */
static struct hrtimer demo_timer;
static atomic64_t timer_fires = ATOMIC64_INIT(0);

static enum hrtimer_restart timer_callback(struct hrtimer *timer)
{
    struct irq_stats *stats = this_cpu_ptr(&cpu_irq_stats);
    ktime_t start = ktime_get();
    ktime_t elapsed;
    
    /* Simulate hardirq work (minimal) */
    stats->hardirq_count++;
    atomic64_inc(&timer_fires);
    
    /* Schedule tasklet (bottom half) */
    if (atomic_inc_return(&tasklet_pending) == 1) {
        tasklet_schedule(&demo_tasklet);
        stats->softirq_count++;
    } else {
        atomic_dec(&tasklet_pending);
    }
    
    /* Measure our own execution time */
    elapsed = ktime_sub(ktime_get(), start);
    stats->total_hardirq_time = ktime_add(stats->total_hardirq_time, elapsed);
    if (ktime_compare(elapsed, stats->max_hardirq_time) > 0)
        stats->max_hardirq_time = elapsed;
    
    /* Rearm timer: fire every 1ms */
    hrtimer_forward_now(timer, ms_to_ktime(1));
    return HRTIMER_RESTART;
}

/* ============================================================
 * Procfs interface for statistics
 * ============================================================ */
static int irq_demo_show(struct seq_file *m, void *v)
{
    int cpu;
    
    seq_printf(m, "%-8s %-12s %-12s %-12s %-12s %-16s %-16s\n",
               "CPU", "hardirqs", "softirqs", "tasklets",
               "workqueues", "avg_hard_ns", "max_hard_ns");
    
    for_each_online_cpu(cpu) {
        struct irq_stats *s = per_cpu_ptr(&cpu_irq_stats, cpu);
        unsigned long avg_ns = 0;
        
        if (s->hardirq_count > 0)
            avg_ns = ktime_to_ns(s->total_hardirq_time) / s->hardirq_count;
        
        seq_printf(m, "%-8d %-12lu %-12lu %-12lu %-12lu %-16lu %-16lld\n",
                   cpu,
                   s->hardirq_count,
                   s->softirq_count,
                   s->tasklet_count,
                   s->workqueue_count,
                   avg_ns,
                   ktime_to_ns(s->max_hardirq_time));
    }
    
    seq_printf(m, "\nTotal timer fires: %lld\n",
               atomic64_read(&timer_fires));
    
    return 0;
}

static int irq_demo_open(struct inode *inode, struct file *file)
{
    return single_open(file, irq_demo_show, NULL);
}

static const struct proc_ops irq_demo_ops = {
    .proc_open    = irq_demo_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static struct proc_dir_entry *proc_entry;

/* ============================================================
 * Module init/exit
 * ============================================================ */
static int __init irq_demo_init(void)
{
    int cpu;
    
    pr_info("IRQ Demo: initializing\n");
    
    /* Zero per-CPU stats */
    for_each_possible_cpu(cpu)
        memset(per_cpu_ptr(&cpu_irq_stats, cpu), 0, sizeof(struct irq_stats));
    
    /* Create workqueue */
    demo_wq = alloc_workqueue("irq_demo_wq",
                               WQ_UNBOUND | WQ_MEM_RECLAIM, 0);
    if (!demo_wq) {
        pr_err("IRQ Demo: failed to create workqueue\n");
        return -ENOMEM;
    }
    
    /* Initialize tasklet */
    tasklet_setup(&demo_tasklet, demo_tasklet_handler);
    
    /* Create proc entry */
    proc_entry = proc_create("irq_demo", 0444, NULL, &irq_demo_ops);
    if (!proc_entry) {
        pr_warn("IRQ Demo: failed to create proc entry\n");
    }
    
    /* Start hrtimer */
    hrtimer_init(&demo_timer, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
    demo_timer.function = timer_callback;
    hrtimer_start(&demo_timer, ms_to_ktime(1), HRTIMER_MODE_REL);
    
    pr_info("IRQ Demo: started. Check /proc/irq_demo\n");
    return 0;
}

static void __exit irq_demo_exit(void)
{
    pr_info("IRQ Demo: shutting down\n");
    
    /* Stop timer first */
    hrtimer_cancel(&demo_timer);
    
    /* Kill tasklet (waits for any running tasklet) */
    tasklet_kill(&demo_tasklet);
    
    /* Drain workqueue */
    drain_workqueue(demo_wq);
    destroy_workqueue(demo_wq);
    
    /* Remove proc entry */
    if (proc_entry)
        proc_remove(proc_entry);
    
    pr_info("IRQ Demo: done\n");
}

module_init(irq_demo_init);
module_exit(irq_demo_exit);
```

### 15.2 Makefile for the Kernel Module

```makefile
# Makefile
obj-m += irq_demo.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod irq_demo.ko

uninstall:
	sudo rmmod irq_demo

stats:
	cat /proc/irq_demo
```

### 15.3 Userspace IRQ Simulation with `signalfd` (C)

For understanding the conceptual model in userspace:

```c
/* irq_sim_userspace.c — IRQ concept simulation in userspace */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <pthread.h>
#include <stdatomic.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <sys/eventfd.h>
#include <poll.h>

/* ============================================================
 * Simulated hardware interrupt line
 * ============================================================ */
typedef struct {
    int efd;                        /* eventfd: simulates IRQ line */
    atomic_int pending_softirq;     /* softirq pending bitmap */
    pthread_t softirq_thread;       /* ksoftirqd analog */
    pthread_mutex_t bh_lock;        /* BH disable analog */
    pthread_cond_t bh_cond;
    
    /* Statistics */
    atomic_long hardirq_count;
    atomic_long softirq_count;
} irq_subsystem_t;

/* Simulated softirq types */
typedef enum {
    SOFTIRQ_TIMER   = (1 << 0),
    SOFTIRQ_NET_RX  = (1 << 1),
    SOFTIRQ_NET_TX  = (1 << 2),
    SOFTIRQ_TASKLET = (1 << 3),
} softirq_type_t;

/* ============================================================
 * Bottom half processor (ksoftirqd analog)
 * ============================================================ */
static void process_softirqs(irq_subsystem_t *sys)
{
    int pending = atomic_exchange(&sys->pending_softirq, 0);
    
    if (pending & SOFTIRQ_NET_RX) {
        atomic_fetch_add(&sys->softirq_count, 1);
        printf("  [NET_RX softirq] Processing received packets\n");
        usleep(100);  /* simulate work */
    }
    if (pending & SOFTIRQ_NET_TX) {
        atomic_fetch_add(&sys->softirq_count, 1);
        printf("  [NET_TX softirq] Completing transmitted packets\n");
        usleep(50);
    }
    if (pending & SOFTIRQ_TIMER) {
        atomic_fetch_add(&sys->softirq_count, 1);
        printf("  [TIMER softirq] Processing expired timers\n");
        usleep(10);
    }
    if (pending & SOFTIRQ_TASKLET) {
        atomic_fetch_add(&sys->softirq_count, 1);
        printf("  [TASKLET softirq] Running tasklet handlers\n");
        usleep(20);
    }
}

/* ============================================================
 * Hardirq handler (runs when interrupt fires)
 * ============================================================ */
static void handle_hardirq(irq_subsystem_t *sys, int device_id)
{
    /* Interrupts are "disabled" during hardirq (atomicity) */
    atomic_fetch_add(&sys->hardirq_count, 1);
    
    printf("[hardirq] Device %d fired! Acknowledging hardware...\n", device_id);
    
    /* Schedule appropriate softirq */
    switch (device_id) {
        case 0:  /* NIC */
            atomic_fetch_or(&sys->pending_softirq, SOFTIRQ_NET_RX);
            break;
        case 1:  /* Timer */
            atomic_fetch_or(&sys->pending_softirq, SOFTIRQ_TIMER);
            break;
        case 2:  /* Block device */
            atomic_fetch_or(&sys->pending_softirq, SOFTIRQ_TASKLET);
            break;
    }
    
    /* Signal ksoftirqd that work is pending */
    pthread_cond_signal(&sys->bh_cond);
}

/* ============================================================
 * ksoftirqd thread
 * ============================================================ */
static void *ksoftirqd_thread(void *arg)
{
    irq_subsystem_t *sys = arg;
    
    while (1) {
        pthread_mutex_lock(&sys->bh_lock);
        
        /* Wait for pending softirqs */
        while (atomic_load(&sys->pending_softirq) == 0)
            pthread_cond_wait(&sys->bh_cond, &sys->bh_lock);
        
        pthread_mutex_unlock(&sys->bh_lock);
        
        /* Process pending softirqs */
        process_softirqs(sys);
    }
    
    return NULL;
}

/* ============================================================
 * Device simulator thread
 * ============================================================ */
static void *device_simulator(void *arg)
{
    int efd = *(int *)arg;
    
    srand(time(NULL));
    
    while (1) {
        /* Random delay between 50-200ms */
        usleep(50000 + (rand() % 150000));
        
        /* Trigger an interrupt */
        int device = rand() % 3;
        uint64_t val = (uint64_t)device + 1;
        write(efd, &val, sizeof(val));
    }
    
    return NULL;
}

/* ============================================================
 * IRQ dispatcher (CPU interrupt handling loop)
 * ============================================================ */
int main(void)
{
    irq_subsystem_t sys = {0};
    pthread_t sim_thread;
    
    /* Initialize */
    sys.efd = eventfd(0, EFD_NONBLOCK);
    pthread_mutex_init(&sys.bh_lock, NULL);
    pthread_cond_init(&sys.bh_cond, NULL);
    atomic_init(&sys.pending_softirq, 0);
    atomic_init(&sys.hardirq_count, 0);
    atomic_init(&sys.softirq_count, 0);
    
    /* Start ksoftirqd analog */
    pthread_create(&sys.softirq_thread, NULL, ksoftirqd_thread, &sys);
    
    /* Start device simulator */
    pthread_create(&sim_thread, NULL, device_simulator, &sys.efd);
    
    printf("IRQ subsystem simulation running...\n\n");
    
    struct pollfd pfd = { .fd = sys.efd, .events = POLLIN };
    
    /* Main interrupt dispatch loop */
    for (int i = 0; i < 20; i++) {
        if (poll(&pfd, 1, 500) > 0) {
            uint64_t val;
            read(sys.efd, &val, sizeof(val));
            handle_hardirq(&sys, (int)(val - 1));
        }
        
        /* After processing hardirq, check for pending softirqs */
        if (atomic_load(&sys.pending_softirq))
            pthread_cond_signal(&sys.bh_cond);
    }
    
    sleep(1);  /* Let pending work complete */
    
    printf("\n=== Statistics ===\n");
    printf("Hardirqs processed: %ld\n", atomic_load(&sys.hardirq_count));
    printf("Softirqs processed: %ld\n", atomic_load(&sys.softirq_count));
    
    return 0;
}
```

---

## 16. Rust Implementation — Kernel & Userspace

### 16.1 Rust in the Linux Kernel (rust-for-linux)

The `rust-for-linux` project (merged in kernel 6.1+) allows writing kernel modules in Rust. Here's how IRQ handling looks:

```rust
// irq_demo.rs — Rust kernel module with IRQ handling
// Requires: CONFIG_RUST=y in kernel config

use kernel::prelude::*;
use kernel::irq::{self, IrqHandler, IrqReturn};
use kernel::sync::{Arc, Mutex};
use kernel::workqueue::{self, Work, WorkQueue};
use kernel::task::Task;

module! {
    type: IrqDemoModule,
    name: "irq_demo_rust",
    author: "Systems Programmer",
    description: "IRQ demo in Rust",
    license: "GPL",
}

/// Per-device state
struct MyDevice {
    count: u64,
    data: Vec<u8>,
}

/// Workqueue item for deferred processing
struct RxWork {
    work: Work<RxWork>,
    packet_data: Vec<u8>,
    device: Arc<Mutex<MyDevice>>,
}

impl workqueue::WorkItem for RxWork {
    type Pointer = Arc<RxWork>;
    
    fn run(this: Arc<RxWork>) {
        // Process packet — process context, CAN sleep (in theory)
        // In Rust kernel code, sleeping APIs are still being developed
        
        let mut dev = this.device.lock();
        dev.count += 1;
        pr_info!("Processed packet #{}, data len={}\n",
                 dev.count, this.packet_data.len());
    }
}

/// IRQ handler
struct MyIrqHandler {
    device: Arc<Mutex<MyDevice>>,
    wq: Arc<WorkQueue>,
}

impl IrqHandler for MyIrqHandler {
    fn handle_irq(&self) -> IrqReturn {
        // Acknowledge hardware (minimal work)
        // In real code: read_volatile from MMIO
        
        // Schedule deferred work
        // (simplified — actual API still evolving)
        pr_debug!("IRQ fired!\n");
        
        IrqReturn::Handled
    }
}

struct IrqDemoModule {
    _irq: irq::Registration<MyIrqHandler>,
}

impl kernel::Module for IrqDemoModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("IRQ Demo Rust: loading\n");
        
        let device = Arc::try_new(Mutex::new(MyDevice {
            count: 0,
            data: Vec::new(),
        }))?;
        
        let wq = WorkQueue::try_new(c_str!("irq_demo_rust_wq"), 0)?;
        
        let handler = MyIrqHandler {
            device,
            wq: Arc::try_new(wq)?,
        };
        
        // Register IRQ handler
        // (IRQ number would come from device tree / PCI in real code)
        let irq_reg = irq::request_irq(
            16,          // IRQ number
            handler,
            irq::flags::SHARED,
            c_str!("irq_demo_rust"),
        )?;
        
        Ok(IrqDemoModule { _irq: irq_reg })
    }
}

impl Drop for IrqDemoModule {
    fn drop(&mut self) {
        pr_info!("IRQ Demo Rust: unloading\n");
        // _irq dropped here: free_irq called automatically
    }
}
```

### 16.2 Userspace IRQ Simulation in Rust — Complete Implementation

```rust
// irq_simulation/src/main.rs
// Cargo.toml: [dependencies] (no external deps needed)

use std::collections::VecDeque;
use std::sync::atomic::{AtomicI32, AtomicU64, Ordering};
use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::{Duration, Instant};

// ================================================================
// IRQ Subsystem Types
// ================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum SoftirqType {
    Hi = 0,
    Timer = 1,
    NetTx = 2,
    NetRx = 3,
    Block = 4,
    Tasklet = 5,
    Sched = 6,
    Hrtimer = 7,
    Rcu = 8,
}

impl SoftirqType {
    pub fn name(&self) -> &'static str {
        match self {
            Self::Hi => "HI",
            Self::Timer => "TIMER",
            Self::NetTx => "NET_TX",
            Self::NetRx => "NET_RX",
            Self::Block => "BLOCK",
            Self::Tasklet => "TASKLET",
            Self::Sched => "SCHED",
            Self::Hrtimer => "HRTIMER",
            Self::Rcu => "RCU",
        }
    }
    
    pub fn bit(&self) -> u32 {
        1 << (*self as u8)
    }
}

#[derive(Debug)]
pub enum IrqReturn {
    None,    // Not our interrupt
    Handled, // We handled it
    WakeThread, // Wake threaded handler
}

// ================================================================
// Statistics
// ================================================================

#[derive(Debug, Default)]
pub struct CpuStats {
    pub hardirq_count: AtomicU64,
    pub softirq_counts: [AtomicU64; 9],
    pub total_hardirq_ns: AtomicU64,
    pub max_hardirq_ns: AtomicU64,
}

impl CpuStats {
    pub fn record_hardirq(&self, duration_ns: u64) {
        self.hardirq_count.fetch_add(1, Ordering::Relaxed);
        self.total_hardirq_ns.fetch_add(duration_ns, Ordering::Relaxed);
        
        // Update max (non-atomic CAS loop)
        let mut current_max = self.max_hardirq_ns.load(Ordering::Relaxed);
        while duration_ns > current_max {
            match self.max_hardirq_ns.compare_exchange(
                current_max, duration_ns,
                Ordering::SeqCst, Ordering::Relaxed
            ) {
                Ok(_) => break,
                Err(actual) => current_max = actual,
            }
        }
    }
    
    pub fn avg_hardirq_ns(&self) -> u64 {
        let count = self.hardirq_count.load(Ordering::Relaxed);
        if count == 0 {
            return 0;
        }
        self.total_hardirq_ns.load(Ordering::Relaxed) / count
    }
}

// ================================================================
// Softirq Subsystem
// ================================================================

type SoftirqHandler = Box<dyn Fn() + Send + Sync>;

pub struct SoftirqVec {
    handlers: [Option<SoftirqHandler>; 9],
}

impl SoftirqVec {
    pub fn new() -> Self {
        // Can't derive Default for arrays of non-Copy Option<Box<dyn Fn>>
        Self {
            handlers: std::array::from_fn(|_| None),
        }
    }
    
    pub fn register(&mut self, irq: SoftirqType, handler: SoftirqHandler) {
        self.handlers[irq as usize] = Some(handler);
    }
    
    /// Process all pending softirqs given the pending bitmask
    pub fn process_pending(&self, pending: u32) {
        // Process in priority order (bit 0 first = HI_SOFTIRQ)
        for i in 0..9u8 {
            if pending & (1 << i) != 0 {
                if let Some(handler) = &self.handlers[i as usize] {
                    handler();
                }
            }
        }
    }
}

// ================================================================
// IRQ Controller (simulates Linux IRQ subsystem)
// ================================================================

pub struct IrqController {
    /// Pending softirq bitmask (per-CPU in real kernel; single for demo)
    pending_softirqs: AtomicI32,
    
    /// Condition variable for ksoftirqd
    softirq_signal: Arc<(Mutex<bool>, Condvar)>,
    
    /// Global stats
    stats: Arc<CpuStats>,
    
    /// Softirq handlers
    softirq_vec: Arc<SoftirqVec>,
    
    /// Workqueue (channel-based)
    work_tx: std::sync::mpsc::SyncSender<WorkItem>,
}

type WorkItem = Box<dyn FnOnce() + Send>;

impl IrqController {
    pub fn new(softirq_vec: Arc<SoftirqVec>) -> (Self, thread::JoinHandle<()>, thread::JoinHandle<()>) {
        let pending_softirqs = AtomicI32::new(0);
        let softirq_signal = Arc::new((Mutex::new(false), Condvar::new()));
        let stats = Arc::new(CpuStats::default());
        let (work_tx, work_rx) = std::sync::mpsc::sync_channel::<WorkItem>(1024);
        
        // Spawn ksoftirqd analog
        let signal_clone = Arc::clone(&softirq_signal);
        let vec_clone = Arc::clone(&softirq_vec);
        let stats_clone = Arc::clone(&stats);
        
        // We need shared pending — use Arc<AtomicI32>
        let pending_arc = Arc::new(AtomicI32::new(0));
        let pending_ksoftirq = Arc::clone(&pending_arc);
        
        let ksoftirqd = thread::Builder::new()
            .name("ksoftirqd/0".into())
            .spawn(move || {
                loop {
                    // Wait for signal
                    let (lock, cvar) = &*signal_clone;
                    let mut signaled = lock.lock().unwrap();
                    while !*signaled {
                        signaled = cvar.wait(signaled).unwrap();
                    }
                    *signaled = false;
                    drop(signaled);
                    
                    // Process pending softirqs
                    let pending = pending_ksoftirq.swap(0, Ordering::AcqRel) as u32;
                    if pending != 0 {
                        println!("  [ksoftirqd] Processing softirqs: 0b{:09b}", pending);
                        vec_clone.process_pending(pending);
                        stats_clone.softirq_counts[0]
                            .fetch_add(pending.count_ones() as u64, Ordering::Relaxed);
                    }
                }
            })
            .unwrap();
        
        // Spawn workqueue worker analog (kworker)
        let kworker = thread::Builder::new()
            .name("kworker/0:1".into())
            .spawn(move || {
                for work in work_rx {
                    work();
                }
            })
            .unwrap();
        
        let ctrl = IrqController {
            pending_softirqs: AtomicI32::new(0), // Will use pending_arc in real impl
            softirq_signal,
            stats,
            softirq_vec,
            work_tx,
        };
        
        // Note: in a full implementation, pending_arc would be shared
        // This demo uses the controller's own AtomicI32
        
        (ctrl, ksoftirqd, kworker)
    }
    
    /// Simulate raising a softirq (like raise_softirq())
    pub fn raise_softirq(&self, irq: SoftirqType) {
        self.pending_softirqs.fetch_or(irq.bit() as i32, Ordering::AcqRel);
        
        let (lock, cvar) = &*self.softirq_signal;
        let mut signaled = lock.lock().unwrap();
        *signaled = true;
        cvar.notify_one();
    }
    
    /// Simulate queuing work to workqueue
    pub fn queue_work(&self, work: WorkItem) {
        let _ = self.work_tx.send(work);
    }
    
    /// Simulate irq_exit() — called after hardirq handler returns
    pub fn irq_exit(&self) {
        let pending = self.pending_softirqs.load(Ordering::Acquire);
        if pending != 0 {
            let (lock, cvar) = &*self.softirq_signal;
            let mut signaled = lock.lock().unwrap();
            *signaled = true;
            cvar.notify_one();
        }
    }
    
    pub fn stats(&self) -> &CpuStats {
        &self.stats
    }
}

// ================================================================
// Device Driver Simulation
// ================================================================

pub struct SimulatedNic {
    irq_number: u32,
    rx_count: AtomicU64,
    tx_count: AtomicU64,
    rx_queue: Arc<Mutex<VecDeque<Vec<u8>>>>,
}

impl SimulatedNic {
    pub fn new(irq: u32) -> Self {
        Self {
            irq_number: irq,
            rx_count: AtomicU64::new(0),
            tx_count: AtomicU64::new(0),
            rx_queue: Arc::new(Mutex::new(VecDeque::new())),
        }
    }
    
    /// Top half: IRQ handler
    /// Returns what work needs deferred
    pub fn handle_irq(&self, controller: &IrqController) -> IrqReturn {
        let start = Instant::now();
        
        // Check interrupt source (simulated)
        let rx_pending = self.rx_count.load(Ordering::Relaxed) % 5 == 0;
        let tx_pending = self.tx_count.load(Ordering::Relaxed) % 7 == 0;
        
        if !rx_pending && !tx_pending {
            return IrqReturn::None;
        }
        
        println!("[hardirq {}] NIC interrupt! RX={} TX={}",
                 self.irq_number, rx_pending, tx_pending);
        
        // Acknowledge hardware (minimal work)
        if rx_pending {
            // Push fake packet to rx queue
            self.rx_queue.lock().unwrap()
                .push_back(vec![0x45, 0x00, 0x00, 0x28, 0x00, 0x01]);
            
            // Schedule NET_RX_SOFTIRQ
            controller.raise_softirq(SoftirqType::NetRx);
        }
        
        if tx_pending {
            controller.raise_softirq(SoftirqType::NetTx);
        }
        
        let elapsed = start.elapsed().as_nanos() as u64;
        controller.stats().record_hardirq(elapsed);
        
        // irq_exit equivalent — check and trigger softirqs
        controller.irq_exit();
        
        IrqReturn::Handled
    }
}

// ================================================================
// Main: Wire it all together
// ================================================================

fn main() {
    println!("=== Linux IRQ Subsystem Simulation (Rust) ===\n");
    
    // Build softirq vector with handlers
    let mut softirq_vec = SoftirqVec::new();
    
    softirq_vec.register(SoftirqType::NetRx, Box::new(|| {
        println!("  [NET_RX softirq] Processing incoming packets");
        thread::sleep(Duration::from_micros(50));
    }));
    
    softirq_vec.register(SoftirqType::NetTx, Box::new(|| {
        println!("  [NET_TX softirq] Completing TX descriptors");
        thread::sleep(Duration::from_micros(20));
    }));
    
    softirq_vec.register(SoftirqType::Timer, Box::new(|| {
        println!("  [TIMER softirq] Firing expired timers");
        thread::sleep(Duration::from_micros(10));
    }));
    
    softirq_vec.register(SoftirqType::Rcu, Box::new(|| {
        println!("  [RCU softirq] Processing RCU callbacks");
        thread::sleep(Duration::from_micros(5));
    }));
    
    let softirq_vec = Arc::new(softirq_vec);
    
    // Create IRQ controller (spawns ksoftirqd and kworker)
    let (controller, _ksoftirqd, _kworker) =
        IrqController::new(Arc::clone(&softirq_vec));
    let controller = Arc::new(controller);
    
    // Create simulated NIC
    let nic = Arc::new(SimulatedNic::new(24));
    
    // Simulate interrupt firing from a hardware timer
    let nic_clone = Arc::clone(&nic);
    let ctrl_clone = Arc::clone(&controller);
    
    let irq_simulator = thread::spawn(move || {
        let mut rng_state: u64 = 12345;  // Simple LCG RNG
        
        for tick in 0..15 {
            // Simulate 1-5ms between interrupts
            rng_state = rng_state.wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            let delay_ms = (rng_state >> 62) + 1;  // 1-4ms
            
            thread::sleep(Duration::from_millis(delay_ms));
            
            println!("\n[tick {}] Hardware IRQ fires!", tick);
            
            // Update counters to vary IRQ behavior
            nic_clone.rx_count.fetch_add(1, Ordering::Relaxed);
            nic_clone.tx_count.fetch_add(1, Ordering::Relaxed);
            
            match nic_clone.handle_irq(&ctrl_clone) {
                IrqReturn::Handled => println!("[tick {}] IRQ handled", tick),
                IrqReturn::None => println!("[tick {}] IRQ not ours (spurious)", tick),
                IrqReturn::WakeThread => println!("[tick {}] Waking threaded handler", tick),
            }
            
            // Occasionally fire timer softirq
            if tick % 4 == 0 {
                ctrl_clone.raise_softirq(SoftirqType::Timer);
                ctrl_clone.irq_exit();
            }
            
            // Occasionally fire RCU
            if tick % 5 == 0 {
                ctrl_clone.raise_softirq(SoftirqType::Rcu);
                ctrl_clone.irq_exit();
            }
        }
    });
    
    irq_simulator.join().unwrap();
    
    // Let pending work drain
    thread::sleep(Duration::from_millis(100));
    
    // Print statistics
    println!("\n=== Interrupt Statistics ===");
    let stats = controller.stats();
    println!("Total hardirqs:    {}", stats.hardirq_count.load(Ordering::Relaxed));
    println!("Avg hardirq time:  {} ns", stats.avg_hardirq_ns());
    println!("Max hardirq time:  {} ns", stats.max_hardirq_ns.load(Ordering::Relaxed));
    println!("Softirq batches:   {}", stats.softirq_counts[0].load(Ordering::Relaxed));
}
```

### 16.3 Rust: Lock-Free IRQ-Safe Ring Buffer

A pattern commonly needed for IRQ → process data transfer:

```rust
// irq_ring_buffer.rs
// Lock-free SPSC ring buffer safe for use between IRQ handler and process context
// Producer: IRQ handler (one producer)
// Consumer: kernel thread / workqueue (one consumer)

use std::sync::atomic::{AtomicUsize, Ordering, fence};
use std::mem::MaybeUninit;
use std::cell::UnsafeCell;

const RING_SIZE: usize = 1024;  // Must be power of 2

pub struct IrqRingBuffer<T> {
    buffer: Box<[UnsafeCell<MaybeUninit<T>>; RING_SIZE]>,
    head: AtomicUsize,  // Written by producer (IRQ)
    tail: AtomicUsize,  // Written by consumer (process)
}

// Safety: Access is protected by head/tail protocol
unsafe impl<T: Send> Send for IrqRingBuffer<T> {}
unsafe impl<T: Send> Sync for IrqRingBuffer<T> {}

impl<T> IrqRingBuffer<T> {
    pub fn new() -> Self {
        Self {
            // SAFETY: MaybeUninit doesn't require initialization
            buffer: Box::new(std::array::from_fn(|_| UnsafeCell::new(MaybeUninit::uninit()))),
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }
    
    /// Push item — called from IRQ handler (producer)
    /// Returns false if buffer is full
    /// 
    /// # Safety  
    /// Must be called from a single producer (one IRQ handler)
    pub fn push(&self, item: T) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        
        // Check if full
        if head.wrapping_sub(tail) >= RING_SIZE {
            return false;
        }
        
        let slot = head & (RING_SIZE - 1);
        
        // Write item
        // SAFETY: slot is unique to this producer at this moment
        unsafe {
            (*self.buffer[slot].get()).write(item);
        }
        
        // Publish — Release: ensures write above is visible before head update
        fence(Ordering::Release);
        self.head.store(head.wrapping_add(1), Ordering::Release);
        
        true
    }
    
    /// Pop item — called from process context (consumer)
    /// Returns None if buffer is empty
    ///
    /// # Safety
    /// Must be called from a single consumer
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);  // Acquire: see producer's writes
        
        if head == tail {
            return None;  // Empty
        }
        
        let slot = tail & (RING_SIZE - 1);
        
        // Read item
        // SAFETY: slot is ready (head > tail confirmed above)
        let item = unsafe {
            (*self.buffer[slot].get()).assume_init_read()
        };
        
        // Advance tail — Release: ensures read above completes before advancing
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        
        Some(item)
    }
    
    pub fn len(&self) -> usize {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Relaxed);
        head.wrapping_sub(tail)
    }
    
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
    
    pub fn is_full(&self) -> bool {
        self.len() >= RING_SIZE
    }
}

// Usage example
#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::thread;
    
    #[test]
    fn test_irq_ringbuf_concurrent() {
        let buf = Arc::new(IrqRingBuffer::<u64>::new());
        let buf_producer = Arc::clone(&buf);
        let buf_consumer = Arc::clone(&buf);
        
        // Producer thread (simulates IRQ handler)
        let producer = thread::spawn(move || {
            for i in 0u64..10000 {
                while !buf_producer.push(i) {
                    std::hint::spin_loop();
                }
            }
        });
        
        // Consumer thread (simulates ksoftirqd / workqueue)
        let consumer = thread::spawn(move || {
            let mut received = 0u64;
            let mut expected = 0u64;
            
            while received < 10000 {
                if let Some(val) = buf_consumer.pop() {
                    assert_eq!(val, expected, "Out of order! Got {} expected {}", val, expected);
                    expected += 1;
                    received += 1;
                } else {
                    std::hint::spin_loop();
                }
            }
        });
        
        producer.join().unwrap();
        consumer.join().unwrap();
    }
}
```

### 16.4 Rust: eBPF Program using Aya Framework

```rust
// aya-based eBPF program for interrupt tracing
// Cargo.toml:
// [dependencies]
// aya = "0.12"
// aya-log = "0.2"
// anyhow = "1"
// tokio = { version = "1", features = ["full"] }
// [build-dependencies]
// aya-build = "0.1"

// src/bpf/irq_tracer.bpf.rs (compiled separately as eBPF bytecode)
// This would use aya-bpf crate in a separate build target

// src/main.rs — userspace loader using Aya
use aya::{
    include_bytes_aligned,
    maps::{HashMap, PerCpuArray, RingBuf},
    programs::TracePoint,
    Bpf,
};
use aya_log::BpfLogger;
use anyhow::Context;
use std::time::Duration;
use tokio::signal;

#[derive(Debug, Clone, Copy)]
#[repr(C)]
struct SoftirqEvent {
    vec: u32,
    cpu: u32,
    duration_ns: u64,
    pid: u32,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load BPF bytecode (compiled separately)
    // In real usage: include_bytes_aligned!("../../target/bpfel-unknown-none/release/irq_tracer")
    let mut bpf = Bpf::load_file("irq_tracer.bpf.o")?;
    
    // Initialize logging
    BpfLogger::init(&mut bpf)?;
    
    // Attach to softirq_entry tracepoint
    let entry_prog: &mut TracePoint = bpf
        .program_mut("trace_softirq_entry")
        .context("entry program not found")?
        .try_into()?;
    entry_prog.load()?;
    entry_prog.attach("irq", "softirq_entry")?;
    
    // Attach to softirq_exit tracepoint
    let exit_prog: &mut TracePoint = bpf
        .program_mut("trace_softirq_exit")
        .context("exit program not found")?
        .try_into()?;
    exit_prog.load()?;
    exit_prog.attach("irq", "softirq_exit")?;
    
    // Read from ring buffer
    let mut ring_buf = RingBuf::try_from(bpf.map_mut("events")?)?;
    
    let softirq_names = ["HI", "TIMER", "NET_TX", "NET_RX", "BLOCK",
                          "IRQ_POLL", "TASKLET", "SCHED", "HRTIMER", "RCU"];
    
    println!("Tracing softirqs... Press Ctrl-C to stop.\n");
    println!("{:<8} {:<4} {:<12} {:<10}", "TYPE", "CPU", "DURATION_US", "PID");
    
    loop {
        tokio::select! {
            _ = signal::ctrl_c() => break,
            _ = tokio::time::sleep(Duration::from_millis(10)) => {
                // Poll ring buffer
                while let Some(item) = ring_buf.next() {
                    let event = unsafe {
                        &*(item.as_ptr() as *const SoftirqEvent)
                    };
                    
                    let name = softirq_names
                        .get(event.vec as usize)
                        .unwrap_or(&"UNKNOWN");
                    
                    println!("{:<8} {:<4} {:<12.3} {:<10}",
                             name,
                             event.cpu,
                             event.duration_ns as f64 / 1000.0,
                             event.pid);
                }
            }
        }
    }
    
    println!("\nDone.");
    Ok(())
}
```

---

## 17. Debugging, Profiling & Observability Tools

### 17.1 `/proc/interrupts` — Real-Time IRQ Counts

```bash
# Watch interrupt counts change in real-time
watch -n 0.5 'cat /proc/interrupts'

# Find the IRQ number for a specific device
grep "eth0\|nvme\|ahci" /proc/interrupts

# Check for spurious interrupts (ERR column)
cat /proc/interrupts | awk '$NF ~ /ERR/ || $NF ~ /MIS/'
```

### 17.2 `/proc/softirqs` — Softirq Statistics

```bash
# Snapshot softirq counts
cat /proc/softirqs

# Monitor NET_RX softirq load over time
watch -n 1 'awk "/NET_RX/{print}" /proc/softirqs'
```

### 17.3 `ftrace` — Kernel Function Tracing

```bash
# Trace irq_handler_entry and irq_handler_exit
cd /sys/kernel/debug/tracing

echo 0 > tracing_on
echo irq_handler_entry irq_handler_exit > set_event
echo 1 > tracing_on
sleep 5
echo 0 > tracing_on
cat trace

# Output shows:
# irq-23      [001] d..1  1234.567890: irq_handler_entry: irq=24 name=eth0
# irq-23      [001] d..1  1234.567892: irq_handler_exit: irq=24 ret=handled

# Trace softirqs
echo softirq_entry softirq_exit > set_event
```

### 17.4 `perf` — Performance Counters

```bash
# Count all interrupts for 10 seconds
perf stat -e 'irq:irq_handler_entry' sleep 10

# Show interrupt distribution
perf record -e 'irq:irq_handler_entry' -a sleep 10
perf report

# Measure IRQ handler duration with perf script
perf record -e 'irq:irq_handler_entry,irq:irq_handler_exit' -a sleep 5
perf script | awk '
/irq_handler_entry/ { start[$4] = $5; name[$4] = $NF }
/irq_handler_exit/  { if (start[$4]) {
    delta = $5 - start[$4]
    printf "IRQ %s: %.3f us\n", name[$4], delta * 1000000
}}'
```

### 17.5 `irqtop` — IRQ Activity Monitor

```bash
# Install irqtop (part of util-linux on some distros)
irqtop

# Or use this one-liner:
watch -n 1 'cat /proc/interrupts | sort -k2 -n -r | head -20'
```

### 17.6 `hardirqs` and `softirqs` BCC Tools

```bash
# Install BCC tools
apt-get install bpfcc-tools

# Summarize hardirq handler latencies as histogram
hardirqs-bpfcc -d 10    # 10 second duration
# Output:
# Tracing hard irq event time... Hit Ctrl-C to end.
#
# irq = 24 (eth0)
# usecs : count     distribution
#  0-1   : 1234     |********************|
#  2-3   : 456      |*******             |
#  4-7   : 78       |*                   |
#  8-15  : 3        |                    |

# Summarize softirq handler latencies
softirqs-bpfcc -d 10
```

### 17.7 `vmstat` — System-Level View

```bash
# 'in' column: interrupts per second
# 'cs' column: context switches per second
vmstat 1
```

### 17.8 Detecting IRQ Storms

```bash
# Script to detect interrupt storms
#!/bin/bash
THRESHOLD=50000  # IRQs per second
PREV=$(grep -o '[0-9]*' /proc/interrupts | paste -sd+ | bc)

while true; do
    sleep 1
    CURR=$(grep -o '[0-9]*' /proc/interrupts | paste -sd+ | bc)
    RATE=$((CURR - PREV))
    
    if [ $RATE -gt $THRESHOLD ]; then
        echo "IRQ STORM DETECTED: ${RATE} IRQs/sec"
        cat /proc/interrupts
    fi
    
    PREV=$CURR
done
```

---

## 18. Common Pitfalls & Anti-Patterns

### 18.1 Sleeping in Interrupt Context

```c
/* WRONG — will cause kernel panic */
static irqreturn_t bad_handler(int irq, void *dev_id)
{
    msleep(10);           /* BUG: sleep in interrupt context */
    mutex_lock(&my_mutex); /* BUG: can sleep */
    kmalloc(size, GFP_KERNEL); /* BUG: can sleep */
    return IRQ_HANDLED;
}

/* CORRECT */
static irqreturn_t good_handler(int irq, void *dev_id)
{
    /* Schedule work to do the sleeping operations */
    schedule_work(&my_work);  /* OK: just queues work */
    return IRQ_HANDLED;
}
```

### 18.2 Forgetting IRQ-Safe Locking

```c
/* WRONG — potential deadlock */
spinlock_t data_lock;

void process_context_func(void)
{
    spin_lock(&data_lock);  /* Doesn't disable IRQs! */
    /* If IRQ fires here and also grabs data_lock: DEADLOCK */
    access_shared_data();
    spin_unlock(&data_lock);
}

irqreturn_t irq_handler(int irq, void *dev_id)
{
    spin_lock(&data_lock);  /* Will deadlock on same CPU */
    access_shared_data();
    spin_unlock(&data_lock);
    return IRQ_HANDLED;
}

/* CORRECT */
void process_context_func(void)
{
    unsigned long flags;
    spin_lock_irqsave(&data_lock, flags);   /* Disables IRQs */
    access_shared_data();
    spin_unlock_irqrestore(&data_lock, flags);
}
```

### 18.3 Not Checking Interrupt Ownership

```c
/* WRONG — for shared IRQ lines */
static irqreturn_t bad_shared_handler(int irq, void *dev_id)
{
    /* Assumes this IRQ is always ours */
    process_data();       /* May process garbage data from other device */
    return IRQ_HANDLED;   /* Falsely claims we handled it */
}

/* CORRECT */
static irqreturn_t good_shared_handler(int irq, void *dev_id)
{
    struct my_device *dev = dev_id;
    
    /* Check hardware register to verify interrupt is ours */
    if (!(readl(dev->base + STATUS_REG) & MY_IRQ_FLAG))
        return IRQ_NONE;  /* Not ours! */
    
    /* Acknowledge and process */
    writel(MY_IRQ_FLAG, dev->base + ACK_REG);
    process_data(dev);
    
    return IRQ_HANDLED;
}
```

### 18.4 Not Freeing IRQ Before Device Cleanup

```c
/* WRONG — use-after-free: IRQ can fire after device is freed */
static void bad_remove(struct platform_device *pdev)
{
    struct my_device *dev = platform_get_drvdata(pdev);
    kfree(dev);           /* BUG: IRQ handler might still be running! */
    free_irq(dev->irq, dev);  /* Too late */
}

/* CORRECT */
static void good_remove(struct platform_device *pdev)
{
    struct my_device *dev = platform_get_drvdata(pdev);
    
    /* Free IRQ FIRST — this waits for any running handler to complete */
    free_irq(dev->irq, dev);
    
    /* Kill tasklet — waits for running tasklet */
    tasklet_kill(&dev->tasklet);
    
    /* Cancel and wait for work */
    cancel_work_sync(&dev->work);
    
    /* Now safe to free */
    kfree(dev);
}
```

### 18.5 Doing Too Much in the Top Half

```c
/* WRONG — blocking the IRQ line too long */
static irqreturn_t slow_handler(int irq, void *dev_id)
{
    struct sk_buff *skb;
    
    /* DMA copy + allocation in hardirq context — too slow */
    skb = alloc_skb(MAX_PACKET, GFP_ATOMIC);
    dma_sync_single_for_cpu(...);
    memcpy(skb->data, dma_buffer, MAX_PACKET);
    netif_rx(skb);
    
    return IRQ_HANDLED;
}

/* CORRECT — use NAPI or schedule bottom half */
static irqreturn_t fast_handler(int irq, void *dev_id)
{
    struct my_nic *nic = dev_id;
    
    /* Just acknowledge and schedule */
    disable_irq_nosync(irq);          /* Prevent more interrupts */
    napi_schedule(&nic->napi);        /* Schedule NAPI poll */
    
    return IRQ_HANDLED;
}
```

### 18.6 Race in tasklet_kill

```c
/* WRONG — race condition */
static void bad_exit(void)
{
    tasklet_disable(&my_tasklet);
    /* tasklet might be scheduled but not yet run */
    kfree(shared_data);             /* shared_data still referenced! */
}

/* CORRECT */
static void good_exit(void)
{
    /* tasklet_kill: waits for running tasklet AND removes from queue */
    tasklet_kill(&my_tasklet);
    /* Now guaranteed: tasklet will never run again */
    kfree(shared_data);
}
```

---

## 19. Performance Engineering Mindset

### 19.1 The Interrupt Performance Model

Understanding interrupt overhead breakdown:

```
Total interrupt overhead = 
    Hardware signal latency       (~50-200 ns, pin-to-CPU)
  + IDT lookup + context save     (~50-100 ns)
  + TLB/cache effects             (~50-500 ns, cache cold)
  + Handler execution             (variable: 1µs - 1ms)
  + softirq processing            (variable: 1µs - 10ms)
  + Context restore               (~50-100 ns)
```

For high-performance systems:
- **Goal**: Minimize total time, especially softirq duration
- **Technique**: Per-CPU data structures eliminate locking overhead
- **Technique**: NAPI batching reduces per-packet overhead
- **Technique**: IRQ affinity ensures cache locality

### 19.2 Cache Considerations

```c
/* BAD: False sharing — both fields on same cache line */
struct my_device {
    int irq_count;      /* Written by IRQ handler */
    int user_count;     /* Written by userspace */
    /* Both on same 64-byte cache line → cache thrashing */
};

/* GOOD: Explicit cache line separation */
struct my_device {
    int irq_count;
    char _pad1[64 - sizeof(int)];  /* Pad to cache line */
    int user_count;
    char _pad2[64 - sizeof(int)];
} __aligned(64);

/* BEST in kernel: use ____cacheline_aligned_in_smp */
struct my_device {
    int irq_count ____cacheline_aligned_in_smp;
    int user_count ____cacheline_aligned_in_smp;
};
```

### 19.3 The Cognitive Framework: Thinking Like the Kernel

When debugging interrupt performance problems, use this mental model:

```
1. WHERE is time being spent?
   → /proc/interrupts (rate) + hardirqs/softirqs BCC tools (duration)

2. WHICH CPU is handling the interrupt?
   → /proc/irq/N/smp_affinity + per-CPU columns in /proc/interrupts

3. IS batching effective?
   → /proc/softirqs NET_RX rate vs packet rate (ratio = batch size)

4. IS there lock contention?
   → perf lock + lockstat in kernel

5. IS cache locality preserved?
   → perf c2c (cache-to-cache transfer detection)
```

### 19.4 Mental Model: The Three Clocks

Every interrupt interacts with three time scales:

| Clock | Scale | Concern |
|---|---|---|
| **Hardware** | ns | Signal propagation, pin latency |
| **Kernel** | µs | Handler, softirq processing |
| **Application** | ms | End-to-end latency, throughput |

Understanding which clock dominates your problem determines the right optimization. A 50µs softirq is invisible at the application level (ms) but catastrophic for real-time systems (µs budget).

### 19.5 Key Invariants to Always Verify

```
✓ IRQ handler returns in < 10µs
✓ softirq completes within budget (MAX_SOFTIRQ_TIME)
✓ No sleeping in interrupt context
✓ IRQ-shared locks always use irqsave variants
✓ free_irq() called before device teardown
✓ tasklet_kill() / cancel_work_sync() before freeing handler data
✓ Per-CPU data accessed only with preemption disabled
✓ GFP_ATOMIC used in all interrupt/softirq allocations
```

---

## Appendix A: Quick Reference Cheat Sheet

```
REGISTERING INTERRUPTS:
  request_irq(irq, handler, flags, name, dev_id)
  request_threaded_irq(irq, handler, thread_fn, flags, name, dev_id)
  free_irq(irq, dev_id)                  ← Must call on cleanup

SOFTIRQ:
  open_softirq(nr, action)               ← Register (compile-time only)
  raise_softirq(nr)                      ← Raise from any context
  raise_softirq_irqoff(nr)              ← Raise with IRQs disabled
  local_bh_disable() / local_bh_enable() ← Disable/enable bottom halves

TASKLET:
  tasklet_setup(&t, callback)            ← Modern init
  tasklet_init(&t, func, data)           ← Old-style init
  tasklet_schedule(&t)                   ← Schedule (TASKLET_SOFTIRQ)
  tasklet_hi_schedule(&t)                ← Schedule (HI_SOFTIRQ)
  tasklet_disable(&t)                    ← Disable (don't run)
  tasklet_enable(&t)                     ← Re-enable
  tasklet_kill(&t)                       ← Remove and wait

WORKQUEUE:
  INIT_WORK(&w, func)
  schedule_work(&w)                      ← Queue on system_wq
  queue_work(wq, &w)                     ← Queue on specific wq
  cancel_work_sync(&w)                   ← Cancel and wait
  alloc_workqueue(name, flags, max)      ← Create custom wq
  destroy_workqueue(wq)                  ← Destroy custom wq

DELAYED WORK:
  INIT_DELAYED_WORK(&dw, func)
  schedule_delayed_work(&dw, delay)
  cancel_delayed_work_sync(&dw)

LOCKING:
  spin_lock_irqsave(&l, flags)           ← Process context, IRQ-safe
  spin_unlock_irqrestore(&l, flags)
  spin_lock_bh(&l)                       ← BH-safe (not in hardirq)
  spin_unlock_bh(&l)
  spin_lock(&l)                          ← Already in hardirq context

CONTEXT QUERIES:
  in_irq()         in_softirq()         in_interrupt()
  in_nmi()         in_task()            in_serving_softirq()
```

---

## Appendix B: Kernel Config Options

```
CONFIG_PREEMPT_NONE       # Server: no voluntary preemption
CONFIG_PREEMPT_VOLUNTARY  # Desktop: voluntary preemption points  
CONFIG_PREEMPT            # Low-latency: full kernel preemption
CONFIG_PREEMPT_RT         # Real-time: full RT preemption

CONFIG_IRQ_FORCED_THREADING  # Force all IRQs to be threaded
CONFIG_SOFTIRQ_FORCE_THREADING # Force softirqs to kernel threads

CONFIG_LOCKUP_DETECTOR    # Detect hard/soft lockups
CONFIG_DETECT_HUNG_TASK   # Detect hung tasks
CONFIG_PROVE_LOCKING      # Lockdep: detect locking bugs at runtime
CONFIG_LOCK_STAT          # Lock contention statistics
CONFIG_IRQSOFF_TRACER     # Trace maximum IRQ-disabled time
CONFIG_PREEMPTOFF_TRACER  # Trace maximum preemption-disabled time
```

---

## Appendix C: Further Reading

- **"Linux Kernel Development"** — Robert Love (Chapter 7: Interrupts and Interrupt Handlers)
- **"Understanding the Linux Kernel"** — Bovet & Cesati (Chapter 4)
- **"Linux Device Drivers"** — Corbet, Rubini, Kroah-Hartman (Chapter 10)
- **Kernel source**: `kernel/softirq.c`, `kernel/irq/`, `arch/x86/kernel/irq.c`
- **Kernel docs**: `Documentation/core-api/irq/`, `Documentation/networking/napi.rst`
- **LWN.net**: "Deferring work in the Linux kernel" series
- **Brendan Gregg**: "BPF Performance Tools" (Chapter on IRQs and Interrupts)
```

This will be a deep, systems-level masterwork. Building it now.The guide is complete. Here's what's inside and the conceptual spine to hold it all together:

---

## The Master Mental Model

The entire document orbits one design tension: **hardware demands instant acknowledgement, but real work takes time**. Every concept — softirqs, tasklets, workqueues, NAPI, threaded IRQs — is a different answer to the same question.

```
Hardware Event
    │
    ▼  TOP HALF (nanoseconds — IRQs disabled)
[hardirq]   → acknowledge, raise softirq, return
    │
    ▼  BOTTOM HALF TIER 1 (microseconds — no sleep)
[softirq / tasklet]  → process bulk data, no locking cost, per-CPU
    │
    ▼  BOTTOM HALF TIER 2 (milliseconds — can sleep)
[workqueue / threaded IRQ]  → filesystem, mutex, memory pressure
```

---

## What the Guide Covers

| Section | Key Insight |
|---|---|
| **hardirq internals** | Full x86 signal path, IDT structure, `irq_enter/exit` |
| **Top/Bottom Half split** | The design pattern and *why* it exists |
| **softirq engine** | `__do_softirq()` loop, budget, ksoftirqd, concurrency model |
| **tasklets** | Serialization via `TASKLET_STATE_RUN`, deprecation status |
| **workqueues (cmwq)** | Process context, sleeping, kworker thread pool |
| **threaded IRQs** | Modern preferred model, `IRQF_ONESHOT` |
| **interrupt context rules** | `preempt_count` anatomy, what's legal where |
| **SMP & IRQ affinity** | APIC routing, `/proc/irq/N/smp_affinity`, NUMA |
| **NAPI** | Hybrid interrupt+polling, budget contract |
| **PREEMPT_RT** | How RT transforms the IRQ model |
| **eBPF** | `bpftrace` one-liners, full BPF C programs, Aya/Rust |
| **C implementations** | Full kernel module with hrtimer, tasklet, workqueue, procfs |
| **Rust implementations** | IRQ simulation, lock-free SPSC ring buffer, Aya eBPF loader |
| **Pitfalls** | 6 anti-patterns with correct/incorrect code side by side |

The Rust SPSC ring buffer in section 16.3 is particularly worth studying — it's the canonical pattern for IRQ→process data transfer with zero locks, using only memory ordering fences.