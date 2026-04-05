# Cache-Line Alignment in Linux: A Complete Reference Guide

> *"The difference between a program that runs in 1ms and 100ms often lives in 64 bytes."*

---

## Table of Contents

1. [Foundational Concepts: The Memory Hierarchy](#1-foundational-concepts-the-memory-hierarchy)
2. [What Is a Cache Line?](#2-what-is-a-cache-line)
3. [Cache Geometry and Organization](#3-cache-geometry-and-organization)
4. [Cache Coherency Protocols (MESI/MESIF/MOESI)](#4-cache-coherency-protocols-mesimesifmoesi)
5. [False Sharing: The Silent Performance Killer](#5-false-sharing-the-silent-performance-killer)
6. [True Sharing vs. False Sharing](#6-true-sharing-vs-false-sharing)
7. [Alignment Fundamentals](#7-alignment-fundamentals)
8. [Linux Kernel Alignment Macros and Attributes](#8-linux-kernel-alignment-macros-and-attributes)
9. [Userspace Alignment Techniques](#9-userspace-alignment-techniques)
10. [C Implementations: Comprehensive Examples](#10-c-implementations-comprehensive-examples)
11. [Go Implementations: Comprehensive Examples](#11-go-implementations-comprehensive-examples)
12. [Rust Implementations: Comprehensive Examples](#12-rust-implementations-comprehensive-examples)
13. [Padding Strategies and Struct Layout](#13-padding-strategies-and-struct-layout)
14. [NUMA (Non-Uniform Memory Access) and Cache Alignment](#14-numa-non-uniform-memory-access-and-cache-alignment)
15. [Atomic Operations and Cache Lines](#15-atomic-operations-and-cache-lines)
16. [Lock-Free Data Structures with Cache Alignment](#16-lock-free-data-structures-with-cache-alignment)
17. [Linux Kernel Data Structure Deep Dive](#17-linux-kernel-data-structure-deep-dive)
18. [DMA (Direct Memory Access) Alignment](#18-dma-direct-memory-access-alignment)
19. [Memory Barriers and Cache Flushing](#19-memory-barriers-and-cache-flushing)
20. [Performance Measurement and Profiling Tools](#20-performance-measurement-and-profiling-tools)
21. [Advanced Patterns and Mental Models](#21-advanced-patterns-and-mental-models)
22. [Common Pitfalls and Anti-Patterns](#22-common-pitfalls-and-anti-patterns)
23. [Quick Reference Card](#23-quick-reference-card)

---

## 1. Foundational Concepts: The Memory Hierarchy

Before we can understand cache-line alignment, we must understand *why caches exist* and what problem they solve.

### The Speed Mismatch Problem

Modern CPUs operate at ~3–5 GHz. DRAM (main memory) has a latency of ~60–100 nanoseconds. This mismatch — called the **memory wall** — means a CPU could execute 200–400 instructions in the time it waits for one memory access.

```
MEMORY HIERARCHY (approximate values for a modern x86 CPU)
===========================================================

  CPU Core
  ┌─────────────────────────────────────────────────────┐
  │  Registers  │  ~0.3ns  │  ~3.4GB/s  │  32–64 regs  │
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │  L1 Cache (I$ + D$)  │  ~1ns   │  ~1TB/s  │  32KB  │
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │  L2 Cache             │  ~4ns   │  ~400GB/s │  256KB│
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │  L3 Cache (shared)    │  ~10ns  │  ~100GB/s │  6–30MB│
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │  DRAM (Main Memory)   │  ~60ns  │  ~50GB/s  │  GBs  │
  └──────────────────────────┬──────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────┐
  │  NVMe SSD             │  ~100μs │  ~7GB/s   │  TBs  │
  └─────────────────────────────────────────────────────┘
```

> **Mental Model:** Think of registers as your desk, L1 as a drawer beside you, L2 as a cabinet in the room, L3 as a filing room down the hall, and DRAM as a warehouse a mile away. You only go to the warehouse when absolutely necessary.

### The Locality Principle

Caches work because programs exhibit **spatial** and **temporal** locality:

- **Temporal locality:** If you access address X, you will likely access X again soon (e.g., loop variables).
- **Spatial locality:** If you access address X, you will likely access X+1, X+2, etc. soon (e.g., array iteration).

Cache-line alignment is about *leveraging* spatial locality and *preventing* the destruction of it.

---

## 2. What Is a Cache Line?

A **cache line** (also called a cache block) is the fundamental unit of data transfer between main memory and the CPU cache. It is **not** a single byte or word — it is a contiguous chunk of memory.

### Size of a Cache Line

On virtually all modern x86, x86-64, ARM, and RISC-V processors, a cache line is **64 bytes**.

```
A 64-byte cache line in memory:
================================

Physical Address
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Byte 0 │ Byte 1 │ Byte 2 │ ... │ Byte 30 │ Byte 31 │ ... │ Byte 62 │ Byte 63│
└────────────────────────────────────────────────────────────────────────────┘
▲                                                                            ▲
│                                                                            │
start (cache-line-aligned address, e.g. 0xFFFF_FFC0)              end (+63)

The start address is ALWAYS a multiple of 64:
  0x0000, 0x0040, 0x0080, 0x00C0, ...
  In binary: last 6 bits are always 0
```

### What Happens on a Cache Miss

When the CPU needs data at address `A`:
1. CPU checks L1 cache → **Miss**
2. CPU checks L2 cache → **Miss**
3. CPU checks L3 cache → **Miss**
4. CPU calculates the cache-line-aligned address: `aligned = A & ~63` (mask last 6 bits)
5. CPU fetches **the entire 64-byte cache line** from DRAM
6. Cache line is loaded into L1, L2, L3
7. CPU reads the specific bytes it needs

```
CACHE MISS FLOW
===============

CPU requests byte at address 0x1005
                │
                ▼
    ┌───────────────────────┐
    │  L1 miss: 0x1005      │──── Not found
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  L2 miss: 0x1005      │──── Not found
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  L3 miss: 0x1005      │──── Not found
    └───────────────────────┘
                │
                ▼
    ┌─────────────────────────────────────────┐
    │  DRAM: fetch 64 bytes                   │
    │  aligned_addr = 0x1005 & ~63 = 0x10C0  │
    │  Fetch bytes [0x10C0 ... 0x10FF]        │
    └─────────────────────────────────────────┘
                │
                ▼
    ┌─────────────────────────────────────────┐
    │  Fill cache line in L3, L2, L1          │
    │  Extract byte at 0x1005 → CPU register  │
    └─────────────────────────────────────────┘
```

### Key Insight

Because **64 bytes are always fetched together**, your data layout determines whether those 64 bytes contain useful, related data (good — spatial locality) or wasted bytes (bad — cache inefficiency).

---

## 3. Cache Geometry and Organization

Understanding how caches are *indexed and tagged* is essential for advanced alignment strategies.

### Cache Structure: Sets, Ways, Lines

A cache is organized as a **set-associative** structure:

```
N-WAY SET-ASSOCIATIVE CACHE STRUCTURE
======================================

Cache is divided into SETS. Each set has N WAYS (N cache lines).

  Set 0:  [ Way 0: line ] [ Way 1: line ] [ Way 2: line ] [ Way 3: line ]
  Set 1:  [ Way 0: line ] [ Way 1: line ] [ Way 2: line ] [ Way 3: line ]
  Set 2:  [ Way 0: line ] [ Way 1: line ] [ Way 2: line ] [ Way 3: line ]
  ...
  Set S:  [ Way 0: line ] [ Way 1: line ] [ Way 2: line ] [ Way 3: line ]

A physical address maps to ONE set, but can occupy ANY way within that set.
```

### Address Decomposition

A 64-bit physical address is split into three fields:

```
ADDRESS BIT DECOMPOSITION (example: 32KB, 8-way, 64B line L1)
===============================================================

  63       12 11      6 5      0
  ┌──────────┬─────────┬────────┐
  │   TAG    │  INDEX  │ OFFSET │
  │  52 bits │  6 bits │ 6 bits │
  └──────────┴─────────┴────────┘

  OFFSET (bits 0-5):  Position within the 64-byte cache line
  INDEX  (bits 6-11): Which set in the cache
  TAG    (bits 12+):  Identifies which memory block occupies this line

  Number of sets = Cache Size / (Line Size × Associativity)
                 = 32768 / (64 × 8) = 64 sets
  INDEX bits = log2(64) = 6 bits
  OFFSET bits = log2(64) = 6 bits
```

### Cache Thrashing

If two frequently-used variables map to the **same cache set** but different addresses, they will evict each other repeatedly. This is **cache thrashing** — alignment can cause or fix it.

```
CACHE THRASHING SCENARIO
=========================

Array A starts at address: 0x0000  → maps to Set 0
Array B starts at address: 0x8000  → also maps to Set 0
  (both are multiples of 32KB = cache size)

Access A[0] → loads Set 0, Way 0
Access B[0] → loads Set 0, Way 0 (evicts A[0] if 1-way!)
Access A[0] → Miss! Reload from DRAM
Access B[0] → Miss! Reload from DRAM
...  ← THRASHING
```

---

## 4. Cache Coherency Protocols (MESI/MESIF/MOESI)

In multi-core systems, each core has its own L1/L2 cache. When multiple cores access the same memory, they must coordinate. This is **cache coherency**.

### MESI Protocol States

Each cache line in a multi-core system is always in one of these states:

```
MESI PROTOCOL STATE DIAGRAM
============================

        ┌────────────────────────────────────────────┐
        │                                            │
        ▼                                            │
  ┌──────────┐  write hit    ┌──────────┐            │
  │          │◄──────────────│          │            │
  │  Modified│               │ Exclusive│            │
  │   (M)    │───────────────►  (E)     │            │
  └──────────┘  other reads  └──────────┘            │
       │                          │                  │
       │ other cache              │ other cache      │
       │ reads (snoop)            │ reads            │
       ▼                          ▼                  │
  ┌──────────┐               ┌──────────┐            │
  │  Shared  │               │ Invalid  │────────────┘
  │   (S)    │◄──────────────│  (I)     │ read miss or write
  └──────────┘               └──────────┘

  M = Modified:  Only this cache has it; data is dirty (not written to DRAM yet)
  E = Exclusive: Only this cache has it; data matches DRAM (clean)
  S = Shared:    Multiple caches have it; data matches DRAM (read-only effectively)
  I = Invalid:   Line is stale/not present; must fetch on next access
```

### Why This Matters for Alignment

When Core 0 writes to a cache line, it must:
1. Send an **invalidation message** to all other cores that hold the same line
2. Wait for acknowledgement

This is called an **RFO (Read For Ownership)** request. If two cores are frequently writing to **different variables that share the same cache line**, every write by one core invalidates the other core's copy — even though they're writing to *different* logical variables. This is the essence of **false sharing**.

---

## 5. False Sharing: The Silent Performance Killer

**False sharing** occurs when two or more threads on different cores access *different* variables that happen to reside on the *same* cache line. Despite touching logically separate data, the cache coherency protocol treats the entire line as shared, causing performance to degrade.

### Visualizing False Sharing

```
FALSE SHARING SCENARIO
=======================

Memory layout of struct Counters:
  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
  │ctr[0]│ctr[1]│ctr[2]│ctr[3]│ctr[4]│ctr[5]│ctr[6]│ctr[7]│
  │ 8B   │ 8B   │ 8B   │ 8B   │ 8B   │ 8B   │ 8B   │ 8B   │
  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
  ←──────────────── ONE 64-BYTE CACHE LINE ──────────────────→

  Core 0 owns ctr[0] — writes to it constantly
  Core 1 owns ctr[1] — writes to it constantly
  Core 2 owns ctr[2] — writes to it constantly
  Core 3 owns ctr[3] — writes to it constantly

WHAT HAPPENS EACH WRITE:
  Core 0 writes ctr[0]
    → Invalidates cache line on Core 1, 2, 3
    → Core 1, 2, 3 must reload from L3/DRAM on next access!

  Core 1 writes ctr[1]
    → Invalidates cache line on Core 0, 2, 3
    → Core 0, 2, 3 must reload!

  ... this repeats with EVERY WRITE from EVERY CORE

Performance: ~10x–100x SLOWER than necessary

THE FIX — Pad each counter to its own cache line:
  ┌──────┬──────────────────────────────────────────────────┐
  │ctr[0]│  padding (56 bytes)                              │
  └──────┴──────────────────────────────────────────────────┘
  ←──────────────── ONE 64-BYTE CACHE LINE ──────────────────→
  ┌──────┬──────────────────────────────────────────────────┐
  │ctr[1]│  padding (56 bytes)                              │
  └──────┴──────────────────────────────────────────────────┘
  ←──────────────── ONE 64-BYTE CACHE LINE ──────────────────→
  ...

Now Core 0's writes never touch Core 1's cache line. No coherency traffic!
```

### Performance Impact Example

| Scenario | Throughput | Latency |
|---|---|---|
| 8 threads, shared cache line (false sharing) | ~50M ops/sec | ~200ns/op |
| 8 threads, padded to separate cache lines | ~800M ops/sec | ~1.2ns/op |

**16x speedup** just from layout change.

---

## 6. True Sharing vs. False Sharing

It's critical to distinguish between these two:

```
TRUE SHARING vs FALSE SHARING
==============================

TRUE SHARING:
  Two threads access the SAME variable.
  Communication is intentional (e.g., mutex, flag, queue node).
  Coherency traffic is NECESSARY.
  → Cannot be eliminated by alignment alone.
  → Must use synchronization (atomics, locks, barriers).

  Thread A writes: flag = 1;
  Thread B reads:  while(flag == 0) {}
  Both access: flag  ← same variable, same bytes
  → Traffic is the POINT. You want B to see A's write.

FALSE SHARING:
  Two threads access DIFFERENT variables.
  They share a cache line only by ACCIDENT.
  Coherency traffic is UNNECESSARY overhead.
  → CAN be eliminated by alignment/padding.
  → No synchronization needed between those variables.

  Thread A writes: counter_a++  (byte 0..7)
  Thread B writes: counter_b++  (byte 8..15)
  Both live on same cache line [0..63]
  → Traffic is ACCIDENTAL. B's work invalidates A's cache.
```

---

## 7. Alignment Fundamentals

### What Is Memory Alignment?

A variable of size `N` bytes is **naturally aligned** when its address is a multiple of `N`.

```
NATURAL ALIGNMENT RULES
========================

  Type      Size  Aligned when address is multiple of
  ───────── ────  ──────────────────────────────────
  char        1   any address (always aligned)
  short       2   2 (last bit = 0)
  int         4   4 (last 2 bits = 00)
  long        8   8 (last 3 bits = 000)
  double      8   8 (last 3 bits = 000)
  __m128     16  16 (last 4 bits = 0000)
  __m256     32  32 (last 5 bits = 00000)
  cache line 64  64 (last 6 bits = 000000)
  SIMD 512  512  512 (last 9 bits = 000000000)

MISALIGNED ACCESS EXAMPLE:
  int* p = (int*)(char_array + 1);  // address ends in ...001
  *p = 42;  // MISALIGNED!
  
  On x86: works but slower (hardware handles it with extra cycle)
  On ARM: may CRASH with SIGBUS (alignment fault)
  On RISC-V: depends on implementation
```

### Alignment in Action: Struct Padding

The compiler inserts **padding** between struct members to maintain natural alignment:

```
STRUCT WITHOUT __attribute__((packed)):
========================================

struct Example {
    char   a;   // 1 byte at offset 0
                // 3 bytes PADDING inserted by compiler
    int    b;   // 4 bytes at offset 4 (must be 4-aligned)
    char   c;   // 1 byte at offset 8
                // 7 bytes PADDING inserted by compiler
    double d;   // 8 bytes at offset 16 (must be 8-aligned)
};              // Total: 24 bytes

Memory layout:
 Offset: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
         ┌──┬──┬──┬──┬──────────┬──┬──┬──┬──┬──┬──┬──┬──────────────────────────┐
         │a │  │  │  │    b     │c │  │  │  │  │  │  │           d              │
         └──┴──┴──┴──┴──────────┴──┴──┴──┴──┴──┴──┴──┴──────────────────────────┘
              pad(3)               pad(7)

struct __attribute__((packed)) Example { ... };  // Total: 14 bytes, but MISALIGNED
```

### Cache-Line Alignment

Cache-line alignment means ensuring a struct or variable **starts at a multiple of 64 bytes**, so it doesn't straddle two cache lines:

```
STRUCT STRADDLING TWO CACHE LINES (BAD):
=========================================

struct Node { int key; int value; };  // 8 bytes

If placed at address 0x003C (60 decimal):
  Cache line 1: [0x0000 ... 0x003F]  contains bytes 0..3 of Node
  Cache line 2: [0x0040 ... 0x007F]  contains bytes 4..7 of Node

Accessing Node.value crosses a cache line boundary!
  → 2 cache line fetches instead of 1
  → 2x worse if both lines aren't cached

STRUCT PROPERLY ALIGNED (GOOD):
=================================

__attribute__((aligned(64))) struct Node { int key; int value; };

Placed at address 0x0040 (64 decimal):
  Cache line:  [0x0040 ... 0x007F]  contains all 8 bytes of Node

Accessing any member: only 1 cache line fetch!
```

---

## 8. Linux Kernel Alignment Macros and Attributes

The Linux kernel provides a rich set of macros for cache-line alignment. These are defined in various header files.

### Core Definitions

```c
/* From: include/linux/cache.h */

/* L1_CACHE_BYTES: Size of a cache line on the current arch */
#ifndef L1_CACHE_BYTES
#define L1_CACHE_BYTES  (1 << L1_CACHE_SHIFT)
#endif

/* On x86-64: L1_CACHE_SHIFT = 6, so L1_CACHE_BYTES = 64 */
/* On ARM64:  L1_CACHE_SHIFT = 6, so L1_CACHE_BYTES = 64 */
/* On PowerPC: varies, can be 64 or 128                   */

/* SMP_CACHE_BYTES: cache line size for SMP coherency purposes */
#ifndef SMP_CACHE_BYTES
#define SMP_CACHE_BYTES L1_CACHE_BYTES
#endif
```

### Alignment Macros

```c
/* From: include/linux/cache.h and include/linux/compiler_attributes.h */

/* 1. __cacheline_aligned
 *    Aligns to L1_CACHE_BYTES.
 *    Use for variables that should start at a cache line boundary.
 *    Works in both UP (uniprocessor) and SMP builds.
 */
#define __cacheline_aligned                                     \
    __attribute__((__aligned__(SMP_CACHE_BYTES)))

/* 2. ____cacheline_aligned
 *    Same as __cacheline_aligned but also forces the struct/var
 *    into the ".data..cacheline_aligned" ELF section.
 *    Use for performance-critical global kernel data.
 */
#define ____cacheline_aligned                                   \
    __attribute__((__aligned__(SMP_CACHE_BYTES)))               \
    __section(".data..cacheline_aligned")

/* 3. ____cacheline_aligned_in_smp
 *    Only aligns in SMP builds (CONFIG_SMP=y).
 *    In UP builds, produces no alignment (saves memory on single-CPU systems).
 *    This is the MOST COMMON in kernel hot paths.
 */
#ifdef CONFIG_SMP
#define ____cacheline_aligned_in_smp ____cacheline_aligned
#else
#define ____cacheline_aligned_in_smp
#endif

/* 4. __cacheline_internodealigned_in_smp
 *    Aligns to INTERNODE_CACHE_BYTES (often 2× cache line for NUMA).
 *    Used for data shared across NUMA nodes.
 */
#ifdef CONFIG_SMP
#define __cacheline_internodealigned_in_smp                     \
    __attribute__((__aligned__(1 << INTERNODE_CACHE_SHIFT)))
#else
#define __cacheline_internodealigned_in_smp
#endif
```

### Usage in Kernel Code

```c
/* Example 1: Per-CPU counter aligned to avoid false sharing */
/* From: kernel/sched/core.c style */
struct rq {
    /* ... scheduler run queue fields ... */
    unsigned long   nr_running;
    unsigned long   nr_switches;
    /* Force next group of fields to a new cache line */
    unsigned long   load_weight;
} ____cacheline_aligned_in_smp;

/* Example 2: Lock aligned to its own cache line */
/* This prevents the lock variable from being on the same
 * line as the data it protects, which would cause contention */
spinlock_t my_lock ____cacheline_aligned_in_smp;
unsigned long protected_data;  /* on a different line now */

/* Example 3: Hot/cold data separation in a struct */
struct my_object {
    /* HOT data — accessed on every operation */
    atomic_t    refcount;
    u32         flags;
    void        *data_ptr;
    
    /* Force cold data to next cache line */
    char        __pad[L1_CACHE_BYTES - 
                      sizeof(atomic_t) - sizeof(u32) - sizeof(void*)];
    
    /* COLD data — accessed rarely */
    char        name[64];
    struct list_head list;
    ktime_t     creation_time;
};
```

### CACHELINE_ALIGN Macro

```c
/* From: include/linux/log2.h and various */

/* ALIGN(x, a): round x up to the next multiple of a */
#define ALIGN(x, a)         __ALIGN_KERNEL((x), (a))
#define __ALIGN_KERNEL(x, a)    __ALIGN_KERNEL_MASK(x, (typeof(x))(a) - 1)
#define __ALIGN_KERNEL_MASK(x, mask)    (((x) + (mask)) & ~(mask))

/* Usage: align a size to cache line boundary */
#define CACHELINE_ALIGN(x)  ALIGN(x, L1_CACHE_BYTES)

/* Example: ensure a buffer is a multiple of cache line size */
size_t buf_size = CACHELINE_ALIGN(user_requested_size);
/* If user_requested_size = 100:
 *   CACHELINE_ALIGN(100) = (100 + 63) & ~63 = 163 & ~63 = 128 */
```

### __read_mostly Attribute

```c
/* Variables marked __read_mostly are placed in a section
 * where frequently-read, rarely-written data lives.
 * This keeps them together in cache and avoids pollution
 * from write-heavy data. */
#define __read_mostly __section(".data..read_mostly")

/* Kernel examples: */
int sysctl_sched_latency __read_mostly = 6000000ULL;
int numa_migrate_retry __read_mostly = 3;
```

### __ro_after_init

```c
/* Data that is written once during init, then read-only forever.
 * Placed in a protected section that becomes read-only after init. */
#define __ro_after_init __section(".data..ro_after_init")

/* Example: */
static unsigned int cache_line_size __ro_after_init;

static int __init detect_cache_line_size(void)
{
    cache_line_size = boot_cpu_data.x86_cache_alignment;
    return 0;
}
```

---

## 9. Userspace Alignment Techniques

### C11 `alignas` and `_Alignas`

```c
#include <stdalign.h>  /* C11 */

/* alignas(N): align a variable or struct to N bytes */
alignas(64) int counter;              /* 64-byte aligned variable */
alignas(64) struct MyStruct { ... };  /* struct aligned to 64 bytes */

/* Get alignment of a type */
size_t align = alignof(int);          /* usually 4 */
size_t cache = alignof(max_align_t);  /* max fundamental alignment */
```

### GCC/Clang `__attribute__((aligned(N)))`

```c
/* Method 1: On variable declaration */
int counter __attribute__((aligned(64)));

/* Method 2: On struct/typedef */
struct __attribute__((aligned(64))) PaddedCounter {
    long value;
};

/* Method 3: Via typedef */
typedef long aligned_counter_t __attribute__((aligned(64)));
aligned_counter_t counters[16];
```

### Dynamic Aligned Allocation

```c
#include <stdlib.h>
#include <malloc.h>

/* POSIX: posix_memalign */
void *ptr;
int ret = posix_memalign(&ptr, 64, size);  /* 64-byte aligned */
if (ret != 0) { /* handle error */ }
free(ptr);

/* C11: aligned_alloc (size must be multiple of alignment) */
void *buf = aligned_alloc(64, CACHELINE_ALIGN(size));
free(buf);

/* Linux-specific: memalign (deprecated but still works) */
void *p = memalign(64, size);
free(p);

/* Checking if allocated memory is aligned */
uintptr_t addr = (uintptr_t)ptr;
if (addr % 64 != 0) {
    fprintf(stderr, "Not aligned!\n");
}
/* Efficient check using bit mask: */
if (addr & 63) {
    fprintf(stderr, "Not aligned!\n");
}
```

### Linux-Specific Aligned Allocation

```c
#include <linux/slab.h>  /* kernel space */

/* kmalloc: kernel allocates naturally aligned memory for power-of-2 sizes */
void *p = kmalloc(64, GFP_KERNEL);   /* guaranteed 64-byte aligned */
void *q = kmalloc(128, GFP_KERNEL);  /* guaranteed 128-byte aligned */
void *r = kmalloc(100, GFP_KERNEL);  /* NOT guaranteed 64-byte aligned */

/* kmem_cache: slab allocator with alignment control */
struct kmem_cache *cache;
cache = kmem_cache_create(
    "my_objects",          /* name */
    sizeof(struct MyObj),  /* size */
    __alignof__(struct MyObj), /* alignment */
    SLAB_HWCACHE_ALIGN,    /* flags: align to cache line */
    NULL                   /* constructor */
);
struct MyObj *obj = kmem_cache_alloc(cache, GFP_KERNEL);
```

---

## 10. C Implementations: Comprehensive Examples

### Example 1: False Sharing Demonstration

```c
/* false_sharing_demo.c
 * Compile: gcc -O2 -pthread -o false_sharing false_sharing_demo.c
 * 
 * This demonstrates the performance difference between
 * false sharing and cache-line padded counters.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdint.h>
#include <time.h>
#include <string.h>

#define NUM_THREADS     8
#define ITERATIONS      100000000ULL
#define CACHE_LINE_SIZE 64

/* ============================================================
 * BAD: All counters on the same cache line
 * When Thread 0 writes counter[0], it invalidates the cache
 * line for ALL other threads.
 * ============================================================ */
typedef struct {
    long counters[NUM_THREADS];  /* 8 * 8 = 64 bytes: ONE cache line */
} BadCounters;

/* ============================================================
 * GOOD: Each counter on its own cache line
 * Padding fills the rest of the 64-byte line.
 * Each thread operates on its own independent cache line.
 * ============================================================ */
typedef struct {
    long value;
    /* pad to fill the rest of the 64-byte cache line */
    char pad[CACHE_LINE_SIZE - sizeof(long)];
} PaddedCounter;

typedef struct {
    PaddedCounter counters[NUM_THREADS];
} GoodCounters;

/* Thread argument */
typedef struct {
    int    thread_id;
    void  *counters_ptr;
    int    use_padded;
} ThreadArg;

/* Thread function for BAD case */
void *bad_thread(void *arg)
{
    ThreadArg *ta = (ThreadArg *)arg;
    BadCounters *bc = (BadCounters *)ta->counters_ptr;
    int tid = ta->thread_id;
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        bc->counters[tid]++;  /* writes to shared cache line */
    }
    return NULL;
}

/* Thread function for GOOD case */
void *good_thread(void *arg)
{
    ThreadArg *ta = (ThreadArg *)arg;
    GoodCounters *gc = (GoodCounters *)ta->counters_ptr;
    int tid = ta->thread_id;
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        gc->counters[tid].value++;  /* writes to isolated cache line */
    }
    return NULL;
}

/* Get nanosecond timestamp */
static inline uint64_t get_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

int main(void)
{
    pthread_t threads[NUM_THREADS];
    ThreadArg args[NUM_THREADS];
    uint64_t start, end;
    
    /* Verify alignment */
    printf("BadCounters size:    %zu bytes\n", sizeof(BadCounters));
    printf("GoodCounters size:   %zu bytes\n", sizeof(GoodCounters));
    printf("PaddedCounter size:  %zu bytes\n", sizeof(PaddedCounter));
    printf("CACHE_LINE_SIZE:     %d bytes\n\n", CACHE_LINE_SIZE);
    
    /* ==== TEST 1: False Sharing ==== */
    BadCounters *bad = aligned_alloc(CACHE_LINE_SIZE, sizeof(BadCounters));
    memset(bad, 0, sizeof(BadCounters));
    
    start = get_ns();
    for (int t = 0; t < NUM_THREADS; t++) {
        args[t].thread_id   = t;
        args[t].counters_ptr = bad;
        args[t].use_padded  = 0;
        pthread_create(&threads[t], NULL, bad_thread, &args[t]);
    }
    for (int t = 0; t < NUM_THREADS; t++)
        pthread_join(threads[t], NULL);
    end = get_ns();
    
    long bad_sum = 0;
    for (int t = 0; t < NUM_THREADS; t++)
        bad_sum += bad->counters[t];
    printf("[FALSE SHARING]  Time: %7.3f ms | Sum: %ld\n",
           (end - start) / 1e6, bad_sum);
    free(bad);
    
    /* ==== TEST 2: Cache-Line Padded ==== */
    GoodCounters *good = aligned_alloc(CACHE_LINE_SIZE, sizeof(GoodCounters));
    memset(good, 0, sizeof(GoodCounters));
    
    start = get_ns();
    for (int t = 0; t < NUM_THREADS; t++) {
        args[t].thread_id   = t;
        args[t].counters_ptr = good;
        args[t].use_padded  = 1;
        pthread_create(&threads[t], NULL, good_thread, &args[t]);
    }
    for (int t = 0; t < NUM_THREADS; t++)
        pthread_join(threads[t], NULL);
    end = get_ns();
    
    long good_sum = 0;
    for (int t = 0; t < NUM_THREADS; t++)
        good_sum += good->counters[t].value;
    printf("[PADDED COUNTER] Time: %7.3f ms | Sum: %ld\n",
           (end - start) / 1e6, good_sum);
    free(good);
    
    return 0;
}
```

### Example 2: Cache-Line Aligned Ring Buffer (Lock-Free SPSC)

```c
/* spsc_ringbuf.h
 * Single-Producer, Single-Consumer ring buffer.
 * Cache-line aware design:
 *   - head (writer) on its own cache line
 *   - tail (reader) on its own cache line
 *   - buffer data follows (no sharing with head/tail)
 *
 * This is a common pattern in high-performance I/O, networking,
 * and audio processing.
 */

#ifndef SPSC_RINGBUF_H
#define SPSC_RINGBUF_H

#include <stdint.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define CACHE_LINE 64
#define ALIGN64     __attribute__((aligned(CACHE_LINE)))

/* ============================================================
 * LAYOUT VISUALIZATION:
 *
 *  ┌──────────────────────────────────────────────────────────┐
 *  │  Cache Line 0: head (write index, owned by producer)     │
 *  │  [_Atomic uint64_t head | padding to 64 bytes]           │
 *  ├──────────────────────────────────────────────────────────┤
 *  │  Cache Line 1: tail (read index, owned by consumer)      │
 *  │  [_Atomic uint64_t tail | padding to 64 bytes]           │
 *  ├──────────────────────────────────────────────────────────┤
 *  │  Cache Line 2: metadata (capacity, element_size)         │
 *  │  read-only after init, shared but rarely written         │
 *  ├──────────────────────────────────────────────────────────┤
 *  │  Data buffer (heap-allocated, cache-line aligned)        │
 *  │  capacity * element_size bytes                           │
 *  └──────────────────────────────────────────────────────────┘
 *
 * Producer touches: head (Cache Line 0), buffer data
 * Consumer touches: tail (Cache Line 1), buffer data
 * → Zero false sharing between producer and consumer!
 * ============================================================ */

typedef struct {
    /* Producer-owned: producer writes head, consumer reads it */
    struct {
        _Atomic uint64_t head;
        /* Pad to exactly one cache line so tail is on a different line */
        char _pad[CACHE_LINE - sizeof(_Atomic uint64_t)];
    } ALIGN64 producer;
    
    /* Consumer-owned: consumer writes tail, producer reads it */
    struct {
        _Atomic uint64_t tail;
        char _pad[CACHE_LINE - sizeof(_Atomic uint64_t)];
    } ALIGN64 consumer;
    
    /* Read-only after init: no cache coherency concerns */
    uint64_t capacity;
    size_t   element_size;
    uint8_t  *buffer;
} spsc_ring_t;

/* Initialize the ring buffer.
 * capacity MUST be a power of 2 (for fast modulo via bitmasking).
 * element_size: size of each element in bytes.
 */
int spsc_init(spsc_ring_t *ring, uint64_t capacity, size_t element_size)
{
    /* Verify power of 2 */
    if (capacity == 0 || (capacity & (capacity - 1)) != 0)
        return -1;
    
    atomic_store_explicit(&ring->producer.head, 0, memory_order_relaxed);
    atomic_store_explicit(&ring->consumer.tail, 0, memory_order_relaxed);
    ring->capacity     = capacity;
    ring->element_size = element_size;
    
    /* Allocate cache-line aligned buffer */
    ring->buffer = aligned_alloc(CACHE_LINE, capacity * element_size);
    if (!ring->buffer) return -1;
    
    return 0;
}

void spsc_destroy(spsc_ring_t *ring)
{
    free(ring->buffer);
    ring->buffer = NULL;
}

/* Producer: push one element.
 * Returns true on success, false if ring is full.
 *
 * Memory ordering analysis:
 *   - Load tail with 'acquire': sees all writes by consumer
 *   - Store head with 'release': consumer sees element before head update
 */
bool spsc_push(spsc_ring_t *ring, const void *elem)
{
    uint64_t head = atomic_load_explicit(&ring->producer.head,
                                         memory_order_relaxed);
    uint64_t tail = atomic_load_explicit(&ring->consumer.tail,
                                         memory_order_acquire);
    
    /* Check if full: head - tail == capacity */
    if (head - tail >= ring->capacity)
        return false;  /* full */
    
    /* Write element to buffer slot */
    uint64_t slot = head & (ring->capacity - 1);  /* fast modulo */
    memcpy(ring->buffer + slot * ring->element_size, elem, ring->element_size);
    
    /* Publish: advance head with release semantics
     * This acts as a memory barrier — the memcpy above is visible
     * to the consumer BEFORE head is incremented */
    atomic_store_explicit(&ring->producer.head, head + 1,
                          memory_order_release);
    return true;
}

/* Consumer: pop one element.
 * Returns true on success, false if ring is empty.
 */
bool spsc_pop(spsc_ring_t *ring, void *elem)
{
    uint64_t tail = atomic_load_explicit(&ring->consumer.tail,
                                         memory_order_relaxed);
    uint64_t head = atomic_load_explicit(&ring->producer.head,
                                         memory_order_acquire);
    
    /* Check if empty */
    if (head == tail)
        return false;  /* empty */
    
    /* Read element from buffer slot */
    uint64_t slot = tail & (ring->capacity - 1);
    memcpy(elem, ring->buffer + slot * ring->element_size, ring->element_size);
    
    /* Advance tail with release semantics */
    atomic_store_explicit(&ring->consumer.tail, tail + 1,
                          memory_order_release);
    return true;
}

#endif /* SPSC_RINGBUF_H */
```

### Example 3: Hot/Cold Data Splitting

```c
/* hot_cold_split.c
 * Demonstrates splitting struct fields into hot and cold regions.
 * Hot fields (accessed on every operation) are grouped at the
 * beginning of the struct to maximize cache efficiency.
 * Cold fields (accessed rarely, e.g., on errors or init) are
 * pushed to later cache lines.
 */

#include <stdint.h>
#include <string.h>

#define CACHE_LINE 64

/* BAD: Mixed hot and cold fields.
 * A cache miss on any field pulls in ALL fields.
 * The 128-byte struct needs 2 cache lines even for a simple lookup.
 */
struct BadNetworkSocket_Slow {
    /* COLD: set once at creation time */
    char     remote_addr[64];   /* 64 bytes — dominates the struct! */
    uint16_t remote_port;
    
    /* HOT: accessed on every packet */
    int      fd;
    uint32_t state;
    uint64_t bytes_sent;
    uint64_t bytes_recv;
    void    *recv_buffer;
    
    /* COLD: error info, rarely accessed */
    int      last_error;
    char     error_msg[32];
};

/* GOOD: Hot data packed in first cache line.
 * Only 64 bytes needed for normal operations.
 * Cold data sits in subsequent cache lines — only loaded on cache miss
 * when actually needed (error handling, logging, etc.)
 */
struct __attribute__((aligned(64))) GoodNetworkSocket {
    /* ── CACHE LINE 0: HOT PATH ──────────────────────────── */
    int      fd;              /* 4 bytes */
    uint32_t state;           /* 4 bytes */
    uint64_t bytes_sent;      /* 8 bytes */
    uint64_t bytes_recv;      /* 8 bytes */
    void    *recv_buffer;     /* 8 bytes */
    void    *send_buffer;     /* 8 bytes */
    uint32_t recv_buf_len;    /* 4 bytes */
    uint32_t send_buf_len;    /* 4 bytes */
    uint16_t local_port;      /* 2 bytes */
    uint8_t  protocol;        /* 1 byte  */
    uint8_t  flags;           /* 1 byte  */
    /* Total hot: 52 bytes. Pad to 64. */
    char     _hot_pad[12];    /* 12 bytes padding */
    /* ── CACHE LINE 1: COLD PATH ─────────────────────────── */
    char     remote_addr[64]; /* 64 bytes: only loaded when needed */
    /* ── CACHE LINE 2: ERROR/DEBUG ──────────────────────── */
    uint16_t remote_port;     /* 2 bytes */
    int      last_error;      /* 4 bytes */
    char     error_msg[58];   /* 58 bytes */
};

/* Demonstrate: counting struct size and layout */
#include <stdio.h>
#include <stddef.h>

void print_socket_layout(void)
{
    printf("=== Socket Layout Analysis ===\n");
    printf("BadNetworkSocket_Slow:\n");
    printf("  size: %zu bytes (%zu cache lines)\n",
           sizeof(struct BadNetworkSocket_Slow),
           (sizeof(struct BadNetworkSocket_Slow) + 63) / 64);
    
    printf("GoodNetworkSocket:\n");
    printf("  size: %zu bytes (%zu cache lines)\n",
           sizeof(struct GoodNetworkSocket),
           (sizeof(struct GoodNetworkSocket) + 63) / 64);
    printf("  fd offset:          %zu\n", offsetof(struct GoodNetworkSocket, fd));
    printf("  bytes_sent offset:  %zu\n", offsetof(struct GoodNetworkSocket, bytes_sent));
    printf("  remote_addr offset: %zu (cache line %zu)\n",
           offsetof(struct GoodNetworkSocket, remote_addr),
           offsetof(struct GoodNetworkSocket, remote_addr) / 64);
}
```

### Example 4: Per-CPU Variables (Kernel Pattern in Userspace)

```c
/* per_cpu_counters.c
 * Simulates Linux kernel per-CPU variables.
 * Each CPU/thread gets its own cache-line-aligned counter.
 * No locking needed — each thread only touches its own counter.
 * 
 * PATTERN: Used in Linux kernel for:
 *   - per_cpu() variables (schedstat, softirq counts, etc.)
 *   - Network device packet counters
 *   - Memory allocator stats
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdint.h>
#include <sched.h>
#include <unistd.h>

#define CACHE_LINE     64
#define MAX_CPUS       64

/* Each CPU gets its own aligned counter block.
 * The __attribute__((aligned(64))) ensures no two CPUs
 * share a cache line.
 */
typedef struct __attribute__((aligned(CACHE_LINE))) {
    uint64_t value;
    /* Pad to fill exactly one cache line */
    uint8_t  _pad[CACHE_LINE - sizeof(uint64_t)];
} per_cpu_counter_t;

/* Array of per-CPU counters.
 * Total size: MAX_CPUS * 64 = 4096 bytes = 64 cache lines
 * Each thread/CPU has its own line. Zero contention!
 */
static per_cpu_counter_t global_counters[MAX_CPUS]
    __attribute__((aligned(CACHE_LINE)));

/* Get the number of CPUs online */
static int num_cpus(void) {
    return sysconf(_SC_NPROCESSORS_ONLN);
}

/* Pin thread to a specific CPU */
static void pin_to_cpu(int cpu_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
}

typedef struct {
    int      cpu_id;
    uint64_t iterations;
} WorkerArg;

void *worker(void *arg) {
    WorkerArg *wa = (WorkerArg *)arg;
    pin_to_cpu(wa->cpu_id);  /* bind to specific CPU */
    
    per_cpu_counter_t *my_counter = &global_counters[wa->cpu_id];
    
    for (uint64_t i = 0; i < wa->iterations; i++) {
        my_counter->value++;  /* no atomic needed! exclusive access */
    }
    return NULL;
}

/* Read total across all CPUs — done rarely (e.g., for stats reporting) */
uint64_t read_total(int num_threads) {
    uint64_t total = 0;
    for (int i = 0; i < num_threads; i++) {
        total += global_counters[i].value;
    }
    return total;
}

int main(void) {
    int ncpus = num_cpus();
    if (ncpus > MAX_CPUS) ncpus = MAX_CPUS;
    
    printf("Using %d CPUs\n", ncpus);
    printf("Counter array size: %zu bytes\n", sizeof(global_counters));
    printf("Each counter aligned to: %d bytes\n", CACHE_LINE);
    printf("Offset of counter[0]: 0x%zx\n", (size_t)&global_counters[0] & 63);
    printf("Offset of counter[1]: 0x%zx\n", (size_t)&global_counters[1] & 63);
    
    pthread_t threads[MAX_CPUS];
    WorkerArg args[MAX_CPUS];
    
    for (int i = 0; i < ncpus; i++) {
        args[i].cpu_id     = i;
        args[i].iterations = 100000000ULL;
        pthread_create(&threads[i], NULL, worker, &args[i]);
    }
    for (int i = 0; i < ncpus; i++)
        pthread_join(threads[i], NULL);
    
    printf("Total count: %lu (expected: %lu)\n",
           read_total(ncpus),
           (uint64_t)ncpus * 100000000ULL);
    return 0;
}
```

---

## 11. Go Implementations: Comprehensive Examples

### Terminology for Go Developers

In Go, struct padding is handled by the compiler. The `sync/atomic` package and the `unsafe` package are used for low-level alignment control. Go's garbage collector moves objects, but the Go runtime guarantees 64-bit alignment for 64-bit values on all platforms.

### Example 1: False Sharing in Go

```go
// false_sharing_go.go
// Demonstrates false sharing in Go and the fix.
// 
// Run: go run false_sharing_go.go
// Build: go build -o bench false_sharing_go.go

package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
	"unsafe"
)

const (
	CacheLineSize = 64
	NumGoroutines = 8
	Iterations    = 100_000_000
)

// ============================================================
// BAD: False Sharing
// All counters packed into a slice — adjacent counters share
// cache lines. When goroutine 0 writes counters[0], it
// invalidates the cache line containing counters[1] too.
// ============================================================

type FalseSharingCounters struct {
	counters [NumGoroutines]int64
}

func benchFalseSharing() time.Duration {
	var c FalseSharingCounters
	var wg sync.WaitGroup

	start := time.Now()
	for g := 0; g < NumGoroutines; g++ {
		wg.Add(1)
		g := g // capture loop variable
		go func() {
			defer wg.Done()
			for i := 0; i < Iterations; i++ {
				c.counters[g]++ // writes to shared cache line!
			}
		}()
	}
	wg.Wait()
	return time.Since(start)
}

// ============================================================
// GOOD: Cache-Line Padding
// Each counter gets its own cache line via a struct with padding.
//
// IMPORTANT Go Detail:
// Go does NOT guarantee cache-line alignment of struct fields
// unless you explicitly add padding. The struct below uses
// [CacheLineSize - unsafe.Sizeof(int64)]byte to pad each counter.
// ============================================================

// PaddedInt64 is an int64 padded to occupy exactly one cache line.
// The unsafe.Sizeof trick computes padding at compile time.
type PaddedInt64 struct {
	val int64
	// Pad to 64 bytes total.
	// CacheLineSize - sizeof(int64) = 64 - 8 = 56 bytes
	_ [CacheLineSize - unsafe.Sizeof(int64(0))]byte
}

type GoodCounters struct {
	counters [NumGoroutines]PaddedInt64
}

func benchGoodCounters() time.Duration {
	var c GoodCounters
	var wg sync.WaitGroup

	start := time.Now()
	for g := 0; g < NumGoroutines; g++ {
		wg.Add(1)
		g := g
		go func() {
			defer wg.Done()
			for i := 0; i < Iterations; i++ {
				c.counters[g].val++ // writes to isolated cache line!
			}
		}()
	}
	wg.Wait()
	return time.Since(start)
}

// ============================================================
// VERIFY: Check sizes and alignment at runtime.
// Note: Go does not expose alignment guarantees via API like C,
// but we can check struct sizes to verify padding.
// ============================================================

func printAlignmentInfo() {
	var c GoodCounters
	fmt.Printf("=== Alignment Analysis ===\n")
	fmt.Printf("CacheLineSize:        %d bytes\n", CacheLineSize)
	fmt.Printf("PaddedInt64 size:     %d bytes (should be %d)\n",
		unsafe.Sizeof(PaddedInt64{}), CacheLineSize)
	fmt.Printf("GoodCounters size:    %d bytes (should be %d)\n",
		unsafe.Sizeof(c), NumGoroutines*CacheLineSize)

	// Print address of each counter to verify no sharing
	for i := 0; i < NumGoroutines; i++ {
		addr := uintptr(unsafe.Pointer(&c.counters[i]))
		fmt.Printf("  counter[%d] at 0x%x (offset from line start: %d)\n",
			i, addr, addr%CacheLineSize)
	}
}

func main() {
	// Use all available CPUs
	runtime.GOMAXPROCS(runtime.NumCPU())

	printAlignmentInfo()
	fmt.Println()

	// Warmup
	benchFalseSharing()
	benchGoodCounters()

	// Measure
	falseTime := benchFalseSharing()
	goodTime := benchGoodCounters()

	fmt.Printf("=== Benchmark Results ===\n")
	fmt.Printf("False sharing:  %v\n", falseTime)
	fmt.Printf("Padded counter: %v\n", goodTime)
	fmt.Printf("Speedup:        %.2fx\n", float64(falseTime)/float64(goodTime))
}
```

### Example 2: Cache-Aligned SPSC Queue in Go

```go
// spsc_queue.go
// Lock-free Single-Producer, Single-Consumer queue.
// Uses cache-line alignment to eliminate false sharing
// between producer state and consumer state.

package main

import (
	"runtime"
	"sync/atomic"
	"unsafe"
)

const (
	cacheLinePad = 64
)

// producerState occupies its own cache line.
// Only the producer goroutine writes to head.
type producerState struct {
	head uint64
	_    [cacheLinePad - unsafe.Sizeof(uint64(0))]byte
}

// consumerState occupies its own cache line.
// Only the consumer goroutine writes to tail.
type consumerState struct {
	tail uint64
	_    [cacheLinePad - unsafe.Sizeof(uint64(0))]byte
}

// SPSCQueue is a lock-free, cache-line-aware ring buffer.
// T is represented as interface{} for generality.
// For production use, consider using generics (Go 1.18+).
//
// LAYOUT:
//   ┌──────────────────────┐  ← 64 bytes (Cache Line 0)
//   │  producer.head       │
//   ├──────────────────────┤  ← 64 bytes (Cache Line 1)
//   │  consumer.tail       │
//   ├──────────────────────┤
//   │  capacity, mask,     │  (read-only after init)
//   │  buffer pointer      │
//   └──────────────────────┘
type SPSCQueue struct {
	producer producerState // Cache Line 0 — written by producer
	consumer consumerState // Cache Line 1 — written by consumer
	capacity uint64
	mask     uint64 // capacity - 1, for fast modulo
	buffer   []unsafe.Pointer
}

// NewSPSCQueue creates a new SPSC queue.
// capacity must be a power of 2.
func NewSPSCQueue(capacity uint64) *SPSCQueue {
	if capacity == 0 || (capacity&(capacity-1)) != 0 {
		panic("capacity must be a power of 2")
	}
	q := &SPSCQueue{
		capacity: capacity,
		mask:     capacity - 1,
		buffer:   make([]unsafe.Pointer, capacity),
	}
	return q
}

// Push enqueues an item. Returns false if queue is full.
// ONLY CALL FROM A SINGLE PRODUCER GOROUTINE.
func (q *SPSCQueue) Push(item interface{}) bool {
	head := atomic.LoadUint64(&q.producer.head)
	tail := atomic.LoadUint64(&q.consumer.tail)

	// Check full: head - tail == capacity
	if head-tail >= q.capacity {
		runtime.Gosched() // yield to allow consumer progress
		return false
	}

	slot := head & q.mask
	// Store item pointer with release semantics
	// (ensures item is visible before head is incremented)
	iface := (*[2]unsafe.Pointer)(unsafe.Pointer(&item))
	atomic.StorePointer(&q.buffer[slot], iface[1]) // store data pointer

	// Publish head
	atomic.StoreUint64(&q.producer.head, head+1)
	return true
}

// Pop dequeues an item. Returns (nil, false) if queue is empty.
// ONLY CALL FROM A SINGLE CONSUMER GOROUTINE.
func (q *SPSCQueue) Pop() (interface{}, bool) {
	tail := atomic.LoadUint64(&q.consumer.tail)
	head := atomic.LoadUint64(&q.producer.head)

	if head == tail {
		return nil, false // empty
	}

	slot := tail & q.mask
	ptr := atomic.LoadPointer(&q.buffer[slot])
	if ptr == nil {
		return nil, false
	}

	// Clear slot and advance tail
	atomic.StorePointer(&q.buffer[slot], nil)
	atomic.StoreUint64(&q.consumer.tail, tail+1)

	// Reconstruct interface{}
	// This is a low-level trick; in production prefer typed channels
	// or generics.
	return ptr, true
}

// Size returns approximate current size (not atomic, approximate only).
func (q *SPSCQueue) Size() uint64 {
	head := atomic.LoadUint64(&q.producer.head)
	tail := atomic.LoadUint64(&q.consumer.tail)
	if head >= tail {
		return head - tail
	}
	return 0
}
```

### Example 3: Go Struct Layout Analyzer

```go
// struct_layout_analyzer.go
// A utility to analyze and print the cache-line layout of any struct.
// Useful for profiling and debugging cache behavior.

package main

import (
	"fmt"
	"reflect"
	"unsafe"
)

const CacheLine = 64

// AnalyzeStruct prints the cache-line layout of a struct value.
// Usage: AnalyzeStruct(MyStruct{})
func AnalyzeStruct(v interface{}) {
	t := reflect.TypeOf(v)
	if t.Kind() != reflect.Struct {
		fmt.Printf("AnalyzeStruct: expected struct, got %s\n", t.Kind())
		return
	}

	totalSize := t.Size()
	numFields := t.NumField()

	fmt.Printf("=== Struct Layout: %s ===\n", t.Name())
	fmt.Printf("Total size:  %d bytes\n", totalSize)
	fmt.Printf("Cache lines: %d (%.1f%% waste if last line partially used)\n",
		(int(totalSize)+CacheLine-1)/CacheLine,
		float64(int(totalSize)%CacheLine)/float64(CacheLine)*100)
	fmt.Println()
	fmt.Printf("%-25s %6s %6s %6s %s\n", "Field", "Offset", "Size", "Align", "Cache Line")
	fmt.Println("─────────────────────────────────────────────────────────────")

	prevEnd := uintptr(0)
	for i := 0; i < numFields; i++ {
		f := t.Field(i)
		if f.Anonymous && f.Name[0] == '_' {
			// Skip padding fields
			continue
		}
		offset := f.Offset
		size := f.Type.Size()
		align := f.Type.Align()
		cacheLine := offset / CacheLine

		// Show padding between fields
		if offset > prevEnd {
			padding := offset - prevEnd
			fmt.Printf("%-25s %6d %6d %6s %d  ← PADDING\n",
				"(padding)", prevEnd, padding, "-", prevEnd/CacheLine)
		}

		// Detect if field straddles a cache line boundary
		startLine := offset / CacheLine
		endLine := (offset + size - 1) / CacheLine
		straddle := ""
		if startLine != endLine {
			straddle = " ← STRADDLES CACHE LINE BOUNDARY!"
		}

		fmt.Printf("%-25s %6d %6d %6d %d%s\n",
			f.Name, offset, size, align, cacheLine, straddle)

		prevEnd = offset + size
	}
	fmt.Println()
}

// Example usage with different structs
type BadLayout struct {
	A bool    // 1 byte at offset 0
	B int64   // 8 bytes at offset 8 (7 bytes padding before)
	C bool    // 1 byte at offset 16
	D int64   // 8 bytes at offset 24 (7 bytes padding before)
}

type GoodLayout struct {
	B int64   // 8 bytes at offset 0
	D int64   // 8 bytes at offset 8
	A bool    // 1 byte at offset 16
	C bool    // 1 byte at offset 17
	// 6 bytes padding
}

type CacheAlignedStruct struct {
	HotData struct {
		Value   int64
		Counter int64
		Flags   uint32
		State   uint32
	}
	_ [CacheLine - 24]byte // pad hot data to own cache line

	ColdData struct {
		Name    [32]byte
		Created int64
	}
}

func main() {
	AnalyzeStruct(BadLayout{})
	AnalyzeStruct(GoodLayout{})
	AnalyzeStruct(CacheAlignedStruct{})

	fmt.Printf("BadLayout size:            %d bytes\n", unsafe.Sizeof(BadLayout{}))
	fmt.Printf("GoodLayout size:           %d bytes\n", unsafe.Sizeof(GoodLayout{}))
	fmt.Printf("CacheAlignedStruct size:   %d bytes\n", unsafe.Sizeof(CacheAlignedStruct{}))
}
```

---

## 12. Rust Implementations: Comprehensive Examples

### Rust Alignment Primitives

```
RUST ALIGNMENT KEYWORDS
========================

#[repr(align(N))]   → align a struct to N bytes (N must be power of 2)
#[repr(C)]          → use C layout rules (predictable field ordering)
#[repr(packed)]     → remove all padding (DANGEROUS: misaligned access UB)
std::mem::align_of::<T>()  → alignment of type T
std::mem::size_of::<T>()   → size of type T
std::alloc::Layout         → describe size+alignment for allocations
```

### Example 1: False Sharing in Rust

```rust
// false_sharing.rs
// Demonstrates false sharing and the solution with cache-line padding.
//
// Build: rustc -O2 false_sharing.rs -o false_sharing
// Or with cargo: cargo build --release

use std::sync::Arc;
use std::thread;
use std::time::Instant;
use std::hint::black_box;

const NUM_THREADS: usize = 8;
const ITERATIONS: u64 = 100_000_000;
const CACHE_LINE_SIZE: usize = 64;

// ============================================================
// BAD: All counters packed together — false sharing guaranteed.
// ============================================================
#[repr(C)]  // use C layout for predictability
struct FalseSharingCounters {
    // 8 * 8 = 64 bytes — exactly one cache line
    // All threads fight over this single line
    counters: [u64; NUM_THREADS],
}

// Unsafe: we access individual elements from different threads
// without synchronization. This is intentional for benchmarking
// false sharing — in production, use atomics.
unsafe impl Send for FalseSharingCounters {}
unsafe impl Sync for FalseSharingCounters {}

fn bench_false_sharing() -> std::time::Duration {
    // Box<> to heap-allocate; align to cache line
    let counters = Arc::new(Box::new(FalseSharingCounters {
        counters: [0u64; NUM_THREADS],
    }));

    let start = Instant::now();
    let mut handles = vec![];

    for t in 0..NUM_THREADS {
        let c = Arc::clone(&counters);
        handles.push(thread::spawn(move || {
            // UNSAFE: multiple threads writing to different elements
            // of the same array without synchronization.
            // We know they write to different indices, but the
            // CACHE LINE is still shared — that's the point.
            let ptr = unsafe {
                &mut *(c.counters.as_ptr().add(t) as *mut u64)
            };
            for _ in 0..ITERATIONS {
                *ptr = ptr.wrapping_add(1);
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    start.elapsed()
}

// ============================================================
// GOOD: Each counter on its own cache line.
// The #[repr(align(64))] guarantees 64-byte alignment.
// The padding field fills the rest of the 64-byte line.
// ============================================================

/// A u64 padded to occupy exactly one cache line (64 bytes).
#[repr(C, align(64))]
struct CacheLineU64 {
    value: u64,
    // Fill remaining 56 bytes with unused padding
    _pad: [u8; CACHE_LINE_SIZE - std::mem::size_of::<u64>()],
}

impl CacheLineU64 {
    const fn new() -> Self {
        CacheLineU64 { value: 0, _pad: [0u8; CACHE_LINE_SIZE - 8] }
    }
}

struct GoodCounters {
    counters: [CacheLineU64; NUM_THREADS],
}

unsafe impl Send for GoodCounters {}
unsafe impl Sync for GoodCounters {}

fn bench_padded_counters() -> std::time::Duration {
    let counters = Arc::new(Box::new(GoodCounters {
        counters: [
            CacheLineU64::new(), CacheLineU64::new(),
            CacheLineU64::new(), CacheLineU64::new(),
            CacheLineU64::new(), CacheLineU64::new(),
            CacheLineU64::new(), CacheLineU64::new(),
        ],
    }));

    let start = Instant::now();
    let mut handles = vec![];

    for t in 0..NUM_THREADS {
        let c = Arc::clone(&counters);
        handles.push(thread::spawn(move || {
            let ptr = unsafe {
                &mut *(c.counters[t].value as *const u64 as *mut u64)
            };
            for _ in 0..ITERATIONS {
                *ptr = ptr.wrapping_add(1);
            }
        }));
    }

    for h in handles { h.join().unwrap(); }
    start.elapsed()
}

fn main() {
    // Alignment verification
    println!("=== Rust Alignment Info ===");
    println!("u64 align:              {} bytes", std::mem::align_of::<u64>());
    println!("CacheLineU64 align:     {} bytes", std::mem::align_of::<CacheLineU64>());
    println!("CacheLineU64 size:      {} bytes", std::mem::size_of::<CacheLineU64>());
    println!("GoodCounters size:      {} bytes", std::mem::size_of::<GoodCounters>());
    println!();

    // Warmup
    black_box(bench_false_sharing());
    black_box(bench_padded_counters());

    // Benchmark
    let false_time = bench_false_sharing();
    let good_time  = bench_padded_counters();

    println!("=== Benchmark Results ===");
    println!("False sharing:   {:?}", false_time);
    println!("Padded counter:  {:?}", good_time);
    println!("Speedup:         {:.2}x",
             false_time.as_nanos() as f64 / good_time.as_nanos() as f64);
}
```

### Example 2: Cache-Aligned Data Structures with crossbeam Patterns

```rust
// cache_aligned_rust.rs
// Production-quality cache-line-aligned types in Rust.
// These patterns are used in crossbeam, tokio, and other
// high-performance Rust libraries.

use std::cell::UnsafeCell;
use std::mem::{align_of, size_of};
use std::ops::{Deref, DerefMut};
use std::fmt;

const CACHE_LINE: usize = 64;

// ============================================================
// CachePadded<T>: The canonical Rust pattern for cache padding.
// This is essentially what crossbeam_utils::CachePadded does.
//
// Usage: CachePadded::new(value) wraps any value and pads it
// to occupy its own cache line.
// ============================================================

/// Pads and aligns a value to the length of a cache line.
///
/// Starting from a cache-aligned address, the value comes first
/// and then the padding fills out the rest of the cache line.
/// This ensures the value does not share a cache line with any
/// other data, preventing false sharing.
#[repr(align(64))]
pub struct CachePadded<T> {
    value: T,
}

impl<T> CachePadded<T> {
    /// Pads a value to the length of a cache line.
    pub fn new(t: T) -> CachePadded<T> {
        CachePadded { value: t }
    }

    /// Returns the inner value.
    pub fn into_inner(self) -> T {
        self.value
    }
}

impl<T> Deref for CachePadded<T> {
    type Target = T;
    fn deref(&self) -> &T {
        &self.value
    }
}

impl<T> DerefMut for CachePadded<T> {
    fn deref_mut(&mut self) -> &mut T {
        &mut self.value
    }
}

impl<T: fmt::Debug> fmt::Debug for CachePadded<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("CachePadded")
            .field("value", &self.value)
            .field("size", &size_of::<Self>())
            .field("align", &align_of::<Self>())
            .finish()
    }
}

// ============================================================
// CacheAlignedAtomic: An atomic integer that lives alone on
// its cache line. Used for performance-critical counters,
// sequence numbers, and lock-free data structure indices.
// ============================================================

use std::sync::atomic::{AtomicU64, Ordering};

#[repr(align(64))]
pub struct CacheAlignedAtomic {
    value: AtomicU64,
}

impl CacheAlignedAtomic {
    pub const fn new(v: u64) -> Self {
        CacheAlignedAtomic { value: AtomicU64::new(v) }
    }

    #[inline(always)]
    pub fn load(&self, order: Ordering) -> u64 {
        self.value.load(order)
    }

    #[inline(always)]
    pub fn store(&self, val: u64, order: Ordering) {
        self.value.store(val, order);
    }

    #[inline(always)]
    pub fn fetch_add(&self, delta: u64, order: Ordering) -> u64 {
        self.value.fetch_add(delta, order)
    }

    #[inline(always)]
    pub fn compare_exchange(
        &self,
        current: u64,
        new: u64,
        success: Ordering,
        failure: Ordering,
    ) -> Result<u64, u64> {
        self.value.compare_exchange(current, new, success, failure)
    }
}

// ============================================================
// Lock-Free SPSC Queue (Rust version)
// Producer and consumer state each on their own cache lines.
// Uses MaybeUninit for safe uninitialized buffer slots.
// ============================================================

use std::sync::Arc;
use std::mem::MaybeUninit;

struct SPSCQueue<T> {
    // CACHE LINE 0: producer's write cursor (only producer writes this)
    head: CachePadded<AtomicU64>,
    // CACHE LINE 1: consumer's read cursor (only consumer writes this)
    tail: CachePadded<AtomicU64>,
    // Read-only after initialization
    capacity: usize,
    mask: u64, // capacity - 1 for fast modulo
    // Buffer — each slot is a MaybeUninit<T> wrapped in UnsafeCell
    // for interior mutability without a lock
    buffer: Box<[UnsafeCell<MaybeUninit<T>>]>,
}

unsafe impl<T: Send> Send for SPSCQueue<T> {}
unsafe impl<T: Send> Sync for SPSCQueue<T> {}

impl<T> SPSCQueue<T> {
    /// Create a new SPSC queue. capacity must be a power of 2.
    pub fn new(capacity: usize) -> Arc<Self> {
        assert!(capacity >= 2);
        assert!(capacity.is_power_of_two(), "capacity must be power of 2");

        let buffer = (0..capacity)
            .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
            .collect::<Vec<_>>()
            .into_boxed_slice();

        Arc::new(SPSCQueue {
            head:     CachePadded::new(AtomicU64::new(0)),
            tail:     CachePadded::new(AtomicU64::new(0)),
            capacity,
            mask:     (capacity - 1) as u64,
            buffer,
        })
    }

    /// Push an item. Returns Err(item) if queue is full.
    /// MUST be called from a single producer thread only.
    pub fn push(&self, item: T) -> Result<(), T> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);

        if head.wrapping_sub(tail) >= self.capacity as u64 {
            return Err(item); // queue full
        }

        let slot = (head & self.mask) as usize;
        unsafe {
            // Write item to uninitialized slot
            (*self.buffer[slot].get()).write(item);
        }

        // Publish with release: ensures item write is visible before head update
        self.head.store(head.wrapping_add(1), Ordering::Release);
        Ok(())
    }

    /// Pop an item. Returns None if queue is empty.
    /// MUST be called from a single consumer thread only.
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);

        if head == tail {
            return None; // queue empty
        }

        let slot = (tail & self.mask) as usize;
        let item = unsafe {
            // Read from initialized slot
            (*self.buffer[slot].get()).assume_init_read()
        };

        // Advance consumer cursor
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        Some(item)
    }

    pub fn len(&self) -> usize {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Relaxed);
        head.wrapping_sub(tail) as usize
    }

    pub fn is_empty(&self) -> bool { self.len() == 0 }
    pub fn is_full(&self)  -> bool { self.len() >= self.capacity }
}

impl<T> Drop for SPSCQueue<T> {
    fn drop(&mut self) {
        // Drain all remaining items to call their destructors
        while let Some(_) = self.pop() {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cache_padded_size() {
        // CachePadded should always be exactly CACHE_LINE bytes
        assert_eq!(size_of::<CachePadded<u8>>(), CACHE_LINE);
        assert_eq!(size_of::<CachePadded<u64>>(), CACHE_LINE);
        assert_eq!(align_of::<CachePadded<u64>>(), CACHE_LINE);
    }

    #[test]
    fn test_spsc_basic() {
        let q = SPSCQueue::new(16);
        assert!(q.push(42u32).is_ok());
        assert_eq!(q.pop(), Some(42u32));
        assert_eq!(q.pop(), None);
    }

    #[test]
    fn test_spsc_threaded() {
        use std::thread;
        let q = SPSCQueue::new(1024);
        let q_producer = Arc::clone(&q);
        let q_consumer = Arc::clone(&q);

        let producer = thread::spawn(move || {
            for i in 0u64..10_000 {
                while q_producer.push(i).is_err() {
                    thread::yield_now();
                }
            }
        });

        let consumer = thread::spawn(move || {
            let mut sum = 0u64;
            let mut count = 0;
            while count < 10_000 {
                if let Some(v) = q_consumer.pop() {
                    sum += v;
                    count += 1;
                } else {
                    thread::yield_now();
                }
            }
            sum
        });

        producer.join().unwrap();
        let sum = consumer.join().unwrap();
        let expected: u64 = (0..10_000u64).sum();
        assert_eq!(sum, expected);
    }
}
```

### Example 3: Custom Aligned Allocator in Rust

```rust
// aligned_allocator.rs
// Custom allocator that always returns cache-line-aligned memory.
// Useful for creating collections of cache-aligned items.

use std::alloc::{GlobalAlloc, Layout, System};

/// A wrapper allocator that always aligns allocations to
/// at least CACHE_LINE bytes.
pub struct CacheAlignedAllocator;

unsafe impl GlobalAlloc for CacheAlignedAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // Upgrade alignment to at least cache-line size
        let aligned_layout = Layout::from_size_align(
            layout.size(),
            layout.align().max(64), // at least 64 bytes
        ).expect("Invalid layout");

        System.alloc(aligned_layout)
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        let aligned_layout = Layout::from_size_align(
            layout.size(),
            layout.align().max(64),
        ).expect("Invalid layout");

        System.dealloc(ptr, aligned_layout)
    }
}

// Use as global allocator:
// #[global_allocator]
// static A: CacheAlignedAllocator = CacheAlignedAllocator;

// ============================================================
// Utility function: verify alignment at runtime
// ============================================================

pub fn verify_alignment<T>(val: &T, expected_align: usize) -> bool {
    let addr = val as *const T as usize;
    addr % expected_align == 0
}

pub fn print_alignment_info<T>(name: &str, val: &T) {
    let addr = val as *const T as usize;
    let size = std::mem::size_of::<T>();
    let align = std::mem::align_of::<T>();
    println!("{}: addr=0x{:x}, size={}, type_align={}, cache_line_offset={}",
        name, addr, size, align, addr % 64);
}
```

---

## 13. Padding Strategies and Struct Layout

### Strategy 1: Explicit Padding Fields

```c
/* Method: Add explicit char arrays to fill cache lines */

struct ExplicitPadding {
    /* Hot region — fits in cache line 0 */
    int  fd;             /*  4 bytes, offset  0 */
    int  state;          /*  4 bytes, offset  4 */
    long bytes_in;       /*  8 bytes, offset  8 */
    long bytes_out;      /*  8 bytes, offset 16 */
    void *rbuf;          /*  8 bytes, offset 24 */
    void *wbuf;          /*  8 bytes, offset 32 */
    int  rlen;           /*  4 bytes, offset 40 */
    int  wlen;           /*  4 bytes, offset 44 */
    /* Used: 48 bytes. Pad to 64. */
    char _pad0[16];      /* 16 bytes, offset 48 */

    /* Cold region — cache line 1 */
    char  name[32];      /* 32 bytes, offset 64 */
    int   err;           /*  4 bytes, offset 96 */
    int   flags;         /*  4 bytes, offset 100 */
    long  created;       /*  8 bytes, offset 104 */
    /* Used: 48 bytes on this line. Pad to 64. */
    char _pad1[16];      /* 16 bytes, offset 112 */
};

/* Total: 128 bytes = exactly 2 cache lines */
```

### Strategy 2: Using `__cacheline_aligned` Inside a Struct

```c
/* Mark specific fields to force them to a new cache line */

struct MixedPaddingStruct {
    /* Fields that must be on their own cache line */
    spinlock_t lock       __cacheline_aligned;  /* lock on its own line */
    atomic_t   refcount   __cacheline_aligned;  /* refcount on its own line */
    
    /* These two will be on the same line as each other */
    int   type;
    int   flags;
};
```

### Strategy 3: Struct Reordering (Zero-Cost Optimization)

```c
/*
 * The OPTIMAL field ordering for minimum size AND cache efficiency:
 * 
 * RULE: Sort fields by descending alignment requirement.
 * 1. All 8-byte fields first
 * 2. All 4-byte fields
 * 3. All 2-byte fields
 * 4. All 1-byte fields
 *
 * This eliminates most compiler-inserted padding automatically.
 */

/* BAD ORDER: 24 bytes with padding */
struct BadOrder {
    char   a;    /* 1 byte  at offset 0 */
                 /* 7 bytes padding! */
    long   b;    /* 8 bytes at offset 8 */
    short  c;    /* 2 bytes at offset 16 */
                 /* 2 bytes padding */
    int    d;    /* 4 bytes at offset 20 */
};               /* Total: 24 bytes */

/* GOOD ORDER: 16 bytes, no padding */
struct GoodOrder {
    long   b;    /* 8 bytes at offset 0 */
    int    d;    /* 4 bytes at offset 8 */
    short  c;    /* 2 bytes at offset 12 */
    char   a;    /* 1 byte  at offset 14 */
                 /* 1 byte  natural padding to align to 8 */
};               /* Total: 16 bytes */
```

### Strategy 4: The Linux Kernel `___cacheline_aligned` Pattern

```
LINUX KERNEL HOT/COLD SPLIT PATTERN
=====================================

Used in struct rq (run queue), struct net_device, etc.

struct kernel_struct {
    /* ======== FREQUENTLY ACCESSED (HOT) ======== */
    spinlock_t lock;
    unsigned long flags;
    void *hot_ptr;
    int fast_counter;
    int state;
    /* ... more hot fields ... */
    
    /* Force boundary — next field starts at cache line N+1 */
    /* padding here if needed */
    
    /* ======== RARELY ACCESSED (COLD) ======== */
    char name[32]       ____cacheline_aligned;
    struct list_head list;
    ktime_t created;
    /* ... more cold fields ... */
} ____cacheline_aligned;
```

---

## 14. NUMA (Non-Uniform Memory Access) and Cache Alignment

### What Is NUMA?

**Glossary:** 
- **NUMA node:** A group of CPUs and the memory bank physically closest to them. Accessing memory on a remote NUMA node is slower than local node memory.
- **Internode:** Between NUMA nodes.

```
NUMA TOPOLOGY (2-socket server)
================================

  Socket 0 (NUMA Node 0)          Socket 1 (NUMA Node 1)
  ┌─────────────────────┐         ┌─────────────────────┐
  │  CPU 0  CPU 1       │         │  CPU 8  CPU 9       │
  │  CPU 2  CPU 3       │         │ CPU 10  CPU 11      │
  │  CPU 4  CPU 5       │         │ CPU 12  CPU 13      │
  │  CPU 6  CPU 7       │         │ CPU 14  CPU 15      │
  │                     │         │                     │
  │  L3 Cache (30MB)    │         │  L3 Cache (30MB)    │
  │                     │         │                     │
  │  Local DRAM (128GB) │◄───────►│  Local DRAM (128GB) │
  └─────────────────────┘  QPI/   └─────────────────────┘
                           UPI
  Local access:  ~70ns
  Remote access: ~140ns (2x slower!)
```

### NUMA-Aware Alignment in Linux Kernel

```c
/* From: include/linux/cache.h */

/* INTERNODE_CACHE_SHIFT: log2 of the inter-node cache line size.
 * On many systems this is the same as L1_CACHE_SHIFT (64 bytes).
 * On IBM POWER, this might be 128 bytes.
 */
#ifndef INTERNODE_CACHE_SHIFT
#define INTERNODE_CACHE_SHIFT L1_CACHE_SHIFT
#endif

#define INTERNODE_CACHE_BYTES (1 << INTERNODE_CACHE_SHIFT)

/* __cacheline_internodealigned_in_smp:
 * For data that is accessed by CPUs on DIFFERENT NUMA nodes.
 * Aligns to the larger internode cache line size.
 * This is larger than __cacheline_aligned because it accounts
 * for the prefetcher fetching multiple cache lines at once
 * when doing remote NUMA accesses.
 */
#ifdef CONFIG_SMP
#define __cacheline_internodealigned_in_smp                         \
    __attribute__((__aligned__(1 << INTERNODE_CACHE_SHIFT)))
#else
#define __cacheline_internodealigned_in_smp
#endif

/* Example: global spinlock accessed by all CPUs */
static spinlock_t global_lock __cacheline_internodealigned_in_smp;
```

### NUMA Memory Allocation

```c
/* Allocate memory on a specific NUMA node */
#include <numa.h>   /* libnuma: apt install libnuma-dev */

void *numa_local_alloc(size_t size)
{
    int node = numa_node_of_cpu(sched_getcpu());  /* my NUMA node */
    void *ptr = numa_alloc_onnode(size, node);
    return ptr;
}

/* Allocate and align to cache line on the local NUMA node */
void *numa_cache_aligned_alloc(size_t size)
{
    /* Round size up to cache line multiple */
    size_t aligned_size = (size + 63) & ~63;
    
    int node = numa_node_of_cpu(sched_getcpu());
    void *ptr = numa_alloc_onnode(aligned_size, node);
    
    /* Verify alignment (numa_alloc_onnode returns page-aligned memory) */
    /* Page size (4096) is a multiple of cache line (64), so always aligned */
    return ptr;
}
```

---

## 15. Atomic Operations and Cache Lines

### The Relationship Between Atomics and Cache Lines

```
ATOMIC OPERATION COST MODEL
==============================

Operation          Cost (cycles)   Description
─────────────────  ─────────────   ─────────────────────────────────
Load (local)             3-5       Variable is in L1, same core
Load (shared)           10-15      Variable in L1, shared S state
CAS (local, success)    15-20      Variable locally owned (E or M)
CAS (remote, success)   50-200+    Must do RFO, invalidate others
atomic_add (1 core)     3-5        No contention
atomic_add (8 cores)    200-600+   False sharing nightmare!

KEY INSIGHT: Atomic operations that contend on the SAME cache line
are as expensive as cache misses — because each CAS/exchange
requires exclusive ownership of the cache line (M state in MESI).
```

### Splitting Read-Heavy and Write-Heavy Atomics

```c
/* Classic pattern: split atomic operations based on access pattern */

/* PROBLEM: A reference counter used across many threads.
 * atomic_dec_and_test() requires the M state — exclusive ownership.
 * If 8 threads all hold references and decrement simultaneously,
 * the cache line bounces between cores constantly.
 */

/* SOLUTION 1: Striped reference counting (like Linux's percpu_ref) */
struct striped_refcount {
    _Atomic int counts[64];  /* one slot per CPU, each on separate line... */
    /* Actually, for full correctness, pad each: */
} __attribute__((aligned(64)));

/* Each CPU increments its own stripe (no contention on inc).
 * Only on final release do we sum all stripes (rare, one atomic). */

/* SOLUTION 2: Use __cacheline_aligned_in_smp on the atomic */
_Atomic long refcount __cacheline_aligned_in_smp;

/* Now at least the refcount doesn't share a line with other data
 * that would get invalidated when refcount changes. */

/* SOLUTION 3: Per-CPU counters (Linux percpu_counter) */
/* See: include/linux/percpu_counter.h */
struct percpu_counter {
    spinlock_t     lock;      /* protects sum and the percpu array */
    s64            count;     /* approximated count sum */
    s32 __percpu  *counters;  /* per-CPU counters, cache-line aligned per CPU */
};
```

---

## 16. Lock-Free Data Structures with Cache Alignment

### Michael-Scott Queue with Cache Alignment

```c
/* ms_queue.c
 * Michael-Scott lock-free queue with cache-conscious design.
 * 
 * The key insight: the head and tail pointers are frequently
 * modified by different threads. Putting them on separate cache
 * lines eliminates false sharing between enqueue and dequeue.
 *
 * Original M&S queue does NOT consider this — this is an
 * improvement commonly used in production code.
 */

#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

#define CACHE_LINE 64

/* Each node in the queue */
typedef struct msq_node {
    void               *data;
    _Atomic(struct msq_node *) next;
    /* Pad to cache line to avoid false sharing between nodes */
    char _pad[CACHE_LINE - sizeof(void*) - sizeof(_Atomic(void*))];
} msq_node_t __attribute__((aligned(CACHE_LINE)));

/* Queue structure with head/tail on separate cache lines */
typedef struct {
    /* CACHE LINE 0: head — dequeue operation touches this */
    struct {
        _Atomic(msq_node_t *) ptr;
        char _pad[CACHE_LINE - sizeof(_Atomic(void*))];
    } __attribute__((aligned(CACHE_LINE))) head;
    
    /* CACHE LINE 1: tail — enqueue operation touches this */
    struct {
        _Atomic(msq_node_t *) ptr;
        char _pad[CACHE_LINE - sizeof(_Atomic(void*))];
    } __attribute__((aligned(CACHE_LINE))) tail;
} ms_queue_t;

/* Initialize queue with a sentinel node */
void msq_init(ms_queue_t *q) {
    msq_node_t *sentinel = aligned_alloc(CACHE_LINE, sizeof(msq_node_t));
    sentinel->data = NULL;
    atomic_store(&sentinel->next, NULL);
    atomic_store(&q->head.ptr, sentinel);
    atomic_store(&q->tail.ptr, sentinel);
}

/* Enqueue: CAS on tail — minimal contention with dequeue */
void msq_enqueue(ms_queue_t *q, void *data) {
    msq_node_t *node = aligned_alloc(CACHE_LINE, sizeof(msq_node_t));
    node->data = data;
    atomic_store_explicit(&node->next, NULL, memory_order_relaxed);
    
    msq_node_t *tail, *next;
    for (;;) {
        tail = atomic_load_explicit(&q->tail.ptr, memory_order_acquire);
        next = atomic_load_explicit(&tail->next, memory_order_acquire);
        
        if (tail == atomic_load(&q->tail.ptr)) {
            if (next == NULL) {
                /* Try to link node at tail */
                if (atomic_compare_exchange_weak_explicit(
                        &tail->next, &next, node,
                        memory_order_release, memory_order_relaxed)) {
                    break;
                }
            } else {
                /* Tail is lagging; advance it */
                atomic_compare_exchange_weak_explicit(
                    &q->tail.ptr, &tail, next,
                    memory_order_release, memory_order_relaxed);
            }
        }
    }
    /* Try to advance tail */
    atomic_compare_exchange_weak_explicit(
        &q->tail.ptr, &tail, node,
        memory_order_release, memory_order_relaxed);
}

/* Dequeue: CAS on head — minimal contention with enqueue */
void *msq_dequeue(ms_queue_t *q) {
    msq_node_t *head, *tail, *next;
    for (;;) {
        head = atomic_load_explicit(&q->head.ptr, memory_order_acquire);
        tail = atomic_load_explicit(&q->tail.ptr, memory_order_acquire);
        next = atomic_load_explicit(&head->next, memory_order_acquire);
        
        if (head == atomic_load(&q->head.ptr)) {
            if (head == tail) {
                if (next == NULL) return NULL;  /* empty */
                /* Tail is lagging */
                atomic_compare_exchange_weak_explicit(
                    &q->tail.ptr, &tail, next,
                    memory_order_release, memory_order_relaxed);
            } else {
                void *data = next->data;
                if (atomic_compare_exchange_weak_explicit(
                        &q->head.ptr, &head, next,
                        memory_order_release, memory_order_relaxed)) {
                    free(head);
                    return data;
                }
            }
        }
    }
}
```

---

## 17. Linux Kernel Data Structure Deep Dive

### `struct task_struct` — Process Descriptor

The Linux `task_struct` is one of the most cache-optimized structs in the kernel:

```c
/* From: include/linux/sched.h (simplified) */

struct task_struct {
    /*
     * For reasons of header soup the first few fields of task_struct
     * are explicitly laid out for cache efficiency.
     */
    
    /* ── CACHE LINE 0: Hot scheduling fields ──────────────── */
    struct thread_info      thread_info;    /* must be first! arch-specific */
    
    /* ── Scheduling state — touched every context switch ──── */
    unsigned int            __state;        /* TASK_RUNNING, TASK_INTERRUPTIBLE etc. */
    
    /* ── STACK pointer — hot during syscall/interrupt ─────── */
    void                    *stack;
    
    /* Refcount */
    refcount_t              usage;
    unsigned int            flags;          /* PF_* flags */
    unsigned int            ptrace;
    
    /* ... many more fields, carefully ordered ... */
    
    /* ── CPU/scheduling affinity ─────────────────────────── */
    int                     on_cpu;
    struct __call_single_data    wake_entry;
    unsigned int            wakee_flips;
    unsigned long           wakee_flip_decay_ts;
    struct task_struct      *last_wakee;
    
    /* Force alignment for the following fields */
    int                     recent_used_cpu;
    int                     wake_cpu;
    
    /* ── Run queue linkage ────────────────────────────────── */
    int                     on_rq;
    int                     prio;
    int                     static_prio;
    int                     normal_prio;
    unsigned int            rt_priority;
    
    /* ── Scheduler class pointer — hot on every schedule() ── */
    const struct sched_class *sched_class;
    struct sched_entity      se;
    struct sched_rt_entity   rt;
    
    /* ... rest of the fields ... */
} __attribute__((aligned(L1_CACHE_BYTES)));
/* Note: the struct itself is cache-line aligned */
```

### `struct rq` — Scheduler Run Queue

```c
/* From: kernel/sched/sched.h (simplified, showing cache strategy) */

struct rq {
    /* ── CACHE LINE 0: Hot scheduling path ───────────────── */
    /* These fields are touched on every scheduler tick */
    raw_spinlock_t          lock;
    unsigned int            nr_running;
    unsigned int            nr_numa_running;
    unsigned int            nr_preferred_running;
    unsigned int            numa_migrate_on_load;
    
    /* ── Load balancing (warm path) ──────────────────────── */
    unsigned long           nr_load_updates;
    u64                     nr_switches;    
    
    /* ── The actual runqueues ─────────────────────────────── */
    struct cfs_rq           cfs;    /* Completely Fair Scheduler */
    struct rt_rq            rt;     /* Real-Time scheduler */
    struct dl_rq            dl;     /* Deadline scheduler */
    
    /* ── Cold: statistics and tuning ─────────────────────── */
#ifdef CONFIG_SMP
    struct root_domain __rcu *rd;
    struct sched_domain __rcu *sd;
    
    unsigned long           cpu_capacity;
    unsigned long           cpu_capacity_orig;
    
    /* Force to new cache line — accessed on load balancer path */
    struct callback_head    *balance_callback;
    unsigned char           nohz_idle_balance;
    unsigned char           idle_balance;
    
    unsigned long           misfit_task_load;
    int                     active_balance;
    int                     push_cpu;
    struct cpu_stop_work    active_balance_work;
#endif
    
    /* ── Timing: read on every tick ─────────────────────── */
    u64                     clock;
    u64                     clock_task;
    u64                     clock_pelt;
    unsigned long           lost_idle_time;
    
    /* ── IRQ time accounting ──────────────────────────────── */
    u64                     prev_irq_time;
    u64                     prev_steal_time;
    
} ____cacheline_aligned_in_smp;
/* The entire struct is cache-line aligned.
 * Per-CPU variable: each CPU has its own rq.
 * No false sharing between CPUs! */
```

### `struct net_device` — Network Device

```c
/* From: include/linux/netdevice.h (key layout decisions) */

struct net_device {
    char            name[IFNAMSIZ];     /* interface name, e.g. "eth0" */
    struct hlist_node   name_hlist;
    
    /* ... */
    
    /* 
     * TX/RX queues are kept on SEPARATE cache lines.
     * TX is typically on a different CPU than RX (multi-queue).
     */
    
    /* ── TX (transmit) path ──────────────────────────────── */
    struct netdev_queue __rcu *_tx ____cacheline_aligned_in_smp;
    unsigned int        num_tx_queues;
    unsigned int        real_num_tx_queues;
    
    /* ── RX (receive) path — new cache line ──────────────── */
    struct netdev_rx_queue  *_rx ____cacheline_aligned_in_smp;
    unsigned int        num_rx_queues;
    unsigned int        real_num_rx_queues;
    
    /* ── Stats ─────────────────────────────────────────────  */
    const struct net_device_ops     *netdev_ops;
    const struct ethtool_ops        *ethtool_ops;
    
    /* ... etc ... */
};
```

---

## 18. DMA (Direct Memory Access) Alignment

**Glossary:** DMA is when a device (e.g., network card, disk controller) reads/writes system memory directly without involving the CPU. Misaligned DMA can corrupt neighboring data or cause hardware faults.

### Why DMA Needs Alignment

```
DMA ALIGNMENT REQUIREMENTS
============================

Device → Memory
  ┌─────────┐                    ┌────────────────────┐
  │ Network  │  DMA transfer      │     DRAM           │
  │  Card    │───────────────────►│  ┌──────────────┐  │
  │  (PCIe)  │  must start at     │  │ DMA Buffer   │  │
  └─────────┘  cache-aligned      │  │ (cache-line  │  │
                address            │  │  aligned)    │  │
                                   │  └──────────────┘  │
                                   └────────────────────┘

WHY ALIGNMENT MATTERS FOR DMA:
1. Cache coherency: DMA must not partially overwrite a cache line
   that the CPU also has cached. If the DMA writes bytes 32-95
   and the CPU has [0-63] in cache, the CPU's cached copy is stale
   for bytes 32-63.

2. IOMMU performance: I/O MMU page translations are more efficient
   with naturally aligned addresses.

3. Hardware requirements: Some DMA controllers require minimum
   alignment (often 64 or 128 bytes).

4. Cache invalidation: Linux's DMA API flushes/invalidates entire
   cache lines. If your buffer straddles cache lines, adjacent data
   (not in the DMA buffer) can be corrupted by the flush.
```

### Linux DMA API with Alignment

```c
/* From: include/linux/dma-mapping.h */

/* Allocate coherent DMA memory.
 * dma_alloc_coherent ensures:
 *   1. Both CPU and device see the same data (no cache inconsistency)
 *   2. Memory is physically contiguous
 *   3. Memory is cache-line aligned (at minimum)
 *   4. Returns both CPU virtual address and DMA physical address
 */
void *cpu_addr = dma_alloc_coherent(
    dev,           /* struct device * */
    size,          /* bytes to allocate */
    &dma_handle,   /* out: DMA address for device to use */
    GFP_KERNEL     /* allocation flags */
);

/* The returned cpu_addr is GUARANTEED to be:
 *   - Virtually contiguous
 *   - Physically contiguous
 *   - Cache-line aligned (at minimum)
 */

/* For streaming DMA (device writes once, CPU reads): */
dma_addr_t dma_addr = dma_map_single(
    dev,
    buffer,        /* pre-allocated buffer (must be cache-line aligned!) */
    size,
    DMA_FROM_DEVICE  /* or DMA_TO_DEVICE */
);

/* CRITICAL: buffer must be cache-line aligned AND
 * its size must be a multiple of cache line size!
 * Otherwise neighboring data can be corrupted. */

/* After DMA is complete: */
dma_unmap_single(dev, dma_addr, size, DMA_FROM_DEVICE);

/* ── Allocating a properly aligned DMA buffer ──────────── */
/* Use kmalloc for power-of-2 sizes (guaranteed aligned) */
char *buf = kmalloc(512, GFP_KERNEL | GFP_DMA);  /* 512-byte aligned */

/* Or use kmem_cache with SLAB_HWCACHE_ALIGN */
struct kmem_cache *dma_cache = kmem_cache_create(
    "dma_buffers",
    BUF_SIZE,
    L1_CACHE_BYTES,          /* min alignment */
    SLAB_HWCACHE_ALIGN,      /* align to hardware cache line */
    NULL
);
```

---

## 19. Memory Barriers and Cache Flushing

### Glossary

- **Memory barrier (fence):** An instruction that prevents the CPU or compiler from reordering memory operations across it.
- **Cache flush:** Writing dirty cache contents back to DRAM.
- **Cache invalidation:** Marking cached data as stale (must be reloaded).
- **Store buffer:** A CPU-internal buffer holding pending writes before they reach the cache.
- **Invalidation queue:** A queue of pending cache invalidation messages a CPU hasn't yet processed.

### Types of Memory Barriers

```
MEMORY BARRIER TYPES
======================

               Prevent reordering of:
Barrier        Loads before    Stores before
               with loads      with stores    Notes
               after           after
─────────────  ─────────────   ─────────────  ─────────────────────────────
Load fence     YES             NO             smp_rmb(), lfence on x86
Store fence    NO              YES            smp_wmb(), sfence on x86
Full fence     YES             YES            smp_mb(), mfence on x86
Compiler only  YES (compiler)  YES (compiler) barrier() — no CPU instruction
```

### Linux Barrier API

```c
/* From: include/asm-generic/barrier.h and arch-specific versions */

/* Full memory barrier: all loads/stores before are complete
 * and visible before any load/store after */
smp_mb();           /* SMP: insert memory barrier */
mb();               /* Always insert (even on UP) */

/* Read barrier: all loads before are complete before loads after */
smp_rmb();          /* SMP read barrier */
rmb();              /* Always */

/* Write barrier: all stores before are complete before stores after */
smp_wmb();          /* SMP write barrier */
wmb();              /* Always */

/* Acquire/Release semantics (paired): */
/* load-acquire: no reads/writes AFTER can be reordered BEFORE */
smp_load_acquire(&ptr)
/* store-release: no reads/writes BEFORE can be reordered AFTER */
smp_store_release(&ptr, val)

/* Compiler-only barrier (no CPU fence): */
barrier();          /* prevents compiler reordering, not CPU reordering */

/* ── Concrete Example: Ring Buffer Producer/Consumer ─── */

/* Producer */
buffer[slot] = value;   /* write data */
smp_wmb();              /* ensure data written before head updated */
head++;                 /* publish: consumer reads this to see new data */

/* Consumer */
tail_snapshot = head;   /* read head */
smp_rmb();              /* ensure head read before data read */
value = buffer[slot];   /* read data — guaranteed to see producer's write */
```

### Cache Flush Operations (ARM/non-coherent architectures)

```c
/* On non-cache-coherent architectures (some ARM, embedded systems),
 * you must manually flush/invalidate caches for DMA. */

/* Flush data cache (write dirty lines to memory) */
flush_dcache_page(page);

/* Invalidate data cache (mark lines as invalid, must reload) */
invalidate_dcache_range(start, end);

/* Flush + Invalidate (clean and invalidate) */
flush_cache_range(vma, start, end);

/* For DMA: the kernel DMA API handles this automatically */
dma_sync_single_for_cpu(dev, dma_addr, size, DMA_FROM_DEVICE);
dma_sync_single_for_device(dev, dma_addr, size, DMA_TO_DEVICE);
```

---

## 20. Performance Measurement and Profiling Tools

### Tool 1: `perf` — Linux Performance Counters

```bash
# Install: apt install linux-perf (or linux-tools-$(uname -r))

# Measure cache misses during execution
perf stat -e cache-misses,cache-references,L1-dcache-loads,L1-dcache-load-misses \
    ./your_program

# Example output:
# 1,234,567    cache-misses          #   2.34% of all cache refs
# 52,734,123   cache-references
# 98,765,432   L1-dcache-loads
# 1,234,567    L1-dcache-load-misses #   1.25% of all L1 loads

# Measure false sharing specifically
perf stat -e \
    mem_load_retired.l1_hit,\
    mem_load_retired.l1_miss,\
    machine_clears.memory_ordering \
    ./your_program

# Record performance data for analysis
perf record -e cache-misses -g ./your_program
perf report  # interactive analysis

# Annotate source code with cache miss hotspots
perf annotate --stdio

# ==== Hardware Events Available ====
perf list cache  # list all cache-related events
# Example events:
#   L1-dcache-load-misses
#   L1-dcache-loads
#   L1-dcache-prefetches
#   L1-icache-load-misses
#   LLC-load-misses          (Last Level Cache)
#   LLC-loads
#   cache-misses
#   cache-references
```

### Tool 2: Valgrind Cachegrind

```bash
# Simulate cache behavior (no need for hardware performance counters)
# Works on any machine, but ~20-50x slower execution
valgrind --tool=cachegrind ./your_program

# More detail on specific cache parameters
valgrind --tool=cachegrind \
    --I1=32768,8,64 \   # L1 instruction cache: 32KB, 8-way, 64B lines
    --D1=32768,8,64 \   # L1 data cache: 32KB, 8-way, 64B lines
    --LL=8388608,16,64 \ # L2/L3: 8MB, 16-way, 64B lines
    ./your_program

# Analyze results
cg_annotate cachegrind.out.<pid>
# Shows per-line cache miss counts in your source code!

# Compare two runs
cg_diff cachegrind.out.1234 cachegrind.out.5678
```

### Tool 3: `perf c2c` — False Sharing Detection

```bash
# c2c = "cache-to-cache" — detects false sharing between cores
# Requires Linux 4.10+ and a Haswell or newer CPU

# Record
perf c2c record -ag -- ./your_program

# Report (shows which cache lines are being shared)
perf c2c report --stats

# Example output:
# =================================================
#  Shared Data Cache Line Table     (6 entries, sorted on Total HITMs)
#                         Total      Total  Total    ...
# Index           Cacheline  HITM   Load   Store  ...
# 0     0xffff8b3c4a9d20c0   5432   12345   3456
#   ↑ This cache line has 5432 HITM (Hit in Modified = false sharing!)
```

### Tool 4: `pmu-tools` and `toplev`

```bash
# toplev: Top-Down performance analysis (Intel)
# pip install pmu-tools

# Analyze bottleneck level (Memory Bound, Core Bound, etc.)
toplev --all -v -x, -o toplev_output.csv ./your_program

# Shows if your bottleneck is:
# - Memory Bound (cache misses, bandwidth)
# - Core Bound (execution units)
# - Bad Speculation (branch mispredicts)
# - Frontend Bound (instruction cache, decode)
```

### Tool 5: Checking Structure Layout with `pahole`

```bash
# pahole: "poke-a-hole" — shows struct layout and padding
# Install: apt install pahole (or dwarves)

# Compile with debug info first
gcc -g -O2 -o myprogram myprogram.c

# Analyze struct layouts
pahole myprogram

# Example output:
# struct BadOrder {
#     char     a;         /*  0    1 */
#     /* XXX  7 bytes hole, try to pack */
#     long     b;         /*  8    8 */
#     short    c;         /* 16    2 */
#     /* XXX  2 bytes hole, try to pack */
#     int      d;         /* 20    4 */
#     /* size: 24, cachelines: 1, members: 4 */
#     /* sum members: 15, holes: 2, sum holes: 9 */
#     /* padding: 0 */
# };

# Filter to specific struct
pahole -C task_struct /proc/kcore  # kernel structs!
```

### Tool 6: In-Code Timing with `rdtsc`

```c
/* Read CPU timestamp counter — cycle-accurate measurement */
#include <stdint.h>
#include <x86intrin.h>  /* _rdtsc, __rdtscp */

static inline uint64_t read_cycles(void) {
    /* __rdtscp: serializing version (prevents out-of-order execution
     * from moving memory accesses past the measurement point) */
    unsigned int aux;
    uint64_t tsc = __rdtscp(&aux);
    /* Compiler barrier: prevent code hoisting */
    asm volatile("" ::: "memory");
    return tsc;
}

/* Usage: */
uint64_t start = read_cycles();
/* ... code to measure ... */
uint64_t end = read_cycles();
uint64_t cycles = end - start;
printf("Cycles: %lu\n", cycles);

/* Convert to nanoseconds (approximate): */
double freq_ghz = 3.5;  /* query with: cat /proc/cpuinfo | grep "cpu MHz" */
double ns = (double)cycles / freq_ghz;
```

---

## 21. Advanced Patterns and Mental Models

### Mental Model 1: The "Ownership" Model

```
CACHE LINE OWNERSHIP MENTAL MODEL
===================================

Think of each cache line as a "token".
A core can only WRITE to a line when it OWNS the token (M state).
If another core wants to write, it must REQUEST the token from the owner.

                     Token Request (RFO)
  Core 0: [owns] ──────────────────────────────────────► Core 1: [wants to write]
           │                                                        │
           │ Token Transfer (+ cache line flush)                    │
           └────────────────────────────────────────────────────────┘
           
Cost:  ~40-200 cycles per transfer (depends on topology)

DESIGN GOAL: Minimize token transfers.
  - If only one core writes: keep token local (good)
  - If multiple cores write: spread data across lines (padding)
  - If cores MOSTLY read: sharing is fine (S state, no RFO needed)
```

### Mental Model 2: The "Working Set" Model

```
WORKING SET MODEL
==================

L1 Cache: 32KB = 512 cache lines of 64 bytes
L2 Cache: 256KB = 4096 cache lines

Your inner loop accesses N bytes total.
If N ≤ 32KB: L1 hit rate should be high → fast
If N ≤ 256KB: L2 hit rate should be high → medium
If N > 256KB: L3 or DRAM → slow

OPTIMIZATION STRATEGY:
  1. Identify your hot loop's working set size
  2. If working set > L1: restructure data to reduce it
     - Strip-mine loops (process in 32KB chunks)
     - Use SoA (Structure of Arrays) instead of AoS (Array of Structures)
     - Cache-oblivious algorithms (Morton order, etc.)
```

### Mental Model 3: The "Ping-Pong" Anti-Pattern

```
CACHE LINE PING-PONG
=====================

When two cores alternate writes to the same cache line,
the line physically travels back and forth (ping-pong):

  Time 0: Core 0 owns line [writes counter++]
  Time 1: Core 1 wants line → Core 0 sends it [~100ns]
           Core 1 owns line [writes counter++]
  Time 2: Core 0 wants line → Core 1 sends it [~100ns]
           Core 0 owns line [writes counter++]
  ...

Each write costs ~100ns (cross-socket even more).
Normal write without sharing: ~1ns.
Ping-pong is 100x slower!

WHEN THIS HAPPENS:
  - Shared mutex/spinlock (intentional, but still costly)
  - False sharing (accidental → fix with padding)
  - Shared atomic counter (use per-CPU then aggregate)
```

### Pattern: AoS vs SoA (Array of Structures vs Structure of Arrays)

```c
/* AoS (Array of Structures): common but cache-unfriendly for partial access */
struct Particle_AoS {
    float x, y, z;    /* position: 12 bytes */
    float vx, vy, vz; /* velocity: 12 bytes */
    float mass;        /* 4 bytes */
    float charge;      /* 4 bytes */
    int   type;        /* 4 bytes */
    /* ... total: 36 bytes, 1 cache line per particle */
};

struct Particle_AoS particles[1000];

/* To update positions (hot loop): only need x,y,z,vx,vy,vz */
for (int i = 0; i < 1000; i++) {
    particles[i].x += particles[i].vx * dt;  /* loads full 64-byte line */
    particles[i].y += particles[i].vy * dt;  /* just to use 24 bytes! */
    particles[i].z += particles[i].vz * dt;
}
/* Efficiency: 24/64 = 37.5% of each cache line is actually used */

/* SoA (Structure of Arrays): cache-friendly for partial access */
struct Particles_SoA {
    float x[1000], y[1000], z[1000];     /* positions: 3 * 4KB */
    float vx[1000], vy[1000], vz[1000];  /* velocities: 3 * 4KB */
    float mass[1000], charge[1000];
    int   type[1000];
};

struct Particles_SoA p;

/* Position update loop: accesses only position + velocity arrays */
for (int i = 0; i < 1000; i++) {
    p.x[i] += p.vx[i] * dt;  /* streams through x[] and vx[] */
    p.y[i] += p.vy[i] * dt;  /* no mass/charge/type loaded at all */
    p.z[i] += p.vz[i] * dt;
}
/* Efficiency: 64/64 = 100% of each cache line used (all floats relevant) */
/* Also enables SIMD auto-vectorization! */
```

---

## 22. Common Pitfalls and Anti-Patterns

### Pitfall 1: Aligning the Wrong Thing

```c
/* WRONG: Aligning the pointer, not the data it points to */
char * __attribute__((aligned(64))) ptr;  /* aligns the pointer variable */
/* The MEMORY ptr points to may not be aligned! */

/* RIGHT: Align the allocation */
char *ptr = aligned_alloc(64, size);  /* aligns the allocated memory */

/* RIGHT: Align the static/global data */
static char buffer[256] __attribute__((aligned(64)));  /* data is aligned */
```

### Pitfall 2: Forgetting About Heap Allocation Alignment

```c
/* malloc() only guarantees alignment to max_align_t (usually 16 bytes).
 * For cache-line alignment, always use aligned_alloc or posix_memalign. */

struct CacheAligned { ... } __attribute__((aligned(64)));

/* WRONG: malloc doesn't honor __attribute__((aligned)) on the TYPE */
struct CacheAligned *p = malloc(sizeof(*p));  /* may not be 64-byte aligned! */

/* RIGHT: use aligned allocation */
struct CacheAligned *p;
posix_memalign((void**)&p, 64, sizeof(*p));
/* OR */
struct CacheAligned *p = aligned_alloc(64, sizeof(*p));
```

### Pitfall 3: Over-Padding (Cache Pollution)

```c
/* Anti-pattern: Padding everything blindly wastes memory.
 * Each padded struct uses 64 bytes even if data is 8 bytes.
 * With thousands of objects, this inflates memory 8x.
 *
 * Rule: Only pad structs that are CONCURRENTLY WRITTEN BY MULTIPLE THREADS.
 * Read-only data doesn't need padding (S state is fine).
 * Single-threaded data doesn't need padding.
 */

/* WASTEFUL: padding a 4-byte struct used only in single-threaded code */
struct __attribute__((aligned(64))) Counter {
    int value;
    /* 60 bytes wasted! */
};
Counter my_array[1000000];  /* 64MB instead of 4MB */

/* CORRECT: pad only when needed */
typedef struct { int value; } Counter;  /* 4 bytes, packed */
Counter my_array[1000000];  /* 4MB — and sequential access is cache-friendly! */
```

### Pitfall 4: False Sharing Through Pointer Aliasing

```c
/* When you heap-allocate multiple objects, the allocator may place
 * them on the same cache line even if you used aligned structs! */

struct __attribute__((aligned(64))) Worker {
    int processed;
    char _pad[60];
};

/* WRONG: If the allocator gives you sequential memory: */
Worker *w0 = malloc(sizeof(Worker));  /* might be at 0x40 */
Worker *w1 = malloc(sizeof(Worker));  /* might be at 0x80 — OK */
Worker *w2 = malloc(sizeof(Worker));  /* might be at 0xC0 — OK */
/* Actually: with malloc, each is page-aligned (4KB), so no sharing */
/* But with a custom slab allocator or pool, this COULD happen */

/* SAFE: Allocate as an array with proper alignment */
Worker *workers = aligned_alloc(64, sizeof(Worker) * num_workers);
/* Now workers[i] is always at address: base + i * 64 — guaranteed aligned */
```

### Pitfall 5: Not Considering WRITE-Heavy vs READ-Heavy Access

```c
/* False sharing only matters for WRITES.
 * If multiple cores all READ the same cache line simultaneously,
 * there is NO performance problem — all get S state, no RFO needed.
 *
 * MISTAKE: Padding read-only data (wastes memory, no benefit).
 * CORRECT: Pad only MUTABLE data accessed from multiple cores.
 */

/* These are read once at startup, never written: */
static const int CONFIG_VALUES[] = { 1, 2, 3, 4, 5, 6, 7, 8 };
/* Fine to leave them packed — all CPUs can read in S state */

/* These are incremented by different threads: */
/* MUST pad each one to its own cache line */
static _Atomic int THREAD_COUNTERS[8] __attribute__((aligned(64)));
/* Each counter must be on a different cache line! */
```

---

## 23. Quick Reference Card

### Linux Kernel Macros Summary

```
MACRO                                 USE CASE
─────────────────────────────────────────────────────────────────────────
__cacheline_aligned                   Global/static data: align to L1 line
____cacheline_aligned                 Global data: align + section placement
____cacheline_aligned_in_smp          SMP-only: most common in kernel hotpaths
__cacheline_internodealigned_in_smp   Cross-NUMA node shared data
__read_mostly                         Frequently read, rarely written data
ALIGN(x, 64)                          Round x up to next multiple of 64
CACHELINE_ALIGN(size)                 Round size up to cache line boundary
L1_CACHE_BYTES                        Cache line size constant (usually 64)
SMP_CACHE_BYTES                       SMP cache line size (usually == L1_CACHE_BYTES)
```

### C Attribute Summary

```
ATTRIBUTE                             EFFECT
─────────────────────────────────────────────────────────────────────────
__attribute__((aligned(64)))          Align variable or struct to 64 bytes
__attribute__((packed))               Remove all padding (DANGEROUS)
__attribute__((section("...")))       Place in specific ELF section
alignas(64)                           C11 alignment specifier (same as above)
aligned_alloc(64, size)               Heap-allocate 64-byte-aligned memory
posix_memalign(&ptr, 64, size)        POSIX aligned heap allocation
```

### Rust Attributes Summary

```
ATTRIBUTE / FUNCTION                  EFFECT
─────────────────────────────────────────────────────────────────────────
#[repr(align(64))]                    Align struct to 64 bytes
#[repr(C)]                            C-compatible struct layout
#[repr(C, align(64))]                 C layout + 64-byte alignment
std::mem::align_of::<T>()             Get alignment of type T
std::mem::size_of::<T>()              Get size of type T
Layout::from_size_align(sz, 64)       Create allocation layout
std::alloc::alloc(layout)             Allocate with specific alignment
crossbeam_utils::CachePadded          Ready-made cache padding wrapper
```

### Go Patterns Summary

```go
// Pad struct to cache line
type PaddedCounter struct {
    value int64
    _     [64 - unsafe.Sizeof(int64(0))]byte
}

// Force cache-line alignment of struct
// (Go doesn't have #[repr(align(N))], use padding)
type CacheLinePadded struct {
    data int64
    _    [56]byte  // 64 - 8 = 56 bytes padding
}

// Check alignment at runtime
addr := uintptr(unsafe.Pointer(&val))
isAligned := addr % 64 == 0

// Atomic access to int64 (Go guarantees 64-bit alignment on 64-bit systems)
import "sync/atomic"
atomic.AddInt64(&val, 1)
```

### Decision Flowchart

```
IS CACHE-LINE ALIGNMENT NEEDED?
================================

Is data accessed from multiple goroutines/threads?
├── NO → No alignment needed for false sharing purposes.
│         Consider alignment for performance (SIMD, prefetcher).
└── YES
    │
    Do different threads/cores WRITE to different parts of the data?
    ├── NO (all reads, or one writer) → No false sharing.
    │                                  Consider __read_mostly.
    └── YES
        │
        Do the written parts fit on the SAME 64-byte cache line?
        ├── NO (they're already on different lines) → No problem.
        └── YES → FALSE SHARING! Apply one of:
                  1. Padding: add bytes to push each to own line
                  2. Per-CPU/per-thread variables
                  3. Reduce sharing: batch writes, aggregate later
                  4. Use different algorithm (avoid shared mutable state)
```

---

## Appendix A: Checking Cache Line Size at Runtime

```c
/* Linux: read from sysfs */
FILE *f = fopen("/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size", "r");
int line_size;
fscanf(f, "%d", &line_size);
fclose(f);
printf("Cache line size: %d bytes\n", line_size);

/* Alternative: using cpuid (x86 only) */
#include <cpuid.h>
unsigned a, b, c, d;
__cpuid(1, a, b, c, d);
int clflush_size = ((b >> 8) & 0xFF) * 8;
printf("Cache line size (cpuid): %d bytes\n", clflush_size);

/* Programmatic (Linux kernel): */
/* boot_cpu_data.x86_cache_alignment */

/* Shell: */
/* getconf LEVEL1_DCACHE_LINESIZE */
```

## Appendix B: Useful Shell Commands

```bash
# CPU cache topology
lscpu | grep -i cache
getconf LEVEL1_DCACHE_LINESIZE   # L1 cache line size
getconf LEVEL1_DCACHE_SIZE       # L1 cache size
getconf LEVEL2_CACHE_LINESIZE    # L2 cache line size

# NUMA topology
numactl --hardware
numastat

# Cache sizes from sysfs (per CPU)
ls /sys/devices/system/cpu/cpu0/cache/
cat /sys/devices/system/cpu/cpu0/cache/index0/size         # L1I
cat /sys/devices/system/cpu/cpu0/cache/index1/size         # L1D
cat /sys/devices/system/cpu/cpu0/cache/index2/size         # L2
cat /sys/devices/system/cpu/cpu0/cache/index3/size         # L3
cat /sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size  # line size

# x86: read CPUID cache info
cpuid | grep -i "cache line"

# Check struct size/alignment in kernel
# (add to your kernel module or use pahole)
pr_info("struct task_struct size: %zu\n", sizeof(struct task_struct));

# Compile and check struct sizes
echo '#include <stdio.h>
#include <stddef.h>
struct S { char a; long b; short c; };
int main() {
    printf("size=%zu align=%zu\n", sizeof(struct S), _Alignof(struct S));
    return 0;
}' | gcc -x c - -o /tmp/check && /tmp/check
```

---

*This guide covers cache-line alignment from the transistor level up through Linux kernel internals, userspace C/Go/Rust implementations, and production profiling techniques. Mastery of these concepts is a hallmark of systems engineers who build the fastest software in the world.*

The guide is complete — 23 sections covering every layer from silicon to source code. Here's a map of what's inside and why it matters:

**Foundational sections (1–4)** build the mental model from scratch: why caches exist (the memory wall), what a 64-byte cache line actually is, how set-associative caches index and tag memory, and how MESI coherency protocol makes multi-core coordination expensive.

**The core problem (5–7)** explains false sharing vs true sharing with ASCII memory layouts, performance numbers (up to 100x regression), and the natural alignment rules that govern when padding is necessary.

**Linux kernel internals (8, 17)** cover every macro: `____cacheline_aligned_in_smp`, `__read_mostly`, `__ro_after_init`, `CACHELINE_ALIGN`, `SMP_CACHE_BYTES`, and how real kernel structs like `struct rq`, `struct task_struct`, and `struct net_device` apply these.

**Implementations (10–12)** provide production-quality code in C, Go, and Rust — including false sharing benchmarks, SPSC lock-free ring buffers with head/tail on separate cache lines, per-CPU counter patterns, and a Go struct layout analyzer.

**Advanced topics (14–19)** cover NUMA-aware alignment, atomic operation cost models, the Michael-Scott lock-free queue with cache-conscious design, DMA alignment requirements, and the full memory barrier API.

**Profiling (20)** gives you `perf stat`, `perf c2c` (false sharing detection), Valgrind Cachegrind, `pahole` for struct layout inspection, and cycle-accurate `rdtsc` timing.

The mental models — ownership token, working set, ping-pong anti-pattern — are what separate engineers who *apply rules* from those who *reason from first principles*.