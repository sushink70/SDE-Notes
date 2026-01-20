# The Complete System Programming Mastery Guide

*A comprehensive journey from hardware fundamentals to advanced systems engineering*

---

## Table of Contents

1. **Foundation: Understanding the Machine**
2. **Memory Architecture & Management**
3. **Process & Thread Management**
4. **File Systems & I/O**
5. **Inter-Process Communication (IPC)**
6. **Synchronization Primitives**
7. **Network Programming**
8. **System Calls Deep Dive**
9. **Performance & Optimization**
10. **Security & Isolation**

---

## 1. Foundation: Understanding the Machine

### 1.1 The Computing Stack

```
┌─────────────────────────────────────┐
│      Application Software           │
├─────────────────────────────────────┤
│      System Libraries (libc)        │
├─────────────────────────────────────┤
│      Operating System Kernel        │
├─────────────────────────────────────┤
│      Hardware Abstraction Layer     │
├─────────────────────────────────────┤
│      Physical Hardware              │
│  (CPU, Memory, Devices, Storage)    │
└─────────────────────────────────────┘
```

**System Programming** operates at the boundary between hardware and application software. You're writing code that directly manages hardware resources, implements OS functionality, or provides low-level services to applications.

### 1.2 CPU Architecture Fundamentals

**Key Concepts:**

- **Register**: Ultra-fast storage locations inside the CPU (8-16 general purpose registers typically)
- **Cache Hierarchy**: L1 (fastest, ~1 cycle), L2 (~10 cycles), L3 (~40 cycles), RAM (~100+ cycles)
- **Instruction Pipeline**: Modern CPUs execute multiple instructions simultaneously
- **Privilege Levels**: Ring 0 (kernel) vs Ring 3 (user space)

```
CPU Execution Model:
┌──────────────────────────────────────────┐
│  Fetch → Decode → Execute → Write Back   │
└──────────────────────────────────────────┘
        Pipeline stages (modern CPUs)
```

**Why This Matters:**
- Cache-friendly code runs 100x faster than cache-missing code
- Understanding CPU pipeline helps you avoid branch mispredictions
- Knowing registers helps you write efficient assembly-aware code

### 1.3 Memory Hierarchy

```
Speed ↑  Cost ↑            Access Time        Size
════════════════════════════════════════════════════
Registers                  ~0.3 ns           64-512 bytes
L1 Cache                   ~1 ns             32-64 KB
L2 Cache                   ~3-10 ns          256 KB-2 MB
L3 Cache                   ~10-40 ns         2-64 MB
RAM (DRAM)                 ~100 ns           4-128 GB
SSD                        ~100 μs           256 GB-4 TB
HDD                        ~10 ms            1-16 TB
Network Storage            ~1-100 ms         Unlimited
```

---

## 2. Memory Architecture & Management

### 2.1 Virtual Memory Concept

**Virtual Memory** is an abstraction that gives each process its own isolated address space, even though physical RAM is shared.

```
Process View (Virtual Address Space):
┌─────────────────────┐ 0xFFFFFFFF (4GB on 32-bit)
│   Kernel Space      │ ← Only kernel can access
├─────────────────────┤ 0xC0000000
│   Stack (grows ↓)   │ ← Function calls, local variables
│         ↓           │
│                     │
│         ↑           │
│   Heap (grows ↑)    │ ← malloc/new allocations
├─────────────────────┤
│   BSS Segment       │ ← Uninitialized global variables
├─────────────────────┤
│   Data Segment      │ ← Initialized global variables
├─────────────────────┤
│   Text Segment      │ ← Program code (read-only)
└─────────────────────┘ 0x00000000
```

**Key Terms:**
- **Virtual Address**: Address that programs use (illusion of contiguous memory)
- **Physical Address**: Actual location in RAM chips
- **Page**: Fixed-size memory block (typically 4KB)
- **Page Table**: Maps virtual pages → physical frames
- **TLB (Translation Lookaside Buffer)**: Cache for page table entries

### 2.2 Memory Management in C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

/* 
 * Memory Allocation Strategies Demo
 * Demonstrates: stack, heap, mmap, memory alignment
 */

// Stack allocation - automatic cleanup
void demo_stack_allocation() {
    printf("=== Stack Allocation ===\n");
    int local_var = 42;  // Allocated on function call
    int array[100];      // 400 bytes on stack
    
    printf("Stack variable address: %p\n", (void*)&local_var);
    printf("Stack grows downward: %p > %p? %s\n",
           (void*)&local_var, (void*)&array,
           (void*)&local_var > (void*)&array ? "yes" : "no");
    // When function returns, these are automatically freed
}

// Heap allocation - manual management required
void demo_heap_allocation() {
    printf("\n=== Heap Allocation ===\n");
    
    // Basic allocation
    int* heap_var = malloc(sizeof(int));
    if (heap_var == NULL) {
        fprintf(stderr, "Allocation failed!\n");
        return;
    }
    *heap_var = 100;
    
    printf("Heap variable address: %p\n", (void*)heap_var);
    
    // Array allocation - two methods
    int* array1 = malloc(10 * sizeof(int));      // Uninitialized
    int* array2 = calloc(10, sizeof(int));        // Zero-initialized
    
    printf("malloc'd array: %d %d %d\n", array1[0], array1[1], array1[2]);
    printf("calloc'd array: %d %d %d\n", array2[0], array2[1], array2[2]);
    
    // Reallocation - resize memory
    array1 = realloc(array1, 20 * sizeof(int));
    
    // CRITICAL: Must free to avoid memory leaks
    free(heap_var);
    free(array1);
    free(array2);
}

