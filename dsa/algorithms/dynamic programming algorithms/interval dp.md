# Comprehensive Guide to Interval DP

## Introduction

**Interval Dynamic Programming** (Interval DP) is a technique used to solve problems where you need to make optimal decisions on contiguous subarrays or subsequences. The key idea is to solve smaller intervals first, then combine them to solve larger intervals.

### When to Use Interval DP

- Merging/splitting intervals optimally
- Problems involving palindromes on substrings
- Matrix chain multiplication variants
- Game theory problems on sequences
- Expression evaluation problems

### Core Pattern

The typical approach processes intervals by **length**, starting from length 1 and building up to the full array:

```
for length in range(1, n+1):
    for i in range(n - length + 1):
        j = i + length - 1
        # dp[i][j] = optimal solution for interval [i, j]
        # Try all possible split points k where i <= k < j
        for k in range(i, j):
            dp[i][j] = optimize(dp[i][k], dp[k+1][j])
```

---

## Problem 1: Matrix Chain Multiplication

**Problem**: Given dimensions of matrices, find the minimum number of scalar multiplications needed to multiply them all.

### Theory

- Matrices: A₁(p₀×p₁), A₂(p₁×p₂), ..., Aₙ(pₙ₋₁×pₙ)
- Cost to multiply (p×q) and (q×r) matrices = p×q×r
- `dp[i][j]` = minimum cost to multiply matrices from i to j
- Recurrence: `dp[i][j] = min(dp[i][k] + dp[k+1][j] + dims[i-1]*dims[k]*dims[j])` for all k in [i, j)

### Python Implementation

```python
def matrix_chain_multiplication(dims):
    """
    Args:
        dims: List of dimensions where matrix i has dims[i-1] x dims[i]
    Returns:
        Minimum number of multiplications needed
    """
    n = len(dims) - 1  # number of matrices
    if n <= 1:
        return 0
    
    # dp[i][j] = min cost to multiply matrices i to j (1-indexed)
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    
    # length of chain
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all split points
            for k in range(i, j):
                cost = (dp[i][k] + 
                       dp[k + 1][j] + 
                       dims[i - 1] * dims[k] * dims[j])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[1][n]

# Example usage
dims = [10, 20, 30, 40, 30]
print(f"Minimum multiplications: {matrix_chain_multiplication(dims)}")
# Output: 30000
```

### Rust Implementation

```rust
fn matrix_chain_multiplication(dims: &[i32]) -> i32 {
    let n = dims.len() - 1;
    if n <= 1 {
        return 0;
    }
    
    let mut dp = vec![vec![0; n + 1]; n + 1];
    
    // Iterate by chain length
    for length in 2..=n {
        for i in 1..=(n - length + 1) {
            let j = i + length - 1;
            dp[i][j] = i32::MAX;
            
            // Try all split points
            for k in i..j {
                let cost = dp[i][k] + 
                          dp[k + 1][j] + 
                          dims[i - 1] * dims[k] * dims[j];
                dp[i][j] = dp[i][j].min(cost);
            }
        }
    }
    
    dp[1][n]
}

fn main() {
    let dims = vec![10, 20, 30, 40, 30];
    println!("Minimum multiplications: {}", 
             matrix_chain_multiplication(&dims));
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "math"
)

func matrixChainMultiplication(dims []int) int {
    n := len(dims) - 1
    if n <= 1 {
        return 0
    }
    
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    // Iterate by chain length
    for length := 2; length <= n; length++ {
        for i := 1; i <= n-length+1; i++ {
            j := i + length - 1
            dp[i][j] = math.MaxInt32
            
            // Try all split points
            for k := i; k < j; k++ {
                cost := dp[i][k] + 
                       dp[k+1][j] + 
                       dims[i-1]*dims[k]*dims[j]
                if cost < dp[i][j] {
                    dp[i][j] = cost
                }
            }
        }
    }
    
    return dp[1][n]
}

func main() {
    dims := []int{10, 20, 30, 40, 30}
    fmt.Printf("Minimum multiplications: %d\n", 
               matrixChainMultiplication(dims))
}
```

---

## Problem 2: Burst Balloons

**Problem**: Given n balloons with coins, bursting balloon i gives `nums[i-1] * nums[i] * nums[i+1]` coins. Find maximum coins obtainable.

### Theory

