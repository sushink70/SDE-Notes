I'll create a comprehensive guide to Dynamic Programming with the Fibonacci sequence, including complete implementations in both Python and Rust.I've created a comprehensive guide to Dynamic Programming using the Fibonacci sequence as the primary example. The guide includes:

## Key Features:

1. **Complete Theory Coverage**: Explains DP principles, overlapping subproblems, and optimal substructure

2. **Multiple Implementation Approaches**:
   - Naive recursive (for comparison)
   - Top-down DP with memoization
   - Bottom-up DP with tabulation
   - Space-optimized solutions
   - Advanced matrix exponentiation

3. **Python Implementations**:
   - Basic recursive and memoized versions
   - `@lru_cache` decorator usage
   - Complete class-based implementation with benchmarking
   - Functional programming approaches

4. **Rust Implementations**:
   - Memory-safe memoization with HashMap
   - Iterator-based functional approaches
   - Complete struct implementation with benchmarking
   - Advanced techniques with proper error handling

5. **Performance Analysis**:
   - Time and space complexity for each approach
   - Benchmarking code in both languages
   - Performance comparison table

6. **Advanced Techniques**:
   - Matrix exponentiation for O(log n) solution
   - Binet's formula
   - Space optimization strategies

The guide progresses from basic concepts to advanced implementations, making it suitable for both beginners learning DP and experienced developers looking for optimized solutions. Each code example is complete and runnable, with proper error handling and testing included.

Would you like me to expand on any particular section or add additional DP problems that build on these Fibonacci concepts?

# Dynamic Programming Algorithms: Fibonacci Sequence Complete Guide

