# Array Manipulation: A Complete In-Depth Guide
> Covering internals, all operations, common mistakes, and implementations in C, Go, and Rust

---

## Table of Contents

1. [What Is an Array — The True Mental Model](#1-what-is-an-array--the-true-mental-model)
2. [Memory Layout Internals](#2-memory-layout-internals)
3. [Static vs Dynamic Arrays](#3-static-vs-dynamic-arrays)
4. [Indexing and Access](#4-indexing-and-access)
5. [Traversal Patterns](#5-traversal-patterns)
6. [Insertion Operations](#6-insertion-operations)
7. [Deletion Operations](#7-deletion-operations)
8. [Searching](#8-searching)
9. [Sorting](#9-sorting)
10. [Reversal](#10-reversal)
11. [Rotation](#11-rotation)
12. [Sliding Window Technique](#12-sliding-window-technique)
13. [Two-Pointer Technique](#13-two-pointer-technique)
14. [Prefix Sum and Difference Array](#14-prefix-sum-and-difference-array)
15. [Subarray Operations](#15-subarray-operations)
16. [Merging Arrays](#16-merging-arrays)
17. [Partitioning](#17-partitioning)
18. [Matrix (2D Array) Operations](#18-matrix-2d-array-operations)
19. [Dynamic Array Internals (Vec, Slice, Vec in Rust)](#19-dynamic-array-internals)
20. [Cache Behavior and Memory Access Patterns](#20-cache-behavior-and-memory-access-patterns)
21. [Common Mistakes — Exhaustive List](#21-common-mistakes--exhaustive-list)
22. [Complexity Reference Table](#22-complexity-reference-table)

---

## 1. What Is an Array — The True Mental Model

An array is a **contiguous block of memory** where every element occupies the same fixed amount of space. This single constraint is the source of everything: its strengths, its weaknesses, every operation's complexity, and every mistake you can make.

The mental model most beginners have — "a list of boxes with numbers" — is incomplete. The correct mental model is:

```
A named pointer to a base address in memory,
combined with a known element size and a known count.
```

That is literally all an array is. Everything else (indexing, iteration, slicing) is arithmetic on that pointer.

```
Array: int arr[5]

Name:  arr
Base:  0x1000          (some address in memory)
Size:  sizeof(int) = 4 bytes
Count: 5 elements

To access arr[i]:
  address = base + (i * element_size)
  address = 0x1000 + (i * 4)
```

This is why:
- Access is O(1): computing one address takes constant time.
- Cache is efficient: data is packed tight, so prefetchers love it.
- Insertion/deletion at the middle is O(n): you must physically shift bytes.

---

## 2. Memory Layout Internals

### 2.1 Flat 1D Array in Memory

```
int arr[6] = {10, 20, 30, 40, 50, 60};

RAM (byte addresses, assuming int = 4 bytes):

  Addr   Bytes              Value
  ─────────────────────────────────────────────────────
  0x1000 [0A 00 00 00]      arr[0] = 10
  0x1004 [14 00 00 00]      arr[1] = 20
  0x1008 [1E 00 00 00]      arr[2] = 30
  0x100C [28 00 00 00]      arr[3] = 40
  0x1010 [32 00 00 00]      arr[4] = 50
  0x1014 [3C 00 00 00]      arr[5] = 60

Index formula:  addr(arr[i]) = 0x1000 + i * 4
```

### 2.2 Stack vs Heap Allocation

```
STACK (fixed-size arrays, local variables)
─────────────────────────────────────────
  High address
  ┌─────────────────────┐
  │   return address    │  ← function call frame
  │   saved registers   │
  │   local variables   │
  │  [arr[4]][arr[3]]   │  ← array lives here, inline
  │  [arr[2]][arr[1]]   │    no pointer indirection
  │  [arr[0]]           │
  └─────────────────────┘
  Low address

  - Allocation: zero cost (just move stack pointer)
  - Deallocation: automatic (on function return)
  - Limit: ~1-8 MB depending on OS

HEAP (dynamic arrays, malloc/new/Box)
─────────────────────────────────────
  Stack frame                    Heap
  ┌────────────────┐             ┌──────────────────────────┐
  │ ptr ──────────────────────► │ [10][20][30][40][50]     │
  │ len = 5        │             │                          │
  │ cap = 8        │             └──────────────────────────┘
  └────────────────┘
    (metadata on stack)            (data on heap)

  - Allocation: system call (mmap/brk), relatively expensive
  - Deallocation: manual (C) or GC/ownership system
  - Size: limited by virtual address space (gigabytes)
```

### 2.3 How the CPU Sees an Array — Cache Lines

```
Cache line = 64 bytes (typical x86-64)

int arr[16];  →  64 bytes exactly → fits in 1 cache line

  Cache Line 0 (64 bytes)
  ┌────────────────────────────────────────────────────────────────┐
  │ arr[0] │ arr[1] │ arr[2] │ arr[3] │ arr[4] │ ... │ arr[15]  │
  └────────────────────────────────────────────────────────────────┘

  When you read arr[0], the CPU fetches the ENTIRE cache line.
  Accessing arr[1..15] after that = ZERO memory latency (L1 hit).

int arr[32];  →  128 bytes → spans 2 cache lines

  Cache Line 0                       Cache Line 1
  ┌────────────────────────────┐     ┌────────────────────────────┐
  │ arr[0] ... arr[15]         │     │ arr[16] ... arr[31]        │
  └────────────────────────────┘     └────────────────────────────┘
```

This is why sequential array access is dramatically faster than linked-list traversal: linked-list nodes are scattered in memory, so every dereference is a potential cache miss.

### 2.4 2D Array Layout: Row-Major vs Column-Major

```
Matrix:
  [ 1  2  3 ]
  [ 4  5  6 ]
  [ 7  8  9 ]

ROW-MAJOR (C, Go, Rust, most languages):
  Memory: [1][2][3][4][5][6][7][8][9]
          row0─────── row1─────── row2───────

  arr[i][j] = base + (i * cols + j) * elem_size

COLUMN-MAJOR (Fortran, MATLAB, Julia):
  Memory: [1][4][7][2][5][8][3][6][9]
          col0─────── col1─────── col2───────

  arr[i][j] = base + (j * rows + i) * elem_size

Implication:
  In C/Go/Rust, iterating row[i][0], row[i][1], row[i][2]... = sequential
  Iterating col[0][j], col[1][j], col[2][j]... = jumping by `cols` elements
  Column-wise traversal of a row-major array is CACHE-UNFRIENDLY.
```

---

## 3. Static vs Dynamic Arrays

### 3.1 Static Array

Fixed size known at compile time. Lives on stack (if local) or in BSS/data segment (if global).

```c
// C
int arr[10];               // stack, uninitialized
int arr[10] = {0};         // stack, zero-initialized
static int arr[10];        // BSS segment, zero-initialized, persists
```

```go
// Go
var arr [10]int            // zero-initialized, stack or heap (compiler decides)
arr := [5]int{1, 2, 3, 4, 5}
arr := [...]int{1, 2, 3}   // compiler counts: [3]int
```

```rust
// Rust
let arr: [i32; 10] = [0; 10];   // zero-initialized
let arr = [1, 2, 3, 4, 5];      // type inferred: [i32; 5]
```

**Key constraint:** Size is part of the type. `[5]int` and `[6]int` are different types in Go and Rust. You cannot resize a static array.

### 3.2 Dynamic Array

Resizable. Lives on heap. Has three important attributes:

```
┌─────────────────────────────────────────────────────────────┐
│  Dynamic Array Internal State                               │
│                                                             │
│  ptr ──────► [ e0 | e1 | e2 | e3 |    |    |    |    ]    │
│  len = 4                       ^         ^                  │
│  cap = 8                    used      allocated             │
│                                                             │
│  len: number of valid elements (logical size)               │
│  cap: total allocated slots (physical size)                 │
│  ptr: pointer to heap block                                 │
└─────────────────────────────────────────────────────────────┘
```

| Language | Type | len | cap | ptr |
|----------|------|-----|-----|-----|
| C | manual (malloc) | manual | manual | `void*` |
| Go | `[]T` (slice) | `len()` | `cap()` | internal |
| Rust | `Vec<T>` | `.len()` | `.capacity()` | internal |

### 3.3 Dynamic Array Growth Strategy

When you push an element and `len == cap`, the array must grow. Doubling is the standard strategy:

```
Initial:  cap=1
Push 1:   [e0]             cap=1,  len=1
Push 2:   [e0|e1|  |  ]   cap=2→4, len=2  (copy + realloc)
Push 3:   [e0|e1|e2|  ]   cap=4,  len=3
Push 4:   [e0|e1|e2|e3]   cap=4,  len=4
Push 5:   [e0|e1|e2|e3|e4|  |  |  |  |  |  |  |  |  |  |  ]
                            cap=4→8→16... len=5

Growth pattern:  1 → 2 → 4 → 8 → 16 → 32 ...

Total copies when pushing N elements:
  = 1 + 2 + 4 + ... + N/2 ≈ N
  = O(N) total, O(1) amortized per push
```

Go's growth factor is approximately 2x for small slices, transitioning to 1.25x for large slices. Rust's `Vec` uses 2x. This ensures amortized O(1) append.

---

## 4. Indexing and Access

### 4.1 Zero-Based vs One-Based Indexing

All three languages (C, Go, Rust) use zero-based indexing. The first element is at index 0, last at index `len-1`.

```
arr = [A, B, C, D, E]
idx =  0  1  2  3  4    (valid)
idx =        -1          (only valid in Python; causes UB in C, panic in Go/Rust)
```

### 4.2 Bounds Checking

```c
// C: NO bounds checking. Out-of-bounds = undefined behavior.
int arr[5] = {1,2,3,4,5};
int x = arr[10];    // reads garbage or crashes — no error!
arr[10] = 99;       // corrupts memory — no error!
```

```go
// Go: runtime bounds check, panic on violation
arr := [5]int{1,2,3,4,5}
x := arr[10]   // panic: runtime error: index out of range [10] with length 5
```

```rust
// Rust: runtime bounds check (index operator), panic on violation
let arr = [1,2,3,4,5];
let x = arr[10];   // thread 'main' panicked at 'index out of range: the len is 5 but the index is 10'

// Rust also offers checked access:
let x = arr.get(10);   // Returns Option<&i32> → None (no panic)
```

### 4.3 Negative Indexing (Python-style)

C, Go, and Rust do NOT support negative indexing natively. In C, `arr[-1]` is undefined behavior. In Go/Rust, it panics with "index out of range."

To access the last element:

```c
// C
arr[n - 1]
```

```go
// Go
arr[len(arr)-1]
```

```rust
// Rust
arr[arr.len() - 1]
// or safely:
arr.last()   // → Option<&T>
```

---

## 5. Traversal Patterns

### 5.1 Forward Traversal

```c
// C
int arr[] = {1, 2, 3, 4, 5};
int n = sizeof(arr) / sizeof(arr[0]);
for (int i = 0; i < n; i++) {
    printf("%d\n", arr[i]);
}
```

```go
// Go — index-based
arr := []int{1, 2, 3, 4, 5}
for i := 0; i < len(arr); i++ {
    fmt.Println(arr[i])
}

// Go — range (preferred)
for i, v := range arr {
    fmt.Printf("arr[%d] = %d\n", i, v)
}

// Go — value only
for _, v := range arr {
    fmt.Println(v)
}
```

```rust
// Rust — index-based
let arr = vec![1, 2, 3, 4, 5];
for i in 0..arr.len() {
    println!("{}", arr[i]);
}

// Rust — iterator (preferred, zero-cost abstraction)
for v in &arr {
    println!("{}", v);
}

// Rust — enumerate (index + value)
for (i, v) in arr.iter().enumerate() {
    println!("arr[{}] = {}", i, v);
}
```

### 5.2 Backward Traversal

```c
// C
for (int i = n - 1; i >= 0; i--) {
    printf("%d\n", arr[i]);
}
```

```go
// Go — no built-in reverse range, must use index
for i := len(arr) - 1; i >= 0; i-- {
    fmt.Println(arr[i])
}
```

```rust
// Rust — rev() on iterator
for v in arr.iter().rev() {
    println!("{}", v);
}
```

### 5.3 Skip/Step Traversal

```c
// Every other element (even indices)
for (int i = 0; i < n; i += 2) { ... }
```

```go
for i := 0; i < len(arr); i += 2 { ... }
```

```rust
for v in arr.iter().step_by(2) { ... }
```

### 5.4 Nested Traversal (2D Array)

```c
int mat[3][4];
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
        printf("%d ", mat[i][j]);
    }
}
// Always iterate row-major (inner loop = columns) for cache efficiency.
```

```go
mat := [3][4]int{}
for i := range mat {
    for j := range mat[i] {
        fmt.Print(mat[i][j], " ")
    }
}
```

```rust
let mat = [[0i32; 4]; 3];
for row in &mat {
    for val in row {
        print!("{} ", val);
    }
}
```

---

## 6. Insertion Operations

### 6.1 Insertion at End (Append)

This is O(1) amortized for dynamic arrays. For static arrays it is impossible unless you track a separate length variable.

```
Before:  [10 | 20 | 30 | 40 |    |    ]   len=4, cap=6
Append 50:
After:   [10 | 20 | 30 | 40 | 50 |    ]   len=5, cap=6
          ↑ no shifting required
```

```c
// C (manual dynamic array)
typedef struct {
    int *data;
    int len;
    int cap;
} IntArray;

void push(IntArray *a, int val) {
    if (a->len == a->cap) {
        a->cap = a->cap == 0 ? 1 : a->cap * 2;
        a->data = realloc(a->data, a->cap * sizeof(int));
    }
    a->data[a->len++] = val;
}
```

```go
// Go
arr := []int{1, 2, 3}
arr = append(arr, 4)   // O(1) amortized; may allocate new backing array
```

```rust
// Rust
let mut arr: Vec<i32> = vec![1, 2, 3];
arr.push(4);   // O(1) amortized
```

### 6.2 Insertion at Beginning

O(n): every existing element must shift right by one.

```
Before:  [10 | 20 | 30 | 40 | 50]   insert 5 at index 0
Step 1 — shift all right:
         [__ | 10 | 20 | 30 | 40 | 50]
Step 2 — write value:
         [ 5 | 10 | 20 | 30 | 40 | 50]
```

```c
// C (assumes enough capacity)
void insert_at_front(int *arr, int *n, int val) {
    for (int i = *n; i > 0; i--) {
        arr[i] = arr[i-1];   // shift right
    }
    arr[0] = val;
    (*n)++;
}
```

```go
// Go — using append trick
arr = append([]int{val}, arr...)   // allocates new slice!
// or: in-place (if cap allows)
arr = arr[:len(arr)+1]
copy(arr[1:], arr[0:])
arr[0] = val
```

```rust
// Rust
arr.insert(0, val);   // O(n) internally shifts all elements
```

### 6.3 Insertion at Arbitrary Index

O(n) worst case (shifting elements from index to end).

```
arr = [10 | 20 | 30 | 40 | 50]   insert 25 at index 2

Shift right from index 2:
  [10 | 20 | 30 | 40 | 50 | __]   ← make room at end
  [10 | 20 | __ | 30 | 40 | 50]   ← shift elements [2..] right
  [10 | 20 | 25 | 30 | 40 | 50]   ← write value

Number of shifts = len - index
Worst case (index=0): n shifts
Best case (index=len): 0 shifts
```

```c
void insert_at(int *arr, int *n, int idx, int val) {
    for (int i = *n; i > idx; i--) {
        arr[i] = arr[i-1];
    }
    arr[idx] = val;
    (*n)++;
}
```

```go
// Go
func insertAt(arr []int, idx, val int) []int {
    arr = append(arr, 0)          // grow by 1
    copy(arr[idx+1:], arr[idx:])  // shift right
    arr[idx] = val
    return arr
}
```

```rust
// Rust
arr.insert(idx, val);   // Vec::insert handles this
```

---

## 7. Deletion Operations

### 7.1 Deletion at End

O(1): just decrement the length. The data can remain; it's logically gone.

```
Before:  [10 | 20 | 30 | 40 | 50]   len=5
Pop 50:  [10 | 20 | 30 | 40 | __ ]   len=4
           ↑ no shifting; element 50 still in memory but inaccessible
```

```c
void pop(IntArray *a) {
    if (a->len > 0) a->len--;
}
```

```go
arr = arr[:len(arr)-1]   // reslice; O(1)
```

```rust
arr.pop();   // → Option<T>; O(1)
```

### 7.2 Deletion at Beginning

O(n): all remaining elements must shift left by one.

```
[10 | 20 | 30 | 40 | 50]   remove arr[0]
Shift left:
[20 | 30 | 40 | 50 | __]
```

```c
void remove_front(int *arr, int *n) {
    for (int i = 0; i < *n - 1; i++) {
        arr[i] = arr[i+1];
    }
    (*n)--;
}
```

```go
arr = arr[1:]   // O(1) — just moves the slice header pointer forward!
// BUT: the backing array still holds arr[0], preventing GC.
// For truly removing: arr = append([]int{}, arr[1:]...)
```

```rust
arr.remove(0);   // O(n) — shifts all elements left
// For O(1) if order doesn't matter:
arr.swap_remove(0);   // moves last element to index 0
```

### 7.3 Deletion at Arbitrary Index

```
arr = [10 | 20 | 30 | 40 | 50]   remove index 2 (value 30)

Shift left from index 3:
[10 | 20 | 40 | 50 | __]   len=4
```

```c
void remove_at(int *arr, int *n, int idx) {
    for (int i = idx; i < *n - 1; i++) {
        arr[i] = arr[i+1];
    }
    (*n)--;
}
```

```go
func removeAt(arr []int, idx int) []int {
    return append(arr[:idx], arr[idx+1:]...)
}
// Warning: this mutates the original backing array!
```

```rust
arr.remove(idx);   // O(n)

// O(1) if order doesn't matter (swap with last, pop):
arr.swap_remove(idx);   // O(1) — does NOT preserve order
```

### 7.4 Deletion by Value (First Occurrence)

Find the index, then delete at that index.

```go
// Go
func removeVal(arr []int, val int) []int {
    for i, v := range arr {
        if v == val {
            return append(arr[:i], arr[i+1:]...)
        }
    }
    return arr
}
```

```rust
// Rust
if let Some(pos) = arr.iter().position(|&x| x == val) {
    arr.remove(pos);
}
```

### 7.5 Deletion of All Matching Elements (Filter)

```go
// Go
func filter(arr []int, predicate func(int) bool) []int {
    out := arr[:0]   // reuse backing array (zero allocation)
    for _, v := range arr {
        if predicate(v) {
            out = append(out, v)
        }
    }
    return out
}
// Usage: keep elements > 3
arr = filter(arr, func(v int) bool { return v > 3 })
```

```rust
// Rust
arr.retain(|&x| x > 3);   // O(n), in-place, preserves order
```

---

## 8. Searching

### 8.1 Linear Search

O(n). Works on any array, sorted or unsorted.

```
arr = [42 | 17 | 83 | 5 | 29]   search for 83

i=0: 42 == 83? No
i=1: 17 == 83? No
i=2: 83 == 83? Yes → return 2
```

```c
int linear_search(int *arr, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}
```

```go
func linearSearch(arr []int, target int) int {
    for i, v := range arr {
        if v == target {
            return i
        }
    }
    return -1
}
```

```rust
fn linear_search(arr: &[i32], target: i32) -> Option<usize> {
    arr.iter().position(|&x| x == target)
}
```

### 8.2 Binary Search

O(log n). Requires **sorted** array.

```
arr = [2 | 5 | 8 | 12 | 16 | 23 | 38 | 42]   search for 23
       0   1   2   3    4    5    6    7

Step 1: lo=0, hi=7, mid=3 → arr[3]=12 < 23 → lo=4
Step 2: lo=4, hi=7, mid=5 → arr[5]=23 == 23 → FOUND at index 5

Visualization:
  [2 | 5 | 8 | 12 | 16 | 23 | 38 | 42]
   lo          mid              hi        step 1
                    lo    mid    hi        step 2 (found)
```

```c
int binary_search(int *arr, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;   // avoids integer overflow vs (lo+hi)/2
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
```

```go
import "sort"
// Standard library
idx := sort.SearchInts(arr, target)   // returns insertion point
if idx < len(arr) && arr[idx] == target {
    // found at idx
}

// Manual implementation
func binarySearch(arr []int, target int) int {
    lo, hi := 0, len(arr)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return -1
}
```

```rust
// Standard library (requires sorted slice)
match arr.binary_search(&target) {
    Ok(idx)  => println!("Found at {}", idx),
    Err(idx) => println!("Not found; would insert at {}", idx),
}
```

### 8.3 Find First/Last Occurrence (Binary Search Variants)

Critical for problems with duplicate elements.

```
arr = [1 | 2 | 2 | 2 | 3 | 4]   find first occurrence of 2

Standard binary search might return index 2.
We want index 1 (the first).

Lower bound:  largest index where arr[mid] < target → then +1
Upper bound:  smallest index where arr[mid] > target → then -1
```

```go
// First occurrence (lower bound)
func lowerBound(arr []int, target int) int {
    lo, hi, result := 0, len(arr)-1, -1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        if arr[mid] == target {
            result = mid
            hi = mid - 1   // keep searching left
        } else if arr[mid] < target {
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return result
}

// Last occurrence (upper bound)
func upperBound(arr []int, target int) int {
    lo, hi, result := 0, len(arr)-1, -1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        if arr[mid] == target {
            result = mid
            lo = mid + 1   // keep searching right
        } else if arr[mid] < target {
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return result
}
```

---

## 9. Sorting

### 9.1 Bubble Sort — O(n²)

```
arr = [5, 3, 8, 1, 2]

Pass 1: compare adjacent pairs, bubble max to end
  [3,5,8,1,2] → [3,5,1,8,2] → [3,5,1,2,8]   8 is settled
Pass 2:
  [3,1,5,2,8] → [3,1,2,5,8]   5 is settled
Pass 3:
  [1,3,2,5,8] → [1,2,3,5,8]   3 is settled
```

```c
void bubble_sort(int *arr, int n) {
    for (int i = 0; i < n-1; i++) {
        int swapped = 0;
        for (int j = 0; j < n-1-i; j++) {
            if (arr[j] > arr[j+1]) {
                int tmp = arr[j]; arr[j] = arr[j+1]; arr[j+1] = tmp;
                swapped = 1;
            }
        }
        if (!swapped) break;   // early termination if already sorted
    }
}
```

### 9.2 Insertion Sort — O(n²) worst, O(n) best

Best for small arrays or nearly-sorted data.

```
arr = [5, 3, 8, 1, 2]

i=1: key=3. Shift 5 right. Insert 3 → [3,5,8,1,2]
i=2: key=8. 8>5, no shift.            → [3,5,8,1,2]
i=3: key=1. Shift 8,5,3 right.        → [1,3,5,8,2]
i=4: key=2. Shift 8,5,3 right.        → [1,2,3,5,8]
```

```c
void insertion_sort(int *arr, int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j+1] = arr[j];
            j--;
        }
        arr[j+1] = key;
    }
}
```

### 9.3 Merge Sort — O(n log n)

Divide and conquer. Stable. Uses O(n) extra space.

```
[5, 3, 8, 1, 2]
        ↓ divide
   [5,3,8]      [1,2]
      ↓             ↓
  [5,3]  [8]    [1]  [2]
    ↓               ↓
 [5]  [3]       [1,2] ← merge
    ↓
 [3,5] ← merge
    ↓
 [3,5,8] ← merge
        ↓
  [1,2,3,5,8] ← final merge
```

```c
void merge(int *arr, int l, int m, int r) {
    int n1 = m - l + 1, n2 = r - m;
    int *L = malloc(n1 * sizeof(int));
    int *R = malloc(n2 * sizeof(int));
    for (int i = 0; i < n1; i++) L[i] = arr[l+i];
    for (int j = 0; j < n2; j++) R[j] = arr[m+1+j];
    int i = 0, j = 0, k = l;
    while (i < n1 && j < n2) {
        if (L[i] <= R[j]) arr[k++] = L[i++];
        else arr[k++] = R[j++];
    }
    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];
    free(L); free(R);
}

void merge_sort(int *arr, int l, int r) {
    if (l < r) {
        int m = l + (r-l)/2;
        merge_sort(arr, l, m);
        merge_sort(arr, m+1, r);
        merge(arr, l, m, r);
    }
}
```

```go
import "sort"
sort.Ints(arr)            // standard library, uses pattern-defeating quicksort
sort.Slice(arr, func(i, j int) bool { return arr[i] < arr[j] })
```

```rust
arr.sort();              // stable sort (merge sort variant), O(n log n)
arr.sort_unstable();     // unstable sort (pattern-defeating quicksort), O(n log n), faster
arr.sort_by(|a, b| a.cmp(b));
arr.sort_by_key(|&x| -x);   // sort descending
```

### 9.4 Quick Sort — O(n log n) average, O(n²) worst

```
arr = [3, 6, 8, 10, 1, 2, 1]   pivot = arr[last] = 1

Partition:
  Elements < 1:  (none)
  Elements == 1: [1, 1]
  Elements > 1:  [3, 6, 8, 10, 2]

Result: [1,1] + [3,6,8,10,2] → recurse on right partition
```

```c
int partition(int *arr, int lo, int hi) {
    int pivot = arr[hi];
    int i = lo - 1;
    for (int j = lo; j < hi; j++) {
        if (arr[j] <= pivot) {
            i++;
            int tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
        }
    }
    int tmp = arr[i+1]; arr[i+1] = arr[hi]; arr[hi] = tmp;
    return i + 1;
}

void quicksort(int *arr, int lo, int hi) {
    if (lo < hi) {
        int pi = partition(arr, lo, hi);
        quicksort(arr, lo, pi-1);
        quicksort(arr, pi+1, hi);
    }
}
```

---

## 10. Reversal

### 10.1 In-Place Reversal — O(n)

The two-pointer approach: one pointer at start, one at end, swap and move inward.

```
arr = [1 | 2 | 3 | 4 | 5]
       L               R

Swap arr[L] and arr[R], move L right, R left:

Step 1: swap(1,5) → [5 | 2 | 3 | 4 | 1]   L=1, R=3
Step 2: swap(2,4) → [5 | 4 | 3 | 2 | 1]   L=2, R=2
Step 3: L >= R → stop

Result: [5, 4, 3, 2, 1]
```

```c
void reverse(int *arr, int n) {
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int tmp = arr[lo]; arr[lo] = arr[hi]; arr[hi] = tmp;
        lo++; hi--;
    }
}
```

```go
// Reverse a slice in-place
func reverse(arr []int) {
    for lo, hi := 0, len(arr)-1; lo < hi; lo, hi = lo+1, hi-1 {
        arr[lo], arr[hi] = arr[hi], arr[lo]
    }
}
```

```rust
arr.reverse();   // in-place, O(n)

// Manual:
let n = arr.len();
for i in 0..n/2 {
    arr.swap(i, n - 1 - i);
}
```

### 10.2 Reversing a Subarray

Useful for array rotation and many other algorithms.

```go
func reverseRange(arr []int, lo, hi int) {
    for lo < hi {
        arr[lo], arr[hi] = arr[hi], arr[lo]
        lo++; hi--
    }
}
```

```rust
arr[lo..=hi].reverse();
```

---

## 11. Rotation

### 11.1 Left Rotation by k Positions

```
arr = [1, 2, 3, 4, 5]   left rotate by 2

Result: [3, 4, 5, 1, 2]

Naive approach: shift one step left, repeat k times → O(n*k)
```

### 11.2 Three-Reversal Trick — O(n), O(1) space

```
Left rotate by k:
  1. Reverse arr[0..k-1]
  2. Reverse arr[k..n-1]
  3. Reverse the whole array

arr = [1, 2, 3, 4, 5]   k=2

Step 1: reverse [1,2]         → [2, 1, 3, 4, 5]
Step 2: reverse [3,4,5]       → [2, 1, 5, 4, 3]
Step 3: reverse whole         → [3, 4, 5, 1, 2] ✓
```

```go
func leftRotate(arr []int, k int) {
    n := len(arr)
    k = k % n   // handle k >= n
    reverse := func(lo, hi int) {
        for lo < hi {
            arr[lo], arr[hi] = arr[hi], arr[lo]
            lo++; hi--
        }
    }
    reverse(0, k-1)
    reverse(k, n-1)
    reverse(0, n-1)
}
```

```rust
fn left_rotate(arr: &mut Vec<i32>, k: usize) {
    let n = arr.len();
    let k = k % n;
    arr[..k].reverse();
    arr[k..].reverse();
    arr.reverse();
}
```

```c
void left_rotate(int *arr, int n, int k) {
    k = k % n;
    reverse(arr, 0, k-1);
    reverse(arr, k, n-1);
    reverse(arr, 0, n-1);
}
```

### 11.3 Right Rotation

Right rotate by k = Left rotate by (n - k).

```go
func rightRotate(arr []int, k int) {
    n := len(arr)
    leftRotate(arr, n-k%n)
}
```

---

## 12. Sliding Window Technique

### 12.1 What It Is

The sliding window is a technique for processing subarrays of a fixed or variable size without recomputing from scratch each time.

```
arr = [2, 1, 5, 1, 3, 2]   window size k=3

Window position 0: [2, 1, 5] → sum=8
Window position 1:    [1, 5, 1] → sum=7   (subtract 2, add 1)
Window position 2:       [5, 1, 3] → sum=9   (subtract 1, add 3)
Window position 3:          [1, 3, 2] → sum=6

Instead of recomputing sum from scratch (O(k) each time),
we do: new_sum = old_sum - arr[left] + arr[right]   → O(1)

Total: O(n) instead of O(n*k)
```

### 12.2 Fixed Window — Maximum Sum of Subarray of Size k

```c
int max_sum_subarray(int *arr, int n, int k) {
    int window_sum = 0;
    for (int i = 0; i < k; i++) window_sum += arr[i];
    int max_sum = window_sum;
    for (int i = k; i < n; i++) {
        window_sum += arr[i] - arr[i-k];
        if (window_sum > max_sum) max_sum = window_sum;
    }
    return max_sum;
}
```

```go
func maxSumSubarray(arr []int, k int) int {
    windowSum := 0
    for _, v := range arr[:k] {
        windowSum += v
    }
    maxSum := windowSum
    for i := k; i < len(arr); i++ {
        windowSum += arr[i] - arr[i-k]
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    return maxSum
}
```

```rust
fn max_sum_subarray(arr: &[i32], k: usize) -> i32 {
    let mut window_sum: i32 = arr[..k].iter().sum();
    let mut max_sum = window_sum;
    for i in k..arr.len() {
        window_sum += arr[i] - arr[i - k];
        max_sum = max_sum.max(window_sum);
    }
    max_sum
}
```

### 12.3 Variable Window — Longest Subarray with Sum ≤ k

```
arr = [1, 2, 3, 1, 1]   find longest subarray with sum <= 4

left=0, right expands:
  right=0: sum=1 ≤ 4, window=[1]
  right=1: sum=3 ≤ 4, window=[1,2]
  right=2: sum=6 > 4 → shrink from left
    left=1: sum=5 > 4 → shrink
    left=2: sum=3 ≤ 4, window=[3]
  right=3: sum=4 ≤ 4, window=[3,1]
  right=4: sum=5 > 4 → shrink
    left=3: sum=2 ≤ 4, window=[1,1]

max_len=2 (windows [1,2] and [3,1] and [1,1])
```

```go
func longestSubarrayWithSumLE(arr []int, k int) int {
    left, sum, maxLen := 0, 0, 0
    for right := 0; right < len(arr); right++ {
        sum += arr[right]
        for sum > k {
            sum -= arr[left]
            left++
        }
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}
```

---

## 13. Two-Pointer Technique

### 13.1 Opposite Direction (Pair Sum)

Find two elements that sum to a target in a sorted array.

```
arr = [1, 2, 4, 6, 8, 10]   target = 10

lo=0, hi=5: arr[0]+arr[5] = 1+10 = 11 > 10 → hi--
lo=0, hi=4: arr[0]+arr[4] = 1+8  = 9  < 10 → lo++
lo=1, hi=4: arr[1]+arr[4] = 2+8  = 10 == 10 → FOUND (1,4)
```

```c
int pair_sum(int *arr, int n, int target, int *i_out, int *j_out) {
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        int s = arr[lo] + arr[hi];
        if (s == target) { *i_out = lo; *j_out = hi; return 1; }
        else if (s < target) lo++;
        else hi--;
    }
    return 0;
}
```

```go
func pairSum(arr []int, target int) (int, int, bool) {
    lo, hi := 0, len(arr)-1
    for lo < hi {
        s := arr[lo] + arr[hi]
        if s == target {
            return lo, hi, true
        } else if s < target {
            lo++
        } else {
            hi--
        }
    }
    return -1, -1, false
}
```

```rust
fn pair_sum(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    let (mut lo, mut hi) = (0, arr.len() - 1);
    while lo < hi {
        let s = arr[lo] + arr[hi];
        if s == target { return Some((lo, hi)); }
        else if s < target { lo += 1; }
        else { hi -= 1; }
    }
    None
}
```

### 13.2 Same Direction (Remove Duplicates In-Place)

```
arr = [1, 1, 2, 2, 3, 4, 4]   sorted; remove duplicates in-place

slow=0, fast=1:
  fast=1: arr[1]==arr[0]? Yes (1==1) → skip
  fast=2: arr[2]==arr[0]? No (2!=1) → slow++, arr[slow]=arr[fast]
  slow=1, arr=[1,2,2,2,3,4,4]
  fast=3: arr[3]==arr[1]? Yes (2==2) → skip
  fast=4: arr[4]==arr[1]? No (3!=2) → slow++, arr[slow]=arr[fast]
  slow=2, arr=[1,2,3,2,3,4,4]
  fast=5: arr[5]==arr[2]? No (4!=3) → slow++
  slow=3, arr=[1,2,3,4,3,4,4]
  fast=6: arr[6]==arr[3]? Yes (4==4) → skip

Result: arr[0..slow+1] = [1,2,3,4], new length = slow+1 = 4
```

```go
func removeDuplicates(arr []int) int {
    if len(arr) == 0 { return 0 }
    slow := 0
    for fast := 1; fast < len(arr); fast++ {
        if arr[fast] != arr[slow] {
            slow++
            arr[slow] = arr[fast]
        }
    }
    return slow + 1
}
```

```rust
fn remove_duplicates(arr: &mut Vec<i32>) {
    arr.dedup();   // requires sorted; O(n) in-place
}
```

---

## 14. Prefix Sum and Difference Array

### 14.1 Prefix Sum

Enables O(1) range sum queries after O(n) preprocessing.

```
arr    = [3, 1, 4, 1, 5, 9, 2, 6]
         idx: 0  1  2  3  4  5  6  7

prefix = [0, 3, 4, 8, 9, 14, 23, 25, 31]
          ^  idx: 0  1  2   3   4   5   6   7
          sentinel

prefix[i] = arr[0] + arr[1] + ... + arr[i-1]
prefix[0] = 0 (empty prefix)

Sum of arr[l..r] (inclusive):
  = prefix[r+1] - prefix[l]

Example: sum(arr[2..5]) = prefix[6] - prefix[2] = 23 - 4 = 19
Check: 4+1+5+9 = 19 ✓
```

```c
void build_prefix(int *arr, int *prefix, int n) {
    prefix[0] = 0;
    for (int i = 0; i < n; i++) {
        prefix[i+1] = prefix[i] + arr[i];
    }
}

int range_sum(int *prefix, int l, int r) {
    return prefix[r+1] - prefix[l];
}
```

```go
func buildPrefix(arr []int) []int {
    prefix := make([]int, len(arr)+1)
    for i, v := range arr {
        prefix[i+1] = prefix[i] + v
    }
    return prefix
}

func rangeSum(prefix []int, l, r int) int {
    return prefix[r+1] - prefix[l]
}
```

```rust
fn build_prefix(arr: &[i32]) -> Vec<i32> {
    let mut prefix = vec![0; arr.len() + 1];
    for (i, &v) in arr.iter().enumerate() {
        prefix[i + 1] = prefix[i] + v;
    }
    prefix
}

fn range_sum(prefix: &[i32], l: usize, r: usize) -> i32 {
    prefix[r + 1] - prefix[l]
}
```

### 14.2 2D Prefix Sum

```
Matrix:         2D Prefix:
[1, 2, 3]       [0, 0,  0,  0]
[4, 5, 6]  →    [0, 1,  3,  6]
[7, 8, 9]       [0, 5, 12, 21]
                [0,12, 27, 45]

prefix[i][j] = sum of all elements in top-left submatrix [0..i-1][0..j-1]

Sum of rectangle (r1,c1) to (r2,c2):
  = prefix[r2+1][c2+1]
  - prefix[r1][c2+1]
  - prefix[r2+1][c1]
  + prefix[r1][c1]   (inclusion-exclusion)
```

### 14.3 Difference Array

Enables O(1) range updates, O(n) reconstruction. Inverse of prefix sum.

```
Problem: apply +5 to arr[2..5], -3 to arr[1..4], repeatedly.

arr  = [0, 0, 0, 0, 0, 0, 0]   (size 7)
diff = [0, 0, 0, 0, 0, 0, 0]

Operation: add 5 to [2..5]
  diff[2]  += 5
  diff[6]  -= 5   (right boundary + 1)
  diff = [0, 0, 5, 0, 0, 0, -5]

Operation: add -3 to [1..4]
  diff[1]  += -3
  diff[5]  -= -3
  diff = [0, -3, 5, 0, 0, 3, -5]

Reconstruct arr via prefix sum on diff:
  arr[0] = diff[0] = 0
  arr[1] = arr[0] + diff[1] = 0 + (-3) = -3
  arr[2] = arr[1] + diff[2] = -3 + 5   = 2
  arr[3] = arr[2] + diff[3] = 2 + 0    = 2
  arr[4] = arr[3] + diff[4] = 2 + 0    = 2
  arr[5] = arr[4] + diff[5] = 2 + 3    = 5
  arr[6] = arr[5] + diff[6] = 5 + (-5) = 0
```

```go
type DiffArray struct {
    diff []int
}

func NewDiffArray(n int) *DiffArray {
    return &DiffArray{diff: make([]int, n+1)}
}

func (d *DiffArray) RangeAdd(l, r, val int) {
    d.diff[l] += val
    d.diff[r+1] -= val
}

func (d *DiffArray) Build() []int {
    result := make([]int, len(d.diff)-1)
    result[0] = d.diff[0]
    for i := 1; i < len(result); i++ {
        result[i] = result[i-1] + d.diff[i]
    }
    return result
}
```

---

## 15. Subarray Operations

### 15.1 Maximum Subarray Sum — Kadane's Algorithm O(n)

```
arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]

        i:   0   1   2   3   4   5   6   7   8
curr_sum:   -2   1  -2   4   3   5   6   1   5
 max_sum:   -2   1   1   4   4   5   6   6   6

Key insight: if curr_sum goes negative, restart from current element.
curr_sum = max(arr[i], curr_sum + arr[i])
```

```c
int kadane(int *arr, int n) {
    int curr = arr[0], max_sum = arr[0];
    for (int i = 1; i < n; i++) {
        curr = (arr[i] > curr + arr[i]) ? arr[i] : curr + arr[i];
        if (curr > max_sum) max_sum = curr;
    }
    return max_sum;
}
```

```go
func kadane(arr []int) int {
    curr, maxSum := arr[0], arr[0]
    for _, v := range arr[1:] {
        if curr+v > v {
            curr = curr + v
        } else {
            curr = v
        }
        if curr > maxSum {
            maxSum = curr
        }
    }
    return maxSum
}
```

```rust
fn kadane(arr: &[i32]) -> i32 {
    let mut curr = arr[0];
    let mut max_sum = arr[0];
    for &v in &arr[1..] {
        curr = v.max(curr + v);
        max_sum = max_sum.max(curr);
    }
    max_sum
}
```

### 15.2 Subarray with Given Sum (Two Pointers, Non-Negative)

```go
func subarrayWithSum(arr []int, target int) (int, int, bool) {
    sum, left := 0, 0
    for right := 0; right < len(arr); right++ {
        sum += arr[right]
        for sum > target && left <= right {
            sum -= arr[left]
            left++
        }
        if sum == target {
            return left, right, true
        }
    }
    return -1, -1, false
}
```

### 15.3 Count of Subarrays with Given Sum (Hash Map, Any Values)

```go
func countSubarraysWithSum(arr []int, target int) int {
    freq := map[int]int{0: 1}   // prefix_sum → count
    sum, count := 0, 0
    for _, v := range arr {
        sum += v
        count += freq[sum-target]   // how many times did (sum-target) appear?
        freq[sum]++
    }
    return count
}
```

---

## 16. Merging Arrays

### 16.1 Merge Two Sorted Arrays

Classic two-pointer merge used in merge sort.

```
A = [1, 3, 5, 7]
B = [2, 4, 6, 8]

i=0, j=0: A[0]=1 < B[0]=2 → out=[1], i=1
i=1, j=0: A[1]=3 > B[0]=2 → out=[1,2], j=1
i=1, j=1: A[1]=3 < B[1]=4 → out=[1,2,3], i=2
...
Result: [1,2,3,4,5,6,7,8]
```

```c
int* merge_sorted(int *A, int m, int *B, int n) {
    int *out = malloc((m+n) * sizeof(int));
    int i = 0, j = 0, k = 0;
    while (i < m && j < n) {
        if (A[i] <= B[j]) out[k++] = A[i++];
        else out[k++] = B[j++];
    }
    while (i < m) out[k++] = A[i++];
    while (j < n) out[k++] = B[j++];
    return out;
}
```

```go
func mergeSorted(A, B []int) []int {
    out := make([]int, 0, len(A)+len(B))
    i, j := 0, 0
    for i < len(A) && j < len(B) {
        if A[i] <= B[j] {
            out = append(out, A[i]); i++
        } else {
            out = append(out, B[j]); j++
        }
    }
    out = append(out, A[i:]...)
    out = append(out, B[j:]...)
    return out
}
```

```rust
fn merge_sorted(a: &[i32], b: &[i32]) -> Vec<i32> {
    let mut out = Vec::with_capacity(a.len() + b.len());
    let (mut i, mut j) = (0, 0);
    while i < a.len() && j < b.len() {
        if a[i] <= b[j] { out.push(a[i]); i += 1; }
        else { out.push(b[j]); j += 1; }
    }
    out.extend_from_slice(&a[i..]);
    out.extend_from_slice(&b[j..]);
    out
}
```

### 16.2 Merge Two Sorted Arrays In-Place (No Extra Space)

```
A = [1, 3, 5, 7, _, _, _, _]   (has space for B at end)
B = [2, 4, 6, 8]

Strategy: merge from the END backwards to avoid overwriting
  i = m-1 (last valid in A)
  j = n-1 (last in B)
  k = m+n-1 (write position)
```

```go
func mergeSortedInPlace(A []int, m int, B []int, n int) {
    i, j, k := m-1, n-1, m+n-1
    for i >= 0 && j >= 0 {
        if A[i] > B[j] {
            A[k] = A[i]; i--
        } else {
            A[k] = B[j]; j--
        }
        k--
    }
    for j >= 0 {
        A[k] = B[j]; j--; k--
    }
}
```

---

## 17. Partitioning

### 17.1 Dutch National Flag (3-Way Partition)

Partition array into three groups: < pivot, == pivot, > pivot. O(n), one pass.

```
arr = [2, 0, 2, 1, 1, 0]   pivot=1

Pointers: low=0, mid=0, high=5

After pass:
  [0, 0, 1, 1, 2, 2]
  low  ───  mid  ─── high

State at each step:
  [2,0,2,1,1,0]  mid=0: arr[mid]=2>1 → swap(mid,high), high--
  [0,0,2,1,1,2]  mid=0: arr[mid]=0<1 → swap(low,mid), low++,mid++
  [0,0,2,1,1,2]  mid=1: arr[mid]=0<1 → swap(low,mid), low++,mid++
  [0,0,2,1,1,2]  mid=2: arr[mid]=2>1 → swap(mid,high), high--
  [0,0,1,1,2,2]  mid=2: arr[mid]=1==1 → mid++
  [0,0,1,1,2,2]  mid=3: arr[mid]=1==1 → mid++
  mid > high → done
```

```go
func dutchNationalFlag(arr []int) {
    lo, mid, hi := 0, 0, len(arr)-1
    for mid <= hi {
        switch {
        case arr[mid] < 1:
            arr[lo], arr[mid] = arr[mid], arr[lo]
            lo++; mid++
        case arr[mid] == 1:
            mid++
        default:
            arr[mid], arr[hi] = arr[hi], arr[mid]
            hi--
        }
    }
}
```

```rust
fn dutch_flag(arr: &mut [i32]) {
    let (mut lo, mut mid, mut hi) = (0, 0, arr.len() - 1);
    while mid <= hi {
        match arr[mid].cmp(&1) {
            std::cmp::Ordering::Less => { arr.swap(lo, mid); lo += 1; mid += 1; }
            std::cmp::Ordering::Equal => { mid += 1; }
            std::cmp::Ordering::Greater => { arr.swap(mid, hi); if hi == 0 { break; } hi -= 1; }
        }
    }
}
```

---

## 18. Matrix (2D Array) Operations

### 18.1 Transpose

```
Original:         Transposed:
[1  2  3]         [1  4  7]
[4  5  6]    →    [2  5  8]
[7  8  9]         [3  6  9]

Rule: swap arr[i][j] with arr[j][i]  (for upper triangle, i < j)
```

```go
func transpose(mat [][]int) {
    n := len(mat)
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {
            mat[i][j], mat[j][i] = mat[j][i], mat[i][j]
        }
    }
}
```

```rust
fn transpose(mat: &mut Vec<Vec<i32>>) {
    let n = mat.len();
    for i in 0..n {
        for j in i+1..n {
            let tmp = mat[i][j];
            mat[i][j] = mat[j][i];
            mat[j][i] = tmp;
        }
    }
}
```

### 18.2 Rotate Matrix 90° Clockwise

```
Step 1: Transpose
Step 2: Reverse each row

Original:    Transpose:   Reverse rows:
[1 2 3]      [1 4 7]      [7 4 1]
[4 5 6]  →   [2 5 8]  →   [8 5 2]
[7 8 9]      [3 6 9]      [9 6 3]
```

```go
func rotate90(mat [][]int) {
    n := len(mat)
    // Transpose
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {
            mat[i][j], mat[j][i] = mat[j][i], mat[i][j]
        }
    }
    // Reverse each row
    for i := 0; i < n; i++ {
        for lo, hi := 0, n-1; lo < hi; lo, hi = lo+1, hi-1 {
            mat[i][lo], mat[i][hi] = mat[i][hi], mat[i][lo]
        }
    }
}
```

### 18.3 Spiral Traversal

```
[1  2  3  4]
[5  6  7  8]
[9 10 11 12]
[13 14 15 16]

Spiral: 1→2→3→4→8→12→16→15→14→13→9→5→6→7→11→10
```

```go
func spiralOrder(mat [][]int) []int {
    if len(mat) == 0 { return nil }
    top, bot := 0, len(mat)-1
    left, right := 0, len(mat[0])-1
    var result []int
    for top <= bot && left <= right {
        for j := left; j <= right; j++ { result = append(result, mat[top][j]) }
        top++
        for i := top; i <= bot; i++ { result = append(result, mat[i][right]) }
        right--
        if top <= bot {
            for j := right; j >= left; j-- { result = append(result, mat[bot][j]) }
            bot--
        }
        if left <= right {
            for i := bot; i >= top; i-- { result = append(result, mat[i][left]) }
            left++
        }
    }
    return result
}
```

---

## 19. Dynamic Array Internals

### 19.1 Go Slice Internals

A Go slice is a three-word struct:

```
type slice struct {
    ptr  *T    // pointer to backing array (8 bytes on 64-bit)
    len  int   // current length (8 bytes)
    cap  int   // capacity (8 bytes)
}               // total: 24 bytes

Two slices sharing the same backing array:

s1 := []int{1, 2, 3, 4, 5}
s2 := s1[1:3]   // slice of s1

Heap (backing array):
  ┌────┬────┬────┬────┬────┐
  │ 1  │ 2  │ 3  │ 4  │ 5  │
  └────┴────┴────┴────┴────┘
    ↑              ↑
    s1.ptr         │
                   s2.ptr (offset into same array)

s1: {ptr=0x1000, len=5, cap=5}
s2: {ptr=0x1008, len=2, cap=4}   ← cap extends to end of backing array

DANGER: modifying s2[0] modifies s1[1]!
```

Appending to s2 when cap > len still modifies the shared backing array:

```go
s2 = append(s2, 99)   // no new allocation (cap=4 > len=2)
// Now s1 = [1, 2, 3, 99, 5]  ← s1[3] was silently changed!
```

To break the sharing, use `copy`:

```go
s2 = append([]int{}, s1[1:3]...)   // new backing array
// or:
s2 = s1[1:3:3]   // three-index slice: cap limited to 3, prevents accidental modification
```

### 19.2 Rust Vec Internals

```
Vec<T> on the stack:
  ┌──────────────────────────────┐
  │ ptr: *mut T    (8 bytes)     │
  │ len: usize     (8 bytes)     │
  │ cap: usize     (8 bytes)     │
  └──────────────────────────────┘

On the heap:
  ┌────┬────┬────┬────┬    ┬    ┐
  │ e0 │ e1 │ e2 │ e3 │    │    │
  └────┴────┴────┴────┴    ┴    ┘
  ←── len=4 ──────────►
  ←── cap=6 ─────────────────────►

Ownership rules:
  - Vec owns its heap allocation
  - Drop (destructor) runs when Vec goes out of scope
  - Slices (&[T]) are borrows: {ptr, len} — no ownership, no cap

Vec<T> growth in Rust (simplified):
  fn grow(&mut self) {
      let new_cap = if self.cap == 0 { 1 } else { self.cap * 2 };
      // allocate new_cap elements
      // copy old elements (memcpy for Copy types, ptr::read for non-Copy)
      // deallocate old buffer
      self.cap = new_cap;
  }
```

### 19.3 C Dynamic Array (Manual)

```c
typedef struct {
    int   *data;
    size_t len;
    size_t cap;
} Vec;

void vec_init(Vec *v) {
    v->data = NULL;
    v->len = v->cap = 0;
}

void vec_push(Vec *v, int val) {
    if (v->len == v->cap) {
        v->cap = v->cap == 0 ? 4 : v->cap * 2;
        int *new_data = realloc(v->data, v->cap * sizeof(int));
        if (!new_data) { /* handle OOM */ exit(1); }
        v->data = new_data;
    }
    v->data[v->len++] = val;
}

void vec_free(Vec *v) {
    free(v->data);
    v->data = NULL;
    v->len = v->cap = 0;
}
```

---

## 20. Cache Behavior and Memory Access Patterns

### 20.1 Sequential vs Random Access

```
Sequential (cache-friendly):
  arr[0], arr[1], arr[2], arr[3] ...
  ────────────────────────────────►
  One cache-line fetch prefetches many future accesses.
  Latency: ~4 cycles (L1 cache hit after first access)

Random (cache-hostile):
  arr[47], arr[3], arr[281], arr[15] ...
  Each access potentially in a new cache line.
  Latency: ~200 cycles (DRAM access) per element

Example: matrix sum, row-major vs column-major access

int mat[1024][1024];

// FAST: row-major (sequential in memory)
for (i = 0; i < 1024; i++)
  for (j = 0; j < 1024; j++)
    sum += mat[i][j];       // stride = 1 element = 4 bytes

// SLOW: column-major (jumps 1024 elements = 4096 bytes per access)
for (j = 0; j < 1024; j++)
  for (i = 0; i < 1024; i++)
    sum += mat[i][j];       // stride = 1024 elements = 4096 bytes

Performance difference: 10x–20x on modern hardware.
```

### 20.2 False Sharing (Multi-threaded Arrays)

```
Two threads write to adjacent array elements:

Thread 1 writes arr[0]
Thread 2 writes arr[1]

arr[0] and arr[1] are in the SAME cache line (64 bytes).
Every write by Thread 1 invalidates Thread 2's cache line, and vice versa.
They appear to be sharing data even though they touch different elements.

Fix: pad elements to cache-line size:

struct PaddedInt {
    int value;
    char pad[60];   // 64 bytes total per element
};
```

---

## 21. Common Mistakes — Exhaustive List

### 21.1 Off-By-One Errors (Most Common)

```
arr = [1, 2, 3, 4, 5]   length = 5, valid indices = 0..4

// WRONG: accessing index == length
for (int i = 0; i <= n; i++)    // ← should be i < n
    arr[i] = 0;    // arr[5] is out of bounds!

// WRONG: missing the last element
for (int i = 0; i < n-1; i++)   // ← should be i < n (if inclusive)
    process(arr[i]);   // arr[4] never processed!

// WRONG: binary search boundary (classic mistake)
int lo = 0, hi = n;     // ← correct for exclusive upper bound
int lo = 0, hi = n-1;   // ← correct for inclusive upper bound
// Mixing these two conventions in one function causes subtle bugs.
```

```go
// Go: accessing slice after reslice
s := []int{1, 2, 3}
s = s[:2]
x := s[2]   // panic: index out of range! len is now 2

// Common in loops:
for i := 0; i <= len(s); i++ {   // ← should be i < len(s)
```

```rust
// Rust: usize subtraction underflow (no negative usize!)
let n: usize = 0;
let prev = n - 1;   // PANIC: attempt to subtract with overflow
// Fix:
let prev = n.checked_sub(1).unwrap_or(0);
// Or: if n > 0 { n - 1 } else { 0 }
```

### 21.2 Modifying Array While Iterating

```go
// WRONG in Go: removing elements while ranging
arr := []int{1, 2, 3, 4, 5}
for i, v := range arr {
    if v == 3 {
        arr = append(arr[:i], arr[i+1:]...)  // ← modifies arr mid-iteration
        // 'i' now points to wrong element in next iteration
    }
}

// CORRECT: iterate and collect, or use filter pattern
result := arr[:0]
for _, v := range arr {
    if v != 3 {
        result = append(result, v)
    }
}
arr = result
```

```rust
// WRONG in Rust: can't iterate and mutate simultaneously (borrow checker prevents it)
// The borrow checker is your friend here — it catches this at compile time.

// CORRECT: retain
arr.retain(|&x| x != 3);
```

### 21.3 Go Slice Aliasing Bugs

This is one of the most common Go mistakes:

```go
// BUG: append may or may not create a new backing array
original := []int{1, 2, 3, 4, 5}
sub := original[1:3]   // sub shares backing array with original

// If cap(sub) > len(sub), append modifies original's memory:
sub = append(sub, 99)   // cap(sub) = 4 > len(sub) = 2
// Now original = [1, 2, 3, 99, 5] — silently mutated!

// FIX: use three-index slicing to control capacity
sub := original[1:3:3]   // cap is now 3, not 4
sub = append(sub, 99)   // new allocation, original is safe

// FIX: explicit copy
sub := make([]int, 2)
copy(sub, original[1:3])
sub = append(sub, 99)   // definitely new array
```

### 21.4 Integer Overflow in Index Arithmetic

```c
// WRONG: classic bug in binary search
int mid = (lo + hi) / 2;   // overflows if lo + hi > INT_MAX

// CORRECT:
int mid = lo + (hi - lo) / 2;

// Same in Go:
mid := (lo + hi) / 2   // can overflow for large indices, though rare in practice
mid := lo + (hi-lo)/2  // correct
```

### 21.5 Wrong sizeof in C

```c
// WRONG: always gets pointer size, not array size
void process(int arr[]) {
    int n = sizeof(arr) / sizeof(arr[0]);  // sizeof(arr) = 8 (pointer), not array size!
}

// WHY: when passed to a function, array decays to a pointer.
// sizeof(pointer) = 8 on 64-bit, regardless of array size.

// CORRECT: always pass the size explicitly
void process(int *arr, int n) { ... }

// Or in C (only valid for static arrays in same scope):
int arr[10];
int n = sizeof(arr) / sizeof(arr[0]);   // correct: 10
```

### 21.6 C: Using Freed Memory (Use-After-Free)

```c
int *arr = malloc(10 * sizeof(int));
// ... fill and use arr ...
free(arr);
arr[0] = 42;   // UNDEFINED BEHAVIOR: memory was freed
// arr is a dangling pointer

// CORRECT: null the pointer after freeing
free(arr);
arr = NULL;
arr[0] = 42;   // segfault (predictable), not silent corruption
```

### 21.7 Rust: Borrow Checker Violations (Common Misunderstandings)

```rust
// WRONG: can't have mutable ref and immutable ref simultaneously
let mut arr = vec![1, 2, 3];
let first = &arr[0];        // immutable borrow
arr.push(4);                // mutable borrow — COMPILE ERROR
println!("{}", first);      // first might be dangling after push realloc!

// The borrow checker catches what C/Go miss: push might reallocate the heap
// buffer, making `first` a dangling pointer.

// CORRECT: don't hold references across mutations
let mut arr = vec![1, 2, 3];
let first_val = arr[0];     // copy the value
arr.push(4);
println!("{}", first_val);  // safe: using copied value, not reference
```

### 21.8 Go: Nil vs Empty Slice

```go
var s1 []int          // nil slice: {nil, 0, 0}
s2 := []int{}         // empty slice: {ptr, 0, 0} (ptr to zero-size allocation)

len(s1) == 0          // true
len(s2) == 0          // true
s1 == nil             // true
s2 == nil             // FALSE — common surprise

// Implication: json.Marshal treats nil slice as null, empty slice as []
import "encoding/json"
b1, _ := json.Marshal(s1)   // → null
b2, _ := json.Marshal(s2)   // → []

// RULE: prefer returning nil slice for "no data", empty slice for "zero items".
```

### 21.9 Not Handling Empty Array Edge Cases

```go
// Many algorithms assume non-empty input:
func max(arr []int) int {
    m := arr[0]   // PANIC if arr is empty!
    for _, v := range arr[1:] {
        if v > m { m = v }
    }
    return m
}

// CORRECT:
func max(arr []int) (int, bool) {
    if len(arr) == 0 { return 0, false }
    m := arr[0]
    for _, v := range arr[1:] {
        if v > m { m = v }
    }
    return m, true
}
```

### 21.10 Forgetting That Go's `append` May or May Not Reallocate

```go
// DANGEROUS ASSUMPTION: append always creates a new array
original := make([]int, 3, 10)   // len=3, cap=10
original[0], original[1], original[2] = 1, 2, 3

derived := append(original, 4)   // NO reallocation (cap=10 > len=3)
// original and derived share the same backing array!

derived[0] = 99
fmt.Println(original[0])   // prints 99, not 1!

// SAFE PATTERN: explicitly copy before appending if you need independence
derived := make([]int, len(original), len(original)+1)
copy(derived, original)
derived = append(derived, 4)
```

### 21.11 C: Stack Overflow with Large Arrays

```c
// WRONG: large array on stack → stack overflow
void dangerous() {
    int arr[10000000];   // ~40MB on stack → crash (stack typically 1-8MB)
    ...
}

// CORRECT: use heap for large arrays
void safe() {
    int *arr = malloc(10000000 * sizeof(int));
    if (!arr) { /* handle OOM */ return; }
    ...
    free(arr);
}
```

### 21.12 Two-Pointer: Not Handling Duplicates

```go
// WRONG: two-sum pair finder with duplicates, returns same element twice
func twoSum(arr []int, target int) [][2]int {
    var result [][2]int
    lo, hi := 0, len(arr)-1
    for lo < hi {
        s := arr[lo] + arr[hi]
        if s == target {
            result = append(result, [2]int{arr[lo], arr[hi]})
            lo++; hi--
            // BUG: not skipping duplicates
            // If arr = [1,1,2,3,3] target=4, we get [1,3],[1,3]
        } else if s < target { lo++ } else { hi-- }
    }
    return result
}

// CORRECT: skip duplicates after finding a pair
if s == target {
    result = append(result, [2]int{arr[lo], arr[hi]})
    for lo < hi && arr[lo] == arr[lo+1] { lo++ }   // skip duplicates
    for lo < hi && arr[hi] == arr[hi-1] { hi-- }   // skip duplicates
    lo++; hi--
}
```

### 21.13 Prefix Sum: Wrong Index Offset

```go
// WRONG: off-by-one in prefix sum access
prefix := buildPrefix(arr)
// arr has n elements, prefix has n+1 elements (with prefix[0]=0)

// Querying sum of arr[l..r] (inclusive):
sum := prefix[r] - prefix[l]      // WRONG: misses arr[r]
sum := prefix[r+1] - prefix[l]    // CORRECT
```

### 21.14 Modifying a Function's Copy of the Slice Header (Go)

```go
// WRONG: expecting the caller's slice to grow
func addElement(arr []int, val int) {
    arr = append(arr, val)   // modifies the LOCAL copy of the slice header
    // caller's slice is unchanged!
}

func main() {
    s := []int{1, 2, 3}
    addElement(s, 4)
    fmt.Println(s)   // [1 2 3] — 4 was NOT added!
}

// CORRECT: return the new slice
func addElement(arr []int, val int) []int {
    return append(arr, val)
}
s = addElement(s, 4)   // [1 2 3 4]

// OR: pass pointer to slice
func addElement(arr *[]int, val int) {
    *arr = append(*arr, val)
}
```

### 21.15 Kadane's Algorithm: All-Negative Arrays

```go
// WRONG: initializing max to 0 fails for all-negative arrays
func kadane(arr []int) int {
    curr, maxSum := 0, 0   // ← wrong! 0 is wrong if all elements are negative
    for _, v := range arr {
        curr += v
        if curr < 0 { curr = 0 }
        if curr > maxSum { maxSum = curr }
    }
    return maxSum   // returns 0 for [-3,-1,-2], but correct answer is -1
}

// CORRECT: initialize to first element
func kadane(arr []int) int {
    curr, maxSum := arr[0], arr[0]
    for _, v := range arr[1:] {
        if curr+v > v { curr = curr + v } else { curr = v }
        if curr > maxSum { maxSum = curr }
    }
    return maxSum
}
```

### 21.16 Binary Search: Infinite Loop

```go
// WRONG: mid calculation causes infinite loop when lo = hi - 1
lo, hi := 0, 5
// if arr[mid] < target: lo = mid
// but mid = (0+1)/2 = 0, so lo never advances → infinite loop!

// CORRECT patterns:
// Pattern 1: lo <= hi, adjust both sides past mid
for lo <= hi {
    mid := lo + (hi-lo)/2
    if arr[mid] == target { return mid }
    if arr[mid] < target { lo = mid + 1 }   // +1, not =mid
    else { hi = mid - 1 }                   // -1, not =mid
}

// Pattern 2: lo < hi, narrow to single element
for lo < hi {
    mid := lo + (hi-lo)/2
    if arr[mid] < target { lo = mid + 1 }
    else { hi = mid }   // not mid-1
}
// check arr[lo] == target after loop
```

### 21.17 Rotation with k > n

```go
// WRONG: rotating by k when k > n causes wrong results or infinite loops
func leftRotate(arr []int, k int) {
    // missing: k = k % n
    reverseRange(arr, 0, k-1)   // PANIC if k > len(arr)!
}

// CORRECT:
func leftRotate(arr []int, k int) {
    n := len(arr)
    if n == 0 { return }
    k = k % n   // normalize
    if k == 0 { return }
    // ... rest of algorithm
}
```

### 21.18 Rust: Index Panic vs get()

```rust
// Panics in production — hard to debug
let val = arr[user_provided_index];

// CORRECT: use .get() for untrusted indices
match arr.get(user_provided_index) {
    Some(&val) => println!("Found: {}", val),
    None => println!("Index out of bounds"),
}
```

### 21.19 Wrong Merge Direction for In-Place Merge

```c
// WRONG: merging two sorted halves forward overwrites unseen elements
// When merging A[0..m-1] and A[m..n-1] with no extra space,
// writing from the front overwrites elements of the first half
// that haven't been compared yet.

// CORRECT: merge from the BACK when one array has trailing space
// (see Section 16.2 for the correct implementation)
```

### 21.20 Not Pre-allocating in Go Loops

```go
// SLOW: repeated allocation inside loop
var result []int
for i := 0; i < 1000000; i++ {
    result = append(result, i)   // many reallocations
}

// FAST: pre-allocate known capacity
result := make([]int, 0, 1000000)
for i := 0; i < 1000000; i++ {
    result = append(result, i)   // no reallocation
}
```

---

## 22. Complexity Reference Table

| Operation | Array (Static) | Dynamic Array (avg) | Notes |
|---|---|---|---|
| Access by index | O(1) | O(1) | Direct address computation |
| Search (unsorted) | O(n) | O(n) | Linear scan |
| Search (sorted) | O(log n) | O(log n) | Binary search |
| Insert at end | N/A | O(1) amortized | May cause reallocation |
| Insert at front | O(n) | O(n) | Shifts all elements |
| Insert at middle | O(n) | O(n) | Shifts n/2 elements on avg |
| Delete at end | O(1) | O(1) | Decrement length |
| Delete at front | O(n) | O(n) | Shifts all elements |
| Delete at middle | O(n) | O(n) | Shifts n/2 elements on avg |
| Reverse | O(n) | O(n) | n/2 swaps |
| Sort | O(n log n) | O(n log n) | Comparison sort lower bound |
| Range sum query | O(n) | O(n) | O(1) with prefix sum |
| Range update | O(n) | O(n) | O(1) with difference array |
| Rotate | O(n) | O(n) | Three-reversal trick |
| Merge (2 sorted) | O(n+m) | O(n+m) | Two-pointer |
| Sliding window | O(n) | O(n) | Fixed or variable window |
| Matrix transpose | O(n²) | O(n²) | In-place for square matrix |
| Matrix rotation 90° | O(n²) | O(n²) | Transpose + reverse rows |

---

## Mental Model Summary

The single most important thing to internalize about arrays:

**An array is a contiguous block of memory. Everything is arithmetic on a base pointer.**

From this, derive all behavior:

1. **Index access is O(1)** because it is one multiply and one add.
2. **Sequential iteration is fast** because the hardware prefetcher predicts the next address.
3. **Insertion/deletion in the middle is O(n)** because you must physically move bytes.
4. **Cache efficiency is unmatched** because data is packed with no gaps or pointers.
5. **Size must be known** for static arrays; dynamic arrays trade some wasted capacity for flexibility.
6. **Slices in Go share backing arrays** — mutation of one can affect the other.
7. **Rust borrows prevent dangling references** to array elements that a reallocation would invalidate.
8. **Every boundary is an opportunity for an off-by-one error** — always test with empty, single-element, and two-element arrays.

When you think about array problems, always ask:
- Can I preprocess? (prefix sums, sorting)
- Can I use two pointers instead of nested loops?
- Can I use a sliding window instead of recomputing the window each step?
- Am I copying when I should be slicing, or slicing when I should be copying?
- Have I handled the empty array, k=0, k=n, and k>n edge cases?
