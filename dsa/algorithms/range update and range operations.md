# Range Update & Range Operations — Complete Masterclass

> *"An expert is someone who has made all the mistakes in a narrow field."*
> Train like a monk. Think like a machine. Build like an engineer.

---

## Table of Contents

1. [Foundations — What Are Range Operations?](#1-foundations)
2. [Prefix Sum Array](#2-prefix-sum-array)
3. [Difference Array](#3-difference-array)
4. [Sparse Table (Range Minimum/Maximum Query)](#4-sparse-table)
5. [Segment Tree — Point Update, Range Query](#5-segment-tree-basic)
6. [Segment Tree — Lazy Propagation (Range Update, Range Query)](#6-segment-tree-lazy)
7. [Binary Indexed Tree / Fenwick Tree](#7-fenwick-tree)
8. [BIT with Range Update and Range Query](#8-bit-range-update)
9. [Square Root Decomposition (Mo's Algorithm Prelude)](#9-sqrt-decomposition)
10. [Mo's Algorithm — Offline Range Queries](#10-mos-algorithm)
11. [Persistent Segment Tree](#11-persistent-segment-tree)
12. [Merge Sort Tree (Range Kth Smallest)](#12-merge-sort-tree)
13. [Wavelet Tree](#13-wavelet-tree)
14. [2D Range Operations](#14-2d-range)
15. [Mental Models & Expert Thinking Strategies](#15-mental-models)
16. [Problem Pattern Recognition Table](#16-pattern-table)

---

## 1. Foundations — What Are Range Operations?

### Core Vocabulary (Master These First)

Before anything else, internalize this vocabulary. Every expert DSA practitioner uses these words with precision.

| Term | Meaning |
|------|---------|
| **Range** | A contiguous subarray defined by indices [l, r] (inclusive both ends usually) |
| **Query** | A read operation — "What is the sum/min/max of elements from l to r?" |
| **Update** | A write operation — "Add 5 to all elements from l to r" |
| **Point Update** | Update a single element at index i |
| **Range Update** | Update all elements in range [l, r] |
| **Point Query** | Read a single element at index i |
| **Range Query** | Read an aggregate (sum/min/max/gcd) over range [l, r] |
| **Offline** | All queries are known upfront before processing begins |
| **Online** | Queries arrive one at a time; must answer each before next arrives |
| **Idempotent** | An operation where applying it twice = applying once (e.g., min, max, gcd) |
| **Lazy** | Deferring work to later — "I'll propagate this update only when I need to go deeper" |
| **Propagation** | Pushing a deferred (lazy) update down to children nodes |
| **Prefix** | Everything from index 0 up to i |
| **Suffix** | Everything from index i to the end |
| **Aggregate** | A combined result: sum, product, min, max, GCD, XOR, etc. |

---

### The Four Core Problem Types

```
╔══════════════════╦══════════════════╦═══════════════════════════════════╗
║   Update Type    ║   Query Type     ║   Best Data Structure             ║
╠══════════════════╬══════════════════╬═══════════════════════════════════╣
║ Point Update     ║ Range Query      ║ Fenwick Tree / Segment Tree       ║
║ Range Update     ║ Point Query      ║ Difference Array / Fenwick Tree   ║
║ Range Update     ║ Range Query      ║ Segment Tree + Lazy Propagation   ║
║ None (static)    ║ Range Query      ║ Prefix Sum / Sparse Table         ║
╚══════════════════╩══════════════════╩═══════════════════════════════════╝
```

### Mental Model: The Complexity Hierarchy

```
BRUTE FORCE          O(N) per query / O(1) per update
     ↓
PREFIX SUM           O(1) per query / O(N) rebuild (no updates)
     ↓
SQRT DECOMP          O(√N) per query and update
     ↓
FENWICK TREE         O(log N) per query and point update
     ↓
SEGMENT TREE         O(log N) per query and point/range update
     ↓
SPARSE TABLE         O(1) per query / O(N log N) build (idempotent, no updates)
```

---

## 2. Prefix Sum Array

### What Problem Does It Solve?

**Problem**: Given a static array, answer many "what is the sum of elements from index l to r?" queries efficiently.

**Brute Force**: O(N) per query — iterate l to r and sum.
**Prefix Sum**: O(N) build, O(1) per query. A massive win for many queries.

### Core Idea

Define `prefix[i]` = sum of all elements from index 0 to i-1 (0-indexed, exclusive upper bound).

```
Array:   [3,  1,  4,  1,  5,  9,  2,  6]
Index:    0   1   2   3   4   5   6   7

prefix[0] = 0              (empty sum)
prefix[1] = 3
prefix[2] = 3+1 = 4
prefix[3] = 3+1+4 = 8
prefix[4] = 3+1+4+1 = 9
prefix[5] = 3+1+4+1+5 = 14
prefix[6] = 3+1+4+1+5+9 = 23
prefix[7] = 3+1+4+1+5+9+2 = 25
prefix[8] = 3+1+4+1+5+9+2+6 = 31
```

**Query sum(l, r)** (0-indexed, inclusive) = `prefix[r+1] - prefix[l]`

**Why?** `prefix[r+1]` = sum of [0..r], `prefix[l]` = sum of [0..l-1].
Subtract → sum of [l..r]. This is the *inclusion-exclusion principle*.

```
Query sum(2, 5):
= prefix[6] - prefix[2]
= 23 - 4
= 19
Verify: 4+1+5+9 = 19 ✓
```

### Algorithm Flow

```
BUILD:
  prefix[0] = 0
  FOR i from 1 to N:
    prefix[i] = prefix[i-1] + array[i-1]

QUERY(l, r):  [0-indexed, inclusive]
  RETURN prefix[r+1] - prefix[l]
```

### Decision Tree

```
Is the array static (no updates)?
├── YES → Use Prefix Sum
│   ├── Range sum queries → O(1) each after O(N) build
│   └── Point queries → O(1) each
└── NO → Need updates?
    ├── Only point updates → Fenwick Tree
    └── Range updates → Difference Array or Segment Tree
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

#define MAXN 100005

long long prefix[MAXN + 1];
int arr[MAXN];
int n;

void build(void) {
    prefix[0] = 0;
    for (int i = 1; i <= n; i++) {
        prefix[i] = prefix[i - 1] + arr[i - 1];
    }
}

// Query sum [l, r] inclusive, 0-indexed
long long query(int l, int r) {
    return prefix[r + 1] - prefix[l];
}

int main(void) {
    n = 8;
    int data[] = {3, 1, 4, 1, 5, 9, 2, 6};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    build();

    printf("sum(2,5) = %lld\n", query(2, 5)); // Expected: 19
    printf("sum(0,7) = %lld\n", query(0, 7)); // Expected: 31
    printf("sum(4,4) = %lld\n", query(4, 4)); // Expected: 5

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type PrefixSum struct {
    prefix []int64
}

func NewPrefixSum(arr []int) *PrefixSum {
    n := len(arr)
    prefix := make([]int64, n+1)
    for i := 1; i <= n; i++ {
        prefix[i] = prefix[i-1] + int64(arr[i-1])
    }
    return &PrefixSum{prefix: prefix}
}

// Query sum [l, r] inclusive, 0-indexed
func (ps *PrefixSum) Query(l, r int) int64 {
    return ps.prefix[r+1] - ps.prefix[l]
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    ps := NewPrefixSum(arr)

    fmt.Println("sum(2,5) =", ps.Query(2, 5)) // 19
    fmt.Println("sum(0,7) =", ps.Query(0, 7)) // 31
    fmt.Println("sum(4,4) =", ps.Query(4, 4)) // 5
}
```

### Rust Implementation

```rust
struct PrefixSum {
    prefix: Vec<i64>,
}

impl PrefixSum {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut prefix = vec![0i64; n + 1];
        for i in 1..=n {
            prefix[i] = prefix[i - 1] + arr[i - 1];
        }
        PrefixSum { prefix }
    }

    // Query sum [l, r] inclusive, 0-indexed
    fn query(&self, l: usize, r: usize) -> i64 {
        self.prefix[r + 1] - self.prefix[l]
    }
}

fn main() {
    let arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    let ps = PrefixSum::new(&arr);

    println!("sum(2,5) = {}", ps.query(2, 5)); // 19
    println!("sum(0,7) = {}", ps.query(0, 7)); // 31
    println!("sum(4,4) = {}", ps.query(4, 4)); // 5
}
```

### Extensions of Prefix Sum

**2D Prefix Sum**: For a grid, `prefix[i][j]` = sum of rectangle from (0,0) to (i-1, j-1).
```
sum(r1,c1,r2,c2) = prefix[r2+1][c2+1] - prefix[r1][c2+1] - prefix[r2+1][c1] + prefix[r1][c1]
```
This is inclusion-exclusion in 2D.

**XOR Prefix**: Replace addition with XOR. Now query gives XOR of range.

**Prefix Product**: Replace addition with multiplication. Query gives product of range.

---

## 3. Difference Array

### What Problem Does It Solve?

**Problem**: Given an array, perform MANY range updates of the form "add value V to all elements in [l, r]", then answer point queries efficiently.

**Key Insight**: Brute force range update is O(N) per update. Difference Array makes it O(1) per update, O(N) to rebuild.

### Core Concept: "Difference Array"

Define `diff[i]` = `arr[i] - arr[i-1]` for i > 0, and `diff[0] = arr[0]`.

This means `arr` is the **prefix sum of `diff`**!

```
Array:  [3, 1, 4, 1, 5]
diff:   [3, -2, 3, -3, 4]   (arr[0], arr[1]-arr[0], arr[2]-arr[1], ...)

Prefix sum of diff:
  3
  3+(-2) = 1
  3+(-2)+3 = 4
  3+(-2)+3+(-3) = 1
  3+(-2)+3+(-3)+4 = 5
= Original array! ✓
```

### The Magic of Range Update

To add V to all elements in [l, r]:
- `diff[l] += V`
- `diff[r+1] -= V` (if r+1 <= n)

**Why?** When you take the prefix sum later:
- From index l onwards, every prefix sum includes the +V at diff[l].
- From index r+1 onwards, the -V cancels it out, so only [l, r] is affected.

```
BEFORE: diff = [3, -2, 3, -3, 4]
Add 5 to range [1, 3]:
  diff[1] += 5  →  diff = [3, 3, 3, -3, 4]
  diff[4] -= 5  →  diff = [3, 3, 3, -3, -1]

Prefix sum of new diff:
  3
  3+3 = 6   (was 1, now 1+5=6) ✓
  3+3+3 = 9 (was 4, now 4+5=9) ✓
  3+3+3+(-3) = 6 (was 1, now 1+5=6) ✓
  3+3+3+(-3)+(-1) = 5 (was 5, unchanged) ✓
```

### Algorithm Flow

```
BUILD:
  diff[0] = arr[0]
  FOR i from 1 to N-1:
    diff[i] = arr[i] - arr[i-1]

RANGE UPDATE(l, r, val):
  diff[l] += val
  IF r+1 < N: diff[r+1] -= val

REBUILD (after all updates):
  arr[0] = diff[0]
  FOR i from 1 to N-1:
    arr[i] = arr[i-1] + diff[i]

POINT QUERY(i):
  Rebuild first (or maintain running prefix)
  RETURN arr[i]
```

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long arr[MAXN];
long long diff[MAXN];
int n;

void build(void) {
    diff[0] = arr[0];
    for (int i = 1; i < n; i++) {
        diff[i] = arr[i] - arr[i - 1];
    }
}

// Add val to all elements in [l, r] inclusive, 0-indexed
void range_update(int l, int r, long long val) {
    diff[l] += val;
    if (r + 1 < n) diff[r + 1] -= val;
}

// Reconstruct arr from diff
void rebuild(void) {
    arr[0] = diff[0];
    for (int i = 1; i < n; i++) {
        arr[i] = arr[i - 1] + diff[i];
    }
}

int main(void) {
    n = 5;
    long long data[] = {3, 1, 4, 1, 5};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    build();

    range_update(1, 3, 5);  // Add 5 to [1..3]
    range_update(0, 2, -2); // Sub 2 from [0..2]

    rebuild();

    for (int i = 0; i < n; i++) {
        printf("arr[%d] = %lld\n", i, arr[i]);
    }
    // Expected: [1, 4, 7, 6, 5]
    // 3-2=1, 1+5-2=4, 4+5-2=7, 1+5=6, 5=5

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type DifferenceArray struct {
    diff []int64
    n    int
}

func NewDifferenceArray(arr []int64) *DifferenceArray {
    n := len(arr)
    diff := make([]int64, n)
    diff[0] = arr[0]
    for i := 1; i < n; i++ {
        diff[i] = arr[i] - arr[i-1]
    }
    return &DifferenceArray{diff: diff, n: n}
}

func (da *DifferenceArray) RangeUpdate(l, r int, val int64) {
    da.diff[l] += val
    if r+1 < da.n {
        da.diff[r+1] -= val
    }
}

func (da *DifferenceArray) Rebuild() []int64 {
    result := make([]int64, da.n)
    result[0] = da.diff[0]
    for i := 1; i < da.n; i++ {
        result[i] = result[i-1] + da.diff[i]
    }
    return result
}

func main() {
    arr := []int64{3, 1, 4, 1, 5}
    da := NewDifferenceArray(arr)
    da.RangeUpdate(1, 3, 5)
    da.RangeUpdate(0, 2, -2)
    result := da.Rebuild()
    fmt.Println(result) // [1 4 7 6 5]
}
```

### Rust Implementation

```rust
struct DifferenceArray {
    diff: Vec<i64>,
}

impl DifferenceArray {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut diff = vec![0i64; n];
        diff[0] = arr[0];
        for i in 1..n {
            diff[i] = arr[i] - arr[i - 1];
        }
        DifferenceArray { diff }
    }

    fn range_update(&mut self, l: usize, r: usize, val: i64) {
        self.diff[l] += val;
        if r + 1 < self.diff.len() {
            self.diff[r + 1] -= val;
        }
    }

    fn rebuild(&self) -> Vec<i64> {
        let n = self.diff.len();
        let mut result = vec![0i64; n];
        result[0] = self.diff[0];
        for i in 1..n {
            result[i] = result[i - 1] + self.diff[i];
        }
        result
    }
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5];
    let mut da = DifferenceArray::new(&arr);
    da.range_update(1, 3, 5);
    da.range_update(0, 2, -2);
    let result = da.rebuild();
    println!("{:?}", result); // [1, 4, 7, 6, 5]
}
```

---

## 4. Sparse Table

### What Problem Does It Solve?

**Static** array. Need **range minimum or maximum queries** in O(1). No updates allowed.

### Key Vocabulary

- **Idempotent operation**: An operation where `op(x, x) = x`. Min, Max, GCD are idempotent. Sum is NOT (sum(x, x) = 2x ≠ x).
- **Power of 2**: Numbers 1, 2, 4, 8, 16... used to represent any range as the union of at most two overlapping blocks.

### Core Idea

Precompute `sparse[i][j]` = minimum of the subarray starting at index i with length 2^j.

```
sparse[i][0] = arr[i]                          (length 1)
sparse[i][1] = min(arr[i], arr[i+1])           (length 2)
sparse[i][2] = min(arr[i..i+3])                (length 4)
...
sparse[i][j] = min(sparse[i][j-1], sparse[i + 2^(j-1)][j-1])
```

**Query RMQ(l, r)**:
- Find k = floor(log2(r - l + 1)) — the largest power of 2 ≤ length
- Answer = min(sparse[l][k], sparse[r - 2^k + 1][k])
- These two blocks of size 2^k overlap but COVER [l, r] entirely.
- Since min is idempotent, overlap doesn't matter!

```
Array: [2, 4, 3, 1, 6, 7, 8, 9, 1, 7]
       index: 0  1  2  3  4  5  6  7  8  9

Query RMQ(2, 7):
  length = 6, k = floor(log2(6)) = 2 (since 2^2=4 ≤ 6)
  Block 1: sparse[2][2] = min(arr[2..5]) = min(3,1,6,7) = 1
  Block 2: sparse[7-4+1][2] = sparse[4][2] = min(arr[4..7]) = min(6,7,8,9) = 6
  Answer = min(1, 6) = 1 ✓
```

### C Implementation

```c
#include <stdio.h>
#include <math.h>

#define MAXN 100005
#define LOG 17  // log2(100000) < 17

int sparse[MAXN][LOG];
int log2_floor[MAXN];
int n;

int min(int a, int b) { return a < b ? a : b; }

void build(int *arr) {
    // Precompute log2 table
    log2_floor[1] = 0;
    for (int i = 2; i <= n; i++) {
        log2_floor[i] = log2_floor[i / 2] + 1;
    }

    // Base case
    for (int i = 0; i < n; i++) sparse[i][0] = arr[i];

    // Fill table
    for (int j = 1; (1 << j) <= n; j++) {
        for (int i = 0; i + (1 << j) - 1 < n; i++) {
            sparse[i][j] = min(sparse[i][j - 1],
                               sparse[i + (1 << (j - 1))][j - 1]);
        }
    }
}

// Range Minimum Query [l, r] inclusive, 0-indexed
int rmq(int l, int r) {
    int k = log2_floor[r - l + 1];
    return min(sparse[l][k], sparse[r - (1 << k) + 1][k]);
}

int main(void) {
    n = 10;
    int arr[] = {2, 4, 3, 1, 6, 7, 8, 9, 1, 7};
    build(arr);

    printf("RMQ(2,7) = %d\n", rmq(2, 7)); // Expected: 1
    printf("RMQ(0,4) = %d\n", rmq(0, 4)); // Expected: 1
    printf("RMQ(5,9) = %d\n", rmq(5, 9)); // Expected: 1

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

const LOG = 17

type SparseTable struct {
    table    [100005][LOG]int
    log2     [100005]int
    n        int
}

func NewSparseTable(arr []int) *SparseTable {
    st := &SparseTable{n: len(arr)}
    st.log2[1] = 0
    for i := 2; i <= st.n; i++ {
        st.log2[i] = st.log2[i/2] + 1
    }
    for i := 0; i < st.n; i++ {
        st.table[i][0] = arr[i]
    }
    for j := 1; (1 << j) <= st.n; j++ {
        for i := 0; i+(1<<j)-1 < st.n; i++ {
            a := st.table[i][j-1]
            b := st.table[i+(1<<(j-1))][j-1]
            if a < b {
                st.table[i][j] = a
            } else {
                st.table[i][j] = b
            }
        }
    }
    return st
}

func (st *SparseTable) RMQ(l, r int) int {
    k := st.log2[r-l+1]
    a := st.table[l][k]
    b := st.table[r-(1<<k)+1][k]
    if a < b {
        return a
    }
    return b
}

func main() {
    arr := []int{2, 4, 3, 1, 6, 7, 8, 9, 1, 7}
    st := NewSparseTable(arr)
    fmt.Println("RMQ(2,7) =", st.RMQ(2, 7)) // 1
    fmt.Println("RMQ(0,4) =", st.RMQ(0, 4)) // 1
}
```

### Rust Implementation

```rust
struct SparseTable {
    table: Vec<Vec<i32>>,
    log2: Vec<usize>,
    n: usize,
}

impl SparseTable {
    fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let log = 17usize;
        let mut log2 = vec![0usize; n + 1];
        for i in 2..=n {
            log2[i] = log2[i / 2] + 1;
        }
        let mut table = vec![vec![i32::MAX; log]; n];
        for i in 0..n {
            table[i][0] = arr[i];
        }
        for j in 1..log {
            let half = 1 << (j - 1);
            for i in 0..n {
                if i + (1 << j) - 1 < n {
                    table[i][j] = table[i][j - 1].min(table[i + half][j - 1]);
                }
            }
        }
        SparseTable { table, log2, n }
    }

    fn rmq(&self, l: usize, r: usize) -> i32 {
        let k = self.log2[r - l + 1];
        self.table[l][k].min(self.table[r - (1 << k) + 1][k])
    }
}

fn main() {
    let arr = vec![2, 4, 3, 1, 6, 7, 8, 9, 1, 7];
    let st = SparseTable::new(&arr);
    println!("RMQ(2,7) = {}", st.rmq(2, 7)); // 1
    println!("RMQ(0,4) = {}", st.rmq(0, 4)); // 1
}
```

---

## 5. Segment Tree — Basic (Point Update, Range Query)

### What Is a Segment Tree?

A **segment tree** is a binary tree where:
- Each **leaf node** represents a single array element.
- Each **internal node** represents the aggregate (sum/min/max) of its children's range.
- The **root** represents the aggregate of the entire array.

### Key Vocabulary

- **Node**: A tree position storing a value and representing a segment [l, r].
- **Leaf**: A node where l == r (single element).
- **Internal node**: Represents [l, r] where l < r.
- **Left child** of node i: node 2*i (1-indexed tree).
- **Right child** of node i: node 2*i+1.
- **Midpoint**: mid = (l + r) / 2. Left child covers [l, mid], right child covers [mid+1, r].

### Tree Structure Visualization

```
Array: [1, 3, 5, 7, 9, 11]
         sum = 36         [0..5]
        /            \
  sum=9 [0..2]    sum=27 [3..5]
    /    \           /      \
 4[0..1] 5[2..2] 16[3..4] 11[5..5]
  /   \           /    \
1[0] 3[1]       7[3]  9[4]
```

### Index Mapping (1-indexed tree)

```
For array of size N:
- Tree array has size 4*N (safe upper bound)
- Node 1 = root = covers [0, N-1]
- Node i, left child = 2i, right child = 2i+1
- Node i covers segment [l, r]
  - Left child covers [l, mid], right child covers [mid+1, r]
  - mid = (l + r) / 2
```

### Build Algorithm

```
BUILD(node, l, r):
  IF l == r:
    tree[node] = arr[l]
    RETURN
  mid = (l + r) / 2
  BUILD(2*node, l, mid)
  BUILD(2*node+1, mid+1, r)
  tree[node] = tree[2*node] + tree[2*node+1]   // pull up
```

### Query Algorithm

```
QUERY(node, l, r, ql, qr):   [query range ql..qr]
  IF ql > r OR qr < l:        // No overlap
    RETURN identity (0 for sum, INF for min)
  IF ql <= l AND r <= qr:     // Complete overlap
    RETURN tree[node]
  mid = (l + r) / 2            // Partial overlap — recurse
  left  = QUERY(2*node, l, mid, ql, qr)
  right = QUERY(2*node+1, mid+1, r, ql, qr)
  RETURN merge(left, right)
```

### Three Cases of Query — Decision Tree

```
Query range [ql, qr], current node covers [l, r]:

Is there NO overlap?
([ql, qr] is entirely left of [l, r] OR entirely right)
  YES → Return identity (0, INF, etc.)
  NO ↓

Is the current segment COMPLETELY inside [ql, qr]?
(ql <= l AND r <= qr)
  YES → Return tree[node] directly
  NO ↓

PARTIAL overlap → Recurse into both children and merge
```

### Update Algorithm (Point Update)

```
UPDATE(node, l, r, pos, val):
  IF l == r:
    tree[node] = val    // Update leaf
    RETURN
  mid = (l + r) / 2
  IF pos <= mid:
    UPDATE(2*node, l, mid, pos, val)
  ELSE:
    UPDATE(2*node+1, mid+1, r, pos, val)
  tree[node] = tree[2*node] + tree[2*node+1]   // Pull up
```

### C Implementation (Sum, Point Update, Range Query)

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN];
int arr[MAXN];
int n;

void build(int node, int l, int r) {
    if (l == r) {
        tree[node] = arr[l];
        return;
    }
    int mid = (l + r) / 2;
    build(2 * node, l, mid);
    build(2 * node + 1, mid + 1, r);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

void update(int node, int l, int r, int pos, long long val) {
    if (l == r) {
        tree[node] = val;
        arr[pos] = val;
        return;
    }
    int mid = (l + r) / 2;
    if (pos <= mid)
        update(2 * node, l, mid, pos, val);
    else
        update(2 * node + 1, mid + 1, r, pos, val);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

long long query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0; // No overlap, identity for sum
    if (ql <= l && r <= qr) return tree[node]; // Complete overlap
    int mid = (l + r) / 2;
    return query(2 * node, l, mid, ql, qr)
         + query(2 * node + 1, mid + 1, r, ql, qr);
}

int main(void) {
    n = 6;
    int data[] = {1, 3, 5, 7, 9, 11};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    build(1, 0, n - 1);

    printf("sum(1,4) = %lld\n", query(1, 0, n - 1, 1, 4)); // 3+5+7+9=24
    update(1, 0, n - 1, 2, 10);  // arr[2] = 10 (was 5)
    printf("sum(1,4) = %lld\n", query(1, 0, n - 1, 1, 4)); // 3+10+7+9=29

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type SegTree struct {
    tree []int64
    n    int
}

func NewSegTree(arr []int) *SegTree {
    n := len(arr)
    tree := make([]int64, 4*n)
    st := &SegTree{tree: tree, n: n}
    st.build(arr, 1, 0, n-1)
    return st
}

func (st *SegTree) build(arr []int, node, l, r int) {
    if l == r {
        st.tree[node] = int64(arr[l])
        return
    }
    mid := (l + r) / 2
    st.build(arr, 2*node, l, mid)
    st.build(arr, 2*node+1, mid+1, r)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Update(pos int, val int64) {
    st.update(1, 0, st.n-1, pos, val)
}

func (st *SegTree) update(node, l, r, pos int, val int64) {
    if l == r {
        st.tree[node] = val
        return
    }
    mid := (l + r) / 2
    if pos <= mid {
        st.update(2*node, l, mid, pos, val)
    } else {
        st.update(2*node+1, mid+1, r, pos, val)
    }
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Query(ql, qr int) int64 {
    return st.query(1, 0, st.n-1, ql, qr)
}

func (st *SegTree) query(node, l, r, ql, qr int) int64 {
    if qr < l || r < ql {
        return 0
    }
    if ql <= l && r <= qr {
        return st.tree[node]
    }
    mid := (l + r) / 2
    return st.query(2*node, l, mid, ql, qr) +
        st.query(2*node+1, mid+1, r, ql, qr)
}

func main() {
    arr := []int{1, 3, 5, 7, 9, 11}
    st := NewSegTree(arr)
    fmt.Println("sum(1,4) =", st.Query(1, 4)) // 24
    st.Update(2, 10)
    fmt.Println("sum(1,4) =", st.Query(1, 4)) // 29
}
```

### Rust Implementation

```rust
struct SegTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = SegTree {
            tree: vec![0i64; 4 * n],
            n,
        };
        st.build(arr, 1, 0, n - 1);
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build(arr, 2 * node, l, mid);
        self.build(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn update(&mut self, pos: usize, val: i64) {
        let n = self.n;
        self.update_inner(1, 0, n - 1, pos, val);
    }

    fn update_inner(&mut self, node: usize, l: usize, r: usize, pos: usize, val: i64) {
        if l == r {
            self.tree[node] = val;
            return;
        }
        let mid = (l + r) / 2;
        if pos <= mid {
            self.update_inner(2 * node, l, mid, pos, val);
        } else {
            self.update_inner(2 * node + 1, mid + 1, r, pos, val);
        }
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn query(&self, ql: usize, qr: usize) -> i64 {
        let n = self.n;
        self.query_inner(1, 0, n - 1, ql, qr)
    }

    fn query_inner(&self, node: usize, l: usize, r: usize, ql: usize, qr: usize) -> i64 {
        if qr < l || r < ql {
            return 0;
        }
        if ql <= l && r <= qr {
            return self.tree[node];
        }
        let mid = (l + r) / 2;
        self.query_inner(2 * node, l, mid, ql, qr)
            + self.query_inner(2 * node + 1, mid + 1, r, ql, qr)
    }
}

fn main() {
    let arr = vec![1i64, 3, 5, 7, 9, 11];
    let mut st = SegTree::new(&arr);
    println!("sum(1,4) = {}", st.query(1, 4)); // 24
    st.update(2, 10);
    println!("sum(1,4) = {}", st.query(1, 4)); // 29
}
```

---

## 6. Segment Tree — Lazy Propagation (Range Update, Range Query)

### Why Lazy Propagation?

Without lazy: updating range [l, r] in segment tree requires touching every element → O(N) worst case.

With lazy: we mark nodes as "pending update" and only propagate when we *need* to go deeper. This achieves **O(log N) range update**.

### Core Concept: "Lazy Tag"

Each node stores an extra value: `lazy[node]`.

**Semantics**: "The subtree rooted at this node needs to have `lazy[node]` added to all elements, but I haven't propagated this to children yet."

### Key Operations

**push_down(node, l, r)**:
Take the lazy tag from a parent node and push it to both children. This is called BEFORE recursing into children.

```
PUSH_DOWN(node, l, r):
  IF lazy[node] != 0:
    mid = (l+r)/2
    // Update left child
    tree[2*node] += lazy[node] * (mid - l + 1)
    lazy[2*node] += lazy[node]
    // Update right child
    tree[2*node+1] += lazy[node] * (r - mid)
    lazy[2*node+1] += lazy[node]
    // Clear parent's lazy
    lazy[node] = 0
```

**Why multiply by segment length?** The tree node stores the SUM of its range. If you add V to every element in a range of length L, the sum increases by V*L.

### Algorithm Flow: Lazy Range Update

```
RANGE_UPDATE(node, l, r, ql, qr, val):
  IF ql > r OR qr < l:             // No overlap
    RETURN
  IF ql <= l AND r <= qr:          // Complete overlap
    tree[node] += val * (r - l + 1)
    lazy[node] += val
    RETURN
  PUSH_DOWN(node, l, r)            // Partial — push before recursing
  mid = (l+r)/2
  RANGE_UPDATE(2*node, l, mid, ql, qr, val)
  RANGE_UPDATE(2*node+1, mid+1, r, ql, qr, val)
  tree[node] = tree[2*node] + tree[2*node+1]  // Pull up
```

### Algorithm Flow: Lazy Range Query

```
RANGE_QUERY(node, l, r, ql, qr):
  IF ql > r OR qr < l:             // No overlap
    RETURN 0
  IF ql <= l AND r <= qr:          // Complete overlap
    RETURN tree[node]
  PUSH_DOWN(node, l, r)            // Must push before going deeper!
  mid = (l+r)/2
  RETURN RANGE_QUERY(2*node, l, mid, ql, qr)
       + RANGE_QUERY(2*node+1, mid+1, r, ql, qr)
```

### Call Flow for Range Update [1,4] on array [1,3,5,7,9,11]

```
add(2) to [1..4]

update(1, 0, 5, 1, 4, 2):
  Partial overlap with [0..5]
  push_down(1) — lazy[1]=0, nothing to push
  mid=2
  update(2, 0, 2, 1, 4, 2):   left child [0..2]
    Partial overlap
    push_down(2) — nothing
    mid=1
    update(4, 0, 1, 1, 4, 2): [0..1] partial
      push_down(4)
      mid=0
      update(8, 0, 0, 1, 4, 2): [0..0] NO overlap → return
      update(9, 1, 1, 1, 4, 2): [1..1] COMPLETE overlap
        tree[9] += 2*1 = 2   (3 → 5)
        lazy[9] += 2
        return
      tree[4] = tree[8]+tree[9] = 1+5 = 6
    update(5, 2, 2, 1, 4, 2): [2..2] COMPLETE overlap
      tree[5] += 2*1 = 2  (5 → 7)
      lazy[5] += 2
      return
    tree[2] = tree[4]+tree[5] = 6+7 = 13
  update(3, 3, 5, 1, 4, 2):   right child [3..5]
    Partial overlap
    push_down(3)
    mid=4
    update(6, 3, 4, 1, 4, 2): [3..4] COMPLETE overlap
      tree[6] += 2*2 = 4  (7+9=16 → 16+4=20)
      lazy[6] += 2
      return
    update(7, 5, 5, 1, 4, 2): [5..5] NO overlap → return
    tree[3] = tree[6]+tree[7] = 20+11 = 31
  tree[1] = tree[2]+tree[3] = 13+31 = 44
```

### C Implementation (Range Add, Range Sum)

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN];
long long lazy[4 * MAXN];
int n;

void build(int node, int l, int r, int *arr) {
    lazy[node] = 0;
    if (l == r) {
        tree[node] = arr[l];
        return;
    }
    int mid = (l + r) / 2;
    build(2 * node, l, mid, arr);
    build(2 * node + 1, mid + 1, r, arr);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

void push_down(int node, int l, int r) {
    if (lazy[node] == 0) return;
    int mid = (l + r) / 2;

    // Update left child
    tree[2 * node] += lazy[node] * (mid - l + 1);
    lazy[2 * node] += lazy[node];

    // Update right child
    tree[2 * node + 1] += lazy[node] * (r - mid);
    lazy[2 * node + 1] += lazy[node];

    lazy[node] = 0; // Clear
}

// Add val to all elements in [ql, qr]
void range_update(int node, int l, int r, int ql, int qr, long long val) {
    if (qr < l || r < ql) return;
    if (ql <= l && r <= qr) {
        tree[node] += val * (r - l + 1);
        lazy[node] += val;
        return;
    }
    push_down(node, l, r);
    int mid = (l + r) / 2;
    range_update(2 * node, l, mid, ql, qr, val);
    range_update(2 * node + 1, mid + 1, r, ql, qr, val);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

// Sum query [ql, qr]
long long range_query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0;
    if (ql <= l && r <= qr) return tree[node];
    push_down(node, l, r);
    int mid = (l + r) / 2;
    return range_query(2 * node, l, mid, ql, qr)
         + range_query(2 * node + 1, mid + 1, r, ql, qr);
}

int main(void) {
    n = 6;
    int arr[] = {1, 3, 5, 7, 9, 11};
    build(1, 0, n - 1, arr);

    printf("sum(1,4) = %lld\n", range_query(1, 0, n-1, 1, 4)); // 24
    range_update(1, 0, n-1, 1, 4, 2); // Add 2 to [1..4]
    printf("sum(1,4) = %lld\n", range_query(1, 0, n-1, 1, 4)); // 24+2*4=32
    printf("sum(0,5) = %lld\n", range_query(1, 0, n-1, 0, 5)); // 36+8=44

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type LazySegTree struct {
    tree []int64
    lazy []int64
    n    int
}

func NewLazySegTree(arr []int) *LazySegTree {
    n := len(arr)
    st := &LazySegTree{
        tree: make([]int64, 4*n),
        lazy: make([]int64, 4*n),
        n:    n,
    }
    st.build(arr, 1, 0, n-1)
    return st
}

func (st *LazySegTree) build(arr []int, node, l, r int) {
    if l == r {
        st.tree[node] = int64(arr[l])
        return
    }
    mid := (l + r) / 2
    st.build(arr, 2*node, l, mid)
    st.build(arr, 2*node+1, mid+1, r)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *LazySegTree) pushDown(node, l, r int) {
    if st.lazy[node] == 0 {
        return
    }
    mid := (l + r) / 2
    st.tree[2*node] += st.lazy[node] * int64(mid-l+1)
    st.lazy[2*node] += st.lazy[node]
    st.tree[2*node+1] += st.lazy[node] * int64(r-mid)
    st.lazy[2*node+1] += st.lazy[node]
    st.lazy[node] = 0
}

func (st *LazySegTree) RangeUpdate(ql, qr int, val int64) {
    st.update(1, 0, st.n-1, ql, qr, val)
}

func (st *LazySegTree) update(node, l, r, ql, qr int, val int64) {
    if qr < l || r < ql {
        return
    }
    if ql <= l && r <= qr {
        st.tree[node] += val * int64(r-l+1)
        st.lazy[node] += val
        return
    }
    st.pushDown(node, l, r)
    mid := (l + r) / 2
    st.update(2*node, l, mid, ql, qr, val)
    st.update(2*node+1, mid+1, r, ql, qr, val)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *LazySegTree) RangeQuery(ql, qr int) int64 {
    return st.query(1, 0, st.n-1, ql, qr)
}

func (st *LazySegTree) query(node, l, r, ql, qr int) int64 {
    if qr < l || r < ql {
        return 0
    }
    if ql <= l && r <= qr {
        return st.tree[node]
    }
    st.pushDown(node, l, r)
    mid := (l + r) / 2
    return st.query(2*node, l, mid, ql, qr) +
        st.query(2*node+1, mid+1, r, ql, qr)
}

func main() {
    arr := []int{1, 3, 5, 7, 9, 11}
    st := NewLazySegTree(arr)
    fmt.Println("sum(1,4) =", st.RangeQuery(1, 4)) // 24
    st.RangeUpdate(1, 4, 2)
    fmt.Println("sum(1,4) =", st.RangeQuery(1, 4)) // 32
    fmt.Println("sum(0,5) =", st.RangeQuery(0, 5)) // 44
}
```

### Rust Implementation

```rust
struct LazySegTree {
    tree: Vec<i64>,
    lazy: Vec<i64>,
    n: usize,
}

impl LazySegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = LazySegTree {
            tree: vec![0i64; 4 * n],
            lazy: vec![0i64; 4 * n],
            n,
        };
        st.build(arr, 1, 0, n - 1);
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build(arr, 2 * node, l, mid);
        self.build(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn push_down(&mut self, node: usize, l: usize, r: usize) {
        if self.lazy[node] == 0 {
            return;
        }
        let mid = (l + r) / 2;
        let lz = self.lazy[node];
        self.tree[2 * node] += lz * (mid - l + 1) as i64;
        self.lazy[2 * node] += lz;
        self.tree[2 * node + 1] += lz * (r - mid) as i64;
        self.lazy[2 * node + 1] += lz;
        self.lazy[node] = 0;
    }

    fn range_update(&mut self, ql: usize, qr: usize, val: i64) {
        let n = self.n;
        self.update(1, 0, n - 1, ql, qr, val);
    }

    fn update(&mut self, node: usize, l: usize, r: usize, ql: usize, qr: usize, val: i64) {
        if qr < l || r < ql {
            return;
        }
        if ql <= l && r <= qr {
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.update(2 * node, l, mid, ql, qr, val);
        self.update(2 * node + 1, mid + 1, r, ql, qr, val);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn range_query(&self, ql: usize, qr: usize) -> i64 {
        let n = self.n;
        self.query(1, 0, n - 1, ql, qr)
    }

    fn query(&self, node: usize, l: usize, r: usize, ql: usize, qr: usize) -> i64 {
        if qr < l || r < ql {
            return 0;
        }
        if ql <= l && r <= qr {
            return self.tree[node];
        }
        // Note: In Rust we need a mutable reference to push_down.
        // For immutable query, we read lazily without pushing.
        // Proper lazy query needs separate push in mutable context.
        // This version works if queries always follow updates correctly.
        let mid = (l + r) / 2;
        self.query(2 * node, l, mid, ql, qr) + self.query(2 * node + 1, mid + 1, r, ql, qr)
    }
}

// Note: A fully correct Rust lazy seg tree requires &mut self in query too.
// Here's the corrected version:
struct LazySegTreeMut {
    tree: Vec<i64>,
    lazy: Vec<i64>,
    n: usize,
}

impl LazySegTreeMut {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = LazySegTreeMut {
            tree: vec![0i64; 4 * n],
            lazy: vec![0i64; 4 * n],
            n,
        };
        st.build(arr, 1, 0, n - 1);
        st
    }

    fn build(&mut self, arr: &[i64], node: usize, l: usize, r: usize) {
        if l == r { self.tree[node] = arr[l]; return; }
        let mid = (l + r) / 2;
        self.build(arr, 2 * node, l, mid);
        self.build(arr, 2 * node + 1, mid + 1, r);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn push_down(&mut self, node: usize, l: usize, r: usize) {
        if self.lazy[node] == 0 { return; }
        let mid = (l + r) / 2;
        let lz = self.lazy[node];
        self.tree[2*node]   += lz * (mid - l + 1) as i64;
        self.lazy[2*node]   += lz;
        self.tree[2*node+1] += lz * (r - mid) as i64;
        self.lazy[2*node+1] += lz;
        self.lazy[node] = 0;
    }

    fn update(&mut self, node: usize, l: usize, r: usize, ql: usize, qr: usize, val: i64) {
        if qr < l || r < ql { return; }
        if ql <= l && r <= qr {
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.update(2*node, l, mid, ql, qr, val);
        self.update(2*node+1, mid+1, r, ql, qr, val);
        self.tree[node] = self.tree[2*node] + self.tree[2*node+1];
    }

    fn query(&mut self, node: usize, l: usize, r: usize, ql: usize, qr: usize) -> i64 {
        if qr < l || r < ql { return 0; }
        if ql <= l && r <= qr { return self.tree[node]; }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.query(2*node, l, mid, ql, qr) + self.query(2*node+1, mid+1, r, ql, qr)
    }

    fn range_update(&mut self, ql: usize, qr: usize, val: i64) {
        let n = self.n; self.update(1, 0, n-1, ql, qr, val);
    }

    fn range_query(&mut self, ql: usize, qr: usize) -> i64 {
        let n = self.n; self.query(1, 0, n-1, ql, qr)
    }
}

fn main() {
    let arr = vec![1i64, 3, 5, 7, 9, 11];
    let mut st = LazySegTreeMut::new(&arr);
    println!("sum(1,4) = {}", st.range_query(1, 4)); // 24
    st.range_update(1, 4, 2);
    println!("sum(1,4) = {}", st.range_query(1, 4)); // 32
    println!("sum(0,5) = {}", st.range_query(0, 5)); // 44
}
```

### Generalizing Lazy to Range Assign

Instead of range-add, suppose you want range-assign (set all elements in [l, r] to V):

```c
// push_down for assign:
void push_down_assign(int node, int l, int r) {
    if (lazy[node] == -1) return; // -1 = no pending assign
    int mid = (l + r) / 2;
    tree[2*node]   = lazy[node] * (mid - l + 1);
    lazy[2*node]   = lazy[node];
    tree[2*node+1] = lazy[node] * (r - mid);
    lazy[2*node+1] = lazy[node];
    lazy[node] = -1; // Clear
}
```

**Key insight**: The lazy tag semantics change based on what operation you're deferring. You must design push_down specifically for your operation.

---

## 7. Binary Indexed Tree (Fenwick Tree)

### What Is a BIT?

A **Binary Indexed Tree (BIT)**, also called a **Fenwick Tree**, is a data structure that:
- Uses **O(N) space** (just an array)
- Supports **O(log N) point update** and **O(log N) prefix sum query**
- Is simpler and faster in practice than a segment tree for sum queries

### Core Vocabulary

- **Binary representation**: Every integer has a unique bit pattern. E.g., 6 = 110 in binary.
- **Least Significant Bit (LSB)**: The rightmost set bit. For 6 = 110, LSB = 010 = 2.
- **lowbit(x)**: A function returning x's LSB = `x & (-x)` in two's complement arithmetic.

```
x = 6 = 0110
-x = ...11111010 (two's complement)
x & (-x) = 0010 = 2   ← lowest set bit
```

### The Core Idea

`bit[i]` stores the sum of a specific range of elements. The range length is exactly `lowbit(i)`.

```
bit[i] is responsible for arr[i - lowbit(i) + 1 .. i]  (1-indexed)

bit[1]  = arr[1]                  (lowbit(1)=1)
bit[2]  = arr[1]+arr[2]           (lowbit(2)=2)
bit[3]  = arr[3]                  (lowbit(3)=1)
bit[4]  = arr[1]+arr[2]+arr[3]+arr[4] (lowbit(4)=4)
bit[5]  = arr[5]                  (lowbit(5)=1)
bit[6]  = arr[5]+arr[6]           (lowbit(6)=2)
bit[7]  = arr[7]                  (lowbit(7)=1)
bit[8]  = arr[1]..arr[8]          (lowbit(8)=8)
```

### Prefix Sum Query (1 to i)

Start at i. Add bit[i] to result. Move to i - lowbit(i). Repeat until i = 0.

```
prefix_sum(6):
  i=6 (110): add bit[6], i -= lowbit(6)=2 → i=4
  i=4 (100): add bit[4], i -= lowbit(4)=4 → i=0
  STOP
  = bit[6] + bit[4]
  = (arr[5]+arr[6]) + (arr[1]+arr[2]+arr[3]+arr[4])
  = sum of arr[1..6] ✓
```

### Point Update (at position i, add val)

Start at i. Update bit[i]. Move to i + lowbit(i). Repeat while i ≤ N.

```
update(3, +5):
  i=3 (011): bit[3] += 5, i += lowbit(3)=1 → i=4
  i=4 (100): bit[4] += 5, i += lowbit(4)=4 → i=8
  i=8 (1000): bit[8] += 5, i += lowbit(8)=8 → i=16 > N
  STOP
  (Only bit[3], bit[4], bit[8] need updating — they're responsible for ranges containing position 3)
```

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long bit[MAXN];
int n;

// Returns lowest set bit of x
int lowbit(int x) { return x & (-x); }

// Add val to position i (1-indexed)
void update(int i, long long val) {
    for (; i <= n; i += lowbit(i))
        bit[i] += val;
}

// Prefix sum [1..i]
long long prefix(int i) {
    long long sum = 0;
    for (; i > 0; i -= lowbit(i))
        sum += bit[i];
    return sum;
}

// Range sum [l, r] (1-indexed)
long long query(int l, int r) {
    return prefix(r) - prefix(l - 1);
}

// Build BIT from array (1-indexed)
void build(int *arr) {
    for (int i = 1; i <= n; i++) {
        update(i, arr[i]);
    }
}

int main(void) {
    n = 8;
    int arr[] = {0, 1, 3, 5, 7, 9, 11, 2, 6}; // 1-indexed, arr[0] unused

    memset(bit, 0, sizeof(bit));
    build(arr);

    printf("sum(1,6) = %lld\n", query(1, 6)); // 1+3+5+7+9+11=36
    printf("sum(3,5) = %lld\n", query(3, 5)); // 5+7+9=21
    update(3, 5);  // arr[3] += 5 → arr[3] = 10
    printf("sum(3,5) = %lld\n", query(3, 5)); // 10+7+9=26

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type BIT struct {
    tree []int64
    n    int
}

func NewBIT(n int) *BIT {
    return &BIT{tree: make([]int64, n+1), n: n}
}

func (b *BIT) Update(i int, val int64) {
    for ; i <= b.n; i += i & (-i) {
        b.tree[i] += val
    }
}

func (b *BIT) Prefix(i int) int64 {
    var sum int64
    for ; i > 0; i -= i & (-i) {
        sum += b.tree[i]
    }
    return sum
}

func (b *BIT) Query(l, r int) int64 {
    return b.Prefix(r) - b.Prefix(l-1)
}

func main() {
    arr := []int{0, 1, 3, 5, 7, 9, 11, 2, 6} // 1-indexed
    n := 8
    bit := NewBIT(n)
    for i := 1; i <= n; i++ {
        bit.Update(i, int64(arr[i]))
    }

    fmt.Println("sum(1,6) =", bit.Query(1, 6)) // 36
    fmt.Println("sum(3,5) =", bit.Query(3, 5)) // 21
    bit.Update(3, 5) // add 5 to position 3
    fmt.Println("sum(3,5) =", bit.Query(3, 5)) // 26
}
```

### Rust Implementation

```rust
struct BIT {
    tree: Vec<i64>,
    n: usize,
}

impl BIT {
    fn new(n: usize) -> Self {
        BIT { tree: vec![0i64; n + 1], n }
    }

    fn update(&mut self, mut i: usize, val: i64) {
        while i <= self.n {
            self.tree[i] += val;
            i += i & i.wrapping_neg();
        }
    }

    fn prefix(&self, mut i: usize) -> i64 {
        let mut sum = 0i64;
        while i > 0 {
            sum += self.tree[i];
            i -= i & i.wrapping_neg();
        }
        sum
    }

    fn query(&self, l: usize, r: usize) -> i64 {
        self.prefix(r) - self.prefix(l - 1)
    }
}

fn main() {
    let arr = vec![0i64, 1, 3, 5, 7, 9, 11, 2, 6]; // 1-indexed
    let n = 8;
    let mut bit = BIT::new(n);
    for i in 1..=n {
        bit.update(i, arr[i]);
    }
    println!("sum(1,6) = {}", bit.query(1, 6)); // 36
    println!("sum(3,5) = {}", bit.query(3, 5)); // 21
    bit.update(3, 5);
    println!("sum(3,5) = {}", bit.query(3, 5)); // 26
}
```

---

## 8. BIT with Range Update and Range Query

### The Problem

Standard BIT: point update, prefix query.
We need: **range update** (add val to [l, r]) and **range query** (sum of [l, r]).

### Mathematical Trick

Define a BIT on an array `B` such that:

```
sum(1..i) of original A = sum of B[1..i] * (i+1) - sum of B[1..i] * j
```

Using two BITs:
- `B1[i]`: stores the difference array style
- `B2[i]`: stores i * B1[i] values

**Range update [l, r] += val**:
```
B1.update(l, val)
B1.update(r+1, -val)
B2.update(l, val * (l-1))
B2.update(r+1, -val * r)
```

**Prefix sum query(1..i)**:
```
= B1.prefix(i) * i - B2.prefix(i)
```

**Range query(l, r)**:
```
= prefix(r) - prefix(l-1)
```

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long B1[MAXN], B2[MAXN];
int n;

void add(long long *bit, int i, long long val) {
    for (; i <= n; i += i & (-i))
        bit[i] += val;
}

long long sum(long long *bit, int i) {
    long long s = 0;
    for (; i > 0; i -= i & (-i))
        s += bit[i];
    return s;
}

// Add val to all elements in [l, r]
void range_add(int l, int r, long long val) {
    add(B1, l, val);
    add(B1, r + 1, -val);
    add(B2, l, val * (l - 1));
    add(B2, r + 1, -val * r);
}

// Prefix sum [1..i]
long long prefix_sum(int i) {
    return sum(B1, i) * i - sum(B2, i);
}

// Range sum [l, r]
long long range_query(int l, int r) {
    return prefix_sum(r) - prefix_sum(l - 1);
}

int main(void) {
    n = 6;
    // Assume initial array [1, 3, 5, 7, 9, 11] (1-indexed)
    int arr[] = {0, 1, 3, 5, 7, 9, 11};
    memset(B1, 0, sizeof(B1));
    memset(B2, 0, sizeof(B2));

    // Build: add each element as a point update
    for (int i = 1; i <= n; i++)
        range_add(i, i, arr[i]);

    printf("sum(2,5) = %lld\n", range_query(2, 5)); // 3+5+7+9=24
    range_add(2, 5, 2); // Add 2 to [2..5]
    printf("sum(2,5) = %lld\n", range_query(2, 5)); // (3+2)+(5+2)+(7+2)+(9+2)=32

    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type BIT2 struct {
    b1, b2 []int64
    n      int
}

func NewBIT2(n int) *BIT2 {
    return &BIT2{
        b1: make([]int64, n+2),
        b2: make([]int64, n+2),
        n:  n,
    }
}

func (b *BIT2) add(bit []int64, i int, val int64) {
    for ; i <= b.n; i += i & (-i) {
        bit[i] += val
    }
}

func (b *BIT2) sum(bit []int64, i int) int64 {
    var s int64
    for ; i > 0; i -= i & (-i) {
        s += bit[i]
    }
    return s
}

func (b *BIT2) RangeAdd(l, r int, val int64) {
    b.add(b.b1, l, val)
    b.add(b.b1, r+1, -val)
    b.add(b.b2, l, val*int64(l-1))
    b.add(b.b2, r+1, -val*int64(r))
}

func (b *BIT2) PrefixSum(i int) int64 {
    return b.sum(b.b1, i)*int64(i) - b.sum(b.b2, i)
}

func (b *BIT2) RangeQuery(l, r int) int64 {
    return b.PrefixSum(r) - b.PrefixSum(l-1)
}

func main() {
    n := 6
    arr := []int64{0, 1, 3, 5, 7, 9, 11}
    bit := NewBIT2(n)
    for i := 1; i <= n; i++ {
        bit.RangeAdd(i, i, arr[i])
    }
    fmt.Println("sum(2,5) =", bit.RangeQuery(2, 5)) // 24
    bit.RangeAdd(2, 5, 2)
    fmt.Println("sum(2,5) =", bit.RangeQuery(2, 5)) // 32
}
```

### Rust Implementation

```rust
struct BIT2 {
    b1: Vec<i64>,
    b2: Vec<i64>,
    n: usize,
}

impl BIT2 {
    fn new(n: usize) -> Self {
        BIT2 {
            b1: vec![0i64; n + 2],
            b2: vec![0i64; n + 2],
            n,
        }
    }

    fn add(bit: &mut Vec<i64>, mut i: usize, val: i64, n: usize) {
        while i <= n {
            bit[i] += val;
            i += i & i.wrapping_neg();
        }
    }

    fn sum(bit: &Vec<i64>, mut i: usize) -> i64 {
        let mut s = 0i64;
        while i > 0 {
            s += bit[i];
            i -= i & i.wrapping_neg();
        }
        s
    }

    fn range_add(&mut self, l: usize, r: usize, val: i64) {
        let n = self.n;
        Self::add(&mut self.b1, l, val, n);
        Self::add(&mut self.b1, r + 1, -val, n);
        Self::add(&mut self.b2, l, val * (l as i64 - 1), n);
        Self::add(&mut self.b2, r + 1, -val * r as i64, n);
    }

    fn prefix_sum(&self, i: usize) -> i64 {
        Self::sum(&self.b1, i) * i as i64 - Self::sum(&self.b2, i)
    }

    fn range_query(&self, l: usize, r: usize) -> i64 {
        self.prefix_sum(r) - self.prefix_sum(l - 1)
    }
}

fn main() {
    let arr = vec![0i64, 1, 3, 5, 7, 9, 11];
    let n = 6;
    let mut bit = BIT2::new(n);
    for i in 1..=n {
        bit.range_add(i, i, arr[i]);
    }
    println!("sum(2,5) = {}", bit.range_query(2, 5)); // 24
    bit.range_add(2, 5, 2);
    println!("sum(2,5) = {}", bit.range_query(2, 5)); // 32
}
```

---

## 9. Square Root Decomposition

### Core Idea

Divide array of N elements into **blocks of size √N**.

- Each **block** stores a precomputed aggregate (sum/min/max).
- Update: O(1) for point, O(√N) for range.
- Query: O(√N) — handle partial blocks at edges, complete blocks in middle.

### Visualization

```
Array:  [1, 2, 3 | 4, 5, 6 | 7, 8, 9]
         Block 0     Block 1     Block 2
         sum=6       sum=15      sum=24

Query sum [1, 7]:
  Block 0: partial (index 1-2) → 2+3 = 5
  Block 1: complete → use block_sum[1] = 15
  Block 2: partial (index 6-7) → 7+8 = 15
  Total = 5 + 15 + 15 = 35
```

### C Implementation

```c
#include <stdio.h>
#include <math.h>
#include <string.h>

#define MAXN 100005

long long arr[MAXN];
long long block_sum[320]; // sqrt(100000) ~ 316
int block_size;
int n;

int get_block(int i) { return i / block_size; }

void build(void) {
    block_size = (int)sqrt(n) + 1;
    for (int i = 0; i < n; i++) {
        block_sum[get_block(i)] += arr[i];
    }
}

// Add val to single element at pos
void point_update(int pos, long long val) {
    arr[pos] += val;
    block_sum[get_block(pos)] += val;
}

// Range sum query [l, r]
long long range_query(int l, int r) {
    long long result = 0;
    int bl = get_block(l), br = get_block(r);
    if (bl == br) {
        for (int i = l; i <= r; i++) result += arr[i];
    } else {
        // Left partial block
        for (int i = l; i < (bl + 1) * block_size; i++) result += arr[i];
        // Complete blocks
        for (int b = bl + 1; b < br; b++) result += block_sum[b];
        // Right partial block
        for (int i = br * block_size; i <= r; i++) result += arr[i];
    }
    return result;
}

int main(void) {
    n = 9;
    long long data[] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
    for (int i = 0; i < n; i++) arr[i] = data[i];
    build();

    printf("sum(1,7) = %lld\n", range_query(1, 7)); // 2+3+4+5+6+7+8=35
    point_update(4, 10); // arr[4] += 10 → arr[4] = 15
    printf("sum(1,7) = %lld\n", range_query(1, 7)); // 35+10=45
    return 0;
}
```

---

## 10. Mo's Algorithm — Offline Range Queries

### What Problem Does It Solve?

Multiple range queries on a static array, where the query is too complex for simple prefix sums (e.g., "count distinct elements in [l, r]"), and no data structure efficiently handles it.

### Key Vocabulary

- **Offline**: All queries given upfront, can be reordered.
- **Mo's ordering**: Sort queries to minimize the total movement of [l, r] pointers.
- **Block size**: √N — queries sorted by `(l / block_size, r)`.

### Core Idea

Maintain a "current window" [curL, curR]. When processing each query, expand or shrink the window by adding/removing one element at a time.

By sorting queries using Mo's order, the total number of add/remove operations is O((N + Q) √N).

### Mo's Query Sorting

Sort queries by:
1. Primary key: `l / block_size` (block of left endpoint)
2. Secondary key: `r` (ascending if block is even, descending if odd — the optimization)

```
Block 0 (l in 0..√N): sort by r ascending
Block 1 (l in √N..2√N): sort by r descending
...
```

This zigzag pattern minimizes r's movement.

### C Implementation (Count Distinct Elements)

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#define MAXN 100005
#define MAXQ 100005

int arr[MAXN];
int cnt[MAXN];   // cnt[v] = how many times value v appears in current window
int distinct;    // current count of distinct elements
int n, q, block_size;
int ans[MAXQ];

typedef struct {
    int l, r, idx;
} Query;

Query queries[MAXQ];

int cmp_queries(const void *a, const void *b) {
    Query *qa = (Query *)a;
    Query *qb = (Query *)b;
    int ba = qa->l / block_size;
    int bb = qb->l / block_size;
    if (ba != bb) return ba - bb;
    // Alternate sort direction per block
    if (ba % 2 == 0) return qa->r - qb->r;
    return qb->r - qa->r;
}

void add(int pos) {
    cnt[arr[pos]]++;
    if (cnt[arr[pos]] == 1) distinct++;
}

void remove_elem(int pos) {
    cnt[arr[pos]]--;
    if (cnt[arr[pos]] == 0) distinct--;
}

int main(void) {
    n = 8;
    q = 3;
    int data[] = {1, 2, 3, 2, 1, 4, 3, 5};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    queries[0] = (Query){0, 4, 0};
    queries[1] = (Query){1, 6, 1};
    queries[2] = (Query){3, 7, 2};

    block_size = (int)sqrt(n) + 1;
    qsort(queries, q, sizeof(Query), cmp_queries);

    int curL = 0, curR = -1;
    distinct = 0;
    memset(cnt, 0, sizeof(cnt));

    for (int i = 0; i < q; i++) {
        int L = queries[i].l, R = queries[i].r;

        while (curR < R) add(++curR);
        while (curL > L) add(--curL);
        while (curR > R) remove_elem(curR--);
        while (curL < L) remove_elem(curL++);

        ans[queries[i].idx] = distinct;
    }

    for (int i = 0; i < q; i++) {
        printf("distinct[%d..%d] = %d\n",
               queries[i].l, queries[i].r, ans[i]);
    }

    return 0;
}
```

---

## 11. Persistent Segment Tree

### What Is Persistence?

A **persistent** data structure preserves all previous versions after updates. You can query any historical version.

### Core Idea

When updating a segment tree, instead of modifying nodes in-place, create **new nodes** along the path from root to the updated leaf. Old nodes are untouched → old root still valid.

```
Version 0 (original):
  root0 → [node A] → [node B] → [leaf]

Version 1 (after update at pos p):
  root1 → [new node A'] → [new node B'] → [new leaf']
                      ↘
                    (old nodes shared)
```

Only O(log N) new nodes per update. Total space: O(N + Q log N).

### Applications

- "What was the sum of [l, r] at time step t?"
- **Offline range kth smallest**: For each r, build version r of the tree.

### C Implementation (Persistent Segment Tree — Sum)

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005
#define MAXNODES (MAXN * 40)  // Enough nodes for persistence

int lc[MAXNODES], rc[MAXNODES]; // Left and right children
long long val[MAXNODES];        // Node value
int node_cnt = 0;
int roots[MAXN];                // roots[i] = root of version i
int n;

int new_node(void) {
    node_cnt++;
    lc[node_cnt] = rc[node_cnt] = 0;
    val[node_cnt] = 0;
    return node_cnt;
}

int build(int l, int r, int *arr) {
    int node = new_node();
    if (l == r) {
        val[node] = arr[l];
        return node;
    }
    int mid = (l + r) / 2;
    lc[node] = build(l, mid, arr);
    rc[node] = build(mid + 1, r, arr);
    val[node] = val[lc[node]] + val[rc[node]];
    return node;
}

// Returns new root after updating position pos to new_val
int update(int prev, int l, int r, int pos, long long new_val) {
    int node = new_node();
    lc[node] = lc[prev];
    rc[node] = rc[prev];
    val[node] = val[prev];

    if (l == r) {
        val[node] = new_val;
        return node;
    }
    int mid = (l + r) / 2;
    if (pos <= mid)
        lc[node] = update(lc[prev], l, mid, pos, new_val);
    else
        rc[node] = update(rc[prev], mid + 1, r, pos, new_val);
    val[node] = val[lc[node]] + val[rc[node]];
    return node;
}

long long query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql || node == 0) return 0;
    if (ql <= l && r <= qr) return val[node];
    int mid = (l + r) / 2;
    return query(lc[node], l, mid, ql, qr)
         + query(rc[node], mid + 1, r, ql, qr);
}

int main(void) {
    n = 5;
    int arr[] = {1, 2, 3, 4, 5};

    roots[0] = build(0, n - 1, arr);

    // Version 1: update arr[2] = 10
    roots[1] = update(roots[0], 0, n - 1, 2, 10);
    // Version 2: update arr[4] = 20
    roots[2] = update(roots[1], 0, n - 1, 4, 20);

    printf("V0 sum(0,4) = %lld\n", query(roots[0], 0, n-1, 0, 4)); // 15
    printf("V1 sum(0,4) = %lld\n", query(roots[1], 0, n-1, 0, 4)); // 22
    printf("V2 sum(0,4) = %lld\n", query(roots[2], 0, n-1, 0, 4)); // 38

    return 0;
}
```

---

## 12. Merge Sort Tree (Range Kth Smallest)

### What Is It?

Each segment tree node stores a **sorted list** of all elements in its range. This allows answering "kth smallest in range [l, r]" queries.

- **Build**: O(N log N) time, O(N log N) space
- **Query**: O(log² N) — binary search on answer, each check O(log N)

### Core Idea for "Count elements ≤ X in [l, r]"

At each node covering [ql, qr] fully, binary search for X in the sorted list → count elements ≤ X.
Sum these counts = total elements ≤ X in [l, r].

### C Implementation (Count ≤ X in range)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

// Dynamic arrays for each node's sorted elements
int *nodes[4 * MAXN];
int node_sizes[4 * MAXN];
int arr[MAXN];
int n;

int cmp_int(const void *a, const void *b) {
    return *(int *)a - *(int *)b;
}

void build(int node, int l, int r) {
    int size = r - l + 1;
    nodes[node] = (int *)malloc(size * sizeof(int));
    node_sizes[node] = size;
    for (int i = l; i <= r; i++) nodes[node][i - l] = arr[i];
    qsort(nodes[node], size, sizeof(int), cmp_int);

    if (l == r) return;
    int mid = (l + r) / 2;
    build(2 * node, l, mid);
    build(2 * node + 1, mid + 1, r);
}

// Count elements <= x in [ql, qr]
int count_leq(int node, int l, int r, int ql, int qr, int x) {
    if (qr < l || r < ql) return 0;
    if (ql <= l && r <= qr) {
        // Binary search in sorted nodes[node]
        int lo = 0, hi = node_sizes[node];
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if (nodes[node][mid] <= x) lo = mid + 1;
            else hi = mid;
        }
        return lo; // lo = count of elements <= x
    }
    int mid = (l + r) / 2;
    return count_leq(2 * node, l, mid, ql, qr, x)
         + count_leq(2 * node + 1, mid + 1, r, ql, qr, x);
}

// Kth smallest in [ql, qr]: binary search on value
int kth_smallest(int ql, int qr, int k) {
    // Binary search on the answer value
    // (using global sorted values for binary search bounds)
    int lo = 0, hi = 1e9; // or use sorted unique values
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (count_leq(1, 0, n - 1, ql, qr, mid) >= k)
            hi = mid;
        else
            lo = mid + 1;
    }
    return lo;
}

int main(void) {
    n = 6;
    int data[] = {3, 1, 4, 1, 5, 9};
    for (int i = 0; i < n; i++) arr[i] = data[i];
    build(1, 0, n - 1);

    printf("count<=3 in [0,4]: %d\n", count_leq(1, 0, n-1, 0, 4, 3)); // 3 (1,1,3)
    printf("2nd smallest in [0,4]: %d\n", kth_smallest(0, 4, 2)); // 1

    return 0;
}
```

---

## 13. Wavelet Tree

### What Is It?

A wavelet tree encodes an array by recursively partitioning its values into halves. It answers range queries about value distributions in O(log(max_val)) per query.

### Capabilities

- Range kth smallest: O(log V)
- Count elements in value range [a, b] within index range [l, r]: O(log V)
- Range frequency of a value: O(log V)

### Core Structure

```
Values in [lo, hi]:
  Partition into:
    Left subtree: values in [lo, mid]
    Right subtree: values in [mid+1, hi]

  For each position i in the node:
    If arr[i] <= mid → goes to left subtree
    Else → goes to right subtree
  
  Store: count of "goes left" at each prefix position → B[i]
```

### C Implementation (Compact)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Wavelet tree node: for each element, track how many went left up to position i
// Implementation for range kth smallest

#define MAXN 100005
#define LOG 18

// Flatten wavelet tree into arrays
int wt[LOG][MAXN];  // wt[level][pos] = value at this level
int cnt[LOG][MAXN]; // cnt[level][i] = # elements that went left in [0..i-1]
int n, lo_val, hi_val;
int arr[MAXN];

void build_level(int *from, int *to, int l, int r, int lo, int hi, int level) {
    if (l > r || lo == hi) return;
    int mid = (lo + hi) / 2;

    // Partition from[] into left (≤ mid) and right (> mid) in to[]
    int left_ptr = l, right_ptr = l;
    int right_start = l;
    // Count how many go left
    for (int i = l; i <= r; i++) if (from[i] <= mid) right_start++;

    int lp = l, rp = right_start;
    cnt[level][l] = 0;
    for (int i = l; i <= r; i++) {
        if (from[i] <= mid) {
            to[lp++] = from[i];
            cnt[level][i + 1] = cnt[level][i] + 1;
        } else {
            to[rp++] = from[i];
            cnt[level][i + 1] = cnt[level][i];
        }
    }

    build_level(to, from, l, right_start - 1, lo, mid, level + 1);
    build_level(to, from, right_start, r, mid + 1, hi, level + 1);
}

// Count elements <= x in [l, r]
int count_leq_val(int l, int r, int x) {
    int lo = lo_val, hi = hi_val, level = 0;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        int lb = cnt[level][l]; // # went left before l
        int rb = cnt[level][r + 1]; // # went left before r+1
        if (x <= mid) {
            r = l + (rb - lb) - 1;
            l = l + (lb - cnt[level][0]);  // Simplified for illustration
            hi = mid;
        } else {
            // go right
            lo = mid + 1;
        }
        level++;
    }
    return r - l + 1;  // Simplified
}
```

> **Note**: Wavelet Tree is complex to implement from scratch. In competitive programming, use it via template after mastering segment trees with lazy propagation. The C pseudocode above shows structure; for production use, refer to well-tested templates.

---

## 14. 2D Range Operations

### 2D Prefix Sum

```
grid[i][j] = value at cell (i, j)
prefix[i][j] = sum of all cells (r, c) where r < i and c < j

BUILD:
  prefix[i][j] = grid[i-1][j-1]
               + prefix[i-1][j] + prefix[i][j-1]
               - prefix[i-1][j-1]  (subtract double-counted corner)

QUERY(r1, c1, r2, c2) [1-indexed, inclusive]:
  = prefix[r2+1][c2+1]
  - prefix[r1][c2+1]
  - prefix[r2+1][c1]
  + prefix[r1][c1]
```

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXR 1005
#define MAXC 1005

long long prefix[MAXR][MAXC];
int R, C;

void build(int grid[MAXR][MAXC]) {
    for (int i = 1; i <= R; i++) {
        for (int j = 1; j <= C; j++) {
            prefix[i][j] = grid[i][j]
                + prefix[i-1][j] + prefix[i][j-1]
                - prefix[i-1][j-1];
        }
    }
}

long long query(int r1, int c1, int r2, int c2) {
    return prefix[r2][c2] - prefix[r1-1][c2]
         - prefix[r2][c1-1] + prefix[r1-1][c1-1];
}

int main(void) {
    R = 3; C = 3;
    int grid[MAXR][MAXC] = {
        {0, 0, 0, 0},
        {0, 1, 2, 3},
        {0, 4, 5, 6},
        {0, 7, 8, 9}
    };
    build(grid);
    printf("sum(1,1,2,2) = %lld\n", query(1, 1, 2, 2)); // 1+2+4+5=12
    printf("sum(2,2,3,3) = %lld\n", query(2, 2, 3, 3)); // 5+6+8+9=28
    return 0;
}
```

### 2D BIT (Fenwick Tree)

Supports 2D point update and 2D prefix sum query in O(log R * log C).

```c
long long bit2d[MAXR][MAXC];

void update2d(int x, int y, long long val) {
    for (int i = x; i <= R; i += i & (-i))
        for (int j = y; j <= C; j += j & (-j))
            bit2d[i][j] += val;
}

long long prefix2d(int x, int y) {
    long long s = 0;
    for (int i = x; i > 0; i -= i & (-i))
        for (int j = y; j > 0; j -= j & (-j))
            s += bit2d[i][j];
    return s;
}

long long query2d(int r1, int c1, int r2, int c2) {
    return prefix2d(r2, c2) - prefix2d(r1-1, c2)
         - prefix2d(r2, c1-1) + prefix2d(r1-1, c1-1);
}
```

---

## 15. Mental Models & Expert Thinking Strategies

### The Five-Question Framework (Before Coding)

Ask yourself these five questions when you see a range query problem:

```
1. STATIC or DYNAMIC?
   Static (no updates) → Prefix Sum / Sparse Table
   Dynamic (with updates) → Segment Tree / BIT

2. OFFLINE or ONLINE?
   Offline (all queries known) → Mo's Algorithm / Persistent Trees
   Online (one at a time) → Segment Tree / BIT

3. WHAT OPERATION?
   Idempotent (min, max, gcd) → Sparse Table O(1) query
   Non-idempotent (sum, product) → Prefix Sum / Segment Tree

4. POINT or RANGE updates?
   Point update + Range query → BIT (simpler) or Segment Tree
   Range update + Point query → Difference Array
   Range update + Range query → Lazy Segment Tree / 2-BIT

5. EXTRA CONSTRAINTS?
   Historical queries (version i) → Persistent Segment Tree
   2D operations → 2D BIT / 2D Segment Tree
   Kth smallest in range → Merge Sort Tree / Wavelet Tree
```

### The Lazy Tag Design Recipe

When designing lazy propagation for a new operation, answer:

```
1. What does tree[node] store? (sum of range? max of range?)
2. What does lazy[node] mean? (pending add? pending assign?)
3. How does lazy affect tree[node] without going deeper?
   → tree[node] += lazy * range_length  (for sum+add)
   → tree[node] = lazy  (for min+assign)
4. How do you combine two lazy tags?
   → For add: lazy_child += lazy_parent
   → For assign: lazy_child = lazy_parent (overwrite)
5. When is lazy "empty" (identity)?
   → For add: 0
   → For assign: a special sentinel like -INF
```

### Cognitive Principles for Range Operations Mastery

**1. Chunking (George Miller's 7±2)**
Range operations are built from chunks: prefix sums, difference arrays, tree traversals. Internalize each chunk until it's automatic. Then combine chunks.

**2. Deliberate Practice (Ericsson)**
Don't just read — implement. Every data structure here: implement it from scratch, debug, test edge cases (empty range, single element, entire array).

**3. The Region-of-Interest Mental Model**
Every range query asks: "What property does this region of the array have?" Train yourself to think: "Can I precompute enough information to answer this without looking at every element?"

**4. Lazy = Deferred Work**
The lazy paradigm appears everywhere in CS: lazy evaluation in functional programming, copy-on-write in OS, deferred rendering in graphics. Recognize this pattern — "mark now, act later."

**5. Telescoping / Cancellation**
Prefix sums, difference arrays, BIT — all exploit telescoping: `sum(l,r) = prefix(r) - prefix(l-1)`. Train your eye to see where cancellation can turn O(N) work into O(1).

**6. Meta-Learning: Build a Problem Taxonomy**
Create a personal journal. After solving each problem, write:
- Problem type (static/dynamic, point/range, offline/online)
- Which structure you used
- Why it was optimal
- What you'd try differently

Over time, you build a mental decision tree that fires instantly.

---

## 16. Problem Pattern Recognition Table

```
╔══════════════════════════════════════╦═══════════════════════════╦══════════════╗
║ Problem Statement                    ║ Data Structure            ║ Complexity   ║
╠══════════════════════════════════════╬═══════════════════════════╬══════════════╣
║ Static sum queries                   ║ Prefix Sum                ║ O(1) query   ║
║ Range add, point query               ║ Difference Array          ║ O(1) update  ║
║ Static RMQ                           ║ Sparse Table              ║ O(1) query   ║
║ Point update, range sum              ║ BIT / Seg Tree            ║ O(log N)     ║
║ Range add, range sum                 ║ Lazy Seg Tree / 2-BIT     ║ O(log N)     ║
║ Range assign, range sum              ║ Lazy Seg Tree             ║ O(log N)     ║
║ Range update, range min/max          ║ Lazy Seg Tree             ║ O(log N)     ║
║ Offline complex queries              ║ Mo's Algorithm            ║ O((N+Q)√N)   ║
║ Historical queries (version k)       ║ Persistent Seg Tree       ║ O(log N)     ║
║ Range kth smallest                   ║ Merge Sort / Wavelet Tree ║ O(log² N)    ║
║ 2D point update, 2D range sum        ║ 2D BIT                    ║ O(log²N)     ║
║ Count in value+index range           ║ Wavelet Tree              ║ O(log V)     ║
╚══════════════════════════════════════╩═══════════════════════════╩══════════════╝
```

### Common Mistakes to Avoid

```
1. Off-by-one errors:
   - Prefix sum: prefix[r+1] - prefix[l], NOT prefix[r] - prefix[l]
   - BIT: usually 1-indexed; adjust carefully for 0-indexed arrays

2. Lazy push_down timing:
   - ALWAYS push_down before recursing into children
   - NEVER push_down on leaf nodes (they have no children)

3. Integer overflow:
   - Sum of N elements each up to 10^9 → up to 10^14 → use long long / int64

4. Range update identity:
   - For range-assign lazy, use a special sentinel (not 0) to mean "no update"
   - Because assigning 0 is a valid operation!

5. Sparse Table for non-idempotent:
   - NEVER use sparse table for sum — overlap causes double counting
   - Only min, max, GCD, bitwise AND/OR

6. Difference array limitations:
   - Only works for "add a constant" updates, not "multiply" or "assign"
```

---

## Summary: The Master Flowchart

```
NEW RANGE PROBLEM
       |
       v
Is the array STATIC (no updates)?
  YES ──→ Range min/max query?
            YES ──→ Sparse Table   O(N log N) build, O(1) query
            NO  ──→ Range sum?
                      YES ──→ Prefix Sum   O(N) build, O(1) query
                      NO  ──→ Segment Tree (build only)
  NO
   |
   v
What type of UPDATE?
  POINT UPDATE only:
    Range sum query ──→ BIT   O(log N) both
    Range min/max   ──→ Segment Tree   O(log N) both

  RANGE UPDATE:
    Point query only ──→ Difference Array   O(1) update, O(N) rebuild
    Range query:
      Sum ──→ Lazy Seg Tree (add) OR 2-BIT
      Min/Max ──→ Lazy Seg Tree (min/max with lazy)
      Both add + assign ──→ Lazy Seg Tree (combined lazy)

  HISTORICAL queries needed?
    ──→ Persistent Segment Tree

  OFFLINE, complex queries?
    ──→ Mo's Algorithm

  Kth smallest in range?
    ──→ Merge Sort Tree O(log²N) OR Wavelet Tree O(log V)

  2D operations?
    ──→ 2D BIT or 2D Segment Tree
```

---

*"The master has failed more times than the beginner has tried."*
*You are not learning algorithms. You are training a mind to see structure in chaos.*

Keep implementing. Keep questioning. Keep refining.
Every data structure above was invented because someone asked:
**"Can we do better?"**

Now you ask the same question.

I'll now craft the complete, comprehensive guide as a `.md` file. This will be large and thorough.Here's your complete masterclass guide. Here's what's packed inside:

**16 chapters covering:**

1. **Foundations** — all vocabulary (range, query, update, lazy, idempotent, prefix, aggregate) with the 4-problem-type matrix and complexity hierarchy
2. **Prefix Sum** — build, query, 2D extension, XOR/product variants — C, Go, Rust
3. **Difference Array** — range-add in O(1), point rebuild — C, Go, Rust
4. **Sparse Table** — idempotency explained, RMQ in O(1) — C, Go, Rust
5. **Segment Tree (Basic)** — build, point update, range query with 3-case decision tree and call flow — C, Go, Rust
6. **Lazy Segment Tree** — full lazy propagation with exact call trace walkthrough, range-add + range-sum — C, Go, Rust (including Rust's `&mut self` correctness fix)
7. **Fenwick Tree (BIT)** — lowbit trick explained, prefix query, point update — C, Go, Rust
8. **BIT Range Update + Range Query** — 2-BIT mathematical derivation — C, Go, Rust
9. **Sqrt Decomposition** — block structure, partial/complete block handling — C
10. **Mo's Algorithm** — offline sorting, zigzag optimization, distinct count example — C
11. **Persistent Segment Tree** — versioned updates, path copying — C
12. **Merge Sort Tree** — range kth smallest with binary search — C
13. **Wavelet Tree** — structure explanation + C pseudocode
14. **2D Range Operations** — 2D prefix sum and 2D BIT — C
15. **Mental Models** — 5-question decision framework, lazy tag design recipe, cognitive principles (chunking, deliberate practice, telescoping)
16. **Master Flowchart & Pattern Table** — instantly identify the right structure for any problem