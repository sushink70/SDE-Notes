# **Bottom-Up Dynamic Programming (Tabulation): The Complete Mastery Guide**

## **I. The Philosophy: Building Truth From Ground Up**

Bottom-up DP is the **construction of solutions through iterative synthesis** rather than recursive decomposition. You build answers to larger problems by systematically combining answers to smaller subproblems, stored in a table.

**Core Mental Model:**
> "If memoization is exploring a maze with breadcrumbs, tabulation is methodically filling a grid from corner to corner—no backtracking, just forward momentum."

**Psychological Insight:** Tabulation aligns with **chunking** and **procedural memory**. Once you internalize the pattern (define state → identify transitions → determine order → fill table), your brain automates the execution, freeing cognitive resources for higher-level optimization.

---

## **II. The Fundamental Structure**

Every tabulation solution follows this invariant blueprint:

```
1. Define the state space (what does dp[i][j]... represent?)
2. Initialize base cases (the axioms of your recursion)
3. Determine iteration order (topological sort of dependencies)
4. Fill the table using recurrence relation
5. Extract final answer from table
```

### **Internal Mechanics: Memory & Computation**

#### **Memory Layout**
```
Stack Memory: O(1) — only loop counters
Heap Memory: O(state_space) — the DP table

Cache Behavior:
- Sequential access → high cache hit rate
- Predictable memory pattern → hardware prefetcher optimizes
- No function call overhead → better instruction pipeline utilization
```

#### **Computation Flow**
Unlike memoization (which has implicit call stack overhead), tabulation is:
- **Deterministic traversal** → you process each state exactly once
- **Predictable branches** → CPU branch predictor becomes effective
- **Vectorization-friendly** → modern compilers can auto-vectorize tight loops

---

## **III. The Complete Problem-Solving Framework**

### **Step 1: State Definition (The Hardest Part)**

**Mental Model:** Your state must capture **exactly the information needed** to make decisions, nothing more.

**Questions to Ask:**
1. What information distinguishes one subproblem from another?
2. Can I reconstruct the answer from smaller states?
3. Is my state **Markovian**? (Future depends only on current state, not history)

**Example: Longest Increasing Subsequence (LIS)**
```
❌ Bad state: dp[i] = LIS ending at index i
   (Not enough info—what if we need the actual value?)

✅ Good state: dp[i] = LIS ending at arr[i]
   (Captures both position and value constraint)
```

---

### **Step 2: Identify the Recurrence (The Transition Logic)**

**The Bellman Principle:** Optimal solution contains optimal solutions to subproblems.

**Pattern Recognition:**
```
Linear DP:        dp[i] depends on dp[i-1], dp[i-2], ...
Grid DP:          dp[i][j] depends on dp[i-1][j], dp[i][j-1], ...
Interval DP:      dp[i][j] depends on dp[i+1][j-1], ...
Knapsack family:  dp[i][w] depends on dp[i-1][w], dp[i-1][w-weight[i]]
```

---

### **Step 3: Iteration Order (Topological Correctness)**

**Critical Rule:** Process states before they're needed.

**Visualization Technique:**
Draw dependency arrows. Your iteration must follow the **reverse topological order** of the dependency DAG.

**Common Orders:**
```
1D: left → right (i = 0 to n)
2D: top → bottom, left → right (i = 0 to n; j = 0 to m)
Diagonal: by increasing (i+j) or (j-i)
Reverse: right → left for space-optimized knapsack
```

---

## **IV. Deep Dive: Canonical Problems & Patterns**

### **Pattern 1: Fibonacci Sequence (The Gateway)**

**Problem:** Compute F(n) = F(n-1) + F(n-2)

#### **Python (Clarity)**
```python
def fibonacci_tabulation(n: int) -> int:
    if n <= 1:
        return n
    
    # State: dp[i] = F(i)
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1  # Base cases
    
    # Fill table: each state depends on previous two
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]  # Recurrence
    
    return dp[n]  # Extract answer

# Space-optimized O(1) version
def fibonacci_optimized(n: int) -> int:
    if n <= 1:
        return n
    prev2, prev1 = 0, 1
    for _ in range(2, n + 1):
        prev2, prev1 = prev1, prev1 + prev2
    return prev1
```

