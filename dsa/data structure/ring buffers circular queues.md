# Ring Buffers (Circular Queues): A Complete Engineering Guide

> **Scope:** Theory → Memory model → Single-threaded → Lock-based concurrent → Lock-free → SPSC/MPMC → C, Rust, Go implementations → Production hardening → Security checklist → Exercises.

---

## Table of Contents

1. [What Is a Ring Buffer?](#1-what-is-a-ring-buffer)
2. [Why Ring Buffers Exist — The Problem They Solve](#2-why-ring-buffers-exist)
3. [Anatomy and Memory Layout](#3-anatomy-and-memory-layout)
4. [Index Arithmetic — The Core Math](#4-index-arithmetic)
5. [Full vs. Empty Disambiguation Strategies](#5-full-vs-empty-disambiguation-strategies)
6. [Taxonomy of Ring Buffer Designs](#6-taxonomy-of-ring-buffer-designs)
7. [Cache Lines, False Sharing, and Padding](#7-cache-lines-false-sharing-and-padding)
8. [Memory Ordering and the Hardware Memory Model](#8-memory-ordering-and-the-hardware-memory-model)
9. [C Implementation — From Naive to Production](#9-c-implementation)
10. [Rust Implementation — Safe, Unsafe, Lock-Free SPSC, MPMC](#10-rust-implementation)
11. [Go Implementation — Channel Internals, Manual Ring Buffer, Lock-Free SPSC](#11-go-implementation)
12. [Lock-Free MPMC: The Dmitry Vyukov Queue](#12-lock-free-mpmc-the-dmitry-vyukov-queue)
13. [Performance Analysis and Benchmarking](#13-performance-analysis-and-benchmarking)
14. [Real-World Use Cases](#14-real-world-use-cases)
15. [Common Pitfalls and Anti-Patterns](#15-common-pitfalls-and-anti-patterns)
16. [Security Checklist](#16-security-checklist)
17. [Exercises](#17-exercises)
18. [Further Reading](#18-further-reading)

---

## 1. What Is a Ring Buffer?

**One-line explanation:** A ring buffer is a fixed-size array used as a circular FIFO queue by wrapping indices modulo capacity rather than shifting elements.

**Analogy:** Imagine a vinyl record on a turntable. The needle plays one groove at a time. Once it reaches the end, it loops back to the start — but instead of replaying old music, a producer has already written new data into those grooves. The needle (consumer) and the writing head (producer) never stop, they just chase each other around the circle.

**Why "ring"?** Because logically the last slot and the first slot are adjacent. The structure has no beginning or end — only a *head* (read pointer) and a *tail* (write pointer) that lap each other.

### Formal Definition

A ring buffer `RB` of capacity `N` is:
- A contiguous array `buf[0..N-1]`
- A write cursor `tail` (producer advances this)
- A read cursor `head` (consumer advances this)
- The invariant: `0 <= (tail - head) <= N` at all times

Elements live at indices `head % N` through `(tail - 1) % N` inclusive.

---

## 2. Why Ring Buffers Exist — The Problem They Solve

### The Naive Queue Problem

A naive queue backed by a linked list or a dynamic array has serious problems in systems programming:

| Problem | Linked List Queue | Dynamic Array Queue | Ring Buffer |
|---|---|---|---|
| Memory allocation per op | Yes (malloc/free) | Amortized | Never |
| Cache locality | Poor (pointer chasing) | Good on dequeue | Excellent |
| Predictable latency | No (allocator jitter) | No | Yes |
| Memory overhead | High (pointers) | Low | Minimal |
| Lock-free possible | Hard | Hard | Well-studied |
| Bounded memory | No | No | Yes, by design |

### Where Ring Buffers Dominate

- **Kernel I/O:** Linux `io_uring`, network driver rings (e.g., Intel DPDK)
- **Audio/Video:** Real-time pipelines where dropping a frame is better than blocking
- **Logging:** Zero-allocation log queues (e.g., Disruptor, LMAX)
- **IPC:** Shared-memory producer-consumer between processes
- **Networking:** TCP receive/send buffers, packet queues in NICs
- **Embedded systems:** UART FIFOs, sensor data rings

---

## 3. Anatomy and Memory Layout

### Basic Structure

```
Capacity = 8 (must be power of 2 for fast modulo)

Index:  0    1    2    3    4    5    6    7
       +----+----+----+----+----+----+----+----+
buf:   | D  | E  | F  |    |    |    | B  | C  |
       +----+----+----+----+----+----+----+----+
                   ^                   ^
                  tail=3              head=6

Logical queue (reading head→tail, wrapping):
  head=6 → buf[6]=B, buf[7]=C, buf[0]=D, buf[1]=E, buf[2]=F ← tail=3
  Items: [B, C, D, E, F]  count = tail - head = 3 - 6 + 8 = 5
```

### Why Power-of-2 Capacity?

Modulo with arbitrary N requires a division instruction (~20-40 cycles on modern CPUs). Power-of-2 capacity lets you replace:

```c
index = cursor % capacity;   // DIV instruction
```

with:

```c
index = cursor & (capacity - 1);  // AND instruction — 1 cycle
```

This is the single most important micro-optimization in ring buffer design.

### Logical vs. Physical Index

The key insight that eliminates most bugs:

- **Physical index** = `cursor & mask` — where in the array
- **Logical cursor** = raw, ever-incrementing integer — tracks total throughput

Never wrap the cursor itself. Let it overflow (this is intentional with unsigned arithmetic). Only wrap when indexing the array.

```
cursor:   0   1   2   3   4   5   6   7   8   9   10  11  ...
physical: 0   1   2   3   4   5   6   7   0   1    2   3  ...
           <--- first lap --->           <--- second lap --->
```

When `cursor` is `uint64_t`, it overflows after 2^64 operations. At 1 billion ops/sec, that's 584 years. Safe to ignore.

---

## 4. Index Arithmetic

### Count, Space, Full, Empty

Given `head` (read cursor), `tail` (write cursor), capacity `N` (power of 2), mask `M = N - 1`:

```
count  = tail - head          // items available to read   (unsigned subtraction wraps correctly)
space  = N - count            // slots available to write
empty  = (count == 0)
full   = (count == N)
```

**Why does unsigned subtraction work when tail has wrapped?**

Say `N=8`, `head=254`, `tail=2` (tail wrapped past 255 → 0 → 1 → 2).

```
tail - head = 2 - 254 = -252 (signed)
            = 2 + (256 - 254) = 4 (unsigned, mod 256)
```

Unsigned subtraction gives correct `count = 4`. This only works if cursors are unsigned and you never allow `(tail - head) > N`. That invariant must be maintained by the push/pop logic.

### The Masking Trick

```c
buf[tail & mask] = item;   // write
tail++;

item = buf[head & mask];   // read
head++;
```

No branches, no modulo. The mask forces the index into `[0, N-1]`.

---

## 5. Full vs. Empty Disambiguation Strategies

The hardest problem in ring buffer design: when `head == tail`, is the buffer empty or full?

### Strategy 1: Waste One Slot (Most Common)

Reserve one slot as a "gap". Full condition: `(tail + 1) % N == head`. Capacity is effectively `N - 1`.

**Pro:** Simple, no extra state. **Con:** Wastes one slot.

### Strategy 2: Separate Count

Maintain an integer `count`. Full: `count == N`. Empty: `count == 0`.

**Pro:** Full capacity used, unambiguous. **Con:** Extra variable; in concurrent code, `count` must be atomic, which creates contention.

### Strategy 3: Mirror Bit (Preferred for Lock-Free)

Use cursors that count modulo `2N` instead of `N`. The high bit acts as a "lap" indicator.

```
full  = (tail - head) == N
empty = (tail - head) == 0
index = cursor % N  (or cursor & (N-1) if N is power of 2)
```

Physical index: `cursor & (N - 1)`. Lap bit: `(cursor >> log2(N)) & 1`.

**Pro:** Full capacity, no wasted slot, single comparison. **Con:** Slightly more complex mental model.

### Strategy 4: Separate Head/Tail with Sequence Numbers (Vyukov Style)

Each slot has a `sequence` atomic integer. Producer checks `sequence == tail`, consumer checks `sequence == tail + 1`. This is the basis of the most efficient MPMC queues. Covered in detail in section 12.

---

## 6. Taxonomy of Ring Buffer Designs

```
Ring Buffers
├── By thread model
│   ├── Single-threaded (ST)
│   ├── SPSC — Single Producer, Single Consumer (lock-free possible)
│   ├── MPSC — Multiple Producer, Single Consumer
│   ├── SPMC — Single Producer, Multiple Consumer
│   └── MPMC — Multiple Producer, Multiple Consumer
│
├── By synchronization mechanism
│   ├── No sync (ST only)
│   ├── Mutex + Condvar
│   ├── Spinlock
│   └── Lock-free (atomics only)
│
├── By overflow policy
│   ├── Block (backpressure)
│   ├── Drop newest (producer fails)
│   └── Drop oldest (overwrite, "overrun mode")
│
└── By memory layout
    ├── Flat array (cache-friendly)
    ├── Pointer array (indirection, variable sizes)
    └── Shared memory (IPC)
```

---

## 7. Cache Lines, False Sharing, and Padding

This section is critical. Failing to understand it leads to ring buffers that are **slower than a mutex-protected queue**.

### Cache Lines

Modern CPUs load memory in 64-byte chunks called cache lines. If two cores write to different variables that share a cache line, every write invalidates the other core's cache entry. This is **false sharing** and it destroys performance.

### The Classic False Sharing Bug in Ring Buffers

```c
// BAD: head and tail on the same cache line
struct ring {
    uint64_t head;   // consumer writes this
    uint64_t tail;   // producer writes this
    // Both fit in one 64-byte cache line → false sharing!
    void *buf[N];
};
```

Every time the producer increments `tail`, the consumer's cache line for `head` is invalidated, and vice versa. On a busy ring with two cores, this causes a cache ping-pong — hundreds of nanoseconds of latency per operation.

### The Fix: Cache Line Padding

```c
#define CACHE_LINE_SIZE 64
#define CACHE_PAD(n) char _pad##n[CACHE_LINE_SIZE]

struct ring {
    // Consumer's data — lives on its own cache line
    _Alignas(CACHE_LINE_SIZE) uint64_t head;
    CACHE_PAD(0);

    // Producer's data — lives on its own cache line
    _Alignas(CACHE_LINE_SIZE) uint64_t tail;
    CACHE_PAD(1);

    // Shared, read-only after init
    _Alignas(CACHE_LINE_SIZE) void **buf;
    uint64_t mask;
};
```

### Cached Remote Cursor

Even with padding, the producer must occasionally read `head` to check for fullness, and the consumer must read `tail` to check for data. Reading a cache line owned by another core is expensive.

**Optimization:** Cache a local copy of the remote cursor. Only re-read it from the real atomic when the cached value says "full" or "empty".

```c
struct spsc_ring {
    _Alignas(64) atomic_uint64_t head;
    uint64_t _head_pad[7];

    _Alignas(64) atomic_uint64_t tail;
    uint64_t _tail_pad[7];

    _Alignas(64) uint64_t head_cache;  // producer's cached copy of head
    uint64_t tail_cache;               // consumer's cached copy of tail
    uint64_t _cache_pad[6];

    void **buf;
    uint64_t mask;
};
```

This technique alone can double throughput on SPSC queues.

---

## 8. Memory Ordering and the Hardware Memory Model

### Why Memory Ordering Matters

Modern CPUs and compilers reorder memory operations for performance. On x86, this is mostly transparent (x86 is TSO — Total Store Order). On ARM and POWER, reorderings are aggressive and the programmer must insert barriers.

### The Four Orderings (C11 / Rust `std::sync::atomic`)

| Ordering | What it prevents | Cost |
|---|---|---|
| `Relaxed` | Nothing reordered | Cheapest |
| `Acquire` | Subsequent reads/writes can't move before this load | Load barrier |
| `Release` | Prior reads/writes can't move after this store | Store barrier |
| `AcqRel` | Both acquire and release on one RMW op | Both |
| `SeqCst` | Total global order, all threads agree | Most expensive |

### The SPSC Ring Buffer Ordering Contract

For a lock-free SPSC ring buffer:

**Producer:**
1. Write data to `buf[tail & mask]` — ordinary write
2. Store `tail + 1` with **Release** ordering

**Consumer:**
1. Load `tail` with **Acquire** ordering
2. Read data from `buf[head & mask]` — ordinary read
3. Store `head + 1` with **Release** ordering

The Release store on `tail` "publishes" the written data. The Acquire load on `tail` "subscribes" to that publication. This creates a happens-before relationship: all writes before the Release are visible after the Acquire.

**Why not SeqCst?** On ARM, SeqCst requires a full memory barrier (DMB ISH), which is ~10x more expensive than Release/Acquire. For SPSC, Release/Acquire is sufficient and safe.

### On x86: Loads Are Acquire, Stores Are Release (Almost)

x86's TSO guarantees that plain loads have acquire semantics and plain stores have release semantics. So on x86, a "relaxed" atomic store/load in C11 compiles to the same instruction as a release/acquire store/load. But **write this code portably** — use explicit orderings. The compiler will generate the cheapest correct code per architecture.

---

## 9. C Implementation

### 9.1 Single-Threaded Ring Buffer

**File: `rb_st.h`**

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/*
 * Single-threaded ring buffer.
 * Capacity must be a power of 2.
 * Uses "mirror bit" strategy: cursors count modulo 2*N.
 * Full:  tail - head == N
 * Empty: tail - head == 0
 * Index: cursor & mask  (mask = N - 1)
 */

typedef struct {
    void   **buf;
    uint64_t head;    /* read cursor  */
    uint64_t tail;    /* write cursor */
    uint64_t mask;    /* N - 1        */
    uint64_t cap;     /* N            */
} rb_t;

static inline bool is_power_of_two(uint64_t n) {
    return n > 0 && (n & (n - 1)) == 0;
}

/* Returns 0 on success, -1 on invalid capacity */
static inline int rb_init(rb_t *rb, uint64_t cap) {
    assert(is_power_of_two(cap));
    rb->buf  = (void **)calloc(cap, sizeof(void *));
    if (!rb->buf) return -1;
    rb->head = 0;
    rb->tail = 0;
    rb->mask = cap - 1;
    rb->cap  = cap;
    return 0;
}

static inline void rb_destroy(rb_t *rb) {
    free(rb->buf);
    rb->buf = NULL;
}

static inline uint64_t rb_count(const rb_t *rb) {
    return rb->tail - rb->head;
}

static inline uint64_t rb_space(const rb_t *rb) {
    return rb->cap - rb_count(rb);
}

static inline bool rb_empty(const rb_t *rb) {
    return rb->head == rb->tail;
}

static inline bool rb_full(const rb_t *rb) {
    return rb_count(rb) == rb->cap;
}

/* Push item. Returns true on success, false if full. */
static inline bool rb_push(rb_t *rb, void *item) {
    if (rb_full(rb)) return false;
    rb->buf[rb->tail & rb->mask] = item;
    rb->tail++;
    return true;
}

/* Pop item. Returns true on success, false if empty. */
static inline bool rb_pop(rb_t *rb, void **item) {
    if (rb_empty(rb)) return false;
    *item = rb->buf[rb->head & rb->mask];
    rb->head++;
    return true;
}

/* Peek without consuming. */
static inline bool rb_peek(const rb_t *rb, void **item) {
    if (rb_empty(rb)) return false;
    *item = rb->buf[rb->head & rb->mask];
    return true;
}

/* Overwrite mode: push even when full by advancing head. */
static inline void rb_push_overwrite(rb_t *rb, void *item) {
    rb->buf[rb->tail & rb->mask] = item;
    rb->tail++;
    if (rb_count(rb) > rb->cap) {
        rb->head++;  /* drop oldest */
    }
}
```

**File: `rb_st_test.c`**

```c
#include "rb_st.h"
#include <stdio.h>

#define ASSERT(cond, msg) \
    do { if (!(cond)) { fprintf(stderr, "FAIL: %s\n", msg); return 1; } \
         else { printf("PASS: %s\n", msg); } } while(0)

int test_basic_operations(void) {
    rb_t rb;
    rb_init(&rb, 4);

    ASSERT(rb_empty(&rb), "initially empty");
    ASSERT(!rb_full(&rb), "not initially full");

    int a = 10, b = 20, c = 30, d = 40;
    ASSERT(rb_push(&rb, &a), "push a");
    ASSERT(rb_push(&rb, &b), "push b");
    ASSERT(rb_push(&rb, &c), "push c");
    ASSERT(rb_push(&rb, &d), "push d");
    ASSERT(rb_full(&rb),  "now full");
    ASSERT(!rb_push(&rb, &a), "push fails when full");

    void *out;
    ASSERT(rb_pop(&rb, &out) && *(int*)out == 10, "pop a");
    ASSERT(rb_pop(&rb, &out) && *(int*)out == 20, "pop b");
    ASSERT(rb_pop(&rb, &out) && *(int*)out == 30, "pop c");
    ASSERT(rb_pop(&rb, &out) && *(int*)out == 40, "pop d");
    ASSERT(rb_empty(&rb), "empty after all pops");
    ASSERT(!rb_pop(&rb, &out), "pop fails when empty");

    rb_destroy(&rb);
    return 0;
}

int test_wrap_around(void) {
    rb_t rb;
    rb_init(&rb, 4);
    int vals[8];
    for (int i = 0; i < 8; i++) vals[i] = i;

    /* Push 3, pop 3, push 3 — forces wrap */
    for (int i = 0; i < 3; i++) rb_push(&rb, &vals[i]);
    void *out;
    for (int i = 0; i < 3; i++) rb_pop(&rb, &out);
    for (int i = 3; i < 6; i++) rb_push(&rb, &vals[i]);

    for (int i = 3; i < 6; i++) {
        rb_pop(&rb, &out);
        ASSERT(*(int*)out == vals[i], "wrap-around FIFO order");
    }
    rb_destroy(&rb);
    return 0;
}

int test_overwrite_mode(void) {
    rb_t rb;
    rb_init(&rb, 4);
    int vals[6];
    for (int i = 0; i < 6; i++) vals[i] = i;

    for (int i = 0; i < 6; i++) rb_push_overwrite(&rb, &vals[i]);

    void *out;
    rb_pop(&rb, &out); ASSERT(*(int*)out == 2, "overwrite: oldest is 2");
    rb_pop(&rb, &out); ASSERT(*(int*)out == 3, "overwrite: next is 3");
    rb_pop(&rb, &out); ASSERT(*(int*)out == 4, "overwrite: next is 4");
    rb_pop(&rb, &out); ASSERT(*(int*)out == 5, "overwrite: newest is 5");

    rb_destroy(&rb);
    return 0;
}

int main(void) {
    int failures = 0;
    failures += test_basic_operations();
    failures += test_wrap_around();
    failures += test_overwrite_mode();
    printf("\n%s\n", failures == 0 ? "ALL TESTS PASSED" : "SOME TESTS FAILED");
    return failures;
}
```

```bash
# Build and run
gcc -O2 -Wall -Wextra -o rb_st_test rb_st_test.c && ./rb_st_test
```

---

### 9.2 Lock-Based Concurrent Ring Buffer (POSIX)

**File: `rb_locked.h`**

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <pthread.h>

/*
 * Thread-safe ring buffer with mutex + condition variables.
 * Supports blocking push/pop with timeout.
 * Any number of producers and consumers.
 */

typedef struct {
    void            **buf;
    uint64_t          head;
    uint64_t          tail;
    uint64_t          mask;
    uint64_t          cap;
    pthread_mutex_t   lock;
    pthread_cond_t    not_full;
    pthread_cond_t    not_empty;
    bool              closed;   /* once true, no more pushes; draining */
} rb_locked_t;

static inline int rb_locked_init(rb_locked_t *rb, uint64_t cap) {
    rb->buf    = (void **)calloc(cap, sizeof(void *));
    if (!rb->buf) return -1;
    rb->head   = rb->tail = 0;
    rb->mask   = cap - 1;
    rb->cap    = cap;
    rb->closed = false;
    pthread_mutex_init(&rb->lock, NULL);
    pthread_cond_init(&rb->not_full, NULL);
    pthread_cond_init(&rb->not_empty, NULL);
    return 0;
}

static inline void rb_locked_destroy(rb_locked_t *rb) {
    pthread_mutex_destroy(&rb->lock);
    pthread_cond_destroy(&rb->not_full);
    pthread_cond_destroy(&rb->not_empty);
    free(rb->buf);
}

/* Close: wake all blocked consumers so they can drain and exit. */
static inline void rb_locked_close(rb_locked_t *rb) {
    pthread_mutex_lock(&rb->lock);
    rb->closed = true;
    pthread_cond_broadcast(&rb->not_empty);
    pthread_mutex_unlock(&rb->lock);
}

/* Non-blocking push. Returns false if full or closed. */
static inline bool rb_locked_try_push(rb_locked_t *rb, void *item) {
    pthread_mutex_lock(&rb->lock);
    if (rb->closed || (rb->tail - rb->head) == rb->cap) {
        pthread_mutex_unlock(&rb->lock);
        return false;
    }
    rb->buf[rb->tail & rb->mask] = item;
    rb->tail++;
    pthread_cond_signal(&rb->not_empty);
    pthread_mutex_unlock(&rb->lock);
    return true;
}

/* Blocking push. Returns false only if closed. */
static inline bool rb_locked_push(rb_locked_t *rb, void *item) {
    pthread_mutex_lock(&rb->lock);
    while (!rb->closed && (rb->tail - rb->head) == rb->cap) {
        pthread_cond_wait(&rb->not_full, &rb->lock);
    }
    if (rb->closed) {
        pthread_mutex_unlock(&rb->lock);
        return false;
    }
    rb->buf[rb->tail & rb->mask] = item;
    rb->tail++;
    pthread_cond_signal(&rb->not_empty);
    pthread_mutex_unlock(&rb->lock);
    return true;
}

/* Blocking pop. Returns false if closed AND empty. */
static inline bool rb_locked_pop(rb_locked_t *rb, void **item) {
    pthread_mutex_lock(&rb->lock);
    while (rb->head == rb->tail && !rb->closed) {
        pthread_cond_wait(&rb->not_empty, &rb->lock);
    }
    if (rb->head == rb->tail) {   /* closed and empty */
        pthread_mutex_unlock(&rb->lock);
        return false;
    }
    *item = rb->buf[rb->head & rb->mask];
    rb->head++;
    pthread_cond_signal(&rb->not_full);
    pthread_mutex_unlock(&rb->lock);
    return true;
}
```

**Internal breakdown of `rb_locked_push`:**

1. **Acquire mutex** — exclusive access to head/tail
2. **Check full** — `tail - head == cap`; if full, `pthread_cond_wait` atomically releases mutex and sleeps
3. **Write slot** — `buf[tail & mask] = item`
4. **Increment tail** — makes item visible (under lock, so no reordering issue)
5. **Signal `not_empty`** — wake one sleeping consumer
6. **Release mutex**

`pthread_cond_wait` can **spuriously wake**. The `while` loop re-checks the condition after every wakeup. This is not optional — it's required by POSIX.

---

### 9.3 Lock-Free SPSC Ring Buffer in C (with stdatomic)

**File: `rb_spsc.h`**

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdatomic.h>

/*
 * Lock-free Single Producer, Single Consumer ring buffer.
 *
 * RULES:
 *   - Exactly one thread calls rb_spsc_push (producer).
 *   - Exactly one thread calls rb_spsc_pop  (consumer).
 *   - No other synchronization needed.
 *
 * Memory ordering:
 *   - Producer: writes data (relaxed), then stores tail (release).
 *   - Consumer: loads tail (acquire), reads data (relaxed), stores head (release).
 *
 * Cache layout:
 *   - head and tail on separate cache lines to prevent false sharing.
 *   - Each side caches the remote cursor to avoid cross-core traffic.
 */

#define CACHE_LINE 64

typedef struct {
    /* Consumer's cache line */
    _Alignas(CACHE_LINE) _Atomic(uint64_t) head;
    uint64_t _head_pad[7];

    /* Producer's cache line */
    _Alignas(CACHE_LINE) _Atomic(uint64_t) tail;
    uint64_t _tail_pad[7];

    /* Cached cursors — reduce cross-core reads */
    _Alignas(CACHE_LINE) uint64_t head_cache;   /* producer's stale copy of head */
    uint64_t                      tail_cache;   /* consumer's stale copy of tail */
    uint64_t _cache_pad[6];

    /* Read-only after init */
    void   **buf;
    uint64_t cap;
    uint64_t mask;
} rb_spsc_t;

static inline int rb_spsc_init(rb_spsc_t *rb, uint64_t cap) {
    /* cap must be power of 2 */
    if (!cap || (cap & (cap - 1))) return -1;
    rb->buf        = (void **)calloc(cap, sizeof(void *));
    if (!rb->buf) return -1;
    atomic_store_explicit(&rb->head, 0, memory_order_relaxed);
    atomic_store_explicit(&rb->tail, 0, memory_order_relaxed);
    rb->head_cache = 0;
    rb->tail_cache = 0;
    rb->cap        = cap;
    rb->mask       = cap - 1;
    return 0;
}

static inline void rb_spsc_destroy(rb_spsc_t *rb) {
    free(rb->buf);
}

/*
 * Producer: push one item.
 * Returns false if full (try again later).
 */
static inline bool rb_spsc_push(rb_spsc_t *rb, void *item) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint64_t next = tail + 1;

    /* Check if full using cached head — avoid cross-core read */
    if (next - rb->head_cache > rb->cap) {
        /* Cache miss: re-read real head */
        rb->head_cache = atomic_load_explicit(&rb->head, memory_order_acquire);
        if (next - rb->head_cache > rb->cap) {
            return false;  /* genuinely full */
        }
    }

    rb->buf[tail & rb->mask] = item;

    /* Release: all writes above are visible before this store */
    atomic_store_explicit(&rb->tail, next, memory_order_release);
    return true;
}

/*
 * Consumer: pop one item.
 * Returns false if empty (try again later).
 */
static inline bool rb_spsc_pop(rb_spsc_t *rb, void **item) {
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);

    /* Check if empty using cached tail */
    if (head == rb->tail_cache) {
        /* Cache miss: re-read real tail */
        rb->tail_cache = atomic_load_explicit(&rb->tail, memory_order_acquire);
        if (head == rb->tail_cache) {
            return false;  /* genuinely empty */
        }
    }

    *item = rb->buf[head & rb->mask];

    /* Release: ensures item read completes before head advances */
    atomic_store_explicit(&rb->head, head + 1, memory_order_release);
    return true;
}

/* Batch push: returns number of items actually pushed */
static inline uint64_t rb_spsc_push_batch(rb_spsc_t *rb, void **items, uint64_t n) {
    uint64_t tail  = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint64_t head  = atomic_load_explicit(&rb->head, memory_order_acquire);
    uint64_t space = rb->cap - (tail - head);
    uint64_t count = n < space ? n : space;

    for (uint64_t i = 0; i < count; i++) {
        rb->buf[(tail + i) & rb->mask] = items[i];
    }
    atomic_store_explicit(&rb->tail, tail + count, memory_order_release);
    return count;
}
```

**Step-by-step internal breakdown of `rb_spsc_push`:**

1. Load `tail` with **relaxed** — only we write tail, so no sync needed to read our own write
2. Compute `next = tail + 1`
3. Check fullness against **cached** `head_cache` — avoids reading the consumer's cache line
4. If cache says full, do an **acquire** load of real `head` — this syncs with consumer's release store on head
5. If still full, return false
6. Write item to `buf[tail & mask]` — plain write (no atomic needed; consumer won't read until tail advances)
7. **Release store** `tail = next` — this is the publication fence; consumer's acquire load of tail creates the happens-before edge

---

## 10. Rust Implementation

### 10.1 Safe Single-Threaded Ring Buffer

**File: `src/rb_st.rs`**

```rust
/// Single-threaded ring buffer backed by a Vec.
/// Uses the "mirror bit" / ever-incrementing cursor strategy.
/// T must be stored by value; uses Option<T> to avoid unsafe MaybeUninit.
pub struct RingBuf<T> {
    buf:  Vec<Option<T>>,
    head: usize,   // read cursor
    tail: usize,   // write cursor
    cap:  usize,   // power-of-2 capacity
    mask: usize,   // cap - 1
}

impl<T> RingBuf<T> {
    /// Creates a ring buffer with `cap` capacity (must be power of 2).
    pub fn new(cap: usize) -> Self {
        assert!(cap.is_power_of_two(), "capacity must be a power of 2");
        let mut buf = Vec::with_capacity(cap);
        for _ in 0..cap { buf.push(None); }
        RingBuf { buf, head: 0, tail: 0, cap, mask: cap - 1 }
    }

    pub fn len(&self) -> usize   { self.tail.wrapping_sub(self.head) }
    pub fn is_empty(&self) -> bool { self.head == self.tail }
    pub fn is_full(&self)  -> bool { self.len() == self.cap }
    pub fn capacity(&self) -> usize { self.cap }

    /// Push an item. Returns the item back on failure (full).
    pub fn push(&mut self, item: T) -> Result<(), T> {
        if self.is_full() { return Err(item); }
        self.buf[self.tail & self.mask] = Some(item);
        self.tail = self.tail.wrapping_add(1);
        Ok(())
    }

    /// Pop an item. Returns None if empty.
    pub fn pop(&mut self) -> Option<T> {
        if self.is_empty() { return None; }
        let item = self.buf[self.head & self.mask].take();
        self.head = self.head.wrapping_add(1);
        item
    }

    /// Peek at the front without consuming.
    pub fn peek(&self) -> Option<&T> {
        self.buf[self.head & self.mask].as_ref()
    }

    /// Push, overwriting oldest item if full.
    pub fn push_overwrite(&mut self, item: T) -> Option<T> {
        let evicted = if self.is_full() {
            let old = self.buf[self.head & self.mask].take();
            self.head = self.head.wrapping_add(1);
            old
        } else {
            None
        };
        self.buf[self.tail & self.mask] = Some(item);
        self.tail = self.tail.wrapping_add(1);
        evicted
    }

    /// Drain all items as an iterator.
    pub fn drain(&mut self) -> impl Iterator<Item = T> + '_ {
        std::iter::from_fn(move || self.pop())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_fifo() {
        let mut rb: RingBuf<i32> = RingBuf::new(4);
        assert!(rb.is_empty());
        rb.push(1).unwrap();
        rb.push(2).unwrap();
        rb.push(3).unwrap();
        rb.push(4).unwrap();
        assert!(rb.is_full());
        assert!(rb.push(5).is_err());
        assert_eq!(rb.pop(), Some(1));
        assert_eq!(rb.pop(), Some(2));
        assert_eq!(rb.pop(), Some(3));
        assert_eq!(rb.pop(), Some(4));
        assert_eq!(rb.pop(), None);
    }

    #[test]
    fn test_wrap_around() {
        let mut rb: RingBuf<i32> = RingBuf::new(4);
        for i in 0..3 { rb.push(i).unwrap(); }
        for _ in 0..3 { rb.pop(); }
        // head = tail = 3 (wrapping), buffer indices wrap
        for i in 10..14 { rb.push(i).unwrap(); }
        let drained: Vec<i32> = rb.drain().collect();
        assert_eq!(drained, vec![10, 11, 12, 13]);
    }

    #[test]
    fn test_overwrite() {
        let mut rb: RingBuf<i32> = RingBuf::new(4);
        for i in 0..4 { rb.push(i).unwrap(); }
        let evicted = rb.push_overwrite(99);
        assert_eq!(evicted, Some(0));
        let drained: Vec<i32> = rb.drain().collect();
        assert_eq!(drained, vec![1, 2, 3, 99]);
    }

    #[test]
    fn test_peek() {
        let mut rb: RingBuf<i32> = RingBuf::new(4);
        rb.push(42).unwrap();
        assert_eq!(rb.peek(), Some(&42));
        assert_eq!(rb.pop(), Some(42));
        assert_eq!(rb.peek(), None);
    }
}
```

---

### 10.2 Unsafe Ring Buffer with MaybeUninit (Zero-Cost, No Option Overhead)

**File: `src/rb_unsafe.rs`**

```rust
use std::mem::MaybeUninit;

/// Ring buffer using MaybeUninit<T> — no Option overhead.
/// Items in [head..tail) are initialized; others are uninitialized.
///
/// SAFETY INVARIANT:
///   buf[i & mask] is initialized iff head <= i < tail (using wrapping arithmetic).
pub struct RingBufUninit<T> {
    buf:  Box<[MaybeUninit<T>]>,
    head: usize,
    tail: usize,
    cap:  usize,
    mask: usize,
}

impl<T> RingBufUninit<T> {
    pub fn new(cap: usize) -> Self {
        assert!(cap.is_power_of_two());
        // SAFETY: MaybeUninit<T> arrays are safe to create uninitialized.
        let buf = (0..cap).map(|_| MaybeUninit::uninit()).collect::<Vec<_>>().into_boxed_slice();
        RingBufUninit { buf, head: 0, tail: 0, cap, mask: cap - 1 }
    }

    pub fn len(&self)      -> usize { self.tail.wrapping_sub(self.head) }
    pub fn is_empty(&self) -> bool  { self.head == self.tail }
    pub fn is_full(&self)  -> bool  { self.len() == self.cap }

    pub fn push(&mut self, item: T) -> Result<(), T> {
        if self.is_full() { return Err(item); }
        // SAFETY: slot is uninitialized (not in [head..tail)), safe to write.
        unsafe {
            self.buf[self.tail & self.mask].as_mut_ptr().write(item);
        }
        self.tail = self.tail.wrapping_add(1);
        Ok(())
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.is_empty() { return None; }
        // SAFETY: slot is initialized (in [head..tail)), safe to read.
        let item = unsafe {
            self.buf[self.head & self.mask].as_ptr().read()
        };
        self.head = self.head.wrapping_add(1);
        Some(item)
    }
}

impl<T> Drop for RingBufUninit<T> {
    fn drop(&mut self) {
        // SAFETY: All items in [head..tail) are initialized and must be dropped.
        while !self.is_empty() {
            self.pop(); // drop each item properly
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_uninit_basic() {
        let mut rb: RingBufUninit<String> = RingBufUninit::new(4);
        rb.push("hello".to_string()).unwrap();
        rb.push("world".to_string()).unwrap();
        assert_eq!(rb.pop().unwrap(), "hello");
        assert_eq!(rb.pop().unwrap(), "world");
        assert!(rb.pop().is_none());
    }

    #[test]
    fn test_drop_runs_destructors() {
        use std::sync::atomic::{AtomicUsize, Ordering};
        use std::sync::Arc;

        let count = Arc::new(AtomicUsize::new(0));
        struct Tracked(Arc<AtomicUsize>);
        impl Drop for Tracked {
            fn drop(&mut self) { self.0.fetch_add(1, Ordering::Relaxed); }
        }

        {
            let mut rb: RingBufUninit<Tracked> = RingBufUninit::new(4);
            rb.push(Tracked(count.clone())).unwrap();
            rb.push(Tracked(count.clone())).unwrap();
            // rb drops here, all 2 items must be dropped
        }
        assert_eq!(count.load(Ordering::Relaxed), 2);
    }
}
```

---

### 10.3 Lock-Free SPSC in Rust

**File: `src/spsc.rs`**

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::mem::MaybeUninit;
use std::cell::UnsafeCell;
use std::sync::Arc;

/// Lock-free Single Producer Single Consumer ring buffer.
///
/// SAFETY CONTRACT:
///   - Arc::clone gives one Producer and one Consumer handle.
///   - Producer and Consumer are !Send across threads unless T: Send.
///   - No aliasing between producer and consumer slots — enforced by
///     the invariant that producer owns tail..tail+space and consumer
///     owns head..tail (read-only).

const CACHE_LINE: usize = 64;

// Pad a value to its own cache line.
#[repr(align(64))]
struct CachePadded<T>(T);

struct Inner<T> {
    head:  CachePadded<AtomicUsize>,
    tail:  CachePadded<AtomicUsize>,
    buf:   Box<[UnsafeCell<MaybeUninit<T>>]>,
    cap:   usize,
    mask:  usize,
}

// SAFETY: We guarantee single-producer/single-consumer access discipline.
unsafe impl<T: Send> Send for Inner<T> {}
unsafe impl<T: Send> Sync for Inner<T> {}

pub struct SpscProducer<T> {
    inner:      Arc<Inner<T>>,
    tail_cache: usize,  // local copy — avoids repeated atomic loads
    head_cache: usize,  // cached remote head — reduces cross-core traffic
}

pub struct SpscConsumer<T> {
    inner:      Arc<Inner<T>>,
    head_cache: usize,
    tail_cache: usize,
}

pub fn spsc_channel<T>(cap: usize) -> (SpscProducer<T>, SpscConsumer<T>) {
    assert!(cap.is_power_of_two(), "capacity must be power of 2");
    let buf = (0..cap)
        .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
        .collect::<Vec<_>>()
        .into_boxed_slice();

    let inner = Arc::new(Inner {
        head: CachePadded(AtomicUsize::new(0)),
        tail: CachePadded(AtomicUsize::new(0)),
        buf,
        cap,
        mask: cap - 1,
    });

    let producer = SpscProducer {
        inner: inner.clone(),
        tail_cache: 0,
        head_cache: 0,
    };
    let consumer = SpscConsumer {
        inner,
        head_cache: 0,
        tail_cache: 0,
    };
    (producer, consumer)
}

impl<T> SpscProducer<T> {
    /// Push an item. Returns Err(item) if full.
    pub fn push(&mut self, item: T) -> Result<(), T> {
        let tail = self.tail_cache;
        let next = tail.wrapping_add(1);

        // Check fullness using cached head
        if next.wrapping_sub(self.head_cache) > self.inner.cap {
            // Refresh from real atomic head
            self.head_cache = self.inner.head.0.load(Ordering::Acquire);
            if next.wrapping_sub(self.head_cache) > self.inner.cap {
                return Err(item);
            }
        }

        // SAFETY: slot is in the "producer-owned" region (tail..tail+space).
        // Only we write to this slot; consumer only reads slots in [head..tail).
        unsafe {
            (*self.inner.buf[tail & self.inner.mask].get())
                .as_mut_ptr()
                .write(item);
        }

        // Publish: release store on tail. Consumer's acquire load of tail
        // creates a happens-before edge covering the write above.
        self.inner.tail.0.store(next, Ordering::Release);
        self.tail_cache = next;
        Ok(())
    }

    /// Returns number of available push slots (approximate).
    pub fn space(&self) -> usize {
        let head = self.inner.head.0.load(Ordering::Acquire);
        self.inner.cap - self.tail_cache.wrapping_sub(head)
    }
}

impl<T> SpscConsumer<T> {
    /// Pop an item. Returns None if empty.
    pub fn pop(&mut self) -> Option<T> {
        let head = self.head_cache;

        // Check emptiness using cached tail
        if head == self.tail_cache {
            // Refresh from real atomic tail
            self.tail_cache = self.inner.tail.0.load(Ordering::Acquire);
            if head == self.tail_cache {
                return None;
            }
        }

        // SAFETY: slot is in [head..tail), fully initialized by producer.
        let item = unsafe {
            (*self.inner.buf[head & self.inner.mask].get())
                .as_ptr()
                .read()
        };

        self.inner.head.0.store(head.wrapping_add(1), Ordering::Release);
        self.head_cache = head.wrapping_add(1);
        Some(item)
    }

    /// Returns number of available items (approximate).
    pub fn len(&self) -> usize {
        let tail = self.inner.tail.0.load(Ordering::Acquire);
        tail.wrapping_sub(self.head_cache)
    }
}

impl<T> Drop for SpscConsumer<T> {
    fn drop(&mut self) {
        // Drain remaining items to run their destructors.
        while self.pop().is_some() {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_spsc_single_thread() {
        let (mut tx, mut rx) = spsc_channel::<i32>(8);
        for i in 0..8 { tx.push(i).unwrap(); }
        assert!(tx.push(99).is_err());
        for i in 0..8 { assert_eq!(rx.pop(), Some(i)); }
        assert_eq!(rx.pop(), None);
    }

    #[test]
    fn test_spsc_cross_thread() {
        const N: usize = 100_000;
        let (mut tx, mut rx) = spsc_channel::<usize>(1024);

        let producer = thread::spawn(move || {
            for i in 0..N {
                loop {
                    if tx.push(i).is_ok() { break; }
                    std::hint::spin_loop();
                }
            }
        });

        let consumer = thread::spawn(move || {
            let mut received = Vec::with_capacity(N);
            while received.len() < N {
                if let Some(v) = rx.pop() {
                    received.push(v);
                } else {
                    std::hint::spin_loop();
                }
            }
            received
        });

        producer.join().unwrap();
        let received = consumer.join().unwrap();

        assert_eq!(received.len(), N);
        for (i, &v) in received.iter().enumerate() {
            assert_eq!(v, i, "FIFO violated at position {}", i);
        }
    }

    #[test]
    fn test_drop_calls_destructors() {
        use std::sync::atomic::{AtomicUsize, Ordering};
        use std::sync::Arc;

        let drops = Arc::new(AtomicUsize::new(0));
        struct Canary(Arc<AtomicUsize>);
        impl Drop for Canary {
            fn drop(&mut self) { self.0.fetch_add(1, Ordering::Relaxed); }
        }

        let (mut tx, rx) = spsc_channel::<Canary>(8);
        tx.push(Canary(drops.clone())).unwrap();
        tx.push(Canary(drops.clone())).unwrap();
        drop(rx);  // consumer drop should drain and call destructors
        assert_eq!(drops.load(Ordering::Relaxed), 2);
    }
}
```

**Run tests and benchmarks:**

```bash
cargo test
cargo bench  # add [dev-dependencies] criterion to Cargo.toml
```

---

### 10.4 Rust Cargo.toml

```toml
[package]
name = "ring-buffers"
version = "0.1.0"
edition = "2021"

[lib]
name = "ring_buffers"
path = "src/lib.rs"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "spsc_bench"
harness = false
```

**File: `benches/spsc_bench.rs`**

```rust
use criterion::{criterion_group, criterion_main, Criterion, black_box};
use ring_buffers::spsc::spsc_channel;

fn bench_spsc_throughput(c: &mut Criterion) {
    c.bench_function("spsc round-trip 1024", |b| {
        let (mut tx, mut rx) = spsc_channel::<u64>(1024);
        b.iter(|| {
            tx.push(black_box(42u64)).ok();
            black_box(rx.pop())
        });
    });
}

criterion_group!(benches, bench_spsc_throughput);
criterion_main!(benches);
```

---

## 11. Go Implementation

### 11.1 How Go's Built-in Channel Is a Ring Buffer

Before writing our own, understand that `make(chan T, N)` creates a ring buffer internally. From `src/runtime/chan.go`:

```go
type hchan struct {
    qcount   uint          // total data in the queue
    dataqsiz uint          // size of the circular queue (capacity)
    buf      unsafe.Pointer // points to an array of dataqsiz elements
    elemsize uint16
    closed   uint32
    sendx    uint          // tail (send index)
    recvx    uint          // head (receive index)
    recvq    waitq         // list of recv waiters (goroutines blocked on <-ch)
    sendq    waitq         // list of send waiters (goroutines blocked on ch<-)
    lock     mutex
}
```

Key takeaways from Go's channel:
- It **is** a ring buffer with mutex + goroutine park/unpark
- `sendx` and `recvx` are raw indices (not cursors); they wrap at `dataqsiz` explicitly
- Blocked goroutines are put in `sendq`/`recvq` wait queues and are resumed by the runtime scheduler, not by OS condition variables
- The lock is a Go runtime spinlock (not `sync.Mutex`), which is lighter weight

### 11.2 Lock-Based MPMC Ring Buffer in Go

**File: `rb_locked.go`**

```go
package ringbuf

import (
	"errors"
	"sync"
)

// ErrFull is returned by TryPush when the ring buffer is full.
var ErrFull = errors.New("ring buffer full")

// ErrEmpty is returned by TryPop when the ring buffer is empty.
var ErrEmpty = errors.New("ring buffer empty")

// ErrClosed is returned when operating on a closed ring buffer.
var ErrClosed = errors.New("ring buffer closed")

// RingBuf is a bounded, thread-safe MPMC ring buffer.
// All operations that block respect context cancellation via the Close method.
type RingBuf[T any] struct {
	buf    []T
	head   uint64
	tail   uint64
	cap    uint64
	mask   uint64
	mu     sync.Mutex
	notFull  sync.Cond
	notEmpty sync.Cond
	closed bool
}

// New creates a RingBuf with the given capacity (must be power of 2).
func New[T any](cap uint64) *RingBuf[T] {
	if cap == 0 || cap&(cap-1) != 0 {
		panic("ringbuf: capacity must be a power of 2")
	}
	rb := &RingBuf[T]{
		buf:  make([]T, cap),
		cap:  cap,
		mask: cap - 1,
	}
	rb.notFull.L  = &rb.mu
	rb.notEmpty.L = &rb.mu
	return rb
}

func (rb *RingBuf[T]) count() uint64 { return rb.tail - rb.head }

// Len returns the number of items currently in the buffer.
func (rb *RingBuf[T]) Len() int {
	rb.mu.Lock()
	n := rb.count()
	rb.mu.Unlock()
	return int(n)
}

// Close marks the buffer as closed. Subsequent Push calls return ErrClosed.
// Pop continues to drain existing items; returns ErrClosed only when empty.
func (rb *RingBuf[T]) Close() {
	rb.mu.Lock()
	rb.closed = true
	rb.notEmpty.Broadcast() // wake all blocked consumers
	rb.notFull.Broadcast()  // wake all blocked producers
	rb.mu.Unlock()
}

// TryPush pushes without blocking. Returns ErrFull or ErrClosed on failure.
func (rb *RingBuf[T]) TryPush(item T) error {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	if rb.closed {
		return ErrClosed
	}
	if rb.count() == rb.cap {
		return ErrFull
	}
	rb.buf[rb.tail&rb.mask] = item
	rb.tail++
	rb.notEmpty.Signal()
	return nil
}

// Push blocks until there is space or the buffer is closed.
func (rb *RingBuf[T]) Push(item T) error {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	for !rb.closed && rb.count() == rb.cap {
		rb.notFull.Wait()
	}
	if rb.closed {
		return ErrClosed
	}
	rb.buf[rb.tail&rb.mask] = item
	rb.tail++
	rb.notEmpty.Signal()
	return nil
}

// TryPop pops without blocking. Returns ErrEmpty or ErrClosed on failure.
func (rb *RingBuf[T]) TryPop() (T, error) {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	var zero T
	if rb.head == rb.tail {
		if rb.closed {
			return zero, ErrClosed
		}
		return zero, ErrEmpty
	}
	item := rb.buf[rb.head&rb.mask]
	rb.head++
	rb.notFull.Signal()
	return item, nil
}

// Pop blocks until an item is available or the buffer is closed and empty.
func (rb *RingBuf[T]) Pop() (T, error) {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	for rb.head == rb.tail && !rb.closed {
		rb.notEmpty.Wait()
	}
	var zero T
	if rb.head == rb.tail {
		return zero, ErrClosed
	}
	item := rb.buf[rb.head&rb.mask]
	rb.head++
	rb.notFull.Signal()
	return item, nil
}
```

**File: `rb_locked_test.go`**

```go
package ringbuf

import (
	"sync"
	"testing"
)

func TestRingBufBasic(t *testing.T) {
	rb := New[int](4)

	if err := rb.TryPush(1); err != nil { t.Fatal(err) }
	if err := rb.TryPush(2); err != nil { t.Fatal(err) }
	if err := rb.TryPush(3); err != nil { t.Fatal(err) }
	if err := rb.TryPush(4); err != nil { t.Fatal(err) }
	if err := rb.TryPush(5); err != ErrFull { t.Fatalf("expected ErrFull, got %v", err) }

	for i := 1; i <= 4; i++ {
		v, err := rb.TryPop()
		if err != nil || v != i {
			t.Fatalf("expected %d, got %d err=%v", i, v, err)
		}
	}
	if _, err := rb.TryPop(); err != ErrEmpty {
		t.Fatalf("expected ErrEmpty")
	}
}

func TestRingBufWrapAround(t *testing.T) {
	rb := New[int](4)
	for i := 0; i < 3; i++ { rb.TryPush(i) }
	for i := 0; i < 3; i++ { rb.TryPop() }
	// head = tail = 3, wraps on next push
	for i := 10; i < 14; i++ { rb.TryPush(i) }
	for i := 10; i < 14; i++ {
		v, _ := rb.TryPop()
		if v != i { t.Errorf("wrap: expected %d got %d", i, v) }
	}
}

func TestRingBufConcurrentMPMC(t *testing.T) {
	const (
		producers = 4
		consumers = 4
		perProd   = 10000
		total     = producers * perProd
	)
	rb := New[int](256)
	var wgProd, wgCons sync.WaitGroup
	results := make([]int, 0, total)
	var mu sync.Mutex

	wgProd.Add(producers)
	for p := 0; p < producers; p++ {
		go func(id int) {
			defer wgProd.Done()
			for i := 0; i < perProd; i++ {
				for rb.Push(id*perProd+i) != nil {}
			}
		}(p)
	}

	wgCons.Add(consumers)
	for c := 0; c < consumers; c++ {
		go func() {
			defer wgCons.Done()
			for {
				v, err := rb.Pop()
				if err == ErrClosed { return }
				mu.Lock()
				results = append(results, v)
				mu.Unlock()
			}
		}()
	}

	wgProd.Wait()
	rb.Close()
	wgCons.Wait()

	if len(results) != total {
		t.Fatalf("expected %d items, got %d", total, len(results))
	}
}

func BenchmarkRingBufPushPop(b *testing.B) {
	rb := New[int](1024)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		rb.TryPush(i)
		rb.TryPop()
	}
}
```

```bash
go test ./... -v -race
go test -bench=. -benchmem ./...
```

---

### 11.3 Lock-Free SPSC in Go

**File: `spsc.go`**

```go
package spsc

import (
	"runtime"
	"sync/atomic"
	"unsafe"
)

// cacheLinePad pads a struct to its own cache line.
const cacheLineSize = 64

type pad [cacheLineSize]byte

// SPSC is a lock-free single-producer single-consumer ring buffer.
//
// RULES:
//   - Only ONE goroutine calls Push (producer).
//   - Only ONE goroutine calls Pop  (consumer).
//
// Uses unsafe.Pointer slots so the buffer is generic without generics overhead.
// For a typed version, wrap this or use Go 1.18+ generics.
type SPSC struct {
	_    pad
	head atomic.Uint64
	_    pad

	_    pad
	tail atomic.Uint64
	_    pad

	// Cached remote cursors — avoid cross-core atomics on the hot path.
	// These are only read by their respective goroutine so no atomics needed.
	headCache uint64 // producer's cached copy of head
	tailCache uint64 // consumer's cached copy of tail
	_         [cacheLineSize - 16]byte

	buf  []unsafe.Pointer
	cap  uint64
	mask uint64
}

// New creates an SPSC ring buffer with the given capacity (must be power of 2).
func New(cap uint64) *SPSC {
	if cap == 0 || cap&(cap-1) != 0 {
		panic("spsc: capacity must be a power of 2")
	}
	return &SPSC{
		buf:  make([]unsafe.Pointer, cap),
		cap:  cap,
		mask: cap - 1,
	}
}

// Push adds an item. Returns false if full. Must be called by one goroutine only.
// item must not be nil; use a pointer to your value.
func (q *SPSC) Push(item unsafe.Pointer) bool {
	tail := q.tail.Load()
	next := tail + 1

	// Check fullness using cached head to avoid cross-core traffic.
	if next-q.headCache > q.cap {
		q.headCache = q.head.Load()
		if next-q.headCache > q.cap {
			return false
		}
	}

	// atomic.StorePointer provides release semantics on all platforms.
	atomic.StorePointer(&q.buf[tail&q.mask], item)
	q.tail.Store(next)
	return true
}

// Pop removes an item. Returns nil if empty. Must be called by one goroutine only.
func (q *SPSC) Pop() unsafe.Pointer {
	head := q.head.Load()

	// Check emptiness using cached tail.
	if head == q.tailCache {
		q.tailCache = q.tail.Load()
		if head == q.tailCache {
			return nil
		}
	}

	item := atomic.LoadPointer(&q.buf[head&q.mask])
	q.head.Store(head + 1)
	return item
}

// Len returns the approximate number of items (snapshot, may be stale).
func (q *SPSC) Len() uint64 {
	tail := q.tail.Load()
	head := q.head.Load()
	return tail - head
}
```

**File: `spsc_typed.go` — Generic Wrapper**

```go
package spsc

import (
	"unsafe"
)

// TypedSPSC is a type-safe wrapper around SPSC.
// T must not contain pointers to stack-allocated memory.
type TypedSPSC[T any] struct {
	inner *SPSC
}

func NewTyped[T any](cap uint64) *TypedSPSC[T] {
	return &TypedSPSC[T]{inner: New(cap)}
}

func (q *TypedSPSC[T]) Push(item *T) bool {
	return q.inner.Push(unsafe.Pointer(item))
}

func (q *TypedSPSC[T]) Pop() *T {
	p := q.inner.Pop()
	if p == nil { return nil }
	return (*T)(p)
}
```

**File: `spsc_test.go`**

```go
package spsc

import (
	"sync"
	"testing"
	"unsafe"
)

func TestSPSCBasic(t *testing.T) {
	q := New(8)
	for i := 0; i < 8; i++ {
		val := new(int)
		*val = i
		if !q.Push(unsafe.Pointer(val)) {
			t.Fatalf("push %d failed", i)
		}
	}
	// Full
	val := new(int)
	if q.Push(unsafe.Pointer(val)) {
		t.Fatal("push to full should fail")
	}
	for i := 0; i < 8; i++ {
		p := q.Pop()
		if p == nil || *(*int)(p) != i {
			t.Fatalf("pop %d: got wrong value", i)
		}
	}
	if q.Pop() != nil {
		t.Fatal("pop from empty should return nil")
	}
}

func TestSPSCCrossGoroutine(t *testing.T) {
	const N = 500_000
	q := New(1024)
	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		for i := 0; i < N; i++ {
			v := new(int)
			*v = i
			for !q.Push(unsafe.Pointer(v)) {
				runtime.Gosched()
			}
		}
	}()

	go func() {
		defer wg.Done()
		for i := 0; i < N; i++ {
			var p unsafe.Pointer
			for {
				p = q.Pop()
				if p != nil { break }
				runtime.Gosched()
			}
			got := *(*int)(p)
			if got != i {
				t.Errorf("FIFO violation: expected %d got %d", i, got)
			}
		}
	}()

	wg.Wait()
}

func BenchmarkSPSCPushPop(b *testing.B) {
	q := New(1024)
	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		// NOTE: This is NOT a valid SPSC benchmark (parallel = multiple goroutines).
		// Use this only for raw throughput indication; use single-threaded loop for SPSC.
	})
	_ = q
}

func BenchmarkSPSCSingleThread(b *testing.B) {
	q := New(1024)
	val := new(int)
	*val = 42
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		q.Push(unsafe.Pointer(val))
		q.Pop()
	}
}
```

```bash
go test ./... -race -count=1
go test -bench=BenchmarkSPSC -benchmem -benchtime=5s ./...
```

---

## 12. Lock-Free MPMC: The Dmitry Vyukov Queue

The gold standard for lock-free MPMC ring buffers. Used in LMAX Disruptor, Folly, Intel DPDK, and countless other high-performance systems.

### Core Idea: Per-Slot Sequence Numbers

Instead of sharing a single tail or head, each slot has an atomic `sequence` number. The sequence encodes which "generation" the slot belongs to.

```
slot[i].sequence = i initially (generation 0)

Producer:
  pos = fetch_add(tail, 1)           // atomically claim a slot
  wait until slot[pos % N].sequence == pos   // wait for slot to be "empty"
  write data
  slot[pos % N].sequence = pos + 1  // mark slot "full"

Consumer:
  pos = fetch_add(head, 1)           // atomically claim a slot
  wait until slot[pos % N].sequence == pos + 1  // wait for slot to be "full"
  read data
  slot[pos % N].sequence = pos + N  // mark slot "empty" for next lap
```

### Implementation in C

**File: `rb_mpmc.h`**

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <string.h>

#define CACHE_LINE_SIZE 64

typedef struct {
    _Alignas(CACHE_LINE_SIZE) _Atomic(uint64_t) sequence;
    void *data;
} mpmc_slot_t;

typedef struct {
    _Alignas(CACHE_LINE_SIZE) _Atomic(uint64_t) tail;
    char _tail_pad[CACHE_LINE_SIZE - sizeof(_Atomic(uint64_t))];

    _Alignas(CACHE_LINE_SIZE) _Atomic(uint64_t) head;
    char _head_pad[CACHE_LINE_SIZE - sizeof(_Atomic(uint64_t))];

    mpmc_slot_t *slots;
    uint64_t     cap;
    uint64_t     mask;
} mpmc_rb_t;

static inline int mpmc_init(mpmc_rb_t *rb, uint64_t cap) {
    if (!cap || (cap & (cap - 1))) return -1;
    rb->slots = (mpmc_slot_t *)aligned_alloc(CACHE_LINE_SIZE,
                    cap * sizeof(mpmc_slot_t));
    if (!rb->slots) return -1;

    for (uint64_t i = 0; i < cap; i++) {
        atomic_store_explicit(&rb->slots[i].sequence, i, memory_order_relaxed);
        rb->slots[i].data = NULL;
    }

    atomic_store_explicit(&rb->tail, 0, memory_order_relaxed);
    atomic_store_explicit(&rb->head, 0, memory_order_relaxed);
    rb->cap  = cap;
    rb->mask = cap - 1;
    return 0;
}

static inline void mpmc_destroy(mpmc_rb_t *rb) {
    free(rb->slots);
}

/*
 * Push item. Returns:
 *  1  — success
 *  0  — full, try again
 * -1  — lagged behind (producer wraparound > N, indicates consumer too slow)
 */
static inline int mpmc_push(mpmc_rb_t *rb, void *item) {
    uint64_t pos = atomic_load_explicit(&rb->tail, memory_order_relaxed);

    for (;;) {
        mpmc_slot_t *slot = &rb->slots[pos & rb->mask];
        uint64_t seq = atomic_load_explicit(&slot->sequence, memory_order_acquire);
        int64_t diff = (int64_t)seq - (int64_t)pos;

        if (diff == 0) {
            /* Slot is empty and pos matches — try to claim it */
            if (atomic_compare_exchange_weak_explicit(
                    &rb->tail, &pos, pos + 1,
                    memory_order_relaxed, memory_order_relaxed)) {
                /* We own this slot */
                slot->data = item;
                atomic_store_explicit(&slot->sequence, pos + 1, memory_order_release);
                return 1;
            }
            /* CAS failed — another producer grabbed this slot; reload pos */
        } else if (diff < 0) {
            /* seq < pos: queue is full (consumer hasn't freed this slot yet) */
            return 0;
        } else {
            /* seq > pos: another producer already claimed this pos; advance */
            pos = atomic_load_explicit(&rb->tail, memory_order_relaxed);
        }
    }
}

/*
 * Pop item. Returns:
 *  1  — success, *item filled
 *  0  — empty, try again
 */
static inline int mpmc_pop(mpmc_rb_t *rb, void **item) {
    uint64_t pos = atomic_load_explicit(&rb->head, memory_order_relaxed);

    for (;;) {
        mpmc_slot_t *slot = &rb->slots[pos & rb->mask];
        uint64_t seq = atomic_load_explicit(&slot->sequence, memory_order_acquire);
        int64_t diff = (int64_t)seq - (int64_t)(pos + 1);

        if (diff == 0) {
            /* Slot is full and pos matches — try to claim it */
            if (atomic_compare_exchange_weak_explicit(
                    &rb->head, &pos, pos + 1,
                    memory_order_relaxed, memory_order_relaxed)) {
                *item = slot->data;
                /* Mark slot empty for next lap: sequence = pos + cap */
                atomic_store_explicit(&slot->sequence, pos + rb->cap, memory_order_release);
                return 1;
            }
        } else if (diff < 0) {
            /* seq < pos+1: queue is empty */
            return 0;
        } else {
            pos = atomic_load_explicit(&rb->head, memory_order_relaxed);
        }
    }
}
```

### Why the Sequence Number Protocol Works

**Producer perspective:**
- `seq == pos`: slot is free (sequence = slot index = pos). CAS on tail to claim.
- `seq < pos` (diff < 0): slot was written but not yet consumed. Queue full.
- `seq > pos` (diff > 0): another producer already claimed this pos. Reload tail.

**Consumer perspective:**
- `seq == pos + 1`: slot was written by producer (sequence = pos + 1). CAS on head to claim.
- `seq < pos + 1` (diff < 0): slot not yet written. Queue empty.
- `seq > pos + 1` (diff > 0): another consumer already claimed this pos. Reload head.

**After consumer reads:** `sequence = pos + cap`. This resets the slot for a future lap. When a producer eventually claims slot `pos + cap` (same physical slot, next generation), it will see `seq == pos + cap == their_pos`. Correct.

**The key insight:** The sequence number encodes both "which slot" and "which generation" in a single atomic value. No ABA problem possible because sequence is monotonically increasing.

---

## 13. Performance Analysis and Benchmarking

### Theoretical Throughput

| Design | Latency (ns) | Throughput (ops/s) | Notes |
|---|---|---|---|
| Mutex-based MPMC | 50–500 | 2M–20M | OS scheduling overhead |
| Go channel (buffered) | 30–100 | 10M–30M | Runtime goroutine park/unpark |
| Lock-free SPSC (with false sharing) | 50–200 | 5M–20M | False sharing kills perf |
| Lock-free SPSC (padded, cached) | 5–20 | 50M–200M | Near hardware limit |
| Vyukov MPMC | 20–50 | 20M–50M | Scales with core count |

*Numbers are approximate; vary heavily with CPU, cache topology, message size.*

### Benchmarking Methodology

**C benchmark:**

```c
#include <time.h>
#include <stdio.h>
#include "rb_spsc.h"

#define N 10000000

double ns_per_op(void) {
    rb_spsc_t rb;
    rb_spsc_init(&rb, 4096);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (uint64_t i = 0; i < N; i++) {
        rb_spsc_push(&rb, (void*)(uintptr_t)i);
        void *out;
        rb_spsc_pop(&rb, &out);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) * 1e9
                   + (end.tv_nsec - start.tv_nsec);
    rb_spsc_destroy(&rb);
    return elapsed / N;
}

int main(void) {
    printf("%.2f ns/op\n", ns_per_op());
}
```

```bash
gcc -O3 -march=native -o bench bench.c && ./bench
```

### Profiling with perf (Linux)

```bash
# CPU cycles breakdown
perf stat -e cycles,instructions,cache-misses,cache-references ./bench

# Cache miss analysis
perf stat -e L1-dcache-load-misses,L1-dcache-loads ./bench

# Identify hot functions
perf record -g ./bench && perf report

# False sharing detection with perf c2c
perf c2c record ./bench
perf c2c report
```

### Go Profiling

```go
import _ "net/http/pprof"
import "net/http"

// In main:
go http.ListenAndServe(":6060", nil)

// Then:
// go tool pprof http://localhost:6060/debug/pprof/profile?seconds=10
// go tool pprof http://localhost:6060/debug/pprof/mutex
```

```bash
go test -bench=. -cpuprofile=cpu.prof ./...
go tool pprof -http=:8080 cpu.prof
```

### Rust Profiling with flamegraph

```bash
cargo install flamegraph
cargo flamegraph --bench spsc_bench
# Open flamegraph.svg in browser
```

---

## 14. Real-World Use Cases

### 14.1 Audio Pipeline (SPSC, Overrun Mode)

```
[Audio callback thread] --push--> [RingBuf] --pop--> [Processing thread]
```
- Capacity: ~10ms of audio at sample rate (e.g., 48kHz × 2ch × 4bytes × 0.01s = 3840 bytes → 960 floats)
- Overflow policy: overrun (drop oldest). A glitch is better than a crash.
- Underrun policy: output silence. Never block the audio callback.

### 14.2 Logger (MPSC, Non-Blocking Producer)

```
[App threads (producers)] --try_push--> [RingBuf] --pop--> [Logger thread]
```
- Multiple threads push log entries; one background thread writes to disk.
- If full: drop the log entry (or use a fallback slow path).
- Capacity: size for burst tolerance (e.g., 64K entries × 256 bytes each = 16MB).

### 14.3 Network Packet Queue (SPSC per flow, MPMC aggregate)

```
[NIC RX ring (kernel)] --> [User-space RX ring] --> [Parser] --> [App ring]
```
- Linux XDP/DPDK pattern: kernel-to-userspace zero-copy via shared memory ring.
- The rings are literally `struct xdp_ring` in the kernel, using the same mask trick.

### 14.4 Disruptor Pattern (High-Performance Event Bus)

```
[Producer] --> [RingBuf] --> [Handler 1]
                         --> [Handler 2]
                         --> [Handler 3]
```
- Single producer, multiple consumers, each with their own head cursor.
- Buffer isn't freed until ALL consumers have processed the slot.
- Used in high-frequency trading for microsecond event processing.

---

## 15. Common Pitfalls and Anti-Patterns

### Pitfall 1: Non-Power-of-2 Capacity with Mask

```c
// BUG: mask = 9 (binary 1001), capacity = 10
// buf[cursor & 9] can map cursor 10 to index 8, skipping index 9 entirely.
// Only valid when capacity is a power of 2.
uint64_t mask = cap - 1;  // WRONG if cap is not power of 2
```

**Fix:** Either assert power-of-2, or use `cursor % cap` (slower but correct for any cap).

### Pitfall 2: Using Signed Integers for Cursors

```c
// BUG: signed overflow is undefined behavior in C
int32_t head = INT32_MAX;
head++;  // UB in C, may not wrap as expected
```

**Fix:** Always use `uint32_t` or `uint64_t` for cursors. Unsigned overflow is well-defined.

### Pitfall 3: False Sharing — head and tail on the Same Cache Line

The most common performance pitfall. Covered in section 7. Always pad.

### Pitfall 4: Missing Memory Barrier on ARM

```c
// BUG: On ARM, this may reorder. Consumer may see stale buf[] before seeing new tail.
buf[tail & mask] = item;
tail++;  // plain store — no release semantics on ARM
```

**Fix:** Use `atomic_store_explicit(..., memory_order_release)` for tail/head. Never plain stores in concurrent ring buffers.

### Pitfall 5: Wrapping the Cursor Instead of the Index

```c
// BUG: tail wraps to 0 after N ops. Difference between wrapped cursors is meaningless.
tail = (tail + 1) % cap;  // WRONG for concurrent use or overflow detection

// CORRECT: Only wrap the index, never the cursor.
buf[tail & mask] = item;
tail++;  // let tail grow unboundedly
```

### Pitfall 6: ABA Problem in Naive Lock-Free Implementations

If you use a CAS on a slot pointer (not a sequence number), you may pop the same item twice due to ABA:

```
Thread 1: reads slot = A, preempted
Thread 2: pops A, pushes B, pushes A (same address reused)
Thread 1: resumes, CAS succeeds because pointer == A again, pops A again
```

**Fix:** Use sequence numbers (Vyukov style) or hazard pointers, not raw pointer CAS.

### Pitfall 7: SpinLooping Without Yielding in Go

```go
// BAD: burns CPU, can starve the scheduler on GOMAXPROCS=1
for !q.Push(item) {}

// GOOD: yield to scheduler periodically
for !q.Push(item) {
    runtime.Gosched()
}
```

### Pitfall 8: Using Go's Race Detector to Validate Unsafe Ring Buffers

The race detector instruments Go's memory model. An unsafe SPSC ring buffer using `atomic` correctly has no data race by definition, but the race detector may still flag it if you access `unsafe.Pointer` slots without going through `atomic.LoadPointer`/`StorePointer`. Always use atomic pointer ops in the hot path.

### Pitfall 9: Capacity of 1 Edge Case

A ring buffer with capacity 1 is valid but behaves oddly: it's either empty or full. Push and pop alternate. Many implementations have off-by-one bugs at capacity=1. Test this case explicitly.

### Pitfall 10: Not Handling Destructor Runs on Drop (Rust)

Using `MaybeUninit<T>` without a proper `Drop` implementation causes memory leaks and UB if `T: Drop`. Always implement `Drop` to drain initialized items.

---

## 16. Security Checklist

### For All Ring Buffer Implementations

- [ ] **Integer overflow:** All cursor arithmetic uses unsigned integers. No signed overflow UB.
- [ ] **Index out of bounds:** `cursor & mask` is always `< cap` when `mask = cap - 1` and `cap` is power of 2. Verify this property is maintained.
- [ ] **Capacity validation:** Reject non-power-of-2 capacities explicitly. A mask derived from a wrong capacity silently corrupts data.
- [ ] **NULL/nil checks:** Never dereference items without checking (especially in C). Explicitly handle NULL items.
- [ ] **Integer overflow in capacity:** `cap * sizeof(void*)` must not overflow. Check before `malloc`.
- [ ] **Shared memory IPC rings:** Treat the entire shared region as untrusted input. A malicious process can set head/tail to arbitrary values. Validate all offsets before array access.
- [ ] **Overrun mode:** Dropping oldest items may drop security events (e.g., audit log entries). Consider a separate "drop counter" metric.
- [ ] **No blocking in signal handlers:** POSIX mutexes are not async-signal-safe. Only use lock-free or the `volatile sig_atomic_t` flag pattern in signal handlers.
- [ ] **Alignment:** `aligned_alloc` for slot arrays (MPMC). Misaligned atomic accesses fault on some architectures.
- [ ] **Capacity DoS:** External input must never control capacity directly. Cap at a sane maximum (e.g., 1GB).

### Rust-Specific

- [ ] **`unsafe` blocks:** Every `unsafe` block must have a `SAFETY:` comment proving the invariant.
- [ ] **`Send`/`Sync` bounds:** `SpscProducer<T>` and `SpscConsumer<T>` must only be `Send` when `T: Send`. Use `PhantomData<T>` or explicit trait impls.
- [ ] **Miri:** Run `cargo miri test` on any `unsafe` ring buffer to catch UB, invalid pointer usage, and memory leaks.
- [ ] **LOOM:** Use the `loom` crate for exhaustive concurrent model checking of atomic operations.

### Go-Specific

- [ ] **Race detector:** Always run `go test -race` in CI.
- [ ] **Goroutine leak:** If a goroutine blocks on a ring buffer pop forever, it leaks. Always provide a close/cancel mechanism.
- [ ] **Context propagation:** Production blocking push/pop should accept a `context.Context` to allow cancellation.

---

## 17. Exercises

### Beginner

1. **Implement a ring buffer with arbitrary (non-power-of-2) capacity** using modulo arithmetic. Benchmark it vs. the power-of-2 version. What is the throughput difference?

2. **Add a `PeekN(n)` function** to the single-threaded C ring buffer that returns the next N items without consuming them. Handle the wrap-around case.

3. **Implement a ring buffer of ring buffers** (a "fan-out" buffer): one producer pushes to a central ring, N consumers each have their own ring that the central ring fans out to. Think about when each sub-ring advances.

### Intermediate

4. **Implement the lock-based MPMC ring buffer with a `context.Context` timeout** for blocking push/pop in Go. Use `sync.Cond` with a deadline. Hint: you need a background goroutine that fires a broadcast when the deadline expires.

5. **Implement batch push/pop** for the Rust SPSC: `push_batch(items: &[T]) -> usize` that writes as many items as possible in a single fence operation. Compare throughput vs. one-at-a-time push.

6. **Write a stress tester for the Vyukov MPMC** that runs M producers and N consumers for T seconds, counting total operations and checking for lost or duplicated items using a CRC or checksum. Find the M:N ratio that maximizes throughput on your machine.

### Advanced

7. **Implement a lock-free MPSC ring buffer using fetch-add on the tail** (similar to Vyukov but only one consumer, so no CAS on head). Profile it vs. the full MPMC version. Measure the overhead saved by eliminating one CAS.

8. **Implement a shared-memory SPSC ring buffer** between two processes in C using `shm_open` + `mmap`. The producer and consumer are separate processes. Handle the startup race (who initializes the shared memory?) with a futex or a spin on a `ready` atomic flag.

9. **Implement the Disruptor pattern** in Go or Rust: one producer, multiple consumers, each with their own `head` cursor. The ring slot is freed only when ALL consumers have advanced past it. The producer must track the minimum of all consumer heads.

---

## 18. Further Reading

### Books

- **"The Art of Multiprocessor Programming"** — Herlihy & Shavit. Chapters on queue implementations and the formal theory of lock-freedom, wait-freedom, and obstruction-freedom.

### Papers and Articles

- **Dmitry Vyukov's MPMC queue** — http://www.1024cores.net/home/lock-free-algorithms/queues/bounded-mpmc-queue — The original writeup with full analysis.
- **"Disruptor: High performance alternative to bounded queues for exchanging data between concurrent threads"** — LMAX, 2011. https://lmax-exchange.github.io/disruptor/disruptor.html
- **"Memory Barriers: a Hardware View for Software Hackers"** — Paul E. McKenney. Comprehensive hardware memory model analysis.
- **Linux kernel ring buffer implementation** — `include/linux/circ_buf.h` and `Documentation/core-api/circular-buffers.rst`. Production-grade reference.

### Repositories

- **`crossbeam-queue`** (Rust) — https://github.com/crossbeam-rs/crossbeam — Production SPSC and MPMC lock-free queues, heavily tested with LOOM.
- **LMAX Disruptor** (Java, but ideas are universal) — https://github.com/LMAX-Exchange/disruptor
- **Intel DPDK `rte_ring`** (C) — https://dpdk.org/doc/guides/prog_guide/ring_lib.html — Used in network dataplane at 100Gbps+.

### Tools

- **`loom`** (Rust) — https://github.com/tokio-rs/loom — Exhaustive concurrent execution model checker. Essential for validating lock-free code.
- **`perf c2c`** — Linux performance tool for detecting false sharing in production.
- **`cargo miri`** — Rust's interpreter for detecting UB in unsafe code.

---

*End of guide. All code is production-oriented; test thoroughly with your specific workload, cache topology, and OS scheduler before deploying.*

This is going to be a large, dense guide. Let me build it fully.~3,500 lines covering everything from first principles to production hardening. Here's what's in each major section:

**Theory (§1–5):** Formal definition, the vinyl record analogy, power-of-2 math, the mirror-bit strategy, and every disambiguation strategy for the full/empty problem — with the exact equations.

**Architecture (§6–8):** Full taxonomy (SPSC/MPSC/SPMC/MPMC), the cache line false sharing trap with the padded struct fix, the cached remote cursor optimization, and a complete treatment of memory ordering (Relaxed/Acquire/Release) including why SPSC only needs Acq/Rel and not SeqCst, and why this matters differently on x86 vs ARM.

**C implementations (§9):**
- Naive single-threaded with overwrite mode
- POSIX mutex + condvar MPMC with `close()` drain semantics
- Lock-free SPSC with `_Atomic` and the head/tail cache optimization

**Rust implementations (§10):**
- Safe `Option<T>` version
- `MaybeUninit<T>` unsafe version with a correct `Drop` that runs destructors
- Full lock-free SPSC with `Arc<Inner>`, proper `Send`/`Sync` bounds, and a criterion benchmark skeleton

**Go implementations (§11):**
- Annotated dissection of `runtime/chan.go` internals
- Generic `RingBuf[T]` with `sync.Cond` and a `Close()` drain contract
- Lock-free SPSC using `atomic.Pointer` + the `unsafe.Pointer` generic wrapper trick

**MPMC Vyukov Queue (§12):** Full C implementation with per-slot sequence numbers, the CAS loop, and a detailed explanation of why `diff < 0 / == 0 / > 0` maps to full/claimable/contended.

**Everything else:** perf/flamegraph/pprof profiling commands, throughput comparison table, 10 documented pitfalls (including the ARM memory barrier one and ABA), a 10-point security checklist, 9 graded exercises (beginner → advanced including the Disruptor pattern), and curated further reading.