- Add dummy balloons with value 1 at both ends
- `dp[i][j]` = max coins from bursting all balloons in open interval (i, j)
- For each k in (i, j), assume k is the **last** balloon to burst
- Recurrence: `dp[i][j] = max(dp[i][k] + dp[k][j] + nums[i]*nums[k]*nums[j])`

### Python Implementation

```python
def max_coins(nums):
    """
    Args:
        nums: List of balloon values
    Returns:
        Maximum coins obtainable
    """
    # Add boundary balloons
    balloons = [1] + nums + [1]
    n = len(balloons)
    
    # dp[i][j] = max coins bursting balloons in open interval (i, j)
    dp = [[0] * n for _ in range(n)]
    
    # length of interval (excluding boundaries)
    for length in range(1, n - 1):
        for i in range(n - length - 1):
            j = i + length + 1
            
            # Try bursting each balloon k last in interval (i, j)
            for k in range(i + 1, j):
                coins = (balloons[i] * balloons[k] * balloons[j] + 
                        dp[i][k] + dp[k][j])
                dp[i][j] = max(dp[i][j], coins)
    
    return dp[0][n - 1]

# Example usage
nums = [3, 1, 5, 8]
print(f"Maximum coins: {max_coins(nums)}")
# Output: 167
```

### Rust Implementation

```rust
fn max_coins(nums: Vec<i32>) -> i32 {
    let mut balloons = vec![1];
    balloons.extend(&nums);
    balloons.push(1);
    let n = balloons.len();
    
    let mut dp = vec![vec![0; n]; n];
    
    // Length of interval
    for length in 1..n-1 {
        for i in 0..n-length-1 {
            let j = i + length + 1;
            
            // Try each balloon k as last to burst
            for k in i+1..j {
                let coins = balloons[i] * balloons[k] * balloons[j] +
                           dp[i][k] + dp[k][j];
                dp[i][j] = dp[i][j].max(coins);
            }
        }
    }
    
    dp[0][n - 1]
}

fn main() {
    let nums = vec![3, 1, 5, 8];
    println!("Maximum coins: {}", max_coins(nums));
}
```

### Go Implementation

```go
package main

import "fmt"

func maxCoins(nums []int) int {
    balloons := make([]int, len(nums)+2)
    balloons[0] = 1
    balloons[len(balloons)-1] = 1
    copy(balloons[1:], nums)
    
    n := len(balloons)
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
    }
    
    // Length of interval
    for length := 1; length < n-1; length++ {
        for i := 0; i < n-length-1; i++ {
            j := i + length + 1
            
            // Try each balloon k as last to burst
            for k := i + 1; k < j; k++ {
                coins := balloons[i]*balloons[k]*balloons[j] +
                        dp[i][k] + dp[k][j]
                if coins > dp[i][j] {
                    dp[i][j] = coins
                }
            }
        }
    }
    
    return dp[0][n-1]
}

func main() {
    nums := []int{3, 1, 5, 8}
    fmt.Printf("Maximum coins: %d\n", maxCoins(nums))
}
```

---

## Problem 3: Longest Palindromic Subsequence

**Problem**: Find the length of the longest palindromic subsequence in a string.

### Theory

- `dp[i][j]` = length of longest palindromic subsequence in s[i:j+1]
- Base case: `dp[i][i] = 1`
- If `s[i] == s[j]`: `dp[i][j] = dp[i+1][j-1] + 2`
- Otherwise: `dp[i][j] = max(dp[i+1][j], dp[i][j-1])`

### Python Implementation

```python
def longest_palindromic_subsequence(s):
    """
    Args:
        s: Input string
    Returns:
        Length of longest palindromic subsequence
    """
    n = len(s)
    if n == 0:
        return 0
    
    # dp[i][j] = LPS length in s[i:j+1]
    dp = [[0] * n for _ in range(n)]
    
    # Base case: single characters
    for i in range(n):
        dp[i][i] = 1
    
    # Build by increasing length
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2 if i + 1 <= j - 1 else 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    
    return dp[0][n - 1]

# Example usage
s = "bbbab"
print(f"Longest palindromic subsequence length: {longest_palindromic_subsequence(s)}")
# Output: 4 (bbbb)
```

### Rust Implementation