// Memory alignment matters for performance
void demo_alignment() {
    printf("\n=== Memory Alignment ===\n");
    
    struct unaligned {
        char c;     // 1 byte
        int i;      // 4 bytes
        char d;     // 1 byte
    } unaligned_example;
    
    struct aligned {
        int i;      // 4 bytes
        char c;     // 1 byte
        char d;     // 1 byte
    } aligned_example;
    
    printf("Unaligned struct size: %zu (padding added)\n", 
           sizeof(unaligned_example));
    printf("Aligned struct size: %zu (more efficient)\n", 
           sizeof(aligned_example));
    
    // Most CPUs require aligned access for performance
    // Misaligned access can be 2-10x slower or cause crashes
}

// Direct memory mapping - bypassing malloc
void demo_mmap() {
    printf("\n=== Memory Mapping (mmap) ===\n");
    
    size_t size = 4096;  // One page
    
    // Allocate memory directly from OS
    void* addr = mmap(
        NULL,                  // Let OS choose address
        size,                  // Size to allocate
        PROT_READ | PROT_WRITE,// Permissions
        MAP_PRIVATE | MAP_ANONYMOUS,  // Private, not backed by file
        -1,                    // No file descriptor
        0                      // No offset
    );
    
    if (addr == MAP_FAILED) {
        perror("mmap failed");
        return;
    }
    
    printf("mmap allocated at: %p\n", addr);
    printf("Page size: %ld bytes\n", sysconf(_SC_PAGESIZE));
    
    // Use the memory
    strcpy((char*)addr, "Hello from mapped memory!");
    printf("Content: %s\n", (char*)addr);
    
    // Release back to OS
    munmap(addr, size);
}

// Memory leak demonstration
void demonstrate_leak() {
    printf("\n=== Memory Leak Example ===\n");
    
    for (int i = 0; i < 5; i++) {
        int* leak = malloc(1024 * 1024);  // 1MB each iteration
        printf("Allocated 1MB (iteration %d)\n", i);
        // BUG: Never freed! Memory leaked.
    }
    
    printf("5MB leaked - use valgrind to detect this!\n");
    printf("Run: valgrind --leak-check=full ./program\n");
}

// Proper memory management pattern
typedef struct {
    int* data;
    size_t size;
} SafeArray;

SafeArray* create_array(size_t size) {
    SafeArray* arr = malloc(sizeof(SafeArray));
    if (arr == NULL) return NULL;
    
    arr->data = malloc(size * sizeof(int));
    if (arr->data == NULL) {
        free(arr);  // Cleanup on failure
        return NULL;
    }
    
    arr->size = size;
    return arr;
}

void destroy_array(SafeArray* arr) {
    if (arr != NULL) {
        free(arr->data);  // Free inner allocation first
        free(arr);        // Then outer
    }
}

int main() {
    demo_stack_allocation();
    demo_heap_allocation();
    demo_alignment();
    demo_mmap();
    demonstrate_leak();
    
    // Proper pattern
    printf("\n=== Proper Resource Management ===\n");
    SafeArray* arr = create_array(100);
    if (arr != NULL) {
        printf("Created safe array of size %zu\n", arr->size);
        destroy_array(arr);
        printf("Cleaned up successfully\n");
    }
    
    return 0;
}
**Example: Understanding malloc internals**

### 2.3 Memory Management in Rust

**The Ownership Model**: Rust's revolutionary approach to memory safety.

