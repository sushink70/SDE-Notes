# 🏔️ The Complete Dynamic Programming Mastery Guide

## From First Principles to Top 1% Understanding

---

# 📚 **TABLE OF CONTENTS**

1. **What is Dynamic Programming? (The Foundation)**
2. **The Two Pillars: Memoization vs Tabulation**
3. **TOP-DOWN: Memoization Deep Dive**
4. **BOTTOM-UP: Tabulation Deep Dive**
5. **Side-by-Side Transformation Process**
6. **When to Use Which Approach**
7. **Implementation Patterns (Python, Rust, Go)**
8. **Classic DP Problems Solved Both Ways**
9. **Mental Models & Problem-Solving Framework**
10. **Optimization Techniques**

---

## 1️⃣ **WHAT IS DYNAMIC PROGRAMMING?**

### **Definition**

Dynamic Programming (DP) is an **optimization technique** that solves complex problems by:

1. Breaking them into **overlapping subproblems**
2. Solving each subproblem **once**
3. **Storing** the results
4. **Reusing** stored results instead of recomputing

### **The Core Insight (Mental Model)**

```
┌─────────────────────────────────────────────────────────────┐
│         THE DP EQUATION OF ENLIGHTENMENT                    │
│                                                             │
│   Overlapping Subproblems + Optimal Substructure = DP       │
│                                                             │
│   "Those who cannot remember the past are                   │
│    condemned to recompute it." - DP Proverb                 │
└─────────────────────────────────────────────────────────────┘
```

### **Two Required Properties for DP**

```
┌──────────────────────────────────────────────────────────────┐
│  PROPERTY 1: OVERLAPPING SUBPROBLEMS                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Problem breaks down into subproblems that are REUSED        │
│  multiple times.                                             │
│                                                              │
│  Example: fib(5) needs fib(3) twice                          │
│                                                              │
│  Contrast with DIVIDE & CONQUER:                             │
│  - Merge Sort: Each subarray sorted once (no overlap)        │
│  - Quick Sort: Each partition processed once                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  PROPERTY 2: OPTIMAL SUBSTRUCTURE                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Optimal solution can be constructed from optimal            │
│  solutions of subproblems.                                   │
│                                                              │
│  Example: Shortest path A→C through B =                      │
│           Shortest(A→B) + Shortest(B→C)                      │
│                                                              │
│  If optimal substructure doesn't hold, DP won't work!        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2️⃣ **THE TWO PILLARS: MEMOIZATION vs TABULATION**

### **The Philosophical Divide**

```
                    DYNAMIC PROGRAMMING
                           |
            ┌──────────────┴──────────────┐
            ↓                             ↓
     TOP-DOWN                       BOTTOM-UP
    (Memoization)                  (Tabulation)
            |                             |
    ┌───────┴────────┐          ┌────────┴────────┐
    ↓                ↓          ↓                 ↓
RECURSIVE        CACHE      ITERATIVE         TABLE
"Solve big       Results    "Build from     Fill array
problem,                    smallest         sequentially
break down"                 to largest"
```

### **Core Conceptual Difference**

```
┌────────────────────────────────────────────────────────────────┐
│                    MEMOIZATION (TOP-DOWN)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Start: "I need fib(5)"                                        │
│  Think: "To get fib(5), I need fib(4) and fib(3)"              │
│  Action: Recursively ask for needed values                     │
│  Store: Cache results as you compute them                      │
│                                                                │
│  Direction: Problem → Subproblems (recursive descent)          │
│  Philosophy: "Lazy evaluation" - compute only what's needed    │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    TABULATION (BOTTOM-UP)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Start: "I know fib(0)=0 and fib(1)=1"                         │
│  Think: "I can build fib(2), then fib(3), ... up to fib(5)"    │
│  Action: Iteratively build table of all values                 │
│  Store: Table/array holds all computed results                 │
│                                                                │
│  Direction: Base cases → Final answer (iterative ascent)       │
│  Philosophy: "Eager evaluation" - compute everything upfront   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ **TOP-DOWN: MEMOIZATION DEEP DIVE**

### **Concept: Memoization**

From Latin "memorandum" (to be remembered). Cache function results keyed by their inputs.

### **The Memoization Pattern**

```
┌─────────────────────────────────────────────────────────────┐
│              MEMOIZATION TEMPLATE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CREATE cache/memo (usually dict/hashmap)                │
│  2. CHECK if answer already in cache → return it            │
│  3. COMPUTE answer recursively                              │
│  4. STORE answer in cache                                   │
│  5. RETURN answer                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Visual: Memoization Flow**

```
                    solve(n)
                       |
                       ↓
              ┌────────────────┐
              │ n in cache?    │
              └────────┬───────┘
                       |
           ┌───────────┴───────────┐
           ↓                       ↓
        YES                      NO
           |                       |
           ↓                       ↓
   Return cache[n]         Compute solve(n-1),
      (O(1) lookup!)             solve(n-2)
                                   |
                                   ↓
                            Store in cache[n]
                                   |
                                   ↓
                              Return result
```

### **Fibonacci: Memoization - All Three Languages**

#### **Python (Dict-based)**

```python
def fib_memo(n, memo=None):
    """
    TOP-DOWN Dynamic Programming with Memoization
    
    TIME: O(n) - each subproblem computed once
    SPACE: O(n) - memo dict + recursion stack
    """
    if memo is None:
        memo = {}
    
    # Base cases
    if n <= 1:
        return n
    
    # Check cache
    if n in memo:
        return memo[n]
    
    # Recursive computation
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]

# Alternative: Using decorator (Pythonic way!)
from functools import lru_cache

@lru_cache(maxsize=None)  # Unlimited cache
def fib_memo_decorator(n):
    """Built-in memoization - Python magic!"""
    if n <= 1:
        return n
    return fib_memo_decorator(n - 1) + fib_memo_decorator(n - 2)
```

#### **Rust (HashMap-based)**

```rust
use std::collections::HashMap;

fn fib_memo(n: i32, memo: &mut HashMap<i32, i64>) -> i64 {
    // TOP-DOWN with memoization
    // TIME: O(n), SPACE: O(n)
    
    // Base cases
    if n <= 1 {
        return n as i64;
    }
    
    // Check cache (Rust pattern matching!)
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    // Recursive computation
    let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    
    // Store in cache
    memo.insert(n, result);
    
    result
}

// Usage
fn main() {
    let mut memo = HashMap::new();
    let result = fib_memo(50, &mut memo);
    println!("fib(50) = {}", result);
}
```

#### **Go (Map-based)**

```go
package main

import "fmt"

func fibMemo(n int, memo map[int]int) int {
    // TOP-DOWN with memoization
    // TIME: O(n), SPACE: O(n)
    
    // Base cases
    if n <= 1 {
        return n
    }
    
    // Check cache
    if val, exists := memo[n]; exists {
        return val
    }
    
    // Recursive computation
    result := fibMemo(n-1, memo) + fibMemo(n-2, memo)
    
    // Store in cache
    memo[n] = result
    
    return result
}

func main() {
    memo := make(map[int]int)
    result := fibMemo(50, memo)
    fmt.Printf("fib(50) = %d\n", result)
}
```

### **Execution Trace: Memoization**

```
Call fib_memo(5) with memo = {}

Step 1: fib_memo(5)
  ├─ 5 not in memo
  ├─ Call fib_memo(4)
  │   ├─ 4 not in memo
  │   ├─ Call fib_memo(3)
  │   │   ├─ 3 not in memo
  │   │   ├─ Call fib_memo(2)
  │   │   │   ├─ 2 not in memo
  │   │   │   ├─ Call fib_memo(1) → 1 (base)
  │   │   │   ├─ Call fib_memo(0) → 0 (base)
  │   │   │   ├─ memo[2] = 1
  │   │   │   └─ Return 1
  │   │   ├─ Call fib_memo(1) → 1 (base)
  │   │   ├─ memo[3] = 2
  │   │   └─ Return 2
  │   ├─ Call fib_memo(2)
  │   │   └─ 2 IN MEMO! Return 1 ✓ (no recursion!)
  │   ├─ memo[4] = 3
  │   └─ Return 3
  ├─ Call fib_memo(3)
  │   └─ 3 IN MEMO! Return 2 ✓ (no recursion!)
  ├─ memo[5] = 5
  └─ Return 5

Final memo state: {0:0, 1:1, 2:1, 3:2, 4:3, 5:5}
Total recursive calls: 9 (vs 15 without memo!)
```

---

## 4️⃣ **BOTTOM-UP: TABULATION DEEP DIVE**

### **Concept: Tabulation**

Build a table (array/list) by solving subproblems in order from smallest to largest, using previously computed values.

### **The Tabulation Pattern**

```
┌─────────────────────────────────────────────────────────────┐
│              TABULATION TEMPLATE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CREATE table (array/list) of size n+1                   │
│  2. INITIALIZE base cases in table                          │
│  3. ITERATE from smallest to largest subproblem             │
│  4. FILL each table[i] using previously computed values     │
│  5. RETURN table[n] (final answer)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Visual: Tabulation Flow**

