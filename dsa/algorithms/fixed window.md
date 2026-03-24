# Fixed Window — Comprehensive DSA Guide
> *"Master the fundamentals so deeply that the advanced becomes obvious."*

---

## Table of Contents

1. [Mental Model & Philosophy](#1-mental-model--philosophy)
2. [What Is a Window? (Foundation)](#2-what-is-a-window-foundation)
3. [Fixed Window — The Core Concept](#3-fixed-window--the-core-concept)
4. [Anatomy of a Fixed Window](#4-anatomy-of-a-fixed-window)
5. [Fixed Window vs Other Window Types](#5-fixed-window-vs-other-window-types)
6. [When to Use Fixed Window — Pattern Recognition](#6-when-to-use-fixed-window--pattern-recognition)
7. [Algorithm Flow & Decision Tree](#7-algorithm-flow--decision-tree)
8. [Core Fixed Window Template](#8-core-fixed-window-template)
9. [Problem Class 1 — Max/Min Sum in Fixed Window](#9-problem-class-1--maxmin-sum-in-fixed-window)
10. [Problem Class 2 — Average of All Windows](#10-problem-class-2--average-of-all-windows)
11. [Problem Class 3 — Fixed Window with Frequency Count](#11-problem-class-3--fixed-window-with-frequency-count)
12. [Problem Class 4 — Fixed Window on Strings (Anagram Detection)](#12-problem-class-4--fixed-window-on-strings-anagram-detection)
13. [Problem Class 5 — First Negative in Every Window](#13-problem-class-5--first-negative-in-every-window)
14. [Problem Class 6 — Fixed Window Rate Limiting](#14-problem-class-6--fixed-window-rate-limiting)
15. [Advanced — Fixed Window + Deque (Monotonic Queue for Sliding Max)](#15-advanced--fixed-window--deque-monotonic-queue-for-sliding-max)
16. [Time & Space Complexity Analysis](#16-time--space-complexity-analysis)
17. [Common Mistakes & Edge Cases](#17-common-mistakes--edge-cases)
18. [Cognitive Strategies & Mental Models](#18-cognitive-strategies--mental-models)
19. [Summary Cheat Sheet](#19-summary-cheat-sheet)

---

## 1. Mental Model & Philosophy

Before writing a single line of code, an expert always builds a **mental model** — a vivid internal picture of what the data is doing. This is the foundation of superior problem-solving.

### The Physical Analogy

Imagine a long strip of paper with numbers written on it:

```
[ 2 | 1 | 5 | 1 | 3 | 2 | 9 | 1 | 6 ]
  0   1   2   3   4   5   6   7   8    <- indices
```

You have a rectangular frame (window) of fixed width `k = 3`. You place it over the strip and slide it:

```
STEP 1:  [ 2   1   5 ] 1   3   2   9   1   6     window sum = 8
STEP 2:    2 [ 1   5   1 ] 3   2   9   1   6     window sum = 7
STEP 3:    2   1 [ 5   1   3 ] 2   9   1   6     window sum = 9  <- max
STEP 4:    2   1   5 [ 1   3   2 ] 9   1   6     window sum = 6
STEP 5:    2   1   5   1 [ 3   2   9 ] 1   6     window sum = 14 <- new max
STEP 6:    2   1   5   1   3 [ 2   9   1 ] 6     window sum = 12
STEP 7:    2   1   5   1   3   2 [ 9   1   6 ]   window sum = 16 <- new max
```

The frame **never changes size**. It just **slides** one step to the right each time.

### The Core Insight

Instead of recomputing the sum from scratch for each window (O(k) per window = O(n*k) total), you use the **incremental update trick**:

```
new_sum = old_sum - element_leaving_left + element_entering_right
```

This is O(1) per slide, making the entire algorithm **O(n)**.

### The Cognitive Principle: Chunking

Fixed Window embodies **chunking** — a cognitive strategy where the brain groups individual elements into a single unit. Instead of thinking about each element independently, you think "what does this k-sized chunk contribute, and how does it change when I slide?" This is exactly how expert programmers think.

---

## 2. What Is a Window? (Foundation)

### Terminology Dictionary

| Term | Definition | Example |
|------|-----------|---------|
| **Window** | A contiguous subarray/substring of a larger sequence | arr = [1,2,3,4,5], window = [2,3,4] |
| **Window Size (k)** | The exact number of elements inside the window | k = 3 means 3 elements always |
| **Left Pointer (L)** | Index of the leftmost element of the window | L = 1 for [2,3,4] |
| **Right Pointer (R)** | Index of the rightmost element | R = 3 for [2,3,4] |
| **Slide** | Moving window one position forward: L++, R++ | [1,2,3] → [2,3,4] |
| **Invariant** | Property that never changes: R - L + 1 == k always | For k=3: R is always L+2 |
| **Subarray** | Contiguous portion of array (order preserved) | [1,2,3] from [1,2,3,4] |
| **Substring** | Contiguous portion of string | "abc" from "abcde" |
| **Outgoing element** | Element leaving the window on the left | arr[L] when we slide right |
| **Incoming element** | Element entering the window on the right | arr[R+1] when we slide right |

### What "Contiguous" Means

```
Array:  [ 2, 1, 5, 1, 3, 2 ]

Contiguous subarrays of size 3:
  [2, 1, 5]  indices 0,1,2  ✓
  [1, 5, 1]  indices 1,2,3  ✓
  [5, 1, 3]  indices 2,3,4  ✓
  [1, 3, 2]  indices 3,4,5  ✓

NOT contiguous (gaps between elements):
  [2, 5, 3]  indices 0,2,4  ✗  (skipped index 1 and 3)
  [2, 1, 3]  indices 0,1,4  ✗  (skipped indices 2,3)
```

The number of contiguous subarrays of size k in an array of size n is:
```
count = n - k + 1
```

For n=6, k=3: count = 6 - 3 + 1 = **4** subarrays.

---

## 3. Fixed Window — The Core Concept

### Definition

A **Fixed Window** is a technique where you maintain a window of **exactly k elements** and slide it across the entire array to examine every possible k-sized chunk in a single O(n) pass.

### Naive Approach vs Fixed Window

**Naive Approach (O(n*k)):**

```
for start = 0 to n-k:         // n-k+1 windows
    sum = 0
    for j = start to start+k-1:  // k elements each time
        sum += arr[j]
    record(sum)
```

For n=1,000,000 and k=500,000: this does 500,000 × 500,000 = 250,000,000,000 operations. Unusable.

**Fixed Window Approach (O(n)):**

```
sum = arr[0] + arr[1] + ... + arr[k-1]   // ONE initial pass: O(k)
record(sum)
for i = k to n-1:                        // n-k iterations
    sum = sum - arr[i-k] + arr[i]        // O(1) update
    record(sum)
```

For n=1,000,000 and k=500,000: this does 1,000,000 operations. Lightning fast.

### ASCII Visualization: The Sliding Process

```
Array:  [ 2,  1,  5,  1,  3,  2 ]    k = 3
Index:    0   1   2   3   4   5

         L=0          R=2
          |           |
INIT:   [ 2,  1,  5 ] 1   3   2      sum = 8

Slide right 1:
              L=1      R=3
               |       |
          2 [ 1,  5,  1 ] 3   2      sum = 8 - arr[0] + arr[3]
                                          = 8 - 2 + 1 = 7
Slide right 1:
                   L=2     R=4
                    |      |
          2  1 [ 5,  1,  3 ] 2       sum = 7 - arr[1] + arr[4]
                                          = 7 - 1 + 3 = 9  ← max

Slide right 1:
                        L=3     R=5
                         |      |
          2  1  5 [ 1,  3,  2 ]      sum = 9 - arr[2] + arr[5]
                                          = 9 - 5 + 2 = 6

Answer: max sum = 9
```

---

## 4. Anatomy of a Fixed Window

### The Two-Pointer Representation

```
Array index:  0    1    2    3    4    5    6    7
              a0   a1   a2   a3   a4   a5   a6   a7

Window pos 0: [a0  a1  a2  a3]                      L=0, R=3 (k=4)
Window pos 1:  a0 [a1  a2  a3  a4]                  L=1, R=4
Window pos 2:  a0  a1 [a2  a3  a4  a5]              L=2, R=5
Window pos 3:  a0  a1  a2 [a3  a4  a5  a6]          L=3, R=6
Window pos 4:  a0  a1  a2  a3 [a4  a5  a6  a7]      L=4, R=7

Invariant: R = L + k - 1    (ALWAYS)
Condition: L <= n - k        (window fits)
```

### Lifecycle Flowchart

```
┌──────────────────────────────────────────────────────┐
│               FIXED WINDOW LIFECYCLE                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ① VALIDATE                                          │
│     Is k valid? (0 < k <= n)                         │
│     If not → return error                            │
│                                                      │
│  ② INITIALIZE                                        │
│     Process first k elements: arr[0 .. k-1]          │
│     Compute initial window_state                     │
│     Set answer = window_state                        │
│                                                      │
│  ③ SLIDE  (repeat n-k times)                         │
│     outgoing = arr[i - k]   ← leaves window left    │
│     incoming = arr[i]       ← enters window right    │
│     window_state = update(window_state,              │
│                            -outgoing, +incoming)     │
│     answer = best(answer, window_state)              │
│                                                      │
│  ④ RETURN answer                                     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 5. Fixed Window vs Other Window Types

Understanding the difference sharpens pattern recognition — one of the most critical skills for top-1% problem solvers.

```
┌──────────────────────┬──────────────────┬──────────────────────────────┐
│   Window Type        │   Size           │   Pointer Movement           │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ Fixed Window         │ Always exactly k │ L and R always move together │
│                      │                  │ R = L + k - 1 always         │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ Dynamic Sliding      │ Variable         │ R moves right freely         │
│ Window               │                  │ L moves right when condition │
│                      │                  │ is violated                  │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ Two Pointers         │ Not a "window"   │ L starts at 0, R at n-1      │
│                      │ per se           │ They move toward each other  │
│                      │                  │ (or both right on sorted arr)│
└──────────────────────┴──────────────────┴──────────────────────────────┘
```

### Fixed Window Trigger Phrases

When a problem says any of these, think Fixed Window immediately:
- "subarray/substring of **size k**"
- "**exactly k** consecutive elements"
- "**every window** of length k"
- "**k-length** subarray"
- "**fixed-size** window"

---

## 6. When to Use Fixed Window — Pattern Recognition

### Decision Tree

```
Does the problem involve an array or string?
        │
        YES
        │
        ▼
Are you examining ALL contiguous chunks of some size?
        │
        YES
        │
        ▼
Is the chunk size FIXED (k given explicitly)?
        │
   ┌────┴────┐
  YES        NO
   │          │
   ▼          ▼
FIXED      DYNAMIC SLIDING WINDOW
WINDOW     (Expand/shrink based on condition)

Examples of FIXED WINDOW:          Examples of DYNAMIC WINDOW:
• Max sum of k elements             • Longest subarray with sum ≤ S
• Average of each k-window          • Minimum window containing all chars
• Count distinct in each k-window   • Longest substring without repeat
• Anagram check (k = len(pattern))  • Smallest subarray with sum ≥ S
• Rate limiting (k requests/second) • Max length subarray of 0s and 1s
```

---

## 7. Algorithm Flow & Decision Tree

### Complete Algorithm Flowchart

```
START
  │
  ▼
Receive: arr[0..n-1], window size k
  │
  ▼
┌─────────────────────────────────────┐
│  VALIDATE: Is k > n or k <= 0?      │
└────────────────┬────────────────────┘
                 │
          NO     │    YES
          │      │─────────────► Return ERROR / empty
          ▼
┌─────────────────────────────────────┐
│  INITIALIZE:                        │
│    Compute window over arr[0..k-1]  │
│    window_state = f(arr[0..k-1])    │
│    best = window_state              │
└────────────────┬────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  i = k        │
         └───────┬───────┘
                 │
         ┌───────▼───────────────────────┐
         │  LOOP: while i < n            │
         │                               │
         │  outgoing = arr[i - k]        │
         │  incoming = arr[i]            │
         │  window_state = update(...)   │
         │  if better: best = window_state│
         │  i++                          │
         └───────────────┬───────────────┘
                         │
                    i == n?
                   YES    NO
                    │      │
                    ▼      └──► loop back
                RETURN best
                    │
                   END
```

---

## 8. Core Fixed Window Template

### Universal Pseudocode Template

```
FUNCTION fixed_window(arr, n, k):

    // ── Guard ──
    IF k > n OR k <= 0:
        RETURN invalid

    // ── Phase 1: Build First Window ──
    state = initial_compute(arr[0 .. k-1])
    best  = state

    // ── Phase 2: Slide Window ──
    FOR i FROM k TO n-1:
        outgoing = arr[i - k]       // element leaving window
        incoming = arr[i]           // element entering window
        state = update(state, remove=outgoing, add=incoming)
        best  = combine(best, state)

    RETURN best
```

The `update` function must be **O(1)** for the overall complexity to be O(n).

| Problem Type | O(1) Update Rule |
|-------------|-----------------|
| Sum | `sum = sum - outgoing + incoming` |
| Average | `avg = (sum - outgoing + incoming) / k` |
| Frequency map | `freq[outgoing]--; freq[incoming]++` |
| Max/Min | Requires Deque (see Section 15) |

---

## 9. Problem Class 1 — Max/Min Sum in Fixed Window

### Problem Statement

Given integer array `arr` of size `n` and integer `k`, find the **maximum sum** of any contiguous subarray of size exactly `k`.

```
Input:  arr = [2, 1, 5, 1, 3, 2],  k = 3
Output: 9

Explanation:
  [2,1,5] → sum=8
  [1,5,1] → sum=7
  [5,1,3] → sum=9  ← maximum
  [1,3,2] → sum=6
```

### Expert Thinking Process

```
1. RECOGNIZE: "subarray of size k" → Fixed Window pattern
2. PROPERTY:  We want maximum SUM → maintain running sum
3. UPDATE:    new_sum = old_sum - arr[L] + arr[R+1]  → O(1) ✓
4. RESULT:    Track max_sum across all windows
```

---

### C Implementation

```c
#include <stdio.h>
#include <limits.h>
#include <stddef.h>

/*
 * fixed_window_max_sum
 *
 * Finds the maximum sum of any contiguous subarray of size k.
 *
 * PARAMETERS:
 *   arr - pointer to integer array
 *   n   - number of elements
 *   k   - window size (must satisfy 1 <= k <= n)
 *
 * RETURNS:
 *   Maximum sum as long long.
 *   Returns LLONG_MIN if k is invalid.
 *
 * TIME:  O(n)
 * SPACE: O(1)
 */
long long fixed_window_max_sum(const int *arr, size_t n, size_t k) {
    if (k == 0 || k > n) return LLONG_MIN;

    /* ── Phase 1: Build initial window [0 .. k-1] ── */
    long long window_sum = 0;
    for (size_t i = 0; i < k; i++) {
        window_sum += arr[i];
    }
    long long max_sum = window_sum;

    /* ── Phase 2: Slide window from position k to n-1 ── */
    /*
     * When i advances by 1:
     *   Element leaving: arr[i - k]   (leftmost of previous window)
     *   Element entering: arr[i]      (rightmost of new window)
     *
     * New window indices: [i-k+1 ... i]
     */
    for (size_t i = k; i < n; i++) {
        window_sum += arr[i] - arr[i - k];
        if (window_sum > max_sum) {
            max_sum = window_sum;
        }
    }

    return max_sum;
}

/* ── Trace helper ── */
void trace_windows(const int *arr, size_t n, size_t k) {
    printf("\n=== Window Trace (k=%zu) ===\n", k);
    long long window_sum = 0;
    for (size_t i = 0; i < k; i++) window_sum += arr[i];

    printf("Window [0..%zu]: sum = %lld\n", k-1, window_sum);
    for (size_t i = k; i < n; i++) {
        window_sum += arr[i] - arr[i - k];
        printf("Window [%zu..%zu]: sum = %lld\n", i-k+1, i, window_sum);
    }
}

int main(void) {
    int arr[] = {2, 1, 5, 1, 3, 2};
    size_t n = sizeof(arr) / sizeof(arr[0]);
    size_t k = 3;

    trace_windows(arr, n, k);
    long long result = fixed_window_max_sum(arr, n, k);
    printf("\nMax sum of size-%zu window: %lld\n", k, result);

    /* Edge cases */
    printf("\n--- Edge Cases ---\n");
    printf("k > n: %lld\n",   fixed_window_max_sum(arr, n, 10)); /* LLONG_MIN */
    printf("k = n: %lld\n",   fixed_window_max_sum(arr, n, n));  /* sum of all = 14 */
    printf("k = 1: %lld\n",   fixed_window_max_sum(arr, n, 1));  /* max element = 5 */

    /* Negative numbers */
    int neg[] = {-3, -1, -5, -2, -4};
    printf("All negative, k=2: %lld\n",
           fixed_window_max_sum(neg, 5, 2));  /* -3 (= -1 + -2) */

    return 0;
}
```

**Expected Output:**
```
=== Window Trace (k=3) ===
Window [0..2]: sum = 8
Window [1..3]: sum = 7
Window [2..4]: sum = 9
Window [3..5]: sum = 6

Max sum of size-3 window: 9
```

---

### Rust Implementation

```rust
use std::i64;

/// Finds the maximum sum of any contiguous subarray of exactly size `k`.
///
/// # Arguments
/// * `arr` - slice of integers
/// * `k`   - fixed window size
///
/// # Returns
/// * `Some(i64)` - maximum sum found
/// * `None`      - k is 0 or larger than array length
///
/// # Complexity
/// * Time:  O(n)
/// * Space: O(1)
///
/// # Examples
/// ```
/// assert_eq!(fixed_window_max_sum(&[2,1,5,1,3,2], 3), Some(9));
/// assert_eq!(fixed_window_max_sum(&[], 3), None);
/// assert_eq!(fixed_window_max_sum(&[1,2,3], 0), None);
/// ```
fn fixed_window_max_sum(arr: &[i32], k: usize) -> Option<i64> {
    let n = arr.len();

    // Guard: invalid window
    if k == 0 || k > n {
        return None;
    }

    // ── Phase 1: Initial window sum over arr[0..k] ──
    // arr[..k] is Rust slice notation for arr[0], arr[1], ..., arr[k-1]
    let mut window_sum: i64 = arr[..k]
        .iter()
        .map(|&x| x as i64)   // cast to i64 to avoid overflow
        .sum();

    let mut max_sum = window_sum;

    // ── Phase 2: Slide ──
    // i is the index of the incoming (rightmost) element.
    // The outgoing element is at index i - k.
    // Window spans indices [i-k+1 .. i] inclusive.
    for i in k..n {
        window_sum += arr[i] as i64 - arr[i - k] as i64;
        if window_sum > max_sum {
            max_sum = window_sum;
        }
    }

    Some(max_sum)
}

/// Returns the STARTING INDEX of the maximum-sum window (useful variant).
fn fixed_window_max_sum_with_index(arr: &[i32], k: usize) -> Option<(i64, usize)> {
    let n = arr.len();
    if k == 0 || k > n { return None; }

    let mut window_sum: i64 = arr[..k].iter().map(|&x| x as i64).sum();
    let mut max_sum = window_sum;
    let mut max_start = 0usize;

    for i in k..n {
        window_sum += arr[i] as i64 - arr[i - k] as i64;
        if window_sum > max_sum {
            max_sum = window_sum;
            max_start = i - k + 1;  // start of current window
        }
    }

    Some((max_sum, max_start))
}

fn main() {
    let arr = [2i32, 1, 5, 1, 3, 2];
    let k = 3;

    // Basic usage
    println!("Max sum: {:?}", fixed_window_max_sum(&arr, k));
    // Output: Max sum: Some(9)

    // With index
    if let Some((sum, start)) = fixed_window_max_sum_with_index(&arr, k) {
        println!(
            "Max sum = {}, window = {:?} (starting at index {})",
            sum,
            &arr[start..start + k],
            start
        );
        // Output: Max sum = 9, window = [5, 1, 3] (starting at index 2)
    }

    // Edge cases
    println!("{:?}", fixed_window_max_sum(&[], 1));       // None
    println!("{:?}", fixed_window_max_sum(&arr, 0));      // None
    println!("{:?}", fixed_window_max_sum(&arr, 10));     // None
    println!("{:?}", fixed_window_max_sum(&arr, 6));      // Some(14)

    // Negative numbers — still works correctly
    let neg = [-3i32, -1, -5, -2, -4];
    println!("Negatives k=2: {:?}", fixed_window_max_sum(&neg, 2));
    // Some(-3)  because -1 + -2 = -3, which is the least negative sum
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

// FixedWindowMaxSum returns the maximum sum of any contiguous subarray of size k.
//
// Time:  O(n)
// Space: O(1)
//
// Returns (maxSum, true) on success, (0, false) if k is invalid.
func FixedWindowMaxSum(arr []int, k int) (int64, bool) {
    n := len(arr)
    if k <= 0 || k > n {
        return 0, false
    }

    // ── Phase 1: Initial window ──
    var windowSum int64
    for i := 0; i < k; i++ {
        windowSum += int64(arr[i])
    }
    maxSum := windowSum

    // ── Phase 2: Slide ──
    // outgoing: arr[i-k]   (leaves from left)
    // incoming: arr[i]     (enters from right)
    for i := k; i < n; i++ {
        windowSum += int64(arr[i]) - int64(arr[i-k])
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }

    return maxSum, true
}

// FixedWindowMaxSumWithIndex also returns the starting index of the best window.
func FixedWindowMaxSumWithIndex(arr []int, k int) (sum int64, startIdx int, ok bool) {
    n := len(arr)
    if k <= 0 || k > n {
        return 0, -1, false
    }

    var windowSum int64
    for i := 0; i < k; i++ {
        windowSum += int64(arr[i])
    }
    maxSum := windowSum
    maxStart := 0

    for i := k; i < n; i++ {
        windowSum += int64(arr[i]) - int64(arr[i-k])
        if windowSum > maxSum {
            maxSum = windowSum
            maxStart = i - k + 1
        }
    }

    return maxSum, maxStart, true
}

func main() {
    arr := []int{2, 1, 5, 1, 3, 2}
    k := 3

    if result, ok := FixedWindowMaxSum(arr, k); ok {
        fmt.Printf("Max sum (k=%d): %d\n", k, result) // 9
    }

    if sum, start, ok := FixedWindowMaxSumWithIndex(arr, k); ok {
        fmt.Printf("Max window: %v, sum=%d, start=%d\n",
            arr[start:start+k], sum, start)
        // Max window: [5 1 3], sum=9, start=2
    }

    // Edge cases
    _, ok1 := FixedWindowMaxSum([]int{}, 3)
    fmt.Println("Empty:", ok1) // false

    _, ok2 := FixedWindowMaxSum(arr, 0)
    fmt.Println("k=0:", ok2) // false

    result, _ := FixedWindowMaxSum(arr, len(arr))
    fmt.Println("k=n:", result) // 14

    // All negatives
    neg := []int{-3, -1, -5, -2, -4}
    result2, _ := FixedWindowMaxSum(neg, 2)
    fmt.Println("All negative, k=2:", result2) // -3

    _ = math.MaxInt64
}
```

---

## 10. Problem Class 2 — Average of All Windows

### Problem Statement

Given array `arr` of `n` numbers, return a new array where each element is the **average** of the corresponding window of size `k`.

```
Input:  arr = [1, 3, 2, 6, -1, 4, 1, 8, 2],  k = 5
Output: [2.2, 2.8, 2.4, 3.6, 2.8]

Number of windows = n - k + 1 = 9 - 5 + 1 = 5

Window 0: (1+3+2+6-1)/5  = 11/5 = 2.2
Window 1: (3+2+6-1+4)/5  = 14/5 = 2.8
Window 2: (2+6-1+4+1)/5  = 12/5 = 2.4
Window 3: (6-1+4+1+8)/5  = 18/5 = 3.6
Window 4: (-1+4+1+8+2)/5 = 14/5 = 2.8
```

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * fixed_window_averages
 *
 * Returns heap-allocated array of (n - k + 1) averages.
 * CALLER must free the returned pointer.
 *
 * TIME:  O(n)
 * SPACE: O(n - k + 1) for output
 */
double *fixed_window_averages(const int *arr, int n, int k, int *out_size) {
    if (k <= 0 || k > n) {
        *out_size = 0;
        return NULL;
    }

    int count = n - k + 1;
    *out_size = count;
    double *result = malloc(count * sizeof(double));
    if (!result) return NULL;

    /* Build initial window */
    double window_sum = 0.0;
    for (int i = 0; i < k; i++) window_sum += arr[i];
    result[0] = window_sum / k;

    /* Slide and record each average */
    for (int i = k; i < n; i++) {
        window_sum += arr[i] - arr[i - k];
        result[i - k + 1] = window_sum / k;
    }

    return result;
}

int main(void) {
    int arr[] = {1, 3, 2, 6, -1, 4, 1, 8, 2};
    int n = 9, k = 5, out_size = 0;

    double *avgs = fixed_window_averages(arr, n, k, &out_size);
    if (!avgs) { fprintf(stderr, "Error\n"); return 1; }

    printf("Averages (k=%d): ", k);
    for (int i = 0; i < out_size; i++) {
        printf("%.1f%s", avgs[i], i < out_size - 1 ? ", " : "\n");
    }
    /* Output: Averages (k=5): 2.2, 2.8, 2.4, 3.6, 2.8 */

    free(avgs);
    return 0;
}
```

---

### Rust Implementation

```rust
/// Returns a Vec of averages for each window of size k.
///
/// Time:  O(n)
/// Space: O(n - k + 1) for output
fn fixed_window_averages(arr: &[i32], k: usize) -> Vec<f64> {
    let n = arr.len();
    if k == 0 || k > n {
        return vec![];
    }

    let mut result = Vec::with_capacity(n - k + 1);

    // Initial window sum
    let mut sum: i64 = arr[..k].iter().map(|&x| x as i64).sum();
    result.push(sum as f64 / k as f64);

    // Slide
    for i in k..n {
        sum += arr[i] as i64 - arr[i - k] as i64;
        result.push(sum as f64 / k as f64);
    }

    result
}

fn main() {
    let arr = [1i32, 3, 2, 6, -1, 4, 1, 8, 2];
    let avgs = fixed_window_averages(&arr, 5);

    for (i, avg) in avgs.iter().enumerate() {
        println!("Window {}: {:.1}", i, avg);
    }
    // Window 0: 2.2
    // Window 1: 2.8
    // Window 2: 2.4
    // Window 3: 3.6
    // Window 4: 2.8
}
```

---

### Go Implementation

```go
package main

import "fmt"

// FixedWindowAverages returns a slice of averages for each window of size k.
//
// Time:  O(n)
// Space: O(n - k + 1) for output
func FixedWindowAverages(arr []int, k int) []float64 {
    n := len(arr)
    if k <= 0 || k > n {
        return nil
    }

    result := make([]float64, 0, n-k+1)

    var sum int64
    for i := 0; i < k; i++ {
        sum += int64(arr[i])
    }
    result = append(result, float64(sum)/float64(k))

    for i := k; i < n; i++ {
        sum += int64(arr[i]) - int64(arr[i-k])
        result = append(result, float64(sum)/float64(k))
    }

    return result
}

func main() {
    arr := []int{1, 3, 2, 6, -1, 4, 1, 8, 2}
    avgs := FixedWindowAverages(arr, 5)
    for i, a := range avgs {
        fmt.Printf("Window %d: %.1f\n", i, a)
    }
}
```

---

## 11. Problem Class 3 — Fixed Window with Frequency Count

### Problem Statement

Given array `arr` and window size `k`, for **each window** count the **number of distinct elements**.

```
Input:  arr = [1, 2, 1, 3, 4, 2, 3],  k = 4
Output: [3, 4, 4, 3]

Window [1,2,1,3]: distinct = {1,2,3}    → 3
Window [2,1,3,4]: distinct = {1,2,3,4}  → 4
Window [1,3,4,2]: distinct = {1,2,3,4}  → 4
Window [3,4,2,3]: distinct = {2,3,4}    → 3
```

**Key Insight:** We use a **hash map (frequency table)** to track counts of elements in the window. When an element's count drops to 0, it's no longer in the window.

```
Frequency Map Update:
  incoming element: freq[elem]++
                    if freq[elem] == 1: distinct_count++   (new element)

  outgoing element: freq[elem]--
                    if freq[elem] == 0: distinct_count--   (element gone)
```

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HASH_SIZE 10007  /* prime for hash table */

typedef struct {
    int key;
    int val;
    int used;
} HashEntry;

static HashEntry table[HASH_SIZE];

static void hash_clear(void) {
    memset(table, 0, sizeof(table));
}

static int hash_get(int key) {
    unsigned idx = (unsigned)(key * 2654435761u) % HASH_SIZE;
    while (table[idx].used && table[idx].key != key) idx = (idx + 1) % HASH_SIZE;
    return table[idx].used ? table[idx].val : 0;
}

static void hash_set(int key, int val) {
    unsigned idx = (unsigned)(key * 2654435761u) % HASH_SIZE;
    while (table[idx].used && table[idx].key != key) idx = (idx + 1) % HASH_SIZE;
    table[idx].key = key;
    table[idx].val = val;
    table[idx].used = 1;
}

/*
 * count_distinct_each_window
 *
 * For each window of size k in arr, counts the number of distinct elements.
 * Returns heap-allocated array of size (n - k + 1). Caller must free.
 *
 * TIME:  O(n)  (amortized, with good hash distribution)
 * SPACE: O(k)  for the frequency table
 */
int *count_distinct_each_window(const int *arr, int n, int k, int *out_size) {
    if (k <= 0 || k > n) { *out_size = 0; return NULL; }

    hash_clear();
    int count = n - k + 1;
    int *result = malloc(count * sizeof(int));
    if (!result) return NULL;
    *out_size = count;

    int distinct = 0;

    /* ── Phase 1: Build first window ── */
    for (int i = 0; i < k; i++) {
        int cur = hash_get(arr[i]);
        if (cur == 0) distinct++;
        hash_set(arr[i], cur + 1);
    }
    result[0] = distinct;

    /* ── Phase 2: Slide ── */
    for (int i = k; i < n; i++) {
        /* Handle outgoing element arr[i - k] */
        int out_val = arr[i - k];
        int out_cnt = hash_get(out_val) - 1;
        hash_set(out_val, out_cnt);
        if (out_cnt == 0) distinct--;  /* element fully removed */

        /* Handle incoming element arr[i] */
        int in_val  = arr[i];
        int in_cnt  = hash_get(in_val);
        if (in_cnt == 0) distinct++;   /* brand new element */
        hash_set(in_val, in_cnt + 1);

        result[i - k + 1] = distinct;
    }

    return result;
}

int main(void) {
    int arr[] = {1, 2, 1, 3, 4, 2, 3};
    int n = 7, k = 4, out_size = 0;

    int *distincts = count_distinct_each_window(arr, n, k, &out_size);

    printf("Distinct counts (k=%d): ", k);
    for (int i = 0; i < out_size; i++) {
        printf("%d%s", distincts[i], i < out_size-1 ? ", " : "\n");
    }
    /* Output: Distinct counts (k=4): 3, 4, 4, 3 */

    free(distincts);
    return 0;
}
```

---

### Rust Implementation

```rust
use std::collections::HashMap;

/// For each window of size k, counts the number of distinct elements.
///
/// Time:  O(n)
/// Space: O(k) for frequency map
fn count_distinct_each_window(arr: &[i32], k: usize) -> Vec<usize> {
    let n = arr.len();
    if k == 0 || k > n { return vec![]; }

    let mut freq: HashMap<i32, usize> = HashMap::new();
    let mut distinct = 0usize;
    let mut result = Vec::with_capacity(n - k + 1);

    // ── Phase 1: First window ──
    for &x in &arr[..k] {
        // entry().or_insert(0) gets value or inserts 0 if absent
        let cnt = freq.entry(x).or_insert(0);
        if *cnt == 0 { distinct += 1; }
        *cnt += 1;
    }
    result.push(distinct);

    // ── Phase 2: Slide ──
    for i in k..n {
        // Remove outgoing
        let out_elem = arr[i - k];
        if let Some(cnt) = freq.get_mut(&out_elem) {
            *cnt -= 1;
            if *cnt == 0 { distinct -= 1; }
        }

        // Add incoming
        let in_elem = arr[i];
        let cnt = freq.entry(in_elem).or_insert(0);
        if *cnt == 0 { distinct += 1; }
        *cnt += 1;

        result.push(distinct);
    }

    result
}

fn main() {
    let arr = [1i32, 2, 1, 3, 4, 2, 3];
    let counts = count_distinct_each_window(&arr, 4);
    println!("{:?}", counts); // [3, 4, 4, 3]
}
```

---

### Go Implementation

```go
package main

import "fmt"

// CountDistinctEachWindow counts distinct elements in each window of size k.
//
// Time:  O(n)
// Space: O(k)
func CountDistinctEachWindow(arr []int, k int) []int {
    n := len(arr)
    if k <= 0 || k > n {
        return nil
    }

    freq := make(map[int]int)
    distinct := 0
    result := make([]int, 0, n-k+1)

    // Phase 1
    for i := 0; i < k; i++ {
        if freq[arr[i]] == 0 {
            distinct++
        }
        freq[arr[i]]++
    }
    result = append(result, distinct)

    // Phase 2
    for i := k; i < n; i++ {
        // Outgoing
        out := arr[i-k]
        freq[out]--
        if freq[out] == 0 {
            distinct--
            delete(freq, out) // clean up zero-count entries (memory hygiene)
        }
        // Incoming
        if freq[arr[i]] == 0 {
            distinct++
        }
        freq[arr[i]]++

        result = append(result, distinct)
    }

    return result
}

func main() {
    arr := []int{1, 2, 1, 3, 4, 2, 3}
    fmt.Println(CountDistinctEachWindow(arr, 4)) // [3 4 4 3]
}
```

---

## 12. Problem Class 4 — Fixed Window on Strings (Anagram Detection)

### Problem Statement

Given strings `s` and `pattern` `p`, find **all starting indices** in `s` where a substring of `s` is an anagram of `p`.

**Anagram:** Two strings are anagrams of each other if they contain the same characters with the same frequencies (order doesn't matter).

```
Input:  s = "cbaebabacd",  p = "abc"
Output: [0, 6]

Explanation:
  s[0..2] = "cba" → sorted = "abc" ✓ anagram of "abc"
  s[1..3] = "bae" → sorted = "abe" ✗
  s[2..4] = "aeb" → sorted = "abe" ✗
  s[3..5] = "eba" → sorted = "abe" ✗
  s[4..6] = "bab" → sorted = "abb" ✗
  s[5..7] = "aba" → sorted = "aab" ✗
  s[6..8] = "bac" → sorted = "abc" ✓ anagram of "abc"
  s[7..9] = "acd" → sorted = "acd" ✗
```

**Key Insight:** The window size is fixed at `len(p)`. Two frequency arrays match → anagram.

```
Comparison:
  p_freq: [a:1, b:1, c:1]
  window "cba": [a:1, b:1, c:1] → MATCH
  window "bae": [a:1, b:1, e:1] → NO MATCH
```

We maintain a `matches` counter tracking how many characters currently have matching frequencies.

---

### C Implementation

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*
 * find_anagrams
 *
 * Finds all starting indices in s where a length-p substring is an anagram of p.
 *
 * APPROACH:
 *   Maintain two frequency arrays: p_freq and window_freq (both size 26).
 *   Track 'matches' = count of chars where p_freq[c] == window_freq[c].
 *   If matches == 26, current window is an anagram.
 *
 * TIME:  O(n)  - each char is processed at most twice (enter + leave)
 * SPACE: O(1)  - only 26-element arrays (fixed alphabet)
 */
int *find_anagrams(const char *s, const char *p,
                   int s_len, int p_len, int *out_count) {
    *out_count = 0;
    if (p_len > s_len || p_len == 0) return NULL;

    int p_freq[26]      = {0};
    int window_freq[26] = {0};

    /* Build frequency arrays for pattern and first window */
    for (int i = 0; i < p_len; i++) {
        p_freq[(unsigned char)p[i] - 'a']++;
        window_freq[(unsigned char)s[i] - 'a']++;
    }

    /* Count initial matches */
    int matches = 0;
    for (int c = 0; c < 26; c++) {
        if (p_freq[c] == window_freq[c]) matches++;
    }

    /* Result storage (worst case: every position matches) */
    int *result = malloc((s_len - p_len + 1) * sizeof(int));
    if (!result) return NULL;

    if (matches == 26) result[(*out_count)++] = 0;

    /* Slide the window */
    for (int i = p_len; i < s_len; i++) {
        int outgoing = (unsigned char)s[i - p_len] - 'a';
        int incoming = (unsigned char)s[i] - 'a';

        /* Add incoming character to window */
        window_freq[incoming]++;
        /* Did this char's frequency now match the pattern? */
        if (window_freq[incoming] == p_freq[incoming])       matches++;
        /* Or did it just become one more than pattern (breaking a match)? */
        else if (window_freq[incoming] == p_freq[incoming]+1) matches--;

        /* Remove outgoing character from window */
        window_freq[outgoing]--;
        /* Did removal make it match? */
        if (window_freq[outgoing] == p_freq[outgoing])       matches++;
        /* Or did removal break a match? */
        else if (window_freq[outgoing] == p_freq[outgoing]-1) matches--;

        if (matches == 26) result[(*out_count)++] = i - p_len + 1;
    }

    return result;
}

int main(void) {
    const char *s = "cbaebabacd";
    const char *p = "abc";
    int s_len = (int)strlen(s);
    int p_len = (int)strlen(p);
    int count = 0;

    int *indices = find_anagrams(s, p, s_len, p_len, &count);
    printf("Anagram start indices: ");
    for (int i = 0; i < count; i++) printf("%d ", indices[i]);
    printf("\n");
    /* Output: Anagram start indices: 0 6 */

    free(indices);

    /* Another test */
    s = "abab"; p = "ab"; s_len = 4; p_len = 2;
    indices = find_anagrams(s, p, s_len, p_len, &count);
    printf("Anagram start indices in 'abab': ");
    for (int i = 0; i < count; i++) printf("%d ", indices[i]);
    printf("\n");
    /* Output: 0 1 2 */
    free(indices);

    return 0;
}
```

---

### Rust Implementation

```rust
/// Returns all starting indices in `s` where a substring of length `p.len()`
/// is an anagram of `p`.
///
/// Time:  O(n) where n = s.len()
/// Space: O(1) — two fixed-size [usize; 26] arrays
fn find_anagrams(s: &[u8], p: &[u8]) -> Vec<usize> {
    let (sn, pn) = (s.len(), p.len());
    if pn > sn || pn == 0 { return vec![]; }

    let mut p_freq    = [0i32; 26];
    let mut win_freq  = [0i32; 26];
    let mut result    = Vec::new();

    // Build frequency tables for p and first window
    for i in 0..pn {
        p_freq[(p[i] - b'a') as usize]   += 1;
        win_freq[(s[i] - b'a') as usize] += 1;
    }

    // Count initial matches
    let mut matches: usize = p_freq.iter().zip(win_freq.iter())
        .filter(|(a, b)| a == b)
        .count();

    if matches == 26 { result.push(0); }

    for i in pn..sn {
        let outgoing = (s[i - pn] - b'a') as usize;
        let incoming = (s[i]      - b'a') as usize;

        // Add incoming
        win_freq[incoming] += 1;
        match win_freq[incoming] - p_freq[incoming] {
             0 => matches += 1,  // now matches
             1 => matches -= 1,  // broke a match (went one over)
             _ => {}
        }

        // Remove outgoing
        win_freq[outgoing] -= 1;
        match win_freq[outgoing] - p_freq[outgoing] {
             0 => matches += 1,  // removal caused a match
            -1 => matches -= 1,  // removal broke a match (went one under)
             _ => {}
        }

        if matches == 26 {
            result.push(i - pn + 1);
        }
    }

    result
}

fn main() {
    let s = b"cbaebabacd".to_vec();
    let p = b"abc".to_vec();
    println!("{:?}", find_anagrams(&s, &p)); // [0, 6]

    let s2 = b"abab".to_vec();
    let p2 = b"ab".to_vec();
    println!("{:?}", find_anagrams(&s2, &p2)); // [0, 1, 2]
}
```

---

### Go Implementation

```go
package main

import "fmt"

// FindAnagrams returns all starting indices in s where a substring
// of length len(p) is an anagram of p.
//
// Time:  O(n)
// Space: O(1) — fixed 26-char alphabet
func FindAnagrams(s, p string) []int {
    sn, pn := len(s), len(p)
    if pn > sn || pn == 0 {
        return nil
    }

    var pFreq, winFreq [26]int
    result := []int{}

    for i := 0; i < pn; i++ {
        pFreq[p[i]-'a']++
        winFreq[s[i]-'a']++
    }

    matches := 0
    for c := 0; c < 26; c++ {
        if pFreq[c] == winFreq[c] {
            matches++
        }
    }
    if matches == 26 {
        result = append(result, 0)
    }

    for i := pn; i < sn; i++ {
        out := s[i-pn] - 'a'
        in  := s[i]    - 'a'

        // Add incoming
        winFreq[in]++
        diff := winFreq[in] - pFreq[in]
        if diff == 0 { matches++ } else if diff == 1 { matches-- }

        // Remove outgoing
        winFreq[out]--
        diff = winFreq[out] - pFreq[out]
        if diff == 0 { matches++ } else if diff == -1 { matches-- }

        if matches == 26 {
            result = append(result, i-pn+1)
        }
    }

    return result
}

func main() {
    fmt.Println(FindAnagrams("cbaebabacd", "abc")) // [0 6]
    fmt.Println(FindAnagrams("abab", "ab"))        // [0 1 2]
}
```

---

## 13. Problem Class 5 — First Negative in Every Window

### Problem Statement

Given array `arr` and window size `k`, for each window of size k print the **first negative number** in that window. If there is no negative number, print 0.

```
Input:  arr = [-8, 2, 3, -6, 10],  k = 2
Output: [-8, 0, -6, -6, 0]

Explanation:
  Window [-8,  2]: first negative = -8
  Window [ 2,  3]: first negative = 0 (none)
  Window [ 3, -6]: first negative = -6
  Window [-6, 10]: first negative = -6
  Window [10,  ?]: only one element shown above
```

**Approach:** Use a **Deque (double-ended queue)** to store indices of negative numbers. The deque stores indices in increasing order, always representing negatives currently inside the window.

### What is a Deque?

A **Deque** (Double-Ended Queue) is a data structure where you can add or remove elements from **both ends** (front and back):

```
Deque:   front ← [ idx_0 | idx_1 | idx_2 ] → back

Operations:
  push_back(x)   - add to right end
  pop_front()    - remove from left end (gives oldest element)
  pop_back()     - remove from right end
  front()        - peek at leftmost element (without removing)
```

For this problem, the deque stores **indices of negative elements** in the current window.

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

/* Simple deque using a circular buffer for indices */
typedef struct {
    int *data;
    int front;
    int back;
    int size;
    int capacity;
} Deque;

Deque *deque_create(int cap) {
    Deque *d = malloc(sizeof(Deque));
    d->data = malloc(cap * sizeof(int));
    d->front = 0; d->back = 0;
    d->size = 0; d->capacity = cap;
    return d;
}

void deque_free(Deque *d) { free(d->data); free(d); }
int  deque_empty(Deque *d) { return d->size == 0; }
int  deque_front(Deque *d) { return d->data[d->front]; }

void deque_push_back(Deque *d, int val) {
    d->data[(d->front + d->size) % d->capacity] = val;
    d->size++;
}
void deque_pop_front(Deque *d) {
    d->front = (d->front + 1) % d->capacity;
    d->size--;
}

/*
 * first_negative_each_window
 *
 * For each window of size k, returns the first negative element (or 0).
 *
 * TIME:  O(n)  — each element enters/leaves deque at most once
 * SPACE: O(k)  — deque holds at most k indices
 */
int *first_negative_each_window(const int *arr, int n, int k, int *out_size) {
    if (k <= 0 || k > n) { *out_size = 0; return NULL; }

    int count = n - k + 1;
    *out_size = count;
    int *result = malloc(count * sizeof(int));
    Deque *dq = deque_create(k + 1);

    /* Phase 1: Process first window - add all negative indices to deque */
    for (int i = 0; i < k; i++) {
        if (arr[i] < 0) deque_push_back(dq, i);
    }
    result[0] = deque_empty(dq) ? 0 : arr[deque_front(dq)];

    /* Phase 2: Slide */
    for (int i = k; i < n; i++) {
        /* Remove indices no longer in window (left boundary = i - k + 1) */
        while (!deque_empty(dq) && deque_front(dq) <= i - k) {
            deque_pop_front(dq);
        }
        /* Add new incoming element if negative */
        if (arr[i] < 0) deque_push_back(dq, i);

        result[i - k + 1] = deque_empty(dq) ? 0 : arr[deque_front(dq)];
    }

    deque_free(dq);
    return result;
}

int main(void) {
    int arr[] = {-8, 2, 3, -6, 10, 2, -1, 4};
    int n = 8, k = 3, out_size = 0;

    int *res = first_negative_each_window(arr, n, k, &out_size);
    printf("First negatives (k=%d): ", k);
    for (int i = 0; i < out_size; i++) printf("%d ", res[i]);
    printf("\n");
    /* Output: -8 0 -6 -6 -1 -1 */
    free(res);
    return 0;
}
```

---

### Rust Implementation

```rust
use std::collections::VecDeque;

/// For each window of size k, returns the first negative element (or 0).
///
/// Time:  O(n)
/// Space: O(k)
fn first_negative_each_window(arr: &[i32], k: usize) -> Vec<i32> {
    let n = arr.len();
    if k == 0 || k > n { return vec![]; }

    // VecDeque stores indices of negative elements in current window
    let mut dq: VecDeque<usize> = VecDeque::new();
    let mut result = Vec::with_capacity(n - k + 1);

    // Phase 1: First window
    for i in 0..k {
        if arr[i] < 0 { dq.push_back(i); }
    }
    result.push(dq.front().map_or(0, |&i| arr[i]));

    // Phase 2: Slide
    for i in k..n {
        // Remove stale front (outside window left boundary = i - k + 1)
        while dq.front().map_or(false, |&idx| idx <= i - k) {
            dq.pop_front();
        }
        // Add incoming if negative
        if arr[i] < 0 { dq.push_back(i); }

        result.push(dq.front().map_or(0, |&idx| arr[idx]));
    }

    result
}

fn main() {
    let arr = [-8i32, 2, 3, -6, 10, 2, -1, 4];
    println!("{:?}", first_negative_each_window(&arr, 3));
    // [-8, 0, -6, -6, -1, -1]

    // No negatives at all
    println!("{:?}", first_negative_each_window(&[1, 2, 3, 4], 2));
    // [0, 0, 0]
}
```

---

### Go Implementation

```go
package main

import "fmt"

// FirstNegativeEachWindow returns the first negative in each window of size k,
// or 0 if no negative exists in that window.
//
// Time:  O(n)
// Space: O(k)
func FirstNegativeEachWindow(arr []int, k int) []int {
    n := len(arr)
    if k <= 0 || k > n { return nil }

    dq := make([]int, 0, k) // stores indices of negatives
    result := make([]int, 0, n-k+1)

    for i := 0; i < k; i++ {
        if arr[i] < 0 { dq = append(dq, i) }
    }
    if len(dq) == 0 { result = append(result, 0) } else { result = append(result, arr[dq[0]]) }

    for i := k; i < n; i++ {
        // Evict stale front
        for len(dq) > 0 && dq[0] <= i-k {
            dq = dq[1:]
        }
        if arr[i] < 0 { dq = append(dq, i) }
        if len(dq) == 0 { result = append(result, 0) } else { result = append(result, arr[dq[0]]) }
    }
    return result
}

func main() {
    arr := []int{-8, 2, 3, -6, 10, 2, -1, 4}
    fmt.Println(FirstNegativeEachWindow(arr, 3)) // [-8 0 -6 -6 -1 -1]
}
```

---

## 14. Problem Class 6 — Fixed Window Rate Limiting

### What is Rate Limiting?

**Rate limiting** is a real-world systems design pattern that restricts how many **requests** (API calls, messages, logins) a user or service can make in a given **time period**.

**Fixed Window Rate Limiting** divides time into discrete, equal-length windows (e.g., 1-minute buckets) and counts requests within each bucket.

```
Timeline divided into fixed 60-second windows:
│<─── Window 1 ──────────>│<─── Window 2 ──────────>│
│ 12:00:00 → 12:00:59     │ 12:01:00 → 12:01:59     │
│ req count: 3            │ req count: 0            │
│ Limit: 5 → ALLOW        │ Limit: 5 → ALLOW         │
```

### The Problem with Fixed Window Rate Limiting

The classic **boundary exploit**: A user can burst 2× the allowed rate across a window boundary.

```
Limit: 5 requests per 60-second window

Window 1 ends at 12:00:59  | Window 2 starts at 12:01:00
                            |
  ·  ·  ·  ·  ·             | ·  ·  ·  ·  ·
12:00:55 - 5 requests       | 12:01:00 - 5 more requests
                            |
In 2 seconds, user made 10 requests (2× limit)!
```

This is a known flaw of Fixed Window counters — Sliding Window overcomes it (see the Sliding Window guide).

---

### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAX_LIMIT 1000

typedef struct {
    long long window_start_sec;  /* Unix timestamp of window start */
    int       count;             /* requests in current window */
    int       limit;             /* max requests allowed per window */
    int       window_size_sec;   /* window duration in seconds */
} FixedWindowLimiter;

FixedWindowLimiter *limiter_create(int limit, int window_size_sec) {
    FixedWindowLimiter *lim = malloc(sizeof(FixedWindowLimiter));
    lim->window_start_sec  = 0;
    lim->count             = 0;
    lim->limit             = limit;
    lim->window_size_sec   = window_size_sec;
    return lim;
}

/*
 * limiter_allow
 *
 * Returns 1 (allow) or 0 (deny) for the given timestamp.
 *
 * ALGORITHM:
 *   1. Compute which window this timestamp falls in.
 *   2. If it's a new window → reset counter.
 *   3. If count < limit → allow (increment count).
 *   4. Otherwise → deny.
 *
 * TIME:  O(1)
 * SPACE: O(1)
 */
int limiter_allow(FixedWindowLimiter *lim, long long timestamp_sec) {
    /* Which window does this timestamp belong to? */
    long long window_id    = timestamp_sec / lim->window_size_sec;
    long long window_start = window_id * lim->window_size_sec;

    /* New window → reset */
    if (window_start != lim->window_start_sec) {
        lim->window_start_sec = window_start;
        lim->count = 0;
    }

    /* Check limit */
    if (lim->count < lim->limit) {
        lim->count++;
        return 1; /* ALLOWED */
    }
    return 0; /* DENIED */
}

void limiter_free(FixedWindowLimiter *lim) { free(lim); }

int main(void) {
    /* Limit: 3 requests per 10-second window */
    FixedWindowLimiter *lim = limiter_create(3, 10);

    /* Simulate requests */
    long long timestamps[] = {0, 1, 2, 3, 10, 11, 12, 19, 20, 20};
    int n = 10;

    printf("Fixed Window Rate Limiter (limit=3, window=10s)\n");
    printf("%-12s %-10s %-6s\n", "Timestamp", "Window", "Result");
    printf("─────────────────────────────\n");

    for (int i = 0; i < n; i++) {
        long long t = timestamps[i];
        long long w = t / lim->window_size_sec;
        int result  = limiter_allow(lim, t);
        printf("t=%-10lld w=%-8lld %s\n", t, w, result ? "ALLOW" : "DENY");
    }

    limiter_free(lim);
    return 0;
}
```

**Expected Output:**

```
Fixed Window Rate Limiter (limit=3, window=10s)
Timestamp    Window     Result
─────────────────────────────
t=0          w=0        ALLOW
t=1          w=0        ALLOW
t=2          w=0        ALLOW
t=3          w=0        DENY    ← 4th request in window 0
t=10         w=1        ALLOW   ← new window resets counter
t=11         w=1        ALLOW
t=12         w=1        ALLOW
t=19         w=1        DENY
t=20         w=2        ALLOW   ← new window again
t=20         w=2        ALLOW
```

---

### Rust Implementation

```rust
/// Fixed Window Rate Limiter
///
/// Divides time into discrete equal-length windows and counts
/// requests per window.
struct FixedWindowLimiter {
    window_start: i64,   // Unix timestamp of current window's start
    count: u32,          // requests in current window
    limit: u32,          // max requests allowed
    window_secs: i64,    // window duration in seconds
}

impl FixedWindowLimiter {
    fn new(limit: u32, window_secs: i64) -> Self {
        Self {
            window_start: 0,
            count: 0,
            limit,
            window_secs,
        }
    }

    /// Returns true if the request at `timestamp` is allowed.
    ///
    /// Time:  O(1)
    /// Space: O(1)
    fn allow(&mut self, timestamp: i64) -> bool {
        // Determine which window this timestamp belongs to
        let window_id    = timestamp / self.window_secs;
        let window_start = window_id * self.window_secs;

        // If we've entered a new window, reset the counter
        if window_start != self.window_start {
            self.window_start = window_start;
            self.count = 0;
        }

        // Check and enforce the limit
        if self.count < self.limit {
            self.count += 1;
            true
        } else {
            false
        }
    }
}

fn main() {
    let mut limiter = FixedWindowLimiter::new(3, 10);

    let timestamps = [0i64, 1, 2, 3, 10, 11, 12, 19, 20, 20];
    println!("{:<12} {:<8} {}", "Timestamp", "Window", "Result");
    println!("{}", "─".repeat(30));

    for &t in &timestamps {
        let window = t / 10;
        let result = limiter.allow(t);
        println!("t={:<10} w={:<6} {}", t, window, if result { "ALLOW" } else { "DENY" });
    }
}
```

---

### Go Implementation

```go
package main

import "fmt"

// FixedWindowLimiter implements a fixed-window rate limiter.
type FixedWindowLimiter struct {
    windowStart int64 // timestamp of current window's start
    count       int   // requests in current window
    limit       int   // max requests per window
    windowSecs  int64 // window size in seconds
}

// NewFixedWindowLimiter creates a new limiter.
func NewFixedWindowLimiter(limit int, windowSecs int64) *FixedWindowLimiter {
    return &FixedWindowLimiter{
        limit:      limit,
        windowSecs: windowSecs,
    }
}

// Allow returns true if the request at timestamp should be permitted.
//
// Time:  O(1)
// Space: O(1)
func (l *FixedWindowLimiter) Allow(timestamp int64) bool {
    windowID    := timestamp / l.windowSecs
    windowStart := windowID * l.windowSecs

    if windowStart != l.windowStart {
        l.windowStart = windowStart
        l.count = 0
    }

    if l.count < l.limit {
        l.count++
        return true
    }
    return false
}

func main() {
    lim := NewFixedWindowLimiter(3, 10)
    timestamps := []int64{0, 1, 2, 3, 10, 11, 12, 19, 20, 20}

    fmt.Printf("%-12s %-8s %s\n", "Timestamp", "Window", "Result")
    for _, t := range timestamps {
        result := lim.Allow(t)
        status := "ALLOW"
        if !result { status = "DENY" }
        fmt.Printf("t=%-10d w=%-6d %s\n", t, t/10, status)
    }
}
```

---

## 15. Advanced — Fixed Window + Deque (Monotonic Queue for Sliding Max)

### Problem: Maximum in Every Window of Size K

**Problem Statement:** Given array `arr` and window size `k`, find the **maximum element** in each window.

```
Input:  arr = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3
Output: [3, 3, 5, 5, 6, 7]

Window [1,  3, -1]: max = 3
Window [3, -1, -3]: max = 3
Window [-1, -3, 5]: max = 5
Window [-3,  5, 3]: max = 5
Window [5,  3,  6]: max = 6
Window [3,  6,  7]: max = 7
```

**Why is this hard?** Unlike sum, when you remove the maximum element from the window, you don't know the new maximum in O(1).

### The Monotonic Deque Solution

#### What is a Monotonic Deque?

A **Monotonic Deque** is a deque that maintains elements in **sorted order** (either always increasing or always decreasing). For sliding maximum, we maintain a **decreasing deque**.

**Invariant:** The deque always contains indices of elements in the current window, **in decreasing order of their values**. The front is always the index of the current maximum.

```
Decreasing Monotonic Deque — Visual Invariant:
                         ┌─────────────────────┐
front → │ idx_of_max │ idx_2 │ idx_3 │ ... │ ← back
        └─────────────────────────────────────┘
        arr[front] ≥ arr[idx_2] ≥ arr[idx_3] ≥ ...

When adding element at index i:
  → Pop all indices from back where arr[back] ≤ arr[i]
    (they can NEVER be the maximum while arr[i] is in window)
  → Push i to back

When the window slides right:
  → If front index < window left boundary: pop from front

The front always gives the current window's maximum!
```

---

### C Implementation (Monotonic Deque for Sliding Max)

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * sliding_window_max
 *
 * Finds the maximum element in each window of size k using
 * a monotonic (decreasing) deque.
 *
 * KEY INVARIANT:
 *   deque stores indices in current window, front = index of maximum.
 *   elements in deque are always in decreasing order of arr values.
 *
 * TIME:  O(n) — each element pushed and popped at most once
 * SPACE: O(k) — deque holds at most k indices
 */
int *sliding_window_max(const int *arr, int n, int k, int *out_size) {
    if (k <= 0 || k > n) { *out_size = 0; return NULL; }

    int count   = n - k + 1;
    *out_size   = count;
    int *result = malloc(count * sizeof(int));
    int *dq     = malloc(n * sizeof(int)); /* deque stores indices */
    int front   = 0, back = 0;            /* dq[front..back-1] */

    for (int i = 0; i < n; i++) {
        /* Step 1: Remove front if it's outside the window */
        /* Left boundary of current window: i - k + 1 */
        if (front < back && dq[front] < i - k + 1) front++;

        /* Step 2: Remove from back all elements < arr[i] */
        /* They can never be the max while arr[i] is in the window */
        while (front < back && arr[dq[back - 1]] <= arr[i]) back--;

        /* Step 3: Add current index to back */
        dq[back++] = i;

        /* Step 4: Record max for completed windows */
        if (i >= k - 1) {
            result[i - k + 1] = arr[dq[front]];
        }
    }

    free(dq);
    return result;
}

int main(void) {
    int arr[] = {1, 3, -1, -3, 5, 3, 6, 7};
    int n = 8, k = 3, out_size = 0;

    int *res = sliding_window_max(arr, n, k, &out_size);
    printf("Sliding max (k=%d): ", k);
    for (int i = 0; i < out_size; i++) printf("%d ", res[i]);
    printf("\n");
    /* Output: 3 3 5 5 6 7 */

    free(res);
    return 0;
}
```

---

### Rust Implementation (Monotonic Deque)

```rust
use std::collections::VecDeque;

/// Returns max element of each window of size k.
///
/// Uses a monotonic decreasing deque.
/// Front of deque = index of current maximum.
///
/// Time:  O(n) — each index pushed/popped at most once
/// Space: O(k) — deque size bounded by window
fn sliding_window_max(arr: &[i32], k: usize) -> Vec<i32> {
    let n = arr.len();
    if k == 0 || k > n { return vec![]; }

    // Deque stores indices. arr[dq.front()] is always the current maximum.
    let mut dq: VecDeque<usize> = VecDeque::new();
    let mut result = Vec::with_capacity(n - k + 1);

    for i in 0..n {
        // Step 1: Remove front index if it's left the window
        // Window left boundary = i - k + 1 (but careful with underflow in usize)
        while dq.front().map_or(false, |&front| {
            front + k <= i  // front < i - k + 1 ↔ front + k < i + 1 ↔ front + k <= i
        }) {
            dq.pop_front();
        }

        // Step 2: Remove from back all indices with smaller values
        while dq.back().map_or(false, |&back| arr[back] <= arr[i]) {
            dq.pop_back();
        }

        // Step 3: Add current index
        dq.push_back(i);

        // Step 4: Record once we have a full window
        if i + 1 >= k {
            result.push(arr[*dq.front().unwrap()]);
        }
    }

    result
}

fn main() {
    let arr = [1i32, 3, -1, -3, 5, 3, 6, 7];
    println!("{:?}", sliding_window_max(&arr, 3));
    // [3, 3, 5, 5, 6, 7]

    // All same
    println!("{:?}", sliding_window_max(&[4, 4, 4, 4], 2));
    // [4, 4, 4]

    // Descending input
    println!("{:?}", sliding_window_max(&[5, 4, 3, 2, 1], 3));
    // [5, 4, 3]
}
```

---

### Deque State Visualization

```
arr = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3

i=0: Push 0. Deque (indices): [0]       arr values: [1]
i=1: arr[0]=1 <= arr[1]=3, pop 0. Push 1. Deque: [1]  values: [3]
i=2: arr[2]=-1 < arr[1]=3. Push 2.    Deque: [1,2]    values: [3,-1]
     i>=k-1 (2>=2): result[0] = arr[dq.front()] = arr[1] = 3 ✓

i=3: Front=1, still in window [1..3]. arr[3]=-3 < arr[2]=-1. Push 3.
     Deque: [1,2,3]  values: [3,-1,-3]
     result[1] = arr[1] = 3 ✓

i=4: Front=1, left boundary=4-3+1=2. Pop front (1<2). Front=2.
     arr[4]=5 > arr[3]=-3, pop 3. arr[4]=5 > arr[2]=-1, pop 2. Push 4.
     Deque: [4]  values: [5]
     result[2] = arr[4] = 5 ✓

i=5: Front=4, still in window [3..5]. arr[5]=3 < arr[4]=5. Push 5.
     Deque: [4,5]  values: [5,3]
     result[3] = arr[4] = 5 ✓

i=6: Front=4, left boundary=4. Still valid. arr[6]=6>arr[5]=3, pop 5.
     arr[6]=6>arr[4]=5, pop 4. Push 6. Deque: [6]  values: [6]
     result[4] = arr[6] = 6 ✓

i=7: Front=6, still valid. arr[7]=7>arr[6]=6, pop 6. Push 7.
     Deque: [7]  values: [7]
     result[5] = arr[7] = 7 ✓

Final: [3, 3, 5, 5, 6, 7]  ✓
```

---

## 16. Time & Space Complexity Analysis

### Complexity Table

```
┌─────────────────────────────────────┬──────────┬──────────┬──────────────────┐
│  Problem                            │  Naive   │  Fixed   │  Notes           │
│                                     │  Time    │ Window   │                  │
│                                     │          │  Time    │                  │
├─────────────────────────────────────┼──────────┼──────────┼──────────────────┤
│ Max/Min Sum of k elements           │  O(n·k)  │  O(n)    │ O(1) update      │
│ Average of each window              │  O(n·k)  │  O(n)    │ O(1) update      │
│ Distinct count per window           │  O(n·k)  │  O(n)    │ HashMap O(1) avg │
│ Anagram detection                   │  O(n·k)  │  O(n)    │ Fixed 26-char    │
│ First negative per window           │  O(n·k)  │  O(n)    │ Deque O(1) amort │
│ Sliding window maximum              │  O(n·k)  │  O(n)    │ Monotonic deque  │
│ Rate limiting (per request)         │  O(1)    │  O(1)    │ Single counter   │
└─────────────────────────────────────┴──────────┴──────────┴──────────────────┘
```

### Space Complexity

```
┌─────────────────────────────────────┬──────────────────────────────┐
│  Problem                            │  Space                       │
├─────────────────────────────────────┼──────────────────────────────┤
│ Max/Min Sum                         │ O(1) — just a running sum    │
│ Average                             │ O(n-k+1) — output array      │
│ Distinct count                      │ O(k) — freq map              │
│ Anagram detection                   │ O(1) — two 26-char arrays    │
│ First negative                      │ O(k) — deque                 │
│ Sliding max (monotonic deque)        │ O(k) — deque                 │
│ Rate limiting                       │ O(1) — single counter        │
└─────────────────────────────────────┴──────────────────────────────┘
```

### Why O(n) Despite the Loop Inside?

The "two loops make O(n²)" intuition **doesn't apply to the monotonic deque**. Here's the proof:

```
Claim: Total operations on deque = O(n)

Proof:
  Each element arr[i] is pushed into the deque exactly ONCE.
  Each element arr[i] is popped from the deque at most ONCE.
  Total push operations: n
  Total pop  operations: at most n

  Therefore: total deque operations = O(2n) = O(n)

This is called "amortized O(1) per element."
It's a key insight: the inner while loop may run many times for one i,
but it can't run more than n times TOTAL across all iterations of outer loop.
```

---

## 17. Common Mistakes & Edge Cases

### Mistake 1: Off-by-One in Window Boundary

```
WRONG:
  for i in k+1 .. n:           ← misses first slide (k → k)

CORRECT:
  for i in k .. n:              ← i=k is first slide
```

Trace: For n=5, k=3:
```
WRONG starts at i=4, only gives 1 window after initial.
CORRECT starts at i=3, gives 3 windows total (n-k+1 = 3 ✓).
```

### Mistake 2: Integer Overflow in Sum

```c
// WRONG for large values:
int sum = 0;
sum += arr[i];  // overflow if arr[i] is large and sum is near INT_MAX

// CORRECT:
long long sum = 0;  // use 64-bit integer
```

### Mistake 3: k > n (Invalid Window)

```
If k > n, there are ZERO valid windows.
Always check: if (k > n || k <= 0) return INVALID
```

### Mistake 4: Forgetting to Shrink Deque Front

```
When sliding the window, you must evict indices that have
moved outside the window's left boundary.

WRONG (missing front eviction):
  dq.push(i)
  if i >= k-1: result.push(arr[dq.front()])  ← stale max!

CORRECT:
  while dq.front() < i - k + 1: dq.pop_front()
  dq.push(i)
  if i >= k-1: result.push(arr[dq.front()])
```

### Mistake 5: Treating Negative Numbers Incorrectly

```
For max sum, negative numbers DON'T require special handling —
the algorithm works correctly because it just tracks the running sum.

For "first negative" problem, be careful:
  arr[i] < 0   (strictly less than zero)
  NOT arr[i] <= 0  (would include zeros, which aren't negative)
```

### Edge Case Checklist

```
□ k == 1       → every element is its own window
□ k == n       → entire array is one window
□ k > n        → no valid windows exist
□ k == 0       → invalid, guard against
□ n == 0       → empty array, return empty result
□ all same     → all windows have identical results
□ all negative → algorithm must still find the least-negative sum
□ sorted asc   → last window has maximum sum
□ sorted desc  → first window has maximum sum
```

---

## 18. Cognitive Strategies & Mental Models

### Mental Model 1: The Conveyor Belt

Think of the window as a **fixed-length conveyor belt** moving over a static array. Items enter from the right, fall off the left. Your job is to maintain some aggregate (sum, max, count) of what's currently on the belt.

```
Static array:    [ 2,  1,  5,  1,  3,  2 ]
                   ↑  ↑  ↑
Conveyor belt:  [ •   •   • ]
                 ↑   ↑
               falls  enters
               off    on
```

### Mental Model 2: The Sliding Frame

Imagine a physical frame of width k sliding over a number line. The frame never changes size. You're computing a property of what's visible through the frame.

### Mental Model 3: Incremental Delta

The expert's mantra:
> **"What was added? What was removed? How does the state change?"**

For every fixed window problem, ask these three questions first. If you can answer each in O(1), you have an O(n) solution.

```
Sum:       added = arr[right],    removed = arr[left],  Δ = added - removed
Frequency: added = freq[in]++,   removed = freq[out]--, Δ = ±1 if count crosses 0
Max/Min:   needs Monotonic Deque (O(1) amortized)
```

### Deliberate Practice Strategy

To reach top 1%, use this framework for every Fixed Window problem:

```
STEP 1 — RECOGNIZE (5 seconds)
  Read problem → identify "contiguous k-size subarray" → Fixed Window

STEP 2 — CHARACTERIZE (1 minute)
  What property? (sum / frequency / max / ...)
  Can it be updated in O(1)? How?

STEP 3 — TEMPLATE (2 minutes)
  Write the template skeleton first (init + slide + result)
  Then fill in the specific update logic

STEP 4 — TRACE (2 minutes)
  Manually trace through the example
  Verify index math: outgoing = arr[i-k], incoming = arr[i]

STEP 5 — EDGE CASES (1 minute)
  k > n? k = 0? Empty array? All negatives?
```

### The Chunking Principle (Cognitive Science)

In **cognitive psychology**, **chunking** is the process of grouping items into a single unit. Expert chess players see "rook-bishop battery" not "white piece on e1 and white piece on f1." Expert DSA solvers see "Fixed Window" not "nested loop with sum." Build your chunk library by solving 20+ Fixed Window problems until the pattern fires instantly.

### The Deliberate Practice Loop

```
┌─────────────────────────────────────────────────────┐
│              DELIBERATE PRACTICE LOOP                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Solve without hints (even if you fail)          │
│     → Failure = neural pathway being built         │
│                                                     │
│  2. Review optimal solution                         │
│     → Understand EVERY line                        │
│                                                     │
│  3. Re-implement from scratch                       │
│     → Not copy-paste; true encoding               │
│                                                     │
│  4. Solve variations                               │
│     → Max sum → min sum → avg → distinct           │
│     → Each variation sharpens the abstraction      │
│                                                     │
│  5. Teach it                                       │
│     → Feynman technique: explain to a rubber duck  │
│     → Gaps in explanation = gaps in understanding  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 19. Summary Cheat Sheet

### Fixed Window at a Glance

```
PROBLEM SIGNAL:    "subarray/substring of exactly k elements"
CORE IDEA:         Slide a k-size frame; update in O(1) per step
COMPLEXITY:        Time O(n), Space O(1) to O(k)
KEY INVARIANT:     R - L + 1 == k  at all times
WINDOWS COUNT:     n - k + 1

TEMPLATE:
  init  = compute(arr[0..k-1])
  for i in k..n:
    window = update(window, remove=arr[i-k], add=arr[i])
    best   = max/min/combine(best, window)
  return best
```

### Update Strategies

```
┌──────────────────┬────────────────────────────────────┬────────────┐
│  Property        │  O(1) Update Rule                  │  Extra DS  │
├──────────────────┼────────────────────────────────────┼────────────┤
│ Sum              │ sum += in - out                    │ None       │
│ Average          │ avg = (sum += in - out) / k        │ None       │
│ Frequency/Count  │ freq[in]++; freq[out]--;           │ HashMap    │
│                  │ distinct ± 1 if freq crosses 0     │            │
│ Max (naive)      │ Re-scan window: O(k)               │ None       │
│ Max (optimal)    │ Monotonic decreasing deque         │ Deque O(k) │
│ Min (optimal)    │ Monotonic increasing deque         │ Deque O(k) │
│ First negative   │ Deque stores indices of negatives  │ Deque O(k) │
└──────────────────┴────────────────────────────────────┴────────────┘
```

### Problem List for Practice

```
BEGINNER:
  □ Maximum sum subarray of size k
  □ Average of all subarrays of size k
  □ Minimum sum subarray of size k

INTERMEDIATE:
  □ First negative in every window of size k
  □ Count distinct elements in every window
  □ Find all anagrams of pattern p in string s
  □ Maximum of all subarrays (monotonic deque)

ADVANCED:
  □ Minimum window containing all distinct chars of pattern
  □ Longest subarray where (max - min) <= k
  □ Fixed window rate limiter (system design)
  □ Number of subarrays with exactly k distinct integers

ELITE:
  □ Minimum number of swaps to group all k blacks together
  □ Maximum sum of k non-overlapping subarrays
  □ Sliding window median (two heaps)
```

### Index Math Quick Reference

```
Window position i (i = 0, 1, ..., n-k):
  Left  boundary: L = i
  Right boundary: R = i + k - 1

When iterating with variable i from k to n-1:
  Current window: [i-k+1 ... i]
  Outgoing element: arr[i - k]      ← leftmost of previous window
  Incoming element: arr[i]          ← new rightmost element
  Window start:    i - k + 1
  Window end:      i
```

---

*Guide complete. Now practice with deliberate intention — 20 problems at this level will make Fixed Window a permanent, instant-recognition pattern in your problem-solving toolkit.*

> *"The expert has made all the mistakes that can be made, in a very narrow field." — Niels Bohr*

**2,418 lines · 73KB — your complete Fixed Window guide.** Here's what's packed inside:

---

### What the Guide Covers

**Foundations**
- Terminology dictionary (window, invariant, outgoing/incoming element, deque, monotonic queue — every term defined)
- Physical analogies (conveyor belt, sliding frame) for mental model clarity
- Why Fixed Window transforms O(n·k) → O(n) with the incremental delta trick

**Pattern Recognition**
- Decision tree: Fixed Window vs Dynamic Window vs Two Pointers
- Trigger phrases to recognize the pattern in <5 seconds
- Full algorithm flowcharts and state transition diagrams

**6 Problem Classes** — each with full C, Rust, and Go implementations:
1. Max/Min Sum in fixed window
2. Average of all windows
3. Distinct count per window (HashMap approach)
4. Anagram detection (frequency array + matches counter)
5. First negative in every window (deque)
6. Fixed Window Rate Limiter (real-world system design)

**Advanced**
- Monotonic Deque for sliding max/min — with full deque state trace showing WHY it's O(n) despite the inner loop (amortized analysis proof)

**Mastery Layer**
- Common mistakes with exact code showing wrong vs correct
- Edge case checklist (k>n, k=0, all negatives, all same, etc.)
- Deliberate practice loop (the Feynman-method cycle)
- Chunking principle from cognitive science applied to DSA
- Practice problem list from Beginner → Elite