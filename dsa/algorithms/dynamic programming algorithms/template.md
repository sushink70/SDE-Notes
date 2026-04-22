# 🧠 The Complete Dynamic Programming Bible
## A World-Class Guide to Every DP Pattern, Template & Mental Model

> *"The expert has failed more times than the beginner has even tried."*
> Train your mind to see structure in chaos — DP is the art of remembering your past to build your future.

---

## TABLE OF CONTENTS

1. [What is Dynamic Programming? — The Deep Truth](#1-what-is-dynamic-programming)
2. [The 5-Step Universal DP Framework](#2-the-5-step-universal-dp-framework)
3. [Memoization vs Tabulation — When & Why](#3-memoization-vs-tabulation)
4. [Template 1: Linear DP (1D)](#4-template-1-linear-dp-1d)
5. [Template 2: Knapsack Family](#5-template-2-knapsack-family)
6. [Template 3: Grid / 2D DP](#6-template-3-grid--2d-dp)
7. [Template 4: Interval DP](#7-template-4-interval-dp)
8. [Template 5: Sequence DP (LCS, LIS, Edit Distance)](#8-template-5-sequence-dp)
9. [Template 6: State Machine DP](#9-template-6-state-machine-dp)
10. [Template 7: Tree DP](#10-template-7-tree-dp)
11. [Template 8: Bitmask DP](#11-template-8-bitmask-dp)
12. [Template 9: Digit DP](#12-template-9-digit-dp)
13. [Template 10: Probability & Expected Value DP](#13-template-10-probability--expected-value-dp)
14. [Space Optimization Master Techniques](#14-space-optimization-master-techniques)
15. [DP on Strings — Master Template](#15-dp-on-strings)
16. [Reconstruction: Tracing Back the Answer](#16-reconstruction-tracing-back-the-answer)
17. [Cognitive Principles & Mental Models for DP Mastery](#17-cognitive-principles--mental-models)

---

## 1. What is Dynamic Programming?

### The Intuition Before the Definition

Before memorizing anything, internalize this truth:

> **Dynamic Programming = Smart Recursion with Memory**

Every DP problem is fundamentally a **recursion problem** where the same subproblems appear **repeatedly**. DP says: "solve each subproblem **once**, store the result, reuse it."

### The Two Necessary Conditions

For DP to apply, a problem **must** have both:

```
┌─────────────────────────────────────────────────────────────┐
│  CONDITION 1: Optimal Substructure                          │
│  The optimal solution to the BIG problem contains           │
│  optimal solutions to its SMALLER subproblems.              │
│                                                             │
│  Example: Shortest path A→C through B =                     │
│           Shortest(A→B) + Shortest(B→C)                     │
├─────────────────────────────────────────────────────────────┤
│  CONDITION 2: Overlapping Subproblems                       │
│  The same smaller problems appear MANY TIMES                │
│  during recursion (unlike Divide & Conquer).                │
│                                                             │
│  Example: Fibonacci fib(5) needs fib(3)                     │
│           AND fib(4) also needs fib(3)                      │
│           → fib(3) is computed TWICE without DP             │
└─────────────────────────────────────────────────────────────┘
```

### Why Naive Recursion Fails — Fibonacci Tree

```
fib(5)
├── fib(4)
│   ├── fib(3)         ← computed here
│   │   ├── fib(2)
│   │   │   ├── fib(1)
│   │   │   └── fib(0)
│   │   └── fib(1)
│   └── fib(2)
│       ├── fib(1)
│       └── fib(0)
└── fib(3)             ← computed AGAIN (wasted!)
    ├── fib(2)
    │   ├── fib(1)
    │   └── fib(0)
    └── fib(1)

Without DP: O(2^n) time
With DP:    O(n) time   ← Every node computed ONCE
```

### Three Forms of DP

```
┌──────────────────┬────────────────────┬──────────────────────┐
│  FORM            │  APPROACH          │  DIRECTION           │
├──────────────────┼────────────────────┼──────────────────────┤
│ Top-Down         │ Recursion +        │ Big problem →        │
│ (Memoization)    │ Cache (HashMap)    │ smaller subproblems  │
├──────────────────┼────────────────────┼──────────────────────┤
│ Bottom-Up        │ Iteration +        │ Base cases →         │
│ (Tabulation)     │ DP Table (Array)   │ bigger subproblems   │
├──────────────────┼────────────────────┼──────────────────────┤
│ Space Optimized  │ Bottom-Up but      │ Only keep what       │
│                  │ minimal memory     │ you need             │
└──────────────────┴────────────────────┴──────────────────────┘
```

---

## 2. The 5-Step Universal DP Framework

> This is the mental framework a world-class competitive programmer uses **before writing a single line of code**.

```
╔═══════════════════════════════════════════════════════════════╗
║  STEP 1:  Define the STATE                                    ║
║           What does dp[i] (or dp[i][j]) MEAN?                ║
║           Answer: "dp[i] = the answer to the problem         ║
║                   considering elements 0..i"                  ║
╠═══════════════════════════════════════════════════════════════╣
║  STEP 2:  Define the TRANSITION (Recurrence Relation)        ║
║           How do I build dp[i] from SMALLER states?           ║
║           Answer: "dp[i] = f(dp[i-1], dp[i-2], ...)"        ║
╠═══════════════════════════════════════════════════════════════╣
║  STEP 3:  Define BASE CASES                                   ║
║           What are the smallest valid inputs?                 ║
║           Answer: "dp[0] = ..., dp[1] = ..."                 ║
╠═══════════════════════════════════════════════════════════════╣
║  STEP 4:  Define TRAVERSAL ORDER                              ║
║           Which direction do we fill the table?               ║
║           (Left→Right, Right→Left, Diagonal, etc.)           ║
╠═══════════════════════════════════════════════════════════════╣
║  STEP 5:  Extract the ANSWER                                  ║
║           Where in the table is the final answer?             ║
║           dp[n]? dp[n][m]? max(dp[0..n])?                    ║
╚═══════════════════════════════════════════════════════════════╝
```

### Applying the 5 Steps: Fibonacci

```
STEP 1 — State:
  dp[i] = the i-th Fibonacci number

STEP 2 — Transition:
  dp[i] = dp[i-1] + dp[i-2]

STEP 3 — Base Cases:
  dp[0] = 0
  dp[1] = 1

STEP 4 — Traversal:
  Left → Right (i from 2 to n)

STEP 5 — Answer:
  dp[n]
```

---

## 3. Memoization vs Tabulation

### Visual Comparison

```
PROBLEM: Compute fib(5)

═══════ MEMOIZATION (Top-Down) ═══════    ═══════ TABULATION (Bottom-Up) ═══════

Call stack goes DOWN then fills UP:       Fill table from left to right:

fib(5)                                    Index:  0   1   2   3   4   5
  └─► fib(4)                              Value:  0   1   ?   ?   ?   ?
        └─► fib(3)                                ↓
              └─► fib(2)                  Index:  0   1   2   3   4   5
                    └─► fib(1)=1          Value:  0   1   1   ?   ?   ?
                    └─► fib(0)=0                          ↑
                    memo[2]=1             Index:  0   1   2   3   4   5
              └─► fib(1)=1               Value:  0   1   1   2   ?   ?
              memo[3]=2                                        ↑
        └─► fib(2)=1 (from memo!)        Index:  0   1   2   3   4   5
        memo[4]=3                         Value:  0   1   1   2   3   ?
  └─► fib(3)=2 (from memo!)                                       ↑
  memo[5]=5                               Index:  0   1   2   3   4   5
                                          Value:  0   1   1   2   3   5
RESULT: 5                                                             ↑
                                          RESULT: dp[5] = 5
```

### Decision Guide

```
┌─────────────────────────────────────────────────────────────────┐
│              WHEN TO USE WHICH?                                 │
├────────────────────────┬────────────────────────────────────────┤
│  USE MEMOIZATION when: │  USE TABULATION when:                  │
│                        │                                        │
│  • Not all states      │  • ALL states need to be computed      │
│    need computing      │                                        │
│  • Tree-shaped         │  • Iteration order is clear            │
│    recursion feels     │                                        │
│    natural             │  • Stack overflow is a concern         │
│  • Complex state       │    (very deep recursion)               │
│    transitions         │                                        │
│  • State space is      │  • Need space optimization             │
│    sparse              │  • Performance critical (no            │
│                        │    function call overhead)             │
└────────────────────────┴────────────────────────────────────────┘
```

---

## 4. Template 1: Linear DP (1D)

### Concept

Linear DP is the simplest form. The state is a single index `i`, and `dp[i]` depends on `dp[i-1]`, `dp[i-2]`, etc.

```
Pattern: dp[i] = f(dp[i-1], dp[i-2], ..., dp[0], arr[i])

Visualization:
  arr: [a0, a1, a2, a3, a4, a5]
  dp:  [d0, d1, d2, d3, d4, d5]
              ↑   ↑
              |   depends on these
              This one
```

### Problem: Climbing Stairs

> You can climb 1 or 2 steps at a time. How many ways to reach step n?

**5-Step Analysis:**
```
State:      dp[i] = number of ways to reach step i
Transition: dp[i] = dp[i-1] + dp[i-2]
            (from step i-1 take 1 step, OR from step i-2 take 2 steps)
Base Cases: dp[0] = 1 (already at top — 1 way: do nothing)
            dp[1] = 1 (only 1 step)
Traversal:  Left → Right
Answer:     dp[n]
```

**Simulation Table for n=5:**
```
Step i:  0    1    2    3    4    5
dp[i]:   1    1    2    3    5    8

i=2: dp[2] = dp[1] + dp[0] = 1 + 1 = 2
     (ways: {1+1}, {2})

i=3: dp[3] = dp[2] + dp[1] = 2 + 1 = 3
     (ways: {1+1+1}, {1+2}, {2+1})

i=4: dp[4] = dp[3] + dp[2] = 3 + 2 = 5

i=5: dp[5] = dp[4] + dp[3] = 5 + 3 = 8
```

**Decision Flow:**
```
At step i, you arrived from:
        ┌─────────────┐
        │  Step i     │
        └──────┬──────┘
               │
       ┌───────┴───────┐
       ▼               ▼
  from step i-1    from step i-2
  (took 1 step)    (took 2 steps)
       │               │
  dp[i-1] ways    dp[i-2] ways
       └───────┬───────┘
               ▼
    dp[i] = dp[i-1] + dp[i-2]
```

### Implementation

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

// Bottom-Up Tabulation
int climbStairs(int n) {
    if (n <= 1) return 1;

    int *dp = (int *)malloc((n + 1) * sizeof(int));
    dp[0] = 1;
    dp[1] = 1;

    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }

    int result = dp[n];
    free(dp);
    return result;
}

// Space Optimized: O(1) space
int climbStairsOptimized(int n) {
    if (n <= 1) return 1;
    int prev2 = 1, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}

int main() {
    printf("Ways to climb 5 steps: %d\n", climbStairs(5));        // 8
    printf("Ways to climb 10 steps: %d\n", climbStairsOptimized(10)); // 89
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

// Bottom-Up Tabulation
func climbStairs(n int) int {
    if n <= 1 {
        return 1
    }
    dp := make([]int, n+1)
    dp[0], dp[1] = 1, 1
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    return dp[n]
}

// Space Optimized
func climbStairsOpt(n int) int {
    if n <= 1 {
        return 1
    }
    prev2, prev1 := 1, 1
    for i := 2; i <= n; i++ {
        curr := prev1 + prev2
        prev2 = prev1
        prev1 = curr
    }
    return prev1
}

// Top-Down Memoization
func climbStairsMemo(n int, memo map[int]int) int {
    if n <= 1 {
        return 1
    }
    if val, ok := memo[n]; ok {
        return val
    }
    memo[n] = climbStairsMemo(n-1, memo) + climbStairsMemo(n-2, memo)
    return memo[n]
}

func main() {
    fmt.Println("Climb 5:", climbStairs(5))            // 8
    fmt.Println("Climb 10:", climbStairsOpt(10))       // 89
    memo := make(map[int]int)
    fmt.Println("Climb 15:", climbStairsMemo(15, memo)) // 987
}
```

**Rust:**
```rust
use std::collections::HashMap;

// Bottom-Up Tabulation
fn climb_stairs(n: usize) -> usize {
    if n <= 1 {
        return 1;
    }
    let mut dp = vec![0usize; n + 1];
    dp[0] = 1;
    dp[1] = 1;
    for i in 2..=n {
        dp[i] = dp[i-1] + dp[i-2];
    }
    dp[n]
}

// Space Optimized: O(1) space
fn climb_stairs_opt(n: usize) -> usize {
    if n <= 1 {
        return 1;
    }
    let (mut prev2, mut prev1) = (1usize, 1usize);
    for _ in 2..=n {
        let curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    prev1
}

// Top-Down Memoization
fn climb_stairs_memo(n: usize, memo: &mut HashMap<usize, usize>) -> usize {
    if n <= 1 {
        return 1;
    }
    if let Some(&val) = memo.get(&n) {
        return val;
    }
    let result = climb_stairs_memo(n-1, memo) + climb_stairs_memo(n-2, memo);
    memo.insert(n, result);
    result
}

fn main() {
    println!("Climb 5:  {}", climb_stairs(5));      // 8
    println!("Climb 10: {}", climb_stairs_opt(10));  // 89
    let mut memo = HashMap::new();
    println!("Climb 15: {}", climb_stairs_memo(15, &mut memo)); // 987
}
```

### Problem: House Robber

> Rob houses in a row; cannot rob two adjacent houses. Maximize money.

**5-Step Analysis:**
```
State:      dp[i] = max money robbing houses 0..i
Transition: dp[i] = max(dp[i-1],          ← skip house i
                        dp[i-2] + arr[i]) ← rob house i
Base:       dp[0] = arr[0]
            dp[1] = max(arr[0], arr[1])
Answer:     dp[n-1]
```

**Simulation: arr = [2, 7, 9, 3, 1]**
```
Index:  0    1    2    3    4
arr:   [2,   7,   9,   3,   1]
dp:    [2,   7,   ?,   ?,   ?]

i=2: dp[2] = max(dp[1], dp[0]+arr[2])
           = max(7,     2+9)
           = max(7, 11) = 11
     (rob houses 0 and 2: 2+9=11)

i=3: dp[3] = max(dp[2], dp[1]+arr[3])
           = max(11,    7+3)
           = max(11, 10) = 11
     (still best: rob houses 0 and 2)

i=4: dp[4] = max(dp[3], dp[2]+arr[4])
           = max(11,    11+1)
           = max(11, 12) = 12
     (rob houses 0, 2, 4: 2+9+1=12)

Final dp: [2, 7, 11, 11, 12]
Answer: dp[4] = 12
```

**C:**
```c
#include <stdio.h>

int rob(int *nums, int n) {
    if (n == 0) return 0;
    if (n == 1) return nums[0];

    int dp[n];
    dp[0] = nums[0];
    dp[1] = nums[0] > nums[1] ? nums[0] : nums[1];

    for (int i = 2; i < n; i++) {
        int skip = dp[i-1];
        int take = dp[i-2] + nums[i];
        dp[i] = skip > take ? skip : take;
    }
    return dp[n-1];
}

// Space Optimized
int robOpt(int *nums, int n) {
    if (n == 0) return 0;
    if (n == 1) return nums[0];

    int prev2 = nums[0];
    int prev1 = nums[0] > nums[1] ? nums[0] : nums[1];

    for (int i = 2; i < n; i++) {
        int curr = prev1 > (prev2 + nums[i]) ? prev1 : (prev2 + nums[i]);
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}

int main() {
    int arr[] = {2, 7, 9, 3, 1};
    printf("Max rob: %d\n", rob(arr, 5));    // 12
    printf("Max rob: %d\n", robOpt(arr, 5)); // 12
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

func rob(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }
    if n == 1 {
        return nums[0]
    }
    dp := make([]int, n)
    dp[0] = nums[0]
    if nums[0] > nums[1] {
        dp[1] = nums[0]
    } else {
        dp[1] = nums[1]
    }
    for i := 2; i < n; i++ {
        skip := dp[i-1]
        take := dp[i-2] + nums[i]
        if skip > take {
            dp[i] = skip
        } else {
            dp[i] = take
        }
    }
    return dp[n-1]
}

func main() {
    fmt.Println(rob([]int{2, 7, 9, 3, 1})) // 12
    fmt.Println(rob([]int{1, 2, 3, 1}))    // 4
}
```

**Rust:**
```rust
fn rob(nums: &[i32]) -> i32 {
    let n = nums.len();
    if n == 0 { return 0; }
    if n == 1 { return nums[0]; }

    let mut dp = vec![0i32; n];
    dp[0] = nums[0];
    dp[1] = nums[0].max(nums[1]);

    for i in 2..n {
        dp[i] = dp[i-1].max(dp[i-2] + nums[i]);
    }
    dp[n-1]
}

fn main() {
    println!("{}", rob(&[2, 7, 9, 3, 1])); // 12
    println!("{}", rob(&[1, 2, 3, 1]));    // 4
}
```

---

## 5. Template 2: Knapsack Family

### The Knapsack Family Tree

```
                     KNAPSACK
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
      0/1 Knapsack   Unbounded        Bounded
      (each item     Knapsack         Knapsack
      used 0 or 1    (each item       (each item
      times)         used ∞ times)    used k times)
         │
    ┌────┴────┐
    ▼         ▼
  Subset     Partition
  Sum        Equal Subset
```

### 5a. 0/1 Knapsack

> Given items with weights and values, and a knapsack of capacity W, maximize value without exceeding weight. Each item can be taken AT MOST ONCE.

**5-Step Analysis:**
```
State:      dp[i][w] = max value using first i items with capacity w
Transition: dp[i][w] = max(dp[i-1][w],                  ← don't take item i
                           dp[i-1][w - wt[i]] + val[i]) ← take item i (if w >= wt[i])
Base:       dp[0][w] = 0 for all w (no items → 0 value)
            dp[i][0] = 0 for all i (0 capacity → 0 value)
Answer:     dp[n][W]
```

**Simulation:**
```
Items: weights=[1,3,4,5], values=[1,4,5,7], W=7

     Capacity w →
     0   1   2   3   4   5   6   7
i=0 [0,  0,  0,  0,  0,  0,  0,  0]  ← no items
i=1 [0,  1,  1,  1,  1,  1,  1,  1]  ← item0: wt=1,val=1
i=2 [0,  1,  1,  4,  5,  5,  5,  5]  ← item1: wt=3,val=4
i=3 [0,  1,  1,  4,  5,  6,  6,  9]  ← item2: wt=4,val=5
i=4 [0,  1,  1,  4,  5,  7,  8,  9]  ← item3: wt=5,val=7

Tracing i=3 (item2: wt=4, val=5):
  w=4: max(dp[2][4]=5, dp[2][0]+5=5) = 5
  w=5: max(dp[2][5]=5, dp[2][1]+5=6) = 6  ← take item2 with item0
  w=6: max(dp[2][6]=5, dp[2][2]+5=6) = 6
  w=7: max(dp[2][7]=5, dp[2][3]+5=9) = 9  ← take item2 with item1

Answer: dp[4][7] = 9
  (items 1 (wt=3,val=4) + item 2 (wt=4,val=5) = 9 value, 7 weight)
```

**C:**
```c
#include <stdio.h>
#include <string.h>

#define MAX_N 105
#define MAX_W 1005

int dp[MAX_N][MAX_W];

int max(int a, int b) { return a > b ? a : b; }

// Standard 0/1 Knapsack - O(n*W) time, O(n*W) space
int knapsack01(int *wt, int *val, int n, int W) {
    memset(dp, 0, sizeof(dp));
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            dp[i][w] = dp[i-1][w]; // don't take item i
            if (w >= wt[i-1]) {    // can take item i
                dp[i][w] = max(dp[i][w], dp[i-1][w - wt[i-1]] + val[i-1]);
            }
        }
    }
    return dp[n][W];
}

// Space Optimized 0/1 Knapsack - O(W) space
// CRITICAL: iterate w RIGHT TO LEFT to prevent using same item twice
int knapsack01Opt(int *wt, int *val, int n, int W) {
    int dp[MAX_W];
    memset(dp, 0, sizeof(dp));
    for (int i = 0; i < n; i++) {
        // RIGHT TO LEFT prevents item from being used multiple times
        for (int w = W; w >= wt[i]; w--) {
            dp[w] = max(dp[w], dp[w - wt[i]] + val[i]);
        }
    }
    return dp[W];
}

int main() {
    int wt[]  = {1, 3, 4, 5};
    int val[] = {1, 4, 5, 7};
    int n = 4, W = 7;
    printf("Max value (2D):  %d\n", knapsack01(wt, val, n, W));    // 9
    printf("Max value (1D):  %d\n", knapsack01Opt(wt, val, n, W)); // 9
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

// 0/1 Knapsack - 2D DP
func knapsack01(wt, val []int, W int) int {
    n := len(wt)
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, W+1)
    }
    for i := 1; i <= n; i++ {
        for w := 0; w <= W; w++ {
            dp[i][w] = dp[i-1][w] // don't take
            if w >= wt[i-1] {
                take := dp[i-1][w-wt[i-1]] + val[i-1]
                if take > dp[i][w] {
                    dp[i][w] = take
                }
            }
        }
    }
    return dp[n][W]
}

// 0/1 Knapsack - Space Optimized O(W)
func knapsack01Opt(wt, val []int, W int) int {
    dp := make([]int, W+1)
    for i := 0; i < len(wt); i++ {
        // MUST iterate right to left for 0/1 knapsack!
        for w := W; w >= wt[i]; w-- {
            if dp[w-wt[i]]+val[i] > dp[w] {
                dp[w] = dp[w-wt[i]] + val[i]
            }
        }
    }
    return dp[W]
}

func main() {
    wt := []int{1, 3, 4, 5}
    val := []int{1, 4, 5, 7}
    fmt.Println("Max value:", knapsack01(wt, val, 7))    // 9
    fmt.Println("Max value:", knapsack01Opt(wt, val, 7)) // 9
}
```

**Rust:**
```rust
fn knapsack_01(wt: &[usize], val: &[i32], cap: usize) -> i32 {
    let n = wt.len();
    let mut dp = vec![vec![0i32; cap + 1]; n + 1];

    for i in 1..=n {
        for w in 0..=cap {
            dp[i][w] = dp[i-1][w]; // skip item i
            if w >= wt[i-1] {
                let take = dp[i-1][w - wt[i-1]] + val[i-1];
                if take > dp[i][w] {
                    dp[i][w] = take;
                }
            }
        }
    }
    dp[n][cap]
}

// Space Optimized
fn knapsack_01_opt(wt: &[usize], val: &[i32], cap: usize) -> i32 {
    let mut dp = vec![0i32; cap + 1];
    for i in 0..wt.len() {
        // RIGHT TO LEFT — essential for 0/1 knapsack!
        for w in (wt[i]..=cap).rev() {
            dp[w] = dp[w].max(dp[w - wt[i]] + val[i]);
        }
    }
    dp[cap]
}

fn main() {
    let wt  = vec![1, 3, 4, 5];
    let val = vec![1, 4, 5, 7];
    println!("Max value (2D): {}", knapsack_01(&wt, &val, 7));     // 9
    println!("Max value (1D): {}", knapsack_01_opt(&wt, &val, 7)); // 9
}
```

### THE KEY INSIGHT: Why Right→Left for 0/1 Knapsack

```
┌──────────────────────────────────────────────────────────┐
│  CRITICAL CONCEPT: The Direction of Iteration            │
│                                                          │
│  0/1 Knapsack (each item used ONCE):                     │
│    Iterate w: W → wt[i]  (RIGHT TO LEFT)                 │
│    Reason: dp[w - wt[i]] hasn't been updated yet         │
│             → uses OLD row (item not yet included)        │
│                                                          │
│  Unbounded Knapsack (item can repeat):                   │
│    Iterate w: wt[i] → W  (LEFT TO RIGHT)                 │
│    Reason: dp[w - wt[i]] IS already updated              │
│             → allows using same item again               │
└──────────────────────────────────────────────────────────┘

Example: item wt=2, val=3, capacity=4

RIGHT TO LEFT (0/1): dp starts [0,0,0,0,0]
  w=4: dp[4] = max(dp[4], dp[2]+3) = max(0, 0+3) = 3
  w=3: dp[3] = max(dp[3], dp[1]+3) = max(0, 0+3) = 3
  w=2: dp[2] = max(dp[2], dp[0]+3) = max(0, 0+3) = 3
  Result: [0,0,3,3,3] ← item used at most once ✓

LEFT TO RIGHT (unbounded): dp starts [0,0,0,0,0]
  w=2: dp[2] = max(dp[2], dp[0]+3) = 3
  w=3: dp[3] = max(dp[3], dp[1]+3) = 3
  w=4: dp[4] = max(dp[4], dp[2]+3) = max(0, 3+3) = 6
  Result: [0,0,3,3,6] ← item used TWICE at w=4 ✓
```

### 5b. Unbounded Knapsack

> Each item can be used unlimited times.

**C:**
```c
// Unbounded Knapsack - LEFT TO RIGHT (key difference!)
int unboundedKnapsack(int *wt, int *val, int n, int W) {
    int dp[W+1];
    memset(dp, 0, (W+1) * sizeof(int));

    for (int w = 0; w <= W; w++) {
        for (int i = 0; i < n; i++) {
            if (wt[i] <= w) {
                dp[w] = max(dp[w], dp[w - wt[i]] + val[i]);
            }
        }
    }
    return dp[W];
}
```

**Go:**
```go
func unboundedKnapsack(wt, val []int, W int) int {
    dp := make([]int, W+1)
    for w := 0; w <= W; w++ {
        for i := range wt {
            if wt[i] <= w && dp[w-wt[i]]+val[i] > dp[w] {
                dp[w] = dp[w-wt[i]] + val[i]
            }
        }
    }
    return dp[W]
}
```

**Rust:**
```rust
fn unbounded_knapsack(wt: &[usize], val: &[i32], cap: usize) -> i32 {
    let mut dp = vec![0i32; cap + 1];
    // LEFT TO RIGHT — allows reuse of same item
    for w in 0..=cap {
        for i in 0..wt.len() {
            if wt[i] <= w {
                dp[w] = dp[w].max(dp[w - wt[i]] + val[i]);
            }
        }
    }
    dp[cap]
}
```

### 5c. Subset Sum (Knapsack variant)

> Can we select a subset that sums exactly to target T?

```
State:      dp[i][s] = true if subset of first i items sums to s
Transition: dp[i][s] = dp[i-1][s]            ← skip item i
                    OR dp[i-1][s - arr[i]]   ← include item i
Base:       dp[i][0] = true (empty subset sums to 0)
Answer:     dp[n][T]
```

**Simulation: arr=[3,1,5,9,12], T=8**
```
Target T=8, items=[3,1,5,9,12]

     Capacity s →
     0    1    2    3    4    5    6    7    8
i=0 [T,   F,   F,   F,   F,   F,   F,   F,   F]
i=1 [T,   F,   F,   T,   F,   F,   F,   F,   F]  ← added 3
i=2 [T,   T,   F,   T,   T,   F,   F,   F,   F]  ← added 1
i=3 [T,   T,   F,   T,   T,   T,   T,   F,   T]  ← added 5
     ↑                                        ↑
    always true                         3+5=8=T ✓

Answer: dp[3][8] = True (subset {3,5} sums to 8)
```

**Go:**
```go
func subsetSum(arr []int, target int) bool {
    n := len(arr)
    dp := make([][]bool, n+1)
    for i := range dp {
        dp[i] = make([]bool, target+1)
        dp[i][0] = true // empty subset sums to 0
    }
    for i := 1; i <= n; i++ {
        for s := 0; s <= target; s++ {
            dp[i][s] = dp[i-1][s] // skip
            if s >= arr[i-1] {
                dp[i][s] = dp[i][s] || dp[i-1][s-arr[i-1]] // include
            }
        }
    }
    return dp[n][target]
}

// Space optimized (1D)
func subsetSumOpt(arr []int, target int) bool {
    dp := make([]bool, target+1)
    dp[0] = true
    for _, num := range arr {
        for s := target; s >= num; s-- { // RIGHT TO LEFT for 0/1
            dp[s] = dp[s] || dp[s-num]
        }
    }
    return dp[target]
}
```

**Rust:**
```rust
fn subset_sum(arr: &[usize], target: usize) -> bool {
    let mut dp = vec![false; target + 1];
    dp[0] = true;
    for &num in arr {
        for s in (num..=target).rev() { // right to left
            if dp[s - num] {
                dp[s] = true;
            }
        }
    }
    dp[target]
}
```

---

## 6. Template 3: Grid / 2D DP

### Concept

The state is a cell (i,j) in a 2D grid. `dp[i][j]` depends on cells above, left, or diagonally above.

```
Direction of filling:
  ┌───┬───┬───┬───┐
  │ ▓ │ ▓ │ ▓ │ ▓ │  ← row 0 filled first
  ├───┼───┼───┼───┤
  │ ▓ │ ▓ │ ▓ │ ▓ │  ← row 1 filled next
  ├───┼───┼───┼───┤
  │ ▓ │ ▓ │ ? │   │  ← dp[2][2] depends on dp[1][2] and dp[2][1]
  ├───┼───┼───┼───┤         ↑ from top        ← from left
  │   │   │   │   │
  └───┴───┴───┴───┘
       Fill: Top-Left → Bottom-Right
```

### Problem: Unique Paths

> Grid m×n. Start top-left, reach bottom-right. Only move right or down.

**5-Step Analysis:**
```
State:      dp[i][j] = number of unique paths to cell (i,j)
Transition: dp[i][j] = dp[i-1][j]   ← came from above
                     + dp[i][j-1]   ← came from left
Base:       dp[0][j] = 1 for all j  ← top row: only one way (keep going right)
            dp[i][0] = 1 for all i  ← left col: only one way (keep going down)
Answer:     dp[m-1][n-1]
```

**Simulation: 3×3 grid:**
```
     col: 0    1    2
row 0: [ 1,   1,   1  ]  ← top row: all 1s
row 1: [ 1,   2,   3  ]
row 2: [ 1,   3,   6  ]
                   ↑
               Answer = 6

Computation:
dp[1][1] = dp[0][1] + dp[1][0] = 1+1 = 2
dp[1][2] = dp[0][2] + dp[1][1] = 1+2 = 3
dp[2][1] = dp[1][1] + dp[2][0] = 2+1 = 3
dp[2][2] = dp[1][2] + dp[2][1] = 3+3 = 6
```

**C:**
```c
#include <stdio.h>
#include <string.h>

int uniquePaths(int m, int n) {
    int dp[m][n];
    // Initialize first row and column to 1
    for (int i = 0; i < m; i++) dp[i][0] = 1;
    for (int j = 0; j < n; j++) dp[0][j] = 1;

    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            dp[i][j] = dp[i-1][j] + dp[i][j-1];
        }
    }
    return dp[m-1][n-1];
}

int main() {
    printf("3x3 paths: %d\n", uniquePaths(3, 3)); // 6
    printf("3x7 paths: %d\n", uniquePaths(3, 7)); // 28
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

func uniquePaths(m, n int) int {
    dp := make([][]int, m)
    for i := range dp {
        dp[i] = make([]int, n)
        dp[i][0] = 1 // left column
    }
    for j := range dp[0] {
        dp[0][j] = 1 // top row
    }
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            dp[i][j] = dp[i-1][j] + dp[i][j-1]
        }
    }
    return dp[m-1][n-1]
}

func main() {
    fmt.Println("3x3:", uniquePaths(3, 3)) // 6
    fmt.Println("3x7:", uniquePaths(3, 7)) // 28
}
```

**Rust:**
```rust
fn unique_paths(m: usize, n: usize) -> usize {
    let mut dp = vec![vec![1usize; n]; m]; // Initialize all to 1
    for i in 1..m {
        for j in 1..n {
            dp[i][j] = dp[i-1][j] + dp[i][j-1];
        }
    }
    dp[m-1][n-1]
}

fn main() {
    println!("3x3: {}", unique_paths(3, 3)); // 6
    println!("3x7: {}", unique_paths(3, 7)); // 28
}
```

### Problem: Minimum Path Sum

> Grid with non-negative integers. Find path from top-left to bottom-right minimizing sum. Move only right or down.

**Simulation: grid = [[1,3,1],[1,5,1],[4,2,1]]**
```
Input grid:        dp table:
1  3  1            1   4   5
1  5  1            2   7   6
4  2  1            6   8   7
                             ↑ Answer = 7

dp[0][0] = grid[0][0] = 1
dp[0][1] = dp[0][0] + grid[0][1] = 1+3 = 4
dp[0][2] = dp[0][1] + grid[0][2] = 4+1 = 5
dp[1][0] = dp[0][0] + grid[1][0] = 1+1 = 2
dp[1][1] = min(dp[0][1], dp[1][0]) + grid[1][1]
         = min(4, 2) + 5 = 7
dp[1][2] = min(dp[0][2], dp[1][1]) + grid[1][2]
         = min(5, 7) + 1 = 6
dp[2][0] = dp[1][0] + grid[2][0] = 2+4 = 6
dp[2][1] = min(dp[1][1], dp[2][0]) + grid[2][1]
         = min(7, 6) + 2 = 8
dp[2][2] = min(dp[1][2], dp[2][1]) + grid[2][2]
         = min(6, 8) + 1 = 7
```

**Go:**
```go
func minPathSum(grid [][]int) int {
    m, n := len(grid), len(grid[0])
    dp := make([][]int, m)
    for i := range dp {
        dp[i] = make([]int, n)
    }
    dp[0][0] = grid[0][0]
    // First row
    for j := 1; j < n; j++ {
        dp[0][j] = dp[0][j-1] + grid[0][j]
    }
    // First column
    for i := 1; i < m; i++ {
        dp[i][0] = dp[i-1][0] + grid[i][0]
    }
    // Fill rest
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            if dp[i-1][j] < dp[i][j-1] {
                dp[i][j] = dp[i-1][j] + grid[i][j]
            } else {
                dp[i][j] = dp[i][j-1] + grid[i][j]
            }
        }
    }
    return dp[m-1][n-1]
}
```

**Rust:**
```rust
fn min_path_sum(grid: &Vec<Vec<i32>>) -> i32 {
    let (m, n) = (grid.len(), grid[0].len());
    let mut dp = vec![vec![i32::MAX; n]; m];
    dp[0][0] = grid[0][0];

    for j in 1..n { dp[0][j] = dp[0][j-1] + grid[0][j]; }
    for i in 1..m { dp[i][0] = dp[i-1][0] + grid[i][0]; }

    for i in 1..m {
        for j in 1..n {
            dp[i][j] = dp[i-1][j].min(dp[i][j-1]) + grid[i][j];
        }
    }
    dp[m-1][n-1]
}
```

**C:**
```c
#include <stdio.h>
#define INF 1e9

int minPathSum(int grid[][3], int m, int n) {
    int dp[m][n];
    dp[0][0] = grid[0][0];
    for (int j = 1; j < n; j++) dp[0][j] = dp[0][j-1] + grid[0][j];
    for (int i = 1; i < m; i++) dp[i][0] = dp[i-1][0] + grid[i][0];
    for (int i = 1; i < m; i++)
        for (int j = 1; j < n; j++) {
            int fromTop  = dp[i-1][j];
            int fromLeft = dp[i][j-1];
            dp[i][j] = (fromTop < fromLeft ? fromTop : fromLeft) + grid[i][j];
        }
    return dp[m-1][n-1];
}

int main() {
    int g[3][3] = {{1,3,1},{1,5,1},{4,2,1}};
    printf("Min path sum: %d\n", minPathSum(g, 3, 3)); // 7
    return 0;
}
```

---

## 7. Template 4: Interval DP

### Concept

Interval DP solves problems defined on **contiguous subarrays or substrings** (intervals). The key is solving smaller intervals first, then building up to larger ones.

```
KEY INSIGHT: To solve interval [i,j], we split it at some point k:
             [i,j] = [i,k] + [k+1,j]  OR  [i,k-1] + [k,j]

Traversal ORDER:
  ┌─────────────────────────────────────────┐
  │  Fill by increasing LENGTH (len=1,2,3...)│
  │  NOT by row/column order!               │
  └─────────────────────────────────────────┘

Visualization (n=4 intervals):
  i\j   0    1    2    3
   0  [base, L2,  L3,  L4 ]   ← dp[0][3] = answer for full array
   1  [ ×,  base, L2,  L3 ]
   2  [ ×,   ×,  base, L2 ]
   3  [ ×,   ×,   ×,  base]

Fill order: diagonals (length 1 → 2 → 3 → 4)
```

### Interval DP Algorithm Flow

```
FOR len = 2 to n:            ← interval length
  FOR i = 0 to n-len:        ← interval start
    j = i + len - 1          ← interval end
    FOR k = i to j-1:        ← split point
      dp[i][j] = optimize(dp[i][j], dp[i][k] + dp[k+1][j] + cost(i,j,k))
```

### Problem: Matrix Chain Multiplication

> Given matrices A1, A2, ..., An, find the order of multiplication that minimizes total scalar multiplications.

**Prerequisite — Matrix Multiplication Cost:**
```
Matrix A has dimensions p × q
Matrix B has dimensions q × r
A × B costs p * q * r multiplications
```

**5-Step Analysis:**
```
dims array: dimensions of matrices
  matrix i has dims[i-1] rows and dims[i] cols

State:      dp[i][j] = min cost to multiply matrices i..j
Transition: dp[i][j] = min over k from i to j-1 of:
              dp[i][k] + dp[k+1][j] + dims[i-1] * dims[k] * dims[j]
              (merge left group result with right group result)
Base:       dp[i][i] = 0 (single matrix — no multiplication needed)
Answer:     dp[1][n]
```

**Simulation: dims = [10, 30, 5, 60] → 3 matrices: (10×30), (30×5), (5×60)**
```
Matrices: M1=(10×30), M2=(30×5), M3=(5×60)
n=3, dims=[10,30,5,60]

Base: dp[1][1]=0, dp[2][2]=0, dp[3][3]=0

Length 2:
  dp[1][2]: split at k=1
    = dp[1][1] + dp[2][2] + dims[0]*dims[1]*dims[2]
    = 0 + 0 + 10*30*5 = 1500
    (M1×M2: 10×30×5 = 1500 ops)

  dp[2][3]: split at k=2
    = dp[2][2] + dp[3][3] + dims[1]*dims[2]*dims[3]
    = 0 + 0 + 30*5*60 = 9000
    (M2×M3: 30×5×60 = 9000 ops)

Length 3:
  dp[1][3]: try k=1 and k=2
    k=1: dp[1][1] + dp[2][3] + dims[0]*dims[1]*dims[3]
       = 0 + 9000 + 10*30*60 = 0+9000+18000 = 27000
       (M1*(M2*M3): first combine M2,M3 then with M1)

    k=2: dp[1][2] + dp[3][3] + dims[0]*dims[2]*dims[3]
       = 1500 + 0 + 10*5*60 = 1500+0+3000 = 4500
       (*(M1*M2)*M3: first combine M1,M2 then with M3)

    dp[1][3] = min(27000, 4500) = 4500

DP Table:
     1      2      3
1 [  0,  1500,  4500 ]
2 [  ×,     0,  9000 ]
3 [  ×,     ×,     0 ]

Answer = 4500 (optimal: (M1*M2)*M3)
```

**C:**
```c
#include <stdio.h>
#include <string.h>
#include <limits.h>

#define MAX_N 105

int dp[MAX_N][MAX_N];

int matrixChain(int *dims, int n) {
    // n = number of matrices, dims has n+1 elements
    memset(dp, 0, sizeof(dp));

    // len = chain length (number of matrices in group)
    for (int len = 2; len <= n; len++) {
        for (int i = 1; i <= n - len + 1; i++) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; k++) {
                int cost = dp[i][k] + dp[k+1][j]
                         + dims[i-1] * dims[k] * dims[j];
                if (cost < dp[i][j]) dp[i][j] = cost;
            }
        }
    }
    return dp[1][n];
}

int main() {
    int dims[] = {10, 30, 5, 60}; // 3 matrices
    printf("Min multiplications: %d\n", matrixChain(dims, 3)); // 4500
    return 0;
}
```

**Go:**
```go
package main

import (
    "fmt"
    "math"
)

func matrixChain(dims []int) int {
    n := len(dims) - 1 // number of matrices
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }

    for length := 2; length <= n; length++ {
        for i := 1; i <= n-length+1; i++ {
            j := i + length - 1
            dp[i][j] = math.MaxInt64
            for k := i; k < j; k++ {
                cost := dp[i][k] + dp[k+1][j] + dims[i-1]*dims[k]*dims[j]
                if cost < dp[i][j] {
                    dp[i][j] = cost
                }
            }
        }
    }
    return dp[1][n]
}

func main() {
    fmt.Println(matrixChain([]int{10, 30, 5, 60})) // 4500
    fmt.Println(matrixChain([]int{40, 20, 30, 10, 30})) // 26000
}
```

**Rust:**
```rust
fn matrix_chain(dims: &[usize]) -> usize {
    let n = dims.len() - 1;
    let mut dp = vec![vec![0usize; n + 1]; n + 1];

    for length in 2..=n {
        for i in 1..=(n - length + 1) {
            let j = i + length - 1;
            dp[i][j] = usize::MAX;
            for k in i..j {
                let cost = dp[i][k]
                    .saturating_add(dp[k+1][j])
                    .saturating_add(dims[i-1] * dims[k] * dims[j]);
                if cost < dp[i][j] {
                    dp[i][j] = cost;
                }
            }
        }
    }
    dp[1][n]
}

fn main() {
    println!("{}", matrix_chain(&[10, 30, 5, 60]));      // 4500
    println!("{}", matrix_chain(&[40, 20, 30, 10, 30])); // 26000
}
```

### Problem: Palindrome Partitioning (Min Cuts)

> Given a string, find minimum number of cuts to make every substring a palindrome.

**Simulation: s = "aab"**
```
Is palindrome table:
     0    1    2   (chars: a, a, b)
0  [ T,   T,   F ]   pal[0][0]=T (a)
1  [ ×,   T,   F ]   pal[0][1]=T (aa), pal[1][2]=F (ab)
2  [ ×,   ×,   T ]   pal[0][2]=F (aab)

dp[i] = min cuts for s[0..i]:
dp[-1] = -1 (empty string, helps with formula dp[i] = dp[k-1]+1)

dp[0]: s[0..0]="a" is palindrome → dp[0] = 0 (no cuts)
dp[1]: s[0..1]="aa" is palindrome → dp[1] = 0
       (also: dp[0]+1=1 but min is 0)
dp[2]: s[0..2]="aab" not palindrome
       k=2: s[2..2]="b" palindrome → dp[1]+1 = 1
       k=1: s[1..2]="ab" not palindrome → skip
       k=0: s[0..2]="aab" not palindrome → skip
       dp[2] = 1

Answer = dp[2] = 1  (cut: "aa|b")
```

**Go:**
```go
func minCut(s string) int {
    n := len(s)
    // Build palindrome table
    pal := make([][]bool, n)
    for i := range pal {
        pal[i] = make([]bool, n)
        pal[i][i] = true // single char
    }
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            if s[i] == s[j] {
                if length == 2 {
                    pal[i][j] = true
                } else {
                    pal[i][j] = pal[i+1][j-1]
                }
            }
        }
    }

    // dp[i] = min cuts for s[0..i]
    dp := make([]int, n)
    for i := range dp {
        dp[i] = i // worst case: cut every character
    }
    for i := 1; i < n; i++ {
        if pal[0][i] { // whole prefix is palindrome
            dp[i] = 0
            continue
        }
        for k := 1; k <= i; k++ {
            if pal[k][i] {
                val := dp[k-1] + 1
                if val < dp[i] {
                    dp[i] = val
                }
            }
        }
    }
    return dp[n-1]
}
```

**Rust:**
```rust
fn min_cut(s: &str) -> usize {
    let n = s.len();
    let chars: Vec<char> = s.chars().collect();

    // palindrome[i][j] = true if s[i..=j] is palindrome
    let mut pal = vec![vec![false; n]; n];
    for i in 0..n { pal[i][i] = true; }
    for length in 2..=n {
        for i in 0..=(n - length) {
            let j = i + length - 1;
            if chars[i] == chars[j] {
                pal[i][j] = if length == 2 { true } else { pal[i+1][j-1] };
            }
        }
    }

    let mut dp = vec![usize::MAX; n];
    for i in 0..n {
        if pal[0][i] { dp[i] = 0; continue; }
        for k in 1..=i {
            if pal[k][i] && dp[k-1] != usize::MAX {
                dp[i] = dp[i].min(dp[k-1] + 1);
            }
        }
    }
    dp[n-1]
}
```

---

## 8. Template 5: Sequence DP

### The Three Classic Sequence Problems

```
┌──────────────────────────────────────────────────────────────┐
│  1. LCS  — Longest Common Subsequence                        │
│     "What's the longest shared subsequence between 2 strings?"│
│                                                              │
│  2. LIS  — Longest Increasing Subsequence                    │
│     "What's the longest subsequence of strictly increasing   │
│      numbers?"                                               │
│                                                              │
│  3. Edit Distance — Levenshtein Distance                     │
│     "How many single-char operations to transform s1 → s2?" │
└──────────────────────────────────────────────────────────────┘
```

### 8a. Longest Common Subsequence (LCS)

**Prerequisite — What is a Subsequence?**
```
String "ABCDE": subsequences include "ACE", "BD", "ABCDE", ""
(elements in order, NOT necessarily contiguous — unlike substring)

"ABCDE"  vs  "ACE":
 A B C D E
 ↑   ↑   ↑     pick positions 0, 2, 4 → subsequence
```

**5-Step Analysis:**
```
State:      dp[i][j] = length of LCS of s1[0..i-1] and s2[0..j-1]
Transition: if s1[i-1] == s2[j-1]:
              dp[i][j] = dp[i-1][j-1] + 1   ← characters match!
            else:
              dp[i][j] = max(dp[i-1][j],     ← skip s1[i-1]
                             dp[i][j-1])     ← skip s2[j-1]
Base:       dp[0][j] = 0, dp[i][0] = 0
Answer:     dp[m][n]
```

**Simulation: s1="ABCBDAB", s2="BDCAB"**
```
     ""   B    D    C    A    B
""  [ 0,  0,   0,   0,   0,   0 ]
A   [ 0,  0,   0,   0,   1,   1 ]
B   [ 0,  1,   1,   1,   1,   2 ]
C   [ 0,  1,   1,   2,   2,   2 ]
B   [ 0,  1,   1,   2,   2,   3 ]
D   [ 0,  1,   2,   2,   2,   3 ]
A   [ 0,  1,   2,   2,   3,   3 ]
B   [ 0,  1,   2,   2,   3,   4 ]
                              ↑
                     LCS length = 4

Trace LCS:
dp[7][5]=4 ← s1[6]='B'==s2[4]='B' → match, go to dp[6][4]
dp[6][4]=3 ← s1[5]='A'==s2[3]='A' → match, go to dp[5][3]
dp[5][3]=2 ← s1[4]='D'!=s2[2]='C' → go to max direction (dp[4][3])
dp[4][3]=2 ← s1[3]='B'!=s2[2]='C' → go to max direction (dp[3][3])
dp[3][3]=2 ← s1[2]='C'==s2[2]='C' → match, go to dp[2][2]
dp[2][2]=1 ← s1[1]='B'==s2[1]='B'? No! s2[1]='D', go to max (dp[1][2])
dp[1][2]=0 ← done

LCS = "BCAB" or "BDAB" (length 4)
```

**C:**
```c
#include <stdio.h>
#include <string.h>

#define MAX 1005

int dp[MAX][MAX];

int lcs(char *s1, char *s2) {
    int m = strlen(s1), n = strlen(s2);
    memset(dp, 0, sizeof(dp));

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i-1] == s2[j-1]) {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = dp[i-1][j] > dp[i][j-1]
                           ? dp[i-1][j] : dp[i][j-1];
            }
        }
    }
    return dp[m][n];
}

int main() {
    char s1[] = "ABCBDAB";
    char s2[] = "BDCAB";
    printf("LCS length: %d\n", lcs(s1, s2)); // 4
    return 0;
}
```

**Go:**
```go
package main

import "fmt"

func lcs(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else if dp[i-1][j] > dp[i][j-1] {
                dp[i][j] = dp[i-1][j]
            } else {
                dp[i][j] = dp[i][j-1]
            }
        }
    }
    return dp[m][n]
}