```rust
/*
 * Rust Memory Management: Zero-Cost Abstractions
 * 
 * Core Principles:
 * 1. Each value has exactly ONE owner
 * 2. When owner goes out of scope, value is dropped
 * 3. Ownership can be transferred (move) or temporarily borrowed
 */

use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

// === OWNERSHIP BASICS ===

fn ownership_demo() {
    println!("=== Ownership Rules ===");
    
    // Stack allocation - Copy types
    let x = 5;
    let y = x;  // Copy (integers implement Copy trait)
    println!("x={}, y={} (both valid, Copy trait)", x, y);
    
    // Heap allocation - Move semantics
    let s1 = String::from("hello");
    let s2 = s1;  // s1 MOVED to s2, s1 is now invalid
    // println!("{}", s1);  // ERROR: value borrowed after move
    println!("s2={} (s1 moved, no longer valid)", s2);
}

// === BORROWING (References) ===

fn borrowing_demo() {
    println!("\n=== Borrowing Rules ===");
    
    let mut data = vec![1, 2, 3, 4, 5];
    
    // Immutable borrow (can have multiple)
    let ref1 = &data;
    let ref2 = &data;
    println!("Shared refs: {:?} {:?}", ref1, ref2);
    
    // Mutable borrow (exclusive access)
    let ref_mut = &mut data;
    ref_mut.push(6);
    println!("Mutable ref: {:?}", ref_mut);
    
    // Can't have mutable + immutable borrows simultaneously
    // let ref3 = &data;  // ERROR: already borrowed as mutable
}

// === LIFETIMES ===

// Lifetime annotations tell compiler how long references live
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    // Return value lifetime tied to input lifetimes
    if x.len() > y.len() { x } else { y }
}

fn lifetime_demo() {
    println!("\n=== Lifetimes ===");
    
    let string1 = String::from("long string");
    {
        let string2 = String::from("short");
        let result = longest(&string1, &string2);
        println!("Longest: {}", result);
    }
    // string2 dropped here, but string1 still valid
}

// === SMART POINTERS ===

use std::rc::Rc;
use std::cell::RefCell;

fn smart_pointers_demo() {
    println!("\n=== Smart Pointers ===");
    
    // Box: heap allocation, single owner
    let boxed = Box::new(42);
    println!("Boxed value: {}", boxed);
    
    // Rc: Reference counted, multiple owners (not thread-safe)
    let rc1 = Rc::new(vec![1, 2, 3]);
    let rc2 = Rc::clone(&rc1);  // Increment ref count
    println!("Rc count: {}", Rc::strong_count(&rc1));
    
    // RefCell: Interior mutability (runtime borrow checking)
    let refcell = RefCell::new(5);
    *refcell.borrow_mut() += 10;
    println!("RefCell value: {}", refcell.borrow());
}

// === UNSAFE RUST & RAW ALLOCATION ===

fn unsafe_allocation_demo() {
    println!("\n=== Unsafe Raw Allocation ===");
    
    unsafe {
        // Allocate 1024 bytes aligned to 8
        let layout = Layout::from_size_align(1024, 8).unwrap();
        let ptr = alloc(layout);
        
        if ptr.is_null() {
            panic!("Allocation failed!");
        }
        
        // Write to raw memory
        ptr::write(ptr as *mut u64, 0xDEADBEEF);
        
        // Read from raw memory
        let value = ptr::read(ptr as *const u64);
        println!("Raw memory value: 0x{:X}", value);
        
        // MUST manually deallocate
        dealloc(ptr, layout);
    }
}

// === ZERO-COPY STRING SLICING ===

fn zero_copy_demo() {
    println!("\n=== Zero-Copy Operations ===");
    
    let data = String::from("Hello, World!");
    
    // String slices are just pointers + length (no allocation)
    let hello = &data[0..5];    // Pointer to index 0
    let world = &data[7..12];   // Pointer to index 7
    
    println!("Original: {}", data);
    println!("Slice 1: {} (no copy)", hello);
    println!("Slice 2: {} (no copy)", world);
}

// === CUSTOM DROP IMPLEMENTATION ===

struct Resource {
    id: u32,
}

impl Drop for Resource {
    fn drop(&mut self) {
        println!("Dropping resource {}", self.id);
        // Cleanup code here (close files, release locks, etc.)
    }
}

fn drop_demo() {
    println!("\n=== Custom Drop (RAII) ===");
    
    {
        let _r1 = Resource { id: 1 };
        let _r2 = Resource { id: 2 };
        println!("Resources created");
    }  // Automatic cleanup here in reverse order
    
    println!("Resources cleaned up");
}

// === PERFORMANCE COMPARISON ===

use std::time::Instant;

fn performance_comparison() {
    println!("\n=== Performance: Ownership vs Cloning ===");
    
    let large_vec: Vec<i32> = (0..1_000_000).collect();
    
    // Move (zero-cost)
    let start = Instant::now();
    let moved = large_vec;
    println!("Move: {:?} (just pointer transfer)", start.elapsed());
    
    // Clone (expensive)
    let start = Instant::now();
    let cloned = moved.clone();
    println!("Clone: {:?} (full memory copy)", start.elapsed());
    
    // Borrow (zero-cost)
    let start = Instant::now();
    let borrowed = &cloned;
    println!("Borrow: {:?} (just pointer)", start.elapsed());
    
    println!("Lengths: {} {}", borrowed.len(), cloned.len());
}

// === MEMORY LAYOUT CONTROL ===

#[repr(C)]  // Use C memory layout
struct CCompatible {
    x: u32,
    y: u32,
}

#[repr(packed)]  // No padding
struct Packed {
    a: u8,
    b: u32,
}

fn layout_demo() {
    println!("\n=== Memory Layout Control ===");
    println!("CCompatible size: {}", std::mem::size_of::<CCompatible>());
    println!("Packed size: {}", std::mem::size_of::<Packed>());
}

fn main() {
    ownership_demo();
    borrowing_demo();
    lifetime_demo();
    smart_pointers_demo();
    unsafe_allocation_demo();
    zero_copy_demo();
    drop_demo();
    performance_comparison();
    layout_demo();
    
    println!("\n=== Key Takeaways ===");
    println!("• Rust enforces memory safety at compile time");
    println!("• Zero runtime overhead for safety guarantees");
    println!("• Ownership = automatic resource management (RAII)");
    println!("• Borrowing = safe aliasing without copying");
}
```

### 2.4 Memory Management in Go

package main

import (
	"fmt"
	"runtime"
	"time"
	"unsafe"
)

/*
 * Go Memory Management
 * 
 * Go uses automatic garbage collection with escape analysis
 * Compiler decides: stack allocation (fast) vs heap allocation (GC'd)
 */

// === STACK VS HEAP ALLOCATION ===

// Stack allocated - doesn't escape function
func stackAllocation() *int {
	x := 42
	return &x  // ESCAPE: returned pointer forces heap allocation
}

// Stack allocated - local only
func pureStack() {
	x := 42
	y := x + 10
	_ = y  // Used locally, stays on stack
}

// Heap allocated - escapes via interface
func heapViaInterface() interface{} {
	x := 42
	return x  // ESCAPE: interface{} causes heap allocation
}

// === ESCAPE ANALYSIS DEMO ===