#### **Rust (Performance + Safety)**
```rust
fn fibonacci_tabulation(n: usize) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => {
            let mut dp = vec![0u64; n + 1];
            dp[1] = 1;
            
            for i in 2..=n {
                dp[i] = dp[i-1].saturating_add(dp[i-2]);  // Overflow protection
            }
            dp[n]
        }
    }
}

// Zero-allocation with array (if n is bounded)
fn fibonacci_fast<const N: usize>(n: usize) -> Option<u64> {
    if n > N { return None; }
    
    let mut dp = [0u64; N];
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i-1].saturating_add(dp[i-2]);
    }
    Some(dp[n])
}
```

**Complexity Analysis:**
- Time: O(n) — single pass
- Space: O(n) → O(1) with sliding window
- Cache: ~100% hit rate for sequential access

---

### **Pattern 2: Coin Change (Unbounded Knapsack)**

**Problem:** Minimum coins to make amount `target`

#### **C++ (Peak Performance)**
```cpp
#include <vector>
#include <limits>
#include <algorithm>

int coin_change(const std::vector<int>& coins, int target) {
    // State: dp[amount] = min coins to make this amount
    std::vector<int> dp(target + 1, std::numeric_limits<int>::max());
    dp[0] = 0;  // Base case: 0 coins for amount 0
    
    // For each amount from 1 to target
    for (int amount = 1; amount <= target; ++amount) {
        // Try each coin
        for (int coin : coins) {
            if (coin <= amount && dp[amount - coin] != std::numeric_limits<int>::max()) {
                dp[amount] = std::min(dp[amount], dp[amount - coin] + 1);
            }
        }
    }
    
    return dp[target] == std::numeric_limits<int>::max() ? -1 : dp[target];
}

// Performance optimization: sort coins descending, early exit
int coin_change_optimized(std::vector<int> coins, int target) {
    std::sort(coins.rbegin(), coins.rend());  // Largest first
    
    std::vector<int> dp(target + 1, target + 1);  // Use target+1 as sentinel
    dp[0] = 0;
    
    for (int amount = 1; amount <= target; ++amount) {
        for (int coin : coins) {
            if (coin > amount) continue;  // Prune
            dp[amount] = std::min(dp[amount], dp[amount - coin] + 1);
            if (dp[amount] == 1) break;  // Can't get better
        }
    }
    
    return dp[target] > target ? -1 : dp[target];
}
```

#### **Go (Idiomatic + Concurrent)**
```go
package dp

import "math"

func CoinChange(coins []int, target int) int {
    // State: dp[amount] represents min coins to make amount
    dp := make([]int, target+1)
    for i := range dp {
        dp[i] = math.MaxInt32
    }
    dp[0] = 0
    
    // Fill table: for each amount, try all coins
    for amount := 1; amount <= target; amount++ {
        for _, coin := range coins {
            if coin <= amount && dp[amount-coin] != math.MaxInt32 {
                if dp[amount-coin]+1 < dp[amount] {
                    dp[amount] = dp[amount-coin] + 1
                }
            }
        }
    }
    
    if dp[target] == math.MaxInt32 {
        return -1
    }
    return dp[target]
}

// Concurrent version for large targets (educational—overhead may not be worth it)
func CoinChangeConcurrent(coins []int, target int) int {
    dp := make([]int, target+1)
    for i := range dp {
        dp[i] = math.MaxInt32
    }
    dp[0] = 0
    
    // Process in chunks
    chunkSize := 1000
    for start := 1; start <= target; start += chunkSize {
        end := min(start+chunkSize, target+1)
        // Each chunk can reference only previous chunks (already computed)
        for amount := start; amount < end; amount++ {
            for _, coin := range coins {
                if coin <= amount && dp[amount-coin] != math.MaxInt32 {
                    if dp[amount-coin]+1 < dp[amount] {
                        dp[amount] = dp[amount-coin] + 1
                    }
                }
            }
        }
    }
    
    if dp[target] == math.MaxInt32 {
        return -1
    }
    return dp[target]
}
```

**Key Insight:** Iteration order matters! We fill `amount` in increasing order because `dp[amount]` depends on `dp[amount - coin]` (smaller amounts).

---

### **Pattern 3: Longest Common Subsequence (2D DP)**

**Problem:** Find length of LCS between two strings