func main() {
    fmt.Println("LCS:", lcs("ABCBDAB", "BDCAB")) // 4
    fmt.Println("LCS:", lcs("AGGTAB", "GXTXAYB")) // 4
}
```

**Rust:**
```rust
fn lcs(s1: &str, s2: &str) -> usize {
    let (s1, s2): (Vec<char>, Vec<char>) = (s1.chars().collect(), s2.chars().collect());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];

    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if s1[i-1] == s2[j-1] {
                dp[i-1][j-1] + 1
            } else {
                dp[i-1][j].max(dp[i][j-1])
            };
        }
    }
    dp[m][n]
}

fn main() {
    println!("LCS: {}", lcs("ABCBDAB", "BDCAB"));  // 4
    println!("LCS: {}", lcs("AGGTAB", "GXTXAYB")); // 4
}
```

### 8b. Longest Increasing Subsequence (LIS)

**Prerequisite — What is an Increasing Subsequence?**
```
Array: [10, 9, 2, 5, 3, 7, 101, 18]
LIS:   [2,  3, 7, 101]  or  [2, 3, 7, 18]  → length 4
```

**5-Step Analysis (O(n²) DP):**
```
State:      dp[i] = length of LIS ending at index i
Transition: dp[i] = 1 + max(dp[j]) for all j < i where arr[j] < arr[i]
            (extend the best increasing subsequence ending before i)
