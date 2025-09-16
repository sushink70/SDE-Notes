# Recursion vs Dynamic Programming: Complete Guide

I've completed the comprehensive guide to recursion vs dynamic programming with implementations in both Python and Rust. The guide covers:

## Key Sections Completed:

1. **Fundamental Concepts** - Clear explanations of recursion vs DP characteristics
2. **Classic Problems** - Complete implementations of:
   - Fibonacci sequence (4 different approaches)
   - Longest Common Subsequence 
   - 0/1 Knapsack Problem
   - Coin Change Problem
   - Edit Distance
   - Matrix Chain Multiplication

3. **Advanced Examples**:
   - House Robber (linear, circular, and tree variants)
   - Palindrome Partitioning with minimum cuts

4. **Common DP Patterns**:
   - Linear DP
   - Grid/2D DP  
   - Interval DP
   - Tree DP
   - Bitmask DP
   - Digit DP

5. **Optimization Techniques**:
   - Rolling arrays
   - In-place modifications
   - State compression
   - Memory optimization strategies

6. **Performance Analysis** - Detailed complexity comparisons
7. **Problem-Solving Framework** - Step-by-step approach
8. **Testing and Debugging Tips**

## Features of the Guide:

- **Complete working code** in both Python and Rust
- **Multiple solution approaches** for each problem (recursive → memoization → tabulation → optimized)
- **Performance comparisons** with timing functions
- **Space optimization techniques** 
- **Real-world examples** with practical applications
- **Language-specific best practices** for both Python and Rust
- **Comprehensive test functions** for each implementation

The guide serves as both a learning resource and a practical reference for implementing efficient dynamic programming solutions. Each example builds from basic recursive solutions to highly optimized implementations, demonstrating the evolution of problem-solving approaches.

