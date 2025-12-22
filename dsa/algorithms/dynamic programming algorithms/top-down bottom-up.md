# Dynamic Programming: Complete Mastery Guide
*From Fundamentals to Top 1% Problem-Solving*

---

## Table of Contents
1. [Core Philosophy & Mental Models](#core-philosophy)
2. [The Mathematics of Optimal Substructure](#mathematics)
3. [Top-Down vs Bottom-Up: Deep Dive](#approaches)
4. [The Universal DP Framework](#framework)
5. [Visual Problem-Solving Maps](#visual-maps)
6. [Classic Patterns with Multi-Language Implementations](#patterns)
7. [Advanced Techniques](#advanced)
8. [Deliberate Practice Strategy](#practice)

---

## 1. Core Philosophy & Mental Models {#core-philosophy}

### The Essence of Dynamic Programming

**DP is not about memorization—it's about seeing recursive structure in optimization problems.**

```
The DP Mindset Transformation:

Novice:  "I need to remember this recurrence relation"
         ↓
Expert:  "I see overlapping decisions creating a DAG of states"
         ↓
Master:  "I intuitively recognize the invariants that define 
          the state space and transition function"
```

### Three Pillars of DP Mastery

1. **Optimal Substructure**: The optimal solution contains optimal solutions to subproblems
2. **Overlapping Subproblems**: Same subproblems are solved repeatedly
3. **Memoization/Tabulation**: Avoid redundant computation by caching results

### The Cognitive Model

```
Problem Recognition → State Definition → Transition Logic → Implementation
        ↓                    ↓                  ↓                ↓
   Pattern match      What changes?      How do states     Choose top-down
   (Fibonacci,        What's minimal     relate? What's    vs bottom-up
   knapsack, LCS,     info needed to     the recurrence?   based on problem
   paths, etc.)       compute answer?                      structure
```

---

## 2. The Mathematics of Optimal Substructure {#mathematics}

### Bellman Equation (The Foundation)

For any optimization problem with optimal substructure:

```
V(s) = max/min { r(s,a) + V(s') } for all actions a
       
Where:
  V(s)   = Value/optimal solution at state s
  r(s,a) = Immediate reward/cost for action a in state s
  s'     = Next state after taking action a
```

### Why This Matters

This equation captures the essence of **every** DP problem:
- The best solution at state `s` depends on making the best immediate choice
- Plus the best solution to the resulting subproblem
- The "action" might be: skip/take, go left/right, use/don't use, etc.

### State Space as a DAG

```
DP problems always form a Directed Acyclic Graph:

    Start State(s)
         ↓
    [State Layer 1] ← These are your subproblems
         ↓
    [State Layer 2]
         ↓
    [State Layer 3]
         ↓
    Goal State(s)

Property: No cycles means we can solve in topological order
```

---

## 3. Top-Down vs Bottom-Up: Deep Dive {#approaches}

### Conceptual Comparison

```
TOP-DOWN (Memoization)          BOTTOM-UP (Tabulation)
━━━━━━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━━━━━━
Start: Problem                  Start: Base cases
Direction: Break down           Direction: Build up
Style: Recursive                Style: Iterative
Compute: On-demand              Compute: All states
Call Stack: O(depth)            Call Stack: O(1)
Intuition: Natural              Intuition: Requires thought
```

### Execution Flow Visualization

```
Problem: Fibonacci(5)

TOP-DOWN (Memoization):
                    fib(5)
                   /      \
              fib(4)      fib(3)
             /     \      /     \
        fib(3)  fib(2) fib(2) fib(1)
       /    \    [HIT]  [HIT]  [BASE]
   fib(2) fib(1) 
   [CALC] [BASE]

Calls: fib(5)→fib(4)→fib(3)→fib(2)→fib(1)→fib(0)
       Cache hits prevent redundant subtree exploration


BOTTOM-UP (Tabulation):
   
   Index:  0   1   2   3   4   5
           ↓   ↓   ↓   ↓   ↓   ↓
   Array: [0] [1] [1] [2] [3] [5]
           ↑       ↑___↑___↑
           |       Build from previous states
           Base cases

Compute: Linear iteration, no recursion overhead
```

### When to Choose Each Approach

**Choose Top-Down (Memoization) when:**
- State space is sparse (won't compute all states)
- Problem naturally expressed recursively
- Transition logic is complex or has many branches
- You need to solve only specific states (e.g., paths in a graph)

**Choose Bottom-Up (Tabulation) when:**
- All/most states will be computed anyway
- You want O(1) space optimization (e.g., sliding window)
- Avoiding recursion overhead is critical
- Order of state computation is obvious

---

## 4. The Universal DP Framework {#framework}

### The 5-Step Problem-Solving Protocol

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: IDENTIFY THE DECISION SEQUENCE                 │
│  "What choices do I make at each step?"                  │
│  Example: Knapsack → "Include item i or skip it?"       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: DEFINE THE STATE                               │
│  "What minimal info do I need to make optimal decision?" │
│  State = f(decision point, relevant constraints)         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: ESTABLISH BASE CASES                           │
│  "What are the trivial/boundary cases I know?"           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 4: DERIVE THE RECURRENCE RELATION                 │
│  "How does optimal(state) depend on smaller states?"     │
│  Apply Bellman principle                                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 5: DETERMINE COMPUTATION ORDER                    │
│  "What order ensures subproblems are solved first?"      │
│  (Only for bottom-up)                                    │
└─────────────────────────────────────────────────────────┘
```

### Example: Applying the Framework to Classic Problems

#### Problem 1: Fibonacci Sequence

```
Step 1 (Decision): "Should I use fib(n-1) or fib(n-2)?" 
                   → Actually no decision, just decomposition

Step 2 (State): dp[i] = i-th Fibonacci number

Step 3 (Base): dp[0] = 0, dp[1] = 1

Step 4 (Recurrence): dp[i] = dp[i-1] + dp[i-2]

Step 5 (Order): i from 2 to n (increasing)
```

#### Problem 2: 0/1 Knapsack

```
Step 1 (Decision): "Include item i or skip it?"

Step 2 (State): dp[i][w] = max value using items 0..i with capacity w

Step 3 (Base): dp[0][w] = 0 for all w (no items)
               dp[i][0] = 0 for all i (no capacity)

Step 4 (Recurrence): 
   if weight[i] > w:
       dp[i][w] = dp[i-1][w]  # Can't include
   else:
       dp[i][w] = max(
           dp[i-1][w],              # Skip item i
           dp[i-1][w-weight[i]] + value[i]  # Include item i
       )

Step 5 (Order): i from 1 to n, w from 1 to capacity
```

---

## 5. Visual Problem-Solving Maps {#visual-maps}

### DP Problem Classification Tree

```
                    DP Problems
                         |
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Sequential        Grid-Based      String-Based
   Decisions         Problems        Problems
        |                |                |
   ┌────┴────┐      ┌───┴───┐       ┌───┴────┐
   ↓         ↓      ↓       ↓       ↓        ↓
Fibonacci  Knapsack Paths  Matrix  LCS    Edit Dist
Climbing   Coin     Min    Max     Palin  Wildcards
Stairs     Change   Path   Sub     -drome
House      Subset   Sum    Square
Robber     Sum
```

### State Transition Patterns

#### Linear Sequence Pattern
```
State depends on previous k states:

dp[i] ← dp[i-1], dp[i-2], ..., dp[i-k]

Example: Fibonacci, Climbing Stairs, House Robber

    [i-2] ──┐
    [i-1] ──┼──→ [i]
    [i-k] ──┘
```

#### Grid Path Pattern
```
State depends on neighbors:

dp[i][j] ← dp[i-1][j], dp[i][j-1], dp[i-1][j-1]

Example: Unique Paths, Min Path Sum, Edit Distance

    [i-1,j-1]  [i-1,j]
         ↓        ↓
    [i,j-1]  →  [i,j]
```

#### Partition Pattern
```
State depends on all previous partitions:

dp[i] ← max/min over all j < i { dp[j] + cost(j,i) }

Example: Palindrome Partitioning, Decode Ways

    dp[0] ──┐
    dp[1] ──┤
    dp[2] ──┼──→ dp[i]
     ...    │
    dp[i-1]─┘
```

---

## 6. Classic Patterns with Multi-Language Implementations {#patterns}

### Pattern 1: Fibonacci (Warm-Up)

**Time Complexity:** 
- Naive Recursive: O(2^n)
- Top-Down DP: O(n)
- Bottom-Up DP: O(n)
- Space-Optimized: O(1)

#### Rust Implementation

```rust
// Top-Down with Memoization
fn fib_memo(n: usize, memo: &mut Vec<Option<u64>>) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    if let Some(result) = memo[n] {
        return result;
    }
    
    let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    memo[n] = Some(result);
    result
}

pub fn fibonacci_top_down(n: usize) -> u64 {
    let mut memo = vec![None; n + 1];
    fib_memo(n, &mut memo)
}

// Bottom-Up Tabulation
pub fn fibonacci_bottom_up(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let mut dp = vec![0u64; n + 1];
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n]
}

// Space-Optimized O(1)
pub fn fibonacci_optimized(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let (mut prev2, mut prev1) = (0u64, 1u64);
    
    for _ in 2..=n {
        let curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    
    prev1
}
```

#### Python Implementation

```python
from typing import List, Optional

# Top-Down with Memoization
def fib_memo(n: int, memo: List[Optional[int]]) -> int:
    if n <= 1:
        return n
    
    if memo[n] is not None:
        return memo[n]
    
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]

def fibonacci_top_down(n: int) -> int:
    memo = [None] * (n + 1)
    return fib_memo(n, memo)

# Bottom-Up Tabulation
def fibonacci_bottom_up(n: int) -> int:
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

# Space-Optimized
def fibonacci_optimized(n: int) -> int:
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for _ in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1
```

#### Go Implementation

```go
package dp

// Top-Down with Memoization
func fibMemo(n int, memo []int) int {
    if n <= 1 {
        return n
    }
    
    if memo[n] != -1 {
        return memo[n]
    }
    
    memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo)
    return memo[n]
}

func FibonacciTopDown(n int) int {
    memo := make([]int, n+1)
    for i := range memo {
        memo[i] = -1
    }
    return fibMemo(n, memo)
}

// Bottom-Up Tabulation
func FibonacciBottomUp(n int) int {
    if n <= 1 {
        return n
    }
    
    dp := make([]int, n+1)
    dp[1] = 1
    
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    
    return dp[n]
}

// Space-Optimized
func FibonacciOptimized(n int) int {
    if n <= 1 {
        return n
    }
    
    prev2, prev1 := 0, 1
    
    for i := 2; i <= n; i++ {
        curr := prev1 + prev2
        prev2, prev1 = prev1, curr
    }
    
    return prev1
}
```

#### C Implementation

```c
#include <stdlib.h>
#include <string.h>

// Top-Down with Memoization
long long fib_memo(int n, long long *memo) {
    if (n <= 1) {
        return n;
    }
    
    if (memo[n] != -1) {
        return memo[n];
    }
    
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    return memo[n];
}

long long fibonacci_top_down(int n) {
    long long *memo = (long long *)malloc((n + 1) * sizeof(long long));
    for (int i = 0; i <= n; i++) {
        memo[i] = -1;
    }
    
    long long result = fib_memo(n, memo);
    free(memo);
    return result;
}

// Bottom-Up Tabulation
long long fibonacci_bottom_up(int n) {
    if (n <= 1) {
        return n;
    }
    
    long long *dp = (long long *)calloc(n + 1, sizeof(long long));
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    long long result = dp[n];
    free(dp);
    return result;
}

// Space-Optimized
long long fibonacci_optimized(int n) {
    if (n <= 1) {
        return n;
    }
    
    long long prev2 = 0, prev1 = 1;
    
    for (int i = 2; i <= n; i++) {
        long long curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    
    return prev1;
}
```

#### C++ Implementation

```cpp
#include <vector>
#include <optional>

// Top-Down with Memoization
long long fibMemo(int n, std::vector<std::optional<long long>>& memo) {
    if (n <= 1) {
        return n;
    }
    
    if (memo[n].has_value()) {
        return memo[n].value();
    }
    
    long long result = fibMemo(n - 1, memo) + fibMemo(n - 2, memo);
    memo[n] = result;
    return result;
}

long long fibonacciTopDown(int n) {
    std::vector<std::optional<long long>> memo(n + 1);
    return fibMemo(n, memo);
}

// Bottom-Up Tabulation
long long fibonacciBottomUp(int n) {
    if (n <= 1) {
        return n;
    }
    
    std::vector<long long> dp(n + 1, 0);
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    return dp[n];
}

// Space-Optimized
long long fibonacciOptimized(int n) {
    if (n <= 1) {
        return n;
    }
    
    long long prev2 = 0, prev1 = 1;
    
    for (int i = 2; i <= n; i++) {
        long long curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    
    return prev1;
}
```

---

### Pattern 2: 0/1 Knapsack (Choice at Each Step)

**Problem:** Given weights and values of n items, put items in a knapsack of capacity W to maximize total value.

**State:** `dp[i][w]` = maximum value using items 0..i-1 with capacity w

**Recurrence:**
```
dp[i][w] = max(
    dp[i-1][w],                          // Don't take item i
    dp[i-1][w - weight[i]] + value[i]    // Take item i
)
```

**Time:** O(n × W), **Space:** O(n × W) → Can optimize to O(W)

#### Rust Implementation

```rust
// Top-Down with Memoization
fn knapsack_memo(
    items: &[(usize, usize)],  // (weight, value)
    capacity: usize,
    idx: usize,
    memo: &mut Vec<Vec<Option<usize>>>,
) -> usize {
    if idx == 0 || capacity == 0 {
        return 0;
    }
    
    if let Some(result) = memo[idx][capacity] {
        return result;
    }
    
    let (weight, value) = items[idx - 1];
    
    let result = if weight > capacity {
        knapsack_memo(items, capacity, idx - 1, memo)
    } else {
        std::cmp::max(
            knapsack_memo(items, capacity, idx - 1, memo),
            knapsack_memo(items, capacity - weight, idx - 1, memo) + value,
        )
    };
    
    memo[idx][capacity] = Some(result);
    result
}

pub fn knapsack_top_down(items: &[(usize, usize)], capacity: usize) -> usize {
    let n = items.len();
    let mut memo = vec![vec![None; capacity + 1]; n + 1];
    knapsack_memo(items, capacity, n, &mut memo)
}

// Bottom-Up Tabulation
pub fn knapsack_bottom_up(items: &[(usize, usize)], capacity: usize) -> usize {
    let n = items.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    for i in 1..=n {
        let (weight, value) = items[i - 1];
        for w in 0..=capacity {
            dp[i][w] = if weight > w {
                dp[i - 1][w]
            } else {
                std::cmp::max(dp[i - 1][w], dp[i - 1][w - weight] + value)
            };
        }
    }
    
    dp[n][capacity]
}

// Space-Optimized O(W)
pub fn knapsack_optimized(items: &[(usize, usize)], capacity: usize) -> usize {
    let mut dp = vec![0; capacity + 1];
    
    for (weight, value) in items {
        // Traverse backwards to avoid using updated values
        for w in (*weight..=capacity).rev() {
            dp[w] = std::cmp::max(dp[w], dp[w - weight] + value);
        }
    }
    
    dp[capacity]
}
```

#### Python Implementation

```python
from typing import List, Tuple, Optional

# Top-Down with Memoization
def knapsack_memo(
    items: List[Tuple[int, int]],
    capacity: int,
    idx: int,
    memo: List[List[Optional[int]]]
) -> int:
    if idx == 0 or capacity == 0:
        return 0
    
    if memo[idx][capacity] is not None:
        return memo[idx][capacity]
    
    weight, value = items[idx - 1]
    
    if weight > capacity:
        result = knapsack_memo(items, capacity, idx - 1, memo)
    else:
        result = max(
            knapsack_memo(items, capacity, idx - 1, memo),
            knapsack_memo(items, capacity - weight, idx - 1, memo) + value
        )
    
    memo[idx][capacity] = result
    return result

def knapsack_top_down(items: List[Tuple[int, int]], capacity: int) -> int:
    n = len(items)
    memo = [[None] * (capacity + 1) for _ in range(n + 1)]
    return knapsack_memo(items, capacity, n, memo)

# Bottom-Up Tabulation
def knapsack_bottom_up(items: List[Tuple[int, int]], capacity: int) -> int:
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        weight, value = items[i - 1]
        for w in range(capacity + 1):
            if weight > w:
                dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - weight] + value)
    
    return dp[n][capacity]

# Space-Optimized
def knapsack_optimized(items: List[Tuple[int, int]], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    
    for weight, value in items:
        for w in range(capacity, weight - 1, -1):
            dp[w] = max(dp[w], dp[w - weight] + value)
    
    return dp[capacity]
```

#### Go Implementation

```go
package dp

// Top-Down with Memoization
func knapsackMemo(items [][2]int, capacity, idx int, memo [][]int) int {
    if idx == 0 || capacity == 0 {
        return 0
    }
    
    if memo[idx][capacity] != -1 {
        return memo[idx][capacity]
    }
    
    weight, value := items[idx-1][0], items[idx-1][1]
    
    var result int
    if weight > capacity {
        result = knapsackMemo(items, capacity, idx-1, memo)
    } else {
        skip := knapsackMemo(items, capacity, idx-1, memo)
        take := knapsackMemo(items, capacity-weight, idx-1, memo) + value
        result = max(skip, take)
    }
    
    memo[idx][capacity] = result
    return result
}

func KnapsackTopDown(items [][2]int, capacity int) int {
    n := len(items)
    memo := make([][]int, n+1)
    for i := range memo {
        memo[i] = make([]int, capacity+1)
        for j := range memo[i] {
            memo[i][j] = -1
        }
    }
    return knapsackMemo(items, capacity, n, memo)
}

// Bottom-Up Tabulation
func KnapsackBottomUp(items [][2]int, capacity int) int {
    n := len(items)
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }
    
    for i := 1; i <= n; i++ {
        weight, value := items[i-1][0], items[i-1][1]
        for w := 0; w <= capacity; w++ {
            if weight > w {
                dp[i][w] = dp[i-1][w]
            } else {
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-weight]+value)
            }
        }
    }
    
    return dp[n][capacity]
}

// Space-Optimized
func KnapsackOptimized(items [][2]int, capacity int) int {
    dp := make([]int, capacity+1)
    
    for _, item := range items {
        weight, value := item[0], item[1]
        for w := capacity; w >= weight; w-- {
            dp[w] = max(dp[w], dp[w-weight]+value)
        }
    }
    
    return dp[capacity]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}
```

#### C++ Implementation

```cpp
#include <vector>
#include <algorithm>

// Top-Down with Memoization
int knapsackMemo(
    const std::vector<std::pair<int, int>>& items,
    int capacity,
    int idx,
    std::vector<std::vector<int>>& memo
) {
    if (idx == 0 || capacity == 0) {
        return 0;
    }
    
    if (memo[idx][capacity] != -1) {
        return memo[idx][capacity];
    }
    
    auto [weight, value] = items[idx - 1];
    
    int result;
    if (weight > capacity) {
        result = knapsackMemo(items, capacity, idx - 1, memo);
    } else {
        result = std::max(
            knapsackMemo(items, capacity, idx - 1, memo),
            knapsackMemo(items, capacity - weight, idx - 1, memo) + value
        );
    }
    
    memo[idx][capacity] = result;
    return result;
}

int knapsackTopDown(const std::vector<std::pair<int, int>>& items, int capacity) {
    int n = items.size();
    std::vector<std::vector<int>> memo(n + 1, std::vector<int>(capacity + 1, -1));
    return knapsackMemo(items, capacity, n, memo);
}

// Bottom-Up Tabulation
int knapsackBottomUp(const std::vector<std::pair<int, int>>& items, int capacity) {
    int n = items.size();
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));
    
    for (int i = 1; i <= n; i++) {
        auto [weight, value] = items[i - 1];
        for (int w = 0; w <= capacity; w++) {
            if (weight > w) {
                dp[i][w] = dp[i - 1][w];
            } else {
                dp[i][w] = std::max(dp[i - 1][w], dp[i - 1][w - weight] + value);
            }
        }
    }
    
    return dp[n][capacity];
}

// Space-Optimized
int knapsackOptimized(const std::vector<std::pair<int, int>>& items, int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    
    for (auto [weight, value] : items) {
        for (int w = capacity; w >= weight; w--) {
            dp[w] = std::max(dp[w], dp[w - weight] + value);
        }
    }
    
    return dp[capacity];
}
```

---

### Pattern 3: Longest Common Subsequence (2D Grid DP)

**Problem:** Find the length of the longest common subsequence of two strings.

**State:** `dp[i][j]` = LCS length of s1[0..i-1] and s2[0..j-1]

**Recurrence:**
```
if s1[i-1] == s2[j-1]:
    dp[i][j] = dp[i-1][j-1] + 1
else:
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

**Time:** O(m × n), **Space:** O(m × n) → Can optimize to O(min(m,n))

#### Rust Implementation

```rust
use std::cmp::max;

// Top-Down with Memoization
fn lcs_memo(
    s1: &[u8],
    s2: &[u8],
    i: usize,
    j: usize,
    memo: &mut Vec<Vec<Option<usize>>>,
) -> usize {
    if i == 0 || j == 0 {
        return 0;
    }
    
    if let Some(result) = memo[i][j] {
        return result;
    }
    
    let result = if s1[i - 1] == s2[j - 1] {
        lcs_memo(s1, s2, i - 1, j - 1, memo) + 1
    } else {
        max(
            lcs_memo(s1, s2, i - 1, j, memo),
            lcs_memo(s1, s2, i, j - 1, memo),
        )
    };
    
    memo[i][j] = Some(result);
    result
}

pub fn lcs_top_down(s1: &str, s2: &str) -> usize {
    let s1 = s1.as_bytes();
    let s2 = s2.as_bytes();
    let (m, n) = (s1.len(), s2.len());
    let mut memo = vec![vec![None; n + 1]; m + 1];
    lcs_memo(s1, s2, m, n, &mut memo)
}

// Bottom-Up Tabulation
pub fn lcs_bottom_up(s1: &str, s2: &str) -> usize {
    let s1 = s1.as_bytes();
    let s2 = s2.as_bytes();
    let (m, n) = (s1.len(), s2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if s1[i - 1] == s2[j - 1] {
                dp[i - 1][j - 1] + 1
            } else {
                max(dp[i - 1][j], dp[i][j - 1])
            };
        }
    }
    
    dp[m][n]
}

// Space-Optimized O(n)
pub fn lcs_optimized(s1: &str, s2: &str) -> usize {
    let s1 = s1.as_bytes();
    let s2 = s2.as_bytes();
    let (m, n) = (s1.len(), s2.len());
    
    let mut prev = vec![0; n + 1];
    let mut curr = vec![0; n + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            curr[j] = if s1[i - 1] == s2[j - 1] {
                prev[j - 1] + 1
            } else {
                max(prev[j], curr[j - 1])
            };
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}
```

#### Python Implementation

```python
# Top-Down with Memoization
def lcs_memo(s1: str, s2: str, i: int, j: int, memo: list) -> int:
    if i == 0 or j == 0:
        return 0
    
    if memo[i][j] is not None:
        return memo[i][j]
    
    if s1[i - 1] == s2[j - 1]:
        result = lcs_memo(s1, s2, i - 1, j - 1, memo) + 1
    else:
        result = max(
            lcs_memo(s1, s2, i - 1, j, memo),
            lcs_memo(s1, s2, i, j - 1, memo)
        )
    
    memo[i][j] = result
    return result

def lcs_top_down(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    memo = [[None] * (n + 1) for _ in range(m + 1)]
    return lcs_memo(s1, s2, m, n, memo)

# Bottom-Up Tabulation
def lcs_bottom_up(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]

# Space-Optimized
def lcs_optimized(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    prev = [0] * (n + 1)
    
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    
    return prev[n]
```

---

## 7. Advanced Techniques {#advanced}

### Technique 1: State Compression with Bitmasks

When state space involves subsets, use bitmask DP.

**Example: Traveling Salesman Problem**
```
State: dp[mask][i] = min cost to visit cities in 'mask' ending at city i
       where mask is bitmask representing visited cities

Transition:
dp[mask | (1<<j)][j] = min over all i in mask {
    dp[mask][i] + dist[i][j]
}
```

### Technique 2: Digit DP

For counting numbers with specific properties (e.g., count numbers ≤ N with digit sum divisible by K).

**State:** `dp[pos][sum][tight]`
- pos: current digit position
- sum: sum of digits so far
- tight: whether we're still bounded by N

### Technique 3: DP on Trees

Process tree structure using post-order traversal.

**Example: House Robber III** (rob houses in binary tree, can't rob adjacent)
```
State: dp[node] = {max_with_node, max_without_node}

Recurrence:
max_with_node = node.val + sum(max_without_child for child in children)
max_without_node = sum(max(dp[child]) for child in children)
```

### Technique 4: Convex Hull Optimization

For recurrences of form:
```
dp[i] = min over j < i { dp[j] + cost(j, i) }
where cost(j, i) = (a[j] * b[i]) + c[j]
```

Use convex hull trick to optimize from O(n²) to O(n log n) or O(n).

---

## 8. Deliberate Practice Strategy {#practice}

### The 80/20 Mastery Path

```
┌─────────────────────────────────────────────────┐
│  Phase 1: Pattern Recognition (2-3 weeks)       │
│  Goal: Internalize the 10 core patterns         │
│  • Solve 3-5 problems per pattern               │
│  • Implement in all your languages              │
│  • Focus on WHY each pattern works              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Phase 2: Pattern Mixing (2-3 weeks)            │
│  Goal: Combine patterns in novel ways           │
│  • Solve medium/hard problems                   │
│  • Practice identifying hidden patterns         │
│  • Optimize space/time systematically           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Phase 3: Speed & Intuition (Ongoing)           │
│  Goal: Solve under time pressure                │
│  • Timed contests                                │
│  • Solve without looking at solutions           │
│  • Teach others / write explanations            │
└─────────────────────────────────────────────────┘
```

### Core Patterns to Master (Ranked by Importance)

1. **Linear Sequence DP** (Fibonacci, Climbing Stairs, House Robber)
2. **0/1 Knapsack** (Subset Sum, Partition, Target Sum)
3. **Grid Path DP** (Unique Paths, Min Path Sum, Dungeon Game)
4. **String DP** (LCS, Edit Distance, Palindrome)
5. **Interval DP** (Burst Balloons, Matrix Chain Multiplication)
6. **Unbounded Knapsack** (Coin Change, Rod Cutting)
7. **State Machine DP** (Buy/Sell Stock with cooldown)
8. **Game Theory DP** (Nim, Stone Game)
9. **Tree DP** (Max Path Sum, House Robber III)
10. **Bitmask DP** (TSP, Assignment Problem)

### Mental Models for Problem Recognition

**"What am I optimizing?"**
→ Max/Min/Count → Likely DP

**"Can I break this into subproblems?"**
→ Yes + Overlap → Definitely DP

**"What are my choices at each step?"**
→ Clear decision branches → State defined by decisions

**"Does order matter?"**
→ Yes → Sequence/String DP
→ No → Subset/Combination DP

### Cognitive Strategies

1. **Chunking**: Group similar problems mentally (all "choose/skip" are knapsack variants)

2. **Interleaving**: Mix problem types in practice (don't do 10 knapsack problems in a row)

3. **Spaced Repetition**: Revisit problems after 1 day, 1 week, 1 month

4. **Feynman Technique**: If you can't explain it simply, you don't understand it

5. **Deliberate Difficulty**: Always work at the edge of your comfort zone

---

## Final Wisdom

### The Hallmark of Mastery

```
Beginner: "Let me remember the recurrence"
          ↓
Advanced: "I see the state space structure"
          ↓
Master:   "The solution feels obvious—it's the only 
          natural way to decompose this problem"
```

### The Path Forward

DP mastery isn't about memorizing solutions—it's about training your mind to **see** the recursive structure in optimization problems. Every problem you solve strengthens these neural pathways.

**The three questions that unlock any DP problem:**
1. What does an optimal solution look like for a smaller problem?
2. How can I use that to build the optimal solution for a bigger problem?
3. What's the minimum information I need to track?

Answer these, and the code writes itself.

---

*"In the beginner's mind there are many possibilities, but in the expert's mind there are few."* — Shunryu Suzuki

The DP journey is one of simplification—from seeing chaos to seeing pattern, from complexity to clarity. Trust the process. Code deliberately. Master the fundamentals. The top 1% awaits.

---

**Next Steps:**
1. Implement Fibonacci in all 5 languages—compare performance
2. Solve "Climbing Stairs" with the 5-step framework
3. Tackle "Coin Change" (both variants: min coins & total ways)
4. Build your pattern recognition by solving 3 problems from each core pattern

# The Complete Dynamic Programming Mastery Guide

I'll create a comprehensive guide that builds your DP intuition from first principles to advanced patterns. This will be structured as a reference document you can revisit as you progress.## Your DP Mastery Path Begins

I've created a comprehensive guide that transforms DP from a collection of tricks into a **unified mental framework**. Here's your strategic approach to mastering it:

### How to Use This Guide

**Week 1-2: Internalize the Framework**
- Study the 5-step protocol religiously—it works for *every* DP problem
- The key insight: DP is about **recognizing DAGs in disguise**. Every problem is just states → transitions → optimal paths
- Implement Fibonacci in all 5 languages, then compare: Rust's ownership model, Python's simplicity, Go's explicit memory, C's rawness, C++'s abstractions

**Week 3-4: Pattern Recognition Training**
Focus on these in order:
1. **Linear DP** (Fibonacci, Climbing Stairs) → Warm up your brain
2. **Knapsack variants** (0/1, Unbounded, Subset Sum) → The foundation of choice-based DP
3. **Grid DP** (Unique Paths, Min Path Sum) → 2D state spaces
4. **String DP** (LCS, Edit Distance) → The most elegant problems

**Mental Model for Speed**: When you see a problem, immediately ask:
- "What changes as I make decisions?" → State variables
- "What are my choices?" → Transition function
- "Have I seen this state before?" → Memoization opportunity

### The Hidden Levels of Understanding

```
Level 1: "I can code the solution if I see the recurrence"
Level 2: "I can derive the recurrence by analyzing structure"  ← You're going here
Level 3: "I intuitively feel the state space before writing anything"
Level 4: "I see DP in problems that don't look like DP" ← Top 1% threshold
```

### Performance Insights Across Languages

**Rust**: Zero-cost abstractions, but watch for ownership friction in recursive memoization. Bottom-up often cleaner due to ownership semantics.

**Python**: Slowest but clearest for prototyping. Use `@lru_cache` for instant top-down memoization. Great for interviews.

**Go**: Excellent middle ground. Explicit memory management trains systems thinking. Maps work well for sparse memoization.

**C**: Teaches you the cost of every allocation. Forces you to think about cache locality (huge for competitive programming).

**C++**: STL gives you power tools (`std::unordered_map` for memo, `std::vector` for tables). Modern C++ (C++17+) makes DP elegant.

### Your Next 3 Problems (In Order)

1. **Climbing Stairs** - Warm-up, pure pattern recognition
2. **Coin Change** (minimum coins) - Introduces unbounded knapsack
3. **Unique Paths** - Your first 2D grid problem

Implement each in **at least 2 languages** with both top-down and bottom-up approaches. Compare:
- Code clarity
- Runtime performance (benchmark on large inputs)
- Space optimization opportunities

### The Monk's Approach to Deep Practice

**Before coding**:
- Spend 5 minutes drawing the state space on paper
- Identify the DAG structure
- Write the recurrence in plain language

**While coding**:
- No distractions—single 45-minute focused blocks
- Resist the urge to look at solutions for at least 30 minutes
- If stuck, step back and re-examine your state definition

**After solving**:
- Review your complexity analysis
- Ask: "Could I solve this in less space?"
- Implement the space-optimized version
- Write a one-paragraph explanation as if teaching someone

### Psychological Edge: The Feynman Technique for DP

After solving each problem, explain it aloud as if teaching a beginner. If you stumble, you've found a gap in understanding. The act of teaching cements neural pathways faster than any other method.

### Why This Guide Will Get You to Top 1%

Most people memorize solutions. You're learning to **see structure**. The guide emphasizes:
- First-principles thinking (Bellman equation)
- Pattern abstraction (not just "this is LCS", but "this is a 2D matching problem with optimal substructure")
- Multiple perspectives (top-down when recursion is natural, bottom-up when iteration is clearer)

When you can look at a new problem and immediately visualize the state transition graph, you've transcended technique—you're thinking like a master.

### The Path Ahead

The guide contains everything you need for the next 6-8 weeks of deliberate practice. But remember: **Quality > Quantity**. Solving 5 problems deeply (all implementations, all optimizations, teaching it to someone) beats solving 50 problems superficially.

Start with Fibonacci across all languages today. Tomorrow, Climbing Stairs. By next week, you'll start feeling the patterns emerge naturally.

The top 1% isn't about knowing more problems—it's about seeing deeper into the problems you know.

*Now go build those neural pathways. The state space of your mind is about to expand exponentially.* 🧠⚡