```
Initialize table:  [0, 1, ?, ?, ?, ?]  ← Base cases set
                    ↑  ↑
                  base cases

Iteration i=2:     [0, 1, 1, ?, ?, ?]  ← table[2] = table[1]+table[0]
                          ↑  ↑
                       use these

Iteration i=3:     [0, 1, 1, 2, ?, ?]  ← table[3] = table[2]+table[1]
                             ↑  ↑
                          use these

Iteration i=4:     [0, 1, 1, 2, 3, ?]  ← table[4] = table[3]+table[2]
                                ↑  ↑
                             use these

Iteration i=5:     [0, 1, 1, 2, 3, 5]  ← table[5] = table[4]+table[3]
                                   ↑  ↑
                                use these

Return table[5] = 5 ✓
```

### **Fibonacci: Tabulation - All Three Languages**

#### **Python (List-based)**

```python
def fib_tab(n):
    """
    BOTTOM-UP Dynamic Programming with Tabulation
    
    TIME: O(n) - single pass through table
    SPACE: O(n) - table array
    """
    # Handle edge cases
    if n <= 1:
        return n
    
    # Create and initialize table
    table = [0] * (n + 1)
    table[0] = 0  # Base case
    table[1] = 1  # Base case
    
    # Fill table iteratively
    for i in range(2, n + 1):
        table[i] = table[i - 1] + table[i - 2]
    
    return table[n]

# Space-optimized version (only need last 2 values!)
def fib_tab_optimized(n):
    """
    SPACE: O(1) - only store 2 values
    
    Mental model: Sliding window of size 2
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1  # fib(0), fib(1)
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1  # Slide window
        prev1 = current
    
    return prev1
```

#### **Rust (Vector-based)**

```rust
fn fib_tab(n: usize) -> i64 {
    // BOTTOM-UP with tabulation
    // TIME: O(n), SPACE: O(n)
    
    if n <= 1 {
        return n as i64;
    }
    
    // Create and initialize table
    let mut table = vec![0i64; n + 1];
    table[0] = 0;
    table[1] = 1;
    
    // Fill table iteratively
    for i in 2..=n {
        table[i] = table[i - 1] + table[i - 2];
    }
    
    table[n]
}

// Space-optimized version
fn fib_tab_optimized(n: usize) -> i64 {
    // SPACE: O(1) - constant space!
    
    if n <= 1 {
        return n as i64;
    }
    
    let (mut prev2, mut prev1) = (0i64, 1i64);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}
```

#### **Go (Slice-based)**

```go
func fibTab(n int) int {
    // BOTTOM-UP with tabulation
    // TIME: O(n), SPACE: O(n)
    
    if n <= 1 {
        return n
    }
    
    // Create and initialize table
    table := make([]int, n+1)
    table[0] = 0
    table[1] = 1
    
    // Fill table iteratively
    for i := 2; i <= n; i++ {
        table[i] = table[i-1] + table[i-2]
    }
    
    return table[n]
}

// Space-optimized version
func fibTabOptimized(n int) int {
    // SPACE: O(1)
    
    if n <= 1 {
        return n
    }
    
    prev2, prev1 := 0, 1
    
    for i := 2; i <= n; i++ {
        current := prev1 + prev2
        prev2 = prev1
        prev1 = current
    }
    
    return prev1
}
```

### **Execution Trace: Tabulation**

```
Call fib_tab(5)

Step 1: Initialize table
table = [0, 1, 0, 0, 0, 0]
         ↑  ↑
      base cases

Step 2: i = 2
table[2] = table[1] + table[0] = 1 + 0 = 1
table = [0, 1, 1, 0, 0, 0]

Step 3: i = 3
table[3] = table[2] + table[1] = 1 + 1 = 2
table = [0, 1, 1, 2, 0, 0]

Step 4: i = 4
table[4] = table[3] + table[2] = 2 + 1 = 3
table = [0, 1, 1, 2, 3, 0]

Step 5: i = 5
table[5] = table[4] + table[3] = 3 + 2 = 5
table = [0, 1, 1, 2, 3, 5]

Return table[5] = 5 ✓

Total iterations: 4 (i = 2, 3, 4, 5)
No recursion! Pure iteration.
```

---

## 5️⃣ **SIDE-BY-SIDE TRANSFORMATION PROCESS**

### **From Naive → Memoization → Tabulation**

```
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1: NAIVE RECURSION (The Problem)                      │
├──────────────────────────────────────────────────────────────┤

def fib_naive(n):
    if n <= 1:
        return n
    return fib_naive(n-1) + fib_naive(n-2)
    
❌ TIME: O(2^n) - exponential disaster
❌ Recalculates same values repeatedly

└──────────────────────────────────────────────────────────────┘

                    ↓ ADD CACHE ↓

┌──────────────────────────────────────────────────────────────┐
│  STAGE 2: MEMOIZATION (Top-Down DP)                          │
├──────────────────────────────────────────────────────────────┤

def fib_memo(n, memo=None):
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n in memo:          # ← CHECK CACHE
        return memo[n]
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]         # ← STORE & RETURN

✓ TIME: O(n) - each value computed once
✓ SPACE: O(n) - memo + recursion stack
✓ Still recursive structure

└──────────────────────────────────────────────────────────────┘

              ↓ ELIMINATE RECURSION ↓

┌──────────────────────────────────────────────────────────────┐
│  STAGE 3: TABULATION (Bottom-Up DP)                          │
├──────────────────────────────────────────────────────────────┤

def fib_tab(n):
    if n <= 1:
        return n
    table = [0] * (n + 1)
    table[0], table[1] = 0, 1
    for i in range(2, n + 1):  # ← ITERATIVE
        table[i] = table[i-1] + table[i-2]
    return table[n]

✓ TIME: O(n) - single loop
✓ SPACE: O(n) - table only (no stack!)
✓ Iterative, easier to optimize

└──────────────────────────────────────────────────────────────┘

         ↓ OPTIMIZE SPACE ↓

┌──────────────────────────────────────────────────────────────┐
│  STAGE 4: SPACE-OPTIMIZED TABULATION                         │
├──────────────────────────────────────────────────────────────┤

def fib_optimized(n):
    if n <= 1:
        return n
    prev2, prev1 = 0, 1
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current  # ← SLIDE WINDOW
    return prev1

✓ TIME: O(n)
✓ SPACE: O(1) - only 2 variables! 🎯
✓ Maximum efficiency achieved

└──────────────────────────────────────────────────────────────┘
```

---

## 6️⃣ **WHEN TO USE WHICH APPROACH**

### **Decision Flowchart**

```
                 Start: Need to solve DP problem
                            |
                            ↓
            ┌───────────────────────────────┐
            │ Can you easily identify       │
            │ the dependency order?         │
            └───────────┬───────────────────┘
                        |
        ┌───────────────┴───────────────┐
        ↓                               ↓
       YES                             NO
        |                               |
        ↓                               ↓
  Use TABULATION                  Use MEMOIZATION
  (Bottom-Up)                     (Top-Down)
        |                               |
        ↓                               ↓
  Clear order:                    Unclear order:
  - fib(0)→fib(1)→...            - Complex dependencies
  - Build smallest first         - Let recursion handle it
        |                               |
        ↓                               ↓
  ┌──────────────┐              ┌──────────────┐
  │ Need to save │              │ Only need    │
  │ all values?  │              │ one answer?  │
  └──────┬───────┘              └──────┬───────┘
         |                             |
    ┌────┴────┐                   ┌────┴────┐
    ↓         ↓                   ↓         ↓
   YES       NO                  YES       NO
    |         |                   |         |
    ↓         ↓                   ↓         ↓
 Use full  Optimize            Keep    Convert to
  table    space               memo    tabulation
           (O(1))                      if possible
```

### **Comparison Table**

