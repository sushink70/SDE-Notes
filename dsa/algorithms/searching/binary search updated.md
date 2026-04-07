# Binary Search — Complete Engineering Reference

> **Summary (6 lines):** Binary search is a divide-and-conquer algorithm that locates a target in a sorted collection in O(log n) time by repeatedly halving the search space. Its correctness hinges on three invariants: the array must be sorted, the search space must be closed (inclusive bounds), and the midpoint calculation must avoid integer overflow. Beyond the canonical "find exact value" form, binary search generalizes to lower-bound, upper-bound, and predicate-based searches — the foundation of `std::lower_bound`, `sort.Search`, and `std::partition_point`. Common failure modes include off-by-one errors in loop termination, incorrect mid-point shrinkage direction, and applying it to unsorted data. The algorithm maps naturally to hardware: branch predictors love the regular comparison pattern, and cache lines cover small arrays entirely. Mastering binary search means mastering the skill of maintaining loop invariants under all boundary conditions.

---

## Table of Contents

1. [Theoretical Foundations](#1-theoretical-foundations)
2. [Loop Invariants and Correctness](#2-loop-invariants-and-correctness)
3. [Variants Taxonomy](#3-variants-taxonomy)
4. [Integer Overflow and Midpoint Safety](#4-integer-overflow-and-midpoint-safety)
5. [Complexity Analysis](#5-complexity-analysis)
6. [Implementation — C](#6-implementation--c)
7. [Implementation — Go](#7-implementation--go)
8. [Implementation — Rust](#8-implementation--rust)
9. [Architecture View](#9-architecture-view)
10. [Standard Library Mappings](#10-standard-library-mappings)
11. [Advanced Patterns](#11-advanced-patterns)
12. [Threat Model and Failure Modes](#12-threat-model-and-failure-modes)
13. [Testing, Fuzzing, and Benchmarks](#13-testing-fuzzing-and-benchmarks)
14. [Real-World Applications](#14-real-world-applications)
15. [Next 3 Steps](#15-next-3-steps)
16. [References](#16-references)

---

## 1. Theoretical Foundations

### 1.1 The Core Insight

Binary search operates on a fundamental observation: if a collection is **totally ordered** (every pair of elements has a defined relationship: a ≤ b or b ≤ a), then examining the middle element divides the remaining candidates into two halves. The target can only reside in one half. Each comparison eliminates half the remaining search space.

This is the definition of **logarithmic reduction**: starting from N elements, after one comparison we have N/2, after two we have N/4, after k comparisons we have N/2^k. When N/2^k = 1, we have k = log₂(N). Hence O(log n).

### 1.2 Prerequisites

Binary search has strict preconditions:

**Sorted order (the critical invariant):** The collection must be sorted in a consistent order. For custom types, the comparison function must define a **strict weak ordering**:
- Irreflexivity: `cmp(a, a) == false`
- Asymmetry: `cmp(a, b) == true` implies `cmp(b, a) == false`
- Transitivity: `cmp(a, b) && cmp(b, c)` implies `cmp(a, c)`

Violating any of these produces undefined behavior in standard library implementations.

**Random access in O(1):** The algorithm requires jumping to the middle element instantly. It works on arrays and array-backed slices. It does NOT work on linked lists (O(n) to reach middle), trees, or streams without buffering.

**Stable comparison semantics:** The comparison function must be pure (no side effects, deterministic). Impure comparators can cause infinite loops.

### 1.3 Historical Context

Binary search was first formally described by John Mauchly in 1946, but a **correct** general implementation without bugs took until 1962 (Bottenbruch). The classic "find exact value" implementation has a well-known bug in almost every textbook: the midpoint calculation `(lo + hi) / 2` overflows for large arrays. This bug existed in Java's standard library `Arrays.binarySearch` for nearly a decade until Jon Bentley identified it in 2006.

### 1.4 Mathematical Model

Given a sorted array `A[0..n-1]` and target `t`:

```
Problem: Find i such that A[i] == t, or report absence.

Invariant: If t exists in A, then t ∈ A[lo..hi] at all times.

Base case: lo > hi → t not in A.

Inductive step:
  mid = lo + (hi - lo) / 2
  if A[mid] == t  → found
  if A[mid] < t   → t ∈ A[mid+1..hi]  → lo = mid + 1
  if A[mid] > t   → t ∈ A[lo..mid-1]  → hi = mid - 1
```

The invariant is maintained at every step. The search space strictly shrinks (hi - lo decreases by at least 1 per iteration), guaranteeing termination.

---

## 2. Loop Invariants and Correctness

### 2.1 The Three Invariant Styles

There are three common ways to define the search space. Each leads to slightly different code. Confusing them is the primary source of bugs.

**Style 1: Closed interval [lo, hi]** — both endpoints are candidates.
```
lo = 0, hi = n-1
Loop: while lo <= hi
Shrink left:  lo = mid + 1
Shrink right: hi = mid - 1
```
This is the most common style. When the loop exits, lo > hi, meaning the search space is empty.

**Style 2: Half-open interval [lo, hi)** — lo is candidate, hi is one past the end.
```
lo = 0, hi = n
Loop: while lo < hi
Shrink left:  lo = mid + 1
Shrink right: hi = mid
```
This is the style used by C++ `lower_bound` and Go's `sort.Search`. When loop exits, lo == hi, pointing to the insertion point.

**Style 3: Open interval (lo, hi)** — neither endpoint is a candidate.
```
lo = -1, hi = n
Loop: while hi - lo > 1
Shrink left:  lo = mid
Shrink right: hi = mid
```
Useful for problems where you want to find the boundary between a predicate being false and true, without examining boundary elements directly.

### 2.2 Why Off-By-One Errors Happen

The most common mistake is mixing styles. For example, initializing `hi = n-1` (closed) but then using `hi = mid` (half-open shrinkage). This creates an infinite loop when `lo == mid`.

Consider `lo = 5, hi = 5, mid = 5, A[mid] > t`:
- With closed style: `hi = mid - 1 = 4` → loop exits (lo > hi). Correct.
- With mixed style: `hi = mid = 5` → loop does not shrink. **Infinite loop.**

### 2.3 Proving Termination

For the closed interval style, define the **potential function** φ = hi - lo + 1 (the number of candidates).

After each iteration:
- If `A[mid] == t`: terminates immediately.
- If `A[mid] < t`: lo becomes mid+1. New φ = hi - (mid+1) + 1 = hi - mid. Since mid ≥ lo, hi - mid ≤ hi - lo < φ. Strictly decreasing.
- If `A[mid] > t`: hi becomes mid-1. New φ = (mid-1) - lo + 1 = mid - lo. Since mid ≤ hi, mid - lo ≤ hi - lo < φ. Strictly decreasing.

Since φ is a non-negative integer that strictly decreases each iteration, the loop terminates.

---

## 3. Variants Taxonomy

```
Binary Search Variants
│
├── Exact Search
│   └── Find index i where A[i] == target (or -1)
│
├── Lower Bound (first occurrence / left boundary)
│   └── Find smallest i where A[i] >= target
│       Used for: insertion point left, first occurrence of duplicates
│
├── Upper Bound (right boundary)
│   └── Find smallest i where A[i] > target
│       Used for: insertion point right, one-past last occurrence of duplicates
│
├── Predicate Search
│   └── Given monotone predicate P, find first i where P(i) == true
│       (generalizes lower/upper bound; P can be arbitrary)
│
├── Rotated Array Search
│   └── Find target in sorted array rotated at unknown pivot
│
├── Search on Answer
│   └── Binary search over the answer space [lo, hi] where feasibility
│       of answer x is a monotone predicate
│       Examples: minimum k, optimal allocation, sqrt(n)
│
├── Exponential / Unbounded Search
│   └── For unknown-size sorted sequences: find range [2^k, 2^(k+1)]
│       containing target, then binary search within it
│
└── Fractional Cascading
    └── Multiple sorted arrays sharing structure; O(log n + k) queries
        after O(n log n) preprocessing
```

### 3.1 Lower Bound

Lower bound finds the **leftmost position** where target could be inserted while maintaining sort order. Equivalently, it finds the first element ≥ target.

```
Array: [1, 3, 3, 3, 5, 7]
         0  1  2  3  4  5

lower_bound(3) → 1   (first 3)
lower_bound(4) → 4   (insertion point, between 3 and 5)
lower_bound(0) → 0   (before all elements)
lower_bound(8) → 6   (after all elements, == n)
```

Count of occurrences of target = `upper_bound(target) - lower_bound(target)`.

### 3.2 Upper Bound

Upper bound finds the **rightmost insertion point** for target. First element strictly greater than target.

```
Array: [1, 3, 3, 3, 5, 7]
upper_bound(3) → 4   (one past last 3)
upper_bound(4) → 4   (same as lower_bound when target absent)
```

### 3.3 Predicate-Based Search (sort.Search style)

The most general form. Given a monotone boolean predicate P such that there exists some threshold k where:
- P(i) == false for i < k
- P(i) == true  for i >= k

Find k. This is exactly what Go's `sort.Search` and C++'s `std::partition_point` compute.

Every binary search variant reduces to predicate search:
- lower_bound(x): P(i) = (A[i] >= x)
- upper_bound(x): P(i) = (A[i] > x)
- exact search: lower_bound(x), then check if A[result] == x

### 3.4 Search on Answer (Binary Search over Value Space)

Many optimization problems can be solved by binary searching over the answer rather than over an array index.

**Pattern:**
```
lo = minimum_possible_answer
hi = maximum_possible_answer
while lo < hi:
    mid = lo + (hi - lo) / 2
    if feasible(mid):
        hi = mid        # mid might be the answer, keep it
    else:
        lo = mid + 1    # mid definitely not the answer
return lo
```

Examples:
- Minimum largest sum when splitting array into k groups
- Minimum speed to arrive before deadline
- Kth smallest element in a sorted matrix
- Integer square root

---

## 4. Integer Overflow and Midpoint Safety

### 4.1 The Classic Bug

The expression `(lo + hi) / 2` overflows when `lo + hi > INT_MAX`. For a 32-bit int, this occurs when searching arrays larger than ~1 billion elements. For a 64-bit int, it occurs at ~9 quintillion — unlikely for array indices but possible when doing "search on answer" over a value space.

```c
// WRONG: overflows when lo + hi > INT32_MAX
int mid = (lo + hi) / 2;

// CORRECT: equivalent, no overflow
int mid = lo + (hi - lo) / 2;

// ALSO CORRECT: uses unsigned right shift (works in C/C++ with unsigned)
size_t mid = ((size_t)lo + (size_t)hi) >> 1;
```

### 4.2 Why `lo + (hi - lo) / 2` is Safe

Since `hi >= lo` (loop invariant), `hi - lo >= 0`. Adding `lo` to a non-negative value that is at most `hi - lo` cannot exceed `hi`. No overflow if individual values fit in the type.

### 4.3 Rust's Approach

Rust's standard library uses `lo + (hi - lo) / 2` internally. For user-facing code, Rust provides `usize::midpoint(a, b)` (stable since 1.85) which computes the midpoint of two `usize` values without overflow using wrapping arithmetic:

```rust
// Equivalent to: lo + (hi - lo) / 2, but branchless
fn midpoint(a: usize, b: usize) -> usize {
    a + (b - a) / 2
}
```

### 4.4 Negative Index Concerns

When binary searching over a signed value space (e.g., answer space [-10^9, 10^9]), ensure `hi - lo` doesn't overflow for negative values:
```c
// If lo = -2^31 and hi = 2^31 - 1, then hi - lo overflows!
// Solution: cast to wider type
int64_t mid = (int64_t)lo + ((int64_t)hi - lo) / 2;
```

---

## 5. Complexity Analysis

### 5.1 Time Complexity

| Operation | Best | Average | Worst |
|-----------|------|---------|-------|
| Exact search | O(1) | O(log n) | O(log n) |
| Lower bound | O(log n) | O(log n) | O(log n) |
| Upper bound | O(log n) | O(log n) | O(log n) |
| Predicate search | O(log n) | O(log n) | O(log n) |

Note: Lower/upper bound do NOT terminate early on a match — they always do exactly ⌈log₂(n+1)⌉ iterations.

### 5.2 Space Complexity

Iterative binary search: **O(1)** auxiliary space. No stack frames, no allocations.

Recursive binary search: **O(log n)** stack space. Tail-recursive implementations can be optimized to O(1) by a compiler, but this is not guaranteed in C/Go/Rust without explicit tail call optimization.

**Always prefer iterative over recursive for production code.**

### 5.3 Exact Iteration Count

For an array of n elements:
- Minimum iterations: 1 (target is the first mid)
- Maximum iterations: ⌈log₂(n+1)⌉

Concrete values:

| n | max iterations |
|---|---------------|
| 10 | 4 |
| 100 | 7 |
| 1,000 | 10 |
| 10,000 | 14 |
| 1,000,000 | 20 |
| 1,000,000,000 | 30 |
| 2^63 | 63 |

### 5.4 Comparison with Linear Search

| n | Linear (avg) | Binary | Speedup |
|---|-------------|--------|---------|
| 100 | 50 | 7 | 7x |
| 10,000 | 5,000 | 14 | 357x |
| 1,000,000 | 500,000 | 20 | 25,000x |

However, for small n (< 16–32 elements), linear search often wins in practice due to:
- Cache effects (entire array fits in L1 cache)
- Branch predictor friendly sequential access
- No branch misprediction from comparison direction changes
- SIMD vectorization of linear scan

Modern implementations often use linear scan below a threshold and binary search above.

### 5.5 Cache Performance

Binary search has **poor cache behavior** for large arrays. Each comparison jumps to a new memory location:

```
Iteration 1: access index n/2     — likely cache miss (cold)
Iteration 2: access index n/4 or 3n/4 — likely cache miss
Iteration 3: access n/8 or similar — likely cache miss
...
Last ~3-4 iterations: within same cache line — hits
```

For a 64-byte cache line with 8-byte elements, the last 3 comparisons are cache-warm. All others are cold misses. This is why B-trees (which keep multiple keys per node) dramatically outperform binary-searched sorted arrays for large n: they amortize cache misses by extracting more information per miss.

**Practical threshold:** Binary search beats linear scan at roughly n > 64 / sizeof(element) elements (one cache line's worth).

---

## 6. Implementation — C

```c
// binary_search.c
// Compile: gcc -O2 -Wall -Wextra -std=c11 binary_search.c -o binary_search
// Test:    ./binary_search

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>
#include <time.h>

// =============================================================================
// 1. EXACT BINARY SEARCH — closed interval [lo, hi]
//    Returns index of target, or -1 if not found.
// =============================================================================
int binary_search(const int *arr, int n, int target) {
    int lo = 0;
    int hi = n - 1;

    while (lo <= hi) {
        // Safe midpoint: avoids (lo + hi) overflow
        int mid = lo + (hi - lo) / 2;

        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}

// =============================================================================
// 2. LOWER BOUND — half-open interval [lo, hi)
//    Returns the index of the first element >= target.
//    Returns n if all elements < target.
//    Invariant: arr[0..lo-1] < target, arr[hi..n-1] >= target
// =============================================================================
int lower_bound(const int *arr, int n, int target) {
    int lo = 0;
    int hi = n; // one past end — valid insertion point

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;

        if (arr[mid] < target) {
            lo = mid + 1; // mid is definitely < target, exclude it
        } else {
            hi = mid;     // mid might be the answer, keep it in range
        }
    }
    // lo == hi: invariant tells us arr[lo] is first element >= target
    return lo;
}

// =============================================================================
// 3. UPPER BOUND — half-open interval [lo, hi)
//    Returns the index of the first element > target.
//    Returns n if all elements <= target.
//    Invariant: arr[0..lo-1] <= target, arr[hi..n-1] > target
// =============================================================================
int upper_bound(const int *arr, int n, int target) {
    int lo = 0;
    int hi = n;

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;

        if (arr[mid] <= target) {
            lo = mid + 1; // mid <= target, first element > target is to right
        } else {
            hi = mid;     // mid > target, might be the answer
        }
    }
    return lo;
}

// =============================================================================
// 4. GENERIC PREDICATE SEARCH
//    Finds first index i in [0, n) where predicate(arr[i], ctx) == true.
//    Predicate must be monotone: false...false,true...true
//    Returns n if predicate is false for all elements.
// =============================================================================
typedef bool (*predicate_fn)(int element, void *ctx);

int predicate_search(const int *arr, int n, predicate_fn pred, void *ctx) {
    int lo = 0;
    int hi = n;

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;

        if (pred(arr[mid], ctx)) {
            hi = mid;     // might be answer, keep
        } else {
            lo = mid + 1; // definitely not answer, exclude
        }
    }
    return lo;
}

// Example predicates
static bool pred_gte(int element, void *ctx) {
    int *target = (int *)ctx;
    return element >= *target;
}

static bool pred_gt(int element, void *ctx) {
    int *target = (int *)ctx;
    return element > *target;
}

// =============================================================================
// 5. SEARCH IN ROTATED SORTED ARRAY
//    Array was sorted then rotated at some unknown pivot.
//    Example: [4,5,6,7,0,1,2] — rotated at index 4.
//    Returns index of target, or -1.
// =============================================================================
int search_rotated(const int *arr, int n, int target) {
    int lo = 0;
    int hi = n - 1;

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;

        if (arr[mid] == target) return mid;

        // Determine which half is properly sorted
        if (arr[lo] <= arr[mid]) {
            // Left half [lo..mid] is sorted
            if (arr[lo] <= target && target < arr[mid]) {
                hi = mid - 1; // target is in sorted left half
            } else {
                lo = mid + 1; // target is in right half
            }
        } else {
            // Right half [mid..hi] is sorted
            if (arr[mid] < target && target <= arr[hi]) {
                lo = mid + 1; // target is in sorted right half
            } else {
                hi = mid - 1; // target is in left half
            }
        }
    }
    return -1;
}

// =============================================================================
// 6. COUNT OCCURRENCES using lower + upper bound
// =============================================================================
int count_occurrences(const int *arr, int n, int target) {
    int lo = lower_bound(arr, n, target);
    if (lo == n || arr[lo] != target) return 0;
    int hi = upper_bound(arr, n, target);
    return hi - lo;
}

// =============================================================================
// 7. INTEGER SQUARE ROOT via binary search on answer space
//    Returns floor(sqrt(n)) without floating point.
// =============================================================================
long long isqrt(long long n) {
    if (n < 0) return -1; // undefined
    if (n == 0) return 0;

    long long lo = 1;
    long long hi = n;

    // Optimization: sqrt(n) <= n/2 for n >= 4
    if (n >= 4) hi = n / 2;

    while (lo < hi) {
        long long mid = lo + (hi - lo + 1) / 2; // round up to avoid infinite loop
        if (mid <= n / mid) {                     // mid*mid <= n (avoids overflow)
            lo = mid;
        } else {
            hi = mid - 1;
        }
    }
    return lo;
}

// =============================================================================
// 8. EXPONENTIAL (UNBOUNDED) SEARCH
//    For when the array size is unknown or infinite.
//    First finds a range [2^k, 2^(k+1)) containing target,
//    then does binary search within that range.
// =============================================================================
int exponential_search(const int *arr, int n, int target) {
    if (n == 0) return -1;
    if (arr[0] == target) return 0;

    // Find range: double the bound until arr[bound] >= target
    int bound = 1;
    while (bound < n && arr[bound] < target) {
        bound *= 2;
    }

    // Binary search in [bound/2, min(bound, n-1)]
    int lo = bound / 2;
    int hi = (bound < n) ? bound : n - 1;

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

// =============================================================================
// TESTS
// =============================================================================
static void test_basic(void) {
    int arr[] = {1, 3, 5, 7, 9, 11, 13};
    int n = sizeof(arr) / sizeof(arr[0]);

    assert(binary_search(arr, n, 1)  == 0);
    assert(binary_search(arr, n, 7)  == 3);
    assert(binary_search(arr, n, 13) == 6);
    assert(binary_search(arr, n, 4)  == -1);
    assert(binary_search(arr, n, 0)  == -1);
    assert(binary_search(arr, n, 14) == -1);
    printf("[PASS] basic exact search\n");
}

static void test_bounds(void) {
    int arr[] = {1, 3, 3, 3, 5, 7};
    int n = sizeof(arr) / sizeof(arr[0]);

    // lower_bound
    assert(lower_bound(arr, n, 3) == 1);  // first 3
    assert(lower_bound(arr, n, 4) == 4);  // insertion point
    assert(lower_bound(arr, n, 0) == 0);  // before all
    assert(lower_bound(arr, n, 8) == 6);  // after all

    // upper_bound
    assert(upper_bound(arr, n, 3) == 4);  // one past last 3
    assert(upper_bound(arr, n, 4) == 4);  // same when absent
    assert(upper_bound(arr, n, 0) == 0);  // before all
    assert(upper_bound(arr, n, 8) == 6);  // after all

    // count
    assert(count_occurrences(arr, n, 3) == 3);
    assert(count_occurrences(arr, n, 1) == 1);
    assert(count_occurrences(arr, n, 4) == 0);
    printf("[PASS] lower/upper bound and count\n");
}

static void test_edge_cases(void) {
    // Empty array
    assert(binary_search(NULL, 0, 5) == -1);
    assert(lower_bound(NULL, 0, 5) == 0);
    assert(upper_bound(NULL, 0, 5) == 0);

    // Single element
    int one[] = {42};
    assert(binary_search(one, 1, 42) == 0);
    assert(binary_search(one, 1, 41) == -1);
    assert(lower_bound(one, 1, 42) == 0);
    assert(lower_bound(one, 1, 43) == 1);
    assert(upper_bound(one, 1, 42) == 1);
    assert(upper_bound(one, 1, 41) == 0);

    printf("[PASS] edge cases\n");
}

static void test_rotated(void) {
    int arr[] = {4, 5, 6, 7, 0, 1, 2};
    int n = sizeof(arr) / sizeof(arr[0]);

    assert(search_rotated(arr, n, 0) == 4);
    assert(search_rotated(arr, n, 4) == 0);
    assert(search_rotated(arr, n, 3) == -1);
    assert(search_rotated(arr, n, 7) == 3);
    printf("[PASS] rotated array search\n");
}

static void test_isqrt(void) {
    assert(isqrt(0) == 0);
    assert(isqrt(1) == 1);
    assert(isqrt(4) == 2);
    assert(isqrt(8) == 2);   // floor(sqrt(8)) = 2
    assert(isqrt(9) == 3);
    assert(isqrt(2147395600LL) == 46340); // near INT32 limit
    printf("[PASS] integer sqrt\n");
}

static void benchmark(void) {
    const int N = 10000000;
    int *arr = (int *)malloc(N * sizeof(int));
    if (!arr) { fprintf(stderr, "malloc failed\n"); return; }

    for (int i = 0; i < N; i++) arr[i] = i * 2; // even numbers 0..2*(N-1)

    int target = (N - 1) * 2; // last element
    int iterations = 1000000;

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    volatile int result = 0;
    for (int i = 0; i < iterations; i++) {
        result += binary_search(arr, N, target);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("[BENCH] %d searches in %.3fs = %.1f ns/search (result=%d)\n",
           iterations, elapsed, elapsed * 1e9 / iterations, result / iterations);

    free(arr);
}

int main(void) {
    test_basic();
    test_bounds();
    test_edge_cases();
    test_rotated();
    test_isqrt();
    benchmark();
    printf("\nAll tests passed.\n");
    return 0;
}
```

### 6.1 Compile and Run

```bash
gcc -O2 -Wall -Wextra -Wshadow -std=c11 binary_search.c -o binary_search
./binary_search

# With AddressSanitizer for memory safety
gcc -O1 -fsanitize=address,undefined -std=c11 binary_search.c -o binary_search_asan
./binary_search_asan

# With valgrind
valgrind --error-exitcode=1 ./binary_search
```

---

## 7. Implementation — Go

```go
// binary_search.go
// Build: go build ./...
// Test:  go test -v -race ./...
// Bench: go test -bench=. -benchmem ./...
// Fuzz:  go test -fuzz=FuzzBinarySearch -fuzztime=30s ./...

package binarysearch

import "sort"

// =============================================================================
// 1. EXACT BINARY SEARCH — closed interval [lo, hi]
// =============================================================================

// Search returns the index of target in arr, or -1 if not found.
// arr must be sorted in ascending order.
func Search(arr []int, target int) int {
	lo, hi := 0, len(arr)-1

	for lo <= hi {
		mid := lo + (hi-lo)/2

		switch {
		case arr[mid] == target:
			return mid
		case arr[mid] < target:
			lo = mid + 1
		default:
			hi = mid - 1
		}
	}
	return -1
}

// =============================================================================
// 2. LOWER BOUND — half-open interval [lo, hi)
//    Returns first index i where arr[i] >= target.
//    Returns len(arr) if all elements < target.
// =============================================================================

func LowerBound(arr []int, target int) int {
	lo, hi := 0, len(arr)

	for lo < hi {
		mid := lo + (hi-lo)/2
		if arr[mid] < target {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	return lo
}

// =============================================================================
// 3. UPPER BOUND — half-open interval [lo, hi)
//    Returns first index i where arr[i] > target.
//    Returns len(arr) if all elements <= target.
// =============================================================================

func UpperBound(arr []int, target int) int {
	lo, hi := 0, len(arr)

	for lo < hi {
		mid := lo + (hi-lo)/2
		if arr[mid] <= target {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	return lo
}

// =============================================================================
// 4. GENERIC PREDICATE SEARCH using sort.Search
//    sort.Search(n, f) finds the smallest index i in [0, n) where f(i) == true.
//    f must be monotone: false for i < k, true for i >= k.
// =============================================================================

// LowerBoundSortSearch uses Go stdlib — equivalent to LowerBound above.
func LowerBoundSortSearch(arr []int, target int) int {
	return sort.Search(len(arr), func(i int) bool {
		return arr[i] >= target
	})
}

// =============================================================================
// 5. GENERIC BINARY SEARCH with custom comparison
//    cmp(i) returns:
//      -1 if arr[i] is too small (search right)
//       0 if arr[i] is the answer
//      +1 if arr[i] is too large (search left)
// =============================================================================

func SearchFunc(n int, cmp func(int) int) int {
	lo, hi := 0, n-1

	for lo <= hi {
		mid := lo + (hi-lo)/2
		switch cmp(mid) {
		case 0:
			return mid
		case -1:
			lo = mid + 1
		default:
			hi = mid - 1
		}
	}
	return -1
}

// =============================================================================
// 6. COUNT OCCURRENCES
// =============================================================================

func CountOccurrences(arr []int, target int) int {
	lo := LowerBound(arr, target)
	if lo == len(arr) || arr[lo] != target {
		return 0
	}
	return UpperBound(arr, target) - lo
}

// =============================================================================
// 7. SEARCH IN ROTATED SORTED ARRAY
// =============================================================================

func SearchRotated(arr []int, target int) int {
	lo, hi := 0, len(arr)-1

	for lo <= hi {
		mid := lo + (hi-lo)/2

		if arr[mid] == target {
			return mid
		}

		if arr[lo] <= arr[mid] {
			// Left half is sorted
			if arr[lo] <= target && target < arr[mid] {
				hi = mid - 1
			} else {
				lo = mid + 1
			}
		} else {
			// Right half is sorted
			if arr[mid] < target && target <= arr[hi] {
				lo = mid + 1
			} else {
				hi = mid - 1
			}
		}
	}
	return -1
}

// =============================================================================
// 8. SEARCH ON ANSWER — find minimum k satisfying a condition
//    Example: smallest x in [lo, hi] where feasible(x) is true.
//    feasible must be monotone: false...false,true...true
// =============================================================================

func SearchOnAnswer(lo, hi int, feasible func(int) bool) int {
	for lo < hi {
		mid := lo + (hi-lo)/2
		if feasible(mid) {
			hi = mid // might be the minimum, keep
		} else {
			lo = mid + 1
		}
	}
	return lo // lo == hi: smallest feasible value
}

// Example: integer square root = largest x where x*x <= n
func ISqrt(n int) int {
	if n < 0 {
		return -1
	}
	if n == 0 {
		return 0
	}
	// Find first x where x*x > n, then subtract 1
	result := sort.Search(n, func(x int) bool {
		return x*x > n
	})
	return result - 1
}

// =============================================================================
// 9. FIND PEAK ELEMENT
//    In an array with no equal adjacent elements, find any peak (element
//    greater than its neighbors). Uses binary search: O(log n).
// =============================================================================

func FindPeak(arr []int) int {
	lo, hi := 0, len(arr)-1

	for lo < hi {
		mid := lo + (hi-lo)/2
		if arr[mid] > arr[mid+1] {
			hi = mid // peak is at mid or to the left
		} else {
			lo = mid + 1 // arr[mid] < arr[mid+1], peak is to the right
		}
	}
	return lo
}
```

### 7.1 Test File

```go
// binary_search_test.go
package binarysearch

import (
	"math/rand"
	"sort"
	"testing"
)

func TestSearch(t *testing.T) {
	arr := []int{1, 3, 5, 7, 9, 11, 13}

	cases := []struct {
		target, want int
	}{
		{1, 0}, {7, 3}, {13, 6},
		{4, -1}, {0, -1}, {14, -1},
	}
	for _, c := range cases {
		if got := Search(arr, c.target); got != c.want {
			t.Errorf("Search(%v) = %d, want %d", c.target, got, c.want)
		}
	}
}

func TestBounds(t *testing.T) {
	arr := []int{1, 3, 3, 3, 5, 7}

	if got := LowerBound(arr, 3); got != 1 {
		t.Errorf("LowerBound(3) = %d, want 1", got)
	}
	if got := UpperBound(arr, 3); got != 4 {
		t.Errorf("UpperBound(3) = %d, want 4", got)
	}
	if got := CountOccurrences(arr, 3); got != 3 {
		t.Errorf("CountOccurrences(3) = %d, want 3", got)
	}
}

func TestEdgeCases(t *testing.T) {
	// Empty
	if Search(nil, 5) != -1 {
		t.Error("empty array search should return -1")
	}
	if LowerBound(nil, 5) != 0 {
		t.Error("empty array lower_bound should return 0")
	}

	// Single element
	one := []int{42}
	if Search(one, 42) != 0 {
		t.Error("single element found at wrong index")
	}
	if Search(one, 41) != -1 {
		t.Error("absent element in single-element array")
	}
}

func TestRotated(t *testing.T) {
	arr := []int{4, 5, 6, 7, 0, 1, 2}
	cases := []struct{ target, want int }{{0, 4}, {4, 0}, {3, -1}, {7, 3}}
	for _, c := range cases {
		if got := SearchRotated(arr, c.target); got != c.want {
			t.Errorf("SearchRotated(%d) = %d, want %d", c.target, got, c.want)
		}
	}
}

func TestISqrt(t *testing.T) {
	cases := []struct{ n, want int }{{0, 0}, {1, 1}, {4, 2}, {8, 2}, {9, 3}, {10, 3}}
	for _, c := range cases {
		if got := ISqrt(c.n); got != c.want {
			t.Errorf("ISqrt(%d) = %d, want %d", c.n, got, c.want)
		}
	}
}

// Property-based test: lower_bound agrees with sort.SearchInts
func TestLowerBoundMatchesStdlib(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	for i := 0; i < 10000; i++ {
		n := rng.Intn(100)
		arr := make([]int, n)
		for j := range arr {
			arr[j] = rng.Intn(200) - 100
		}
		sort.Ints(arr)
		target := rng.Intn(200) - 100

		got := LowerBound(arr, target)
		want := sort.SearchInts(arr, target)
		if got != want {
			t.Errorf("LowerBound mismatch: arr=%v target=%d got=%d want=%d",
				arr, target, got, want)
		}
	}
}

// Fuzz test — go test -fuzz=FuzzBinarySearch
func FuzzBinarySearch(f *testing.F) {
	f.Add([]byte{1, 3, 5, 7, 9}, byte(5))
	f.Fuzz(func(t *testing.T, data []byte, target byte) {
		arr := make([]int, len(data))
		for i, b := range data {
			arr[i] = int(b)
		}
		sort.Ints(arr)

		tgt := int(target)
		idx := Search(arr, tgt)

		if idx == -1 {
			// Verify it's truly absent
			lb := LowerBound(arr, tgt)
			if lb < len(arr) && arr[lb] == tgt {
				t.Errorf("Search returned -1 but element %d exists at lb=%d", tgt, lb)
			}
		} else {
			// Verify it's the correct element
			if arr[idx] != tgt {
				t.Errorf("Search returned index %d with value %d, want %d", idx, arr[idx], tgt)
			}
			// Verify within bounds
			if idx < 0 || idx >= len(arr) {
				t.Errorf("Search returned out-of-bounds index %d", idx)
			}
		}
	})
}

func BenchmarkSearch(b *testing.B) {
	n := 10_000_000
	arr := make([]int, n)
	for i := range arr {
		arr[i] = i * 2
	}
	target := (n - 1) * 2

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Search(arr, target)
	}
}

func BenchmarkLowerBound(b *testing.B) {
	n := 10_000_000
	arr := make([]int, n)
	for i := range arr {
		arr[i] = i * 2
	}
	target := (n - 1) * 2

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		LowerBound(arr, target)
	}
}

func BenchmarkSortSearchInts(b *testing.B) {
	n := 10_000_000
	arr := make([]int, n)
	for i := range arr {
		arr[i] = i * 2
	}
	target := (n - 1) * 2

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sort.SearchInts(arr, target)
	}
}
```

### 7.2 Build and Test

```bash
# Initialize module (if needed)
go mod init github.com/yourorg/binarysearch

# Run tests with race detector
go test -v -race ./...

# Run benchmarks
go test -bench=. -benchmem -count=5 ./...

# Fuzz for 60 seconds
go test -fuzz=FuzzBinarySearch -fuzztime=60s ./...

# Coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

---

## 8. Implementation — Rust

```rust
// src/lib.rs
// Build:  cargo build --release
// Test:   cargo test
// Bench:  cargo bench
// Fuzz:   cargo +nightly fuzz run fuzz_target_1 (with cargo-fuzz)

#![deny(unsafe_code)]
#![warn(clippy::all, clippy::pedantic)]

use std::cmp::Ordering;

// =============================================================================
// 1. EXACT BINARY SEARCH — closed interval [lo, hi]
//    Returns Some(index) if found, None otherwise.
// =============================================================================

/// Search for `target` in a sorted slice.
/// Returns the index of target, or None.
/// # Panics
/// Does not panic. Safe for empty slices.
#[must_use]
pub fn binary_search<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut lo = 0usize;
    let mut hi = arr.len().checked_sub(1)?; // Returns None if arr is empty

    loop {
        let mid = lo + (hi - lo) / 2;

        match arr[mid].cmp(target) {
            Ordering::Equal => return Some(mid),
            Ordering::Less => {
                if mid == hi {
                    return None; // would overflow: lo = mid + 1 > hi
                }
                lo = mid + 1;
            }
            Ordering::Greater => {
                if mid == lo {
                    return None; // would underflow: hi = mid - 1 < lo
                }
                hi = mid - 1;
            }
        }

        if lo > hi {
            return None;
        }
    }
}

// Note: Rust's std slice has built-in binary_search:
//   arr.binary_search(&target)  → Result<usize, usize>
//   Ok(i)  = found at index i
//   Err(i) = not found, would be inserted at i (== lower_bound!)

// =============================================================================
// 2. LOWER BOUND — half-open interval [lo, hi)
//    Returns first index i where arr[i] >= target.
//    Returns arr.len() if all elements < target.
//    Note: this is exactly what arr.partition_point(|x| x < target) returns.
// =============================================================================

#[must_use]
pub fn lower_bound<T: Ord>(arr: &[T], target: &T) -> usize {
    let mut lo = 0usize;
    let mut hi = arr.len();

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if arr[mid] < *target {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    lo
}

// Idiomatic Rust equivalent using partition_point:
#[must_use]
pub fn lower_bound_idiomatic<T: Ord>(arr: &[T], target: &T) -> usize {
    arr.partition_point(|x| x < target)
}

// =============================================================================
// 3. UPPER BOUND — half-open interval [lo, hi)
//    Returns first index i where arr[i] > target.
// =============================================================================

#[must_use]
pub fn upper_bound<T: Ord>(arr: &[T], target: &T) -> usize {
    let mut lo = 0usize;
    let mut hi = arr.len();

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if arr[mid] <= *target {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    lo
}

// Idiomatic Rust equivalent:
#[must_use]
pub fn upper_bound_idiomatic<T: Ord>(arr: &[T], target: &T) -> usize {
    arr.partition_point(|x| x <= target)
}

// =============================================================================
// 4. COUNT OCCURRENCES
// =============================================================================

#[must_use]
pub fn count_occurrences<T: Ord>(arr: &[T], target: &T) -> usize {
    let lo = lower_bound(arr, target);
    if lo >= arr.len() || &arr[lo] != target {
        return 0;
    }
    upper_bound(arr, target) - lo
}

// =============================================================================
// 5. GENERIC PREDICATE SEARCH
//    Finds first i in [0, n) where predicate(i) is true.
//    Predicate must be monotone.
// =============================================================================

#[must_use]
pub fn predicate_search<F>(n: usize, mut predicate: F) -> usize
where
    F: FnMut(usize) -> bool,
{
    let mut lo = 0usize;
    let mut hi = n;

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if predicate(mid) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    lo
}

// =============================================================================
// 6. SEARCH IN ROTATED SORTED ARRAY
// =============================================================================

#[must_use]
pub fn search_rotated<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    if arr.is_empty() {
        return None;
    }
    let mut lo = 0usize;
    let mut hi = arr.len() - 1;

    while lo <= hi {
        let mid = lo + (hi - lo) / 2;

        if &arr[mid] == target {
            return Some(mid);
        }

        if arr[lo] <= arr[mid] {
            // Left half is sorted
            if arr[lo] <= *target && target < &arr[mid] {
                if mid == 0 { return None; }
                hi = mid - 1;
            } else {
                lo = mid + 1;
            }
        } else {
            // Right half is sorted
            if &arr[mid] < target && target <= &arr[hi] {
                lo = mid + 1;
            } else {
                if mid == 0 { return None; }
                hi = mid - 1;
            }
        }

        if lo > hi { break; }
    }
    None
}

// =============================================================================
// 7. SEARCH ON ANSWER — find minimum value in [lo, hi] satisfying feasible
// =============================================================================

#[must_use]
pub fn search_on_answer<F>(mut lo: i64, mut hi: i64, mut feasible: F) -> i64
where
    F: FnMut(i64) -> bool,
{
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if feasible(mid) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    lo
}

/// Integer square root: floor(sqrt(n))
#[must_use]
pub fn isqrt(n: u64) -> u64 {
    if n == 0 {
        return 0;
    }
    // Find first x where x*x > n
    let result = predicate_search(n as usize + 1, |x| {
        let x = x as u64;
        x.saturating_mul(x) > n
    });
    (result as u64) - 1
}

// =============================================================================
// 8. FIND PEAK ELEMENT
// =============================================================================

#[must_use]
pub fn find_peak(arr: &[i64]) -> Option<usize> {
    if arr.is_empty() {
        return None;
    }
    let mut lo = 0usize;
    let mut hi = arr.len() - 1;

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        if arr[mid] > arr[mid + 1] {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    Some(lo)
}

// =============================================================================
// TESTS
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use rand::prelude::*;

    #[test]
    fn test_exact_search() {
        let arr = vec![1, 3, 5, 7, 9, 11, 13];
        assert_eq!(binary_search(&arr, &1), Some(0));
        assert_eq!(binary_search(&arr, &7), Some(3));
        assert_eq!(binary_search(&arr, &13), Some(6));
        assert_eq!(binary_search(&arr, &4), None);
        assert_eq!(binary_search(&arr, &0), None);
        assert_eq!(binary_search(&arr, &14), None);
    }

    #[test]
    fn test_empty() {
        let arr: Vec<i32> = vec![];
        assert_eq!(binary_search(&arr, &5), None);
        assert_eq!(lower_bound(&arr, &5), 0);
        assert_eq!(upper_bound(&arr, &5), 0);
    }

    #[test]
    fn test_single_element() {
        let arr = vec![42];
        assert_eq!(binary_search(&arr, &42), Some(0));
        assert_eq!(binary_search(&arr, &41), None);
        assert_eq!(lower_bound(&arr, &42), 0);
        assert_eq!(lower_bound(&arr, &43), 1);
        assert_eq!(upper_bound(&arr, &42), 1);
        assert_eq!(upper_bound(&arr, &41), 0);
    }

    #[test]
    fn test_bounds_with_duplicates() {
        let arr = vec![1, 3, 3, 3, 5, 7];
        assert_eq!(lower_bound(&arr, &3), 1);
        assert_eq!(upper_bound(&arr, &3), 4);
        assert_eq!(count_occurrences(&arr, &3), 3);
        assert_eq!(count_occurrences(&arr, &4), 0);

        // Idiomatic versions must agree
        assert_eq!(lower_bound_idiomatic(&arr, &3), lower_bound(&arr, &3));
        assert_eq!(upper_bound_idiomatic(&arr, &3), upper_bound(&arr, &3));
    }

    #[test]
    fn test_rotated() {
        let arr = vec![4, 5, 6, 7, 0, 1, 2];
        assert_eq!(search_rotated(&arr, &0), Some(4));
        assert_eq!(search_rotated(&arr, &4), Some(0));
        assert_eq!(search_rotated(&arr, &3), None);
        assert_eq!(search_rotated(&arr, &7), Some(3));
    }

    #[test]
    fn test_isqrt() {
        assert_eq!(isqrt(0), 0);
        assert_eq!(isqrt(1), 1);
        assert_eq!(isqrt(4), 2);
        assert_eq!(isqrt(8), 2);
        assert_eq!(isqrt(9), 3);
        assert_eq!(isqrt(10), 3);
    }

    #[test]
    fn test_stdlib_agrees() {
        let arr = vec![1, 3, 3, 3, 5, 7, 9];
        // Rust std partition_point == our lower_bound
        for target in 0..=10 {
            let our = lower_bound(&arr, &target);
            let std = arr.partition_point(|x| x < &target);
            assert_eq!(our, std, "lower_bound mismatch for target={}", target);
        }
    }

    // Property-based test: lower_bound is consistent with stdlib
    #[test]
    fn test_property_lower_bound() {
        let mut rng = StdRng::seed_from_u64(42);
        for _ in 0..10_000 {
            let n: usize = rng.gen_range(0..=100);
            let mut arr: Vec<i32> = (0..n).map(|_| rng.gen_range(-50..50)).collect();
            arr.sort();
            let target: i32 = rng.gen_range(-50..50);

            let our = lower_bound(&arr, &target);
            let std = arr.partition_point(|x| x < &target);
            assert_eq!(our, std);
        }
    }

    #[test]
    fn test_search_on_answer_sqrt() {
        for n in 0u64..=1000 {
            let got = isqrt(n);
            assert!(got * got <= n);
            assert!((got + 1) * (got + 1) > n);
        }
    }
}
```

### 8.1 Cargo.toml

```toml
[package]
name = "binary_search"
version = "0.1.0"
edition = "2021"

[dependencies]

[dev-dependencies]
rand = "0.8"
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "bench_binary_search"
harness = false
```

### 8.2 Benchmark File (benches/bench_binary_search.rs)

```rust
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use binary_search::{binary_search, lower_bound};

fn bench_search(c: &mut Criterion) {
    let sizes = [1_000, 100_000, 10_000_000];
    let mut group = c.benchmark_group("binary_search");

    for &n in &sizes {
        let arr: Vec<i64> = (0..n as i64).map(|x| x * 2).collect();
        let target = (n as i64 - 1) * 2;

        group.bench_with_input(BenchmarkId::new("exact", n), &n, |b, _| {
            b.iter(|| binary_search(black_box(&arr), black_box(&target)))
        });

        group.bench_with_input(BenchmarkId::new("lower_bound", n), &n, |b, _| {
            b.iter(|| lower_bound(black_box(&arr), black_box(&target)))
        });

        group.bench_with_input(BenchmarkId::new("stdlib_partition_point", n), &n, |b, _| {
            b.iter(|| arr.partition_point(|x| x < black_box(&target)))
        });
    }
    group.finish();
}

criterion_group!(benches, bench_search);
criterion_main!(benches);
```

### 8.3 Build and Test

```bash
# Build and test
cargo build --release
cargo test
cargo test -- --nocapture  # show println! output

# Benchmark
cargo bench

# Fuzz (requires nightly + cargo-fuzz)
cargo install cargo-fuzz
cargo +nightly fuzz init
cargo +nightly fuzz add fuzz_binary_search
# Edit fuzz/fuzz_targets/fuzz_binary_search.rs, then:
cargo +nightly fuzz run fuzz_binary_search -- -max_total_time=60

# Miri for undefined behavior detection
rustup component add miri
cargo +nightly miri test

# Clippy
cargo clippy -- -D warnings
```

---

## 9. Architecture View

```
Binary Search — Decision Tree (n=8, target=6)
═══════════════════════════════════════════════

Array: [1, 2, 3, 5, 6, 7, 8, 9]
Index:  0  1  2  3  4  5  6  7

                   ┌─────────┐
                   │ lo=0    │  Search space: [0..7]
                   │ hi=7    │
                   │ mid=3   │  arr[3]=5
                   └────┬────┘
                        │  5 < 6 → search right
                        ▼
                   ┌─────────┐
                   │ lo=4    │  Search space: [4..7]
                   │ hi=7    │
                   │ mid=5   │  arr[5]=7
                   └────┬────┘
                        │  7 > 6 → search left
                        ▼
                   ┌─────────┐
                   │ lo=4    │  Search space: [4..4]
                   │ hi=4    │
                   │ mid=4   │  arr[4]=6
                   └────┬────┘
                        │  6 == 6 → FOUND at index 4
                        ▼
                   ┌─────────┐
                   │ return 4│
                   └─────────┘

Comparisons: 3 = ⌈log₂(8)⌉


Memory Layout and Cache Behavior (n=1M, int64)
══════════════════════════════════════════════

Physical Memory:
┌──────────────────────────────────────────────────────────────┐
│ arr[0]          arr[250K]       arr[500K]     arr[750K]  arr[1M]│
│   │                │               │              │          │  │
│   ▼                ▼               ▼              ▼          ▼  │
│ [cold]          [cold]          iter 1         [cold]     [cold]│
│                               cache miss                       │
└──────────────────────────────────────────────────────────────┘

Iteration access pattern for 20 iterations:
iter  1: index 500,000    → cache miss (random page)
iter  2: index 750,000    → cache miss
iter  3: index 875,000    → cache miss
...
iter 17: index X          → cache miss
iter 18: index X±1        → likely same cache line
iter 19: index X±1        → cache hit (64B line covers 8 int64s)
iter 20: index X          → cache hit

Only last ~3 iterations benefit from cache locality.
B-trees: O(B) comparisons per cache line vs O(1) for binary search.


Lower Bound vs Upper Bound — Visual
════════════════════════════════════

arr: [1, 3, 3, 3, 5, 7]
      0  1  2  3  4  5

      lower_bound(3)=1          upper_bound(3)=4
             │                         │
             ▼                         ▼
      ┌──┬──┬──┬──┬──┬──┐
      │1 │3 │3 │3 │5 │7 │
      └──┴──┴──┴──┴──┴──┘
             ↑←─ range ─→↑
          first 3       first element > 3

count(3) = upper_bound(3) - lower_bound(3) = 4 - 1 = 3


Predicate Search — Boolean View
════════════════════════════════

Predicate P(i): arr[i] >= target (lower_bound style)

index:     0     1     2     3     4     5
arr:      [1,    3,    3,    3,    5,    7]
P(i,3):  [F,    T,    T,    T,    T,    T]
                 ↑
                 first True = lower_bound result = 1

The algorithm finds the BOUNDARY between F and T regions.
This works for ANY monotone predicate over ANY domain.


Search on Answer — Value Space Binary Search
═════════════════════════════════════════════

Problem: Find minimum bandwidth B such that transfer is feasible.

feasible(B):  [F, F, F, F, F, T, T, T, T, T]
               1  2  3  4  5  6  7  8  9  10
                              ↑
                         lo=hi=6 → answer

The "array" here is the answer space [1..10], not a real array.
feasible() is called O(log(max-min)) times.
```

---

## 10. Standard Library Mappings

| Language | Exact Search | Lower Bound | Upper Bound | Notes |
|----------|-------------|-------------|-------------|-------|
| **C** | `bsearch(3)` | No stdlib; use custom | No stdlib; use custom | `bsearch` returns pointer, not index |
| **C++** | `std::binary_search` | `std::lower_bound` | `std::upper_bound` | All in `<algorithm>`; work on iterators |
| **Go** | `sort.Search` + manual check | `sort.Search(n, f)` where `f = arr[i]>=x` | `sort.Search(n, f)` where `f = arr[i]>x` | `sort.SearchInts/Strings/Float64s` for common types |
| **Rust** | `slice.binary_search(&x)` | `slice.partition_point(\|x\| x < target)` | `slice.partition_point(\|x\| x <= target)` | `binary_search` returns `Err(i)` = insertion point on miss |
| **Python** | `bisect.bisect_left` + check | `bisect.bisect_left` | `bisect.bisect_right` | C implementation, very fast |

### 10.1 C++ `std::lower_bound` Iterator Contract

```cpp
// Works on any ForwardIterator (not just RandomAccess),
// but O(n) for non-random-access iterators.
// For RandomAccessIterator: O(log n) comparisons, O(log n) total.
auto it = std::lower_bound(vec.begin(), vec.end(), target);
size_t idx = std::distance(vec.begin(), it); // O(1) for RandomAccess
```

### 10.2 Rust `binary_search` Return Semantics

```rust
let arr = vec![1, 3, 5, 7];
match arr.binary_search(&4) {
    Ok(idx)  => println!("Found at {}", idx),
    Err(idx) => println!("Not found; insertion point: {}", idx),
    // Err(idx) == lower_bound(arr, 4) == 2
}
// When duplicates exist, Ok(idx) returns SOME index, not necessarily first.
// Use partition_point for guaranteed first/last occurrence.
```

---

## 11. Advanced Patterns

### 11.1 Fractional Cascading

When you need to binary search the same target in k sorted arrays of total size n, naive approach costs O(k log(n/k)). Fractional cascading achieves O(log n + k) by preprocessing bridges between arrays.

Used in: computational geometry (stabbing queries), range trees, 3D orthogonal range search.

### 11.2 Parallel Binary Search

When k independent binary searches share the same expensive feasibility oracle, batch them:

```
Round 1: For each of k searches, test their current mid.
         → One batch call to oracle for all k mids.
Round 2: Update lo/hi for each search based on results.
         → Repeat.
Total rounds: O(log n). Total oracle calls: O(k log n) → O(log n) batches.
```

Used in: offline range queries, competitive programming, distributed search.

### 11.3 Bitset-Accelerated Lower Bound

For finding the first set bit in a large bitset — conceptually lower_bound on an implicit sorted array of set indices:

```c
// Instead of binary search O(log n), use CLZ (count leading zeros):
// __builtin_ctz(x) gives index of lowest set bit in x — O(1)
// For 64-bit words: scan words linearly until non-zero, then CLZ.
// O(n/64) with SIMD, much faster than O(log n) for dense bitsets.
```

### 11.4 van Emde Boas Tree

For integer universe [0, U-1], van Emde Boas trees achieve O(log log U) for search — faster than O(log n) when n << U. Used in priority queues and dynamic predecessor/successor queries.

### 11.5 Branchless Binary Search

Branch mispredictions in binary search cost ~15 cycles on modern CPUs. The comparison direction changes every iteration, making prediction difficult. A branchless version uses conditional moves (CMOV):

```c
// Branchless binary search — avoids branch misprediction
// Compiler may generate CMOV instructions with -O2
size_t branchless_lower_bound(const int *arr, size_t n, int target) {
    size_t lo = 0;
    while (n > 1) {
        size_t half = n / 2;
        // Conditional: if arr[lo + half - 1] < target, advance lo
        lo += (arr[lo + half - 1] < target) ? half : 0;
        n -= half;
    }
    return lo;
}
```

This is the technique used in some high-performance database engines. Benchmark before adopting — the benefit depends heavily on data distribution and CPU architecture.

### 11.6 B-Tree vs Binary-Searched Array

For a sorted dataset of n elements that fits in memory:

```
Binary search on array: O(log n) comparisons, O(log n) cache misses
B-tree with fanout B:   O(log_B n) node accesses, each node = 1 cache line

For B=64 (8-byte keys, 64-byte cache line, 8 keys/node):
  n=1M: binary search = 20 comparisons, B-tree = log_64(1M) ≈ 3.3 node reads
  n=1B: binary search = 30 comparisons, B-tree = log_64(1B) ≈ 5 node reads

Cache line efficiency: B-tree extracts log₂(B)=6 bits of info per cache miss
                       Binary search: 1 bit per cache miss
```

**Recommendation:** For read-heavy workloads on large datasets, consider `std::BTreeMap` (Rust) or a cache-oblivious sorted structure over a plain sorted Vec.

---

## 12. Threat Model and Failure Modes

### 12.1 Classic Bugs

| Bug | Symptom | Root Cause | Fix |
|-----|---------|------------|-----|
| Integer overflow in midpoint | Incorrect results for large arrays | `(lo+hi)/2` overflows | Use `lo + (hi-lo)/2` |
| Off-by-one in loop condition | Element at boundary never found | Wrong invariant style mixed | Choose one style consistently |
| Infinite loop | CPU spin at 100% | `hi = mid` instead of `hi = mid-1` in closed interval | Match shrink direction to style |
| Wrong result on duplicates | First/last occurrence wrong | Using exact search instead of lower/upper bound | Use bounds explicitly |
| Applying to unsorted data | Random wrong answers | Precondition violated | Sort first, or verify sorted |
| Wrong comparison for custom types | Misses elements that exist | Comparator violates strict weak order | Validate comparator properties |

### 12.2 Security Considerations

**Algorithmic complexity attacks:** If an attacker controls the input and can trigger worst-case behavior, binary search is safe — it's always O(log n), unlike hash tables (O(n) worst case) or naive string matching.

**Integer overflow in index arithmetic:** Even with safe midpoint, if `lo` or `hi` can exceed `SIZE_MAX/2`, the entire arithmetic is unsafe. Validate input bounds.

**Out-of-bounds access:** If the array can be concurrently modified (without synchronization), mid could fall outside the current array bounds. Ensure concurrent access is properly locked or use an immutable snapshot.

**Timing side-channels:** Binary search terminates at different iterations depending on target location. This can leak information about data distribution in security-sensitive contexts (e.g., password hashing comparison). Use constant-time comparison for sensitive data.

```c
// Constant-time equality check — no early exit
// Use for sensitive data (cryptographic keys, passwords)
// Returns 0 if equal, non-zero otherwise
int ct_memcmp(const void *a, const void *b, size_t len) {
    const unsigned char *p = a, *q = b;
    unsigned char diff = 0;
    for (size_t i = 0; i < len; i++) diff |= p[i] ^ q[i];
    return diff;
}
```

**Type confusion:** In C, `bsearch` takes `void *` — wrong cast of comparison function leads to wrong comparisons without compiler warning. Always validate types explicitly.

**TOCTOU in persistent storage:** If binary searching a sorted file or database that can be modified between comparisons, use MVCC or snapshot isolation.

### 12.3 Failure Modes in Distributed Systems

Binary searching a distributed sorted dataset (e.g., across sorted SST files in RocksDB/LevelDB):
- Network partitions can cause non-monotone comparison results
- Clock skew can make "sorted by timestamp" comparisons inconsistent
- Compaction races can change the data mid-search

**Mitigation:** Always binary search a snapshot/generation, not a live mutable view.

---

## 13. Testing, Fuzzing, and Benchmarks

### 13.1 Test Strategy

**Unit tests — boundary cases:**
- Empty array
- Single element (target == element, target < element, target > element)
- Two elements
- All elements equal to target
- Target smaller than all elements
- Target larger than all elements
- Target equal to first element
- Target equal to last element
- Power-of-two sized array
- Power-of-two-minus-one sized array

**Property-based tests:**
- `lower_bound(arr, x)` agrees with stdlib for all random (arr, x)
- `binary_search` result is consistent with `lower_bound`:
  - If `binary_search(arr, x) != -1`, then `arr[lower_bound(arr, x)] == x`
- `upper_bound - lower_bound == count_occurrences`
- For any sorted arr and any x: `lower_bound(arr, x) <= upper_bound(arr, x)`

**Invariant verification:**
```go
// After binary_search returns idx:
if idx >= 0 {
    assert(arr[idx] == target)
    assert(idx >= 0 && idx < len(arr))
}
// After lower_bound returns lo:
assert(lo >= 0 && lo <= len(arr))
for i := 0; i < lo; i++ { assert(arr[i] < target) }
if lo < len(arr) { assert(arr[lo] >= target) }
```

### 13.2 Fuzzing

**Go fuzz (built-in):**
```bash
go test -fuzz=FuzzBinarySearch -fuzztime=5m -parallel=8 ./...
# Corpus stored in testdata/fuzz/
# Failures replayed with: go test -run=FuzzBinarySearch/corpus_file
```

**Rust cargo-fuzz (libFuzzer):**
```bash
cargo +nightly fuzz run fuzz_binary_search -- \
    -max_total_time=300 \
    -jobs=8 \
    -rss_limit_mb=2048
```

**C with AFL++:**
```bash
apt-get install afl++
# Instrument binary
afl-gcc -O2 -std=c11 binary_search_fuzz.c -o binary_search_fuzz

# Create initial corpus
mkdir corpus
echo "0" > corpus/seed

# Run fuzzer
afl-fuzz -i corpus -o findings -m none -- ./binary_search_fuzz @@
```

### 13.3 Benchmarks

```bash
# Go: compare implementations
go test -bench=. -benchmem -count=10 ./... | tee bench.txt
# Use benchstat for statistical analysis:
go install golang.org/x/perf/cmd/benchstat@latest
benchstat bench.txt

# Rust: criterion generates HTML report
cargo bench
open target/criterion/report/index.html

# C: use perf for hardware counters
gcc -O2 -pg binary_search.c -o binary_search_prof
./binary_search_prof
gprof binary_search_prof gmon.out > profile.txt

# Cache miss analysis with perf
perf stat -e cache-misses,cache-references,instructions,cycles \
    ./binary_search_prof
```

### 13.4 Expected Benchmark Results (rough, modern x86-64)

| Implementation | Array Size | Time/op |
|---------------|------------|---------|
| Linear scan (L1 cached) | 16 elements | ~3 ns |
| Binary search (L1 cached) | 16 elements | ~8 ns |
| Binary search (L2 cached) | 1,000 elements | ~20 ns |
| Binary search (LLC cached) | 100,000 elements | ~80 ns |
| Binary search (RAM) | 10,000,000 elements | ~200 ns |

The crossover point where binary search beats linear scan is typically 32-64 elements due to branch prediction and cache effects.

---

## 14. Real-World Applications

### 14.1 Database Systems

**Index lookup (B-tree leaf scan):** After B-tree traversal reaches the correct leaf page, binary search within the leaf node (typically 4–16KB) finds the exact key. This is the hot path in every relational database.

**RocksDB/LevelDB SST file search:** Each SST file has an index block mapping key ranges to data blocks. Binary search on the index block, then binary search within the data block.

**Database range queries:** `WHERE age BETWEEN 25 AND 35` → `lower_bound(25)` to `upper_bound(35)` on the index.

### 14.2 Operating Systems

**Page table walks:** Virtual-to-physical address translation uses sorted page table entries — binary search is implicit in the hardware TLB.

**`mmap` region lookup:** The kernel's `vm_area_struct` list is searched with `find_vma()` which uses an interval tree (augmented BST) — conceptually binary search on address ranges.

**`sched` deadline scheduling:** Sorted runqueue lookup for earliest deadline first — binary search.

### 14.3 Networking

**Longest prefix match (LPM) in routing tables:** IP routing performs LPM on the routing table. Hardware implementations use ternary CAMs or tries, but software fallbacks use sorted arrays with binary search on prefix/mask pairs.

**CIDR range membership:** Is IP 10.0.5.1 in any of these subnets? Sort subnets by start address, binary search for largest start ≤ IP, verify end ≥ IP.

### 14.4 Security

**Certificate revocation (CRL binary search):** X.509 CRLs are sorted lists of revoked serial numbers. Checking if a certificate is revoked = binary search on the CRL.

**Firewall rule lookup:** Sorted IP range deny-lists are searched with lower_bound for fast packet classification.

**Bloom filter false-positive validation:** Binary search on a sorted whitelist to confirm membership after a Bloom filter hit.

### 14.5 CNCF/Cloud Infrastructure

**etcd:** Stores key-value pairs in a B-tree (bbolt). Key lookups within B-tree nodes use binary search.

**Prometheus label index:** Time series are sorted by label set fingerprint. Binary search locates series matching a label selector.

**Kubernetes API server watch cache:** Sorted event log — binary search to find events since a given resource version.

**eBPF maps (sorted):** `BPF_MAP_TYPE_ARRAY` lookups are O(1), but range-based lookups on sorted arrays in eBPF programs use binary search patterns.

---

## 15. Next 3 Steps

**Step 1 — Implement and validate the search-on-answer pattern.**
Take a concrete problem: "minimum number of days to make m bouquets" (LeetCode 1482) or "kth smallest in sorted matrix." Implement it using the `search_on_answer` template above. Verify your feasibility function is actually monotone before trusting results.

```bash
# Verify monotonicity of your feasibility function manually:
for x in range(lo, hi+1):
    print(x, feasible(x))
# Should print: F F F ... F T T T ... T with no gaps
```

**Step 2 — Benchmark branchless vs branchy binary search on your hardware.**
Implement both versions in C or Rust. Use `perf stat -e branch-misses` to measure mispredictions. Plot performance vs array size. Understand where the crossover is for your specific CPU.

```bash
gcc -O2 -march=native binary_search.c -o bs_branch
gcc -O3 -march=native binary_search.c -o bs_branchless
perf stat -e branch-misses,cycles ./bs_branch
perf stat -e branch-misses,cycles ./bs_branchless
```

**Step 3 — Read the partition_point RFC and std::lower_bound source.**
Rust's `partition_point` and C++'s `lower_bound` are the canonical correct implementations. Reading their source and inline documentation builds intuition for invariant maintenance that transfers to every binary search variant.

```bash
# Rust partition_point source:
# https://doc.rust-lang.org/src/core/slice/mod.rs.html
# Search for "partition_point"

# libc++ lower_bound source:
# https://github.com/llvm/llvm-project/blob/main/libcxx/include/__algorithm/lower_bound.h
```

---

## 16. References

**Foundational:**
- Knuth, D.E. — *The Art of Computer Programming, Vol. 3: Sorting and Searching*, §6.2.1 "Searching an Ordered Table". The definitive mathematical treatment.
- Bentley, J. — *Programming Pearls* (2nd ed.), Column 4 "Writing Correct Programs". Contains the famous overflow bug analysis.
- Bentley, J. — "Nearly All Binary Searches and Mergesorts are Broken" (2006). https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/

**Standard Library Sources:**
- Rust `partition_point`: https://doc.rust-lang.org/std/primitive.slice.html#method.partition_point
- Rust `binary_search`: https://doc.rust-lang.org/std/primitive.slice.html#method.binary_search
- Go `sort.Search`: https://pkg.go.dev/sort#Search
- C++ `std::lower_bound`: https://en.cppreference.com/w/cpp/algorithm/lower_bound
- GNU libc `bsearch`: https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/bsearch.c

**Performance:**
- Khuong, P. — "Array Layouts for Comparison-Based Searching" (2017). Analyzes cache-oblivious layouts that improve binary search performance 2–3x.
- Algorithmica.org — "Binary Search" chapter: https://en.algorithmica.org/hpc/data-structures/binary-search/

**Advanced:**
- Fredman, M., Willard, D. — "Surpassing the Information Theoretic Bound with Fusion Trees" (1993). Achieves O(log n / log log n) for integer keys.
- van Emde Boas, P. — "Preserving order in a forest in less than logarithmic time" (1975). van Emde Boas trees for O(log log U) operations.
- CLRS — *Introduction to Algorithms* (4th ed.), Chapter 2 (basic), Chapter 12 (BST comparison).
```

Now I'll create the comprehensive binary search guide:The guide covers the full depth of binary search across 16 sections. Here's what's inside:

**Theory and Correctness** — First-principles derivation, the three loop invariant styles (closed/half-open/open), formal proof of termination via potential function, and why off-by-one bugs happen at the invariant-style boundary.

**Variants Taxonomy** — Exact search, lower bound, upper bound, predicate search (the generalizing primitive), rotated array search, search on answer (value-space binary search), exponential/unbounded search, and fractional cascading overview.

**Overflow Analysis** — The classic `(lo+hi)/2` bug, why `lo+(hi-lo)/2` is safe, Rust's `usize::midpoint`, and the signed-space overflow edge case for answer-space searches.

**Implementations** — All three languages (C/Go/Rust) with: exact search, lower bound, upper bound, predicate search, rotated array search, count occurrences, integer sqrt via search-on-answer, exponential search, find peak. Tests, fuzz harnesses, and benchmarks included for each.

**Architecture ASCII** — Decision tree trace, cache miss pattern (showing why only last 3 iterations are warm), lower/upper bound visual, predicate monotonicity diagram, search-on-answer value-space diagram.

**Threat model** — Timing side-channels, TOCTOU in distributed search, algorithmic complexity attack resistance, type confusion in C `bsearch`, constant-time comparison pattern.

**Real-World Applications** — etcd, Prometheus, Kubernetes watch cache, RocksDB SST search, eBPF maps, LPM routing, CRL revocation lookup, B-tree leaf scan.