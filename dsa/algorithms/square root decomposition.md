# Square Root Decomposition — Complete & Comprehensive Guide

> *"The art of programming is the art of organizing complexity."*
> — Edsger W. Dijkstra

---

## Table of Contents

1. [The Mental Model: Why This Technique Exists](#1-the-mental-model-why-this-technique-exists)
2. [Foundational Vocabulary](#2-foundational-vocabulary)
3. [Core Idea: The √N Sweet Spot](#3-core-idea-the-n-sweet-spot)
4. [Block Decomposition Visualized (ASCII)](#4-block-decomposition-visualized-ascii)
5. [Classic Problem: Range Sum Query with Point Updates](#5-classic-problem-range-sum-query-with-point-updates)
6. [Algorithm Flow & Decision Trees](#6-algorithm-flow--decision-trees)
7. [Implementation — C](#7-implementation--c)
8. [Implementation — Go](#8-implementation--go)
9. [Implementation — Rust](#9-implementation--rust)
10. [Range Minimum Query (RMQ)](#10-range-minimum-query-rmq)
11. [Range Update + Range Query (Lazy Block)](#11-range-update--range-query-lazy-block)
12. [Mo's Algorithm (Offline Queries)](#12-mos-algorithm-offline-queries)
13. [Mo's Algorithm Implementations](#13-mos-algorithm-implementations)
14. [Sqrt Decomposition on Strings](#14-sqrt-decomposition-on-strings)
15. [Sqrt Decomposition on Trees (Heavy Path Intuition)](#15-sqrt-decomposition-on-trees-heavy-path-intuition)
16. [Complexity Analysis Deep Dive](#16-complexity-analysis-deep-dive)
17. [Comparison: Sqrt vs Segment Tree vs Fenwick Tree](#17-comparison-sqrt-vs-segment-tree-vs-fenwick-tree)
18. [Common Patterns & Template Thinking](#18-common-patterns--template-thinking)
19. [Common Mistakes & Pitfalls](#19-common-mistakes--pitfalls)
20. [Problem Set & Practice Ladder](#20-problem-set--practice-ladder)
21. [Expert Mental Models & Cognitive Strategies](#21-expert-mental-models--cognitive-strategies)

---

## 1. The Mental Model: Why This Technique Exists

Before writing a single line of code, understand the *problem space* that gives birth to sqrt decomposition.

### The Core Tension

Imagine you have an array of N elements. You face two operations:

```
QUERY:  Ask something about a range [L, R]   (e.g., sum, min, max)
UPDATE: Modify one or more elements
```

**Naive approaches hit a wall:**

```
APPROACH A — Precompute everything:
  Build a prefix sum table → O(N) space, O(1) query, O(N) update
  Problem: Each update forces O(N) recomputation of prefix sums

APPROACH B — Recompute on demand:
  Store raw array → O(N) query (iterate L to R), O(1) update
  Problem: Each query is slow for large ranges

THE WALL:
  If we have Q queries and Q updates, both on N elements:
  - Approach A: O(N) build + O(Q*N) updates + O(Q) queries = O(QN)
  - Approach B: O(Q*N) queries + O(Q) updates              = O(QN)
```

**Can we find a middle ground?** Yes. That's sqrt decomposition.

### The Philosophical Insight

> Split the problem into blocks of size √N.
> Precompute answers for whole blocks.
> For partial blocks, recompute naively.
>
> Result: Neither query nor update dominates. Both cost O(√N).

This is a classic **time-space tradeoff** and a form of **chunking** — a cognitive science principle where breaking a large problem into manageable units reduces cognitive (and computational) load.

---

## 2. Foundational Vocabulary

Before proceeding, let's define every term you'll encounter:

| Term | Meaning |
|------|---------|
| **Block** | A contiguous sub-array of size ~√N |
| **Block size (B)** | Typically ⌊√N⌋ — the size of each block |
| **Block index** | `i / B` — which block does index `i` belong to? |
| **Block boundary** | The indices where one block ends and another begins |
| **Partial block** | A block that is only partially covered by a query range |
| **Complete block** | A block fully contained within a query range |
| **Block aggregate** | A precomputed value for an entire block (sum, min, max, etc.) |
| **Lazy tag** | A pending operation on a block that hasn't been pushed down yet |
| **Offline query** | A query that doesn't need to be answered immediately; can be reordered |
| **Online query** | A query that must be answered before the next one arrives |
| **Range query** | A question asked about a contiguous sub-array [L, R] |
| **Point update** | Changing exactly one element |
| **Range update** | Changing all elements in a range [L, R] |
| **Mo's algorithm** | Offline sqrt technique that answers range queries in O((N+Q)√N) |
| **Invariant** | A property that must hold true at all times (e.g., block sums are up-to-date) |

---

## 3. Core Idea: The √N Sweet Spot

### Why √N?

Let block size = B. Then:

```
Number of blocks = ceil(N / B)

Query cost:
  - At most 2 partial blocks → cost O(B) each
  - At most ceil(N/B) complete blocks → cost O(N/B) each
  - Total: O(B + N/B)

Update cost:
  - Change element → O(1)
  - Rebuild one block aggregate → O(B)
  - Total: O(B)

To minimize query cost, differentiate and set to zero:
  d/dB [B + N/B] = 1 - N/B² = 0
  => B² = N
  => B = √N

At B = √N:
  Query:  O(√N + N/√N) = O(√N + √N) = O(√N)
  Update: O(√N)
```

### The Mathematical Beauty

```
     Cost
      |
   N  |  *
      | * *
      |*   *
  √N  |     *----*----*
      |              * *
      |                 *
      +--√N-----------N---> Block size B

The minimum cost occurs at B = √N, giving O(√N) for both ops.
```

---

## 4. Block Decomposition Visualized (ASCII)

### Array Layout with Blocks

```
Array indices:  0   1   2   3   4   5   6   7   8   9   10  11
Array values: [ 3 | 1 | 4 | 1 | 5 | 9 | 2 | 6 | 5 | 3 | 5 | 8 ]
               |___________|   |___________|   |___________|
                  Block 0         Block 1         Block 2
                 sum = 9          sum = 22        sum = 21

Block size B = 4 (for N=12, √12 ≈ 3.46, rounded up to 4)

block_sum[0] = 3+1+4+1 = 9
block_sum[1] = 5+9+2+6 = 22
block_sum[2] = 5+3+5+8 = 21
```

### Query: sum(2, 9)  [L=2, R=9]

```
Index:          0   1  [2   3   4   5   6   7   8   9]  10  11
               [ 3 | 1 | 4 | 1 | 5 | 9 | 2 | 6 | 5 | 3 | 5 | 8 ]
                       |_____| |___________|  |_____|
                       Partial   Complete     Partial
                       Block 0   Block 1      Block 2
                        (4+1)     (22)         (5+3)
                          5    +   22    +       8    = 35

Step 1: L=2 is in block 0 (2/4=0), not at block start (0*4=0). Partial.
        Sum indices 2..3 manually: arr[2]+arr[3] = 4+1 = 5

Step 2: R=9 is in block 2 (9/4=2), not at block end (2*4+3=11). Partial.
        Sum indices 8..9 manually: arr[8]+arr[9] = 5+3 = 8

Step 3: Full blocks between block 1..1: block_sum[1] = 22

Total = 5 + 22 + 8 = 35 ✓
```

### Query Anatomy — Decision Flow

```
Given query [L, R]:

  block_L = L / B          (which block does L fall in?)
  block_R = R / B          (which block does R fall in?)

  CASE 1: block_L == block_R
          (both endpoints in same block)

          ┌─────────────────────────────────┐
          │  Iterate L..R directly: O(B)    │
          └─────────────────────────────────┘

  CASE 2: block_L != block_R
          (endpoints in different blocks)

          ┌──────────────────────────────────────────────────────────┐
          │                                                          │
          │  LEFT PARTIAL:  L .. (block_L+1)*B - 1    → O(B)        │
          │  MIDDLE FULL:   block_sum[block_L+1 .. block_R-1] → O(N/B)│
          │  RIGHT PARTIAL: block_R*B .. R             → O(B)        │
          │                                                          │
          └──────────────────────────────────────────────────────────┘
```

---

## 5. Classic Problem: Range Sum Query with Point Updates

### Problem Statement

```
Given: Array A[0..N-1]
Operations:
  1. query(L, R)   → return A[L] + A[L+1] + ... + A[R]
  2. update(i, v)  → set A[i] = v
```

### Preprocessing

```
B = sqrt(N)
block_sum[k] = sum of A[k*B .. min((k+1)*B-1, N-1)]

BUILD: O(N)
SPACE: O(√N) extra for block_sum
```

---

## 6. Algorithm Flow & Flowcharts

### Build Phase

```
START
  |
  v
B = floor(sqrt(N))
  |
  v
FOR i = 0 to N-1:
  |
  +---> block_id = i / B
  |
  +---> block_sum[block_id] += A[i]
  |
  v
END BUILD
```

### Query Flow

```
query(L, R):
     |
     v
block_L = L / B
block_R = R / B
result  = 0
     |
     v
  [block_L == block_R?]
     |          |
    YES         NO
     |          |
     v          v
  sum A[L..R]   LEFT PARTIAL:
  manually      FOR i = L to (block_L+1)*B - 1:
  return           result += A[i]
                |
                v
                MIDDLE FULL BLOCKS:
                FOR b = block_L+1 to block_R-1:
                   result += block_sum[b]
                |
                v
                RIGHT PARTIAL:
                FOR i = block_R*B to R:
                   result += A[i]
                |
                v
              return result
```

### Update Flow

```
update(i, v):
     |
     v
block_id = i / B
     |
     v
block_sum[block_id] -= A[i]   (remove old contribution)
     |
     v
A[i] = v                      (set new value)
     |
     v
block_sum[block_id] += v      (add new contribution)
     |
     v
END
```

---

## 7. Implementation — C

```c
/*
 * Square Root Decomposition — Range Sum Query + Point Update
 * Language: C
 * Time:  Query O(√N), Update O(1) [with block rebuild O(√N) worst case]
 * Space: O(N + √N)
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 100005

typedef long long ll;

int  arr[MAXN];
ll   block_sum[320];   /* ceil(sqrt(100000)) ≈ 317 */
int  N, B;             /* B = block size */

/* ─────────────────────────────────────────────
   Build: compute block sums from scratch
   Time: O(N)
   ───────────────────────────────────────────── */
void build(int *a, int n) {
    N = n;
    B = (int)sqrt((double)n);
    if (B == 0) B = 1;   /* guard for tiny arrays */

    memset(block_sum, 0, sizeof(block_sum));

    for (int i = 0; i < n; i++) {
        arr[i] = a[i];
        block_sum[i / B] += a[i];
    }
}

/* ─────────────────────────────────────────────
   Query: sum of A[L..R] (inclusive, 0-indexed)
   Time: O(√N)
   ───────────────────────────────────────────── */
ll query(int L, int R) {
    ll result = 0;
    int block_L = L / B;
    int block_R = R / B;

    if (block_L == block_R) {
        /* Both endpoints in the same block: iterate directly */
        for (int i = L; i <= R; i++)
            result += arr[i];
        return result;
    }

    /* Left partial block */
    int left_end = (block_L + 1) * B - 1;
    for (int i = L; i <= left_end; i++)
        result += arr[i];

    /* Middle complete blocks */
    for (int b = block_L + 1; b <= block_R - 1; b++)
        result += block_sum[b];

    /* Right partial block */
    int right_start = block_R * B;
    for (int i = right_start; i <= R; i++)
        result += arr[i];

    return result;
}

/* ─────────────────────────────────────────────
   Point Update: set A[i] = val
   Time: O(1)
   ───────────────────────────────────────────── */
void update(int i, int val) {
    int block_id = i / B;
    block_sum[block_id] -= arr[i];
    arr[i] = val;
    block_sum[block_id] += val;
}

/* ─────────────────────────────────────────────
   Demo
   ───────────────────────────────────────────── */
int main(void) {
    int a[] = {3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8};
    int n = sizeof(a) / sizeof(a[0]);

    build(a, n);

    printf("Block size B = %d\n", B);
    printf("query(2, 9)  = %lld  (expected 35)\n", query(2, 9));
    printf("query(0, 11) = %lld  (expected 52)\n", query(0, 11));

    update(4, 10);    /* A[4] was 5, now 10 */
    printf("After update(4, 10):\n");
    printf("query(2, 9)  = %lld  (expected 40)\n", query(2, 9));

    return 0;
}
```

### C — Range Update + Range Query (Lazy Blocks)

```c
/*
 * Sqrt Decomposition — Range Add Update + Range Sum Query
 * Uses a "lazy" tag per block for pending additions.
 *
 * Invariant:
 *   True sum of arr[i] = arr[i] + lazy[block_id_of_i]
 *   block_sum[b] = sum of raw arr values in block b (WITHOUT lazy)
 *   Actual sum of block b = block_sum[b] + lazy[b] * B
 *
 * Time: Update O(√N), Query O(√N)
 */

#include <stdio.h>
#include <math.h>
#include <string.h>

#define MAXN 100005

typedef long long ll;

int  arr[MAXN];
ll   block_sum[320];
ll   lazy[320];       /* pending addition for entire block */
int  N, B, num_blocks;

void build(int *a, int n) {
    N = n;
    B = (int)sqrt((double)n);
    if (B == 0) B = 1;
    num_blocks = (n + B - 1) / B;

    memset(block_sum, 0, sizeof(block_sum));
    memset(lazy, 0, sizeof(lazy));

    for (int i = 0; i < n; i++) {
        arr[i] = a[i];
        block_sum[i / B] += a[i];
    }
}

/*
 * Range Add: add val to all elements in [L, R]
 *
 * MENTAL MODEL:
 *   For partial blocks at boundaries → update individual elements
 *     and fix block_sum directly.
 *   For complete blocks → just increment lazy[b] (O(1) per block).
 */
void range_add(int L, int R, ll val) {
    int block_L = L / B;
    int block_R = R / B;

    if (block_L == block_R) {
        /* Same block: update individually */
        for (int i = L; i <= R; i++) {
            arr[i] += val;
            block_sum[block_L] += val;
        }
        return;
    }

    /* Left partial block */
    int left_end = (block_L + 1) * B - 1;
    for (int i = L; i <= left_end; i++) {
        arr[i] += val;
        block_sum[block_L] += val;
    }

    /* Complete middle blocks: just touch lazy */
    for (int b = block_L + 1; b <= block_R - 1; b++)
        lazy[b] += val;

    /* Right partial block */
    int right_start = block_R * B;
    for (int i = right_start; i <= R; i++) {
        arr[i] += val;
        block_sum[block_R] += val;
    }
}

/*
 * Range Sum Query
 *
 * For partial blocks: sum raw arr values (lazy NOT yet applied to arr[i]),
 *   add lazy[block] * (number of elements covered in that block).
 * For complete blocks: block_sum[b] + lazy[b] * B.
 */
ll range_query(int L, int R) {
    ll result = 0;
    int block_L = L / B;
    int block_R = R / B;

    if (block_L == block_R) {
        for (int i = L; i <= R; i++)
            result += arr[i] + lazy[block_L];
        return result;
    }

    /* Left partial */
    int left_end = (block_L + 1) * B - 1;
    for (int i = L; i <= left_end; i++)
        result += arr[i] + lazy[block_L];

    /* Middle full blocks */
    for (int b = block_L + 1; b <= block_R - 1; b++) {
        int block_size_b = (b == num_blocks - 1) ? (N - b * B) : B;
        result += block_sum[b] + lazy[b] * block_size_b;
    }

    /* Right partial */
    int right_start = block_R * B;
    for (int i = right_start; i <= R; i++)
        result += arr[i] + lazy[block_R];

    return result;
}

int main(void) {
    int a[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int n   = 10;
    build(a, n);

    printf("Initial sum(0,9) = %lld (expected 55)\n", range_query(0, 9));

    range_add(2, 7, 5);    /* add 5 to indices 2..7 */
    printf("After add(2,7,5): sum(0,9) = %lld (expected 85)\n", range_query(0, 9));
    printf("sum(3,5) = %lld (expected 27)\n", range_query(3, 5));

    return 0;
}
```

---

## 8. Implementation — Go

```go
// Square Root Decomposition — Range Sum Query + Point Update
// Language: Go
// Time:  Query O(√N), Update O(1)
// Space: O(N + √N)

package main

import (
	"fmt"
	"math"
)

// SqrtDecomposition holds the array and block sums.
type SqrtDecomposition struct {
	arr      []int
	blockSum []int
	n        int
	b        int // block size
}

// NewSqrtDecomp builds the structure from a slice.
// Time: O(N)
func NewSqrtDecomp(a []int) *SqrtDecomposition {
	n := len(a)
	b := int(math.Sqrt(float64(n)))
	if b == 0 {
		b = 1
	}

	numBlocks := (n + b - 1) / b
	arr := make([]int, n)
	blockSum := make([]int, numBlocks)

	copy(arr, a)
	for i, v := range a {
		blockSum[i/b] += v
	}

	return &SqrtDecomposition{arr: arr, blockSum: blockSum, n: n, b: b}
}

// Query returns sum of arr[L..R] inclusive (0-indexed).
// Time: O(√N)
func (s *SqrtDecomposition) Query(L, R int) int {
	result := 0
	blockL := L / s.b
	blockR := R / s.b

	if blockL == blockR {
		// Same block: iterate directly
		for i := L; i <= R; i++ {
			result += s.arr[i]
		}
		return result
	}

	// Left partial block
	leftEnd := (blockL+1)*s.b - 1
	for i := L; i <= leftEnd; i++ {
		result += s.arr[i]
	}

	// Middle complete blocks
	for b := blockL + 1; b <= blockR-1; b++ {
		result += s.blockSum[b]
	}

	// Right partial block
	rightStart := blockR * s.b
	for i := rightStart; i <= R; i++ {
		result += s.arr[i]
	}

	return result
}

// Update sets arr[i] = val.
// Time: O(1)
func (s *SqrtDecomposition) Update(i, val int) {
	blockID := i / s.b
	s.blockSum[blockID] -= s.arr[i]
	s.arr[i] = val
	s.blockSum[blockID] += val
}

// ─────────────────────────────────────────────────────────────
// Range Minimum Query using Sqrt Decomposition
// ─────────────────────────────────────────────────────────────

type SqrtRMQ struct {
	arr      []int
	blockMin []int
	n        int
	b        int
}

func NewSqrtRMQ(a []int) *SqrtRMQ {
	n := len(a)
	b := int(math.Sqrt(float64(n)))
	if b == 0 {
		b = 1
	}

	numBlocks := (n + b - 1) / b
	arr := make([]int, n)
	blockMin := make([]int, numBlocks)
	copy(arr, a)

	// Initialize block minimums to a large sentinel
	for i := range blockMin {
		blockMin[i] = math.MaxInt64
	}
	for i, v := range a {
		if v < blockMin[i/b] {
			blockMin[i/b] = v
		}
	}

	return &SqrtRMQ{arr: arr, blockMin: blockMin, n: n, b: b}
}

// QueryMin returns minimum value in arr[L..R].
func (s *SqrtRMQ) QueryMin(L, R int) int {
	mn := math.MaxInt64
	blockL := L / s.b
	blockR := R / s.b

	if blockL == blockR {
		for i := L; i <= R; i++ {
			if s.arr[i] < mn {
				mn = s.arr[i]
			}
		}
		return mn
	}

	// Left partial
	leftEnd := (blockL+1)*s.b - 1
	for i := L; i <= leftEnd; i++ {
		if s.arr[i] < mn {
			mn = s.arr[i]
		}
	}

	// Middle complete blocks
	for b := blockL + 1; b <= blockR-1; b++ {
		if s.blockMin[b] < mn {
			mn = s.blockMin[b]
		}
	}

	// Right partial
	rightStart := blockR * s.b
	for i := rightStart; i <= R; i++ {
		if s.arr[i] < mn {
			mn = s.arr[i]
		}
	}

	return mn
}

// UpdateMin updates arr[i] = val and rebuilds block min for that block.
// Time: O(B) = O(√N) because we must recompute the block's minimum.
// NOTE: Unlike sum, min requires full block rescan on update.
func (s *SqrtRMQ) UpdateMin(i, val int) {
	blockID := i / s.b
	s.arr[i] = val

	// Recompute block minimum
	blockStart := blockID * s.b
	blockEnd := min(blockStart+s.b, s.n) - 1
	s.blockMin[blockID] = math.MaxInt64
	for j := blockStart; j <= blockEnd; j++ {
		if s.arr[j] < s.blockMin[blockID] {
			s.blockMin[blockID] = s.arr[j]
		}
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ─────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────

func main() {
	fmt.Println("=== Range Sum Query ===")
	a := []int{3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8}
	sd := NewSqrtDecomp(a)

	fmt.Printf("Block size B = %d\n", sd.b)
	fmt.Printf("query(2,9)  = %d  (expected 35)\n", sd.Query(2, 9))
	fmt.Printf("query(0,11) = %d  (expected 52)\n", sd.Query(0, 11))

	sd.Update(4, 10)
	fmt.Printf("After update(4,10): query(2,9) = %d  (expected 40)\n", sd.Query(2, 9))

	fmt.Println("\n=== Range Minimum Query ===")
	rmq := NewSqrtRMQ(a)
	fmt.Printf("min(1,8)  = %d  (expected 1)\n", rmq.QueryMin(1, 8))
	fmt.Printf("min(5,11) = %d  (expected 2)\n", rmq.QueryMin(5, 11))

	rmq.UpdateMin(5, 0)
	fmt.Printf("After update(5,0): min(3,7) = %d  (expected 0)\n", rmq.QueryMin(3, 7))
}
```

---

## 9. Implementation — Rust

```rust
//! Square Root Decomposition — Comprehensive Implementation
//! Language: Rust
//!
//! Covers:
//!   1. Range Sum Query + Point Update
//!   2. Range Update (add) + Range Sum Query (lazy blocks)
//!   3. Range Minimum Query

use std::cmp;

// ─────────────────────────────────────────────────────────────
// 1. Range Sum Query + Point Update
// ─────────────────────────────────────────────────────────────

struct SqrtDecomp {
    arr: Vec<i64>,
    block_sum: Vec<i64>,
    n: usize,
    b: usize, // block size
}

impl SqrtDecomp {
    /// Build from a slice. Time: O(N).
    fn new(a: &[i64]) -> Self {
        let n = a.len();
        let b = cmp::max(1, (n as f64).sqrt() as usize);
        let num_blocks = (n + b - 1) / b;

        let arr = a.to_vec();
        let mut block_sum = vec![0i64; num_blocks];

        for (i, &v) in arr.iter().enumerate() {
            block_sum[i / b] += v;
        }

        SqrtDecomp { arr, block_sum, n, b }
    }

    /// Range sum query [L, R] inclusive. Time: O(√N).
    fn query(&self, l: usize, r: usize) -> i64 {
        let block_l = l / self.b;
        let block_r = r / self.b;
        let mut result = 0i64;

        if block_l == block_r {
            // Same block: iterate
            return self.arr[l..=r].iter().sum();
        }

        // Left partial block
        let left_end = (block_l + 1) * self.b - 1;
        result += self.arr[l..=left_end].iter().sum::<i64>();

        // Complete middle blocks
        for b in (block_l + 1)..block_r {
            result += self.block_sum[b];
        }

        // Right partial block
        let right_start = block_r * self.b;
        result += self.arr[right_start..=r].iter().sum::<i64>();

        result
    }

    /// Point update: set arr[i] = val. Time: O(1).
    fn update(&mut self, i: usize, val: i64) {
        let block_id = i / self.b;
        self.block_sum[block_id] -= self.arr[i];
        self.arr[i] = val;
        self.block_sum[block_id] += val;
    }
}

// ─────────────────────────────────────────────────────────────
// 2. Range Add Update + Range Sum Query (Lazy Blocks)
// ─────────────────────────────────────────────────────────────

struct SqrtLazy {
    arr: Vec<i64>,
    block_sum: Vec<i64>,
    lazy: Vec<i64>,    // pending addition per block
    n: usize,
    b: usize,
    num_blocks: usize,
}

impl SqrtLazy {
    fn new(a: &[i64]) -> Self {
        let n = a.len();
        let b = cmp::max(1, (n as f64).sqrt() as usize);
        let num_blocks = (n + b - 1) / b;

        let arr = a.to_vec();
        let mut block_sum = vec![0i64; num_blocks];
        let lazy = vec![0i64; num_blocks];

        for (i, &v) in arr.iter().enumerate() {
            block_sum[i / b] += v;
        }

        SqrtLazy { arr, block_sum, lazy, n, b, num_blocks }
    }

    /// Returns the actual block size for block b (last block may be smaller).
    fn block_len(&self, b: usize) -> usize {
        let start = b * self.b;
        let end = cmp::min(start + self.b, self.n);
        end - start
    }

    /// Range add: add val to all arr[L..=R]. Time: O(√N).
    fn range_add(&mut self, l: usize, r: usize, val: i64) {
        let block_l = l / self.b;
        let block_r = r / self.b;

        if block_l == block_r {
            for i in l..=r {
                self.arr[i] += val;
                self.block_sum[block_l] += val;
            }
            return;
        }

        // Left partial
        let left_end = (block_l + 1) * self.b - 1;
        for i in l..=left_end {
            self.arr[i] += val;
            self.block_sum[block_l] += val;
        }

        // Complete middle blocks: only update lazy
        for b in (block_l + 1)..block_r {
            self.lazy[b] += val;
        }

        // Right partial
        let right_start = block_r * self.b;
        for i in right_start..=r {
            self.arr[i] += val;
            self.block_sum[block_r] += val;
        }
    }

    /// Range sum query. Time: O(√N).
    ///
    /// For partial blocks: each element is arr[i] + lazy[block].
    /// For full blocks: block_sum[b] + lazy[b] * block_len(b).
    fn range_query(&self, l: usize, r: usize) -> i64 {
        let block_l = l / self.b;
        let block_r = r / self.b;
        let mut result = 0i64;

        if block_l == block_r {
            for i in l..=r {
                result += self.arr[i] + self.lazy[block_l];
            }
            return result;
        }

        // Left partial
        let left_end = (block_l + 1) * self.b - 1;
        for i in l..=left_end {
            result += self.arr[i] + self.lazy[block_l];
        }

        // Complete middle blocks
        for b in (block_l + 1)..block_r {
            result += self.block_sum[b] + self.lazy[b] * self.block_len(b) as i64;
        }

        // Right partial
        let right_start = block_r * self.b;
        for i in right_start..=r {
            result += self.arr[i] + self.lazy[block_r];
        }

        result
    }
}

// ─────────────────────────────────────────────────────────────
// 3. Range Minimum Query
// ─────────────────────────────────────────────────────────────

struct SqrtRMQ {
    arr: Vec<i64>,
    block_min: Vec<i64>,
    n: usize,
    b: usize,
}

impl SqrtRMQ {
    fn new(a: &[i64]) -> Self {
        let n = a.len();
        let b = cmp::max(1, (n as f64).sqrt() as usize);
        let num_blocks = (n + b - 1) / b;

        let arr = a.to_vec();
        let mut block_min = vec![i64::MAX; num_blocks];

        for (i, &v) in arr.iter().enumerate() {
            block_min[i / b] = cmp::min(block_min[i / b], v);
        }

        SqrtRMQ { arr, block_min, n, b }
    }

    /// Range minimum query [L, R]. Time: O(√N).
    fn query_min(&self, l: usize, r: usize) -> i64 {
        let block_l = l / self.b;
        let block_r = r / self.b;
        let mut mn = i64::MAX;

        if block_l == block_r {
            return *self.arr[l..=r].iter().min().unwrap();
        }

        // Left partial
        let left_end = (block_l + 1) * self.b - 1;
        mn = cmp::min(mn, *self.arr[l..=left_end].iter().min().unwrap());

        // Complete middle blocks
        for b in (block_l + 1)..block_r {
            mn = cmp::min(mn, self.block_min[b]);
        }

        // Right partial
        let right_start = block_r * self.b;
        mn = cmp::min(mn, *self.arr[right_start..=r].iter().min().unwrap());

        mn
    }

    /// Point update: set arr[i] = val. Requires block rescan. Time: O(√N).
    /// NOTE: Unlike sum, minimum requires full block rescan.
    fn update_min(&mut self, i: usize, val: i64) {
        let block_id = i / self.b;
        self.arr[i] = val;

        let start = block_id * self.b;
        let end = cmp::min(start + self.b, self.n);
        self.block_min[block_id] = *self.arr[start..end].iter().min().unwrap();
    }
}

// ─────────────────────────────────────────────────────────────
// Demo
// ─────────────────────────────────────────────────────────────

fn main() {
    println!("=== Range Sum Query + Point Update ===");
    let a: Vec<i64> = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8];
    let mut sd = SqrtDecomp::new(&a);

    println!("Block size B = {}", sd.b);
    println!("query(2,9)  = {}  (expected 35)", sd.query(2, 9));
    println!("query(0,11) = {}  (expected 52)", sd.query(0, 11));

    sd.update(4, 10);
    println!("After update(4,10): query(2,9) = {}  (expected 40)", sd.query(2, 9));

    println!("\n=== Range Add + Range Sum (Lazy) ===");
    let b: Vec<i64> = (1..=10).collect();
    let mut sl = SqrtLazy::new(&b);

    println!("sum(0,9)  = {}  (expected 55)", sl.range_query(0, 9));
    sl.range_add(2, 7, 5);
    println!("After add(2,7,+5): sum(0,9) = {}  (expected 85)", sl.range_query(0, 9));
    println!("sum(3,5) = {}  (expected 27)", sl.range_query(3, 5));

    println!("\n=== Range Minimum Query ===");
    let c: Vec<i64> = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3];
    let mut rmq = SqrtRMQ::new(&c);

    println!("min(0,9) = {}  (expected 1)", rmq.query_min(0, 9));
    println!("min(5,9) = {}  (expected 2)", rmq.query_min(5, 9));

    rmq.update_min(5, 0);
    println!("After update(5,0): min(4,8) = {}  (expected 0)", rmq.query_min(4, 8));
}
```

---

## 10. Range Minimum Query (RMQ)

### Key Difference from Sum

With **sum**, block aggregates can be maintained in O(1) on point updates:
```
block_sum[b] -= old_value
block_sum[b] += new_value
```

With **minimum**, this is NOT possible in O(1):
```
If we decrease a value: new minimum might be this value. Easy.
If we increase a value that WAS the minimum: we must scan the whole
  block to find the new minimum. O(B) = O(√N).
```

This is a **fundamental asymmetry** in min/max vs sum/xor aggregates.

```
OPERATION COST TABLE:

              | Sum/XOR | Min/Max
--------------+---------+--------
Point update  |  O(1)   |  O(√N)
Range query   |  O(√N)  |  O(√N)
```

---

## 11. Range Update + Range Query (Lazy Block)

### The Lazy Concept

**Lazy** (from Latin *laziness*) means "defer work until necessary."

When we add a value to an entire block, instead of updating all B elements one by one (O(B)), we store the pending addition in `lazy[block]` and apply it only when we actually need individual element values.

```
BEFORE range_add(1, 8, +5):

  Index:  0   1   2   3 | 4   5   6   7 | 8   9
  arr:  [ 1   2   3   4 | 5   6   7   8 | 9  10 ]
  lazy: [ 0               0               0     ]

  Query [0,9] = 1+2+3+4+5+6+7+8+9+10 = 55

──────────────────────────────────────────────────

AFTER range_add(1, 8, +5):
  Indices 1..3 → partial block 0 → update arr directly
  Indices 4..7 → full block 1   → lazy[1] += 5
  Index 8      → partial block 2 → update arr directly

  arr:  [ 1   7   8   9 | 5   6   7   8 | 14  10 ]
                    ^^^            ^^^     ^^^
                    +5 applied     raw     +5 applied
  lazy: [ 0               5               0     ]

  Query [0,9]:
    Block 0 (partial): arr[0..3] with lazy[0]=0 → 1+7+8+9 = 25
    Block 1 (full):    block_sum[1] + lazy[1]*4  = 26 + 20 = 46
    Block 2 (partial): arr[8..9] with lazy[2]=0  → 14+10 = 24
    Total = 25 + 46 + 24 = ... wait, we want [0,9]:
    Actually 1+7+8+9 + (5+6+7+8)+5*4 + 14+10 = 25 + 46 + 24 = 95 - wait

  Let me recalculate with correct expected:
  Original: 1..10 = 55
  Add 5 to indices 1..8: 8 elements * 5 = 40
  New total = 55 + 40 = 95 ✓
```

### Lazy Tag Invariant (Critical)

```
INVARIANT:
  The actual value at index i = arr[i] + lazy[i/B]
  block_sum[b] = sum of raw arr[b*B .. (b+1)*B-1] (WITHOUT lazy applied)
  Actual block sum = block_sum[b] + lazy[b] * block_len(b)

When querying a PARTIAL block, for each element i in the block:
  actual[i] = arr[i] + lazy[block_of_i]

When querying a FULL block b:
  actual sum = block_sum[b] + lazy[b] * block_len(b)
```

---

## 12. Mo's Algorithm (Offline Queries)

### What is an Offline Algorithm?

An **offline algorithm** reads ALL queries first before answering any of them. This allows reordering the queries for efficiency.

**Online** = must answer each query before receiving the next (real-time).
**Offline** = all queries known in advance, can be batched/reordered.

### The Core Problem Mo's Solves

```
Given: Array A[0..N-1]
Given: Q range queries [L_i, R_i]
Goal:  Answer some function f(L, R) for each query.

f can be: number of distinct elements, count of occurrences,
          frequency-based answers, etc.

Constraint: f must be EXTENDABLE and SHRINKABLE.
  add(i)    → extend current window to include index i
  remove(i) → shrink current window to exclude index i
```

### Mo's Key Insight

If current window is [curL, curR] and next query is [L, R]:
- Naive: recompute from scratch → O(N) per query → O(QN) total
- Mo's: move the endpoints incrementally

The trick is to **sort queries** so that the total movement of endpoints is minimized.

### Mo's Ordering

```
Sort queries by (block_of_L, R):
  - Primary sort: block that L falls in
  - Secondary sort: R value (ascending if block is even, descending if odd)

The "odd-even trick" (also called Hilbert curve ordering) cuts the
constant factor roughly in half.
```

### Why Does This Work?

```
Total movement analysis for N elements and Q queries, block size B = √N:

  Movement of R:
    Within each block of L: R is monotonically increasing (or decreasing)
    → R moves at most N per block-group
    → There are ceil(Q/B) distinct L-blocks
    → But actually R moves O(N) per L-block group
    → Total R movement = O(N * N/B) = O(N * √N)   [N/B blocks]

  Wait, let me redo:
    There are ceil(N/B) ≈ √N L-block groups
    Within each group, R moves at most N (monotonically)
    Total R movement = √N * N = N√N

  Movement of L:
    Within a single L-block group, L moves at most B = √N per query
    For Q queries: O(Q * √N)

  Total = O(N√N + Q√N) = O((N+Q)√N)
```

### Mo's Algorithm ASCII Flow

```
PREPROCESSING:
  B = sqrt(N)
  For each query i: block_i = L_i / B

SORT queries:
  Compare (q1, q2):
    if block(q1.L) != block(q2.L): sort by block ascending
    else if block is ODD: sort by R ascending
    else (block is EVEN): sort by R descending  [optional optimization]

PROCESS:
  curL = 0, curR = -1   (empty window)
  result[0..Q-1] = uninitialized

  For each query (L, R) in sorted order:
    While curR < R: curR++; add(arr[curR])
    While curL > L: curL--; add(arr[curL])
    While curR > R: remove(arr[curR]); curR--
    While curL < L: remove(arr[curL]); curL++
    result[query_index] = current_answer

NOTE: The ORDER of pointer movements matters!
  Expand before shrinking to keep window valid.
```

### Mo's Order of Pointer Movements

```
CORRECT ORDER:
  1. Extend R first (curR < R)  → adds elements
  2. Extend L left (curL > L)   → adds elements
  3. Shrink R (curR > R)        → removes elements
  4. Shrink L right (curL < L)  → removes elements

WHY: We must never have curR < curL (invalid window).
  Expanding before shrinking prevents this.
```

---

## 13. Mo's Algorithm Implementations

### C — Mo's Algorithm (Count Distinct Elements)

```c
/*
 * Mo's Algorithm: Count Distinct Elements in Range
 *
 * Given array A[0..N-1] and Q queries [L, R],
 * answer: how many distinct values in A[L..R]?
 *
 * Time:  O((N+Q)√N)
 * Space: O(N + Q)
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#define MAXN  100005
#define MAXQ  100005
#define MAXVAL 1000005  /* value range */

typedef struct {
    int L, R, idx;      /* query range and original index */
} Query;

int arr[MAXN];
int freq[MAXVAL];       /* frequency of each value in current window */
int current_answer;     /* current distinct count */
int block_size;
int N, Q;

/* Comparator for Mo's ordering */
int cmp_query(const void *a, const void *b) {
    Query *qa = (Query *)a;
    Query *qb = (Query *)b;

    int ba = qa->L / block_size;
    int bb = qb->L / block_size;

    if (ba != bb) return ba - bb;

    /* Within same block: alternate R direction for optimization */
    if (ba & 1) return qb->R - qa->R;   /* odd block: R descending */
    return qa->R - qb->R;               /* even block: R ascending */
}

/* Add element at index i to the current window */
void add_element(int i) {
    freq[arr[i]]++;
    if (freq[arr[i]] == 1) current_answer++;   /* new distinct element */
}

/* Remove element at index i from the current window */
void remove_element(int i) {
    freq[arr[i]]--;
    if (freq[arr[i]] == 0) current_answer--;   /* element gone from window */
}

int mo_query(Query *queries, int *answers) {
    int curL = 0, curR = -1;
    current_answer = 0;
    memset(freq, 0, sizeof(freq));

    for (int q = 0; q < Q; q++) {
        int L = queries[q].L;
        int R = queries[q].R;

        /* Expand R */
        while (curR < R) { curR++; add_element(curR); }
        /* Expand L leftward */
        while (curL > L) { curL--; add_element(curL); }
        /* Shrink R */
        while (curR > R) { remove_element(curR); curR--; }
        /* Shrink L rightward */
        while (curL < L) { remove_element(curL); curL++; }

        answers[queries[q].idx] = current_answer;
    }

    return 0;
}

int main(void) {
    int a[] = {1, 3, 2, 1, 3, 5, 2, 4};
    N = 8;
    Q = 4;

    for (int i = 0; i < N; i++) arr[i] = a[i];

    block_size = (int)sqrt((double)N);
    if (block_size == 0) block_size = 1;

    Query queries[MAXQ];
    queries[0] = (Query){0, 4, 0};   /* [0,4]: {1,3,2,1,3} → 3 distinct */
    queries[1] = (Query){1, 6, 1};   /* [1,6]: {3,2,1,3,5,2} → 4 distinct */
    queries[2] = (Query){2, 2, 2};   /* [2,2]: {2} → 1 distinct */
    queries[3] = (Query){0, 7, 3};   /* [0,7]: all → 5 distinct */

    qsort(queries, Q, sizeof(Query), cmp_query);

    int answers[MAXQ];
    mo_query(queries, answers);

    printf("Query [0,4] distinct = %d (expected 3)\n", answers[0]);
    printf("Query [1,6] distinct = %d (expected 4)\n", answers[1]);
    printf("Query [2,2] distinct = %d (expected 1)\n", answers[2]);
    printf("Query [0,7] distinct = %d (expected 5)\n", answers[3]);

    return 0;
}
```

### Go — Mo's Algorithm

```go
// Mo's Algorithm: Count Distinct Elements
// Language: Go

package main

import (
	"fmt"
	"math"
	"sort"
)

type Query struct {
	L, R, idx int
}

type MoSolver struct {
	arr         []int
	freq        map[int]int
	curAnswer   int
	blockSize   int
}

func NewMoSolver(a []int) *MoSolver {
	b := int(math.Sqrt(float64(len(a))))
	if b == 0 {
		b = 1
	}
	return &MoSolver{
		arr:       a,
		freq:      make(map[int]int),
		blockSize: b,
	}
}

func (m *MoSolver) addElement(i int) {
	v := m.arr[i]
	m.freq[v]++
	if m.freq[v] == 1 {
		m.curAnswer++
	}
}

func (m *MoSolver) removeElement(i int) {
	v := m.arr[i]
	m.freq[v]--
	if m.freq[v] == 0 {
		delete(m.freq, v)
		m.curAnswer--
	}
}

// Solve answers all queries offline.
// Returns answers indexed by original query index.
func (m *MoSolver) Solve(queries []Query) []int {
	n := len(queries)
	answers := make([]int, n)

	// Sort by Mo's ordering
	sort.Slice(queries, func(i, j int) bool {
		bi := queries[i].L / m.blockSize
		bj := queries[j].L / m.blockSize
		if bi != bj {
			return bi < bj
		}
		if bi&1 == 1 {
			return queries[i].R > queries[j].R // odd block: R descending
		}
		return queries[i].R < queries[j].R // even block: R ascending
	})

	curL, curR := 0, -1
	m.curAnswer = 0

	for _, q := range queries {
		L, R := q.L, q.R

		for curR < R { curR++; m.addElement(curR) }
		for curL > L { curL--; m.addElement(curL) }
		for curR > R { m.removeElement(curR); curR-- }
		for curL < L { m.removeElement(curL); curL++ }

		answers[q.idx] = m.curAnswer
	}

	return answers
}

func main() {
	a := []int{1, 3, 2, 1, 3, 5, 2, 4}
	solver := NewMoSolver(a)

	queries := []Query{
		{0, 4, 0},
		{1, 6, 1},
		{2, 2, 2},
		{0, 7, 3},
	}

	answers := solver.Solve(queries)

	fmt.Printf("Query [0,4] distinct = %d (expected 3)\n", answers[0])
	fmt.Printf("Query [1,6] distinct = %d (expected 4)\n", answers[1])
	fmt.Printf("Query [2,2] distinct = %d (expected 1)\n", answers[2])
	fmt.Printf("Query [0,7] distinct = %d (expected 5)\n", answers[3])
}
```

### Rust — Mo's Algorithm

```rust
//! Mo's Algorithm — Count Distinct Elements in Range
//! Language: Rust

use std::collections::HashMap;

struct MoSolver {
    arr: Vec<i32>,
    freq: HashMap<i32, usize>,
    cur_answer: usize,
    block_size: usize,
}

#[derive(Clone)]
struct Query {
    l: usize,
    r: usize,
    idx: usize,
}

impl MoSolver {
    fn new(a: Vec<i32>) -> Self {
        let b = (a.len() as f64).sqrt() as usize;
        let b = b.max(1);
        MoSolver {
            arr: a,
            freq: HashMap::new(),
            cur_answer: 0,
            block_size: b,
        }
    }

    fn add(&mut self, i: usize) {
        let v = self.arr[i];
        let cnt = self.freq.entry(v).or_insert(0);
        if *cnt == 0 { self.cur_answer += 1; }
        *cnt += 1;
    }

    fn remove(&mut self, i: usize) {
        let v = self.arr[i];
        let cnt = self.freq.entry(v).or_insert(0);
        *cnt -= 1;
        if *cnt == 0 { self.cur_answer -= 1; }
    }

    fn solve(&mut self, mut queries: Vec<Query>) -> Vec<usize> {
        let b = self.block_size;
        let n = queries.len();
        let mut answers = vec![0usize; n];

        queries.sort_unstable_by(|a, b_q| {
            let ba = a.l / b;
            let bb = b_q.l / b;
            if ba != bb { return ba.cmp(&bb); }
            if ba & 1 == 1 { b_q.r.cmp(&a.r) } else { a.r.cmp(&b_q.r) }
        });

        let (mut cur_l, mut cur_r) = (0usize, 0usize);
        // Use wrapping to handle cur_r = usize::MAX as "empty" (-1)
        let mut initialized = false;

        for q in &queries {
            let (l, r) = (q.l, q.r);

            if !initialized {
                // Initialize window to [l, l]
                cur_l = l;
                cur_r = l;
                self.add(l);
                initialized = true;
            }

            while cur_r < r { cur_r += 1; self.add(cur_r); }
            while cur_l > l { cur_l -= 1; self.add(cur_l); }
            while cur_r > r { self.remove(cur_r); cur_r -= 1; }
            while cur_l < l { self.remove(cur_l); cur_l += 1; }

            answers[q.idx] = self.cur_answer;
        }

        answers
    }
}

fn main() {
    let a = vec![1i32, 3, 2, 1, 3, 5, 2, 4];
    let mut solver = MoSolver::new(a);

    let queries = vec![
        Query { l: 0, r: 4, idx: 0 },
        Query { l: 1, r: 6, idx: 1 },
        Query { l: 2, r: 2, idx: 2 },
        Query { l: 0, r: 7, idx: 3 },
    ];

    let answers = solver.solve(queries);

    println!("Query [0,4] distinct = {}  (expected 3)", answers[0]);
    println!("Query [1,6] distinct = {}  (expected 4)", answers[1]);
    println!("Query [2,2] distinct = {}  (expected 1)", answers[2]);
    println!("Query [0,7] distinct = {}  (expected 5)", answers[3]);
}
```

---

## 14. Sqrt Decomposition on Strings

### Problem: Range Frequency Query

```
Given string S, answer Q queries:
  query(L, R, c): How many times does character c appear in S[L..R]?

Naive: O(N) per query = O(QN) total
Sqrt:  O(√N) per query
```

### Data Structure

```
For each block b and each character c (a-z):
  block_freq[b][c] = count of c in block b

Build: O(N * 26) = O(N)
Query: O(B + N/B) * 26 → still O(√N) because 26 is constant

Prefix approach (faster query):
  prefix_freq[i][c] = count of c in S[0..i-1]
  But prefix approach is O(26*N) space and O(1) query per character.
  For 26 chars × 10^5 = 2.6×10^6 — acceptable!
  But sqrt is more general for arbitrary predicates.
```

### C Implementation — Frequency Query

```c
/*
 * Sqrt Decomposition on Strings
 * Range Frequency Query: count occurrences of char c in S[L..R]
 */

#include <stdio.h>
#include <string.h>
#include <math.h>

#define MAXN 100005
#define ALPHA 26

char str[MAXN];
int  block_freq[320][ALPHA];   /* block_freq[b][c] */
int  N, B;

void build(const char *s, int n) {
    N = n;
    B = (int)sqrt((double)n);
    if (B == 0) B = 1;

    memset(block_freq, 0, sizeof(block_freq));
    for (int i = 0; i < n; i++) {
        str[i] = s[i];
        block_freq[i / B][s[i] - 'a']++;
    }
}

int query_freq(int L, int R, char c) {
    int ci = c - 'a';
    int count = 0;
    int block_L = L / B;
    int block_R = R / B;

    if (block_L == block_R) {
        for (int i = L; i <= R; i++)
            if (str[i] == c) count++;
        return count;
    }

    /* Left partial */
    int left_end = (block_L + 1) * B - 1;
    for (int i = L; i <= left_end; i++)
        if (str[i] == c) count++;

    /* Middle full blocks */
    for (int b = block_L + 1; b <= block_R - 1; b++)
        count += block_freq[b][ci];

    /* Right partial */
    int right_start = block_R * B;
    for (int i = right_start; i <= R; i++)
        if (str[i] == c) count++;

    return count;
}

/* Point update: change character at position i */
void update_char(int i, char new_c) {
    int block_id = i / B;
    block_freq[block_id][str[i] - 'a']--;
    str[i] = new_c;
    block_freq[block_id][new_c - 'a']++;
}

int main(void) {
    const char *s = "abracadabra";
    int n = 11;
    build(s, n);

    printf("freq('a', [0,10]) = %d  (expected 5)\n", query_freq(0, 10, 'a'));
    printf("freq('r', [0,4])  = %d  (expected 1)\n", query_freq(0, 4, 'r'));

    update_char(1, 'a');  /* 'b' → 'a' at index 1 */
    printf("After update: freq('a', [0,3]) = %d  (expected 3)\n",
           query_freq(0, 3, 'a'));

    return 0;
}
```

---

## 15. Sqrt Decomposition on Trees (Heavy Path Intuition)

### The Basic Idea

Trees don't have natural "blocks" like arrays. But we can apply sqrt thinking using:

1. **Centroid decomposition** (block by depth/subtree size)
2. **Path queries with sqrt chunking** on Euler tour / DFS order
3. **Heavy-light decomposition** (a more refined version)

### Sqrt Chunking on DFS Order

```
Given: Tree with N nodes, Q path queries "sum of values from u to v"

Approach:
  1. Flatten tree to array using DFS (in-order traversal)
  2. Apply sqrt decomposition on the flattened array
  3. For path queries, convert to range on flattened array

This requires LCA (Lowest Common Ancestor) to correctly convert
path u→v into one or two array ranges.
```

### Block Cut Tree (Conceptual)

```
For trees, a "block" is a group of √N nodes processed together.
Any path between two nodes crosses at most 2√N block boundaries.

This gives path queries in O(√N) time.
```

---

## 16. Complexity Analysis Deep Dive

### Choosing the Optimal Block Size

```
General formula: if query cost = O(B + N/B + X) and update cost = O(Y + B):

  Optimal B = sqrt(N) assuming X, Y are constants.

  If query scans partial blocks in O(B * f) and full blocks in O((N/B) * g):
    Minimize: B*f + (N/B)*g
    Derivative = f - Ng/B² = 0
    B = sqrt(Ng/f)

  Example: If full-block query is O(1) (precomputed) but
           partial-block query has cost 2x of element scan:
    B = sqrt(N * 1 / 2) = sqrt(N/2) ≈ 0.7 * sqrt(N)
```

### Complexity Summary Table

```
Operation             | Naive   | Sqrt Decomp | Segment Tree | Fenwick Tree
──────────────────────┼─────────┼─────────────┼──────────────┼─────────────
Build                 | O(N)    | O(N)        | O(N)         | O(N)
Point update (sum)    | O(1)    | O(1)        | O(log N)     | O(log N)
Range query (sum)     | O(N)    | O(√N)       | O(log N)     | O(log N)
Range update (add)    | O(N)    | O(√N)       | O(log N)     | O(log N)
Range query after RU  | O(N)    | O(√N)       | O(log N)     | O(log N)
Point update (min)    | O(1)    | O(√N)       | O(log N)     | N/A
Range query (min)     | O(N)    | O(√N)       | O(log N)     | N/A
Mo's offline queries  | O(QN)   | O((N+Q)√N)  | —            | —
Implementation ease   | Easy    | Easy        | Medium       | Medium
```

### When N and Q are Large

```
N = 10^5, Q = 10^5:

  Naive approach:   Q * N = 10^10 → TOO SLOW (~100 seconds)
  Sqrt approach:    Q * √N = 10^5 * 316 ≈ 3.16 × 10^7 → FAST (~0.3 seconds)
  Segment Tree:     Q * log N = 10^5 * 17 ≈ 1.7 × 10^6 → VERY FAST

  Sqrt vs Segment Tree:
    Sqrt is ~18x slower than segment tree for simple ops
    BUT sqrt has lower constant factors in practice for complex operations
    AND sqrt is much simpler to implement correctly
```

---

## 17. Comparison: Sqrt vs Segment Tree vs Fenwick Tree

### When to Choose Sqrt Decomposition

```
USE SQRT when:
  ✓ Query/update function is complex (not just sum/min/max)
  ✓ You need Mo's algorithm (offline range queries)
  ✓ The aggregation function is hard to "merge" (segment trees need merge)
  ✓ Implementation simplicity is paramount in contest
  ✓ Operations are non-invertible (segment tree needs lazy; sqrt uses brute force on partial)
  ✓ N ≤ 10^5 and O(√N) per operation is sufficient

USE SEGMENT TREE when:
  ✓ O(log N) is required (N or Q up to 10^6, 10^7)
  ✓ Complex range updates + range queries (with lazy propagation)
  ✓ Merging operations are well-defined

USE FENWICK TREE when:
  ✓ Only prefix sums/products (queries always from index 0)
  ✓ Point update + prefix query
  ✓ Lowest implementation overhead
```

### The "Hardness Spectrum"

```
HARD TO IMPLEMENT ──────────────────────────────────── EASY TO IMPLEMENT

  Persistent Seg Tree → Seg Tree → Fenwick → Sqrt Decomp → Prefix Sum

SLOW ──────────────────────────────────────────────────────────── FAST

  O(N) naive → O(√N) sqrt → O(log N) seg tree → O(1) sparse table (static)
```

---

## 18. Common Patterns & Template Thinking

### Pattern 1: Block Preprocessing

```
Template:
  1. Choose block size B = sqrt(N) or tune empirically
  2. For each block b:
       block_agg[b] = aggregate(arr[b*B .. min((b+1)*B-1, N-1)])
  3. Query [L, R]:
       Handle left partial, full middle blocks, right partial
  4. Update:
       Modify arr[i], recompute block_agg[i/B]
```

### Pattern 2: Lazy Block Update

```
Template:
  - lazy[b]: pending operation on all elements of block b
  - For range update [L, R] with val:
      Partial blocks: apply directly to arr[i] and block_agg[b]
      Full blocks: lazy[b] += val (deferred)
  - For query:
      Partial blocks: actual value = arr[i] + lazy[block(i)]
      Full blocks: block_agg[b] + f(lazy[b], block_len(b))
```

### Pattern 3: Mo's Template

```
Template:
  struct Query { int L, R, idx; }
  sort by (L/B, R with alternating direction)

  add(i), remove(i): O(1) per call
  curL, curR: maintain current window

  For each sorted query:
    expand/shrink curL and curR to match query
    record answer
```

### Pattern 4: Block-Wise Invariant

```
At ALL times (invariant):
  block_agg[b] is correct for the current state of arr[]
  lazy[b] is a pending offset/multiplier not yet applied to arr[]

After any update, immediately fix the invariant.
Never leave the structure in an inconsistent state.
```

---

## 19. Common Mistakes & Pitfalls

### Mistake 1: Off-by-One in Block Boundaries

```
WRONG:
  left_end = block_L * B + B - 1      // This is (block_L+1)*B - 1
  left_end = (block_L + 1) * B        // This goes one too far

CORRECT:
  left_end = (block_L + 1) * B - 1    // Last index of block_L
  right_start = block_R * B           // First index of block_R
```

### Mistake 2: Last Block Size

```
If N = 10 and B = 3:
  Block 0: indices 0,1,2    (size 3)
  Block 1: indices 3,4,5    (size 3)
  Block 2: indices 6,7,8    (size 3)
  Block 3: indices 9        (size 1) ← NOT 3!

WRONG: Always assume block size = B
CORRECT: actual_size = min(B, N - b*B)
```

### Mistake 3: Forgetting the Same-Block Case

```
WRONG: Directly falling into left-partial + right-partial logic
       when L and R are in the same block.
       This gives L..left_end overlapping right_start..R.

CORRECT:
  if (block_L == block_R) {
    iterate L..R directly; return;
  }
  // Now handle partial-full-partial
```

### Mistake 4: Mo's Order of Pointer Movements

```
WRONG order (can create invalid window where curL > curR):
  while (curL < L) { remove(arr[curL]); curL++; }  // shrink first
  while (curR > R) { remove(arr[curR]); curR--; }  // then shrink
  while (curR < R) { curR++; add(arr[curR]); }     // then expand
  while (curL > L) { curL--; add(arr[curL]); }     // then expand

CORRECT: always EXPAND before SHRINK
  while (curR < R) { curR++; add(curR); }
  while (curL > L) { curL--; add(curL); }
  while (curR > R) { remove(curR); curR--; }
  while (curL < L) { remove(curL); curL++; }
```

### Mistake 5: Block Size = 0

```
If N = 0 or N = 1, sqrt(N) = 0 or 1.
Always guard: B = max(1, (int)sqrt(N))
```

### Mistake 6: RMQ Update O(1) Assumption

```
WRONG assumption: "I can update block_min in O(1) like block_sum"
REALITY: Increasing the minimum element requires re-scanning the
         entire block to find the new minimum. O(B) = O(√N).
```

---

## 20. Problem Set & Practice Ladder

### Level 1 — Foundation (Implement from scratch)

```
1. CSES - Static Range Sum Queries
   → Solve with prefix sum, then with sqrt to understand the difference

2. CSES - Dynamic Range Sum Queries
   → Classic point update + range sum

3. CSES - Range Minimum Queries
   → Classic, note the O(√N) update cost for min
```

### Level 2 — Standard (Apply the template)

```
4. Codeforces 86D - Powerful array
   → Mo's algorithm classic: sum of (freq[v])^2

5. Codeforces 940F - Machine Learning
   → Mo's with updates (Mo's on modifications, 3D Mo's)
   → Block size B = N^(2/3) for 3D Mo's

6. SPOJ DQUERY - D-Query
   → Count distinct elements in range (Mo's)
```

### Level 3 — Advanced (Combine with other structures)

```
7. Codeforces 617E - XOR and Favorite Number
   → Mo's with XOR prefix sums

8. Codeforces 1093G - Multidimensional Queries
   → Segment tree with sqrt-style blocks

9. Tree path queries with sqrt-ordered DFS traversal

10. Interval coloring with lazy sqrt blocks
```

### Level 4 — Expert (Derive the technique)

```
11. Offline LCT (Link-Cut Tree) simulation using sqrt batching

12. Sqrt decomposition on queries for problems with
    "snapshot" queries (answer state at time T)

13. Mo's algorithm with rollback (Mo's on trees)
```

---

## 21. Expert Mental Models & Cognitive Strategies

### Mental Model 1: The Ruler Analogy

Think of sqrt decomposition like measuring with a ruler that has two scales:
- **Coarse scale (blocks)**: gives fast approximate answers for big spans
- **Fine scale (individual elements)**: handles the edges precisely

A carpenter doesn't measure every millimeter when cutting a plank. They measure in feet/meters first, then adjust for centimeters at the ends. You're doing the same computationally.

### Mental Model 2: Lazy = "Put It on a Tab"

The lazy array is like running a bar tab. Instead of collecting payment each time someone orders (O(N) per round update), you note the total per table (O(1) per block), and only settle when a specific person needs their bill (partial block query).

### Mental Model 3: The √N Tradeoff Curve

Visualize this always when choosing block size:

```
Total cost = (query cost) = B + N/B

  Too small B → many blocks → full block scan is slow
  Too large B → partial blocks are slow to iterate
  Sweet spot  → B = √N
```

When you face an unfamiliar problem, ask:
> "What is my query cost as a function of B? What is my update cost as a function of B? Where do they balance?"

### Mental Model 4: Mo's as a Space-Filling Curve

Mo's sort order approximately traces a **Hilbert curve** through the 2D query space (L, R). This minimizes the total "distance" traveled when processing all queries. Any time you see offline range queries, think: "Can I sort these cleverly to minimize pointer movement?"

### Cognitive Principles for Mastery

**1. Chunking (George Miller, 1956)**
Sqrt decomposition IS chunking. You learn it by internalizing the pattern: "boundary partial + middle aggregate + boundary partial." Once chunked, this becomes one mental unit, not three steps.

**2. Deliberate Practice — The 3-Step Loop**
```
Step 1: Implement from memory (no reference)
Step 2: Test on edge cases (B=1, all same block, last block partial)
Step 3: Analyze: where did your mental model break down?
Repeat until the implementation flows without thought.
```

**3. Interleaved Practice (Roediger, 2006)**
Don't just practice sqrt in isolation. Alternate between:
- Sqrt + segment tree (same problem, two implementations)
- Mo's + offline sorting
- Lazy sqrt + Fenwick tree

This prevents the illusion of mastery and builds true adaptability.

**4. Transfer Learning — The Meta-Pattern**
Sqrt decomposition is an instance of a deeper pattern:
```
"When direct computation is O(N) and precomputation is O(N),
 find a block size B that balances both costs."
```
This same idea appears in:
- B-trees (disk I/O optimization, B = disk block size)
- Cache-oblivious algorithms
- Batch processing in databases
- Approximation algorithms (sample √N representatives)

Train your mind to recognize this pattern everywhere, not just in competitive programming.

**5. The Expert Checklist Before Coding**

```
BEFORE writing sqrt decomposition, answer these:
  □ What is my array? What are the elements?
  □ What is my query? Can it be answered per-block?
  □ What is my update? Does it affect block aggregates?
  □ Is this online or offline? (Mo's if offline)
  □ What is the block aggregate? (sum, min, max, xor, count?)
  □ Is the aggregate invertible? (sum yes, min no → update cost differs)
  □ What is N? What is Q? Is O(√N) per op fast enough?
  □ What edge cases exist? (B=1, single block, last block size)
```

---

## Summary — The Complete Picture

```
SQRT DECOMPOSITION — ONE-PAGE CHEATSHEET

Block size: B = floor(sqrt(N))
Num blocks: ceil(N / B)

BUILD:     For i in 0..N: block_agg[i/B] = combine(block_agg[i/B], arr[i])
           Time: O(N)

QUERY(L,R): if same block: iterate L..R directly
            else: partial(L..block_end) + full_blocks + partial(block_start..R)
            Time: O(√N)

UPDATE(i,v): block_agg[i/B] = recompute(remove old, add new)
             Time: O(1) for sum, O(√N) for min/max

LAZY UPDATE(L,R,val):
             Partial blocks: update arr + block_agg directly
             Full blocks: lazy[b] += val
             Time: O(√N)

MO'S (offline):
             Sort queries by (L/B, R with alternating direction)
             Maintain window [curL, curR], expand then shrink
             Time: O((N+Q)√N)

CHOOSE SQRT WHEN:
  - Operation too complex for segment tree
  - Offline range queries (Mo's)
  - Need simplicity over log-factor performance
  - N ≤ 10^5 with Q ≤ 10^5
```

---

*"Every expert was once a beginner who refused to give up on understanding."*

*Practice not until you get it right — practice until you cannot get it wrong.*

Now let me create the comprehensive guide:Here's your complete guide. Here's what's packed inside:

**Core Theory**
- Why √N is the mathematical sweet spot — derived from first principles with the optimization calculus
- Every vocabulary term defined before use (block, lazy, aggregate, invariant, offline/online, etc.)
- ASCII visualizations of block layout, query anatomy, and lazy update state

**All Major Variants Covered**
1. **Range Sum + Point Update** — the canonical form, all three languages
2. **Range Update + Range Sum (Lazy Blocks)** — with full invariant explanation
3. **Range Minimum Query** — including the critical asymmetry: min updates cost O(√N), not O(1)
4. **Mo's Algorithm** — full offline query ordering with alternating direction optimization
5. **String frequency queries** — sqrt on characters
6. **Tree path queries** — conceptual foundation

**Implementations in C, Go, Rust** — each idiomatic to the language, with:
- Guard conditions (B=0, last block partial size)
- Correct Mo's pointer expansion-before-shrink order
- Type safety (Rust `i64::MAX`, Go `math.MaxInt64`)

**Expert Insight: The Key Asymmetry Most Learners Miss**

> Sum aggregates → point update is O(1): `block_sum -= old; block_sum += new`
> Min/Max aggregates → point update is O(√N): must rescan the entire block

This is because subtraction is the inverse of addition, but "un-minimizing" has no inverse — you must look at all remaining elements.

**Mental model to carry forward:** Every time you see Q offline range queries, your first instinct should be — *"Can I sort these queries to minimize pointer movement? Mo's algorithm."*