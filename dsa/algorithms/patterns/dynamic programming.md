# Dynamic Programming: A Comprehensive Guide

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [How Dynamic Programming Works](#how-dp-works)
3. [Classic Problems with Implementations](#classic-problems)
4. [Real-World Applications](#real-world-applications)

---

## Core Concepts

### What is Dynamic Programming?

Dynamic Programming (DP) is an algorithmic paradigm that solves complex problems by:
1. **Breaking them into overlapping subproblems**
2. **Storing solutions to avoid redundant computation**
3. **Building up solutions from smaller subproblems**

### Two Key Properties

**1. Overlapping Subproblems**
```
Problem is broken into smaller subproblems that are reused multiple times.

Example: Fibonacci(5)
         
                    fib(5)
                   /      \
              fib(4)      fib(3)
             /     \      /     \
        fib(3)   fib(2) fib(2) fib(1)
        /    \    /   \  /   \
    fib(2) fib(1) ... ... ... ...
    
Notice: fib(3), fib(2), fib(1) computed multiple times!
```

**2. Optimal Substructure**
```
Optimal solution to problem contains optimal solutions to subproblems.

Example: Shortest path from A to D
    
    A ---2---> B ---3---> D     Total: 5
     \                           
      4                          
       \                         
        C ---1---> D             Total: 5
        
If A→B→D is optimal, then B→D must be optimal for that subpath.
```

---

## How Dynamic Programming Works

### Two Approaches: Memoization vs Tabulation

#### Memoization (Top-Down)
```
Start from original problem, recursively break down, cache results.

Call Stack:          Memory Cache:
                     
fib(5) ─────┐       [·, ·, ·, ·, ·, ·]
    │       │
fib(4) ─┐   │       [·, ·, ·, ·, ·, ·]
    │   │   │
fib(3) ─┼───┘       [·, ·, ·, 2, ·, ·]  ← Cache fib(3)
    │   │
fib(2) ─┘           [·, ·, 1, 2, ·, ·]  ← Cache fib(2)
                    [·, ·, 1, 2, 3, ·]  ← Cache fib(4)
Return fib(3)       [·, ·, 1, 2, 3, 5]  ← Cache fib(5)
from cache! ────────────────┘
```

#### Tabulation (Bottom-Up)
```
Start from base cases, iteratively build up to solution.

Table Building Process:

Step 0:  [0, 1, ·, ·, ·, ·]  ← Initialize base cases
         
Step 1:  [0, 1, 1, ·, ·, ·]  ← fib(2) = fib(0) + fib(1)
         
Step 2:  [0, 1, 1, 2, ·, ·]  ← fib(3) = fib(1) + fib(2)
         
Step 3:  [0, 1, 1, 2, 3, ·]  ← fib(4) = fib(2) + fib(3)
         
Step 4:  [0, 1, 1, 2, 3, 5]  ← fib(5) = fib(3) + fib(4)
```

### Complexity Comparison
```
Naive Recursion:     Memoization:        Tabulation:
                     
Time:  O(2^n)        Time:  O(n)         Time:  O(n)
Space: O(n)          Space: O(n)         Space: O(n)
      (call stack)         (cache)             (table)

Recursion Tree       Linear Calls        Iterative Fill
   (exponential)     (with caching)      (bottom-up)
```

---

## Classic Problems

### Problem 1: Fibonacci Sequence

**Problem Statement**: Find the nth Fibonacci number where F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)

**Recurrence Relation**:
```
F(n) = F(n-1) + F(n-2)

Base cases: F(0) = 0, F(1) = 1
```

**Visualization**:
```
n:     0   1   2   3   4   5   6   7   8
F(n):  0   1   1   2   3   5   8  13  21
       ↑   ↑   └───┴───┘
     base  base    sum of previous two
```

#### Python Implementation

```python
# 1. Naive Recursion (Exponential Time)
def fib_naive(n):
    if n <= 1:
        return n
    return fib_naive(n-1) + fib_naive(n-2)

# 2. Memoization (Top-Down DP)
def fib_memo(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]

# 3. Tabulation (Bottom-Up DP)
def fib_tab(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]

# 4. Space-Optimized (O(1) space)
def fib_optimized(n):
    if n <= 1:
        return n
    prev2, prev1 = 0, 1
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    return prev1
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

// 1. Naive Recursion
long long fib_naive(int n) {
    if (n <= 1) return n;
    return fib_naive(n-1) + fib_naive(n-2);
}

// 2. Memoization
long long fib_memo_helper(int n, long long* memo) {
    if (memo[n] != -1) return memo[n];
    if (n <= 1) return n;
    memo[n] = fib_memo_helper(n-1, memo) + fib_memo_helper(n-2, memo);
    return memo[n];
}

long long fib_memo(int n) {
    long long* memo = (long long*)malloc((n+1) * sizeof(long long));
    for (int i = 0; i <= n; i++) memo[i] = -1;
    long long result = fib_memo_helper(n, memo);
    free(memo);
    return result;
}

// 3. Tabulation
long long fib_tab(int n) {
    if (n <= 1) return n;
    long long* dp = (long long*)malloc((n+1) * sizeof(long long));
    dp[0] = 0;
    dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    long long result = dp[n];
    free(dp);
    return result;
}

// 4. Space-Optimized
long long fib_optimized(int n) {
    if (n <= 1) return n;
    long long prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        long long current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    return prev1;
}
```

#### C++ Implementation

```cpp
#include <vector>
#include <unordered_map>

// 1. Naive Recursion
long long fib_naive(int n) {
    if (n <= 1) return n;
    return fib_naive(n-1) + fib_naive(n-2);
}

// 2. Memoization
long long fib_memo(int n, std::unordered_map<int, long long>& memo) {
    if (memo.find(n) != memo.end()) return memo[n];
    if (n <= 1) return n;
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo);
    return memo[n];
}

long long fib_memo(int n) {
    std::unordered_map<int, long long> memo;
    return fib_memo(n, memo);
}

// 3. Tabulation
long long fib_tab(int n) {
    if (n <= 1) return n;
    std::vector<long long> dp(n + 1);
    dp[0] = 0;
    dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    return dp[n];
}

// 4. Space-Optimized
long long fib_optimized(int n) {
    if (n <= 1) return n;
    long long prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        long long current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    return prev1;
}
```

#### Go Implementation

```go
package main

// 1. Naive Recursion
func fibNaive(n int) int64 {
    if n <= 1 {
        return int64(n)
    }
    return fibNaive(n-1) + fibNaive(n-2)
}

// 2. Memoization
func fibMemo(n int, memo map[int]int64) int64 {
    if val, exists := memo[n]; exists {
        return val
    }
    if n <= 1 {
        return int64(n)
    }
    memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo)
    return memo[n]
}

func fibMemoWrapper(n int) int64 {
    memo := make(map[int]int64)
    return fibMemo(n, memo)
}

// 3. Tabulation
func fibTab(n int) int64 {
    if n <= 1 {
        return int64(n)
    }
    dp := make([]int64, n+1)
    dp[0] = 0
    dp[1] = 1
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    return dp[n]
}

// 4. Space-Optimized
func fibOptimized(n int) int64 {
    if n <= 1 {
        return int64(n)
    }
    prev2, prev1 := int64(0), int64(1)
    for i := 2; i <= n; i++ {
        current := prev1 + prev2
        prev2, prev1 = prev1, current
    }
    return prev1
}
```

#### Rust Implementation

```rust
use std::collections::HashMap;

// 1. Naive Recursion
fn fib_naive(n: u32) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    fib_naive(n - 1) + fib_naive(n - 2)
}

// 2. Memoization
fn fib_memo(n: u32, memo: &mut HashMap<u32, u64>) -> u64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    if n <= 1 {
        return n as u64;
    }
    let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    memo.insert(n, result);
    result
}

fn fib_memo_wrapper(n: u32) -> u64 {
    let mut memo = HashMap::new();
    fib_memo(n, &mut memo)
}

// 3. Tabulation
fn fib_tab(n: u32) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    let mut dp = vec![0u64; (n + 1) as usize];
    dp[1] = 1;
    for i in 2..=n as usize {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    dp[n as usize]
}

// 4. Space-Optimized
fn fib_optimized(n: u32) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    let (mut prev2, mut prev1) = (0u64, 1u64);
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    prev1
}
```

---

### Problem 2: 0/1 Knapsack

**Problem Statement**: Given weights and values of n items, put items in a knapsack of capacity W to maximize total value. Each item can be taken once (0/1 choice).

**Recurrence Relation**:
```
dp[i][w] = maximum value using first i items with capacity w

dp[i][w] = max(
    dp[i-1][w],              // Don't take item i
    dp[i-1][w-weight[i]] + value[i]  // Take item i
)

Base case: dp[0][w] = 0 (no items = 0 value)
```

**Visualization**:
```
Items:  weight = [2, 3, 4, 5]
        value  = [3, 4, 5, 6]
Capacity W = 5

DP Table (i = item index, w = capacity):

      w=0  w=1  w=2  w=3  w=4  w=5
i=0    0    0    0    0    0    0   (no items)
i=1    0    0    3    3    3    3   (item 0: wt=2, val=3)
i=2    0    0    3    4    4    7   (item 1: wt=3, val=4)
i=3    0    0    3    4    5    7   (item 2: wt=4, val=5)
i=4    0    0    3    4    5    7   (item 3: wt=5, val=6)
                              ↑
                           Answer: max value = 7

Decision at dp[2][5]:
- Don't take item 1: dp[1][5] = 3
- Take item 1: dp[1][2] + 4 = 3 + 4 = 7
- Choose max(3, 7) = 7
```

#### Python Implementation

```python
def knapsack_01(weights, values, capacity):
    n = len(weights)
    # dp[i][w] = max value using first i items with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            # Take item i-1 if it fits
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]

# Space-optimized version (O(W) space)
def knapsack_01_optimized(weights, values, capacity):
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        # Traverse backwards to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

int max(int a, int b) {
    return (a > b) ? a : b;
}

int knapsack_01(int* weights, int* values, int n, int capacity) {
    int** dp = (int**)malloc((n + 1) * sizeof(int*));
    for (int i = 0; i <= n; i++) {
        dp[i] = (int*)calloc(capacity + 1, sizeof(int));
    }
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];
            
            if (weights[i-1] <= w) {
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        }
    }
    
    int result = dp[n][capacity];
    
    for (int i = 0; i <= n; i++) {
        free(dp[i]);
    }
    free(dp);
    
    return result;
}

// Space-optimized version
int knapsack_01_optimized(int* weights, int* values, int n, int capacity) {
    int* dp = (int*)calloc(capacity + 1, sizeof(int));
    
    for (int i = 0; i < n; i++) {
        for (int w = capacity; w >= weights[i]; w--) {
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    int result = dp[capacity];
    free(dp);
    return result;
}
```

#### C++ Implementation

```cpp
#include <vector>
#include <algorithm>

int knapsack_01(const std::vector<int>& weights, 
                const std::vector<int>& values, 
                int capacity) {
    int n = weights.size();
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];
            
            if (weights[i-1] <= w) {
                dp[i][w] = std::max(dp[i][w], 
                                   dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        }
    }
    
    return dp[n][capacity];
}

// Space-optimized version
int knapsack_01_optimized(const std::vector<int>& weights, 
                         const std::vector<int>& values, 
                         int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    
    for (int i = 0; i < weights.size(); i++) {
        for (int w = capacity; w >= weights[i]; w--) {
            dp[w] = std::max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    return dp[capacity];
}
```

#### Go Implementation

```go
func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func knapsack01(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }
    
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            dp[i][w] = dp[i-1][w]
            
            if weights[i-1] <= w {
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w-weights[i-1]] + values[i-1])
            }
        }
    }
    
    return dp[n][capacity]
}

// Space-optimized version
func knapsack01Optimized(weights, values []int, capacity int) int {
    dp := make([]int, capacity+1)
    
    for i := 0; i < len(weights); i++ {
        for w := capacity; w >= weights[i]; w-- {
            dp[w] = max(dp[w], dp[w-weights[i]] + values[i])
        }
    }
    
    return dp[capacity]
}
```

#### Rust Implementation

```rust
use std::cmp::max;

fn knapsack_01(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=capacity {
            dp[i][w] = dp[i-1][w];
            
            if weights[i-1] <= w {
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        }
    }
    
    dp[n][capacity]
}

// Space-optimized version
fn knapsack_01_optimized(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let mut dp = vec![0; capacity + 1];
    
    for i in 0..weights.len() {
        for w in (weights[i]..=capacity).rev() {
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    dp[capacity]
}
```

---

### Problem 3: Longest Common Subsequence (LCS)

**Problem Statement**: Find the length of the longest subsequence common to two sequences.

**Recurrence Relation**:
```
LCS(i, j) = length of LCS of text1[0..i] and text2[0..j]

LCS(i, j) = 
    1 + LCS(i-1, j-1)           if text1[i] == text2[j]
    max(LCS(i-1, j), LCS(i, j-1))  otherwise

Base case: LCS(i, 0) = LCS(0, j) = 0
```

**Visualization**:
```
text1 = "ABCDGH"
text2 = "AEDFHR"

DP Table:

        ""  A  E  D  F  H  R
    ""   0  0  0  0  0  0  0
    A    0  1  1  1  1  1  1
    B    0  1  1  1  1  1  1
    C    0  1  1  1  1  1  1
    D    0  1  1  2  2  2  2
    G    0  1  1  2  2  2  2
    H    0  1  1  2  2  3  3
                         ↑
                    Answer: LCS length = 3

How it works:
- text1[0]='A' matches text2[0]='A': dp[1][1] = 1 + dp[0][0] = 1
- text1[3]='D' matches text2[2]='D': dp[4][3] = 1 + dp[3][2] = 2
- text1[5]='H' matches text2[4]='H': dp[6][5] = 1 + dp[5][4] = 3

LCS = "ADH"
```

#### Python Implementation

```python
def lcs(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = 1 + dp[i-1][j-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

# Space-optimized version (O(min(m,n)) space)
def lcs_optimized(text1, text2):
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    
    m, n = len(text1), len(text2)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                curr[j] = 1 + prev[j-1]
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev, curr = curr, prev
    
    return prev[n]
```

#### C Implementation

```c
#include <string.h>

int max(int a, int b) {
    return (a > b) ? a : b;
}

int lcs(const char* text1, const char* text2) {
    int m = strlen(text1);
    int n = strlen(text2);
    
    int** dp = (int**)malloc((m + 1) * sizeof(int*));
    for (int i = 0; i <= m; i++) {
        dp[i] = (int*)calloc(n + 1, sizeof(int));
    }
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1[i-1] == text2[j-1]) {
                dp[i][j] = 1 + dp[i-1][j-1];
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    
    int result = dp[m][n];
    
    for (int i = 0; i <= m; i++) {
        free(dp[i]);
    }
    free(dp);
    
    return result;
}
```

#### C++ Implementation

```cpp
#include <string>
#include <vector>
#include <algorithm>

int lcs(const std::string& text1, const std::string& text2) {
    int m = text1.length();
    int n = text2.length();
    
    std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1[i-1] == text2[j-1]) {
                dp[i][j] = 1 + dp[i-1][j-1];
            } else {
                dp[i][j] = std::max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    
    return dp[m][n];
}

// Space-optimized version
int lcs_optimized(const std::string& text1, const std::string& text2) {
    int m = text1.length();
    int n = text2.length();
    
    std::vector<int> prev(n + 1, 0);
    std::vector<int> curr(n + 1, 0);
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1[i-1] == text2[j-1]) {
                curr[j] = 1 + prev[j-1];
            } else {
                curr[j] = std::max(prev[j], curr[j-1]);
            }
        }
        std::swap(prev, curr);
    }
    
    return prev[n];
}
```

#### Go Implementation

```go
func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func lcs(text1, text2 string) int {
    m, n := len(text1), len(text2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if text1[i-1] == text2[j-1] {
                dp[i][j] = 1 + dp[i-1][j-1]
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    
    return dp[m][n]
}

// Space-optimized version
func lcsOptimized(text1, text2 string) int {
    m, n := len(text1), len(text2)
    prev := make([]int, n+1)
    curr := make([]int, n+1)
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if text1[i-1] == text2[j-1] {
                curr[j] = 1 + prev[j-1]
            } else {
                curr[j] = max(prev[j], curr[j-1])
            }
        }
        prev, curr = curr, prev
    }
    
    return prev[n]
}
```

#### Rust Implementation

```rust
use std::cmp::max;

fn lcs(text1: &str, text2: &str) -> usize {
    let m = text1.len();
    let n = text2.len();
    let text1: Vec<char> = text1.chars().collect();
    let text2: Vec<char> = text2.chars().collect();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if text1[i-1] == text2[j-1] {
                dp[i][j] = 1 + dp[i-1][j-1];
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    
    dp[m][n]
}

// Space-optimized version
fn lcs_optimized(text1: &str, text2: &str) -> usize {
    let m = text1.len();
    let n = text2.len();
    let text1: Vec<char> = text1.chars().collect();
    let text2: Vec<char> = text2.chars().collect();
    
    let mut prev = vec![0; n + 1];
    let mut curr = vec![0; n + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if text1[i-1] == text2[j-1] {
                curr[j] = 1 + prev[j-1];
            } else {
                curr[j] = max(prev[j], curr[j-1]);
            }
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}
```

---

## Advanced DP Patterns

### State Machine DP

Used when problem has distinct states with transitions between them.

```
Example: Stock Buy/Sell with Cooldown

States:   [Hold]  ←──buy───  [NoStock]
            │                    ↑
            └──sell──→  [Cooldown]

State transitions:
hold[i] = max(hold[i-1], nostock[i-1] - price[i])
cooldown[i] = hold[i-1] + price[i]
nostock[i] = max(nostock[i-1], cooldown[i-1])
```

### Interval DP

Used for problems on subarrays/substrings where solution depends on interval endpoints.

```
dp[i][j] = solution for interval [i, j]

Common pattern:
dp[i][j] = max/min over all k in [i, j] of:
           dp[i][k] + dp[k+1][j] + cost(i, j)

Example: Matrix Chain Multiplication
dp[i][j] = minimum multiplications for matrices[i..j]
```

### Bitmask DP

Used when state can be represented by a set of binary flags.

```
dp[mask] = solution when subset represented by mask is processed

mask = 101101 (binary)
       ││││└─ element 0: included
       │││└── element 1: included
       ││└─── element 2: excluded
       │└──── element 3: included
       └───── element 4: excluded

Transitions using bitwise operations:
- Add element i: mask | (1 << i)
- Remove element i: mask & ~(1 << i)
- Check element i: mask & (1 << i)
```

### Digit DP

Used for counting numbers with specific properties in a range.

```
Count numbers from 0 to N with property P

dp[pos][tight][...state...] = count of valid numbers

pos = current digit position
tight = whether we're still bounded by N
state = problem-specific state

Example: Count numbers with no consecutive 1s in binary
```

---

## Real-World Applications

### 1. **Bioinformatics**
- DNA sequence alignment (LCS variant)
- Protein folding prediction
- Gene prediction and annotation
- Phylogenetic tree construction
- RNA secondary structure prediction

### 2. **Compiler Optimization**
- Register allocation
- Instruction scheduling
- Code generation
- Loop optimization
- Dead code elimination

### 3. **Network Routing**
- Shortest path algorithms (Bellman-Ford)
- Network flow optimization
- Bandwidth allocation
- Quality of Service (QoS) routing
- Multi-path routing protocols

### 4. **Image Processing**
- Seam carving for content-aware image resizing
- Image compression (JPEG optimization)
- Stereo correspondence in computer vision
- Video encoding optimization
- Optical character recognition (OCR)

### 5. **Natural Language Processing**
- Spell checking and correction (edit distance)
- Machine translation
- Speech recognition (Viterbi algorithm)
- Part-of-speech tagging
- Text justification and line breaking

### 6. **Finance**
- Portfolio optimization
- Option pricing (binomial trees)
- Risk assessment models
- Trading strategy optimization
- Resource allocation

### 7. **Operations Research**
- Job scheduling with deadlines
- Facility location problems
- Vehicle routing optimization
- Warehouse layout optimization
- Production planning

### 8. **Game Development**
- Pathfinding (A* with DP components)
- Strategy game AI
- Puzzle solving algorithms
- Resource management optimization
- Animation blending

### 9. **Computational Geometry**
- Convex hull construction
- Polygon triangulation
- Closest pair of points
- Line segment intersection
- Geometric packing problems

### 10. **Database Systems**
- Query optimization
- Join ordering
- Index selection
- Materialized view selection
- Cache replacement policies

### 11. **Telecommunication**
- Signal processing optimization
- Error correction codes
- Network protocol design
- Bandwidth allocation
- Call routing in telephony

### 12. **Machine Learning**
- Hidden Markov Models
- Viterbi algorithm for sequence labeling
- Reinforcement learning (value iteration)
- Dynamic time warping for time series
- Neural network optimization

---

## Key Takeaways

### When to Use Dynamic Programming

1. **Problem exhibits overlapping subproblems**
   - Same subproblem computed multiple times
   - Can cache results for reuse

2. **Problem has optimal substructure**
   - Optimal solution contains optimal solutions to subproblems
   - Can build solution bottom-up

3. **Problem involves optimization**
   - Maximize or minimize some quantity
   - Count number of ways to do something

4. **Problem has recursive structure**
   - Natural recursive solution exists
   - But has exponential time complexity

### DP vs Other Approaches

```
Greedy vs DP:
├─ Greedy: Makes locally optimal choice at each step
│          May not give global optimum
│          Example: Coin change with specific denominations
│
└─ DP:     Considers all possibilities
           Guarantees global optimum
           Higher time/space complexity

Divide & Conquer vs DP:
├─ D&C:    Subproblems are independent
│          No overlap
│          Example: Merge sort
│
└─ DP:     Subproblems overlap
           Cache results
           Example: Fibonacci
```

### Complexity Analysis

```
Time Complexity = (Number of States) × (Time per State)

Space Complexity:
├─ Memoization:  O(number of unique states) + O(recursion depth)
└─ Tabulation:   O(number of states)

Optimization:
└─ Often can reduce space from O(n²) to O(n) or O(1)
   by keeping only necessary previous states
```

---

## Practice Problems by Difficulty

### Beginner
- Climbing Stairs
- Min Cost Climbing Stairs
- House Robber
- Maximum Subarray
- Best Time to Buy and Sell Stock

### Intermediate
- Coin Change
- Longest Increasing Subsequence
- Edit Distance
- Unique Paths
- Partition Equal Subset Sum

### Advanced
- Burst Balloons
- Regular Expression Matching
- Wildcard Matching
- Palindrome Partitioning II
- Maximal Rectangle

### Expert
- Shortest Palindrome
- Minimum Window Subsequence
- Number of Ways to Stay in Same Place
- Cherry Pickup II
- Count Different Palindromic Subsequences

# Dynamic Programming: Comprehensive Guide

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [How DP Works](#how-dp-works)
3. [Problem-Solving Patterns](#problem-solving-patterns)
4. [Implementation Examples](#implementation-examples)
5. [Real-World Use Cases](#real-world-use-cases)
6. [Advanced Techniques](#advanced-techniques)

---

## Core Concepts

### What is Dynamic Programming?

Dynamic Programming (DP) is an algorithmic optimization technique that solves complex problems by:
- **Breaking them into overlapping subproblems**
- **Storing solutions to avoid recomputation**
- **Building solutions bottom-up or top-down**

### The Two Pillars of DP

**1. Optimal Substructure**: The optimal solution can be constructed from optimal solutions of subproblems.

**2. Overlapping Subproblems**: The same subproblems are solved multiple times.

---

## How DP Works

### Without DP (Naive Recursion)
```
Fibonacci(5) - Computing without memoization

                        fib(5)
                      /       \
                fib(4)          fib(3)
               /     \         /     \
          fib(3)   fib(2)   fib(2)  fib(1)
         /    \    /   \    /   \
     fib(2) fib(1) ...  ... ...  ...
     /   \
 fib(1) fib(0)

Time Complexity: O(2^n) - Exponential
Space Complexity: O(n) - Recursion stack

Problem: fib(3) computed MULTIPLE times
         fib(2) computed EVEN MORE times
```

### With DP (Memoization)
```
Fibonacci(5) - With memoization cache

Step 1: fib(5) → needs fib(4) and fib(3)
Step 2: fib(4) → needs fib(3) and fib(2)
Step 3: fib(3) → needs fib(2) and fib(1) → compute & cache
Step 4: fib(2) → needs fib(1) and fib(0) → compute & cache
Step 5: fib(3) → CACHE HIT! Return stored value
Step 6: fib(4) → use cached fib(3) and fib(2)
Step 7: fib(5) → use cached fib(4) and fib(3)

Cache: {0:0, 1:1, 2:1, 3:2, 4:3, 5:5}

Time Complexity: O(n) - Each subproblem solved once
Space Complexity: O(n) - Cache + recursion stack
```

### DP Visualization: State Transition

```
State Space Exploration (1D DP Example)

Index:     0    1    2    3    4    5
          ┌────┬────┬────┬────┬────┬────┐
State:    │ S₀ │ S₁ │ S₂ │ S₃ │ S₄ │ S₅ │
          └────┴────┴────┴────┴────┴────┘
            ↓    ↓    ↓    ↓    ↓    ↓
          ┌────┬────┬────┬────┬────┬────┐
DP Array: │ 0  │ 1  │ 1  │ 2  │ 3  │ 5  │
          └────┴────┴────┴────┴────┴────┘

Transition: dp[i] = f(dp[i-1], dp[i-2], ...)
```

---

## Problem-Solving Patterns

### Pattern 1: Linear DP (1D State Space)

**Decision Tree:**
```
At each position i, you have limited choices

         Position i
         /    |    \
    Choice1 Choice2 Choice3
       ↓       ↓       ↓
    State1  State2  State3
```

**Examples:** Fibonacci, Climbing Stairs, House Robber

### Pattern 2: Grid DP (2D State Space)

**Grid Traversal:**
```
Start (0,0)                    Goal (m,n)
    ┌─────┬─────┬─────┬─────┐
    │  S  │  →  │  →  │  →  │
    ├─────┼─────┼─────┼─────┤
    │  ↓  │  ↘  │  →  │  ↓  │
    ├─────┼─────┼─────┼─────┤
    │  ↓  │  →  │  ↘  │  ↓  │
    ├─────┼─────┼─────┼─────┤
    │  →  │  →  │  →  │  G  │
    └─────┴─────┴─────┴─────┘

Recurrence: dp[i][j] = f(dp[i-1][j], dp[i][j-1])
Constraints: Can only move → or ↓
```

**Examples:** Unique Paths, Minimum Path Sum, Edit Distance

### Pattern 3: Sequence DP

**Subsequence Analysis:**
```
Sequence: [a₁, a₂, a₃, a₄, a₅]

For each element, decide:
   INCLUDE          EXCLUDE
      ↓                ↓
  New sequence    Continue without

Example: Longest Increasing Subsequence
  [10, 9, 2, 5, 3, 7, 101, 18]
   
   LIS ending at each position:
   10: [10]           length=1
   9:  [9]            length=1
   2:  [2]            length=1
   5:  [2,5]          length=2
   3:  [2,3]          length=2
   7:  [2,5,7]        length=3
   101:[2,5,7,101]    length=4
   18: [2,5,7,18]     length=4
```

### Pattern 4: Knapsack DP

**State Representation:**
```
Items:     i₁    i₂    i₃    i₄
Weight:    2     3     4     5
Value:     3     4     5     6
Capacity: W = 8

DP Table: dp[items][capacity]

        W: 0   1   2   3   4   5   6   7   8
    ┌─────┬───┬───┬───┬───┬───┬───┬───┬───┐
i=0 │  0  │ 0 │ 0 │ 0 │ 0 │ 0 │ 0 │ 0 │ 0 │
    ├─────┼───┼───┼───┼───┼───┼───┼───┼───┤
i=1 │  0  │ 0 │ 3 │ 3 │ 3 │ 3 │ 3 │ 3 │ 3 │
    ├─────┼───┼───┼───┼───┼───┼───┼───┼───┤
i=2 │  0  │ 0 │ 3 │ 4 │ 4 │ 7 │ 7 │ 7 │ 7 │
    ├─────┼───┼───┼───┼───┼───┼───┼───┼───┤
i=3 │  0  │ 0 │ 3 │ 4 │ 5 │ 7 │ 8 │ 9 │ 9 │
    └─────┴───┴───┴───┴───┴───┴───┴───┴───┘

Decision at dp[i][w]:
  - Take item i:    dp[i-1][w-weight[i]] + value[i]
  - Skip item i:    dp[i-1][w]
  - Choose maximum
```

---

## Implementation Examples

### 1. Fibonacci Sequence

**Problem:** Calculate nth Fibonacci number
**Recurrence:** F(n) = F(n-1) + F(n-2), F(0)=0, F(1)=1

#### Python Implementation

```python
# Approach 1: Top-Down (Memoization)
def fib_memoization(n, memo=None):
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fib_memoization(n-1, memo) + fib_memoization(n-2, memo)
    return memo[n]

# Approach 2: Bottom-Up (Tabulation)
def fib_tabulation(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Approach 3: Space-Optimized
def fib_optimized(n):
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    
    return prev1

# Test
print(fib_memoization(10))   # 55
print(fib_tabulation(10))     # 55
print(fib_optimized(10))      # 55
```

#### C Implementation

```c
#include <stdio.h>
#include <stdlib.h>

// Top-Down with Memoization
int fib_memo_helper(int n, int* memo) {
    if (memo[n] != -1) {
        return memo[n];
    }
    
    if (n <= 1) {
        memo[n] = n;
        return n;
    }
    
    memo[n] = fib_memo_helper(n-1, memo) + fib_memo_helper(n-2, memo);
    return memo[n];
}

int fib_memoization(int n) {
    int* memo = (int*)malloc((n + 1) * sizeof(int));
    for (int i = 0; i <= n; i++) {
        memo[i] = -1;
    }
    
    int result = fib_memo_helper(n, memo);
    free(memo);
    return result;
}

// Bottom-Up Tabulation
int fib_tabulation(int n) {
    if (n <= 1) return n;
    
    int* dp = (int*)malloc((n + 1) * sizeof(int));
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    
    int result = dp[n];
    free(dp);
    return result;
}

// Space-Optimized
int fib_optimized(int n) {
    if (n <= 1) return n;
    
    int prev2 = 0, prev1 = 1, current;
    
    for (int i = 2; i <= n; i++) {
        current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    return prev1;
}

int main() {
    printf("Fib(10) = %d\n", fib_memoization(10));
    printf("Fib(10) = %d\n", fib_tabulation(10));
    printf("Fib(10) = %d\n", fib_optimized(10));
    return 0;
}
```

#### C++ Implementation

```cpp
#include <iostream>
#include <vector>
#include <unordered_map>

// Top-Down with Memoization
class FibonacciMemo {
private:
    std::unordered_map<int, long long> memo;
    
public:
    long long calculate(int n) {
        if (memo.find(n) != memo.end()) {
            return memo[n];
        }
        
        if (n <= 1) {
            memo[n] = n;
            return n;
        }
        
        memo[n] = calculate(n-1) + calculate(n-2);
        return memo[n];
    }
};

// Bottom-Up Tabulation
long long fib_tabulation(int n) {
    if (n <= 1) return n;
    
    std::vector<long long> dp(n + 1);
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    
    return dp[n];
}

// Space-Optimized
long long fib_optimized(int n) {
    if (n <= 1) return n;
    
    long long prev2 = 0, prev1 = 1;
    
    for (int i = 2; i <= n; i++) {
        long long current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    return prev1;
}

int main() {
    FibonacciMemo fib_memo;
    std::cout << "Fib(10) = " << fib_memo.calculate(10) << std::endl;
    std::cout << "Fib(10) = " << fib_tabulation(10) << std::endl;
    std::cout << "Fib(10) = " << fib_optimized(10) << std::endl;
    return 0;
}
```

#### Go Implementation

```go
package main

import "fmt"

// Top-Down with Memoization
func fibMemoization(n int, memo map[int]int) int {
    if val, exists := memo[n]; exists {
        return val
    }
    
    if n <= 1 {
        memo[n] = n
        return n
    }
    
    memo[n] = fibMemoization(n-1, memo) + fibMemoization(n-2, memo)
    return memo[n]
}

// Bottom-Up Tabulation
func fibTabulation(n int) int {
    if n <= 1 {
        return n
    }
    
    dp := make([]int, n+1)
    dp[0] = 0
    dp[1] = 1
    
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    
    return dp[n]
}

// Space-Optimized
func fibOptimized(n int) int {
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

func main() {
    memo := make(map[int]int)
    fmt.Println("Fib(10) =", fibMemoization(10, memo))
    fmt.Println("Fib(10) =", fibTabulation(10))
    fmt.Println("Fib(10) =", fibOptimized(10))
}
```

#### Rust Implementation

```rust
use std::collections::HashMap;

// Top-Down with Memoization
fn fib_memoization(n: usize, memo: &mut HashMap<usize, u64>) -> u64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    if n <= 1 {
        memo.insert(n, n as u64);
        return n as u64;
    }
    
    let result = fib_memoization(n - 1, memo) + fib_memoization(n - 2, memo);
    memo.insert(n, result);
    result
}

// Bottom-Up Tabulation
fn fib_tabulation(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let mut dp = vec![0u64; n + 1];
    dp[0] = 0;
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n]
}

// Space-Optimized
fn fib_optimized(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let (mut prev2, mut prev1) = (0u64, 1u64);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}

fn main() {
    let mut memo = HashMap::new();
    println!("Fib(10) = {}", fib_memoization(10, &mut memo));
    println!("Fib(10) = {}", fib_tabulation(10));
    println!("Fib(10) = {}", fib_optimized(10));
}
```

---

### 2. Longest Common Subsequence (LCS)

**Problem:** Find the length of longest subsequence common to two sequences.

**State Representation:**
```
String 1: "ABCDGH"
String 2: "AEDFHR"

DP Table Construction:

       ""  A  E  D  F  H  R
    ┌────┬───┬───┬───┬───┬───┬───┐
""  │  0 │ 0 │ 0 │ 0 │ 0 │ 0 │ 0 │
    ├────┼───┼───┼───┼───┼───┼───┤
A   │  0 │ 1 │ 1 │ 1 │ 1 │ 1 │ 1 │
    ├────┼───┼───┼───┼───┼───┼───┤
B   │  0 │ 1 │ 1 │ 1 │ 1 │ 1 │ 1 │
    ├────┼───┼───┼───┼───┼───┼───┤
C   │  0 │ 1 │ 1 │ 1 │ 1 │ 1 │ 1 │
    ├────┼───┼───┼───┼───┼───┼───┤
D   │  0 │ 1 │ 1 │ 2 │ 2 │ 2 │ 2 │
    ├────┼───┼───┼───┼───┼───┼───┤
G   │  0 │ 1 │ 1 │ 2 │ 2 │ 2 │ 2 │
    ├────┼───┼───┼───┼───┼───┼───┤
H   │  0 │ 1 │ 1 │ 2 │ 2 │ 3 │ 3 │
    └────┴───┴───┴───┴───┴───┴───┘

Recurrence:
  if s1[i] == s2[j]: dp[i][j] = dp[i-1][j-1] + 1
  else:              dp[i][j] = max(dp[i-1][j], dp[i][j-1])

LCS: "ADH" (length = 3)
```

#### Python Implementation

```python
def lcs_length(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def lcs_string(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Build DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Backtrack to find LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i-1] == s2[j-1]:
            lcs.append(s1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))

# Test
s1 = "ABCDGH"
s2 = "AEDFHR"
print(f"LCS Length: {lcs_length(s1, s2)}")  # 3
print(f"LCS String: {lcs_string(s1, s2)}")  # ADH
```

#### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAX(a, b) ((a) > (b) ? (a) : (b))

int lcs_length(const char* s1, const char* s2) {
    int m = strlen(s1);
    int n = strlen(s2);
    
    int dp[m + 1][n + 1];
    
    // Initialize base cases
    for (int i = 0; i <= m; i++) dp[i][0] = 0;
    for (int j = 0; j <= n; j++) dp[0][j] = 0;
    
    // Fill DP table
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i-1] == s2[j-1]) {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = MAX(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    
    return dp[m][n];
}

int main() {
    const char* s1 = "ABCDGH";
    const char* s2 = "AEDFHR";
    printf("LCS Length: %d\n", lcs_length(s1, s2));
    return 0;
}
```

#### C++ Implementation

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

class LCS {
public:
    static int length(const std::string& s1, const std::string& s2) {
        int m = s1.length();
        int n = s2.length();
        
        std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));
        
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1[i-1] == s2[j-1]) {
                    dp[i][j] = dp[i-1][j-1] + 1;
                } else {
                    dp[i][j] = std::max(dp[i-1][j], dp[i][j-1]);
                }
            }
        }
        
        return dp[m][n];
    }
    
    static std::string getString(const std::string& s1, const std::string& s2) {
        int m = s1.length();
        int n = s2.length();
        
        std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));
        
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1[i-1] == s2[j-1]) {
                    dp[i][j] = dp[i-1][j-1] + 1;
                } else {
                    dp[i][j] = std::max(dp[i-1][j], dp[i][j-1]);
                }
            }
        }
        
        // Backtrack
        std::string lcs;
        int i = m, j = n;
        while (i > 0 && j > 0) {
            if (s1[i-1] == s2[j-1]) {
                lcs.push_back(s1[i-1]);
                i--;
                j--;
            } else if (dp[i-1][j] > dp[i][j-1]) {
                i--;
            } else {
                j--;
            }
        }
        
        std::reverse(lcs.begin(), lcs.end());
        return lcs;
    }
};

int main() {
    std::string s1 = "ABCDGH";
    std::string s2 = "AEDFHR";
    std::cout << "LCS Length: " << LCS::length(s1, s2) << std::endl;
    std::cout << "LCS String: " << LCS::getString(s1, s2) << std::endl;
    return 0;
}
```

#### Go Implementation

```go
package main

import "fmt"

func lcsLength(s1, s2 string) int {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    
    return dp[m][n]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func lcsString(s1, s2 string) string {
    m, n := len(s1), len(s2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    
    // Backtrack
    lcs := make([]byte, 0)
    i, j := m, n
    for i > 0 && j > 0 {
        if s1[i-1] == s2[j-1] {
            lcs = append(lcs, s1[i-1])
            i--
            j--
        } else if dp[i-1][j] > dp[i][j-1] {
            i--
        } else {
            j--
        }
    }
    
    // Reverse
    for i, j := 0, len(lcs)-1; i < j; i, j = i+1, j-1 {
        lcs[i], lcs[j] = lcs[j], lcs[i]
    }
    
    return string(lcs)
}

func main() {
    s1 := "ABCDGH"
    s2 := "AEDFHR"
    fmt.Printf("LCS Length: %d\n", lcsLength(s1, s2))
    fmt.Printf("LCS String: %s\n", lcsString(s1, s2))
}
```

#### Rust Implementation

```rust
use std::cmp::max;

fn lcs_length(s1: &str, s2: &str) -> usize {
    let s1_chars: Vec<char> = s1.chars().collect();
    let s2_chars: Vec<char> = s2.chars().collect();
    let m = s1_chars.len();
    let n = s2_chars.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1_chars[i - 1] == s2_chars[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

fn lcs_string(s1: &str, s2: &str) -> String {
    let s1_chars: Vec<char> = s1.chars().collect();
    let s2_chars: Vec<char> = s2.chars().collect();
    let m = s1_chars.len();
    let n = s2_chars.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1_chars[i - 1] == s2_chars[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    // Backtrack
    let mut lcs = Vec::new();
    let (mut i, mut j) = (m, n);
    
    while i > 0 && j > 0 {
        if s1_chars[i - 1] == s2_chars[j - 1] {
            lcs.push(s1_chars[i - 1]);
            i -= 1;
            j -= 1;
        } else if dp[i - 1][j] > dp[i][j - 1] {
            i -= 1;
        } else {
            j -= 1;
        }
    }
    
    lcs.reverse();
    lcs.into_iter().collect()
}

fn main() {
    let s1 = "ABCDGH";
    let s2 = "AEDFHR";
    println!("LCS Length: {}", lcs_length(s1, s2));
    println!("LCS String: {}", lcs_string(s1, s2));
}
```

---

### 3. 0/1 Knapsack Problem

**Problem:** Given weights and values of items, maximize value without exceeding capacity.

**State Transition:**
```
Items: [(w₁,v₁), (w₂,v₂), ..., (wₙ,vₙ)]
Capacity: W

Decision Tree for Item i:
                    Item i
                   /      \
            TAKE (if w≤W)  SKIP
                /              \
         v+f(i+1,W-w)      f(i+1,W)
              ↓                 ↓
        Use capacity      Don't use capacity
```

#### Python Implementation

```python
def knapsack_01(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            # Take item i-1 if possible
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]

def knapsack_with_items(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    # Fill DP table
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    # Backtrack to find items
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(i-1)
            w -= weights[i-1]
    
    return dp[n][capacity], selected[::-1]

# Space-Optimized Version
def knapsack_optimized(weights, values, capacity):
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        # Traverse backwards to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]

# Test
weights = [2, 3, 4, 5]
values = [3, 4, 5, 6]
capacity = 8

print(f"Max value: {knapsack_01(weights, values, capacity)}")
max_val, items = knapsack_with_items(weights, values, capacity)
print(f"Max value: {max_val}, Items: {items}")
print(f"Max value (optimized): {knapsack_optimized(weights, values, capacity)}")
```

#### C Implementation

```c
#include <stdio.h>
#include <string.h>

#define MAX(a, b) ((a) > (b) ? (a) : (b))

int knapsack_01(int weights[], int values[], int n, int capacity) {
    int dp[n + 1][capacity + 1];
    
    // Initialize base cases
    memset(dp, 0, sizeof(dp));
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            dp[i][w] = dp[i-1][w];
            
            if (weights[i-1] <= w) {
                dp[i][w] = MAX(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1]);
            }
        }
    }
    
    return dp[n][capacity];
}

int main() {
    int weights[] = {2, 3, 4, 5};
    int values[] = {3, 4, 5, 6};
    int n = 4;
    int capacity = 8;
    
    printf("Max value: %d\n", knapsack_01(weights, values, n, capacity));
    return 0;
}
```

#### C++ Implementation

```cpp
#include <iostream>
#include <vector>
#include <algorithm>

class Knapsack {
public:
    static int solve(const std::vector<int>& weights, 
                    const std::vector<int>& values, 
                    int capacity) {
        int n = weights.size();
        std::vector<std::vector<int>> dp(n + 1, 
                                        std::vector<int>(capacity + 1, 0));
        
        for (int i = 1; i <= n; i++) {
            for (int w = 0; w <= capacity; w++) {
                dp[i][w] = dp[i-1][w];
                
                if (weights[i-1] <= w) {
                    dp[i][w] = std::max(dp[i][w], 
                                       dp[i-1][w - weights[i-1]] + values[i-1]);
                }
            }
        }
        
        return dp[n][capacity];
    }
    
    static int solveOptimized(const std::vector<int>& weights,
                             const std::vector<int>& values,
                             int capacity) {
        std::vector<int> dp(capacity + 1, 0);
        
        for (size_t i = 0; i < weights.size(); i++) {
            for (int w = capacity; w >= weights[i]; w--) {
                dp[w] = std::max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        
        return dp[capacity];
    }
};

int main() {
    std::vector<int> weights = {2, 3, 4, 5};
    std::vector<int> values = {3, 4, 5, 6};
    int capacity = 8;
    
    std::cout << "Max value: " << Knapsack::solve(weights, values, capacity) << std::endl;
    std::cout << "Max value (optimized): " << Knapsack::solveOptimized(weights, values, capacity) << std::endl;
    return 0;
}
```

#### Go Implementation

```go
package main

import "fmt"

func knapsack01(weights, values []int, capacity int) int {
    n := len(weights)
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }
    
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            dp[i][w] = dp[i-1][w]
            
            if weights[i-1] <= w {
                take := dp[i-1][w-weights[i-1]] + values[i-1]
                if take > dp[i][w] {
                    dp[i][w] = take
                }
            }
        }
    }
    
    return dp[n][capacity]
}

func knapsackOptimized(weights, values []int, capacity int) int {
    dp := make([]int, capacity+1)
    
    for i := 0; i < len(weights); i++ {
        for w := capacity; w >= weights[i]; w-- {
            take := dp[w-weights[i]] + values[i]
            if take > dp[w] {
                dp[w] = take
            }
        }
    }
    
    return dp[capacity]
}

func main() {
    weights := []int{2, 3, 4, 5}
    values := []int{3, 4, 5, 6}
    capacity := 8
    
    fmt.Printf("Max value: %d\n", knapsack01(weights, values, capacity))
    fmt.Printf("Max value (optimized): %d\n", knapsackOptimized(weights, values, capacity))
}
```

#### Rust Implementation

```rust
use std::cmp::max;

fn knapsack_01(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=capacity {
            dp[i][w] = dp[i - 1][w];
            
            if weights[i - 1] <= w {
                dp[i][w] = max(dp[i][w], 
                              dp[i - 1][w - weights[i - 1]] + values[i - 1]);
            }
        }
    }
    
    dp[n][capacity]
}

fn knapsack_optimized(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let mut dp = vec![0; capacity + 1];
    
    for i in 0..weights.len() {
        for w in (weights[i]..=capacity).rev() {
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    dp[capacity]
}

fn main() {
    let weights = vec![2, 3, 4, 5];
    let values = vec![3, 4, 5, 6];
    let capacity = 8;
    
    println!("Max value: {}", knapsack_01(&weights, &values, capacity));
    println!("Max value (optimized): {}", knapsack_optimized(&weights, &values, capacity));
}
```

---

## Real-World Use Cases

### 1. **Bioinformatics & Computational Biology**
- DNA sequence alignment using LCS and edit distance
- Protein structure prediction
- Gene prediction and phylogenetic tree construction
- RNA folding optimization

### 2. **Financial Markets & Trading**
- Portfolio optimization (Knapsack variants)
- Option pricing models
- Maximum profit from stock transactions
- Arbitrage detection in currency exchange

### 3. **Natural Language Processing**
- Spell checking and autocorrect (Edit distance)
- Machine translation alignment
- Text difference algorithms (diff tools)
- Speech recognition with Hidden Markov Models

### 4. **Operations Research & Logistics**
- Resource allocation in manufacturing
- Cutting stock problem (minimize waste)
- Vehicle routing optimization
- Project scheduling (PERT/CPM)

### 5. **Computer Graphics & Image Processing**
- Seam carving for content-aware image resizing
- Image compression algorithms
- Texture synthesis
- 3D mesh optimization

### 6. **Telecommunications**
- Network routing optimization
- Bandwidth allocation
- Error correction codes
- Signal processing

### 7. **Game Development**
- Pathfinding algorithms
- AI decision trees
- Inventory management systems
- Turn-based strategy optimization

### 8. **Compiler Design**
- Code optimization
- Register allocation
- Parsing algorithms
- Dead code elimination

### 9. **Data Compression**
- Huffman coding optimization
- LZW compression
- Video codec optimization
- Database query optimization

### 10. **Machine Learning**
- Hidden Markov Models training
- Sequence labeling (CRF)
- Reinforcement learning (value iteration)
- Neural network backpropagation optimization

---

## Advanced Techniques

### 1. State Compression

**Bitmask DP:**
```
Problem: Traveling Salesman Problem (TSP)

State: (current_city, visited_cities_bitmask)

Example with 4 cities (0,1,2,3):
  Bitmask 1011₂ = 11₁₀ means cities 0,1,3 visited

DP Table Structure:
  dp[mask][city] = minimum cost to reach 'city' 
                   with 'mask' cities visited

Transition:
  From city 'u' to city 'v':
  new_mask = mask | (1 << v)
  dp[new_mask][v] = min(dp[new_mask][v], 
                        dp[mask][u] + dist[u][v])
```

### 2. Convex Hull Trick

**Optimizing DP with Lines:**
```
Problem: dp[i] = min(dp[j] + cost(j, i)) for j < i

When cost function is convex/concave:
  - Maintain envelope of optimal lines
  - Query using binary search
  - Time: O(n log n) instead of O(n²)

Geometric Interpretation:
       Value
         ↑
         │     Line j₃
         │    /
         │   /  Line j₂
         │  /  /
         │ /  /  Line j₁
         │/  /  /
         └─────────→ Position i

Only keep lines on convex hull
```

### 3. Divide and Conquer DP

**When transitions satisfy quadrangle inequality:**
```
Optimization: dp[i][j] = min(dp[i][k] + dp[k+1][j] + cost[i][j])

Observation: opt[i][j-1] ≤ opt[i][j] ≤ opt[i+1][j]

Divide and Conquer approach:
  1. Compute middle column
  2. Recursively solve left and right halves
  3. Time: O(n² log n) instead of O(n³)

Structure:
       j
    ───────────
  i │ ╲ ╲ ╲ ╲ │
    │  ╲ ╲ ╲ ╲│
    │   ╲ ╲ ╲ │
    │    ╲ ╲ ╲│
    └─────────┘
  
  Optimal k moves monotonically
```

### 4. Matrix Chain Multiplication Pattern

**Optimal Parenthesization:**
```
Problem: Multiply matrices A₁×A₂×...×Aₙ optimally

State: dp[i][j] = min multiplications for Aᵢ...Aⱼ

Partition at k:
  dp[i][j] = min(dp[i][k] + dp[k+1][j] + cost(i,k,j))

Fill Order (by chain length):
  Length 1: dp[i][i] = 0
  Length 2: dp[i][i+1]
  Length 3: dp[i][i+2]
  ...
  Length n: dp[1][n]

Diagonal filling pattern:
    1  2  3  4  5
  ┌──┬──┬──┬──┬──┐
1 │ 0│② │④│⑥│⑧ │
  ├──┼──┼──┼──┼──┤
2 │  │ 0│③│⑤ │⑦ │
  ├──┼──┼──┼──┼──┤
3 │  │  │ 0│④│⑥ │
  ├──┼──┼──┼──┼──┤
4 │  │  │  │ 0│⑤ │
  ├──┼──┼──┼──┼──┤
5 │  │  │  │  │ 0│
  └──┴──┴──┴──┴──┘
```

### 5. DP on Trees

**Tree DP Structure:**
```
Problem: Maximum independent set on tree

State: 
  dp[node][0] = max value excluding node
  dp[node][1] = max value including node

Recurrence:
  dp[node][1] = value[node] + Σ dp[child][0]
  dp[node][0] = Σ max(dp[child][0], dp[child][1])

Tree Structure:
           Root
          /  |  \
         /   |   \
        A    B    C
       / \   |   / \
      D   E  F  G   H

DFS Post-order traversal:
  Process leaves first (D,E,F,G,H)
  Then internal nodes (A,B,C)
  Finally root
```

### 6. Digit DP

**Counting numbers with constraints:**
```
Problem: Count numbers ≤ N with property P

State: dp[pos][tight][state]
  pos: current digit position
  tight: whether we're bounded by N
  state: problem-specific state

Example: Count numbers ≤ 12345 with sum of digits = 10

Digit tree exploration:
         Root
        /  |  \
       /   |   \
      0    1    2...9  (first digit)
     /|\  /|\  
    0 1.. (second digit)
    
Tight constraint propagation:
  If N = 12345 and we choose 1:
    Next digit can be 0-2 (tight)
  If we choose 0:
    Next digit can be 0-9 (not tight)
```

---

## Complexity Analysis

### Space Optimization Techniques

**1. Rolling Array:**
```
2D → 1D transformation

I've created a comprehensive guide on Dynamic Programming with:

## What's Included:

1. **Core Concepts**
   - Clear definitions with visual explanations
   - Two fundamental pillars explained
   - Why DP works better than naive recursion

2. **Visual Learning with ASCII Diagrams**
   - State space exploration
   - Fibonacci tree comparison (with/without memoization)
   - Grid traversal patterns
   - Knapsack decision tables
   - LCS matrix construction

3. **Problem-Solving Patterns**
   - Linear DP (1D states)
   - Grid DP (2D states)
   - Sequence DP
   - Knapsack variants

4. **Complete Implementations** in all 5 languages:
   - **Fibonacci** - Basic DP introduction (3 approaches each)
   - **Longest Common Subsequence** - 2D DP with backtracking
   - **0/1 Knapsack** - Classic optimization problem

5. **Real-World Applications**
   - 10 major domains with specific use cases
   - From bioinformatics to machine learning
   - Practical industry applications

6. **Advanced Techniques**
   - State compression with bitmasks
   - Convex hull trick
   - Divide and conquer DP
   - Matrix chain multiplication
   - Tree DP
   - Digit DP

Each implementation includes proper comments and shows different approaches (memoization, tabulation, space-optimized). The ASCII diagrams illustrate the core mechanics of how DP builds solutions incrementally.

Would you like me to add more specific problems or go deeper into any particular pattern?