func escapeAnalysisDemo() {
	fmt.Println("=== Escape Analysis ===")
	
	// Check with: go build -gcflags='-m' program.go
	// Shows compiler decisions about stack vs heap
	
	p := stackAllocation()
	fmt.Printf("Value: %d (heap allocated)\n", *p)
	
	pureStack()
	fmt.Println("pureStack() uses stack only")
	
	i := heapViaInterface()
	fmt.Printf("Interface value: %v (heap allocated)\n", i)
}

// === MEMORY STATISTICS ===

func memoryStats() {
	fmt.Println("\n=== Memory Statistics ===")
	
	var m runtime.MemStats
	
	// Before allocation
	runtime.ReadMemStats(&m)
	fmt.Printf("Before: Alloc=%v MB, TotalAlloc=%v MB\n",
		m.Alloc/1024/1024, m.TotalAlloc/1024/1024)
	
	// Allocate 10MB
	data := make([]byte, 10*1024*1024)
	_ = data
	
	runtime.ReadMemStats(&m)
	fmt.Printf("After:  Alloc=%v MB, TotalAlloc=%v MB\n",
		m.Alloc/1024/1024, m.TotalAlloc/1024/1024)
	fmt.Printf("NumGC: %v\n", m.NumGC)
}

// === GARBAGE COLLECTION BEHAVIOR ===

func gcDemo() {
	fmt.Println("\n=== Garbage Collection ===")
	
	// Force GC
	runtime.GC()
	
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	before := m.NumGC
	
	// Create garbage
	for i := 0; i < 1000; i++ {
		_ = make([]byte, 1024*1024)  // 1MB each, immediately garbage
	}
	
	runtime.GC()
	runtime.ReadMemStats(&m)
	after := m.NumGC
	
	fmt.Printf("GC runs: %d -> %d (triggered %d times)\n",
		before, after, after-before)
	fmt.Printf("Pause time: %v ns\n", m.PauseNs[(m.NumGC+255)%256])
}

// === SYNC.POOL - OBJECT REUSE ===

type Buffer struct {
	data []byte
}

var bufferPool = sync.Pool{
	New: func() interface{} {
		return &Buffer{
			data: make([]byte, 0, 1024),
		}
	},
}

func poolDemo() {
	fmt.Println("\n=== sync.Pool (Object Reuse) ===")
	
	// Get from pool (or create new)
	buf := bufferPool.Get().(*Buffer)
	buf.data = append(buf.data, "hello"...)
	
	fmt.Printf("Using buffer: %s\n", buf.data)
	
	// Reset and return to pool
	buf.data = buf.data[:0]
	bufferPool.Put(buf)
	
	fmt.Println("Buffer returned to pool for reuse")
}

// === MEMORY ALIGNMENT ===

func alignmentDemo() {
	fmt.Println("\n=== Memory Alignment ===")
	
	type Unaligned struct {
		a bool   // 1 byte
		b int64  // 8 bytes
		c bool   // 1 byte
	}
	
	type Aligned struct {
		b int64  // 8 bytes
		a bool   // 1 byte
		c bool   // 1 byte
	}
	
	fmt.Printf("Unaligned size: %d bytes (with padding)\n",
		unsafe.Sizeof(Unaligned{}))
	fmt.Printf("Aligned size: %d bytes (optimized)\n",
		unsafe.Sizeof(Aligned{}))
}

// === SLICE INTERNALS ===

func sliceInternals() {
	fmt.Println("\n=== Slice Internals ===")
	
	// Slice header: pointer + len + cap
	s := make([]int, 5, 10)
	
	fmt.Printf("Slice: len=%d, cap=%d\n", len(s), cap(s))
	fmt.Printf("Header size: %d bytes\n", unsafe.Sizeof(s))
	
	// Slicing doesn't copy data
	s2 := s[1:3]
	fmt.Printf("Sub-slice: len=%d, cap=%d (shares backing array)\n",
		len(s2), cap(s2))
	
	// Modifying s2 affects s
	s2[0] = 999
	fmt.Printf("s[1]=%d (modified via s2)\n", s[1])
}

// === POINTER ARITHMETIC (UNSAFE) ===

func unsafePointers() {
	fmt.Println("\n=== Unsafe Pointers ===")
	
	arr := [5]int{1, 2, 3, 4, 5}
	ptr := unsafe.Pointer(&arr[0])
	
	// Pointer arithmetic (dangerous!)
	for i := 0; i < 5; i++ {
		// Get pointer to arr[i]
		elemPtr := (*int)(unsafe.Pointer(
			uintptr(ptr) + uintptr(i)*unsafe.Sizeof(arr[0])))
		fmt.Printf("arr[%d] = %d\n", i, *elemPtr)
	}
	
	fmt.Println("WARNING: Unsafe pointer arithmetic bypasses safety!")
}

// === FINALIZERS ===

type Resource struct {
	id int
}

func (r *Resource) Close() {
	fmt.Printf("Closing resource %d\n", r.id)
}

func finalizerDemo() {
	fmt.Println("\n=== Finalizers ===")
	
	r := &Resource{id: 42}
	
	// Register cleanup function (runs when GC collects object)
	runtime.SetFinalizer(r, func(r *Resource) {
		r.Close()
	})
	
	r = nil  // Make eligible for GC
	runtime.GC()
	time.Sleep(100 * time.Millisecond)  // Give GC time to run
	
	fmt.Println("Note: Finalizers are unpredictable, use defer instead!")
}

// === MEMORY-EFFICIENT PATTERNS ===

