# Spinlocks in Linux — A Complete, In-Depth Guide
> *From hardware primitives to kernel internals, with C and Rust implementations*

---

## Table of Contents

1. [Conceptual Foundation — What Is a Spinlock?](#1-conceptual-foundation)
2. [Hardware Prerequisites — Memory Model & Atomics](#2-hardware-prerequisites)
3. [The Anatomy of Busy-Waiting](#3-anatomy-of-busy-waiting)
4. [Compare-and-Swap: The Universal Primitive](#4-compare-and-swap)
5. [Test-and-Set vs Test-and-Test-and-Set](#5-test-and-set-vs-test-and-test-and-set)
6. [Memory Ordering — The Critical Dimension](#6-memory-ordering)
7. [Linux Kernel Spinlock Internals](#7-linux-kernel-spinlock-internals)
8. [Ticket Spinlocks — Fairness Guaranteed](#8-ticket-spinlocks)
9. [MCS Locks — Cache-Efficient Queuing](#9-mcs-locks)
10. [qspinlock — The Linux Default](#10-qspinlock)
11. [Read-Write Spinlocks](#11-read-write-spinlocks)
12. [IRQ-Safe Spinlocks](#12-irq-safe-spinlocks)
13. [Recursive vs Non-Recursive Spinlocks](#13-recursive-vs-non-recursive-spinlocks)
14. [Spinlock Pathologies — Deadlock, Livelock, Starvation](#14-spinlock-pathologies)
15. [NUMA Topology and Spinlock Performance](#15-numa-topology-and-performance)
16. [Spinlocks vs Mutexes vs Semaphores](#16-spinlocks-vs-mutexes-vs-semaphores)
17. [C Implementation — From Scratch to Production-Grade](#17-c-implementation)
18. [Rust Implementation — Safe Abstractions Over Unsafe Primitives](#18-rust-implementation)
19. [Debugging Spinlocks — Lockdep, KCSAN, and Beyond](#19-debugging-spinlocks)
20. [Performance Analysis and Benchmarking](#20-performance-analysis)
21. [Expert Mental Models](#21-expert-mental-models)

---

## 1. Conceptual Foundation

### What Is a Spinlock?

A **spinlock** is a synchronization primitive where a thread that cannot acquire the lock does not block or sleep — it **loops (spins) continuously**, re-testing the lock condition in a tight CPU loop, until the lock becomes available.

The name is literal: the thread spins in place, consuming CPU cycles while waiting. This is the fundamental characteristic that distinguishes spinlocks from all blocking synchronization primitives.

```
Thread A (holds lock)          Thread B (waiting)
─────────────────────          ──────────────────
[critical section]     ←────   while (lock == LOCKED) {}  // spinning
...                            while (lock == LOCKED) {}  // spinning
[release lock]    ──────────→  acquire lock
                               [critical section]
```

### The Core Trade-off

The design philosophy of a spinlock encodes a single, critical assumption:

> **The lock will be held for a very short duration — shorter than the cost of a context switch.**

If this assumption holds, spinning wastes fewer cycles than sleeping (which requires: saving context, scheduling another thread, context switching back, cache warming). If it does not hold, spinlocks are catastrophically wasteful — a spinning thread burns an entire CPU core doing nothing useful.

This is not just a performance concern. In the Linux kernel, spinlocks are the *only* synchronization primitive legal in interrupt context, because sleeping in an interrupt handler is impossible (there is no "thread" to put to sleep — interrupts are not scheduled entities).

### When Are Spinlocks Appropriate?

| Condition | Use Spinlock | Use Mutex/Sleep |
|-----------|:---:|:---:|
| Interrupt/NMI context | ✅ | ❌ (cannot sleep) |
| Critical section < few microseconds | ✅ | ✅ |
| Critical section > ~50 microseconds | ❌ | ✅ |
| Preemption must be disabled | ✅ | ❌ |
| User space | Rarely | ✅ |
| Kernel bottom-half (tasklets) | ✅ | ❌ |
| NUMA system, many waiters | ❌ (use MCS/qspinlock) | ✅ |

---

## 2. Hardware Prerequisites — Memory Model & Atomics

### Why Hardware Matters

You cannot understand spinlocks without understanding **what the CPU and memory subsystem actually do**. The gap between what the programmer writes and what the hardware executes is vast and filled with reordering, speculation, and caching.

### The Von Neumann Lie

Modern CPUs do not execute instructions in order. They maintain the *illusion* of in-order execution for a single thread through the **Program Order guarantee**, but this guarantee evaporates the moment multiple cores are involved.

### Store Buffers and Load Buffers

Each CPU core has:

- **Store Buffer**: Outgoing writes are queued here before being committed to the L1 cache. This allows the CPU to continue executing without waiting for slow cache operations.
- **Load Buffer / Invalidation Queue**: Incoming cache invalidations are queued. A core might read a stale value from its cache even after another core has written a new value, because the invalidation is still sitting in the queue.

```
Core 0                    Core 1
──────                    ──────
[Store Buffer]            [Store Buffer]
     │                         │
     ↓                         ↓
[L1 Cache] ←──── L2 ────→ [L1 Cache]
```

These buffers are the root cause of why atomics and memory barriers are necessary.

### The x86 Memory Model (TSO — Total Store Order)

x86 provides a relatively strong memory model called **Total Store Order**:
- Loads are not reordered with older loads
- Stores are not reordered with older stores
- Stores are not reordered with older loads
- **BUT: Loads CAN be reordered with older stores** (store-load reordering)

This means on x86, the only reordering you must guard against is a load seeing a value written *before* a preceding store from the same thread has become visible to other threads. This is the `StoreLoad` barrier.

### The ARM/RISC-V Memory Model (Weakly Ordered)

ARM uses a **weakly ordered** memory model. Almost any reordering is permitted unless explicitly forbidden. This is why spinlock implementations differ between x86 and ARM — x86 gets some guarantees "for free" from TSO, while ARM needs explicit barrier instructions everywhere.

### CPU Cache Coherence — MESI Protocol

Multiple cores share the same physical memory but have private L1/L2 caches. The **MESI protocol** keeps them coherent:

| State | Meaning |
|-------|---------|
| **M**odified | Cache line is dirty; only this core has it; must write-back |
| **E**xclusive | Cache line is clean; only this core has it |
| **S**hared | Cache line is in multiple caches in read-only mode |
| **I**nvalid | Cache line is stale; must fetch from memory or another cache |

**The critical implication for spinlocks**: When a cache line moves from `S` → `M` (a core takes exclusive ownership to write), all other cores that had it in `S` state receive an **invalidation message**. They must then re-fetch the cache line before they can read the new value. This cross-core invalidation is expensive — typically 50–300 nanoseconds on modern hardware.

A naive spinlock where all cores write to the same cache line continuously to try to acquire it causes a **cache line ping-pong storm** — the single cache line bounces between cores in Modified state at enormous cost. This is why MCS locks were invented.

---

## 3. The Anatomy of Busy-Waiting

### Naive Spin Loop

```c
// This is conceptually what spinning means
while (lock->value == LOCKED) {
    /* burn CPU cycles */
}
```

### The `PAUSE` Instruction (x86) / `YIELD` (ARM)

Modern ISAs provide hints to the pipeline that the current code is a spin loop:

- **x86**: `PAUSE` instruction — tells the CPU this is a speculative spin loop. Prevents memory order violations that would otherwise require pipeline flushes when the spin ends. Also reduces power consumption. Adds ~5–10 cycles of delay, which actually *improves* throughput by reducing bus contention.
- **ARM**: `YIELD` instruction — similar hint, also reduces power
- **RISC-V**: `pause` pseudo-instruction (maps to `fence` in some implementations)

Without `PAUSE`, the CPU speculatively executes beyond the spin loop, then must flush the pipeline when the memory order violation is detected. This causes severe slowdowns on Hyper-Threaded systems because the spinning logical core starves its sibling.

```c
// x86 spin with PAUSE
while (atomic_load(&lock->value) == LOCKED) {
    __asm__ volatile("pause" ::: "memory");
}
```

### Exponential Backoff

A more sophisticated strategy: instead of spinning as fast as possible, introduce increasing delays between retries:

```c
void spin_with_backoff(spinlock_t *lock) {
    int delay = 1;
    while (atomic_load_explicit(&lock->value, memory_order_acquire) == LOCKED) {
        for (int i = 0; i < delay; i++) {
            __asm__ volatile("pause" ::: "memory");
        }
        delay = (delay < MAX_BACKOFF) ? delay * 2 : MAX_BACKOFF;
    }
}
```

This reduces bus contention dramatically under high load, at the cost of slightly higher latency when the lock becomes immediately available.

---

## 4. Compare-and-Swap: The Universal Primitive

### CAS — The Foundation of Lock-Free and Lock-Based Synchronization

**Compare-and-Swap (CAS)** is the fundamental hardware atomic instruction upon which virtually all synchronization primitives are built:

```
CAS(address, expected, desired) → old_value:
  atomically {
    old = *address
    if old == expected:
      *address = desired
    return old
  }
```

The operation is **atomic** — the read-compare-write sequence cannot be interrupted by any other memory operation on any core.

### x86 Implementation

On x86, CAS is the `LOCK CMPXCHG` instruction:

```asm
; Compare [rdi] with rax, if equal, write rdx to [rdi]
lock cmpxchg [rdi], rdx
```

The `LOCK` prefix acquires the bus (or cache line lock on modern CPUs) for the duration of the instruction, making the entire read-modify-write sequence atomic.

### ARM Implementation (LDXR/STXR — Load-Link/Store-Conditional)

ARM does not have a native CAS. Instead it uses **LL/SC** (Load-Link/Store-Conditional):

```asm
.loop:
    ldaxr   w1, [x0]       // Load-Acquire-Exclusive: load and mark exclusive
    cmp     w1, w2         // Compare with expected
    b.ne    .fail          // If not equal, fail
    stlxr   w3, w4, [x0]  // Store-Release-Exclusive: store if exclusive still held
    cbnz    w3, .loop      // If store failed (exclusive lost), retry
.fail:
```

The **exclusive monitor** tracks whether any other core wrote to the address between the `LDXR` and `STXR`. If so, `STXR` fails and returns 1. This is more composable than CAS and avoids the ABA problem at the hardware level.

### Implementing a Spinlock with CAS

```c
#define UNLOCKED 0
#define LOCKED   1

typedef struct { _Atomic int value; } spinlock_t;

void spin_lock(spinlock_t *lock) {
    int expected = UNLOCKED;
    // Spin until CAS succeeds: atomically change UNLOCKED → LOCKED
    while (!atomic_compare_exchange_weak_explicit(
        &lock->value,
        &expected,
        LOCKED,
        memory_order_acquire,    // success ordering
        memory_order_relaxed     // failure ordering
    )) {
        expected = UNLOCKED;  // Reset expected after failed CAS
        // Spin-wait with PAUSE to reduce cache pressure
        while (atomic_load_explicit(&lock->value, memory_order_relaxed) == LOCKED) {
            __asm__ volatile("pause" ::: "memory");
        }
    }
}

void spin_unlock(spinlock_t *lock) {
    atomic_store_explicit(&lock->value, UNLOCKED, memory_order_release);
}
```

### `weak` vs `strong` CAS

- `compare_exchange_strong`: Guaranteed to succeed or fail based purely on value comparison. May loop internally on LL/SC architectures.
- `compare_exchange_weak`: Allowed to fail spuriously (even if values match). On LL/SC architectures this maps directly to one LL/SC attempt without internal looping. **Always preferred in spin loops** because the outer loop handles retries anyway.

---

## 5. Test-and-Set vs Test-and-Test-and-Set

### Test-and-Set (TAS)

The simplest possible spinlock primitive: atomically write 1 (LOCKED) and return the old value.

```c
// Returns the old value — if 0, you got the lock
int test_and_set(volatile int *lock) {
    return __atomic_exchange_n(lock, 1, __ATOMIC_ACQUIRE);
}

void spin_lock_tas(volatile int *lock) {
    while (test_and_set(lock) == 1) {
        // Spin — but every iteration does an atomic WRITE
    }
}
```

**Problem**: Every iteration of the spin loop performs an atomic write (to set the value to 1). Atomic writes require exclusive ownership of the cache line. With N threads spinning:

- All N threads are constantly writing
- The cache line bounces between all N cores in `Modified` state
- O(N) cache line transfers per lock acquisition attempt
- Performance collapses as N grows

### Test-and-Test-and-Set (TTAS)

The key insight: **read first, only attempt atomic write when the lock looks free**.

```c
void spin_lock_ttas(volatile int *lock) {
    while (1) {
        // Phase 1: Spin with READS (cache line stays in Shared state)
        while (atomic_load_explicit((_Atomic int*)lock, memory_order_relaxed) == 1) {
            __asm__ volatile("pause" ::: "memory");
        }
        // Phase 2: Only now attempt the atomic write
        if (test_and_set(lock) == 0) {
            return;  // Got the lock
        }
        // Someone else grabbed it first — go back to spinning reads
    }
}
```

**Why TTAS is better**:

During Phase 1, the cache line is in `Shared` state on all waiting cores — they can all read it simultaneously with no cache traffic. Only when the lock is released (the value changes to 0) does the cache line get invalidated on all waiting cores. Then they all race in Phase 2, but this contention event happens once per lock release rather than continuously.

Cache traffic goes from O(N × time) to O(N × lock_acquisitions).

---

## 6. Memory Ordering — The Critical Dimension

### The Six C11 Memory Orders

| Order | Store | Load | Description |
|-------|-------|------|-------------|
| `relaxed` | ✅ | ✅ | No ordering guarantees — only atomicity |
| `consume` | ❌ | ✅ | Data-dependency ordering (rarely used correctly) |
| `acquire` | ❌ | ✅ | No loads/stores can be reordered before this load |
| `release` | ✅ | ❌ | No loads/stores can be reordered after this store |
| `acq_rel` | ✅ | ✅ | Both acquire and release semantics |
| `seq_cst` | ✅ | ✅ | Total global order — strongest, most expensive |

### What Acquire and Release Actually Mean

**Release**: When you store with `release`, you are making a **promise**: all memory writes that happened in this thread *before* this store are visible to any thread that subsequently performs an `acquire` load that sees this store's value.

**Acquire**: When you load with `acquire`, you are making a **promise**: all memory reads in this thread *after* this load will see all writes that happened in any thread *before* their corresponding `release` store.

Together, release-acquire creates a **synchronizes-with** relationship — the classic "happens-before" guarantee that makes shared memory programming tractable.

### Spinlock Ordering Analysis

```c
// Correct spinlock memory ordering analysis:

// ACQUIRE on lock:
// - Must prevent subsequent critical section operations from being
//   reordered BEFORE the lock acquisition
// - Ensures we see all writes the previous lock holder made inside
//   the critical section before releasing

// RELEASE on unlock:
// - Must prevent critical section operations from being reordered
//   AFTER the unlock
// - Ensures the next lock acquirer sees all our writes

void spin_lock(spinlock_t *lock) {
    // memory_order_acquire: creates "acquire fence" here
    // Nothing below this can move above it
    while (atomic_exchange_explicit(&lock->value, LOCKED, memory_order_acquire) == LOCKED) {
        while (atomic_load_explicit(&lock->value, memory_order_relaxed) == LOCKED) {
            cpu_relax();  // PAUSE on x86
        }
    }
    // --- All operations in critical section stay below here ---
}

void spin_unlock(spinlock_t *lock) {
    // --- All operations in critical section stay above here ---
    // memory_order_release: creates "release fence" here
    // Nothing above this can move below it
    atomic_store_explicit(&lock->value, UNLOCKED, memory_order_release);
}
```

### Why `relaxed` is Safe for the Spin-Read

The inner spin loop uses `relaxed` ordering. This is correct because:
1. We don't act on the value read — we only use it as a hint to stop spinning
2. The actual lock acquisition uses `acquire`, which provides all necessary guarantees
3. Using `acquire` in the inner loop would generate unnecessary barrier instructions on every iteration

### Hardware Barrier Instructions

| Arch | Store-Store | Load-Load | Store-Load (full) | Load-Store |
|------|-------------|-----------|-------------------|------------|
| x86 | implicit | implicit | `MFENCE` | implicit |
| ARM64 | `DMB ISHST` | `DMB ISHLD` | `DMB ISH` | `DMB ISH` |
| RISC-V | `fence w,w` | `fence r,r` | `fence rw,rw` | `fence r,w` |

ARM's `LDAR`/`STLR` instructions (Load-Acquire, Store-Release) encode the barriers directly into the memory access, which is more efficient than separate barrier + access.

---

## 7. Linux Kernel Spinlock Internals

### Historical Evolution

```
Linux 2.0:   Simple bit test-and-set (non-FIFO, starvation possible)
Linux 2.6:   Ticket spinlocks (FIFO, fair)
Linux 3.15:  MCS lock queuing introduced  
Linux 4.2:   qspinlock (PV-aware, NUMA-optimized) becomes default
```

### The `spinlock_t` Type

In the Linux kernel, `spinlock_t` is a wrapper defined in `<linux/spinlock_types.h>`:

```c
typedef struct spinlock {
    union {
        struct raw_spinlock rlock;
        // Debug members when CONFIG_DEBUG_LOCK_ALLOC is set
    };
} spinlock_t;

typedef struct raw_spinlock {
    arch_spinlock_t raw_lock;
    // Lockdep tracking fields (when enabled)
} raw_spinlock_t;
```

The `arch_spinlock_t` is architecture-specific:

```c
// x86 (arch/x86/include/asm/spinlock_types.h)
typedef struct arch_spinlock {
    unsigned int val;  // qspinlock value
} arch_spinlock_t;
```

### Kernel Spinlock API

```c
// Declaration and initialization
DEFINE_SPINLOCK(my_lock);           // Static initialization
spinlock_t my_lock = __SPIN_LOCK_UNLOCKED(my_lock); // Equivalent
spin_lock_init(&my_lock);           // Dynamic initialization

// Basic operations
spin_lock(&lock);                   // Acquire (preemption disabled)
spin_unlock(&lock);                 // Release (preemption re-enabled)

// IRQ-safe variants (covered in detail later)
spin_lock_irq(&lock);               // Disable IRQs + acquire
spin_unlock_irq(&lock);             // Release + enable IRQs
spin_lock_irqsave(&lock, flags);    // Save IRQ state + disable + acquire
spin_unlock_irqrestore(&lock, flags); // Release + restore IRQ state

// Bottom-half safe variants
spin_lock_bh(&lock);                // Disable softirqs + acquire
spin_unlock_bh(&lock);              // Release + enable softirqs

// Trylock (non-blocking)
int ret = spin_trylock(&lock);      // Returns 1 if acquired, 0 if not
```

### Preemption and Spinlocks

A fundamental rule: **in the Linux kernel, acquiring a spinlock disables preemption on the current CPU**.

Why? Consider:

```
Thread A: spin_lock(&L)       // Acquires L
          [context switch]    // Preempted! Another thread runs
Thread B: spin_lock(&L)       // Spins trying to acquire L
          [L is never released because A is not running]
          [DEADLOCK]
```

If A holds the lock and is preempted, B (on the same CPU) will spin forever waiting for A to release the lock — but A cannot run because B is spinning. The kernel prevents this by disabling preemption when a spinlock is held.

This is implemented through `preempt_disable()` / `preempt_enable()`:

```c
// Simplified kernel spin_lock implementation
static inline void spin_lock(spinlock_t *lock) {
    preempt_disable();           // Prevent preemption
    do_raw_spin_lock(&lock->rlock);
}

static inline void spin_unlock(spinlock_t *lock) {
    do_raw_spin_unlock(&lock->rlock);
    preempt_enable();            // Re-enable preemption
}
```

### The Preemption Counter

The kernel maintains a per-CPU preemption counter:

```c
// include/linux/preempt.h
#define preempt_disable()   do { preempt_count_inc(); barrier(); } while (0)
#define preempt_enable()    do { ... if (preempt_count_dec_and_test()) __preempt_schedule(); } while (0)
```

When the counter is non-zero, the scheduler will not preempt the current task. Spinlock nesting is tracked automatically.

---

## 8. Ticket Spinlocks — Fairness Guaranteed

### The Fairness Problem

A basic TAS/TTAS spinlock has no fairness guarantee. When the lock is released, all spinning threads race to acquire it. A thread that has been waiting for 1 millisecond has no advantage over one that started waiting 1 nanosecond ago. Under high contention, some threads can starve indefinitely.

### The Ticket Lock Algorithm

Inspired by deli counters: you take a number when you arrive, and the counter calls numbers in order.

```c
typedef struct {
    _Atomic uint16_t next_ticket;   // Next ticket to be issued
    _Atomic uint16_t now_serving;   // Ticket currently being served
} ticket_spinlock_t;
```

**Acquire**: Atomically fetch-and-increment `next_ticket` to get your ticket. Spin until `now_serving == your_ticket`.

**Release**: Increment `now_serving` to serve the next waiter.

```c
void ticket_spin_lock(ticket_spinlock_t *lock) {
    // Atomically take a ticket (fetch-and-increment)
    uint16_t my_ticket = atomic_fetch_add_explicit(
        &lock->next_ticket, 1, memory_order_relaxed
    );

    // Wait until our turn
    while (atomic_load_explicit(&lock->now_serving, memory_order_acquire) != my_ticket) {
        // On x86: PAUSE to reduce bus traffic
        // We know exactly when to wake up: when now_serving == my_ticket
        cpu_relax();
    }
    // Implicit acquire barrier from the load above
}

void ticket_spin_unlock(ticket_spinlock_t *lock) {
    // Increment now_serving — the next waiter's spin condition becomes true
    // Note: no need for fetch_add — only the lock holder ever writes now_serving
    uint16_t next = atomic_load_explicit(&lock->now_serving, memory_order_relaxed) + 1;
    atomic_store_explicit(&lock->now_serving, next, memory_order_release);
}
```

### Properties of Ticket Locks

- **FIFO fairness**: Threads are served strictly in arrival order
- **Bounded waiting**: A thread with ticket N waits for at most N lock acquisitions by others
- **Still has cache coherence problem**: All waiters spin on `now_serving`. When it increments, all waiting CPUs simultaneously receive an invalidation and re-fetch the cache line. This is an O(N) broadcast problem on each unlock.

---

## 9. MCS Locks — Cache-Efficient Queuing

### The Cache Line Broadcast Problem

With ticket locks (and all locks where waiters spin on a shared location), each unlock causes:
1. One invalidation message to N waiting cores
2. N cores simultaneously attempt to load the new value
3. Cache line bounces between N cores

On a system with 256 cores, unlocking causes 256 simultaneous cache operations. This is a scalability cliff.

### MCS Lock: Each Thread Spins Locally

**Key insight**: Instead of all threads spinning on one shared location, each thread spins on its *own* location. Unlock sends a targeted signal to only the *next* waiter.

The lock is a linked list of per-thread nodes. The list is the queue of waiters.

```c
// Each thread has its own node
typedef struct mcs_node {
    struct mcs_node *next;      // Next waiter in the queue
    _Atomic int locked;         // This thread's spin variable (LOCAL!)
} mcs_node_t;

// The lock is just a pointer to the tail of the queue
typedef struct {
    _Atomic (mcs_node_t*) tail;
} mcs_lock_t;
```

### MCS Acquire

```c
void mcs_lock(mcs_lock_t *lock, mcs_node_t *my_node) {
    my_node->next = NULL;
    atomic_store_explicit(&my_node->locked, 1, memory_order_relaxed);

    // Atomically add ourselves to the tail of the queue
    // Returns the previous tail (our predecessor)
    mcs_node_t *prev = atomic_exchange_explicit(
        &lock->tail, my_node, memory_order_acq_rel
    );

    if (prev == NULL) {
        // Queue was empty — we got the lock immediately
        return;
    }

    // Link predecessor to us
    atomic_store_explicit(&prev->next, my_node, memory_order_release);

    // Spin on OUR OWN locked field — not a shared variable!
    // When our predecessor unlocks and writes to our->locked, only WE see it
    while (atomic_load_explicit(&my_node->locked, memory_order_acquire) == 1) {
        cpu_relax();
    }
    // We now hold the lock
}
```

### MCS Release

```c
void mcs_unlock(mcs_lock_t *lock, mcs_node_t *my_node) {
    mcs_node_t *next = atomic_load_explicit(&my_node->next, memory_order_relaxed);

    if (next == NULL) {
        // Check if we're the only one in the queue
        mcs_node_t *expected = my_node;
        if (atomic_compare_exchange_strong_explicit(
            &lock->tail, &expected, NULL,
            memory_order_release, memory_order_relaxed
        )) {
            // Successfully set tail to NULL — we were alone
            return;
        }
        // Someone is in the process of enqueuing — spin until they link to us
        while ((next = atomic_load_explicit(&my_node->next, memory_order_relaxed)) == NULL) {
            cpu_relax();
        }
    }

    // Signal the next waiter — write to THEIR locked field
    // This is a TARGETED signal to one specific cache line on one specific core
    atomic_store_explicit(&next->locked, 0, memory_order_release);
    // ^ Only next->locked's cache line is invalidated — on one core
}
```

### MCS Properties

- **O(1) unlock**: Notify exactly one waiter, invalidate exactly one cache line
- **Each thread spins on private memory**: No shared-location contention
- **FIFO**: Queue preserves arrival order
- **Scalable**: Performance is flat from 2 to 1000+ threads (on a single NUMA node)
- **Cost**: Extra indirection (node must be allocated per lock operation), slightly higher single-threaded overhead

---

## 10. qspinlock — The Linux Default

### Why qspinlock?

MCS locks require a per-acquisition node (stack-allocated or per-CPU). The Linux kernel uses spinlocks in contexts where stack space is precious and per-CPU memory must be managed carefully. Additionally, the kernel runs on **paravirtualized** environments (KVM, Xen) where a vCPU can be de-scheduled by the hypervisor while holding a spinlock, causing real CPUs to waste time spinning.

`qspinlock` (queued spinlock) combines:
- Compact representation (fits in one 32-bit word)
- MCS-like queue for scalability
- Paravirtualization awareness (PV spinlocks)

### The 32-bit Value

```
 31                                   0
┌─────────────────────────────────────┐
│  tail (pending + CPU index + level) │  locked  │
│         18 bits                     │  8 bits  │
└─────────────────────────────────────┘
```

```c
// arch/x86/include/asm/qspinlock_types.h
typedef struct qspinlock {
    union {
        atomic_t val;
        struct {
            u8 locked;    // Low byte: 0=free, 1=locked
            u8 pending;   // Pending byte: 1=one waiter, becoming next
            u16 tail;     // MCS queue tail: CPU | nest_level
        };
    };
} arch_spinlock_t;
```

### Three Cases on Acquisition

**Case 1 — Fast path (no contention)**:
CAS `val` from 0 to `_Q_LOCKED_VAL` (1). If it succeeds, lock acquired. No queue involvement.

**Case 2 — One waiter (pending path)**:
Set the `pending` bit. Spin on `locked` byte. When previous holder clears `locked`, pending waiter clears `pending` and sets `locked`. Still no MCS queue.

**Case 3 — Multiple waiters (slow path)**:
Use the MCS queue. Encode `(cpu_id | nest_level)` in the `tail` field. Allocate an MCS node from per-CPU storage. Follow MCS acquire/release protocol.

This three-level structure means that under low-to-medium contention, the full MCS overhead is avoided, while under high contention, the MCS queue provides O(1) cache-efficient handoff.

### Paravirtualized Spinlocks

In a VM, a vCPU spinning while the host has scheduled another vCPU on that physical core wastes real CPU cycles. PV spinlocks allow:
1. A spinning vCPU to *yield* (tell the hypervisor "I'm spinning, schedule someone else")
2. The lock holder (when releasing) to *kick* the next waiter (tell the hypervisor "wake up that vCPU")

This transforms a spinning lock into an efficient blocking mechanism in virtualized environments, without changing the API.

---

## 11. Read-Write Spinlocks

### The Concept

When shared data is read frequently but written rarely, a plain spinlock is overly conservative: it serializes all readers, even though concurrent reads are safe.

An **rwlock** allows:
- Multiple concurrent readers (no mutual exclusion between readers)
- Exclusive writer access (mutual exclusion between writer and all readers/writers)

### Linux Kernel RW Spinlock

```c
// Declaration
DEFINE_RWLOCK(my_rwlock);
rwlock_t my_rwlock = __RW_LOCK_UNLOCKED(my_rwlock);

// Reader operations
read_lock(&my_rwlock);
/* ... read shared data ... */
read_unlock(&my_rwlock);

// Writer operations
write_lock(&my_rwlock);
/* ... modify shared data ... */
write_unlock(&my_rwlock);

// IRQ-safe variants (same pattern as spinlock)
read_lock_irqsave(&my_rwlock, flags);
read_unlock_irqrestore(&my_rwlock, flags);
write_lock_irqsave(&my_rwlock, flags);
write_unlock_irqrestore(&my_rwlock, flags);
```

### Implementation Concept

```c
typedef struct {
    _Atomic int32_t count;
    // Positive: number of active readers
    // -1: one writer holds the lock
    // 0: unlocked
} rwspinlock_t;

#define WRITE_LOCK_VAL  (-1)

void read_spin_lock(rwspinlock_t *lock) {
    int32_t val;
    do {
        // Wait until no writer
        while ((val = atomic_load_explicit(&lock->count, memory_order_relaxed)) < 0) {
            cpu_relax();
        }
        // Try to increment reader count
    } while (!atomic_compare_exchange_weak_explicit(
        &lock->count, &val, val + 1,
        memory_order_acquire, memory_order_relaxed
    ));
}

void read_spin_unlock(rwspinlock_t *lock) {
    atomic_fetch_sub_explicit(&lock->count, 1, memory_order_release);
}

void write_spin_lock(rwspinlock_t *lock) {
    int32_t expected = 0;
    while (!atomic_compare_exchange_weak_explicit(
        &lock->count, &expected, WRITE_LOCK_VAL,
        memory_order_acquire, memory_order_relaxed
    )) {
        expected = 0;
        while (atomic_load_explicit(&lock->count, memory_order_relaxed) != 0) {
            cpu_relax();
        }
    }
}

void write_spin_unlock(rwspinlock_t *lock) {
    atomic_store_explicit(&lock->count, 0, memory_order_release);
}
```

### The Writer Starvation Problem

The above implementation can starve writers: if readers continuously hold the lock, a writer waiting for the count to reach 0 may wait indefinitely. Some implementations solve this with a "writer pending" flag that prevents new readers from acquiring while a writer waits.

### seq_lock — The Alternative

The Linux kernel provides `seqlock` (sequence lock) for the write-rarely, read-frequently pattern in situations where readers can be optimistic:

```c
// Writer: increment sequence counter (odd = writer active, even = stable)
write_seqlock(&my_seqlock);
/* modify data */
write_sequnlock(&my_seqlock);

// Reader: read sequence, read data, verify sequence unchanged
unsigned seq;
do {
    seq = read_seqbegin(&my_seqlock);
    /* read data */
} while (read_seqretry(&my_seqlock, seq));
```

Readers never block writers. If a write happens during a read, the reader simply retries. This is optimal when reads are fast and writes are rare.

---

## 12. IRQ-Safe Spinlocks

### The Problem: Interrupt Context

Interrupts can fire at any time, preempting any running code. If:
1. Thread A holds spinlock L
2. An interrupt fires on the same CPU
3. The interrupt handler tries to acquire L

→ **Deadlock**: The interrupt handler spins forever waiting for L, but L's holder (Thread A) cannot run because the interrupt hasn't returned.

### The Solution: Disable Interrupts

```c
// spin_lock_irqsave: disable ALL interrupts and save their state
unsigned long flags;
spin_lock_irqsave(&lock, flags);
/* critical section — safe from both interrupt handlers and other CPUs */
spin_unlock_irqrestore(&lock, flags);
```

Implementation:

```c
#define spin_lock_irqsave(lock, flags)          \
    do {                                        \
        local_irq_save(flags);  /* PUSHF; CLI on x86 */ \
        preempt_disable();                      \
        do_raw_spin_lock(lock);                 \
    } while (0)

#define spin_unlock_irqrestore(lock, flags)     \
    do {                                        \
        do_raw_spin_unlock(lock);               \
        local_irq_restore(flags);  /* POPF on x86 */    \
        preempt_enable();                       \
    } while (0)
```

The `flags` variable saves the CPU's interrupt flag register state (not just whether IRQs are enabled — the entire FLAGS register on x86). This allows correct nesting: if interrupts were already disabled before the lock, they remain disabled after the unlock.

### spin_lock_irq vs spin_lock_irqsave

```c
// spin_lock_irq: unconditionally disable IRQs
// SAFE only if you are CERTAIN IRQs are currently enabled
spin_lock_irq(&lock);
/* ... */
spin_unlock_irq(&lock);  // Re-enables IRQs unconditionally

// spin_lock_irqsave: save current IRQ state and disable
// SAFE in any context — handles nesting correctly
spin_lock_irqsave(&lock, flags);
/* ... */
spin_unlock_irqrestore(&lock, flags);  // Restores previous state
```

**Rule**: Prefer `irqsave`/`irqrestore` unless you are absolutely certain about the IRQ state at the call site.

### Bottom-Half (Softirq) Context

If a spinlock is shared between process context and a softirq (but NOT a hardirq handler), use `spin_lock_bh`:

```c
spin_lock_bh(&lock);    // Disable softirqs + acquire
/* ... */
spin_unlock_bh(&lock);  // Release + enable softirqs
```

This is cheaper than disabling all interrupts but protects against softirq preemption.

### Decision Matrix

| Lock shared with | Use |
|------------------|-----|
| No interrupts / same context | `spin_lock` / `spin_unlock` |
| Softirq handler | `spin_lock_bh` / `spin_unlock_bh` |
| Hardirq handler (IRQ state unknown) | `spin_lock_irqsave` / `spin_unlock_irqrestore` |
| Hardirq handler (know IRQs are on) | `spin_lock_irq` / `spin_unlock_irq` |

---

## 13. Recursive vs Non-Recursive Spinlocks

### Linux Spinlocks Are Non-Recursive

If a thread acquires a spinlock it already holds, it deadlocks:

```c
spin_lock(&L);
    spin_lock(&L);  // DEADLOCK — thread spins waiting for itself
```

This is intentional. Recursive locks hide design bugs. If you need to call a function that might acquire a lock you already hold, the design is wrong — you need to restructure so the inner call uses unlocked variants.

### The Linux `raw_spinlock_t`

`raw_spinlock_t` is the "cannot sleep even with preemption" version. On `PREEMPT_RT` (real-time) kernels, `spinlock_t` is reimplemented as a sleeping mutex (to reduce latency), but `raw_spinlock_t` always spins. Use `raw_spinlock_t` only for the absolute lowest-level kernel code that truly cannot sleep under any circumstance.

---

## 14. Spinlock Pathologies

### Deadlock

**Conditions (Coffman)**:
1. Mutual exclusion
2. Hold and wait
3. No preemption
4. Circular wait

**AB-BA Deadlock** — the classic pattern:

```
Thread A                Thread B
────────                ────────
lock(L1)                lock(L2)
lock(L2) ← spins        lock(L1) ← spins
                        ↑ DEADLOCK
```

**Solution**: Establish a global lock ordering. Always acquire locks in a consistent order (e.g., by address, by assigned ID). The Linux kernel uses `lockdep` to detect and report ordering violations.

### Livelock

All threads make progress (not stuck) but no thread makes useful progress — they all continuously react to each other:

```
Thread A: tries to acquire L, backs off
Thread B: tries to acquire L, backs off
Thread A: tries again at same time as B, backs off
Thread B: tries again at same time as A, backs off
... forever
```

**Solution**: Randomized exponential backoff. With random delay, the probability of simultaneous contention decreases exponentially.

### Priority Inversion

```
Low-priority task:  lock(L)  ← holds L
High-priority task: lock(L)  ← spins (blocked by low-priority!)
Medium-priority:    runs (preempts low-priority while it holds L!)
```

A high-priority task is effectively blocked by a medium-priority task, despite never interacting with it. 

In kernel space, spinlocks prevent preemption (partially mitigating this). In real-time systems, **priority inheritance** or **priority ceiling** protocols are used.

### Cache Thrashing (False Sharing)

If a spinlock variable shares a cache line with frequently modified data, writes to that data will constantly invalidate the spinlock's cache line on all spinning cores:

```c
// BAD: lock and data share a cache line (64 bytes typically)
struct {
    spinlock_t lock;        // 4 bytes
    int hot_data[15];       // 60 bytes — same cache line!
} shared;

// GOOD: align lock to its own cache line
struct {
    spinlock_t lock __attribute__((aligned(64)));
    int hot_data[16] __attribute__((aligned(64)));
} shared;
```

### The Thundering Herd

When a lock is released, all waiting threads wake up (or their spin conditions change) simultaneously. Most will fail to acquire the lock and go back to spinning — wasteful.

Ticket locks and MCS locks solve this: only the designated next-holder's condition changes on release.

---

## 15. NUMA Topology and Spinlock Performance

### NUMA — Non-Uniform Memory Access

In NUMA systems, memory access time depends on whether the target memory is local (on the same NUMA node as the CPU) or remote (on another node, requiring inter-node interconnect traversal).

```
Node 0                          Node 1
┌──────────────┐                ┌──────────────┐
│ CPU 0  CPU 1 │◄──QPI/NUMAlink─►│ CPU 2  CPU 3 │
│              │                │              │
│  Local RAM   │                │  Local RAM   │
└──────────────┘                └──────────────┘
```

Local access: ~4ns
Remote access: ~40–100ns

### Spinlock Behavior on NUMA

A spinlock whose cache line is on Node 0 causes all CPUs on Node 1 that try to acquire it to pay remote memory access costs on every spin iteration. This is catastrophic for performance.

### NUMA-Aware Spinlock Design

**Cohort Locks**: Hierarchical locks where:
1. A local lock per NUMA node
2. A global lock across nodes
3. Threads first acquire their local lock, then the global
4. The global is passed between NUMA nodes in "cohorts" to amortize cross-node transfers

**Linux numa_spinlock** (used in some kernel subsystems): Routes lock acquisitions preferentially to CPUs on the node where the lock is "homed", batching acquisitions from the same node before passing to another.

---

## 16. Spinlocks vs Mutexes vs Semaphores

### Comparative Analysis

| Property | Spinlock | Mutex | Semaphore |
|----------|----------|-------|-----------|
| Waiting strategy | Busy-wait (spin) | Sleep (block) | Sleep (block) |
| Context switch overhead | None | 2× switch cost | 2× switch cost |
| CPU waste while waiting | High | None | None |
| Usable in interrupt context | ✅ | ❌ | ❌ |
| Preemption state | Disabled | Enabled | Enabled |
| Counting support | ❌ | ❌ | ✅ |
| Recursive acquisition | ❌ | Sometimes | ✅ (counting) |
| Optimal for | Very short CS, IRQ | Longer CS, user space | Resource counting |

### The Break-Even Point

The break-even point between spinning and sleeping depends on:
- Context switch time (~1–10 microseconds on modern Linux)
- Cache miss cost when re-entering (cache was evicted during sleep)
- Critical section duration

**Rule of thumb**: If critical section < 2× context switch time → spin. Otherwise → sleep.

---

## 17. C Implementation

### Complete Production-Grade Spinlock Implementation

```c
/*
 * spinlock.h — Complete spinlock implementation in C11
 * Supports: x86_64, ARM64, RISC-V
 * Features: TAS, TTAS, Ticket, MCS
 */

#ifndef SPINLOCK_H
#define SPINLOCK_H

#include <stdint.h>
#include <stdatomic.h>
#include <stdbool.h>

/* ─────────────────────────────────────────────────────────────────
 * CPU Relaxation / Spin Hint
 * ───────────────────────────────────────────────────────────────── */

static inline void cpu_relax(void) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("pause" ::: "memory");
#elif defined(__aarch64__)
    __asm__ volatile("yield" ::: "memory");
#elif defined(__riscv)
    __asm__ volatile("pause" ::: "memory");
#else
    __asm__ volatile("" ::: "memory");  // Compiler barrier only
#endif
}

/* ─────────────────────────────────────────────────────────────────
 * Compiler Barrier
 * ───────────────────────────────────────────────────────────────── */
#define COMPILER_BARRIER() __asm__ volatile("" ::: "memory")

/* ─────────────────────────────────────────────────────────────────
 * 1. Simple Spinlock (Test-and-Set)
 * ───────────────────────────────────────────────────────────────── */

typedef struct {
    atomic_int value;       /* 0 = UNLOCKED, 1 = LOCKED */
} spinlock_t;

#define SPINLOCK_INIT { .value = ATOMIC_VAR_INIT(0) }

static inline void spinlock_init(spinlock_t *lock) {
    atomic_init(&lock->value, 0);
}

/*
 * spinlock_lock — Acquire the lock.
 *
 * Uses TTAS (Test-and-Test-and-Set) pattern:
 * 1. Spin with reads (shared cache line, no bus traffic)
 * 2. Attempt atomic write only when lock appears free
 *
 * Memory ordering:
 * - Inner loop: relaxed (no ordering needed for spin hint)
 * - Acquisition: acquire (establishes happens-before with release)
 */
static inline void spinlock_lock(spinlock_t *lock) {
    for (;;) {
        /* Fast path: try to atomically acquire from unlocked state */
        int expected = 0;
        if (atomic_compare_exchange_weak_explicit(
            &lock->value,
            &expected,
            1,
            memory_order_acquire,   /* success */
            memory_order_relaxed    /* failure */
        )) {
            return;
        }

        /* Slow path: spin on reads until lock appears free */
        while (atomic_load_explicit(&lock->value, memory_order_relaxed) != 0) {
            cpu_relax();
        }
        /* Go back to try CAS again — may race with other threads */
    }
}

/*
 * spinlock_trylock — Non-blocking acquire attempt.
 * Returns: true if lock acquired, false if already held.
 */
static inline bool spinlock_trylock(spinlock_t *lock) {
    int expected = 0;
    return atomic_compare_exchange_strong_explicit(
        &lock->value,
        &expected,
        1,
        memory_order_acquire,
        memory_order_relaxed
    );
}

/*
 * spinlock_unlock — Release the lock.
 *
 * Memory ordering: release — ensures all critical section writes
 * are visible to the next thread that acquires this lock.
 *
 * Note: A plain store (not RMW) is sufficient here because only
 * the lock holder calls unlock. The release barrier is the key.
 */
static inline void spinlock_unlock(spinlock_t *lock) {
    atomic_store_explicit(&lock->value, 0, memory_order_release);
}

/* ─────────────────────────────────────────────────────────────────
 * 2. Ticket Spinlock — FIFO Fair
 * ───────────────────────────────────────────────────────────────── */

typedef struct {
    _Atomic uint16_t next_ticket;   /* Next ticket to dispense */
    _Atomic uint16_t now_serving;   /* Current ticket being served */
} ticket_lock_t;

#define TICKET_LOCK_INIT { \
    .next_ticket = ATOMIC_VAR_INIT(0), \
    .now_serving = ATOMIC_VAR_INIT(0) \
}

static inline void ticket_lock_init(ticket_lock_t *lock) {
    atomic_init(&lock->next_ticket, 0);
    atomic_init(&lock->now_serving, 0);
}

static inline void ticket_lock_acquire(ticket_lock_t *lock) {
    /* Take our ticket atomically (fetch-and-increment) */
    uint16_t my_ticket = atomic_fetch_add_explicit(
        &lock->next_ticket, 1, memory_order_relaxed
    );

    /* Spin until our number is called */
    while (atomic_load_explicit(&lock->now_serving, memory_order_acquire) != my_ticket) {
        cpu_relax();
    }
    /* The acquire on now_serving synchronizes with the release on unlock */
}

static inline void ticket_lock_release(ticket_lock_t *lock) {
    uint16_t serving = atomic_load_explicit(&lock->now_serving, memory_order_relaxed);
    /*
     * Only lock holder writes now_serving, so no CAS needed.
     * Use release to synchronize with the next acquirer's acquire load.
     */
    atomic_store_explicit(&lock->now_serving, (uint16_t)(serving + 1), memory_order_release);
}

/* ─────────────────────────────────────────────────────────────────
 * 3. MCS Lock — Scalable Queue-Based
 * ───────────────────────────────────────────────────────────────── */

typedef struct mcs_node {
    _Atomic(struct mcs_node *) next;    /* Next waiter in queue */
    _Atomic int locked;                  /* This node's spin variable */
} mcs_node_t;

typedef struct {
    _Atomic(mcs_node_t *) tail;         /* Tail of MCS queue (NULL = unlocked) */
} mcs_lock_t;

#define MCS_LOCK_INIT   { .tail = ATOMIC_VAR_INIT(NULL) }
#define MCS_NODE_INIT   { .next = ATOMIC_VAR_INIT(NULL), .locked = ATOMIC_VAR_INIT(0) }

static inline void mcs_lock_init(mcs_lock_t *lock) {
    atomic_init(&lock->tail, NULL);
}

static inline void mcs_node_init(mcs_node_t *node) {
    atomic_init(&node->next, NULL);
    atomic_init(&node->locked, 0);
}

/*
 * mcs_lock_acquire — O(1) acquire with local spinning.
 *
 * @lock: The MCS lock
 * @node: Caller-provided node (must be per-thread or per-call-site unique)
 *
 * The caller must provide a node. Typically this is a stack-allocated
 * or thread-local node. The node must not be reused while held.
 */
static inline void mcs_lock_acquire(mcs_lock_t *lock, mcs_node_t *node) {
    /* Initialize our node */
    atomic_store_explicit(&node->next, NULL, memory_order_relaxed);
    atomic_store_explicit(&node->locked, 1, memory_order_relaxed);

    /*
     * Atomically insert ourselves at the tail of the queue.
     * Returns the previous tail (our predecessor), or NULL if we're first.
     * Uses acq_rel to synchronize with predecessor's unlock.
     */
    mcs_node_t *prev = atomic_exchange_explicit(
        &lock->tail, node, memory_order_acq_rel
    );

    if (prev == NULL) {
        /* Queue was empty — we got the lock immediately */
        return;
    }

    /*
     * Tell our predecessor that we're in line after them.
     * Uses release to synchronize with their load of ->next in unlock.
     */
    atomic_store_explicit(&prev->next, node, memory_order_release);

    /*
     * Spin on OUR OWN locked field.
     * Our predecessor will write 0 here when it unlocks.
     * This is LOCAL spinning — no cache line contention with others.
     */
    while (atomic_load_explicit(&node->locked, memory_order_acquire) != 0) {
        cpu_relax();
    }
}

/*
 * mcs_lock_release — O(1) release that notifies exactly one waiter.
 */
static inline void mcs_lock_release(mcs_lock_t *lock, mcs_node_t *node) {
    mcs_node_t *next = atomic_load_explicit(&node->next, memory_order_relaxed);

    if (next == NULL) {
        /*
         * No known successor. Attempt to set tail to NULL (indicating queue empty).
         * If this succeeds, we were the last in the queue.
         */
        mcs_node_t *expected = node;
        if (atomic_compare_exchange_strong_explicit(
            &lock->tail, &expected, NULL,
            memory_order_release, memory_order_relaxed
        )) {
            return;  /* We were the sole waiter — done */
        }

        /*
         * CAS failed: another thread is in the process of inserting itself.
         * It has done the exchange on tail but hasn't yet stored into our ->next.
         * Spin briefly until it does.
         */
        while ((next = atomic_load_explicit(&node->next, memory_order_acquire)) == NULL) {
            cpu_relax();
        }
    }

    /*
     * Hand the lock to our successor by clearing their locked flag.
     * Uses release to synchronize with their acquire in mcs_lock_acquire.
     * This is a TARGETED write to exactly one cache line on one core.
     */
    atomic_store_explicit(&next->locked, 0, memory_order_release);
}

/* ─────────────────────────────────────────────────────────────────
 * 4. Backoff Spinlock — Reduces Contention Under Load
 * ───────────────────────────────────────────────────────────────── */

#define BACKOFF_MIN    1
#define BACKOFF_MAX    1024

typedef spinlock_t backoff_spinlock_t;

static inline void backoff_spin_lock(backoff_spinlock_t *lock) {
    unsigned int delay = BACKOFF_MIN;

    for (;;) {
        int expected = 0;
        if (atomic_compare_exchange_weak_explicit(
            &lock->value, &expected, 1,
            memory_order_acquire, memory_order_relaxed
        )) {
            return;
        }

        /* Exponential backoff: spin for 'delay' PAUSE iterations */
        for (unsigned int i = 0; i < delay; i++) {
            cpu_relax();
        }

        /* Double the delay (capped at BACKOFF_MAX) */
        if (delay < BACKOFF_MAX) {
            delay <<= 1;
        }

        /* Spin-read until lock looks free before retrying CAS */
        while (atomic_load_explicit(&lock->value, memory_order_relaxed) != 0) {
            cpu_relax();
        }
    }
}

#define backoff_spin_unlock spinlock_unlock

/* ─────────────────────────────────────────────────────────────────
 * 5. Read-Write Spinlock
 * ───────────────────────────────────────────────────────────────── */

/*
 * count encoding:
 *  count > 0  : number of active readers
 *  count == 0 : unlocked
 *  count == -1: writer holds the lock
 */
typedef struct {
    _Atomic int32_t count;
} rwspinlock_t;

#define RWSPINLOCK_INIT { .count = ATOMIC_VAR_INIT(0) }

static inline void rwspinlock_init(rwspinlock_t *lock) {
    atomic_init(&lock->count, 0);
}

static inline void rwspinlock_read_lock(rwspinlock_t *lock) {
    for (;;) {
        int32_t cur = atomic_load_explicit(&lock->count, memory_order_relaxed);

        /* Wait if a writer holds or is waiting */
        if (cur < 0) {
            while (atomic_load_explicit(&lock->count, memory_order_relaxed) < 0) {
                cpu_relax();
            }
            continue;
        }

        /* Try to increment reader count */
        if (atomic_compare_exchange_weak_explicit(
            &lock->count, &cur, cur + 1,
            memory_order_acquire, memory_order_relaxed
        )) {
            return;
        }
        /* CAS failed (another reader or writer intervened) — retry */
    }
}

static inline void rwspinlock_read_unlock(rwspinlock_t *lock) {
    atomic_fetch_sub_explicit(&lock->count, 1, memory_order_release);
}

static inline void rwspinlock_write_lock(rwspinlock_t *lock) {
    for (;;) {
        int32_t expected = 0;  /* Only acquire when fully unlocked */
        if (atomic_compare_exchange_weak_explicit(
            &lock->count, &expected, -1,
            memory_order_acquire, memory_order_relaxed
        )) {
            return;
        }
        /* Wait until both readers and writers are gone */
        while (atomic_load_explicit(&lock->count, memory_order_relaxed) != 0) {
            cpu_relax();
        }
    }
}

static inline void rwspinlock_write_unlock(rwspinlock_t *lock) {
    atomic_store_explicit(&lock->count, 0, memory_order_release);
}

#endif /* SPINLOCK_H */
```

### Usage Example

```c
/*
 * example.c — Demonstrating all spinlock variants
 */

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "spinlock.h"

/* ─── Simple Spinlock Example ─── */

static spinlock_t counter_lock = SPINLOCK_INIT;
static volatile long counter = 0;

void *increment_thread(void *arg) {
    long iterations = (long)arg;
    for (long i = 0; i < iterations; i++) {
        spinlock_lock(&counter_lock);
        counter++;              /* Critical section */
        spinlock_unlock(&counter_lock);
    }
    return NULL;
}

/* ─── MCS Lock Example ─── */

static mcs_lock_t mcs_lock = MCS_LOCK_INIT;
static volatile long mcs_counter = 0;

void *mcs_increment_thread(void *arg) {
    long iterations = (long)arg;
    mcs_node_t node;           /* Stack-allocated per-call node */
    mcs_node_init(&node);

    for (long i = 0; i < iterations; i++) {
        mcs_lock_acquire(&mcs_lock, &node);
        mcs_counter++;
        mcs_lock_release(&mcs_lock, &node);
    }
    return NULL;
}

/* ─── RW Spinlock Example ─── */

static rwspinlock_t rw_lock = RWSPINLOCK_INIT;
static volatile long shared_data = 0;

void *reader_thread(void *arg) {
    long reads = (long)arg;
    long sum = 0;
    for (long i = 0; i < reads; i++) {
        rwspinlock_read_lock(&rw_lock);
        sum += shared_data;    /* Read — concurrent with other readers */
        rwspinlock_read_unlock(&rw_lock);
    }
    return (void *)sum;
}

void *writer_thread(void *arg) {
    long writes = (long)arg;
    for (long i = 0; i < writes; i++) {
        rwspinlock_write_lock(&rw_lock);
        shared_data++;         /* Write — exclusive */
        rwspinlock_write_unlock(&rw_lock);
    }
    return NULL;
}

int main(void) {
    const int N_THREADS = 4;
    const long ITERS = 1000000L;
    pthread_t threads[N_THREADS];

    /* Test simple spinlock */
    counter = 0;
    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment_thread, (void *)ITERS);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    printf("Spinlock counter: %ld (expected %ld)\n", counter, (long)N_THREADS * ITERS);

    /* Test MCS lock */
    mcs_counter = 0;
    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, mcs_increment_thread, (void *)ITERS);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    printf("MCS lock counter: %ld (expected %ld)\n", mcs_counter, (long)N_THREADS * ITERS);

    return 0;
}
```

### Linux Kernel Usage Pattern

```c
/*
 * kernel_example.c — How spinlocks are used in the Linux kernel
 * (Pseudocode illustrating kernel patterns, not compilable as-is)
 */

#include <linux/spinlock.h>
#include <linux/list.h>

struct my_device {
    spinlock_t lock;                /* Protects the list and count */
    struct list_head pending_list;
    unsigned int pending_count;
    /* ... other fields ... */
};

/* Initialization (called once during device probe) */
void my_device_init(struct my_device *dev) {
    spin_lock_init(&dev->lock);
    INIT_LIST_HEAD(&dev->pending_list);
    dev->pending_count = 0;
}

/* Called from process context */
int my_device_enqueue(struct my_device *dev, struct work_item *item) {
    unsigned long flags;

    /*
     * Use irqsave because this lock is also acquired from the
     * interrupt handler below. Without irqsave, if an interrupt
     * fires while we hold the lock (on the same CPU), deadlock.
     */
    spin_lock_irqsave(&dev->lock, flags);

    if (dev->pending_count >= MAX_PENDING) {
        spin_unlock_irqrestore(&dev->lock, flags);
        return -EBUSY;
    }

    list_add_tail(&item->list, &dev->pending_list);
    dev->pending_count++;

    spin_unlock_irqrestore(&dev->lock, flags);
    return 0;
}

/* Called from interrupt handler (hardirq context) */
irqreturn_t my_device_irq_handler(int irq, void *dev_id) {
    struct my_device *dev = dev_id;
    struct work_item *item = NULL;

    /*
     * In interrupt context — interrupts for this IRQ are already masked,
     * but spin_lock (not irqsave) is still correct here if this is the
     * only IRQ that accesses this lock.
     * Using spin_lock (not irqsave) because we're already in IRQ context.
     */
    spin_lock(&dev->lock);  /* Just preemption disable + acquire */

    if (!list_empty(&dev->pending_list)) {
        item = list_first_entry(&dev->pending_list, struct work_item, list);
        list_del(&item->list);
        dev->pending_count--;
    }

    spin_unlock(&dev->lock);

    if (item) {
        process_work_item(item);
        return IRQ_HANDLED;
    }
    return IRQ_NONE;
}
```

---

## 18. Rust Implementation

### Philosophy: Safe Abstractions Over Unsafe Primitives

Rust's ownership and type system allows us to express lock invariants at compile time. The key insight: the locked data should be *inside* the lock type, and the lock guard should be the only way to access it. This is not just good ergonomics — it is a correctness guarantee enforced by the type system.

### Core Spinlock in Rust

```rust
//! spinlock.rs — Production-grade spinlock implementations
//! 
//! Demonstrates:
//! - AtomicBool/AtomicUsize for primitives
//! - Safe wrappers with type-system guarantees
//! - Send/Sync bounds for thread safety
//! - Guard pattern for automatic unlock

use std::cell::UnsafeCell;
use std::ops::{Deref, DerefMut};
use std::sync::atomic::{AtomicBool, AtomicU16, AtomicUsize, Ordering, fence};
use std::hint;

// ─────────────────────────────────────────────────────────────────
// CPU Relax / Spin Hint
// ─────────────────────────────────────────────────────────────────

/// Emit a CPU spin-loop hint.
/// Maps to PAUSE on x86, YIELD on ARM, pause on RISC-V.
#[inline(always)]
fn cpu_relax() {
    // std::hint::spin_loop() is the stable API for this
    // It maps to the appropriate ISA instruction
    hint::spin_loop();
}

// ─────────────────────────────────────────────────────────────────
// 1. Basic Spinlock<T> — Safe Wrapper with Guard Pattern
// ─────────────────────────────────────────────────────────────────

/// A mutual exclusion spinlock that owns its protected data.
///
/// Unlike `std::sync::Mutex`, this never sleeps — it busy-waits.
/// Appropriate for very short critical sections or situations where
/// blocking is impossible (e.g., custom runtime, no-std environments).
///
/// # Safety Invariants
///
/// - The `locked` flag is `true` iff some thread holds the lock
/// - `data` is only accessible through `SpinlockGuard`
/// - `SpinlockGuard` releases the lock on drop (even on panic)
pub struct Spinlock<T> {
    locked: AtomicBool,
    data: UnsafeCell<T>,
}

/// SAFETY:
/// Spinlock<T> can be safely shared across threads if T: Send.
/// The AtomicBool ensures mutual exclusion, so T need not be Sync.
unsafe impl<T: Send> Send for Spinlock<T> {}
unsafe impl<T: Send> Sync for Spinlock<T> {}

impl<T> Spinlock<T> {
    /// Create a new, unlocked spinlock containing `data`.
    pub const fn new(data: T) -> Self {
        Self {
            locked: AtomicBool::new(false),
            data: UnsafeCell::new(data),
        }
    }

    /// Acquire the lock. Spins until the lock is available.
    ///
    /// # Memory Ordering
    ///
    /// Uses Acquire on success, Relaxed on failure (for the CAS),
    /// and Relaxed for the inner spin reads.
    ///
    /// The Acquire ordering on successful CAS creates the
    /// "synchronizes-with" relationship with the Release on unlock,
    /// establishing happens-before for all critical section operations.
    pub fn lock(&self) -> SpinlockGuard<'_, T> {
        loop {
            // Fast path: CAS false → true with Acquire
            if self.locked
                .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_ok()
            {
                break;
            }

            // Slow path: spin with reads until lock appears free
            // Relaxed is safe here — we don't act on this value,
            // only use it as a hint to avoid useless CAS attempts
            while self.locked.load(Ordering::Relaxed) {
                cpu_relax();
            }
        }

        SpinlockGuard { lock: self }
    }

    /// Attempt to acquire the lock without spinning.
    /// Returns `Some(guard)` if acquired, `None` if already locked.
    pub fn try_lock(&self) -> Option<SpinlockGuard<'_, T>> {
        self.locked
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .ok()
            .map(|_| SpinlockGuard { lock: self })
    }

    /// Force-unlock. 
    ///
    /// # Safety
    ///
    /// Caller must hold the lock. Calling this without holding the lock
    /// is undefined behavior — it allows two threads to simultaneously
    /// access the protected data.
    unsafe fn force_unlock(&self) {
        // Release ordering: ensures all critical section writes are
        // visible to the next thread that acquires with Acquire.
        self.locked.store(false, Ordering::Release);
    }
}

/// RAII guard that holds the spinlock and provides access to the data.
///
/// The lock is automatically released when the guard is dropped,
/// including when unwinding due to a panic. This is the "lock guard"
/// pattern — it is impossible to access the protected data without
/// holding the lock, and impossible to forget to release it.
pub struct SpinlockGuard<'a, T> {
    lock: &'a Spinlock<T>,
}

impl<T> Deref for SpinlockGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: We hold the lock. No other thread can access data.
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for SpinlockGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        // SAFETY: We hold the lock exclusively. Mut access is safe.
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for SpinlockGuard<'_, T> {
    fn drop(&mut self) {
        // SAFETY: SpinlockGuard is only created in Spinlock::lock/try_lock,
        // which atomically acquired the lock. We release it here.
        unsafe { self.lock.force_unlock() }
    }
}

// ─────────────────────────────────────────────────────────────────
// 2. Ticket Lock — FIFO Fair
// ─────────────────────────────────────────────────────────────────

/// A fair (FIFO) spinlock using the ticket algorithm.
///
/// Threads are served in arrival order. No thread can starve.
pub struct TicketLock<T> {
    next_ticket: AtomicU16,
    now_serving: AtomicU16,
    data: UnsafeCell<T>,
}

unsafe impl<T: Send> Send for TicketLock<T> {}
unsafe impl<T: Send> Sync for TicketLock<T> {}

impl<T> TicketLock<T> {
    pub const fn new(data: T) -> Self {
        Self {
            next_ticket: AtomicU16::new(0),
            now_serving: AtomicU16::new(0),
            data: UnsafeCell::new(data),
        }
    }

    pub fn lock(&self) -> TicketGuard<'_, T> {
        // Atomically take a ticket (fetch-and-increment)
        // Relaxed is safe here — ordering is established by the subsequent
        // Acquire load of now_serving when our ticket is called
        let my_ticket = self.next_ticket.fetch_add(1, Ordering::Relaxed);

        // Spin until our ticket is called
        // The Acquire on this load synchronizes with the Release on unlock
        while self.now_serving.load(Ordering::Acquire) != my_ticket {
            cpu_relax();
        }

        TicketGuard { lock: self }
    }

    unsafe fn release(&self) {
        // Increment now_serving to serve the next waiter
        // Only the lock holder calls this, so no CAS needed (no contention on write)
        // Release ordering synchronizes with the next waiter's Acquire load
        let cur = self.now_serving.load(Ordering::Relaxed);
        self.now_serving.store(cur.wrapping_add(1), Ordering::Release);
    }
}

pub struct TicketGuard<'a, T> {
    lock: &'a TicketLock<T>,
}

impl<T> Deref for TicketGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for TicketGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for TicketGuard<'_, T> {
    fn drop(&mut self) {
        unsafe { self.lock.release() }
    }
}

// ─────────────────────────────────────────────────────────────────
// 3. MCS Lock — Cache-Efficient Scalable Queue
// ─────────────────────────────────────────────────────────────────

use std::ptr;
use std::sync::atomic::AtomicPtr;

/// MCS queue node — one per pending acquisition.
/// Must be pinned in memory (not moved) while in the queue.
#[repr(align(64))]  // Pad to cache line to prevent false sharing
pub struct McsNode {
    next: AtomicPtr<McsNode>,   // Next waiter
    locked: AtomicBool,          // This node's spin variable
}

impl McsNode {
    pub fn new() -> Self {
        Self {
            next: AtomicPtr::new(ptr::null_mut()),
            locked: AtomicBool::new(false),
        }
    }
}

impl Default for McsNode {
    fn default() -> Self {
        Self::new()
    }
}

/// MCS lock — scalable queue-based spinlock.
/// O(1) per-lock-operation cache coherence traffic.
pub struct McsLock<T> {
    tail: AtomicPtr<McsNode>,
    data: UnsafeCell<T>,
}

unsafe impl<T: Send> Send for McsLock<T> {}
unsafe impl<T: Send> Sync for McsLock<T> {}

impl<T> McsLock<T> {
    pub const fn new(data: T) -> Self {
        Self {
            tail: AtomicPtr::new(ptr::null_mut()),
            data: UnsafeCell::new(data),
        }
    }

    /// Acquire the lock. 
    ///
    /// `node` must be a mutable reference to a caller-owned McsNode.
    /// The node must not be moved or dropped until the returned guard is dropped.
    /// Typically, use a stack-allocated or thread-local node.
    ///
    /// # Returns
    ///
    /// An McsGuard that provides access to the data and releases the lock on drop.
    pub fn lock<'a>(&'a self, node: &'a mut McsNode) -> McsGuard<'a, T> {
        // Initialize node
        node.next.store(ptr::null_mut(), Ordering::Relaxed);
        node.locked.store(true, Ordering::Relaxed);

        let node_ptr = node as *mut McsNode;

        // Enqueue ourselves atomically: swap tail to our node
        // AcqRel: Acquire for reading our predecessor's state,
        //         Release so our node initialization is visible to successor
        let prev = self.tail.swap(node_ptr, Ordering::AcqRel);

        if prev.is_null() {
            // Queue was empty — we have the lock
            return McsGuard { lock: self, node };
        }

        // Tell our predecessor we're behind them
        // Release: our node initialization (locked=true, next=null) must
        //          be visible before predecessor reads our locked field in its release
        unsafe { (*prev).next.store(node_ptr, Ordering::Release) };

        // Spin on our OWN locked field — local spinning, no shared cache line
        // Acquire: synchronizes with predecessor's Release store to our locked
        while node.locked.load(Ordering::Acquire) {
            cpu_relax();
        }

        McsGuard { lock: self, node }
    }
}

pub struct McsGuard<'a, T> {
    lock: &'a McsLock<T>,
    node: &'a mut McsNode,
}

impl<T> Deref for McsGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for McsGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for McsGuard<'_, T> {
    fn drop(&mut self) {
        let node_ptr = self.node as *mut McsNode;

        // Check for a successor
        let mut next = self.node.next.load(Ordering::Relaxed);

        if next.is_null() {
            // No known successor — try to clear the tail
            let mut tail_expected = node_ptr;
            if self.lock.tail.compare_exchange(
                tail_expected,
                ptr::null_mut(),
                Ordering::Release,
                Ordering::Relaxed,
            ).is_ok() {
                return; // We were the last — done
            }

            // Someone is enqueuing — wait for them to store into our next
            loop {
                next = self.node.next.load(Ordering::Acquire);
                if !next.is_null() {
                    break;
                }
                cpu_relax();
            }
        }

        // Signal our successor by clearing their locked flag
        // Release: all our critical section writes are now visible to successor
        unsafe { (*next).locked.store(false, Ordering::Release) };
    }
}

// ─────────────────────────────────────────────────────────────────
// 4. RW Spinlock — Concurrent Readers, Exclusive Writer
// ─────────────────────────────────────────────────────────────────

/// Read-write spinlock.
///
/// Encoding of `state`:
/// - 0: unlocked
/// - n > 0: n active readers
/// - usize::MAX (-1 as isize): writer holds the lock
const WRITER: usize = usize::MAX;

pub struct RwSpinlock<T> {
    state: AtomicUsize,
    data: UnsafeCell<T>,
}

unsafe impl<T: Send> Send for RwSpinlock<T> {}
unsafe impl<T: Send + Sync> Sync for RwSpinlock<T> {}

impl<T> RwSpinlock<T> {
    pub const fn new(data: T) -> Self {
        Self {
            state: AtomicUsize::new(0),
            data: UnsafeCell::new(data),
        }
    }

    pub fn read(&self) -> ReadGuard<'_, T> {
        loop {
            let cur = self.state.load(Ordering::Relaxed);

            if cur == WRITER {
                // Writer active — spin-wait
                while self.state.load(Ordering::Relaxed) == WRITER {
                    cpu_relax();
                }
                continue;
            }

            // Try to increment reader count
            if self.state.compare_exchange_weak(
                cur, cur + 1,
                Ordering::Acquire,
                Ordering::Relaxed,
            ).is_ok() {
                return ReadGuard { lock: self };
            }
        }
    }

    pub fn write(&self) -> WriteGuard<'_, T> {
        loop {
            if self.state.compare_exchange_weak(
                0, WRITER,
                Ordering::Acquire,
                Ordering::Relaxed,
            ).is_ok() {
                return WriteGuard { lock: self };
            }
            // Wait until fully unlocked
            while self.state.load(Ordering::Relaxed) != 0 {
                cpu_relax();
            }
        }
    }
}

pub struct ReadGuard<'a, T> {
    lock: &'a RwSpinlock<T>,
}

impl<T> Deref for ReadGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> Drop for ReadGuard<'_, T> {
    fn drop(&mut self) {
        self.lock.state.fetch_sub(1, Ordering::Release);
    }
}

pub struct WriteGuard<'a, T> {
    lock: &'a RwSpinlock<T>,
}

impl<T> Deref for WriteGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for WriteGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for WriteGuard<'_, T> {
    fn drop(&mut self) {
        self.lock.state.store(0, Ordering::Release);
    }
}

// ─────────────────────────────────────────────────────────────────
// 5. Usage Examples
// ─────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::thread;

    #[test]
    fn spinlock_mutual_exclusion() {
        let lock = Arc::new(Spinlock::new(0u64));
        let n_threads = 8;
        let iters = 100_000;

        let handles: Vec<_> = (0..n_threads).map(|_| {
            let lock = Arc::clone(&lock);
            thread::spawn(move || {
                for _ in 0..iters {
                    let mut guard = lock.lock();
                    *guard += 1;
                    // Guard dropped here — lock released
                }
            })
        }).collect();

        for h in handles { h.join().unwrap(); }
        assert_eq!(*lock.lock(), n_threads * iters);
    }

    #[test]
    fn ticket_lock_fairness_no_data_races() {
        let lock = Arc::new(TicketLock::new(Vec::<u64>::new()));
        let n_threads = 4;
        let iters = 1000;

        let handles: Vec<_> = (0..n_threads).map(|i| {
            let lock = Arc::clone(&lock);
            thread::spawn(move || {
                for _ in 0..iters {
                    let mut guard = lock.lock();
                    guard.push(i as u64);
                }
            })
        }).collect();

        for h in handles { h.join().unwrap(); }
        assert_eq!(lock.lock().len(), n_threads * iters);
    }

    #[test]
    fn mcs_lock_correctness() {
        let lock = Arc::new(McsLock::new(0u64));
        let n_threads = 4;
        let iters = 10_000;

        let handles: Vec<_> = (0..n_threads).map(|_| {
            let lock = Arc::clone(&lock);
            thread::spawn(move || {
                for _ in 0..iters {
                    let mut node = McsNode::new();
                    let mut guard = lock.lock(&mut node);
                    *guard += 1;
                    // guard dropped: releases lock; then node dropped: safe
                }
            })
        }).collect();

        for h in handles { h.join().unwrap(); }
        assert_eq!(*lock.lock(&mut McsNode::new()), n_threads as u64 * iters);
    }

    #[test]
    fn rwlock_concurrent_reads() {
        let lock = Arc::new(RwSpinlock::new(42u64));

        // Multiple readers concurrently
        let handles: Vec<_> = (0..8).map(|_| {
            let lock = Arc::clone(&lock);
            thread::spawn(move || {
                for _ in 0..1000 {
                    let guard = lock.read();
                    assert_eq!(*guard, 42u64);
                }
            })
        }).collect();

        for h in handles { h.join().unwrap(); }
        assert_eq!(*lock.read(), 42u64);
    }

    #[test]
    fn spinlock_guard_is_sendable() {
        // This tests that SpinlockGuard can cross thread boundaries
        // (it can — as long as T: Send)
        fn assert_send<T: Send>() {}
        assert_send::<SpinlockGuard<'static, u64>>();
    }
}

// ─────────────────────────────────────────────────────────────────
// 6. No-std / Embedded Spinlock (portable, no heap)
// ─────────────────────────────────────────────────────────────────

/// Spinlock usable in no_std environments (no heap, no std::thread).
/// Useful for embedded systems and OS kernels.
///
/// In no_std, you may need to provide your own cpu_relax implementation.
pub struct NoStdSpinlock {
    locked: AtomicBool,
}

impl NoStdSpinlock {
    pub const fn new() -> Self {
        Self { locked: AtomicBool::new(false) }
    }

    /// Acquire the lock. Spins indefinitely.
    ///
    /// # Correctness
    ///
    /// On single-core systems without preemption, this will deadlock
    /// if called while already holding the lock. On embedded systems,
    /// ensure either:
    /// a) Interrupts are disabled while the lock is held, or
    /// b) The lock is never acquired from an interrupt handler
    ///    that could interrupt a lock holder on the same "core"
    #[inline]
    pub fn lock(&self) {
        while self.locked.compare_exchange_weak(
            false, true,
            Ordering::Acquire,
            Ordering::Relaxed,
        ).is_err() {
            while self.locked.load(Ordering::Relaxed) {
                core::hint::spin_loop();
            }
        }
    }

    #[inline]
    pub fn unlock(&self) {
        self.locked.store(false, Ordering::Release);
    }

    #[inline]
    pub fn try_lock(&self) -> bool {
        self.locked.compare_exchange(
            false, true,
            Ordering::Acquire,
            Ordering::Relaxed,
        ).is_ok()
    }
}
```

### Rust Type System Guarantees

Notice what Rust's type system enforces that C cannot:

1. **No access without acquiring**: `data` is wrapped in `UnsafeCell`, which is only accessible through the guard. You cannot write `lock.data.field` — it won't compile.

2. **No use-after-unlock**: The guard borrows from the lock with lifetime `'a`. The lock cannot be moved or dropped while the guard exists. The Rust borrow checker enforces this.

3. **No lock leakage**: The guard implements `Drop`. The lock is always released, even on panic. In C, if you `return` early from a critical section, you must manually unlock — a common source of bugs.

4. **Sendability tracked**: `Spinlock<T>` is only `Sync` (shareable across threads) if `T: Send`. This prevents accidentally sharing non-thread-safe types.

5. **`UnsafeCell` is the only way**: Rust's aliasing rules prohibit multiple mutable references. `UnsafeCell` is the only legal way to have interior mutability — the compiler will refuse any other approach.

---

## 19. Debugging Spinlocks

### Linux Lockdep

**Lockdep** is the Linux kernel's runtime lock validator. It tracks:
- Lock acquisition and release events
- The "lock class" of each lock (based on code location, not address)
- The order in which lock classes have been acquired

When it detects a potential deadlock cycle (A→B in some context, B→A in another), it immediately reports it — even if the deadlock has never actually occurred.

```
WARNING: possible circular locking dependency detected
task/pid is trying to acquire lock:
    (lock_B){....}, at: function_b+0x50

but task is already holding lock:
    (lock_A){....}, at: function_a+0x30

which lock already depends on the new lock.

the existing dependency chain:
-> (lock_A){....} at function_a+0x30
-> (lock_B){....} at function_b+0x50

Possible unsafe locking scenario:
CPU 0           CPU 1
----            ----
lock(A)         lock(B)
lock(B)         lock(A)
```

Enable with `CONFIG_PROVE_LOCKING=y`, `CONFIG_LOCKDEP=y`.

### KCSAN — Kernel Concurrency Sanitizer

KCSAN is a dynamic race detector for the kernel. It instruments memory accesses and reports when two threads access the same location concurrently without proper synchronization. Unlike Lockdep (which analyzes locking patterns), KCSAN directly detects data races.

Enable with `CONFIG_KCSAN=y`.

KCSAN output example:
```
BUG: KCSAN: data-race in function_x / function_y
write to 0xffff... of 4 bytes by task 123 on cpu 0:
    function_x+0x40
read to 0xffff... of 4 bytes by task 456 on cpu 1:
    function_y+0x20
```

### TSAN — Thread Sanitizer (User Space)

For user-space C/Rust, compile with ThreadSanitizer:

```bash
# C
gcc -fsanitize=thread -g program.c -o program

# Rust
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test
```

TSAN instruments every memory access and uses a happens-before graph to detect races. It has approximately 5–15× runtime overhead but catches races that would otherwise manifest as rare, non-reproducible bugs.

### Valgrind Helgrind

For user-space C:
```bash
valgrind --tool=helgrind ./program
```

### Common Debugging Strategies

**Symptom: Hangs / Stalls**
- Suspect a deadlock or livelock
- Check: Are multiple locks acquired in different orders?
- Check: Is a spinlock acquired in code that could be called from an interrupt handler without IRQ disabling?
- Tool: `sysrq-t` in the kernel (dumps all CPU states) or `gdb` attach

**Symptom: Data corruption / intermittent wrong results**
- Suspect a race condition (missing lock, wrong lock, wrong ordering)
- Tool: KCSAN, TSAN, Helgrind
- Check: Are relaxed operations used where acquire/release is needed?

**Symptom: Performance degradation under load**
- Suspect lock contention, cache thrashing, or false sharing
- Tool: `perf stat -e cache-misses,cache-references`, `perf lock`
- Check: Cache line alignment of lock and data variables

---

## 20. Performance Analysis

### Measuring Lock Overhead

```c
/*
 * bench.c — Measuring spinlock latency and throughput
 * Compile: gcc -O2 -pthread -march=native bench.c -o bench
 */
#include <stdio.h>
#include <pthread.h>
#include <time.h>
#include "spinlock.h"

#define ITERS 10000000L

typedef struct {
    spinlock_t lock;
    char _pad[60];  /* Pad to separate from counter on cache line */
    volatile long counter;
} __attribute__((aligned(64))) bench_data_t;

static bench_data_t bench;

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}

void *bench_thread(void *arg) {
    int n = *(int *)arg;
    for (long i = 0; i < ITERS / n; i++) {
        spinlock_lock(&bench.lock);
        bench.counter++;
        spinlock_unlock(&bench.lock);
    }
    return NULL;
}

void run_bench(int n_threads) {
    bench.counter = 0;
    spinlock_init(&bench.lock);

    pthread_t threads[n_threads];
    double t0 = now_ns();

    for (int i = 0; i < n_threads; i++) {
        pthread_create(&threads[i], NULL, bench_thread, &n_threads);
    }
    for (int i = 0; i < n_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    double elapsed = now_ns() - t0;
    printf("Threads: %2d | Ops/sec: %10.0f | Latency: %6.1f ns\n",
           n_threads,
           ITERS / (elapsed / 1e9),
           elapsed / ITERS);
}

int main(void) {
    printf("Spinlock benchmark\n");
    for (int t = 1; t <= 16; t *= 2) {
        run_bench(t);
    }
    return 0;
}
```

### Performance Intuitions

**Uncontended lock**: Should be ~5–20 ns (2–8 clock cycles). Just an atomic CAS.

**Lightly contended (2 threads)**: ~50–200 ns. One cache line transfer.

**Heavily contended (N threads, N large)**: Can exceed 1000 ns per acquisition. Multiple cache bounces, invalidation storms.

**Key metrics to watch**:

| Metric | Healthy | Problematic |
|--------|---------|-------------|
| `cache-misses` rate | < 1% | > 10% |
| `lock contention` time | < 5% of CPU time | > 20% |
| Lock acquisition latency | < 100ns | > 1000ns |
| Lock hold time | < 1 µs | > 10 µs |

### `perf lock` Analysis

```bash
# Record lock events
perf lock record ./my_program

# Analyze
perf lock report
```

Output shows: which locks are most contended, average wait time, total time spent waiting.

---

## 21. Expert Mental Models

### Mental Model 1: The Cache Line as a Token

Visualize a spinlock as a physical token (the cache line in Modified state). Only one CPU can hold the token at a time. Every atomic operation is a request to hold the token. Spinning is repeatedly requesting the token. The entire goal of advanced spinlock designs (MCS, qspinlock) is to eliminate unnecessary token transfers — each unnecessary transfer costs 50–300 ns.

### Mental Model 2: Critical Sections as Monolithic Blocks

When reasoning about correctness, mentally collapse the entire critical section into a single, indivisible step. If the result of your program is correct regardless of the order in which these collapsed steps interleave, the lock is correct. If not, the lock is protecting the wrong invariant.

### Mental Model 3: Memory Ordering as Causality

`release` + `acquire` creates a causal link between two events:
> "Everything I did before my release *caused* everything you see after your acquire."

If you can't draw a causal chain from a write to a read using release/acquire edges, the read may see a stale value. When debugging memory ordering bugs, draw the happens-before graph explicitly.

### Mental Model 4: The Hierarchy of Intervention Cost

From cheapest to most expensive:
1. **Cache hit (same core)**: 1 cycle
2. **Cache hit (different L1, same L2)**: 5 cycles
3. **L3 cache hit**: 30–40 cycles
4. **Cache line invalidation + transfer**: 100–300 cycles
5. **NUMA remote memory access**: 500–1500 cycles
6. **Context switch**: 5,000–50,000 cycles
7. **Syscall**: 100–1000 cycles

A spinlock held for 10 cycles that causes 5 cache transfers is already more expensive than holding it for 1500 cycles without contention. **Contention, not hold time, is the enemy.**

### Mental Model 5: Atomics as Fence Posts

Think of atomic operations as fence posts that the compiler and CPU cannot reorder across. `acquire` is a fence that nothing subsequent can cross going backward. `release` is a fence that nothing prior can cross going forward. `seq_cst` is a two-way fence. `relaxed` has no fence — it's just atomicity.

### The Cognitive Principle: Chunking Concurrency Patterns

When you encounter concurrent code, your expert intuition should immediately chunk it into known patterns:
- **Producer-consumer** → mutex/semaphore (or lock-free queue)
- **Read-mostly** → rwlock or seqlock
- **Short critical section, IRQ context** → spinlock
- **Many waiters, NUMA system** → MCS/qspinlock
- **Resource counting** → semaphore or atomic counter

This chunking reduces cognitive load from O(n) (reasoning about every line) to O(1) (pattern recognition). It is built through deliberate study of implementations and deliberate practice debugging races.

---

## Summary: The Spinlock Mastery Matrix

| Concept | Beginner | Intermediate | Expert |
|---------|----------|-------------|--------|
| What | Busy-wait lock | CAS + memory ordering | Cache coherence implications |
| Why | Short CS, IRQ context | Preemption model | NUMA topology, PV systems |
| How — C | `while (locked)` | TTAS + PAUSE | ticket/MCS/qspinlock internals |
| How — Rust | `AtomicBool` + guard | Type-system guarantees | `unsafe` interior mutability |
| Ordering | `SeqCst` everywhere | `Acquire`/`Release` analysis | `Relaxed` optimization |
| Debug | Add `sleep(1)` | TSAN/Helgrind | Lockdep + KCSAN |
| Perf | "It's slow" | Count cache misses | Trace cache line ownership |

---

*The discipline of concurrent systems programming is ultimately the discipline of reasoning precisely about time and causality across multiple agents. Master the memory model, and the rest follows from first principles.*

Now let me create the comprehensive guide:The guide is complete — here's what it covers across **21 deep sections**:

**Hardware Foundation**
The guide starts where all experts must — at the CPU level. Store buffers, load buffers, MESI protocol, TSO vs weakly-ordered memory models (x86 vs ARM). You cannot reason correctly about spinlocks without these.

**Primitive Progression (with full rationale)**
TAS → TTAS → Ticket → MCS → qspinlock. Each step is motivated by the failure mode of the previous design. TTAS solves the "atomic write storm" of TAS. Ticket solves starvation. MCS solves the "O(N) cache broadcast on unlock" of ticket. qspinlock compresses MCS into 32 bits and adds PV awareness. This is the evolutionary logic of the Linux kernel from 2.0 to 4.2+.

**Memory Ordering — Surgical Precision**
Every atomic operation in the C and Rust code has its ordering justified from first principles — why `Relaxed` for the inner spin read, why `Acquire` on success, why a plain `store` with `Release` suffices for unlock.

**Linux Kernel Internals**
The actual `spinlock_t` → `raw_spinlock_t` → `arch_spinlock_t` type chain, preemption counter mechanics, IRQ-safe variants with the full decision matrix, bottom-half context, `spin_lock_irqsave` internals.

**C and Rust Implementations**
- C: Portable `spinlock.h` with TAS, TTAS, Ticket Lock, MCS Lock, Backoff Lock, RW Spinlock — all with `__asm__` PAUSE hints and proper cache-line awareness
- Rust: Full `Spinlock<T>`, `TicketLock<T>`, `McsLock<T>`, `RwSpinlock<T>` with guard pattern, `unsafe impl Send/Sync`, and `no_std` variant

**The mental model section at the end** — "Cache line as a token", "Causality chains for memory ordering", "The hierarchy of intervention costs" — these are the cognitive tools that let experts *feel* concurrency bugs before running the code.