```
┌─────────────────┬──────────────────────┬─────────────────────┐
│   CRITERIA      │   MEMOIZATION        │    TABULATION       │
│                 │   (Top-Down)         │    (Bottom-Up)      │
├─────────────────┼──────────────────────┼─────────────────────┤
│ Approach        │ Recursive            │ Iterative           │
│                 │                      │                     │
│ Direction       │ Problem → Base       │ Base → Problem      │
│                 │                      │                     │
│ Structure       │ Recursion tree       │ Loop + table        │
│                 │                      │                     │
│ Evaluation      │ Lazy (on-demand)     │ Eager (all values)  │
│                 │                      │                     │
│ Space           │ O(n) + stack         │ O(n) or O(1)        │
│                 │                      │ (optimizable!)      │
│                 │                      │                     │
│ Intuition       │ Natural (like        │ Requires planning   │
│                 │ problem statement)   │                     │
│                 │                      │                     │
│ Debugging       │ Harder (recursion)   │ Easier (linear)     │
│                 │                      │                     │
│ Stack overflow  │ Risk for large n     │ No risk             │
│                 │                      │                     │
│ Partial solve   │ Yes (compute only    │ No (computes all)   │
│                 │ needed)              │                     │
│                 │                      │                     │
│ Performance     │ Slightly slower      │ Slightly faster     │
│                 │ (function calls)     │ (no call overhead)  │
│                 │                      │                     │
│ Best for        │ - Complex deps       │ - Clear order       │
│                 │ - Not all values     │ - Need all values   │
│                 │   needed             │ - Space optimization│
│                 │ - Easier to write    │ - Performance       │
└─────────────────┴──────────────────────┴─────────────────────┘
```

### **When to Choose: Decision Matrix**

```
┌──────────────────────────────────────────────────────────────┐
│                    USE MEMOIZATION IF:                       │
├──────────────────────────────────────────────────────────────┤
│ ✓ Problem naturally suggests recursion                       │
│ ✓ Not all subproblems need to be solved                      │
│ ✓ Dependencies are complex or unclear                        │
│ ✓ You want to code it quickly (mirrors problem statement)    │
│ ✓ Input space is sparse (not computing everything)           │
│                                                              │
│ Examples: Some tree problems, graph problems with pruning    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    USE TABULATION IF:                        │
├──────────────────────────────────────────────────────────────┤
│ ✓ Clear ordering of subproblems exists                       │
│ ✓ All (or most) subproblems will be solved anyway            │
│ ✓ You need maximum performance                               │
│ ✓ Stack overflow is a concern (large n)                      │
│ ✓ Space can be optimized (sliding window pattern)            │
│                                                              │
│ Examples: Fibonacci, Climbing Stairs, Coin Change            │
└──────────────────────────────────────────────────────────────┘
```

---

## 7️⃣ **CLASSIC DP PROBLEM: CLIMBING STAIRS**

### **Problem Statement**

You're climbing stairs. You can take 1 or 2 steps at a time.
How many distinct ways can you climb to the top with n steps?

### **Analysis**

```
Example: n = 3

Ways to reach step 3:
1. One step + one step + one step  (1+1+1)
2. One step + two steps            (1+2)
3. Two steps + one step            (2+1)

Answer: 3 ways

Pattern Recognition:
- To reach step n, you must come from step (n-1) or step (n-2)
- ways(n) = ways(n-1) + ways(n-2)
- This is Fibonacci in disguise! 🎭
```

### **Solution 1: Memoization (Top-Down)**

```python
def climb_stairs_memo(n, memo=None):
    """
    Top-Down DP: Memoization
    
    Recurrence: ways(n) = ways(n-1) + ways(n-2)
    Base: ways(0)=1, ways(1)=1
    
    TIME: O(n), SPACE: O(n)
    """
    if memo is None:
        memo = {}
    
    # Base cases
    if n <= 1:
        return 1
    
    # Check cache
    if n in memo:
        return memo[n]
    
    # Recursive relation
    memo[n] = climb_stairs_memo(n-1, memo) + climb_stairs_memo(n-2, memo)
    return memo[n]
```

### **Solution 2: Tabulation (Bottom-Up)**

```python
def climb_stairs_tab(n):
    """
    Bottom-Up DP: Tabulation
    
    Build table from base cases upward
    
    TIME: O(n), SPACE: O(n)
    """
    if n <= 1:
        return 1
    
    # Create table
    dp = [0] * (n + 1)
    dp[0] = 1  # 1 way to stay at ground
    dp[1] = 1  # 1 way to reach step 1
    
    # Fill table
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]
```

### **Solution 3: Space-Optimized**

```python
def climb_stairs_optimized(n):
    """
    Space-Optimized Tabulation
    
    Only need last 2 values!
    
    TIME: O(n), SPACE: O(1) 🎯
    """
    if n <= 1:
        return 1
    
    prev2, prev1 = 1, 1  # ways(0), ways(1)
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    
    return prev1
```

### **Visual: State Transitions**

```
Problem: climb_stairs(5)

TABULATION BUILD:
┌───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ ← step
├───┼───┼───┼───┼───┼───┤
│ 1 │ 1 │ ? │ ? │ ? │ ? │ ← ways
└───┴───┴───┴───┴───┴───┘

Step 1: dp[2] = dp[1] + dp[0] = 1 + 1 = 2
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 1 │ 2 │ ? │ ? │ ? │
└───┴───┴───┴───┴───┴───┘
      ↑   ↑
      └───┴─ add these

Step 2: dp[3] = dp[2] + dp[1] = 2 + 1 = 3
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 1 │ 2 │ 3 │ ? │ ? │
└───┴───┴───┴───┴───┴───┘
          ↑   ↑
          └───┴─ add these

Step 3: dp[4] = dp[3] + dp[2] = 3 + 2 = 5
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 1 │ 2 │ 3 │ 5 │ ? │
└───┴───┴───┴───┴───┴───┘
              ↑   ↑
              └───┴─ add these

Step 4: dp[5] = dp[4] + dp[3] = 5 + 3 = 8
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 1 │ 2 │ 3 │ 5 │ 8 │ ← Answer!
└───┴───┴───┴───┴───┴───┘
                  ↑   ↑
                  └───┴─ add these
```

---

## 8️⃣ **CLASSIC DP PROBLEM: MIN COST CLIMBING STAIRS**

### **Problem**

Each step has a cost. You start at index 0 or 1. 
Find minimum cost to reach the top (past last step).

```
Example: cost = [10, 15, 20]
         indices: 0   1   2   (top is index 3)

Options:
- Start at 0: pay 10, jump to 2, pay 20, reach top = 30
- Start at 1: pay 15, jump to top = 15 ✓ (minimum!)

Answer: 15
```

### **Key Insight**

```
dp[i] = minimum cost to reach step i
dp[i] = cost[i] + min(dp[i-1], dp[i-2])
        └──┬──┘   └────────┬───────────┘
      pay current   cheaper previous path
```

### **Solution: Both Approaches**

#### **Memoization**

```python
def min_cost_memo(cost, i, memo):
    """
    Top-Down: What's min cost to reach step i?
    
    TIME: O(n), SPACE: O(n)
    """
    # Reached past the end
    if i >= len(cost):
        return 0
    
    if i in memo:
        return memo[i]
    
    # Choose cheaper of two previous steps
    memo[i] = cost[i] + min(
        min_cost_memo(cost, i+1, memo),
        min_cost_memo(cost, i+2, memo)
    )
    return memo[i]

def min_cost_climbing_stairs(cost):
    memo = {}
    # Start from step 0 or step 1
    return min(
        min_cost_memo(cost, 0, memo),
        min_cost_memo(cost, 1, memo)
    )
```

#### **Tabulation**

```python
def min_cost_tab(cost):
    """
    Bottom-Up: Build minimum costs from bottom
    
    TIME: O(n), SPACE: O(n)
    """
    n = len(cost)
    if n == 0:
        return 0
    if n == 1:
        return cost[0]
    
    # dp[i] = min cost to reach step i
    dp = [0] * (n + 1)
    
    # Base: can start at step 0 or 1 for free
    dp[0] = cost[0]
    dp[1] = cost[1]
    
    # Fill table
    for i in range(2, n):
        dp[i] = cost[i] + min(dp[i-1], dp[i-2])
    
    # Top is one step beyond, reachable from n-1 or n-2
    return min(dp[n-1], dp[n-2])
```

#### **Space-Optimized**

```python
def min_cost_optimized(cost):
    """
    Only need last 2 values!
    
    TIME: O(n), SPACE: O(1) 🎯
    """
    n = len(cost)
    if n == 0:
        return 0
    if n == 1:
        return cost[0]
    
    prev2 = cost[0]
    prev1 = cost[1]
    
    for i in range(2, n):
        current = cost[i] + min(prev1, prev2)
        prev2 = prev1
        prev1 = current
    
    return min(prev1, prev2)
```

### **Execution Trace**

```
cost = [10, 15, 20]

TABULATION:
┌─────┬─────┬─────┬──────┐
│ i=0 │ i=1 │ i=2 │ top  │
├─────┼─────┼─────┼──────┤
│ 10  │ 15  │ 20  │  ?   │ ← step costs
└─────┴─────┴─────┴──────┘

Initialize:
dp[0] = 10  (start here, pay 10)
dp[1] = 15  (start here, pay 15)

i=2:
dp[2] = cost[2] + min(dp[1], dp[0])
      = 20 + min(15, 10)
      = 20 + 10 = 30

Final table:
┌─────┬─────┬─────┐
│ 10  │ 15  │ 30  │
└─────┴─────┴─────┘

Answer: min(dp[2], dp[1]) = min(30, 15) = 15 ✓

Path: Start at 1 (pay 15) → Jump to top
```