Base:       dp[i] = 1 (each element is a subsequence of length 1)
Answer:     max(dp[0..n-1])
```

**Simulation: arr = [10, 9, 2, 5, 3, 7, 101, 18]**
```
Index:   0    1    2    3    4    5    6     7
arr:    [10,  9,   2,   5,   3,   7,  101,  18]
dp:     [ 1,  1,   1,   ?,   ?,   ?,    ?,   ?]

dp[3]=5: arr[3]=5
  j=0: arr[0]=10 > 5, skip
  j=1: arr[1]=9  > 5, skip
  j=2: arr[2]=2  < 5 ✓ → dp[3] = max(1, dp[2]+1) = max(1,2) = 2
  dp[3] = 2  (subsequence: [2,5])

dp[4]=3: arr[4]=3
  j=0: 10>3, skip
  j=1: 9>3, skip
  j=2: arr[2]=2 < 3 ✓ → dp[4] = max(1, dp[2]+1) = 2
  j=3: arr[3]=5 > 3, skip
  dp[4] = 2  (subsequence: [2,3])

dp[5]=7: arr[5]=7
  j=2: 2<7 → dp[5] = max(1, dp[2]+1)=2
  j=3: 5<7 → dp[5] = max(2, dp[3]+1)=3
  j=4: 3<7 → dp[5] = max(3, dp[4]+1)=3
  dp[5] = 3  (subsequence: [2,5,7] or [2,3,7])

