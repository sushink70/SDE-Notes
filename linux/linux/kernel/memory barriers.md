# Memory Barriers: A Complete, In-Depth Guide
## For Systems Programmers — C, Go, Rust, and Linux Kernel

---

> *"The CPU is lying to you. Memory barriers are how you catch it in the act."*

---

## Table of Contents

1. [The Fundamental Problem](#1-the-fundamental-problem)
2. [CPU Microarchitecture Deep Dive](#2-cpu-microarchitecture-deep-dive)
3. [The Memory Hierarchy and Coherency](#3-the-memory-hierarchy-and-coherency)
4. [Memory Ordering Models](#4-memory-ordering-models)
5. [Types of Memory Barriers](#5-types-of-memory-barriers)
6. [x86-64 Architecture Specifics](#6-x86-64-architecture-specifics)
7. [ARM Architecture Specifics](#7-arm-architecture-specifics)
8. [RISC-V Memory Model](#8-risc-v-memory-model)
9. [Linux Kernel Memory Barriers](#9-linux-kernel-memory-barriers)
10. [C11 Atomics and Memory Order](#10-c11-atomics-and-memory-order)
11. [Go Memory Model](#11-go-memory-model)
12. [Rust Memory Model and Atomics](#12-rust-memory-model-and-atomics)
13. [Classic Synchronization Patterns](#13-classic-synchronization-patterns)
14. [Lock-Free Data Structures](#14-lock-free-data-structures)
15. [The ABA Problem](#15-the-aba-problem)
16. [Memory Reclamation Patterns](#16-memory-reclamation-patterns)
17. [Real-World Linux Kernel Examples](#17-real-world-linux-kernel-examples)
18. [Compiler Barriers vs Hardware Barriers](#18-compiler-barriers-vs-hardware-barriers)
19. [Performance Analysis and Costs](#19-performance-analysis-and-costs)
20. [Common Bugs and Debugging](#20-common-bugs-and-debugging)
21. [Mental Models for Experts](#21-mental-models-for-experts)

---

## 1. The Fundamental Problem

### Why Memory Ordering Exists

In a sequential, single-threaded, single-core world, the intuitive model of memory holds perfectly:

```
write(x, 1)   // x is now 1
read(x)       // returns 1
```

This breaks catastrophically in the real world due to three independent sources of reordering:

1. **The Compiler** — may reorder, eliminate, or hoist memory operations for optimization.
2. **The CPU out-of-order execution engine** — executes instructions in a different order than written.
3. **The memory subsystem** — store buffers, invalidation queues, cache coherency protocols all introduce temporal gaps between a "write" and when that write becomes globally visible.

### The Canonical Example: Message Passing

Imagine two threads on two different CPU cores:

```
Thread 1 (Producer)      Thread 2 (Consumer)
─────────────────────    ─────────────────────
data  = 42;              while (!ready) {}
ready = true;            assert(data == 42);  // CAN FAIL
```

Without barriers, the assertion can fail. Not because of a race in the traditional sense — Thread 2 does wait for `ready`. It fails because:

- **Thread 1** may have its store to `data` reordered after its store to `ready` (either by compiler or CPU).
- **Thread 2** may observe `ready == true` before it observes `data == 42`, because they are in different cache lines and the coherency protocol delivered them in a different order.

This is not a hypothetical. On ARM, POWER, and RISC-V architectures, this exact failure occurs without memory barriers. On x86, the TSO model prevents this specific case, but many others remain.

### What a Memory Barrier Actually Does

A memory barrier is an instruction — or a compiler directive — that constrains the observable ordering of memory operations. It is a **promise** from the hardware that operations before the barrier are globally visible before operations after the barrier begin (for the relevant direction: load/store, or both).

Barriers operate in at least two dimensions:
- **Direction**: Load-Load, Load-Store, Store-Load, Store-Store (explained in Section 5)
- **Scope**: Compiler-only (no instruction emitted) vs. hardware (actual fence instruction)

---

## 2. CPU Microarchitecture Deep Dive

### Out-of-Order Execution (OOO)

Modern CPUs execute instructions out of order to maximize throughput. The pipeline stages:

```
Fetch → Decode → Rename/Dispatch → Issue/Schedule → Execute → Reorder Buffer → Commit
                                                                    ^
                                                           Results buffered here
                                                           until retirement
```

The **Reorder Buffer (ROB)** holds completed-but-not-yet-committed instructions. The CPU commits them in program order, but executes them speculatively and out-of-order.

**Key insight:** A load that misses in L1 cache takes ~100 cycles. The CPU cannot stall everything — it issues later independent instructions immediately. From the perspective of another core, those later stores become visible before the earlier load completes. This creates apparent load-store reordering.

### Store Buffers

Every CPU core has a **store buffer** (also called a store queue) — a small FIFO buffer that sits between the execution engine and the L1 cache.

```
CPU Core
┌──────────────────────────────────────┐
│  Execute Unit                        │
│       │                              │
│       ▼                              │
│  Store Buffer  [W:addr1=val1]        │
│                [W:addr2=val2]        │
│                [W:addr3=val3]        │
│       │                              │
│       ▼                              │
│  L1 Cache ──────────────────────────┼── Cache Coherency Bus
└──────────────────────────────────────┘
```

When a CPU executes a store:
1. The value is placed in the store buffer immediately — the store "completes" from the CPU's perspective.
2. The value drains from the store buffer to L1 cache asynchronously, in the background.
3. **Other cores cannot see the value until it drains to L1 and the coherency protocol propagates it.**

**Critical implication**: A CPU reading its own store buffer will see its own recent writes (store-to-load forwarding). Other cores will not, until the buffer drains. This is the root cause of **store-load reordering** from other cores' perspectives.

### Load Buffers and Speculative Loads

CPUs also speculatively issue loads ahead of time. A load may be issued before preceding stores commit, before preceding branches resolve, or before preceding loads complete.

If a load is issued speculatively and another core subsequently invalidates that cache line before the load's result is consumed, the CPU must **squash** the speculative load and re-execute it (a "memory ordering machine clear"). This is invisible to the programmer but impacts performance.

### Invalidation Queues (ARM, POWER)

On some architectures (notably ARM and POWER but **not x86**), the cache coherency protocol uses **invalidation queues**:

```
Core A sends:  INVALIDATE line X
Core B receives: [queues the invalidation, sends ACK immediately]
Core B later:  [processes the invalidation, marks line X invalid]
```

The ACK is sent before the invalidation is processed. This means Core B can read a stale value from cache line X even after Core A believes Core B has acknowledged the invalidation. This is the source of **load-load reordering** on weakly-ordered architectures.

An **`isb`** (instruction synchronization barrier) or **`dmb`** (data memory barrier) on ARM forces the invalidation queue to drain before allowing subsequent loads.

### Cache Coherency Protocols: MESI and Variants

Most modern systems use a variant of the **MESI protocol**:

| State | Meaning |
|-------|---------|
| **M**odified | Line is dirty; only this cache has it |
| **E**xclusive | Line is clean; only this cache has it |
| **S**hared | Line is clean; multiple caches may have it |
| **I**nvalid | Line is not present or stale |

**Write propagation flow:**
1. Core A wants to write to address X (currently Shared).
2. Core A sends a **RFO (Request For Ownership)** on the bus.
3. All other cores holding X in S state receive an invalidation message.
4. They queue the invalidation and ACK.
5. Core A transitions X to Modified state and writes.
6. Eventually the invalidations are processed by other cores.

The gap between step 4 (ACK) and step 6 (actual invalidation processed) is where weak memory models permit additional reordering. x86 avoids this by processing invalidations immediately (no invalidation queue).

**MESIF** (Intel) adds **F**orward state — one Shared copy designated to respond to snoops, reducing bus traffic.  
**MOESI** (AMD) adds **O**wned state — allows dirty sharing without writeback to main memory.

---

## 3. The Memory Hierarchy and Coherency

### Cache Line Granularity

The unit of coherency is a **cache line** — typically 64 bytes on modern x86/ARM, 128 bytes on POWER.

```
Address layout:
┌──────────────────┬───────────────┬──────────┐
│   Tag bits       │   Index bits  │  Offset  │
│   (which line)   │  (which set)  │ (6 bits) │
└──────────────────┴───────────────┴──────────┘
                                      └── 64 bytes = 2^6
```

**False sharing**: Two independent variables in the same cache line cause coherency traffic even though they are logically unrelated. A write to one invalidates the entire line in all other caches. This is a performance killer, not a correctness issue.

```c
// False sharing — x and y are in the same cache line
struct Counter {
    int64_t x;  // Thread 1 writes
    int64_t y;  // Thread 2 writes
};

// Fix: pad to cache line boundary
struct Counter {
    int64_t x;
    char pad[56];  // 64 - 8 = 56 bytes
    int64_t y;
};
```

### Memory-Mapped I/O (MMIO)

Device registers accessed via MMIO have special requirements. A CPU may coalesce multiple writes to the same address (write combining), reorder MMIO writes with respect to each other, or cache MMIO reads from a write buffer rather than the device.

Linux marks MMIO regions as **uncacheable** or **write-combining** via page table attributes. Explicit barriers (`mb()`, `wmb()`, `rmb()`) are required around MMIO operations even on x86, because the hardware does not guarantee ordering between MMIO and DMA operations.

---

## 4. Memory Ordering Models

### Total Store Order (TSO) — x86

x86 implements **TSO**, which provides strong ordering guarantees:

**What TSO guarantees:**
- Load-Load: Loads are not reordered with respect to each other ✓
- Store-Store: Stores are not reordered with respect to each other ✓
- Load-Store: A load is never reordered after a later store ✓

**What TSO does NOT guarantee:**
- Store-Load: A store may appear reordered after a later load ✗ (because stores go to the store buffer; loads can bypass them)

This means on x86, the only barrier you typically need is `MFENCE` (or `LOCK XCHG`) to prevent store-load reordering. All other barriers are either free (no-op hardware-wise) or handled by the architecture.

**The x86 programmer's false sense of security**: Many bugs are invisible on x86 because of TSO, then manifest when ported to ARM or POWER. Always write code that is correct on weakly-ordered architectures.

### Release-Acquire (Most Architectures)

The **Release-Acquire** (RA) model, used by most modern ISAs (ARM64, RISC-V, POWER), provides:

- **Acquire load**: No loads or stores after this load may be reordered before it. (Prevents load-load and load-store reordering after the acquire.)
- **Release store**: No loads or stores before this store may be reordered after it. (Prevents load-store and store-store reordering before the release.)

Together, acquire and release create a **happens-before** relationship: everything before the release store is visible to anyone who observes the acquire load returning the released value.

```
Thread 1                     Thread 2
────────────────────         ──────────────────────
data = 42;                   while (!ready.load(Acquire)) {}
ready.store(1, Release);     // All stores before Release are
                             // visible here after Acquire
                             assert(data == 42); // SAFE
```

### Sequential Consistency (SC)

The strongest model — all threads observe memory operations in the same total order, consistent with program order. This is the programmer's intuitive model.

**Cost**: Every sequentially consistent operation requires a full fence on most architectures. SC is often 5-10x slower than Release-Acquire for the same task.

The C11/C++11 default for `atomic<T>` operations is sequentially consistent. This is often unnecessarily strong. An expert uses the weakest ordering that maintains correctness.

### Relaxed Ordering

The weakest ordering — no ordering constraints whatsoever. Only guarantees atomicity of the individual operation. Used for statistics counters, flags where only the value matters not the ordering.

```c
// Relaxed is correct here — we only care about the count,
// not about ordering with respect to other operations
atomic_fetch_add_explicit(&stats.request_count, 1, memory_order_relaxed);
```

---

## 5. Types of Memory Barriers

### Load-Load Barrier (Read Barrier, `smp_rmb()`)

Ensures that all loads before the barrier complete before any loads after the barrier.

```
[load A]
[load B]    ← rmb() ensures A is globally visible before B is issued
rmb()
[load C]
[load D]
```

**When needed**: When you load a pointer, then dereference it. The pointer load and the dereference must not be reordered.

```c
ptr = atomic_load(&global_ptr);
smp_rmb();   // Ensure we see the object ptr points to
data = ptr->value;
```

### Store-Store Barrier (Write Barrier, `smp_wmb()`)

Ensures all stores before the barrier complete (drain to cache) before any stores after the barrier.

```
[store A]
[store B]    ← wmb() ensures A,B are visible before C,D
wmb()
[store C]
[store D]
```

**When needed**: When you write data, then write a flag indicating the data is ready.

```c
buffer[i] = data;     // Write data first
smp_wmb();            // Ensure data write precedes flag write
flag = 1;             // Signal consumer
```

### Load-Store Barrier

Ensures loads before the barrier are not reordered after stores following the barrier. This ordering is typically preserved by most architectures except in very weak models (like IBM POWER in certain configurations).

### Store-Load Barrier (Full Barrier, the expensive one)

Ensures all stores before the barrier are visible to all processors before any loads after the barrier are issued. This is the most expensive barrier.

```c
store(x, 1);
full_barrier(); // MFENCE on x86, DSB+ISB on ARM, SYNC on POWER
load(y);
```

**On x86**: This is `MFENCE`. All other barriers are compiler-only no-ops.  
**On ARM**: This is `DMB ISH` (inner shareable domain).  
**On POWER**: This is `SYNC` (heavyweight) or `LWSYNC` (lightweight, excludes store-load).

### Acquire Barrier

A **one-way** barrier that prevents hoisting of subsequent operations above this point. Equivalent to a load-load + load-store barrier.

Think of it as: "acquire the lock — no one can enter the critical section before I hold the lock."

```
acquire()
───── nothing moves UP through this line ─────
[read/write protected data]
```

### Release Barrier

A **one-way** barrier that prevents sinking of preceding operations below this point. Equivalent to a store-store + load-store barrier.

Think of it as: "release the lock — no one can see I released before my writes are visible."

```
[read/write protected data]
───── nothing moves DOWN through this line ─────
release()
```

**Acquire and Release are half-fences.** Together, they are cheaper than a full barrier because:
- A full barrier blocks both directions.
- Acquire only blocks forward (subsequent operations can't move up).
- Release only blocks backward (preceding operations can't move down).

### Sequentially Consistent Barrier

Combines acquire + release + a global ordering constraint. All SC operations across all threads form a single total order agreed upon by all cores.

---

## 6. x86-64 Architecture Specifics

### x86 Fence Instructions

| Instruction | Effect |
|-------------|--------|
| `LFENCE` | Load fence: serializes loads — no load after LFENCE executes before all loads before it complete. Also prevents speculative execution past it. |
| `SFENCE` | Store fence: serializes stores — all stores before SFENCE become globally visible before any store after it. |
| `MFENCE` | Full fence: combines LFENCE + SFENCE. Also ensures store-load ordering. The most expensive. |
| `LOCK` prefix | Implies full memory barrier. `LOCK CMPXCHG`, `LOCK XADD`, etc. |
| `XCHG` | Implies `LOCK` even without prefix. Often used for acquire-release semantics. |

### x86 Implicit Barriers

On x86, **most barriers are free** because TSO handles them:

```asm
; Store-store: implicit, TSO prevents reordering
MOV [addr1], rax
MOV [addr2], rbx   ; guaranteed to appear after first store

; Load-load: implicit, TSO prevents reordering
MOV rax, [addr1]
MOV rbx, [addr2]   ; guaranteed to appear after first load

; Load-store: implicit
MOV rax, [addr1]
MOV [addr2], rbx   ; never reordered before the load

; Store-load: NOT implicit — the only case requiring MFENCE
MOV [addr1], rax
MFENCE             ; required to prevent store-load reordering
MOV rbx, [addr2]
```

### x86 and LFENCE for Speculation Control

After the Spectre vulnerability class was discovered, `LFENCE` gained new importance. It is a **speculation barrier** — the CPU will not speculatively execute instructions past an LFENCE. Used in mitigations:

```asm
; Spectre gadget mitigation
array_index &= mask     ; bounds check
LFENCE                  ; prevent speculative execution past check
load array[array_index] ; now safe from speculative out-of-bounds access
```

### x86 Memory Types and PAT

x86 supports multiple memory types via the **Page Attribute Table (PAT)**:

| Type | WC | WT | WB | UC- | UC |
|------|----|----|----|-----|-----|
| Write Combining | ✓ | | | | |
| Write Through | | ✓ | | | |
| Write Back (normal) | | | ✓ | | |
| UC- (MTRR override) | | | | ✓ | |
| Uncacheable | | | | | ✓ |

Write-combining memory: stores are buffered and combined before being sent to memory/device. Useful for framebuffers. Requires `SFENCE` to flush the write-combine buffer.

---

## 7. ARM Architecture Specifics

### ARM is Weakly Ordered

ARM's memory model (ARMv8-A and later) is significantly weaker than x86. It allows:
- Load-load reordering
- Load-store reordering  
- Store-store reordering
- Store-load reordering

This means virtually every shared-memory pattern requires explicit barriers.

### ARM Barrier Instructions

#### DMB — Data Memory Barrier

```
DMB <option>
```

Options (sharing domain × access type):

| Option | Meaning |
|--------|---------|
| `ISH` | Inner Shareable domain, all accesses (most common for SMP) |
| `ISHST` | Inner Shareable domain, store-store only |
| `ISHLD` | Inner Shareable domain, load-load + load-store |
| `OSH` | Outer Shareable domain (across clusters) |
| `SY` | Full system, all accesses |
| `ST` | Full system, store-store only |
| `LD` | Full system, load-load + load-store |

`DMB ISH` is the standard full barrier for SMP Linux on ARM. `DMB ISHST` is a store-store barrier (cheaper).

#### DSB — Data Synchronization Barrier

Stronger than DMB. Ensures not just ordering, but **completion** of all outstanding cache operations, TLB maintenance, branch predictor maintenance, etc. Required after cache/TLB maintenance operations before they take effect.

```asm
DC IVAC, x0    ; invalidate cache by VA
DSB ISH        ; wait for invalidation to complete
```

#### ISB — Instruction Synchronization Barrier

Flushes the CPU pipeline and forces refetch from cache/memory. Required after modifying page tables, changing system registers (SCTLR, TTBR), or modifying executable code (JIT compilation, self-modifying code).

```asm
; After installing new page table entry:
STR x1, [x0]   ; write PTE
DSB ISH         ; ensure write completes
ISB             ; flush pipeline so new PTE takes effect
```

### ARM Load-Acquire and Store-Release (ARMv8)

ARMv8 introduced native acquire/release instructions:

```asm
LDAR x0, [x1]      ; Load-Acquire Register
STLR x0, [x1]      ; Store-Release Register
LDAPR x0, [x1]     ; Load-Acquire RCpc (weaker, cheaper)
```

`LDAR` is a full acquire barrier: all loads and stores after it are ordered after it.
`STLR` is a full release barrier: all loads and stores before it are ordered before it.

These are cheaper than explicit DMBs because they only constrain one point rather than all outstanding operations.

**Exclusive variants** for atomic RMW:
```asm
LDAXR x0, [x1]    ; Load-Acquire Exclusive
STLXR w2, x0, [x1] ; Store-Release Exclusive (w2 = 0 on success)
```

---

## 8. RISC-V Memory Model

RISC-V uses **RVWMO** (RISC-V Weak Memory Ordering), a carefully defined formal model.

### FENCE Instruction

```
FENCE [pred], [succ]
```

Where `pred` and `succ` are combinations of:
- `i` — instruction fetch
- `r` — read (load)
- `w` — write (store)
- `o` — output (device)

Examples:
```asm
FENCE rw, rw    ; Full barrier — all loads/stores before, all loads/stores after
FENCE w, w      ; Store-store barrier
FENCE r, r      ; Load-load barrier
FENCE r, rw     ; Acquire barrier (load-load + load-store)
FENCE rw, w     ; Release barrier (load-store + store-store)
FENCE.TSO       ; Implies TSO semantics for the enclosing region
```

### RISC-V Atomic Instructions with Ordering

```asm
LR.W.AQ    t0, (a0)     ; Load Reserved, Acquire
SC.W.RL    t1, t2, (a0) ; Store Conditional, Release
AMOADD.W.AQR t0, t1, (a0) ; AMO with both Acquire and Release
```

The `.AQ` and `.RL` suffixes embed ordering directly in atomic instructions, avoiding separate FENCE instructions.

---

## 9. Linux Kernel Memory Barriers

### Core Barrier API

The Linux kernel abstracts hardware barriers behind a portable API in `<asm/barrier.h>` and `<linux/compiler.h>`:

```c
// Full barriers
mb()     // Full memory barrier (loads + stores in both directions)
smp_mb() // SMP-safe full barrier (no-op on UP, full barrier on SMP)

// Store barriers
wmb()     // Write memory barrier (store-store ordering)
smp_wmb() // SMP write barrier

// Load barriers
rmb()     // Read memory barrier (load-load ordering)
smp_rmb() // SMP read barrier

// Acquire/Release
smp_load_acquire(p)     // Atomic load with acquire semantics
smp_store_release(p, v) // Atomic store with release semantics

// Compiler-only (no hardware instruction)
barrier()              // Compiler barrier — prevents compiler reordering
```

### Why `smp_mb()` vs `mb()`?

- `mb()` emits a hardware barrier unconditionally (including on uniprocessor systems). Required for MMIO because even on UP, the hardware bus ordering matters.
- `smp_mb()` emits a hardware barrier only on SMP configurations. On UP builds, it compiles to just `barrier()` (compiler fence only), because a single CPU's execution is inherently ordered.

**Rule**: Use `smp_*` barriers for CPU-to-CPU synchronization. Use `mb()`/`rmb()`/`wmb()` for MMIO/DMA synchronization.

### DMA Barriers

When a CPU hands data to a DMA engine:

```c
// CPU writes data
buffer[0] = 0xDEADBEEF;
buffer[1] = 0xCAFEBABE;

// Ensure writes are visible to DMA hardware before programming the DMA engine
dma_wmb();  // write barrier between CPU writes and DMA descriptor writes

// Program DMA engine (MMIO writes)
dma->src  = phys_addr;
dma->len  = len;
dma->ctrl = DMA_START;
```

`dma_wmb()` maps to `wmb()` on most architectures but may be weaker on architectures where DMA hardware is in the inner-shareable domain and doesn't require full system barriers.

### Linux Kernel: Read-Copy-Update (RCU)

RCU is the most sophisticated use of memory barriers in the kernel. It allows lock-free reads of data structures that may be concurrently updated.

**Core RCU guarantee**: Readers see either the old or new version of data, never a torn/partial update.

**Key primitives:**

```c
// Reader side
rcu_read_lock();          // Disables preemption (SRCU: takes read lock)
p = rcu_dereference(ptr); // Load pointer with consume semantics
use(p->data);
rcu_read_unlock();

// Writer side
new_node = kmalloc(sizeof(*new_node), GFP_KERNEL);
new_node->data = new_data;
old_node = ptr;
rcu_assign_pointer(ptr, new_node);  // Store with release semantics
synchronize_rcu();                   // Wait for all readers to finish
kfree(old_node);                    // Safe to free old node now
```

**`rcu_dereference()`** uses `READ_ONCE()` with a **data dependency barrier** on DEC Alpha (the only architecture where data dependencies don't imply ordering). On all other architectures, a causal data dependency (reading a pointer then dereferencing it) prevents load reordering, so no hardware barrier is needed.

**`rcu_assign_pointer()`** uses `smp_store_release()` — ensures all writes to the new object are visible before the pointer itself is made visible.

### WRITE_ONCE and READ_ONCE

```c
// Prevents compiler from:
// - Tearing the access into multiple operations
// - Merging/eliminating the access
// - Speculating the value
WRITE_ONCE(x, val);  // Volatile store of the correct size
val = READ_ONCE(x);  // Volatile load of the correct size

// Implementation (simplified):
#define READ_ONCE(x) (*(volatile typeof(x) *)&(x))
#define WRITE_ONCE(x, val) (*(volatile typeof(x) *)&(x) = (val))
```

**Why is this necessary?** Without `volatile`, the compiler may:
- Load `x` once and use the cached register value in a loop, missing updates from other CPUs.
- Tear a 64-bit access into two 32-bit accesses on a 32-bit CPU.
- Assume `x` cannot change between two reads and optimize away the second read.

`READ_ONCE`/`WRITE_ONCE` do **not** emit hardware barriers. They only prevent compiler optimizations. Use them together with appropriate `smp_*` barriers.

### Kernel Locking and Implied Barriers

All kernel locking primitives imply barriers:

```c
spin_lock(lock)   // Implies acquire barrier — nothing from inside the CS
                  // moves before the lock acquisition
spin_unlock(lock) // Implies release barrier — nothing from inside the CS
                  // moves after the unlock

mutex_lock(m)     // Implies acquire
mutex_unlock(m)   // Implies release
```

**This means: if you hold a spinlock, you don't need additional barriers for operations protected by that lock.** The lock itself provides the necessary ordering.

### Kernel Atomic Operations

```c
// Relaxed (no barrier implied)
atomic_read(v)         // READ_ONCE
atomic_set(v, i)       // WRITE_ONCE

// With barrier
atomic_read_acquire(v)    // Load with acquire semantics
atomic_set_release(v, i)  // Store with release semantics

// RMW operations (full barrier by default)
atomic_add(i, v)
atomic_sub(i, v)
atomic_inc(v)
atomic_dec(v)
atomic_cmpxchg(v, old, new)  // Full barrier

// Conditional returns
atomic_dec_and_test(v)  // Returns true if result is 0, implies full barrier
atomic_inc_and_test(v)  // Returns true if result is 0
atomic_add_negative(i, v) // Returns true if result is negative
```

**Important**: `atomic_read()` and `atomic_set()` are **not** barriers — they are just `READ_ONCE`/`WRITE_ONCE`. If you need ordering around an atomic read, you must use `atomic_read_acquire()` or add explicit `smp_mb()` calls.

### Bitwise Atomic Operations in the Kernel

```c
set_bit(nr, addr)       // Atomic set, full barrier on some architectures
clear_bit(nr, addr)     // Atomic clear
change_bit(nr, addr)    // Atomic toggle
test_and_set_bit(nr, addr)   // Returns old value, full barrier
test_and_clear_bit(nr, addr) // Returns old value, full barrier
test_and_change_bit(nr, addr) // Returns old value, full barrier

// Non-atomic variants (require external locking)
__set_bit(nr, addr)
__clear_bit(nr, addr)
```

### Memory Barriers in the Linux Scheduler

The scheduler uses careful barrier placement to ensure visibility between the task being scheduled out and the CPU that schedules it in:

```c
// In context switch (simplified):
// CPU A: schedules out task T
smp_store_release(&T->on_cpu, 0);  // Release: T's state is fully written

// CPU B: picks up task T to run
while (!smp_load_acquire(&T->on_cpu)) {}  // Acquire: ensure T's state visible
// Now CPU B can safely access T's stack, registers, etc.
```

### Ordering with respect to IRQ/NMI

In interrupt context:

```c
// Main thread writes:
WRITE_ONCE(data, value);
smp_mb();              // Ensure data is visible before flag
WRITE_ONCE(flag, 1);

// IRQ handler reads:
if (READ_ONCE(flag)) {
    smp_mb();          // Ensure flag read before data read
    use(READ_ONCE(data));
}
```

`smp_mb()` in interrupt context is valid and necessary. NMIs and hardware interrupts have an implicit ordering with respect to interrupted code (the interrupt itself serves as a barrier on the interrupted CPU), but not with respect to other CPUs.

---

## 10. C11 Atomics and Memory Order

### The C11 Memory Model

C11/C17 provides a formal memory model via `<stdatomic.h>`:

```c
#include <stdatomic.h>

// Declare atomic types
_Atomic int x;
atomic_int y;       // Equivalent to _Atomic int
atomic_flag f;      // Guaranteed lock-free flag

// Memory order constants
memory_order_relaxed   // No ordering constraints (only atomicity)
memory_order_consume   // Load with data dependency ordering (deprecated in C++17)
memory_order_acquire   // Load barrier
memory_order_release   // Store barrier
memory_order_acq_rel   // RMW with both acquire and release
memory_order_seq_cst   // Sequentially consistent (default)
```

### C11 Atomic Operations

```c
// Load
int val = atomic_load_explicit(&x, memory_order_acquire);

// Store
atomic_store_explicit(&x, 42, memory_order_release);

// Fetch-and-modify
int old = atomic_fetch_add_explicit(&x, 1, memory_order_relaxed);
int old = atomic_fetch_sub_explicit(&x, 1, memory_order_acq_rel);
int old = atomic_fetch_or_explicit(&x, mask, memory_order_relaxed);
int old = atomic_fetch_and_explicit(&x, mask, memory_order_relaxed);
int old = atomic_fetch_xor_explicit(&x, mask, memory_order_relaxed);

// Compare-and-swap
// Strong: never fails spuriously
bool ok = atomic_compare_exchange_strong_explicit(
    &x, &expected, desired,
    memory_order_acq_rel,   // Success order (applied when CAS succeeds)
    memory_order_acquire    // Failure order (applied when CAS fails, must be <= success)
);

// Weak: may fail spuriously (can retry in a loop; sometimes maps to LDREX/STREX)
bool ok = atomic_compare_exchange_weak_explicit(
    &x, &expected, desired,
    memory_order_acq_rel,
    memory_order_acquire
);

// Exchange
int old = atomic_exchange_explicit(&x, new_val, memory_order_acq_rel);

// Standalone fence
atomic_thread_fence(memory_order_seq_cst);
atomic_signal_fence(memory_order_seq_cst); // compiler-only, for signal handlers
```

### Complete C11 Implementation: Message Passing

```c
#include <stdatomic.h>
#include <stdint.h>
#include <assert.h>
#include <pthread.h>
#include <stdio.h>

static int64_t data = 0;
static atomic_int ready = 0;

void *producer(void *arg) {
    data = 42;                                          // plain write
    atomic_store_explicit(&ready, 1, memory_order_release); // release store
    return NULL;
}

void *consumer(void *arg) {
    // Spin until we see ready == 1 via acquire load
    while (atomic_load_explicit(&ready, memory_order_acquire) == 0)
        ;
    // After the acquire load returns 1, all stores before the
    // release store (including data = 42) are guaranteed visible
    assert(data == 42);
    printf("data = %ld\n", data);
    return NULL;
}

int main(void) {
    pthread_t p, c;
    pthread_create(&p, NULL, producer, NULL);
    pthread_create(&c, NULL, consumer, NULL);
    pthread_join(p, NULL);
    pthread_join(c, NULL);
    return 0;
}
```

### C11 Implementation: Spinlock

```c
#include <stdatomic.h>

typedef struct {
    atomic_flag locked;
} spinlock_t;

#define SPINLOCK_INIT { .locked = ATOMIC_FLAG_INIT }

static inline void spinlock_lock(spinlock_t *lock) {
    // test_and_set returns the previous value
    // spin until we set it from false (unlocked) to true (locked)
    while (atomic_flag_test_and_set_explicit(
               &lock->locked, memory_order_acquire))
        ; // busy wait
    // acquire semantics: no operations below this can move above it
}

static inline void spinlock_unlock(spinlock_t *lock) {
    // release semantics: no operations above this can move below it
    atomic_flag_clear_explicit(&lock->locked, memory_order_release);
}

// Usage
spinlock_t lock = SPINLOCK_INIT;

void critical_section(void) {
    spinlock_lock(&lock);
    // ... protected operations ...
    spinlock_unlock(&lock);
}
```

### C11 Implementation: SPSC Lock-Free Queue

Single-producer, single-consumer queue — the simplest correct lock-free structure:

```c
#include <stdatomic.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdlib.h>

#define QUEUE_SIZE 1024

typedef struct {
    void *data[QUEUE_SIZE];
    atomic_size_t head;  // consumer index (only consumer writes)
    atomic_size_t tail;  // producer index (only producer writes)
} spsc_queue_t;

void spsc_queue_init(spsc_queue_t *q) {
    atomic_store_explicit(&q->head, 0, memory_order_relaxed);
    atomic_store_explicit(&q->tail, 0, memory_order_relaxed);
}

// Called by producer only
bool spsc_enqueue(spsc_queue_t *q, void *item) {
    size_t tail = atomic_load_explicit(&q->tail, memory_order_relaxed);
    size_t next = (tail + 1) % QUEUE_SIZE;

    // Load head with acquire to see consumer's progress
    if (next == atomic_load_explicit(&q->head, memory_order_acquire))
        return false; // full

    q->data[tail] = item;

    // Release: data write must be visible before tail update
    atomic_store_explicit(&q->tail, next, memory_order_release);
    return true;
}

// Called by consumer only
bool spsc_dequeue(spsc_queue_t *q, void **item) {
    size_t head = atomic_load_explicit(&q->head, memory_order_relaxed);

    // Acquire: see data written before tail was stored
    if (head == atomic_load_explicit(&q->tail, memory_order_acquire))
        return false; // empty

    *item = q->data[head];

    // Release: data read before head advances
    atomic_store_explicit(&q->head, (head + 1) % QUEUE_SIZE,
                           memory_order_release);
    return true;
}
```

### memory_order_consume (and why you should avoid it)

`memory_order_consume` was designed for **data-dependent loads** — cases where a load depends on the value of a previous load (pointer chasing):

```c
// Intended use
node_t *p = atomic_load_explicit(&list_head, memory_order_consume);
int val = p->value;  // This load is data-dependent on p; 
                     // consume should guarantee ordering
```

On DEC Alpha (the only architecture that can violate data-dependency ordering), consume maps to a hardware barrier. On all other architectures, it is a no-op.

**Problem**: No compiler correctly implements `consume`. All compilers currently promote consume to acquire. The C++ committee deprecated `consume` in C++17 and is working on replacements. **Use `acquire` in practice.**

---

## 11. Go Memory Model

### Go's Formal Memory Model

Go adopted a formally specified memory model in Go 1.19, aligned with C11/Java's approach. The model defines:

1. **Sequenced before**: Within a single goroutine, operations are ordered.
2. **Synchronized before**: Across goroutines, via synchronization primitives.
3. **Happens before**: The transitive closure of sequenced-before and synchronized-before.

**The fundamental rule**: A read `r` of variable `x` is allowed to observe a write `w` to `x` if and only if `w` happens before `r`, and there is no other write `w'` to `x` such that `w` happens before `w'` and `w'` happens before `r`.

### Go Synchronization Primitives and Barriers

Go's synchronization happens through:

```go
// Channel operations: send synchronizes-before corresponding receive
ch <- v   // synchronizes-before
v = <-ch  // happens-after

// sync.Mutex
mu.Lock()    // acquire barrier
mu.Unlock()  // release barrier

// sync.WaitGroup
wg.Done()   // release: signals completion
wg.Wait()   // acquire: observes completion

// sync/atomic
atomic.Store()  // release
atomic.Load()   // acquire
```

### Go's `sync/atomic` Package

```go
package main

import (
    "sync/atomic"
    "fmt"
)

// int32, int64, uint32, uint64, uintptr, unsafe.Pointer

var (
    data  int64
    ready int32 // 0 = not ready, 1 = ready
)

func producer() {
    atomic.StoreInt64(&data, 42)          // plain store (non-atomic, race if concurrent)
    atomic.StoreInt32(&ready, 1)          // release store
}
// NOTE: In Go, plain writes to non-atomic variables are NOT safe
// across goroutines without synchronization. data = 42 would be a
// data race unless protected by a mutex or if the goroutine
// creation itself provides the happens-before edge.

func consumer() {
    for atomic.LoadInt32(&ready) == 0 {
    }
    // After atomic.Load returns 1 with acquire semantics,
    // the atomic.Store to data happens-before this point.
    // BUT: In Go's model, plain (non-atomic) stores to data
    // are NOT guaranteed to be visible even with atomic ready.
    // The Go memory model requires ALL concurrent accesses to
    // shared data to go through synchronized operations.
    fmt.Println(atomic.LoadInt64(&data))
}
```

**Important Go-specific nuance**: Unlike C11, Go does not specify the memory order for `sync/atomic` operations explicitly. The Go spec guarantees that all `sync/atomic` operations are sequentially consistent with respect to each other. This is stronger than necessary but simpler.

### Go's `sync.Mutex` Implementation

Under the hood, Go's mutex uses atomic operations and OS-level futexes:

```go
// Simplified internal view of sync.Mutex
type Mutex struct {
    state int32   // bits: locked | woken | starving | waiter_count
    sema  uint32  // semaphore for blocking waiters
}

func (m *Mutex) Lock() {
    // Fast path: CAS from 0 (unlocked) to 1 (locked)
    if atomic.CompareAndSwapInt32(&m.state, 0, mutexLocked) {
        return
    }
    // Slow path: spin, then block
    m.lockSlow()
}

func (m *Mutex) Unlock() {
    // Fast path: CAS from 1 (locked) to 0 (unlocked)
    new := atomic.AddInt32(&m.state, -mutexLocked)
    if new != 0 {
        m.unlockSlow(new)
    }
}
```

The `atomic.CompareAndSwapInt32` call emits a `LOCK CMPXCHG` on x86 or `LDAXR/STLXR` sequence on ARM, providing the necessary barrier.

### Go Memory Model: Channel-Based Synchronization

Channels are Go's idiomatic synchronization primitive. They provide strong ordering guarantees:

```go
// Rule: the k-th send on a channel with capacity C
// synchronizes before the (k+C)-th receive completes.

ch := make(chan int, 0) // unbuffered

go func() {
    data = 42          // plain write
    ch <- struct{}{}   // send synchronizes-before receive
}()

<-ch                   // receive synchronizes-after send
fmt.Println(data)      // SAFE: data = 42 is guaranteed visible
```

```go
// Buffered channel with capacity C=1
ch := make(chan int, 1)

// The SECOND receive (k=2, C=1, k+C=3) is synchronized before
// the THIRD send. This is the "channel as semaphore" pattern.
```

### Go: `sync/atomic.Value` for Complex Types

```go
import "sync/atomic"

type Config struct {
    MaxConns int
    Timeout  int
}

var config atomic.Value // stores interface{}

// Writer goroutine
func updateConfig(c *Config) {
    config.Store(c) // atomic store with release semantics
}

// Reader goroutine (many concurrent)
func getConfig() *Config {
    c := config.Load() // atomic load with acquire semantics
    if c == nil {
        return &Config{MaxConns: 100, Timeout: 30}
    }
    return c.(*Config)
}
```

`atomic.Value` uses an internal lock or CAS loop to ensure the stored value is never torn. On 64-bit architectures, a single pointer store is already atomic, so the overhead is minimal.

### Go: Implementing a SPSC Queue

```go
package queue

import (
    "runtime"
    "sync/atomic"
    "unsafe"
)

const cacheLinePad = 64

type slot struct {
    val  unsafe.Pointer
    seq  uint64
}

// MPMC queue (Dmitry Vyukov's algorithm)
type Queue struct {
    _    [cacheLinePad]byte
    head uint64
    _    [cacheLinePad - 8]byte
    tail uint64
    _    [cacheLinePad - 8]byte
    buf  []slot
    mask uint64
}

func NewQueue(size uint64) *Queue {
    // size must be power of 2
    q := &Queue{
        buf:  make([]slot, size),
        mask: size - 1,
    }
    for i := range q.buf {
        atomic.StoreUint64(&q.buf[i].seq, uint64(i))
    }
    return q
}

func (q *Queue) Enqueue(val unsafe.Pointer) bool {
    var slot *slot
    pos := atomic.LoadUint64(&q.tail)
    for {
        slot = &q.buf[pos&q.mask]
        seq := atomic.LoadUint64(&slot.seq)
        diff := int64(seq) - int64(pos)
        if diff == 0 {
            if atomic.CompareAndSwapUint64(&q.tail, pos, pos+1) {
                break
            }
        } else if diff < 0 {
            return false // full
        } else {
            pos = atomic.LoadUint64(&q.tail)
        }
        runtime.Gosched()
    }
    slot.val = val
    atomic.StoreUint64(&slot.seq, pos+1) // release: val written before seq
    return true
}

func (q *Queue) Dequeue() (unsafe.Pointer, bool) {
    var slot *slot
    pos := atomic.LoadUint64(&q.head)
    for {
        slot = &q.buf[pos&q.mask]
        seq := atomic.LoadUint64(&slot.seq) // acquire: see val after seq
        diff := int64(seq) - int64(pos+1)
        if diff == 0 {
            if atomic.CompareAndSwapUint64(&q.head, pos, pos+1) {
                break
            }
        } else if diff < 0 {
            return nil, false // empty
        } else {
            pos = atomic.LoadUint64(&q.head)
        }
        runtime.Gosched()
    }
    val := slot.val
    atomic.StoreUint64(&slot.seq, pos+q.mask+1)
    return val, true
}
```

---

## 12. Rust Memory Model and Atomics

### Rust's Safety Guarantees

Rust's ownership and borrow system eliminates data races at compile time. If two threads could concurrently access the same data, at least one being a write, the code **will not compile** without unsafe and proper atomic types.

```rust
use std::sync::atomic::{AtomicI32, AtomicI64, Ordering};
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(AtomicI64::new(0));
    let ready = Arc::new(AtomicI32::new(0));

    let d = Arc::clone(&data);
    let r = Arc::clone(&ready);

    let producer = thread::spawn(move || {
        d.store(42, Ordering::Relaxed);         // write data
        r.store(1, Ordering::Release);          // signal with release
    });

    let consumer = thread::spawn(move || {
        // Spin with acquire semantics
        while ready.load(Ordering::Acquire) == 0 {
            std::hint::spin_loop(); // emit PAUSE on x86, YIELD on ARM
        }
        // All writes before the Release store are visible here
        assert_eq!(data.load(Ordering::Relaxed), 42);
    });

    producer.join().unwrap();
    consumer.join().unwrap();
}
```

### Rust Ordering enum

```rust
pub enum Ordering {
    Relaxed,   // No ordering — only atomicity
    Acquire,   // Load barrier
    Release,   // Store barrier  
    AcqRel,    // Both — for RMW operations
    SeqCst,    // Sequentially consistent (default, strongest)
}
```

**Rules for valid ordering combinations in CAS:**
- Success ordering can be any.
- Failure ordering must be ≤ success ordering.
- Failure ordering cannot be Release or AcqRel.

```rust
let result = x.compare_exchange(
    expected,          // expected value
    desired,           // new value
    Ordering::AcqRel,  // success ordering
    Ordering::Acquire  // failure ordering (must be <= AcqRel, not Release)
);
```

### Rust Atomic Types

```rust
use std::sync::atomic::{
    AtomicBool,
    AtomicI8, AtomicI16, AtomicI32, AtomicI64, AtomicIsize,
    AtomicU8, AtomicU16, AtomicU32, AtomicU64, AtomicUsize,
    AtomicPtr<T>,
    fence,       // standalone fence
    compiler_fence, // compiler-only fence
    Ordering,
};
```

### Rust: Standalone Fence

```rust
use std::sync::atomic::{fence, Ordering};

// Equivalent to a hardware fence instruction
fence(Ordering::SeqCst);    // Full fence
fence(Ordering::Acquire);   // Acquire fence (for loads before it)
fence(Ordering::Release);   // Release fence (for stores after it)

// Compiler-only fence (no hardware instruction)
use std::sync::atomic::compiler_fence;
compiler_fence(Ordering::SeqCst);
```

**When to use `fence()` instead of ordering on atomics:**

```rust
// Pattern: Relaxed loads + single fence (sometimes more efficient)
// when you need to do multiple loads and one barrier

let a = x.load(Ordering::Relaxed);
let b = y.load(Ordering::Relaxed);
fence(Ordering::Acquire);  // One fence for both loads
// Use a and b here with acquire semantics
```

### Rust: Implementing a Spinlock

```rust
use std::cell::UnsafeCell;
use std::ops::{Deref, DerefMut};
use std::sync::atomic::{AtomicBool, Ordering};

pub struct Spinlock<T> {
    locked: AtomicBool,
    data: UnsafeCell<T>,
}

// SAFETY: We guarantee mutual exclusion, so Sync is safe to impl
unsafe impl<T: Send> Sync for Spinlock<T> {}
unsafe impl<T: Send> Send for Spinlock<T> {}

pub struct SpinlockGuard<'a, T> {
    lock: &'a Spinlock<T>,
}

impl<T> Spinlock<T> {
    pub const fn new(val: T) -> Self {
        Spinlock {
            locked: AtomicBool::new(false),
            data: UnsafeCell::new(val),
        }
    }

    pub fn lock(&self) -> SpinlockGuard<'_, T> {
        // Exponential backoff to reduce bus contention
        let mut backoff = 1usize;
        loop {
            // Optimistic: try to acquire without a write (cheap read-only check)
            if !self.locked.load(Ordering::Relaxed) {
                // Try to actually acquire with CAS
                if self.locked
                    .compare_exchange_weak(
                        false,
                        true,
                        Ordering::Acquire,  // success: acquire barrier
                        Ordering::Relaxed,  // failure: no barrier needed
                    )
                    .is_ok()
                {
                    return SpinlockGuard { lock: self };
                }
            }
            // Backoff: spin locally without hitting the bus
            for _ in 0..backoff {
                std::hint::spin_loop();
            }
            backoff = (backoff * 2).min(64);
        }
    }
}

impl<T> Drop for SpinlockGuard<'_, T> {
    fn drop(&mut self) {
        // Release barrier: all protected writes visible before unlock
        self.lock.locked.store(false, Ordering::Release);
    }
}

impl<T> Deref for SpinlockGuard<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        // SAFETY: We hold the lock
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for SpinlockGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        // SAFETY: We hold the lock
        unsafe { &mut *self.lock.data.get() }
    }
}
```

### Rust: Seqlock (Sequence Lock)

A seqlock allows concurrent readers without blocking, at the cost of readers potentially retrying:

```rust
use std::sync::atomic::{AtomicU64, Ordering, fence};
use std::cell::UnsafeCell;

pub struct Seqlock<T: Copy> {
    seq: AtomicU64,
    data: UnsafeCell<T>,
}

unsafe impl<T: Copy + Send> Sync for Seqlock<T> {}

impl<T: Copy> Seqlock<T> {
    pub const fn new(val: T) -> Self {
        Seqlock {
            seq: AtomicU64::new(0),  // even = consistent, odd = write in progress
            data: UnsafeCell::new(val),
        }
    }

    pub fn read(&self) -> T {
        loop {
            // Acquire: see the data written before seq was incremented to even
            let seq1 = self.seq.load(Ordering::Acquire);
            if seq1 % 2 != 0 {
                // Writer is in the middle of a write — spin
                std::hint::spin_loop();
                continue;
            }
            // SAFETY: We check sequence numbers to detect torn reads
            let val = unsafe { *self.data.get() };

            // Acquire: check if seq changed during our read
            let seq2 = self.seq.load(Ordering::Acquire);
            if seq1 == seq2 {
                return val; // Consistent read
            }
            // Torn read: retry
        }
    }

    pub fn write(&self, val: T) {
        // Odd seq signals write in progress
        let seq = self.seq.fetch_add(1, Ordering::Release);
        assert!(seq % 2 == 0, "Concurrent writes are not allowed");

        // SAFETY: We are the sole writer
        unsafe { *self.data.get() = val; }

        // Release: data fully written before seq becomes even again
        self.seq.fetch_add(1, Ordering::Release);
    }
}
```

### Rust: SPSC Ring Buffer

```rust
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

pub struct SPSCQueue<T, const N: usize> {
    buf: [UnsafeCell<MaybeUninit<T>>; N],
    head: AtomicUsize,  // consumer reads head
    tail: AtomicUsize,  // producer reads tail
}

// SAFETY: The design guarantees that head is only written by consumer
// and tail is only written by producer, with proper barriers.
unsafe impl<T: Send, const N: usize> Send for SPSCQueue<T, N> {}
unsafe impl<T: Send, const N: usize> Sync for SPSCQueue<T, N> {}

impl<T, const N: usize> SPSCQueue<T, N> {
    const ASSERT_POWER_OF_TWO: () = assert!(N.is_power_of_two());
    const MASK: usize = N - 1;

    pub fn new() -> Self {
        let _ = Self::ASSERT_POWER_OF_TWO;
        // SAFETY: MaybeUninit doesn't need initialization
        Self {
            buf: unsafe { MaybeUninit::uninit().assume_init() },
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }

    /// Returns false if the queue is full
    pub fn push(&self, val: T) -> bool {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire); // see consumer's progress
        if (tail - head) == N {
            return false; // full
        }
        unsafe {
            (*self.buf[tail & Self::MASK].get()).write(val);
        }
        // Release: val written before tail is updated
        self.tail.store(tail + 1, Ordering::Release);
        true
    }

    /// Returns None if the queue is empty
    pub fn pop(&self) -> Option<T> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire); // see producer's progress
        if head == tail {
            return None; // empty
        }
        let val = unsafe {
            (*self.buf[head & Self::MASK].get()).assume_init_read()
        };
        // Release: val read before head is updated
        self.head.store(head + 1, Ordering::Release);
        Some(val)
    }
}
```

### Rust: Arc and Atomic Reference Counting

`Arc<T>` uses atomics internally. Understanding this is key to understanding ordering costs:

```rust
// Simplified Arc internals (from std library)
struct ArcInner<T> {
    strong: AtomicUsize,   // strong reference count
    weak:   AtomicUsize,   // weak reference count
    data:   T,
}

impl<T> Arc<T> {
    fn clone(&self) -> Arc<T> {
        // Relaxed: we only care about the count,
        // not ordering with respect to T's data
        // (the original Arc already has proper barriers)
        self.inner().strong.fetch_add(1, Ordering::Relaxed);
        Arc { ptr: self.ptr }
    }

    fn drop(&mut self) {
        // Release: ensure all accesses to T are visible before decrement
        if self.inner().strong.fetch_sub(1, Ordering::Release) != 1 {
            return;
        }
        // Acquire fence: synchronize with all Release decrements
        // Ensures we see all writes to T before freeing it
        fence(Ordering::Acquire);
        // Now safe to drop T
        unsafe { drop_in_place(self.ptr.as_mut()); }
    }
}
```

This is a perfect example of: **clone uses Relaxed** (no data access), **drop uses Release** (finish accessing data), **final drop uses Acquire fence** (see all prior Releases before freeing).

---

## 13. Classic Synchronization Patterns

### Pattern 1: Message Passing (Publication)

**Problem**: Thread A produces data, signals Thread B that it's ready.

```c
// C11
int data;
atomic_int ready = 0;

// Producer
data = compute();
atomic_store_explicit(&ready, 1, memory_order_release);

// Consumer
while (!atomic_load_explicit(&ready, memory_order_acquire)) {}
use(data);
```

```rust
// Rust
let data = AtomicI32::new(0);
let ready = AtomicBool::new(false);

// Producer
data.store(compute(), Ordering::Relaxed);
ready.store(true, Ordering::Release);

// Consumer
while !ready.load(Ordering::Acquire) { hint::spin_loop(); }
use(data.load(Ordering::Relaxed));
```

### Pattern 2: Mutual Exclusion (Locking)

The acquire-release pattern around a critical section:

```
acquire() ─── entering critical section
              [exclusively access shared state]
release() ─── leaving critical section
```

```go
// Go: sync.Mutex
var mu sync.Mutex
var shared int

// Goroutine A
mu.Lock()
shared = 42
mu.Unlock()

// Goroutine B
mu.Lock()
fmt.Println(shared) // guaranteed to see 42
mu.Unlock()
```

### Pattern 3: Observer/Dependency Chain

One thread sets up a data structure and publishes a pointer:

```c
// C11 — RCU-like pointer publication
typedef struct { int x, y; } Point;
_Atomic(Point *) global_point = NULL;

// Publisher
Point *p = malloc(sizeof(Point));
p->x = 10;
p->y = 20;
// Publish with release — ensures p->x and p->y are written first
atomic_store_explicit(&global_point, p, memory_order_release);

// Observer
Point *p = atomic_load_explicit(&global_point, memory_order_acquire);
if (p) {
    // After acquire, guaranteed to see p->x = 10, p->y = 20
    printf("%d %d\n", p->x, p->y);
}
```

### Pattern 4: Double-Checked Locking

A common pattern for lazy initialization. **Incorrect without barriers:**

```c
// WRONG (pre-C11)
if (!initialized) {
    lock();
    if (!initialized) {
        obj = create_object();  // stores may be reordered after initialized = 1
        initialized = 1;
    }
    unlock();
}
use(obj);  // may see uninitialized object on other CPUs
```

**Correct with C11:**

```c
// CORRECT
static _Atomic int initialized = 0;
static void *obj = NULL;
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;

if (!atomic_load_explicit(&initialized, memory_order_acquire)) {
    pthread_mutex_lock(&mu);
    if (!atomic_load_explicit(&initialized, memory_order_relaxed)) {
        void *new_obj = create_object();
        // Store obj first, then set initialized with release
        obj = new_obj;  // visibility guaranteed by the release below
        atomic_store_explicit(&initialized, 1, memory_order_release);
    }
    pthread_mutex_unlock(&mu);
}
// After acquire load of initialized == 1, obj is fully initialized
use(obj);
```

**In Rust, use `std::sync::OnceLock` (or `once_cell`):**

```rust
use std::sync::OnceLock;

static OBJ: OnceLock<ExpensiveObject> = OnceLock::new();

fn get_obj() -> &'static ExpensiveObject {
    OBJ.get_or_init(|| create_expensive_object())
}
```

### Pattern 5: Reference Counting (Manual)

```rust
use std::sync::atomic::{AtomicUsize, Ordering, fence};

struct Ref {
    count: AtomicUsize,
    data: String,
}

impl Ref {
    fn acquire(r: *mut Self) {
        unsafe {
            (*r).count.fetch_add(1, Ordering::Relaxed);
            // Relaxed: we don't access data here, just increment count
        }
    }

    fn release(r: *mut Self) {
        unsafe {
            // Release: ensure all our accesses to data complete before decrement
            if (*r).count.fetch_sub(1, Ordering::Release) == 1 {
                // Acquire fence: synchronize with all other Release decrements
                // Ensures we see all writes from other threads before freeing
                fence(Ordering::Acquire);
                drop(Box::from_raw(r));
            }
        }
    }
}
```

---

## 14. Lock-Free Data Structures

### Lock-Free Stack (Treiber Stack)

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    val: T,
    next: *mut Node<T>,
}

pub struct Stack<T> {
    head: AtomicPtr<Node<T>>,
}

unsafe impl<T: Send> Send for Stack<T> {}
unsafe impl<T: Send> Sync for Stack<T> {}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Stack { head: AtomicPtr::new(ptr::null_mut()) }
    }

    pub fn push(&self, val: T) {
        let node = Box::into_raw(Box::new(Node {
            val,
            next: ptr::null_mut(),
        }));

        loop {
            let head = self.head.load(Ordering::Relaxed);
            unsafe { (*node).next = head; }

            // AcqRel: Release ensures node's data visible after CAS
            //         Acquire for the failure case (retry loop)
            match self.head.compare_exchange_weak(
                head, node,
                Ordering::Release,
                Ordering::Relaxed,
            ) {
                Ok(_) => return,
                Err(_) => std::hint::spin_loop(),
            }
        }
    }

    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            // Acquire: if CAS succeeds, we can access head's data
            if head.is_null() {
                return None;
            }
            let next = unsafe { (*head).next };
            match self.head.compare_exchange_weak(
                head, next,
                Ordering::Acquire,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    // SAFETY: We won the CAS — we own this node
                    // HAZARD: Another thread might be reading head
                    // This is the memory reclamation problem! See Section 16.
                    let val = unsafe { Box::from_raw(head).val };
                    return Some(val);
                }
                Err(_) => std::hint::spin_loop(),
            }
        }
    }
}
```

**Warning**: The stack above has a memory reclamation bug — see Section 16 for hazard pointers and epoch-based reclamation.

### Michael-Scott Lock-Free Queue

```c
// C11 implementation of the Michael-Scott MPMC queue
#include <stdatomic.h>
#include <stdlib.h>
#include <stddef.h>

typedef struct Node {
    _Atomic(struct Node *) next;
    int value;
} Node;

typedef struct {
    _Atomic(Node *) head; // Dequeue from head
    _Atomic(Node *) tail; // Enqueue to tail
} MSQueue;

void ms_queue_init(MSQueue *q) {
    Node *dummy = calloc(1, sizeof(Node));
    atomic_store_explicit(&dummy->next, NULL, memory_order_relaxed);
    atomic_store_explicit(&q->head, dummy, memory_order_relaxed);
    atomic_store_explicit(&q->tail, dummy, memory_order_relaxed);
}

void ms_queue_enqueue(MSQueue *q, int val) {
    Node *node = malloc(sizeof(Node));
    node->value = val;
    atomic_store_explicit(&node->next, NULL, memory_order_relaxed);

    while (1) {
        Node *tail = atomic_load_explicit(&q->tail, memory_order_acquire);
        Node *next = atomic_load_explicit(&tail->next, memory_order_acquire);

        // Verify tail is still the actual tail
        if (tail == atomic_load_explicit(&q->tail, memory_order_acquire)) {
            if (next == NULL) {
                // Tail is pointing to the last node; try to link
                if (atomic_compare_exchange_weak_explicit(
                        &tail->next, &next, node,
                        memory_order_release,
                        memory_order_relaxed)) {
                    // Try to swing tail (ok if it fails — next enqueue will fix it)
                    atomic_compare_exchange_strong_explicit(
                        &q->tail, &tail, node,
                        memory_order_release,
                        memory_order_relaxed);
                    return;
                }
            } else {
                // Tail is not pointing to last node; advance it
                atomic_compare_exchange_strong_explicit(
                    &q->tail, &tail, next,
                    memory_order_release,
                    memory_order_relaxed);
            }
        }
    }
}

int ms_queue_dequeue(MSQueue *q, int *out) {
    while (1) {
        Node *head = atomic_load_explicit(&q->head, memory_order_acquire);
        Node *tail = atomic_load_explicit(&q->tail, memory_order_acquire);
        Node *next = atomic_load_explicit(&head->next, memory_order_acquire);

        if (head == atomic_load_explicit(&q->head, memory_order_acquire)) {
            if (head == tail) {
                if (next == NULL) return 0; // Empty
                // Tail is behind; advance it
                atomic_compare_exchange_strong_explicit(
                    &q->tail, &tail, next,
                    memory_order_release,
                    memory_order_relaxed);
            } else {
                *out = next->value;
                if (atomic_compare_exchange_weak_explicit(
                        &q->head, &head, next,
                        memory_order_release,
                        memory_order_relaxed)) {
                    free(head); // reclaim the old dummy node
                    return 1;
                }
            }
        }
    }
}
```

---

## 15. The ABA Problem

### What is ABA?

The ABA problem occurs in lock-free algorithms that use CAS:

```
Initial state: head → A → B → C

Thread 1: reads head = A, gets preempted
Thread 2: pops A (head → B → C), pushes D (head → D → B → C), pops B (head → D → C), pushes A (head → A → D → C)
Thread 1: resumes, does CAS(head, A, B) — succeeds!
           But B is no longer in the list — this is wrong!
```

The CAS succeeded because the value at head is still `A`, even though the structure of the list changed completely.

### Solutions to ABA

**1. Tagged Pointer (Version Counter)**

```c
// C11 with 128-bit CAS (Intel: CMPXCHG16B)
typedef struct {
    Node *ptr;
    uint64_t tag;
} TaggedPtr;

_Atomic(TaggedPtr) head;

// CAS with tag
TaggedPtr old_head = atomic_load_explicit(&head, memory_order_acquire);
TaggedPtr new_head = { old_head.ptr->next, old_head.tag + 1 };
atomic_compare_exchange_weak_explicit(
    &head, &old_head, new_head,
    memory_order_acq_rel, memory_order_acquire);
// Even if ptr == old_head.ptr, the tag will be different if ABA occurred
```

**2. Hazard Pointers** — see Section 16

**3. Epoch-Based Reclamation** — see Section 16

---

## 16. Memory Reclamation Patterns

The fundamental problem in lock-free structures: when can you safely free a node that no thread is reading?

### Hazard Pointers

Each thread announces the pointers it is currently accessing. Before freeing, check all hazard pointers:

```c
// Simplified hazard pointer implementation in C
#define MAX_THREADS 64
#define MAX_HAZARD  2

_Atomic(void *) hazard[MAX_THREADS][MAX_HAZARD];

// Per-thread retirement list
typedef struct RetiredNode {
    void *ptr;
    struct RetiredNode *next;
} RetiredNode;

__thread RetiredNode *retired_list = NULL;
__thread int thread_id = -1;

void hp_set(int slot, void *ptr) {
    atomic_store_explicit(
        &hazard[thread_id][slot], ptr, memory_order_release);
}

void hp_clear(int slot) {
    atomic_store_explicit(
        &hazard[thread_id][slot], NULL, memory_order_relaxed);
}

void hp_retire(void *ptr) {
    RetiredNode *node = malloc(sizeof(RetiredNode));
    node->ptr = ptr;
    node->next = retired_list;
    retired_list = node;
    hp_scan(); // Try to reclaim
}

void hp_scan(void) {
    // Collect all active hazard pointers
    void *hazards[MAX_THREADS * MAX_HAZARD];
    int count = 0;
    for (int t = 0; t < MAX_THREADS; t++)
        for (int s = 0; s < MAX_HAZARD; s++) {
            void *h = atomic_load_explicit(
                &hazard[t][s], memory_order_acquire);
            if (h) hazards[count++] = h;
        }

    // Free any retired node not in the hazard set
    RetiredNode **prev = &retired_list;
    RetiredNode *curr = retired_list;
    while (curr) {
        bool hazardous = false;
        for (int i = 0; i < count; i++)
            if (hazards[i] == curr->ptr) { hazardous = true; break; }

        if (!hazardous) {
            free(curr->ptr);
            *prev = curr->next;
            RetiredNode *tmp = curr;
            curr = curr->next;
            free(tmp);
        } else {
            prev = &curr->next;
            curr = curr->next;
        }
    }
}
```

**In Rust**: Use the `haphazard` crate for production-grade hazard pointers.

### Epoch-Based Reclamation (EBR)

Used by crossbeam in Rust, jemalloc, and many production systems:

```rust
// Conceptual model of epoch-based reclamation
// (Crossbeam's actual implementation is more sophisticated)

use std::sync::atomic::{AtomicUsize, Ordering};

static GLOBAL_EPOCH: AtomicUsize = AtomicUsize::new(0);

// Each thread has a local epoch and pinned state
struct Guard {
    local_epoch: usize,
}

fn pin() -> Guard {
    let epoch = GLOBAL_EPOCH.load(Ordering::Acquire);
    // Announce we're reading at this epoch
    Guard { local_epoch: epoch }
}

// Retire an object — add to epoch-stamped deferred free list
fn retire<T>(ptr: *mut T, epoch: usize) {
    // Add to deferred_free[epoch % 3]
    // Objects in epoch E can be freed when all threads
    // have advanced past epoch E
}

// Advance the global epoch if all threads are in sync
fn try_advance() {
    let epoch = GLOBAL_EPOCH.load(Ordering::Relaxed);
    // Check if all pinned threads are in current epoch
    // If yes: increment global epoch, free objects from 2 epochs ago
    GLOBAL_EPOCH.fetch_add(1, Ordering::Release);
}
```

**Crossbeam's actual usage:**

```rust
use crossbeam_epoch::{self as epoch, Atomic, Owned, Shared};

let a: Atomic<String> = Atomic::null();

// Write
let guard = &epoch::pin();
let old = a.swap(Owned::new("hello".to_string()), Ordering::AcqRel, guard);
unsafe { guard.defer_destroy(old); } // Deferred free

// Read
let guard = &epoch::pin();
let val: Shared<'_, String> = a.load(Ordering::Acquire, guard);
if let Some(s) = unsafe { val.as_ref() } {
    println!("{}", s);
}
// Guard released on drop — may trigger epoch advance and reclamation
```

---

## 17. Real-World Linux Kernel Examples

### Kernel Example 1: Scheduler Task State

From `kernel/sched/core.c` — setting task state with ordering:

```c
// Set task to sleeping state, then check if there's pending work
// The ordering here is critical: we must check for work AFTER
// setting the state, not before.

set_current_state(TASK_INTERRUPTIBLE);
// Expands to:
//   smp_store_mb(current->state, TASK_INTERRUPTIBLE);
// which is:
//   WRITE_ONCE(current->state, TASK_INTERRUPTIBLE);
//   smp_mb();

if (condition_to_wait_for) {
    schedule(); // Go to sleep
}

// The smp_mb() ensures that if another CPU sets the condition and
// calls wake_up() concurrently, either:
// 1. We see the condition (don't sleep), OR
// 2. wake_up() sees our TASK_INTERRUPTIBLE state (wakes us up)
// Without the barrier, BOTH can fail: we miss the condition AND
// the waker sees TASK_RUNNING (won't wake us). Deadlock.
```

### Kernel Example 2: RCU List Manipulation

```c
// From include/linux/rculist.h — adding a node to an RCU list
static inline void list_add_rcu(struct list_head *new,
                                 struct list_head *head)
{
    __list_add_rcu(new, head, head->next);
}

static inline void __list_add_rcu(struct list_head *new,
    struct list_head *prev, struct list_head *next)
{
    if (!IS_ENABLED(CONFIG_PROVE_RCU_LIST)) {
        WARN_ON_ONCE(!in_rcu_read_lock_region());
    }
    new->next = next;
    new->prev = prev;
    rcu_assign_pointer(list_next_rcu(prev), new);
    // rcu_assign_pointer expands to:
    //   smp_store_release(&(prev->next), new)
    // This ensures all writes to *new are visible before
    // prev->next is updated to point to new.
    next->prev = new;
}
```

### Kernel Example 3: Seqlocks in the Kernel

The kernel's timekeeping uses seqlocks for high-frequency, read-mostly data:

```c
// From kernel/time/timekeeping.c (simplified)
static struct {
    seqcount_t seq;
    struct timespec64 wall_time;
} tk_core;

// Reader (called billions of times per second)
static void timekeeping_read(struct timespec64 *ts)
{
    unsigned int seq;
    do {
        seq = read_seqcount_begin(&tk_core.seq);
        *ts = tk_core.wall_time;
    } while (read_seqcount_retry(&tk_core.seq, seq));
    // read_seqcount_begin: loads seq (acquire), returns it
    // If seq is odd, spins (writer active)
    // read_seqcount_retry: loads seq again (acquire), checks if changed
}

// Writer (called periodically by timer interrupt)
static void timekeeping_update(struct timespec64 *new_ts)
{
    write_seqcount_begin(&tk_core.seq);
    // write_seqcount_begin: seq++ (now odd), smp_wmb()
    tk_core.wall_time = *new_ts;
    write_seqcount_end(&tk_core.seq);
    // write_seqcount_end: smp_wmb(), seq++ (now even)
}
```

The seqlock implementation:
```c
// Simplified seqlock from include/linux/seqlock.h
typedef struct {
    unsigned sequence;
    spinlock_t lock;
} seqlock_t;

static inline unsigned read_seqbegin(const seqlock_t *sl)
{
    unsigned ret;
    repeat:
        ret = READ_ONCE(sl->sequence);
        if (unlikely(ret & 1)) {
            cpu_relax(); // PAUSE on x86
            goto repeat;
        }
        smp_rmb(); // Acquire: reads of protected data follow this
        return ret;
}

static inline unsigned read_seqretry(const seqlock_t *sl, unsigned start)
{
    smp_rmb(); // Acquire: ensure we've read all the protected data
    return unlikely(sl->sequence != start);
}

static inline void write_seqlock(seqlock_t *sl)
{
    spin_lock(&sl->lock);
    ++sl->sequence; // Odd = write in progress
    smp_wmb();      // Release: seq increment visible before data writes
}

static inline void write_sequnlock(seqlock_t *sl)
{
    smp_wmb();      // Release: data writes visible before seq increment
    ++sl->sequence; // Even = write complete
    spin_unlock(&sl->lock);
}
```

### Kernel Example 4: Per-CPU Data and Barriers

```c
// Per-CPU data avoids false sharing and atomic operations
// But requires barriers when publishing results to other CPUs

DEFINE_PER_CPU(long, request_count);

// Increment: no atomic needed, we're only CPU to write this variable
this_cpu_inc(request_count);

// To read from another CPU (approximate total):
long total = 0;
int cpu;
for_each_online_cpu(cpu) {
    total += per_cpu(request_count, cpu);
}
// Note: this is a relaxed read — we may see stale values from other CPUs.
// This is acceptable for statistics but not for synchronization.

// For a consistent snapshot, you would need smp_mb() before reading each
// per-CPU value and on the writing CPU before updating:
smp_mb__before_atomic(); // or appropriate barrier
this_cpu_inc(request_count);
smp_mb__after_atomic();
```

### Kernel Example 5: Memory Barriers in Network Drivers

```c
// From a typical network driver — DMA descriptor ring
struct rx_desc {
    __le32 status;    // Ownership bit: 0=CPU, 1=NIC
    __le32 length;
    __le64 addr;
};

void driver_rx_fill(struct net_device *dev, int idx)
{
    struct rx_desc *desc = &dev->rx_ring[idx];
    dma_addr_t dma = dma_map_single(...);

    desc->addr   = cpu_to_le64(dma);
    desc->length = cpu_to_le32(MAX_RX_BUF);

    // CRITICAL: status must be written LAST, after addr and length
    // Without this barrier, the NIC might see status=NIC before
    // seeing the correct addr and length
    dma_wmb(); // Write barrier before handing to DMA hardware

    desc->status = cpu_to_le32(DESC_STATUS_NIC_OWNS); // Handoff to NIC
}

void driver_rx_process(struct net_device *dev, int idx)
{
    struct rx_desc *desc = &dev->rx_ring[idx];

    // Check if NIC has completed this descriptor
    if (le32_to_cpu(desc->status) & DESC_STATUS_DONE) {
        dma_rmb(); // Read barrier: ensure we see length/addr after status
        int len = le32_to_cpu(desc->length);
        // ... process received frame ...
    }
}
```

---

## 18. Compiler Barriers vs Hardware Barriers

### The Compiler's Role

The compiler performs many optimizations that can reorder memory accesses:

1. **Common Subexpression Elimination (CSE)**: Load `x` once, reuse the cached value.
2. **Dead Store Elimination**: Remove a store if the stored value is never read (by the compiler's analysis).
3. **Invariant Hoisting**: Move a load out of a loop if the compiler believes the value doesn't change.
4. **Register Allocation**: Keep a value in a register instead of writing it to memory.

These optimizations are all valid for single-threaded code. They are **dangerous** for multi-threaded code.

### Compiler Barrier

```c
// C: compiler barrier — prevents compiler reordering across this point
// Emits no hardware instruction
asm volatile("" ::: "memory");

// Or equivalently in the Linux kernel:
barrier();

// Or using C11:
atomic_signal_fence(memory_order_seq_cst); // compiler-only fence
```

```rust
// Rust compiler barrier
use std::sync::atomic::{compiler_fence, Ordering};
compiler_fence(Ordering::SeqCst);
```

```go
// Go doesn't expose compiler barriers directly — use atomic operations
// or runtime.Gosched() as a soft barrier
```

### Hardware Barrier

```c
// C: hardware barrier — emits an actual fence instruction
asm volatile("mfence" ::: "memory"); // x86
asm volatile("dmb ish" ::: "memory"); // ARM

// Or use C11 atomics which generate appropriate hardware fences:
atomic_thread_fence(memory_order_seq_cst);
```

### When Compiler Barriers Suffice

Compiler barriers are sufficient when:
1. You're on a sequentially consistent architecture (x86) and only need to prevent compiler optimizations.
2. You're synchronizing between the main thread and a signal handler on the same thread (signals run on the same CPU; no hardware reordering possible).
3. You need to prevent the compiler from eliminating or reordering stores to hardware registers that you've mapped via volatile pointers (though `volatile` alone also achieves this in C).

```c
// Signal handler synchronization — compiler barrier is sufficient
// because signals are delivered on the same CPU as the main thread
volatile sig_atomic_t signal_received = 0;

void signal_handler(int sig) {
    data = compute_data();
    asm volatile("" ::: "memory"); // Compiler barrier
    signal_received = 1;
}

void main_loop(void) {
    while (!signal_received) {}
    asm volatile("" ::: "memory"); // Compiler barrier
    use(data); // Safe: same CPU delivered the signal
}
```

### Volatile vs Atomics vs Barriers

| Mechanism | Prevents compiler elim. | Prevents compiler reorder | Prevents hardware reorder | Guarantees atomicity |
|-----------|------------------------|--------------------------|--------------------------|---------------------|
| `volatile` | ✓ | ✗ | ✗ | ✗ |
| `barrier()` / `asm volatile` | ✓ | ✓ | ✗ | ✗ |
| `atomic_thread_fence` | ✓ | ✓ | ✓ | ✗ |
| `atomic_load/store` | ✓ | ✓ | ✓ | ✓ |

**`volatile` in C is not thread-safe.** It prevents the compiler from caching a value in a register but does not prevent hardware reordering and does not guarantee atomicity. Use `_Atomic` / `atomic_*` for shared variables.

---

## 19. Performance Analysis and Costs

### Benchmark: Barrier Costs on x86 (approximate cycles)

| Operation | Cycles (approx.) |
|-----------|-----------------|
| Normal load | 4-5 (L1 hit) |
| Normal store | 4-5 (L1 hit) |
| `LFENCE` | 20-30 |
| `SFENCE` | 5-10 (usually cheap; stores are buffered anyway) |
| `MFENCE` | 40-100+ |
| `LOCK XCHG` | 40-100+ |
| `LOCK CMPXCHG` (uncontested) | 40-80 |
| `LOCK CMPXCHG` (contested) | 200-1000+ |
| Cache line invalidation | 100-300 (DRAM access) |

### Benchmark: Barrier Costs on ARM (approximate cycles)

| Operation | Cycles (approx.) |
|-----------|-----------------|
| `DMB ISH` | 30-100+ |
| `DSB ISH` | 40-200+ |
| `ISB` | 20-50 |
| `LDAR` (load-acquire) | Same as uncached load + ~20 |
| `STLR` (store-release) | Same as store + ~10 |

**Key insight**: On ARM, load-acquire (`LDAR`) and store-release (`STLR`) are typically cheaper than explicit `DMB` instructions because they only constrain one point, not all outstanding operations.

### The Cost of False Sharing

```c
// Benchmark setup: 4 threads, each incrementing their counter 1M times
struct {
    long count; // All 4 in same 64-byte cache line
} counters[4];

// vs.

struct {
    long count;
    char pad[56]; // Each counter in its own cache line
} counters_padded[4];
```

Typical result: the padded version is 5-10x faster due to elimination of cache line ping-pong (MESI protocol transitions between Modified states).

### Reducing Barrier Overhead: Strategies

**1. Use acquire/release instead of full fences**

```rust
// Expensive: seq_cst on both sides
x.store(1, Ordering::SeqCst);
y.load(Ordering::SeqCst);

// Cheaper: release on store, acquire on load
x.store(1, Ordering::Release);
y.load(Ordering::Acquire);
```

**2. Batch operations with a single fence**

```rust
// Expensive: 3 separate acquire loads
let a = x.load(Ordering::Acquire);
let b = y.load(Ordering::Acquire);
let c = z.load(Ordering::Acquire);

// Cheaper: 3 relaxed loads + one fence
let a = x.load(Ordering::Relaxed);
let b = y.load(Ordering::Relaxed);
let c = z.load(Ordering::Relaxed);
fence(Ordering::Acquire);
```

**3. Read-side optimization: SeqLock over RWMutex for read-heavy workloads**

```
RWMutex: reader must atomically increment/decrement reader count.
         Writer must wait for all readers to drain.
         Even reads have an atomic operation with a write.

SeqLock: reader only reads (no write operations on the lock).
         Only cost is the two sequence number reads + potential retries.
         Faster for very short critical sections.
```

**4. Per-CPU / Thread-Local State**

Where possible, eliminate sharing entirely using per-CPU data (kernel) or thread-local storage (userspace). No barriers needed for thread-local data.

---

## 20. Common Bugs and Debugging

### Bug 1: Missing Load Barrier

```c
// BUG: Missing rmb() between flag check and data read
if (READ_ONCE(flag)) {
    // No rmb() here — data read may be reordered before flag check
    use(READ_ONCE(data)); // POTENTIAL BUG ON ARM/POWER
}

// FIX:
if (READ_ONCE(flag)) {
    smp_rmb();
    use(READ_ONCE(data));
}
// Or use atomic_load_explicit with memory_order_acquire for flag
```

### Bug 2: Missing Store Barrier

```c
// BUG: Data may not be visible when flag is set
WRITE_ONCE(data, 42);
// No wmb() here
WRITE_ONCE(flag, 1); // Consumer may see flag=1 but data != 42

// FIX:
WRITE_ONCE(data, 42);
smp_wmb();
WRITE_ONCE(flag, 1);
```

### Bug 3: Incorrect Memory Order in CAS

```rust
// BUG: Failure ordering stronger than success
x.compare_exchange(old, new,
    Ordering::Relaxed,  // success: relaxed!
    Ordering::SeqCst);  // failure: seq_cst — stronger than success!
// This is actually invalid — failure ordering must be <= success ordering

// BUG: Using Release for failure ordering
x.compare_exchange(old, new,
    Ordering::Release,  // success
    Ordering::Release); // failure: Release is invalid for failure!
// Release is not valid for failure ordering — use Acquire or Relaxed

// CORRECT:
x.compare_exchange(old, new,
    Ordering::AcqRel,   // success
    Ordering::Acquire); // failure: <= AcqRel, and valid for failure
```

### Bug 4: Read-Modify-Write Without AcqRel

```rust
// BUG: Using separate load+store instead of RMW atomic
let val = counter.load(Ordering::Acquire);
counter.store(val + 1, Ordering::Release);
// TOCTOU race! Another thread may have incremented between our load and store.

// FIX: Use atomic fetch_add
counter.fetch_add(1, Ordering::AcqRel);
// Or Relaxed if no ordering needed:
counter.fetch_add(1, Ordering::Relaxed);
```

### Bug 5: Broken Double-Checked Locking (C, pre-C11 or missing barriers)

```c
// CLASSIC BUG — broken before C11 and even in C11 without proper ordering
static Object *obj = NULL;
static Mutex mu;

Object *get_obj() {
    if (obj != NULL) {        // Check 1: not protected, potential data race
        return obj;           // obj seen, but fields may be uninitialized!
    }
    lock(&mu);
    if (obj == NULL) {        // Check 2: protected
        obj = create();       // Stores to obj's fields may be visible
                              // AFTER obj pointer itself becomes non-NULL
    }
    unlock(&mu);
    return obj;
}

// FIX: Use _Atomic for the pointer, with acquire/release ordering
static _Atomic(Object *) obj = NULL;

Object *get_obj() {
    Object *p = atomic_load_explicit(&obj, memory_order_acquire);
    if (p) return p;
    lock(&mu);
    p = atomic_load_explicit(&obj, memory_order_relaxed);
    if (!p) {
        p = create();
        atomic_store_explicit(&obj, p, memory_order_release);
    }
    unlock(&mu);
    return p;
}
```

### Debugging Tools

**1. ThreadSanitizer (TSan)**
Detects data races at runtime. Works with C, C++, Go, and Rust.
```bash
# C/C++
clang -fsanitize=thread -g -O1 prog.c -o prog && ./prog

# Go
go test -race ./...

# Rust
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test
```

**2. Helgrind (Valgrind)**
```bash
valgrind --tool=helgrind ./prog
```

**3. Linux `perf` for Memory Ordering Costs**
```bash
perf stat -e instructions,cache-misses,LLC-store-misses,mem-stores ./prog
```

**4. Intel Inspector XE**
Deterministic memory race detection on x86.

**5. Litmus Tests**
Small test programs designed to expose specific memory ordering violations. The `herd7`/`litmus7` tool from the diy7 suite can model-check litmus tests against formal memory models.

```
(* Litmus test: MP — Message Passing *)
AArch64 MP
{
  0:X1=x; 0:X3=y;
  1:X1=x; 1:X3=y;
}
P0          | P1           ;
STR X2,[X1] | LDR X2,[X3] ;
STR X4,[X3] | LDR X5,[X1] ;
exists (1:X2=1 /\ 1:X5=0)
(* On ARM without barriers, this outcome IS observable *)
```

---

## 21. Mental Models for Experts

### Mental Model 1: "Multiple Observers on Different Trains"

Imagine each CPU as a train moving along a track (time). Each train has its own view of "now". Two trains may be at the same clock time but have different views of which events they've observed. A memory barrier is like a **radio communication protocol**: "Before you see me wave my flag, you must have seen my package delivered."

### Mental Model 2: "The Post Office Model"

- Stores are letters you drop in a mailbox. They're sent but not yet delivered.
- Loads are checking your own mailbox.
- Other CPUs have their own mailboxes.
- A release barrier is **sealing and stamping all your outgoing letters** — guaranteeing they'll be delivered before any future letters.
- An acquire barrier is **waiting for the mail carrier** before reading your incoming mail.
- A full fence is both: send all outgoing, then wait for incoming.

### Mental Model 3: "The Scoreboard"

Think of a CPU as having two scoreboards: a **local scoreboard** (store buffer) and the **global scoreboard** (cache coherency state). When you write, you update your local scoreboard immediately. The global scoreboard updates asynchronously. A barrier forces a sync between local and global.

### Mental Model 4: Happens-Before Graph

Every memory model can be described as a directed graph where edges represent "happens-before" relationships. Adding a barrier adds an edge. A program is race-free if for every pair of conflicting accesses (at least one a write), there is a happens-before path between them.

```
Thread 1: [write data] ──release──→ [write ready]
                                              │
                                         synchronizes
                                              │
Thread 2:                         [read ready] ──acquire──→ [read data]
```

The release-acquire pair creates the edge. Any write before the release is happens-before any read after the acquire on the other side.

### Mental Model 5: The Litmus Test Mindset

Before writing any concurrent code, ask: "What is the weakest reordering this architecture permits, and does my code remain correct under that reordering?"

For each pair of accesses from different threads:
1. Can the CPU reorder them? (Consult architecture manual)
2. Can the compiler reorder them? (Always yes, without barriers)
3. Is that reordering observable? (Does it produce incorrect behavior?)
4. What is the minimum barrier needed to prevent it?

### The Expert's Checklist

For every shared variable access in concurrent code:

- [ ] Is this access protected by a lock? (If yes, the lock provides the barriers)
- [ ] Is this a standalone atomic with explicit ordering?
- [ ] What ordering does this access need: relaxed, acquire, release, or seq_cst?
- [ ] Is the variable marked atomic? (Prevents compiler from assuming exclusivity)
- [ ] Have I verified correctness on weakly-ordered architectures (ARM/POWER)?
- [ ] Have I checked for the ABA problem in any CAS loops?
- [ ] Have I addressed memory reclamation (hazard pointers / EBR) for lock-free structures?
- [ ] Is there potential for false sharing? (Check struct layout and cache line alignment)

### The Deliberate Practice Loop for Concurrency Mastery

1. **Study the formal model**: Read the architecture manual's memory model chapter. For Linux kernel work, read `Documentation/memory-barriers.txt` (one of the most comprehensive documents on the topic).

2. **Write litmus tests**: For every pattern you write, construct the corresponding litmus test and reason about what outcomes are possible.

3. **Read production code**: Study the Linux kernel's synchronization (`kernel/locking/`, `include/linux/seqlock.h`), crossbeam's lock-free structures, and Tokio's runtime.

4. **Break things deliberately**: Write code with intentionally missing barriers and observe failures with TSan or on weakly-ordered hardware (Raspberry Pi for ARM, QEMU for emulated POWER).

5. **Formalize your reasoning**: Before writing any lock-free code, write a comment that describes the invariant maintained, the happens-before relationships established, and why every access has the minimum necessary ordering.

---

## Appendix: Quick Reference

### C11 Memory Orders

| Order | Valid for | Semantics |
|-------|-----------|-----------|
| `relaxed` | all | Atomicity only |
| `acquire` | load, RMW | No reorder after |
| `release` | store, RMW | No reorder before |
| `acq_rel` | RMW only | Both acquire + release |
| `seq_cst` | all | Total order |
| `consume` | load | Data dependency (use acquire instead) |

### Rust Ordering

| `Ordering` | Use for |
|------------|---------|
| `Relaxed` | Counters, flags without ordering constraints |
| `Acquire` | Load: guard following accesses |
| `Release` | Store: protect preceding accesses |
| `AcqRel` | RMW: protect both sides |
| `SeqCst` | When you need a global total order |

### Linux Kernel Barrier Summary

| Barrier | Prevents |
|---------|---------|
| `smp_mb()` | All reordering across barrier |
| `smp_rmb()` | Load-load reordering |
| `smp_wmb()` | Store-store reordering |
| `smp_load_acquire(p)` | Reordering of following accesses before this load |
| `smp_store_release(p, v)` | Reordering of preceding accesses after this store |
| `barrier()` | Compiler reordering only (no HW fence) |
| `mb()` | Hardware barrier including MMIO/DMA |
| `dma_wmb()` | Store ordering for DMA descriptor updates |
| `READ_ONCE(x)` | Compiler elimination/splitting of load |
| `WRITE_ONCE(x, v)` | Compiler elimination/splitting of store |

### Architecture Comparison

| Feature | x86-64 | ARM64 | RISC-V | POWER |
|---------|--------|-------|--------|-------|
| Default model | TSO | Weak | Weak (RVWMO) | Weak |
| Load-load reorder | No | Yes | Yes | Yes |
| Load-store reorder | No | Yes | Yes | Yes |
| Store-store reorder | No | Yes | Yes | Yes |
| Store-load reorder | Yes | Yes | Yes | Yes |
| Full fence | MFENCE | DMB ISH | FENCE rw,rw | SYNC |
| Acq/Rel native | No (use LOCK) | LDAR/STLR | LR/SC + .AQ/.RL | LWARX/STWCX |

---

*"Concurrency is not just a technical skill — it is a cognitive discipline. The expert's advantage is not knowing more barrier types, but maintaining a precise mental model of what every thread observes at every point in time. Build that model with the same rigor you would apply to a formal proof."*

Now I'll create the comprehensive memory barriers guide. This will be an extensive document.**2,717 lines, ~11,700 words** — here is your complete guide. Here is what's covered across 21 chapters:

---

**Hardware foundations** — Store buffers, invalidation queues, the MESI/MESIF/MOESI coherency protocols, out-of-order execution and the Reorder Buffer, and why each of these independently causes reordering.

**Architecture specifics** — Deep dives into x86-64 TSO (MFENCE, LFENCE, SFENCE, LOCK prefix, write-combining), ARM64 (DMB/DSB/ISB with sharing domains, native LDAR/STLR acquire-release instructions, ARMv8 exclusive monitors), and RISC-V RVWMO (FENCE predicate/successor matrix, .AQ/.RL on atomics).

**Linux kernel** — Every kernel primitive: `smp_mb/rmb/wmb`, `READ_ONCE/WRITE_ONCE`, `smp_load_acquire/smp_store_release`, RCU internals (`rcu_dereference`, `rcu_assign_pointer`, `synchronize_rcu`), seqlocks with real timekeeping code, DMA barriers, scheduler task state ordering, per-CPU data, and network driver descriptor ring patterns.

**C11 atomics** — All six memory orders with formal semantics, correct CAS patterns (strong vs weak, success/failure order rules), SPSC queue implementation, double-checked locking, and the `memory_order_consume` deprecation story.

**Go memory model** — The formal Go 1.19 model, `sync/atomic` with correct usage, channel synchronization guarantees, `sync.Mutex` internals, `atomic.Value` for complex types, and an MPMC queue implementation.

**Rust** — All `Ordering` variants, standalone `fence` vs `compiler_fence`, `Arc` internal reference counting ordering analysis, a production-grade `Spinlock<T>` with exponential backoff, a `Seqlock<T>`, and a const-generic SPSC ring buffer with `MaybeUninit`.

**Lock-free patterns** — Treiber stack, Michael-Scott queue, ABA problem and tagged pointer solution, hazard pointers, and epoch-based reclamation (with Crossbeam examples).

**Debugging and performance** — TSan, Helgrind, litmus tests with herd7, false sharing costs, barrier cycle costs on x86 vs ARM, and batching relaxed loads with a single fence.