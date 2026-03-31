# Shared Ring Buffer in Linux: A Complete & Comprehensive Guide

> *"The ring buffer is not just a data structure — it is a philosophy of time: what has passed is overwritten, what is present is consumed, and the circle never breaks."*

---

## Table of Contents

1. [Conceptual Foundation](#1-conceptual-foundation)
2. [Memory Layout & Circular Addressing](#2-memory-layout--circular-addressing)
3. [Full/Empty Disambiguation Strategies](#3-fullempty-disambiguation-strategies)
4. [Power-of-Two Sizing: The Modulo Trick](#4-power-of-two-sizing-the-modulo-trick)
5. [Cache Line Alignment & False Sharing](#5-cache-line-alignment--false-sharing)
6. [Memory Ordering & Barriers](#6-memory-ordering--barriers)
7. [Producer-Consumer Variants: SPSC, MPSC, MPMC](#7-producer-consumer-variants-spsc-mpsc-mpmc)
8. [Lock-Free Ring Buffer Design](#8-lock-free-ring-buffer-design)
9. [Shared Memory via mmap](#9-shared-memory-via-mmap)
10. [The Magic Mirroring Trick (Virtual Address Doubling)](#10-the-magic-mirroring-trick-virtual-address-doubling)
11. [Linux Kernel Ring Buffers: kfifo](#11-linux-kernel-ring-buffers-kfifo)
12. [io_uring: The Pinnacle of Ring Buffer Design](#12-io_uring-the-pinnacle-of-ring-buffer-design)
13. [perf Ring Buffer](#13-perf-ring-buffer)
14. [BPF Ring Buffer (bpf_ringbuf)](#14-bpf-ring-buffer-bpf_ringbuf)
15. [Implementation in C: SPSC Lock-Free](#15-implementation-in-c-spsc-lock-free)
16. [Implementation in Rust: Safe SPSC & MPMC](#16-implementation-in-rust-safe-spsc--mpmc)
17. [Implementation in Go: Channels vs Manual Ring Buffer](#17-implementation-in-go-channels-vs-manual-ring-buffer)
18. [Cross-Process Shared Ring Buffer via POSIX Shared Memory](#18-cross-process-shared-ring-buffer-via-posix-shared-memory)
19. [Overflow Policies](#19-overflow-policies)
20. [Benchmarking & Profiling](#20-benchmarking--profiling)
21. [Real-World Design Patterns](#21-real-world-design-patterns)
22. [Common Pitfalls & Subtle Bugs](#22-common-pitfalls--subtle-bugs)
23. [Mental Models for Mastery](#23-mental-models-for-mastery)

---

## 1. Conceptual Foundation

### What Is a Ring Buffer?

A **ring buffer** (also called a **circular buffer** or **circular queue**) is a fixed-size, contiguous block of memory that is treated as if the end wraps around to the beginning — forming a logical circle. It is a FIFO (First In, First Out) data structure.

The core insight: instead of shifting elements on dequeue (O(n)), you simply advance a pointer modularly (O(1)). The buffer "rotates" in place — hence "ring."

```
Index: [0] [1] [2] [3] [4] [5] [6] [7]
        |                               |
        +-- logical wrap: 7 → 0 --------+

  head ----→ [A] [B] [C] [ ] [ ] [ ] [ ] [  ]
                              ↑
                            tail
  Data: A, B, C (3 elements in buffer)
```

### Why Ring Buffers Dominate Systems Programming

| Property | Ring Buffer | Dynamic Queue | Linked List Queue |
|----------|-------------|---------------|-------------------|
| Push complexity | O(1) | O(1) amortized | O(1) |
| Pop complexity | O(1) | O(1) | O(1) |
| Memory allocation | Zero (after init) | Frequent | Per-element |
| Cache friendliness | Excellent | Good | Poor |
| Lock-free feasibility | Natural fit | Hard | Very hard |
| Predictable latency | Yes | No | No |
| Kernel/IPC suitability | Excellent | Poor | Poor |

The **zero allocation after init** property is critical in systems programming. Memory allocation involves locking, system calls, and unpredictable latency — all catastrophic in kernel code, real-time systems, and high-frequency trading.

### The Three Laws of Ring Buffers

1. **The Modular Law**: All indexing is modulo capacity — `index = counter % capacity`
2. **The Separation Law**: Producer owns the tail; consumer owns the head — they never contend for the same variable simultaneously in SPSC
3. **The Capacity Law**: You can store at most `capacity - 1` elements (or `capacity` with a separate count) — never confuse logical fullness with physical fullness

---

## 2. Memory Layout & Circular Addressing

### Physical Memory View

A ring buffer is allocated as a single contiguous array:

```
Physical Memory:
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ e0 │ e1 │ e2 │ e3 │ e4 │ e5 │ e6 │ e7 │  ← capacity = 8
└────┴────┴────┴────┴────┴────┴────┴────┘
  0    1    2    3    4    5    6    7
```

But logically, it wraps:

```
Logical View:
          head=2           tail=6
            ↓                ↓
... [e2] [e3] [e4] [e5] [e6] [e2] [e3] ...
     ↑                         ↑
  oldest                    newest
```

### Monotonically Increasing Counters (The Expert Approach)

Amateur implementations track head and tail as array indices (0 to capacity-1). **Expert implementations use monotonically increasing counters** that are never reset.

```c
// Amateur: index-based (causes subtle bugs at boundary)
uint32_t head = 0;  // resets at capacity
uint32_t tail = 0;  // resets at capacity

// Expert: monotonic counters (never reset)
uint64_t head = 0;  // always increasing
uint64_t tail = 0;  // always increasing

// To get actual index:
size_t head_idx = head & (capacity - 1);  // works only if capacity is power of 2
size_t tail_idx = tail & (capacity - 1);

// Number of elements in buffer:
size_t count = tail - head;  // always correct, even across wraparound
```

**Why monotonic counters are superior:**
- `tail - head` always gives the correct element count — even if counters have wrapped around (for 64-bit counters, wraparound takes ~584 years at 1 billion ops/sec)
- No edge cases at boundary conditions
- Enables easy sequence number tracking for reliability protocols
- Simpler full/empty detection: `tail - head == capacity` means full

### Wraparound Arithmetic

For a capacity of 8 (`0b1000`), the mask is `7` (`0b0111`):

```
counter:  0  1  2  3  4  5  6  7  8  9  10  11 ...
index:    0  1  2  3  4  5  6  7  0  1   2   3 ...
         (counter & 7 = counter % 8 when capacity is power of 2)
```

This bitwise AND (`counter & mask`) replaces modulo (`counter % capacity`), eliminating a division instruction — a 5–20x speedup on most CPUs.

---

## 3. Full/Empty Disambiguation Strategies

The fundamental challenge: with a head and tail pointer, when does `head == tail` mean **empty** vs **full**? This is the most common source of off-by-one bugs.

### Strategy 1: Waste One Slot (Classic)

Reserve one slot, never use it. Buffer is full when `(tail + 1) % capacity == head`.

```c
bool is_empty(rb) { return rb->tail == rb->head; }
bool is_full(rb)  { return (rb->tail + 1) % rb->capacity == rb->head; }
// Usable capacity: capacity - 1
```

**Drawback**: Wastes one slot. Confusing with power-of-two optimizations.

### Strategy 2: Separate Size Counter

Track element count separately.

```c
atomic_size_t count;
bool is_empty(rb) { return atomic_load(&rb->count) == 0; }
bool is_full(rb)  { return atomic_load(&rb->count) == rb->capacity; }
```

**Drawback**: In lock-free MPMC, updating count atomically alongside head/tail requires careful CAS composition.

### Strategy 3: Monotonic Counters (Recommended)

```c
bool is_empty(rb) { return rb->tail == rb->head; }
bool is_full(rb)  { return rb->tail - rb->head == rb->capacity; }
size_t count(rb)  { return rb->tail - rb->head; }
size_t free(rb)   { return rb->capacity - (rb->tail - rb->head); }
```

Clean, correct, no wasted slots. This is what the Linux kernel's `kfifo` and `io_uring` use.

### Strategy 4: Mirror Bit (Knuth's Method)

Use one extra bit beyond the capacity bits. When the high bit differs, the buffer is full; when both high bits are equal and lower bits are equal, it's empty.

```c
// For capacity 8 (indices 0..7), use 4 bits (0..15)
// head=0b0000, tail=0b1000: full (high bits differ, lower bits match)
// head=0b0011, tail=0b1011: full
// head=0b0011, tail=0b0011: empty (all bits match)
bool is_full(rb)  { return rb->tail ^ rb->head == rb->capacity; }
bool is_empty(rb) { return rb->tail == rb->head; }
size_t index(ptr) { return ptr & (rb->capacity - 1); }
```

Used in some network card drivers.

---

## 4. Power-of-Two Sizing: The Modulo Trick

This is one of the most important micro-optimizations in systems programming.

### The Math

For any integer `n` and power-of-two `p`:

```
n % p == n & (p - 1)
```

Proof: `p = 2^k`, so `p - 1 = 0b111...1` (k ones). ANDing with this mask extracts the lower k bits, which is exactly the remainder when dividing by `2^k`.

### Performance Impact

On x86-64:
- `div` instruction: 20–100 clock cycles
- `and` instruction: 1 clock cycle

For a ring buffer processing millions of elements per second, this is the difference between throughput measured in millions vs billions of ops/sec.

### Enforcing Power-of-Two at Initialization

```c
// C: Round up to next power of two
size_t next_pow2(size_t n) {
    if (n == 0) return 1;
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    n |= n >> 32;  // for 64-bit
    return n + 1;
}

// Assert at init time
assert((capacity & (capacity - 1)) == 0 && "Capacity must be power of 2");
size_t mask = capacity - 1;
```

```rust
// Rust
fn next_pow2(n: usize) -> usize {
    n.next_power_of_two()
}

// Usage
assert!(capacity.is_power_of_two(), "Capacity must be power of 2");
let mask = capacity - 1;
let index = counter & mask;
```

```go
// Go
func nextPow2(n uint64) uint64 {
    if n == 0 { return 1 }
    n--
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    n |= n >> 32
    return n + 1
}
```

---

## 5. Cache Line Alignment & False Sharing

This is where most ring buffer implementations fail in practice, even when logically correct.

### The Cache Line Problem

Modern CPUs access memory in **cache lines** of 64 bytes (on x86-64, ARM64). If two variables modified by different threads share a cache line, every write by one thread **invalidates the cache line** for the other — even though they're modifying different variables. This is **false sharing**.

```
Without alignment:
Cache line 0 (bytes 0-63):
  [head: 8 bytes][tail: 8 bytes][...padding...]
  
  Thread A writes head → invalidates cache line for Thread B
  Thread B writes tail → invalidates cache line for Thread A
  → Constant cache line ping-pong = catastrophic performance
```

### The MESI Protocol and Cache Coherence

CPUs maintain cache coherence via the **MESI protocol** (Modified, Exclusive, Shared, Invalid). When a core modifies a cache line:
- It sends an **RFO (Request For Ownership)** to all other cores
- All other cores must **invalidate** their copy
- The modifying core gets exclusive ownership
- Any subsequent read by another core triggers a **cache miss** + transfer

For a ring buffer where producer modifies `tail` and consumer modifies `head`:
- If both fit in one cache line: every producer write forces the consumer to reload head, and vice versa
- Round-trip latency between cores: 40–300 ns on modern x86 systems (NUMA-aware)
- At 1GHz operation frequency: 40–300 wasted cycles per operation

### Solution: Pad to Separate Cache Lines

```c
// BAD: False sharing
struct ring_buffer_bad {
    volatile uint64_t head;
    volatile uint64_t tail;
    size_t capacity;
    void *data;
};

// GOOD: Each hot variable on its own cache line
#define CACHE_LINE_SIZE 64
#define CACHE_ALIGNED   __attribute__((aligned(CACHE_LINE_SIZE)))

struct ring_buffer {
    // Producer-owned: only written by producer
    uint64_t tail CACHE_ALIGNED;
    char _pad0[CACHE_LINE_SIZE - sizeof(uint64_t)];
    
    // Consumer-owned: only written by consumer  
    uint64_t head CACHE_ALIGNED;
    char _pad1[CACHE_LINE_SIZE - sizeof(uint64_t)];
    
    // Read-only after init: shared freely
    size_t  capacity CACHE_ALIGNED;
    size_t  mask;
    void   *data;
};
```

```rust
// Rust: CachePadded from crossbeam
use crossbeam_utils::CachePadded;

struct RingBuffer<T> {
    head: CachePadded<AtomicUsize>,   // consumer's hot variable
    tail: CachePadded<AtomicUsize>,   // producer's hot variable
    capacity: usize,
    mask: usize,
    data: Box<[UnsafeCell<MaybeUninit<T>>]>,
}
```

```go
// Go: Manual padding
type RingBuffer struct {
    _    [0]func() // non-copyable
    tail uint64
    _    [56]byte  // pad to 64 bytes
    head uint64
    _    [56]byte  // pad to 64 bytes
    cap  uint64
    mask uint64
    data unsafe.Pointer
}
```

### Measuring False Sharing

Use `perf stat -e cache-misses,cache-references` or `perf c2c` (cache-to-cache transfer analysis):

```bash
# Detect false sharing
perf c2c record ./your_program
perf c2c report

# Or with Linux perf events
perf stat -e mem_load_l3_hit_retired.xsnp_hitm ./your_program
# HITM = Hit Modified = another core had a modified copy = false sharing signal
```

---

## 6. Memory Ordering & Barriers

This is the deepest and most intellectually demanding aspect of ring buffer implementation. Understanding memory ordering separates average programmers from systems masters.

### The Problem: CPU and Compiler Reordering

Both the **compiler** and the **CPU** reorder memory operations for performance:

```c
// Source code:
data[tail & mask] = value;    // (1) write data
tail++;                        // (2) advance tail

// CPU may execute as:
tail++;                        // (2) first — CONSUMER READS EMPTY SLOT!
data[tail & mask] = value;    // (1) after — data appears after index
```

This is not a theoretical concern — it happens on ARM, POWER, and RISC-V architectures. x86 has a **total store order (TSO)** model that prevents most reorderings, but compilers can still reorder.

### The C11/C++11 Memory Model (and Linux's model)

Four key orderings (from weakest to strongest):

| Ordering | Description | Cost |
|----------|-------------|------|
| `relaxed` | No ordering guarantees | Cheapest |
| `acquire` | All subsequent reads/writes happen after this load | Moderate |
| `release` | All previous reads/writes happen before this store | Moderate |
| `seq_cst` | Global total ordering | Expensive |

### Ring Buffer Memory Ordering Rules

**Producer:**
```c
// Step 1: Write data — no ordering needed yet
store(data[tail & mask], value, memory_order_relaxed);

// Step 2: Publish tail — must be RELEASE
// Ensures: data write is visible BEFORE tail increment to any thread
// that subsequently reads tail with ACQUIRE
atomic_store_explicit(&rb->tail, tail + 1, memory_order_release);
```

**Consumer:**
```c
// Step 1: Read tail — must be ACQUIRE
// Ensures: all stores by producer before release are visible
uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_acquire);

if (head == tail) return EMPTY;

// Step 2: Read data — now safe, no ordering needed
T value = load(data[head & mask], memory_order_relaxed);

// Step 3: Advance head — must be RELEASE (if producer reads head)
atomic_store_explicit(&rb->head, head + 1, memory_order_release);
```

**The Release-Acquire Pair**: This is the fundamental synchronization primitive for lock-free data structures. A `release` store on thread A **happens-before** any `acquire` load on thread B that reads that same value. This establishes a causal ordering edge.

### ARM vs x86: Why This Matters

On x86 (TSO model):
- Loads are never reordered with other loads
- Stores are never reordered with other stores
- Stores are not reordered with prior loads
- Only `store → load` can be reordered (hence `mfence` for seq_cst)
- Release/Acquire cost: essentially free (just compiler barriers)

On ARM (weak memory model):
- Almost any reordering is permitted by the architecture
- `dmb ish` (Data Memory Barrier Inner Shareable) must be emitted for acquire/release
- Cost: 10–50 cycles per barrier

This is why lock-free code that "works" on x86 can silently break on ARM. Always use C11/C++11 atomics or Rust's `std::sync::atomic` — never rely on platform-specific behavior.

### Linux Kernel Memory Barriers

The Linux kernel has its own barrier API (used in `kfifo`, `io_uring`):

```c
// Full memory barrier (both load and store)
mb()   // = smp_mb() in SMP context

// Store barrier: ensures all stores before are visible before stores after
wmb()  // = smp_wmb()

// Load barrier: ensures all loads after see stores that happened before
rmb()  // = smp_rmb()

// Acquire/Release semantics (more modern, preferred)
smp_load_acquire(&var)    // load + acquire barrier
smp_store_release(&var, val) // release barrier + store

// In kfifo (simplified):
// Producer:
kfifo->buf[tail & mask] = data;
smp_store_release(&kfifo->in, tail + 1);  // release: data visible before index

// Consumer:
tail = smp_load_acquire(&kfifo->in);       // acquire: see all data up to tail
data = kfifo->buf[head & mask];
smp_store_release(&kfifo->out, head + 1); // release: done reading
```

---

## 7. Producer-Consumer Variants: SPSC, MPSC, MPMC

### SPSC: Single Producer, Single Consumer

The simplest and most performant variant. Only two threads access the buffer — one producer (owns tail) and one consumer (owns head).

**Key insight**: In SPSC, producer never contends with another producer on `tail`, and consumer never contends with another consumer on `head`. The only shared variables are the counter that the other thread reads — and these are read-only for the reading thread.

**Synchronization needed**: Only `release` on write, `acquire` on read — no CAS, no locks.

**Throughput**: Can exceed 1 billion ops/sec on modern hardware.

### MPSC: Multiple Producers, Single Consumer

Multiple threads push; one thread pops. Common in:
- Logger implementations (many threads log, one writes to disk)
- Task queues (many generators, one executor)
- Network packet processing

**Challenge**: Multiple producers race on `tail`. Solution: atomic CAS (Compare-And-Swap) on tail.

```c
// MPSC push (lock-free)
bool mpsc_push(rb, value) {
    uint64_t tail, next;
    do {
        tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
        if (tail - atomic_load_explicit(&rb->head, memory_order_acquire) == rb->capacity)
            return false; // full
        next = tail + 1;
    } while (!atomic_compare_exchange_weak_explicit(
        &rb->tail, &tail, next,
        memory_order_release, memory_order_relaxed));
    
    rb->data[tail & rb->mask] = value;
    return true;
}
```

**Subtle bug alert**: In the above naive MPSC, after winning the CAS, the producer writes to `data[tail & mask]`. But another producer may have already written to an adjacent slot. The consumer must wait for this slot to become valid. This requires a separate **sequence/version array** per slot — see Section 8.

### MPMC: Multiple Producers, Multiple Consumers

The most general and complex variant. Both producers race on `tail` AND consumers race on `head`.

**Used in**: Thread pools, work-stealing queues, message buses.

**Implementation options**:
1. **Mutex + SPSC**: Simple, correct, highest latency
2. **Disruptor pattern**: Lock-free, uses sequence barriers
3. **Per-slot versioning**: Each slot has an atomic sequence number

---

## 8. Lock-Free Ring Buffer Design

### The Sequence/Version Array Pattern (LMAX Disruptor Concept)

The key insight for MPMC: instead of protecting the whole buffer with a lock, protect **each slot independently** with a version counter.

```
slots: [  0  ][  1  ][  2  ][  3  ]  ← data
seqs:  [ v=0 ][ v=1 ][ v=2 ][ v=3 ]  ← sequence numbers
```

**Rules for sequence numbers:**
- Empty slot at position `i`: `seq == i` (initial state)
- Written slot at position `i`: `seq == i + 1`
- After consumer reads slot `i`: `seq == i + capacity`

```c
struct slot {
    _Atomic uint64_t sequence;
    char data[SLOT_SIZE];
};

// MPMC Push:
bool mpmc_push(rb, data) {
    uint64_t pos;
    struct slot *slot;
    
    pos = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    
    for (;;) {
        slot = &rb->slots[pos & rb->mask];
        uint64_t seq = atomic_load_explicit(&slot->sequence, memory_order_acquire);
        int64_t diff = (int64_t)seq - (int64_t)pos;
        
        if (diff == 0) {
            // Slot is ready to be written
            if (atomic_compare_exchange_weak_explicit(
                    &rb->tail, &pos, pos + 1,
                    memory_order_relaxed, memory_order_relaxed)) {
                break; // we claimed this slot
            }
        } else if (diff < 0) {
            return false; // buffer full
        } else {
            pos = atomic_load_explicit(&rb->tail, memory_order_relaxed);
        }
    }
    
    memcpy(slot->data, data, SLOT_SIZE);
    // Publish: advance sequence to pos + 1, signaling slot is ready to read
    atomic_store_explicit(&slot->sequence, pos + 1, memory_order_release);
    return true;
}
```

### The ABA Problem

Classic CAS pitfall: thread A reads value X, thread B changes X → Y → X, thread A's CAS succeeds even though the state has changed.

In ring buffers with monotonic counters: **ABA is impossible** because counters only increase. This is why monotonic counters are preferred over index-based approaches.

### Compare-Exchange Weak vs Strong

```c
// weak: may spuriously fail (but is faster on LL/SC architectures like ARM)
// Use in loops — the loop retries on spurious failure anyway
atomic_compare_exchange_weak_explicit(...)

// strong: never spuriously fails
// Use when you cannot retry (if/else logic)
atomic_compare_exchange_strong_explicit(...)
```

On ARM, `compare_exchange_weak` maps to `LDREX/STREX` (load-linked/store-conditional) which is more efficient than the software retry loop of `strong`.

### The Fetch-Add Alternative

For MPSC (multiple producers), `fetch_add` is often better than CAS loops:

```c
// Claim a slot atomically — no loop needed!
uint64_t tail = atomic_fetch_add_explicit(&rb->tail, 1, memory_order_relaxed);
// But: the slot may not be immediately writable if another thread is slow
// Must use sequence-based availability check
```

`fetch_add` is **not** a CAS loop — it's a single atomic read-modify-write that always succeeds. On x86, it compiles to the `LOCK XADD` instruction. This is the basis of the Dmitry Vyukov MPMC queue (widely used in Go's runtime).

---

## 9. Shared Memory via mmap

To share a ring buffer between processes, you need shared memory. Linux provides several mechanisms:

### POSIX Shared Memory (`shm_open`)

```c
// Producer process
int fd = shm_open("/my_ring_buffer", O_CREAT | O_RDWR, 0666);
ftruncate(fd, sizeof(struct shared_ring_buffer));
struct shared_ring_buffer *rb = mmap(
    NULL,
    sizeof(struct shared_ring_buffer),
    PROT_READ | PROT_WRITE,
    MAP_SHARED,
    fd, 0
);
```

```c
// Consumer process
int fd = shm_open("/my_ring_buffer", O_RDWR, 0666);
struct shared_ring_buffer *rb = mmap(
    NULL,
    sizeof(struct shared_ring_buffer),
    PROT_READ | PROT_WRITE,
    MAP_SHARED,
    fd, 0
);
```

**Key considerations for cross-process ring buffers:**
- No pointers in the shared struct — use offsets
- Atomics work across processes if using `MAP_SHARED` (the kernel ensures coherence)
- `pthread_mutex_t` can be shared across processes with `PTHREAD_PROCESS_SHARED` attribute
- Data must be in the shared region (not just the header)

### Anonymous mmap (parent-child via fork)

```c
void *shared = mmap(NULL, size,
    PROT_READ | PROT_WRITE,
    MAP_ANONYMOUS | MAP_SHARED,
    -1, 0);

struct ring_buffer *rb = (struct ring_buffer *)shared;
rb->data = (char *)(rb + 1);  // data follows struct in same mmap
rb->capacity = (size - sizeof(*rb));

pid_t pid = fork();
if (pid == 0) {
    // Child: consumer
    consume(rb);
} else {
    // Parent: producer
    produce(rb);
}
```

### memfd_create (Linux 3.17+)

More secure than `shm_open` — not visible on the filesystem:

```c
int fd = memfd_create("ring_buffer", MFD_CLOEXEC);
ftruncate(fd, total_size);
// Pass fd over Unix domain socket to other process
// Other process mmaps the same fd
```

---

## 10. The Magic Mirroring Trick (Virtual Address Doubling)

This is one of the most elegant tricks in Linux systems programming. It eliminates the need for wrap-around logic in the data copy path.

### The Problem with Naive Copying

When reading/writing data that spans the wrap-around point:

```
Buffer: [e5][e6][e7][e0][e1][e2][e3][e4]
         ^head                  ^tail
         
To read 5 elements: e0,e1,e2,e3,e4
Naive: requires TWO memcpy calls:
  memcpy(dst,   data + head, 3);  // e5,e6,e7 (end of buffer)
  memcpy(dst+3, data,        2);  // e0,e1    (beginning of buffer)
```

### The Mirror Solution

Map the same physical memory **twice** in virtual address space, back-to-back:

```
Virtual Address Space:
┌──────────────────────────────┬──────────────────────────────┐
│   First mapping (0x1000)     │   Second mapping (0x2000)    │
│  [e0][e1][e2][e3][e4][e5]... │  [e0][e1][e2][e3][e4][e5]...│
└──────────────────────────────┴──────────────────────────────┘
  Same physical pages                Same physical pages
  
  Now: ANY read of up to `capacity` bytes can be ONE memcpy!
  The wrap-around is invisible.
```

### Implementation

```c
size_t mmap_mirror_ring_buffer(struct ring_buffer *rb, size_t capacity) {
    // capacity must be multiple of page size
    assert(capacity % getpagesize() == 0);
    
    // Create anonymous file
    int fd = memfd_create("ring_mirror", 0);
    ftruncate(fd, capacity);
    
    // Reserve 2x virtual address space
    void *addr = mmap(NULL, 2 * capacity,
        PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    
    // Map first copy
    mmap(addr, capacity,
        PROT_READ | PROT_WRITE,
        MAP_SHARED | MAP_FIXED, fd, 0);
    
    // Map second copy (immediately after)
    mmap((char *)addr + capacity, capacity,
        PROT_READ | PROT_WRITE,
        MAP_SHARED | MAP_FIXED, fd, 0);
    
    rb->data = addr;
    rb->capacity = capacity;
    close(fd);
    return 0;
}

// Now reads/writes never need wrap-around handling:
void produce(rb, data, len) {
    size_t idx = rb->tail & (rb->capacity - 1);
    memcpy((char *)rb->data + idx, data, len);  // SINGLE memcpy, always
    atomic_store_release(&rb->tail, rb->tail + len);
}
```

**Used by**: Many network packet capture systems, audio processing frameworks (JACK uses this), and streaming media pipelines.

**Cost**: Uses 2x virtual address space. On 64-bit systems with 48-bit virtual address space (256 TB), this is practically free.

---

## 11. Linux Kernel Ring Buffers: kfifo

`kfifo` is the kernel's canonical lock-free SPSC ring buffer. Located in `include/linux/kfifo.h` and `lib/kfifo.c`.

### kfifo Design Principles

```c
// From linux/kfifo.h (simplified)
struct __kfifo {
    unsigned int in;    // tail (producer counter)
    unsigned int out;   // head (consumer counter)
    unsigned int mask;  // capacity - 1 (power of 2 guaranteed)
    unsigned int esize; // element size
    void        *data;  // ring buffer storage
};
```

**Notable choices:**
- Uses `unsigned int` (32-bit) for counters — wraparound at ~4 billion, which is safe
- `mask = capacity - 1` stored explicitly (no division)
- Separate `esize` enables type-generic operation
- Lock-free for SPSC; external lock required for MPMC

### kfifo's Memory Barrier Usage

```c
// kfifo_in (producer path, simplified):
static inline unsigned int kfifo_in(struct kfifo *fifo, const void *buf, unsigned int len) {
    unsigned int l;
    len = min(kfifo_avail(fifo), len);
    
    l = min(len, fifo->mask + 1 - (fifo->in & fifo->mask));
    memcpy(fifo->buf + (fifo->in & fifo->mask), buf, l);
    memcpy(fifo->buf, buf + l, len - l);
    
    // CRITICAL: Full memory barrier before advancing 'in'
    // smp_wmb ensures data is visible before in counter update
    smp_wmb();
    fifo->in += len;
    return len;
}

// kfifo_out (consumer path, simplified):
static inline unsigned int kfifo_out(struct kfifo *fifo, void *buf, unsigned int len) {
    unsigned int l;
    len = min(kfifo_len(fifo), len);
    
    // CRITICAL: Ensure we see all data up to 'in' before reading
    smp_rmb();
    
    l = min(len, fifo->mask + 1 - (fifo->out & fifo->mask));
    memcpy(buf, fifo->buf + (fifo->out & fifo->mask), l);
    memcpy(buf + l, fifo->buf, len - l);
    
    smp_mb();
    fifo->out += len;
    return len;
}
```

### kfifo Macro API

Modern `kfifo` uses C macros for type safety without generics:

```c
// Static declaration
DECLARE_KFIFO(my_fifo, int, 64);  // fifo of ints, capacity 64
INIT_KFIFO(my_fifo);

// Dynamic allocation
struct kfifo my_fifo;
kfifo_alloc(&my_fifo, sizeof(int) * 64, GFP_KERNEL);

// Operations
kfifo_put(&my_fifo, value);    // push one element
kfifo_get(&my_fifo, &value);   // pop one element
kfifo_peek(&my_fifo, &value);  // peek without consuming
kfifo_len(&my_fifo);           // number of elements
kfifo_avail(&my_fifo);         // free slots
kfifo_is_empty(&my_fifo);
kfifo_is_full(&my_fifo);

// Batch operations (efficient for byte streams)
kfifo_in(&my_fifo, buf, count);
kfifo_out(&my_fifo, buf, count);
```

---

## 12. io_uring: The Pinnacle of Ring Buffer Design

`io_uring` (introduced in Linux 5.1, 2019) is arguably the most sophisticated ring buffer design in production use. It achieves near-zero-overhead async I/O through a pair of shared ring buffers between userspace and kernel.

### The Two-Ring Architecture

```
Userspace                         Kernel
    │                               │
    │  SQ Ring (Submission Queue)   │
    │  ┌─────────────────────────┐  │
    │  │ head (kernel-owned)     │──┼→ kernel reads here
    │  │ tail (user-owned)       │←─┼─ user writes here
    │  │ sqes[] (SQ entries)     │  │
    │  └─────────────────────────┘  │
    │                               │
    │  CQ Ring (Completion Queue)   │
    │  ┌─────────────────────────┐  │
    │  │ head (user-owned)       │←─┼─ user reads here
    │  │ tail (kernel-owned)     │──┼→ kernel writes here
    │  │ cqes[] (CQ entries)     │  │
    │  └─────────────────────────┘  │
```

**Key innovation**: Both rings are **mmap'd into userspace** — no syscall needed to submit or retrieve I/O completions in the common case.

### io_uring Memory Layout

```c
// From linux/io_uring.h

// Submission Queue Entry (SQE) - 64 bytes
struct io_uring_sqe {
    __u8    opcode;      // IORING_OP_READ, WRITE, etc.
    __u8    flags;
    __u16   ioprio;
    __s32   fd;
    __u64   off;         // file offset
    __u64   addr;        // buffer address
    __u32   len;         // buffer length
    __u32   rw_flags;
    __u64   user_data;   // passed back in CQE for correlation
    // ... more fields
};

// Completion Queue Entry (CQE) - 16 bytes
struct io_uring_cqe {
    __u64   user_data;  // matches SQE's user_data
    __s32   res;        // result (bytes or error)
    __u32   flags;
};

// Shared ring control structure (mmap'd)
struct io_uring_sq {
    unsigned *khead;     // kernel's head pointer (mmap'd kernel memory)
    unsigned *ktail;     // kernel's tail pointer
    unsigned *kring_mask;
    unsigned *kring_entries;
    unsigned *kflags;
    unsigned *kdropped;
    unsigned *array;     // SQE index array (indirection layer!)
    struct io_uring_sqe *sqes;  // actual SQE array
    // ... userspace bookkeeping
};
```

### The Indirection Layer in SQ Ring

This is a subtle and important design choice. The SQ ring doesn't directly contain SQEs — it contains **indices** into the SQE array:

```
SQ Ring: [2][5][1][3]  ← indices
SQE Array: [sqe0][sqe1][sqe2][sqe3][sqe4][sqe5]
                   ↑          ↑
            indexed by 1   indexed by 2 (first in queue)
```

**Why?** SQEs are 64 bytes each. Moving 64-byte entries around in the ring would be expensive. Moving 4-byte indices is cheap. Also, userspace can prepare SQEs in any order and only commit them to the ring when ready — enabling batching.

### io_uring Submission (Userspace, No Syscall)

```c
// Get next available SQE slot
struct io_uring_sqe *io_uring_get_sqe(struct io_uring *ring) {
    struct io_uring_sq *sq = &ring->sq;
    unsigned next = sq->sqe_tail + 1;
    
    if (next - sq->sqe_head > *sq->kring_entries)
        return NULL; // SQ ring full
    
    // Return pointer to SQE (in mmap'd region)
    return &sq->sqes[sq->sqe_tail++ & *sq->kring_mask];
}

// Submit: update tail atomically
int io_uring_submit(struct io_uring *ring) {
    struct io_uring_sq *sq = &ring->sq;
    unsigned submitted = sq->sqe_tail - sq->sqe_head;
    
    // Publish to kernel: write tail with release semantics
    io_uring_smp_store_release(sq->ktail, *sq->ktail + submitted);
    
    // If SQPOLL mode: kernel thread polls, no syscall needed
    // Otherwise: syscall to wake kernel
    if (!(ring->flags & IORING_SETUP_SQPOLL))
        return syscall(__NR_io_uring_enter, ring->ring_fd, submitted, 0, 0, NULL, 0);
    return submitted;
}
```

### io_uring SQPOLL Mode: True Zero-Syscall I/O

With `IORING_SETUP_SQPOLL`, the kernel spawns a dedicated thread that polls the SQ ring continuously. Userspace just writes to the shared ring and the kernel thread picks it up — **no syscall at all** for I/O submission.

This reduces per-operation overhead from ~2 microseconds (syscall + context switch) to ~50 nanoseconds (cache line exchange).

### io_uring Completion Harvesting

```c
// Userspace reaps completions without syscall
struct io_uring_cqe *io_uring_peek_cqe(struct io_uring *ring) {
    struct io_uring_cq *cq = &ring->cq;
    struct io_uring_cqe *cqe = NULL;
    unsigned mask = *cq->kring_mask;
    
    // Acquire-load of tail: ensures we see completed data
    unsigned tail = io_uring_smp_load_acquire(cq->ktail);
    
    if (cq->khead != tail) {
        // There's a completion available
        cqe = &cq->cqes[*cq->khead & mask];
    }
    return cqe;
}

void io_uring_cqe_seen(struct io_uring *ring, struct io_uring_cqe *cqe) {
    // Advance head with release semantics — tell kernel we consumed this CQE
    io_uring_smp_store_release(ring->cq.khead, *ring->cq.khead + 1);
}
```

### io_uring Performance Numbers (Real-World)

- Traditional `read()` syscall: ~2 μs per operation
- `epoll` + `read()`: ~3 μs per operation (includes epoll overhead)
- `io_uring` with syscall: ~0.5 μs per operation
- `io_uring` with SQPOLL (no syscall): ~0.05–0.1 μs per operation
- **20–40x improvement over traditional I/O**

---

## 13. perf Ring Buffer

The `perf` subsystem uses per-CPU ring buffers to stream events (hardware performance counters, tracepoints, kprobes) from kernel to userspace with minimal overhead.

### perf_event mmap Layout

```c
// struct perf_event_mmap_page — first page of mmap
struct perf_event_mmap_page {
    __u32 version;
    __u32 compat_version;
    __u32 lock;          // seqlock for reading
    __u32 index;
    __s64 offset;
    __u64 time_enabled;
    __u64 time_running;
    union {
        __u64 capabilities;
        struct { /* capability bits */ };
    };
    __u16 pmc_width;
    __u16 time_shift;
    __u32 time_mult;
    __u64 time_offset;
    // ... 
    __u64 data_head;    // tail: kernel writes here (ring head for producer)
    __u64 data_tail;    // head: user reads here (ring tail for consumer)
    __u64 data_offset;  // offset to actual ring data
    __u64 data_size;    // size of ring data
    // ...
};
```

### Seqlock for Consistent Reads

`perf` uses a **seqlock** for reading hardware counters atomically (which are 64-bit on 32-bit systems — non-atomic naturally):

```c
// Reading a hardware counter with seqlock:
uint64_t read_pmc_with_seqlock(struct perf_event_mmap_page *pc) {
    uint32_t seq, cyc;
    uint64_t time, count;
    
    do {
        // Read sequence number (odd = writer holds lock)
        seq = pc->lock;
        rmb();
        
        // Read the value
        count = pc->offset;
        // ... more reads
        
        rmb();
        // If lock hasn't changed, we got a consistent read
    } while (pc->lock != seq);
    
    return count;
}
```

### Reading perf Events from Userspace

```c
void read_perf_ring_buffer(int fd, size_t mmap_size) {
    // mmap: 1 page header + N pages ring data
    struct perf_event_mmap_page *header = mmap(
        NULL, mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    
    void *data_base = (char *)header + header->data_offset;
    uint64_t data_size = header->data_size;
    uint64_t mask = data_size - 1;
    
    // Consumer loop
    uint64_t tail = header->data_tail;
    while (true) {
        // Acquire-load of head
        uint64_t head = __atomic_load_n(&header->data_head, __ATOMIC_ACQUIRE);
        
        while (tail != head) {
            // Read event at current position
            struct perf_event_header *event =
                (struct perf_event_header *)((char *)data_base + (tail & mask));
            
            process_event(event);
            tail += event->size;
        }
        
        // Update tail (release: tell kernel we've consumed up to here)
        __atomic_store_n(&header->data_tail, tail, __ATOMIC_RELEASE);
        
        // Wait for more events (poll or spin)
        poll_or_sleep(fd);
    }
}
```

---

## 14. BPF Ring Buffer (bpf_ringbuf)

Introduced in Linux 5.8, `bpf_ringbuf` supersedes `BPF_MAP_TYPE_PERF_EVENT_ARRAY` for event streaming from BPF programs to userspace.

### Advantages over perf_event

| Feature | perf_event | bpf_ringbuf |
|---------|-----------|-------------|
| Per-CPU buffers | Yes (high overhead) | No (shared, efficient) |
| Variable-size records | Partial | Native |
| Memory efficiency | Poor (per-CPU waste) | Excellent |
| Order preservation | No (per-CPU) | Yes |
| API complexity | High | Low |

### bpf_ringbuf Design

The key innovation: **reservation-based protocol**. The BPF program reserves space, writes data, then commits — all without per-slot locking.

```c
// In BPF program (kernel side):
struct event {
    u32 pid;
    u64 timestamp;
    char comm[16];
};

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) {
    // Reserve space in ring buffer (non-blocking)
    struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) return 0;  // buffer full
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->timestamp = bpf_ktime_get_ns();
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    
    // Commit (makes visible to userspace) or discard
    bpf_ringbuf_submit(e, 0);  // or bpf_ringbuf_discard(e, 0)
    return 0;
}
```

```c
// Userspace consumer using libbpf:
static int handle_event(void *ctx, void *data, size_t size) {
    struct event *e = data;
    printf("PID %u execve at %llu: %s\n", e->pid, e->timestamp, e->comm);
    return 0;
}

int main() {
    struct ring_buffer *rb = ring_buffer__new(
        bpf_map__fd(skel->maps.rb),
        handle_event, NULL, NULL);
    
    while (!stop) {
        ring_buffer__poll(rb, 100 /* timeout_ms */);
    }
}
```

### bpf_ringbuf Internal Layout

```
┌────────────────────────────────────────────────────────────┐
│ consumer_pos (8 bytes, cache-aligned)                      │ ← userspace reads
├────────────────────────────────────────────────────────────┤
│ [64 byte padding]                                          │
├────────────────────────────────────────────────────────────┤
│ producer_pos (8 bytes, cache-aligned)                      │ ← kernel writes
├────────────────────────────────────────────────────────────┤
│ [64 byte padding]                                          │
├────────────────────────────────────────────────────────────┤
│ Data pages (ring buffer, mmap'd twice for mirror trick)    │
│ Each record: [len: 4 bytes][flags: 4 bytes][data: len]     │
└────────────────────────────────────────────────────────────┘
```

---

## 15. Implementation in C: SPSC Lock-Free

A complete, production-quality SPSC ring buffer in C11:

```c
// spsc_ring.h
#ifndef SPSC_RING_H
#define SPSC_RING_H

#include <stdatomic.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define CACHE_LINE_SIZE 64
#define CACHE_ALIGNED   __attribute__((aligned(CACHE_LINE_SIZE)))

// SPSC Ring Buffer — lock-free for single producer + single consumer
// All capacity constraints: must be power of 2
typedef struct spsc_ring {
    // --- Producer's hot cache line ---
    _Atomic uint64_t tail CACHE_ALIGNED;          // written by producer
    uint64_t         tail_cache;                   // cached copy (no atomic needed)
    char             _pad0[CACHE_LINE_SIZE - 2 * sizeof(uint64_t)];
    
    // --- Consumer's hot cache line ---
    _Atomic uint64_t head CACHE_ALIGNED;          // written by consumer
    uint64_t         head_cache;                   // cached copy
    char             _pad1[CACHE_LINE_SIZE - 2 * sizeof(uint64_t)];
    
    // --- Shared read-only metadata ---
    uint64_t capacity CACHE_ALIGNED;
    uint64_t mask;
    size_t   elem_size;
    char     *data;
} spsc_ring_t;

// Initialize ring buffer. capacity MUST be power of 2.
static inline int spsc_ring_init(spsc_ring_t *rb, size_t capacity, size_t elem_size) {
    assert(capacity > 0 && (capacity & (capacity - 1)) == 0
           && "Capacity must be a power of 2");
    
    rb->data = (char *)aligned_alloc(CACHE_LINE_SIZE, capacity * elem_size);
    if (!rb->data) return -1;
    
    atomic_init(&rb->tail, 0);
    atomic_init(&rb->head, 0);
    rb->tail_cache = 0;
    rb->head_cache = 0;
    rb->capacity = capacity;
    rb->mask = capacity - 1;
    rb->elem_size = elem_size;
    return 0;
}

void spsc_ring_destroy(spsc_ring_t *rb) {
    free(rb->data);
}

// Producer: push one element. Returns true on success, false if full.
static inline bool spsc_ring_push(spsc_ring_t *rb, const void *elem) {
    // Load tail relaxed (only we write it)
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    
    // Use cached head to avoid atomic load every push
    // Only refresh cache when buffer appears full
    uint64_t head_cache = rb->head_cache;
    
    if (__builtin_expect(tail - head_cache == rb->capacity, 0)) {
        // Refresh head cache: acquire to see all consumer writes
        head_cache = atomic_load_explicit(&rb->head, memory_order_acquire);
        rb->head_cache = head_cache;
        if (tail - head_cache == rb->capacity) {
            return false; // truly full
        }
    }
    
    // Write element to slot
    memcpy(rb->data + (tail & rb->mask) * rb->elem_size, elem, rb->elem_size);
    
    // Publish: release ensures data write is visible before tail increment
    atomic_store_explicit(&rb->tail, tail + 1, memory_order_release);
    return true;
}

// Consumer: pop one element. Returns true on success, false if empty.
static inline bool spsc_ring_pop(spsc_ring_t *rb, void *elem) {
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint64_t tail_cache = rb->tail_cache;
    
    if (__builtin_expect(head == tail_cache, 0)) {
        // Refresh tail cache: acquire to see all producer writes
        tail_cache = atomic_load_explicit(&rb->tail, memory_order_acquire);
        rb->tail_cache = tail_cache;
        if (head == tail_cache) {
            return false; // truly empty
        }
    }
    
    // Read element from slot (data is now guaranteed visible via acquire)
    memcpy(elem, rb->data + (head & rb->mask) * rb->elem_size, rb->elem_size);
    
    // Advance head: release so producer sees updated head
    atomic_store_explicit(&rb->head, head + 1, memory_order_release);
    return true;
}

// Peek without consuming
static inline bool spsc_ring_peek(spsc_ring_t *rb, void *elem) {
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_acquire);
    
    if (head == tail) return false;
    
    memcpy(elem, rb->data + (head & rb->mask) * rb->elem_size, rb->elem_size);
    return true;
}

static inline uint64_t spsc_ring_size(spsc_ring_t *rb) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_acquire);
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_acquire);
    return tail - head;
}

static inline bool spsc_ring_is_empty(spsc_ring_t *rb) {
    return spsc_ring_size(rb) == 0;
}

static inline bool spsc_ring_is_full(spsc_ring_t *rb) {
    return spsc_ring_size(rb) == rb->capacity;
}

#endif // SPSC_RING_H
```

### Usage Example in C

```c
#include <stdio.h>
#include <pthread.h>
#include "spsc_ring.h"

typedef struct { uint64_t value; } Message;

static spsc_ring_t g_ring;

void *producer_thread(void *arg) {
    Message msg;
    for (uint64_t i = 0; i < 10000000; i++) {
        msg.value = i;
        while (!spsc_ring_push(&g_ring, &msg))
            ; // spin (or add backoff)
    }
    return NULL;
}

void *consumer_thread(void *arg) {
    Message msg;
    uint64_t expected = 0;
    while (expected < 10000000) {
        if (spsc_ring_pop(&g_ring, &msg)) {
            assert(msg.value == expected++);
        }
    }
    return NULL;
}

int main(void) {
    spsc_ring_init(&g_ring, 1024, sizeof(Message));
    
    pthread_t prod, cons;
    pthread_create(&prod, NULL, producer_thread, NULL);
    pthread_create(&cons, NULL, consumer_thread, NULL);
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);
    
    spsc_ring_destroy(&g_ring);
    printf("All messages transferred correctly.\n");
    return 0;
}

// Compile: gcc -O2 -std=c11 -pthread -o ring_test ring_test.c
```

### Key Optimization: Cached Counter Trick

Notice `head_cache` and `tail_cache` in the implementation. This is a critical optimization:

- The producer caches the last-seen head value. It only refreshes via atomic load when the buffer appears full.
- In the common case (buffer not full), the producer avoids an expensive atomic load of head every iteration.
- On x86, atomic loads are cheap (just compiler barriers), but on ARM they involve memory barriers — this cache eliminates them.

**Effect**: Reduces the number of cache line transfers by 2–5x in producer-heavy workloads.

---

## 16. Implementation in Rust: Safe SPSC & MPMC

### Safe SPSC Ring Buffer in Rust

```rust
// src/spsc_ring.rs
use std::sync::atomic::{AtomicU64, Ordering};
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use crossbeam_utils::CachePadded;

/// Single-Producer Single-Consumer lock-free ring buffer.
/// Safety invariant: only one thread calls push(), only one calls pop().
pub struct SpscRing<T> {
    head: CachePadded<AtomicU64>,
    tail: CachePadded<AtomicU64>,
    capacity: usize,
    mask: usize,
    // UnsafeCell for interior mutability; MaybeUninit to avoid drop on uninitialized
    buffer: Box<[UnsafeCell<MaybeUninit<T>>]>,
}

// SAFETY: SpscRing is Send because we guarantee single-producer/single-consumer access
unsafe impl<T: Send> Send for SpscRing<T> {}
unsafe impl<T: Send> Sync for SpscRing<T> {}

impl<T> SpscRing<T> {
    /// Create a new ring buffer. `capacity` must be a power of two.
    pub fn new(capacity: usize) -> Self {
        assert!(capacity.is_power_of_two(), "Capacity must be power of two");
        assert!(capacity > 0);
        
        let buffer = (0..capacity)
            .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
            .collect::<Vec<_>>()
            .into_boxed_slice();
        
        Self {
            head: CachePadded::new(AtomicU64::new(0)),
            tail: CachePadded::new(AtomicU64::new(0)),
            capacity,
            mask: capacity - 1,
            buffer,
        }
    }
    
    /// Push an element. Returns Err(value) if the buffer is full.
    ///
    /// SAFETY: Must be called from exactly one thread at a time (producer).
    pub fn push(&self, value: T) -> Result<(), T> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        
        if tail.wrapping_sub(head) == self.capacity as u64 {
            return Err(value); // full
        }
        
        let slot = &self.buffer[(tail as usize) & self.mask];
        // SAFETY: We own this slot (producer). No consumer touches slots above head.
        unsafe {
            (*slot.get()).write(value);
        }
        
        // Release: make the write visible before advancing tail
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        Ok(())
    }
    
    /// Pop an element. Returns None if empty.
    ///
    /// SAFETY: Must be called from exactly one thread at a time (consumer).
    pub fn pop(&self) -> Option<T> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        
        if head == tail {
            return None; // empty
        }
        
        let slot = &self.buffer[(head as usize) & self.mask];
        // SAFETY: Slot at head is initialized (producer wrote it, tail > head).
        let value = unsafe { (*slot.get()).assume_init_read() };
        
        // Release: signal to producer that this slot is free
        self.head.store(head.wrapping_add(1), Ordering::Release);
        Some(value)
    }
    
    pub fn len(&self) -> usize {
        let tail = self.tail.load(Ordering::Acquire);
        let head = self.head.load(Ordering::Acquire);
        tail.wrapping_sub(head) as usize
    }
    
    pub fn is_empty(&self) -> bool { self.len() == 0 }
    pub fn is_full(&self) -> bool { self.len() == self.capacity }
    pub fn capacity(&self) -> usize { self.capacity }
}

impl<T> Drop for SpscRing<T> {
    fn drop(&mut self) {
        // Drain remaining elements to run their destructors
        while self.pop().is_some() {}
    }
}
```

### Splitting into Producer/Consumer Handles (Idiomatic Rust)

```rust
use std::sync::Arc;

pub struct Producer<T>(Arc<SpscRing<T>>);
pub struct Consumer<T>(Arc<SpscRing<T>>);

pub fn channel<T>(capacity: usize) -> (Producer<T>, Consumer<T>) {
    let ring = Arc::new(SpscRing::new(capacity));
    (Producer(ring.clone()), Consumer(ring))
}

impl<T> Producer<T> {
    pub fn push(&self, value: T) -> Result<(), T> {
        self.0.push(value)
    }
}

impl<T> Consumer<T> {
    pub fn pop(&self) -> Option<T> {
        self.0.pop()
    }
}

// Usage:
fn main() {
    let (tx, rx) = channel::<u64>(1024);
    
    let producer = std::thread::spawn(move || {
        for i in 0..1_000_000_u64 {
            while tx.push(i).is_err() {
                std::hint::spin_loop();
            }
        }
    });
    
    let consumer = std::thread::spawn(move || {
        let mut count = 0u64;
        while count < 1_000_000 {
            if let Some(v) = rx.pop() {
                assert_eq!(v, count);
                count += 1;
            } else {
                std::hint::spin_loop();
            }
        }
    });
    
    producer.join().unwrap();
    consumer.join().unwrap();
}
```

### MPMC Ring Buffer in Rust (Sequence-Based)

```rust
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use crossbeam_utils::CachePadded;

struct Slot<T> {
    sequence: AtomicUsize,
    data: UnsafeCell<MaybeUninit<T>>,
}

pub struct MpmcRing<T> {
    buffer: Box<[Slot<T>]>,
    capacity: usize,
    mask: usize,
    enqueue_pos: CachePadded<AtomicUsize>, // tail
    dequeue_pos: CachePadded<AtomicUsize>, // head
}

unsafe impl<T: Send> Send for MpmcRing<T> {}
unsafe impl<T: Send> Sync for MpmcRing<T> {}

impl<T> MpmcRing<T> {
    pub fn new(capacity: usize) -> Self {
        assert!(capacity.is_power_of_two());
        
        let buffer: Box<[Slot<T>]> = (0..capacity)
            .map(|i| Slot {
                sequence: AtomicUsize::new(i), // Initial sequence = index
                data: UnsafeCell::new(MaybeUninit::uninit()),
            })
            .collect::<Vec<_>>()
            .into_boxed_slice();
        
        Self {
            buffer,
            capacity,
            mask: capacity - 1,
            enqueue_pos: CachePadded::new(AtomicUsize::new(0)),
            dequeue_pos: CachePadded::new(AtomicUsize::new(0)),
        }
    }
    
    pub fn push(&self, value: T) -> Result<(), T> {
        let mut pos = self.enqueue_pos.load(Ordering::Relaxed);
        
        loop {
            let slot = &self.buffer[pos & self.mask];
            let seq = slot.sequence.load(Ordering::Acquire);
            let diff = seq as isize - pos as isize;
            
            match diff.cmp(&0) {
                std::cmp::Ordering::Equal => {
                    // Slot is ready; try to claim it
                    match self.enqueue_pos.compare_exchange_weak(
                        pos, pos + 1,
                        Ordering::Relaxed, Ordering::Relaxed,
                    ) {
                        Ok(_) => break,           // claimed
                        Err(p) => pos = p,        // retry with updated pos
                    }
                }
                std::cmp::Ordering::Less => {
                    // Buffer is full (sequence is behind pos)
                    return Err(value);
                }
                std::cmp::Ordering::Greater => {
                    // Another producer advanced; reload pos
                    pos = self.enqueue_pos.load(Ordering::Relaxed);
                }
            }
        }
        
        let slot = &self.buffer[pos & self.mask];
        // SAFETY: We exclusively own this slot after winning the CAS
        unsafe { (*slot.data.get()).write(value); }
        
        // Publish: sequence = pos + 1 signals slot is ready to read
        slot.sequence.store(pos + 1, Ordering::Release);
        Ok(())
    }
    
    pub fn pop(&self) -> Option<T> {
        let mut pos = self.dequeue_pos.load(Ordering::Relaxed);
        
        loop {
            let slot = &self.buffer[pos & self.mask];
            let seq = slot.sequence.load(Ordering::Acquire);
            let diff = seq as isize - (pos + 1) as isize;
            
            match diff.cmp(&0) {
                std::cmp::Ordering::Equal => {
                    // Slot has data; try to claim it
                    match self.dequeue_pos.compare_exchange_weak(
                        pos, pos + 1,
                        Ordering::Relaxed, Ordering::Relaxed,
                    ) {
                        Ok(_) => break,
                        Err(p) => pos = p,
                    }
                }
                std::cmp::Ordering::Less => {
                    return None; // empty
                }
                std::cmp::Ordering::Greater => {
                    pos = self.dequeue_pos.load(Ordering::Relaxed);
                }
            }
        }
        
        let slot = &self.buffer[pos & self.mask];
        // SAFETY: We exclusively own this slot after winning the CAS
        let value = unsafe { (*slot.data.get()).assume_init_read() };
        
        // Reset slot sequence for next round: pos + capacity
        slot.sequence.store(pos + self.capacity, Ordering::Release);
        Some(value)
    }
}
```

---

## 17. Implementation in Go: Channels vs Manual Ring Buffer

### When to Use Channels vs Manual Ring Buffer in Go

| Use Case | Go Channel | Manual Ring Buffer |
|----------|------------|-------------------|
| General communication | ✓ | Overkill |
| > 1M ops/sec | Limited | ✓ |
| Known fixed capacity | ✓ buffered | ✓ |
| Lock-free requirement | No (uses mutex) | ✓ |
| Cross-process | No | ✓ |
| Zero allocations | No | ✓ |

### Go's Buffered Channel Internals

Go's channels are implemented as ring buffers internally (`runtime/chan.go`):

```go
// From Go runtime (simplified)
type hchan struct {
    qcount   uint           // total data in queue
    dataqsiz uint           // size of circular queue
    buf      unsafe.Pointer // pointer to array of dataqsiz elements
    elemsize uint16
    closed   uint32
    sendx    uint           // send index (tail)
    recvx    uint           // receive index (head)
    recvq    waitq          // blocked receivers
    sendq    waitq          // blocked senders
    lock     mutex          // protects all fields
}
```

**Key takeaway**: Go channels use a mutex. For ultra-high-throughput scenarios, this is a bottleneck.

### Manual Lock-Free SPSC in Go

```go
// spsc_ring.go
package ringbuffer

import (
    "runtime"
    "sync/atomic"
    "unsafe"
)

const cacheLineSize = 64

type SpscRing[T any] struct {
    // Producer hot: tail counter
    tail uint64
    _    [cacheLineSize - 8]byte

    // Consumer hot: head counter
    head uint64
    _    [cacheLineSize - 8]byte

    // Shared read-only
    cap  uint64
    mask uint64
    buf  []T
}

func NewSpscRing[T any](capacity uint64) *SpscRing[T] {
    if capacity == 0 || (capacity&(capacity-1)) != 0 {
        panic("capacity must be a power of two")
    }
    return &SpscRing[T]{
        cap:  capacity,
        mask: capacity - 1,
        buf:  make([]T, capacity),
    }
}

// Push adds an element. Returns false if full.
// Must be called from one goroutine only (producer).
func (r *SpscRing[T]) Push(v T) bool {
    tail := atomic.LoadUint64(&r.tail)
    head := atomic.LoadUint64(&r.head) // acquire semantics via LoadUint64

    if tail-head == r.cap {
        return false // full
    }

    r.buf[tail&r.mask] = v

    // Release store: ensure data is visible before tail update
    atomic.StoreUint64(&r.tail, tail+1)
    return true
}

// Pop removes and returns an element. Returns false if empty.
// Must be called from one goroutine only (consumer).
func (r *SpscRing[T]) Pop() (T, bool) {
    head := atomic.LoadUint64(&r.head)
    tail := atomic.LoadUint64(&r.tail) // acquire semantics

    if head == tail {
        var zero T
        return zero, false // empty
    }

    v := r.buf[head&r.mask]

    // Release store: signal slot is free to producer
    atomic.StoreUint64(&r.head, head+1)
    return v, true
}

func (r *SpscRing[T]) Len() uint64 {
    tail := atomic.LoadUint64(&r.tail)
    head := atomic.LoadUint64(&r.head)
    return tail - head
}

// SpinPush spins until push succeeds (blocking producer)
func (r *SpscRing[T]) SpinPush(v T) {
    for !r.Push(v) {
        runtime.Gosched() // yield to scheduler instead of burning CPU
    }
}

// SpinPop spins until pop succeeds (blocking consumer)
func (r *SpscRing[T]) SpinPop() T {
    for {
        if v, ok := r.Pop(); ok {
            return v
        }
        runtime.Gosched()
    }
}
```

**Note on Go memory model**: `sync/atomic` operations in Go provide sequential consistency by default (stronger than acquire/release). This means on ARM, Go's `atomic.StoreUint64` emits a `dmb` instruction. For maximum performance on ARM, this is conservative, but Go provides no weaker ordering API — correctness over performance is Go's philosophy.

### Cross-Process Ring Buffer in Go via mmap

```go
// mmap_ring.go
package ringbuffer

import (
    "fmt"
    "os"
    "sync/atomic"
    "syscall"
    "unsafe"
)

// SharedHeader is the control structure in shared memory
// All fields are atomic; no pointers (only offsets are valid cross-process)
type SharedHeader struct {
    Tail     uint64
    _        [56]byte // pad to 64 bytes
    Head     uint64
    _        [56]byte
    Capacity uint64
    Mask     uint64
    ElemSize uint64
}

type MmapRing struct {
    hdr  *SharedHeader
    data unsafe.Pointer
    size int
}

func CreateMmapRing(path string, capacity, elemSize uint64) (*MmapRing, error) {
    if capacity == 0 || (capacity&(capacity-1)) != 0 {
        return nil, fmt.Errorf("capacity must be power of two")
    }

    headerSize := uint64(unsafe.Sizeof(SharedHeader{}))
    totalSize := int(headerSize + capacity*elemSize)

    f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0666)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    if err := f.Truncate(int64(totalSize)); err != nil {
        return nil, err
    }

    data, err := syscall.Mmap(
        int(f.Fd()), 0, totalSize,
        syscall.PROT_READ|syscall.PROT_WRITE,
        syscall.MAP_SHARED,
    )
    if err != nil {
        return nil, err
    }

    hdr := (*SharedHeader)(unsafe.Pointer(&data[0]))
    hdr.Capacity = capacity
    hdr.Mask = capacity - 1
    hdr.ElemSize = elemSize
    atomic.StoreUint64(&hdr.Head, 0)
    atomic.StoreUint64(&hdr.Tail, 0)

    return &MmapRing{
        hdr:  hdr,
        data: unsafe.Pointer(&data[headerSize]),
        size: totalSize,
    }, nil
}

func OpenMmapRing(path string) (*MmapRing, error) {
    f, err := os.OpenFile(path, os.O_RDWR, 0666)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    stat, _ := f.Stat()
    totalSize := int(stat.Size())

    data, err := syscall.Mmap(
        int(f.Fd()), 0, totalSize,
        syscall.PROT_READ|syscall.PROT_WRITE,
        syscall.MAP_SHARED,
    )
    if err != nil {
        return nil, err
    }

    hdr := (*SharedHeader)(unsafe.Pointer(&data[0]))
    headerSize := uint64(unsafe.Sizeof(SharedHeader{}))

    return &MmapRing{
        hdr:  hdr,
        data: unsafe.Pointer(&data[headerSize]),
        size: totalSize,
    }, nil
}

func (r *MmapRing) Write(src unsafe.Pointer) bool {
    tail := atomic.LoadUint64(&r.hdr.Tail)
    head := atomic.LoadUint64(&r.hdr.Head)
    if tail-head == r.hdr.Capacity {
        return false
    }
    
    offset := (tail & r.hdr.Mask) * r.hdr.ElemSize
    dst := unsafe.Pointer(uintptr(r.data) + uintptr(offset))
    // Use memmove-equivalent via slice copy
    dstSlice := (*[1 << 30]byte)(dst)[:r.hdr.ElemSize:r.hdr.ElemSize]
    srcSlice := (*[1 << 30]byte)(src)[:r.hdr.ElemSize:r.hdr.ElemSize]
    copy(dstSlice, srcSlice)

    atomic.StoreUint64(&r.hdr.Tail, tail+1)
    return true
}

func (r *MmapRing) Read(dst unsafe.Pointer) bool {
    head := atomic.LoadUint64(&r.hdr.Head)
    tail := atomic.LoadUint64(&r.hdr.Tail)
    if head == tail {
        return false
    }
    
    offset := (head & r.hdr.Mask) * r.hdr.ElemSize
    src := unsafe.Pointer(uintptr(r.data) + uintptr(offset))
    srcSlice := (*[1 << 30]byte)(src)[:r.hdr.ElemSize:r.hdr.ElemSize]
    dstSlice := (*[1 << 30]byte)(dst)[:r.hdr.ElemSize:r.hdr.ElemSize]
    copy(dstSlice, srcSlice)

    atomic.StoreUint64(&r.hdr.Head, head+1)
    return true
}

func (r *MmapRing) Close() error {
    size := r.size
    ptr := unsafe.Pointer(r.hdr)
    return syscall.Munmap((*[1 << 30]byte)(ptr)[:size:size])
}
```

---

## 18. Cross-Process Shared Ring Buffer via POSIX Shared Memory

### Complete C Implementation

```c
// shared_ring.h — cross-process SPSC ring buffer
#ifndef SHARED_RING_H
#define SHARED_RING_H

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

#define CACHE_LINE 64

typedef struct {
    // Metadata (read-only after init)
    uint64_t capacity;
    uint64_t mask;
    uint64_t elem_size;
    uint64_t data_offset; // offset from start of this struct to data

    // Producer-owned
    _Atomic uint64_t tail __attribute__((aligned(CACHE_LINE)));
    char _p0[CACHE_LINE - sizeof(uint64_t)];
    
    // Consumer-owned
    _Atomic uint64_t head __attribute__((aligned(CACHE_LINE)));
    char _p1[CACHE_LINE - sizeof(uint64_t)];

    // Data follows immediately after (flexible array member style)
} shared_ring_hdr_t;

typedef struct {
    shared_ring_hdr_t *hdr;
    char              *data; // pointer to data region
    size_t             total_size;
    int                fd;
    char               name[256];
} shared_ring_t;

static inline size_t _shared_ring_total_size(size_t cap, size_t elem_size) {
    return sizeof(shared_ring_hdr_t) + cap * elem_size;
}

// Create a new shared ring buffer
int shared_ring_create(shared_ring_t *ring,
                       const char *name,
                       size_t capacity,
                       size_t elem_size)
{
    // Validate power of 2
    if (!capacity || (capacity & (capacity - 1))) return -1;
    
    size_t total = _shared_ring_total_size(capacity, elem_size);
    
    int fd = shm_open(name, O_CREAT | O_RDWR | O_TRUNC, 0666);
    if (fd < 0) return -1;
    
    if (ftruncate(fd, total) < 0) { close(fd); shm_unlink(name); return -1; }
    
    void *addr = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) { close(fd); shm_unlink(name); return -1; }
    
    shared_ring_hdr_t *hdr = (shared_ring_hdr_t *)addr;
    hdr->capacity    = capacity;
    hdr->mask        = capacity - 1;
    hdr->elem_size   = elem_size;
    hdr->data_offset = sizeof(shared_ring_hdr_t);
    atomic_store_explicit(&hdr->tail, 0, memory_order_relaxed);
    atomic_store_explicit(&hdr->head, 0, memory_order_relaxed);
    
    ring->hdr        = hdr;
    ring->data       = (char *)addr + sizeof(shared_ring_hdr_t);
    ring->total_size = total;
    ring->fd         = fd;
    strncpy(ring->name, name, sizeof(ring->name) - 1);
    return 0;
}

// Open an existing shared ring buffer
int shared_ring_open(shared_ring_t *ring, const char *name) {
    int fd = shm_open(name, O_RDWR, 0666);
    if (fd < 0) return -1;
    
    struct stat st;
    fstat(fd, &st);
    size_t total = (size_t)st.st_size;
    
    void *addr = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) { close(fd); return -1; }
    
    shared_ring_hdr_t *hdr = (shared_ring_hdr_t *)addr;
    ring->hdr        = hdr;
    ring->data       = (char *)addr + sizeof(shared_ring_hdr_t);
    ring->total_size = total;
    ring->fd         = fd;
    strncpy(ring->name, name, sizeof(ring->name) - 1);
    return 0;
}

void shared_ring_close(shared_ring_t *ring) {
    munmap(ring->hdr, ring->total_size);
    close(ring->fd);
}

void shared_ring_unlink(shared_ring_t *ring) {
    shm_unlink(ring->name);
}

static inline bool shared_ring_push(shared_ring_t *ring, const void *elem) {
    shared_ring_hdr_t *h = ring->hdr;
    uint64_t tail = atomic_load_explicit(&h->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&h->head, memory_order_acquire);
    
    if (tail - head == h->capacity) return false;
    
    memcpy(ring->data + (tail & h->mask) * h->elem_size, elem, h->elem_size);
    atomic_store_explicit(&h->tail, tail + 1, memory_order_release);
    return true;
}

static inline bool shared_ring_pop(shared_ring_t *ring, void *elem) {
    shared_ring_hdr_t *h = ring->hdr;
    uint64_t head = atomic_load_explicit(&h->head, memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&h->tail, memory_order_acquire);
    
    if (head == tail) return false;
    
    memcpy(elem, ring->data + (head & h->mask) * h->elem_size, h->elem_size);
    atomic_store_explicit(&h->head, head + 1, memory_order_release);
    return true;
}

#endif // SHARED_RING_H
```

### Producer Process

```c
// producer.c
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include "shared_ring.h"

int main(void) {
    shared_ring_t ring;
    if (shared_ring_create(&ring, "/my_ring", 1024, sizeof(uint64_t)) < 0) {
        perror("shared_ring_create");
        return 1;
    }
    
    for (uint64_t i = 0; i < 10000; i++) {
        while (!shared_ring_push(&ring, &i)) {
            usleep(1); // back off if full
        }
        printf("produced: %llu\n", (unsigned long long)i);
    }
    
    shared_ring_close(&ring);
    // Don't unlink here — consumer needs it
    return 0;
}
// gcc -O2 -o producer producer.c -lrt
```

### Consumer Process

```c
// consumer.c
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include "shared_ring.h"

int main(void) {
    shared_ring_t ring;
    // Wait for producer to create the shared memory
    while (shared_ring_open(&ring, "/my_ring") < 0) {
        usleep(1000);
    }
    
    for (uint64_t expected = 0; expected < 10000; ) {
        uint64_t val;
        if (shared_ring_pop(&ring, &val)) {
            printf("consumed: %llu\n", (unsigned long long)val);
            expected++;
        } else {
            usleep(1);
        }
    }
    
    shared_ring_close(&ring);
    shared_ring_unlink(&ring); // consumer cleans up
    return 0;
}
// gcc -O2 -o consumer consumer.c -lrt
```

---

## 19. Overflow Policies

When a producer tries to push to a full ring buffer, what should happen? This is an architectural decision with significant implications.

### Policy 1: Drop New (Blocking Producer)

Producer spins or sleeps until space is available. Lossless but can cause backpressure cascades.

```c
// Blocking with exponential backoff
uint32_t spin_count = 0;
while (!spsc_ring_push(rb, &item)) {
    if (++spin_count < 1000) {
        __asm__ volatile("pause" ::: "memory"); // x86 PAUSE hint
    } else if (spin_count < 10000) {
        sched_yield();
    } else {
        usleep(1);
        spin_count = 0;
    }
}
```

### Policy 2: Drop Oldest (Overwriting Ring Buffer)

Producer overwrites the oldest element. Used in: logging, telemetry, audio capture.

```c
bool overwrite_push(ring_t *rb, void *elem) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_acquire);
    
    if (tail - head == rb->capacity) {
        // Advance head atomically (drop oldest)
        atomic_store_explicit(&rb->head, head + 1, memory_order_release);
    }
    
    memcpy(rb->data + (tail & rb->mask) * rb->elem_size, elem, rb->elem_size);
    atomic_store_explicit(&rb->tail, tail + 1, memory_order_release);
    return true;
}
// WARNING: In MPSC/MPMC, overwrite_push has race conditions — needs locking
```

### Policy 3: Drop New (Non-Blocking Producer)

Producer gives up immediately. Used in: real-time systems, high-frequency trading.

```c
if (!spsc_ring_push(rb, &item)) {
    drop_counter++;
    // Log drop, emit metric, etc.
}
```

### Policy 4: Resize (Amortized Dynamic)

For non-real-time applications: double the buffer on overflow.

```c
// WARNING: Requires pausing the producer during resize
// Not suitable for lock-free implementations
// Typically requires a lock + memcpy of existing elements
```

---

## 20. Benchmarking & Profiling

### Key Metrics

1. **Throughput**: Operations per second (ops/s)
2. **Latency**: Time from push to pop visible
3. **Tail latency**: P99, P999 (critical for real-time systems)
4. **Cache efficiency**: L1/L2/L3 miss rates

### Benchmarking Template in C

```c
#include <time.h>
#include <stdint.h>

uint64_t ns_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

void benchmark_spsc(size_t n_ops) {
    spsc_ring_t ring;
    spsc_ring_init(&ring, 65536, sizeof(uint64_t));
    
    uint64_t start = ns_now();
    
    for (uint64_t i = 0; i < n_ops; i++) {
        uint64_t val = i;
        while (!spsc_ring_push(&ring, &val));
        uint64_t out;
        while (!spsc_ring_pop(&ring, &out));
    }
    
    uint64_t elapsed = ns_now() - start;
    printf("Throughput: %.2f Mops/s\n", (double)n_ops / elapsed * 1000.0);
    printf("Latency:    %.2f ns/op\n", (double)elapsed / n_ops);
    
    spsc_ring_destroy(&ring);
}
```

### Benchmarking Template in Rust

```rust
// Cargo.toml: [dev-dependencies] criterion = "0.5"

use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_spsc(c: &mut Criterion) {
    c.bench_function("spsc_push_pop", |b| {
        let ring = SpscRing::<u64>::new(65536);
        b.iter(|| {
            ring.push(black_box(42u64)).ok();
            black_box(ring.pop())
        });
    });
}

criterion_group!(benches, bench_spsc);
criterion_main!(benches);
```

### Using perf for Ring Buffer Analysis

```bash
# CPU cycles and cache misses
perf stat -e cycles,instructions,cache-misses,cache-references,L1-dcache-loads,L1-dcache-load-misses ./ring_bench

# False sharing detection
perf c2c record -ag -- ./ring_bench
perf c2c report --stdio

# Flame graph for hotspot identification
perf record -g ./ring_bench
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

# Hardware performance counters: memory bandwidth
perf stat -e mem_uops_retired.all_loads,mem_uops_retired.all_stores ./ring_bench
```

### Throughput Expectations (Modern x86-64, 2024)

| Configuration | Expected Throughput |
|--------------|---------------------|
| SPSC, same core (hyperthreaded) | 200–500 Mops/s |
| SPSC, different cores, same socket | 100–300 Mops/s |
| SPSC, different NUMA nodes | 50–150 Mops/s |
| MPSC (4 producers), same socket | 50–150 Mops/s |
| MPMC (4+4), same socket | 20–80 Mops/s |
| Go buffered channel (SPSC) | 20–50 Mops/s |

---

## 21. Real-World Design Patterns

### Pattern 1: Batched Operations (Amortized Overhead)

Instead of push/pop one-at-a-time, batch multiple operations per atomic update:

```c
// Batch push: claim N slots at once, fill, then publish
bool spsc_ring_push_batch(spsc_ring_t *rb, const void *elems, size_t count) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_acquire);
    
    if (rb->capacity - (tail - head) < count) return false; // not enough space
    
    // Fill all slots
    for (size_t i = 0; i < count; i++) {
        size_t slot = (tail + i) & rb->mask;
        memcpy(rb->data + slot * rb->elem_size,
               (const char *)elems + i * rb->elem_size,
               rb->elem_size);
    }
    
    // Single release publish for entire batch
    atomic_store_explicit(&rb->tail, tail + count, memory_order_release);
    return true;
}
```

**Performance gain**: Reduces atomic operations from N to 2 per batch of N — especially impactful on ARM with expensive barriers.

### Pattern 2: Consumer Batching for Throughput

```c
size_t spsc_ring_pop_batch(spsc_ring_t *rb, void *out, size_t max_count) {
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_acquire);
    
    size_t available = (size_t)(tail - head);
    size_t count = available < max_count ? available : max_count;
    
    if (count == 0) return 0;
    
    // Two-part copy (handle wrap-around)
    size_t head_idx  = head & rb->mask;
    size_t first_cnt = rb->capacity - head_idx;
    
    if (first_cnt >= count) {
        // No wrap-around
        memcpy(out, rb->data + head_idx * rb->elem_size, count * rb->elem_size);
    } else {
        // Wrap-around
        memcpy(out, rb->data + head_idx * rb->elem_size, first_cnt * rb->elem_size);
        memcpy((char *)out + first_cnt * rb->elem_size,
               rb->data, (count - first_cnt) * rb->elem_size);
    }
    
    atomic_store_explicit(&rb->head, head + count, memory_order_release);
    return count;
}
```

### Pattern 3: Zero-Copy with Reservation API

Expose the ring buffer's internal memory directly to avoid copies:

```c
// Producer reserves a slot — returns pointer directly into ring buffer
void *spsc_ring_reserve(spsc_ring_t *rb) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&rb->head, memory_order_acquire);
    
    if (tail - head == rb->capacity) return NULL;
    
    // Return internal pointer; caller writes directly
    return rb->data + (tail & rb->mask) * rb->elem_size;
}

// Producer commits after writing
void spsc_ring_commit(spsc_ring_t *rb) {
    uint64_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    atomic_store_explicit(&rb->tail, tail + 1, memory_order_release);
}

// Usage (zero-copy):
struct MyEvent *evt = spsc_ring_reserve(&ring);
if (evt) {
    evt->type = TYPE_NETWORK;
    evt->timestamp = get_timestamp();
    memcpy(evt->payload, packet_data, packet_len); // only one copy, from network
    spsc_ring_commit(&ring);
}
```

### Pattern 4: Work Stealing Queue (Chase-Lev Deque)

For work-stealing thread pools, you need a deque (double-ended queue) where:
- The owner thread pushes and pops from the bottom (LIFO — better cache locality)
- Thieves steal from the top (FIFO)

```c
// Based on "Dynamic Circular Work-Stealing Deque" (Chase & Lev, 2005)
typedef struct {
    _Atomic int64_t  top;    // thieves pop here
    char _p0[CACHE_LINE - 8];
    _Atomic int64_t  bottom; // owner pushes/pops here
    char _p1[CACHE_LINE - 8];
    _Atomic uintptr_t array; // pointer to current array
} work_stealing_queue_t;

// Owner push (bottom)
void wsq_push(work_stealing_queue_t *q, task_t *task) {
    int64_t b = atomic_load_explicit(&q->bottom, memory_order_relaxed);
    array_t *a = (array_t *)atomic_load_explicit(&q->array, memory_order_relaxed);
    
    if (b - atomic_load_explicit(&q->top, memory_order_acquire) > a->size - 1) {
        a = grow_array(a, b, atomic_load_explicit(&q->top, memory_order_relaxed));
        atomic_store_explicit(&q->array, (uintptr_t)a, memory_order_relaxed);
    }
    
    a->items[b & a->mask] = task;
    atomic_thread_fence(memory_order_release);
    atomic_store_explicit(&q->bottom, b + 1, memory_order_relaxed);
}

// Owner pop (bottom — LIFO)
task_t *wsq_pop(work_stealing_queue_t *q) {
    int64_t b = atomic_load_explicit(&q->bottom, memory_order_relaxed) - 1;
    array_t *a = (array_t *)atomic_load_explicit(&q->array, memory_order_relaxed);
    atomic_store_explicit(&q->bottom, b, memory_order_relaxed);
    atomic_thread_fence(memory_order_seq_cst); // full barrier needed here
    
    int64_t t = atomic_load_explicit(&q->top, memory_order_relaxed);
    if (t <= b) {
        task_t *task = a->items[b & a->mask];
        if (t == b) {
            // Last element — race with thieves
            if (!atomic_compare_exchange_strong_explicit(
                    &q->top, &t, t + 1, memory_order_seq_cst, memory_order_relaxed)) {
                task = NULL; // thief won
            }
            atomic_store_explicit(&q->bottom, b + 1, memory_order_relaxed);
        }
        return task;
    }
    atomic_store_explicit(&q->bottom, b + 1, memory_order_relaxed);
    return NULL;
}
```

---

## 22. Common Pitfalls & Subtle Bugs

### Pitfall 1: Non-Power-of-Two Capacity with Mask Optimization

```c
// BUG: capacity = 100, mask = 99
// 100 % 99 = 1, but 100 & 99 = 4 (WRONG)
//
// Only safe when capacity is power of 2:
// 128 & 127 = 0 ✓, 256 & 255 = 0 ✓
```

Always `assert((capacity & (capacity - 1)) == 0)` at init.

### Pitfall 2: Signed vs Unsigned Counter Subtraction

```c
// BUG: If head and tail are int32_t
int32_t tail = INT32_MAX;
int32_t head = INT32_MIN;
int32_t count = tail - head; // UNDEFINED BEHAVIOR (signed overflow)

// CORRECT: Use unsigned types — wrapping is well-defined
uint64_t count = tail - head; // always correct
```

### Pitfall 3: Missing Release After Data Write

```c
// BUG: No barrier between data write and tail increment
rb->data[tail & mask] = value;   // store
rb->tail = tail + 1;              // store — may be reordered BEFORE data write on ARM
                                   // Consumer reads tail, sees new value, reads stale data

// CORRECT:
rb->data[tail & mask] = value;
atomic_store_explicit(&rb->tail, tail + 1, memory_order_release); // barrier
```

### Pitfall 4: Double-Checked Locking Without Barriers

```c
// BUG in MPMC: CAS succeeds, then writing data without proper ordering
uint64_t pos;
atomic_compare_exchange_weak(&rb->tail, &pos, pos+1); // CAS
rb->data[pos & mask] = value; // BUG: other threads may see tail+1 but empty slot
// Must use per-slot sequence numbers to signal readiness

// CORRECT: Use sequence numbers (see Section 8)
```

### Pitfall 5: Capacity vs Available Space Off-By-One

```c
// BUG: Using >= instead of ==
if (tail - head >= capacity) return false; // WRONG: >= means checking for overflow

// CORRECT:
if (tail - head == capacity) return false; // full
```

### Pitfall 6: False Sharing After Adding Fields

Adding a field to the ring buffer struct can silently cause false sharing:

```c
// Before (correct):
struct { uint64_t tail [pad56]; uint64_t head [pad56]; }

// After adding statistics (BROKEN):
struct {
    uint64_t tail;
    uint64_t drop_count;  // NEW: now shares cache line with tail!
    [pad48];
    uint64_t head;
    [pad56];
}
```

Always re-verify alignment with `offsetof()` checks after struct changes:

```c
_Static_assert(offsetof(spsc_ring_t, head) % CACHE_LINE_SIZE == 0,
               "head must be cache-line aligned");
_Static_assert(offsetof(spsc_ring_t, tail) % CACHE_LINE_SIZE == 0,
               "tail must be cache-line aligned");
```

### Pitfall 7: Lazy Consumer Creates Backpressure Cascade

A slow consumer fills the ring buffer. Producer blocks (or drops). Producer's buffer fills. Network drops. This cascade can bring down a system. Always monitor `drop_count` and `utilization` metrics.

### Pitfall 8: mmap Shared Ring with Pointers

```c
// BUG: Storing a pointer in the shared ring
struct Event {
    char *message; // WRONG: pointer valid only in this process's address space
};

// CORRECT: Store data inline or use offsets
struct Event {
    char message[256]; // inline data
    // OR: uint64_t offset; // offset into another shared region
};
```

---

## 23. Mental Models for Mastery

### The Fundamental Principle: Ownership Transfer

A ring buffer is, at its core, a **protocol of exclusive ownership transfer**:

1. Producer **owns** a slot when: `tail <= slot_index < tail + free_space`
2. After `release(tail)`: slot ownership transfers to consumer
3. Consumer **owns** a slot when: `head <= slot_index < tail`
4. After `release(head)`: slot ownership returns to producer

This ownership model is the same principle Rust's borrow checker enforces at compile time. When you internalize this, lock-free correctness becomes intuitive rather than magic.

### The "Happens-Before" Graph Mental Model

For any lock-free data structure, draw the happens-before graph:

```
Producer thread:              Consumer thread:
  write(data)                    read(data)
      |                               |
      ↓ (sequenced-before)            ↑ (sequenced-before)
  release(tail) ─────────────→ acquire(tail)
                (happens-before edge)

Result: write(data) happens-before read(data) ✓
```

Any data race is equivalent to a missing edge in this graph.

### Chunking for Pattern Recognition

Expert programmers **chunk** ring buffer operations into three mental units:

1. **Claim**: Atomically reserve a slot (CAS on counter)
2. **Execute**: Write/read the slot data (relaxed, no barrier)
3. **Publish**: Signal completion (release store on sequence/counter)

Once you internalize this three-step pattern, you can analyze any ring buffer variant in seconds.

### The Contention Spectrum

```
SPSC ←————————————————————————→ MPMC
Low contention                High contention
Max throughput                Lower throughput
Simplest code                 Most complex code
No CAS needed                 CAS on every operation

Choose the leftmost option that satisfies your requirements.
```

### Cache Architecture Mental Model

Always think in terms of **cache line ownership**:

```
Core 0 modifies tail → becomes "owner" of that cache line
Core 1 reads tail    → triggers RFO from Core 0
Core 0 sends cache line → ~100-300 ns

Lesson: Every cross-core synchronization costs ~100-300 ns.
Design to minimize cross-core accesses.
```

**The caching optimization**: `head_cache` and `tail_cache` work because in a steady-state ring buffer, the buffer is rarely truly full or empty. The producer almost never needs to read head (and vice versa). Caching the last-seen value exploits this temporal locality.

### Deliberate Practice Framework for Ring Buffers

To reach the top 1%, practice these progressive exercises:

**Level 1**: Implement SPSC in C from scratch. Verify with TSAN (ThreadSanitizer).

**Level 2**: Add the head/tail cache optimization. Benchmark before/after.

**Level 3**: Implement MPSC with `fetch_add` and sequence numbers.

**Level 4**: Implement MPMC with the Dmitry Vyukov algorithm. Run on ARM.

**Level 5**: Implement cross-process SPSC via mmap. Test across NUMA nodes.

**Level 6**: Implement the magic mirroring trick. Benchmark zero-copy vs copy path.

**Level 7**: Read `io_uring`'s source code (`io_uring/io_uring.c`). Map each design choice to a principle in this guide.

**Level 8**: Implement a custom ring buffer for a real workload (network capture, logging, metrics). Profile with `perf c2c`. Eliminate all false sharing.

---

## Summary: The Expert's Checklist

When designing a ring buffer for production:

- [ ] **Capacity**: Power of two, enforced at initialization
- [ ] **Counters**: Monotonically increasing `uint64_t`, never reset
- [ ] **Indexing**: `counter & mask` (not `counter % capacity`)
- [ ] **Alignment**: Producer's `tail` and consumer's `head` on separate cache lines
- [ ] **Barriers**: `release` on publish, `acquire` on observe — nothing stronger unless needed
- [ ] **Counter caching**: Cache the remote counter to avoid atomic loads on every operation
- [ ] **Variant**: Use SPSC unless you need MPSC/MPMC — choose the weakest synchronization that works
- [ ] **Overflow policy**: Explicit and documented (drop new, drop old, block, resize)
- [ ] **Verification**: Run with ThreadSanitizer and MemorySanitizer on both x86 and ARM
- [ ] **Profiling**: Use `perf c2c` to verify no false sharing in production workloads
- [ ] **Shared memory**: No pointers in the shared struct; validate all offsets

---

*This guide reflects design principles found in Linux kernel source (`kfifo.c`, `io_uring/io_uring.c`, `kernel/events/ring_buffer.c`), the LMAX Disruptor, Dmitry Vyukov's lock-free algorithms, and the C11/C++11 memory model specification.*

Now let me write the comprehensive guide as a markdown file:Here is your complete guide — **23 chapters**, covering every layer of the ring buffer from first principles to Linux kernel internals.

Here is a map of what each section delivers:

**Foundations (1–4)**: The conceptual model, monotonic counters vs index-based (and why monotonic always wins), full/empty disambiguation strategies, and the power-of-two bitwise mask trick that eliminates division entirely.

**Hardware-Level Thinking (5–6)**: Cache line alignment and false sharing — the silent killer of performant ring buffers — explained via the MESI protocol. Then a rigorous treatment of memory ordering: the C11 acquire/release model, how it maps to actual x86 vs ARM instructions, and the Linux kernel's `smp_store_release`/`smp_load_acquire` API.

**Concurrency Variants (7–8)**: SPSC → MPSC → MPMC with precise reasoning for when each is appropriate. Lock-free design via per-slot sequence numbers, the ABA problem (and why monotonic counters make it impossible), and `fetch_add` vs CAS trade-offs.

**Linux-Specific Architecture (9–14)**: mmap-based shared memory, the **magic mirroring trick** (virtual address doubling for zero wrap-around copies), `kfifo`, and deep dives into `io_uring` (the SQ/CQ dual-ring design, SQPOLL mode, zero-syscall I/O), the `perf` ring buffer with its seqlock, and `bpf_ringbuf`.

**Complete Implementations (15–18)**: Production-quality code in C11, Rust (safe SPSC + MPMC with sequence numbers), and Go (manual lock-free + mmap cross-process), all with correct memory ordering.

**Design Mastery (19–23)**: Overflow policies, benchmarking methodology with `perf c2c`, batching patterns, zero-copy reservation APIs, work-stealing deques, and 8 pitfalls that fail silently even on correct-looking code.