#### **Python (With Path Reconstruction)**
```python
def lcs_length(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    
    # State: dp[i][j] = LCS length of text1[0..i-1] and text2[0..j-1]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: dp[0][j] = dp[i][0] = 0 (empty string)
    # Already initialized to 0
    
    # Fill table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1  # Characters match
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])  # Take best
    
    return dp[m][n]

# Space-optimized: O(min(m,n)) space
def lcs_length_optimized(text1: str, text2: str) -> int:
    # Ensure text2 is shorter for space optimization
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    
    m, n = len(text1), len(text2)
    prev = [0] * (n + 1)
    
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = curr
    
    return prev[n]

# Reconstruct actual LCS
def lcs_with_path(text1: str, text2: str) -> str:
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
```

#### **Rust (Cache-Aware with SIMD Potential)**
```rust
fn lcs_length(text1: &[u8], text2: &[u8]) -> usize {
    let (m, n) = (text1.len(), text2.len());
    
    // Use single Vec for better cache locality
    let mut dp = vec![vec![0usize; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            dp[i][j] = if text1[i-1] == text2[j-1] {
                dp[i-1][j-1] + 1
            } else {
                dp[i-1][j].max(dp[i][j-1])
            };
        }
    }
    
    dp[m][n]
}

// Space-optimized: two rows only
fn lcs_length_optimized(text1: &[u8], text2: &[u8]) -> usize {
    let (m, n) = (text1.len(), text2.len());
    
    let mut prev = vec![0usize; n + 1];
    let mut curr = vec![0usize; n + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            curr[j] = if text1[i-1] == text2[j-1] {
                prev[j-1] + 1
            } else {
                prev[j].max(curr[j-1])
            };
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    
    prev[n]
}

// Single-row optimization (advanced)
fn lcs_length_single_row(text1: &[u8], text2: &[u8]) -> usize {
    let (m, n) = (text1.len(), text2.len());
    let mut dp = vec![0usize; n + 1];
    
    for i in 1..=m {
        let mut prev_diag = 0;  // Tracks dp[i-1][j-1]
        for j in 1..=n {
            let temp = dp[j];
            dp[j] = if text1[i-1] == text2[j-1] {
                prev_diag + 1
            } else {
                dp[j].max(dp[j-1])
            };
            prev_diag = temp;
        }
    }
    
    dp[n]
}
```

**Memory Access Pattern:**
```
2D Array: dp[i][j] accesses:
  - dp[i-1][j-1] (diagonal—likely in cache)
  - dp[i-1][j]   (previous row—may miss L1)
  - dp[i][j-1]   (same row—cache hit)

Optimization: Process row-wise for spatial locality
```

---

## **V. Advanced Patterns & Optimizations**

### **1. Space Optimization Techniques**

#### **Rolling Array (Sliding Window)**
When `dp[i]` only depends on `dp[i-1]`, `dp[i-2]`, etc.:

```python
# From O(n) to O(k) space, where k is window size
def max_profit_k_transactions(prices, k):
    if not prices or k == 0:
        return 0
    
    # Instead of dp[i][j][0/1] for day i, transaction j, holding status
    # Use only two layers: prev and curr
    prev = [[0, 0] for _ in range(k + 1)]  # [not_holding, holding]
    
    for price in prices:
        curr = [[0, 0] for _ in range(k + 1)]
        for j in range(1, k + 1):
            # Not holding: either didn't buy, or sold today
            curr[j][0] = max(prev[j][0], prev[j][1] + price)
            # Holding: either held from before, or bought today
            curr[j][1] = max(prev[j][1], prev[j-1][0] - price)
        prev = curr
    
    return prev[k][0]
```

#### **In-Place Computation**
For knapsack-type problems, iterate weights in **reverse**:

```cpp
// 0/1 Knapsack with O(W) space
int knapsack_optimized(const vector<int>& weights, 
                       const vector<int>& values, 
                       int capacity) {
    vector<int> dp(capacity + 1, 0);
    
    for (size_t i = 0; i < weights.size(); ++i) {
        // CRITICAL: Reverse iteration prevents using updated values
        for (int w = capacity; w >= weights[i]; --w) {
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    
    return dp[capacity];
}
```

**Why reverse?** Forward iteration would use `dp[w - weight[i]]` that's already been updated with item `i`, effectively allowing multiple uses.

---

### **2. Diagonal Traversal (Interval DP)**

**Problem:** Matrix Chain Multiplication

