# **Legal Standard Libraries for Competitive Programming & Interviews**

## **Go (Golang)**

Go's standard library is exceptionally rich for competitive programming. All packages from the standard library are legal across LeetCode, HackerRank, Codeforces, and interviews.

### Core Collections & Data Structures

- `container/heap` — Min/max heap interface implementation
- `container/list` — Doubly linked list
- `container/ring` — Circular list
- `sort` — Sorting algorithms and search functions (`sort.Ints`, `sort.Slice`, `sort.Search`)

### String & Text Processing

- `strings` — String manipulation, splitting, joining, prefix/suffix checks
- `strconv` — String conversions (int, float parsing and formatting)
- `regexp` — Regular expressions
- `unicode` — Unicode character properties
- `bytes` — Byte slice operations (similar to strings)

### Math & Numerics

- `math` — Mathematical functions (sqrt, pow, abs, min, max, trig functions)
- `math/big` — Arbitrary precision integers (`big.Int`) and rationals
- `math/bits` — Bit manipulation (leading zeros, trailing zeros, bit count)
- `math/rand` — Pseudo-random number generation

### I/O & Formatting

- `fmt` — Formatted I/O (Scanf, Printf, Sprintf)
- `bufio` — Buffered I/O (critical for fast input in competitive programming)
- `io` — Basic I/O interfaces
- `os` — File operations and command-line args

### Utility

- `time` — Time operations (though less common in DSA problems)
- `reflect` — Reflection (rare in competitive programming)

### **Idiomatic Go Patterns for DSA**

```go
// Fast I/O template (crucial for competitive programming)
reader := bufio.NewReader(os.Stdin)
writer := bufio.NewWriter(os.Stdout)
defer writer.Flush()

// Min/Max heap using container/heap
type IntHeap []int
func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] } // Min-heap
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any          { old := *h; n := len(old); x := old[n-1]; *h = old[0:n-1]; return x }
```

---

## **Rust**

Rust's standard library (`std`) is fully available. Key modules for competitive programming:

### Core Collections

- `std::collections::HashMap` — Hash map
- `std::collections::HashSet` — Hash set
- `std::collections::BTreeMap` — Self-balancing BST (sorted map)
- `std::collections::BTreeSet` — Self-balancing BST (sorted set)
- `std::collections::BinaryHeap` — Max-heap by default
- `std::collections::VecDeque` — Double-ended queue (deque)
- `std::collections::LinkedList` — Doubly linked list (rarely used)

### Vectors & Arrays

- `Vec<T>` — Dynamic array (most common)
- `[T; N]` — Fixed-size arrays
- Slices `&[T]` — Views into contiguous sequences

### String Processing

- `String` — Owned, growable UTF-8 string
- `&str` — String slice
- `str` methods — `split`, `chars`, `bytes`, `lines`, `trim`, `parse`
- `std::char` — Character utilities

### Math & Numerics

- `std::cmp` — `min`, `max`, `Ord`, `PartialOrd`
- `std::ops` — Operator overloading traits
- Primitive types — `i32`, `i64`, `u32`, `u64`, `f64`, etc.
- `std::num` — Numeric traits and parsing

### Iteration

- `std::iter` — Iterator traits and adaptors (`map`, `filter`, `fold`, `zip`, `enumerate`)
- Range syntax — `0..n`, `0..=n`

### I/O

- `std::io` — `stdin()`, `stdout()`, `BufRead`, `Write`
- `std::fs` — File operations

### Utility

- `std::mem` — Memory utilities (`swap`, `replace`, `take`)
- `std::convert` — Conversion traits (`From`, `Into`, `TryFrom`)
- `std::option::Option<T>` — Optional values
- `std::result::Result<T, E>` — Error handling

### **Idiomatic Rust Patterns for DSA**