```rust
fn longest_palindromic_subsequence(s: &str) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n == 0 {
        return 0;
    }
    
    let mut dp = vec![vec![0; n]; n];
    
    // Base case: single characters
    for i in 0..n {
        dp[i][i] = 1;
    }
    
    // Build by increasing length
    for length in 2..=n {
        for i in 0..=n-length {
            let j = i + length - 1;
            
            if chars[i] == chars[j] {
                dp[i][j] = if i + 1 <= j - 1 {
                    dp[i + 1][j - 1] + 2
                } else {
                    2
                };
            } else {
                dp[i][j] = dp[i + 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[0][n - 1]
}

fn main() {
    let s = "bbbab";
    println!("Longest palindromic subsequence length: {}", 
             longest_palindromic_subsequence(s));
}
```

### Go Implementation

```go
package main

import "fmt"

func longestPalindromicSubsequence(s string) int {
    n := len(s)
    if n == 0 {
        return 0
    }
    
    dp := make([][]int, n)
    for i := range dp {
        dp[i] = make([]int, n)
        dp[i][i] = 1
    }
    
    // Build by increasing length
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            
            if s[i] == s[j] {
                if i+1 <= j-1 {
                    dp[i][j] = dp[i+1][j-1] + 2
                } else {
                    dp[i][j] = 2
                }
            } else {
                dp[i][j] = max(dp[i+1][j], dp[i][j-1])
            }
        }
    }
    
    return dp[0][n-1]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

func main() {
    s := "bbbab"
    fmt.Printf("Longest palindromic subsequence length: %d\n", 
               longestPalindromicSubsequence(s))
}
```

---

## Problem 4: Minimum Cost to Merge Stones

**Problem**: Merge piles of stones with minimum cost. Can only merge exactly K consecutive piles at a time.

### Theory

- `dp[i][j][m]` = min cost to merge stones[i:j+1] into m piles
- Base case: `dp[i][i][1] = 0` (one pile, no cost)
- Recurrence: 
  - To get m piles: merge first part into 1 pile, rest into m-1 piles
  - To get 1 pile from K piles: `dp[i][j][1] = dp[i][j][K] + sum(stones[i:j+1])`

### Python Implementation

```python
def merge_stones(stones, K):
    """
    Args:
        stones: List of stone pile sizes
        K: Number of consecutive piles that can be merged
    Returns:
        Minimum cost to merge all stones, or -1 if impossible
    """
    n = len(stones)
    
    # Check if it's possible to merge
    if (n - 1) % (K - 1) != 0:
        return -1
    
    # Prefix sums for quick range sum calculation
    prefix = [0]
    for stone in stones:
        prefix.append(prefix[-1] + stone)
    
    # dp[i][j][m] = min cost to merge stones[i:j+1] into m piles
    dp = [[[float('inf')] * (K + 1) for _ in range(n)] for _ in range(n)]
    
    # Base case: single pile
    for i in range(n):
        dp[i][i][1] = 0
    
    # Build by increasing length
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            # Try to create m piles
            for m in range(2, K + 1):
                for mid in range(i, j, K - 1):
                    cost = dp[i][mid][1] + dp[mid + 1][j][m - 1]
                    dp[i][j][m] = min(dp[i][j][m], cost)
            
            # Merge K piles into 1
            dp[i][j][1] = dp[i][j][K] + prefix[j + 1] - prefix[i]
    
    return dp[0][n - 1][1]

# Example usage
stones = [3, 2, 4, 1]
K = 2
print(f"Minimum cost: {merge_stones(stones, K)}")
# Output: 20
```

### Rust Implementation

```rust
fn merge_stones(stones: &[i32], k: usize) -> i32 {
    let n = stones.len();
    
    if (n - 1) % (k - 1) != 0 {
        return -1;
    }
    
    // Prefix sums
    let mut prefix = vec![0];
    for &stone in stones {
        prefix.push(prefix.last().unwrap() + stone);
    }
    
    let inf = i32::MAX / 2;
    let mut dp = vec![vec![vec![inf; k + 1]; n]; n];
    
    // Base case
    for i in 0..n {
        dp[i][i][1] = 0;
    }
    
    // Build by length
    for length in 2..=n {
        for i in 0..=n-length {
            let j = i + length - 1;
            
            // Create m piles
            for m in 2..=k {
                let mut mid = i;
                while mid < j {
                    let cost = dp[i][mid][1] + dp[mid + 1][j][m - 1];
                    dp[i][j][m] = dp[i][j][m].min(cost);
                    mid += k - 1;
                }
            }
            
            // Merge K piles into 1
            dp[i][j][1] = dp[i][j][k] + prefix[j + 1] - prefix[i];
        }
    }
    
    dp[0][n - 1][1]
}

fn main() {
    let stones = vec![3, 2, 4, 1];
    let k = 2;
    println!("Minimum cost: {}", merge_stones(&stones, k));
}
```