func efficientPatterns() {
	fmt.Println("\n=== Memory-Efficient Patterns ===")
	
	// Pre-allocate with known size
	items := make([]int, 0, 1000)  // Capacity 1000, length 0
	for i := 0; i < 1000; i++ {
		items = append(items, i)  // No reallocation needed
	}
	
	fmt.Println("Pre-allocated slice: no reallocation overhead")
	
	// String builder for concatenation
	var builder strings.Builder
	builder.Grow(100)  // Pre-allocate
	for i := 0; i < 10; i++ {
		builder.WriteString("x")
	}
	result := builder.String()
	
	fmt.Printf("Efficient string building: %s\n", result)
}

// === GC TUNING ===

func gcTuning() {
	fmt.Println("\n=== GC Tuning ===")
	
	// GOGC=100 (default): GC when heap doubles
	// GOGC=200: GC when heap triples (less frequent, more memory)
	// GOGC=50: GC more aggressively (less memory, more CPU)
	
	fmt.Println("GC tuning via GOGC environment variable:")
	fmt.Println("  GOGC=100 (default) - balance")
	fmt.Println("  GOGC=200 - less GC, more memory")
	fmt.Println("  GOGC=50 - more GC, less memory")
	
	// Can also set programmatically
	debug.SetGCPercent(100)
}

func main() {
	escapeAnalysisDemo()
	memoryStats()
	gcDemo()
	poolDemo()
	alignmentDemo()
	sliceInternals()
	unsafePointers()
	finalizerDemo()
	efficientPatterns()
	gcTuning()
	
	fmt.Println("\n=== Key Takeaways ===")
	fmt.Println("• Go manages memory automatically via GC")
	fmt.Println("• Escape analysis determines stack vs heap")
	fmt.Println("• Use tools: go build -gcflags='-m' for analysis")
	fmt.Println("• Optimize: pre-allocate, use sync.Pool, avoid escapes")
}

---

## 3. Process & Thread Management

### 3.1 What is a Process?

A **process** is an instance of a running program. Each process has:

```
Process Structure:
┌────────────────────────────────┐
│  Process Control Block (PCB)   │
├────────────────────────────────┤
│  • Process ID (PID)            │
│  • Parent PID (PPID)           │
│  • Process state               │
│  • CPU registers               │
│  • Memory pointers             │
│  • Open file descriptors       │
│  • Signal handlers             │
│  • Priority/scheduling info    │
└────────────────────────────────┘
```

**Process States:**
```
    ┌─────────┐
    │   NEW   │ ← Process being created
    └────┬────┘
         ↓
    ┌─────────┐
    │  READY  │ ← Waiting for CPU
    └────┬────┘
         ↓
    ┌─────────┐
    │ RUNNING │ ← Executing on CPU
    └────┬────┘
         ↓
    ┌─────────┐      ┌─────────┐
    │ WAITING │ ←──→ │ BLOCKED │ ← Waiting for I/O
    └────┬────┘      └─────────┘
         ↓
    ┌─────────┐
    │TERMINATED│ ← Process finished
    └─────────┘
```

### 3.2 Process Creation (fork/exec model)

**In Unix/Linux**, new processes are created using `fork()` + `exec()`:

```
Fork Process:
Parent Process          Child Process
┌──────────┐           ┌──────────┐
│ PID: 100 │  fork()   │ PID: 101 │
│  Code    │  ──────→  │  Code    │ (copy)
│  Data    │           │  Data    │ (copy)
│  Stack   │           │  Stack   │ (copy)
└──────────┘           └──────────┘
     │                      │
     │                      │ exec()
     │                      ↓
     │                 ┌──────────┐
     │                 │New Program│
     └─────────────────│  Loaded  │
                       └──────────┘
```

### 3.3 Threads vs Processes

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include <string.h>

/*
 * Process Management in C
 * System calls: fork, exec, wait, exit, signal
 */

// === BASIC FORK ===

void demo_fork() {
    printf("=== Fork Demo ===\n");
    printf("Parent PID: %d\n", getpid());
    
    pid_t pid = fork();  // Creates child process
    
    if (pid < 0) {
        // Fork failed
        perror("fork failed");
        return;
    } else if (pid == 0) {
        // Child process (pid == 0)
        printf("Child:  PID=%d, Parent PID=%d\n", 
               getpid(), getppid());
        printf("Child:  Doing child work...\n");
        sleep(1);
        printf("Child:  Exiting\n");
        exit(0);  // Child terminates
    } else {
        // Parent process (pid == child's PID)
        printf("Parent: Created child with PID=%d\n", pid);
        printf("Parent: Waiting for child...\n");
        
        int status;
        wait(&status);  // Wait for child to finish
        
        if (WIFEXITED(status)) {
            printf("Parent: Child exited with status %d\n",
                   WEXITSTATUS(status));
        }
    }
}

// === FORK + EXEC ===

void demo_exec() {
    printf("\n=== Fork + Exec Demo ===\n");
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child: replace with new program
        printf("Child: Executing 'ls -l'\n");
        
        char *args[] = {"ls", "-l", "/tmp", NULL};
        execvp("ls", args);  // Replace process image
        
        // Only reaches here if exec fails
        perror("exec failed");
        exit(1);
    } else {
        // Parent waits
        wait(NULL);
        printf("Parent: Child process completed\n");
    }
}

// === MULTIPLE CHILDREN ===

