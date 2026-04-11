# Complete Guide: Intervals and Segments of an Array
## From Fundamentals to Mastery — DSA Deep Dive

---

## Table of Contents

1. [What Is an Interval / Segment?](#1-what-is-an-interval--segment)
2. [Core Vocabulary and Mental Models](#2-core-vocabulary-and-mental-models)
3. [Brute Force Range Queries](#3-brute-force-range-queries)
4. [Prefix Sum Array](#4-prefix-sum-array)
5. [Difference Array](#5-difference-array)
6. [Sparse Table (Range Minimum / Maximum Query)](#6-sparse-table-range-minimum--maximum-query)
7. [Segment Tree — Point Update, Range Query](#7-segment-tree--point-update-range-query)
8. [Segment Tree — Range Update with Lazy Propagation](#8-segment-tree--range-update-with-lazy-propagation)
9. [Fenwick Tree (Binary Indexed Tree / BIT)](#9-fenwick-tree-binary-indexed-tree--bit)
10. [Interval Merging](#10-interval-merging)
11. [Sweep Line Algorithm](#11-sweep-line-algorithm)
12. [Two-Pointer / Sliding Window on Intervals](#12-two-pointer--sliding-window-on-intervals)
13. [Comparative Analysis and When to Use What](#13-comparative-analysis-and-when-to-use-what)
14. [Classic Problems and Patterns](#14-classic-problems-and-patterns)
15. [Psychological and Cognitive Mastery Notes](#15-psychological-and-cognitive-mastery-notes)

---

## 1. What Is an Interval / Segment?

### Definition

An **interval** (also called a **segment** or **range**) in the context of arrays is a **contiguous subarray** defined by two indices:

```
Array A = [ 3, 1, 4, 1, 5, 9, 2, 6 ]
           index: 0  1  2  3  4  5  6  7

Interval [2, 5] = A[2..5] = [ 4, 1, 5, 9 ]
                              ^^^^^^^^^^^^
                              L=2        R=5
```

- **L** = Left boundary (inclusive)
- **R** = Right boundary (inclusive)
- **Length** of interval = R - L + 1

### Why Intervals Matter

Almost every non-trivial array problem reduces to some **range operation**:

```
Query Types:
┌────────────────────────────────────────────────────────────────┐
│  Range Sum Query    → What is A[L] + A[L+1] + ... + A[R]?    │
│  Range Min Query    → What is min(A[L..R])?                   │
│  Range Max Query    → What is max(A[L..R])?                   │
│  Range GCD Query    → What is gcd(A[L..R])?                   │
│  Range Update       → Add X to every element in A[L..R]       │
│  Range Assignment   → Set every element in A[L..R] to X       │
└────────────────────────────────────────────────────────────────┘
```

The entire subject is about: **"How do we answer these queries FAST, even after updates?"**

---

## 2. Core Vocabulary and Mental Models

Before going deeper, understand these terms precisely:

### 2.1 Key Terms

| Term | Meaning |
|------|---------|
| **Query** | A question asked about a range, e.g., sum of A[2..7] |
| **Update** | A modification to the array, e.g., A[3] += 5 |
| **Point Update** | Change exactly one element |
| **Range Update** | Change all elements in a range [L, R] |
| **Offline** | All queries known in advance |
| **Online** | Queries arrive one by one, must be answered immediately |
| **Idempotent** | f(f(x)) = f(x) — e.g., min, max (used in sparse tables) |
| **Associative** | f(f(a,b), c) = f(a, f(b,c)) — required for segment trees |
| **Prefix** | From index 0 to some index i |
| **Suffix** | From some index i to the last index |
| **Subarray** | Any contiguous slice of the array |

### 2.2 The Core Mental Model

Think of range queries as building a **hierarchy of answers**:

```
Array:    [ 1,  3,  2,  7,  4,  5,  8,  6 ]
           \_______/  \_______/  \_______/   <- small blocks
           \_________________/               <- medium blocks
           \_________________________________/ <- whole array
```

The key insight is: **precompute answers for sub-problems so that any range query = combine a few precomputed answers**.

### 2.3 Decision Tree: Which Tool to Use?

```
Is the array STATIC (no updates)?
│
├─ YES ──► Do you need OVERLAPPING ranges (like RMQ)?
│          ├─ YES ──► Sparse Table  (O(1) query, O(n log n) build)
│          └─ NO  ──► Prefix Sum    (O(1) query, O(n) build)
│
└─ NO (updates exist)
   │
   ├─ Point updates + Range queries?
   │   ├─ Sum only?  ──► Fenwick Tree (BIT) — simpler
   │   └─ Any assoc. function? ──► Segment Tree
   │
   └─ Range updates + Range queries?
       └─ Segment Tree with Lazy Propagation
```

---

## 3. Brute Force Range Queries

### Concept

For every query (L, R), just loop through A[L..R] and compute.

```
Time:  O(n) per query
Space: O(1)
```

```
Query: sum(A[2..5])

i=2: sum = 4
i=3: sum = 4+1 = 5
i=4: sum = 5+5 = 10
i=5: sum = 10+9 = 19

Answer = 19
```

### When it fails

If you have Q queries each over range of size n → **O(n×Q)** total.
For n=100000 and Q=100000 → 10^10 operations → **Too Slow**.

### C Implementation

```c
#include <stdio.h>

int range_sum_brute(int *arr, int L, int R) {
    int sum = 0;
    for (int i = L; i <= R; i++) {
        sum += arr[i];
    }
    return sum;
}

int range_min_brute(int *arr, int L, int R) {
    int mn = arr[L];
    for (int i = L + 1; i <= R; i++) {
        if (arr[i] < mn) mn = arr[i];
    }
    return mn;
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = 8;
    printf("Sum [2,5] = %d\n", range_sum_brute(arr, 2, 5)); // 19
    printf("Min [0,4] = %d\n", range_min_brute(arr, 0, 4)); // 1
    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

func rangeSumBrute(arr []int, L, R int) int {
    sum := 0
    for i := L; i <= R; i++ {
        sum += arr[i]
    }
    return sum
}

func rangeMinBrute(arr []int, L, R int) int {
    mn := arr[L]
    for i := L + 1; i <= R; i++ {
        if arr[i] < mn {
            mn = arr[i]
        }
    }
    return mn
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    fmt.Println("Sum [2,5] =", rangeSumBrute(arr, 2, 5)) // 19
    fmt.Println("Min [0,4] =", rangeMinBrute(arr, 0, 4)) // 1
}
```

### Rust Implementation

```rust
fn range_sum_brute(arr: &[i64], l: usize, r: usize) -> i64 {
    arr[l..=r].iter().sum()
}

fn range_min_brute(arr: &[i64], l: usize, r: usize) -> i64 {
    *arr[l..=r].iter().min().unwrap()
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    println!("Sum [2,5] = {}", range_sum_brute(&arr, 2, 5)); // 19
    println!("Min [0,4] = {}", range_min_brute(&arr, 0, 4)); // 1
}
```

---

## 4. Prefix Sum Array

### Concept

**Prefix Sum** (also called **cumulative sum**) is one of the most powerful and elegant tools in DSA.

#### What is a Prefix?
A **prefix** of an array is any subarray starting from index 0:
- Prefix of length 1: A[0]
- Prefix of length 3: A[0], A[1], A[2]

#### The Key Insight

```
Define:  prefix[i] = A[0] + A[1] + ... + A[i]

Then:    sum(A[L..R]) = prefix[R] - prefix[L-1]
```

**Why?** Because `prefix[R]` contains the sum of everything from 0 to R.
`prefix[L-1]` contains the sum from 0 to L-1.
Subtracting cancels out the part before L, leaving only L to R.

```
Array:      [ 3,  1,  4,  1,  5,  9,  2,  6 ]
Index:        0   1   2   3   4   5   6   7

Prefix[0] = 3
Prefix[1] = 3+1 = 4
Prefix[2] = 4+4 = 8
Prefix[3] = 8+1 = 9
Prefix[4] = 9+5 = 14
Prefix[5] = 14+9 = 23
Prefix[6] = 23+2 = 25
Prefix[7] = 25+6 = 31

Prefix: [ 3,  4,  8,  9, 14, 23, 25, 31 ]

Query sum(A[2..5]):
= Prefix[5] - Prefix[1]    (Prefix[L-1] = Prefix[2-1] = Prefix[1])
= 23 - 4
= 19  ✓

Check: A[2]+A[3]+A[4]+A[5] = 4+1+5+9 = 19 ✓
```

### Complexity

```
Build:  O(n)
Query:  O(1)
Update: O(n)  ← This is the weakness! Prefix sum doesn't support fast updates.
```

### Algorithm Flow

```
BUILD PHASE:
┌─────────┐
│ i = 0   │
└────┬────┘
     │
     ▼
┌─────────────────────────────────┐
│ prefix[i] = A[i] + prefix[i-1] │ ◄─── (use 0 if i=0)
└────────────────┬────────────────┘
                 │
                 ▼
           ┌──────────┐
           │ i == n-1?│──YES──► Done
           └────┬─────┘
                │ NO
                ▼
              i = i+1
              (loop back)

QUERY PHASE (L, R):
┌────────────────────────────────────┐
│ if L == 0:                        │
│   return prefix[R]                │
│ else:                             │
│   return prefix[R] - prefix[L-1]  │
└────────────────────────────────────┘
```

### Handling the L=0 edge case

A common trick is to make the prefix array **1-indexed** (shift by 1), so prefix[0] = 0:

```
prefix[0] = 0 (sentinel)
prefix[i] = A[i-1] + prefix[i-1]   for i from 1 to n

Query sum(A[L..R]):       (0-indexed L, R)
= prefix[R+1] - prefix[L]
```

This eliminates the L=0 special case entirely.

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    long long *prefix;
    int n;
} PrefixSum;

// Build with 1-indexed prefix (prefix[0]=0)
PrefixSum* prefix_build(int *arr, int n) {
    PrefixSum *ps = malloc(sizeof(PrefixSum));
    ps->n = n;
    ps->prefix = calloc(n + 1, sizeof(long long));
    for (int i = 1; i <= n; i++) {
        ps->prefix[i] = ps->prefix[i-1] + arr[i-1];
    }
    return ps;
}

// Query sum of A[L..R] (0-indexed)
long long prefix_query(PrefixSum *ps, int L, int R) {
    return ps->prefix[R+1] - ps->prefix[L];
}

void prefix_free(PrefixSum *ps) {
    free(ps->prefix);
    free(ps);
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = 8;

    PrefixSum *ps = prefix_build(arr, n);

    printf("Sum [2,5] = %lld\n", prefix_query(ps, 2, 5)); // 19
    printf("Sum [0,7] = %lld\n", prefix_query(ps, 0, 7)); // 31
    printf("Sum [0,0] = %lld\n", prefix_query(ps, 0, 0)); // 3

    prefix_free(ps);
    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type PrefixSum struct {
    prefix []int64
    n      int
}

func NewPrefixSum(arr []int) *PrefixSum {
    n := len(arr)
    prefix := make([]int64, n+1)
    for i := 1; i <= n; i++ {
        prefix[i] = prefix[i-1] + int64(arr[i-1])
    }
    return &PrefixSum{prefix: prefix, n: n}
}

// Query returns sum of arr[L..R] (0-indexed, inclusive)
func (ps *PrefixSum) Query(L, R int) int64 {
    return ps.prefix[R+1] - ps.prefix[L]
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    ps := NewPrefixSum(arr)

    fmt.Println("Sum [2,5] =", ps.Query(2, 5)) // 19
    fmt.Println("Sum [0,7] =", ps.Query(0, 7)) // 31
    fmt.Println("Sum [0,0] =", ps.Query(0, 0)) // 3
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

    // Query sum of arr[l..=r] (0-indexed, inclusive)
    fn query(&self, l: usize, r: usize) -> i64 {
        self.prefix[r + 1] - self.prefix[l]
    }
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    let ps = PrefixSum::new(&arr);

    println!("Sum [2,5] = {}", ps.query(2, 5)); // 19
    println!("Sum [0,7] = {}", ps.query(0, 7)); // 31
    println!("Sum [0,0] = {}", ps.query(0, 0)); // 3
}
```

### 2D Prefix Sum

The idea extends beautifully to 2D grids (matrices):

```
prefix2D[i][j] = sum of all elements in rectangle (0,0) to (i,j)

prefix2D[i][j] = A[i][j]
               + prefix2D[i-1][j]
               + prefix2D[i][j-1]
               - prefix2D[i-1][j-1]   ← subtract double-counted corner

Query sum(rectangle (r1,c1) to (r2,c2)):
= prefix2D[r2][c2]
  - prefix2D[r1-1][c2]
  - prefix2D[r2][c1-1]
  + prefix2D[r1-1][c1-1]
```

```
Inclusion-Exclusion Visualization:

    c1       c2
r1  ┌────────┐
    │  WANT  │
r2  └────────┘

prefix[r2][c2]     = everything from (0,0) to (r2,c2)
prefix[r1-1][c2]   = top strip (subtract)
prefix[r2][c1-1]   = left strip (subtract)
prefix[r1-1][c1-1] = top-left corner (was subtracted twice, add back)
```

---

## 5. Difference Array

### Concept

The **Difference Array** is the dual of the prefix sum — it is designed for **range updates** on a static-query scenario.

#### The Problem It Solves

> Given an array, perform Q updates each of the form "add X to every element from L to R", then answer point queries.

With brute force: each update is O(n) → O(n×Q) total.
With difference array: each update is O(1) → O(n + Q) total.

#### What is a Difference Array?

```
Define: D[i] = A[i] - A[i-1]     for i > 0
        D[0] = A[0]

Then:   A[i] = D[0] + D[1] + ... + D[i]   (prefix sum of D = original A)
```

```
Array A:     [ 3,  1,  4,  1,  5,  9,  2,  6 ]

D[0] = A[0]              = 3
D[1] = A[1]-A[0] = 1-3   = -2
D[2] = A[2]-A[1] = 4-1   = 3
D[3] = A[3]-A[2] = 1-4   = -3
D[4] = A[4]-A[3] = 5-1   = 4
D[5] = A[5]-A[4] = 9-5   = 4
D[6] = A[6]-A[5] = 2-9   = -7
D[7] = A[7]-A[6] = 6-2   = 4

Diff:  [ 3, -2,  3, -3,  4,  4, -7,  4 ]
```

#### The Key Trick: Range Update in O(1)

To add X to A[L..R]:

```
D[L]   += X        ← "start the increase at L"
D[R+1] -= X        ← "stop the increase after R"
```

**Why does this work?**

When you take the prefix sum of D to recover A:
- At index L: the +X accumulates forward → all elements from L onward get +X
- At index R+1: the -X cancels it → all elements after R are unaffected

```
Example: Add 5 to A[2..4]

Before:  D = [ 3, -2,  3, -3,  4,  4, -7,  4 ]
Operation: D[2] += 5  →  D[2] = 8
           D[5] -= 5  →  D[5] = -1

After:   D = [ 3, -2,  8, -3,  4, -1, -7,  4 ]

Recover: prefix sum of D:
A[0] = 3
A[1] = 3 + (-2) = 1
A[2] = 1 + 8    = 9   (was 4, now 4+5 = 9) ✓
A[3] = 9 + (-3) = 6   (was 1, now 1+5 = 6) ✓
A[4] = 6 + 4    = 10  (was 5, now 5+5 = 10) ✓
A[5] = 10 + (-1) = 9  (was 9, unchanged) ✓
A[6] = 9 + (-7) = 2   (unchanged) ✓
A[7] = 2 + 4    = 6   (unchanged) ✓
```

### Algorithm Flow

```
RANGE UPDATE ADD(L, R, X):
┌────────────────────────────┐
│ D[L]   += X               │
│ if R+1 < n: D[R+1] -= X  │
└────────────────────────────┘

RECONSTRUCT:
┌──────────────────────────────────────┐
│ A[0] = D[0]                         │
│ for i = 1 to n-1:                   │
│   A[i] = A[i-1] + D[i]             │
└──────────────────────────────────────┘
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    long long *diff;
    int n;
} DiffArray;

DiffArray* diff_build(int *arr, int n) {
    DiffArray *da = malloc(sizeof(DiffArray));
    da->n = n;
    da->diff = calloc(n + 1, sizeof(long long)); // +1 for D[R+1] edge
    da->diff[0] = arr[0];
    for (int i = 1; i < n; i++) {
        da->diff[i] = arr[i] - arr[i-1];
    }
    return da;
}

// Add X to arr[L..R] (0-indexed)
void diff_range_add(DiffArray *da, int L, int R, long long X) {
    da->diff[L] += X;
    if (R + 1 < da->n) da->diff[R + 1] -= X;
}

// Reconstruct the array after all updates
void diff_reconstruct(DiffArray *da, long long *out) {
    out[0] = da->diff[0];
    for (int i = 1; i < da->n; i++) {
        out[i] = out[i-1] + da->diff[i];
    }
}

void diff_free(DiffArray *da) {
    free(da->diff);
    free(da);
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = 8;

    DiffArray *da = diff_build(arr, n);
    diff_range_add(da, 2, 4, 5);   // Add 5 to [2..4]
    diff_range_add(da, 0, 3, -1);  // Subtract 1 from [0..3]

    long long out[8];
    diff_reconstruct(da, out);

    for (int i = 0; i < n; i++) {
        printf("A[%d] = %lld\n", i, out[i]);
    }
    diff_free(da);
    return 0;
}
```

### Go Implementation

```go
package main

import "fmt"

type DiffArray struct {
    diff []int64
    n    int
}

func NewDiffArray(arr []int) *DiffArray {
    n := len(arr)
    diff := make([]int64, n+1)
    diff[0] = int64(arr[0])
    for i := 1; i < n; i++ {
        diff[i] = int64(arr[i]) - int64(arr[i-1])
    }
    return &DiffArray{diff: diff, n: n}
}

func (da *DiffArray) RangeAdd(L, R int, X int64) {
    da.diff[L] += X
    if R+1 < da.n {
        da.diff[R+1] -= X
    }
}

func (da *DiffArray) Reconstruct() []int64 {
    out := make([]int64, da.n)
    out[0] = da.diff[0]
    for i := 1; i < da.n; i++ {
        out[i] = out[i-1] + da.diff[i]
    }
    return out
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    da := NewDiffArray(arr)
    da.RangeAdd(2, 4, 5)
    da.RangeAdd(0, 3, -1)

    result := da.Reconstruct()
    for i, v := range result {
        fmt.Printf("A[%d] = %d\n", i, v)
    }
}
```

### Rust Implementation

```rust
struct DiffArray {
    diff: Vec<i64>,
    n: usize,
}

impl DiffArray {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut diff = vec![0i64; n + 1];
        diff[0] = arr[0];
        for i in 1..n {
            diff[i] = arr[i] - arr[i - 1];
        }
        DiffArray { diff, n }
    }

    fn range_add(&mut self, l: usize, r: usize, x: i64) {
        self.diff[l] += x;
        if r + 1 < self.n {
            self.diff[r + 1] -= x;
        }
    }

    fn reconstruct(&self) -> Vec<i64> {
        let mut out = vec![0i64; self.n];
        out[0] = self.diff[0];
        for i in 1..self.n {
            out[i] = out[i - 1] + self.diff[i];
        }
        out
    }
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    let mut da = DiffArray::new(&arr);
    da.range_add(2, 4, 5);
    da.range_add(0, 3, -1);

    let result = da.reconstruct();
    for (i, v) in result.iter().enumerate() {
        println!("A[{}] = {}", i, v);
    }
}
```

---

## 6. Sparse Table (Range Minimum / Maximum Query)

### Concept

A **Sparse Table** is a data structure that answers **static range minimum/maximum queries in O(1)** after O(n log n) preprocessing.

#### What is "Sparse"?

The table stores answers for ranges of sizes that are **powers of 2**: 1, 2, 4, 8, 16...

This is "sparse" because we skip most range sizes — only powers of 2.

#### What is "Idempotent"?

An operation is **idempotent** if applying it twice gives the same result:
- `min(min(a,b), min(b,c))` → the duplicated `b` doesn't change the minimum
- Same for `max`, `gcd`

This property allows overlapping ranges in O(1) queries.

#### The Precomputation

```
Define: table[i][j] = minimum of A[i .. i + 2^j - 1]
                      (range starting at i with length 2^j)

Base case: table[i][0] = A[i]   (range of length 1)

Recurrence:
table[i][j] = min(table[i][j-1], table[i + 2^(j-1)][j-1])

               |____first half___|  |____second half____|
               length 2^(j-1)       length 2^(j-1)
```

```
Example: A = [3, 1, 4, 1, 5, 9, 2, 6]

j=0 (length 1): table[i][0] = A[i]
table[0][0]=3, table[1][0]=1, table[2][0]=4, table[3][0]=1,
table[4][0]=5, table[5][0]=9, table[6][0]=2, table[7][0]=6

j=1 (length 2):
table[0][1] = min(table[0][0], table[1][0]) = min(3,1) = 1
table[1][1] = min(table[1][0], table[2][0]) = min(1,4) = 1
table[2][1] = min(table[2][0], table[3][0]) = min(4,1) = 1
table[3][1] = min(table[3][0], table[4][0]) = min(1,5) = 1
table[4][1] = min(table[4][0], table[5][0]) = min(5,9) = 5
table[5][1] = min(table[5][0], table[6][0]) = min(9,2) = 2
table[6][1] = min(table[6][0], table[7][0]) = min(2,6) = 2

j=2 (length 4):
table[0][2] = min(table[0][1], table[2][1]) = min(1,1) = 1
table[1][2] = min(table[1][1], table[3][1]) = min(1,1) = 1
...
```

#### The Query

For range [L, R]:

```
length = R - L + 1
k = floor(log2(length))   ← largest power of 2 that fits in the range

answer = min(table[L][k], table[R - 2^k + 1][k])
         |___left coverage___|  |___right coverage___|
```

The two ranges OVERLAP, but that's OK because min is idempotent!

```
Example: min(A[1..5])  →  L=1, R=5, length=5

k = floor(log2(5)) = 2   →   2^k = 4

Left:  table[1][2] = min(A[1..4]) = 1
Right: table[5-4+1][2] = table[2][2] = min(A[2..5]) = 1

answer = min(1, 1) = 1  ✓ (actual min of [1,4,1,5] = 1)
```

### Algorithm Flow

```
BUILD:
for i from 0 to n-1:
    table[i][0] = A[i]

for j from 1 to LOG:
    for i from 0 to n - 2^j:
        table[i][j] = min(table[i][j-1],
                          table[i + 2^(j-1)][j-1])

QUERY(L, R):
k = floor(log2(R - L + 1))
return min(table[L][k], table[R - (1<<k) + 1][k])
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define MAXN 100005
#define LOG  17

int sparse[MAXN][LOG];
int log2_table[MAXN];

int min(int a, int b) { return a < b ? a : b; }

void build(int *arr, int n) {
    // Precompute log2 values
    log2_table[1] = 0;
    for (int i = 2; i <= n; i++) {
        log2_table[i] = log2_table[i / 2] + 1;
    }

    for (int i = 0; i < n; i++) {
        sparse[i][0] = arr[i];
    }
    for (int j = 1; (1 << j) <= n; j++) {
        for (int i = 0; i + (1 << j) - 1 < n; i++) {
            sparse[i][j] = min(sparse[i][j-1],
                               sparse[i + (1 << (j-1))][j-1]);
        }
    }
}

int query_min(int L, int R) {
    int k = log2_table[R - L + 1];
    return min(sparse[L][k], sparse[R - (1 << k) + 1][k]);
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = 8;
    build(arr, n);

    printf("Min [1,5] = %d\n", query_min(1, 5)); // 1
    printf("Min [4,7] = %d\n", query_min(4, 7)); // 2
    printf("Min [0,7] = %d\n", query_min(0, 7)); // 1
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
    logTable [100005]int
    n        int
}

func minInt(a, b int) int {
    if a < b {
        return a
    }
    return b
}

func NewSparseTable(arr []int) *SparseTable {
    st := &SparseTable{n: len(arr)}
    n := st.n

    st.logTable[1] = 0
    for i := 2; i <= n; i++ {
        st.logTable[i] = st.logTable[i/2] + 1
    }

    for i := 0; i < n; i++ {
        st.table[i][0] = arr[i]
    }
    for j := 1; (1 << j) <= n; j++ {
        for i := 0; i+(1<<j)-1 < n; i++ {
            st.table[i][j] = minInt(st.table[i][j-1],
                st.table[i+(1<<(j-1))][j-1])
        }
    }
    return st
}

func (st *SparseTable) QueryMin(L, R int) int {
    k := st.logTable[R-L+1]
    return minInt(st.table[L][k], st.table[R-(1<<k)+1][k])
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    st := NewSparseTable(arr)

    fmt.Println("Min [1,5] =", st.QueryMin(1, 5)) // 1
    fmt.Println("Min [4,7] =", st.QueryMin(4, 7)) // 2
    fmt.Println("Min [0,7] =", st.QueryMin(0, 7)) // 1
}
```

### Rust Implementation

```rust
const LOG: usize = 17;

struct SparseTable {
    table: Vec<Vec<i64>>,
    log_table: Vec<usize>,
    n: usize,
}

impl SparseTable {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut log_table = vec![0usize; n + 1];
        for i in 2..=n {
            log_table[i] = log_table[i / 2] + 1;
        }

        let mut table = vec![vec![i64::MAX; LOG]; n];
        for i in 0..n {
            table[i][0] = arr[i];
        }
        for j in 1..LOG {
            let len = 1 << j;
            if len > n { break; }
            for i in 0..=n - len {
                table[i][j] = table[i][j - 1]
                    .min(table[i + (1 << (j - 1))][j - 1]);
            }
        }
        SparseTable { table, log_table, n }
    }

    fn query_min(&self, l: usize, r: usize) -> i64 {
        let k = self.log_table[r - l + 1];
        self.table[l][k].min(self.table[r - (1 << k) + 1][k])
    }
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    let st = SparseTable::new(&arr);

    println!("Min [1,5] = {}", st.query_min(1, 5)); // 1
    println!("Min [4,7] = {}", st.query_min(4, 7)); // 2
    println!("Min [0,7] = {}", st.query_min(0, 7)); // 1
}
```

---

## 7. Segment Tree — Point Update, Range Query

### Concept

A **Segment Tree** is a binary tree where:
- Each **leaf** represents a single element A[i]
- Each **internal node** represents an interval [L, R] and stores some aggregate (sum, min, max, gcd...)

This is the most versatile range query structure.

#### The Tree Structure

```
Array: A = [1, 3, 2, 7, 4, 5, 8, 6]

                   [0,7]=36
                 /           \
           [0,3]=13         [4,7]=23
           /     \           /     \
        [0,1]=4  [2,3]=9  [4,5]=9  [6,7]=14
        /   \    /   \    /   \    /    \
       1     3  2     7  4     5  8      6
      [0]  [1] [2]  [3] [4]  [5] [6]  [7]
```

Each node [L, R] stores the sum of A[L..R].
Node [L, R] has children [L, mid] and [mid+1, R] where mid = (L+R)/2.

#### Indexing with an Array

We store the tree in a flat array (1-indexed):
- Root is at index 1
- Left child of node i: `2*i`
- Right child of node i: `2*i + 1`
- Parent of node i: `i/2`

This requires an array of size **4*n** to be safe.

```
Node Layout:
         1
       /   \
      2     3
    /  \   / \
   4    5 6   7
  /\ /\ /\ /\
 8 9 ...
```

#### Build: O(n)

```
BUILD(node, L, R):
├── if L == R:
│       tree[node] = A[L]
│       return
├── mid = (L + R) / 2
├── BUILD(2*node, L, mid)        ← build left subtree
├── BUILD(2*node+1, mid+1, R)    ← build right subtree
└── tree[node] = tree[2*node] + tree[2*node+1]  ← combine
```

#### Query: O(log n)

For range sum query [QL, QR]:

```
QUERY(node, L, R, QL, QR):
├── if QL > R or QR < L:         ← NO OVERLAP
│       return 0                 ← identity for sum
├── if QL <= L and R <= QR:      ← FULL OVERLAP (entire segment in query)
│       return tree[node]        ← use precomputed value!
├── mid = (L + R) / 2
├── left  = QUERY(2*node, L, mid, QL, QR)
├── right = QUERY(2*node+1, mid+1, R, QL, QR)
└── return left + right
```

The key insight: **no overlap → skip the subtree entirely** (huge speedup).

```
Query [2, 6] on tree:

Visit node 1 [0,7]: partial overlap → recurse
├── Visit node 2 [0,3]: partial overlap → recurse
│   ├── Visit node 4 [0,1]: NO overlap (1 < 2) → return 0
│   └── Visit node 5 [2,3]: FULL overlap → return 9
└── Visit node 3 [4,7]: partial overlap → recurse
    ├── Visit node 6 [4,5]: FULL overlap → return 9
    └── Visit node 7 [6,7]: partial overlap → recurse
        ├── Visit node 14 [6,6]: FULL overlap → return 8
        └── Visit node 15 [7,7]: NO overlap (7 > 6) → return 0

Answer = 0 + 9 + 9 + 8 + 0 = 26
Actual: A[2]+A[3]+A[4]+A[5]+A[6] = 2+7+4+5+8 = 26 ✓
```

#### Point Update: O(log n)

To update A[pos] += delta:

```
UPDATE(node, L, R, pos, delta):
├── if L == R:
│       tree[node] += delta
│       return
├── mid = (L + R) / 2
├── if pos <= mid:
│       UPDATE(2*node, L, mid, pos, delta)
└── else:
        UPDATE(2*node+1, mid+1, R, pos, delta)
└── tree[node] = tree[2*node] + tree[2*node+1]  ← update on way back up
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN];
int n_global;

void build(int *arr, int node, int L, int R) {
    if (L == R) {
        tree[node] = arr[L];
        return;
    }
    int mid = (L + R) / 2;
    build(arr, 2 * node, L, mid);
    build(arr, 2 * node + 1, mid + 1, R);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

// Point update: A[pos] += delta (0-indexed pos)
void update(int node, int L, int R, int pos, long long delta) {
    if (L == R) {
        tree[node] += delta;
        return;
    }
    int mid = (L + R) / 2;
    if (pos <= mid)
        update(2 * node, L, mid, pos, delta);
    else
        update(2 * node + 1, mid + 1, R, pos, delta);
    tree[node] = tree[2 * node] + tree[2 * node + 1];
}

// Range sum query [QL, QR]
long long query(int node, int L, int R, int QL, int QR) {
    if (QL > R || QR < L) return 0;         // no overlap
    if (QL <= L && R <= QR) return tree[node]; // full overlap
    int mid = (L + R) / 2;
    return query(2 * node, L, mid, QL, QR)
         + query(2 * node + 1, mid + 1, R, QL, QR);
}

int main() {
    int arr[] = {1, 3, 2, 7, 4, 5, 8, 6};
    int n = 8;
    n_global = n;

    build(arr, 1, 0, n - 1);

    printf("Sum [2,6] = %lld\n", query(1, 0, n-1, 2, 6)); // 26

    update(1, 0, n-1, 3, 3); // A[3] += 3  (7 becomes 10)
    printf("Sum [2,6] after update = %lld\n", query(1, 0, n-1, 2, 6)); // 29

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
    st := &SegTree{
        tree: make([]int64, 4*n),
        n:    n,
    }
    st.build(arr, 1, 0, n-1)
    return st
}

func (st *SegTree) build(arr []int, node, L, R int) {
    if L == R {
        st.tree[node] = int64(arr[L])
        return
    }
    mid := (L + R) / 2
    st.build(arr, 2*node, L, mid)
    st.build(arr, 2*node+1, mid+1, R)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Update(node, L, R, pos int, delta int64) {
    if L == R {
        st.tree[node] += delta
        return
    }
    mid := (L + R) / 2
    if pos <= mid {
        st.Update(2*node, L, mid, pos, delta)
    } else {
        st.Update(2*node+1, mid+1, R, pos, delta)
    }
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *SegTree) Query(node, L, R, QL, QR int) int64 {
    if QL > R || QR < L {
        return 0
    }
    if QL <= L && R <= QR {
        return st.tree[node]
    }
    mid := (L + R) / 2
    return st.Query(2*node, L, mid, QL, QR) +
        st.Query(2*node+1, mid+1, R, QL, QR)
}

func main() {
    arr := []int{1, 3, 2, 7, 4, 5, 8, 6}
    st := NewSegTree(arr)
    n := len(arr)

    fmt.Println("Sum [2,6] =", st.Query(1, 0, n-1, 2, 6)) // 26
    st.Update(1, 0, n-1, 3, 3)
    fmt.Println("Sum [2,6] after update =", st.Query(1, 0, n-1, 2, 6)) // 29
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

    fn update(&mut self, node: usize, l: usize, r: usize, pos: usize, delta: i64) {
        if l == r {
            self.tree[node] += delta;
            return;
        }
        let mid = (l + r) / 2;
        if pos <= mid {
            self.update(2 * node, l, mid, pos, delta);
        } else {
            self.update(2 * node + 1, mid + 1, r, pos, delta);
        }
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn query(&self, node: usize, l: usize, r: usize, ql: usize, qr: usize) -> i64 {
        if ql > r || qr < l {
            return 0;
        }
        if ql <= l && r <= qr {
            return self.tree[node];
        }
        let mid = (l + r) / 2;
        self.query(2 * node, l, mid, ql, qr)
            + self.query(2 * node + 1, mid + 1, r, ql, qr)
    }
}

fn main() {
    let arr = vec![1i64, 3, 2, 7, 4, 5, 8, 6];
    let n = arr.len();
    let mut st = SegTree::new(&arr);

    println!("Sum [2,6] = {}", st.query(1, 0, n - 1, 2, 6)); // 26
    st.update(1, 0, n - 1, 3, 3);
    println!("Sum [2,6] after update = {}", st.query(1, 0, n - 1, 2, 6)); // 29
}
```

---

## 8. Segment Tree — Range Update with Lazy Propagation

### The Problem

What if we want to **add X to all elements in A[L..R]** AND answer range sum queries?

A simple point-update segment tree would need O(n) updates (one per element in [L,R]).

**Lazy Propagation** defers the update — instead of immediately updating all leaves, we mark a node saying "I'll update my children later, when I actually need to visit them."

### The "Lazy" Concept

Every node has a **lazy tag** (initially 0).

```
Lazy tag at node v = "pending addition that I need to push to my children"
```

When we visit a node and it has a non-zero lazy tag:
1. Apply the tag to both children (push down)
2. Reset the tag to 0

### How Range Update Works

```
RANGE_UPDATE(node, L, R, QL, QR, val):
├── if QL > R or QR < L:
│       return    ← no overlap, nothing to do
├── if QL <= L and R <= QR:    ← full overlap
│       tree[node] += val * (R - L + 1)   ← update this node's sum
│       lazy[node] += val                  ← mark pending for children
│       return
├── PUSH_DOWN(node, L, R)     ← propagate pending to children first!
├── mid = (L+R)/2
├── RANGE_UPDATE(2*node, L, mid, QL, QR, val)
├── RANGE_UPDATE(2*node+1, mid+1, R, QL, QR, val)
└── tree[node] = tree[2*node] + tree[2*node+1]

PUSH_DOWN(node, L, R):
├── if lazy[node] == 0: return
├── mid = (L+R)/2
├── Apply lazy[node] to left child:
│       tree[2*node] += lazy[node] * (mid - L + 1)
│       lazy[2*node] += lazy[node]
├── Apply lazy[node] to right child:
│       tree[2*node+1] += lazy[node] * (R - mid)
│       lazy[2*node+1] += lazy[node]
└── lazy[node] = 0
```

### Visual Example

```
Initial tree (sum):
         [0,3]=13
         /      \
     [0,1]=4   [2,3]=9
     /   \      /   \
    1     3    2     7

Range update: add 2 to [1,3]

Step 1: Visit [0,3] — partial overlap, push down (lazy=0, nothing to push)
    Recurse left [0,1]: partial overlap
        Recurse left [0,0]: no overlap → return
        Recurse right [1,1]: FULL overlap
            tree[[1,1]] += 2*1 = 2   (now 5)
            lazy[[1,1]] += 2
    Update [0,1]: tree = 4 + 2 = 6
    Recurse right [2,3]: FULL overlap
        tree[[2,3]] += 2*2 = 4   (now 13)
        lazy[[2,3]] += 2
Update [0,3]: tree = 6 + 13 = 19

Result tree:
         [0,3]=19
         /        \
     [0,1]=6    [2,3]=13 (lazy=2)
     /    \       /    \
    1      5     ?      ?   ← children not yet updated!
           (updated)
```

When we later query [2,3], we first push down the lazy=2 tag to leaves.

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

long long tree[4 * MAXN];
long long lazy[4 * MAXN];

void build(int *arr, int node, int L, int R) {
    lazy[node] = 0;
    if (L == R) { tree[node] = arr[L]; return; }
    int mid = (L + R) / 2;
    build(arr, 2*node, L, mid);
    build(arr, 2*node+1, mid+1, R);
    tree[node] = tree[2*node] + tree[2*node+1];
}

void push_down(int node, int L, int R) {
    if (lazy[node] == 0) return;
    int mid = (L + R) / 2;
    // Left child: covers [L, mid], size = mid-L+1
    tree[2*node]   += lazy[node] * (mid - L + 1);
    lazy[2*node]   += lazy[node];
    // Right child: covers [mid+1, R], size = R-mid
    tree[2*node+1] += lazy[node] * (R - mid);
    lazy[2*node+1] += lazy[node];
    lazy[node] = 0;
}

void range_update(int node, int L, int R, int QL, int QR, long long val) {
    if (QL > R || QR < L) return;
    if (QL <= L && R <= QR) {
        tree[node] += val * (R - L + 1);
        lazy[node] += val;
        return;
    }
    push_down(node, L, R);
    int mid = (L + R) / 2;
    range_update(2*node, L, mid, QL, QR, val);
    range_update(2*node+1, mid+1, R, QL, QR, val);
    tree[node] = tree[2*node] + tree[2*node+1];
}

long long range_query(int node, int L, int R, int QL, int QR) {
    if (QL > R || QR < L) return 0;
    if (QL <= L && R <= QR) return tree[node];
    push_down(node, L, R);
    int mid = (L + R) / 2;
    return range_query(2*node, L, mid, QL, QR)
         + range_query(2*node+1, mid+1, R, QL, QR);
}

int main() {
    int arr[] = {1, 3, 2, 7, 4, 5, 8, 6};
    int n = 8;
    build(arr, 1, 0, n-1);

    printf("Sum [1,5] = %lld\n", range_query(1, 0, n-1, 1, 5)); // 21
    range_update(1, 0, n-1, 1, 3, 2); // Add 2 to A[1..3]
    printf("Sum [1,5] after +2 on [1,3] = %lld\n",
           range_query(1, 0, n-1, 1, 5)); // 21 + 2*3 = 27
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

func (st *LazySegTree) build(arr []int, node, L, R int) {
    if L == R {
        st.tree[node] = int64(arr[L])
        return
    }
    mid := (L + R) / 2
    st.build(arr, 2*node, L, mid)
    st.build(arr, 2*node+1, mid+1, R)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *LazySegTree) pushDown(node, L, R int) {
    if st.lazy[node] == 0 {
        return
    }
    mid := (L + R) / 2
    st.tree[2*node] += st.lazy[node] * int64(mid-L+1)
    st.lazy[2*node] += st.lazy[node]
    st.tree[2*node+1] += st.lazy[node] * int64(R-mid)
    st.lazy[2*node+1] += st.lazy[node]
    st.lazy[node] = 0
}

func (st *LazySegTree) RangeUpdate(node, L, R, QL, QR int, val int64) {
    if QL > R || QR < L {
        return
    }
    if QL <= L && R <= QR {
        st.tree[node] += val * int64(R-L+1)
        st.lazy[node] += val
        return
    }
    st.pushDown(node, L, R)
    mid := (L + R) / 2
    st.RangeUpdate(2*node, L, mid, QL, QR, val)
    st.RangeUpdate(2*node+1, mid+1, R, QL, QR, val)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

func (st *LazySegTree) RangeQuery(node, L, R, QL, QR int) int64 {
    if QL > R || QR < L {
        return 0
    }
    if QL <= L && R <= QR {
        return st.tree[node]
    }
    st.pushDown(node, L, R)
    mid := (L + R) / 2
    return st.RangeQuery(2*node, L, mid, QL, QR) +
        st.RangeQuery(2*node+1, mid+1, R, QL, QR)
}

func main() {
    arr := []int{1, 3, 2, 7, 4, 5, 8, 6}
    st := NewLazySegTree(arr)
    n := len(arr)

    fmt.Println("Sum [1,5] =", st.RangeQuery(1, 0, n-1, 1, 5)) // 21
    st.RangeUpdate(1, 0, n-1, 1, 3, 2)
    fmt.Println("Sum [1,5] after update =", st.RangeQuery(1, 0, n-1, 1, 5)) // 27
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
            tree: vec![0; 4 * n],
            lazy: vec![0; 4 * n],
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

    fn range_update(&mut self, node: usize, l: usize, r: usize,
                    ql: usize, qr: usize, val: i64) {
        if ql > r || qr < l { return; }
        if ql <= l && r <= qr {
            self.tree[node] += val * (r - l + 1) as i64;
            self.lazy[node] += val;
            return;
        }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.range_update(2 * node, l, mid, ql, qr, val);
        self.range_update(2 * node + 1, mid + 1, r, ql, qr, val);
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1];
    }

    fn range_query(&mut self, node: usize, l: usize, r: usize,
                   ql: usize, qr: usize) -> i64 {
        if ql > r || qr < l { return 0; }
        if ql <= l && r <= qr { return self.tree[node]; }
        self.push_down(node, l, r);
        let mid = (l + r) / 2;
        self.range_query(2 * node, l, mid, ql, qr)
            + self.range_query(2 * node + 1, mid + 1, r, ql, qr)
    }
}

fn main() {
    let arr = vec![1i64, 3, 2, 7, 4, 5, 8, 6];
    let n = arr.len();
    let mut st = LazySegTree::new(&arr);

    println!("Sum [1,5] = {}", st.range_query(1, 0, n-1, 1, 5)); // 21
    st.range_update(1, 0, n-1, 1, 3, 2);
    println!("Sum [1,5] after update = {}", st.range_query(1, 0, n-1, 1, 5)); // 27
}
```

---

## 9. Fenwick Tree (Binary Indexed Tree / BIT)

### Concept

A **Fenwick Tree** (also called **Binary Indexed Tree** or **BIT**) is a compact, elegant data structure that supports:
- Point updates in O(log n)
- Prefix sum queries in O(log n)

It uses a clever observation about binary representations.

#### What is a "Binary Indexed Tree"?

Each index `i` in the BIT stores the sum of a range of elements. **Which range?** The range determined by the **lowest set bit** of `i`.

```
The "lowest set bit" (LSB) of a number:
  LSB(6) = LSB(110₂) = 010₂ = 2
  LSB(4) = LSB(100₂) = 100₂ = 4
  LSB(7) = LSB(111₂) = 001₂ = 1

In code: LSB(i) = i & (-i)   (bitwise trick)
```

```
BIT[i] stores sum of A[i - LSB(i) + 1 .. i]

i=1 (001): LSB=1 → BIT[1] = A[1]
i=2 (010): LSB=2 → BIT[2] = A[1]+A[2]
i=3 (011): LSB=1 → BIT[3] = A[3]
i=4 (100): LSB=4 → BIT[4] = A[1]+A[2]+A[3]+A[4]
i=5 (101): LSB=1 → BIT[5] = A[5]
i=6 (110): LSB=2 → BIT[6] = A[5]+A[6]
i=7 (111): LSB=1 → BIT[7] = A[7]
i=8 (1000): LSB=8 → BIT[8] = A[1]+...+A[8]
```

```
Visual (1-indexed):

BIT Coverage:
Index: 1  2  3  4  5  6  7  8
BIT:  [1][12][3][1234][5][56][7][12345678]
```

#### Prefix Query: Sum A[1..i]

Start at i, add BIT[i], then move to i - LSB(i), repeat:

```
prefix(7) = BIT[7] + BIT[6] + BIT[4]
           (111)   (110)    (100)
           →7-1=6  →6-2=4   →4-4=0 (stop)

= A[7] + (A[5]+A[6]) + (A[1]+A[2]+A[3]+A[4])
= sum of A[1..7] ✓
```

#### Point Update: A[i] += delta

Start at i, update BIT[i], move to i + LSB(i), repeat:

```
update(3, delta):
i=3 (011): BIT[3] += delta, i → 3+1 = 4
i=4 (100): BIT[4] += delta, i → 4+4 = 8
i=8 (1000): BIT[8] += delta, i → 8+8 = 16 > n, stop
```

This "propagates up" through all nodes that cover position 3.

#### Range Query [L, R]

```
sum(A[L..R]) = prefix(R) - prefix(L-1)
```

### Algorithm Flow

```
PREFIX(i):         UPDATE(i, delta):
i > 0?             i <= n?
├─YES               ├─YES
│  sum += BIT[i]    │  BIT[i] += delta
│  i -= i & (-i)    │  i += i & (-i)
│  (loop back)      │  (loop back)
└─NO → return sum  └─NO → done
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

long long bit[MAXN];
int n_bit;

void bit_update(int i, long long delta) {
    for (; i <= n_bit; i += i & (-i))
        bit[i] += delta;
}

long long bit_prefix(int i) {
    long long sum = 0;
    for (; i > 0; i -= i & (-i))
        sum += bit[i];
    return sum;
}

// Sum of A[L..R] (1-indexed)
long long bit_range(int L, int R) {
    return bit_prefix(R) - bit_prefix(L - 1);
}

void bit_build(int *arr, int n) {
    n_bit = n;
    memset(bit, 0, sizeof(bit));
    for (int i = 1; i <= n; i++)
        bit_update(i, arr[i-1]); // arr is 0-indexed, BIT is 1-indexed
}

int main() {
    int arr[] = {1, 3, 2, 7, 4, 5, 8, 6};
    int n = 8;
    bit_build(arr, n);

    printf("Sum [1,5] = %lld\n", bit_range(1, 5)); // 17
    printf("Sum [3,7] = %lld\n", bit_range(3, 7)); // 26

    bit_update(3, 3); // A[3] += 3 (1-indexed: A[3] was 2, now 5)
    printf("Sum [1,5] after update = %lld\n", bit_range(1, 5)); // 20

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

func NewBIT(arr []int) *BIT {
    n := len(arr)
    b := &BIT{tree: make([]int64, n+1), n: n}
    for i, v := range arr {
        b.Update(i+1, int64(v)) // 1-indexed
    }
    return b
}

func (b *BIT) Update(i int, delta int64) {
    for ; i <= b.n; i += i & (-i) {
        b.tree[i] += delta
    }
}

func (b *BIT) Prefix(i int) int64 {
    var sum int64
    for ; i > 0; i -= i & (-i) {
        sum += b.tree[i]
    }
    return sum
}

// Range sum [L, R] (1-indexed)
func (b *BIT) Range(L, R int) int64 {
    return b.Prefix(R) - b.Prefix(L-1)
}

func main() {
    arr := []int{1, 3, 2, 7, 4, 5, 8, 6}
    b := NewBIT(arr)

    fmt.Println("Sum [1,5] =", b.Range(1, 5)) // 17
    fmt.Println("Sum [3,7] =", b.Range(3, 7)) // 26
    b.Update(3, 3)
    fmt.Println("Sum [1,5] after update =", b.Range(1, 5)) // 20
}
```

### Rust Implementation

```rust
struct BIT {
    tree: Vec<i64>,
    n: usize,
}

impl BIT {
    fn new(arr: &[i64]) -> Self {
        let n = arr.len();
        let mut bit = BIT {
            tree: vec![0; n + 1],
            n,
        };
        for (i, &v) in arr.iter().enumerate() {
            bit.update(i + 1, v);
        }
        bit
    }

    fn update(&mut self, mut i: usize, delta: i64) {
        while i <= self.n {
            self.tree[i] += delta;
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

    fn range(&self, l: usize, r: usize) -> i64 {
        self.prefix(r) - self.prefix(l - 1)
    }
}

fn main() {
    let arr = vec![1i64, 3, 2, 7, 4, 5, 8, 6];
    let mut bit = BIT::new(&arr);

    println!("Sum [1,5] = {}", bit.range(1, 5)); // 17
    println!("Sum [3,7] = {}", bit.range(3, 7)); // 26
    bit.update(3, 3);
    println!("Sum [1,5] after update = {}", bit.range(1, 5)); // 20
}
```

---

## 10. Interval Merging

### Concept

Given a collection of intervals (not necessarily covering an array), **merge all overlapping intervals** into a minimal set of non-overlapping intervals.

#### Definition of Overlap

Intervals [a, b] and [c, d] overlap if and only if: `a <= d AND c <= b`

```
Overlapping:     [1,4]   [3,6]  →  [1,6]
                    |____|
                       ↕
Non-overlapping: [1,3]   [5,7]  →  [1,3], [5,7]
                     |  gap  |
```

#### Algorithm

1. Sort intervals by their **left endpoint**
2. Iterate: if the current interval overlaps the last merged interval, extend it; otherwise, start a new interval.

```
MERGE_INTERVALS(intervals):
Sort intervals by L (left endpoint)

result = [intervals[0]]

for each interval [L, R] starting from index 1:
    last = result.back()
    if L <= last.R:        ← overlaps
        last.R = max(last.R, R)    ← extend
    else:
        result.push([L, R])        ← new interval

return result
```

```
Example: [[1,3],[2,6],[8,10],[15,18]]

After sort (already sorted by L):

i=0: result = [[1,3]]
i=1: [2,6] — L=2 <= last.R=3 → extend to [1,6]   result=[[1,6]]
i=2: [8,10] — L=8 > last.R=6 → new interval       result=[[1,6],[8,10]]
i=3: [15,18] — L=15 > last.R=10 → new interval    result=[[1,6],[8,10],[15,18]]
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int L, R; } Interval;

int cmp_interval(const void *a, const void *b) {
    return ((Interval*)a)->L - ((Interval*)b)->L;
}

int merge_intervals(Interval *arr, int n, Interval *result) {
    if (n == 0) return 0;
    qsort(arr, n, sizeof(Interval), cmp_interval);

    int cnt = 0;
    result[cnt++] = arr[0];

    for (int i = 1; i < n; i++) {
        Interval *last = &result[cnt - 1];
        if (arr[i].L <= last->R) {
            if (arr[i].R > last->R) last->R = arr[i].R;
        } else {
            result[cnt++] = arr[i];
        }
    }
    return cnt;
}

int main() {
    Interval arr[] = {{1,3},{2,6},{8,10},{15,18}};
    int n = 4;
    Interval result[10];

    int cnt = merge_intervals(arr, n, result);
    for (int i = 0; i < cnt; i++) {
        printf("[%d, %d]\n", result[i].L, result[i].R);
    }
    return 0;
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

type Interval struct{ L, R int }

func mergeIntervals(intervals []Interval) []Interval {
    if len(intervals) == 0 {
        return nil
    }
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i].L < intervals[j].L
    })

    result := []Interval{intervals[0]}
    for _, iv := range intervals[1:] {
        last := &result[len(result)-1]
        if iv.L <= last.R {
            if iv.R > last.R {
                last.R = iv.R
            }
        } else {
            result = append(result, iv)
        }
    }
    return result
}

func main() {
    intervals := []Interval{{1, 3}, {2, 6}, {8, 10}, {15, 18}}
    merged := mergeIntervals(intervals)
    for _, iv := range merged {
        fmt.Printf("[%d, %d]\n", iv.L, iv.R)
    }
}
```

### Rust Implementation

```rust
#[derive(Debug, Clone)]
struct Interval {
    l: i64,
    r: i64,
}

fn merge_intervals(mut intervals: Vec<Interval>) -> Vec<Interval> {
    if intervals.is_empty() {
        return vec![];
    }
    intervals.sort_by_key(|iv| iv.l);

    let mut result: Vec<Interval> = vec![intervals[0].clone()];
    for iv in intervals.into_iter().skip(1) {
        let last = result.last_mut().unwrap();
        if iv.l <= last.r {
            last.r = last.r.max(iv.r);
        } else {
            result.push(iv);
        }
    }
    result
}

fn main() {
    let intervals = vec![
        Interval { l: 1, r: 3 },
        Interval { l: 2, r: 6 },
        Interval { l: 8, r: 10 },
        Interval { l: 15, r: 18 },
    ];
    let merged = merge_intervals(intervals);
    for iv in &merged {
        println!("[{}, {}]", iv.l, iv.r);
    }
}
```

---

## 11. Sweep Line Algorithm

### Concept

A **Sweep Line** imagines a vertical line sweeping from left to right across the number line. As it passes each event (start or end of an interval), we process it.

#### Classic Problem: Maximum Interval Coverage

> Given N intervals, at what point is the maximum number of intervals active simultaneously?

```
Intervals: [1,4], [2,6], [3,5], [7,9]

          1   2   3   4   5   6   7   8   9
[1,4]:    |_____________|
[2,6]:        |_______________|
[3,5]:            |_______|
[7,9]:                            |_______|

Coverage:  1   2   3   3   2   1   1   1   0

Maximum = 3 (at time 3 or 4)
```

#### Algorithm Using Events

```
For each interval [L, R]:
    Add event: (L, +1)   ← "enters" at L
    Add event: (R+1, -1) ← "exits" after R

Sort events by time (break ties: exits before entries, or as per problem)

Sweep through events, maintain running count.
```

```
Events from [1,4],[2,6],[3,5],[7,9]:
(1,+1), (2,+1), (3,+1), (5,-1), (5,-1), (7,+1), (7,-1), (10,-1)

Wait, (R+1,-1):
[1,4]: (1,+1),(5,-1)
[2,6]: (2,+1),(7,-1)
[3,5]: (3,+1),(6,-1)
[7,9]: (7,+1),(10,-1)

Sort: (1,+1),(2,+1),(3,+1),(5,-1),(6,-1),(7,+1),(7,-1),(10,-1)

time=1: count=1, max=1
time=2: count=2, max=2
time=3: count=3, max=3
time=5: count=2, max=3
time=6: count=1, max=3
time=7: count=1 (one leaves, one enters simultaneously)
time=10: count=0

Answer: 3
```

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct { int time, type; } Event; // type: +1=start, -1=end

int cmp_event(const void *a, const void *b) {
    Event *ea = (Event*)a, *eb = (Event*)b;
    if (ea->time != eb->time) return ea->time - eb->time;
    return ea->type - eb->type; // exits (-1) before entries (+1)
}

int max_overlap(int intervals[][2], int n) {
    Event *events = malloc(2 * n * sizeof(Event));
    for (int i = 0; i < n; i++) {
        events[2*i]   = (Event){intervals[i][0], +1};
        events[2*i+1] = (Event){intervals[i][1] + 1, -1};
    }
    qsort(events, 2*n, sizeof(Event), cmp_event);

    int cur = 0, mx = 0;
    for (int i = 0; i < 2 * n; i++) {
        cur += events[i].type;
        if (cur > mx) mx = cur;
    }
    free(events);
    return mx;
}

int main() {
    int intervals[][2] = {{1,4},{2,6},{3,5},{7,9}};
    printf("Max overlap = %d\n", max_overlap(intervals, 4)); // 3
    return 0;
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "sort"
)

type Event struct{ time, typ int }

func maxOverlap(intervals [][2]int) int {
    events := make([]Event, 0, 2*len(intervals))
    for _, iv := range intervals {
        events = append(events, Event{iv[0], +1})
        events = append(events, Event{iv[1] + 1, -1})
    }
    sort.Slice(events, func(i, j int) bool {
        if events[i].time != events[j].time {
            return events[i].time < events[j].time
        }
        return events[i].typ < events[j].typ
    })

    cur, mx := 0, 0
    for _, e := range events {
        cur += e.typ
        if cur > mx {
            mx = cur
        }
    }
    return mx
}

func main() {
    intervals := [][2]int{{1, 4}, {2, 6}, {3, 5}, {7, 9}}
    fmt.Println("Max overlap =", maxOverlap(intervals)) // 3
}
```

### Rust Implementation

```rust
fn max_overlap(intervals: &[(i64, i64)]) -> i64 {
    let mut events: Vec<(i64, i64)> = Vec::new();
    for &(l, r) in intervals {
        events.push((l, 1));
        events.push((r + 1, -1));
    }
    events.sort();

    let (mut cur, mut mx) = (0i64, 0i64);
    for (_, typ) in events {
        cur += typ;
        mx = mx.max(cur);
    }
    mx
}

fn main() {
    let intervals = vec![(1, 4), (2, 6), (3, 5), (7, 9)];
    println!("Max overlap = {}", max_overlap(&intervals)); // 3
}
```

---

## 12. Two-Pointer / Sliding Window on Intervals

### Concept

The **sliding window** (or **two-pointer**) technique maintains a window [L, R] over the array where both pointers move **only forward**.

#### When to Use

When the problem requires finding a **subarray** (contiguous interval) satisfying some condition, and that condition has **monotonic** behavior:
- "Shrinking the window never breaks the condition"
- "Expanding the window never unexpectedly satisfies the condition"

#### Classic: Minimum Window with Sum ≥ K

Find the shortest subarray with sum ≥ K.

```
Algorithm:
1. Start with L=0, R=0, window_sum=0
2. Expand R: add A[R] to window_sum
3. While window_sum >= K:
       record length R-L+1
       shrink: subtract A[L], increment L
4. Repeat until R reaches end

Window Behavior:
┌───────────────────────────────────────────┐
│  L                       R                │
│  │                       │                │
│  ▼                       ▼                │
│ [3, 1, 4, 1, 5, 9, 2, 6]                 │
│  expand R →                               │
│  ← shrink L when sum >= K                 │
└───────────────────────────────────────────┘
```

### C Implementation

```c
#include <stdio.h>
#include <limits.h>

int min_window_sum(int *arr, int n, int K) {
    int L = 0, min_len = INT_MAX;
    long long sum = 0;
    for (int R = 0; R < n; R++) {
        sum += arr[R];
        while (sum >= K) {
            int len = R - L + 1;
            if (len < min_len) min_len = len;
            sum -= arr[L++];
        }
    }
    return min_len == INT_MAX ? -1 : min_len;
}

// Maximum sum subarray of fixed length k (sliding window)
long long max_sum_fixed_window(int *arr, int n, int k) {
    long long window = 0;
    for (int i = 0; i < k; i++) window += arr[i];
    long long mx = window;
    for (int i = k; i < n; i++) {
        window += arr[i] - arr[i - k];
        if (window > mx) mx = window;
    }
    return mx;
}

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = 8;
    printf("Min window sum >= 15: length = %d\n",
           min_window_sum(arr, n, 15)); // 2 (9+6)
    printf("Max sum window of size 3 = %lld\n",
           max_sum_fixed_window(arr, n, 3)); // 17 (9+2+6 or 5+9+... check)
    return 0;
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "math"
)

func minWindowSum(arr []int, K int) int {
    L, minLen := 0, math.MaxInt64
    sum := 0
    for R := 0; R < len(arr); R++ {
        sum += arr[R]
        for sum >= K {
            if R-L+1 < minLen {
                minLen = R - L + 1
            }
            sum -= arr[L]
            L++
        }
    }
    if minLen == math.MaxInt64 {
        return -1
    }
    return minLen
}

func maxSumFixedWindow(arr []int, k int) int64 {
    var window int64
    for i := 0; i < k; i++ {
        window += int64(arr[i])
    }
    mx := window
    for i := k; i < len(arr); i++ {
        window += int64(arr[i]) - int64(arr[i-k])
        if window > mx {
            mx = window
        }
    }
    return mx
}

func main() {
    arr := []int{3, 1, 4, 1, 5, 9, 2, 6}
    fmt.Println("Min window sum >= 15:", minWindowSum(arr, 15))
    fmt.Println("Max sum window k=3:", maxSumFixedWindow(arr, 3))
}
```

### Rust Implementation

```rust
fn min_window_sum(arr: &[i64], k: i64) -> Option<usize> {
    let mut l = 0usize;
    let mut sum = 0i64;
    let mut min_len = usize::MAX;

    for r in 0..arr.len() {
        sum += arr[r];
        while sum >= k {
            min_len = min_len.min(r - l + 1);
            sum -= arr[l];
            l += 1;
        }
    }
    if min_len == usize::MAX { None } else { Some(min_len) }
}

fn max_sum_fixed_window(arr: &[i64], k: usize) -> i64 {
    let mut window: i64 = arr[..k].iter().sum();
    let mut mx = window;
    for i in k..arr.len() {
        window += arr[i] - arr[i - k];
        mx = mx.max(window);
    }
    mx
}

fn main() {
    let arr = vec![3i64, 1, 4, 1, 5, 9, 2, 6];
    println!("Min window sum >= 15: {:?}", min_window_sum(&arr, 15));
    println!("Max sum window k=3: {}", max_sum_fixed_window(&arr, 3));
}
```

---

## 13. Comparative Analysis and When to Use What

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║            COMPLETE COMPARISON: RANGE QUERY DATA STRUCTURES                  ║
╠══════════════════╦═════════╦══════════╦═════════════╦═════════════════════════╣
║ Structure        ║ Build   ║ Query    ║ Update      ║ Notes                   ║
╠══════════════════╬═════════╬══════════╬═════════════╬═════════════════════════╣
║ Brute Force      ║ O(1)    ║ O(n)     ║ O(1)        ║ Baseline, always works  ║
║ Prefix Sum       ║ O(n)    ║ O(1)     ║ O(n)        ║ No updates; sum only    ║
║ Difference Array ║ O(n)    ║ O(n)*    ║ O(1) range  ║ Batch updates, then Q   ║
║ Sparse Table     ║ O(nlogn)║ O(1)     ║ O(nlogn)    ║ Idempotent ops only     ║
║ Segment Tree     ║ O(n)    ║ O(logn)  ║ O(logn)     ║ Most versatile          ║
║ Lazy Seg Tree    ║ O(n)    ║ O(logn)  ║ O(logn)     ║ Range updates           ║
║ Fenwick Tree     ║ O(nlogn)║ O(logn)  ║ O(logn)     ║ Sum only; compact       ║
╚══════════════════╩═════════╩══════════╩═════════════╩═════════════════════════╝
* Diff array: O(1) range update, but O(n) to reconstruct for point queries
```

### Decision Guide (Expanded)

```
PROBLEM TYPE                     →  BEST TOOL
─────────────────────────────────────────────────────────────
Static array, range sum          →  Prefix Sum
Static array, range min/max      →  Sparse Table
Batch range-add, then queries    →  Difference Array
Point updates + range sum        →  Fenwick Tree (BIT)
Point updates + range min/max    →  Segment Tree
Range updates + range queries    →  Lazy Segment Tree
Interval merging                 →  Sort + Greedy
Event counting over time         →  Sweep Line
Subarray condition (monotone)    →  Two Pointer / Sliding Window
```

---

## 14. Classic Problems and Patterns

### Problem 1: Maximum Subarray Sum (Kadane's Algorithm)

> Find the subarray [L, R] with maximum sum.

```
Kadane's insight: At each position i, the best subarray ending at i is either:
- Just A[i] alone (start fresh)
- Extend the best subarray ending at i-1

max_ending_here = max(A[i], max_ending_here + A[i])
global_max = max(global_max, max_ending_here)
```

```c
long long kadane(int *arr, int n) {
    long long max_here = arr[0], global_max = arr[0];
    for (int i = 1; i < n; i++) {
        if (max_here + arr[i] > arr[i])
            max_here = max_here + arr[i];
        else
            max_here = arr[i];
        if (max_here > global_max) global_max = max_here;
    }
    return global_max;
}
```

### Problem 2: Number of Subarrays with Sum = K

Use prefix sum + hashmap:

```
prefix[0] = 0
For each i, compute prefix[i]
If (prefix[i] - K) was seen before → subarray exists!

Why? prefix[i] - prefix[j] = K means sum(A[j+1..i]) = K
```

```go
func countSubarraysSumK(arr []int, K int) int {
    count := 0
    prefix := 0
    freq := map[int]int{0: 1} // prefix=0 seen once (empty prefix)
    for _, v := range arr {
        prefix += v
        count += freq[prefix-K]
        freq[prefix]++
    }
    return count
}
```

### Problem 3: Range Updates then Range Queries

Use two BITs (Fenwick Trees):

```
For range add on [L,R] with value V, and later range sum query [0,i]:

Fact: sum(A[0..i]) after range updates =
    BIT1.query(i) * (i+1) - BIT2.query(i)

Update [L,R] by V:
    BIT1.update(L, V);        BIT2.update(L, V*(L-1))
    BIT1.update(R+1, -V);     BIT2.update(R+1, -V*R)

This is an advanced technique for when both range update AND range sum query are needed simultaneously without lazy propagation.
```

### Problem 4: Minimum Number of Meeting Rooms

> Given meeting intervals, find the minimum number of rooms needed.

= Maximum number of overlapping intervals (sweep line).

### Problem 5: Longest Subarray with at Most K Distinct Elements

```
Sliding window with a frequency map:
- Expand R: add arr[R] to frequency map
- While distinct count > K: shrink L
- Track max window size

Time: O(n)
```

---

## 15. Psychological and Cognitive Mastery Notes

### The Expert's Mental Model Stack

When approaching any interval problem, experts cycle through these mental checks:

```
LEVEL 1 — PATTERN RECOGNITION (1 second)
"Is this a range query problem?"
"Are there updates? Static or dynamic?"
"What operation? Sum? Min? Max? Custom?"

LEVEL 2 — CONSTRAINT ANALYSIS (10 seconds)
n = 10^5, Q = 10^5 → O(n log n) needed
n = 10^6 → need O(n) or O(n log n), no O(n^2)
Offline possible? → Can use MO's algorithm or offline BIT tricks

LEVEL 3 — STRUCTURE SELECTION (30 seconds)
Based on decision tree above, pick the right tool.

LEVEL 4 — IMPLEMENTATION (minutes)
Build confidently using known templates.
```

### Deliberate Practice Protocol

To master interval problems:

1. **Chunking**: Deeply understand each structure (prefix, BIT, segment tree) as a single unit before combining.
2. **Interleaving**: After learning each structure, practice problems mixing multiple techniques.
3. **Retrieval Practice**: Implement each structure from scratch without notes 3 times.
4. **Spaced Repetition**: Revisit harder problems (lazy propagation) after 3 days, 1 week, 2 weeks.

### Mental Models for Segment Trees

- **Divide and Conquer**: Every segment tree IS divide-and-conquer made persistent.
- **The Push Down Principle**: "Never access a child before resolving the parent's lazy tag." This is a constraint that, once internalized, makes lazy propagation feel natural.
- **Idempotent vs Non-idempotent**: Min/max are idempotent → sparse table wins. Sum is not → need segment tree or BIT.

### The Monk's Approach to Debugging

When a segment tree gives wrong answers:

```
Checklist (in order):
1. Did you handle the base case (L == R) correctly?
2. Is your push_down called BEFORE recursing in both update and query?
3. Is your tree size 4*n (not 2*n or n)?
4. Are you using 1-indexed consistently?
5. Does your identity value match the operation? (0 for sum, INF for min)
6. Are your lazy tags correctly cleared after pushing down?
```

### Flow State Protocol

Before a timed contest:
1. **Warm up** with one easy prefix sum problem (5 min)
2. **Read** all problems before coding any
3. **Map** each problem to a known pattern/tool
4. **Code** the simplest correct solution first, then optimize

Remember: **Clarity of thought precedes clarity of code.** A top 1% programmer thinks on paper for twice as long as they code. The code should almost write itself once the logic is airtight.

---

## Summary: The Interval Mastery Ladder

```
BEGINNER
│
├── Brute force range loops
├── Prefix sum (1D and 2D)
└── Difference array

INTERMEDIATE
│
├── Sparse table (RMQ in O(1))
├── Segment tree (build, query, point update)
└── Interval merging + sweep line

ADVANCED
│
├── Segment tree with lazy propagation
├── Fenwick tree + BIT tricks
├── Two BITs for range-update + range-query
└── Offline query processing

EXPERT
│
├── Persistent segment tree
├── Merge sort tree (queries on sorted subarrays)
├── Fractional cascading
└── MO's algorithm (offline sqrt decomposition)
```

> **The Monk's Principle**: You do not rise to the level of your ambition. You fall to the level of your preparation. Build the foundations so solid that complex problems feel simple.

---

*End of Guide — Array Intervals and Segments: Complete DSA Mastery Reference*

Now let me create the comprehensive guide:Here is your complete guide. Here's what's covered inside:

**Foundational Concepts** — What an interval is, vocabulary (prefix, suffix, idempotent, associative), and a master decision tree to pick the right structure instantly.

**All 9 Core Structures** — Each explained from scratch with theory, algorithm flow diagrams, worked examples, and full C + Go + Rust implementations:
1. Brute Force (baseline)
2. Prefix Sum (1D + 2D extension)
3. Difference Array (O(1) range updates)
4. Sparse Table (O(1) RMQ, static only)
5. Segment Tree (point update + range query)
6. Segment Tree with Lazy Propagation (range update + range query)
7. Fenwick Tree / BIT (compact, elegant sum structure)
8. Interval Merging (sort + greedy)
9. Sweep Line + Sliding Window

**Complexity comparison table**, classic problem patterns (Kadane's, subarray count, meeting rooms), and a full **Mastery Ladder** from beginner to expert level.

The **Monk's debugging checklist** for segment trees is especially worth memorizing — it covers every mistake beginners make with lazy propagation. The next natural step after mastering this guide is **Persistent Segment Tree** and **MO's Algorithm**, which build directly on everything here.