dp[6]=101: all < 101
  dp[6] = max across all j + 1 = dp[5]+1 = 4  ([2,5,7,101])

dp[7]=18: 
  j=5: 7<18 → dp[7] = max(1, dp[5]+1) = 4
  j=6: 101>18, skip
  dp[7] = 4  ([2,5,7,18])

Final dp: [1, 1, 1, 2, 2, 3, 4, 4]
Answer = max(dp) = 4
```

**C:**
```c
#include <stdio.h>

int lis(int *arr, int n) {
    int dp[n];
    for (int i = 0; i < n; i++) dp[i] = 1;

    int maxLen = 1;
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (arr[j] < arr[i] && dp[j] + 1 > dp[i]) {
                dp[i] = dp[j] + 1;
            }
        }
        if (dp[i] > maxLen) maxLen = dp[i];
    }
    return maxLen;
}

int main() {
    int arr[] = {10, 9, 2, 5, 3, 7, 101, 18};
    printf("LIS length: %d\n", lis(arr, 8)); // 4
    return 0;
}
```

**Go:**
```go
func lisNSquared(nums []int) int {
    n := len(nums)
    dp := make([]int, n)
    for i := range dp { dp[i] = 1 }
    maxLen := 1
    for i := 1; i < n; i++ {
        for j := 0; j < i; j++ {
            if nums[j] < nums[i] && dp[j]+1 > dp[i] {
                dp[i] = dp[j] + 1
            }
        }
        if dp[i] > maxLen { maxLen = dp[i] }
    }
    return maxLen
}
```

**Rust:**
```rust
fn lis_n_squared(nums: &[i32]) -> usize {
    let n = nums.len();
    let mut dp = vec![1usize; n];
    let mut max_len = 1;
    for i in 1..n {
        for j in 0..i {
            if nums[j] < nums[i] {
                dp[i] = dp[i].max(dp[j] + 1);
            }
        }
        max_len = max_len.max(dp[i]);
    }
    max_len
}
```

### LIS O(n log n) — Patience Sort Method

> **Concept**: Maintain a `tails` array where `tails[i]` is the smallest tail element of all increasing subsequences of length `i+1`.

```
Array: [10, 9, 2, 5, 3, 7, 101, 18]

tails starts empty. Process each element:

10  → tails=[]      → append → tails=[10]
9   → 9<10 (pos 0)  → replace → tails=[9]
2   → 2<9  (pos 0)  → replace → tails=[2]
5   → 5>2  (pos 1)  → append  → tails=[2,5]
3   → 3<5  (pos 1)  → replace → tails=[2,3]
7   → 7>3  (pos 2)  → append  → tails=[2,3,7]
101 → 101>7 (pos 3) → append  → tails=[2,3,7,101]
18  → 18<101 (pos 3)→ replace → tails=[2,3,7,18]

LIS length = len(tails) = 4
```

**Go (O(n log n) LIS):**
```go
import "sort"

func lisNLogN(nums []int) int {
    tails := []int{}
    for _, num := range nums {
        // Binary search for first tail >= num
        pos := sort.SearchInts(tails, num)
        if pos == len(tails) {
            tails = append(tails, num) // extend
        } else {
            tails[pos] = num // replace
        }
    }
    return len(tails)
}
```

**Rust (O(n log n) LIS):**
```rust
fn lis_n_log_n(nums: &[i32]) -> usize {
    let mut tails: Vec<i32> = Vec::new();
    for &num in nums {
        // Binary search for first position where tails[pos] >= num
        let pos = tails.partition_point(|&x| x < num);
        if pos == tails.len() {
            tails.push(num);
        } else {
            tails[pos] = num;
        }
    }
    tails.len()
}
```

**C (O(n log n) LIS with binary search):**
```c
#include <stdio.h>

