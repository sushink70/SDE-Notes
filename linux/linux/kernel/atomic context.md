# Atomic Context in Linux — Complete Comprehensive Guide

> **Summary (4–8 lines)**
> Atomic context in the Linux kernel describes any execution state where sleeping, rescheduling, or blocking is forbidden — including interrupt handlers (hardirq/softirq), NMI handlers, tasklets, spinlock-held sections, and RCU read-side critical sections. The CPU cannot be preempted or voluntarily yield while in atomic context; violating this constraint causes deadlocks, scheduler corruption, or silent data races. The kernel enforces this through `preempt_count`, a per-CPU integer whose sub-fields encode lock depth, BH depth, hardirq/NMI nesting, and preemption disables. Understanding atomic context is prerequisite knowledge for writing correct kernel code, lock-free data structures, and safe cross-language FFI from Rust/Go into the kernel. Memory ordering, cache coherency, and hardware memory barriers are inseparable from atomic context. This guide covers all theory, every kernel primitive, debugging tooling, and concrete C, Go, and Rust implementations.

---

## Table of Contents

1. [First Principles: What Is Atomic Context?](#1-first-principles-what-is-atomic-context)
2. [Execution Contexts in the Linux Kernel](#2-execution-contexts-in-the-linux-kernel)
3. [preempt_count — The Atomic Context Register](#3-preempt_count--the-atomic-context-register)
4. [Hardware Memory Model & Cache Coherency](#4-hardware-memory-model--cache-coherency)
5. [Memory Barriers & Compiler Barriers](#5-memory-barriers--compiler-barriers)
6. [Atomic Operations (atomics)](#6-atomic-operations-atomics)
7. [Spinlocks](#7-spinlocks)
8. [Read-Write Spinlocks](#8-read-write-spinlocks)
9. [Seqlocks (Sequence Locks)](#9-seqlocks-sequence-locks)
10. [RCU — Read-Copy-Update](#10-rcu--read-copy-update)
11. [Per-CPU Variables](#11-per-cpu-variables)
12. [Softirqs, Tasklets, and Work Queues](#12-softirqs-tasklets-and-work-queues)
13. [NMI Context](#13-nmi-context)
14. [Memory Allocation in Atomic Context](#14-memory-allocation-in-atomic-context)
15. [The Sleep-in-Atomic-Context Bug](#15-the-sleep-in-atomic-context-bug)
16. [Lockdep & Debugging Infrastructure](#16-lockdep--debugging-infrastructure)
17. [PREEMPT_RT and Realtime Atomics](#17-preempt_rt-and-realtime-atomics)
18. [Architecture View (ASCII)](#18-architecture-view-ascii)
19. [C Implementations](#19-c-implementations)
20. [Go Implementations](#20-go-implementations)
21. [Rust Implementations](#21-rust-implementations)
22. [Threat Model & Mitigations](#22-threat-model--mitigations)
23. [Testing, Fuzzing & Benchmarking](#23-testing-fuzzing--benchmarking)
24. [Roll-out / Rollback Plan](#24-roll-out--rollback-plan)
25. [References](#25-references)

---

## 1. First Principles: What Is Atomic Context?

### 1.1 Definition

An **atomic context** is a CPU execution state in which the current task (or the interrupt handler running on this CPU) **must not** sleep, block, or be preempted. The word "atomic" here does not mean "a single CPU instruction" — it means **indivisible from the scheduler's perspective**: the scheduler cannot preempt the CPU and switch it to another task.

Three orthogonal constraints define atomic context:

| Constraint | Meaning |
|---|---|
| **No sleep / block** | Cannot call `schedule()`, `wait_event()`, `mutex_lock()`, `copy_from_user()` or any sleeping primitive |
| **No preemption** | Kernel preemption is disabled for the duration |
| **No allocation** | Cannot call `kmalloc(GFP_KERNEL)` — must use `GFP_ATOMIC` |

Violating any of these leads to one of:
- **Deadlock** (sleeping while holding a spinlock; another CPU tries to acquire → starvation)
- **Kernel oops / BUG()** (detected via `might_sleep()` / `lockdep`)
- **Silent data corruption** (races caused by incorrect ordering assumptions)

### 1.2 Why the Kernel Needs Atomic Context

The kernel must service hardware interrupts at any moment. An interrupt arrives asynchronously — even if a task holds a lock, the CPU must handle the interrupt immediately. If the interrupt handler itself tries to acquire a lock that the preempted task holds, a deadlock results. The solution is:

1. Interrupt handlers run in **hardirq context** — an inherently atomic context.
2. Shared data between process context and interrupt handlers is protected with **spinlocks** (which disable interrupts on the local CPU while held).
3. Spinlock-held sections are therefore **atomic context**.

The entire edifice of kernel correctness rests on this discipline.

### 1.3 Relationship to CPU Preemption

Linux supports three preemption models (configured at build time):

```
CONFIG_PREEMPT_NONE         # Server/throughput: only preempts at explicit schedule() points
CONFIG_PREEMPT_VOLUNTARY    # Desktop: adds extra preemption points
CONFIG_PREEMPT              # Low-latency: preempts anywhere except atomic context
CONFIG_PREEMPT_RT           # Real-time: makes even most spinlocks preemptible
```

In all models, **atomic context is never preemptible**. The preemption model only controls where the kernel can preempt *non-atomic* process context.

---

## 2. Execution Contexts in the Linux Kernel

The kernel has a precise hierarchy of execution contexts, ordered by privilege and restrictions:

```
Priority (highest → lowest):
  NMI (Non-Maskable Interrupt)
  Hardirq (hardware interrupt)
  Softirq (including tasklets)
  Process context (task running in kernel mode)
  Idle (cpu_idle loop)
```

### 2.1 Process Context

A task running inside a system call or kernel thread. This is the **only** context where sleeping is allowed.

- `current` pointer is valid and meaningful
- Can access user memory (with `copy_from_user`, `get_user`)
- Can call `schedule()` voluntarily
- Can hold mutexes, semaphores, completion variables
- Can allocate with `GFP_KERNEL`

### 2.2 Hardirq Context (Hardware Interrupt)

Triggered by hardware (NIC, disk controller, timer). The CPU saves current registers, jumps to the interrupt vector.

- `in_interrupt()` returns true
- `in_hardirq()` returns true
- **Absolutely no sleeping**
- All local interrupts may be disabled (depends on `IRQF_DISABLED`)
- Runs on the interrupted CPU's stack (or dedicated interrupt stack on x86)
- Should be **short** — defer work to softirq/tasklet/workqueue

### 2.3 Softirq Context

Softirqs are a deferred mechanism run after hardirq handlers return, on the same CPU. There are a fixed number (32 max, currently ~10 used):

```c
enum {
    HI_SOFTIRQ=0,        /* high-priority tasklets */
    TIMER_SOFTIRQ,
    NET_TX_SOFTIRQ,
    NET_RX_SOFTIRQ,
    BLOCK_SOFTIRQ,
    IRQ_POLL_SOFTIRQ,
    TASKLET_SOFTIRQ,
    SCHED_SOFTIRQ,
    HRTIMER_SOFTIRQ,
    RCU_SOFTIRQ,
    NR_SOFTIRQS
};
```

Properties:
- Can run concurrently on different CPUs (same softirq type can run on multiple CPUs simultaneously — requires per-CPU data or lock protection)
- **Cannot sleep**
- `in_softirq()` returns true
- `in_serving_softirq()` returns true when directly in a softirq handler
- `local_bh_disable()` prevents softirqs from running on current CPU

### 2.4 Tasklet Context

A special softirq (HI_SOFTIRQ or TASKLET_SOFTIRQ) where a given tasklet instance is **serialized** — it never runs concurrently on multiple CPUs.

- Simpler to use than raw softirqs (no concurrent execution of the same instance)
- Still **cannot sleep**
- Still atomic context
- Deprecated in favor of threaded IRQs / workqueues in modern kernels (since ~5.x)

### 2.5 NMI Context

Non-Maskable Interrupts cannot be masked by `cli`/`local_irq_disable()`. Used for:
- Machine check exceptions (hardware errors)
- NMI watchdog (detecting hard lockups)
- Perf PMU overflow

Properties:
- Can interrupt **anything**, including other interrupt handlers
- Extremely restricted — almost no kernel primitives are safe
- Cannot use spinlocks (could deadlock against preempted code that holds the lock)
- Uses **NMI-safe** primitives only (e.g., `atomic_t`, lock-free ring buffers)
- `in_nmi()` returns true

### 2.6 Spinlock-Held Context

Any code path holding a spinlock is atomic context, regardless of whether it's in process, softirq, or hardirq context:

```c
spin_lock(&lock);          /* preemption disabled here */
/* atomic context */
spin_unlock(&lock);        /* preemption re-enabled */
```

Variants:
- `spin_lock()` — disables preemption
- `spin_lock_bh()` — disables preemption + softirqs (BH = Bottom Half)
- `spin_lock_irq()` — disables preemption + all local interrupts
- `spin_lock_irqsave(lock, flags)` — saves interrupt state first

### 2.7 RCU Read-Side Critical Section

```c
rcu_read_lock();
/* atomic context (preemption disabled in non-PREEMPT_RCU) */
rcu_read_unlock();
```

In `CONFIG_PREEMPT_RCU`, the read-side section is preemptible but still tracks readers via `rcu_read_lock_nesting`. In PREEMPT_NONE/VOLUNTARY, it simply disables preemption.

---

## 3. preempt_count — The Atomic Context Register

The entire atomic context tracking mechanism is implemented in a single per-CPU integer: `preempt_count`.

### 3.1 Bit Layout

On x86_64 (kernel 6.x):

```
Bit layout of preempt_count (32 bits):
  [7:0]   = PREEMPT_BITS   (preemption disable count, incremented by preempt_disable())
  [15:8]  = SOFTIRQ_BITS   (softirq/BH disable count, incremented by local_bh_disable())
  [19:16] = HARDIRQ_BITS   (hardirq nesting depth, incremented by irq_enter())
  [20]    = NMI_MASK        (set by NMI entry)
```

```
Bits:  31                   21 20  19    16 15         8 7          0
       +--------------------+--+--+-------+-----------+-----------+
       |      unused        |  |N |HARDIRQ|  SOFTIRQ  |  PREEMPT  |
       +--------------------+--+--+-------+-----------+-----------+
                               ^
                               NMI_MASK
```

### 3.2 Key Macros

```c
/* include/linux/preempt.h */

#define preempt_count()         (current_thread_info()->preempt_count)

/* Check functions */
#define in_irq()                (hardirq_count())         /* in hardirq handler */
#define in_softirq()            (softirq_count())         /* softirq or bh disabled */
#define in_interrupt()          (irq_count())             /* hardirq OR softirq */
#define in_serving_softirq()    (softirq_count() & SOFTIRQ_OFFSET)
#define in_nmi()                (preempt_count() & NMI_MASK)
#define in_atomic()             (preempt_count() != 0)    /* ANY atomic context */

/* Manipulation */
#define preempt_disable()       do { preempt_count_inc(); barrier(); } while (0)
#define preempt_enable()        do { ... schedule_if_needed(); } while (0)

#define local_bh_disable()      __local_bh_disable_ip(_THIS_IP_, SOFTIRQ_DISABLE_OFFSET)
#define local_bh_enable()       __local_bh_enable_ip(_THIS_IP_, SOFTIRQ_DISABLE_OFFSET)

#define local_irq_disable()     do { raw_local_irq_disable(); trace_hardirqs_off(); } while (0)
#define local_irq_enable()      do { trace_hardirqs_on(); raw_local_irq_enable(); } while (0)
```

### 3.3 preempt_count Lifecycle (x86 interrupt entry)

```
Process running in kernel (preempt_count = 0)
  |
  | Hardware interrupt fires
  v
ENTRY(interrupt_entry):         ; arch/x86/entry/entry_64.S
  ; Save registers (RSP, RIP, RFLAGS, CS, etc.) on stack
  call irq_enter_rcu            ; increments HARDIRQ_BITS in preempt_count
  ; preempt_count now = 0x00010000 (HARDIRQ_OFFSET)
  call handle_irq               ; run actual handler
  call irq_exit_rcu             ; decrements HARDIRQ_BITS, runs softirqs if pending
  ; preempt_count back to 0x00000000
  ; Check TIF_NEED_RESCHED, potentially call schedule()
  iretq                         ; restore registers
```

### 3.4 Reading preempt_count in Practice

```c
/* Access from kernel code */
#include <linux/preempt.h>

void example(void)
{
    pr_info("preempt_count = %d\n", preempt_count());
    pr_info("in_atomic = %d\n", in_atomic());
    pr_info("in_interrupt = %d\n", in_interrupt());
}
```

From `/proc` and debugfs:
```bash
# Check current preemption info
cat /proc/sys/kernel/preempt_count    # not directly exposed

# Use ftrace to see preempt_count during tracing
trace-cmd record -e 'irq:*' -e 'preemptirq:*' sleep 1
trace-cmd report | grep preempt_count
```

---

## 4. Hardware Memory Model & Cache Coherency

### 4.1 Why Memory Ordering Matters in Atomic Context

Modern CPUs execute instructions out-of-order, and each CPU core has its own L1/L2 cache. Without explicit ordering constraints, a CPU may:
1. Execute later stores before earlier loads (store-load reordering)
2. Speculatively read a cache line before it's globally visible
3. Batch writes to a write-combining buffer

In single-CPU atomic context, **within-CPU ordering** is maintained by the CPU's own pipeline. But across CPUs, you need barriers.

### 4.2 Memory Ordering Models by Architecture

| Architecture | Model | Notes |
|---|---|---|
| x86 / x86_64 | **TSO** (Total Store Order) | Strongest model; loads never reordered w.r.t. loads, stores w.r.t. stores. Only store-load reordering allowed |
| ARM64 (AArch64) | **Weak** | Most reorderings allowed; needs explicit barriers |
| RISC-V | **Weak** (RVWMO) | Similar to ARM; explicit `fence` instructions required |
| POWER (IBM) | **Weak** | Even more reorderings than ARM |
| s390 | **Strong** | Similar to TSO |

### 4.3 MESI Cache Coherency Protocol

All modern multi-core systems implement a cache coherency protocol (typically MESI or a variant):

```
M (Modified)  — only this cache has the line, dirty (not in memory)
E (Exclusive) — only this cache has the line, clean
S (Shared)    — multiple caches have the line, clean
I (Invalid)   — this cache's copy is stale

State transitions (simplified):
  CPU0 reads  → S or E
  CPU0 writes → M (others go to I = cache invalidation)
  CPU1 reads  → S (CPU0 goes from M to S, write-back to memory)
```

**Cache line invalidation** is the mechanism by which atomic operations achieve coherence. A `LOCK XADD` on x86 asserts the bus lock, invalidating other caches, ensuring exclusive access.

### 4.4 False Sharing

When two CPUs access different variables that happen to share a cache line (64 bytes on x86_64):

```c
/* BAD: counter_a and counter_b share a cache line */
struct bad_counters {
    atomic_t counter_a;   /* CPU0 writes */
    atomic_t counter_b;   /* CPU1 writes */
};

/* GOOD: pad to cache-line boundary */
struct good_counters {
    atomic_t counter_a;
    char _pad[64 - sizeof(atomic_t)];
    atomic_t counter_b;
} ____cacheline_aligned;

/* Kernel macro */
struct good_counters {
    atomic_t counter_a ____cacheline_aligned_in_smp;
    atomic_t counter_b ____cacheline_aligned_in_smp;
};
```

---

## 5. Memory Barriers & Compiler Barriers

### 5.1 Compiler Barrier

Prevents the **compiler** from reordering memory accesses across the barrier. Has no effect on hardware:

```c
/* include/linux/compiler.h */
#define barrier()  __asm__ __volatile__("": : :"memory")

/* Usage: */
a = 1;
barrier();    /* compiler must not move 'a = 1' past barrier */
b = 2;
```

### 5.2 Hardware Memory Barriers

These generate actual CPU instructions that prevent hardware reordering:

```c
/* Full barrier: no loads/stores cross in either direction */
mb();          /* smp_mb() for SMP, mb() even on UP */
smp_mb();      /* Full memory barrier (SMP only, no-op on UP) */

/* Store barrier: all prior stores complete before subsequent stores */
wmb();
smp_wmb();

/* Load barrier: all prior loads complete before subsequent loads */
rmb();
smp_rmb();

/* Acquire: subsequent loads/stores cannot move before this */
smp_load_acquire(ptr);    /* returns *ptr with acquire semantics */

/* Release: prior loads/stores cannot move after this */
smp_store_release(ptr, val);   /* stores val with release semantics */
```

### 5.3 Barrier Implementation by Architecture

```c
/* x86_64: arch/x86/include/asm/barrier.h */
#define mb()    asm volatile("mfence":::"memory")
#define rmb()   asm volatile("lfence":::"memory")  /* or just barrier() on x86 TSO */
#define wmb()   asm volatile("sfence":::"memory")

/* smp_mb on x86 uses LOCK prefix trick (cheaper than mfence in some cases) */
#define smp_mb()  asm volatile("lock; addl $0,-4(%%rsp)": : :"memory", "cc")

/* ARM64: arch/arm64/include/asm/barrier.h */
#define mb()    dsb(sy)     /* Data Synchronization Barrier, full system */
#define rmb()   dsb(ld)     /* Load barrier */
#define wmb()   dsb(st)     /* Store barrier */
#define smp_mb() dmb(ish)   /* Inner Sharable domain */
```

### 5.4 Acquire-Release Pairing (The Fundamental Pattern)

```
CPU 0 (producer):                CPU 1 (consumer):
  data = compute();                while (!READ_ONCE(ready))
  smp_store_release(&ready, 1);       cpu_relax();
                                   smp_load_acquire(&ready); /* or use READ_ONCE + smp_rmb */
                                   use(data);
```

`smp_store_release` + `smp_load_acquire` form a **synchronizes-with** relationship: all stores before the release are visible after the acquire.

### 5.5 READ_ONCE / WRITE_ONCE

Prevent the compiler from merging, splitting, or eliminating reads/writes:

```c
/* Without READ_ONCE, compiler may cache the value in a register */
while (flag == 0) { /* compiler may read flag once and loop forever */ }

/* Correct: */
while (READ_ONCE(flag) == 0) { cpu_relax(); }

/* WRITE_ONCE prevents compiler from splitting a write */
WRITE_ONCE(ptr->field, value);
```

These compile to `volatile` accesses but are semantically richer than C `volatile`.

---

## 6. Atomic Operations (atomics)

### 6.1 atomic_t and atomic64_t

The kernel's primary atomic integer types:

```c
/* include/linux/types.h */
typedef struct { int counter; } atomic_t;
typedef struct { long counter; } atomic64_t;
```

### 6.2 Complete API Reference

```c
/* Initialization */
atomic_t v = ATOMIC_INIT(0);
atomic_set(&v, 5);

/* Read */
int val = atomic_read(&v);           /* READ_ONCE(v.counter) */

/* Add/Sub */
atomic_add(delta, &v);               /* no return value */
atomic_sub(delta, &v);
int r = atomic_add_return(delta, &v); /* returns new value */
int r = atomic_sub_return(delta, &v);
int r = atomic_fetch_add(delta, &v);  /* returns OLD value */
int r = atomic_fetch_sub(delta, &v);

/* Increment/Decrement */
atomic_inc(&v);
atomic_dec(&v);
int r = atomic_inc_return(&v);        /* returns new value */
int r = atomic_dec_return(&v);
bool z = atomic_dec_and_test(&v);    /* true if result == 0 */
bool z = atomic_inc_and_test(&v);
bool z = atomic_sub_and_test(n, &v); /* true if result == 0 */

/* Bitwise */
atomic_or(mask, &v);
atomic_and(mask, &v);
atomic_xor(mask, &v);
int r = atomic_fetch_or(mask, &v);   /* returns OLD value */
int r = atomic_fetch_and(mask, &v);
int r = atomic_fetch_xor(mask, &v);

/* Compare-and-swap (CAS) */
bool ok = atomic_cmpxchg(&v, old, new);  /* returns OLD value */
/* actual modern API: */
int old = atomic_cmpxchg(&v, expected, desired); /* returns prev value */

/* Exchange */
int prev = atomic_xchg(&v, new_val);   /* returns old value */

/* Conditional operations */
bool ok = atomic_add_unless(&v, delta, unless_val); /* add only if v != unless_val */
bool ok = atomic_inc_unless_negative(&v);
bool ok = atomic_dec_unless_positive(&v);
```

### 6.3 Memory Ordering of Atomic Operations

Linux atomic ops have specific ordering guarantees:

```c
/* Fully ordered (default for arithmetic returning a value): */
atomic_add_return()     /* full smp_mb() before AND after */
atomic_sub_return()
atomic_inc_return()
atomic_dec_return()
atomic_xchg()
atomic_cmpxchg()

/* Relaxed (no barrier): */
atomic_add()            /* no ordering guarantee */
atomic_inc()
atomic_set()
atomic_read()           /* just READ_ONCE */

/* Acquire semantics (barrier after): */
atomic_read_acquire()
atomic_cmpxchg_acquire()

/* Release semantics (barrier before): */
atomic_set_release()
atomic_cmpxchg_release()

/* Relaxed CAS: */
atomic_cmpxchg_relaxed()
```

### 6.4 Long and Pointer Atomics

```c
/* atomic_long_t: pointer-width atomic */
atomic_long_t lv = ATOMIC_LONG_INIT(0);
atomic_long_inc(&lv);
long val = atomic_long_read(&lv);

/* Atomic pointer operations */
void *old = xchg(&ptr, new_ptr);        /* atomic pointer swap */
void *old = cmpxchg(&ptr, expected, new_ptr);
```

### 6.5 Atomic Bit Operations

```c
/* include/asm-generic/bitops/atomic.h */
unsigned long flags_word = 0;

set_bit(bit_nr, &flags_word);          /* atomic set */
clear_bit(bit_nr, &flags_word);        /* atomic clear */
change_bit(bit_nr, &flags_word);       /* atomic toggle */
bool was_set = test_and_set_bit(bit_nr, &flags_word);   /* returns old value */
bool was_set = test_and_clear_bit(bit_nr, &flags_word);
bool was_set = test_and_change_bit(bit_nr, &flags_word);
bool val = test_bit(bit_nr, &flags_word);  /* non-atomic read */

/* Non-atomic variants (process context only): */
__set_bit(bit_nr, &flags_word);        /* faster, no LOCK prefix */
__clear_bit(bit_nr, &flags_word);

/* Find operations (non-atomic): */
int pos = find_first_bit(addr, size);
int pos = find_next_bit(addr, size, offset);
int pos = find_first_zero_bit(addr, size);
```

### 6.6 x86_64 Implementation Deep Dive

On x86_64, `atomic_add_return` compiles to:

```c
static __always_inline int arch_atomic_add_return(int i, atomic_t *v)
{
    return i + xadd(&v->counter, i);
}

/* xadd: */
static __always_inline int xadd(int *ptr, int inc)
{
    asm volatile(LOCK_PREFIX "xaddl %0, %1"
                 : "+r" (inc), "+m" (*ptr)
                 : : "memory");
    return inc;
}
/* LOCK_PREFIX = "lock " on SMP, "" on UP */
/* XADD: exchange and add; atomically: tmp=*ptr; *ptr+=inc; return tmp */
```

---

## 7. Spinlocks

### 7.1 What Is a Spinlock?

A spinlock is a mutual exclusion mechanism where the waiting CPU **spins** (busy-waits) rather than sleeping. This is correct in atomic context because:

1. Sleeping would require `schedule()`, which requires non-atomic context
2. Spinning consumes CPU but avoids the overhead of context switching for very short critical sections

### 7.2 Spinlock Types and Selection

```
raw_spinlock_t    — cannot be made preemptible by PREEMPT_RT; used in core kernel paths
spinlock_t        — becomes a sleeping lock (mutex) under PREEMPT_RT
```

**Use `raw_spinlock_t` only when the critical section is truly tiny and RT latency is not a concern (e.g., scheduler internals, interrupt controller code). Use `spinlock_t` everywhere else.**

### 7.3 Spinlock Internal Implementation

On modern kernels (>= 4.2), Linux uses **queued spinlocks** (qspinlock):

```c
/* include/asm-generic/qspinlock.h */
typedef struct qspinlock {
    union {
        atomic_t val;
        struct {
            u8 locked;      /* lock byte: 0=free, 1=locked */
            u8 pending;     /* a waiter is about to acquire */
            u16 tail;       /* tail of MCS queue */
        };
    };
} arch_spinlock_t;
```

The MCS (Mellor-Crummey-Scott) queue ensures **FIFO ordering** and **cache-friendly spinning** — each CPU spins on its own local variable, not the shared lock word (which would cause cache-line bouncing):

```
Ticket-based (old):
  CPU0 holds lock, CPU1 and CPU2 spin on same cache line → cache thrashing

MCS-queue (new, qspinlock):
  CPU0 holds lock
  CPU1 queued: spins on per-CPU mcs_node.locked
  CPU2 queued: spins on per-CPU mcs_node.locked
  When CPU0 releases, it writes to CPU1's node.locked → CPU1 acquires
```

### 7.4 Complete Spinlock API

```c
/* Declaration and initialization */
DEFINE_SPINLOCK(my_lock);          /* static */
spinlock_t my_lock = __SPIN_LOCK_UNLOCKED(my_lock);  /* static */
spin_lock_init(&my_lock);          /* dynamic */

/* Locking variants */

/* Process context only, shared data not accessed from IRQ/softirq: */
spin_lock(&lock);
spin_unlock(&lock);

/* Process context, data shared with softirq handlers: */
spin_lock_bh(&lock);               /* disables bottom halves (softirqs) */
spin_unlock_bh(&lock);

/* Process context, data shared with any IRQ handler: */
spin_lock_irq(&lock);              /* disables all local IRQs */
spin_unlock_irq(&lock);

/* PREFERRED when called from context where IRQs may already be disabled: */
unsigned long flags;
spin_lock_irqsave(&lock, flags);   /* saves current IRQ state */
spin_unlock_irqrestore(&lock, flags);

/* Non-blocking try: */
bool acquired = spin_trylock(&lock);        /* returns 1 if acquired */
bool acquired = spin_trylock_bh(&lock);
bool acquired = spin_trylock_irq(&lock);
bool acquired = spin_trylock_irqsave(&lock, &flags);

/* Check state: */
bool is_locked = spin_is_locked(&lock);     /* debug only, racy */
bool is_contended = spin_is_contended(&lock);
```

### 7.5 Spinlock Usage Rules

```
Rule 1: Never sleep while holding a spinlock.
Rule 2: Always hold spinlocks for the shortest possible time.
Rule 3: Acquire locks in a consistent order to avoid deadlock.
Rule 4: If a lock protects data accessed from IRQ context, always use irqsave.
Rule 5: Don't call spin_lock_irq() if your caller may have already disabled IRQs.
        Use spin_lock_irqsave() instead.
Rule 6: spin_lock_bh() sufficient if data only accessed from softirq (not hardirq).
Rule 7: Nested spinlocks → must prove no deadlock (lockdep validates this).
```

### 7.6 Lock Nesting and Subclass

```c
/* For intentional same-lock-class nesting (e.g., two locks of same type): */
spin_lock_nested(&lock, subclass);

/* Lockdep subclasses: */
#define SINGLE_DEPTH_NESTING    1
#define DOUBLE_DEPTH_NESTING    2
```

---

## 8. Read-Write Spinlocks

### 8.1 rwlock_t

Allows multiple concurrent readers or one exclusive writer:

```c
DEFINE_RWLOCK(my_rwlock);

/* Reader path (can be multiple concurrent readers): */
read_lock(&my_rwlock);
/* ... read shared data ... */
read_unlock(&my_rwlock);

/* Reader variants: */
read_lock_bh(&my_rwlock);
read_lock_irq(&my_rwlock);
read_lock_irqsave(&my_rwlock, flags);

/* Writer path (exclusive): */
write_lock(&my_rwlock);
/* ... modify shared data ... */
write_unlock(&my_rwlock);

/* Writer variants: */
write_lock_bh(&my_rwlock);
write_lock_irq(&my_rwlock);
write_lock_irqsave(&my_rwlock, flags);

/* Try variants: */
bool ok = read_trylock(&my_rwlock);
bool ok = write_trylock(&my_rwlock);
```

### 8.2 Limitations of rwlock_t

- **Writer starvation**: If readers hold the lock continuously, writers starve
- **No reader fairness**: Readers are not queued; a writer waiting blocks new readers on some implementations (depends on arch)
- **Cache thrashing**: Multiple readers updating the reader count causes cacheline contention
- **Alternative**: Use RCU for read-heavy workloads; rwlock_t is rarely the right choice

---

## 9. Seqlocks (Sequence Locks)

### 9.1 Concept

Seqlocks allow **concurrent reading without holding a lock**, detecting if a write occurred during the read. Writers always succeed immediately; readers may need to retry.

**Perfect for**: frequently read, infrequently written, small data (e.g., `jiffies`, `timespec`).

### 9.2 Seqlock API

```c
#include <linux/seqlock.h>

DEFINE_SEQLOCK(my_seqlock);
seqlock_t my_seqlock = __SEQLOCK_UNLOCKED(my_seqlock);

/* Writer (exclusive, disables preemption): */
write_seqlock(&my_seqlock);
/* ... write data ... */
write_sequnlock(&my_seqlock);

/* Writer variants: */
write_seqlock_irqsave(&my_seqlock, flags);
write_sequnlock_irqrestore(&my_seqlock, flags);
write_seqlock_bh(&my_seqlock);

/* Reader (retries if writer concurrent): */
unsigned int seq;
do {
    seq = read_seqbegin(&my_seqlock);
    /* ... read data (may be inconsistent!) ... */
} while (read_seqretry(&my_seqlock, seq));

/* Reader in IRQ context: */
do {
    seq = read_seqbegin(&my_seqlock);
    /* read... */
} while (read_seqretry(&my_seqlock, seq));
```

### 9.3 Seqlock Internal Mechanism

```c
/* The sequence counter: */
typedef struct {
    unsigned sequence;   /* incremented by writer: odd=writing, even=not writing */
    spinlock_t lock;
} seqlock_t;

/* write_seqlock: */
spin_lock(&sl->lock);
sl->sequence++;          /* now odd → indicates write in progress */
smp_wmb();

/* write_sequnlock: */
smp_wmb();
sl->sequence++;          /* now even → write complete */
spin_unlock(&sl->lock);

/* read_seqbegin: returns sequence (must be even, i.e., no write in progress) */
/* read_seqretry: returns true if sequence changed (odd or different) → retry */
```

### 9.4 Raw Seqcount (Without Spinlock)

```c
seqcount_t my_seqcount = SEQCNT_ZERO(my_seqcount);

/* Writer must ensure external mutual exclusion: */
write_seqcount_begin(&my_seqcount);
/* ... write ... */
write_seqcount_end(&my_seqcount);

/* Reader: */
unsigned seq;
do {
    seq = read_seqcount_begin(&my_seqcount);
    /* read... */
} while (read_seqcount_retry(&my_seqcount, seq));
```

---

## 10. RCU — Read-Copy-Update

### 10.1 Concept

RCU is the most important synchronization mechanism in the Linux kernel for read-heavy, pointer-based data structures. The core insight:

- **Readers**: hold `rcu_read_lock()`, no synchronization overhead, no spinlocks, can run concurrently with writers
- **Writers**: make a new copy of the data, atomically update the pointer, then **wait for all readers that saw the old pointer** to finish (a "grace period")

### 10.2 RCU Variants

```
SRCU (Sleepable RCU)     — readers can sleep; uses per-SRCU-domain state
SRCU with Tree           — scalable SRCU for large systems (CONFIG_TREE_SRCU)
Tiny RCU                 — for UP kernels (CONFIG_TINY_RCU)
Tree RCU                 — hierarchical RCU for SMP (CONFIG_TREE_RCU, default)
Tasks RCU                — for tracing, waits for tasks to be not in user code
```

### 10.3 Core RCU API

```c
#include <linux/rcupdate.h>

/* Read side (atomic context — preemption disabled in non-PREEMPT_RCU): */
rcu_read_lock();
struct my_data *p = rcu_dereference(global_ptr); /* must use this, not plain read */
if (p) {
    /* use p safely — guaranteed not freed until rcu_read_unlock() */
    use(p->field);
}
rcu_read_unlock();

/* Write side — update pointer atomically: */
new_p = kmalloc(sizeof(*new_p), GFP_KERNEL);
/* ... fill new_p ... */
old_p = rcu_dereference_protected(global_ptr, lockdep_is_held(&my_lock));
spin_lock(&my_lock);
rcu_assign_pointer(global_ptr, new_p);  /* smp_store_release internally */
spin_unlock(&my_lock);

/* Wait for all pre-existing readers to complete: */
synchronize_rcu();           /* blocks until grace period elapsed */
/* Now safe to free: */
kfree(old_p);

/* Or asynchronous: */
call_rcu(&old_p->rcu_head, my_free_callback);

/* Or deferred kfree (most common): */
kfree_rcu(old_p, rcu_head_field_name);
```

### 10.4 RCU-Protected List Operations

```c
#include <linux/rculist.h>

/* Traversal (read side): */
rcu_read_lock();
list_for_each_entry_rcu(entry, &my_list, list_member) {
    /* process entry */
}
rcu_read_unlock();

/* Insertion (write side, no grace period needed): */
spin_lock(&list_lock);
list_add_rcu(&new_entry->list_member, &my_list);
spin_unlock(&list_lock);

/* Deletion (write side): */
spin_lock(&list_lock);
list_del_rcu(&entry->list_member);   /* safe: readers may still traverse */
spin_unlock(&list_lock);
synchronize_rcu();                   /* wait for readers */
kfree(entry);
```

### 10.5 rcu_dereference vs. Plain Pointer Read

```c
/* WRONG — compiler may optimize away, no READ_ONCE, no data dependency barrier: */
struct foo *p = global_rcu_ptr;

/* CORRECT — expands to READ_ONCE() + data dependency barrier on some archs: */
struct foo *p = rcu_dereference(global_rcu_ptr);

/* In update side (holding lock): */
struct foo *p = rcu_dereference_protected(global_rcu_ptr,
                    lockdep_is_held(&global_lock));

/* In __init or module init (no RCU readers possible): */
struct foo *p = rcu_dereference_raw(global_rcu_ptr);
```

### 10.6 Grace Period Mechanics

```
Timeline:
  t=0: global_ptr updated via rcu_assign_pointer()
  t=0: Reader A (already in critical section) uses old pointer — SAFE
  t=1: Reader B enters rcu_read_lock() — sees new pointer
  ...
  t=N: Reader A calls rcu_read_unlock() — last old-pointer reader done
  t=N: synchronize_rcu() returns — grace period complete
  t=N+: kfree(old_p) safe

Grace period detection (Tree RCU):
  Each CPU must pass through a "quiescent state":
  - Context switch (most common)
  - Idle entry
  - User space entry
  - Explicit rcu_note_context_switch()
```

### 10.7 SRCU (Sleepable RCU)

```c
#include <linux/srcu.h>

DEFINE_STATIC_SRCU(my_srcu);  /* or: struct srcu_struct my_srcu; init_srcu_struct(&my_srcu); */

/* Read side (CAN SLEEP): */
int idx = srcu_read_lock(&my_srcu);
/* ... may sleep here ... */
srcu_read_unlock(&my_srcu, idx);

/* Write side: */
synchronize_srcu(&my_srcu);   /* waits for all readers with this srcu_struct */
call_srcu(&my_srcu, &obj->rcu_head, callback);
```

---

## 11. Per-CPU Variables

### 11.1 Concept

Per-CPU variables have one instance per logical CPU. Each CPU accesses only its own copy, eliminating the need for locks for CPU-local data:

```c
#include <linux/percpu.h>

/* Define a static per-CPU variable: */
DEFINE_PER_CPU(int, my_counter);
DEFINE_PER_CPU(struct stats, cpu_stats);

/* Dynamically allocated: */
int __percpu *dyn_counter = alloc_percpu(int);
free_percpu(dyn_counter);
```

### 11.2 Accessing Per-CPU Variables

```c
/* Access current CPU's instance (preemption must be disabled): */
preempt_disable();
int val = __this_cpu_read(my_counter);
__this_cpu_write(my_counter, 42);
__this_cpu_add(my_counter, 1);
__this_cpu_inc(my_counter);
preempt_enable();

/* Macros that disable preemption automatically: */
int val = this_cpu_read(my_counter);   /* disables preemption around read */
this_cpu_write(my_counter, 42);
this_cpu_add(my_counter, delta);
this_cpu_inc(my_counter);

/* Access another CPU's instance: */
int *ptr = per_cpu_ptr(&my_counter, cpu_id);
int val = *ptr;   /* safe only if that CPU won't access it simultaneously */

/* Iterate all CPUs: */
int cpu;
for_each_possible_cpu(cpu) {
    int *p = per_cpu_ptr(&my_counter, cpu);
    total += *p;
}
```

### 11.3 Why Preemption Must Be Disabled

```c
/* BUG: task migrates between disable and the access */
int val = __this_cpu_read(my_counter);  /* reads CPU 0's counter */
/* ... task migrated to CPU 1 here ... */
__this_cpu_write(my_counter, val + 1); /* writes CPU 1's counter! */

/* CORRECT: use this_cpu_* which disables preemption, or hold spinlock */
```

### 11.4 Lockless Statistics Pattern

```c
DEFINE_PER_CPU(u64, rx_packets);

/* In IRQ/softirq handler (already non-preemptible): */
__this_cpu_inc(rx_packets);

/* Read aggregate: */
u64 total = 0;
int cpu;
for_each_possible_cpu(cpu)
    total += per_cpu(rx_packets, cpu);
```

---

## 12. Softirqs, Tasklets, and Work Queues

### 12.1 Softirq Architecture

```
Hardirq fires → handler runs → returns → irq_exit() checks softirq pending bits
                                          → runs softirq handler on same CPU (ksoftirqd if overload)

struct softirq_action {
    void (*action)(struct softirq_action *);
};

static struct softirq_action softirq_vec[NR_SOFTIRQS];
```

### 12.2 Raising a Softirq

```c
/* Only allowed for built-in softirqs (you can't add new softirq types at runtime): */
raise_softirq(NET_RX_SOFTIRQ);          /* sets bit in __softirq_pending, schedules */
raise_softirq_irqoff(NET_RX_SOFTIRQ);   /* must be called with IRQs disabled */

/* Check pending: */
local_softirq_pending()                  /* bitmask of pending softirqs */
```

### 12.3 Registering a Softirq Handler

```c
/* Done once at boot (not dynamically): */
open_softirq(NET_RX_SOFTIRQ, net_rx_action);

/* Handler signature: */
static void net_rx_action(struct softirq_action *h)
{
    /* atomic context, cannot sleep */
    /* runs with softirqs disabled on this CPU */
    /* can be interrupted by hardirqs */
}
```

### 12.4 Tasklets

```c
#include <linux/interrupt.h>

/* Old API (deprecated in 5.x but still widely used): */
DECLARE_TASKLET(my_tasklet, my_tasklet_handler);
DECLARE_TASKLET_DISABLED(my_tasklet, my_tasklet_handler);

/* Dynamic: */
struct tasklet_struct my_tasklet;
tasklet_init(&my_tasklet, my_tasklet_handler, (unsigned long)data);

/* Handler: */
static void my_tasklet_handler(unsigned long data)
{
    /* atomic context — cannot sleep */
    /* serialized: this tasklet instance never runs concurrently */
}

/* Schedule (from hardirq or any context): */
tasklet_schedule(&my_tasklet);        /* schedules for TASKLET_SOFTIRQ */
tasklet_hi_schedule(&my_tasklet);     /* schedules for HI_SOFTIRQ */

/* Control: */
tasklet_disable(&my_tasklet);   /* prevent running (waits if currently running) */
tasklet_enable(&my_tasklet);
tasklet_kill(&my_tasklet);      /* remove pending tasklet (may block) */
```

### 12.5 Work Queues (Non-Atomic Deferred Work)

Work queues execute in **process context** — they CAN sleep. Use for heavier deferred work:

```c
#include <linux/workqueue.h>

/* System-wide work queues (use these when possible): */
schedule_work(&my_work);              /* system_wq */
schedule_delayed_work(&my_work, HZ);  /* system_wq, delayed by 1 second */
schedule_work_on(cpu, &my_work);      /* pin to specific CPU */

/* Declare and initialize: */
static struct work_struct my_work;
INIT_WORK(&my_work, my_work_handler);

static struct delayed_work my_delayed_work;
INIT_DELAYED_WORK(&my_delayed_work, my_dwork_handler);

/* Handler (process context — CAN sleep): */
static void my_work_handler(struct work_struct *work)
{
    struct my_device *dev = container_of(work, struct my_device, my_work);
    /* can sleep, allocate with GFP_KERNEL, etc. */
}

/* Custom work queue (for isolation/priority): */
struct workqueue_struct *my_wq = alloc_workqueue("my_wq",
    WQ_UNBOUND | WQ_HIGHPRI, 0);
queue_work(my_wq, &my_work);
destroy_workqueue(my_wq);

/* Work queue flags: */
WQ_UNBOUND          /* not bound to a specific CPU (for long-running) */
WQ_HIGHPRI          /* run on high-priority worker threads */
WQ_CPU_INTENSIVE    /* hint: may block CPU */
WQ_FREEZABLE        /* freeze during system suspend */
WQ_MEM_RECLAIM      /* has a rescue worker for memory pressure */
WQ_SYSFS            /* expose in /sys/bus/workqueue */
```

---

## 13. NMI Context

### 13.1 What Makes NMI Special

NMIs are the most constrained context in the kernel. They can interrupt:
- Normal process code
- IRQ handlers
- Code with interrupts disabled
- Spinlock-held sections
- Even other NMI handlers on some architectures (nested NMI)

This means **spinlocks are unsafe in NMI context** — if an NMI fires while a CPU holds a spinlock, and the NMI handler tries to acquire the same spinlock, the result is a deadlock.

### 13.2 NMI-Safe Primitives

```c
/* Safe in NMI context: */
atomic_t
atomic64_t
atomic_long_t
/* Atomic bit ops: */
set_bit(), clear_bit(), test_bit()
/* Lock-free ring buffers: */
/* e.g., perf ring buffer, ftrace ring buffer */

/* Lock-free algorithms using cmpxchg: */
atomic_cmpxchg()
cmpxchg()
xchg()

/* NOT safe in NMI: */
spinlock_t          /* DEADLOCK risk */
raw_spinlock_t      /* DEADLOCK risk */
mutex_t             /* DEADLOCK + sleep */
kmalloc()           /* may acquire locks internally */
printk()            /* unsafe in strict NMI — use nmi_vprintk_readable() */
```

### 13.3 NMI-Safe Ring Buffer Pattern

```c
/* perf/ftrace use this pattern: */
struct ring_buffer {
    atomic_t head;
    atomic_t tail;
    void    *data;
    size_t   size;
};

/* NMI-safe write: */
static int rb_write_nmi(struct ring_buffer *rb, void *data, size_t len)
{
    int tail, new_tail, head;
    
    do {
        tail = atomic_read(&rb->tail);
        head = atomic_read(&rb->head);
        if (CIRC_SPACE(tail, head, rb->size) < len)
            return -ENOSPC;
        new_tail = (tail + len) & (rb->size - 1);
    } while (atomic_cmpxchg(&rb->tail, tail, new_tail) != tail);
    
    memcpy(rb->data + tail, data, len);
    return 0;
}
```

### 13.4 Checking NMI Context

```c
if (in_nmi()) {
    /* use only NMI-safe operations */
}

/* Architecture-specific NMI handler registration: */
/* register_nmi_handler(NMI_UNKNOWN, my_nmi_handler, 0, "my_nmi"); */
```

---

## 14. Memory Allocation in Atomic Context

### 14.1 GFP Flags

```c
/* Process context (can sleep, may block): */
ptr = kmalloc(size, GFP_KERNEL);

/* Atomic context (CANNOT sleep, may fail): */
ptr = kmalloc(size, GFP_ATOMIC);

/* GFP_ATOMIC internals: */
/* = __GFP_HIGH | __GFP_ATOMIC | __GFP_KSWAPD_RECLAIM */
/* - Can access emergency memory reserves */
/* - Cannot wait for memory reclaim */
/* - Lower order allocations more likely to succeed */
/* - WILL FAIL on high memory pressure */

/* Softirq context: */
ptr = kmalloc(size, GFP_ATOMIC);
/* same as above */

/* NMI context: */
/* kmalloc is UNSAFE even with GFP_ATOMIC (may acquire locks internally) */
/* Use pre-allocated pools or mempool */
```

### 14.2 mempool — Pre-allocated Pool

```c
#include <linux/mempool.h>

/* Create a pool with min_nr guaranteed elements: */
mempool_t *pool = mempool_create_kmalloc_pool(min_nr, obj_size);
mempool_t *pool = mempool_create_slab_pool(min_nr, my_slab_cache);
mempool_t *pool = mempool_create(min_nr, my_alloc_fn, my_free_fn, pool_data);

/* Allocate (never fails if pool has elements, may sleep if GFP_KERNEL): */
void *p = mempool_alloc(pool, GFP_ATOMIC); /* atomic: may return from reserve */
void *p = mempool_alloc(pool, GFP_KERNEL); /* process context: may sleep to refill */

/* Free (may return element to pool if below min_nr): */
mempool_free(p, pool);

/* Destroy: */
mempool_destroy(pool);
```

### 14.3 SLAB/SLUB Caches

```c
#include <linux/slab.h>

/* Create a cache for frequently allocated objects: */
struct kmem_cache *my_cache = kmem_cache_create(
    "my_object",          /* name (shown in /proc/slabinfo) */
    sizeof(struct my_obj), /* object size */
    __alignof__(struct my_obj), /* alignment */
    SLAB_HWCACHE_ALIGN | SLAB_PANIC, /* flags */
    NULL                  /* constructor */
);

/* Allocate from cache: */
struct my_obj *obj = kmem_cache_alloc(my_cache, GFP_ATOMIC); /* atomic OK */
struct my_obj *obj = kmem_cache_alloc(my_cache, GFP_KERNEL);  /* process context */

/* Free: */
kmem_cache_free(my_cache, obj);

/* Destroy cache: */
kmem_cache_destroy(my_cache);
```

### 14.4 Stack Allocation (Always Safe in Atomic Context)

```c
/* Stack variables are always safe — no allocation involved: */
void my_irq_handler(void)
{
    char buf[128];      /* on the kernel stack — always OK */
    struct my_small_struct s; /* OK if fits on stack */
    /* Kernel stack is typically 8KB or 16KB (CONFIG_THREAD_SIZE_ORDER) */
}
```

---

## 15. The Sleep-in-Atomic-Context Bug

### 15.1 Why It's Catastrophic

If code sleeps while in atomic context:
1. `schedule()` is called
2. The current task is put to sleep (e.g., waiting for I/O)
3. Another task runs on this CPU
4. If the sleeping task held a spinlock, any task trying to acquire it will spin forever
5. **Deadlock** or **kernel hang**

If `CONFIG_DEBUG_ATOMIC_SLEEP` is enabled, the kernel calls `might_sleep()` which checks `in_atomic()` and triggers a warning/oops.

### 15.2 Common Bugs

```c
/* BUG 1: kmalloc with GFP_KERNEL in atomic context */
spin_lock(&lock);
ptr = kmalloc(size, GFP_KERNEL);  /* may sleep! BUG */
spin_unlock(&lock);

/* FIX: */
spin_lock(&lock);
ptr = kmalloc(size, GFP_ATOMIC);  /* won't sleep */
spin_unlock(&lock);

/* BUG 2: mutex_lock in atomic context */
spin_lock(&lock);
mutex_lock(&my_mutex);  /* sleeps! BUG */
spin_unlock(&lock);

/* BUG 3: copy_from_user in atomic context */
spin_lock(&lock);
copy_from_user(kbuf, ubuf, len);  /* may page fault → sleep */
spin_unlock(&lock);

/* FIX: copy before acquiring lock */
if (copy_from_user(kbuf, ubuf, len)) return -EFAULT;
spin_lock(&lock);
/* use kbuf */
spin_unlock(&lock);

/* BUG 4: msleep / schedule_timeout */
spin_lock_irqsave(&lock, flags);
msleep(10);  /* SLEEP! BUG */
spin_unlock_irqrestore(&lock, flags);

/* FIX: use udelay/ndelay for short waits in atomic context */
spin_lock_irqsave(&lock, flags);
udelay(100);  /* busy-wait 100 microseconds */
spin_unlock_irqrestore(&lock, flags);
```

### 15.3 might_sleep() and might_resched()

```c
/* These are inserted by the kernel in potentially-sleeping functions: */
void mutex_lock(struct mutex *m)
{
    might_sleep();   /* checks in_atomic(), warns if true */
    /* ... */
}

/* might_sleep() expands to: */
#define might_sleep() \
    do { __might_sleep(__FILE__, __LINE__, 0); } while (0)

void __might_sleep(const char *file, int line, int preempt_offset)
{
    if (in_atomic() || irqs_disabled()) {
        printk(KERN_ERR "BUG: sleeping function called from invalid context...");
        dump_stack();
        /* CONFIG_DEBUG_ATOMIC_SLEEP: add_taint, possibly BUG() */
    }
}
```

### 15.4 Busy-Wait Alternatives for Atomic Context

```c
/* Instead of msleep() — use busy-wait loops (only for very short delays): */
ndelay(100);          /* nanosecond delay (pure busy-wait) */
udelay(10);           /* microsecond delay (pure busy-wait) */
mdelay(1);            /* millisecond delay (busy-wait — AVOID except testing) */

/* CPU relaxation hint (reduces power/contention during spin): */
cpu_relax();          /* typically: rep nop / yield / isb */

/* For longer waits in process context: */
usleep_range(min_us, max_us);   /* sleeps; process context only */
msleep(ms);                     /* sleeps; process context only */
ssleep(s);                      /* sleeps; process context only */
```

---

## 16. Lockdep & Debugging Infrastructure

### 16.1 Lockdep

Lockdep is the kernel's **lock dependency validator**. Enabled with `CONFIG_LOCKDEP=y`. It:
- Tracks lock acquisition order across all execution paths
- Detects potential deadlocks (lock order inversions) at runtime
- Detects lock misuse (e.g., acquiring a sleeping lock in atomic context)

```
Lockdep output example:
======================================================
WARNING: possible circular locking dependency detected
5.15.0 #1 Not tainted
------------------------------------------------------
sysrq/143 is trying to acquire lock:
... (&zone->lock){-.-.}-{2:2}, at: rmqueue_bulk+0x57/0x630
but task is already holding lock:
... (&(&pool->lock)->rlock){-.-.}-{2:2}, at: ...
the existing dependency chain is:
  -> (&zone->lock) from: ...
  -> (&pool->lock) from: ...
  which creates a cycle!
```

Lock annotation markers:
```
{-.-.}  means:
  - (minus) = not held in hardirq (safe to hold here without irqsave)
  . (dot)   = sometimes held in softirq
  . (dot)   = sometimes held in softirq (read)
```

### 16.2 Enabling Debug Kernel Options

```bash
# In Kconfig / .config:
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_SPINLOCK=y
CONFIG_DEBUG_MUTEXES=y
CONFIG_DEBUG_LOCK_ALLOC=y
CONFIG_PROVE_LOCKING=y         # lockdep
CONFIG_LOCKDEP=y
CONFIG_DEBUG_ATOMIC_SLEEP=y    # detect sleep-in-atomic
CONFIG_DEBUG_PREEMPT=y         # check preempt_count invariants
CONFIG_PROVE_RCU=y             # RCU correctness checking
CONFIG_RCU_TRACE=y
CONFIG_DEBUG_LIST=y
CONFIG_DEBUG_OBJECTS=y
CONFIG_KASAN=y                 # kernel address sanitizer
CONFIG_KCSAN=y                 # kernel concurrency sanitizer
CONFIG_UBSAN=y                 # undefined behavior sanitizer
```

### 16.3 KCSAN — Kernel Concurrency Sanitizer

KCSAN is a dynamic data race detector for the kernel:

```bash
# Enable: CONFIG_KCSAN=y
# Run with: scripts/kernel-doc to instrument accesses

# KCSAN inserts callbacks before each memory access:
__kcsan_check_access(ptr, size, KCSAN_ACCESS_WRITE);

# If two CPUs access same location concurrently (one write): RACE detected!
```

Output:
```
==================================================================
BUG: KCSAN: data-race in my_func / my_other_func
write to 0xffff... of 4 bytes by task 1234 on cpu 1:
  my_func+0x20/0x40
  ...
read to 0xffff... of 4 bytes by task 5678 on cpu 0:
  my_other_func+0x15/0x30
  ...
```

### 16.4 KASAN — Kernel Address Sanitizer

Detects use-after-free, out-of-bounds access:

```bash
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y   # faster but larger binary

# In atomic context, KASAN is always active if enabled.
# It uses shadow memory to track allocation state.
```

### 16.5 ftrace for Atomic Context Analysis

```bash
# Trace hardirq enable/disable events:
echo 1 > /sys/kernel/debug/tracing/events/preemptirq/irq_enable/enable
echo 1 > /sys/kernel/debug/tracing/events/preemptirq/irq_disable/enable
cat /sys/kernel/debug/tracing/trace

# Trace preemption disable/enable:
echo 1 > /sys/kernel/debug/tracing/events/preemptirq/preempt_enable/enable
echo 1 > /sys/kernel/debug/tracing/events/preemptirq/preempt_disable/enable

# Measure interrupt latency:
echo irqsoff > /sys/kernel/debug/tracing/current_tracer
# ... trigger workload ...
cat /sys/kernel/debug/tracing/trace

# Measure preemption off latency:
echo preemptoff > /sys/kernel/debug/tracing/current_tracer
```

### 16.6 /proc Interfaces

```bash
# View spinlock statistics (CONFIG_DEBUG_SPINLOCK):
cat /proc/lock_stat

# lockdep stats:
cat /proc/lockdep_stats
cat /proc/lockdep           # full lock class list

# IRQ affinity:
cat /proc/interrupts
cat /proc/irq/*/affinity_hint

# softirq stats:
cat /proc/softirqs
```

---

## 17. PREEMPT_RT and Realtime Atomics

### 17.1 What PREEMPT_RT Changes

The `PREEMPT_RT` patchset (now merged into mainline >= 6.12) converts most spinlocks to **rt_mutex** (sleeping mutex with priority inheritance). This dramatically reduces worst-case latency.

Key changes:
```
spinlock_t     → rt_spinlock (backed by rt_mutex, preemptible)
rwlock_t       → rt_rwlock (preemptible)
local_bh_*     → BH is now a kernel thread, not a softirq on same CPU
Softirqs       → run in dedicated kthread (ksoftirqd/N) with RT priority
```

### 17.2 raw_spinlock_t vs. spinlock_t on RT

```c
/* raw_spinlock_t is ALWAYS a spinning lock, even on PREEMPT_RT:
   Use ONLY for: scheduler code, interrupt controllers, core timing */
raw_spinlock_t raw_lock;
raw_spin_lock(&raw_lock);       /* cannot sleep even on RT */
raw_spin_unlock(&raw_lock);

/* spinlock_t becomes a sleeping lock on PREEMPT_RT:
   Use for all other cases — allows RT task to preempt lock holder */
spinlock_t lock;
spin_lock(&lock);               /* on RT: may sleep with priority inheritance */
spin_unlock(&lock);
```

### 17.3 Priority Inheritance

```
Without PI (non-RT): Low-priority task holds spinlock, high-priority task spins.
                      High-priority task is effectively blocked by low-priority task.
                      → Priority inversion!

With PI (RT): rt_mutex gives the lock holder the priority of the highest-priority
              waiter temporarily. Low-priority task runs at high priority until
              it releases the lock. Then reverts to original priority.
              → No priority inversion.
```

### 17.4 IRQ Threads on PREEMPT_RT

```c
/* On PREEMPT_RT, hardirq handlers run in interrupt threads: */
request_threaded_irq(irq, primary_handler, thread_fn, flags, name, dev);

/* primary_handler: runs in true hardirq context (minimal, filters/acks HW) */
/* thread_fn: runs in kernel thread context (CAN sleep!) */

/* Even without PREEMPT_RT, threaded IRQs are best practice: */
static irqreturn_t my_primary(int irq, void *dev)
{
    /* minimal: ack interrupt, wake thread */
    return IRQ_WAKE_THREAD;
}

static irqreturn_t my_thread_fn(int irq, void *dev)
{
    /* runs in kthread context: can sleep, use mutexes, etc. */
    return IRQ_HANDLED;
}
```

---

## 18. Architecture View (ASCII)

```
LINUX ATOMIC CONTEXT HIERARCHY
================================

  ┌─────────────────────────────────────────────────────────────────────┐
  │                         NMI Context                                 │
  │  [in_nmi() == true]  Interrupts ALL disabled, preempt_count |= NMI │
  │  Only atomic_t / lock-free ring buffers safe                        │
  │  ┌──────────────────────────────────────────────────────────────┐   │
  │  │                    Hardirq Context                           │   │
  │  │  [in_hardirq() == true]  preempt_count HARDIRQ bits set     │   │
  │  │  GFP_ATOMIC alloc, no sleep, no mutex, no schedule()        │   │
  │  │  ┌───────────────────────────────────────────────────────┐  │   │
  │  │  │                 Softirq Context                       │  │   │
  │  │  │  [in_serving_softirq()] SOFTIRQ offset set            │  │   │
  │  │  │  Cannot sleep, GFP_ATOMIC only                        │  │   │
  │  │  │  Runs on same CPU after hardirq returns               │  │   │
  │  │  │  ┌────────────────────────────────────────────────┐   │  │   │
  │  │  │  │           Spinlock-Held Context               │   │  │   │
  │  │  │  │  [preempt_count PREEMPT bits set]             │   │  │   │
  │  │  │  │  spin_lock() / raw_spin_lock()                │   │  │   │
  │  │  │  │  Cannot sleep (non-RT kernels)                │   │  │   │
  │  │  │  │  GFP_ATOMIC only                              │   │  │   │
  │  │  │  │  ┌─────────────────────────────────────────┐  │   │  │   │
  │  │  │  │  │       RCU Read-Side Critical Section    │  │   │  │   │
  │  │  │  │  │  [rcu_read_lock()]                      │  │   │  │   │
  │  │  │  │  │  Preempt disabled (non-PREEMPT_RCU)     │  │   │  │   │
  │  │  │  │  │  Cannot call synchronize_rcu()          │  │   │  │   │
  │  │  │  │  │                                         │  │   │  │   │
  │  │  │  │  │  [rcu_read_unlock()]                    │  │   │  │   │
  │  │  │  │  └─────────────────────────────────────────┘  │   │  │   │
  │  │  │  └────────────────────────────────────────────────┘   │  │   │
  │  │  └───────────────────────────────────────────────────────┘  │   │
  │  └──────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────────────┐
  │                      Process Context                                │
  │  [!in_interrupt(), preempt_count == 0]                              │
  │  CAN sleep, CAN block, GFP_KERNEL, mutex_lock, schedule()           │
  │  Work queues, kernel threads, system calls                          │
  └─────────────────────────────────────────────────────────────────────┘


PREEMPT_COUNT BIT LAYOUT (32-bit field, per-CPU):
====================================================

  31         21  20  19    16  15         8  7          0
  +-----------+---+---+------+------------+------------+
  |  UNUSED   |   | N |HIRQ  |  SOFTIRQ   |  PREEMPT   |
  +-----------+---+---+------+------------+------------+
               ^   ^   ^
               |   |   +-- irq_enter() / irq_exit()
               |   +------ NMI_MASK (set/clear_nmi)
               +---------- (reserved)

  PREEMPT[7:0]  : incremented by preempt_disable(), spin_lock()
  SOFTIRQ[15:8] : incremented by local_bh_disable(), softirq entry
  HARDIRQ[19:16]: incremented by irq_enter()
  NMI_MASK[20]  : set by nmi_enter()


MEMORY ORDERING LAYERS:
=========================

  Application / User Space
       |
       | syscall / copy_to/from_user
       v
  Kernel Process Context
  [READ_ONCE / WRITE_ONCE / smp_mb() / smp_rmb() / smp_wmb()]
       |
       | hardirq entry (saves registers, preempt_count++)
       v
  Hardirq Handler
  [atomic_t, spinlock, local_irq_disable]
       |
       | (NMI arrives)
       v
  NMI Handler
  [atomic_t, atomic_cmpxchg, lock-free ring buffer only]
       |
       v
  CPU Pipeline + Cache Hierarchy
  [L1 → L2 → L3 → DRAM]
  [MESI coherency protocol across cores]
  [Hardware memory barriers: MFENCE/LFENCE/SFENCE on x86, DSB/DMB on ARM]
```

---

## 19. C Implementations

### 19.1 Lock-Free Stack Using atomic_t (Kernel-Style C)

```c
/* lf_stack.h — Lock-free Treiber stack using cmpxchg */
#ifndef LF_STACK_H
#define LF_STACK_H

#include <linux/atomic.h>
#include <linux/slab.h>
#include <linux/rcupdate.h>

struct lf_node {
    void            *data;
    struct lf_node  *next;     /* never modify after publish */
    struct rcu_head  rcu;      /* for RCU-deferred free */
};

struct lf_stack {
    struct lf_node __rcu *head;  /* RCU-protected pointer */
    atomic_long_t         count;
};

static inline void lf_stack_init(struct lf_stack *s)
{
    RCU_INIT_POINTER(s->head, NULL);
    atomic_long_set(&s->count, 0);
}

/*
 * lf_stack_push - push a node onto the stack
 * Safe from any context (atomic or not).
 * Uses compare-and-swap loop.
 */
static inline void lf_stack_push(struct lf_stack *s, struct lf_node *node)
{
    struct lf_node *old_head;

    do {
        old_head = rcu_dereference_raw(s->head);
        node->next = old_head;
        /*
         * smp_store_release inside rcu_assign_pointer ensures
         * node->next is visible before the pointer update.
         */
    } while (cmpxchg((struct lf_node **)&s->head, old_head, node) != old_head);

    atomic_long_inc(&s->count);
}

/*
 * lf_stack_pop - pop a node from the stack
 * Returns NULL if empty. Safe from atomic context.
 * NOTE: Uses cmpxchg — ABA problem is avoided by never reusing addresses
 * before an RCU grace period (handled by caller via kfree_rcu).
 */
static inline struct lf_node *lf_stack_pop(struct lf_stack *s)
{
    struct lf_node *old_head, *next;

    rcu_read_lock();
    do {
        old_head = rcu_dereference(s->head);
        if (!old_head) {
            rcu_read_unlock();
            return NULL;
        }
        next = old_head->next;
    } while (cmpxchg((struct lf_node **)&s->head, old_head, next) != old_head);
    rcu_read_unlock();

    atomic_long_dec(&s->count);
    return old_head;
}

#endif /* LF_STACK_H */
```

### 19.2 IRQ-Safe Reference Counter

```c
/* refcount.c — demonstrates atomic refcount with cleanup callback */
#include <linux/atomic.h>
#include <linux/slab.h>
#include <linux/workqueue.h>

struct my_object {
    refcount_t      refs;        /* kernel's safe refcount (no overflow) */
    struct work_struct destroy_work;
    char            data[256];
};

static void my_object_destroy(struct work_struct *work)
{
    struct my_object *obj = container_of(work, struct my_object, destroy_work);
    /* Process context — can sleep, free memory etc. */
    pr_info("destroying object %p\n", obj);
    kfree(obj);
}

static struct my_object *my_object_alloc(void)
{
    struct my_object *obj = kzalloc(sizeof(*obj), GFP_KERNEL);
    if (!obj)
        return NULL;
    refcount_set(&obj->refs, 1);
    INIT_WORK(&obj->destroy_work, my_object_destroy);
    return obj;
}

/* Safe to call from atomic context (hardirq, softirq, spinlock-held) */
static void my_object_get(struct my_object *obj)
{
    refcount_inc(&obj->refs);
}

/* Safe to call from atomic context */
static void my_object_put(struct my_object *obj)
{
    if (refcount_dec_and_test(&obj->refs)) {
        /* Schedule destruction in process context */
        schedule_work(&obj->destroy_work);
    }
}
```

### 19.3 Per-CPU Counter with Atomic Aggregation

```c
/* percpu_counter.c */
#include <linux/percpu.h>
#include <linux/atomic.h>
#include <linux/smp.h>
#include <linux/cpumask.h>

struct fast_counter {
    DEFINE_PER_CPU(s64, cpu_count);
    atomic64_t  global_count;  /* periodically synced */
    spinlock_t  sync_lock;
};

static void fc_init(struct fast_counter *fc)
{
    int cpu;
    for_each_possible_cpu(cpu)
        per_cpu(fc->cpu_count, cpu) = 0;
    atomic64_set(&fc->global_count, 0);
    spin_lock_init(&fc->sync_lock);
}

/* Call from any context (atomic safe via preempt disable): */
static void fc_add(struct fast_counter *fc, s64 delta)
{
    this_cpu_add(fc->cpu_count, delta);  /* disables preemption internally */
}

/* Call from process context to read accurate total: */
static s64 fc_read(struct fast_counter *fc)
{
    s64 total = atomic64_read(&fc->global_count);
    int cpu;
    for_each_possible_cpu(cpu)
        total += per_cpu(fc->cpu_count, cpu);
    return total;
}

/* Sync per-CPU counts to global (call periodically from process context): */
static void fc_sync(struct fast_counter *fc)
{
    s64 local;
    int cpu;

    for_each_possible_cpu(cpu) {
        local = per_cpu(fc->cpu_count, cpu);
        if (local == 0)
            continue;
        /* xchg is atomic: read and zero in one operation */
        local = xchg(per_cpu_ptr(&fc->cpu_count, cpu), 0);
        atomic64_add(local, &fc->global_count);
    }
}
```

### 19.4 Seqlock-Protected Timestamp

```c
/* seqlock_time.c — seqlock protecting a compound timestamp */
#include <linux/seqlock.h>
#include <linux/time64.h>
#include <linux/ktime.h>

struct protected_time {
    seqlock_t   lock;
    ktime_t     monotonic;
    ktime_t     realtime;
    u64         cycles;
};

static struct protected_time global_time;

/* Writer (called from timer interrupt — atomic context OK with seqlock): */
static void update_global_time(ktime_t mono, ktime_t real, u64 cyc)
{
    write_seqlock(&global_time.lock);
    global_time.monotonic = mono;
    global_time.realtime  = real;
    global_time.cycles    = cyc;
    write_sequnlock(&global_time.lock);
}

/* Reader (can be called from any context — no lock held): */
static void read_global_time(ktime_t *mono, ktime_t *real, u64 *cyc)
{
    unsigned int seq;
    do {
        seq = read_seqbegin(&global_time.lock);
        *mono = global_time.monotonic;
        *real = global_time.realtime;
        *cyc  = global_time.cycles;
    } while (read_seqretry(&global_time.lock, seq));
}
```

### 19.5 NMI-Safe Ring Buffer

```c
/* nmi_ringbuf.c — NMI-safe lock-free single-producer ring buffer */
#include <linux/atomic.h>
#include <linux/slab.h>
#include <linux/string.h>

#define NMI_RB_SIZE  (1 << 12)   /* must be power of 2: 4096 entries */
#define NMI_RB_MASK  (NMI_RB_SIZE - 1)

struct nmi_rb_entry {
    u64  timestamp;
    u32  type;
    u32  size;
    u8   data[56];   /* 64-byte total entry */
} __packed __aligned(64);

struct nmi_ring_buffer {
    atomic_t        head;    /* written by NMI handler (producer) */
    atomic_t        tail;    /* written by consumer (kthread) */
    struct nmi_rb_entry entries[NMI_RB_SIZE];
} ____cacheline_aligned;

DEFINE_PER_CPU(struct nmi_ring_buffer, nmi_rb);

/*
 * nmi_rb_write - write entry from NMI context
 * Returns 0 on success, -ENOSPC if full.
 */
static int nmi_rb_write(struct nmi_ring_buffer *rb,
                         u32 type, const void *data, u32 len)
{
    int head, tail, next;

    if (WARN_ON_ONCE(len > sizeof(rb->entries[0].data)))
        len = sizeof(rb->entries[0].data);

    head = atomic_read(&rb->head);
    tail = atomic_read(&rb->tail);

    /* Check space: circular buffer full when head + 1 == tail */
    if (((head + 1) & NMI_RB_MASK) == (tail & NMI_RB_MASK))
        return -ENOSPC;

    /* Write entry (NMI is single-producer per CPU, so no CAS needed) */
    rb->entries[head & NMI_RB_MASK].timestamp = ktime_get_mono_fast_ns();
    rb->entries[head & NMI_RB_MASK].type      = type;
    rb->entries[head & NMI_RB_MASK].size      = len;
    memcpy(rb->entries[head & NMI_RB_MASK].data, data, len);

    /* Publish: store head AFTER data (store-release) */
    next = (head + 1) & NMI_RB_MASK;
    atomic_set_release(&rb->head, next);

    return 0;
}

/*
 * nmi_rb_read - read entry from consumer (process context)
 * Returns 0 if empty.
 */
static int nmi_rb_read(struct nmi_ring_buffer *rb,
                        struct nmi_rb_entry *out)
{
    int head, tail;

    tail = atomic_read_acquire(&rb->tail);
    head = atomic_read(&rb->head);

    if (tail == head)
        return 0;   /* empty */

    *out = rb->entries[tail & NMI_RB_MASK];

    /* Advance tail */
    atomic_set(&rb->tail, (tail + 1) & NMI_RB_MASK);
    return 1;
}
```

### 19.6 Compile-Time Assertions for Atomic Safety

```c
/* Useful macros for documenting and verifying atomic context requirements */
#include <linux/preempt.h>

/* Assert we are in atomic context: */
#define ASSERT_ATOMIC_CONTEXT()  \
    WARN_ON_ONCE(!in_atomic() && !irqs_disabled())

/* Assert we are NOT in atomic context: */
#define ASSERT_SLEEPABLE_CONTEXT() \
    might_sleep()

/* Assert holding specific lock: */
#define ASSERT_HOLDING(lock) \
    lockdep_assert_held(lock)

/* Assert not holding specific lock: */
#define ASSERT_NOT_HOLDING(lock) \
    lockdep_assert_not_held(lock)
```

---

## 20. Go Implementations

Go does not run in the Linux kernel, but understanding Go's runtime atomics and goroutine scheduler is essential for:
1. Writing Go code that calls into kernel via CGo/eBPF
2. Understanding Go's own memory model (analogous to Linux's)
3. Writing safe concurrent Go for userspace components (eBPF loaders, CNI plugins, etc.)

### 20.1 Go Memory Model Overview

Go's memory model (revised 2022) uses the C11 happens-before model:
- A `sync/atomic` store with `Release` semantics **synchronizes-with** a `Load` with `Acquire` semantics on the same variable
- Channel sends/receives establish happens-before relationships
- `sync.Mutex` Lock/Unlock establish happens-before

### 20.2 sync/atomic Package

```go
// atomic_demo.go — demonstrates Go atomic operations analogous to Linux kernel atomics
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"unsafe"
)

// ============================================================
// Basic atomic operations (analogous to kernel atomic_t)
// ============================================================

type AtomicCounter struct {
	_   [0]func() // prevent copying
	val int64
}

func (c *AtomicCounter) Add(delta int64) int64 {
	return atomic.AddInt64(&c.val, delta)
}

func (c *AtomicCounter) Load() int64 {
	return atomic.LoadInt64(&c.val)
}

func (c *AtomicCounter) Store(val int64) {
	atomic.StoreInt64(&c.val, val)
}

func (c *AtomicCounter) Swap(new int64) (old int64) {
	return atomic.SwapInt64(&c.val, new)
}

func (c *AtomicCounter) CompareAndSwap(old, new int64) bool {
	return atomic.CompareAndSwapInt64(&c.val, old, new)
}

// ============================================================
// Go 1.19+ atomic.Value for typed atomics (like atomic pointer in kernel)
// ============================================================

type Config struct {
	MaxConn int
	Timeout int
}

type AtomicConfig struct {
	val atomic.Pointer[Config] // Go 1.19+ generic atomic pointer
}

func (ac *AtomicConfig) Load() *Config {
	return ac.val.Load() // acquire semantics
}

func (ac *AtomicConfig) Store(cfg *Config) {
	ac.val.Store(cfg) // release semantics
}

// ============================================================
// Lock-free stack (Treiber stack) — analogous to kernel lf_stack
// ============================================================

type LFNode[T any] struct {
	data T
	next atomic.Pointer[LFNode[T]]
}

type LFStack[T any] struct {
	head  atomic.Pointer[LFNode[T]]
	count atomic.Int64
}

func (s *LFStack[T]) Push(data T) {
	node := &LFNode[T]{data: data}
	for {
		old := s.head.Load()
		node.next.Store(old)
		if s.head.CompareAndSwap(old, node) {
			s.count.Add(1)
			return
		}
		// CAS failed: another goroutine pushed; retry
	}
}

func (s *LFStack[T]) Pop() (T, bool) {
	for {
		old := s.head.Load()
		if old == nil {
			var zero T
			return zero, false
		}
		next := old.next.Load()
		if s.head.CompareAndSwap(old, next) {
			s.count.Add(-1)
			return old.data, true
		}
	}
}

// ============================================================
// Go 1.19 atomic.Int32/Int64/Uint32/Uint64/Uintptr/Bool/Pointer
// ============================================================

type SafeFlag struct {
	set atomic.Bool
}

func (f *SafeFlag) Set()      { f.set.Store(true) }
func (f *SafeFlag) Clear()    { f.set.Store(false) }
func (f *SafeFlag) IsSet() bool { return f.set.Load() }

// ============================================================
// Seqlock equivalent in Go (no kernel seqlock, but pattern applies)
// ============================================================

// GoSeqlock is a userspace seqlock using atomic operations.
// Equivalent to kernel seqcount_t.
type GoSeqlock struct {
	seq atomic.Uint64
}

type TimeSnapshot struct {
	Mono    int64
	Real    int64
	Cycles  uint64
}

type ProtectedTime struct {
	mu   GoSeqlock
	data TimeSnapshot
}

func (pt *ProtectedTime) Write(snap TimeSnapshot) {
	pt.mu.seq.Add(1) // seq now odd — write in progress
	// smp_wmb equivalent: Go compiler + runtime ensures visibility
	atomic.StoreInt64(&pt.data.Mono, snap.Mono)
	atomic.StoreInt64(&pt.data.Real, snap.Real)
	atomic.StoreUint64(&pt.data.Cycles, snap.Cycles)
	pt.mu.seq.Add(1) // seq now even — write complete
}

func (pt *ProtectedTime) Read() TimeSnapshot {
	var snap TimeSnapshot
	for {
		seq1 := pt.mu.seq.Load()
		if seq1&1 != 0 {
			// Write in progress — spin
			continue
		}
		snap.Mono = atomic.LoadInt64(&pt.data.Mono)
		snap.Real = atomic.LoadInt64(&pt.data.Real)
		snap.Cycles = atomic.LoadUint64(&pt.data.Cycles)
		seq2 := pt.mu.seq.Load()
		if seq1 == seq2 {
			break // consistent read
		}
		// seq changed during read — retry
	}
	return snap
}

// ============================================================
// Per-goroutine-safe rate limiter using atomic CAS
// (analogous to per-CPU counters)
// ============================================================

type TokenBucket struct {
	tokens    atomic.Int64
	maxTokens int64
	refillPer int64 // tokens per refill period
}

func NewTokenBucket(max, refill int64) *TokenBucket {
	tb := &TokenBucket{maxTokens: max, refillPer: refill}
	tb.tokens.Store(max)
	return tb
}

func (tb *TokenBucket) TryConsume(n int64) bool {
	for {
		cur := tb.tokens.Load()
		if cur < n {
			return false
		}
		if tb.tokens.CompareAndSwap(cur, cur-n) {
			return true
		}
	}
}

func (tb *TokenBucket) Refill() {
	for {
		cur := tb.tokens.Load()
		next := cur + tb.refillPer
		if next > tb.maxTokens {
			next = tb.maxTokens
		}
		if tb.tokens.CompareAndSwap(cur, next) {
			return
		}
	}
}

// ============================================================
// Go runtime goroutine preemption — analogous to kernel preempt_disable
// runtime.LockOSThread pins goroutine to OS thread
// ============================================================

func pinToOSThread(fn func()) {
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		// Pin this goroutine to its OS thread (analogous to per-CPU ops)
		// Needed when calling C code that uses thread-local storage,
		// or when working with kernel resources bound to a thread.
		// runtime.LockOSThread()
		// defer runtime.UnlockOSThread()
		fn()
	}()
	wg.Wait()
}

// ============================================================
// atomic.Value for RCU-like pointer swap
// ============================================================

type RCUPointer[T any] struct {
	p atomic.Pointer[T]
}

func (r *RCUPointer[T]) Load() *T {
	return r.p.Load() // atomic load with acquire semantics in Go
}

func (r *RCUPointer[T]) Store(newVal *T) {
	r.p.Store(newVal) // atomic store with release semantics
	// Go GC handles memory safety — no need for grace periods
	// (GC is the "grace period" mechanism for Go)
}

// ============================================================
// Demonstrating unsafe pointer atomics (advanced)
// ============================================================

func atomicPointerCAS(ptr *unsafe.Pointer, old, new unsafe.Pointer) bool {
	return atomic.CompareAndSwapPointer(ptr, old, new)
}

func main() {
	// Test LFStack
	var stack LFStack[int]
	for i := 0; i < 10; i++ {
		stack.Push(i)
	}
	for {
		v, ok := stack.Pop()
		if !ok {
			break
		}
		fmt.Printf("Popped: %d\n", v)
	}

	// Test ProtectedTime (seqlock equivalent)
	var pt ProtectedTime
	pt.Write(TimeSnapshot{Mono: 1000, Real: 2000, Cycles: 3000})
	snap := pt.Read()
	fmt.Printf("Snapshot: %+v\n", snap)

	// Test TokenBucket
	tb := NewTokenBucket(100, 10)
	fmt.Printf("Consumed 50: %v\n", tb.TryConsume(50))
	fmt.Printf("Consumed 60: %v\n", tb.TryConsume(60)) // should fail
}
```

### 20.3 Go eBPF Loader with Atomic Map Operations

```go
// ebpf_atomic.go — Go code interacting with Linux kernel via eBPF maps
// Uses cilium/ebpf library
// go get github.com/cilium/ebpf
package main

import (
	"fmt"
	"log"

	"github.com/cilium/ebpf"
)

// Demonstrates how Go interacts with kernel atomic operations via eBPF maps.
// The eBPF map operations (Update/Lookup/Delete) themselves are atomic at
// the map entry level when using BPF_EXIST / BPF_NOEXIST flags.

type PacketStats struct {
	RxPackets uint64
	RxBytes   uint64
	TxPackets uint64
	TxBytes   uint64
}

func readAtomicStats(m *ebpf.Map, cpuID uint32) (*PacketStats, error) {
	var stats PacketStats
	if err := m.Lookup(cpuID, &stats); err != nil {
		return nil, fmt.Errorf("map lookup: %w", err)
	}
	return &stats, nil
}

// Atomic increment of a per-CPU eBPF map entry
// (actual atomicity is guaranteed by the kernel's BPF map implementation)
func atomicIncrementCounter(m *ebpf.Map, key uint32, delta uint64) error {
	var current uint64
	// BPF_MAP_UPDATE_ELEM with BPF_EXIST is atomic at the kernel level
	if err := m.Lookup(key, &current); err != nil {
		current = 0
	}
	return m.Update(key, current+delta, ebpf.UpdateExist)
}

func main() {
	// This is a demonstration structure; actual usage requires
	// a loaded eBPF program with the map pinned or passed via fd.
	log.Println("eBPF atomic map operations demo")
	log.Println("Run with: sudo go run ebpf_atomic.go")
}
```

### 20.4 Go GOMAXPROCS and Scheduler Interaction

```go
// scheduler_awareness.go — understanding Go scheduler in context of kernel atomics
package main

import (
	"fmt"
	"runtime"
	"sync/atomic"
	"time"
)

// Go goroutines are multiplexed onto OS threads (M:N threading).
// When a goroutine calls a blocking syscall, the Go runtime:
// 1. Parks the goroutine
// 2. Hands the OS thread (M) to the scheduler
// 3. Other goroutines run on other Ms
//
// This is analogous to how Linux kernel process context can sleep:
// the CPU is released to other tasks.
//
// Non-preemptible sections in Go:
// - Code between runtime.LockOSThread() and UnlockOSThread()
// - Goroutines in system calls (not yielding to Go scheduler)
// - CGo calls (cross into C → no goroutine preemption)

type GoSchedulerStats struct {
	goroutines atomic.Int64
	switches   atomic.Int64
}

func demonstrateSchedulerInteraction() {
	stats := &GoSchedulerStats{}
	
	// Go 1.14+ async preemption: goroutines are preempted at safe points
	// even without function calls (via SIGURG signal on Linux).
	// This is analogous to kernel's CONFIG_PREEMPT.
	
	done := make(chan struct{})
	
	// Spawn goroutines that track scheduler behavior
	for i := 0; i < runtime.GOMAXPROCS(0); i++ {
		stats.goroutines.Add(1)
		go func(id int) {
			defer stats.goroutines.Add(-1)
			for {
				select {
				case <-done:
					return
				default:
					// Yield to scheduler (analogous to cpu_relax() + schedule())
					runtime.Gosched()
					stats.switches.Add(1)
				}
			}
		}(i)
	}
	
	time.Sleep(100 * time.Millisecond)
	close(done)
	time.Sleep(10 * time.Millisecond)
	
	fmt.Printf("Scheduler switches: %d\n", stats.switches.Load())
	fmt.Printf("Active goroutines: %d\n", stats.goroutines.Load())
}

func main() {
	fmt.Printf("GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))
	fmt.Printf("NumCPU: %d\n", runtime.NumCPU())
	demonstrateSchedulerInteraction()
}
```

---

## 21. Rust Implementations

### 21.1 Rust Memory Model and Ordering

Rust uses C11 memory ordering semantics via `std::sync::atomic::Ordering`:

```
Relaxed  — no ordering constraints; just atomicity (like kernel's atomic_read/add without barriers)
Acquire  — like smp_load_acquire(); subsequent accesses cannot move before this load
Release  — like smp_store_release(); prior accesses cannot move after this store
AcqRel   — both Acquire and Release; for read-modify-write ops (like atomic_xchg)
SeqCst   — sequentially consistent; like smp_mb() + operation + smp_mb()
```

### 21.2 Core Atomic Types in Rust

```rust
// rust_atomics.rs — comprehensive atomic operations in Rust
use std::sync::atomic::{
    AtomicBool, AtomicI32, AtomicI64, AtomicIsize, 
    AtomicPtr, AtomicU32, AtomicU64, AtomicUsize,
    Ordering::{self, *},
};
use std::sync::Arc;
use std::thread;
use std::ptr;

// ============================================================
// Basic atomic integer (analogous to kernel atomic_t)
// ============================================================

struct AtomicCounter {
    val: AtomicI64,
}

impl AtomicCounter {
    const fn new(initial: i64) -> Self {
        Self { val: AtomicI64::new(initial) }
    }
    
    // Relaxed: just atomicity, no ordering (like atomic_add in kernel with no barrier)
    fn add_relaxed(&self, delta: i64) {
        self.val.fetch_add(delta, Relaxed);
    }
    
    // Release: analogous to smp_store_release equivalent
    fn store_release(&self, val: i64) {
        self.val.store(val, Release);
    }
    
    // Acquire: analogous to smp_load_acquire
    fn load_acquire(&self) -> i64 {
        self.val.load(Acquire)
    }
    
    // Full barrier: analogous to atomic_add_return (full smp_mb)
    fn fetch_add_seqcst(&self, delta: i64) -> i64 {
        self.val.fetch_add(delta, SeqCst)
    }
    
    // Compare-and-swap: analogous to atomic_cmpxchg
    fn cas(&self, expected: i64, desired: i64) -> Result<i64, i64> {
        self.val.compare_exchange(expected, desired, AcqRel, Acquire)
    }
    
    // Weak CAS (may spuriously fail — valid for loops, maps to LL/SC on ARM)
    fn cas_weak(&self, expected: i64, desired: i64) -> Result<i64, i64> {
        self.val.compare_exchange_weak(expected, desired, AcqRel, Acquire)
    }
}

// ============================================================
// Seqlock in Rust (no_std compatible pattern)
// ============================================================

use std::cell::UnsafeCell;

struct SeqLock<T: Copy> {
    seq:  AtomicU64,
    data: UnsafeCell<T>,
}

// SAFETY: SeqLock implements its own synchronization
unsafe impl<T: Copy + Send> Sync for SeqLock<T> {}
unsafe impl<T: Copy + Send> Send for SeqLock<T> {}

impl<T: Copy> SeqLock<T> {
    pub fn new(data: T) -> Self {
        Self {
            seq: AtomicU64::new(0),
            data: UnsafeCell::new(data),
        }
    }
    
    // Writer: increments seq to odd (write-in-progress), writes, increments to even
    pub fn write(&self, new_data: T) {
        // Mark write-in-progress (seq → odd)
        self.seq.fetch_add(1, Release);
        
        // SAFETY: we have exclusive write access via the seqlock protocol
        unsafe { *self.data.get() = new_data; }
        
        // smp_wmb + seq increment to even (write complete)
        self.seq.fetch_add(1, Release);
    }
    
    // Reader: retry if seq was odd or changed during read
    pub fn read(&self) -> T {
        loop {
            let seq1 = self.seq.load(Acquire);
            
            // Spin if writer is active (odd seq)
            if seq1 & 1 != 0 {
                std::hint::spin_loop(); // analogous to cpu_relax()
                continue;
            }
            
            // SAFETY: no writer active (seq is even), copy data
            let data = unsafe { *self.data.get() };
            
            let seq2 = self.seq.load(Acquire);
            
            if seq1 == seq2 {
                return data; // consistent read
            }
            // Retry: seq changed during read
        }
    }
}

// ============================================================
// Lock-free Treiber stack in Rust (analogous to kernel lf_stack)
// ============================================================

use std::mem::ManuallyDrop;

struct Node<T> {
    data: ManuallyDrop<T>,
    next: AtomicPtr<Node<T>>,
}

struct TreiberStack<T> {
    head: AtomicPtr<Node<T>>,
    count: AtomicUsize,
}

impl<T> TreiberStack<T> {
    pub fn new() -> Self {
        Self {
            head: AtomicPtr::new(ptr::null_mut()),
            count: AtomicUsize::new(0),
        }
    }
    
    pub fn push(&self, data: T) {
        let node = Box::into_raw(Box::new(Node {
            data: ManuallyDrop::new(data),
            next: AtomicPtr::new(ptr::null_mut()),
        }));
        
        loop {
            let old_head = self.head.load(Relaxed);
            // SAFETY: node is uniquely owned at this point
            unsafe { (*node).next.store(old_head, Relaxed); }
            
            match self.head.compare_exchange_weak(old_head, node, Release, Relaxed) {
                Ok(_) => {
                    self.count.fetch_add(1, Relaxed);
                    return;
                }
                Err(_) => {
                    // CAS failed — retry (another thread pushed)
                    std::hint::spin_loop();
                }
            }
        }
    }
    
    pub fn pop(&self) -> Option<T> {
        loop {
            let old_head = self.head.load(Acquire);
            if old_head.is_null() {
                return None;
            }
            
            // SAFETY: old_head is non-null and was published with Release
            let next = unsafe { (*old_head).next.load(Relaxed) };
            
            match self.head.compare_exchange_weak(old_head, next, AcqRel, Acquire) {
                Ok(_) => {
                    self.count.fetch_sub(1, Relaxed);
                    // SAFETY: We have exclusive ownership of this node now
                    let data = unsafe { ManuallyDrop::take(&mut (*old_head).data) };
                    // SAFETY: Reconstruct Box so it's properly dropped
                    unsafe { drop(Box::from_raw(old_head)); }
                    return Some(data);
                }
                Err(_) => {
                    std::hint::spin_loop();
                }
            }
        }
    }
    
    pub fn len(&self) -> usize {
        self.count.load(Relaxed)
    }
    
    pub fn is_empty(&self) -> bool {
        self.head.load(Relaxed).is_null()
    }
}

// SAFETY: TreiberStack is safe to share across threads
unsafe impl<T: Send> Sync for TreiberStack<T> {}
unsafe impl<T: Send> Send for TreiberStack<T> {}

impl<T> Drop for TreiberStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}

// ============================================================
// Spinlock implementation in Rust (for no_std / embedded / kernel)
// ============================================================

pub struct SpinLock<T> {
    locked: AtomicBool,
    data:   UnsafeCell<T>,
}

pub struct SpinLockGuard<'a, T> {
    lock: &'a SpinLock<T>,
}

impl<T> SpinLock<T> {
    pub const fn new(data: T) -> Self {
        Self {
            locked: AtomicBool::new(false),
            data:   UnsafeCell::new(data),
        }
    }
    
    pub fn lock(&self) -> SpinLockGuard<'_, T> {
        // Acquire semantics: subsequent accesses cannot move before this
        while self.locked.compare_exchange_weak(false, true, Acquire, Relaxed).is_err() {
            // Spin with cpu_relax() equivalent
            while self.locked.load(Relaxed) {
                std::hint::spin_loop();
            }
        }
        SpinLockGuard { lock: self }
    }
    
    pub fn try_lock(&self) -> Option<SpinLockGuard<'_, T>> {
        if self.locked.compare_exchange(false, true, Acquire, Relaxed).is_ok() {
            Some(SpinLockGuard { lock: self })
        } else {
            None
        }
    }
}

impl<T> std::ops::Deref for SpinLockGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: we hold the lock
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> std::ops::DerefMut for SpinLockGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        // SAFETY: we hold the lock exclusively
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for SpinLockGuard<'_, T> {
    fn drop(&mut self) {
        // Release: prior accesses cannot move after this store
        self.lock.locked.store(false, Release);
    }
}

unsafe impl<T: Send> Sync for SpinLock<T> {}
unsafe impl<T: Send> Send for SpinLock<T> {}

// ============================================================
// Per-thread (pseudo per-CPU) counter in Rust using thread_local
// ============================================================

use std::cell::Cell;

thread_local! {
    static THREAD_COUNTER: Cell<u64> = Cell::new(0);
}

struct PerThreadCounter {
    global: AtomicU64,
}

impl PerThreadCounter {
    pub const fn new() -> Self {
        Self { global: AtomicU64::new(0) }
    }
    
    // Called from any thread — updates thread-local first (no atomic needed)
    pub fn inc(&self) {
        THREAD_COUNTER.with(|c| c.set(c.get() + 1));
    }
    
    // Sync thread-local to global (called periodically)
    pub fn sync(&self) {
        THREAD_COUNTER.with(|c| {
            let local = c.get();
            if local > 0 {
                self.global.fetch_add(local, Relaxed);
                c.set(0);
            }
        });
    }
    
    // Read global (approximate — thread-local values not included)
    pub fn read_approx(&self) -> u64 {
        self.global.load(Relaxed)
    }
}

// ============================================================
// Main test
// ============================================================

fn main() {
    // Test SeqLock
    let sl = Arc::new(SeqLock::new(42i32));
    let sl_r = sl.clone();
    
    let reader = thread::spawn(move || {
        for _ in 0..100 {
            let v = sl_r.read();
            println!("Read: {}", v);
        }
    });
    
    for i in 0..10 {
        sl.write(i * 10);
    }
    reader.join().unwrap();
    
    // Test TreiberStack
    let stack = Arc::new(TreiberStack::<i32>::new());
    let mut handles = vec![];
    
    for i in 0..4 {
        let s = stack.clone();
        handles.push(thread::spawn(move || {
            for j in 0..100 {
                s.push(i * 100 + j);
            }
        }));
    }
    for h in handles { h.join().unwrap(); }
    
    let mut count = 0;
    while stack.pop().is_some() { count += 1; }
    println!("Popped {} items from TreiberStack (expected 400)", count);
    
    // Test SpinLock
    let spin = Arc::new(SpinLock::new(0i64));
    let mut threads = vec![];
    for _ in 0..8 {
        let s = spin.clone();
        threads.push(thread::spawn(move || {
            for _ in 0..10000 {
                *s.lock() += 1;
            }
        }));
    }
    for t in threads { t.join().unwrap(); }
    println!("SpinLock final value: {} (expected 80000)", *spin.lock());
}
```

### 21.3 Rust in the Linux Kernel (rust for linux)

```rust
// kernel_module.rs — Rust kernel module demonstrating atomic context
// Requires: CONFIG_RUST=y, rust-for-linux kernel

// This is illustrative — actual kernel Rust API is in kernel:: crate

use kernel::prelude::*;
use kernel::sync::{SpinLock, UniqueArc};
use core::sync::atomic::{AtomicU64, Ordering};

module! {
    type: MyAtomicModule,
    name: "my_atomic",
    author: "Engineer",
    description: "Atomic context demo in Rust kernel module",
    license: "GPL",
}

struct MyAtomicModule {
    irq_count:  AtomicU64,
    data:       SpinLock<MyData>,
}

struct MyData {
    value: u64,
    flag:  bool,
}

impl kernel::Module for MyAtomicModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("MyAtomicModule: init\n");
        
        let data = SpinLock::new(MyData { value: 0, flag: false });
        
        Ok(MyAtomicModule {
            irq_count: AtomicU64::new(0),
            data,
        })
    }
}

impl MyAtomicModule {
    // This would be called from an IRQ handler (atomic context)
    fn handle_irq(&self) {
        // Atomic increment — safe in any context
        let count = self.irq_count.fetch_add(1, Ordering::Relaxed);
        pr_debug!("IRQ #{}\n", count);
        
        // SpinLock::lock() in kernel Rust disables preemption (and optionally IRQs)
        // kernel::sync::SpinLockIrqSave would save/restore IRQ state
        let mut guard = self.data.lock();
        guard.value += 1;
        guard.flag = count & 1 == 0;
        // guard dropped here — spinlock released, preemption re-enabled
    }
}

impl Drop for MyAtomicModule {
    fn drop(&mut self) {
        pr_info!("MyAtomicModule: exit, irq_count={}\n",
                 self.irq_count.load(Ordering::Relaxed));
    }
}
```

### 21.4 Rust no_std Atomic Ring Buffer (Kernel-Portable)

```rust
// ring_buffer.rs — no_std atomic ring buffer usable in kernel Rust modules
#![no_std]

use core::sync::atomic::{AtomicUsize, Ordering::*};
use core::mem::MaybeUninit;
use core::cell::UnsafeCell;

/// Lock-free Single-Producer Single-Consumer (SPSC) ring buffer.
/// - Producer (writer) owns the tail.
/// - Consumer (reader) owns the head.
/// - Safe from different contexts (e.g., IRQ produces, process consumes).
pub struct SpscRingBuffer<T, const N: usize> {
    head:    AtomicUsize,  // consumer index
    _pad1:   [u8; 64 - core::mem::size_of::<AtomicUsize>()],
    tail:    AtomicUsize,  // producer index
    _pad2:   [u8; 64 - core::mem::size_of::<AtomicUsize>()],
    buffer:  [UnsafeCell<MaybeUninit<T>>; N],
}

// SAFETY: SpscRingBuffer provides its own synchronization for T: Send
unsafe impl<T: Send, const N: usize> Sync for SpscRingBuffer<T, N> {}
unsafe impl<T: Send, const N: usize> Send for SpscRingBuffer<T, N> {}

impl<T: Copy, const N: usize> SpscRingBuffer<T, N> {
    const ASSERT_POW2: () = assert!(N.is_power_of_two(), "N must be power of 2");
    const MASK: usize = N - 1;
    
    pub const fn new() -> Self {
        // SAFETY: MaybeUninit is always valid uninitialized
        Self {
            head:   AtomicUsize::new(0),
            _pad1:  [0u8; 64 - core::mem::size_of::<AtomicUsize>()],
            tail:   AtomicUsize::new(0),
            _pad2:  [0u8; 64 - core::mem::size_of::<AtomicUsize>()],
            buffer: unsafe { MaybeUninit::uninit().assume_init() },
        }
    }
    
    /// Push from producer (e.g., IRQ handler). Returns false if full.
    /// Only one producer may call this at a time.
    pub fn push(&self, item: T) -> bool {
        let tail = self.tail.load(Relaxed);
        let next_tail = (tail + 1) & Self::MASK;
        
        // Acquire: read head with acquire so we see consumer's head updates
        let head = self.head.load(Acquire);
        
        if next_tail == head {
            return false; // buffer full
        }
        
        // Write item — producer owns this slot
        unsafe {
            (*self.buffer[tail].get()).write(item);
        }
        
        // Release: publish tail with release so consumer sees the written data
        self.tail.store(next_tail, Release);
        true
    }
    
    /// Pop from consumer (e.g., process context). Returns None if empty.
    /// Only one consumer may call this at a time.
    pub fn pop(&self) -> Option<T> {
        let head = self.head.load(Relaxed);
        
        // Acquire: read tail with acquire so we see producer's written data
        let tail = self.tail.load(Acquire);
        
        if head == tail {
            return None; // buffer empty
        }
        
        // Read item — consumer owns this slot
        let item = unsafe {
            (*self.buffer[head].get()).assume_init_read()
        };
        
        // Release: advance head so producer sees freed slot
        self.head.store((head + 1) & Self::MASK, Release);
        Some(item)
    }
    
    /// Number of items available to read (approximate).
    pub fn len(&self) -> usize {
        let head = self.head.load(Relaxed);
        let tail = self.tail.load(Relaxed);
        tail.wrapping_sub(head) & Self::MASK
    }
    
    pub fn is_empty(&self) -> bool {
        self.head.load(Relaxed) == self.tail.load(Relaxed)
    }
    
    pub fn is_full(&self) -> bool {
        let head = self.head.load(Relaxed);
        let tail = self.tail.load(Relaxed);
        ((tail + 1) & Self::MASK) == head
    }
}

impl<T: Copy, const N: usize> Drop for SpscRingBuffer<T, N> {
    fn drop(&mut self) {
        // Drain remaining items to properly drop T values
        while self.pop().is_some() {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_spsc() {
        let rb = SpscRingBuffer::<u32, 16>::new();
        assert!(rb.is_empty());
        
        assert!(rb.push(1));
        assert!(rb.push(2));
        assert!(rb.push(3));
        
        assert_eq!(rb.pop(), Some(1));
        assert_eq!(rb.pop(), Some(2));
        assert_eq!(rb.pop(), Some(3));
        assert_eq!(rb.pop(), None);
    }
    
    #[test]
    fn test_full_buffer() {
        let rb = SpscRingBuffer::<u32, 4>::new(); // 4 slots, but 3 usable (SPSC invariant)
        assert!(rb.push(1));
        assert!(rb.push(2));
        assert!(rb.push(3));
        assert!(!rb.push(4)); // full (next_tail == head)
    }
}
```

---

## 22. Threat Model & Mitigations

### 22.1 Threat: Race Condition via Missing Atomics

| Threat | Unprotected concurrent read-modify-write of a shared variable |
|---|---|
| **Impact** | Silent data corruption, counter underflow/overflow, use-after-free |
| **Detection** | KCSAN, ThreadSanitizer (for userspace), code review |
| **Mitigation** | Use `atomic_t` / `READ_ONCE` / `WRITE_ONCE` for shared scalar fields; use appropriate locks for compound data |

### 22.2 Threat: Sleep-in-Atomic Deadlock

| Threat | Calling sleeping primitive (mutex, kmalloc GFP_KERNEL) while holding spinlock |
|---|---|
| **Impact** | CPU hangs, system deadlock |
| **Detection** | `CONFIG_DEBUG_ATOMIC_SLEEP=y`, lockdep, `might_sleep()` |
| **Mitigation** | Use `GFP_ATOMIC` in atomic context; use work queues for deferred sleeping work; audit all lock-held paths |

### 22.3 Threat: Lock Order Inversion (Deadlock)

| Threat | Two CPUs acquire locks A and B in opposite orders |
|---|---|
| **Impact** | Permanent deadlock (neither CPU progresses) |
| **Detection** | lockdep (detects at first attempt, not just when deadlock occurs) |
| **Mitigation** | Establish global lock ordering; use `lockdep_set_class()` for documentation; use `trylock` with backoff where order cannot be fixed |

### 22.4 Threat: ABA Problem in Lock-Free Algorithms

| Threat | CAS sees "A", another thread frees A, allocates new B at same address, original CAS succeeds incorrectly |
|---|---|
| **Impact** | Data corruption, use-after-free |
| **Detection** | Very hard — intermittent, race-condition-dependent |
| **Mitigation** | Never reuse memory addresses before a grace period (RCU); use tagged pointers (hazard pointers); use epoch-based reclamation |

### 22.5 Threat: False Sharing (Performance + Correctness)

| Threat | Two CPUs write different fields on the same cache line |
|---|---|
| **Impact** | Severe performance degradation (cache thrashing); no correctness issue if properly atomic |
| **Detection** | `perf stat -e cache-misses`, `perf c2c` (cache-to-cache) |
| **Mitigation** | `____cacheline_aligned_in_smp` padding; separate hot/cold data; per-CPU counters |

### 22.6 Threat: Missing Memory Barrier

| Threat | Code relies on memory ordering that the hardware does not guarantee |
|---|---|
| **Impact** | Data seen out-of-order; initialization code appears uninitialized to another CPU |
| **Detection** | KCSAN, formal verification (herd7), manual review on weak-memory architectures |
| **Mitigation** | Use `smp_store_release`/`smp_load_acquire` pairs; prefer `atomic_*` APIs which include proper barriers; test on ARM64/POWER not just x86 |

### 22.7 Threat: NMI Stack Overflow

| Threat | NMI handler uses excessive stack space; overflows into adjacent memory |
|---|---|
| **Impact** | Memory corruption, kernel crash |
| **Detection** | Stack canaries (`CONFIG_STACK_PROTECTOR_STRONG`), KASAN |
| **Mitigation** | Keep NMI handlers minimal; use dedicated NMI stack (x86 has IST for NMI); verify stack usage with `scripts/stackusage` |

### 22.8 Threat: Interrupt Latency / Starvation

| Threat | Long atomic sections delay interrupt servicing |
|---|---|
| **Impact** | Missed interrupts, high latency, NMI watchdog triggers |
| **Detection** | `irqsoff` tracer, `/proc/irq/*/spurious`, perf |
| **Mitigation** | Keep critical sections < 1µs; use PREEMPT_RT for latency requirements; defer work to softirq/workqueue |

---

## 23. Testing, Fuzzing & Benchmarking

### 23.1 Kernel Testing with KUnit

```bash
# Enable KUnit in kernel:
CONFIG_KUNIT=y
CONFIG_KUNIT_DEBUGFS=y

# Write atomic tests:
```

```c
/* atomic_test.c — KUnit tests for atomic context code */
#include <kunit/test.h>
#include <linux/atomic.h>
#include <linux/spinlock.h>

static void test_atomic_add_return(struct kunit *test)
{
    atomic_t v = ATOMIC_INIT(0);
    int result = atomic_add_return(5, &v);
    KUNIT_EXPECT_EQ(test, result, 5);
    KUNIT_EXPECT_EQ(test, atomic_read(&v), 5);
}

static void test_atomic_cmpxchg(struct kunit *test)
{
    atomic_t v = ATOMIC_INIT(10);
    int old = atomic_cmpxchg(&v, 10, 20);
    KUNIT_EXPECT_EQ(test, old, 10);
    KUNIT_EXPECT_EQ(test, atomic_read(&v), 20);
    
    old = atomic_cmpxchg(&v, 10, 30); /* should fail — v is 20 */
    KUNIT_EXPECT_EQ(test, old, 20);
    KUNIT_EXPECT_EQ(test, atomic_read(&v), 20);
}

static void test_spinlock_basic(struct kunit *test)
{
    DEFINE_SPINLOCK(lock);
    int counter = 0;
    unsigned long flags;
    
    spin_lock_irqsave(&lock, flags);
    /* Verify we're in atomic context */
    KUNIT_EXPECT_TRUE(test, in_atomic());
    counter++;
    spin_unlock_irqrestore(&lock, flags);
    
    KUNIT_EXPECT_EQ(test, counter, 1);
    KUNIT_EXPECT_FALSE(test, in_atomic());
}

static struct kunit_case atomic_test_cases[] = {
    KUNIT_CASE(test_atomic_add_return),
    KUNIT_CASE(test_atomic_cmpxchg),
    KUNIT_CASE(test_spinlock_basic),
    {}
};

static struct kunit_suite atomic_test_suite = {
    .name  = "atomic_context_tests",
    .test_cases = atomic_test_cases,
};

kunit_test_suite(atomic_test_suite);
MODULE_LICENSE("GPL");
```

```bash
# Run KUnit tests:
./tools/testing/kunit/kunit.py run --kconfig_add CONFIG_KUNIT=y
# Or via sysfs after loading module:
cat /sys/kernel/debug/kunit/atomic_context_tests/results
```

### 23.2 Stress Testing with Kernel Lockup Detector

```bash
# CONFIG_LOCKUP_DETECTOR=y
# CONFIG_HARDLOCKUP_DETECTOR=y
# CONFIG_SOFTLOCKUP_DETECTOR=y

# Softlockup: fires if a CPU is in kernel mode for > kernel.watchdog_thresh seconds
# (default 10s) without scheduling

# Check watchdog:
cat /proc/sys/kernel/watchdog_thresh   # default 10 (seconds)
cat /proc/sys/kernel/watchdog          # 1=enabled
cat /proc/sys/kernel/nmi_watchdog      # 1=enabled (uses PMU NMI)

# Trigger artificial lockup (testing only):
echo KASAN > /sys/kernel/debug/provoke-crash/DIRECT  # various crash types
```

### 23.3 KCSAN Race Detection

```bash
# Build kernel with:
CONFIG_KCSAN=y
CONFIG_KCSAN_REPORT_RACE_UNKNOWN_ORIGIN=y

# Boot and run workloads. KCSAN reports to dmesg:
dmesg | grep "KCSAN: data-race"

# Run syzkaller (kernel fuzzer) with KCSAN enabled for automated race detection:
# https://github.com/google/syzkaller
```

### 23.4 Benchmarking Atomic Operations

```bash
# Use kernel's built-in locking micro-benchmarks:
# CONFIG_LOCK_TORTURE_TEST=y
modprobe locktorture torture_type=spin_lock nwriters_stress=8 nreaders_stress=8
cat /proc/sys/kernel/locktorture/stats

# Measure cache-to-cache atomic operations with perf:
perf stat -e \
    cache-references,cache-misses,\
    mem_inst_retired.all_loads,mem_inst_retired.all_stores \
    -- stress-ng --atomic 8 --timeout 10s

# Measure spinlock contention:
perf lock stat -a sleep 5
perf lock report
```

### 23.5 Rust Atomic Tests and Benchmarks

```bash
# Run tests:
cargo test -- --nocapture

# Run with sanitizers:
RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test  # ThreadSanitizer
RUSTFLAGS="-Zsanitizer=address" cargo +nightly test  # AddressSanitizer

# Benchmark with criterion:
cargo bench --bench atomic_bench
```

```rust
// benches/atomic_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::sync::atomic::{AtomicU64, Ordering::*};
use std::sync::Arc;
use std::thread;

fn bench_atomic_relaxed(c: &mut Criterion) {
    let counter = AtomicU64::new(0);
    c.bench_function("atomic_relaxed_inc", |b| {
        b.iter(|| {
            black_box(counter.fetch_add(1, Relaxed))
        })
    });
}

fn bench_atomic_seqcst(c: &mut Criterion) {
    let counter = AtomicU64::new(0);
    c.bench_function("atomic_seqcst_inc", |b| {
        b.iter(|| {
            black_box(counter.fetch_add(1, SeqCst))
        })
    });
}

fn bench_contended_atomic(c: &mut Criterion) {
    let mut group = c.benchmark_group("contended_atomic");
    
    for threads in [1, 2, 4, 8, 16] {
        group.bench_with_input(BenchmarkId::from_parameter(threads), &threads, |b, &t| {
            let counter = Arc::new(AtomicU64::new(0));
            b.iter_custom(|iters| {
                let start = std::time::Instant::now();
                let handles: Vec<_> = (0..t).map(|_| {
                    let c = counter.clone();
                    let n = iters / t as u64;
                    thread::spawn(move || {
                        for _ in 0..n {
                            c.fetch_add(1, Relaxed);
                        }
                    })
                }).collect();
                for h in handles { h.join().unwrap(); }
                start.elapsed()
            });
        });
    }
    group.finish();
}

criterion_group!(benches, bench_atomic_relaxed, bench_atomic_seqcst, bench_contended_atomic);
criterion_main!(benches);
```

### 23.6 Go Race Detector

```bash
# Build and run with race detector:
go build -race ./...
go test -race ./...

# Example output when race detected:
# ==================
# WARNING: DATA RACE
# Write at 0x00c0000b6010 by goroutine 8:
#   main.main.func1()
#       /tmp/race.go:12 +0x44
# Previous read at 0x00c0000b6010 by goroutine 7:
# ==================
```

---

## 24. Roll-out / Rollback Plan

### 24.1 Introducing New Atomic Synchronization in Production Kernel Code

```
Phase 1: Development & Review
  □ Implement with CONFIG_DEBUG_SPINLOCK, CONFIG_LOCKDEP, CONFIG_PROVE_LOCKING
  □ Run KUnit tests: ./tools/testing/kunit/kunit.py run
  □ Run lockdep analysis: boot under qemu with debug config
  □ Enable KCSAN and run stress tests: locktorture, rcutorture
  □ Get code review focused on: lock ordering, memory barriers, GFP flags
  
Phase 2: Staging/CI
  □ Run on ARM64 (weakest memory model in common use) — not just x86
  □ Run syzkaller for 24-48 hours against new code paths
  □ Enable NMI watchdog and check for lockups: /proc/sys/kernel/watchdog
  □ Profile for false sharing: perf c2c, perf mem
  
Phase 3: Canary Rollout
  □ Deploy to 1% of fleet; monitor:
     - /proc/softirqs (increasing too fast?)
     - /proc/interrupts (spurious count)
     - dmesg for lockdep warnings, BUG(), WARN()
     - kernel.panic_on_oops=1 for immediate detection
  □ Hold for 24-72 hours under production traffic
  
Phase 4: Full Rollout
  □ Gradual traffic increase: 1% → 10% → 50% → 100%
  □ Monitor atomic contention: perf lock stat
  □ Keep previous kernel version available for emergency kexec rollback

Rollback Triggers:
  □ Any lockdep warning in production
  □ Softlockup or hardlockup detected
  □ Unexpected increase in /proc/softirqs rate
  □ Any WARN() or BUG() in new code paths
  □ > 5% latency regression on lock-protected paths

Rollback Procedure:
  1. kexec into previous kernel (< 30 seconds downtime):
     kexec -l /boot/vmlinuz-previous --initrd=/boot/initrd-previous --reuse-cmdline
     kexec -e
  2. Or: grub reboot into previous kernel entry
  3. File immediate bug report with: dmesg output, lockdep dump, perf lock report
```

---

## 25. References

### Kernel Documentation (in-tree)

```
Documentation/memory-barriers.txt        — THE definitive memory barrier reference
Documentation/locking/spinlocks.rst      — Spinlock usage guide
Documentation/locking/locktypes.rst      — Lock type comparison
Documentation/locking/lockdep-design.txt — Lockdep internals
Documentation/locking/seqlock.rst        — Seqlock documentation
Documentation/RCU/                       — Complete RCU documentation tree
Documentation/core-api/atomic_ops.rst    — Atomic operation reference
Documentation/core-api/kernel-api.rst    — General kernel API
Documentation/driver-api/basics.rst      — IRQ, task, memory fundamentals
Documentation/cpu-freq/cpu-drivers.rst   — CPU-specific details
```

### Source Code References

```
include/linux/atomic.h              — Atomic type definitions
include/linux/spinlock.h            — Spinlock API
include/linux/spinlock_types.h      — Lock type definitions
include/linux/preempt.h             — preempt_count, in_atomic(), etc.
include/linux/rcupdate.h            — RCU core API
include/linux/seqlock.h             — Seqlock API
include/linux/percpu.h              — Per-CPU variable API
include/linux/interrupt.h           — IRQ, softirq, tasklet API
include/linux/workqueue.h           — Workqueue API
include/linux/mempool.h             — Memory pool API
include/asm-generic/barrier.h       — Generic memory barrier implementation
arch/x86/include/asm/barrier.h      — x86 barrier implementations
arch/arm64/include/asm/barrier.h    — ARM64 barrier implementations
kernel/locking/qspinlock.c          — Queued spinlock implementation
kernel/locking/lockdep.c            — Lockdep implementation
kernel/rcu/tree.c                   — Tree RCU implementation
kernel/softirq.c                    — Softirq implementation
```

### Books and Papers

```
"Linux Kernel Development" — Robert Love (3rd ed.) — Ch. 7, 8, 10
"Understanding the Linux Kernel" — Bovet & Cesati (3rd ed.) — Ch. 5, 11
"Linux Device Drivers" — Corbet, Rubini, Kroah-Hartman (3rd ed.) — Ch. 5
"Is Parallel Programming Hard?" — Paul McKenney — free: kernel.org/pub/linux/kernel/people/paulmck/perfbook/
"A Tutorial Introduction to the ARM and POWER Relaxed Memory Models" — Maranget et al.
"Herding Cats: Modelling, Simulation, Testing, and Data-Mining for Weak Memory" — Alglave et al.
"Memory Barriers: a Hardware View for Software Hackers" — Paul McKenney
"RCU Usage In the Linux Kernel: One Decade Later" — McKenney et al. (2013)
"Bounded Queues" — Dmitry Vyukov (lockfree.org)
"The Art of Multiprocessor Programming" — Herlihy & Shavit
```

### Online Resources

```
https://www.kernel.org/doc/html/latest/locking/
https://www.kernel.org/doc/html/latest/RCU/
https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0124r6.html  — C++ memory model (maps to Linux)
https://godbolt.org/  — Compiler Explorer: inspect generated atomic instructions
https://herd7.inria.fr/  — Formal memory model checker
https://github.com/google/syzkaller  — Kernel fuzzer (exercises atomic paths)
https://github.com/Rust-for-Linux/linux  — Rust in Linux kernel
https://doc.rust-lang.org/nomicon/atomics.html  — Rust atomics & memory model
https://marabos.nl/atomics/  — "Rust Atomics and Locks" (free online book)
```

---

## Next 3 Steps

1. **Instrument your kernel with KCSAN + lockdep**: Boot a debug kernel with `CONFIG_KCSAN=y CONFIG_PROVE_LOCKING=y CONFIG_DEBUG_ATOMIC_SLEEP=y` under QEMU/KVM (`qemu-system-x86_64 -kernel vmlinuz -append "kasan_multi_shot"`). Run `locktorture` and `rcutorture` for 30 minutes. Fix every WARN that appears before writing new code.

2. **Port the SPSC ring buffer to a kernel module**: Take the Rust `SpscRingBuffer` or C `nmi_ringbuf.c` above, write a `struct file_operations`-backed char device that lets a userspace process consume NMI/IRQ events written by a test IRQ handler. This forces you to practice the producer-consumer context boundary (NMI → process context) with real `perf mem` measurement.

3. **Run the Go + Rust benchmarks against each other**: Use the `criterion` benchmarks to measure `Relaxed` vs `AcqRel` vs `SeqCst` across 1, 2, 4, 8, 16 threads on your target hardware (especially on ARM64 if available). Compare `perf stat -e mem_inst_retired.all_stores` counts. Then re-run on x86_64 and observe how x86 TSO collapses the ordering cost differences.

**Summary**: The guide covers every layer of atomic context from hardware cache coherency (MESI) through the kernel's `preempt_count` bit layout, all the way to production-grade C, Go, and Rust implementations. Here's what's inside across 25 sections:

**Kernel Theory (Sections 1–17)**
- All execution contexts: process, hardirq, softirq, tasklet, NMI — with exact `in_*()` predicates and `preempt_count` bit-field layout (PREEMPT/SOFTIRQ/HARDIRQ/NMI bits)
- Hardware memory models (TSO vs weak), MESI coherency, false sharing, and every barrier: `smp_mb/rmb/wmb`, `smp_load_acquire`, `smp_store_release`, `READ_ONCE/WRITE_ONCE`
- Complete `atomic_t` / `atomic64_t` API with ordering semantics per-operation (relaxed vs acquire/release vs seqcst), including x86 `LOCK XADD` disassembly
- Queued spinlocks (MCS queue internals), rwlock, seqlock/seqcount, RCU (Tree/SRCU/grace period mechanics), per-CPU variables
- `GFP_ATOMIC` vs `GFP_KERNEL`, mempool, SLAB caches, and why `kmalloc` is unsafe in NMI
- PREEMPT_RT behavioral differences: `spinlock_t` → `rt_mutex`, threaded IRQs, priority inheritance

**Debugging (Section 16)**
- All Kconfig options: lockdep, KCSAN, KASAN, DEBUG_ATOMIC_SLEEP, PROVE_LOCKING
- ftrace `irqsoff`/`preemptoff` tracers, `perf lock stat`, `/proc/lock_stat`, `/proc/lockdep_stats`

**Implementations (Sections 19–21)**
- **C**: NMI-safe ring buffer, lock-free Treiber stack with RCU reclamation, per-CPU counter with atomic aggregation, seqlock-protected timestamp, IRQ-safe refcount
- **Go**: `sync/atomic` full API, generic lock-free Treiber stack, seqlock equivalent, token bucket CAS, eBPF map atomic interaction
- **Rust**: `Ordering` semantics mapped to kernel barriers, `SeqLock<T>` with `UnsafeCell`, `TreiberStack<T>` with hazard-pointer-safe pop, `SpinLock<T>` with RAII guard, `no_std` SPSC ring buffer with cache-line padding — plus Rust-for-Linux kernel module sketch

**Next 3 Steps** are at the bottom of the document.