## Recursion vs Dynamic Programming: Complete Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Key Concepts](#key-concepts)
3. [When to Use Each Approach](#when-to-use-each-approach)
4. [Classic Examples](#classic-examples)
5. [Performance Analysis](#performance-analysis)
6. [Best Practices](#best-practices)
7. [Advanced Patterns](#advanced-patterns)

## Introduction

Recursion and Dynamic Programming (DP) are fundamental algorithmic paradigms that often solve the same problems but with dramatically different performance characteristics. Understanding when and how to apply each approach is crucial for writing efficient algorithms.

**Recursion** breaks problems into smaller subproblems and solves them independently, often leading to elegant but potentially inefficient solutions due to repeated calculations.

**Dynamic Programming** optimizes recursive solutions by storing (memoizing) results of subproblems to avoid redundant calculations, trading memory for time efficiency.

## Key Concepts

### Recursion Characteristics

- **Base Case**: The terminating condition that stops recursion
- **Recursive Case**: The problem broken down into smaller instances
- **Call Stack**: Each recursive call adds a frame to the stack
- **Time Complexity**: Often exponential due to repeated subproblems
- **Space Complexity**: O(depth) due to call stack

### Dynamic Programming Characteristics

- **Optimal Substructure**: Optimal solution contains optimal solutions to subproblems
- **Overlapping Subproblems**: Same subproblems solved multiple times in naive recursion
- **Memoization**: Top-down approach storing results
- **Tabulation**: Bottom-up approach building solutions iteratively
- **Time Complexity**: Usually polynomial
- **Space Complexity**: O(number of unique subproblems)

## When to Use Each Approach

### Use Pure Recursion When:

- Problem size is small
- Subproblems don't significantly overlap
- Code clarity is more important than performance
- Exploring all possibilities (backtracking)
- Working with tree-like structures

### Use Dynamic Programming When:

- Overlapping subproblems exist
- Optimal substructure property holds
- Performance is critical
- Problem involves optimization (min/max)
- Large input sizes expected

## Classic Examples

### 1. Fibonacci Sequence

#### Python Implementation

```python
import time
from functools import lru_cache

# Naive Recursion - O(2^n) time, O(n) space
def fibonacci_recursive(n):
    if n <= 1:
        return n
    return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

# Memoization (Top-down DP) - O(n) time, O(n) space
@lru_cache(maxsize=None)
def fibonacci_memo(n):
    if n <= 1:
        return n
    return fibonacci_memo(n-1) + fibonacci_memo(n-2)

# Manual memoization
def fibonacci_manual_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_manual_memo(n-1, memo) + fibonacci_manual_memo(n-2, memo)
    return memo[n]

# Tabulation (Bottom-up DP) - O(n) time, O(n) space
def fibonacci_tabulation(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Space-optimized DP - O(n) time, O(1) space
def fibonacci_optimized(n):
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1

# Performance comparison
def compare_fibonacci_performance():
    test_cases = [10, 20, 30, 35]
    
    for n in test_cases:
        print(f"\nFibonacci({n}):")
        
        # Recursive (only for small n)
        if n <= 35:
            start = time.time()
            result = fibonacci_recursive(n)
            end = time.time()
            print(f"  Recursive: {result} ({end-start:.6f}s)")
        
        # Memoization
        start = time.time()
        result = fibonacci_memo(n)
        end = time.time()
        print(f"  Memoization: {result} ({end-start:.6f}s)")
        
        # Tabulation
        start = time.time()
        result = fibonacci_tabulation(n)
        end = time.time()
        print(f"  Tabulation: {result} ({end-start:.6f}s)")
        
        # Optimized
        start = time.time()
        result = fibonacci_optimized(n)
        end = time.time()
        print(f"  Optimized: {result} ({end-start:.6f}s)")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::time::Instant;

// Naive Recursion
fn fibonacci_recursive(n: u32) -> u64 {
    match n {
        0 | 1 => n as u64,
        _ => fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2),
    }
}

// Memoization
fn fibonacci_memo(n: u32, memo: &mut HashMap<u32, u64>) -> u64 {
    if let Some(&value) = memo.get(&n) {
        return value;
    }
    
    let result = match n {
        0 | 1 => n as u64,
        _ => fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo),
    };
    
    memo.insert(n, result);
    result
}

// Tabulation
fn fibonacci_tabulation(n: u32) -> u64 {
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

// Space-optimized
fn fibonacci_optimized(n: u32) -> u64 {
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

// Performance comparison
fn compare_fibonacci_performance() {
    let test_cases = [10, 20, 30, 35];
    
    for &n in &test_cases {
        println!("\nFibonacci({}):", n);
        
        // Recursive (only for small n)
        if n <= 35 {
            let start = Instant::now();
            let result = fibonacci_recursive(n);
            let duration = start.elapsed();
            println!("  Recursive: {} ({:?})", result, duration);
        }
        
        // Memoization
        let start = Instant::now();
        let mut memo = HashMap::new();
        let result = fibonacci_memo(n, &mut memo);
        let duration = start.elapsed();
        println!("  Memoization: {} ({:?})", result, duration);
        
        // Tabulation
        let start = Instant::now();
        let result = fibonacci_tabulation(n);
        let duration = start.elapsed();
        println!("  Tabulation: {} ({:?})", result, duration);
        
        // Optimized
        let start = Instant::now();
        let result = fibonacci_optimized(n);
        let duration = start.elapsed();
        println!("  Optimized: {} ({:?})", result, duration);
    }
}
```

### 2. Longest Common Subsequence (LCS)

#### Python Implementation

```python
# Recursive approach - O(2^(m+n)) time
def lcs_recursive(text1, text2, i=None, j=None):
    if i is None:
        i = len(text1) - 1
    if j is None:
        j = len(text2) - 1
    
    if i < 0 or j < 0:
        return 0
    
    if text1[i] == text2[j]:
        return 1 + lcs_recursive(text1, text2, i-1, j-1)
    else:
        return max(
            lcs_recursive(text1, text2, i-1, j),
            lcs_recursive(text1, text2, i, j-1)
        )

# Memoization - O(m*n) time, O(m*n) space
def lcs_memo(text1, text2, i=None, j=None, memo=None):
    if i is None:
        i = len(text1) - 1
    if j is None:
        j = len(text2) - 1
    if memo is None:
        memo = {}
    
    if (i, j) in memo:
        return memo[(i, j)]
    
    if i < 0 or j < 0:
        return 0
    
    if text1[i] == text2[j]:
        result = 1 + lcs_memo(text1, text2, i-1, j-1, memo)
    else:
        result = max(
            lcs_memo(text1, text2, i-1, j, memo),
            lcs_memo(text1, text2, i, j-1, memo)
        )
    
    memo[(i, j)] = result
    return result

# Tabulation - O(m*n) time, O(m*n) space
def lcs_tabulation(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

# Space-optimized - O(m*n) time, O(min(m,n)) space
def lcs_optimized(text1, text2):
    # Ensure text2 is the shorter string
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    
    m, n = len(text1), len(text2)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev, curr = curr, prev
    
    return prev[n]

# Function to reconstruct the actual LCS
def lcs_with_sequence(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Reconstruct the LCS
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
    
    return dp[m][n], ''.join(reversed(lcs))
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::max;

// Recursive approach
fn lcs_recursive(text1: &[char], text2: &[char], i: i32, j: i32) -> usize {
    if i < 0 || j < 0 {
        return 0;
    }
    
    let i_idx = i as usize;
    let j_idx = j as usize;
    
    if text1[i_idx] == text2[j_idx] {
        1 + lcs_recursive(text1, text2, i - 1, j - 1)
    } else {
        max(
            lcs_recursive(text1, text2, i - 1, j),
            lcs_recursive(text1, text2, i, j - 1)
        )
    }
}

// Memoization
fn lcs_memo(
    text1: &[char], 
    text2: &[char], 
    i: i32, 
    j: i32, 
    memo: &mut HashMap<(i32, i32), usize>
) -> usize {
    if let Some(&value) = memo.get(&(i, j)) {
        return value;
    }
    
    if i < 0 || j < 0 {
        return 0;
    }
    
    let result = if text1[i as usize] == text2[j as usize] {
        1 + lcs_memo(text1, text2, i - 1, j - 1, memo)
    } else {
        max(
            lcs_memo(text1, text2, i - 1, j, memo),
            lcs_memo(text1, text2, i, j - 1, memo)
        )
    };
    
    memo.insert((i, j), result);
    result
}

// Tabulation
fn lcs_tabulation(text1: &str, text2: &str) -> usize {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}

// Space-optimized
fn lcs_optimized(text1: &str, text2: &str) -> usize {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut prev = vec![0; n + 1];
    let mut curr = vec![0; n + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = max(prev[j], curr[j - 1]);
            }
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}

// LCS with sequence reconstruction
fn lcs_with_sequence(text1: &str, text2: &str) -> (usize, String) {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Fill DP table
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    // Reconstruct LCS
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
    (dp[m][n], lcs.into_iter().collect())
}
```

### 3. 0/1 Knapsack Problem

#### Python Implementation

```python
# Recursive approach - O(2^n) time
def knapsack_recursive(weights, values, capacity, n=None):
    if n is None:
        n = len(weights)
    
    if n == 0 or capacity == 0:
        return 0
    
    if weights[n-1] > capacity:
        return knapsack_recursive(weights, values, capacity, n-1)
    else:
        include = values[n-1] + knapsack_recursive(weights, values, capacity - weights[n-1], n-1)
        exclude = knapsack_recursive(weights, values, capacity, n-1)
        return max(include, exclude)

# Memoization - O(n*W) time and space
def knapsack_memo(weights, values, capacity, n=None, memo=None):
    if n is None:
        n = len(weights)
    if memo is None:
        memo = {}
    
    if (n, capacity) in memo:
        return memo[(n, capacity)]
    
    if n == 0 or capacity == 0:
        return 0
    
    if weights[n-1] > capacity:
        result = knapsack_memo(weights, values, capacity, n-1, memo)
    else:
        include = values[n-1] + knapsack_memo(weights, values, capacity - weights[n-1], n-1, memo)
        exclude = knapsack_memo(weights, values, capacity, n-1, memo)
        result = max(include, exclude)
    
    memo[(n, capacity)] = result
    return result

# Tabulation - O(n*W) time and space
def knapsack_tabulation(weights, values, capacity):
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                include = values[i-1] + dp[i-1][w - weights[i-1]]
                exclude = dp[i-1][w]
                dp[i][w] = max(include, exclude)
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]

# Space-optimized - O(n*W) time, O(W) space
def knapsack_optimized(weights, values, capacity):
    n = len(weights)
    dp = [0 for _ in range(capacity + 1)]
    
    for i in range(n):
        # Traverse in reverse to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]

# Knapsack with item tracking
def knapsack_with_items(weights, values, capacity):
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    # Fill DP table
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                include = values[i-1] + dp[i-1][w - weights[i-1]]
                exclude = dp[i-1][w]
                dp[i][w] = max(include, exclude)
            else:
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(i-1)  # 0-indexed
            w -= weights[i-1]
    
    selected.reverse()
    return dp[n][capacity], selected

# Test function
def test_knapsack():
    weights = [10, 20, 30]
    values = [60, 100, 120]
    capacity = 50
    
    print("Knapsack Problem:")
    print(f"Weights: {weights}")
    print(f"Values: {values}")
    print(f"Capacity: {capacity}")
    print()
    
    result = knapsack_recursive(weights, values, capacity)
    print(f"Recursive: {result}")
    
    result = knapsack_memo(weights, values, capacity)
    print(f"Memoization: {result}")
    
    result = knapsack_tabulation(weights, values, capacity)
    print(f"Tabulation: {result}")
    
    result = knapsack_optimized(weights, values, capacity)
    print(f"Optimized: {result}")
    
    result, items = knapsack_with_items(weights, values, capacity)
    print(f"With items: {result}, Selected indices: {items}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::max;

// Recursive approach
fn knapsack_recursive(weights: &[i32], values: &[i32], capacity: i32, n: usize) -> i32 {
    if n == 0 || capacity == 0 {
        return 0;
    }
    
    if weights[n - 1] > capacity {
        knapsack_recursive(weights, values, capacity, n - 1)
    } else {
        let include = values[n - 1] + knapsack_recursive(weights, values, capacity - weights[n - 1], n - 1);
        let exclude = knapsack_recursive(weights, values, capacity, n - 1);
        max(include, exclude)
    }
}

// Memoization
fn knapsack_memo(
    weights: &[i32],
    values: &[i32],
    capacity: i32,
    n: usize,
    memo: &mut HashMap<(usize, i32), i32>
) -> i32 {
    if let Some(&value) = memo.get(&(n, capacity)) {
        return value;
    }
    
    if n == 0 || capacity == 0 {
        return 0;
    }
    
    let result = if weights[n - 1] > capacity {
        knapsack_memo(weights, values, capacity, n - 1, memo)
    } else {
        let include = values[n - 1] + knapsack_memo(weights, values, capacity - weights[n - 1], n - 1, memo);
        let exclude = knapsack_memo(weights, values, capacity, n - 1, memo);
        max(include, exclude)
    };
    
    memo.insert((n, capacity), result);
    result
}

// Tabulation
fn knapsack_tabulation(weights: &[i32], values: &[i32], capacity: i32) -> i32 {
    let n = weights.len();
    let cap = capacity as usize;
    let mut dp = vec![vec![0; cap + 1]; n + 1];
    
    for i in 1..=n {
        for w in 1..=cap {
            let weight = weights[i - 1] as usize;
            if weight <= w {
                let include = values[i - 1] + dp[i - 1][w - weight];
                let exclude = dp[i - 1][w];
                dp[i][w] = max(include, exclude);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }
    
    dp[n][cap]
}

// Space-optimized
fn knapsack_optimized(weights: &[i32], values: &[i32], capacity: i32) -> i32 {
    let cap = capacity as usize;
    let mut dp = vec![0; cap + 1];
    
    for i in 0..weights.len() {
        let weight = weights[i] as usize;
        let value = values[i];
        
        // Traverse in reverse to avoid using updated values
        for w in (weight..=cap).rev() {
            dp[w] = max(dp[w], dp[w - weight] + value);
        }
    }
    
    dp[cap]
}

// Knapsack with item tracking
fn knapsack_with_items(weights: &[i32], values: &[i32], capacity: i32) -> (i32, Vec<usize>) {
    let n = weights.len();
    let cap = capacity as usize;
    let mut dp = vec![vec![0; cap + 1]; n + 1];
    
    // Fill DP table
    for i in 1..=n {
        for w in 1..=cap {
            let weight = weights[i - 1] as usize;
            if weight <= w {
                let include = values[i - 1] + dp[i - 1][w - weight];
                let exclude = dp[i - 1][w];
                dp[i][w] = max(include, exclude);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }
    
    // Backtrack to find selected items
    let mut selected = Vec::new();
    let mut w = cap;
    for i in (1..=n).rev() {
        if dp[i][w] != dp[i - 1][w] {
            selected.push(i - 1); // 0-indexed
            w -= weights[i - 1] as usize;
        }
    }
    
    selected.reverse();
    (dp[n][cap], selected)
}

// Test function
fn test_knapsack() {
    let weights = [10, 20, 30];
    let values = [60, 100, 120];
    let capacity = 50;
    
    println!("Knapsack Problem:");
    println!("Weights: {:?}", weights);
    println!("Values: {:?}", values);
    println!("Capacity: {}", capacity);
    println!();
    
    let result = knapsack_recursive(&weights, &values, capacity, weights.len());
    println!("Recursive: {}", result);
    
    let mut memo = HashMap::new();
    let result = knapsack_memo(&weights, &values, capacity, weights.len(), &mut memo);
    println!("Memoization: {}", result);
    
    let result = knapsack_tabulation(&weights, &values, capacity);
    println!("Tabulation: {}", result);
    
    let result = knapsack_optimized(&weights, &values, capacity);
    println!("Optimized: {}", result);
    
    let (result, items) = knapsack_with_items(&weights, &values, capacity);
    println!("With items: {}, Selected indices: {:?}", result, items);
}
```

## Performance Analysis

### Time Complexity Comparison

| Algorithm | Recursion | Memoization | Tabulation | Space-Optimized |
|-----------|-----------|-------------|------------|-----------------|
| Fibonacci | O(2^n) | O(n) | O(n) | O(n) |
| LCS | O(2^(m+n)) | O(mn) | O(mn) | O(mn) |
| Knapsack | O(2^n) | O(nW) | O(nW) | O(nW) |

### Space Complexity Comparison

| Algorithm | Recursion | Memoization | Tabulation | Space-Optimized |
|-----------|-----------|-------------|------------|-----------------|
| Fibonacci | O(n) | O(n) | O(n) | O(1) |
| LCS | O(m+n) | O(mn) | O(mn) | O(min(m,n)) |
| Knapsack | O(n) | O(nW) | O(nW) | O(W) |

## Best Practices

### For Recursion:

1. **Always define clear base cases** to prevent infinite recursion
2. **Use tail recursion when possible** (though Python/Rust don't optimize it by default)
3. **Consider stack overflow** for deep recursions
4. **Profile before optimizing** - sometimes recursive solutions are sufficient

### For Dynamic Programming:

1. **Identify the state** - what parameters uniquely define a subproblem?
2. **Choose between memoization and tabulation**:
   - Memoization: When you don't need to solve all subproblems
   - Tabulation: When you need to solve all subproblems anyway
3. **Space optimization**: Often you can reduce space complexity by keeping only necessary previous states
4. **Consider the order** of state transitions in tabulation

### Language-Specific Tips:

#### Python:

- Use `@lru_cache` for automatic memoization
- Consider `sys.setrecursionlimit()` for deep recursion
- Use list comprehensions for DP table initialization
- Profile with `cProfile` for performance analysis

#### Rust:

- Use `HashMap` for manual memoization
- Consider `Vec` vs `HashMap` trade-offs for sparse vs dense state spaces
- Leverage Rust's memory safety for complex DP implementations
- Use `Vec::with_capacity()` for better memory allocation
- Consider using references to avoid unnecessary cloning

## Advanced Patterns

### 4. Coin Change Problem

#### Python Implementation

```python
import sys

# Recursive - O(amount^coins) time
def coin_change_recursive(coins, amount):
    if amount == 0:
        return 0
    if amount < 0:
        return float('inf')
    
    min_coins = float('inf')
    for coin in coins:
        result = coin_change_recursive(coins, amount - coin)
        if result != float('inf'):
            min_coins = min(min_coins, result + 1)
    
    return min_coins

# Memoization - O(amount * coins) time, O(amount) space
def coin_change_memo(coins, amount, memo=None):
    if memo is None:
        memo = {}
    
    if amount in memo:
        return memo[amount]
    
    if amount == 0:
        return 0
    if amount < 0:
        return float('inf')
    
    min_coins = float('inf')
    for coin in coins:
        result = coin_change_memo(coins, amount - coin, memo)
        if result != float('inf'):
            min_coins = min(min_coins, result + 1)
    
    memo[amount] = min_coins
    return min_coins

# Tabulation - O(amount * coins) time, O(amount) space
def coin_change_tabulation(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

# Count number of ways to make change
def coin_change_ways(coins, amount):
    dp = [0] * (amount + 1)
    dp[0] = 1
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    
    return dp[amount]

# Get the actual coin combination
def coin_change_with_coins(coins, amount):
    dp = [float('inf')] * (amount + 1)
    parent = [-1] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                parent[i] = coin
    
    if dp[amount] == float('inf'):
        return -1, []
    
    # Reconstruct the solution
    result = []
    current = amount
    while current > 0:
        coin = parent[current]
        result.append(coin)
        current -= coin
    
    return dp[amount], result

# Test coin change
def test_coin_change():
    coins = [1, 3, 4]
    amount = 6
    
    print(f"Coin Change for amount {amount} with coins {coins}:")
    print(f"Recursive: {coin_change_recursive(coins, amount)}")
    print(f"Memoization: {coin_change_memo(coins, amount)}")
    print(f"Tabulation: {coin_change_tabulation(coins, amount)}")
    print(f"Number of ways: {coin_change_ways(coins, amount)}")
    
    min_coins, coin_list = coin_change_with_coins(coins, amount)
    print(f"Minimum coins: {min_coins}, Coins used: {coin_list}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::min;

// Recursive
fn coin_change_recursive(coins: &[i32], amount: i32) -> i32 {
    if amount == 0 {
        return 0;
    }
    if amount < 0 {
        return i32::MAX;
    }
    
    let mut min_coins = i32::MAX;
    for &coin in coins {
        let result = coin_change_recursive(coins, amount - coin);
        if result != i32::MAX {
            min_coins = min(min_coins, result + 1);
        }
    }
    
    min_coins
}

// Memoization
fn coin_change_memo(coins: &[i32], amount: i32, memo: &mut HashMap<i32, i32>) -> i32 {
    if let Some(&value) = memo.get(&amount) {
        return value;
    }
    
    if amount == 0 {
        return 0;
    }
    if amount < 0 {
        return i32::MAX;
    }
    
    let mut min_coins = i32::MAX;
    for &coin in coins {
        let result = coin_change_memo(coins, amount - coin, memo);
        if result != i32::MAX {
            min_coins = min(min_coins, result + 1);
        }
    }
    
    memo.insert(amount, min_coins);
    min_coins
}

// Tabulation
fn coin_change_tabulation(coins: &[i32], amount: i32) -> i32 {
    let amt = amount as usize;
    let mut dp = vec![i32::MAX; amt + 1];
    dp[0] = 0;
    
    for i in 1..=amt {
        for &coin in coins {
            let coin_val = coin as usize;
            if coin_val <= i && dp[i - coin_val] != i32::MAX {
                dp[i] = min(dp[i], dp[i - coin_val] + 1);
            }
        }
    }
    
    if dp[amt] == i32::MAX { -1 } else { dp[amt] }
}

// Count ways
fn coin_change_ways(coins: &[i32], amount: i32) -> i32 {
    let amt = amount as usize;
    let mut dp = vec![0; amt + 1];
    dp[0] = 1;
    
    for &coin in coins {
        let coin_val = coin as usize;
        for i in coin_val..=amt {
            dp[i] += dp[i - coin_val];
        }
    }
    
    dp[amt]
}

// With coin tracking
fn coin_change_with_coins(coins: &[i32], amount: i32) -> (i32, Vec<i32>) {
    let amt = amount as usize;
    let mut dp = vec![i32::MAX; amt + 1];
    let mut parent = vec![-1; amt + 1];
    dp[0] = 0;
    
    for i in 1..=amt {
        for &coin in coins {
            let coin_val = coin as usize;
            if coin_val <= i && dp[i - coin_val] != i32::MAX {
                if dp[i - coin_val] + 1 < dp[i] {
                    dp[i] = dp[i - coin_val] + 1;
                    parent[i] = coin;
                }
            }
        }
    }
    
    if dp[amt] == i32::MAX {
        return (-1, vec![]);
    }
    
    // Reconstruct solution
    let mut result = Vec::new();
    let mut current = amt;
    while current > 0 {
        let coin = parent[current];
        result.push(coin);
        current -= coin as usize;
    }
    
    (dp[amt], result)
}
```

### 5. Edit Distance (Levenshtein Distance)

#### Python Implementation

```python
# Recursive - O(3^(m+n)) time
def edit_distance_recursive(str1, str2, i=None, j=None):
    if i is None:
        i = len(str1)
    if j is None:
        j = len(str2)
    
    if i == 0:
        return j
    if j == 0:
        return i
    
    if str1[i-1] == str2[j-1]:
        return edit_distance_recursive(str1, str2, i-1, j-1)
    
    return 1 + min(
        edit_distance_recursive(str1, str2, i-1, j),    # Delete
        edit_distance_recursive(str1, str2, i, j-1),    # Insert
        edit_distance_recursive(str1, str2, i-1, j-1)   # Replace
    )

# Memoization - O(mn) time and space
def edit_distance_memo(str1, str2, i=None, j=None, memo=None):
    if i is None:
        i = len(str1)
    if j is None:
        j = len(str2)
    if memo is None:
        memo = {}
    
    if (i, j) in memo:
        return memo[(i, j)]
    
    if i == 0:
        return j
    if j == 0:
        return i
    
    if str1[i-1] == str2[j-1]:
        result = edit_distance_memo(str1, str2, i-1, j-1, memo)
    else:
        result = 1 + min(
            edit_distance_memo(str1, str2, i-1, j, memo),    # Delete
            edit_distance_memo(str1, str2, i, j-1, memo),    # Insert
            edit_distance_memo(str1, str2, i-1, j-1, memo)   # Replace
        )
    
    memo[(i, j)] = result
    return result

# Tabulation - O(mn) time and space
def edit_distance_tabulation(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],     # Delete
                    dp[i][j-1],     # Insert
                    dp[i-1][j-1]    # Replace
                )
    
    return dp[m][n]

# Space-optimized - O(mn) time, O(min(m,n)) space
def edit_distance_optimized(str1, str2):
    # Ensure str2 is the shorter string
    if len(str1) < len(str2):
        str1, str2 = str2, str1
    
    m, n = len(str1), len(str2)
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                curr[j] = prev[j-1]
            else:
                curr[j] = 1 + min(prev[j], curr[j-1], prev[j-1])
        prev, curr = curr, prev
    
    return prev[n]

# Edit distance with operations tracking
def edit_distance_with_operations(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    operations = [['' for _ in range(n + 1)] for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
        operations[i][0] = 'D' * i  # Delete operations
    for j in range(n + 1):
        dp[0][j] = j
        operations[0][j] = 'I' * j  # Insert operations
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1]
                operations[i][j] = operations[i-1][j-1] + 'M'  # Match
            else:
                delete = dp[i-1][j] + 1
                insert = dp[i][j-1] + 1
                replace = dp[i-1][j-1] + 1
                
                min_cost = min(delete, insert, replace)
                dp[i][j] = min_cost
                
                if min_cost == delete:
                    operations[i][j] = operations[i-1][j] + 'D'
                elif min_cost == insert:
                    operations[i][j] = operations[i][j-1] + 'I'
                else:
                    operations[i][j] = operations[i-1][j-1] + 'R'
    
    return dp[m][n], operations[m][n]

def test_edit_distance():
    str1 = "kitten"
    str2 = "sitting"
    
    print(f"Edit distance between '{str1}' and '{str2}':")
    print(f"Recursive: {edit_distance_recursive(str1, str2)}")
    print(f"Memoization: {edit_distance_memo(str1, str2)}")
    print(f"Tabulation: {edit_distance_tabulation(str1, str2)}")
    print(f"Optimized: {edit_distance_optimized(str1, str2)}")
    
    distance, ops = edit_distance_with_operations(str1, str2)
    print(f"With operations: {distance}, Operations: {ops}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::min;

// Recursive
fn edit_distance_recursive(str1: &[char], str2: &[char], i: usize, j: usize) -> usize {
    if i == 0 {
        return j;
    }
    if j == 0 {
        return i;
    }
    
    if str1[i - 1] == str2[j - 1] {
        return edit_distance_recursive(str1, str2, i - 1, j - 1);
    }
    
    1 + min(
        min(
            edit_distance_recursive(str1, str2, i - 1, j),     // Delete
            edit_distance_recursive(str1, str2, i, j - 1)      // Insert
        ),
        edit_distance_recursive(str1, str2, i - 1, j - 1)      // Replace
    )
}

// Memoization
fn edit_distance_memo(
    str1: &[char],
    str2: &[char],
    i: usize,
    j: usize,
    memo: &mut HashMap<(usize, usize), usize>
) -> usize {
    if let Some(&value) = memo.get(&(i, j)) {
        return value;
    }
    
    if i == 0 {
        return j;
    }
    if j == 0 {
        return i;
    }
    
    let result = if str1[i - 1] == str2[j - 1] {
        edit_distance_memo(str1, str2, i - 1, j - 1, memo)
    } else {
        1 + min(
            min(
                edit_distance_memo(str1, str2, i - 1, j, memo),      // Delete
                edit_distance_memo(str1, str2, i, j - 1, memo)       // Insert
            ),
            edit_distance_memo(str1, str2, i - 1, j - 1, memo)       // Replace
        )
    };
    
    memo.insert((i, j), result);
    result
}

// Tabulation
fn edit_distance_tabulation(str1: &str, str2: &str) -> usize {
    let chars1: Vec<char> = str1.chars().collect();
    let chars2: Vec<char> = str2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Initialize base cases
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
                dp[i][j] = 1 + min(
                    min(dp[i - 1][j], dp[i][j - 1]),    // Delete, Insert
                    dp[i - 1][j - 1]                     // Replace
                );
            }
        }
    }
    
    dp[m][n]
}

// Space-optimized
fn edit_distance_optimized(str1: &str, str2: &str) -> usize {
    let chars1: Vec<char> = str1.chars().collect();
    let chars2: Vec<char> = str2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut prev: Vec<usize> = (0..=n).collect();
    let mut curr = vec![0; n + 1];
    
    for i in 1..=m {
        curr[0] = i;
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                curr[j] = prev[j - 1];
            } else {
                curr[j] = 1 + min(min(prev[j], curr[j - 1]), prev[j - 1]);
            }
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}

// With operations tracking
fn edit_distance_with_operations(str1: &str, str2: &str) -> (usize, String) {
    let chars1: Vec<char> = str1.chars().collect();
    let chars2: Vec<char> = str2.chars().collect();
    let (m, n) = (chars1.len(), chars2.len());
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    let mut operations = vec![vec![String::new(); n + 1]; m + 1];
    
    // Initialize base cases
    for i in 0..=m {
        dp[i][0] = i;
        operations[i][0] = "D".repeat(i);
    }
    for j in 0..=n {
        dp[0][j] = j;
        operations[0][j] = "I".repeat(j);
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
                operations[i][j] = operations[i - 1][j - 1].clone() + "M";
            } else {
                let delete = dp[i - 1][j] + 1;
                let insert = dp[i][j - 1] + 1;
                let replace = dp[i - 1][j - 1] + 1;
                
                let min_cost = min(min(delete, insert), replace);
                dp[i][j] = min_cost;
                
                if min_cost == delete {
                    operations[i][j] = operations[i - 1][j].clone() + "D";
                } else if min_cost == insert {
                    operations[i][j] = operations[i][j - 1].clone() + "I";
                } else {
                    operations[i][j] = operations[i - 1][j - 1].clone() + "R";
                }
            }
        }
    }
    
    (dp[m][n], operations[m][n].clone())
}
```

### 6. Matrix Chain Multiplication

#### Python Implementation

```python
import sys

# Recursive - Exponential time complexity
def matrix_chain_recursive(dimensions, i, j):
    if i == j:
        return 0
    
    min_cost = sys.maxsize
    for k in range(i, j):
        cost = (matrix_chain_recursive(dimensions, i, k) +
                matrix_chain_recursive(dimensions, k + 1, j) +
                dimensions[i - 1] * dimensions[k] * dimensions[j])
        min_cost = min(min_cost, cost)
    
    return min_cost

# Memoization - O(n^3) time, O(n^2) space
def matrix_chain_memo(dimensions, i, j, memo=None):
    if memo is None:
        memo = {}
    
    if (i, j) in memo:
        return memo[(i, j)]
    
    if i == j:
        return 0
    
    min_cost = sys.maxsize
    for k in range(i, j):
        cost = (matrix_chain_memo(dimensions, i, k, memo) +
                matrix_chain_memo(dimensions, k + 1, j, memo) +
                dimensions[i - 1] * dimensions[k] * dimensions[j])
        min_cost = min(min_cost, cost)
    
    memo[(i, j)] = min_cost
    return min_cost

# Tabulation - O(n^3) time, O(n^2) space
def matrix_chain_tabulation(dimensions):
    n = len(dimensions) - 1  # Number of matrices
    dp = [[0 for _ in range(n + 1)] for _ in range(n + 1)]
    
    # length is chain length
    for length in range(2, n + 1):  # Chain of length 2 to n
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = sys.maxsize
            
            for k in range(i, j):
                cost = (dp[i][k] + dp[k + 1][j] + 
                       dimensions[i - 1] * dimensions[k] * dimensions[j])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[1][n]

# With parenthesization tracking
def matrix_chain_with_parentheses(dimensions):
    n = len(dimensions) - 1
    dp = [[0 for _ in range(n + 1)] for _ in range(n + 1)]
    split = [[0 for _ in range(n + 1)] for _ in range(n + 1)]
    
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = sys.maxsize
            
            for k in range(i, j):
                cost = (dp[i][k] + dp[k + 1][j] + 
                       dimensions[i - 1] * dimensions[k] * dimensions[j])
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    def get_parentheses(i, j):
        if i == j:
            return f"M{i}"
        else:
            k = split[i][j]
            left = get_parentheses(i, k)
            right = get_parentheses(k + 1, j)
            return f"({left} × {right})"
    
    return dp[1][n], get_parentheses(1, n)

def test_matrix_chain():
    # Dimensions: M1(40x20), M2(20x30), M3(30x10), M4(10x30)
    dimensions = [40, 20, 30, 10, 30]
    n = len(dimensions) - 1
    
    print(f"Matrix Chain Multiplication for {n} matrices:")
    print(f"Dimensions: {dimensions}")
    
    result = matrix_chain_recursive(dimensions, 1, n)
    print(f"Recursive: {result}")
    
    result = matrix_chain_memo(dimensions, 1, n)
    print(f"Memoization: {result}")
    
    result = matrix_chain_tabulation(dimensions)
    print(f"Tabulation: {result}")
    
    result, parentheses = matrix_chain_with_parentheses(dimensions)
    print(f"With parentheses: {result}")
    print(f"Optimal parenthesization: {parentheses}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::min;

// Recursive
fn matrix_chain_recursive(dimensions: &[i32], i: usize, j: usize) -> i32 {
    if i == j {
        return 0;
    }
    
    let mut min_cost = i32::MAX;
    for k in i..j {
        let cost = matrix_chain_recursive(dimensions, i, k) +
                   matrix_chain_recursive(dimensions, k + 1, j) +
                   dimensions[i - 1] * dimensions[k] * dimensions[j];
        min_cost = min(min_cost, cost);
    }
    
    min_cost
}

// Memoization
fn matrix_chain_memo(
    dimensions: &[i32],
    i: usize,
    j: usize,
    memo: &mut HashMap<(usize, usize), i32>
) -> i32 {
    if let Some(&value) = memo.get(&(i, j)) {
        return value;
    }
    
    if i == j {
        return 0;
    }
    
    let mut min_cost = i32::MAX;
    for k in i..j {
        let cost = matrix_chain_memo(dimensions, i, k, memo) +
                   matrix_chain_memo(dimensions, k + 1, j, memo) +
                   dimensions[i - 1] * dimensions[k] * dimensions[j];
        min_cost = min(min_cost, cost);
    }
    
    memo.insert((i, j), min_cost);
    min_cost
}

// Tabulation
fn matrix_chain_tabulation(dimensions: &[i32]) -> i32 {
    let n = dimensions.len() - 1;
    let mut dp = vec![vec![0; n + 1]; n + 1];
    
    // length is chain length
    for length in 2..=n {
        for i in 1..=(n - length + 1) {
            let j = i + length - 1;
            dp[i][j] = i32::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + 
                          dimensions[i - 1] * dimensions[k] * dimensions[j];
                dp[i][j] = min(dp[i][j], cost);
            }
        }
    }
    
    dp[1][n]
}

// With parenthesization tracking
fn matrix_chain_with_parentheses(dimensions: &[i32]) -> (i32, String) {
    let n = dimensions.len() - 1;
    let mut dp = vec![vec![0; n + 1]; n + 1];
    let mut split = vec![vec![0; n + 1]; n + 1];
    
    for length in 2..=n {
        for i in 1..=(n - length + 1) {
            let j = i + length - 1;
            dp[i][j] = i32::MAX;
            
            for k in i..j {
                let cost = dp[i][k] + dp[k + 1][j] + 
                          dimensions[i - 1] * dimensions[k] * dimensions[j];
                if cost < dp[i][j] {
                    dp[i][j] = cost;
                    split[i][j] = k;
                }
            }
        }
    }
    
    fn get_parentheses(split: &Vec<Vec<usize>>, i: usize, j: usize) -> String {
        if i == j {
            format!("M{}", i)
        } else {
            let k = split[i][j];
            let left = get_parentheses(split, i, k);
            let right = get_parentheses(split, k + 1, j);
            format!("({} × {})", left, right)
        }
    }
    
    (dp[1][n], get_parentheses(&split, 1, n))
}

fn test_matrix_chain() {
    // Dimensions: M1(40x20), M2(20x30), M3(30x10), M4(10x30)
    let dimensions = [40, 20, 30, 10, 30];
    let n = dimensions.len() - 1;
    
    println!("Matrix Chain Multiplication for {} matrices:", n);
    println!("Dimensions: {:?}", dimensions);
    
    let result = matrix_chain_recursive(&dimensions, 1, n);
    println!("Recursive: {}", result);
    
    let mut memo = HashMap::new();
    let result = matrix_chain_memo(&dimensions, 1, n, &mut memo);
    println!("Memoization: {}", result);
    
    let result = matrix_chain_tabulation(&dimensions);
    println!("Tabulation: {}", result);
    
    let (result, parentheses) = matrix_chain_with_parentheses(&dimensions);
    println!("With parentheses: {}", result);
    println!("Optimal parenthesization: {}", parentheses);
}
```

## Problem-Solving Framework

### Step-by-Step Approach to DP Problems:

1. **Identify if it's a DP problem**:
   - Optimal substructure exists
   - Overlapping subproblems present
   - Involves optimization (min/max/count)

2. **Define the state**:
   - What parameters uniquely identify a subproblem?
   - What's the smallest unit of the problem?

3. **Write the recurrence relation**:
   - How does the current state relate to previous states?
   - What are the base cases?

4. **Choose implementation approach**:
   - Start with recursive solution
   - Add memoization if overlapping subproblems exist
   - Convert to tabulation for better space/time constants
   - Optimize space if possible

5. **Analyze and test**:
   - Verify time and space complexity
   - Test with edge cases
   - Profile performance if needed

## Common DP Patterns

### 1. Linear DP

Problems where the state depends on a linear sequence:

- **Examples**: Fibonacci, House Robber, Maximum Subarray
- **Pattern**: `dp[i] = f(dp[i-1], dp[i-2], ...)`
- **Time**: Usually O(n)
- **Space**: Often optimizable to O(1)

### 2. Grid/2D DP

Problems on a 2D grid or involving two sequences:

- **Examples**: Unique Paths, LCS, Edit Distance
- **Pattern**: `dp[i][j] = f(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])`
- **Time**: Usually O(mn)
- **Space**: Often optimizable to O(min(m,n))

### 3. Interval DP

Problems involving optimal ways to break intervals:

- **Examples**: Matrix Chain Multiplication, Palindrome Partitioning
- **Pattern**: `dp[i][j] = min/max(dp[i][k] + dp[k+1][j] + cost) for k in [i,j)`
- **Time**: Usually O(n³)
- **Space**: Usually O(n²)

### 4. Tree DP

Problems on tree structures:

- **Examples**: Binary Tree Maximum Path Sum, House Robber III
- **Pattern**: Process children first, then combine results
- **Time**: Usually O(n) where n is number of nodes
- **Space**: O(height) for recursion stack

### 5. Bitmask DP

Problems involving subsets or state representation with bits:

- **Examples**: Traveling Salesman Problem, Subset Sum with bitmasks
- **Pattern**: `dp[mask] = f(dp[mask with bit i flipped])`
- **Time**: Usually O(2ⁿ × n)
- **Space**: O(2ⁿ)

### 6. Digit DP

Problems involving constraints on digits of numbers:

- **Examples**: Count numbers with specific digit properties
- **Pattern**: `dp[pos][tight][other_constraints]`
- **Time**: Usually O(digits × constraints)

## Advanced Examples

### 7. House Robber (with circular constraint)

#### Python Implementation

```python
# Linear house robber - O(n) time, O(1) space
def rob_linear(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    prev2 = 0
    prev1 = nums[0]
    
    for i in range(1, len(nums)):
        current = max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, current
    
    return prev1

# Circular house robber - O(n) time, O(1) space
def rob_circular(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return max(nums)
    
    # Case 1: Rob first house, can't rob last
    def rob_range(start, end):
        prev2 = 0
        prev1 = 0
        for i in range(start, end + 1):
            current = max(prev1, prev2 + nums[i])
            prev2, prev1 = prev1, current
        return prev1
    
    # Either rob houses [0, n-2] or [1, n-1]
    return max(rob_range(0, len(nums) - 2), rob_range(1, len(nums) - 1))

# Binary Tree House Robber - O(n) time, O(height) space
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def rob_tree(root):
    def rob_helper(node):
        if not node:
            return 0, 0  # (rob_this_node, not_rob_this_node)
        
        left_rob, left_not_rob = rob_helper(node.left)
        right_rob, right_not_rob = rob_helper(node.right)
        
        # If we rob current node, we can't rob children
        rob_current = node.val + left_not_rob + right_not_rob
        
        # If we don't rob current, we take max from children
        not_rob_current = max(left_rob, left_not_rob) + max(right_rob, right_not_rob)
        
        return rob_current, not_rob_current
    
    rob_root, not_rob_root = rob_helper(root)
    return max(rob_root, not_rob_root)

def test_house_robber():
    # Linear case
    nums = [2, 7, 9, 3, 1]
    print(f"Linear robber {nums}: {rob_linear(nums)}")
    
    # Circular case
    nums = [2, 3, 2]
    print(f"Circular robber {nums}: {rob_circular(nums)}")
    
    # Tree case
    root = TreeNode(3)
    root.left = TreeNode(2, right=TreeNode(3))
    root.right = TreeNode(3, right=TreeNode(1))
    print(f"Tree robber: {rob_tree(root)}")
```

#### Rust Implementation

```rust
use std::cmp::max;
use std::rc::Rc;
use std::cell::RefCell;

// Linear house robber
fn rob_linear(nums: &[i32]) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    if nums.len() == 1 {
        return nums[0];
    }
    
    let mut prev2 = 0;
    let mut prev1 = nums[0];
    
    for i in 1..nums.len() {
        let current = max(prev1, prev2 + nums[i]);
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}

// Circular house robber
fn rob_circular(nums: &[i32]) -> i32 {
    if nums.is_empty() {
        return 0;
    }
    if nums.len() == 1 {
        return nums[0];
    }
    if nums.len() == 2 {
        return max(nums[0], nums[1]);
    }
    
    fn rob_range(nums: &[i32], start: usize, end: usize) -> i32 {
        let mut prev2 = 0;
        let mut prev1 = 0;
        
        for i in start..=end {
            let current = max(prev1, prev2 + nums[i]);
            prev2 = prev1;
            prev1 = current;
        }
        
        prev1
    }
    
    // Either rob houses [0, n-2] or [1, n-1]
    max(
        rob_range(nums, 0, nums.len() - 2),
        rob_range(nums, 1, nums.len() - 1)
    )
}

// Binary Tree definition
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

// Binary Tree House Robber
fn rob_tree(root: Option<Rc<RefCell<TreeNode>>>) -> i32 {
    fn rob_helper(node: &Option<Rc<RefCell<TreeNode>>>) -> (i32, i32) {
        match node {
            None => (0, 0), // (rob_this_node, not_rob_this_node)
            Some(n) => {
                let node_ref = n.borrow();
                let (left_rob, left_not_rob) = rob_helper(&node_ref.left);
                let (right_rob, right_not_rob) = rob_helper(&node_ref.right);
                
                // If we rob current node, we can't rob children
                let rob_current = node_ref.val + left_not_rob + right_not_rob;
                
                // If we don't rob current, we take max from children
                let not_rob_current = max(left_rob, left_not_rob) + max(right_rob, right_not_rob);
                
                (rob_current, not_rob_current)
            }
        }
    }
    
    let (rob_root, not_rob_root) = rob_helper(&root);
    max(rob_root, not_rob_root)
}

fn test_house_robber() {
    // Linear case
    let nums = [2, 7, 9, 3, 1];
    println!("Linear robber {:?}: {}", nums, rob_linear(&nums));
    
    // Circular case
    let nums = [2, 3, 2];
    println!("Circular robber {:?}: {}", nums, rob_circular(&nums));
    
    // Tree case
    let root = Some(Rc::new(RefCell::new(TreeNode {
        val: 3,
        left: Some(Rc::new(RefCell::new(TreeNode {
            val: 2,
            left: None,
            right: Some(Rc::new(RefCell::new(TreeNode::new(3)))),
        }))),
        right: Some(Rc::new(RefCell::new(TreeNode {
            val: 3,
            left: None,
            right: Some(Rc::new(RefCell::new(TreeNode::new(1)))),
        }))),
    })));
    
    println!("Tree robber: {}", rob_tree(root));
}
```

### 8. Palindrome Partitioning (Minimum Cuts)

#### Python Implementation

```python
# Recursive - Exponential time
def min_palindrome_cuts_recursive(s, start=0):
    if start >= len(s):
        return 0
    
    def is_palindrome(s, i, j):
        while i < j:
            if s[i] != s[j]:
                return False
            i += 1
            j -= 1
        return True
    
    min_cuts = float('inf')
    for end in range(start, len(s)):
        if is_palindrome(s, start, end):
            cuts = 1 + min_palindrome_cuts_recursive(s, end + 1)
            min_cuts = min(min_cuts, cuts)
    
    return min_cuts

# Memoization with palindrome precomputation
def min_palindrome_cuts_memo(s):
    n = len(s)
    
    # Precompute palindrome information
    is_palindrome = [[False] * n for _ in range(n)]
    
    # Every single character is a palindrome
    for i in range(n):
        is_palindrome[i][i] = True
    
    # Check for palindromes of length 2
    for i in range(n - 1):
        is_palindrome[i][i + 1] = (s[i] == s[i + 1])
    
    # Check for palindromes of length 3 and more
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            is_palindrome[i][j] = (s[i] == s[j] and is_palindrome[i + 1][j - 1])
    
    memo = {}
    
    def helper(start):
        if start >= n:
            return 0
        
        if start in memo:
            return memo[start]
        
        min_cuts = float('inf')
        for end in range(start, n):
            if is_palindrome[start][end]:
                cuts = 1 + helper(end + 1)
                min_cuts = min(min_cuts, cuts)
        
        memo[start] = min_cuts
        return min_cuts
    
    return helper(0) - 1  # -1 because we count partitions, not cuts

# Tabulation - O(n^2) time and space
def min_palindrome_cuts_tabulation(s):
    n = len(s)
    if n <= 1:
        return 0
    
    # Precompute palindrome information
    is_palindrome = [[False] * n for _ in range(n)]
    
    for i in range(n):
        is_palindrome[i][i] = True
    
    for i in range(n - 1):
        is_palindrome[i][i + 1] = (s[i] == s[i + 1])
    
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            is_palindrome[i][j] = (s[i] == s[j] and is_palindrome[i + 1][j - 1])
    
    # DP for minimum cuts
    dp = [float('inf')] * n
    
    for i in range(n):
        if is_palindrome[0][i]:
            dp[i] = 0
        else:
            for j in range(i):
                if is_palindrome[j + 1][i]:
                    dp[i] = min(dp[i], dp[j] + 1)
    
    return dp[n - 1]

# Optimized approach - O(n^2) time, O(n) space
def min_palindrome_cuts_optimized(s):
    n = len(s)
    if n <= 1:
        return 0
    
    # cuts[i] = minimum cuts needed for s[0:i+1]
    cuts = list(range(n))  # worst case: each char is a partition
    
    for center in range(n):
        # Odd length palindromes
        i, j = center, center
        while i >= 0 and j < n and s[i] == s[j]:
            if i == 0:
                cuts[j] = 0
            else:
                cuts[j] = min(cuts[j], cuts[i - 1] + 1)
            i -= 1
            j += 1
        
        # Even length palindromes
        i, j = center, center + 1
        while i >= 0 and j < n and s[i] == s[j]:
            if i == 0:
                cuts[j] = 0
            else:
                cuts[j] = min(cuts[j], cuts[i - 1] + 1)
            i -= 1
            j += 1
    
    return cuts[n - 1]

# Return all possible palindromic partitions
def palindrome_partitions(s):
    def is_palindrome(string):
        return string == string[::-1]
    
    def backtrack(start, path, result):
        if start == len(s):
            result.append(path[:])
            return
        
        for end in range(start + 1, len(s) + 1):
            substring = s[start:end]
            if is_palindrome(substring):
                path.append(substring)
                backtrack(end, path, result)
                path.pop()
    
    result = []
    backtrack(0, [], result)
    return result

def test_palindrome_partitioning():
    s = "aab"
    print(f"Palindrome partitioning for '{s}':")
    print(f"Recursive min cuts: {min_palindrome_cuts_recursive(s)}")
    print(f"Memoization min cuts: {min_palindrome_cuts_memo(s)}")
    print(f"Tabulation min cuts: {min_palindrome_cuts_tabulation(s)}")
    print(f"Optimized min cuts: {min_palindrome_cuts_optimized(s)}")
    print(f"All partitions: {palindrome_partitions(s)}")
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::cmp::min;

// Recursive
fn min_palindrome_cuts_recursive(s: &str, start: usize) -> i32 {
    if start >= s.len() {
        return 0;
    }
    
    let chars: Vec<char> = s.chars().collect();
    
    fn is_palindrome(chars: &[char], i: usize, j: usize) -> bool {
        let (mut left, mut right) = (i, j);
        while left < right {
            if chars[left] != chars[right] {
                return false;
            }
            left += 1;
            right -= 1;
        }
        true
    }
    
    let mut min_cuts = i32::MAX;
    for end in start..chars.len() {
        if is_palindrome(&chars, start, end) {
            let cuts = 1 + min_palindrome_cuts_recursive(s, end + 1);
            min_cuts = min(min_cuts, cuts);
        }
    }
    
    min_cuts
}

// Memoization with precomputed palindromes
fn min_palindrome_cuts_memo(s: &str) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n <= 1 {
        return 0;
    }
    
    // Precompute palindrome information
    let mut is_palindrome = vec![vec![false; n]; n];
    
    // Single characters are palindromes
    for i in 0..n {
        is_palindrome[i][i] = true;
    }
    
    // Check 2-character palindromes
    for i in 0..n - 1 {
        is_palindrome[i][i + 1] = chars[i] == chars[i + 1];
    }
    
    // Check longer palindromes
    for length in 3..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            is_palindrome[i][j] = chars[i] == chars[j] && is_palindrome[i + 1][j - 1];
        }
    }
    
    let mut memo = HashMap::new();
    
    fn helper(
        start: usize,
        n: usize,
        is_palindrome: &Vec<Vec<bool>>,
        memo: &mut HashMap<usize, i32>
    ) -> i32 {
        if start >= n {
            return 0;
        }
        
        if let Some(&value) = memo.get(&start) {
            return value;
        }
        
        let mut min_cuts = i32::MAX;
        for end in start..n {
            if is_palindrome[start][end] {
                let cuts = 1 + helper(end + 1, n, is_palindrome, memo);
                min_cuts = min(min_cuts, cuts);
            }
        }
        
        memo.insert(start, min_cuts);
        min_cuts
    }
    
    helper(0, n, &is_palindrome, &mut memo) - 1
}

// Tabulation
fn min_palindrome_cuts_tabulation(s: &str) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n <= 1 {
        return 0;
    }
    
    // Precompute palindrome information
    let mut is_palindrome = vec![vec![false; n]; n];
    
    for i in 0..n {
        is_palindrome[i][i] = true;
    }
    
    for i in 0..n - 1 {
        is_palindrome[i][i + 1] = chars[i] == chars[i + 1];
    }
    
    for length in 3..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            is_palindrome[i][j] = chars[i] == chars[j] && is_palindrome[i + 1][j - 1];
        }
    }
    
    let mut dp = vec![i32::MAX; n];
    
    for i in 0..n {
        if is_palindrome[0][i] {
            dp[i] = 0;
        } else {
            for j in 0..i {
                if is_palindrome[j + 1][i] {
                    dp[i] = min(dp[i], dp[j] + 1);
                }
            }
        }
    }
    
    dp[n - 1]
}

// Optimized approach
fn min_palindrome_cuts_optimized(s: &str) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n <= 1 {
        return 0;
    }
    
    let mut cuts: Vec<i32> = (0..n as i32).collect();
    
    for center in 0..n {
        // Odd length palindromes
        let (mut i, mut j) = (center as i32, center);
        while i >= 0 && j < n && chars[i as usize] == chars[j] {
            if i == 0 {
                cuts[j] = 0;
            } else {
                cuts[j] = min(cuts[j], cuts[i as usize - 1] + 1);
            }
            i -= 1;
            j += 1;
        }
        
        // Even length palindromes
        let (mut i, mut j) = (center as i32, center + 1);
        while i >= 0 && j < n && chars[i as usize] == chars[j] {
            if i == 0 {
                cuts[j] = 0;
            } else {
                cuts[j] = min(cuts[j], cuts[i as usize - 1] + 1);
            }
            i -= 1;
            j += 1;
        }
    }
    
    cuts[n - 1]
}

fn test_palindrome_partitioning() {
    let s = "aab";
    println!("Palindrome partitioning for '{}':", s);
    println!("Recursive min cuts: {}", min_palindrome_cuts_recursive(s, 0));
    println!("Memoization min cuts: {}", min_palindrome_cuts_memo(s));
    println!("Tabulation min cuts: {}", min_palindrome_cuts_tabulation(s));
    println!("Optimized min cuts: {}", min_palindrome_cuts_optimized(s));
}
```

## Memory Optimization Techniques

### 1. Rolling Arrays

When DP state only depends on previous few states:

```python
# Instead of: dp[i][j] = dp[i-1][j] + dp[i][j-1]
# Use: curr[j] = prev[j] + curr[j-1]

def optimized_2d_dp(matrix):
    m, n = len(matrix), len(matrix[0])
    prev = [0] * n
    
    for i in range(m):
        curr = [0] * n
        for j in range(n):
            # Compute curr[j] based on prev and curr
            pass
        prev = curr
    
    return prev[-1]
```

### 2. In-Place Modifications

When input array can be modified:

```python
def in_place_dp(nums):
    # Modify nums in-place to store DP values
    for i in range(1, len(nums)):
        nums[i] = max(nums[i], nums[i-1] + nums[i])
    return nums[-1]
```

### 3. State Compression

Using bit manipulation to represent states compactly:

```python
def bitmask_dp(n):
    dp = {}  # state -> value
    
    def solve(mask):
        if mask in dp:
            return dp[mask]
        
        # Base case
        if mask == 0:
            return 0
        
        result = float('inf')
        for i in range(n):
            if mask & (1 << i):  # if bit i is set
                result = min(result, 1 + solve(mask ^ (1 << i)))
        
        dp[mask] = result
        return result
    
    return solve((1 << n) - 1)  # All bits set
```

## Testing and Debugging Tips

### 1. Start Small

Always test with small inputs first:

```python
def test_dp_solution():
    # Test edge cases
    assert solution([]) == expected_empty
    assert solution([1]) == expected_single
    
    # Test small cases manually
    assert solution([1, 2]) == expected_two
    assert solution([1, 2, 3]) == expected_three
    
    # Test larger cases
    large_input = generate_large_test_case()
    result = solution(large_input)
    # Verify result makes sense
```

### 2. Verify Recurrence

Manually trace through small examples:

```python
def debug_dp(input_data):
    print("Tracing DP execution:")
    # Add print statements to show state transitions
    # Compare recursive vs memoized vs tabulated results
```

### 3. Check Boundary Conditions

Ensure proper handling of:

- Empty inputs
- Single element inputs
- Boundary indices
- Integer overflow (especially in Rust)

## Conclusion

Dynamic Programming transforms exponential recursive solutions into polynomial-time algorithms by eliminating redundant calculations. The key insights are:

1. **Recognition**: Identify optimal substructure and overlapping subproblems
2. **Modeling**: Define states and transitions clearly
3. **Implementation**: Choose between memoization and tabulation based on the problem
4. **Optimization**: Apply space optimization techniques when possible
5. **Testing**: Verify correctness with comprehensive test cases

Both Python and Rust offer excellent support for DP implementations, with Python providing more concise syntax and built-in memoization tools, while Rust offers better performance and memory safety guarantees.

The examples and patterns covered in this guide provide a solid foundation for tackling a wide variety of dynamic programming problems. Practice identifying these patterns and applying the appropriate techniques to become proficient in dynamic programming.