void demo_multiple_children() {
    printf("\n=== Multiple Children ===\n");
    
    #define NUM_CHILDREN 3
    
    for (int i = 0; i < NUM_CHILDREN; i++) {
        pid_t pid = fork();
        
        if (pid == 0) {
            // Child process
            printf("Child %d: PID=%d\n", i, getpid());
            sleep(i + 1);  // Different sleep times
            printf("Child %d: Done\n", i);
            exit(i);  // Exit with different codes
        }
    }
    
    // Parent waits for all children
    for (int i = 0; i < NUM_CHILDREN; i++) {
        int status;
        pid_t child_pid = wait(&status);
        printf("Parent: Child %d exited with status %d\n",
               child_pid, WEXITSTATUS(status));
    }
}

// === ZOMBIE PROCESSES ===

void demo_zombie() {
    printf("\n=== Zombie Process Demo ===\n");
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child exits immediately
        printf("Child: Exiting (will become zombie)\n");
        exit(0);
    } else {
        printf("Parent: Child created, sleeping (child is zombie)...\n");
        printf("        Run 'ps aux | grep Z' in another terminal\n");
        sleep(5);  // Child is zombie during this time
        
        wait(NULL);  // Reap zombie
        printf("Parent: Zombie reaped\n");
    }
}

// === ORPHAN PROCESSES ===

void demo_orphan() {
    printf("\n=== Orphan Process Demo ===\n");
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child sleeps while parent exits
        printf("Child: Sleeping...\n");
        sleep(3);
        printf("Child: Awake! My parent PID is now: %d (init/systemd)\n",
               getppid());
        exit(0);
    } else {
        printf("Parent: Exiting immediately (child becomes orphan)\n");
        exit(0);  // Parent dies, child adopted by init
    }
}

// === SIGNAL HANDLING ===

volatile sig_atomic_t signal_received = 0;

void signal_handler(int sig) {
    if (sig == SIGUSR1) {
        signal_received = 1;
    }
}

void demo_signals() {
    printf("\n=== Signal Handling ===\n");
    
    // Install signal handler
    signal(SIGUSR1, signal_handler);
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Child sends signal to parent
        printf("Child: Sleeping 1 second...\n");
        sleep(1);
        printf("Child: Sending SIGUSR1 to parent (%d)\n", getppid());
        kill(getppid(), SIGUSR1);
        exit(0);
    } else {
        // Parent waits for signal
        printf("Parent: Waiting for signal...\n");
        
        while (!signal_received) {
            pause();  // Sleep until signal
        }
        
        printf("Parent: Received SIGUSR1!\n");
        wait(NULL);
    }
}

// === PROCESS TERMINATION ===

void demo_exit_handlers() {
    printf("\n=== Exit Handlers ===\n");
    
    void cleanup1() {
        printf("Cleanup handler 1 called\n");
    }
    
    void cleanup2() {
        printf("Cleanup handler 2 called\n");
    }
    
    // Register exit handlers (called in reverse order)
    atexit(cleanup1);
    atexit(cleanup2);
    
    printf("Handlers registered, exiting...\n");
}

// === PROCESS GROUPS ===

void demo_process_groups() {
    printf("\n=== Process Groups ===\n");
    
    pid_t pgid = getpgrp();
    printf("Process group ID: %d\n", pgid);
    
    pid_t pid = fork();
    
    if (pid == 0) {
        // Create new process group
        setpgid(0, 0);  // Set child's PGID to its PID
        printf("Child: New process group: %d\n", getpgrp());
        
        // Can send signals to entire group
        // kill(-getpgrp(), SIGTERM);
        
        exit(0);
    } else {
        wait(NULL);
        printf("Parent: Still in group: %d\n", getpgrp());
    }
}

// === WAITPID VARIATIONS ===

void demo_waitpid() {
    printf("\n=== waitpid Variations ===\n");
    
    pid_t pid1 = fork();
    if (pid1 == 0) {
        sleep(2);
        exit(1);
    }
    
    pid_t pid2 = fork();
    if (pid2 == 0) {
        sleep(1);
        exit(2);
    }
    
    // Wait for specific child
    int status;
    pid_t finished = waitpid(pid2, &status, 0);
    printf("Child %d finished first with status %d\n",
           finished, WEXITSTATUS(status));
    
    // Non-blocking wait
    while (1) {
        pid_t result = waitpid(-1, &status, WNOHANG);
        if (result == 0) {
            printf("No children ready yet...\n");
            sleep(1);
        } else if (result > 0) {
            printf("Child %d finished with status %d\n",
                   result, WEXITSTATUS(status));
            break;
        } else {
            break;  // No more children
        }
    }
}

int main() {
    demo_fork();
    demo_exec();
    demo_multiple_children();
    demo_zombie();
    
    // demo_orphan();  // Commented: parent exits
    
    demo_signals();
    demo_process_groups();
    demo_waitpid();
    
    printf("\n=== Exiting main (exit handlers will run) ===\n");
    demo_exit_handlers();
    
    return 0;
}

```
Process vs Thread:

PROCESS                           THREAD
┌──────────────────┐             ┌──────────────────┐
│  Separate memory │             │  Shared memory   │
│  Heavy creation  │             │  Light creation  │
│  IPC required    │             │  Direct sharing  │
│  Safer isolation │             │  Risk of races   │
└──────────────────┘             └──────────────────┘

Multi-Process:                    Multi-Thread:
┌─────────┐  ┌─────────┐         ┌─────────────────┐
│ Process │  │ Process │         │     Process     │
│┌───────┐│  │┌───────┐│         │┌───┐ ┌───┐ ┌───┐│
││Memory ││  ││Memory ││         ││Thr│ │Thr│ │Thr││
│└───────┘│  │└───────┘│         │└───┘ └───┘ └───┘│
└─────────┘  └─────────┘         │  Shared Memory  │
                                  └─────────────────┘
```

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

