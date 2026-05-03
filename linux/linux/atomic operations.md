# Atomic Operations: A Complete Systems-Level Guide

> **Summary (4-8 lines):**
> Atomic operations are the lowest-level primitive for safe concurrent access to shared memory — indivisible from the perspective of any observer in the system. Understanding them requires mastering the full stack: CPU microarchitecture (pipelines, caches, store buffers), cache-coherency protocols (MESI/MESIF/MOESI), memory consistency models (TSO, weak ordering), compiler barriers, hardware fences, ISA-level instructions (LOCK prefix, LDREX/STREX, LR/SC), and language-level memory models (C11, Rust). They underpin every lock, every lock-free structure, every RCU mechanism, and every kernel synchronization primitive. Misuse is catastrophic — data corruption, ABA bugs, livelock, and TOCTOU races are all real production failures. This guide builds a first-principles mental model: hardware → kernel → language → patterns → security.

---

## Table of Contents

1. [Why Atomics Exist: The Problem Space](#1-why-atomics-exist)
2. [CPU Microarchitecture Foundations](#2-cpu-microarchitecture-foundations)
3. [Cache Coherency: MESI, MESIF, MOESI](#3-cache-coherency)
4. [Memory Consistency Models](#4-memory-consistency-models)
5. [Memory Barriers and Fences](#5-memory-barriers-and-fences)
6. [ISA-Level Atomic Instructions](#6-isa-level-atomic-instructions)
7. [C11 Atomics (complete)](#7-c11-atomics)
8. [GCC Built-ins and Legacy Patterns](#8-gcc-built-ins-and-legacy-patterns)
9. [Rust Atomics (complete)](#9-rust-atomics)
10. [Linux Kernel Atomic API](#10-linux-kernel-atomic-api)
11. [Lock-Free Data Structures](#11-lock-free-data-structures)
12. [The ABA Problem and Mitigations](#12-the-aba-problem)
13. [Hazard Pointers](#13-hazard-pointers)
14. [Read-Copy-Update (RCU)](#14-read-copy-update-rcu)
15. [Seqlocks](#15-seqlocks)
16. [Wait-Free vs Lock-Free vs Obstruction-Free](#16-progress-guarantees)
17. [Common Pitfalls and Anti-patterns](#17-common-pitfalls)
18. [Testing, Fuzzing, and Tooling](#18-testing-fuzzing-and-tooling)
19. [Security Threat Model](#19-security-threat-model)
20. [Performance and Benchmarking](#20-performance-and-benchmarking)
21. [Architecture Diagrams (ASCII)](#21-architecture-diagrams)
22. [Next 3 Steps](#22-next-3-steps)
23. [References](#23-references)

---

## 1. Why Atomics Exist

### The Fundamental Problem

On a uniprocessor with a single-threaded program, a read-modify-write (RMW) of a variable is safe because no other agent intervenes. On a modern system:

- Multiple CPU cores share a memory subsystem
- Each core has private L1/L2 caches
- Compilers reorder instructions for optimization
- CPUs speculatively execute and reorder memory operations
- Store buffers and load queues decouple execution from memory visibility

Without explicit synchronization, **concurrent RMW sequences are not atomic**:

```
Thread 1: LOAD counter (reads 5)
Thread 2: LOAD counter (reads 5)
Thread 1: ADD 1 → 6, STORE counter
Thread 2: ADD 1 → 6, STORE counter
Result:   counter = 6  (expected 7)
```

This is a **lost update** — a classic race condition. The fix requires the entire LOAD→MODIFY→STORE to appear instantaneous to all observers. That is an **atomic operation**.

### Two Layers of Non-Atomicity

**Layer 1: Compiler reordering.** The compiler is free to reorder loads/stores between variables if it cannot see cross-thread dependencies. A global variable written by one thread may never be "seen" written by another without a barrier, because the compiler may keep the value in a register.

**Layer 2: CPU reordering.** Even if the compiler emits correct instructions, the CPU's memory subsystem reorders memory accesses (store buffers, load-store reordering on ARM/POWER). A write committed to a store buffer is not yet globally visible.

Atomics solve both layers simultaneously.

### Atomicity Granularity

Not all atomics are equal in scope:

| Scope | What it guarantees |
|---|---|
| **Compiler barrier** | No compiler reordering across the barrier |
| **CPU fence** | Drains store buffers, orders memory visibility across cores |
| **Atomic RMW** | Indivisible read-modify-write + implied ordering |
| **Hardware transaction (HTM)** | Speculative multi-word atomicity (TSX/TME) |

---

## 2. CPU Microarchitecture Foundations

### The Modern Out-of-Order Core

```
  Fetch → Decode → Rename → Issue Queue → Execute Units → Commit (ROB)
                                                |
                                         [Load/Store Unit]
                                                |
                                    +-----------+----------+
                                    |                      |
                              [Load Queue]           [Store Buffer]
                                    |                      |
                              L1 D-Cache <----- Store-to-Load Forwarding
```

**Register Renaming (ROB):** The CPU maintains a Reorder Buffer. Instructions execute out-of-order but commit in-order. This is invisible to a single thread but visible across threads via the memory subsystem.

**Store Buffer:** When a STORE instruction executes, the data goes into the store buffer — a FIFO queue between the execute unit and L1 cache. The store is not yet globally visible. The executing thread can read its own store via store-to-load forwarding, but other cores cannot see it yet.

**Load Queue:** Loads are tracked for memory ordering violations. If a younger load executes before an older store to the same address, and the store later drains, the CPU detects the violation and squashes+replays the load.

**Why this matters for atomics:** A plain store to a shared variable may sit in the store buffer for dozens of cycles before becoming globally visible. An atomic store with the right memory order forces the store buffer to drain.

### The Cache Hierarchy

```
Core 0          Core 1          Core 2          Core 3
  |               |               |               |
[L1-I][L1-D]  [L1-I][L1-D]  [L1-I][L1-D]  [L1-I][L1-D]
  |               |               |               |
 [L2]           [L2]           [L2]           [L2]
  |               |               |               |
  +-------+-------+               +-------+-------+
          |                               |
         [L3 (shared, sliced)]           [L3 (shared, sliced)]
                  |                       |
                  +-----------+-----------+
                              |
                         [Memory Controller]
                              |
                           [DRAM]
```

**Cache lines:** The unit of transfer between L1 and L2 is a cache line (typically 64 bytes on x86, 64 bytes on ARM). Atomics operate on sub-cache-line quantities (1, 2, 4, 8 bytes). An atomic operation on a naturally aligned address that fits within a single cache line is inherently indivisible from the cache coherency protocol's perspective on most architectures.

**False sharing:** Two independent variables sharing a cache line cause unnecessary coherency traffic. Critical for atomic performance — put frequently-modified atomics on their own cache lines (pad to 128 bytes to avoid adjacency issues with hardware prefetchers).

---

## 3. Cache Coherency

### Why Coherency is Needed

If Core 0 modifies a cache line and Core 1 reads it, Core 1 must see Core 0's modification. Without a protocol, each core's private cache is inconsistent. Cache coherency protocols ensure that all cores observe a consistent view of memory, even though they have private caches.

### MESI Protocol

The dominant protocol for x86 (Intel) systems. Each cache line is in one of four states:

```
+----------+------------------------------------------------------------+
| State    | Meaning                                                    |
+----------+------------------------------------------------------------+
| Modified | Line is dirty, only this cache has it, must write back     |
| Exclusive| Line is clean, only this cache has it, no write-back needed|
| Shared   | Line is clean, multiple caches may have it (read-only)     |
| Invalid  | Line is not present or stale — must fetch before use       |
+----------+------------------------------------------------------------+
```

**State Transitions:**

```
                         Local Read (Hit)
                    ┌─────────────────────┐
                    ▼                     │
  ┌───────────────────────────────────────┴──────────────────────────┐
  │                       State Machine                              │
  │                                                                  │
  │   ┌─────────┐  Local Write    ┌──────────┐                       │
  │   │ Shared  │───────────────▶ │ Modified │                       │
  │   │   (S)   │◀────────────── │   (M)    │                       │
  │   └────┬────┘  Remote Read    └────┬─────┘                       │
  │        │                          │ Remote Read (write-back)     │
  │        │ Remote Write             │                              │
  │        ▼  (Invalidate)            ▼                              │
  │   ┌─────────┐               ┌──────────┐                        │
  │   │ Invalid │◀──────────────│Exclusive │                        │
  │   │   (I)   │  Remote Write │   (E)    │                        │
  │   └─────────┘               └──────────┘                        │
  └──────────────────────────────────────────────────────────────────┘
```

**For an atomic RMW (e.g., `lock xadd`):**

1. Core requests the cache line in **Exclusive** state (RFO — Request For Ownership)
2. All other copies are invalidated (broadcast on the coherency interconnect)
3. Core performs RMW on the now-exclusive line
4. Line transitions to **Modified**
5. Other cores that want the line must wait for the write-back or snoop the data

This is expensive! An RFO requires a bus transaction and invalidations. On NUMA systems, cross-socket RFOs go through the QPI/UPI or HyperTransport interconnect — roughly 100–300 ns vs ~4 ns for an L1 hit.

### MESIF (Intel)

Intel extended MESI with **Forward (F)**: a designated cache that responds to snoops on behalf of all sharers, reducing snoop responses from O(N) to O(1). The F state is a modified form of S — only one sharer has F at a time.

### MOESI (AMD)

AMD added **Owner (O)**: a cache can hold a dirty line and share it (respond to snoops) without writing back to memory first. Reduces memory write-back traffic on heavy-read workloads.

### The Interconnect

```
Socket 0                           Socket 1
┌──────────────────────────┐      ┌──────────────────────────┐
│ Core0 Core1 Core2 Core3  │      │ Core4 Core5 Core6 Core7  │
│  L1   L1   L1   L1      │      │  L1   L1   L1   L1      │
│  L2   L2   L2   L2      │      │  L2   L2   L2   L2      │
│  ┌────────────────┐      │      │  ┌────────────────┐      │
│  │ L3 (LLC)       │      │      │  │ L3 (LLC)       │      │
│  └────────────────┘      │      │  └────────────────┘      │
│  Memory Controller       │      │  Memory Controller       │
│  DIMM0  DIMM1            │      │  DIMM2  DIMM3            │
└──────────┬───────────────┘      └────────────┬─────────────┘
           │                                   │
           └──────────── QPI/UPI ──────────────┘
```

Cross-socket atomic operations traverse QPI/UPI. This is the primary reason NUMA-aware programming avoids sharing hot atomics across sockets.

---

## 4. Memory Consistency Models

A **memory consistency model** defines what values a load is allowed to return given a set of stores from all threads. It is the contract between the hardware and the programmer.

### Sequential Consistency (SC)

The ideal model (Lamport, 1979). All operations appear to execute in a global total order consistent with each thread's program order. No reordering at all. Very slow — prohibits store buffers, load forwarding across barriers, etc.

```
Thread 1:    Thread 2:
x = 1        y = 1
r1 = y       r2 = x

SC guarantees: NOT possible to observe r1=0 AND r2=0 simultaneously.
```

No modern high-performance CPU implements SC by default.

### Total Store Order (TSO) — x86

x86's model. Writes are not reordered with other writes (total store order). Reads are not reordered with other reads. BUT: a write may be delayed in the store buffer, so a read by another core may not see it immediately (write→read reordering is allowed). A core always sees its own writes immediately (store-to-load forwarding).

**What x86 can reorder:** Store → Load (a write to X followed by a read from Y may be observed in reverse order by another core, because the write is in the store buffer while the read goes directly to cache).

**What x86 cannot reorder:**
- Load → Load (reads are in program order)
- Store → Store (writes are in program order)
- Load → Store (a read before a write stays before the write)

TSO is relatively strong. This is why a lot of C code written without explicit memory orders "works" on x86 but breaks on ARM.

### Weak/Relaxed Ordering — ARM, POWER, RISC-V

ARM and POWER allow almost all reorderings unless explicitly prevented with barriers:
- Load → Load reordering allowed
- Load → Store reordering allowed
- Store → Store reordering allowed
- Store → Load reordering allowed

POWER additionally allows non-multi-copy-atomic stores (a write by Core A may be visible to Core B before it is visible to Core C).

ARM v8+ (AArch64) is multi-copy atomic but still allows extensive reordering.

### The C/C++ and Rust Memory Model

C11, C++11, and Rust adopt an abstract memory model based on the work of Boehm & Adve. It defines:

- **Happens-before** relationship (HB): if operation A happens-before B, A's effects are visible to B
- **Synchronizes-with** (SW): an atomic store with Release **synchronizes-with** a load from the same location with Acquire that observes the stored value
- **Data race**: two unsynchronized conflicting accesses (at least one is a write) — undefined behavior in C/C++/Rust

The model is deliberately agnostic of hardware — it describes allowed behaviors, not mechanisms. The compiler maps the abstract model to hardware instructions.

---

## 5. Memory Barriers and Fences

A memory barrier (fence) is a CPU instruction (or compiler directive) that constrains the reordering of memory operations.

### Barrier Types

| Barrier | Meaning |
|---|---|
| **Load fence (lfence)** | All loads before the fence complete before any load after |
| **Store fence (sfence)** | All stores before the fence are globally visible before any store after |
| **Full fence (mfence)** | Both load and store fences combined |
| **Acquire fence** | All memory ops after the fence cannot move before it |
| **Release fence** | All memory ops before the fence cannot move after it |
| **Compiler barrier** | Prevents compiler reordering only, no CPU instruction emitted |

### x86 Instructions

```asm
; Compiler barrier only (no CPU instruction)
asm volatile("" ::: "memory");

; Load fence — prevents Load/Load reordering across this point
lfence

; Store fence — ensures all prior stores are globally visible
sfence

; Full fence — Load+Store ordering in both directions
mfence

; LOCK prefix — implies full fence + atomicity on the addressed memory
lock xadd [rdi], eax

; XCHG with memory — implies LOCK prefix automatically on x86
xchg [rdi], eax
```

On x86, because TSO is already strong, `lfence` and `sfence` are rarely needed in application code. `mfence` is used for preventing store-load reordering. Most atomic operations with LOCK prefix act as full fences.

### ARM Instructions

ARM has a richer barrier vocabulary:

```asm
; Data Memory Barrier — full barrier on all memory types
dmb ish          ; Inner Shareable domain (normal operation)
dmb ishld        ; Load-only barrier
dmb ishst        ; Store-only barrier

; Data Synchronization Barrier — stronger: waits for all memory ops to complete
dsb ish

; Instruction Synchronization Barrier — flushes pipeline (for self-modifying code)
isb

; Load-Acquire (ldar): load with acquire semantics
ldar x0, [x1]

; Store-Release (stlr): store with release semantics
stlr x0, [x1]
```

ARMv8.3+ adds LDAPR (load-acquire RCpc — Release Consistency processor-consistent) which is weaker than full acquire but sufficient for many patterns, with better performance.

### POWER Instructions

POWER has the most complex barrier set:

```asm
; Lightweight sync (lwsync) — prevents all reorderings except store→load
lwsync

; Full sync — prevents all reorderings including store→load
sync

; isync — instruction synchronization (like ARM isb)
isync

; eieio — for device I/O ordering (legacy)
eieio
```

### Compiler-Only Barrier in C

```c
/* GCC/Clang: prevents compiler reordering, no CPU instruction */
asm volatile("" ::: "memory");

/* Equivalent: signal fence in C11 */
atomic_signal_fence(memory_order_seq_cst);
```

---

## 6. ISA-Level Atomic Instructions

### x86/x86-64

x86 provides atomicity through:

**1. The LOCK prefix** — makes the following RMW instruction atomic. It asserts the LOCK# signal on the memory bus (or uses cache locking for cached lines), preventing any other agent from accessing the addressed memory until the instruction completes.

```asm
lock xchg  [mem], reg      ; atomic exchange
lock xadd  [mem], reg      ; atomic fetch-add (reg gets old value, mem gets mem+reg)
lock cmpxchg [mem], reg    ; atomic CAS: if mem==rax, mem←reg, else rax←mem
lock cmpxchg8b [mem]       ; 64-bit CAS on 32-bit mode
lock cmpxchg16b [mem]      ; 128-bit double-wide CAS (DCAS)
lock inc   [mem]           ; atomic increment
lock dec   [mem]           ; atomic decrement
lock add   [mem], imm      ; atomic add
lock and/or/xor [mem], reg ; atomic bitwise ops
lock bts/btr/btc [mem], reg ; atomic bit test-and-set/reset/complement
```

**CMPXCHG in detail:**
```
Inputs:  rax = expected, rdx:rax for 128-bit, [mem] = location, reg = desired
Operation:
  if [mem] == rax:
      ZF = 1
      [mem] = reg  (success: store desired)
  else:
      ZF = 0
      rax = [mem]  (failure: load current into rax for retry)
```

**2. XCHG** — always has an implicit LOCK (even without the prefix).

**3. CMPXCHG8B / CMPXCHG16B** — double-width CAS. CMPXCHG16B requires the address to be 16-byte aligned. Used for tagged pointers and the classic lock-free node reclamation workaround for ABA.

**PAUSE instruction** — in spin-wait loops, PAUSE hints to the CPU that it is in a spin loop. Reduces power consumption and prevents memory order machine clears (mis-speculation penalties). Always use PAUSE in spinlocks:

```asm
spin:
    pause
    cmp [lock], 0
    jne spin
```

### ARM (AArch64)

ARM uses a different approach — exclusive monitors rather than bus-locking:

**Load-Exclusive / Store-Exclusive (LDXR/STXR):**

```asm
; Load-exclusive: marks the address in the exclusive monitor
ldxr x0, [x1]         ; x0 = *x1, exclusive monitor set

; ... modify x0 ...

; Store-exclusive: succeeds only if monitor is still set
stxr w2, x0, [x1]     ; if monitor ok: *x1 = x0, w2=0 (success)
                       ; if monitor cleared: w2=1 (failure, retry)

cbnz w2, retry        ; if failed, retry
```

The **exclusive monitor** is a per-CPU hardware register that tracks one address. Any intervening store to that address (by another core, or even a context switch) clears the monitor, causing STXR to fail. This is **LL/SC (Load-Linked / Store-Conditional)**.

**Load-Acquire / Store-Release (LDAR/STLR):**

```asm
; Load with acquire semantics — no loads/stores after can reorder before
ldar x0, [x1]

; Store with release semantics — no loads/stores before can reorder after
stlr x0, [x1]
```

**Combining exclusives with ordering:**

```asm
ldaxr x0, [x1]        ; Load-Acquire-Exclusive (LDAR + LDXR combined)
; ... compute new value in x2 ...
stlxr w3, x2, [x1]    ; Store-Release-Exclusive
cbnz w3, retry
```

LDAXR/STLXR is the ARM equivalent of `lock cmpxchg` with acquire/release ordering.

**ARMv8.1-A Large System Extensions (LSE):**

ARMv8.1 added native atomic instructions that do not require LL/SC loops:

```asm
; Atomic add — no retry loop needed
ldadd x0, x1, [x2]    ; x1 += *x2, x0 = old value

; Atomic compare-and-swap
cas x0, x1, [x2]       ; if *x2==x0: *x2=x1; else x0=*x2

; Atomic bit operations
ldset x0, x1, [x2]     ; atomic OR
ldclr x0, x1, [x2]     ; atomic AND-NOT (clear bits)
ldeor x0, x1, [x2]     ; atomic XOR
```

LSE atomics are much faster than LL/SC on contended workloads — no retry loops, and they use hardware-level bus transactions. Linux compiles with `+lse` when targeting ARMv8.1+.

### RISC-V

RISC-V uses the **A extension (Atomics)**:

```asm
; LR/SC — similar to ARM
lr.w  t0, (a0)          ; load-reserved: t0 = *a0
sc.w  t1, t2, (a0)      ; store-conditional: if reserved, *a0=t2, t1=0

; Atomic memory operations (AMO)
amoadd.w  t0, t1, (a0) ; t0=*a0, *a0+=t1 (atomic)
amoswap.w t0, t1, (a0) ; t0=*a0, *a0=t1  (atomic swap)
amoor.w   t0, t1, (a0) ; atomic OR
amoand.w  t0, t1, (a0) ; atomic AND
amoxor.w  t0, t1, (a0) ; atomic XOR
amomax.w  t0, t1, (a0) ; atomic max (signed)

; Ordering suffixes: .aq (acquire), .rl (release), .aqrl (both)
amoadd.w.aq  t0, t1, (a0)   ; acquire
amoadd.w.rl  t0, t1, (a0)   ; release
amoadd.w.aqrl t0, t1, (a0)  ; full fence
```

---

## 7. C11 Atomics

C11 introduced `<stdatomic.h>`, providing a portable atomic API. C++11 provides `<atomic>`.

### The Memory Order Enum

```c
typedef enum memory_order {
    memory_order_relaxed,   // No ordering constraints — just atomicity
    memory_order_consume,   // Deprecated/broken in practice (use acquire)
    memory_order_acquire,   // Acquire fence: prevents loads/stores after from moving before
    memory_order_release,   // Release fence: prevents loads/stores before from moving after
    memory_order_acq_rel,   // Both acquire and release (for RMW operations)
    memory_order_seq_cst,   // Sequential consistency — total global order
} memory_order;
```

**Mental model for acquire/release:**

```
Thread 1 (producer):           Thread 2 (consumer):
data = compute();              while (!flag.load(acquire)) {}
flag.store(1, release);        use(data);  // safe: sees compute() result

The release store "publishes" all prior writes.
The acquire load "subscribes" to all published writes.
Everything before the release is visible after the acquire.
```

**memory_order_relaxed** — atomicity only, no ordering. Useful for counters where you only need the final count to be accurate, not for communication between threads:

```c
// Correct: just counting, no communication
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);
```

**memory_order_seq_cst** — the default. Generates a full fence on x86 (MFENCE or LOCK prefix), and full DMB on ARM. Most expensive. Use only when you genuinely need a total order across all seq_cst operations in the program.

**memory_order_consume** — was intended for dependent loads (pointer reads where the loaded value is used to index another load). The hardware data dependency implicitly orders this without a fence on most architectures. In practice, no compiler implements consume correctly — all promote it to acquire. Avoid.

### Atomic Types

```c
#include <stdatomic.h>

// Primitive atomic types
atomic_bool         // _Atomic _Bool
atomic_char         // _Atomic char
atomic_int          // _Atomic int
atomic_uint         // _Atomic unsigned int
atomic_long         // _Atomic long
atomic_ulong        // _Atomic unsigned long
atomic_llong        // _Atomic long long
atomic_ullong       // _Atomic unsigned long long
atomic_intptr_t     // _Atomic intptr_t
atomic_uintptr_t    // _Atomic uintptr_t
atomic_size_t       // _Atomic size_t
atomic_ptrdiff_t    // _Atomic ptrdiff_t

// Generic: apply _Atomic to any type
_Atomic(struct Foo) foo;  // Only lock-free if sizeof(Foo) is 1,2,4,8 (or 16 w/ CMPXCHG16B)
```

**Lock-free check:**

```c
// Compile-time: ATOMIC_INT_LOCK_FREE, ATOMIC_LONG_LOCK_FREE, etc.
// Values: 0=never, 1=sometimes (depends on alignment), 2=always

// Runtime:
if (atomic_is_lock_free(&my_atomic)) {
    // guaranteed no hidden mutex
}
```

### Complete C11 API

```c
/* INITIALIZATION */
atomic_int x = ATOMIC_VAR_INIT(0);         // Static initialization
atomic_init(&x, 0);                         // Dynamic initialization

/* LOAD */
int val = atomic_load(&x);                          // seq_cst
int val = atomic_load_explicit(&x, memory_order_acquire);

/* STORE */
atomic_store(&x, 42);                               // seq_cst
atomic_store_explicit(&x, 42, memory_order_release);

/* EXCHANGE */
int old = atomic_exchange(&x, 42);                  // seq_cst
int old = atomic_exchange_explicit(&x, 42, memory_order_acq_rel);

/* COMPARE-AND-EXCHANGE (CAS) */
// Strong CAS: guaranteed to succeed if *obj == *expected
// Weak CAS: may spuriously fail even if equal (LL/SC architectures)
int expected = 5;
bool ok = atomic_compare_exchange_strong(&x, &expected, 10);
// if ok: x was 5, now 10. expected unchanged.
// if !ok: x was not 5. expected is updated to current x value.

bool ok = atomic_compare_exchange_weak(&x, &expected, 10);
// May fail spuriously — must be in a loop

// Explicit ordering variants
bool ok = atomic_compare_exchange_strong_explicit(
    &x, &expected, 10,
    memory_order_acq_rel,    // success ordering
    memory_order_acquire     // failure ordering (must be <= success)
);

/* FETCH-MODIFY-RETURN operations (return OLD value) */
int old = atomic_fetch_add(&x, 1);          // old = x; x += 1
int old = atomic_fetch_sub(&x, 1);          // old = x; x -= 1
int old = atomic_fetch_and(&x, mask);       // old = x; x &= mask
int old = atomic_fetch_or(&x,  mask);       // old = x; x |= mask
int old = atomic_fetch_xor(&x, mask);       // old = x; x ^= mask

// Explicit ordering:
int old = atomic_fetch_add_explicit(&x, 1, memory_order_relaxed);

/* FENCES (standalone) */
atomic_thread_fence(memory_order_release);  // release fence without atomic op
atomic_thread_fence(memory_order_acquire);  // acquire fence
atomic_thread_fence(memory_order_seq_cst);  // full fence (MFENCE on x86)

// Signal fence: only prevents compiler reordering (for signal handlers)
atomic_signal_fence(memory_order_seq_cst);

/* ATOMIC FLAG (guaranteed lock-free) */
atomic_flag flag = ATOMIC_FLAG_INIT;        // initialized to clear
bool was_set = atomic_flag_test_and_set(&flag);   // set and return old
atomic_flag_clear(&flag);                          // clear
// Explicit:
bool was_set = atomic_flag_test_and_set_explicit(&flag, memory_order_acquire);
atomic_flag_clear_explicit(&flag, memory_order_release);
```

### Complete C Example: Spinlock

```c
// spinlock.h
#ifndef SPINLOCK_H
#define SPINLOCK_H

#include <stdatomic.h>
#include <stdbool.h>

typedef struct {
    atomic_flag flag;
} spinlock_t;

#define SPINLOCK_INIT { ATOMIC_FLAG_INIT }

static inline void spin_lock(spinlock_t *lock) {
    while (atomic_flag_test_and_set_explicit(&lock->flag, memory_order_acquire)) {
        // Spin: CPU hint to reduce power and prevent memory order machine clears
        #if defined(__x86_64__) || defined(__i386__)
            __builtin_ia32_pause();
        #elif defined(__aarch64__)
            asm volatile("yield" ::: "memory");
        #endif
    }
}

static inline void spin_unlock(spinlock_t *lock) {
    atomic_flag_clear_explicit(&lock->flag, memory_order_release);
}

static inline bool spin_trylock(spinlock_t *lock) {
    return !atomic_flag_test_and_set_explicit(&lock->flag, memory_order_acquire);
}

#endif
```

### Complete C Example: Lock-Free Stack

```c
// lockfree_stack.c
// Michael-Scott lock-free stack using CAS
// WARNING: ABA-prone without hazard pointers or tagged pointers

#include <stdatomic.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

// Tagged pointer to solve ABA on 16-byte-CAS capable systems
typedef struct {
    void    *ptr;
    uint64_t tag;
} tagged_ptr_t;

typedef struct node {
    struct node *next;
    void        *data;
} node_t;

typedef struct {
    _Atomic(tagged_ptr_t) head;  // Tagged to prevent ABA
} lf_stack_t;

void lf_stack_init(lf_stack_t *s) {
    tagged_ptr_t zero = {NULL, 0};
    atomic_store_explicit(&s->head, zero, memory_order_relaxed);
}

void lf_stack_push(lf_stack_t *s, void *data) {
    node_t *n = malloc(sizeof(*n));
    n->data = data;

    tagged_ptr_t old_head = atomic_load_explicit(&s->head, memory_order_relaxed);
    tagged_ptr_t new_head;
    do {
        n->next = old_head.ptr;
        new_head.ptr = n;
        new_head.tag = old_head.tag + 1;
    } while (!atomic_compare_exchange_weak_explicit(
        &s->head,
        &old_head,
        new_head,
        memory_order_release,    // success: publish the node
        memory_order_relaxed     // failure: just reload head
    ));
}

void *lf_stack_pop(lf_stack_t *s) {
    tagged_ptr_t old_head = atomic_load_explicit(&s->head, memory_order_acquire);
    tagged_ptr_t new_head;

    while (old_head.ptr != NULL) {
        new_head.ptr = old_head.ptr->next;
        new_head.tag = old_head.tag + 1;

        if (atomic_compare_exchange_weak_explicit(
            &s->head,
            &old_head,
            new_head,
            memory_order_acq_rel,
            memory_order_acquire
        )) {
            void *data = old_head.ptr->data;
            free(old_head.ptr);   // UNSAFE without hazard pointers!
            return data;
        }
        // old_head was updated by CAS failure — retry
    }
    return NULL;  // empty
}
```

**Note:** The `free(old_head.ptr)` above is unsafe in the presence of concurrent pops. A thread may be reading `old_head.ptr->next` while another thread has already freed the node. This requires hazard pointers or epoch-based reclamation — covered in Section 13.

### Complete C Example: SPSC Ring Buffer (Lock-Free)

```c
// spsc_ringbuf.c
// Single-Producer Single-Consumer ring buffer
// Can use relaxed atomics because SPSC has guaranteed ordering

#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

#define RING_SIZE 1024  // Must be power of 2
#define RING_MASK (RING_SIZE - 1)

typedef struct {
    _Alignas(64) atomic_size_t head;   // Written by producer, read by consumer
    _Alignas(64) atomic_size_t tail;   // Written by consumer, read by producer
    void *buf[RING_SIZE];
} spsc_ring_t;

void spsc_init(spsc_ring_t *r) {
    atomic_init(&r->head, 0);
    atomic_init(&r->tail, 0);
    memset(r->buf, 0, sizeof(r->buf));
}

// Producer: returns true on success
bool spsc_push(spsc_ring_t *r, void *item) {
    size_t head = atomic_load_explicit(&r->head, memory_order_relaxed);
    size_t tail = atomic_load_explicit(&r->tail, memory_order_acquire);

    if (head - tail >= RING_SIZE) {
        return false;  // full
    }

    r->buf[head & RING_MASK] = item;

    // Release: ensure buf write is visible before head update
    atomic_store_explicit(&r->head, head + 1, memory_order_release);
    return true;
}

// Consumer: returns item or NULL if empty
void *spsc_pop(spsc_ring_t *r) {
    size_t tail = atomic_load_explicit(&r->tail, memory_order_relaxed);
    size_t head = atomic_load_explicit(&r->head, memory_order_acquire);

    if (tail == head) {
        return NULL;  // empty
    }

    void *item = r->buf[tail & RING_MASK];

    // Release: ensure item read before tail update
    atomic_store_explicit(&r->tail, tail + 1, memory_order_release);
    return item;
}
```

**Why this is correct:** Producer owns `head`; consumer owns `tail`. The acquire on reading the other's index establishes happens-before with the release on writing it. No CAS needed — the single writer/single reader invariant means no contention.

---

## 8. GCC Built-ins and Legacy Patterns

Before C11, GCC provided `__sync_*` and `__atomic_*` built-ins. Understanding these is essential for reading kernel and legacy code.

### `__sync_*` (Legacy, avoid in new code)

```c
// These imply full sequential consistency (all barriers)
T   __sync_fetch_and_add(T *ptr, T val);     // returns OLD
T   __sync_fetch_and_sub(T *ptr, T val);
T   __sync_fetch_and_and(T *ptr, T val);
T   __sync_fetch_and_or(T *ptr, T val);
T   __sync_fetch_and_xor(T *ptr, T val);
T   __sync_fetch_and_nand(T *ptr, T val);

T   __sync_add_and_fetch(T *ptr, T val);     // returns NEW (deprecated)
bool __sync_bool_compare_and_swap(T *ptr, T old, T new);  // returns success
T    __sync_val_compare_and_swap(T *ptr, T old, T new);   // returns old value

void __sync_synchronize();                   // Full memory barrier
```

### `__atomic_*` (GCC 4.7+, preferred over `__sync_*`)

These map directly to the C11 model and take explicit memory order arguments:

```c
// Memory orders: __ATOMIC_RELAXED, __ATOMIC_CONSUME, __ATOMIC_ACQUIRE,
//                __ATOMIC_RELEASE, __ATOMIC_ACQ_REL, __ATOMIC_SEQ_CST

T    __atomic_load_n(T *ptr, int memorder);
void __atomic_load(T *ptr, T *ret, int memorder);

void __atomic_store_n(T *ptr, T val, int memorder);
void __atomic_store(T *ptr, T *val, int memorder);

T    __atomic_exchange_n(T *ptr, T val, int memorder);

bool __atomic_compare_exchange_n(T *ptr, T *expected, T desired,
                                 bool weak, int success_mo, int fail_mo);

T    __atomic_fetch_add(T *ptr, T val, int memorder);
T    __atomic_fetch_sub(T *ptr, T val, int memorder);
T    __atomic_fetch_and(T *ptr, T val, int memorder);
T    __atomic_fetch_or(T *ptr, T val, int memorder);
T    __atomic_fetch_xor(T *ptr, T val, int memorder);
T    __atomic_fetch_nand(T *ptr, T val, int memorder);

// Add-and-return-new (less common)
T    __atomic_add_fetch(T *ptr, T val, int memorder);

void __atomic_thread_fence(int memorder);
void __atomic_signal_fence(int memorder);
bool __atomic_is_lock_free(size_t size, void *ptr);
```

### Volatile — What It Does and Doesn't Do

`volatile` in C:
- Prevents the compiler from caching the value in a register (re-reads from memory on every access)
- Prevents the compiler from optimizing away reads/writes
- Does NOT prevent CPU reordering
- Does NOT provide atomicity
- Is NOT a substitute for atomics

`volatile` is correct for memory-mapped I/O (MMIO) registers, where the hardware may change the value between reads. It is NOT correct for inter-thread communication.

**Kernel exception:** The Linux kernel uses `volatile` in specific macros (like `READ_ONCE` / `WRITE_ONCE`) combined with explicit barriers. This is not standard C volatile semantics — it is a carefully controlled pattern with additional asm barriers.

---

## 9. Rust Atomics

Rust's `std::sync::atomic` module provides the safest atomic API. The type system prevents data races at compile time (no `Sync` for non-atomic shared references to mutable data).

### Atomic Types

```rust
use std::sync::atomic::{
    AtomicBool,
    AtomicI8, AtomicI16, AtomicI32, AtomicI64, AtomicIsize,
    AtomicU8, AtomicU16, AtomicU32, AtomicU64, AtomicUsize,
    AtomicPtr<T>,
    Ordering,
    compiler_fence, fence,
};
```

### Ordering Enum

```rust
pub enum Ordering {
    Relaxed,    // Atomicity only
    Acquire,    // Load barrier
    Release,    // Store barrier
    AcqRel,     // Both (for RMW)
    SeqCst,     // Total order (default, most expensive)
}
```

### Complete Rust API

```rust
use std::sync::atomic::{AtomicI32, Ordering};

let x = AtomicI32::new(0);

// LOAD
let val: i32 = x.load(Ordering::Acquire);
let val: i32 = x.load(Ordering::SeqCst);

// STORE
x.store(42, Ordering::Release);
x.store(42, Ordering::SeqCst);

// SWAP (exchange)
let old: i32 = x.swap(42, Ordering::AcqRel);

// COMPARE-AND-SWAP
// compare_exchange: strong (no spurious failure)
match x.compare_exchange(
    5,                  // expected
    10,                 // desired
    Ordering::AcqRel,  // success ordering
    Ordering::Acquire, // failure ordering
) {
    Ok(prev) => { /* prev == 5, x is now 10 */ }
    Err(actual) => { /* x was not 5, actual is current value */ }
}

// compare_exchange_weak: may spuriously fail (use in loops)
let mut expected = 5i32;
loop {
    match x.compare_exchange_weak(expected, expected + 1, Ordering::AcqRel, Ordering::Relaxed) {
        Ok(_) => break,
        Err(current) => expected = current,
    }
}

// FETCH-MODIFY (return OLD value)
let old: i32 = x.fetch_add(1, Ordering::Relaxed);
let old: i32 = x.fetch_sub(1, Ordering::Relaxed);
let old: i32 = x.fetch_and(0xFF, Ordering::Relaxed);
let old: i32 = x.fetch_or(0x01, Ordering::Relaxed);
let old: i32 = x.fetch_xor(0x01, Ordering::Relaxed);
let old: i32 = x.fetch_max(10, Ordering::Relaxed);  // atomic max
let old: i32 = x.fetch_min(10, Ordering::Relaxed);  // atomic min
let old: i32 = x.fetch_nand(mask, Ordering::Relaxed);

// Unsafely get a mutable reference (only safe if exclusive access is guaranteed)
let mutable_ref: &mut i32 = x.get_mut();

// Convert from/to raw integer (bypasses atomicity - only for initialization/teardown)
let raw: i32 = x.into_inner();

// STANDALONE FENCES
fence(Ordering::SeqCst);          // Full CPU fence
compiler_fence(Ordering::Release); // Compiler-only, no CPU instruction
```

### Rust: Spinlock Implementation

```rust
// spinlock.rs
use std::cell::UnsafeCell;
use std::ops::{Deref, DerefMut};
use std::sync::atomic::{AtomicBool, Ordering, fence};
use std::hint;

pub struct SpinLock<T> {
    locked: AtomicBool,
    data:   UnsafeCell<T>,
}

// Safety: SpinLock provides mutual exclusion, so T need not be Sync
unsafe impl<T: Send> Sync for SpinLock<T> {}
unsafe impl<T: Send> Send for SpinLock<T> {}

pub struct SpinGuard<'a, T> {
    lock: &'a SpinLock<T>,
}

impl<T> SpinLock<T> {
    pub const fn new(data: T) -> Self {
        SpinLock {
            locked: AtomicBool::new(false),
            data: UnsafeCell::new(data),
        }
    }

    pub fn lock(&self) -> SpinGuard<T> {
        // Outer loop: backoff before trying TAS
        loop {
            // Inner loop: spin on load (avoids excessive cache invalidation from TAS)
            while self.locked.load(Ordering::Relaxed) {
                hint::spin_loop(); // PAUSE on x86, YIELD on ARM
            }
            // Try to acquire with TAS
            if self.locked
                .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_ok()
            {
                return SpinGuard { lock: self };
            }
        }
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
        // Safety: we hold the lock
        unsafe { &*self.lock.data.get() }
    }
}

impl<T> DerefMut for SpinGuard<'_, T> {
    fn deref_mut(&mut self) -> &mut T {
        // Safety: we hold the lock exclusively
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<T> Drop for SpinGuard<'_, T> {
    fn drop(&mut self) {
        self.lock.locked.store(false, Ordering::Release);
    }
}
```

### Rust: Lock-Free Stack with Epoch-Based Reclamation (crossbeam)

```rust
// lf_stack.rs — using crossbeam-epoch for safe memory reclamation
use crossbeam_epoch::{self as epoch, Atomic, Owned, Shared};
use std::sync::atomic::Ordering;

pub struct Node<T> {
    data: T,
    next: Atomic<Node<T>>,
}

pub struct TreiberStack<T> {
    head: Atomic<Node<T>>,
}

impl<T> TreiberStack<T> {
    pub fn new() -> Self {
        TreiberStack { head: Atomic::null() }
    }

    pub fn push(&self, data: T) {
        let guard = epoch::pin();
        let node = Owned::new(Node {
            data,
            next: Atomic::null(),
        });

        loop {
            let head = self.head.load(Ordering::Relaxed, &guard);
            node.next.store(head, Ordering::Relaxed);

            match self.head.compare_exchange(
                head,
                node,
                Ordering::Release,
                Ordering::Relaxed,
                &guard,
            ) {
                Ok(_) => break,
                Err(e) => {
                    // CAS failed; e.new is the node we tried to insert
                    // crossbeam returns ownership back to us
                    let _ = e;
                    // In real usage, reconstruct from e.new
                    break; // simplified for illustration
                }
            }
        }
    }

    pub fn pop(&self) -> Option<T> {
        let guard = epoch::pin();
        loop {
            let head = self.head.load(Ordering::Acquire, &guard);
            match unsafe { head.as_ref() } {
                None => return None,
                Some(node) => {
                    let next = node.next.load(Ordering::Relaxed, &guard);
                    if self.head
                        .compare_exchange(head, next, Ordering::Release, Ordering::Relaxed, &guard)
                        .is_ok()
                    {
                        // Safe to defer deallocation; epoch GC handles it
                        unsafe {
                            guard.defer_destroy(head);
                            return Some(std::ptr::read(&node.data));
                        }
                    }
                }
            }
        }
    }
}

impl<T> Drop for TreiberStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}
```

### Rust: SPSC Ring Buffer

```rust
// spsc.rs — cache-line padded, relaxed atomics, zero unsafe in public API
use std::sync::atomic::{AtomicUsize, Ordering};
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;

const SIZE: usize = 1024; // power of 2
const MASK: usize = SIZE - 1;

#[repr(C)]
pub struct SpscRing<T> {
    #[repr(align(64))]
    head: AtomicUsize,              // producer-owned
    _pad1: [u8; 64 - 8],
    #[repr(align(64))]
    tail: AtomicUsize,              // consumer-owned
    _pad2: [u8; 64 - 8],
    buf: [UnsafeCell<MaybeUninit<T>>; SIZE],
}

unsafe impl<T: Send> Send for SpscRing<T> {}
unsafe impl<T: Send> Sync for SpscRing<T> {}

impl<T> SpscRing<T> {
    pub fn new() -> Box<Self> {
        // Use box to avoid stack overflow for large SIZE
        unsafe {
            let layout = std::alloc::Layout::new::<Self>();
            let ptr = std::alloc::alloc_zeroed(layout) as *mut Self;
            // Initialize atomics
            (*ptr).head = AtomicUsize::new(0);
            (*ptr).tail = AtomicUsize::new(0);
            Box::from_raw(ptr)
        }
    }

    /// Producer: push item. Returns false if full.
    pub fn push(&self, item: T) -> bool {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        if head.wrapping_sub(tail) >= SIZE {
            return false;
        }
        unsafe {
            (*self.buf[head & MASK].get()).write(item);
        }
        self.head.store(head.wrapping_add(1), Ordering::Release);
        true
    }

    /// Consumer: pop item. Returns None if empty.
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        if tail == head {
            return None;
        }
        let item = unsafe { (*self.buf[tail & MASK].get()).assume_init_read() };
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        Some(item)
    }
}
```

### Rust: AtomicPtr Usage

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

// AtomicPtr<T> is for raw pointer manipulation
// Always pair with a safe reclamation strategy

let ptr: AtomicPtr<u32> = AtomicPtr::new(ptr::null_mut());

// Store a heap-allocated value
let boxed = Box::new(42u32);
ptr.store(Box::into_raw(boxed), Ordering::Release);

// Load and use
let raw = ptr.load(Ordering::Acquire);
if !raw.is_null() {
    // Safety: must ensure the pointer is still valid (use epoch/hazard pointers)
    let val = unsafe { *raw };
    println!("{}", val);
}

// Swap (returns old pointer — you own the old allocation)
let new_val = Box::into_raw(Box::new(100u32));
let old_raw = ptr.swap(new_val, Ordering::AcqRel);
if !old_raw.is_null() {
    unsafe { drop(Box::from_raw(old_raw)); }
}
```

---

## 10. Linux Kernel Atomic API

The Linux kernel has its own atomic infrastructure, architecture-specific implementations, and an extensive set of higher-level synchronization primitives built on top.

### Kernel Atomic Types

```c
// include/linux/atomic.h and arch/x86/include/asm/atomic.h

// 32-bit signed atomic integer
typedef struct { int counter; } atomic_t;

// 64-bit signed atomic integer
typedef struct { s64 counter; } atomic64_t;

// Long-width atomic (pointer-sized)
typedef struct { long counter; } atomic_long_t;
```

### 32-bit Operations (`atomic_t`)

```c
/* INITIALIZATION */
atomic_t v = ATOMIC_INIT(0);

/* READ (no ordering guarantee on its own) */
int val = atomic_read(&v);           // Equivalent to ACCESS_ONCE
int val = atomic_read_acquire(&v);   // With acquire semantics

/* SET */
atomic_set(&v, 42);
atomic_set_release(&v, 42);

/* ADD/SUB */
atomic_add(5, &v);
atomic_sub(3, &v);

/* INC/DEC */
atomic_inc(&v);
atomic_dec(&v);

/* Returns-new-value variants */
int new = atomic_inc_return(&v);     // ++v (atomic)
int new = atomic_dec_return(&v);     // --v
int new = atomic_add_return(5, &v);
int new = atomic_sub_return(3, &v);

/* Returns-old-value variants (fetch-op) */
int old = atomic_fetch_add(5, &v);
int old = atomic_fetch_sub(3, &v);
int old = atomic_fetch_and(mask, &v);
int old = atomic_fetch_or(mask, &v);
int old = atomic_fetch_xor(mask, &v);

/* Bitwise (no return) */
atomic_and(mask, &v);
atomic_or(mask, &v);
atomic_xor(mask, &v);

/* Test-and-set patterns (return bool) */
bool zero = atomic_dec_and_test(&v);    // dec, return (result == 0)
bool zero = atomic_inc_and_test(&v);    // inc, return (result == 0)
bool neg  = atomic_add_negative(n, &v); // add, return (result < 0)

/* EXCHANGE */
int old = atomic_xchg(&v, 42);               // atomic exchange
int old = atomic_cmpxchg(&v, old_val, new_val); // CAS, returns old value

/* Ordered variants (explicit acquire/release) */
int old = atomic_fetch_add_acquire(5, &v);
int old = atomic_fetch_add_release(5, &v);

/* Relaxed variants (no barrier) */
atomic_add_relaxed(5, &v);
int old = atomic_fetch_add_relaxed(5, &v);
```

### 64-bit Operations (`atomic64_t`)

```c
// Same API prefix with atomic64_
atomic64_t v64 = ATOMIC64_INIT(0);
s64 val = atomic64_read(&v64);
atomic64_set(&v64, 100LL);
s64 old = atomic64_fetch_add(1, &v64);
s64 old = atomic64_cmpxchg(&v64, expected, desired);
// etc.
```

### Kernel Memory Barriers

```c
// include/linux/compiler.h and include/asm-generic/barrier.h

/* COMPILER BARRIERS */
barrier();              // Prevents compiler reordering; no CPU instruction
                        // Equivalent to: asm volatile("" ::: "memory");

/* CPU MEMORY BARRIERS */
mb();                   // Full memory barrier (both read and write)
rmb();                  // Read memory barrier (prevents Load/Load reordering)
wmb();                  // Write memory barrier (prevents Store/Store reordering)

/* SMP-aware barriers (no-op on uniprocessor builds) */
smp_mb();               // Full barrier on SMP; no-op on UP
smp_rmb();              // Read barrier on SMP
smp_wmb();              // Write barrier on SMP

/* Acquire/release barriers */
smp_mb__before_atomic(); // Full barrier before atomic op
smp_mb__after_atomic();  // Full barrier after atomic op

/* READ_ONCE / WRITE_ONCE — prevents compiler from merging/splitting accesses */
int val = READ_ONCE(shared_variable);   // volatile load + compiler barrier
WRITE_ONCE(shared_variable, 42);        // volatile store + compiler barrier

/* DMA barriers (for device driver memory ordering) */
dma_rmb();
dma_wmb();

/* smp_load_acquire / smp_store_release (C11-style) */
int val = smp_load_acquire(&x);
smp_store_release(&x, 42);
```

**READ_ONCE / WRITE_ONCE** are critical in the kernel. They prevent the compiler from:
- Tearing multi-byte accesses into smaller pieces
- Merging two loads into one (might miss a change)
- Speculating away a load (assuming value didn't change)

They do not provide ordering between CPUs — that requires smp_* barriers.

### Kernel Atomic Bit Operations

```c
// include/linux/bitops.h — operate on unsigned long arrays

/* Set/clear/toggle */
void set_bit(int nr, volatile unsigned long *addr);
void clear_bit(int nr, volatile unsigned long *addr);
void change_bit(int nr, volatile unsigned long *addr);

/* Test-and-set/clear/change (return old bit value) */
int test_and_set_bit(int nr, volatile unsigned long *addr);
int test_and_clear_bit(int nr, volatile unsigned long *addr);
int test_and_change_bit(int nr, volatile unsigned long *addr);

/* Non-atomic variants (must hold a lock) */
void __set_bit(int nr, volatile unsigned long *addr);
void __clear_bit(int nr, volatile unsigned long *addr);

/* Test (atomic read) */
int test_bit(int nr, const volatile unsigned long *addr);

/* Find operations */
unsigned long find_first_bit(const unsigned long *addr, unsigned long size);
unsigned long find_next_bit(const unsigned long *addr, unsigned long size, unsigned long offset);
unsigned long find_first_zero_bit(const unsigned long *addr, unsigned long size);
```

### Kernel Spinlock

```c
#include <linux/spinlock.h>

spinlock_t lock;
spin_lock_init(&lock);

// Acquire/release
spin_lock(&lock);           // Disable preemption + acquire
spin_unlock(&lock);         // Release + enable preemption

// IRQ-safe variants
unsigned long flags;
spin_lock_irqsave(&lock, flags);    // Save+disable IRQs, acquire
spin_unlock_irqrestore(&lock, flags); // Release, restore IRQs

// BH (bottom-half) safe
spin_lock_bh(&lock);
spin_unlock_bh(&lock);

// Try
if (spin_trylock(&lock)) {
    // critical section
    spin_unlock(&lock);
}

// Reader-writer spinlock
rwlock_t rwlock;
rwlock_init(&rwlock);
read_lock(&rwlock);     read_unlock(&rwlock);
write_lock(&rwlock);    write_unlock(&rwlock);
```

### Kernel RCU Integration with Atomics

```c
#include <linux/rcupdate.h>

struct my_data {
    atomic_t refcount;
    struct rcu_head rcu;
    int data;
};

static struct my_data __rcu *global_ptr;

// Reader (in RCU read-side critical section)
rcu_read_lock();
struct my_data *p = rcu_dereference(global_ptr);  // Implies smp_load_acquire
if (p) {
    int val = p->data;  // Safe: RCU protects from premature free
}
rcu_read_unlock();

// Writer (update pointer)
struct my_data *new = kmalloc(sizeof(*new), GFP_KERNEL);
new->data = 42;
atomic_set(&new->refcount, 1);

struct my_data *old = rcu_replace_pointer(global_ptr, new, ...);
synchronize_rcu();  // Wait for all pre-existing readers to complete
kfree(old);         // Safe: all readers have finished
```

### Kernel Reference Counting (`kref`)

```c
#include <linux/kref.h>

struct my_object {
    struct kref refcount;
    // ... other fields
};

void my_object_init(struct my_object *obj) {
    kref_init(&obj->refcount);  // Sets count to 1
}

struct my_object *my_object_get(struct my_object *obj) {
    kref_get(&obj->refcount);   // Atomic increment
    return obj;
}

static void my_object_release(struct kref *ref) {
    struct my_object *obj = container_of(ref, struct my_object, refcount);
    kfree(obj);
}

void my_object_put(struct my_object *obj) {
    kref_put(&obj->refcount, my_object_release);  // Decrement; if 0, call release
}

// Safer: kref_put_mutex / kref_put_lock for patterns where you need
// the lock held while the final release happens
```

### Per-CPU Atomics (Kernel)

```c
#include <linux/percpu.h>

// Declare per-CPU variable (one instance per CPU core)
DEFINE_PER_CPU(int, my_counter);

// Increment on current CPU (preemption must be disabled)
preempt_disable();
this_cpu_inc(my_counter);      // Atomic with respect to current CPU only
preempt_enable();

// Access via pointer
int __percpu *ptr = alloc_percpu(int);
per_cpu_ptr(ptr, cpu_id);

// Aggregate across all CPUs
int total = 0;
int cpu;
for_each_possible_cpu(cpu) {
    total += per_cpu(my_counter, cpu);
}
```

Per-CPU variables are extremely fast (no cache invalidation, no CAS) because only one CPU writes each copy. The global sum is eventually consistent — suitable for statistics, but not for strict synchronization.

---

## 11. Lock-Free Data Structures

### Treiber Stack (LIFO, Lock-Free)

The simplest lock-free structure. Push and pop use CAS on the head pointer.

```
Initial:     head → [A] → [B] → [C] → NULL

Push D:
  1. new_node.next = head (= A)
  2. CAS(&head, A, D)      ← may fail if head changed; retry
  3. head → [D] → [A] → [B] → [C] → NULL

Pop:
  1. old_head = head (= D)
  2. new_head = old_head.next (= A)
  3. CAS(&head, D, A)       ← may fail if another pop ran; retry
  4. return D's data
  5. head → [A] → [B] → [C] → NULL
```

**Problem:** ABA. See Section 12.

### Michael-Scott Queue (FIFO, Lock-Free)

Two-pointer (head + tail) queue with a sentinel node.

```c
// MS Queue node
typedef struct node {
    _Atomic(struct node *) next;
    void *value;
} msq_node_t;

typedef struct {
    _Atomic(msq_node_t *) head;  // Points to sentinel
    _Atomic(msq_node_t *) tail;  // Points to last enqueued or sentinel
} msq_t;

void msq_init(msq_t *q) {
    msq_node_t *sentinel = calloc(1, sizeof(*sentinel));
    atomic_store(&q->head, sentinel);
    atomic_store(&q->tail, sentinel);
}

void msq_enqueue(msq_t *q, void *value) {
    msq_node_t *n = malloc(sizeof(*n));
    atomic_store_explicit(&n->next, NULL, memory_order_relaxed);
    n->value = value;

    msq_node_t *tail, *next;
    while (1) {
        tail = atomic_load_explicit(&q->tail, memory_order_acquire);
        next = atomic_load_explicit(&tail->next, memory_order_acquire);
        if (tail != atomic_load_explicit(&q->tail, memory_order_relaxed)) continue;

        if (next == NULL) {
            // Try to link n at the end
            if (atomic_compare_exchange_weak_explicit(
                &tail->next, &next, n,
                memory_order_release, memory_order_relaxed)) {
                break;  // linked; tail update may be done by anyone
            }
        } else {
            // Tail is not pointing to last node — help advance it
            atomic_compare_exchange_weak_explicit(
                &q->tail, &tail, next,
                memory_order_release, memory_order_relaxed);
        }
    }
    // Try to swing tail to new node (may be done by another thread)
    atomic_compare_exchange_strong_explicit(
        &q->tail, &tail, n,
        memory_order_release, memory_order_relaxed);
}

void *msq_dequeue(msq_t *q) {
    msq_node_t *head, *tail, *next;
    while (1) {
        head = atomic_load_explicit(&q->head, memory_order_acquire);
        tail = atomic_load_explicit(&q->tail, memory_order_acquire);
        next = atomic_load_explicit(&head->next, memory_order_acquire);

        if (head != atomic_load_explicit(&q->head, memory_order_relaxed)) continue;
        if (head == tail) {
            if (next == NULL) return NULL;   // empty
            // Tail lagging — help advance
            atomic_compare_exchange_weak_explicit(
                &q->tail, &tail, next,
                memory_order_release, memory_order_relaxed);
        } else {
            void *value = next->value;
            if (atomic_compare_exchange_weak_explicit(
                &q->head, &head, next,
                memory_order_release, memory_order_relaxed)) {
                free(head);   // sentinel (old head) is freed
                return value;
            }
        }
    }
}
```

### Lock-Free Hash Map Concepts

A full lock-free hash map is complex. Common approaches:

1. **Split-ordered list (Shalev & Shavit):** The hash table is backed by a split-ordered linked list. Resizing is done by inserting sentinel nodes. CAS on next pointers for insert/delete.

2. **Linear probing with CAS:** Probe linearly, CAS to claim a slot. Deletion requires tombstone markers. Resize requires a migration phase coordinated by CAS.

3. **Epoch-based resizing:** Old and new table coexist during resize. Reads check both; writers migrate and CAS entries. Used in Java's ConcurrentHashMap.

For production use in Rust, prefer `dashmap` (sharded RwLock), `flurry` (Cliff Click's lock-free HM), or `crossbeam-skiplist`.

---

## 12. The ABA Problem

### What Is ABA?

A **compare-and-swap** reads a pointer, makes a decision based on its value, then CAS-swaps it. ABA occurs when:

1. Thread 1 reads pointer = A
2. Thread 1 is preempted
3. Thread 2 pops A, pushes B, pops B, pushes A (the same pointer value, but different state)
4. Thread 1 resumes: CAS sees pointer == A, **succeeds** — but the stack structure has changed

**Concrete disaster:**

```
Stack: head → [A] → [B] → NULL

Thread 1: reads head=A, reads A.next=B  (wants to pop A, new head=B)
Thread 1: preempted

Thread 2: pops A (head=B), pops B (head=NULL), pushes A (head=A, A.next=NULL)
  (B is freed)

Thread 1: resumes, CAS(&head, A, B) SUCCEEDS (head is still A)
  Result: head = B  (DANGLING POINTER — B was freed!)
```

### Mitigation 1: Tagged Pointer (Double-Width CAS)

Append a generation counter to the pointer. The tag is incremented on every modification, so the same pointer value with a different tag causes CAS to fail.

```c
// 128-bit tagged pointer on x86-64 (requires CMPXCHG16B)
typedef struct {
    void    *ptr;    // 8 bytes
    uint64_t tag;    // 8 bytes (generation counter)
} tagged_ptr_t __attribute__((aligned(16)));

// CAS on the 128-bit structure
// Both ptr AND tag must match for CAS to succeed
```

Rust equivalent using `AtomicU128` or a packed struct in an `AtomicU128`.

**Limitation:** Requires 16-byte CAS support (`cmpxchg16b` on x86-64, present since Core 2). Not universally available on all architectures without emulation.

### Mitigation 2: Hazard Pointers

Protect pointers from being freed while any thread holds a reference. See Section 13.

### Mitigation 3: Epoch-Based Reclamation (EBR)

Threads announce which epoch they are in. Memory is deferred for reclamation until all threads have advanced past the epoch in which the memory was freed. Used in crossbeam-epoch and Folly's Hazptr.

### Mitigation 4: Never Reuse Memory (in practice: slabs)

In slab allocators with per-type caches, freed objects are recycled only within the same type. Combined with generation tags, this dramatically reduces ABA probability but does not eliminate it.

### Mitigation 5: Avoid Pointer-Based Structures

Use indices into a fixed array rather than pointers. CAS on (index, tag) pairs. The array never moves, so ABA requires the same index slot to be reused with the same tag — much harder if tags are 32+ bits.

---

## 13. Hazard Pointers

Hazard pointers (Michael, 2004) provide safe memory reclamation for lock-free data structures without stopping the world.

### Concept

Each thread maintains a small array of "hazard pointers" — pointers to memory that the thread is currently accessing and that must not be freed. Before accessing a shared pointer, a thread publishes it in its hazard array. Before freeing memory, the reclaimer checks all hazard arrays.

```
Thread 1 (reader):              Thread 2 (reclaimer):
  hazard[0] = ptr;              // collect all hazard pointers
  fence(Acquire);               // scan retired list
  if (head == ptr) {            // if ptr NOT in any hazard array:
      use(*ptr);                //   free(ptr)
  }                             // if ptr IN hazard array:
  hazard[0] = NULL;             //   defer to later
```

### Rust Implementation Sketch

```rust
// hazard_ptr.rs — simplified educational implementation
use std::sync::atomic::{AtomicPtr, AtomicUsize, Ordering, fence};
use std::ptr;

const MAX_THREADS: usize = 64;
const HAZARD_PER_THREAD: usize = 2;

// Global hazard pointer table
static HAZARD_TABLE: [[AtomicPtr<u8>; HAZARD_PER_THREAD]; MAX_THREADS] = {
    // Const initialization
    const INIT: [AtomicPtr<u8>; 2] = [
        AtomicPtr::new(ptr::null_mut()),
        AtomicPtr::new(ptr::null_mut()),
    ];
    [INIT; MAX_THREADS]
};

static THREAD_COUNTER: AtomicUsize = AtomicUsize::new(0);

thread_local! {
    static THREAD_ID: usize = THREAD_COUNTER.fetch_add(1, Ordering::Relaxed);
    static RETIRED: std::cell::RefCell<Vec<*mut u8>> =
        std::cell::RefCell::new(Vec::new());
}

/// Protect a pointer: publish it in our hazard slot
/// Returns the protected pointer (or null if the source changed)
pub fn protect<T>(slot: usize, source: &AtomicPtr<T>) -> *mut T {
    THREAD_ID.with(|&tid| {
        loop {
            let ptr = source.load(Ordering::Relaxed);
            // Publish our hazard
            HAZARD_TABLE[tid][slot].store(ptr as *mut u8, Ordering::Release);
            // Verify source hasn't changed
            fence(Ordering::SeqCst);
            if source.load(Ordering::Relaxed) == ptr {
                return ptr;
            }
            // Source changed; retry
        }
    })
}

/// Release a hazard slot
pub fn release(slot: usize) {
    THREAD_ID.with(|&tid| {
        HAZARD_TABLE[tid][slot].store(ptr::null_mut(), Ordering::Release);
    });
}

/// Retire a pointer for eventual deallocation
pub unsafe fn retire<T>(ptr: *mut T) {
    RETIRED.with(|retired| {
        retired.borrow_mut().push(ptr as *mut u8);
    });
    // Scan when retired list grows large enough
    scan();
}

fn scan() {
    // Collect all hazard pointers
    let mut hazards = std::collections::HashSet::new();
    for tid in 0..MAX_THREADS {
        for slot in 0..HAZARD_PER_THREAD {
            let p = HAZARD_TABLE[tid][slot].load(Ordering::Acquire);
            if !p.is_null() {
                hazards.insert(p as usize);
            }
        }
    }

    // Free all retired pointers not in hazard set
    RETIRED.with(|retired| {
        let mut r = retired.borrow_mut();
        r.retain(|&ptr| {
            if hazards.contains(&(ptr as usize)) {
                true // still hazardous — keep
            } else {
                unsafe { drop(Box::from_raw(ptr)) }; // safe to free
                false
            }
        });
    });
}
```

### Trade-offs

| Property | Hazard Pointers | Epoch-Based Reclamation |
|---|---|---|
| Memory bound | O(K × N) where K=hazards/thread | Unbounded in long read sections |
| Overhead | Per-access (publish + verify) | Per-critical-section boundary |
| Long read sections | Fine | Memory can accumulate |
| Complexity | Moderate | Higher |
| Read-side cost | ~2 fences | ~1 atomic inc |

---

## 14. Read-Copy-Update (RCU)

RCU is a synchronization mechanism that allows reads to proceed concurrently with writes and deletions, without any read-side locking or atomic operations (on most architectures).

### Core Idea

- **Readers** never block, never use locks, often need only a memory barrier or nothing (on TSO)
- **Writers** copy the data structure, modify the copy, then atomically publish the new version
- **Reclamation** happens after a **grace period** — once all pre-existing readers have completed

```
Before update:         After update:
head → [old_data]     head → [new_data]
                               [old_data]  ← will be freed after grace period

Readers that started before the pointer swap: still using [old_data] — safe
Readers that start after the pointer swap:    use [new_data]
```

### Grace Period

A grace period is the time span after a write during which old readers may still hold references. Once all CPUs have passed through a **quiescent state** (a point where they cannot hold an RCU reference — i.e., they are not in an RCU read-side critical section), the grace period ends and old memory can be freed.

**Quiescent states in the kernel:**
- CPU context switch (the process gave up the CPU)
- CPU is idle
- CPU is in user space

### Linux Kernel RCU API

```c
#include <linux/rcupdate.h>

/* READ SIDE — extremely cheap */
rcu_read_lock();                              // Disables preemption (or not, in SRCU)
struct data *p = rcu_dereference(global_p);  // READ_ONCE + data dependency barrier
// Use p safely here — it won't be freed
rcu_read_unlock();

/* WRITE SIDE */
struct data *new_p = kmalloc(...);
init_data(new_p);

// Atomically publish new pointer
rcu_assign_pointer(global_p, new_p);         // smp_store_release

// Wait for all pre-existing readers to complete
synchronize_rcu();                           // Blocking; may sleep

kfree(old_p);

/* CALLBACK-BASED (non-blocking) */
call_rcu(&old_p->rcu_head, my_free_func);    // Schedule free after grace period

/* ALTERNATIVE: kfree_rcu — zero-boilerplate */
kfree_rcu(old_p, rcu_head);
```

### RCU Read-Side Cost Analysis

On x86 (TSO):
- `rcu_read_lock()` = `preempt_disable()` = single per-CPU memory access (no fence)
- `rcu_dereference()` = `READ_ONCE()` = single load (implicit data dependency ordering on x86)
- `rcu_read_unlock()` = `preempt_enable()` = single per-CPU memory access

Near-zero overhead for readers. This is why RCU is used in hot paths (networking, VFS, scheduler).

### Userspace RCU (liburcu)

```c
#include <urcu.h>

// Reader
rcu_read_lock();
struct data *p = rcu_dereference(global_p);
// use p
rcu_read_unlock();

// Writer
struct data *new_p = malloc(sizeof(*new_p));
rcu_assign_pointer(global_p, new_p);
synchronize_rcu();
free(old_p);

// Required: readers must periodically call
rcu_quiescent_state();   // signal we've left any critical section
// OR register with: rcu_register_thread()
```

---

## 15. Seqlocks

A seqlock (sequential lock) is a reader-writer synchronization mechanism optimized for frequent reads and infrequent writes to small data (like timestamps). Readers are never blocked by writers.

### How It Works

```c
typedef struct {
    atomic_uint sequence;  // Odd = write in progress, Even = no write
    // ... data ...
    int x, y, z;
} seqlock_t;

void seqlock_init(seqlock_t *sl) {
    atomic_init(&sl->sequence, 0);
}

/* WRITER */
void seqlock_write_begin(seqlock_t *sl) {
    // Increment to odd (signals write in progress)
    atomic_fetch_add_explicit(&sl->sequence, 1, memory_order_release);
}

void seqlock_write_end(seqlock_t *sl) {
    // Increment to even (write complete)
    atomic_fetch_add_explicit(&sl->sequence, 1, memory_order_release);
}

/* READER — retry loop */
int read_consistent(seqlock_t *sl, int *x, int *y, int *z) {
    unsigned seq;
    do {
        seq = atomic_load_explicit(&sl->sequence, memory_order_acquire);
        if (seq & 1) continue;  // Writer in progress — spin

        *x = sl->x;
        *y = sl->y;
        *z = sl->z;

        // Re-read sequence: if changed, retry
    } while (atomic_load_explicit(&sl->sequence, memory_order_acquire) != seq);
    return 0;
}
```

### Linux Kernel Seqlock

```c
#include <linux/seqlock.h>

seqlock_t sl;
seqlock_init(&sl);

/* Writer */
write_seqlock(&sl);
// ... modify data ...
write_sequnlock(&sl);

/* Reader */
unsigned seq;
do {
    seq = read_seqbegin(&sl);
    // ... read data ...
} while (read_seqretry(&sl, seq));

/* IRQ-safe variants */
write_seqlock_irq(&sl);
write_sequnlock_irq(&sl);
```

### Seqlock Properties

- Readers never block writers
- Writers never block readers (but readers retry)
- Suitable for: timestamps, statistics, small frequently-read structs
- Not suitable for: pointers (reader may dereference a pointer mid-update — the retried read doesn't undo the dereference), large structures (excessive retries)

---

## 16. Progress Guarantees

Progress guarantees classify how concurrent algorithms behave under adversarial scheduling.

### Blocking

At least one thread can be indefinitely delayed (e.g., mutex, spinlock). If the thread holding the lock is preempted, all other threads wait.

### Obstruction-Free

A thread makes progress if it runs **alone** (all other threads are suspended). Multiple concurrent threads may livelock.

### Lock-Free

At least one thread in the system makes progress in a finite number of steps. Individual threads may starve, but the system as a whole always advances. CAS-retry loops are typically lock-free.

### Wait-Free

**Every** thread makes progress in a finite number of steps, regardless of other threads. The strongest guarantee. Rare in practice (complex to implement). Example: single-reader single-writer ring buffers, fetch-add counters.

```
Strength:  Blocking < Obstruction-Free < Lock-Free < Wait-Free
Cost:      Low overhead ──────────────────────────── High overhead
```

### Implications for Security

Lock-free algorithms are resistant to **priority inversion** (a low-priority thread holding a mutex that a high-priority thread needs). Wait-free algorithms provide **bounded execution time** — important for real-time systems and defense against DoS via thread scheduling manipulation.

---

## 17. Common Pitfalls and Anti-patterns

### 1. Incorrect Memory Ordering

```c
// WRONG: relaxed store, acquire load — no synchronization
atomic_store_explicit(&flag, 1, memory_order_relaxed);  // producer
while (!atomic_load_explicit(&flag, memory_order_acquire)) {} // consumer
// Consumer sees flag=1 but may NOT see the data written before flag!

// CORRECT:
atomic_store_explicit(&flag, 1, memory_order_release);  // release after data
```

### 2. Mixing Atomics and Non-Atomics (Data Race)

```c
// WRONG: x is read non-atomically while another thread may write it
int x = 0;
// Thread 1:
x = 1;                         // non-atomic write
// Thread 2:
if (x == 1) { ... }            // non-atomic read — DATA RACE

// CORRECT: use _Atomic(int) or atomic_int
```

### 3. Double-Checked Locking (broken without atomics)

```c
// CLASSIC BUG (pre-C11, without volatile or atomics):
if (instance == NULL) {
    mutex_lock(&lock);
    if (instance == NULL) {
        instance = create_instance(); // Compiler may reorder: ptr published before init
    }
    mutex_unlock(&lock);
}

// CORRECT C11:
struct inst *tmp = atomic_load_explicit(&instance, memory_order_acquire);
if (!tmp) {
    mutex_lock(&lock);
    tmp = atomic_load_explicit(&instance, memory_order_relaxed);
    if (!tmp) {
        tmp = create_instance();
        atomic_store_explicit(&instance, tmp, memory_order_release);
    }
    mutex_unlock(&lock);
}
```

### 4. False Sharing

```c
// BAD: two hot counters on the same cache line
struct counters {
    atomic_int a;   // 4 bytes
    atomic_int b;   // 4 bytes — shares cache line with a
};
// Core 0 increments a, Core 1 increments b — constant cache invalidation

// GOOD: pad to separate cache lines
struct counters {
    _Alignas(64) atomic_int a;
    _Alignas(64) atomic_int b;
};
```

Rust:
```rust
#[repr(align(64))]
struct Padded<T>(T, [u8; 64 - std::mem::size_of::<T>()]);
// Or use crossbeam::utils::CachePadded
```

### 5. Infinite Retry Without Backoff

```c
// BAD: Under high contention, all threads spin on CAS → memory bus saturation
while (!atomic_compare_exchange_weak(&x, &expected, desired)) {}

// BETTER: exponential backoff
int backoff = 1;
while (!atomic_compare_exchange_weak(&x, &expected, desired)) {
    for (int i = 0; i < backoff; i++) {
        __builtin_ia32_pause();
    }
    backoff = (backoff < 1024) ? backoff * 2 : 1024;
}
```

### 6. Assuming Sequential Consistency on ARM

Code that "works" on x86 (due to TSO) often breaks on ARM:

```c
// Thread 1:       Thread 2:
x = 1;            y = 1;
r1 = y;           r2 = x;

// On x86 (TSO): r1=0 && r2=0 is IMPOSSIBLE
// On ARM:       r1=0 && r2=0 IS POSSIBLE (both stores in store buffers)
// IRIW (Independent Reads of Independent Writes) litmus test
```

### 7. Using `volatile` for Thread Synchronization

See Section 8. `volatile` is not an atomic. Never use it for inter-thread communication. It prevents only compiler optimization, not CPU reordering.

### 8. Composing Lock-Free Operations

Individual lock-free operations are atomic; their composition is not:

```c
// WRONG: thinking "two atomics = atomic pair"
int a = atomic_load(&shared_a);   // load a
int b = atomic_load(&shared_b);   // load b
// Another thread may have modified BOTH between these two loads
// a and b are from different "moments" — inconsistent snapshot

// CORRECT: use a seqlock, RCU, or combine under a lock
```

---

## 18. Testing, Fuzzing, and Tooling

### ThreadSanitizer (TSan)

The most important tool for detecting data races and atomicity violations.

```bash
# C: compile with TSan
gcc -fsanitize=thread -g -O1 -o test test.c

# Rust: 
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu

# Run and examine report
./test
# TSan output includes:
#   RACE: two accesses to the same address, at least one write, no happens-before
#   DEADLOCK: lock ordering violations
```

TSan uses shadow memory to track happens-before relationships. It has ~5-15x slowdown and 5-10x memory overhead. Run in CI, not production.

### Helgrind (Valgrind)

```bash
valgrind --tool=helgrind --history-level=approx ./test
```

Slower than TSan but more precise for some race patterns. Detects lock ordering violations (potential deadlock), unlocking a mutex you don't own.

### Loom (Rust)

Loom is a model checker for concurrent Rust code. It explores all possible thread interleavings systematically.

```rust
// Cargo.toml
[dev-dependencies]
loom = "0.7"

// test.rs
#[cfg(test)]
mod tests {
    use loom::sync::atomic::{AtomicUsize, Ordering};
    use loom::thread;
    use std::sync::Arc;

    #[test]
    fn test_counter() {
        loom::model(|| {
            let counter = Arc::new(AtomicUsize::new(0));

            let c1 = Arc::clone(&counter);
            let t1 = thread::spawn(move || {
                c1.fetch_add(1, Ordering::Relaxed);
            });

            let c2 = Arc::clone(&counter);
            let t2 = thread::spawn(move || {
                c2.fetch_add(1, Ordering::Relaxed);
            });

            t1.join().unwrap();
            t2.join().unwrap();

            // This must hold for ALL interleavings
            assert_eq!(counter.load(Ordering::SeqCst), 2);
        });
    }
}
```

Loom replaces `std::sync::atomic` with a model-checking version that explores all possible orderings.

### CDSChecker

C/C++ model checker that explores all legal behaviors under the C11 memory model:

```bash
git clone https://github.com/computersystems/cdschecker
cd cdschecker && make
# Run your program through cdschecker — it reports races and invalid orderings
./cdschecker -- ./your_lockfree_program
```

### Litmus Tests

Litmus tests are minimal concurrent programs designed to test a specific memory model behavior. The `herd7` tool from INRIA can simulate them:

```
# IRIW litmus test (Independent Reads of Independent Writes)
# Tests whether two readers can see writes in different orders
C IRIW
{
  int x = 0; int y = 0;
}
P0 (int *x) { *x = 1; }
P1 (int *y) { *y = 1; }
P2 (int *x, int *y) { int r0 = *x; int r1 = *y; }
P3 (int *x, int *y) { int r0 = *y; int r1 = *x; }
exists (2:r0=1 /\ 2:r1=0 /\ 3:r0=1 /\ 3:r1=0)
# This is allowed on POWER but not on x86
```

### Benchmarking Atomics

```rust
// benches/atomic_bench.rs (Criterion)
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use std::sync::atomic::{AtomicUsize, Ordering};

fn bench_relaxed(c: &mut Criterion) {
    let x = AtomicUsize::new(0);
    c.bench_function("fetch_add relaxed", |b| {
        b.iter(|| x.fetch_add(black_box(1), Ordering::Relaxed))
    });
}

fn bench_seqcst(c: &mut Criterion) {
    let x = AtomicUsize::new(0);
    c.bench_function("fetch_add seqcst", |b| {
        b.iter(|| x.fetch_add(black_box(1), Ordering::SeqCst))
    });
}

criterion_group!(benches, bench_relaxed, bench_seqcst);
criterion_main!(benches);
```

```bash
cargo bench
# Typical results on modern x86:
#   relaxed: ~1.5 ns (L1 hit, no fence)
#   seqcst:  ~5-8 ns (MFENCE or LOCK XADD)
#   cross-socket: ~100-300 ns (QPI/UPI round trip)
```

### Linux Kernel Tooling

```bash
# KCSAN: Kernel Concurrency Sanitizer (analogous to TSan for kernel)
# Enable in Kconfig:
CONFIG_KCSAN=y
CONFIG_KCSAN_REPORT_RACE=y

# lockdep: lock ordering validator
CONFIG_PROVE_LOCKING=y
CONFIG_LOCKDEP=y
# Run any code path that acquires locks — lockdep builds a graph
# and reports cycles (potential deadlocks)

# perf: analyze atomic contention
perf stat -e cache-misses,cache-references,LLC-load-misses ./program

# perf lock: lock contention analysis (kernel locks)
perf lock record -- ./program
perf lock report
```

---

## 19. Security Threat Model

### Threat: TOCTOU (Time-of-Check to Time-of-Use)

A race between checking a condition and using the result. Classic in file system code:

```c
// VULNERABLE: stat then open — another process can replace the file between calls
if (stat(path, &st) == 0 && S_ISREG(st.st_mode)) {
    fd = open(path, O_RDONLY);  // Attacker replaced path with a symlink!
}

// MITIGATION: use O_NOFOLLOW, openat with fstat, or open-then-fstat
fd = open(path, O_RDONLY | O_NOFOLLOW);
if (fd >= 0) {
    fstat(fd, &st);  // stat the fd, not the path
}
```

In concurrent data structures, TOCTOU manifests as:

```c
// WRONG: check then act is not atomic
if (atomic_load(&count) > 0) {
    atomic_fetch_sub(&count, 1);  // count may be 0 by the time we sub!
}

// CORRECT: CAS-based decrement that checks atomically
int val = atomic_load_explicit(&count, memory_order_relaxed);
while (val > 0) {
    if (atomic_compare_exchange_weak_explicit(&count, &val, val - 1,
        memory_order_acq_rel, memory_order_relaxed)) {
        break;
    }
    // val was updated by CAS failure; loop re-checks val > 0
}
```

### Threat: Integer Overflow in Atomics

```c
// Wrapping atomic increment — overflow is well-defined for unsigned,
// but logic bugs occur if code assumes monotonic increase
atomic_uint refcount = ATOMIC_VAR_INIT(0);

// Attacker causes 4 billion increments → refcount wraps to 0
// → object freed while references still exist

// MITIGATION: saturating increment
uint32_t old = atomic_load_explicit(&refcount, memory_order_relaxed);
while (old < UINT32_MAX) {
    if (atomic_compare_exchange_weak_explicit(&refcount, &old, old + 1,
        memory_order_acquire, memory_order_relaxed)) {
        break; // success
    }
}
if (old == UINT32_MAX) {
    // overflow: panic, return error, or abort
}
```

### Threat: Spectre via Shared Atomics

Speculative execution can leak data through cache timing side channels. An attacker can:
1. Train a branch predictor to speculatively execute a load from an atomic-protected structure
2. Read the speculatively loaded value via cache timing (Flush+Reload)

**Mitigation:** `LFENCE` after bounds checks in sensitive code paths. The Linux kernel added `array_index_nospec()`:

```c
// Prevents speculative out-of-bounds index
index = array_index_nospec(user_index, array_size);
```

### Threat: Lock-Free Code and Memory Safety (Rust)

Rust's ownership system prevents most memory safety bugs in safe code. However, atomics require `unsafe` for raw pointer manipulation. Key rules:

1. **Never dereference a raw pointer without a valid hazard pointer or epoch guard**
2. **All `unsafe` blocks must document their invariants**
3. **Use `crossbeam-epoch` or `haphazard` — do not implement reclamation manually**
4. **Miri: run code through the Rust interpreter to detect UB**

```bash
MIRIFLAGS="-Zmiri-preemption-rate=0.01" cargo +nightly miri test
```

### Threat: Kernel Refcount UAF

Use-after-free (UAF) from reference counting bugs is a common kernel exploitation primitive:

```
1. Attacker causes refcount to reach 0 → object freed
2. Object is reallocated for attacker-controlled data
3. Old reference still exists (from race) → reads/writes attacker's data
```

**Mitigation in Linux:** `refcount_t` (wraps `atomic_t` with overflow/underflow detection):

```c
#include <linux/refcount.h>

refcount_t refs;
refcount_set(&refs, 1);
refcount_inc(&refs);           // safe increment (warns on overflow)
if (refcount_dec_and_test(&refs)) {
    // cleanup
}
// refcount_dec_not_one, refcount_inc_not_zero, etc.
```

`refcount_t` uses `atomic_add_unless` internally to prevent increment past a sentinel value and detects underflow (decrement below 0).

### Threat: NUMA-Aware Attack Surface

On NUMA systems, remote memory accesses are significantly slower. An attacker who knows the NUMA topology can cause a victim to perform cross-socket atomic operations (via cache invalidations) as a DoS — degrading throughput by 50-100x. Mitigate with NUMA-local per-CPU data and shard hot atomics per NUMA node.

---

## 20. Performance and Benchmarking

### Atomic Operation Costs (approximate, modern x86)

```
Operation                          Cost (cycles)  Notes
-------------------------------------------------------------------
atomic_load relaxed                ~1             L1 hit, no fence
atomic_load acquire                ~1             On x86, same as relaxed
atomic_store release               ~1             Into store buffer
atomic_store seq_cst               ~20-40         MFENCE or XCHG
atomic_fetch_add relaxed           ~4             LOCK XADD, L1 hit
atomic_fetch_add seq_cst           ~25-40         LOCK XADD + MFENCE
CAS (uncontended, L1 hit)          ~4             LOCK CMPXCHG
CAS (contended, same socket L3)    ~30-60         L3 hit + coherency
CAS (contended, cross-socket)      ~200-400       QPI/UPI round trip
mutex lock (uncontended)           ~20-30         futex fast path
mutex lock (contended)             ~1000+         kernel entry + wake
```

### The Lock vs. Atomic Tradeoff

```
Contention level:    Low        Medium      High
----------------------------------------------------
Spinlock             Fast       OK          Bad (CPU waste)
Mutex                OK         OK          OK (sleeps)
Lock-free (CAS)      Fast       Fast        Bad (retry loops)
Wait-free            Fast       Fast        Fast (no loops)
Per-CPU/sharded      Fastest    Fastest     Fastest (no sharing)
```

At very high contention (>8 threads on same atomic), CAS loops can be worse than a mutex because all threads are burning CPU in retry loops, saturating the memory bus. The best solution is to eliminate sharing: per-CPU counters, sharded data structures, or redesigning the algorithm.

### Cache Line Contention — Microbenchmark

```c
// False sharing benchmark
#define THREADS 8
#define ITERS   10000000

// BAD: all threads share one cache line
atomic_long_t shared_counter = ATOMIC_VAR_INIT(0);

// GOOD: per-thread counter, aggregate later
_Alignas(64) atomic_long_t per_thread_counter[THREADS];

// Measurement: shared_counter throughput is ~8x worse under 8 threads
```

### Throughput Scaling

```
Throughput (Mops/s) — fetch_add on single variable

Threads:     1      2      4      8      16
Same socket: 100    55     30     17     10   (coherency overhead)
Per-thread:  100    200    400    800    1600  (perfect scaling)
```

Perfect scaling requires elimination of shared state. Use atomic operations for coordination signals (flags, sequence numbers), not for data movement.

---

## 21. Architecture Diagrams (ASCII)

### Full Stack: From Application to Hardware

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        APPLICATION LAYER                             │
 │  Rust: AtomicUsize::fetch_add(1, Ordering::SeqCst)                  │
 │  C11:  atomic_fetch_add_explicit(&x, 1, memory_order_seq_cst)        │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │ Compiler lowers to ISA instruction
 ┌──────────────────────────────▼───────────────────────────────────────┐
 │                        COMPILER LAYER                                │
 │  x86-64:  lock xadd DWORD PTR [rdi], 1                               │
 │  AArch64: ldaxr / stlxr loop   (pre-LSE)                             │
 │           ldaddal              (ARMv8.1 LSE)                          │
 │  RISC-V:  amoadd.w.aqrl        (A extension)                         │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │ CPU executes instruction
 ┌──────────────────────────────▼───────────────────────────────────────┐
 │                        CPU PIPELINE LAYER                            │
 │                                                                      │
 │  Fetch → Decode → Rename ──────────────────────────────────────┐     │
 │                               │                                │     │
 │                         ROB (Reorder Buffer)                   │     │
 │                               │                                │     │
 │                      Load/Store Unit                           │     │
 │                         │          │                           │     │
 │                   Load Queue    Store Buffer ──── Drain ───────┘     │
 │                         │          │                                 │
 │  ◄──── Store-to-Load Forwarding ───┘                                 │
 │                         │                                            │
 │                    L1 Data Cache (4 cycles)                          │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │ Cache miss / RFO (Request For Ownership)
 ┌──────────────────────────────▼───────────────────────────────────────┐
 │                      CACHE COHERENCY LAYER                           │
 │                                                                      │
 │  ┌─────────┐  snoop/invalidate  ┌─────────┐                         │
 │  │ Core 0  │◄──────────────────►│ Core 1  │                         │
 │  │ L1/L2   │                    │ L1/L2   │                         │
 │  │ [E→M]   │                    │ [S→I]   │  ← invalidated          │
 │  └────┬────┘                    └─────────┘                         │
 │       │ RFO granted                                                  │
 │  ┌────▼──────────────────────────────────┐                          │
 │  │           L3 (LLC) — shared           │                          │
 │  └───────────────────────────────────────┘                          │
 │  MESI Protocol:  M=Modified E=Exclusive S=Shared I=Invalid          │
 └──────────────────────────────────────────────────────────────────────┘
```

### Memory Ordering: Acquire-Release Synchronization

```
 Thread 1 (Producer)                    Thread 2 (Consumer)
 ─────────────────────                  ─────────────────────
 data[0] = compute_a();   ─────┐        │
 data[1] = compute_b();        │        │
 ...                           │        │
 result = process(data);       │        │   ← These reads see all writes
                               │        │      above the release store,
 flag.store(1, Release) ───────┼──────► │      because of the happens-before
                               │        │      chain established by:
     ┌─────── All writes ◄─────┘        │      Release STORE → Acquire LOAD
     │   before Release are             │
     │   visible after Acquire          ▼
     └──────────────────────► while (!flag.load(Acquire)) {}
                               // happens-before: flag store → flag load
                               use(result);  // SAFE: sees all data[] writes
```

### Linux Kernel Synchronization Layers

```
 ┌────────────────────────────────────────────────────────────────────┐
 │                    User Space                                      │
 │  pthread_mutex  atomic_fetch_add  __atomic_*  std::atomic          │
 └──────────────────────────────┬─────────────────────────────────────┘
                                │ syscall (futex, etc.)
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │                    Linux Kernel                                    │
 │                                                                    │
 │  High-level:  mutex  rwsem  semaphore  completion                  │
 │  Medium:      spinlock  rwlock  seqlock                            │
 │  RCU:         rcu_read_lock/unlock  synchronize_rcu  call_rcu      │
 │  Low-level:   atomic_t  atomic64_t  atomic_long_t                 │
 │               atomic_read/set/add/sub/inc/dec/cmpxchg/xchg        │
 │  Barriers:    mb() rmb() wmb() smp_mb() READ_ONCE() WRITE_ONCE()  │
 │  Per-CPU:     per_cpu  this_cpu_inc/dec/add  get_cpu_var           │
 │  Bit ops:     set_bit  clear_bit  test_and_set_bit                 │
 └──────────────────────────────┬─────────────────────────────────────┘
                                │ arch-specific asm
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │           Architecture-Specific Implementation                    │
 │  x86:    LOCK CMPXCHG, LOCK XADD, LOCK XCHG, MFENCE, LFENCE      │
 │  ARM64:  LDAXR/STLXR, LDAR/STLR, LDADDAL, DMB ISH               │
 │  RISC-V: LR.W/SC.W, AMOADD.W.AQRL, FENCE RW,RW                   │
 └──────────────────────────────┬─────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │                    Hardware                                        │
 │  CPU Cores → Store Buffers → L1/L2 Cache → L3 (LLC) → DRAM        │
 │  Cache Coherency Ring/Mesh (MESI/MESIF/MOESI)                     │
 │  QPI/UPI (cross-socket) / Infinity Fabric (AMD)                   │
 └────────────────────────────────────────────────────────────────────┘
```

### CAS Loop State Machine

```
 ┌──────────────────────────────────────────────────────────┐
 │                    CAS Retry Loop                        │
 │                                                          │
 │   START                                                  │
 │     │                                                    │
 │     ▼                                                    │
 │   Load current value → expected                         │
 │     │                                                    │
 │     ▼                                                    │
 │   Compute desired = f(expected)                         │
 │     │                                                    │
 │     ▼                                                    │
 │   CAS(addr, expected, desired)                          │
 │     │                                                    │
 │     ├──── SUCCESS (ZF=1) ────────────────────► DONE     │
 │     │     addr now holds desired                        │
 │     │                                                    │
 │     └──── FAILURE (ZF=0) ─────────────────────┐         │
 │           expected ← current addr value        │         │
 │           (updated by CPU on failure)          │         │
 │                                                │         │
 │       ┌── Contended? ──────────────────────────┘         │
 │       │   PAUSE/yield/backoff                            │
 │       └─────────────────────────────────────────┐        │
 │                                                 │        │
 │       Loop (lock-free guarantee: at least       ▼        │
 │            one thread wins each round)       RETRY       │
 └──────────────────────────────────────────────────────────┘
```

### NUMA System and Cross-Socket Atomics

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │  NUMA Node 0                    NUMA Node 1                         │
 │  ┌──────────────────────┐       ┌──────────────────────┐            │
 │  │ Core0 Core1 Core2 C3 │       │ Core4 Core5 Core6 C7 │            │
 │  │  L1   L1   L1   L1  │       │  L1   L1   L1   L1  │            │
 │  │  L2   L2   L2   L2  │       │  L2   L2   L2   L2  │            │
 │  │  ┌────────────────┐  │       │  ┌────────────────┐  │            │
 │  │  │    L3 / LLC    │  │       │  │    L3 / LLC    │  │            │
 │  │  └────────────────┘  │       │  └────────────────┘  │            │
 │  │  Memory Controller   │       │  Memory Controller   │            │
 │  │  Local DRAM (~80ns)  │       │  Local DRAM (~80ns)  │            │
 │  └──────────┬───────────┘       └──────────┬───────────┘            │
 │             │                              │                        │
 │             └─────── QPI/UPI (~200ns) ─────┘                        │
 │                   Intel UltraPath Interconnect                      │
 │                                                                     │
 │  Hot atomic in Node 0 memory, accessed from Node 1:                │
 │    → Cache miss on Node 1 L3                                       │
 │    → RFO travels QPI: Node 1 → Node 0 (~100ns each way)            │
 │    → Node 0 L3 invalidates/transfers line                          │
 │    → Total: ~200-400ns per atomic operation                        │
 │                                                                     │
 │  Solution: per-NUMA-node sharding                                   │
 │    counter[numa_node_id()]++;   // local, ~4ns                     │
 │    total = counter[0] + counter[1]; // aggregate when needed       │
 └─────────────────────────────────────────────────────────────────────┘
```

### Memory Model Ordering Spectrum

```
 Strictest ◄──────────────────────────────────────────────► Most Relaxed

 SeqCst          AcqRel        Acquire/Release      Relaxed
   │               │                 │                 │
   │               │                 │                 │
 Total global    RMW with         Load:Acquire      Atomicity
 order on all    both acq+rel     Store:Release     only, no
 seq_cst ops     semantics        Pairs for sync    ordering
   │               │                 │                 │
   │               │                 │                 │
 x86: MFENCE    LOCK XADD        LDAR/STLR         LOCK XADD
 ARM: DMB ISH   LDAXR/STLXR      separate          relaxed AMO
 RISC-V:FENCE   amoadd.aqrl      ldar/stlr         amoadd
   │               │                 │                 │
   │               │                 │                 │
 Use for:       RMW ops in      Producer-Consumer   Counters,
 total order    lock-free DS    flag protocols      statistics
 on flags       (CAS loops)     (most common)       (per-CPU)
```

---

## 22. Next 3 Steps

**Step 1 — Run the Loom model checker on your existing lock-free code**

```bash
# In your Rust project:
cargo add --dev loom

# Write a loom test for every lock-free structure you own
# Run: RUSTFLAGS="--cfg loom" cargo test
# This systematically explores all thread interleavings
# and will surface ordering bugs that TSan misses (TSan is probabilistic)
```

**Step 2 — Profile and eliminate false sharing in production services**

```bash
# Use perf to find cache line bouncing:
perf stat -e cache-misses,LLC-load-misses,cache-references -p <pid> -- sleep 5

# Use perf c2c (cache-to-cache) to find false sharing hot spots:
perf c2c record -g -- ./your_service
perf c2c report --call-graph --stdio | head -100

# Then pad your hot shared structures to 64-byte (or 128-byte) boundaries
# and re-measure
```

**Step 3 — Read and annotate the Linux kernel's atomic implementation for your target arch**

```bash
# x86:
cat linux/arch/x86/include/asm/atomic.h
cat linux/arch/x86/include/asm/cmpxchg.h

# ARM64:
cat linux/arch/arm64/include/asm/atomic.h
cat linux/arch/arm64/include/asm/atomic_lse.h  # LSE (ARMv8.1) atomics

# Core model (arch-independent wrappers):
cat linux/include/linux/atomic.h
cat linux/include/linux/atomic/atomic-arch-fallback.h

# Trace how atomic_fetch_add maps to the arch instruction
# This gives you the authoritative mapping between the abstract model and hardware
```

---

## 23. References

### Primary Sources

- **Herlihy & Shavit — "The Art of Multiprocessor Programming"** (2nd ed., 2020)
  The canonical textbook. Chapters 3-5 cover atomics, locks, lock-free structures.

- **Boehm & Adve — "Foundations of the C++ Concurrency Memory Model"** (PLDI 2008)
  The paper that defined the C11/C++11 memory model.

- **Michael — "Hazard Pointers: Safe Memory Reclamation for Lock-Free Objects"** (IEEE TPDS 2004)

- **McKenney — "Is Parallel Programming Hard, And, If So, What Can You Do About It?"**
  https://www.kernel.org/doc/Documentation/RCU/ — The authoritative RCU reference, by its author.

- **Lamport — "How to Make a Multiprocessor Computer That Correctly Executes Multiprocess Programs"** (1979)
  Original sequential consistency paper.

### ISA References

- **Intel® 64 and IA-32 Architectures Software Developer's Manual — Volume 3, Chapter 8**
  (Memory Ordering, LOCK prefix, CMPXCHG semantics)

- **ARM Architecture Reference Manual — AArch64 profile**
  (B2: The AArch64 Application Level Memory Model)

- **RISC-V Unprivileged ISA Specification — Chapter 14 (Atomics)**

### Linux Kernel

- `Documentation/memory-barriers.txt` — Linux memory model and barrier documentation
- `Documentation/RCU/` — Complete RCU documentation
- `tools/memory-model/` — Linux Kernel Memory Model (LKMM) formalization

### Tools

- ThreadSanitizer: https://clang.llvm.org/docs/ThreadSanitizer.html
- Loom (Rust): https://github.com/tokio-rs/loom
- CDSChecker: http://plrg.eecs.uci.edu/software_page/42-2/
- herd7 / litmus7: https://diy.inria.fr/
- crossbeam (Rust atomics/epoch): https://github.com/crossbeam-rs/crossbeam

### Papers on Memory Models

- **Alglave et al. — "Herding Cats: Modelling, Simulation, Testing, and Data Mining for Weak Memory"** (TOPLAS 2014)
- **Maranget et al. — "A Tutorial Introduction to the ARM and POWER Relaxed Memory Models"** (2012)
- **Batty et al. — "Mathematizing C++ Concurrency"** (POPL 2011)

---

*End of guide. Total coverage: hardware → cache coherency → memory models → fences → ISA instructions → C11 → GCC builtins → Rust → Linux kernel → lock-free structures → ABA → hazard pointers → RCU → seqlocks → progress guarantees → pitfalls → testing → security → performance.*

This is a large, deeply technical guide. I'll write it now as a comprehensive `.md` file.~23 sections, end-to-end. Here's a quick orientation of what's in each major block:

**Hardware foundations (§2–3):** Store buffers, ROB, load queues — why a plain RMW is not atomic even if it "looks" like one instruction. Full MESI/MESIF/MOESI transition diagrams with what an RFO costs (4 ns L1 → 400 ns cross-socket QPI).

**Memory models (§4–5):** TSO vs weak ordering with concrete litmus tests. The IRIW example is the exact test that proves ARM/POWER differ from x86 — that alone resolves most "works on my machine" bugs. Full barrier taxonomy: `lfence/sfence/mfence`, `dmb ishld/ishst`, `lwsync/sync`, and compiler-only `barrier()`.

**ISA instructions (§6):** LOCK prefix mechanics, CMPXCHG truth table, ARM LL/SC exclusive monitors vs ARMv8.1 LSE native atomics (`ldaddal`, `cas`), RISC-V AMO ordering suffixes (`.aq/.rl/.aqrl`). PAUSE/YIELD in spin loops is explicitly called out — missing it causes machine clears on x86.

**C11 (§7):** Complete API with every ordering variant. SPSC ring buffer with cache-line alignment and the exact relaxed/acquire/release assignment that makes it correct. Tagged-pointer CAS for ABA mitigation.

**Rust (§8–9):** Spinlock with `UnsafeCell` + correct `Sync` impl. SPSC with `MaybeUninit` and wrapping index arithmetic. `crossbeam-epoch` stack to show safe reclamation.

**Linux kernel (§10):** Full `atomic_t`/`atomic64_t` API, `READ_ONCE`/`WRITE_ONCE` semantics, `refcount_t` security (overflow/underflow detection), `kref`, per-CPU variables, seqlock, RCU integration.

**Security (§19):** TOCTOU with file descriptor fix, refcount overflow exploitation model, `refcount_t` as mitigation, Spectre via shared atomics + `array_index_nospec`, NUMA-targeted DoS via cross-socket cache invalidation flooding.

**Next 3 steps** are concrete and immediately actionable: Loom model checking, `perf c2c` false sharing profiling, and reading the kernel arch-specific atomic headers for your target.