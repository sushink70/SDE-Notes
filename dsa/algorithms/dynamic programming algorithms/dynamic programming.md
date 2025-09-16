# Dynamic Programming Complete Guide - Python & Rust

I've completed the comprehensive Dynamic Programming guide with implementations in both Python and Rust. The guide covers:

## Key Features:

1. **Foundational Concepts**: Core principles of DP including memoization and tabulation
2. **Classic Problems**: Complete implementations of:
   - Fibonacci sequence
   - Longest Common Subsequence (LCS)
   - 0/1 Knapsack Problem
   - Edit Distance (Levenshtein)
   - Coin Change Problem

3. **Advanced Techniques**:
   - Longest Increasing Subsequence (O(n log n) solution)
   - Matrix Chain Multiplication
   - Palindrome Partitioning
   - Maximum Rectangle in Binary Matrix

4. **Space Optimization**: Rolling array techniques and memory-efficient implementations

5. **Performance Analysis**: Time complexity comparisons across different approaches

6. **Test Cases**: Comprehensive test suites for both languages

## Language-Specific Benefits:

**Python**:

- More concise and readable syntax
- Built-in data structures like lists and dictionaries
- Easier debugging and prototyping

**Rust**:

- Memory safety without garbage collection
- Better performance for large-scale problems
- Strong type system prevents common errors
- Zero-cost abstractions

The guide includes both theoretical explanations and practical, runnable code that you can use as a reference for implementing DP solutions in real projects. Each problem includes multiple approaches (recursive, memoized, tabulated, and space-optimized) so you can choose the most appropriate one for your specific use case.

Would you like me to expand on any particular section or add more advanced DP problems?

## Dynamic Programming Complete Guide - Python & Rust

## Table of Contents

