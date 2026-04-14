# Linux Synchronization Primitives: A Complete Kernel-Depth Guide
## Semaphore · Mutex · Spinlock · Lock · Monitor · Livelock · Deadlock

> *"Concurrency bugs are not random — they are the inevitable result of incorrect reasoning about time, order, and shared state."*

---

## Table of Contents

1. [Mental Model: Why Synchronization Exists](#1-mental-model-why-synchronization-exists)
2. [Hardware Foundations: What the CPU Actually Does](#2-hardware-foundations-what-the-cpu-actually-does)
3. [Memory Model and Ordering](#3-memory-model-and-ordering)
4. [Spinlock](#4-spinlock)
5. [Mutex](#5-mutex)
6. [Semaphore](#6-semaphore)
7. [Read-Write Locks (rwlock)](#7-read-write-locks-rwlock)
8. [Monitor](#8-monitor)
9. [Futex — The Linux Kernel's Secret Weapon](#9-futex--the-linux-kernels-secret-weapon)
10. [Deadlock](#10-deadlock)
11. [Livelock](#11-livelock)
12. [Starvation](#12-starvation)
13. [Priority Inversion](#13-priority-inversion)
14. [Lock-Free and Wait-Free Algorithms](#14-lock-free-and-wait-free-algorithms)
15. [Linux Kernel Synchronization Internals](#15-linux-kernel-synchronization-internals)
16. [C Implementations](#16-c-implementations)
17. [Go Implementations](#17-go-implementations)
18. [Rust Implementations](#18-rust-implementations)
19. [Comparative Analysis](#19-comparative-analysis)
20. [Expert Mental Models and Heuristics](#20-expert-mental-models-and-heuristics)

---

## 1. Mental Model: Why Synchronization Exists

### The Root Problem: Shared Mutable State Over Time

Modern computers execute multiple threads of execution simultaneously across multiple CPU cores. The moment two threads share any mutable state — a variable, a data structure, a file descriptor — you have a **race condition** unless you explicitly control access ordering.

The deeper truth: **the CPU, compiler, and memory subsystem all independently reorder operations** for performance. Without synchronization primitives:

- The **compiler** may reorder loads and stores (dead code elimination, loop unrolling, register caching).
- The **CPU** may execute instructions out-of-order (OoO execution pipelines, store buffers, load queues).
- The **cache coherency protocol** (MESI/MOESI) may propagate writes to other cores with arbitrary delay.
- The **memory controller** may reorder DRAM accesses.

```
Thread A                    Thread B
--------                    --------
x = 1;                      if (ready) {
ready = true;                   assert(x == 1); // MAY FAIL
                            }
```

Without memory barriers, `ready = true` may become visible to Thread B before `x = 1` due to store buffer reordering.

### The Critical Section Model

Every synchronization problem reduces to one primitive concept:

```
[Entry Protocol] → [Critical Section] → [Exit Protocol]
```

The **critical section** is a code region that must execute atomically with respect to other threads. The entry and exit protocols are the lock acquire and release operations.

### The Four Properties of Correct Synchronization (Dijkstra's Requirements)

1. **Mutual Exclusion**: At most one thread is in the critical section at any time.
2. **Progress**: If no thread is in the critical section and some threads want to enter, one of them eventually enters in finite time.
3. **Bounded Waiting (No Starvation)**: There is a bound on how many times other threads can enter before a waiting thread gets its turn.
4. **No Assumptions About Speed**: The algorithm must work regardless of relative thread speeds or scheduling.

---

## 2. Hardware Foundations: What the CPU Actually Does

### Atomic Instructions

All high-level synchronization primitives are ultimately built on a small set of hardware atomic instructions. The CPU guarantees these complete indivisibly with respect to all other processors.

#### Test-and-Set (TAS)
```
TAS(memory_location):
    old_value = *memory_location
    *memory_location = 1
    return old_value
// All of this happens atomically — no other CPU can interleave
```

#### Compare-and-Swap (CAS) — The Universal Primitive
```
CAS(addr, expected, new_value):
    if *addr == expected:
        *addr = new_value
        return true
    return false
// Atomically: if memory matches expected, replace it
```

CAS is Turing-complete for building synchronization — any lock-free algorithm can be expressed with CAS.

#### Fetch-and-Add (FAA)
```
FAA(addr, increment):
    old = *addr
    *addr += increment
    return old
// Used in ticket locks and semaphore counters
```

#### Load-Linked / Store-Conditional (LL/SC) — ARM and RISC-V
```
// ARM64 equivalent:
LDXR x0, [x1]     // Load-exclusive: mark address in exclusive monitor
// ... compute new value in x2 ...
STXR w3, x2, [x1] // Store-conditional: succeeds only if exclusive monitor still set
                   // w3 = 0 means success, 1 means failure (retry loop needed)
```

LL/SC avoids the **ABA problem** that plagues CAS-based algorithms.

### x86_64 Specific: LOCK Prefix and XCHG

On x86, the `LOCK` prefix makes any read-modify-write instruction atomic across all processors:

```asm
lock xchg [mutex], eax    ; atomic swap (used in spinlock acquire)
lock cmpxchg [addr], ecx  ; CAS
lock xadd [addr], eax     ; fetch-and-add
```

x86 has a **strong memory model** (Total Store Order — TSO): all stores are globally visible in program order, and all loads see the most recent store. This means x86 only requires `MFENCE` for very specific cases. ARM and RISC-V have **weak memory models** requiring explicit barriers much more frequently.

### MESI Cache Coherency Protocol

Every cache line (64 bytes on modern x86/ARM) is in one of four states:

| State    | Meaning                                                      |
|----------|--------------------------------------------------------------|
| Modified | Only in this cache, differs from memory, dirty               |
| Exclusive| Only in this cache, matches memory, clean                    |
| Shared   | In multiple caches, matches memory, read-only                |
| Invalid  | Not present in this cache                                    |

When Thread A on Core 0 writes to a cache line that Core 1 has in Shared state:
1. Core 0 sends an **Invalidate** message on the interconnect.
2. Core 1 receives it, marks the line Invalid, sends acknowledgment.
3. Core 0 upgrades to Modified, performs the write.
4. If Core 1 now reads, it triggers a cache miss → bus transaction → Core 0 flushes its modified line.

This is **cache line bouncing** — the primary performance cost of naive locking.

**False sharing**: Two unrelated variables on the same 64-byte cache line cause them to serialize even though they're logically independent. Expert systems align hot per-thread data to cache line boundaries.

```c
// Bad: x and y share a cache line, causing false sharing
struct { int x; int y; } shared;

// Good: each on its own cache line
struct { int x; char pad[60]; } thread_a_data;
struct { int y; char pad[60]; } thread_b_data;
```

---

## 3. Memory Model and Ordering

### Memory Barriers (Fences)

A **memory barrier** is an instruction that prevents the CPU and compiler from reordering memory operations across the barrier.

| Barrier Type | Meaning                                           | x86 Instruction | ARM Instruction |
|--------------|---------------------------------------------------|-----------------|-----------------|
| Store-Store  | All stores before barrier complete before stores after | (implicit on x86) | `DMB ST`    |
| Load-Load    | All loads before barrier complete before loads after  | (implicit on x86) | `DMB LD`    |
| Store-Load   | All stores before visible before any load after   | `MFENCE`        | `DMB ISH`       |
| Full         | No reordering across barrier in any direction     | `MFENCE`        | `DMB ISH`       |

### C11/C++11 Memory Order Model

```c
// 6 memory orderings from weakest to strongest:
memory_order_relaxed   // No ordering guarantees, only atomicity
memory_order_consume   // Data-dependency ordering (deprecated in practice)
memory_order_acquire   // No loads/stores after this can be reordered before
memory_order_release   // No loads/stores before this can be reordered after
memory_order_acq_rel   // Both acquire and release semantics
memory_order_seq_cst   // Total sequential consistency (default, most expensive)
```

**Acquire-Release Pairing** is the foundational pattern:

```
Thread A (writer):          Thread B (reader):
data = 42;                  // acquire load synchronizes-with release store
flag.store(1, release);     if (flag.load(acquire)) {
                                assert(data == 42); // GUARANTEED SAFE
                            }
```

The release store in Thread A "publishes" all prior stores. The acquire load in Thread B "subscribes" to all stores that happened before the matching release.

---

## 4. Spinlock

### What It Is

A **spinlock** is a lock where the waiting thread **busy-waits** (spins in a tight loop) rather than sleeping. The thread remains runnable, consuming CPU, checking the lock state repeatedly until it becomes available.

### When To Use Spinlocks

**Use spinlocks when:**
- The critical section is extremely short (< few hundred nanoseconds).
- You are in a context where sleeping is impossible (interrupt handlers, NMI handlers, kernel code with interrupts disabled).
- The lock contention is expected to be very low.
- The overhead of a context switch (1-10 µs) exceeds the expected wait time.

**Never use spinlocks when:**
- The critical section may sleep or block on I/O.
- You are on a uniprocessor system (spinning prevents the lock holder from running).
- Hold time is long.

### Naive Spinlock (Test-and-Set)

```
lock:
    while TAS(&lock_var) == 1:  // spin until we set it from 0 to 1
        // busy wait

unlock:
    lock_var = 0
```

**Problem**: Under contention, all waiters hammer the same cache line, causing massive cache coherency traffic. Every CAS attempt broadcasts an "Invalidate" to all other cores.

### Ticket Lock (Fair Spinlock)

The ticket lock solves the unfairness of TAS spinlocks by using a system analogous to a deli counter:

```
struct ticket_lock {
    atomic_uint ticket;   // next ticket to be issued
    atomic_uint serving;  // currently serving this ticket
};

acquire:
    my_ticket = FAA(&lock.ticket, 1)  // atomically get next number
    while lock.serving != my_ticket:  // spin until our turn
        CPU_RELAX()

release:
    FAA(&lock.serving, 1)  // advance the serving counter
```

**Properties**: FIFO ordering — threads acquire the lock in the exact order they requested it. **Bounded waiting** is satisfied.

**Problem**: Still has cache line bouncing — all waiters spin on `serving`, which is written on every release. On large NUMA machines, this causes O(N) cache traffic per release.

### MCS Lock (Mellor-Crummey Scott) — The Scalable Spinlock

The MCS lock is the gold standard for scalable spinlocks. Each waiter spins on its **own** node in a linked list, eliminating shared cache line bouncing:

```
struct mcs_node {
    atomic_int locked;      // spin on this
    struct mcs_node *next;  // chain to next waiter
};

struct mcs_lock {
    struct mcs_node *tail;  // points to last node in queue
};

acquire(lock, my_node):
    my_node->next = NULL
    my_node->locked = 1
    predecessor = XCHG(&lock->tail, my_node)  // atomically link into queue
    if predecessor != NULL:
        predecessor->next = my_node
        while my_node->locked:  // spin on OUR OWN node
            CPU_RELAX()

release(lock, my_node):
    if my_node->next == NULL:
        if CAS(&lock->tail, my_node, NULL): return  // no waiters
        while my_node->next == NULL: CPU_RELAX()  // wait for next to be set
    my_node->next->locked = 0  // wake up the next waiter (one cache line write)
```

**Advantage**: Release causes exactly **one cache invalidation** to exactly one core. O(1) cache traffic per operation regardless of contention.

**Disadvantage**: Lock state is distributed across thread-local nodes — querier context needed for release.

The Linux kernel's `qspinlock` (queued spinlock) is a compact version of MCS that fits in 4 bytes.

### The CPU_RELAX() Instruction

Inside every spin loop, `CPU_RELAX()` is critical:

```c
// x86: PAUSE instruction
static inline void cpu_relax(void) {
    asm volatile("pause" ::: "memory");
}

// ARM: YIELD instruction
static inline void cpu_relax(void) {
    asm volatile("yield" ::: "memory");
}
```

`PAUSE` on x86:
1. Gives a hint to the CPU that this is a spin-wait loop.
2. Reduces power consumption.
3. Avoids **memory order violation** pipeline flushes when the spin ends (the CPU knows the load in the spin loop will change).
4. Improves HyperThreading performance (yields execution pipeline to sibling logical core).

Without `PAUSE`, spin loops cause severe performance degradation on modern CPUs.

### Spinlock: IRQ Safety in the Linux Kernel

The Linux kernel has multiple spinlock variants based on interrupt context:

```c
spin_lock(&lock);                    // Basic: disables kernel preemption only
spin_lock_irq(&lock);               // Disables local CPU interrupts + preemption
spin_lock_irqsave(&lock, flags);    // Saves + disables IRQ state
spin_lock_bh(&lock);                // Disables bottom-half (softirq) + preemption
```

**Why IRQ-safe spinlocks?** If an interrupt fires while a spinlock is held, and the interrupt handler also tries to acquire the same spinlock, you have a **single-CPU deadlock** — the interrupt handler spins waiting for the lock, but the interrupted code (which holds the lock) can never run because the interrupt won't return.

---

## 5. Mutex

### What It Is

A **mutex** (mutual exclusion lock) is a sleeping lock. When a thread fails to acquire a mutex, it is **put to sleep** (deschedules) and woken up later when the mutex is released. This makes mutexes appropriate for longer critical sections where the blocking overhead is acceptable.

### Mutex vs Spinlock: The Decision Framework

```
Expected wait time < Context switch overhead (~1-10 µs)?
    YES → Spinlock
    NO  → Mutex

Can the lock holder sleep?
    YES → Must use Mutex (sleeping locks)
    NO  → Spinlock

Single CPU system?
    YES → Must use Mutex (spinlock causes deadlock on uniprocessor)
    NO  → Either, depending on above
```

### Mutex Internal State Machine

```
State: UNLOCKED (0)
    |
    | thread calls lock()
    v
CAS(0 → 1) succeeds?
    YES → State: LOCKED_NO_WAITERS (1) → thread enters critical section
    NO  →
        CAS(1 → 2)?
            State: LOCKED_WITH_WAITERS (2)
            thread calls futex_wait() → sleeps in kernel wait queue
    
When unlock():
    State == 1 (no waiters)?
        CAS(1 → 0) → done (fast path, no syscall)
    State == 2 (waiters exist)?
        Set state = 0
        futex_wake() → wake one waiter from kernel queue
```

This is the exact state machine used by glibc's `pthread_mutex_t` (using futex internally).

### Mutex Properties

- **Ownership**: A mutex has an **owner** — only the thread that locked it can unlock it. This is a semantic difference from semaphores.
- **Non-recursive by default**: A thread trying to lock a mutex it already holds will deadlock (unless it's a `PTHREAD_MUTEX_RECURSIVE` type).
- **No IRQ context**: Mutexes cannot be used in interrupt handlers (they may sleep).

### Linux Kernel Mutex (`struct mutex`)

The Linux kernel mutex is distinct from user-space `pthread_mutex_t`:

```c
// Defined in include/linux/mutex.h
struct mutex {
    atomic_long_t       owner;     // current owner task_struct, or flags
    raw_spinlock_t      wait_lock; // protects wait_list
    struct list_head    wait_list; // list of waiting tasks
#ifdef CONFIG_DEBUG_MUTEXES
    const char          *name;
    void                *magic;
    struct lockdep_map  dep_map;
#endif
};
```

The `owner` field encodes both the owner pointer and flags in the low bits (pointer alignment guarantees at least 3 bits are zero):
- Bit 0: **MUTEX_FLAG_WAITERS** — there are waiters in the queue.
- Bit 1: **MUTEX_FLAG_HANDOFF** — lock handoff to top waiter is pending.
- Bit 2: **MUTEX_FLAG_PICKUP** — top waiter is being set up to take ownership.

### Optimistic Spinning (Midpath)

The Linux kernel mutex implements a critical optimization: **optimistic spinning** (also called adaptive spinning).

When a thread fails to acquire a mutex, instead of immediately sleeping:
1. Check if the lock owner is **currently running** on some CPU.
2. If yes, spin briefly (MCS-style) hoping the owner will release soon.
3. If the owner gets preempted or sleeps, stop spinning and go to sleep.

This avoids the expensive sleep/wake cycle for short-duration contention:

```
Acquire path:
  Fast path: CAS(0 → owner) succeeds → locked, return
  Midpath: Owner is running → MCS spin, opportunistically acquire
  Slow path: futex_wait() → sleep in wait queue
```

---

## 6. Semaphore

### What It Is

A **semaphore** is a synchronization primitive that maintains an integer counter and supports two atomic operations:

- **`wait()` / `P()` / `down()`**: Decrement counter. If result < 0, block until another thread increments it.
- **`signal()` / `V()` / `up()`**: Increment counter. If there are blocked threads, wake one.

Named `P` and `V` from Dijkstra's Dutch: *Proberen* (to test) and *Verhogen* (to increment).

### Binary vs Counting Semaphore

**Binary Semaphore** (value 0 or 1): Can be used like a mutex, but **lacks ownership** — any thread can signal it, even one that didn't wait. This makes binary semaphores useful for **signaling** between threads.

**Counting Semaphore** (value 0 to N): Controls access to a pool of N resources. Classic use case: connection pool of size N.

```
semaphore = N  // N available resources

// Thread wanting a resource:
wait(semaphore)        // decrements; blocks if 0
use_resource()
signal(semaphore)      // increments; wakes a waiter if any
```

### Semaphore vs Mutex: The Critical Distinction

| Property          | Mutex                        | Binary Semaphore             |
|-------------------|------------------------------|------------------------------|
| Ownership         | Yes — only owner can unlock  | No — any thread can signal   |
| Recursion         | Configurable                 | N/A                          |
| Primary Use       | Mutual exclusion             | Signaling / resource counting|
| Priority Inheritance | Often supported           | Typically not                |
| Initial Value     | Unlocked (1)                 | Typically 0 (for signaling)  |

**The semaphore as signal pattern:**
```
// Producer-Consumer with semaphore as a signal
semaphore items = 0    // how many items are available
semaphore spaces = N   // how many spaces are free

// Producer:
wait(spaces)
produce_item()
signal(items)

// Consumer:
wait(items)
consume_item()
signal(spaces)
```

### POSIX Semaphores: Named vs Unnamed

**Unnamed (anonymous) semaphores** — between threads in the same process (or related processes via shared memory):
```c
sem_t sem;
sem_init(&sem, 0 /*not shared*/, initial_value);
sem_wait(&sem);
sem_post(&sem);
sem_destroy(&sem);
```

**Named semaphores** — identified by a filesystem path, usable between unrelated processes:
```c
sem_t *sem = sem_open("/my_semaphore", O_CREAT, 0644, 1);
sem_wait(sem);
sem_post(sem);
sem_close(sem);
sem_unlink("/my_semaphore");
```

Named semaphores appear in `/dev/shm/` on Linux.

### Linux Kernel Semaphore

```c
struct semaphore {
    raw_spinlock_t  lock;       // protects the fields below
    unsigned int    count;      // current semaphore value
    struct list_head wait_list; // list of sleeping tasks
};

// Usage:
DEFINE_SEMAPHORE(my_sem);     // count = 1
down(&my_sem);                 // P() — may sleep
up(&my_sem);                   // V()
down_trylock(&my_sem);         // non-blocking attempt
down_interruptible(&my_sem);   // can be interrupted by signals
down_killable(&my_sem);        // only interruptible by fatal signals
down_timeout(&my_sem, timeout);
```

**Important kernel note**: The kernel's `semaphore` should not be confused with `mutex`. In the kernel, prefer `mutex` when you need mutual exclusion (it has more optimization like adaptive spinning, lockdep support). Use `semaphore` only when you need counting or non-ownership semantics.

---

## 7. Read-Write Locks (rwlock)

### Motivation

Many data structures are **read-mostly** — many threads read simultaneously, but writes are rare. A plain mutex serializes all access, eliminating read concurrency. The read-write lock exploits this asymmetry:

- **Multiple readers** may hold the lock simultaneously.
- **Writers** require exclusive access — no readers, no other writers.

### State Machine

```
States:
  UNLOCKED:           readers=0, writer=false
  READ_LOCKED:        readers>0, writer=false
  WRITE_LOCKED:       readers=0, writer=true
  READ_LOCKED+WRITER_PENDING: readers>0, writer=false, writer_waiting=true
```

### Reader Preference vs Writer Preference

**Reader preference** (naive implementation): New readers can acquire even if a writer is waiting. Can cause **writer starvation** if the read rate is high.

**Writer preference**: No new readers can acquire once a writer is waiting. Can cause **reader starvation** in write-heavy workloads.

**Fair (FIFO) rwlock**: Writers and readers are queued in arrival order. The Linux kernel's `rwsem` uses this approach.

### Linux Kernel `rwlock_t` (Spinlock variant)

For short critical sections:
```c
rwlock_t lock = __RW_LOCK_UNLOCKED(lock);
read_lock(&lock);
// ... shared read access ...
read_unlock(&lock);

write_lock(&lock);
// ... exclusive write access ...
write_unlock(&lock);
```

### Linux Kernel `rw_semaphore` (Sleeping variant)

For longer critical sections:
```c
struct rw_semaphore rwsem;
init_rwsem(&rwsem);

down_read(&rwsem);
// ... read critical section ...
up_read(&rwsem);

down_write(&rwsem);
// ... write critical section ...
up_write(&rwsem);

// Upgrade read → write (may fail if others hold read):
downgrade_write(&rwsem);  // downgrade write → read after a write
```

### Seqlock — Optimistic Read Concurrency

The seqlock is a Linux-specific mechanism for extremely fast reads where writes are infrequent and reads are non-destructive:

```c
seqlock_t seqlock;

// Writer (always uses a spinlock internally):
write_seqlock(&seqlock);
// ... write shared data ...
write_sequnlock(&seqlock);

// Reader (lockless — may retry):
unsigned seq;
do {
    seq = read_seqbegin(&seqlock);  // read version counter (even = stable)
    // ... read shared data ...
} while (read_seqretry(&seqlock, seq));  // retry if seq changed (odd during write)
```

**How it works**: The sequence counter is incremented **twice per write** (once at start, once at end). Odd values mean a write is in progress. Readers check the counter before and after reading — if it changed (or was odd), the data was mutated during the read, so retry.

**Cost**: Readers pay only two atomic reads + a conditional branch. No write to any shared cache line. Effectively **zero overhead for readers** in the absence of writers.

Used extensively in the Linux kernel for `jiffies`, `xtime` (wall clock time), and network routing.

---

## 8. Monitor

### What It Is

A **monitor** is a high-level synchronization construct that combines:
1. A **mutex** protecting shared data.
2. One or more **condition variables** for waiting on state changes.
3. The **invariant** — a logical condition that must hold whenever no thread is inside the monitor.

Monitors were formalized by Hoare (1974) and Brinch Hansen (1975) and are the foundation of Java's `synchronized` blocks and `wait()/notify()`.

### Condition Variables

A condition variable allows threads to atomically **release a mutex and sleep** waiting for a condition, then **reacquire the mutex** when woken. The key: the release and sleep are atomic — no wakeup can be missed.

**The three operations:**
- `wait(cv, mutex)`: Atomically release mutex + sleep. On wake: reacquire mutex, return.
- `signal(cv)` / `notify_one()`: Wake exactly one waiting thread.
- `broadcast(cv)` / `notify_all()`: Wake all waiting threads.

### Hoare vs Mesa Semantics

**Hoare semantics** (original): When `signal()` is called, the waiting thread runs **immediately**, and the signaling thread is suspended. The woken thread is guaranteed the condition holds without rechecking.

**Mesa semantics** (practical): When `signal()` is called, the waiting thread is **moved to the ready queue** but the signaling thread continues. The woken thread must **re-check the condition** because it may have changed by the time it runs.

Modern systems (pthreads, Go, Rust) use Mesa semantics. This is why condition variable waits must **always be in a loop**:

```c
// WRONG (Hoare assumption — breaks on Mesa):
pthread_cond_wait(&cv, &mutex);
use_resource(); // assumes condition still holds — IT MAY NOT

// CORRECT (Mesa — always re-check):
while (!condition_is_true()) {
    pthread_cond_wait(&cv, &mutex);
}
use_resource();
```

### Spurious Wakeups

POSIX explicitly permits condition variable waits to return **spuriously** — without any signal being sent. This is an implementation artifact (some `futex` wait calls return early due to signal delivery). This reinforces: **always use while loops, never if statements, for condition variable waits.**

### The Classic Monitor Pattern: Bounded Buffer (Producer-Consumer)

```
Monitor BoundedBuffer:
    mutex: protect all access
    not_full: CV — signal when buffer not full
    not_empty: CV — signal when buffer not empty
    buffer[N]: the shared buffer
    count: number of items in buffer

produce(item):
    lock(mutex)
    while count == N:
        wait(not_full, mutex)  // release mutex, sleep
    buffer[in] = item
    in = (in + 1) % N
    count++
    signal(not_empty)          // wake a consumer
    unlock(mutex)

consume():
    lock(mutex)
    while count == 0:
        wait(not_empty, mutex) // release mutex, sleep
    item = buffer[out]
    out = (out + 1) % N
    count--
    signal(not_full)           // wake a producer
    unlock(mutex)
    return item
```

---

## 9. Futex — The Linux Kernel's Secret Weapon

### The Problem Futex Solves

Prior to futex (Linux 2.6), every mutex operation (even uncontended) required a system call. System calls cost 100-1000ns (due to privilege level switch, TLB flush on some architectures, kernel stack setup). For low-contention locks, this is catastrophic.

**Futex insight**: In the common case (no contention), locking should be **entirely in user space** with no kernel involvement. The kernel is only invoked when we actually need to sleep or wake.

### Futex Architecture

A futex is just a 4-byte integer in user memory, shared between user space and kernel:

```c
// The two core syscalls:
futex(addr, FUTEX_WAIT, expected_val, timeout, ...)
// If *addr == expected_val, sleep; otherwise return EAGAIN immediately

futex(addr, FUTEX_WAKE, num_to_wake, ...)
// Wake up to num_to_wake threads sleeping on addr
```

**Fast path (no contention):** CAS entirely in user space. No syscall. ~10ns.
**Slow path (contention):** `futex(FUTEX_WAIT)` → kernel hashes `addr` → thread added to hash bucket wait queue → sleeps.
**Release path:** CAS in user space. If waiters exist, `futex(FUTEX_WAKE)` → kernel finds wait queue → wakes thread.

### Futex Internals: The Hash Table

The kernel maintains a global hash table of **futex wait queues**, indexed by the physical address of the futex word. This means:
- Different addresses with different physical backing map to different buckets.
- Shared memory futexes between processes work correctly (hashed by physical address, not virtual).

```
user space: |u32 futex_word| at virtual addr 0x7fff...
                    |
              [kernel maps to physical addr]
                    |
kernel: hash_table[hash(phys_addr)] → linked list of sleeping tasks
```

### Private vs Shared Futex

```c
FUTEX_WAIT_PRIVATE  // faster: hashed by virtual address (same process only)
FUTEX_WAIT          // slower: hashed by physical address (cross-process)
```

glibc uses `FUTEX_WAIT_PRIVATE` for `pthread_mutex_t` by default since threads share an address space.

### Futex Requeue (FUTEX_REQUEUE)

`FUTEX_REQUEUE` atomically moves waiters from one futex to another. This is used by `pthread_cond_broadcast`:

```c
// When signaling a condition variable, move sleepers from cv's futex
// to the mutex's futex, so they compete for the mutex on wake:
futex(&cv->__data.__futex, FUTEX_REQUEUE_PRIVATE, 1, INT_MAX,
      &mutex->__data.__lock, 0);
```

Without this, waking all CV waiters would cause a **thundering herd** — all trying to acquire the mutex simultaneously. Requeue serializes them through the mutex queue.

---

## 10. Deadlock

### Definition

A **deadlock** is a state where a set of threads are each waiting for a resource held by another thread in the set, forming a cycle. No thread can proceed. The system is permanently frozen.

### The Four Coffman Conditions (1971)

Deadlock requires **all four** conditions simultaneously. Eliminating any one prevents deadlock.

1. **Mutual Exclusion**: Resources cannot be shared — only one thread can hold a resource at a time.
2. **Hold and Wait**: A thread holds at least one resource while waiting for additional resources.
3. **No Preemption**: Resources cannot be forcibly taken from a thread — only voluntarily released.
4. **Circular Wait**: A circular chain of threads where each thread waits for a resource held by the next thread in the chain.

### Resource Allocation Graph (RAG)

A deadlock can be detected by finding a **cycle** in the Resource Allocation Graph:

```
Nodes: Threads (T1, T2) and Resources (R1, R2)
Edges:
  T → R: Thread T is requesting Resource R (request edge)
  R → T: Resource R is assigned to Thread T (assignment edge)

Deadlock ↔ Cycle in the graph (for single-instance resources)
```

```
T1 → R1 → T2 → R2 → T1  (cycle = deadlock)
```

### Classic Example: Dining Philosophers

Five philosophers sit at a round table, each needing two forks (shared with neighbors). If all simultaneously pick up their left fork:

```
Philosopher 1: holds fork 1, waits for fork 2
Philosopher 2: holds fork 2, waits for fork 3
Philosopher 3: holds fork 3, waits for fork 4
Philosopher 4: holds fork 4, waits for fork 5
Philosopher 5: holds fork 5, waits for fork 1  ← CYCLE
```

**Solutions:**
1. **Impose ordering**: Always pick up the lower-numbered fork first (breaks circular wait).
2. **Allow at most N-1 philosophers to eat simultaneously** (breaks hold-and-wait).
3. **Try-lock with timeout**: Use `trylock()` — if second fork unavailable, release first and retry.
4. **Chandy-Misra solution**: Token-based, allows parallelism.

### Deadlock Prevention Strategies

#### 1. Lock Ordering (Hierarchical Locking)
Assign a global total order to all locks. Always acquire in increasing order. Never hold lock N while acquiring lock M if M < N.

```c
// Define a canonical order:
// account_lock has order by account ID
void transfer(Account *from, Account *to, int amount) {
    Account *first  = (from->id < to->id) ? from : to;
    Account *second = (from->id < to->id) ? to   : from;
    lock(first->mutex);
    lock(second->mutex);
    // transfer...
    unlock(second->mutex);
    unlock(first->mutex);
}
```

#### 2. Try-Lock with Backoff
```c
while (true) {
    lock(mutex_a);
    if (trylock(mutex_b)) {
        // critical section
        unlock(mutex_b);
        unlock(mutex_a);
        break;
    }
    unlock(mutex_a);
    // exponential backoff to reduce livelock risk
    sleep(random_backoff());
}
```

#### 3. Resource Preemption
If thread T1 needs a resource held by T2 and T2 is waiting, preempt T2's resource. Requires rollback mechanism.

#### 4. Banker's Algorithm (Deadlock Avoidance)
Before granting a resource request, simulate the future state and verify it remains **safe** (a safe state has at least one execution order where all threads can complete). If unsafe, block the requester until safe.

```
Safe state: ∃ sequence [T1, T2, ..., Tn] such that for each Ti,
            Ti's remaining resource needs ≤ available resources
            + resources released by T1..T(i-1)
```

Too expensive for real-time use; used in batch systems.

### Deadlock Detection

Rather than prevent deadlock, detect it after the fact and recover:

1. Maintain the RAG. Periodically run cycle detection (DFS).
2. On cycle detection: kill one thread in the cycle (the "victim"), rollback its state, release its resources.

**Linux kernel deadlock detection: lockdep**

The kernel's `lockdep` subsystem is a runtime deadlock validator:

```c
// lockdep tracks every lock acquisition order:
// If thread A acquires lock X then Y, lockdep records: X → Y
// If thread B acquires Y then X, lockdep reports: POTENTIAL DEADLOCK

// Enable in kernel config:
CONFIG_DEBUG_LOCKDEP=y
CONFIG_PROVE_LOCKING=y
CONFIG_LOCK_STAT=y
```

lockdep maintains a directed graph of lock class acquisition orders and reports cycles immediately when a violating acquisition occurs — even before the actual deadlock happens. It has found hundreds of real kernel deadlocks.

### ABBA Deadlock Pattern

The most common deadlock in practice:

```
Thread A:                 Thread B:
lock(mutex_A)            lock(mutex_B)
lock(mutex_B)  ← waits  lock(mutex_A)  ← waits
```

Fix: Consistent acquisition order. Use lockdep.

---

## 11. Livelock

### Definition

A **livelock** is a state where threads are **active** (not sleeping, not blocked on OS wait) but making **no progress** because they keep reacting to each other's state changes in a cycle.

Unlike deadlock (threads are frozen), in a livelock threads appear busy — CPU usage may be high — but the system makes no useful progress.

### The Classic Hallway Livelock

Two people walking toward each other in a hallway:
- Person A steps right.
- Person B, also stepping right (from B's perspective, left), both block.
- A steps left. B steps left. Both block again.
- They mirror each other indefinitely.

### Livelock in Lock Acquisition

```
Thread A:                         Thread B:
loop:                             loop:
  lock(mutex_a)                     lock(mutex_b)
  if !trylock(mutex_b):             if !trylock(mutex_a):
    unlock(mutex_a)                   unlock(mutex_b)
    sleep(10ms)    ← both sleep      sleep(10ms) ← same time!
    continue                          continue
  break                             break
```

If A and B always retry at the same time, they will always collide. This is livelock: both threads are running, both making state changes, but neither makes progress.

### Livelock vs Deadlock Comparison

| Property           | Deadlock                    | Livelock                         |
|--------------------|-----------------------------|----------------------------------|
| Thread state       | Blocked/sleeping            | Running (busy)                   |
| CPU usage          | Low/zero                    | High (spinning)                  |
| Progress           | None                        | None                             |
| Visibility         | Easy to detect (stalled)    | Hard to detect (looks busy)      |
| Resolution         | Kill/rollback a thread      | Randomized backoff               |

### Livelock Solutions

1. **Randomized exponential backoff**: Add `sleep(random() % max_wait)` before retry. Breaks synchrony.
2. **Priority-based resolution**: Assign priorities; lower-priority thread always yields to higher.
3. **Token-based resolution**: Use a separate protocol (leader election) to determine who proceeds first.
4. **Deterministic tie-breaking**: Use thread ID to determine who retries first.

```c
// Randomized backoff prevents livelock:
int backoff = INITIAL_BACKOFF;
while (true) {
    lock(mutex_a);
    if (trylock(mutex_b)) break;
    unlock(mutex_a);
    usleep(rand() % backoff);    // randomized delay
    backoff = min(backoff * 2, MAX_BACKOFF);  // exponential growth
}
```

---

## 12. Starvation

### Definition

**Starvation** occurs when a thread is perpetually denied access to a resource it needs, even though the system is making overall progress. Unlike livelock, other threads are making progress — just not the starving thread.

### Causes

1. **Unfair scheduling**: Non-FIFO lock implementations where newly arriving threads can steal the lock from long-waiting ones.
2. **Priority inversion** (without inheritance): A low-priority thread holds a lock that a high-priority thread needs, but medium-priority threads keep preempting the low-priority thread.
3. **Greedy algorithms**: A thread checking a resource and finding it busy may keep checking while new requesters keep arriving.
4. **Reader-heavy rwlocks**: Continuous readers block a writer indefinitely.

### Solution: Fairness

**FIFO queuing** in lock implementations (ticket locks, MCS locks) guarantees bounded waiting — by definition, no starvation.

**Aging**: Increase a thread's priority the longer it waits. Eventually, it becomes the highest-priority waiter and gets the resource.

---

## 13. Priority Inversion

### The Mars Pathfinder Bug (1997)

The Mars Pathfinder spacecraft experienced repeated system resets. Root cause: **priority inversion** due to shared mutex between three tasks:

- High-priority: Information bus manager (time-critical)
- Medium-priority: Communications task
- Low-priority: Meteorological data gathering

The low-priority task held a mutex. The high-priority task waited for it. The medium-priority task preempted the low-priority task (since medium > low). Result: The high-priority task was effectively blocked by the medium-priority task — priority inversion.

### Priority Inheritance Protocol

**Solution**: When a high-priority thread blocks on a mutex, temporarily **elevate the priority** of the mutex owner to that of the blocked high-priority thread, so it can complete and release the mutex quickly.

```
H (priority=10) blocks on mutex held by L (priority=1)
  → L's priority elevated to 10
  → L preempts M (priority=5) — because now L has priority 10
  → L releases mutex
  → L's priority restored to 1
  → H acquires mutex, runs
```

Linux `pthread_mutex_t` supports this via `PTHREAD_PRIO_INHERIT` protocol:
```c
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
pthread_mutex_init(&mutex, &attr);
```

The Linux kernel's `rtmutex` implements priority inheritance for real-time tasks (CONFIG_PREEMPT_RT).

### Priority Ceiling Protocol

Alternative: Assign each mutex a **ceiling priority** equal to the highest priority of any thread that can lock it. Any thread locking the mutex is temporarily elevated to the ceiling priority. Prevents priority inversion entirely and also prevents deadlock.

---

## 14. Lock-Free and Wait-Free Algorithms

### Definitions

**Lock-free**: At least one thread makes progress in any finite number of steps. Individual threads can starve, but the system as a whole always progresses.

**Wait-free**: Every thread makes progress in a finite number of its own steps. No starvation possible. Much harder to design.

**Obstruction-free**: A thread makes progress if it runs in isolation (no other threads interfere). Weakest guarantee.

### Lock-Free Stack with CAS

```c
struct Node {
    int value;
    struct Node *next;
};

struct Stack {
    _Atomic(struct Node*) top;
};

void push(struct Stack *s, struct Node *node) {
    struct Node *old_top;
    do {
        old_top = atomic_load(&s->top);
        node->next = old_top;
    } while (!atomic_compare_exchange_weak(&s->top, &old_top, node));
}

struct Node *pop(struct Stack *s) {
    struct Node *old_top, *new_top;
    do {
        old_top = atomic_load(&s->top);
        if (old_top == NULL) return NULL;
        new_top = old_top->next;
    } while (!atomic_compare_exchange_weak(&s->top, &old_top, new_top));
    return old_top;
}
```

**ABA Problem**: Thread A reads top=X. Thread B pops X, pushes Y, pops Y, pushes X again. Thread A's CAS succeeds (top still == X) but the stack state has changed — `X->next` may be dangling.

**Solutions to ABA**:
1. **Tagged pointers**: Use low bits or a separate counter packed into the pointer.
2. **Hazard pointers**: Mark pointers in use; defer reclamation until no thread references them.
3. **Epoch-based reclamation** (used in Rust's `crossbeam`): Divide time into epochs; reclaim only when all threads have advanced past the epoch.
4. **LL/SC on ARM**: Naturally avoids ABA because the exclusive monitor tracks the physical address state.

---

## 15. Linux Kernel Synchronization Internals

### The Lock Hierarchy in Linux

The Linux kernel uses many synchronization mechanisms for different contexts:

```
Context:              Permitted primitives:
IRQ handler           spinlock (IRQ-safe), atomic ops, RCU read
Softirq/tasklet       spinlock, atomic ops, RCU read
Process context       mutex, semaphore, spinlock, rwlock, rwsem, RCU
Kernel thread         mutex, semaphore, spinlock, rwlock, rwsem, RCU
```

### RCU — Read-Copy-Update

RCU is the most important synchronization mechanism in the Linux kernel, used pervasively for read-heavy data structures (routing tables, process lists, network device lists).

**Core idea**: Readers are **completely lockless** and never block writers. Writers make a copy, modify the copy, then atomically publish the new pointer. Old copies are freed only after all readers that saw the old pointer have finished.

```
Read side:
    rcu_read_lock();          // marks entry into RCU read-side critical section
    p = rcu_dereference(ptr); // safely load RCU-protected pointer
    // use p->data
    rcu_read_unlock();        // marks exit

Write side:
    new_node = kmalloc(...);
    *new_node = *old_node;    // copy
    new_node->value = new_value;  // modify copy
    rcu_assign_pointer(ptr, new_node); // publish (with memory barrier)
    synchronize_rcu();        // wait for all readers of old_node to finish
    kfree(old_node);          // safe to reclaim
```

**Grace period**: The time between publishing the new pointer and reclaiming the old. `synchronize_rcu()` blocks until every CPU has passed through a **quiescent state** (context switch, idle loop, user space execution) — proving all pre-existing read-side critical sections have ended.

**RCU guarantees**:
- Read side: O(1) overhead, zero cache line dirtying, no memory barriers on x86.
- Write side: occasional `synchronize_rcu()` (can be expensive in latency, not CPU).
- Memory: The old version must be kept until the grace period ends.

### Atomic Operations in the Kernel

```c
atomic_t v = ATOMIC_INIT(0);    // 32-bit atomic
atomic64_t v64;                  // 64-bit atomic

atomic_set(&v, 5);
atomic_read(&v);
atomic_add(3, &v);
atomic_sub(2, &v);
atomic_inc(&v);
atomic_dec(&v);
atomic_inc_return(&v);           // returns new value
atomic_cmpxchg(&v, old, new);   // CAS
atomic_xchg(&v, new);           // exchange

// Bit operations:
set_bit(nr, &word);
clear_bit(nr, &word);
test_and_set_bit(nr, &word);
test_and_clear_bit(nr, &word);
```

### Completion Variables

A completion is a one-time signaling mechanism — thread A signals completion, thread B waits for it:

```c
struct completion done;
init_completion(&done);

// Thread B:
wait_for_completion(&done);  // blocks until signaled

// Thread A:
complete(&done);              // wake Thread B
complete_all(&done);          // wake all waiters
```

Used for kernel thread synchronization, DMA completion, device probe synchronization.

### Per-CPU Variables

Per-CPU variables are the ultimate way to avoid synchronization overhead for frequently updated counters and caches:

```c
DEFINE_PER_CPU(int, my_counter);

// On each CPU, accesses are local (no cache coherency traffic):
int val = get_cpu_var(my_counter);  // disables preemption
put_cpu_var(my_counter);

// For read-mostly with rare updates:
this_cpu_inc(my_counter);           // single-instruction atomic on same CPU
```

Per-CPU data eliminates false sharing entirely — each CPU has its own copy. Aggregation happens only when a global sum is needed.

### SRCU — Sleepable RCU

Regular RCU read-side critical sections cannot sleep. SRCU (Sleepable RCU) relaxes this:

```c
struct srcu_struct my_srcu;
init_srcu_struct(&my_srcu);

// Read side (can sleep):
idx = srcu_read_lock(&my_srcu);
// ... can schedule here ...
srcu_read_unlock(&my_srcu, idx);

// Write side:
synchronize_srcu(&my_srcu);  // waits for all readers
```

Used in kernel notifier chains, module unloading, NFS.

---

## 16. C Implementations

### Complete Spinlock Implementation

```c
#include <stdatomic.h>
#include <stdbool.h>
#include <sched.h>
#include <stdint.h>

/* ─── Test-and-Set Spinlock ─── */

typedef struct {
    atomic_flag locked;
} tas_spinlock_t;

#define TAS_SPINLOCK_INIT { .locked = ATOMIC_FLAG_INIT }

static inline void tas_spinlock_lock(tas_spinlock_t *lock) {
    while (atomic_flag_test_and_set_explicit(&lock->locked, memory_order_acquire)) {
        /* PAUSE hint: reduces power, avoids memory order violation flushes */
        __asm__ volatile("pause" ::: "memory");
    }
}

static inline bool tas_spinlock_trylock(tas_spinlock_t *lock) {
    return !atomic_flag_test_and_set_explicit(&lock->locked, memory_order_acquire);
}

static inline void tas_spinlock_unlock(tas_spinlock_t *lock) {
    atomic_flag_clear_explicit(&lock->locked, memory_order_release);
}

/* ─── Ticket Spinlock (FIFO, fair) ─── */

typedef struct {
    _Atomic uint32_t ticket;   /* next ticket to issue */
    _Atomic uint32_t serving;  /* currently serving   */
} ticket_spinlock_t;

#define TICKET_SPINLOCK_INIT { .ticket = 0, .serving = 0 }

static inline void ticket_spinlock_lock(ticket_spinlock_t *lock) {
    uint32_t my_ticket = atomic_fetch_add_explicit(
        &lock->ticket, 1, memory_order_relaxed);
    
    while (atomic_load_explicit(&lock->serving, memory_order_acquire) != my_ticket) {
        __asm__ volatile("pause" ::: "memory");
    }
}

static inline void ticket_spinlock_unlock(ticket_spinlock_t *lock) {
    /* Only the current owner calls this — no CAS needed */
    uint32_t current = atomic_load_explicit(&lock->serving, memory_order_relaxed);
    atomic_store_explicit(&lock->serving, current + 1, memory_order_release);
}

/* ─── MCS Spinlock (scalable, zero cache bouncing) ─── */

typedef struct mcs_node {
    _Atomic(struct mcs_node *) next;
    atomic_int                 locked; /* spin on this field */
    /* Pad to cache line to prevent false sharing with neighboring nodes */
    char _pad[64 - sizeof(void*) - sizeof(int)];
} mcs_node_t;

typedef struct {
    _Atomic(mcs_node_t *) tail;
} mcs_spinlock_t;

#define MCS_SPINLOCK_INIT { .tail = NULL }

static inline void mcs_spinlock_lock(mcs_spinlock_t *lock, mcs_node_t *node) {
    atomic_store_explicit(&node->next, NULL, memory_order_relaxed);
    atomic_store_explicit(&node->locked, 1, memory_order_relaxed);

    /* Atomically put ourselves at the end of the queue */
    mcs_node_t *prev = atomic_exchange_explicit(
        &lock->tail, node, memory_order_acq_rel);
    
    if (prev != NULL) {
        /* There was a predecessor — link ourselves in */
        atomic_store_explicit(&prev->next, node, memory_order_release);
        /* Spin on OUR OWN node — no shared cache line bouncing */
        while (atomic_load_explicit(&node->locked, memory_order_acquire)) {
            __asm__ volatile("pause" ::: "memory");
        }
    }
    /* If prev == NULL, we were the first — we own the lock directly */
}

static inline void mcs_spinlock_unlock(mcs_spinlock_t *lock, mcs_node_t *node) {
    mcs_node_t *next = atomic_load_explicit(&node->next, memory_order_relaxed);

    if (next == NULL) {
        /* Optimistic: try to clear the tail (we might be the last) */
        mcs_node_t *expected = node;
        if (atomic_compare_exchange_strong_explicit(
                &lock->tail, &expected, NULL,
                memory_order_release, memory_order_relaxed)) {
            return; /* success — no one else in queue */
        }
        /* Another thread is in the process of enqueuing — wait for next pointer */
        while ((next = atomic_load_explicit(&node->next, memory_order_acquire)) == NULL) {
            __asm__ volatile("pause" ::: "memory");
        }
    }
    /* Wake the next waiter by clearing their locked flag */
    atomic_store_explicit(&next->locked, 0, memory_order_release);
}
```

### Complete Mutex Implementation (Futex-based)

```c
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdatomic.h>
#include <errno.h>

/*
 * Three-state futex mutex — mirrors glibc's implementation:
 *   0 = UNLOCKED
 *   1 = LOCKED, no waiters
 *   2 = LOCKED, waiters present
 *
 * Fast path: pure user-space CAS, zero syscalls
 * Slow path: futex_wait / futex_wake
 */

typedef struct {
    atomic_int state; /* 0=unlocked, 1=locked, 2=locked+waiters */
} futex_mutex_t;

#define FUTEX_MUTEX_INIT { .state = ATOMIC_VAR_INIT(0) }

static int futex_wait(atomic_int *addr, int expected) {
    return syscall(SYS_futex, addr, FUTEX_WAIT_PRIVATE, expected, NULL, NULL, 0);
}

static int futex_wake(atomic_int *addr, int num) {
    return syscall(SYS_futex, addr, FUTEX_WAKE_PRIVATE, num, NULL, NULL, 0);
}

void futex_mutex_lock(futex_mutex_t *m) {
    int expected = 0;
    
    /* Fast path: try to go 0 → 1 (no waiters) */
    if (atomic_compare_exchange_strong_explicit(
            &m->state, &expected, 1,
            memory_order_acquire, memory_order_relaxed)) {
        return; /* acquired — common case, zero syscall */
    }
    
    /* Slow path */
    do {
        /* Mark that we're a waiter: transition to state 2 if not already */
        if (expected == 2 ||
            atomic_compare_exchange_strong_explicit(
                &m->state, &expected, 2,
                memory_order_acquire, memory_order_relaxed)) {
            /*
             * Sleep if state is still 2. 
             * If state changed (lock released), futex_wait returns immediately.
             */
            futex_wait(&m->state, 2);
        }
        expected = 0;
        /* Retry: attempt to claim the lock by setting 0 → 2 (we know there are waiters) */
    } while (!atomic_compare_exchange_strong_explicit(
                 &m->state, &expected, 2,
                 memory_order_acquire, memory_order_relaxed));
}

void futex_mutex_unlock(futex_mutex_t *m) {
    int old = atomic_fetch_sub_explicit(&m->state, 1, memory_order_release);
    if (old != 1) {
        /* There were waiters (old == 2): wake one */
        atomic_store_explicit(&m->state, 0, memory_order_release);
        futex_wake(&m->state, 1);
    }
    /* If old == 1: no waiters, we already set state to 0 via fetch_sub. Done. */
}

bool futex_mutex_trylock(futex_mutex_t *m) {
    int expected = 0;
    return atomic_compare_exchange_strong_explicit(
        &m->state, &expected, 1,
        memory_order_acquire, memory_order_relaxed);
}
```

### Semaphore Implementation

```c
#include <stdatomic.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>

typedef struct {
    atomic_int count;
} semaphore_t;

void sem_init_custom(semaphore_t *s, int initial) {
    atomic_store_explicit(&s->count, initial, memory_order_relaxed);
}

void sem_wait_custom(semaphore_t *s) {
    int c;
    while (true) {
        /* Try to decrement if positive */
        c = atomic_load_explicit(&s->count, memory_order_relaxed);
        while (c > 0) {
            if (atomic_compare_exchange_weak_explicit(
                    &s->count, &c, c - 1,
                    memory_order_acquire, memory_order_relaxed)) {
                return; /* successfully decremented */
            }
            /* CAS failed — c was updated, retry inner loop */
        }
        /* count is 0 (or negative) — sleep */
        syscall(SYS_futex, &s->count, FUTEX_WAIT_PRIVATE, c, NULL, NULL, 0);
        /* On wake, retry from the top */
    }
}

void sem_post_custom(semaphore_t *s) {
    int old = atomic_fetch_add_explicit(&s->count, 1, memory_order_release);
    if (old <= 0) {
        /* There might be sleepers — wake one */
        syscall(SYS_futex, &s->count, FUTEX_WAKE_PRIVATE, 1, NULL, NULL, 0);
    }
}

/* ─── Monitor (Mutex + Condition Variable) ─── */

#include <pthread.h>
#include <stdlib.h>

#define BUFFER_SIZE 16

typedef struct {
    int         buffer[BUFFER_SIZE];
    int         head, tail, count;
    pthread_mutex_t  lock;
    pthread_cond_t   not_full;
    pthread_cond_t   not_empty;
} bounded_buffer_t;

void bb_init(bounded_buffer_t *bb) {
    bb->head = bb->tail = bb->count = 0;
    pthread_mutex_init(&bb->lock, NULL);
    pthread_cond_init(&bb->not_full, NULL);
    pthread_cond_init(&bb->not_empty, NULL);
}

void bb_produce(bounded_buffer_t *bb, int item) {
    pthread_mutex_lock(&bb->lock);
    
    /* Always use while — Mesa semantics + spurious wakeups */
    while (bb->count == BUFFER_SIZE) {
        pthread_cond_wait(&bb->not_full, &bb->lock);
    }
    
    bb->buffer[bb->tail] = item;
    bb->tail = (bb->tail + 1) % BUFFER_SIZE;
    bb->count++;
    
    pthread_cond_signal(&bb->not_empty); /* wake one consumer */
    pthread_mutex_unlock(&bb->lock);
}

int bb_consume(bounded_buffer_t *bb) {
    pthread_mutex_lock(&bb->lock);
    
    while (bb->count == 0) {
        pthread_cond_wait(&bb->not_empty, &bb->lock);
    }
    
    int item = bb->buffer[bb->head];
    bb->head = (bb->head + 1) % BUFFER_SIZE;
    bb->count--;
    
    pthread_cond_signal(&bb->not_full);
    pthread_mutex_unlock(&bb->lock);
    return item;
}

/* ─── Deadlock Demo and Prevention ─── */

#include <stdio.h>
#include <pthread.h>

pthread_mutex_t mutex_a = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t mutex_b = PTHREAD_MUTEX_INITIALIZER;

/* DEADLOCK-PRONE: Thread 1 locks A then B; Thread 2 locks B then A */
void *deadlock_thread1(void *arg) {
    pthread_mutex_lock(&mutex_a);
    usleep(1000); /* context switch here makes deadlock likely */
    pthread_mutex_lock(&mutex_b); /* <── may deadlock */
    /* critical section */
    pthread_mutex_unlock(&mutex_b);
    pthread_mutex_unlock(&mutex_a);
    return NULL;
}

void *deadlock_thread2(void *arg) {
    pthread_mutex_lock(&mutex_b); /* <── may deadlock */
    pthread_mutex_lock(&mutex_a);
    pthread_mutex_unlock(&mutex_a);
    pthread_mutex_unlock(&mutex_b);
    return NULL;
}

/* DEADLOCK-FREE: Use consistent lock ordering */
pthread_mutex_t *lock_order_min(pthread_mutex_t *a, pthread_mutex_t *b) {
    return (uintptr_t)a < (uintptr_t)b ? a : b;
}
pthread_mutex_t *lock_order_max(pthread_mutex_t *a, pthread_mutex_t *b) {
    return (uintptr_t)a > (uintptr_t)b ? a : b;
}

void safe_double_lock(pthread_mutex_t *a, pthread_mutex_t *b) {
    pthread_mutex_lock(lock_order_min(a, b));
    pthread_mutex_lock(lock_order_max(a, b));
}
```

### Read-Write Lock with Seqlock

```c
#include <stdatomic.h>

typedef struct {
    atomic_uint sequence;  /* even = stable, odd = write in progress */
    char _pad[60];         /* align data to separate cache lines */
    /* protected data follows... */
} seqlock_t;

#define SEQLOCK_INIT { .sequence = ATOMIC_VAR_INIT(0) }

/* Writer: increment sequence (odd), write, increment again (even) */
static inline void seqlock_write_begin(seqlock_t *sl) {
    unsigned s = atomic_fetch_add_explicit(&sl->sequence, 1, memory_order_acquire);
    (void)s;
    /* Now sequence is odd — readers will retry */
}

static inline void seqlock_write_end(seqlock_t *sl) {
    atomic_fetch_add_explicit(&sl->sequence, 1, memory_order_release);
    /* Now sequence is even — readers can validate */
}

/* Reader: read sequence, read data, re-read sequence, compare */
static inline unsigned seqlock_read_begin(seqlock_t *sl) {
    unsigned seq;
    do {
        seq = atomic_load_explicit(&sl->sequence, memory_order_acquire);
    } while (seq & 1); /* spin while odd (write in progress) */
    return seq;
}

static inline int seqlock_read_retry(seqlock_t *sl, unsigned seq) {
    /* Returns non-zero if data was modified during our read */
    atomic_thread_fence(memory_order_acquire);
    return atomic_load_explicit(&sl->sequence, memory_order_relaxed) != seq;
}

/* Usage: */
typedef struct {
    seqlock_t sl;
    int x, y;
} point_t;

void read_point(point_t *p, int *x, int *y) {
    unsigned seq;
    do {
        seq = seqlock_read_begin(&p->sl);
        *x = p->x;
        *y = p->y;
    } while (seqlock_read_retry(&p->sl, seq));
}

void write_point(point_t *p, int x, int y) {
    seqlock_write_begin(&p->sl);
    p->x = x;
    p->y = y;
    seqlock_write_end(&p->sl);
}
```

---

## 17. Go Implementations

Go's concurrency model is built on CSP (Communicating Sequential Processes) — "Do not communicate by sharing memory; instead, share memory by communicating." However, Go also provides full mutex and synchronization primitives via `sync` and `sync/atomic` packages, as well as direct access to OS primitives via `syscall`.

### Go Runtime Synchronization Architecture

Go's goroutines are multiplexed onto OS threads (M:N threading). The runtime scheduler (work-stealing, G:M:P model) handles goroutine blocking:

- When a goroutine blocks on a mutex/channel, it is **descheduled** by the Go runtime — the OS thread is reused for another goroutine.
- This is much cheaper than OS thread blocking (~100ns vs ~10µs).
- `sync.Mutex` in Go is implemented with a combination of CAS, spinning, and OS-level futex waits.

### Go `sync.Mutex` Internals

```go
// From Go runtime source (simplified):
// State field bit layout:
//   bit 0: mutex locked
//   bit 1: goroutine awakened (about to acquire)
//   bit 2: starvation mode
//   bits 3+: count of goroutines waiting

// Go mutex has TWO modes:
// Normal mode: FIFO queue, but a newly woken goroutine competes with new arrivals
//              (new arrivals often win due to being on CPU — better throughput)
// Starvation mode: engaged if goroutine waits > 1ms
//                  next unlocker passes lock directly to oldest waiter
//                  prevents starvation at cost of throughput

// This adaptive behavior is the key insight in Go's mutex design.
```

### Mutex and Condition Variable

```go
package sync_primitives

import (
    "sync"
    "time"
)

// ─── Basic Mutex Usage ───

type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock() // defer ensures unlock even on panic
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// ─── RWMutex for Read-Heavy Workloads ───

type ReadHeavyCache struct {
    mu    sync.RWMutex
    store map[string]string
}

func (c *ReadHeavyCache) Get(key string) (string, bool) {
    c.mu.RLock()         // multiple goroutines can hold RLock simultaneously
    defer c.mu.RUnlock()
    val, ok := c.store[key]
    return val, ok
}

func (c *ReadHeavyCache) Set(key, val string) {
    c.mu.Lock()          // exclusive — blocks all readers and writers
    defer c.mu.Unlock()
    c.store[key] = val
}

// ─── Monitor Pattern: Bounded Buffer ───

type BoundedBuffer[T any] struct {
    mu       sync.Mutex
    notFull  *sync.Cond
    notEmpty *sync.Cond
    buf      []T
    head     int
    tail     int
    count    int
    cap      int
}

func NewBoundedBuffer[T any](capacity int) *BoundedBuffer[T] {
    bb := &BoundedBuffer[T]{
        buf: make([]T, capacity),
        cap: capacity,
    }
    bb.notFull = sync.NewCond(&bb.mu)
    bb.notEmpty = sync.NewCond(&bb.mu)
    return bb
}

func (bb *BoundedBuffer[T]) Put(item T) {
    bb.mu.Lock()
    defer bb.mu.Unlock()
    
    // ALWAYS use for loop — Mesa semantics + spurious wakeups
    for bb.count == bb.cap {
        bb.notFull.Wait() // atomically releases lock and sleeps
    }
    
    bb.buf[bb.tail] = item
    bb.tail = (bb.tail + 1) % bb.cap
    bb.count++
    bb.notEmpty.Signal() // wake one consumer
}

func (bb *BoundedBuffer[T]) Get() T {
    bb.mu.Lock()
    defer bb.mu.Unlock()
    
    for bb.count == 0 {
        bb.notEmpty.Wait()
    }
    
    item := bb.buf[bb.head]
    bb.head = (bb.head + 1) % bb.cap
    bb.count--
    bb.notFull.Signal()
    return item
}

// ─── Semaphore in Go (no built-in, build with channel) ───

type Semaphore struct {
    tokens chan struct{}
}

func NewSemaphore(n int) *Semaphore {
    s := &Semaphore{tokens: make(chan struct{}, n)}
    for i := 0; i < n; i++ {
        s.tokens <- struct{}{}
    }
    return s
}

func (s *Semaphore) Acquire() {
    <-s.tokens // blocks until a token is available
}

func (s *Semaphore) TryAcquire() bool {
    select {
    case <-s.tokens:
        return true
    default:
        return false
    }
}

func (s *Semaphore) AcquireTimeout(d time.Duration) bool {
    select {
    case <-s.tokens:
        return true
    case <-time.After(d):
        return false
    }
}

func (s *Semaphore) Release() {
    s.tokens <- struct{}{}
}

// ─── Spinlock in Go (when you need it) ───

import "sync/atomic"

type SpinLock struct {
    state atomic.Int32
}

func (sl *SpinLock) Lock() {
    for !sl.state.CompareAndSwap(0, 1) {
        // runtime.Gosched() yields the goroutine scheduler,
        // allowing other goroutines to run — important on GOMAXPROCS=1
        // In tight hot loops on multicore, this can be omitted.
        // For kernel-like behavior with spinning:
        for i := 0; i < 30; i++ {
            // ~30 PAUSE-equivalent spins before yielding
            _ = sl.state.Load()
        }
    }
}

func (sl *SpinLock) Unlock() {
    sl.state.Store(0)
}

// ─── Deadlock Detection Pattern ───

// Go's race detector and deadlock detector:
// go run -race ./...          detects data races at runtime
// A goroutine blocked forever = deadlock → Go runtime panics with "all goroutines are asleep - deadlock!"

// Deadlock prevention via lock ordering:
type OrderedLock struct {
    id   uint64
    mu   sync.Mutex
}

var globalLockOrder atomic.Uint64

func NewOrderedLock() *OrderedLock {
    return &OrderedLock{id: globalLockOrder.Add(1)}
}

// Always lock lower-ID first:
func LockPair(a, b *OrderedLock) {
    if a.id < b.id {
        a.mu.Lock()
        b.mu.Lock()
    } else {
        b.mu.Lock()
        a.mu.Lock()
    }
}

func UnlockPair(a, b *OrderedLock) {
    a.mu.Unlock()
    b.mu.Unlock()
}
```

### Go Channel-Based Synchronization

```go
package channel_sync

// Channels in Go are first-class synchronization:
// - Unbuffered channel: synchronizes sender and receiver (rendezvous)
// - Buffered channel:   semaphore-like, capacity = token count

// ─── Worker Pool (Semaphore pattern) ───

func WorkerPool(jobs <-chan int, results chan<- int, numWorkers int) {
    var wg sync.WaitGroup
    sem := make(chan struct{}, numWorkers) // limit concurrency to numWorkers
    
    for job := range jobs {
        wg.Add(1)
        sem <- struct{}{}     // acquire slot (blocks if pool full)
        go func(j int) {
            defer wg.Done()
            defer func() { <-sem }() // release slot
            results <- processJob(j)
        }(job)
    }
    wg.Wait()
}

// ─── Once: Single-initialization (lazy singleton) ───

type LazyService struct {
    once sync.Once
    conn *Connection
}

func (s *LazyService) GetConn() *Connection {
    s.once.Do(func() {
        s.conn = newExpensiveConnection() // called exactly once, ever
    })
    return s.conn
}

// ─── sync/atomic for lock-free operations ───

import "sync/atomic"

type LockFreeStack[T any] struct {
    head atomic.Pointer[node[T]]
}

type node[T any] struct {
    value T
    next  *node[T]
}

func (s *LockFreeStack[T]) Push(val T) {
    newNode := &node[T]{value: val}
    for {
        old := s.head.Load()
        newNode.next = old
        if s.head.CompareAndSwap(old, newNode) {
            return
        }
        // CAS failed — another goroutine modified head, retry
    }
}

func (s *LockFreeStack[T]) Pop() (T, bool) {
    for {
        old := s.head.Load()
        if old == nil {
            var zero T
            return zero, false
        }
        if s.head.CompareAndSwap(old, old.next) {
            return old.value, true
        }
    }
}

// ─── Livelock Prevention with Randomized Backoff ───

import (
    "math/rand"
    "time"
)

func acquireWithBackoff(lockA, lockB *sync.Mutex) {
    backoff := time.Millisecond
    maxBackoff := time.Second
    
    for {
        lockA.Lock()
        if lockB.TryLock() {
            return // both acquired
        }
        lockA.Unlock()
        
        // Randomized exponential backoff prevents livelock
        jitter := time.Duration(rand.Int63n(int64(backoff)))
        time.Sleep(backoff + jitter)
        
        if backoff < maxBackoff {
            backoff *= 2
        }
    }
}
```

---

## 18. Rust Implementations

Rust's ownership system provides **compile-time data race prevention** — the type system encodes concurrency safety. There are no data races possible in safe Rust (the type system prevents them). Unsafe Rust allows raw pointer manipulation but requires the programmer to uphold the invariants manually.

### Rust's Send and Sync Traits

```rust
// Send: A type that can be transferred to another thread.
//       If T: Send, then T can be sent across thread boundaries.
//       Raw pointers are !Send (cannot cross threads without unsafe).

// Sync: A type where &T can be shared between threads.
//       If T: Sync, then &T: Send.
//       Most types with interior mutability need Sync to be safe.

// Arc<T>: T: Send + Sync → Arc<T>: Send + Sync (thread-safe reference counting)
// Rc<T>:  !Send, !Sync (single-thread reference counting only)
// Mutex<T>: T: Send → Mutex<T>: Send + Sync
// RefCell<T>: T: Send → RefCell<T>: Send but !Sync (not thread-safe)
```

### Core Synchronization Primitives

```rust
use std::sync::{Arc, Mutex, RwLock, Condvar, Once};
use std::sync::atomic::{AtomicI32, AtomicBool, AtomicPtr, Ordering};
use std::thread;
use std::time::Duration;
use std::collections::VecDeque;

// ─── Mutex<T>: Lock-protected Data ───
// Key Rust insight: the LOCK and the DATA are one unit — Mutex<T> owns the T.
// You CANNOT access T without holding the lock. Enforced at compile time.

fn mutex_example() {
    let counter = Arc::new(Mutex::new(0i64));

    let handles: Vec<_> = (0..8).map(|_| {
        let c = Arc::clone(&counter);
        thread::spawn(move || {
            for _ in 0..1000 {
                let mut val = c.lock().unwrap(); // MutexGuard<i64>
                *val += 1;
                // Guard dropped here → lock automatically released
                // RAII: impossible to forget to unlock
            }
        })
    }).collect();

    for h in handles { h.join().unwrap(); }
    println!("Final: {}", *counter.lock().unwrap()); // always 8000
}

// ─── RwLock<T>: Read-Write Lock ───

fn rwlock_example() {
    let cache = Arc::new(RwLock::new(std::collections::HashMap::<String, i32>::new()));

    // Multiple readers simultaneously:
    let readers: Vec<_> = (0..4).map(|_| {
        let c = Arc::clone(&cache);
        thread::spawn(move || {
            let guard = c.read().unwrap(); // RwLockReadGuard — shared, non-exclusive
            let _ = guard.get("key");
        })
    }).collect();

    // One writer (exclusive):
    let writer = {
        let c = Arc::clone(&cache);
        thread::spawn(move || {
            let mut guard = c.write().unwrap(); // RwLockWriteGuard — exclusive
            guard.insert("key".to_string(), 42);
        })
    };

    for r in readers { r.join().unwrap(); }
    writer.join().unwrap();
}

// ─── Condvar: Monitor Pattern ───
// Condvar is always paired with a Mutex in Rust.

struct BoundedBuffer<T> {
    inner: Mutex<BoundedBufferInner<T>>,
    not_full: Condvar,
    not_empty: Condvar,
}

struct BoundedBufferInner<T> {
    buf: VecDeque<T>,
    capacity: usize,
}

impl<T: Send> BoundedBuffer<T> {
    fn new(capacity: usize) -> Arc<Self> {
        Arc::new(BoundedBuffer {
            inner: Mutex::new(BoundedBufferInner {
                buf: VecDeque::with_capacity(capacity),
                capacity,
            }),
            not_full: Condvar::new(),
            not_empty: Condvar::new(),
        })
    }

    fn put(&self, item: T) {
        let mut guard = self.inner.lock().unwrap();
        
        // Must use loop — Mesa semantics
        guard = self.not_full.wait_while(guard, |inner| {
            inner.buf.len() == inner.capacity
        }).unwrap(); // wait_while loops automatically — idiomatic Rust
        
        guard.buf.push_back(item);
        self.not_empty.notify_one();
    }

    fn get(&self) -> T {
        let mut guard = self.inner.lock().unwrap();
        
        guard = self.not_empty.wait_while(guard, |inner| {
            inner.buf.is_empty()
        }).unwrap();
        
        let item = guard.buf.pop_front().unwrap();
        self.not_full.notify_one();
        item
    }
}

// ─── Atomic Operations ───

fn atomic_example() {
    let flag = Arc::new(AtomicBool::new(false));
    let data = Arc::new(Mutex::new(0i32));

    // Producer: write data, then set flag (release ordering publishes the write)
    let (f, d) = (Arc::clone(&flag), Arc::clone(&data));
    thread::spawn(move || {
        *d.lock().unwrap() = 42;
        f.store(true, Ordering::Release); // all prior writes visible to Acquire load
    });

    // Consumer: acquire-load synchronizes with release-store
    loop {
        if flag.load(Ordering::Acquire) {
            println!("Data: {}", *data.lock().unwrap()); // guaranteed to see 42
            break;
        }
        std::hint::spin_loop(); // CPU PAUSE hint
    }
}

// ─── Custom Spinlock in Rust ───

use std::sync::atomic::{AtomicBool, Ordering};
use std::cell::UnsafeCell;

pub struct SpinLock<T> {
    locked: AtomicBool,
    data: UnsafeCell<T>, // interior mutability, bypasses borrow checker
}

// SAFETY: We guarantee exclusive access via the atomic locked flag
unsafe impl<T: Send> Send for SpinLock<T> {}
unsafe impl<T: Send> Sync for SpinLock<T> {}

pub struct SpinLockGuard<'a, T> {
    lock: &'a SpinLock<T>,
}

impl<T> SpinLock<T> {
    pub fn new(data: T) -> Self {
        SpinLock {
            locked: AtomicBool::new(false),
            data: UnsafeCell::new(data),
        }
    }

    pub fn lock(&self) -> SpinLockGuard<'_, T> {
        while self.locked.compare_exchange_weak(
            false, true,
            Ordering::Acquire,  // success ordering: acquire (synchronizes with release on unlock)
            Ordering::Relaxed,  // failure ordering: just a load, no sync needed
        ).is_err() {
            // compare_exchange_weak may spuriously fail — use loop
            // Busy spin with pause hint:
            while self.locked.load(Ordering::Relaxed) {
                std::hint::spin_loop();
            }
        }
        SpinLockGuard { lock: self }
    }
}

impl<'a, T> std::ops::Deref for SpinLockGuard<'a, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: locked flag is set (acquire), so exclusive access guaranteed
        unsafe { &*self.lock.data.get() }
    }
}

impl<'a, T> std::ops::DerefMut for SpinLockGuard<'a, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<'a, T> Drop for SpinLockGuard<'a, T> {
    fn drop(&mut self) {
        // Release ordering: all prior writes are published before unlocking
        self.lock.locked.store(false, Ordering::Release);
    }
}

// ─── Lock-Free Stack with Epoch-Based Reclamation (crossbeam pattern) ───

use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

// WARNING: This implementation is simplified for illustration.
// In production, use crossbeam::epoch for safe memory reclamation.
struct LockFreeStack<T> {
    head: AtomicPtr<StackNode<T>>,
}

struct StackNode<T> {
    value: T,
    next: *mut StackNode<T>,
}

impl<T> LockFreeStack<T> {
    fn new() -> Self {
        LockFreeStack { head: AtomicPtr::new(ptr::null_mut()) }
    }

    fn push(&self, value: T) {
        let node = Box::into_raw(Box::new(StackNode {
            value,
            next: ptr::null_mut(),
        }));
        loop {
            let old_head = self.head.load(Ordering::Relaxed);
            unsafe { (*node).next = old_head; }
            match self.head.compare_exchange_weak(
                old_head, node,
                Ordering::Release, Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(_) => {} // retry
            }
        }
    }

    fn pop(&self) -> Option<T> {
        loop {
            let old_head = self.head.load(Ordering::Acquire);
            if old_head.is_null() {
                return None;
            }
            let new_head = unsafe { (*old_head).next };
            match self.head.compare_exchange_weak(
                old_head, new_head,
                Ordering::Acquire, Ordering::Relaxed,
            ) {
                Ok(_) => {
                    // SAFETY (simplified — real code needs hazard pointers/epochs):
                    let node = unsafe { Box::from_raw(old_head) };
                    return Some(node.value);
                }
                Err(_) => {} // retry
            }
        }
    }
}

// ─── Once: Thread-safe lazy initialization ───

use std::sync::Once;

static INIT: Once = Once::new();
static mut CONFIG: Option<Config> = None;

fn get_config() -> &'static Config {
    unsafe {
        INIT.call_once(|| {
            CONFIG = Some(load_config()); // called exactly once across all threads
        });
        CONFIG.as_ref().unwrap()
    }
}

// Or use std::sync::OnceLock (stable since Rust 1.70):
use std::sync::OnceLock;

static CONFIG_V2: OnceLock<Config> = OnceLock::new();

fn get_config_v2() -> &'static Config {
    CONFIG_V2.get_or_init(|| load_config()) // thread-safe, no unsafe needed
}

// ─── Deadlock Prevention via Type System ───
// Rust cannot prevent all deadlocks, but RAII ensures locks are always released.
// The lock ordering pattern:

fn safe_transfer(
    acc_a: &Arc<Mutex<i64>>,
    id_a: u64,
    acc_b: &Arc<Mutex<i64>>,
    id_b: u64,
    amount: i64,
) {
    // Lock in canonical order by ID
    let (_guard_low, _guard_high) = if id_a < id_b {
        let g1 = acc_a.lock().unwrap();
        let g2 = acc_b.lock().unwrap();
        (g1, g2) // both held; dropped in reverse order at end of scope
    } else {
        let g1 = acc_b.lock().unwrap();
        let g2 = acc_a.lock().unwrap();
        (g1, g2)
    };
    // perform transfer with both locks held...
}

// ─── Parking Lot Crate: Production-Grade Primitives ───
// parking_lot::Mutex is faster than std::sync::Mutex:
// - Uses futex directly, no allocation
// - Adaptive spinning before sleeping
// - Smaller memory footprint (1 byte vs 40 bytes)
// - unlock() cannot fail (no poisoning on panic by default)
//
// use parking_lot::{Mutex, RwLock, Condvar, ReentrantMutex};
```

### Rust: Semaphore with `tokio` (Async)

```rust
// For async Rust — tokio's semaphore for async contexts:
use tokio::sync::{Semaphore, Mutex as AsyncMutex};
use std::sync::Arc;

async fn connection_pool_example() {
    // Limit concurrent DB connections to 10:
    let sem = Arc::new(Semaphore::new(10));
    
    let mut handles = vec![];
    for i in 0..100 {
        let sem = Arc::clone(&sem);
        handles.push(tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap(); // blocks if 10 already acquired
            // Only 10 goroutines here at once
            do_database_work(i).await;
            // permit dropped = released automatically
        }));
    }
    
    for h in handles { h.await.unwrap(); }
}
```

---

## 19. Comparative Analysis

### Performance Characteristics

| Primitive       | Uncontended Acquire | Contended Acquire   | Memory     | Fairness     | Appropriate Context         |
|-----------------|---------------------|---------------------|------------|--------------|------------------------------|
| TAS Spinlock    | ~10ns (CAS)         | O(N²) cache traffic | 4 bytes    | None         | Very short critical sections |
| Ticket Spinlock | ~20ns (FAA+load)    | O(N) cache traffic  | 8 bytes    | FIFO         | Short, fairness needed       |
| MCS Spinlock    | ~30ns               | O(1) cache traffic  | Per-thread | FIFO         | High-contention short locks  |
| Futex Mutex     | ~10ns (CAS)         | ~1-10µs (syscall)   | 4 bytes    | FIFO (often) | General purpose              |
| Semaphore       | ~15ns               | ~1-10µs             | 8+ bytes   | FIFO (often) | Resource counting, signaling |
| RwLock          | ~20ns (read)        | ~1-10µs (write)     | 8 bytes    | Writer pref. | Read-heavy data structures   |
| Seqlock         | ~2ns (read)         | ~2ns (always retry) | 4 bytes    | Writers only | Read-heavy, retry-safe reads |
| RCU             | ~1ns (read, x86)    | synchronize_rcu     | Per-copy   | —            | Read-dominated kernel data   |
| Channel (Go)    | ~100ns              | ~200ns              | 96+ bytes  | FIFO         | Goroutine coordination       |

### Semantic Differences Matrix

| Property              | Spinlock | Mutex  | Semaphore     | Monitor       |
|-----------------------|----------|--------|---------------|---------------|
| Sleeping on contend   | No       | Yes    | Yes           | Yes           |
| Ownership             | Yes      | Yes    | No            | Yes           |
| Recursion             | No       | Config | N/A           | Yes (Hoare)   |
| Counting              | No       | No     | Yes           | Via CV loop   |
| Condition waiting     | No       | No     | No            | Yes (CV)      |
| IRQ safe              | Yes      | No     | No            | No            |
| Priority inheritance  | No       | Yes    | Rare          | Via mutex     |
| Implementation cost   | Trivial  | Medium | Medium        | High          |

### When To Use What: Decision Tree

```
Do you need to protect a critical section?
├── Is the critical section < 1µs AND you have multiple CPUs?
│   └── Spinlock (ticket or MCS for fairness)
│       └── In kernel interrupt handler? → spin_lock_irq
└── Is the critical section > 1µs OR can it sleep?
    ├── Simple mutual exclusion?
    │   └── Mutex / sync.Mutex / Mutex<T>
    ├── Read-heavy access pattern?
    │   ├── Very short reads, infrequent writes → Seqlock (Linux kernel)
    │   └── Longer reads → RwLock
    ├── Need to wait for a condition (not just lock)?
    │   └── Monitor (Mutex + Condvar)
    ├── Counting resources (pool of N)?
    │   └── Semaphore
    ├── Signal between threads (producer signals consumer)?
    │   ├── One-time? → sync.Once / OnceLock / completion
    │   └── Repeated? → Semaphore OR Channel (Go)
    └── Extremely read-heavy, lockless reads required?
        └── RCU (Linux kernel) / epoch-based (crossbeam)
```

---

## 20. Expert Mental Models and Heuristics

### Mental Model 1: The Lock as a Protocol, Not a Guard

Beginners think of locks as "protecting data." Experts think of locks as **enforcing a protocol** — ensuring that a set of operations appear atomic to all observers. This distinction matters because:

- The lock itself doesn't protect anything unless every access goes through it.
- The protocol is the set of invariants maintained by the lock: "When no thread holds this lock, `count` equals the sum of all items in `queue`."

**Exercise**: Before writing any lock, write the invariant it protects. If you can't state it, you don't understand what you're locking.

### Mental Model 2: The ABA Problem is About Identity, Not Value

When using CAS for lock-free algorithms, the issue is not just that the value matches — it's that **the value at an address can be the same for different logical states**. A pointer being the same address doesn't mean it's the same object.

This is why:
- x86 ABA is prevented by DCAS (double-width CAS) with a version counter.
- ARM LL/SC inherently prevents it (the exclusive monitor tracks the address state).
- Rust's epoch-based reclamation prevents it by ensuring freed memory is not reused while any reader could see it.

### Mental Model 3: The Memory Barrier is a Contract

A `Release` store says: "Everything I did before this point is now visible to whoever does an `Acquire` load of this address."
An `Acquire` load says: "I will not see any stores from the releasing thread happen after the Release."

This is the **happens-before** relationship. Drawing happens-before graphs is the most reliable way to reason about concurrent code correctness.

### Mental Model 4: Contention is the Enemy, Not the Lock

An uncontended lock is nearly free (10-30ns). The cost comes from **contention** — multiple threads competing for the same lock simultaneously. Therefore:

- **Reduce critical section size**: Hold locks for the minimum time necessary.
- **Reduce lock scope**: Use multiple fine-grained locks instead of one coarse lock.
- **Reduce sharing**: Per-CPU/per-thread data eliminates contention entirely.
- **Use the right algorithm**: Read-heavy? Use RwLock. Update-rarely? Use RCU. Batch updates? Use fine-grained locking with merge.

### Mental Model 5: The Four Dangerous Patterns

1. **Lock inversion** (A→B in thread 1, B→A in thread 2): Always audit lock acquisition order.
2. **Lock in callback** (holding a lock while calling a user-provided callback): The callback may acquire the same lock.
3. **Lock with I/O** (holding a spinlock while doing I/O): I/O can sleep, spinning cannot.
4. **Forgetting to unlock on error path**: Use RAII (Rust guards, Go defer, C++ unique_lock) — never manually unlock.

### Mental Model 6: Amdahl's Law Applied to Locking

If 10% of your code is in a serialized critical section, **maximum theoretical speedup from parallelism is 10x**, regardless of how many CPUs you have. Locking makes your serial fraction larger. Reducing the serial fraction (shortening critical sections, fine-grained locking, lock-free algorithms) is the fundamental work of concurrent programming.

### Cognitive Principle: Chunking Lock Patterns

Expert concurrency programmers have a library of **chunked patterns** they recognize instantly:

- RAII acquisition → cleanup guaranteed
- CV wait in while loop → Mesa semantics
- Lock ordering by address/ID → ABBA prevention
- FAA + load in loop → ticket lock
- Publish via atomic store, consume via atomic load → producer-consumer without locks
- CAS loop with exponential backoff → lock-free retry
- RCU read-side with rcu_dereference → zero-cost concurrent read

Build this vocabulary through deliberate practice: implement each primitive from scratch, then study its production implementation (glibc, Go runtime source, parking_lot crate).

### Heuristic: The Cache Line is the Unit of Contention

Every hot-path synchronization decision should be made with the 64-byte cache line in mind:

1. **One atomic variable per cache line** for frequently contended data.
2. **Align thread-local data** to prevent false sharing.
3. **MCS/CLH locks** are specifically designed to avoid sharing cache lines between waiters.
4. **Per-CPU counters** (Linux `percpu`, Go `expvar`, Rust `thread_local!`) eliminate cache line sharing entirely for counters.

### The Monk's Approach to Concurrency: Progressive Depth

Start with correctness (mutex everywhere, coarse-grained), verify with tools (race detector, TSAN, lockdep), then optimize using profiling data (perf, pprof). Only reach for spinlocks, RCU, and lock-free when profiling proves the mutex is the bottleneck. The most dangerous code is premature lock-free optimization — it trades correctness for speculative performance.

---

*This guide reflects the state of Linux 6.x kernel synchronization, C11/C17 memory model, Go 1.22 runtime, and Rust 2021 edition. The fundamental invariants — acquire/release ordering, the four Coffman conditions, the ABA problem — are timeless.*

---
**References (for further depth):**
- *The Linux Kernel source* — `kernel/locking/` directory (spinlock, mutex, rwsem, futex, rtmutex implementations)
- *Is Parallel Programming Hard?* — Paul E. McKenney (RCU bible, free PDF)
- *The Art of Multiprocessor Programming* — Herlihy & Shavit (lock-free theory)
- *Linux Device Drivers* — Corbet, Rubini, Kroah-Hartman (kernel sync in practice)
- *Go runtime source* — `src/sync/mutex.go`, `src/runtime/lock_futex.go`
- *parking_lot source* — Amanieu d'Antras (state-of-the-art Rust synchronization)
- *Futex Are Tricky* — Ulrich Drepper (2011) — the canonical futex reference

Now I'll build this — a full, kernel-depth reference document. This will take a moment.Here's your complete guide. Here's a high-level map of what's inside, so you can navigate with intent:

**Layers of depth, in order:**

1. **Hardware foundations** — MESI cache coherency, TAS/CAS/FAA/LL-SC atomic instructions, x86 vs ARM memory models, why `PAUSE`/`YIELD` exist inside spin loops.

2. **Spinlock evolution** — TAS → Ticket Lock (FIFO, O(N) bouncing) → MCS Lock (O(1) cache traffic, each waiter spins on its own node). This is the progression every kernel engineer must internalize.

3. **Mutex internals** — the three-state futex state machine (`0/1/2`), optimistic spinning (midpath), and how `FUTEX_REQUEUE` prevents thundering herd in `pthread_cond_broadcast`.

4. **Semaphore vs Mutex** — the ownership distinction is the crux. Semaphores are for *signaling and resource counting*, mutexes are for *mutual exclusion with identity*. Most bugs in this space come from confusing the two.

5. **Monitor** — Hoare vs Mesa semantics, and why `while (!condition)` is non-negotiable (spurious wakeups + Mesa = always loop).

6. **Deadlock/Livelock/Starvation** — Coffman conditions, RAG cycle detection, lockdep internals, priority inversion (the Pathfinder bug explained fully), banker's algorithm.

7. **RCU** — the most important synchronization mechanism in the Linux kernel. Grace periods, quiescent states, `rcu_dereference`/`rcu_assign_pointer` with memory barriers.

8. **C/Go/Rust implementations** — each covering the full spectrum from spinlock to monitor to lock-free, with correct memory orderings throughout.

The section on **Mental Model 1** (lock as protocol, not guard) is worth reading three times — it separates engineers who write correct concurrent code from those who get lucky.