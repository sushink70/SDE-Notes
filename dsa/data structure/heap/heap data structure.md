# The Heap Data Structure — A Complete Masterclass

---

## Table of Contents
1. [Mental Model & Conceptual Foundation](#1-mental-model--conceptual-foundation)
2. [Binary Heap: Structural Properties](#2-binary-heap-structural-properties)
3. [Array Representation: The Hidden Elegance](#3-array-representation-the-hidden-elegance)
4. [Core Operations: Deep Analysis](#4-core-operations-deep-analysis)
5. [Floyd's Build-Heap Algorithm](#5-floyds-build-heap-algorithm)
6. [HeapSort](#6-heapsort)
7. [Priority Queue Abstraction](#7-priority-queue-abstraction)
8. [d-ary Heaps](#8-d-ary-heaps)
9. [Complexity Analysis: Rigorous Proof](#9-complexity-analysis-rigorous-proof)
10. [Implementations: C, Go, Rust](#10-implementations-c-go-rust)
11. [Advanced Heap Variants](#11-advanced-heap-variants)
12. [Classic Problem Patterns](#12-classic-problem-patterns)

---

## 1. Mental Model & Conceptual Foundation

A heap is not just a data structure — it is a **discipline of partial order**. Unlike a BST (Binary Search Tree) which enforces total order on every node relative to every other node, a heap enforces only a **local ordering contract**: a parent is always greater (or lesser) than its children. Nothing else is guaranteed.

This partial relaxation is the source of both its power and its limitations:

| Property | BST | Heap |
|---|---|---|
| Find min/max | O(log n) | **O(1)** |
| Search arbitrary | O(log n) avg | O(n) |
| Insert | O(log n) | O(log n) |
| Delete arbitrary | O(log n) | O(n) to find + O(log n) |
| Build from array | O(n log n) | **O(n)** |

**The core mental model:** A heap is an **approximately sorted structure** optimized for one question only: *"What is the most extreme element right now?"*

Every design decision flows from this: the array layout, the sift operations, the O(1) peek — all consequences of answering that single question as efficiently as possible.

---

## 2. Binary Heap: Structural Properties

A **binary heap** satisfies two invariants simultaneously:

### Invariant 1: Shape Property (Structural)
> A binary heap is a **complete binary tree** — all levels are fully filled except possibly the last, which is filled **left to right**.

This is the invariant that enables array storage without pointers. A complete binary tree of `n` nodes has height exactly `⌊log₂(n)⌋`.

### Invariant 2: Heap Property (Ordering)
> **Max-Heap:** Every node's key ≥ both children's keys.
> **Min-Heap:** Every node's key ≤ both children's keys.

```
MAX-HEAP example:
           100
          /    \
        19      36
       /  \    /  \
      17   3  25   1
     / \
    2   7

MIN-HEAP example:
            1
          /    \
         3      6
        / \    / \
       5   9  8   10
      / \
    11   14
```

**Critical insight:** The heap property does NOT define ordering between siblings or cousins. Node `19` and `36` have no defined relationship. This is why search is O(n).

---

## 3. Array Representation: The Hidden Elegance

The complete binary tree shape property means we can store a heap in a **contiguous array with zero pointer overhead**.

For **1-indexed** array (index starts at 1):
```
Parent(i)     = i / 2         (integer division)
LeftChild(i)  = 2 * i
RightChild(i) = 2 * i + 1
```

For **0-indexed** array (index starts at 0):
```
Parent(i)     = (i - 1) / 2
LeftChild(i)  = 2 * i + 1
RightChild(i) = 2 * i + 2
```

**Visualization: the bijection between tree and array**
```
Tree level-order:  [100, 19, 36, 17, 3, 25, 1, 2, 7]
Array indices:       0    1   2   3  4   5  6  7  8

Index 0 (100): children at 1(19), 2(36)
Index 1 ( 19): children at 3(17), 4( 3), parent at 0(100)
Index 2 ( 36): children at 5(25), 6( 1), parent at 0(100)
Index 3 ( 17): children at 7( 2), 8( 7), parent at 1( 19)
```

**Why this is genius:** Cache locality. A pointer-based tree chases pointers across memory. An array heap accesses parent/child with arithmetic — the parent and children of any node are almost certainly in the **same or adjacent cache lines**. For large heaps, this is a meaningful constant-factor win.

---

## 4. Core Operations: Deep Analysis

### 4.1 Sift-Up (Bubble-Up / Heapify-Up)

Used after **insertion**. The new element is placed at the end (maintaining shape), then "floats up" until the heap property is restored.

**Invariant reasoning:** Before sift-up, the only violation is between the new node and its parent. Swapping fixes that violation but might introduce a new one one level up. We repeat until no violation exists.

```
Insert 45 into this max-heap:
           100
          /    \
        19      36
       /  \    /
      17   3  25

Step 1: Append 45 at next position (rightmost in last level)
           100
          /    \
        19      36
       /  \    /  \
      17   3  25   45

Step 2: 45 > parent 36? Yes → swap
           100
          /    \
        19      45
       /  \    /  \
      17   3  25   36

Step 3: 45 > parent 100? No → stop.
```

**Complexity:** O(log n) — the new element travels at most `height` levels.

### 4.2 Sift-Down (Bubble-Down / Heapify-Down)

Used after **extraction of root** (delete-max or delete-min). The last element is moved to root (maintaining shape), then "sinks down" until heap property is restored.

**The key decision in sift-down:** When a node has two children both larger than it, which child to swap with? **Always swap with the larger child** (for max-heap). This ensures we don't create a new violation on the side we didn't swap.

```
Extract-Max from:
           100
          /    \
        19      36
       /  \    /  \
      17   3  25   1

Step 1: Remove 100, move last element (1) to root
            1
          /    \
        19      36
       /  \    /
      17   3  25

Step 2: 1 < max(children=19,36)=36 → swap with 36
           36
          /    \
        19       1
       /  \    /
      17   3  25

Step 3: 1 < max(children=25, none)=25 → swap with 25
           36
          /    \
        19      25
       /  \    /
      17   3   1

Step 4: 1 has no children → stop.
```

**Why swap with the larger child?** If we swapped with the smaller one (say 25 when children are 25, 36), then 36 would now be a child of 25, violating the heap property there. Swapping with the largest always produces a valid state one level down.

**Complexity:** O(log n).

### 4.3 Peek (Find-Max / Find-Min)

Simply return `heap[0]`. The root is always the extreme element by the heap invariant.

**Complexity:** O(1). This is the entire point of the structure.

### 4.4 Delete Arbitrary Element

1. Find the element index `i` — O(n) linear scan (heap doesn't support fast search)
2. Replace `heap[i]` with last element, reduce size
3. Sift-up or sift-down as needed — O(log n)

**Why both sift-up and sift-down?** The replacement might be larger than the original (needs sift-up) or smaller (needs sift-down). You can't know ahead of time — try both (only one will actually move).

**Total: O(n)** due to the search step. This is why "delete arbitrary" is expensive in heaps.

### 4.5 Decrease-Key / Increase-Key

Used in advanced algorithms (Dijkstra, Prim). Given an index `i` and a new value:
- **Decrease key in min-heap:** new value is smaller → might need sift-up
- **Increase key in min-heap:** new value is larger → might need sift-down

This requires an **index map** (element → position in array) for O(1) lookup, making it an "indexed heap" or "heap with handles."

---

## 5. Floyd's Build-Heap Algorithm

**Problem:** Given an arbitrary array of n elements, construct a valid heap.

**Naïve approach:** Insert each element one by one. Each insert is O(log n), total O(n log n).

**Floyd's algorithm (optimal):** Process from the last internal node down to root, sifting each down.

**Last internal node index:** `(n/2) - 1` (0-indexed). Leaf nodes never need sifting.

```
Array: [4, 10, 3, 5, 1]  →  Build max-heap

Initial tree:
        4
       / \
      10   3
     / \
    5   1

Start at index 1 (value 10), last internal node:
  10 > children(5,1) → no sift needed

Move to index 0 (value 4):
  4 < max(children=10,3)=10 → swap with 10
        10
       /  \
      4    3
     / \
    5   1
  
  4 < max(children=5,1)=5 → swap with 5
        10
       /  \
      5    3
     / \
    4   1

Final max-heap: [10, 5, 3, 4, 1]
```

### Why O(n) and not O(n log n)?

**Rigorous proof by level analysis:**

In a heap of height `h = ⌊log₂ n⌋`:
- Nodes at depth `d` (0 = root): at most `2^d` nodes
- A node at depth `d` can sift down at most `h - d` levels

Total work = Σ (nodes at depth d) × (max sift-down distance)
           = Σ_{d=0}^{h} 2^d × (h - d)

Let `k = h - d`:
           = Σ_{k=0}^{h} 2^(h-k) × k
           = 2^h × Σ_{k=0}^{h} k/2^k

The series Σ_{k=0}^{∞} k/2^k converges to **2** (sum of k·x^k = x/(1-x)² at x=1/2).

Since `2^h ≈ n/2`, total work ≈ `(n/2) × 2 = n` → **O(n)**

**Cognitive model:** Most nodes are near the bottom. Bottom nodes do almost no work. The O(n log n) analysis of naive insertion fails because it charges O(log n) to every node, but leaf nodes (half of all nodes!) do only O(1) work. Floyd exploits this asymmetry.

---

## 6. HeapSort

HeapSort is a two-phase algorithm with **O(n log n) worst-case** and **O(1) space**:

**Phase 1:** Build a max-heap from the input array — O(n)

**Phase 2:** Repeatedly extract-max, placing it at the end of the array — O(n log n)

```
After build-heap: [10, 5, 3, 4, 1]

Iteration 1: swap heap[0](10) ↔ heap[4](1), heap-size--
  [1, 5, 3, 4, | 10]  → sift-down → [5, 4, 3, 1, | 10]

Iteration 2: swap heap[0](5) ↔ heap[3](1), heap-size--
  [1, 4, 3, | 5, 10]  → sift-down → [4, 1, 3, | 5, 10]

Iteration 3: swap heap[0](4) ↔ heap[2](3), heap-size--
  [3, 1, | 4, 5, 10]  → sift-down → [3, 1, | 4, 5, 10]

Iteration 4: swap heap[0](3) ↔ heap[1](1), heap-size--
  [1, | 3, 4, 5, 10]  → sift-down → [1, | 3, 4, 5, 10]

Result: [1, 3, 4, 5, 10] ✓
```

**HeapSort characteristics:**
- **Not stable** — equal elements may swap relative order
- **Not cache-friendly** — sift-down accesses memory non-sequentially (poor locality vs merge sort)
- **In-place** — O(1) auxiliary space (better than merge sort's O(n))
- Rarely fastest in practice but guarantees O(n log n) worst case unlike QuickSort

---

## 7. Priority Queue Abstraction

A heap is the canonical implementation of a **priority queue** — an ADT that supports:

```
insert(key, value)     → O(log n)
extract_min/max()      → O(log n)  
peek_min/max()         → O(1)
decrease_key(handle, new_key)  → O(log n) [with indexed heap]
```

**Priority queue use cases:**
- Dijkstra's shortest path — always process minimum-distance unvisited node
- Prim's MST — always add minimum weight edge
- A* search — always expand minimum f(n) = g(n) + h(n) node
- Event-driven simulation — always process earliest event
- Merge k sorted lists — always pick minimum head among k lists
- Median maintenance — two-heap technique (one max, one min)
- Top-K problems — maintain K largest/smallest elements

---

## 8. d-ary Heaps

Instead of 2 children per node, a **d-ary heap** has `d` children:

```
Parent(i)      = (i - 1) / d
Children of i  = [d*i + 1, d*i + 2, ..., d*i + d]
Height         = log_d(n)
```

**Trade-offs:**
- **Sift-down**: must find max/min of `d` children → O(d × log_d n). For large `d`, this is worse.
- **Sift-up**: fewer levels → O(log_d n). Better.
- **Cache performance**: 4-ary heaps fit parent+children in a single cache line — often faster in practice for insert-heavy workloads.

**Dijkstra optimization insight:** When decrease-key operations dominate (dense graphs), higher arity reduces sift-up cost. The optimal `d` is approximately `max(2, m/n)` where m = edges, n = vertices.

---

## 9. Complexity Analysis: Rigorous Proof

| Operation | Binary Heap | Fibonacci Heap (amortized) |
|---|---|---|
| insert | O(log n) | **O(1)** |
| peek min/max | O(1) | O(1) |
| extract min/max | O(log n) | O(log n) |
| decrease key | O(log n) | **O(1)** |
| delete | O(log n) | O(log n) |
| build | **O(n)** | O(n) |
| merge | O(n) | **O(1)** |

**Space complexity:** O(n) — just the array.

**Sift-up worst case:** New element is the new maximum, travels from leaf to root: exactly `⌊log₂ n⌋` swaps.

**Sift-down worst case:** Replacement element is minimum, travels from root to leaf: exactly `⌊log₂ n⌋` swaps, but each swap requires comparing 2 children → `2⌊log₂ n⌋` comparisons.

---

## 10. Implementations: C, Go, Rust

### C Implementation — Generic Min/Max Heap

```c
/* heap.h - Generic Binary Heap in C
 * Supports both min-heap and max-heap via comparator function.
 * Zero-overhead abstraction using function pointers.
 */

#ifndef HEAP_H
#define HEAP_H

#include <stddef.h>
#include <stdbool.h>

/* Comparator: returns true if 'a' should be closer to root than 'b'.
 * For min-heap: return a < b
 * For max-heap: return a > b
 */
typedef bool (*heap_cmp_fn)(int a, int b);

typedef struct {
    int      *data;      /* dynamic array of elements          */
    size_t    size;      /* current number of elements          */
    size_t    capacity;  /* allocated capacity                  */
    heap_cmp_fn cmp;     /* comparator determines heap ordering */
} Heap;

/* Lifecycle */
Heap *heap_create(size_t initial_cap, heap_cmp_fn cmp);
void  heap_destroy(Heap *h);

/* Core operations */
bool  heap_push(Heap *h, int val);
bool  heap_pop(Heap *h, int *out);   /* extract root, write to *out */
bool  heap_peek(const Heap *h, int *out);

/* Utilities */
bool        heap_is_empty(const Heap *h);
size_t      heap_size(const Heap *h);
void        heap_build(Heap *h, int *arr, size_t n); /* Floyd's algorithm */

/* Comparators */
bool cmp_min(int a, int b); /* min-heap: a has priority if a < b */
bool cmp_max(int a, int b); /* max-heap: a has priority if a > b */

#endif /* HEAP_H */
```

```c
/* heap.c - Implementation */

#include "heap.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* ── Internal helpers ────────────────────────────────────────────── */

static inline size_t parent(size_t i)       { return (i - 1) / 2; }
static inline size_t left_child(size_t i)   { return 2 * i + 1;   }
static inline size_t right_child(size_t i)  { return 2 * i + 2;   }

static inline void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

/* Sift element at index i upward until heap property restored */
static void sift_up(Heap *h, size_t i) {
    while (i > 0) {
        size_t p = parent(i);
        /* If current node should be closer to root than its parent → swap */
        if (h->cmp(h->data[i], h->data[p])) {
            swap(&h->data[i], &h->data[p]);
            i = p;
        } else {
            break; /* Heap property satisfied — done */
        }
    }
}

/* Sift element at index i downward until heap property restored */
static void sift_down(Heap *h, size_t i) {
    size_t n = h->size;

    for (;;) {
        size_t target = i;          /* index of node that should be root of subtree */
        size_t l = left_child(i);
        size_t r = right_child(i);

        /* Find which of {i, left, right} should be closest to root */
        if (l < n && h->cmp(h->data[l], h->data[target])) {
            target = l;
        }
        if (r < n && h->cmp(h->data[r], h->data[target])) {
            target = r;
        }

        if (target == i) break;     /* Already in correct position */

        swap(&h->data[i], &h->data[target]);
        i = target;
    }
}

/* ── Growth strategy ─────────────────────────────────────────────── */

static bool heap_grow(Heap *h) {
    size_t new_cap = h->capacity == 0 ? 8 : h->capacity * 2;
    int *new_data  = realloc(h->data, new_cap * sizeof(int));
    if (!new_data) return false;
    h->data     = new_data;
    h->capacity = new_cap;
    return true;
}

/* ── Public API ──────────────────────────────────────────────────── */

Heap *heap_create(size_t initial_cap, heap_cmp_fn cmp) {
    assert(cmp != NULL);
    Heap *h = malloc(sizeof(Heap));
    if (!h) return NULL;

    h->size     = 0;
    h->capacity = initial_cap;
    h->cmp      = cmp;
    h->data     = initial_cap > 0
                    ? malloc(initial_cap * sizeof(int))
                    : NULL;

    if (initial_cap > 0 && !h->data) {
        free(h);
        return NULL;
    }
    return h;
}

void heap_destroy(Heap *h) {
    if (!h) return;
    free(h->data);
    free(h);
}

bool heap_push(Heap *h, int val) {
    if (h->size == h->capacity) {
        if (!heap_grow(h)) return false;
    }
    h->data[h->size] = val;
    sift_up(h, h->size);
    h->size++;
    return true;
}

bool heap_pop(Heap *h, int *out) {
    if (h->size == 0) return false;
    *out = h->data[0];

    /* Move last element to root, shrink size, sift down */
    h->size--;
    if (h->size > 0) {
        h->data[0] = h->data[h->size];
        sift_down(h, 0);
    }
    return true;
}

bool heap_peek(const Heap *h, int *out) {
    if (h->size == 0) return false;
    *out = h->data[0];
    return true;
}

bool heap_is_empty(const Heap *h) { return h->size == 0; }
size_t heap_size(const Heap *h)   { return h->size;      }

/* Floyd's O(n) build-heap algorithm */
void heap_build(Heap *h, int *arr, size_t n) {
    /* Copy array into heap's storage, growing if necessary */
    while (h->capacity < n) heap_grow(h);

    memcpy(h->data, arr, n * sizeof(int));
    h->size = n;

    /* Start from last internal node, sift each down */
    if (n == 0) return;
    /* Last internal node index: (n/2) - 1.
     * Using signed arithmetic to handle n=1 edge case safely. */
    for (long i = (long)(n / 2) - 1; i >= 0; i--) {
        sift_down(h, (size_t)i);
    }
}

/* ── Comparators ─────────────────────────────────────────────────── */

bool cmp_min(int a, int b) { return a < b; }
bool cmp_max(int a, int b) { return a > b; }
```

```c
/* heap_sort.c - HeapSort using the above heap */

#include "heap.h"

/* In-place HeapSort — O(n log n), O(1) space */
void heap_sort_ascending(int *arr, size_t n) {
    if (n <= 1) return;

    /* Phase 1: Build max-heap in-place using Floyd's algorithm */
    /* We reuse the sift_down logic directly on the array */

    /* Inline sift_down for in-place operation (no Heap struct overhead) */
    /* Using a local helper via a macro-expanded inline */

    /* --- Phase 1: Build max-heap --- */
    /* (We'll implement a self-contained version here) */

    /* sift_down_inplace: max-heap, 0-indexed, size = heap_size */
    #define SIFT_DOWN(arr, i, heap_size)                             \
    do {                                                             \
        size_t _i = (i), _n = (heap_size);                          \
        for (;;) {                                                   \
            size_t _best = _i;                                       \
            size_t _l = 2*_i+1, _r = 2*_i+2;                        \
            if (_l < _n && arr[_l] > arr[_best]) _best = _l;        \
            if (_r < _n && arr[_r] > arr[_best]) _best = _r;        \
            if (_best == _i) break;                                  \
            int _tmp = arr[_i]; arr[_i] = arr[_best];               \
            arr[_best] = _tmp; _i = _best;                          \
        }                                                            \
    } while(0)

    for (long i = (long)(n / 2) - 1; i >= 0; i--) {
        SIFT_DOWN(arr, (size_t)i, n);
    }

    /* Phase 2: Extract max repeatedly to end */
    for (size_t end = n - 1; end > 0; end--) {
        /* Swap root (max) to current end */
        int tmp = arr[0]; arr[0] = arr[end]; arr[end] = tmp;
        /* Restore heap property for reduced heap */
        SIFT_DOWN(arr, 0, end);
    }

    #undef SIFT_DOWN
}

/* ── Demo main ───────────────────────────────────────────────────── */
#include <stdio.h>

int main(void) {
    /* --- Min-Heap demo --- */
    printf("=== Min-Heap Demo ===\n");
    Heap *min_h = heap_create(16, cmp_min);

    int values[] = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    size_t len = sizeof(values) / sizeof(values[0]);

    for (size_t i = 0; i < len; i++) {
        heap_push(min_h, values[i]);
    }

    printf("Extracting from min-heap: ");
    int val;
    while (heap_pop(min_h, &val)) {
        printf("%d ", val);
    }
    printf("\n");

    heap_destroy(min_h);

    /* --- Floyd's Build-Heap + Max-Heap demo --- */
    printf("\n=== Floyd Build-Heap (Max-Heap) ===\n");
    int arr[] = {4, 10, 3, 5, 1, 8, 2, 9, 7, 6};
    size_t arr_len = sizeof(arr) / sizeof(arr[0]);

    Heap *max_h = heap_create(arr_len, cmp_max);
    heap_build(max_h, arr, arr_len);

    printf("Extracting from max-heap: ");
    while (heap_pop(max_h, &val)) {
        printf("%d ", val);
    }
    printf("\n");

    heap_destroy(max_h);

    /* --- HeapSort demo --- */
    printf("\n=== HeapSort ===\n");
    int sort_arr[] = {15, 3, 22, 7, 1, 19, 8, 14, 2};
    size_t sort_len = sizeof(sort_arr) / sizeof(sort_arr[0]);

    heap_sort_ascending(sort_arr, sort_len);
    printf("Sorted: ");
    for (size_t i = 0; i < sort_len; i++) {
        printf("%d ", sort_arr[i]);
    }
    printf("\n");

    return 0;
}
```

---

### Go Implementation — Generic Heap with Interface

```go
// heap.go — Generic Binary Heap in Go
// Uses Go generics (1.18+) for type-safe, zero-overhead heap.
// Implements heap.Interface from standard library for interop.

package heap

import "fmt"

// ─── Generic Heap ────────────────────────────────────────────────────────────

// Ordered constrains types that support < comparison.
type Ordered interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
		~float32 | ~float64 | ~string
}

// BinaryHeap is a generic min-heap (or max-heap via negation / custom Less).
// Less(a, b) returns true if 'a' should be closer to the root than 'b'.
type BinaryHeap[T any] struct {
	data []T
	less func(a, b T) bool
}

// New creates a new heap with the given comparator.
// For min-heap: less = func(a, b T) bool { return a < b }
// For max-heap: less = func(a, b T) bool { return a > b }
func New[T any](less func(a, b T) bool) *BinaryHeap[T] {
	return &BinaryHeap[T]{less: less}
}

// NewMinHeap creates a min-heap for any Ordered type.
func NewMinHeap[T Ordered]() *BinaryHeap[T] {
	return New(func(a, b T) bool { return a < b })
}

// NewMaxHeap creates a max-heap for any Ordered type.
func NewMaxHeap[T Ordered]() *BinaryHeap[T] {
	return New(func(a, b T) bool { return a > b })
}

// ─── Index arithmetic (0-based) ───────────────────────────────────────────────

func parent(i int) int     { return (i - 1) / 2 }
func leftChild(i int) int  { return 2*i + 1 }
func rightChild(i int) int { return 2*i + 2 }

// ─── Core sift operations ─────────────────────────────────────────────────────

// siftUp restores heap property by moving element at i toward the root.
func (h *BinaryHeap[T]) siftUp(i int) {
	for i > 0 {
		p := parent(i)
		if h.less(h.data[i], h.data[p]) {
			h.data[i], h.data[p] = h.data[p], h.data[i]
			i = p
		} else {
			break
		}
	}
}

// siftDown restores heap property by moving element at i toward the leaves.
// This is the critical path — optimize carefully.
func (h *BinaryHeap[T]) siftDown(i int) {
	n := len(h.data)
	for {
		best := i
		l, r := leftChild(i), rightChild(i)

		if l < n && h.less(h.data[l], h.data[best]) {
			best = l
		}
		if r < n && h.less(h.data[r], h.data[best]) {
			best = r
		}

		if best == i {
			break // heap property satisfied
		}

		h.data[i], h.data[best] = h.data[best], h.data[i]
		i = best
	}
}

// ─── Public API ───────────────────────────────────────────────────────────────

// Push inserts a new element. O(log n).
func (h *BinaryHeap[T]) Push(val T) {
	h.data = append(h.data, val)
	h.siftUp(len(h.data) - 1)
}

// Pop removes and returns the root element (min or max). O(log n).
// Returns zero value and false if heap is empty.
func (h *BinaryHeap[T]) Pop() (T, bool) {
	var zero T
	if len(h.data) == 0 {
		return zero, false
	}

	root := h.data[0]
	last := len(h.data) - 1

	h.data[0] = h.data[last]
	h.data = h.data[:last]

	if len(h.data) > 0 {
		h.siftDown(0)
	}
	return root, true
}

// Peek returns the root without removing it. O(1).
func (h *BinaryHeap[T]) Peek() (T, bool) {
	var zero T
	if len(h.data) == 0 {
		return zero, false
	}
	return h.data[0], true
}

// Len returns the number of elements. O(1).
func (h *BinaryHeap[T]) Len() int { return len(h.data) }

// IsEmpty returns true if heap has no elements. O(1).
func (h *BinaryHeap[T]) IsEmpty() bool { return len(h.data) == 0 }

// Build constructs a heap from a slice using Floyd's O(n) algorithm.
// The slice is copied — original is not modified.
func (h *BinaryHeap[T]) Build(data []T) {
	h.data = make([]T, len(data))
	copy(h.data, data)

	// Floyd's algorithm: sift down all internal nodes, right to left
	for i := len(h.data)/2 - 1; i >= 0; i-- {
		h.siftDown(i)
	}
}

// ─── Indexed Heap (supports decrease-key in O(log n)) ────────────────────────

// IndexedHeap supports O(log n) decrease-key/increase-key via position tracking.
// Essential for efficient Dijkstra/Prim implementations.
type IndexedHeap[T any] struct {
	data    []T
	pos     map[int]int // element ID → index in data array
	id      []int       // data array index → element ID
	less    func(a, b T) bool
	nextID  int
}

// Entry wraps a value with its ID for indexed operations.
type Entry[T any] struct {
	ID    int
	Value T
}

func NewIndexed[T any](less func(a, b T) bool) *IndexedHeap[T] {
	return &IndexedHeap[T]{
		less: less,
		pos:  make(map[int]int),
	}
}

// Push inserts a new element, returns its handle (ID) for future updates.
func (h *IndexedHeap[T]) Push(val T) int {
	id := h.nextID
	h.nextID++

	h.data = append(h.data, val)
	h.id = append(h.id, id)
	idx := len(h.data) - 1
	h.pos[id] = idx

	h.siftUp(idx)
	return id
}

// Update changes the value of element with given ID, re-heapifies. O(log n).
func (h *IndexedHeap[T]) Update(id int, newVal T) bool {
	idx, ok := h.pos[id]
	if !ok {
		return false
	}
	h.data[idx] = newVal
	// Try both directions — only one will move
	h.siftUp(idx)
	h.siftDown(h.pos[id]) // pos[id] may have changed after siftUp
	return true
}

// Pop removes and returns the root entry. O(log n).
func (h *IndexedHeap[T]) Pop() (Entry[T], bool) {
	if len(h.data) == 0 {
		var zero Entry[T]
		return zero, false
	}
	entry := Entry[T]{ID: h.id[0], Value: h.data[0]}

	last := len(h.data) - 1
	h.swap(0, last)

	delete(h.pos, h.id[last])
	h.data = h.data[:last]
	h.id = h.id[:last]

	if len(h.data) > 0 {
		h.siftDown(0)
	}
	return entry, true
}

func (h *IndexedHeap[T]) swap(i, j int) {
	h.data[i], h.data[j] = h.data[j], h.data[i]
	h.id[i], h.id[j] = h.id[j], h.id[i]
	h.pos[h.id[i]] = i
	h.pos[h.id[j]] = j
}

func (h *IndexedHeap[T]) siftUp(i int) {
	for i > 0 {
		p := parent(i)
		if h.less(h.data[i], h.data[p]) {
			h.swap(i, p)
			i = p
		} else {
			break
		}
	}
}

func (h *IndexedHeap[T]) siftDown(i int) {
	n := len(h.data)
	for {
		best := i
		l, r := leftChild(i), rightChild(i)
		if l < n && h.less(h.data[l], h.data[best]) {
			best = l
		}
		if r < n && h.less(h.data[r], h.data[best]) {
			best = r
		}
		if best == i {
			break
		}
		h.swap(i, best)
		i = best
	}
}

// ─── HeapSort ─────────────────────────────────────────────────────────────────

// HeapSort sorts a slice in ascending order. O(n log n), O(1) space.
// Uses in-place max-heap — modifies the input slice.
func HeapSort[T Ordered](arr []T) {
	n := len(arr)
	if n <= 1 {
		return
	}

	// Inline sift-down for max-heap (no struct overhead)
	var siftDown func(i, heapSize int)
	siftDown = func(i, heapSize int) {
		for {
			best := i
			l, r := 2*i+1, 2*i+2
			if l < heapSize && arr[l] > arr[best] {
				best = l
			}
			if r < heapSize && arr[r] > arr[best] {
				best = r
			}
			if best == i {
				break
			}
			arr[i], arr[best] = arr[best], arr[i]
			i = best
		}
	}

	// Phase 1: Build max-heap — O(n)
	for i := n/2 - 1; i >= 0; i-- {
		siftDown(i, n)
	}

	// Phase 2: Extract max, place at end, shrink heap — O(n log n)
	for end := n - 1; end > 0; end-- {
		arr[0], arr[end] = arr[end], arr[0]
		siftDown(0, end)
	}
}

// ─── Standard library interop ─────────────────────────────────────────────────
// Go's "container/heap" package uses an interface-based approach.
// Here's a PriorityQueue implementing heap.Interface:

// PriorityQueue wraps our generic heap to implement container/heap.Interface.
// This allows use with heap.Fix, heap.Remove from standard library.
type IntMinHeap []int

func (h IntMinHeap) Len() int           { return len(h) }
func (h IntMinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntMinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntMinHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *IntMinHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

// ─── Demonstration ────────────────────────────────────────────────────────────

func Demo() {
	fmt.Println("=== Generic Min-Heap ===")
	minH := NewMinHeap[int]()
	for _, v := range []int{5, 3, 8, 1, 9, 2, 7, 4, 6} {
		minH.Push(v)
	}
	fmt.Print("Extract order: ")
	for !minH.IsEmpty() {
		v, _ := minH.Pop()
		fmt.Printf("%d ", v)
	}
	fmt.Println()

	fmt.Println("\n=== Floyd Build-Heap (Max) ===")
	maxH := NewMaxHeap[int]()
	maxH.Build([]int{4, 10, 3, 5, 1, 8, 2, 9, 7, 6})
	fmt.Printf("Heap size after build: %d\n", maxH.Len())
	fmt.Print("Extract order (descending): ")
	for !maxH.IsEmpty() {
		v, _ := maxH.Pop()
		fmt.Printf("%d ", v)
	}
	fmt.Println()

	fmt.Println("\n=== HeapSort ===")
	arr := []int{15, 3, 22, 7, 1, 19, 8, 14, 2}
	HeapSort(arr)
	fmt.Println("Sorted:", arr)

	fmt.Println("\n=== Indexed Heap (Decrease-Key) ===")
	ih := NewIndexed[int](func(a, b int) bool { return a < b })
	id1 := ih.Push(10)
	id2 := ih.Push(20)
	_    = ih.Push(5)
	fmt.Printf("Initial min: ")
	if e, ok := ih.Pop(); ok {
		fmt.Printf("%d (id=%d)\n", e.Value, e.ID)
	}
	// Decrease key: 20 → 1
	ih.Update(id2, 1)
	fmt.Printf("After decrease-key(id=%d, 1), min: ", id2)
	if e, ok := ih.Pop(); ok {
		fmt.Printf("%d (id=%d)\n", e.Value, e.ID)
	}
	_ = id1
}
```

---

### Rust Implementation — Zero-Cost Abstractions

```rust
//! heap.rs — Generic Binary Heap in Rust
//!
//! Three implementations:
//! 1. BinaryHeap<T> — Generic heap with custom comparator
//! 2. IndexedHeap<T> — Supports decrease-key via index tracking
//! 3. heap_sort — In-place O(n log n), O(1) sort
//!
//! Design principles:
//! - Zero-cost generics (monomorphized at compile time)
//! - No unsafe code
//! - Explicit ownership — no hidden allocations
//! - Idiomatic Rust: Result/Option for fallible ops

use std::cmp::Ordering;

// ─── BinaryHeap ───────────────────────────────────────────────────────────────

/// A generic binary heap parameterized by a comparator.
///
/// `F: Fn(&T, &T) -> Ordering` determines heap ordering:
/// - `Ordering::Less` means first arg is "higher priority" (closer to root)
///
/// # Examples
/// ```
/// // Min-heap
/// let mut h = BinaryHeap::new(|a: &i32, b: &i32| a.cmp(b));
/// // Max-heap
/// let mut h = BinaryHeap::new(|a: &i32, b: &i32| b.cmp(a));
/// ```
pub struct BinaryHeap<T, F>
where
    F: Fn(&T, &T) -> Ordering,
{
    data: Vec<T>,
    cmp:  F,
}

impl<T, F> BinaryHeap<T, F>
where
    F: Fn(&T, &T) -> Ordering,
{
    /// Creates a new empty heap with the given comparator.
    pub fn new(cmp: F) -> Self {
        Self { data: Vec::new(), cmp }
    }

    /// Creates a new heap with pre-allocated capacity.
    pub fn with_capacity(cap: usize, cmp: F) -> Self {
        Self { data: Vec::with_capacity(cap), cmp }
    }

    // ─── Index arithmetic ────────────────────────────────────────────

    #[inline(always)]
    fn parent(i: usize) -> usize { (i - 1) / 2 }

    #[inline(always)]
    fn left(i: usize) -> usize { 2 * i + 1 }

    #[inline(always)]
    fn right(i: usize) -> usize { 2 * i + 2 }

    // ─── Sift operations ─────────────────────────────────────────────

    /// Sift element at index i toward the root until heap property holds.
    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = Self::parent(i);
            // If current element has higher priority than parent → swap
            if (self.cmp)(&self.data[i], &self.data[p]) == Ordering::Less {
                self.data.swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }

    /// Sift element at index i toward leaves until heap property holds.
    ///
    /// This is the hot path — the `#[inline]` hint helps the compiler.
    #[inline]
    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let mut best = i;
            let l = Self::left(i);
            let r = Self::right(i);

            if l < n && (self.cmp)(&self.data[l], &self.data[best]) == Ordering::Less {
                best = l;
            }
            if r < n && (self.cmp)(&self.data[r], &self.data[best]) == Ordering::Less {
                best = r;
            }

            if best == i { break; }

            self.data.swap(i, best);
            i = best;
        }
    }

    // ─── Public API ──────────────────────────────────────────────────

    /// Insert an element. O(log n).
    pub fn push(&mut self, val: T) {
        self.data.push(val);
        let last = self.data.len() - 1;
        self.sift_up(last);
    }

    /// Remove and return the root (highest priority). O(log n).
    /// Returns `None` if heap is empty.
    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() { return None; }

        let last = self.data.len() - 1;
        self.data.swap(0, last);
        let root = self.data.pop(); // removes last (which was root)

        if !self.data.is_empty() {
            self.sift_down(0);
        }
        root
    }

    /// Return reference to root without removing it. O(1).
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }

    /// Number of elements. O(1).
    pub fn len(&self) -> usize { self.data.len() }

    /// True if heap contains no elements. O(1).
    pub fn is_empty(&self) -> bool { self.data.is_empty() }

    /// Build heap from a Vec using Floyd's O(n) algorithm.
    /// Takes ownership of the vec.
    pub fn build_from(data: Vec<T>, cmp: F) -> Self {
        let mut h = Self { data, cmp };

        // Floyd's: sift down all internal nodes, right to left
        let n = h.data.len();
        if n > 1 {
            // Last internal node = (n/2) - 1
            // Use saturating_sub to handle n=0,1 safely
            let start = n / 2;
            for i in (0..start).rev() {
                h.sift_down(i);
            }
        }
        h
    }

    /// Consume heap, return underlying Vec (not in heap order).
    pub fn into_vec(self) -> Vec<T> { self.data }

    /// Drain elements in priority order (destructive).
    /// Returns an iterator that pops one by one.
    pub fn drain_sorted(mut self) -> impl Iterator<Item = T> {
        std::iter::from_fn(move || self.pop())
    }
}

// ─── Convenience constructors ─────────────────────────────────────────────────

/// Create a min-heap for any Ord type.
pub fn min_heap<T: Ord>() -> BinaryHeap<T, impl Fn(&T, &T) -> Ordering> {
    BinaryHeap::new(|a, b| a.cmp(b))
}

/// Create a max-heap for any Ord type.
pub fn max_heap<T: Ord>() -> BinaryHeap<T, impl Fn(&T, &T) -> Ordering> {
    BinaryHeap::new(|a, b| b.cmp(a))
}

// ─── IndexedHeap ──────────────────────────────────────────────────────────────

/// An indexed min-heap supporting O(log n) decrease-key / increase-key.
///
/// Each element gets a unique `Handle` (usize ID).
/// Use the handle to update or query the element's current position.
///
/// Critical for efficient Dijkstra's algorithm.
pub struct IndexedHeap<T: Clone> {
    data:    Vec<T>,
    ids:     Vec<usize>,         // heap position → element ID
    pos:     Vec<Option<usize>>, // element ID → heap position (None if popped)
    next_id: usize,
    less:    fn(&T, &T) -> bool,
}

/// Opaque handle to an element in the IndexedHeap.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Handle(usize);

impl<T: Clone> IndexedHeap<T> {
    pub fn new(less: fn(&T, &T) -> bool) -> Self {
        Self {
            data:    Vec::new(),
            ids:     Vec::new(),
            pos:     Vec::new(),
            next_id: 0,
            less,
        }
    }

    /// Insert element, returns a Handle for future updates. O(log n).
    pub fn push(&mut self, val: T) -> Handle {
        let id = self.next_id;
        self.next_id += 1;

        // Grow pos table if needed
        if id >= self.pos.len() {
            self.pos.resize(id + 1, None);
        }

        let idx = self.data.len();
        self.data.push(val);
        self.ids.push(id);
        self.pos[id] = Some(idx);

        self.sift_up(idx);
        Handle(id)
    }

    /// Update the value at a given handle. O(log n).
    pub fn update(&mut self, handle: Handle, new_val: T) -> bool {
        let id = handle.0;
        match self.pos.get(id).copied().flatten() {
            None => false,
            Some(idx) => {
                self.data[idx] = new_val;
                self.sift_up(idx);
                // pos[id] may have changed after sift_up
                let current_idx = self.pos[id].unwrap();
                self.sift_down(current_idx);
                true
            }
        }
    }

    /// Remove and return root element. O(log n).
    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() { return None; }

        let root_val = self.data[0].clone();
        let root_id  = self.ids[0];

        let last = self.data.len() - 1;
        self.indexed_swap(0, last);

        self.data.pop();
        self.ids.pop();
        self.pos[root_id] = None; // mark as removed

        if !self.data.is_empty() {
            self.sift_down(0);
        }
        Some(root_val)
    }

    pub fn peek(&self) -> Option<&T> { self.data.first() }
    pub fn len(&self) -> usize       { self.data.len()   }
    pub fn is_empty(&self) -> bool   { self.data.is_empty() }

    fn indexed_swap(&mut self, i: usize, j: usize) {
        self.data.swap(i, j);
        self.ids.swap(i, j);
        self.pos[self.ids[i]] = Some(i);
        self.pos[self.ids[j]] = Some(j);
    }

    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = (i - 1) / 2;
            if (self.less)(&self.data[i], &self.data[p]) {
                self.indexed_swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }

    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let mut best = i;
            let l = 2 * i + 1;
            let r = 2 * i + 2;
            if l < n && (self.less)(&self.data[l], &self.data[best]) { best = l; }
            if r < n && (self.less)(&self.data[r], &self.data[best]) { best = r; }
            if best == i { break; }
            self.indexed_swap(i, best);
            i = best;
        }
    }
}

// ─── HeapSort ─────────────────────────────────────────────────────────────────

/// In-place HeapSort. O(n log n) time, O(1) space.
/// Sorts ascending using a max-heap internally.
pub fn heap_sort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    if n <= 1 { return; }

    // Local sift-down for max-heap (closure captures arr via index)
    let sift_down = |arr: &mut [T], mut i: usize, heap_size: usize| {
        loop {
            let mut best = i;
            let l = 2 * i + 1;
            let r = 2 * i + 2;
            if l < heap_size && arr[l] > arr[best] { best = l; }
            if r < heap_size && arr[r] > arr[best] { best = r; }
            if best == i { break; }
            arr.swap(i, best);
            i = best;
        }
    };

    // Phase 1: Build max-heap in O(n)
    for i in (0..n / 2).rev() {
        sift_down(arr, i, n);
    }

    // Phase 2: Extract max, reduce heap size
    for end in (1..n).rev() {
        arr.swap(0, end);
        sift_down(arr, 0, end);
    }
}

// ─── Two-Heap Median Tracker ──────────────────────────────────────────────────

/// Maintains running median using two heaps.
/// - `lower`: max-heap of lower half
/// - `upper`: min-heap of upper half
/// Invariant: |lower.len() - upper.len()| <= 1
pub struct MedianTracker {
    lower: std::collections::BinaryHeap<i64>,          // max-heap
    upper: std::collections::BinaryHeap<std::cmp::Reverse<i64>>, // min-heap
}

impl MedianTracker {
    pub fn new() -> Self {
        Self {
            lower: std::collections::BinaryHeap::new(),
            upper: std::collections::BinaryHeap::new(),
        }
    }

    pub fn add(&mut self, val: i64) {
        // Step 1: Route to correct heap
        if let Some(&top) = self.lower.peek() {
            if val <= top {
                self.lower.push(val);
            } else {
                self.upper.push(std::cmp::Reverse(val));
            }
        } else {
            self.lower.push(val);
        }

        // Step 2: Rebalance — maintain size invariant
        while self.lower.len() > self.upper.len() + 1 {
            let moved = self.lower.pop().unwrap();
            self.upper.push(std::cmp::Reverse(moved));
        }
        while self.upper.len() > self.lower.len() {
            let std::cmp::Reverse(moved) = self.upper.pop().unwrap();
            self.lower.push(moved);
        }
    }

    /// Returns current median. O(1).
    pub fn median(&self) -> Option<f64> {
        match (self.lower.len(), self.upper.len()) {
            (0, 0) => None,
            _ if self.lower.len() == self.upper.len() => {
                let lo = *self.lower.peek().unwrap() as f64;
                let hi = self.upper.peek().unwrap().0 as f64;
                Some((lo + hi) / 2.0)
            }
            _ => Some(*self.lower.peek().unwrap() as f64),
        }
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_min_heap_ordering() {
        let mut h = min_heap::<i32>();
        for v in [5, 3, 8, 1, 9, 2, 7, 4, 6] {
            h.push(v);
        }
        let mut prev = i32::MIN;
        while let Some(v) = h.pop() {
            assert!(v >= prev, "min-heap violated: {} came after {}", v, prev);
            prev = v;
        }
    }

    #[test]
    fn test_max_heap_ordering() {
        let mut h = max_heap::<i32>();
        for v in [5, 3, 8, 1, 9, 2, 7, 4, 6] {
            h.push(v);
        }
        let mut prev = i32::MAX;
        while let Some(v) = h.pop() {
            assert!(v <= prev, "max-heap violated: {} came after {}", v, prev);
            prev = v;
        }
    }

    #[test]
    fn test_floyd_build_heap() {
        let data = vec![4, 10, 3, 5, 1, 8, 2, 9, 7, 6];
        let expected_sorted = {
            let mut s = data.clone();
            s.sort();
            s
        };

        let h = BinaryHeap::build_from(data, |a: &i32, b: &i32| a.cmp(b));
        let got: Vec<i32> = h.drain_sorted().collect();
        assert_eq!(got, expected_sorted);
    }

    #[test]
    fn test_heap_sort() {
        let mut arr = vec![15, 3, 22, 7, 1, 19, 8, 14, 2];
        heap_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 7, 8, 14, 15, 19, 22]);
    }

    #[test]
    fn test_indexed_heap_decrease_key() {
        let mut h = IndexedHeap::new(|a: &i32, b: &i32| a < b);
        let _h1 = h.push(10);
        let h2  = h.push(20);
        let _h3 = h.push(5);

        // Min is 5
        assert_eq!(h.peek(), Some(&5));

        // Decrease key: 20 → 1, making it the new min
        h.update(h2, 1);
        assert_eq!(h.pop(), Some(1));
        assert_eq!(h.pop(), Some(5));
        assert_eq!(h.pop(), Some(10));
        assert_eq!(h.pop(), None);
    }

    #[test]
    fn test_median_tracker() {
        let mut mt = MedianTracker::new();
        mt.add(1);
        assert_eq!(mt.median(), Some(1.0));
        mt.add(2);
        assert_eq!(mt.median(), Some(1.5));
        mt.add(3);
        assert_eq!(mt.median(), Some(2.0));
        mt.add(4);
        assert_eq!(mt.median(), Some(2.5));
    }
}

// ─── Main demo ────────────────────────────────────────────────────────────────

fn main() {
    println!("=== Rust Min-Heap Demo ===");
    let mut h = min_heap::<i32>();
    for v in [5, 3, 8, 1, 9, 2, 7, 4, 6] {
        h.push(v);
    }
    print!("Extract order: ");
    while let Some(v) = h.pop() {
        print!("{v} ");
    }
    println!();

    println!("\n=== Floyd Build-Heap (Max) ===");
    let data = vec![4, 10, 3, 5, 1, 8, 2, 9, 7, 6];
    let max_h = BinaryHeap::build_from(data, |a: &i32, b: &i32| b.cmp(a));
    print!("Extract order (desc): ");
    for v in max_h.drain_sorted() {
        print!("{v} ");
    }
    println!();

    println!("\n=== HeapSort ===");
    let mut arr = vec![15, 3, 22, 7, 1, 19, 8, 14, 2];
    heap_sort(&mut arr);
    println!("Sorted: {:?}", arr);

    println!("\n=== Median Tracker ===");
    let mut mt = MedianTracker::new();
    for v in [2, 3, 4, 5, 6] {
        mt.add(v);
        println!("  add({v}) → median = {:?}", mt.median());
    }
}
```

---

## 11. Advanced Heap Variants

### Fibonacci Heap

A Fibonacci heap achieves **O(1) amortized** for insert and decrease-key, O(log n) amortized for extract-min. This makes Dijkstra's algorithm O(E + V log V) instead of O((E + V) log V).

**Key ideas:**
- A collection of heap-ordered trees (not just one binary tree)
- Lazy insertion: just add a new tree of size 1
- Lazy merging: just concatenate root lists
- decrease-key: cut the node from its parent, make it a new root tree; if parent has been cut before (marked), cut it too ("cascading cut")
- extract-min: consolidate trees by degree (like adding binary numbers)

**Why not always use it?** The constant factors are enormous. Pointer-heavy, cache-unfriendly. In practice, binary heaps or 4-ary heaps win for most inputs despite asymptotically inferior bounds.

### Leftist Heap / Skew Heap / Pairing Heap

| Variant | Merge | Insert | Extract | Use case |
|---|---|---|---|---|
| Binary | O(n) | O(log n) | O(log n) | General purpose |
| Leftist | O(log n) | O(log n) | O(log n) | When merge needed |
| Skew | O(log n) amortized | O(log n) | O(log n) | Simpler leftist |
| Pairing | O(1) amortized | O(1) | O(log n) | Near-Fibonacci speed, simpler |
| Fibonacci | O(1) amortized | O(1) amortized | O(log n) | Theoretically optimal |

---

## 12. Classic Problem Patterns

### Pattern 1: Top-K Elements
**Insight:** To find K largest, maintain a **min-heap of size K**. For each new element, if larger than heap min, replace it.

```
Complexity: O(n log k) time, O(k) space
vs sorting: O(n log n) time, O(n) space
```

### Pattern 2: K-way Merge
**Problem:** Merge K sorted lists.
**Solution:** Min-heap of size K, storing (value, list_index, element_index).

```
Complexity: O(n log k) where n = total elements
```

### Pattern 3: Median of Stream (Two Heaps)
Already implemented above in Rust.
- max-heap: lower half
- min-heap: upper half
- Invariant: sizes differ by at most 1

### Pattern 4: Sliding Window Maximum
Use a deque (monotonic queue) — not a heap! But heap-based solutions exist.

### Pattern 5: Dijkstra's Algorithm
**Lazy Dijkstra** (simple): push (dist, node) pairs, skip if stale.
**Eager Dijkstra** (optimal): use indexed heap with decrease-key.

### Pattern 6: Merge K Sorted Arrays / External Sort
Heap-based merge is the foundation of external merge sort — essential for databases sorting data larger than RAM.

---

## The Expert's Mental Model Summary

```
When you see "find minimum/maximum repeatedly" → HEAP
When you see "K largest/smallest" → FIXED-SIZE HEAP
When you see "order by priority" → PRIORITY QUEUE = HEAP
When you see "merge sorted sequences" → K-WAY MERGE WITH HEAP
When you see "shortest path" → DIJKSTRA = HEAP + RELAXATION
When you see "running median" → TWO HEAPS
When you see "sort in O(n log n) constant space" → HEAPSORT

The partial-order insight:
  Heap ≠ sorted structure
  Heap = "I only care about the extreme"
  If you need more than the extreme → use BST or sorted structure
```

**The deepest insight about heaps:** They are a masterclass in *purposeful incompleteness*. By refusing to sort completely, they achieve operations impossible for fully sorted structures — O(n) build time, O(1) peek. Every data structure is a set of trade-offs; the heap's trade-off is the most beautifully balanced for priority-driven problems.

The monk's practice: implement each operation from scratch until `sift_up` and `sift_down` feel as natural as breathing. Then every heap-based algorithm becomes transparent.