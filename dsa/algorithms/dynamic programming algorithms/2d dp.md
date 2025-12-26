# Complete 2D Dynamic Programming Mastery Guide

## Table of Contents
1. [Core Intuition & Mental Models](#core-intuition)
2. [Recognition Patterns](#recognition)
3. [State Space Design](#state-space)
4. [Classic Patterns & Templates](#patterns)
5. [Complete Problem Walkthroughs](#walkthroughs)
6. [Optimization Techniques](#optimization)
7. [Practice Progression](#progression)

---

## <a name="core-intuition"></a>1. Core Intuition & Mental Models

### **The Essence of 2D DP**

2D DP extends 1D DP by tracking **two independent dimensions of state**. Think of it as navigating a grid where each cell represents a subproblem defined by two parameters.

**Mental Model: The Grid Navigator**
- **State**: `dp[i][j]` = "optimal answer for subproblem defined by indices i and j"
- **Transition**: How do I reach `dp[i][j]` from previously solved states?
- **Base Cases**: What are the simplest subproblems I can solve directly?

**Key Insight**: In 1D DP, you're building a sequence. In 2D DP, you're building a **matrix of solutions** where each cell depends on its neighbors according to specific rules.

### **When Problems Require 2D State**

You need 2D DP when the optimal substructure requires tracking:
1. **Two sequences/arrays** (e.g., longest common subsequence)
2. **Position + remaining capacity** (e.g., 0/1 knapsack)
3. **Matrix traversal** with constraints (e.g., min path sum)
4. **Interval endpoints** [i, j] (e.g., palindrome partitioning)
5. **State + previous choice** (e.g., buy/sell stock with cooldown)

### **The Three Pillars of DP Mastery**

1. **State Definition**: What information do I need to uniquely identify a subproblem?
2. **Recurrence Relation**: How do smaller subproblems combine to solve larger ones?
3. **Evaluation Order**: In what sequence should I fill the DP table?

---

## <a name="recognition"></a>2. Recognition Patterns

### **How to Identify 2D DP Problems**

**Pattern 1: Two Input Sequences**
- Keywords: "common subsequence", "edit distance", "matching"
- State: `dp[i][j]` = solution considering first i elements of sequence A and first j of sequence B

**Pattern 2: Bounded Resource**
- Keywords: "capacity", "weight limit", "budget", "k items"
- State: `dp[i][w]` = best solution using first i items with weight limit w

**Pattern 3: Matrix/Grid Navigation**
- Keywords: "path", "reach", "sum", "grid"
- State: `dp[i][j]` = solution reaching cell (i, j)

**Pattern 4: Interval/Range Problems**
- Keywords: "subarray", "interval", "split", "palindrome"
- State: `dp[i][j]` = solution for range [i, j]

**Pattern 5: Stateful Transitions**
- Keywords: "cooldown", "transaction limit", "state machine"
- State: `dp[i][state]` = solution at position i in given state

---

## <a name="state-space"></a>3. State Space Design

### **Dimensional Analysis Framework**

**Step 1: Identify Variables**
What changes as you make decisions? Each independent variable → one dimension.

**Step 2: Define Semantics**
Be precise: "dp[i][j] = maximum profit using first i items with capacity j"

**Step 3: Verify Independence**
Can you determine dp[i][j] knowing only i, j, and previously computed states?

### **Common Pitfalls**

❌ **Ambiguous state**: "dp[i][j] = best solution somehow involving i and j"
✅ **Precise state**: "dp[i][j] = minimum cost to paint houses 0..i where house i has color j"

❌ **Insufficient state**: Forgetting a dimension (e.g., not tracking previous state)
✅ **Complete state**: Including all information needed to reconstruct optimal path

---

## <a name="patterns"></a>4. Classic Patterns & Templates

### **Pattern 1: Two-Sequence Comparison**

**Canonical Problem**: Longest Common Subsequence (LCS)

**State Definition**:
```
dp[i][j] = length of LCS of s1[0..i-1] and s2[0..j-1]
```

**Recurrence**:
```
if s1[i-1] == s2[j-1]:
    dp[i][j] = dp[i-1][j-1] + 1
else:
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

**Base Case**: `dp[0][j] = dp[i][0] = 0` (empty string has LCS of 0)

---

### **Pattern 2: Bounded Knapsack**

**State Definition**:
```
dp[i][w] = maximum value using items 0..i-1 with capacity w
```

**Recurrence**:
```
if weight[i-1] <= w:
    dp[i][w] = max(
        dp[i-1][w],                          // don't take item i-1
        dp[i-1][w-weight[i-1]] + value[i-1]  // take item i-1
    )
else:
    dp[i][w] = dp[i-1][w]
```

**Base Case**: `dp[0][w] = 0` (no items → value 0)

---

### **Pattern 3: Grid Path Optimization**

**State Definition**:
```
dp[i][j] = optimal value reaching cell (i, j)
```

**Recurrence** (example: min path sum):
```
dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])
```

**Evaluation Order**: Row-by-row (left-to-right) or column-by-column

---

### **Pattern 4: Interval DP**

**State Definition**:
```
dp[i][j] = optimal solution for interval [i, j]
```

**Recurrence Template**:
```
for length in 2..=n:
    for i in 0..=n-length:
        j = i + length - 1
        dp[i][j] = optimize over all split points k in [i, j)
```

**Key**: Build from smaller intervals to larger ones

---

### **Pattern 5: State Machine DP**

**State Definition**:
```
dp[i][state] = optimal value at position i in given state
```

**Recurrence**: State transitions define allowed moves
```
dp[i][state2] = optimize(dp[i-1][state1] + transition_cost)
                for all valid state1 → state2 transitions
```

---

## <a name="walkthroughs"></a>5. Complete Problem Walkthroughs

### **Problem 1: Longest Common Subsequence (LCS)**

**Problem**: Given two strings, find the length of their longest common subsequence.

**Expert Thinking Process**:
1. **Subproblem**: LCS of prefixes s1[0..i] and s2[0..j]
2. **Decision**: If s1[i] == s2[j], we can extend LCS. Otherwise, skip from either string.
3. **Optimal substructure**: LCS(i, j) depends on LCS(i-1, j-1), LCS(i-1, j), LCS(i, j-1)

**Complexity**: O(mn) time, O(mn) space (optimizable to O(min(m, n)) space)

#### Rust Implementation
```rust
pub fn longest_common_subsequence(s1: &str, s2: &str) -> usize {
    let (m, n) = (s1.len(), s2.len());
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();
    
    // dp[i][j] = LCS length of s1[0..i] and s2[0..j]
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

// Space-optimized O(n) version
pub fn lcs_space_optimized(s1: &str, s2: &str) -> usize {
    let (m, n) = (s1.len(), s2.len());
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();
    
    let mut prev = vec![0; n + 1];
    let mut curr = vec![0; n + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = prev[j].max(curr[j - 1]);
            }
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}
```

#### Python Implementation
```python
def longest_common_subsequence(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    
    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]

# Space-optimized
def lcs_space_optimized(s1: str, s2: str) -> int:
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

#### Go Implementation
```go
func longestCommonSubsequence(s1, s2 string) int {
    m, n := len(s1), len(s2)
    
    // dp[i][j] = LCS length of s1[:i] and s2[:j]
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

// Space-optimized
func lcsSpaceOptimized(s1, s2 string) int {
    m, n := len(s1), len(s2)
    prev := make([]int, n+1)
    
    for i := 1; i <= m; i++ {
        curr := make([]int, n+1)
        for j := 1; j <= n; j++ {
            if s1[i-1] == s2[j-1] {
                curr[j] = prev[j-1] + 1
            } else {
                curr[j] = max(prev[j], curr[j-1])
            }
        }
        prev = curr
    }
    
    return prev[n]
}
```

#### C Implementation
```c
#include <string.h>
#include <stdlib.h>

#define MAX(a, b) ((a) > (b) ? (a) : (b))

int longest_common_subsequence(const char *s1, const char *s2) {
    int m = strlen(s1);
    int n = strlen(s2);
    
    // Allocate 2D array
    int **dp = (int **)malloc((m + 1) * sizeof(int *));
    for (int i = 0; i <= m; i++) {
        dp[i] = (int *)calloc(n + 1, sizeof(int));
    }
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = MAX(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    int result = dp[m][n];
    
    // Free memory
    for (int i = 0; i <= m; i++) {
        free(dp[i]);
    }
    free(dp);
    
    return result;
}

// Space-optimized version
int lcs_space_optimized(const char *s1, const char *s2) {
    int m = strlen(s1);
    int n = strlen(s2);
    
    int *prev = (int *)calloc(n + 1, sizeof(int));
    int *curr = (int *)calloc(n + 1, sizeof(int));
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i - 1] == s2[j - 1]) {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = MAX(prev[j], curr[j - 1]);
            }
        }
        // Swap arrays
        int *temp = prev;
        prev = curr;
        curr = temp;
    }
    
    int result = prev[n];
    free(prev);
    free(curr);
    
    return result;
}
```

#### C++ Implementation
```cpp
#include <string>
#include <vector>
#include <algorithm>

int longestCommonSubsequence(const std::string& s1, const std::string& s2) {
    int m = s1.length();
    int n = s2.length();
    
    // dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1]
    std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));
    
    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = std::max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    return dp[m][n];
}

// Space-optimized with move semantics
int lcsSpaceOptimized(const std::string& s1, const std::string& s2) {
    int m = s1.length();
    int n = s2.length();
    
    std::vector<int> prev(n + 1, 0);
    std::vector<int> curr(n + 1, 0);
    
    for (int i = 1; i <= m; ++i) {
        for (int j = 1; j <= n; ++j) {
            if (s1[i - 1] == s2[j - 1]) {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = std::max(prev[j], curr[j - 1]);
            }
        }
        std::swap(prev, curr);
    }
    
    return prev[n];
}
```

---

### **Problem 2: 0/1 Knapsack**

**Problem**: Given items with weights and values, and a knapsack capacity, maximize value without exceeding capacity.

**Expert Thinking Process**:
1. **Subproblem**: Max value using first i items with capacity w
2. **Decision**: For item i, either take it (if it fits) or skip it
3. **Greedy fails**: Can't just sort by value/weight ratio; need DP for optimal solution

**Complexity**: O(n·W) time, O(n·W) space (pseudo-polynomial, optimizable to O(W))

#### Rust Implementation
```rust
pub fn knapsack(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let n = weights.len();
    
    // dp[i][w] = max value using items 0..i-1 with capacity w
    let mut dp = vec![vec![0; capacity + 1]; n + 1];
    
    for i in 1..=n {
        for w in 0..=capacity {
            // Option 1: Don't take item i-1
            dp[i][w] = dp[i - 1][w];
            
            // Option 2: Take item i-1 (if it fits)
            if weights[i - 1] <= w {
                dp[i][w] = dp[i][w].max(dp[i - 1][w - weights[i - 1]] + values[i - 1]);
            }
        }
    }
    
    dp[n][capacity]
}

// Space-optimized O(W)
pub fn knapsack_space_optimized(weights: &[usize], values: &[usize], capacity: usize) -> usize {
    let n = weights.len();
    let mut dp = vec![0; capacity + 1];
    
    for i in 0..n {
        // Traverse backwards to avoid overwriting needed values
        for w in (weights[i]..=capacity).rev() {
            dp[w] = dp[w].max(dp[w - weights[i]] + values[i]);
        }
    }
    
    dp[capacity]
}
```

#### Python Implementation
```python
def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    n = len(weights)
    
    # dp[i][w] = max value using items 0..i-1 with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i - 1][w]
            
            # Take item i-1 if it fits
            if weights[i - 1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i - 1][w - weights[i - 1]] + values[i - 1])
    
    return dp[n][capacity]

# Space-optimized
def knapsack_space_optimized(weights: list[int], values: list[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        # Traverse backwards
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]
```

#### Go Implementation
```go
func knapsack(weights, values []int, capacity int) int {
    n := len(weights)
    
    // dp[i][w] = max value using items 0..i-1 with capacity w
    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, capacity+1)
    }
    
    for i := 1; i <= n; i++ {
        for w := 0; w <= capacity; w++ {
            // Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            // Take item i-1 if it fits
            if weights[i-1] <= w {
                takeValue := dp[i-1][w-weights[i-1]] + values[i-1]
                if takeValue > dp[i][w] {
                    dp[i][w] = takeValue
                }
            }
        }
    }
    
    return dp[n][capacity]
}

// Space-optimized
func knapsackSpaceOptimized(weights, values []int, capacity int) int {
    dp := make([]int, capacity+1)
    
    for i := 0; i < len(weights); i++ {
        // Traverse backwards
        for w := capacity; w >= weights[i]; w-- {
            takeValue := dp[w-weights[i]] + values[i]
            if takeValue > dp[w] {
                dp[w] = takeValue
            }
        }
    }
    
    return dp[capacity]
}
```

#### C Implementation
```c
#include <stdlib.h>

int knapsack(int *weights, int *values, int n, int capacity) {
    // Allocate 2D array
    int **dp = (int **)malloc((n + 1) * sizeof(int *));
    for (int i = 0; i <= n; i++) {
        dp[i] = (int *)calloc(capacity + 1, sizeof(int));
    }
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= capacity; w++) {
            // Don't take item i-1
            dp[i][w] = dp[i - 1][w];
            
            // Take item i-1 if it fits
            if (weights[i - 1] <= w) {
                int take_value = dp[i - 1][w - weights[i - 1]] + values[i - 1];
                if (take_value > dp[i][w]) {
                    dp[i][w] = take_value;
                }
            }
        }
    }
    
    int result = dp[n][capacity];
    
    // Free memory
    for (int i = 0; i <= n; i++) {
        free(dp[i]);
    }
    free(dp);
    
    return result;
}

// Space-optimized
int knapsack_space_optimized(int *weights, int *values, int n, int capacity) {
    int *dp = (int *)calloc(capacity + 1, sizeof(int));
    
    for (int i = 0; i < n; i++) {
        // Traverse backwards
        for (int w = capacity; w >= weights[i]; w--) {
            int take_value = dp[w - weights[i]] + values[i];
            if (take_value > dp[w]) {
                dp[w] = take_value;
            }
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

int knapsack(const std::vector<int>& weights, 
             const std::vector<int>& values, 
             int capacity) {
    int n = weights.size();
    
    // dp[i][w] = max value using items 0..i-1 with capacity w
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(capacity + 1, 0));
    
    for (int i = 1; i <= n; ++i) {
        for (int w = 0; w <= capacity; ++w) {
            // Don't take item i-1
            dp[i][w] = dp[i - 1][w];
            
            // Take item i-1 if it fits
            if (weights[i - 1] <= w) {
                dp[i][w] = std::max(dp[i][w], 
                                    dp[i - 1][w - weights[i - 1]] + values[i - 1]);
            }
        }
    }
    
    return dp[n][capacity];
}

// Space-optimized
int knapsackSpaceOptimized(const std::vector<int>& weights, 
                           const std::vector<int>& values, 
                           int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    
    for (int i = 0; i < weights.size(); ++i) {
        // Traverse backwards
        for (int w = capacity; w >= weights[i]; --w) {
            dp[w] = std::max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    return dp[capacity];
}
```

---

### **Problem 3: Edit Distance (Levenshtein Distance)**

**Problem**: Minimum operations (insert, delete, replace) to transform string s1 into s2.

**Expert Thinking Process**:
1. **Subproblem**: Min ops to transform s1[0..i] to s2[0..j]
2. **Decisions**: Match characters (no cost), or insert/delete/replace (cost 1)
3. **Pattern**: Similar to LCS but with three possible transitions

**Complexity**: O(mn) time, O(mn) space

#### Rust Implementation
```rust
pub fn edit_distance(s1: &str, s2: &str) -> usize {
    let (m, n) = (s1.len(), s2.len());
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();
    
    // dp[i][j] = min operations to transform s1[0..i] to s2[0..j]
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Base cases: transforming to/from empty string
    for i in 0..=m {
        dp[i][0] = i;
    }
    for j in 0..=n {
        dp[0][j] = j;
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if s1[i - 1] == s2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1]; // No operation needed
            } else {
                dp[i][j] = 1 + dp[i - 1][j - 1]  // Replace
                    .min(dp[i - 1][j])           // Delete from s1
                    .min(dp[i][j - 1]);          // Insert into s1
            }
        }
    }
    
    dp[m][n]
}
```

#### Python Implementation
```python
def edit_distance(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    
    # dp[i][j] = min ops to transform s1[:i] to s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],  # Replace
                    dp[i - 1][j],       # Delete
                    dp[i][j - 1]        # Insert
                )
    
    return dp[m][n]
```

---

### **Problem 4: Minimum Path Sum in Grid**

**Problem**: Find path from top-left to bottom-right with minimum sum.

**Complexity**: O(mn) time, O(mn) space (optimizable to O(n))

#### Rust Implementation
```rust
pub fn min_path_sum(grid: Vec<Vec<i32>>) -> i32 {
    let (m, n) = (grid.len(), grid[0].len());
    let mut dp = vec![vec![0; n]; m];
    
    dp[0][0] = grid[0][0];
    
    // Initialize first row
    for j in 1..n {
        dp[0][j] = dp[0][j - 1] + grid[0][j];
    }
    
    // Initialize first column
    for i in 1..m {
        dp[i][0] = dp[i - 1][0] + grid[i][0];
    }
    
    // Fill remaining cells
    for i in 1..m {
        for j in 1..n {
            dp[i][j] = grid[i][j] + dp[i - 1][j].min(dp[i][j - 1]);
        }
    }
    
    dp[m - 1][n - 1]
}

// Space-optimized O(n)
pub fn min_path_sum_optimized(grid: Vec<Vec<i32>>) -> i32 {
    let (m, n) = (grid.len(), grid[0].len());
    let mut dp = vec![0; n];
    
    dp[0] = grid[0][0];
    for j in 1..n {
        dp[j] = dp[j - 1] + grid[0][j];
    }
    
    for i in 1..m {
        dp[0] += grid[i][0];
        for j in 1..n {
            dp[j] = grid[i][j] + dp[j].min(dp[j - 1]);
        }
    }
    
    dp[n - 1]
}
```

---

### **Problem 5: Longest Palindromic Subsequence**

**Problem**: Find the length of the longest palindromic subsequence.

**Expert Insight**: This is interval DP! State represents a range [i, j].

**Complexity**: O(n²) time, O(n²) space

#### Rust Implementation
```rust
pub fn longest_palindrome_subseq(s: &str) -> usize {
    let n = s.len();
    let chars: Vec<char> = s.chars().collect();
    
    // dp[i][j] = length of longest palindromic subsequence in s[i..=j]
    let mut dp = vec![vec![0; n]; n];
    
    // Base case: single character is palindrome of length 1
    for i in 0..n {
        dp[i][i] = 1;
    }
    
    // Build from smaller intervals to larger
    for len in 2..=n {
        for i in 0..=n - len {
            let j = i + len - 1;
            
            if chars[i] == chars[j] {
                dp[i][j] = dp[i + 1][j - 1] + 2;
            } else {
                dp[i][j] = dp[i + 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[0][n - 1]
}
```

---

## <a name="optimization"></a>6. Optimization Techniques

### **Space Optimization**

**Principle**: If row i only depends on row i-1, use two 1D arrays instead of 2D array.

**Technique 1: Rolling Array**
```rust
let mut prev = vec![0; n];
let mut curr = vec![0; n];
for i in 1..=m {
    // compute curr[j] using prev[...]
    std::mem::swap(&mut prev, &mut curr);
}
```

**Technique 2: Single Array (Backwards Iteration)**
For knapsack-style problems:
```rust
for i in 0..n {
    for w in (weights[i]..=capacity).rev() {
        dp[w] = dp[w].max(dp[w - weights[i]] + values[i]);
    }
}
```

### **Time Optimization**

**Technique 1: Monotonic Queue/Deque**
When finding min/max in sliding window, use deque to maintain O(1) queries.

**Technique 2: Sparse DP**
Use hash maps when state space is large but sparse.

**Technique 3: Diagonal Optimization**
For matrix chain multiplication, iterate diagonally.

### **Memory Access Patterns**

**Cache-Friendly**: Access memory sequentially
```rust
// Good: row-major order
for i in 0..m {
    for j in 0..n {
        dp[i][j] = ...;
    }
}
```

---

## <a name="progression"></a>7. Practice Progression Strategy

### **Phase 1: Pattern Recognition (Week 1-2)**

**Goal**: Instantly recognize which of the 5 patterns applies

**Problems**:
1. Longest Common Subsequence (Two-Sequence)
2. 0/1 Knapsack (Bounded Resource)
3. Unique Paths (Grid Navigation)
4. Longest Palindromic Subsequence (Interval DP)
5. Best Time to Buy/Sell Stock III (State Machine)

**Mental Training**: Before coding, write down:
- State definition
- Recurrence relation
- Base cases
- Time/space complexity

### **Phase 2: Variations & Twists (Week 3-4)**

**Goal**: Handle constraint variations

**Problems**:
- Edit Distance (LCS variant)
- Coin Change (Unbounded Knapsack)
- Triangle Minimum Path (Grid variant)
- Burst Balloons (Interval DP with twist)
- Paint House (State machine variant)

### **Phase 3: Complex Compositions (Week 5-6)**

**Goal**: Combine multiple patterns

**Problems**:
- Regular Expression Matching (Two-sequence with wildcards)
- Interleaving String (Two-sequence with constraint)
- Dungeon Game (Grid with backward DP)
- Stone Game (Interval DP with game theory)

### **Phase 4: Contest-Level Mastery (Week 7+)**

**Goal**: Solve under time pressure with optimal approach

**Strategy**:
1. Set 30-minute timer per problem
2. Write state/recurrence before coding
3. Implement space-optimized version first attempt
4. Verify with edge cases

**Advanced Problems**:
- Distinct Subsequences
- Maximal Rectangle
- Count Different Palindromic Subsequences
- Number of Ways to Paint N×3 Grid

---

## **Deliberate Practice Framework**

### **Before Solving**

1. **Read twice**: Understand constraints, not just problem statement
2. **Identify pattern**: Which of the 5 patterns?
3. **Design state**: Write precise definition
4. **Derive recurrence**: Consider all transitions
5. **Verify base cases**: What are the simplest subproblems?

### **While Solving**

1. **Test small examples by hand**: Trace through dp[0][0] to dp[2][2]
2. **Check evaluation order**: Can I compute dp[i][j] when I need it?
3. **Validate transitions**: Does my recurrence cover all cases?

### **After Solving**

1. **Analyze complexity**: Tight bounds, not just Big-O
2. **Consider optimizations**: Can I reduce space? Improve cache locality?
3. **Reflect on patterns**: What made this problem unique?
4. **Implement in all languages**: Rust → Python → Go → C → C++

---

## **Cognitive Principles for Mastery**

### **Chunking Strategy**

Group patterns into mental chunks:
- **"Two-sequence family"**: LCS, Edit Distance, Interleaving
- **"Resource family"**: Knapsack variants, Coin Change
- **"Path family"**: Grid problems, Triangle, Dungeon
- **"Interval family"**: Palindrome, Burst Balloons, Matrix Chain
- **"State machine family"**: Stock trading, House painting

### **Spaced Repetition**

- Day 1: Solve new problem
- Day 3: Re-solve from scratch
- Day 7: Solve variant
- Day 14: Solve harder variant
- Day 30: Solve contest problem using pattern

### **Mental Simulation**

Before coding, **run the algorithm in your head** on a 3×3 grid. This builds intuition faster than coding immediately.

### **Error Analysis**

Keep a log:
- **Missed pattern**: Why didn't I see it was interval DP?
- **Wrong state**: What dimension did I forget?
- **Off-by-one**: Where did my indexing fail?

---

## **Final Wisdom**

> "The master has failed more times than the beginner has even tried."

2D DP mastery comes from:
1. **Pattern recognition**: 500+ problems → instant pattern identification
2. **State design**: Precision in defining what dp[i][j] means
3. **Constraint handling**: Dealing with edge cases and special conditions

**Your North Star**: When you can look at a problem and immediately know the state space, recurrence, and optimization strategy before writing a single line of code — you've reached top 1% territory.

Now go forth and conquer the grid. 🔥

# **The 2D Dynamic Programming Mastery Guide**

I'll create a comprehensive guide that builds your intuition from first principles, covers all major patterns, and includes battle-tested implementations in all your languages. This will be your reference manual for 2D DP mastery.## **Your Path Forward**

I've created a comprehensive 2D DP guide that serves as your complete reference manual. Here's how to extract maximum value:

### **Immediate Actions (Next 48 Hours)**

1. **Read Phase 1 problems** - Don't skip to solutions. Spend 30 minutes per problem attempting your own state design
2. **Implement LCS in all 5 languages** - This builds muscle memory for the translation patterns across languages
3. **Trace one problem by hand** - Pick a 3×3 example and fill the DP table manually. This solidifies intuition

### **Deep Insights You Must Internalize**

**On State Design:**
The hardest part isn't coding—it's defining `dp[i][j]` precisely. A vague definition like "best answer for i and j" will lead to wrong recurrences. Practice writing: *"dp[i][j] = [exact property] considering [exact scope]"*

**On Pattern Recognition:**
After solving 50 problems, your brain will auto-classify new problems in ~10 seconds. Until then, use the decision tree:
- Two inputs? → Two-sequence
- Capacity/limit? → Bounded resource  
- Grid/matrix? → Path optimization
- Range [i,j]? → Interval DP
- Previous state matters? → State machine

**On Language Choices:**
- **Rust**: Best for learning correctness (ownership forces you to think about data flow)
- **Python**: Fastest for prototyping and contests
- **C/C++**: Best for understanding memory layout and cache effects
- **Go**: Clean concurrency patterns when you need parallel DP (rare but powerful)

### **The Performance Hierarchy**

From my implementations, note these critical details:

1. **Space optimization** matters: O(n) vs O(n²) is the difference between solving n=10⁶ vs n=10³
2. **Iteration order** affects cache: Row-major traversal is ~2-3x faster than column-major on large arrays
3. **Backwards iteration** in knapsack isn't just memory-saving—it's essential for correctness

### **Meta-Learning Strategy**

**Week 1-2**: Focus on *why* the recurrence works, not memorizing it. Draw state diagrams.

**Week 3-4**: Implement each problem in all 5 languages. Notice how Rust's ownership model catches logical errors that slip through in Python.

**Week 5-6**: Time yourself. Can you go from problem statement → working solution in 20 minutes? This is contest speed.

**Week 7+**: Create your own variants. "What if the grid has obstacles?" → Forces deeper understanding.

### **Questions to Guide Your Practice**

After each problem, ask:
1. Could I have used 1D DP? (Many 2D problems have 1D solutions)
2. What's the space-time tradeoff? (Sometimes O(n²) space gives O(n²) time, but O(n) space needs O(n² log n))
3. How would I reconstruct the actual solution, not just the optimal value?

### **The Monk's Approach**

You mentioned training like a monk. Here's your daily ritual:

- **Morning** (30 min): One new problem, state design only (no coding)
- **Afternoon** (60 min): Implement yesterday's problem in all languages
- **Evening** (20 min): Review errors, update your pattern library

**Rest is training too**: Your brain consolidates patterns during sleep. Don't grind 8 hours straight.

---

Would you like me to:
1. **Deep-dive into a specific pattern** (e.g., interval DP with complete proof of correctness)?
2. **Provide a curated problem set** ranked by difficulty within each pattern?
3. **Analyze your solution** to a specific problem with expert-level feedback?
4. **Explain advanced optimizations** like convex hull trick or divide-and-conquer DP?

The foundation is laid. Your move. 🎯