# Cache Efficiency Mastery: A World-Class Engineer's Complete Guide

> *"The difference between a good programmer and a great one is understanding what the machine actually does."*  
> — Every systems engineer who has ever profiled a program

---

## Table of Contents

1. [The Memory Hierarchy — Why This Exists](#1-the-memory-hierarchy)
2. [CPU Cache Architecture Deep Dive](#2-cpu-cache-architecture)
3. [Cache Lines — The Atom of Memory Transfer](#3-cache-lines)
4. [Types of Cache Misses — The Three Cs](#4-types-of-cache-misses)
5. [Locality — Temporal and Spatial](#5-locality)
6. [Cache Mapping — Direct, Set-Associative, Fully Associative](#6-cache-mapping)
7. [Data Layout Strategies — AoS vs SoA vs AoSoA](#7-data-layout-strategies)
8. [Cache-Friendly Algorithms](#8-cache-friendly-algorithms)
9. [False Sharing — The Silent Killer in Parallel Code](#9-false-sharing)
10. [Hardware Prefetching and Software Prefetching](#10-prefetching)
11. [NUMA Architecture and Cache Implications](#11-numa-architecture)
12. [TLB — Translation Lookaside Buffer](#12-tlb)
13. [Write Policies — Write-Through vs Write-Back](#13-write-policies)
14. [Memory Barriers and Cache Coherence Protocols (MESI)](#14-cache-coherence)
15. [Linux Kernel Cache Concepts](#15-linux-kernel-cache-concepts)
16. [Compiler Optimizations for Cache](#16-compiler-optimizations)
17. [Profiling Tools — Seeing Cache Behavior](#17-profiling-tools)
18. [Advanced Patterns — Tiling, Blocking, Loop Transformations](#18-advanced-patterns)
19. [Allocator Strategies for Cache Efficiency](#19-allocator-strategies)
20. [Production Case Studies](#20-production-case-studies)

---

## 1. The Memory Hierarchy

### What is the Memory Hierarchy?

Every computer system has multiple levels of storage. The fundamental problem: **fast memory is expensive and small; cheap memory is large and slow**. The solution is a hierarchy — multiple layers, each faster but smaller than the one below it.

```
Speed ↑                Size ↓
───────────────────────────────────────────────────
│  CPU Registers    │  ~64 bytes     │  < 1 cycle  │
│  L1 Cache         │  32–64 KB      │  4–5 cycles │
│  L2 Cache         │  256KB–1MB     │  12 cycles  │
│  L3 Cache (LLC)   │  8–64 MB       │  30–40 cyc  │
│  Main RAM (DRAM)  │  8–512 GB      │  ~200 cyc   │
│  NVMe SSD         │  1–4 TB        │  ~100,000   │
│  HDD / Network    │  Terabytes     │  Millions   │
───────────────────────────────────────────────────
Speed ↓                Size ↑
```

### Why Does This Matter for Code?

Consider a simple loop that sums an array of 64 million integers:

- **If data is in L1 cache**: completes in ~0.2 seconds
- **If data is in RAM**: completes in ~2 seconds — **10× slower**

Your algorithm might be O(n) and "optimal" in theory, but if it causes constant RAM accesses, a competitor with an O(n log n) algorithm that fits in cache can beat you.

**Key insight**: *The machine you program is not the abstract RAM model you were taught. It is a deeply hierarchical system where data placement determines performance more than algorithmic complexity at certain scales.*

---

## 2. CPU Cache Architecture

### What is a CPU Cache?

A CPU cache is a small, extremely fast SRAM (Static RAM) integrated directly into or near the processor die. It stores **copies** of recently used data from main memory so the CPU can access them without waiting for slow DRAM.

### Cache Levels Explained

**L1 Cache (Level 1)**
- Sits directly inside each CPU core
- Split into: **L1i** (instruction cache) and **L1d** (data cache)
- Typical size: 32–64 KB per core
- Latency: 4–5 clock cycles
- This is where your hot loop variables must live

**L2 Cache (Level 2)**
- Usually per-core (sometimes shared between 2 cores)
- Typical size: 256 KB – 1 MB per core
- Latency: 12–15 clock cycles
- Unified (both instructions and data)

**L3 Cache / LLC (Last Level Cache)**
- Shared across all cores on the same socket
- Typical size: 8 MB – 64 MB
- Latency: 30–40 clock cycles
- This is the last line of defense before main memory

**Checking your actual cache topology on Linux:**
```bash
# View cache sizes
lscpu | grep -i cache

# Detailed topology
cat /sys/devices/system/cpu/cpu0/cache/index*/size
cat /sys/devices/system/cpu/cpu0/cache/index*/level
cat /sys/devices/system/cpu/cpu0/cache/index*/type

# Using lstopo (hwloc package)
lstopo --of txt
```

### Cache Inclusion Policies

**Inclusive**: L3 contains copies of everything in L1 and L2. Simpler coherence, wastes L3 space.  
**Exclusive**: Each level holds unique data. More effective total capacity.  
**Non-inclusive (NINE)**: Used by AMD Zen; L3 may or may not contain L1/L2 contents.

Intel historically used inclusive L3. AMD Zen uses NINE. This affects how evictions cascade.

---

## 3. Cache Lines

### What is a Cache Line?

**A cache line is the minimum unit of data transferred between cache levels and between cache and RAM.**

Modern CPUs use **64-byte cache lines** (almost universally on x86-64 and ARM64). This means:

> When the CPU reads a single byte from RAM, it actually fetches the entire 64-byte block containing that byte.

```
RAM Layout (visualized in 64-byte chunks):
┌──────────────────────────────────────────────────────────────┐
│  Byte 0 ... Byte 63   ← Cache Line 0                        │
├──────────────────────────────────────────────────────────────┤
│  Byte 64 ... Byte 127 ← Cache Line 1                        │
├──────────────────────────────────────────────────────────────┤
│  Byte 128 ... Byte 191 ← Cache Line 2                       │
└──────────────────────────────────────────────────────────────┘

If you access Byte 65, the CPU loads ALL of Cache Line 1 (bytes 64–127).
```

### Implications of Cache Lines

1. **Spatial locality pays off automatically**: Access byte 65, then byte 66? The second access is free (already in cache).
2. **Wasted bandwidth**: Access byte 65 of every cache line = load 64 bytes, use 1. 98% waste.
3. **Struct padding matters**: Misaligned structs can straddle two cache lines.

### Cache Line Alignment in Code

**C — Aligned struct:**
```c
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

#define CACHE_LINE_SIZE 64

/* Force alignment to cache line boundary */
typedef struct __attribute__((aligned(CACHE_LINE_SIZE))) {
    int64_t counter;
    int64_t padding[7]; /* Fill the rest of the cache line: 8 * 8 = 64 bytes */
} aligned_counter_t;

/* Verify at compile time */
_Static_assert(sizeof(aligned_counter_t) == CACHE_LINE_SIZE,
               "aligned_counter_t must be exactly one cache line");

/* BAD: Two counters share a cache line — false sharing risk */
typedef struct {
    int64_t counter_a;
    int64_t counter_b;
} bad_counters_t;

/* GOOD: Each counter owns its cache line */
typedef struct {
    aligned_counter_t a;
    aligned_counter_t b;
} good_counters_t;

int main(void) {
    printf("Cache line size: %d bytes\n", CACHE_LINE_SIZE);
    printf("aligned_counter_t size: %zu bytes\n", sizeof(aligned_counter_t));
    printf("good_counters_t size: %zu bytes\n", sizeof(good_counters_t));
    return 0;
}
```

**Go — Cache line awareness:**
```go
package main

import (
	"fmt"
	"unsafe"
)

const CacheLineSize = 64

// CacheLinePad is used to pad structs to cache line boundaries.
// This prevents false sharing between struct fields accessed by different goroutines.
type CacheLinePad [CacheLineSize - unsafe.Sizeof(uint64(0))]byte

// PaddedCounter: each counter lives on its own cache line.
// Critical pattern for per-CPU or per-goroutine counters.
type PaddedCounter struct {
	value uint64
	_     CacheLinePad // anonymous field = padding
}

// NaiveCounters: WRONG — both share same cache line
type NaiveCounters struct {
	a uint64
	b uint64
}

// SafeCounters: CORRECT — each on own cache line
type SafeCounters struct {
	a PaddedCounter
	b PaddedCounter
}

func main() {
	var sc SafeCounters
	fmt.Printf("SafeCounters size: %d bytes\n", unsafe.Sizeof(sc))
	fmt.Printf("Each counter size: %d bytes\n", unsafe.Sizeof(sc.a))

	// Verify alignment
	fmt.Printf("a offset: %d\n", unsafe.Offsetof(sc.a))
	fmt.Printf("b offset: %d\n", unsafe.Offsetof(sc.b))
	// b offset should be exactly 64 (one cache line away from a)
}
```

**Rust — Cache line padding:**
```rust
use std::mem;

const CACHE_LINE_SIZE: usize = 64;

/// Pad a type T to occupy a full cache line.
/// Prevents false sharing when multiple instances are placed adjacently.
#[repr(C, align(64))]
pub struct CacheAligned<T> {
    value: T,
    // Compiler handles the rest of the padding due to `align(64)`
    _pad: [u8; CACHE_LINE_SIZE - mem::size_of::<T>()],
    // Note: This only works when size_of::<T>() <= CACHE_LINE_SIZE.
    // For generic T, use a const generic workaround or crossbeam's CachePadded.
}

// In production, prefer crossbeam::utils::CachePadded<T> which handles
// the generic sizing correctly using const generics.

/// Production pattern using crossbeam (add to Cargo.toml: crossbeam = "0.8")
// use crossbeam::utils::CachePadded;
// let counter = CachePadded::new(AtomicU64::new(0));

/// Manual implementation for demonstration:
#[repr(C, align(64))]
pub struct PaddedU64 {
    pub value: u64,
    _padding: [u8; 56], // 64 - 8 = 56 bytes of padding
}

impl PaddedU64 {
    pub fn new(v: u64) -> Self {
        PaddedU64 { value: v, _padding: [0u8; 56] }
    }
}

fn main() {
    assert_eq!(mem::size_of::<PaddedU64>(), 64);
    assert_eq!(mem::align_of::<PaddedU64>(), 64);
    
    let a = PaddedU64::new(0);
    let b = PaddedU64::new(0);
    
    // These will be on separate cache lines if allocated adjacently in an array
    let arr = [PaddedU64::new(0), PaddedU64::new(0)];
    println!("arr[0] addr: {:p}", &arr[0].value);
    println!("arr[1] addr: {:p}", &arr[1].value);
    // Difference should be exactly 64 bytes
}
```

---

## 4. Types of Cache Misses — The Three Cs

Cache misses are categorized into three fundamental types, known as **the Three Cs**:

### 4.1 Compulsory Misses (Cold Misses)

**Definition**: The first time you access any data, it cannot be in cache. This miss is unavoidable.

- Also called "cold miss" or "first-reference miss"
- Irreducible — every byte must be fetched at least once
- Mitigation: prefetching (bring data before you need it)

```
First access to array[0..N]:
Access 0   → MISS (cold) → loads cache line containing elements 0..15
Access 1   → HIT  (spatial locality pays off)
...
Access 15  → HIT
Access 16  → MISS (cold) → loads next cache line
```

### 4.2 Capacity Misses

**Definition**: Your working set is larger than the cache. Even with perfect replacement policy, misses occur.

- Occurs when the set of data you're actively using exceeds cache capacity
- Cannot be fixed by a better replacement policy
- Mitigation: reduce working set size, use cache blocking/tiling

```
L1 = 32KB. Your matrix = 64KB.
Even if you access elements perfectly sequentially,
older cache lines get evicted before you reuse them.
```

### 4.3 Conflict Misses

**Definition**: Two addresses map to the same cache set, causing evictions even though the cache has free capacity elsewhere.

- Only affects direct-mapped and set-associative caches
- Fully associative caches have no conflict misses
- Mitigation: pad data structures, use different base addresses

```
Direct-mapped cache: address mod cache_size → set
Array A at address 0x0000 and Array B at address 0x8000
Both map to set 0, 1, 2, ... (same sets!)
Alternating access A[i], B[i] = constant misses.
```

**A 4th C — Coherence Misses** (in multicore systems):
- Occurs when another core modifies a cache line you have
- Your copy is invalidated (MESI protocol)
- Related to false sharing

---

## 5. Locality

### Temporal Locality

**Definition**: If you access data item X, you are likely to access it again soon.

```
for i in 0..N:
    sum += array[i]   # array[i] accessed once per iteration — low temporal locality
    count += 1        # count accessed every iteration — HIGH temporal locality
```

`count` has perfect temporal locality. Keep frequently reused variables in registers or L1.

### Spatial Locality

**Definition**: If you access data item X, you are likely to access data near X soon.

```
Accessing array[0], array[1], array[2]... → HIGH spatial locality
Accessing array[0], array[1000], array[500000]... → LOW spatial locality
```

**The stride problem**: A stride of 1 element = sequential, best spatial locality. A stride of 16 elements on an int array (64-byte cache line = 16 ints) = exactly one element per cache line loaded. You use 4 bytes, waste 60.

### Measuring Stride Impact — C:
```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_SIZE (1 << 26)  /* 64M elements = 256MB */
#define ITERATIONS 3

/* Sum array with a given stride */
static uint64_t sum_with_stride(const int32_t *arr, size_t n, size_t stride) {
    uint64_t sum = 0;
    for (size_t i = 0; i < n; i += stride) {
        sum += arr[i];
    }
    return sum;
}

int main(void) {
    int32_t *arr = calloc(ARRAY_SIZE, sizeof(int32_t));
    if (!arr) {
        perror("calloc");
        return 1;
    }

    /* Initialize */
    for (size_t i = 0; i < ARRAY_SIZE; i++) {
        arr[i] = (int32_t)(i & 0xFF);
    }

    size_t strides[] = {1, 2, 4, 8, 16, 32, 64};
    printf("%-10s %-15s %-15s\n", "Stride", "Time (ms)", "Throughput");
    printf("%-10s %-15s %-15s\n", "------", "---------", "----------");

    for (size_t s = 0; s < sizeof(strides) / sizeof(strides[0]); s++) {
        size_t stride = strides[s];
        
        struct timespec t0, t1;
        clock_gettime(CLOCK_MONOTONIC, &t0);
        
        volatile uint64_t result = 0;
        for (int it = 0; it < ITERATIONS; it++) {
            result += sum_with_stride(arr, ARRAY_SIZE, stride);
        }
        
        clock_gettime(CLOCK_MONOTONIC, &t1);
        
        double ms = (t1.tv_sec - t0.tv_sec) * 1000.0 +
                    (t1.tv_nsec - t0.tv_nsec) / 1e6;
        size_t elements = ARRAY_SIZE / stride;
        double gb_s = (double)(elements * sizeof(int32_t) * ITERATIONS) / (ms * 1e6);
        
        printf("stride=%-4zu  %-15.2f %-10.2f GB/s  (result=%lu)\n",
               stride, ms, gb_s, result);
    }

    free(arr);
    return 0;
}
/*
 * Compile: gcc -O2 -o stride stride.c
 * Expected output: stride=1 fastest, stride=64 approaching random access performance
 */
```

**Go — Stride benchmark:**
```go
package main

import (
	"fmt"
	"runtime"
	"time"
	"unsafe"
)

const ArraySize = 1 << 24 // 16M int32s = 64MB

func sumStride(arr []int32, stride int) int64 {
	var sum int64
	for i := 0; i < len(arr); i += stride {
		sum += int64(arr[i])
	}
	return sum
}

func benchmark(arr []int32, stride int, iterations int) time.Duration {
	// Warm up
	_ = sumStride(arr, stride)

	start := time.Now()
	var result int64
	for i := 0; i < iterations; i++ {
		result += sumStride(arr, stride)
	}
	runtime.KeepAlive(result)
	return time.Since(start)
}

func main() {
	arr := make([]int32, ArraySize)
	for i := range arr {
		arr[i] = int32(i & 0xFF)
	}

	fmt.Printf("Array size: %d MB\n", int(unsafe.Sizeof(arr[0]))*ArraySize/(1<<20))
	fmt.Printf("%-12s  %-15s  %-15s\n", "Stride", "Duration", "Elements/sec")
	fmt.Println("----------------------------------------------")

	strides := []int{1, 2, 4, 8, 16, 32, 64, 128}
	const iterations = 5

	for _, stride := range strides {
		dur := benchmark(arr, stride, iterations)
		elements := ArraySize / stride * iterations
		elemsPerSec := float64(elements) / dur.Seconds()
		fmt.Printf("stride=%-5d  %-15v  %.2e elem/s\n", stride, dur, elemsPerSec)
	}
}
```

**Rust — Stride benchmark:**
```rust
use std::time::Instant;

const ARRAY_SIZE: usize = 1 << 24; // 16M elements

fn sum_stride(arr: &[i32], stride: usize) -> i64 {
    arr.iter()
        .step_by(stride)
        .map(|&x| x as i64)
        .sum()
}

fn benchmark(arr: &[i32], stride: usize, iterations: usize) -> std::time::Duration {
    // Warm up — don't count cold cache effects
    let _ = sum_stride(arr, stride);

    let start = Instant::now();
    let mut result: i64 = 0;
    for _ in 0..iterations {
        result = result.wrapping_add(sum_stride(arr, stride));
    }
    // Prevent dead code elimination
    std::hint::black_box(result);
    start.elapsed()
}

fn main() {
    let arr: Vec<i32> = (0..ARRAY_SIZE as i32).map(|x| x & 0xFF).collect();

    println!("Array size: {} MB", ARRAY_SIZE * 4 / (1 << 20));
    println!("{:<12}  {:<20}  {:<15}", "Stride", "Duration", "Elements/sec");
    println!("{}", "-".repeat(50));

    let strides = [1usize, 2, 4, 8, 16, 32, 64, 128];
    const ITERATIONS: usize = 5;

    for &stride in &strides {
        let dur = benchmark(&arr, stride, ITERATIONS);
        let elements = (ARRAY_SIZE / stride) * ITERATIONS;
        let elems_per_sec = elements as f64 / dur.as_secs_f64();
        println!(
            "stride={:<5}  {:<20?}  {:.2e} elem/s",
            stride, dur, elems_per_sec
        );
    }
}
```

---

## 6. Cache Mapping

### What is Cache Mapping?

Cache mapping is the strategy a cache uses to decide **which cache set** a given memory address maps to, and **which way** within that set can hold it.

### 6.1 Direct-Mapped Cache

Each memory address maps to exactly **one** cache location.

```
Cache Set Index = (memory_address / cache_line_size) mod num_cache_sets

Example:
cache_line_size = 64
num_cache_sets = 1024

address 0x0000 → set 0
address 0x0040 → set 1
address 0x10000 → set (0x10000/64) mod 1024 = 256 mod 1024 = 256
address 0x10400 → set (0x10400/64) mod 1024 = 260 mod 1024 = 260
```

**Problem**: Two addresses that differ by exactly `cache_size` collide in the same set. Alternating access = 100% conflict misses.

### 6.2 Set-Associative Cache (N-Way)

Each address maps to one **set**, but the set holds **N ways** (N cache lines). If N=8, you can have 8 different lines in the same set simultaneously.

```
Modern typical: 
  L1: 8-way set associative
  L2: 8-way
  L3: 16-way or higher

Set Index = (address / line_size) mod num_sets
Way = chosen by replacement policy (LRU, pseudo-LRU)
```

Higher associativity → fewer conflict misses → more hardware complexity → slightly higher latency.

### 6.3 Fully Associative Cache

Any address can go in any cache slot. Zero conflict misses. Only used for small caches (TLB, victim cache) due to hardware cost — requires comparing all tags simultaneously.

### Cache Address Decomposition (x86-64, 64-byte lines, 8-way L1 32KB):

```
64-bit virtual address:
┌─────────────────────────┬──────────────┬──────────────┐
│         TAG             │  Set Index   │   Offset     │
│       (bits 63-11)      │  (bits 10-6) │  (bits 5-0)  │
└─────────────────────────┴──────────────┴──────────────┘

Offset:     6 bits → 2^6 = 64 bytes per cache line
Set Index:  5 bits → 2^5 = 32 sets × 8 ways = 256 lines × 64 bytes = 16384... 
Wait: 32KB / 64 bytes = 512 lines. 512 lines / 8 ways = 64 sets → 6-bit set index
```

---

## 7. Data Layout Strategies

### What is AoS vs SoA?

These are two fundamental ways to organize collections of structured data. The choice has massive cache implications.

### 7.1 Array of Structures (AoS)

Each element is a struct, and you have an array of these structs.

```
Memory layout:
[x0 y0 z0 mass0 | x1 y1 z1 mass1 | x2 y2 z2 mass2 | ...]
 ← particle 0 →   ← particle 1 →   ← particle 2 →
```

**Good for**: Accessing all fields of one particle at a time.  
**Bad for**: Accessing one field across many particles (e.g., all x values).

### 7.2 Structure of Arrays (SoA)

One array per field.

```
Memory layout:
xs:    [x0 | x1 | x2 | x3 | ... xN]
ys:    [y0 | y1 | y2 | y3 | ... yN]
zs:    [z0 | z1 | z2 | z3 | ... zN]
masses:[m0 | m1 | m2 | m3 | ... mN]
```

**Good for**: Vectorized operations on a single field (SIMD friendly).  
**Bad for**: Operations needing all fields of one element simultaneously (more pointer chasing).

### 7.3 AoSoA (Array of Structures of Arrays) — The Expert Pattern

Hybrid approach used in high-performance physics engines, game engines (Unity's ECS, Unreal).

```
Chunk of 8 particles:
[x0..x7 | y0..y7 | z0..z7 | m0..m7]  ← fits in cache, SIMD-friendly
[x8..x15 | ...]
```

### Complete Implementation — C (N-body simulation):

```c
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define N_PARTICLES 100000
#define SIMD_WIDTH  8  /* AVX2: 8 floats per register */
#define SOFTENING   1e-9f

/* ── AoS Layout ─────────────────────────────────────────────────── */
typedef struct {
    float x, y, z;
    float vx, vy, vz;
    float mass;
    float _pad; /* align to 32 bytes */
} particle_aos_t;

/* ── SoA Layout ─────────────────────────────────────────────────── */
typedef struct {
    float *x, *y, *z;
    float *vx, *vy, *vz;
    float *mass;
    size_t count;
} particles_soa_t;

/* ── AoSoA Layout (SIMD_WIDTH elements per sub-array) ───────────── */
#define CHUNK_SIZE SIMD_WIDTH
typedef struct {
    float x[CHUNK_SIZE];
    float y[CHUNK_SIZE];
    float z[CHUNK_SIZE];
    float mass[CHUNK_SIZE];
} particle_chunk_t;

/* ───────────────────────────────────────────────────────────────── */
/* Utility: aligned allocation                                        */
static void *aligned_alloc_safe(size_t align, size_t size) {
    void *ptr = NULL;
    if (posix_memalign(&ptr, align, size) != 0) return NULL;
    return ptr;
}

/* ───────────────────────────────────────────────────────────────── */
/* AoS: compute sum of all x-coordinates (simulates "get all X")    */
static double sum_x_aos(const particle_aos_t *particles, size_t n) {
    double sum = 0.0;
    for (size_t i = 0; i < n; i++) {
        sum += particles[i].x;  /* Every access jumps 32 bytes */
    }
    return sum;
}

/* SoA: compute sum of all x-coordinates                            */
static double sum_x_soa(const particles_soa_t *p) {
    double sum = 0.0;
    /* Sequential access through contiguous array — cache friendly  */
    for (size_t i = 0; i < p->count; i++) {
        sum += p->x[i];
    }
    return sum;
}

/* ───────────────────────────────────────────────────────────────── */
/* AoS: gravity update (needs all fields of each particle)          */
static void gravity_step_aos(particle_aos_t *p, size_t n, float dt) {
    for (size_t i = 0; i < n; i++) {
        float fx = 0.0f, fy = 0.0f, fz = 0.0f;
        for (size_t j = 0; j < n; j++) {
            if (i == j) continue;
            float dx = p[j].x - p[i].x;
            float dy = p[j].y - p[i].y;
            float dz = p[j].z - p[i].z;
            float dist_sq = dx*dx + dy*dy + dz*dz + SOFTENING;
            float inv_dist = 1.0f / sqrtf(dist_sq);
            float inv_dist3 = inv_dist * inv_dist * inv_dist;
            float f = p[j].mass * inv_dist3;
            fx += dx * f;
            fy += dy * f;
            fz += dz * f;
        }
        p[i].vx += fx * dt;
        p[i].vy += fy * dt;
        p[i].vz += fz * dt;
    }
    for (size_t i = 0; i < n; i++) {
        p[i].x += p[i].vx * dt;
        p[i].y += p[i].vy * dt;
        p[i].z += p[i].vz * dt;
    }
}

/* ───────────────────────────────────────────────────────────────── */
/* SoA: gravity update — SIMD-friendly, compiler can auto-vectorize */
static void gravity_step_soa(particles_soa_t *p, float dt) {
    size_t n = p->count;
    
    /* First pass: accumulate forces (inner loop over contiguous arrays) */
    float *__restrict__ vx = p->vx;
    float *__restrict__ vy = p->vy;
    float *__restrict__ vz = p->vz;
    const float *__restrict__ x  = p->x;
    const float *__restrict__ y  = p->y;
    const float *__restrict__ z  = p->z;
    const float *__restrict__ m  = p->mass;

    for (size_t i = 0; i < n; i++) {
        float fx = 0.0f, fy = 0.0f, fz = 0.0f;
        float xi = x[i], yi = y[i], zi = z[i];

        /* Inner loop: all j accesses are sequential — auto-vectorizable */
        for (size_t j = 0; j < n; j++) {
            float dx = x[j] - xi;
            float dy = y[j] - yi;
            float dz = z[j] - zi;
            float dist_sq = dx*dx + dy*dy + dz*dz + SOFTENING;
            float inv_dist3 = 1.0f / (dist_sq * sqrtf(dist_sq));
            fx += dx * m[j] * inv_dist3;
            fy += dy * m[j] * inv_dist3;
            fz += dz * m[j] * inv_dist3;
        }
        vx[i] += fx * dt;
        vy[i] += fy * dt;
        vz[i] += fz * dt;
    }
    
    /* Position update: fully sequential, optimal cache behavior */
    for (size_t i = 0; i < n; i++) {
        p->x[i] += vx[i] * dt;
        p->y[i] += vy[i] * dt;
        p->z[i] += vz[i] * dt;
    }
}

/* ───────────────────────────────────────────────────────────────── */
int main(void) {
    const size_t n = 1000;  /* Small for O(n^2) demo */

    /* Allocate AoS */
    particle_aos_t *aos = aligned_alloc_safe(64, n * sizeof(particle_aos_t));
    
    /* Allocate SoA — each array cache-line aligned */
    particles_soa_t soa = {
        .x    = aligned_alloc_safe(64, n * sizeof(float)),
        .y    = aligned_alloc_safe(64, n * sizeof(float)),
        .z    = aligned_alloc_safe(64, n * sizeof(float)),
        .vx   = aligned_alloc_safe(64, n * sizeof(float)),
        .vy   = aligned_alloc_safe(64, n * sizeof(float)),
        .vz   = aligned_alloc_safe(64, n * sizeof(float)),
        .mass = aligned_alloc_safe(64, n * sizeof(float)),
        .count = n,
    };

    if (!aos || !soa.x || !soa.y || !soa.z || !soa.vx || !soa.vy || !soa.vz || !soa.mass) {
        fprintf(stderr, "Allocation failed\n");
        return 1;
    }

    /* Initialize both layouts with same data */
    srand(42);
    for (size_t i = 0; i < n; i++) {
        float x = (float)rand() / RAND_MAX;
        float y = (float)rand() / RAND_MAX;
        float z = (float)rand() / RAND_MAX;
        float m = 1.0f + (float)rand() / RAND_MAX;

        aos[i] = (particle_aos_t){ x, y, z, 0, 0, 0, m, 0 };
        soa.x[i] = x; soa.y[i] = y; soa.z[i] = z;
        soa.vx[i] = soa.vy[i] = soa.vz[i] = 0.0f;
        soa.mass[i] = m;
    }

    /* Benchmark AoS */
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    gravity_step_aos(aos, n, 0.01f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double aos_ms = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    /* Benchmark SoA */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    gravity_step_soa(&soa, 0.01f);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double soa_ms = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    printf("AoS gravity step: %.3f ms\n", aos_ms);
    printf("SoA gravity step: %.3f ms\n", soa_ms);
    printf("Speedup: %.2fx\n", aos_ms / soa_ms);

    /* Cleanup */
    free(aos);
    free(soa.x); free(soa.y); free(soa.z);
    free(soa.vx); free(soa.vy); free(soa.vz);
    free(soa.mass);
    return 0;
}
/*
 * Compile: gcc -O3 -march=native -ffast-math -o nbody nbody.c -lm
 * With -O3 -march=native, the SoA inner loop will be auto-vectorized with AVX2
 */
```

**Go — AoS vs SoA with benchmark:**
```go
package main

import (
	"fmt"
	"math"
	"time"
)

const (
	NumParticles = 10000
	Softening    = 1e-9
)

// ── AoS Layout ───────────────────────────────────────────────────────
type ParticleAoS struct {
	X, Y, Z       float32
	VX, VY, VZ    float32
	Mass          float32
	_pad          float32 // alignment padding
}

// ── SoA Layout ───────────────────────────────────────────────────────
type ParticlesSoA struct {
	X, Y, Z    []float32
	VX, VY, VZ []float32
	Mass       []float32
}

func newSoA(n int) *ParticlesSoA {
	return &ParticlesSoA{
		X:    make([]float32, n),
		Y:    make([]float32, n),
		Z:    make([]float32, n),
		VX:   make([]float32, n),
		VY:   make([]float32, n),
		VZ:   make([]float32, n),
		Mass: make([]float32, n),
	}
}

// gravityStepAoS: N-body force computation with AoS layout
// Cache behavior: inner loop accesses p[j].x, p[j].y, p[j].z, p[j].mass
// — all within same struct, good per-element access.
// But loading p[j] brings VX/VY/VZ too (wasted bandwidth).
func gravityStepAoS(p []ParticleAoS, dt float32) {
	n := len(p)
	for i := 0; i < n; i++ {
		var fx, fy, fz float32
		xi, yi, zi := p[i].X, p[i].Y, p[i].Z
		for j := 0; j < n; j++ {
			dx := p[j].X - xi
			dy := p[j].Y - yi
			dz := p[j].Z - zi
			distSq := dx*dx + dy*dy + dz*dz + Softening
			invDist3 := float32(1.0 / (distSq * math.Sqrt(float64(distSq))))
			mj := p[j].Mass
			fx += dx * mj * invDist3
			fy += dy * mj * invDist3
			fz += dz * mj * invDist3
		}
		p[i].VX += fx * dt
		p[i].VY += fy * dt
		p[i].VZ += fz * dt
	}
	for i := 0; i < n; i++ {
		p[i].X += p[i].VX * dt
		p[i].Y += p[i].VY * dt
		p[i].Z += p[i].VZ * dt
	}
}

// gravityStepSoA: same computation but SoA layout
// Inner loop: x[j], y[j], z[j], mass[j] — all separate arrays.
// Cache behavior: hardware prefetcher handles sequential arrays well.
// Go's escape analysis keeps slices on heap, but access pattern is optimal.
func gravityStepSoA(p *ParticlesSoA, dt float32) {
	n := len(p.X)
	x, y, z := p.X, p.Y, p.Z
	vx, vy, vz := p.VX, p.VY, p.VZ
	mass := p.Mass

	for i := 0; i < n; i++ {
		var fx, fy, fz float32
		xi, yi, zi := x[i], y[i], z[i]
		for j := 0; j < n; j++ {
			dx := x[j] - xi
			dy := y[j] - yi
			dz := z[j] - zi
			distSq := dx*dx + dy*dy + dz*dz + Softening
			invDist3 := float32(1.0 / (distSq * math.Sqrt(float64(distSq))))
			mj := mass[j]
			fx += dx * mj * invDist3
			fy += dy * mj * invDist3
			fz += dz * mj * invDist3
		}
		vx[i] += fx * dt
		vy[i] += fy * dt
		vz[i] += fz * dt
	}
	for i := 0; i < n; i++ {
		x[i] += vx[i] * dt
		y[i] += vy[i] * dt
		z[i] += vz[i] * dt
	}
}

func benchmarkAoS(n int, iterations int) time.Duration {
	particles := make([]ParticleAoS, n)
	for i := range particles {
		particles[i] = ParticleAoS{
			X: float32(i) * 0.001, Y: float32(i) * 0.002, Z: float32(i) * 0.003,
			Mass: 1.0,
		}
	}
	// Warm up
	gravityStepAoS(particles, 0.01)

	start := time.Now()
	for it := 0; it < iterations; it++ {
		gravityStepAoS(particles, 0.01)
	}
	return time.Since(start)
}

func benchmarkSoA(n int, iterations int) time.Duration {
	p := newSoA(n)
	for i := range p.X {
		p.X[i] = float32(i) * 0.001
		p.Y[i] = float32(i) * 0.002
		p.Z[i] = float32(i) * 0.003
		p.Mass[i] = 1.0
	}
	// Warm up
	gravityStepSoA(p, 0.01)

	start := time.Now()
	for it := 0; it < iterations; it++ {
		gravityStepSoA(p, 0.01)
	}
	return time.Since(start)
}

func main() {
	const n = 1000
	const iterations = 10

	fmt.Printf("N-body simulation: %d particles, %d iterations\n\n", n, iterations)

	aosDur := benchmarkAoS(n, iterations)
	soaDur := benchmarkSoA(n, iterations)

	fmt.Printf("AoS layout: %v\n", aosDur)
	fmt.Printf("SoA layout: %v\n", soaDur)
	fmt.Printf("Speedup (SoA/AoS): %.2fx\n",
		float64(aosDur)/float64(soaDur))
}
```

**Rust — AoS vs SoA with idiomatic patterns:**
```rust
use std::time::Instant;

const SOFTENING: f32 = 1e-9;

// ── AoS Layout ───────────────────────────────────────────────────────
#[derive(Clone, Default)]
#[repr(C)]  // Predictable field ordering
struct ParticleAoS {
    x: f32, y: f32, z: f32,
    vx: f32, vy: f32, vz: f32,
    mass: f32,
    _pad: f32,  // Align to 32 bytes
}

// ── SoA Layout ───────────────────────────────────────────────────────
/// All positions/velocities stored in separate contiguous arrays.
/// This is the preferred layout for data-parallel computation.
struct ParticlesSoA {
    x: Vec<f32>,
    y: Vec<f32>,
    z: Vec<f32>,
    vx: Vec<f32>,
    vy: Vec<f32>,
    vz: Vec<f32>,
    mass: Vec<f32>,
}

impl ParticlesSoA {
    fn new(n: usize) -> Self {
        ParticlesSoA {
            x:    vec![0.0; n],
            y:    vec![0.0; n],
            z:    vec![0.0; n],
            vx:   vec![0.0; n],
            vy:   vec![0.0; n],
            vz:   vec![0.0; n],
            mass: vec![1.0; n],
        }
    }
    
    fn len(&self) -> usize { self.x.len() }
}

// ── AoS gravity step ────────────────────────────────────────────────
fn gravity_step_aos(particles: &mut [ParticleAoS], dt: f32) {
    let n = particles.len();
    let mut forces = vec![(0.0f32, 0.0f32, 0.0f32); n];
    
    // Compute forces: reads scattered across AoS struct fields
    for i in 0..n {
        let (xi, yi, zi) = (particles[i].x, particles[i].y, particles[i].z);
        let mut fx = 0.0f32;
        let mut fy = 0.0f32;
        let mut fz = 0.0f32;
        
        for j in 0..n {
            let dx = particles[j].x - xi;
            let dy = particles[j].y - yi;
            let dz = particles[j].z - zi;
            let dist_sq = dx*dx + dy*dy + dz*dz + SOFTENING;
            let inv_dist3 = 1.0 / (dist_sq * dist_sq.sqrt());
            let mj = particles[j].mass;
            fx += dx * mj * inv_dist3;
            fy += dy * mj * inv_dist3;
            fz += dz * mj * inv_dist3;
        }
        forces[i] = (fx, fy, fz);
    }
    
    // Apply forces and integrate positions
    for i in 0..n {
        particles[i].vx += forces[i].0 * dt;
        particles[i].vy += forces[i].1 * dt;
        particles[i].vz += forces[i].2 * dt;
        particles[i].x += particles[i].vx * dt;
        particles[i].y += particles[i].vy * dt;
        particles[i].z += particles[i].vz * dt;
    }
}

// ── SoA gravity step ────────────────────────────────────────────────
/// LLVM can auto-vectorize the inner loop since all arrays are contiguous.
/// Mark slices as restrict-like with split borrows.
fn gravity_step_soa(p: &mut ParticlesSoA, dt: f32) {
    let n = p.len();
    let mut fx_buf = vec![0.0f32; n];
    let mut fy_buf = vec![0.0f32; n];
    let mut fz_buf = vec![0.0f32; n];
    
    // Borrow immutably for position/mass reads
    let x = p.x.as_slice();
    let y = p.y.as_slice();
    let z = p.z.as_slice();
    let mass = p.mass.as_slice();
    
    for i in 0..n {
        let (xi, yi, zi) = (x[i], y[i], z[i]);
        let mut fx = 0.0f32;
        let mut fy = 0.0f32;
        let mut fz = 0.0f32;
        
        // This inner loop iterates over contiguous arrays — LLVM vectorizes this
        for j in 0..n {
            let dx = x[j] - xi;
            let dy = y[j] - yi;
            let dz = z[j] - zi;
            let dist_sq = dx*dx + dy*dy + dz*dz + SOFTENING;
            let inv_dist3 = 1.0 / (dist_sq * dist_sq.sqrt());
            fx += dx * mass[j] * inv_dist3;
            fy += dy * mass[j] * inv_dist3;
            fz += dz * mass[j] * inv_dist3;
        }
        fx_buf[i] = fx;
        fy_buf[i] = fy;
        fz_buf[i] = fz;
    }
    
    // Apply: all sequential array writes
    for i in 0..n {
        p.vx[i] += fx_buf[i] * dt;
        p.vy[i] += fy_buf[i] * dt;
        p.vz[i] += fz_buf[i] * dt;
        p.x[i] += p.vx[i] * dt;
        p.y[i] += p.vy[i] * dt;
        p.z[i] += p.vz[i] * dt;
    }
}

fn main() {
    const N: usize = 500;
    const ITERATIONS: usize = 5;
    
    // AoS benchmark
    let mut aos: Vec<ParticleAoS> = (0..N).map(|i| ParticleAoS {
        x: i as f32 * 0.001,
        y: i as f32 * 0.002,
        z: i as f32 * 0.003,
        mass: 1.0,
        ..Default::default()
    }).collect();
    
    gravity_step_aos(&mut aos, 0.01); // warm up
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        gravity_step_aos(&mut aos, 0.01);
    }
    let aos_dur = start.elapsed();
    
    // SoA benchmark
    let mut soa = ParticlesSoA::new(N);
    for i in 0..N {
        soa.x[i] = i as f32 * 0.001;
        soa.y[i] = i as f32 * 0.002;
        soa.z[i] = i as f32 * 0.003;
    }
    
    gravity_step_soa(&mut soa, 0.01); // warm up
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        gravity_step_soa(&mut soa, 0.01);
    }
    let soa_dur = start.elapsed();
    
    println!("N={N}, iterations={ITERATIONS}");
    println!("AoS: {:?}", aos_dur);
    println!("SoA: {:?}", soa_dur);
    println!("Speedup: {:.2}x", aos_dur.as_secs_f64() / soa_dur.as_secs_f64());
}
// Build: RUSTFLAGS="-C target-cpu=native" cargo build --release
```

---

## 8. Cache-Friendly Algorithms

### 8.1 Matrix Multiplication — The Classic Cache Lesson

#### Naive (Cache-Oblivious Disaster):

```
for i in 0..N:
    for j in 0..N:
        for k in 0..N:
            C[i][j] += A[i][k] * B[k][j]   ← B is accessed column-wise!
```

Row-major storage: `B[k][j]` and `B[k+1][j]` are N elements apart (N×4 bytes). For N=1024, that's 4KB apart — stride = 1024 = L1 miss every access.

#### Transposed (Better, but wasteful):

Transpose B first, then multiply. Works, but costs O(N²) extra work.

#### Cache-Blocked (Tiled) Matrix Multiplication:

**The key insight**: Divide the matrix into blocks that fit in L1/L2 cache. Work on one block at a time.

**C — Production matrix multiply with blocking:**
```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/*
 * Cache blocking / tiling for matrix multiplication.
 *
 * Target: Tile A (BLOCK_M × BLOCK_K) and B (BLOCK_K × BLOCK_N) both fit in L1.
 * L1 size = 32KB. We need: BLOCK_M*BLOCK_K + BLOCK_K*BLOCK_N + BLOCK_M*BLOCK_N ≤ 32KB/4
 * With BLOCK = 64: 64*64*4 = 16KB per matrix portion — fits comfortably.
 */
#define BLOCK_SIZE 64

typedef float f32;

/* Naive matrix multiply: O(N^3) with poor cache behavior */
static void matmul_naive(const f32 *A, const f32 *B, f32 *C,
                          int M, int N, int K) {
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            f32 sum = 0.0f;
            for (int k = 0; k < K; k++) {
                sum += A[i*K + k] * B[k*N + j];  /* B: column-major access = bad */
            }
            C[i*N + j] = sum;
        }
    }
}

/* Blocked matrix multiply: tiles are cache-resident */
static void matmul_blocked(const f32 *A, const f32 *B, f32 *C,
                             int M, int N, int K) {
    /* Zero output */
    memset(C, 0, (size_t)M * N * sizeof(f32));
    
    for (int i = 0; i < M; i += BLOCK_SIZE) {
        for (int j = 0; j < N; j += BLOCK_SIZE) {
            for (int k = 0; k < K; k += BLOCK_SIZE) {
                /* Inner block: A[i..i+B, k..k+B] × B[k..k+B, j..j+B] → C[i..i+B, j..j+B] */
                int i_end = (i + BLOCK_SIZE < M) ? i + BLOCK_SIZE : M;
                int j_end = (j + BLOCK_SIZE < N) ? j + BLOCK_SIZE : N;
                int k_end = (k + BLOCK_SIZE < K) ? k + BLOCK_SIZE : K;
                
                for (int ii = i; ii < i_end; ii++) {
                    for (int kk = k; kk < k_end; kk++) {
                        /* A[ii][kk] is constant for inner j loop — pulled to register */
                        f32 a_val = A[ii*K + kk];
                        for (int jj = j; jj < j_end; jj++) {
                            /* B[kk][jj]: sequential access ✓ */
                            /* C[ii][jj]: sequential access ✓ */
                            C[ii*N + jj] += a_val * B[kk*N + jj];
                        }
                    }
                }
            }
        }
    }
}

static double elapsed_ms(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;
}

int main(void) {
    const int M = 512, N = 512, K = 512;
    
    f32 *A = aligned_alloc(64, M * K * sizeof(f32));
    f32 *B = aligned_alloc(64, K * N * sizeof(f32));
    f32 *C_naive   = aligned_alloc(64, M * N * sizeof(f32));
    f32 *C_blocked = aligned_alloc(64, M * N * sizeof(f32));
    
    if (!A || !B || !C_naive || !C_blocked) {
        perror("aligned_alloc");
        return 1;
    }

    /* Initialize with random-ish values */
    for (int i = 0; i < M * K; i++) A[i] = (f32)(i % 100) * 0.01f;
    for (int i = 0; i < K * N; i++) B[i] = (f32)(i % 100) * 0.01f;

    struct timespec t0, t1;
    
    clock_gettime(CLOCK_MONOTONIC, &t0);
    matmul_naive(A, B, C_naive, M, N, K);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("Naive:   %.2f ms\n", elapsed_ms(t0, t1));
    
    clock_gettime(CLOCK_MONOTONIC, &t0);
    matmul_blocked(A, B, C_blocked, M, N, K);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("Blocked: %.2f ms (block=%d)\n", elapsed_ms(t0, t1), BLOCK_SIZE);

    /* Verify correctness (compare first element) */
    printf("C[0][0]: naive=%.4f blocked=%.4f\n", C_naive[0], C_blocked[0]);

    free(A); free(B); free(C_naive); free(C_blocked);
    return 0;
}
```

**Rust — Cache-blocked matrix multiply:**
```rust
const BLOCK: usize = 64;

/// Matrix multiply with cache blocking.
/// A: M×K, B: K×N, C: M×N (row-major, C-style layout)
pub fn matmul_blocked(
    a: &[f32], b: &[f32], c: &mut [f32],
    m: usize, n: usize, k: usize,
) {
    assert_eq!(a.len(), m * k);
    assert_eq!(b.len(), k * n);
    assert_eq!(c.len(), m * n);
    
    // Initialize output to zero
    c.fill(0.0);
    
    // Tile loops: i, j, k blocking
    for i_start in (0..m).step_by(BLOCK) {
        let i_end = (i_start + BLOCK).min(m);
        
        for j_start in (0..n).step_by(BLOCK) {
            let j_end = (j_start + BLOCK).min(n);
            
            for k_start in (0..k).step_by(BLOCK) {
                let k_end = (k_start + BLOCK).min(k);
                
                // Inner microkernel: operates on block that fits in L1 cache
                for ii in i_start..i_end {
                    for kk in k_start..k_end {
                        // Hoist A[ii][kk] out of innermost loop
                        // This scalar lives in a register for the entire j loop
                        let a_val = a[ii * k + kk];
                        
                        // Innermost: sequential reads of b[kk][jj] and c[ii][jj]
                        // Both arrays accessed at stride=1 — maximal cache efficiency
                        let b_row = &b[kk * n + j_start..kk * n + j_end];
                        let c_row = &mut c[ii * n + j_start..ii * n + j_end];
                        
                        // Iterator-based: enables LLVM to auto-vectorize
                        c_row.iter_mut().zip(b_row.iter()).for_each(|(cv, &bv)| {
                            *cv += a_val * bv;
                        });
                    }
                }
            }
        }
    }
}

/// Naive: column-major access of B causes L1 thrashing
pub fn matmul_naive(
    a: &[f32], b: &[f32], c: &mut [f32],
    m: usize, n: usize, k: usize,
) {
    for i in 0..m {
        for j in 0..n {
            let mut sum = 0.0f32;
            for kk in 0..k {
                // b[kk * n + j]: stride = n elements between accesses
                // For n=512: stride = 2048 bytes >> cache line size
                sum += a[i * k + kk] * b[kk * n + j];
            }
            c[i * n + j] = sum;
        }
    }
}

fn main() {
    use std::time::Instant;
    
    let m = 512usize;
    let n = 512usize;
    let k = 512usize;
    
    let a: Vec<f32> = (0..m*k).map(|i| (i % 100) as f32 * 0.01).collect();
    let b: Vec<f32> = (0..k*n).map(|i| (i % 100) as f32 * 0.01).collect();
    let mut c_naive   = vec![0.0f32; m * n];
    let mut c_blocked = vec![0.0f32; m * n];
    
    // Warm up
    matmul_naive(&a, &b, &mut c_naive, m, n, k);
    
    let t = Instant::now();
    matmul_naive(&a, &b, &mut c_naive, m, n, k);
    let naive_dur = t.elapsed();
    
    let t = Instant::now();
    matmul_blocked(&a, &b, &mut c_blocked, m, n, k);
    let blocked_dur = t.elapsed();
    
    println!("Naive:   {:?}", naive_dur);
    println!("Blocked: {:?} (block={})", blocked_dur, BLOCK);
    println!("Speedup: {:.2}x", naive_dur.as_secs_f64() / blocked_dur.as_secs_f64());
    
    // Verify
    let max_err = c_naive.iter().zip(c_blocked.iter())
        .map(|(a, b)| (a - b).abs())
        .fold(0.0f32, f32::max);
    println!("Max error: {:.6}", max_err);
}
// RUSTFLAGS="-C target-cpu=native" cargo run --release
```

### 8.2 Binary Search vs Eytzinger Layout

Traditional binary search has poor cache behavior: accesses at indices n/2, n/4, 3n/4... — no spatial locality.

**Eytzinger layout** reorganizes the array so a BFS-order traversal of the search tree is stored sequentially. The first few levels of the tree fit in L1, next levels in L2, etc.

**Rust — Eytzinger layout:**
```rust
/// Eytzinger layout: reorganize sorted array for cache-optimal binary search.
/// Array stored BFS-order: root at index 1, left child at 2i, right at 2i+1.
pub struct EytzingerArray {
    data: Vec<i32>,
    original_size: usize,
}

impl EytzingerArray {
    /// Build Eytzinger layout from sorted slice.
    pub fn from_sorted(sorted: &[i32]) -> Self {
        let n = sorted.len();
        let mut data = vec![0i32; n + 1]; // 1-indexed
        
        Self::build(sorted, &mut data, 0, 1);
        
        EytzingerArray { data, original_size: n }
    }
    
    fn build(sorted: &[i32], layout: &mut Vec<i32>, sorted_idx: usize, node: usize) -> usize {
        let n = sorted.len();
        if node > n {
            return sorted_idx;
        }
        // Left subtree
        let idx = Self::build(sorted, layout, sorted_idx, 2 * node);
        // Place current node
        layout[node] = sorted[idx];
        // Right subtree
        Self::build(sorted, layout, idx + 1, 2 * node + 1)
    }
    
    /// Search: much more cache-friendly than traditional binary search.
    /// First ~4 comparisons touch only cache line 1 (indices 1..15).
    pub fn search(&self, target: i32) -> bool {
        let mut idx = 1usize;
        while idx <= self.original_size {
            // Branch-free comparison: avoids branch mispredictions
            idx = if self.data[idx] < target {
                2 * idx + 1  // right child
            } else {
                2 * idx      // left child
            };
        }
        // Retrieve comparison result from the final position
        // idx >> trailing_zeros gives the index where we stopped
        let result_idx = idx >> idx.trailing_zeros();
        result_idx <= self.original_size && self.data[result_idx] == target
    }
    
    /// Standard binary search for comparison
    pub fn binary_search_standard(sorted: &[i32], target: i32) -> bool {
        sorted.binary_search(&target).is_ok()
    }
}

fn main() {
    use std::time::Instant;
    
    let n = 1 << 20; // 1M elements
    let sorted: Vec<i32> = (0..n as i32 * 2).step_by(2).collect(); // even numbers
    
    let eytzinger = EytzingerArray::from_sorted(&sorted);
    
    let queries: Vec<i32> = (0..100_000).map(|i| i * 3).collect(); // mix hits/misses
    
    // Benchmark standard binary search
    let t = Instant::now();
    let mut found_std = 0usize;
    for &q in &queries {
        if EytzingerArray::binary_search_standard(&sorted, q) {
            found_std += 1;
        }
    }
    let std_dur = t.elapsed();
    
    // Benchmark Eytzinger
    let t = Instant::now();
    let mut found_eyt = 0usize;
    for &q in &queries {
        if eytzinger.search(q) {
            found_eyt += 1;
        }
    }
    let eyt_dur = t.elapsed();
    
    println!("Standard binary search: {:?} (found {})", std_dur, found_std);
    println!("Eytzinger layout:       {:?} (found {})", eyt_dur, found_eyt);
    println!("Speedup: {:.2}x", std_dur.as_secs_f64() / eyt_dur.as_secs_f64());
    assert_eq!(found_std, found_eyt, "Results must match!");
}
```

---

## 9. False Sharing — The Silent Killer in Parallel Code

### What is False Sharing?

**False sharing** occurs when two threads on different CPU cores modify different variables that happen to **share the same cache line**.

Even though the threads are accessing *logically independent data*, the hardware cache coherence protocol (MESI) treats the entire cache line as a shared unit. When Core 0 writes to byte 0 and Core 1 writes to byte 8 of the same 64-byte cache line:

1. Core 1 writes → cache line marked "Modified" in Core 1's cache
2. Core 0 needs to write → must invalidate Core 1's copy first
3. Core 1's cache line evicted to LLC or RAM
4. Core 0 fetches the line, writes, marks "Modified"
5. Core 1 needs to write → must invalidate Core 0's copy...

This **ping-pong** of cache lines between cores destroys parallel performance. Two cores appear to be contending over a lock that doesn't exist in your code.

```
Without false sharing:
Core 0: Write counter_a ... Write counter_a ... (stays in L1)
Core 1: Write counter_b ... Write counter_b ... (stays in L1)

With false sharing (same cache line):
Core 0: Write counter_a → Core 1 invalidated → Core 0 re-fetches
Core 1: Write counter_b → Core 0 invalidated → Core 1 re-fetches
→ Both cores spending most time waiting for cache coherence traffic!
```

### C — Demonstrating and fixing false sharing:

```c
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define NUM_THREADS  4
#define ITERATIONS   100000000LL
#define CACHE_LINE   64

/* ─── BAD: All counters packed into one cache line ─────────────── */
typedef struct {
    volatile int64_t counters[NUM_THREADS];
    /* 4 × 8 bytes = 32 bytes — fits in one cache line */
} bad_counters_t;

/* ─── GOOD: Each counter padded to its own cache line ─────────── */
typedef struct {
    volatile int64_t value;
    char _pad[CACHE_LINE - sizeof(int64_t)];  /* 56 bytes padding */
} __attribute__((aligned(CACHE_LINE))) padded_counter_t;

typedef struct {
    padded_counter_t counters[NUM_THREADS];
} good_counters_t;

/* Thread argument */
typedef struct {
    void     *counters;  /* pointer to either bad or good counters */
    int       thread_id;
    int       is_good;
} thread_arg_t;

static void *increment_bad(void *arg) {
    thread_arg_t *ta = (thread_arg_t *)arg;
    bad_counters_t *bc = (bad_counters_t *)ta->counters;
    int id = ta->thread_id;
    for (int64_t i = 0; i < ITERATIONS; i++) {
        bc->counters[id]++;  /* False sharing: all in same cache line */
    }
    return NULL;
}

static void *increment_good(void *arg) {
    thread_arg_t *ta = (thread_arg_t *)arg;
    good_counters_t *gc = (good_counters_t *)ta->counters;
    int id = ta->thread_id;
    for (int64_t i = 0; i < ITERATIONS; i++) {
        gc->counters[id].value++;  /* Each thread owns its cache line */
    }
    return NULL;
}

static double run_benchmark(int is_good) {
    pthread_t threads[NUM_THREADS];
    thread_arg_t args[NUM_THREADS];
    
    bad_counters_t  *bc = NULL;
    good_counters_t *gc = NULL;
    
    if (is_good) {
        gc = aligned_alloc(CACHE_LINE, sizeof(good_counters_t));
        if (!gc) { perror("aligned_alloc"); exit(1); }
        for (int i = 0; i < NUM_THREADS; i++) gc->counters[i].value = 0;
    } else {
        bc = aligned_alloc(CACHE_LINE, sizeof(bad_counters_t));
        if (!bc) { perror("aligned_alloc"); exit(1); }
        for (int i = 0; i < NUM_THREADS; i++) bc->counters[i] = 0;
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].counters  = is_good ? (void *)gc : (void *)bc;
        args[i].thread_id = i;
        args[i].is_good   = is_good;
        pthread_create(&threads[i], NULL,
                       is_good ? increment_good : increment_bad, &args[i]);
    }
    
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < NUM_THREADS; i++) pthread_join(threads[i], NULL);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    
    double ms = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;
    
    if (is_good) free(gc); else free(bc);
    return ms;
}

int main(void) {
    printf("False sharing benchmark: %d threads × %lld iterations\n\n",
           NUM_THREADS, ITERATIONS);
    
    double bad_ms  = run_benchmark(0);
    double good_ms = run_benchmark(1);
    
    printf("With false sharing (bad):     %.0f ms\n", bad_ms);
    printf("Without false sharing (good): %.0f ms\n", good_ms);
    printf("Speedup: %.2fx\n", bad_ms / good_ms);
    printf("\nNote: bad/good ratio shows cache coherence overhead\n");
    return 0;
}
/* Compile: gcc -O2 -pthread -o false_sharing false_sharing.c */
```

**Go — False sharing with goroutines:**
```go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
	"unsafe"
)

const (
	NumGoroutines = 4
	Iterations    = 50_000_000
	CacheLineSize = 64
)

// ─── BAD: All counters in contiguous memory ──────────────────────────
type BadCounters struct {
	vals [NumGoroutines]int64
}

// ─── GOOD: Each counter padded to its own cache line ─────────────────
type PaddedInt64 struct {
	val  int64
	_pad [CacheLineSize - unsafe.Sizeof(int64(0))]byte
}

type GoodCounters struct {
	vals [NumGoroutines]PaddedInt64
}

func benchmarkCounters(usePadding bool) time.Duration {
	var wg sync.WaitGroup
	wg.Add(NumGoroutines)

	bad  := &BadCounters{}
	good := &GoodCounters{}

	runtime.GC() // flush GC pressure before benchmark
	start := time.Now()

	for g := 0; g < NumGoroutines; g++ {
		g := g // capture loop variable
		go func() {
			defer wg.Done()
			if usePadding {
				for i := 0; i < Iterations; i++ {
					good.vals[g].val++ // each goroutine owns its cache line
				}
			} else {
				for i := 0; i < Iterations; i++ {
					bad.vals[g]++ // all goroutines share cache lines
				}
			}
		}()
	}

	wg.Wait()
	return time.Since(start)
}

func main() {
	runtime.GOMAXPROCS(NumGoroutines)
	fmt.Printf("Goroutines: %d, Iterations: %d\n\n", NumGoroutines, Iterations)

	// Run multiple times and take minimum (best-case = most cache-coherent)
	const runs = 3
	var badMin, goodMin time.Duration = 1<<62, 1<<62

	for i := 0; i < runs; i++ {
		if d := benchmarkCounters(false); d < badMin { badMin = d }
		if d := benchmarkCounters(true);  d < goodMin { goodMin = d }
	}

	fmt.Printf("With false sharing:    %v\n", badMin)
	fmt.Printf("Without false sharing: %v\n", goodMin)
	fmt.Printf("Speedup: %.2fx\n", float64(badMin)/float64(goodMin))
}
```

**Rust — False sharing with atomic operations:**
```rust
use std::sync::{Arc, atomic::{AtomicI64, Ordering}};
use std::thread;
use std::time::Instant;

const NUM_THREADS: usize = 4;
const ITERATIONS: i64 = 50_000_000;
const CACHE_LINE: usize = 64;

// ─── BAD: Atomic counters packed tightly ─────────────────────────────
struct BadCounters {
    vals: [AtomicI64; NUM_THREADS],
}

impl BadCounters {
    fn new() -> Self {
        BadCounters {
            vals: [
                AtomicI64::new(0), AtomicI64::new(0),
                AtomicI64::new(0), AtomicI64::new(0),
            ],
        }
    }
}

// ─── GOOD: Each counter padded to one cache line ──────────────────────
#[repr(C, align(64))]
struct PaddedAtomic {
    val: AtomicI64,
    _pad: [u8; CACHE_LINE - std::mem::size_of::<AtomicI64>()],
}

impl PaddedAtomic {
    const fn new() -> Self {
        PaddedAtomic {
            val: AtomicI64::new(0),
            _pad: [0u8; CACHE_LINE - std::mem::size_of::<AtomicI64>()],
        }
    }
}

// Array of padded atomics — each on its own cache line
struct GoodCounters {
    vals: [PaddedAtomic; NUM_THREADS],
}

impl GoodCounters {
    fn new() -> Self {
        GoodCounters {
            vals: [
                PaddedAtomic::new(), PaddedAtomic::new(),
                PaddedAtomic::new(), PaddedAtomic::new(),
            ],
        }
    }
}

fn bench_bad() -> std::time::Duration {
    let counters = Arc::new(BadCounters::new());
    let mut handles = Vec::with_capacity(NUM_THREADS);
    
    let start = Instant::now();
    for t in 0..NUM_THREADS {
        let c = Arc::clone(&counters);
        handles.push(thread::spawn(move || {
            for _ in 0..ITERATIONS {
                // Relaxed: no ordering guarantee needed for benchmark
                c.vals[t].fetch_add(1, Ordering::Relaxed);
            }
        }));
    }
    for h in handles { h.join().unwrap(); }
    start.elapsed()
}

fn bench_good() -> std::time::Duration {
    let counters = Arc::new(GoodCounters::new());
    let mut handles = Vec::with_capacity(NUM_THREADS);
    
    let start = Instant::now();
    for t in 0..NUM_THREADS {
        let c = Arc::clone(&counters);
        handles.push(thread::spawn(move || {
            for _ in 0..ITERATIONS {
                c.vals[t].val.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }
    for h in handles { h.join().unwrap(); }
    start.elapsed()
}

fn main() {
    println!("False sharing benchmark: {} threads × {} iterations", NUM_THREADS, ITERATIONS);
    println!("AtomicI64 size: {} bytes", std::mem::size_of::<AtomicI64>());
    println!("PaddedAtomic size: {} bytes\n", std::mem::size_of::<PaddedAtomic>());
    
    // Warm up
    let _ = bench_bad();
    let _ = bench_good();
    
    let bad_dur  = bench_bad();
    let good_dur = bench_good();
    
    println!("With false sharing:    {:?}", bad_dur);
    println!("Without false sharing: {:?}", good_dur);
    println!("Speedup: {:.2}x", bad_dur.as_secs_f64() / good_dur.as_secs_f64());
}
```

---

## 10. Prefetching

### What is Prefetching?

Prefetching is the act of **loading data into cache before it is needed**, hiding the latency of the cache miss. If a memory access takes 200 cycles and the CPU is working on the current data for 300 cycles, perfect prefetching makes the memory latency zero from the programmer's perspective.

### Two Types of Prefetching:

**Hardware Prefetcher**: The CPU automatically detects stride patterns and prefetches ahead. It handles:
- Sequential accesses (stride=1): always prefetched
- Constant strides: often detected
- Indirect access patterns (pointer chasing): usually NOT detected

**Software Prefetcher**: You explicitly issue a prefetch hint, telling the CPU to load data now while you work on other data.

### Prefetch Intrinsics

```c
/* GCC/Clang */
__builtin_prefetch(addr, rw, locality);
/* rw: 0=read, 1=write */
/* locality: 0=no cache retention, 1=L3, 2=L2, 3=L1 (highest) */

/* x86 SSE */
#include <xmmintrin.h>
_mm_prefetch(addr, _MM_HINT_T0); /* L1  */
_mm_prefetch(addr, _MM_HINT_T1); /* L2  */
_mm_prefetch(addr, _MM_HINT_T2); /* L3  */
_mm_prefetch(addr, _MM_HINT_NTA);/* Non-temporal: bypass cache */
```

### When Hardware Prefetcher Fails — Linked List Traversal:

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define LIST_SIZE 1000000
#define PREFETCH_DISTANCE 10  /* How many nodes ahead to prefetch */

typedef struct node {
    int64_t      value;
    struct node *next;
    char         _pad[48]; /* Pad to 64 bytes = one cache line */
} node_t;

/* Each node is 64 bytes — accessing next = pointer chase to unknown address.
   Hardware prefetcher cannot predict where next will be. */
static int64_t traverse_no_prefetch(node_t *head) {
    int64_t sum = 0;
    node_t *cur = head;
    while (cur) {
        sum += cur->value;
        cur = cur->next;  /* Hardware prefetcher: "where is this?!" */
    }
    return sum;
}

/* Software prefetch: issue prefetch D nodes ahead while processing current.
   This pipeline-overlaps memory latency with computation. */
static int64_t traverse_with_prefetch(node_t *head) {
    int64_t sum = 0;
    node_t *cur = head;
    node_t *prefetch_target = head;
    
    /* Advance the prefetch pointer PREFETCH_DISTANCE nodes ahead */
    for (int i = 0; i < PREFETCH_DISTANCE && prefetch_target; i++) {
        prefetch_target = prefetch_target->next;
    }
    
    while (cur) {
        /* Issue prefetch for a node that is PREFETCH_DISTANCE ahead */
        if (prefetch_target) {
            __builtin_prefetch(prefetch_target, 0, 1);  /* L2 prefetch */
            prefetch_target = prefetch_target->next;
        }
        sum += cur->value;
        cur = cur->next;
    }
    return sum;
}

int main(void) {
    /* Allocate nodes */
    node_t *nodes = calloc(LIST_SIZE, sizeof(node_t));
    if (!nodes) { perror("calloc"); return 1; }
    
    /* Build linked list in non-sequential order to defeat hardware prefetcher */
    /* Create a shuffled permutation */
    int *perm = malloc(LIST_SIZE * sizeof(int));
    for (int i = 0; i < LIST_SIZE; i++) perm[i] = i;
    /* Fisher-Yates shuffle */
    srand(12345);
    for (int i = LIST_SIZE - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int tmp = perm[i]; perm[i] = perm[j]; perm[j] = tmp;
    }
    
    for (int i = 0; i < LIST_SIZE; i++) {
        nodes[perm[i]].value = perm[i];
        nodes[perm[i]].next  = (i + 1 < LIST_SIZE) ? &nodes[perm[i+1]] : NULL;
    }
    node_t *head = &nodes[perm[0]];
    free(perm);
    
    struct timespec t0, t1;
    
    /* Warm up */
    volatile int64_t r = traverse_no_prefetch(head);
    
    clock_gettime(CLOCK_MONOTONIC, &t0);
    r = traverse_no_prefetch(head);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double no_pf_ms = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;
    
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int64_t r2 = traverse_with_prefetch(head);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double with_pf_ms = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;
    
    printf("No prefetch:   %.2f ms (sum=%ld)\n", no_pf_ms, r);
    printf("With prefetch: %.2f ms (sum=%ld)\n", with_pf_ms, r2);
    printf("Speedup: %.2fx\n", no_pf_ms / with_pf_ms);
    
    free(nodes);
    return 0;
}
```

**Go — Prefetch using runtime.prefetch:**
```go
package main

import (
	"fmt"
	"math/rand"
	"time"
	"unsafe"
)

// Note: Go does not expose hardware prefetch intrinsics in the public API.
// The internal runtime uses runtime.prefetch* but these are unexported.
// The idiomatic Go approach is to:
// 1. Use sequential data structures (slice vs linked list)
// 2. Restructure algorithms for spatial locality
// 3. For performance-critical code: use CGo or assembly

// This demonstrates the algorithmic equivalent: converting pointer-chasing
// to sequential array access (the "flattening" pattern).

const ListSize = 500_000

type ListNode struct {
	Value int64
	Next  *ListNode
}

// SliceNode: flattened representation — no pointer chasing
type SliceList struct {
	Values []int64
	Nexts  []int32 // index into Values slice
}

// Build a randomly ordered linked list
func buildLinkedList(n int) *ListNode {
	nodes := make([]ListNode, n)
	perm  := rand.Perm(n)
	
	for i := 0; i < n; i++ {
		nodes[perm[i]].Value = int64(perm[i])
		if i+1 < n {
			nodes[perm[i]].Next = &nodes[perm[i+1]]
		}
	}
	return &nodes[perm[0]]
}

// Traverse linked list: poor cache behavior due to random pointer chasing
func traverseLinkedList(head *ListNode) int64 {
	var sum int64
	for cur := head; cur != nil; cur = cur.Next {
		sum += cur.Value
	}
	return sum
}

// Convert linked list to slice (preprocessing for cache-friendly access)
func toSlice(head *ListNode, n int) []int64 {
	result := make([]int64, 0, n)
	for cur := head; cur != nil; cur = cur.Next {
		result = append(result, cur.Value)
	}
	return result
}

// Traverse slice: sequential, hardware prefetcher handles it perfectly
func traverseSlice(vals []int64) int64 {
	var sum int64
	for _, v := range vals {
		sum += v
	}
	return sum
}

func main() {
	_ = unsafe.Sizeof(0) // suppress unused import
	
	fmt.Printf("Building list of %d nodes...\n", ListSize)
	head := buildLinkedList(ListSize)
	
	// Warm up
	_ = traverseLinkedList(head)
	
	// Benchmark linked list traversal
	const iters = 10
	start := time.Now()
	var result int64
	for i := 0; i < iters; i++ {
		result += traverseLinkedList(head)
	}
	listDur := time.Since(start)
	
	// Convert to slice
	slice := toSlice(head, ListSize)
	
	// Benchmark slice traversal
	start = time.Now()
	var result2 int64
	for i := 0; i < iters; i++ {
		result2 += traverseSlice(slice)
	}
	sliceDur := time.Since(start)
	
	fmt.Printf("Linked list traversal: %v (sum=%d)\n", listDur, result)
	fmt.Printf("Slice traversal:       %v (sum=%d)\n", sliceDur, result2)
	fmt.Printf("Speedup: %.2fx\n", float64(listDur)/float64(sliceDur))
	fmt.Println("\nLesson: Eliminating pointer chasing is the most powerful 'prefetch'")
}
```

---

## 11. NUMA Architecture

### What is NUMA?

**NUMA** stands for **Non-Uniform Memory Access**. In systems with multiple physical CPU sockets (servers, workstations), each socket has its own local RAM. Accessing remote RAM (on another socket) is significantly slower than accessing local RAM.

```
NUMA System (2-socket server):
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│  Socket 0 (Node 0)              │    │  Socket 1 (Node 1)              │
│  Cores: 0-31                    │◄──►│  Cores: 32-63                   │
│  L1/L2/L3 Cache                 │    │  L1/L2/L3 Cache                 │
│  Local RAM: 128 GB              │    │  Local RAM: 128 GB              │
│  Latency: ~70 ns                │    │  Latency: ~70 ns                │
└─────────────────────────────────┘    └─────────────────────────────────┘
          │                                          │
          └──────────── QPI/UPI Link ───────────────┘
                    Remote access: ~140 ns (2× slower)
```

### Linux NUMA Tools:

```bash
# Check NUMA topology
numactl --hardware

# Run process on specific NUMA node
numactl --cpunodebind=0 --membind=0 ./myprogram

# Check NUMA statistics
cat /proc/vmstat | grep numa
numastat

# NUMA-aware allocation in code
# Link with -lnuma

# Check current NUMA memory policy
cat /proc/self/numa_maps
```

### C — NUMA-aware memory allocation:

```c
#include <numa.h>
#include <numaif.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 
 * NUMA-aware allocation: allocate memory on a specific NUMA node.
 * This ensures memory is physically close to the cores that will access it.
 * Link with: -lnuma
 */

#define BUFFER_SIZE (256 * 1024 * 1024)  /* 256 MB */

static void *numa_alloc_on_node(size_t size, int node) {
    if (numa_available() < 0) {
        fprintf(stderr, "NUMA not available, using malloc\n");
        return malloc(size);
    }
    return numa_alloc_onnode(size, node);
}

static void demonstrate_numa(void) {
    if (numa_available() < 0) {
        printf("NUMA not available on this system\n");
        return;
    }
    
    int num_nodes = numa_num_configured_nodes();
    int num_cpus  = numa_num_configured_cpus();
    
    printf("NUMA nodes: %d, CPUs: %d\n", num_nodes, num_cpus);
    
    for (int node = 0; node < num_nodes; node++) {
        long long free_mem, total_mem;
        total_mem = numa_node_size64(node, &free_mem);
        printf("Node %d: total=%lld MB, free=%lld MB\n",
               node, total_mem >> 20, free_mem >> 20);
    }
    
    /* Allocate on node 0 */
    void *local_buf = numa_alloc_on_node(BUFFER_SIZE, 0);
    if (!local_buf) {
        perror("numa_alloc_onnode");
        return;
    }
    
    /* Touch pages to ensure physical allocation on node 0 */
    memset(local_buf, 0, BUFFER_SIZE);
    
    /* Check which node memory actually landed on */
    int status[1];
    void *pages[1] = { local_buf };
    move_pages(0, 1, pages, NULL, status, 0);
    printf("Buffer allocated on NUMA node: %d\n", status[0]);
    
    numa_free(local_buf, BUFFER_SIZE);
}

int main(void) {
    demonstrate_numa();
    return 0;
}
/* Compile: gcc -O2 -o numa_demo numa_demo.c -lnuma */
```

**Go — NUMA-awareness:**
```go
package main

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
)

// Go's runtime is NUMA-aware since Go 1.x:
// - The GC respects NUMA topology for allocation
// - GOMAXPROCS controls goroutine parallelism
// - Use numactl at the OS level for socket pinning

// Check NUMA topology via /sys filesystem
func getNUMAInfo() {
	entries, err := os.ReadDir("/sys/devices/system/node")
	if err != nil {
		fmt.Println("NUMA info not available:", err)
		return
	}

	fmt.Printf("NUMA nodes detected:\n")
	for _, entry := range entries {
		if !strings.HasPrefix(entry.Name(), "node") {
			continue
		}
		nodeID := entry.Name()[4:] // strip "node" prefix
		
		// Read memory size
		memFile := "/sys/devices/system/node/" + entry.Name() + "/meminfo"
		data, err := os.ReadFile(memFile)
		if err == nil {
			lines := strings.Split(string(data), "\n")
			for _, line := range lines {
				if strings.Contains(line, "MemTotal") {
					fmt.Printf("  Node %s: %s\n", nodeID, strings.TrimSpace(line))
					break
				}
			}
		}
		
		// Read CPU list
		cpuFile := "/sys/devices/system/node/" + entry.Name() + "/cpulist"
		cpuData, err := os.ReadFile(cpuFile)
		if err == nil {
			fmt.Printf("  Node %s CPUs: %s\n", nodeID, strings.TrimSpace(string(cpuData)))
		}
	}
}

// Get current process's NUMA node
func getCurrentNUMANode() int {
	// Read from /proc/self/status or use numastat
	data, err := os.ReadFile("/proc/self/status")
	if err != nil {
		return -1
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "Cpus_allowed:") {
			// Parse the CPU mask
			_ = line
		}
	}
	return 0 // simplified
}

// numactl wraps a command to run on a specific NUMA node
func runOnNUMANode(node int, program string, args ...string) error {
	numaArgs := []string{
		fmt.Sprintf("--cpunodebind=%d", node),
		fmt.Sprintf("--membind=%d", node),
		program,
	}
	numaArgs = append(numaArgs, args...)
	cmd := exec.Command("numactl", numaArgs...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func main() {
	fmt.Printf("Go version: %s\n", runtime.Version())
	fmt.Printf("GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))
	fmt.Printf("NumCPU: %d\n", runtime.NumCPU())
	fmt.Println()
	
	getNUMAInfo()
	
	fmt.Println("\nNUMA best practices in Go:")
	fmt.Println("1. Use 'numactl --cpunodebind=N --membind=N ./binary' at launch")
	fmt.Println("2. Set GOMAXPROCS to number of cores on one socket for NUMA locality")
	fmt.Println("3. Avoid cross-socket channel communication in hot paths")
	fmt.Println("4. Profile with 'numastat' and 'perf stat -e numa:*'")
	
	// Example: restrict to node 0's core count
	nodeStr := os.Getenv("NUMA_NODE")
	if nodeStr != "" {
		node, _ := strconv.Atoi(nodeStr)
		fmt.Printf("\nRunning with NUMA_NODE=%d\n", node)
		// In real code: use numactl at process start
	}
}
```

---

## 12. TLB — Translation Lookaside Buffer

### What is Virtual Memory and TLB?

Modern operating systems use **virtual memory**: each process sees its own address space (0 to 2^48 on x86-64). The CPU's **MMU** (Memory Management Unit) translates virtual addresses to physical addresses using **page tables** stored in RAM.

**The problem**: Every memory access requires a page table walk (multiple RAM accesses) just to translate the address. This would make memory access 4× slower.

**The TLB** (Translation Lookaside Buffer) is a small, fully associative cache that stores recent virtual→physical translations. A TLB hit costs ~1 cycle; a TLB miss costs ~20–100 cycles (page walk).

```
Virtual Address → TLB Lookup → (hit) → Physical Address → Cache Lookup
                            → (miss) → Page Table Walk → Physical Address
                                        (4 RAM accesses on x86-64)
```

### TLB Characteristics:

| TLB Level | Entries | Coverage (4KB pages) | Coverage (2MB huge pages) |
|-----------|---------|---------------------|--------------------------|
| L1 ITLB   | 128     | 512 KB              | 256 MB                   |
| L1 DTLB   | 64      | 256 KB              | 128 MB                   |
| L2 TLB    | 1024    | 4 MB                | 2 GB                     |

**Key insight**: With 4KB pages and 64-entry L1 DTLB, you can have 64 different pages in TLB = 256KB of working set with zero TLB misses. For large datasets, TLB thrashing is a major bottleneck.

### Solution: Huge Pages

```bash
# Check huge page support
cat /proc/meminfo | grep Huge

# Enable transparent huge pages (THP)
echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Allocate huge pages explicitly
echo 512 > /proc/sys/vm/nr_hugepages  # 512 × 2MB = 1GB of huge pages

# Use mmap with MAP_HUGETLB
```

**C — Huge page allocation:**
```c
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>

#define HUGE_PAGE_SIZE (2 * 1024 * 1024)  /* 2 MB */
#define ALLOC_SIZE     (512UL * HUGE_PAGE_SIZE)  /* 1 GB */

/* Allocate memory backed by 2MB huge pages */
static void *alloc_huge_pages(size_t size) {
    /* Round up to huge page boundary */
    size_t rounded = (size + HUGE_PAGE_SIZE - 1) & ~(size_t)(HUGE_PAGE_SIZE - 1);
    
    void *ptr = mmap(NULL, rounded,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                     -1, 0);
    
    if (ptr == MAP_FAILED) {
        /* Fall back to regular pages + madvise */
        fprintf(stderr, "MAP_HUGETLB failed (%s), trying madvise fallback\n",
                strerror(errno));
        
        ptr = mmap(NULL, rounded,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS,
                   -1, 0);
        
        if (ptr == MAP_FAILED) {
            perror("mmap");
            return NULL;
        }
        
        /* Hint kernel to use huge pages (Transparent Huge Pages) */
        madvise(ptr, rounded, MADV_HUGEPAGE);
    }
    
    return ptr;
}

int main(void) {
    printf("Allocating %lu MB with huge pages...\n", ALLOC_SIZE >> 20);
    
    void *mem = alloc_huge_pages(ALLOC_SIZE);
    if (!mem) return 1;
    
    /* Touch all pages to force physical allocation */
    uint8_t *bytes = (uint8_t *)mem;
    for (size_t i = 0; i < ALLOC_SIZE; i += HUGE_PAGE_SIZE) {
        bytes[i] = 1;  /* One write per huge page = one TLB entry covers 2MB */
    }
    
    printf("Allocated successfully\n");
    printf("With 4KB pages: would need %lu TLB entries\n", ALLOC_SIZE / 4096);
    printf("With 2MB pages: needs only %lu TLB entries\n", ALLOC_SIZE / HUGE_PAGE_SIZE);
    
    munmap(mem, ALLOC_SIZE);
    return 0;
}
```

**Rust — Huge page-aware allocator:**
```rust
use std::ptr;

const HUGE_PAGE_SIZE: usize = 2 * 1024 * 1024; // 2MB

/// Allocate a buffer backed by transparent huge pages.
/// Falls back to regular allocation with MADV_HUGEPAGE hint.
pub struct HugePageBuffer {
    ptr: *mut u8,
    len: usize,
}

impl HugePageBuffer {
    pub fn new(size: usize) -> Option<Self> {
        // Round up to huge page boundary
        let aligned_size = (size + HUGE_PAGE_SIZE - 1) & !(HUGE_PAGE_SIZE - 1);
        
        let ptr = unsafe {
            // Try MAP_HUGETLB first
            #[cfg(target_os = "linux")]
            {
                use libc::{mmap, MAP_ANONYMOUS, MAP_FAILED, MAP_HUGETLB, MAP_PRIVATE,
                           PROT_READ, PROT_WRITE, MADV_HUGEPAGE, madvise};
                
                let p = mmap(
                    ptr::null_mut(),
                    aligned_size,
                    PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                    -1,
                    0,
                );
                
                if p == MAP_FAILED {
                    // Fall back to regular mmap + MADV_HUGEPAGE
                    let p2 = mmap(
                        ptr::null_mut(),
                        aligned_size,
                        PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS,
                        -1,
                        0,
                    );
                    if p2 == MAP_FAILED { return None; }
                    madvise(p2, aligned_size, MADV_HUGEPAGE);
                    p2 as *mut u8
                } else {
                    p as *mut u8
                }
            }
            
            #[cfg(not(target_os = "linux"))]
            {
                // Non-Linux: regular aligned allocation
                std::alloc::alloc(
                    std::alloc::Layout::from_size_align(aligned_size, HUGE_PAGE_SIZE)
                        .ok()?
                )
            }
        };
        
        if ptr.is_null() { return None; }
        
        Some(HugePageBuffer { ptr, len: aligned_size })
    }
    
    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }
    
    pub fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.ptr, self.len) }
    }
}

impl Drop for HugePageBuffer {
    fn drop(&mut self) {
        unsafe {
            #[cfg(target_os = "linux")]
            libc::munmap(self.ptr as *mut libc::c_void, self.len);
            
            #[cfg(not(target_os = "linux"))]
            std::alloc::dealloc(
                self.ptr,
                std::alloc::Layout::from_size_align(self.len, HUGE_PAGE_SIZE).unwrap()
            );
        }
    }
}

// SAFETY: Single-threaded use only without synchronization
unsafe impl Send for HugePageBuffer {}

fn main() {
    const SIZE: usize = 256 * 1024 * 1024; // 256 MB
    
    match HugePageBuffer::new(SIZE) {
        Some(mut buf) => {
            println!("Allocated {} MB with huge page backing", SIZE >> 20);
            println!("Required TLB entries (4KB pages): {}", SIZE / 4096);
            println!("Required TLB entries (2MB pages): {}", SIZE / HUGE_PAGE_SIZE);
            
            // Touch pages to force physical allocation
            let slice = buf.as_mut_slice();
            for i in (0..slice.len()).step_by(HUGE_PAGE_SIZE) {
                slice[i] = 1;
            }
            println!("All pages touched successfully");
        }
        None => eprintln!("Huge page allocation failed"),
    }
}
```

---

## 13. Write Policies

### Write-Through Cache

When the CPU writes to a cache line, the write is **immediately propagated** to the next level (RAM).

**Pros**: Consistency — RAM always has latest data.  
**Cons**: Every write causes a RAM bus transaction. Slow for write-heavy workloads.

### Write-Back Cache

Writes stay in cache and are only written to RAM when the cache line is **evicted** (dirty eviction).

**Pros**: Multiple writes to the same line coalesce into one RAM write.  
**Cons**: RAM may have stale data; needs hardware tracking of "dirty" lines.

Modern CPUs use **write-back** for normal memory. **Write-through** is used for device memory/MMIO regions.

### Write Combining (WC) Memory

A special memory type for framebuffers and DMA targets. Multiple writes are buffered in a **Write Combining Buffer** (WCB) and sent as a single burst when the buffer is full or flushed. Bypasses cache entirely.

```c
/* Non-temporal stores: write directly to RAM, bypass cache */
/* Used for streaming writes where data won't be read back soon */
#include <immintrin.h>

void stream_write(float *dst, const float *src, size_t n) {
    size_t i = 0;
    /* Write 32 bytes at a time using non-temporal (streaming) stores */
    for (; i + 8 <= n; i += 8) {
        __m256 v = _mm256_loadu_ps(src + i);
        _mm256_stream_ps(dst + i, v);  /* NT store: bypass L1/L2/L3 */
    }
    /* Handle remainder */
    for (; i < n; i++) {
        dst[i] = src[i];
    }
    /* Ensure all NT stores are visible before proceeding */
    _mm_sfence();
}
```

---

## 14. Cache Coherence — MESI Protocol

### What is the MESI Protocol?

In a multi-core CPU, each core has its own L1/L2 cache. Without coordination, two cores could have different versions of the same data — **cache incoherence**. The **MESI protocol** ensures all cores agree on the state of each cache line.

### MESI States (for each cache line):

| State    | Meaning                                             | Can read? | Can write? |
|----------|-----------------------------------------------------|-----------|------------|
| **M**odified  | Line is dirty; I have the only valid copy       | Yes       | Yes        |
| **E**xclusive | Line is clean; I have the only copy             | Yes       | Yes (→M)   |
| **S**hared    | Line is clean; other caches may also have it    | Yes       | No (→I first) |
| **I**nvalid   | Line is not valid                               | No        | No         |

### MESI State Transitions:

```
Core 0 reads X:        I → E (only reader) or I → S (others have it)
Core 0 writes X (E):   E → M (silent upgrade)
Core 0 writes X (S):   S → M (broadcast invalidate to other cores)
Core 1 reads X (Core 0 has M): Core 0: M → S, Core 1: I → S
```

### Memory Barriers

Memory barriers (fences) prevent reordering of memory operations across the barrier. Required for correct multi-core code.

**C — Memory barriers:**
```c
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>

/*
 * Memory order hierarchy (from weakest to strongest):
 * - relaxed:    No ordering guarantees. Only atomicity.
 * - acquire:    All loads/stores AFTER this load see stores from the release.
 * - release:    All loads/stores BEFORE this store are visible before the load that acquires.
 * - acq_rel:    Combines acquire + release. For read-modify-write ops.
 * - seq_cst:    Total ordering. Most expensive. Default for atomic operations.
 */

/* Producer-consumer with proper acquire-release ordering */
typedef struct {
    atomic_int   ready;   /* Flag: 0 = not ready, 1 = ready */
    int64_t      data;    /* The payload */
} shared_data_t;

static shared_data_t shared = { .ready = ATOMIC_VAR_INIT(0), .data = 0 };

/* Producer thread */
static void producer(void) {
    shared.data = 42;  /* Write data */
    /* Release fence: all writes above become visible before ready=1 */
    atomic_store_explicit(&shared.ready, 1, memory_order_release);
}

/* Consumer thread */
static void consumer(void) {
    /* Acquire fence: spin until ready=1, then all prior writes are visible */
    while (!atomic_load_explicit(&shared.ready, memory_order_acquire)) {
        /* Hint CPU this is a spin-wait: reduces power, helps HT partner */
        __asm__ volatile("pause" ::: "memory");
    }
    printf("Got: %ld\n", shared.data);  /* Guaranteed to see 42 */
}

int main(void) {
    /* In single-threaded context, demonstrate the pattern */
    producer();
    consumer();
    return 0;
}
```

**Rust — Memory ordering:**
```rust
use std::sync::atomic::{AtomicI64, AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;

/// Demonstrates correct acquire-release pairing for a lock-free flag.
fn producer_consumer_example() {
    let data  = Arc::new(AtomicI64::new(0));
    let ready = Arc::new(AtomicBool::new(false));
    
    let data2  = Arc::clone(&data);
    let ready2 = Arc::clone(&ready);
    
    // Producer: write data, then signal readiness
    let producer = thread::spawn(move || {
        data2.store(42, Ordering::Relaxed);   // data write — no ordering needed here...
        // ...because the release below ensures this write happens-before
        ready2.store(true, Ordering::Release); // Release: establishes happens-before
    });
    
    // Consumer: wait for signal, then read data
    let consumer = thread::spawn(move || {
        // Acquire: pairs with producer's Release
        // Guarantees: all writes before ready.store(true, Release)
        //             are visible after ready.load(Acquire) returns true
        while !ready.load(Ordering::Acquire) {
            std::hint::spin_loop(); // x86: PAUSE instruction
        }
        let val = data.load(Ordering::Relaxed); // Safe: acquire saw the release
        println!("Consumer received: {val}");
        assert_eq!(val, 42, "Data must be 42 — ordering guarantee violated!");
    });
    
    producer.join().unwrap();
    consumer.join().unwrap();
}

fn main() {
    producer_consumer_example();
    println!("Memory ordering example completed successfully");
}
```

---

## 15. Linux Kernel Cache Concepts

### 15.1 The Slab Allocator (SLUB/SLAB/SLOB)

The Linux kernel manages its own heap using the **slab allocator** — a cache-friendly memory allocator specifically designed for kernel objects.

**Key concepts:**
- **Slab**: A contiguous block of memory (usually one or more pages) pre-divided into fixed-size object slots
- **Cache**: A named pool of same-sized objects (e.g., `task_struct` cache, `inode` cache)
- **Magazine/Per-CPU cache**: Each CPU has a local free-list to avoid lock contention

**Why slabs are cache-friendly:**
1. Same-type objects packed together → accessing many objects = sequential scan
2. Per-CPU caches = recently freed objects are still warm in cache
3. Cache coloring: slab start offset varies per slab to reduce conflict misses

```bash
# View kernel slab allocator statistics
cat /proc/slabinfo

# View specific slab caches
sudo slabtop

# Key fields:
# NAME: slab cache name (dentry, inode_cache, task_struct, etc.)
# ACTIVE: currently allocated objects
# OBJSIZE: bytes per object
# OBJPERSLAB: objects per slab page

# More detailed view
cat /sys/kernel/slab/*/alloc_calls  # where objects are allocated from
```

### 15.2 The Page Cache

The Linux **page cache** is the kernel's mechanism for caching disk data in RAM. When you read a file, the kernel reads it into the page cache. Subsequent reads are served from RAM. All file I/O goes through the page cache by default.

```bash
# View page cache usage
free -h  
# "buff/cache" column = page cache + buffer cache

# Drop page cache (for benchmarking)
sync && echo 3 > /proc/sys/vm/drop_caches
# 1: page cache, 2: dentries+inodes, 3: all

# View which files are in page cache
sudo vmtouch /path/to/file         # shows % cached
sudo vmtouch -t /path/to/file      # touch = load into page cache
sudo vmtouch -e /path/to/file      # evict from page cache

# fincore: pages cached for a specific file
fincore /path/to/large/file
```

**Cache-friendly file I/O in C:**
```c
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

/* 
 * mmap vs read() for large sequential file access:
 * - mmap: kernel page cache directly mapped into process address space
 *         hardware prefetcher can work across pages
 * - read(): copies from page cache to user buffer (one extra copy)
 *
 * For random access large files: mmap is usually better.
 * For sequential reads: read() with large buffer can be similar or better.
 */

/* Approach 1: read() with large buffer — amortizes syscall cost */
static long sum_file_buffered(const char *path) {
    const size_t BUF_SIZE = 1024 * 1024;  /* 1MB buffer */
    
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open"); return -1; }
    
    /* Tell kernel we'll read sequentially — enables aggressive readahead */
    posix_fadvise(fd, 0, 0, POSIX_FADV_SEQUENTIAL);
    
    char   *buf = malloc(BUF_SIZE);
    long    sum = 0;
    ssize_t n;
    
    while ((n = read(fd, buf, BUF_SIZE)) > 0) {
        for (ssize_t i = 0; i < n; i++) {
            sum += (unsigned char)buf[i];
        }
    }
    
    free(buf);
    close(fd);
    return sum;
}

/* Approach 2: mmap — zero-copy, kernel handles paging */
static long sum_file_mmap(const char *path) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open"); return -1; }
    
    struct stat st;
    if (fstat(fd, &st) < 0) { perror("fstat"); close(fd); return -1; }
    
    size_t size = (size_t)st.st_size;
    if (size == 0) { close(fd); return 0; }
    
    /* Map file into address space — no data read yet (demand paging) */
    void *mapped = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    
    if (mapped == MAP_FAILED) { perror("mmap"); return -1; }
    
    /* Advise kernel: sequential access, enable readahead */
    madvise(mapped, size, MADV_SEQUENTIAL);
    /* Also: MADV_WILLNEED = prefetch now; MADV_DONTNEED = evict after use */
    
    const unsigned char *data = (const unsigned char *)mapped;
    long sum = 0;
    for (size_t i = 0; i < size; i++) {
        sum += data[i];
    }
    
    /* Free the mapping — data may stay in page cache */
    munmap(mapped, size);
    return sum;
}

/* Approach 3: O_DIRECT — bypass page cache entirely */
/* Use when: writing data you'll never re-read (log files, database WAL) */
static long sum_file_direct(const char *path) {
    /* O_DIRECT requires: buffer aligned to 512 bytes, size multiple of 512 */
    const size_t BLOCK_SIZE = 4096;  /* must match filesystem block size */
    
    int fd = open(path, O_RDONLY | O_DIRECT);
    if (fd < 0) {
        /* O_DIRECT may not be supported on all filesystems */
        fprintf(stderr, "O_DIRECT not supported, using buffered\n");
        return sum_file_buffered(path);
    }
    
    /* Aligned buffer for O_DIRECT */
    void *buf = NULL;
    if (posix_memalign(&buf, BLOCK_SIZE, BLOCK_SIZE * 256) != 0) {
        perror("posix_memalign");
        close(fd);
        return -1;
    }
    
    long    sum = 0;
    ssize_t n;
    while ((n = read(fd, buf, BLOCK_SIZE * 256)) > 0) {
        const unsigned char *data = (const unsigned char *)buf;
        for (ssize_t i = 0; i < n; i++) {
            sum += data[i];
        }
    }
    
    free(buf);
    close(fd);
    return sum;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <file>\n", argv[0]);
        return 1;
    }
    
    printf("Buffered: sum = %ld\n", sum_file_buffered(argv[1]));
    printf("mmap:     sum = %ld\n", sum_file_mmap(argv[1]));
    printf("direct:   sum = %ld\n", sum_file_direct(argv[1]));
    return 0;
}
```

### 15.3 Cache-Related Kernel Parameters

```bash
# ──── Virtual Memory / Page Cache Tuning ────────────────────────────

# vm.swappiness: 0=avoid swap (keep data in RAM), 100=aggressive swap
cat /proc/sys/vm/swappiness
sudo sysctl -w vm.swappiness=10

# vm.dirty_ratio: % of RAM that can be dirty before write is forced
cat /proc/sys/vm/dirty_ratio
sudo sysctl -w vm.dirty_ratio=5

# vm.dirty_background_ratio: % where background writeback starts
sudo sysctl -w vm.dirty_background_ratio=2

# ──── Transparent Huge Pages ─────────────────────────────────────────
# Always/madvise/never
cat /sys/kernel/mm/transparent_hugepage/enabled
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled

# ──── NUMA Balancing ─────────────────────────────────────────────────
# Automatic NUMA page migration — moves pages closer to accessing CPU
cat /proc/sys/kernel/numa_balancing
sudo sysctl -w kernel.numa_balancing=1

# ──── CPU Cache Flushing ─────────────────────────────────────────────
# wbinvd: write-back and invalidate all caches (kernel mode only)
# Used during power management, CPU hotplug, etc.

# ──── perf cache events ──────────────────────────────────────────────
# hardware cache events exposed via perf
perf stat -e \
  cache-references,\
  cache-misses,\
  L1-dcache-loads,\
  L1-dcache-load-misses,\
  L1-dcache-stores,\
  LLC-loads,\
  LLC-load-misses,\
  dTLB-loads,\
  dTLB-load-misses \
  ./your_program

# ──── CPU frequency and cache interaction ────────────────────────────
# Cache access latencies scale with CPU frequency.
# At 3GHz: L1 miss = 4ns (12 cycles). At 1GHz: L1 miss = 12ns but still 12 cycles.
# Set performance governor for consistent benchmarks:
sudo cpupower frequency-set -g performance
```

### 15.4 Linux Kernel Cache-Conscious Data Structures

The Linux kernel itself is a masterclass in cache-conscious design:

**`task_struct` Cache Coloring**: The kernel slab allocator assigns different start offsets (colors) to slabs of the same type. This prevents multiple `task_struct` objects from mapping to the same cache sets.

**`rcu` (Read-Copy-Update)**: RCU allows read-side critical sections with zero locking overhead. Readers never block, never use locks — hot path remains cache-friendly.

**Per-CPU variables**: Each CPU has its own copy of frequently-modified kernel variables, eliminating false sharing:

```c
/* Linux kernel per-CPU example (conceptual) */
DEFINE_PER_CPU(unsigned long, cpu_events);

/* Read on current CPU — no cache line bouncing */
unsigned long events = this_cpu_read(cpu_events);

/* Write on current CPU */
this_cpu_inc(cpu_events);

/* Aggregate across all CPUs */
unsigned long total = 0;
for_each_possible_cpu(cpu) {
    total += per_cpu(cpu_events, cpu);
}
```

**Applying the per-CPU pattern in user-space C:**
```c
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_CPUS     128
#define CACHE_LINE   64
#define ITERATIONS   10000000

/* Per-CPU counter — modeled after Linux kernel DEFINE_PER_CPU */
typedef struct {
    int64_t value;
    char    _pad[CACHE_LINE - sizeof(int64_t)];
} __attribute__((aligned(CACHE_LINE))) per_cpu_counter_t;

static per_cpu_counter_t global_counter[MAX_CPUS];
static int               num_cpus;

typedef struct {
    int cpu_id;
} worker_arg_t;

static void *worker(void *arg) {
    worker_arg_t *wa = (worker_arg_t *)arg;
    int cpu = wa->cpu_id;
    
    /* Each thread modifies only its own CPU's counter */
    for (int i = 0; i < ITERATIONS; i++) {
        global_counter[cpu].value++;  /* Hot line stays in this core's L1 */
    }
    return NULL;
}

static int64_t aggregate_counter(void) {
    int64_t total = 0;
    for (int i = 0; i < num_cpus; i++) {
        total += global_counter[i].value;
    }
    return total;
}

int main(void) {
    num_cpus = 4;
    pthread_t threads[MAX_CPUS];
    worker_arg_t args[MAX_CPUS];
    
    for (int i = 0; i < num_cpus; i++) {
        global_counter[i].value = 0;
        args[i].cpu_id = i;
        pthread_create(&threads[i], NULL, worker, &args[i]);
    }
    for (int i = 0; i < num_cpus; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("Total: %ld (expected: %d)\n",
           aggregate_counter(), num_cpus * ITERATIONS);
    return 0;
}
```

### 15.5 `perf` — Linux Performance Counters

`perf` reads hardware performance counters (PMU — Performance Monitoring Unit) built into the CPU. These counters measure actual cache events happening in silicon.

```bash
# ── Basic cache miss profiling ─────────────────────────────────────
perf stat -e cache-misses,cache-references ./program
# Output: cache miss rate = misses/references

# ── Detailed cache breakdown ──────────────────────────────────────
perf stat -e \
  L1-dcache-loads,L1-dcache-load-misses,\
  L1-icache-loads,L1-icache-load-misses,\
  L1-dcache-prefetch-misses,\
  LLC-loads,LLC-load-misses,\
  LLC-stores,LLC-store-misses \
  ./program

# ── Record + report for hotspot analysis ──────────────────────────
perf record -e cache-misses:u -g ./program
perf report  # interactive TUI showing which functions cause misses

# ── Memory access pattern profiling (PEBS — Precise Event Based Sampling)
perf mem record ./program
perf mem report  # shows load/store latencies with source locations

# ── TLB miss profiling ────────────────────────────────────────────
perf stat -e dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses ./program

# ── false sharing detection with perf c2c ─────────────────────────
# c2c = cache-to-cache transfer (indicates false sharing)
perf c2c record ./program
perf c2c report  # shows hot cache lines with sharing information

# ── vtune equivalent: toplev ──────────────────────────────────────
# pip install pmu-tools
toplev ./program  # top-down microarchitecture analysis
```

### 15.6 `/proc/cpuinfo` Cache Information

```bash
# Full cache info per CPU
cat /proc/cpuinfo | grep -A5 "cache"

# Detailed cache topology via sysfs
for cache in /sys/devices/system/cpu/cpu0/cache/index*; do
    echo "=== $cache ==="
    echo "Level: $(cat $cache/level)"
    echo "Type:  $(cat $cache/type)"
    echo "Size:  $(cat $cache/size)"
    echo "Associativity: $(cat $cache/ways_of_associativity)"
    echo "Line size: $(cat $cache/coherency_line_size)"
    echo "Sets: $(cat $cache/number_of_sets)"
done
```

### 15.7 `cachestat` / `bpftrace` — Tracing Page Cache

```bash
# cachestat: Linux page cache hit/miss rates (from BCC tools)
sudo cachestat 1  # 1-second intervals

# bpftrace: trace cache events with eBPF
sudo bpftrace -e '
tracepoint:filemap:mm_filemap_add_to_page_cache { @add[comm] = count(); }
tracepoint:filemap:mm_filemap_delete_from_page_cache { @del[comm] = count(); }
interval:s:5 { print(@add); print(@del); clear(@add); clear(@del); }
'

# cachetop: top-like interface for page cache
sudo cachetop 5

# fincore: check what fraction of a file is in page cache
sudo fincore /path/to/file
```

---

## 16. Compiler Optimizations for Cache

### 16.1 Restrict Keyword (C) / `noalias` (LLVM)

When two pointers might alias (point to overlapping memory), the compiler cannot reorder or fuse loads/stores. `restrict` tells the compiler the pointers are independent — enabling vectorization and better scheduling.

```c
/* Without restrict: compiler assumes src and dst might overlap */
void copy_slow(float *dst, const float *src, size_t n) {
    for (size_t i = 0; i < n; i++) {
        dst[i] = src[i];  /* Cannot be vectorized: dst[i] might = src[i+1] */
    }
}

/* With restrict: guaranteed no aliasing — compiler can use SIMD memcpy */
void copy_fast(float *__restrict__ dst, const float *__restrict__ src, size_t n) {
    for (size_t i = 0; i < n; i++) {
        dst[i] = src[i];  /* Can be vectorized: independent writes/reads */
    }
}
/* gcc -O3 will vectorize copy_fast with AVX2: 8 floats per instruction */
```

### 16.2 `__builtin_expect` — Branch Prediction Hints

Branch mispredictions flush the CPU pipeline and indirectly hurt cache performance (wrong speculative fetches pollute the instruction cache).

```c
/* Without hint: compiler doesn't know which branch is hot */
if (error_condition) {
    handle_error();
}

/* With hint: tell compiler (and CPU branch predictor) this is rare */
if (__builtin_expect(error_condition, 0)) {  /* 0 = unlikely */
    handle_error();  /* cold path: compiler moves this far from hot code */
}

/* For likely branches */
if (__builtin_expect(normal_case, 1)) {  /* 1 = likely */
    fast_path();
}

/* C++20 / modern C: [[likely]] / [[unlikely]] attributes */
/* GCC macro convention */
#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
```

### 16.3 Loop Optimizations

**C — Loop transformations for cache:**
```c
#include <stddef.h>

/* ─── Loop Unrolling ─────────────────────────────────────────────── */
/* Without unrolling: one iteration = one add, one compare, one branch */
void sum_basic(const int *arr, int *out, size_t n) {
    int s = 0;
    for (size_t i = 0; i < n; i++) s += arr[i];
    *out = s;
}

/* Manual 4× unroll: reduces loop overhead, exposes ILP to CPU */
void sum_unrolled(const int *arr, int *out, size_t n) {
    int s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    size_t i = 0;
    for (; i + 4 <= n; i += 4) {
        s0 += arr[i + 0];  /* Independent: CPU executes all 4 in parallel */
        s1 += arr[i + 1];  /* (superscalar execution) */
        s2 += arr[i + 2];
        s3 += arr[i + 3];
    }
    for (; i < n; i++) s0 += arr[i];  /* tail */
    *out = s0 + s1 + s2 + s3;
}
/* Or: tell compiler to unroll: #pragma GCC unroll 4 */

/* ─── Loop Fusion ────────────────────────────────────────────────── */
/* BAD: Two passes over array = each element loaded from cache twice */
void two_passes(const float *arr, float *out_sq, float *out_abs, size_t n) {
    for (size_t i = 0; i < n; i++) out_sq[i]  = arr[i] * arr[i];
    for (size_t i = 0; i < n; i++) out_abs[i] = arr[i] < 0 ? -arr[i] : arr[i];
}

/* GOOD: One pass = each element loaded once */
void one_pass(const float *arr, float *out_sq, float *out_abs, size_t n) {
    for (size_t i = 0; i < n; i++) {
        float v = arr[i];         /* Load once */
        out_sq[i]  = v * v;
        out_abs[i] = v < 0 ? -v : v;
    }
}

/* ─── Loop Fission (opposite of fusion) ─────────────────────────── */
/* When two independent operations in one loop prevent vectorization */
/* Split them so each can be vectorized separately */
```

**Rust — Compiler optimization hints:**
```rust
/// Demonstrate various Rust compiler optimization techniques for cache efficiency.

/// Branch hint: cold path
#[cold]
#[inline(never)]
fn handle_error(msg: &str) {
    eprintln!("Error: {msg}");
}

/// Likely to be inlined and placed in hot code path
#[inline(always)]
fn fast_path(x: f32) -> f32 {
    x * x + x
}

/// Tell LLVM this function is latency-critical
/// Use target_feature to enable SIMD
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn vectorized_sum(arr: &[f32]) -> f32 {
    // With avx2 enabled, the compiler can use 256-bit SIMD
    arr.iter().sum()
}

/// Loop with explicit LLVM vectorization hint via iter
fn sum_with_simd_hint(arr: &[f32]) -> f32 {
    // Rust's iterator `sum` is vectorized by LLVM when compiled with:
    // RUSTFLAGS="-C target-cpu=native"
    arr.iter().copied().sum()
}

/// Prefetch-aware chunk processing
/// Process data in chunks that fit in L1 cache
fn process_chunked(data: &mut [f32], chunk_size: usize) {
    for chunk in data.chunks_mut(chunk_size) {
        // This chunk fits in L1 cache
        for x in chunk.iter_mut() {
            *x = x.sqrt() + x.ln().abs();
        }
    }
}

fn main() {
    let mut data: Vec<f32> = (1..=1_000_000).map(|i| i as f32).collect();
    
    // L1 cache = 32KB. f32 = 4 bytes. L1 holds 8192 f32s.
    const L1_CHUNK: usize = 8192;
    process_chunked(&mut data, L1_CHUNK);
    
    let sum = sum_with_simd_hint(&data);
    println!("Sum: {sum:.2}");
    
    // Error path: marked cold, moves out of hot code
    if data.is_empty() {
        handle_error("empty data"); // cold path
    }
}
```

### 16.4 Profile-Guided Optimization (PGO)

PGO uses actual runtime profiles to guide compiler decisions: inlining, branch layout, function ordering.

```bash
# ── GCC PGO ────────────────────────────────────────────────────────
# Step 1: Compile with instrumentation
gcc -O2 -fprofile-generate -o program_instr program.c

# Step 2: Run with representative workload
./program_instr < typical_input.txt

# Step 3: Compile with profile data
gcc -O2 -fprofile-use -fprofile-correction -o program_pgo program.c

# ── Clang PGO ──────────────────────────────────────────────────────
clang -O2 -fprofile-instr-generate -o program_instr program.c
./program_instr < typical_input.txt
llvm-profdata merge -output=default.profdata default.profraw
clang -O2 -fprofile-instr-use=default.profdata -o program_pgo program.c

# ── Rust PGO ───────────────────────────────────────────────────────
# Step 1: Build with instrumentation
RUSTFLAGS="-Cprofile-generate=/tmp/pgo-data" \
    cargo build --release --target x86_64-unknown-linux-gnu

# Step 2: Run representative workload
./target/release/myprogram < workload.txt

# Step 3: Merge profile data
llvm-profdata merge -o /tmp/pgo-data/merged.profdata /tmp/pgo-data

# Step 4: Build with profile data
RUSTFLAGS="-Cprofile-use=/tmp/pgo-data/merged.profdata" \
    cargo build --release --target x86_64-unknown-linux-gnu
```

---

## 17. Profiling Tools

### 17.1 `perf` — The Linux Profiler

```bash
# ── Installation ──────────────────────────────────────────────────
sudo apt-get install linux-tools-common linux-tools-$(uname -r)

# ── Record cache misses with call graphs ─────────────────────────
perf record -e cache-misses:u --call-graph dwarf -g ./program args
perf report --stdio | head -100

# ── Annotate specific function with cache miss counts ─────────────
perf annotate function_name

# ── One-liner: cache miss rate ────────────────────────────────────
perf stat -e LLC-loads,LLC-load-misses ./program 2>&1 | \
    awk '/LLC/ {print $0}'

# ── Memory access latency distribution ────────────────────────────
perf mem record ./program
perf mem report --sort=mem,sym --stdio 2>/dev/null | head -50
```

### 17.2 Valgrind Cachegrind

```bash
# ── Run program through Cachegrind simulator ──────────────────────
valgrind --tool=cachegrind \
         --cache-sim=yes \
         --branch-sim=yes \
         --D1=32768,8,64 \        # L1 data: 32KB, 8-way, 64B lines
         --LL=8388608,16,64 \     # LLC: 8MB, 16-way, 64B lines
         ./program args

# ── Annotate source code with miss counts ─────────────────────────
cg_annotate --auto=yes cachegrind.out.PID

# ── Compare two runs ─────────────────────────────────────────────
cg_diff cachegrind.out.PID1 cachegrind.out.PID2
```

### 17.3 Intel VTune / AMD μProf

```bash
# ── VTune hotspot analysis ────────────────────────────────────────
vtune -collect hotspots -result-dir r001 -- ./program
vtune -report hotspots -result-dir r001

# ── VTune memory access analysis ─────────────────────────────────
vtune -collect memory-access -result-dir r002 -- ./program
vtune -report summary -result-dir r002
```

### 17.4 `likwid` — LIKWID Performance Tools

```bash
# ── Install ───────────────────────────────────────────────────────
sudo apt-get install likwid

# ── Measure cache performance groups ─────────────────────────────
likwid-perfctr -C 0 -g CACHE ./program
likwid-perfctr -C 0 -g L2CACHE ./program
likwid-perfctr -C 0 -g L3 ./program
likwid-perfctr -C 0 -g FALSE_SHARE ./program  # false sharing detection!

# ── Measure memory bandwidth ──────────────────────────────────────
likwid-perfctr -C 0 -g MEM_DP ./program

# ── likwid-bench: micro-benchmark cache/memory bandwidth ──────────
likwid-bench -t copy -w S0:1GB:4  # Copy 1GB using 4 threads on socket 0
```

### 17.5 `heaptrack` — Heap Allocation Profiler

```bash
heaptrack ./program
heaptrack_gui heaptrack.program.PID.gz
# Shows allocations that cause cache-unfriendly memory patterns
```

---

## 18. Advanced Patterns

### 18.1 Cache-Oblivious Algorithms

A **cache-oblivious algorithm** is designed to be cache-efficient for *any* cache size and line size, without knowing these parameters at compile or run time. It works by using recursive divide-and-conquer that naturally creates working sets that fit in whatever cache level exists.

**Cache-oblivious matrix transpose:**
```c
#include <stddef.h>
#include <stdint.h>

#define TRANSPOSE_THRESHOLD 64  /* Base case: fits comfortably in L1 */

/* 
 * Recursive cache-oblivious transpose.
 * Divides the matrix recursively until the submatrix fits in cache.
 * No knowledge of actual cache size needed.
 */
static void transpose_recursive(
    float *A, float *B,
    size_t r1, size_t c1,  /* source top-left */
    size_t r2, size_t c2,  /* dest top-left */
    size_t rows, size_t cols,
    size_t N  /* original matrix stride */
) {
    if (rows <= TRANSPOSE_THRESHOLD && cols <= TRANSPOSE_THRESHOLD) {
        /* Base case: small block — fits in L1 */
        for (size_t i = 0; i < rows; i++) {
            for (size_t j = 0; j < cols; j++) {
                B[(c2 + i) * N + (r2 + j)] = A[(r1 + i) * N + (c1 + j)];
            }
        }
        return;
    }
    
    /* Divide the larger dimension */
    if (rows >= cols) {
        size_t half = rows / 2;
        transpose_recursive(A, B, r1,         c1, r2,         c2, half,        cols, N);
        transpose_recursive(A, B, r1 + half,  c1, r2, c2 + half,  rows - half, cols, N);
    } else {
        size_t half = cols / 2;
        transpose_recursive(A, B, r1, c1,        r2,         c2, rows, half,        N);
        transpose_recursive(A, B, r1, c1 + half, r2 + half,  c2, rows, cols - half, N);
    }
}

void matrix_transpose_oblivious(const float *src, float *dst, size_t N) {
    /* We cast away const for the recursive helper's uniform interface */
    transpose_recursive((float *)src, dst, 0, 0, 0, 0, N, N, N);
}
```

### 18.2 Software-Managed Streaming

For data that is **written but never reread** (streaming output), use non-temporal stores to bypass the cache entirely. This avoids polluting the cache with data you won't use.

```c
#include <immintrin.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * Non-temporal (streaming) memcpy.
 * Reads source normally (benefits from prefetch/cache),
 * writes destination via NT stores (bypasses cache).
 * 
 * Use when: writing large buffers that won't be re-read soon.
 * Examples: disk I/O buffers, framebuffer writes, network packet output.
 */
void stream_memcpy(void *dst, const void *src, size_t n) {
    const char *s = (const char *)src;
    char       *d = (char *)dst;
    
    /* Process 256-bit (32-byte) chunks */
    size_t i = 0;
    for (; i + 32 <= n; i += 32) {
        /* Prefetch source 512 bytes ahead */
        __builtin_prefetch(s + i + 512, 0, 1);
        
        /* Load 32 bytes from source (goes through cache) */
        __m256i v = _mm256_loadu_si256((const __m256i *)(s + i));
        
        /* Non-temporal store to destination (bypasses cache) */
        _mm256_stream_si256((__m256i *)(d + i), v);
    }
    
    /* Handle remainder */
    memcpy(d + i, s + i, n - i);
    
    /* Ensure all NT stores are globally visible */
    _mm_sfence();
}
```

### 18.3 B-Tree vs Cache-Friendly B-Tree

Traditional B-trees use dynamic node allocation (heap pointers everywhere). For maximum cache efficiency, use an **arena-allocated B-tree** with integer indices instead of pointers.

**Rust — Arena-based B-tree node:**
```rust
/// Cache-friendly B-tree: nodes stored in a flat Vec (arena).
/// Use integer indices instead of pointers → better cache density,
/// no heap fragmentation, NUMA-friendly batch allocation.

const ORDER: usize = 16; // Each node holds up to 2*ORDER-1 keys

#[derive(Clone)]
struct BTreeNode {
    keys:     [i64; 2 * ORDER - 1],
    children: [u32; 2 * ORDER],   // indices into arena, u32 saves 4 bytes vs u64
    num_keys: u32,
    is_leaf:  bool,
    _pad:     [u8; 3],            // explicit padding
}

impl BTreeNode {
    fn new_leaf() -> Self {
        BTreeNode {
            keys:     [0; 2 * ORDER - 1],
            children: [u32::MAX; 2 * ORDER], // u32::MAX = null sentinel
            num_keys: 0,
            is_leaf:  true,
            _pad:     [0; 3],
        }
    }
    
    fn new_internal() -> Self {
        let mut node = Self::new_leaf();
        node.is_leaf = false;
        node
    }
}

/// Arena-based B-tree: all nodes in one Vec → sequential memory → cache-friendly
struct BTree {
    arena: Vec<BTreeNode>,  // All nodes live here — contiguous allocation
    root:  u32,             // Index of root node
}

impl BTree {
    fn new() -> Self {
        let mut arena = Vec::with_capacity(1024);
        arena.push(BTreeNode::new_leaf()); // root starts as empty leaf
        BTree { arena, root: 0 }
    }
    
    fn alloc_node(&mut self, node: BTreeNode) -> u32 {
        let idx = self.arena.len() as u32;
        self.arena.push(node);
        idx
    }
    
    fn search(&self, key: i64) -> bool {
        let mut node_idx = self.root;
        loop {
            let node = &self.arena[node_idx as usize];
            // Linear scan within node — all keys fit in 1-2 cache lines
            let pos = node.keys[..node.num_keys as usize]
                .iter()
                .position(|&k| k >= key);
            
            match pos {
                Some(i) if node.keys[i] == key => return true,
                _ if node.is_leaf => return false,
                Some(i) => node_idx = node.children[i],
                None    => node_idx = node.children[node.num_keys as usize],
            }
        }
    }
}
```

---

## 19. Allocator Strategies for Cache Efficiency

### 19.1 Pool Allocator

Pre-allocate a fixed number of same-sized objects. Returns cache-hot objects (recently freed = still warm in cache). Eliminates heap fragmentation.

**C — Pool allocator:**
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define POOL_BLOCK_SIZE  64   /* Align each block to cache line */
#define POOL_CAPACITY    4096 /* Pre-allocate this many objects */

typedef struct free_node {
    struct free_node *next;
} free_node_t;

typedef struct {
    void       *memory;       /* Backing storage: one big contiguous allocation */
    free_node_t *free_list;   /* Linked list of free blocks */
    size_t       object_size; /* Size of each object */
    size_t       capacity;    /* Max objects */
    size_t       in_use;      /* Currently allocated count */
} pool_allocator_t;

static int pool_init(pool_allocator_t *pool, size_t object_size, size_t capacity) {
    /* Each slot must be at least sizeof(free_node_t) and aligned to cache line */
    size_t slot_size = object_size > sizeof(free_node_t) ? object_size : sizeof(free_node_t);
    slot_size = (slot_size + POOL_BLOCK_SIZE - 1) & ~(size_t)(POOL_BLOCK_SIZE - 1);
    
    pool->memory = aligned_alloc(POOL_BLOCK_SIZE, slot_size * capacity);
    if (!pool->memory) return -1;
    
    pool->object_size = slot_size;
    pool->capacity    = capacity;
    pool->in_use      = 0;
    
    /* Build the free list through the memory block */
    pool->free_list = (free_node_t *)pool->memory;
    char *ptr = (char *)pool->memory;
    for (size_t i = 0; i < capacity - 1; i++) {
        free_node_t *node = (free_node_t *)ptr;
        node->next = (free_node_t *)(ptr + slot_size);
        ptr += slot_size;
    }
    ((free_node_t *)ptr)->next = NULL;  /* Last node: no next */
    
    return 0;
}

static void *pool_alloc(pool_allocator_t *pool) {
    if (!pool->free_list) return NULL;  /* Pool exhausted */
    
    free_node_t *node = pool->free_list;
    pool->free_list = node->next;
    pool->in_use++;
    
    /* Clear only the object data (not the entire slot) */
    memset(node, 0, pool->object_size);
    return (void *)node;
}

static void pool_free(pool_allocator_t *pool, void *ptr) {
    if (!ptr) return;
    /* Re-insert at head of free list — LIFO = returns cache-hot blocks */
    free_node_t *node = (free_node_t *)ptr;
    node->next = pool->free_list;
    pool->free_list = node;
    pool->in_use--;
}

static void pool_destroy(pool_allocator_t *pool) {
    free(pool->memory);
    memset(pool, 0, sizeof(*pool));
}

/* Example usage */
typedef struct {
    int64_t id;
    float   x, y, z;
    char    name[32];
} entity_t;

int main(void) {
    pool_allocator_t pool;
    if (pool_init(&pool, sizeof(entity_t), POOL_CAPACITY) != 0) {
        perror("pool_init");
        return 1;
    }
    
    entity_t *entities[10];
    for (int i = 0; i < 10; i++) {
        entities[i] = (entity_t *)pool_alloc(&pool);
        if (!entities[i]) { fprintf(stderr, "Pool exhausted\n"); break; }
        entities[i]->id = i;
        entities[i]->x  = (float)i * 1.5f;
    }
    
    printf("Pool: %zu/%zu in use\n", pool.in_use, pool.capacity);
    
    for (int i = 0; i < 10; i++) {
        pool_free(&pool, entities[i]);
    }
    
    printf("After free: %zu in use\n", pool.in_use);
    pool_destroy(&pool);
    return 0;
}
```

**Rust — Arena allocator using `bumpalo`:**
```rust
// Add to Cargo.toml: bumpalo = "3"

/// Arena allocator: bump-pointer allocation.
/// All allocations from one contiguous block.
/// Entire arena freed at once — no individual deallocation overhead.
/// Freed objects remain warm in cache (no fragmentation).
///
/// Perfect for: request-lifetime allocations, temporary workspaces,
///              parser/compiler AST nodes.

// Using bumpalo crate (production-grade bump allocator):
// use bumpalo::Bump;
// 
// let arena = Bump::new();
// let x: &mut MyStruct = arena.alloc(MyStruct::new());
// let slice: &mut [i32] = arena.alloc_slice_fill_default(1000);
// // All memory freed when `arena` is dropped

/// Manual simple arena for demonstration:
pub struct Arena {
    memory: Vec<u8>,
    offset: usize,
}

impl Arena {
    pub fn new(capacity: usize) -> Self {
        Arena {
            memory: vec![0u8; capacity],
            offset: 0,
        }
    }
    
    /// Allocate `size` bytes aligned to `align`.
    pub fn alloc_raw(&mut self, size: usize, align: usize) -> Option<*mut u8> {
        // Align up
        let aligned = (self.offset + align - 1) & !(align - 1);
        let new_offset = aligned + size;
        
        if new_offset > self.memory.len() {
            return None; // Arena exhausted
        }
        
        self.offset = new_offset;
        Some(unsafe { self.memory.as_mut_ptr().add(aligned) })
    }
    
    /// Allocate a value of type T.
    /// SAFETY: The returned reference is valid for the arena's lifetime.
    pub fn alloc<T>(&mut self, value: T) -> Option<&mut T> {
        let ptr = self.alloc_raw(
            std::mem::size_of::<T>(),
            std::mem::align_of::<T>(),
        )? as *mut T;
        
        unsafe {
            ptr.write(value);
            Some(&mut *ptr)
        }
    }
    
    /// Reset: reuse entire arena memory (all previous allocations invalidated)
    pub fn reset(&mut self) {
        self.offset = 0;
        // Memory stays allocated — just reset the pointer
        // Previously allocated objects may still be warm in cache
    }
    
    pub fn bytes_used(&self) -> usize { self.offset }
    pub fn capacity(&self) -> usize { self.memory.len() }
}

#[derive(Debug)]
struct Vector3 { x: f32, y: f32, z: f32 }

fn main() {
    let mut arena = Arena::new(1024 * 1024); // 1MB arena
    
    // All allocations from the same contiguous block
    let v1 = arena.alloc(Vector3 { x: 1.0, y: 2.0, z: 3.0 }).unwrap();
    let v2 = arena.alloc(Vector3 { x: 4.0, y: 5.0, z: 6.0 }).unwrap();
    
    v1.x += v2.x; // Modifying through raw pointer — unsound without careful lifetime management
    
    println!("v1: {:?}", v1);
    println!("Used: {}/{} bytes", arena.bytes_used(), arena.capacity());
    
    // Reset for next "frame" or "request" — O(1) deallocation of all objects
    arena.reset();
    println!("After reset: {}/{} bytes", arena.bytes_used(), arena.capacity());
}
```

---

## 20. Production Case Studies

### Case Study 1: Hash Map — Robin Hood Hashing

Standard `std::unordered_map` (C++) stores each element in a separately-heap-allocated node — pointer chasing on every lookup. Cache-friendly hash maps use **open addressing**: all elements in one flat array.

**Go — Cache-friendly open-addressing hash map:**
```go
package main

import (
	"fmt"
	"math/bits"
)

// RobinHoodMap: open-addressing hash map with Robin Hood collision resolution.
// All entries in one flat slice → sequential memory → cache-friendly.
// No per-element heap allocation unlike Go's built-in map.

const (
	emptySlot   = int64(-1 << 63)  // sentinel: empty
	deletedSlot = int64(-1<<63 + 1) // sentinel: deleted (tombstone)
	maxLoadPct  = 70 // resize when 70% full
)

type entry struct {
	key   int64
	value int64
	dist  int32 // probe distance from ideal slot
}

type RobinHoodMap struct {
	entries  []entry
	count    int
	capacity int
	mask     int
}

func NewRobinHoodMap(initialCap int) *RobinHoodMap {
	// Round up to power of two
	cap := 1
	for cap < initialCap {
		cap <<= 1
	}
	entries := make([]entry, cap)
	for i := range entries {
		entries[i].key = emptySlot
	}
	return &RobinHoodMap{entries: entries, capacity: cap, mask: cap - 1}
}

func (m *RobinHoodMap) hash(key int64) int {
	// Fibonacci hashing: good distribution
	h := uint64(key) * 11400714819323198485
	return int(h >> (64 - bits.Len(uint(m.capacity))))
}

func (m *RobinHoodMap) Insert(key, value int64) {
	if m.count*100/m.capacity >= maxLoadPct {
		m.grow()
	}
	
	idx := m.hash(key) & m.mask
	incoming := entry{key: key, value: value, dist: 0}
	
	for {
		cur := &m.entries[idx]
		
		if cur.key == emptySlot || cur.key == deletedSlot {
			*cur = incoming
			m.count++
			return
		}
		
		if cur.key == incoming.key {
			cur.value = incoming.value // Update existing
			return
		}
		
		// Robin Hood: steal from the rich (low dist), give to the poor (high dist)
		if cur.dist < incoming.dist {
			*cur, incoming = incoming, *cur
		}
		
		idx = (idx + 1) & m.mask
		incoming.dist++
	}
}

func (m *RobinHoodMap) Get(key int64) (int64, bool) {
	idx := m.hash(key) & m.mask
	dist := int32(0)
	
	for {
		cur := &m.entries[idx]
		
		if cur.key == emptySlot || cur.dist < dist {
			return 0, false // Key not present
		}
		if cur.key == key {
			return cur.value, true
		}
		
		idx = (idx + 1) & m.mask
		dist++
	}
}

func (m *RobinHoodMap) grow() {
	old := m.entries
	m.capacity *= 2
	m.mask = m.capacity - 1
	m.entries = make([]entry, m.capacity)
	for i := range m.entries {
		m.entries[i].key = emptySlot
	}
	m.count = 0
	
	for _, e := range old {
		if e.key != emptySlot && e.key != deletedSlot {
			m.Insert(e.key, e.value)
		}
	}
}

func main() {
	m := NewRobinHoodMap(64)
	
	// Insert
	for i := int64(0); i < 1000; i++ {
		m.Insert(i, i*i)
	}
	
	// Lookup
	val, ok := m.Get(42)
	fmt.Printf("Get(42) = %d, found=%v\n", val, ok) // 1764, true
	
	_, ok = m.Get(9999)
	fmt.Printf("Get(9999) found=%v\n", ok) // false
	
	fmt.Printf("Count: %d, Capacity: %d, Load: %d%%\n",
		m.count, m.capacity, m.count*100/m.capacity)
}
```

### Case Study 2: Ring Buffer (Lock-Free, Cache-Efficient)

```rust
use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicUsize, Ordering};

/// Single-producer, single-consumer lock-free ring buffer.
/// Cache-optimized: producer and consumer indices on separate cache lines.
/// Elements stored in flat array — no heap allocation per element.

const RING_SIZE: usize = 1024; // Must be power of two

#[repr(C)]
pub struct RingBuffer<T> {
    // Producer writes here; consumer reads this — separate cache lines!
    head: CacheAligned<AtomicUsize>,  // written by producer
    tail: CacheAligned<AtomicUsize>,  // written by consumer
    
    // Data array — all elements contiguous
    data: [UnsafeCell<T>; RING_SIZE],
}

#[repr(C, align(64))]
struct CacheAligned<T> {
    val: T,
}

impl<T: Default + Copy> RingBuffer<T> {
    pub fn new() -> Box<Self> {
        let buf = Box::new(RingBuffer {
            head: CacheAligned { val: AtomicUsize::new(0) },
            tail: CacheAligned { val: AtomicUsize::new(0) },
            data: std::array::from_fn(|_| UnsafeCell::new(T::default())),
        });
        buf
    }
    
    /// Push item. Returns false if buffer is full.
    pub fn push(&self, item: T) -> bool {
        let head = self.head.val.load(Ordering::Relaxed);
        let next_head = (head + 1) & (RING_SIZE - 1);
        
        // Check if full: next head would reach tail
        if next_head == self.tail.val.load(Ordering::Acquire) {
            return false; // Full
        }
        
        // Write item
        unsafe { *self.data[head].get() = item; }
        
        // Publish: release ensures item write is visible before head update
        self.head.val.store(next_head, Ordering::Release);
        true
    }
    
    /// Pop item. Returns None if buffer is empty.
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.val.load(Ordering::Relaxed);
        
        // Check if empty: tail == head
        if tail == self.head.val.load(Ordering::Acquire) {
            return None; // Empty
        }
        
        // Read item
        let item = unsafe { *self.data[tail].get() };
        
        // Advance tail: release ensures item read before tail update
        let next_tail = (tail + 1) & (RING_SIZE - 1);
        self.tail.val.store(next_tail, Ordering::Release);
        
        Some(item)
    }
    
    pub fn len(&self) -> usize {
        let head = self.head.val.load(Ordering::Relaxed);
        let tail = self.tail.val.load(Ordering::Relaxed);
        (head.wrapping_sub(tail)) & (RING_SIZE - 1)
    }
}

unsafe impl<T: Send> Send for RingBuffer<T> {}
unsafe impl<T: Send> Sync for RingBuffer<T> {}

fn main() {
    use std::sync::Arc;
    use std::thread;
    
    let ring: Arc<RingBuffer<i64>> = Arc::new(*RingBuffer::new());
    let ring2 = Arc::clone(&ring);
    
    // Producer
    let producer = thread::spawn(move || {
        let mut sent = 0i64;
        for i in 0..100_000i64 {
            while !ring.push(i) {
                std::hint::spin_loop(); // Back-pressure: wait for consumer
            }
            sent += 1;
        }
        println!("Sent: {sent}");
    });
    
    // Consumer
    let consumer = thread::spawn(move || {
        let mut received = 0i64;
        let mut sum = 0i64;
        while received < 100_000 {
            if let Some(val) = ring2.pop() {
                sum += val;
                received += 1;
            } else {
                std::hint::spin_loop();
            }
        }
        println!("Received: {received}, Sum: {sum}");
    });
    
    producer.join().unwrap();
    consumer.join().unwrap();
}
```

---

## Quick Reference: Cache Optimization Checklist

```
□ Data Layout
  □ Use SoA instead of AoS for vectorizable fields
  □ Group hot fields together (put cold fields at end of struct)
  □ Align frequently-used structs to cache lines (64 bytes)
  □ Pad shared structs to prevent false sharing

□ Access Patterns
  □ Prefer sequential (stride-1) access over random access
  □ Process data in chunks that fit in L1 cache
  □ Use loop fusion to combine multiple passes into one
  □ Use cache-blocking/tiling for 2D+ algorithms

□ Concurrency
  □ Pad per-thread/per-core data to 64-byte boundaries
  □ Use per-CPU variables for counters
  □ Use NUMA-aware allocation for multi-socket systems

□ Memory Allocation
  □ Use pool/arena allocators for same-sized objects
  □ Prefer flat arrays over pointer-linked structures
  □ Use huge pages (2MB) for large working sets (>64MB)
  □ Use mmap + MADV_SEQUENTIAL for sequential file reads
  □ Use O_DIRECT for streaming writes to disk

□ Compiler Hints
  □ Mark hot/cold paths with __builtin_expect or likely/unlikely
  □ Use __restrict__ on non-aliasing pointer parameters
  □ Enable -march=native for auto-vectorization
  □ Use PGO for production workloads
  □ Mark rarely-called functions with __attribute__((cold))

□ Measurement
  □ Profile with perf stat -e cache-misses,LLC-load-misses
  □ Detect false sharing with perf c2c
  □ Verify TLB impact with perf stat -e dTLB-load-misses
  □ Simulate with Cachegrind for detailed miss attribution
  □ Check memory bandwidth with likwid-perfctr -g MEM
```

---

## Mental Models for Cache Mastery

### The "Working Set" Mental Model
Before writing any data-intensive code, ask:
> *What is the total size of data touched in my innermost loop?*  
> If > L1: can I restructure to reduce it?  
> If > L2: can I tile/block to keep hot data in L2?  
> If > L3: is the algorithm fundamentally memory-bound?

### The "Cache Miss = Branch Misprediction = Stall" Model
Every cache miss is a CPU stall of 4–200 cycles. Treat them like exceptions — they must be eliminated in hot paths, not just minimized.

### The "Think in Cache Lines" Model
Never think of your data as bytes or elements. Think in **64-byte blocks**. When you access element i, elements i±7 come for free. Design your structs so the 7 free neighbors are also useful.

### Chunking (Cognitive Principle)
Just as human experts chunk complex patterns into single mental units, you should chunk your data access into cache-line-sized "atoms of work." An expert coder doesn't think "load byte 65, load byte 66..."; they think "load cache line 1 containing elements 16..31."

### Deliberate Practice for Cache Mastery
1. **Benchmark everything**: intuition about cache behavior is unreliable. Measure.
2. **Read `perf report` weekly**: develop pattern recognition for cache-miss hotspots.
3. **Study real codebases**: Linux kernel, Redis, RocksDB, Zig's standard library are cache-conscious masterpieces.
4. **Implement from scratch**: write your own ring buffer, pool allocator, open-addressing hash map. Understanding implementation = understanding performance.

---

*"Hardware is fast. Memory is slow. The programmer's job is to make them meet in the middle."*

---

**Compile Commands Reference:**
```bash
# C — Maximum optimization with cache-friendly flags
gcc -O3 -march=native -ffast-math -funroll-loops \
    -fprofile-use -o program program.c

# Go — Enable bounds-check elimination insights
go build -gcflags="-d=ssa/check_bce/debug=1" .
GOARCH=amd64 GOFLAGS="-p=1" go test -bench=. -count=5

# Rust — Maximum native optimization
RUSTFLAGS="-C target-cpu=native -C opt-level=3 -C lto=fat" \
    cargo build --release

# Check auto-vectorization (Rust/LLVM)
RUSTFLAGS="--emit=asm -C target-cpu=native" cargo build --release
# Inspect target/release/deps/*.s for ymm/zmm registers (AVX/AVX-512)
```

Now let me craft this comprehensive guide. This will be a large, deeply structured document.Here is your complete guide. Here's a structured summary of everything it covers:

---

## What's Inside — 20 Deep Topics

**Foundations**
- **Memory Hierarchy** — why registers → L1 → L2 → L3 → RAM → SSD exist, with real latency numbers
- **CPU Cache Architecture** — L1i/L1d split, per-core vs shared caches, inclusion policies (Intel inclusive vs AMD NINE), how to inspect your hardware via `/sys/`
- **Cache Lines** — the 64-byte atom of transfer, alignment code in all three languages, why misalignment costs double cache line fetches

**Miss Analysis**
- **The Three Cs** — Compulsory, Capacity, Conflict misses, plus the 4th C (Coherence) for multi-core; with stride benchmarks in C, Go, and Rust showing 10x+ difference between stride-1 and stride-64

**Architecture**
- **Cache Mapping** — Direct-mapped vs N-way set-associative vs fully-associative, address decomposition bit diagrams
- **Write Policies** — write-through vs write-back vs write-combining, non-temporal stores
- **MESI Protocol** — the state machine that drives false sharing and cache coherence, with acquire/release memory ordering code

**Data & Algorithm Design**
- **AoS vs SoA vs AoSoA** — full N-body simulation in all three languages demonstrating real speedup
- **Cache-Friendly Algorithms** — blocked matrix multiply (tiling), Eytzinger binary search layout
- **False Sharing** — complete benchmark showing 5-10x penalty, padding solutions in all three languages
- **Prefetching** — hardware limits (can't predict pointer chasing), software prefetch for linked list traversal
- **Advanced Patterns** — cache-oblivious algorithms, non-temporal streaming writes, arena B-tree with integer indices

**Linux Kernel**
- **Slab/SLUB Allocator** — cache coloring, per-CPU magazines, `slabtop` commands
- **Page Cache** — `mmap` vs `read()` vs `O_DIRECT`, `posix_fadvise`, `MADV_SEQUENTIAL/HUGEPAGE/WILLNEED`
- **TLB & Huge Pages** — full math showing 2MB pages reduce TLB entries by 512x, `mmap(MAP_HUGETLB)` in C and Rust
- **NUMA** — socket topology, `numactl`, `move_pages()`, remote vs local access latency
- **Kernel Parameters** — `vm.swappiness`, `dirty_ratio`, THP, NUMA balancing, all `perf` cache events

**Tooling**
- **perf** — `perf stat`, `perf mem`, `perf c2c` (false sharing detection), `perf record` + annotate
- **Cachegrind, likwid, vtune** — full command references
- **PGO** — step-by-step for GCC, Clang, and Rust

**Production Patterns**
- Robin Hood open-addressing hash map (Go)
- Lock-free SPSC ring buffer with false-sharing-safe head/tail (Rust)
- Pool allocator with LIFO free-list (C) and arena allocator (Rust)