// Binary search: find index of first element >= target in arr[0..len-1]
int lower_bound(int *arr, int len, int target) {
    int lo = 0, hi = len;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}

int lisOptimal(int *nums, int n) {
    int tails[n];
    int len = 0;
    for (int i = 0; i < n; i++) {
        int pos = lower_bound(tails, len, nums[i]);
        tails[pos] = nums[i];
        if (pos == len) len++;
    }
    return len;
}

int main() {
    int arr[] = {10, 9, 2, 5, 3, 7, 101, 18};
    printf("LIS (O(nlogn)): %d\n", lisOptimal(arr, 8)); // 4
    return 0;
}
```

### 8c. Edit Distance (Levenshtein Distance)

> Minimum operations (insert, delete, replace) to transform word1 into word2.

**5-Step Analysis:**
```
State:      dp[i][j] = min operations to transform word1[0..i-1] to word2[0..j-1]
Transition: if word1[i-1] == word2[j-1]:
              dp[i][j] = dp[i-1][j-1]          ← characters match, no op needed
            else:
              dp[i][j] = 1 + min(
                dp[i-1][j],     ← delete word1[i-1]
                dp[i][j-1],     ← insert word2[j-1]
                dp[i-1][j-1]    ← replace word1[i-1] with word2[j-1]
              )
Base:       dp[0][j] = j (insert j characters)
            dp[i][0] = i (delete i characters)
Answer:     dp[m][n]
```

**Simulation: word1="horse", word2="ros"**
```
     ""   r    o    s
""  [ 0,  1,   2,   3 ]
h   [ 1,  1,   2,   3 ]
o   [ 2,  2,   1,   2 ]
r   [ 3,  2,   2,   2 ]
s   [ 4,  3,   3,   2 ]
e   [ 5,  4,   4,   3 ]
                    ↑
              Answer = 3

Operations: horse → rorse (replace h→r)
                  → rose  (delete r)
                  → ros   (delete e)
```

**C:**
```c
#include <stdio.h>
#include <string.h>

int min3(int a, int b, int c) {
    int m = a < b ? a : b;
    return m < c ? m : c;
}

int editDistance(char *w1, char *w2) {
    int m = strlen(w1), n = strlen(w2);
    int dp[m+1][n+1];

    for (int i = 0; i <= m; i++) dp[i][0] = i;
    for (int j = 0; j <= n; j++) dp[0][j] = j;

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (w1[i-1] == w2[j-1]) {
                dp[i][j] = dp[i-1][j-1];
            } else {
                dp[i][j] = 1 + min3(dp[i-1][j],    // delete
                                    dp[i][j-1],     // insert
                                    dp[i-1][j-1]);  // replace
            }
        }
    }
    return dp[m][n];
}

int main() {
    printf("horse→ros: %d\n", editDistance("horse", "ros"));      // 3
    printf("intention→execution: %d\n", editDistance("intention", "execution")); // 5
    return 0;
}
```

**Go:**
```go
func editDistance(word1, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        dp[i][0] = i
    }
    for j := 0; j <= n; j++ { dp[0][j] = j }

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1]
            } else {
                del := dp[i-1][j] + 1
                ins := dp[i][j-1] + 1
                rep := dp[i-1][j-1] + 1
                dp[i][j] = del
                if ins < dp[i][j] { dp[i][j] = ins }
                if rep < dp[i][j] { dp[i][j] = rep }
            }
        }
    }
    return dp[m][n]
}
```

**Rust:**
```rust
fn edit_distance(word1: &str, word2: &str) -> usize {
    let (w1, w2): (Vec<char>, Vec<char>) = (word1.chars().collect(), word2.chars().collect());
    let (m, n) = (w1.len(), w2.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];

    for i in 0..=m { dp[i][0] = i; }
    for j in 0..=n { dp[0][j] = j; }

    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if w1[i-1] == w2[j-1] {
                dp[i-1][j-1]
            } else {
                1 + dp[i-1][j].min(dp[i][j-1]).min(dp[i-1][j-1])
            };
        }
    }
    dp[m][n]
}

fn main() {
    println!("{}", edit_distance("horse", "ros"));      // 3
    println!("{}", edit_distance("intention", "execution")); // 5
}
```

---

## 9. Template 6: State Machine DP

### Concept

State Machine DP models problems where you're in one of several **states** and transition between them. Classic use: stock trading problems, patterns with rules.

```
GENERAL FORM:
  States: S0, S1, S2, ...
  Each day/element, you're in one state
  Transitions have costs/gains

