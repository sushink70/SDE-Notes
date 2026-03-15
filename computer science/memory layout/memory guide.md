# The Complete Memory Mastery Guide
### A World-Class Reference for Systems Programmers

> *"To master memory is to master the machine. Everything else is abstraction."*

---

## TABLE OF CONTENTS

1. [The Nature of Memory — What Is It Really?](#1-the-nature-of-memory)
2. [Memory Hierarchy — The Speed-Size Tradeoff](#2-memory-hierarchy)
3. [How a Process Sees Memory — Virtual Address Space](#3-virtual-address-space)
4. [The Stack — Deep Dive](#4-the-stack)
5. [The Heap — Deep Dive](#5-the-heap)
6. [Pointers and Addresses — The Raw Truth](#6-pointers-and-addresses)
7. [Manual Memory Management in C](#7-manual-memory-management-c)
8. [Memory Ownership — Rust's Model](#8-memory-ownership-rust)
9. [Garbage Collection — Go's Model](#9-garbage-collection-go)
10. [Memory Allocators — How malloc Actually Works](#10-memory-allocators)
11. [Virtual Memory, Paging, and the OS Role](#11-virtual-memory-and-paging)
12. [CPU Cache and Memory Locality](#12-cpu-cache-and-locality)
13. [Memory Alignment and Struct Padding](#13-memory-alignment-and-padding)
14. [Memory Safety — Bugs, Exploits, and Prevention](#14-memory-safety)
15. [Advanced Allocation — Arenas, Pools, Slabs](#15-advanced-allocators)
16. [Concurrency and Memory — Ordering, Atomics, Fences](#16-concurrency-and-memory)
17. [NUMA — Non-Uniform Memory Access](#17-numa)
18. [Memory Profiling and Debugging](#18-profiling-and-debugging)
19. [Memory in Real Systems — Case Studies](#19-real-world-case-studies)
20. [Mental Models and Expert Intuition](#20-mental-models)

---

## 1. The Nature of Memory

### What Memory Actually Is

At the physical level, memory is a grid of capacitors (DRAM) or flip-flops (SRAM). Each cell holds one bit — a charge or no charge, a 1 or 0. Everything above this — variables, objects, strings, functions — is a human-imposed abstraction built on top of raw bytes.

**The fundamental truth:** Memory is just a long, flat array of bytes. Your CPU and OS build the illusion of "structured data" on top of it.

```
Physical DRAM Layout (conceptual):
Address:  0x0000  0x0001  0x0002  0x0003  0x0004  ...
Value:    [0xFF]  [0x3A]  [0x00]  [0x01]  [0xC4]  ...
```

Every variable, every struct, every object is just a contiguous sequence of bytes at some address. The *type system* is how we tell the compiler how to interpret those bytes.

### The Three Fundamental Questions About Any Memory Location

When reasoning about memory as an expert, always ask:
1. **Where** is this data stored? (Stack, Heap, Static, Register)
2. **Who owns** this data? (Who is responsible for freeing it)
3. **How long** does this data live? (Lifetime / scope)

These three questions drive every memory decision. Internalise them.

### Bits, Bytes, and Words

| Unit | Size | Notes |
|------|------|-------|
| Bit | 1 bit | Smallest addressable unit conceptually |
| Byte | 8 bits | Smallest individually addressable unit on modern CPUs |
| Word | Platform-dependent | Native integer size: 32-bit on x86, 64-bit on x86-64 |
| Cache Line | 64 bytes (typical) | Unit of transfer between RAM and L1 cache |
| Page | 4096 bytes (typical) | Unit of transfer between disk and RAM |

**Why does this matter?** Because the CPU cannot read one byte from RAM — it reads a full cache line (64 bytes). This is why data locality matters profoundly for performance.

### Real-World Analogy: The Library System

Think of the memory hierarchy as a library system:

- **Registers** = The book currently open on your desk. Zero travel time. Only 1-2 books fit.
- **L1/L2/L3 Cache** = Shelves behind you in your private office. A few seconds to grab.
- **RAM** = The main library floor. A minute to walk there.
- **SSD/Disk** = Offsite warehouse. An hour to retrieve.
- **Network** = A different country's library. Days.

The performance difference between these levels is not 2x or 10x — it is **thousands to millions times** slower as you go down. This is why cache misses devastate performance.

---

## 2. Memory Hierarchy

### The Hierarchy in Detail

```
                    ┌──────────────────┐
                    │    REGISTERS     │  ~0.3 ns  |  ~1 KB
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   L1 CACHE       │  ~1 ns    |  32–64 KB
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   L2 CACHE       │  ~4 ns    |  256 KB – 1 MB
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   L3 CACHE       │  ~10 ns   |  8–64 MB (shared)
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   MAIN RAM       │  ~100 ns  |  4 GB – TBs
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   SSD/NVME       │  ~100 µs  |  Hundreds of GBs
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  HDD / NETWORK   │  ~10 ms+  |  Unlimited
                    └──────────────────┘
```

### Registers

Registers are the CPU's internal storage. They have no address in the traditional sense — they are referenced by name (rax, rbx, rsp, rip on x86-64). A 64-bit CPU has 16 general-purpose registers plus many special-purpose ones.

The compiler's register allocator decides which variables live in registers vs. being spilled to the stack. This is one of the key jobs of an optimising compiler.

```c
// In C, the register hint (mostly ignored by modern compilers):
register int x = 5;

// Modern compilers make better register allocation decisions than you,
// but you can help by keeping hot variables in small, tight scopes.
```

### Cache Architecture

Each CPU core typically has its own L1 and L2 cache. L3 is usually shared across cores.

**Cache Line:** The fundamental unit. When you read 1 byte from RAM, 64 bytes come into cache. If you read the next byte immediately after, it's already in cache — free.

**Cache Associativity:** Not every memory address can go in every cache slot. N-way set-associative caches are a compromise between fully associative (expensive) and direct-mapped (conflict-prone).

**Write Policies:**
- **Write-through**: Every write goes to both cache and RAM immediately.
- **Write-back**: Writes go to cache only; RAM is updated when the cache line is evicted.

### Why This Changes How You Code

```c
// Example: Row-major vs Column-major traversal
// Matrix is stored row-by-row in memory (row-major in C)

#define N 1024
int matrix[N][N];

// FAST: Row-major traversal - sequential memory access, cache-friendly
for (int i = 0; i < N; i++)
    for (int j = 0; j < N; j++)
        matrix[i][j]++;  // Access pattern: [0][0],[0][1],[0][2]...

// SLOW: Column-major traversal - strided access, cache-hostile
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++)
        matrix[i][j]++;  // Access pattern: [0][0],[1][0],[2][0]...
// Each access is 1024 * 4 = 4096 bytes apart — every access is a cache miss!
```

On a modern CPU, this difference can be **50-100x** in real performance.

---

## 3. Virtual Address Space

### The Great Illusion

Every modern process believes it owns the **entire address space** — 0x0000000000000000 to 0xFFFFFFFFFFFFFFFF on 64-bit systems. This is the virtual address space. The OS and CPU work together (via the MMU — Memory Management Unit) to map virtual addresses to physical RAM.

This illusion provides:
1. **Isolation** — Process A cannot read Process B's memory
2. **Simplicity** — Programs don't need to know where in RAM they are
3. **Virtual memory** — More virtual address space than physical RAM

### Process Memory Layout

```
High Addresses (0xFFFFFFFFFFFFFFFF)
┌──────────────────────────────────────┐
│          KERNEL SPACE                │  ← OS kernel lives here
│   (inaccessible from user space)    │
├──────────────────────────────────────┤  0xFFFF800000000000 (approx)
│                                      │
│          STACK                       │  ← Grows DOWN ↓
│    (local variables, call frames)   │
│              ↓                       │
│         [GUARD PAGE]                │  ← Causes segfault if hit
│                                      │
│          (unmapped gap)              │
│                                      │
│              ↑                       │
│    MEMORY MAPPED FILES / mmap()     │  ← Shared libs, file-backed pages
│    (also: thread stacks live here)  │
│                                      │
│              ↑                       │
│          HEAP                        │  ← Grows UP ↑
│    (dynamic allocations)            │
│                                      │
├──────────────────────────────────────┤  ← brk / sbrk boundary
│          BSS SEGMENT                 │  ← Uninitialised global/static vars (zeroed by OS)
├──────────────────────────────────────┤
│          DATA SEGMENT                │  ← Initialised global/static vars
├──────────────────────────────────────┤
│          TEXT SEGMENT                │  ← Executable code (read-only)
│          (CODE)                      │
└──────────────────────────────────────┘
Low Addresses (0x0000000000000000)
```

### Inspecting This in Practice

```bash
# On Linux, inspect any process's memory map:
cat /proc/self/maps

# Or for a specific PID:
cat /proc/1234/maps

# Output looks like:
# 55a3f1e2a000-55a3f1e2b000 r--p 00000000 08:01 1234  /usr/bin/cat
# 55a3f1e2b000-55a3f1e2c000 r-xp 00001000 08:01 1234  /usr/bin/cat
# 7f8ab2c00000-7f8ab2e00000 rw-p 00000000 00:00 0     [heap]
# 7ffe3a800000-7ffe3a821000 rw-p 00000000 00:00 0     [stack]
```

```c
// In C: Print addresses of different segment types
#include <stdio.h>
#include <stdlib.h>

int global_init = 42;           // DATA segment
int global_uninit;              // BSS segment
static int static_var = 10;    // DATA segment

int main() {
    int local = 5;              // STACK
    int *heap_var = malloc(4);  // HEAP
    
    printf("Code  (TEXT):  %p\n", (void*)main);
    printf("Global init:   %p\n", (void*)&global_init);
    printf("Global uninit: %p\n", (void*)&global_uninit);
    printf("Static:        %p\n", (void*)&static_var);
    printf("Local (stack): %p\n", (void*)&local);
    printf("Heap:          %p\n", (void*)heap_var);
    
    free(heap_var);
    return 0;
}
```

You will see addresses in completely different regions, confirming the segment layout above.

### Segment Permissions

Each segment has read/write/execute permissions enforced by the MMU:

| Segment | Read | Write | Execute | Notes |
|---------|------|-------|---------|-------|
| TEXT (code) | ✅ | ❌ | ✅ | Prevents code modification |
| DATA | ✅ | ✅ | ❌ | Prevents data execution |
| BSS | ✅ | ✅ | ❌ | Same as DATA |
| HEAP | ✅ | ✅ | ❌ | DEP protection |
| STACK | ✅ | ✅ | ❌ | DEP/NX protection |

**NX (No-Execute) bit** / **DEP (Data Execution Prevention)**: This hardware feature prevents code injection attacks where an attacker injects shellcode into a buffer and then executes it — the hardware won't allow it because the stack/heap is not executable.

---

## 4. The Stack

### What the Stack Actually Is

The stack is a **contiguous region of memory** managed automatically by the CPU using two registers:
- **RSP** (Stack Pointer): Points to the current top of the stack
- **RBP** (Base Pointer / Frame Pointer): Points to the base of the current stack frame

The stack grows **downward** — when you push something, RSP decrements. When you pop, RSP increments. This is a hardware convention, not a software choice.

```
High Memory (stack base)
┌─────────────────────┐ ← RSP + N (before any function call)
│  main() frame       │
│  int x = 10        │
│  int y = 20        │
├─────────────────────┤ ← old RBP stored here
│  foo() frame        │
│  return address    │ ← where to jump when foo() returns
│  int a = 5         │
│  int b = 7         │
├─────────────────────┤
│  bar() frame        │
│  return address    │
│  char buf[256]     │ ← 256 bytes allocated on stack
│                     │
│         ↓           │
│                     │ ← RSP (current top)
Low Memory
```

### Stack Frame Anatomy (x86-64 Calling Convention)

When a function is called, the CPU executes this sequence:
1. Caller pushes arguments (or puts them in registers: rdi, rsi, rdx, rcx, r8, r9)
2. Caller executes `CALL` — which pushes return address and jumps
3. Callee pushes old RBP (`push rbp`)
4. Callee sets RBP = RSP (`mov rbp, rsp`)
5. Callee subtracts from RSP to allocate locals (`sub rsp, N`)

On return:
1. Callee restores RSP from RBP (`mov rsp, rbp`)
2. Callee pops old RBP (`pop rbp`)
3. Callee executes `RET` — pops return address and jumps

```c
// This C code:
int add(int a, int b) {
    int result = a + b;  // local variable on stack
    return result;
}

// Compiles to approximately (x86-64):
// add:
//   push rbp
//   mov  rbp, rsp
//   sub  rsp, 16        ; allocate space for 'result'
//   mov  DWORD PTR [rbp-4], edi    ; store 'a'
//   mov  DWORD PTR [rbp-8], esi    ; store 'b'
//   mov  eax, DWORD PTR [rbp-4]
//   add  eax, DWORD PTR [rbp-8]
//   mov  DWORD PTR [rbp-12], eax   ; store 'result'
//   mov  eax, DWORD PTR [rbp-12]
//   leave                           ; mov rsp, rbp; pop rbp
//   ret
```

### Stack in C

```c
#include <stdio.h>
#include <stdint.h>

void show_stack_growth() {
    int a = 1;
    int b = 2;
    int c = 3;
    
    // On most systems, stack grows down:
    printf("&a = %p\n", (void*)&a);
    printf("&b = %p\n", (void*)&b);  // lower address than &a
    printf("&c = %p\n", (void*)&c);  // lower address than &b
    
    // Difference:
    printf("&a - &b = %td bytes\n", (uintptr_t)&a - (uintptr_t)&b);
}

// Variable-Length Arrays (VLAs) — runtime-determined stack allocation
// Dangerous for large n — can overflow stack silently
void vla_example(int n) {
    int arr[n];  // Allocated on stack at runtime (C99)
    // Stack pointer decremented by n*sizeof(int)
    // No bounds checking. Stack overflow if n is too large.
    for (int i = 0; i < n; i++) arr[i] = i;
}
```

### Stack in Rust

```rust
fn stack_demo() {
    // All of these live on the stack:
    let x: i32 = 10;          // 4 bytes on stack
    let arr: [i32; 5] = [1,2,3,4,5]; // 20 bytes on stack
    let tuple: (i64, f64) = (1, 2.0); // 16 bytes on stack
    
    // Rust knows sizes at compile time (Sized trait)
    // Stack allocation is just RSP arithmetic — zero overhead
    println!("x at: {:p}", &x);
    println!("arr at: {:p}", &arr);
}

// Box<T> moves data from stack to heap:
fn heap_vs_stack() {
    let stack_val: i32 = 42;          // Stack
    let heap_val: Box<i32> = Box::new(42); // Pointer on stack, data on heap
    
    // Box is just a smart pointer. It's 8 bytes (pointer size) on the stack.
    // The i32 lives on the heap.
    println!("Stack pointer: {:p}", &stack_val);
    println!("Box pointer:   {:p}", &heap_val);   // address of the Box itself
    println!("Box content:   {:p}", heap_val.as_ref()); // address of the heap data
}
```

### Stack in Go

```go
package main

import (
    "fmt"
    "runtime"
)

func stackDemo() {
    x := 42
    arr := [5]int{1, 2, 3, 4, 5}
    fmt.Printf("x at: %p\n", &x)
    fmt.Printf("arr at: %p\n", &arr)
    
    // Go's stack starts small (2-8 KB) and GROWS dynamically
    // This is called "stack segmentation" or "goroutine stacks"
    // Go 1.4+ uses contiguous stacks with copying when growth needed
}

// Goroutine stacks — Go's killer feature for concurrency
func goroutineStackGrowth() {
    // Each goroutine starts with ~2-8 KB stack (not OS threads' 8MB!)
    // Go's runtime grows the stack automatically as needed
    // This allows millions of goroutines concurrently
    
    for i := 0; i < 100000; i++ {
        go func() {
            var buf [128]byte // tiny stack allocation per goroutine
            _ = buf
            runtime.Gosched()
        }()
    }
}
```

### Stack Overflow — The Real Danger

```c
// Classic stack overflow via infinite recursion:
void infinite() {
    char buf[1024];  // Each call consumes 1024+ bytes of stack
    infinite();      // Stack overflow after ~8000 calls on a system with 8MB stack
}

// More subtle: deep recursion with large locals
long factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);  // n=100000 will overflow typical stack
}

// Solution: Tail recursion (compiler can optimise to iteration)
long factorial_tail(int n, long acc) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc);  // Tail call — no new frame needed
}
// Or simply: use iteration for deep recursion
```

**Key Stack Properties:**
- **Fixed maximum size** (typically 1-8 MB per thread on Linux)
- **O(1) allocation/deallocation** — just RSP arithmetic
- **Automatic lifetime** — freed when function returns
- **No fragmentation** — LIFO order guarantees contiguity
- **Cache-friendly** — recently-used data is always nearby
- **Not suitable for large data** — limited size, no dynamic growth (except Go)

---

## 5. The Heap

### What the Heap Actually Is

The heap is a region of memory that the OS reserves for **dynamic allocation** — memory whose size or lifetime isn't known at compile time. Unlike the stack, heap memory has:
- **No automatic lifetime** — you control when it's freed
- **Arbitrary size** — limited only by available RAM (and virtual address space)
- **Random access patterns** — can lead to fragmentation

The "heap" name is misleading — it has nothing to do with the heap data structure. It's just the region of memory managed by the allocator.

### The Heap Abstraction Layers

```
Your Code (malloc/Box::new/make/new)
         ↓
   Memory Allocator (jemalloc/tcmalloc/mimalloc/Go runtime)
         ↓
   OS System Calls (brk/sbrk/mmap on Linux)
         ↓
   Physical Memory Manager (page frames, physical RAM)
```

### How the Heap Grows

On Linux, the heap starts just above the BSS segment. Two system calls manage its extent:

```c
// brk() — sets the end of the heap (program break)
// sbrk() — increments the program break by a delta

#include <unistd.h>

void manual_heap_demo() {
    void *start = sbrk(0);   // Current program break
    void *block = sbrk(4096); // Request 4096 more bytes from OS
    
    // Now [start, start+4096) is available raw memory
    // malloc() manages this for you — don't call sbrk() directly!
    
    // Large allocations (>128KB typically) use mmap() instead of brk()
    // mmap gives a completely separate mapping, not contiguous with heap
}
```

### Heap in C (Manual Management)

```c
#include <stdlib.h>
#include <string.h>

// malloc: allocate uninitialized memory
int *arr = malloc(10 * sizeof(int)); // 40 bytes, content undefined
if (!arr) { /* handle OOM */ }

// calloc: allocate zero-initialized memory
int *zero_arr = calloc(10, sizeof(int)); // 40 bytes, all zeros

// realloc: resize allocation
arr = realloc(arr, 20 * sizeof(int)); // Grow to 80 bytes
// realloc may return a NEW pointer — old pointer may be invalid!

// free: release memory back to allocator
free(arr);
arr = NULL; // CRITICAL: zero the pointer after freeing
// Not zeroing it = dangling pointer = undefined behaviour

// sizeof a struct:
typedef struct {
    int id;
    double value;
    char name[32];
} Record;

Record *r = malloc(sizeof(Record)); // sizeof knows the size at compile time
r->id = 1;
r->value = 3.14;
strncpy(r->name, "hello", 31);
free(r);
```

### Heap in Rust

```rust
use std::alloc::{alloc, dealloc, Layout};

fn heap_in_rust() {
    // Box<T> — simplest heap allocation
    let x: Box<i32> = Box::new(42);
    // When x goes out of scope, Box's Drop impl calls dealloc automatically
    
    // Vec<T> — growable heap array
    let mut v: Vec<i32> = Vec::new();
    v.push(1); v.push(2); v.push(3);
    // Vec stores: (pointer to heap buffer, length, capacity)
    // That's 3 words (24 bytes) on the stack; data is on the heap
    
    println!("Vec ptr:  {:p}", v.as_ptr());    // heap address
    println!("Vec len:  {}", v.len());
    println!("Vec cap:  {}", v.capacity());
    
    // String — heap-allocated UTF-8 string
    let s = String::from("hello");
    // Same layout as Vec<u8>: ptr + len + cap
    
    // Raw allocation (unsafe) — when you need to bypass abstractions
    unsafe {
        let layout = Layout::array::<i32>(10).unwrap();
        let ptr = alloc(layout) as *mut i32;
        
        for i in 0..10 {
            ptr.add(i).write(i as i32);
        }
        
        // Must manually deallocate
        dealloc(ptr as *mut u8, layout);
    }
}

// Rust's ownership system ensures: EVERY heap allocation is freed
// exactly once. No GC needed. No runtime cost. Checked at compile time.
fn ownership_example() {
    let b = Box::new(100); // allocated
    {
        let c = b; // ownership transferred to c
        // b is no longer valid — compiler enforces this
        println!("{}", c);
    } // c goes out of scope → Drop is called → memory freed
    // 'b' is gone, 'c' is gone — perfect.
}
```

### Heap in Go

```go
package main

import "fmt"

func heapInGo() {
    // Go hides the stack/heap distinction from you deliberately
    // The compiler decides based on escape analysis
    
    // This may or may not go to heap depending on escape analysis:
    x := 42
    _ = x
    
    // This WILL go to heap — pointer escapes the function:
    p := newInt(42)
    fmt.Println(*p) // GC will clean this up
    
    // Slices — header on stack, backing array on heap:
    s := make([]int, 10, 20)
    // Stack: SliceHeader{ptr, len=10, cap=20}  (24 bytes)
    // Heap: backing array of 20 ints (160 bytes)
    fmt.Printf("slice header: %p\n", &s)
    fmt.Printf("backing array: %p\n", &s[0])
    
    // Maps — always on heap
    m := make(map[string]int)
    m["a"] = 1
    _ = m
}

func newInt(n int) *int {
    // 'n' is a local variable. Taking its address causes it to ESCAPE to heap.
    // The compiler detects this via escape analysis.
    return &n
}
```

### Escape Analysis (Go)

```go
// Run: go build -gcflags="-m" to see escape analysis decisions

package main

import "fmt"

func doesNotEscape() int {
    x := 42  // stays on stack
    return x  // value copy, no escape
}

func doesEscape() *int {
    x := 42    // escapes to heap because pointer is returned
    return &x
}

func interfaceEscape() {
    x := 42
    var i interface{} = x  // x may escape if interface is passed to functions
    fmt.Println(i)
}
```

### Stack vs Heap — The Expert's Decision Matrix

| Factor | Stack | Heap |
|--------|-------|------|
| Allocation speed | O(1) — RSP arithmetic | O(1) amortised (but more expensive) |
| Deallocation | Automatic (function return) | Manual/GC/Drop |
| Size limit | ~1-8 MB (fixed) | Limited by RAM |
| Lifetime | Tied to scope | Flexible |
| Fragmentation | None | Possible |
| Cache behaviour | Excellent | Variable |
| Concurrency | Per-thread, no sharing | Shared, needs synchronisation |
| Compile-time size | Required | Not required |

**Expert Rule:** Prefer stack allocation. Use heap only when you need one of: dynamic size, long lifetime, large data, or sharing across threads/scopes.

---

## 6. Pointers and Addresses

### The Raw Truth About Pointers

A pointer is simply an integer that holds a memory address. On a 64-bit system, every pointer is 8 bytes. That's it. The type attached to a pointer (e.g., `int*`) is entirely a compiler construct — it tells the compiler how many bytes to read/write when dereferencing, and what pointer arithmetic to do.

```c
// In C, pointers are explicit and raw:
int x = 42;
int *p = &x;  // p holds the address of x

// Dereferencing: read the int at address p
int val = *p;  // val == 42

// Pointer arithmetic: add sizeof(int) bytes to the address
int arr[5] = {10, 20, 30, 40, 50};
int *q = arr;      // points to arr[0]
int *r = q + 2;    // points to arr[2] (advances by 2 * sizeof(int) = 8 bytes)
printf("%d\n", *r); // 30

// Cast: view the same memory through a different type
// This is legal but dangerous — you must know what you're doing
unsigned char *bytes = (unsigned char *)&x;
for (int i = 0; i < sizeof(int); i++) {
    printf("byte[%d] = 0x%02X\n", i, bytes[i]);
}
// On little-endian x86: byte[0]=0x2A, byte[1]=0x00, byte[2]=0x00, byte[3]=0x00
// 0x2A = 42 in decimal
```

### Pointer Sizes and Indirection Levels

```c
int x = 42;
int *p = &x;       // pointer to int
int **pp = &p;     // pointer to pointer to int
int ***ppp = &pp;  // pointer to pointer to pointer to int

// Dereferencing levels:
printf("%d\n", x);      // 42
printf("%d\n", *p);     // 42 — one dereference
printf("%d\n", **pp);   // 42 — two dereferences
printf("%d\n", ***ppp); // 42 — three dereferences
```

### Function Pointers

```c
// A function pointer holds the address of machine code:
int add(int a, int b) { return a + b; }
int mul(int a, int b) { return a * b; }

// Declare a function pointer:
int (*op)(int, int);

op = add;
printf("%d\n", op(3, 4)); // 7

op = mul;
printf("%d\n", op(3, 4)); // 12

// Array of function pointers (vtable pattern):
int (*ops[])(int, int) = {add, mul};
printf("%d\n", ops[0](3, 4)); // 7
printf("%d\n", ops[1](3, 4)); // 12
```

### Pointers in Rust

```rust
// Rust has multiple pointer types with different safety guarantees:

fn rust_pointer_types() {
    let x = 42i32;
    
    // 1. References — safe, checked at compile time:
    let r: &i32 = &x;       // immutable reference
    let mut y = 42i32;
    let m: &mut i32 = &mut y; // mutable reference (exclusive)
    *m = 100;
    
    // 2. Raw pointers — unsafe, no borrow checking:
    let raw_const: *const i32 = &x;
    let raw_mut: *mut i32 = &mut y;
    
    unsafe {
        println!("raw: {}", *raw_const);  // must be in unsafe block
        *raw_mut = 200;
    }
    
    // 3. Smart pointers — ownership semantics:
    let boxed: Box<i32> = Box::new(42);         // unique ownership
    let rc: std::rc::Rc<i32> = std::rc::Rc::new(42);  // shared ownership (single-thread)
    let arc: std::sync::Arc<i32> = std::sync::Arc::new(42); // shared ownership (multi-thread)
    
    // Pointer arithmetic (unsafe):
    let arr = [1i32, 2, 3, 4, 5];
    let p: *const i32 = arr.as_ptr();
    unsafe {
        let third = p.add(2); // advance by 2 * sizeof(i32) bytes
        println!("third element: {}", *third); // 3
    }
}
```

### Pointers in Go

```go
package main

import "fmt"

func goPointers() {
    x := 42
    
    // & operator: take address
    p := &x
    
    // * operator: dereference
    fmt.Println(*p) // 42
    
    // Modify through pointer:
    *p = 100
    fmt.Println(x)  // 100
    
    // new() allocates on heap and returns a pointer:
    q := new(int) // *int pointing to zero-initialized int on heap
    *q = 55
    fmt.Println(*q)
    
    // No pointer arithmetic in Go — type safety is enforced
    // use unsafe.Pointer for raw pointer operations
    
    // Go pointers are safe: no dangling pointers (GC ensures referenced objects live)
    // No pointer arithmetic (prevents buffer overflows via pointers)
    // nil pointer dereference panics (recoverable) instead of undefined behaviour
}

// nil pointer:
func nilPointerDemo() {
    var p *int // zero value for *int is nil
    if p == nil {
        fmt.Println("p is nil")
        // *p would panic here — safe failure
    }
}
```

### Endianness — How Multi-Byte Values Are Stored

```c
#include <stdio.h>
#include <stdint.h>

void endianness_demo() {
    uint32_t value = 0x01020304;
    unsigned char *bytes = (unsigned char *)&value;
    
    // Little-endian (x86, ARM, most modern): least significant byte first
    // memory layout: [0x04][0x03][0x02][0x01]
    
    // Big-endian (network byte order, some older architectures): MSB first
    // memory layout: [0x01][0x02][0x03][0x04]
    
    printf("byte[0] = 0x%02X\n", bytes[0]); // 0x04 on little-endian
    printf("byte[1] = 0x%02X\n", bytes[1]); // 0x03
    printf("byte[2] = 0x%02X\n", bytes[2]); // 0x02
    printf("byte[3] = 0x%02X\n", bytes[3]); // 0x01
    
    // Check endianness:
    if (bytes[0] == 0x04) printf("Little-endian system\n");
    else printf("Big-endian system\n");
}

// Why this matters: network protocols use big-endian ("network byte order")
// htons(), htonl(), ntohs(), ntohl() convert between host and network order
```

---

## 7. Manual Memory Management in C

### The Contract of malloc/free

The fundamental contract is simple but requires perfect discipline:
- **Every `malloc`** must be matched with exactly **one `free`**
- **Never** free twice (double-free)
- **Never** use memory after freeing it (use-after-free)
- **Never** access beyond the allocated region (buffer overflow)

Breaking any of these rules is **undefined behaviour** — the program may crash, corrupt data, or appear to work correctly (the worst outcome).

### Complete Memory Management Patterns in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

//─────────────────────────────────────────────────────
// Pattern 1: Basic allocation with error handling
//─────────────────────────────────────────────────────
int *create_array(size_t n) {
    if (n == 0 || n > SIZE_MAX / sizeof(int)) {
        return NULL; // Prevent integer overflow in size calculation
    }
    
    int *arr = malloc(n * sizeof(int));
    if (!arr) {
        fprintf(stderr, "malloc failed: %s\n", strerror(errno));
        return NULL;
    }
    
    memset(arr, 0, n * sizeof(int)); // Explicitly zero if needed
    return arr;
}

void destroy_array(int **arr) {
    if (arr && *arr) {
        free(*arr);
        *arr = NULL; // Zero the caller's pointer — prevents dangling pointer use
    }
}

//─────────────────────────────────────────────────────
// Pattern 2: Struct with owned memory (RAII pattern in C)
//─────────────────────────────────────────────────────
typedef struct {
    char *data;
    size_t length;
    size_t capacity;
} String;

String string_new(const char *initial) {
    size_t len = strlen(initial);
    String s;
    s.length = len;
    s.capacity = len + 1;
    s.data = malloc(s.capacity);
    if (!s.data) {
        s.length = s.capacity = 0;
        return s;
    }
    memcpy(s.data, initial, s.capacity);
    return s;
}

int string_append(String *s, const char *suffix) {
    size_t slen = strlen(suffix);
    size_t new_len = s->length + slen;
    
    if (new_len + 1 > s->capacity) {
        size_t new_cap = (new_len + 1) * 2; // 2x growth factor
        char *new_data = realloc(s->data, new_cap);
        if (!new_data) return -1; // Original s->data still valid on realloc failure
        s->data = new_data;
        s->capacity = new_cap;
    }
    
    memcpy(s->data + s->length, suffix, slen + 1);
    s->length = new_len;
    return 0;
}

void string_free(String *s) {
    free(s->data);
    s->data = NULL;
    s->length = s->capacity = 0;
}

//─────────────────────────────────────────────────────
// Pattern 3: Dynamic array (vector)
//─────────────────────────────────────────────────────
typedef struct {
    void *data;
    size_t elem_size;
    size_t length;
    size_t capacity;
} Vector;

Vector vec_new(size_t elem_size, size_t initial_cap) {
    Vector v;
    v.elem_size = elem_size;
    v.length = 0;
    v.capacity = initial_cap > 0 ? initial_cap : 4;
    v.data = malloc(v.capacity * elem_size);
    if (!v.data) v.capacity = 0;
    return v;
}

int vec_push(Vector *v, const void *elem) {
    if (v->length == v->capacity) {
        size_t new_cap = v->capacity * 2;
        void *new_data = realloc(v->data, new_cap * v->elem_size);
        if (!new_data) return -1;
        v->data = new_data;
        v->capacity = new_cap;
    }
    memcpy((char*)v->data + v->length * v->elem_size, elem, v->elem_size);
    v->length++;
    return 0;
}

void *vec_get(const Vector *v, size_t i) {
    if (i >= v->length) return NULL;
    return (char*)v->data + i * v->elem_size;
}

void vec_free(Vector *v) {
    free(v->data);
    v->data = NULL;
    v->length = v->capacity = 0;
}

//─────────────────────────────────────────────────────
// Usage example
//─────────────────────────────────────────────────────
int main() {
    // Array pattern
    int *arr = create_array(100);
    for (int i = 0; i < 100; i++) arr[i] = i * i;
    destroy_array(&arr); // arr is now NULL
    
    // String pattern
    String s = string_new("Hello");
    string_append(&s, ", World!");
    printf("%s\n", s.data); // Hello, World!
    string_free(&s);
    
    // Vector pattern
    Vector v = vec_new(sizeof(int), 4);
    for (int i = 0; i < 10; i++) vec_push(&v, &i);
    int *elem = vec_get(&v, 5);
    if (elem) printf("v[5] = %d\n", *elem); // 5
    vec_free(&v);
    
    return 0;
}
```

### Common C Memory Bugs — Illustrated

```c
// Bug 1: Memory Leak — allocated but never freed
void leak() {
    int *p = malloc(100);
    p[0] = 1;
    return; // leaked! malloc'd memory never freed
}

// Bug 2: Double Free — undefined behaviour
void double_free() {
    int *p = malloc(4);
    free(p);
    free(p); // UNDEFINED BEHAVIOUR — may corrupt allocator state
}

// Bug 3: Use After Free — undefined behaviour
void use_after_free() {
    int *p = malloc(sizeof(int));
    *p = 42;
    free(p);
    printf("%d\n", *p); // UNDEFINED BEHAVIOUR — memory may have been reused
}

// Bug 4: Buffer Overflow
void buffer_overflow() {
    int arr[5];
    arr[10] = 99; // writes to memory outside the array — corrupts neighbouring data
}

// Bug 5: Stack Buffer Overflow (common vulnerability)
void gets_danger(void) {
    char buf[32];
    gets(buf); // NO length limit — attacker can overwrite return address!
    // Use fgets(buf, sizeof(buf), stdin) instead
}

// Bug 6: Uninitialized Read
void uninit_read() {
    int x;           // uninitialized — value is whatever was on the stack before
    printf("%d\n", x); // UNDEFINED BEHAVIOUR — reads garbage
}

// Bug 7: Returning address of local variable
int* return_local() {
    int x = 42;
    return &x; // UNDEFINED BEHAVIOUR — x is on the stack and will be invalid after return
}

// Bug 8: Integer overflow in size calculation
void size_overflow(size_t n) {
    // If n is very large, n * sizeof(int) overflows size_t
    int *arr = malloc(n * sizeof(int)); // Potential overflow!
    // Safe version:
    if (n > SIZE_MAX / sizeof(int)) { /* error */ return; }
    arr = malloc(n * sizeof(int));
    free(arr);
}
```

---

## 8. Memory Ownership — Rust's Model

### The Core Innovation

Rust's ownership system eliminates the entire class of memory safety bugs without a garbage collector. It does this through three rules enforced at **compile time**:

1. **Each value has exactly one owner**
2. **When the owner goes out of scope, the value is dropped**
3. **There can be either one mutable reference OR any number of immutable references — never both simultaneously**

This is enforced by the **borrow checker** — a compile-time analysis pass. There is zero runtime cost.

### Ownership in Practice

```rust
fn ownership_fundamentals() {
    // Rule 1: One owner
    let s1 = String::from("hello"); // s1 owns the heap-allocated string
    let s2 = s1;                    // MOVE: s1 transfers ownership to s2
    // println!("{}", s1);          // COMPILE ERROR: s1 is no longer valid
    println!("{}", s2);             // OK
    
    // Clone: explicit deep copy
    let s3 = s2.clone(); // s2 still valid; s3 owns a new copy
    println!("{} {}", s2, s3);
    
    // Copy types (stack-only, trivially copyable):
    let x = 5;    // i32 implements Copy
    let y = x;    // COPY: x is still valid (no heap involved)
    println!("{} {}", x, y); // both valid
    
} // s2, s3 dropped here; their heap memory freed automatically

// Ownership through functions:
fn takes_ownership(s: String) {
    println!("{}", s);
} // s dropped here

fn gives_ownership() -> String {
    String::from("hello") // ownership transferred to caller
}

fn demo() {
    let s = String::from("hello");
    takes_ownership(s);       // s moved into function
    // println!("{}", s);    // COMPILE ERROR: s was moved
    
    let s2 = gives_ownership(); // s2 owns the returned String
    println!("{}", s2);
}
```

### Borrowing — References Without Ownership Transfer

```rust
// &T — immutable borrow: can read, cannot modify
// &mut T — mutable borrow: can read and modify (exclusive)

fn borrowing() {
    let s = String::from("hello");
    
    // Immutable borrow:
    let len = calculate_length(&s); // lend s, don't move it
    println!("{} has {} chars", s, len); // s still valid here
    
    // Multiple immutable borrows OK:
    let r1 = &s;
    let r2 = &s;
    println!("{} {}", r1, r2); // fine
    
    // Mutable borrow:
    let mut ms = String::from("hello");
    let mr = &mut ms;
    mr.push_str(", world");
    // Can't use ms here — it's mutably borrowed
    println!("{}", mr); // fine
    // Now mr is no longer used:
    println!("{}", ms); // fine again
    
    // COMPILE ERROR: cannot have mutable AND immutable reference simultaneously
    // let r = &ms;
    // let mr = &mut ms;  // ERROR
    // println!("{} {}", r, mr);
}

fn calculate_length(s: &String) -> usize {
    s.len() // borrows s, doesn't own it
} // s is NOT dropped here (we don't own it)
```

### Lifetimes — When References Must Not Outlive Data

```rust
// Lifetimes ensure references are always valid
// They're annotations, not runtime constructs

// This won't compile — lifetime error:
// fn dangling() -> &String {
//     let s = String::from("hello");
//     &s  // ERROR: s is dropped at end of function, reference would dangle
// }

// Lifetime annotations tell the borrow checker how lifetimes relate:
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    // The returned reference lives at least as long as the shorter of x and y
    if x.len() > y.len() { x } else { y }
}

fn lifetime_demo() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xyz");
        result = longest(s1.as_str(), s2.as_str());
        println!("{}", result); // OK — s2 still alive here
    }
    // println!("{}", result); // ERROR — s2 dropped, result could point to s2
}

// Struct with reference — must annotate lifetime:
struct Important<'a> {
    part: &'a str,
}

impl<'a> Important<'a> {
    fn announce(&self) -> &str {
        self.part
    }
}
```

### Smart Pointers — Heap Ownership Patterns

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::sync::{Arc, Mutex};

fn smart_pointers() {
    // Box<T>: unique ownership, heap allocation
    let b = Box::new(5);
    println!("{}", b); // auto-deref

    // Rc<T>: shared ownership, single-threaded reference counting
    let a = Rc::new(vec![1, 2, 3]);
    let b = Rc::clone(&a); // increment reference count
    let c = Rc::clone(&a);
    println!("count = {}", Rc::strong_count(&a)); // 3
    // All three have access. Freed when last Rc drops.
    
    // RefCell<T>: interior mutability — borrow checking at runtime
    // Use when you NEED shared mutability (e.g., graph nodes)
    let shared = Rc::new(RefCell::new(vec![1, 2, 3]));
    let clone = Rc::clone(&shared);
    shared.borrow_mut().push(4);
    println!("{:?}", clone.borrow()); // [1, 2, 3, 4]
    
    // Arc<T>: shared ownership, thread-safe (atomic reference counting)
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    std::thread::spawn(move || {
        data_clone.lock().unwrap().push(4);
    }).join().unwrap();
    println!("{:?}", data.lock().unwrap()); // [1, 2, 3, 4]
}
```

### Memory Layout of Rust Types

```rust
use std::mem;

fn memory_layouts() {
    // Primitives:
    println!("bool:   {} byte",  mem::size_of::<bool>());   // 1
    println!("i32:    {} bytes", mem::size_of::<i32>());    // 4
    println!("i64:    {} bytes", mem::size_of::<i64>());    // 8
    println!("f64:    {} bytes", mem::size_of::<f64>());    // 8
    println!("char:   {} bytes", mem::size_of::<char>());   // 4 (Unicode scalar)
    
    // References and pointers: always pointer-sized (8 bytes on 64-bit)
    println!("&i32:   {} bytes", mem::size_of::<&i32>());   // 8
    println!("Box<i32>: {} bytes", mem::size_of::<Box<i32>>()); // 8
    
    // Fat pointers (pointer + metadata):
    println!("&[i32]: {} bytes", mem::size_of::<&[i32]>());  // 16 (ptr + len)
    println!("&str:   {} bytes", mem::size_of::<&str>());    // 16 (ptr + len)
    
    // Vec<T>: pointer + length + capacity
    println!("Vec<i32>: {} bytes", mem::size_of::<Vec<i32>>()); // 24
    
    // Option<T>: nullable type — zero cost with niche optimisation
    println!("Option<i32>:    {} bytes", mem::size_of::<Option<i32>>());  // 8
    println!("Option<Box<i32>>: {} bytes", mem::size_of::<Option<Box<i32>>>()); // 8! (null = None)
    
    // Structs:
    #[repr(C)]
    struct Compact { x: i32, y: i32 } // 8 bytes
    #[repr(C)]
    struct Padded { x: u8, y: i32 }   // 8 bytes (padded), not 5
    
    println!("Compact: {} bytes", mem::size_of::<Compact>()); // 8
    println!("Padded:  {} bytes", mem::size_of::<Padded>());  // 8 (with padding)
}
```

---

## 9. Garbage Collection — Go's Model

### What Garbage Collection Does

A garbage collector automatically reclaims heap memory that is no longer reachable. The programmer never calls `free()`. The GC periodically identifies objects with no live references and reclaims them.

Trade-offs:
- **Benefit**: No manual memory management, no dangling pointers, no double frees
- **Cost**: Stop-the-world pauses (however brief), throughput overhead, less predictable latency, less control over memory layout

### Go's Tricolor Mark-and-Sweep GC

Go uses a **concurrent, tricolor mark-and-sweep** GC with write barriers.

```
Phase 1: MARK (mostly concurrent)
─────────────────────────────────
Objects are coloured:
  WHITE = not yet visited (initially all objects)
  GREY  = discovered, children not yet scanned
  BLACK = fully scanned (both object and all its references)

Start: Root set (globals, goroutine stacks) → colour GREY

Loop:
  Pick a GREY object
  Colour all its WHITE children GREY
  Colour the object BLACK

End: All WHITE objects are unreachable → garbage

Phase 2: SWEEP (concurrent)
────────────────────────────
Walk through heap, free all WHITE objects
Reset for next cycle
```

**Write Barrier**: Ensures that if the GC is running concurrently and mutator (your code) writes a pointer, the GC doesn't miss objects. Go uses the Dijkstra/Yuasa hybrid write barrier.

### Go Memory Model — Key Concepts

```go
package main

import (
    "fmt"
    "runtime"
    "runtime/debug"
)

func gcDemo() {
    // Force GC to run:
    runtime.GC()
    
    // Print GC stats:
    var stats runtime.MemStats
    runtime.ReadMemStats(&stats)
    fmt.Printf("Alloc:      %v KB\n", stats.Alloc/1024)
    fmt.Printf("TotalAlloc: %v KB\n", stats.TotalAlloc/1024)
    fmt.Printf("Sys:        %v KB\n", stats.Sys/1024)
    fmt.Printf("NumGC:      %v\n", stats.NumGC)
    
    // GC tuning via GOGC environment variable (default 100):
    // GOGC=100 means GC triggers when heap doubles since last GC
    // GOGC=50 = more frequent GC, less memory used
    // GOGC=200 = less frequent GC, more memory used, less CPU
    // GOGC=off = disable GC (dangerous for long-running programs)
    
    // Programmatic GC control:
    debug.SetGCPercent(200) // equivalent to GOGC=200
    
    // Soft memory limit (Go 1.19+):
    debug.SetMemoryLimit(512 * 1024 * 1024) // 512 MB
}

// Reducing GC pressure — expert techniques:

// 1. Sync pools for frequently allocated/freed objects
var pool = &sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 4096)
    },
}

func poolDemo() {
    // Get from pool (may reuse a previous allocation)
    buf := pool.Get().([]byte)
    buf = append(buf[:0], "hello world"...)
    
    // Use buf...
    fmt.Println(string(buf))
    
    // Return to pool for reuse
    pool.Put(buf[:0])
}
```

### Escape Analysis in Go — Deep Dive

```go
package main

// Run: go build -gcflags="-m -m" ./...
// to see detailed escape analysis

// Variables escape to heap when:
// 1. Their address is taken and used beyond the function's scope
// 2. They're assigned to an interface{}
// 3. They're sent on a channel
// 4. They're too large for the stack

func stackAlloc() int {
    x := 42  // stays on stack
    return x  // return by value — no escape
}

func heapAlloc() *int {
    x := 42  // ESCAPES — pointer returned
    return &x
}

func interfaceEscape() {
    x := 42
    var i interface{} = x  // x may escape
    _ = i
}

// Expert technique: avoid allocations in hot paths

type Point struct{ X, Y float64 }

// This causes allocation for each call (interface conversion):
func badDistance(a, b interface{}) float64 {
    pa := a.(Point)
    pb := b.(Point)
    dx := pa.X - pb.X
    dy := pa.Y - pb.Y
    return dx*dx + dy*dy
}

// No allocation — concrete types, no escaping:
func goodDistance(a, b Point) float64 {
    dx := a.X - b.X
    dy := a.Y - b.Y
    return dx*dx + dy*dy
}
```

### Go Memory Profiling

```go
import (
    "os"
    "runtime/pprof"
)

func profileMemory() {
    // Write heap profile:
    f, _ := os.Create("mem.prof")
    defer f.Close()
    runtime.GC() // get up-to-date statistics
    pprof.WriteHeapProfile(f)
    
    // Analyse with: go tool pprof mem.prof
    // Then: top, list funcName, web (requires graphviz)
}
```

---

## 10. Memory Allocators — How malloc Actually Works

### The Allocator's Job

The allocator sits between your code and the OS. Its job:
- Maintain a pool of memory obtained from the OS
- Efficiently satisfy arbitrary allocation requests (any size)
- Efficiently reclaim freed memory for reuse
- Minimise fragmentation
- Be fast and thread-safe

### Internal Allocator State — Free Lists

The classic approach: maintain lists of free blocks.

```
Heap memory as the allocator sees it:

┌─────────┬──────────────────┬───────────┬──────────────────┬──────────┐
│ HEADER  │   User Data      │  HEADER   │    User Data     │  HEADER  │
│ size=40 │  (40 bytes)      │ size=24   │   (24 bytes)     │ size=64  │
│ used=1  │                  │ used=0    │                  │ used=1   │
└─────────┴──────────────────┴───────────┴──────────────────┴──────────┘
                                  ↑
                              FREE block — on the free list
```

Each free block typically contains a header with size, a prev/next pointer for the free list, and optionally a footer with size (for coalescing).

### Buddy System Allocator

```
Memory is split into power-of-2 sized blocks called "buddies".

Initial: [    64 bytes    ]

Request 10 bytes:
→ Split: [32][32]
→ Split first 32: [16][16][32]
→ Allocate first 16 for the 10-byte request: [16*][16][32]

Free the 16* block:
→ [16 free][16][32]
→ Check if buddy (the other 16) is free: YES
→ Merge: [32 free][32]
→ Check if buddy (the other 32) is free: NO
→ Stop. State: [32 free][32]
```

Advantages: O(log n) allocation/free, excellent coalescing.
Disadvantage: Internal fragmentation (requesting 17 bytes wastes 15 bytes to get a 32-byte block).

### Size-Class Allocators (jemalloc, tcmalloc)

Modern allocators use **size classes** to avoid searching for the right block:

```
Small object size classes (example from jemalloc):
8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, ...

For an allocation of 37 bytes:
→ Round up to size class 40
→ Take from the pre-prepared pool of 40-byte blocks
→ O(1) allocation

Large objects (>= 4KB): use page-aligned mmap() regions

For free:
→ Determine size class from the block's address (via page metadata)
→ Return to the appropriate size class pool
→ O(1) deallocation
```

### Thread-Local Caching (tcmalloc / Go's runtime allocator)

The bottleneck in multi-threaded allocation is the lock on the global free list. Solution: give each thread its own cache.

```
Thread 1         Thread 2         Thread 3
   │                │                │
[Thread Cache]  [Thread Cache]  [Thread Cache]
   │                │                │
   └────────────────┴────────────────┘
                    │
             [Central Cache]
                    │
             [OS / mmap()]
```

Each thread gets from its local cache first. Only when the cache is empty does it go to the central (locked) cache. This makes allocation nearly lock-free in practice.

### Implementing a Simple Allocator in C

```c
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>

// A minimal bump (arena) allocator:
typedef struct {
    uint8_t *start;
    uint8_t *current;
    size_t   capacity;
} Arena;

Arena arena_new(size_t capacity) {
    Arena a;
    a.start = mmap(NULL, capacity,
                   PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS,
                   -1, 0);
    a.current = a.start;
    a.capacity = capacity;
    return a;
}

void *arena_alloc(Arena *a, size_t size, size_t align) {
    // Align the current pointer:
    uintptr_t curr = (uintptr_t)a->current;
    uintptr_t aligned = (curr + align - 1) & ~(align - 1);
    
    if (aligned + size > (uintptr_t)a->start + a->capacity) {
        return NULL; // OOM
    }
    
    a->current = (uint8_t *)(aligned + size);
    return (void *)aligned;
}

// Free ALL at once — O(1), no per-object overhead:
void arena_reset(Arena *a) {
    a->current = a->start;
}

void arena_free(Arena *a) {
    munmap(a->start, a->capacity);
    a->start = a->current = NULL;
    a->capacity = 0;
}

// Usage:
int main() {
    Arena arena = arena_new(1024 * 1024); // 1 MB arena
    
    int *arr = arena_alloc(&arena, 100 * sizeof(int), _Alignof(int));
    char *str = arena_alloc(&arena, 256, _Alignof(char));
    
    for (int i = 0; i < 100; i++) arr[i] = i;
    strcpy(str, "hello arena");
    
    // No per-object free needed!
    arena_reset(&arena); // Free everything at once
    arena_free(&arena);  // Return to OS
    return 0;
}
```

---

## 11. Virtual Memory and Paging

### The MMU and Address Translation

Every memory access goes through the **MMU (Memory Management Unit)** — a hardware component that translates virtual addresses to physical addresses.

```
Virtual Address (64-bit, x86-64):
Bits [63:48] = Sign extension (unused)
Bits [47:39] = Level 4 page table index (PML4)
Bits [38:30] = Level 3 page table index (PDPT)
Bits [29:21] = Level 2 page table index (PD)
Bits [20:12] = Level 1 page table index (PT)
Bits [11:0]  = Offset within page (4096 bytes = 2^12)

Translation:
VA → PML4[idx4] → PML4E → PDPT[idx3] → PDPTE → PD[idx2] → PDE → PT[idx1] → PTE → PA + offset
```

Each process has its own **page table** — a tree of tables mapping virtual pages to physical frames. The OS keeps this table in RAM. The CPU caches recent translations in the **TLB (Translation Lookaside Buffer)**.

### Pages and Page Faults

A **page** is the unit of memory that the OS manages. Typically 4 KB. A **frame** is a physical 4 KB chunk of RAM.

**Page Fault** occurs when you access a virtual page that:
1. Is not in RAM (paged out to disk) → OS fetches it from swap
2. Does not exist (unmapped) → Segmentation fault
3. Violates permissions (write to read-only) → Segfault or copy-on-write

```c
// Triggering a page fault intentionally (to understand demand paging):
#include <sys/mman.h>
#include <stdio.h>

int main() {
    size_t size = 1024 * 1024 * 1024; // 1 GB virtual mapping
    
    // MAP_ANONYMOUS | MAP_PRIVATE: virtual pages, NOT backed by RAM yet
    char *mem = mmap(NULL, size,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS,
                     -1, 0);
    
    // At this point: 1 GB of virtual address space is reserved
    // But NO physical RAM is used — pages are not backed yet
    
    // When we access each page, a page fault occurs:
    // OS allocates a physical frame and maps the page
    for (size_t i = 0; i < size; i += 4096) {
        mem[i] = 1; // page fault on first access to each page
    }
    
    // Now 1 GB of RAM is used
    munmap(mem, size);
    return 0;
}
```

### mmap — Memory-Mapped Files

`mmap` maps a file directly into the process's virtual address space. Instead of read()/write() system calls, you access file data via pointers.

```c
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>

// Read a file via mmap — zero-copy file access:
void mmap_read_example(const char *filename) {
    int fd = open(filename, O_RDONLY);
    struct stat sb;
    fstat(fd, &sb);
    size_t size = sb.st_size;
    
    // Map the file into memory:
    char *data = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd); // fd can be closed after mmap
    
    // Access file contents as memory:
    for (size_t i = 0; i < size; i++) {
        // data[i] is the i-th byte of the file
        // Page faults bring in 4KB at a time from disk
    }
    
    // Hint to the OS about access pattern:
    madvise(data, size, MADV_SEQUENTIAL); // Tell OS we'll read linearly
    
    munmap(data, size);
}

// Write to a file via mmap:
void mmap_write_example(const char *filename, size_t size) {
    int fd = open(filename, O_RDWR | O_CREAT | O_TRUNC, 0644);
    ftruncate(fd, size); // Set file size
    
    char *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    
    // Write to memory → OS writes to file asynchronously
    for (size_t i = 0; i < size; i++) data[i] = 'A';
    
    msync(data, size, MS_SYNC); // Ensure written to disk
    munmap(data, size);
}
```

### Huge Pages

Standard pages are 4 KB. Huge pages are 2 MB (or 1 GB). Using huge pages for large allocations reduces TLB pressure (fewer TLB entries needed to cover the same memory).

```c
// Allocate with huge pages:
void *huge = mmap(NULL, 2 * 1024 * 1024,
                  PROT_READ | PROT_WRITE,
                  MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                  -1, 0);
// Transparent Huge Pages (THP): Linux can use 2MB pages automatically
// for large anonymous mappings without the MAP_HUGETLB flag.
```

### Swap Space

When physical RAM is full, the OS **swaps out** cold pages to disk (swap partition or swap file). When those pages are needed again, a page fault occurs and they're swapped back in. This allows the total working set to exceed physical RAM — at the cost of disk access latency (~1000x slower than RAM).

---

## 12. CPU Cache and Memory Locality

### The Two Types of Locality

**Temporal Locality**: If you access address X, you'll likely access X again soon.
- **Implication**: Keep hot data small. Avoid evicting data you'll need again.

**Spatial Locality**: If you access address X, you'll likely access X+1, X+2... soon.
- **Implication**: Store related data contiguously. Use arrays, not linked lists for sequential access.

### Cache Lines — The Fundamental Unit

Cache lines are 64 bytes on modern x86. When you read any byte, the CPU fetches all 64 bytes surrounding it into cache. This is why arrays beat linked lists for sequential scans — a linked list node may be anywhere in memory.

```c
#include <time.h>
#include <stdlib.h>

#define SIZE (16 * 1024 * 1024)  // 16 MB — larger than L3 cache

// SLOW: random access — every access is a cache miss
void random_access_benchmark() {
    int *arr = malloc(SIZE * sizeof(int));
    int *idx = malloc(SIZE * sizeof(int));
    
    // Create random permutation:
    for (int i = 0; i < SIZE; i++) idx[i] = i;
    for (int i = SIZE-1; i > 0; i--) {
        int j = rand() % (i+1);
        int tmp = idx[i]; idx[i] = idx[j]; idx[j] = tmp;
    }
    
    long sum = 0;
    for (int i = 0; i < SIZE; i++) sum += arr[idx[i]]; // cache miss every time
    printf("sum=%ld\n", sum);
    
    free(arr); free(idx);
}

// FAST: sequential access — prefetcher handles it
void sequential_access_benchmark() {
    int *arr = malloc(SIZE * sizeof(int));
    long sum = 0;
    for (int i = 0; i < SIZE; i++) sum += arr[i]; // cache-friendly
    printf("sum=%ld\n", sum);
    free(arr);
}
```

### Data-Oriented Design (DOD)

The key insight: design your data layout for the access pattern, not for conceptual organisation.

```c
// ─────────────────────────────────────────────────────
// AOS — Array of Structures (naive, cache-unfriendly)
// ─────────────────────────────────────────────────────
typedef struct {
    float x, y, z;   // position (used in hot loop)
    float vx, vy, vz; // velocity (used in hot loop)
    char  name[32];   // name (rarely needed)
    int   id;
    double mass;
} Particle_AOS;

// To update positions, you load ALL data for each particle
// including the 32-byte name field you don't need:
void update_positions_AOS(Particle_AOS *particles, int n, float dt) {
    for (int i = 0; i < n; i++) {
        // Each particle is ~64 bytes. Loading x, vx also loads name.
        // Cache line wasted on unused 'name' data.
        particles[i].x += particles[i].vx * dt;
        particles[i].y += particles[i].vy * dt;
        particles[i].z += particles[i].vz * dt;
    }
}

// ─────────────────────────────────────────────────────
// SOA — Structure of Arrays (cache-friendly)
// ─────────────────────────────────────────────────────
typedef struct {
    float *x, *y, *z;     // positions (contiguous arrays)
    float *vx, *vy, *vz;  // velocities (contiguous arrays)
    char  (*names)[32];   // names (separate, accessed rarely)
    int   *ids;
    double *masses;
    int    count;
} Particles_SOA;

void update_positions_SOA(Particles_SOA *p, float dt) {
    // x, y, z, vx, vy, vz are packed separately
    // Loading p->x[i] also loads x[i+1]...x[i+15] into cache
    // Every cache line is 100% useful data for this operation
    for (int i = 0; i < p->count; i++) {
        p->x[i] += p->vx[i] * dt;
        p->y[i] += p->vy[i] * dt;
        p->z[i] += p->vz[i] * dt;
    }
    // With SIMD (AVX2), this can process 8 floats per instruction
}
```

### Cache-Friendly Data Structures in Rust

```rust
// B-Tree vs Binary Search Tree
// BST nodes: pointer + data + 2 pointers = scattered in memory
// B-Tree: all keys in a node are contiguous → cache line friendly

use std::collections::BTreeMap;
use std::collections::HashMap;

fn btree_vs_hash() {
    let mut btree: BTreeMap<i32, i32> = BTreeMap::new();
    let mut hash: HashMap<i32, i32> = HashMap::new();
    
    // For sequential access patterns, BTreeMap wins on cache performance
    // For random access, HashMap wins on O(1) vs O(log n)
    
    for i in 0..10000 {
        btree.insert(i, i * 2);
        hash.insert(i, i * 2);
    }
}

// Cache-line padding to prevent false sharing:
use std::sync::atomic::AtomicU64;

#[repr(align(64))] // Align to cache line boundary
struct PaddedCounter {
    value: AtomicU64,
    _pad: [u8; 56], // Fill to 64 bytes
}
// Each counter is on its own cache line — threads don't fight over it
```

### Prefetching

CPUs have hardware prefetchers that detect sequential access patterns and speculatively load future cache lines. You can also hint manually:

```c
#include <xmmintrin.h>  // SSE prefetch intrinsics

void prefetch_demo(int *arr, int n) {
    for (int i = 0; i < n; i++) {
        // Prefetch data 8 iterations ahead:
        if (i + 8 < n) {
            _mm_prefetch((char*)&arr[i + 8], _MM_HINT_T0);
        }
        // Process current element:
        arr[i] *= 2;
    }
}
```

---

## 13. Memory Alignment and Struct Padding

### Why Alignment Exists

CPUs read memory in aligned chunks. A 64-bit integer is most efficiently read when it's at an address divisible by 8. Reading it at an unaligned address either:
- Requires two memory reads + a shift+or operation (slow), or
- Causes a hardware fault (on strict architectures like early MIPS/SPARC)

The compiler inserts **padding** between struct fields to ensure each field meets its alignment requirement.

### Alignment Rules

| Type | Size | Alignment |
|------|------|-----------|
| char | 1 | 1 |
| short | 2 | 2 |
| int | 4 | 4 |
| long (64-bit) | 8 | 8 |
| float | 4 | 4 |
| double | 8 | 8 |
| pointer | 8 | 8 |

A struct's alignment = the maximum alignment of any of its members. Its size is rounded up to a multiple of its alignment.

### Padding in Practice

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

// Bad layout — wastes 7 bytes:
struct Bad {
    char   a;   // 1 byte at offset 0
    // 7 bytes padding here (to align d to 8)
    double d;   // 8 bytes at offset 8
    char   b;   // 1 byte at offset 16
    // 3 bytes padding (to align i to 4)
    int    i;   // 4 bytes at offset 20
    // 4 bytes padding at end (to align struct to 8)
};
// Total: 1 + 7 + 8 + 1 + 3 + 4 + 4 = 28 bytes (but could be 14!)

// Good layout — fields ordered by size (largest first):
struct Good {
    double d;   // 8 bytes at offset 0
    int    i;   // 4 bytes at offset 8
    char   a;   // 1 byte at offset 12
    char   b;   // 1 byte at offset 13
    // 2 bytes padding to align struct to 8
};
// Total: 8 + 4 + 1 + 1 + 2 = 16 bytes

void alignment_demo() {
    printf("Bad struct size: %zu\n", sizeof(struct Bad));    // 28
    printf("Good struct size: %zu\n", sizeof(struct Good));  // 16
    
    // Offsets:
    printf("offsetof Bad.a: %zu\n",  offsetof(struct Bad, a)); // 0
    printf("offsetof Bad.d: %zu\n",  offsetof(struct Bad, d)); // 8
    printf("offsetof Bad.b: %zu\n",  offsetof(struct Bad, b)); // 16
    printf("offsetof Bad.i: %zu\n",  offsetof(struct Bad, i)); // 20
    
    printf("offsetof Good.d: %zu\n", offsetof(struct Good, d)); // 0
    printf("offsetof Good.i: %zu\n", offsetof(struct Good, i)); // 8
    printf("offsetof Good.a: %zu\n", offsetof(struct Good, a)); // 12
    printf("offsetof Good.b: %zu\n", offsetof(struct Good, b)); // 13
}

// Packed struct (no padding) — use only when interfacing with protocols/hardware:
struct __attribute__((packed)) Packed {
    char   a;  // 0
    double d;  // 1 (unaligned! slow on x86, fault on strict architectures)
    int    i;  // 9
};
printf("Packed size: %zu\n", sizeof(struct Packed)); // 13
```

### Alignment in Rust

```rust
use std::mem;

// Rust automatically optimises struct layout for you (unlike C)
// But you can control it:

// Default Rust layout (can reorder fields for optimal packing):
struct Auto {
    a: u8,
    b: f64,
    c: u32,
}
// Rust may reorder to: b(8), c(4), a(1) + 3 padding = 16 bytes

// C-compatible layout (exact field order, C padding rules):
#[repr(C)]
struct CCompat {
    a: u8,   // 0
    // 7 pad
    b: f64,  // 8
    c: u32,  // 16
    // 4 pad
}
// Size: 24

// Packed (no padding):
#[repr(packed)]
struct Packed {
    a: u8,
    b: f64,
    c: u32,
}
// Size: 13 — but accessing b and c is UNSAFE (unaligned reads)

// Custom alignment:
#[repr(align(64))]
struct CacheAligned {
    data: [u8; 32],
}
// Always starts at a 64-byte boundary

fn alignment_info() {
    println!("Auto size:  {}", mem::size_of::<Auto>());     // 16
    println!("Auto align: {}", mem::align_of::<Auto>());    // 8
    println!("CCompat size: {}", mem::size_of::<CCompat>()); // 24
}
```

### Alignment in Go

```go
package main

import (
    "fmt"
    "unsafe"
)

type Bad struct {
    A byte    // 1 byte
    // 7 pad
    B float64 // 8 bytes
    C byte    // 1 byte
    // 3 pad
    D int32   // 4 bytes
    // 4 pad at end
} // Total: 28 bytes

type Good struct {
    B float64 // 8 bytes
    D int32   // 4 bytes
    A byte    // 1 byte
    C byte    // 1 byte
    // 2 pad
} // Total: 16 bytes

func alignmentDemo() {
    fmt.Println("Bad size:", unsafe.Sizeof(Bad{}))    // 28
    fmt.Println("Good size:", unsafe.Sizeof(Good{}))  // 16
    
    // Offsets:
    fmt.Println("Bad.A offset:", unsafe.Offsetof(Bad{}.A)) // 0
    fmt.Println("Bad.B offset:", unsafe.Offsetof(Bad{}.B)) // 8
    
    // Go struct alignment: go vet can warn about suboptimal struct layouts
    // Use: go vet -copylocks ./...
    // fieldalignment linter: golang.org/x/tools/go/analysis/passes/fieldalignment
}
```

---

## 14. Memory Safety

### The Taxonomy of Memory Bugs

**Category 1: Temporal Violations** (using memory at the wrong time)
- Use-after-free
- Double free
- Use of uninitialized memory

**Category 2: Spatial Violations** (accessing the wrong location)
- Buffer overflow (out-of-bounds write)
- Buffer over-read (out-of-bounds read)
- Stack overflow

**Category 3: Ownership Violations**
- Memory leaks
- Dangling pointers

### Use-After-Free in Depth

```c
#include <stdlib.h>
#include <stdio.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;

// Classic UAF in a linked list:
void uaf_demo() {
    Node *head = malloc(sizeof(Node));
    Node *second = malloc(sizeof(Node));
    head->value = 1;
    head->next = second;
    second->value = 2;
    second->next = NULL;
    
    free(second);    // Free second node
    
    // Now head->next is a dangling pointer!
    // The memory second pointed to may have been reallocated.
    
    // This is a use-after-free — undefined behaviour:
    printf("%d\n", head->next->value); // May print 2, 0, garbage, or crash
    
    // Mitigation pattern — zero pointers after free:
    free(head);
    head = NULL;
    // But we can't fix second because we already freed it
}
```

### Buffer Overflow — A Security Perspective

```c
// Classic stack buffer overflow (CVE archetype):
void vulnerable_function(char *user_input) {
    char buffer[64];
    strcpy(buffer, user_input); // No length check!
    
    // Stack layout:
    // [buffer[64]] [saved_rbp] [return_address] [arguments]
    
    // If user_input is 80 bytes:
    // buffer is overflowed, saved_rbp overwritten, return address overwritten
    // Attacker controls where this function "returns" to
}

// Safe version:
void safe_function(const char *user_input) {
    char buffer[64];
    strncpy(buffer, user_input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
}

// Modern protections against buffer overflow attacks:
// 1. Stack Canaries: compiler inserts a "canary" value before return address
//    If it's modified, the program aborts (detect overflow)
// 2. ASLR: Address Space Layout Randomisation — stack/heap/libs at random addresses
// 3. NX: No-Execute bit — stack/heap not executable (no shellcode execution)
// 4. SafeStack: stores sensitive data on a separate, protected stack
```

### How Rust Prevents ALL of These at Compile Time

```rust
// 1. No use-after-free: borrow checker prevents it
fn no_uaf() {
    let s = String::from("hello");
    let r = &s;
    drop(s); // Free s
    // println!("{}", r); // COMPILE ERROR: cannot use 'r' because 's' was moved
}

// 2. No double-free: each value has exactly one owner
fn no_double_free() {
    let s = String::from("hello");
    let s2 = s; // s moved to s2
    drop(s2); // freed
    // drop(s); // COMPILE ERROR: s was moved
}

// 3. No buffer overflow: bounds checked at runtime (in safe Rust)
fn no_overflow() {
    let v = vec![1, 2, 3];
    // v[10]; // RUNTIME PANIC: index out of bounds (not silent UB!)
    
    // Explicitly out-of-bounds without panicking:
    match v.get(10) {
        Some(val) => println!("{}", val),
        None => println!("out of bounds"),
    }
}

// 4. No dangling pointers: lifetimes prevent this at compile time
// fn dangling() -> &i32 {
//     let x = 5;
//     &x // COMPILE ERROR: x does not live long enough
// }

// 5. No data races: ownership rules apply to concurrency too
use std::sync::{Arc, Mutex};
use std::thread;

fn no_data_race() {
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    
    let t = thread::spawn(move || {
        let mut d = data_clone.lock().unwrap();
        d.push(4);
    });
    
    t.join().unwrap();
    println!("{:?}", data.lock().unwrap());
}
```

### Valgrind, AddressSanitizer, MemorySanitizer

```bash
# Valgrind: full memory error detection (slower, works on any binary)
gcc -g -O0 program.c -o program
valgrind --leak-check=full --track-origins=yes ./program

# AddressSanitizer (ASan): fast (~2x overhead), detects:
# - Heap buffer overflow/underflow
# - Stack buffer overflow
# - Use-after-free
# - Use-after-return
# - Memory leaks
gcc -g -fsanitize=address -fno-omit-frame-pointer program.c -o program
./program

# MemorySanitizer (MSan): detects uninitialised reads
# (requires clang, full recompilation of dependencies)
clang -g -fsanitize=memory program.c -o program

# UBSanitizer (UBSan): detects undefined behaviour
gcc -g -fsanitize=undefined program.c -o program

# In Rust: AddressSanitizer available via:
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build

# In Go: race detector (detects data races):
go test -race ./...
go build -race ./...

# Go ASan (Go 1.18+):
go build -asan ./...
```

---

## 15. Advanced Allocators — Arenas, Pools, Slabs

### The Problem with General-Purpose Allocation

General-purpose allocators like `malloc` are remarkable engineering achievements, but they carry overhead:
- Lock contention in multi-threaded code
- Metadata overhead per allocation
- Fragmentation over time
- Cache-unfriendly allocation patterns

When you have domain knowledge about your allocation pattern, you can do better.

### Arena (Bump) Allocator

```rust
// Arena allocator in Rust:
pub struct Arena {
    data: Vec<u8>,
    offset: usize,
}

impl Arena {
    pub fn new(capacity: usize) -> Self {
        Arena { data: vec![0u8; capacity], offset: 0 }
    }
    
    pub fn alloc<T>(&mut self) -> Option<&mut T> {
        let align = std::mem::align_of::<T>();
        let size  = std::mem::size_of::<T>();
        
        // Align the offset:
        let aligned = (self.offset + align - 1) & !(align - 1);
        
        if aligned + size > self.data.len() {
            return None; // OOM
        }
        
        self.offset = aligned + size;
        
        // Safety: we just verified bounds and alignment
        unsafe {
            let ptr = self.data.as_mut_ptr().add(aligned) as *mut T;
            Some(&mut *ptr)
        }
    }
    
    // Free all at once — O(1)
    pub fn reset(&mut self) {
        self.offset = 0;
    }
}

// Usage: per-request arena for a web server
// Each request gets an arena, entire request's allocations freed at once
fn handle_request(arena: &mut Arena) {
    let buf: &mut [u8; 256] = arena.alloc().unwrap();
    // use buf...
    // No individual frees needed!
}
```

### Object Pool

```go
// Go object pool using sync.Pool
package main

import (
    "sync"
    "net/http"
)

// Pool of reusable byte buffers — avoids repeated allocation/GC:
var bufPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 4096)
    },
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
    // Get a buffer (may be recycled from previous request):
    buf := bufPool.Get().([]byte)
    buf = buf[:0] // Reset length, keep capacity
    
    defer func() {
        bufPool.Put(buf) // Return to pool when done
    }()
    
    // Use buf for processing...
    buf = append(buf, "response data"...)
    w.Write(buf)
}
```

### Slab Allocator (Linux Kernel Pattern)

```c
// The Linux kernel's slab allocator manages fixed-size objects efficiently
// Each "slab" contains multiple objects of the same type

typedef struct Slab {
    void      *memory;       // The contiguous memory block
    size_t     obj_size;     // Fixed size of each object
    size_t     capacity;     // Number of objects this slab holds
    size_t     used;         // Number of objects in use
    uint64_t   free_bitmap;  // Bit i = 1 means object i is free
    struct Slab *next;
} Slab;

typedef struct SlabCache {
    size_t   obj_size;
    Slab    *partial;  // Slabs with some free objects
    Slab    *full;     // Slabs with no free objects
    Slab    *empty;    // Slabs entirely free
} SlabCache;

Slab *slab_new(size_t obj_size, size_t count) {
    Slab *s = malloc(sizeof(Slab) + obj_size * count);
    s->memory     = (char*)s + sizeof(Slab);
    s->obj_size   = obj_size;
    s->capacity   = count;
    s->used       = 0;
    s->free_bitmap = (count == 64) ? ~0ULL : ((1ULL << count) - 1);
    s->next = NULL;
    return s;
}

void *slab_alloc(Slab *s) {
    if (!s->free_bitmap) return NULL;
    int idx = __builtin_ctzll(s->free_bitmap); // Find first free bit
    s->free_bitmap &= ~(1ULL << idx);           // Mark as used
    s->used++;
    return (char*)s->memory + idx * s->obj_size;
}

void slab_free(Slab *s, void *ptr) {
    size_t idx = ((char*)ptr - (char*)s->memory) / s->obj_size;
    s->free_bitmap |= (1ULL << idx);  // Mark as free
    s->used--;
}

// Advantages:
// - O(1) allocation via bit manipulation
// - Zero fragmentation (all objects same size)
// - Cache-friendly (objects compactly packed in slab)
// - No per-object metadata overhead
```

### Stack Allocator

```c
// Stack allocator: allocate in order, free in reverse order only
// Useful for temporary allocations with strict LIFO pattern

typedef struct {
    uint8_t *buffer;
    size_t   capacity;
    size_t   top;
} StackAllocator;

typedef size_t StackMarker; // Save/restore points

StackMarker stack_save(StackAllocator *s) {
    return s->top;
}

void *stack_alloc(StackAllocator *s, size_t size, size_t align) {
    size_t aligned = (s->top + align - 1) & ~(align - 1);
    if (aligned + size > s->capacity) return NULL;
    s->top = aligned + size;
    return s->buffer + aligned;
}

void stack_restore(StackAllocator *s, StackMarker marker) {
    s->top = marker; // Free everything allocated since marker
}

// Usage:
void process_frame(StackAllocator *sa) {
    StackMarker start = stack_save(sa);
    
    // Allocate temporary data:
    int *temp1 = stack_alloc(sa, 100 * sizeof(int), _Alignof(int));
    float *temp2 = stack_alloc(sa, 50 * sizeof(float), _Alignof(float));
    
    // ... process using temp1 and temp2 ...
    
    stack_restore(sa, start); // Free both in one shot
}
```

---

## 16. Concurrency and Memory

### The Memory Consistency Problem

On a single CPU, operations appear in program order. But:
1. CPUs **reorder** instructions for performance (out-of-order execution)
2. Compilers **reorder** instructions for optimisation
3. Multiple CPUs have **separate caches** — writes are not immediately visible to other cores

This means: without explicit synchronisation, two threads reading/writing shared memory may see inconsistent results.

### The C11/C++11 Memory Model

```c
#include <stdatomic.h>
#include <stdio.h>
#include <threads.h>

// Without atomics — DATA RACE (undefined behaviour):
int x = 0;
void unsafe_increment() { x++; } // NOT SAFE — read-modify-write is not atomic

// With atomics — safe:
atomic_int ax = 0;
void safe_increment() {
    atomic_fetch_add(&ax, 1); // Guaranteed atomic read-modify-write
}

// Memory orders (from weakest/fastest to strongest/safest):

// RELAXED: Only atomicity guaranteed. No ordering w.r.t. other operations.
// Use for: statistics counters, progress meters
atomic_store_explicit(&ax, 1, memory_order_relaxed);

// ACQUIRE: This load happens before all subsequent loads/stores in this thread.
// Use for: lock acquire, read side of producer-consumer
int val = atomic_load_explicit(&ax, memory_order_acquire);

// RELEASE: All previous loads/stores in this thread happen before this store.
// Use for: lock release, write side of producer-consumer
atomic_store_explicit(&ax, 1, memory_order_release);

// ACQ_REL: Combines acquire and release. Use for: compare-and-swap
atomic_compare_exchange_strong_explicit(
    &ax, &expected, desired,
    memory_order_acq_rel,
    memory_order_acquire);

// SEQ_CST: Full sequential consistency. Strongest. Slowest.
// Default for atomic_fetch_add, atomic_store, etc.
// Use for: general purpose, correctness over speed
atomic_fetch_add(&ax, 1); // Implicitly seq_cst
```

### The Happens-Before Relationship

```
Happens-Before (HB): operation A HB operation B means B sees A's effects.

Rules:
1. Within one thread: A before B in code → A HB B
2. Across threads:    Thread 1 releases lock L → Thread 2 acquires L → all of Thread 1's
                      writes before the release are visible to Thread 2 after acquire
3. Atomic operations: rel-store to X HB acq-load of X (if load sees the store's value)

Example: Producer-Consumer
Thread 1 (producer):          Thread 2 (consumer):
data = expensive_compute();   while (!ready.load(acquire));
ready.store(1, release);      use(data);  // Sees data correctly because:
                              // T1's release HB T2's acquire
                              // T1's write to 'data' HB T2's read of 'data'
```

### Rust's Concurrency Memory Safety

```rust
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex, RwLock};
use std::thread;

fn atomics_in_rust() {
    let counter = Arc::new(AtomicUsize::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                // SeqCst for correctness; Relaxed if you only need atomicity
                c.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }
    
    for h in handles { h.join().unwrap(); }
    println!("Final: {}", counter.load(Ordering::SeqCst)); // 10000
}

// Spinlock implementation using atomics:
pub struct SpinLock {
    locked: AtomicBool,
}

impl SpinLock {
    pub fn new() -> Self { SpinLock { locked: AtomicBool::new(false) } }
    
    pub fn lock(&self) {
        while self.locked.compare_exchange_weak(
            false, true,
            Ordering::Acquire,
            Ordering::Relaxed,
        ).is_err() {
            // Hint to CPU that we're in a spin-wait loop:
            std::hint::spin_loop();
        }
    }
    
    pub fn unlock(&self) {
        self.locked.store(false, Ordering::Release);
    }
}

// False sharing — the cache-line problem with concurrent data:
// Two atomic variables on the SAME cache line cause contention:
static A: AtomicUsize = AtomicUsize::new(0);
static B: AtomicUsize = AtomicUsize::new(0);
// A and B are adjacent in memory — on the same cache line
// Thread 1 writes A, Thread 2 writes B: cache line bounces between cores

// Solution: pad to separate cache lines:
#[repr(align(64))]
struct Padded(AtomicUsize);

static PA: Padded = Padded(AtomicUsize::new(0)); // own cache line
static PB: Padded = Padded(AtomicUsize::new(0)); // own cache line
```

---

## 17. NUMA — Non-Uniform Memory Access

### The NUMA Architecture

In systems with multiple physical CPU sockets (common in servers), each socket has its own local RAM. Accessing local RAM is fast; accessing another socket's RAM is slower (crossing the QPI/UPI bus).

```
Socket 0                        Socket 1
┌─────────────────────┐        ┌─────────────────────┐
│  Core 0 .. Core 15  │        │  Core 16 .. Core 31 │
│                     │        │                     │
│  Local RAM: 64 GB   │◄──────►│  Local RAM: 64 GB   │
│  Latency: ~70 ns    │  QPI   │  Latency: ~70 ns    │
└─────────────────────┘        └─────────────────────┘
                 Cross-socket: ~150-300 ns
```

### NUMA-Aware Programming

```c
#include <numa.h>
#include <numaif.h>

// Allocate memory on a specific NUMA node:
void *mem = numa_alloc_onnode(size, 0); // Allocate on node 0

// Allocate memory local to current thread's node:
void *local_mem = numa_alloc_local(size);

// Pin thread to a specific CPU:
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(0, &cpuset); // Pin to CPU 0 (NUMA node 0)
pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);

// Query NUMA topology:
int num_nodes = numa_num_configured_nodes();
int node_for_cpu = numa_node_of_cpu(cpu_id);

// Check which node a pointer belongs to:
int policy;
unsigned long nodemask;
get_mempolicy(&policy, &nodemask, sizeof(nodemask) * 8, mem, MPOL_F_ADDR);
```

### NUMA Impact on Performance

```
Access pattern:         Latency     Bandwidth
─────────────────────────────────────────────
Local (same socket):    70 ns       ~100 GB/s
Remote (other socket):  140-300 ns  ~50 GB/s

For a database with 100M random reads/sec:
Local:  100M × 70ns  = 7 seconds of latency per second (7x load)
Remote: 100M × 200ns = 20 seconds of latency per second (20x load — 3x worse!)
```

Real-world implications: Redis, databases, and HPC applications explicitly bind worker threads to NUMA nodes and ensure data is allocated locally.

---

## 18. Memory Profiling and Debugging

### Profiling in C/Go/Rust

```bash
#─────────────────────────────────────────────────────
# C: Valgrind heap profiler
#─────────────────────────────────────────────────────
gcc -g -O1 program.c -o program
valgrind --tool=massif ./program
ms_print massif.out.* | head -50

# massif shows heap usage over time with allocation call stacks

#─────────────────────────────────────────────────────
# Go: built-in pprof
#─────────────────────────────────────────────────────
# Add to your main.go:
# import _ "net/http/pprof"
# go func() { http.ListenAndServe(":6060", nil) }()

# Then:
go tool pprof http://localhost:6060/debug/pprof/heap
# In pprof: top, list <funcname>, web

# Record allocation profile:
go tool pprof -alloc_objects http://localhost:6060/debug/pprof/heap

#─────────────────────────────────────────────────────
# Rust: heaptrack, cargo-flamegraph
#─────────────────────────────────────────────────────
cargo install heaptrack  # or use system package
heaptrack ./target/release/program
heaptrack_gui heaptrack.*.zst

# Alternative: DHAT (dynamic heap analysis tool via valgrind)
cargo build --release
valgrind --tool=dhat ./target/release/program
dh_view.html (open in browser with the DHAT output file)
```

### Finding Memory Leaks

```go
// Go: track allocations over time
package main

import (
    "fmt"
    "runtime"
    "time"
)

func detectLeak() {
    var before, after runtime.MemStats
    
    runtime.GC()
    runtime.ReadMemStats(&before)
    
    // Potentially leaky code:
    for i := 0; i < 10000; i++ {
        _ = make([]byte, 1024)
    }
    
    runtime.GC()
    runtime.ReadMemStats(&after)
    
    fmt.Printf("Heap before: %d bytes\n", before.HeapInuse)
    fmt.Printf("Heap after:  %d bytes\n", after.HeapInuse)
    fmt.Printf("Allocated:   %d bytes\n", after.TotalAlloc - before.TotalAlloc)
}
```

```c
// C: wrapper around malloc to track all allocations
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// Simple leak tracker:
typedef struct AllocRecord {
    void *ptr;
    size_t size;
    const char *file;
    int line;
    struct AllocRecord *next;
} AllocRecord;

static AllocRecord *alloc_list = NULL;

void *tracked_malloc(size_t size, const char *file, int line) {
    void *ptr = malloc(size);
    if (!ptr) return NULL;
    
    AllocRecord *rec = malloc(sizeof(AllocRecord));
    rec->ptr = ptr;
    rec->size = size;
    rec->file = file;
    rec->line = line;
    rec->next = alloc_list;
    alloc_list = rec;
    return ptr;
}

void tracked_free(void *ptr) {
    AllocRecord **cur = &alloc_list;
    while (*cur) {
        if ((*cur)->ptr == ptr) {
            AllocRecord *found = *cur;
            *cur = found->next;
            free(found);
            free(ptr);
            return;
        }
        cur = &(*cur)->next;
    }
    fprintf(stderr, "ERROR: free of untracked pointer %p\n", ptr);
}

void check_leaks() {
    for (AllocRecord *r = alloc_list; r; r = r->next) {
        fprintf(stderr, "LEAK: %zu bytes at %s:%d (addr=%p)\n",
                r->size, r->file, r->line, r->ptr);
    }
}

#define malloc(n) tracked_malloc(n, __FILE__, __LINE__)
#define free(p) tracked_free(p)
```

---

## 19. Real-World Case Studies

### Case Study 1: Redis — All Data In Memory

Redis keeps ALL data in RAM. This design decision drives everything:
- Sub-millisecond latency (no disk seeks)
- Custom allocator (jemalloc) to reduce fragmentation
- Copy-On-Write for persistence (fork() + save snapshot)
- RDB: serialize the entire heap snapshot to disk
- AOF: append every write command to a log file

**Memory layout insight:** Redis uses `zmalloc` — a thin wrapper around jemalloc — with a global counter tracking total allocated bytes. This lets Redis enforce a `maxmemory` limit with LRU eviction.

### Case Study 2: Linux Kernel — Slab Allocator

The kernel allocates thousands of `task_struct`, `inode`, `file`, `socket` objects constantly. Rather than calling `malloc()` (which doesn't exist in the kernel), it uses the **slab allocator**:

- One slab cache per object type (e.g., `kmem_cache_create("task_struct", sizeof(task_struct), ...)`)
- Objects are pre-initialised to avoid repeated constructor calls
- Per-CPU caches for lock-free allocation in the common case

Result: Kernel object allocation is O(1) with minimal cache pressure.

### Case Study 3: Game Engines — Arena Per Frame

AAA game engines allocate from per-frame arenas:
- Frame begins: reset the arena (one pointer store)
- Allocate all temporary game state: particles, AI state, render commands
- Frame ends: the arena is reset — all temporary data is gone in O(1)
- No individual frees, no fragmentation, cache-friendly linear memory

This is why games can maintain 60-120 FPS with thousands of objects per frame.

### Case Study 4: Go's Goroutine Stacks

Traditional OS threads have 1-8 MB stacks (fixed). Go goroutines start with 2-8 KB.

Go achieves this via **copying stacks**: when a goroutine's stack overflows, Go:
1. Allocates a larger stack (2x the current size)
2. Copies all stack frames to the new location
3. Updates all pointers within the copied frames
4. Frees the old stack

This allows millions of goroutines with minimal memory cost. The trade-off: pointers to stack variables can be invalidated by stack growth (Go prevents you from taking an interior pointer to a stack-grown variable across function calls).

### Case Study 5: Rust's Zero-Cost Abstractions

Rust's ownership model compiles down to the exact same machine code as handwritten C. Consider:

```rust
fn sum(v: &[i32]) -> i64 {
    v.iter().map(|&x| x as i64).sum()
}
```

This compiles to a tight loop with SIMD vectorisation — the iterator abstraction costs nothing. This is possible because the borrow checker eliminates aliasing: the compiler knows `v` has no other writers, enabling aggressive optimisation.

---

## 20. Mental Models and Expert Intuition

### The Seven Mental Models of Memory Mastery

**Model 1: "Memory is Physics"**
Every byte has a physical location. Speed is determined by distance (latency) and road width (bandwidth). Design data to minimize travel distance and maximize road utilization.

**Model 2: "The Ownership Graph"**
Every allocation is a node. Ownership edges connect parent to child. For memory to be safe, this graph must be a tree (DAG at most). Cycles require special handling (Rc, Arc, GC, weak pointers). When the root of a subtree is freed, all nodes in that subtree are freed.

**Model 3: "Lifetime as a Time Window"**
Every piece of data has a "birth" (allocation/scope entry) and "death" (free/scope exit). A reference is valid only when the referent's window contains the reference's window. The borrow checker mechanically enforces this.

**Model 4: "The Allocator Contract"**
Every custom allocator has a contract: what sizes it handles efficiently, what patterns it's optimised for, what its failure modes are. Violating the implicit contract (e.g., using a pool allocator for variable sizes) destroys its advantages.

**Model 5: "Think in Cache Lines"**
Your program doesn't access bytes — it accesses cache lines. Every struct layout, every data structure choice, every access pattern should be evaluated in terms of: how many cache lines does this touch per operation?

**Model 6: "The Aliasing Restriction"**
Performance and safety both require limiting aliasing. When the compiler knows a pointer is not aliased, it can keep values in registers, avoid redundant loads, and vectorise loops. Rust's borrow checker enforces no aliasing as a language rule. C has `restrict`. This is why Fortran was historically faster than C — no pointers meant no aliasing.

**Model 7: "Memory as a Resource Like Time"**
Just as you analyse time complexity (how does this scale with input?), analyse memory complexity. Does this algorithm's memory usage grow O(1), O(n), O(n²)? Is there a space-time tradeoff you can exploit? Memoisation trades space for time. Streaming algorithms trade time for constant space.

### Cognitive Principles for Mastery

**Chunking**: Memory concepts cluster into groups — stack/heap is one chunk, ownership is another, cache performance is another. Master each chunk holistically before connecting them.

**Deliberate Practice**: Don't just read about memory — instrument real programs. Use `/proc/self/maps`, `valgrind`, `pprof`, ASan. See the effects of your understanding in real numbers.

**First-Principles Reasoning**: When debugging a memory issue, don't guess. Reason from: What was allocated? Who owns it? When does it die? Where is the mismatch?

**Systems Thinking**: Memory doesn't exist in isolation. It's connected to CPU execution (cache), OS (paging), concurrency (cache coherence), and compiler (optimisation). A change in one dimension affects all others.

---

## Quick Reference Cheatsheet

### When to Use What

| Situation | Solution |
|-----------|----------|
| Small, fixed-size, short-lived data | Stack |
| Large, dynamic, long-lived data | Heap (Box/malloc) |
| Shared ownership, single-thread | Rc<T> (Rust) / manual ref-counting (C) |
| Shared ownership, multi-thread | Arc<T> (Rust) / atomic ref-counting |
| Many same-sized objects | Pool/Slab allocator |
| Many temporary allocations per operation | Arena/bump allocator |
| Known-size array | Stack array |
| Unknown-size collection | Vec/slice |
| Zero-copy file I/O | mmap() |
| Global shared state | Arc<Mutex<T>> / sync.Mutex |
| Read-mostly shared state | Arc<RwLock<T>> / sync.RWMutex |

### Alignment Quick Reference

| Align to | Mask |
|----------|------|
| 2 bytes | `addr & ~1` or `(addr + 1) & ~1` |
| 4 bytes | `(addr + 3) & ~3` |
| 8 bytes | `(addr + 7) & ~7` |
| N bytes (power of 2) | `(addr + N - 1) & ~(N - 1)` |

### Complexity Reference

| Operation | Stack | Heap (malloc) | Pool/Slab | Arena |
|-----------|-------|---------------|-----------|-------|
| Allocate | O(1) | O(1) amortised | O(1) | O(1) |
| Free | O(1) | O(1) amortised | O(1) | O(1) bulk |
| Fragmentation | None | Possible | None | None |
| Thread-safe | Per-thread | Requires lock/TLS | Depends | Per-thread |
| Max size | ~8 MB | ~RAM | Fixed | Fixed |

---

*"The expert knows not just what the tools are, but which tool fits which nail — and more importantly, why."*

I'll create a comprehensive, end-to-end memory guide as a detailed markdown document. This will be one of the most thorough references you'll ever use.**2,919 lines. 20 chapters. Everything.** Here is what the guide covers, structured as a complete learning arc:

---

**Foundation Layer** — Chapters 1–3 establish the mental bedrock: what memory physically *is* at the transistor level, the full memory hierarchy from registers to disk with real latency numbers, and exactly how a process's virtual address space is laid out (TEXT, DATA, BSS, Stack, Heap, mmap regions). You learn to read `/proc/self/maps` and reason about *where* any variable lives.

**Core Mechanics** — Chapters 4–6 go deep into the stack and heap individually, with full assembly-level explanation of stack frames, RSP/RBP mechanics, calling conventions, and the allocator contract of `malloc/free`. Chapter 6 covers pointers raw — endianness, function pointers, fat pointers, arithmetic.

**Language Models** — Chapters 7–9 show the three philosophies side by side: **C's manual management** (with full safe patterns for vectors, strings, and structs), **Rust's ownership/borrow checker** (lifetimes, smart pointers, the compile-time proof system), and **Go's GC** (tricolor mark-and-sweep, escape analysis, `sync.Pool`, `pprof`).

**System Depth** — Chapters 10–13 go beneath user-space: how `malloc` actually works internally (free lists, buddy system, size classes, thread-local caches), virtual memory and paging (MMU, TLB, page faults, `mmap`), cache architecture and data-oriented design (AoS vs SoA with real impact), and struct alignment/padding with full numeric examples.

**Expert Territory** — Chapters 14–17 cover memory safety taxonomy and how each language addresses it, arena/pool/slab allocators with working implementations in C and Rust, the C11/Rust memory models with `happens-before`, memory ordering, and false sharing, then NUMA architecture for multi-socket servers.

**Practice Layer** — Chapters 18–20 give you profiling tools (Valgrind, ASan, `pprof`, heaptrack), five real-world case studies (Redis, Linux kernel slab, game engines, Go goroutine stacks, Rust zero-cost abstractions), and seven mental models that experts use to *think* about memory problems before touching code.

The quick-reference cheatsheet at the end distills the decision matrices you'll use daily.