---

## 9️⃣ **MENTAL MODELS & PROBLEM-SOLVING FRAMEWORK**

### **The DP Master Framework**

```
┌──────────────────────────────────────────────────────────────┐
│         5-STEP DP PROBLEM-SOLVING FRAMEWORK                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  STEP 1: IDENTIFY if it's a DP problem                       │
│    ❓ Ask: "Are there overlapping subproblems?"              │
│    ❓ Ask: "Does optimal solution use optimal subproblems?"  │
│                                                              │
│  STEP 2: DEFINE the state                                    │
│    📝 What does dp[i] represent?                             │
│    📝 What are the dimensions? (1D, 2D, 3D array?)           │
│                                                              │
│  STEP 3: FIND the recurrence relation                        │
│    🔄 How does dp[i] relate to previous values?              │
│    🔄 Write the mathematical formula                         │
│                                                              │
│  STEP 4: IDENTIFY base cases                                 │
│    🎯 What are the smallest subproblems?                     │
│    🎯 What can you solve directly?                           │
│                                                              │
│  STEP 5: DETERMINE the order of computation                  │
│    📊 Top-down (memo) or bottom-up (tab)?                    │
│    📊 Can space be optimized?                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Pattern Recognition: Common DP Types**

```
┌──────────────────────────────────────────────────────────────┐
│                   DP PROBLEM TAXONOMY                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. LINEAR DP (1D)                                           │
│     - Fibonacci, Climbing Stairs                             │
│     - House Robber                                           │
│     - Decode Ways                                            │
│     Pattern: dp[i] depends on dp[i-1], dp[i-2], etc.         │
│                                                              │
│  2. 2D GRID DP                                               │
│     - Unique Paths                                           │
│     - Minimum Path Sum                                       │
│     Pattern: dp[i][j] depends on dp[i-1][j], dp[i][j-1]      │
│                                                              │
│  3. SEQUENCE DP (2D)                                         │
│     - Longest Common Subsequence (LCS)                       │
│     - Edit Distance                                          │
│     Pattern: dp[i][j] for two sequences                      │
│                                                              │
│  4. KNAPSACK DP                                              │
│     - 0/1 Knapsack                                           │
│     - Coin Change                                            │
│     Pattern: dp[i][w] = (items, capacity)                    │
│                                                              │
│  5. INTERVAL DP                                              │
│     - Burst Balloons                                         │
│     - Matrix Chain Multiplication                            │
│     Pattern: dp[i][j] = subproblem from i to j               │
│                                                              │
│  6. TREE DP                                                  │
│     - House Robber III                                       │
│     - Maximum Path Sum in Binary Tree                        │
│     Pattern: dp on tree nodes                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Cognitive Strategy: How Experts Think**

```
┌──────────────────────────────────────────────────────────────┐
│            EXPERT DP THOUGHT PROCESS                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🧠 PHASE 1: PATTERN MATCHING (First 30 seconds)             │
│     "Have I seen something like this before?"                │
│     - Fibonacci pattern? (add last 2)                        │
│     - Choice problem? (take/skip, buy/sell)                  │
│     - Sequence matching? (2 strings/arrays)                  │
│     - Grid traversal? (paths, minimum cost)                  │
│                                                              │
│  🔍 PHASE 2: STATE DEFINITION (Next 1-2 minutes)             │
│     "What information do I need to track?"                   │
│     - Position/index?                                        │
│     - Remaining capacity/budget?                             │
│     - Previous choice?                                       │
│     - Minimum dimensions needed?                             │
│                                                              │
│  ⚡ PHASE 3: TRANSITION LOGIC (Next 2-3 minutes)              │
│     "How do states connect?"                                 │
│     - Draw small example (n=3 or n=4)                        │
│     - Find pattern manually                                  │
│     - Generalize to formula                                  │
│                                                              │
│  ✅ PHASE 4: VALIDATION (Next 1-2 minutes)                   │
│     "Does my logic cover all cases?"                         │
│     - Test on base cases                                     │
│     - Check boundary conditions                              │
│     - Verify with small example                              │
│                                                              │
│  💻 PHASE 5: IMPLEMENTATION (Rest of time)                   │
│     "Code with confidence"                                   │
│     - Start with memoization (easier)                        │
│     - Convert to tabulation if needed                        │
│     - Optimize space if obvious                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Chunking: Building Your DP "Library"**

```
As you solve more problems, these patterns become CHUNKS in your mind:

┌─────────────────────────────────────────────────────────┐
│  BEGINNER (0-10 problems)                               │
│  Sees: "This problem has recursion and subproblems"     │
│  Thinks: "Maybe DP? Let me try memoization..."          │
│  Time: 30-45 minutes per problem                        │
└─────────────────────────────────────────────────────────┘
                        ↓ Practice
┌─────────────────────────────────────────────────────────┐
│  INTERMEDIATE (10-50 problems)                          │
│  Sees: "dp[i] = dp[i-1] + dp[i-2] pattern"              │
│  Thinks: "Fibonacci-like, I know this!"                 │
│  Time: 15-20 minutes per problem                        │
└─────────────────────────────────────────────────────────┘
                        ↓ Practice
┌─────────────────────────────────────────────────────────┐
│  EXPERT (50+ problems)                                  │
│  Sees: Problem statement                                │
│  Thinks: Instantly categorizes (Linear? 2D? Knapsack?)  │
│  Time: 5-10 minutes per problem                         │
│  Has internalized dozens of patterns                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔟 **OPTIMIZATION TECHNIQUES**

### **Space Optimization: The Sliding Window Pattern**

```
OBSERVATION: Many DP solutions only need last k values

Fibonacci: dp[i] = dp[i-1] + dp[i-2]
           └─────────┬─────────┘
                  Only need last 2!

┌──────────────────────────────────────────────────────────┐
│  FROM:  [dp[0], dp[1], dp[2], ..., dp[n]]                │
│         └────────────── O(n) space ──────────────┘       │
│                                                          │
│  TO:    prev2, prev1                                     │
│         └──── O(1) space ────┘                           │
└──────────────────────────────────────────────────────────┘
```

### **Generic Space Optimization Template**

```python
def dp_space_optimized(n):
    """
    Pattern: When dp[i] only depends on last k values
    Keep only those k values in memory
    """
    # For last 2 values (most common)
    if n <= base_case_threshold:
        return handle_base_case(n)
    
    # Initialize window
    prev2 = base_value_1
    prev1 = base_value_2
    
    # Slide window
    for i in range(start, n + 1):
        current = compute(prev1, prev2)
        prev2 = prev1  # Slide
        prev1 = current
    
    return prev1
```

### **Time Optimization: State Space Reduction**

```
Sometimes you can reduce the state space itself!

Example: Coin Change
NAIVE:  dp[i][amount] = min coins using first i coin types
        ↓
OPTIMIZED: dp[amount] = min coins using any coins
           (order of coins doesn't matter!)

STATE SPACE: O(n × amount) → O(amount)
```

---

## 📚 **PRACTICE ROADMAP: FROM BEGINNER TO TOP 1%**

### **Level 1: Foundation (Problems 1-10)**

```
1. Fibonacci Number (the classic)
2. Climbing Stairs
3. Min Cost Climbing Stairs
4. House Robber (cannot rob adjacent)
5. Best Time to Buy/Sell Stock (one transaction)
6. Maximum Subarray (Kadane's algorithm)
7. Decode Ways
8. Unique Paths (grid)
9. Minimum Path Sum (grid)
10. Jump Game

Goal: Master 1D linear DP, understand both approaches
```

### **Level 2: Intermediate (Problems 11-30)**

```
11. Longest Increasing Subsequence
12. Coin Change (unbounded knapsack)
13. Coin Change 2 (count ways)
14. 0/1 Knapsack
15. Partition Equal Subset Sum
16. House Robber II (circular)
17. Decode Ways II
18. Unique Paths II (obstacles)
19. Best Time to Buy/Sell Stock II (multiple transactions)
20. Jump Game II
... (and more)

Goal: Master 2D DP, knapsack patterns, complex transitions
```

### **Level 3: Advanced (Problems 31-60)**

```
31. Longest Common Subsequence (LCS)
32. Edit Distance
33. Longest Palindromic Subsequence
34. Burst Balloons
35. Regular Expression Matching
36. Wildcard Matching
37. Distinct Subsequences
38. Interleaving String
39. Best Time to Buy/Sell Stock III (2 transactions)
40. Best Time to Buy/Sell Stock IV (k transactions)
... (and more)

Goal: Master sequence DP, interval DP, state machine DP
```