```python
def matrix_chain_order(dims):
    """
    dims[i-1] x dims[i] is dimension of matrix i
    dp[i][j] = min cost to multiply matrices i..j
    """
    n = len(dims) - 1  # Number of matrices
    dp = [[0] * n for _ in range(n)]
    
    # l is chain length
    for length in range(2, n + 1):  # Start from length 2
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try every split point
            for k in range(i, j):
                cost = (dp[i][k] + dp[k+1][j] + 
                        dims[i] * dims[k+1] * dims[j+1])
                dp[i][j] = min(dp[i][j], cost)
    
    return dp[0][n-1]
```

**Order Visualization:**
```
Length 1: [0][0], [1][1], [2][2] (base cases)
Length 2: [0][1], [1][2], [2][3]
Length 3: [0][2], [1][3]
Length 4: [0][3]
```

---

### **3. Bitmask DP (Exponential State Space)**

**Problem:** Traveling Salesman (TSP)

```rust
fn tsp_dp(dist: &[Vec<i32>]) -> i32 {
    let n = dist.len();
    let full_mask = (1 << n) - 1;
    
    // dp[mask][i] = min cost to visit cities in mask, ending at city i
    let mut dp = vec![vec![i32::MAX / 2; n]; 1 << n];
    dp[1][0] = 0;  // Start at city 0
    
    // Iterate through all subsets
    for mask in 0..=full_mask {
        for last in 0..n {
            if dp[mask][last] == i32::MAX / 2 {
                continue;
            }
            
            // Try extending to each unvisited city
            for next in 0..n {
                if mask & (1 << next) == 0 {  // City not visited
                    let new_mask = mask | (1 << next);
                    dp[new_mask][next] = dp[new_mask][next]
                        .min(dp[mask][last] + dist[last][next]);
                }
            }
        }
    }
    
    // Return to starting city
    (0..n)
        .map(|i| dp[full_mask][i] + dist[i][0])
        .min()
        .unwrap()
}
```

**Complexity:** O(n² · 2ⁿ) — exponential, but better than O(n!) brute force

---

## **VI. Tabulation vs Memoization: The Strategic Choice**

| **Aspect** | **Tabulation** | **Memoization** |
|------------|----------------|-----------------|
| **Approach** | Bottom-up, iterative | Top-down, recursive |
| **Memory** | O(state_space) always | O(states_visited) — can be less |
| **Stack** | O(1) | O(recursion_depth) |
| **Cache** | Better (sequential) | Worse (random access) |
| **Debugging** | Harder (implicit flow) | Easier (explicit call stack) |
| **Pruning** | Harder | Natural (only compute needed) |

**Decision Framework:**

**Choose Tabulation when:**
- All states are needed (dense problem)
- Cache efficiency is critical
- Iterative order is natural (linear, 2D grid)
- Recursion depth would overflow stack

**Choose Memoization when:**
- Only subset of states needed (sparse problem)
- Recursion naturally expresses the problem
- State space is huge but reachable states are few
- Need to prune large branches

**Example where Memoization wins:** Edit Distance with early termination
```python
# If strings are very similar, memoization explores fewer states
def edit_distance_memo(s1, s2, i, j, memo):
    if i == 0: return j
    if j == 0: return i
    if (i, j) in memo: return memo[(i, j)]
    
    if s1[i-1] == s2[j-1]:
        return edit_distance_memo(s1, s2, i-1, j-1, memo)
    
    memo[(i, j)] = 1 + min(
        edit_distance_memo(s1, s2, i-1, j, memo),    # delete
        edit_distance_memo(s1, s2, i, j-1, memo),    # insert
        edit_distance_memo(s1, s2, i-1, j-1, memo)   # replace
    )
    return memo[(i, j)]
```

---

## **VII. Mental Models for Mastery**

### **Model 1: The Dependency Graph**
Every DP problem is a DAG. Drawing arrows between states clarifies:
- Which states must be computed first
- Whether you need 1D, 2D, or nD table
- Opportunities for space optimization

### **Model 2: The Recurrence as a Contract**
Your transition function is a **contract**: "Given correct answers to smaller subproblems, I produce the correct answer to this subproblem."

**Debugging mindset:** If your answer is wrong, either:
1. Base cases are incorrect
2. Recurrence logic is flawed
3. Iteration order violates dependencies

