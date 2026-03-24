# Subarray vs. Subset vs. Subsequence
## A World-Class Comprehensive Guide for DSA Mastery

> *"Understanding the shape of data is the first step to commanding it."*

---

## Table of Contents

1. [The Big Picture — Why This Distinction Matters](#1-the-big-picture)
2. [Prerequisite Vocabulary](#2-prerequisite-vocabulary)
3. [Definitions — Precise and Formal](#3-definitions)
4. [Visual ASCII Intuition](#4-visual-ascii-intuition)
5. [Mathematical Foundations](#5-mathematical-foundations)
6. [Counting — How Many of Each?](#6-counting)
7. [Properties Deep Dive](#7-properties-deep-dive)
8. [Enumeration Algorithms (Generate All)](#8-enumeration-algorithms)
9. [The Decision Tree — Which Concept Applies?](#9-decision-tree)
10. [Common Problem Patterns](#10-common-problem-patterns)
11. [Implementations: Rust, Go, C](#11-implementations)
12. [Complexity Analysis Table](#12-complexity-analysis)
13. [Advanced Patterns and Techniques](#13-advanced-patterns)
14. [Mental Models and Problem-Solving Framework](#14-mental-models)
15. [Practice Problems with Expert Thinking](#15-practice-problems)

---

## 1. The Big Picture

When you look at an array like `[3, 1, 4, 1, 5]`, you can ask three fundamentally different questions:

| Question | Concept | Constraint |
|---|---|---|
| "Give me a contiguous window" | Subarray | Must be consecutive, must preserve order |
| "Give me a selection of elements" | Subset | No order needed, no repetition |
| "Give me elements that respect relative order" | Subsequence | Order preserved, not necessarily contiguous |

These three are **not interchangeable**. Using the wrong model in a problem leads to wrong algorithms, wrong complexities, and wrong answers. This guide will burn the distinctions into your intuition permanently.

---

## 2. Prerequisite Vocabulary

Before diving in, let us define every word that will be used:

### Array / Sequence
A **finite, ordered collection** of elements indexed from `0` to `n-1`.
```
arr = [3, 1, 4, 1, 5]
       ^  ^  ^  ^  ^
       0  1  2  3  4    ← indices
```

### Index
A **position** in the array. Index `0` is the first element.

### Contiguous
Means **"touching/adjacent"** — elements that sit next to each other in memory with no gaps between them.
```
[3, 1, 4, 1, 5]
    ^^^^        ← [1, 4] is contiguous (indices 1 and 2 are adjacent)
    ^    ^      ← [1, 1] from index 1 and 3 is NOT contiguous (gap at index 2)
```

### Order Preservation
If element `a` appears before element `b` in the original array, **order is preserved** means `a` also appears before `b` in the derived collection.

### Empty Collection
A collection with **zero elements** — valid in all three concepts.

### Power Set
The **set of all subsets** of a set. If a set has `n` elements, its power set has `2^n` elements.

### Bitmask
A binary number used to **represent which elements are selected**. If the `i`-th bit is `1`, element `i` is included.

---

## 3. Definitions — Precise and Formal

### 3.1 Subarray

> A **subarray** is a **contiguous**, **non-empty** (by most definitions), **order-preserving** portion of an array.

Given array `A[0..n-1]`, a subarray is `A[i..j]` where `0 <= i <= j <= n-1`.

```
A = [3, 1, 4, 1, 5]

Valid subarrays:
  [3]           → A[0..0]
  [3, 1]        → A[0..1]
  [3, 1, 4]     → A[0..2]
  [3, 1, 4, 1]  → A[0..3]
  [3, 1, 4, 1, 5] → A[0..4]
  [1]           → A[1..1]
  [1, 4]        → A[1..2]
  ...
  [5]           → A[4..4]

INVALID as subarray:
  [3, 4]        → NOT contiguous (skips index 1)
  [1, 5]        → NOT contiguous (skips indices 2, 3)
  [5, 1]        → Order not preserved (reversal)
```

**Key insight:** A subarray is defined entirely by its **start index `i`** and **end index `j`**.

---

### 3.2 Subset

> A **subset** is any **selection of elements** from a set, where **order does not matter** and **each element can appear at most once** (based on position, not value).

When applied to an array (which is technically a multiset if values repeat), a subset selects some indices.

```
A = [3, 1, 4]

All subsets (power set):
  {}            → empty subset
  {3}           → select index 0
  {1}           → select index 1
  {4}           → select index 2
  {3, 1}        → select indices 0, 1
  {3, 4}        → select indices 0, 2
  {1, 4}        → select indices 1, 2
  {3, 1, 4}     → select all

Total: 2^3 = 8 subsets
```

**Key insight:** Order does **not** matter. `{3, 4}` and `{4, 3}` are the **same subset**.

---

### 3.3 Subsequence

> A **subsequence** is a collection of elements obtained by **deleting zero or more elements** from the original array **without changing the relative order** of the remaining elements.

```
A = [3, 1, 4, 1, 5]

Valid subsequences:
  []            → delete all
  [3]           → keep only index 0
  [3, 4]        → keep indices 0, 2 (order preserved: 3 before 4 ✓)
  [1, 1]        → keep indices 1, 3 (order preserved: first 1 before second 1 ✓)
  [3, 1, 5]     → keep indices 0, 1, 4 ✓
  [3, 1, 4, 1, 5] → keep all ✓

INVALID as subsequence:
  [4, 1, 3]     → reverses order (4 is at index 2, but 3 is at index 0 — 3 cannot come AFTER 4)
  [5, 1]        → reverses order (5 is at index 4, 1 is at index 1 — 1 cannot come AFTER 5)
```

**Key insight:** A subsequence is defined by a **set of indices** `i1 < i2 < ... < ik`. It is like a subset, but the **order in which elements appear matters** (relative order of chosen indices must be increasing).

---

## 4. Visual ASCII Intuition

### The Fundamental Comparison

```
Original Array:  [ 3 ][ 1 ][ 4 ][ 1 ][ 5 ]
                   0    1    2    3    4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUBARRAY  — Contiguous window, must be a solid block:

  [3, 1, 4] is valid:
  [ 3 ][ 1 ][ 4 ][ 1 ][ 5 ]
  |████████████|             ← solid, no gaps

  [3, 4] is INVALID:
  [ 3 ][ 1 ][ 4 ][ 1 ][ 5 ]
  |████|    |███|            ← GAP! Not contiguous.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUBSEQUENCE — Pick elements, but preserve relative order:

  [3, 4, 5] is valid:
  [ 3 ][ 1 ][ 4 ][ 1 ][ 5 ]
   (*)       (*)       (*)   ← indices 0, 2, 4 — order preserved

  [4, 3] is INVALID:
  [ 3 ][ 1 ][ 4 ][ 1 ][ 5 ]
             (4)  (3)?        ← 3 is at index 0, can't come AFTER 4 at index 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUBSET — Pick elements, order doesn't matter:

  {3, 4} is valid:
  [ 3 ][ 4 ] — order in output doesn't matter, {4, 3} is same subset

  {4, 3} is also the SAME subset as {3, 4}.
  No ordering constraint at all.
```

---

### Venn Relationship Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                        ALL SUBSETS                          │
│   {any selection of elements, any order, duplicates ok}     │
│                                                             │
│   ┌───────────────────────────────────────────────────┐     │
│   │               ALL SUBSEQUENCES                   │     │
│   │   {selection preserving relative order}           │     │
│   │                                                   │     │
│   │   ┌───────────────────────────────────────┐       │     │
│   │   │           ALL SUBARRAYS               │       │     │
│   │   │   {contiguous, order preserved}       │       │     │
│   │   │                                       │       │     │
│   │   └───────────────────────────────────────┘       │     │
│   │                                                   │     │
│   └───────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Every subarray is also a subsequence.
Every subsequence is also a subset (if we ignore ordering).
NOT every subsequence is a subarray.
NOT every subset is a subsequence (order might be violated).
```

---

### Index Lattice — Understanding via Index Selection

```
Array: [A, B, C, D]   (indices 0, 1, 2, 3)

SUBARRAY requires: consecutive index range [i, j]
  Valid index sets: {0}, {1}, {2}, {3},
                   {0,1}, {1,2}, {2,3},
                   {0,1,2}, {1,2,3},
                   {0,1,2,3}
  Count: n*(n+1)/2 = 10

SUBSEQUENCE requires: strictly increasing indices i1 < i2 < ... < ik
  Valid index sets: {}, {0}, {1}, {2}, {3},
                   {0,1}, {0,2}, {0,3}, {1,2}, {1,3}, {2,3},
                   {0,1,2}, {0,1,3}, {0,2,3}, {1,2,3},
                   {0,1,2,3}
  Count: 2^n = 16

SUBSET: same as subsequence (both pick from n elements, each at most once)
  But in the context of a SET (not array), order in output doesn't matter.
  Count: 2^n = 16
```

---

## 5. Mathematical Foundations

### 5.1 Counting Subarrays

For an array of length `n`:

```
Number of subarrays = n*(n+1)/2

Derivation:
  - Choose start index i: n choices
  - Choose end index j >= i: (n - i) choices
  - Total = Σ(i=0 to n-1) (n - i) = n + (n-1) + ... + 1 = n*(n+1)/2

For n=5: 5*6/2 = 15
```

### 5.2 Counting Subsequences

```
Number of non-empty subsequences = 2^n - 1
Number of subsequences (including empty) = 2^n

Derivation:
  - For each of the n elements, independently decide: include or exclude
  - 2 choices per element → 2^n total

For n=5: 2^5 = 32 (including empty), 31 non-empty
```

### 5.3 Counting Subsets

```
Same as subsequences: 2^n (including empty set)

Note: If elements are DISTINCT, |subsets| = |subsequences|
If elements REPEAT, subsequences count duplicates by position,
but subsets by value may be fewer.
```

### 5.4 Growth Rate Comparison

```
n=5:    subarrays=15,      subsequences=32,       subsets≤32
n=10:   subarrays=55,      subsequences=1024,     subsets≤1024
n=20:   subarrays=210,     subsequences=1048576,  subsets≤1048576
n=30:   subarrays=465,     subsequences≈10^9,     subsets≈10^9
n=50:   subarrays=1275,    subsequences≈10^15,    subsets≈10^15

KEY INSIGHT:
  Subarrays grow as O(n^2)       → polynomial, tractable
  Subsequences/Subsets grow as O(2^n) → exponential, intractable for large n

This is WHY:
  - Subarray problems often allow O(n) or O(n log n) solutions
  - Subset/Subsequence problems often need DP to avoid exponential enumeration
```

---

## 6. Counting

### Visualization of All Subarrays for `[A, B, C, D]`

```
Length 1: [A]   [B]   [C]   [D]
Length 2: [A,B] [B,C] [C,D]
Length 3: [A,B,C] [B,C,D]
Length 4: [A,B,C,D]

Total: 4+3+2+1 = 10 = n*(n+1)/2 where n=4

Visual as a triangle:
     j=0  j=1  j=2  j=3
i=0: [A]  [AB] [ABC][ABCD]
i=1:      [B]  [BC] [BCD]
i=2:           [C]  [CD]
i=3:                [D]
```

### Visualization of All Subsequences for `[A, B, C]`

```
Bitmask → Subsequence:
  000 → []        (empty)
  001 → [C]
  010 → [B]
  011 → [B, C]
  100 → [A]
  101 → [A, C]
  110 → [A, B]
  111 → [A, B, C]

Total: 2^3 = 8

The bitmask perfectly encodes which elements to include.
Bit i being SET means "include element at index i".
```

---

## 7. Properties Deep Dive

### 7.1 Subarray Properties

```
Property 1: CONTIGUITY
  A[i..j] is contiguous — every element between index i and j is included.

Property 2: UNIQUENESS BY BOUNDS
  Two subarrays are the same iff they have identical (start, end) pairs.

Property 3: SLIDING WINDOW APPLICABILITY
  Because subarrays are contiguous, you can SLIDE a window across the array.
  Adding one element to the right / removing from left is O(1).
  This makes subarrays amenable to two-pointer / sliding window techniques.

Property 4: PREFIX DECOMPOSITION
  Any subarray A[i..j] = PrefixSum[j] - PrefixSum[i-1]
  This is the basis for prefix sum optimization.

Property 5: SUBARRAY CANNOT SKIP
  If A[i] and A[k] (i < k) are both in a subarray, then A[i+1], ..., A[k-1]
  must also be in that subarray.
```

### 7.2 Subsequence Properties

```
Property 1: ORDER PRESERVATION
  If element A[i] is chosen and element A[j] is chosen with i < j,
  then A[i] appears before A[j] in the subsequence.

Property 2: NO CONTIGUITY REQUIRED
  Gaps are allowed between chosen indices.

Property 3: EVERY SUBARRAY IS A SUBSEQUENCE
  Proof: A subarray A[i..j] selects consecutive indices i, i+1, ..., j.
  These are strictly increasing, so it qualifies as a subsequence. ✓

Property 4: RECURSIVE STRUCTURE (KEY FOR DP)
  A subsequence of A[0..n-1] either:
  - Includes A[n-1], making it (subsequence of A[0..n-2]) + A[n-1], OR
  - Excludes A[n-1], making it just (subsequence of A[0..n-2])
  This binary choice structure is WHY subsequence problems use DP.

Property 5: LCS, LIS EXPLOIT THIS
  Longest Common Subsequence (LCS) and Longest Increasing Subsequence (LIS)
  both exploit the recursive structure above.
```

### 7.3 Subset Properties

```
Property 1: NO ORDER
  {A, B} = {B, A} as sets.

Property 2: POWER SET
  The collection of ALL subsets is called the Power Set, written 2^S or P(S).

Property 3: BITMASK BIJECTION
  For a set of n elements, each subset corresponds to exactly one n-bit binary number.
  This gives a natural way to enumerate all subsets.

Property 4: INCLUSION-EXCLUSION PRINCIPLE
  For counting elements with certain properties:
  |A ∪ B| = |A| + |B| - |A ∩ B|
  This generalizes to multiple sets and is used in combinatorics problems.

Property 5: SUBSET SUM RECURSION (KEY FOR DP)
  "Can we form sum S using some subset of array A?"
  Answer for A[0..i] and sum S =
    (answer for A[0..i-1] and sum S)          [exclude A[i]]
    OR
    (answer for A[0..i-1] and sum S - A[i])   [include A[i]]
```

---

## 8. Enumeration Algorithms

### 8.1 Generate All Subarrays

**Algorithm:**
```
For each start index i from 0 to n-1:
    For each end index j from i to n-1:
        Output A[i..j]

Time: O(n^3) if printing, O(n^2) pairs
Space: O(1) extra (not counting output)
```

**Flow:**
```
i=0 ──► j=0: output [A[0]]
     ──► j=1: output [A[0], A[1]]
     ──► j=2: output [A[0], A[1], A[2]]
     ...
i=1 ──► j=1: output [A[1]]
     ──► j=2: output [A[1], A[2]]
     ...
...
i=n-1 ──► j=n-1: output [A[n-1]]
```

---

### 8.2 Generate All Subsequences (Recursive / Bitmask)

**Recursive approach — Decision Tree:**
```
At each index, make a binary decision: INCLUDE or EXCLUDE

                    []
               /          \
           [A]              []
          /    \           /    \
       [A,B]   [A]       [B]    []
       / \     / \       / \    / \
   [A,B,C][A,B][A,C][A][B,C][B][C][]

Each leaf is a valid subsequence.
Tree has 2^n leaves → 2^n subsequences.
```

**Bitmask approach:**
```
For mask = 0 to 2^n - 1:
    current_subsequence = []
    For bit i = 0 to n-1:
        if mask has bit i set:
            append A[i] to current_subsequence
    Output current_subsequence
```

---

### 8.3 Generate All Subsets

```
Identical to subsequences when elements are treated positionally.

The bitmask method directly applies:
  mask 000...0 → empty set
  mask 111...1 → full set

For set-based (order doesn't matter in output), same as above.
```

---

## 9. Decision Tree — Which Concept Applies?

```
┌─────────────────────────────────────────────────────────────────┐
│          START: You have a problem involving an array           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Must the selected elements   │
          │  be CONTIGUOUS in the array?  │
          └───────────────────────────────┘
                    │           │
                   YES          NO
                    │           │
                    ▼           ▼
            ┌──────────┐    ┌──────────────────────────────────┐
            │ SUBARRAY │    │  Does the RELATIVE ORDER of the  │
            │          │    │  selected elements matter?       │
            │ Use:     │    └──────────────────────────────────┘
            │ Two-ptr  │               │           │
            │ Prefix   │              YES          NO
            │ Sliding  │               │           │
            │ Window   │               ▼           ▼
            └──────────┘       ┌─────────────┐  ┌────────┐
                               │ SUBSEQUENCE │  │ SUBSET │
                               │             │  │        │
                               │ Use:        │  │ Use:   │
                               │ DP (LCS,    │  │ DP     │
                               │  LIS, etc.) │  │ Bitmask│
                               │ Greedy      │  │ Backtr.│
                               └─────────────┘  └────────┘

ADDITIONAL SIGNALS:
  ┌──────────────────────────────────────────────────────────┐
  │ Problem says "contiguous" / "window" → SUBARRAY         │
  │ Problem says "strictly increasing subsequence" → SUBSEQ │
  │ Problem says "select k elements" / "sum subset" → SUBSET│
  │ Problem involves "common" between two arrays → SUBSEQ   │
  │ Problem asks for max/min of contiguous range → SUBARRAY │
  └──────────────────────────────────────────────────────────┘
```

---

## 10. Common Problem Patterns

### 10.1 Subarray Patterns

```
PATTERN 1: Maximum/Minimum Subarray
  Problem: Find subarray with maximum sum (Kadane's Algorithm)
  Key insight: At each position, decide: extend previous subarray or start fresh?
  
  State: max_ending_here = max(A[i], max_ending_here + A[i])
  
  Example: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
  Answer: [4, -1, 2, 1] with sum = 6

─────────────────────────────────────────────────────────────

PATTERN 2: Subarray with Target Sum (Two Pointers / Prefix Sum)
  Problem: Count subarrays with sum = K
  
  Method 1 (Positive numbers): Two-pointer / sliding window
  Method 2 (Any numbers): Prefix sum + HashMap
    - prefix_sum[j] - prefix_sum[i-1] = K
    - So prefix_sum[j] - K = prefix_sum[i-1]
    - Count how many previous prefix sums equal current_prefix - K

─────────────────────────────────────────────────────────────

PATTERN 3: Longest/Shortest Subarray with Property
  Examples:
    - Longest subarray with at most k distinct elements → Sliding window
    - Shortest subarray with sum >= S → Two pointers
  Key: Contiguity allows O(n) sliding window solutions

─────────────────────────────────────────────────────────────

PATTERN 4: Subarray Sum Divisibility
  Problem: Count subarrays divisible by K
  Key: (prefix[j] - prefix[i]) % K == 0
       ⟹ prefix[j] % K == prefix[i] % K
  Use frequency array of remainders.
```

### 10.2 Subsequence Patterns

```
PATTERN 1: Longest Increasing Subsequence (LIS)
  Find the longest subsequence where each element is greater than the previous.
  
  Naive DP: O(n^2)
    dp[i] = max(dp[j] + 1) for all j < i where A[j] < A[i]
  
  Optimized: O(n log n) using patience sorting + binary search

─────────────────────────────────────────────────────────────

PATTERN 2: Longest Common Subsequence (LCS)
  Given two strings/arrays, find the longest subsequence present in both.
  
  DP recurrence:
    if A[i] == B[j]: dp[i][j] = dp[i-1][j-1] + 1
    else:            dp[i][j] = max(dp[i-1][j], dp[i][j-1])

─────────────────────────────────────────────────────────────

PATTERN 3: Is T a Subsequence of S?
  Two pointers: iterate S with one pointer, advance T pointer on match.
  
  i=0 (T pointer), j=0 (S pointer)
  While j < len(S) and i < len(T):
    if S[j] == T[i]: i++
    j++
  Return i == len(T)

─────────────────────────────────────────────────────────────

PATTERN 4: Count Distinct Subsequences
  Classic DP: How many ways can we form T as a subsequence of S?
  dp[i][j] = ways to form T[0..j-1] using S[0..i-1]
```

### 10.3 Subset Patterns

```
PATTERN 1: Subset Sum
  Can we select elements summing to target T?
  
  DP (0/1 Knapsack):
    dp[i][s] = true if we can achieve sum s using first i elements
    dp[i][s] = dp[i-1][s] || dp[i-1][s - A[i]]

─────────────────────────────────────────────────────────────

PATTERN 2: Partition Equal Subset Sum
  Can we split array into two equal-sum subsets?
  
  Reduce to: Can any subset sum to total_sum / 2?
  Use subset sum DP.

─────────────────────────────────────────────────────────────

PATTERN 3: Count Subsets with Given Sum
  Count how many subsets have sum = K
  Same DP but track count instead of boolean.

─────────────────────────────────────────────────────────────

PATTERN 4: Bitmask DP (Small n ≤ 20)
  When n is small, enumerate all 2^n subsets explicitly using bitmasks.
  Common in TSP (Traveling Salesman), Set Cover, etc.
```

---

## 11. Implementations

### 11.1 C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ─────────────────────────────────────────────────────────────
// SECTION A: Generate All Subarrays
// ─────────────────────────────────────────────────────────────

/*
 * Print all subarrays of arr[0..n-1]
 * Time:  O(n^3) — O(n^2) pairs, O(n) to print each
 * Space: O(1) extra
 */
void generate_all_subarrays(int *arr, int n) {
    printf("=== ALL SUBARRAYS ===\n");
    int count = 0;
    for (int i = 0; i < n; i++) {           // start index
        for (int j = i; j < n; j++) {       // end index
            printf("[");
            for (int k = i; k <= j; k++) {
                printf("%d", arr[k]);
                if (k < j) printf(", ");
            }
            printf("]\n");
            count++;
        }
    }
    printf("Total subarrays: %d (expected n*(n+1)/2 = %d)\n\n", count, n*(n+1)/2);
}

// ─────────────────────────────────────────────────────────────
// SECTION B: Generate All Subsequences (Bitmask)
// ─────────────────────────────────────────────────────────────

/*
 * Generate all subsequences using bitmask enumeration.
 *
 * MENTAL MODEL:
 *   mask = 0b101 means "include index 0 and index 2, exclude index 1"
 *   For each mask from 0 to 2^n - 1, we check each bit.
 *
 * Time:  O(n * 2^n) — 2^n masks, O(n) to process each
 * Space: O(1) extra
 */
void generate_all_subsequences_bitmask(int *arr, int n) {
    printf("=== ALL SUBSEQUENCES (Bitmask) ===\n");
    int total = 1 << n;   // 2^n
    int count = 0;

    for (int mask = 0; mask < total; mask++) {
        printf("[");
        int first = 1;
        for (int i = 0; i < n; i++) {
            if (mask & (1 << i)) {   // if bit i is set
                if (!first) printf(", ");
                printf("%d", arr[i]);
                first = 0;
            }
        }
        printf("]  (mask=%d)\n", mask);
        count++;
    }
    printf("Total: %d (expected 2^%d = %d)\n\n", count, n, total);
}

// ─────────────────────────────────────────────────────────────
// SECTION C: Generate All Subsequences (Recursive)
// ─────────────────────────────────────────────────────────────

/*
 * Recursive subsequence generation.
 * At each index, we make a binary choice: INCLUDE or EXCLUDE.
 *
 * RECURSION TREE:
 *   generate(arr, idx, current, n)
 *     ├─ INCLUDE arr[idx], recurse on idx+1
 *     └─ EXCLUDE arr[idx], recurse on idx+1
 *
 * Time:  O(n * 2^n)
 * Space: O(n) stack depth + O(n) current buffer
 */
void generate_subsequences_rec(int *arr, int n, int idx, int *current, int curr_len) {
    if (idx == n) {
        // Base case: print whatever we've accumulated
        printf("[");
        for (int i = 0; i < curr_len; i++) {
            printf("%d", current[i]);
            if (i < curr_len - 1) printf(", ");
        }
        printf("]\n");
        return;
    }
    // Branch 1: INCLUDE arr[idx]
    current[curr_len] = arr[idx];
    generate_subsequences_rec(arr, n, idx + 1, current, curr_len + 1);

    // Branch 2: EXCLUDE arr[idx]
    generate_subsequences_rec(arr, n, idx + 1, current, curr_len);
}

void generate_all_subsequences_recursive(int *arr, int n) {
    printf("=== ALL SUBSEQUENCES (Recursive) ===\n");
    int *current = (int *)malloc(n * sizeof(int));
    generate_subsequences_rec(arr, n, 0, current, 0);
    free(current);
    printf("\n");
}

// ─────────────────────────────────────────────────────────────
// SECTION D: Generate All Subsets (Power Set via Bitmask)
// ─────────────────────────────────────────────────────────────

/*
 * Subsets (power set) — identical to subsequences for arrays,
 * but semantically we don't care about output order.
 *
 * For a SET {3, 1, 4}, {3,4} and {4,3} are the same subset.
 * We always print in index order for consistency.
 */
void generate_power_set(int *arr, int n) {
    printf("=== POWER SET (All Subsets) ===\n");
    int total = 1 << n;

    for (int mask = 0; mask < total; mask++) {
        printf("{");
        int first = 1;
        for (int i = 0; i < n; i++) {
            if (mask & (1 << i)) {
                if (!first) printf(", ");
                printf("%d", arr[i]);
                first = 0;
            }
        }
        printf("}\n");
    }
    printf("\n");
}

// ─────────────────────────────────────────────────────────────
// SECTION E: Kadane's Algorithm (Max Subarray Sum)
// ─────────────────────────────────────────────────────────────

/*
 * KADANE'S ALGORITHM
 *
 * KEY INSIGHT: At each position i, we ask:
 *   "Is it better to extend the best subarray ending at i-1,
 *    or start a brand new subarray at i?"
 *
 * max_ending_here = max(arr[i], max_ending_here + arr[i])
 *
 * Why it works:
 *   If max_ending_here < 0, adding arr[i] to it gives something
 *   smaller than arr[i] alone → better to start fresh.
 *
 * Time:  O(n)
 * Space: O(1)
 */
typedef struct {
    int max_sum;
    int start;   // start index of max subarray
    int end;     // end index of max subarray
} KadaneResult;

KadaneResult kadane(int *arr, int n) {
    KadaneResult res = { arr[0], 0, 0 };
    int max_ending_here = arr[0];
    int temp_start = 0;

    for (int i = 1; i < n; i++) {
        if (max_ending_here + arr[i] < arr[i]) {
            // Starting fresh is better
            max_ending_here = arr[i];
            temp_start = i;
        } else {
            // Extend the current subarray
            max_ending_here += arr[i];
        }

        if (max_ending_here > res.max_sum) {
            res.max_sum = max_ending_here;
            res.start = temp_start;
            res.end = i;
        }
    }
    return res;
}

// ─────────────────────────────────────────────────────────────
// SECTION F: Subset Sum (0/1 Knapsack DP)
// ─────────────────────────────────────────────────────────────

/*
 * SUBSET SUM PROBLEM
 * Can any subset of arr[] sum to target?
 *
 * DP STATE: dp[s] = 1 if sum s is achievable using elements seen so far
 *
 * TRANSITION:
 *   For each element a in arr:
 *     For s from target down to a:   ← IMPORTANT: iterate backwards!
 *       dp[s] |= dp[s - a]
 *
 * WHY iterate backwards?
 *   If we iterate forward, we might use the same element twice.
 *   Going backwards ensures we only use each element once (0/1).
 *
 * Time:  O(n * target)
 * Space: O(target)
 */
int subset_sum(int *arr, int n, int target) {
    int *dp = (int *)calloc(target + 1, sizeof(int));
    dp[0] = 1;   // empty subset sums to 0

    for (int i = 0; i < n; i++) {
        // Traverse backwards to ensure 0/1 property
        for (int s = target; s >= arr[i]; s--) {
            dp[s] |= dp[s - arr[i]];
        }
    }

    int result = dp[target];
    free(dp);
    return result;
}

// ─────────────────────────────────────────────────────────────
// SECTION G: Is T a Subsequence of S? (Two Pointers)
// ─────────────────────────────────────────────────────────────

/*
 * SUBSEQUENCE CHECK
 *
 * MENTAL MODEL:
 *   Walk through S (source) with pointer j.
 *   Try to "match" T (target) left-to-right with pointer i.
 *   Every time S[j] == T[i], advance i (we matched one character of T).
 *   If i reaches len(T), we matched all of T → T is subsequence of S.
 *
 * Visual:
 *   S = [a, c, b, a, b, c]
 *   T = [a, b, c]
 *
 *   j: 0  1  2  3  4  5
 *   S: a  c  b  a  b  c
 *   i: ↑           ← start matching T[0]='a'
 *      match at j=0, i→1 (looking for T[1]='b')
 *                 match at j=2, i→2 (looking for T[2]='c')
 *                             match at j=5, i→3
 *   i == len(T) → TRUE
 *
 * Time:  O(|S| + |T|)
 * Space: O(1)
 */
int is_subsequence(int *S, int len_S, int *T, int len_T) {
    int i = 0;   // pointer into T
    int j = 0;   // pointer into S

    while (j < len_S && i < len_T) {
        if (S[j] == T[i]) {
            i++;   // matched T[i], move to next target
        }
        j++;       // always advance through S
    }

    return i == len_T;   // did we match all of T?
}

// ─────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────

int main(void) {
    int arr[] = {3, 1, 4};
    int n = sizeof(arr) / sizeof(arr[0]);

    generate_all_subarrays(arr, n);
    generate_all_subsequences_bitmask(arr, n);
    generate_all_subsequences_recursive(arr, n);
    generate_power_set(arr, n);

    // Kadane's
    int arr2[] = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
    int n2 = sizeof(arr2) / sizeof(arr2[0]);
    KadaneResult kr = kadane(arr2, n2);
    printf("=== KADANE'S MAX SUBARRAY ===\n");
    printf("Max sum: %d, indices [%d, %d]\n\n", kr.max_sum, kr.start, kr.end);

    // Subset Sum
    int arr3[] = {2, 3, 7, 8, 10};
    int n3 = sizeof(arr3) / sizeof(arr3[0]);
    printf("=== SUBSET SUM ===\n");
    printf("Subset summing to 11: %s\n", subset_sum(arr3, n3, 11) ? "YES" : "NO");
    printf("Subset summing to 6:  %s\n\n", subset_sum(arr3, n3, 6)  ? "YES" : "NO");

    // Subsequence check
    int S[] = {1, 2, 3, 4, 5};
    int T1[] = {1, 3, 5};
    int T2[] = {1, 5, 3};
    printf("=== SUBSEQUENCE CHECK ===\n");
    printf("[1,3,5] is subsequence of [1,2,3,4,5]: %s\n",
           is_subsequence(S, 5, T1, 3) ? "YES" : "NO");
    printf("[1,5,3] is subsequence of [1,2,3,4,5]: %s\n",
           is_subsequence(S, 5, T2, 3) ? "YES" : "NO");

    return 0;
}
```

---

### 11.2 Go Implementation

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────────
// SECTION A: Generate All Subarrays
// ─────────────────────────────────────────────────────────────

// GenerateAllSubarrays prints every contiguous subarray of arr.
//
// COMPLEXITY:
//   Time:  O(n^3) — O(n^2) pairs, O(n) to copy/print each
//   Space: O(n) for the slice copy
func GenerateAllSubarrays(arr []int) {
	fmt.Println("=== ALL SUBARRAYS ===")
	n := len(arr)
	count := 0
	for i := 0; i < n; i++ {
		for j := i; j < n; j++ {
			// arr[i:j+1] is a slice (Go slices are half-open: [i, j+1))
			// NOTE: In Go, arr[i:j+1] does NOT copy — it shares memory.
			// We print it directly here; in production, copy if needed.
			fmt.Printf("  arr[%d:%d] = %v\n", i, j+1, arr[i:j+1])
			count++
		}
	}
	fmt.Printf("Total: %d\n\n", count)
}

// ─────────────────────────────────────────────────────────────
// SECTION B: Generate All Subsequences (Bitmask)
// ─────────────────────────────────────────────────────────────

// GenerateAllSubsequencesBitmask uses bitmask enumeration.
//
// HOW IT WORKS:
//   For each integer mask from 0 to 2^n - 1:
//     bit i of mask is 1 → include arr[i] in this subsequence
//
// COMPLEXITY:
//   Time:  O(n * 2^n)
//   Space: O(n) for the current subsequence slice
func GenerateAllSubsequencesBitmask(arr []int) {
	fmt.Println("=== ALL SUBSEQUENCES (Bitmask) ===")
	n := len(arr)
	total := 1 << n // 2^n

	for mask := 0; mask < total; mask++ {
		subseq := make([]int, 0, n)
		for i := 0; i < n; i++ {
			if mask&(1<<i) != 0 { // bit i is set
				subseq = append(subseq, arr[i])
			}
		}
		fmt.Printf("  mask=%03b → %v\n", mask, subseq)
	}
	fmt.Printf("Total: %d\n\n", total)
}

// ─────────────────────────────────────────────────────────────
// SECTION C: Generate All Subsequences (Recursive Backtracking)
// ─────────────────────────────────────────────────────────────

// generateSubseqRec is the recursive helper.
// current holds the elements chosen so far.
// idx is the current position in arr we're deciding on.
func generateSubseqRec(arr []int, idx int, current []int) {
	if idx == len(arr) {
		// Make a copy to print (current is reused across calls)
		snapshot := make([]int, len(current))
		copy(snapshot, current)
		fmt.Printf("  %v\n", snapshot)
		return
	}
	// Branch 1: INCLUDE arr[idx]
	generateSubseqRec(arr, idx+1, append(current, arr[idx]))

	// Branch 2: EXCLUDE arr[idx]
	// NOTE: We pass current without arr[idx].
	// append(current, arr[idx]) may or may not reuse the underlying array.
	// To be safe with backtracking in Go, we often use current[:len(current)].
	generateSubseqRec(arr, idx+1, current)
}

// GenerateAllSubsequencesRecursive is the public entry point.
func GenerateAllSubsequencesRecursive(arr []int) {
	fmt.Println("=== ALL SUBSEQUENCES (Recursive) ===")
	generateSubseqRec(arr, 0, []int{})
	fmt.Println()
}

// ─────────────────────────────────────────────────────────────
// SECTION D: Kadane's Algorithm
// ─────────────────────────────────────────────────────────────

// KadaneResult holds the result of Kadane's algorithm.
type KadaneResult struct {
	MaxSum int
	Start  int
	End    int
}

// Kadane finds the maximum subarray sum in O(n) time.
//
// ALGORITHM WALKTHROUGH:
//   maxEndingHere: best sum of subarray ending exactly at current index
//   maxSoFar:      best sum seen across all ending positions
//
//   At each index i:
//     Option A: extend previous subarray → maxEndingHere + arr[i]
//     Option B: start fresh subarray     → arr[i]
//     Take the max of these two.
//
//   WHY THIS WORKS:
//     If maxEndingHere < 0, then arr[i] alone is better than
//     arr[i] + maxEndingHere. So we "reset" by starting fresh.
func Kadane(arr []int) KadaneResult {
	if len(arr) == 0 {
		return KadaneResult{}
	}

	maxEndingHere := arr[0]
	maxSoFar := arr[0]
	tempStart := 0
	result := KadaneResult{MaxSum: arr[0], Start: 0, End: 0}

	for i := 1; i < len(arr); i++ {
		if maxEndingHere+arr[i] < arr[i] {
			// Starting fresh is better
			maxEndingHere = arr[i]
			tempStart = i
		} else {
			maxEndingHere += arr[i]
		}

		if maxEndingHere > maxSoFar {
			maxSoFar = maxEndingHere
			result = KadaneResult{MaxSum: maxSoFar, Start: tempStart, End: i}
		}
	}

	return result
}

// ─────────────────────────────────────────────────────────────
// SECTION E: Subset Sum (DP)
// ─────────────────────────────────────────────────────────────

// SubsetSum determines if any subset of arr sums to target.
//
// DP FORMULATION:
//   dp[s] = true if sum s is achievable using a subset of elements seen so far.
//
// INITIALIZATION: dp[0] = true (empty subset has sum 0)
//
// TRANSITION (for each element a):
//   For s from target down to a:
//     dp[s] = dp[s] || dp[s-a]
//
//   Reading this: "Sum s is achievable if either:
//     (a) it was achievable without element a, OR
//     (b) sum (s-a) was achievable and we ADD element a"
//
// WHY backwards iteration?
//   If we went forward: dp[a] becomes true when we process arr[0]=a.
//   Then when s=2a, dp[2a] = dp[a] = true, meaning we used arr[0] TWICE.
//   Going backwards prevents "using an element multiple times."
//
// Time:  O(n * target)
// Space: O(target)
func SubsetSum(arr []int, target int) bool {
	dp := make([]bool, target+1)
	dp[0] = true

	for _, a := range arr {
		// Iterate backwards: prevent using element a multiple times
		for s := target; s >= a; s-- {
			dp[s] = dp[s] || dp[s-a]
		}
	}

	return dp[target]
}

// ─────────────────────────────────────────────────────────────
// SECTION F: Count Subsets with Given Sum
// ─────────────────────────────────────────────────────────────

// CountSubsetsWithSum counts how many subsets sum to target.
//
// Same DP as SubsetSum but we track COUNT instead of boolean.
// dp[s] = number of subsets from elements seen so far that sum to s.
//
// Time:  O(n * target)
// Space: O(target)
func CountSubsetsWithSum(arr []int, target int) int {
	dp := make([]int, target+1)
	dp[0] = 1 // one way to achieve sum 0: empty subset

	for _, a := range arr {
		for s := target; s >= a; s-- {
			dp[s] += dp[s-a]
		}
	}

	return dp[target]
}

// ─────────────────────────────────────────────────────────────
// SECTION G: Is T a Subsequence of S?
// ─────────────────────────────────────────────────────────────

// IsSubsequence checks if t is a subsequence of s using two pointers.
//
// ALGORITHM:
//   i = pointer into t (what we still need to match)
//   j = pointer into s (what we're scanning)
//
//   For each element in s:
//     If it matches t[i], advance i.
//   If i == len(t), we matched all of t.
//
// Time:  O(len(s))
// Space: O(1)
func IsSubsequence(s, t []int) bool {
	i := 0 // pointer into t
	for j := 0; j < len(s) && i < len(t); j++ {
		if s[j] == t[i] {
			i++
		}
	}
	return i == len(t)
}

// ─────────────────────────────────────────────────────────────
// SECTION H: Longest Increasing Subsequence (LIS) — O(n^2) DP
// ─────────────────────────────────────────────────────────────

// LIS finds the length of the Longest Increasing Subsequence.
//
// DP STATE:
//   dp[i] = length of the LIS ending at index i
//
// TRANSITION:
//   For each j < i where arr[j] < arr[i]:
//     dp[i] = max(dp[i], dp[j] + 1)
//
// WHY THIS IS CORRECT:
//   We ask: "What is the longest increasing subsequence that
//   MUST include arr[i] as its last element?"
//   For each earlier element arr[j] < arr[i], we can EXTEND
//   the LIS ending at j by appending arr[i].
//
// EXAMPLE:
//   arr = [10, 9, 2, 5, 3, 7, 101, 18]
//   dp  = [ 1, 1, 1, 2, 2, 3,   4,  4]
//                       ↑ dp[3]=2 because arr[2]=2 < arr[3]=5, dp[2]+1=2
//   Answer: max(dp) = 4  → [2, 3, 7, 101] or [2, 5, 7, 101]
//
// Time:  O(n^2)
// Space: O(n)
func LIS(arr []int) int {
	n := len(arr)
	if n == 0 {
		return 0
	}
	dp := make([]int, n)
	for i := range dp {
		dp[i] = 1 // every element is an LIS of length 1 by itself
	}

	maxLen := 1
	for i := 1; i < n; i++ {
		for j := 0; j < i; j++ {
			if arr[j] < arr[i] && dp[j]+1 > dp[i] {
				dp[i] = dp[j] + 1
			}
		}
		if dp[i] > maxLen {
			maxLen = dp[i]
		}
	}
	return maxLen
}

// ─────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────

func main() {
	arr := []int{3, 1, 4}

	GenerateAllSubarrays(arr)
	GenerateAllSubsequencesBitmask(arr)
	GenerateAllSubsequencesRecursive(arr)

	// Kadane's
	arr2 := []int{-2, 1, -3, 4, -1, 2, 1, -5, 4}
	kr := Kadane(arr2)
	fmt.Printf("=== KADANE'S ===\nMax sum: %d, subarray: %v\n\n",
		kr.MaxSum, arr2[kr.Start:kr.End+1])

	// Subset Sum
	arr3 := []int{2, 3, 7, 8, 10}
	fmt.Println("=== SUBSET SUM ===")
	fmt.Printf("Sum 11 achievable: %v\n", SubsetSum(arr3, 11))
	fmt.Printf("Sum 6 achievable:  %v\n\n", SubsetSum(arr3, 6))

	// Count Subsets
	arr4 := []int{1, 1, 1, 1}
	fmt.Println("=== COUNT SUBSETS WITH SUM 2 ===")
	fmt.Printf("Count: %d\n\n", CountSubsetsWithSum(arr4, 2))

	// Subsequence check
	s := []int{1, 2, 3, 4, 5}
	fmt.Println("=== SUBSEQUENCE CHECK ===")
	fmt.Printf("[1,3,5] ⊆ [1,2,3,4,5]: %v\n", IsSubsequence(s, []int{1, 3, 5}))
	fmt.Printf("[1,5,3] ⊆ [1,2,3,4,5]: %v\n\n", IsSubsequence(s, []int{1, 5, 3}))

	// LIS
	arr5 := []int{10, 9, 2, 5, 3, 7, 101, 18}
	fmt.Println("=== LIS ===")
	fmt.Printf("LIS length of %v: %d\n", arr5, LIS(arr5))
}
```

---

### 11.3 Rust Implementation

```rust
// ─────────────────────────────────────────────────────────────
// Rust: Subarray, Subsequence, Subset Algorithms
//
// RUST-SPECIFIC NOTES:
//   - We use slices (&[i32]) instead of raw pointers for safety
//   - Iterators are idiomatic; we use them where natural
//   - We avoid unnecessary allocations (zero-copy where possible)
//   - The bitmask approach uses Rust's bit manipulation operators
// ─────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────
// SECTION A: Generate All Subarrays
// ─────────────────────────────────────────────────────────────

/// Returns all subarrays as a Vec of Vec<i32>.
///
/// # Complexity
/// - Time: O(n^3)  — O(n^2) pairs × O(n) to clone each slice
/// - Space: O(n^3) total for all subarrays
///
/// # Rust Note
/// `arr[i..=j]` is inclusive range syntax (i through j inclusive).
/// `.to_vec()` copies the slice into an owned Vec<i32>.
pub fn generate_all_subarrays(arr: &[i32]) -> Vec<Vec<i32>> {
    let n = arr.len();
    let mut result = Vec::with_capacity(n * (n + 1) / 2);

    for i in 0..n {
        for j in i..n {
            result.push(arr[i..=j].to_vec());
        }
    }
    result
}

// ─────────────────────────────────────────────────────────────
// SECTION B: Generate All Subsequences (Bitmask)
// ─────────────────────────────────────────────────────────────

/// Generate all subsequences using bitmask enumeration.
///
/// # Mental Model
/// Each u32 value `mask` from 0 to 2^n - 1 represents one subsequence.
/// Bit `i` being set means "include arr[i]".
///
/// # Complexity
/// - Time:  O(n × 2^n)
/// - Space: O(n × 2^n) for all results
///
/// # Rust Note
/// `1u32 << i` shifts the bit left. `mask & (1 << i) != 0` checks if bit i is set.
/// We use u32 here, so max n = 32. For larger n, use u64 or a Vec<bool>.
pub fn generate_all_subsequences_bitmask(arr: &[i32]) -> Vec<Vec<i32>> {
    let n = arr.len();
    assert!(n <= 30, "n must be ≤ 30 for u32 bitmask"); // safety guard

    let total = 1u32 << n; // 2^n
    let mut result = Vec::with_capacity(total as usize);

    for mask in 0..total {
        let subseq: Vec<i32> = (0..n)
            .filter(|&i| mask & (1 << i) != 0) // keep bits that are SET
            .map(|i| arr[i])
            .collect();
        result.push(subseq);
    }
    result
}

// ─────────────────────────────────────────────────────────────
// SECTION C: Generate All Subsequences (Recursive Backtracking)
// ─────────────────────────────────────────────────────────────

/// Recursive subsequence generation.
///
/// # Design
/// We pass `current` as a mutable reference and PUSH/POP elements
/// to simulate the call stack's "include/exclude" binary choices.
/// This is classic backtracking.
///
/// # Rust Note
/// Using `&mut Vec<i32>` avoids allocation on every recursive call.
/// We clone the snapshot only when we reach the base case.
fn generate_subseq_rec(arr: &[i32], idx: usize, current: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
    if idx == arr.len() {
        result.push(current.clone()); // snapshot current state
        return;
    }
    // Branch 1: INCLUDE arr[idx]
    current.push(arr[idx]);
    generate_subseq_rec(arr, idx + 1, current, result);
    current.pop(); // BACKTRACK — undo the inclusion

    // Branch 2: EXCLUDE arr[idx]
    generate_subseq_rec(arr, idx + 1, current, result);
}

pub fn generate_all_subsequences_recursive(arr: &[i32]) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    generate_subseq_rec(arr, 0, &mut current, &mut result);
    result
}

// ─────────────────────────────────────────────────────────────
// SECTION D: Kadane's Algorithm (Max Subarray Sum)
// ─────────────────────────────────────────────────────────────

/// Result of Kadane's algorithm.
#[derive(Debug)]
pub struct KadaneResult {
    pub max_sum: i32,
    pub start: usize,
    pub end: usize,
}

/// Kadane's algorithm: find the maximum sum subarray.
///
/// # Algorithm
/// ```
/// max_ending_here = arr[0]
/// for each element arr[i]:
///     max_ending_here = max(arr[i], max_ending_here + arr[i])
///     max_so_far = max(max_so_far, max_ending_here)
/// ```
///
/// # Key Insight
/// If `max_ending_here` becomes negative, it's dragging future sums down.
/// We reset it to `arr[i]` (start a fresh subarray).
///
/// # Complexity
/// - Time:  O(n)
/// - Space: O(1)
pub fn kadane(arr: &[i32]) -> KadaneResult {
    assert!(!arr.is_empty(), "Array must be non-empty");

    let mut max_ending_here = arr[0];
    let mut max_so_far = arr[0];
    let mut temp_start = 0usize;
    let mut result = KadaneResult { max_sum: arr[0], start: 0, end: 0 };

    for i in 1..arr.len() {
        if max_ending_here + arr[i] < arr[i] {
            max_ending_here = arr[i];
            temp_start = i;
        } else {
            max_ending_here += arr[i];
        }

        if max_ending_here > max_so_far {
            max_so_far = max_ending_here;
            result = KadaneResult { max_sum: max_so_far, start: temp_start, end: i };
        }
    }
    result
}

// ─────────────────────────────────────────────────────────────
// SECTION E: Subset Sum (DP)
// ─────────────────────────────────────────────────────────────

/// Check if any subset of `arr` sums to `target`.
///
/// # DP Formulation
/// dp[s] = true means "sum s is achievable using some subset of seen elements"
///
/// # Transition
/// For each element `a`:
///   for s in (a..=target).rev():    ← reverse prevents using `a` twice
///     dp[s] |= dp[s - a]
///
/// # Rust Note
/// We iterate over the range in reverse using `.rev()`.
/// `dp[s] |= dp[s - a]` is equivalent to `dp[s] = dp[s] || dp[s - a]`.
///
/// # Complexity
/// - Time:  O(n × target)
/// - Space: O(target)
pub fn subset_sum(arr: &[i32], target: usize) -> bool {
    let mut dp = vec![false; target + 1];
    dp[0] = true; // empty subset sums to 0

    for &a in arr {
        let a = a as usize;
        if a > target { continue; }
        // Reverse iteration: crucial for 0/1 knapsack correctness
        for s in (a..=target).rev() {
            if dp[s - a] {
                dp[s] = true;
            }
        }
    }

    dp[target]
}

// ─────────────────────────────────────────────────────────────
// SECTION F: Count Subsets with Given Sum
// ─────────────────────────────────────────────────────────────

/// Count the number of subsets that sum to `target`.
///
/// Same structure as subset_sum, but dp[s] now holds COUNT.
///
/// # Complexity
/// - Time:  O(n × target)
/// - Space: O(target)
pub fn count_subsets_with_sum(arr: &[i32], target: usize) -> u64 {
    let mut dp = vec![0u64; target + 1];
    dp[0] = 1; // one way to form sum 0: pick nothing

    for &a in arr {
        let a = a as usize;
        if a > target { continue; }
        for s in (a..=target).rev() {
            dp[s] += dp[s - a];
        }
    }

    dp[target]
}

// ─────────────────────────────────────────────────────────────
// SECTION G: Is T a Subsequence of S?
// ─────────────────────────────────────────────────────────────

/// Check if `t` is a subsequence of `s`.
///
/// # Algorithm
/// Two pointers: `i` tracks position in `t`, `j` scans `s`.
/// When `s[j] == t[i]`, we've matched one element of `t`, so advance `i`.
/// If `i` reaches `t.len()`, all of `t` has been matched.
///
/// # Complexity
/// - Time:  O(|s|)
/// - Space: O(1)
pub fn is_subsequence(s: &[i32], t: &[i32]) -> bool {
    let mut i = 0; // pointer into t
    let mut j = 0; // pointer into s

    while j < s.len() && i < t.len() {
        if s[j] == t[i] {
            i += 1; // matched t[i], move to next target character
        }
        j += 1;
    }

    i == t.len()
}

// ─────────────────────────────────────────────────────────────
// SECTION H: Longest Increasing Subsequence (LIS) — O(n^2)
// ─────────────────────────────────────────────────────────────

/// Find the length of the Longest Increasing Subsequence.
///
/// # DP State
/// dp[i] = length of the LIS that ENDS at index i.
///
/// # Transition
/// For each j < i where arr[j] < arr[i]:
///   dp[i] = max(dp[i], dp[j] + 1)
///
/// # Reading the Transition
/// "The LIS ending at i is at least as long as the LIS ending at j,
/// extended by one element (arr[i])."
///
/// # Complexity
/// - Time:  O(n^2)
/// - Space: O(n)
pub fn lis(arr: &[i32]) -> usize {
    if arr.is_empty() {
        return 0;
    }
    let n = arr.len();
    let mut dp = vec![1usize; n]; // each element alone is an LIS of length 1

    for i in 1..n {
        for j in 0..i {
            if arr[j] < arr[i] {
                dp[i] = dp[i].max(dp[j] + 1);
            }
        }
    }

    *dp.iter().max().unwrap()
}

// ─────────────────────────────────────────────────────────────
// SECTION I: LIS Optimized — O(n log n) using Binary Search
// ─────────────────────────────────────────────────────────────

/// LIS in O(n log n) using the patience sorting / tails array technique.
///
/// # KEY INSIGHT (Patience Sorting)
/// Maintain an array `tails` where tails[i] is the smallest tail element
/// of all increasing subsequences of length i+1 seen so far.
///
/// For each element x:
///   - Find the first position in `tails` where tails[pos] >= x (binary search)
///   - Replace tails[pos] with x (or append if x > all tails)
///
/// The LENGTH of `tails` at the end = length of LIS.
///
/// WHY REPLACING WORKS:
///   We're not tracking the actual subsequence, just the POTENTIAL.
///   Replacing with a smaller value keeps the door open for longer sequences.
///
/// # Example
///   arr = [3, 1, 8, 2, 5]
///   Process 3: tails = [3]
///   Process 1: 1 < 3, replace tails[0]: tails = [1]
///   Process 8: 8 > all, append: tails = [1, 8]
///   Process 2: 2 < 8, replace tails[1]: tails = [1, 2]
///   Process 5: 5 > all, append: tails = [1, 2, 5]
///   Answer: len(tails) = 3
///
/// # Complexity
/// - Time:  O(n log n)
/// - Space: O(n)
pub fn lis_optimized(arr: &[i32]) -> usize {
    let mut tails: Vec<i32> = Vec::new();

    for &x in arr {
        // Binary search: find first index where tails[i] >= x
        let pos = tails.partition_point(|&t| t < x);
        //           ↑ returns index of first element NOT satisfying t < x
        //             i.e., first element where t >= x
        if pos == tails.len() {
            tails.push(x); // x is greater than all tails → extend
        } else {
            tails[pos] = x; // replace with smaller value → maintain potential
        }
    }

    tails.len()
}

// ─────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────

fn main() {
    // Subarrays
    let arr = vec![3, 1, 4];
    println!("=== ALL SUBARRAYS ===");
    let subarrays = generate_all_subarrays(&arr);
    for s in &subarrays {
        println!("  {:?}", s);
    }
    println!("Total: {}\n", subarrays.len());

    // Subsequences
    println!("=== ALL SUBSEQUENCES (bitmask) ===");
    let subseqs = generate_all_subsequences_bitmask(&arr);
    for s in &subseqs {
        println!("  {:?}", s);
    }
    println!("Total: {}\n", subseqs.len());

    println!("=== ALL SUBSEQUENCES (recursive) ===");
    let subseqs2 = generate_all_subsequences_recursive(&arr);
    for s in &subseqs2 {
        println!("  {:?}", s);
    }
    println!("Total: {}\n", subseqs2.len());

    // Kadane
    let arr2 = vec![-2, 1, -3, 4, -1, 2, 1, -5, 4];
    let kr = kadane(&arr2);
    println!("=== KADANE'S ===");
    println!("Max sum: {}, subarray: {:?}\n", kr.max_sum, &arr2[kr.start..=kr.end]);

    // Subset Sum
    let arr3 = vec![2, 3, 7, 8, 10];
    println!("=== SUBSET SUM ===");
    println!("Sum 11: {}", subset_sum(&arr3, 11));
    println!("Sum 6:  {}\n", subset_sum(&arr3, 6));

    // Count Subsets
    let arr4 = vec![1, 1, 1, 1];
    println!("=== COUNT SUBSETS WITH SUM 2 ===");
    println!("Count: {}\n", count_subsets_with_sum(&arr4, 2));

    // Subsequence check
    let s = vec![1, 2, 3, 4, 5];
    println!("=== IS SUBSEQUENCE ===");
    println!("[1,3,5]: {}", is_subsequence(&s, &[1, 3, 5]));
    println!("[1,5,3]: {}\n", is_subsequence(&s, &[1, 5, 3]));

    // LIS
    let arr5 = vec![10, 9, 2, 5, 3, 7, 101, 18];
    println!("=== LIS ===");
    println!("O(n^2) LIS length: {}", lis(&arr5));
    println!("O(n log n) LIS length: {}", lis_optimized(&arr5));
}
```

---

## 12. Complexity Analysis

### Full Comparison Table

```
┌─────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ Operation                   │   Subarray   │ Subsequence  │    Subset    │
├─────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Count (total)               │  O(n^2)      │  O(2^n)      │  O(2^n)      │
│ Enumerate all               │  O(n^3)      │  O(n·2^n)    │  O(n·2^n)    │
│ Check membership            │  O(n)        │  O(n)        │  O(n)        │
│ Find max-sum (Kadane)        │  O(n)        │  N/A         │  N/A         │
│ Find subseq / subset exists │  N/A         │  O(n)        │  O(n·target) │
│ Find LIS / LCS              │  N/A         │  O(n^2) DP   │  N/A         │
│ LIS optimized               │  N/A         │  O(n log n)  │  N/A         │
│ Subset sum (DP)             │  N/A         │  N/A         │ O(n·target)  │
└─────────────────────────────┴──────────────┴──────────────┴──────────────┘
```

### Why Subarray Problems are Easier

```
Subarrays have STRUCTURE that subsequences and subsets lack:

1. CONTIGUITY → Sliding Window: Adding/removing 1 element = O(1) update
2. PREFIX DECOMPOSITION: sum(A[i..j]) = prefix[j] - prefix[i-1]
3. DIVIDE AND CONQUER: A subarray either crosses the midpoint or doesn't

Subsequences and subsets lack this → need DP to avoid exponential brute force.

ANALOGY:
  Subarray = searching a sorted array        → O(log n) binary search
  Subsequence/Subset = searching unsorted    → O(n) linear scan minimum

The structure allows dramatically faster algorithms.
```

---

## 13. Advanced Patterns and Techniques

### 13.1 Prefix Sum — The Subarray Superpower

```
CORE IDEA:
  prefix[i] = arr[0] + arr[1] + ... + arr[i-1]  (prefix[0] = 0)

  Then: sum(arr[i..j]) = prefix[j+1] - prefix[i]

This transforms "sum of subarray" into "difference of two prefix values."
O(n^2) subarray sum computation → O(n) with prefix array.

DERIVATION:
  arr = [3, 1, 4, 1, 5]
  pre = [0, 3, 4, 8, 9, 14]

  sum(arr[1..3]) = arr[1]+arr[2]+arr[3] = 1+4+1 = 6
                = pre[4] - pre[1] = 9 - 3 = 6  ✓

APPLICATION (Count subarrays with sum K):
  prefix[j] - prefix[i] = K
  ⟹ prefix[i] = prefix[j] - K

  As we compute prefix sums left to right, maintain a HashMap:
    freq[prefix_sum] = number of times this prefix sum has occurred.
  
  At each j, count += freq[prefix[j] - K]
  Then add prefix[j] to freq.

  Time: O(n) — single pass with hashmap
```

### 13.2 The Sliding Window Technique

```
APPLICABLE TO: Subarrays only (contiguity is the key enabler)

TEMPLATE:
  left = 0
  for right in 0..n:
      // Add arr[right] to window
      update_window(arr[right])

      // Shrink from left if window is invalid
      while window_is_invalid():
          remove_from_window(arr[left])
          left++

      // Record answer for current valid window
      update_answer(right - left + 1)

EXAMPLES:
  - Longest substring with at most k distinct chars
  - Minimum window substring
  - Maximum sum subarray of size k
  - Subarray with product < k

WHY THIS WORKS:
  Because elements are CONTIGUOUS, adding to the right and removing
  from the left takes O(1) per step → O(n) total.
  This is IMPOSSIBLE for subsequences (non-contiguous).
```

### 13.3 Bitmask DP for Subsets (Small n ≤ 20)

```
WHEN TO USE: n ≤ 20 (at most 2^20 ≈ 1 million states)

STATE: dp[mask] = answer for the subset represented by `mask`

TRANSITION: dp[mask] = f(dp[mask without some bit])

EXAMPLE — Minimum number of sets to cover all elements:
  dp[mask] = min sets needed to cover all elements in mask
  dp[0] = 0  (no elements, no sets needed)
  dp[mask] = min over all subsets s of mask:
               1 + dp[mask ^ s]   (if s is a valid "cover set")

ITERATING OVER ALL SUBSETS OF A MASK:
  for sub_mask = mask; sub_mask > 0; sub_mask = (sub_mask - 1) & mask:
      // process sub_mask (this is a subset of mask)
  
  This enumerates all subsets of mask in O(2^popcount(mask)) time.
  Total over all masks: O(3^n) (by inclusion of binomial theorem).
```

### 13.4 LCS → Edit Distance → Alignment

```
LCS (Longest Common Subsequence) connects to many string problems:

  LCS(S, T) = longest sequence appearing as subsequence in both S and T

  RELATIONSHIP TO EDIT DISTANCE:
    edit_distance(S, T) = |S| + |T| - 2 * LCS(S, T)
    (substitutions counted as 2 ops: delete + insert)

  DP:
    dp[i][j] = LCS of S[0..i-1] and T[0..j-1]

    if S[i] == T[j]:  dp[i][j] = dp[i-1][j-1] + 1
    else:             dp[i][j] = max(dp[i-1][j], dp[i][j-1])

  VISUALIZATION for S="ABCBDAB", T="BDCAB":
    LCS = "BCAB" or "BDAB" → length 4

  THE 2D DP TABLE PATTERN:
         ""  B  D  C  A  B
      "" [ 0  0  0  0  0  0 ]
      A  [ 0  0  0  0  1  1 ]
      B  [ 0  1  1  1  1  2 ]
      C  [ 0  1  1  2  2  2 ]
      B  [ 0  1  1  2  2  3 ]
      D  [ 0  1  2  2  2  3 ]
      A  [ 0  1  2  2  3  3 ]
      B  [ 0  1  2  2  3  4 ]
```

---

## 14. Mental Models and Problem-Solving Framework

### 14.1 The Three Questions Framework

When you see a problem involving arrays, immediately ask:

```
QUESTION 1: "Are the elements CONTIGUOUS?"
  YES → Think SUBARRAY → Think sliding window, prefix sums, Kadane's
  NO  → Go to question 2

QUESTION 2: "Does RELATIVE ORDER matter?"
  YES → Think SUBSEQUENCE → Think DP (LCS, LIS), two-pointer check
  NO  → Think SUBSET → Think bitmask, knapsack DP, backtracking
```

### 14.2 Recognizing the Constraint

```
SUBARRAY SIGNALS in problem statement:
  "contiguous subarray"
  "subarray with maximum sum"
  "window of size k"
  "subarray starting at index i"
  Any problem where you slide a window

SUBSEQUENCE SIGNALS:
  "without changing relative order"
  "longest increasing subsequence"
  "common subsequence"
  "string matching" (is s a subsequence of t?)
  "delete characters to form"

SUBSET SIGNALS:
  "any selection of elements"
  "can we achieve sum S"
  "partition into two equal parts"
  "choose k elements such that"
  "minimum/maximum sum of exactly k elements"
```

### 14.3 The DP Pattern Recognition

```
SUBARRAY DP (1D):
  dp[i] = answer considering subarray ending at index i
  Example: Kadane's, max product subarray

SUBSEQUENCE DP (1D):
  dp[i] = answer considering subsequence ending at index i
  Example: LIS

SUBSEQUENCE DP (2D — two arrays):
  dp[i][j] = answer for first i elements of A, first j elements of B
  Example: LCS, Edit Distance

SUBSET DP (1D with bitmask):
  dp[mask] = answer for the subset defined by this bitmask
  Example: TSP, Set Cover

SUBSET DP (2D — knapsack):
  dp[i][s] = answer using first i elements with capacity/sum s
  Example: Subset Sum, 0/1 Knapsack
```

### 14.4 Cognitive Principle — Chunking

The concept of **chunking** (from cognitive science, George Miller's "The Magical Number Seven") states that the brain stores information in "chunks" — compressed meaningful units.

For DSA mastery, build these chunks:

```
CHUNK 1: "Contiguous → Sliding Window / Prefix"
  When you see CONTIGUOUS, your brain should IMMEDIATELY fire:
  "O(n) sliding window or prefix sum is likely possible."

CHUNK 2: "Order-preserving selection → DP on index pairs"
  Subsequence DP has a standard template.
  Burn the LCS template into muscle memory.

CHUNK 3: "Selection without order → Bitmask or Knapsack DP"
  Subset problems have a standard 0/1 knapsack DP form.
  The backwards iteration trick is a permanent mental note.

CHUNK 4: "2^n elements → think bitmask, think n ≤ 20"
  If you see exponential growth, ask: is n small enough for bitmask?
  If n > 20, exponential is too slow → need a smarter approach.
```

### 14.5 Deliberate Practice Strategy

```
PHASE 1 — RECOGNITION (Week 1-2):
  Solve 20 problems, categorize them BEFORE coding:
  "Is this subarray, subsequence, or subset?"
  Train the diagnostic reflex.

PHASE 2 — TEMPLATES (Week 3-4):
  Implement each core template (Kadane, LIS, LCS, Subset Sum)
  from scratch, without reference, until fluent.

PHASE 3 — VARIATION (Week 5-8):
  Each template has 5-10 variations (count instead of yes/no,
  find all instead of one, etc.) Practice each variation.

PHASE 4 — COMBINATION (Week 9+):
  Real problems often combine two concepts.
  "Max sum subsequence with no adjacent elements" = DP that
  borrows from both Kadane's intuition and subsequence DP.
```

---

## 15. Practice Problems with Expert Thinking

### Problem 1: Maximum Subarray Sum (Easy → Core)

```
Input:  [-2, 1, -3, 4, -1, 2, 1, -5, 4]
Output: 6 (subarray [4, -1, 2, 1])

EXPERT THINKING PROCESS:
  1. "Maximum sum" + "subarray" → Kadane's algorithm
  2. Key question: "At each position, extend or restart?"
  3. If max_ending_here < 0, restart (negative prefix hurts more than helps)
  4. Track max seen so far separately from current window.
  5. O(n) time, O(1) space — optimal.

TRAP: Students often think O(n^2) brute force is needed.
  Insight: The "restart" decision makes O(n) possible.
```

### Problem 2: Count Subarrays with Sum K (Medium)

```
Input:  arr = [1, 1, 1], k = 2
Output: 2

EXPERT THINKING:
  1. Brute force: O(n^2) check all pairs (i, j), compute sum → 9 operations
  2. Insight: prefix[j] - prefix[i] = k → prefix[i] = prefix[j] - k
  3. As we walk left to right, keep count of each prefix sum in a HashMap.
  4. At position j: answer += count(prefix[j] - k)
  5. O(n) time, O(n) space.

COMMON MISTAKE: Not initializing freq[0] = 1 (for subarrays starting at index 0).
WHY: prefix[0] = 0 before any element. If prefix[j] = k, then
     prefix[j] - prefix[0] = k, which is a valid subarray [0..j].
```

### Problem 3: Longest Increasing Subsequence (Medium → Advanced)

```
Input:  [10, 9, 2, 5, 3, 7, 101, 18]
Output: 4 ([2, 3, 7, 101] or [2, 5, 7, 101])

EXPERT THINKING:
  1. "Longest" + "subsequence" + "increasing" → LIS DP
  2. Naive: For each position, check all earlier positions → O(n^2)
  3. Key observation: We don't need to track which elements are in the LIS,
     only the SMALLEST TAIL of each length class.
  4. tails array: tails[i] = smallest tail of IS of length i+1
  5. Binary search to find where to insert → O(n log n)

DEEPER INSIGHT: This is patience sorting — the same algorithm used
  to sort cards into piles optimally. The number of piles = LIS length.
  This connects to Dilworth's theorem in combinatorics.
```

### Problem 4: Subset Sum (Medium)

```
Input:  arr = [3, 34, 4, 12, 5, 2], target = 9
Output: true ({4, 5} sums to 9)

EXPERT THINKING:
  1. "Any subset" + "sum" → 0/1 Knapsack DP
  2. dp[s] = "can we achieve sum s?"
  3. For each element, update dp backwards to avoid double-counting.
  4. O(n × target) time and O(target) space.

VARIATION 1: Count subsets → dp[s] tracks count, not boolean
VARIATION 2: Find the actual subset → trace back through DP table
VARIATION 3: Partition equal subset → reduce to target = sum/2
```

### Problem 5: Is S a Subsequence of T? (Easy → Understand deeply)

```
Input:  s = "abc", t = "ahbgdc"
Output: true

EXPERT THINKING:
  1. Two pointers: one for s, one for t.
  2. Scan t; when we find s[i], advance i.
  3. If i reaches len(s), all matched → true.
  4. O(|t|) time, O(1) space.

FOLLOW-UP: What if there are 10^9 queries of checking different s
           against the same t?
  Optimization: Precompute for each position j in t and each character c,
                "next occurrence of c at or after position j"
  This allows O(|s| log |t|) per query using binary search.
  Total: O(|t| × 26 + Q × |s| × log|t|) instead of O(Q × |t|).
  This is a beautiful application of preprocessing + binary search.
```

---

## Summary: The Master Cheat Sheet

```
┌─────────────────┬──────────────────┬───────────────────┬───────────────────┐
│                 │    SUBARRAY      │   SUBSEQUENCE     │     SUBSET        │
├─────────────────┼──────────────────┼───────────────────┼───────────────────┤
│ CONTIGUOUS?     │      YES         │       NO          │       NO          │
│ ORDER MATTERS?  │      YES         │      YES          │       NO          │
│ COUNT           │   n*(n+1)/2      │      2^n          │      2^n          │
│ GROWTH          │   O(n^2)         │     O(2^n)        │     O(2^n)        │
│ KEY ALGORITHM   │ Sliding Window   │    DP (LIS/LCS)   │   Knapsack DP     │
│                 │ Prefix Sum       │    Two Pointer    │   Bitmask DP      │
│                 │ Kadane's         │                   │   Backtracking    │
│ EXAMPLES        │ Max sum subarray │  LIS, LCS         │ Subset Sum        │
│                 │ Subarray sum=K   │  Is S ⊆ T?        │ Partition Equal   │
│                 │ Smallest window  │  Count distinct   │ TSP (bitmask)     │
├─────────────────┼──────────────────┼───────────────────┼───────────────────┤
│ SIGNAL WORDS    │ "contiguous"     │ "relative order"  │ "any selection"   │
│                 │ "window"         │ "without changing"│ "partition"       │
│                 │ "consecutive"    │ "delete elements" │ "choose k"        │
└─────────────────┴──────────────────┴───────────────────┴───────────────────┘

HIERARCHY:
  Every SUBARRAY is a SUBSEQUENCE.
  Every SUBSEQUENCE is a SUBSET (ignoring order).
  The reverse does NOT hold.

COMPLEXITY INTUITION:
  More structure (subarray) → faster algorithms (O(n) or O(n^2))
  Less structure (subset) → slower algorithms (O(n × target) or O(n × 2^n))

THE FUNDAMENTAL TRADE-OFF:
  Subarray problems: constraints HELP you → sliding window, prefix sums
  Subsequence/Subset: constraints are LOOSE → need DP to avoid enumeration
```

---

*"Mastery is not about knowing more — it is about seeing more clearly."*

*Keep solving, keep questioning, keep refining. The patterns will reveal themselves.*

Here is your comprehensive guide. Here is what it covers, at a glance:

**Structure of the guide:**

The guide is organized into 15 deep sections. Here are the intellectual highlights worth your attention as you study:

**The single most important insight** — the Venn relationship:
> Every subarray is a subsequence. Every subsequence is a subset. The reverse never holds.

**Why this matters for algorithm design** — subarrays have *structural constraints* (contiguity) that enable O(n) sliding window and O(n) prefix sum tricks. Subsequences and subsets lack this, which is precisely *why* they need DP to avoid exponential enumeration.

**The counting hierarchy** that you must internalize:
- Subarrays: `n*(n+1)/2` — polynomial growth → tractable brute force
- Subsequences/Subsets: `2^n` — exponential growth → DP is mandatory

**Key algorithms covered with full implementations in C, Go, and Rust:**
- All enumeration (subarrays, subsequences, subsets) — bitmask + recursive
- Kadane's Algorithm (max subarray sum) — with index tracking
- Subset Sum / Count Subsets — 0/1 knapsack DP with the backwards-iteration trick explained deeply
- `IsSubsequence` — two-pointer with full visual walkthrough
- LIS — both O(n²) DP and O(n log n) patience sorting (Rust uses `partition_point` idiomatically)

**The backwards-iteration trick in knapsack DP** is explained from first principles — this is the subtlety that trips up almost everyone and the guide explains exactly *why* forward iteration would be wrong.