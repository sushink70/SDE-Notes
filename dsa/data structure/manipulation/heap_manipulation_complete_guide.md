# 🧠 Heap Manipulation: The Complete In-Depth Guide
## From Fundamentals to Expert-Level Mastery

> *"A heap is not just a data structure — it is a contract. Understanding what it promises, what it forbids, and where it lies is the difference between a coder and an engineer."*

---

## Table of Contents

1. [Prerequisites — Terms You Must Know](#1-prerequisites)
2. [What Is a Heap?](#2-what-is-a-heap)
3. [Heap Properties — The Contract](#3-heap-properties)
4. [Internal Memory Layout — How a Heap Really Looks](#4-internal-memory-layout)
5. [Types of Heaps](#5-types-of-heaps)
6. [Index Arithmetic — The Heart of Array-Based Heaps](#6-index-arithmetic)
7. [What You CAN Do — All Legal Operations](#7-what-you-can-do)
   - 7.1 Insert (Push)
   - 7.2 Extract Max/Min (Pop)
   - 7.3 Peek
   - 7.4 Sift Up (Bubble Up)
   - 7.5 Sift Down (Heapify Down)
   - 7.6 Build Heap (Heapify)
   - 7.7 Decrease Key / Increase Key
   - 7.8 Delete Arbitrary Element
   - 7.9 Heap Sort
   - 7.10 Merge Heaps
   - 7.11 Replace Root
   - 7.12 Meld (Mergeable Heaps)
8. [What You CANNOT Do Efficiently](#8-what-you-cannot-do)
9. [Common Mistakes — The Traps Every Developer Falls Into](#9-common-mistakes)
10. [Advanced Heap Variants](#10-advanced-heap-variants)
11. [Complexity Reference Card](#11-complexity-reference-card)
12. [Implementations — C, Rust, Go](#12-implementations)
    - 12.1 C Implementation
    - 12.2 Rust Implementation
    - 12.3 Go Implementation
13. [Mental Models for Heap Intuition](#13-mental-models)
14. [Deliberate Practice Problems](#14-deliberate-practice-problems)

---

## 1. Prerequisites

Before anything else — terms that will appear everywhere in this guide.

### Glossary of Terms

| Term | Plain English Meaning |
|------|----------------------|
| **Node** | A single element/value stored in the heap |
| **Root** | The very top element. In a max-heap: the largest. In a min-heap: the smallest |
| **Parent** | The node directly above a given node in the tree |
| **Child** | A node directly below a given node (left child, right child) |
| **Leaf** | A node with no children — at the bottom of the tree |
| **Complete Binary Tree** | A tree where every level is fully filled except possibly the last, and the last level is filled from left to right |
| **Height** | Number of edges from the root to the deepest leaf. For n elements: floor(log₂ n) |
| **Level** | Distance from the root (root = level 0) |
| **Sift Up** | Moving a node UP toward the root by swapping with its parent |
| **Sift Down** | Moving a node DOWN away from root by swapping with its largest/smallest child |
| **Heapify** | The process of building or restoring heap property |
| **Heap Property** | The rule: parent is always ≥ children (max-heap) or ≤ children (min-heap) |
| **Priority** | The "importance" of an element; higher priority = served first |
| **In-place** | Sorting/transforming without extra memory |
| **Auxiliary Array** | A helper/temporary array used during computation |
| **Invariant** | A property that must always hold true (like heap property) |
| **Amortized** | Average cost over many operations, even if some individual ops are expensive |

---

## 2. What Is a Heap?

A **heap** is a specialized, partially-ordered tree-based data structure that satisfies the **heap property**. It is most commonly implemented as an **array** (not as nodes with pointers), making it cache-friendly and memory-efficient.

### Two Key Facts That Define a Heap:

1. **It is a Complete Binary Tree** — every level is filled left to right
2. **It satisfies the Heap Property** — parent is always greater than (or less than) both children

A heap is **NOT** a fully sorted structure. It is only **partially ordered** — you only know the root is the best (max or min), not the entire order.

### Why Does This Matter?

```
SORTED ARRAY:          [1, 2, 3, 4, 5, 6, 7]     <- knows all ordering
MAX-HEAP (array):      [7, 5, 6, 3, 4, 1, 2]     <- only knows root is max
```

This "partial order" is exactly what gives heaps their power:
- Insert: O(log n)  — sorted array: O(n)
- Get max/min: O(1) — sorted array: O(1)
- Extract max/min: O(log n) — sorted array: O(n) to maintain order

---

## 3. Heap Properties — The Contract

### Max-Heap Property
> **For every node N: value(N) ≥ value(children of N)**

```
                    100
                   /    \
                 90       80
                /  \     /  \
              70    60  50   40
             / \
            30  20

Every parent is GREATER THAN or EQUAL to its children.
100 ≥ 90, 100 ≥ 80
90 ≥ 70, 90 ≥ 60
80 ≥ 50, 80 ≥ 40
70 ≥ 30, 70 ≥ 20
```

### Min-Heap Property
> **For every node N: value(N) ≤ value(children of N)**

```
                     1
                   /    \
                  3       2
                /  \     /  \
               7    5   8    4
              / \
             10   9

Every parent is LESS THAN or EQUAL to its children.
1 ≤ 3, 1 ≤ 2
3 ≤ 7, 3 ≤ 5
etc.
```

### Critical Insight — What Heap Property Does NOT Tell You

```
MAX-HEAP:
                    100
                   /    \
                 19       36
                /  \     /  \
              17    3  25   1

Q: Is 19 > 17?   YES (happens to be true)
Q: Is 19 > 25?   NO!  (19 < 25, but that's FINE — they're in different subtrees)
Q: Is 36 > 19?   YES  (but only because root-to-leaf matters, not siblings)

SIBLINGS HAVE NO ORDERING GUARANTEE.
LEFT CHILD vs RIGHT CHILD — NO ORDERING GUARANTEE.
```

This is the single most important insight about heaps. The ordering is ONLY vertical (parent-child), never horizontal (sibling-sibling).

---

## 4. Internal Memory Layout — How a Heap Really Looks

### Array Representation

A heap is stored as a **1D array** (or 0-indexed array). The tree structure is implicit — there are no actual pointers.

```
TREE VISUAL:
                     Index: 0
                        |
                       100
                      /     \
              Index:1         Index:2
                90               80
              /    \           /    \
         Index:3  Index:4  Index:5  Index:6
           70       60       50       40
          /  \
      Index:7 Index:8
        30      20


ARRAY LAYOUT (index 0 to 8):
 ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
 │ 100 │  90 │  80 │  70 │  60 │  50 │  40 │  30 │  20 │
 └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
   [0]   [1]   [2]   [3]   [4]   [5]   [6]   [7]   [8]


MEMORY (bytes, assuming 4-byte ints, contiguous in RAM):
 Address:  0x00  0x04  0x08  0x0C  0x10  0x14  0x18  0x1C  0x20
           ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
           │ 100 │  90 │  80 │  70 │  60 │  50 │  40 │  30 │  20 │
           └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

### Level-by-Level Breakdown

```
LEVEL 0 (root):    [0]                          → 1 node
LEVEL 1:           [1],  [2]                    → 2 nodes
LEVEL 2:           [3],  [4],  [5],  [6]        → 4 nodes
LEVEL 3:           [7],  [8],  [9], [10]...     → up to 8 nodes
LEVEL k:           starts at index 2^k - 1      → up to 2^k nodes

For n elements, the heap occupies exactly indices 0..n-1
```

### Why Array and Not Pointers?

```
POINTER-BASED TREE (BAD for heaps):
   Node { value: 100, left: *Node, right: *Node }
   ↓
   Memory scattered across heap (the OS heap, not our data structure!)
   Cache miss every traversal — each pointer dereference potentially
   jumps to a totally different memory region.

ARRAY-BASED (GOOD):
   arr[0], arr[1], arr[2]... all contiguous
   CPU cache line = 64 bytes = fits ~16 ints
   Traversal reads sequential memory → cache hits → FAST
```

---

## 5. Types of Heaps

### 5.1 Binary Heap (Most Common)

```
Each node has AT MOST 2 children.
This is what people mean when they say "heap" without qualification.

Max-Heap: root = maximum element
Min-Heap: root = minimum element
```

### 5.2 d-ary Heap (Generalized)

```
Each node has AT MOST d children (d = 2, 3, 4...)

d=4 (quad-heap) example:
                    100
               /   / \   \
             90   80  70  60
            /|\ \
          50 40 30 20 ...

Array index arithmetic for d-ary heap (0-indexed):
  Parent of i:       floor((i - 1) / d)
  k-th child of i:   d*i + k + 1   (k = 0..d-1)

TRADE-OFF:
  Larger d → shallower tree → fewer sift-down steps
  But each sift-down step compares d children instead of 2
  Optimal d ≈ 4 for cache performance in practice
```

### 5.3 Fibonacci Heap

```
Collection of heap-ordered trees (not necessarily binary).
Lazy merging and consolidation.

KEY ADVANTAGE:
  Decrease-key: O(1) amortized  (binary heap: O(log n))
  Used in Dijkstra's and Prim's for best theoretical complexity.

PRACTICAL ISSUE:
  High constant factors, complex implementation → rarely used in practice
```

### 5.4 Binomial Heap

```
Collection of binomial trees.
Supports O(log n) merge.

Binomial tree B_k:
  B_0 = single node
  B_k = two B_(k-1) trees, one attached as leftmost child of other

B_0:  •
B_1:  •
      |
      •
B_2:  •
     / \
    •   •
    |
    •
B_3:  •
     /|\  \
    •  •   •
   /|  |
  • •  •
  |
  •
```

### 5.5 Leftist Heap / Skew Heap

```
Binary heaps that support efficient merge.
Leftist heap: maintains "s-value" (shortest path to null descendant)
Skew heap: self-adjusting version of leftist heap (amortized O(log n) merge)
```

### 5.6 Min-Max Heap

```
Levels alternate between min-levels and max-levels.
- Even levels (0, 2, 4...): min-levels
- Odd levels (1, 3, 5...): max-levels

Allows BOTH min AND max extraction in O(log n).

         8  ← min level (level 0, root = global min)
        / \
      71   70  ← max level (these are local maxima)
     / \  / \
    31 10 48 13  ← min level
   /
   9  ← min level
```

---

## 6. Index Arithmetic — The Heart of Array-Based Heaps

This is the **magic formula** that makes array-based heaps work without pointers.

### 0-Indexed (Most Common in Modern Code)

```
For element at index i:

  PARENT:      floor((i - 1) / 2)    [invalid for i = 0, that's the root]
  LEFT CHILD:  2*i + 1
  RIGHT CHILD: 2*i + 2

Example for node at index 3 (value = 70):
  Parent:       floor((3-1)/2) = floor(1) = 1   → arr[1] = 90 ✓
  Left child:   2*3 + 1 = 7                      → arr[7] = 30 ✓
  Right child:  2*3 + 2 = 8                      → arr[8] = 20 ✓

BOUNDS CHECK:
  Left child exists:   2*i + 1 < n
  Right child exists:  2*i + 2 < n
  Is a leaf:           2*i + 1 >= n  (no left child → no children at all,
                                      because heap is complete left-to-right)
```

### 1-Indexed (Classic Textbook Style)

```
For element at index i (root at index 1):

  PARENT:      floor(i / 2)
  LEFT CHILD:  2*i
  RIGHT CHILD: 2*i + 1

Slightly simpler formulas (bit-shift friendly):
  Parent: i >> 1
  Left:   i << 1
  Right:  (i << 1) | 1
```

### Visualization of Index Relationships

```
0-INDEXED ARRAY HEAP (n=9):

Index:  0    1    2    3    4    5    6    7    8
Value: 100   90   80   70   60   50   40   30   20

PARENT-CHILD RELATIONSHIPS:
  arr[0]=100  → children: arr[1]=90,  arr[2]=80
  arr[1]=90   → children: arr[3]=70,  arr[4]=60   parent: arr[0]=100
  arr[2]=80   → children: arr[5]=50,  arr[6]=40   parent: arr[0]=100
  arr[3]=70   → children: arr[7]=30,  arr[8]=20   parent: arr[1]=90
  arr[4]=60   → no children (leaf)                parent: arr[1]=90
  arr[5]=50   → no children (leaf)                parent: arr[2]=80
  arr[6]=40   → no children (leaf)                parent: arr[2]=80
  arr[7]=30   → no children (leaf)                parent: arr[3]=70
  arr[8]=20   → no children (leaf)                parent: arr[3]=70

TREE (with array indices shown):
              [0]100
             /       \
         [1]90       [2]80
         /   \       /   \
      [3]70 [4]60 [5]50 [6]40
      /   \
  [7]30  [8]20
```

---

## 7. What You CAN Do — All Legal Operations

### 7.1 Insert (Push)

**What it does:** Add a new element while maintaining heap property.

**Algorithm:**
1. Place new element at the END of the array (next available position)
2. Sift Up: compare with parent, swap if out of order, repeat

**Why insert at the end?** Because the heap must remain a complete binary tree. Adding anywhere else would break the structure.

```
ALGORITHM FLOW — Insert 85 into max-heap:

BEFORE:
              100
             /     \
           90        80
          /  \      /  \
        70    60  50    40
        /\
      30  20

STEP 1: Add 85 at end (index 9):
              100
             /     \
           90        80
          /  \      /  \
        70    60  50    40
        /\ \
      30  20 85   ← new element, last position

Array: [100, 90, 80, 70, 60, 50, 40, 30, 20, 85]
                                                ^^

STEP 2: Sift Up — compare 85 with parent
  Index of 85 = 9
  Parent = floor((9-1)/2) = floor(4) = 4 → arr[4] = 60
  85 > 60? YES → SWAP

              100
             /     \
           90        80
          /  \      /  \
        70    85  50    40
        /\ \
      30  20 60

Array: [100, 90, 80, 70, 85, 50, 40, 30, 20, 60]

STEP 3: Sift Up continues — compare 85 with new parent
  Index of 85 = 4
  Parent = floor((4-1)/2) = floor(1) = 1 → arr[1] = 90
  85 > 90? NO → STOP

FINAL:
              100
             /     \
           90        80
          /  \      /  \
        70    85  50    40
        /\ \
      30  20 60

Array: [100, 90, 80, 70, 85, 50, 40, 30, 20, 60]
```

**Flowchart — Insert Operation:**

```
  ┌─────────────────────────────┐
  │  INSERT(heap, value)         │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │  Append value to end        │
  │  heap[n] = value; n++       │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │  i = n - 1  (last index)    │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │  Is i > 0?                  │◄──────────────┐
  └──────────────┬──────────────┘               │
           YES   │    NO                        │
                 │     └──► DONE                │
                 ▼                              │
  ┌─────────────────────────────┐               │
  │  parent = (i-1)/2           │               │
  │  Is heap[i] > heap[parent]? │               │
  └──────────────┬──────────────┘               │
           YES   │    NO                        │
                 │     └──► DONE                │
                 ▼                              │
  ┌─────────────────────────────┐               │
  │  SWAP heap[i] and           │               │
  │  heap[parent]               │               │
  └──────────────┬──────────────┘               │
                 │                              │
                 ▼                              │
  ┌─────────────────────────────┐               │
  │  i = parent                 │───────────────┘
  └─────────────────────────────┘
```

**Complexity:** O(log n) — in the worst case, we sift up the full height of the tree.
**Best case:** O(1) — new element is already smaller than (max-heap) its parent.

---

### 7.2 Extract Max/Min (Pop)

**What it does:** Remove and return the root (the max or min element).

**Algorithm:**
1. Save root value (to return it)
2. Move LAST element to root position
3. Decrease size by 1
4. Sift Down from root

**Why move last element to root?** Because we must remove a node while keeping the complete binary tree property. Only the last element can be removed without breaking the structure.

```
ALGORITHM FLOW — Extract Max from max-heap:

BEFORE:
              100   ← this is what we return
             /     \
           90        80
          /  \      /  \
        70    60  50    40
        /\
      30  20

STEP 1: Save 100, move last element (20) to root:
               20   ← out of order! needs fixing
             /     \
           90        80
          /  \      /  \
        70    60  50    40
        /
      30

Array: [20, 90, 80, 70, 60, 50, 40, 30]   (size = 8)

STEP 2: Sift Down from root (index 0, value=20)
  Left child:  arr[1] = 90
  Right child: arr[2] = 80
  Largest child: 90 at index 1
  20 < 90? YES → SWAP

               90
             /     \
           20        80
          /  \      /  \
        70    60  50    40
        /
      30

STEP 3: Continue Sift Down (now at index 1, value=20)
  Left child:  arr[3] = 70
  Right child: arr[4] = 60
  Largest child: 70 at index 3
  20 < 70? YES → SWAP

               90
             /     \
           70        80
          /  \      /  \
        20    60  50    40
        /
      30

STEP 4: Continue Sift Down (now at index 3, value=20)
  Left child:  arr[7] = 30
  Right child: arr[8] → doesn't exist (n=8)
  Only left child: 30
  20 < 30? YES → SWAP

               90
             /     \
           70        80
          /  \      /  \
        30    60  50    40
        /
      20

STEP 5: Continue Sift Down (now at index 7, value=20)
  Left child: arr[15] → doesn't exist (n=8)
  No children → STOP (20 is now a leaf)

FINAL: Return 100, heap is now:
[90, 70, 80, 30, 60, 50, 40, 20]
```

**Flowchart — Extract Max:**

```
  ┌─────────────────────────────┐
  │  EXTRACT_MAX(heap)           │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │  Is heap empty? (n == 0)    │
  └──────────────┬──────────────┘
           YES   │    NO
                 │     │
       Error/    │     ▼
       None  ◄───┘  ┌─────────────────────────────┐
                    │  max = heap[0]               │
                    │  heap[0] = heap[n-1]         │
                    │  n--                         │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  SIFT_DOWN(heap, 0, n)       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  return max                 │
                    └─────────────────────────────┘
```

**Complexity:** O(log n) — sift down traverses at most tree height levels.

---

### 7.3 Peek

**What it does:** Return root element WITHOUT removing it.

```
PEEK(heap) = heap[0]    // O(1), just array access

For max-heap: returns the maximum element
For min-heap: returns the minimum element
```

**Complexity:** O(1) — always, guaranteed.

---

### 7.4 Sift Up (Bubble Up)

**What it does:** Restore heap property upward from a given index. Used after insert or decrease-key on a max-heap (increase-key on min-heap).

```
SIFT_UP(heap, i):
  while i > 0:
    parent = (i - 1) / 2
    if heap[i] > heap[parent]:   // max-heap condition
      swap(heap[i], heap[parent])
      i = parent
    else:
      break

VISUAL — Sift Up from index 8 (value=95, max-heap violation):

BEFORE:
              100
             /     \
           90        80
          /  \      /  \
        70    60  50    40
        /\
      30  95   ← too large! violates heap property with parent 70

STEP 1: i=8, parent=3. 95 > 70? YES → SWAP
              100
             /     \
           90        80
          /  \      /  \
        70    60  50    40  [wrong, re-draw]
       ↓
              100
             /     \
           90        80
          /  \      /  \
        95    60  50    40
        /\
      30  70

STEP 2: i=3, parent=1. 95 > 90? YES → SWAP
              100
             /     \
           95        80
          /  \      /  \
        90    60  50    40
        /\
      30  70

STEP 3: i=1, parent=0. 95 > 100? NO → STOP

DONE.
```

---

### 7.5 Sift Down (Heapify Down)

**What it does:** Restore heap property downward from a given index. Core of Extract and Build-Heap.

```
SIFT_DOWN(heap, i, n):
  loop:
    largest = i
    left  = 2*i + 1
    right = 2*i + 2

    if left < n AND heap[left] > heap[largest]:
      largest = left
    if right < n AND heap[right] > heap[largest]:
      largest = right

    if largest != i:
      swap(heap[i], heap[largest])
      i = largest
    else:
      break   // heap property restored

CRITICAL: We find the LARGEST among {i, left, right} and swap i with it.
          This ensures we always move the LARGER value UP.

VISUAL — Sift Down from index 0 (value=5, n=7):

BEFORE:
                5    ← too small for root
              /    \
            15       10
           /   \    /   \
          12    9  7     6

STEP 1: i=0. left=1(15), right=2(10). largest=1(15). 5<15 → SWAP
               15
              /    \
             5       10
           /   \    /   \
          12    9  7     6

STEP 2: i=1. left=3(12), right=4(9). largest=3(12). 5<12 → SWAP
               15
              /    \
            12       10
           /   \    /   \
          5     9  7     6

STEP 3: i=3. left=7, right=8. Both >= n=7? No children. STOP.

DONE:
               15
              /    \
            12       10
           /   \    /   \
          5     9  7     6
```

---

### 7.6 Build Heap (Heapify / Heapify-All)

**What it does:** Convert an arbitrary array into a valid heap IN-PLACE.

**The Naïve Way:** Insert elements one by one → O(n log n)

**The Smart Way (Floyd's Algorithm):** Start from the last non-leaf node and sift down each node toward the root → **O(n)** ← This is a famous result!

```
WHY O(n) and not O(n log n)?

Mathematical proof intuition:
  - Nodes at height h: ≈ n / 2^(h+1)
  - Sift-down cost for height h: O(h)
  - Total = Σ (n/2^(h+1)) * h  for h=0 to log n
           = n * Σ (h / 2^(h+1))
           = n * 1  (the sum converges to 1)
           = O(n)

Half the nodes are leaves → sift-down cost = 0
Quarter of nodes at height 1 → sift-down cost = 1
Eighth at height 2 → cost = 2
...very few nodes near the top!
```

**Algorithm:**

```
BUILD_HEAP(arr, n):
  // Last non-leaf node is at index floor((n-2)/2)
  // For n elements in 0-indexed: last_non_leaf = n/2 - 1
  for i from (n/2 - 1) down to 0:
    SIFT_DOWN(arr, i, n)

VISUAL — Build Max-Heap from [3, 1, 6, 5, 2, 4]:

ORIGINAL ARRAY:
 ┌───┬───┬───┬───┬───┬───┐
 │ 3 │ 1 │ 6 │ 5 │ 2 │ 4 │
 └───┴───┴───┴───┴───┴───┘
   0   1   2   3   4   5

AS A TREE:
               3
             /    \
            1      6
           / \    /
          5   2  4

n=6, last non-leaf = 6/2 - 1 = 2

ITERATION 1: i=2 (value=6)
  Children: arr[5]=4, arr[6]=doesn't exist
  6 > 4, no swap needed.

ITERATION 2: i=1 (value=1)
  Children: arr[3]=5, arr[4]=2
  Largest child: 5 at index 3
  1 < 5 → SWAP

               3
             /    \
            5      6
           / \    /
          1   2  4

ITERATION 3: i=0 (value=3)
  Children: arr[1]=5, arr[2]=6
  Largest child: 6 at index 2
  3 < 6 → SWAP

               6
             /    \
            5      3
           / \    /
          1   2  4

  Now continue sift-down from index 2 (value=3):
  Children: arr[5]=4, arr[6]=doesn't exist
  3 < 4 → SWAP

               6
             /    \
            5      4
           / \    /
          1   2  3

DONE! Valid max-heap: [6, 5, 4, 1, 2, 3]

 ┌───┬───┬───┬───┬───┬───┐
 │ 6 │ 5 │ 4 │ 1 │ 2 │ 3 │
 └───┴───┴───┴───┴───┴───┘
```

---

### 7.7 Decrease Key / Increase Key

**What it does:** Change the value of an existing element and restore heap property.

**Requirements:** You must know the **index** of the element to change (O(1) if you have a position map).

```
For MAX-HEAP:
  DECREASE_KEY(heap, i, new_val):
    heap[i] = new_val      // value decreased
    SIFT_DOWN(heap, i, n)  // might need to go DOWN

  INCREASE_KEY(heap, i, new_val):
    heap[i] = new_val      // value increased
    SIFT_UP(heap, i)       // might need to go UP

For MIN-HEAP (used in Dijkstra's, Prim's):
  DECREASE_KEY(heap, i, new_val):
    heap[i] = new_val      // value decreased
    SIFT_UP(heap, i)       // smaller value → might go UP

WHY:
  If a node's value INCREASES in a max-heap:
    It might now be larger than its parent → sift UP
  If a node's value DECREASES in a max-heap:
    It might now be smaller than its children → sift DOWN

EXAMPLE — decrease key 90 → 5 in max-heap:

BEFORE:
              100
             /     \
           90        80
          /  \      /  \
        70    60  50    40

AFTER setting arr[1] = 5:
              100
             /     \
            5        80   ← VIOLATION! 5 < 70, 5 < 60
          /  \      /  \
        70    60  50    40

Sift Down from index 1 (value=5):
  Left=70, Right=60, Largest=70 → SWAP

              100
             /     \
           70        80
          /  \      /  \
         5    60  50    40

  Left child of index 3 = arr[7] (doesn't exist), no children → STOP

FINAL:
              100
             /     \
           70        80
          /  \      /  \
         5    60  50    40
```

**Complexity:** O(log n) for both sift-up and sift-down paths.

**Real-World Use:** This is crucial for Dijkstra's shortest path algorithm — when a shorter distance to a node is found, decrease its key in the priority queue.

---

### 7.8 Delete Arbitrary Element

**What it does:** Remove an element at any index (not just root).

**Algorithm:**
1. Replace element at index i with the LAST element
2. Decrease size by 1
3. Run BOTH sift-up AND sift-down (only one will actually do work)

```
DELETE_AT(heap, i, n):
  heap[i] = heap[n-1]   // replace with last
  n--
  SIFT_UP(heap, i)      // one of these will do nothing
  SIFT_DOWN(heap, i, n) // the other will fix violations

WHY BOTH SIFT-UP AND SIFT-DOWN?
  The replacement value (previously the last element) could be:
  - LARGER than deleted node's parent → needs to go UP
  - SMALLER than deleted node's children → needs to go DOWN
  - Perfect as is → neither runs

EXAMPLE — Delete element at index 2 (value=80):

BEFORE:
              100
             /     \
           90        80   ← delete this
          /  \      /  \
        70    60  50    40
        /\
      30  20

STEP 1: Replace index 2 with last element (20):
              100
             /     \
           90        20   ← 20 is here now
          /  \      /  \
        70    60  50    40
        /
      30

Array: [100, 90, 20, 70, 60, 50, 40, 30]  n=8

STEP 2: Sift Up from index 2 (value=20):
  Parent = arr[0] = 100. 20 < 100 → no swap. DONE with sift-up.

STEP 3: Sift Down from index 2 (value=20):
  Left=arr[5]=50, Right=arr[6]=40. Largest=50 at index 5. 20<50 → SWAP.

              100
             /     \
           90        50
          /  \      /  \
        70    60  20    40
        /
      30

  Continue from index 5 (value=20): no children (2*5+1=11 >= 8). STOP.

FINAL:
              100
             /     \
           90        50
          /  \      /  \
        70    60  20    40
        /
      30
```

**Complexity:** O(log n)

---

### 7.9 Heap Sort

**What it does:** Sort an array in-place using a heap. O(n log n) worst case, O(1) extra space.

**Algorithm:**
1. Build a max-heap from the array → O(n)
2. Repeatedly extract max and place at end → O(n log n)

```
HEAP_SORT(arr, n):
  BUILD_HEAP(arr, n)                // O(n)
  for i from n-1 down to 1:        // n-1 iterations
    swap(arr[0], arr[i])            // largest goes to end
    SIFT_DOWN(arr, 0, i)            // restore heap in arr[0..i-1]

VISUAL — Heap Sort on [3, 1, 6, 5, 2, 4]:

STEP 1: Build max-heap → [6, 5, 4, 1, 2, 3]
 ┌───┬───┬───┬───┬───┬───┐
 │ 6 │ 5 │ 4 │ 1 │ 2 │ 3 │
 └───┴───┴───┴───┴───┴───┘

STEP 2: Swap arr[0] ↔ arr[5], sift-down on [0..4]:
 ┌───┬───┬───┬───┬───║───┐
 │ 5 │ 3 │ 4 │ 1 │ 2 ║ 6 │
 └───┴───┴───┴───┴───║───┘
  (heap region)   (sorted region)

STEP 3: Swap arr[0] ↔ arr[4], sift-down on [0..3]:
 ┌───┬───┬───┬───║───┬───┐
 │ 4 │ 3 │ 2 │ 1 ║ 5 │ 6 │
 └───┴───┴───┴───║───┴───┘

STEP 4: Swap arr[0] ↔ arr[3], sift-down on [0..2]:
 ┌───┬───┬───║───┬───┬───┐
 │ 3 │ 1 │ 2 ║ 4 │ 5 │ 6 │
 └───┴───┴───║───┴───┴───┘

STEP 5: Swap arr[0] ↔ arr[2], sift-down on [0..1]:
 ┌───┬───║───┬───┬───┬───┐
 │ 2 │ 1 ║ 3 │ 4 │ 5 │ 6 │
 └───┴───║───┴───┴───┴───┘

STEP 6: Swap arr[0] ↔ arr[1]:
 ┌───║───┬───┬───┬───┬───┐
 │ 1 ║ 2 │ 3 │ 4 │ 5 │ 6 │
 └───║───┴───┴───┴───┴───┘

SORTED: [1, 2, 3, 4, 5, 6] ✓

KEY INSIGHT:
  Heap sort using MAX-HEAP gives ASCENDING order (largest placed at end first).
  Heap sort using MIN-HEAP gives DESCENDING order.
```

**Complexity:** O(n log n) always. Not stable (equal elements may reorder). Cache-unfriendly due to random access patterns → slower than quicksort in practice despite same asymptotic complexity.

---

### 7.10 Merge Two Heaps

**Naïve merge (binary heap):**

```
MERGE(heap1[n1], heap2[n2]) → heap[n1+n2]:
  1. Concatenate both arrays → arr[n1+n2]
  2. BUILD_HEAP(arr, n1+n2)   → O(n1+n2)

This is O(n) total, which is actually good!
But it destroys the original heaps.

EXAMPLE:
  heap1 = [10, 7, 9, 4, 3]
  heap2 = [8, 6, 5, 1, 2]
  merged_arr = [10, 7, 9, 4, 3, 8, 6, 5, 1, 2]
  BUILD_HEAP → [10, 7, 9, 5, 3, 8, 6, 4, 1, 2]
```

**True O(log n) merge requires advanced heaps** (Fibonacci, Leftist, Skew, Binomial).

---

### 7.11 Replace Root

**What it does:** Replace root with a new value without two separate operations.

```
REPLACE_ROOT(heap, new_val, n):
  heap[0] = new_val
  SIFT_DOWN(heap, 0, n)

This is MORE EFFICIENT than extract_max + insert:
  extract + insert: 2 * O(log n) with constants
  replace_root: 1 * O(log n) — one traversal

WHEN TO USE:
  When you want to "update" the top element.
  Used in: top-k algorithms, sliding window maximums.
```

---

### 7.12 k-th Largest Element Using Heap

```
Find k-th largest in n elements:

APPROACH 1 — Min-heap of size k:
  1. Build min-heap of first k elements
  2. For each remaining element x:
     if x > heap_min: replace root with x, sift-down
  3. Root of heap = k-th largest

  Time: O(n log k)  Space: O(k)

APPROACH 2 — Max-heap, extract k times:
  1. Build max-heap of all n elements → O(n)
  2. Extract max k times → O(k log n)

  Time: O(n + k log n)  Space: O(n)

Which is better?
  k << n → Approach 1 (streaming, memory efficient)
  k ≈ n  → Approach 2

VISUAL — k=3rd largest from [3,2,1,5,6,4]:

  min-heap of size 3:
  After [3,2,1]: heap = [1,3,2] (root=1, min)
  Process 5: 5>1 → replace root → [2,3,5] → sift → [2,3,5]
  Process 6: 6>2 → replace root → [3,5,6] → sift → [3,5,6]
  Process 4: 4>3 → replace root → [4,5,6] → sift → [4,5,6]
  Root = 4 → 3rd largest ✓
```

---

## 8. What You CANNOT Do Efficiently

Understanding the **limitations** of a heap is equally important as knowing its operations. These limitations define when you should choose a different data structure.

### 8.1 Search for Arbitrary Element — O(n)

```
CANNOT do: find(heap, 42) in O(log n)

WHY: Heap has NO ordering guarantee between siblings.
     You must scan the entire array.

EXAMPLE — Search for 50 in max-heap:
  [100, 90, 80, 70, 60, 50, 40, 30, 20]
  You CANNOT binary-search this.
  Yes, you can prune subtrees where root < target (max-heap),
  but worst case is still O(n).

ALTERNATIVE: Use a hash map alongside heap for O(1) lookup.
  This is the "indexed priority queue" pattern.
```

### 8.2 Find k-th Element (for arbitrary k) — O(k log n) or O(n)

```
CANNOT do: kth_element(heap, k) in O(log k) or O(1)

To find k-th largest: must extract k times → O(k log n)
To find k-th smallest: must traverse carefully → still O(k log n) typically

WHY: The partial order doesn't tell you which subtrees contain the k-th element
     without exploration.

ALTERNATIVE: Use an Order Statistics Tree (balanced BST with rank info)
             for O(log n) k-th element queries.
```

### 8.3 Sort in O(n) — Cannot

```
Heap sort = O(n log n). You cannot exploit heap structure to sort faster.
WHY: Getting from partial order to total order requires O(n log n) comparisons.
     (Lower bound for comparison-based sorting)
```

### 8.4 Predecessor / Successor Queries — O(n)

```
CANNOT do: what is the next-smaller element after x? → O(n)

WHY: Heap has no in-order traversal concept.
     Siblings have no ordering.

ALTERNATIVE: Balanced BST (AVL, Red-Black) → O(log n) predecessor/successor.
```

### 8.5 Range Queries — O(n)

```
CANNOT do: find all elements in range [lo, hi] efficiently

WHY: Same reason — no total order maintained.
     Must scan all elements.

ALTERNATIVE: Segment tree or balanced BST for O(log n + k) range queries.
```

### 8.6 Efficient Merge of Two Binary Heaps — O(n)

```
CANNOT do O(log n) merge with a standard binary heap.
Naive merge (concatenate + build-heap) = O(n1 + n2).

ALTERNATIVE:
  Leftist heap, Skew heap, Fibonacci heap → O(log n) merge
  Binomial heap → O(log n) merge
```

### 8.7 Decrease Key Without Knowing Index — O(n)

```
CANNOT efficiently decrease-key if you don't have the index.

First you must find the element → O(n) scan
Then apply decrease-key → O(log n)

Total = O(n) which defeats the purpose.

SOLUTION: Maintain a separate map: element → heap index
          Update map on every swap.
          This is the "indexed priority queue" or "heap with position tracking".
```

### Summary Decision Table

```
OPERATION               | HEAP    | BST     | SORTED ARRAY | HASH MAP
------------------------|---------|---------|--------------|----------
Get min/max             | O(1)    | O(log n)| O(1)         | O(n)
Insert                  | O(log n)| O(log n)| O(n)         | O(1) avg
Delete min/max          | O(log n)| O(log n)| O(n)         | O(n)
Delete arbitrary        | O(log n)*| O(log n)| O(n)         | O(1) avg
Search                  | O(n)   | O(log n)| O(log n)     | O(1) avg
k-th element            | O(k log n)| O(log n)| O(1)       | O(n)
Predecessor/Successor   | O(n)   | O(log n)| O(log n)     | O(n)
Range query             | O(n)   | O(log n+k)| O(log n+k) | O(n)
Merge                   | O(n)   | O(m log(n+m))| O(n+m) | O(n)

* Requires knowing the index (use indexed heap for O(log n))
```

---

## 9. Common Mistakes — The Traps Every Developer Falls Into

### Mistake 1: Off-by-One in Index Arithmetic

```
WRONG (0-indexed, common error):
  parent = i / 2          // WRONG! This is 1-indexed formula
  left   = 2 * i          // WRONG!
  right  = 2 * i + 1      // WRONG!

CORRECT (0-indexed):
  parent = (i - 1) / 2
  left   = 2 * i + 1
  right  = 2 * i + 2

CORRECT (1-indexed):
  parent = i / 2
  left   = 2 * i
  right  = 2 * i + 1

MIXING THEM is a catastrophic bug. Decide and stick to one convention.
```

### Mistake 2: Forgetting Bounds Check in Sift Down

```c
// WRONG — may access out-of-bounds memory:
void sift_down(int *heap, int i, int n) {
    int left = 2*i + 1;
    int right = 2*i + 2;
    int largest = i;

    if (heap[left] > heap[largest])   // BUG: left might be >= n!
        largest = left;
    if (heap[right] > heap[largest])  // BUG: right might be >= n!
        largest = right;
    ...
}

// CORRECT:
void sift_down(int *heap, int i, int n) {
    int left = 2*i + 1;
    int right = 2*i + 2;
    int largest = i;

    if (left < n && heap[left] > heap[largest])
        largest = left;
    if (right < n && heap[right] > heap[largest])
        largest = right;
    ...
}
```

### Mistake 3: Using Wrong Heap Type

```
PROBLEM: Using max-heap when you need min-heap (or vice versa).

EXAMPLE — Dijkstra's algorithm:
  You need the SHORTEST (minimum) distance → use MIN-HEAP
  Many people accidentally use max-heap → wrong shortest path!

IN LANGUAGES WITH MAX-HEAP ONLY (like Rust's BinaryHeap):
  To simulate min-heap: negate all values, negate result when extracting.
  heap.push(-(distance));
  let min_dist = -heap.pop().unwrap();

  OR use std::cmp::Reverse wrapper:
  heap.push(Reverse(distance));
  let min_dist = heap.pop().unwrap().0;
```

### Mistake 4: Modifying Elements Without Restoring Heap Property

```
// WRONG — directly modifying a value destroys heap invariant:
heap[3] = 999;  // HEAP IS NOW CORRUPT!

// CORRECT:
heap[3] = 999;
sift_up(heap, 3);    // or sift_down, depending on direction
// actually: run BOTH and only one will do work
```

### Mistake 5: Heap Sort Order Confusion

```
COMMON CONFUSION:
  "I want ascending order, I'll use min-heap for heap sort."

ACTUALLY:
  MAX-HEAP → ascending order after sort (max goes to end first)
  MIN-HEAP → descending order after sort

WHY: In heap sort, we repeatedly swap ROOT with the LAST element.
     Max root → goes to the END → array is ascending.
```

### Mistake 6: Assuming Equal Elements Have Any Order

```
BAD ASSUMPTION:
  "Both children are equal to parent, so left child is 'more equal'."

REALITY:
  Heap property is ≥ (or ≤), not strict >.
  Equal elements can be ANYWHERE in the heap.
  [5, 5, 5, 5, 5] is a valid heap.
  The order of equal elements is UNDEFINED.

IMPACT: If you use a heap as a priority queue and two tasks have equal
        priority, you cannot predict which one is returned first.
        If order matters → use a stable data structure OR add a
        secondary tiebreaker (e.g., insertion timestamp).
```

### Mistake 7: Not Handling the Single-Element or Empty Heap Case

```c
// WRONG — extracting from empty heap:
int extract_max(int *heap, int *n) {
    int max = heap[0];      // CRASH if n=0!
    heap[0] = heap[*n - 1];
    (*n)--;
    sift_down(heap, 0, *n);
    return max;
}

// CORRECT:
int extract_max(int *heap, int *n) {
    if (*n == 0) return -1; // or error code, or panic
    if (*n == 1) { (*n)--; return heap[0]; }
    int max = heap[0];
    heap[0] = heap[--(*n)];
    sift_down(heap, 0, *n);
    return max;
}
```

### Mistake 8: Build-Heap Starting from Wrong Index

```c
// WRONG:
for (int i = n-1; i >= 0; i--)  // starts from last node
    sift_down(heap, i, n);

// Still gives correct result, but wasteful!
// Leaf nodes (i >= n/2) have no children, sift_down is a no-op.

// CORRECT AND EFFICIENT:
for (int i = n/2 - 1; i >= 0; i--)  // start from last NON-LEAF
    sift_down(heap, i, n);

// Last non-leaf = floor((n-2)/2) = n/2 - 1 (0-indexed)
```

### Mistake 9: Heap as a Sorted Container

```
WRONG MENTAL MODEL:
  "If I just read the heap array from left to right, I get sorted order."

REALITY:
  Heap array is NOT sorted. Only the root is guaranteed to be max/min.

  Max-heap [10, 7, 9, 4, 3, 8, 6]:
  Reading left to right: 10, 7, 9, 4, 3, 8, 6  ← NOT sorted!

  To get sorted order: run heap sort, which takes O(n log n) extra work.
```

### Mistake 10: Integer Overflow in Index Calculation

```c
// POTENTIAL OVERFLOW on large heaps:
int left = 2 * i + 1;  // if i is near INT_MAX/2, overflow!

// SAFE VERSION:
// Ensure your index type can hold 2*n values.
// Use size_t or long long in C/C++.
// In practice for competitive programming, usually fine with int,
// but in production: be careful.
```

### Mistake 11: Confusing Heap the Data Structure with the Memory Heap

```
Two completely different things:

1. HEAP DATA STRUCTURE: The tree-like priority queue we discuss here.

2. HEAP MEMORY (OS/runtime): The region of memory used for dynamic
   allocation (malloc in C, Box<T> in Rust, new in Go).

malloc() allocates on the MEMORY heap, not the DATA STRUCTURE heap.
A heap data structure can itself be allocated on either the stack or
the memory heap.
```

### Mistake 12: Forgetting That Priority Queue Is Not FIFO

```
MISTAKE: Using a priority queue like a regular queue (FIFO).

REALITY:
  Regular queue: FIFO — first in, first out.
  Priority queue (heap): highest priority OUT first, regardless of insertion order.

  If you push [3, 1, 4, 1, 5, 9] into a max-heap priority queue
  and pop them all, you get: 9, 5, 4, 3, 1, 1 — NOT insertion order.
```

---

## 10. Advanced Heap Variants

### 10.1 Indexed Priority Queue

Adds a position map to enable O(log n) decrease-key without searching.

```
STRUCTURE:
  heap[]       — the heap array of (key, value) pairs
  pos_map[]    — pos_map[elem] = index of elem in heap array
  inv_map[]    — inv_map[index] = element at that index

INVARIANT: pos_map[inv_map[i]] == i   for all i

On every SWAP(i, j):
  pos_map[inv_map[i]] = j
  pos_map[inv_map[j]] = i
  swap(inv_map[i], inv_map[j])
  swap(heap[i], heap[j])

APPLICATION: Dijkstra's algorithm with decrease-key
  When dist[v] decreases:
    i = pos_map[v]
    heap[i].dist = new_dist
    sift_up(i)   // or sift_down, check both

VISUAL:
  Elements: A=10, B=5, C=8, D=3

  heap:    [D=3, B=5, C=8, A=10]  ← sorted by priority
  pos_map: [A→3, B→1, C→2, D→0]  ← where is each element?
  inv_map: [D, B, C, A]           ← who is at each index?

  To update priority of C from 8 to 1:
    i = pos_map[C] = 2
    heap[2].dist = 1
    sift_up(2) → C bubbles up past B and D
```

### 10.2 Segment Tree vs Heap

```
WHEN HEAP IS BETTER:
  - Priority queue operations (insert, extract-min/max)
  - Heap sort
  - Top-k elements
  - Streaming median

WHEN SEGMENT TREE IS BETTER:
  - Range min/max queries
  - Range sum queries
  - Point updates with range queries
  - Lazy propagation for range updates
```

### 10.3 Soft Heap (Kaplan & Tarjan)

```
Introduces "corruption" of elements to achieve O(1) amortized operations.
- Allows some elements to be corrupted (their key is increased)
- ε-fraction of elements can be corrupted at any time
- Used in optimal sorting algorithms and minimum spanning tree algorithms
- Achieves amortized O(log(1/ε)) per operation
```

### 10.4 Pairing Heap

```
Simple self-adjusting heap structure.
- Excellent practical performance despite complex amortized analysis
- O(1) merge, insert, find-min
- O(log n) amortized delete-min
- Often outperforms Fibonacci heap in practice

Structure: heap-ordered multiway tree
  push: create singleton tree, merge with root
  pop:  remove root, merge all children (pairing step)
```

---

## 11. Complexity Reference Card

```
┌─────────────────────────┬──────────────┬──────────────────────────┐
│ Operation               │ Binary Heap  │ Notes                    │
├─────────────────────────┼──────────────┼──────────────────────────┤
│ Build (heapify)         │ O(n)         │ Floyd's algorithm        │
│ Insert                  │ O(log n)     │ O(1) amortized for Fib   │
│ Find min/max (peek)     │ O(1)         │ Always guaranteed        │
│ Extract min/max         │ O(log n)     │ Swap+sift-down           │
│ Decrease Key            │ O(log n)     │ O(1) amortized Fib heap  │
│ Delete arbitrary        │ O(log n)*    │ *Need index (pos map)    │
│ Merge two heaps         │ O(n)         │ Rebuild from scratch     │
│ Search arbitrary        │ O(n)         │ No shortcut exists       │
│ Heap sort               │ O(n log n)   │ In-place, not stable     │
│ Space                   │ O(n)         │ No pointer overhead      │
├─────────────────────────┼──────────────┼──────────────────────────┤
│ FIBONACCI HEAP          │              │                          │
│ Insert                  │ O(1)         │ Amortized                │
│ Find min                │ O(1)         │                          │
│ Decrease Key            │ O(1)         │ Amortized                │
│ Delete                  │ O(log n)     │ Amortized                │
│ Merge                   │ O(1)         │ Just link root lists     │
├─────────────────────────┼──────────────┼──────────────────────────┤
│ BINOMIAL HEAP           │              │                          │
│ Insert                  │ O(log n)     │ O(1) amortized           │
│ Find min                │ O(log n)     │                          │
│ Merge                   │ O(log n)     │ Key advantage            │
│ Decrease Key            │ O(log n)     │                          │
└─────────────────────────┴──────────────┴──────────────────────────┘
```

---

## 12. Implementations

### 12.1 C Implementation

Complete, production-quality max-heap in pure C with all operations.

```c
/*
 * max_heap.c
 * Complete Max-Heap implementation in C
 * All operations: insert, extract_max, peek, build_heap,
 *                 decrease_key, increase_key, delete_at,
 *                 heap_sort, heap_size, is_empty
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* ─────────────────────────────────────────────
 *  STRUCTURES
 * ───────────────────────────────────────────── */

#define MAX_HEAP_CAPACITY 1024

typedef struct {
    int  *data;       /* the underlying array */
    int   size;       /* current number of elements */
    int   capacity;   /* maximum capacity */
} MaxHeap;

/* ─────────────────────────────────────────────
 *  CONSTRUCTION / DESTRUCTION
 * ───────────────────────────────────────────── */

MaxHeap *heap_create(int capacity) {
    MaxHeap *h = (MaxHeap *)malloc(sizeof(MaxHeap));
    if (!h) { perror("malloc"); exit(1); }
    h->data     = (int *)malloc(sizeof(int) * capacity);
    if (!h->data) { perror("malloc"); exit(1); }
    h->size     = 0;
    h->capacity = capacity;
    return h;
}

void heap_destroy(MaxHeap *h) {
    free(h->data);
    free(h);
}

/* ─────────────────────────────────────────────
 *  INDEX ARITHMETIC (0-indexed)
 * ───────────────────────────────────────────── */

static inline int parent(int i)      { return (i - 1) / 2; }
static inline int left_child(int i)  { return 2 * i + 1;   }
static inline int right_child(int i) { return 2 * i + 2;   }

static inline void swap(int *a, int *b) {
    int tmp = *a; *a = *b; *b = tmp;
}

/* ─────────────────────────────────────────────
 *  CORE OPERATIONS
 * ───────────────────────────────────────────── */

/*
 * sift_up: restore heap property upward from index i.
 * Called after: insert, increase_key.
 * Time: O(log n)
 */
static void sift_up(MaxHeap *h, int i) {
    while (i > 0) {
        int p = parent(i);
        if (h->data[i] > h->data[p]) {
            swap(&h->data[i], &h->data[p]);
            i = p;
        } else {
            break;  /* heap property restored */
        }
    }
}

/*
 * sift_down: restore heap property downward from index i.
 * Called after: extract_max, decrease_key, build_heap.
 * Time: O(log n)
 */
static void sift_down(MaxHeap *h, int i) {
    int n = h->size;
    while (1) {
        int largest = i;
        int l       = left_child(i);
        int r       = right_child(i);

        if (l < n && h->data[l] > h->data[largest])
            largest = l;
        if (r < n && h->data[r] > h->data[largest])
            largest = r;

        if (largest != i) {
            swap(&h->data[i], &h->data[largest]);
            i = largest;
        } else {
            break;  /* heap property satisfied */
        }
    }
}

/* ─────────────────────────────────────────────
 *  PUBLIC API
 * ───────────────────────────────────────────── */

int heap_is_empty(const MaxHeap *h) { return h->size == 0; }
int heap_size(const MaxHeap *h)     { return h->size;      }

/*
 * heap_peek: return max element without removing.
 * Time: O(1)
 */
int heap_peek(const MaxHeap *h) {
    assert(h->size > 0 && "peek on empty heap");
    return h->data[0];
}

/*
 * heap_insert: add new element.
 * Time: O(log n)
 */
void heap_insert(MaxHeap *h, int val) {
    assert(h->size < h->capacity && "heap overflow");
    h->data[h->size] = val;
    h->size++;
    sift_up(h, h->size - 1);
}

/*
 * heap_extract_max: remove and return the maximum element.
 * Time: O(log n)
 */
int heap_extract_max(MaxHeap *h) {
    assert(h->size > 0 && "extract from empty heap");

    int max_val      = h->data[0];
    h->data[0]       = h->data[h->size - 1];
    h->size--;

    if (h->size > 0)
        sift_down(h, 0);

    return max_val;
}

/*
 * heap_decrease_key: decrease value at index i to new_val.
 * new_val MUST be <= current value (otherwise use increase_key).
 * Time: O(log n)
 */
void heap_decrease_key(MaxHeap *h, int i, int new_val) {
    assert(i >= 0 && i < h->size);
    assert(new_val <= h->data[i] && "new_val must be <= current (use increase_key)");
    h->data[i] = new_val;
    sift_down(h, i);  /* decreased value may violate with children */
}

/*
 * heap_increase_key: increase value at index i to new_val.
 * new_val MUST be >= current value.
 * Time: O(log n)
 */
void heap_increase_key(MaxHeap *h, int i, int new_val) {
    assert(i >= 0 && i < h->size);
    assert(new_val >= h->data[i] && "new_val must be >= current (use decrease_key)");
    h->data[i] = new_val;
    sift_up(h, i);  /* increased value may violate with parent */
}

/*
 * heap_delete_at: delete element at index i.
 * Time: O(log n)
 */
void heap_delete_at(MaxHeap *h, int i) {
    assert(i >= 0 && i < h->size);

    /* Replace with last element */
    h->data[i] = h->data[h->size - 1];
    h->size--;

    if (i < h->size) {
        sift_up(h, i);    /* one of these will be a no-op */
        sift_down(h, i);
    }
}

/*
 * heap_build: build a max-heap from an existing array IN-PLACE.
 * Uses Floyd's O(n) algorithm.
 * arr[] is borrowed; the heap wraps it.
 * Time: O(n)
 */
MaxHeap *heap_build(int *arr, int n, int capacity) {
    MaxHeap *h = (MaxHeap *)malloc(sizeof(MaxHeap));
    if (!h) { perror("malloc"); exit(1); }
    h->data     = arr;
    h->size     = n;
    h->capacity = capacity;

    /* Start from last non-leaf, go to root */
    for (int i = n / 2 - 1; i >= 0; i--)
        sift_down(h, i);

    return h;
}

/*
 * heap_sort_inplace: sort array ascending using max-heap.
 * MODIFIES the array in-place.
 * Time: O(n log n), Space: O(1)
 */
void heap_sort_inplace(int *arr, int n) {
    /* Step 1: Build max-heap */
    MaxHeap tmp = { .data = arr, .size = n, .capacity = n };
    for (int i = n / 2 - 1; i >= 0; i--)
        sift_down(&tmp, i);

    /* Step 2: Repeatedly extract max to end */
    for (int end = n - 1; end > 0; end--) {
        swap(&arr[0], &arr[end]);
        tmp.size = end;
        sift_down(&tmp, 0);
    }
}

/* ─────────────────────────────────────────────
 *  VALIDATION (for debugging)
 * ───────────────────────────────────────────── */

int heap_is_valid(const MaxHeap *h) {
    for (int i = 1; i < h->size; i++) {
        int p = parent(i);
        if (h->data[p] < h->data[i]) {
            fprintf(stderr, "HEAP VIOLATION: parent[%d]=%d < child[%d]=%d\n",
                    p, h->data[p], i, h->data[i]);
            return 0;
        }
    }
    return 1;
}

void heap_print(const MaxHeap *h) {
    printf("Heap (size=%d): [", h->size);
    for (int i = 0; i < h->size; i++) {
        printf("%d", h->data[i]);
        if (i < h->size - 1) printf(", ");
    }
    printf("]\n");
}

/* ─────────────────────────────────────────────
 *  DEMONSTRATION
 * ───────────────────────────────────────────── */

int main(void) {
    printf("=== Max-Heap Demo ===\n\n");

    /* --- Test Insert --- */
    MaxHeap *h = heap_create(64);
    int values[] = {3, 1, 6, 5, 2, 4};
    printf("Inserting: ");
    for (int i = 0; i < 6; i++) {
        printf("%d ", values[i]);
        heap_insert(h, values[i]);
    }
    printf("\n");
    heap_print(h);
    assert(heap_is_valid(h));

    /* --- Test Peek --- */
    printf("Peek (max): %d\n", heap_peek(h));

    /* --- Test Extract Max --- */
    printf("Extracting all: ");
    while (!heap_is_empty(h)) {
        printf("%d ", heap_extract_max(h));
    }
    printf("\n");

    /* --- Test Build Heap --- */
    int arr[] = {3, 1, 6, 5, 2, 4, 9, 7, 8};
    int n = sizeof(arr) / sizeof(arr[0]);
    printf("\nBuild heap from [3,1,6,5,2,4,9,7,8]:\n");
    MaxHeap *h2 = heap_build(arr, n, n);
    heap_print(h2);
    assert(heap_is_valid(h2));
    free(h2);  /* don't free arr, it's on stack */

    /* --- Test Heap Sort --- */
    int sort_arr[] = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    int sort_n = sizeof(sort_arr) / sizeof(sort_arr[0]);
    printf("\nHeap Sort [5,3,8,1,9,2,7,4,6]:\n");
    heap_sort_inplace(sort_arr, sort_n);
    printf("Sorted: [");
    for (int i = 0; i < sort_n; i++) {
        printf("%d", sort_arr[i]);
        if (i < sort_n - 1) printf(", ");
    }
    printf("]\n");

    /* --- Test Decrease/Increase Key --- */
    MaxHeap *h3 = heap_create(64);
    for (int i = 0; i < 6; i++) heap_insert(h3, values[i]);
    printf("\nBefore decrease_key(1, 0): ");
    heap_print(h3);
    heap_decrease_key(h3, 1, 0);
    printf("After:                     ");
    heap_print(h3);
    assert(heap_is_valid(h3));

    heap_destroy(h);
    heap_destroy(h3);

    printf("\nAll assertions passed.\n");
    return 0;
}
```

---

### 12.2 Rust Implementation

```rust
//! max_heap.rs
//! Complete, idiomatic Rust Max-Heap implementation
//! Uses generics + Ord trait for any comparable type.
//! Demonstrates: insert, extract_max, peek, build_heap,
//!               decrease_key, increase_key, delete_at, heap_sort.

use std::fmt::Debug;

/// A max-heap where T must implement Ord (total ordering).
/// Internally stored as a Vec<T> for cache-friendly access.
#[derive(Debug, Clone)]
pub struct MaxHeap<T: Ord> {
    data: Vec<T>,
}

impl<T: Ord + Debug> MaxHeap<T> {
    // ─────────────────────────────────────────────
    //  CONSTRUCTION
    // ─────────────────────────────────────────────

    /// Create an empty heap.
    pub fn new() -> Self {
        MaxHeap { data: Vec::new() }
    }

    /// Create a heap with pre-allocated capacity.
    pub fn with_capacity(cap: usize) -> Self {
        MaxHeap { data: Vec::with_capacity(cap) }
    }

    /// Build a max-heap from an existing Vec using Floyd's O(n) algorithm.
    pub fn from_vec(v: Vec<T>) -> Self {
        let mut heap = MaxHeap { data: v };
        let n = heap.data.len();
        if n > 1 {
            // Start from last non-leaf: (n/2 - 1) down to 0
            for i in (0..=(n / 2).saturating_sub(1)).rev() {
                heap.sift_down(i);
            }
        }
        heap
    }

    // ─────────────────────────────────────────────
    //  INDEX ARITHMETIC (0-indexed)
    // ─────────────────────────────────────────────

    #[inline]
    fn parent(i: usize) -> usize {
        // Safe: only called when i > 0
        (i - 1) / 2
    }

    #[inline]
    fn left(i: usize) -> usize {
        2 * i + 1
    }

    #[inline]
    fn right(i: usize) -> usize {
        2 * i + 2
    }

    // ─────────────────────────────────────────────
    //  CORE INTERNAL OPERATIONS
    // ─────────────────────────────────────────────

    /// Sift element at index i UP toward the root.
    /// Called after insert or increase_key.
    fn sift_up(&mut self, mut i: usize) {
        while i > 0 {
            let p = Self::parent(i);
            if self.data[i] > self.data[p] {
                self.data.swap(i, p);
                i = p;
            } else {
                break;
            }
        }
    }

    /// Sift element at index i DOWN away from root.
    /// Called after extract_max, decrease_key, or build_heap.
    fn sift_down(&mut self, mut i: usize) {
        let n = self.data.len();
        loop {
            let mut largest = i;
            let l = Self::left(i);
            let r = Self::right(i);

            if l < n && self.data[l] > self.data[largest] {
                largest = l;
            }
            if r < n && self.data[r] > self.data[largest] {
                largest = r;
            }

            if largest != i {
                self.data.swap(i, largest);
                i = largest;
            } else {
                break;
            }
        }
    }

    // ─────────────────────────────────────────────
    //  PUBLIC API
    // ─────────────────────────────────────────────

    /// Return number of elements.
    pub fn len(&self) -> usize {
        self.data.len()
    }

    /// Return true if heap is empty.
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// Peek at maximum element without removing.
    /// Returns None if heap is empty.
    /// Time: O(1)
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }

    /// Insert a new element and maintain heap property.
    /// Time: O(log n)
    pub fn push(&mut self, val: T) {
        self.data.push(val);
        let last = self.data.len() - 1;
        self.sift_up(last);
    }

    /// Remove and return the maximum element.
    /// Returns None if heap is empty.
    /// Time: O(log n)
    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() {
            return None;
        }
        let n = self.data.len();
        self.data.swap(0, n - 1);          // move max to end
        let max_val = self.data.pop();     // remove from end
        if !self.data.is_empty() {
            self.sift_down(0);
        }
        max_val
    }

    /// Replace root with a new value and restore heap property.
    /// More efficient than pop() + push() when you know new value.
    /// Time: O(log n)
    pub fn replace_root(&mut self, val: T) -> Option<T> {
        if self.data.is_empty() {
            self.data.push(val);
            return None;
        }
        // Swap root with new value, then fix heap
        let old = std::mem::replace(&mut self.data[0], val);
        self.sift_down(0);
        Some(old)
    }

    /// Decrease the value at index i (max-heap: value must go down or equal).
    /// Panics if new_val > current value (use increase_key_at instead).
    /// Time: O(log n)
    pub fn decrease_key_at(&mut self, i: usize, new_val: T) {
        assert!(i < self.data.len(), "index out of bounds");
        assert!(new_val <= self.data[i], "decrease_key: new_val must be <= current");
        self.data[i] = new_val;
        self.sift_down(i);  // smaller value may violate with children
    }

    /// Increase the value at index i.
    /// Panics if new_val < current value.
    /// Time: O(log n)
    pub fn increase_key_at(&mut self, i: usize, new_val: T) {
        assert!(i < self.data.len(), "index out of bounds");
        assert!(new_val >= self.data[i], "increase_key: new_val must be >= current");
        self.data[i] = new_val;
        self.sift_up(i);   // larger value may violate with parent
    }

    /// Delete the element at index i.
    /// Time: O(log n)
    pub fn delete_at(&mut self, i: usize) {
        assert!(i < self.data.len(), "index out of bounds");
        let n = self.data.len();

        if i == n - 1 {
            // Deleting last element, no fix-up needed
            self.data.pop();
            return;
        }

        self.data.swap(i, n - 1);
        self.data.pop();

        if i < self.data.len() {
            // Only one will actually do work, other is no-op
            self.sift_up(i);
            self.sift_down(i);
        }
    }

    /// Sort the heap's data in ascending order.
    /// Consumes the heap and returns sorted Vec.
    /// Time: O(n log n)
    pub fn into_sorted_vec(mut self) -> Vec<T> {
        let n = self.data.len();
        // Repeatedly swap root (max) with last unsorted element
        for end in (1..n).rev() {
            self.data.swap(0, end);
            // Temporarily shrink to 'end' for sift_down
            let saved = self.data.split_off(end);
            self.sift_down(0);
            self.data.extend(saved);
        }
        self.data
    }

    /// Validate that the heap property holds for all nodes.
    /// For debugging and testing only.
    pub fn is_valid(&self) -> bool {
        let n = self.data.len();
        for i in 1..n {
            let p = Self::parent(i);
            if self.data[p] < self.data[i] {
                eprintln!(
                    "HEAP VIOLATION: parent[{}]={:?} < child[{}]={:?}",
                    p, self.data[p], i, self.data[i]
                );
                return false;
            }
        }
        true
    }
}

// ─────────────────────────────────────────────
//  MIN-HEAP using std::cmp::Reverse
//  This is the IDIOMATIC Rust pattern.
// ─────────────────────────────────────────────

use std::cmp::Reverse;
use std::collections::BinaryHeap;

/// Demonstrates min-heap using BinaryHeap<Reverse<T>>
fn min_heap_example() {
    // BinaryHeap is max-heap by default.
    // Wrap values in Reverse to invert ordering.
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();

    for val in [5, 1, 3, 2, 4] {
        min_heap.push(Reverse(val));
    }

    println!("Min-heap extraction order:");
    while let Some(Reverse(val)) = min_heap.pop() {
        print!("{} ", val);  // prints: 1 2 3 4 5
    }
    println!();
}

// ─────────────────────────────────────────────
//  IN-PLACE HEAP SORT (pure function, no struct)
// ─────────────────────────────────────────────

/// Sort slice in ascending order using heap sort.
/// In-place, O(n log n), O(1) extra space.
pub fn heap_sort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    if n <= 1 { return; }

    // Step 1: Build max-heap (Floyd's algorithm)
    for i in (0..n / 2).rev() {
        sift_down_slice(arr, i, n);
    }

    // Step 2: Extract max to end, shrink heap boundary
    for end in (1..n).rev() {
        arr.swap(0, end);
        sift_down_slice(arr, 0, end);
    }
}

fn sift_down_slice<T: Ord>(arr: &mut [T], mut i: usize, n: usize) {
    loop {
        let mut largest = i;
        let l = 2 * i + 1;
        let r = 2 * i + 2;

        if l < n && arr[l] > arr[largest] { largest = l; }
        if r < n && arr[r] > arr[largest] { largest = r; }

        if largest != i {
            arr.swap(i, largest);
            i = largest;
        } else {
            break;
        }
    }
}

// ─────────────────────────────────────────────
//  DEMONSTRATION
// ─────────────────────────────────────────────

fn main() {
    println!("=== Max-Heap Demo (Rust) ===\n");

    // --- Build from Vec ---
    let v = vec![3, 1, 6, 5, 2, 4, 9, 7, 8];
    println!("Building heap from {:?}", v);
    let mut heap = MaxHeap::from_vec(v);
    assert!(heap.is_valid());
    println!("Heap valid: {}", heap.is_valid());
    println!("Peek (max): {:?}", heap.peek());

    // --- Push ---
    heap.push(100);
    heap.push(50);
    println!("After pushing 100 and 50, peek: {:?}", heap.peek());
    assert!(heap.is_valid());

    // --- Pop all ---
    print!("Extracting: ");
    let mut result = Vec::new();
    while let Some(v) = heap.pop() {
        result.push(v);
        print!("{} ", result.last().unwrap());
    }
    println!();
    // Verify descending order
    for i in 0..result.len()-1 {
        assert!(result[i] >= result[i+1], "pop order violated!");
    }

    // --- Heap Sort ---
    let mut arr = vec![5, 3, 8, 1, 9, 2, 7, 4, 6];
    println!("\nHeap sorting {:?}", arr);
    heap_sort(&mut arr);
    println!("Sorted: {:?}", arr);
    assert!(arr.windows(2).all(|w| w[0] <= w[1]));

    // --- Min-Heap using Reverse ---
    println!("\n--- Min-Heap via Reverse ---");
    min_heap_example();

    // --- Standard Library BinaryHeap ---
    println!("\n--- std::collections::BinaryHeap ---");
    let mut std_heap: BinaryHeap<i32> = BinaryHeap::new();
    for x in [10, 3, 7, 1, 5] {
        std_heap.push(x);
    }
    println!("std BinaryHeap peek: {:?}", std_heap.peek());

    // into_sorted_vec returns ascending order
    let sorted = std_heap.into_sorted_vec();
    println!("into_sorted_vec: {:?}", sorted);

    println!("\nAll tests passed!");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_and_extract() {
        let mut h: MaxHeap<i32> = MaxHeap::new();
        for x in [5, 3, 8, 1, 9, 2, 7, 4, 6] {
            h.push(x);
        }
        let mut prev = i32::MAX;
        while let Some(v) = h.pop() {
            assert!(v <= prev, "heap order violated");
            prev = v;
        }
    }

    #[test]
    fn test_build_heap_validity() {
        let v = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        let h = MaxHeap::from_vec(v);
        assert!(h.is_valid());
        assert_eq!(h.peek(), Some(&10));
    }

    #[test]
    fn test_heap_sort() {
        let mut arr = vec![5, 3, 8, 1, 9, 2, 7, 4, 6];
        heap_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 4, 5, 6, 7, 8, 9]);
    }

    #[test]
    fn test_decrease_key() {
        let mut h = MaxHeap::from_vec(vec![10, 8, 9, 5, 7, 6, 4]);
        h.decrease_key_at(0, 1); // root 10 → 1
        assert!(h.is_valid());
        assert_ne!(h.peek(), Some(&10));
    }

    #[test]
    fn test_delete_at() {
        let mut h = MaxHeap::from_vec(vec![10, 8, 9, 5, 7, 6, 4]);
        let original_size = h.len();
        h.delete_at(2); // delete element at index 2
        assert_eq!(h.len(), original_size - 1);
        assert!(h.is_valid());
    }
}
```

---

### 12.3 Go Implementation

```go
// max_heap.go
// Complete Max-Heap implementation in Go
// Uses Go generics (1.18+) with constraints.Ordered
// Implements: push, pop, peek, build, decrease_key,
//             increase_key, delete_at, heap_sort, validation

package heap

import (
	"cmp"
	"fmt"
	"strings"
)

// ─────────────────────────────────────────────
//  STRUCTURES
// ─────────────────────────────────────────────

// MaxHeap is a generic max-heap for any ordered type.
// T must satisfy cmp.Ordered (int, float64, string, etc.)
type MaxHeap[T cmp.Ordered] struct {
	data []T
}

// ─────────────────────────────────────────────
//  CONSTRUCTION
// ─────────────────────────────────────────────

// New creates an empty MaxHeap.
func New[T cmp.Ordered]() *MaxHeap[T] {
	return &MaxHeap[T]{data: make([]T, 0)}
}

// WithCapacity creates an empty MaxHeap with pre-allocated capacity.
func WithCapacity[T cmp.Ordered](cap int) *MaxHeap[T] {
	return &MaxHeap[T]{data: make([]T, 0, cap)}
}

// FromSlice builds a max-heap from an existing slice using Floyd's O(n) algorithm.
// NOTE: Takes ownership; modifies the slice in-place.
func FromSlice[T cmp.Ordered](data []T) *MaxHeap[T] {
	h := &MaxHeap[T]{data: data}
	n := len(h.data)
	// Start from last non-leaf, go to root
	for i := n/2 - 1; i >= 0; i-- {
		h.siftDown(i)
	}
	return h
}

// ─────────────────────────────────────────────
//  INDEX ARITHMETIC (0-indexed)
// ─────────────────────────────────────────────

func parent(i int) int { return (i - 1) / 2 }
func left(i int) int   { return 2*i + 1 }
func right(i int) int  { return 2*i + 2 }

// ─────────────────────────────────────────────
//  CORE INTERNAL OPERATIONS
// ─────────────────────────────────────────────

// siftUp restores heap property upward from index i.
// Called after Push or IncreaseKeyAt.
func (h *MaxHeap[T]) siftUp(i int) {
	for i > 0 {
		p := parent(i)
		if h.data[i] > h.data[p] {
			h.data[i], h.data[p] = h.data[p], h.data[i]
			i = p
		} else {
			break
		}
	}
}

// siftDown restores heap property downward from index i.
// Called after Pop, DecreaseKeyAt, or FromSlice.
func (h *MaxHeap[T]) siftDown(i int) {
	n := len(h.data)
	for {
		largest := i
		l := left(i)
		r := right(i)

		if l < n && h.data[l] > h.data[largest] {
			largest = l
		}
		if r < n && h.data[r] > h.data[largest] {
			largest = r
		}

		if largest != i {
			h.data[i], h.data[largest] = h.data[largest], h.data[i]
			i = largest
		} else {
			break
		}
	}
}

// ─────────────────────────────────────────────
//  PUBLIC API
// ─────────────────────────────────────────────

// Len returns the number of elements in the heap.
func (h *MaxHeap[T]) Len() int { return len(h.data) }

// IsEmpty returns true if the heap has no elements.
func (h *MaxHeap[T]) IsEmpty() bool { return len(h.data) == 0 }

// Peek returns the maximum element without removing it.
// Returns the zero value and false if heap is empty.
// Time: O(1)
func (h *MaxHeap[T]) Peek() (T, bool) {
	if h.IsEmpty() {
		var zero T
		return zero, false
	}
	return h.data[0], true
}

// Push adds an element to the heap and maintains heap property.
// Time: O(log n)
func (h *MaxHeap[T]) Push(val T) {
	h.data = append(h.data, val)
	h.siftUp(len(h.data) - 1)
}

// Pop removes and returns the maximum element.
// Returns the zero value and false if heap is empty.
// Time: O(log n)
func (h *MaxHeap[T]) Pop() (T, bool) {
	if h.IsEmpty() {
		var zero T
		return zero, false
	}
	n := len(h.data)
	maxVal := h.data[0]

	// Move last element to root
	h.data[0] = h.data[n-1]
	h.data = h.data[:n-1]

	if len(h.data) > 0 {
		h.siftDown(0)
	}
	return maxVal, true
}

// ReplaceRoot replaces the root with a new value without two separate operations.
// More efficient than Pop() + Push() for bounded heaps.
// Time: O(log n)
func (h *MaxHeap[T]) ReplaceRoot(val T) (T, bool) {
	if h.IsEmpty() {
		h.Push(val)
		var zero T
		return zero, false
	}
	old := h.data[0]
	h.data[0] = val
	h.siftDown(0)
	return old, true
}

// DecreaseKeyAt decreases the value at index i.
// new_val must be <= current value.
// Time: O(log n)
func (h *MaxHeap[T]) DecreaseKeyAt(i int, newVal T) error {
	if i < 0 || i >= len(h.data) {
		return fmt.Errorf("index %d out of bounds [0, %d)", i, len(h.data))
	}
	if newVal > h.data[i] {
		return fmt.Errorf("DecreaseKeyAt: newVal must be <= current value")
	}
	h.data[i] = newVal
	h.siftDown(i) // decreased value may violate with children
	return nil
}

// IncreaseKeyAt increases the value at index i.
// new_val must be >= current value.
// Time: O(log n)
func (h *MaxHeap[T]) IncreaseKeyAt(i int, newVal T) error {
	if i < 0 || i >= len(h.data) {
		return fmt.Errorf("index %d out of bounds [0, %d)", i, len(h.data))
	}
	if newVal < h.data[i] {
		return fmt.Errorf("IncreaseKeyAt: newVal must be >= current value")
	}
	h.data[i] = newVal
	h.siftUp(i) // increased value may violate with parent
	return nil
}

// DeleteAt removes the element at index i.
// Time: O(log n)
func (h *MaxHeap[T]) DeleteAt(i int) error {
	n := len(h.data)
	if i < 0 || i >= n {
		return fmt.Errorf("index %d out of bounds [0, %d)", i, n)
	}

	// If deleting last element, just shrink
	if i == n-1 {
		h.data = h.data[:n-1]
		return nil
	}

	// Replace with last, shrink, then fix heap property
	h.data[i] = h.data[n-1]
	h.data = h.data[:n-1]

	h.siftUp(i)   // one will be no-op
	h.siftDown(i) // the other restores property
	return nil
}

// IsValid checks the heap property for all nodes.
// For debugging only. Time: O(n)
func (h *MaxHeap[T]) IsValid() bool {
	n := len(h.data)
	for i := 1; i < n; i++ {
		p := parent(i)
		if h.data[p] < h.data[i] {
			fmt.Printf("HEAP VIOLATION: parent[%d]=%v < child[%d]=%v\n",
				p, h.data[p], i, h.data[i])
			return false
		}
	}
	return true
}

// String returns a human-readable representation of the heap.
func (h *MaxHeap[T]) String() string {
	parts := make([]string, len(h.data))
	for i, v := range h.data {
		parts[i] = fmt.Sprintf("%v", v)
	}
	return "MaxHeap[" + strings.Join(parts, ", ") + "]"
}

// ─────────────────────────────────────────────
//  HEAP SORT (standalone function, no struct needed)
// ─────────────────────────────────────────────

// HeapSort sorts a slice in ascending order using max-heap.
// In-place, O(n log n) time, O(1) extra space.
func HeapSort[T cmp.Ordered](arr []T) {
	n := len(arr)
	if n <= 1 {
		return
	}

	// Step 1: Build max-heap (Floyd's O(n) algorithm)
	for i := n/2 - 1; i >= 0; i-- {
		siftDownSlice(arr, i, n)
	}

	// Step 2: Extract max to end, restore heap on remaining
	for end := n - 1; end > 0; end-- {
		arr[0], arr[end] = arr[end], arr[0]
		siftDownSlice(arr, 0, end)
	}
}

// siftDownSlice is a helper for HeapSort (operates on a slice segment).
func siftDownSlice[T cmp.Ordered](arr []T, i, n int) {
	for {
		largest := i
		l := 2*i + 1
		r := 2*i + 2

		if l < n && arr[l] > arr[largest] {
			largest = l
		}
		if r < n && arr[r] > arr[largest] {
			largest = r
		}

		if largest != i {
			arr[i], arr[largest] = arr[largest], arr[i]
			i = largest
		} else {
			break
		}
	}
}

// ─────────────────────────────────────────────
//  STANDARD LIBRARY HEAP (container/heap interface)
// ─────────────────────────────────────────────

// Go's standard library provides container/heap which requires:
//   Len() int
//   Less(i, j int) bool
//   Swap(i, j int)
//   Push(x any)
//   Pop() any
//
// Example: implementing a min-heap priority queue using container/heap

// IntMinHeap implements heap.Interface for a min-heap of ints.
// (This is the idiomatic Go pattern using container/heap)
type IntMinHeap []int

func (h IntMinHeap) Len() int           { return len(h) }
func (h IntMinHeap) Less(i, j int) bool { return h[i] < h[j] } // min-heap: smaller = higher priority
func (h IntMinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *IntMinHeap) Push(x any) {
	*h = append(*h, x.(int))
}

func (h *IntMinHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

// ─────────────────────────────────────────────
//  DEMONSTRATION (main package)
// ─────────────────────────────────────────────

// NOTE: In a real project, put main in package main.
// This demonstrates usage patterns.

func DemoMaxHeap() {
	fmt.Println("=== Max-Heap Demo (Go) ===\n")

	// --- Build from slice ---
	data := []int{3, 1, 6, 5, 2, 4, 9, 7, 8}
	fmt.Printf("Building heap from %v\n", data)
	h := FromSlice(data)
	fmt.Printf("Result: %v\n", h)
	fmt.Printf("Valid: %v\n", h.IsValid())

	// --- Push ---
	h.Push(100)
	h.Push(50)
	max, _ := h.Peek()
	fmt.Printf("\nAfter pushing 100 and 50, peek: %v\n", max)

	// --- Pop all in order ---
	fmt.Print("Extracting: ")
	prev := int(^uint(0) >> 1) // MaxInt
	for !h.IsEmpty() {
		v, _ := h.Pop()
		fmt.Printf("%v ", v)
		if v > prev {
			panic("heap order violated!")
		}
		prev = v
	}
	fmt.Println()

	// --- Heap Sort ---
	arr := []int{5, 3, 8, 1, 9, 2, 7, 4, 6}
	fmt.Printf("\nHeap sorting %v\n", arr)
	HeapSort(arr)
	fmt.Printf("Sorted: %v\n", arr)

	// --- DecreaseKeyAt ---
	h2 := FromSlice([]int{10, 8, 9, 5, 7, 6, 4})
	fmt.Printf("\nBefore DecreaseKeyAt(0, 1): %v\n", h2)
	if err := h2.DecreaseKeyAt(0, 1); err != nil {
		fmt.Println("Error:", err)
	}
	fmt.Printf("After: %v, valid: %v\n", h2, h2.IsValid())

	// --- DeleteAt ---
	h3 := FromSlice([]int{10, 8, 9, 5, 7, 6, 4})
	fmt.Printf("\nBefore DeleteAt(2): %v\n", h3)
	h3.DeleteAt(2)
	fmt.Printf("After: %v, valid: %v\n", h3, h3.IsValid())

	// --- String heap ---
	sh := New[string]()
	for _, s := range []string{"banana", "apple", "cherry", "date"} {
		sh.Push(s)
	}
	fmt.Printf("\nString max-heap peek: ")
	if v, ok := sh.Peek(); ok {
		fmt.Printf("%v\n", v) // "date" (lexicographically largest)
	}
}
```

---

## 13. Mental Models for Heap Intuition

### Mental Model 1: The Tournament Tree

```
Think of a max-heap as a tournament.
Every node won against its children.
The root is the overall champion.

When we remove the champion (extract max):
  - The runner-up (one of root's children) must win a new tournament.
  - We bring in a wildcard (last element) and let it compete.
  - Sift-down = the wildcard fighting its way to the correct position.

When we add a new player (insert):
  - Newcomer enters at the bottom (last position).
  - Sift-up = the newcomer beating stronger opponents on the way up.
```

### Mental Model 2: The Bubbling Liquid

```
MAX-HEAP: Heavy elements (large values) float UP, light elements sink DOWN.

INSERT: New element enters at bottom.
  If it's heavy (large), it bubbles UP past lighter elements.

EXTRACT: Remove the heaviest (top).
  Fill the hole with bottom element.
  If the filler is light, it sinks DOWN to its correct level.

SIFT-UP:   O(log n) — bubble rises
SIFT-DOWN: O(log n) — bubble sinks
```

### Mental Model 3: Invariant-Based Thinking

```
A heap has ONE invariant: parent ≥ all descendants (max-heap).

Every operation must:
1. Perform its task (possibly breaking the invariant temporarily)
2. RESTORE the invariant

This is a powerful mental model for designing algorithms:
  Step 1: What is the invariant?
  Step 2: What operation might break it?
  Step 3: How do I restore it?

INSERT:       Breaks invariant (new element may be larger than parent)
              → Restore with sift-up (compare upward, swap if needed)

EXTRACT MAX:  Breaks invariant (hole at root filled with potentially small value)
              → Restore with sift-down (compare downward, swap if needed)

DECREASE KEY: Breaks invariant (smaller value may violate with children)
              → Restore with sift-down

INCREASE KEY: Breaks invariant (larger value may violate with parent)
              → Restore with sift-up
```

### Mental Model 4: The Lazy Sorter

```
A heap is a LAZY SORTER.
It doesn't bother sorting everything.
It only guarantees: "I always know who's BEST."

When you need the best element: O(1)
When you've used the best and need the NEXT best: O(log n) — now it sorts just enough

This "lazy evaluation" is why heaps are ideal for:
  - Priority queues (always serve highest priority first)
  - Top-k algorithms (only sort until we have k elements)
  - Event-driven simulation (next event = smallest timestamp)
  - Dijkstra's algorithm (next node = minimum distance)
```

### Mental Model 5: Levels as "Certainty Zones"

```
MAX-HEAP CERTAINTY:

Level 0 (root):     100% certain it's the maximum.
Level 1:            Known to be ≥ their respective subtrees.
                    NOT known relative to each other.
Level 2:            Known to be ≥ their respective subtrees.
                    NOT known relative to Level 1 of OTHER subtrees.
...
Leaf Level:         Only know they're the smallest in their own path to root.

UNCERTAINTY INCREASES as you go DEEPER or ACROSS.

This explains why:
  - Peek = O(1): root has 100% certainty
  - Search = O(n): deep/cross nodes have zero inter-subtree certainty
```

---

### Cognitive Principles for Mastery

```
DELIBERATE PRACTICE:
  Don't just code heap operations. CODE and then BREAK them deliberately.
  Introduce off-by-one errors, observe the chaos, fix them back.
  This "error-injection" accelerates deep understanding.

CHUNKING:
  Master these "chunks" individually before combining:
  Chunk 1: Index arithmetic (parent, left, right) — internalize to reflex
  Chunk 2: Sift-up pattern
  Chunk 3: Sift-down pattern
  Chunk 4: Build-heap = apply sift-down to all non-leaves
  Chunk 5: Every operation = (do work) + (restore invariant)

META-LEARNING:
  After implementing, ask:
  "Can I derive THIS operation from first principles without notes?"
  If yes → you own it. If no → implement again without looking.

FLOW STATE:
  Heap problems in contests require INSTANT recognition of:
  - "Top-k → min-heap of size k"
  - "Priority order → heap-based priority queue"
  - "Always need current min/max → heap"
  Practice these pattern triggers until they're reflexive.
```

---

## 14. Deliberate Practice Problems

Work through these in order. Each level unlocks a new capability.

```
LEVEL 1 — FOUNDATION:
  P1: Implement max-heap from scratch (no library). All operations.
  P2: Convert max-heap to min-heap by negating comparison.
  P3: Validate a given array is a valid max-heap.
  P4: Find all ancestors of element at index i.

LEVEL 2 — CLASSIC APPLICATIONS:
  P5: Kth Largest Element in an Array (LeetCode 215)
  P6: Merge K Sorted Lists using min-heap (LeetCode 23)
  P7: Find Median from Data Stream (LeetCode 295) — two-heap technique
  P8: Task Scheduler (LeetCode 621)

LEVEL 3 — ADVANCED PATTERNS:
  P9:  Top K Frequent Elements (LeetCode 347)
  P10: Sliding Window Maximum (LeetCode 239) — monotonic deque vs heap
  P11: Dijkstra's Shortest Path with indexed priority queue
  P12: Reorganize String (LeetCode 767)

LEVEL 4 — DEEP MASTERY:
  P13: Implement Heap Sort without library (prove O(n) build, O(n log n) sort)
  P14: Implement an indexed priority queue for Dijkstra's
  P15: Design Twitter (LeetCode 355) using heap for top 10 tweets
  P16: The Skyline Problem (LeetCode 218) — complex heap usage

TWO-HEAP TECHNIQUE (for median finding):
  Maintain TWO heaps:
  - max_heap: stores the lower half of numbers
  - min_heap: stores the upper half of numbers

  INVARIANT:
    max_heap.size() == min_heap.size()      (even count)
    OR
    max_heap.size() == min_heap.size() + 1  (odd count)
    AND
    max_heap.top() <= min_heap.top()        (ordering between halves)

  Median = max_heap.top()                  (odd count)
         = (max_heap.top() + min_heap.top()) / 2  (even count)

  This is one of the most elegant heap tricks in competitive programming.
```

---

## Summary — The Expert's Mental Checklist

When you encounter a problem, ask these questions in order:

```
┌─────────────────────────────────────────────────────────────────┐
│  HEAP DECISION FRAMEWORK                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Do I repeatedly need the min or max of a dynamic set?        │
│     YES → Use a heap (priority queue)                            │
│                                                                  │
│  2. Do I need the TOP K elements from a stream?                  │
│     YES → Min-heap of size k                                     │
│                                                                  │
│  3. Do I need to efficiently merge multiple sorted sequences?    │
│     YES → Min-heap with (value, sequence_index) pairs           │
│                                                                  │
│  4. Do I need fast decrease-key (Dijkstra, Prim)?                │
│     YES → Indexed priority queue (heap + position map)           │
│                                                                  │
│  5. Do I need the median dynamically?                            │
│     YES → Two-heap technique                                     │
│                                                                  │
│  6. Do I need search, range queries, predecessor/successor?      │
│     NO → Heap cannot help. Use BST, segment tree, etc.           │
│                                                                  │
│  7. Do I need to sort completely?                                 │
│     MAYBE → Heap sort is in-place O(n log n) but cache-unfriendly│
│             Prefer quicksort for cache performance               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*A heap is not about what it CAN do — it is about what it is OPTIMIZED to do. The master understands both sides of that coin.*

*Practice until the index arithmetic feels like arithmetic itself — natural, automatic, invisible. That's when pattern recognition becomes intuition.*