### **Deliberate Practice Strategy**

```
┌──────────────────────────────────────────────────────────┐
│           THE MONK'S DP PRACTICE METHOD                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  DAY 1-3: Solve ONE problem                              │
│    - 45 min: Understand deeply                           │
│    - Implement both memo AND tab versions                │
│    - Optimize space if possible                          │
│    - Write detailed comments                             │
│                                                          │
│  DAY 4: Review Day                                       │
│    - Redo 3 problems from scratch (no looking!)          │
│    - Compare your new code to original                   │
│    - Note what improved, what you forgot                 │
│                                                          │
│  DAY 5-7: Repeat cycle with new problems                 │
│                                                          │
│  WEEKLY REVIEW:                                          │
│    - Solve 5 random previous problems (timed: 15 min)    │
│    - Identify weak patterns                              │
│    - Deep dive into those patterns                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 **COMPLETE EXAMPLE: COIN CHANGE PROBLEM**

### **Problem Statement**

You have coins of different denominations and a total amount.
Find the **minimum number** of coins needed to make that amount.
If impossible, return -1.

```
Example:
coins = [1, 2, 5], amount = 11

Answer: 3 coins (5 + 5 + 1)
```

### **Step-by-Step Analysis**

#### **Step 1: Identify DP Properties**

```
✓ Overlapping Subproblems?
  - To make amount=11, we need min_coins(10) or min_coins(9) or min_coins(6)
  - These subproblems repeat in different branches

✓ Optimal Substructure?
  - min_coins(11) = 1 + min(min_coins(10), min_coins(9), min_coins(6))
                        └──────────┬──────────┘
                              optimal subproblems

YES → This is a DP problem!
```

#### **Step 2: Define State**

```
dp[i] = minimum number of coins needed to make amount i

Example: amount = 11
dp[0] = 0    (0 coins for amount 0)
dp[1] = ?
dp[2] = ?
...
dp[11] = ?   (what we want!)
```

#### **Step 3: Recurrence Relation**

```
For each coin c in coins:
  dp[i] = min(dp[i], 1 + dp[i - c])
          └──┬──┘  └────┬────┘
          current   take coin c
          best      + solve remainder

Base case: dp[0] = 0
Invalid: dp[i] = infinity (impossible)
```

#### **Step 4: Visual Example**

```
coins = [1, 2, 5], amount = 11

Build table dp[0...11]:

Initialize:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │11 │
├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
│ 0 │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │ ∞ │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

For i=1, try each coin:
  coin=1: dp[1] = 1 + dp[0] = 1
  coin=2: can't use (2 > 1)
  coin=5: can't use (5 > 1)
  dp[1] = 1

For i=2, try each coin:
  coin=1: dp[2] = 1 + dp[1] = 2
  coin=2: dp[2] = 1 + dp[0] = 1 ✓ better!
  coin=5: can't use
  dp[2] = 1

For i=5, try each coin:
  coin=1: 1 + dp[4] = 1 + 2 = 3
  coin=2: 1 + dp[3] = 1 + 2 = 3
  coin=5: 1 + dp[0] = 1 ✓ best!
  dp[5] = 1

... continue for all amounts ...

Final table:
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │11 │
├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
│ 0 │ 1 │ 1 │ 2 │ 2 │ 1 │ 2 │ 2 │ 3 │ 3 │ 2 │ 3 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
                                                ↑
                                          answer: 3
```

### **Implementation: All Three Approaches**

#### **1. Memoization (Top-Down)**

```python
def coin_change_memo(coins, amount, memo=None):
    """
    Top-Down DP with Memoization
    
    TIME: O(amount × len(coins))
    SPACE: O(amount) for memo + recursion stack
    """
    if memo is None:
        memo = {}
    
    # Base case
    if amount == 0:
        return 0
    if amount < 0:
        return float('inf')  # Impossible
    
    # Check cache
    if amount in memo:
        return memo[amount]
    
    # Try each coin, take minimum
    min_coins = float('inf')
    for coin in coins:
        result = coin_change_memo(coins, amount - coin, memo)
        if result != float('inf'):
            min_coins = min(min_coins, 1 + result)
    
    memo[amount] = min_coins
    return min_coins

def coin_change(coins, amount):
    result = coin_change_memo(coins, amount)
    return result if result != float('inf') else -1
```

#### **2. Tabulation (Bottom-Up)**

```python
def coin_change_tab(coins, amount):
    """
    Bottom-Up DP with Tabulation
    
    TIME: O(amount × len(coins))
    SPACE: O(amount) for dp array
    """
    # Initialize DP table
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case
    
    # Fill table
    for i in range(1, amount + 1):
        # Try each coin
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], 1 + dp[i - coin])
    
    return dp[amount] if dp[amount] != float('inf') else -1
```

#### **3. Rust Version (Tabulation)**

```rust
pub fn coin_change(coins: Vec<i32>, amount: i32) -> i32 {
    let amount = amount as usize;
    let mut dp = vec![i32::MAX; amount + 1];
    dp[0] = 0; // Base case
    
    for i in 1..=amount {
        for &coin in &coins {
            let coin = coin as usize;
            if coin <= i && dp[i - coin] != i32::MAX {
                dp[i] = dp[i].min(1 + dp[i - coin]);
            }
        }
    }
    
    if dp[amount] == i32::MAX {
        -1
    } else {
        dp[amount]
    }
}
```

#### **4. Go Version (Tabulation)**

```go
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    
    // Initialize with "impossible" value
    for i := 1; i <= amount; i++ {
        dp[i] = amount + 1  // More than possible
    }
    dp[0] = 0  // Base case
    
    for i := 1; i <= amount; i++ {
        for _, coin := range coins {
            if coin <= i {
                dp[i] = min(dp[i], 1 + dp[i-coin])
            }
        }
    }
    
    if dp[amount] > amount {
        return -1
    }
    return dp[amount]
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

---

## 🧠 **PSYCHOLOGICAL PRINCIPLES FOR MASTERY**

### **1. Deliberate Practice (Anders Ericsson)**

```
┌──────────────────────────────────────────────────────────┐
│  DELIBERATE PRACTICE FOR DP                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ❌ WRONG: Solve 100 problems superficially              │
│  ✓ RIGHT: Solve 30 problems DEEPLY                       │
│                                                          │
│  For each problem:                                       │
│  1. Solve without looking (struggle = growth)            │
│  2. Implement BOTH memo and tab                          │
│  3. Optimize space                                       │
│  4. Explain to rubber duck (or imaginary student)        │
│  5. Wait 3 days, solve again from scratch                │
│  6. Compare: What did you forget? What improved?         │
│                                                          │
│  The 3-day gap is CRUCIAL for memory consolidation       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### **2. Chunking (Miller's Law)**

```
Your brain can hold 7±2 chunks in working memory.

BEGINNER: Each line of code is a chunk
  → Overwhelmed by dp[i] = dp[i-1] + dp[i-2]

EXPERT: Entire pattern is ONE chunk
  → Instantly recognizes "Fibonacci pattern"

HOW TO BUILD CHUNKS:
  1. Solve similar problems consecutively
  2. Explicitly note patterns: "This is Type X"
  3. Create your own pattern library
  4. Name patterns (e.g., "The Knapsack Pattern")
```

### **3. Mental Models (Charlie Munger)**

```
Build multiple mental models for DP:

MODEL 1: Graph Traversal
  "DP is finding shortest path in a DAG"
  States = nodes, transitions = edges

MODEL 2: Caching
  "DP is smart recursion with a notebook"
  Don't recompute, just look it up!

MODEL 3: State Machine
  "DP tracks all possible states and transitions"
  Each state leads to new states

MODEL 4: Time Series
  "DP builds answer chronologically"
  Past determines present determines future

Having multiple models helps you approach from different angles!
```

### **4. Flow State (Mihály Csíkszentmihályi)**

```
┌──────────────────────────────────────────────────────────┐
│         ACHIEVING FLOW IN DP PRACTICE                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  CONDITIONS FOR FLOW:                                    │
│                                                          │
│  1. Clear goals: "Solve this, implement both ways"       │
│  2. Immediate feedback: Code runs or doesn't             │
│  3. Challenge-skill balance: Not too hard, not too easy  │
│                                                          │
│  FLOW ZONE:                                              │
│     High Challenge                                       │
│          ↑                                               │
│          │        ANXIETY                                │
│          │                                               │
│          │   FLOW  ←  Sweet spot!                        │
│          │                                               │
│          │        BOREDOM                                │
│          └──────────────────→                            │
│              High Skill                                  │
│                                                          │
│  PRACTICE TIP:                                           │
│  If bored → Pick harder problems                         │
│  If anxious → Review fundamentals, pick easier problems  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### **5. Spaced Repetition (Ebbinghaus)**