/*
 * POSIX Threads (pthreads) - Multithreading in C
 * 
 * Threads share: code, data, heap, open files
 * Threads have separate: stack, registers, thread ID
 */

// === BASIC THREAD CREATION ===

void* thread_function(void* arg) {
    int thread_num = *(int*)arg;
    printf("Thread %d: Started (TID=%lu)\n", 
           thread_num, pthread_self());
    
    sleep(1);
    
    printf("Thread %d: Finishing\n", thread_num);
    return NULL;
}

void demo_basic_threads() {
    printf("=== Basic Thread Creation ===\n");
    
    pthread_t threads[3];
    int thread_args[3];
    
    // Create threads
    for (int i = 0; i < 3; i++) {
        thread_args[i] = i;
        int result = pthread_create(&threads[i], NULL, 
                                    thread_function, &thread_args[i]);
        if (result != 0) {
            fprintf(stderr, "Thread creation failed: %s\n", 
                    strerror(result));
            return;
        }
    }
    
    // Wait for all threads
    for (int i = 0; i < 3; i++) {
        pthread_join(threads[i], NULL);
        printf("Main: Thread %d joined\n", i);
    }
}

// === THREAD RETURN VALUES ===

void* computation_thread(void* arg) {
    int n = *(int*)arg;
    int* result = malloc(sizeof(int));
    *result = n * n;
    
    printf("Thread: Computing %d^2 = %d\n", n, *result);
    return result;  // Return pointer to result
}

void demo_return_values() {
    printf("\n=== Thread Return Values ===\n");
    
    pthread_t thread;
    int input = 42;
    
    pthread_create(&thread, NULL, computation_thread, &input);
    
    void* return_value;
    pthread_join(thread, &return_value);
    
    int result = *(int*)return_value;
    printf("Main: Received result: %d\n", result);
    
    free(return_value);  // Clean up
}

// === RACE CONDITIONS ===

int shared_counter = 0;

void* unsafe_increment(void* arg) {
    for (int i = 0; i < 100000; i++) {
        shared_counter++;  // RACE CONDITION!
        // This is actually: load, increment, store
        // Can be interleaved by multiple threads
    }
    return NULL;
}

