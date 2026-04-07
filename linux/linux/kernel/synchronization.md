# The Complete Synchronization Guide
## From First Principles to Linux Kernel Internals

> *"Concurrency is not parallelism — but both demand discipline."*  
> Train like a monk. Think like a systems engineer.

---

## TABLE OF CONTENTS

1. [Foundations: Why Synchronization Exists](#1-foundations)
2. [The Hardware Reality: CPU, Cache, Memory](#2-hardware-reality)
3. [Memory Models & Ordering](#3-memory-models)
4. [Atomicity & Atomic Operations](#4-atomicity)
5. [Race Conditions & Critical Sections](#5-race-conditions)
6. [Mutual Exclusion: Mutex & Lock](#6-mutex)
7. [Spinlocks](#7-spinlocks)
8. [Read-Write Locks (RWLock)](#8-rwlock)
9. [Semaphores](#9-semaphores)
10. [Condition Variables](#10-condition-variables)
11. [Monitors](#11-monitors)
12. [Barriers & Fences](#12-barriers)
13. [Lock-Free & Wait-Free Programming](#13-lockfree)
14. [Classic Synchronization Problems](#14-classic-problems)
15. [Deadlock, Livelock, Starvation](#15-deadlock)
16. [Priority Inversion](#16-priority-inversion)
17. [Linux Kernel Synchronization Primitives](#17-linux-kernel)
18. [RCU: Read-Copy-Update](#18-rcu)
19. [Seqlocks](#19-seqlocks)
20. [Per-CPU Variables](#20-percpu)
21. [Memory Barriers in Depth](#21-memory-barriers)
22. [Transactional Memory](#22-transactional-memory)
23. [Mental Models & Expert Intuition](#23-mental-models)

---

# 1. FOUNDATIONS: WHY SYNCHRONIZATION EXISTS {#1-foundations}

## 1.1 The Sequential Illusion

When you write a single-threaded program, you enjoy a beautiful illusion: instructions execute one after another, in the exact order you wrote them, on a single timeline.

```
Thread A: read x → compute → write x → done
```

This is the **sequential execution model** — simple, predictable, safe.

## 1.2 The Concurrent Reality

Modern systems run **multiple threads** (or processes) simultaneously:
- Multiple CPU cores execute different instruction streams **at the same time**
- The operating system time-slices threads on each core
- Hardware reorders instructions for performance
- Caches hold different "views" of memory on different cores

```
Core 0 (Thread A):   read x ──────────────────── write x
Core 1 (Thread B):            read x ── write x
                                         ↑
                              What value does B read?
                              What is the final value of x?
```

When multiple threads access **shared mutable state** without coordination, the result is **undefined**, **non-deterministic**, and often catastrophically wrong.

**Synchronization** is the discipline of coordinating concurrent access so that programs behave correctly regardless of the speed or ordering of threads.

## 1.3 A Concrete Motivating Example

Imagine a bank: two tellers both read your balance ($1000), both add $500 from separate deposits, both write back.

```
Teller A: reads $1000 → computes $1500 → writes $1500
Teller B: reads $1000 → computes $1500 → writes $1500
Final balance: $1500   ← WRONG! Should be $2000
```

This is called a **lost update** — one write overwrote another. No crashes. No errors. Just silently wrong data. This is why synchronization is among the most dangerous and subtle topics in systems programming.

---

# 2. THE HARDWARE REALITY: CPU, CACHE, MEMORY {#2-hardware-reality}

## 2.1 The Memory Hierarchy

Before understanding synchronization, you must understand *why* it is hard at the hardware level.

```
Speed (fast→slow):   Registers → L1 Cache → L2 Cache → L3 Cache → RAM → Disk

                     ┌──────────────────────────────────────────────┐
                     │                   CPU Core 0                  │
                     │  ┌──────────┐   ┌──────────┐   ┌──────────┐ │
                     │  │Registers │   │  L1 Cache│   │  L2 Cache│ │
                     │  │ ~1 cycle │   │ ~4 cycles│   │~12 cycles│ │
                     │  └──────────┘   └──────────┘   └──────────┘ │
                     └──────────────────────────────────────────────┘
                     ┌──────────────────────────────────────────────┐
                     │                   CPU Core 1                  │
                     │  ┌──────────┐   ┌──────────┐   ┌──────────┐ │
                     │  │Registers │   │  L1 Cache│   │  L2 Cache│ │
                     │  └──────────┘   └──────────┘   └──────────┘ │
                     └──────────────────────────────────────────────┘
                                  ┌────────────┐
                                  │  L3 Cache  │  shared, ~40 cycles
                                  └────────────┘
                                  ┌────────────┐
                                  │    RAM     │  ~100-200 cycles
                                  └────────────┘
```

**Key insight**: Each CPU core has its own **private** L1/L2 cache. A write to memory from Core 0 is NOT immediately visible to Core 1. The hardware uses **cache coherence protocols** (like MESI) to propagate changes, but this takes time and is not instantaneous from a program's perspective without explicit synchronization.

## 2.2 Cache Coherence: The MESI Protocol

**MESI** = Modified, Exclusive, Shared, Invalid — the four states a cache line can be in.

```
State        Meaning
─────────────────────────────────────────────────────────────
Modified     Line is in THIS cache only, DIRTY (differs from RAM)
Exclusive    Line is in THIS cache only, CLEAN (matches RAM)
Shared       Line may be in MULTIPLE caches, all CLEAN
Invalid      Line is stale; must fetch from another cache or RAM
```

**The problem**: Between the time Core 0 writes a value and Core 1 invalidates its cached copy and fetches the new value, there is a **window of inconsistency**. Without explicit synchronization instructions, you cannot predict when (or if) Core 1 will see Core 0's write.

## 2.3 Out-of-Order Execution & Instruction Reordering

Modern CPUs don't execute instructions in program order. They use:

- **Out-of-Order Execution (OOO)**: CPU reorders instructions internally for performance
- **Store Buffers**: Writes are queued in a buffer before being committed to cache
- **Invalidation Queues**: Invalidation messages from other cores are buffered

**The compiler also reorders**: The compiler may reorder instructions as long as the result appears correct *for a single thread*. It does not consider multi-threaded correctness by default.

```c
// What you write:
flag = 1;
data = 42;

// What the compiler/CPU might actually execute:
data = 42;   // reordered BEFORE flag!
flag = 1;
```

If another thread polls `flag` and then reads `data`, it might see `flag=1` but `data=0` (the old value).

## 2.4 False Sharing

A **cache line** is typically 64 bytes. If two threads write to different variables that happen to be in the *same* cache line, they cause **cache line bouncing** — the line is constantly being invalidated and fetched between cores, destroying performance even though the threads are logically independent.

```
Cache line (64 bytes):
[ counter_A (8 bytes) | counter_B (8 bytes) | padding (48 bytes) ]
    Thread A writes ↑       Thread B writes ↑

Even though A and B write different variables,
they fight over the SAME cache line → false sharing
```

**Solution**: Pad structs to align each hot field to a separate cache line.

---

# 3. MEMORY MODELS & ORDERING {#3-memory-models}

## 3.1 What is a Memory Model?

A **memory model** is a contract between:
- The programmer (who writes the code)
- The compiler (which transforms the code)
- The hardware (which executes the code)

It defines: **what values a thread is allowed to observe** when it reads a memory location.

Without a memory model, every read could potentially return any previously-written value — making reasoning about concurrent programs impossible.

## 3.2 Memory Ordering Levels

From weakest (fastest, least guarantees) to strongest (slowest, most guarantees):

```
Relaxed ──────────────────────────────────────────── SeqCst
  │                                                      │
  │  Acquire                     Release                 │
  │──────────────────────────────────────────            │
  │                                                      │
fastest, minimal guarantees              slowest, total order
```

### Relaxed Ordering
No synchronization guarantees. Only atomicity of the operation itself. Used for counters where you don't care about the exact value observed by other threads.

```c
// C11 atomic
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);
```

### Acquire Ordering
A **load** with acquire semantics: all reads/writes AFTER this load (in program order) cannot be reordered BEFORE it. Think of it as: "I am acquiring a lock — let me first see all the writes that happened before the lock was released."

```
Thread A (release):              Thread B (acquire):
  data = 42;                       if (flag.load(acquire) == 1):
  flag.store(1, release);            // guaranteed to see data == 42
```

### Release Ordering
A **store** with release semantics: all reads/writes BEFORE this store (in program order) cannot be reordered AFTER it. Think of it as: "I am releasing a lock — let all my preceding writes be visible first."

### Sequentially Consistent (SeqCst)
The strongest ordering. All sequentially consistent operations appear in a single total order observed by all threads. This is what most humans intuitively expect but what hardware doesn't provide by default.

## 3.3 Happens-Before Relationship

**Happens-before** is the formal mathematical relation that defines visibility in concurrent programs.

Operation A **happens-before** operation B means: A's side effects are guaranteed to be visible to B.

Rules for happens-before:
1. Within a single thread: if A comes before B in program order, A happens-before B
2. Synchronization: a mutex unlock **happens-before** the next lock of the same mutex
3. Thread creation: all ops before `thread_create(T)` happen-before all ops in T
4. Thread join: all ops in T happen-before a successful `thread_join(T)` returns

```
Thread A:                    Thread B:
  x = 1;           ┐
  mutex.lock();    │         mutex.lock();   ←─── This is the
  y = 2;           │happens     z = y;            synchronization
  mutex.unlock();  ┘before      mutex.unlock();   point
```

Here: `x=1` and `y=2` happen-before `z=y`. So B will see `y=2`. But B's view of `x` is also guaranteed (through the mutex's happens-before chain).

## 3.4 C11/C++11 Memory Model

C11 introduced formal memory model semantics via `<stdatomic.h>`:

```c
#include <stdatomic.h>

atomic_int counter = ATOMIC_VAR_INIT(0);

// Different ordering modes:
atomic_store_explicit(&counter, 1, memory_order_relaxed);
atomic_store_explicit(&counter, 1, memory_order_release);
atomic_store_explicit(&counter, 1, memory_order_seq_cst);

atomic_load_explicit(&counter, memory_order_relaxed);
atomic_load_explicit(&counter, memory_order_acquire);
atomic_load_explicit(&counter, memory_order_seq_cst);
```

## 3.5 Rust Memory Model

Rust's `std::sync::atomic` mirrors C++11:

```rust
use std::sync::atomic::{AtomicI32, Ordering};

let counter = AtomicI32::new(0);
counter.store(1, Ordering::Relaxed);
counter.store(1, Ordering::Release);
counter.store(1, Ordering::SeqCst);

counter.load(Ordering::Relaxed);
counter.load(Ordering::Acquire);
counter.load(Ordering::SeqCst);
```

## 3.6 Go Memory Model

Go's memory model is simpler: it defines synchronization through **channel operations**, **sync primitives**, and **atomic operations** in `sync/atomic`. Go's model says: "within a goroutine, happens-before follows program order; across goroutines, you need explicit synchronization."

---

# 4. ATOMICITY & ATOMIC OPERATIONS {#4-atomicity}

## 4.1 What is Atomicity?

An operation is **atomic** if it appears to execute as a single indivisible unit — no other thread can observe a partial state of the operation.

**Non-atomic example**: `x++` in C compiles to:
```
LOAD  x → register
ADD   register, 1
STORE register → x
```
These are THREE separate instructions. A thread switch can happen between any two steps.

**Atomic example**: Hardware provides special instructions like `LOCK XADD` on x86 that perform read-modify-write atomically.

## 4.2 Hardware Atomic Primitives

Modern CPUs provide several fundamental atomic operations:

### Test-and-Set (TAS)
Atomically: read value, write 1, return old value.
```
atomic {
    old = *ptr;
    *ptr = 1;
    return old;
}
```

### Compare-and-Swap (CAS) — The Foundation of Lock-Free
Atomically: if `*ptr == expected`, set `*ptr = new` and return true; else return false.
```
atomic {
    if (*ptr == expected) {
        *ptr = new;
        return true;
    }
    return false;
}
```

CAS is the most powerful primitive. Almost every lock-free algorithm is built from CAS.

### Fetch-and-Add (FAA)
Atomically: read value, add delta, return old value.
```
atomic {
    old = *ptr;
    *ptr = old + delta;
    return old;
}
```

## 4.3 C Implementation: Atomic Operations

```c
#include <stdio.h>
#include <stdatomic.h>
#include <pthread.h>
#include <stdlib.h>

// ============================================================
// SECTION: Basic Atomic Counter
// ============================================================

atomic_int shared_counter = 0;

void* increment_worker(void* arg) {
    int iterations = *(int*)arg;
    for (int i = 0; i < iterations; i++) {
        // atomic_fetch_add returns old value, adds 1
        atomic_fetch_add_explicit(&shared_counter, 1, memory_order_relaxed);
    }
    return NULL;
}

void demo_atomic_counter(void) {
    const int NUM_THREADS = 4;
    const int ITERATIONS  = 100000;
    pthread_t threads[NUM_THREADS];
    int iters = ITERATIONS;

    for (int i = 0; i < NUM_THREADS; i++)
        pthread_create(&threads[i], NULL, increment_worker, &iters);
    for (int i = 0; i < NUM_THREADS; i++)
        pthread_join(threads[i], NULL);

    printf("Expected: %d, Got: %d\n",
           NUM_THREADS * ITERATIONS,
           atomic_load(&shared_counter));
    // Will always print the correct value because of atomicity
}

// ============================================================
// SECTION: Compare-and-Swap (CAS) — Manual Implementation
// ============================================================

// Simulate a lock using CAS (this is essentially a spinlock)
typedef atomic_int cas_lock_t;

void cas_lock_init(cas_lock_t* lock) {
    atomic_store(lock, 0); // 0 = unlocked, 1 = locked
}

void cas_lock_acquire(cas_lock_t* lock) {
    int expected = 0;
    // Spin until we successfully swap 0 → 1
    while (!atomic_compare_exchange_weak_explicit(
                lock,
                &expected,    // expected value
                1,            // desired value
                memory_order_acquire,  // success ordering
                memory_order_relaxed   // failure ordering
           )) {
        expected = 0; // reset expected after failure
        // Optional: CPU hint to reduce power/contention
        // __builtin_ia32_pause(); // x86 PAUSE instruction
    }
}

void cas_lock_release(cas_lock_t* lock) {
    atomic_store_explicit(lock, 0, memory_order_release);
}

// ============================================================
// SECTION: Lock-Free Stack using CAS
// ============================================================

typedef struct node {
    int value;
    struct node* next;
} node_t;

// _Atomic pointer — the pointer itself is atomic
typedef _Atomic(node_t*) atomic_node_ptr;

typedef struct {
    atomic_node_ptr top;
} lock_free_stack_t;

void stack_init(lock_free_stack_t* s) {
    atomic_store(&s->top, NULL);
}

void stack_push(lock_free_stack_t* s, int value) {
    node_t* new_node = malloc(sizeof(node_t));
    new_node->value = value;

    node_t* old_top;
    do {
        old_top = atomic_load_explicit(&s->top, memory_order_relaxed);
        new_node->next = old_top;
        // CAS: if top is still old_top, set it to new_node
    } while (!atomic_compare_exchange_weak_explicit(
                 &s->top, &old_top, new_node,
                 memory_order_release,
                 memory_order_relaxed));
}

int stack_pop(lock_free_stack_t* s, int* out_value) {
    node_t* old_top;
    node_t* new_top;
    do {
        old_top = atomic_load_explicit(&s->top, memory_order_acquire);
        if (old_top == NULL) return 0; // empty
        new_top = old_top->next;
    } while (!atomic_compare_exchange_weak_explicit(
                 &s->top, &old_top, new_top,
                 memory_order_acquire,
                 memory_order_relaxed));

    *out_value = old_top->value;
    free(old_top);
    return 1;
}

int main(void) {
    demo_atomic_counter();

    lock_free_stack_t stack;
    stack_init(&stack);
    stack_push(&stack, 10);
    stack_push(&stack, 20);
    stack_push(&stack, 30);

    int val;
    while (stack_pop(&stack, &val))
        printf("Popped: %d\n", val);

    return 0;
}
```

## 4.4 Rust Implementation: Atomic Operations

```rust
use std::sync::atomic::{AtomicI32, AtomicPtr, Ordering};
use std::sync::Arc;
use std::thread;
use std::ptr;

// ============================================================
// SECTION: Atomic Counter
// ============================================================

fn demo_atomic_counter() {
    let counter = Arc::new(AtomicI32::new(0));
    let mut handles = vec![];

    for _ in 0..4 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..100_000 {
                c.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    println!("Counter: {}", counter.load(Ordering::SeqCst));
    // Always prints 400000
}

// ============================================================
// SECTION: Spinlock using AtomicBool + CAS
// ============================================================

use std::sync::atomic::AtomicBool;
use std::hint;

pub struct SpinLock {
    locked: AtomicBool,
}

impl SpinLock {
    pub const fn new() -> Self {
        SpinLock { locked: AtomicBool::new(false) }
    }

    pub fn acquire(&self) {
        // compare_exchange: if locked==false, set to true
        // Uses acquire ordering on success (establishes happens-before)
        // Uses relaxed on failure (just spinning, no sync needed)
        while self.locked
            .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            // Spin with hint::spin_loop() — tells CPU we're in a spin loop
            // On x86 this emits PAUSE, reducing power and helping hyperthreading
            while self.locked.load(Ordering::Relaxed) {
                hint::spin_loop();
            }
        }
    }

    pub fn release(&self) {
        self.locked.store(false, Ordering::Release);
    }
}

// ============================================================
// SECTION: Lock-Free Stack
// ============================================================

struct Node<T> {
    value: T,
    next: *mut Node<T>,
}

pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

// Safety: We manage the pointer carefully with CAS
unsafe impl<T: Send> Send for LockFreeStack<T> {}
unsafe impl<T: Send> Sync for LockFreeStack<T> {}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack { head: AtomicPtr::new(ptr::null_mut()) }
    }

    pub fn push(&self, value: T) {
        let new_node = Box::into_raw(Box::new(Node {
            value,
            next: ptr::null_mut(),
        }));

        loop {
            let old_head = self.head.load(Ordering::Relaxed);
            unsafe { (*new_node).next = old_head; }

            // CAS: if head == old_head, swap in new_node
            match self.head.compare_exchange_weak(
                old_head, new_node,
                Ordering::Release, Ordering::Relaxed,
            ) {
                Ok(_)  => break,
                Err(_) => {} // retry
            }
        }
    }

    pub fn pop(&self) -> Option<T> {
        loop {
            let old_head = self.head.load(Ordering::Acquire);
            if old_head.is_null() { return None; }

            let new_head = unsafe { (*old_head).next };

            match self.head.compare_exchange_weak(
                old_head, new_head,
                Ordering::Acquire, Ordering::Relaxed,
            ) {
                Ok(_) => {
                    let value = unsafe {
                        let node = Box::from_raw(old_head);
                        node.value
                    };
                    return Some(value);
                }
                Err(_) => {} // retry
            }
        }
    }
}

fn main() {
    demo_atomic_counter();

    let stack = LockFreeStack::new();
    stack.push(10);
    stack.push(20);
    stack.push(30);
    while let Some(v) = stack.pop() {
        println!("Popped: {}", v);
    }
}
```

## 4.5 Go Implementation: Atomic Operations

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
    "unsafe"
)

// ============================================================
// SECTION: Atomic Counter
// ============================================================

func demoAtomicCounter() {
    var counter int64
    var wg sync.WaitGroup

    for i := 0; i < 4; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 100_000; j++ {
                atomic.AddInt64(&counter, 1)
            }
        }()
    }

    wg.Wait()
    fmt.Printf("Counter: %d\n", atomic.LoadInt64(&counter))
    // Always prints 400000
}

// ============================================================
// SECTION: CAS-based Spinlock
// ============================================================

type SpinLock struct {
    state int32 // 0=unlocked, 1=locked
}

func (sl *SpinLock) Lock() {
    for !atomic.CompareAndSwapInt32(&sl.state, 0, 1) {
        // Spin. In production use runtime.Gosched() to yield.
        // Pure spinning is dangerous in Go's cooperative scheduler.
    }
}

func (sl *SpinLock) Unlock() {
    atomic.StoreInt32(&sl.state, 0)
}

// ============================================================
// SECTION: Lock-Free Stack using unsafe + CAS
// ============================================================

type stackNode struct {
    value int
    next  unsafe.Pointer // *stackNode
}

type LockFreeStack struct {
    head unsafe.Pointer // *stackNode
}

func (s *LockFreeStack) Push(value int) {
    newNode := &stackNode{value: value}
    for {
        oldHead := atomic.LoadPointer(&s.head)
        newNode.next = oldHead
        if atomic.CompareAndSwapPointer(&s.head,
            oldHead, unsafe.Pointer(newNode)) {
            return
        }
    }
}

func (s *LockFreeStack) Pop() (int, bool) {
    for {
        oldHead := atomic.LoadPointer(&s.head)
        if oldHead == nil {
            return 0, false
        }
        node := (*stackNode)(oldHead)
        newHead := atomic.LoadPointer(&node.next)
        if atomic.CompareAndSwapPointer(&s.head, oldHead, newHead) {
            return node.value, true
        }
    }
}

func main() {
    demoAtomicCounter()

    s := &LockFreeStack{}
    s.Push(10)
    s.Push(20)
    s.Push(30)
    for {
        v, ok := s.Pop()
        if !ok { break }
        fmt.Printf("Popped: %d\n", v)
    }
}
```

---

# 5. RACE CONDITIONS & CRITICAL SECTIONS {#5-race-conditions}

## 5.1 What is a Race Condition?

A **race condition** occurs when the correctness of a program depends on the relative timing or interleaving of multiple threads. The outcome "races" with the scheduling decisions made by the OS.

**Formal definition**: A data race occurs when:
1. Two or more threads access the same memory location **concurrently**
2. At least one access is a **write**
3. There is **no synchronization** between the accesses

## 5.2 Anatomy of a Race Condition

```
                    Thread A                Thread B
                    ────────                ────────
Time 1:             LOAD x (reads 0)
Time 2:                                     LOAD x (reads 0)
Time 3:             ADD 1 → 1
Time 4:                                     ADD 1 → 1
Time 5:             STORE x = 1
Time 6:                                     STORE x = 1
                    
                    Expected x = 2, Got x = 1  ← RACE CONDITION
```

This is called a **write-write race** (two threads both wrote). There are also **read-write races** (one reads, one writes concurrently).

## 5.3 The Critical Section

A **critical section** is a region of code that accesses shared resources and must not be executed by more than one thread at a time.

```
┌─────────────────────────────────────────────┐
│              Thread Execution               │
│                                             │
│  Non-critical code (safe to run parallel)  │
│            ↓                               │
│  ┌─────────────────────────────────┐       │
│  │        CRITICAL SECTION         │       │
│  │  (access to shared resources)   │  ←────┼── Only ONE thread
│  │  balance += deposit;            │       │    at a time!
│  └─────────────────────────────────┘       │
│            ↓                               │
│  Non-critical code (safe to run parallel)  │
└─────────────────────────────────────────────┘
```

**Requirements for correct critical section management** (the **Mutual Exclusion Problem**):

1. **Mutual Exclusion**: At most one thread in the critical section at any time
2. **Progress**: If no thread is in the critical section and some want to enter, one must be allowed to eventually enter
3. **Bounded Waiting**: A thread requesting entry must eventually be granted it (no starvation)
4. **No busy waiting** (desirable, not strictly required): Threads waiting should not consume CPU

## 5.4 Detecting Race Conditions

### ThreadSanitizer (TSan)
A powerful runtime race detector built into GCC and Clang:

```bash
# C/C++
gcc -fsanitize=thread -g -o program program.c
./program

# Go (built-in)
go run -race main.go
go build -race -o program .

# Rust (using LLVM's TSan)
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run
```

TSan instruments memory accesses and tracks synchronization events to detect data races at runtime.

---

# 6. MUTUAL EXCLUSION: MUTEX & LOCK {#6-mutex}

## 6.1 What is a Mutex?

**Mutex** = **Mut**ual **Ex**clusion lock.

A mutex is a synchronization primitive with exactly two states: **locked** and **unlocked**. Only one thread can hold the lock at a time. Any other thread that tries to lock it will **block** (be put to sleep by the OS) until the holder unlocks it.

```
State Machine:
                    lock()              unlock()
    UNLOCKED ──────────────→ LOCKED ──────────────→ UNLOCKED
         ↑                                               │
         └───────────────────────────────────────────────┘
         
    Thread trying to lock() on a LOCKED mutex:
    → Goes to SLEEP (OS removes it from runqueue)
    → Woken up when current holder calls unlock()
```

## 6.2 Mutex Internal Implementation (Conceptual)

Underneath, a mutex typically uses:
1. An **atomic flag** (locked/unlocked)
2. A **wait queue** (list of sleeping threads)

```
mutex = {
    atomic_int state;     // 0=unlocked, 1=locked (or 2=contended)
    wait_queue_t waiters; // threads sleeping on this mutex
}

lock(mutex):
    if CAS(mutex.state, 0, 1) succeeds:
        return  // fast path: no contention
    else:
        // slow path: mark as contended and sleep
        state = 2  // 2 = locked + contended
        while (state != 0):
            futex_wait(mutex.state, 2)  // sleep in kernel
            CAS(mutex.state, 0, 2)      // try to acquire again

unlock(mutex):
    if atomic_swap(mutex.state, 0) == 2:  // was contended?
        futex_wake(mutex.state, 1)   // wake one waiter
```

The key system call on Linux is **futex** (Fast Userspace muTEX), which allows lock/unlock in userspace without a syscall in the uncontended case.

## 6.3 C Implementation: POSIX Mutex

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <errno.h>
#include <string.h>

// ============================================================
// SECTION: Basic Mutex Usage
// ============================================================

typedef struct {
    pthread_mutex_t lock;
    long balance;
} bank_account_t;

void account_init(bank_account_t* acc, long initial_balance) {
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);

    // PTHREAD_MUTEX_ERRORCHECK: returns error if same thread locks twice
    // PTHREAD_MUTEX_RECURSIVE: allows same thread to lock multiple times
    // PTHREAD_MUTEX_DEFAULT:   undefined behavior on recursive lock
    pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK);

    pthread_mutex_init(&acc->lock, &attr);
    pthread_mutexattr_destroy(&attr);
    acc->balance = initial_balance;
}

void account_destroy(bank_account_t* acc) {
    pthread_mutex_destroy(&acc->lock);
}

int account_deposit(bank_account_t* acc, long amount) {
    int err = pthread_mutex_lock(&acc->lock);
    if (err != 0) {
        fprintf(stderr, "Failed to lock: %s\n", strerror(err));
        return -1;
    }

    // ===== CRITICAL SECTION BEGIN =====
    acc->balance += amount;
    // ===== CRITICAL SECTION END =====

    pthread_mutex_unlock(&acc->lock);
    return 0;
}

int account_withdraw(bank_account_t* acc, long amount) {
    pthread_mutex_lock(&acc->lock);
    int result = 0;
    if (acc->balance >= amount) {
        acc->balance -= amount;
        result = 1; // success
    }
    pthread_mutex_unlock(&acc->lock);
    return result;
}

long account_balance(bank_account_t* acc) {
    pthread_mutex_lock(&acc->lock);
    long b = acc->balance;
    pthread_mutex_unlock(&acc->lock);
    return b;
}

// ============================================================
// SECTION: Transfer between two accounts (two locks — careful!)
// ============================================================

// WRONG — Can deadlock!
void transfer_wrong(bank_account_t* from, bank_account_t* to, long amount) {
    pthread_mutex_lock(&from->lock);  // Thread A locks from
    pthread_mutex_lock(&to->lock);    // Thread A waits for to
                                      // Thread B locked to, waits for from → DEADLOCK
    from->balance -= amount;
    to->balance += amount;
    pthread_mutex_unlock(&to->lock);
    pthread_mutex_unlock(&from->lock);
}

// CORRECT — Lock ordering by address prevents deadlock
void transfer_correct(bank_account_t* acc1, bank_account_t* acc2, long amount) {
    // Always lock the lower-address mutex first — global ordering
    bank_account_t* first  = (acc1 < acc2) ? acc1 : acc2;
    bank_account_t* second = (acc1 < acc2) ? acc2 : acc1;
    bank_account_t* from   = acc1;
    bank_account_t* to     = acc2;

    pthread_mutex_lock(&first->lock);
    pthread_mutex_lock(&second->lock);

    if (from->balance >= amount) {
        from->balance -= amount;
        to->balance += amount;
    }

    pthread_mutex_unlock(&second->lock);
    pthread_mutex_unlock(&first->lock);
}

// ============================================================
// SECTION: Try-lock (non-blocking attempt)
// ============================================================

int account_try_deposit(bank_account_t* acc, long amount) {
    // Returns 0 on success, EBUSY if already locked
    int err = pthread_mutex_trylock(&acc->lock);
    if (err == EBUSY) {
        printf("Mutex busy, skipping deposit\n");
        return -1;
    }
    acc->balance += amount;
    pthread_mutex_unlock(&acc->lock);
    return 0;
}

// ============================================================
// SECTION: Timed lock
// ============================================================

int account_timed_deposit(bank_account_t* acc, long amount, int timeout_ms) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_nsec += timeout_ms * 1000000LL;
    if (ts.tv_nsec >= 1000000000LL) {
        ts.tv_sec++;
        ts.tv_nsec -= 1000000000LL;
    }

    int err = pthread_mutex_timedlock(&acc->lock, &ts);
    if (err == ETIMEDOUT) {
        printf("Timed out waiting for mutex\n");
        return -1;
    }
    acc->balance += amount;
    pthread_mutex_unlock(&acc->lock);
    return 0;
}

int main(void) {
    bank_account_t account;
    account_init(&account, 1000);

    const int NUM_THREADS = 8;
    pthread_t threads[NUM_THREADS];

    // Each thread deposits 100, total should be 1000 + 8*100 = 1800
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, (void*(*)(void*))account_deposit,
                       &(struct {bank_account_t* a; long amt;}){&account, 100});
        // Note: simplified for demo — use a proper arg struct in production
    }
    // For demo correctness, just deposit serially:
    for (int i = 0; i < 8; i++)
        account_deposit(&account, 100);

    printf("Balance: %ld (expected 1800)\n", account_balance(&account));
    account_destroy(&account);
    return 0;
}
```

## 6.4 Rust Implementation: Mutex

```rust
use std::sync::{Arc, Mutex, MutexGuard};
use std::thread;

// ============================================================
// SECTION: Basic Mutex — Rust's Mutex is ALWAYS paired with data
// In Rust, the Mutex<T> OWNS the data it protects.
// You cannot access the data without holding the lock.
// This is enforced at COMPILE TIME — no accidental unsynchronized access.
// ============================================================

#[derive(Debug)]
struct BankAccount {
    balance: i64,
}

fn demo_basic_mutex() {
    // Mutex<BankAccount> — the data IS inside the mutex
    let account = Arc::new(Mutex::new(BankAccount { balance: 1000 }));
    let mut handles = vec![];

    for _ in 0..8 {
        let acc = Arc::clone(&account);
        handles.push(thread::spawn(move || {
            // lock() returns a MutexGuard<BankAccount>
            // Guard implements Deref → you access data through the guard
            // Guard implements Drop → automatically unlocked when guard goes out of scope
            let mut guard: MutexGuard<BankAccount> = acc.lock().unwrap();
            guard.balance += 100;
            // guard drops here → mutex automatically unlocked
            // NO manual unlock() needed!
        }));
    }

    for h in handles { h.join().unwrap(); }

    let final_balance = account.lock().unwrap().balance;
    println!("Balance: {} (expected 1800)", final_balance);
}

// ============================================================
// SECTION: Poisoning — Rust's Unique Safety Feature
// If a thread panics while holding a mutex, the mutex is "poisoned"
// Subsequent lock() calls return Err(PoisonError)
// This prevents other threads from seeing potentially inconsistent state
// ============================================================

fn demo_poisoning() {
    let mutex = Arc::new(Mutex::new(0i32));
    let m = Arc::clone(&mutex);

    let handle = thread::spawn(move || {
        let _guard = m.lock().unwrap();
        panic!("thread panicked while holding lock!");
    });

    let _ = handle.join(); // panicked

    // Now the mutex is "poisoned"
    match mutex.lock() {
        Ok(val)  => println!("Lock acquired: {}", *val),
        Err(e)   => {
            // You can STILL access the data via into_inner()
            let val = e.into_inner();
            println!("Mutex was poisoned, value: {}", *val);
        }
    }
}

// ============================================================
// SECTION: try_lock — non-blocking
// ============================================================

fn demo_try_lock() {
    let mutex = Arc::new(Mutex::new(42));
    let m = Arc::clone(&mutex);

    // Hold the lock in the main thread
    let _guard = mutex.lock().unwrap();

    let handle = thread::spawn(move || {
        match m.try_lock() {
            Ok(val)   => println!("Got lock: {}", *val),
            Err(_)    => println!("Lock busy, moving on"),
        }
    });

    handle.join().unwrap();
}

// ============================================================
// SECTION: Transfer (two mutexes — avoiding deadlock with ordering)
// ============================================================

fn transfer(
    from: &Arc<Mutex<BankAccount>>,
    to: &Arc<Mutex<BankAccount>>,
    amount: i64,
) {
    // Use Arc pointer addresses to enforce consistent lock ordering
    // This is the same "lock by address order" strategy as in C
    let from_ptr = Arc::as_ptr(from) as usize;
    let to_ptr   = Arc::as_ptr(to)   as usize;

    if from_ptr < to_ptr {
        let mut f = from.lock().unwrap();
        let mut t = to.lock().unwrap();
        if f.balance >= amount {
            f.balance -= amount;
            t.balance += amount;
        }
    } else {
        let mut t = to.lock().unwrap();
        let mut f = from.lock().unwrap();
        if f.balance >= amount {
            f.balance -= amount;
            t.balance += amount;
        }
    }
}

fn main() {
    demo_basic_mutex();
    demo_poisoning();
    demo_try_lock();
}
```

## 6.5 Go Implementation: sync.Mutex

```go
package main

import (
    "fmt"
    "sync"
)

// ============================================================
// SECTION: Basic Mutex in Go
// In Go, sync.Mutex is a VALUE type — do NOT copy it after first use.
// Convention: embed in struct with the data it protects.
// ============================================================

type BankAccount struct {
    mu      sync.Mutex // Convention: mu as field name
    balance int64
}

func NewBankAccount(initial int64) *BankAccount {
    return &BankAccount{balance: initial}
}

func (a *BankAccount) Deposit(amount int64) {
    a.mu.Lock()
    defer a.mu.Unlock() // idiomatic Go: always defer Unlock
    a.balance += amount
}

func (a *BankAccount) Withdraw(amount int64) bool {
    a.mu.Lock()
    defer a.mu.Unlock()
    if a.balance < amount {
        return false
    }
    a.balance -= amount
    return true
}

func (a *BankAccount) Balance() int64 {
    a.mu.Lock()
    defer a.mu.Unlock()
    return a.balance
}

// ============================================================
// SECTION: TryLock (Go 1.18+)
// ============================================================

func (a *BankAccount) TryDeposit(amount int64) bool {
    if !a.mu.TryLock() {
        return false // mutex is already locked
    }
    defer a.mu.Unlock()
    a.balance += amount
    return true
}

// ============================================================
// SECTION: Transfer — Lock ordering by pointer value
// ============================================================

func Transfer(from, to *BankAccount, amount int64) {
    // Enforce consistent ordering using pointer comparison
    first, second := from, to
    if uintptr(fmt.Sprintf("%p", from)[0]) > uintptr(fmt.Sprintf("%p", to)[0]) {
        first, second = to, from
    }
    // Better: use unsafe.Pointer for comparison
    first.mu.Lock()
    second.mu.Lock()
    defer second.mu.Unlock()
    defer first.mu.Unlock()

    if from.balance >= amount {
        from.balance -= amount
        to.balance += amount
    }
}

func main() {
    account := NewBankAccount(1000)
    var wg sync.WaitGroup

    for i := 0; i < 8; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            account.Deposit(100)
        }()
    }

    wg.Wait()
    fmt.Printf("Balance: %d (expected 1800)\n", account.Balance())
}
```

## 6.6 Decision Flow: When to Use a Mutex

```
Do you have shared mutable state?
    │
    ├── No → No synchronization needed
    │
    └── Yes
          │
          ├── Is contention LOW and hold time SHORT?
          │       └── Yes → Consider SPINLOCK (avoid syscall overhead)
          │
          ├── Is access mostly READS with occasional WRITES?
          │       └── Yes → Consider RWLOCK
          │
          ├── Do you need PRODUCER-CONSUMER patterns?
          │       └── Yes → Consider MUTEX + CONDITION VARIABLE
          │
          └── Is access UNCONTENDED mostly?
                  └── Yes → MUTEX is perfect (futex fast path)
```

---

# 7. SPINLOCKS {#7-spinlocks}

## 7.1 What is a Spinlock?

A **spinlock** is a lock where the waiting thread does NOT go to sleep. Instead, it continuously "spins" in a tight loop, repeatedly checking if the lock is available.

```
lock(spinlock):
    while (compare_and_swap(spinlock, 0, 1) fails):
        // Keep looping! (spinning)
        // CPU is 100% utilized on this core during the wait
        NOP / PAUSE / hint
    // Lock acquired
```

**Contrast with mutex**:
```
Mutex:    Thread blocks → OS context switch (expensive ~1-10μs)
Spinlock: Thread spins  → No context switch but wastes CPU cycles
```

## 7.2 When to Use Spinlocks

| Use Spinlock | Use Mutex |
|---|---|
| Lock hold time is very short (< 1-2 μs) | Lock hold time may be long |
| Low contention expected | High contention possible |
| Cannot sleep (interrupt context, kernel) | Userspace threads are fine sleeping |
| Single-CPU: **NEVER** (deadlocks!) | Any environment |
| Lock-time < context switch cost | When sleep is acceptable |

**The golden rule**: Never use a spinlock if the holder might be preempted or if the waiter and holder are on the **same CPU core**.

## 7.3 Ticket Spinlock (Fair Spinlock)

A basic test-and-set spinlock has a problem: **unfairness** — any waiting thread might acquire the lock after release, not necessarily the longest-waiting one.

A **ticket lock** works like a bakery: take a number, wait for your number to be called.

```
ticket_lock = {
    next_ticket: atomic_int,  // dispenser
    now_serving: atomic_int,  // display
}

lock:
    my_ticket = fetch_and_add(next_ticket, 1)
    while (now_serving != my_ticket):
        spin()

unlock:
    fetch_and_add(now_serving, 1)
```

This guarantees **FIFO ordering** — threads are served in the order they arrived.

## 7.4 C Implementation: Spinlock Variants

```c
#include <stdio.h>
#include <stdatomic.h>
#include <pthread.h>
#include <stdlib.h>

// ============================================================
// SECTION: Test-and-Set Spinlock (Basic, Unfair)
// ============================================================

typedef struct {
    atomic_int locked; // 0=free, 1=held
} tas_spinlock_t;

void tas_init(tas_spinlock_t* sl) {
    atomic_store(&sl->locked, 0);
}

void tas_lock(tas_spinlock_t* sl) {
    // Two-phase spinning: first spin with reads (cheaper, cache-friendly)
    // then try to CAS
    while (1) {
        // Fast path: try to grab immediately
        int expected = 0;
        if (atomic_compare_exchange_weak_explicit(
                &sl->locked, &expected, 1,
                memory_order_acquire, memory_order_relaxed)) {
            return;
        }
        // Slow path: spin on loads until it looks free
        while (atomic_load_explicit(&sl->locked, memory_order_relaxed) != 0) {
            // x86: PAUSE instruction — reduces pipeline pressure
            // Without this, spinning causes memory bus contention
            __asm__ volatile("pause" ::: "memory");
        }
    }
}

void tas_unlock(tas_spinlock_t* sl) {
    atomic_store_explicit(&sl->locked, 0, memory_order_release);
}

// ============================================================
// SECTION: Ticket Spinlock (Fair, FIFO ordering)
// ============================================================

typedef struct {
    atomic_uint next_ticket;   // number to give out
    atomic_uint now_serving;   // currently held ticket
} ticket_spinlock_t;

void ticket_init(ticket_spinlock_t* sl) {
    atomic_store(&sl->next_ticket, 0);
    atomic_store(&sl->now_serving, 0);
}

void ticket_lock(ticket_spinlock_t* sl) {
    // Grab my ticket number
    unsigned my_ticket = atomic_fetch_add_explicit(
        &sl->next_ticket, 1, memory_order_relaxed);

    // Wait until it's our turn
    while (atomic_load_explicit(&sl->now_serving, memory_order_acquire)
           != my_ticket) {
        __asm__ volatile("pause" ::: "memory");
    }
}

void ticket_unlock(ticket_spinlock_t* sl) {
    // Advance the "now serving" counter — next waiter will see their number
    atomic_fetch_add_explicit(&sl->now_serving, 1, memory_order_release);
}

// ============================================================
// SECTION: MCS Lock (Scalable Spinlock — best for many cores)
// Each thread spins on its OWN local variable → no cache line contention
// ============================================================

typedef struct mcs_node {
    _Atomic(struct mcs_node*) next;
    atomic_int                locked; // 1 = still waiting, 0 = acquired
} mcs_node_t;

typedef _Atomic(mcs_node_t*) mcs_lock_t;

void mcs_init(mcs_lock_t* lock) {
    atomic_store(lock, NULL);
}

void mcs_lock(mcs_lock_t* lock, mcs_node_t* node) {
    // Initialize my node
    atomic_store(&node->next, NULL);
    atomic_store(&node->locked, 1); // I'm waiting

    // Atomically put myself at the end of the queue
    mcs_node_t* prev = atomic_exchange(lock, node);

    if (prev == NULL) {
        // Queue was empty — I got the lock immediately
        return;
    }

    // Queue was non-empty — link myself after prev
    atomic_store(&prev->next, node);

    // Spin on MY OWN node's locked field (not the global lock)
    while (atomic_load_explicit(&node->locked, memory_order_acquire) == 1) {
        __asm__ volatile("pause" ::: "memory");
    }
}

void mcs_unlock(mcs_lock_t* lock, mcs_node_t* node) {
    mcs_node_t* next = atomic_load(&node->next);

    if (next == NULL) {
        // Try to set lock back to NULL (I'm the last in queue)
        mcs_node_t* expected = node;
        if (atomic_compare_exchange_strong(lock, &expected, NULL)) {
            return; // Successfully removed self — queue is now empty
        }
        // CAS failed: someone is queuing up — wait for them to set node->next
        while ((next = atomic_load(&node->next)) == NULL) {
            __asm__ volatile("pause" ::: "memory");
        }
    }

    // Hand lock to next waiter
    atomic_store_explicit(&next->locked, 0, memory_order_release);
}

// ============================================================
// SECTION: Benchmark — spinlock vs mutex for short critical sections
// ============================================================

#define ITERATIONS 10000000

static long counter_spin = 0;
static long counter_mutex = 0;
static tas_spinlock_t spin_lock;
static pthread_mutex_t posix_mutex = PTHREAD_MUTEX_INITIALIZER;

void* spinlock_bench(void* arg) {
    for (int i = 0; i < ITERATIONS / 4; i++) {
        tas_lock(&spin_lock);
        counter_spin++;
        tas_unlock(&spin_lock);
    }
    return NULL;
}

void* mutex_bench(void* arg) {
    for (int i = 0; i < ITERATIONS / 4; i++) {
        pthread_mutex_lock(&posix_mutex);
        counter_mutex++;
        pthread_mutex_unlock(&posix_mutex);
    }
    return NULL;
}

int main(void) {
    tas_init(&spin_lock);

    pthread_t t1, t2, t3, t4;

    // Spinlock benchmark
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    pthread_create(&t1, NULL, spinlock_bench, NULL);
    pthread_create(&t2, NULL, spinlock_bench, NULL);
    pthread_create(&t3, NULL, spinlock_bench, NULL);
    pthread_create(&t4, NULL, spinlock_bench, NULL);
    pthread_join(t1, NULL); pthread_join(t2, NULL);
    pthread_join(t3, NULL); pthread_join(t4, NULL);
    clock_gettime(CLOCK_MONOTONIC, &end);
    long spin_ns = (end.tv_sec - start.tv_sec) * 1e9 + (end.tv_nsec - start.tv_nsec);

    printf("Spinlock: counter=%ld, time=%ldms\n",
           counter_spin, spin_ns / 1000000);

    // Mutex benchmark
    clock_gettime(CLOCK_MONOTONIC, &start);
    pthread_create(&t1, NULL, mutex_bench, NULL);
    pthread_create(&t2, NULL, mutex_bench, NULL);
    pthread_create(&t3, NULL, mutex_bench, NULL);
    pthread_create(&t4, NULL, mutex_bench, NULL);
    pthread_join(t1, NULL); pthread_join(t2, NULL);
    pthread_join(t3, NULL); pthread_join(t4, NULL);
    clock_gettime(CLOCK_MONOTONIC, &end);
    long mutex_ns = (end.tv_sec - start.tv_sec) * 1e9 + (end.tv_nsec - start.tv_nsec);

    printf("Mutex: counter=%ld, time=%ldms\n",
           counter_mutex, mutex_ns / 1000000);

    return 0;
}
```

## 7.5 Rust Implementation: Spinlock

```rust
use std::cell::UnsafeCell;
use std::ops::{Deref, DerefMut};
use std::sync::atomic::{AtomicBool, Ordering};
use std::hint;

// ============================================================
// SECTION: Production-quality Spinlock with Guard pattern
// Mirrors Rust's Mutex<T>: data is INSIDE the lock
// ============================================================

pub struct SpinLock<T> {
    locked: AtomicBool,
    data:   UnsafeCell<T>, // Interior mutability — T is inside
}

// SpinLock<T> is Send+Sync only if T is Send
// (Safe to send across threads, safe to share reference)
unsafe impl<T: Send> Send for SpinLock<T> {}
unsafe impl<T: Send> Sync for SpinLock<T> {}

pub struct SpinGuard<'a, T> {
    lock: &'a SpinLock<T>,
}

impl<T> SpinLock<T> {
    pub const fn new(value: T) -> Self {
        SpinLock {
            locked: AtomicBool::new(false),
            data:   UnsafeCell::new(value),
        }
    }

    pub fn lock(&self) -> SpinGuard<T> {
        // Two-phase spin: try CAS, if fail spin on load first
        loop {
            // Try to grab the lock
            if self.locked
                .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_ok()
            {
                break;
            }
            // Spin while locked, reading with Relaxed (stays in cache)
            while self.locked.load(Ordering::Relaxed) {
                hint::spin_loop(); // emits PAUSE on x86
            }
        }
        SpinGuard { lock: self }
    }

    pub fn try_lock(&self) -> Option<SpinGuard<T>> {
        self.locked
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .ok()
            .map(|_| SpinGuard { lock: self })
    }
}

impl<T> Deref for SpinGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: We hold the lock; no other thread can access data
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for SpinGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for SpinGuard<'_, T> {
    fn drop(&mut self) {
        // Release ordering ensures all preceding writes are visible
        self.lock.locked.store(false, Ordering::Release);
    }
}

// ============================================================
// SECTION: Ticket Spinlock (Fair)
// ============================================================

use std::sync::atomic::AtomicU32;

pub struct TicketLock<T> {
    next_ticket:  AtomicU32,
    now_serving:  AtomicU32,
    data:         UnsafeCell<T>,
}

unsafe impl<T: Send> Send for TicketLock<T> {}
unsafe impl<T: Send> Sync for TicketLock<T> {}

pub struct TicketGuard<'a, T> {
    lock: &'a TicketLock<T>,
}

impl<T> TicketLock<T> {
    pub fn new(value: T) -> Self {
        TicketLock {
            next_ticket: AtomicU32::new(0),
            now_serving: AtomicU32::new(0),
            data:        UnsafeCell::new(value),
        }
    }

    pub fn lock(&self) -> TicketGuard<T> {
        let my_ticket = self.next_ticket.fetch_add(1, Ordering::Relaxed);
        while self.now_serving.load(Ordering::Acquire) != my_ticket {
            hint::spin_loop();
        }
        TicketGuard { lock: self }
    }
}

impl<T> Deref for TicketGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T { unsafe { &*self.lock.data.get() } }
}

impl<T> DerefMut for TicketGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T { unsafe { &mut *self.lock.data.get() } }
}

impl<T> Drop for TicketGuard<'_, T> {
    fn drop(&mut self) {
        self.lock.now_serving.fetch_add(1, Ordering::Release);
    }
}

fn main() {
    use std::sync::Arc;
    use std::thread;

    let lock = Arc::new(SpinLock::new(0i64));
    let mut handles = vec![];

    for _ in 0..4 {
        let l = Arc::clone(&lock);
        handles.push(thread::spawn(move || {
            for _ in 0..100_000 {
                let mut guard = l.lock();
                *guard += 1;
                // guard drops here, lock released
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    println!("Counter: {}", *lock.lock()); // 400000
}
```

---

# 8. READ-WRITE LOCKS (RWLOCK) {#8-rwlock}

## 8.1 The Readers-Writers Problem

In many applications, reads are much more common than writes. A plain mutex allows only one thread at a time — even readers block each other unnecessarily.

**RWLock** (Read-Write Lock) distinguishes between:
- **Readers**: Multiple readers CAN access the data simultaneously (no writes happening)
- **Writers**: A writer needs EXCLUSIVE access (no readers, no other writers)

```
Valid states:
  UNLOCKED:        0 readers, 0 writers
  READ_LOCKED:     N readers (N ≥ 1), 0 writers
  WRITE_LOCKED:    0 readers, 1 writer

Transition rules:
  UNLOCKED → READ_LOCKED:   always allowed
  READ_LOCKED → READ_LOCKED: another reader can join
  UNLOCKED → WRITE_LOCKED:  always allowed
  READ_LOCKED → WRITE_LOCKED: MUST WAIT for all readers to leave
  WRITE_LOCKED → anything:  MUST WAIT for writer to finish
```

## 8.2 RWLock State Machine

```
             read_lock()            read_unlock() (last reader)
UNLOCKED ─────────────→ READ_LOCKED ──────────────────────────→ UNLOCKED
    │                       │   ↑                                    │
    │                       │   └─ read_lock() (more readers)        │
    │                       │                                        │
    │    write_lock()        │ write_lock()                          │
    └───────────────→ WRITE_LOCKED                                    │
                            │                                        │
                            └── write_unlock() ──────────────────────┘
```

## 8.3 Writer Starvation Problem

Naive RWLock implementations can **starve writers**: if readers keep arriving, a waiting writer never gets access because there's always a reader holding the lock.

**Solution strategies**:
1. **Writer preference**: Once a writer is waiting, new readers are blocked
2. **Fair queuing**: FIFO ordering for all lock requests
3. **Reader preference**: Readers have priority (can starve writers — bad for write-heavy)

## 8.4 C Implementation: RWLock

```c
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>

// ============================================================
// SECTION: POSIX RWLock
// ============================================================

typedef struct {
    pthread_rwlock_t rwlock;
    int data;
} shared_resource_t;

void resource_init(shared_resource_t* r, int initial) {
    pthread_rwlockattr_t attr;
    pthread_rwlockattr_init(&attr);
    // PREFER_WRITER_NONRECURSIVE: writers preferred, prevents writer starvation
    pthread_rwlockattr_setkind_np(&attr, PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP);
    pthread_rwlock_init(&r->rwlock, &attr);
    pthread_rwlockattr_destroy(&attr);
    r->data = initial;
}

int resource_read(shared_resource_t* r) {
    pthread_rwlock_rdlock(&r->rwlock);   // Shared read lock
    int val = r->data;                    // Multiple readers can be here
    pthread_rwlock_unlock(&r->rwlock);
    return val;
}

void resource_write(shared_resource_t* r, int value) {
    pthread_rwlock_wrlock(&r->rwlock);   // Exclusive write lock
    r->data = value;                      // Only one writer
    pthread_rwlock_unlock(&r->rwlock);
}

// ============================================================
// SECTION: Manual RWLock implementation (instructional)
// Uses a counter: >0 = N readers, -1 = writer
// ============================================================

typedef struct {
    pthread_mutex_t   mutex;      // protects the state
    pthread_cond_t    readers_ok; // signal: reading is now OK
    pthread_cond_t    writer_ok;  // signal: writing is now OK
    int               readers;    // number of active readers
    int               writers;    // number of active writers (0 or 1)
    int               write_waiters; // writers waiting (for fairness)
} manual_rwlock_t;

void manual_rwlock_init(manual_rwlock_t* rw) {
    pthread_mutex_init(&rw->mutex, NULL);
    pthread_cond_init(&rw->readers_ok, NULL);
    pthread_cond_init(&rw->writer_ok, NULL);
    rw->readers = rw->writers = rw->write_waiters = 0;
}

void manual_read_lock(manual_rwlock_t* rw) {
    pthread_mutex_lock(&rw->mutex);
    // Wait if a writer is active OR writers are waiting (prevent starvation)
    while (rw->writers > 0 || rw->write_waiters > 0) {
        pthread_cond_wait(&rw->readers_ok, &rw->mutex);
    }
    rw->readers++;
    pthread_mutex_unlock(&rw->mutex);
}

void manual_read_unlock(manual_rwlock_t* rw) {
    pthread_mutex_lock(&rw->mutex);
    rw->readers--;
    if (rw->readers == 0) {
        pthread_cond_signal(&rw->writer_ok); // last reader — wake a writer
    }
    pthread_mutex_unlock(&rw->mutex);
}

void manual_write_lock(manual_rwlock_t* rw) {
    pthread_mutex_lock(&rw->mutex);
    rw->write_waiters++;
    while (rw->readers > 0 || rw->writers > 0) {
        pthread_cond_wait(&rw->writer_ok, &rw->mutex);
    }
    rw->write_waiters--;
    rw->writers++;
    pthread_mutex_unlock(&rw->mutex);
}

void manual_write_unlock(manual_rwlock_t* rw) {
    pthread_mutex_lock(&rw->mutex);
    rw->writers--;
    if (rw->write_waiters > 0) {
        pthread_cond_signal(&rw->writer_ok); // wake another writer
    } else {
        pthread_cond_broadcast(&rw->readers_ok); // wake all readers
    }
    pthread_mutex_unlock(&rw->mutex);
}
```

## 8.5 Rust Implementation: RwLock

```rust
use std::sync::{Arc, RwLock};
use std::thread;

fn demo_rwlock() {
    // RwLock<T>: multiple readers OR one writer
    let data = Arc::new(RwLock::new(vec![1, 2, 3, 4, 5]));
    let mut handles = vec![];

    // Spawn 5 reader threads
    for i in 0..5 {
        let d = Arc::clone(&data);
        handles.push(thread::spawn(move || {
            // read() returns RwLockReadGuard — multiple can coexist
            let guard = d.read().unwrap();
            println!("Reader {}: {:?}", i, *guard);
            // Many readers can be here simultaneously
        }));
    }

    // Spawn 2 writer threads
    for i in 0..2 {
        let d = Arc::clone(&data);
        handles.push(thread::spawn(move || {
            // write() returns RwLockWriteGuard — exclusive
            let mut guard = d.write().unwrap();
            guard.push(10 + i);
            println!("Writer {} added element", i);
        }));
    }

    for h in handles { h.join().unwrap(); }

    println!("Final: {:?}", *data.read().unwrap());
}

// ============================================================
// SECTION: Custom Phase-fair RWLock (prevents starvation)
// Uses atomic state: bits encode readers + writer-waiting flag
// ============================================================

use std::sync::atomic::{AtomicU32, Ordering};

const WRITER_BIT:    u32 = 1 << 31; // highest bit = writer active
const WAITING_BIT:  u32 = 1 << 30; // second bit = writer waiting
const READER_MASK:  u32 = (1 << 30) - 1; // lower 30 bits = reader count

pub struct PhaseFairRwLock<T> {
    state: AtomicU32,
    data:  std::cell::UnsafeCell<T>,
}

unsafe impl<T: Send> Send for PhaseFairRwLock<T> {}
unsafe impl<T: Send> Sync for PhaseFairRwLock<T> {}

impl<T> PhaseFairRwLock<T> {
    pub fn new(val: T) -> Self {
        PhaseFairRwLock {
            state: AtomicU32::new(0),
            data:  std::cell::UnsafeCell::new(val),
        }
    }

    pub fn read(&self) -> &T {
        loop {
            let s = self.state.load(Ordering::Relaxed);
            // Only proceed if no writer active or waiting
            if s & (WRITER_BIT | WAITING_BIT) == 0 {
                let new_s = s + 1;
                if self.state.compare_exchange_weak(
                    s, new_s, Ordering::Acquire, Ordering::Relaxed
                ).is_ok() {
                    break;
                }
            } else {
                std::hint::spin_loop();
            }
        }
        unsafe { &*self.data.get() }
    }

    pub fn read_unlock(&self) {
        self.state.fetch_sub(1, Ordering::Release);
    }

    pub fn write(&self) -> &mut T {
        // Signal waiting
        self.state.fetch_or(WAITING_BIT, Ordering::Relaxed);
        loop {
            let s = self.state.load(Ordering::Relaxed);
            // Wait until no readers AND no current writer
            if s & (READER_MASK | WRITER_BIT) == WAITING_BIT {
                if self.state.compare_exchange_weak(
                    s, WRITER_BIT, Ordering::Acquire, Ordering::Relaxed
                ).is_ok() {
                    break;
                }
            } else {
                std::hint::spin_loop();
            }
        }
        unsafe { &mut *self.data.get() }
    }

    pub fn write_unlock(&self) {
        self.state.fetch_and(!WRITER_BIT, Ordering::Release);
    }
}

fn main() {
    demo_rwlock();
}
```

---

# 9. SEMAPHORES {#9-semaphores}

## 9.1 What is a Semaphore?

A **semaphore** is a synchronization primitive invented by Edsger Dijkstra. It is an integer counter with two atomic operations:

- **P (wait / down / acquire)**: Decrement the counter. If counter would go below 0, block until it becomes positive again.
- **V (signal / up / release)**: Increment the counter. If any thread is blocked on P, wake one.

```
Semaphore has:
    count:  integer (initially N)

P(sem):
    atomic {
        if (count > 0):
            count--
            return  // acquired
        else:
            block() // sleep until count > 0
    }

V(sem):
    atomic {
        count++
        if (any threads blocked):
            wake one of them
    }
```

## 9.2 Types of Semaphores

**Binary Semaphore** (count = 0 or 1):
- Equivalent in behavior to a mutex
- Unlike a mutex, can be released by a *different* thread (no ownership)

**Counting Semaphore** (count = N):
- Allows up to N threads to enter the "section" simultaneously
- Perfect for resource pools (N connections, N slots)

## 9.3 Semaphore vs Mutex

```
Feature              Mutex           Semaphore
────────────────────────────────────────────────────────
Ownership            Yes (owner)     No ownership concept
Initial value        Always 1        Any non-negative int
Release by other     Not allowed     Allowed
Primary use          Mutual exclusion Signaling / counting
Can count > 1        No              Yes
Recursive lock       Variant exists  Not applicable
```

**KEY INSIGHT**: A semaphore is primarily a **signaling** mechanism, while a mutex is a **mutual exclusion** mechanism. Confusing them leads to subtle bugs.

## 9.4 C Implementation: Semaphores

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>
#include <unistd.h>

// ============================================================
// SECTION: POSIX Semaphores — sem_t
// Two types:
//   1. Named:   sem_open("/name", ...) — visible across processes
//   2. Unnamed: sem_init(&sem, 0, N) — within one process (pshared=0)
// ============================================================

// EXAMPLE 1: Connection Pool — counting semaphore
#define POOL_SIZE 3

sem_t pool_semaphore;

void* connection_user(void* arg) {
    int id = *(int*)arg;
    printf("Thread %d: requesting connection...\n", id);

    sem_wait(&pool_semaphore); // P: acquire one slot
    printf("Thread %d: got connection, working...\n", id);
    sleep(1); // simulate work
    printf("Thread %d: releasing connection\n", id);
    sem_post(&pool_semaphore); // V: release one slot

    return NULL;
}

void demo_connection_pool(void) {
    sem_init(&pool_semaphore, 0, POOL_SIZE); // initially 3 connections available

    pthread_t threads[7];
    int ids[7];
    for (int i = 0; i < 7; i++) {
        ids[i] = i;
        pthread_create(&threads[i], NULL, connection_user, &ids[i]);
    }
    for (int i = 0; i < 7; i++)
        pthread_join(threads[i], NULL);

    sem_destroy(&pool_semaphore);
}

// EXAMPLE 2: Producer-Consumer with bounded buffer
#define BUFFER_SIZE 5

int buffer[BUFFER_SIZE];
int buf_read_idx  = 0;
int buf_write_idx = 0;

sem_t empty_slots; // how many empty slots (start = BUFFER_SIZE)
sem_t full_slots;  // how many full slots (start = 0)
pthread_mutex_t buf_mutex = PTHREAD_MUTEX_INITIALIZER;

void* producer(void* arg) {
    for (int i = 0; i < 10; i++) {
        int item = i * 10;

        sem_wait(&empty_slots);    // wait for an empty slot
        pthread_mutex_lock(&buf_mutex);

        buffer[buf_write_idx] = item;
        buf_write_idx = (buf_write_idx + 1) % BUFFER_SIZE;
        printf("Produced: %d\n", item);

        pthread_mutex_unlock(&buf_mutex);
        sem_post(&full_slots);     // signal: one more full slot
    }
    return NULL;
}

void* consumer(void* arg) {
    for (int i = 0; i < 10; i++) {
        sem_wait(&full_slots);     // wait for a full slot
        pthread_mutex_lock(&buf_mutex);

        int item = buffer[buf_read_idx];
        buf_read_idx = (buf_read_idx + 1) % BUFFER_SIZE;
        printf("Consumed: %d\n", item);

        pthread_mutex_unlock(&buf_mutex);
        sem_post(&empty_slots);    // signal: one more empty slot
    }
    return NULL;
}

void demo_producer_consumer(void) {
    sem_init(&empty_slots, 0, BUFFER_SIZE); // initially all slots empty
    sem_init(&full_slots, 0, 0);            // initially no full slots

    pthread_t prod, cons;
    pthread_create(&prod, NULL, producer, NULL);
    pthread_create(&cons, NULL, consumer, NULL);
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);

    sem_destroy(&empty_slots);
    sem_destroy(&full_slots);
}

// EXAMPLE 3: Thread synchronization (start-gun pattern)
sem_t start_gun;

void* racer(void* arg) {
    int id = *(int*)arg;
    printf("Racer %d: ready at starting line\n", id);
    sem_wait(&start_gun); // all threads wait here
    printf("Racer %d: GO!\n", id);
    return NULL;
}

void demo_start_gun(void) {
    sem_init(&start_gun, 0, 0); // initially 0 — all will block

    const int N = 5;
    pthread_t threads[5];
    int ids[5];
    for (int i = 0; i < N; i++) {
        ids[i] = i;
        pthread_create(&threads[i], NULL, racer, &ids[i]);
    }

    sleep(1); // let all threads reach the barrier
    printf("Starting all racers!\n");

    // Post N times to release all N waiting threads
    for (int i = 0; i < N; i++)
        sem_post(&start_gun);

    for (int i = 0; i < N; i++)
        pthread_join(threads[i], NULL);

    sem_destroy(&start_gun);
}

int main(void) {
    demo_connection_pool();
    demo_producer_consumer();
    demo_start_gun();
    return 0;
}
```

## 9.5 Go Implementation: Semaphores

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// ============================================================
// Go has no built-in semaphore, but we build one with channels.
// A buffered channel of capacity N acts as a counting semaphore.
// ============================================================

type Semaphore struct {
    ch chan struct{}
}

func NewSemaphore(n int) *Semaphore {
    return &Semaphore{ch: make(chan struct{}, n)}
}

// Acquire (P): blocks if no capacity
func (s *Semaphore) Acquire() {
    s.ch <- struct{}{}
}

// TryAcquire: non-blocking
func (s *Semaphore) TryAcquire() bool {
    select {
    case s.ch <- struct{}{}:
        return true
    default:
        return false
    }
}

// Release (V): never blocks
func (s *Semaphore) Release() {
    <-s.ch
}

// ============================================================
// SECTION: Connection Pool using Semaphore
// ============================================================

type ConnectionPool struct {
    sem  *Semaphore
    mu   sync.Mutex
    conns []string // available connections
}

func NewConnectionPool(n int) *ConnectionPool {
    conns := make([]string, n)
    for i := range conns {
        conns[i] = fmt.Sprintf("conn-%d", i)
    }
    return &ConnectionPool{
        sem:   NewSemaphore(n),
        conns: conns,
    }
}

func (p *ConnectionPool) Get() string {
    p.sem.Acquire() // block if no connections available
    p.mu.Lock()
    defer p.mu.Unlock()
    conn := p.conns[len(p.conns)-1]
    p.conns = p.conns[:len(p.conns)-1]
    return conn
}

func (p *ConnectionPool) Put(conn string) {
    p.mu.Lock()
    p.conns = append(p.conns, conn)
    p.mu.Unlock()
    p.sem.Release() // signal: one more available
}

// ============================================================
// SECTION: Producer-Consumer with buffered channel
// Go's channels ARE the producer-consumer primitive!
// ============================================================

func demoProducerConsumer() {
    buffer := make(chan int, 5) // buffered channel = bounded buffer

    var wg sync.WaitGroup

    // Producer
    wg.Add(1)
    go func() {
        defer wg.Done()
        defer close(buffer)
        for i := 0; i < 10; i++ {
            buffer <- i * 10 // blocks if buffer full
            fmt.Printf("Produced: %d\n", i*10)
        }
    }()

    // Consumer
    wg.Add(1)
    go func() {
        defer wg.Done()
        for item := range buffer { // blocks if buffer empty
            fmt.Printf("Consumed: %d\n", item)
            time.Sleep(50 * time.Millisecond)
        }
    }()

    wg.Wait()
}

func main() {
    pool := NewConnectionPool(3)
    var wg sync.WaitGroup
    for i := 0; i < 7; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            conn := pool.Get()
            fmt.Printf("Worker %d using %s\n", id, conn)
            time.Sleep(100 * time.Millisecond)
            pool.Put(conn)
        }(i)
    }
    wg.Wait()

    demoProducerConsumer()
}
```

---

# 10. CONDITION VARIABLES {#10-condition-variables}

## 10.1 What is a Condition Variable?

A **condition variable** is a synchronization primitive that allows threads to wait for a specific **condition** to become true, without busy-waiting. It is always used together with a mutex.

**The pattern**:
```
Thread A (waiter):
    mutex.lock()
    while (condition is NOT true):
        cond.wait(mutex)    // atomically: releases mutex AND sleeps
    // Now condition IS true
    do work
    mutex.unlock()

Thread B (notifier):
    mutex.lock()
    make condition true
    cond.signal()   // wake one waiter
    mutex.unlock()
```

## 10.2 Why Always Use a While Loop?

Critical: always use `while`, never `if`, when checking the condition after `wait()`.

Reasons:
1. **Spurious wakeups**: The OS can wake a thread for no reason. You must recheck the condition.
2. **Multiple waiters**: When `broadcast()` is called, all waiters wake. By the time a particular thread runs, another might have already consumed the resource.
3. **Lost wakeups without mutex**: The signal could come between the condition check and the wait call, causing the wait to sleep forever.

```
ALWAYS:                      NEVER:
while (!condition)           if (!condition)      ← BUG!
    cond.wait(mutex);            cond.wait(mutex);
do work                      do work
```

## 10.3 Signal vs Broadcast

- `signal()` / `notify_one()`: Wake **one** waiting thread (usually the one waiting longest)
- `broadcast()` / `notify_all()`: Wake **all** waiting threads

Use `signal` when: exactly one thread can make progress.
Use `broadcast` when: multiple threads might be able to make progress, or the condition change affects multiple waiters.

## 10.4 C Implementation: Condition Variables

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdbool.h>
#include <time.h>

// ============================================================
// SECTION: Classic Bounded Buffer (Producer-Consumer)
// This is the CANONICAL use of condition variables
// ============================================================

#define BUFFER_CAPACITY 5

typedef struct {
    int  data[BUFFER_CAPACITY];
    int  count;      // current items in buffer
    int  head;       // next read index
    int  tail;       // next write index

    pthread_mutex_t lock;
    pthread_cond_t  not_full;   // signaled when buffer is not full
    pthread_cond_t  not_empty;  // signaled when buffer is not empty
} bounded_buffer_t;

void bb_init(bounded_buffer_t* bb) {
    bb->count = bb->head = bb->tail = 0;
    pthread_mutex_init(&bb->lock, NULL);
    pthread_cond_init(&bb->not_full,  NULL);
    pthread_cond_init(&bb->not_empty, NULL);
}

void bb_put(bounded_buffer_t* bb, int item) {
    pthread_mutex_lock(&bb->lock);

    // WHILE loop — not if — handles spurious wakeups
    while (bb->count == BUFFER_CAPACITY) {
        // Buffer is full — wait for a consumer to take an item
        // cond_wait ATOMICALLY: releases lock AND sleeps
        // When woken: REACQUIRES lock before returning
        pthread_cond_wait(&bb->not_full, &bb->lock);
    }

    bb->data[bb->tail] = item;
    bb->tail = (bb->tail + 1) % BUFFER_CAPACITY;
    bb->count++;

    // Signal a waiting consumer that data is available
    pthread_cond_signal(&bb->not_empty);

    pthread_mutex_unlock(&bb->lock);
}

int bb_get(bounded_buffer_t* bb) {
    pthread_mutex_lock(&bb->lock);

    while (bb->count == 0) {
        // Buffer empty — wait for producer to add an item
        pthread_cond_wait(&bb->not_empty, &bb->lock);
    }

    int item = bb->data[bb->head];
    bb->head = (bb->head + 1) % BUFFER_CAPACITY;
    bb->count--;

    pthread_cond_signal(&bb->not_full);

    pthread_mutex_unlock(&bb->lock);
    return item;
}

// ============================================================
// SECTION: Thread Pool using condition variables
// ============================================================

#define MAX_TASKS 64
#define NUM_WORKERS 4

typedef void (*task_fn)(void*);

typedef struct {
    task_fn fn;
    void*   arg;
} task_t;

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t  task_available;
    pthread_cond_t  all_done;

    task_t   queue[MAX_TASKS];
    int      head, tail, count;
    int      active_tasks;  // tasks currently being processed
    bool     shutdown;

    pthread_t workers[NUM_WORKERS];
} thread_pool_t;

void* worker_thread(void* arg) {
    thread_pool_t* pool = (thread_pool_t*)arg;

    while (true) {
        pthread_mutex_lock(&pool->lock);

        // Wait until there's a task or shutdown is requested
        while (pool->count == 0 && !pool->shutdown) {
            pthread_cond_wait(&pool->task_available, &pool->lock);
        }

        if (pool->shutdown && pool->count == 0) {
            pthread_mutex_unlock(&pool->lock);
            break;
        }

        // Dequeue a task
        task_t task = pool->queue[pool->head];
        pool->head = (pool->head + 1) % MAX_TASKS;
        pool->count--;
        pool->active_tasks++;

        pthread_mutex_unlock(&pool->lock);

        // Execute task WITHOUT holding the lock
        task.fn(task.arg);

        pthread_mutex_lock(&pool->lock);
        pool->active_tasks--;
        if (pool->count == 0 && pool->active_tasks == 0) {
            pthread_cond_broadcast(&pool->all_done); // all tasks complete
        }
        pthread_mutex_unlock(&pool->lock);
    }

    return NULL;
}

void pool_init(thread_pool_t* pool) {
    pthread_mutex_init(&pool->lock, NULL);
    pthread_cond_init(&pool->task_available, NULL);
    pthread_cond_init(&pool->all_done, NULL);
    pool->head = pool->tail = pool->count = pool->active_tasks = 0;
    pool->shutdown = false;

    for (int i = 0; i < NUM_WORKERS; i++)
        pthread_create(&pool->workers[i], NULL, worker_thread, pool);
}

void pool_submit(thread_pool_t* pool, task_fn fn, void* arg) {
    pthread_mutex_lock(&pool->lock);

    pool->queue[pool->tail] = (task_t){fn, arg};
    pool->tail = (pool->tail + 1) % MAX_TASKS;
    pool->count++;

    pthread_cond_signal(&pool->task_available); // wake one worker
    pthread_mutex_unlock(&pool->lock);
}

void pool_wait(thread_pool_t* pool) {
    pthread_mutex_lock(&pool->lock);
    while (pool->count > 0 || pool->active_tasks > 0) {
        pthread_cond_wait(&pool->all_done, &pool->lock);
    }
    pthread_mutex_unlock(&pool->lock);
}

void pool_shutdown(thread_pool_t* pool) {
    pthread_mutex_lock(&pool->lock);
    pool->shutdown = true;
    pthread_cond_broadcast(&pool->task_available); // wake all workers
    pthread_mutex_unlock(&pool->lock);
    for (int i = 0; i < NUM_WORKERS; i++)
        pthread_join(pool->workers[i], NULL);
}

// ============================================================
// SECTION: Timed condition wait
// ============================================================

bool bb_get_timed(bounded_buffer_t* bb, int* out, int timeout_ms) {
    struct timespec deadline;
    clock_gettime(CLOCK_REALTIME, &deadline);
    deadline.tv_nsec += (long)timeout_ms * 1000000;
    if (deadline.tv_nsec >= 1000000000L) {
        deadline.tv_sec++;
        deadline.tv_nsec -= 1000000000L;
    }

    pthread_mutex_lock(&bb->lock);
    while (bb->count == 0) {
        int rc = pthread_cond_timedwait(&bb->not_empty, &bb->lock, &deadline);
        if (rc == ETIMEDOUT) {
            pthread_mutex_unlock(&bb->lock);
            return false; // timed out
        }
    }
    *out = bb->data[bb->head];
    bb->head = (bb->head + 1) % BUFFER_CAPACITY;
    bb->count--;
    pthread_cond_signal(&bb->not_full);
    pthread_mutex_unlock(&bb->lock);
    return true;
}
```

## 10.5 Rust Implementation: Condvar

```rust
use std::sync::{Arc, Mutex, Condvar};
use std::thread;
use std::collections::VecDeque;
use std::time::Duration;

// ============================================================
// SECTION: Rust Condvar — always paired with Mutex
// Rust's Condvar::wait() takes a MutexGuard and releases+sleeps
// ============================================================

struct BoundedBuffer<T> {
    data:     Mutex<VecDeque<T>>,
    not_full: Condvar,
    not_empty: Condvar,
    capacity: usize,
}

impl<T> BoundedBuffer<T> {
    fn new(capacity: usize) -> Self {
        BoundedBuffer {
            data:      Mutex::new(VecDeque::with_capacity(capacity)),
            not_full:  Condvar::new(),
            not_empty: Condvar::new(),
            capacity,
        }
    }

    fn put(&self, item: T) {
        let mut guard = self.data.lock().unwrap();

        // WHILE loop — spurious wakeups and multiple waiters
        // Condvar::wait() atomically releases lock and sleeps
        // Returns new MutexGuard when woken
        while guard.len() == self.capacity {
            guard = self.not_full.wait(guard).unwrap();
        }

        guard.push_back(item);
        self.not_empty.notify_one();
        // guard drops here → lock released
    }

    fn get(&self) -> T {
        let mut guard = self.data.lock().unwrap();

        while guard.is_empty() {
            guard = self.not_empty.wait(guard).unwrap();
        }

        let item = guard.pop_front().unwrap();
        self.not_full.notify_one();
        item
    }

    fn get_timeout(&self, dur: Duration) -> Option<T> {
        let mut guard = self.data.lock().unwrap();

        while guard.is_empty() {
            let result = self.not_empty.wait_timeout(guard, dur).unwrap();
            guard = result.0;
            if result.1.timed_out() {
                return None;
            }
        }

        let item = guard.pop_front().unwrap();
        self.not_full.notify_one();
        Some(item)
    }
}

fn demo_bounded_buffer() {
    let buf = Arc::new(BoundedBuffer::new(5));
    let mut handles = vec![];

    // Producer
    let b = Arc::clone(&buf);
    handles.push(thread::spawn(move || {
        for i in 0..20i32 {
            b.put(i);
            println!("Produced: {}", i);
        }
    }));

    // Consumer
    let b = Arc::clone(&buf);
    handles.push(thread::spawn(move || {
        for _ in 0..20 {
            let item = b.get();
            println!("Consumed: {}", item);
            thread::sleep(Duration::from_millis(10));
        }
    }));

    for h in handles { h.join().unwrap(); }
}

// ============================================================
// SECTION: Barrier using Condvar
// ============================================================

struct Barrier {
    mutex:   Mutex<(usize, usize)>, // (count, generation)
    condvar: Condvar,
    total:   usize,
}

impl Barrier {
    fn new(n: usize) -> Self {
        Barrier {
            mutex:   Mutex::new((0, 0)),
            condvar: Condvar::new(),
            total:   n,
        }
    }

    fn wait(&self) {
        let mut guard = self.mutex.lock().unwrap();
        let gen = guard.1;
        guard.0 += 1;

        if guard.0 == self.total {
            // Last thread — advance generation and wake all
            guard.0 = 0;
            guard.1 += 1;
            self.condvar.notify_all();
        } else {
            // Wait for the last thread, but guard against spurious wakeups
            // using the generation counter
            while guard.1 == gen {
                guard = self.condvar.wait(guard).unwrap();
            }
        }
    }
}

fn main() {
    demo_bounded_buffer();
}
```

## 10.6 Go Implementation: sync.Cond

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// ============================================================
// SECTION: Bounded Buffer using sync.Cond
// ============================================================

type BoundedBuffer struct {
    mu       sync.Mutex
    notFull  *sync.Cond
    notEmpty *sync.Cond
    buf      []int
    head, tail, count, cap int
}

func NewBoundedBuffer(capacity int) *BoundedBuffer {
    bb := &BoundedBuffer{
        buf: make([]int, capacity),
        cap: capacity,
    }
    bb.notFull  = sync.NewCond(&bb.mu)
    bb.notEmpty = sync.NewCond(&bb.mu)
    return bb
}

func (bb *BoundedBuffer) Put(item int) {
    bb.mu.Lock()
    for bb.count == bb.cap {
        bb.notFull.Wait() // release lock, sleep, reacquire lock on wake
    }
    bb.buf[bb.tail] = item
    bb.tail = (bb.tail + 1) % bb.cap
    bb.count++
    bb.notEmpty.Signal()
    bb.mu.Unlock()
}

func (bb *BoundedBuffer) Get() int {
    bb.mu.Lock()
    for bb.count == 0 {
        bb.notEmpty.Wait()
    }
    item := bb.buf[bb.head]
    bb.head = (bb.head + 1) % bb.cap
    bb.count--
    bb.notFull.Signal()
    bb.mu.Unlock()
    return item
}

// ============================================================
// Note: In idiomatic Go, channels are preferred over sync.Cond
// for producer-consumer. sync.Cond is mainly useful when you
// need to broadcast to all waiters or have complex conditions.
// ============================================================

// Idiomatic Go: channels for producer-consumer
func idiomaticProducerConsumer() {
    ch := make(chan int, 5)
    var wg sync.WaitGroup

    wg.Add(1)
    go func() {
        defer wg.Done()
        defer close(ch)
        for i := 0; i < 20; i++ {
            ch <- i
        }
    }()

    wg.Add(1)
    go func() {
        defer wg.Done()
        for v := range ch {
            fmt.Println("Got:", v)
            time.Sleep(10 * time.Millisecond)
        }
    }()

    wg.Wait()
}

func main() {
    bb := NewBoundedBuffer(5)
    var wg sync.WaitGroup

    wg.Add(1)
    go func() {
        defer wg.Done()
        for i := 0; i < 10; i++ {
            bb.Put(i * 10)
        }
    }()

    wg.Add(1)
    go func() {
        defer wg.Done()
        for i := 0; i < 10; i++ {
            v := bb.Get()
            fmt.Println("Got:", v)
        }
    }()

    wg.Wait()
}
```

---

# 11. MONITORS {#11-monitors}

## 11.1 What is a Monitor?

A **monitor** is a high-level synchronization construct that combines:
1. A **mutex** (for mutual exclusion)
2. One or more **condition variables** (for waiting/signaling)
3. The **data** being protected

The key insight: the mutex and data are **encapsulated together**. You cannot touch the data without automatically acquiring the lock. This prevents forgetting to acquire the lock.

**Java's `synchronized` blocks are monitors.** In C, Go, and Rust, you build them manually.

```
Monitor = {
    mutex M
    condition variables C1, C2, ...
    shared data D

    procedure f1():
        lock M
        while (!condition1): wait(C1, M)
        modify D
        signal(C2)
        unlock M

    procedure f2():
        lock M
        while (!condition2): wait(C2, M)
        modify D
        signal(C1)
        unlock M
}
```

## 11.2 Monitor Pattern in Rust (Idiomatic)

Rust's `Mutex<T>` IS a monitor — the data T is inside the Mutex, and you cannot access T without the guard.

```rust
use std::sync::{Arc, Mutex, Condvar};
use std::collections::VecDeque;

// A complete monitor: mutex + condvar + data all encapsulated
pub struct Monitor<T> {
    inner: Arc<MonitorInner<T>>,
}

struct MonitorInner<T> {
    data: Mutex<T>,
    cond: Condvar,
}

impl<T> Monitor<T> {
    pub fn new(data: T) -> Self {
        Monitor {
            inner: Arc::new(MonitorInner {
                data: Mutex::new(data),
                cond: Condvar::new(),
            }),
        }
    }

    // Execute a closure while holding the lock
    pub fn with<F, R>(&self, f: F) -> R
    where F: FnOnce(&mut T) -> R {
        let mut guard = self.inner.data.lock().unwrap();
        f(&mut *guard)
    }

    // Wait until predicate is true, then execute closure
    pub fn wait_until<P, F, R>(&self, mut pred: P, f: F) -> R
    where
        P: FnMut(&T) -> bool,
        F: FnOnce(&mut T) -> R,
    {
        let mut guard = self.inner.data.lock().unwrap();
        while !pred(&*guard) {
            guard = self.inner.cond.wait(guard).unwrap();
        }
        f(&mut *guard)
    }

    pub fn notify_one(&self) { self.inner.cond.notify_one(); }
    pub fn notify_all(&self) { self.inner.cond.notify_all(); }

    pub fn clone(&self) -> Self {
        Monitor { inner: Arc::clone(&self.inner) }
    }
}
```

---

# 12. BARRIERS & FENCES {#12-barriers}

## 12.1 Thread Barrier (Synchronization Barrier)

A **thread barrier** is a synchronization point where all threads in a group must arrive before any can proceed. Like a "rendezvous point" in concurrent computation.

```
Thread 1: Phase1 ──────────────────────────→ ║ ──→ Phase2
Thread 2: Phase1 ──────────────────────────→ ║ ──→ Phase2
Thread 3: Phase1 ──────────────────────────→ ║ ──→ Phase2
Thread 4: Phase1 ──────────────────────────→ ║ ──→ Phase2
                                             ↑
                                         BARRIER
                            All must arrive before any can proceed
```

Used heavily in parallel computation (e.g., parallel matrix multiplication where all threads must complete phase 1 before any starts phase 2).

## 12.2 C Implementation: Barrier

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// ============================================================
// POSIX Barrier (pthread_barrier_t)
// ============================================================

void demo_posix_barrier(void) {
    const int NUM_THREADS = 4;
    pthread_barrier_t barrier;
    pthread_barrier_init(&barrier, NULL, NUM_THREADS);

    // Simulate parallel computation phases
    pthread_t threads[4];
    // ... create threads that call pthread_barrier_wait(&barrier)
    // The barrier_wait call blocks until all NUM_THREADS have called it

    pthread_barrier_destroy(&barrier);
}

// ============================================================
// Manual Barrier — Reusable (uses generation counter)
// ============================================================

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t  all_arrived;
    int             count;      // how many have arrived this phase
    int             total;      // how many need to arrive
    int             generation; // which phase we're in (prevents spurious wake)
} reusable_barrier_t;

void barrier_init(reusable_barrier_t* b, int total) {
    pthread_mutex_init(&b->lock, NULL);
    pthread_cond_init(&b->all_arrived, NULL);
    b->count = 0;
    b->total = total;
    b->generation = 0;
}

void barrier_wait(reusable_barrier_t* b) {
    pthread_mutex_lock(&b->lock);
    int my_gen = b->generation;

    b->count++;
    if (b->count == b->total) {
        // Last thread to arrive
        b->count = 0;            // reset for next use
        b->generation++;         // advance generation
        pthread_cond_broadcast(&b->all_arrived); // wake all
    } else {
        // Not last — wait until generation advances
        while (b->generation == my_gen) {
            pthread_cond_wait(&b->all_arrived, &b->lock);
        }
    }
    pthread_mutex_unlock(&b->lock);
}

// ============================================================
// SECTION: Memory Fence / Memory Barrier (hardware level)
// These are COMPILER and HARDWARE barriers, not thread barriers
// ============================================================

void demo_memory_fences(void) {
    int x = 0, y = 0;

    // Full memory barrier: no reads or writes can cross this point
    __sync_synchronize();          // GCC built-in full barrier
    __asm__ volatile ("" ::: "memory"); // compiler barrier only (no hw fence)

    // Specific fence types (x86):
    __asm__ volatile ("mfence" ::: "memory"); // full memory fence
    __asm__ volatile ("lfence" ::: "memory"); // load fence
    __asm__ volatile ("sfence" ::: "memory"); // store fence

    // C11 atomic fence:
    atomic_thread_fence(memory_order_seq_cst);
    atomic_thread_fence(memory_order_acquire);
    atomic_thread_fence(memory_order_release);
}
```

## 12.3 Rust: Barriers and Fences

```rust
use std::sync::{Arc, Barrier};
use std::thread;
use std::sync::atomic::{fence, Ordering};

fn demo_barrier() {
    let barrier = Arc::new(Barrier::new(4));
    let mut handles = vec![];

    for i in 0..4 {
        let b = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            // Phase 1: each thread does its work
            println!("Thread {}: Phase 1 done", i);

            b.wait(); // Block until all 4 threads reach this point

            // Phase 2: all threads guaranteed to have finished Phase 1
            println!("Thread {}: Phase 2 starting", i);
        }));
    }

    for h in handles { h.join().unwrap(); }
}

fn demo_atomic_fence() {
    use std::sync::atomic::AtomicI32;
    let data = AtomicI32::new(0);
    let flag = AtomicI32::new(0);

    // Writer thread:
    data.store(42, Ordering::Relaxed);
    fence(Ordering::Release); // All writes before fence are visible after acquire fence
    flag.store(1, Ordering::Relaxed);

    // Reader thread:
    while flag.load(Ordering::Relaxed) == 0 {}
    fence(Ordering::Acquire); // Pairs with release fence above
    let val = data.load(Ordering::Relaxed); // Guaranteed to see 42
    println!("val = {}", val);
}

fn main() {
    demo_barrier();
}
```

---

# 13. LOCK-FREE & WAIT-FREE PROGRAMMING {#13-lockfree}

## 13.1 Definitions

**Lock-free**: At least one thread makes progress in a finite number of steps, regardless of what other threads do. Other threads might starve temporarily, but the system as a whole never gets stuck.

**Wait-free**: EVERY thread makes progress in a finite number of steps. No thread can be indefinitely delayed. The strongest guarantee.

**Obstruction-free**: A thread makes progress if it runs alone (no interference).

```
Hierarchy (strongest → weakest):
    Wait-free ⊂ Lock-free ⊂ Obstruction-free ⊂ Deadlock-free

Wait-free:        Every thread finishes in bounded steps
Lock-free:        System always makes progress (some thread finishes)
Obstruction-free: Thread finishes if it runs in isolation
Deadlock-free:    System doesn't permanently stall (weaker than LF)
```

## 13.2 The ABA Problem

The most notorious hazard in lock-free programming.

```
Thread A: reads top = ptr_A (value = 10)
Thread B: runs and:
    - pops A (top → ptr_B)
    - pops B (top → NULL)
    - pushes A back (top → ptr_A) — SAME ADDRESS, possibly DIFFERENT value!
Thread A: CAS(top, ptr_A, new_node) SUCCEEDS because address matches
         But the stack structure has been changed! Data corruption.
```

**Solutions**:
1. **Tagged pointers**: Combine pointer + counter. ABA impossible because counter changes even if pointer repeats.
2. **Hazard pointers**: Before dereferencing a pointer, announce it as "hazardous" — prevent reclamation.
3. **RCU (Read-Copy-Update)**: Defer reclamation until all readers are done.
4. **Epoch-based reclamation**: Track "epochs" and only free memory when no thread is in the old epoch.

## 13.3 C Implementation: Tagged Pointer (ABA Prevention)

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdatomic.h>

// ============================================================
// SECTION: Tagged Pointer for ABA Prevention
// Uses 128-bit compare-and-swap (CMPXCHG16B on x86-64)
// ============================================================

typedef struct node {
    int value;
    struct node* next;
} node_t;

// A tagged pointer: pointer + version counter
typedef struct {
    node_t* ptr;
    uint64_t tag;
} tagged_ptr_t;

// _Atomic struct — 128-bit atomic on x86-64
typedef _Atomic(tagged_ptr_t) atomic_tagged_ptr_t;

// We need __int128 or GCC's __atomic builtins for 128-bit CAS
// This is platform-specific but works on x86-64

typedef struct {
    atomic_tagged_ptr_t top;
} tagged_stack_t;

void tagged_stack_init(tagged_stack_t* s) {
    tagged_ptr_t initial = {.ptr = NULL, .tag = 0};
    atomic_store(&s->top, initial);
}

void tagged_stack_push(tagged_stack_t* s, int value) {
    node_t* node = malloc(sizeof(node_t));
    node->value = value;

    tagged_ptr_t old_top, new_top;
    do {
        old_top = atomic_load(&s->top);
        node->next = old_top.ptr;
        new_top.ptr = node;
        new_top.tag = old_top.tag + 1; // increment tag on every operation
    } while (!atomic_compare_exchange_weak(&s->top, &old_top, new_top));
}

int tagged_stack_pop(tagged_stack_t* s, int* out) {
    tagged_ptr_t old_top, new_top;
    do {
        old_top = atomic_load(&s->top);
        if (old_top.ptr == NULL) return 0;
        new_top.ptr = old_top.ptr->next;
        new_top.tag = old_top.tag + 1; // tag change makes ABA detectable
    } while (!atomic_compare_exchange_weak(&s->top, &old_top, new_top));

    *out = old_top.ptr->value;
    free(old_top.ptr);
    return 1;
}

// ============================================================
// SECTION: Lock-Free Queue (Michael & Scott, 1996)
// One of the most famous lock-free algorithms
// Uses sentinel node (dummy head) to separate head and tail
// ============================================================

typedef struct ms_node {
    int value;
    _Atomic(struct ms_node*) next;
} ms_node_t;

typedef struct {
    _Atomic(ms_node_t*) head; // dequeue end
    _Atomic(ms_node_t*) tail; // enqueue end
} ms_queue_t;

void ms_queue_init(ms_queue_t* q) {
    ms_node_t* sentinel = calloc(1, sizeof(ms_node_t));
    atomic_store(&sentinel->next, NULL);
    atomic_store(&q->head, sentinel);
    atomic_store(&q->tail, sentinel);
}

void ms_queue_enqueue(ms_queue_t* q, int value) {
    ms_node_t* node = malloc(sizeof(ms_node_t));
    node->value = value;
    atomic_store(&node->next, NULL);

    ms_node_t* tail, *next;
    while (1) {
        tail = atomic_load(&q->tail);
        next = atomic_load(&tail->next);

        if (tail == atomic_load(&q->tail)) { // consistent read
            if (next == NULL) {
                // Tail is truly the last node — try to link new node
                ms_node_t* expected_null = NULL;
                if (atomic_compare_exchange_weak(&tail->next, &expected_null, node)) {
                    // Success! Swing tail to new node (best-effort)
                    atomic_compare_exchange_strong(&q->tail, &tail, node);
                    return;
                }
            } else {
                // Tail is lagging — help advance it
                atomic_compare_exchange_strong(&q->tail, &tail, next);
            }
        }
    }
}

int ms_queue_dequeue(ms_queue_t* q, int* out) {
    ms_node_t* head, *tail, *next;
    while (1) {
        head = atomic_load(&q->head);
        tail = atomic_load(&q->tail);
        next = atomic_load(&head->next);

        if (head == atomic_load(&q->head)) {
            if (head == tail) {
                if (next == NULL) return 0; // empty
                // Tail is lagging, help it advance
                atomic_compare_exchange_strong(&q->tail, &tail, next);
            } else {
                *out = next->value;
                if (atomic_compare_exchange_weak(&q->head, &head, next)) {
                    free(head); // free old sentinel
                    return 1;
                }
            }
        }
    }
}
```

---

# 14. CLASSIC SYNCHRONIZATION PROBLEMS {#14-classic-problems}

## 14.1 The Dining Philosophers Problem

**Setup**: 5 philosophers sit at a round table. Between each pair of philosophers is one fork. To eat, a philosopher needs BOTH forks (left and right). A philosopher who can't get both forks must wait.

**Problem**: Each philosopher grabs their left fork → everyone waits for their right fork → **DEADLOCK**.

```
        P0
       /  \
   Fork4    Fork0
    /          \
  P4            P1
   \            /
   Fork3    Fork1
     \        /
       P3--P2
          |
        Fork2
```

**Solutions**:

1. **Resource hierarchy** (Dijkstra): Number forks 0-4. Always pick up the lower-numbered fork first. Philosopher 4 picks up Fork0 before Fork4 — breaks the cycle.

2. **Chandy/Misra**: Use "dirty/clean" forks and message passing.

3. **Arbitrator**: A waiter grants permission — only 4 philosophers can hold a fork simultaneously (prevents deadlock by ensuring at least one can always complete).

```c
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

#define N 5

pthread_mutex_t forks[N];

// WRONG — Can deadlock
void* philosopher_wrong(void* arg) {
    int id = *(int*)arg;
    int left  = id;
    int right = (id + 1) % N;

    while (1) {
        printf("Philosopher %d thinking\n", id);
        sleep(1);
        pthread_mutex_lock(&forks[left]);   // ALL grab left
        pthread_mutex_lock(&forks[right]);  // ALL wait for right → DEADLOCK
        printf("Philosopher %d eating\n", id);
        sleep(1);
        pthread_mutex_unlock(&forks[right]);
        pthread_mutex_unlock(&forks[left]);
    }
    return NULL;
}

// CORRECT — Resource hierarchy (always pick lower-numbered fork first)
void* philosopher_correct(void* arg) {
    int id = *(int*)arg;
    int left  = id;
    int right = (id + 1) % N;
    // First fork = lower number, Second = higher number
    int first  = (left < right) ? left  : right;
    int second = (left < right) ? right : left;

    while (1) {
        printf("Philosopher %d thinking\n", id);
        sleep(1);
        pthread_mutex_lock(&forks[first]);
        pthread_mutex_lock(&forks[second]);
        printf("Philosopher %d eating\n", id);
        sleep(1);
        pthread_mutex_unlock(&forks[second]);
        pthread_mutex_unlock(&forks[first]);
    }
    return NULL;
}

// CORRECT — Chandy/Misra with semaphores (allow at most N-1 to try)
sem_t room_sem; // only N-1 philosophers can hold a fork simultaneously

void* philosopher_semaphore(void* arg) {
    int id = *(int*)arg;
    int left  = id;
    int right = (id + 1) % N;

    while (1) {
        sleep(1); // think
        sem_wait(&room_sem);           // enter "room" (max N-1)
        pthread_mutex_lock(&forks[left]);
        pthread_mutex_lock(&forks[right]);
        sleep(1); // eat
        pthread_mutex_unlock(&forks[right]);
        pthread_mutex_unlock(&forks[left]);
        sem_post(&room_sem);           // leave "room"
    }
    return NULL;
}
```

## 14.2 The Readers-Writers Problem (Complete Solution)

Three variants with different fairness properties:

```c
// VARIANT 1: Reader preference (writers can starve)
// VARIANT 2: Writer preference (readers can starve)
// VARIANT 3: Fair (FIFO ordering, no starvation)

// Variant 3 — Fair RWLock using a queue
typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t  ok_to_read;
    pthread_cond_t  ok_to_write;
    int  readers;         // active readers
    int  writers;         // active writers (0 or 1)
    int  waiting_readers;
    int  waiting_writers;
} fair_rwlock_t;

void fair_read_lock(fair_rwlock_t* rw) {
    pthread_mutex_lock(&rw->lock);
    rw->waiting_readers++;
    // Block if writer active OR writer waiting (writer preference to prevent starvation)
    while (rw->writers > 0 || rw->waiting_writers > 0) {
        pthread_cond_wait(&rw->ok_to_read, &rw->lock);
    }
    rw->waiting_readers--;
    rw->readers++;
    pthread_mutex_unlock(&rw->lock);
}

void fair_read_unlock(fair_rwlock_t* rw) {
    pthread_mutex_lock(&rw->lock);
    rw->readers--;
    if (rw->readers == 0 && rw->waiting_writers > 0) {
        pthread_cond_signal(&rw->ok_to_write);
    }
    pthread_mutex_unlock(&rw->lock);
}

void fair_write_lock(fair_rwlock_t* rw) {
    pthread_mutex_lock(&rw->lock);
    rw->waiting_writers++;
    while (rw->readers > 0 || rw->writers > 0) {
        pthread_cond_wait(&rw->ok_to_write, &rw->lock);
    }
    rw->waiting_writers--;
    rw->writers++;
    pthread_mutex_unlock(&rw->lock);
}

void fair_write_unlock(fair_rwlock_t* rw) {
    pthread_mutex_lock(&rw->lock);
    rw->writers--;
    if (rw->waiting_writers > 0) {
        pthread_cond_signal(&rw->ok_to_write); // prefer writers
    } else {
        pthread_cond_broadcast(&rw->ok_to_read); // wake all readers
    }
    pthread_mutex_unlock(&rw->lock);
}
```

## 14.3 The Sleeping Barber Problem

**Setup**: A barber shop with one barber, one barber chair, and N waiting chairs. If no customers: barber sleeps. If customer arrives and barber asleep: wake barber. If waiting room full: customer leaves.

```c
#include <semaphore.h>

sem_t customers;      // counts waiting customers (barber waits on this)
sem_t barber;         // barber ready signal (customer waits on this)
pthread_mutex_t mutex;
int waiting = 0;
#define CHAIRS 5

void* barber_thread(void* arg) {
    while (1) {
        sem_wait(&customers);    // sleep until a customer arrives
        pthread_mutex_lock(&mutex);
        waiting--;
        sem_post(&barber);       // signal: ready to cut hair
        pthread_mutex_unlock(&mutex);
        // cut_hair()
        printf("Barber: cutting hair\n");
        sleep(1);
    }
    return NULL;
}

void* customer_thread(void* arg) {
    int id = *(int*)arg;
    pthread_mutex_lock(&mutex);
    if (waiting < CHAIRS) {
        waiting++;
        sem_post(&customers);    // signal: customer waiting
        pthread_mutex_unlock(&mutex);
        sem_wait(&barber);       // wait for barber to be ready
        // get_haircut()
        printf("Customer %d: getting haircut\n", id);
    } else {
        pthread_mutex_unlock(&mutex);
        printf("Customer %d: no chairs, leaving\n", id);
    }
    return NULL;
}
```

---

# 15. DEADLOCK, LIVELOCK, STARVATION {#15-deadlock}

## 15.1 Deadlock

**Deadlock** is a state where a group of threads are each waiting for a resource held by another thread in the group — creating a cycle of waits with no escape.

**Coffman's Four Necessary Conditions** (ALL must hold for deadlock):
1. **Mutual Exclusion**: Resources cannot be shared (only one thread at a time)
2. **Hold and Wait**: Thread holds one resource while waiting for another
3. **No Preemption**: Resources cannot be forcibly taken away
4. **Circular Wait**: A cycle exists in the wait-for graph

**Breaking any one condition prevents deadlock:**

```
Condition         Prevention Strategy
────────────────────────────────────────────────────────────────
Mutual Exclusion  Make resources shareable (e.g., RWLock for reads)
Hold and Wait     Require all resources at once (all-or-nothing)
No Preemption     Allow resource preemption (timeout, trylock)
Circular Wait     Impose global ordering on resource acquisition
```

## 15.2 Deadlock Detection Algorithm (Wait-For Graph)

```
Thread A holds: Lock1,  waits for: Lock2
Thread B holds: Lock2,  waits for: Lock3
Thread C holds: Lock3,  waits for: Lock1

Wait-for graph:
    A ──→ B ──→ C
    ↑            │
    └────────────┘   CYCLE DETECTED → DEADLOCK
```

To detect deadlock: build the wait-for graph and check for cycles using DFS.

```c
// Simplified deadlock detection
// Real systems (like databases) run this periodically

#define MAX_THREADS 10
#define MAX_LOCKS   20

// wait_for[i] = j means thread i is waiting for thread j to release a lock
int wait_for[MAX_THREADS]; // -1 = not waiting

// DFS to detect cycle
int visited[MAX_THREADS];
int in_stack[MAX_THREADS];

int has_cycle_dfs(int node) {
    visited[node] = 1;
    in_stack[node] = 1;

    int next = wait_for[node];
    if (next != -1) {
        if (!visited[next] && has_cycle_dfs(next)) return 1;
        else if (in_stack[next]) return 1; // back edge → cycle
    }

    in_stack[node] = 0;
    return 0;
}

int detect_deadlock(int num_threads) {
    memset(visited,  0, sizeof(visited));
    memset(in_stack, 0, sizeof(in_stack));

    for (int i = 0; i < num_threads; i++) {
        if (!visited[i] && has_cycle_dfs(i)) {
            return 1; // deadlock detected
        }
    }
    return 0;
}
```

## 15.3 Livelock

**Livelock** is like deadlock, but threads keep changing state in response to each other without making progress. They are "alive" but stuck in a loop.

Classic example: Two people in a hallway trying to pass each other — each steps aside in the same direction simultaneously, forever.

```c
// Livelock example: two threads using trylock
void* thread_a(void* arg) {
    while (1) {
        if (pthread_mutex_trylock(&lockA) == 0) {
            if (pthread_mutex_trylock(&lockB) == 0) {
                // do work
                pthread_mutex_unlock(&lockB);
                pthread_mutex_unlock(&lockA);
                return NULL;
            }
            pthread_mutex_unlock(&lockA); // Can't get B — give up A!
        }
        // Both release, both retry at same time → livelock
        usleep(rand() % 1000); // Random backoff breaks livelock
    }
}
```

**Solution**: Randomized backoff (exponential backoff used in Ethernet, lock-free algorithms).

## 15.4 Starvation

**Starvation** occurs when a thread is indefinitely denied access to a resource it needs, even though the resource is repeatedly becoming available — just never to that thread.

Cause: Unfair scheduling or lock policy that always favors certain threads.

**Prevention**: Use fair locks (ticket locks, FIFO queues), or ensure bounded waiting time.

## 15.5 The Banker's Algorithm (Deadlock Avoidance)

Dijkstra's Banker's Algorithm determines if granting a resource request would leave the system in a **safe state** (one where all threads can eventually complete).

```
System state:
  Available: [A=3, B=3, C=2]  (currently available resources)

  Thread  Max   Allocated  Need (Max-Allocated)
  ──────────────────────────────────────────────
  P0      7,5,3   0,1,0        7,4,3
  P1      3,2,2   2,0,0        1,2,2
  P2      9,0,2   3,0,2        6,0,0
  P3      2,2,2   2,1,1        0,1,1
  P4      4,3,3   0,0,2        4,3,1

Safe sequence: P1 → P3 → P4 → P0 → P2
Each thread can be satisfied using available + what previously-finished threads returned
```

---

# 16. PRIORITY INVERSION {#16-priority-inversion}

## 16.1 What is Priority Inversion?

**Priority inversion** occurs when a high-priority thread is effectively blocked waiting for a low-priority thread that holds a lock — while a medium-priority thread runs, preventing the low-priority thread from releasing the lock.

```
Priority: HIGH=3, MED=2, LOW=1

Timeline:
t=1: LOW thread locks mutex M
t=2: HIGH thread tries to lock M → BLOCKS (LOW holds it)
t=3: MED thread becomes runnable → PREEMPTS LOW (higher priority)
     MED runs continuously...
     LOW cannot run because MED is scheduled instead
     HIGH cannot run because LOW hasn't released M
     HIGH is effectively blocked by MED — PRIORITY INVERSION

HIGH ──────────────────────────BLOCKED──────────BLOCKED────────────
MED  ─────────────────────────────────RUNNING─────────────────────
LOW  ──RUNNING─── (holds M)   blocked by MED      RUNNING─release
```

**Famous real-world case**: Mars Pathfinder rover (1997) — priority inversion caused repeated system resets. Fixed in-flight by enabling **Priority Ceiling Protocol** via uplink.

## 16.2 Solutions

### Priority Inheritance
When a low-priority thread holds a mutex that a high-priority thread is waiting for, temporarily **raise the low-priority thread's priority** to match the high-priority waiter.

```
HIGH waiting for LOW's mutex
→ LOW gets boosted to HIGH priority
→ LOW runs, releases mutex
→ LOW's priority returns to original
→ HIGH acquires mutex and continues
```

### Priority Ceiling Protocol
Each mutex has a **ceiling** = maximum priority of any thread that might lock it. When a thread locks a mutex, its priority is raised to the ceiling.

```c
// Linux: PTHREAD_PRIO_INHERIT — automatically enable priority inheritance
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
pthread_mutex_init(&mutex, &attr);
```

---

# 17. LINUX KERNEL SYNCHRONIZATION PRIMITIVES {#17-linux-kernel}

## 17.1 Overview

The Linux kernel has unique synchronization requirements:
- Code runs in different contexts: **process context** (can sleep), **interrupt context** (CANNOT sleep)
- Multi-processor support (SMP)
- Performance is critical — kernel is in the hot path of everything
- No standard library, no POSIX threads

```
Kernel Contexts:
┌─────────────────────────────────────────────────────────────┐
│  PROCESS CONTEXT (can sleep, can access user space)          │
│  - System calls                                              │
│  - Kernel threads                                            │
│  - Can use: mutex, semaphore, rwsem, completion, RCU         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  INTERRUPT CONTEXT (cannot sleep, cannot access user space)  │
│  - Hardware interrupt handlers (ISRs)                        │
│  - Softirqs, tasklets                                        │
│  - Can ONLY use: spinlock, atomic ops, RCU read-side         │
└─────────────────────────────────────────────────────────────┘
```

## 17.2 Kernel Spinlocks

```c
#include <linux/spinlock.h>

// BASIC SPINLOCK (SMP-safe, but NOT interrupt-safe)
spinlock_t my_lock;
spin_lock_init(&my_lock);

spin_lock(&my_lock);       // acquire
// critical section
spin_unlock(&my_lock);     // release

// INTERRUPT-SAFE SPINLOCK (saves/restores interrupt flags)
// Use this when lock can be acquired from interrupt handler
unsigned long flags;
spin_lock_irqsave(&my_lock, flags);    // disable interrupts + spin
// critical section — safe from ALL interruption
spin_unlock_irqrestore(&my_lock, flags); // restore interrupt state

// SOFTIRQ-SAFE SPINLOCK (disables only softirqs)
spin_lock_bh(&my_lock);    // disable bottom half (softirq/tasklet)
spin_unlock_bh(&my_lock);

// TRY VARIANTS
if (spin_trylock(&my_lock)) {
    // got it
    spin_unlock(&my_lock);
}

// READ-WRITE SPINLOCK
rwlock_t rw_lock;
rwlock_init(&rw_lock);

read_lock(&rw_lock);
// multiple readers
read_unlock(&rw_lock);

write_lock(&rw_lock);
// exclusive writer
write_unlock(&rw_lock);

// IRQ-safe versions
read_lock_irqsave(&rw_lock, flags);
read_unlock_irqrestore(&rw_lock, flags);
write_lock_irqsave(&rw_lock, flags);
write_unlock_irqrestore(&rw_lock, flags);
```

**Critical Kernel Rules**:
1. Never sleep while holding a spinlock
2. Never call `kmalloc(GFP_KERNEL)` (which can sleep) while holding a spinlock
3. Preemption is automatically disabled while holding a spinlock (on SMP)
4. Always use `irqsave` variant if the lock can be accessed from an interrupt handler

## 17.3 Kernel Mutex

```c
#include <linux/mutex.h>

// Kernel mutex — CAN SLEEP (process context only!)
struct mutex my_mutex;
mutex_init(&my_mutex);

// OR static initialization:
DEFINE_MUTEX(my_mutex);

mutex_lock(&my_mutex);           // blocks if locked (sleeps, not spins)
mutex_lock_interruptible(&my_mutex); // can be interrupted by signal
mutex_trylock(&my_mutex);        // returns 1 if acquired, 0 if busy
mutex_unlock(&my_mutex);

// is_mutex_locked() — debug only
```

**Kernel mutex vs spinlock decision tree**:
```
Are you in interrupt context (ISR/softirq)?
    YES → Must use spinlock (cannot sleep)
    NO  → Can use either
             ↓
         Is critical section very short (< few hundred ns)?
             YES → Spinlock (avoid sleep overhead)
             NO  → Mutex (allow other threads to run while waiting)
```

## 17.4 Kernel Read-Write Semaphore (rwsem)

```c
#include <linux/rwsem.h>

struct rw_semaphore my_rwsem;
init_rwsem(&my_rwsem);

// STATIC:
DECLARE_RWSEM(my_rwsem);

// Read side (multiple simultaneous readers allowed)
down_read(&my_rwsem);
// ... read shared data ...
up_read(&my_rwsem);

// Non-blocking read
if (down_read_trylock(&my_rwsem)) {
    // ... read ...
    up_read(&my_rwsem);
}

// Write side (exclusive)
down_write(&my_rwsem);
// ... modify data ...
up_write(&my_rwsem);

// Downgrade write to read (atomic, no gap)
down_write(&my_rwsem);
// ... do write work ...
downgrade_write(&my_rwsem); // now holding read lock
// ... continue reading ...
up_read(&my_rwsem);
```

## 17.5 Completions

A **completion** is like a one-shot semaphore — a lightweight mechanism for one thread to tell another "I'm done."

```c
#include <linux/completion.h>

// Declare and initialize
struct completion data_ready;
init_completion(&data_ready);
// OR:
DECLARE_COMPLETION(data_ready);

// --- Thread/Code that WAITS ---
// Blocks until complete() is called
wait_for_completion(&data_ready);
// OR: with timeout (returns 0 on timeout, jiffies remaining if completed)
unsigned long remain = wait_for_completion_timeout(&data_ready, HZ * 5); // 5 sec
// OR: interruptible
int ret = wait_for_completion_interruptible(&data_ready);

// --- Thread/Code that SIGNALS completion ---
complete(&data_ready);           // wake one waiter
complete_all(&data_ready);       // wake ALL waiters (like broadcast)

// Reinitialize for reuse
reinit_completion(&data_ready);
```

**Use case**: Driver initialization — a kernel thread signals when hardware is ready; calling code waits for the signal before proceeding.

## 17.6 Atomic Operations in the Kernel

```c
#include <linux/atomic.h>

atomic_t counter = ATOMIC_INIT(0);

atomic_read(&counter);                // load
atomic_set(&counter, 5);             // store
atomic_add(3, &counter);             // add 3
atomic_sub(2, &counter);             // subtract 2
atomic_inc(&counter);                // +1
atomic_dec(&counter);                // -1
atomic_add_return(1, &counter);      // add + return NEW value
atomic_fetch_add(1, &counter);       // add + return OLD value
atomic_inc_and_test(&counter);       // increment; returns true if result is 0
atomic_dec_and_test(&counter);       // decrement; returns true if result is 0

// 64-bit:
atomic64_t cnt64 = ATOMIC64_INIT(0);
atomic64_inc(&cnt64);

// atomic_cmpxchg — CAS
int old = atomic_cmpxchg(&counter, expected, new_val);
// if counter == expected: set to new_val, return expected
// if counter != expected: no change, return current value

// Bitwise atomic operations on regular integers
#include <linux/bitops.h>
unsigned long word = 0;
set_bit(3, &word);      // set bit 3
clear_bit(3, &word);    // clear bit 3
test_bit(3, &word);     // test bit 3
test_and_set_bit(3, &word);   // atomic TAS
test_and_clear_bit(3, &word); // atomic TAC
```

## 17.7 Linux Kernel Memory Barriers

```c
#include <linux/compiler.h>
#include <asm/barrier.h>

// FULL BARRIERS (prevent reordering of reads AND writes)
mb();        // full memory barrier
smp_mb();    // SMP memory barrier (NOP on UP kernels)
barrier();   // compiler-only barrier (no CPU fence)

// LOAD BARRIERS (prevent reordering of reads)
rmb();       // read memory barrier
smp_rmb();   // SMP read barrier

// STORE BARRIERS (prevent reordering of writes)
wmb();       // write memory barrier
smp_wmb();   // SMP write barrier

// ACQUIRE/RELEASE (paired with each other)
smp_load_acquire(ptr);    // load with acquire semantics
smp_store_release(ptr, val); // store with release semantics

// ANNOTATE ACCESSES (documentation + potential optimization hints)
READ_ONCE(x);     // prevent compiler from coalescing reads
WRITE_ONCE(x, v); // prevent compiler from coalescing writes
// These also function as compiler barriers
```

**Key kernel barrier usage pattern**:
```c
// Producer (interrupt handler):
data = new_value;
smp_wmb();          // ensure data write is visible before flag
flag = 1;
WRITE_ONCE(flag, 1); // even better: tells compiler not to merge

// Consumer (kernel thread):
while (!READ_ONCE(flag)) cpu_relax();
smp_rmb();          // ensure flag read happens before data read
use(data);
```

## 17.8 per_cpu Variables

Per-CPU variables avoid locking entirely for CPU-local state — each CPU has its own copy.

```c
#include <linux/percpu.h>
#include <linux/percpu-defs.h>

// STATIC declaration
DEFINE_PER_CPU(int, my_counter);
DECLARE_PER_CPU(int, my_counter); // in header

// DYNAMIC allocation
int __percpu *dyn_counter;
dyn_counter = alloc_percpu(int);
free_percpu(dyn_counter);

// ACCESSING per-cpu variables
// MUST disable preemption while accessing!
// (preemption could move task to different CPU mid-access)

int val;
preempt_disable();
val = this_cpu_read(my_counter);      // read this CPU's copy
this_cpu_write(my_counter, 42);       // write this CPU's copy
this_cpu_add(my_counter, 5);          // add to this CPU's copy
this_cpu_inc(my_counter);             // increment this CPU's copy
preempt_enable();

// Or using get_cpu/put_cpu (which also disable preemption):
int cpu = get_cpu();    // get current CPU number + disable preemption
per_cpu(my_counter, cpu)++;
put_cpu();              // re-enable preemption

// Access another CPU's copy (for statistics gathering):
int cpu0_val = per_cpu(my_counter, 0);

// Sum across all CPUs:
long total = 0;
for_each_possible_cpu(cpu) {
    total += per_cpu(my_counter, cpu);
}
```

---

# 18. RCU: READ-COPY-UPDATE {#18-rcu}

## 18.1 What is RCU?

**RCU (Read-Copy-Update)** is the most important and unique synchronization mechanism in the Linux kernel. It allows readers to access data structures with **zero overhead** — no locks, no atomic operations, no memory barriers on the read path.

**Core idea**: Readers are never blocked. Writers create a new version of the data, make it visible atomically, then wait for all existing readers to finish with the old version before freeing it.

```
                 OLD version                NEW version
                 ┌───────┐                 ┌───────┐
                 │ x = 1 │                 │ x = 2 │
                 └───────┘                 └───────┘
                     ↑                         ↑
                     │                         │
Reader A: ────→ [reading old]         
                                 Publish ──────┘
Reader B:                         ──────────────→ [reading new]
                                                     
                 Wait for Reader A to finish
                 ("grace period")
                      │
                      ↓
                 Free old version
```

## 18.2 RCU Mechanism

**Three phases**:
1. **Publish**: Writer atomically updates a pointer (using `rcu_assign_pointer`)
2. **Grace period**: System waits until all current readers complete their RCU read-side critical sections
3. **Reclaim**: Old data is freed (using `kfree_rcu` or `call_rcu`)

**Grace period**: A grace period has elapsed when every CPU has gone through at least one **quiescent state** (a point where it's not in an RCU read-side critical section — e.g., blocking, user space, idle).

## 18.3 RCU Read-Side Cost

On x86_64 with CONFIG_PREEMPT=n (server kernels):
- `rcu_read_lock()`: NOP (just a barrier, often optimized away)
- `rcu_read_unlock()`: NOP
- No atomic operations
- No memory barriers (on most architectures)
- **Literally free** in many cases

## 18.4 Linux Kernel RCU API

```c
#include <linux/rcupdate.h>
#include <linux/rculist.h>

// ============================================================
// SECTION: Basic RCU Usage Pattern — Pointer Update
// ============================================================

struct config {
    int timeout;
    char name[32];
};

// Global pointer protected by RCU
struct config __rcu *current_config;

// READER (can run from ANY context — process, softirq, etc.)
void reader_function(void) {
    struct config *cfg;

    rcu_read_lock();   // Start RCU read-side critical section
                       // On non-preemptible kernel: disables preemption
                       // On PREEMPT_RT: lightweight

    // rcu_dereference: safe pointer dereference with proper memory barrier
    cfg = rcu_dereference(current_config);

    if (cfg) {
        // Safe to read cfg here — even if writer is replacing it
        // The old config object is guaranteed to exist for
        // the duration of the RCU read-side critical section
        printk("timeout = %d\n", cfg->timeout);
    }

    rcu_read_unlock(); // End critical section
    // After this point, cfg is NOT safe to dereference
    // (unless you took a reference to it)
}

// WRITER (must run in process context — grace period requires sleeping)
void writer_function(int new_timeout, const char *new_name) {
    struct config *old_cfg;
    struct config *new_cfg;

    // 1. COPY: allocate and initialize new config
    new_cfg = kmalloc(sizeof(*new_cfg), GFP_KERNEL);
    if (!new_cfg) return;

    // Copy old values, then modify
    old_cfg = rcu_dereference_protected(current_config,
                                         lockdep_is_held(&my_update_lock));
    if (old_cfg) {
        *new_cfg = *old_cfg; // copy existing values
    }
    new_cfg->timeout = new_timeout;
    strncpy(new_cfg->name, new_name, sizeof(new_cfg->name));

    // 2. UPDATE: atomically publish new pointer
    // rcu_assign_pointer includes smp_wmb() — all writes to new_cfg
    // are visible before the pointer update
    rcu_assign_pointer(current_config, new_cfg);

    // 3. WAIT: grace period — wait for all existing readers to finish
    synchronize_rcu(); // sleeps until all CPUs have had a quiescent state
                       // After this returns, no reader can see old_cfg

    // 4. RECLAIM: free the old object
    kfree(old_cfg);
}

// ALTERNATIVE: Asynchronous reclamation (non-blocking writer)
void async_writer_function(void) {
    struct config *old_cfg = rcu_dereference_protected(current_config, 1);
    struct config *new_cfg = kmalloc(sizeof(*new_cfg), GFP_KERNEL);
    // ... set up new_cfg ...

    rcu_assign_pointer(current_config, new_cfg);

    // kfree_rcu: schedules kfree AFTER the next grace period
    // No need to call synchronize_rcu() manually
    kfree_rcu(old_cfg, rcu_head); // rcu_head must be a field in struct config
}

// ============================================================
// SECTION: RCU-Protected Linked List
// ============================================================

#include <linux/rculist.h>

struct my_item {
    struct list_head list;  // must be first or use list_entry
    int key;
    int value;
    struct rcu_head rcu;    // for kfree_rcu
};

LIST_HEAD(my_list);
DEFINE_SPINLOCK(list_lock); // protects write operations only

// READER — no lock needed!
void rcu_list_lookup(int key) {
    struct my_item *item;

    rcu_read_lock();
    list_for_each_entry_rcu(item, &my_list, list) {
        if (item->key == key) {
            printk("Found: value=%d\n", item->value);
            break;
        }
    }
    rcu_read_unlock();
}

// WRITER — needs spinlock to serialize multiple writers
void rcu_list_add(int key, int value) {
    struct my_item *item = kmalloc(sizeof(*item), GFP_KERNEL);
    item->key = key;
    item->value = value;

    spin_lock(&list_lock);
    list_add_rcu(&item->list, &my_list); // RCU-safe list insertion
    spin_unlock(&list_lock);
}

void rcu_list_remove(int key) {
    struct my_item *item;

    spin_lock(&list_lock);
    list_for_each_entry(item, &my_list, list) {
        if (item->key == key) {
            list_del_rcu(&item->list); // atomically removes from list
            spin_unlock(&list_lock);
            // Free after grace period
            kfree_rcu(item, rcu); // rcu = name of rcu_head field
            return;
        }
    }
    spin_unlock(&list_lock);
}

// ============================================================
// SECTION: RCU Flavors
// ============================================================

// rcu_read_lock()      — standard RCU
// rcu_read_lock_bh()   — bottom-half RCU (faster, no BH preemption)
// rcu_read_lock_sched()— scheduler RCU (quiescent = context switch)
// srcu_read_lock()     — Sleepable RCU (readers CAN sleep!)

#include <linux/srcu.h>
static struct srcu_struct my_srcu;

void srcu_example(void) {
    int idx = srcu_read_lock(&my_srcu);
    // readers can SLEEP here (unlike regular RCU)
    // useful in contexts where sleeping is needed but RCU semantics are wanted
    srcu_read_unlock(&my_srcu, idx);
}
```

## 18.5 RCU Use Cases

```
When to use RCU:
╔═══════════════════════════════════════════════════════════════╗
║  Reads >> Writes (99% reads, 1% writes)                       ║
║  Readers need zero overhead                                   ║
║  Data can be "copied and replaced" on update                  ║
║  Update doesn't need to be immediately visible to all CPUs    ║
╠═══════════════════════════════════════════════════════════════╣
║  Examples: routing tables, security policies,                 ║
║           /proc data, driver parameters, module list          ║
╚═══════════════════════════════════════════════════════════════╝

When NOT to use RCU:
╔═══════════════════════════════════════════════════════════════╗
║  Writes are frequent (too many grace periods = overhead)      ║
║  Need immediate consistency (readers must see latest write)   ║
║  Data is very large (copying is expensive)                    ║
║  Write side can't sleep (use spinlock instead)                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

# 19. SEQLOCKS {#19-seqlocks}

## 19.1 What is a Seqlock?

A **seqlock** (sequence lock) is a reader-writer mechanism where:
- **Writers** never wait for readers (unlike rwsem/rwlock)
- **Readers** detect if a write occurred during their read and retry

It uses a **sequence counter**: writers increment it before and after writing. Readers check the counter before and after reading — if it changed, a write occurred, and the read is retried.

```
Writer:
    seq++ (make it odd — signals "write in progress")
    write data
    seq++ (make it even — signals "write done")

Reader:
    seq1 = read seq (wait until even — no write in progress)
    read data
    seq2 = read seq
    if seq1 != seq2: retry (a write happened during our read)
```

## 19.2 Properties

- **Writers never wait**: Great for frequently-updated data
- **Readers may retry**: Low overhead if writes are rare; high overhead if writes are frequent
- **Not suitable for**: Pointers (can't safely retry after following stale pointer), write-mostly data

**Primary kernel use**: `jiffies`, `xtime` (system clock), `seqlock_t` throughout the kernel for timestamp and counter updates.

## 19.3 C Implementation (Userspace & Kernel-style)

```c
#include <stdatomic.h>
#include <stdio.h>
#include <pthread.h>

// ============================================================
// SECTION: Userspace Seqlock Implementation
// ============================================================

typedef struct {
    atomic_uint  seq;     // sequence counter; odd=writing, even=done
    // data protected by this seqlock:
    long         seconds;
    long         nanoseconds;
} seqlock_time_t;

void seqlock_init(seqlock_time_t* sl) {
    atomic_store(&sl->seq, 0);
}

// WRITER: never blocks
void seqlock_write_begin(seqlock_time_t* sl) {
    unsigned old = atomic_load_explicit(&sl->seq, memory_order_relaxed);
    // seq must be even before we begin (no concurrent writer)
    // In real use, writers are serialized by a separate mutex
    atomic_store_explicit(&sl->seq, old + 1, memory_order_release);
    // seq is now ODD → readers will retry
}

void seqlock_write_end(seqlock_time_t* sl) {
    unsigned old = atomic_load_explicit(&sl->seq, memory_order_relaxed);
    atomic_store_explicit(&sl->seq, old + 1, memory_order_release);
    // seq is now EVEN again → readers can proceed
}

// READER: retries if sequence changed
void seqlock_read_time(seqlock_time_t* sl, long* sec, long* nsec) {
    unsigned seq1, seq2;
    do {
        // Spin until sequence is even (no write in progress)
        do {
            seq1 = atomic_load_explicit(&sl->seq, memory_order_acquire);
        } while (seq1 & 1); // odd = write in progress

        // Read the data
        *sec  = sl->seconds;
        *nsec = sl->nanoseconds;

        // Check if sequence changed (write started during our read)
        seq2 = atomic_load_explicit(&sl->seq, memory_order_acquire);
    } while (seq1 != seq2); // retry if sequence changed
}

// ============================================================
// LINUX KERNEL SEQLOCK API (for reference):
// ============================================================

/*
#include <linux/seqlock.h>

seqlock_t my_seqlock = SEQLOCK_UNLOCKED;
// OR: seqlock_init(&my_seqlock);

// WRITER (uses internal spinlock):
write_seqlock(&my_seqlock);   // spin_lock + increment seq
// ... write data ...
write_sequnlock(&my_seqlock); // increment seq + spin_unlock

// Also: write_seqlock_irqsave(), write_seqlock_bh()

// READER:
unsigned seq;
do {
    seq = read_seqbegin(&my_seqlock);  // read seq, spin if odd
    // ... read data ...
} while (read_seqretry(&my_seqlock, seq)); // retry if seq changed

// Seqcount (seqlock without the spinlock — writer serialized externally):
seqcount_t my_seqcount = SEQCNT_ZERO(my_seqcount);

write_seqcount_begin(&my_seqcount); // just increments counter
write_seqcount_end(&my_seqcount);   // just increments counter

unsigned seq;
do {
    seq = read_seqcount_begin(&my_seqcount);
    // read data
} while (read_seqcount_retry(&my_seqcount, seq));
*/
```

---

# 20. PER-CPU VARIABLES {#20-percpu}

## 20.1 Concept

**Per-CPU variables** are the ultimate in lock-free: instead of sharing one variable with synchronization, give each CPU its own private copy. No sharing → no contention → no synchronization needed.

```
       CPU 0          CPU 1          CPU 2          CPU 3
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ counter=5│   │ counter=3│   │ counter=8│   │ counter=2│
    └──────────┘   └──────────┘   └──────────┘   └──────────┘
    
    Total = 5+3+8+2 = 18 (sum all CPUs for global value)
    
    Each CPU reads/writes ONLY its own copy → zero contention!
```

**When to aggregate**: When you need the global total (for reporting, limits), sum all per-CPU copies with a lock or atomic approach.

## 20.2 Userspace Per-CPU Pattern (C)

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h>

// ============================================================
// SECTION: Userspace Per-CPU Counter Simulation
// Real per-CPU = one slot per CPU core, aligned to cache line
// ============================================================

#define MAX_CPUS 64
#define CACHE_LINE_SIZE 64

// Each slot padded to cache line to prevent false sharing
typedef struct {
    long value;
    char padding[CACHE_LINE_SIZE - sizeof(long)];
} __attribute__((aligned(CACHE_LINE_SIZE))) percpu_counter_slot_t;

typedef struct {
    percpu_counter_slot_t slots[MAX_CPUS];
    int num_cpus;
} percpu_counter_t;

// Get CPU id — in real code use sched_getcpu()
static __thread int thread_cpu_id = -1;
static atomic_int cpu_id_counter = 0;

int get_cpu_id(void) {
    if (thread_cpu_id == -1) {
        thread_cpu_id = atomic_fetch_add(&cpu_id_counter, 1) % MAX_CPUS;
    }
    return thread_cpu_id;
}

void percpu_counter_init(percpu_counter_t* c) {
    c->num_cpus = MAX_CPUS;
    for (int i = 0; i < MAX_CPUS; i++)
        c->slots[i].value = 0;
}

// No locking needed! Each thread operates on its own slot
void percpu_counter_add(percpu_counter_t* c, long val) {
    c->slots[get_cpu_id()].value += val;
}

void percpu_counter_inc(percpu_counter_t* c) {
    percpu_counter_add(c, 1);
}

// Aggregation: need to sum all slots
long percpu_counter_sum(percpu_counter_t* c) {
    long total = 0;
    for (int i = 0; i < c->num_cpus; i++)
        total += c->slots[i].value;
    return total;
}

// ============================================================
// BENCHMARK: Compare global atomic vs per-cpu
// ============================================================

#define ITERATIONS 10000000

static atomic_long global_counter = 0;
static percpu_counter_t percpu_counter;

void* global_counter_worker(void* arg) {
    for (int i = 0; i < ITERATIONS / 8; i++)
        atomic_fetch_add(&global_counter, 1);
    return NULL;
}

void* percpu_counter_worker(void* arg) {
    for (int i = 0; i < ITERATIONS / 8; i++)
        percpu_counter_inc(&percpu_counter);
    return NULL;
}
```

## 20.3 Rust Per-CPU Pattern

```rust
use std::cell::Cell;
use std::sync::atomic::{AtomicI64, Ordering};

// ============================================================
// Rust's thread_local! is the idiomatic per-thread (≈ per-CPU) storage
// Combined with cache line padding to prevent false sharing
// ============================================================

#[repr(align(64))] // align to cache line
struct CacheAligned<T>(T);

// Thread-local counter — no synchronization needed for per-thread access
thread_local! {
    static LOCAL_COUNTER: Cell<i64> = Cell::new(0);
}

fn thread_local_inc() {
    LOCAL_COUNTER.with(|c| c.set(c.get() + 1));
}

fn thread_local_get() -> i64 {
    LOCAL_COUNTER.with(|c| c.get())
}

// For true per-CPU counters in Rust userspace, we need external crates
// (crossbeam's CachePadded, or manual alignment + thread-id mapping)

// The principle: each thread has its own counter, no contention
fn demo_thread_local() {
    use std::thread;
    use std::sync::{Arc, Mutex};

    let all_totals = Arc::new(Mutex::new(vec![]));
    let mut handles = vec![];

    for _ in 0..8 {
        let totals = Arc::clone(&all_totals);
        handles.push(thread::spawn(move || {
            for _ in 0..1_000_000 {
                thread_local_inc();
            }
            let local_total = thread_local_get();
            totals.lock().unwrap().push(local_total);
        }));
    }

    for h in handles { h.join().unwrap(); }

    let total: i64 = all_totals.lock().unwrap().iter().sum();
    println!("Total (per-thread): {}", total); // 8,000,000
}
```

---

# 21. MEMORY BARRIERS IN DEPTH {#21-memory-barriers}

## 21.1 Why Memory Barriers Exist

Processors and compilers reorder memory operations for performance. Memory barriers (also called fences) prevent specific reorderings.

```
Types of reordering:
                        (both can be prevented by barriers)
                         ↓                      ↓
Store-Load:    WRITE A, then READ B  →  CPU may execute READ B first
Store-Store:   WRITE A, then WRITE B →  CPU may execute WRITE B first
Load-Load:     READ A, then READ B   →  CPU may execute READ B first
Load-Store:    READ A, then WRITE B  →  CPU may execute WRITE B first
```

## 21.2 x86 vs ARM Memory Models

```
x86-64 (Total Store Order — strong model):
  - All writes are visible in order (strong store-store guarantee)
  - Only Store-Load can be reordered
  - Most code needs only StoreLoad barriers (mfence)
  - This is why x86 feels "easy" for lock-free code

ARM/POWER (Weak memory model):
  - All four reorderings are possible
  - Need explicit barriers for almost all cross-thread communication
  - Much more thought required for lock-free code
```

## 21.3 C: Memory Barrier Patterns

```c
#include <stdatomic.h>

// ============================================================
// PATTERN 1: Publication (store-release / load-acquire pair)
// ============================================================

static int shared_data  = 0;
static atomic_int ready = 0;

void publisher(void) {
    shared_data = 42;    // Write data FIRST
    // RELEASE: all preceding writes visible before this store
    atomic_store_explicit(&ready, 1, memory_order_release);
}

void subscriber(void) {
    // ACQUIRE: all subsequent reads happen after this load
    while (atomic_load_explicit(&ready, memory_order_acquire) == 0)
        ; // spin
    // Guaranteed: shared_data == 42 here
    printf("%d\n", shared_data); // always prints 42
}

// ============================================================
// PATTERN 2: Dekker's handshake (SeqCst required)
// ============================================================

static atomic_int flag_a = 0;
static atomic_int flag_b = 0;
static int critical_work = 0;

void thread_a(void) {
    // SeqCst provides total order — both threads see same order of operations
    atomic_store(&flag_a, 1);    // memory_order_seq_cst (default)
    if (!atomic_load(&flag_b)) { // memory_order_seq_cst
        // Safe to enter critical section
        critical_work = 1;
    }
}

// ============================================================
// PATTERN 3: Compiler barrier (prevent compiler reordering only)
// ============================================================

int x = 0;
int y = 0;

void write_xy(void) {
    x = 1;
    __asm__ volatile("" ::: "memory"); // compiler barrier
    // Compiler won't reorder x and y writes
    // But CPU MIGHT still reorder them (need smp_wmb for that)
    y = 1;
}

// ============================================================
// PATTERN 4: Standalone fences (separate from atomic ops)
// ============================================================

void fence_example(void) {
    // fence(release) + atomic store(relaxed) ≡ atomic store(release)
    // But fences can protect multiple operations at once

    shared_data = 1;
    shared_data = 2;  // Two writes
    atomic_thread_fence(memory_order_release); // Single fence for both
    atomic_store_explicit(&ready, 1, memory_order_relaxed);
}
```

## 21.4 Rust Memory Barrier Patterns

```rust
use std::sync::atomic::{AtomicBool, AtomicI32, Ordering, fence};

// ============================================================
// PATTERN: Consume semantics (data dependency ordering)
// Rust doesn't expose consume directly; use acquire instead
// ============================================================

static DATA: AtomicI32 = AtomicI32::new(0);
static READY: AtomicBool = AtomicBool::new(false);

fn writer() {
    DATA.store(42, Ordering::Relaxed);
    READY.store(true, Ordering::Release);  // Release pairs with Acquire
}

fn reader() -> i32 {
    while !READY.load(Ordering::Acquire) {
        std::hint::spin_loop();
    }
    DATA.load(Ordering::Relaxed) // Safe: guaranteed to see 42
}

// ============================================================
// PATTERN: SeqLock in Rust
// ============================================================

use std::sync::atomic::AtomicU32;

struct SeqLock {
    seq:     AtomicU32,
    seconds: AtomicI32,
    nanos:   AtomicI32,
}

impl SeqLock {
    const fn new() -> Self {
        SeqLock {
            seq:     AtomicU32::new(0),
            seconds: AtomicI32::new(0),
            nanos:   AtomicI32::new(0),
        }
    }

    fn write(&self, sec: i32, ns: i32) {
        // Begin write: make seq odd
        let old = self.seq.fetch_add(1, Ordering::Release);
        assert!(old % 2 == 0, "concurrent writer!");

        self.seconds.store(sec, Ordering::Relaxed);
        self.nanos.store(ns, Ordering::Relaxed);

        // End write: make seq even again
        self.seq.fetch_add(1, Ordering::Release);
    }

    fn read(&self) -> (i32, i32) {
        loop {
            // Wait for even seq (no write in progress)
            let seq1 = loop {
                let s = self.seq.load(Ordering::Acquire);
                if s % 2 == 0 { break s; }
                std::hint::spin_loop();
            };

            let sec = self.seconds.load(Ordering::Relaxed);
            let ns  = self.nanos.load(Ordering::Relaxed);

            // Fence ensures reads above complete before seq2 check
            fence(Ordering::Acquire);
            let seq2 = self.seq.load(Ordering::Relaxed);

            if seq1 == seq2 {
                return (sec, ns); // consistent read
            }
            // else: retry
        }
    }
}
```

---

# 22. TRANSACTIONAL MEMORY {#22-transactional-memory}

## 22.1 What is Transactional Memory?

**Transactional Memory (TM)** applies database transaction concepts to shared memory synchronization:
- A **transaction** groups multiple memory operations atomically
- If no conflict occurs → transaction **commits** (changes become visible)
- If a conflict occurs → transaction **aborts** and retries

```
thread A transaction:
    begin_transaction
    x = x + 1
    y = y - 1
    commit_transaction   ← atomic: either all happen or none
```

**Benefits**: Programmer writes optimistic, lock-free-looking code without managing CAS loops. Hardware or software detects and resolves conflicts.

## 22.2 Hardware Transactional Memory (HTM) — Intel TSX

```c
#include <immintrin.h> // for _xbegin, _xend, _xabort

// ============================================================
// Intel TSX (Transactional Synchronization Extensions)
// RTM: Restricted Transactional Memory
// ============================================================

int transactional_increment(int* counter) {
    unsigned status;

    // _XBEGIN_STARTED = 0xFFFFFFFF
    if ((status = _xbegin()) == _XBEGIN_STARTED) {
        // TRANSACTIONAL PATH: execute optimistically
        (*counter)++;
        _xend(); // commit: changes become visible atomically
        return 1; // success
    }

    // Transaction aborted: fall back to locked path
    // status encodes reason for abort:
    if (status & _XABORT_RETRY) {
        // Conflict detected — safe to retry
    }
    if (status & _XABORT_CAPACITY) {
        // Transaction too large for CPU's tracking capacity
    }
    if (status & _XABORT_EXPLICIT) {
        // Code called _xabort() explicitly
    }

    // Fallback: use regular lock
    return 0;
}

// ============================================================
// SECTION: HTM with lock elision (common pattern)
// Try hardware transaction; fall back to software lock on failure
// ============================================================

pthread_mutex_t fallback_lock = PTHREAD_MUTEX_INITIALIZER;

void htm_locked_operation(int* shared_data) {
    for (int retry = 0; retry < 3; retry++) {
        if (_xbegin() == _XBEGIN_STARTED) {
            // Inside transaction: check if lock is held
            // (if another thread holds the lock, this will abort the transaction)
            if (pthread_mutex_trylock(&fallback_lock) != 0) {
                _xabort(0xFF); // abort explicitly if lock is held
            }
            // Do the work
            (*shared_data)++;
            _xend();
            return;
        }
        // Retry up to 3 times
    }

    // All retries failed: use the lock
    pthread_mutex_lock(&fallback_lock);
    (*shared_data)++;
    pthread_mutex_unlock(&fallback_lock);
}
```

## 22.3 Go: STM Simulation

Go doesn't have built-in STM, but channels and goroutines naturally provide transaction-like semantics for many use cases:

```go
package main

import "fmt"

// Using channels as a "database" with a single goroutine managing state
// This is Go's idiomatic approach to safe shared state

type Request struct {
    op       string
    key      string
    value    int
    response chan int
}

func stateManager(req chan Request) {
    state := make(map[string]int)
    for r := range req {
        switch r.op {
        case "get":
            r.response <- state[r.key]
        case "set":
            state[r.key] = r.value
            r.response <- 0
        case "add":
            state[r.key] += r.value
            r.response <- state[r.key]
        }
    }
}

func main() {
    ch := make(chan Request, 10)
    go stateManager(ch)

    resp := make(chan int, 1)
    ch <- Request{"set", "balance", 1000, resp}
    <-resp

    ch <- Request{"add", "balance", 500, resp}
    newBalance := <-resp
    fmt.Printf("New balance: %d\n", newBalance)
}
```

---

# 23. MENTAL MODELS & EXPERT INTUITION {#23-mental-models}

## 23.1 The Synchronization Decision Framework

```
QUESTION 1: Is the data SHARED (accessed by multiple threads)?
    NO  → No synchronization needed. Done.
    YES → Continue.

QUESTION 2: Is the data MUTABLE (can any thread write)?
    NO  → Read-only data is always safe. Done.
    YES → Continue.

QUESTION 3: How are ACCESSES DISTRIBUTED (read-heavy vs write-heavy)?
    Read-heavy (95%+ reads) → Consider RCU, RWLock, or seqlock
    Write-heavy → Use Mutex or Spinlock

QUESTION 4: How LONG is the critical section?
    < 1 microsecond → Spinlock (avoid sleep overhead)
    > 1 microsecond → Mutex (allow scheduler to use CPU productively)

QUESTION 5: Is access from INTERRUPT CONTEXT?
    YES → MUST use spinlock (interrupts cannot sleep)
    NO  → Any primitive works

QUESTION 6: Do you need COUNTING or SIGNALING (not just exclusion)?
    YES → Semaphore or Condvar
    NO  → Mutex/Spinlock

QUESTION 7: Is the DATA STRUCTURE complex (linked list, tree)?
    Consider lock-free structures or RCU for read scalability

QUESTION 8: Can you ELIMINATE sharing entirely?
    Per-CPU variables → zero synchronization overhead
    Message passing (Go channels) → share by communicating
```

## 23.2 The Ownership Mental Model (Rust's Approach)

Rust's type system enforces synchronization correctness at compile time:

```
RULES:
1. Multiple owners → Arc<T>             (shared ownership)
2. Shared mutable  → Arc<Mutex<T>>      (interior mutability + sync)
3. Read-heavy      → Arc<RwLock<T>>     (many readers, one writer)
4. No sharing      → T (by value)       (moved across threads)
5. Read-only share → Arc<T>             (immutable = always safe)

The Rust borrow checker ensures:
- You cannot alias AND mutate (Aliased XOR Mutable)
- You cannot send non-Send types to other threads
- You cannot share non-Sync types across threads

If it compiles → no data races. This is PROVEN, not assumed.
```

## 23.3 The Go Philosophy: Communicate, Don't Share

```
TRADITIONAL (mutex-based):
  Thread A ──writes──→ [shared memory] ←──reads── Thread B
                            ↑
                         mutex protects

GO IDIOMATIC (channel-based):
  Thread A ──sends message──→ [channel] ──receives──→ Thread B
  
  "Do not communicate by sharing memory;
   instead, share memory by communicating."
   — Go team motto

WHEN TO USE CHANNELS:  Ownership transfer, pipelines, fan-out/fan-in
WHEN TO USE MUTEX:     Simple state protection, caches, counters
```

## 23.4 The ABA Problem Mental Model

"The address is the same, but the world has changed."

Always ask: **Can a pointer/value revert to a previous state after I read it?**
- If YES: You need tagged pointers, hazard pointers, or epoch-based memory
- If NO (values are monotonically increasing, or objects are never recycled): Basic CAS is safe

## 23.5 The Happens-Before Checklist

Before publishing data to another thread, ask:
1. Have I written all the data BEFORE the publish operation?
2. Does the publish use Release ordering (or equivalent)?
3. Does the reader use Acquire ordering on the same atomic variable?
4. Is there a clear "signal" variable that acts as the synchronization point?

## 23.6 Lock Hierarchy Anti-Patterns

```
ANTI-PATTERNS TO AVOID:
════════════════════════════════════════════════════════════════
1. Lock inversion: Thread A locks L1 then L2; Thread B locks L2 then L1
   FIX: Always acquire locks in consistent global order

2. Lock while calling user callbacks: Callback might try to acquire same lock
   FIX: Copy data, release lock, then call callback

3. Holding locks across blocking calls (I/O, sleep, syscall)
   FIX: Release lock before blocking; reacquire after

4. Excessive lock granularity: One giant lock for everything
   FIX: Use fine-grained locks or lock-free structures

5. Insufficient lock granularity: Lock per-element when you need atomicity across elements
   FIX: Use broader lock scope for compound operations

6. Forgetting lock on one code path (error handling)
   FIX: Use RAII (Rust guards, C++ lock_guard, Go defer)
```

## 23.7 Deliberate Practice Plan for Mastering Synchronization

```
PHASE 1 (Weeks 1-2): Foundation
  □ Implement spinlock from scratch (CAS only)
  □ Implement mutex using futex (Linux)
  □ Solve producer-consumer with semaphores
  □ Write programs with intentional race conditions, find them with TSan

PHASE 2 (Weeks 3-4): Intermediate
  □ Implement MPMC queue (lock-based, then lock-free)
  □ Implement RWLock with fairness
  □ Solve dining philosophers with 3 different strategies
  □ Write a thread pool with work stealing

PHASE 3 (Weeks 5-6): Advanced
  □ Implement MCS lock (scalable spinlock)
  □ Implement epoch-based memory reclamation
  □ Study Linux kernel RCU implementation (kernel/rcu/tree.c)
  □ Implement seqlock and use it for a clock

PHASE 4 (Weeks 7-8): Expert
  □ Implement a lock-free hash table
  □ Study TSan's implementation (understand shadow memory)
  □ Read "The Art of Multiprocessor Programming" (Herlihy & Shavit)
  □ Contribute a synchronization fix to an open-source project
```

## 23.8 Cognitive Principles for Mastery

**Chunking**: Group related synchronization patterns into "chunks" — e.g., "lock + condvar + while loop" is one unit of thought for producer-consumer. Don't think about each line; think about the pattern.

**Deliberate Practice**: Don't just write code that works. Write it wrong on purpose, use TSan to find races, then fix it. This builds intuition faster than only writing correct code.

**Mental Simulation**: Before coding, trace through at least 3 possible thread interleavings in your head. Ask: "What is the worst possible scheduler could do here?"

**Invariant Thinking**: For every lock, state the invariant it protects. A mutex protecting `balance` has invariant: "balance is consistent between lock and unlock." If you can't state the invariant, you don't understand the lock's purpose.

**The Empty Room Test**: When analyzing a critical section, ask "What happens if the scheduler interrupts this thread at EVERY possible instruction boundary?" This forces you to find all races.

---

# APPENDIX A: QUICK REFERENCE

## Synchronization Primitive Comparison Table

```
Primitive          | Ownership | Readers | Interrupt Safe | Can Sleep | Use Case
───────────────────────────────────────────────────────────────────────────────
Mutex (POSIX)      | Yes       | 1       | No             | Yes       | General mutual exclusion
Spinlock           | No        | 1       | Yes            | No        | Short critical sections
RWLock             | No        | N       | No             | Yes       | Read-heavy data
Semaphore (count)  | No        | N       | Partial        | Yes       | Resource pools, signaling
Condition Variable | No        | —       | No             | Yes       | Event waiting
Kernel Mutex       | Yes       | 1       | No             | Yes       | Kernel process context
Kernel Spinlock    | No        | 1       | Yes            | No        | Kernel (any context)
RCU                | No        | ∞       | Yes (read)     | Yes(write)| Read-mostly kernel data
Seqlock            | No        | ∞*      | Yes            | No        | Frequently updated scalars
Per-CPU            | Per-core  | 1/core  | N/A            | N/A       | Per-CPU statistics
Atomic ops         | N/A       | N/A     | Yes            | No        | Single-variable sync

* Readers may retry
```

## Memory Ordering Quick Reference

```
Ordering     | C11 Name              | Rust Name         | Use When
─────────────────────────────────────────────────────────────────────────
Relaxed      | memory_order_relaxed  | Ordering::Relaxed | Just need atomicity (counters)
Acquire      | memory_order_acquire  | Ordering::Acquire | Load that "acquires" a lock/flag
Release      | memory_order_release  | Ordering::Release | Store that "releases" a lock/flag
AcqRel       | memory_order_acq_rel  | Ordering::AcqRel  | RMW ops that both acquire and release
SeqCst       | memory_order_seq_cst  | Ordering::SeqCst  | Need total global order
```

## Linux Kernel Lock Decision Chart

```
         Is code in interrupt context (ISR/softirq)?
                    │
           YES ─────┘─────── NO
            │                │
     Must use spinlock    Can thread SLEEP?
            │                │
    Need IRQ safety?    YES──┘──NO
            │            │      │
     YES    NO          Mutex  Spinlock
      │      │
   spin_lock_ spin_lock()
   irqsave()
```

---

# APPENDIX B: FURTHER READING

- **"The Art of Multiprocessor Programming"** — Herlihy & Shavit (definitive textbook)
- **"Is Parallel Programming Hard..."** — Paul McKenney (free online, covers RCU deeply)
- **"C++ Concurrency in Action"** — Anthony Williams (best practical guide for C++ memory model)
- **Linux kernel documentation**: `Documentation/memory-barriers.txt` (comprehensive hardware barrier guide)
- **Dmitry Vyukov's blog** (1024cores.net) — world-class lock-free algorithm designs
- **cppreference.com/atomic** — authoritative C++ memory model reference
- **Rust Nomicon** — chapters on atomics, `Send`/`Sync` (formal Rust concurrency guarantees)

---

*"Master the fundamentals so deeply that complexity becomes simple.  
Every lock-free algorithm is just CAS with patience.  
Every deadlock is just forgotten ordering.  
Every race condition is just unclaimed ownership.  
Think in invariants. Code in clarity. Debug with TSan."*

---
**END OF DOCUMENT**

I'll now build the complete, comprehensive synchronization guide. This will be a large, deeply structured `.md` file.**5,024 lines · 160 KB** — the complete guide is yours.

---

Here is a precise map of everything covered, so you can use it as a training syllabus:

**Part 1 — Hardware Reality (the "why")**
Covers CPU caches, MESI coherence protocol, out-of-order execution, store buffers, and false sharing. You cannot truly master synchronization without understanding *why* the hardware makes it hard.

**Part 2 — Memory Models**
Covers happens-before, acquire/release/SeqCst ordering, and why C11, Rust, and Go model memory the way they do. Every lock-free algorithm depends on this.

**Part 3 — Atomicity & CAS**
Full implementations in C, Rust, and Go of atomic counters, CAS-based spinlocks, and lock-free stacks. The ABA problem is introduced here.

**Part 4 — Mutual Exclusion (Mutex → Spinlock → RWLock)**
All three with full implementations, including ticket locks (FIFO-fair), MCS locks (cache-scalable), and phase-fair RWLocks. Includes the lock-ordering strategy for multi-lock deadlock prevention.

**Part 5 — Semaphores, Condvars, Monitors, Barriers**
Canonical patterns with bounded buffers, thread pools, connection pools, and start-gun synchronization in all three languages.

**Part 6 — Classic Problems**
Dining Philosophers (3 solutions), Readers-Writers (3 fairness variants), Sleeping Barber — all with working code.

**Part 7 — Linux Kernel**
Kernel spinlocks (irqsave, bh variants), kernel mutex, rwsem, completions, atomic_t, per-cpu variables, and all memory barrier macros (`smp_mb`, `READ_ONCE`, `WRITE_ONCE`, `smp_load_acquire`).

**Part 8 — RCU, Seqlocks, Per-CPU**
The three most powerful kernel-specific primitives. Full RCU lifecycle (publish → grace period → reclaim), RCU-protected linked lists, srcu, seqlock implementation, and per-cpu counter patterns.

**Part 9 — Lock-Free, HTM, Mental Models**
ABA-safe tagged pointer stack, Michael-Scott queue, Intel TSX transactional memory, and the complete decision framework for choosing the right primitive.