```
The Forgetting Curve:

Memory
  │ \
  │  \
  │   \___
  │       \____
  │            \____
  └──────────────────→ Time
    1h  1d  3d  7d  30d

STRATEGY:
Day 1: Learn new DP pattern (e.g., Knapsack)
Day 2: Review same problem
Day 4: Solve similar problem (spaced)
Day 7: Solve from scratch (spaced more)
Day 30: Final review

This transforms short-term → long-term memory
```

---

## 🎓 **ADVANCED CONCEPT: STATE COMPRESSION**

Sometimes, you can compress state space using bit manipulation!

### **Example: Traveling Salesman Problem (TSP)**

```
Problem: Visit all cities exactly once, minimize distance

NAIVE STATE: "Which cities visited?" → Use boolean array
  → 2^n possible subsets

OPTIMIZED: Use bitmask!
  visited = 0b10110  → cities 1, 2, 4 visited
  
  dp[mask][city] = min cost to reach 'city' with 'mask' cities visited
```

### **Bitmask DP Template**

```python
def bitmask_dp(n):
    """
    State: dp[mask][i]
    mask = bitmask representing visited set
    i = current position
    """
    dp = [[float('inf')] * n for _ in range(1 << n)]
    
    # Base case: starting position
    dp[1 << start][start] = 0
    
    # Iterate through all masks
    for mask in range(1 << n):
        for i in range(n):
            if not (mask & (1 << i)):  # i not in mask
                continue
            
            # Try transitioning to j
            for j in range(n):
                if mask & (1 << j):  # j already visited
                    continue
                
                new_mask = mask | (1 << j)
                dp[new_mask][j] = min(
                    dp[new_mask][j],
                    dp[mask][i] + cost[i][j]
                )
    
    return min(dp[(1 << n) - 1])  # All cities visited
```

This is **advanced** - don't worry if it's overwhelming now. 
You'll get here after mastering the basics!

---

## 🏆 **YOUR DP MASTERY CHECKLIST**

```
┌──────────────────────────────────────────────────────────┐
│         FROM BEGINNER TO TOP 1% - YOUR PATH              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  LEVEL 1: FOUNDATION (Week 1-2)                          │
│  □ Understand what DP is conceptually                    │
│  □ Implement Fibonacci both ways                         │
│  □ Solve 10 basic 1D problems                            │
│  □ Can explain memoization to a friend                   │
│                                                          │
│  LEVEL 2: COMPETENCE (Week 3-6)                          │
│  □ Recognize Fibonacci-like patterns instantly           │
│  □ Solve 2D grid problems                                │
│  □ Understand knapsack pattern                           │
│  □ Can optimize space in most problems                   │
│  □ Solved 30 problems total                              │
│                                                          │
│  LEVEL 3: PROFICIENCY (Week 7-12)                        │
│  □ Solve LeetCode Medium in 15-20 min                    │
│  □ Master sequence DP (LCS, Edit Distance)               │
│  □ Understand state machine DP                           │
│  □ Can derive recurrence from scratch                    │
│  □ Solved 50 problems total                              │
│                                                          │
│  LEVEL 4: EXPERTISE (Month 4-6)                          │
│  □ Recognize problem type in 30 seconds                  │
│  □ Solve LeetCode Hard systematically                    │
│  □ Know 10+ DP patterns by heart                         │
│  □ Can teach DP to others                                │
│  □ Solved 100+ problems total                            │
│                                                          │
│  LEVEL 5: MASTERY (Month 7-12)                           │
│  □ Top 1% on competitive coding platforms                │
│  □ Can solve novel DP problems in contests               │
│  □ Deep intuition for state design                       │
│  □ Contribute to DP discussions/explanations             │
│  □ DP is second nature                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 **FINAL WISDOM: THE DP MINDSET**

```
┌──────────────────────────────────────────────────────────┐
│              THE MASTER'S MINDSET                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  "Dynamic Programming is not about memorizing            │
│   solutions. It's about training your mind to            │
│   SEE problems differently."                             │
│                                                          │
│  When you see a problem, ask:                            │
│    • Can I break this into smaller versions?             │
│    • Will I solve the same small version multiple times? │
│    • Can I build up from the smallest case?              │
│                                                          │
│  If YES to all three → DP is your weapon.                │
│                                                          │
│  Remember:                                               │
│  - Memoization: "Lazy but clever" (compute when needed)  │
│  - Tabulation: "Organized and efficient" (plan ahead)    │
│                                                          │
│  Both reach the summit. Choose your path wisely.         │
│                                                          │
│  The journey from naive recursion to optimized DP        │
│  mirrors your growth from beginner to master.            │
│                                                          │
│  Trust the process. Stay disciplined. Keep practicing.   │
│                                                          │
│  You're building not just coding skills, but a new       │
│  way of thinking that will serve you for life.           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📝 **SUMMARY: THE CORE DIFFERENCES**

```
╔══════════════════════════════════════════════════════════╗
║           MEMOIZATION vs TABULATION                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  MEMOIZATION (Top-Down)      TABULATION (Bottom-Up)      ║
║  ═══════════════════          ═══════════════════        ║
║                                                          ║
║  Recursive                    Iterative                  ║
║  Cache (dict/map)            Table (array)               ║
║  Solve big → small           Solve small → big           ║
║  Lazy evaluation             Eager evaluation            ║
║  Natural to write            Requires planning           ║
║  O(n) space + stack          O(n) or O(1) space          ║
║  Risk stack overflow         No stack risk               ║
║  Slightly slower             Slightly faster             ║
║                                                          ║
║  WHEN TO USE:                WHEN TO USE:                ║
║  • Complex dependencies      • Clear order exists        ║
║  • Not all sub-problems      • Need all values           ║
║    needed                    • Want max performance      ║
║  • Quick to implement        • Space optimization        ║
║                                                          ║
║  BOTH solve same problems! Choose based on situation.    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

**You now have the complete foundation for Dynamic Programming mastery.** 

This isn't just a guide - it's your training manual for the next 6-12 months. 

**Print it. Study it. Live it.**

Start with Fibonacci. Master it both ways. Then climb the ladder, one problem at a time.

**Remember:** The gap between knowing about DP and MASTERING DP is filled with deliberate practice. Every top 1% coder walked this same path.

**Your journey to DP enlightenment begins now.** 🚀⚡

# Dynamic Programming: The Mental Framework

Most people struggle with DP not because of the code — but because they don't have a **systematic way to think about it**. Let me fix that.

---

## The Core Insight

> DP = "I've solved smaller versions of this problem. Can I use those answers to build the bigger answer?"

**Analogy:** You're climbing stairs. You don't need to figure out how to climb all 100 stairs at once. You just need to know: *"If I'm at stair N, I got here from stair N-1 or N-2."* That recurrence IS the DP.

---

## The 5-Step Framework (Apply to Every DP Problem)

```
1. IDENTIFY   → Is this even a DP problem?
2. STATE      → What are my "variables" that define a subproblem?
3. TRANSITION → How do I go from smaller to bigger? (The recurrence)
4. BASE CASE  → Where does the recursion bottom out?
5. DIRECTION  → Top-down (memo) or Bottom-up (table)?
```

---

## Step 1: Is it DP?

Ask yourself two questions:

```
✓ Overlapping subproblems?  → Same sub-calculation appears multiple times
✓ Optimal substructure?     → Optimal answer is built from optimal sub-answers
```

**Signal words in problem statements:**
- "minimum/maximum"
- "number of ways"
- "can you reach / is it possible"
- "longest / shortest"
- "count distinct"

---

## Step 2: Define the STATE

This is where 90% of people get stuck. The state is what you need to **fully describe** a subproblem.

```go
// Ask: "dp[?] means what exactly?"
//
// Fibonacci:  dp[i] = the i-th fibonacci number
// Knapsack:   dp[i][w] = max value using first i items, with weight limit w
// LCS:        dp[i][j] = length of LCS of first i chars of A, first j chars of B
// Coin Change:dp[i] = min coins needed to make amount i
```

**Rule of thumb:** If the problem has one "dimension" (index, amount), your state is 1D. If it has two "things changing" (two sequences, index + remaining capacity), your state is 2D.

---

## Step 3: Write the TRANSITION

This is the heart of DP. It's always: **"dp[i] depends on dp[something smaller]"**

```go
// Fibonacci
dp[i] = dp[i-1] + dp[i-2]

// Coin Change (min coins for amount i)
dp[i] = min(dp[i - coin] + 1) for each coin

// 0/1 Knapsack
// Either take item i, or don't
dp[i][w] = max(dp[i-1][w], dp[i-1][w-weight[i]] + value[i])