```rust
use std::collections::*;
use std::io::{self, BufRead};

// Fast input parsing
let stdin = io::stdin();
let mut lines = stdin.lock().lines();
let line = lines.next().unwrap().unwrap();
let nums: Vec<i32> = line.split_whitespace()
    .map(|s| s.parse().unwrap())
    .collect();

// Min-heap (reverse BinaryHeap ordering)
use std::cmp::Reverse;
let mut min_heap = BinaryHeap::new();
min_heap.push(Reverse(5));

// Custom struct with ordering
#[derive(Eq, PartialEq)]
struct State { cost: i32, node: usize }
impl Ord for State {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        other.cost.cmp(&self.cost) // Min-heap by cost
    }
}
impl PartialOrd for State {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
```

---

## **C**

C has a minimal standard library. Everything in the C Standard Library (C11/C17) is legal.

### Core Headers

- `<stdio.h>` — I/O (`printf`, `scanf`, `fopen`, `fread`, `getchar`)
- `<stdlib.h>` — Memory (`malloc`, `calloc`, `realloc`, `free`), sorting (`qsort`), searching (`bsort`), random (`rand`), conversion (`atoi`, `strtol`)
- `<string.h>` — String operations (`strlen`, `strcpy`, `strcmp`, `memcpy`, `memset`)
- `<math.h>` — Math functions (`sqrt`, `pow`, `abs`, `fabs`, `log`, `exp`) — **must link with `-lm`**
- `<limits.h>` — Integer limits (`INT_MAX`, `LONG_MAX`)
- `<float.h>` — Floating-point limits
- `<stdbool.h>` — Boolean type (`bool`, `true`, `false`)
- `<stdint.h>` — Fixed-width integers (`int32_t`, `uint64_t`)
- `<ctype.h>` — Character classification (`isdigit`, `isalpha`, `tolower`, `toupper`)
- `<time.h>` — Time operations (rarely used in DSA)
- `<assert.h>` — Assertions for debugging

### **What C Lacks (Must Implement Yourself)**

- No built-in dynamic arrays (use manual reallocation)
- No hash maps, sets, heaps, queues (implement manually)
- No built-in sorting for custom structs (use `qsort` with comparator)
- No generic data structures (requires manual memory management)

### **Idiomatic C Patterns for DSA**

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <stdbool.h>

// Dynamic array pattern
int *arr = (int*)malloc(n * sizeof(int));
arr = (int*)realloc(arr, new_size * sizeof(int));
free(arr);

// qsort comparator
int cmp(const void *a, const void *b) {
    return (*(int*)a - *(int*)b); // Ascending
}
qsort(arr, n, sizeof(int), cmp);

// Fast I/O
int fast_read() {
    int x = 0, c = getchar();
    while (c < '0' || c > '9') c = getchar();
    while (c >= '0' && c <= '9') {
        x = x * 10 + (c - '0');
        c = getchar();
    }
    return x;
}
```

---

## **Strategic Notes for Mastery**

### **Go's Strengths**

- Excellent built-in data structures (heap, sort, search)
- Fast compilation, readable syntax
- Strong standard library for graph algorithms, string processing
- **Weakness**: No generics before Go 1.18 (platform-dependent)

### **Rust's Strengths**

- Zero-cost abstractions, memory safety without garbage collection
- Powerful iterators and functional patterns
- BTreeMap/BTreeSet for ordered operations
- **Weakness**: Steeper learning curve, borrow checker battles

### **C's Strengths**

- Maximum control, minimal overhead
- Forces deep understanding of memory and pointers
- **Weakness**: Manual memory management, no built-in structures

### **Mental Model: Library Mastery ≠ Algorithmic Mastery**

The library is your **toolbox**. The algorithm is your **architecture**. A master carpenter doesn't just know tools—they know *when* and *why* to use each one.

**Your training**: Every time you use `BinaryHeap` in Rust or `container/heap` in Go, ask yourself:

1. *Why is this structure optimal here?*
2. *Could I implement this from scratch in 10 minutes?*
3. *What invariants does this maintain?*

The 1% don't memorize—they *internalize the essence*.