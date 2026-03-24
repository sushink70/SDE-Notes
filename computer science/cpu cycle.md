# The Complete Guide to Busy Waiting — Wasting CPU by Constantly Checking a Condition

> *"A thread that spins is a thread that burns — CPU cycles consumed, progress zero."*

---

## Table of Contents

1. [What is Busy Waiting?](#1-what-is-busy-waiting)
2. [The CPU and Scheduling — Mental Model](#2-the-cpu-and-scheduling--mental-model)
3. [The Anatomy of Wasted CPU Cycles](#3-the-anatomy-of-wasted-cpu-cycles)
4. [Forms of Busy Waiting](#4-forms-of-busy-waiting)
5. [Polling vs Interrupts — The Core Contrast](#5-polling-vs-interrupts--the-core-contrast)
6. [Spin Locks — The Canonical Busy Wait Primitive](#6-spin-locks--the-canonical-busy-wait-primitive)
7. [Busy Waiting in Real Code — Rust, Go, C](#7-busy-waiting-in-real-code--rust-go-c)
8. [The Problems It Causes (Deep Dive)](#8-the-problems-it-causes-deep-dive)
9. [Solutions: Blocking Synchronization Primitives](#9-solutions-blocking-synchronization-primitives)
10. [Condition Variables — The Elegant Fix](#10-condition-variables--the-elegant-fix)
11. [Semaphores](#11-semaphores)
12. [Channels (Go Philosophy)](#12-channels-go-philosophy)
13. [When Busy Waiting IS Acceptable](#13-when-busy-waiting-is-acceptable)
14. [Hybrid Approach: Spin Then Block](#14-hybrid-approach-spin-then-block)
15. [Memory Ordering and Atomics](#15-memory-ordering-and-atomics)
16. [OS-Level Concepts: Context Switch, Scheduler, Run Queue](#16-os-level-concepts-context-switch-scheduler-run-queue)
17. [Benchmarking & Profiling Busy Waits](#17-benchmarking--profiling-busy-waits)
18. [Decision Tree: What to Use When](#18-decision-tree-what-to-use-when)
19. [Summary of Mental Models](#19-summary-of-mental-models)

---

## 1. What is Busy Waiting?

### Definition

**Busy waiting** (also called **spinning**, **spin-waiting**, or **active waiting**) is a technique where a thread or process **repeatedly checks** whether a condition is true, doing nothing productive in the meantime, consuming CPU cycles purely for the check itself.

The thread is "busy" (it is on the CPU, running instructions) but it is "waiting" (it is not making forward progress on actual work).

### The simplest possible example

```
WHILE condition_is_false:
    do_nothing  ← CPU keeps executing this loop
```

This is equivalent to a person standing at a door, checking every millisecond whether the door is unlocked, instead of sitting down and waiting to be notified.

### Vocabulary you must know

| Term | Meaning |
|------|---------|
| **Thread** | A unit of execution inside a process. Multiple threads share the same memory. |
| **Process** | An independent program instance, has its own memory. |
| **CPU core** | A physical computation unit. On a quad-core machine, 4 cores can truly run simultaneously. |
| **Context switch** | The OS saves the state of one thread and loads another. Expensive (~1–10 µs). |
| **Scheduler** | The OS component that decides which thread runs on which CPU core and for how long. |
| **Blocking** | A thread voluntarily gives up the CPU and waits to be woken up. |
| **Spinning** | A thread keeps the CPU but loops checking a flag. |
| **Mutex** | Mutual Exclusion lock — ensures only one thread is in a critical section at a time. |
| **Critical Section** | A region of code that accesses shared data and must not be entered by more than one thread simultaneously. |
| **Atomic operation** | An operation that completes in a single, indivisible step — no other thread can see it "halfway done". |
| **Cache line** | The smallest unit of memory transferred between CPU and cache, typically 64 bytes. |

---

## 2. The CPU and Scheduling — Mental Model

To understand *why* busy waiting is wasteful, you must understand how the OS and CPU collaborate.

### The Time-Slice Model

```
TIME ──────────────────────────────────────────────────────►

Thread A:  [RUNS][RUNS][RUNS][RUNS][context switch]
Thread B:                               [RUNS][RUNS][RUNS][RUNS]
Thread C:  [WAITING FOR LOCK──────────────────────────────]
```

Each thread gets a **time slice** (quantum), typically 1–10 ms on Linux. The scheduler runs all runnable threads in round-robin (simplified). If a thread has nothing useful to do, ideally it should be **not runnable** — parked, sleeping, waiting.

### What happens during busy waiting

```
TIME ──────────────────────────────────────────────────────►

Thread A (has lock):  [RUNS: doing real work]
Thread B (spinning):  [CHECK][CHECK][CHECK][CHECK][CHECK][CHECK]
                       CPU is BURNED here    ^^^^^^^^^^^^^^^^^^^

Thread B is ON the CPU doing nothing productive.
Thread A might even be preempted by Thread B's spinning!
```

Thread B is consuming a full CPU core — no other thread can use that core while Thread B is in its spin loop (on a single-core machine). On a multi-core machine, it wastes one core.

---

## 3. The Anatomy of Wasted CPU Cycles

Let us look at what a busy-wait loop actually executes at the hardware level.

### The C loop

```c
// Thread B: waiting for flag to become 1
while (flag == 0) {
    // NOTHING
}
```

### What the CPU executes (pseudo-assembly)

```
spin_loop:
    MOV  rax, [flag_address]   ; Load flag from memory (or cache)
    CMP  rax, 0                ; Compare with 0
    JE   spin_loop             ; If equal (still 0), jump back
    ; ... proceed ...
```

Every iteration:
- A memory read (or cache access)
- A comparison
- A conditional branch

On a modern 3 GHz CPU, this loop can execute **~1 billion iterations per second**. All of them are useless. That is 1 billion wasted memory reads per second.

### Cache Line Thrashing

When two cores both access the same memory location repeatedly, they fight over the **cache line** containing that memory. This is called **false sharing** or **cache line ping-pong**.

```
ASCII: Cache Line Thrashing

Core 0 (Thread A): writes flag → [CACHE LINE INVALIDATED on Core 1]
Core 1 (Thread B): reads flag  → [CACHE MISS, must re-fetch from L3 or RAM]
Core 0 (Thread A): writes flag → [CACHE LINE INVALIDATED again]
Core 1 (Thread B): reads flag  → [CACHE MISS again]

This creates a "hot" cache line bouncing between cores.
Latency: ~40ns per bounce (L3 access) instead of ~1ns (L1 hit)
```

---

## 4. Forms of Busy Waiting

### 4.1 Pure Spin Loop (Worst)

```c
while (shared_flag == 0) { /* nothing */ }
```

Maximal CPU waste. No pause, no yield, no sleep.

### 4.2 Spin with CPU Hint (Better Spin)

```c
while (shared_flag == 0) {
    __asm__ volatile ("pause");  // x86 PAUSE instruction
}
```

The `PAUSE` instruction:
- Signals to the CPU that this is a spin loop
- Reduces power consumption slightly
- Improves performance on hyperthreaded CPUs by releasing pipeline pressure to the sibling hyperthread
- Adds ~140 clock cycles of delay — reduces memory bus contention

### 4.3 Spin with Yield

```c
while (shared_flag == 0) {
    sched_yield();  // Give up CPU time slice voluntarily
}
```

The thread tells the OS: "I don't have useful work right now, let someone else run." But it immediately comes back into the run queue — still wasteful if the wait is long.

### 4.4 Spin with Sleep (Exponential Backoff)

```c
int delay = 1; // microseconds
while (shared_flag == 0) {
    usleep(delay);
    delay = min(delay * 2, 1000); // cap at 1ms
}
```

Progressively backs off — trades latency for CPU savings. A pragmatic middle ground.

### 4.5 Polling (Event Loops)

```c
// Periodically check multiple conditions
while (running) {
    if (socket_ready())   handle_socket();
    if (timer_expired())  handle_timer();
    if (signal_received()) handle_signal();
    usleep(1000); // 1ms poll interval
}
```

Polling is a structured form of busy-wait used in event-driven systems. The `usleep` is critical — without it, this is pure busy waiting.

---

## 5. Polling vs Interrupts — The Core Contrast

This is the fundamental design choice in systems programming.

```
POLLING (Busy Wait Model):

Thread: "Is the data ready yet?"
Device: [no response, just has data when ready]
Thread: "Is the data ready yet?"
Thread: "Is the data ready yet?"
Thread: "Is the data ready yet?"
Device: [data arrives]
Thread: "Is the data ready yet?" ← NOW YES!
Thread: processes data

─────────────────────────────────────────────

INTERRUPT (Event-Driven Model):

Thread: [doing other work, or sleeping]
Device: [data arrives] → fires INTERRUPT signal
OS:     wakes up Thread, delivers data
Thread: processes data immediately
```

### Analogy

**Polling**: You repeatedly refresh your email inbox every second.
**Interrupt**: Your phone buzzes when a new email arrives.

### Comparison Table

| Property | Polling | Interrupt / Block |
|----------|---------|-------------------|
| CPU usage (idle) | HIGH (spins) | ZERO (thread sleeps) |
| Latency | Low (if polling fast) | Low-medium (wakeup overhead) |
| Implementation | Simple | More complex |
| Power consumption | High | Low |
| Scalability | Poor | Good |
| Best use case | Very short waits (<1µs) | Any wait > 1µs |

---

## 6. Spin Locks — The Canonical Busy Wait Primitive

### What is a Lock (Mutex)?

A **mutex** (mutual exclusion lock) ensures that only **one thread** can execute a **critical section** at a time.

```
Thread A: acquire_lock() → [critical section] → release_lock()
Thread B: acquire_lock() → WAITS until A releases → [critical section] → release_lock()
```

### What is a Spin Lock?

A **spin lock** is a mutex where the **waiting is done by busy-waiting** — the thread spins in a loop checking if the lock is available.

```
SPIN LOCK ACQUIRE LOGIC:

   ┌──────────────────────────────────────────┐
   │  Try to atomically set lock from 0 to 1  │
   │  (atomic compare-and-swap)               │
   └──────────────┬───────────────────────────┘
                  │
          ┌───────▼────────┐
          │ Was it 0?      │
          └──┬──────────┬──┘
          YES│          │NO
             ▼          ▼
          GOT LOCK!   SPIN: loop back
                      and try again

SPIN LOCK RELEASE LOGIC:

   ┌──────────────┐
   │ Set lock = 0 │  (atomic store)
   └──────────────┘
```

### The atomic compare-and-swap (CAS) operation

**CAS** is the hardware primitive underlying nearly all lock implementations.

```
CAS(memory_address, expected_value, new_value):
    ATOMICALLY:
        if *memory_address == expected_value:
            *memory_address = new_value
            return SUCCESS
        else:
            return FAILURE
```

"Atomically" means no other CPU can interrupt this operation mid-way. The hardware guarantees this using a special CPU instruction (`CMPXCHG` on x86, `ldxr/stxr` on ARM).

---

## 7. Busy Waiting in Real Code — Rust, Go, C

### 7.1 C — Pure Busy Wait (The Problem)

```c
// busy_wait_demo.c
// Compile: gcc -O2 -lpthread busy_wait_demo.c -o busy_wait_demo

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <stdatomic.h>

// PROBLEM: This is how NOT to do it
// volatile tells the compiler: this variable can change outside your knowledge.
// Without volatile, the compiler might optimize the loop away entirely!
// With C11 atomics, we use _Atomic instead.

_Atomic int flag = 0;   // shared flag between threads

void* producer(void* arg) {
    printf("[Producer] Working for 2 seconds...\n");
    sleep(2);  // simulate work
    printf("[Producer] Done! Setting flag.\n");
    atomic_store_explicit(&flag, 1, memory_order_release);
    return NULL;
}

void* consumer_busy_wait(void* arg) {
    printf("[Consumer] Busy-waiting on flag...\n");
    long long spins = 0;

    // BUSY WAIT: this loop burns 100% of one CPU core for 2 seconds
    while (atomic_load_explicit(&flag, memory_order_acquire) == 0) {
        spins++;
        // no sleep, no yield — pure spin
    }

    printf("[Consumer] Flag set! Spun %lld times — ALL WASTED.\n", spins);
    return NULL;
}

int main(void) {
    pthread_t t_producer, t_consumer;
    pthread_create(&t_producer, NULL, producer, NULL);
    pthread_create(&t_consumer, NULL, consumer_busy_wait, NULL);
    pthread_join(t_producer, NULL);
    pthread_join(t_consumer, NULL);
    return 0;
}
```

**Expected output:**
```
[Producer] Working for 2 seconds...
[Consumer] Busy-waiting on flag...
[Producer] Done! Setting flag.
[Consumer] Flag set! Spun 2,000,000,000+ times — ALL WASTED.
```

Two billion wasted iterations in 2 seconds. Each iteration consumed real electricity.

---

### 7.2 C — Spin Lock Implementation from Scratch

```c
// spinlock.c
// Compile: gcc -O2 -lpthread spinlock.c -o spinlock

#include <stdio.h>
#include <stdatomic.h>
#include <pthread.h>
#include <unistd.h>

// ─── SPIN LOCK DEFINITION ───────────────────────────────────────────────────

typedef struct {
    _Atomic int locked;  // 0 = free, 1 = held
} spinlock_t;

// Initialize a spinlock to unlocked state
void spinlock_init(spinlock_t* lock) {
    atomic_store_explicit(&lock->locked, 0, memory_order_relaxed);
}

// Acquire: spin until we get the lock
// memory_order_acquire: no reads/writes AFTER this point can be reordered BEFORE it
void spinlock_acquire(spinlock_t* lock) {
    int expected;
    while (1) {
        expected = 0;
        // Try to swap: if locked==0, set it to 1 and return SUCCESS
        if (atomic_compare_exchange_weak_explicit(
                &lock->locked,
                &expected,          // expected value (0 = free)
                1,                  // desired new value (1 = held)
                memory_order_acquire,
                memory_order_relaxed)) {
            // SUCCESS: we got the lock
            return;
        }
        // FAILURE: lock was already 1 (held by someone else)
        // SPIN: add x86 PAUSE hint to reduce power + improve hyperthreading
        // On non-x86, this compiles away (no-op) — still correct, just less optimal
        #if defined(__x86_64__) || defined(__i386__)
            __asm__ volatile ("pause" ::: "memory");
        #endif
    }
}

// Release: set to 0 atomically
// memory_order_release: no reads/writes BEFORE this point can be reordered AFTER it
void spinlock_release(spinlock_t* lock) {
    atomic_store_explicit(&lock->locked, 0, memory_order_release);
}

// ─── USAGE EXAMPLE ──────────────────────────────────────────────────────────

spinlock_t my_lock;
int shared_counter = 0;

void* increment_worker(void* arg) {
    int thread_id = *(int*)arg;
    for (int i = 0; i < 100000; i++) {
        spinlock_acquire(&my_lock);
        shared_counter++;  // critical section: only ONE thread here at a time
        spinlock_release(&my_lock);
    }
    printf("[Thread %d] Done.\n", thread_id);
    return NULL;
}

int main(void) {
    spinlock_init(&my_lock);

    pthread_t threads[4];
    int ids[4] = {0, 1, 2, 3};

    for (int i = 0; i < 4; i++) {
        pthread_create(&threads[i], NULL, increment_worker, &ids[i]);
    }
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }

    // Should be exactly 400,000 if no race conditions
    printf("Final counter: %d (expected: 400000)\n", shared_counter);
    return 0;
}
```

### Memory Ordering Explained (C)

```
MEMORY ORDER — WHAT IT MEANS:

acquire:   ─────────────────── FENCE ──────────────────────
           All operations AFTER this line                   │
           will NOT be reordered to BEFORE this line.       │
           Sees all writes from the thread that did release.│

release:   All operations BEFORE this line                  │
           will NOT be reordered to AFTER this line.        │
─────────────────────── FENCE ──────────────────────────────

relaxed:   No ordering guarantees. Just atomicity.
           Use only when you don't care about ordering.

WHY THIS MATTERS:
Thread A writes data, then sets flag=1 (release)
Thread B reads flag==1 (acquire), then reads data
→ Thread B is GUARANTEED to see Thread A's data writes.
Without proper ordering, Thread B might see stale data
even after seeing flag==1.
```

---

### 7.3 Rust — Busy Wait (Atomic Spin)

```rust
// busy_wait_rust.rs
// cargo build --release

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn main() {
    // Arc = Atomically Reference Counted — shared ownership across threads
    // AtomicBool = a boolean that can be safely read/written from multiple threads
    let flag = Arc::new(AtomicBool::new(false));

    let flag_producer = Arc::clone(&flag);
    let flag_consumer = Arc::clone(&flag);

    // ── Producer Thread ──────────────────────────────────────────────────────
    let producer = thread::spawn(move || {
        println!("[Producer] Doing work for 1 second...");
        thread::sleep(Duration::from_secs(1));
        println!("[Producer] Work done. Setting flag.");

        // Ordering::Release: ensures all writes before this store
        // are visible to any thread that later loads with Acquire
        flag_producer.store(true, Ordering::Release);
    });

    // ── Consumer: BUSY WAIT (BAD) ────────────────────────────────────────────
    let consumer = thread::spawn(move || {
        println!("[Consumer] Busy-waiting...");
        let mut spin_count: u64 = 0;

        // PROBLEM: burns 100% of one CPU core
        // Ordering::Acquire: we see all writes from the producer's Release
        while !flag_consumer.load(Ordering::Acquire) {
            spin_count += 1;

            // std::hint::spin_loop() emits the x86 PAUSE instruction
            // (or equivalent on ARM: YIELD instruction)
            // Still busy-waiting, but slightly more power-efficient
            std::hint::spin_loop();
        }

        println!(
            "[Consumer] Flag seen! Wasted {} spin iterations.",
            spin_count
        );
    });

    producer.join().unwrap();
    consumer.join().unwrap();
}
```

### 7.4 Rust — Spin Lock from Scratch

```rust
// spinlock_rust.rs

use std::cell::UnsafeCell;
use std::ops::{Deref, DerefMut};
use std::sync::atomic::{AtomicBool, Ordering};

// ─── SPIN LOCK DEFINITION ────────────────────────────────────────────────────

pub struct SpinLock<T> {
    locked: AtomicBool,
    // UnsafeCell: tells Rust "I am managing the interior mutability myself"
    // Rust's ownership model normally prevents shared mutation.
    // UnsafeCell is the escape hatch — we use it carefully with our lock.
    data: UnsafeCell<T>,
}

// SAFETY: SpinLock is safe to send between threads (Send)
// and safe to share references to across threads (Sync)
// because we guarantee exclusive access via our atomic lock.
unsafe impl<T: Send> Send for SpinLock<T> {}
unsafe impl<T: Send> Sync for SpinLock<T> {}

// ─── GUARD: holds the lock, releases on drop ─────────────────────────────────
// This is the RAII pattern: "Resource Acquisition Is Initialization"
// When the guard is dropped (goes out of scope), the lock is automatically released.

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

    pub fn lock(&self) -> SpinLockGuard<T> {
        // Spin until we can set locked from false to true
        loop {
            // compare_exchange: if locked==false, set to true and return Ok
            //                   if locked==true,  return Err (someone else holds it)
            // Acquire: we see all writes from the previous lock holder's Release
            // Relaxed: on failure, no ordering needed (we're just spinning)
            if self
                .locked
                .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_ok()
            {
                // We got the lock!
                return SpinLockGuard { lock: self };
            }

            // Spin hint: lets the CPU know we're in a spin loop
            std::hint::spin_loop();
        }
    }
}

// Deref: guard.deref() gives &T — immutable access to protected data
impl<T> Deref for SpinLockGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: we hold the lock, so exclusive access is guaranteed
        unsafe { &*self.lock.data.get() }
    }
}

// DerefMut: guard.deref_mut() gives &mut T — mutable access to protected data
impl<T> DerefMut for SpinLockGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        // SAFETY: we hold the lock, so no other thread has access
        unsafe { &mut *self.lock.data.get() }
    }
}

// Drop: automatically release lock when guard goes out of scope
impl<T> Drop for SpinLockGuard<'_, T> {
    fn drop(&mut self) {
        // Release: all our writes are visible to the next lock acquirer
        self.lock.locked.store(false, Ordering::Release);
    }
}

// ─── USAGE ───────────────────────────────────────────────────────────────────

use std::sync::Arc;
use std::thread;

fn main() {
    let counter = Arc::new(SpinLock::new(0u64));
    let mut handles = vec![];

    for thread_id in 0..4 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100_000 {
                // Lock acquired here. Guard returned.
                let mut guard = counter_clone.lock();
                *guard += 1;
                // Guard dropped here → lock released AUTOMATICALLY
            }
            println!("Thread {} done", thread_id);
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let final_count = counter.lock();
    println!("Final count: {} (expected: 400000)", *final_count);
}
```

---

### 7.5 Go — Busy Wait (The Problem)

```go
// busywait.go
// go run busywait.go

package main

import (
    "fmt"
    "runtime"
    "sync/atomic"
    "time"
)

func main() {
    var flag int32 = 0 // shared atomic flag

    // Producer goroutine
    go func() {
        fmt.Println("[Producer] Working for 1 second...")
        time.Sleep(1 * time.Second)
        fmt.Println("[Producer] Done! Setting flag.")
        atomic.StoreInt32(&flag, 1) // atomic write
    }()

    // Consumer: BUSY WAIT (BAD)
    fmt.Println("[Consumer] Busy-waiting...")
    spinCount := int64(0)

    // Burns 100% of a CPU core (one goroutine scheduler thread / P)
    for atomic.LoadInt32(&flag) == 0 {
        spinCount++

        // runtime.Gosched(): yield to Go scheduler — slightly better than nothing
        // But still wasteful if the wait is long (keeps coming back immediately)
        // COMMENT THIS OUT to see true busy-wait behavior
        runtime.Gosched()
    }

    fmt.Printf("[Consumer] Flag seen after %d spins.\n", spinCount)
    time.Sleep(100 * time.Millisecond) // let producer goroutine finish printing
}
```

### 7.6 Go — Spin Lock (for educational purposes; use sync.Mutex in production)

```go
// spinlock_go.go
// go run spinlock_go.go

package main

import (
    "fmt"
    "runtime"
    "sync/atomic"
    "sync"
)

// ─── SPIN LOCK ───────────────────────────────────────────────────────────────

type SpinLock struct {
    state int32 // 0 = unlocked, 1 = locked
}

// Lock: spin until we acquire
func (sl *SpinLock) Lock() {
    for {
        // Try to swap 0 → 1 atomically
        // If state was 0 (unlocked), CompareAndSwapInt32 sets it to 1 and returns true
        // If state was 1 (locked),   CompareAndSwapInt32 does nothing and returns false
        if atomic.CompareAndSwapInt32(&sl.state, 0, 1) {
            return // Got the lock
        }
        // Spin: voluntarily yield so other goroutines can run
        // In Go, if you don't yield, you can starve other goroutines on the same OS thread
        runtime.Gosched()
    }
}

// Unlock: atomically set state back to 0
func (sl *SpinLock) Unlock() {
    atomic.StoreInt32(&sl.state, 0)
}

// ─── USAGE ───────────────────────────────────────────────────────────────────

func main() {
    var sl SpinLock
    var counter int64
    var wg sync.WaitGroup

    for i := 0; i < 4; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for j := 0; j < 100_000; j++ {
                sl.Lock()
                counter++ // critical section
                sl.Unlock()
            }
            fmt.Printf("Goroutine %d done\n", id)
        }(i)
    }

    wg.Wait()
    fmt.Printf("Final counter: %d (expected: 400000)\n", counter)
}
```

---

## 8. The Problems It Causes (Deep Dive)

### 8.1 CPU Starvation

```
SYSTEM: 4-core CPU, 8 threads needing to run

WITHOUT BUSY WAIT:
Core 0: [Thread A: real work][Thread C: real work][Thread E: real work]
Core 1: [Thread B: real work][Thread D: real work][Thread F: real work]
Core 2: [Thread G: real work][Thread A: real work][Thread B: real work]
Core 3: [Thread H: real work][Thread C: real work][Thread G: real work]
All threads make progress!

WITH BUSY WAIT (Thread E spinning):
Core 0: [Thread E: SPINNING][Thread E: SPINNING][Thread E: SPINNING]
Core 1: [Thread A: real work][Thread C: real work][Thread F: real work]
Core 2: [Thread B: real work][Thread D: real work][Thread G: real work]
Core 3: [Thread H: real work][Thread A: real work][Thread B: real work]
One core is WASTED. Thread E produces no value.
```

### 8.2 Priority Inversion

```
PRIORITY INVERSION SCENARIO:

Thread HIGH (priority 10): waiting for lock, spinning
Thread MED  (priority  5): runnable, doing other work
Thread LOW  (priority  1): holds the lock, doing slow work

Problem:
- Thread LOW holds the lock but is rarely scheduled (low priority)
- Thread HIGH is spinning (high priority) consuming the CPU
- Thread MED may run more than Thread LOW
- Thread LOW never gets scheduled → never releases lock → Thread HIGH spins forever

This is priority inversion: a LOW priority task indirectly blocks a HIGH priority task.
```

### 8.3 Power Consumption and Thermal Throttling

A spinning CPU core draws full power. On battery-powered devices this drains the battery. On servers this increases electricity bills and heat, which can cause **thermal throttling** — the CPU slows itself down to cool down.

```
POWER STATES:

C0 state (Active):   Core running at full clock, ~15-25W per core
C1 state (Halt):     Core stopped, waiting for interrupt, ~0.5W
C6 state (Deep Sleep): Core powered down, ~0.05W

Busy waiting PREVENTS the CPU from entering C1/C6 states.
Blocking allows the CPU to enter C1/C6.

A server with 32 cores all busy-waiting:
32 × 20W = 640W WASTED (minus what real work would cost).
```

### 8.4 Incorrect Results (if done naively without atomics)

```c
// DANGEROUS: non-atomic flag read
volatile int flag = 0;  // volatile alone is NOT enough for thread safety!

// Thread B reads this value
// Problem: the compiler or CPU might reorder memory operations
// Thread A might write to flag BEFORE writing to shared_data,
// but Thread B might see flag=1 before seeing the updated shared_data.

// CORRECT: use C11 atomic with proper memory ordering
_Atomic int flag = 0;
atomic_store_explicit(&flag, 1, memory_order_release);  // in producer
atomic_load_explicit(&flag, memory_order_acquire);       // in consumer
```

### 8.5 Livelock

A **livelock** is like a deadlock but the threads keep moving:

```
Thread A: "You go first!"  → backs off → tries again
Thread B: "No, you go!"   → backs off → tries again
...repeat forever...

Both threads are ACTIVE (not blocked), but neither makes progress.
This can happen with naive backoff strategies in spin locks.
```

---

## 9. Solutions: Blocking Synchronization Primitives

The fundamental solution: **make the waiting thread sleep** (block), and have the OS **wake it up** when the condition becomes true.

### The Blocking Model

```
BLOCKING SYNCHRONIZATION FLOW:

Thread B wants lock held by Thread A:

1. Thread B calls mutex_lock()
2. Lock is held → OS puts Thread B in "blocked" state
   Thread B is removed from the run queue
   ┌────────────────────────────────────────────────┐
   │  BLOCKED QUEUE:  [Thread B]                    │
   │  RUN QUEUE:      [Thread A, Thread C, ...]     │
   └────────────────────────────────────────────────┘
3. Thread A finishes, calls mutex_unlock()
4. OS moves Thread B from blocked queue → run queue
   Thread B wakes up with the lock held
5. Thread B executes critical section
6. Thread B calls mutex_unlock()

THREAD B CONSUMED ZERO CPU while waiting! ✓
```

### 9.1 C — POSIX Mutex (Blocking Mutex)

```c
// blocking_mutex.c
// Compile: gcc -O2 -lpthread blocking_mutex.c -o blocking_mutex

#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
int shared_counter = 0;

void* worker(void* arg) {
    int id = *(int*)arg;
    for (int i = 0; i < 100000; i++) {
        // pthread_mutex_lock:
        // - If lock is free: acquires it instantly, returns
        // - If lock is held: puts THIS THREAD to sleep (blocks)
        //   The OS wakes this thread when the lock is released
        //   NO CPU WASTED during the wait!
        pthread_mutex_lock(&lock);

        shared_counter++;  // critical section

        // pthread_mutex_unlock:
        // - Releases the lock
        // - If any threads are sleeping waiting for this lock,
        //   the OS wakes one of them up
        pthread_mutex_unlock(&lock);
    }
    printf("[Thread %d] Done.\n", id);
    return NULL;
}

int main(void) {
    pthread_t threads[4];
    int ids[4] = {0, 1, 2, 3};

    for (int i = 0; i < 4; i++) {
        pthread_create(&threads[i], NULL, worker, &ids[i]);
    }
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Final counter: %d (expected: 400000)\n", shared_counter);
    pthread_mutex_destroy(&lock);
    return 0;
}
```

---

## 10. Condition Variables — The Elegant Fix

A **condition variable** is a synchronization primitive that allows a thread to **sleep** until a specific condition becomes true, and be **woken up** by another thread when it does.

### What is a Condition Variable?

Think of it as a "waiting room" with a "notification bell":
- Threads enter the waiting room (sleep on the condition variable)
- Another thread rings the bell (signals the condition variable)
- Sleeping threads wake up and check if the condition they need is now true

### Why is a Mutex needed alongside a Condition Variable?

```
SPURIOUS WAKEUPS & THE LOST WAKEUP PROBLEM:

Without a mutex:
Thread B: checks condition → false
[CONTEXT SWITCH to Thread A]
Thread A: makes condition true → signals condvar → no one is waiting yet!
[CONTEXT SWITCH back to Thread B]
Thread B: goes to sleep → SLEEPS FOREVER (missed the signal!)

With a mutex:
Thread B: acquires mutex → checks condition → false → atomically releases mutex + sleeps
Thread A: acquires mutex → makes condition true → signals condvar → releases mutex
Thread B: wakes up → reacquires mutex → checks condition → true → proceeds

The mutex ensures: checking the condition and going to sleep is ATOMIC.
No signals can be lost.
```

### 10.1 C — Condition Variable

```c
// condvar.c
// Compile: gcc -O2 -lpthread condvar.c -o condvar

#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <stdbool.h>

// The triad: mutex + condition variable + shared state
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t  cond  = PTHREAD_COND_INITIALIZER;
bool data_ready = false;   // The actual condition we're waiting for
int  shared_data = 0;

void* producer(void* arg) {
    printf("[Producer] Producing data...\n");
    sleep(2);

    // STEP 1: Lock the mutex (protects the shared state)
    pthread_mutex_lock(&mutex);

    // STEP 2: Modify shared state
    shared_data = 42;
    data_ready = true;
    printf("[Producer] Data ready: %d\n", shared_data);

    // STEP 3: Signal the condition variable — wake up one waiting thread
    // pthread_cond_broadcast() would wake up ALL waiting threads
    pthread_cond_signal(&cond);

    // STEP 4: Unlock
    pthread_mutex_unlock(&mutex);

    return NULL;
}

void* consumer(void* arg) {
    printf("[Consumer] Waiting for data (SLEEPING, not spinning)...\n");

    // STEP 1: Lock the mutex
    pthread_mutex_lock(&mutex);

    // STEP 2: While the condition is not true, SLEEP
    // pthread_cond_wait:
    //   a) atomically RELEASES the mutex
    //   b) puts this thread to SLEEP (no CPU consumed!)
    //   c) when signaled, re-acquires the mutex and returns
    //
    // WHY "while" and not "if"?
    // SPURIOUS WAKEUPS: The OS can wake up a thread even without a signal.
    // Always check the condition in a loop!
    while (!data_ready) {
        pthread_cond_wait(&cond, &mutex);
    }

    // STEP 3: Condition is true, we have the mutex — process data
    printf("[Consumer] Got data: %d (consumed ZERO CPU while waiting!)\n", shared_data);

    // STEP 4: Unlock
    pthread_mutex_unlock(&mutex);

    return NULL;
}

int main(void) {
    pthread_t t_prod, t_cons;
    pthread_create(&t_cons, NULL, consumer, NULL);  // consumer starts first
    pthread_create(&t_prod, NULL, producer, NULL);
    pthread_join(t_prod, NULL);
    pthread_join(t_cons, NULL);

    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&cond);
    return 0;
}
```

### 10.2 Rust — Condvar

```rust
// condvar_rust.rs

use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::Duration;

fn main() {
    // Mutex wraps the shared data (data_ready flag + actual data)
    // Condvar is the notification mechanism
    // Both are wrapped in Arc for shared ownership across threads
    let pair = Arc::new((Mutex::new((false, 0i32)), Condvar::new()));
    //                               ^^^^^  ^^^^^
    //                               ready  data

    let pair_producer = Arc::clone(&pair);
    let pair_consumer = Arc::clone(&pair);

    // ── Producer ────────────────────────────────────────────────────────────
    let producer = thread::spawn(move || {
        println!("[Producer] Working...");
        thread::sleep(Duration::from_secs(1));

        let (mutex, condvar) = &*pair_producer;

        // Lock the mutex, modify shared state
        let mut state = mutex.lock().unwrap(); // MutexGuard returned
        state.0 = true;  // data_ready = true
        state.1 = 42;    // shared_data = 42
        println!("[Producer] Data = 42, signaling.");

        // Notify ONE waiting thread (use notify_all() to wake all)
        condvar.notify_one();
        // MutexGuard dropped here → mutex automatically released
    });

    // ── Consumer ────────────────────────────────────────────────────────────
    let consumer = thread::spawn(move || {
        println!("[Consumer] Waiting (sleeping, zero CPU)...");
        let (mutex, condvar) = &*pair_consumer;

        // Lock the mutex
        let mut state = mutex.lock().unwrap();

        // Wait WHILE the condition is false
        // condvar.wait(state):
        //   a) Releases the mutex atomically
        //   b) Puts thread to sleep
        //   c) On wakeup: reacquires mutex, returns new MutexGuard
        //
        // wait_while is idiomatic Rust — handles spurious wakeups automatically
        state = condvar
            .wait_while(state, |s| !s.0)  // sleep while data_ready is false
            .unwrap();

        println!(
            "[Consumer] Woke up! Data = {} (zero CPU burned waiting)",
            state.1
        );
    });

    producer.join().unwrap();
    consumer.join().unwrap();
}
```

### 10.3 Go — Channel (Go's Idiomatic Solution)

```go
// channel_go.go
// Channels are Go's primary way to communicate + synchronize. No busy waiting needed.

package main

import (
    "fmt"
    "time"
)

func main() {
    // A channel is a typed conduit for sending values between goroutines.
    // make(chan int) creates an UNBUFFERED channel (synchronous handshake).
    // make(chan int, 10) creates a BUFFERED channel (up to 10 items stored).
    dataChan := make(chan int)

    // ── Producer ────────────────────────────────────────────────────────────
    go func() {
        fmt.Println("[Producer] Working...")
        time.Sleep(1 * time.Second)
        fmt.Println("[Producer] Sending data.")

        // Send: blocks PRODUCER until consumer is ready to receive
        // (for unbuffered channel)
        // This is the SIGNAL: wakes up the consumer
        dataChan <- 42
    }()

    // ── Consumer ────────────────────────────────────────────────────────────
    fmt.Println("[Consumer] Waiting for data (goroutine is parked)...")

    // Receive: blocks CONSUMER (goroutine parked, no CPU used!) until producer sends
    // When producer sends, OS/Go runtime wakes THIS goroutine
    value := <-dataChan

    fmt.Printf("[Consumer] Got %d — consumed ZERO CPU while waiting!\n", value)
}
```

### Go — Select: Waiting on Multiple Conditions

```go
// select_go.go
// select is like a switch statement for channels — waits on multiple conditions

package main

import (
    "fmt"
    "time"
)

func main() {
    dataChan   := make(chan int)
    cancelChan := make(chan struct{})  // empty struct: used as signal, takes 0 bytes
    timeout    := time.After(3 * time.Second) // built-in: sends after duration

    // Producer
    go func() {
        time.Sleep(1 * time.Second)
        dataChan <- 99
    }()

    // Cancel (could be from user input, OS signal, etc.)
    go func() {
        time.Sleep(5 * time.Second) // won't fire before data
        close(cancelChan)
    }()

    // Wait on MULTIPLE conditions — first one ready wins
    // The goroutine is SLEEPING the entire time, consuming ZERO CPU
    select {
    case val := <-dataChan:
        fmt.Printf("Got data: %d\n", val)

    case <-cancelChan:
        fmt.Println("Cancelled!")

    case <-timeout:
        fmt.Println("Timed out!")
    }
}
```

---

## 11. Semaphores

A **semaphore** is a generalization of a mutex. Where a mutex allows exactly 1 thread in the critical section, a semaphore allows **N** threads.

### Mental Model

```
SEMAPHORE:

Imagine a parking lot with N=3 spaces.
- A car arrives → checks if space available → enters (count--)
- If lot full (count==0) → car WAITS (blocks, no busy spinning)
- A car leaves → count++ → waiting car is notified and enters

COUNT = 3: [SPACE][SPACE][SPACE]  ← 3 threads can enter
COUNT = 0: [FULL ][FULL ][FULL ]  ← next thread blocks

BINARY SEMAPHORE (count = 0 or 1) ≡ MUTEX
```

### C — Semaphore

```c
// semaphore.c
// Compile: gcc -O2 -lpthread semaphore.c -o semaphore

#include <stdio.h>
#include <semaphore.h>
#include <pthread.h>
#include <unistd.h>

// Producer-Consumer problem using a semaphore
// Producer produces items; consumer consumes them.
// Semaphore tracks: how many items are available.

sem_t items_available;  // semaphore: count of produced-but-not-consumed items
int buffer = -1;        // simplistic 1-item buffer

void* producer(void* arg) {
    for (int i = 0; i < 5; i++) {
        sleep(1); // simulate work
        buffer = i * 10;
        printf("[Producer] Produced: %d\n", buffer);

        // sem_post: increments semaphore count by 1
        // If any thread is blocked in sem_wait, it wakes it up
        // THIS IS THE SIGNAL — no busy waiting!
        sem_post(&items_available);
    }
    return NULL;
}

void* consumer(void* arg) {
    for (int i = 0; i < 5; i++) {
        // sem_wait: decrements semaphore count by 1
        // If count is 0: THIS THREAD SLEEPS (blocks) until count > 0
        // No busy waiting — OS handles the wakeup
        sem_wait(&items_available);

        printf("[Consumer] Consumed: %d\n", buffer);
    }
    return NULL;
}

int main(void) {
    // sem_init(sem, pshared, initial_value)
    // pshared=0: semaphore is between threads of same process
    // initial_value=0: nothing to consume yet
    sem_init(&items_available, 0, 0);

    pthread_t t_prod, t_cons;
    pthread_create(&t_cons, NULL, consumer, NULL);
    pthread_create(&t_prod, NULL, producer, NULL);
    pthread_join(t_prod, NULL);
    pthread_join(t_cons, NULL);

    sem_destroy(&items_available);
    return 0;
}
```

### Rust — Semaphore

```rust
// semaphore_rust.rs
// Rust's std doesn't have a semaphore, but we can build one with Condvar + Mutex

use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::Duration;

struct Semaphore {
    count: Mutex<usize>,
    condvar: Condvar,
}

impl Semaphore {
    fn new(initial: usize) -> Self {
        Semaphore {
            count: Mutex::new(initial),
            condvar: Condvar::new(),
        }
    }

    // "down" or "wait" or "acquire" — decrements; blocks if count == 0
    fn acquire(&self) {
        let mut count = self.count.lock().unwrap();
        // Wait while count is 0 (no resources available)
        count = self.condvar.wait_while(count, |c| *c == 0).unwrap();
        *count -= 1;
    }

    // "up" or "signal" or "release" — increments; wakes a waiting thread
    fn release(&self) {
        let mut count = self.count.lock().unwrap();
        *count += 1;
        self.condvar.notify_one(); // wake one waiting thread
    }
}

fn main() {
    // Allow max 2 concurrent workers in "critical section"
    let sem = Arc::new(Semaphore::new(2));
    let mut handles = vec![];

    for i in 0..6 {
        let sem = Arc::clone(&sem);
        let handle = thread::spawn(move || {
            println!("Thread {} waiting to enter...", i);
            sem.acquire();
            println!("Thread {} INSIDE (max 2 at a time)", i);
            thread::sleep(Duration::from_millis(500)); // simulate work
            println!("Thread {} leaving.", i);
            sem.release();
        });
        handles.push(handle);
    }

    for h in handles {
        h.join().unwrap();
    }
}
```

---

## 12. Channels (Go Philosophy)

Go's philosophy: **"Do not communicate by sharing memory; instead, share memory by communicating."**

This means: instead of having shared variables protected by mutexes (the C/Rust way), use channels to pass data between goroutines.

```
TRADITIONAL (C/Rust style):                GO STYLE:

Shared memory:                             Channels:
  ┌──────────┐                              ┌──────────┐
  │ shared   │                              │ Producer │
  │ data     │                              │ goroutine│
  └────┬─────┘                              └────┬─────┘
  Thread A ──lock──► read/write                  │ send(data)
  Thread B ──lock──► read/write             ─────▼──────
  Thread C ──lock──► read/write            │  channel   │
  [CONTENTION, BUSY WAIT RISK]              ─────┬──────
                                                 │ receive(data)
                                            ┌────▼─────┐
                                            │ Consumer │
                                            │ goroutine│
                                            └──────────┘
                                            [NO SHARED STATE, NO LOCKS]
```

```go
// pipeline_go.go
// Demonstrates a pipeline pattern — chains of goroutines connected by channels

package main

import "fmt"

// Stage 1: generate numbers 0..n-1
func generate(n int) <-chan int {
    out := make(chan int)
    go func() {
        for i := 0; i < n; i++ {
            out <- i  // send; goroutine sleeps if no receiver ready
        }
        close(out) // signal: no more data
    }()
    return out
}

// Stage 2: square each number
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for v := range in { // range: receive until channel is closed
            out <- v * v
        }
        close(out)
    }()
    return out
}

// Stage 3: add 1 to each number
func addOne(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for v := range in {
            out <- v + 1
        }
        close(out)
    }()
    return out
}

func main() {
    // Chain pipeline: generate → square → addOne → print
    // Each goroutine is SLEEPING when its partner is not ready.
    // Zero busy waiting. Zero wasted CPU.

    nums    := generate(5)      // 0, 1, 2, 3, 4
    squared := square(nums)     // 0, 1, 4, 9, 16
    result  := addOne(squared)  // 1, 2, 5, 10, 17

    for v := range result {
        fmt.Println(v)
    }
}
```

---

## 13. When Busy Waiting IS Acceptable

This is crucial knowledge for top-tier performance engineering. Busy waiting is NOT always bad.

### Rule of Thumb

```
Wait duration vs Context Switch Cost:

  Context switch cost: ~1,000–10,000 ns (1–10 µs)

  If expected wait < context switch cost:  SPIN (busy wait)
  If expected wait > context switch cost:  BLOCK (sleep)

  Why?
  Blocking → sleep → wakeup = 2 context switches = ~2–20 µs overhead
  If the lock will be released in 500 ns, spinning is FASTER than sleeping!
```

### Valid Use Cases for Busy Waiting / Spin Locks

| Scenario | Why Spinning is OK |
|----------|-------------------|
| OS kernel spinlocks | Can't sleep inside an interrupt handler; waits are < 1µs |
| Real-time systems | Predictable timing required; blocking has variable latency |
| Lock-free data structures | Short wait between CAS attempts |
| High-frequency trading | Every nanosecond counts; lock acquire must be deterministic |
| Multi-producer single-consumer queues | Wait times can be sub-microsecond |
| Polling hardware registers (embedded) | Device registers change in nanoseconds |

### 13.1 Rust — Spin Loop Hint (Polite Spinning)

```rust
// polite_spin.rs

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn main() {
    let done = Arc::new(AtomicBool::new(false));
    let done2 = Arc::clone(&done);

    thread::spawn(move || {
        // Simulate very short work (300 ns realistic in production)
        thread::sleep(Duration::from_micros(1)); // 1µs to demo
        done2.store(true, Ordering::Release);
    });

    // For very short waits (< a few µs), spinning with hint is faster than blocking
    while !done.load(Ordering::Acquire) {
        // std::hint::spin_loop() does:
        // - x86:   `PAUSE` instruction (reduces power, tells CPU it's a spin loop)
        // - ARM64: `YIELD` instruction
        // - WASM:  nothing (compiles to no-op)
        std::hint::spin_loop();
    }

    println!("Done!");
}
```

---

## 14. Hybrid Approach: Spin Then Block

The best production spinlocks (like Linux's `futex`-based mutex) use a **hybrid strategy**: spin for a short time, then block if the lock is still held.

```
HYBRID SPIN-THEN-BLOCK:

   START
     │
     ▼
 ┌──────────────────────────────────────┐
 │  PHASE 1: SPIN (for N iterations)    │
 │                                      │
 │  loop:                               │
 │    if lock_free? → acquire → DONE    │
 │    if spun N times? → exit loop      │
 │    else: spin_hint(); continue       │
 └───────────────┬──────────────────────┘
                 │ (N iterations elapsed, lock still held)
                 ▼
 ┌──────────────────────────────────────┐
 │  PHASE 2: BLOCK                      │
 │                                      │
 │  call OS → put thread to sleep       │
 │  OS wakes thread when lock released  │
 └──────────────────────────────────────┘

The right N value is typically: 40–100 spin attempts (tunable).
```

### C — Hybrid Mutex

```c
// hybrid_mutex.c
// Compile: gcc -O2 -lpthread hybrid_mutex.c -o hybrid_mutex

#include <stdio.h>
#include <stdatomic.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_SPIN_ITERATIONS 100

typedef struct {
    _Atomic int    spinlock;   // fast-path: spin on this
    pthread_mutex_t fallback;  // slow-path: OS blocking mutex
} hybrid_mutex_t;

void hybrid_mutex_init(hybrid_mutex_t* m) {
    atomic_store(&m->spinlock, 0);
    pthread_mutex_init(&m->fallback, NULL);
}

void hybrid_mutex_lock(hybrid_mutex_t* m) {
    // PHASE 1: Try to spin-acquire for MAX_SPIN_ITERATIONS
    for (int i = 0; i < MAX_SPIN_ITERATIONS; i++) {
        int expected = 0;
        if (atomic_compare_exchange_weak_explicit(
                &m->spinlock, &expected, 1,
                memory_order_acquire, memory_order_relaxed)) {
            return;  // Got the lock in spin phase!
        }
        #if defined(__x86_64__) || defined(__i386__)
            __asm__ volatile ("pause" ::: "memory");
        #endif
    }

    // PHASE 2: Spin failed — fall back to blocking OS mutex
    pthread_mutex_lock(&m->fallback);
    // Store 1 in spinlock to indicate we hold the lock via fallback path
    atomic_store_explicit(&m->spinlock, 1, memory_order_relaxed);
    // Note: in a full impl, we'd use the fallback's state to manage this
}

void hybrid_mutex_unlock(hybrid_mutex_t* m) {
    atomic_store_explicit(&m->spinlock, 0, memory_order_release);
    // Try to unlock fallback (no-op if we acquired via spin)
    // In a production impl, track which path was used
    pthread_mutex_unlock(&m->fallback);
}

void hybrid_mutex_destroy(hybrid_mutex_t* m) {
    pthread_mutex_destroy(&m->fallback);
}
```

### 14.1 Linux Futex (The Real Hybrid)

Linux's **futex** (Fast Userspace muTEX) is the mechanism underlying almost all modern blocking mutexes on Linux:

```
FUTEX CONCEPT:

State A (no contention):
  Lock/unlock happens in USERSPACE via atomics.
  ZERO kernel calls, ZERO system calls.
  Extremely fast.

State B (contention):
  When a thread must wait, it calls futex_wait() → kernel syscall
  Thread is put to sleep by the kernel.
  When lock is released, futex_wake() → kernel syscall
  Waiting threads are woken.

Best of both worlds:
- Fast path (no contention): ~5ns (userspace CAS)
- Slow path (contention): ~1–10µs (kernel context switch)
```

---

## 15. Memory Ordering and Atomics

Understanding why we need atomic operations and memory ordering is essential.

### The Problem: Compiler and CPU Reordering

```
YOUR CODE:            WHAT CPU/COMPILER MIGHT DO:

data = 42;           data = 42;      ← same
flag = 1;            flag = 1;       ← same (single-threaded: safe)

BUT with multiple threads:

Thread A:            Thread B reads:
  data = 42;           if flag == 1:
  flag = 1;              use(data)   ← might see data = 0!

Why?
1. Compiler may reorder flag = 1 BEFORE data = 42 (legal for single-threaded code)
2. CPU's store buffer may flush flag=1 to cache before flushing data=42
3. Thread B's CPU may have data=0 in its cache while flag=1 is already in its cache
```

### Memory Barriers

A **memory barrier** (or fence) prevents the CPU and compiler from reordering operations across it.

```
Thread A:
  STORE data = 42
  ─────── RELEASE BARRIER ───────  ← nothing BEFORE this can cross BELOW
  STORE flag = 1

Thread B:
  LOAD flag              ← must see 1 before proceeding
  ─────── ACQUIRE BARRIER ───────  ← nothing AFTER this can cross ABOVE
  LOAD data              ← guaranteed to see 42
```

### 15.1 Rust Memory Ordering Summary

```rust
use std::sync::atomic::Ordering;

// Ordering::Relaxed
// - No ordering guarantees beyond atomicity
// - Use for: pure counters, statistics, flags you don't read after
let counter = AtomicU64::new(0);
counter.fetch_add(1, Ordering::Relaxed); // fine for non-synchronized counters

// Ordering::Acquire (for loads / reads)
// - All operations AFTER this load cannot be reordered BEFORE it
// - Pairs with Release
// - Use when: reading a flag that, when true, means data is ready

// Ordering::Release (for stores / writes)
// - All operations BEFORE this store cannot be reordered AFTER it
// - Pairs with Acquire
// - Use when: writing a flag that signals data is ready

// Ordering::AcqRel (for read-modify-write: fetch_add, compare_exchange)
// - Both Acquire and Release in one operation
// - Use for: updating a value that other threads both read and write

// Ordering::SeqCst (Sequential Consistency)
// - Total global ordering visible to all threads
// - STRONGEST and MOST EXPENSIVE (involves full memory fence)
// - Use when: you need a single global order seen by all threads
// - Default when unsure (safe but potentially slow)
```

### 15.2 C Memory Ordering Summary

```c
#include <stdatomic.h>

// memory_order_relaxed: atomic, no ordering
// memory_order_acquire: load barrier
// memory_order_release: store barrier
// memory_order_acq_rel: both (for CAS, fetch_add)
// memory_order_seq_cst: full fence, strongest

// Safe producer-consumer pattern
// Producer:
atomic_store_explicit(&flag, 1, memory_order_release);

// Consumer:
while (atomic_load_explicit(&flag, memory_order_acquire) == 0) {
    __asm__ volatile ("pause");
}
// After this loop: all writes done before the release are visible here
```

---

## 16. OS-Level Concepts: Context Switch, Scheduler, Run Queue

### The Run Queue

```
OS SCHEDULER STRUCTURE:

RUN QUEUE (threads ready to run):
┌─────────────────────────────────────────────────────┐
│  [Thread A] [Thread B] [Thread C] [Thread F] ...    │
└─────────────────────────────────────────────────────┘
        ↑
    Scheduler picks next thread based on:
    - Priority (nice value, real-time priority)
    - Time since last run (fairness)
    - CPU affinity (which core it last ran on)

BLOCKED/SLEEP QUEUE (waiting for event):
┌─────────────────────────────────────────────────────┐
│  [Thread D: waiting for mutex lock]                 │
│  [Thread E: sleeping for 100ms]                     │
│  [Thread G: waiting for network I/O]                │
└─────────────────────────────────────────────────────┘
        ↑
    When event occurs, thread moves to RUN QUEUE
    THREADS HERE CONSUME ZERO CPU ← KEY INSIGHT
```

### What happens during a context switch

```
CONTEXT SWITCH: saving Thread A, loading Thread B

1. Timer interrupt fires (or Thread A calls sleep/block)
2. CPU enters kernel mode
3. Save Thread A's state:
   - All registers (rax, rbx, ..., rsp, rip — instruction pointer!)
   - Floating point registers (~256 bytes on x86-64)
   - CPU flags
   - TLS (Thread-Local Storage) pointer
4. Load Thread B's state (reverse of above)
5. Flush TLB if different process (EXPENSIVE for processes, cheap for same-process threads)
6. Return to userspace in Thread B

Cost: ~1,000–10,000 ns (depends on cache state, TLB, etc.)
This is why for sub-microsecond waits, spinning can be cheaper.
```

### System Call: The Interface

```
BUSY WAIT: no system calls
  Thread stays in userspace → NO kernel involvement → FAST transitions
  But: CPU fully consumed

BLOCKING: system calls required
  pthread_mutex_lock → futex_wait → kernel → thread parked
  futex_wake → kernel → thread unparked → returns to userspace
  Cost: ~1000 ns minimum per transition
  But: CPU freed for other work
```

---

## 17. Benchmarking & Profiling Busy Waits

### How to detect busy waiting in your programs

**Method 1: CPU usage observation**

```bash
# Linux: watch CPU per-thread
top -H    # shows all threads, press '1' for per-CPU
htop      # visual, per-core view

# A thread burning 100% of a core: visible as 100% on one CPU
# A blocking thread: shows 0% or near 0%
```

**Method 2: perf (Linux profiler)**

```bash
# Profile a running program
perf top -p <PID>

# Record and analyze
perf record ./my_program
perf report

# A busy-waiting thread will show up with a tight loop in the hottest functions
# Look for functions with 90%+ of samples in the call chain
```

**Method 3: strace (System Call Trace)**

```bash
# Busy-waiting thread: almost NO system calls (just spinning in userspace)
strace -p <PID>   # see: sparse output, few syscalls

# Blocking thread: regular futex calls
# futex(addr, FUTEX_WAIT, ...) — going to sleep
# futex(addr, FUTEX_WAKE, ...) — waking up
```

### 17.1 Rust — Measuring Spin Waste

```rust
// measure_spin.rs

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

fn measure_spin_waste() {
    let flag = Arc::new(AtomicBool::new(false));
    let flag2 = Arc::clone(&flag);

    // Producer sets flag after 10ms
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(10));
        flag2.store(true, Ordering::Release);
    });

    let start = Instant::now();
    let mut spin_count: u64 = 0;

    while !flag.load(Ordering::Acquire) {
        spin_count += 1;
        std::hint::spin_loop();
    }

    let elapsed = start.elapsed();
    println!(
        "Waited: {:?} | Spin iterations: {} | ~{:.0} iterations/ms",
        elapsed,
        spin_count,
        spin_count as f64 / elapsed.as_secs_f64() / 1000.0
    );
    println!(
        "CPU cycles wasted: ~{} billion",
        spin_count / 1_000_000_000 + 1
    );
}

fn main() {
    measure_spin_waste();
}
```

---

## 18. Decision Tree: What to Use When

```
START: You need one thread to wait for something from another thread.
│
├── Q1: How long is the typical wait?
│   │
│   ├── < 1 microsecond (ns range)
│   │   └── USE: Spin lock / std::hint::spin_loop()
│   │         Reason: context switch (~1µs) costs more than the wait
│   │
│   └── > 1 microsecond (µs–ms range)
│       └── GO TO Q2
│
├── Q2: What are you waiting FOR?
│   │
│   ├── A LOCK (mutual exclusion, one thread at a time)
│   │   └── USE: Mutex
│   │         C:    pthread_mutex_t
│   │         Rust: std::sync::Mutex
│   │         Go:   sync.Mutex
│   │
│   ├── A CONDITION (wait until some boolean is true)
│   │   └── USE: Condition Variable
│   │         C:    pthread_cond_t + pthread_mutex_t
│   │         Rust: std::sync::Condvar + Mutex
│   │         Go:   channel (idiomatic) or sync.Cond
│   │
│   ├── N RESOURCES (semaphore pattern)
│   │   └── USE: Semaphore
│   │         C:    sem_t (POSIX)
│   │         Rust: build with Condvar + Mutex (no stdlib sem)
│   │         Go:   buffered channel (make(chan struct{}, N))
│   │
│   └── DATA TRANSFER between goroutines/threads
│       └── USE: Channel (Go) / MPSC channel (Rust)
│             Go:   chan T
│             Rust: std::sync::mpsc
│
└── Q3: Do you need ultra-low latency AND are waits sometimes short?
    │
    ├── YES: USE Hybrid spin-then-block
    │         Spin for ~100 iterations, then block
    │         C:    futex (Linux), or WaitOnAddress (Windows)
    │         Rust: parking_lot crate (adaptive mutex)
    │         Go:   sync.Mutex is already adaptive internally
    │
    └── NO: USE standard blocking primitive (see Q2)
```

---

## 19. Summary of Mental Models

### The Core Insight

```
BUSY WAIT:
Thread on CPU → checking condition → CPU registers: "BUSY"
Produces:   0 units of work
Consumes:   100% of 1 CPU core
Generates:  heat, power consumption, cache pressure

BLOCKING:
Thread off CPU → sleeping → CPU registers: "FREE"
Produces:   0 units of work
Consumes:   0% CPU
Generates:  nothing — thread is truly idle
```

### The Three Rules

```
RULE 1: If wait > cost of context switch → BLOCK
        (context switch ≈ 1–10 µs)

RULE 2: If wait < cost of context switch → SPIN
        (but add std::hint::spin_loop() hint)

RULE 3: If you don't know → start with blocking
        Profile first, optimize second
        Premature spin-optimization is a real problem
```

### Cognitive Model: The Waiting Room Analogy

```
BUSY WAIT ≡ Standing at the door, checking every millisecond.
            You are PRESENT, AWAKE, DOING NOTHING USEFUL.
            The space you occupy (CPU core) cannot be used by anyone else.

BLOCKING   ≡ Sitting in the waiting room, reading a book.
            You are PRESENT but NOT CONSUMING THE DOOR.
            Others can check in; the receptionist will call your name.
            You instantly stop reading when called (OS wakeup).

CHANNEL    ≡ Going home. The receptionist will call your phone.
(Go)          You are NOT PRESENT at all.
            Maximum efficiency. Zero resource consumption while waiting.
```

### Key Primitives Summary

| Primitive | Language | CPU while waiting | Use Case |
|-----------|----------|------------------|----------|
| `while flag == 0 {}` | C/Rust/Go | 100% (bad!) | Never, unless truly < 1µs |
| `spin_loop()` hint | Rust | ~95% (less bad) | Sub-µs, kernel code |
| `pthread_mutex_t` | C | 0% | Mutual exclusion |
| `pthread_cond_t` | C | 0% | Condition waiting |
| `sem_t` | C | 0% | N-resource limiting |
| `Mutex<T>` | Rust | 0% | Mutual exclusion |
| `Condvar` | Rust | 0% | Condition waiting |
| `Arc<(Mutex, Condvar)>` | Rust | 0% | Signaling between threads |
| `chan T` | Go | 0% | Data passing + sync |
| `select {}` | Go | 0% | Multiple channel wait |
| `sync.WaitGroup` | Go | 0% | Waiting for N goroutines |

---

## Further Reading and Deliberate Practice

### Problems to solve (in order of depth)

1. **Implement** a blocking flag using condvar (C, then Rust, then Go channels)
2. **Implement** a bounded blocking queue (producer blocks when full, consumer blocks when empty)
3. **Implement** a reader-writer lock (multiple readers OR one writer, never both)
4. **Implement** a barrier (N threads must all arrive before any continue)
5. **Implement** a semaphore from scratch using only a mutex and condvar
6. **Profile** a program using `perf` — find and eliminate a busy wait

### Cognitive Principle: Deliberate Practice Applied Here

Each primitive above (mutex, condvar, semaphore, channel) is a **chunk** in cognitive chunking theory. Once a primitive is a solid mental unit, you can combine them to solve complex synchronization problems the way a master chess player recognizes patterns rather than computing moves.

Your goal: make these primitives instinctive. Then when you see "Thread A waits for Thread B", you immediately pattern-match to the right tool without analysis paralysis.

> *"The expert is one who has converted conscious incompetence to unconscious competence — the right primitive appears without effort."*

---

*Document ends. Build these implementations yourself. Profile them. Break them deliberately. That is the path.*

Here's your complete guide. Let me walk you through what's inside and the core mental architecture:

---

## What the guide covers

**The Problem — What & Why**
- Exact definition of busy waiting with CPU assembly-level breakdown showing *what the hardware actually executes* during a spin loop
- Cache line thrashing explained with ASCII — why two threads fighting over one flag causes ~40x slower memory access
- Power states (C0/C1/C6) showing the thermal and electrical cost of spinning

**Four Forms of Busy Waiting** — pure spin → PAUSE hint → yield → exponential backoff — each with trade-offs

**The Root Contrast: Polling vs Interrupts**
The email inbox analogy ties it together: polling = refreshing every second; interrupt = phone buzzes when mail arrives.

**Full Implementations in C, Rust, Go:**
- Spin locks from scratch (with CAS explained from first principles)
- Blocking POSIX mutex in C
- Condition variables (C + Rust) — with the critical "why while-not-if" explained
- Semaphores (C + Rust built from condvar)
- Go channels + `select` for multi-condition waiting
- Hybrid spin-then-block (the real production strategy)

**The Decision Tree** answers the only question that matters in practice: *what primitive do I reach for, and when?*

---

## The One Principle to Internalize

```
wait duration vs context switch cost (~1–10 µs)

wait < switch cost  → SPIN   (spinning is cheaper than sleeping+waking)
wait > switch cost  → BLOCK  (sleeping burns zero CPU)
don't know          → BLOCK  (measure first, optimize second)
```

Mastering this threshold is what separates engineers who blindly mutex everything from those who choose precisely. The guide gives you the tools to measure both.