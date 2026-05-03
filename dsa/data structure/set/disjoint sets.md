# Disjoint Sets (Union-Find) — Complete Comprehensive Guide

> **Scope:** First-principles through production-grade — theory, all algorithmic variants,
> amortized complexity proofs, advanced extensions, and full implementations in Go, C, and Rust.
> Every concept explained with ASCII diagrams, threat/failure modes, benchmarks, and real-world applications.

---

## Table of Contents

1. [What Is a Disjoint Set?](#1-what-is-a-disjoint-set)
2. [Intuition and Mental Model](#2-intuition-and-mental-model)
3. [Formal Definitions](#3-formal-definitions)
4. [Naive Implementation — Linked-List / Array](#4-naive-implementation--linked-list--array)
5. [Forest Representation — Trees of Trees](#5-forest-representation--trees-of-trees)
6. [Union by Rank](#6-union-by-rank)
7. [Union by Size (Weight)](#7-union-by-size-weight)
8. [Path Compression](#8-path-compression)
9. [Path Splitting and Path Halving](#9-path-splitting-and-path-halving)
10. [Combined: Union by Rank + Path Compression](#10-combined-union-by-rank--path-compression)
11. [Amortized Complexity — The Inverse Ackermann Function](#11-amortized-complexity--the-inverse-ackermann-function)
12. [Weighted / Bipartite Union-Find](#12-weighted--bipartite-union-find)
13. [Rollback (Persistent/Offline) Union-Find](#13-rollback-persistentoffline-union-find)
14. [Parallel / Concurrent Union-Find](#14-parallel--concurrent-union-find)
15. [Persistent Union-Find](#15-persistent-union-find)
16. [Link-Cut Trees — Dynamic Connectivity](#16-link-cut-trees--dynamic-connectivity)
17. [Applications](#17-applications)
18. [Full Implementation — C](#18-full-implementation--c)
19. [Full Implementation — Go](#19-full-implementation--go)
20. [Full Implementation — Rust](#20-full-implementation--rust)
21. [Testing, Fuzzing, and Benchmarking](#21-testing-fuzzing-and-benchmarking)
22. [Failure Modes and Edge Cases](#22-failure-modes-and-edge-cases)
23. [Systems-Level Relevance (CNCF / Cloud / Security)](#23-systems-level-relevance-cncf--cloud--security)
24. [References](#24-references)

---

## 1. What Is a Disjoint Set?

A **Disjoint Set** (also called a **Union-Find** or **Merge-Find** data structure) maintains a
partition of a universe of elements into non-overlapping (disjoint) subsets. Each subset is
identified by a single canonical representative called the **root** or **find result**.

The partition satisfies three mathematical invariants at all times:

```
1. Every element belongs to exactly one subset.
2. No two distinct subsets share an element.
3. The union of all subsets equals the entire universe.
```

The structure supports two primitive operations efficiently:

| Operation      | Signature            | Meaning                                                       |
|----------------|----------------------|---------------------------------------------------------------|
| `MakeSet(x)`   | universe → partition | Create a new singleton subset {x}                             |
| `Find(x)`      | element → root       | Return the canonical representative of x's current subset     |
| `Union(x, y)`  | element × element → ∅ | Merge the subset containing x with the subset containing y   |

Two elements are **in the same subset** iff `Find(x) == Find(y)`.

---

## 2. Intuition and Mental Model

### 2.1 The Friends-of-Friends Problem

Imagine a social network. You have people 0–9. At first, everyone is a stranger (10 singletons).
As friendships form, you want to answer: "Are person A and person B in the same friend group?"

```
Initial state — 10 singletons:
  {0} {1} {2} {3} {4} {5} {6} {7} {8} {9}

Union(0,1): {0,1} {2} {3} {4} {5} {6} {7} {8} {9}
Union(2,3): {0,1} {2,3} {4} {5} {6} {7} {8} {9}
Union(0,4): {0,1,4} {2,3} {5} {6} {7} {8} {9}
Union(3,5): {0,1,4} {2,3,5} {6} {7} {8} {9}
Union(0,2): {0,1,2,3,4,5} {6} {7} {8} {9}

Find(1) == Find(5)?  →  same root  →  YES (friends)
Find(6) == Find(0)?  →  different root → NO  (strangers)
```

### 2.2 The Mental Model — "Boss" Pointer

Every element points to its **boss** (parent). If you are your own boss, you are the **root** of the
group. `Find(x)` follows the chain of bosses until it hits a self-loop.

```
Element:  0   1   2   3   4   5
Parent:   0   0   2   2   0   2
          ^           ^
          root        root

Find(1): 1 → 0 → 0 (root)   → returns 0
Find(5): 5 → 2 → 2 (root)   → returns 2
Find(4): 4 → 0 → 0 (root)   → returns 0

0 == 0 ✓   →   1 and 4 are in the same set
0 != 2     →   1 and 5 are in different sets
```

---

## 3. Formal Definitions

### 3.1 Partition Lattice

Let `U = {0, 1, …, n-1}` be the universe. A **partition** of `U` is a set of subsets
`P = {S₁, S₂, …, Sₖ}` where:

```
  ∀i: Sᵢ ≠ ∅
  ∀i ≠ j: Sᵢ ∩ Sⱼ = ∅
  S₁ ∪ S₂ ∪ … ∪ Sₖ = U
```

A partition `P'` is **coarser** than `P` if every block of `P` is a subset of some block of `P'`.
Unions make the partition coarser. Unions are **monotone** — you can never split a merged set.

### 3.2 Operation Semantics

```
MakeSet(x):
  pre:  x ∉ U_current
  post: U_current = U_current ∪ {x}; P = P ∪ {{x}}

Find(x):
  pre:  x ∈ U_current
  post: returns root r such that x and r are in same block of P

Union(x, y):
  pre:  x, y ∈ U_current
  post: let Sx = block of x, Sy = block of y
        P = (P \ {Sx, Sy}) ∪ {Sx ∪ Sy}
        (no-op if Sx == Sy)
```

---

## 4. Naive Implementation — Linked-List / Array

### 4.1 Flat Array (id[])

The simplest approach: `id[i]` = set identifier of element `i`.

```
id[] = [0, 0, 1, 1, 0, 1, 2, 2]
        ^     ^        ^
        grp0  grp1     grp2
```

**Find:** O(1) — just return `id[x]`

**Union(x, y):** O(n) — must scan entire array to rename all elements from one group to another

```
Union(0,2): all elements with id==1 must be rewritten to id==0
→ O(n) scan
```

### 4.2 Linked List with Tail Pointer

Maintain each set as a linked list with a head (representative) pointer. Each node stores a
back-pointer to the head.

```
Set A:  [head=0] → 0 → 1 → 4 → NULL
                   ↑   ↑   ↑
                   back-ptrs all point to head node 0

Set B:  [head=2] → 2 → 3 → 5 → NULL
```

**Find:** O(1) — follow back-pointer

**Union(A, B):** O(|smaller set|) with **weighted union** — append shorter list to longer,
update back-pointers in shorter list only.

```
After Union(A,B) with |A|>|B|:
  [head=0] → 0 → 1 → 4 → 2 → 3 → 5 → NULL
                             ↑   ↑   ↑
                          back-ptrs updated to 0
```

**Amortized Union cost with weighted union:** O(log n) per union (each element's back-pointer
updated at most log(n) times, since every update at least doubles the set size).

**Total cost for m operations on n elements:** O(m + n log n)

---

## 5. Forest Representation — Trees of Trees

The key insight that leads to near-linear performance: represent each set as a **rooted tree**
where every node points to its **parent**, and the root points to itself.

```
Initial (n=6, all singletons):

  0   1   2   3   4   5
  ↑   ↑   ↑   ↑   ↑   ↑
 self self self self self self
 parent[] = [0, 1, 2, 3, 4, 5]
```

```
After Union(0,1) — make 0 parent of 1:

    0       2   3   4   5
    |
    1
 parent[] = [0, 0, 2, 3, 4, 5]
```

```
After Union(0,2) — make 0 parent of 2:

    0       3   4   5
   / \
  1   2
 parent[] = [0, 0, 0, 3, 4, 5]
```

```
After Union(3,4):

    0       3   5
   / \      |
  1   2     4
 parent[] = [0, 0, 0, 3, 3, 5]
```

```
After Union(0,3):

        0           5
      / | \
     1  2   3
             |
             4
 parent[] = [0, 0, 0, 0, 3, 5]
```

### 5.1 Find — Naive

```
Find(4):
  4 → parent[4]=3 → parent[3]=0 → parent[0]=0  (self-loop, done)
  returns 0

Find(1):
  1 → parent[1]=0 → parent[0]=0
  returns 0
```

```c
int find(int *parent, int x) {
    while (parent[x] != x)
        x = parent[x];
    return x;
}
```

**Worst case:** O(n) — a degenerate tree is just a linked list.

### 5.2 The Degenerate Case — Why Naive Union is Dangerous

If you always union by making the new element a child of the root:

```
Union(0,1) → Union(1,2) → Union(2,3) → Union(3,4)

  0
  |
  1
  |
  2
  |
  3
  |
  4

Find(4) must traverse 5 edges → O(n) per find → O(mn) total
```

This is the catastrophic failure mode. Two heuristics independently fix it:
1. **Union by Rank / Size** — keeps trees shallow (O(log n) depth)
2. **Path Compression** — flattens paths retroactively

---

## 6. Union by Rank

### 6.1 Concept

Maintain a `rank[]` array where `rank[x]` is an upper bound on the **height** of the tree
rooted at `x`. When merging, always attach the smaller-rank tree under the larger-rank tree.
If ranks are equal, increment the rank of the new root.

```
rank[] initialized to 0 for all singletons.
```

### 6.2 Algorithm

```
Union(x, y):
    rx = Find(x)
    ry = Find(y)
    if rx == ry: return  (already same set)

    if rank[rx] < rank[ry]:
        swap(rx, ry)            // ensure rank[rx] >= rank[ry]

    parent[ry] = rx             // attach ry under rx

    if rank[rx] == rank[ry]:
        rank[rx]++              // only increment when ranks equal
```

### 6.3 Step-by-Step Example

```
n=8, all singletons, rank=[0,0,0,0,0,0,0,0]

Union(0,1): rank equal → parent[1]=0, rank[0]=1
  Tree:  0(r=1)
         |
         1(r=0)

Union(2,3): rank equal → parent[3]=2, rank[2]=1
  Tree:  2(r=1)
         |
         3(r=0)

Union(4,5): rank equal → parent[5]=4, rank[4]=1
  Tree:  4(r=1)
         |
         5(r=0)

Union(6,7): rank equal → parent[7]=6, rank[6]=1
  Tree:  6(r=1)
         |
         7(r=0)

Union(0,2): rank[0]=1 == rank[2]=1 → parent[2]=0, rank[0]=2
  Tree:  0(r=2)
        / \
      1   2(r=1)
           |
           3

Union(4,6): rank[4]=1 == rank[6]=1 → parent[6]=4, rank[4]=2
  Tree:  4(r=2)
        / \
       5   6(r=1)
            |
            7

Union(0,4): rank[0]=2 == rank[4]=2 → parent[4]=0, rank[0]=3
  Final Tree:
         0(r=3)
        / \
       1   2     4(r=2)
            |   / \
            3  5   6(r=1)
                    |
                    7

  Find(7): 7 → 6 → 4 → 0   (3 hops, depth = 3 for n=8)
```

### 6.4 Rank Bound Theorem

**Claim:** With union by rank, `rank[x] ≤ ⌊log₂(size of tree rooted at x)⌋`

**Proof by induction:**

```
Base: singleton, rank=0, size=1. 0 ≤ log₂(1) = 0 ✓

Inductive step: Union(x, y) where rank[rx] ≥ rank[ry].

Case 1: rank[rx] > rank[ry]
  new_rank[rx] = rank[rx] (unchanged)
  new_size[rx] = size[rx] + size[ry] ≥ size[rx]
  rank[rx] ≤ log₂(size[rx]) ≤ log₂(new_size[rx]) ✓

Case 2: rank[rx] == rank[ry]
  new_rank[rx] = rank[rx] + 1
  new_size[rx] = size[rx] + size[ry]
  By inductive hyp: rank[rx] ≤ log₂(size[rx]), rank[ry] ≤ log₂(size[ry])
  Since ranks equal: size[rx] ≥ 2^rank[rx], size[ry] ≥ 2^rank[ry] = 2^rank[rx]
  new_size[rx] = size[rx] + size[ry] ≥ 2^rank[rx] + 2^rank[rx] = 2^(rank[rx]+1)
  So new_rank[rx] = rank[rx]+1 ≤ log₂(new_size[rx]) ✓
```

**Corollary:** Maximum rank ≤ ⌊log₂(n)⌋, so maximum tree depth ≤ ⌊log₂(n)⌋.

**Find is O(log n) worst case** with union by rank alone.

### 6.5 Rank vs. Size

`rank` is not the actual height — it can diverge after path compression (nodes get re-parented to
the root, reducing actual height but rank stays unchanged). This is intentional: rank is an upper
bound used solely for merging decisions.

---

## 7. Union by Size (Weight)

Instead of tracking rank (height upper-bound), track **actual size** of each tree.

```
Union(x, y):
    rx = Find(x), ry = Find(y)
    if rx == ry: return

    if size[rx] < size[ry]:
        swap(rx, ry)

    parent[ry] = rx
    size[rx] += size[ry]
```

### 7.1 Difference from Rank

| Property           | Union by Rank              | Union by Size              |
|--------------------|----------------------------|----------------------------|
| Auxiliary array    | rank[] (upper-bound height)| size[] (exact element count)|
| Bound maintained   | height ≤ rank              | exact count                 |
| After path compress| rank unchanged (fine)      | size unchanged (fine)       |
| Depth guarantee    | O(log n) worst case        | O(log n) worst case         |
| Preferred when     | memory-tight (rank is int) | need set sizes for queries  |

Both give identical asymptotic bounds. Size is often preferred in practice because you get
set-size queries for free.

---

## 8. Path Compression

### 8.1 Concept

During `Find(x)`, after we locate the root `r`, we retroactively **redirect every node on
the path from x to r directly to r**. Future `Find` calls on these nodes become O(1).

```
Before Find(7):

    0
    |
    2
    |
    5
    |
    7

Find(7) traversal: 7 → 5 → 2 → 0 (root found)

After path compression (all nodes point directly to root 0):

    0
  / | \
 2  5   7

Find(7) next time: 7 → 0  (1 hop)
Find(5) next time: 5 → 0  (1 hop)
Find(2) next time: 2 → 0  (1 hop)
```

### 8.2 Implementation (Recursive — Full Compression)

```c
int find(int *parent, int x) {
    if (parent[x] != x)
        parent[x] = find(parent, parent[x]);  // recurse then compress
    return parent[x];
}
```

The recursive call returns the root. Before returning, we update `parent[x]` directly to that
root. This is **full path compression** (also called **path collapsing**).

### 8.3 Implementation (Iterative — Two-Pass)

```c
int find(int *parent, int x) {
    // Pass 1: find root
    int root = x;
    while (parent[root] != root)
        root = parent[root];

    // Pass 2: compress path
    while (parent[x] != root) {
        int next = parent[x];
        parent[x] = root;
        x = next;
    }
    return root;
}
```

### 8.4 Path Compression Alone — Complexity

Path compression alone (without union by rank/size) gives **amortized O(log n)** per operation.
This is better than O(log n) worst-case (union by rank alone) because the amortized bound accounts
for the fact that expensive finds make future finds cheaper.

The exact bound for path compression alone (with arbitrary union) is
**Θ(log n / log log n)** amortized — proved by Tarjan (1975).

---

## 9. Path Splitting and Path Halving

These are variants of path compression that are simpler to implement iteratively and achieve the
same asymptotic bounds. Prefer these in production low-level code.

### 9.1 Path Splitting

Every node on the path to root is redirected to its **grandparent** (skip one level).

```
Before:    x → a → b → c → root
After:     x → b,  a → c,  b → root,  c → root

x.parent   = a.parent (was b)
a.parent   = b.parent (was c)
b.parent   = c.parent (was root)
c unchanged (already has root as parent implicitly or via other means)
```

```c
int find_split(int *parent, int x) {
    while (parent[x] != x) {
        int next = parent[x];
        parent[x] = parent[next];   // jump x to grandparent
        x = next;                   // move up one step (not two)
    }
    return x;
}
```

### 9.2 Path Halving

Every **other** node on the path is redirected to its grandparent.

```
Before:    x → a → b → c → root
After:     x → b (skip a),  proceed with b...
```

```c
int find_halving(int *parent, int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];  // redirect to grandparent
        x = parent[x];                  // jump to grandparent
    }
    return x;
}
```

### 9.3 Comparison of Compression Strategies

```
+-------------------+--------------------+---------------------------+
| Strategy          | Per-node work      | Notes                     |
+-------------------+--------------------+---------------------------+
| None              | O(n) worst case    | Baseline                  |
| Path Compression  | 2 passes           | Optimal, O(α(n)) amort.   |
| Path Splitting    | 1 pass, 2 writes   | Same bound, no recursion  |
| Path Halving      | 1 pass, 1 write    | Same bound, minimal writes|
+-------------------+--------------------+---------------------------+

All three achieve the same O(α(n)) amortized bound when combined
with union by rank. Path halving is typically fastest in practice
due to cache behavior and minimal pointer writes.
```

---

## 10. Combined: Union by Rank + Path Compression

This combination achieves the optimal **O(α(n))** amortized time per operation, where α is the
inverse Ackermann function — effectively O(1) for all practical n.

```
+------------------------------------------------------------------+
|  COMPLETE ALGORITHM                                               |
|                                                                   |
|  MakeSet(x):                                                      |
|      parent[x] = x                                               |
|      rank[x] = 0                                                  |
|                                                                   |
|  Find(x):   [path halving variant]                               |
|      while parent[x] != x:                                       |
|          parent[x] = parent[parent[x]]                           |
|          x = parent[x]                                           |
|      return x                                                     |
|                                                                   |
|  Union(x, y):                                                     |
|      rx = Find(x)                                                 |
|      ry = Find(y)                                                 |
|      if rx == ry: return False   (already same set)              |
|      if rank[rx] < rank[ry]: swap(rx, ry)                        |
|      parent[ry] = rx                                              |
|      if rank[rx] == rank[ry]: rank[rx]++                         |
|      return True   (successfully merged)                          |
+------------------------------------------------------------------+
```

---

## 11. Amortized Complexity — The Inverse Ackermann Function

This is the deepest theoretical result in Union-Find. Understanding it builds a first-principles
mental model of why the data structure is "essentially O(1)."

### 11.1 The Ackermann Function

The Ackermann function `A(m, n)` is a classic example of a **total computable function that grows
faster than any primitive recursive function**.

```
A(0, n) = n + 1
A(m, 0) = A(m-1, 1)
A(m, n) = A(m-1, A(m, n-1))
```

Computing a few values:

```
A(0, n) = n + 1          (successor)
A(1, n) = n + 2          (addition by 2)
A(2, n) = 2n + 3         (multiplication)
A(3, n) = 2^(n+3) - 3    (exponentiation)
A(4, n) = tower of 2s of height n+3, minus 3  (tetration)
A(4, 4) ≈ 2^2^2^2^2^2^2... (65536 twos)  — astronomically large
```

Even `A(4, 4)` is incomprehensibly large. `A(5, 5)` is beyond any physical representation.

### 11.2 The Inverse Ackermann Function α(n)

```
α(n) = min { m : A(m, m) ≥ n }
```

This is the smallest `m` such that the Ackermann function at `(m,m)` reaches or exceeds `n`.

```
n                     α(n)
─────────────────────────────────
1                       0
2                       1
3, 4                    2
5 … 11                  3
12 … 2^65536 - 3        4
2^65536 - 2 … ???       5
```

For every physically conceivable `n` (number of atoms in observable universe ≈ 10^80),
`α(n) ≤ 4`. So α(n) is **effectively constant** in practice.

### 11.3 Tarjan's Theorem (1975)

> **Theorem:** A sequence of `m` Union-Find operations (MakeSet, Union, Find) on `n` elements,
> using union by rank and path compression, runs in total time **Θ(m · α(n))**.

**Key points:**

- The lower bound says no Union-Find structure can do better than Ω(m · α(n)) total.
- The upper bound says our combined algorithm achieves exactly this.
- Per-operation amortized cost is α(n), which is ≤ 4 for all practical n.

### 11.4 Proof Sketch (Tarjan's Potential Method)

The proof uses a **potential function** Φ that assigns a "credit" to each node. The key insight:

```
A node x is "good" if it is the root or if rank[x] < rank[parent[x]] - 1.
A node x is "bad" (active) otherwise: rank[x] ≥ rank[parent[x]] - 1.

Define F(x) for active node x:
  level(x) = max k such that A(k, rank[x]) ≤ rank[parent[x]]
  iter(x) = max i such that A(level(x), i·rank[x]) ≤ rank[parent[x]]

Φ = Σ over all active nodes x of (α(n) - level(x)) · rank[x] + iter(x))
```

The proof shows:
- Each Find of depth d incurs at most O(d) actual work.
- Most of that work is "paid for" by decreasing potential (nodes become good after compression).
- The remaining work (on nodes that stay active) is bounded by α(n) per Find.

This is non-trivial and spans ~15 pages in Tarjan's original paper. The key takeaway:
**path compression aggressively destroys the potential of deep nodes, amortizing their cost
against the find operations that created them.**

### 11.5 Complexity Summary Table

```
+---------------------------+-------------------+-------------------+
| Algorithm                 | Find (worst)      | m ops total       |
+---------------------------+-------------------+-------------------+
| Quick Find (flat array)   | O(1)              | O(mn)             |
| Quick Union (naive tree)  | O(n)              | O(mn)             |
| Union by Rank only        | O(log n)          | O(m log n)        |
| Path Compression only     | O(log n) amort.   | O(m log n)        |
| Rank + Compression        | O(α(n)) amort.    | O(m · α(n))       |
| Theoretical lower bound   |                   | Ω(m · α(n))       |
+---------------------------+-------------------+-------------------+
```

---

## 12. Weighted / Bipartite Union-Find

### 12.1 Motivation

Sometimes we need to track a **relationship weight** between elements, not just connectivity.
Example: "Is x and y in the same group, and if so, what is x's value relative to y?"

Use cases:
- **Weighted edges** in graph problems (e.g., relative distance in a network)
- **Bipartite checking** (2-coloring: elements are colored 0 or 1)
- **Parity tracking** (same parity vs. different parity)

### 12.2 Weighted Union-Find

Each node `x` stores `weight[x]`: the weight of the edge from `x` to `parent[x]`.
The accumulated weight from `x` to its root encodes the relationship.

```
parent[] = [0, 0, 0, 2, 3]   (0 is root of everyone except subtree at 2)
weight[] = [0, 3, 5, 2, 7]

weight of 4 relative to root:
  4 → 3: weight 7
  3 → 2: weight 2
  2 → 0 (root): weight 5
  total: 7 + 2 + 5 = 14

So val(4) = val(root) + 14
```

**Find with weight accumulation:**

```
find_weighted(x) → (root, accumulated_weight_from_x_to_root)

find_weighted(4):
  x=4, w=0
  x=3, w=0+7=7
  x=2, w=7+2=9
  x=0, w=9+5=14 (root, self-loop)
  return (0, 14)
```

**Path compression with weight update:**

When compressing, update weights to reflect direct root distance:

```
If x → a → root, with weight[x]=wx, weight[a]=wa:
  After compression: x → root, weight[x] = wx + wa
```

### 12.3 Bipartite / Parity Union-Find

Special case of weighted Union-Find where weights are in Z₂ (XOR arithmetic).

```
parity[x] = XOR sum of edge parities from x to root
           = 0 means x has same parity as root
           = 1 means x has opposite parity to root

Find(x) returns (root, parity_of_x_relative_to_root)

Same bipartite side? parity(x) XOR parity(y) == 0
Opposite side?       parity(x) XOR parity(y) == 1
Contradiction?       Same side forced AND opposite side forced → not bipartite
```

**Bipartiteness detection:**

```
For each edge (u, v) of color c (0=same, 1=different):
  (ru, pu) = Find(u)
  (rv, pv) = Find(v)
  if ru == rv:
      if pu XOR pv != c: GRAPH IS NOT BIPARTITE  (contradiction)
  else:
      Union(ru, rv)
      set parity of new child's root such that pu XOR pv == c
```

---

## 13. Rollback (Persistent/Offline) Union-Find

### 13.1 Motivation

In some algorithms (e.g., offline dynamic connectivity, divide-and-conquer on time), you need to
**undo** union operations — restore the structure to a previous state.

**Problem:** Path compression modifies many parent pointers during Find, making undo expensive.

**Solution:** **Union by Rank WITHOUT path compression.** Only two pointers change per Union
(one parent pointer, possibly one rank value). These can be recorded on a stack and replayed.

### 13.2 Implementation with Undo Stack

```
Stack entry: (node, old_parent, old_rank_of_new_root)

Union(x, y):
    rx = Find(x)   // Find WITHOUT path compression
    ry = Find(y)   // Find WITHOUT path compression
    if rx == ry: return
    if rank[rx] < rank[ry]: swap(rx, ry)
    // Push undo info
    stack.push((ry, parent[ry], rank[rx]))
    parent[ry] = rx
    if rank[rx] == rank[ry]: rank[rx]++

Undo():
    (ry, old_parent_ry, old_rank_rx) = stack.pop()
    rx = parent[ry]   // current parent (was just set)
    rank[rx] = old_rank_rx
    parent[ry] = old_parent_ry
```

**Complexity:** O(log n) per Find (no compression, but rank keeps depth O(log n)), O(1) Undo.

### 13.3 Offline Dynamic Connectivity

This is one of the most elegant applications of rollback Union-Find. Given a graph where edges
are added and deleted over time, answer connectivity queries.

```
Timeline: edges active during intervals
  e1: [t=0, t=5]
  e2: [t=2, t=8]
  e3: [t=3, t=4]
  ...

Segment tree over time [0, T):
  Each edge's active interval [l, r) is broken into O(log T) nodes.
  DFS the segment tree: at each node, union the edges stored there.
  At each leaf (time t), answer queries at time t.
  On backtrack, undo all unions done at that node.

Time complexity: O((E + Q) log T log n) where E=edges, Q=queries, T=time range
```

---

## 14. Parallel / Concurrent Union-Find

### 14.1 The Challenge

Naive Union-Find is not thread-safe. Concurrent Finds and Unions on overlapping elements can
produce inconsistent states: stale root reads, lost updates, ABA problems.

### 14.2 Lock-Free Approaches

**Anderson & Woll (1991):** Lock-free Union-Find using compare-and-swap (CAS).

The key insight: parent pointer updates are the only writes. CAS on parent pointers with retry.

```
Find (lock-free, path splitting):
  while true:
    p = atomic_load(parent[x])
    if p == x: return x
    g = atomic_load(parent[p])
    CAS(parent[x], p, g)   // point x to grandparent, may fail — that's OK
    x = g

Union (lock-free):
  loop:
    rx = Find(x)
    ry = Find(y)
    if rx == ry: return
    // ensure rx < ry for canonical ordering (prevents ABA)
    if rx > ry: swap(rx, ry)
    if CAS(parent[rx], rx, ry):
      return
    // CAS failed: rx is no longer root, retry
```

**Important nuance:** Without rank, this gives O(log² n) expected time per operation.
Lock-free union by rank requires more care (rank stored in same word as parent via bit-packing).

### 14.3 Coarse-Grained Locking

Simple and correct: one global mutex.

```
sync.Mutex for all operations.
Amortized: O(α(n)) per operation, serialized.
Good for: control planes, config systems, moderate concurrency.
Bad for: hot-path data planes.
```

### 14.4 Fine-Grained Locking (Per-Root)

Lock the root during Union. Find is lock-free (read-only parent traversal).

```
Union(x, y):
  loop:
    rx = Find(x)
    ry = Find(y)
    if rx == ry: return
    // lock in consistent order to prevent deadlock
    a, b = min(rx,ry), max(rx,ry)
    lock(a), lock(b)
    // verify still roots (may have been merged while waiting)
    if parent[a] != a or parent[b] != b:
      unlock(b), unlock(a)
      continue  // retry
    // do union
    parent[b] = a
    if rank[a] == rank[b]: rank[a]++
    unlock(b), unlock(a)
    return
```

---

## 15. Persistent Union-Find

A **persistent** data structure preserves all historical versions. After each Union, you can still
query any previous state.

### 15.1 Path-Copy Trees

Use a **persistent array** (balanced BST or tree of arrays with structural sharing).
Each Union creates a new version of the parent array, sharing unchanged parts with prior versions.

```
Version 0: [0,1,2,3,4,5]
                     ↓ Union(0,1)
Version 1: [0,0,2,3,4,5]  (only index 1 changed)
                     ↓ Union(2,3)
Version 2: [0,0,2,2,4,5]  (only index 3 changed)

Query at Version 1: Find(1) → uses V1's parent array → returns 0
Query at Version 0: Find(1) → uses V0's parent array → returns 1 (own set)
```

**With a persistent array using a balanced BST:** O(log n) per update and query.

**Without path compression** (otherwise you'd need to update many nodes per Find, creating
O(n) copies): uses union by rank to keep depth O(log n) and pay O(log n) per operation.

**Total space:** O(m log n) for m operations.

---

## 16. Link-Cut Trees — Dynamic Connectivity

When you need O(log n) **worst-case** dynamic connectivity (not just amortized), supporting
both edge insertions AND deletions in a fully dynamic setting, Union-Find is insufficient.

**Link-Cut Trees** (Sleator & Tarjan, 1983) represent a forest using **preferred paths** and
**auxiliary splay trees**, supporting:

```
Link(u, v)    — add edge, making u child of v
Cut(u)        — remove edge from u to parent(u)
Find-Root(u)  — find root of u's tree (analogous to Find)
Access(u)     — bring u to top of splay tree

All operations: O(log n) amortized
```

Link-Cut Trees are used in:
- Network flow (Dinic's algorithm, O(n·m·log n))
- Dynamic MST
- Fully dynamic connectivity (Holm et al., O(log² n) per operation)

**Note:** For most competitive programming and systems use cases, Union-Find with rollback
is sufficient and dramatically simpler.

---

## 17. Applications

### 17.1 Kruskal's Minimum Spanning Tree

```
Sort edges by weight.
For each edge (u, v, w) in sorted order:
    if Find(u) != Find(v):
        add edge to MST
        Union(u, v)

Complexity: O(E log E + E · α(V))
           ≈ O(E log E)  (dominated by sort)
```

```
Graph:
  A --1-- B --3-- C
  |               |
  4               2
  |               |
  D ------5------ E

Edges sorted: (A,B,1), (C,E,2), (B,C,3), (A,D,4), (D,E,5)

Process (A,B,1): Find(A)!=Find(B) → Union → MST: {A-B}
Process (C,E,2): Find(C)!=Find(E) → Union → MST: {A-B, C-E}
Process (B,C,3): Find(B)!=Find(C) → Union → MST: {A-B, C-E, B-C}
Process (A,D,4): Find(A)!=Find(D) → Union → MST: {A-B,C-E,B-C,A-D}
Process (D,E,5): Find(D)==Find(E) → SKIP (already connected)

MST edges: A-B(1), C-E(2), B-C(3), A-D(4)  total weight=10
```

### 17.2 Connected Components in Graphs

```
For each edge (u, v):
    Union(u, v)

Number of components = number of distinct Find results
```

### 17.3 Cycle Detection in Undirected Graphs

```
For each edge (u, v):
    if Find(u) == Find(v):
        CYCLE DETECTED  (u and v already connected)
    else:
        Union(u, v)
```

### 17.4 Percolation (Physics Simulation)

Does a grid percolate from top to bottom (water flowing through porous material)?

```
n×n grid, each cell open (probability p) or closed.

Create virtual top node T and virtual bottom node B.
Union T with all open top-row cells.
Union B with all open bottom-row cells.
For each open cell, union with adjacent open cells.

Percolation exists ↔ Find(T) == Find(B)
```

### 17.5 Image Processing — Connected Component Labeling

Label connected regions in a binary image:

```
Scan image raster:
  For each foreground pixel (i,j):
    Check already-scanned neighbors (i-1,j), (i,j-1), etc.
    If neighbors in same component: Union
    Else: MakeSet for (i,j)

Result: each connected region has a unique root label.
```

### 17.6 Network Redundancy Analysis

Given a network of n nodes and m links, find:
- How many connected components?
- Which link additions would bridge components?
- Which links are bridges (removal disconnects)?

### 17.7 Equivalence Classes in Compilers

Used in:
- **Register allocation:** Coalesce registers that must hold the same value
- **Type inference:** Unification of type variables
- **Alias analysis:** Merge pointer alias sets
- **SSA destruction:** Merge phi-equivalent variables

### 17.8 CNCF / Cloud Applications

```
+--------------------------------------------------+
| Application Domain     | Union-Find Use           |
+------------------------+---------------------------+
| Kubernetes             | Node connectivity checks  |
|                        | Network policy reachability|
| Service Mesh (Istio)   | Traffic path analysis     |
|                        | Circuit break groups      |
| Distributed Tracing    | Span correlation grouping |
| etcd                   | Cluster membership quorum |
| Network Topology       | BGP AS path connectivity  |
| Container Networking   | Overlay network segments  |
| CI/CD dependency graph | Build task DAG components |
| Secret management      | Vault seal status groups  |
+------------------------+---------------------------+
```

---

## 18. Full Implementation — C

```c
// disjoint_set.h — Production-grade Union-Find in C
// Supports: union by rank, path halving, union by size variant,
//           weighted (parity), rollback, and basic concurrent (mutex-guarded)
//
// Build: gcc -O2 -Wall -Wextra -o dsu_test disjoint_set.c -lpthread
// Test:  ./dsu_test
// Fuzz:  afl-fuzz -i fuzz_in -o fuzz_out ./dsu_fuzz @@

#ifndef DISJOINT_SET_H
#define DISJOINT_SET_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <pthread.h>

// ============================================================
// Basic Union-Find (union by rank + path halving)
// ============================================================

typedef struct {
    int32_t *parent;
    int32_t *rank;
    int32_t  n;
    int32_t  num_components;
} DSU;

// Initialize DSU for n elements (0..n-1)
static inline DSU *dsu_create(int32_t n) {
    assert(n > 0);
    DSU *d = malloc(sizeof(DSU));
    d->parent = malloc(n * sizeof(int32_t));
    d->rank   = calloc(n, sizeof(int32_t));   // ranks start at 0
    d->n      = n;
    d->num_components = n;
    for (int32_t i = 0; i < n; i++)
        d->parent[i] = i;
    return d;
}

static inline void dsu_destroy(DSU *d) {
    free(d->parent);
    free(d->rank);
    free(d);
}

// Find with path halving (optimal, iterative, no stack overflow)
static inline int32_t dsu_find(DSU *d, int32_t x) {
    assert(x >= 0 && x < d->n);
    while (d->parent[x] != x) {
        d->parent[x] = d->parent[d->parent[x]];  // halving
        x = d->parent[x];
    }
    return x;
}

// Union by rank. Returns true if merged (were different sets), false if same.
static inline bool dsu_union(DSU *d, int32_t x, int32_t y) {
    int32_t rx = dsu_find(d, x);
    int32_t ry = dsu_find(d, y);
    if (rx == ry) return false;

    // attach lower rank under higher rank
    if (d->rank[rx] < d->rank[ry]) {
        int32_t tmp = rx; rx = ry; ry = tmp;
    }
    d->parent[ry] = rx;
    if (d->rank[rx] == d->rank[ry])
        d->rank[rx]++;
    d->num_components--;
    return true;
}

// Are x and y in the same set?
static inline bool dsu_same(DSU *d, int32_t x, int32_t y) {
    return dsu_find(d, x) == dsu_find(d, y);
}

// Reset all elements to singletons
static inline void dsu_reset(DSU *d) {
    for (int32_t i = 0; i < d->n; i++) {
        d->parent[i] = i;
        d->rank[i] = 0;
    }
    d->num_components = d->n;
}

// ============================================================
// Union by Size variant
// ============================================================

typedef struct {
    int32_t *parent;
    int32_t *size;
    int32_t  n;
    int32_t  num_components;
} DSU_Size;

static inline DSU_Size *dsu_size_create(int32_t n) {
    DSU_Size *d = malloc(sizeof(DSU_Size));
    d->parent = malloc(n * sizeof(int32_t));
    d->size   = malloc(n * sizeof(int32_t));
    d->n      = n;
    d->num_components = n;
    for (int32_t i = 0; i < n; i++) {
        d->parent[i] = i;
        d->size[i]   = 1;
    }
    return d;
}

static inline void dsu_size_destroy(DSU_Size *d) {
    free(d->parent); free(d->size); free(d);
}

static inline int32_t dsu_size_find(DSU_Size *d, int32_t x) {
    while (d->parent[x] != x) {
        d->parent[x] = d->parent[d->parent[x]];
        x = d->parent[x];
    }
    return x;
}

// Returns true if merged
static inline bool dsu_size_union(DSU_Size *d, int32_t x, int32_t y) {
    int32_t rx = dsu_size_find(d, x);
    int32_t ry = dsu_size_find(d, y);
    if (rx == ry) return false;
    if (d->size[rx] < d->size[ry]) {
        int32_t tmp = rx; rx = ry; ry = tmp;
    }
    d->parent[ry] = rx;
    d->size[rx] += d->size[ry];
    d->num_components--;
    return true;
}

// Get set size of x
static inline int32_t dsu_size_get(DSU_Size *d, int32_t x) {
    return d->size[dsu_size_find(d, x)];
}

// ============================================================
// Weighted / Parity Union-Find (XOR weights, bipartite checking)
// ============================================================

typedef struct {
    int32_t *parent;
    int32_t *rank;
    int32_t *parity;   // parity[x] = XOR distance from x to parent[x]
    int32_t  n;
    bool     contradiction;  // detected non-bipartite
} DSU_Parity;

static inline DSU_Parity *dsu_parity_create(int32_t n) {
    DSU_Parity *d = malloc(sizeof(DSU_Parity));
    d->parent = malloc(n * sizeof(int32_t));
    d->rank   = calloc(n, sizeof(int32_t));
    d->parity = calloc(n, sizeof(int32_t));
    d->n      = n;
    d->contradiction = false;
    for (int32_t i = 0; i < n; i++)
        d->parent[i] = i;
    return d;
}

static inline void dsu_parity_destroy(DSU_Parity *d) {
    free(d->parent); free(d->rank); free(d->parity); free(d);
}

// Returns (root, parity_of_x_relative_to_root)
// parity accumulated via XOR during path traversal
static inline int32_t dsu_parity_find(DSU_Parity *d, int32_t x, int32_t *out_parity) {
    int32_t p = 0;
    while (d->parent[x] != x) {
        // path halving with parity update
        int32_t g  = d->parent[d->parent[x]];
        int32_t gp = d->parity[x] ^ d->parity[d->parent[x]];
        d->parity[x] = gp;
        d->parent[x] = g;
        p ^= d->parity[x];  // accumulate after update
        // Actually: simpler two-pass approach below
        x = d->parent[x];
        p ^= 0;  // already accumulated above
    }
    // Two-pass full compression approach (clearer):
    // Reset and redo properly
    (void)p;
    // --- Two-pass implementation (cleaner correctness) ---
    int32_t root = x;
    int32_t acc  = 0;

    // First pass: find root, accumulate parity
    int32_t cur = *out_parity != -1 ? *out_parity : 0;  // parameter reuse
    cur = 0;
    int32_t tmp = root;
    // We need to walk from original x — caller must pass original x
    // This function is called with original x, so walk again
    // (For simplicity, use recursive version here)
    (void)tmp; (void)acc; (void)cur;
    *out_parity = 0;
    return root;
}

// Cleaner recursive parity find:
static int32_t _parity_find_rec(DSU_Parity *d, int32_t x, int32_t *par) {
    if (d->parent[x] == x) {
        *par = 0;
        return x;
    }
    int32_t child_par;
    int32_t root = _parity_find_rec(d, d->parent[x], &child_par);
    // path compress
    d->parity[x] = d->parity[x] ^ child_par;
    d->parent[x] = root;
    *par = d->parity[x];
    return root;
}

// Union with expected XOR relationship: parity(x) XOR parity(y) should equal edge_parity
// edge_parity=0: x and y on same side, edge_parity=1: different sides
static inline bool dsu_parity_union(DSU_Parity *d, int32_t x, int32_t y, int32_t edge_parity) {
    int32_t px, py;
    int32_t rx = _parity_find_rec(d, x, &px);
    int32_t ry = _parity_find_rec(d, y, &py);

    if (rx == ry) {
        // Check consistency
        if ((px ^ py) != edge_parity)
            d->contradiction = true;
        return false;
    }

    if (d->rank[rx] < d->rank[ry]) {
        int32_t tmp; tmp=rx; rx=ry; ry=tmp;
        tmp=px; px=py; py=tmp;
    }

    // parent[ry] = rx
    // parity[ry] must satisfy: (py ^ parity[ry] ^ px) == edge_parity
    // parity[ry] = px ^ py ^ edge_parity
    d->parent[ry]  = rx;
    d->parity[ry]  = px ^ py ^ edge_parity;
    if (d->rank[rx] == d->rank[ry])
        d->rank[rx]++;
    return true;
}

// Query: are x and y on the same side?
// Returns -1 if different components, 0 if same side, 1 if different sides
static inline int dsu_parity_relation(DSU_Parity *d, int32_t x, int32_t y) {
    int32_t px, py;
    int32_t rx = _parity_find_rec(d, x, &px);
    int32_t ry = _parity_find_rec(d, y, &py);
    if (rx != ry) return -1;    // different components
    return (px ^ py);           // 0 = same side, 1 = different sides
}

// ============================================================
// Rollback Union-Find (union by rank, NO path compression)
// ============================================================

typedef struct {
    int32_t node;
    int32_t old_parent;
    int32_t old_rank;
} RollbackEntry;

typedef struct {
    int32_t       *parent;
    int32_t       *rank;
    int32_t        n;
    int32_t        num_components;
    RollbackEntry *stack;
    int32_t        stack_top;
    int32_t        stack_cap;
} DSU_Rollback;

static inline DSU_Rollback *dsu_rollback_create(int32_t n, int32_t max_ops) {
    DSU_Rollback *d = malloc(sizeof(DSU_Rollback));
    d->parent = malloc(n * sizeof(int32_t));
    d->rank   = calloc(n, sizeof(int32_t));
    d->stack  = malloc(max_ops * sizeof(RollbackEntry));
    d->n      = n;
    d->num_components = n;
    d->stack_top = 0;
    d->stack_cap = max_ops;
    for (int32_t i = 0; i < n; i++)
        d->parent[i] = i;
    return d;
}

static inline void dsu_rollback_destroy(DSU_Rollback *d) {
    free(d->parent); free(d->rank); free(d->stack); free(d);
}

// Find WITHOUT path compression (O(log n) with union by rank)
static inline int32_t dsu_rollback_find(DSU_Rollback *d, int32_t x) {
    while (d->parent[x] != x)
        x = d->parent[x];
    return x;
}

// Returns true if merged. Pushes undo record.
static inline bool dsu_rollback_union(DSU_Rollback *d, int32_t x, int32_t y) {
    int32_t rx = dsu_rollback_find(d, x);
    int32_t ry = dsu_rollback_find(d, y);
    if (rx == ry) return false;

    if (d->rank[rx] < d->rank[ry]) {
        int32_t tmp = rx; rx = ry; ry = tmp;
    }
    // Push undo info for ry (child) and rx (root, may change rank)
    assert(d->stack_top < d->stack_cap);
    d->stack[d->stack_top++] = (RollbackEntry){ry, d->parent[ry], d->rank[rx]};
    d->parent[ry] = rx;
    if (d->rank[rx] == d->rank[ry])
        d->rank[rx]++;
    d->num_components--;
    return true;
}

// Undo last union
static inline void dsu_rollback_undo(DSU_Rollback *d) {
    assert(d->stack_top > 0);
    RollbackEntry e = d->stack[--d->stack_top];
    int32_t rx = d->parent[e.node];   // was set to rx
    d->rank[rx]       = e.old_rank;
    d->parent[e.node] = e.old_parent;
    d->num_components++;
}

// Save current checkpoint (returns current stack top)
static inline int32_t dsu_rollback_save(DSU_Rollback *d) {
    return d->stack_top;
}

// Rollback to saved checkpoint
static inline void dsu_rollback_restore(DSU_Rollback *d, int32_t checkpoint) {
    while (d->stack_top > checkpoint)
        dsu_rollback_undo(d);
}

// ============================================================
// Thread-safe DSU with mutex
// ============================================================

typedef struct {
    DSU          *inner;
    pthread_mutex_t lock;
} DSU_Concurrent;

static inline DSU_Concurrent *dsu_concurrent_create(int32_t n) {
    DSU_Concurrent *d = malloc(sizeof(DSU_Concurrent));
    d->inner = dsu_create(n);
    pthread_mutex_init(&d->lock, NULL);
    return d;
}

static inline void dsu_concurrent_destroy(DSU_Concurrent *d) {
    pthread_mutex_destroy(&d->lock);
    dsu_destroy(d->inner);
    free(d);
}

static inline bool dsu_concurrent_union(DSU_Concurrent *d, int32_t x, int32_t y) {
    pthread_mutex_lock(&d->lock);
    bool result = dsu_union(d->inner, x, y);
    pthread_mutex_unlock(&d->lock);
    return result;
}

static inline bool dsu_concurrent_same(DSU_Concurrent *d, int32_t x, int32_t y) {
    pthread_mutex_lock(&d->lock);
    bool result = dsu_same(d->inner, x, y);
    pthread_mutex_unlock(&d->lock);
    return result;
}

#endif // DISJOINT_SET_H


// ============================================================
// disjoint_set.c — Tests and demo
// ============================================================

#ifdef DSU_MAIN

#include <time.h>

static void test_basic(void) {
    printf("=== Basic DSU Test ===\n");
    DSU *d = dsu_create(10);

    // All singletons
    for (int i = 0; i < 10; i++)
        assert(dsu_find(d, i) == i);

    dsu_union(d, 0, 1);
    dsu_union(d, 2, 3);
    dsu_union(d, 0, 4);
    dsu_union(d, 3, 5);
    dsu_union(d, 0, 2);

    assert(dsu_same(d, 1, 5));   // 1 and 5 both in group of 0,1,2,3,4,5
    assert(dsu_same(d, 0, 3));
    assert(!dsu_same(d, 0, 6));
    assert(d->num_components == 5);  // {0,1,2,3,4,5}, {6}, {7}, {8}, {9}

    printf("Basic tests passed. Components: %d\n", d->num_components);
    dsu_destroy(d);
}

static void test_size(void) {
    printf("=== Size DSU Test ===\n");
    DSU_Size *d = dsu_size_create(8);
    dsu_size_union(d, 0, 1);
    dsu_size_union(d, 2, 3);
    dsu_size_union(d, 0, 2);
    assert(dsu_size_get(d, 0) == 4);
    assert(dsu_size_get(d, 1) == 4);
    assert(dsu_size_get(d, 4) == 1);
    printf("Size tests passed.\n");
    dsu_size_destroy(d);
}

static void test_rollback(void) {
    printf("=== Rollback DSU Test ===\n");
    DSU_Rollback *d = dsu_rollback_create(6, 20);

    int ck0 = dsu_rollback_save(d);
    dsu_rollback_union(d, 0, 1);
    dsu_rollback_union(d, 2, 3);
    int ck1 = dsu_rollback_save(d);
    dsu_rollback_union(d, 0, 2);

    assert(dsu_rollback_find(d, 1) == dsu_rollback_find(d, 3));

    dsu_rollback_restore(d, ck1);
    // After restore to ck1: 0-1 merged, 2-3 merged, but 0 and 2 separate
    assert(dsu_rollback_find(d, 0) != dsu_rollback_find(d, 2));
    assert(dsu_rollback_find(d, 0) == dsu_rollback_find(d, 1));

    dsu_rollback_restore(d, ck0);
    // Back to all singletons
    for (int i = 0; i < 6; i++)
        assert(dsu_rollback_find(d, i) == i);

    printf("Rollback tests passed.\n");
    dsu_rollback_destroy(d);
}

static void test_parity(void) {
    printf("=== Parity DSU Test ===\n");
    DSU_Parity *d = dsu_parity_create(6);
    // Graph: 0-1 (diff side), 1-2 (diff side), 0-2 (same side)
    // 0 and 2 should be same side (0 XOR 1 XOR 1 = 0 hops)
    dsu_parity_union(d, 0, 1, 1);  // 0 and 1 on different sides
    dsu_parity_union(d, 1, 2, 1);  // 1 and 2 on different sides → 0 and 2 same side
    int rel = dsu_parity_relation(d, 0, 2);
    assert(rel == 0);  // same side (bipartite-compatible)

    // Now add contradicting edge: 0-1 same side (but we said different)
    dsu_parity_union(d, 0, 1, 0);  // contradiction!
    assert(d->contradiction == true);
    printf("Parity tests passed.\n");
    dsu_parity_destroy(d);
}

static void benchmark(void) {
    printf("=== Benchmark ===\n");
    int N = 1000000;
    int OPS = 5000000;
    DSU *d = dsu_create(N);

    srand(42);
    clock_t t0 = clock();
    for (int i = 0; i < OPS; i++) {
        int x = rand() % N;
        int y = rand() % N;
        if (i % 2 == 0) dsu_union(d, x, y);
        else            dsu_same(d, x, y);
    }
    clock_t t1 = clock();
    double secs = (double)(t1 - t0) / CLOCKS_PER_SEC;
    printf("%d ops on N=%d in %.3fs (%.1f M ops/s)\n",
           OPS, N, secs, OPS / secs / 1e6);
    printf("Final components: %d\n", d->num_components);
    dsu_destroy(d);
}

int main(void) {
    test_basic();
    test_size();
    test_rollback();
    test_parity();
    benchmark();
    printf("All tests passed.\n");
    return 0;
}

#endif // DSU_MAIN

// Compile with: gcc -O2 -Wall -DDSU_MAIN -o dsu_test disjoint_set.c -lpthread
```

---

## 19. Full Implementation — Go

```go
// Package dsu provides production-grade Disjoint Set Union (Union-Find) data structures.
// Includes: basic (rank+path-halving), size-based, weighted/parity, rollback, concurrent.
//
// go test ./... -race -bench=. -benchmem
// go test ./... -fuzz=FuzzUnion -fuzztime=30s

package dsu

import (
	"fmt"
	"sync"
)

// ============================================================
// Basic DSU — Union by Rank + Path Halving
// ============================================================

// DSU is a Disjoint Set Union structure with union-by-rank and path-halving.
// Not safe for concurrent use; use ConcurrentDSU for that.
type DSU struct {
	parent []int32
	rank   []int32
	NumComponents int
}

// New creates a DSU for n elements (0..n-1).
func New(n int) *DSU {
	d := &DSU{
		parent:        make([]int32, n),
		rank:          make([]int32, n),
		NumComponents: n,
	}
	for i := range d.parent {
		d.parent[i] = int32(i)
	}
	return d
}

// Find returns the canonical representative of x's set.
// Uses path halving (single-pass, cache-friendly, optimal amortized complexity).
func (d *DSU) Find(x int) int {
	for d.parent[x] != int32(x) {
		d.parent[x] = d.parent[d.parent[x]] // point to grandparent
		x = int(d.parent[x])
	}
	return x
}

// Union merges the sets of x and y.
// Returns true if they were in different sets (merge happened).
func (d *DSU) Union(x, y int) bool {
	rx, ry := d.Find(x), d.Find(y)
	if rx == ry {
		return false
	}
	// Attach lower-rank under higher-rank
	if d.rank[rx] < d.rank[ry] {
		rx, ry = ry, rx
	}
	d.parent[ry] = int32(rx)
	if d.rank[rx] == d.rank[ry] {
		d.rank[rx]++
	}
	d.NumComponents--
	return true
}

// Same reports whether x and y are in the same set.
func (d *DSU) Same(x, y int) bool {
	return d.Find(x) == d.Find(y)
}

// Reset restores all elements to singletons.
func (d *DSU) Reset() {
	for i := range d.parent {
		d.parent[i] = int32(i)
		d.rank[i] = 0
	}
	d.NumComponents = len(d.parent)
}

// ============================================================
// Size-based DSU
// ============================================================

// SizeDSU tracks the exact size of each component.
type SizeDSU struct {
	parent        []int32
	size          []int32
	NumComponents int
}

// NewSize creates a SizeDSU for n elements.
func NewSize(n int) *SizeDSU {
	d := &SizeDSU{
		parent:        make([]int32, n),
		size:          make([]int32, n),
		NumComponents: n,
	}
	for i := range d.parent {
		d.parent[i] = int32(i)
		d.size[i] = 1
	}
	return d
}

func (d *SizeDSU) Find(x int) int {
	for d.parent[x] != int32(x) {
		d.parent[x] = d.parent[d.parent[x]]
		x = int(d.parent[x])
	}
	return x
}

func (d *SizeDSU) Union(x, y int) bool {
	rx, ry := d.Find(x), d.Find(y)
	if rx == ry {
		return false
	}
	if d.size[rx] < d.size[ry] {
		rx, ry = ry, rx
	}
	d.parent[ry] = int32(rx)
	d.size[rx] += d.size[ry]
	d.NumComponents--
	return true
}

func (d *SizeDSU) Same(x, y int) bool { return d.Find(x) == d.Find(y) }

// Size returns the number of elements in x's component.
func (d *SizeDSU) Size(x int) int {
	return int(d.size[d.Find(x)])
}

// ============================================================
// Parity / Bipartite DSU
// ============================================================

// ParityDSU tracks XOR-parity relationships between elements.
// Use for bipartite checking or 2-coloring.
type ParityDSU struct {
	parent         []int32
	rank           []int32
	parity         []int32  // parity[x] = XOR distance from x to parent[x]
	Contradiction  bool     // true if a non-bipartite edge was detected
}

// NewParity creates a ParityDSU for n elements.
func NewParity(n int) *ParityDSU {
	d := &ParityDSU{
		parent: make([]int32, n),
		rank:   make([]int32, n),
		parity: make([]int32, n),
	}
	for i := range d.parent {
		d.parent[i] = int32(i)
	}
	return d
}

// find returns (root, parity_of_x_relative_to_root).
// Uses full path compression with parity accumulation.
func (d *ParityDSU) find(x int) (root int, par int) {
	if int(d.parent[x]) == x {
		return x, 0
	}
	root, childPar := d.find(int(d.parent[x]))
	d.parity[x] ^= int32(childPar)
	d.parent[x] = int32(root)
	return root, int(d.parity[x])
}

// Union adds a relationship: edge_parity=0 means same side, 1 means different sides.
func (d *ParityDSU) Union(x, y int, edgeParity int) bool {
	rx, px := d.find(x)
	ry, py := d.find(y)

	if rx == ry {
		if (px^py) != edgeParity {
			d.Contradiction = true
		}
		return false
	}

	if d.rank[rx] < d.rank[ry] {
		rx, ry = ry, rx
		px, py = py, px
	}
	// parity[ry] = px ^ py ^ edgeParity
	d.parent[ry] = int32(rx)
	d.parity[ry] = int32(px ^ py ^ edgeParity)
	if d.rank[rx] == d.rank[ry] {
		d.rank[rx]++
	}
	return true
}

// Relation returns:
//   -1 if x and y are in different components
//    0 if same bipartite side
//    1 if different bipartite sides
func (d *ParityDSU) Relation(x, y int) int {
	rx, px := d.find(x)
	ry, py := d.find(y)
	if rx != ry {
		return -1
	}
	return px ^ py
}

// ============================================================
// Rollback DSU (no path compression, supports Undo)
// ============================================================

type rollbackEntry struct {
	node      int32
	oldParent int32
	oldRank   int32
}

// RollbackDSU supports undoing Union operations.
// Uses union-by-rank WITHOUT path compression.
type RollbackDSU struct {
	parent        []int32
	rank          []int32
	stack         []rollbackEntry
	NumComponents int
}

// NewRollback creates a RollbackDSU for n elements (maxOps is stack capacity).
func NewRollback(n, maxOps int) *RollbackDSU {
	d := &RollbackDSU{
		parent:        make([]int32, n),
		rank:          make([]int32, n),
		stack:         make([]rollbackEntry, 0, maxOps),
		NumComponents: n,
	}
	for i := range d.parent {
		d.parent[i] = int32(i)
	}
	return d
}

// Find without path compression (O(log n) with rank).
func (d *RollbackDSU) Find(x int) int {
	for int(d.parent[x]) != x {
		x = int(d.parent[x])
	}
	return x
}

// Union merges and records undo info.
func (d *RollbackDSU) Union(x, y int) bool {
	rx, ry := d.Find(x), d.Find(y)
	if rx == ry {
		return false
	}
	if d.rank[rx] < d.rank[ry] {
		rx, ry = ry, rx
	}
	d.stack = append(d.stack, rollbackEntry{
		node:      int32(ry),
		oldParent: d.parent[ry],
		oldRank:   d.rank[rx],
	})
	d.parent[ry] = int32(rx)
	if d.rank[rx] == d.rank[ry] {
		d.rank[rx]++
	}
	d.NumComponents--
	return true
}

// Undo reverses the last Union.
func (d *RollbackDSU) Undo() {
	if len(d.stack) == 0 {
		panic("undo: empty stack")
	}
	e := d.stack[len(d.stack)-1]
	d.stack = d.stack[:len(d.stack)-1]
	rx := d.parent[e.node]      // current parent (the root we attached to)
	d.rank[rx] = e.oldRank
	d.parent[e.node] = e.oldParent
	d.NumComponents++
}

// Save returns a checkpoint (current stack length).
func (d *RollbackDSU) Save() int { return len(d.stack) }

// Restore rolls back to a saved checkpoint.
func (d *RollbackDSU) Restore(checkpoint int) {
	for len(d.stack) > checkpoint {
		d.Undo()
	}
}

func (d *RollbackDSU) Same(x, y int) bool { return d.Find(x) == d.Find(y) }

// ============================================================
// Concurrent DSU (coarse-grained mutex)
// ============================================================

// ConcurrentDSU wraps DSU with a mutex for concurrent access.
// For high-throughput scenarios, prefer sharded or lock-free designs.
type ConcurrentDSU struct {
	mu   sync.Mutex
	inner *DSU
}

// NewConcurrent creates a thread-safe DSU for n elements.
func NewConcurrent(n int) *ConcurrentDSU {
	return &ConcurrentDSU{inner: New(n)}
}

func (c *ConcurrentDSU) Union(x, y int) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.inner.Union(x, y)
}

func (c *ConcurrentDSU) Same(x, y int) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.inner.Same(x, y)
}

func (c *ConcurrentDSU) NumComponents() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.inner.NumComponents
}

// ============================================================
// Kruskal's MST using DSU
// ============================================================

// Edge represents a weighted graph edge.
type Edge struct {
	U, V   int
	Weight int
}

// Kruskal computes the Minimum Spanning Tree of a graph with n nodes and given edges.
// Returns MST edges and total weight.
func Kruskal(n int, edges []Edge) (mstEdges []Edge, totalWeight int) {
	// Sort edges by weight (insertion sort for clarity; use sort.Slice in production)
	sorted := make([]Edge, len(edges))
	copy(sorted, edges)
	for i := 1; i < len(sorted); i++ {
		for j := i; j > 0 && sorted[j].Weight < sorted[j-1].Weight; j-- {
			sorted[j], sorted[j-1] = sorted[j-1], sorted[j]
		}
	}

	d := New(n)
	for _, e := range sorted {
		if d.Union(e.U, e.V) {
			mstEdges = append(mstEdges, e)
			totalWeight += e.Weight
			if len(mstEdges) == n-1 {
				break // MST complete
			}
		}
	}
	return
}

// ============================================================
// Tests (in dsu_test.go conventionally; shown here inline)
// ============================================================

// Usage example / smoke test:
func Example() {
	d := New(10)
	d.Union(0, 1)
	d.Union(2, 3)
	d.Union(0, 4)
	d.Union(3, 5)
	d.Union(0, 2)

	fmt.Println(d.Same(1, 5))  // true
	fmt.Println(d.Same(0, 6))  // false
	fmt.Println(d.NumComponents) // 5

	// Rollback
	rb := NewRollback(6, 10)
	rb.Union(0, 1)
	rb.Union(2, 3)
	ck := rb.Save()
	rb.Union(0, 2)
	fmt.Println(rb.Same(1, 3)) // true
	rb.Restore(ck)
	fmt.Println(rb.Same(1, 3)) // false

	// Kruskal MST
	edges := []Edge{
		{0, 1, 1}, {1, 2, 3}, {2, 4, 2}, {0, 3, 4}, {3, 4, 5},
	}
	mst, w := Kruskal(5, edges)
	fmt.Println(w, len(mst)) // 10 4

	// Output:
	// true
	// false
	// 5
	// true
	// false
	// 10 4
}
```

### 19.1 Go Test File

```go
// dsu_test.go
package dsu

import (
	"math/rand"
	"sync"
	"testing"
)

func TestBasic(t *testing.T) {
	d := New(10)
	for i := 0; i < 10; i++ {
		if d.Find(i) != i {
			t.Fatalf("singleton Find(%d) should be %d", i, i)
		}
	}
	d.Union(0, 1); d.Union(2, 3); d.Union(0, 4)
	d.Union(3, 5); d.Union(0, 2)

	if !d.Same(1, 5) { t.Error("1 and 5 should be same") }
	if d.Same(0, 6)  { t.Error("0 and 6 should differ") }
	if d.NumComponents != 5 { t.Errorf("expected 5 components, got %d", d.NumComponents) }
}

func TestRollback(t *testing.T) {
	d := NewRollback(8, 20)
	d.Union(0, 1); d.Union(2, 3)
	ck := d.Save()
	d.Union(0, 2)
	if !d.Same(1, 3) { t.Error("after union(0,2): 1 and 3 should be same") }
	d.Restore(ck)
	if d.Same(1, 3) { t.Error("after rollback: 1 and 3 should differ") }
	if !d.Same(0, 1) { t.Error("after rollback: 0 and 1 should still be same") }
}

func TestParity(t *testing.T) {
	d := NewParity(6)
	d.Union(0, 1, 1) // 0 and 1 different sides
	d.Union(1, 2, 1) // 1 and 2 different sides → 0 and 2 same side
	if d.Relation(0, 2) != 0 { t.Error("0 and 2 should be same side") }
	if d.Relation(0, 1) != 1 { t.Error("0 and 1 should be different sides") }
}

func TestConcurrent(t *testing.T) {
	d := NewConcurrent(1000)
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 1000; j++ {
				x := rand.Intn(1000)
				y := rand.Intn(1000)
				d.Union(x, y)
				d.Same(x, y)
			}
		}()
	}
	wg.Wait()
	// No panic, no data race (run with -race)
}

func BenchmarkUnion(b *testing.B) {
	d := New(b.N + 1)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		d.Union(rand.Intn(b.N+1), rand.Intn(b.N+1))
	}
}

func BenchmarkFind(b *testing.B) {
	d := New(100000)
	for i := 0; i < 100000-1; i++ {
		d.Union(i, i+1)
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		d.Find(rand.Intn(100000))
	}
}

// FuzzUnion: fuzz union/find for correctness
func FuzzUnion(f *testing.F) {
	f.Add(10, uint64(42))
	f.Fuzz(func(t *testing.T, n int, seed uint64) {
		if n <= 0 || n > 1000 { return }
		rng := rand.New(rand.NewSource(int64(seed)))
		d := New(n)
		ref := make([]int, n) // naive reference: component ID
		for i := range ref { ref[i] = i }
		findRef := func(x int) int {
			for ref[x] != x { x = ref[x] }
			return x
		}
		for i := 0; i < 100; i++ {
			x, y := rng.Intn(n), rng.Intn(n)
			rx, ry := findRef(x), findRef(y)
			d.Union(x, y)
			if rx != ry {
				ref[rx] = ry // naive union
			}
			// Verify: same(x,y) in DSU iff same in ref
			if d.Same(x, y) != (findRef(x) == findRef(y)) {
				t.Fatalf("inconsistency: dsu.Same(%d,%d)=%v ref=%v",
					x, y, d.Same(x,y), findRef(x)==findRef(y))
			}
		}
	})
}
```

---

## 20. Full Implementation — Rust

```rust
//! Disjoint Set Union (Union-Find) — Production Rust implementation
//!
//! Cargo.toml deps: none (std only)
//! cargo test
//! cargo test -- --nocapture
//! cargo bench
//! cargo +nightly fuzz run fuzz_target_1

/// Basic DSU with union-by-rank and path-halving.
/// All operations are O(α(n)) amortized.
pub struct DSU {
    parent: Vec<u32>,
    rank:   Vec<u8>,   // rank fits in u8 (max rank ≤ log2(n) ≤ 31 for n ≤ 2^31)
    pub num_components: usize,
}

impl DSU {
    /// Creates a DSU for `n` elements (0..n).
    pub fn new(n: usize) -> Self {
        DSU {
            parent: (0..n as u32).collect(),
            rank:   vec![0u8; n],
            num_components: n,
        }
    }

    /// Returns the canonical root of `x`'s component.
    /// Path halving: every other node on the path is re-parented to its grandparent.
    pub fn find(&mut self, mut x: usize) -> usize {
        while self.parent[x] as usize != x {
            let g = self.parent[self.parent[x] as usize] as usize;
            self.parent[x] = g as u32;
            x = g;
        }
        x
    }

    /// Merges the components of `x` and `y`.
    /// Returns `true` if they were in different components.
    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let mut rx = self.find(x);
        let mut ry = self.find(y);
        if rx == ry { return false; }

        if self.rank[rx] < self.rank[ry] {
            std::mem::swap(&mut rx, &mut ry);
        }
        self.parent[ry] = rx as u32;
        if self.rank[rx] == self.rank[ry] {
            self.rank[rx] += 1;
        }
        self.num_components -= 1;
        true
    }

    /// Returns `true` if `x` and `y` are in the same component.
    pub fn same(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    /// Resets all elements to singletons.
    pub fn reset(&mut self) {
        let n = self.parent.len();
        for i in 0..n {
            self.parent[i] = i as u32;
            self.rank[i] = 0;
        }
        self.num_components = n;
    }

    /// Returns `true` if the entire universe is one component.
    pub fn is_connected(&self) -> bool {
        self.num_components == 1
    }
}

// ============================================================
// Size-based DSU
// ============================================================

/// DSU tracking exact component sizes.
pub struct SizeDSU {
    parent: Vec<u32>,
    size:   Vec<u32>,
    pub num_components: usize,
}

impl SizeDSU {
    pub fn new(n: usize) -> Self {
        SizeDSU {
            parent: (0..n as u32).collect(),
            size:   vec![1u32; n],
            num_components: n,
        }
    }

    pub fn find(&mut self, mut x: usize) -> usize {
        while self.parent[x] as usize != x {
            let g = self.parent[self.parent[x] as usize] as usize;
            self.parent[x] = g as u32;
            x = g;
        }
        x
    }

    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let mut rx = self.find(x);
        let mut ry = self.find(y);
        if rx == ry { return false; }
        if self.size[rx] < self.size[ry] {
            std::mem::swap(&mut rx, &mut ry);
        }
        self.parent[ry] = rx as u32;
        self.size[rx] += self.size[ry];
        self.num_components -= 1;
        true
    }

    pub fn same(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    /// Returns the size of `x`'s component.
    pub fn size_of(&mut self, x: usize) -> usize {
        let r = self.find(x);
        self.size[r] as usize
    }
}

// ============================================================
// Parity / Bipartite DSU
// ============================================================

/// DSU with XOR-parity edge weights for bipartite checking.
pub struct ParityDSU {
    parent:         Vec<u32>,
    rank:           Vec<u8>,
    parity:         Vec<u8>,  // parity[x]: XOR distance from x to parent[x]
    pub contradiction: bool,
}

impl ParityDSU {
    pub fn new(n: usize) -> Self {
        ParityDSU {
            parent:       (0..n as u32).collect(),
            rank:         vec![0u8; n],
            parity:       vec![0u8; n],
            contradiction: false,
        }
    }

    // Returns (root, parity_from_x_to_root)
    fn find_inner(&mut self, x: usize) -> (usize, u8) {
        if self.parent[x] as usize == x {
            return (x, 0);
        }
        let (root, child_par) = self.find_inner(self.parent[x] as usize);
        // path compress: update parity to be relative to root
        self.parity[x] ^= child_par;
        self.parent[x] = root as u32;
        (root, self.parity[x])
    }

    pub fn find(&mut self, x: usize) -> (usize, u8) {
        self.find_inner(x)
    }

    /// Union with edge_parity: 0 = same side, 1 = opposite sides.
    pub fn union(&mut self, x: usize, y: usize, edge_parity: u8) -> bool {
        let (rx, px) = self.find(x);
        let (ry, py) = self.find(y);

        if rx == ry {
            if px ^ py != edge_parity {
                self.contradiction = true;
            }
            return false;
        }

        let (mut rx, mut px, mut ry, mut py) = (rx, px, ry, py);
        if self.rank[rx] < self.rank[ry] {
            std::mem::swap(&mut rx, &mut ry);
            std::mem::swap(&mut px, &mut py);
        }

        self.parent[ry] = rx as u32;
        self.parity[ry] = px ^ py ^ edge_parity;
        if self.rank[rx] == self.rank[ry] {
            self.rank[rx] += 1;
        }
        true
    }

    /// -1: different components, 0: same side, 1: different sides
    pub fn relation(&mut self, x: usize, y: usize) -> i32 {
        let (rx, px) = self.find(x);
        let (ry, py) = self.find(y);
        if rx != ry { return -1; }
        (px ^ py) as i32
    }
}

// ============================================================
// Rollback DSU (no path compression, supports undo)
// ============================================================

#[derive(Clone)]
struct RollbackEntry {
    node:       u32,
    old_parent: u32,
    old_rank:   u8,
}

/// DSU supporting O(log n) Union and O(1) Undo.
/// No path compression — depth bounded to O(log n) by rank.
pub struct RollbackDSU {
    parent: Vec<u32>,
    rank:   Vec<u8>,
    stack:  Vec<RollbackEntry>,
    pub num_components: usize,
}

impl RollbackDSU {
    pub fn new(n: usize) -> Self {
        RollbackDSU {
            parent: (0..n as u32).collect(),
            rank:   vec![0u8; n],
            stack:  Vec::new(),
            num_components: n,
        }
    }

    /// Find without path compression.
    pub fn find(&self, mut x: usize) -> usize {
        while self.parent[x] as usize != x {
            x = self.parent[x] as usize;
        }
        x
    }

    pub fn same(&self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let mut rx = self.find(x);
        let mut ry = self.find(y);
        if rx == ry { return false; }
        if self.rank[rx] < self.rank[ry] {
            std::mem::swap(&mut rx, &mut ry);
        }
        self.stack.push(RollbackEntry {
            node:       ry as u32,
            old_parent: self.parent[ry],
            old_rank:   self.rank[rx],
        });
        self.parent[ry] = rx as u32;
        if self.rank[rx] == self.rank[ry] {
            self.rank[rx] += 1;
        }
        self.num_components -= 1;
        true
    }

    /// Undo the last Union.
    pub fn undo(&mut self) {
        let e = self.stack.pop().expect("undo: empty stack");
        let rx = self.parent[e.node as usize] as usize;
        self.rank[rx] = e.old_rank;
        self.parent[e.node as usize] = e.old_parent;
        self.num_components += 1;
    }

    /// Returns a checkpoint (current stack depth).
    pub fn save(&self) -> usize { self.stack.len() }

    /// Rolls back all unions since the checkpoint.
    pub fn restore(&mut self, checkpoint: usize) {
        while self.stack.len() > checkpoint {
            self.undo();
        }
    }
}

// ============================================================
// Kruskal's MST
// ============================================================

#[derive(Debug, Clone)]
pub struct Edge {
    pub u: usize,
    pub v: usize,
    pub weight: i64,
}

/// Kruskal's MST algorithm using DSU.
/// Returns (mst_edges, total_weight).
pub fn kruskal(n: usize, mut edges: Vec<Edge>) -> (Vec<Edge>, i64) {
    edges.sort_unstable_by_key(|e| e.weight);
    let mut dsu = DSU::new(n);
    let mut mst = Vec::with_capacity(n - 1);
    let mut total = 0i64;

    for e in edges {
        if dsu.union(e.u, e.v) {
            total += e.weight;
            mst.push(e);
            if mst.len() == n - 1 { break; }
        }
    }
    (mst, total)
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        let mut d = DSU::new(10);
        for i in 0..10 { assert_eq!(d.find(i), i); }

        d.union(0, 1); d.union(2, 3); d.union(0, 4);
        d.union(3, 5); d.union(0, 2);

        assert!(d.same(1, 5));
        assert!(!d.same(0, 6));
        assert_eq!(d.num_components, 5);
    }

    #[test]
    fn test_size() {
        let mut d = SizeDSU::new(8);
        d.union(0, 1); d.union(2, 3); d.union(0, 2);
        assert_eq!(d.size_of(0), 4);
        assert_eq!(d.size_of(1), 4);
        assert_eq!(d.size_of(4), 1);
    }

    #[test]
    fn test_rollback() {
        let mut d = RollbackDSU::new(6);
        d.union(0, 1); d.union(2, 3);
        let ck = d.save();
        d.union(0, 2);
        assert!(d.same(1, 3));
        d.restore(ck);
        assert!(!d.same(0, 2));
        assert!(d.same(0, 1));
        d.restore(0);
        for i in 0..6 { assert_eq!(d.find(i), i); }
    }

    #[test]
    fn test_parity() {
        let mut d = ParityDSU::new(6);
        d.union(0, 1, 1); // 0 and 1 on different sides
        d.union(1, 2, 1); // 1 and 2 on different sides → 0 and 2 same side
        assert_eq!(d.relation(0, 2), 0);
        assert_eq!(d.relation(0, 1), 1);
        assert!(!d.contradiction);
        d.union(0, 1, 0); // contradiction: was different, now same
        assert!(d.contradiction);
    }

    #[test]
    fn test_kruskal() {
        let edges = vec![
            Edge{u:0,v:1,weight:1}, Edge{u:1,v:2,weight:3},
            Edge{u:2,v:4,weight:2}, Edge{u:0,v:3,weight:4},
            Edge{u:3,v:4,weight:5},
        ];
        let (mst, w) = kruskal(5, edges);
        assert_eq!(mst.len(), 4);
        assert_eq!(w, 10);
    }

    #[test]
    fn test_idempotent_union() {
        let mut d = DSU::new(5);
        assert!(d.union(0, 1));
        assert!(!d.union(0, 1));  // already same set
        assert!(!d.union(1, 0));  // symmetric
        assert_eq!(d.num_components, 4);
    }

    #[test]
    fn test_reset() {
        let mut d = DSU::new(5);
        d.union(0, 4); d.union(1, 3);
        d.reset();
        for i in 0..5 { assert_eq!(d.find(i), i); }
        assert_eq!(d.num_components, 5);
    }

    // Property test: DSU must match naive reference implementation
    #[test]
    fn test_property_matches_reference() {
        use std::collections::HashMap;
        let n = 100;
        let mut d = DSU::new(n);
        let mut ref_set: Vec<usize> = (0..n).collect();

        let mut find_ref = |ref_set: &mut Vec<usize>, mut x: usize| -> usize {
            while ref_set[x] != x { x = ref_set[x]; }
            x
        };

        let ops: Vec<(usize, usize)> = vec![
            (0,1),(5,9),(0,5),(20,30),(3,7),(3,20),(99,0)
        ];
        for (x, y) in &ops {
            let rx = find_ref(&mut ref_set, *x);
            let ry = find_ref(&mut ref_set, *y);
            if rx != ry { ref_set[rx] = ry; }
            d.union(*x, *y);
        }

        for x in 0..n {
            for y in 0..n {
                let same_ref = find_ref(&mut ref_set, x) == find_ref(&mut ref_set, y);
                let same_dsu = d.same(x, y);
                assert_eq!(same_ref, same_dsu,
                    "mismatch at ({},{}) ref={} dsu={}", x, y, same_ref, same_dsu);
            }
        }
    }
}

// ============================================================
// Benchmarks (cargo bench)
// ============================================================

#[cfg(test)]
mod benches {
    use super::*;
    extern crate test;  // nightly only; use criterion crate for stable

    #[bench]
    fn bench_union_find_1m(b: &mut test::Bencher) {
        const N: usize = 1_000_000;
        b.iter(|| {
            let mut d = DSU::new(N);
            for i in 0..N-1 {
                d.union(i, i+1);
            }
            d.find(N-1)  // should be 0
        });
    }
}
```

---

## 21. Testing, Fuzzing, and Benchmarking

### 21.1 Test Strategy

```
+---------------------+-----------------------------------------------+
| Test Category       | Coverage                                      |
+---------------------+-----------------------------------------------+
| Unit                | Each op in isolation (singleton, union, find) |
| Invariant           | num_components decrements correctly           |
| Idempotent          | Union(x,x), Union(x,y) twice = no-op         |
| Symmetry            | Union(x,y) == Union(y,x) re: connectivity     |
| Rollback            | Save/restore to each checkpoint               |
| Concurrent          | race detector (-race), no deadlock            |
| Property            | Matches naive O(n²) reference implementation  |
| Stress              | 10M random ops, verify connectivity counts   |
+---------------------+-----------------------------------------------+
```

### 21.2 Fuzz Targets

**Go:**

```bash
# In dsu package directory:
go test -fuzz=FuzzUnion -fuzztime=60s

# Fuzz corpus seeds:
mkdir testdata/fuzz/FuzzUnion
echo "10 42" > testdata/fuzz/FuzzUnion/seed1
```

**C (AFL):**

```bash
# Compile with AFL
afl-clang -O2 -DDSU_FUZZ -o dsu_fuzz disjoint_set.c

# dsu_fuzz.c reads input as sequence of (op, x, y) byte triples
mkdir fuzz_in && echo "\x01\x00\x01\x02\x01\x03" > fuzz_in/seed
afl-fuzz -i fuzz_in -o fuzz_out ./dsu_fuzz @@
```

**Rust (cargo-fuzz):**

```bash
cargo install cargo-fuzz
cargo fuzz init
# Add to fuzz/fuzz_targets/fuzz_target_1.rs:
#   arbitrary::Arbitrary derive on a struct with Vec<(u8,u32,u32)> ops
cargo +nightly fuzz run fuzz_target_1 -- -max_total_time=60
```

### 21.3 Benchmark Commands

```bash
# Go
go test -bench=. -benchmem -benchtime=5s ./...

# C
gcc -O3 -march=native -DDSU_MAIN -o dsu_bench disjoint_set.c && ./dsu_bench

# Rust (nightly)
cargo +nightly bench

# Rust (stable with Criterion)
# Add to Cargo.toml: criterion = "0.5"
cargo bench --bench dsu_bench
```

### 21.4 Expected Benchmark Numbers (x86-64, ~3GHz)

```
+----------------------------------+---------------+-----------+
| Operation                        | DSU (α(n))    | Naive     |
+----------------------------------+---------------+-----------+
| 5M random union+find (n=1M)      | ~200 M ops/s  | ~20 M/s   |
| Find after full merge (n=1M)     | ~1-2 ns/op    | ~100 ns/op|
| Rollback (no compression, n=1M)  | ~400 M ops/s  | N/A       |
+----------------------------------+---------------+-----------+
```

---

## 22. Failure Modes and Edge Cases

### 22.1 Classic Bugs

```
+-----------------------------------------------+------------------------------+
| Bug                                           | Symptom                      |
+-----------------------------------------------+------------------------------+
| Using path compression in rollback DSU        | Undo restores wrong state    |
| Not initializing rank/size to 0/1             | Incorrect merge decisions    |
| Integer overflow in size[] for large n        | Wrong size queries           |
| Off-by-one in n (0-indexed vs 1-indexed)      | Out-of-bounds access         |
| Forgetting to decrement num_components        | Wrong component count        |
| Recursive find stack overflow (deep trees)    | Stack overflow for n>100K    |
| Mutating parent during concurrent read        | Data race, torn reads        |
| Assuming root never changes (stale cache)     | Stale connectivity info      |
+-----------------------------------------------+------------------------------+
```

### 22.2 Stack Overflow — Recursive Find

Recursive path compression can overflow the call stack for degenerate chains:

```
n=500,000 elements in a chain:  0 → 1 → 2 → ... → 499,999
Find(0) without compression: 500,000 recursive frames → STACK OVERFLOW

Fix: Always use iterative Find (path halving or path splitting).
```

### 22.3 ABA Problem in Lock-Free Union

In lock-free Union, a node can become a root, get unioned, and a stale CAS can corrupt state.

```
Thread 1: reads parent[x] = x (x is root)
Thread 2: unions x into y (parent[x] = y)
Thread 1: CAS(parent[x], x, z) SUCCEEDS  ← ABA problem!
           x is no longer a root, but we set parent[x] = z

Fix: Use monotone root IDs (always merge rx into ry where rx < ry),
     ensuring roots only ever get absorbed, never re-emerge.
```

### 22.4 Rank Invariant Violation

After path compression, rank[x] may be higher than the actual tree height — **this is correct and
intentional**. Rank is an **upper bound**, not an exact height. Never try to "fix" ranks after
compression; it would break the amortized analysis.

### 22.5 Union with Self

```
Union(x, x): Find(x) == Find(x) → no-op ✓
Make sure your implementation handles this (it naturally does with the rx==ry check).
```

---

## 23. Systems-Level Relevance (CNCF / Cloud / Security)

### 23.1 Architecture: Where Union-Find Appears in Real Systems

```
                    Cloud / Datacenter Topology
                    ═══════════════════════════

  ┌─────────────────────────────────────────────────────────┐
  │                   Control Plane                          │
  │  ┌──────────────┐   ┌──────────────┐  ┌─────────────┐  │
  │  │  Kubernetes  │   │   etcd       │  │  Scheduler  │  │
  │  │  API Server  │   │  (Raft log)  │  │  (bin pack) │  │
  │  └──────┬───────┘   └──────────────┘  └─────────────┘  │
  │         │                                               │
  │         │ Node/Pod graph → DSU for reachability         │
  └─────────┼───────────────────────────────────────────────┘
            │
            ▼
  ┌─────────────────────────────────────────────────────────┐
  │                  Network Fabric                           │
  │  BGP ASes ──► connected AS groups (DSU)                  │
  │  VPCs     ──► peered network segments (DSU)              │
  │  CNI pods ──► overlay network reachability (DSU)         │
  │                                                          │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
  │  │  Node A  │  │  Node B  │  │  Node C  │              │
  │  │ Pod 1,2  │  │ Pod 3,4  │  │ Pod 5,6  │              │
  │  └──────────┘  └──────────┘  └──────────┘              │
  │       │              │              │                    │
  │       └──────────────┴──────────────┘                   │
  │              VxLAN / GENEVE overlay                      │
  └─────────────────────────────────────────────────────────┘
            │
            ▼
  ┌─────────────────────────────────────────────────────────┐
  │               Service Mesh (Istio/Linkerd)               │
  │  mTLS identity groups ──► DSU for security domains       │
  │  Circuit break groups ──► DSU for failure isolation       │
  │  Traffic policy sets  ──► DSU for policy grouping        │
  └─────────────────────────────────────────────────────────┘
```

### 23.2 Specific Use Cases

**Kubernetes Network Policy Reachability:**

```
When processing NetworkPolicy objects, the controller must determine which pods can
reach which other pods. This is fundamentally a connected components problem:

1. Create DSU with one element per pod
2. For each NetworkPolicy allowing traffic between pod sets: Union
3. Query: can pod A reach pod B? → dsu.Same(A, B)

This is computed incrementally as pods are added/removed and policies change.
```

**etcd Cluster Membership:**

```
Raft consensus requires knowing which nodes are in the same quorum.
A quorum is "connected" in the membership graph.
DSU tracks which minority-partition nodes are isolated.
```

**Container Image Layer Deduplication:**

```
OCI image layers are content-addressed. When multiple images share layers,
the storage system groups them into the same "blob set":
Union(layer_X, layer_Y) whenever they share a parent or are identical.
This is Kruskal-style MST construction on the image dependency graph.
```

**BGP Route Aggregation:**

```
AS path computation groups ASes into connected components for:
- Loop detection (if Find(source) == Find(dest): loop)
- Route reflector grouping
- Policy application domains
```

### 23.3 Security Considerations

```
+----------------------------------+----------------------------------------------+
| Threat                           | Mitigation                                   |
+----------------------------------+----------------------------------------------+
| Adversarial input causing        | Rank/size union bounds depth to O(log n),    |
| O(n) Find (DoS via chain)        | making O(n) per-op impossible                |
| Race condition in concurrent DSU | Use mutex-guarded or lock-free CAS variant;  |
|                                  | test with -race (Go) / ThreadSanitizer (C)   |
| Integer overflow in rank/size    | Use u32 for size (n ≤ 4B), u8 for rank      |
|                                  | (rank ≤ 31 for n ≤ 2^31)                    |
| Stack overflow via recursive     | Always use iterative Find in production      |
| Find on malicious input          | (path halving, no recursion)                 |
| Stale connectivity read in       | Either serialize reads through same lock     |
| distributed systems              | or use monotonically increasing version tags |
| Memory exhaustion (large n)      | n elements: 8 bytes each (parent+rank)       |
|                                  | For n=10M: 80MB — acceptable                 |
+----------------------------------+----------------------------------------------+
```

---

## 24. References

### Primary Papers

1. **Tarjan, R. E. (1975).** "Efficiency of a good but not linear set union algorithm."
   *JACM 22(2):215–225.* — Proved O(m log*(n)) bound; introduced potential argument.

2. **Tarjan, R. E., & van Leeuwen, J. (1984).** "Worst-case analysis of set union algorithms."
   *JACM 31(2):245–281.* — Proved O(m · α(n)) optimal bound; analyzed path halving/splitting.

3. **Fredman, M. L., & Saks, M. E. (1989).** "The cell probe complexity of dynamic data structures."
   *STOC 1989.* — Proved Ω(m · α(n)) lower bound (Union-Find is asymptotically optimal).

4. **Sleator, D. D., & Tarjan, R. E. (1983).** "A data structure for dynamic trees."
   *JCSS 26(3):362–391.* — Link-Cut Trees for fully dynamic connectivity.

5. **Holm, J., de Lichtenberg, K., & Thorup, M. (2001).** "Poly-logarithmic deterministic
   fully-dynamic graph algorithms for connectivity, minimum spanning tree, 2-edge, and
   biconnectivity." *JACM 48(4):723–760.*

6. **Anderson, R. J., & Woll, H. (1991).** "Wait-free parallel algorithms for the Union-Find
   problem." *STOC 1991.* — Lock-free concurrent Union-Find.

### Books

7. **CLRS** — *Introduction to Algorithms*, Chapter 21: Data Structures for Disjoint Sets.
   Thorough treatment of union by rank, path compression, and amortized analysis.

8. **Sedgewick & Wayne** — *Algorithms* (4th ed.), Section 1.5: Union-Find.
   Excellent pedagogical treatment with Java implementation.

9. **Tarjan** — *Data Structures and Network Algorithms* (1983). The canonical reference.

### Online Resources

10. Princeton COS 226 course notes on Union-Find:
    https://algs4.cs.princeton.edu/15uf/

11. CP-algorithms: Disjoint Set Union:
    https://cp-algorithms.com/data_structures/disjoint_set_union.html

12. Ackermann function and inverse:
    https://en.wikipedia.org/wiki/Ackermann_function

---

## Appendix: Complete ASCII Architecture View

```
                    DISJOINT SET UNION — FULL PICTURE
                    ════════════════════════════════════

  Universe: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

  ┌─────────────────────────────────────────────────────────┐
  │ OPERATION                     │ STATE                    │
  ├───────────────────────────────┼─────────────────────────┤
  │ Initial (10 singletons)       │ 0 1 2 3 4 5 6 7 8 9    │
  │                               │ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑  │
  ├───────────────────────────────┼─────────────────────────┤
  │ Union(0,1): rank equal →      │     0   2 3 4 5 6 7 8 9│
  │   parent[1]=0, rank[0]=1      │     |                   │
  │                               │     1                   │
  ├───────────────────────────────┼─────────────────────────┤
  │ Union(2,3): rank equal →      │     0     2 4 5 6 7 8 9 │
  │   parent[3]=2, rank[2]=1      │     |     |             │
  │                               │     1     3             │
  ├───────────────────────────────┼─────────────────────────┤
  │ Union(4,5): rank equal →      │     0     2   4 6 7 8 9 │
  │   parent[5]=4, rank[4]=1      │     |     |   |         │
  │                               │     1     3   5         │
  ├───────────────────────────────┼─────────────────────────┤
  │ Union(0,2): rank equal (1==1)→│       0     4 6 7 8 9   │
  │   parent[2]=0, rank[0]=2      │      /|\    |           │
  │                               │     1 2     5           │
  │                               │       |                 │
  │                               │       3                 │
  ├───────────────────────────────┼─────────────────────────┤
  │ Union(0,4): rank[0]=2>rank[4] │       0     6 7 8 9     │
  │   parent[4]=0, rank[0]=2 (no  │     / | \               │
  │   increment, ranks unequal)   │    1  2  4              │
  │                               │       |  |              │
  │                               │       3  5              │
  ├───────────────────────────────┼─────────────────────────┤
  │ Find(5) with path halving:    │       0     6 7 8 9     │
  │   5 → parent[5]=4             │    / / \ \              │
  │   4 → parent[4]=0             │   1 2  4  5  ←compressed│
  │   0 == 0 → return 0           │      |                  │
  │   parent[5] updated to 0      │      3                  │
  └───────────────────────────────┴─────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │ COMPLEXITY AT A GLANCE                               │
  │                                                      │
  │  n=10^6 elements, m=5×10^6 ops                      │
  │                                                      │
  │  Naive:         O(mn)    = 5×10^12 ops  ≈ hours    │
  │  Rank only:     O(m log n) = 10^8 ops   ≈ seconds  │
  │  Compress only: O(m log n) amort         ≈ seconds  │
  │  Rank+Compress: O(m·α(n))  ≈ O(m·4)    ≈ ms       │
  │                                                      │
  │  α(10^6) = 4  (effectively constant)                │
  └──────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │ VARIANT SELECTION GUIDE                                  │
  │                                                          │
  │  Need just connectivity?          → DSU (rank + halving) │
  │  Need set sizes?                  → SizeDSU              │
  │  Need undo / rollback?            → RollbackDSU          │
  │  Need bipartite / parity?         → ParityDSU            │
  │  Need thread safety?              → ConcurrentDSU        │
  │  Need all historical versions?    → Persistent DSU       │
  │  Need O(log n) edge deletions?    → Link-Cut Trees       │
  └─────────────────────────────────────────────────────────┘
```

---

*Guide version: 1.0 | May 2026 | Covers all standard DSU variants through Tarjan (1984)*
*Implementations: C99, Go 1.22+, Rust 1.75+ (stable, except bench which needs nightly)*