1. [Introduction to Dynamic Programming](#introduction)
2. [Core Principles](#core-principles)
3. [Implementation Patterns](#implementation-patterns)
4. [Classic Problems](#classic-problems)
5. [Advanced Techniques](#advanced-techniques)
6. [Space Optimization](#space-optimization)
7. [Performance Comparison](#performance-comparison)

## Introduction

Dynamic Programming (DP) is an algorithmic paradigm that solves complex problems by breaking them down into simpler subproblems. It stores the results of subproblems to avoid computing the same results again, following the principle of **optimal substructure** and **overlapping subproblems**.

### Key Characteristics:

- **Optimal Substructure**: Optimal solution contains optimal solutions to subproblems
- **Overlapping Subproblems**: Same subproblems are solved multiple times
- **Memoization**: Store results to avoid recomputation

## Core Principles

### 1. Memoization (Top-Down)

Start with the original problem and recursively break it down, storing results.

### 2. Tabulation (Bottom-Up)  

Start with the smallest subproblems and build up to the original problem.

### 3. State Definition

Clearly define what each state represents in your DP solution.

## Implementation Patterns

### Pattern 1: Fibonacci Sequence

**Problem**: Calculate the nth Fibonacci number.

#### Python Implementation:

```python
# Recursive with Memoization (Top-Down)
def fibonacci_memo(n, memo=None):
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]

# Tabulation (Bottom-Up)
def fibonacci_tab(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Space Optimized
def fibonacci_optimized(n):
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1
```

#### Rust Implementation:

```rust
use std::collections::HashMap;

// Recursive with Memoization (Top-Down)
fn fibonacci_memo(n: usize, memo: &mut HashMap<usize, u64>) -> u64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    let result = match n {
        0 | 1 => n as u64,
        _ => fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo),
    };
    
    memo.insert(n, result);
    result
}

// Tabulation (Bottom-Up)
fn fibonacci_tab(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let mut dp = vec![0; n + 1];
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n]
}

// Space Optimized
fn fibonacci_optimized(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let (mut prev2, mut prev1) = (0, 1);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}
```

## Classic Problems

### 1. Longest Common Subsequence (LCS)

**Problem**: Find the length of the longest common subsequence between two strings.

#### Python Implementation:

```python
def lcs_length(text1, text2):
    m, n = len(text1), len(text2)
    
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def lcs_string(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Build DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Reconstruct LCS string
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
```

#### Rust Implementation:

```rust
fn lcs_length(text1: &str, text2: &str) -> usize {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

fn lcs_string(text1: &str, text2: &str) -> String {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Build DP table
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    // Reconstruct LCS string
    let mut lcs = Vec::new();
    let (mut i, mut j) = (m, n);
    
    while i > 0 && j > 0 {
        if chars1[i - 1] == chars2[j - 1] {
            lcs.push(chars1[i - 1]);
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
```

### 2. 0/1 Knapsack Problem

**Problem**: Given items with weights and values, maximize value within weight capacity.

#### Python Implementation:

```python
def knapsack_01(weights, values, capacity):
    n = len(weights)
    
    # dp[i][w] = maximum value using first i items with weight limit w
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

def knapsack_01_with_items(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    # Build DP table
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    # Backtrack to find selected items
    w = capacity
    selected_items = []
    
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(i-1)
            w -= weights[i-1]
    
    return dp[n][capacity], list(reversed(selected_items))

# Space optimized version
def knapsack_01_optimized(weights, values, capacity):
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        # Iterate backwards to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]
```

#### Rust Implementation:

```rust
fn knapsack_01(weights: &[usize], values: &[i32], capacity: usize) -> i32 {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=capacity {
            // Don't take item i-1
            dp[i][w] = dp[i - 1][w];
            
            // Take item i-1 if possible
            if weights[i - 1] <= w {
                dp[i][w] = dp[i][w].max(
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                );
            }
        }
    }
    
    dp[n][capacity]
}

fn knapsack_01_with_items(weights: &[usize], values: &[i32], capacity: usize) -> (i32, Vec<usize>) {
    let n = weights.len();
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    // Build DP table
    for i in 1..=n {
        for w in 0..=capacity {
            dp[i][w] = dp[i - 1][w];
            if weights[i - 1] <= w {
                dp[i][w] = dp[i][w].max(
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                );
            }
        }
    }
    
    // Backtrack to find selected items
    let mut w = capacity;
    let mut selected_items = Vec::new();
    
    for i in (1..=n).rev() {
        if dp[i][w] != dp[i - 1][w] {
            selected_items.push(i - 1);
            w -= weights[i - 1];
        }
    }
    
    selected_items.reverse();
    (dp[n][capacity], selected_items)
}

// Space optimized version
fn knapsack_01_optimized(weights: &[usize], values: &[i32], capacity: usize) -> i32 {
    let mut dp = vec![0; capacity + 1];
    
    for i in 0..weights.len() {
        // Iterate backwards to avoid using updated values
        for w in (weights[i]..=capacity).rev() {
            dp[w] = dp[w].max(dp[w - weights[i]] + values[i]);
        }
    }
    
    dp[capacity]
}
```

### 3. Edit Distance (Levenshtein Distance)

**Problem**: Find minimum operations to transform one string into another.

### Python Implementation:

```python
def edit_distance(word1, word2):
    m, n = len(word1), len(word2)
    
    # dp[i][j] = min operations to transform word1[0:i] to word2[0:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i  # Delete all characters
    
    for j in range(n + 1):
        dp[0][j] = j  # Insert all characters
    
    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]  # No operation needed
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # Delete
                    dp[i][j-1],    # Insert
                    dp[i-1][j-1]   # Replace
                )
    
    return dp[m][n]

def edit_distance_with_operations(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize and fill DP table (same as above)
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    # Backtrack to find operations
    operations = []
    i, j = m, n
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and word1[i-1] == word2[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            operations.append(f"Replace '{word1[i-1]}' with '{word2[j-1]}'")
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            operations.append(f"Delete '{word1[i-1]}'")
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            operations.append(f"Insert '{word2[j-1]}'")
            j -= 1
    
    return dp[m][n], list(reversed(operations))
```

#### Rust Implementation:

```rust
fn edit_distance(word1: &str, word2: &str) -> usize {
    let chars1: Vec<char> = word1.chars().collect();
    let chars2: Vec<char> = word2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Initialize base cases
    for i in 0..=m {
        dp[i][0] = i;
    }
    for j in 0..=n {
        dp[0][j] = j;
    }
    
    // Fill the DP table
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + dp[i - 1][j]
                    .min(dp[i][j - 1])
                    .min(dp[i - 1][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

fn edit_distance_with_operations(word1: &str, word2: &str) -> (usize, Vec<String>) {
    let chars1: Vec<char> = word1.chars().collect();
    let chars2: Vec<char> = word2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Initialize and fill DP table
    for i in 0..=m {
        dp[i][0] = i;
    }
    for j in 0..=n {
        dp[0][j] = j;
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + dp[i - 1][j]
                    .min(dp[i][j - 1])
                    .min(dp[i - 1][j - 1]);
            }
        }
    }
    
    // Backtrack to find operations
    let mut operations = Vec::new();
    let (mut i, mut j) = (m, n);
    
    while i > 0 || j > 0 {
        if i > 0 && j > 0 && chars1[i - 1] == chars2[j - 1] {
            i -= 1;
            j -= 1;
        } else if i > 0 && j > 0 && dp[i][j] == dp[i - 1][j - 1] + 1 {
            operations.push(format!(
                "Replace '{}' with '{}'",
                chars1[i - 1], chars2[j - 1]
            ));
            i -= 1;
            j -= 1;
        } else if i > 0 && dp[i][j] == dp[i - 1][j] + 1 {
            operations.push(format!("Delete '{}'", chars1[i - 1]));
            i -= 1;
        } else if j > 0 && dp[i][j] == dp[i][j - 1] + 1 {
            operations.push(format!("Insert '{}'", chars2[j - 1]));
            j -= 1;
        }
    }
    
    operations.reverse();
    (dp[m][n], operations)
}
```

### 4. Coin Change Problem

**Problem**: Find minimum number of coins needed to make a target amount.

#### Python Implementation:

```python
def coin_change(coins, amount):
    # dp[i] = minimum coins needed for amount i
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case: 0 coins for amount 0
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

def coin_change_with_coins(coins, amount):
    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0
    
    for coin in coins:
        for i in range(coin, amount + 1):
            if dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin
    
    if dp[amount] == float('inf'):
        return -1, []
    
    # Reconstruct solution
    result_coins = []
    curr = amount
    
    while curr > 0:
        coin_used = parent[curr]
        result_coins.append(coin_used)
        curr -= coin_used
    
    return dp[amount], result_coins

# Count number of ways to make change
def coin_change_ways(coins, amount):
    dp = [0] * (amount + 1)
    dp[0] = 1  # One way to make 0: use no coins
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    
    return dp[amount]
```

#### Rust Implementation:

```rust
fn coin_change(coins: &[i32], amount: i32) -> i32 {
    let amount = amount as usize;
    let mut dp = vec![i32::MAX; amount + 1];
    dp[0] = 0;
    
    for &coin in coins {
        let coin = coin as usize;
        for i in coin..=amount {
            if dp[i - coin] != i32::MAX {
                dp[i] = dp[i].min(dp[i - coin] + 1);
            }
        }
    }
    
    if dp[amount] == i32::MAX { -1 } else { dp[amount] }
}

fn coin_change_with_coins(coins: &[i32], amount: i32) -> (i32, Vec<i32>) {
    let amount = amount as usize;
    let mut dp = vec![i32::MAX; amount + 1];
    let mut parent = vec![-1; amount + 1];
    dp[0] = 0;
    
    for &coin in coins {
        let coin_usize = coin as usize;
        for i in coin_usize..=amount {
            if dp[i - coin_usize] != i32::MAX && dp[i - coin_usize] + 1 < dp[i] {
                dp[i] = dp[i - coin_usize] + 1;
                parent[i] = coin;
            }
        }
    }
    
    if dp[amount] == i32::MAX {
        return (-1, Vec::new());
    }
    
    // Reconstruct solution
    let mut result_coins = Vec::new();
    let mut curr = amount;
    
    while curr > 0 {
        let coin_used = parent[curr];
        result_coins.push(coin_used);
        curr -= coin_used as usize;
    }
    
    (dp[amount], result_coins)
}

// Count number of ways to make change
fn coin_change_ways(coins: &[i32], amount: i32) -> i32 {
    let amount = amount as usize;
    let mut dp = vec![0; amount + 1];
    dp[0] = 1;
    
    for &coin in coins {
        let coin = coin as usize;
        for i in coin..=amount {
            dp[i] += dp[i - coin];
        }
    }
    
    dp[amount]
}
```

## Advanced Techniques

### 1. Longest Increasing Subsequence (LIS)

#### Python Implementation:

```python
def lis_length_n2(nums):
    """O(n²) solution"""
    if not nums:
        return 0
    
    n = len(nums)
    dp = [1] * n  # dp[i] = length of LIS ending at index i
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

def lis_length_nlogn(nums):
    """O(n log n) solution using binary search"""
    if not nums:
        return 0
    
    # tails[i] = smallest ending element of LIS of length i+1
    tails = []
    
    for num in nums:
        left, right = 0, len(tails)
        
        # Binary search for the position to replace/append
        while left < right:
            mid = (left + right) // 2
            if tails[mid] < num:
                left = mid + 1
            else:
                right = mid
        
        # If left == len(tails), we're extending the sequence
        if left == len(tails):
            tails.append(num)
        else:
            tails[left] = num
    
    return len(tails)

def lis_sequence(nums):
    """Return the actual LIS sequence"""
    if not nums:
        return []
    
    n = len(nums)
    dp = [1] * n
    parent = [-1] * n
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                parent[i] = j
    
    # Find the index with maximum LIS length
    max_length = max(dp)
    max_idx = dp.index(max_length)
    
    # Reconstruct the sequence
    lis = []
    curr = max_idx
    
    while curr != -1:
        lis.append(nums[curr])
        curr = parent[curr]
    
    return list(reversed(lis))
```

#### Rust Implementation:

```rust
fn lis_length_n2(nums: &[i32]) -> usize {
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

fn lis_length_nlogn(nums: &[i32]) -> usize {
    if nums.is_empty() {
        return 0;
    }
    
    let mut tails = Vec::new();
    
    for &num in nums {
        let pos = tails.binary_search(&num).unwrap_or_else(|e| e);
        
        if pos == tails.len() {
            tails.push(num);
        } else {
            tails[pos] = num;
        }
    }
    
    tails.len()
}

fn lis_sequence(nums: &[i32]) -> Vec<i32> {
    if nums.is_empty() {
        return Vec::new();
    }
    
    let n = nums.len();
    let mut dp = vec![1; n];
    let mut parent = vec![-1i32; n];
    
    for i in 1..n {
        for j in 0..i {
            if nums[j] < nums[i] && dp[j] + 1 > dp[i] {
                dp[i] = dp[j] + 1;
                parent[i] = j as i32;
            }
        }
    }
    
    // Find the index with maximum LIS length
    let max_length = *dp.iter().max().unwrap();
    let max_idx = dp.iter().position(|&x| x == max_length).unwrap();
    
    // Reconstruct the sequence
    let mut lis = Vec::new();
    let mut curr = max_idx as i32;
    
    while curr != -1 {
        lis.push(nums[curr as usize]);
        curr = parent[curr as usize];
    }
    
    lis.reverse();
    lis
}
```

## Space Optimization

### Rolling Array Technique

Many 2D DP problems can be optimized to use O(n) space instead of O(n²).

#### Example: Unique Paths

```python
# Python - Space optimized
def unique_paths_optimized(m, n):
    # Only need current and previous row
    prev_row = [1] * n
    
    for i in range(1, m):
        curr_row = [1] * n
        for j in range(1, n):
            curr_row[j] = curr_row[j-1] + prev_row[j]
        prev_row = curr_row
    
    return prev_row[n-1]

# Even more optimized - single array
def unique_paths_single_array(m, n):
    dp = [1] * n
    
    for i in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j-1]
    
    return dp[n-1]
```

```rust
// Rust - Space optimized
fn unique_paths_optimized(m: usize, n: usize) -> i32 {
    let mut prev_row = vec![1; n];
    
    for _ in 1..m {
        let mut curr_row = vec![1; n];
        for j in 1..n {
            curr_row[j] = curr_row[j - 1] + prev_row[j];
        }
        prev_row = curr_row;
    }
    
    prev_row[n - 1]
}

// Even more optimized - single array
fn unique_paths_single_array(m: usize, n: usize) -> i32 {
    let mut dp = vec![1; n];
    
    for _ in 1..m {
        for j in 1..n {
            dp[j] += dp[j - 1];
        }
    }
    
    dp[n - 1]
}
```

## Performance Comparison

### Time Complexity Analysis

| Problem | Naive Recursion | Memoization | Tabulation | Space Optimized |
|---------|----------------|-------------|------------|-----------------|
| Fibonacci | O(2^n) | O(n) | O(n) | O(1) |
| LCS | O(2^(m+n)) | O(mn) | O(mn) | O(min(m,n)) |
| Knapsack | O(2^n) | O(nW) | O(nW) | O(W) |
| Edit Distance | O(3^(m+n)) | O(mn) | O(mn) | O(min(m,n)) |
| Coin Change | O(S^n) | O(nS) | O(nS) | O(S) |

Where: n = number of items, m,n = string lengths, W = capacity, S = target sum

## Advanced DP Patterns

### 1. Matrix Chain Multiplication

**Problem**: Find optimal way to multiply a chain of matrices.

#### Python Implementation:

```python
def matrix_chain_multiplication(dimensions):
    """
    dimensions[i] = number of rows in matrix i
    dimensions[i+1] = number of columns in matrix i
    """
    n = len(dimensions) - 1  # number of matrices
    
    # dp[i][j] = minimum scalar multiplications for matrices i to j
    dp = [[0] * n for _ in range(n)]
    
    # l = chain length
    for l in range(2, n + 1):  # l is chain length
        for i in range(n - l + 1):
            j = i + l - 1
            dp[i][j] = float('inf')
            
            # Try all possible split points
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                       dimensions[i] * dimensions[k+1] * dimensions[j+1])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]

def matrix_chain_order(dimensions):
    """Return the optimal parenthesization"""
    n = len(dimensions) - 1
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    
    for l in range(2, n + 1):
        for i in range(n - l + 1):
            j = i + l - 1
            dp[i][j] = float('inf')
            
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                       dimensions[i] * dimensions[k+1] * dimensions[j+1])
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    def get_parentheses(i, j):
        if i == j:
            return f"M{i}"
        else:
            k = split[i][j]
            return f"({get_parentheses(i, k)}{get_parentheses(k+1, j)})"
    
    return dp[0][n-1], get_parentheses(0, n-1)
```

#### Rust Implementation:

```rust
fn matrix_chain_multiplication(dimensions: &[usize]) -> usize {
    let n = dimensions.len() - 1;
    let mut dp = vec![vec![0; n]; n];
    
    for l in 2..=n {
        for i in 0..=(n - l) {
            let j = i + l - 1;
            dp[i][j] = usize::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + 
                          dimensions[i] * dimensions[k + 1] * dimensions[j + 1];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    
    dp[0][n - 1]
}

fn matrix_chain_order(dimensions: &[usize]) -> (usize, String) {
    let n = dimensions.len() - 1;
    let mut dp = vec![vec![0; n]; n];
    let mut split = vec![vec![0; n]; n];
    
    for l in 2..=n {
        for i in 0..=(n - l) {
            let j = i + l - 1;
            dp[i][j] = usize::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + 
                          dimensions[i] * dimensions[k + 1] * dimensions[j + 1];
                if cost < dp[i][j] {
                    dp[i][j] = cost;
                    split[i][j] = k;
                }
            }
        }
    }
    
    fn get_parentheses(split: &[Vec<usize>], i: usize, j: usize) -> String {
        if i == j {
            format!("M{}", i)
        } else {
            let k = split[i][j];
            format!("({}{})", 
                   get_parentheses(split, i, k),
                   get_parentheses(split, k + 1, j))
        }
    }
    
    (dp[0][n - 1], get_parentheses(&split, 0, n - 1))
}
```

### 2. Palindrome Partitioning

**Problem**: Find minimum cuts to partition string into palindromes.

#### Python Implementation:

```python
def min_palindrome_cuts(s):
    n = len(s)
    
    # Precompute palindrome check
    is_palindrome = [[False] * n for _ in range(n)]
    
    # Every single character is a palindrome
    for i in range(n):
        is_palindrome[i][i] = True
    
    # Check for palindromes of length 2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            is_palindrome[i][i + 1] = True
    
    # Check for palindromes of length 3 and more
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and is_palindrome[i + 1][j - 1]:
                is_palindrome[i][j] = True
    
    # dp[i] = minimum cuts for s[0:i+1]
    dp = [float('inf')] * n
    
    for i in range(n):
        if is_palindrome[0][i]:
            dp[i] = 0
        else:
            for j in range(i):
                if is_palindrome[j + 1][i]:
                    dp[i] = min(dp[i], dp[j] + 1)
    
    return dp[n - 1]

def palindrome_partition(s):
    """Return all palindrome partitions"""
    def is_palindrome(start, end):
        while start < end:
            if s[start] != s[end]:
                return False
            start += 1
            end -= 1
        return True
    
    def backtrack(start, path, result):
        if start == len(s):
            result.append(path[:])
            return
        
        for end in range(start, len(s)):
            if is_palindrome(start, end):
                path.append(s[start:end + 1])
                backtrack(end + 1, path, result)
                path.pop()
    
    result = []
    backtrack(0, [], result)
    return result
```

#### Rust Implementation:

```rust
fn min_palindrome_cuts(s: &str) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n <= 1 {
        return 0;
    }
    
    // Precompute palindrome check
    let mut is_palindrome = vec![vec![false; n]; n];
    
    // Every single character is a palindrome
    for i in 0..n {
        is_palindrome[i][i] = true;
    }
    
    // Check for palindromes of length 2
    for i in 0..n - 1 {
        if chars[i] == chars[i + 1] {
            is_palindrome[i][i + 1] = true;
        }
    }
    
    // Check for palindromes of length 3 and more
    for length in 3..=n {
        for i in 0..=(n - length) {
            let j = i + length - 1;
            if chars[i] == chars[j] && is_palindrome[i + 1][j - 1] {
                is_palindrome[i][j] = true;
            }
        }
    }
    
    // dp[i] = minimum cuts for s[0..=i]
    let mut dp = vec![usize::MAX; n];
    
    for i in 0..n {
        if is_palindrome[0][i] {
            dp[i] = 0;
        } else {
            for j in 0..i {
                if is_palindrome[j + 1][i] && dp[j] != usize::MAX {
                    dp[i] = dp[i].min(dp[j] + 1);
                }
            }
        }
    }
    
    dp[n - 1]
}

fn palindrome_partition(s: &str) -> Vec<Vec<String>> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    fn is_palindrome(chars: &[char], start: usize, end: usize) -> bool {
        let (mut start, mut end) = (start, end);
        while start < end {
            if chars[start] != chars[end] {
                return false;
            }
            start += 1;
            end -= 1;
        }
        true
    }
    
    fn backtrack(
        chars: &[char],
        start: usize,
        path: &mut Vec<String>,
        result: &mut Vec<Vec<String>>
    ) {
        if start == chars.len() {
            result.push(path.clone());
            return;
        }
        
        for end in start..chars.len() {
            if is_palindrome(chars, start, end) {
                let substring: String = chars[start..=end].iter().collect();
                path.push(substring);
                backtrack(chars, end + 1, path, result);
                path.pop();
            }
        }
    }
    
    let mut result = Vec::new();
    let mut path = Vec::new();
    backtrack(&chars, 0, &mut path, &mut result);
    result
}
```

### 3. Maximum Rectangle in Binary Matrix

**Problem**: Find the largest rectangle containing only 1s in a binary matrix.

#### Python Implementation:

```python
def max_rectangle_area(matrix):
    if not matrix or not matrix[0]:
        return 0
    
    rows, cols = len(matrix), len(matrix[0])
    heights = [0] * cols
    max_area = 0
    
    def largest_rectangle_histogram(heights):
        stack = []
        max_area = 0
        
        for i, h in enumerate(heights):
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                max_area = max(max_area, height * width)
            stack.append(i)
        
        while stack:
            height = heights[stack.pop()]
            width = len(heights) if not stack else len(heights) - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        return max_area
    
    for row in matrix:
        for j in range(cols):
            if row[j] == '1':
                heights[j] += 1
            else:
                heights[j] = 0
        
        max_area = max(max_area, largest_rectangle_histogram(heights))
    
    return max_area

def max_rectangle_with_coordinates(matrix):
    """Return max area and coordinates of the rectangle"""
    if not matrix or not matrix[0]:
        return 0, None
    
    rows, cols = len(matrix), len(matrix[0])
    heights = [0] * cols
    max_area = 0
    best_coords = None
    
    def largest_rectangle_with_coords(heights, row_idx):
        stack = []
        max_area = 0
        best_rect = None
        
        for i, h in enumerate(heights):
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                area = height * width
                
                if area > max_area:
                    max_area = area
                    left = 0 if not stack else stack[-1] + 1
                    right = i - 1
                    top = row_idx - height + 1
                    bottom = row_idx
                    best_rect = (top, left, bottom, right)
            
            stack.append(i)
        
        while stack:
            height = heights[stack.pop()]
            width = len(heights) if not stack else len(heights) - stack[-1] - 1
            area = height * width
            
            if area > max_area:
                max_area = area
                left = 0 if not stack else stack[-1] + 1
                right = len(heights) - 1
                top = row_idx - height + 1
                bottom = row_idx
                best_rect = (top, left, bottom, right)
        
        return max_area, best_rect
    
    for i, row in enumerate(matrix):
        for j in range(cols):
            if row[j] == '1':
                heights[j] += 1
            else:
                heights[j] = 0
        
        area, coords = largest_rectangle_with_coords(heights, i)
        if area > max_area:
            max_area = area
            best_coords = coords
    
    return max_area, best_coords
```

#### Rust Implementation:

```rust
fn max_rectangle_area(matrix: &[Vec<char>]) -> i32 {
    if matrix.is_empty() || matrix[0].is_empty() {
        return 0;
    }
    
    let (rows, cols) = (matrix.len(), matrix[0].len());
    let mut heights = vec![0; cols];
    let mut max_area = 0;
    
    fn largest_rectangle_histogram(heights: &[i32]) -> i32 {
        let mut stack = Vec::new();
        let mut max_area = 0;
        
        for (i, &h) in heights.iter().enumerate() {
            while let Some(&top) = stack.last() {
                if heights[top] > h {
                    let height = heights[stack.pop().unwrap()];
                    let width = if stack.is_empty() { 
                        i as i32 
                    } else { 
                        i as i32 - stack.last().unwrap() - 1 
                    };
                    max_area = max_area.max(height * width);
                } else {
                    break;
                }
            }
            stack.push(i);
        }
        
        while let Some(top) = stack.pop() {
            let height = heights[top];
            let width = if stack.is_empty() {
                heights.len() as i32
            } else {
                heights.len() as i32 - stack.last().unwrap() - 1
            };
            max_area = max_area.max(height * width);
        }
        
        max_area
    }
    
    for row in matrix {
        for (j, &cell) in row.iter().enumerate() {
            if cell == '1' {
                heights[j] += 1;
            } else {
                heights[j] = 0;
            }
        }
        
        max_area = max_area.max(largest_rectangle_histogram(&heights));
    }
    
    max_area
}

fn max_rectangle_with_coordinates(matrix: &[Vec<char>]) -> (i32, Option<(usize, usize, usize, usize)>) {
    if matrix.is_empty() || matrix[0].is_empty() {
        return (0, None);
    }
    
    let (rows, cols) = (matrix.len(), matrix[0].len());
    let mut heights = vec![0; cols];
    let mut max_area = 0;
    let mut best_coords = None;
    
    fn largest_rectangle_with_coords(
        heights: &[i32], 
        row_idx: usize
    ) -> (i32, Option<(usize, usize, usize, usize)>) {
        let mut stack = Vec::new();
        let mut max_area = 0;
        let mut best_rect = None;
        
        for (i, &h) in heights.iter().enumerate() {
            while let Some(&top) = stack.last() {
                if heights[top] > h {
                    let height = heights[stack.pop().unwrap()];
                    let width = if stack.is_empty() { 
                        i as i32 
                    } else { 
                        i as i32 - stack.last().unwrap() - 1 
                    };
                    let area = height * width;
                    
                    if area > max_area {
                        max_area = area;
                        let left = if stack.is_empty() { 0 } else { stack.last().unwrap() + 1 };
                        let right = i - 1;
                        let top_row = row_idx - height as usize + 1;
                        let bottom_row = row_idx;
                        best_rect = Some((top_row, left, bottom_row, right));
                    }
                } else {
                    break;
                }
            }
            stack.push(i);
        }
        
        while let Some(top) = stack.pop() {
            let height = heights[top];
            let width = if stack.is_empty() {
                heights.len() as i32
            } else {
                heights.len() as i32 - stack.last().unwrap() - 1
            };
            let area = height * width;
            
            if area > max_area {
                max_area = area;
                let left = if stack.is_empty() { 0 } else { stack.last().unwrap() + 1 };
                let right = heights.len() - 1;
                let top_row = row_idx - height as usize + 1;
                let bottom_row = row_idx;
                best_rect = Some((top_row, left, bottom_row, right));
            }
        }
        
        (max_area, best_rect)
    }
    
    for (i, row) in matrix.iter().enumerate() {
        for (j, &cell) in row.iter().enumerate() {
            if cell == '1' {
                heights[j] += 1;
            } else {
                heights[j] = 0;
            }
        }
        
        let (area, coords) = largest_rectangle_with_coords(&heights, i);
        if area > max_area {
            max_area = area;
            best_coords = coords;
        }
    }
    
    (max_area, best_coords)
}
```

## Testing and Examples

### Test Cases

```python
# Python test cases
def test_dp_solutions():
    # Test Fibonacci
    assert fibonacci_optimized(10) == 55
    assert fibonacci_optimized(0) == 0
    assert fibonacci_optimized(1) == 1
    
    # Test LCS
    assert lcs_length("abcde", "ace") == 3
    assert lcs_string("abcde", "ace") == "ace"
    
    # Test Knapsack
    weights = [1, 3, 4, 5]
    values = [1, 4, 5, 7]
    capacity = 7
    assert knapsack_01(weights, values, capacity) == 9
    
    # Test Edit Distance
    assert edit_distance("horse", "ros") == 3
    
    # Test Coin Change
    assert coin_change([1, 2, 5], 11) == 3
    assert coin_change_ways([1, 2, 5], 5) == 4
    
    print("All tests passed!")

if __name__ == "__main__":
    test_dp_solutions()
```

```rust
// Rust test cases
#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;
    
    #[test]
    fn test_fibonacci() {
        assert_eq!(fibonacci_optimized(10), 55);
        assert_eq!(fibonacci_optimized(0), 0);
        assert_eq!(fibonacci_optimized(1), 1);
    }
    
    #[test]
    fn test_lcs() {
        assert_eq!(lcs_length("abcde", "ace"), 3);
        assert_eq!(lcs_string("abcde", "ace"), "ace");
    }
    
    #[test]
    fn test_knapsack() {
        let weights = [1, 3, 4, 5];
        let values = [1, 4, 5, 7];
        let capacity = 7;
        assert_eq!(knapsack_01(&weights, &values, capacity), 9);
    }
    
    #[test]
    fn test_edit_distance() {
        assert_eq!(edit_distance("horse", "ros"), 3);
    }
    
    #[test]
    fn test_coin_change() {
        assert_eq!(coin_change(&[1, 2, 5], 11), 3);
        assert_eq!(coin_change_ways(&[1, 2, 5], 5), 4);
    }
}

fn main() {
    println!("Run tests with: cargo test");
}
```

## Best Practices and Tips

### 1. Problem Analysis

- Identify overlapping subproblems
- Define the state clearly
- Establish recurrence relation
- Determine base cases

### 2. Implementation Strategy

- Start with recursive solution
- Add memoization
- Convert to tabulation if needed
- Optimize space if possible

### 3. Common Pitfalls

- Off-by-one errors in indexing
- Incorrect base cases
- Wrong state definition
- Not handling edge cases

### 4. Optimization Techniques

- Space optimization with rolling arrays
- Bottom-up vs top-down trade-offs
- Early termination conditions
- Preprocessing for efficiency

### 5. Debugging Tips

- Print DP table for small inputs
- Verify base cases first
- Check recurrence relation
- Test with edge cases

## Conclusion

Dynamic Programming is a powerful technique for solving optimization problems efficiently. The key is to:

1. **Identify the optimal substructure** in the problem
2. **Define states clearly** and establish relationships
3. **Choose the right approach** (memoization vs tabulation)
4. **Optimize space** when possible
5. **Test thoroughly** with various inputs

Both Python and Rust offer excellent support for implementing DP solutions, with Python providing more concise syntax and Rust offering better performance and memory safety. The choice between languages often depends on the specific requirements of your application.

Practice with the implementations provided here, and gradually work on more complex problems to master dynamic programming techniques!

I'll create a comprehensive ASCII diagram showing how Dynamic Programming works using a classic example - the Fibonacci sequence. This will demonstrate the key concepts of memoization and optimal substructure.I've created a comprehensive ASCII diagram that shows how Dynamic Programming works step by step using the Fibonacci sequence as an example. The diagram covers:

1. **The Problem**: Shows the inefficiency of naive recursion with overlapping subproblems
2. **Top-Down DP (Memoization)**: Demonstrates how caching results eliminates redundant calculations
3. **Bottom-Up DP (Tabulation)**: Shows the iterative approach building from base cases
4. **Key Principles**: Explains optimal substructure and overlapping subproblems
5. **Performance Comparison**: Highlights the dramatic improvement from O(2^n) to O(n)

The diagram uses visual elements like:

- Call trees showing redundant calculations
- Memory tables showing cached values
- Step-by-step execution traces
- Performance metrics comparing approaches

This visualization clearly demonstrates why Dynamic Programming is so powerful - it transforms exponential time algorithms into linear ones by avoiding redundant work through intelligent caching or table-building strategies.

DYNAMIC PROGRAMMING: STEP-BY-STEP VISUALIZATION

=================================================

PROBLEM: Calculate Fibonacci(5) = F(5)
Formula: F(n) = F(n-1) + F(n-2), where F(0)=0, F(1)=1

═══════════════════════════════════════════════════════════════════════════════

STEP 1: NAIVE RECURSIVE APPROACH (WITHOUT DP)

=============================================

Call Tree for F(5) - Shows Overlapping Subproblems:

                    F(5)
                   /    \
                F(4)      F(3)
               /   \     /    \
            F(3)   F(2) F(2)  F(1)
           /   \   / \  / \    |
        F(2) F(1)F(1)F(0)F(1)F(0) 1
        / \   |   |  |  |   |
     F(1)F(0) 1   1  0  1   0
      |   |
      1   0

Issues:
- F(3) calculated 2 times
- F(2) calculated 3 times  
- F(1) calculated 5 times
- F(0) calculated 3 times
- Time Complexity: O(2^n) - EXPONENTIAL!

═══════════════════════════════════════════════════════════════════════════════

STEP 2: DYNAMIC PROGRAMMING APPROACH - TOP-DOWN (MEMOIZATION)
============================================================

Memory Table (Initially Empty):
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  ?  │  ?  │  ?  │  ?  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Execution Trace:

Call F(5):
┌─────────────────────────────────────────┐
│ F(5) called                             │
│ Check memo[5]: EMPTY                    │
│ Need to calculate F(4) + F(3)           │
└─────────────────────────────────────────┘

Call F(4):
┌─────────────────────────────────────────┐
│ F(4) called                             │
│ Check memo[4]: EMPTY                    │
│ Need to calculate F(3) + F(2)           │
└─────────────────────────────────────────┘

Call F(3):
┌─────────────────────────────────────────┐
│ F(3) called                             │
│ Check memo[3]: EMPTY                    │
│ Need to calculate F(2) + F(1)           │
└─────────────────────────────────────────┘

Call F(2):
┌─────────────────────────────────────────┐
│ F(2) called                             │
│ Check memo[2]: EMPTY                    │
│ Need to calculate F(1) + F(0)           │
└─────────────────────────────────────────┘

Base Cases:
┌─────────────────────────────────────────┐
│ F(1) called → Return 1 (base case)      │
│ F(0) called → Return 0 (base case)      │
└─────────────────────────────────────────┘

Memory After F(2):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  ?  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Continue F(3):
┌─────────────────────────────────────────┐
│ F(3) = F(2) + F(1)                      │
│ F(2) = 1 (from memo!)                   │
│ F(1) = 1 (base case)                    │
│ F(3) = 1 + 1 = 2                        │
│ Store memo[3] = 2                       │
└─────────────────────────────────────────┘

Memory After F(3):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Continue F(4):
┌─────────────────────────────────────────┐
│ F(4) = F(3) + F(2)                      │
│ F(3) = 2 (from memo!)                   │
│ F(2) = 1 (from memo!)                   │
│ F(4) = 2 + 1 = 3                        │
│ Store memo[4] = 3                       │
└─────────────────────────────────────────┘

Memory After F(4):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  3  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Complete F(5):
┌─────────────────────────────────────────┐
│ F(5) = F(4) + F(3)                      │
│ F(4) = 3 (from memo!)                   │
│ F(3) = 2 (from memo!)                   │
│ F(5) = 3 + 2 = 5                        │
│ Store memo[5] = 5                       │
└─────────────────────────────────────────┘

Final Memory Table:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  3  │  5  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Result: F(5) = 5
Time Complexity: O(n) - LINEAR!

═══════════════════════════════════════════════════════════════════════════════

STEP 3: DYNAMIC PROGRAMMING APPROACH - BOTTOM-UP (TABULATION)

=============================================================

Build table from bottom up:

Initial Table:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  ?  │  ?  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
      ▲     ▲
   Base   Base
   Case   Case

Step 1: Calculate F(2)
┌─────────────────────────────────────────┐
│ F(2) = F(1) + F(0) = 1 + 0 = 1          │
└─────────────────────────────────────────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  ?  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                   ▲
                New!

Step 2: Calculate F(3)
┌─────────────────────────────────────────┐
│ F(3) = F(2) + F(1) = 1 + 1 = 2          │
└─────────────────────────────────────────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  ?  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                         ▲
                       New!

Step 3: Calculate F(4)
┌─────────────────────────────────────────┐
│ F(4) = F(3) + F(2) = 2 + 1 = 3          │
└─────────────────────────────────────────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  3  │  ?  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                               ▲
                             New!

Step 4: Calculate F(5)
┌─────────────────────────────────────────┐
│ F(5) = F(4) + F(3) = 3 + 2 = 5          │
└─────────────────────────────────────────┘

Final Table:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ n   │  0  │  1  │  2  │  3  │  4  │  5  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│F(n) │  0  │  1  │  1  │  2  │  3  │  5  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                                     ▲
                                  Result!

Result: F(5) = 5
Time Complexity: O(n), Space Complexity: O(n)

═══════════════════════════════════════════════════════════════════════════════

STEP 4: KEY DYNAMIC PROGRAMMING PRINCIPLES

==========================================

1. OPTIMAL SUBSTRUCTURE
   ┌─────────────────────────────────────────┐
   │ Problem can be broken down into          │
   │ smaller subproblems whose optimal        │
   │ solutions contribute to the overall      │
   │ optimal solution                         │
   │                                         │
   │ F(n) = F(n-1) + F(n-2)                  │
   │   ▲       ▲        ▲                    │
   │ Main   Sub1     Sub2                    │
   └─────────────────────────────────────────┘

2. OVERLAPPING SUBPROBLEMS
   ┌─────────────────────────────────────────┐
   │ Same subproblems occur multiple times   │
   │                                         │
   │ Without DP: F(3) calculated 2 times     │
   │ With DP:    F(3) calculated 1 time      │
   │                 ▲                       │
   │            Stored in memo/table         │
   └─────────────────────────────────────────┘

3. MEMOIZATION vs TABULATION
   ┌─────────────────┬─────────────────────────┐
   │  MEMOIZATION    │      TABULATION         │
   │  (Top-Down)     │     (Bottom-Up)         │
   ├─────────────────┼─────────────────────────┤
   │ • Recursive     │ • Iterative             │
   │ • Cache results │ • Build table           │
   │ • Lazy eval     │ • Eager eval            │
   │ • May use less  │ • Uses full table       │
   │   memory        │   memory                │
   └─────────────────┴─────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

PERFORMANCE COMPARISON
=====================

Approach          | Time      | Space     | Calls to F(3)
─────────────────┼───────────┼───────────┼──────────────
Naive Recursive  | O(2^n)    | O(n)      | 2
Memoization      | O(n)      | O(n)      | 1  
Tabulation       | O(n)      | O(n)      | 1

For F(10):
- Naive: 1,664 function calls
- DP:    19 function calls

IMPROVEMENT: ~87x faster for F(10)!

═══════════════════════════════════════════════════════════════════════════════

WHEN TO USE DYNAMIC PROGRAMMING
==============================

✓ Problem has optimal substructure
✓ Problem has overlapping subproblems
✓ Recursive solution exists but is inefficient
✓ Can identify state transitions

Common DP Problems:
• Fibonacci sequence
• Longest Common Subsequence
• 0/1 Knapsack Problem
• Coin Change Problem
• Edit Distance
• Maximum Subarray Sum