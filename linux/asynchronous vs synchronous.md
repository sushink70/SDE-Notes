# Asynchronous vs Synchronous Execution in Linux
## A Complete, Elite-Level Technical Reference
### Covering: Linux Internals · gRPC · C · Rust · Go

---

> **The Expert Mental Model (Read First)**
>
> Synchronization and asynchrony are not opposites — they are orthogonal axes. Synchronization is about
> *ordering* and *mutual exclusion* between concurrent entities. Asynchrony is about *when you wait* for
> an operation to complete. You can have synchronous code that is fully lock-free, and asynchronous
> code that still serializes access to shared state. Conflating these two concepts is the #1 source of
> architectural bugs in systems code. Master both axes independently, then reason about their interaction.

---

## Table of Contents

1. [Foundational Mental Models](#1-foundational-mental-models)
2. [The Linux Execution Model](#2-the-linux-execution-model)
3. [Synchronization Primitives — Linux Kernel Perspective](#3-synchronization-primitives--linux-kernel-perspective)
4. [POSIX User-Space Synchronization (C)](#4-posix-user-space-synchronization-c)
5. [Asynchronous I/O in Linux](#5-asynchronous-io-in-linux)
6. [Memory Ordering and the Memory Model](#6-memory-ordering-and-the-memory-model)
7. [Lock-Free and Wait-Free Programming](#7-lock-free-and-wait-free-programming)
8. [Rust: Ownership as the Synchronization Primitive](#8-rust-ownership-as-the-synchronization-primitive)
9. [Rust Async/Await — The Complete Internals](#9-rust-asyncawait--the-complete-internals)
10. [Go: Goroutines, Channels, and the Runtime Scheduler](#10-go-goroutines-channels-and-the-runtime-scheduler)
11. [gRPC: Synchronous vs Asynchronous Patterns](#11-grpc-synchronous-vs-asynchronous-patterns)
12. [When to Use What — Decision Framework](#12-when-to-use-what--decision-framework)
13. [Anti-Patterns and Failure Modes](#13-anti-patterns-and-failure-modes)
14. [Malware and Security Perspective](#14-malware-and-security-perspective)
15. [Performance Benchmarks and Trade-offs](#15-performance-benchmarks-and-trade-offs)
16. [Reference Tables](#16-reference-tables)

---

## 1. Foundational Mental Models

### 1.1 The Two Axes: Concurrency vs Parallelism vs Async vs Sync

These four terms are routinely confused. Internalize this taxonomy permanently:

```
AXIS 1: EXECUTION MODEL
┌─────────────────────────────────────────────────────────┐
│  Sequential       │  Concurrent        │  Parallel       │
│  One task at a    │  Multiple tasks    │  Multiple tasks  │
│  time, in order   │  interleaved       │  simultaneously  │
│  (no CPU overlap) │  (logical overlap) │  (physical cores)│
└─────────────────────────────────────────────────────────┘

AXIS 2: WAITING MODEL
┌──────────────────────────────────────────────────────────┐
│  Synchronous                │  Asynchronous              │
│  Caller waits for result    │  Caller continues; result  │
│  before proceeding          │  delivered via callback,   │
│  (blocking)                 │  future, or event          │
└──────────────────────────────────────────────────────────┘
```

**Key insight**: You can write *synchronous concurrent* code (e.g., multiple threads, each blocking on
their own I/O). You can also write *asynchronous sequential* code (e.g., a single-threaded event loop).
These axes are independent.

### 1.2 The Five Fundamental Problems Synchronization Solves

Every synchronization primitive you will ever use is solving one or more of these:

```
┌────────────────────────────────────────────────────────────────────┐
│  Problem              │  Failure Mode           │  Primitive Used  │
├────────────────────────────────────────────────────────────────────┤
│  Race Condition       │  Data corruption        │  Mutex, Atomic   │
│  Deadlock             │  System hang            │  Lock ordering   │
│  Livelock             │  Infinite spin, no prog.│  Backoff, CAS    │
│  Starvation           │  Thread never runs      │  Fair locks      │
│  Priority Inversion   │  RT thread starved      │  PI-Mutex        │
└────────────────────────────────────────────────────────────────────┘
```

### 1.3 The Cost Hierarchy (Never Forget This)

```
OPERATION COST (approximate, modern x86-64, L1 hit = 1)
┌────────────────────────────────────┬──────────────────┐
│  L1 cache access                   │  ~4 cycles       │
│  L2 cache access                   │  ~12 cycles      │
│  L3 cache access                   │  ~40 cycles      │
│  Atomic CAS (no contention)        │  ~10-20 cycles   │
│  Atomic CAS (high contention)      │  ~100-1000 cyc.  │
│  Mutex lock (uncontended)          │  ~25-50 cycles   │
│  Mutex lock (contended, futex)     │  ~200-500 cycles │
│  Context switch (kernel)           │  ~1-10 µs        │
│  DRAM access                       │  ~60-100 ns      │
│  Syscall (fast path)               │  ~100-300 ns     │
│  Thread creation (pthread)         │  ~5-50 µs        │
│  epoll_wait (no events)            │  ~1-2 µs         │
│  io_uring submission               │  ~50-200 ns      │
│  Network RTT (localhost)           │  ~10-50 µs       │
└────────────────────────────────────┴──────────────────┘
```

---

## 2. The Linux Execution Model

### 2.1 Threads vs Processes in Linux

Linux makes no kernel-level distinction between threads and processes. Both are **tasks** in the kernel
(`struct task_struct`). The difference is in how resources are shared via `clone(2)` flags.

```
clone(2) flags that define "thread-ness":
┌─────────────────────────────────────────────────────────────────┐
│  CLONE_VM        │  Share virtual memory space                  │
│  CLONE_FS        │  Share filesystem (cwd, umask)               │
│  CLONE_FILES     │  Share file descriptor table                 │
│  CLONE_SIGHAND   │  Share signal handlers                       │
│  CLONE_THREAD    │  Share thread group (same PID to userspace)  │
│  CLONE_SYSVSEM   │  Share SysV semaphore undo values            │
└─────────────────────────────────────────────────────────────────┘

pthread_create() essentially calls clone() with all of the above set.
fork()          calls clone() with NONE of the above set.
```

### 2.2 The Scheduler: CFS and Real-Time Classes

The Completely Fair Scheduler (CFS) uses a **red-black tree** ordered by virtual runtime (`vruntime`).
The task with the lowest vruntime always runs next. This is critical for understanding blocking behavior:

```
SCHEDULING CLASSES (priority order, high to low):

  SCHED_DEADLINE  ──►  EDF (Earliest Deadline First), hard RT
  SCHED_FIFO      ──►  FIFO real-time (no preemption unless blocked/yielded)
  SCHED_RR        ──►  Round-Robin real-time (time quantum)
  SCHED_NORMAL    ──►  CFS (default for userspace threads)
  SCHED_BATCH     ──►  CFS variant, no interactivity boost
  SCHED_IDLE      ──►  Runs only when nothing else can

When a thread blocks (mutex, I/O, futex):
  task_struct.state = TASK_INTERRUPTIBLE or TASK_UNINTERRUPTIBLE
  Removed from CFS runqueue
  Added to wait_queue of the blocking object
  schedule() called → context switch to next task

When the blocking condition resolves:
  Wake function called → task moved back to runqueue
  Task eventually selected by scheduler → runs again
```

### 2.3 The futex: The Foundation of All User-Space Locking

**Everything in user-space locking — pthreads, Rust std::sync, Go's runtime mutexes — ultimately
reduces to futex(2) on Linux.** Understanding futex is non-negotiable.

```c
// Futex system call signature
long futex(uint32_t *uaddr,    // User-space address of the lock word
           int futex_op,        // Operation (FUTEX_WAIT, FUTEX_WAKE, ...)
           uint32_t val,        // Expected value (for WAIT)
           struct timespec *timeout,
           uint32_t *uaddr2,
           uint32_t val3);
```

**The critical insight about futex**: It allows user-space to avoid the kernel on the *fast path*
(no contention) using atomic operations, and falls into the kernel only when blocking is necessary.

```
FUTEX FAST-PATH MUTEX LOCK (no contention):
┌─────────────────────────────────────────────────────────────┐
│  1. Atomic CAS: if lock_word == 0, set to 1                 │
│  2. CAS succeeds → locked, NO syscall, NO kernel entry      │
│  3. Cost: ~1 atomic instruction                             │
└─────────────────────────────────────────────────────────────┘

FUTEX SLOW-PATH (contention detected):
┌─────────────────────────────────────────────────────────────┐
│  1. Atomic CAS fails (lock_word != 0)                       │
│  2. Set lock_word to 2 (indicating waiters exist)           │
│  3. Call futex(FUTEX_WAIT, uaddr, 2) → enter kernel         │
│  4. Kernel checks: if *uaddr still == 2, block task         │
│  5. Unlocker sees lock_word == 2 → futex(FUTEX_WAKE, uaddr)│
│  6. Kernel wakes one waiter → CAS retry loop                │
└─────────────────────────────────────────────────────────────┘
```

**Lock word states for a typical futex mutex:**
```
State 0: Unlocked
State 1: Locked, no waiters (fast path)
State 2: Locked, waiters exist (slow path needed on unlock)
```

### 2.4 The wait_queue Mechanism (Kernel Level)

When a kernel subsystem needs to block a task and wake it later:

```c
// Kernel data structures (simplified)
struct wait_queue_head {
    spinlock_t          lock;
    struct list_head    head;     // Linked list of waiters
};

struct wait_queue_entry {
    unsigned int        flags;
    void               *private;  // Points to task_struct
    wait_queue_func_t   func;     // Wake function (default_wake_function)
    struct list_head    entry;
};

// Usage pattern in kernel drivers/subsystems
DECLARE_WAIT_QUEUE_HEAD(wq);

// Producer side (interrupt handler, timer, etc.)
wake_up(&wq);             // Wake one waiter
wake_up_all(&wq);         // Wake all waiters

// Consumer side (blocking thread)
wait_event(wq, condition);          // Uninterruptible
wait_event_interruptible(wq, cond); // Interruptible by signal
```

---

## 3. Synchronization Primitives — Linux Kernel Perspective

### 3.1 Complete Primitive Taxonomy

```
SYNCHRONIZATION PRIMITIVE TREE
│
├── SPIN-BASED (busy-wait, never sleep)
│   ├── spinlock_t          ─── Basic spinlock (disables preemption)
│   ├── rwlock_t            ─── Reader-writer spinlock
│   ├── raw_spinlock_t      ─── Non-preemptible spinlock (RT kernel)
│   └── bit_spinlock        ─── Lock embedded in a single bit
│
├── SLEEP-BASED (can block, task yields CPU)
│   ├── mutex               ─── Exclusive ownership, priority inheritance
│   ├── rt_mutex            ─── Real-time mutex with PI
│   ├── semaphore           ─── Counting (not for mutual exclusion!)
│   ├── rw_semaphore        ─── Reader-writer, can starve writers
│   └── completion          ─── One-shot event notification
│
├── SEQUENCE COUNTERS (lock-free reads)
│   ├── seqlock_t           ─── Writer-priority, readers retry
│   └── seqcount_t          ─── seqlock without spinlock portion
│
├── RCU (Read-Copy-Update)
│   ├── rcu_read_lock()     ─── Preemption-disabled read section
│   ├── synchronize_rcu()   ─── Wait for all pre-existing readers
│   └── call_rcu()          ─── Async callback after grace period
│
└── ATOMIC OPERATIONS
    ├── atomic_t / atomic64_t
    ├── atomic_cmpxchg()
    └── __atomic_* builtins (C11/GCC)
```

### 3.2 RCU — Read-Copy-Update Deep Dive

RCU is the most sophisticated synchronization primitive in the Linux kernel. **It achieves
zero-overhead reads for concurrent read-heavy workloads** by deferring reclamation.

**The core principle:**
```
PROBLEM: Data structure needs frequent reads, infrequent writes.
         Readers must never be blocked by writers.

RCU SOLUTION:

Writer:
  1. Create a COPY of the data structure
  2. Modify the COPY
  3. Atomically swap pointer: old_ptr → new_ptr (single pointer store)
  4. Wait for "grace period" (all pre-existing read sections end)
  5. Free the OLD data structure

Reader:
  1. rcu_read_lock()     ← disables preemption, marks read section
  2. ptr = rcu_dereference(global_ptr)  ← READ the current pointer
  3. Use ptr->data safely within this section
  4. rcu_read_unlock()   ← ends read section

GUARANTEE: During step 3, the old data is still alive because the
           writer won't free it until ALL readers finish step 4.
```

```
TIMELINE:
  Writer:  [Copy]──[Modify]──[Swap ptr]──[Wait grace period]──[Free old]
  Reader1:                         [lock]──────[use]──[unlock]
  Reader2:             [lock]────────────────────────[unlock]
  Reader3: [lock]─[unlock]
  
  Grace period: from swap until Reader2 unlocks (last pre-swap reader)
  Reader3 completed before swap → irrelevant to this grace period
```

**When to use RCU:**
- Frequently-read, rarely-written linked lists, hash tables, trees
- Network routing tables, security policy lists, device driver lists
- Anywhere lock-free reads matter more than write latency

### 3.3 seqlock — Writer Priority with Lock-Free Reads

```
seqlock STATE:
  Sequence counter (even = unlocked/stable, odd = write in progress)

Writer path:
  1. write_seqlock()   ──► increment counter (even→odd), acquire spinlock
  2. Modify data
  3. write_sequnlock() ──► release spinlock, increment counter (odd→even)

Reader path:
  1. seq = read_seqbegin()    ──► read counter, spin if odd
  2. Read data
  3. if read_seqretry(seq):   ──► if counter changed, RETRY from step 1
  4. Use data

COST: Readers pay the cost of retry when writes occur.
      Writers never wait for readers.
      
USE CASE: jiffies, system time (xtime_lock in kernel)
          Things that must always have fresh data, not stale cached values.
```

### 3.4 Spinlock vs Mutex Decision Tree

```
Should I use a spinlock or a mutex?

Start
  │
  ▼
Are you in kernel space?
  │ No ──► Use pthread_mutex or Rust Mutex (futex-based)
  │ Yes
  ▼
Can the lock holder sleep? (do IO, call kmalloc, etc.)
  │ Yes ──► Must use mutex (spinlocks disable preemption)
  │ No
  ▼
Is the critical section < a few dozen instructions?
  │ No  ──► Consider mutex (long spin wastes CPU)
  │ Yes
  ▼
Are you in interrupt context?
  │ Yes ──► Must use spinlock (mutex can sleep, not allowed in IRQ)
  │ No
  ▼
Are you protecting data accessed from IRQ handlers?
  │ Yes ──► spin_lock_irqsave() (also disables local IRQs)
  │ No  ──► spinlock_t is fine, or mutex if section length allows
```

---

## 4. POSIX User-Space Synchronization (C)

### 4.1 pthread_mutex_t — Complete API and Internals

```c
#include <pthread.h>

// ─── INITIALIZATION ────────────────────────────────────────────────
pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;  // Static init

// Dynamic init with attributes
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK);
// Types:
//   PTHREAD_MUTEX_NORMAL       ─ No error checking, deadlocks if re-locked
//   PTHREAD_MUTEX_ERRORCHECK   ─ Returns EDEADLK if re-locked by same thread
//   PTHREAD_MUTEX_RECURSIVE    ─ Same thread can lock multiple times
//   PTHREAD_MUTEX_DEFAULT      ─ Undefined behavior for re-lock (usually NORMAL)
pthread_mutex_init(&mtx, &attr);
pthread_mutexattr_destroy(&attr);

// ─── OPERATIONS ────────────────────────────────────────────────────
pthread_mutex_lock(&mtx);           // Block until locked
pthread_mutex_trylock(&mtx);        // Returns EBUSY if locked (non-blocking)
pthread_mutex_timedlock(&mtx, &ts); // Block with timeout
pthread_mutex_unlock(&mtx);

// ─── PRIORITY INHERITANCE ──────────────────────────────────────────
// Prevents priority inversion (high-priority thread blocked by low-priority)
pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
// Protocol options:
//   PTHREAD_PRIO_NONE     ─ No PI (default, dangerous for RT)
//   PTHREAD_PRIO_INHERIT  ─ Waiter's priority donated to holder
//   PTHREAD_PRIO_PROTECT  ─ Holder runs at ceiling priority

// ─── ROBUST MUTEX ──────────────────────────────────────────────────
// Returns EOWNERDEAD if lock holder dies without unlocking
pthread_mutexattr_setrobust(&attr, PTHREAD_MUTEX_ROBUST);
int rc = pthread_mutex_lock(&mtx);
if (rc == EOWNERDEAD) {
    // Recover shared state, then:
    pthread_mutex_consistent(&mtx);  // Mark recovered
}

// ─── CLEANUP ───────────────────────────────────────────────────────
pthread_mutex_destroy(&mtx);
```

**Production pattern — RAII-style cleanup in C:**

```c
// Using __attribute__((cleanup)) for automatic unlock
static void mutex_cleanup(pthread_mutex_t **m) {
    pthread_mutex_unlock(*m);
}

void safe_function(pthread_mutex_t *mtx, shared_data_t *data) {
    pthread_mutex_lock(mtx);
    // GCC extension: auto-unlock when mtx_ptr goes out of scope
    pthread_mutex_t *mtx_ptr __attribute__((cleanup(mutex_cleanup))) = mtx;

    // Critical section — cannot forget to unlock
    data->value += 1;
}   // mutex_cleanup called automatically here
```

### 4.2 pthread_rwlock_t — Reader-Writer Lock

```c
pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

// Multiple readers OR one writer, never both
pthread_rwlock_rdlock(&rwlock);   // Acquire read lock (blocks if writer holds)
pthread_rwlock_wrlock(&rwlock);   // Acquire write lock (blocks until all readers done)
pthread_rwlock_tryrdlock(&rwlock);
pthread_rwlock_trywrlock(&rwlock);
pthread_rwlock_unlock(&rwlock);

// ─── CRITICAL DANGER ───────────────────────────────────────────────
// Default behavior is implementation-defined regarding writer starvation.
// On Linux (glibc), the default favors readers → writers can starve.
// Use PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP to fix:
pthread_rwlockattr_t attr;
pthread_rwlockattr_init(&attr);
pthread_rwlockattr_setkind_np(&attr, PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP);
pthread_rwlock_init(&rwlock, &attr);
```

### 4.3 pthread_cond_t — Condition Variables

Condition variables are the backbone of the **producer-consumer** pattern.
**The mutex is always paired with the condvar — this is not optional.**

```c
pthread_mutex_t mtx   = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t  ready = PTHREAD_COND_INITIALIZER;
int             data_ready = 0;

// ─── CONSUMER (waiter) ─────────────────────────────────────────────
void *consumer(void *arg) {
    pthread_mutex_lock(&mtx);

    // CRITICAL: Always use a WHILE loop, never IF.
    // Reason: spurious wakeups are allowed by POSIX.
    // The condition must be re-checked after every wakeup.
    while (!data_ready) {
        // Atomically: release mutex + block on condvar
        // On return: mutex is re-acquired automatically
        pthread_cond_wait(&ready, &mtx);
    }

    // Process data — mutex is held here
    process_data();
    pthread_mutex_unlock(&mtx);
    return NULL;
}

// ─── PRODUCER (signaler) ───────────────────────────────────────────
void *producer(void *arg) {
    pthread_mutex_lock(&mtx);
    produce_data();
    data_ready = 1;

    // Signal vs Broadcast:
    //   pthread_cond_signal()    ─ Wake ONE waiter (undefined which one)
    //   pthread_cond_broadcast() ─ Wake ALL waiters (all re-check condition)
    pthread_cond_signal(&ready);  // or pthread_cond_broadcast()

    pthread_mutex_unlock(&mtx);
    return NULL;
}

// ─── WHY THE MUTEX IN pthread_cond_wait? ──────────────────────────
// Without the mutex, there's a TOCTOU race:
//
//  Consumer:              Producer:
//  check condition=false
//                         set condition=true
//                         signal condvar (no one is waiting yet!)
//  wait forever <──── MISSED WAKEUP
//
// pthread_cond_wait atomically:
//   1. Adds consumer to condvar wait list
//   2. Releases mutex
//   (These two are atomic from the producer's perspective)
// This closes the race window.
```

### 4.4 POSIX Semaphores

Semaphores are **counting** synchronization objects. **Do not use them for mutual exclusion** —
use mutex for that. Use semaphores for *resource counting* and *signaling across processes*.

```c
#include <semaphore.h>

// ─── UNNAMED SEMAPHORE (for threads in same process) ───────────────
sem_t sem;
sem_init(&sem,
    0,          // pshared=0: between threads (pshared=1: between processes)
    10          // initial value = 10 resources available
);

sem_wait(&sem);    // Decrement (block if value == 0) — "P operation"
sem_post(&sem);    // Increment (wake one waiter)     — "V operation"
sem_trywait(&sem); // Non-blocking, returns EAGAIN if value == 0
sem_timedwait(&sem, &ts);
sem_getvalue(&sem, &val);
sem_destroy(&sem);

// ─── NAMED SEMAPHORE (for cross-process synchronization) ───────────
sem_t *sem = sem_open("/my_semaphore", O_CREAT, 0644, 1);
// Lives in /dev/shm on Linux
sem_wait(sem);
sem_post(sem);
sem_close(sem);
sem_unlink("/my_semaphore");  // Remove from filesystem

// ─── SEMAPHORE AS A SIGNAL (binary semaphore pattern) ─────────────
// Thread A signals thread B that work is ready:
sem_t work_ready;
sem_init(&work_ready, 0, 0);  // Start at 0 (no work yet)

// Thread B: blocks until A signals
sem_wait(&work_ready);        // Blocks

// Thread A: signal that work is ready
sem_post(&work_ready);        // Unblocks B

// ─── SEMAPHORE vs MUTEX ────────────────────────────────────────────
// Mutex:     has ownership concept (only locker can unlock)
//            used for mutual exclusion
//            priority inheritance possible
// Semaphore: no ownership (any thread can post)
//            used for signaling, resource counting
//            no priority inheritance (danger for RT)
```

### 4.5 Barriers — Rendezvous Points

```c
// All threads must arrive before any can proceed
pthread_barrier_t barrier;
pthread_barrier_init(&barrier, NULL, N_THREADS);  // N threads must arrive

// Each thread calls:
int rc = pthread_barrier_wait(&barrier);
if (rc == PTHREAD_BARRIER_SERIAL_THREAD) {
    // One (unspecified) thread gets this return value
    // Used for "do this once after all threads arrive" work
    consolidate_results();
}
// All threads proceed past this point together

pthread_barrier_destroy(&barrier);
```

### 4.6 Spinlocks in User Space

```c
// GCC built-in atomic spinlock (DO NOT use in production without careful analysis)
typedef int spinlock_t;
#define SPIN_LOCK_INITIALIZER 0

static inline void spin_lock(spinlock_t *lock) {
    while (__sync_lock_test_and_set(lock, 1)) {
        // Busy-wait — burns CPU
        // Add pause hint to reduce memory bus contention:
        while (*lock) __asm__ volatile("pause" ::: "memory");
    }
}

static inline void spin_unlock(spinlock_t *lock) {
    __sync_lock_release(lock);  // Atomic store of 0
}

// C11 stdatomic version (prefer this)
#include <stdatomic.h>
typedef atomic_flag spinlock_t;
#define SPIN_LOCK_INITIALIZER ATOMIC_FLAG_INIT

static inline void spin_lock(spinlock_t *lock) {
    while (atomic_flag_test_and_set_explicit(lock, memory_order_acquire)) {
        __asm__ volatile("pause" ::: "memory");
    }
}

static inline void spin_unlock(spinlock_t *lock) {
    atomic_flag_clear_explicit(lock, memory_order_release);
}

// ─── WHEN TO USE SPINLOCKS IN USER SPACE ──────────────────────────
// ALMOST NEVER. Only when:
//   1. Critical section is < 5 instructions
//   2. You are certain the holder will not be preempted
//   3. You have measured that futex overhead dominates
// 
// On a preemptible kernel with time slicing, a thread holding
// a spinlock CAN be preempted — all other spinners waste CPU.
```

---

## 5. Asynchronous I/O in Linux

### 5.1 The Evolution of Async I/O on Linux

```
LINUX ASYNC I/O EVOLUTION TIMELINE:

1993  select(2)      ─ First async I/O. O(n) scan, 1024 fd limit, useless
1997  poll(2)        ─ No fd limit, still O(n). Both deprecated for servers.
2002  epoll(4)       ─ O(1) per event, scalable to millions of fds.
                       The standard for high-performance servers since then.
2003  POSIX AIO      ─ (aio_read/aio_write) Standard but kernel impl = bad.
                       Linux used threads internally. Mostly useless.
2014  io_uring (none)─ Doesn't exist yet...
2019  io_uring(7)    ─ True async kernel I/O via shared ring buffers.
                       Zero syscall per operation on fast path.
                       The future of I/O on Linux.
```

### 5.2 epoll — The Standard Model

```c
#include <sys/epoll.h>

// ─── SETUP ─────────────────────────────────────────────────────────
int epfd = epoll_create1(EPOLL_CLOEXEC);  // Create epoll instance
// epfd is a file descriptor to the kernel's internal event data structure

// ─── REGISTRATION ──────────────────────────────────────────────────
struct epoll_event ev = {
    .events  = EPOLLIN | EPOLLET,  // Level-triggered vs Edge-triggered (see below)
    .data.fd = sockfd              // or .data.ptr = (void *)my_conn_struct
};
epoll_ctl(epfd, EPOLL_CTL_ADD, sockfd, &ev);  // Register fd
epoll_ctl(epfd, EPOLL_CTL_MOD, sockfd, &ev);  // Modify
epoll_ctl(epfd, EPOLL_CTL_DEL, sockfd, NULL);  // Remove

// ─── EVENT LOOP ────────────────────────────────────────────────────
#define MAX_EVENTS 1024
struct epoll_event events[MAX_EVENTS];

while (1) {
    int nfds = epoll_wait(epfd,         // epoll instance
                          events,        // events buffer
                          MAX_EVENTS,    // max events to return
                          -1);           // timeout ms (-1 = infinite)
    for (int i = 0; i < nfds; i++) {
        if (events[i].events & EPOLLIN) {
            handle_read(events[i].data.fd);
        }
        if (events[i].events & EPOLLOUT) {
            handle_write(events[i].data.fd);
        }
        if (events[i].events & (EPOLLERR | EPOLLHUP)) {
            close(events[i].data.fd);
        }
    }
}

// ─── LEVEL vs EDGE TRIGGERED ───────────────────────────────────────
//
// LEVEL-TRIGGERED (default, EPOLLIN without EPOLLET):
//   epoll_wait returns as long as data is available.
//   If you don't read all data, next epoll_wait still reports EPOLLIN.
//   Easier to use, but requires attention to avoid busy-loop.
//
// EDGE-TRIGGERED (EPOLLET):
//   epoll_wait returns ONCE when the state changes (data becomes available).
//   You MUST read until EAGAIN/EWOULDBLOCK to drain the buffer.
//   If you don't drain, the event won't fire again until more data arrives!
//   Required pattern with ET:

void handle_read_et(int fd) {
    char buf[4096];
    ssize_t n;
    while ((n = read(fd, buf, sizeof(buf))) > 0) {
        process(buf, n);
    }
    if (n == -1 && errno != EAGAIN && errno != EWOULDBLOCK) {
        perror("read");
        close(fd);
    }
    // n == -1, errno == EAGAIN: buffer drained, all good
}

// ─── EPOLLONESHOT ──────────────────────────────────────────────────
// After one event is delivered, the fd is disabled (not removed).
// Use in multi-threaded event loops to prevent multiple threads
// from receiving the same event simultaneously.
ev.events = EPOLLIN | EPOLLONESHOT | EPOLLET;
// After handling, re-arm with:
epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);  // Re-enable

// ─── EPOLLET + EPOLLONESHOT IS THE PRODUCTION PATTERN ─────────────
// Used by nginx, libuv, tokio, and every serious event loop.
```

**epoll Internal Architecture:**
```
KERNEL INTERNAL STRUCTURE:
┌─────────────────────────────────────────────────────────────────┐
│  epoll instance (eventpoll struct)                              │
│  ┌─────────────────┐   ┌─────────────────────────────────────┐ │
│  │  rbr             │   │  rdllist (ready list)               │ │
│  │  (Red-Black Tree)│   │  ┌──────┐ ┌──────┐ ┌──────┐       │ │
│  │  All monitored   │   │  │ epitem│→│epitem│→│epitem│       │ │
│  │  fds stored here │   │  └──────┘ └──────┘ └──────┘       │ │
│  └─────────────────┘   └─────────────────────────────────────┘ │
│                                                                  │
│  When fd becomes ready:                                          │
│    file->f_op->poll() → ep_poll_callback() → add to rdllist     │
│    wake up threads blocked in epoll_wait()                       │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 io_uring — The Modern Model

io_uring achieves true zero-syscall I/O on the fast path via shared memory ring buffers between
userspace and the kernel. Understanding the ring buffer design is essential.

```
io_uring ARCHITECTURE:

Userspace                        Kernel
┌──────────────────────────────────────────────────────────┐
│                    SHARED MEMORY (mmap'd)                 │
│  ┌─────────────────────────┐  ┌───────────────────────┐  │
│  │  SQ (Submission Queue)  │  │  CQ (Completion Queue)│  │
│  │                         │  │                        │  │
│  │  ┌─────┬─────┬─────┐   │  │  ┌─────┬─────┬─────┐  │  │
│  │  │SQE 0│SQE 1│SQE 2│   │  │  │CQE 0│CQE 1│CQE 2│  │  │
│  │  └─────┴─────┴─────┘   │  │  └─────┴─────┴─────┘  │  │
│  │                         │  │                        │  │
│  │  sq_tail (user writes)  │  │  cq_head (user reads)  │  │
│  │  sq_head (kernel reads) │  │  cq_tail (kernel write)│  │
│  └─────────────────────────┘  └───────────────────────┘  │
└──────────────────────────────────────────────────────────┘

FLOW:
1. User writes SQEs (submission queue entries) to SQ
2. User calls io_uring_enter() OR kernel polls (SQPOLL mode)
3. Kernel processes SQEs, performs I/O async
4. Kernel writes CQEs (completion queue entries) to CQ
5. User reads CQEs to get results — NO SYSCALL NEEDED
```

```c
#include <liburing.h>  // liburing wrapper

// ─── SETUP ─────────────────────────────────────────────────────────
struct io_uring ring;
io_uring_queue_init(
    256,        // queue depth (SQ/CQ size)
    &ring,
    0           // flags: IORING_SETUP_SQPOLL for kernel polling
);

// ─── SUBMIT READ ───────────────────────────────────────────────────
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe,
    fd,           // file descriptor
    buf,          // user buffer
    sizeof(buf),  // length
    0             // offset (-1 for stream)
);
sqe->user_data = (uint64_t)my_context;  // Tag with context pointer

io_uring_submit(&ring);  // Submit all pending SQEs (one syscall for N operations)

// ─── WAIT FOR COMPLETIONS ──────────────────────────────────────────
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);  // Block until one completion

if (cqe->res < 0) {
    fprintf(stderr, "I/O error: %s\n", strerror(-cqe->res));
} else {
    process_data(buf, cqe->res, (context_t *)cqe->user_data);
}
io_uring_cqe_seen(&ring, cqe);  // Advance CQ head

// ─── PEEK WITHOUT BLOCKING ─────────────────────────────────────────
while (io_uring_peek_cqe(&ring, &cqe) == 0) {
    handle_completion(cqe);
    io_uring_cqe_seen(&ring, cqe);
}

// ─── VECTORED / LINKED OPERATIONS ─────────────────────────────────
// Link operations: next SQE only runs if this one succeeds
sqe->flags |= IOSQE_IO_LINK;

// ─── FIXED BUFFERS (zero-copy) ─────────────────────────────────────
// Pre-register buffers with kernel → no copy on submit
struct iovec iovecs[N_BUFS];
io_uring_register_buffers(&ring, iovecs, N_BUFS);
io_uring_prep_read_fixed(sqe, fd, buf, len, 0, buf_index);

// ─── SQPOLL MODE (zero syscall) ────────────────────────────────────
struct io_uring_params params = {
    .flags = IORING_SETUP_SQPOLL,
    .sq_thread_idle = 10000  // Kernel thread sleeps after 10s idle
};
io_uring_queue_init_params(256, &ring, &params);
// Now io_uring_submit() is not needed — kernel thread polls SQ
// Requires CAP_SYS_NICE or RLIMIT_NICE adjustment

io_uring_queue_exit(&ring);
```

### 5.4 epoll vs io_uring vs select/poll — Comparison

```
┌────────────────┬──────────────┬───────────────┬──────────────┐
│  Feature       │  select/poll │  epoll        │  io_uring    │
├────────────────┼──────────────┼───────────────┼──────────────┤
│  Scalability   │  O(n) fds    │  O(1) events  │  O(1) events │
│  Fd limit      │  1024 (sel.) │  Unlimited    │  Unlimited   │
│  File types    │  Sockets only│  Sockets+files│  All files   │
│  Read/Write    │  Notify only │  Notify only  │  Actual I/O  │
│  Syscalls/op   │  1/wait      │  1/wait       │  0 (SQPOLL)  │
│  Zero-copy     │  No          │  No           │  Yes (fixed) │
│  Kernel copy   │  fd_set      │  Kernel state │  Ring buffers│
│  Operations    │  I/O notify  │  I/O notify   │  I/O + ops   │
│  Linked ops    │  No          │  No           │  Yes         │
│  Timeouts      │  Yes         │  Yes          │  Yes (SQE)   │
│  Cross-process │  Yes (mmap)  │  Yes (fd pass)│  Planned     │
│  Kernel ver.   │  Ancient     │  2.6+         │  5.1+        │
│  Complexity    │  Low         │  Medium       │  High        │
└────────────────┴──────────────┴───────────────┴──────────────┘
```

**io_uring operations beyond I/O:**
```
IORING_OP_NOP              ─ No-op (test)
IORING_OP_READV            ─ readv()
IORING_OP_WRITEV           ─ writev()
IORING_OP_FSYNC            ─ fsync()
IORING_OP_READ_FIXED       ─ read with pre-registered buffer
IORING_OP_WRITE_FIXED      ─ write with pre-registered buffer
IORING_OP_POLL_ADD         ─ add poll monitor (replaces epoll!)
IORING_OP_POLL_REMOVE      ─ remove poll monitor
IORING_OP_SYNC_FILE_RANGE  ─ sync_file_range()
IORING_OP_SENDMSG          ─ sendmsg()
IORING_OP_RECVMSG          ─ recvmsg()
IORING_OP_TIMEOUT          ─ arm a timeout
IORING_OP_TIMEOUT_REMOVE   ─ remove timeout
IORING_OP_ACCEPT           ─ accept()
IORING_OP_ASYNC_CANCEL     ─ cancel pending operation
IORING_OP_CONNECT          ─ connect()
IORING_OP_FALLOCATE        ─ fallocate()
IORING_OP_OPENAT           ─ openat()
IORING_OP_CLOSE            ─ close()
IORING_OP_STATX            ─ statx()
IORING_OP_READ             ─ read()
IORING_OP_WRITE            ─ write()
IORING_OP_SPLICE           ─ splice()
IORING_OP_SEND             ─ send()
IORING_OP_RECV             ─ recv()
IORING_OP_SOCKET           ─ socket()  (kernel 5.19+)
```

### 5.5 Signal-Based Async Notification (Signals as Events)

```c
#include <signal.h>
#include <sys/signalfd.h>

// ─── signalfd: signals as file descriptors ─────────────────────────
// Convert signals to readable events — use with epoll!
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGINT);
sigaddset(&mask, SIGTERM);
sigaddset(&mask, SIGCHLD);

// Block these signals from default delivery
sigprocmask(SIG_BLOCK, &mask, NULL);

// Create a file descriptor that becomes readable when signals arrive
int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);

// Add to epoll
epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &(struct epoll_event){
    .events = EPOLLIN,
    .data.fd = sfd
});

// Read signal info
struct signalfd_siginfo si;
read(sfd, &si, sizeof(si));
printf("Got signal %u from PID %u\n", si.ssi_signo, si.ssi_pid);

// ─── eventfd: integer counter as event source ──────────────────────
#include <sys/eventfd.h>
int efd = eventfd(0,               // initial value
                  EFD_NONBLOCK     // non-blocking
                  | EFD_CLOEXEC
                  | EFD_SEMAPHORE  // each read decrements by 1 (semaphore mode)
                                   // without EFD_SEMAPHORE: read returns and resets to 0
);

// Thread A: signal
uint64_t v = 1;
write(efd, &v, 8);  // Increment counter

// Thread B (or via epoll): wait and receive
uint64_t val;
read(efd, &val, 8); // Returns current count, resets to 0 (or -1 with EFD_SEMAPHORE)
```

---

## 6. Memory Ordering and the Memory Model

### 6.1 Why Memory Ordering Exists

Modern CPUs and compilers reorder operations for performance. Without explicit ordering constraints,
concurrent code that "looks correct" to a human will produce undefined behavior.

```
THE PROBLEM — Store-Load Reordering:

Thread 1:                   Thread 2:
  x = 1;                      y = 1;
  print(y);                   print(x);

Possible outputs with reordering: 0 0 (both see initial values)
This is not possible on a sequential machine, but it IS on x86/ARM!

x86: Total Store Order (TSO) — stores are buffered in store buffer
     Loads can be reordered ahead of stores (from other CPUs' perspective)
     
ARM: Weakly ordered — nearly any reorder is possible
     Requires explicit barriers for almost everything
```

### 6.2 C11 Memory Orders

```c
#include <stdatomic.h>

// The six memory orders (from weakest to strongest):

// memory_order_relaxed
//   No ordering constraints beyond atomicity.
//   Only guarantees: this operation is atomic.
//   Use: statistics counters, sequence numbers (no data dependency)
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);

// memory_order_consume
//   Like acquire, but only for data-dependent operations.
//   Rarely useful; compilers often treat as acquire.
//   Avoid in new code.

// memory_order_acquire
//   On a LOAD: no reads/writes in current thread can be reordered
//              to appear BEFORE this load.
//   Pairs with: release stores.
//   Use: lock acquisition, reading a "published" pointer.
void *ptr = atomic_load_explicit(&shared_ptr, memory_order_acquire);

// memory_order_release
//   On a STORE: no reads/writes in current thread can be reordered
//               to appear AFTER this store.
//   Pairs with: acquire loads.
//   Use: lock release, "publishing" data for another thread.
atomic_store_explicit(&shared_ptr, new_ptr, memory_order_release);

// memory_order_acq_rel
//   Combined acquire + release for read-modify-write operations.
//   Use: atomic_fetch_add, atomic_compare_exchange in the middle of a chain.
atomic_fetch_add_explicit(&x, 1, memory_order_acq_rel);

// memory_order_seq_cst
//   Strongest. All threads see ALL seq_cst operations in the same total order.
//   Includes a full memory barrier on most architectures.
//   Default when you use atomic_load/store without explicit order.
//   Use: when you need global ordering guarantees across multiple atomics.
atomic_store_explicit(&x, 1, memory_order_seq_cst);

// ─── ACQUIRE-RELEASE PAIRING EXAMPLE ──────────────────────────────
// This is the fundamental pattern for "publishing" data:

_Atomic int ready = 0;
int data[1024];  // Non-atomic data

// Publisher thread:
void publish(void) {
    data[0] = 42;                     // Write data
    data[1] = 100;                    // Write data
    // Release: all writes above are visible before ready=1
    atomic_store_explicit(&ready, 1, memory_order_release);
}

// Consumer thread:
void consume(void) {
    // Acquire: if we see ready==1, all writes before release are visible
    while (!atomic_load_explicit(&ready, memory_order_acquire))
        ; // spin
    // Safe to read data[] here
    assert(data[0] == 42);   // Always true
    assert(data[1] == 100);  // Always true
}
```

### 6.3 Hardware Barriers

```c
// Compiler barrier: prevents compiler reordering, NOT CPU reordering
#define compiler_barrier() __asm__ volatile("" ::: "memory")

// Full memory barrier (CPU + compiler): all loads/stores before
// are complete before any loads/stores after
#define smp_mb()   __asm__ volatile("mfence" ::: "memory")  // x86
#define smp_mb()   __asm__ volatile("dmb ish" ::: "memory") // ARM64

// Store barrier: all stores before are visible before stores after
#define smp_wmb()  __asm__ volatile("sfence" ::: "memory")  // x86
                   // No-op on TSO x86, but needed for ARM

// Load barrier: all loads before complete before loads after
#define smp_rmb()  __asm__ volatile("lfence" ::: "memory")  // x86

// x86 NOTE: x86 TSO means:
//   - Store→Store reordering: NEVER happens (no sfence needed between stores)
//   - Load→Load reordering:   NEVER happens (no lfence needed between loads)
//   - Store→Load reordering:  CAN happen (mfence needed if ordering required)
//   - Load→Store reordering:  NEVER happens
// This makes x86 the most programmer-friendly architecture.
```

### 6.4 The Happens-Before Relationship

```
DEFINITION: Operation A "happens-before" B if:
  1. A and B are in the same thread, and A appears before B in program order
  2. A is a release operation and B is an acquire operation on the same atomic,
     and B observes the value written by A
  3. Transitivity: if A hb B and B hb C, then A hb C

If NO happens-before relation exists between a write and a concurrent read
of the same non-atomic variable → DATA RACE → UNDEFINED BEHAVIOR

This is why you cannot use regular int* for inter-thread communication
even if the writes are "probably" visible. UB is UB.
```

---

## 7. Lock-Free and Wait-Free Programming

### 7.1 Terminology

```
BLOCKING:    A thread can be delayed indefinitely by other threads.
             (Any mutex-based code is blocking.)

LOCK-FREE:   System-wide progress is guaranteed.
             At least one thread always makes progress.
             Individual threads can starve.

WAIT-FREE:   Every thread completes in a bounded number of steps.
             No thread can starve. Strongest guarantee.
             Extremely hard to implement correctly.

OBSTRUCTION-FREE: A thread makes progress if it runs in isolation.
                  Weakest non-blocking guarantee.
```

### 7.2 Compare-And-Swap: The Foundation of Lock-Free

```c
// CAS: Atomically compare *ptr with expected;
//      if equal, store desired; return true.
//      if not equal, load current value into expected; return false.

_Atomic int x = 0;

int expected = 0;
int desired  = 1;

if (atomic_compare_exchange_strong_explicit(
        &x, &expected, desired,
        memory_order_acq_rel,   // success order
        memory_order_acquire    // failure order
)) {
    // CAS succeeded: x was 0, now 1
} else {
    // CAS failed: expected now holds the actual value of x
    printf("x was actually %d\n", expected);
}

// ─── WEAK vs STRONG ────────────────────────────────────────────────
// strong: Never fails spuriously. More expensive on some architectures.
// weak:   May fail spuriously (returns false even if *ptr == expected).
//         Use in retry loops — allows compiler to generate better code on ARM.

// Retry loop (the standard lock-free pattern):
int expected_val;
do {
    expected_val = atomic_load_explicit(&x, memory_order_relaxed);
    // compute new_val from expected_val
} while (!atomic_compare_exchange_weak_explicit(
    &x, &expected_val, new_val,
    memory_order_release,
    memory_order_relaxed
));
```

### 7.3 Lock-Free Stack (Treiber Stack)

```c
typedef struct node {
    int          value;
    struct node *next;  // Must be pointer, not index, for ABA immunity... sort of
} node_t;

typedef _Atomic(node_t *) atomic_node_ptr;

// The ABA PROBLEM and the solution:
// Thread 1 reads top = A
// Thread 2 pops A, pushes B, pops B, pushes A again (ABA!)
// Thread 1's CAS succeeds — but 'next' might now be garbage!

// Solution 1: Tagged pointers (use high bits of pointer as version counter)
typedef struct {
    node_t *ptr;
    uintptr_t tag;  // Version counter
} tagged_ptr_t;

// Use 128-bit atomic (CMPXCHG16B on x86-64)
typedef struct {
    node_t   *ptr;
    uint64_t  tag;
} __attribute__((aligned(16))) tagged_stack_head;

_Atomic tagged_stack_head stack_head = {NULL, 0};

void stack_push(node_t *node) {
    tagged_stack_head old_head, new_head;
    do {
        old_head = atomic_load(&stack_head);
        node->next = old_head.ptr;
        new_head.ptr = node;
        new_head.tag = old_head.tag + 1;  // Increment tag — prevents ABA
    } while (!atomic_compare_exchange_weak(&stack_head, &old_head, new_head));
}

node_t *stack_pop(void) {
    tagged_stack_head old_head, new_head;
    do {
        old_head = atomic_load(&stack_head);
        if (old_head.ptr == NULL) return NULL;
        new_head.ptr = old_head.ptr->next;
        new_head.tag = old_head.tag + 1;
    } while (!atomic_compare_exchange_weak(&stack_head, &old_head, new_head));
    return old_head.ptr;
}
```

### 7.4 Michael-Scott Lock-Free Queue

```c
// Non-blocking MPMC (multi-producer, multi-consumer) queue
// Used in Java's java.util.concurrent.ConcurrentLinkedQueue

typedef struct ms_node {
    _Atomic int           value;
    _Atomic(struct ms_node *) next;
} ms_node_t;

typedef struct {
    _Atomic(ms_node_t *) head;  // Consumers dequeue from head
    _Atomic(ms_node_t *) tail;  // Producers enqueue at tail
} ms_queue_t;

void ms_queue_init(ms_queue_t *q) {
    ms_node_t *sentinel = calloc(1, sizeof(ms_node_t));
    atomic_init(&sentinel->next, NULL);
    atomic_init(&q->head, sentinel);
    atomic_init(&q->tail, sentinel);
}

void ms_enqueue(ms_queue_t *q, int value) {
    ms_node_t *node = malloc(sizeof(ms_node_t));
    atomic_init(&node->value, value);
    atomic_init(&node->next, NULL);

    ms_node_t *tail, *next;
    while (1) {
        tail = atomic_load_explicit(&q->tail, memory_order_acquire);
        next = atomic_load_explicit(&tail->next, memory_order_acquire);

        if (tail == atomic_load_explicit(&q->tail, memory_order_acquire)) {
            if (next == NULL) {
                // Tail is pointing to last node → try to link new node
                if (atomic_compare_exchange_weak_explicit(
                        &tail->next, &next, node,
                        memory_order_release, memory_order_relaxed)) {
                    break;  // Enqueue done
                }
            } else {
                // Tail is lagging — advance it
                atomic_compare_exchange_weak_explicit(
                    &q->tail, &tail, next,
                    memory_order_release, memory_order_relaxed);
            }
        }
    }
    // Try to advance tail (may fail if another thread does it first — OK)
    atomic_compare_exchange_weak_explicit(
        &q->tail, &tail, node,
        memory_order_release, memory_order_relaxed);
}
```

---

## 8. Rust: Ownership as the Synchronization Primitive

### 8.1 The Rust Guarantee: No Data Races at Compile Time

Rust's ownership system makes data races **impossible to compile** (in safe code). Understanding why
requires understanding the two key marker traits:

```rust
// Send: Safe to TRANSFER to another thread
// Sync: Safe to SHARE REFERENCES across threads (T is Sync iff &T is Send)

// Types and their Send/Sync status:
// i32, f64, bool, String          → Send + Sync  (trivially safe)
// Vec<T> where T: Send            → Send (ownership transfer OK)
// Arc<T> where T: Sync            → Send + Sync (reference counting)
// Mutex<T> where T: Send          → Send + Sync (guards access)
// Rc<T>                           → !Send, !Sync (single-thread only)
// Cell<T>, RefCell<T>             → Send (if T:Send), but NOT Sync
// *mut T (raw pointer)            → !Send, !Sync (opt out of safety)
// MutexGuard<'_, T>               → !Send (can't send guard to another thread)
```

**The fundamental split:**
```
┌────────────────────┬──────────────────────────────────────────┐
│  Interior Mutability│  External Mutability                    │
│  (Single-threaded) │  (Multi-threaded)                        │
├────────────────────┼──────────────────────────────────────────┤
│  Cell<T>           │  Mutex<T>                                │
│  RefCell<T>        │  RwLock<T>                               │
│  OnceCell<T>       │  Atomic* types                           │
│                    │  Arc<Mutex<T>>                           │
│  Checked at RUNTIME│  Checked at COMPILE TIME (mostly)        │
└────────────────────┴──────────────────────────────────────────┘
```

### 8.2 Mutex and RwLock in Rust

```rust
use std::sync::{Arc, Mutex, RwLock, MutexGuard};
use std::thread;

// ─── BASIC MUTEX ───────────────────────────────────────────────────
let counter = Arc::new(Mutex::new(0i64));

let handles: Vec<_> = (0..8).map(|_| {
    let counter = Arc::clone(&counter);
    thread::spawn(move || {
        // lock() returns Result<MutexGuard> — can fail if previous holder panicked
        let mut guard: MutexGuard<i64> = counter.lock().unwrap();
        *guard += 1;
        // guard is dropped here → mutex unlocked automatically (RAII)
    })
}).collect();

for h in handles { h.join().unwrap(); }
println!("{}", *counter.lock().unwrap());  // 8

// ─── POISON HANDLING ───────────────────────────────────────────────
// If a thread panics while holding a Mutex, the Mutex becomes "poisoned".
// Subsequent lock() calls return Err(PoisonError<MutexGuard>).
// You can still recover the guard:
match mutex.lock() {
    Ok(guard) => use_guard(guard),
    Err(poisoned) => {
        let guard = poisoned.into_inner(); // Recover the guard
        // Fix the potentially-inconsistent state
        use_guard(guard);
    }
}

// ─── RWLOCK ────────────────────────────────────────────────────────
let db: Arc<RwLock<HashMap<String, String>>> = Arc::new(RwLock::new(HashMap::new()));

// Multiple readers simultaneously:
let readers: Vec<_> = (0..4).map(|_| {
    let db = Arc::clone(&db);
    thread::spawn(move || {
        let read_guard = db.read().unwrap();  // Multiple allowed
        println!("{:?}", read_guard.get("key"));
        // read_guard dropped → read lock released
    })
}).collect();

// Single writer (blocks until all readers done):
{
    let mut write_guard = db.write().unwrap();  // Exclusive
    write_guard.insert("key".to_string(), "value".to_string());
}   // write_guard dropped → write lock released

// ─── TRY_LOCK ──────────────────────────────────────────────────────
match mutex.try_lock() {
    Ok(guard) => { /* got lock immediately */ }
    Err(_)    => { /* lock was held, don't block */ }
}

// ─── PARKING_LOT: The drop-in better Mutex ─────────────────────────
// parking_lot::Mutex is faster (no poison), smaller, and supports:
// - lock_for (timeout), try_lock_for, try_lock_until
// - fair unlocking (wake the longest-waiting thread)
use parking_lot::{Mutex, RwLock, Condvar};
let m = Mutex::new(0);
let guard = m.lock();  // Infallible — no Result
```

### 8.3 Rust Atomic Operations

```rust
use std::sync::atomic::{AtomicI64, AtomicBool, AtomicPtr, Ordering};
use std::sync::Arc;

let counter = Arc::new(AtomicI64::new(0));

// ─── BASIC OPERATIONS ──────────────────────────────────────────────
counter.fetch_add(1, Ordering::Relaxed);    // Atomic increment
counter.fetch_sub(1, Ordering::Relaxed);    // Atomic decrement
counter.fetch_and(0xFF, Ordering::SeqCst);  // Atomic AND
counter.fetch_or(0x01, Ordering::Release);  // Atomic OR
counter.fetch_xor(0x0F, Ordering::AcqRel);
counter.swap(42, Ordering::Relaxed);        // Exchange, return old value
counter.load(Ordering::Acquire);            // Read
counter.store(42, Ordering::Release);       // Write

// ─── ORDERING MAP (Rust → C11) ─────────────────────────────────────
// Ordering::Relaxed   →  memory_order_relaxed
// Ordering::Acquire   →  memory_order_acquire   (loads only)
// Ordering::Release   →  memory_order_release   (stores only)
// Ordering::AcqRel    →  memory_order_acq_rel   (RMW ops)
// Ordering::SeqCst    →  memory_order_seq_cst

// ─── COMPARE-AND-SWAP ──────────────────────────────────────────────
let x = AtomicI64::new(0);

// compare_exchange: strong (never spuriously fails)
match x.compare_exchange(
    0,                  // expected
    1,                  // desired
    Ordering::AcqRel,  // success ordering
    Ordering::Acquire  // failure ordering
) {
    Ok(old) => println!("CAS succeeded, old value: {}", old),
    Err(actual) => println!("CAS failed, actual value: {}", actual),
}

// compare_exchange_weak: may fail spuriously (use in loops)
let mut expected = 0i64;
loop {
    match x.compare_exchange_weak(expected, expected + 1,
                                  Ordering::AcqRel, Ordering::Relaxed) {
        Ok(_)  => break,
        Err(e) => expected = e,  // Update expected and retry
    }
}

// ─── SPINLOCK IMPLEMENTED WITH ATOMICS ─────────────────────────────
use std::hint;
struct SpinLock(AtomicBool);

impl SpinLock {
    fn new() -> Self { SpinLock(AtomicBool::new(false)) }

    fn lock(&self) {
        while self.0.compare_exchange_weak(
            false, true,
            Ordering::Acquire,
            Ordering::Relaxed
        ).is_err() {
            // Spin: yield to avoid wasting bus bandwidth
            while self.0.load(Ordering::Relaxed) {
                hint::spin_loop(); // PAUSE instruction on x86
            }
        }
    }

    fn unlock(&self) {
        self.0.store(false, Ordering::Release);
    }
}

// ─── SEQLOCK IN RUST ───────────────────────────────────────────────
struct SeqLock<T> {
    seq: AtomicUsize,
    data: UnsafeCell<T>,
}

unsafe impl<T: Send> Sync for SeqLock<T> {}

impl<T: Copy> SeqLock<T> {
    fn read(&self) -> T {
        loop {
            let seq1 = self.seq.load(Ordering::Acquire);
            if seq1 & 1 != 0 {
                hint::spin_loop();
                continue; // Writer in progress
            }
            let data = unsafe { *self.data.get() };
            let seq2 = self.seq.load(Ordering::Acquire);
            if seq1 == seq2 { return data; } // No write occurred
            // else: retry
        }
    }

    fn write(&self, val: T) {
        // Increment seq (even→odd = write in progress)
        let seq = self.seq.fetch_add(1, Ordering::Release);
        assert!(seq & 1 == 0, "concurrent writers");
        unsafe { *self.data.get() = val; }
        // Increment seq (odd→even = write done)
        self.seq.fetch_add(1, Ordering::Release);
    }
}
```

### 8.4 Channels in Rust

```rust
use std::sync::mpsc;  // Multi-Producer, Single-Consumer

// ─── SYNCHRONOUS (RENDEZVOUS) CHANNEL ─────────────────────────────
// sync_channel(0): sender BLOCKS until receiver is ready
// sync_channel(N): sender blocks only when buffer is full
let (tx, rx) = mpsc::sync_channel::<i32>(0); // Rendezvous channel

let tx2 = tx.clone(); // Clone for multiple producers
thread::spawn(move || tx.send(1).unwrap());
thread::spawn(move || tx2.send(2).unwrap());
println!("{}", rx.recv().unwrap()); // Blocks until one sender sends

// ─── ASYNCHRONOUS (UNBOUNDED) CHANNEL ─────────────────────────────
// channel(): sender NEVER blocks (unbounded buffer, but heap grows!)
let (tx, rx) = mpsc::channel::<String>();
tx.send("hello".to_string()).unwrap(); // Non-blocking
let msg = rx.recv().unwrap();          // Blocks until message
let msg = rx.try_recv();               // Non-blocking, returns Err if empty
let msg = rx.recv_timeout(Duration::from_secs(1)); // With timeout

// ─── CROSSBEAM-CHANNEL (production use) ───────────────────────────
use crossbeam_channel::{bounded, unbounded, select};

let (s, r) = bounded(100);   // Bounded MPMC channel
let (s2, r2) = unbounded();  // Unbounded MPMC channel

// Select across multiple channels (like Go's select):
select! {
    recv(r) -> msg  => println!("r: {:?}", msg),
    recv(r2) -> msg => println!("r2: {:?}", msg),
    default         => println!("no message ready"),
}

// ─── WHEN TO USE WHICH ─────────────────────────────────────────────
// mpsc::channel       : Simple one-way data flow, acceptable backpressure loss
// mpsc::sync_channel  : Need backpressure, simple case
// crossbeam bounded   : Production MPMC, backpressure, select!
// crossbeam unbounded : When you know sender rate ≤ consumer rate
// Arc<Mutex<VecDeque>>: When you need to peek or have complex access patterns
```

---

## 9. Rust Async/Await — The Complete Internals

### 9.1 What `async fn` Actually Compiles To

```rust
// This source:
async fn fetch_data(url: &str) -> Result<String, Error> {
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    Ok(body)
}

// Desugars to approximately this:
fn fetch_data(url: &str) -> impl Future<Output = Result<String, Error>> + '_ {
    FetchDataFuture::new(url)
}

// The Future trait:
pub trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

pub enum Poll<T> {
    Ready(T),     // Computation complete, value available
    Pending,      // Not ready yet, will be woken up
}
```

**The state machine generated for an async function:**

```rust
// The compiler generates something like this internally:
enum FetchDataState<'a> {
    // Initial state: haven't started
    Start { url: &'a str },
    // Awaiting reqwest::get() — stores the Future we're waiting on
    AwaitingGet {
        url: &'a str,
        get_fut: reqwest::RequestBuilder,
    },
    // Awaiting response.text() — stores response AND the text future
    AwaitingText {
        text_fut: reqwest::ResponseText,
    },
    // Terminal state
    Complete,
}

impl<'a> Future for FetchDataState<'a> {
    type Output = Result<String, Error>;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        loop {
            match &mut *self {
                FetchDataState::Start { url } => {
                    // Transition to AwaitingGet
                    *self = FetchDataState::AwaitingGet { ... };
                }
                FetchDataState::AwaitingGet { get_fut, .. } => {
                    // Poll the inner future
                    match Pin::new(get_fut).poll(cx) {
                        Poll::Ready(Ok(response)) => {
                            // Transition to AwaitingText
                            *self = FetchDataState::AwaitingText { ... };
                        }
                        Poll::Ready(Err(e)) => return Poll::Ready(Err(e)),
                        Poll::Pending => return Poll::Pending,
                        // Waker is set by cx — runtime will call poll() again
                    }
                }
                FetchDataState::AwaitingText { text_fut } => {
                    match Pin::new(text_fut).poll(cx) {
                        Poll::Ready(body) => {
                            *self = FetchDataState::Complete;
                            return Poll::Ready(Ok(body));
                        }
                        Poll::Pending => return Poll::Pending,
                    }
                }
                FetchDataState::Complete => panic!("polled after completion"),
            }
        }
    }
}
```

### 9.2 The Waker and the Executor

```
THE FLOW:
┌─────────────────────────────────────────────────────────────────────┐
│  Executor (Tokio runtime)                                           │
│  ┌──────────────────────────────┐                                   │
│  │  Task Queue (ready to poll)  │                                   │
│  │  [Task A] [Task B] [Task C]  │                                   │
│  └──────────────────────────────┘                                   │
│         │                                                           │
│         ▼ Pop Task A                                                │
│  poll(task_a_future, context_with_waker)                            │
│         │                                                           │
│         ▼                                                           │
│  Returns Poll::Pending                                              │
│         │                                                           │
│         ▼                                                           │
│  Task A is "parked" — NOT in queue                                  │
│  Waker was registered with the I/O source (epoll, etc.)            │
│         │                                                           │
│  ... I/O completes ...                                              │
│         │                                                           │
│         ▼                                                           │
│  waker.wake() called by I/O driver                                  │
│         │                                                           │
│         ▼                                                           │
│  Task A re-added to ready queue                                     │
│  Next: executor polls Task A again                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 Tokio Runtime Architecture

```rust
// ─── MULTI-THREAD RUNTIME (default) ────────────────────────────────
// - N worker threads (default: number of CPU cores)
// - Work-stealing scheduler: idle threads steal tasks from busy threads
// - Uses epoll/io_uring for I/O
// - Best for CPU-heterogeneous workloads

#[tokio::main]  // Expands to: Runtime::new().block_on(main_async())
async fn main() {
    tokio::spawn(async { heavy_compute().await });
}

// ─── EXPLICIT RUNTIME CONFIGURATION ───────────────────────────────
use tokio::runtime;

let rt = runtime::Builder::new_multi_thread()
    .worker_threads(4)               // Pin to 4 workers
    .max_blocking_threads(512)       // For spawn_blocking pool
    .thread_stack_size(2 * 1024 * 1024)
    .enable_all()                    // io + time drivers
    .build()
    .unwrap();

rt.block_on(async { main_logic().await });

// ─── CURRENT-THREAD RUNTIME (single-threaded event loop) ──────────
let rt = runtime::Builder::new_current_thread()
    .enable_all()
    .build()
    .unwrap();

// ─── SPAWN vs SPAWN_BLOCKING ───────────────────────────────────────
// spawn(): for async tasks (non-blocking work)
// spawn_blocking(): for synchronous/blocking work (runs in separate thread pool)
//                  NEVER run blocking I/O inside async fn without spawn_blocking!

let handle = tokio::spawn(async {
    do_async_work().await
});

let result = tokio::task::spawn_blocking(|| {
    // CPU-bound or blocking I/O here — runs in separate thread
    heavy_computation()
}).await.unwrap();

// ─── TOKIO SYNCHRONIZATION PRIMITIVES ─────────────────────────────
use tokio::sync::{Mutex, RwLock, Semaphore, Notify, oneshot, mpsc, broadcast, watch};

// Tokio Mutex: async-aware (doesn't block the thread, yields instead)
let mtx = Arc::new(tokio::sync::Mutex::new(0));
let guard = mtx.lock().await;  // Async! Other tasks run while waiting.

// Semaphore: limit concurrent operations (e.g., max 10 HTTP requests)
let sem = Arc::new(Semaphore::new(10));
let _permit = sem.acquire().await.unwrap();
// permit dropped when _permit goes out of scope

// Notify: signal without data (like condvar)
let notify = Arc::new(Notify::new());
let notify2 = Arc::clone(&notify);
tokio::spawn(async move {
    notify2.notify_one(); // Signal
});
notify.notified().await; // Wait for signal

// oneshot: single value from one sender to one receiver
let (tx, rx) = oneshot::channel::<String>();
tokio::spawn(async move { tx.send("result".into()).unwrap(); });
let result = rx.await.unwrap();

// watch: multiple receivers always see the latest value
let (tx, mut rx) = watch::channel("initial");
tx.send("updated").unwrap();
let val = rx.borrow_and_update();
rx.changed().await.unwrap(); // Wait until value changes

// broadcast: multiple receivers each get all messages
let (tx, mut rx1) = broadcast::channel::<i32>(16); // buffer 16
let mut rx2 = tx.subscribe();
tx.send(42).unwrap();
println!("{}", rx1.recv().await.unwrap());
println!("{}", rx2.recv().await.unwrap());
```

### 9.4 The Pin Requirement

```rust
// WHY Pin<&mut Self>?
//
// When an async fn awaits, it stores local variables IN the future struct.
// If those locals are self-referential (e.g., a pointer to another local),
// moving the struct in memory would invalidate the pointer.
//
// Pin<P> guarantees: the value pointed to by P will NOT be moved in memory.
//
// Example of the problem:
async fn problem() {
    let data = [1u8; 1024];
    let ptr = &data; // ptr points into the stack frame
    some_future.await;
    // Compiler stores `data` and `ptr` in the generated Future struct.
    // If that struct is moved (e.g., Box<dyn Future>), ptr is now dangling!
    println!("{}", ptr[0]); // UNDEFINED BEHAVIOR without Pin
}

// The rule:
// !Unpin types (most async futures) CANNOT be moved after first poll.
// Pin enforces this.

// In practice:
// - Box::pin(future)           : allocate on heap, pin there
// - pin_mut!(future)           : pin on stack (from futures or tokio crate)
// - tokio::pin!(future)        : tokio's stack-pin macro
```

---

## 10. Go: Goroutines, Channels, and the Runtime Scheduler

### 10.1 The Go Runtime Scheduler (GMP Model)

```
G = Goroutine (lightweight coroutine, ~2KB initial stack, grows dynamically)
M = Machine (OS thread, one per CPU core typically)
P = Processor (logical CPU context; holds local runqueue)

ARCHITECTURE:
┌──────────────────────────────────────────────────────────────────┐
│  GOMAXPROCS=4 (4 logical processors)                             │
│                                                                  │
│  P0 [G1][G2][G3]    P1 [G4][G5]    P2 [G6]    P3 []            │
│   │                  │               │           │               │
│  M0 (OS thread)     M1              M2          M3               │
│  (running G1)       (running G4)    (running G6)(idle)          │
│                                                                  │
│  Global Runqueue: [G7][G8][G9] (overflow from local queues)     │
│                                                                  │
│  When P3 has no goroutines:                                      │
│    1. Try to steal from another P's local queue (work-stealing)  │
│    2. Check global runqueue                                       │
│    3. Check I/O poller (netpoller — epoll-based)                 │
│    4. If still nothing, M3 parks (OS thread sleeps)              │
└──────────────────────────────────────────────────────────────────┘
```

**Key properties of goroutines:**
- Initial stack: **2KB** (vs ~1MB for pthreads)
- Stack **grows and shrinks** dynamically (segmented stacks, then contiguous)
- Scheduled **cooperatively** at preemption points (function calls, channel ops, etc.)
- **Asynchronous preemption** added in Go 1.14 (signal-based, no longer needs function call)

### 10.2 Channels — The Primary Synchronization Mechanism

```go
package main

import (
    "fmt"
    "time"
)

// ─── UNBUFFERED CHANNEL (rendezvous) ──────────────────────────────
// Send BLOCKS until receiver is ready.
// Receive BLOCKS until sender is ready.
// Guarantees: sender and receiver synchronize at the channel operation.
ch := make(chan int)    // Unbuffered

go func() {
    ch <- 42            // Blocks until main goroutine receives
}()
val := <-ch             // Blocks until goroutine sends

// ─── BUFFERED CHANNEL ─────────────────────────────────────────────
// Send: blocks only when buffer is FULL
// Receive: blocks only when buffer is EMPTY
ch := make(chan int, 100) // Buffered, capacity 100

ch <- 1   // Non-blocking (buffer not full)
ch <- 2   // Non-blocking
<-ch      // Non-blocking (buffer not empty)

// ─── DIRECTIONAL CHANNELS ─────────────────────────────────────────
func producer(out chan<- int) { out <- 42 }   // Send-only
func consumer(in <-chan int)  { _ = <-in }     // Receive-only

// ─── CLOSE AND RANGE ──────────────────────────────────────────────
ch := make(chan int, 5)
for i := 0; i < 5; i++ { ch <- i }
close(ch)  // Signal no more values; receivers drain remaining, then get zero value

// Two ways to detect close:
val, ok := <-ch  // ok == false means channel closed and drained
for val := range ch { fmt.Println(val) } // Exits when closed+drained

// ─── SELECT: MULTIPLEXING CHANNELS ────────────────────────────────
ch1 := make(chan string)
ch2 := make(chan string)
timer := time.After(5 * time.Second)

select {
case msg := <-ch1:
    fmt.Println("ch1:", msg)
case msg := <-ch2:
    fmt.Println("ch2:", msg)
case <-timer:
    fmt.Println("timeout")
case ch1 <- "response":     // Can also have send cases
    fmt.Println("sent to ch1")
default:                     // Non-blocking: runs if no case is ready
    fmt.Println("nothing ready")
}

// ─── DONE CHANNEL PATTERN (cancellation) ──────────────────────────
done := make(chan struct{})  // struct{}{} is zero-size, no allocation

go func() {
    for {
        select {
        case <-done:
            return  // Cancelled
        case work := <-workQueue:
            process(work)
        }
    }
}()

close(done)  // Broadcasts cancellation to ALL receivers simultaneously
// Closing a channel is the ONLY way to wake multiple goroutines at once

// ─── CHANNEL AS SEMAPHORE ──────────────────────────────────────────
sem := make(chan struct{}, 10)  // Max 10 concurrent goroutines
for _, item := range items {
    sem <- struct{}{}   // Acquire
    go func(item Item) {
        defer func() { <-sem }()  // Release
        processItem(item)
    }(item)
}
// Wait for all to finish:
for i := 0; i < cap(sem); i++ { sem <- struct{}{} }
```

### 10.3 The sync Package — When to Avoid Channels

```go
import "sync"

// ─── MUTEX ─────────────────────────────────────────────────────────
var mu sync.Mutex
var count int

mu.Lock()
count++
mu.Unlock()

// Defer pattern (ensure unlock on panic):
func safe() {
    mu.Lock()
    defer mu.Unlock()
    // critical section
}

// ─── RWMUTEX ───────────────────────────────────────────────────────
var rw sync.RWMutex
var cache = map[string]string{}

func read(key string) string {
    rw.RLock()
    defer rw.RUnlock()
    return cache[key]
}

func write(key, value string) {
    rw.Lock()
    defer rw.Unlock()
    cache[key] = value
}

// ─── ONCE ──────────────────────────────────────────────────────────
var once sync.Once
var instance *Singleton

func getInstance() *Singleton {
    once.Do(func() {
        instance = &Singleton{...}
    })
    return instance
}

// ─── WAITGROUP: Fire and forget with synchronization ───────────────
var wg sync.WaitGroup

for i := 0; i < 10; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        doWork()
    }()
}
wg.Wait()  // Block until all Done() calls

// ─── COND ──────────────────────────────────────────────────────────
var mu sync.Mutex
cond := sync.NewCond(&mu)
ready := false

// Waiter:
mu.Lock()
for !ready {             // Always use for loop, not if
    cond.Wait()          // Atomically release mu + block
}
// ... use condition ...
mu.Unlock()

// Signaler:
mu.Lock()
ready = true
cond.Signal()   // Wake one waiter
// cond.Broadcast() // Wake all waiters
mu.Unlock()

// ─── SYNCMAP: Concurrent-safe map ─────────────────────────────────
var m sync.Map

m.Store("key", "value")
val, ok := m.Load("key")
actual, loaded := m.LoadOrStore("key", "default")  // Atomic
m.Delete("key")
m.Range(func(k, v interface{}) bool {
    fmt.Println(k, v)
    return true  // Return false to stop iteration
})

// sync.Map is optimized for:
//   - Write-once, read-many workloads
//   - Disjoint keys read/written by different goroutines
// NOT a general replacement for map + RWMutex (which is often faster
// when write/read ratio is even)

// ─── ATOMIC ────────────────────────────────────────────────────────
import "sync/atomic"

var x int64
atomic.AddInt64(&x, 1)
atomic.StoreInt64(&x, 42)
val := atomic.LoadInt64(&x)
swapped := atomic.CompareAndSwapInt64(&x, 42, 100)  // Returns bool
old := atomic.SwapInt64(&x, 0)

// Go 1.19+ atomic types:
var atomicX atomic.Int64
atomicX.Store(1)
atomicX.Add(1)
atomicX.CompareAndSwap(2, 3)
```

### 10.4 Context — The Go Cancellation Protocol

```go
import "context"

// Context propagates deadlines, cancellation, and request-scoped values.
// ALWAYS pass Context as the FIRST argument to functions that do I/O.

// ─── CANCELLATION ──────────────────────────────────────────────────
ctx, cancel := context.WithCancel(context.Background())
defer cancel()  // Always call cancel to release resources

go func(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            // ctx.Err() returns context.Canceled or context.DeadlineExceeded
            return
        default:
            doWork()
        }
    }
}(ctx)

cancel()  // Cancel the context — all goroutines using it are notified

// ─── DEADLINE / TIMEOUT ────────────────────────────────────────────
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(5*time.Second))
defer cancel()

// ─── VALUES ────────────────────────────────────────────────────────
type key int
const requestIDKey key = 0

// Set:
ctx = context.WithValue(ctx, requestIDKey, "req-123")

// Get:
if id, ok := ctx.Value(requestIDKey).(string); ok {
    fmt.Println("Request ID:", id)
}

// ─── PASSING TO STANDARD LIBRARY ───────────────────────────────────
// HTTP client:
req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
resp, err := http.DefaultClient.Do(req)
if err != nil {
    if errors.Is(err, context.DeadlineExceeded) { /* timeout */ }
    if errors.Is(err, context.Canceled) { /* cancelled */ }
}

// Database:
rows, err := db.QueryContext(ctx, "SELECT ...")

// gRPC (see gRPC section):
resp, err := client.SomeRPC(ctx, &pb.Request{})
```

### 10.5 Go Memory Model Guarantees

```go
// The Go Memory Model specifies when goroutines are guaranteed to observe
// writes from other goroutines.

// ─── HAPPENS-BEFORE RULES ──────────────────────────────────────────
// Channel send happens-before the corresponding receive completes.
// Channel receive from CLOSED channel happens-after the close.
// sync.Mutex.Lock(): call N happens-after call N-1's Unlock.
// sync.Once.Do: the function call happens-before any Do returns.

// INCORRECT (data race):
var x int
go func() { x = 1 }()
fmt.Println(x)  // May print 0 — no synchronization!

// CORRECT:
var x int
ch := make(chan struct{})
go func() {
    x = 1
    ch <- struct{}{}  // Happens-before receive below
}()
<-ch
fmt.Println(x)  // Guaranteed to print 1

// DETECT RACES AT RUNTIME:
// go test -race ./...
// go run -race main.go
// The race detector uses happens-before graph analysis (ThreadSanitizer)
```

---

## 11. gRPC: Synchronous vs Asynchronous Patterns

### 11.1 gRPC Communication Models

```
gRPC has four RPC types — each with different sync/async characteristics:

┌────────────────────────────────────────────────────────────────────────┐
│ RPC Type            │ Request   │ Response  │ Use Case                 │
├────────────────────────────────────────────────────────────────────────┤
│ Unary               │ Single    │ Single    │ Simple request/response   │
│ Server Streaming    │ Single    │ Stream    │ Large data, events       │
│ Client Streaming    │ Stream    │ Single    │ Upload, telemetry        │
│ Bidirectional       │ Stream    │ Stream    │ Chat, real-time comms    │
└────────────────────────────────────────────────────────────────────────┘
```

**Protocol Buffer definition:**
```protobuf
syntax = "proto3";
package example;

service DataService {
  // Unary: one request, one response
  rpc GetData(DataRequest) returns (DataResponse);

  // Server streaming: one request, stream of responses
  rpc StreamData(DataRequest) returns (stream DataResponse);

  // Client streaming: stream of requests, one response
  rpc UploadData(stream DataRequest) returns (UploadResponse);

  // Bidirectional streaming
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

message DataRequest  { string id = 1; int32 limit = 2; }
message DataResponse { string data = 1; int64 timestamp = 2; }
message ChatMessage  { string user = 1; string text = 2; }
message UploadResponse { int64 bytes_received = 1; }
```

### 11.2 gRPC in Go — Sync and Async Patterns

```go
// ─── SERVER SETUP ──────────────────────────────────────────────────
import (
    "google.golang.org/grpc"
    pb "path/to/proto"
)

type server struct {
    pb.UnimplementedDataServiceServer
}

// Unary handler (synchronous from handler perspective)
func (s *server) GetData(ctx context.Context, req *pb.DataRequest) (*pb.DataResponse, error) {
    // ctx carries deadline/cancellation from client
    if ctx.Err() != nil {
        return nil, status.Error(codes.Canceled, "client cancelled")
    }
    
    // Do work (can call other services, query DB, etc.)
    data, err := fetchFromDB(ctx, req.Id)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "db error: %v", err)
    }
    return &pb.DataResponse{Data: data}, nil
}

// Server streaming handler
func (s *server) StreamData(req *pb.DataRequest, stream pb.DataService_StreamDataServer) error {
    ctx := stream.Context()
    
    for i := 0; i < int(req.Limit); i++ {
        // Check for client cancellation
        if ctx.Err() != nil {
            return status.Error(codes.Canceled, "client disconnected")
        }
        
        chunk := fetchChunk(i)
        if err := stream.Send(&pb.DataResponse{Data: chunk}); err != nil {
            return err  // Client disconnected
        }
    }
    return nil  // Stream complete
}

// Client streaming handler
func (s *server) UploadData(stream pb.DataService_UploadDataServer) error {
    var total int64
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            // Client finished sending
            return stream.SendAndClose(&pb.UploadResponse{BytesReceived: total})
        }
        if err != nil {
            return err
        }
        total += int64(len(req.Data))
        store(req.Data)
    }
}

// Bidirectional streaming
func (s *server) Chat(stream pb.DataService_ChatServer) error {
    for {
        msg, err := stream.Recv()
        if err == io.EOF { return nil }
        if err != nil { return err }
        
        // Process and respond
        resp := processMessage(msg)
        if err := stream.Send(resp); err != nil {
            return err
        }
    }
}

// Start server
func main() {
    lis, _ := net.Listen("tcp", ":50051")
    
    grpcServer := grpc.NewServer(
        grpc.MaxConcurrentStreams(1000),
        grpc.KeepaliveParams(keepalive.ServerParameters{
            MaxConnectionIdle:     15 * time.Second,
            MaxConnectionAge:      30 * time.Second,
            MaxConnectionAgeGrace: 5 * time.Second,
            Time:                  5 * time.Second,
            Timeout:               1 * time.Second,
        }),
    )
    
    pb.RegisterDataServiceServer(grpcServer, &server{})
    grpcServer.Serve(lis)
}
```

```go
// ─── CLIENT PATTERNS ───────────────────────────────────────────────

conn, _ := grpc.Dial(":50051",
    grpc.WithTransportCredentials(insecure.NewCredentials()),
    grpc.WithBlock(),  // Wait for connection on Dial
    grpc.WithDefaultCallOptions(
        grpc.MaxCallRecvMsgSize(1024*1024*10),  // 10MB
    ),
)
defer conn.Close()
client := pb.NewDataServiceClient(conn)

// Unary call (synchronous from caller's perspective, but goroutine-friendly)
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
resp, err := client.GetData(ctx, &pb.DataRequest{Id: "123"})

// ─── CONCURRENT UNARY CALLS ────────────────────────────────────────
// gRPC multiplexes requests over a single TCP connection (HTTP/2 streams).
// Safe to call concurrently — no connection-per-request needed.

results := make(chan *pb.DataResponse, N)
errs    := make(chan error, N)

for _, id := range ids {
    id := id
    go func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        defer cancel()
        resp, err := client.GetData(ctx, &pb.DataRequest{Id: id})
        if err != nil { errs <- err; return }
        results <- resp
    }()
}

// ─── CLIENT-SIDE STREAMING ─────────────────────────────────────────
stream, err := client.UploadData(context.Background())
for _, chunk := range data {
    stream.Send(&pb.DataRequest{Data: chunk})
}
resp, err := stream.CloseAndRecv()

// ─── RECEIVING A SERVER STREAM ─────────────────────────────────────
stream, err := client.StreamData(ctx, &pb.DataRequest{Limit: 100})
for {
    resp, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil   { return err }
    process(resp)
}

// ─── BIDIRECTIONAL STREAM ──────────────────────────────────────────
stream, err := client.Chat(context.Background())

// Send and receive concurrently:
var wg sync.WaitGroup

wg.Add(1)
go func() {    // Sender goroutine
    defer wg.Done()
    for _, msg := range messages {
        stream.Send(msg)
    }
    stream.CloseSend()
}()

// Receiver in this goroutine:
for {
    msg, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil   { return err }
    fmt.Println(msg.Text)
}
wg.Wait()
```

### 11.3 gRPC in C — Core Library (grpc-core)

```c
#include <grpc/grpc.h>
#include <grpc/support/alloc.h>

// gRPC C uses a completion-queue based async model.
// ALL operations are async — you submit work and poll a completion queue.

// ─── SERVER (ASYNC) ────────────────────────────────────────────────
grpc_server *server = grpc_server_create(NULL, NULL);
grpc_completion_queue *cq = grpc_completion_queue_create_for_next(NULL);
grpc_server_register_completion_queue(server, cq, NULL);
grpc_server_add_insecure_http2_port(server, "[::]:50051");
grpc_server_start(server);

// Request a call
grpc_call *call;
grpc_call_details call_details;
grpc_metadata_array request_metadata;
grpc_metadata_array_init(&request_metadata);

grpc_server_request_call(
    server, &call, &call_details, &request_metadata, cq, cq,
    (void *)REQUEST_TAG  // Tag to identify this event
);

// Poll completion queue
grpc_event event = grpc_completion_queue_next(cq, gpr_inf_future(GPR_CLOCK_REALTIME), NULL);
if (event.type == GRPC_OP_COMPLETE && event.tag == (void *)REQUEST_TAG) {
    // A client connected and sent a request
    handle_request(call, &call_details);
}

// ─── CLIENT (ASYNC) ────────────────────────────────────────────────
grpc_channel *channel = grpc_insecure_channel_create("localhost:50051", NULL, NULL);
grpc_completion_queue *cq = grpc_completion_queue_create_for_next(NULL);
grpc_call *call = grpc_channel_create_call(
    channel, NULL, GRPC_PROPAGATE_DEFAULTS, cq,
    grpc_slice_from_static_string("/example.DataService/GetData"),
    NULL, gpr_inf_future(GPR_CLOCK_REALTIME), NULL
);

// Batch operations
grpc_op ops[6];
grpc_metadata_array initial_metadata;
grpc_metadata_array trailing_metadata;
grpc_status_code status;
grpc_slice response_payload_slice;

// Send initial metadata + request + recv response + recv status
ops[0].op = GRPC_OP_SEND_INITIAL_METADATA;
ops[0].data.send_initial_metadata.count = 0;
ops[1].op = GRPC_OP_SEND_MESSAGE;
ops[1].data.send_message.send_message = request_byte_buffer;
ops[2].op = GRPC_OP_SEND_CLOSE_FROM_CLIENT;
ops[3].op = GRPC_OP_RECV_INITIAL_METADATA;
ops[3].data.recv_initial_metadata.recv_initial_metadata = &initial_metadata;
ops[4].op = GRPC_OP_RECV_MESSAGE;
ops[4].data.recv_message.recv_message = &response_byte_buffer;
ops[5].op = GRPC_OP_RECV_STATUS_ON_CLIENT;
ops[5].data.recv_status_on_client.trailing_metadata = &trailing_metadata;
ops[5].data.recv_status_on_client.status = &status;

grpc_call_error error = grpc_call_start_batch(call, ops, 6, (void *)CALL_TAG, NULL);

// Poll:
grpc_event event = grpc_completion_queue_next(cq, deadline, NULL);
```

### 11.4 gRPC in Rust — tonic

```rust
// ─── PROTO-GENERATED CODE ─── (via tonic-build in build.rs)
// tonic::build::compile_protos("proto/service.proto").unwrap();

// ─── SERVER ────────────────────────────────────────────────────────
use tonic::{transport::Server, Request, Response, Status};
use tokio_stream::wrappers::ReceiverStream;

pub mod pb {
    tonic::include_proto!("example");
}

use pb::{data_service_server::{DataService, DataServiceServer}, *};

#[derive(Debug, Default)]
pub struct MyDataService;

#[tonic::async_trait]
impl DataService for MyDataService {
    // Unary
    async fn get_data(&self, req: Request<DataRequest>) -> Result<Response<DataResponse>, Status> {
        let metadata = req.metadata();   // Headers
        let inner = req.into_inner();    // The proto message
        
        if inner.id.is_empty() {
            return Err(Status::invalid_argument("id required"));
        }
        
        Ok(Response::new(DataResponse {
            data: format!("data for {}", inner.id),
            timestamp: 12345,
        }))
    }

    // Server streaming
    type StreamDataStream = ReceiverStream<Result<DataResponse, Status>>;
    
    async fn stream_data(
        &self,
        req: Request<DataRequest>,
    ) -> Result<Response<Self::StreamDataStream>, Status> {
        let (tx, rx) = tokio::sync::mpsc::channel(32);
        let limit = req.into_inner().limit as usize;

        tokio::spawn(async move {
            for i in 0..limit {
                if tx.send(Ok(DataResponse {
                    data: format!("chunk {}", i),
                    timestamp: i as i64,
                })).await.is_err() {
                    break;  // Client disconnected
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }

    // Client streaming
    async fn upload_data(
        &self,
        req: Request<tonic::Streaming<DataRequest>>,
    ) -> Result<Response<UploadResponse>, Status> {
        let mut stream = req.into_inner();
        let mut total = 0i64;
        
        while let Some(chunk) = stream.message().await? {
            total += chunk.data.len() as i64;
        }
        
        Ok(Response::new(UploadResponse { bytes_received: total }))
    }

    // Bidirectional streaming
    type ChatStream = ReceiverStream<Result<ChatMessage, Status>>;
    
    async fn chat(
        &self,
        req: Request<tonic::Streaming<ChatMessage>>,
    ) -> Result<Response<Self::ChatStream>, Status> {
        let mut stream = req.into_inner();
        let (tx, rx) = tokio::sync::mpsc::channel(32);

        tokio::spawn(async move {
            while let Some(msg) = stream.message().await.unwrap() {
                let response = ChatMessage {
                    user: "server".to_string(),
                    text: format!("Echo: {}", msg.text),
                };
                if tx.send(Ok(response)).await.is_err() { break; }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    Server::builder()
        .add_service(DataServiceServer::new(MyDataService::default()))
        .serve(addr)
        .await?;
    Ok(())
}

// ─── CLIENT ────────────────────────────────────────────────────────
use pb::data_service_client::DataServiceClient;
use tokio_stream::iter;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut client = DataServiceClient::connect("http://[::1]:50051").await?;

    // Unary
    let resp = client.get_data(DataRequest { id: "123".into(), limit: 0 }).await?;
    println!("{:?}", resp.into_inner());

    // Consume server stream
    let mut stream = client.stream_data(DataRequest { id: "x".into(), limit: 5 })
        .await?.into_inner();
    while let Some(msg) = stream.message().await? {
        println!("{:?}", msg);
    }

    // Send client stream
    let messages = vec![
        DataRequest { id: "a".into(), limit: 0 },
        DataRequest { id: "b".into(), limit: 0 },
    ];
    let resp = client.upload_data(iter(messages)).await?;
    println!("{:?}", resp.into_inner());

    Ok(())
}
```

### 11.5 gRPC Metadata, Interceptors, and Middleware

```go
// ─── INTERCEPTORS (middleware) ─────────────────────────────────────

// Unary server interceptor:
func loggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    resp, err := handler(ctx, req)  // Call actual handler
    log.Printf("method=%s latency=%v err=%v", info.FullMethod, time.Since(start), err)
    return resp, err
}

grpc.NewServer(grpc.UnaryInterceptor(loggingInterceptor))

// Chain multiple interceptors:
import "google.golang.org/grpc/middleware"
grpc.NewServer(
    grpc.ChainUnaryInterceptor(
        loggingInterceptor,
        authInterceptor,
        rateLimitInterceptor,
    ),
)

// ─── METADATA (headers) ────────────────────────────────────────────
import "google.golang.org/grpc/metadata"

// Send from client:
md := metadata.Pairs(
    "authorization", "Bearer "+token,
    "x-request-id", requestID,
)
ctx := metadata.NewOutgoingContext(ctx, md)
resp, err := client.GetData(ctx, req)

// Receive on server:
md, ok := metadata.FromIncomingContext(ctx)
if ok {
    tokens := md.Get("authorization")
}

// Send from server (trailer / response headers):
grpc.SendHeader(ctx, metadata.Pairs("x-server-id", "srv-1"))
grpc.SetTrailer(ctx, metadata.Pairs("x-processing-time", "12ms"))

// ─── DEADLINES AND TIMEOUTS ────────────────────────────────────────
// gRPC propagates deadlines across service boundaries via HTTP/2 headers.
// Child services automatically inherit and respect parent deadlines.

// Client sets deadline:
ctx, cancel := context.WithDeadline(ctx, time.Now().Add(5*time.Second))
defer cancel()

// Server can check remaining time:
if deadline, ok := ctx.Deadline(); ok {
    remaining := time.Until(deadline)
    if remaining < 100*time.Millisecond {
        return nil, status.Error(codes.DeadlineExceeded, "not enough time")
    }
}
```

### 11.6 gRPC Connection Management and Load Balancing

```go
// ─── KEEPALIVE ─────────────────────────────────────────────────────
import "google.golang.org/grpc/keepalive"

conn, _ := grpc.Dial(target,
    grpc.WithKeepaliveParams(keepalive.ClientParameters{
        Time:                10 * time.Second, // Send ping if idle for 10s
        Timeout:             2 * time.Second,  // Wait 2s for pong
        PermitWithoutStream: true,             // Ping even without active RPCs
    }),
)

// ─── CLIENT-SIDE LOAD BALANCING ────────────────────────────────────
conn, _ := grpc.Dial(
    "dns:///my-service.namespace.svc.cluster.local:50051",
    grpc.WithDefaultServiceConfig(`{
        "loadBalancingPolicy": "round_robin",
        "methodConfig": [{
            "name": [{"service": "example.DataService"}],
            "retryPolicy": {
                "maxAttempts": 3,
                "initialBackoff": "0.1s",
                "maxBackoff": "1s",
                "backoffMultiplier": 2,
                "retryableStatusCodes": ["UNAVAILABLE", "RESOURCE_EXHAUSTED"]
            }
        }]
    }`),
)

// ─── FLOW CONTROL ──────────────────────────────────────────────────
// gRPC uses HTTP/2 flow control at both connection and stream level.
// If a consumer is slow, the server's Send() will block naturally.
// For streaming servers, check stream.Context().Err() to detect slow consumers.

// Custom window size:
grpc.NewServer(
    grpc.InitialWindowSize(1<<20),           // Per-stream: 1MB
    grpc.InitialConnWindowSize(1<<20 * 10),  // Per-connection: 10MB
)
```

---

## 12. When to Use What — Decision Framework

### 12.1 Synchronization Primitive Selection

```
WHICH PRIMITIVE TO USE?

1. Do I need mutual exclusion (one thread at a time)?
   │
   ├── Is the critical section < 10 instructions AND no sleeping inside?
   │   ├── High contention? → Spinlock (carefully!)
   │   └── Low contention?  → Mutex (futex fast path is nearly free)
   │
   ├── Read-heavy, write-rare access pattern?
   │   └── RwLock / sync.RWMutex / parking_lot::RwLock
   │
   ├── Data modified by writers, read locklessly?
   │   └── RCU (kernel) / crossbeam::epoch (userspace)
   │
   └── Just need an atomic counter/flag (no compound data)?
       └── Atomic operations (AtomicI64, atomic_fetch_add, sync/atomic)

2. Do I need to signal/coordinate between threads?
   │
   ├── One-shot event (condition becomes true once)?
   │   ├── Rust: std::sync::OnceLock, tokio::sync::Notify
   │   ├── Go:   sync.Once, close(done)
   │   └── C:    pthread_cond + flag, sem_post(binary semaphore)
   │
   ├── Recurring condition (wait/notify pattern)?
   │   ├── pthread_cond_wait + mutex
   │   ├── sync.Cond (Go)
   │   └── tokio::sync::Notify (Rust async)
   │
   ├── Data passing with flow control?
   │   ├── Go: buffered channel (built-in backpressure)
   │   ├── Rust: crossbeam::bounded or tokio::mpsc
   │   └── C: POSIX semaphore + ring buffer, or kfifo (kernel)
   │
   └── Resource counting (limit concurrency)?
       ├── POSIX semaphore / Go buffered channel / Tokio Semaphore
       └── Rust: tokio::sync::Semaphore or std::sync::Semaphore

3. Do I need async I/O?
   │
   ├── Simple server with many connections, Linux 2.6+?
   │   └── epoll (the baseline; every framework uses this internally)
   │
   ├── High-performance disk I/O, or want zero-copy / zero-syscall?
   │   └── io_uring (Linux 5.1+, kernel 5.10+ for stability)
   │
   ├── Rust application?
   │   └── tokio (uses io_uring via tokio-uring, or epoll via mio)
   │
   ├── Go application?
   │   └── net package (runtime uses epoll internally — transparent to user)
   │
   └── Need max control, C/C++ system code?
       └── liburing directly, or libuv for portable async
```

### 12.2 The "Channels vs Mutex" Debate (Go Context)

```
RULE: Don't communicate by sharing memory; share memory by communicating.
      But this is a guideline, not a law.

USE CHANNELS WHEN:
  ✓ Transferring ownership of data between goroutines
  ✓ Distributing work units to worker goroutines
  ✓ Broadcasting a signal to multiple goroutines (close(done))
  ✓ Implementing pipeline stages (data flows through goroutines)
  ✓ Receiving async results from concurrent operations

USE MUTEX WHEN:
  ✓ Protecting a cache or map accessed by many goroutines
  ✓ Updating a simple struct's fields atomically
  ✓ Wrapping a non-concurrent-safe library (e.g., SQLite connection)
  ✓ Reference counting
  ✓ High-frequency, short critical sections (mutex has less overhead)

CHANNELS HAVE OVERHEAD:
  - Each send/receive: goroutine scheduling, potentially a context switch
  - Channel creation: allocation
  - Closed channel check on every operation
  For tight inner loops updating shared state, mutex is usually faster.

BENCHMARK COMPARISON (nanoseconds/op, approximate):
  sync.Mutex lock/unlock:     ~25 ns (uncontended)
  Channel send/recv (buf=1):  ~50-100 ns
  sync/atomic operation:      ~10-20 ns
  sync.RWMutex read lock:     ~20 ns
```

### 12.3 Async vs Sync I/O Selection

```
┌─────────────────────────────────────────────────────────────────────┐
│                    I/O MODEL DECISION TREE                          │
│                                                                     │
│  How many concurrent connections/requests do you expect?            │
│                                                                     │
│  < 100 ──► Thread-per-connection (blocking I/O + threads)          │
│             Simple, debuggable, no callback hell                    │
│             Cost: 1MB stack per thread = 100MB for 100 threads     │
│                                                                     │
│  100-10,000 ──► Thread pool + async I/O                            │
│                 Fixed thread pool + epoll/io_uring                  │
│                 Languages: Go (transparent), Rust/tokio             │
│                                                                     │
│  10,000+ ──► Full async I/O with minimal threads                   │
│              epoll/io_uring, event-driven, or async runtime        │
│              "C10K problem" territory                               │
│                                                                     │
│  > 1,000,000 ──► io_uring + kernel bypass (DPDK, RDMA)            │
│                  Specialized hardware/kernel paths                  │
└─────────────────────────────────────────────────────────────────────┘

WHEN BLOCKING I/O IS BETTER:
  ✓ Simple scripts, CLI tools
  ✓ Low concurrency (< 100 simultaneous)
  ✓ CPU-bound code (async doesn't help)
  ✓ Code where stack traces/debugging matter
  ✓ Code that calls synchronous C libraries

WHEN ASYNC I/O IS BETTER:
  ✓ High concurrency (thousands of simultaneous connections)
  ✓ I/O bound workloads (waiting on network, disk)
  ✓ Low-latency services (tail latency matters)
  ✓ Microservices making many downstream calls
  ✗ NOT for CPU-bound computation (offload to thread pool)
```

---

## 13. Anti-Patterns and Failure Modes

### 13.1 Deadlock Patterns

```
DEADLOCK: Circular wait on resources.

PATTERN 1: Lock ordering violation
Thread 1: lock(A), lock(B)
Thread 2: lock(B), lock(A)  ← DEADLOCK if both acquire first lock simultaneously

SOLUTION: Always lock in a consistent global order.

PATTERN 2: Lock held across blocking operation (C/Go)
mu.Lock()
result := http.Get(url)  // Blocks for seconds!
mu.Unlock()
// Any other goroutine trying to lock mu is blocked for seconds.
// Solution: Drop lock before blocking; use a local variable for data.

PATTERN 3: Callback called with lock held (C/Rust)
mu.lock();
callback(data);  // If callback tries to acquire same mutex → deadlock
mu.unlock();
// Solution: Copy data, release lock, call callback with copy.

PATTERN 4: Recursive mutex needed but NORMAL mutex used
void function_a() {
    pthread_mutex_lock(&mu);
    function_b();  // function_b also locks mu → DEADLOCK
    pthread_mutex_unlock(&mu);
}
// Solution: Use PTHREAD_MUTEX_RECURSIVE (rarely the right answer;
//           usually indicates design flaw). Better: refactor to not re-lock.

PATTERN 5: Go channel deadlock
ch := make(chan int)
ch <- 1  // Main goroutine blocks — nobody receives! goroutine leak.
// Runtime detects "all goroutines are asleep" → panic: all goroutines are asleep
```

### 13.2 Race Conditions

```go
// PATTERN 1: Check-then-act (TOCTOU)
if _, exists := cache[key]; !exists {
    // Another goroutine could insert here!
    cache[key] = computeExpensive(key)
}
// Fix: Use sync.Map.LoadOrStore(), or hold mutex across both operations.

// PATTERN 2: Goroutine capturing loop variable (pre-Go 1.22)
for _, v := range items {
    go func() {
        process(v)  // v is shared! All goroutines see the LAST value of v
    }()
}
// Fix (pre-1.22): go func(v Item) { process(v) }(v)
// In Go 1.22+: loop variable is per-iteration by default.

// PATTERN 3: Slice/map concurrent modification
var results []Result
for _, item := range items {
    go func(item Item) {
        result := process(item)
        results = append(results, result)  // DATA RACE! slice is shared
    }(item)
}
// Fix: Use channel or mutex to protect append.
```

```rust
// PATTERN 1: Mutex poisoning panic (Rust)
let data = Arc::new(Mutex::new(vec![]));
let data_clone = Arc::clone(&data);

std::thread::spawn(move || {
    let mut guard = data_clone.lock().unwrap();
    guard.push(1);
    panic!("oops");  // Mutex is now poisoned!
}).join().unwrap_err();

// Next lock() returns Err(PoisonError)
let guard = data.lock().unwrap_or_else(|e| e.into_inner());

// PATTERN 2: async fn holding sync Mutex across await point
async fn bad() {
    let mu = std::sync::Mutex::new(0);
    let guard = mu.lock().unwrap();
    some_async_operation().await;  // Guard held across await!
    // During await, the thread is released, but the guard is still held.
    // If another task on same thread tries to lock → deadlock!
    // If multi-threaded runtime, guard is sent to another thread → Send violation (compile error)
    drop(guard);
}
// Fix: Use tokio::sync::Mutex, or drop guard before .await
```

### 13.3 The "Thundering Herd" Problem

```
SCENARIO: 10,000 connections are all waiting on the same epoll fd.
          One new connection arrives.
          epoll wakes ALL 10,000 threads/goroutines.
          Only one can accept() successfully; 9,999 get EAGAIN and go back to sleep.
          This causes massive spurious context switches.

SOLUTIONS:
1. EPOLLONESHOT: Event disabled after delivery; only one thread wakes.
   After handling, re-arm with EPOLL_CTL_MOD.

2. SO_REUSEPORT: Multiple sockets bound to the same port.
   Kernel distributes new connections across sockets.
   Each worker thread has its own socket → no sharing needed.
   
3. accept4() with SOCK_NONBLOCK: Non-blocking accept.
   Workers drain with a loop until EAGAIN.
   
4. Linux 3.9+: SO_REUSEPORT does load balancing in kernel.
   Nginx uses this; each worker process has its own listen socket.
```

### 13.4 Memory Ordering Bugs

```c
// BUG: Insufficient ordering (can happen on ARM, theoretically on x86)
_Atomic int initialized = 0;
data_t *shared_data;

// Thread 1 (initializer):
shared_data = malloc(sizeof(data_t));
shared_data->value = 42;                      // Store to data
atomic_store(&initialized, 1, memory_order_relaxed);  // BUG: relaxed!
// On ARM: the value=42 store may not be visible to Thread 2
// even after Thread 2 sees initialized=1!

// CORRECT:
atomic_store(&initialized, 1, memory_order_release);  // Release fence

// Thread 2:
while (!atomic_load(&initialized, memory_order_acquire)) {} // Acquire fence
// Now guaranteed to see value=42
assert(shared_data->value == 42);  // Always true with correct ordering
```

### 13.5 Goroutine Leaks

```go
// PATTERN 1: Goroutine blocked on channel, sender abandoned
func leak() {
    ch := make(chan int)
    go func() {
        val := <-ch  // Blocks forever if nobody sends!
        process(val)
    }()
    // Return without sending to ch or closing it → goroutine leak
}

// PATTERN 2: Goroutine blocked on send, receiver abandoned
func producerLeak(items []Item) <-chan Result {
    ch := make(chan Result)  // Unbuffered!
    go func() {
        for _, item := range items {
            ch <- process(item)  // Blocks if consumer stops receiving early
        }
    }()
    return ch
}
// If caller only reads first result and returns, producer goroutine leaks.
// Fix: Use context cancellation + select

func producerFixed(ctx context.Context, items []Item) <-chan Result {
    ch := make(chan Result, len(items))  // Buffered, or use context
    go func() {
        defer close(ch)
        for _, item := range items {
            select {
            case ch <- process(item):
            case <-ctx.Done():
                return  // Context cancelled → goroutine exits
            }
        }
    }()
    return ch
}

// Detect goroutine leaks in tests:
import "go.uber.org/goleak"
func TestSomething(t *testing.T) {
    defer goleak.VerifyNone(t)
    // ... test code ...
}
```

---

## 14. Malware and Security Perspective

### 14.1 Synchronization Primitives as Anti-Analysis Techniques

**Elite malware uses synchronization and async patterns as both functional requirements
and anti-analysis mechanisms. Recognizing these patterns is critical for RE work.**

#### Timing-Based Anti-Debug via Synchronization

```c
// PATTERN: Sleep-based sandbox evasion (observed in Emotet, Dridex, many RATs)
// Simple version detectable via sleep acceleration in sandboxes:
Sleep(120000);  // 2 minutes — sandbox expires

// Sophisticated version using synchronization:
// Create an event, wait with timeout, measure elapsed time
HANDLE hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
DWORD start = GetTickCount();
WaitForSingleObject(hEvent, 5000);  // 5 second timeout
DWORD elapsed = GetTickCount() - start;

if (elapsed < 4900) {  // Sandbox accelerated sleep
    // We're being analyzed — exit or go dormant
    ExitProcess(0);
}
// Real machine: elapsed ≈ 5000ms → proceed with malicious activity

// Detection signature in Ghidra:
// Look for: CreateEvent(NULL,*,FALSE,NULL) → WaitForSingleObject → GetTickCount comparison
```

#### Mutex as Infection Marker (Single-Instance Check)

```c
// Named mutex as "already infected" check — classic technique
// Seen in: banking trojans, ransomware (many families check for this)
HANDLE hMutex = CreateMutexA(NULL, TRUE, "Global\\{GUID-HERE}");
if (GetLastError() == ERROR_ALREADY_EXISTS) {
    // Another instance already running → exit silently
    CloseHandle(hMutex);
    ExitProcess(0);
}

// In Ghidra/IDA — detection:
// xref CreateMutexA → check for comparison with ERROR_ALREADY_EXISTS (0xB7)
// The GUID/name is an IOC — pivot it in VirusTotal
```

#### Thread Injection with Synchronization

```c
// Process injection with WaitForSingleObject (standard, used universally):
HANDLE hThread = CreateRemoteThread(hProcess, NULL, 0, 
                                    (LPTHREAD_START_ROUTINE)loadAddr,
                                    NULL, 0, NULL);
// Wait for injection to complete before proceeding
WaitForSingleObject(hThread, INFINITE);
CloseHandle(hThread);

// Ghosting/Herpaderping use SYNCHRONIZATION:
// Section + Event objects to coordinate write→map→delete→execute timing
// The synchronization IS the evasion — race condition with AV scanner
```

#### io_uring as Evasion Vector

```
THREAT: io_uring bypasses many security hooks:
- seccomp filters only see io_uring_enter(), not individual ops
- eBPF socket filters may not see io_uring network ops
- LSM hooks may be incomplete for io_uring paths

APT USE: An implant using io_uring for C2 communication may evade
         seccomp-based container security policies.
         CVE-2023-2598: io_uring privilege escalation
         CVE-2022-29582: io_uring use-after-free

Detection:
  - Audit io_uring_setup() syscalls (uncommon in production workloads)
  - SECCOMP_FILTER: Deny IORING_OP_CONNECT, IORING_OP_SEND explicitly
  - eBPF: Hook io_uring entry points via fentry probes
```

### 14.2 Recognizing Language-Specific Async in Malware

#### Rust Async Malware Signatures (BlackCat/ALPHV)

```
IN DISASSEMBLY — Rust async Future state machines:

1. Large enums with discriminant field at fixed offset
   Look for: switch/jump table on first word of struct at function entry

2. core::future::poll loop:
   - Calls to functions ending in "::poll"
   - Return value checked for 0 (Pending) vs 1 (Ready)

3. Tokio worker thread names:
   STRINGS search: "tokio-runtime-worker"
   
4. Panic handler: "called `Result::unwrap()` on an `Err` value"
   Present in release builds when malware author left unwrap() calls

5. Go-style ABI: Rust doesn't use Windows ABI for async internally
   Cross-function references through function pointers stored in vtable-like structs
   (the Future vtable: poll + drop)

YARA fingerprint:
rule rust_tokio_binary {
    strings:
        $s1 = "tokio-runtime-worker" ascii
        $s2 = "called `Result::unwrap()" ascii
        $s3 = "thread 'main' panicked" ascii
        $s4 = { 48 8B 07 FF 50 ?? }  // call qword ptr [rax+offset] (vtable dispatch)
    condition:
        2 of them
}
```

#### Go Malware Signatures (Sliver, Merlin C2)

```
BINARY ARTIFACTS:
1. pclntab: Go runtime symbol table (present in most Go binaries)
   At fixed offset, contains function name → PC mapping
   Use "go-parser" or "go-strip" tools; Ghidra has Go analyzer

2. Goroutine stacks: Each goroutine has its own stack
   Look for: runtime.newproc, runtime.goexit in call graph

3. Channel operations:
   runtime.chansend1, runtime.chanrecv1 — easily searchable
   
4. String representation: Go strings are (ptr, length) pair
   NOT null-terminated; strings in .data section may lack null bytes

5. Interface dispatch: similar to C++ vtable
   Look for: LEAQ data_section, RAX; MOV [RSP+8], RAX; CALL [RAX]

6. Goroutine leak detection IOC:
   "all goroutines are asleep - deadlock!" in binary → developer debug

Detection rule:
rule golang_binary {
    strings:
        $pclntab = { FF FF FF FB 00 00 }  // pclntab magic (Go 1.18+)
        $go1 = "Go build ID:" ascii
        $go2 = "runtime.goexit" ascii
        $go3 = "goroutine" ascii
    condition:
        any of them
}
```

### 14.3 Forensics: Finding Synchronization Artifacts in Memory

```python
# Volatility 3: Finding mutexes in Windows memory dump

# List all named mutexes:
vol -f memory.dmp windows.handles --types Mutant

# Find named events used by malware:
vol -f memory.dmp windows.handles --types Event

# Look for infection markers:
# Common malware mutex names:
# - GUIDs: {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
# - {BCDFB400-72C1-4E57-8C3E-33F87A3CAAAA} (Emotet variant)
# - "RotorSysMutex", "l3m0n_mutex", "Chrome_WasHere" (various families)

# Process threads and their wait states:
vol -f memory.dmp windows.threads
# Look for threads in WAIT state on Mutant (mutex) objects
# Multiple threads waiting on same mutex → injection/coordination

# Linux: Find futex addresses in memory
# Futex addresses are in user-space — look for stack frames containing
# sys_futex calls with FUTEX_WAIT in /proc/PID/syscall
```

### 14.4 YARA Rules for Async/Sync Malware Patterns

```yara
// Detect synchronization-based sandbox evasion
rule timing_check_sync_evasion {
    meta:
        description = "Sync-based timing check for sandbox evasion"
        mitre_attack = "T1497.003"  // Time-Based Evasion
    strings:
        $create_event = { FF 15 ?? ?? ?? ?? }  // CALL CreateEvent (indirect)
        $wait_obj = "WaitForSingleObject" ascii nocase
        $get_tick  = "GetTickCount" ascii nocase
        $exit_proc = "ExitProcess" ascii nocase
    condition:
        all of them and
        filesize < 10MB
}

// Detect named mutex infection marker
rule named_mutex_infection_marker {
    meta:
        description = "Named mutex used as single-instance check"
        mitre_attack = "T1480"  // Execution Guardrails
    strings:
        $mutex = "CreateMutex" ascii nocase wide
        $already_exists = { B7 00 00 00 }  // ERROR_ALREADY_EXISTS = 0xB7
        $global_prefix = "Global\\" ascii wide
    condition:
        $mutex and $already_exists and $global_prefix
}

// Detect Rust async binary (BlackCat/ALPHV fingerprint)
rule rust_async_ransomware {
    meta:
        description = "Rust binary with tokio async runtime"
        mitre_attack = "T1486"  // Data Encrypted for Impact
    strings:
        $tokio_worker = "tokio-runtime-worker" ascii
        $rust_panic   = "called `Result::unwrap()` on an `Err` value" ascii
        $rust_alloc   = "__rust_alloc" ascii
        $future_poll  = { 48 8B 07 48 89 ?? 24 FF 50 ?? }  // vtable poll dispatch
    condition:
        3 of them
}

// Detect Go C2 framework (Sliver, Merlin)
rule go_c2_framework {
    meta:
        description = "Go-compiled C2 framework binary"
        mitre_attack = "T1071"  // Application Layer Protocol
    strings:
        $go_magic  = { FF FF FF FB }  // pclntab magic
        $go_build  = "Go build ID:" ascii
        $goroutine = "goroutine" ascii
        $chan_send  = "runtime.chansend1" ascii
        $tls_hello = "tls: no supported versions" ascii  // Go net/tls
    condition:
        ($go_magic or $go_build) and
        2 of ($goroutine, $chan_send, $tls_hello)
}
```

---

## 15. Performance Benchmarks and Trade-offs

### 15.1 Synchronization Overhead at Scale

```
BENCHMARK: Protected counter increment, 8 threads, 1M iterations each

Primitive                  │ Total time │ Throughput   │ Notes
───────────────────────────┼────────────┼──────────────┼──────────────────
sync/atomic.AddInt64       │   0.4s     │ 20M ops/s    │ Lock-free, best
std::atomic fetch_add      │   0.4s     │ 20M ops/s    │ Same
Go sync.Mutex + counter++  │   1.2s     │  6.6M ops/s  │ ~3x slower
pthread_mutex              │   1.5s     │  5.3M ops/s  │ Contended futex
Rust Mutex<i64>            │   1.3s     │  6.1M ops/s  │ parking_lot faster
parking_lot::Mutex         │   0.9s     │  8.8M ops/s  │ ~30% faster than std
RwLock (reads only, 8 thr) │   0.2s     │ 40M ops/s    │ No contention → fast
RwLock (write-heavy)       │   3.0s     │  2.6M ops/s  │ Writer starvation risk
Spinlock (8 threads)       │   2.8s     │  2.8M ops/s  │ Wasted CPU cycles
```

### 15.2 I/O Model Benchmark (HTTP Server, 10K Connections)

```
MODEL                      │ RPS      │ P99 Latency │ CPU Usage
───────────────────────────┼──────────┼─────────────┼──────────
Thread-per-conn (blocking) │  5,000   │  200ms      │  85%
Thread pool + epoll        │ 50,000   │   20ms      │  60%
Go net/http (goroutines)   │ 80,000   │   10ms      │  55%
Rust tokio (epoll)         │ 120,000  │    5ms      │  40%
Rust tokio (io_uring)      │ 150,000  │    3ms      │  35%
C epoll + io_uring         │ 200,000  │    2ms      │  30%

Conditions: localhost, 100 byte responses, keep-alive, 8 CPU cores
```

### 15.3 Channel vs Mutex in Go (Specific Patterns)

```go
// Benchmark: shared counter with high contention (8 goroutines)

// Mutex version: ~25ns/op
var mu sync.Mutex
var c int
mu.Lock()
c++
mu.Unlock()

// Atomic version: ~10ns/op
var c atomic.Int64
c.Add(1)

// Channel version: ~80ns/op
type cmd struct{}
ch := make(chan cmd, 1)
// ... send/recv overhead ...

// CONCLUSION: Use atomic for simple counters.
//             Use mutex for compound state.
//             Use channels for data transfer and coordination.
//             Never use channels for simple counters (3-8x overhead).
```

---

## 16. Reference Tables

### 16.1 Complete Primitive Comparison

```
┌────────────────────┬──────────┬──────────┬───────────┬────────────┬──────────────┐
│  Primitive         │  C       │  Rust    │  Go       │  Blocking  │  Use Case    │
├────────────────────┼──────────┼──────────┼───────────┼────────────┼──────────────┤
│  Mutex             │  pthread │  Mutex<T>│  sync.Mu  │  Yes       │  Exclusion   │
│  RwLock            │  pthread │  RwLock  │  RWMutex  │  Yes       │  Read-heavy  │
│  Spinlock          │  custom  │  custom  │  N/A      │  No (spin) │  Short crits │
│  Condvar           │  pthread │  Condvar │  sync.Cnd │  Yes       │  Wait/notify │
│  Semaphore         │  POSIX   │  crate   │  chan{}    │  Yes       │  Counting    │
│  Barrier           │  pthread │  Barrier │  WaitGroup│  Yes       │  Rendezvous  │
│  Atomic            │  C11     │  Atomic* │  sync/atm │  No        │  Simple vals │
│  Lock-free queue   │  custom  │  crossbm │  custom   │  No        │  MPMC queue  │
│  Channel           │  N/A     │  channel │  chan T    │  Varies    │  Data xfer   │
│  RCU               │  kernel  │  epoch   │  N/A      │  No (read) │  Read-heavy  │
│  SeqLock           │  custom  │  custom  │  N/A      │  No (read) │  Freq reads  │
│  futex             │  syscall │  internal│  internal │  Yes       │  Base layer  │
└────────────────────┴──────────┴──────────┴───────────┴────────────┴──────────────┘
```

### 16.2 Async I/O API Comparison

```
┌───────────────────────┬──────────────────────────────────────────────────────┐
│  Operation            │  epoll           │  io_uring        │  Go net       │
├───────────────────────┼──────────────────┼──────────────────┼───────────────┤
│  Create instance      │  epoll_create1() │  io_uring_setup()│  Transparent  │
│  Register fd          │  epoll_ctl(ADD)  │  SQE: POLL_ADD   │  Transparent  │
│  Wait for events      │  epoll_wait()    │  io_uring_enter()│  Transparent  │
│  Actual read          │  read() after    │  SQE: READ       │  net.Conn.Read│
│  Actual write         │  write() after   │  SQE: WRITE      │  net.Conn.Write│
│  Accept connection    │  accept4()       │  SQE: ACCEPT     │  net.Listener │
│  Syscalls per read    │  2 (wait+read)   │  0 (SQPOLL)     │  ~0 (runtime) │
│  Zero-copy support    │  No              │  Yes             │  No           │
│  Linked operations    │  No              │  Yes             │  No           │
│  Kernel version       │  2.6.17+         │  5.1+            │  Any          │
└───────────────────────┴──────────────────┴──────────────────┴───────────────┘
```

### 16.3 MITRE ATT&CK Mapping for Sync/Async Techniques

```
┌──────────────────────────────────────┬────────────┬──────────────────────────┐
│  Technique                           │  ATT&CK ID │  Notes                   │
├──────────────────────────────────────┼────────────┼──────────────────────────┤
│  Mutex as infection marker           │  T1480     │  Execution Guardrails    │
│  Sleep/timing-based evasion          │  T1497.003 │  Time-Based Evasion      │
│  Mutex-based C2 signaling            │  T1205     │  Traffic Signaling       │
│  Thread injection coordination       │  T1055     │  Process Injection       │
│  Event-driven C2 (async model)       │  T1071     │  App Layer Protocol      │
│  Semaphore resource limiting         │  T1629.001 │  Impair Defenses         │
│  io_uring seccomp bypass             │  T1562.001 │  Disable Security Tools  │
│  Goroutine/thread pool for parallel  │  T1047     │  Windows Management Inst │
│  Named pipe async I/O                │  T1559.001 │  Inter-Process Comms     │
│  Async exfiltration (channels)       │  T1048     │  Exfiltration Over C2    │
└──────────────────────────────────────┴────────────┴──────────────────────────┘
```

### 16.4 Sigma Rules for Runtime Detection

```yaml
# Detect named mutex creation patterns used by malware
title: Suspicious Named Mutex Creation
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Named mutex with GUID-like name, common malware infection marker
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        EventID: 4656  # Object handle requested
        ObjectType: 'Mutant'
        ObjectName|re: '\\(Global|Local)\\\\{[0-9A-Fa-f-]{36}}'
    condition: selection
falsepositives:
    - Legitimate software using GUID-named mutexes
level: medium
tags:
    - attack.defense_evasion
    - attack.t1480

---
# Detect io_uring usage in containers (unusual, potential evasion)
title: io_uring Syscall in Container
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: io_uring_setup syscall detected in container - potential seccomp bypass
logsource:
    product: linux
    category: syscall
detection:
    selection:
        syscall: 'io_uring_setup'
        container: true
    condition: selection
falsepositives:
    - Containers running high-performance I/O workloads
level: high
tags:
    - attack.defense_evasion
    - attack.t1562.001
```

---

## The Expert Mental Model — Synthesis

> A top-tier analyst internalizes synchronization and asynchrony as two independent
> dimensions of any system's design, each with a cost-benefit curve that must be
> optimized for the specific workload. Synchronization primitives are not "safety
> switches" to be applied liberally — they are *performance contracts* between
> threads, each with measurable overhead that compounds under contention. The futex
> is the invisible backbone of all user-space locking on Linux; every Mutex in Rust,
> every sync.Mutex in Go, every pthread_mutex in C collapses to futex(2) under
> contention. Async I/O is not "faster code" — it is "more efficient waiting": the
> same CPU cycles, but distributed across more concurrent work units. io_uring
> represents the apex of Linux I/O design, eliminating the syscall boundary for
> steady-state operation while remaining composable with the broader event model.
> From a defensive security perspective, these mechanisms are double-edged: the
> same named mutex that protects shared state in legitimate code becomes an
> infection marker and sandbox evasion tool in malware; the same async I/O that
> makes a server handle 200K RPS allows an implant to bypass seccomp filters. The
> analyst who understands the mechanism deeply will recognize both uses instantly —
> in disassembly, in memory forensics, and in network telemetry. Theory without
> detection is incomplete. Detection without mechanism is fragile. You need both.

---

*Document Version: 1.0 | Covers: Linux 6.x, Rust 1.80+, Go 1.22+, gRPC 1.64+*
*Key References: Linux kernel source, futex(7), io_uring(7), Tokio documentation,*
*"The Linux Programming Interface" (Kerrisk), "Programming Rust" (Blandy/Orendorff)*

Here's the complete guide. Here's a map of everything covered:

**Foundations**
- The two axes (execution model vs waiting model) — why "sync vs async" is the wrong framing
- The five fundamental problems synchronization solves, and the cost hierarchy from L1 cache to thread creation

**Linux Kernel Internals**
- The futex — fast path (atomic CAS, zero syscall) vs slow path (kernel block/wake), and lock word state machine
- RCU (Read-Copy-Update) with timeline diagrams — the most sophisticated primitive in the kernel
- seqlock, spinlock vs mutex decision tree, kernel wait_queue mechanics
- Scheduler internals (CFS, real-time classes, how blocking works at task_struct level)

**POSIX / C**
- Full pthread_mutex API including robust mutexes, priority inheritance, RAII cleanup via `__attribute__((cleanup))`
- pthread_rwlock writer starvation pitfall and the fix
- pthread_cond — why you always use a `while` loop, the missed-wakeup race explained
- POSIX semaphores (named and unnamed), eventfd, signalfd integration with epoll
- User-space spinlocks with `PAUSE` instruction and C11 stdatomic

**Async I/O**
- epoll: level-triggered vs edge-triggered, EPOLLONESHOT, internal red-black tree + ready list architecture
- io_uring: SQ/CQ ring buffer design, fixed buffers, SQPOLL zero-syscall mode, full operation table
- Comparison table: select/poll/epoll/io_uring across 14 dimensions

**Memory Ordering**
- All six C11 memory orders with exact hardware behavior on x86 TSO vs ARM
- Acquire-release pairing pattern, happens-before formal definition
- Hardware barrier instructions per architecture

**Lock-Free Programming**
- CAS retry loop pattern, weak vs strong CAS
- ABA problem and the tagged-pointer solution (CMPXCHG16B)
- Treiber stack and Michael-Scott queue implementations

**Rust**
- Send/Sync trait system — why data races are compile errors
- Mutex, RwLock, parking_lot comparison
- Full atomic operations with Ordering mapping to C11
- async/await state machine desugration — what the compiler actually generates
- Pin requirement explained from first principles
- Tokio runtime (GMP-style), spawn vs spawn_blocking, all sync primitives

**Go**
- GMP scheduler architecture with work-stealing
- Channels (buffered/unbuffered/directional), select, done-channel pattern
- sync package: Mutex, RWMutex, Once, WaitGroup, Cond, Map, atomic
- Context propagation for cancellation/deadlines
- Go memory model happens-before guarantees
- Race detector usage

**gRPC**
- All four RPC types with proto definitions
- Go: server/client for all streaming patterns, interceptors, metadata, deadline propagation
- C: completion queue async model
- Rust/tonic: async trait implementation, ReceiverStream pattern
- Connection management: keepalive, SO_REUSEPORT, load balancing, flow control

**Security & Malware**
- Mutex as infection marker (single-instance check) with Ghidra detection notes
- Sync-based timing evasion (WaitForSingleObject pattern)
- io_uring as seccomp bypass vector (CVE-2023-2598, CVE-2022-29582)
- Rust async binary signatures (BlackCat/ALPHV) and Go binary signatures (Sliver/Merlin)
- YARA rules for all patterns, Sigma rules for runtime detection
- Volatility commands for mutex/event forensics
- MITRE ATT&CK mapping table