// Longest Common Subsequence
if A[i] == B[j]:
    dp[i][j] = dp[i-1][j-1] + 1
else:
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

---

## The 4 Core DP Patterns (Covers ~80% of Problems)

### Pattern 1: Linear DP — "Looking back a few steps"

```go
// Template: dp[i] depends on dp[i-1], dp[i-2], ...
// Problems: Fibonacci, Climbing Stairs, House Robber, Jump Game

// House Robber: can't rob adjacent houses, maximize money
// STATE: dp[i] = max money robbing from houses 0..i
// TRANSITION: rob house i, or skip it
func rob(nums []int) int {
    n := len(nums)
    if n == 1 {
        return nums[0]
    }

    dp := make([]int, n)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])

    for i := 2; i < n; i++ {
        dp[i] = max(dp[i-1], dp[i-2]+nums[i]) // skip i, OR rob i
    }
    return dp[n-1]
}
```

### Pattern 2: Knapsack — "Take it or leave it"

```go
// Template: dp[i][w] = best answer using first i items with constraint w
// Problems: 0/1 Knapsack, Subset Sum, Partition Equal Subset

// Subset Sum: can we pick numbers that sum to target?
// STATE: dp[i][s] = can we reach sum s using first i numbers?
// TRANSITION: use nums[i], or don't
func canPartition(nums []int) bool {
    total := 0
    for _, n := range nums {
        total += n
    }
    if total%2 != 0 {
        return false
    }
    target := total / 2
    n := len(nums)

    // dp[i][s] = true if sum s is reachable using first i elements
    dp := make([][]bool, n+1)
    for i := range dp {
        dp[i] = make([]bool, target+1)
        dp[i][0] = true // sum=0 always reachable (pick nothing)
    }

    for i := 1; i <= n; i++ {
        for s := 0; s <= target; s++ {
            dp[i][s] = dp[i-1][s] // don't take nums[i-1]
            if s >= nums[i-1] {
                dp[i][s] = dp[i][s] || dp[i-1][s-nums[i-1]] // take it
            }
        }
    }
    return dp[n][target]
}
```

### Pattern 3: Two-Sequence DP — "Comparing two strings/arrays"

```go
// Template: dp[i][j] = answer for first i elements of A, first j of B
// Problems: LCS, Edit Distance, Longest Common Substring

// Edit Distance: min operations to convert word1 → word2
// TRANSITION:
//   if chars match: dp[i][j] = dp[i-1][j-1]
//   else: min of insert, delete, replace
func minDistance(word1 string, word2 string) int {
    m, n := len(word1), len(word2)

    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }

    // Base cases: converting to/from empty string
    for i := 0; i <= m; i++ { dp[i][0] = i } // delete all of word1
    for j := 0; j <= n; j++ { dp[0][j] = j } // insert all of word2

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1] // chars match, no cost
            } else {
                dp[i][j] = 1 + min3(
                    dp[i-1][j],   // delete from word1
                    dp[i][j-1],   // insert into word1
                    dp[i-1][j-1], // replace
                )
            }
        }
    }
    return dp[m][n]
}
```

### Pattern 4: Interval DP — "Best way to split a range"

```go
// Template: dp[i][j] = answer for subarray from i to j
// Problems: Matrix Chain Multiplication, Burst Balloons, Palindrome Partitioning

// Minimum cost to multiply a chain of matrices
// dp[i][j] = min multiplications for matrices i..j
func matrixChainOrder(p []int) int {
    n := len(p) - 1
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
    }

    // length of chain
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            dp[i][j] = 1<<31 - 1
            // try every split point k
            for k := i; k < j; k++ {
                cost := dp[i][k] + dp[k+1][j] + p[i]*p[k+1]*p[j+1]
                if cost < dp[i][j] {
                    dp[i][j] = cost
                }
            }
        }
    }
    return dp[0][n-1]
}
```

---

## The Decision Flowchart

```
Problem arrives
      │
      ▼
Single sequence/value?
 ├─ YES → 1D DP (Linear / Knapsack)
 │         ├─ "take or skip"? → Knapsack pattern
 │         └─ "look back k steps"? → Linear pattern
 └─ NO
      │
Two sequences?
 ├─ YES → 2D DP (Two-sequence pattern)
 └─ NO
      │
Range/interval problem?
 └─ YES → Interval DP (split at every point)
```

---

## Space Optimization (Almost Always Possible)

Once your 2D table works, notice most problems only look back **one row**:

```go
// Knapsack: O(n*W) space → O(W) space
// Instead of dp[i][w], just dp[w], iterate backwards

func knapsack(weights, values []int, W int) int {
    dp := make([]int, W+1)

    for i := range weights {
        // BACKWARDS to prevent using item twice
        for w := W; w >= weights[i]; w-- {
            if val := dp[w-weights[i]] + values[i]; val > dp[w] {
                dp[w] = val
            }
        }
    }
    return dp[W]
}
```

---

## Top-Down vs Bottom-Up

| | Top-Down (Memoization) | Bottom-Up (Tabulation) |
|---|---|---|
| **Code style** | Recursive + cache map | Iterative + array |
| **When to use** | State space is sparse | State space is dense |
| **Pitfall** | Stack overflow on large n | Must figure out fill order |
| **Easier for** | 2D/3D problems | Linear problems |

---

## Your Exercises

1. **Climbing Stairs** → identical structure to Fibonacci. Add a twist: you can take 1, 2, or 3 steps. Modify the transition.

2. **Coin Change** → given coins `[1,5,10,25]` and amount `N`, find minimum coins. State: `dp[i]` = min coins for amount `i`. Transition: `dp[i] = min(dp[i - coin] + 1)` for each coin.

3. **Longest Increasing Subsequence** → `dp[i]` = length of LIS ending at index `i`. For each `j < i`, if `nums[j] < nums[i]`, then `dp[i] = max(dp[i], dp[j] + 1)`.

Solve each of these by **writing the state definition and transition first** before any code. That discipline is what separates people who "get" DP from those who just memorize solutions.

---

