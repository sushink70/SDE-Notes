# Dynamic Programming Problem Patterns Guide

## Table of Contents
1. [Introduction to Dynamic Programming](#introduction)
2. [Pattern 1: Linear DP](#linear-dp)
3. [Pattern 2: Grid/2D DP](#grid-2d-dp)
4. [Pattern 3: Knapsack Problems](#knapsack-problems)
5. [Pattern 4: Longest Common Subsequence (LCS)](#longest-common-subsequence)
6. [Pattern 5: Palindrome Problems](#palindrome-problems)
7. [Pattern 6: Interval DP](#interval-dp)
8. [Pattern 7: Tree DP](#tree-dp)
9. [Pattern 8: State Machine DP](#state-machine-dp)
10. [Pattern 9: Digit DP](#digit-dp)
11. [Pattern 10: Bitmask DP](#bitmask-dp)

## Introduction to Dynamic Programming {#introduction}

Dynamic Programming (DP) is an optimization technique that solves complex problems by breaking them down into simpler subproblems. The key principles are:

- **Optimal Substructure**: The optimal solution contains optimal solutions to subproblems
- **Overlapping Subproblems**: The same subproblems are solved multiple times
- **Memoization**: Store solutions to avoid recomputation

### General Approach
1. Identify the state space
2. Define the recurrence relation
3. Determine base cases
4. Choose between top-down (memoization) or bottom-up (tabulation)

---

## Pattern 1: Linear DP {#linear-dp}

Linear DP problems involve making decisions at each position in a sequence.

### Problem: Fibonacci Sequence

**Python Implementation:**
```python
def fibonacci_memo(n, memo={}):
    """Top-down approach with memoization"""
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]

def fibonacci_tabulation(n):
    """Bottom-up approach"""
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

def fibonacci_optimized(n):
    """Space-optimized version"""
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

fn fibonacci_memo(n: i32, memo: &mut HashMap<i32, i64>) -> i64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    let result = match n {
        0 | 1 => n as i64,
        _ => fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo),
    };
    
    memo.insert(n, result);
    result
}

fn fibonacci_tabulation(n: i32) -> i64 {
    if n <= 1 {
        return n as i64;
    }
    
    let mut dp = vec![0i64; (n + 1) as usize];
    dp[1] = 1;
    
    for i in 2..=n as usize {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n as usize]
}

fn fibonacci_optimized(n: i32) -> i64 {
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

### Problem: House Robber

**Python Implementation:**
```python
def rob(nums):
    """
    You cannot rob two adjacent houses.
    Find maximum amount you can rob.
    """
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    # dp[i] = maximum money we can rob up to house i
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    
    for i in range(2, len(nums)):
        # Either rob current house + best from i-2, or skip current house
        dp[i] = max(dp[i-1], dp[i-2] + nums[i])
    
    return dp[-1]

def rob_optimized(nums):
    """Space-optimized version"""
    if not nums:
        return 0
    
    prev2 = prev1 = 0
    for num in nums:
        current = max(prev1, prev2 + num)
        prev2, prev1 = prev1, current
    
    return prev1
```

**Rust Implementation:**
```rust
fn rob(nums: Vec<i32>) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    if nums.len() == 1 {
        return nums[0];
    }
    
    let mut dp = vec![0; nums.len()];
    dp[0] = nums[0];
    dp[1] = nums[0].max(nums[1]);
    
    for i in 2..nums.len() {
        dp[i] = dp[i - 1].max(dp[i - 2] + nums[i]);
    }
    
    dp[nums.len() - 1]
}

fn rob_optimized(nums: Vec<i32>) -> i32 {
    let (mut prev2, mut prev1) = (0, 0);
    
    for num in nums {
        let current = prev1.max(prev2 + num);
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}
```

---

## Pattern 2: Grid/2D DP {#grid-2d-dp}

Grid DP problems involve navigating through a 2D matrix with certain constraints.

### Problem: Unique Paths

**Python Implementation:**
```python
def unique_paths(m, n):
    """Find number of unique paths from top-left to bottom-right"""
    dp = [[1] * n for _ in range(m)]
    
    # First row and column are all 1s (only one way to reach them)
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i-1][j] + dp[i][j-1]
    
    return dp[m-1][n-1]

def unique_paths_optimized(m, n):
    """Space-optimized version using 1D array"""
    dp = [1] * n
    
    for i in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j-1]
    
    return dp[n-1]

def unique_paths_with_obstacles(obstacle_grid):
    """Unique paths with obstacles (0 = empty, 1 = obstacle)"""
    if not obstacle_grid or obstacle_grid[0][0] == 1:
        return 0
    
    m, n = len(obstacle_grid), len(obstacle_grid[0])
    dp = [[0] * n for _ in range(m)]
    dp[0][0] = 1
    
    # Fill first row
    for j in range(1, n):
        dp[0][j] = dp[0][j-1] if obstacle_grid[0][j] == 0 else 0
    
    # Fill first column
    for i in range(1, m):
        dp[i][0] = dp[i-1][0] if obstacle_grid[i][0] == 0 else 0
    
    # Fill rest of the grid
    for i in range(1, m):
        for j in range(1, n):
            if obstacle_grid[i][j] == 0:
                dp[i][j] = dp[i-1][j] + dp[i][j-1]
    
    return dp[m-1][n-1]
```

**Rust Implementation:**
```rust
fn unique_paths(m: i32, n: i32) -> i32 {
    let (m, n) = (m as usize, n as usize);
    let mut dp = vec![vec![1; n]; m];
    
    for i in 1..m {
        for j in 1..n {
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1];
        }
    }
    
    dp[m - 1][n - 1]
}

fn unique_paths_optimized(m: i32, n: i32) -> i32 {
    let n = n as usize;
    let mut dp = vec![1; n];
    
    for _ in 1..m {
        for j in 1..n {
            dp[j] += dp[j - 1];
        }
    }
    
    dp[n - 1]
}

fn unique_paths_with_obstacles(obstacle_grid: Vec<Vec<i32>>) -> i32 {
    if obstacle_grid.is_empty() || obstacle_grid[0][0] == 1 {
        return 0;
    }
    
    let (m, n) = (obstacle_grid.len(), obstacle_grid[0].len());
    let mut dp = vec![vec![0; n]; m];
    dp[0][0] = 1;
    
    // Fill first row
    for j in 1..n {
        dp[0][j] = if obstacle_grid[0][j] == 0 { dp[0][j - 1] } else { 0 };
    }
    
    // Fill first column
    for i in 1..m {
        dp[i][0] = if obstacle_grid[i][0] == 0 { dp[i - 1][0] } else { 0 };
    }
    
    // Fill rest of the grid
    for i in 1..m {
        for j in 1..n {
            if obstacle_grid[i][j] == 0 {
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1];
            }
        }
    }
    
    dp[m - 1][n - 1]
}
```

---

## Pattern 3: Knapsack Problems {#knapsack-problems}

Knapsack problems involve selecting items with given weights and values to maximize value within weight constraint.

### 0/1 Knapsack

**Python Implementation:**
```python
def knapsack_01(weights, values, capacity):
    """0/1 Knapsack: each item can be taken at most once"""
    n = len(weights)
    # dp[i][w] = maximum value using first i items with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            # Take item i-1 if possible
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]

def knapsack_01_optimized(weights, values, capacity):
    """Space-optimized version"""
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        # Iterate backwards to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]

def knapsack_01_with_items(weights, values, capacity):
    """Returns both max value and selected items"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    
    # Backtrack to find selected items
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(i-1)
            w -= weights[i-1]
    
    return dp[n][capacity], selected[::-1]
```

**Rust Implementation:**
```rust
fn knapsack_01(weights: Vec<i32>, values: Vec<i32>, capacity: i32) -> i32 {
    let n = weights.len();
    let cap = capacity as usize;
    let mut dp = vec![vec![0; cap + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=cap {
            dp[i][w] = dp[i - 1][w];
            
            if weights[i - 1] as usize <= w {
                let new_val = dp[i - 1][w - weights[i - 1] as usize] + values[i - 1];
                dp[i][w] = dp[i][w].max(new_val);
            }
        }
    }
    
    dp[n][cap]
}

fn knapsack_01_optimized(weights: Vec<i32>, values: Vec<i32>, capacity: i32) -> i32 {
    let cap = capacity as usize;
    let mut dp = vec![0; cap + 1];
    
    for i in 0..weights.len() {
        for w in (weights[i] as usize..=cap).rev() {
            dp[w] = dp[w].max(dp[w - weights[i] as usize] + values[i]);
        }
    }
    
    dp[cap]
}

fn knapsack_01_with_items(weights: Vec<i32>, values: Vec<i32>, capacity: i32) -> (i32, Vec<usize>) {
    let n = weights.len();
    let cap = capacity as usize;
    let mut dp = vec![vec![0; cap + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=cap {
            dp[i][w] = dp[i - 1][w];
            if weights[i - 1] as usize <= w {
                let new_val = dp[i - 1][w - weights[i - 1] as usize] + values[i - 1];
                dp[i][w] = dp[i][w].max(new_val);
            }
        }
    }
    
    // Backtrack
    let mut selected = Vec::new();
    let mut w = cap;
    for i in (1..=n).rev() {
        if dp[i][w] != dp[i - 1][w] {
            selected.push(i - 1);
            w -= weights[i - 1] as usize;
        }
    }
    
    selected.reverse();
    (dp[n][cap], selected)
}
```

### Unbounded Knapsack

**Python Implementation:**
```python
def unbounded_knapsack(weights, values, capacity):
    """Unbounded Knapsack: unlimited quantity of each item"""
    dp = [0] * (capacity + 1)
    
    for w in range(1, capacity + 1):
        for i in range(len(weights)):
            if weights[i] <= w:
                dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]

def coin_change(coins, amount):
    """Minimum coins to make amount (unbounded knapsack variant)"""
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for coin in coins:
        for amt in range(coin, amount + 1):
            if dp[amt - coin] != float('inf'):
                dp[amt] = min(dp[amt], dp[amt - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

def coin_change_ways(coins, amount):
    """Number of ways to make amount"""
    dp = [0] * (amount + 1)
    dp[0] = 1
    
    for coin in coins:
        for amt in range(coin, amount + 1):
            dp[amt] += dp[amt - coin]
    
    return dp[amount]
```

**Rust Implementation:**
```rust
fn unbounded_knapsack(weights: Vec<i32>, values: Vec<i32>, capacity: i32) -> i32 {
    let cap = capacity as usize;
    let mut dp = vec![0; cap + 1];
    
    for w in 1..=cap {
        for i in 0..weights.len() {
            if weights[i] as usize <= w {
                dp[w] = dp[w].max(dp[w - weights[i] as usize] + values[i]);
            }
        }
    }
    
    dp[cap]
}

fn coin_change(coins: Vec<i32>, amount: i32) -> i32 {
    let amt = amount as usize;
    let mut dp = vec![i32::MAX; amt + 1];
    dp[0] = 0;
    
    for coin in coins {
        for a in coin as usize..=amt {
            if dp[a - coin as usize] != i32::MAX {
                dp[a] = dp[a].min(dp[a - coin as usize] + 1);
            }
        }
    }
    
    if dp[amt] == i32::MAX { -1 } else { dp[amt] }
}

fn coin_change_ways(coins: Vec<i32>, amount: i32) -> i32 {
    let amt = amount as usize;
    let mut dp = vec![0; amt + 1];
    dp[0] = 1;
    
    for coin in coins {
        for a in coin as usize..=amt {
            dp[a] += dp[a - coin as usize];
        }
    }
    
    dp[amt]
}
```

---

## Pattern 4: Longest Common Subsequence (LCS) {#longest-common-subsequence}

LCS problems involve finding common patterns between sequences.

### Classic LCS

**Python Implementation:**
```python
def lcs_length(text1, text2):
    """Length of Longest Common Subsequence"""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def lcs_string(text1, text2):
    """Actual LCS string"""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Backtrack to build LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if text1[i-1] == text2[j-1]:
            lcs.append(text1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))

def edit_distance(word1, word2):
    """Minimum edit distance (insertions, deletions, substitutions)"""
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # deletion
                    dp[i][j-1],    # insertion
                    dp[i-1][j-1]   # substitution
                )
    
    return dp[m][n]

def longest_increasing_subsequence(nums):
    """Length of LIS using DP"""
    if not nums:
        return 0
    
    n = len(nums)
    dp = [1] * n
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

def longest_increasing_subsequence_optimized(nums):
    """LIS using binary search (O(n log n))"""
    if not nums:
        return 0
    
    from bisect import bisect_left
    
    tails = []
    for num in nums:
        pos = bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    
    return len(tails)
```

**Rust Implementation:**
```rust
fn lcs_length(text1: String, text2: String) -> i32 {
    let (s1, s2) = (text1.chars().collect::<Vec<_>>(), text2.chars().collect::<Vec<_>>());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

fn lcs_string(text1: String, text2: String) -> String {
    let (s1, s2) = (text1.chars().collect::<Vec<_>>(), text2.chars().collect::<Vec<_>>());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    // Backtrack
    let mut lcs = Vec::new();
    let (mut i, mut j) = (m, n);
    while i > 0 && j > 0 {
        if s1[i - 1] == s2[j - 1] {
            lcs.push(s1[i - 1]);
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

fn edit_distance(word1: String, word2: String) -> i32 {
    let (s1, s2) = (word1.chars().collect::<Vec<_>>(), word2.chars().collect::<Vec<_>>());
    let (m, n) = (s1.len(), s2.len());
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Initialize base cases
    for i in 0..=m {
        dp[i][0] = i as i32;
    }
    for j in 0..=n {
        dp[0][j] = j as i32;
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + dp[i - 1][j].min(dp[i][j - 1]).min(dp[i - 1][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

fn longest_increasing_subsequence(nums: Vec<i32>) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    
    let n = nums.len();
    let mut dp = vec![1; n];
    
    for i in 1..n {
        for j in 0..i {
            if nums[j] < nums[i] {
                dp[i] = dp[i].max(dp[j] + 1);
            }
        }
    }
    
    *dp.iter().max().unwrap()
}

fn longest_increasing_subsequence_optimized(nums: Vec<i32>) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    
    let mut tails = Vec::new();
    
    for num in nums {
        match tails.binary_search(&num) {
            Ok(_) => {}, // num already exists
            Err(pos) => {
                if pos == tails.len() {
                    tails.push(num);
                } else {
                    tails[pos] = num;
                }
            }
        }
    }
    
    tails.len() as i32
}
```

---

## Pattern 5: Palindrome Problems {#palindrome-problems}

Palindrome problems involve finding palindromic subsequences or substrings.

**Python Implementation:**
```python
def longest_palindromic_subsequence(s):
    """Length of longest palindromic subsequence"""
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    
    # Every single character is a palindrome of length 1
    for i in range(n):
        dp[i][i] = 1
    
    # Check for palindromes of length 2 to n
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i+1][j-1] + 2
            else:
                dp[i][j] = max(dp[i+1][j], dp[i][j-1])
    
    return dp[0][n-1]

def longest_palindromic_substring(s):
    """Longest palindromic substring"""
    if not s:
        return ""
    
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start = 0
    max_len = 1
    
    # Single characters are palindromes
    for i in range(n):
        dp[i][i] = True
    
    # Check for palindromes of length 2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            dp[i][i + 1] = True
            start = i
            max_len = 2
    
    # Check for palindromes of length 3 to n
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            if s[i] == s[j] and dp[i + 1][j - 1]:
                dp[i][j] = True
                start = i
                max_len = length
    
    return s[start:start + max_len]

def count_palindromic_substrings(s):
    """Count all palindromic substrings"""
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    count = 0
    
    # Single characters
    for i in range(n):
        dp[i][i] = True
        count += 1
    
    # Length 2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            dp[i][i + 1] = True
            count += 1
    
    # Length 3+
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and dp[i + 1][j - 1]:
                dp[i][j] = True
                count += 1
    
    return count

def palindrome_partitioning_min_cuts(s):
    """Minimum cuts needed to partition string into palindromes"""
    n = len(s)
    
    # Build palindrome table
    is_palindrome = [[False] * n for _ in range(n)]
    
    # Single characters
    for i in range(n):
        is_palindrome[i][i] = True
    
    # Length 2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            is_palindrome[i][i + 1] = True
    
    # Length 3+
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                is_palindrome[i][j] = is_palindrome[i + 1][j - 1]
    
    # DP for minimum cuts
    cuts = [0] * n
    for i in range(n):
        if is_palindrome[0][i]:
            cuts[i] = 0
        else:
            cuts[i] = i  # worst case: i cuts
            for j in range(i):
                if is_palindrome[j + 1][i]:
                    cuts[i] = min(cuts[i], cuts[j] + 1)
    
    return cuts[n - 1]
```

**Rust Implementation:**
```rust
fn longest_palindromic_subsequence(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut dp = vec![vec![0; n]; n];
    
    // Single characters
    for i in 0..n {
        dp[i][i] = 1;
    }
    
    // Length 2 to n
    for length in 2..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            
            if chars[i] == chars[j] {
                if length == 2 {
                    dp[i][j] = 2;
                } else {
                    dp[i][j] = dp[i + 1][j - 1] + 2;
                }
            } else {
                dp[i][j] = dp[i + 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[0][n - 1]
}

fn longest_palindromic_substring(s: String) -> String {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    if n == 0 {
        return String::new();
    }
    
    let mut dp = vec![vec![false; n]; n];
    let mut start = 0;
    let mut max_len = 1;
    
    // Single characters
    for i in 0..n {
        dp[i][i] = true;
    }
    
    // Length 2
    for i in 0..n - 1 {
        if chars[i] == chars[i + 1] {
            dp[i][i + 1] = true;
            start = i;
            max_len = 2;
        }
    }
    
    // Length 3+
    for length in 3..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            if chars[i] == chars[j] && dp[i + 1][j - 1] {
                dp[i][j] = true;
                start = i;
                max_len = length;
            }
        }
    }
    
    chars[start..start + max_len].iter().collect()
}

fn count_palindromic_substrings(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut dp = vec![vec![false; n]; n];
    let mut count = 0;
    
    // Single characters
    for i in 0..n {
        dp[i][i] = true;
        count += 1;
    }
    
    // Length 2
    for i in 0..n - 1 {
        if chars[i] == chars[i + 1] {
            dp[i][i + 1] = true;
            count += 1;
        }
    }
    
    // Length 3+
    for length in 3..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            if chars[i] == chars[j] && dp[i + 1][j - 1] {
                dp[i][j] = true;
                count += 1;
            }
        }
    }
    
    count
}

fn palindrome_partitioning_min_cuts(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    // Build palindrome table
    let mut is_palindrome = vec![vec![false; n]; n];
    
    // Single characters
    for i in 0..n {
        is_palindrome[i][i] = true;
    }
    
    // Length 2
    for i in 0..n - 1 {
        if chars[i] == chars[i + 1] {
            is_palindrome[i][i + 1] = true;
        }
    }
    
    // Length 3+
    for length in 3..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            if chars[i] == chars[j] {
                is_palindrome[i][j] = is_palindrome[i + 1][j - 1];
            }
        }
    }
    
    // DP for minimum cuts
    let mut cuts = vec![0; n];
    for i in 0..n {
        if is_palindrome[0][i] {
            cuts[i] = 0;
        } else {
            cuts[i] = i as i32;
            for j in 0..i {
                if is_palindrome[j + 1][i] {
                    cuts[i] = cuts[i].min(cuts[j] + 1);
                }
            }
        }
    }
    
    cuts[n - 1]
}
```

---

## Pattern 6: Interval DP {#interval-dp}

Interval DP problems involve finding optimal solutions over intervals or ranges.

### Matrix Chain Multiplication

**Python Implementation:**
```python
def matrix_chain_multiplication(dimensions):
    """
    Find minimum scalar multiplications needed to multiply chain of matrices.
    dimensions[i-1] x dimensions[i] is the dimension of matrix i.
    """
    n = len(dimensions) - 1  # number of matrices
    if n < 2:
        return 0
    
    # dp[i][j] = minimum multiplications to multiply matrices from i to j
    dp = [[0] * n for _ in range(n)]
    
    # length is chain length
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all possible split points
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                       dimensions[i] * dimensions[k+1] * dimensions[j+1])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]

def matrix_chain_order(dimensions):
    """Returns both minimum cost and optimal parenthesization"""
    n = len(dimensions) - 1
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                       dimensions[i] * dimensions[k+1] * dimensions[j+1])
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    def build_solution(i, j):
        if i == j:
            return f"M{i}"
        else:
            k = split[i][j]
            left = build_solution(i, k)
            right = build_solution(k+1, j)
            return f"({left} * {right})"
    
    return dp[0][n-1], build_solution(0, n-1)

def burst_balloons(nums):
    """
    Burst balloons to get maximum coins.
    When you burst balloon i, you get nums[left]*nums[i]*nums[right] coins.
    """
    # Add boundary balloons with value 1
    balloons = [1] + nums + [1]
    n = len(balloons)
    
    # dp[i][j] = maximum coins from bursting balloons between i and j (exclusive)
    dp = [[0] * n for _ in range(n)]
    
    # length is the gap between boundaries
    for length in range(2, n):
        for left in range(n - length):
            right = left + length
            
            # Try bursting each balloon k between left and right
            for k in range(left + 1, right):
                coins = balloons[left] * balloons[k] * balloons[right]
                dp[left][right] = max(dp[left][right], 
                                    dp[left][k] + dp[k][right] + coins)
    
    return dp[0][n-1]

def minimum_cost_tree_from_leaf_values(arr):
    """Build binary tree with minimum sum of non-leaf values"""
    n = len(arr)
    
    # max_val[i][j] = maximum value in arr[i:j+1]
    max_val = [[0] * n for _ in range(n)]
    for i in range(n):
        max_val[i][i] = arr[i]
        for j in range(i + 1, n):
            max_val[i][j] = max(max_val[i][j-1], arr[j])
    
    # dp[i][j] = minimum sum for subarray arr[i:j+1]
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + max_val[i][k] * max_val[k+1][j]
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]
```

**Rust Implementation:**
```rust
fn matrix_chain_multiplication(dimensions: Vec<i32>) -> i32 {
    let n = dimensions.len() - 1;
    if n < 2 {
        return 0;
    }
    
    let mut dp = vec![vec![0; n]; n];
    
    for length in 2..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            dp[i][j] = i32::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + 
                          dimensions[i] * dimensions[k + 1] * dimensions[j + 1];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    
    dp[0][n - 1]
}

fn burst_balloons(nums: Vec<i32>) -> i32 {
    let mut balloons = vec![1];
    balloons.extend(nums);
    balloons.push(1);
    let n = balloons.len();
    
    let mut dp = vec![vec![0; n]; n];
    
    for length in 2..n {
        for left in 0..=n - length - 1 {
            let right = left + length;
            
            for k in left + 1..right {
                let coins = balloons[left] * balloons[k] * balloons[right];
                dp[left][right] = dp[left][right].max(
                    dp[left][k] + dp[k][right] + coins
                );
            }
        }
    }
    
    dp[0][n - 1]
}

fn minimum_cost_tree_from_leaf_values(arr: Vec<i32>) -> i32 {
    let n = arr.len();
    
    // Build max_val table
    let mut max_val = vec![vec![0; n]; n];
    for i in 0..n {
        max_val[i][i] = arr[i];
        for j in i + 1..n {
            max_val[i][j] = max_val[i][j - 1].max(arr[j]);
        }
    }
    
    let mut dp = vec![vec![0; n]; n];
    
    for length in 2..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            dp[i][j] = i32::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + max_val[i][k] * max_val[k + 1][j];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    
    dp[0][n - 1]
}
```

---

## Pattern 7: Tree DP {#tree-dp}

Tree DP problems involve making optimal decisions at each node considering subtrees.

**Python Implementation:**
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def rob_tree(root):
    """House Robber in Binary Tree"""
    def dfs(node):
        if not node:
            return (0, 0)  # (rob_node, not_rob_node)
        
        left_rob, left_not_rob = dfs(node.left)
        right_rob, right_not_rob = dfs(node.right)
        
        # If we rob current node, we can't rob children
        rob_current = node.val + left_not_rob + right_not_rob
        
        # If we don't rob current node, we can choose optimally for children
        not_rob_current = max(left_rob, left_not_rob) + max(right_rob, right_not_rob)
        
        return (rob_current, not_rob_current)
    
    return max(dfs(root))

def diameter_of_binary_tree(root):
    """Diameter of binary tree (longest path between any two nodes)"""
    def dfs(node):
        if not node:
            return 0
        
        left_depth = dfs(node.left)
        right_depth = dfs(node.right)
        
        # Update global diameter
        nonlocal max_diameter
        max_diameter = max(max_diameter, left_depth + right_depth)
        
        # Return depth of current subtree
        return 1 + max(left_depth, right_depth)
    
    max_diameter = 0
    dfs(root)
    return max_diameter

def binary_tree_maximum_path_sum(root):
    """Maximum path sum in binary tree"""
    def dfs(node):
        if not node:
            return 0
        
        # Get maximum contribution from left and right subtrees
        # If negative, don't include them (use 0)
        left_gain = max(dfs(node.left), 0)
        right_gain = max(dfs(node.right), 0)
        
        # Maximum path sum including current node as highest point
        current_max = node.val + left_gain + right_gain
        
        # Update global maximum
        nonlocal max_sum
        max_sum = max(max_sum, current_max)
        
        # Return maximum gain if we continue path through current node
        return node.val + max(left_gain, right_gain)
    
    max_sum = float('-inf')
    dfs(root)
    return max_sum

def longest_univalue_path(root):
    """Longest path with same values"""
    def dfs(node):
        if not node:
            return 0
        
        left_length = dfs(node.left)
        right_length = dfs(node.right)
        
        # Reset lengths if values don't match
        left_path = left_length + 1 if node.left and node.left.val == node.val else 0
        right_path = right_length + 1 if node.right and node.right.val == node.val else 0
        
        # Update global maximum (path through current node)
        nonlocal max_path
        max_path = max(max_path, left_path + right_path)
        
        # Return longer path continuing from current node
        return max(left_path, right_path)
    
    max_path = 0
    dfs(root)
    return max_path

def count_good_nodes(root):
    """Count nodes where all nodes in path from root have smaller values"""
    def dfs(node, max_val):
        if not node:
            return 0
        
        count = 1 if node.val >= max_val else 0
        new_max = max(max_val, node.val)
        
        count += dfs(node.left, new_max)
        count += dfs(node.right, new_max)
        
        return count
    
    return dfs(root, float('-inf'))

# For general trees (not binary)
def tree_dp_general():
    """Template for general tree DP"""
    # Example: Maximum independent set in tree
    def max_independent_set(adj, node, parent):
        """
        adj: adjacency list representation
        Returns (include_node, exclude_node)
        """
        include = 1  # Include current node
        exclude = 0  # Exclude current node
        
        for neighbor in adj[node]:
            if neighbor != parent:
                inc_child, exc_child = max_independent_set(adj, neighbor, node)
                include += exc_child  # If we include node, exclude children
                exclude += max(inc_child, exc_child)  # If we exclude node, choose optimally
        
        return (include, exclude)
    
    # Usage example for a tree with n nodes
    # return max(max_independent_set(adj, 0, -1))
    pass
```

**Rust Implementation:**
```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    #[inline]
    pub fn new(val: i32) -> Self {
        TreeNode {
            val,
            left: None,
            right: None,
        }
    }
}

fn rob_tree(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>) -> (i32, i32) {
        match node {
            None => (0, 0),
            Some(n) => {
                let node_ref = n.borrow();
                let (left_rob, left_not_rob) = dfs(&node_ref.left);
                let (right_rob, right_not_rob) = dfs(&node_ref.right);
                
                let rob_current = node_ref.val + left_not_rob + right_not_rob;
                let not_rob_current = left_rob.max(left_not_rob) + right_rob.max(right_not_rob);
                
                (rob_current, not_rob_current)
            }
        }
    }
    
    let (rob, not_rob) = dfs(&root);
    rob.max(not_rob)
}

fn diameter_of_binary_tree(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>, max_diameter: &mut i32) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let node_ref = n.borrow();
                let left_depth = dfs(&node_ref.left, max_diameter);
                let right_depth = dfs(&node_ref.right, max_diameter);
                
                *max_diameter = (*max_diameter).max(left_depth + right_depth);
                
                1 + left_depth.max(right_depth)
            }
        }
    }
    
    let mut max_diameter = 0;
    dfs(&root, &mut max_diameter);
    max_diameter
}

fn binary_tree_maximum_path_sum(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>, max_sum: &mut i32) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let node_ref = n.borrow();
                let left_gain = dfs(&node_ref.left, max_sum).max(0);
                let right_gain = dfs(&node_ref.right, max_sum).max(0);
                
                let current_max = node_ref.val + left_gain + right_gain;
                *max_sum = (*max_sum).max(current_max);
                
                node_ref.val + left_gain.max(right_gain)
            }
        }
    }
    
    let mut max_sum = i32::MIN;
    dfs(&root, &mut max_sum);
    max_sum
}

fn longest_univalue_path(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>, max_path: &mut i32) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let node_ref = n.borrow();
                let left_length = dfs(&node_ref.left, max_path);
                let right_length = dfs(&node_ref.right, max_path);
                
                let left_path = if let Some(left) = &node_ref.left {
                    if left.borrow().val == node_ref.val {
                        left_length + 1
                    } else {
                        0
                    }
                } else {
                    0
                };
                
                let right_path = if let Some(right) = &node_ref.right {
                    if right.borrow().val == node_ref.val {
                        right_length + 1
                    } else {
                        0
                    }
                } else {
                    0
                };
                
                *max_path = (*max_path).max(left_path + right_path);
                left_path.max(right_path)
            }
        }
    }
    
    let mut max_path = 0;
    dfs(&root, &mut max_path);
    max_path
}

fn count_good_nodes(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn dfs(node: &Option<Rc<RefCell<TreeNode>>>, max_val: i32) -> i32 {
        match node {
            None => 0,
            Some(n) => {
                let node_ref = n.borrow();
                let count = if node_ref.val >= max_val { 1 } else { 0 };
                let new_max = max_val.max(node_ref.val);
                
                count + dfs(&node_ref.left, new_max) + dfs(&node_ref.right, new_max)
            }
        }
    }
    
    dfs(&root, i32::MIN)
}
```

---

## Pattern 8: State Machine DP {#state-machine-dp}

State machine DP problems involve transitioning between different states with certain rules.

**Python Implementation:**
```python
def best_time_to_buy_sell_stock_with_cooldown(prices):
    """Stock trading with cooldown period"""
    if not prices or len(prices) <= 1:
        return 0
    
    n = len(prices)
    # States: hold[i] = max profit on day i while holding stock
    #         sold[i] = max profit on day i after selling (cooldown)
    #         rest[i] = max profit on day i while not holding stock
    
    hold = [0] * n
    sold = [0] * n
    rest = [0] * n
    
    hold[0] = -prices[0]  # Buy on first day
    sold[0] = 0           # Can't sell on first day
    rest[0] = 0           # Rest on first day
    
    for i in range(1, n):
        hold[i] = max(hold[i-1], rest[i-1] - prices[i])  # Keep holding or buy today
        sold[i] = hold[i-1] + prices[i]                  # Sell today
        rest[i] = max(rest[i-1], sold[i-1])              # Rest (cooldown from selling)
    
    return max(sold[n-1], rest[n-1])

def best_time_to_buy_sell_stock_with_cooldown_optimized(prices):
    """Space-optimized version"""
    if not prices or len(prices) <= 1:
        return 0
    
    hold = -prices[0]  # Max profit while holding stock
    sold = 0           # Max profit after selling (in cooldown)
    rest = 0           # Max profit while resting
    
    for i in range(1, len(prices)):
        prev_sold = sold
        sold = hold + prices[i]                    # Sell today
        hold = max(hold, rest - prices[i])         # Keep holding or buy today
        rest = max(rest, prev_sold)                # Rest (cooldown)
    
    return max(sold, rest)

def best_time_to_buy_sell_stock_with_transaction_fee(prices, fee):
    """Stock trading with transaction fee"""
    if not prices:
        return 0
    
    hold = -prices[0]  # Max profit while holding stock
    sold = 0           # Max profit while not holding stock
    
    for i in range(1, len(prices)):
        hold = max(hold, sold - prices[i])        # Keep holding or buy today
        sold = max(sold, hold + prices[i] - fee)  # Keep not holding or sell today
    
    return sold

def best_time_to_buy_sell_stock_k_transactions(k, prices):
    """At most k transactions"""
    if not prices or k == 0:
        return 0
    
    n = len(prices)
    
    # If k >= n/2, we can make as many transactions as we want
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            if prices[i] > prices[i-1]:
                profit += prices[i] - prices[i-1]
        return profit
    
    # buy[i] = max profit after at most i transactions while holding stock
    # sell[i] = max profit after at most i transactions while not holding stock
    buy = [-prices[0]] * (k + 1)
    sell = [0] * (k + 1)
    
    for i in range(1, n):
        for j in range(k, 0, -1):
            sell[j] = max(sell[j], buy[j] + prices[i])
            buy[j] = max(buy[j], sell[j-1] - prices[i])
    
    return sell[k]

def paint_house(costs):
    """Paint houses with 3 colors, no adjacent houses same color"""
    if not costs:
        return 0
    
    n = len(costs)
    # dp[i][j] = min cost to paint house i with color j
    dp = [[0] * 3 for _ in range(n)]
    dp[0] = costs[0][:]
    
    for i in range(1, n):
        dp[i][0] = costs[i][0] + min(dp[i-1][1], dp[i-1][2])
        dp[i][1] = costs[i][1] + min(dp[i-1][0], dp[i-1][2])
        dp[i][2] = costs[i][2] + min(dp[i-1][0], dp[i-1][1])
    
    return min(dp[n-1])

def paint_house_optimized(costs):
    """Space-optimized version"""
    if not costs:
        return 0
    
    prev_red, prev_blue, prev_green = costs[0]
    
    for i in range(1, len(costs)):
        curr_red = costs[i][0] + min(prev_blue, prev_green)
        curr_blue = costs[i][1] + min(prev_red, prev_green)
        curr_green = costs[i][2] + min(prev_red, prev_blue)
        
        prev_red, prev_blue, prev_green = curr_red, curr_blue, curr_green
    
    return min(prev_red, prev_blue, prev_green)

def paint_fence(n, k):
    """Paint fence with k colors, no more than 2 adjacent same color"""
    if n == 0:
        return 0
    if n == 1:
        return k
    
    # same = ways to paint with last two posts same color
    # diff = ways to paint with last two posts different colors
    same = k          # First two posts same color: k ways
    diff = k * (k - 1)  # First two posts different: k * (k-1) ways
    
    for i in range(3, n + 1):
        prev_same = same
        same = diff        # Last two same = previous different
        diff = (prev_same + diff) * (k - 1)  # Last two different
    
    return same + diff
```

**Rust Implementation:**
```rust
fn best_time_to_buy_sell_stock_with_cooldown(prices: Vec<i32>) -> i32 {
    if prices.len() <= 1 {
        return 0;
    }
    
    let mut hold = -prices[0];
    let mut sold = 0;
    let mut rest = 0;
    
    for i in 1..prices.len() {
        let prev_sold = sold;
        sold = hold + prices[i];
        hold = hold.max(rest - prices[i]);
        rest = rest.max(prev_sold);
    }
    
    sold.max(rest)
}

fn best_time_to_buy_sell_stock_with_transaction_fee(prices: Vec<i32>, fee: i32) -> i32 {
    if prices.is_empty() {
        return 0;
    }
    
    let mut hold = -prices[0];
    let mut sold = 0;
    
    for i in 1..prices.len() {
        hold = hold.max(sold - prices[i]);
        sold = sold.max(hold + prices[i] - fee);
    }
    
    sold
}

fn best_time_to_buy_sell_stock_k_transactions(k: i32, prices: Vec<i32>) -> i32 {
    if prices.is_empty() || k == 0 {
        return 0;
    }
    
    let n = prices.len();
    let k = k as usize;
    
    // If k >= n/2, unlimited transactions
    if k >= n / 2 {
        let mut profit = 0;
        for i in 1..n {
            if prices[i] > prices[i - 1] {
                profit += prices[i] - prices[i - 1];
            }
        }
        return profit;
    }
    
    let mut buy = vec![-prices[0]; k + 1];
    let mut sell = vec![0; k + 1];
    
    for i in 1..n {
        for j in (1..=k).rev() {
            sell[j] = sell[j].max(buy[j] + prices[i]);
            buy[j] = buy[j].max(sell[j - 1] - prices[i]);
        }
    }
    
    sell[k]
}

fn paint_house(costs: Vec<Vec<i32>>) -> i32 {
    if costs.is_empty() {
        return 0;
    }
    
    let mut prev = costs[0].clone();
    
    for i in 1..costs.len() {
        let curr = vec![
            costs[i][0] + prev[1].min(prev[2]),
            costs[i][1] + prev[0].min(prev[2]),
            costs[i][2] + prev[0].min(prev[1]),
        ];
        prev = curr;
    }
    
    *prev.iter().min().unwrap()
}

fn paint_fence(n: i32, k: i32) -> i32 {
    if n == 0 {
        return 0;
    }
    if n == 1 {
        return k;
    }
    
    let mut same = k;
    let mut diff = k * (k - 1);
    
    for _ in 3..=n {
        let prev_same = same;
        same = diff;
        diff = (prev_same + diff) * (k - 1);
    }
    
    same + diff
}
```

---

## Pattern 9: Digit DP {#digit-dp}

Digit DP is used for counting numbers with certain properties within a range.

**Python Implementation:**
```python
def count_numbers_with_unique_digits(n):
    """Count numbers from 0 to 10^n - 1 with unique digits"""
    if n == 0:
        return 1
    
    # For n=1: 0,1,2...9 = 10 numbers
    # For n=2: 9 * 9 new numbers (first digit 1-9, second different from first)
    # For n=3: 9 * 9 * 8 new numbers, etc.
    
    result = 10  # All single digit numbers
    unique_digits = 9  # Numbers with unique digits starting from 10
    available_digits = 9  # Available digits for next position
    
    for i in range(2, n + 1):
        unique_digits *= available_digits
        result += unique_digits
        available_digits -= 1
    
    return result

def count_digit_one(n):
    """Count occurrences of digit 1 from 1 to n"""
    def count_digit_one_in_position(n, position):
        """Count 1s in specific position (units, tens, hundreds, etc.)"""
        power_of_ten = 10 ** position
        higher = n // (power_of_ten * 10)
        current = (n // power_of_ten) % 10
        lower = n % power_of_ten
        
        if current == 0:
            return higher * power_of_ten
        elif current == 1:
            return higher * power_of_ten + lower + 1
        else:
            return (higher + 1) * power_of_ten
    
    count = 0
    position = 0
    while 10 ** position <= n:
        count += count_digit_one_in_position(n, position)
        position += 1
    
    return count

def numbers_at_most_n_given_digit_set(digits, n):
    """Count numbers <= n that can be formed using given digits"""
    s = str(n)
    k = len(s)
    digits = sorted(set(digits))
    
    # Count numbers with fewer digits
    result = 0
    for i in range(1, k):
        result += len(digits) ** i
    
    # Count numbers with exactly k digits
    def dp(pos, tight, started):
        if pos == k:
            return int(started)
        
        limit = int(s[pos]) if tight else 9
        count = 0
        
        # Don't start the number yet (leading zeros)
        if not started:
            count += dp(pos + 1, tight and (0 == limit), False)
        
        # Try each digit
        for digit in digits:
            digit_int = int(digit)
            if digit_int <= limit:
                new_tight = tight and (digit_int == limit)
                count += dp(pos + 1, new_tight, True)
            else:
                break
        
        return count
    
    # Memoization version
    from functools import lru_cache
    
    @lru_cache(None)
    def dp_memo(pos, tight, started):
        if pos == k:
            return int(started)
        
        limit = int(s[pos]) if tight else 9
        count = 0
        
        if not started:
            count += dp_memo(pos + 1, tight and (0 <= limit), False)
        
        for digit in digits:
            digit_int = int(digit)
            if digit_int <= limit:
                new_tight = tight and (digit_int == limit)
                count += dp_memo(pos + 1, new_tight, True)
            else:
                break
        
        return count
    
    result += dp_memo(0, True, False)
    return result

def count_numbers_with_digit_sum(n, target_sum):
    """Count n-digit numbers with digit sum equal to target_sum"""
    @lru_cache(None)
    def dp(pos, remaining_sum, tight, started):
        if pos == n:
            return 1 if remaining_sum == 0 and started else 0
        
        if remaining_sum < 0:
            return 0
        
        result = 0
        limit = 9 if not tight else int(str(target_sum)[pos]) if pos < len(str(target_sum)) else 9
        
        for digit in range(0, min(10, remaining_sum + 1)):
            if digit <= limit:
                new_started = started or (digit > 0)
                if not started and digit == 0 and pos < n - 1:
                    # Leading zero
                    result += dp(pos + 1, remaining_sum, False, False)
                else:
                    result += dp(pos + 1, remaining_sum - digit, 
                               tight and digit == limit, new_started)
        
        return result
    
    return dp(0, target_sum, False, False)

def count_stepping_numbers(low, high):
    """Count stepping numbers in range [low, high]
    Stepping number: adjacent digits differ by exactly 1"""
    
    def count_up_to(num):
        if num < 0:
            return 0
        
        s = str(num)
        n = len(s)
        
        @lru_cache(None)
        def dp(pos, last_digit, tight, started):
            if pos == n:
                return int(started)
            
            result = 0
            limit = int(s[pos]) if tight else 9
            
            # Leading zero
            if not started:
                result += dp(pos + 1, -1, tight and (0 <= limit), False)
            
            # Try each digit
            start = 0 if not started else 0
            for digit in range(start, limit + 1):
                if not started:
                    if digit == 0:
                        continue
                    result += dp(pos + 1, digit, tight and (digit == limit), True)
                else:
                    if last_digit == -1 or abs(digit - last_digit) == 1:
                        result += dp(pos + 1, digit, tight and (digit == limit), True)
            
            return result
        
        return dp(0, -1, True, False)
    
    # Add single digit stepping numbers (0-9 are all stepping)
    result = count_up_to(high) - count_up_to(low - 1)
    return result
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

fn count_numbers_with_unique_digits(n: i32) -> i32 {
    if n == 0 {
        return 1;
    }
    
    let mut result = 10;
    let mut unique_digits = 9;
    let mut available_digits = 9;
    
    for _ in 2..=n {
        unique_digits *= available_digits;
        result += unique_digits;
        available_digits -= 1;
    }
    
    result
}

fn count_digit_one(n: i32) -> i32 {
    fn count_in_position(n: i32, position: i32) -> i32 {
        let power_of_ten = 10_i32.pow(position as u32);
        let higher = n / (power_of_ten * 10);
        let current = (n / power_of_ten) % 10;
        let lower = n % power_of_ten;
        
        match current {
            0 => higher * power_of_ten,
            1 => higher * power_of_ten + lower + 1,
            _ => (higher + 1) * power_of_ten,
        }
    }
    
    let mut count = 0;
    let mut position = 0;
    
    while 10_i32.pow(position) <= n {
        count += count_in_position(n, position as i32);
        position += 1;
    }
    
    count
}

fn numbers_at_most_n_given_digit_set(digits: Vec<String>, n: i32) -> i32 {
    let s = n.to_string();
    let k = s.len();
    let mut digits: Vec<i32> = digits.into_iter()
        .map(|d| d.parse().unwrap())
        .collect();
    digits.sort();
    digits.dedup();
    
    // Count numbers with fewer digits
    let mut result = 0;
    for i in 1..k {
        result += (digits.len() as i32).pow(i as u32);
    }
    
    // Count numbers with exactly k digits using memoization
    let mut memo = HashMap::new();
    
    fn dp(pos: usize, tight: bool, started: bool, 
          s: &str, digits: &[i32], 
          memo: &mut HashMap<(usize, bool, bool), i32>) -> i32 {
        if pos == s.len() {
            return if started { 1 } else { 0 };
        }
        
        let key = (pos, tight, started);
        if let Some(&cached) = memo.get(&key) {
            return cached;
        }
        
        let limit = if tight {
            s.chars().nth(pos).unwrap().to_digit(10).unwrap() as i32
        } else {
            9
        };
        
        let mut count = 0;
        
        // Leading zero
        if !started {
            count += dp(pos + 1, tight && (0 <= limit), false, s, digits, memo);
        }
        
        // Try each digit
        for &digit in digits {
            if digit <= limit {
                let new_tight = tight && (digit == limit);
                count += dp(pos + 1, new_tight, true, s, digits, memo);
            } else {
                break;
            }
        }
        
        memo.insert(key, count);
        count
    }
    
    result + dp(0, true, false, &s, &digits, &mut memo)
}

fn count_stepping_numbers(low: i32, high: i32) -> i32 {
    fn count_up_to(num: i32) -> i32 {
        if num < 0 {
            return 0;
        }
        
        let s = num.to_string();
        let mut memo = HashMap::new();
        
        fn dp(pos: usize, last_digit: i32, tight: bool, started: bool,
              s: &str, memo: &mut HashMap<(usize, i32, bool, bool), i32>) -> i32 {
            if pos == s.len() {
                return if started { 1 } else { 0 };
            }
            
            let key = (pos, last_digit, tight, started);
            if let Some(&cached) = memo.get(&key) {
                return cached;
            }
            
            let limit = if tight {
                s.chars().nth(pos).unwrap().to_digit(10).unwrap() as i32
            } else {
                9
            };
            
            let mut result = 0;
            
            // Leading zero
            if !started {
                result += dp(pos + 1, -1, tight && (0 <= limit), false, s, memo);
            }
            
            // Try each digit
            for digit in 0..=limit {
                if !started {
                    if digit == 0 {
                        continue;
                    }
                    result += dp(pos + 1, digit, tight && (digit == limit), true, s, memo);
                } else if last_digit == -1 || (digit - last_digit).abs() == 1 {
                    result += dp(pos + 1, digit, tight && (digit == limit), true, s, memo);
                }
            }
            
            memo.insert(key, result);
            result
        }
        
        dp(0, -1, true, false, &s, &mut memo)
    }
    
    count_up_to(high) - count_up_to(low - 1)
}
```

---

## Pattern 10: Bitmask DP {#bitmask-dp}

Bitmask DP is used when the state can be represented using bits, often for subset problems.

**Python Implementation:**
```python
def traveling_salesman_problem(dist):
    """TSP using bitmask DP - find minimum cost to visit all cities"""
    n = len(dist)
    
    # dp[mask][i] = minimum cost to visit cities in mask, ending at city i
    dp = [[float('inf')] * n for _ in range(1 << n)]
    
    # Start from city 0
    dp[1][0] = 0  # mask = 1 (only city 0 visited), at city 0
    
    for mask in range(1 << n):
        for u in range(n):
            if not (mask & (1 << u)):  # City u not in current set
                continue
            
            for v in range(n):
                if u == v or not (mask & (1 << v)):  # Same city or v not visited
                    continue
                
                # Try going from v to u
                prev_mask = mask ^ (1 << u)  # Remove u from mask
                if dp[prev_mask][v] != float('inf'):
                    dp[mask][u] = min(dp[mask][u], dp[prev_mask][v] + dist[v][u])
    
    # Find minimum cost to return to start
    full_mask = (1 << n) - 1
    result = float('inf')
    for i in range(1, n):
        if dp[full_mask][i] != float('inf'):
            result = min(result, dp[full_mask][i] + dist[i][0])
    
    return result if result != float('inf') else -1

def assignment_problem(cost):
    """Assign n workers to n jobs with minimum cost"""
    n = len(cost)
    
    # dp[mask] = minimum cost to assign jobs in mask
    dp = [float('inf')] * (1 << n)
    dp[0] = 0
    
    for mask in range(1 << n):
        if dp[mask] == float('inf'):
            continue
        
        # Count number of assigned jobs
        assigned_jobs = bin(mask).count('1')
        
        if assigned_jobs == n:
            continue
        
        # Try assigning next worker to each unassigned job
        worker = assigned_jobs
        for job in range(n):
            if not (mask & (1 << job)):  # Job not assigned
                new_mask = mask | (1 << job)
                dp[new_mask] = min(dp[new_mask], dp[mask] + cost[worker][job])
    
    return dp[(1 << n) - 1]

def count_bits_subsets(nums):
    """Count number of AND subsets for each possible value"""
    n = len(nums)
    max_val = max(nums) if nums else 0
    
    # Count how many subsets have AND value = i
    count = [0] * (max_val + 1)
    
    # For each subset
    for mask in range(1, 1 << n):
        and_result = (1 << 20) - 1  # Start with all bits set
        
        for i in range(n):
            if mask & (1 << i):
                and_result &= nums[i]
        
        if and_result <= max_val:
            count[and_result] += 1
    
    return count

def shortest_superstring(words):
    """Find shortest superstring containing all words"""
    n = len(words)
    
    # Precompute overlap between each pair of words
    overlap = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                # Find maximum overlap when words[i] comes before words[j]
                max_overlap = min(len(words[i]), len(words[j]))
                for k in range(max_overlap, 0, -1):
                    if words[i][-k:] == words[j][:k]:
                        overlap[i][j] = k
                        break
    
    # dp[mask][i] = minimum length to cover words in mask, ending with word i
    dp = [[float('inf')] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    
    # Initialize single words
    for i in range(n):
        dp[1 << i][i] = len(words[i])
    
    # Fill DP table
    for mask in range(1 << n):
        for i in range(n):
            if not (mask & (1 << i)) or dp[mask][i] == float('inf'):
                continue
            
            for j in range(n):
                if i == j or (mask & (1 << j)):
                    continue
                
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + len(words[j]) - overlap[i][j]
                
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
    
    # Find minimum cost and ending word
    full_mask = (1 << n) - 1
    min_cost = float('inf')
    last_word = -1
    
    for i in range(n):
        if dp[full_mask][i] < min_cost:
            min_cost = dp[full_mask][i]
            last_word = i
    
    # Reconstruct solution
    path = []
    mask = full_mask
    curr = last_word
    
    while curr != -1:
        path.append(curr)
        next_curr = parent[mask][curr]
        mask ^= (1 << curr)
        curr = next_curr
    
    path.reverse()
    
    # Build superstring
    result = words[path[0]]
    for i in range(1, len(path)):
        prev_word = path[i-1]
        curr_word = path[i]
        result += words[curr_word][overlap[prev_word][curr_word]:]
    
    return result

def max_score_words(words, letters, score):
    """Maximum score of valid words using given letters"""
    from collections import Counter
    
    n = len(words)
    
    def get_score(word_indices):
        letter_count = Counter()
        total_score = 0
        
        for i in word_indices:
            for char in words[i]:
                letter_count[char] += 1
                total_score += score[ord(char) - ord('a')]
        
        # Check if we have enough letters
        available = Counter(letters)
        for char, needed in letter_count.items():
            if needed > available[char]:
                return -1
        
        return total_score
    
    max_score_val = 0
    
    # Try all possible subsets
    for mask in range(1 << n):
        word_indices = []
        for i in range(n):
            if mask & (1 << i):
                word_indices.append(i)
        
        current_score = get_score(word_indices)
        if current_score > max_score_val:
            max_score_val = current_score
    
    return max_score_val
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

fn traveling_salesman_problem(dist: Vec<Vec<i32>>) -> i32 {
    let n = dist.len();
    let mut dp = vec![vec![i32::MAX; n]; 1 << n];
    
    dp[1][0] = 0; // Start at city 0
    
    for mask in 0..(1 << n) {
        for u in 0..n {
            if (mask & (1 << u)) == 0 || dp[mask][u] == i32::MAX {
                continue;
            }
            
            for v in 0..n {
                if u == v || (mask & (1 << v)) == 0 {
                    continue;
                }
                
                let prev_mask = mask ^ (1 << u);
                if dp[prev_mask][v] != i32::MAX {
                    dp[mask][u] = dp[mask][u].min(dp[prev_mask][v] + dist[v][u]);
                }
            }
        }
    }
    
    let full_mask = (1 << n) - 1;
    let mut result = i32::MAX;
    
    for i in 1..n {
        if dp[full_mask][i] != i32::MAX {
            result = result.min(dp[full_mask][i] + dist[i][0]);
        }
    }
    
    if result == i32::MAX { -1 } else { result }
}

fn assignment_problem(cost: Vec<Vec<i32>>) -> i32 {
    let n = cost.len();
    let mut dp = vec![i32::MAX; 1 << n];
    dp[0] = 0;
    
    for mask in 0..(1 << n) {
        if dp[mask] == i32::MAX {
            continue;
        }
        
        let assigned_jobs = mask.count_ones() as usize;
        if assigned_jobs == n {
            continue;
        }
        
        let worker = assigned_jobs;
        for job in 0..n {
            if (mask & (1 << job)) == 0 {
                let new_mask = mask | (1 << job);
                dp[new_mask] = dp[new_mask].min(dp[mask] + cost[worker][job]);
            }
        }
    }
    
    dp[(1 << n) - 1]
}

fn shortest_superstring(words: Vec<String>) -> String {
    let n = words.len();
    
    // Compute overlaps
    let mut overlap = vec![vec![0; n]; n];
    for i in 0..n {
        for j in 0..n {
            if i != j {
                let max_overlap = words[i].len().min(words[j].len());
                for k in (1..=max_overlap).rev() {
                    if words[i][words[i].len()-k..] == words[j][..k] {
                        overlap[i][j] = k;
                        break;
                    }
                }
            }
        }
    }
    
    let mut dp = vec![vec![i32::MAX; n]; 1 << n];
    let mut parent = vec![vec![-1i32; n]; 1 << n];
    
    // Initialize
    for i in 0..n {
        dp[1 << i][i] = words[i].len() as i32;
    }
    
    // Fill DP
    for mask in 0..(1 << n) {
        for i in 0..n {
            if (mask & (1 << i)) == 0 || dp[mask][i] == i32::MAX {
                continue;
            }
            
            for j in 0..n {
                if i == j || (mask & (1 << j)) != 0 {
                    continue;
                }
                
                let new_mask = mask | (1 << j);
                let new_cost = dp[mask][i] + words[j].len() as i32 - overlap[i][j] as i32;
                
                if new_cost < dp[new_mask][j] {
                    dp[new_mask][j] = new_cost;
                    parent[new_mask][j] = i as i32;
                }
            }
        }
    }
    
    // Find optimal solution
    let full_mask = (1 << n) - 1;
    let mut min_cost = i32::MAX;
    let mut last_word = 0;
    
    for i in 0..n {
        if dp[full_mask][i] < min_cost {
            min_cost = dp[full_mask][i];
            last_word = i;
        }
    }
    
    // Reconstruct path
    let mut path = Vec::new();
    let mut mask = full_mask;
    let mut curr = last_word as i32;
    
    while curr != -1 {
        path.push(curr as usize);
        let next_curr = parent[mask][curr as usize];
        mask ^= 1 << curr;
        curr = next_curr;
    }
    
    path.reverse();
    
    // Build result
    let mut result = words[path[0]].clone();
    for i in 1..path.len() {
        let prev_word = path[i-1];
        let curr_word = path[i];
        let overlap_len = overlap[prev_word][curr_word];
        result.push_str(&words[curr_word][overlap_len..]);
    }
    
    result
}

fn max_score_words(words: Vec<String>, letters: Vec<char>, score: Vec<i32>) -> i32 {
    use std::collections::HashMap;
    
    let n = words.len();
    
    fn get_score(word_indices: &[usize], words: &[String], 
                letters: &[char], score: &[i32]) -> i32 {
        let mut letter_count = HashMap::new();
        let mut total_score = 0;
        
        for &i in word_indices {
            for ch in words[i].chars() {
                *letter_count.entry(ch).or_insert(0) += 1;
                total_score += score[(ch as u8 - b'a') as usize];
            }
        }
        
        let mut available = HashMap::new();
        for &ch in letters {
            *available.entry(ch).or_insert(0) += 1;
        }
        
        for (ch, needed) in letter_count {
            if needed > *available.get(&ch).unwrap_or(&0) {
                return -1;
            }
        }
        
        total_score
    }
    
    let mut max_score_val = 0;
    
    for mask in 0..(1 << n) {
        let word_indices: Vec<usize> = (0..n)
            .filter(|&i| (mask & (1 << i)) != 0)
            .collect();
        
        let current_score = get_score(&word_indices, &words, &letters, &score);
        if current_score > max_score_val {
            max_score_val = current_score;
        }
    }
    
    max_score_val
}
```

---

## Summary and Problem-Solving Strategy

### General DP Problem-Solving Steps:

1. **Identify the Pattern**: Determine which DP pattern the problem follows
2. **Define State**: What information do we need to track?
3. **State Transition**: How do we move from one state to another?
4. **Base Cases**: What are the simplest cases?
5. **Optimization**: Can we reduce space complexity?

### Time and Space Complexity Analysis:

| Pattern | Typical Time | Typical Space | Example Problems |
|---------|-------------|---------------|------------------|
| Linear DP | O(n) | O(n) → O(1) | Fibonacci, House Robber |
| Grid DP | O(m×n) | O(m×n) → O(n) | Unique Paths, Edit Distance |
| Knapsack | O(n×W) | O(n×W) → O(W) | 0/1 Knapsack, Coin Change |
| LCS | O(m×n) | O(m×n) | Edit Distance, LCS |
| Interval DP | O(n³) | O(n²) | Matrix Chain, Burst Balloons |
| Tree DP | O(n) | O(h) | Tree problems with DFS |
| Bitmask DP | O(n×2ⁿ) | O(2ⁿ) | TSP, Subset problems |

### Common Optimizations:

1. **Space Optimization**: Use rolling arrays when only previous states are needed
2. **Memoization vs Tabulation**: Choose based on problem constraints
3. **Coordinate Compression**: For large coordinate ranges
4. **State Reduction**: Minimize state dimensions when possible

This guide covers the most important Dynamic Programming patterns with complete implementations in both Python and Rust. Each pattern includes explanations, code snippets, and complexity analysis to help you understand and apply these techniques effectively.