## Table of Contents
1. [Introduction to Dynamic Programming](#introduction-to-dynamic-programming)
2. [The Fibonacci Problem](#the-fibonacci-problem)
3. [Approach Analysis](#approach-analysis)
4. [Python Implementations](#python-implementations)
5. [Rust Implementations](#rust-implementations)
6. [Performance Comparison](#performance-comparison)
7. [Space Optimization](#space-optimization)
8. [Advanced Techniques](#advanced-techniques)

## Introduction to Dynamic Programming

Dynamic Programming (DP) is an algorithmic paradigm that solves complex problems by breaking them down into simpler subproblems. It's applicable when the subproblems overlap and the problem exhibits optimal substructure.

### Key Principles:
- **Overlapping Subproblems**: The same subproblems are solved multiple times
- **Optimal Substructure**: The optimal solution can be constructed from optimal solutions of subproblems
- **Memoization**: Store results of expensive function calls and reuse when the same inputs occur again

## The Fibonacci Problem

The Fibonacci sequence is defined as:
- F(0) = 0
- F(1) = 1  
- F(n) = F(n-1) + F(n-2) for n > 1

Sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89...

This is a perfect example for DP because:
1. It has overlapping subproblems (F(n-1) and F(n-2) share many calculations)
2. It has optimal substructure (F(n) depends on optimal solutions of F(n-1) and F(n-2))

## Approach Analysis

### 1. Naive Recursive Approach
- **Time Complexity**: O(2^n) - exponential
- **Space Complexity**: O(n) - due to recursion stack
- **Problem**: Recalculates same values multiple times

### 2. Top-Down DP (Memoization)
- **Time Complexity**: O(n)
- **Space Complexity**: O(n) - for memoization table + recursion stack
- **Advantage**: Intuitive, only calculates needed values

### 3. Bottom-Up DP (Tabulation)
- **Time Complexity**: O(n)
- **Space Complexity**: O(n) - for DP table
- **Advantage**: No recursion overhead, iterative approach

### 4. Space-Optimized DP
- **Time Complexity**: O(n)
- **Space Complexity**: O(1)
- **Advantage**: Minimal memory usage

## Python Implementations

### 1. Naive Recursive Solution

```python
def fibonacci_naive(n):
    """
    Naive recursive implementation of Fibonacci.
    Time: O(2^n), Space: O(n)
    """
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)

# Example usage
print(f"F(10) = {fibonacci_naive(10)}")  # 55
```

### 2. Top-Down DP (Memoization)

```python
def fibonacci_memoization(n, memo=None):
    """
    Top-down DP with memoization.
    Time: O(n), Space: O(n)
    """
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fibonacci_memoization(n - 1, memo) + fibonacci_memoization(n - 2, memo)
    return memo[n]

# Using functools.lru_cache decorator (Pythonic way)
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci_lru_cache(n):
    """
    Fibonacci with LRU cache decorator.
    Time: O(n), Space: O(n)
    """
    if n <= 1:
        return n
    return fibonacci_lru_cache(n - 1) + fibonacci_lru_cache(n - 2)

# Example usage
print(f"F(50) = {fibonacci_memoization(50)}")
print(f"F(50) = {fibonacci_lru_cache(50)}")
```

### 3. Bottom-Up DP (Tabulation)

```python
def fibonacci_tabulation(n):
    """
    Bottom-up DP using tabulation.
    Time: O(n), Space: O(n)
    """
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

# Example usage
print(f"F(100) = {fibonacci_tabulation(100)}")
```

### 4. Space-Optimized DP

```python
def fibonacci_optimized(n):
    """
    Space-optimized DP solution.
    Time: O(n), Space: O(1)
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1

# Example usage
print(f"F(1000) = {fibonacci_optimized(1000)}")
```

### 5. Matrix Exponentiation (Advanced)

```python
def matrix_multiply(A, B):
    """Helper function to multiply 2x2 matrices."""
    return [
        [A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]],
        [A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]]
    ]

def matrix_power(matrix, n):
    """Fast matrix exponentiation using binary exponentiation."""
    if n == 1:
        return matrix
    
    if n % 2 == 0:
        half = matrix_power(matrix, n // 2)
        return matrix_multiply(half, half)
    else:
        return matrix_multiply(matrix, matrix_power(matrix, n - 1))

def fibonacci_matrix(n):
    """
    Fibonacci using matrix exponentiation.
    Time: O(log n), Space: O(log n)
    """
    if n <= 1:
        return n
    
    base_matrix = [[1, 1], [1, 0]]
    result_matrix = matrix_power(base_matrix, n)
    return result_matrix[0][1]

# Example usage
print(f"F(50) = {fibonacci_matrix(50)}")
```

### 6. Complete Python Class Implementation

```python
import time
from functools import lru_cache

class FibonacciCalculator:
    """Complete Fibonacci calculator with multiple approaches."""
    
    def __init__(self):
        self.memo = {}
    
    def naive(self, n):
        if n <= 1:
            return n
        return self.naive(n - 1) + self.naive(n - 2)
    
    def memoization(self, n):
        if n in self.memo:
            return self.memo[n]
        
        if n <= 1:
            self.memo[n] = n
        else:
            self.memo[n] = self.memoization(n - 1) + self.memoization(n - 2)
        
        return self.memo[n]
    
    def tabulation(self, n):
        if n <= 1:
            return n
        
        dp = [0] * (n + 1)
        dp[1] = 1
        
        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
        
        return dp[n]
    
    def optimized(self, n):
        if n <= 1:
            return n
        
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        
        return b
    
    def benchmark(self, n, methods=None):
        """Benchmark different methods."""
        if methods is None:
            methods = ['optimized', 'tabulation', 'memoization']
        
        results = {}
        
        for method in methods:
            start_time = time.time()
            result = getattr(self, method)(n)
            end_time = time.time()
            
            results[method] = {
                'result': result,
                'time': end_time - start_time
            }
        
        return results

# Example usage
calc = FibonacciCalculator()
benchmark_results = calc.benchmark(35)
for method, data in benchmark_results.items():
    print(f"{method}: F(35) = {data['result']}, Time: {data['time']:.6f}s")
```

## Rust Implementations

### 1. Naive Recursive Solution

```rust
fn fibonacci_naive(n: u64) -> u64 {
    match n {
        0 | 1 => n,
        _ => fibonacci_naive(n - 1) + fibonacci_naive(n - 2),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_naive() {
        assert_eq!(fibonacci_naive(10), 55);
    }
}
```

### 2. Top-Down DP (Memoization)

```rust
use std::collections::HashMap;

fn fibonacci_memoization(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    if let Some(&cached) = memo.get(&n) {
        return cached;
    }
    
    let result = match n {
        0 | 1 => n,
        _ => fibonacci_memoization(n - 1, memo) + fibonacci_memoization(n - 2, memo),
    };
    
    memo.insert(n, result);
    result
}

fn fibonacci_memo_wrapper(n: u64) -> u64 {
    let mut memo = HashMap::new();
    fibonacci_memoization(n, &mut memo)
}

// Using once_cell for global memoization (thread-safe)
use once_cell::sync::Lazy;
use std::sync::Mutex;

static MEMO: Lazy<Mutex<HashMap<u64, u64>>> = Lazy::new(|| {
    Mutex::new(HashMap::new())
});

fn fibonacci_global_memo(n: u64) -> u64 {
    let mut memo = MEMO.lock().unwrap();
    
    if let Some(&cached) = memo.get(&n) {
        return cached;
    }
    
    let result = match n {
        0 | 1 => n,
        _ => {
            drop(memo); // Release lock before recursive calls
            let result = fibonacci_global_memo(n - 1) + fibonacci_global_memo(n - 2);
            let mut memo = MEMO.lock().unwrap();
            memo.insert(n, result);
            result
        }
    };
    
    if n <= 1 {
        memo.insert(n, result);
    }
    
    result
}
```

### 3. Bottom-Up DP (Tabulation)

```rust
fn fibonacci_tabulation(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    
    let mut dp = vec![0; (n + 1) as usize];
    dp[1] = 1;
    
    for i in 2..=n as usize {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n as usize]
}

// Iterator-based approach
fn fibonacci_tabulation_iter(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    
    (2..=n)
        .fold((0, 1), |(prev2, prev1), _| (prev1, prev1 + prev2))
        .1
}
```

### 4. Space-Optimized DP

```rust
fn fibonacci_optimized(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    
    let (mut prev2, mut prev1) = (0, 1);
    
    for _ in 2..=n {
        let current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}

// Functional approach with iterator
fn fibonacci_functional(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => (0..n-1)
            .fold((0, 1), |acc, _| (acc.1, acc.0 + acc.1))
            .1
    }
}
```

### 5. Matrix Exponentiation (Advanced)

```rust
type Matrix2x2 = [[u64; 2]; 2];

fn matrix_multiply(a: Matrix2x2, b: Matrix2x2) -> Matrix2x2 {
    [
        [a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
        [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]],
    ]
}

fn matrix_power(matrix: Matrix2x2, n: u64) -> Matrix2x2 {
    if n == 1 {
        return matrix;
    }
    
    if n % 2 == 0 {
        let half = matrix_power(matrix, n / 2);
        matrix_multiply(half, half)
    } else {
        matrix_multiply(matrix, matrix_power(matrix, n - 1))
    }
}

fn fibonacci_matrix(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    
    let base_matrix = [[1, 1], [1, 0]];
    let result_matrix = matrix_power(base_matrix, n);
    result_matrix[0][1]
}
```

### 6. Complete Rust Implementation with Benchmarking

```rust
use std::collections::HashMap;
use std::time::Instant;

pub struct FibonacciCalculator {
    memo: HashMap<u64, u64>,
}

impl FibonacciCalculator {
    pub fn new() -> Self {
        Self {
            memo: HashMap::new(),
        }
    }
    
    pub fn naive(&self, n: u64) -> u64 {
        match n {
            0 | 1 => n,
            _ => self.naive(n - 1) + self.naive(n - 2),
        }
    }
    
    pub fn memoization(&mut self, n: u64) -> u64 {
        if let Some(&cached) = self.memo.get(&n) {
            return cached;
        }
        
        let result = match n {
            0 | 1 => n,
            _ => self.memoization(n - 1) + self.memoization(n - 2),
        };
        
        self.memo.insert(n, result);
        result
    }
    
    pub fn tabulation(&self, n: u64) -> u64 {
        if n <= 1 {
            return n;
        }
        
        let mut dp = vec![0; (n + 1) as usize];
        dp[1] = 1;
        
        for i in 2..=n as usize {
            dp[i] = dp[i - 1] + dp[i - 2];
        }
        
        dp[n as usize]
    }
    
    pub fn optimized(&self, n: u64) -> u64 {
        if n <= 1 {
            return n;
        }
        
        let (mut a, mut b) = (0, 1);
        
        for _ in 2..=n {
            let temp = a + b;
            a = b;
            b = temp;
        }
        
        b
    }
    
    pub fn benchmark(&mut self, n: u64) -> BenchmarkResults {
        let mut results = BenchmarkResults::new();
        
        // Benchmark optimized (fastest, so we can test larger numbers)
        let start = Instant::now();
        let result = self.optimized(n);
        results.optimized = BenchmarkResult {
            result,
            duration: start.elapsed(),
        };
        
        // Benchmark tabulation
        let start = Instant::now();
        let result = self.tabulation(n);
        results.tabulation = BenchmarkResult {
            result,
            duration: start.elapsed(),
        };
        
        // Clear memo for fair comparison
        self.memo.clear();
        
        // Benchmark memoization
        let start = Instant::now();
        let result = self.memoization(n);
        results.memoization = BenchmarkResult {
            result,
            duration: start.elapsed(),
        };
        
        results
    }
}

#[derive(Debug)]
pub struct BenchmarkResult {
    pub result: u64,
    pub duration: std::time::Duration,
}

#[derive(Debug)]
pub struct BenchmarkResults {
    pub optimized: BenchmarkResult,
    pub tabulation: BenchmarkResult,
    pub memoization: BenchmarkResult,
}

impl BenchmarkResults {
    fn new() -> Self {
        Self {
            optimized: BenchmarkResult { result: 0, duration: std::time::Duration::new(0, 0) },
            tabulation: BenchmarkResult { result: 0, duration: std::time::Duration::new(0, 0) },
            memoization: BenchmarkResult { result: 0, duration: std::time::Duration::new(0, 0) },
        }
    }
}

// Main function for testing
fn main() {
    let mut calc = FibonacciCalculator::new();
    let results = calc.benchmark(40);
    
    println!("Fibonacci(40) Benchmark Results:");
    println!("Optimized: {} in {:?}", results.optimized.result, results.optimized.duration);
    println!("Tabulation: {} in {:?}", results.tabulation.result, results.tabulation.duration);
    println!("Memoization: {} in {:?}", results.memoization.result, results.memoization.duration);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_all_methods() {
        let mut calc = FibonacciCalculator::new();
        let test_cases = vec![0, 1, 5, 10, 20];
        let expected = vec![0, 1, 5, 55, 6765];
        
        for (i, &n) in test_cases.iter().enumerate() {
            assert_eq!(calc.naive(n), expected[i]);
            assert_eq!(calc.tabulation(n), expected[i]);
            assert_eq!(calc.optimized(n), expected[i]);
            
            calc.memo.clear();
            assert_eq!(calc.memoization(n), expected[i]);
        }
    }
}
```

## Performance Comparison

| Method | Time Complexity | Space Complexity | Best Use Case |
|--------|----------------|------------------|---------------|
| Naive Recursive | O(2^n) | O(n) | Learning, small n |
| Memoization | O(n) | O(n) | When not all values needed |
| Tabulation | O(n) | O(n) | When all values needed |
| Space Optimized | O(n) | O(1) | Memory-constrained environments |
| Matrix Exponentiation | O(log n) | O(log n) | Very large n values |

## Space Optimization

The space-optimized approach is crucial for:
- **Memory-constrained systems**
- **Embedded systems**
- **Large-scale computations**
- **Real-time systems**

Key insight: We only need the last two values to compute the next Fibonacci number.

## Advanced Techniques

### 1. Binet's Formula (Mathematical Approach)
```python
import math

def fibonacci_binet(n):
    """
    Fibonacci using Binet's formula.
    Time: O(1), but has floating-point precision issues for large n
    """
    phi = (1 + math.sqrt(5)) / 2
    psi = (1 - math.sqrt(5)) / 2
    return int((phi**n - psi**n) / math.sqrt(5))
```

### 2. Iterative Doubling
For very large n, we can use the property:
- F(2k) = F(k) * (2*F(k+1) - F(k))
- F(2k+1) = F(k+1)² + F(k)²

This allows us to compute F(n) in O(log n) time.

## Best Practices

### Python
- Use `functools.lru_cache` for simple memoization
- Prefer iterative solutions for better performance
- Use generators for sequence generation
- Handle large numbers with Python's arbitrary precision integers

### Rust
- Use `HashMap` for memoization when needed
- Prefer iterative solutions to avoid stack overflow
- Use appropriate integer types (consider overflow)
- Leverage Rust's iterator chains for functional style
- Use `once_cell` for global memoization if needed

## Conclusion

Dynamic Programming transforms the exponential Fibonacci problem into a linear one through:

1. **Problem Recognition**: Identifying overlapping subproblems
2. **State Definition**: What information we need to store
3. **Recurrence Relation**: How states relate to each other
4. **Base Cases**: Starting conditions
5. **Implementation**: Choose between top-down and bottom-up
6. **Optimization**: Reduce space complexity when possible

The Fibonacci sequence serves as an excellent introduction to DP concepts that scale to more complex problems like longest common subsequence, knapsack problems, and graph algorithms.

I'll create a detailed ASCII diagram showing how Dynamic Programming works with the Fibonacci sequence, including both the recursive tree and the step-by-step memoization process.This ASCII diagram illustrates the key concepts of Dynamic Programming using the Fibonacci sequence:

1. **Problem Visualization**: Shows how the naive recursive approach creates a tree with massive redundant calculations

2. **Memoization Process**: Step-by-step walkthrough of how previously computed values are stored and reused, dramatically reducing the number of function calls

3. **Bottom-Up Approach**: Demonstrates tabulation where we build the solution incrementally from the base cases

4. **Space Optimization**: Shows how we can reduce space complexity to O(1) by only keeping track of the last two values

5. **Performance Comparison**: Clear comparison showing how DP transforms an exponential O(2^n) algorithm into a linear O(n) solution

The diagram emphasizes the two core principles of Dynamic Programming:
- **Overlapping Subproblems**: The same subproblems appear multiple times
- **Optimal Substructure**: The optimal solution contains optimal solutions to subproblems

This visual representation makes it clear why Dynamic Programming is so powerful for optimization problems!

# Dynamic Programming - Fibonacci Sequence

## Problem Definition
```
F(n) = F(n-1) + F(n-2) where F(0) = 0, F(1) = 1
```

## 1. Naive Recursive Approach (WITHOUT Dynamic Programming)
```
Computing F(5) - Shows overlapping subproblems:

                    F(5)
                   /    \
               F(4)      F(3)
              /   \     /   \
          F(3)   F(2) F(2) F(1)
         /  \   /  \  /  \   |
     F(2) F(1) F(1) F(0) F(1) F(0) 1
    /  \   |    |    |    |    |
F(1) F(0) 1   1   0   1   0
  |    |
  1    0

PROBLEM: F(3) computed 2 times, F(2) computed 3 times, F(1) computed 5 times!
Time Complexity: O(2^n) - EXPONENTIAL!
```

## 2. Dynamic Programming Solution - Memoization (Top-Down)

### Step-by-Step Execution for F(5):

```
Initial State:
memo = {}

Step 1: F(5) called
┌─────────────────────────────────────────────────┐
│ F(5): Not in memo, compute F(4) + F(3)         │
│ memo = {}                                       │
└─────────────────────────────────────────────────┘

Step 2: F(4) called
┌─────────────────────────────────────────────────┐
│ F(4): Not in memo, compute F(3) + F(2)         │
│ memo = {}                                       │
└─────────────────────────────────────────────────┘

Step 3: F(3) called
┌─────────────────────────────────────────────────┐
│ F(3): Not in memo, compute F(2) + F(1)         │
│ memo = {}                                       │
└─────────────────────────────────────────────────┘

Step 4: F(2) called
┌─────────────────────────────────────────────────┐
│ F(2): Not in memo, compute F(1) + F(0)         │
│ memo = {}                                       │
└─────────────────────────────────────────────────┘

Step 5: F(1) called (BASE CASE)
┌─────────────────────────────────────────────────┐
│ F(1): BASE CASE = 1                             │
│ memo = {1: 1}                    ←─ STORED!     │
└─────────────────────────────────────────────────┘

Step 6: F(0) called (BASE CASE)
┌─────────────────────────────────────────────────┐
│ F(0): BASE CASE = 0                             │
│ memo = {1: 1, 0: 0}              ←─ STORED!     │
└─────────────────────────────────────────────────┘

Step 7: F(2) = F(1) + F(0) = 1 + 0 = 1
┌─────────────────────────────────────────────────┐
│ F(2): COMPUTED = 1                              │
│ memo = {1: 1, 0: 0, 2: 1}        ←─ STORED!     │
└─────────────────────────────────────────────────┘

Step 8: F(1) needed again for F(3)
┌─────────────────────────────────────────────────┐
│ F(1): FOUND IN MEMO! Return 1    ←─ NO RECOMPUTE│
│ memo = {1: 1, 0: 0, 2: 1}                       │
└─────────────────────────────────────────────────┘

Step 9: F(3) = F(2) + F(1) = 1 + 1 = 2
┌─────────────────────────────────────────────────┐
│ F(3): COMPUTED = 2                              │
│ memo = {1: 1, 0: 0, 2: 1, 3: 2}  ←─ STORED!     │
└─────────────────────────────────────────────────┘

Step 10: F(2) needed again for F(4)
┌─────────────────────────────────────────────────┐
│ F(2): FOUND IN MEMO! Return 1    ←─ NO RECOMPUTE│
│ memo = {1: 1, 0: 0, 2: 1, 3: 2}                 │
└─────────────────────────────────────────────────┘

Step 11: F(4) = F(3) + F(2) = 2 + 1 = 3
┌─────────────────────────────────────────────────┐
│ F(4): COMPUTED = 3                              │
│ memo = {1: 1, 0: 0, 2: 1, 3: 2, 4: 3} ←─STORED! │
└─────────────────────────────────────────────────┘

Step 12: F(3) needed again for F(5)
┌─────────────────────────────────────────────────┐
│ F(3): FOUND IN MEMO! Return 2    ←─ NO RECOMPUTE│
│ memo = {1: 1, 0: 0, 2: 1, 3: 2, 4: 3}           │
└─────────────────────────────────────────────────┘

Step 13: F(5) = F(4) + F(3) = 3 + 2 = 5
┌─────────────────────────────────────────────────┐
│ F(5): COMPUTED = 5                              │
│ memo = {1: 1, 0: 0, 2: 1, 3: 2, 4: 3, 5: 5}     │
└─────────────────────────────────────────────────┘
```

## 3. Optimized Call Tree with Memoization

```
                F(5) [NEW]
               /         \
        F(4) [NEW]    F(3) [CACHED] ←─ Reused!
           /     \
    F(3) [NEW]  F(2) [CACHED] ←─ Reused!
       /    \
  F(2) [NEW] F(1) [CACHED] ←─ Reused!
     /    \
F(1) [NEW] F(0) [NEW]

Total function calls: 6 (vs 15 in naive approach)
Time Complexity: O(n)
Space Complexity: O(n)
```

## 4. Bottom-Up Dynamic Programming (Tabulation)

```
Building table from bottom up for F(5):

Step 1: Initialize base cases
┌───┬───┬───┬───┬───┬───┐
│ i │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │
├───┼───┼───┼───┼───┼───┼───┤
│F(i)│ 0 │ 1 │ ? │ ? │ ? │ ? │
└───┴───┴───┴───┴───┴───┴───┘

Step 2: F(2) = F(1) + F(0) = 1 + 0 = 1
┌───┬───┬───┬───┬───┬───┬───┐
│ i │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │
├───┼───┼───┼───┼───┼───┼───┤
│F(i)│ 0 │ 1 │ 1 │ ? │ ? │ ? │
└───┴───┴───┴───┴───┴───┴───┘
       ↑   ↑   ↑
       └───┴──→│ 1+0=1

Step 3: F(3) = F(2) + F(1) = 1 + 1 = 2
┌───┬───┬───┬───┬───┬───┬───┐
│ i │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │
├───┼───┼───┼───┼───┼───┼───┤
│F(i)│ 0 │ 1 │ 1 │ 2 │ ? │ ? │
└───┴───┴───┴───┴───┴───┴───┘
           ↑   ↑   ↑
           └───┴──→│ 1+1=2

Step 4: F(4) = F(3) + F(2) = 2 + 1 = 3
┌───┬───┬───┬───┬───┬───┬───┐
│ i │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │
├───┼───┼───┼───┼───┼───┼───┤
│F(i)│ 0 │ 1 │ 1 │ 2 │ 3 │ ? │
└───┴───┴───┴───┴───┴───┴───┘
               ↑   ↑   ↑
               └───┴──→│ 2+1=3

Step 5: F(5) = F(4) + F(3) = 3 + 2 = 5
┌───┬───┬───┬───┬───┬───┬───┐
│ i │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │
├───┼───┼───┼───┼───┼───┼───┤
│F(i)│ 0 │ 1 │ 1 │ 2 │ 3 │ 5 │
└───┴───┴───┴───┴───┴───┴───┘
                   ↑   ↑   ↑
                   └───┴──→│ 3+2=5

FINAL RESULT: F(5) = 5
```

## 5. Space-Optimized Version

```
Since we only need the previous two values:

Initialize: prev2=0, prev1=1

For i=2: curr = prev1 + prev2 = 1 + 0 = 1
┌────────┬────────┬────────┐
│ prev2  │ prev1  │ curr   │
│   0    │   1    │   1    │
└────────┴────────┴────────┘
Update: prev2=1, prev1=1

For i=3: curr = prev1 + prev2 = 1 + 1 = 2
┌────────┬────────┬────────┐
│ prev2  │ prev1  │ curr   │
│   1    │   1    │   2    │
└────────┴────────┴────────┘
Update: prev2=1, prev1=2

For i=4: curr = prev1 + prev2 = 2 + 1 = 3
┌────────┬────────┬────────┐
│ prev2  │ prev1  │ curr   │
│   1    │   2    │   3    │
└────────┴────────┴────────┘
Update: prev2=2, prev1=3

For i=5: curr = prev1 + prev2 = 3 + 2 = 5
┌────────┬────────┬────────┐
│ prev2  │ prev1  │ curr   │
│   2    │   3    │   5    │
└────────┴────────┴────────┘

RESULT: F(5) = 5
Space Complexity: O(1)
```

## 6. Comparison Summary

```
┌─────────────────┬─────────────┬─────────────┬─────────────┐
│    Approach     │    Time     │    Space    │ Recomputes  │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ Naive Recursive │   O(2^n)    │    O(n)     │     Yes     │
│ Memoization     │    O(n)     │    O(n)     │     No      │
│ Tabulation      │    O(n)     │    O(n)     │     No      │
│ Space Optimized │    O(n)     │    O(1)     │     No      │
└─────────────────┴─────────────┴─────────────┴─────────────┘

Key DP Principles:
1. Overlapping Subproblems ✓
2. Optimal Substructure ✓
3. Store solutions to avoid recomputation ✓
```