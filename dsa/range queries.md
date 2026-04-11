# Range Queries — Complete Deep-Dive Guide

> *"A range query asks a question over a contiguous sub-array. Mastering the data structures that answer these questions fast is the single most impactful chapter in competitive DSA."*

---

## Table of Contents

1. [What Is a Range Query?](#1-what-is-a-range-query)
2. [Prefix Sum — 1D](#2-prefix-sum--1d)
3. [Prefix Sum — 2D](#3-prefix-sum--2d)
4. [Difference Array](#4-difference-array)
5. [Sparse Table (RMQ)](#5-sparse-table-rmq)
6. [Segment Tree](#6-segment-tree)
7. [Segment Tree with Lazy Propagation](#7-segment-tree-with-lazy-propagation)
8. [Binary Indexed Tree (Fenwick Tree)](#8-binary-indexed-tree-fenwick-tree)
9. [Square Root Decomposition](#9-square-root-decomposition)
10. [Mo's Algorithm](#10-mos-algorithm)
11. [Choosing the Right Structure](#11-choosing-the-right-structure)
12. [Complexity Cheat Sheet](#12-complexity-cheat-sheet)

---

## 1. What Is a Range Query?

### Plain-Language Definition

Imagine an array of numbers, say exam scores of 1 million students.  
A **range query** asks: *"What is the sum (or min, max, GCD, XOR…) of elements from index `l` to index `r`?"*  
A **range update** asks: *"Add 5 to every element from index `l` to index `r`."*

Doing this naively (loop from `l` to `r`) takes **O(n)** per query. If you have **Q** queries on an array of size **n**, naïve is **O(n × Q)** — that is 10^12 operations for n = Q = 10^6. This is too slow.

Range query data structures reduce this to **O(1)**, **O(log n)**, or **O(√n)** per query.

### Vocabulary You Must Know

| Term | Meaning |
|------|---------|
| **Query** | Read-only question over a range [l, r] |
| **Update** | Modify one element (point update) or a range of elements (range update) |
| **Idempotent function** | f(f(x, x), x) = f(x, x). Example: min, max, GCD. Sum is NOT idempotent |
| **Associative function** | f(a, f(b, c)) = f(f(a, b), c). All functions we care about are associative |
| **Prefix** | Elements from index 0 to some index i |
| **Suffix** | Elements from some index i to the last |
| **Segment** | Contiguous subarray [l, r] |
| **Node** | A unit in a tree structure representing a segment |
| **Lazy tag / pending update** | A deferred update stored at a node, applied later |
| **Block** | A contiguous chunk of √n elements (used in Mo's / sqrt decomp) |

### The Core Trade-off

```
Fast Build → Slow Query   (naïve, O(1) build, O(n) query)
Slow Build → Fast Query   (sparse table, O(n log n) build, O(1) query)
Balanced   → Balanced     (segment tree, O(n) build, O(log n) query/update)
```

Every structure you will learn is a point on this trade-off curve.

---

## 2. Prefix Sum — 1D

### Concept

**Prefix sum** is the gateway technique. It is perhaps the single most reused idea in all of competitive programming.

Define:
```
pre[0] = 0
pre[i] = arr[0] + arr[1] + ... + arr[i-1]   (1-indexed prefix)
```

Then the sum of any range [l, r] (1-indexed) is:
```
sum(l, r) = pre[r] - pre[l-1]
```

Why does this work? Because `pre[r]` accumulates the sum from index 1 to r. Subtracting `pre[l-1]` removes the sum from 1 to l-1, leaving exactly l to r.

### Visual Walk-through

```
Array (1-indexed):  [3,  1,  4,  1,  5,  9,  2,  6]
Index:               1   2   3   4   5   6   7   8

Prefix array:
pre[0] = 0
pre[1] = 3
pre[2] = 4   (3+1)
pre[3] = 8   (3+1+4)
pre[4] = 9   (3+1+4+1)
pre[5] = 14  (3+1+4+1+5)
pre[6] = 23  (3+1+4+1+5+9)
pre[7] = 25  (3+1+4+1+5+9+2)
pre[8] = 31  (3+1+4+1+5+9+2+6)

Query: sum(3, 6) = pre[6] - pre[2] = 23 - 4 = 19
Check: 4+1+5+9 = 19  ✓
```

### Time and Space Complexity

| Operation | Complexity |
|-----------|-----------|
| Build prefix array | O(n) |
| Answer range sum query | O(1) |
| Point update (change arr[i]) | O(n) — must rebuild! |
| Space | O(n) |

> **Critical insight**: Prefix sum is ideal for **static arrays** (no updates after build). If you need updates, use Fenwick Tree or Segment Tree.

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * PrefixSum1D
 * -----------
 * pre[0] = 0 (sentinel)
 * pre[i] = arr[0] + arr[1] + ... + arr[i-1]
 * Query sum(l, r) — l and r are 1-indexed inclusive.
 */

typedef struct {
    long long *pre;  /* prefix array, size n+1 */
    int n;
} PrefixSum;

/* Build: O(n) */
PrefixSum ps_build(int *arr, int n) {
    PrefixSum ps;
    ps.n = n;
    ps.pre = (long long *)calloc(n + 1, sizeof(long long));
    for (int i = 1; i <= n; i++) {
        ps.pre[i] = ps.pre[i - 1] + arr[i - 1];
    }
    return ps;
}

/* Query sum [l, r], 1-indexed, inclusive: O(1) */
long long ps_query(PrefixSum *ps, int l, int r) {
    return ps->pre[r] - ps->pre[l - 1];
}

void ps_free(PrefixSum *ps) {
    free(ps->pre);
}

/* ---- demo ---- */
int main(void) {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = sizeof(arr) / sizeof(arr[0]);

    PrefixSum ps = ps_build(arr, n);

    printf("sum(3,6) = %lld\n", ps_query(&ps, 3, 6)); /* 19 */
    printf("sum(1,8) = %lld\n", ps_query(&ps, 1, 8)); /* 31 */
    printf("sum(2,4) = %lld\n", ps_query(&ps, 2, 4)); /* 6  */

    ps_free(&ps);
    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// PrefixSum1D holds the cumulative prefix sum array.
// All indices are 1-based (pre[0] = 0 is a sentinel).
type PrefixSum1D struct {
	pre []int64
}

// NewPrefixSum1D builds the prefix array in O(n).
func NewPrefixSum1D(arr []int) *PrefixSum1D {
	n := len(arr)
	pre := make([]int64, n+1)
	for i := 1; i <= n; i++ {
		pre[i] = pre[i-1] + int64(arr[i-1])
	}
	return &PrefixSum1D{pre: pre}
}

// Query returns the sum of arr[l..r] (1-indexed, inclusive) in O(1).
func (ps *PrefixSum1D) Query(l, r int) int64 {
	return ps.pre[r] - ps.pre[l-1]
}

func main() {
	arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
	ps := NewPrefixSum1D(arr)

	fmt.Println("sum(3,6) =", ps.Query(3, 6)) // 19
	fmt.Println("sum(1,8) =", ps.Query(1, 8)) // 31
	fmt.Println("sum(2,4) =", ps.Query(2, 4)) // 6
}
```

---

### Rust Implementation

```rust
/// PrefixSum1D — static range sum in O(1) after O(n) build.
/// Uses 1-indexed semantics: pre[0] = 0 (sentinel).
struct PrefixSum1D {
    pre: Vec<i64>,
}

impl PrefixSum1D {
    /// Build from a slice in O(n).
    fn new(arr: &[i64]) -> Self {
        let mut pre = vec![0i64; arr.len() + 1];
        for (i, &v) in arr.iter().enumerate() {
            pre[i + 1] = pre[i] + v;
        }
        PrefixSum1D { pre }
    }

    /// Sum of arr[l..=r] (1-indexed, inclusive) in O(1).
    fn query(&self, l: usize, r: usize) -> i64 {
        self.pre[r] - self.pre[l - 1]
    }
}

fn main() {
    let arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    let ps = PrefixSum1D::new(&arr);

    println!("sum(3,6) = {}", ps.query(3, 6)); // 19
    println!("sum(1,8) = {}", ps.query(1, 8)); // 31
    println!("sum(2,4) = {}", ps.query(2, 4)); // 6
}
```

---

## 3. Prefix Sum — 2D

### Concept

Extends to a 2D grid. Given an n×m matrix, answer: *"What is the sum of all elements in the sub-rectangle whose top-left is (r1,c1) and bottom-right is (r2,c2)?"*

Define:
```
pre2d[i][j] = sum of all elements in rectangle (1,1) to (i,j)
```

**Build formula** (inclusion-exclusion on rectangles):
```
pre2d[i][j] = arr[i][j]
             + pre2d[i-1][j]
             + pre2d[i][j-1]
             - pre2d[i-1][j-1]
```

**Query formula**:
```
sum(r1, c1, r2, c2) = pre2d[r2][c2]
                    - pre2d[r1-1][c2]
                    - pre2d[r2][c1-1]
                    + pre2d[r1-1][c1-1]
```

### Why Inclusion-Exclusion?

```
         c1-1  c2
          |    |
r1-1 ---- A -- B
          |    |
r2   ---- C -- D

sum(r1,c1,r2,c2) = D - B - C + A

Where D = pre2d[r2][c2]  (whole rectangle 1,1 to r2,c2)
      B = pre2d[r1-1][c2] (region above our rectangle)
      C = pre2d[r2][c1-1] (region left of our rectangle)
      A = pre2d[r1-1][c1-1] (we subtracted A twice, add back once)
```

---

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 1005

long long pre2d[MAXN][MAXN];
int arr[MAXN][MAXN];
int n, m;

/* Build 2D prefix sum: O(n*m) */
void build2d(void) {
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= m; j++) {
            pre2d[i][j] = arr[i][j]
                        + pre2d[i-1][j]
                        + pre2d[i][j-1]
                        - pre2d[i-1][j-1];
        }
    }
}

/* Query sum of sub-rectangle (r1,c1)-(r2,c2), 1-indexed: O(1) */
long long query2d(int r1, int c1, int r2, int c2) {
    return pre2d[r2][c2]
         - pre2d[r1-1][c2]
         - pre2d[r2][c1-1]
         + pre2d[r1-1][c1-1];
}

int main(void) {
    n = 3; m = 3;
    int data[3][3] = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= m; j++)
            arr[i][j] = data[i-1][j-1];

    build2d();

    /* Sub-rectangle (2,2) to (3,3): 5+6+8+9 = 28 */
    printf("sum(2,2,3,3) = %lld\n", query2d(2, 2, 3, 3));

    /* Whole matrix: 1+2+...+9 = 45 */
    printf("sum(1,1,3,3) = %lld\n", query2d(1, 1, 3, 3));

    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// PrefixSum2D enables O(1) rectangle sum queries after O(n*m) build.
type PrefixSum2D struct {
	pre [][]int64
	n, m int
}

func NewPrefixSum2D(grid [][]int) *PrefixSum2D {
	n, m := len(grid), len(grid[0])
	pre := make([][]int64, n+1)
	for i := range pre {
		pre[i] = make([]int64, m+1)
	}
	for i := 1; i <= n; i++ {
		for j := 1; j <= m; j++ {
			pre[i][j] = int64(grid[i-1][j-1]) +
				pre[i-1][j] + pre[i][j-1] - pre[i-1][j-1]
		}
	}
	return &PrefixSum2D{pre: pre, n: n, m: m}
}

// Query returns the sum of sub-rectangle (r1,c1)-(r2,c2), 1-indexed.
func (ps *PrefixSum2D) Query(r1, c1, r2, c2 int) int64 {
	return ps.pre[r2][c2] -
		ps.pre[r1-1][c2] -
		ps.pre[r2][c1-1] +
		ps.pre[r1-1][c1-1]
}

func main() {
	grid := [][]int{
		{1, 2, 3},
		{4, 5, 6},
		{7, 8, 9},
	}
	ps := NewPrefixSum2D(grid)
	fmt.Println("sum(2,2,3,3) =", ps.Query(2, 2, 3, 3)) // 28
	fmt.Println("sum(1,1,3,3) =", ps.Query(1, 1, 3, 3)) // 45
}
```

---

### Rust Implementation

```rust
struct PrefixSum2D {
    pre: Vec<Vec<i64>>,
}

impl PrefixSum2D {
    fn new(grid: &[Vec<i64>]) -> Self {
        let n = grid.len();
        let m = grid[0].len();
        let mut pre = vec![vec![0i64; m + 1]; n + 1];
        for i in 1..=n {
            for j in 1..=m {
                pre[i][j] = grid[i - 1][j - 1]
                    + pre[i - 1][j]
                    + pre[i][j - 1]
                    - pre[i - 1][j - 1];
            }
        }
        PrefixSum2D { pre }
    }

    /// Sum of sub-rectangle (r1,c1)-(r2,c2), 1-indexed, in O(1).
    fn query(&self, r1: usize, c1: usize, r2: usize, c2: usize) -> i64 {
        self.pre[r2][c2]
            - self.pre[r1 - 1][c2]
            - self.pre[r2][c1 - 1]
            + self.pre[r1 - 1][c1 - 1]
    }
}

fn main() {
    let grid = vec![
        vec![1, 2, 3],
        vec![4, 5, 6],
        vec![7, 8, 9],
    ];
    let ps = PrefixSum2D::new(&grid);
    println!("sum(2,2,3,3) = {}", ps.query(2, 2, 3, 3)); // 28
    println!("sum(1,1,3,3) = {}", ps.query(1, 1, 3, 3)); // 45
}
```

---

## 4. Difference Array

### Concept

The difference array is the **inverse** of prefix sum. It is designed for **range update + point query**, the opposite problem.

**Problem**: Apply `Q` updates of the form "add `v` to every element in [l, r]", then answer "what is the value of element at index i?"

**Naïve approach**: Each update is O(n). Total: O(n × Q). Too slow.

**Difference array approach**:
- Build `diff[i] = arr[i] - arr[i-1]` (with diff[0] = arr[0]).
- To add `v` to range [l, r]: set `diff[l] += v` and `diff[r+1] -= v`. This is O(1) per update!
- To reconstruct arr after all updates: compute prefix sum of diff. O(n) once.

### Why Does It Work?

The prefix sum of the difference array recovers the original array.  
When you do `diff[l] += v`, that `v` propagates through the prefix sum to all positions l, l+1, ..., n-1.  
When you do `diff[r+1] -= v`, that `-v` cancels the propagation at position r+1 and beyond.  
Net result: only indices l to r receive `+v`.

```
arr    = [0, 0, 0, 0, 0, 0]   (1-indexed, zero initially)
diff   = [0, 0, 0, 0, 0, 0]

Update: add 3 to [2, 4]
diff[2] += 3  =>  diff = [0, 3, 0, 0, 0, 0]
diff[5] -= 3  =>  diff = [0, 3, 0, 0,-3, 0]

Update: add 2 to [1, 3]
diff[1] += 2  =>  diff = [2, 3, 0, 0,-3, 0]
diff[4] -= 2  =>  diff = [2, 3, 0,-2,-3, 0]

Final arr = prefix sum of diff:
arr[1] = 2
arr[2] = 2+3 = 5
arr[3] = 2+3+0 = 5
arr[4] = 2+3+0-2 = 3
arr[5] = 2+3+0-2-3 = 0
```

---

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long diff[MAXN]; /* difference array, 1-indexed */
int n;

/* Range update: add val to arr[l..r], O(1) */
void range_add(int l, int r, long long val) {
    diff[l]   += val;
    diff[r+1] -= val;
}

/* Reconstruct arr[i] after all updates: O(n) once, then O(1) per query */
void reconstruct(long long *arr) {
    arr[1] = diff[1];
    for (int i = 2; i <= n; i++) {
        arr[i] = arr[i-1] + diff[i];
    }
}

int main(void) {
    n = 6;
    memset(diff, 0, sizeof(diff));

    range_add(2, 4, 3);   /* add 3 to positions 2,3,4 */
    range_add(1, 3, 2);   /* add 2 to positions 1,2,3 */

    long long arr[MAXN];
    reconstruct(arr);

    for (int i = 1; i <= n; i++) {
        printf("arr[%d] = %lld\n", i, arr[i]);
    }
    /* Expected: 2 5 5 3 0 0 */
    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// DiffArray enables O(1) range updates and O(n) final reconstruction.
type DiffArray struct {
	diff []int64
	n    int
}

func NewDiffArray(n int) *DiffArray {
	return &DiffArray{diff: make([]int64, n+2), n: n}
}

// RangeAdd adds val to every element in [l, r] (1-indexed) in O(1).
func (d *DiffArray) RangeAdd(l, r int, val int64) {
	d.diff[l] += val
	d.diff[r+1] -= val
}

// Reconstruct returns the final array after all updates in O(n).
func (d *DiffArray) Reconstruct() []int64 {
	arr := make([]int64, d.n+1)
	arr[1] = d.diff[1]
	for i := 2; i <= d.n; i++ {
		arr[i] = arr[i-1] + d.diff[i]
	}
	return arr
}

func main() {
	da := NewDiffArray(6)
	da.RangeAdd(2, 4, 3)
	da.RangeAdd(1, 3, 2)

	arr := da.Reconstruct()
	for i := 1; i <= 6; i++ {
		fmt.Printf("arr[%d] = %d\n", i, arr[i])
	}
}
```

---

### Rust Implementation

```rust
struct DiffArray {
    diff: Vec<i64>,
    n: usize,
}

impl DiffArray {
    fn new(n: usize) -> Self {
        DiffArray { diff: vec![0; n + 2], n }
    }

    /// Add val to every element in [l, r] (1-indexed) in O(1).
    fn range_add(&mut self, l: usize, r: usize, val: i64) {
        self.diff[l] += val;
        self.diff[r + 1] -= val;
    }

    /// Reconstruct the final array in O(n).
    fn reconstruct(&self) -> Vec<i64> {
        let mut arr = vec![0i64; self.n + 1];
        arr[1] = self.diff[1];
        for i in 2..=self.n {
            arr[i] = arr[i - 1] + self.diff[i];
        }
        arr
    }
}

fn main() {
    let mut da = DiffArray::new(6);
    da.range_add(2, 4, 3);
    da.range_add(1, 3, 2);

    let arr = da.reconstruct();
    for i in 1..=6 {
        println!("arr[{}] = {}", i, arr[i]);
    }
}
```

---

## 5. Sparse Table (RMQ)

### Concept

**RMQ = Range Minimum Query** (or Range Maximum Query — same idea).

**Problem**: Given a static array, answer Q queries of the form "what is the minimum element in [l, r]?"

**Key idea**: Any range [l, r] can be covered by **two possibly overlapping intervals** of length that is a power of 2, as long as min is the function (because min is idempotent — taking the min of an element already in the answer again doesn't change the answer).

### What Is "Idempotent"?

A function `f` is **idempotent** if `f(x, x) = x`. Examples: min(5, 5) = 5, max(3, 3) = 3, gcd(6, 6) = 6. Sum is NOT idempotent: 5+5 = 10 ≠ 5.

Sparse table works for idempotent functions only (since ranges may overlap). For non-idempotent functions (like sum), use a Fenwick Tree or Segment Tree.

### Build

Define `sparse[j][i]` = the minimum in the range starting at index `i` with length `2^j`.

```
sparse[0][i] = arr[i]                     (range of length 1 = 2^0)
sparse[j][i] = min(sparse[j-1][i], sparse[j-1][i + 2^(j-1)])
```

This says: "the min of a range of length 2^j = min of the left half and right half, each of length 2^(j-1)."

### Query

For a query [l, r], find `k = floor(log2(r - l + 1))`.  
Then: `min(l, r) = min(sparse[k][l], sparse[k][r - 2^k + 1])`

These two ranges overlap, but that's fine because min is idempotent.

```
Array:  [3, 1, 4, 1, 5, 9, 2, 6]
         0  1  2  3  4  5  6  7

sparse[0] = [3, 1, 4, 1, 5, 9, 2, 6]  (each element alone)
sparse[1] = [1, 1, 1, 1, 5, 2, 2, -]  (min of pairs)
sparse[2] = [1, 1, 1, 1, 2, 2, -, -]  (min of quads)
sparse[3] = [1, 1, -, -, -, -, -, -]  (min of octets)

Query min(2, 6) — 0-indexed, elements: 4,1,5,9,2
  len = 6-2+1 = 5, k = floor(log2(5)) = 2
  = min(sparse[2][2], sparse[2][6-4+1]) = min(sparse[2][2], sparse[2][3])
  = min(1, 1) = 1  ✓
```

### Time and Space Complexity

| Operation | Complexity |
|-----------|-----------|
| Build | O(n log n) |
| Query (RMQ) | O(1) |
| Update | NOT supported (static only) |
| Space | O(n log n) |

---

### C Implementation

```c
#include <stdio.h>
#include <math.h>

#define MAXN  100005
#define MAXLOG 17   /* log2(10^5) ≈ 17 */

int sparse[MAXLOG][MAXN];
int log2_floor[MAXN];
int n;

static inline int min2(int a, int b) { return a < b ? a : b; }

/* Precompute floor(log2(i)) for i in [1, n]: O(n) */
void build_log(void) {
    log2_floor[1] = 0;
    for (int i = 2; i <= n; i++) {
        log2_floor[i] = log2_floor[i / 2] + 1;
    }
}

/* Build sparse table: O(n log n) */
void build_sparse(int *arr) {
    for (int i = 0; i < n; i++) sparse[0][i] = arr[i];
    for (int j = 1; (1 << j) <= n; j++) {
        for (int i = 0; i + (1 << j) - 1 < n; i++) {
            sparse[j][i] = min2(sparse[j-1][i], sparse[j-1][i + (1 << (j-1))]);
        }
    }
}

/* Query min in [l, r] (0-indexed, inclusive): O(1) */
int query_min(int l, int r) {
    int k = log2_floor[r - l + 1];
    return min2(sparse[k][l], sparse[k][r - (1 << k) + 1]);
}

int main(void) {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    n = 8;

    build_log();
    build_sparse(arr);

    printf("min(0,7) = %d\n", query_min(0, 7)); /* 1 */
    printf("min(4,7) = %d\n", query_min(4, 7)); /* 2 */
    printf("min(2,6) = %d\n", query_min(2, 6)); /* 1 */

    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

const MAXLOG = 17

// SparseTable supports O(1) range minimum queries on a static array.
type SparseTable struct {
	table    [MAXLOG][]int
	log2     []int
	n        int
}

func NewSparseTable(arr []int) *SparseTable {
	n := len(arr)
	st := &SparseTable{n: n}

	// Precompute floor(log2) values
	st.log2 = make([]int, n+1)
	st.log2[1] = 0
	for i := 2; i <= n; i++ {
		st.log2[i] = st.log2[i/2] + 1
	}

	// Build table
	st.table[0] = make([]int, n)
	copy(st.table[0], arr)

	for j := 1; (1 << j) <= n; j++ {
		length := n - (1 << j) + 1
		st.table[j] = make([]int, length)
		for i := 0; i < length; i++ {
			a := st.table[j-1][i]
			b := st.table[j-1][i+(1<<(j-1))]
			if a < b {
				st.table[j][i] = a
			} else {
				st.table[j][i] = b
			}
		}
	}
	return st
}

// QueryMin returns the minimum in arr[l..r] (0-indexed) in O(1).
func (st *SparseTable) QueryMin(l, r int) int {
	k := st.log2[r-l+1]
	a := st.table[k][l]
	b := st.table[k][r-(1<<k)+1]
	if a < b {
		return a
	}
	return b
}

func main() {
	arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
	st := NewSparseTable(arr)

	fmt.Println("min(0,7) =", st.QueryMin(0, 7)) // 1
	fmt.Println("min(4,7) =", st.QueryMin(4, 7)) // 2
	fmt.Println("min(2,6) =", st.QueryMin(2, 6)) // 1
}
```

---

### Rust Implementation

```rust
const MAXLOG: usize = 17;

/// SparseTable — O(n log n) build, O(1) RMQ on static arrays.
struct SparseTable {
    table: Vec<Vec<i32>>,
    log2: Vec<usize>,
    n: usize,
}

impl SparseTable {
    fn new(arr: &[i32]) -> Self {
        let n = arr.len();
        let mut log2 = vec![0usize; n + 1];
        for i in 2..=n {
            log2[i] = log2[i / 2] + 1;
        }

        let mut table: Vec<Vec<i32>> = vec![arr.to_vec()];
        let mut j = 1;
        while (1 << j) <= n {
            let half = 1 << (j - 1);
            let len = n - (1 << j) + 1;
            let prev = table[j - 1].clone();
            let row: Vec<i32> = (0..len)
                .map(|i| prev[i].min(prev[i + half]))
                .collect();
            table.push(row);
            j += 1;
        }

        SparseTable { table, log2, n }
    }

    /// Range minimum query on [l, r] (0-indexed, inclusive) in O(1).
    fn query_min(&self, l: usize, r: usize) -> i32 {
        let k = self.log2[r - l + 1];
        self.table[k][l].min(self.table[k][r - (1 << k) + 1])
    }
}

fn main() {
    let arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    let st = SparseTable::new(&arr);

    println!("min(0,7) = {}", st.query_min(0, 7)); // 1
    println!("min(4,7) = {}", st.query_min(4, 7)); // 2
    println!("min(2,6) = {}", st.query_min(2, 6)); // 1
}
```

---

## 6. Segment Tree

### Concept

The **Segment Tree** is the most versatile and important range query data structure. It handles:
- Range queries (sum, min, max, GCD, XOR, etc.)
- Point updates
- Range updates (with lazy propagation, covered in Section 7)

### Structure

A segment tree is a **complete binary tree** built over an array. Each node stores the aggregate (e.g., sum) of a contiguous segment of the array.

```
Array:  [1, 3, 2, 7, 9, 11]
         0  1  2  3  4   5

Segment Tree (sum):

                  [0..5] = 33
                /              \
         [0..2] = 6         [3..5] = 27
          /    \               /     \
      [0..1]=4 [2..2]=2   [3..4]=16 [5..5]=11
       / \
  [0]=1 [1]=3
```

**Key Insight**:
- Root = entire array [0, n-1]
- Each node [l, r] has left child [l, mid] and right child [mid+1, r], where mid = (l+r)/2
- Leaves = individual elements
- Internal nodes = aggregate of children

### Indexing in a 1-Based Array

We store the segment tree in a 1D array of size `4*n` (safe upper bound).  
- Node at index `v` has left child at `2*v` and right child at `2*v+1`.
- This is a standard binary heap-style indexing.

### Build: O(n)

```
build(node, l, r):
    if l == r:
        tree[node] = arr[l]
        return
    mid = (l + r) / 2
    build(2*node, l, mid)
    build(2*node+1, mid+1, r)
    tree[node] = tree[2*node] + tree[2*node+1]   // combine children
```

### Point Update: O(log n)

To update arr[pos], walk from root to leaf pos, updating each ancestor along the way.

```
update(node, l, r, pos, val):
    if l == r:
        tree[node] = val
        return
    mid = (l + r) / 2
    if pos <= mid: update(2*node, l, mid, pos, val)
    else:          update(2*node+1, mid+1, r, pos, val)
    tree[node] = tree[2*node] + tree[2*node+1]
```

### Range Query: O(log n)

Three cases when visiting a node [l, r] for query [ql, qr]:
1. **No overlap**: [l, r] and [ql, qr] are disjoint → return identity (0 for sum)
2. **Full overlap**: [l, r] is completely inside [ql, qr] → return tree[node]
3. **Partial overlap**: recurse on both children, combine results

```
query(node, l, r, ql, qr):
    if qr < l or r < ql: return 0          // no overlap
    if ql <= l and r <= qr: return tree[node]  // full overlap
    mid = (l + r) / 2
    left_sum  = query(2*node, l, mid, ql, qr)
    right_sum = query(2*node+1, mid+1, r, ql, qr)
    return left_sum + right_sum
```

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN];
int n;

/* Build segment tree for range sum: O(n) */
void build(int node, int l, int r, long long *arr) {
    if (l == r) {
        tree[node] = arr[l];
        return;
    }
    int mid = (l + r) / 2;
    build(2 * node, l, mid, arr);
    build(2 * node + 1, mid + 1, r, arr);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

/* Point update: set arr[pos] = val, O(log n) */
void update(int node, int l, int r, int pos, long long val) {
    if (l == r) {
        tree[node] = val;
        return;
    }
    int mid = (l + r) / 2;
    if (pos <= mid) update(2 * node, l, mid, pos, val);
    else            update(2 * node + 1, mid + 1, r, pos, val);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

/* Range sum query [ql, qr]: O(log n) */
long long query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0;              /* no overlap */
    if (ql <= l && r <= qr) return tree[node];   /* full overlap */
    int mid = (l + r) / 2;
    return query(2 * node, l, mid, ql, qr)
         + query(2 * node + 1, mid + 1, r, ql, qr);
}

int main(void) {
    long long arr[] = {1, 3, 2, 7, 9, 11};
    n = 6;

    build(1, 0, n - 1, arr);

    printf("sum(1,4) = %lld\n", query(1, 0, n-1, 1, 4)); /* 3+2+7+9=21 */
    printf("sum(0,5) = %lld\n", query(1, 0, n-1, 0, 5)); /* 33 */

    /* Update arr[2] = 10 */
    update(1, 0, n - 1, 2, 10);
    printf("After update arr[2]=10:\n");
    printf("sum(1,4) = %lld\n", query(1, 0, n-1, 1, 4)); /* 3+10+7+9=29 */

    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// SegTree is a segment tree for range sum queries with point updates.
type SegTree struct {
	tree []int64
	n    int
}

func NewSegTree(arr []int64) *SegTree {
	n := len(arr)
	st := &SegTree{tree: make([]int64, 4*n), n: n}
	st.build(1, 0, n-1, arr)
	return st
}

func (st *SegTree) build(node, l, r int, arr []int64) {
	if l == r {
		st.tree[node] = arr[l]
		return
	}
	mid := (l + r) / 2
	st.build(2*node, l, mid, arr)
	st.build(2*node+1, mid+1, r, arr)
	st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

// Update sets arr[pos] = val in O(log n).
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

// Query returns the sum of arr[l..r] in O(log n).
func (st *SegTree) Query(l, r int) int64 {
	return st.query(1, 0, st.n-1, l, r)
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
	arr := []int64{1, 3, 2, 7, 9, 11}
	st := NewSegTree(arr)

	fmt.Println("sum(1,4) =", st.Query(1, 4)) // 21
	fmt.Println("sum(0,5) =", st.Query(0, 5)) // 33

	st.Update(2, 10)
	fmt.Println("After update arr[2]=10:")
	fmt.Println("sum(1,4) =", st.Query(1, 4)) // 29
}
```

---

### Rust Implementation

```rust
/// SegTree — range sum query, point update. O(n) build, O(log n) query/update.
struct SegTree {
    tree: Vec<i64>,
    n: usize,
}

impl SegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = SegTree { tree: vec![0; 4 * n], n };
        st.build(1, 0, n - 1, arr);
        st
    }

    fn build(&mut self, node: usize, l: usize, r: usize, arr: &[i64]) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build(2 * node, l, mid, arr);
        self.build(2 * node + 1, mid + 1, r, arr);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    /// Point update: set arr[pos] = val in O(log n).
    fn update(&mut self, pos: usize, val: i64) {
        self.update_inner(1, 0, self.n - 1, pos, val);
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

    /// Range sum query [ql, qr] in O(log n).
    fn query(&self, ql: usize, qr: usize) -> i64 {
        self.query_inner(1, 0, self.n - 1, ql, qr)
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
    let arr = vec![1, 3, 2, 7, 9, 11];
    let mut st = SegTree::new(&arr);

    println!("sum(1,4) = {}", st.query(1, 4)); // 21
    println!("sum(0,5) = {}", st.query(0, 5)); // 33

    st.update(2, 10);
    println!("After update arr[2]=10:");
    println!("sum(1,4) = {}", st.query(1, 4)); // 29
}
```

---

## 7. Segment Tree with Lazy Propagation

### Concept

**Problem**: Support range updates. Without lazy propagation, "add 5 to every element in [l, r]" would require touching O(n) leaf nodes — no better than naïve.

**Lazy propagation** = defer (postpone) updates. When you visit a node and need to apply an update to all its children, you don't do it immediately. Instead, you store a **lazy tag** at that node meaning "I need to propagate this update to my children later."

You only push the lazy tag down when you actually need to access the children (during a query or another update).

### What Does "Push Down" Mean?

When you arrive at a node that has a pending lazy tag, you:
1. Apply the tag to the node's value (update the stored aggregate).
2. Pass the tag to the left and right children (so they know about the pending update).
3. Clear the tag at the current node.

This is called **push down** or **lazy push** or **propagation**.

### Mental Model: Whiteboard of Pending Work

Think of each node as having a sticky note.  
"Add 5 to everyone below me."  
When someone needs to look at your children, you first hand them each a copy of your note, then tear yours off.

### Walk-through

```
Segment Tree for sum on [0..5]:

Start state:
  Node covering [0..5] = 33, lazy = 0
  Node covering [0..2] =  6, lazy = 0
  Node covering [3..5] = 27, lazy = 0
  ... (leaves)

Range update: add 3 to [1..4]

  Visit [0..5]: partial overlap. Push down (lazy=0, nothing to push). Recurse.
    Visit [0..2]: partial overlap.
      Visit [0..1]: partial overlap.
        Visit [0..0]: no overlap. Return.
        Visit [1..1]: full overlap. tree[1..1] += 3*(1 element). lazy[1..1] += 3.
      Update [0..1] = tree[0..0] + tree[1..1]
    Visit [2..2]: full overlap. tree[2..2] += 3*1. lazy[2..2] += 3.
    Update [0..2]
    Visit [3..5]: partial overlap.
      Visit [3..4]: full overlap. tree[3..4] += 3*2. lazy[3..4] += 3.
      Visit [5..5]: no overlap. Return.
    Update [3..5]
  Update [0..5]
```

### Key Rule

When a node with lazy tag is pushed down:
```
child.lazy  += parent.lazy
child.value += parent.lazy * (number of elements in child's range)
parent.lazy  = 0
```

---

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN]; /* sum stored in each node */
long long lazy[4 * MAXN]; /* pending add value for this node's range */
int n;

/* Push down the lazy tag from node to its two children */
static void push_down(int node, int l, int r) {
    if (lazy[node] == 0) return;
    int mid = (l + r) / 2;
    int lc = 2 * node, rc = 2 * node + 1;

    /* Apply lazy to left child */
    tree[lc]  += lazy[node] * (mid - l + 1);
    lazy[lc]  += lazy[node];

    /* Apply lazy to right child */
    tree[rc]  += lazy[node] * (r - mid);
    lazy[rc]  += lazy[node];

    /* Clear the tag */
    lazy[node] = 0;
}

/* Build: O(n) */
void build(int node, int l, int r, long long *arr) {
    lazy[node] = 0;
    if (l == r) { tree[node] = arr[l]; return; }
    int mid = (l + r) / 2;
    build(2 * node, l, mid, arr);
    build(2 * node + 1, mid + 1, r, arr);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

/* Range add: add val to every element in [ql, qr]: O(log n) */
void range_add(int node, int l, int r, int ql, int qr, long long val) {
    if (qr < l || r < ql) return;
    if (ql <= l && r <= qr) {
        tree[node] += val * (r - l + 1);
        lazy[node] += val;
        return;
    }
    push_down(node, l, r);
    int mid = (l + r) / 2;
    range_add(2 * node, l, mid, ql, qr, val);
    range_add(2 * node + 1, mid + 1, r, ql, qr, val);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

/* Range sum query [ql, qr]: O(log n) */
long long range_query(int node, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0;
    if (ql <= l && r <= qr) return tree[node];
    push_down(node, l, r);
    int mid = (l + r) / 2;
    return range_query(2 * node, l, mid, ql, qr)
         + range_query(2 * node + 1, mid + 1, r, ql, qr);
}

int main(void) {
    long long arr[] = {1, 3, 2, 7, 9, 11};
    n = 6;

    build(1, 0, n - 1, arr);

    printf("sum(1,4) = %lld\n", range_query(1, 0, n-1, 1, 4)); /* 21 */

    /* Add 3 to every element in [1..4] */
    range_add(1, 0, n - 1, 1, 4, 3);
    printf("After add 3 to [1,4]:\n");
    printf("sum(0,5) = %lld\n", range_query(1, 0, n-1, 0, 5)); /* 33+12=45 */
    printf("sum(1,4) = %lld\n", range_query(1, 0, n-1, 1, 4)); /* 21+12=33 */

    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// LazySegTree is a segment tree supporting range-add and range-sum queries.
type LazySegTree struct {
	tree []int64
	lazy []int64
	n    int
}

func NewLazySegTree(arr []int64) *LazySegTree {
	n := len(arr)
	st := &LazySegTree{
		tree: make([]int64, 4*n),
		lazy: make([]int64, 4*n),
		n:    n,
	}
	st.build(1, 0, n-1, arr)
	return st
}

func (st *LazySegTree) pushDown(node, l, r int) {
	if st.lazy[node] == 0 {
		return
	}
	mid := (l + r) / 2
	lc, rc := 2*node, 2*node+1
	st.tree[lc] += st.lazy[node] * int64(mid-l+1)
	st.lazy[lc] += st.lazy[node]
	st.tree[rc] += st.lazy[node] * int64(r-mid)
	st.lazy[rc] += st.lazy[node]
	st.lazy[node] = 0
}

func (st *LazySegTree) build(node, l, r int, arr []int64) {
	if l == r {
		st.tree[node] = arr[l]
		return
	}
	mid := (l + r) / 2
	st.build(2*node, l, mid, arr)
	st.build(2*node+1, mid+1, r, arr)
	st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

// RangeAdd adds val to every element in [ql, qr] in O(log n).
func (st *LazySegTree) RangeAdd(ql, qr int, val int64) {
	st.rangeAdd(1, 0, st.n-1, ql, qr, val)
}

func (st *LazySegTree) rangeAdd(node, l, r, ql, qr int, val int64) {
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
	st.rangeAdd(2*node, l, mid, ql, qr, val)
	st.rangeAdd(2*node+1, mid+1, r, ql, qr, val)
	st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

// Query returns the sum of arr[ql..qr] in O(log n).
func (st *LazySegTree) Query(ql, qr int) int64 {
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
	arr := []int64{1, 3, 2, 7, 9, 11}
	st := NewLazySegTree(arr)

	fmt.Println("sum(1,4) =", st.Query(1, 4)) // 21
	st.RangeAdd(1, 4, 3)
	fmt.Println("After RangeAdd(1,4,3):")
	fmt.Println("sum(0,5) =", st.Query(0, 5)) // 45
	fmt.Println("sum(1,4) =", st.Query(1, 4)) // 33
}
```

---

### Rust Implementation

```rust
/// LazySegTree — range-add updates, range-sum queries. O(log n) per op.
struct LazySegTree {
    tree: Vec<i64>,
    lazy: Vec<i64>,
    n: usize,
}

impl LazySegTree {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut st = LazySegTree {
            tree: vec![0; 4 * n],
            lazy: vec![0; 4 * n],
            n,
        };
        st.build(1, 0, n - 1, arr);
        st
    }

    fn build(&mut self, node: usize, l: usize, r: usize, arr: &[i64]) {
        if l == r {
            self.tree[node] = arr[l];
            return;
        }
        let mid = (l + r) / 2;
        self.build(2 * node, l, mid, arr);
        self.build(2 * node + 1, mid + 1, r, arr);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn push_down(&mut self, node: usize, l: usize, r: usize) {
        if self.lazy[node] == 0 {
            return;
        }
        let mid = (l + r) / 2;
        let (lc, rc) = (2 * node, 2 * node + 1);
        self.tree[lc] += self.lazy[node] * (mid - l + 1) as i64;
        self.lazy[lc] += self.lazy[node];
        self.tree[rc] += self.lazy[node] * (r - mid) as i64;
        self.lazy[rc] += self.lazy[node];
        self.lazy[node] = 0;
    }

    /// Add val to arr[ql..=qr] in O(log n).
    fn range_add(&mut self, ql: usize, qr: usize, val: i64) {
        self.range_add_inner(1, 0, self.n - 1, ql, qr, val);
    }

    fn range_add_inner(
        &mut self, node: usize, l: usize, r: usize,
        ql: usize, qr: usize, val: i64,
    ) {
        if qr < l || r < ql { return; }
        if ql <= l && r <= qr {
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.range_add_inner(2 * node, l, mid, ql, qr, val);
        self.range_add_inner(2 * node + 1, mid + 1, r, ql, qr, val);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    /// Sum of arr[ql..=qr] in O(log n).
    fn query(&mut self, ql: usize, qr: usize) -> i64 {
        self.query_inner(1, 0, self.n - 1, ql, qr)
    }

    fn query_inner(&mut self, node: usize, l: usize, r: usize,
                   ql: usize, qr: usize) -> i64 {
        if qr < l || r < ql { return 0; }
        if ql <= l && r <= qr { return self.tree[node]; }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.query_inner(2 * node, l, mid, ql, qr)
            + self.query_inner(2 * node + 1, mid + 1, r, ql, qr)
    }
}

fn main() {
    let arr = vec![1, 3, 2, 7, 9, 11];
    let mut st = LazySegTree::new(&arr);

    println!("sum(1,4) = {}", st.query(1, 4)); // 21
    st.range_add(1, 4, 3);
    println!("After range_add(1,4,3):");
    println!("sum(0,5) = {}", st.query(0, 5)); // 45
    println!("sum(1,4) = {}", st.query(1, 4)); // 33
}
```

---

## 8. Binary Indexed Tree (Fenwick Tree)

### Concept

The **Fenwick Tree** (invented by Peter Fenwick, 1994) achieves the same O(log n) per update and query as a Segment Tree, but with:
- Simpler code (no recursion needed)
- Smaller constant factor (1/2 to 1/3 the memory and operations)
- Less intuitive to understand initially

It is the preferred structure for competitive programming when you need **point update + prefix sum query**.

### The Brilliant Bit Trick

Every positive integer `i` can be written in binary. The **lowest set bit** (LSB) of `i` tells us how many elements the Fenwick node at index `i` is responsible for.

```
i = 6  = 110₂  →  LSB = 2  →  node 6 covers 2 elements: arr[5] and arr[6]
i = 4  = 100₂  →  LSB = 4  →  node 4 covers 4 elements: arr[1]..arr[4]
i = 7  = 111₂  →  LSB = 1  →  node 7 covers 1 element:  arr[7]

How to get LSB: i & (-i)  (two's complement trick)
```

### How BIT Works

`bit[i]` stores the sum of a specific range ending at index `i`.  
The length of that range is `i & (-i)` (the lowest set bit of `i`).

**Prefix sum query** (sum from 1 to i):
- Start at index `i`
- Add `bit[i]`, then move to `i - (i & -i)` (remove the LSB)
- Repeat until `i == 0`

**Update** (add val to arr[pos]):
- Start at index `pos`
- Add val to `bit[pos]`, then move to `pos + (pos & -pos)` (add the LSB)
- Repeat while `pos <= n`

```
Prefix query for i=7: 7 → 6 → 4 → 0
                 bit[7] + bit[6] + bit[4]

Update at pos=3: 3 → 4 → 8 → ...
           update bit[3], bit[4], bit[8], ...
```

### Visual

```
Index:  1    2    3    4    5    6    7    8
BIT:  [1]  [1+3] [2]  [1+3+2+7] [5] [5+9] [2] [1+3+2+7+9+11+2+6]

       = 1    4    2     13      5    14    2       45

Each node's range length = LSB of its index:
  BIT[1]=1: len=1 (covers arr[1])
  BIT[2]=4: len=2 (covers arr[1..2])
  BIT[4]=13: len=4 (covers arr[1..4])
  BIT[8]=45: len=8 (covers arr[1..8])
```

### Time and Space Complexity

| Operation | Complexity |
|-----------|-----------|
| Build (n updates) | O(n log n) or O(n) with clever init |
| Point update | O(log n) |
| Prefix query (1 to i) | O(log n) |
| Range query (l to r) | O(log n) via prefix(r) - prefix(l-1) |
| Space | O(n) |

---

### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAXN 100005

long long bit[MAXN];  /* 1-indexed BIT */
int n;

/* Get lowest set bit */
#define LSB(i) ((i) & (-(i)))

/* Point update: add val to index i (1-indexed): O(log n) */
void update(int i, long long val) {
    for (; i <= n; i += LSB(i))
        bit[i] += val;
}

/* Prefix sum query: sum from 1 to i (1-indexed): O(log n) */
long long prefix(int i) {
    long long s = 0;
    for (; i > 0; i -= LSB(i))
        s += bit[i];
    return s;
}

/* Range sum query [l, r] (1-indexed): O(log n) */
long long range_query(int l, int r) {
    return prefix(r) - prefix(l - 1);
}

/* Build BIT from array in O(n) using the propagation trick */
void build(long long *arr) {
    for (int i = 1; i <= n; i++) {
        bit[i] += arr[i];
        int j = i + LSB(i);
        if (j <= n) bit[j] += bit[i];
    }
}

int main(void) {
    long long arr[] = {0, 1, 3, 2, 7, 9, 11, 2, 6}; /* 1-indexed */
    n = 8;

    memset(bit, 0, sizeof(bit));
    build(arr);

    printf("sum(1,4) = %lld\n", range_query(1, 4)); /* 1+3+2+7=13 */
    printf("sum(1,8) = %lld\n", range_query(1, 8)); /* 41 */

    /* Update: arr[3] += 5 */
    update(3, 5);
    printf("After arr[3] += 5:\n");
    printf("sum(1,4) = %lld\n", range_query(1, 4)); /* 18 */

    return 0;
}
```

---

### Go Implementation

```go
package main

import "fmt"

// BIT is a 1-indexed Fenwick Tree for point-update, prefix-sum queries.
type BIT struct {
	tree []int64
	n    int
}

func NewBIT(n int) *BIT {
	return &BIT{tree: make([]int64, n+1), n: n}
}

// NewBITFromArray builds a BIT from arr (1-indexed) in O(n).
func NewBITFromArray(arr []int64) *BIT {
	n := len(arr) - 1 // arr is 1-indexed, arr[0] unused
	b := NewBIT(n)
	copy(b.tree, arr)
	for i := 1; i <= n; i++ {
		j := i + (i & -i)
		if j <= n {
			b.tree[j] += b.tree[i]
		}
	}
	return b
}

// Update adds val to position i (1-indexed) in O(log n).
func (b *BIT) Update(i int, val int64) {
	for ; i <= b.n; i += i & -i {
		b.tree[i] += val
	}
}

// Prefix returns the sum from 1 to i (1-indexed) in O(log n).
func (b *BIT) Prefix(i int) int64 {
	var s int64
	for ; i > 0; i -= i & -i {
		s += b.tree[i]
	}
	return s
}

// Query returns the sum from l to r (1-indexed) in O(log n).
func (b *BIT) Query(l, r int) int64 {
	return b.Prefix(r) - b.Prefix(l-1)
}

func main() {
	// 1-indexed array: arr[0] unused
	arr := []int64{0, 1, 3, 2, 7, 9, 11, 2, 6}
	b := NewBITFromArray(arr)

	fmt.Println("sum(1,4) =", b.Query(1, 4)) // 13
	fmt.Println("sum(1,8) =", b.Query(1, 8)) // 41

	b.Update(3, 5)
	fmt.Println("After arr[3] += 5:")
	fmt.Println("sum(1,4) =", b.Query(1, 4)) // 18
}
```

---

### Rust Implementation

```rust
/// BIT (Fenwick Tree) — 1-indexed. O(log n) update and prefix query.
struct BIT {
    tree: Vec<i64>,
    n: usize,
}

impl BIT {
    fn new(n: usize) -> Self {
        BIT { tree: vec![0; n + 1], n }
    }

    /// Build from a 1-indexed slice (index 0 unused) in O(n).
    fn from_array(arr: &[i64]) -> Self {
        let n = arr.len() - 1;
        let mut b = BIT { tree: arr.to_vec(), n };
        for i in 1..=n {
            let j = i + (i & i.wrapping_neg());
            if j <= n {
                b.tree[j] += b.tree[i];
            }
        }
        b
    }

    /// Add val to index i (1-indexed) in O(log n).
    fn update(&mut self, mut i: usize, val: i64) {
        while i <= self.n {
            self.tree[i] += val;
            i += i & i.wrapping_neg();
        }
    }

    /// Sum from 1 to i (1-indexed) in O(log n).
    fn prefix(&self, mut i: usize) -> i64 {
        let mut s = 0;
        while i > 0 {
            s += self.tree[i];
            i -= i & i.wrapping_neg();
        }
        s
    }

    /// Sum from l to r (1-indexed) in O(log n).
    fn query(&self, l: usize, r: usize) -> i64 {
        self.prefix(r) - self.prefix(l - 1)
    }
}

fn main() {
    // Index 0 unused; array is 1-indexed.
    let arr = vec![0, 1, 3, 2, 7, 9, 11, 2, 6];
    let mut b = BIT::from_array(&arr);

    println!("sum(1,4) = {}", b.query(1, 4)); // 13
    println!("sum(1,8) = {}", b.query(1, 8)); // 41

    b.update(3, 5);
    println!("After arr[3] += 5:");
    println!("sum(1,4) = {}", b.query(1, 4)); // 18
}
```

---

## 9. Square Root Decomposition

### Concept

**Sqrt decomposition** is a simple but powerful technique: divide the array into blocks of size approximately `√n`. Each block precomputes and stores an aggregate (e.g., sum or min).

```
Array of size n = 9, block size = √9 = 3:

[1  3  2 | 7  9  11 | 2  6  4]
Block 0    Block 1    Block 2
sum=6      sum=27     sum=12
```

**Query [l, r]**:
- Elements in the **partial left block** (from l to end of its block): iterate individually.
- **Complete blocks** in the middle: use precomputed block aggregate.
- Elements in the **partial right block** (from start of block to r): iterate individually.

**Update at pos**:
- Update `arr[pos]`.
- Update the corresponding block's aggregate.

### Time and Space Complexity

| Operation | Complexity |
|-----------|-----------|
| Build | O(n) |
| Query | O(√n) |
| Point update | O(1) |
| Range update | O(√n) |
| Space | O(n) |

> **When to use**: When you need simplicity over log n performance, or when your function is not easily decomposable into a tree structure (like mode, median). Also the base of Mo's Algorithm.

---

### C Implementation

```c
#include <stdio.h>
#include <math.h>

#define MAXN 100005

long long arr[MAXN];
long long block_sum[320]; /* ceil(sqrt(MAXN)) blocks */
int n, block_size;

/* Build blocks: O(n) */
void build(void) {
    block_size = (int)sqrt(n) + 1;
    for (int i = 0; i < n; i++) {
        block_sum[i / block_size] += arr[i];
    }
}

/* Range sum query [l, r] (0-indexed): O(sqrt n) */
long long query(int l, int r) {
    long long result = 0;
    int bl = l / block_size, br = r / block_size;

    if (bl == br) {
        /* l and r are in the same block: iterate directly */
        for (int i = l; i <= r; i++) result += arr[i];
        return result;
    }

    /* Left partial block */
    int left_end = (bl + 1) * block_size - 1;
    for (int i = l; i <= left_end; i++) result += arr[i];

    /* Complete middle blocks */
    for (int b = bl + 1; b < br; b++) result += block_sum[b];

    /* Right partial block */
    int right_start = br * block_size;
    for (int i = right_start; i <= r; i++) result += arr[i];

    return result;
}

/* Point update: set arr[pos] = val, O(1) */
void point_update(int pos, long long val) {
    block_sum[pos / block_size] += val - arr[pos];
    arr[pos] = val;
}

int main(void) {
    long long data[] = {1, 3, 2, 7, 9, 11, 2, 6, 4};
    n = 9;
    for (int i = 0; i < n; i++) arr[i] = data[i];

    build();

    printf("sum(1,7) = %lld\n", query(1, 7)); /* 3+2+7+9+11+2+6=40 */
    printf("sum(0,8) = %lld\n", query(0, 8)); /* 45 */

    point_update(3, 10); /* arr[3] = 10 (was 7) */
    printf("After arr[3]=10:\n");
    printf("sum(0,8) = %lld\n", query(0, 8)); /* 48 */

    return 0;
}
```

---

### Go Implementation

```go
package main

import (
	"fmt"
	"math"
)

// SqrtDecomp provides O(sqrt(n)) range queries and O(1) point updates.
type SqrtDecomp struct {
	arr       []int64
	blockSum  []int64
	blockSize int
	n         int
}

func NewSqrtDecomp(data []int64) *SqrtDecomp {
	n := len(data)
	bs := int(math.Sqrt(float64(n))) + 1
	blocks := (n + bs - 1) / bs
	sd := &SqrtDecomp{
		arr:       make([]int64, n),
		blockSum:  make([]int64, blocks),
		blockSize: bs,
		n:         n,
	}
	copy(sd.arr, data)
	for i, v := range data {
		sd.blockSum[i/bs] += v
	}
	return sd
}

// Query returns sum of arr[l..r] (0-indexed) in O(sqrt n).
func (sd *SqrtDecomp) Query(l, r int) int64 {
	var result int64
	bl, br := l/sd.blockSize, r/sd.blockSize
	if bl == br {
		for i := l; i <= r; i++ {
			result += sd.arr[i]
		}
		return result
	}
	for i := l; i < (bl+1)*sd.blockSize; i++ {
		result += sd.arr[i]
	}
	for b := bl + 1; b < br; b++ {
		result += sd.blockSum[b]
	}
	for i := br * sd.blockSize; i <= r; i++ {
		result += sd.arr[i]
	}
	return result
}

// Update sets arr[pos] = val in O(1).
func (sd *SqrtDecomp) Update(pos int, val int64) {
	sd.blockSum[pos/sd.blockSize] += val - sd.arr[pos]
	sd.arr[pos] = val
}

func main() {
	data := []int64{1, 3, 2, 7, 9, 11, 2, 6, 4}
	sd := NewSqrtDecomp(data)

	fmt.Println("sum(1,7) =", sd.Query(1, 7)) // 40
	fmt.Println("sum(0,8) =", sd.Query(0, 8)) // 45

	sd.Update(3, 10)
	fmt.Println("After arr[3]=10:")
	fmt.Println("sum(0,8) =", sd.Query(0, 8)) // 48
}
```

---

### Rust Implementation

```rust
/// SqrtDecomp — O(sqrt n) range sum queries, O(1) point updates.
struct SqrtDecomp {
    arr: Vec<i64>,
    block_sum: Vec<i64>,
    block_size: usize,
    n: usize,
}

impl SqrtDecomp {
    fn new(data: &[i64]) -> Self {
        let n = data.len();
        let bs = (n as f64).sqrt() as usize + 1;
        let num_blocks = (n + bs - 1) / bs;
        let mut block_sum = vec![0i64; num_blocks];
        for (i, &v) in data.iter().enumerate() {
            block_sum[i / bs] += v;
        }
        SqrtDecomp {
            arr: data.to_vec(),
            block_sum,
            block_size: bs,
            n,
        }
    }

    /// Sum of arr[l..=r] (0-indexed) in O(sqrt n).
    fn query(&self, l: usize, r: usize) -> i64 {
        let (bl, br) = (l / self.block_size, r / self.block_size);
        if bl == br {
            return self.arr[l..=r].iter().sum();
        }
        let left_sum: i64 = self.arr[l..(bl + 1) * self.block_size].iter().sum();
        let mid_sum: i64 = self.block_sum[bl + 1..br].iter().sum();
        let right_sum: i64 = self.arr[br * self.block_size..=r].iter().sum();
        left_sum + mid_sum + right_sum
    }

    /// Set arr[pos] = val in O(1).
    fn update(&mut self, pos: usize, val: i64) {
        self.block_sum[pos / self.block_size] += val - self.arr[pos];
        self.arr[pos] = val;
    }
}

fn main() {
    let data = vec![1, 3, 2, 7, 9, 11, 2, 6, 4];
    let mut sd = SqrtDecomp::new(&data);

    println!("sum(1,7) = {}", sd.query(1, 7)); // 40
    println!("sum(0,8) = {}", sd.query(0, 8)); // 45

    sd.update(3, 10);
    println!("After arr[3]=10:");
    println!("sum(0,8) = {}", sd.query(0, 8)); // 48
}
```

---

## 10. Mo's Algorithm

### Concept

**Mo's Algorithm** is a powerful offline technique for answering range queries in **O((n + Q) × √n)** time for queries that cannot be answered online (i.e., all queries are known in advance).

It is especially useful for queries involving **frequency counts**, **distinct values**, **mode**, or any aggregate that is expensive to recompute from scratch but cheap to update incrementally.

### What "Offline" Means

**Online**: Queries arrive one by one; you must answer each before seeing the next.  
**Offline**: All queries are known upfront; you can reorder them for efficiency.

Mo's algorithm reorders the queries to minimize the total movement of the left and right window pointers.

### The Core Idea

Maintain a sliding window [cur_l, cur_r] over the array.  
To answer query [l, r], move cur_l and cur_r to l and r step by step, updating your data structure as you expand or shrink the window.

**Naive**: Each query is O(n) → total O(n × Q)  
**Mo's**: Reorder queries cleverly → total O((n + Q) × √n)

### Query Ordering

Divide indices into blocks of size `√n`.  
Sort queries by (block of left endpoint, right endpoint):
- If two queries are in the same block, sort by right endpoint (ascending).
- If in different blocks, sort by block number (ascending).

This ensures:
- The right pointer moves at most O(n) per block of queries → O(n × √n) total for right pointer.
- The left pointer moves at most O(√n) per query → O(Q × √n) total.

### Template

```
Sort queries.
cur_l = 0, cur_r = -1 (empty window initially)
For each query [l, r]:
    while cur_r < r: cur_r++; add arr[cur_r]
    while cur_l > l: cur_l--; add arr[cur_l]
    while cur_r > r: remove arr[cur_r]; cur_r--
    while cur_l < l: remove arr[cur_l]; cur_l++
    answer = current state of your data structure
```

> **Order matters!** Always expand before shrinking to avoid going below an empty window.

---

### C Implementation — Count distinct elements in range

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#define MAXN 100005
#define MAXV 100005   /* value range */

int arr[MAXN];
int cnt[MAXV];        /* count of each value in current window */
int cur_distinct;     /* number of distinct values in window */
int n, q;
int block_size;

typedef struct {
    int l, r, idx;
} Query;

Query queries[MAXN];
int answers[MAXN];

int cmp_query(const void *a, const void *b) {
    const Query *qa = (Query *)a;
    const Query *qb = (Query *)b;
    int ba = qa->l / block_size;
    int bb = qb->l / block_size;
    if (ba != bb) return ba - bb;
    /* Same block: sort by r. Alternate direction for even/odd blocks (optimization) */
    return (ba & 1) ? (qb->r - qa->r) : (qa->r - qb->r);
}

void add(int val) {
    if (cnt[val] == 0) cur_distinct++;
    cnt[val]++;
}

void remove_val(int val) {
    cnt[val]--;
    if (cnt[val] == 0) cur_distinct--;
}

int main(void) {
    n = 8;
    int data[] = {1, 3, 2, 1, 5, 3, 2, 1};
    for (int i = 0; i < n; i++) arr[i] = data[i];

    /* Example queries: [0,3], [2,6], [0,7] */
    q = 3;
    int ql[] = {0, 2, 0};
    int qr[] = {3, 6, 7};
    for (int i = 0; i < q; i++) {
        queries[i] = (Query){ql[i], qr[i], i};
    }

    block_size = (int)sqrt(n) + 1;
    qsort(queries, q, sizeof(Query), cmp_query);

    memset(cnt, 0, sizeof(cnt));
    cur_distinct = 0;

    int cur_l = 0, cur_r = -1;
    for (int i = 0; i < q; i++) {
        int l = queries[i].l, r = queries[i].r;
        while (cur_r < r) { cur_r++; add(arr[cur_r]); }
        while (cur_l > l) { cur_l--; add(arr[cur_l]); }
        while (cur_r > r) { remove_val(arr[cur_r]); cur_r--; }
        while (cur_l < l) { remove_val(arr[cur_l]); cur_l++; }
        answers[queries[i].idx] = cur_distinct;
    }

    for (int i = 0; i < q; i++) {
        printf("Distinct in [%d,%d] = %d\n", ql[i], qr[i], answers[i]);
    }
    return 0;
}
```

---

### Go Implementation

```go
package main

import (
	"fmt"
	"math"
	"sort"
)

type Query struct {
	l, r, idx int
}

// MoQuery answers "count of distinct elements in [l,r]" for all queries
// offline using Mo's algorithm in O((n+Q)*sqrt(n)).
func MoQuery(arr []int, queries []Query) []int {
	n := len(arr)
	blockSize := int(math.Sqrt(float64(n))) + 1

	sort.Slice(queries, func(i, j int) bool {
		bi, bj := queries[i].l/blockSize, queries[j].l/blockSize
		if bi != bj {
			return bi < bj
		}
		if bi%2 == 0 {
			return queries[i].r < queries[j].r
		}
		return queries[i].r > queries[j].r
	})

	maxVal := 0
	for _, v := range arr {
		if v > maxVal {
			maxVal = v
		}
	}
	cnt := make([]int, maxVal+1)
	distinct := 0

	addVal := func(v int) {
		if cnt[v] == 0 {
			distinct++
		}
		cnt[v]++
	}
	removeVal := func(v int) {
		cnt[v]--
		if cnt[v] == 0 {
			distinct--
		}
	}

	answers := make([]int, len(queries))
	curL, curR := 0, -1

	for _, q := range queries {
		for curR < q.r {
			curR++
			addVal(arr[curR])
		}
		for curL > q.l {
			curL--
			addVal(arr[curL])
		}
		for curR > q.r {
			removeVal(arr[curR])
			curR--
		}
		for curL < q.l {
			removeVal(arr[curL])
			curL++
		}
		answers[q.idx] = distinct
	}
	return answers
}

func main() {
	arr := []int{1, 3, 2, 1, 5, 3, 2, 1}
	queries := []Query{
		{0, 3, 0},
		{2, 6, 1},
		{0, 7, 2},
	}
	answers := MoQuery(arr, queries)
	for i, q := range []struct{ l, r int }{{0, 3}, {2, 6}, {0, 7}} {
		fmt.Printf("Distinct in [%d,%d] = %d\n", q.l, q.r, answers[i])
	}
}
```

---

### Rust Implementation

```rust
fn mo_query(arr: &[usize], queries: &[(usize, usize)]) -> Vec<usize> {
    let n = arr.len();
    let block_size = (n as f64).sqrt() as usize + 1;

    let max_val = *arr.iter().max().unwrap_or(&0);
    let mut cnt = vec![0usize; max_val + 1];
    let mut distinct = 0usize;

    let mut indexed: Vec<(usize, usize, usize)> = queries
        .iter()
        .enumerate()
        .map(|(i, &(l, r))| (l, r, i))
        .collect();

    indexed.sort_unstable_by(|&(la, ra, _), &(lb, rb, _)| {
        let ba = la / block_size;
        let bb = lb / block_size;
        if ba != bb {
            return ba.cmp(&bb);
        }
        if ba % 2 == 0 { ra.cmp(&rb) } else { rb.cmp(&ra) }
    });

    let mut add = |v: usize| {
        if cnt[v] == 0 { distinct += 1; }
        cnt[v] += 1;
    };
    let mut remove = |v: usize| {
        cnt[v] -= 1;
        if cnt[v] == 0 { distinct -= 1; }
    };

    let mut answers = vec![0usize; queries.len()];
    let (mut cur_l, mut cur_r) = (0usize, 0usize);
    // Start with window [0, 0) — we need to handle isize-like logic via early expansion.
    let mut started = false;

    for &(l, r, idx) in &indexed {
        if !started {
            // Initialize with the first element
            add(arr[0]);
            started = true;
        }
        while cur_r < r { cur_r += 1; add(arr[cur_r]); }
        while cur_l > l { cur_l -= 1; add(arr[cur_l]); }
        while cur_r > r { remove(arr[cur_r]); cur_r -= 1; }
        while cur_l < l { remove(arr[cur_l]); cur_l += 1; }
        answers[idx] = distinct;
    }
    answers
}

fn main() {
    let arr = vec![1, 3, 2, 1, 5, 3, 2, 1];
    let queries = vec![(0, 3), (2, 6), (0, 7)];
    let answers = mo_query(&arr, &queries);

    let labels = [(0, 3), (2, 6), (0, 7)];
    for (i, &(l, r)) in labels.iter().enumerate() {
        println!("Distinct in [{},{}] = {}", l, r, answers[i]);
    }
}
```

---

## 11. Choosing the Right Structure

### Decision Flow

```
Does the array change (updates)?
  NO → Is the function idempotent (min, max, gcd)?
          YES → Sparse Table: O(n log n) build, O(1) query
          NO  → Prefix Sum: O(n) build, O(1) query
  YES → What kind of updates?
          Point update + range query:
              Simple code OK? → Fenwick Tree (BIT)
              Need max/min?   → Segment Tree
          Range update + range query:
              → Segment Tree with Lazy Propagation
          Range update + point query:
              → Difference Array (then reconstruct)
          Complex query (mode, distinct, etc.) + offline?
              → Mo's Algorithm
          Simplicity + medium n?
              → Sqrt Decomposition
```

### Summary Table

| Structure | Build | Point Update | Range Update | Range Query | Static? |
|-----------|-------|-------------|-------------|-------------|---------|
| Prefix Sum 1D | O(n) | — | — | O(1) sum | Yes |
| Prefix Sum 2D | O(nm) | — | — | O(1) rect sum | Yes |
| Difference Array | O(n) | O(1) | O(1) | O(n) reconstruct | Batch |
| Sparse Table | O(n log n) | — | — | O(1) RMQ | Yes |
| Segment Tree | O(n) | O(log n) | — | O(log n) | No |
| Lazy Seg Tree | O(n) | O(log n) | O(log n) | O(log n) | No |
| Fenwick Tree | O(n) | O(log n) | — | O(log n) prefix | No |
| Sqrt Decomp | O(n) | O(1) | O(√n) | O(√n) | No |
| Mo's Algorithm | — | — | — | O((n+Q)√n) | Offline |

---

## 12. Complexity Cheat Sheet

```
n = 10^5 elements, Q = 10^5 queries

Structure         Build         Query         Update
─────────────────────────────────────────────────────
Prefix Sum       0.1 ms        instant        N/A
Sparse Table     1.7 ms        instant        N/A
Segment Tree     0.3 ms        17 ops         17 ops
Lazy Seg Tree    0.3 ms        17 ops         17 ops
Fenwick Tree     1.7 ms        17 ops         17 ops
Sqrt Decomp      0.1 ms       316 ops          1 op
Mo's Algorithm   N/A      (n+Q)*√n = 6.3×10^7 total

Naïve Array      0.1 ms       10^5 ops       1 op

Key insight: log2(10^5) ≈ 17,  sqrt(10^5) ≈ 316
So log n is ~18x faster than sqrt n for queries.
Use sqrt/Mo only when the function is hard to encode in a tree.
```

---

## Deep Expert Mental Models

### 1. The "Coverage" Mental Model for Segment Trees

A query [l, r] is answered by identifying a minimal set of segment tree nodes that together cover [l, r] exactly with no overlaps. This set has at most `4 log n` nodes. The key insight: at each level of the tree, at most 2 nodes can be "partially" inside the query range — all others are either fully inside (directly returned) or fully outside (immediately pruned). This is why the complexity is O(log n) and not O(n).

### 2. The "Lazy = Unpaid Debt" Mental Model

Every lazy tag is a deferred operation. When you travel down a path from root to leaf, you pay all the accumulated debt you encounter. The guarantee is: **a node's tree value is always correct given that all lazy tags above it have been applied**. The moment you need to look at a node's children, you first pay the debt (push down), restoring the invariant.

### 3. BIT as "Responsibility Intervals"

Each BIT index `i` is "responsible" for the sum of exactly `LSB(i)` elements. When you update index `i`, you need to notify all indices responsible for ranges that contain `i`. These are exactly `i, i + LSB(i), i + LSB(i + LSB(i)), ...`. When you query prefix(i), you walk down the responsibility chain: `i, i - LSB(i), i - LSB(i - LSB(i)), ...`. The elegance: these two traversals are mirrors of each other, and they visit at most `log n` nodes.

### 4. Mo's Algorithm as "Minimizing Taxi Distance"

Think of each query as a taxi ride from (cur_l, cur_r) to (l, r) in 2D space. Mo's algorithm sorts queries so the total Manhattan distance traveled is minimized. The block decomposition turns an O(n × Q) naive strategy into O((n + Q) × √n) — the classic time/space tradeoff at the level of query ordering.

---

*End of Guide — Range Queries: Complete Deep-Dive*

Here is your complete Range Queries guide. Here's a high-level map of everything inside:

---

**What's Covered (10 Structures, 3 Languages Each)**

| # | Structure | Superpower |
|---|-----------|-----------|
| 1 | Prefix Sum 1D | Static range sum in O(1) |
| 2 | Prefix Sum 2D | Static rectangle sum in O(1) |
| 3 | Difference Array | Range update in O(1), reconstruct once |
| 4 | Sparse Table | Static RMQ in O(1) via idempotent overlap |
| 5 | Segment Tree | Range query + point update in O(log n) |
| 6 | Lazy Segment Tree | Range update + range query in O(log n) |
| 7 | Fenwick / BIT | Simpler + faster constant than seg tree for prefix sum |
| 8 | Sqrt Decomposition | O(√n) universal fallback, simplest code |
| 9 | Mo's Algorithm | Offline distinct/frequency queries in O((n+Q)√n) |

---

**Key Takeaways to Internalize**

- **Prefix Sum** → your first instinct for static sum problems. O(1) query after O(n) build.
- **Difference Array** → the inverse of prefix sum. Think "range update, then read once."
- **Sparse Table** → the only O(1) query structure, but idempotent functions only (min, max, gcd).
- **Segment Tree** → the universal workhorse. Master this deeply before Mo's.
- **Lazy propagation** is not an extension — it's a mental model: *defer work, pay when needed.*
- **BIT** = Segment Tree's lean twin. Same O(log n), half the code, elegant bit manipulation.
- **Mo's** = reorder queries to minimize window movement. Think 2D taxi distance minimization.

The guide also ends with **4 expert mental models** that will rewire how you reason about these structures — especially the "Lazy = Unpaid Debt" and "BIT as Responsibility Intervals" framings. These are the kind of abstractions that separate people who memorize code from people who derive it.