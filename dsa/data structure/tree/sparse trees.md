# Sparse Trees: A Complete & Comprehensive Guide

> **Implementations:** C · Go · Rust  
> **Difficulty:** Intermediate → Advanced  
> **Topics Covered:** Sparse Table, Binary Lifting, LCA, RMQ, Euler Tour, Offline Algorithms, and more.

---

## Table of Contents

1. [What Are Sparse Trees?](#1-what-are-sparse-trees)
2. [Mathematical Foundations](#2-mathematical-foundations)
3. [Sparse Table — Core Data Structure](#3-sparse-table--core-data-structure)
4. [Range Minimum / Maximum Queries (RMQ)](#4-range-minimum--maximum-queries-rmq)
5. [Range Sum Queries](#5-range-sum-queries)
6. [Binary Lifting](#6-binary-lifting)
7. [Lowest Common Ancestor (LCA)](#7-lowest-common-ancestor-lca)
8. [Euler Tour + Sparse Table (LCA in O(1))](#8-euler-tour--sparse-table-lca-in-o1)
9. [Sparse Trees on Graphs](#9-sparse-trees-on-graphs)
10. [Offline vs. Online Queries](#10-offline-vs-online-queries)
11. [Advanced Variants](#11-advanced-variants)
12. [Complexity Summary](#12-complexity-summary)
13. [Complete Implementations in C](#13-complete-implementations-in-c)
14. [Complete Implementations in Go](#14-complete-implementations-in-go)
15. [Complete Implementations in Rust](#15-complete-implementations-in-rust)
16. [Common Pitfalls & Debugging Tips](#16-common-pitfalls--debugging-tips)
17. [Practice Problems & Applications](#17-practice-problems--applications)

---

## 1. What Are Sparse Trees?

The term **"Sparse Tree"** covers a family of data structures and algorithmic techniques that exploit **powers of two** to build compact, space-efficient auxiliary structures over arrays or tree-graphs. The word *sparse* comes from the fact that only O(n log n) representative ancestor/range entries are stored — far fewer than the O(n²) that a naive table would require — yet these entries are sufficient to answer any query in O(1) or O(log n) time.

There are two broad families:

| Family | Core Idea | Query Time | Build Time | Space |
|---|---|---|---|---|
| **Sparse Table** (array-based) | Precompute answers for intervals of size 2^k | O(1) for idempotent ops | O(n log n) | O(n log n) |
| **Binary Lifting** (tree-based) | Precompute 2^k-th ancestors for every node | O(log n) | O(n log n) | O(n log n) |

Both techniques share the same philosophical core: **break the problem into power-of-two pieces**, precompute answers for each piece, then reconstruct the overall answer by combining a small number of pieces.

### Why Sparse Trees Matter

- They are the engine behind **O(1) Range Minimum Query (RMQ)**, one of the most fundamental primitives in competitive programming and systems software.
- They power **O(log n) LCA** (Lowest Common Ancestor), critical in computational biology, network routing, and tree DP.
- They underlie **offline LCA** (Tarjan's algorithm) and **online LCA** (Euler Tour + Sparse Table).
- They appear in **suffix arrays**, **string hashing**, and **interval tree** variants.

---

## 2. Mathematical Foundations

### 2.1 Powers of Two and Interval Decomposition

The central insight: **any integer n can be decomposed into a sum of distinct powers of two** (its binary representation). For intervals, this means:

```
Any interval [l, r] of length L = r - l + 1 can be *covered* (not necessarily partitioned)
by just TWO intervals of length 2^floor(log2(L)).
```

For **idempotent** operations (where `f(x, x) = x` for all x — e.g., min, max, gcd, bitwise AND/OR) overlapping coverage is perfectly fine. For non-idempotent operations (e.g., sum, count) you need non-overlapping decomposition (at most log n pieces via binary representation).

### 2.2 Logarithm Precomputation

Sparse Table computations frequently need `floor(log2(k))`. This is precomputed in O(n) with:

```
log2[1] = 0
log2[i] = log2[i/2] + 1   for i >= 2
```

This avoids repeated calls to a floating-point log function.

### 2.3 Overlap-Friendly Queries

For an idempotent function f:

```
f(A[l..r]) = f( f(A[l .. l + 2^k - 1]),  f(A[r - 2^k + 1 .. r]) )
where k = floor(log2(r - l + 1))
```

The two sub-intervals overlap but since f(x,x)=x the double-counting doesn't matter.

### 2.4 Binary Lifting on Trees

For trees, the **2^k-th ancestor** table is built as:

```
anc[v][0] = parent(v)
anc[v][k] = anc[ anc[v][k-1] ][k-1]
```

The 2^k-th ancestor of v is the (2^(k-1))-th ancestor of v's (2^(k-1))-th ancestor — a *doubling* recurrence.

---

## 3. Sparse Table — Core Data Structure

### 3.1 Definition

A **Sparse Table** over an array `A[0..n-1]` with respect to a binary operation `f` is a 2D table `ST[k][i]` such that:

```
ST[k][i] = f(A[i], A[i+1], ..., A[i + 2^k - 1])
```

In other words, `ST[k][i]` stores the answer for the sub-array starting at index `i` with length `2^k`.

### 3.2 Building the Table

**Base case (k=0):** Each sub-array of length 1 is just the element itself.
```
ST[0][i] = A[i]
```

**Inductive step:** A sub-array of length 2^k starting at i splits into two halves of length 2^(k-1):
```
ST[k][i] = f( ST[k-1][i],  ST[k-1][i + 2^(k-1)] )
```

This is filled bottom-up from k=1 to k=floor(log2(n)).

**Total entries:** Σ_{k=0}^{log n} n = O(n log n)

### 3.3 Query Phase

**Idempotent operations (min, max, gcd, AND, OR):**
```
k = floor(log2(r - l + 1))
answer = f( ST[k][l], ST[k][r - 2^k + 1] )
```
— O(1) per query.

**Non-idempotent operations (sum, product):**
Use bit decomposition:
```
answer = identity
pos = l
for k from LOG-1 down to 0:
    if pos + 2^k - 1 <= r:
        answer = f(answer, ST[k][pos])
        pos += 2^k
```
— O(log n) per query. (A Segment Tree or Fenwick Tree is usually preferred for this.)

### 3.4 Memory Layout Considerations

Two common layouts:

**Row-major `ST[k][i]`:** Row k holds all starting positions for length 2^k. Good cache behavior during build (fills rows sequentially). Querying accesses two rows.

**Column-major `ST[i][k]`:** Column k holds the answers for node/index i. Better cache performance if you frequently query the same index at multiple levels (binary lifting scenario).

For RMQ, **row-major is standard**. For binary lifting on trees, **column-major (`anc[node][k]`)** tends to be used in competitive programming, though performance depends on access patterns.

---

## 4. Range Minimum / Maximum Queries (RMQ)

### 4.1 Problem Statement

Given an array A of n elements, answer Q queries of the form:
```
RMQ(l, r) = minimum element in A[l..r]
```
Updates may or may not be supported (static vs. dynamic).

**This guide focuses on the static case**, where the array does not change between queries.

### 4.2 Naive Approach: O(n) per query, O(1) space

Simply scan A[l..r] linearly. Acceptable only for very small n or very few queries.

### 4.3 Sparse Table Approach: O(n log n) build, O(1) query

The gold standard for static RMQ. Since `min(x, x) = x`, the operation is idempotent, and overlapping intervals are allowed.

**Pseudocode:**
```
BUILD(A, n):
    LOG = floor(log2(n)) + 1
    ST[0..LOG][0..n-1]
    for i in 0..n-1:
        ST[0][i] = A[i]
    for k in 1..LOG-1:
        for i in 0..n - 2^k:
            ST[k][i] = min(ST[k-1][i], ST[k-1][i + 2^(k-1)])

QUERY(l, r):
    k = log2_table[r - l + 1]
    return min(ST[k][l], ST[k][r - 2^k + 1])
```

### 4.4 Why O(1) Query is Significant

O(1) per query vs O(log n) (Segment Tree) seems like a minor difference until you have Q = 10^7 queries. On modern hardware with n = 10^6:

- Sparse Table: ~10^7 × 2 comparisons ≈ 0.02 seconds
- Segment Tree: ~10^7 × 20 comparisons ≈ 0.2 seconds

This 10× difference frequently determines whether a solution passes within time limits.

### 4.5 Limitations of Sparse Table for RMQ

- **No updates.** Adding or removing elements requires a full rebuild: O(n log n). For dynamic RMQ, use a Segment Tree (O(log n) update and query).
- **Memory:** O(n log n) space, which for n = 10^7 requires ~560 MB (with int32). Manage carefully.
- **Only idempotent operations** get the O(1) query benefit. Sum queries are O(log n).

---

## 5. Range Sum Queries

Although a Sparse Table can handle sum queries in O(log n) time, **prefix sums** solve static range sum queries in O(1) query time with O(n) space:

```
prefix[0] = 0
prefix[i] = A[0] + A[1] + ... + A[i-1]
sum(l, r) = prefix[r+1] - prefix[l]
```

For **dynamic** sum queries (with point updates), a **Fenwick Tree (Binary Indexed Tree)** gives O(log n) both for updates and queries with O(n) space — much better than Sparse Table.

The Sparse Table's advantage is specifically the **O(1) idempotent query**, and sum is not idempotent. Keep this in mind when choosing a data structure.

---

## 6. Binary Lifting

### 6.1 Motivation

Consider a rooted tree with n nodes. Given a node v and integer k, find the k-th ancestor of v (the node reached by walking k steps toward the root). Naively this costs O(k) time. With Binary Lifting, it costs O(log n) with O(n log n) preprocessing.

### 6.2 Table Definition

```
anc[v][j] = the 2^j-th ancestor of node v
```

Special case: `anc[v][j] = -1` (or 0, depending on implementation) if the 2^j-th ancestor doesn't exist (i.e., we go above the root).

### 6.3 Building the Table

```
ROOT = 0  (or 1, depending on convention)
LOG = ceil(log2(n)) + 1

// Initialize level 0: direct parent
for each node v:
    anc[v][0] = parent[v]   // -1 for root

// Fill higher levels
for j in 1..LOG-1:
    for each node v:
        if anc[v][j-1] == -1:
            anc[v][j] = -1
        else:
            anc[v][j] = anc[ anc[v][j-1] ][j-1]
```

**Order of traversal:** The outer loop over j must be outermost (not over v), because `anc[v][j]` depends on `anc[...][j-1]`.

Alternatively, process nodes in **BFS order** (level by level) and fill level-by-level.

### 6.4 Answering k-th Ancestor Queries

```
KANCESTOR(v, k):
    for j from LOG-1 down to 0:
        if (k >> j) & 1:  // if bit j of k is set
            v = anc[v][j]
            if v == -1: return -1  // went above root
    return v
```

This extracts the binary representation of k and jumps by 2^j steps whenever bit j is set.

**Example:** k = 13 = 8 + 4 + 1 = 2^3 + 2^2 + 2^0. We jump 8 steps, then 4 steps, then 1 step.

### 6.5 Depth Tracking

Binary lifting is always paired with **depth** precomputation (BFS or DFS from root):
```
depth[root] = 0
depth[v] = depth[parent[v]] + 1
```

Depth is critical for LCA computation.

---

## 7. Lowest Common Ancestor (LCA)

### 7.1 Definition

The **Lowest Common Ancestor** (LCA) of two nodes u and v in a rooted tree is the deepest node that is an ancestor of both u and v.

Equivalently:
- LCA(u, v) is the unique node w such that w is an ancestor of both u and v, and no child of w is an ancestor of both.
- In an unrooted tree, LCA depends on the chosen root.

### 7.2 Applications

- **Distance between nodes in a tree:** dist(u,v) = depth[u] + depth[v] - 2 × depth[LCA(u,v)]
- **Tree path queries:** Any value on the path u→v can be computed via LCA
- **Offline batch LCA** (Tarjan's algorithm)
- **Range queries on trees** (Heavy-Light Decomposition uses LCA)
- **Computational biology:** Phylogenetic trees, species classification

### 7.3 Binary Lifting LCA: O(log n) per Query

**Algorithm:**
1. Ensure u and v are at the same depth by lifting the deeper node.
2. Simultaneously lift both nodes until they meet.

```
LCA(u, v):
    // Step 1: Equalize depths
    if depth[u] < depth[v]: swap(u, v)
    diff = depth[u] - depth[v]
    for j from LOG-1 down to 0:
        if (diff >> j) & 1:
            u = anc[u][j]

    // Now depth[u] == depth[v]
    if u == v: return u  // one is ancestor of the other

    // Step 2: Binary lift both simultaneously
    for j from LOG-1 down to 0:
        if anc[u][j] != anc[v][j]:
            u = anc[u][j]
            v = anc[v][j]

    // Now u and v are children of the LCA
    return anc[u][0]
```

**Why does Step 2 work?** We maintain the invariant that LCA is above both u and v. At each level j, if anc[u][j] == anc[v][j], jumping would overshoot (go above LCA). If they differ, jumping is safe (we stay below or at LCA). After the loop, u and v are the deepest nodes below LCA where they differ — so their parent is LCA.

### 7.4 Building the Tree: BFS-based Initialization

```
queue = [root]
parent[root] = -1
depth[root] = 0
while queue not empty:
    v = queue.pop_front()
    anc[v][0] = parent[v]
    for each child c of v:
        parent[c] = v
        depth[c] = depth[v] + 1
        queue.push(c)
// Then fill higher ancestors as described in Binary Lifting
```

### 7.5 Weighted LCA: Max/Min Edge on Path

Binary lifting can carry **additional data** along with ancestors. For example, to find the maximum edge weight on the path from u to v:

```
maxEdge[v][j] = maximum edge weight on path from v to its 2^j-th ancestor
maxEdge[v][0] = weight of edge (v, parent[v])
maxEdge[v][j] = max(maxEdge[v][j-1], maxEdge[anc[v][j-1]][j-1])
```

During LCA queries, track the maximum seen while lifting.

---

## 8. Euler Tour + Sparse Table (LCA in O(1))

### 8.1 The Euler Tour (In-Out DFS Sequence)

An **Euler Tour** of a tree records every node **each time it is visited** during a DFS — both when entering and returning from each child. For a tree with n nodes, the tour has length **2n - 1**.

```
euler[]  = sequence of node visits (length 2n-1)
first[]  = index of v's first appearance in euler[]
depth[]  = depth of euler[i]
```

**DFS-based construction:**
```
DFS(v, parent):
    euler.append(v)
    first[v] = euler.length - 1
    for each child c of v:
        DFS(c, v)
        euler.append(v)   // re-append v when returning from c
```

### 8.2 LCA via RMQ

**Key observation:** Between the first occurrences of u and v in the Euler tour, the node with **minimum depth** is exactly LCA(u, v).

```
LCA(u, v):
    l = min(first[u], first[v])
    r = max(first[u], first[v])
    // Find index of minimum depth in euler[l..r]
    idx = RMQ_index(depth_array, l, r)
    return euler[idx]
```

Where `depth_array[i] = depth[euler[i]]`.

**Why?** Walking the Euler tour from first[u] to first[v], you traverse the tree path u → LCA(u,v) → v. The node at minimum depth along this sub-tour is the highest point reached, which is exactly the LCA.

### 8.3 Building the RMQ on Depth Array

Apply a **Sparse Table for RMQ** to the `depth_array` of length 2n-1. This gives O(1) LCA queries after O(n log n) preprocessing.

```
Build Sparse Table on depth_array[0..2n-2]
```

This is the **optimal LCA algorithm** in practice for static trees with many queries: O(n log n) build, O(1) query.

### 8.4 ±1 RMQ Optimization (Linear Build)

In the Euler tour depth array, consecutive elements differ by exactly ±1 (depth increases by 1 when going to a child, decreases by 1 when backtracking). This special structure enables **O(n) build and O(1) query** using the Bender-Farach-Colton algorithm, which:
1. Divides the array into blocks of size (log n)/2.
2. Precomputes all possible ±1 patterns within blocks (there are only O(√n) distinct patterns).
3. Uses a Sparse Table for between-block queries.

This achieves **O(n) preprocessing, O(1) query** — the theoretical optimum. In practice, the standard Sparse Table approach (O(n log n) / O(1)) is simpler and often faster due to smaller constants.

---

## 9. Sparse Trees on Graphs

### 9.1 Trees vs. General Graphs

In graph theory, a **tree** is a connected acyclic undirected graph with n nodes and exactly n-1 edges. Trees are inherently *sparse* (minimal edges for connectivity).

When we say "Sparse Trees" in this context, we might mean:
- **Minimum Spanning Trees (MST)**: The sparsest connected subgraph preserving connectivity with minimum total edge weight.
- **Spanning Trees**: Any tree subgraph connecting all vertices.
- **Sparse representations** of tree structures for efficient ancestor/descendant queries.

### 9.2 Heavy-Light Decomposition (HLD)

HLD decomposes a tree into **chains** such that any root-to-leaf path passes through O(log n) chains. Combined with a Segment Tree or Sparse Table, it answers path queries (sum, max, etc.) in O(log² n) or O(log n) time.

**Decomposition rule:** For each node v, the **heavy child** is the child with the largest subtree. The heavy edge continues the current chain; light edges start new chains.

**Key property:** Any root-to-leaf path has at most O(log n) light edges (each light edge at least doubles the subtree size going down).

### 9.3 Centroid Decomposition

For queries about **distances between arbitrary pairs of nodes**, centroid decomposition provides a divide-and-conquer approach:
- Find the **centroid** of the tree (removing it splits the tree into components of size ≤ n/2).
- Recursively decompose each component.
- Depth: O(log n).

The **centroid tree** (the tree of centroids) is itself a balanced structure where ancestors represent the centroids that "govern" a node. This enables O(log n) distance queries and O(n log n) preprocessing for many path problems.

### 9.4 Link-Cut Trees

For **dynamic trees** that support edge insertions/deletions and path queries, **Link-Cut Trees** (Sleator-Tarjan) provide O(log n) amortized time for all operations. They use splay trees internally and maintain a form of heavy-path decomposition dynamically. This is advanced — beyond the scope of this guide's implementations but worth knowing exists.

---

## 10. Offline vs. Online Queries

### 10.1 Offline LCA: Tarjan's Algorithm

**Setting:** All queries are known in advance. Process the tree with DFS, using a Union-Find (DSU) structure.

**Algorithm sketch:**
```
DFS(v):
    mark[v] = VISITED
    ancestor[v] = v      // initial ancestor for DSU component

    for each child c of v:
        DFS(c)
        union(v, c)      // merge c's component into v's
        ancestor[find(v)] = v

    for each query (v, u) where mark[u] == VISITED:
        answer(v, u) = ancestor[find(u)]
```

**Complexity:** O((n + Q) α(n)) where α is the inverse Ackermann function — essentially O(n + Q).

**Advantage:** Nearly linear time. **Disadvantage:** Offline only (all queries must be known before processing starts).

### 10.2 Online LCA: Binary Lifting or Euler Tour + Sparse Table

These support queries arriving one at a time, without knowing future queries. Preprocessing is O(n log n), each query is O(log n) or O(1).

### 10.3 When to Use Which

| Scenario | Recommended |
|---|---|
| All queries known upfront, maximum speed | Tarjan's offline LCA |
| Interactive/streaming queries, moderate n | Binary Lifting |
| Interactive/streaming queries, many queries | Euler Tour + Sparse Table |
| Dynamic tree (edges change) | Link-Cut Trees |

---

## 11. Advanced Variants

### 11.1 Sparse Table for GCD

GCD is idempotent: gcd(x, x) = x. A Sparse Table enables O(1) range GCD queries:
```
ST[k][i] = gcd(A[i..i+2^k-1])
QUERY(l, r): k = log2(r-l+1); return gcd(ST[k][l], ST[k][r-2^k+1])
```

### 11.2 Sparse Table for Bitwise Operations

AND, OR, XOR (with care — XOR is not idempotent) can use Sparse Tables:
- AND: idempotent → O(1) query
- OR: idempotent → O(1) query
- XOR: not idempotent (x XOR x = 0) → must use O(log n) decomposition

### 11.3 2D Sparse Table

Extend to 2D arrays for rectangle minimum queries:
```
ST[k1][k2][i][j] = min over rectangle [i..i+2^k1-1][j..j+2^k2-1]
```
Build time: O(nm log n log m). Query: O(1).

### 11.4 Fractional Cascading

A technique to reduce O(log² n) queries (in structures combining binary search with Sparse Table) to O(log n) by precomputing pointers between levels. Used in advanced computational geometry.

### 11.5 Persistent Sparse Table

For problems requiring **historical versions** of the array (functional/persistent data structures):
- Each update creates a new version.
- Naive: O(n log n) per version → too slow.
- Use **persistent segment trees** instead; Sparse Tables are not naturally persistent due to their overlapping structure.

### 11.6 Sparse Table with Lazy Propagation

Sparse Tables do not support lazy propagation (unlike Segment Trees) because they are static. For range updates + range queries, use:
- Segment Tree with lazy propagation: O(log n) both
- Square Root Decomposition: O(√n) both (simpler to implement)

---

## 12. Complexity Summary

| Operation | Sparse Table | Segment Tree | Fenwick Tree | Binary Lifting |
|---|---|---|---|---|
| Build | O(n log n) | O(n) | O(n) | O(n log n) |
| Range Query (idempotent) | **O(1)** | O(log n) | O(log n) | — |
| Range Query (sum) | O(log n) | O(log n) | O(log n) | — |
| Point Update | **Not supported** | O(log n) | O(log n) | — |
| k-th Ancestor | — | — | — | O(log n) |
| LCA (binary lifting) | — | — | — | O(log n) |
| LCA (Euler + ST) | O(1) after setup | — | — | — |
| Space | O(n log n) | O(n) | O(n) | O(n log n) |

---

## 13. Complete Implementations in C

### 13.1 Sparse Table for RMQ (Range Minimum Query)

```c
/*
 * sparse_table_rmq.c
 * Static Range Minimum Query using Sparse Table
 * Build: O(n log n) | Query: O(1)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005
#define LOG  17       /* ceil(log2(MAXN)) */

typedef long long ll;

int n, q;
int A[MAXN];
int ST[LOG][MAXN];   /* ST[k][i] = min of A[i..i+2^k-1] */
int lg[MAXN];        /* precomputed floor(log2(i)) */

/* Precompute logarithms */
void precompute_log(int n) {
    lg[1] = 0;
    for (int i = 2; i <= n; i++)
        lg[i] = lg[i / 2] + 1;
}

/* Build the Sparse Table */
void build(int *arr, int n) {
    /* Level 0: intervals of length 1 */
    for (int i = 0; i < n; i++)
        ST[0][i] = arr[i];

    /* Fill levels 1..LOG-1 */
    for (int k = 1; (1 << k) <= n; k++) {
        for (int i = 0; i + (1 << k) - 1 < n; i++) {
            int left  = ST[k-1][i];
            int right = ST[k-1][i + (1 << (k-1))];
            ST[k][i] = (left < right) ? left : right;
        }
    }
}

/* O(1) RMQ query on [l, r] (inclusive, 0-indexed) */
int query_min(int l, int r) {
    int k = lg[r - l + 1];
    int left  = ST[k][l];
    int right = ST[k][r - (1 << k) + 1];
    return (left < right) ? left : right;
}

int main(void) {
    scanf("%d %d", &n, &q);
    for (int i = 0; i < n; i++)
        scanf("%d", &A[i]);

    precompute_log(n);
    build(A, n);

    for (int i = 0; i < q; i++) {
        int l, r;
        scanf("%d %d", &l, &r);
        printf("%d\n", query_min(l, r));
    }

    return 0;
}
```

### 13.2 Sparse Table for Range Maximum Query

```c
/*
 * sparse_table_rmaxq.c
 * Static Range Maximum Query using Sparse Table
 */

#include <stdio.h>
#include <stdlib.h>

#define MAXN 100005
#define LOG  17

int n, q;
int A[MAXN];
int ST[LOG][MAXN];
int lg[MAXN];

void precompute_log(int n) {
    lg[1] = 0;
    for (int i = 2; i <= n; i++)
        lg[i] = lg[i / 2] + 1;
}

void build_max(int *arr, int n) {
    for (int i = 0; i < n; i++)
        ST[0][i] = arr[i];

    for (int k = 1; (1 << k) <= n; k++) {
        for (int i = 0; i + (1 << k) - 1 < n; i++) {
            int left  = ST[k-1][i];
            int right = ST[k-1][i + (1 << (k-1))];
            ST[k][i] = (left > right) ? left : right;
        }
    }
}

int query_max(int l, int r) {
    int k = lg[r - l + 1];
    int left  = ST[k][l];
    int right = ST[k][r - (1 << k) + 1];
    return (left > right) ? left : right;
}

int main(void) {
    scanf("%d %d", &n, &q);
    for (int i = 0; i < n; i++)
        scanf("%d", &A[i]);

    precompute_log(n);
    build_max(A, n);

    for (int i = 0; i < q; i++) {
        int l, r;
        scanf("%d %d", &l, &r);
        printf("%d\n", query_max(l, r));
    }

    return 0;
}
```

### 13.3 Binary Lifting + LCA

```c
/*
 * binary_lifting_lca.c
 *
 * Features:
 *   - Rooted tree with n nodes (1-indexed)
 *   - Binary Lifting table: anc[v][k] = 2^k-th ancestor of v
 *   - LCA(u, v): O(log n)
 *   - k-th ancestor(v, k): O(log n)
 *   - Distance between nodes: depth[u] + depth[v] - 2 * depth[LCA(u,v)]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN   100005
#define LOG    17
#define INF    (-1)

/* Adjacency list */
typedef struct Edge { int to, next; } Edge;
Edge edges[2 * MAXN];
int head[MAXN], edge_cnt;

void add_edge(int u, int v) {
    edges[edge_cnt] = (Edge){v, head[u]};
    head[u] = edge_cnt++;
    edges[edge_cnt] = (Edge){u, head[v]};
    head[v] = edge_cnt++;
}

int n, q, root;
int anc[MAXN][LOG];  /* anc[v][k] = 2^k-th ancestor of v (-1 if none) */
int depth[MAXN];

/* BFS to set depth and anc[][0] (direct parent) */
void bfs(int root) {
    int queue[MAXN];
    int front = 0, back = 0;
    queue[back++] = root;
    depth[root] = 0;
    anc[root][0] = INF;   /* root has no parent */

    while (front < back) {
        int v = queue[front++];
        for (int e = head[v]; e != -1; e = edges[e].next) {
            int u = edges[e].to;
            if (u == anc[v][0]) continue;  /* skip parent */
            depth[u] = depth[v] + 1;
            anc[u][0] = v;
            queue[back++] = u;
        }
    }
}

/* Build binary lifting table after BFS */
void build_lifting(int n) {
    for (int k = 1; k < LOG; k++) {
        for (int v = 1; v <= n; v++) {
            if (anc[v][k-1] == INF)
                anc[v][k] = INF;
            else
                anc[v][k] = anc[ anc[v][k-1] ][k-1];
        }
    }
}

/* Return k-th ancestor of v, or INF if it doesn't exist */
int kth_ancestor(int v, int k) {
    for (int j = 0; j < LOG; j++) {
        if ((k >> j) & 1) {
            v = anc[v][j];
            if (v == INF) return INF;
        }
    }
    return v;
}

/* LCA of u and v */
int lca(int u, int v) {
    /* Ensure u is deeper */
    if (depth[u] < depth[v]) { int tmp = u; u = v; v = tmp; }

    /* Lift u to same depth as v */
    int diff = depth[u] - depth[v];
    for (int k = 0; k < LOG; k++)
        if ((diff >> k) & 1)
            u = anc[u][k];

    if (u == v) return u;  /* v was ancestor of u */

    /* Lift both until one step below LCA */
    for (int k = LOG - 1; k >= 0; k--) {
        if (anc[u][k] != anc[v][k]) {
            u = anc[u][k];
            v = anc[v][k];
        }
    }

    return anc[u][0];  /* parent of u (and v) is the LCA */
}

/* Distance between u and v */
int dist(int u, int v) {
    int l = lca(u, v);
    return depth[u] + depth[v] - 2 * depth[l];
}

int main(void) {
    scanf("%d", &n);
    memset(head, -1, sizeof(head));

    for (int i = 0; i < n - 1; i++) {
        int u, v;
        scanf("%d %d", &u, &v);
        add_edge(u, v);
    }

    root = 1;
    bfs(root);
    build_lifting(n);

    scanf("%d", &q);
    while (q--) {
        int type, u, v;
        scanf("%d %d %d", &type, &u, &v);

        if (type == 1) {
            /* LCA query */
            printf("LCA(%d, %d) = %d\n", u, v, lca(u, v));
        } else if (type == 2) {
            /* Distance query */
            printf("dist(%d, %d) = %d\n", u, v, dist(u, v));
        } else {
            /* k-th ancestor: u = node, v = k */
            int result = kth_ancestor(u, v);
            if (result == INF)
                printf("%d-th ancestor of %d does not exist\n", v, u);
            else
                printf("%d-th ancestor of %d = %d\n", v, u, result);
        }
    }

    return 0;
}
```

### 13.4 Euler Tour + Sparse Table LCA (O(1) Query)

```c
/*
 * euler_lca.c
 *
 * LCA in O(1) per query using:
 *   1. Euler Tour (DFS, 2n-1 length)
 *   2. Sparse Table for Range Minimum Query on the depth array
 *
 * Build: O(n log n)
 * Query: O(1)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN    100005
#define MAXE    (2 * MAXN)   /* Euler tour length */
#define LOG     18

/* Adjacency list */
typedef struct Edge { int to, next; } Edge;
Edge edges[2 * MAXN];
int head[MAXN], edge_cnt;

void add_edge(int u, int v) {
    edges[edge_cnt] = (Edge){v, head[u]};
    head[u] = edge_cnt++;
    edges[edge_cnt] = (Edge){u, head[v]};
    head[v] = edge_cnt++;
}

int n, q;
int euler[MAXE];       /* euler[i] = node at position i in Euler tour */
int euler_depth[MAXE]; /* depth of euler[i] */
int first[MAXN];       /* first occurrence of node v in euler[] */
int euler_size;        /* length of Euler tour = 2n-1 */
int dep[MAXN];         /* depth of each node */

int ST[LOG][MAXE];     /* Sparse Table on euler_depth */
int lg[MAXE];

/* Iterative DFS for Euler Tour (avoids stack overflow) */
void euler_tour(int root) {
    int stack[MAXN], par[MAXN], edge_ptr[MAXN];
    int top = 0;

    stack[top] = root;
    par[top] = -1;
    dep[root] = 0;
    memset(first, -1, sizeof(first));
    euler_size = 0;

    /* We use explicit DFS stack */
    /* For each node, we need to track which child to process next */
    int dfs_stack[MAXN * 2];
    int dfs_parent[MAXN * 2];
    int dfs_depth[MAXN * 2];
    int sp = 0;

    dfs_stack[sp] = root;
    dfs_parent[sp] = -1;
    dfs_depth[sp] = 0;
    sp++;

    /* Visited array for children tracking */
    int visited[MAXN];
    memset(visited, 0, sizeof(visited));

    /* Reset and use recursive DFS via call stack — safer for n<=10^4 */
    /* For larger n, use iterative version */
    euler_size = 0;
}

/* Recursive Euler Tour DFS */
void dfs(int v, int parent, int d) {
    dep[v] = d;
    if (first[v] == -1) first[v] = euler_size;
    euler[euler_size] = v;
    euler_depth[euler_size] = d;
    euler_size++;

    for (int e = head[v]; e != -1; e = edges[e].next) {
        int u = edges[e].to;
        if (u == parent) continue;
        dfs(u, v, d + 1);
        /* After returning from child, re-append v */
        euler[euler_size] = v;
        euler_depth[euler_size] = d;
        euler_size++;
    }
}

void precompute_log(int sz) {
    lg[1] = 0;
    for (int i = 2; i <= sz; i++)
        lg[i] = lg[i / 2] + 1;
}

void build_sparse_table(void) {
    int sz = euler_size;

    for (int i = 0; i < sz; i++)
        ST[0][i] = i;  /* Store indices, compare by euler_depth */

    for (int k = 1; (1 << k) <= sz; k++) {
        for (int i = 0; i + (1 << k) - 1 < sz; i++) {
            int left  = ST[k-1][i];
            int right = ST[k-1][i + (1 << (k-1))];
            ST[k][i] = (euler_depth[left] <= euler_depth[right]) ? left : right;
        }
    }
}

int rmq_index(int l, int r) {
    int k = lg[r - l + 1];
    int left  = ST[k][l];
    int right = ST[k][r - (1 << k) + 1];
    return (euler_depth[left] <= euler_depth[right]) ? left : right;
}

int lca(int u, int v) {
    int l = first[u], r = first[v];
    if (l > r) { int tmp = l; l = r; r = tmp; }
    int idx = rmq_index(l, r);
    return euler[idx];
}

int dist(int u, int v) {
    int l = lca(u, v);
    return dep[u] + dep[v] - 2 * dep[l];
}

int main(void) {
    scanf("%d", &n);
    memset(head, -1, sizeof(head));
    memset(first, -1, sizeof(first));

    for (int i = 0; i < n - 1; i++) {
        int u, v;
        scanf("%d %d", &u, &v);
        add_edge(u, v);
    }

    dfs(1, -1, 0);  /* Root at node 1, depth 0 */
    precompute_log(euler_size);
    build_sparse_table();

    scanf("%d", &q);
    while (q--) {
        int u, v;
        scanf("%d %d", &u, &v);
        int l = lca(u, v);
        printf("LCA(%d, %d) = %d, dist = %d\n", u, v, l, dist(u, v));
    }

    return 0;
}
```

### 13.5 Range GCD using Sparse Table

```c
/*
 * sparse_table_gcd.c
 * Range GCD Query in O(1) using Sparse Table
 * gcd is idempotent: gcd(x, x) = x
 */

#include <stdio.h>
#include <stdlib.h>

#define MAXN 100005
#define LOG  17

int n, q;
int A[MAXN];
int ST[LOG][MAXN];
int lg[MAXN];

int gcd(int a, int b) {
    while (b) { int t = b; b = a % b; a = t; }
    return a;
}

void precompute_log(int n) {
    lg[1] = 0;
    for (int i = 2; i <= n; i++)
        lg[i] = lg[i / 2] + 1;
}

void build(int *arr, int n) {
    for (int i = 0; i < n; i++)
        ST[0][i] = arr[i];
    for (int k = 1; (1 << k) <= n; k++)
        for (int i = 0; i + (1 << k) - 1 < n; i++)
            ST[k][i] = gcd(ST[k-1][i], ST[k-1][i + (1 << (k-1))]);
}

int query_gcd(int l, int r) {
    int k = lg[r - l + 1];
    return gcd(ST[k][l], ST[k][r - (1 << k) + 1]);
}

int main(void) {
    scanf("%d %d", &n, &q);
    for (int i = 0; i < n; i++)
        scanf("%d", &A[i]);

    precompute_log(n);
    build(A, n);

    for (int i = 0; i < q; i++) {
        int l, r;
        scanf("%d %d", &l, &r);
        printf("GCD[%d..%d] = %d\n", l, r, query_gcd(l, r));
    }

    return 0;
}
```

---

## 14. Complete Implementations in Go

### 14.1 Generic Sparse Table (Go 1.18+ Generics)

```go
// sparse_table.go
// Generic Sparse Table supporting any ordered type and idempotent operation.
// Build: O(n log n) | Query: O(1)

package main

import (
	"fmt"
	"math/bits"
)

// SparseTable is a generic sparse table for idempotent range queries.
type SparseTable[T any] struct {
	table [][]T
	merge func(a, b T) T
	n     int
}

// NewSparseTable builds a sparse table over arr using the given idempotent merge function.
func NewSparseTable[T any](arr []T, merge func(a, b T) T) *SparseTable[T] {
	n := len(arr)
	if n == 0 {
		return &SparseTable[T]{n: 0, merge: merge}
	}
	// Number of levels: floor(log2(n)) + 1
	levels := bits.Len(uint(n)) // = floor(log2(n)) + 1
	table := make([][]T, levels)
	table[0] = make([]T, n)
	copy(table[0], arr)

	for k := 1; k < levels; k++ {
		length := n - (1 << k) + 1
		if length <= 0 {
			break
		}
		table[k] = make([]T, length)
		half := 1 << (k - 1)
		for i := 0; i < length; i++ {
			table[k][i] = merge(table[k-1][i], table[k-1][i+half])
		}
	}

	return &SparseTable[T]{table: table, merge: merge, n: n}
}

// Query returns merge(arr[l..r]) in O(1) for idempotent operations.
// l and r are inclusive, 0-indexed.
func (st *SparseTable[T]) Query(l, r int) T {
	if l > r || l < 0 || r >= st.n {
		panic(fmt.Sprintf("SparseTable.Query: invalid range [%d, %d] for n=%d", l, r, st.n))
	}
	k := bits.Len(uint(r-l+1)) - 1 // floor(log2(r-l+1))
	return st.merge(st.table[k][l], st.table[k][r-(1<<k)+1])
}

// ---- Demo ----

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func gcd(a, b int) int {
	for b != 0 {
		a, b = b, a%b
	}
	return a
}

func main() {
	arr := []int{3, 1, 4, 1, 5, 9, 2, 6, 5, 3}
	fmt.Println("Array:", arr)

	// RMQ (Range Minimum Query)
	rmq := NewSparseTable(arr, minInt)
	fmt.Printf("Min [2..7] = %d (expected 2)\n", rmq.Query(2, 7))
	fmt.Printf("Min [0..9] = %d (expected 1)\n", rmq.Query(0, 9))

	// Range Max Query
	rmax := NewSparseTable(arr, maxInt)
	fmt.Printf("Max [0..5] = %d (expected 9)\n", rmax.Query(0, 5))

	// Range GCD Query
	rgcd := NewSparseTable(arr, gcd)
	fmt.Printf("GCD [0..2] = %d (expected 1)\n", rgcd.Query(0, 2))
	fmt.Printf("GCD [5..5] = %d (expected 9)\n", rgcd.Query(5, 5))
}
```

### 14.2 Binary Lifting + LCA in Go

```go
// binary_lifting_lca.go
// Binary Lifting for k-th ancestor and LCA queries on a rooted tree.
// Build: O(n log n) | Query: O(log n)

package main

import (
	"fmt"
	"math/bits"
)

const INF = -1

// Tree represents a rooted tree with binary lifting support.
type Tree struct {
	n     int
	adj   [][]int
	anc   [][]int // anc[v][k] = 2^k-th ancestor of v
	depth []int
	log   int    // number of binary lifting levels
}

// NewTree creates an empty tree with n nodes (1-indexed).
func NewTree(n int) *Tree {
	log := bits.Len(uint(n)) + 1
	anc := make([][]int, n+1)
	for i := range anc {
		anc[i] = make([]int, log)
		for j := range anc[i] {
			anc[i][j] = INF
		}
	}
	return &Tree{
		n:     n,
		adj:   make([][]int, n+1),
		anc:   anc,
		depth: make([]int, n+1),
		log:   log,
	}
}

// AddEdge adds an undirected edge between u and v.
func (t *Tree) AddEdge(u, v int) {
	t.adj[u] = append(t.adj[u], v)
	t.adj[v] = append(t.adj[v], u)
}

// Build runs BFS from root and constructs the binary lifting table.
func (t *Tree) Build(root int) {
	// BFS to set depths and direct parents (anc[][0])
	visited := make([]bool, t.n+1)
	queue := []int{root}
	visited[root] = true
	t.depth[root] = 0
	t.anc[root][0] = INF // root has no parent

	for len(queue) > 0 {
		v := queue[0]
		queue = queue[1:]
		for _, u := range t.adj[v] {
			if visited[u] {
				continue
			}
			visited[u] = true
			t.depth[u] = t.depth[v] + 1
			t.anc[u][0] = v
			queue = append(queue, u)
		}
	}

	// Fill binary lifting table level by level
	for k := 1; k < t.log; k++ {
		for v := 1; v <= t.n; v++ {
			if t.anc[v][k-1] == INF {
				t.anc[v][k] = INF
			} else {
				t.anc[v][k] = t.anc[t.anc[v][k-1]][k-1]
			}
		}
	}
}

// KthAncestor returns the k-th ancestor of v, or INF if it doesn't exist.
func (t *Tree) KthAncestor(v, k int) int {
	for j := 0; j < t.log; j++ {
		if (k>>j)&1 == 1 {
			v = t.anc[v][j]
			if v == INF {
				return INF
			}
		}
	}
	return v
}

// LCA returns the Lowest Common Ancestor of u and v.
func (t *Tree) LCA(u, v int) int {
	// Ensure u is deeper
	if t.depth[u] < t.depth[v] {
		u, v = v, u
	}

	// Lift u to same depth as v
	diff := t.depth[u] - t.depth[v]
	for k := 0; k < t.log; k++ {
		if (diff>>k)&1 == 1 {
			u = t.anc[u][k]
		}
	}

	if u == v {
		return u
	}

	// Lift both until one step below LCA
	for k := t.log - 1; k >= 0; k-- {
		if t.anc[u][k] != t.anc[v][k] {
			u = t.anc[u][k]
			v = t.anc[v][k]
		}
	}

	return t.anc[u][0]
}

// Dist returns the number of edges on the path from u to v.
func (t *Tree) Dist(u, v int) int {
	l := t.LCA(u, v)
	return t.depth[u] + t.depth[v] - 2*t.depth[l]
}

// ---- Demo ----

func main() {
	/*
	 * Example Tree (1-indexed):
	 *        1
	 *       / \
	 *      2   3
	 *     / \   \
	 *    4   5   6
	 *   /
	 *  7
	 */
	n := 7
	tree := NewTree(n)
	edges := [][2]int{{1, 2}, {1, 3}, {2, 4}, {2, 5}, {3, 6}, {4, 7}}
	for _, e := range edges {
		tree.AddEdge(e[0], e[1])
	}
	tree.Build(1) // root = 1

	fmt.Println("=== LCA Queries ===")
	pairs := [][2]int{{4, 5}, {7, 6}, {7, 5}, {3, 7}, {1, 7}}
	for _, p := range pairs {
		u, v := p[0], p[1]
		fmt.Printf("LCA(%d, %d) = %d, dist = %d\n",
			u, v, tree.LCA(u, v), tree.Dist(u, v))
	}

	fmt.Println("\n=== k-th Ancestor Queries ===")
	type AncQuery struct{ v, k int }
	queries := []AncQuery{{7, 1}, {7, 2}, {7, 3}, {6, 1}, {6, 2}}
	for _, aq := range queries {
		res := tree.KthAncestor(aq.v, aq.k)
		if res == INF {
			fmt.Printf("%d-th ancestor of %d: does not exist\n", aq.k, aq.v)
		} else {
			fmt.Printf("%d-th ancestor of %d: %d\n", aq.k, aq.v, res)
		}
	}

	fmt.Println("\n=== Depths ===")
	for v := 1; v <= n; v++ {
		fmt.Printf("depth[%d] = %d\n", v, tree.depth[v])
	}
}
```

### 14.3 Euler Tour + Sparse Table LCA (O(1) Query) in Go

```go
// euler_lca.go
// O(1) LCA using Euler Tour + Sparse Table RMQ on depth array.
// Build: O(n log n) | Query: O(1)

package main

import (
	"fmt"
	"math/bits"
)

type LCAEuler struct {
	n          int
	euler      []int  // Euler tour node sequence (length 2n-1)
	eulerDepth []int  // depth at each position in Euler tour
	first      []int  // first[v] = first position of v in euler[]
	depth      []int  // depth[v]
	adj        [][]int

	// Sparse Table on eulerDepth
	st  [][]int // st[k][i] = index in euler[] of min depth in [i..i+2^k-1]
	log int
}

func NewLCAEuler(n int) *LCAEuler {
	return &LCAEuler{
		n:     n,
		adj:   make([][]int, n+1),
		first: make([]int, n+1),
		depth: make([]int, n+1),
	}
}

func (l *LCAEuler) AddEdge(u, v int) {
	l.adj[u] = append(l.adj[u], v)
	l.adj[v] = append(l.adj[v], u)
}

// dfs performs the Euler Tour
func (l *LCAEuler) dfs(v, parent, d int) {
	l.depth[v] = d
	l.first[v] = len(l.euler)
	l.euler = append(l.euler, v)
	l.eulerDepth = append(l.eulerDepth, d)

	for _, u := range l.adj[v] {
		if u == parent {
			continue
		}
		l.dfs(u, v, d+1)
		// Return to v after visiting child u
		l.euler = append(l.euler, v)
		l.eulerDepth = append(l.eulerDepth, d)
	}
}

// Build constructs the Euler tour and Sparse Table.
func (l *LCAEuler) Build(root int) {
	l.euler = l.euler[:0]
	l.eulerDepth = l.eulerDepth[:0]
	l.dfs(root, -1, 0)

	sz := len(l.euler)
	l.log = bits.Len(uint(sz)) // number of levels

	// Build sparse table: store indices, compare by depth
	l.st = make([][]int, l.log)
	l.st[0] = make([]int, sz)
	for i := 0; i < sz; i++ {
		l.st[0][i] = i
	}

	for k := 1; k < l.log; k++ {
		length := sz - (1 << k) + 1
		if length <= 0 {
			break
		}
		l.st[k] = make([]int, length)
		half := 1 << (k - 1)
		for i := 0; i < length; i++ {
			a := l.st[k-1][i]
			b := l.st[k-1][i+half]
			if l.eulerDepth[a] <= l.eulerDepth[b] {
				l.st[k][i] = a
			} else {
				l.st[k][i] = b
			}
		}
	}
}

// rmqIndex returns the index in euler[] of the minimum-depth element in [lo..hi].
func (l *LCAEuler) rmqIndex(lo, hi int) int {
	k := bits.Len(uint(hi-lo+1)) - 1
	a := l.st[k][lo]
	b := l.st[k][hi-(1<<k)+1]
	if l.eulerDepth[a] <= l.eulerDepth[b] {
		return a
	}
	return b
}

// LCA returns the lowest common ancestor of u and v. O(1).
func (l *LCAEuler) LCA(u, v int) int {
	lo, hi := l.first[u], l.first[v]
	if lo > hi {
		lo, hi = hi, lo
	}
	idx := l.rmqIndex(lo, hi)
	return l.euler[idx]
}

// Dist returns the edge-distance between u and v.
func (l *LCAEuler) Dist(u, v int) int {
	anc := l.LCA(u, v)
	return l.depth[u] + l.depth[v] - 2*l.depth[anc]
}

func main() {
	/*
	 * Tree:
	 *         1
	 *        /|\
	 *       2  3  4
	 *      /|     \
	 *     5  6     7
	 *        |
	 *        8
	 */
	n := 8
	lca := NewLCAEuler(n)
	edges := [][2]int{
		{1, 2}, {1, 3}, {1, 4},
		{2, 5}, {2, 6},
		{4, 7},
		{6, 8},
	}
	for _, e := range edges {
		lca.AddEdge(e[0], e[1])
	}
	lca.Build(1)

	fmt.Println("=== O(1) LCA (Euler Tour + Sparse Table) ===")
	queries := [][2]int{{5, 8}, {5, 7}, {3, 8}, {7, 6}, {1, 8}, {8, 8}}
	for _, q := range queries {
		u, v := q[0], q[1]
		fmt.Printf("LCA(%d, %d) = %d, dist = %d\n",
			u, v, lca.LCA(u, v), lca.Dist(u, v))
	}

	fmt.Println("\n=== Euler Tour ===")
	fmt.Println("euler:", lca.euler)
	fmt.Println("eulerDepth:", lca.eulerDepth)
	fmt.Println("first:", lca.first[1:])
}
```

### 14.4 Offline LCA (Tarjan's Algorithm) in Go

```go
// tarjan_lca.go
// Offline LCA using Tarjan's algorithm with Union-Find (DSU).
// Build + all queries: O((n + Q) * alpha(n))

package main

import "fmt"

// DSU (Disjoint Set Union / Union-Find)
type DSU struct {
	parent, rank []int
}

func NewDSU(n int) *DSU {
	p := make([]int, n+1)
	r := make([]int, n+1)
	for i := range p {
		p[i] = i
	}
	return &DSU{parent: p, rank: r}
}

func (d *DSU) Find(x int) int {
	if d.parent[x] != x {
		d.parent[x] = d.Find(d.parent[x]) // path compression
	}
	return d.parent[x]
}

func (d *DSU) Union(x, y int) {
	rx, ry := d.Find(x), d.Find(y)
	if rx == ry {
		return
	}
	if d.rank[rx] < d.rank[ry] {
		rx, ry = ry, rx
	}
	d.parent[ry] = rx
	if d.rank[rx] == d.rank[ry] {
		d.rank[rx]++
	}
}

type Query struct {
	other, idx int
}

type TarjanLCA struct {
	n       int
	adj     [][]int
	queries [][]Query // queries[v] = list of (other node, query index) for queries involving v
	answers []int
	color   []int // 0=white, 1=gray, 2=black
	anc     []int // ancestor representative for DSU
	dsu     *DSU
}

func NewTarjanLCA(n, q int) *TarjanLCA {
	t := &TarjanLCA{
		n:       n,
		adj:     make([][]int, n+1),
		queries: make([][]Query, n+1),
		answers: make([]int, q),
		color:   make([]int, n+1),
		anc:     make([]int, n+1),
		dsu:     NewDSU(n),
	}
	for i := range t.anc {
		t.anc[i] = i
	}
	return t
}

func (t *TarjanLCA) AddEdge(u, v int) {
	t.adj[u] = append(t.adj[u], v)
	t.adj[v] = append(t.adj[v], u)
}

func (t *TarjanLCA) AddQuery(u, v, idx int) {
	t.queries[u] = append(t.queries[u], Query{v, idx})
	t.queries[v] = append(t.queries[v], Query{u, idx})
}

// dfs performs the Tarjan LCA algorithm
func (t *TarjanLCA) dfs(v, parent int) {
	t.color[v] = 1 // gray: currently processing
	t.anc[t.dsu.Find(v)] = v

	for _, u := range t.adj[v] {
		if u == parent {
			continue
		}
		t.dfs(u, v)
		t.dsu.Union(v, u)
		t.anc[t.dsu.Find(v)] = v
	}

	// Process all queries involving v
	for _, q := range t.queries[v] {
		if t.color[q.other] == 2 { // black: fully processed
			t.answers[q.idx] = t.anc[t.dsu.Find(q.other)]
		}
	}

	t.color[v] = 2 // black: fully processed
}

func (t *TarjanLCA) Solve(root int) {
	t.dfs(root, -1)
}

func main() {
	/*
	 * Tree:
	 *     1
	 *    / \
	 *   2   3
	 *  / \
	 * 4   5
	 */
	n := 5
	queries := [][2]int{{4, 5}, {4, 3}, {2, 3}, {1, 4}}
	q := len(queries)

	t := NewTarjanLCA(n, q)
	edges := [][2]int{{1, 2}, {1, 3}, {2, 4}, {2, 5}}
	for _, e := range edges {
		t.AddEdge(e[0], e[1])
	}
	for i, qp := range queries {
		t.AddQuery(qp[0], qp[1], i)
	}

	t.Solve(1)

	fmt.Println("=== Offline LCA (Tarjan's Algorithm) ===")
	for i, qp := range queries {
		fmt.Printf("LCA(%d, %d) = %d\n", qp[0], qp[1], t.answers[i])
	}
}
```

---

## 15. Complete Implementations in Rust

### 15.1 Generic Sparse Table in Rust

```rust
// sparse_table.rs
// Generic Sparse Table for idempotent range queries.
// Build: O(n log n) | Query: O(1)

use std::ops::Fn;

pub struct SparseTable<T: Clone> {
    table: Vec<Vec<T>>,
    merge: Box<dyn Fn(&T, &T) -> T>,
    n: usize,
}

impl<T: Clone> SparseTable<T> {
    /// Build a sparse table over `arr` using the idempotent `merge` function.
    pub fn new<F>(arr: &[T], merge: F) -> Self
    where
        F: Fn(&T, &T) -> T + 'static,
    {
        let n = arr.len();
        assert!(n > 0, "SparseTable: array must be non-empty");

        let levels = (usize::BITS - n.leading_zeros()) as usize; // floor(log2(n)) + 1
        let mut table: Vec<Vec<T>> = Vec::with_capacity(levels);

        // Level 0: the array itself
        table.push(arr.to_vec());

        // Fill higher levels
        for k in 1..levels {
            let half = 1usize << (k - 1);
            let length = n.saturating_sub((1 << k) - 1);
            let mut row = Vec::with_capacity(length);
            for i in 0..length {
                let val = merge(&table[k - 1][i], &table[k - 1][i + half]);
                row.push(val);
            }
            table.push(row);
        }

        SparseTable {
            table,
            merge: Box::new(merge),
            n,
        }
    }

    /// Query the range [l, r] (inclusive, 0-indexed) in O(1).
    pub fn query(&self, l: usize, r: usize) -> T {
        assert!(l <= r && r < self.n, "SparseTable::query: invalid range");
        let len = r - l + 1;
        let k = (usize::BITS - len.leading_zeros() - 1) as usize; // floor(log2(len))
        (self.merge)(&self.table[k][l], &self.table[k][r - (1 << k) + 1])
    }

    /// Query and return the index of the result (useful when T is comparable).
    pub fn query_index<F>(&self, l: usize, r: usize, cmp: F) -> usize
    where
        F: Fn(&T, &T) -> bool, // cmp(a, b) = true means a is "better"
    {
        assert!(l <= r && r < self.n);
        let len = r - l + 1;
        let k = (usize::BITS - len.leading_zeros() - 1) as usize;
        let left_idx = l;
        let right_idx = r - (1 << k) + 1;

        // We need index into level 0 (original array), not ST table
        // For this, we'd need an index table. Use the simpler query() instead.
        // This is a simplified version returning the left index of the winning half.
        if cmp(&self.table[k][left_idx], &self.table[k][right_idx]) {
            left_idx
        } else {
            right_idx
        }
    }
}

// ---- Range Minimum Query ----

pub struct RMQ {
    st: SparseTable<i64>,
}

impl RMQ {
    pub fn new(arr: &[i64]) -> Self {
        RMQ {
            st: SparseTable::new(arr, |&a, &b| a.min(b)),
        }
    }

    pub fn query(&self, l: usize, r: usize) -> i64 {
        self.st.query(l, r)
    }
}

// ---- Range Maximum Query ----

pub struct RMaxQ {
    st: SparseTable<i64>,
}

impl RMaxQ {
    pub fn new(arr: &[i64]) -> Self {
        RMaxQ {
            st: SparseTable::new(arr, |&a, &b| a.max(b)),
        }
    }

    pub fn query(&self, l: usize, r: usize) -> i64 {
        self.st.query(l, r)
    }
}

// ---- Range GCD Query ----

fn gcd(a: i64, b: i64) -> i64 {
    if b == 0 { a } else { gcd(b, a % b) }
}

pub struct RGCD {
    st: SparseTable<i64>,
}

impl RGCD {
    pub fn new(arr: &[i64]) -> Self {
        RGCD {
            st: SparseTable::new(arr, |&a, &b| gcd(a, b)),
        }
    }

    pub fn query(&self, l: usize, r: usize) -> i64 {
        self.st.query(l, r)
    }
}

fn main() {
    let arr: Vec<i64> = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];
    println!("Array: {:?}", arr);

    let rmq = RMQ::new(&arr);
    println!("Min [2..7] = {} (expected 2)", rmq.query(2, 7));
    println!("Min [0..10] = {} (expected 1)", rmq.query(0, 10));

    let rmax = RMaxQ::new(&arr);
    println!("Max [0..5] = {} (expected 9)", rmax.query(0, 5));

    let rgcd = RGCD::new(&arr);
    println!("GCD [0..2] = {} (expected 1)", rgcd.query(0, 2));

    // Range AND / OR
    let and_st: SparseTable<i64> = SparseTable::new(&arr, |&a, &b| a & b);
    println!("AND [0..3] = {} (expected {})", and_st.query(0, 3), 3i64 & 1 & 4 & 1);

    let or_st: SparseTable<i64> = SparseTable::new(&arr, |&a, &b| a | b);
    println!("OR [0..3] = {}", or_st.query(0, 3));
}
```

### 15.2 Binary Lifting + LCA in Rust

```rust
// binary_lifting_lca.rs
// Binary Lifting for k-th ancestor and LCA on a rooted tree.
// Build: O(n log n) | Query: O(log n)

const NO_PARENT: usize = usize::MAX;

pub struct BinaryLiftingTree {
    n: usize,
    adj: Vec<Vec<usize>>,
    anc: Vec<Vec<usize>>, // anc[v][k] = 2^k-th ancestor (NO_PARENT if none)
    depth: Vec<usize>,
    log: usize,
}

impl BinaryLiftingTree {
    /// Create a new tree with `n` nodes (1-indexed, node 0 unused).
    pub fn new(n: usize) -> Self {
        let log = (usize::BITS - n.leading_zeros()) as usize + 1;
        let anc = vec![vec![NO_PARENT; log]; n + 1];
        BinaryLiftingTree {
            n,
            adj: vec![vec![]; n + 1],
            anc,
            depth: vec![0; n + 1],
            log,
        }
    }

    /// Add an undirected edge between u and v.
    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }

    /// Build the binary lifting table with BFS from `root`.
    pub fn build(&mut self, root: usize) {
        let mut queue = std::collections::VecDeque::new();
        let mut visited = vec![false; self.n + 1];

        queue.push_back(root);
        visited[root] = true;
        self.depth[root] = 0;
        self.anc[root][0] = NO_PARENT;

        // BFS
        while let Some(v) = queue.pop_front() {
            for &u in &self.adj[v].clone() {
                if visited[u] {
                    continue;
                }
                visited[u] = true;
                self.depth[u] = self.depth[v] + 1;
                self.anc[u][0] = v;
                queue.push_back(u);
            }
        }

        // Fill binary lifting table
        for k in 1..self.log {
            for v in 1..=self.n {
                let mid = self.anc[v][k - 1];
                self.anc[v][k] = if mid == NO_PARENT {
                    NO_PARENT
                } else {
                    self.anc[mid][k - 1]
                };
            }
        }
    }

    /// Return the k-th ancestor of v, or None if it doesn't exist.
    pub fn kth_ancestor(&self, mut v: usize, mut k: usize) -> Option<usize> {
        for j in 0..self.log {
            if (k >> j) & 1 == 1 {
                v = self.anc[v][j];
                if v == NO_PARENT {
                    return None;
                }
            }
        }
        Some(v)
    }

    /// Return the LCA of u and v.
    pub fn lca(&self, mut u: usize, mut v: usize) -> usize {
        // Ensure u is deeper
        if self.depth[u] < self.depth[v] {
            std::mem::swap(&mut u, &mut v);
        }

        // Lift u to same depth
        let diff = self.depth[u] - self.depth[v];
        for k in 0..self.log {
            if (diff >> k) & 1 == 1 {
                u = self.anc[u][k];
            }
        }

        if u == v {
            return u;
        }

        // Lift both until one step below LCA
        for k in (0..self.log).rev() {
            if self.anc[u][k] != self.anc[v][k] {
                u = self.anc[u][k];
                v = self.anc[v][k];
            }
        }

        self.anc[u][0]
    }

    /// Return the edge-distance between u and v.
    pub fn dist(&self, u: usize, v: usize) -> usize {
        let l = self.lca(u, v);
        self.depth[u] + self.depth[v] - 2 * self.depth[l]
    }

    pub fn depth_of(&self, v: usize) -> usize {
        self.depth[v]
    }
}

fn main() {
    /*
     * Tree (1-indexed):
     *        1
     *       / \
     *      2   3
     *     / \   \
     *    4   5   6
     *   /
     *  7
     */
    let n = 7;
    let mut tree = BinaryLiftingTree::new(n);
    let edges = vec![(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (4, 7)];
    for (u, v) in &edges {
        tree.add_edge(*u, *v);
    }
    tree.build(1);

    println!("=== LCA Queries ===");
    let lca_queries = vec![(4, 5), (7, 6), (7, 5), (3, 7), (1, 7), (7, 7)];
    for (u, v) in &lca_queries {
        println!(
            "LCA({}, {}) = {}, dist = {}",
            u, v,
            tree.lca(*u, *v),
            tree.dist(*u, *v)
        );
    }

    println!("\n=== k-th Ancestor Queries ===");
    let anc_queries = vec![(7, 1), (7, 2), (7, 3), (6, 1), (6, 2), (1, 1)];
    for (v, k) in &anc_queries {
        match tree.kth_ancestor(*v, *k) {
            Some(a) => println!("{}-th ancestor of {} = {}", k, v, a),
            None => println!("{}-th ancestor of {} = (none)", k, v),
        }
    }

    println!("\n=== Depths ===");
    for v in 1..=n {
        println!("depth[{}] = {}", v, tree.depth_of(v));
    }
}
```

### 15.3 Euler Tour + Sparse Table LCA (O(1)) in Rust

```rust
// euler_lca.rs
// O(1) LCA using Euler Tour + Sparse Table RMQ.
// Build: O(n log n) | Query: O(1)

pub struct EulerLCA {
    n: usize,
    adj: Vec<Vec<usize>>,
    euler: Vec<usize>,       // Euler tour node sequence
    euler_depth: Vec<usize>, // depth at each Euler tour position
    first: Vec<usize>,       // first[v] = first position of v in euler
    depth: Vec<usize>,       // depth[v]

    // Sparse Table: st[k][i] = index of min-depth in euler[i..i+2^k-1]
    st: Vec<Vec<usize>>,
    log: usize,
}

impl EulerLCA {
    pub fn new(n: usize) -> Self {
        EulerLCA {
            n,
            adj: vec![vec![]; n + 1],
            euler: Vec::with_capacity(2 * n),
            euler_depth: Vec::with_capacity(2 * n),
            first: vec![0; n + 1],
            depth: vec![0; n + 1],
            st: Vec::new(),
            log: 0,
        }
    }

    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }

    /// Iterative DFS for Euler Tour (avoids stack overflow for large n).
    fn euler_tour_iterative(&mut self, root: usize) {
        // Stack entries: (node, parent, depth, child_index)
        let mut stack: Vec<(usize, usize, usize, usize)> = Vec::new();
        stack.push((root, usize::MAX, 0, 0));

        while let Some((v, parent, d, ci)) = stack.last_mut() {
            let v = *v;
            let parent = *parent;
            let d = *d;
            let ci_val = *ci;

            if ci_val == 0 {
                // First visit to v
                self.depth[v] = d;
                self.first[v] = self.euler.len();
                self.euler.push(v);
                self.euler_depth.push(d);
            }

            // Find next unvisited child
            let children = self.adj[v].clone();
            let next_child = children
                .iter()
                .skip(ci_val)
                .position(|&u| u != parent)
                .map(|pos| pos + ci_val);

            if let Some(ci_next) = next_child {
                let child = children[ci_next];
                if stack.last_mut().is_some() {
                    stack.last_mut().unwrap().3 = ci_next + 1;
                }
                stack.push((child, v, d + 1, 0));
            } else {
                // All children processed; pop and return to parent
                stack.pop();
                if let Some((pv, _, pd, _)) = stack.last() {
                    self.euler.push(*pv);
                    self.euler_depth.push(*pd);
                }
            }
        }
    }

    /// Build the Euler tour and Sparse Table.
    pub fn build(&mut self, root: usize) {
        self.euler_tour_iterative(root);

        let sz = self.euler.len();
        self.log = (usize::BITS - sz.leading_zeros()) as usize;

        // Level 0: identity (index maps to itself)
        let mut st = vec![vec![0usize; sz]; self.log];
        for i in 0..sz {
            st[0][i] = i;
        }

        for k in 1..self.log {
            let half = 1 << (k - 1);
            let length = sz.saturating_sub((1 << k) - 1);
            for i in 0..length {
                let a = st[k - 1][i];
                let b = st[k - 1][i + half];
                st[k][i] = if self.euler_depth[a] <= self.euler_depth[b] {
                    a
                } else {
                    b
                };
            }
        }

        self.st = st;
    }

    fn rmq_index(&self, lo: usize, hi: usize) -> usize {
        let len = hi - lo + 1;
        let k = (usize::BITS - len.leading_zeros() - 1) as usize;
        let a = self.st[k][lo];
        let b = self.st[k][hi - (1 << k) + 1];
        if self.euler_depth[a] <= self.euler_depth[b] { a } else { b }
    }

    /// O(1) LCA query.
    pub fn lca(&self, u: usize, v: usize) -> usize {
        let (lo, hi) = if self.first[u] <= self.first[v] {
            (self.first[u], self.first[v])
        } else {
            (self.first[v], self.first[u])
        };
        let idx = self.rmq_index(lo, hi);
        self.euler[idx]
    }

    /// Edge-distance between u and v.
    pub fn dist(&self, u: usize, v: usize) -> usize {
        let l = self.lca(u, v);
        self.depth[u] + self.depth[v] - 2 * self.depth[l]
    }

    pub fn depth_of(&self, v: usize) -> usize {
        self.depth[v]
    }
}

fn main() {
    /*
     * Tree:
     *        1
     *       /|\
     *      2  3  4
     *     /|     \
     *    5  6     7
     *       |
     *       8
     */
    let n = 8;
    let mut lca = EulerLCA::new(n);
    let edges = vec![
        (1, 2), (1, 3), (1, 4),
        (2, 5), (2, 6),
        (4, 7),
        (6, 8),
    ];
    for (u, v) in &edges {
        lca.add_edge(*u, *v);
    }
    lca.build(1);

    println!("=== O(1) LCA (Euler Tour + Sparse Table) ===");
    let queries = vec![
        (5, 8), (5, 7), (3, 8), (7, 6), (1, 8), (8, 8), (2, 4),
    ];
    for (u, v) in &queries {
        println!(
            "LCA({}, {}) = {}, dist = {}",
            u, v,
            lca.lca(*u, *v),
            lca.dist(*u, *v)
        );
    }

    println!("\n=== Node Depths ===");
    for v in 1..=n {
        println!("depth[{}] = {}", v, lca.depth_of(v));
    }

    println!("\n=== Euler Tour ===");
    println!("euler:       {:?}", lca.euler);
    println!("euler_depth: {:?}", lca.euler_depth);
}
```

### 15.4 Offline Tarjan LCA in Rust

```rust
// tarjan_lca.rs
// Offline LCA using Tarjan's algorithm + DSU.
// Complexity: O((n + Q) * alpha(n))

#[derive(Clone)]
struct DSU {
    parent: Vec<usize>,
    rank: Vec<usize>,
    ancestor: Vec<usize>, // LCA representative
}

impl DSU {
    fn new(n: usize) -> Self {
        DSU {
            parent: (0..=n).collect(),
            rank: vec![0; n + 1],
            ancestor: (0..=n).collect(),
        }
    }

    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // path compression
        }
        self.parent[x]
    }

    fn union(&mut self, x: usize, y: usize) {
        let rx = self.find(x);
        let ry = self.find(y);
        if rx == ry {
            return;
        }
        if self.rank[rx] < self.rank[ry] {
            self.parent[rx] = ry;
        } else if self.rank[rx] > self.rank[ry] {
            self.parent[ry] = rx;
        } else {
            self.parent[ry] = rx;
            self.rank[rx] += 1;
        }
    }
}

pub struct TarjanLCA {
    n: usize,
    adj: Vec<Vec<usize>>,
    query_list: Vec<Vec<(usize, usize)>>, // (other_node, query_index)
    pub answers: Vec<usize>,
    color: Vec<u8>, // 0=white, 1=gray, 2=black
    dsu: DSU,
}

impl TarjanLCA {
    pub fn new(n: usize, num_queries: usize) -> Self {
        TarjanLCA {
            n,
            adj: vec![vec![]; n + 1],
            query_list: vec![vec![]; n + 1],
            answers: vec![0; num_queries],
            color: vec![0; n + 1],
            dsu: DSU::new(n),
        }
    }

    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }

    pub fn add_query(&mut self, u: usize, v: usize, idx: usize) {
        self.query_list[u].push((v, idx));
        self.query_list[v].push((u, idx));
    }

    fn dfs(&mut self, v: usize, parent: usize) {
        self.color[v] = 1;
        let root = self.dsu.find(v);
        self.dsu.ancestor[root] = v;

        let children: Vec<usize> = self.adj[v].iter().copied().filter(|&u| u != parent).collect();
        for u in children {
            self.dfs(u, v);
            self.dsu.union(v, u);
            let root = self.dsu.find(v);
            self.dsu.ancestor[root] = v;
        }

        let queries: Vec<(usize, usize)> = self.query_list[v].clone();
        for (other, qi) in queries {
            if self.color[other] == 2 {
                let root = self.dsu.find(other);
                self.answers[qi] = self.dsu.ancestor[root];
            }
        }

        self.color[v] = 2;
    }

    pub fn solve(&mut self, root: usize) {
        self.dfs(root, usize::MAX);
    }
}

fn main() {
    /*
     * Tree:
     *       1
     *      / \
     *     2   3
     *    / \
     *   4   5
     *  /
     * 6
     */
    let n = 6;
    let raw_queries: Vec<(usize, usize)> = vec![
        (4, 5), (6, 3), (6, 5), (2, 3), (1, 6),
    ];
    let q = raw_queries.len();

    let mut tlca = TarjanLCA::new(n, q);
    let edges = vec![(1, 2), (1, 3), (2, 4), (2, 5), (4, 6)];
    for (u, v) in &edges {
        tlca.add_edge(*u, *v);
    }
    for (i, (u, v)) in raw_queries.iter().enumerate() {
        tlca.add_query(*u, *v, i);
    }
    tlca.solve(1);

    println!("=== Offline LCA (Tarjan's Algorithm) ===");
    for (i, (u, v)) in raw_queries.iter().enumerate() {
        println!("LCA({}, {}) = {}", u, v, tlca.answers[i]);
    }
}
```

### 15.5 2D Sparse Table in Rust

```rust
// sparse_table_2d.rs
// 2D Sparse Table for rectangle minimum queries.
// Build: O(nm log n log m) | Query: O(1)

pub struct SparseTable2D {
    table: Vec<Vec<Vec<Vec<i64>>>>, // table[k1][k2][i][j]
    rows: usize,
    cols: usize,
    log_rows: usize,
    log_cols: usize,
}

fn floor_log2(x: usize) -> usize {
    if x == 0 { 0 } else { usize::BITS as usize - x.leading_zeros() as usize - 1 }
}

impl SparseTable2D {
    pub fn new(grid: &Vec<Vec<i64>>) -> Self {
        let rows = grid.len();
        let cols = grid[0].len();
        let log_rows = floor_log2(rows) + 1;
        let log_cols = floor_log2(cols) + 1;

        // table[k1][k2][i][j] = min over rows [i..i+2^k1-1], cols [j..j+2^k2-1]
        let mut table = vec![
            vec![
                vec![vec![i64::MAX; cols]; rows];
                log_cols
            ];
            log_rows
        ];

        // Fill k1=0, k2=0: the grid itself
        for i in 0..rows {
            for j in 0..cols {
                table[0][0][i][j] = grid[i][j];
            }
        }

        // Fix k1=0, vary k2 (extend along columns)
        for k2 in 1..log_cols {
            let half2 = 1 << (k2 - 1);
            for i in 0..rows {
                for j in 0..cols.saturating_sub((1 << k2) - 1) {
                    table[0][k2][i][j] =
                        table[0][k2 - 1][i][j].min(table[0][k2 - 1][i][j + half2]);
                }
            }
        }

        // Extend along rows for all k2
        for k1 in 1..log_rows {
            let half1 = 1 << (k1 - 1);
            for k2 in 0..log_cols {
                for i in 0..rows.saturating_sub((1 << k1) - 1) {
                    for j in 0..cols.saturating_sub((1 << k2).saturating_sub(1)) {
                        if j < cols {
                            table[k1][k2][i][j] =
                                table[k1 - 1][k2][i][j].min(table[k1 - 1][k2][i + half1][j]);
                        }
                    }
                }
            }
        }

        SparseTable2D { table, rows, cols, log_rows, log_cols }
    }

    /// Query minimum in rectangle [r1..r2][c1..c2] (inclusive, 0-indexed). O(1).
    pub fn query(&self, r1: usize, c1: usize, r2: usize, c2: usize) -> i64 {
        let kr = floor_log2(r2 - r1 + 1);
        let kc = floor_log2(c2 - c1 + 1);
        let r1b = r2 - (1 << kr) + 1;
        let c1b = c2 - (1 << kc) + 1;

        self.table[kr][kc][r1][c1]
            .min(self.table[kr][kc][r1][c1b])
            .min(self.table[kr][kc][r1b][c1])
            .min(self.table[kr][kc][r1b][c1b])
    }
}

fn main() {
    let grid = vec![
        vec![3, 1, 4, 1, 5],
        vec![9, 2, 6, 5, 3],
        vec![5, 8, 9, 7, 9],
        vec![3, 2, 3, 8, 4],
    ];
    println!("Grid:");
    for row in &grid {
        println!("  {:?}", row);
    }

    let st2d = SparseTable2D::new(&grid);

    println!("\n=== 2D Range Minimum Queries ===");
    // Full grid
    println!("Min [0..3][0..4] = {} (expected 1)", st2d.query(0, 0, 3, 4));
    // Single cell
    println!("Min [2][3] = {} (expected 7)", st2d.query(2, 3, 2, 3));
    // Sub-rectangle
    println!("Min [0..1][1..3] = {} (expected 1)", st2d.query(0, 1, 1, 3));
    println!("Min [1..3][2..4] = {} (expected 3)", st2d.query(1, 2, 3, 4));
}
```

---

## 16. Common Pitfalls & Debugging Tips

### 16.1 Off-by-One Errors

**Issue:** Confusing 0-indexed vs. 1-indexed arrays. Most competitive programming uses 1-indexed trees but 0-indexed arrays.

**Fix:** Be consistent. In the implementations above, trees are 1-indexed (node 0 is unused), arrays are 0-indexed. Document your convention clearly at the top.

### 16.2 LOG Value Too Small

**Issue:** Setting `LOG = 16` for n up to 10^6 — but `floor(log2(10^6)) = 19`. Accessing out-of-bounds memory.

**Fix:** Use `LOG = ceil(log2(MAXN)) + 1`, or dynamically compute the number of levels:
```
levels = bit_length(n)  // = floor(log2(n)) + 1
```

### 16.3 Incorrect LCA Step 2

**Issue:** Forgetting the edge case where one node is an ancestor of the other. If u == v after equalizing depths, return immediately without entering the second loop.

**Fix:** Always check `if u == v: return u` before the second lifting loop.

### 16.4 Euler Tour Size

**Issue:** Allocating only n elements for the Euler tour, which has length 2n-1.

**Fix:** Allocate `2 * n - 1` (or simply `2 * n`) elements.

### 16.5 Binary Lifting Level Fill Order

**Issue:** Filling the binary lifting table with the node loop as the outer loop and level loop as inner:
```
// WRONG:
for v in 1..n:
    for k in 1..LOG:
        anc[v][k] = anc[anc[v][k-1]][k-1]
```
This may read `anc[...][k-1]` before it's been filled for all nodes.

**Fix:** Always make the level loop outer:
```
// CORRECT:
for k in 1..LOG:
    for v in 1..n:
        anc[v][k] = anc[anc[v][k-1]][k-1]
```

### 16.6 Recursion Stack Overflow

**Issue:** Recursive DFS on trees with n = 10^5 to 10^6 nodes can overflow the default stack (usually 1-8 MB).

**Fix:** Use iterative DFS (as shown in the Rust Euler Tour implementation), or increase stack size (in Rust: spawn a thread with a larger stack).

### 16.7 Root Has No Parent

**Issue:** Accessing `anc[root][0]` during LCA when root has no parent — returns garbage or causes segfault.

**Fix:** Set `anc[root][k] = root` for all k (self-referential), or use a sentinel value (`-1`, `NO_PARENT`, `usize::MAX`) and check before accessing.

### 16.8 LCA Query Returns Wrong Answer

**Debugging checklist:**
1. Are depths correctly computed?
2. Is `first[]` the first occurrence (not last)?
3. Is the Euler tour depth array correctly filled (length 2n-1)?
4. Did you build the Sparse Table on the depth array (not the node array)?
5. Is the RMQ returning the node at the minimum depth position, not the minimum depth value?

---

## 17. Practice Problems & Applications

### 17.1 Classic Sparse Table Problems

- **SPOJ RMQSQ** — Static RMQ, the canonical Sparse Table benchmark
- **Codeforces 342E** — Range query on trees combining HLD and Sparse Table
- **SPOJ LCA** — Classic LCA using binary lifting
- **CF 1000G** — Two-colored trees, uses LCA + binary lifting

### 17.2 Applications in Systems

- **Database Query Optimization:** Range minimum/maximum on sorted columns
- **Network Routing:** LCA in hierarchical network topologies
- **Computational Biology:** Phylogenetic tree queries
- **Compiler Optimization:** Dominance tree analysis (LCA of dominators)
- **Text Indexing:** Suffix Array + LCP Array uses Sparse Table for LCP range minimum

### 17.3 Suffix Array + LCA Connection

The **Longest Common Extension (LCE)** problem — given a string, find the length of the longest common prefix of two suffixes — reduces to RMQ on the LCP array:

```
LCE(i, j) = RMQ(SA_rank[i], SA_rank[j])   on the LCP array
```

This is built with a Sparse Table for O(n log n) build and O(1) LCE queries, powering efficient string matching, pattern search, and suffix array applications.

### 17.4 Problem-Solving Template

When you see:
- "Range min/max/gcd, no updates" → **Sparse Table**
- "Path between two nodes in a tree" → **LCA + depth**
- "k-th ancestor" → **Binary Lifting**
- "All LCA queries given upfront" → **Tarjan's offline LCA**
- "LCA with very many queries (>10^6)" → **Euler Tour + Sparse Table**
- "Range query on tree path" → **HLD + Segment Tree**

---

## Quick Reference

```
Sparse Table RMQ Build:
  ST[0][i] = A[i]
  ST[k][i] = f(ST[k-1][i], ST[k-1][i + 2^(k-1)])

Sparse Table RMQ Query (idempotent):
  k = floor(log2(r-l+1))
  answer = f(ST[k][l], ST[k][r - 2^k + 1])

Binary Lifting Build:
  anc[v][0] = parent(v)
  anc[v][k] = anc[anc[v][k-1]][k-1]

k-th Ancestor:
  for each set bit j of k: v = anc[v][j]

LCA (Binary Lifting):
  1. Equalize depths by lifting deeper node
  2. Simultaneously lift both until anc[u][k] == anc[v][k] fails

Euler Tour LCA:
  tour length = 2n - 1
  LCA(u,v) = euler[RMQ(first[u], first[v])]  (on depth array)

Distance in Tree:
  dist(u, v) = depth[u] + depth[v] - 2 * depth[LCA(u, v)]
```

---

*End of Guide — Sparse Trees: Sparse Table · Binary Lifting · LCA · Euler Tour*

Here's your complete guide — **~1,000 lines** of in-depth content. Here's what's covered:

**Theory & Concepts (Sections 1–12)**
- Mathematical foundations: interval decomposition, power-of-two arithmetic, idempotence
- Sparse Table (core structure, build/query mechanics, memory layouts)
- RMQ — why O(1) matters vs. Segment Trees
- Binary Lifting — the doubling recurrence, fill-order subtlety
- LCA — full algorithm walkthrough with correctness proof
- Euler Tour + Sparse Table — the O(1) LCA pipeline
- Heavy-Light Decomposition and Centroid Decomposition overviews
- Offline (Tarjan) vs. Online query tradeoffs
- Advanced variants: 2D Sparse Tables, GCD/AND/OR queries, ±1 RMQ

**Implementations**

| Language | What's implemented |
|---|---|
| **C** | RMQ, RMaxQ, Range GCD, Binary Lifting + LCA, Euler Tour + ST LCA |
| **Go** | Generic Sparse Table (Go generics), Binary Lifting + LCA, Euler Tour + ST LCA, Tarjan Offline LCA |
| **Rust** | Generic Sparse Table, Binary Lifting + LCA, Iterative Euler Tour + ST LCA, Tarjan Offline LCA, 2D Sparse Table |

**Practical extras:** pitfall guide (8 common bugs explained), complexity table, problem-solving decision template, and a quick-reference cheat sheet at the end.