**Further reading:**
- 📖 *"Dynamic Programming for Coding Interviews"* — Meenakshi & Kamal Rawat (very pattern-focused)
- 🔗 [neetcode.io DP playlist](https://neetcode.io) — problems grouped by exact patterns above

## "If I'm at stair N, I got here from stair N-1 or N-2"

---

## ASCII Diagram — 5 Stairs

```
STAIR:    [0]   [1]   [2]   [3]   [4]   [5]
           │     │     │     │     │     │
           ▼     ▼     ▼     ▼     ▼     ▼
          GROUND  1     2     3     4    GOAL

You are at stair 5.
How did you get here?

Option A: You were at stair 4, took 1 step
          [4] ──(+1)──► [5]

Option B: You were at stair 3, took 2 steps
          [3] ──(+2)──► [5]

So:  ways(5) = ways(4) + ways(3)
```

```
Visualizing ALL paths for n=4:

START
  │
  ├─ 1 ─► 2 ─► 3 ─► 4       (1+1+1+1)
  │
  ├─ 1 ─► 2 ─► 4             (1+1+2)
  │
  ├─ 1 ─► 3 ─► 4             (1+2+1)
  │
  ├─ 2 ─► 3 ─► 4             (2+1+1)
  │
  └─ 2 ─► 4                  (2+2)

Total = 5 ways
```

---

## Simulation Table — n = 6

At every stair, ask: **"from where could I have arrived here?"**

```
┌───────┬──────────────────────────────────────────┬────────────┐
│ Stair │ Arrived from                             │  ways[i]   │
├───────┼──────────────────────────────────────────┼────────────┤
│   0   │ Base case (ground, you start here)       │     1      │
│   1   │ Only from stair 0 (+1 step)              │     1      │
│   2   │ From stair 1 (+1)  OR  stair 0 (+2)      │   1+1 = 2  │
│   3   │ From stair 2 (+1)  OR  stair 1 (+2)      │   2+1 = 3  │
│   4   │ From stair 3 (+1)  OR  stair 2 (+2)      │   3+2 = 5  │
│   5   │ From stair 4 (+1)  OR  stair 3 (+2)      │   5+3 = 8  │
│   6   │ From stair 5 (+1)  OR  stair 4 (+2)      │   8+5 = 13 │
└───────┴──────────────────────────────────────────┴────────────┘

Recurrence:  ways[i] = ways[i-1] + ways[i-2]
```

---

## The Key Mental Shift

```
WRONG way to think:
  "How do I GET to stair 5?"   ← forward thinking, hard to formulate

RIGHT way to think:
  "I AM at stair 5.
   Which stair was I JUST at?" ← backward thinking, always 2 choices
        │
        ├── I was at N-1  (took 1 step)
        └── I was at N-2  (took 2 steps)

This backward question IS the recurrence relation.
Apply this to EVERY DP problem:

  "I am at state X. Which smaller state did I come from?"
```

---

## 3-Step Twist: Take 1, 2, or 3 Steps

The moment you add a third choice, the table just gains one more column:

```
┌───────┬────────────────────────────────────────────────────┬────────────┐
│ Stair │ Arrived from                                       │  ways[i]   │
├───────┼────────────────────────────────────────────────────┼────────────┤
│   0   │ Base case                                          │     1      │
│   1   │ From 0                                             │     1      │
│   2   │ From 1 (+1)  OR  from 0 (+2)                       │   1+1 = 2  │
│   3   │ From 2 (+1)  OR  from 1 (+2)  OR  from 0 (+3)      │  2+1+1 = 4 │
│   4   │ From 3 (+1)  OR  from 2 (+2)  OR  from 1 (+3)      │  4+2+1 = 7 │
│   5   │ From 4 (+1)  OR  from 3 (+2)  OR  from 2 (+3)      │  7+4+2 = 13│
└───────┴────────────────────────────────────────────────────┴────────────┘

Recurrence:  ways[i] = ways[i-1] + ways[i-2] + ways[i-3]
Code change: ONE extra term. That's it.
```

```go
for i := 3; i <= n; i++ {
    dp[i] = dp[i-1] + dp[i-2] + dp[i-3]  // ← just add the new "from" case
}
```

**This is exactly how you extend ANY DP — change the question "where could I have come from", and the recurrence writes itself.**

## The Mental Model: From "Solve It" to "Split It"

---

## The Core Shift in Thinking

```
NORMAL brain:          "How do I solve the WHOLE problem?"
DP brain:              "How do I solve it for ONE element,
                        assuming everything smaller is ALREADY solved?"

That assumption — "already solved" — is the entire trick.
```

---

## The 3-Question Method (Apply in Order)

```
┌─────────────────────────────────────────────────────┐
│  Q1: "What is the LAST thing that happens           │
│        before I reach the answer?"                  │
│                                                     │
│  Q2: "What choices did I have at that last step?"  │
│                                                     │
│  Q3: "If I knew the answer to each choice,         │
│        how do I COMBINE them?"                      │
└─────────────────────────────────────────────────────┘
```

This is not intuition. It is a **mechanical process**. Let me show you.

---

## Live Walkthrough — 3 Problems, Same Mental Process

---

### Problem 1: Climbing Stairs

```
Plain English problem:
  "Count ways to reach stair N, taking 1 or 2 steps at a time"

───────────────────────────────────────────────
Q1: What is the LAST thing that happens?
    → The very last step I take to land on stair N

Q2: What choices did I have at that last step?
    → I took 1 step  (came from N-1)
    → I took 2 steps (came from N-2)

Q3: How do I combine them?
    → Total ways = ways from (N-1) + ways from (N-2)
───────────────────────────────────────────────

Recurrence writes itself:
    dp[n] = dp[n-1] + dp[n-2]
```

---

### Problem 2: Coin Change (minimum coins for amount N)

```
Plain English:
  "Given coins [1, 5, 10], find minimum coins to make amount N"

───────────────────────────────────────────────
Q1: What is the LAST thing that happens?
    → I place one final coin to complete amount N

Q2: What choices did I have for that final coin?
    → I placed coin 1  (previous amount was N-1)
    → I placed coin 5  (previous amount was N-5)
    → I placed coin 10 (previous amount was N-10)

Q3: How do I combine them?
    → I want MINIMUM, so:
    → dp[N] = min(dp[N-1], dp[N-5], dp[N-10]) + 1
                                                 ↑
                                    that final coin I placed
───────────────────────────────────────────────

Recurrence:
    dp[n] = min(dp[n - coin] + 1) for each coin
```

---

### Problem 3: Longest Increasing Subsequence (LIS)

```
Plain English:
  "Given [3, 1, 8, 2, 5], find length of longest increasing subsequence"

This feels harder. Same 3 questions.

───────────────────────────────────────────────
Q1: What is the LAST thing that happens?
    → The sequence ENDS at some element.
      Pick any index i as "the last element of my LIS"

Q2: What choices did I have before that last element?
    → Any index j < i where nums[j] < nums[i]
      (because the sequence must be increasing)

Q3: How do I combine?
    → I want LONGEST, so:
    → dp[i] = max(dp[j] + 1) for all j < i where nums[j] < nums[i]
                          ↑
                  extend that subsequence by 1 (adding nums[i])
───────────────────────────────────────────────

Recurrence:
    dp[i] = max(dp[j] + 1)  for all valid j
```

---

## The Pattern You Just Saw

```
Every single problem followed the same skeleton:

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  dp[i] = COMBINE( dp[smaller] + cost_of_last_decision )     │
│                                                              │
│  COMBINE is:                                                 │
│    → "count ways"  problem   →  SUM  all choices            │
│    → "minimum"     problem   →  MIN  all choices             │
│    → "maximum"     problem   →  MAX  all choices             │
│    → "is possible" problem   →  OR   all choices             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## The Full Mental Process as a Flowchart

```
Read the problem
      │
      ▼
Step 1: RESTATE in one line
  "Find X for input of size N"
      │
      ▼
Step 2: SHRINK the problem by 1
  "What if I already knew the answer for N-1?"
  "Can I use that to get answer for N?"
      │
      ├── YES → You have a recurrence. Write it.
      └── NO  → Your "state" is wrong. Add another variable.
                (e.g., move from dp[i] to dp[i][j])
      │
      ▼
Step 3: IDENTIFY the last decision
  "What is the last choice made before reaching state N?"
  List ALL options for that choice.
      │
      ▼
Step 4: WRITE the recurrence
  dp[N] = COMBINE over all choices of dp[smaller state]
      │
      ▼
Step 5: BASE CASES
  "What is the smallest N where the answer is obvious?"
  Hard-code those.
      │
      ▼
Step 6: FILL ORDER
  Bottom-up: fill small → large (loop)
  Top-down:  fill on demand (recursion + memo)
```

---

## The "Shrink by 1" Practice Drill

This is the single most important habit to build. Take any problem and ask:

```
"Suppose I have the answer for N-1.
 Now element N arrives.
 What do I do with it?"

Problem: Max subarray sum
  → "I know best sum ending at index N-1.
     Element N arrives.
     Do I EXTEND that subarray, or START fresh from N?"
  → dp[i] = max(dp[i-1] + nums[i],  nums[i])
                 ↑ extend              ↑ restart

Problem: House Robber
  → "I know max money from houses 0..N-1.
     House N arrives.
     Do I ROB it (skip N-1) or SKIP it?"
  → dp[i] = max(dp[i-2] + nums[i],  dp[i-1])
                 ↑ rob N               ↑ skip N

Problem: Unique Paths in Grid
  → "I know ways to reach cell (i-1,j) and (i,j-1).
     Cell (i,j) arrives.
     I could have come from TOP or from LEFT."
  → dp[i][j] = dp[i-1][j] + dp[i][j-1]
```

See what's happening? The problem **tells you** the subproblems once you ask the right question.

---

## When 1D Fails: Add a Dimension

```
If you cannot express the problem with dp[i] alone,
it means your state is MISSING information.

Signal: "My transition doesn't know enough to decide"

Fix: Add another variable to the state.

Example:
  "0/1 Knapsack — max value, weight limit W"

  Try dp[i]:
    → "best value using first i items"
    → Transition: take item i, or don't
    → PROBLEM: If I take item i, I need to know remaining weight.
                dp[i] alone doesn't track that.

  Fix → dp[i][w]:
    → "best value using first i items WITH weight limit w"
    → Now I know everything I need.
    → dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt[i]] + val[i])
                      ↑ skip i        ↑ take i (weight reduces)
```

---

## One Rule to Remember

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Your STATE must contain exactly enough information │
│  to make the next decision WITHOUT looking at       │
│  anything you've already passed.                    │
│                                                     │
│  Too little info → add a dimension                  │
│  Right info      → recurrence is clean              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Your Practice Protocol

Do these 5 problems **in this exact order**. Write the 3 questions on paper before touching code:

```
1. Coin Change          → min/max + single sequence
2. House Robber         → skip/take + single sequence  
3. Unique Paths         → grid, 2D state is obvious
4. Subset Sum           → take/skip + target constraint → 2D
5. Longest Common Sub.  → two sequences → 2D, Q1 is tricky
```

For each one, before writing a single line of Go:

```
Write on paper:
  Q1: "Last thing that happens is ___________"
  Q2: "My choices at that last step are ______"
  Q3: "I combine them with min/max/sum because ___"
  STATE: "dp[i] means ___________"
  BASE:  "dp[0] = ___ because ___"
```

Once that paper is filled out, the code is just transcription.