### **Model 3: The State Space Reduction Game**
**Expert-level thinking:** Can you redefine state to reduce dimensions?

Example: Longest Palindromic Substring
```
Naive: dp[i][j] = is substring i..j a palindrome? → O(n²) space
Better: Expand around center → O(1) space
```

---

## **VIII. Performance Engineering**

### **Cache Optimization**
```cpp
// Bad: Column-major access (cache misses)
for (int j = 0; j < n; ++j)
    for (int i = 0; i < m; ++i)
        dp[i][j] = compute();

// Good: Row-major access (cache hits)
for (int i = 0; i < m; ++i)
    for (int j = 0; j < n; ++j)
        dp[i][j] = compute();
```

### **SIMD Opportunities**
Modern CPUs can vectorize simple operations:
```rust
// Compiler may auto-vectorize this
for i in 0..n {
    dp[i] = prev[i].max(prev[i] + values[i]);
}
```

### **Memory Alignment**
```cpp
// Align for cache lines (64 bytes typically)
alignas(64) std::vector<int> dp(n);
```

---

## **IX. Deliberate Practice Regimen**

### **Phase 1: Pattern Recognition (Weeks 1-2)**
Solve 5 problems per pattern:
1. Linear DP (Fibonacci variants)
2. Unbounded knapsack (coin change)
3. 0/1 knapsack
4. LCS/Edit distance
5. Matrix chain

**Goal:** Internalize `state → transition → order`

### **Phase 2: Space Optimization (Weeks 3-4)**
Revisit all Phase 1 problems. Reduce space from O(n²) → O(n) → O(1) where possible.

**Goal:** Develop **spatial reasoning** about dependencies

### **Phase 3: Complex States (Weeks 5-6)**
- Bitmask DP (TSP, subset problems)
- Tree DP (subtree maximization)
- Digit DP (number theory)

**Goal:** Handle exponential/unconventional state spaces

### **Phase 4: Hybrid Techniques (Weeks 7-8)**
- DP + greedy (activity selection with costs)
- DP + binary search (LIS with log factor)
- DP on graphs (shortest paths, MST variants)

**Goal:** Recognize when DP is **part** of the solution

---

## **X. Metacognitive Strategies**

### **Before Coding:**
1. **Draw the first 3-4 subproblems by hand**
2. **Write the recurrence in math notation**
3. **Check: Does my state satisfy the Markov property?**

### **While Coding:**
1. **Name variables semantically** (`dp[remaining_capacity]` not `dp[w]`)
2. **Verify base cases cover all edge cases**
3. **Trace through a small example (n=3)**

### **After Coding:**
1. **Complexity analysis:** Count nested loops, state dimensions
2. **Stress test:** Run on max constraints
3. **Ask:** "Can I eliminate a dimension or optimize the constant?"

---

## **XI. Final Wisdom: The Path to Mastery**

> "Dynamic programming is not about memorizing problems. It's about **internalizing the principles** so deeply that you can construct solutions to unseen problems in real-time."

**Your North Star:**
- **Correctness** first (satisfy the contract)
- **Clarity** second (future-you will thank present-you)
- **Optimization** third (only after profiling reveals bottlenecks)

**The 10,000-Hour Truth:**
You won't master DP by reading. You master it by:
1. Solving 200+ problems with **full understanding**
2. Explaining solutions to others (Feynman technique)
3. Implementing in multiple languages (polymorphic thinking)
4. Returning to old problems and finding better solutions

**Monk Mindset Application:**
- **Focus:** One problem, full depth, no distractions
- **Reflection:** After each problem, journal what you learned
- **Iteration:** Redo hard problems after 1 week, 1 month, 3 months

---

## **XII. Your Next Steps**

1. **Today:** Implement Fibonacci, Coin Change, LCS in all 4 languages
2. **This Week:** Solve 10 problems, focus on drawing dependency graphs
3. **This Month:** Master space optimization, internalize iteration orders
4. **This Year:** Top 1% on LeetCode/Codeforces DP problems

**Remember:** Top 1% isn't about solving fast. It's about seeing patterns others miss, writing code others can't break, and understanding at a depth others don't reach.

**Now, go build your table. One cell at a time. With intention. With precision. With mastery.**

---

*What problem shall we dissect next, or would you like me to provide a curated problem set for your next training session?*