### Go Implementation

```go
package main

import (
    "fmt"
    "math"
)

func mergeStones(stones []int, k int) int {
    n := len(stones)
    
    if (n-1)%(k-1) != 0 {
        return -1
    }
    
    // Prefix sums
    prefix := make([]int, n+1)
    for i, stone := range stones {
        prefix[i+1] = prefix[i] + stone
    }
    
    // Initialize DP
    inf := math.MaxInt32 / 2
    dp := make([][][]int, n)
    for i := range dp {
        dp[i] = make([][]int, n)
        for j := range dp[i] {
            dp[i][j] = make([]int, k+1)
            for m := range dp[i][j] {
                dp[i][j][m] = inf
            }
        }
        dp[i][i][1] = 0
    }
    
    // Build by length
    for length := 2; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            
            // Create m piles
            for m := 2; m <= k; m++ {
                for mid := i; mid < j; mid += k - 1 {
                    cost := dp[i][mid][1] + dp[mid+1][j][m-1]
                    if cost < dp[i][j][m] {
                        dp[i][j][m] = cost
                    }
                }
            }
            
            // Merge k piles into 1
            dp[i][j][1] = dp[i][j][k] + prefix[j+1] - prefix[i]
        }
    }
    
    return dp[0][n-1][1]
}

func main() {
    stones := []int{3, 2, 4, 1}
    k := 2
    fmt.Printf("Minimum cost: %d\n", mergeStones(stones, k))
}
```

---

## Time and Space Complexity Analysis

| Problem | Time Complexity | Space Complexity | Notes |
|---------|----------------|------------------|-------|
| Matrix Chain | O(n³) | O(n²) | Two loops for intervals, one for split points |
| Burst Balloons | O(n³) | O(n²) | Similar structure to matrix chain |
| Palindromic Subseq | O(n²) | O(n²) | No third loop needed |
| Merge Stones | O(n³ × K) | O(n² × K) | Extra dimension for pile count |

---

## Optimization Techniques

### 1. Space Optimization

For some interval DP problems, you can reduce space by processing diagonally:

```python
# Instead of full 2D array
dp = [[0] * n for _ in range(n)]

# Use only what's needed
for length in range(1, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        # Only access dp[i][j], dp[i][k], dp[k+1][j]
```

### 2. Memoization (Top-Down)

Sometimes recursion with memoization is clearer:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def solve(i, j):
    if i > j:
        return 0
    if i == j:
        return base_case
    
    result = float('inf')
    for k in range(i, j):
        result = min(result, solve(i, k) + solve(k + 1, j) + cost(i, k, j))
    return result
```

### 3. Early Termination

Check validity before computing:

```python
if j - i + 1 < min_length:
    continue  # Skip impossible intervals
```

---

## Common Pitfalls

1. **Off-by-one errors**: Be careful with 0-indexed vs 1-indexed arrays
2. **Iteration order**: Always process smaller intervals before larger ones
3. **Base cases**: Initialize single elements and empty intervals correctly
4. **Boundaries**: Handle edge cases when i == j or i + 1 == j
5. **Integer overflow**: Use appropriate data types in Rust/Go

---

## Practice Problems

1. **LeetCode 312**: Burst Balloons
2. **LeetCode 516**: Longest Palindromic Subsequence
3. **LeetCode 1039**: Minimum Score Triangulation of Polygon
4. **LeetCode 1547**: Minimum Cost to Cut a Stick
5. **LeetCode 1000**: Minimum Cost to Merge Stones
6. **LeetCode 375**: Guess Number Higher or Lower II
7. **LeetCode 664**: Strange Printer

---

## Summary

Interval DP is powerful for problems involving:
- **Optimal merging/splitting** of contiguous segments
- **Palindrome-related** problems on substrings
- **Game theory** where players choose from intervals
- **Cost minimization** on sequences

**Key steps**:
1. Define `dp[i][j]` representing optimal solution for interval [i, j]
2. Identify base cases (usually single elements)
3. Iterate by increasing interval length
4. For each interval, try all possible split points
5. Combine solutions from smaller subproblems

The pattern is consistent across languages - the main differences are syntax and initialization conventions.