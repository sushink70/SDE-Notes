# Priority Queue — The Complete Masterclass

> *The heap is the mechanism. The priority queue is the contract. Master the distinction and every algorithm that uses one becomes clear.*

---

## Table of Contents

1. [The Priority Queue ADT — Formal Definition](#1-the-priority-queue-adt--formal-definition)
2. [Implementation Landscape — All Approaches](#2-implementation-landscape--all-approaches)
3. [Binary Heap as Priority Queue — Deep Internals](#3-binary-heap-as-priority-queue--deep-internals)
4. [The Indexed Priority Queue — Decrease-Key Unlocked](#4-the-indexed-priority-queue--decrease-key-unlocked)
5. [Monotonic Priority Queues](#5-monotonic-priority-queues)
6. [Double-Ended Priority Queue](#6-double-ended-priority-queue)
7. [Complexity Landscape Across All Implementations](#7-complexity-landscape-across-all-implementations)
8. [C Implementation — Generic IPQ with Decrease-Key](#8-c-implementation--generic-ipq-with-decrease-key)
9. [Go Implementation — Full PQ Suite](#9-go-implementation--full-pq-suite)
10. [Rust Implementation — Zero-Cost PQ Abstractions](#10-rust-implementation--zero-cost-pq-abstractions)
11. [Algorithmic Applications — Deep Dives](#11-algorithmic-applications--deep-dives)
12. [Problem Patterns & Recognition Map](#12-problem-patterns--recognition-map)

---

## 1. The Priority Queue ADT — Formal Definition

A **Priority Queue** is an **Abstract Data Type** — a mathematical contract independent of any implementation. It models a multiset of elements where each element carries a **priority key**, and the structure always provides efficient access to the element with the **extreme priority** (minimum or maximum).

### Formal Contract

```
ADT PriorityQueue<K, V> where K is totally ordered:

  insert(key: K, value: V) → Handle
      Precondition:  none
      Postcondition: element (key,value) is in the PQ
      Returns:       opaque Handle for future update/delete

  find_min() → (K, V)
      Precondition:  PQ is not empty
      Postcondition: PQ is unchanged
      Returns:       element with minimum key

  extract_min() → (K, V)
      Precondition:  PQ is not empty
      Postcondition: element with minimum key is removed
      Returns:       that element

  decrease_key(h: Handle, new_key: K)
      Precondition:  h is valid, new_key ≤ current key of h
      Postcondition: key of element at h is new_key
      Side effects:  structural reorder as needed

  delete(h: Handle)
      Precondition:  h is valid
      Postcondition: element at h is removed

  merge(other: PQ) → PQ
      Postcondition: returns union of both PQs
```

### The Key Insight: ADT vs Implementation

```
ADT (What):                 Implementation (How):
┌─────────────────┐         ┌───────────────────────────┐
│ PriorityQueue   │ ──────► │ Binary Heap                │
│                 │         │ Fibonacci Heap             │
│ insert          │         │ Sorted Array               │
│ find_min        │         │ Unsorted Array             │
│ extract_min     │         │ Balanced BST               │
│ decrease_key    │         │ Skip List                  │
│ delete          │         │ Pairing Heap               │
└─────────────────┘         └───────────────────────────┘
```

You must always think at the ADT level when designing algorithms, and drop to the implementation level only when analyzing complexity. This **separation of concerns** is what distinguishes expert programmers from beginners.

### Total vs Partial Order

A priority key must satisfy **total order**:
- **Reflexivity:** k ≤ k
- **Antisymmetry:** k₁ ≤ k₂ and k₂ ≤ k₁ → k₁ = k₂
- **Transitivity:** k₁ ≤ k₂ and k₂ ≤ k₃ → k₁ ≤ k₃
- **Totality:** either k₁ ≤ k₂ or k₂ ≤ k₁

**Tie-breaking:** When two elements have equal priority, a PQ makes **no guarantee** about which is returned first unless you augment keys with a secondary comparison (e.g., insertion timestamp for FIFO tie-breaking, making it a **stable priority queue**).

```
Stable PQ key: (priority, insertion_sequence_number)
Compare: first by priority, then by sequence number ascending
This restores FIFO ordering among equal-priority elements.
```

---

## 2. Implementation Landscape — All Approaches

Before committing to binary heap, understand the **full design space**. Different implementations dominate under different operation mixes.

### 2.1 Unsorted Array / List

```
insert:      O(1) amortized  — just append
find_min:    O(n)            — linear scan
extract_min: O(n)            — linear scan + remove
decrease_key:O(1)            — just update value (no reorder needed)
```

**When to use:** Operation mix is overwhelmingly inserts with rare extractions. Real-time streaming where you batch-process occasionally.

### 2.2 Sorted Array

```
insert:      O(n)    — binary search + shift
find_min:    O(1)    — first element
extract_min: O(n)    — shift remaining elements
decrease_key:O(n)    — find + shift
```

**When to use:** Essentially never for dynamic PQ. Only when the set is static and you query min repeatedly.

### 2.3 Sorted Linked List

```
insert:      O(n)    — find insertion point
find_min:    O(1)    — head node
extract_min: O(1)    — remove head
decrease_key:O(n)    — find + relink
```

**When to use:** When you need O(1) extract-min and can afford O(n) inserts. Very specialized.

### 2.4 Binary Heap

```
insert:      O(log n)
find_min:    O(1)
extract_min: O(log n)
decrease_key:O(log n)  [requires indexed heap]
delete:      O(log n)  [requires indexed heap]
build:       O(n)      [Floyd's algorithm]
```

**When to use:** General purpose. The default choice for most problems. Cache-friendly, simple to implement, consistent performance.

### 2.5 Balanced BST (AVL / Red-Black Tree)

```
insert:      O(log n)
find_min:    O(log n)  [leftmost node]
extract_min: O(log n)
decrease_key:O(log n)
delete:      O(log n)
find_max:    O(log n)  [rightmost node]  ← bonus
```

**When to use:** When you need **both** min AND max efficiently (double-ended PQ), or when you need arbitrary element search/delete, or when you need sorted iteration. BST is strictly more powerful than a heap — it maintains total order, not just partial. The cost: higher constant factors and no O(n) build.

### 2.6 Fibonacci Heap

```
insert:      O(1) amortized
find_min:    O(1)
extract_min: O(log n) amortized
decrease_key:O(1) amortized    ← this is the killer feature
delete:      O(log n) amortized
merge:       O(1)
```

**When to use:** Theoretically optimal for decrease-key heavy workloads. Dijkstra on dense graphs: O(E + V log V) vs O((E + V) log V) with binary heap. In practice, constant factors make it competitive only for enormous E/V ratios.

### 2.7 Pairing Heap

Simpler than Fibonacci heap, nearly identical amortized complexity in practice:
```
insert:      O(1) amortized
find_min:    O(1)
extract_min: O(log n) amortized
decrease_key:O(log n) amortized (conjectured O(log log n))
merge:       O(1)
```

**When to use:** When you need Fibonacci-like performance without the implementation complexity. The practical alternative to Fibonacci heap.

### Decision Matrix

```
Need?                                → Use
──────────────────────────────────────────────────────
Simple min/max extraction             Binary Heap
Decrease-key (Dijkstra/Prim)          Indexed Binary Heap
Both min AND max                      Min-Max Heap / BST
Merge two PQs efficiently             Pairing/Leftist Heap
Theoretically optimal (huge graphs)  Fibonacci Heap
Sorted iteration + min/max           Balanced BST
```

---

## 3. Binary Heap as Priority Queue — Deep Internals

### 3.1 The Heap-as-PQ Mental Model

When you use a heap as a priority queue, think of it as maintaining a **dynamic sorted stream**:

```
Stream of insertions:  [8, 3, 1, 5, 9, 2, 7]
At any point in time:  O(1) to know the minimum
                       O(log n) to remove it and find next minimum
                       O(n log n) total to drain all in sorted order
```

The heap never sorts everything — it only guarantees that **the minimum is always at the root**. This lazy-sorting property is what grants O(n) build and O(1) peek.

### 3.2 Priority vs Value Separation

In real PQ usage, you always have two components:

```
Element = (priority_key, payload)

Examples:
  Dijkstra:  key = distance,    payload = node_id
  Prim's:    key = edge_weight, payload = vertex
  A*:        key = f(n)=g+h,    payload = (node, path)
  Task scheduler: key = deadline, payload = task_id
  Event sim:  key = timestamp,   payload = Event struct
```

The heap orders by key. The payload rides along for free.

### 3.3 Lazy Deletion Pattern

When you can't afford an indexed heap but need to delete elements:

```
1. Mark element as "deleted" in a hash set
2. When extract_min returns a marked element, discard and try again
3. Elements are "lazily" removed when they surface to the root

Cost: Extra memory for deleted set, extra pops on extraction
Benefit: No need for position tracking, simpler implementation
```

```go
// Lazy deletion in Go
type LazyPQ struct {
    heap    []Item
    deleted map[int]bool // set of deleted IDs
}

func (pq *LazyPQ) Delete(id int) {
    pq.deleted[id] = true // O(1), element stays in heap
}

func (pq *LazyPQ) ExtractMin() (Item, bool) {
    for len(pq.heap) > 0 {
        item := pq.popRaw()
        if !pq.deleted[item.ID] {
            return item, true // valid element
        }
        // discard stale/deleted element, continue
    }
    return Item{}, false
}
```

**Lazy Dijkstra** uses exactly this pattern — push `(new_dist, node)` without decrease-key, and skip outdated entries at extraction time.

### 3.4 The Stability Problem

Standard heaps are **unstable**. Equal-priority elements may be returned in any order. For deterministic behavior, augment the key:

```c
// Stable PQ key: composite (priority, sequence_number)
typedef struct {
    int   priority;
    long  seq;       // monotonically increasing insertion counter
    void *data;
} StableItem;

// Comparator: first by priority, then by seq (FIFO among equals)
bool stable_less(StableItem a, StableItem b) {
    if (a.priority != b.priority) return a.priority < b.priority;
    return a.seq < b.seq;  // earlier inserted = higher priority
}
```

---

## 4. The Indexed Priority Queue — Decrease-Key Unlocked

The **Indexed Priority Queue (IPQ)** is the most important PQ variant for algorithm implementation. It enables O(log n) decrease-key by maintaining a **bidirectional mapping** between elements and their positions in the heap array.

### 4.1 The Core Problem

In a plain heap:

```
heap array: [1, 5, 3, 8, 9, 4, 7]
            index: 0  1  2  3  4  5  6

Question: Where is node 8 (value=9)?
Answer:   You must linear scan. O(n).

Question: After decrease_key(node=8, newval=0)?
Answer:   You found it at index 4. Sift up. O(log n) sift.
          Total: O(n) find + O(log n) sift = O(n). Useless.
```

### 4.2 The Three-Array Solution

An IPQ maintains three parallel arrays:

```
Element IDs:   0   1   2   3   4   5   6
               ─   ─   ─   ─   ─   ─   ─
keys[]:        ∞   3   ∞   7   1   5   ∞   ← priority key per element ID
               (∞ = not in heap)

heap[]:        4   1   5   3   .   .   .   ← heap position i → element ID
               pos 0   1   2   3

pos[]:         .   1   .   3   0   2   .   ← element ID → heap position
               (. = not in heap)
```

**Invariant:** `heap[pos[i]] == i` and `pos[heap[j]] == j` for all valid i, j.

**The magic:** Given element ID `i`, find its heap position in O(1): `pos[i]`. Then sift up/down in O(log n). Total decrease-key: **O(log n)**.

### 4.3 Every Operation with the Three-Array Model

```
insert(id, key):
  keys[id] = key
  heap[size] = id
  pos[id] = size
  size++
  sift_up(pos[id])

decrease_key(id, new_key):
  keys[id] = new_key
  sift_up(pos[id])     // new key is smaller → move toward root

increase_key(id, new_key):
  keys[id] = new_key
  sift_down(pos[id])   // new key is larger → move toward leaves

extract_min():
  min_id = heap[0]
  swap(heap, 0, size-1)
  size--
  sift_down(0)
  pos[min_id] = -1     // mark as removed
  return (min_id, keys[min_id])

delete(id):
  decrease_key(id, -∞)  // bubble to root
  extract_min()

contains(id):
  return pos[id] >= 0 and pos[id] < size

swap_in_heap(i, j):           ← THE CRITICAL OPERATION
  heap[i], heap[j] = heap[j], heap[i]
  pos[heap[i]] = i            ← update both reverse lookups
  pos[heap[j]] = j            ← MUST update both on every swap
```

**The critical discipline:** Every single swap in the heap array **must** update both `pos` entries. Miss one and the invariant breaks silently — producing wrong answers that are hard to debug.

### 4.4 Why Dijkstra Needs This

```
Standard Dijkstra with lazy heap:
  - Push (dist[v], v) for every relaxation → O(E) pushes
  - Each extract_min: O(log E) → O(E log E) total
  - E can be O(V²) for dense graphs → O(V² log V)

Dijkstra with Indexed Priority Queue:
  - Each node is in heap at most once → O(V) heap size
  - decrease_key instead of new push → O(log V) per relaxation
  - E relaxations × O(log V) = O(E log V)
  - extract_min: V times × O(log V) = O(V log V)
  - Total: O((E + V) log V)

For sparse graphs (E ~ V): identical
For dense graphs (E ~ V²): IPQ wins significantly
```

---

## 5. Monotonic Priority Queues

A **monotonic queue** is a deque maintaining elements in monotonically increasing or decreasing order. It's not a general PQ — it's a specialized structure for the **sliding window extremum** problem.

### 5.1 Monotonic Deque Invariant

```
Monotonic decreasing deque (for window maximum):
  - Front always holds the maximum
  - Elements decrease from front to back
  - When adding element x: pop from back all elements < x
    (they can never be the window max while x is alive)
  - When sliding window: pop from front if front index is out of window
```

### 5.2 Sliding Window Maximum

```
Array:  [1, 3, -1, -3, 5, 3, 6, 7], k=3
Window: [1,3,-1] → 3
        [3,-1,-3] → 3
        [-1,-3,5] → 5
        [-3,5,3] → 5
        [5,3,6] → 6
        [3,6,7] → 7

Naive PQ approach: O(n log k) — heap with lazy deletion
Monotonic deque:   O(n)       — each element pushed/popped once
```

```go
// Sliding window maximum — O(n) monotonic deque
func slidingWindowMax(nums []int, k int) []int {
    deque := make([]int, 0, k) // stores indices, not values
    result := make([]int, 0, len(nums)-k+1)

    for i, val := range nums {
        // Remove indices outside window
        for len(deque) > 0 && deque[0] < i-k+1 {
            deque = deque[1:]
        }
        // Maintain decreasing order: remove smaller elements from back
        for len(deque) > 0 && nums[deque[len(deque)-1]] < val {
            deque = deque[:len(deque)-1]
        }
        deque = append(deque, i)

        // Window is full
        if i >= k-1 {
            result = append(result, nums[deque[0]])
        }
    }
    return result
}
```

---

## 6. Double-Ended Priority Queue

A **DEPQ** (Double-Ended Priority Queue) supports both `find_min` and `find_max` in O(1), and both `extract_min` and `extract_max` in O(log n).

### 6.1 Min-Max Heap

A min-max heap is a complete binary tree where levels alternate between min-levels (even depth) and max-levels (odd depth):

```
Level 0 (min):         8
Level 1 (max):      41    18
Level 2 (min):    28 39  17  10
Level 3 (max):  1 7

Invariant:
- Even-level node: smaller than ALL descendants
- Odd-level node:  larger  than ALL descendants

find_min: O(1) → root (level 0)
find_max: O(1) → max of root's children (level 1), at most 2 comparisons
extract_min: O(log n) → root removal with restructure
extract_max: O(log n) → max-child removal with restructure
```

### 6.2 Two-Heap DEPQ (Simpler Implementation)

Maintain two synchronized heaps:

```
min_heap: stores all elements (min-heap)
max_heap: stores all elements (max-heap, negated)
cross_map: element_id → (min_heap_pos, max_heap_pos)

find_min: O(1)    → min_heap root
find_max: O(1)    → max_heap root
extract_min: remove from min_heap, delete from max_heap via cross_map
extract_max: remove from max_heap, delete from min_heap via cross_map
```

### 6.3 The Two-Heap Median Tracker (Deep Analysis)

The **Running Median** problem is the canonical DEPQ application:

```
Maintain two heaps:
  lower: max-heap  (contains lower half of elements)
  upper: min-heap  (contains upper half of elements)

Invariant:
  1. |lower.size - upper.size| ≤ 1     (size balance)
  2. lower.max ≤ upper.min             (order invariant)

add(x):
  if lower is empty OR x ≤ lower.max:
      lower.push(x)
  else:
      upper.push(x)
  
  rebalance:
    while lower.size > upper.size + 1:
        upper.push(lower.pop())
    while upper.size > lower.size:
        lower.push(upper.pop())

median():
  if lower.size == upper.size:
      return (lower.max + upper.min) / 2.0
  else:
      return lower.max   (lower always has ≥ elements)
```

**Why this works:** The max of `lower` and min of `upper` are the two middle elements. Their relationship gives us the median in O(1).

**Invariant proof of correctness:**
- After every add + rebalance, `lower.size == upper.size` or `lower.size == upper.size + 1`
- Order invariant `lower.max ≤ upper.min` holds because we route elements correctly and both heaps maintain their own ordering

---

## 7. Complexity Landscape Across All Implementations

```
                    │ Insert  │ Find-Min │ Ext-Min │ Dec-Key │ Delete  │ Merge  │
────────────────────┼─────────┼──────────┼─────────┼─────────┼─────────┼────────│
Unsorted Array      │ O(1)*   │ O(n)     │ O(n)    │ O(1)    │ O(1)    │ O(1)   │
Sorted Array        │ O(n)    │ O(1)     │ O(1)    │ O(n)    │ O(n)    │ O(n)   │
Binary Heap         │ O(log n)│ O(1)     │ O(log n)│ O(log n)│ O(log n)│ O(n)   │
d-ary Heap          │ O(log n)│ O(1)     │ O(d log)│ O(log n)│ O(log n)│ O(n)   │
Binomial Heap       │ O(log n)│ O(log n) │ O(log n)│ O(log n)│ O(log n)│ O(log) │
Leftist Heap        │ O(log n)│ O(1)     │ O(log n)│ O(log n)│ O(log n)│ O(log) │
Skew Heap           │ O(log n)│ O(1)     │ O(log n)│ O(log n)│ O(log n)│ O(log) │
Pairing Heap        │ O(1)    │ O(1)     │ O(log n)│ O(log n)│ O(log n)│ O(1)   │
Fibonacci Heap      │ O(1)    │ O(1)     │ O(log n)│ O(1)    │ O(log n)│ O(1)   │
Balanced BST        │ O(log n)│ O(log n) │ O(log n)│ O(log n)│ O(log n)│ O(n)   │

* amortized, † amortized
All amortized unless otherwise specified.
```

**The Fibonacci dominance theorem:** For algorithms where decrease-key is called more than extract-min, Fibonacci heap asymptotically dominates all others. Dijkstra's algorithm on sparse graphs (E >> V): this matters enormously at scale.

---

## 8. C Implementation — Generic IPQ with Decrease-Key

```c
/* ============================================================
 * ipq.h  —  Indexed Priority Queue
 *
 * A min-heap where each element has:
 *   - An integer ID (0..capacity-1) for O(1) lookup
 *   - A comparable key (int here; extend via void* + comparator)
 *
 * Supports: insert, extract_min, decrease_key, increase_key,
 *           delete, contains, peek — all O(log n)
 * ============================================================ */

#ifndef IPQ_H
#define IPQ_H

#include <stdbool.h>
#include <stddef.h>

#define IPQ_NOT_IN_HEAP  (-1)
#define IPQ_KEY_NEG_INF  (INT_MIN)
#define IPQ_KEY_POS_INF  (INT_MAX)

#include <limits.h>

typedef struct {
    int     *heap;      /* heap[i]    = element ID at heap position i  */
    int     *pos;       /* pos[id]    = heap position of element id     */
    int     *keys;      /* keys[id]   = priority key of element id      */
    int      size;      /* current number of elements in heap           */
    int      capacity;  /* max number of unique IDs                     */
} IPQ;

/* Lifecycle */
IPQ  *ipq_create(int capacity);
void  ipq_destroy(IPQ *q);

/* Core operations — all O(log n) */
bool  ipq_insert(IPQ *q, int id, int key);
bool  ipq_extract_min(IPQ *q, int *out_id, int *out_key);
bool  ipq_peek(const IPQ *q, int *out_id, int *out_key);
bool  ipq_decrease_key(IPQ *q, int id, int new_key);
bool  ipq_increase_key(IPQ *q, int id, int new_key);
bool  ipq_update_key(IPQ *q, int id, int new_key); /* auto-direction */
bool  ipq_delete(IPQ *q, int id);
bool  ipq_contains(const IPQ *q, int id);
int   ipq_size(const IPQ *q);
bool  ipq_is_empty(const IPQ *q);
int   ipq_key_of(const IPQ *q, int id);

#endif /* IPQ_H */
```

```c
/* ============================================================
 * ipq.c  —  Indexed Priority Queue implementation
 * ============================================================ */

#include "ipq.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* ── Internal index arithmetic ───────────────────────────────────── */
static inline int pq_parent(int i) { return (i - 1) / 2; }
static inline int pq_left  (int i) { return  2 * i + 1;  }
static inline int pq_right (int i) { return  2 * i + 2;  }

/* ── The critical operation: swap heap positions, update pos[] ───── */
static void ipq_swap(IPQ *q, int i, int j) {
    /* Swap IDs in heap array */
    int tmp    = q->heap[i];
    q->heap[i] = q->heap[j];
    q->heap[j] = tmp;

    /* CRITICAL: update both reverse-lookup entries
     * Failing to update both = silent invariant violation */
    q->pos[q->heap[i]] = i;
    q->pos[q->heap[j]] = j;
}

/* ── Sift operations ─────────────────────────────────────────────── */

/* Move element at heap position i toward root (its key decreased) */
static void ipq_sift_up(IPQ *q, int i) {
    while (i > 0) {
        int p = pq_parent(i);
        if (q->keys[q->heap[i]] < q->keys[q->heap[p]]) {
            ipq_swap(q, i, p);
            i = p;
        } else {
            break;
        }
    }
}

/* Move element at heap position i toward leaves (its key increased) */
static void ipq_sift_down(IPQ *q, int i) {
    for (;;) {
        int best = i;
        int l    = pq_left(i);
        int r    = pq_right(i);

        if (l < q->size && q->keys[q->heap[l]] < q->keys[q->heap[best]])
            best = l;
        if (r < q->size && q->keys[q->heap[r]] < q->keys[q->heap[best]])
            best = r;

        if (best == i) break;
        ipq_swap(q, i, best);
        i = best;
    }
}

/* ── Lifecycle ───────────────────────────────────────────────────── */

IPQ *ipq_create(int capacity) {
    assert(capacity > 0);
    IPQ *q = malloc(sizeof(IPQ));
    if (!q) return NULL;

    q->heap     = malloc(capacity * sizeof(int));
    q->pos      = malloc(capacity * sizeof(int));
    q->keys     = malloc(capacity * sizeof(int));
    q->size     = 0;
    q->capacity = capacity;

    if (!q->heap || !q->pos || !q->keys) {
        ipq_destroy(q);
        return NULL;
    }

    /* Initialize pos[] to sentinel: not in heap */
    for (int i = 0; i < capacity; i++) {
        q->pos[i]  = IPQ_NOT_IN_HEAP;
        q->keys[i] = IPQ_KEY_POS_INF;
    }
    return q;
}

void ipq_destroy(IPQ *q) {
    if (!q) return;
    free(q->heap);
    free(q->pos);
    free(q->keys);
    free(q);
}

/* ── Core operations ─────────────────────────────────────────────── */

bool ipq_contains(const IPQ *q, int id) {
    return id >= 0 && id < q->capacity &&
           q->pos[id] != IPQ_NOT_IN_HEAP;
}

int ipq_size(const IPQ *q)    { return q->size;       }
bool ipq_is_empty(const IPQ *q){ return q->size == 0; }

int ipq_key_of(const IPQ *q, int id) {
    assert(ipq_contains(q, id));
    return q->keys[id];
}

bool ipq_insert(IPQ *q, int id, int key) {
    if (id < 0 || id >= q->capacity) return false;
    if (ipq_contains(q, id))         return false; /* already present */
    if (q->size >= q->capacity)      return false; /* full */

    q->keys[id]      = key;
    q->heap[q->size] = id;
    q->pos[id]       = q->size;
    q->size++;

    ipq_sift_up(q, q->pos[id]);
    return true;
}

bool ipq_peek(const IPQ *q, int *out_id, int *out_key) {
    if (q->size == 0) return false;
    if (out_id)  *out_id  = q->heap[0];
    if (out_key) *out_key = q->keys[q->heap[0]];
    return true;
}

bool ipq_extract_min(IPQ *q, int *out_id, int *out_key) {
    if (q->size == 0) return false;

    int min_id  = q->heap[0];
    int min_key = q->keys[min_id];

    /* Move last element to root position */
    ipq_swap(q, 0, q->size - 1);
    q->size--;

    /* Mark extracted element as removed */
    q->pos[min_id] = IPQ_NOT_IN_HEAP;

    /* Restore heap property */
    if (q->size > 0) {
        ipq_sift_down(q, 0);
    }

    if (out_id)  *out_id  = min_id;
    if (out_key) *out_key = min_key;
    return true;
}

bool ipq_decrease_key(IPQ *q, int id, int new_key) {
    if (!ipq_contains(q, id))  return false;
    if (new_key > q->keys[id]) return false; /* use increase_key instead */

    q->keys[id] = new_key;
    ipq_sift_up(q, q->pos[id]); /* smaller key → float toward root */
    return true;
}

bool ipq_increase_key(IPQ *q, int id, int new_key) {
    if (!ipq_contains(q, id))  return false;
    if (new_key < q->keys[id]) return false; /* use decrease_key instead */

    q->keys[id] = new_key;
    ipq_sift_down(q, q->pos[id]); /* larger key → sink toward leaves */
    return true;
}

bool ipq_update_key(IPQ *q, int id, int new_key) {
    if (!ipq_contains(q, id)) return false;

    int old_key = q->keys[id];
    q->keys[id] = new_key;

    if (new_key < old_key) {
        ipq_sift_up(q, q->pos[id]);
    } else if (new_key > old_key) {
        ipq_sift_down(q, q->pos[id]);
    }
    /* equal: no-op */
    return true;
}

bool ipq_delete(IPQ *q, int id) {
    if (!ipq_contains(q, id)) return false;

    /* Decrease key to -∞ so element bubbles to root */
    q->keys[id] = IPQ_KEY_NEG_INF;
    ipq_sift_up(q, q->pos[id]);

    /* Now at root: extract it */
    return ipq_extract_min(q, NULL, NULL);
}

/* ── Dijkstra's Algorithm using IPQ ─────────────────────────────── */

#include <stdio.h>

#define INF IPQ_KEY_POS_INF

/* Adjacency list edge */
typedef struct Edge { int to, weight, next; } Edge;

/* Graph with adjacency list */
typedef struct {
    Edge *edges;
    int  *head;   /* head[v] = index of first edge from v */
    int   edge_count;
    int   V;
} Graph;

/* Shortest paths from src to all vertices.
 * dist[] must be pre-allocated with size V.
 * Returns false if V exceeds IPQ capacity.
 */
bool dijkstra(const Graph *g, int src, int *dist) {
    IPQ *pq = ipq_create(g->V);
    if (!pq) return false;

    /* Initialize distances */
    for (int v = 0; v < g->V; v++) {
        dist[v] = (v == src) ? 0 : INF;
    }

    /* Insert all vertices: source with dist 0, rest with INF */
    for (int v = 0; v < g->V; v++) {
        ipq_insert(pq, v, dist[v]);
    }

    while (!ipq_is_empty(pq)) {
        int u, d_u;
        ipq_extract_min(pq, &u, &d_u);

        if (d_u == INF) break; /* remaining vertices unreachable */

        /* Relax all neighbors of u */
        for (int e = g->head[u]; e != -1; e = g->edges[e].next) {
            int v      = g->edges[e].to;
            int new_d  = d_u + g->edges[e].weight;

            if (new_d < dist[v] && ipq_contains(pq, v)) {
                dist[v] = new_d;
                ipq_decrease_key(pq, v, new_d); /* O(log V) */
            }
        }
    }

    ipq_destroy(pq);
    return true;
}

/* ── Verification: check heap invariant ─────────────────────────── */

bool ipq_verify(const IPQ *q) {
    for (int i = 1; i < q->size; i++) {
        int p = pq_parent(i);
        if (q->keys[q->heap[p]] > q->keys[q->heap[i]]) {
            fprintf(stderr, "Heap violation at pos %d (parent) vs %d\n", p, i);
            return false;
        }
        if (q->pos[q->heap[i]] != i) {
            fprintf(stderr, "pos[] inconsistency at heap pos %d\n", i);
            return false;
        }
    }
    return true;
}

/* ── Demo ────────────────────────────────────────────────────────── */

int main(void) {
    printf("=== Indexed Priority Queue Demo ===\n\n");

    IPQ *pq = ipq_create(10);

    /* Insert elements with IDs 0..6 */
    int initial_keys[] = {15, 8, 23, 4, 42, 16, 7};
    for (int i = 0; i < 7; i++) {
        ipq_insert(pq, i, initial_keys[i]);
        printf("insert(id=%d, key=%d)\n", i, initial_keys[i]);
    }

    printf("\nHeap valid: %s\n", ipq_verify(pq) ? "YES" : "NO");

    /* Decrease key of ID 5 from 16 to 2 */
    printf("\ndecrease_key(id=5, 2)  [was 16]\n");
    ipq_decrease_key(pq, 5, 2);
    printf("Heap valid: %s\n", ipq_verify(pq) ? "YES" : "NO");

    /* Increase key of ID 3 from 4 to 100 */
    printf("\nincrease_key(id=3, 100) [was 4]\n");
    ipq_increase_key(pq, 3, 100);

    /* Delete ID 6 */
    printf("delete(id=6) [key was 7]\n");
    ipq_delete(pq, 6);

    /* Drain in priority order */
    printf("\nExtract all in priority order:\n");
    int id, key;
    while (ipq_extract_min(pq, &id, &key)) {
        printf("  id=%d  key=%d\n", id, key);
    }

    ipq_destroy(pq);
    return 0;
}
```

---

## 9. Go Implementation — Full PQ Suite

```go
// package pq — Complete Priority Queue suite in Go
//
// Provides:
//   1. GenericPQ      — comparator-based heap, any type
//   2. IndexedPQ      — O(log n) decrease-key with handles
//   3. LazyPQ         — lazy deletion for simpler code paths
//   4. MedianTracker  — O(log n) add, O(1) median
//   5. dijkstra       — Dijkstra using IndexedPQ
//
// All using Go generics (1.21+)

package pq

import (
	"cmp"
	"fmt"
	"math"
)

// ─── 1. Generic Priority Queue ────────────────────────────────────────────────

// PQ is a generic binary heap parameterized by key type K and value type V.
// Less(a, b) → true means 'a' has higher priority (closer to root) than 'b'.
type PQ[K any, V any] struct {
	data []entry[K, V]
	less func(a, b K) bool
}

type entry[K any, V any] struct {
	key K
	val V
}

// NewPQ creates a PQ with a custom less function.
func NewPQ[K any, V any](less func(a, b K) bool) *PQ[K, V] {
	return &PQ[K, V]{less: less}
}

// NewMinPQ creates a min-heap for any cmp.Ordered key type.
func NewMinPQ[K cmp.Ordered, V any]() *PQ[K, V] {
	return NewPQ[K, V](func(a, b K) bool { return a < b })
}

// NewMaxPQ creates a max-heap for any cmp.Ordered key type.
func NewMaxPQ[K cmp.Ordered, V any]() *PQ[K, V] {
	return NewPQ[K, V](func(a, b K) bool { return a > b })
}

func (pq *PQ[K, V]) Len() int        { return len(pq.data) }
func (pq *PQ[K, V]) IsEmpty() bool   { return len(pq.data) == 0 }

// Push inserts (key, value). O(log n).
func (pq *PQ[K, V]) Push(key K, val V) {
	pq.data = append(pq.data, entry[K, V]{key, val})
	pq.siftUp(len(pq.data) - 1)
}

// Pop removes and returns the highest-priority entry. O(log n).
func (pq *PQ[K, V]) Pop() (K, V, bool) {
	if pq.IsEmpty() {
		var zk K
		var zv V
		return zk, zv, false
	}
	root := pq.data[0]
	last := len(pq.data) - 1
	pq.data[0] = pq.data[last]
	pq.data = pq.data[:last]
	if !pq.IsEmpty() {
		pq.siftDown(0)
	}
	return root.key, root.val, true
}

// Peek returns the root without removing it. O(1).
func (pq *PQ[K, V]) Peek() (K, V, bool) {
	if pq.IsEmpty() {
		var zk K
		var zv V
		return zk, zv, false
	}
	return pq.data[0].key, pq.data[0].val, true
}

// Build constructs heap in O(n) from a slice of (key, val) pairs.
func (pq *PQ[K, V]) Build(keys []K, vals []V) {
	n := len(keys)
	pq.data = make([]entry[K, V], n)
	for i := range n {
		pq.data[i] = entry[K, V]{keys[i], vals[i]}
	}
	for i := n/2 - 1; i >= 0; i-- {
		pq.siftDown(i)
	}
}

func (pq *PQ[K, V]) siftUp(i int) {
	for i > 0 {
		p := (i - 1) / 2
		if pq.less(pq.data[i].key, pq.data[p].key) {
			pq.data[i], pq.data[p] = pq.data[p], pq.data[i]
			i = p
		} else {
			break
		}
	}
}

func (pq *PQ[K, V]) siftDown(i int) {
	n := len(pq.data)
	for {
		best := i
		l, r := 2*i+1, 2*i+2
		if l < n && pq.less(pq.data[l].key, pq.data[best].key) {
			best = l
		}
		if r < n && pq.less(pq.data[r].key, pq.data[best].key) {
			best = r
		}
		if best == i {
			break
		}
		pq.data[i], pq.data[best] = pq.data[best], pq.data[i]
		i = best
	}
}

// ─── 2. Indexed Priority Queue ────────────────────────────────────────────────

// IndexedPQ supports O(log n) decrease_key, increase_key, delete, contains.
// Element IDs are integers in [0, capacity).
// Key type K must be ordered; use a custom less for other types.
type IndexedPQ[K cmp.Ordered] struct {
	heap []int            // heap[i]   = element ID at position i
	pos  []int            // pos[id]   = heap position of id (-1 if absent)
	keys []K              // keys[id]  = priority key of id
	size int
	cap  int
	less func(a, b K) bool
}

const notInHeap = -1

// NewIndexedPQ creates an indexed min-PQ for IDs in [0, capacity).
func NewIndexedPQ[K cmp.Ordered](capacity int) *IndexedPQ[K] {
	q := &IndexedPQ[K]{
		heap: make([]int, capacity),
		pos:  make([]int, capacity),
		keys: make([]K, capacity),
		cap:  capacity,
		less: func(a, b K) bool { return a < b },
	}
	for i := range capacity {
		q.pos[i] = notInHeap
	}
	return q
}

// NewIndexedPQCustom creates an indexed PQ with a custom comparator.
func NewIndexedPQCustom[K cmp.Ordered](capacity int, less func(K, K) bool) *IndexedPQ[K] {
	q := NewIndexedPQ[K](capacity)
	q.less = less
	return q
}

func (q *IndexedPQ[K]) Len() int      { return q.size }
func (q *IndexedPQ[K]) IsEmpty() bool { return q.size == 0 }

// Contains returns true if element with given ID is in the PQ. O(1).
func (q *IndexedPQ[K]) Contains(id int) bool {
	return id >= 0 && id < q.cap && q.pos[id] != notInHeap
}

// KeyOf returns the current key of element with given ID. O(1).
func (q *IndexedPQ[K]) KeyOf(id int) (K, bool) {
	if !q.Contains(id) {
		var zero K
		return zero, false
	}
	return q.keys[id], true
}

// Insert adds element with given ID and key. O(log n).
// Returns false if ID is out of range or already present.
func (q *IndexedPQ[K]) Insert(id int, key K) bool {
	if id < 0 || id >= q.cap || q.Contains(id) || q.size >= q.cap {
		return false
	}
	q.keys[id] = key
	q.heap[q.size] = id
	q.pos[id] = q.size
	q.size++
	q.siftUp(q.pos[id])
	return true
}

// Peek returns (id, key) of root without removing it. O(1).
func (q *IndexedPQ[K]) Peek() (int, K, bool) {
	if q.IsEmpty() {
		var zero K
		return -1, zero, false
	}
	id := q.heap[0]
	return id, q.keys[id], true
}

// ExtractMin removes and returns the minimum-key element. O(log n).
func (q *IndexedPQ[K]) ExtractMin() (int, K, bool) {
	if q.IsEmpty() {
		var zero K
		return -1, zero, false
	}
	minID  := q.heap[0]
	minKey := q.keys[minID]

	q.swap(0, q.size-1)
	q.size--
	q.pos[minID] = notInHeap

	if q.size > 0 {
		q.siftDown(0)
	}
	return minID, minKey, true
}

// DecreaseKey reduces the key of element id. O(log n).
func (q *IndexedPQ[K]) DecreaseKey(id int, newKey K) bool {
	if !q.Contains(id) {
		return false
	}
	if !q.less(newKey, q.keys[id]) {
		return false // new key is not smaller
	}
	q.keys[id] = newKey
	q.siftUp(q.pos[id])
	return true
}

// IncreaseKey raises the key of element id. O(log n).
func (q *IndexedPQ[K]) IncreaseKey(id int, newKey K) bool {
	if !q.Contains(id) {
		return false
	}
	if q.less(newKey, q.keys[id]) {
		return false // new key is not larger
	}
	q.keys[id] = newKey
	q.siftDown(q.pos[id])
	return true
}

// UpdateKey sets the key of element id to newKey, sifting in correct direction.
func (q *IndexedPQ[K]) UpdateKey(id int, newKey K) bool {
	if !q.Contains(id) {
		return false
	}
	old := q.keys[id]
	q.keys[id] = newKey
	switch {
	case q.less(newKey, old):
		q.siftUp(q.pos[id])
	case q.less(old, newKey):
		q.siftDown(q.pos[id])
	}
	return true
}

// Delete removes element with given ID. O(log n).
func (q *IndexedPQ[K]) Delete(id int) bool {
	if !q.Contains(id) {
		return false
	}
	// Move to root by sifting up forcibly via position swap trick:
	// Instead of setting -∞, directly swap with root and sift down
	heapPos := q.pos[id]
	q.swap(heapPos, q.size-1)
	q.size--
	q.pos[id] = notInHeap

	if heapPos < q.size {
		// The element moved to heapPos might need to go up or down
		q.siftUp(heapPos)
		q.siftDown(q.pos[q.heap[heapPos]]) // pos may have changed after siftUp
	}
	return true
}

// ─── The invariant-preserving swap ────────────────────────────────
func (q *IndexedPQ[K]) swap(i, j int) {
	q.heap[i], q.heap[j] = q.heap[j], q.heap[i]
	q.pos[q.heap[i]] = i
	q.pos[q.heap[j]] = j
}

func (q *IndexedPQ[K]) siftUp(i int) {
	for i > 0 {
		p := (i - 1) / 2
		if q.less(q.keys[q.heap[i]], q.keys[q.heap[p]]) {
			q.swap(i, p)
			i = p
		} else {
			break
		}
	}
}

func (q *IndexedPQ[K]) siftDown(i int) {
	for {
		best := i
		l, r := 2*i+1, 2*i+2
		if l < q.size && q.less(q.keys[q.heap[l]], q.keys[q.heap[best]]) {
			best = l
		}
		if r < q.size && q.less(q.keys[q.heap[r]], q.keys[q.heap[best]]) {
			best = r
		}
		if best == i {
			break
		}
		q.swap(i, best)
		i = best
	}
}

// Verify checks the heap invariant. Use in tests/debug. O(n).
func (q *IndexedPQ[K]) Verify() bool {
	for i := 1; i < q.size; i++ {
		p := (i - 1) / 2
		if q.less(q.keys[q.heap[i]], q.keys[q.heap[p]]) {
			return false
		}
		if q.pos[q.heap[i]] != i {
			return false
		}
	}
	return true
}

// ─── 3. Lazy Deletion PQ ─────────────────────────────────────────────────────

// LazyPQ wraps a standard heap with tombstone-based lazy deletion.
// Trade-off: simpler code, extra memory/time per extraction.
// Best for: Dijkstra where stale entries are common.
type LazyPQ[K cmp.Ordered, V comparable] struct {
	inner   *PQ[K, V]
	deleted map[V]bool
}

func NewLazyPQ[K cmp.Ordered, V comparable]() *LazyPQ[K, V] {
	return &LazyPQ[K, V]{
		inner:   NewMinPQ[K, V](),
		deleted: make(map[V]bool),
	}
}

func (q *LazyPQ[K, V]) Push(key K, val V)    { q.inner.Push(key, val) }
func (q *LazyPQ[K, V]) Delete(val V)         { q.deleted[val] = true  }

// Pop skips tombstoned entries. O(log n) amortized.
func (q *LazyPQ[K, V]) Pop() (K, V, bool) {
	for {
		k, v, ok := q.inner.Pop()
		if !ok {
			return k, v, false
		}
		if !q.deleted[v] {
			return k, v, true
		}
		delete(q.deleted, v) // clean up tombstone
	}
}

// ─── 4. Median Tracker ───────────────────────────────────────────────────────

// MedianTracker maintains the running median using two heaps.
// Add: O(log n). Median: O(1).
type MedianTracker struct {
	lower *PQ[float64, struct{}] // max-heap: lower half
	upper *PQ[float64, struct{}] // min-heap: upper half
}

func NewMedianTracker() *MedianTracker {
	return &MedianTracker{
		lower: NewMaxPQ[float64, struct{}](),
		upper: NewMinPQ[float64, struct{}](),
	}
}

func (m *MedianTracker) Add(val float64) {
	// Route to correct half
	if lk, _, ok := m.lower.Peek(); !ok || val <= lk {
		m.lower.Push(val, struct{}{})
	} else {
		m.upper.Push(val, struct{}{})
	}

	// Rebalance: lower may have at most 1 more element than upper
	for m.lower.Len() > m.upper.Len()+1 {
		k, _, _ := m.lower.Pop()
		m.upper.Push(k, struct{}{})
	}
	for m.upper.Len() > m.lower.Len() {
		k, _, _ := m.upper.Pop()
		m.lower.Push(k, struct{}{})
	}
}

func (m *MedianTracker) Median() (float64, bool) {
	if m.lower.Len() == 0 {
		return 0, false
	}
	lo, _, _ := m.lower.Peek()
	if m.lower.Len() == m.upper.Len() {
		hi, _, _ := m.upper.Peek()
		return (lo + hi) / 2.0, true
	}
	return lo, true
}

// ─── 5. Dijkstra with IndexedPQ ──────────────────────────────────────────────

// Edge represents a directed weighted edge.
type Edge struct{ To, Weight int }

// Dijkstra computes shortest paths from src using IndexedPQ.
// Returns dist[] where dist[v] = shortest distance from src to v.
// O((E + V) log V)
func Dijkstra(graph [][]Edge, src int) []int {
	V := len(graph)
	dist := make([]int, V)
	for i := range dist {
		dist[i] = math.MaxInt
	}
	dist[src] = 0

	pq := NewIndexedPQ[int](V)
	for v := range V {
		pq.Insert(v, dist[v])
	}

	for !pq.IsEmpty() {
		u, dU, _ := pq.ExtractMin()

		if dU == math.MaxInt {
			break // all remaining vertices unreachable
		}

		for _, e := range graph[u] {
			newDist := dU + e.Weight
			if newDist < dist[e.To] && pq.Contains(e.To) {
				dist[e.To] = newDist
				pq.DecreaseKey(e.To, newDist) // O(log V) — the key operation
			}
		}
	}
	return dist
}

// ─── 6. K-way Merge using PQ ─────────────────────────────────────────────────

// KWayMerge merges k sorted slices into one sorted slice.
// O(n log k) where n = total elements.
func KWayMerge(lists [][]int) []int {
	type cursor struct {
		listIdx, elemIdx int
	}

	pq := NewPQ[int, cursor](func(a, b int) bool { return a < b })

	// Initialize: push first element of each list
	for i, list := range lists {
		if len(list) > 0 {
			pq.Push(list[0], cursor{i, 0})
		}
	}

	result := make([]int, 0)
	for !pq.IsEmpty() {
		val, cur, _ := pq.Pop()
		result = append(result, val)

		// Advance cursor in the same list
		next := cur.elemIdx + 1
		if next < len(lists[cur.listIdx]) {
			pq.Push(lists[cur.listIdx][next], cursor{cur.listIdx, next})
		}
	}
	return result
}

// ─── 7. Top-K Elements ───────────────────────────────────────────────────────

// TopK returns the k largest elements from nums.
// Uses a min-heap of size k. O(n log k).
func TopK(nums []int, k int) []int {
	if k <= 0 || len(nums) == 0 {
		return nil
	}
	pq := NewMinPQ[int, struct{}]()

	for _, n := range nums {
		pq.Push(n, struct{}{})
		if pq.Len() > k {
			pq.Pop() // evict the smallest among current k+1
		}
	}

	result := make([]int, 0, k)
	for !pq.IsEmpty() {
		v, _, _ := pq.Pop()
		result = append(result, v)
	}
	return result // sorted ascending; reverse for descending
}

// ─── Demo ─────────────────────────────────────────────────────────────────────

func Demo() {
	fmt.Println("════════════════════════════════")
	fmt.Println(" Generic PQ Demo")
	fmt.Println("════════════════════════════════")

	pq := NewMinPQ[int, string]()
	pq.Push(5, "task-E")
	pq.Push(1, "task-A")
	pq.Push(3, "task-C")
	pq.Push(2, "task-B")
	pq.Push(4, "task-D")

	fmt.Println("Processing tasks by priority:")
	for !pq.IsEmpty() {
		pri, task, _ := pq.Pop()
		fmt.Printf("  priority=%d  %s\n", pri, task)
	}

	fmt.Println("\n════════════════════════════════")
	fmt.Println(" Indexed PQ — Decrease-Key")
	fmt.Println("════════════════════════════════")

	ipq := NewIndexedPQ[int](6)
	initial := []int{10, 30, 20, 5, 40, 15}
	for i, k := range initial {
		ipq.Insert(i, k)
		fmt.Printf("insert(id=%d, key=%d)\n", i, k)
	}

	fmt.Printf("\nMin: ")
	id, key, _ := ipq.Peek()
	fmt.Printf("id=%d key=%d\n", id, key)

	ipq.DecreaseKey(2, 1) // 20 → 1
	fmt.Printf("After decrease_key(id=2, 1): min=")
	id, key, _ = ipq.Peek()
	fmt.Printf("id=%d key=%d\n", id, key)

	fmt.Printf("Heap valid: %v\n", ipq.Verify())

	fmt.Println("\n════════════════════════════════")
	fmt.Println(" Dijkstra Shortest Path")
	fmt.Println("════════════════════════════════")

	// Graph: 5 nodes, directed weighted edges
	graph := [][]Edge{
		{{1, 4}, {2, 1}},           // 0 → 1(w4), 0 → 2(w1)
		{{3, 1}},                   // 1 → 3(w1)
		{{1, 2}, {3, 5}},           // 2 → 1(w2), 2 → 3(w5)
		{{4, 3}},                   // 3 → 4(w3)
		{},                         // 4 (sink)
	}
	dist := Dijkstra(graph, 0)
	fmt.Printf("Shortest distances from node 0: %v\n", dist)

	fmt.Println("\n════════════════════════════════")
	fmt.Println(" K-Way Merge")
	fmt.Println("════════════════════════════════")

	lists := [][]int{
		{1, 4, 7, 10},
		{2, 5, 8, 11},
		{3, 6, 9, 12},
	}
	merged := KWayMerge(lists)
	fmt.Println("Merged:", merged)

	fmt.Println("\n════════════════════════════════")
	fmt.Println(" Median Tracker")
	fmt.Println("════════════════════════════════")

	mt := NewMedianTracker()
	for _, v := range []float64{5, 15, 1, 3, 2, 8, 7, 9, 10, 6, 11, 4} {
		mt.Add(v)
		med, _ := mt.Median()
		fmt.Printf("add(%.0f) → median=%.1f\n", v, med)
	}

	fmt.Println("\n════════════════════════════════")
	fmt.Println(" Top-3 from stream")
	fmt.Println("════════════════════════════════")

	nums := []int{3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5}
	fmt.Printf("nums:  %v\nTop-3: %v\n", nums, TopK(nums, 3))
}
```

---

## 10. Rust Implementation — Zero-Cost PQ Abstractions

```rust
//! pq.rs — Complete Priority Queue suite in Rust
//!
//! 1. PriorityQueue<K, V>   — generic comparator-based heap
//! 2. IndexedPQ<K>          — O(log n) decrease-key, delete, contains
//! 3. LazyPQ<K, V>          — lazy deletion (Dijkstra-friendly)
//! 4. MedianTracker         — O(log n) add, O(1) median
//! 5. dijkstra()            — O((E+V) log V) using IndexedPQ
//! 6. k_way_merge()         — O(n log k)
//! 7. top_k()               — O(n log k)

use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet};

// ─── 1. Generic Priority Queue ────────────────────────────────────────────────

/// Generic binary heap. `cmp(a, b) = Less` means `a` has higher priority.
pub struct PriorityQueue<K, V> {
    data: Vec<(K, V)>,
    cmp:  fn(&K, &K) -> Ordering,
}

impl<K, V> PriorityQueue<K, V> {
    pub fn new(cmp: fn(&K, &K) -> Ordering) -> Self {
        Self { data: Vec::new(), cmp }
    }

    /// Min-heap: element with smallest K has highest priority.
    pub fn min_heap() -> Self
    where K: Ord
    {
        Self::new(|a, b| a.cmp(b))
    }

    /// Max-heap: element with largest K has highest priority.
    pub fn max_heap() -> Self
    where K: Ord
    {
        Self::new(|a, b| b.cmp(a))
    }

    pub fn len(&self)     -> usize { self.data.len()     }
    pub fn is_empty(&self) -> bool { self.data.is_empty() }

    /// Insert (key, value). O(log n).
    pub fn push(&mut self, key: K, val: V) {
        self.data.push((key, val));
        self.sift_up(self.data.len() - 1);
    }

    /// Remove and return highest-priority entry. O(log n).
    pub fn pop(&mut self) -> Option<(K, V)> {
        if self.data.is_empty() { return None; }
        let last = self.data.len() - 1;
        self.data.swap(0, last);
        let root = self.data.pop();
        if !self.data.is_empty() { self.sift_down(0); }
        root
    }

    /// Peek at root without removing. O(1).
    pub fn peek(&self) -> Option<(&K, &V)> {
        self.data.first().map(|(k, v)| (k, v))
    }

    /// Build from iterator using Floyd's O(n) algorithm.
    pub fn build<I: IntoIterator<Item = (K, V)>>(iter: I, cmp: fn(&K, &K) -> Ordering) -> Self {
        let mut pq = Self { data: iter.into_iter().collect(), cmp };
        let n = pq.data.len();
        if n > 1 {
            for i in (0..n / 2).rev() {
                pq.sift_down(i);
            }
        }
        pq
    }

    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = (i - 1) / 2;
            if (self.cmp)(&self.data[i].0, &self.data[p].0) == Ordering::Less {
                self.data.swap(i, p);
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
            if l < n && (self.cmp)(&self.data[l].0, &self.data[best].0) == Ordering::Less {
                best = l;
            }
            if r < n && (self.cmp)(&self.data[r].0, &self.data[best].0) == Ordering::Less {
                best = r;
            }
            if best == i { break; }
            self.data.swap(i, best);
            i = best;
        }
    }
}

// ─── 2. Indexed Priority Queue ────────────────────────────────────────────────

/// Indexed min-PQ for element IDs in `[0, capacity)`.
/// Supports O(log n): insert, extract_min, decrease_key, increase_key,
///                    delete, contains, key_of.
pub struct IndexedPQ<K: Clone + PartialOrd> {
    heap: Vec<usize>,         // heap[i]  = element ID at position i
    pos:  Vec<Option<usize>>, // pos[id]  = heap position of id
    keys: Vec<Option<K>>,     // keys[id] = current key of id
    size: usize,
    less: fn(&K, &K) -> bool,
}

impl<K: Clone + PartialOrd> IndexedPQ<K> {
    /// Creates a min-PQ. IDs must be in `[0, capacity)`.
    pub fn new(capacity: usize, less: fn(&K, &K) -> bool) -> Self {
        Self {
            heap: vec![0; capacity],
            pos:  vec![None; capacity],
            keys: vec![None; capacity],
            size: 0,
            less,
        }
    }

    pub fn len(&self)      -> usize { self.size         }
    pub fn is_empty(&self) -> bool  { self.size == 0    }

    /// Check if element with `id` is in the PQ. O(1).
    pub fn contains(&self, id: usize) -> bool {
        id < self.pos.len() && self.pos[id].is_some()
    }

    /// Return the current key of element `id`. O(1).
    pub fn key_of(&self, id: usize) -> Option<&K> {
        self.keys.get(id)?.as_ref()
    }

    /// Insert element `id` with `key`. O(log n).
    pub fn insert(&mut self, id: usize, key: K) -> bool {
        if id >= self.pos.len() || self.contains(id) || self.size >= self.pos.len() {
            return false;
        }
        self.keys[id] = Some(key);
        self.heap[self.size] = id;
        self.pos[id] = Some(self.size);
        self.size += 1;
        let idx = self.pos[id].unwrap();
        self.sift_up(idx);
        true
    }

    /// Peek at the minimum (id, key) without removing. O(1).
    pub fn peek(&self) -> Option<(usize, &K)> {
        if self.is_empty() { return None; }
        let id = self.heap[0];
        Some((id, self.keys[id].as_ref().unwrap()))
    }

    /// Remove and return the minimum-key element. O(log n).
    pub fn extract_min(&mut self) -> Option<(usize, K)> {
        if self.is_empty() { return None; }

        let min_id  = self.heap[0];
        let min_key = self.keys[min_id].take().unwrap();

        self.swap(0, self.size - 1);
        self.size -= 1;
        self.pos[min_id] = None;

        if self.size > 0 {
            self.sift_down(0);
        }
        Some((min_id, min_key))
    }

    /// Decrease key of element `id`. O(log n).
    /// Returns false if id absent or new_key is not smaller.
    pub fn decrease_key(&mut self, id: usize, new_key: K) -> bool {
        if !self.contains(id) { return false; }
        if !(self.less)(&new_key, self.keys[id].as_ref().unwrap()) {
            return false;
        }
        self.keys[id] = Some(new_key);
        let idx = self.pos[id].unwrap();
        self.sift_up(idx);
        true
    }

    /// Increase key of element `id`. O(log n).
    pub fn increase_key(&mut self, id: usize, new_key: K) -> bool {
        if !self.contains(id) { return false; }
        if (self.less)(&new_key, self.keys[id].as_ref().unwrap()) {
            return false;
        }
        self.keys[id] = Some(new_key);
        let idx = self.pos[id].unwrap();
        self.sift_down(idx);
        true
    }

    /// Update key in correct direction automatically. O(log n).
    pub fn update_key(&mut self, id: usize, new_key: K) -> bool {
        if !self.contains(id) { return false; }
        let old = self.keys[id].as_ref().unwrap();
        let go_up   = (self.less)(&new_key, old);
        let go_down = (self.less)(old, &new_key);
        self.keys[id] = Some(new_key);
        let idx = self.pos[id].unwrap();
        if go_up   { self.sift_up(idx);   }
        if go_down { self.sift_down(idx); }
        true
    }

    /// Delete element `id` from PQ. O(log n).
    pub fn delete(&mut self, id: usize) -> bool {
        if !self.contains(id) { return false; }
        let heap_pos = self.pos[id].unwrap();

        self.swap(heap_pos, self.size - 1);
        self.size -= 1;
        self.pos[id] = None;
        self.keys[id] = None;

        if heap_pos < self.size {
            // The displaced element may need to move either direction
            self.sift_up(heap_pos);
            // Get current position after potential sift_up
            let displaced_id = self.heap[heap_pos];
            if let Some(cur_pos) = self.pos[displaced_id] {
                self.sift_down(cur_pos);
            }
        }
        true
    }

    /// Verify heap invariant. Use in tests. O(n).
    pub fn verify(&self) -> bool {
        for i in 1..self.size {
            let p = (i - 1) / 2;
            let ki = self.keys[self.heap[i]].as_ref().unwrap();
            let kp = self.keys[self.heap[p]].as_ref().unwrap();
            if (self.less)(ki, kp) { return false; }
            if self.pos[self.heap[i]] != Some(i) { return false; }
        }
        true
    }

    fn swap(&mut self, i: usize, j: usize) {
        self.heap.swap(i, j);
        // CRITICAL: update both reverse-lookup entries
        let id_i = self.heap[i];
        let id_j = self.heap[j];
        self.pos[id_i] = Some(i);
        self.pos[id_j] = Some(j);
    }

    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p  = (i - 1) / 2;
            let ki = self.keys[self.heap[i]].as_ref().unwrap();
            let kp = self.keys[self.heap[p]].as_ref().unwrap();
            if (self.less)(ki, kp) {
                self.swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }

    fn sift_down(&mut self, mut i: usize) {
        loop {
            let mut best = i;
            let l = 2 * i + 1;
            let r = 2 * i + 2;
            if l < self.size {
                let kl = self.keys[self.heap[l]].as_ref().unwrap();
                let kb = self.keys[self.heap[best]].as_ref().unwrap();
                if (self.less)(kl, kb) { best = l; }
            }
            if r < self.size {
                let kr = self.keys[self.heap[r]].as_ref().unwrap();
                let kb = self.keys[self.heap[best]].as_ref().unwrap();
                if (self.less)(kr, kb) { best = r; }
            }
            if best == i { break; }
            self.swap(i, best);
            i = best;
        }
    }
}

// ─── 3. Lazy Deletion PQ ─────────────────────────────────────────────────────

/// Wraps Rust's std BinaryHeap with lazy deletion.
/// V must be Eq + Hash for the tombstone set.
pub struct LazyPQ<K: Ord, V: Eq + std::hash::Hash + Clone> {
    heap:    BinaryHeap<(K, V)>,
    deleted: HashSet<V>,
}

impl<K: Ord, V: Eq + std::hash::Hash + Clone> LazyPQ<K, V> {
    pub fn new() -> Self {
        Self { heap: BinaryHeap::new(), deleted: HashSet::new() }
    }

    pub fn push(&mut self, key: K, val: V) {
        self.heap.push((key, val));
    }

    /// Mark element as deleted — O(1). Does not reorder heap.
    pub fn delete(&mut self, val: V) {
        self.deleted.insert(val);
    }

    /// Pop, skipping all tombstoned entries — O(log n) amortized.
    pub fn pop(&mut self) -> Option<(K, V)> {
        loop {
            let (k, v) = self.heap.pop()?;
            if !self.deleted.contains(&v) {
                return Some((k, v));
            }
            self.deleted.remove(&v);
        }
    }
}

// ─── 4. Median Tracker ───────────────────────────────────────────────────────

use std::cmp::Reverse;

/// Running median via two heaps. Add: O(log n). Median: O(1).
pub struct MedianTracker {
    lower: BinaryHeap<i64>,           // max-heap: lower half
    upper: BinaryHeap<Reverse<i64>>,  // min-heap: upper half
}

impl MedianTracker {
    pub fn new() -> Self {
        Self { lower: BinaryHeap::new(), upper: BinaryHeap::new() }
    }

    pub fn add(&mut self, val: i64) {
        match self.lower.peek() {
            Some(&top) if val > top => self.upper.push(Reverse(val)),
            _                      => self.lower.push(val),
        }
        self.rebalance();
    }

    fn rebalance(&mut self) {
        while self.lower.len() > self.upper.len() + 1 {
            let v = self.lower.pop().unwrap();
            self.upper.push(Reverse(v));
        }
        while self.upper.len() > self.lower.len() {
            let Reverse(v) = self.upper.pop().unwrap();
            self.lower.push(v);
        }
    }

    /// Current median. O(1).
    pub fn median(&self) -> Option<f64> {
        match (self.lower.peek(), self.upper.peek()) {
            (None, _) => None,
            (Some(&lo), Some(&Reverse(hi))) if self.lower.len() == self.upper.len() => {
                Some((lo + hi) as f64 / 2.0)
            }
            (Some(&lo), _) => Some(lo as f64),
        }
    }
}

// ─── 5. Dijkstra using IndexedPQ ─────────────────────────────────────────────

pub struct WeightedEdge { pub to: usize, pub weight: i64 }

/// O((E + V) log V) Dijkstra using IndexedPQ.
pub fn dijkstra(graph: &[Vec<WeightedEdge>], src: usize) -> Vec<i64> {
    let v = graph.len();
    let mut dist = vec![i64::MAX; v];
    dist[src] = 0;

    let mut pq = IndexedPQ::<i64>::new(v, |a, b| a < b);
    for node in 0..v {
        pq.insert(node, dist[node]);
    }

    while let Some((u, d_u)) = pq.extract_min() {
        if d_u == i64::MAX { break; }

        for edge in &graph[u] {
            let new_dist = d_u + edge.weight;
            if new_dist < dist[edge.to] && pq.contains(edge.to) {
                dist[edge.to] = new_dist;
                pq.decrease_key(edge.to, new_dist);
            }
        }
    }
    dist
}

// ─── 6. K-Way Merge ──────────────────────────────────────────────────────────

/// Merge k sorted slices. O(n log k).
pub fn k_way_merge(lists: &[Vec<i32>]) -> Vec<i32> {
    // Min-heap entries: (value, list_index, elem_index)
    let mut heap = BinaryHeap::<Reverse<(i32, usize, usize)>>::new();

    for (i, list) in lists.iter().enumerate() {
        if let Some(&v) = list.first() {
            heap.push(Reverse((v, i, 0)));
        }
    }

    let total: usize = lists.iter().map(|l| l.len()).sum();
    let mut result = Vec::with_capacity(total);

    while let Some(Reverse((val, list_i, elem_i))) = heap.pop() {
        result.push(val);
        let next = elem_i + 1;
        if next < lists[list_i].len() {
            heap.push(Reverse((lists[list_i][next], list_i, next)));
        }
    }
    result
}

// ─── 7. Top-K Elements ───────────────────────────────────────────────────────

/// Return the k largest elements. O(n log k).
pub fn top_k(nums: &[i32], k: usize) -> Vec<i32> {
    if k == 0 { return vec![]; }

    // Min-heap of size k: smallest of the "top k" at root
    let mut heap = BinaryHeap::<Reverse<i32>>::new();

    for &n in nums {
        heap.push(Reverse(n));
        if heap.len() > k {
            heap.pop(); // eject the smallest
        }
    }
    heap.into_iter().map(|Reverse(v)| v).collect()
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generic_pq_min() {
        let mut pq = PriorityQueue::min_heap();
        for v in [5, 3, 8, 1, 9, 2] { pq.push(v, ()); }
        let mut last = i32::MIN;
        while let Some((k, _)) = pq.pop() {
            assert!(k >= last);
            last = k;
        }
    }

    #[test]
    fn test_indexed_pq_decrease_key() {
        let mut ipq = IndexedPQ::new(5, |a: &i32, b: &i32| a < b);
        for (id, key) in [(0, 10), (1, 30), (2, 20), (3, 5), (4, 40)] {
            ipq.insert(id, key);
        }
        assert!(ipq.verify());

        // Decrease id=1 from 30 to 1 — should become new min
        ipq.decrease_key(1, 1);
        assert!(ipq.verify());
        let (id, key) = ipq.extract_min().unwrap();
        assert_eq!((id, key), (1, 1));
        assert!(ipq.verify());
    }

    #[test]
    fn test_indexed_pq_delete() {
        let mut ipq = IndexedPQ::new(4, |a: &i32, b: &i32| a < b);
        for (id, key) in [(0, 10), (1, 5), (2, 15), (3, 1)] {
            ipq.insert(id, key);
        }
        ipq.delete(3); // remove the current min (key=1)
        let (id, key) = ipq.extract_min().unwrap();
        assert_eq!((id, key), (1, 5)); // next min is 5
    }

    #[test]
    fn test_dijkstra() {
        let graph = vec![
            vec![WeightedEdge { to: 1, weight: 4 }, WeightedEdge { to: 2, weight: 1 }],
            vec![WeightedEdge { to: 3, weight: 1 }],
            vec![WeightedEdge { to: 1, weight: 2 }, WeightedEdge { to: 3, weight: 5 }],
            vec![WeightedEdge { to: 4, weight: 3 }],
            vec![],
        ];
        let dist = dijkstra(&graph, 0);
        assert_eq!(dist, vec![0, 3, 1, 4, 7]);
    }

    #[test]
    fn test_k_way_merge() {
        let lists = vec![
            vec![1, 4, 7],
            vec![2, 5, 8],
            vec![3, 6, 9],
        ];
        assert_eq!(k_way_merge(&lists), vec![1, 2, 3, 4, 5, 6, 7, 8, 9]);
    }

    #[test]
    fn test_median_tracker() {
        let mut mt = MedianTracker::new();
        mt.add(1); assert_eq!(mt.median(), Some(1.0));
        mt.add(2); assert_eq!(mt.median(), Some(1.5));
        mt.add(3); assert_eq!(mt.median(), Some(2.0));
        mt.add(4); assert_eq!(mt.median(), Some(2.5));
        mt.add(5); assert_eq!(mt.median(), Some(3.0));
    }

    #[test]
    fn test_top_k() {
        let nums = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3];
        let mut result = top_k(&nums, 3);
        result.sort();
        assert_eq!(result, vec![5, 6, 9]);
    }
}

fn main() {
    println!("=== Generic Min PQ ===");
    let mut pq = PriorityQueue::min_heap();
    for (k, v) in [(5,"E"),(1,"A"),(3,"C"),(2,"B"),(4,"D")] {
        pq.push(k, v);
    }
    while let Some((k, v)) = pq.pop() {
        println!("  priority={k} val={v}");
    }

    println!("\n=== Indexed PQ ===");
    let mut ipq = IndexedPQ::new(5, |a: &i32, b: &i32| a < b);
    for (id, key) in [(0,10),(1,30),(2,5),(3,20),(4,1)] {
        ipq.insert(id, key);
        println!("  insert(id={id}, key={key})");
    }
    println!("  valid: {}", ipq.verify());
    ipq.decrease_key(1, 0);
    println!("  decrease_key(1, 0) → min: {:?}", ipq.peek());

    println!("\n=== Dijkstra ===");
    let graph = vec![
        vec![WeightedEdge{to:1,weight:4}, WeightedEdge{to:2,weight:1}],
        vec![WeightedEdge{to:3,weight:1}],
        vec![WeightedEdge{to:1,weight:2}, WeightedEdge{to:3,weight:5}],
        vec![WeightedEdge{to:4,weight:3}],
        vec![],
    ];
    println!("  dist from 0: {:?}", dijkstra(&graph, 0));

    println!("\n=== Median Tracker ===");
    let mut mt = MedianTracker::new();
    for v in [2, 3, 4, 5, 6, 11, 1] {
        mt.add(v);
        println!("  add({v:2}) → median={:?}", mt.median());
    }

    println!("\n=== K-Way Merge ===");
    let lists = vec![vec![1,4,7,10], vec![2,5,8,11], vec![3,6,9,12]];
    println!("  merged: {:?}", k_way_merge(&lists));

    println!("\n=== Top-3 ===");
    let nums = vec![3,1,4,1,5,9,2,6,5,3,5];
    println!("  top-3 of {:?}: {:?}", nums, top_k(&nums, 3));
}
```

---

## 11. Algorithmic Applications — Deep Dives

### 11.1 Dijkstra — Two Implementation Strategies

```
LAZY DIJKSTRA (simple)              EAGER DIJKSTRA (optimal)
─────────────────────────           ─────────────────────────
PQ contains (dist, node) pairs      PQ is an IndexedPQ of size V
Multiple entries per node OK        Each node appears at most once
On extraction, skip stale ones      decrease_key on relaxation
Space: O(E) in worst case           Space: O(V) always
Time:  O(E log E)                   Time:  O((E+V) log V)

For sparse graphs (E ~ V): equivalent
For dense graphs (E ~ V²): Eager wins — O(V² log V) vs O(V² log V²) = O(V² log V)
```

### 11.2 Prim's MST — PQ-centric View

```
Maintain a PQ of vertices, keyed by min edge weight to current MST.
Initially: source has key 0, all others have key ∞.

Each iteration:
  1. extract_min: vertex u with minimum edge weight to MST
  2. Add u to MST
  3. For each neighbor v of u:
       if edge(u,v).weight < key[v]:
           decrease_key(v, edge(u,v).weight)  ← Indexed PQ required

Complexity: O((V + E) log V) with binary heap IPQ
            O(E + V log V)   with Fibonacci heap
```

### 11.3 A* Search

```
PQ ordered by f(n) = g(n) + h(n):
  g(n) = cost from start to n (known)
  h(n) = heuristic estimate from n to goal

Key insight: A* is Dijkstra + heuristic guidance.
The PQ structure is identical — only the key changes from dist to f(n).

When h(n) = 0 for all n: A* degenerates to Dijkstra
When h(n) is consistent (triangle inequality): A* is optimal
Admissible but inconsistent h: may re-expand nodes → need visited set
```

### 11.4 Huffman Coding

```
Build prefix code by repeatedly merging the two lowest-frequency symbols:

1. Insert all symbols into min-PQ keyed by frequency
2. While PQ.size > 1:
     a. left  = PQ.extract_min()
     b. right = PQ.extract_min()
     c. merged = internal_node(freq = left.freq + right.freq)
     d. PQ.insert(merged)
3. PQ root = Huffman tree root

This is a greedy algorithm — PQ enforces the greedy choice at each step.
Time: O(n log n)
Proof of optimality: Exchange argument on prefix-free codes
```

### 11.5 Event-Driven Simulation

```
Priority Queue models a timeline of future events:
  key   = event timestamp
  value = Event { type, parameters }

Main loop:
  while PQ not empty:
      (time, event) = PQ.extract_min()
      advance_clock(time)
      process(event)         ← may insert new future events into PQ
      for new_event in generated_events:
          PQ.insert(new_event.time, new_event)

This is used in: network simulators, physics engines,
                 operating system schedulers, circuit simulators
```

---

## 12. Problem Patterns & Recognition Map

```
PATTERN RECOGNITION GUIDE
═══════════════════════════════════════════════════════════

SIGNAL IN PROBLEM               → APPROACH
─────────────────────────────────────────────────────────
"kth largest/smallest"          → Fixed-size heap of size k
"top k elements"                → Fixed-size min-heap of size k
"stream, find median"           → Two-heap median tracker
"merge k sorted lists"          → k-way merge with min-heap
"shortest path weighted"        → Dijkstra = IPQ + relaxation
"minimum spanning tree"         → Prim = IPQ + decrease-key
"schedule tasks by priority"    → Priority queue direct use
"sliding window max/min"        → Monotonic deque (not heap!)
"event simulation"              → Min-heap keyed by timestamp
"optimal prefix code"           → Huffman = min-heap greedy
"connect ropes minimum cost"    → Min-heap, repeatedly merge 2
"find k closest points"         → Max-heap of size k
"sort nearly sorted array"      → Min-heap of size k+1
"process in arrival order, tie" → Stable PQ (composite key)
"graph: all pairs shortest"     → Dijkstra from each vertex

HEAP SIZING RULE:
  Find k LARGEST?  → Keep a min-heap of size k
  Find k SMALLEST? → Keep a max-heap of size k
  (Counterintuitive: to find largest, keep the smallest as a "gate")

TWO-HEAP PROBLEMS:
  Median maintenance
  Balance load between two groups
  Partition stream into two halves with property

LAZY VS EAGER HEAP:
  Lazy deletion: simpler code, slightly more memory/time
  Indexed PQ:    asymptotically better, required for decrease-key
  Rule: use lazy unless graph is dense or time limit is strict
```

---

## The Master Summary

The Priority Queue ADT is one of the most consequential abstractions in computer science. Every graph algorithm of note — Dijkstra, Prim, A*, Huffman — reduces to: *always process the most promising element first*. The PQ enforces this discipline mechanically.

**The expert's hierarchy of understanding:**

```
Level 1 (Novice):    "A heap is an array with some swapping"
Level 2 (Intermediate): "A heap is a complete binary tree in array form"
Level 3 (Advanced):  "A heap is a partial-order structure optimized for extremum queries"
Level 4 (Expert):    "A priority queue is an ADT. The binary heap is one
                       implementation. The choice of implementation determines
                       the algorithm's asymptotic complexity. The indexed
                       priority queue enables decrease-key, which is the
                       operation that separates O(E log E) from O((E+V) log V)
                       in Dijkstra — a difference that matters at scale."
```

The monk's discipline here: implement the Indexed Priority Queue from scratch — the three-array dance (`heap`, `pos`, `keys`) — until every swap automatically triggers both `pos` updates without thinking. That is when you have truly internalized the structure.