void demo_race_condition() {
    printf("\n=== Race Condition Demo ===\n");
    
    shared_counter = 0;
    pthread_t threads[10];
    
    for (int i = 0; i < 10; i++) {
        pthread_create(&threads[i], NULL, unsafe_increment, NULL);
    }
    
    for (int i = 0; i < 10; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("Expected: 1000000\n");
    printf("Actual:   %d (likely wrong due to races)\n", shared_counter);
}

// === MUTEX (MUTUAL EXCLUSION) ===

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int safe_counter = 0;

void* safe_increment(void* arg) {
    for (int i = 0; i < 100000; i++) {
        pthread_mutex_lock(&mutex);    // CRITICAL SECTION START
        safe_counter++;
        pthread_mutex_unlock(&mutex);  // CRITICAL SECTION END
    }
    return NULL;
}

void demo_mutex() {
    printf("\n=== Mutex Protection ===\n");
    
    safe_counter = 0;
    pthread_t threads[10];
    
    for (int i = 0; i < 10; i++) {
        pthread_create(&threads[i], NULL, safe_increment, NULL);
    }
    
    for (int i = 0; i < 10; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("Expected: 1000000\n");
    printf("Actual:   %d (correct with mutex)\n", safe_counter);
    
    pthread_mutex_destroy(&mutex);
}

// === DEADLOCK EXAMPLE ===

pthread_mutex_t lock1 = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t lock2 = PTHREAD_MUTEX_INITIALIZER;

void* thread_a(void* arg) {
    printf("Thread A: Acquiring lock1...\n");
    pthread_mutex_lock(&lock1);
    sleep(1);  // Simulate work
    
    printf("Thread A: Acquiring lock2...\n");
    pthread_mutex_lock(&lock2);  // DEADLOCK HERE
    
    printf("Thread A: Got both locks!\n");
    
    pthread_mutex_unlock(&lock2);
    pthread_mutex_unlock(&lock1);
    return NULL;
}

void* thread_b(void* arg) {
    printf("Thread B: Acquiring lock2...\n");
    pthread_mutex_lock(&lock2);
    sleep(1);  // Simulate work
    
    printf("Thread B: Acquiring lock1...\n");
    pthread_mutex_lock(&lock1);  // DEADLOCK HERE
    
    printf("Thread B: Got both locks!\n");
    
    pthread_mutex_unlock(&lock1);
    pthread_mutex_unlock(&lock2);
    return NULL;
}

void demo_deadlock() {
    printf("\n=== Deadlock Demo (commented out - would hang) ===\n");
    printf("Thread A: lock1 → lock2\n");
    printf("Thread B: lock2 → lock1\n");
    printf("Result: DEADLOCK (both wait forever)\n");
    
    /*
    pthread_t ta, tb;
    pthread_create(&ta, NULL, thread_a, NULL);
    pthread_create(&tb, NULL, thread_b, NULL);
    pthread_join(ta, NULL);
    pthread_join(tb, NULL);
    */
}

// === CONDITION VARIABLES ===

pthread_mutex_t cond_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t condition = PTHREAD_COND_INITIALIZER;
int data_ready = 0;

void* producer(void* arg) {
    sleep(2);  // Simulate slow data generation
    
    pthread_mutex_lock(&cond_mutex);
    printf("Producer: Data ready, signaling consumer\n");
    data_ready = 1;
    pthread_cond_signal(&condition);  // Wake up consumer
    pthread_mutex_unlock(&cond_mutex);
    
    return NULL;
}

void* consumer(void* arg) {
    pthread_mutex_lock(&cond_mutex);
    
    while (!data_ready) {
        printf("Consumer: Waiting for data...\n");
        pthread_cond_wait(&condition, &cond_mutex);
        // Atomically: unlock mutex, wait for signal, re-lock mutex
    }
    
    printf("Consumer: Data received!\n");
    pthread_mutex_unlock(&cond_mutex);
    
    return NULL;
}

void demo_condition_variable() {
    printf("\n=== Condition Variables ===\n");
    
    pthread_t prod, cons;
    
    pthread_create(&cons, NULL, consumer, NULL);
    pthread_create(&prod, NULL, producer, NULL);
    
    pthread_join(cons, NULL);
    pthread_join(prod, NULL);
    
    pthread_mutex_destroy(&cond_mutex);
    pthread_cond_destroy(&condition);
}

// === THREAD-LOCAL STORAGE ===

__thread int thread_local_var = 0;

void* tls_thread(void* arg) {
    int id = *(int*)arg;
    thread_local_var = id * 100;
    
    printf("Thread %d: thread_local_var = %d\n", id, thread_local_var);
    sleep(1);
    printf("Thread %d: thread_local_var still = %d\n", id, thread_local_var);
    
    return NULL;
}

void demo_thread_local() {
    printf("\n=== Thread-Local Storage ===\n");
    
    pthread_t threads[3];
    int ids[3] = {1, 2, 3};
    
    for (int i = 0; i < 3; i++) {
        pthread_create(&threads[i], NULL, tls_thread, &ids[i]);
    }
    
    for (int i = 0; i < 3; i++) {
        pthread_join(threads[i], NULL);
    }
}

// === THREAD ATTRIBUTES ===

void demo_thread_attributes() {
    printf("\n=== Thread Attributes ===\n");
    
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    
    // Set detached state (no join needed)
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
    
    // Set stack size
    size_t stacksize = 2 * 1024 * 1024;  // 2MB
    pthread_attr_setstacksize(&attr, stacksize);
    
    printf("Thread attributes set: detached, 2MB stack\n");
    
    pthread_attr_destroy(&attr);
}

int main() {
    demo_basic_threads();
    demo_return_values();
    demo_race_condition();
    demo_mutex();
    demo_deadlock();
    demo_condition_variable();
    demo_thread_local();
    demo_thread_attributes();
    
    printf("\n=== Key Takeaways ===\n");
    printf("• Threads share memory - fast but risky\n");
    printf("• Always protect shared data with mutexes\n");
    printf("• Avoid deadlocks: consistent lock ordering\n");
    printf("• Use condition variables for synchronization\n");
    
    return 0;
}

---

## 4. File Systems & I/O

### 4.1 File System Hierarchy

```
Linux/Unix File System:
┌────────────────────────────────────┐
│           / (root)                 │
├────┬───────┬────────┬──────────────┤
│/bin│ /etc  │ /home  │ /dev  │ /proc│
└────┴───────┴────────┴──────────────┘
 │     │       │        │       │
 │     │       │        │       └─> Process info (virtual)
 │     │       │        └─> Device files
 │     │       └─> User home directories
 │     └─> Configuration files
 └─> Essential binaries
```

**Everything is a File** in Unix:
- Regular files: `/home/user/document.txt`
- Directories: `/home/user/`
- Device files: `/dev/sda` (hard drive), `/dev/null` (bit bucket)
- Pipes: `/tmp/mypipe`
- Sockets: `/var/run/docker.sock`
- Symbolic links: `/usr/bin/python -> /usr/bin/python3`

### 4.2 File Descriptors

**File Descriptor**: An integer that represents an open file in a process.

```
File Descriptor Table (per process):
┌────┬──────────────────────┐
│ 0  │ stdin (keyboard)     │
│ 1  │ stdout (screen)      │
│ 2  │ stderr (screen)      │
│ 3  │ /home/user/file.txt  │
│ 4  │ socket connection    │
│... │ ...                  │
└────┴──────────────────────┘
```

### 4.3 I/O Operations

**Two levels of I/O:**
1. **System Call I/O** (unbuffered): `open()`, `read()`, `write()`, `close()`
2. **Standard I/O** (buffered): `fopen()`, `fread()`, `fwrite()`, `fclose()`

```
Buffered I/O Flow:
Application
    ↓ fwrite()
User Buffer (in program)
    ↓ (flush when full)
Kernel Buffer
    ↓ (write to disk)
Physical Disk
```

This guide is getting extensive - I'll continue with the remaining sections. Would you like me to:

1. **Continue with the remaining major sections** (IPC, Synchronization, Network Programming, System Calls, etc.)
2. **Go deeper into any specific topic** you found most interesting
3. **Provide hands-on projects** to practice these concepts
4. **Focus on performance optimization** and advanced techniques

Each major section contains theory + code examples in C, Rust, and Go. I'm tailoring explanations to build your mental models from first principles.

What would serve your mastery journey best right now?