State Diagram Example (Stock: buy/sell/cooldown):
  ┌─────────┐  buy   ┌──────────┐  sell  ┌──────────┐
  │  EMPTY  │──────►│  HOLDING │───────►│ COOLDOWN │
  │(no stock│◄──────│ (has stk)│        │(just sold│
  └─────────┘  sell └──────────┘        └──────────┘
       ▲                                      │
       └──────────────────────────────────────┘
                    cooldown ends
```

### Problem: Best Time to Buy and Sell Stock (with Cooldown)

> After selling, must wait 1 day (cooldown). Maximize profit.

**5-Step Analysis:**
```
States:
  held[i]   = max profit on day i if you HOLD a stock
  sold[i]   = max profit on day i if you JUST SOLD (now in cooldown)
  rest[i]   = max profit on day i if in REST state (no stock, no cooldown)

Transition:
  held[i] = max(held[i-1],       ← hold from yesterday
                rest[i-1]-price) ← buy today (must come from rest, not cooldown!)

  sold[i] = held[i-1] + price    ← sell today

  rest[i] = max(rest[i-1],       ← keep resting
                sold[i-1])       ← cooldown over

Base: held[0] = -price[0], sold[0] = -INF, rest[0] = 0
Answer: max(sold[n-1], rest[n-1])
```

**Simulation: prices = [1, 2, 3, 0, 2]**
```
Day:     0     1     2     3     4
price:  [1,    2,    3,    0,    2]

Day 0:
  held[0] = -1   (buy at price 1)
  sold[0] = -INF (can't sell on day 0 without buying)
  rest[0] = 0    (do nothing)

Day 1 (price=2):
  held[1] = max(held[0], rest[0]-2)  = max(-1, 0-2)   = max(-1,-2) = -1
  sold[1] = held[0]+2                = -1+2            = 1
  rest[1] = max(rest[0], sold[0])    = max(0,-INF)     = 0

Day 2 (price=3):
  held[2] = max(held[1], rest[1]-3)  = max(-1, 0-3)   = -1
  sold[2] = held[1]+3                = -1+3            = 2
  rest[2] = max(rest[1], sold[1])    = max(0, 1)       = 1

Day 3 (price=0):
  held[3] = max(held[2], rest[2]-0)  = max(-1, 1-0)   = max(-1,1) = 1
  sold[3] = held[2]+0                = -1+0            = -1
  rest[3] = max(rest[2], sold[2])    = max(1, 2)       = 2

Day 4 (price=2):
  held[4] = max(held[3], rest[3]-2)  = max(1, 2-2)    = max(1,0) = 1
  sold[4] = held[3]+2                = 1+2             = 3
  rest[4] = max(rest[3], sold[3])    = max(2, -1)      = 2

Answer = max(sold[4], rest[4]) = max(3, 2) = 3
(Strategy: buy day0@1, sell day1@2, cooldown day2, buy day3@0, sell day4@2)
```

**Go:**
```go
import "math"

func maxProfitCooldown(prices []int) int {
    n := len(prices)
    if n <= 1 { return 0 }

    held := make([]int, n)
    sold := make([]int, n)
    rest := make([]int, n)

    held[0] = -prices[0]
    sold[0] = math.MinInt64 / 2
    rest[0] = 0

    for i := 1; i < n; i++ {
        held[i] = max2(held[i-1], rest[i-1]-prices[i])
        sold[i] = held[i-1] + prices[i]
        rest[i] = max2(rest[i-1], sold[i-1])
    }
    return max2(sold[n-1], rest[n-1])
}

func max2(a, b int) int {
    if a > b { return a }
    return b
}
```

**Rust:**
```rust
fn max_profit_cooldown(prices: &[i32]) -> i32 {
    let n = prices.len();
    if n <= 1 { return 0; }

    let (mut held, mut sold, mut rest) = (-prices[0], i32::MIN / 2, 0);

    for i in 1..n {
        let new_held = held.max(rest - prices[i]);
        let new_sold = held + prices[i];
        let new_rest = rest.max(sold);
        held = new_held;
        sold = new_sold;
        rest = new_rest;
    }
    sold.max(rest)
}

fn main() {
    println!("{}", max_profit_cooldown(&[1, 2, 3, 0, 2])); // 3
    println!("{}", max_profit_cooldown(&[1]));              // 0
}
```

**C:**
```c
#include <stdio.h>
#include <limits.h>

int maxProfitCooldown(int *prices, int n) {
    if (n <= 1) return 0;

    int held = -prices[0];
    int sold = INT_MIN / 2;
    int rest = 0;

    for (int i = 1; i < n; i++) {
        int new_held = held > (rest - prices[i]) ? held : (rest - prices[i]);
        int new_sold = held + prices[i];
        int new_rest = rest > sold ? rest : sold;
        held = new_held;
        sold = new_sold;
        rest = new_rest;
    }
    return sold > rest ? sold : rest;
}

int main() {
    int p[] = {1, 2, 3, 0, 2};
    printf("Max profit: %d\n", maxProfitCooldown(p, 5)); // 3
    return 0;
}
```

---

## 10. Template 7: Tree DP

### Concept

Tree DP computes DP values on a tree (rooted or unrooted). Each node's value depends on its **children's** values.

```
GENERAL PATTERN:
  1. Root the tree (choose any node as root)
  2. DFS from root
  3. Compute dp[node] from dp[children]
  4. Post-order traversal (children before parent)

Tree structure:
         1
        / \
       2   3
      / \
     4   5

Post-order: 4 → 5 → 2 → 3 → 1
            ↑ children computed before parent
```

### Problem: House Robber III (Tree Version)

> Rob houses on a binary tree. Cannot rob two directly connected nodes. Maximize money.

**5-Step Analysis:**
```
State:      For each node, compute TWO values:
            dp[node][0] = max money if we DON'T rob this node
            dp[node][1] = max money if we DO rob this node

Transition:
  If we DON'T rob node:
    dp[node][0] = sum of max(dp[child][0], dp[child][1]) for each child
                  (each child can be robbed or not)

  If we DO rob node:
    dp[node][1] = node.val + sum of dp[child][0] for each child
                  (children CANNOT be robbed)

Base: leaf node
  dp[leaf][0] = 0
  dp[leaf][1] = leaf.val

Answer: max(dp[root][0], dp[root][1])
```

**Simulation:**
```
Tree:         3
             / \
            2   3
             \   \
              3   1

Post-order DFS:

Node 3 (leaf, left child of 2):
  not_rob=0, rob=3 → return (0,3)

Node 2:
  left child returned (0, 3)
  right child = nil → (0, 0)
  not_rob = max(0,3) + max(0,0) = 3 + 0 = 3
  rob     = 2 + 0 + 0 = 2           (children not robbed)
  return (3, 2)

Node 1 (leaf, right child of right 3):
  not_rob=0, rob=1 → return (0,1)

Right Node 3:
  right child returned (0, 1)
  not_rob = max(0,1) = 1
  rob     = 3 + 0 = 3
  return (1, 3)

Root Node 3:
  left child returned (3, 2)
  right child returned (1, 3)
  not_rob = max(3,2) + max(1,3) = 3+3 = 6
  rob     = 3 + 3 + 1 = 7
  return (6, 7)

Answer = max(6, 7) = 7
```

**Go:**
```go
type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// Returns (notRob, rob) pair for each subtree
func robTree(node *TreeNode) (int, int) {
    if node == nil {
        return 0, 0
    }
    leftNot, leftRob   := robTree(node.Left)
    rightNot, rightRob := robTree(node.Right)

    // Don't rob this node: children can be robbed or not
    notRob := max2(leftNot, leftRob) + max2(rightNot, rightRob)
    // Rob this node: children CANNOT be robbed
    rob := node.Val + leftNot + rightNot

    return notRob, rob
}

func rob3(root *TreeNode) int {
    notRob, rob := robTree(root)
    return max2(notRob, rob)
}
```

**Rust:**
```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Rc<RefCell<TreeNode>>>,
    right: Option<Rc<RefCell<TreeNode>>>,
}

fn rob_tree(node: &Option<Rc<RefCell<TreeNode>>>) -> (i32, i32) {
    match node {
        None => (0, 0),
        Some(n) => {
            let n = n.borrow();
            let (left_not, left_rob)   = rob_tree(&n.left);
            let (right_not, right_rob) = rob_tree(&n.right);

            let not_rob = left_not.max(left_rob) + right_not.max(right_rob);
            let rob     = n.val + left_not + right_not;
            (not_rob, rob)
        }
    }
}

fn rob3(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    let (not_rob, rob) = rob_tree(&root);
    not_rob.max(rob)
}
```

**C:**
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

typedef struct { int notRob, rob; } Pair;

Pair robTree(TreeNode *node) {
    if (!node) return (Pair){0, 0};

    Pair left  = robTree(node->left);
    Pair right = robTree(node->right);

    int notRob = (left.notRob > left.rob ? left.notRob : left.rob)
               + (right.notRob > right.rob ? right.notRob : right.rob);
    int rob = node->val + left.notRob + right.notRob;

    return (Pair){notRob, rob};
}

int rob3(TreeNode *root) {
    Pair p = robTree(root);
    return p.notRob > p.rob ? p.notRob : p.rob;
}
```

---

## 11. Template 8: Bitmask DP

### Prerequisite — What is a Bitmask?

A **bitmask** is an integer used as a set of binary flags. If you have `n` elements, a bitmask of `n` bits can represent **which subset of those elements have been "visited" or "chosen"**.

```
Example with 4 cities (indices 0,1,2,3):

Bitmask = 0101 (binary) = 5 (decimal)
          ↑↑↑↑
          3210  ← city index

bit 0 = 1 → city 0 is visited
bit 1 = 0 → city 1 is NOT visited
bit 2 = 1 → city 2 is visited
bit 3 = 0 → city 3 is NOT visited

BITMASK OPERATIONS:
  Check if city i visited:   mask & (1 << i)
  Mark city i as visited:    mask | (1 << i)
  Unmark city i:             mask & ~(1 << i)
  Check all n visited:       mask == (1<<n) - 1
  Count set bits:            __builtin_popcount(mask)  [C]

For n=4: all cities visited = 1111 = 15 = (1<<4)-1
```

### Concept

Bitmask DP is used for problems involving **subsets** of a small set (typically n ≤ 20). The state includes the bitmask representing which elements are "used".

### Problem: Travelling Salesman Problem (TSP)

> Visit all n cities exactly once and return to start. Minimize total distance.

**5-Step Analysis:**
```
State:      dp[mask][i] = min distance to reach city i
                          having visited exactly the cities in mask

Transition: dp[mask | (1<<j)][j] = min(dp[mask][j],
                                       dp[mask][i] + dist[i][j])
            (from city i, go to unvisited city j)

Base:       dp[1][0] = 0  (start at city 0, only city 0 visited)
            dp[mask][i] = INF otherwise

Answer:     min over all i of dp[(1<<n)-1][i] + dist[i][0]
            (visit all cities, return to start)
```

**Simulation: n=4 cities, distance matrix:**
```
dist:
     0    1    2    3
0  [ 0,  10,  15,  20 ]
1  [10,   0,  35,  25 ]
2  [15,  35,   0,  30 ]
3  [20,  25,  30,   0 ]

All cities visited mask = 1111 = 15

Starting at city 0 (bit 0 set): mask=0001=1
dp[0001][0] = 0

From city 0 to city 1: mask becomes 0011=3
dp[0011][1] = dp[0001][0] + dist[0][1] = 0+10 = 10

From city 0 to city 2: mask becomes 0101=5
dp[0101][2] = 0+15 = 15

From city 0 to city 3: mask becomes 1001=9
dp[1001][3] = 0+20 = 20

... (continue for all reachable states) ...

Final: For mask=1111=15:
dp[15][1] = min path ending at 1, all visited
dp[15][2] = min path ending at 2, all visited
dp[15][3] = min path ending at 3, all visited

Answer = min(dp[15][i] + dist[i][0]) for i in 1..n-1
       = 80  (path: 0→1→3→2→0 = 10+25+30+15=80)
```

**C:**
```c
#include <stdio.h>
#include <string.h>
#include <limits.h>

#define MAX_N 20

int dp[1 << MAX_N][MAX_N];
int dist[MAX_N][MAX_N];

int tsp(int n) {
    int FULL = (1 << n) - 1;

    // Initialize all to INF
    for (int mask = 0; mask <= FULL; mask++)
        for (int i = 0; i < n; i++)
            dp[mask][i] = INT_MAX / 2;

    dp[1][0] = 0; // start at city 0, only city 0 visited

    for (int mask = 1; mask <= FULL; mask++) {
        for (int i = 0; i < n; i++) {
            if (!(mask & (1 << i))) continue; // i not in mask, skip
            if (dp[mask][i] == INT_MAX/2) continue;

            // Try visiting each unvisited city j
            for (int j = 0; j < n; j++) {
                if (mask & (1 << j)) continue; // j already visited
                int newMask = mask | (1 << j);
                int newCost = dp[mask][i] + dist[i][j];
                if (newCost < dp[newMask][j])
                    dp[newMask][j] = newCost;
            }
        }
    }

    int ans = INT_MAX;
    for (int i = 1; i < n; i++) {
        if (dp[FULL][i] + dist[i][0] < ans)
            ans = dp[FULL][i] + dist[i][0];
    }
    return ans;
}

int main() {
    int n = 4;
    int d[4][4] = {{0,10,15,20},{10,0,35,25},{15,35,0,30},{20,25,30,0}};
    for (int i=0;i<n;i++) for(int j=0;j<n;j++) dist[i][j]=d[i][j];
    printf("TSP min cost: %d\n", tsp(n)); // 80
    return 0;
}
```

**Go:**
```go
import "math"

func tsp(dist [][]int) int {
    n := len(dist)
    FULL := (1 << n) - 1

    // dp[mask][i] = min cost to have visited cities in mask, ending at i
    dp := make([][]int, FULL+1)
    for i := range dp {
        dp[i] = make([]int, n)
        for j := range dp[i] { dp[i][j] = math.MaxInt64 / 2 }
    }
    dp[1][0] = 0 // start at city 0

    for mask := 1; mask <= FULL; mask++ {
        for i := 0; i < n; i++ {
            if mask&(1<<i) == 0 || dp[mask][i] == math.MaxInt64/2 { continue }
            for j := 0; j < n; j++ {
                if mask&(1<<j) != 0 { continue } // already visited
                newMask := mask | (1 << j)
                cost := dp[mask][i] + dist[i][j]
                if cost < dp[newMask][j] {
                    dp[newMask][j] = cost
                }
            }
        }
    }

    ans := math.MaxInt64
    for i := 1; i < n; i++ {
        total := dp[FULL][i] + dist[i][0]
        if total < ans { ans = total }
    }
    return ans
}

func main() {
    dist := [][]int{
        {0, 10, 15, 20},
        {10, 0, 35, 25},
        {15, 35, 0, 30},
        {20, 25, 30, 0},
    }
    fmt.Println("TSP:", tsp(dist)) // 80
}
```

**Rust:**
```rust
fn tsp(dist: &Vec<Vec<i32>>) -> i32 {
    let n = dist.len();
    let full = (1usize << n) - 1;
    let inf = i32::MAX / 2;

    let mut dp = vec![vec![inf; n]; full + 1];
    dp[1][0] = 0;

    for mask in 1..=full {
        for i in 0..n {
            if mask & (1 << i) == 0 || dp[mask][i] == inf { continue; }
            for j in 0..n {
                if mask & (1 << j) != 0 { continue; }
                let new_mask = mask | (1 << j);
                let cost = dp[mask][i] + dist[i][j];
                if cost < dp[new_mask][j] {
                    dp[new_mask][j] = cost;
                }
            }
        }
    }

    (1..n).map(|i| dp[full][i] + dist[i][0]).min().unwrap_or(inf)
}

fn main() {
    let dist = vec![
        vec![0, 10, 15, 20],
        vec![10, 0, 35, 25],
        vec![15, 35, 0, 30],
        vec![20, 25, 30, 0],
    ];
    println!("TSP: {}", tsp(&dist)); // 80
}
```

---

## 12. Template 9: Digit DP

### Concept

Digit DP counts numbers in a range `[0, N]` that satisfy some digit-based property (sum of digits, digit count, no repeated digits, etc.).

**Key Ideas:**
```
┌────────────────────────────────────────────────────────────┐
│  DIGIT DP STATES:                                          │
│                                                            │
│  pos   = current digit position (left to right)           │
│  tight = are we still bounded by N's digits?               │
│          (true = can only use digits ≤ N[pos])            │
│          (false = can use any digit 0-9)                   │
│  [extra state based on problem: sum, count, etc.]          │
│                                                            │
│  TIGHT CONSTRAINT:                                         │
│  N = 3 2 5                                                 │
│  pos=0: tight=true → can use 0,1,2,3 (not 4-9)            │
│    chose 3: tight STAYS true                               │
│    chose 2: tight becomes FALSE (already less than N)      │
│             → remaining positions: any digit 0-9           │
└────────────────────────────────────────────────────────────┘
```

### Problem: Count Numbers with Sum of Digits = S in [0, N]

**Decision Flow:**
```
At each position pos with tight=true/false:
  FOR each digit d from 0 to (tight ? N[pos] : 9):
    new_tight = tight AND (d == N[pos])
    recurse(pos+1, sum+d, new_tight)

At pos == n (processed all digits):
  if sum == S: return 1
  else:        return 0

Memoize: memo[pos][sum][tight]
```

**Go:**
```go
package main

import "fmt"

var (
    digits []int
    memo   [15][200][2]int
)

func digitDP(pos, sum, tight int) int {
    if pos == len(digits) {
        if sum == 0 { return 1 }
        return 0
    }
    if memo[pos][sum][tight] != -1 {
        return memo[pos][sum][tight]
    }

    limit := 9
    if tight == 1 { limit = digits[pos] }

    result := 0
    for d := 0; d <= limit; d++ {
        if sum-d < 0 { break }
        newTight := 0
        if tight == 1 && d == limit { newTight = 1 }
        result += digitDP(pos+1, sum-d, newTight)
    }

    memo[pos][sum][tight] = result
    return result
}

// Count numbers in [0, N] with digit sum = S
func countDigitSum(N, S int) int {
    digits = []int{}
    temp := N
    for temp > 0 {
        digits = append([]int{temp % 10}, digits...)
        temp /= 10
    }
    // Initialize memo to -1
    for i := range memo {
        for j := range memo[i] {
            memo[i][j][0] = -1
            memo[i][j][1] = -1
        }
    }
    return digitDP(0, S, 1)
}

func main() {
    fmt.Println(countDigitSum(100, 9))  // Count numbers 0-100 with digit sum 9
    fmt.Println(countDigitSum(1000, 9)) // Count numbers 0-1000 with digit sum 9
}
```

**Rust:**
```rust
use std::collections::HashMap;

fn digit_dp(
    pos: usize,
    sum: i32,
    tight: bool,
    digits: &[u8],
    target: i32,
    memo: &mut HashMap<(usize, i32, bool), i64>,
) -> i64 {
    if pos == digits.len() {
        return if sum == 0 { 1 } else { 0 };
    }
    let key = (pos, sum, tight);
    if let Some(&cached) = memo.get(&key) {
        return cached;
    }
    let limit = if tight { digits[pos] } else { 9 };
    let mut result = 0i64;
    for d in 0..=limit {
        if sum - d as i32 < 0 { break; }
        let new_tight = tight && (d == limit);
        result += digit_dp(pos + 1, sum - d as i32, new_tight, digits, target, memo);
    }
    memo.insert(key, result);
    result
}

fn count_digit_sum(n: u64, target: i32) -> i64 {
    let digits: Vec<u8> = n.to_string()
        .chars()
        .map(|c| c as u8 - b'0')
        .collect();
    let mut memo = HashMap::new();
    digit_dp(0, target, true, &digits, target, &mut memo)
}

fn main() {
    println!("{}", count_digit_sum(100, 9));  
    println!("{}", count_digit_sum(1000, 9)); 
}
```

**C:**
```c
#include <stdio.h>
#include <string.h>

int digits[20], n_digits;
int dp_memo[20][200][2]; // pos, sum, tight

int digitDP(int pos, int sum, int tight, int target) {
    if (pos == n_digits) return sum == 0 ? 1 : 0;
    if (dp_memo[pos][sum][tight] != -1) return dp_memo[pos][sum][tight];

    int limit = tight ? digits[pos] : 9;
    int result = 0;
    for (int d = 0; d <= limit; d++) {
        if (sum - d < 0) break;
        int newTight = tight && (d == limit);
        result += digitDP(pos+1, sum-d, newTight, target);
    }
    return dp_memo[pos][sum][tight] = result;
}

int countDigitSum(long long N, int target) {
    n_digits = 0;
    long long temp = N;
    while (temp > 0) {
        digits[n_digits++] = temp % 10;
        temp /= 10;
    }
    // Reverse digits (most significant first)
    for (int i=0, j=n_digits-1; i<j; i++,j--) {
        int t=digits[i]; digits[i]=digits[j]; digits[j]=t;
    }
    memset(dp_memo, -1, sizeof(dp_memo));
    return digitDP(0, target, 1, target);
}

int main() {
    printf("%d\n", countDigitSum(100, 9));  
    printf("%d\n", countDigitSum(1000, 9)); 
    return 0;
}
```

---

## 13. Template 10: Probability & Expected Value DP

### Concept

**Probability DP** computes the probability of reaching some state.  
**Expected Value DP** computes the expected number of steps/cost to reach a goal.

```
KEY INSIGHT: DP works on probabilities and expectations just like counts!

  Probability:    p[state] = sum of (prob of transition) * p[next_state]
  Expected Value: E[state] = 1 + sum of (prob of move) * E[next_state]

Direction: Often computed BACKWARDS (from known terminal states)
```

### Problem: Knight Probability on Chessboard

> Knight starts at (r,c) on N×N board. After K moves, what's the probability it stays on board?

**5-Step Analysis:**
```
State:      dp[k][i][j] = probability that knight is at (i,j) after k moves

Transition: dp[k][i][j] = sum of dp[k-1][i-dr][j-dc] / 8
            for each of 8 knight moves (dr,dc)
            (probability of being at each origin / 8 moves)

Base:       dp[0][r][c] = 1.0 (knight starts at (r,c) with probability 1)

Answer:     sum of dp[K][i][j] for all valid (i,j)
```

**Simulation: N=3, K=2, start=(0,0)**
```
8 possible knight moves: (±1,±2), (±2,±1)

Step 0: dp[0][0][0] = 1.0

Step 1: From (0,0), valid moves:
  (0+1, 0+2) = (1,2) ← valid
  (0+2, 0+1) = (2,1) ← valid
  Others go off-board
  
  dp[1][1][2] += 1.0/8 = 0.125
  dp[1][2][1] += 1.0/8 = 0.125
  
  Probability on board after 1 move = 0.125+0.125 = 0.25

Step 2: From (1,2):
  Valid moves from (1,2): check each (1±1,2±2), (1±2,2±1)
  ... (continue simulation) ...
  
Final: sum all dp[2][i][j] = probability of staying on board after 2 moves
```

**Go:**
```go
package main

import "fmt"

var moves = [][2]int{{-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}}

func knightProbability(n, k, row, col int) float64 {
    // dp[i][j] = probability of being at (i,j)
    dp := make([][]float64, n)
    for i := range dp { dp[i] = make([]float64, n) }
    dp[row][col] = 1.0

    for step := 0; step < k; step++ {
        newDp := make([][]float64, n)
        for i := range newDp { newDp[i] = make([]float64, n) }

        for r := 0; r < n; r++ {
            for c := 0; c < n; c++ {
                if dp[r][c] == 0 { continue }
                for _, m := range moves {
                    nr, nc := r+m[0], c+m[1]
                    if nr >= 0 && nr < n && nc >= 0 && nc < n {
                        newDp[nr][nc] += dp[r][c] / 8.0
                    }
                }
            }
        }
        dp = newDp
    }

    prob := 0.0
    for r := 0; r < n; r++ {
        for c := 0; c < n; c++ {
            prob += dp[r][c]
        }
    }
    return prob
}

func main() {
    fmt.Printf("%.5f\n", knightProbability(3, 2, 0, 0)) // 0.06250
    fmt.Printf("%.5f\n", knightProbability(8, 3, 4, 4)) // 0.61230
}
```

**Rust:**
```rust
fn knight_probability(n: usize, k: usize, row: usize, col: usize) -> f64 {
    let moves: [(i32, i32); 8] = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)];
    let mut dp = vec![vec![0.0f64; n]; n];
    dp[row][col] = 1.0;

    for _ in 0..k {
        let mut new_dp = vec![vec![0.0f64; n]; n];
        for r in 0..n {
            for c in 0..n {
                if dp[r][c] == 0.0 { continue; }
                for &(dr, dc) in &moves {
                    let nr = r as i32 + dr;
                    let nc = c as i32 + dc;
                    if nr >= 0 && nr < n as i32 && nc >= 0 && nc < n as i32 {
                        new_dp[nr as usize][nc as usize] += dp[r][c] / 8.0;
                    }
                }
            }
        }
        dp = new_dp;
    }

    dp.iter().flat_map(|row| row.iter()).sum()
}

fn main() {
    println!("{:.5}", knight_probability(3, 2, 0, 0)); // 0.06250
    println!("{:.5}", knight_probability(8, 3, 4, 4)); // 0.61230
}
```

---

## 14. Space Optimization Master Techniques

### Technique 1: Rolling Array (2D → 1D)

**When**: dp[i][j] only depends on dp[i-1][...] (previous row only)

```
BEFORE (2D, O(m×n) space):
  dp[i][j] = dp[i-1][j] + dp[i][j-1]

AFTER (1D, O(n) space):
  dp[j] = dp[j] + dp[j-1]
  ↑             ↑
  this is       this is dp[i][j-1]
  dp[i-1][j]    (already updated this row)
  (not yet 
  overwritten)

CAREFUL: must update left→right, since dp[j-1] = current row value
```

**Example: LCS with O(n) space**
```
Before:
  if s1[i-1]==s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
  else:                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

After (rolling + diagonal trick):
  Need to save dp[i-1][j-1] before overwriting dp[j]
  Use variable 'prev' to hold the diagonal value
```

**Go (Space-Optimized LCS):**
```go
func lcsSpaceOpt(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([]int, n+1) // only 1 row

    for i := 1; i <= m; i++ {
        prev := 0 // this holds dp[i-1][j-1]
        for j := 1; j <= n; j++ {
            temp := dp[j] // save dp[i-1][j] before overwrite
            if s1[i-1] == s2[j-1] {
                dp[j] = prev + 1
            } else if dp[j] > dp[j-1] {
                dp[j] = dp[j]
            } else {
                dp[j] = dp[j-1]
            }
            prev = temp // dp[i-1][j] becomes dp[i-1][j-1] for next iteration
        }
    }
    return dp[n]
}
```

**Rust (Space-Optimized LCS):**
```rust
fn lcs_space_opt(s1: &str, s2: &str) -> usize {
    let (s1, s2): (Vec<char>, Vec<char>) = (s1.chars().collect(), s2.chars().collect());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![0usize; n + 1];

    for i in 1..=m {
        let mut prev = 0usize; // tracks dp[i-1][j-1]
        for j in 1..=n {
            let temp = dp[j]; // save dp[i-1][j]
            dp[j] = if s1[i-1] == s2[j-1] {
                prev + 1
            } else {
                dp[j].max(dp[j-1])
            };
            prev = temp;
        }
    }
    dp[n]
}
```

### Technique 2: Two-Row Rolling Array

**When**: You need explicit i-1 and i rows (harder to collapse to 1 row)

```go
// Example: Edit Distance with 2 rows
func editDistOpt(word1, word2 string) int {
    m, n := len(word1), len(word2)
    prev := make([]int, n+1)
    curr := make([]int, n+1)

    for j := 0; j <= n; j++ { prev[j] = j }

    for i := 1; i <= m; i++ {
        curr[0] = i
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                curr[j] = prev[j-1]
            } else {
                curr[j] = 1 + min3int(prev[j], curr[j-1], prev[j-1])
            }
        }
        prev, curr = curr, prev // swap rows
    }
    return prev[n]
}

func min3int(a, b, c int) int {
    if a < b { if a < c { return a } else { return c } }
    if b < c { return b }
    return c
}
```

### Technique 3: State Compression Table

```
PROBLEM               ORIGINAL SPACE   OPTIMIZED SPACE   TECHNIQUE
─────────────────────────────────────────────────────────────────────
Climbing Stairs       O(n)             O(1)              Keep 2 vars
House Robber          O(n)             O(1)              Keep 2 vars
Unique Paths          O(m×n)           O(n)              1 row
LCS                   O(m×n)           O(n)              Rolling + prev
Edit Distance         O(m×n)           O(n)              Rolling 2 rows
0/1 Knapsack          O(n×W)           O(W)              1D + R-to-L
Palindrome Check      O(n²)            O(n)              Expand around center
```

### Technique 4: The "Two Variables" Trick (O(1) space for linear DP)

```
When dp[i] only depends on dp[i-1] and dp[i-2]:

  int a = dp[0];   // dp[i-2]
  int b = dp[1];   // dp[i-1]
  for (i = 2 to n):
      int c = a + b  // dp[i]
      a = b
      b = c
  return b;          // dp[n]

This pattern works for: Fibonacci, Climbing Stairs, House Robber, etc.
```

---

## 15. DP on Strings

### The Master String DP Template

```
For two strings s1 (length m) and s2 (length n):

dp[i][j] defined on s1[0..i-1] and s2[0..j-1]

TEMPLATE:
  for i in 1..=m:
    for j in 1..=n:
      if s1[i-1] == s2[j-1]:
        dp[i][j] = f(dp[i-1][j-1])  ← diagonal: both chars used
      else:
        dp[i][j] = g(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                       ↑             ↑             ↑
                     skip s1[i-1]  skip s2[j-1]  replace

KEY RELATIONSHIPS:
  dp[i-1][j-1] → diagonal (match/mismatch)
  dp[i-1][j]   → from above (skip char in s1)
  dp[i][j-1]   → from left  (skip char in s2)
```

### String DP Problems Comparison Table

```
┌──────────────────────┬──────────────────────────────────────────────┐
│ Problem              │ Recurrence                                   │
├──────────────────────┼──────────────────────────────────────────────┤
│ LCS                  │ match: dp[i-1][j-1]+1                        │
│                      │ else:  max(dp[i-1][j], dp[i][j-1])          │
├──────────────────────┼──────────────────────────────────────────────┤
│ Edit Distance        │ match: dp[i-1][j-1]                          │
│                      │ else:  1+min(dp[i-1][j], dp[i][j-1],        │
│                      │             dp[i-1][j-1])                    │
├──────────────────────┼──────────────────────────────────────────────┤
│ Longest Common       │ match: dp[i-1][j-1]+1                        │
│ Substring (contiguous│ else:  0  ← RESET (not max!)                 │
│ — NOT subsequence)   │                                              │
├──────────────────────┼──────────────────────────────────────────────┤
│ Short Common         │ match: dp[i-1][j-1]+1                        │
│ Supersequence        │ else:  1+min(dp[i-1][j], dp[i][j-1])        │
│                      │ (build on top of LCS)                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ Distinct Subsequences│ match: dp[i-1][j-1] + dp[i-1][j]            │
│ (count ways s ⊆ t)   │ else:  dp[i-1][j]                           │
├──────────────────────┼──────────────────────────────────────────────┤
│ Wildcard Matching    │ '*': dp[i-1][j] | dp[i][j-1]                │
│                      │ '?'/match: dp[i-1][j-1]                      │
└──────────────────────┴──────────────────────────────────────────────┘
```

### Problem: Longest Common Substring (Contiguous)

```
CONTRAST WITH LCS:
  LCS:       "ABCDE" and "ACE" → "ACE" (skip B,D) → length 3
  Substring: "ABCDE" and "ACE" → "A","C","E" individually → max = 1
             "ABCDE" and "BCDE" → "BCDE" → length 4

KEY DIFFERENCE:
  Substring RESETS to 0 when characters don't match.
  LCS takes the max (allows gaps).
```

**Simulation: s1="ABABC", s2="BABCAB"**
```
       ""   B    A    B    C    A    B
""   [  0,  0,   0,   0,   0,   0,   0 ]
A    [  0,  0,   1,   0,   0,   1,   0 ]
B    [  0,  1,   0,   2,   0,   0,   2 ]
A    [  0,  0,   2,   0,   0,   1,   0 ]
B    [  0,  1,   0,   3,   0,   0,   2 ]
C    [  0,  0,   0,   0,   4,   0,   0 ]
               ↑           ↑
           max so far=2   new max=4

At dp[5][4]: s1[4]='C'==s2[3]='C' ✓
  dp[5][4] = dp[4][3]+1 = 3+1 = 4
  (BABC matched!)

Answer: max in table = 4 (substring "BABC")
```

**Go:**
```go
func longestCommonSubstring(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1) }

    maxLen := 0
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > maxLen { maxLen = dp[i][j] }
            } else {
                dp[i][j] = 0 // RESET — key difference from LCS!
            }
        }
    }
    return maxLen
}
```

**Rust:**
```rust
fn longest_common_substring(s1: &str, s2: &str) -> usize {
    let (s1, s2): (Vec<char>, Vec<char>) = (s1.chars().collect(), s2.chars().collect());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];
    let mut max_len = 0;

    for i in 1..=m {
        for j in 1..=n {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1;
                max_len = max_len.max(dp[i][j]);
            } // else dp[i][j] = 0 (default, already initialized)
        }
    }
    max_len
}
```

### Problem: Wildcard Pattern Matching

> `?` matches any single character. `*` matches any sequence (including empty).

**Decision Tree for each (i,j):**
```
               p[j-1] == '*' ?
              /               \
           YES                 NO
            │                  │
  dp[i][j] = dp[i-1][j]   s[i-1]==p[j-1] or p[j-1]=='?'?
             (use * to          /              \
              match s[i-1])   YES               NO
           OR dp[i][j-1]       │                │
             (* matches 0   dp[i][j] =       dp[i][j] =
              chars)         dp[i-1][j-1]      false/0
```

**Go:**
```go
func isMatchWildcard(s, p string) bool {
    m, n := len(s), len(p)
    dp := make([][]bool, m+1)
    for i := range dp { dp[i] = make([]bool, n+1) }
    dp[0][0] = true

    // Initialize: "***" matches empty string
    for j := 1; j <= n; j++ {
        if p[j-1] == '*' {
            dp[0][j] = dp[0][j-1]
        }
    }

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if p[j-1] == '*' {
                dp[i][j] = dp[i-1][j] || dp[i][j-1]
                //         (* matches    (* matches
                //          s[i-1])       empty)
            } else if p[j-1] == '?' || s[i-1] == p[j-1] {
                dp[i][j] = dp[i-1][j-1]
            }
        }
    }
    return dp[m][n]
}
```

**Rust:**
```rust
fn is_match_wildcard(s: &str, p: &str) -> bool {
    let (s, p): (Vec<char>, Vec<char>) = (s.chars().collect(), p.chars().collect());
    let (m, n) = (s.len(), p.len());
    let mut dp = vec![vec![false; n + 1]; m + 1];
    dp[0][0] = true;

    for j in 1..=n {
        if p[j-1] == '*' { dp[0][j] = dp[0][j-1]; }
    }

    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if p[j-1] == '*' {
                dp[i-1][j] || dp[i][j-1]
            } else if p[j-1] == '?' || s[i-1] == p[j-1] {
                dp[i-1][j-1]
            } else {
                false
            };
        }
    }
    dp[m][n]
}
```

---

## 16. Reconstruction: Tracing Back the Answer

> Computing dp values gives you the **optimal value**. But often you need the **actual path/sequence**. This requires tracing back through the dp table.

### General Reconstruction Framework

```
APPROACH 1: Build parent/choice array during DP
  During DP, store WHERE you came from:
  choice[i][j] = "which direction/option led to dp[i][j]"
  Then trace back from dp[n][m] → dp[0][0]

APPROACH 2: Re-derive path from dp table
  At each state, check which transition matches dp[i][j]
  Move to that state (no extra array needed, but re-traverses)
```

### LCS Reconstruction

```
dp table for s1="ABCBDAB", s2="BDCAB":

       ""   B    D    C    A    B
""   [ 0,  0,   0,   0,   0,   0 ]
A    [ 0,  0,   0,   0,   1,   1 ]
B    [ 0,  1,   1,   1,   1,   2 ]
C    [ 0,  1,   1,   2,   2,   2 ]
B    [ 0,  1,   1,   2,   2,   3 ]
D    [ 0,  1,   2,   2,   2,   3 ]
A    [ 0,  1,   2,   2,   3,   3 ]
B    [ 0,  1,   2,   2,   3,   4 ]

Traceback from dp[7][5]=4:
  s1[6]='B' == s2[4]='B' → match! Add 'B', go to dp[6][4]
  dp[6][4]=3, s1[5]='A' == s2[3]='A' → match! Add 'A', go to dp[5][3]
  dp[5][3]=2, s1[4]='D' != s2[2]='C'
    dp[4][3]=2 == dp[5][3]=2 → go UP (skip s1[4])
  dp[4][3]=2, s1[3]='B' != s2[2]='C'
    dp[3][3]=2 == dp[4][3]=2 → go UP
  dp[3][3]=2, s1[2]='C' == s2[2]='C' → match! Add 'C', go to dp[2][2]
  dp[2][2]=1, s1[1]='B' == s2[1]='D'? No.
    dp[1][2]=0 < dp[2][2]=1, so dp[2][1]=1 > dp[1][2]=0 → go LEFT
  dp[2][1]=1, s1[1]='B' == s2[0]='B' → match! Add 'B', go to dp[1][0]
  dp[1][0]=0 → STOP

Reading backwards: B,A,C,B → LCS = "BCAB"
```

**Go (LCS with Reconstruction):**
```go
func lcsWithReconstruction(s1, s2 string) string {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp { dp[i] = make([]int, n+1) }

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else if dp[i-1][j] > dp[i][j-1] {
                dp[i][j] = dp[i-1][j]
            } else {
                dp[i][j] = dp[i][j-1]
            }
        }
    }

    // Reconstruct
    result := []byte{}
    i, j := m, n
    for i > 0 && j > 0 {
        if s1[i-1] == s2[j-1] {
            result = append([]byte{s1[i-1]}, result...)
            i--
            j--
        } else if dp[i-1][j] > dp[i][j-1] {
            i-- // came from above
        } else {
            j-- // came from left
        }
    }
    return string(result)
}
```

**Rust:**
```rust
fn lcs_reconstruction(s1: &str, s2: &str) -> String {
    let (s1, s2): (Vec<char>, Vec<char>) = (s1.chars().collect(), s2.chars().collect());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0usize; n + 1]; m + 1];

    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if s1[i-1] == s2[j-1] {
                dp[i-1][j-1] + 1
            } else {
                dp[i-1][j].max(dp[i][j-1])
            };
        }
    }

    let mut result = Vec::new();
    let (mut i, mut j) = (m, n);
    while i > 0 && j > 0 {
        if s1[i-1] == s2[j-1] {
            result.push(s1[i-1]);
            i -= 1;
            j -= 1;
        } else if dp[i-1][j] > dp[i][j-1] {
            i -= 1;
        } else {
            j -= 1;
        }
    }
    result.iter().rev().collect()
}
```

### 0/1 Knapsack Reconstruction

```go
func knapsackReconstruction(wt, val []int, W int) (int, []int) {
    n := len(wt)
    dp := make([][]int, n+1)
    for i := range dp { dp[i] = make([]int, W+1) }

    for i := 1; i <= n; i++ {
        for w := 0; w <= W; w++ {
            dp[i][w] = dp[i-1][w]
            if w >= wt[i-1] {
                take := dp[i-1][w-wt[i-1]] + val[i-1]
                if take > dp[i][w] { dp[i][w] = take }
            }
        }
    }

    // Trace back which items were included
    chosen := []int{}
    w := W
    for i := n; i >= 1; i-- {
        if dp[i][w] != dp[i-1][w] {
            // item i-1 was included
            chosen = append(chosen, i-1)
            w -= wt[i-1]
        }
    }
    return dp[n][W], chosen
}
```

---

## 17. Cognitive Principles & Mental Models for DP Mastery

### The Expert's Thinking Process: Step-by-Step

```
WHEN YOU SEE A DP PROBLEM, DO THIS:

Step 1 — RECOGNITION (5 seconds)
  Ask: "Does this problem ask for min/max/count/true-false
        over some combinatorial structure?"
  If YES → likely DP

Step 2 — STATE IDENTIFICATION (30 seconds)
  Ask: "What CHANGES as I process elements?"
  → Those changing things are your state variables.
  
  Common state variables:
  • Index i in array
  • Remaining capacity
  • Current sum
  • Bitmask of visited elements
  • Position in string
  
Step 3 — RECURRENCE (2 minutes)
  Ask: "For each state, what CHOICES do I have?"
  For each choice, compute the resulting substate.
  
Step 4 — DIRECTION CHECK
  Ask: "Do I need results from SMALLER subproblems?"
  → Bottom-up: fill base cases first, build up
  → Top-down:  start big, recurse to smaller

Step 5 — BASE CASES
  Ask: "What's the trivially smallest problem?"
  Size 0, 1, empty, or single element.

Step 6 — ANSWER EXTRACTION
  Ask: "Where in my DP table is the final answer?"
  Often: dp[n], dp[n][m], max(dp[...])
```

### The Chunking Mental Model

> **Chunking** (cognitive science): experts perceive complex patterns as single units. In DP, this means:

```
BEGINNER sees:   "I need to check all subsets of size k..."
EXPERT sees:     "This is a Knapsack variant."

BEGINNER sees:   "I need to compare two strings character by character..."
EXPERT sees:     "This is LCS structure — diagonal DP table."

Build your chunk library:
  Pattern A: "max/min value from n items with constraint" → Knapsack
  Pattern B: "count paths in grid/recursion" → Grid DP
  Pattern C: "optimal split of array/string" → Interval DP
  Pattern D: "process elements, state carries forward" → Linear DP
  Pattern E: "string comparison or alignment" → Sequence DP
  Pattern F: "small set of items (n≤20)" → Bitmask DP
  Pattern G: "count numbers with digit property" → Digit DP
```

### Pattern Recognition Table

```
┌─────────────────────────────────────┬────────────────────────────┐
│ Problem Keywords                    │ DP Pattern                 │
├─────────────────────────────────────┼────────────────────────────┤
│ "ways to climb n stairs"            │ Linear DP (Fibonacci-like) │
│ "minimum cost path in grid"         │ Grid DP                    │
│ "select items, max value ≤ W"       │ 0/1 Knapsack               │
│ "item can be used multiple times"   │ Unbounded Knapsack         │
│ "longest common subsequence"        │ LCS (Sequence DP)          │
│ "longest increasing subsequence"    │ LIS (Linear DP)            │
│ "transform string A to B"           │ Edit Distance              │
│ "optimal parenthesization"          │ Interval DP                │
│ "buy/sell stocks with constraints"  │ State Machine DP           │
│ "rob connected houses/tree"         │ Tree DP                    │
│ "visit all cities exactly once"     │ Bitmask DP (TSP)           │
│ "count numbers with property ≤ N"   │ Digit DP                   │
│ "probability of sequence of events" │ Probability DP             │
│ "palindrome partitioning"           │ Interval DP                │
│ "game theory: two players optimal"  │ Minimax DP                 │
└─────────────────────────────────────┴────────────────────────────┘
```

### The Deliberate Practice Framework for DP

```
LEVEL 1 — Fundamentals (Week 1-2)
  Problems: Fibonacci, Climbing Stairs, House Robber
  Goal: Internalize the 5-step framework
  Practice: Write both memoization AND tabulation versions

LEVEL 2 — Classic Patterns (Week 3-5)
  Problems: 0/1 Knapsack, LCS, LIS, Edit Distance, Coin Change
  Goal: Recognize and implement major DP templates
  Practice: Space-optimize every solution

LEVEL 3 — 2D & Interval (Week 6-8)
  Problems: Matrix Chain, Palindrome Partitioning, Unique Paths
  Goal: Master diagonal traversal and interval splitting
  Practice: Reconstruct actual solutions, not just values

LEVEL 4 — Advanced Patterns (Week 9-12)
  Problems: TSP (Bitmask), Digit DP, Tree DP
  Goal: Apply DP to non-standard structures
  Practice: Derive recurrences independently

LEVEL 5 — Competition-Level (Month 4+)
  Problems: DP with segment tree, Convex Hull Trick, Divide & Conquer DP
  Goal: Optimize DP with advanced data structures
  Practice: Solve under time pressure
```

### Psychological Flow State for DP

```
HOW TO ENTER FLOW while solving DP problems:

1. REDUCE ANXIETY: Start by identifying "what changes"
   Don't rush to code — spend 5 min on paper first.

2. BUILD CONFIDENCE: Always start with brute force O(2^n) or O(n!)
   Then ask "what am I recomputing?" → that's your memoization target.

3. CHUNKING PRACTICE: After solving, close your eyes and
   replay the solution structure. Build pattern memory.

4. SPACED REPETITION: Revisit solved problems after 1 day,
   3 days, 1 week, 2 weeks. Rebuild from scratch each time.

5. METACOGNITION: After each problem, ask:
   "What was my wrong assumption?"
   "What pattern should I have recognized earlier?"
   "How does this relate to problems I already know?"
```

### The 3-Layer DP Understanding Model

```
Layer 1 — WHAT: Surface (Code)
  "dp[i] = dp[i-1] + dp[i-2]"
  Can write the code if given the recurrence

Layer 2 — WHY: Structure (Reasoning)
  "We sum prev two because at each step we can come
   from 1 or 2 positions behind"
  Can derive the recurrence from problem description

Layer 3 — WHEN: Pattern (Intuition)
  "This looks like a reachability/counting problem
   on a linear sequence — use Fibonacci-like DP"
  Can RECOGNIZE the pattern before even reading fully

GOAL: Reach Layer 3 for all major patterns.
      This is the level of top-1% competitive programmers.
```

---

## COMPLETE TEMPLATE REFERENCE CARD

```
╔════════════════════════════════════════════════════════════════╗
║                  DP TEMPLATE CHEAT SHEET                      ║
╠══════════════════╦════════════════════════════╦═══════════════╣
║ PATTERN          ║ STATE                      ║ DIRECTION     ║
╠══════════════════╬════════════════════════════╬═══════════════╣
║ Linear           ║ dp[i]                      ║ L → R         ║
║ Grid             ║ dp[i][j]                   ║ TL → BR       ║
║ Knapsack 0/1     ║ dp[i][w]                   ║ L→R, w: R←L   ║
║ Knapsack Unbound ║ dp[w]                      ║ L → R         ║
║ Interval         ║ dp[i][j] (length first)    ║ diagonal      ║
║ LCS/Edit Dist    ║ dp[i][j]                   ║ TL → BR       ║
║ LIS O(n²)        ║ dp[i]                      ║ L → R         ║
║ LIS O(nlogn)     ║ tails[] + binary search    ║ L → R         ║
║ State Machine    ║ dp[day][state]             ║ L → R         ║
║ Tree DP          ║ dp[node][choice]           ║ post-order    ║
║ Bitmask          ║ dp[mask][pos]              ║ mask: 0→2^n   ║
║ Digit            ║ dp[pos][sum/prop][tight]   ║ recursion+memo║
║ Probability      ║ dp[step][pos]              ║ L → R         ║
╚══════════════════╩════════════════════════════╩═══════════════╝

SPACE OPTIMIZATION GUIDE:
  dp[i] depends on dp[i-1] only        → O(1) with 2 variables
  dp[i][j] depends on dp[i-1][j,j-1]  → O(n) rolling array
  0/1 Knapsack 1D                      → iterate W: right→left
  Unbounded Knapsack 1D                → iterate W: left→right

RECURRENCE CATEGORIES:
  Take/Skip:  dp[i] = max(dp[i-1], dp[i-k] + val[i])
  Split:      dp[i][j] = min over k of dp[i][k] + dp[k+1][j] + cost
  Align:      dp[i][j] = match ? dp[i-1][j-1]+1 : f(dp[i-1][j], dp[i][j-1])
  Reachable:  dp[i][j] = dp[i-1][j] + dp[i][j-1]
```

---

*"The difference between a good programmer and a great one is not cleverness — it is the depth of pattern recognition built through disciplined repetition. Every problem you solve deepens the neural pathways that make the next problem faster to see."*

*Master these templates not as recipes, but as mental structures. When you internalize the WHY behind each recurrence, you gain the power to derive them from scratch — and that is the mark of the top 1%.*

Now I'll craft the full comprehensive guide. This will be extensive — let me build it in sections.Here is your complete DP Bible — **3,582 lines, 105KB** of pure depth. Here's what's inside:

---

## What This Guide Covers

**10 Complete DP Templates**, each with:
- Deep conceptual explanation (prerequisites explained before use)
- The 5-step framework applied to every problem
- ASCII simulation tables showing exact dp values step-by-step
- Decision flow diagrams and traversal order visualizations
- Full implementations in **Go, C, and Rust**

```
| # | Template | Problems Covered |
|---|---|---|
| 1 | **Linear DP** | Climbing Stairs, House Robber |
| 2 | **Knapsack Family** | 0/1, Unbounded, Subset Sum — with the crucial right→left vs left→right direction insight |
| 3 | **Grid / 2D DP** | Unique Paths, Min Path Sum |
| 4 | **Interval DP** | Matrix Chain Multiplication, Palindrome Min Cuts |
| 5 | **Sequence DP** | LCS, LIS (O(n²) and O(n log n)), Edit Distance |
| 6 | **State Machine DP** | Stock Trading with Cooldown |
| 7 | **Tree DP** | House Robber III |
| 8 | **Bitmask DP** | Travelling Salesman Problem |
| 9 | **Digit DP** | Count numbers with digit-sum property in [0,N] |
| 10 | **Probability DP** | Knight Probability on Chessboard |

```

**Plus:**
- Space optimization master techniques (rolling array, 2-row swap, O(1) collapse)
- Full **reconstruction/traceback** framework with worked LCS example
- String DP master comparison table (LCS vs Substring vs Edit Distance vs Wildcard)
- Cognitive mastery section: chunking, deliberate practice levels 1–5, pattern recognition table, the 3-layer understanding model

The single most important insight to carry always: **the direction of inner loop iteration** (right→left for 0/1 Knapsack, left→right for Unbounded) determines whether an item is reused — that one insight unlocks the entire knapsack family.