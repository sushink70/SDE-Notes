# The Complete Mental Model: Problem Decomposition, DSA, Linux Kernel, and Rust/C Interop

> A comprehensive, in-depth reference for building the right mental framework to think, decompose, code, and reason efficiently — from abstract problem solving down to kernel-level C and systems Rust.

---

## Table of Contents

1. [The Mental Model for Problem Solving](#1-the-mental-model-for-problem-solving)
2. [Divide and Conquer — Deep Mechanics](#2-divide-and-conquer--deep-mechanics)
3. [Problem Decomposition Methodology](#3-problem-decomposition-methodology)
4. [Solving Sub-Problems Efficiently](#4-solving-sub-problems-efficiently)
5. [Merging Solutions Properly](#5-merging-solutions-properly)
6. [Decision Making in Algorithm Design](#6-decision-making-in-algorithm-design)
7. [Data Structures — Deep Internals](#7-data-structures--deep-internals)
8. [Algorithm Patterns and When to Use Them](#8-algorithm-patterns-and-when-to-use-them)
9. [Complexity Analysis — The Real Mental Model](#9-complexity-analysis--the-real-mental-model)
10. [Linux Kernel Programming — The Complete Model](#10-linux-kernel-programming--the-complete-model)
11. [Kernel Data Structures and Mechanisms](#11-kernel-data-structures-and-mechanisms)
12. [Memory Management in the Kernel](#12-memory-management-in-the-kernel)
13. [Synchronization and Concurrency in the Kernel](#13-synchronization-and-concurrency-in-the-kernel)
14. [Kernel Subsystems Architecture](#14-kernel-subsystems-architecture)
15. [C Implementation Patterns for Systems Programming](#15-c-implementation-patterns-for-systems-programming)
16. [Rust in Systems Programming](#16-rust-in-systems-programming)
17. [C and Rust Interoperability](#17-c-and-rust-interoperability)
18. [Rust in the Linux Kernel](#18-rust-in-the-linux-kernel)
19. [Debugging Mental Models](#19-debugging-mental-models)
20. [Performance Mental Models](#20-performance-mental-models)

---

## 1. The Mental Model for Problem Solving

### What Is a Mental Model?

A mental model is an internal representation of how a system works. It is not memorization. It is a compressed, generative structure that lets you derive solutions to new problems from first principles.

The goal is not to memorize a hundred algorithms. The goal is to hold a small number of deep models that generate the right algorithm for any situation.

### The Problem-Solving Stack

Every problem you encounter sits somewhere in this stack:

```
+--------------------------------------------------+
|           PROBLEM STATEMENT                      |
|  (ambiguous, incomplete, in natural language)    |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           FORMAL SPECIFICATION                   |
|  (precise inputs, outputs, constraints)          |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           STRUCTURAL RECOGNITION                 |
|  (what KIND of problem is this?)                 |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           DECOMPOSITION                          |
|  (split into tractable sub-problems)             |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           SUB-PROBLEM SOLVING                    |
|  (apply known techniques)                        |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           SOLUTION MERGING                       |
|  (compose sub-solutions correctly)               |
+--------------------------------------------------+
              |
              v
+--------------------------------------------------+
|           VERIFICATION                           |
|  (correctness, complexity, edge cases)           |
+--------------------------------------------------+
```

### The First Principle: Understand Before Solving

Before writing a single line of code or picking a data structure, you must achieve total clarity on:

1. **What are the exact inputs?** Type, size, constraints, guarantees (sorted? unique? bounded?).
2. **What are the exact outputs?** Single value, a structure, a modified input, an order?
3. **What are the constraints?** Time limit, memory limit, mutation allowed?
4. **What is the problem's invariant?** What stays true throughout the computation?
5. **What are the edge cases?** Empty input, single element, maximum size, negative numbers, duplicates.

This is not a checklist you tick and move on. Each answer reshapes your entire approach.

### Example: "Find the maximum subarray sum"

Wrong approach: Jump to code.

Right approach:
- Input: an array of integers, possibly negative, possibly empty.
- Output: a single integer, the maximum sum.
- Constraint: O(n) preferred.
- Invariant: At each position, we either extend the previous subarray or start fresh.
- Edge case: all negative? Return the least negative. Empty array? Return 0 or undefined.

Now the algorithm (Kadane's) drops out naturally from the invariant.

---

## 2. Divide and Conquer — Deep Mechanics

### The Core Idea

Divide and Conquer is not just a technique. It is a structural observation: **many problems have optimal substructure**, meaning the solution to a problem can be built from solutions to smaller versions of the same problem.

The three steps are:

```
DIVIDE   --> Split problem into smaller sub-problems of the same type
CONQUER  --> Solve each sub-problem (recursively, or base case directly)
COMBINE  --> Merge sub-solutions into the final solution
```

### The Recurrence Relation

Every divide-and-conquer algorithm has a recurrence that captures its time complexity:

```
T(n) = a * T(n/b) + f(n)
```

Where:
- `a` = number of sub-problems
- `n/b` = size of each sub-problem
- `f(n)` = cost of dividing and combining

The **Master Theorem** solves this:

```
Compare f(n) to n^(log_b(a)):

Case 1: f(n) = O(n^(log_b(a) - ε))  -->  T(n) = Θ(n^log_b(a))
Case 2: f(n) = Θ(n^log_b(a))        -->  T(n) = Θ(n^log_b(a) * log n)
Case 3: f(n) = Ω(n^(log_b(a) + ε))  -->  T(n) = Θ(f(n))
```

### Merge Sort — The Canonical Example

```
Problem: Sort array A[0..n-1]

DIVIDE:  Split into A[0..n/2-1] and A[n/2..n-1]         O(1)
CONQUER: Recursively sort both halves                    2*T(n/2)
COMBINE: Merge two sorted halves into one sorted array   O(n)

Recurrence: T(n) = 2*T(n/2) + O(n)
Master Theorem: a=2, b=2, f(n)=n, n^log_2(2) = n^1 = n
Case 2: T(n) = O(n log n)
```

ASCII diagram of merge sort:

```
[8, 3, 5, 1, 9, 2, 7, 4]
         DIVIDE
   [8,3,5,1]      [9,2,7,4]
   DIVIDE          DIVIDE
 [8,3]  [5,1]   [9,2]  [7,4]
 DIV     DIV     DIV    DIV
[8][3] [5][1]  [9][2] [7][4]
         CONQUER (base cases)
 [3,8]  [1,5]   [2,9]  [4,7]
         COMBINE
   [1,3,5,8]      [2,4,7,9]
         COMBINE
   [1,2,3,4,5,7,8,9]
```

### Quick Sort — The Partition-Based Variant

Quick Sort also divides and conquers but without guaranteed equal splits:

```
DIVIDE:  Partition around a pivot: [< pivot] [pivot] [> pivot]
CONQUER: Sort left and right partitions recursively
COMBINE: Nothing — the array is sorted in-place

Average: T(n) = 2*T(n/2) + O(n) = O(n log n)
Worst:   T(n) = T(n-1) + O(n) = O(n^2)   (sorted input, bad pivot)
```

The key insight: the COMBINE step is free when you do work in DIVIDE (partition). This is a general trade-off: do you pay in dividing or combining?

### Binary Search — Divide and Conquer Without Combining

```
DIVIDE:  Compare target to midpoint, eliminate half the array
CONQUER: Recurse on the relevant half
COMBINE: Nothing — answer is directly returned

T(n) = T(n/2) + O(1) = O(log n)
```

This shows that D&C does not always require a merge step. When CONQUER produces the final answer directly, COMBINE is a no-op.

### Strassen's Matrix Multiplication — When Constant Factors Matter

Naive matrix multiply: O(n^3), T(n) = 8*T(n/2) + O(n^2)

Strassen: T(n) = 7*T(n/2) + O(n^2) → O(n^2.807)

Reducing sub-problem count from 8 to 7 by algebraic manipulation of the combine step. The lesson: **the number of recursive calls is often the dominant term**, and creative algebraic rearrangement can reduce it.

---

## 3. Problem Decomposition Methodology

### Step 1: Problem Classification

Before decomposing, classify the problem:

```
+-------------------+------------------------------------------+
| CLASS             | SIGNATURE                                |
+-------------------+------------------------------------------+
| Search            | Find an element satisfying a predicate   |
| Optimization      | Find min/max over a space                |
| Counting          | Count valid configurations               |
| Construction      | Build an object with properties          |
| Decision          | Yes/no answer                            |
| Transformation    | Convert input to a different form        |
| Ordering          | Sort or rank elements                    |
| Graph Problem     | Connectivity, path, flow, coloring       |
+-------------------+------------------------------------------+
```

Each class has canonical sub-problem patterns.

### Step 2: Identify Problem Dimensions

What varies? What is fixed? Every degree of freedom is a potential decomposition axis.

Example: "Find the kth largest element in an unsorted array."

Dimensions:
- **k**: varies (which element we want)
- **array size n**: varies
- **ordering**: we want the kth in sorted order

Decomposition axes:
- Decompose by **position** (quick-select: partition and recurse on the relevant partition)
- Decompose by **value** (use a heap of size k)
- Decompose by **count** (count elements larger than a threshold)

Each axis gives a different algorithm with different trade-offs.

### Step 3: The Decomposition Tree

Explicitly draw the decomposition:

```
ORIGINAL PROBLEM
├── Sub-problem A
│   ├── Sub-sub-problem A1
│   └── Sub-sub-problem A2
├── Sub-problem B
│   ├── Sub-sub-problem B1
│   └── Sub-sub-problem B2
└── COMBINE (A, B)
```

The key questions at each node:
- Is this sub-problem independent of the others? (true D&C)
- Does this sub-problem overlap with another? (dynamic programming territory)
- Is this sub-problem a base case? (termination condition)
- What is the interface between this node and its parent? (what does it return?)

### Step 4: Interface Design

The interface between sub-problems is where most bugs live. Define it precisely:

```
Sub-problem: solve(array, left, right)
Returns: the sorted array in [left, right]
Precondition: left <= right
Postcondition: array[left..right] is sorted, all other elements unchanged
```

Write this before writing a single line of implementation. The interface is the contract.

### Step 5: Base Case Identification

The base case must:
1. Be reachable from every recursive call
2. Be solvable directly without recursion
3. Not be trivially wrong (off-by-one errors live here)

Common base cases:
- n == 0: empty input → return identity element
- n == 1: single element → trivially sorted/searched/summed
- n == 2: smallest non-trivial case → often handle explicitly
- left == right: single-index range → base case for range-based recursion

### Step 6: The Recursion Invariant

Every recursive algorithm must have an invariant — a property that is true before and after every recursive call.

Example for merge sort:
- **Invariant**: After `solve(A, l, r)` returns, `A[l..r]` is sorted.
- This is true for base case (single element is sorted).
- If true for both halves before merge, true for full range after merge.

This is how you prove recursive algorithms correct: establish the invariant, show base case satisfies it, show inductive step preserves it.

---

## 4. Solving Sub-Problems Efficiently

### The Technique Selection Matrix

```
+----------------------------+--------------------+------------------+
| PROBLEM PROPERTY           | TECHNIQUE          | COMPLEXITY       |
+----------------------------+--------------------+------------------+
| Sorted input, search       | Binary Search      | O(log n)         |
| Overlapping subproblems    | Dynamic Programming| O(n^k) typical   |
| Greedy choice property     | Greedy             | O(n log n) usual |
| Graph: shortest path       | Dijkstra/BFS/BF    | O(E log V)       |
| Graph: MST                 | Kruskal/Prim       | O(E log V)       |
| String matching            | KMP/Z-algo         | O(n + m)         |
| Range queries              | Segment Tree/BIT   | O(log n)         |
| Frequency/hash lookup      | Hash Map           | O(1) amortized   |
| Order statistics           | BST/Heap           | O(log n)         |
| Streaming/online           | Sliding Window     | O(n)             |
| Two-pointer problems       | Two Pointers       | O(n)             |
| Combinatorial optimization | Backtracking       | O(exponential)   |
+----------------------------+--------------------+------------------+
```

### Dynamic Programming: The Overlap Detector

DP is the right tool when:
1. The problem has **optimal substructure**: the optimal solution contains optimal solutions to sub-problems.
2. Sub-problems **overlap**: the same sub-problem is solved multiple times in a naive recursive approach.

The mental model:

```
NAIVE RECURSION with MEMOIZATION  =  TOP-DOWN DP
BOTTOM-UP TABLE FILLING           =  BOTTOM-UP DP
```

Both are equivalent. Bottom-up is often faster (no recursion overhead, better cache behavior).

#### Fibonacci as DP template:

```c
// Naive: O(2^n) — exponential due to recomputation
int fib_naive(int n) {
    if (n <= 1) return n;
    return fib_naive(n-1) + fib_naive(n-2);
}

// Top-down DP with memoization: O(n)
int memo[1001];
int fib_memo(int n) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = fib_memo(n-1) + fib_memo(n-2);
}

// Bottom-up DP: O(n) time, O(n) space
int fib_dp(int n) {
    int dp[n+1];
    dp[0] = 0; dp[1] = 1;
    for (int i = 2; i <= n; i++)
        dp[i] = dp[i-1] + dp[i-2];
    return dp[n];
}

// Space-optimized: O(n) time, O(1) space
int fib_opt(int n) {
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int c = a + b;
        a = b; b = c;
    }
    return b;
}
```

#### State Design in DP

The hardest part of DP is state design. Ask:
- What is the minimum information I need to describe where I am in the computation?
- What is the recurrence relation between states?
- What is the base case (initial state)?

For "Longest Common Subsequence":
- State: `dp[i][j]` = LCS of first i chars of s1 and first j chars of s2
- Recurrence: if `s1[i] == s2[j]`: `dp[i][j] = dp[i-1][j-1] + 1` else `max(dp[i-1][j], dp[i][j-1])`
- Base: `dp[0][j] = dp[i][0] = 0`

### Greedy: When Locally Optimal Is Globally Optimal

Greedy works when there is a **greedy choice property**: making the locally optimal choice at each step leads to a globally optimal solution.

This must be **proved**, not assumed. The proof is usually by exchange argument: assume the greedy solution is not optimal, show you can swap a non-greedy choice with a greedy choice without making things worse.

Canonical greedy problems:
- Activity selection: always pick the activity that ends earliest
- Huffman coding: always merge the two least-frequent nodes
- Kruskal's MST: always add the cheapest edge that doesn't form a cycle

### Two Pointers: The Linear Scan Mental Model

Two pointers work when the problem has a monotonic structure: moving one pointer forward makes the condition more or less satisfied, and you can adjust the other pointer accordingly.

```
Problem: Find pair in sorted array that sums to target.

left = 0, right = n-1
while left < right:
    sum = A[left] + A[right]
    if sum == target: found
    if sum < target: left++   (need larger sum)
    if sum > target: right--  (need smaller sum)
```

The invariant: the answer, if it exists, always lies within [left, right].

### Sliding Window: Fixed and Variable

Fixed window: maintain a window of size k moving across the array.
Variable window: expand right pointer until condition violated, then shrink left.

```
Variable window for "smallest subarray with sum >= S":

left = 0, sum = 0, min_len = infinity
for right = 0 to n-1:
    sum += A[right]
    while sum >= S:
        min_len = min(min_len, right - left + 1)
        sum -= A[left]
        left++
```

The invariant: `[left, right]` is the smallest valid window ending at `right`.

---

## 5. Merging Solutions Properly

### The Merge as the Algorithm's Heart

Merging is where most of the algorithm's intelligence lives. The divide step is usually mechanical. The merge step encodes the problem's structure.

### What to Think About When Merging

1. **Order of combination**: Does it matter which sub-solution is combined first?
2. **Invariant preservation**: Does the merged result maintain the invariant?
3. **Information loss**: What information from sub-solutions is needed for merging? What can be discarded?
4. **Efficiency**: Can the merge be done in O(n) or better?

### The Merge Sort Merge — Two-Pointer Technique

```c
void merge(int *A, int left, int mid, int right) {
    int n1 = mid - left + 1;
    int n2 = right - mid;

    // Temporary arrays
    int L[n1], R[n2];
    for (int i = 0; i < n1; i++) L[i] = A[left + i];
    for (int i = 0; i < n2; i++) R[i] = A[mid + 1 + i];

    int i = 0, j = 0, k = left;

    // Merge: always pick the smaller of the two front elements
    while (i < n1 && j < n2) {
        if (L[i] <= R[j]) A[k++] = L[i++];
        else               A[k++] = R[j++];
    }

    // Copy remainders (at most one of these loops executes)
    while (i < n1) A[k++] = L[i++];
    while (j < n2) A[k++] = R[j++];
}
```

**Why this works**: Both halves are sorted. We maintain the invariant that the smallest unplaced element is at the front of one of the two halves. We greedily pick the smallest.

### Counting Inversions — Non-Trivial Merge

An inversion is a pair (i, j) where i < j but A[i] > A[j]. Counting inversions uses merge sort's merge step to count them efficiently:

```
During merge of [left..mid] and [mid+1..right]:
When we pick an element from the RIGHT half (R[j])
before an element from the LEFT half (L[i]),
every remaining element in L is an inversion partner.
Count += (n1 - i)
```

This piggybacks extra computation onto the merge step — a powerful general technique.

### The Segment Tree Merge

Segment trees answer range queries by merging answers from child nodes. The merge function depends entirely on the query type:

```
Range sum:    merge(left, right) = left.sum + right.sum
Range min:    merge(left, right) = min(left.min, right.min)
Range max:    merge(left, right) = max(left.max, right.max)
Range GCD:    merge(left, right) = gcd(left.gcd, right.gcd)
```

The tree structure is the same. The merge function encodes what we're querying.

### Incorrect Merges and How to Avoid Them

Common merge bugs:

1. **Off-by-one in index ranges**: Use half-open intervals [left, right) consistently, or always closed [left, right]. Never mix.
2. **Modifying input during merge**: If sub-problems share data, merging one can corrupt input to another.
3. **Missing edge case in base case**: A single-element is "sorted" but may not satisfy other properties (e.g., a single-element subarray sum is the element itself, including if it's negative).
4. **Forgetting the combine step**: In-place algorithms (quicksort) may make you forget that the work is done — explicitly verify no combine is needed.

---

## 6. Decision Making in Algorithm Design

### The Algorithm Design Decision Tree

```
Given a problem, ask in order:

1. Is there a known O(n) or O(log n) solution?
   YES: Use it. (Sorting a bounded integer range? Counting sort.)
   NO: Continue.

2. Can I solve it greedily?
   Ask: does the greedy choice property hold?
   If provable: implement greedy.
   If not clear: continue.

3. Does it have overlapping subproblems?
   YES: Dynamic programming.
   NO: Continue.

4. Can it be divided into independent subproblems of the same type?
   YES: Divide and conquer.
   NO: Continue.

5. Is the solution space small enough to explore?
   YES: Backtracking with pruning.
   NO: Look for better decomposition or approximation.
```

### Choosing Data Structures

```
NEED                           USE                    WHY
---------------------------    -------------------    --------------------------------
O(1) lookup by key             Hash Map               Direct address / chaining
Ordered iteration              BST / Sorted Array     In-order traversal / binary search
Min/max with updates           Heap                   Heap property maintained
Range min/max queries          Segment Tree / Sparse  O(log n) / O(1) query
Union and find disjoint sets   Union-Find (DSU)       Nearly O(1) amortized with path comp.
FIFO ordering                  Queue / Deque          Circular buffer
LIFO ordering                  Stack                  Array or linked list
Connected components           BFS / DFS + visited    Linear traversal
Frequency counting             Hash Map / Array       Indexed by value
String prefix search           Trie                   Character-by-character descent
Top-k elements                 Heap of size k         O(n log k)
Rank/select operations         Order Statistics Tree  Augmented BST
```

### When to Prefer Simplicity

Never choose a complex data structure when a simple one suffices. A sorted array with binary search beats a BST for static data because:
- Better cache locality (contiguous memory)
- No pointer overhead
- Simpler implementation
- Same O(log n) search complexity

The rule: **use the simplest structure that meets your complexity requirements**.

### The Space-Time Trade-off

Almost every algorithmic optimization trades space for time or vice versa:

```
Memoization:       More space    → Less time    (cache results)
Recomputation:     Less space    → More time    (recompute each time)
Lookup table:      More space    → O(1) time    (precomputed answers)
Compression:       Less space    → More time    (decode before use)
Index structures:  More space    → Faster query (B-tree, hash index)
Streaming:         O(1) space    → Single pass  (may lose accuracy)
```

---

## 7. Data Structures — Deep Internals

### Arrays — The Foundation

An array is a contiguous block of memory. Every array operation is ultimately expressed in terms of:
- Base address
- Stride (element size)
- Index arithmetic

```
Address of A[i] = base_address + i * sizeof(element)
```

This makes array access O(1) — it is a single memory read after arithmetic.

**Cache behavior**: Arrays are the most cache-friendly structure. Sequential access patterns have perfect spatial locality. Prefetchers predict sequential access and preload cache lines.

```
Cache line size: typically 64 bytes
int array: 16 ints per cache line
On cache miss: entire 64-byte line loaded
Sequential access: 1 miss per 16 accesses = very efficient
Random access: 1 miss per access = cache unfriendly
```

### Linked Lists — Pointer-Based Traversal

```
Singly linked:
[data|next] --> [data|next] --> [data|next] --> NULL

Doubly linked:
NULL <-- [prev|data|next] <-- --> [prev|data|next] --> NULL

Circular:
[data|next] --> [data|next] --> [data|next] -+
^                                             |
+---------------------------------------------+
```

**Why linked lists exist**: O(1) insert/delete at known position without shifting. Useful for:
- Implementing queues and deques efficiently
- Adjacency lists in graphs
- LRU cache (hash map + doubly linked list)
- Kernel memory allocators (free list)

**Why linked lists are often wrong**: Cache unfriendly. Each node is a separate heap allocation. Pointer chasing is expensive on modern hardware. For most data < 10,000 elements, an array with shifting is faster in practice due to cache effects.

### Hash Maps — O(1) Everything (Amortized)

```
Key --(hash function)--> bucket index --> linked list / probe sequence

+--------+----------+
| bucket | chain    |
+--------+----------+
|   0    | -> [K,V] |
|   1    | NULL     |
|   2    | -> [K,V] -> [K,V] |
|   3    | -> [K,V] |
|  ...   | ...      |
+--------+----------+
```

**Hash function requirements**:
1. Deterministic: same key → same hash always
2. Uniform distribution: minimize collisions
3. Fast to compute

**Collision resolution**:
- **Chaining**: Each bucket is a linked list. Simple, handles high load factors.
- **Open addressing**: Probe sequence (linear, quadratic, double hashing). Better cache behavior, sensitive to load factor.

**Load factor** α = n/m (elements / buckets):
- Keep α < 0.75 for chaining, < 0.5 for open addressing
- When exceeded, resize (double capacity, rehash all elements) → amortized O(1) insertion

**The amortized analysis**: n insertions into a table that doubles at capacity:
- Resizing costs O(k) where k is current size
- Resizing happens at sizes 1, 2, 4, 8, ..., n
- Total cost: 1 + 2 + 4 + ... + n = O(n)
- Amortized cost per insertion: O(n)/n = O(1)

### Binary Search Tree (BST)

```
        8
       / \
      3   10
     / \    \
    1   6   14
       / \  /
      4   7 13
```

**BST property**: left subtree < node < right subtree (for all nodes)

Operations:
- Search: O(h) — follow comparisons down
- Insert: O(h) — find position, add leaf
- Delete: O(h) — three cases: leaf, one child, two children
- h = height = O(log n) for balanced, O(n) worst case (degenerate/sorted input)

**Why balance matters**: A BST built from sorted input degenerates to a linked list. Self-balancing BSTs (AVL, Red-Black) maintain O(log n) height through rotations.

### Red-Black Tree — The Production BST

Properties:
1. Every node is RED or BLACK
2. Root is BLACK
3. Every leaf (NULL) is BLACK
4. Red node's children are both BLACK
5. All paths from any node to descendant leaves have same number of BLACK nodes

These properties guarantee: height ≤ 2*log(n+1), so all operations are O(log n).

```
        B:8
       /   \
      R:3   B:10
     / \      \
    B:1 B:6   R:14
        / \   /
       R:4 R:7 B:13
```

C uses red-black trees in: Linux kernel (CFS scheduler, memory manager VMA tree), Java's `TreeMap`, C++ `std::map`.

### Heap — The Priority Queue

A heap is a complete binary tree stored as an array, satisfying the heap property:
- **Max-heap**: parent ≥ children (max at root)
- **Min-heap**: parent ≤ children (min at root)

```
Array: [16, 14, 10, 8, 7, 9, 3, 2, 4, 1]
Index:  0   1   2  3  4  5  6  7  8  9

Tree representation:
            16 (0)
           /      \
        14 (1)    10 (2)
       /    \     /    \
     8 (3)  7(4) 9(5)  3(6)
    / \     /
  2(7) 4(8) 1(9)

For node at index i:
  Parent:       (i-1) / 2
  Left child:   2*i + 1
  Right child:  2*i + 2
```

**Insert**: Add to end, sift up — O(log n)
**Extract-min/max**: Replace root with last element, sift down — O(log n)
**Heapify**: Build heap from array — O(n) (not O(n log n) — by tighter analysis)

### Trie — Prefix Trees

```
Dictionary: ["cat", "car", "card", "care", "bat"]

        root
       /    \
      c      b
      |      |
      a      a
     / \     |
    t   r    t
        |\ 
        d  e
```

Each path from root to a node represents a prefix. Mark "end of word" at terminal nodes.

Insert/search: O(m) where m = string length (independent of number of strings!)
Space: O(total characters in all strings)

Uses: autocomplete, spell checking, IP routing (longest prefix match), dictionary compression.

### Union-Find (Disjoint Set Union)

Tracks which elements belong to the same set. Two operations:
- **Find(x)**: return the representative of x's set
- **Union(x, y)**: merge the sets containing x and y

```
Initially: {0} {1} {2} {3} {4}
parent: [0, 1, 2, 3, 4]

Union(0,1): 0 becomes root of {0,1}
parent: [0, 0, 2, 3, 4]

Union(1,2): find root of 1 (it's 0), find root of 2 (it's 2), merge
parent: [0, 0, 0, 3, 4]

Find(2): 2 -> 0 (root), return 0
```

**Path compression**: During Find, make all nodes on the path point directly to root.
**Union by rank**: Always make the smaller tree the child of the larger.

With both optimizations: nearly O(1) amortized per operation (inverse Ackermann function, practically constant).

---

## 8. Algorithm Patterns and When to Use Them

### Pattern: Reduce to Known Problem

Often the fastest solution is recognizing that your problem is isomorphic to a well-solved one.

"Find if a string has all unique characters" → "Count frequencies" → "Check if any frequency > 1"
"Find cycle in linked list" → Floyd's tortoise and hare (two-pointer)
"Schedule intervals without overlap" → Activity selection (greedy by end time)

### Pattern: Think Backwards

Some problems are much easier to solve in reverse.

"Find the last non-repeating character in a stream" → Process from right to left.
"Restore the original sequence after k reversals" → Simulate in reverse.

### Pattern: Binary Search on the Answer

When the answer is a number in a range, and you can check "is X achievable?" in O(n) or less, binary search on the answer:

```
Is it possible to do X in T time? (monotone: if possible in T, also possible in T+1)

Binary search on T from [lo, hi]:
  mid = (lo + hi) / 2
  if check(mid): hi = mid
  else: lo = mid + 1
answer = lo
```

Applies to: minimum time to complete tasks, maximum K with some property, etc.

### Pattern: Monotonic Stack

Use when you need to find, for each element, the next/previous greater/smaller element.

```c
// Next greater element for each position
int stack[MAXN]; int top = -1;
int next_greater[MAXN];
memset(next_greater, -1, sizeof(next_greater));

for (int i = 0; i < n; i++) {
    // Pop elements smaller than current
    while (top >= 0 && A[stack[top]] < A[i]) {
        next_greater[stack[top--]] = i;
    }
    stack[++top] = i;
}
// Remaining elements in stack have no next greater element
```

Applications: largest rectangle in histogram, daily temperatures, maximum width ramp.

### Pattern: Prefix Sums

Precompute cumulative sums for O(1) range sum queries:

```c
int prefix[n+1];
prefix[0] = 0;
for (int i = 0; i < n; i++) prefix[i+1] = prefix[i] + A[i];

// Sum of A[l..r]:
int range_sum = prefix[r+1] - prefix[l];
```

Extend to 2D for matrix range sum queries.

### Pattern: Meet in the Middle

When brute force is O(2^n) and n ≤ 40, split into two halves of n/2, enumerate all 2^(n/2) subsets for each, then combine.

Reduces O(2^40) to O(2^20 * log(2^20)) — feasible.

---

## 9. Complexity Analysis — The Real Mental Model

### Time Complexity Is Not What You Think

Time complexity is not about wall-clock time. It is about **how the algorithm's resource usage scales as input grows**. It is a model, and like all models, it is an approximation.

What it ignores:
- Constant factors (cache effects, instruction-level parallelism)
- Input-specific behavior (average vs worst case)
- Hardware-specific behavior (memory hierarchy, branch prediction)

What it captures:
- The dominant term as n → ∞
- The qualitative scaling behavior

### Big-O, Big-Ω, Big-Θ

```
f(n) = O(g(n)):   f grows no faster than g     (upper bound)
f(n) = Ω(g(n)):   f grows no slower than g     (lower bound)
f(n) = Θ(g(n)):   f grows at the same rate as g (tight bound)
```

When people say "this algorithm is O(n log n)", they usually mean Θ(n log n). The distinction matters when proving lower bounds (showing no algorithm can do better than Ω(n log n) for comparison-based sorting).

### Amortized Analysis

When individual operations are sometimes expensive but rare, amortized analysis gives a better average:

**Dynamic array (append)**:
- Most appends: O(1)
- Occasional resize: O(n)
- Amortized: O(1) (total n appends cost O(n) total)

**Methods**:
1. **Aggregate**: total cost / n operations
2. **Accounting**: assign credits to cheap operations, spend on expensive ones
3. **Potential**: define potential function Φ representing "stored work"

### Space Complexity

Often overlooked. Recursive algorithms have implicit O(h) stack space where h = recursion depth.

```
Merge sort: O(n) auxiliary space for temporary arrays
Quick sort: O(log n) average stack space, O(n) worst case
DFS on graph: O(V) stack space (recursion depth = path length)
```

### Practical Complexity

For competitive programming / real systems, rough operation counts:

```
n ≤ 10:         O(n!), O(2^n)       backtracking fine
n ≤ 20:         O(2^n)              bitmask DP
n ≤ 400:        O(n^3)              Floyd-Warshall, 3-nested loops
n ≤ 5000:       O(n^2)              bubble/insertion sort, N^2 DP
n ≤ 10^6:       O(n log n)          merge sort, most tree operations
n ≤ 10^8:       O(n)                linear scan, prefix sum
n ≤ 10^18:      O(log n)            binary search, matrix exponentiation
```

---

## 10. Linux Kernel Programming — The Complete Model

### Why Kernel Programming Is Different

Kernel programming is not systems programming. It is a completely different discipline with different rules:

1. **No standard library**: No `malloc`, no `printf`, no `stdlib.h`, no exceptions.
2. **No memory protection from yourself**: A kernel bug corrupts the entire system.
3. **Concurrency everywhere**: Multiple CPUs, interrupts, softirqs — all competing.
4. **No floating point** (usually): FPU state is not saved in kernel context.
5. **Fixed stack size**: ~8KB per thread. No large local arrays. No deep recursion.
6. **Cannot sleep in atomic context**: No blocking operations while holding a spinlock or in interrupt handlers.

### The Kernel Address Space

```
Virtual Address Space (x86-64):

0xFFFFFFFFFFFFFFFF  +-----------------------------+
                    |   Kernel space              |
                    |   (128 TB on x86-64)        |
0xFFFF800000000000  +-----------------------------+
                    |   Non-canonical "hole"      |
0x00007FFFFFFFFFFF  +-----------------------------+
                    |   User space                |
                    |   (128 TB on x86-64)        |
0x0000000000000000  +-----------------------------+

Kernel virtual memory layout (typical x86-64):
0xFFFFFFFF80000000  Kernel text/data (direct map of physical memory)
0xFFFF888000000000  Direct physical memory map
0xFFFFEA0000000000  vmalloc area
0xFFFFEE0000000000  Persistent kernel mappings
```

### Kernel Source Tree Structure

```
linux/
├── arch/          CPU-specific code (x86, arm64, riscv, ...)
│   └── x86/
│       ├── kernel/    x86 core (entry.S, process.c, irq.c)
│       ├── mm/        x86 memory management
│       └── include/   x86-specific headers
├── block/         Block I/O layer
├── drivers/       Device drivers (bulk of kernel source)
├── fs/            Filesystems (ext4, btrfs, vfs layer)
├── include/       Architecture-independent headers
│   ├── linux/     Core kernel headers
│   └── uapi/      Userspace-visible API headers
├── init/          Kernel startup (main.c, init process)
├── ipc/           Inter-process communication
├── kernel/        Core kernel (scheduler, signals, timers)
├── lib/           Utility functions (string, sort, CRC, ...)
├── mm/            Memory management
├── net/           Networking stack
├── scripts/       Build scripts, kconfig
└── security/      LSMs (SELinux, AppArmor, eBPF)
```

### The Kernel Build System (Kbuild)

Every kernel module has a Makefile:

```makefile
# For in-tree module:
obj-$(CONFIG_MY_DRIVER) += my_driver.o
my_driver-y := main.o helper.o

# For out-of-tree module:
obj-m += my_module.o

# Build command:
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
```

### Writing a Minimal Kernel Module (C)

```c
// hello_module.c
#include <linux/module.h>    // MODULE_* macros
#include <linux/kernel.h>    // pr_info, KERN_INFO
#include <linux/init.h>      // module_init, module_exit

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Author Name");
MODULE_DESCRIPTION("A minimal kernel module");
MODULE_VERSION("1.0");

static int __init hello_init(void)
{
    pr_info("Hello kernel: module loaded\n");
    return 0;  // Non-zero means init failed, module not loaded
}

static void __exit hello_exit(void)
{
    pr_info("Goodbye kernel: module unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);
```

The `__init` and `__exit` annotations tell the linker to place these functions in special sections that can be freed after use.

### Kernel Logging

```c
// Log levels (from highest to lowest priority):
pr_emerg("System is unusable\n");        // KERN_EMERG   "0"
pr_alert("Action must be taken\n");      // KERN_ALERT   "1"
pr_crit("Critical condition\n");         // KERN_CRIT    "2"
pr_err("Error condition\n");             // KERN_ERR     "3"
pr_warn("Warning condition\n");          // KERN_WARNING "4"
pr_notice("Normal but significant\n");   // KERN_NOTICE  "5"
pr_info("Informational message\n");      // KERN_INFO    "6"
pr_debug("Debug-level message\n");       // KERN_DEBUG   "7"

// pr_debug is compiled out unless DEBUG is defined or dynamic debug enabled
// Use dev_info(), dev_err(), etc. for device driver messages (adds device context)
```

### Kernel Coding Style (Enforced)

The kernel uses a very specific coding style (enforced by `checkpatch.pl`):

```c
// Indentation: TABS, not spaces (8-character tab stops)
// Line length: 80 columns (soft), 100 (hard max)
// Braces: K&R style

// Functions: opening brace on its own line
int my_function(int arg)
{
    // Local variable declarations first, then code
    int result;
    unsigned long flags;

    // No blank line between declaration and first statement
    result = 0;

    // if/else/while/for: brace even for single statements
    if (condition) {
        do_something();
    } else {
        do_other();
    }

    // goto is acceptable for error handling (cleans up resources)
    if (error_condition)
        goto out_free;

    return result;

out_free:
    kfree(buf);
    return -ENOMEM;
}

// Naming: lowercase_with_underscores
// Constants: UPPERCASE_WITH_UNDERSCORES
// Avoid typedef except for function pointers
```

### Error Handling in the Kernel

The kernel uses negative errno values as error codes:

```c
#include <linux/errno.h>

// Common errors:
return -ENOMEM;   // Out of memory
return -EINVAL;   // Invalid argument
return -EFAULT;   // Bad address (user/kernel pointer issue)
return -ENODEV;   // No such device
return -EBUSY;    // Resource busy
return -ETIMEDOUT; // Operation timed out
return -ENOTSUPP; // Operation not supported
return -EPERM;    // Not permitted

// Check errors with IS_ERR and PTR_ERR:
ptr = some_alloc();
if (IS_ERR(ptr)) {
    return PTR_ERR(ptr);  // Extracts the negative error code
}

// Return error pointers from functions:
return ERR_PTR(-ENOMEM);
```

The goto-based cleanup pattern is idiomatic and correct:

```c
int my_init(void)
{
    int ret;

    ret = allocate_resource_a();
    if (ret)
        return ret;

    ret = allocate_resource_b();
    if (ret)
        goto free_a;

    ret = allocate_resource_c();
    if (ret)
        goto free_b;

    return 0;  // Success

free_b:
    free_resource_b();
free_a:
    free_resource_a();
    return ret;
}
```

This unwinds in reverse allocation order — correct and readable.

---

## 11. Kernel Data Structures and Mechanisms

### The Linux Kernel List (Intrusive Doubly Linked List)

The kernel does not use a generic linked list where each node holds a `void *data`. Instead, it uses **intrusive** lists: the list node (`struct list_head`) is embedded directly in the data structure.

```c
// Definition in <linux/list.h>
struct list_head {
    struct list_head *next, *prev;
};

// Embed in your structure:
struct my_process {
    pid_t pid;
    char name[16];
    struct list_head list;  // Embedded list node
};

// Initialize a list head (macro):
LIST_HEAD(my_list);   // static initialization
// or:
INIT_LIST_HEAD(&my_list);  // dynamic initialization

// Add to list:
list_add(&proc->list, &my_list);       // Add at front (after head)
list_add_tail(&proc->list, &my_list);  // Add at back (before head)

// Remove from list:
list_del(&proc->list);
list_del_init(&proc->list);  // Also re-initializes to empty

// Iterate:
struct my_process *p;
list_for_each_entry(p, &my_list, list) {
    pr_info("Process: %d %s\n", p->pid, p->name);
}

// Safe iteration (allows deletion during iteration):
struct my_process *p, *tmp;
list_for_each_entry_safe(p, tmp, &my_list, list) {
    if (p->pid == target_pid) {
        list_del(&p->list);
        kfree(p);
    }
}
```

The magic behind `list_for_each_entry`: the `container_of` macro.

```c
// container_of: given a pointer to a member, get pointer to containing struct
#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

// Given &proc->list, get proc:
struct my_process *p = container_of(list_ptr, struct my_process, list);
```

This is a fundamental kernel pattern: embedding generic infrastructure into domain structures, not wrapping domain data in generic nodes.

### The Red-Black Tree (`rbtree`)

```c
#include <linux/rbtree.h>

struct my_node {
    struct rb_node node;   // Embedded RB node
    int key;
    char data[64];
};

struct rb_root my_tree = RB_ROOT;

// Insert:
void my_insert(struct rb_root *root, struct my_node *new_node)
{
    struct rb_node **link = &root->rb_node, *parent = NULL;

    while (*link) {
        struct my_node *entry = rb_entry(*link, struct my_node, node);
        parent = *link;

        if (new_node->key < entry->key)
            link = &(*link)->rb_left;
        else if (new_node->key > entry->key)
            link = &(*link)->rb_right;
        else
            return;  // Duplicate
    }

    rb_link_node(&new_node->node, parent, link);
    rb_insert_color(&new_node->node, root);  // Rebalance
}

// Search:
struct my_node *my_search(struct rb_root *root, int key)
{
    struct rb_node *node = root->rb_node;
    while (node) {
        struct my_node *entry = rb_entry(node, struct my_node, node);
        if (key < entry->key)
            node = node->rb_left;
        else if (key > entry->key)
            node = node->rb_right;
        else
            return entry;
    }
    return NULL;
}
```

### Hash Tables (`hashtable.h`)

```c
#include <linux/hashtable.h>

// Declare hash table with 2^bits buckets:
DEFINE_HASHTABLE(my_htable, 8);  // 256 buckets

struct my_entry {
    int key;
    char value[32];
    struct hlist_node node;
};

// Add:
struct my_entry *e = kmalloc(sizeof(*e), GFP_KERNEL);
e->key = 42;
hash_add(my_htable, &e->node, e->key);

// Lookup:
struct my_entry *found;
hash_for_each_possible(my_htable, found, node, 42) {
    if (found->key == 42) {
        // found it
    }
}

// Delete:
hash_del(&e->node);

// Iterate all:
int bkt;
hash_for_each(my_htable, bkt, found, node) {
    pr_info("key=%d\n", found->key);
}
```

### Radix Tree / XArray

The XArray is the modern replacement for the radix tree, used for mapping integer indices to pointers (e.g., page cache: file offset → page struct):

```c
#include <linux/xarray.h>

DEFINE_XARRAY(my_xa);

// Store:
xa_store(&my_xa, index, value, GFP_KERNEL);

// Load:
void *val = xa_load(&my_xa, index);

// Erase:
xa_erase(&my_xa, index);

// Iterate:
unsigned long idx;
void *entry;
xa_for_each(&my_xa, idx, entry) {
    // process entry at idx
}
```

---

## 12. Memory Management in the Kernel

### The Physical Memory Model

```
Physical Memory Organization:
+----------------------------+
| ZONE_DMA (0-16MB)          |  Legacy ISA DMA devices
+----------------------------+
| ZONE_DMA32 (0-4GB)         |  32-bit DMA devices
+----------------------------+
| ZONE_NORMAL (rest)         |  Normal kernel memory
+----------------------------+
| ZONE_HIGHMEM (32-bit only) |  Not directly mapped (x86-32)
+----------------------------+

Each zone managed by a buddy allocator.
Smallest allocation: 1 page (4KB typical)
Buddy allocator works in powers of 2: 1,2,4,8,...,1024 pages
```

### Kernel Memory Allocators

#### `kmalloc` — General Purpose Small Allocations

```c
#include <linux/slab.h>

// Allocate and free:
void *ptr = kmalloc(size, flags);
kfree(ptr);

// Zero-initialized:
void *ptr = kzalloc(size, flags);

// Reallocate:
void *ptr = krealloc(old_ptr, new_size, flags);

// For arrays:
void *ptr = kmalloc_array(count, element_size, flags);
void *ptr = kcalloc(count, element_size, flags);  // zero-initialized
```

**GFP flags (Get Free Pages)**:

```c
GFP_KERNEL    // Normal allocation, may sleep, may reclaim memory
GFP_ATOMIC    // Cannot sleep (interrupt context, spinlock held), may fail
GFP_NOWAIT    // Like atomic but no emergency reserves
GFP_NOIO      // Cannot start I/O (to avoid deadlocks in storage drivers)
GFP_NOFS      // Cannot call into filesystem
GFP_DMA       // Allocate from DMA zone
GFP_HIGHUSER  // Allocate from high memory for user pages
```

**When to use which**:
- In process context (can sleep): `GFP_KERNEL`
- In interrupt handler, softirq, spinlock held: `GFP_ATOMIC`
- In block device driver: `GFP_NOIO`
- In filesystem code: `GFP_NOFS`

`kmalloc` is backed by the **SLAB/SLUB allocator**, which maintains caches for common sizes (8, 16, 32, 64, 128, 256, ... bytes) to reduce fragmentation and improve performance.

#### `vmalloc` — Large Non-Contiguous Allocations

```c
#include <linux/vmalloc.h>

void *ptr = vmalloc(size);     // Virtually contiguous, not physically
void *ptr = vzalloc(size);     // Zero-initialized
vfree(ptr);
```

Use `vmalloc` when:
- You need more than a few pages (> 128KB or so)
- Physical contiguity is not required
- The allocation may fail with `kmalloc` due to fragmentation

`vmalloc` is slower due to TLB setup. Never use for small allocations.

#### `get_free_pages` — Page-Level Allocation

```c
// Allocate 2^order pages (must be physically contiguous):
unsigned long page = __get_free_pages(GFP_KERNEL, order);
free_pages(page, order);

// Single page:
unsigned long page = __get_free_page(GFP_KERNEL);
free_page(page);

// Get struct page pointer:
struct page *p = alloc_pages(GFP_KERNEL, order);
__free_pages(p, order);
```

#### Custom Slab Caches — Per-Object Pools

For frequently allocated/freed fixed-size structures, create a dedicated cache:

```c
#include <linux/slab.h>

// Create cache at module init:
static struct kmem_cache *my_cache;

my_cache = kmem_cache_create(
    "my_object_cache",        // name (appears in /proc/slabinfo)
    sizeof(struct my_object), // object size
    0,                        // alignment (0 = natural)
    SLAB_HWCACHE_ALIGN,       // flags
    NULL                      // constructor (optional)
);

// Allocate from cache:
struct my_object *obj = kmem_cache_alloc(my_cache, GFP_KERNEL);

// Free back to cache:
kmem_cache_free(my_cache, obj);

// Destroy cache at module exit:
kmem_cache_destroy(my_cache);
```

### User Space Memory Access

When kernel code needs to read/write user space memory, it must use special functions:

```c
#include <linux/uaccess.h>

// Copy from user to kernel:
if (copy_from_user(kernel_buf, user_ptr, count))
    return -EFAULT;

// Copy from kernel to user:
if (copy_to_user(user_ptr, kernel_buf, count))
    return -EFAULT;

// Single values:
int val;
if (get_user(val, (int __user *)user_ptr))
    return -EFAULT;

if (put_user(val, (int __user *)user_ptr))
    return -EFAULT;
```

The `__user` annotation is checked by `sparse` (kernel static analyzer). Never dereference a user pointer directly in kernel space — it may be invalid, unmapped, or malicious.

---

## 13. Synchronization and Concurrency in the Kernel

### Why Kernel Concurrency Is Unique

The kernel faces multiple concurrent execution contexts:

```
Execution contexts (from highest to lowest priority):
+------------------+------------------------------------------+
| Hardware IRQ     | Cannot be preempted by anything          |
| Softirq          | Cannot be preempted by softirqs          |
| Tasklet          | Per-CPU, serialized per tasklet          |
| Workqueue        | Process context, can sleep               |
| Kernel thread    | Process context, can sleep               |
| System call      | Process context, can sleep               |
+------------------+------------------------------------------+

Additionally: SMP (multiple CPUs running simultaneously)
```

A lock taken in process context can be interrupted by an IRQ on the same CPU. The IRQ handler cannot acquire the same lock (deadlock). Solution: disable IRQs while holding the lock.

### Spinlocks

A spinlock causes the CPU to busy-wait (spin) until the lock is available. Used when the critical section is short and sleeping is not allowed.

```c
#include <linux/spinlock.h>

// Declare and initialize:
spinlock_t my_lock;
spin_lock_init(&my_lock);

// Or static initialization:
DEFINE_SPINLOCK(my_lock);

// Basic lock/unlock (process context only, IRQs must not be enabled):
spin_lock(&my_lock);
// critical section
spin_unlock(&my_lock);

// In process context when IRQ handler might access the same data:
unsigned long flags;
spin_lock_irqsave(&my_lock, flags);    // Disables IRQs, saves flags
// critical section
spin_unlock_irqrestore(&my_lock, flags);

// In IRQ handler (IRQs already disabled on this CPU):
spin_lock(&my_lock);
// critical section
spin_unlock(&my_lock);

// If only need to disable softirqs (bottom halves):
spin_lock_bh(&my_lock);
spin_unlock_bh(&my_lock);
```

**Rules for spinlocks**:
1. Never sleep while holding a spinlock.
2. Keep critical sections short.
3. Never call any function that might sleep (kmalloc with GFP_KERNEL, copy_from_user, etc.).
4. Use `irqsave` variant if the lock is shared with IRQ handlers.

### Mutexes

A mutex can sleep — the task blocks and is scheduled away instead of spinning. Use in process context for longer critical sections.

```c
#include <linux/mutex.h>

struct mutex my_mutex;
mutex_init(&my_mutex);

// Or static:
DEFINE_MUTEX(my_mutex);

// Lock (may sleep):
mutex_lock(&my_mutex);
// critical section (can sleep here)
mutex_unlock(&my_mutex);

// Non-blocking attempt:
if (mutex_trylock(&my_mutex)) {
    // got the lock
    mutex_unlock(&my_mutex);
}

// Interruptible lock (returns -EINTR if signal received):
if (mutex_lock_interruptible(&my_mutex))
    return -ERESTARTSYS;
mutex_unlock(&my_mutex);
```

**Rules for mutexes**:
1. Cannot be used in interrupt context (IRQ, softirq, tasklet).
2. Must be unlocked by the same task that locked it.
3. Must not be used in atomic context.

### Read-Write Locks

When reads are frequent and writes are rare, use `rwlock` or `rw_semaphore`:

```c
#include <linux/rwlock.h>

DEFINE_RWLOCK(my_rwlock);

// Multiple readers simultaneously:
read_lock(&my_rwlock);
// read data
read_unlock(&my_rwlock);

// Exclusive writer:
write_lock(&my_rwlock);
// modify data
write_unlock(&my_rwlock);

// For process context (can sleep):
#include <linux/rwsem.h>
DECLARE_RWSEM(my_rwsem);
down_read(&my_rwsem);
up_read(&my_rwsem);
down_write(&my_rwsem);
up_write(&my_rwsem);
```

### RCU — Read-Copy-Update

RCU is the kernel's most scalable synchronization mechanism for read-heavy workloads. Readers are completely lock-free. Writers make a copy, modify it, then atomically update the pointer.

```c
#include <linux/rcupdate.h>

// Reader:
rcu_read_lock();
struct my_data *p = rcu_dereference(global_ptr);
if (p)
    use(p->field);  // Safe to read while in RCU read-side critical section
rcu_read_unlock();

// Writer:
struct my_data *old = rcu_dereference(global_ptr);
struct my_data *new = kmalloc(sizeof(*new), GFP_KERNEL);
*new = *old;           // Copy old data
new->field = new_val;  // Modify copy
rcu_assign_pointer(global_ptr, new);  // Atomically publish new
synchronize_rcu();     // Wait for all readers of old to finish
kfree(old);            // Safe to free now
```

The `synchronize_rcu()` call waits for a "grace period" — until all currently executing RCU read-side critical sections have completed. After this, no reader holds a reference to the old pointer.

**When to use RCU**:
- Data is read far more often than written
- Read-side performance is critical (networking, file system path lookup)
- Deletions are fine to defer

### Atomic Operations

For simple counters and flags, atomic operations avoid locks entirely:

```c
#include <linux/atomic.h>

atomic_t my_counter = ATOMIC_INIT(0);

atomic_inc(&my_counter);                    // ++counter
atomic_dec(&my_counter);                    // --counter
int val = atomic_read(&my_counter);         // read
atomic_set(&my_counter, 5);                 // write
int old = atomic_fetch_add(3, &my_counter); // return old, add 3
bool dec_and_zero = atomic_dec_and_test(&my_counter); // dec, test if 0

// 64-bit:
atomic64_t big_counter = ATOMIC64_INIT(0);

// Bitwise:
set_bit(n, &flags);
clear_bit(n, &flags);
test_bit(n, &flags);
test_and_set_bit(n, &flags);
```

### Completion Variables

Completions synchronize between two execution paths: one waits, the other signals completion.

```c
#include <linux/completion.h>

DECLARE_COMPLETION(my_comp);
// or:
struct completion my_comp;
init_completion(&my_comp);

// Waiter:
wait_for_completion(&my_comp);        // Blocks until complete
wait_for_completion_timeout(&my_comp, HZ);  // With timeout

// Signaler:
complete(&my_comp);         // Wake up one waiter
complete_all(&my_comp);     // Wake up all waiters
```

---

## 14. Kernel Subsystems Architecture

### The VFS Layer

The Virtual Filesystem Switch is an abstraction layer that provides a unified interface to all filesystems:

```
User Space:  open(), read(), write(), close(), stat(), ...
             |
             v
+------------------------------------------+
|              SYSTEM CALL LAYER            |
+------------------------------------------+
             |
             v
+------------------------------------------+
|              VFS LAYER                    |
|  struct inode, dentry, file, super_block  |
|  path_lookup(), vfs_read(), vfs_write()   |
+------------------------------------------+
        |           |           |
        v           v           v
  +----------+ +--------+ +---------+
  |  ext4    | |  tmpfs | |  proc   |
  +----------+ +--------+ +---------+
        |
        v
+------------------------------------------+
|          BLOCK LAYER                      |
|  request queues, I/O scheduling           |
+------------------------------------------+
        |
        v
+------------------------------------------+
|          DEVICE DRIVER                    |
|  (SCSI, NVMe, SATA, ...)                 |
+------------------------------------------+
```

Key VFS structures:

```c
struct super_block {     // Represents a mounted filesystem
    unsigned long s_blocksize;
    struct file_system_type *s_type;
    struct super_operations *s_op;
    // ...
};

struct inode {           // Represents a file (metadata only)
    umode_t i_mode;      // Permissions
    kuid_t i_uid;
    kgid_t i_gid;
    loff_t i_size;
    struct inode_operations *i_op;
    struct address_space *i_mapping;
    // ...
};

struct dentry {          // Directory entry (name → inode mapping)
    struct inode *d_inode;
    struct dentry *d_parent;
    struct qstr d_name;
    // ...
};

struct file {            // Represents an open file descriptor
    struct path f_path;
    struct inode *f_inode;
    struct file_operations *f_op;
    loff_t f_pos;        // Current file position
    // ...
};
```

### The Scheduler (CFS)

The Completely Fair Scheduler maintains a red-black tree of runnable tasks ordered by **virtual runtime** (vruntime):

```
CFS Red-Black Tree (keyed by vruntime):

        [task C: vrt=100]
       /                  \
[task A: vrt=80]    [task D: vrt=120]
       \
  [task B: vrt=95]

Always runs the leftmost (minimum vruntime) task.

vruntime += delta_exec * NICE_0_LOAD / task->load.weight

Tasks with lower nice (higher priority) accumulate vruntime more slowly
→ they run more often but for similar wall-clock duration
```

```c
// Scheduler-related kernel code patterns:

// Check if we need to reschedule:
if (need_resched())
    schedule();

// Voluntary yield:
cond_resched();  // Reschedule if needed (check in long loops)
schedule();      // Unconditional schedule

// Set task state before sleeping:
set_current_state(TASK_INTERRUPTIBLE);   // Woken by signal or wake_up()
set_current_state(TASK_UNINTERRUPTIBLE); // Only by wake_up()
schedule();      // Actually sleep

// Wake up a task:
wake_up_process(task);
```

### Device Driver Model

```
Platform Bus:
+-------------------+     +-------------------+
| struct platform_  |     | struct platform_  |
| device (hardware) |<--->| driver (software) |
+-------------------+     +-------------------+
        |                         |
        v                         v
  probe() called when driver matches device

PCI Bus:
+-------------------+     +-------------------+
| struct pci_dev    |<--->| struct pci_driver |
+-------------------+     +-------------------+
```

Minimal character device driver:

```c
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>

#define DEVICE_NAME "mydev"
#define BUF_SIZE 1024

static int major;
static struct class *my_class;
static struct cdev my_cdev;
static char buf[BUF_SIZE];

static int my_open(struct inode *inode, struct file *file)
{
    pr_info("mydev: opened\n");
    return 0;
}

static int my_release(struct inode *inode, struct file *file)
{
    pr_info("mydev: closed\n");
    return 0;
}

static ssize_t my_read(struct file *file, char __user *user_buf,
                       size_t count, loff_t *ppos)
{
    int len = strlen(buf);
    if (*ppos >= len) return 0;
    if (count > len - *ppos) count = len - *ppos;

    if (copy_to_user(user_buf, buf + *ppos, count))
        return -EFAULT;

    *ppos += count;
    return count;
}

static ssize_t my_write(struct file *file, const char __user *user_buf,
                        size_t count, loff_t *ppos)
{
    if (count >= BUF_SIZE) count = BUF_SIZE - 1;

    if (copy_from_user(buf, user_buf, count))
        return -EFAULT;

    buf[count] = '\0';
    return count;
}

static struct file_operations my_fops = {
    .owner   = THIS_MODULE,
    .open    = my_open,
    .release = my_release,
    .read    = my_read,
    .write   = my_write,
};

static int __init my_init(void)
{
    dev_t dev;
    int ret;

    ret = alloc_chrdev_region(&dev, 0, 1, DEVICE_NAME);
    if (ret < 0) return ret;

    major = MAJOR(dev);
    cdev_init(&my_cdev, &my_fops);
    my_cdev.owner = THIS_MODULE;

    ret = cdev_add(&my_cdev, dev, 1);
    if (ret) goto unregister;

    my_class = class_create(THIS_MODULE, DEVICE_NAME);
    if (IS_ERR(my_class)) { ret = PTR_ERR(my_class); goto del_cdev; }

    device_create(my_class, NULL, dev, NULL, DEVICE_NAME);
    pr_info("mydev: registered with major %d\n", major);
    return 0;

del_cdev:
    cdev_del(&my_cdev);
unregister:
    unregister_chrdev_region(dev, 1);
    return ret;
}

static void __exit my_exit(void)
{
    dev_t dev = MKDEV(major, 0);
    device_destroy(my_class, dev);
    class_destroy(my_class);
    cdev_del(&my_cdev);
    unregister_chrdev_region(dev, 1);
    pr_info("mydev: unregistered\n");
}

module_init(my_init);
module_exit(my_exit);
MODULE_LICENSE("GPL");
```

---

## 15. C Implementation Patterns for Systems Programming

### Memory Layout Awareness

In systems C, you must think about memory layout explicitly:

```c
// Structure padding and alignment:
struct bad {      // 12 bytes due to padding
    char a;       // 1 byte + 3 bytes padding
    int b;        // 4 bytes
    char c;       // 1 byte + 3 bytes padding
};

struct good {     // 6 bytes (or 8 with trailing padding)
    int b;        // 4 bytes
    char a;       // 1 byte
    char c;       // 1 byte + 2 bytes padding to align to int
};

struct packed {   // 6 bytes exactly (unaligned, slower access)
    char a;
    int b;
    char c;
} __attribute__((packed));

// Verify with:
_Static_assert(sizeof(struct good) == 8, "Unexpected size");
```

### Bit Fields and Bit Manipulation

```c
// Bit manipulation fundamentals:
#define BIT(n)          (1UL << (n))
#define BITS_MASK(n)    (BIT(n) - 1)

// Set bit n:
flags |= BIT(n);

// Clear bit n:
flags &= ~BIT(n);

// Toggle bit n:
flags ^= BIT(n);

// Test bit n:
if (flags & BIT(n)) { ... }

// Extract bits [high:low]:
#define FIELD_GET(mask, val)  (((val) & (mask)) >> __builtin_ctzl(mask))
#define FIELD_PREP(mask, val) (((val) << __builtin_ctzl(mask)) & (mask))

// Count set bits (popcount):
__builtin_popcount(x)    // int
__builtin_popcountl(x)   // long
__builtin_popcountll(x)  // long long

// Find first set bit (position):
__builtin_ffs(x)    // 1-indexed, 0 if none
__builtin_ctz(x)    // count trailing zeros
__builtin_clz(x)    // count leading zeros
```

### Function Pointers and Callbacks

```c
// Function pointer type:
typedef int (*compare_fn)(const void *a, const void *b);

// Using callbacks:
void generic_sort(void *base, size_t n, size_t size, compare_fn cmp)
{
    // ... sorting logic using cmp(a, b)
}

// Implement a comparator:
int int_compare(const void *a, const void *b)
{
    int x = *(const int *)a;
    int y = *(const int *)b;
    return (x > y) - (x < y);  // Branchless: returns -1, 0, or 1
}

// Use:
int arr[] = {5, 3, 1, 4, 2};
generic_sort(arr, 5, sizeof(int), int_compare);
```

### The Object-Oriented Pattern in C (vtable)

```c
// "Class" definition:
struct shape;

struct shape_ops {
    double (*area)(const struct shape *s);
    double (*perimeter)(const struct shape *s);
    void   (*draw)(const struct shape *s);
    void   (*destroy)(struct shape *s);
};

struct shape {
    const struct shape_ops *ops;  // vtable pointer
};

// "Derived class":
struct circle {
    struct shape base;            // Must be first member
    double radius;
};

// Implement virtual functions:
static double circle_area(const struct shape *s)
{
    const struct circle *c = (const struct circle *)s;
    return 3.14159265 * c->radius * c->radius;
}

static void circle_destroy(struct shape *s)
{
    free(s);
}

static const struct shape_ops circle_ops = {
    .area      = circle_area,
    .perimeter = circle_perimeter,
    .draw      = circle_draw,
    .destroy   = circle_destroy,
};

// Constructor:
struct shape *circle_create(double radius)
{
    struct circle *c = malloc(sizeof(*c));
    if (!c) return NULL;
    c->base.ops = &circle_ops;
    c->radius = radius;
    return &c->base;
}

// Polymorphic usage:
void print_area(const struct shape *s)
{
    printf("Area: %f\n", s->ops->area(s));
}
```

This is exactly how the Linux kernel implements VFS (file_operations), network protocol stacks (proto_ops), and device drivers.

### Defensive Programming in C

```c
// NEVER trust input sizes:
void process_buffer(const char *buf, size_t len)
{
    if (!buf || len == 0)
        return;
    if (len > MAX_ALLOWED_SIZE)
        len = MAX_ALLOWED_SIZE;
    // ...
}

// Use strnlen, strncpy, snprintf — never strlen on unvalidated input:
char dest[64];
snprintf(dest, sizeof(dest), "%s", source);  // Always safe

// Check every allocation:
void *ptr = malloc(size);
if (!ptr) {
    perror("malloc");
    return -ENOMEM;
}

// Initialize all memory:
memset(ptr, 0, size);
// Or use calloc:
void *ptr = calloc(count, element_size);

// Integer overflow protection:
if (a > SIZE_MAX - b)  // Check before: a + b
    return -EOVERFLOW;
size_t result = a + b;
```

---

## 16. Rust in Systems Programming

### Why Rust for Systems Code

Rust provides memory safety guarantees that C cannot, at zero runtime cost:

1. **Ownership**: Every value has exactly one owner. Value is dropped when owner goes out of scope.
2. **Borrowing**: You can borrow a value as `&T` (immutable, many) or `&mut T` (mutable, one at a time).
3. **Lifetimes**: References cannot outlive what they point to.
4. **No null pointers**: Use `Option<T>` instead.
5. **No uninitialized memory**: Must initialize before use.
6. **No data races**: The type system prevents concurrent mutable access without synchronization.

These are compile-time guarantees. They cost nothing at runtime.

### Ownership and Borrowing — The Mental Model

```rust
// Ownership transfer (move):
let s1 = String::from("hello");
let s2 = s1;           // s1 is moved into s2
// println!("{}", s1); // Compile error: s1 was moved

// Clone to avoid move:
let s1 = String::from("hello");
let s2 = s1.clone();   // Deep copy
println!("{} {}", s1, s2);  // Both valid

// Borrowing (immutable reference):
fn compute_length(s: &String) -> usize {
    s.len()  // Can read but not modify
}
let s = String::from("hello");
let len = compute_length(&s);  // Lend s to function
println!("{} {}", s, len);     // s still valid

// Mutable borrowing:
fn append(s: &mut String) {
    s.push_str(", world");
}
let mut s = String::from("hello");
append(&mut s);
// Only ONE mutable reference at a time — prevents data races
```

### Lifetimes — Making Implicit Relationships Explicit

```rust
// This function returns a reference — to what?
// Lifetime annotation says: returned ref lives as long as the shorter of x or y
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct holding a reference:
struct Excerpt<'a> {
    part: &'a str,  // 'a: the excerpt lives no longer than the source
}

impl<'a> Excerpt<'a> {
    fn level(&self) -> i32 { 3 }
}
```

### Rust Error Handling — No Exceptions

```rust
use std::fs::File;
use std::io::{self, Read};

// Result<T, E> is either Ok(T) or Err(E)
fn read_file(path: &str) -> Result<String, io::Error> {
    let mut file = File::open(path)?;  // ? propagates error
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

// Option<T> is either Some(T) or None (like nullable)
fn find_first_even(nums: &[i32]) -> Option<i32> {
    nums.iter().find(|&&x| x % 2 == 0).copied()
}

// Pattern matching on results:
match read_file("config.txt") {
    Ok(contents) => println!("File contents: {}", contents),
    Err(e) => eprintln!("Error reading file: {}", e),
}

// Combinators:
let val = some_option
    .map(|x| x * 2)           // Transform if Some
    .filter(|&x| x > 10)      // Keep if predicate
    .unwrap_or(0);             // Default if None
```

### Rust Traits — The Interface System

```rust
// Define a trait (like an interface):
trait Animal {
    fn name(&self) -> &str;
    fn sound(&self) -> &str;

    // Default implementation:
    fn describe(&self) -> String {
        format!("{} says {}", self.name(), self.sound())
    }
}

// Implement for a type:
struct Dog;
impl Animal for Dog {
    fn name(&self) -> &str { "Dog" }
    fn sound(&self) -> &str { "woof" }
}

// Generic functions with trait bounds:
fn print_description<T: Animal>(animal: &T) {
    println!("{}", animal.describe());
}

// Multiple bounds:
fn process<T: Animal + Clone + Debug>(x: &T) { ... }

// Dynamic dispatch (runtime polymorphism):
let animals: Vec<Box<dyn Animal>> = vec![
    Box::new(Dog),
    Box::new(Cat),
];
for a in &animals {
    println!("{}", a.describe());  // Virtual dispatch
}
```

### Unsafe Rust — Controlled Danger

In safe Rust, you cannot:
- Dereference raw pointers
- Call unsafe functions
- Access mutable static variables
- Implement unsafe traits
- Read from uninitialized memory

`unsafe` blocks unlock these capabilities, with the programmer taking responsibility:

```rust
// Raw pointer operations:
let x: i32 = 42;
let r = &x as *const i32;

unsafe {
    println!("Value at raw pointer: {}", *r);  // Dereference
}

// Call an unsafe function:
unsafe fn dangerous() {
    // ... something unsafe
}
unsafe { dangerous(); }

// Interface with C:
extern "C" {
    fn abs(x: i32) -> i32;
}
let result = unsafe { abs(-5) };

// Slice from raw parts:
let slice: &[i32] = unsafe {
    std::slice::from_raw_parts(ptr, len)
};
```

The key principle: **unsafe code must maintain invariants that safe code relies on**. The `unsafe` keyword is a promise to the compiler: "I checked this, it's correct."

---

## 17. C and Rust Interoperability

### The FFI Layer

Rust can call C, and C can call Rust. The boundary is the **Foreign Function Interface (FFI)**.

### Calling C from Rust

```rust
// Declare C functions in extern "C" block:
extern "C" {
    fn strlen(s: *const std::os::raw::c_char) -> usize;
    fn malloc(size: usize) -> *mut std::os::raw::c_void;
    fn free(ptr: *mut std::os::raw::c_void);
    fn memcpy(
        dest: *mut std::os::raw::c_void,
        src: *const std::os::raw::c_void,
        n: usize,
    ) -> *mut std::os::raw::c_void;
}

// Use them:
use std::ffi::CString;

let s = CString::new("hello world").expect("CString failed");
let len = unsafe { strlen(s.as_ptr()) };
println!("Length: {}", len);
```

**Type correspondence table**:

```
C Type              Rust Type
------------------  ----------------------------
void                ()
bool                bool
char                c_char (i8 or u8 depending on platform)
short               c_short (i16)
int                 c_int (i32)
long                c_long (i32 or i64 depending on platform)
long long           c_longlong (i64)
unsigned int        c_uint (u32)
size_t              usize
ptrdiff_t           isize
float               c_float (f32)
double              c_double (f64)
void *              *mut c_void
const void *        *const c_void
char *              *mut c_char
const char *        *const c_char
int (*fn)(int)      Option<unsafe extern "C" fn(c_int) -> c_int>
```

### Calling Rust from C

Rust function must be:
1. Declared `pub`
2. Annotated `#[no_mangle]` (prevent name mangling)
3. Use `extern "C"` ABI

```rust
// lib.rs
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn rust_strlen(s: *const std::os::raw::c_char) -> usize {
    if s.is_null() {
        return 0;
    }
    unsafe {
        let mut len = 0;
        while *s.add(len) != 0 {
            len += 1;
        }
        len
    }
}
```

Corresponding C header:

```c
// rust_lib.h
#pragma once
#include <stdint.h>
#include <stddef.h>

int32_t rust_add(int32_t a, int32_t b);
size_t rust_strlen(const char *s);
```

C usage:

```c
#include "rust_lib.h"
#include <stdio.h>

int main(void) {
    printf("3 + 4 = %d\n", rust_add(3, 4));
    return 0;
}
```

Build:

```bash
# Build Rust as static library:
cargo build --release
# Produces: target/release/libmylib.a

# Link with C:
gcc main.c -L./target/release -lmylib -lpthread -ldl -o main
```

### bindgen — Auto-Generate Rust Bindings from C Headers

Instead of manually writing `extern "C"` declarations, use `bindgen`:

```bash
# Install:
cargo install bindgen-cli

# Generate bindings from C header:
bindgen input.h -o src/bindings.rs

# In build.rs (build script):
```

```rust
// build.rs
fn main() {
    let bindings = bindgen::Builder::default()
        .header("wrapper.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks))
        .generate()
        .expect("Unable to generate bindings");

    let out_path = std::path::PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
```

```rust
// src/lib.rs
#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
```

### Sharing Data Structures Between C and Rust

```c
// C header: shared_types.h
#pragma once
#include <stdint.h>

typedef struct {
    uint32_t id;
    float x;
    float y;
    char name[32];
} Point;

int process_points(const Point *points, size_t count);
```

```rust
// Rust equivalent (must match C layout exactly):
#[repr(C)]  // Use C memory layout
#[derive(Debug, Clone)]
pub struct Point {
    pub id: u32,
    pub x: f32,
    pub y: f32,
    pub name: [std::os::raw::c_char; 32],
}

// Static assertion: sizes match
const _: () = assert!(
    std::mem::size_of::<Point>() == 44,  // 4+4+4+32 = 44
    "Point size mismatch"
);

extern "C" {
    fn process_points(points: *const Point, count: usize) -> std::os::raw::c_int;
}

pub fn safe_process_points(points: &[Point]) -> i32 {
    unsafe { process_points(points.as_ptr(), points.len()) }
}
```

The `#[repr(C)]` attribute is critical. Without it, Rust may reorder fields for efficiency, breaking C compatibility.

### Safe Wrappers — The Right Pattern

Never expose raw FFI to safe Rust code. Wrap it:

```rust
pub struct SafeBuffer {
    ptr: *mut u8,
    len: usize,
}

impl SafeBuffer {
    pub fn new(size: usize) -> Option<Self> {
        let ptr = unsafe { libc::malloc(size) as *mut u8 };
        if ptr.is_null() {
            None
        } else {
            Some(SafeBuffer { ptr, len: size })
        }
    }

    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }

    pub fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.ptr, self.len) }
    }
}

impl Drop for SafeBuffer {
    fn drop(&mut self) {
        unsafe { libc::free(self.ptr as *mut libc::c_void) }
    }
}

// Now it's safe to use:
let buf = SafeBuffer::new(1024).expect("allocation failed");
let data = buf.as_slice();  // Safe slice reference
// Automatically freed when buf goes out of scope (Drop impl)
```

---

## 18. Rust in the Linux Kernel

### The Rust for Linux Project

Since Linux 6.1 (2022), Rust is an officially supported second language for kernel development. The goal is to write new kernel modules in Rust, benefiting from memory safety while sharing the kernel's C infrastructure.

### Architecture

```
+-----------------------------------------------------------+
|                    KERNEL (C + Rust)                      |
+-----------------------------------------------------------+
|  Rust modules  |  Safe Rust bindings  |  C kernel core   |
|  (new drivers) |  (linux/src/rust/)   |  (unchanged)     |
+-----------------------------------------------------------+
        |                  |                    |
        v                  v                    v
  Uses safe Rust    Wraps C APIs          C primitives
  abstractions      in Rust types         (spinlock, etc.)
```

The Rust kernel code lives in `rust/` in the kernel source tree and provides safe wrappers around kernel C APIs.

### Kernel Rust Abstractions

The `kernel` crate provides safe wrappers:

```rust
// A Rust kernel module:
use kernel::prelude::*;
use kernel::{Module, ThisModule};

module! {
    type: RustHelloModule,
    name: "rust_hello",
    author: "Author",
    description: "Hello World in Rust",
    license: "GPL",
}

struct RustHelloModule;

impl kernel::Module for RustHelloModule {
    fn init(_name: &'static CStr, _module: &'static ThisModule)
        -> Result<Self>
    {
        pr_info!("Hello from Rust kernel module!\n");
        Ok(RustHelloModule)
    }
}

impl Drop for RustHelloModule {
    fn drop(&mut self) {
        pr_info!("Goodbye from Rust kernel module!\n");
    }
}
```

### Rust Kernel: Mutex Abstraction

```rust
use kernel::sync::{Mutex, Arc};
use kernel::prelude::*;

// Rust's type system enforces locking discipline:
// You CANNOT access data inside a Mutex without locking it
// The lock guard's lifetime ensures unlock on drop

let data = Arc::new(Mutex::new(vec![1, 2, 3]));

{
    let mut guard = data.lock();  // Locked
    guard.push(4);                // Access data
}                                 // Automatically unlocked here

// This prevents the classic "forgot to unlock" kernel bug.
```

### Rust Kernel: The Pin Pattern

Many kernel data structures cannot be moved in memory once initialized (they contain self-referential pointers, are registered with C code, etc.). Rust's `Pin<T>` type expresses this:

```rust
use core::pin::Pin;

// A pinned struct cannot be moved after pinning:
struct NonMovable {
    self_ref: *const NonMovable,
    data: i32,
}

// Pin<&mut NonMovable> guarantees the data won't move
// This maps to kernel's requirement that once registered,
// objects like wait_queue_head_t stay at their address
```

### Building Rust Kernel Modules

```bash
# Enable Rust support:
make LLVM=1 menuconfig
# Select: General Setup → Rust support

# Build:
make LLVM=1

# Build a specific Rust module:
make LLVM=1 samples/rust/

# Out-of-tree Rust module:
# Cargo.toml must reference the kernel crate
# Use the kernel's build system via Makefile
```

### The `bindgen` Role in Kernel Rust

The kernel uses `bindgen` to generate Rust bindings for C kernel headers at build time. This is the bridge:

```
C kernel headers (include/linux/*.h)
         |
         v
    bindgen (at build time)
         |
         v
Rust bindings (rust/bindings/bindings_generated.rs)
         |
         v
Safe Rust abstractions (rust/kernel/*.rs)
         |
         v
Rust kernel modules (drivers/*/rust/*.rs)
```

---

## 19. Debugging Mental Models

### The Scientific Method for Bugs

1. **Observe**: What exactly is the wrong behavior? (not "it crashes", but "it segfaults at address 0x1234 in function foo() with input X")
2. **Hypothesize**: What could cause this specific behavior?
3. **Predict**: If my hypothesis is correct, what should I see when I test it?
4. **Test**: Minimize the reproduction case. Run the test.
5. **Conclude**: Was the hypothesis correct? If no, revise and repeat.

### Kernel Debugging Tools

**`printk` / `pr_*`**: The most reliable debugging tool. Always works, even in interrupt context.

**`/proc/kmsg` and `dmesg`**: Read kernel log.

**`ftrace`**: Kernel function tracer with near-zero overhead.

```bash
# Trace all calls to a function:
echo schedule > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace
```

**`kgdb`**: Full kernel debugger over serial.

**`KASAN` (Kernel Address SANitizer)**: Detects use-after-free, out-of-bounds in C kernel code.

```bash
# Enable in kernel config:
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y
```

**`lockdep`**: Detects lock ordering violations and potential deadlocks.

```bash
CONFIG_LOCKDEP=y
CONFIG_PROVE_LOCKING=y
```

### Common Kernel Bugs and Their Signatures

```
BUG SIGNATURE                    CAUSE
-------------------------------  ----------------------------------------
NULL pointer dereference         Accessing uninitialized pointer
Use-after-free                   Accessing freed memory (UAF)
Buffer overflow                  Writing past array/buffer end
Stack overflow                   Too-deep recursion or large local arrays
Deadlock                         Two locks acquired in opposite order
Race condition                   Missing synchronization
Memory leak                      Alloc without matching free
Integer overflow                 Arithmetic on fixed-width types
Sleeping in atomic context       kmalloc(GFP_KERNEL) with spinlock held
```

### Valgrind and Sanitizers (Userspace C)

```bash
# Memory error detection:
valgrind --leak-check=full --show-leak-kinds=all ./program

# AddressSanitizer (faster than valgrind):
gcc -fsanitize=address -g -O1 program.c -o program
./program  # Reports errors with full stack traces

# ThreadSanitizer (data race detection):
gcc -fsanitize=thread -g -O1 program.c -o program

# UBSanitizer (undefined behavior):
gcc -fsanitize=undefined -g program.c -o program

# Combine:
gcc -fsanitize=address,undefined -g -O1 program.c -o program
```

### Rust Debugging

```bash
# Cargo test with backtrace:
RUST_BACKTRACE=1 cargo test

# Cargo with sanitizers:
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test

# GDB with Rust:
rust-gdb target/debug/program
```

---

## 20. Performance Mental Models

### The Memory Hierarchy — The Most Important Mental Model

```
+------------------+----------+-----------+------------------+
| Storage          | Latency  | Bandwidth | Size             |
+------------------+----------+-----------+------------------+
| CPU registers    | ~0 ns    | ~TB/s     | ~KB (handful)    |
| L1 cache         | ~1 ns    | ~500 GB/s | 32-64 KB         |
| L2 cache         | ~4 ns    | ~200 GB/s | 256 KB - 1 MB    |
| L3 cache         | ~12 ns   | ~100 GB/s | 4-64 MB          |
| Main memory      | ~100 ns  | ~50 GB/s  | GB               |
| NVMe SSD         | ~100 µs  | ~7 GB/s   | TB               |
| SATA SSD         | ~500 µs  | ~600 MB/s | TB               |
| HDD              | ~10 ms   | ~200 MB/s | TB               |
| Network (LAN)    | ~500 µs  | ~10 GB/s  | (infinite)       |
| Network (WAN)    | ~50 ms   | ~GB/s     | (infinite)       |
+------------------+----------+-----------+------------------+
```

L1 to main memory is a 100x difference in latency. A cache miss that goes to main memory stalls the CPU for 200+ cycles. This is why data structure layout matters more than algorithm complexity for small n.

### Cache Optimization Principles

**Spatial locality**: Access memory in sequential or nearby patterns. Arrays are good. Pointer-chasing (linked lists, trees with separate allocation) is bad.

**Temporal locality**: Reuse recently accessed data. Process all data needed from a cache line before moving on.

**Structure of Arrays vs Array of Structures**:

```c
// Array of Structures (AoS) — bad for SIMD, mixed cache usage:
struct Particle { float x, y, z, mass; };
struct Particle particles[N];  // Accessing only x: load 4 floats, use 1

// Structure of Arrays (SoA) — cache-friendly for SIMD:
struct Particles {
    float x[N];    // All x's contiguous
    float y[N];    // All y's contiguous
    float z[N];
    float mass[N];
};
// Accessing only x: loads N/16 cache lines for N floats
```

### The Cost Model

Develop an intuitive cost model for operations:

```
Operation                           Approximate Cost
---------------------------------   -----------------
Integer add/sub/and/or/xor          1 cycle
Integer multiply                    3-5 cycles
Integer divide                      20-90 cycles (AVOID in hot paths)
Floating point add/mul              3-5 cycles (pipelined)
Branch (predicted)                  0-1 cycles
Branch (mispredicted)               15-20 cycles penalty
L1 cache hit                        4 cycles
L2 cache hit                        12 cycles
L3 cache hit                        40 cycles
Main memory access                  200 cycles
Syscall                             1000-2000 cycles
Context switch                      5000-10000 cycles
```

### SIMD — Single Instruction Multiple Data

Modern CPUs can operate on multiple values simultaneously:

```c
#include <immintrin.h>  // x86 AVX intrinsics

// Add 8 floats at once (AVX):
__m256 a = _mm256_loadu_ps(array_a);  // Load 8 floats
__m256 b = _mm256_loadu_ps(array_b);
__m256 c = _mm256_add_ps(a, b);       // Add 8 pairs simultaneously
_mm256_storeu_ps(result, c);          // Store 8 floats
```

The compiler can often auto-vectorize simple loops. Help it:
- Avoid aliasing (use `restrict` keyword)
- Keep loop bodies simple
- Ensure data is aligned (or use unaligned loads explicitly)
- Use `-O3 -march=native` to enable auto-vectorization

### Lock-Free Programming

Lock-free algorithms use atomic operations instead of locks:

```c
// Lock-free stack (Treiber stack):
typedef struct Node {
    int value;
    struct Node *next;
} Node;

_Atomic(Node *) head = NULL;

void push(int val) {
    Node *new_node = malloc(sizeof(Node));
    new_node->value = val;
    Node *old_head;
    do {
        old_head = atomic_load(&head);
        new_node->next = old_head;
    } while (!atomic_compare_exchange_weak(&head, &old_head, new_node));
}

Node *pop(void) {
    Node *old_head;
    Node *new_head;
    do {
        old_head = atomic_load(&head);
        if (!old_head) return NULL;
        new_head = old_head->next;
    } while (!atomic_compare_exchange_weak(&head, &old_head, new_head));
    return old_head;
}
```

The `compare_exchange_weak` atomically: reads current value, compares to expected, if equal writes new value, returns success/failure. The `weak` variant may spuriously fail (hence the loop) but is faster on some architectures.

**ABA problem**: A CAS-based algorithm can be fooled: value is A, changed to B, changed back to A — the CAS sees A and thinks nothing changed. Solutions: tagged pointers (add a version counter), hazard pointers, or epoch-based reclamation.

---

## Summary: The Integrated Mental Model

The complete mental framework, from problem to production:

```
PROBLEM
  |
  +-- Classify (search/optimize/count/graph?)
  |
  +-- Formalize (exact I/O, constraints, edge cases)
  |
  +-- Decompose (independent subproblems or overlapping?)
  |       |
  |       +-- Independent: Divide and Conquer
  |       +-- Overlapping: Dynamic Programming
  |       +-- Greedy Choice: Greedy Algorithm
  |
  +-- Select Data Structures (what access patterns dominate?)
  |
  +-- Implement (interface first, invariant explicit, base case careful)
  |
  +-- Merge Solutions (what info needed? order matters? efficiency?)
  |
  +-- Verify (prove invariant, trace edge cases, complexity analysis)
  |
  +-- Optimize (memory hierarchy, cache, SIMD, lock-free if needed)
  |
  +-- In Kernel? (no sleep in atomic, spinlock/mutex choice, RCU for reads,
                  GFP flags, no stdlib, error codes, goto cleanup)
  |
  +-- In Rust? (ownership model, safe wrappers for unsafe, repr(C) for FFI,
                Result/Option instead of null/errno, lifetime annotations)
```

Every problem you face can be mapped to this framework. The details change. The structure does not.

The deepest truth: **correctness first, then clarity, then performance**. A fast wrong answer is worse than a slow correct one. A correct but unreadable implementation will be broken the moment someone touches it. Only then optimize, measure, and measure again.

---

*This document covers: Problem Decomposition, Divide and Conquer, Dynamic Programming, Greedy Algorithms, Two Pointers, Sliding Window, Data Structures (Arrays, Linked Lists, Hash Maps, BST, Red-Black Trees, Heaps, Tries, Union-Find), Algorithm Patterns, Complexity Analysis, Linux Kernel Architecture, Kernel Modules, Kernel Memory Management, Kernel Synchronization (Spinlocks, Mutexes, RCU, Atomics), VFS, Scheduler (CFS), Device Drivers, C Systems Patterns (vtable, bit manipulation, safe C), Rust Ownership/Borrowing/Lifetimes/Traits/Unsafe, C-Rust FFI (bindgen, repr(C), safe wrappers), Rust in Linux Kernel, Debugging, and Performance (cache hierarchy, SIMD, lock-free).*
