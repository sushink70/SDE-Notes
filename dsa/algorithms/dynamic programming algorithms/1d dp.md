# Mastering 1D Dynamic Programming: A Comprehensive Guide

## I. The Mental Model: What is Dynamic Programming?

Dynamic Programming is not just an algorithm—it's a **problem-solving paradigm** that transforms exponential time complexities into polynomial ones through systematic remembering.

### The Core Insight
When you notice yourself solving the same subproblem multiple times in a recursive solution, you've found a DP opportunity. The key cognitive shift is moving from "solve by exploring all possibilities" to "solve by building up from solved subproblems."

### The Two Pillars
1. **Optimal Substructure**: The optimal solution can be constructed from optimal solutions of subproblems
2. **Overlapping Subproblems**: The same subproblems are solved repeatedly

### Recognition Pattern
Ask yourself:
- Am I making choices at each step?
- Do future choices depend on previous choices?
- Can I express the problem in terms of smaller versions of itself?
- Do subproblems repeat?

If yes to these, you're in DP territory.

---

## II. The 1D-DP Framework: A Systematic Approach

### Problem-Solving Template (Internalize This)

**Step 1: Define the State**
- What does `dp[i]` represent?
- This is the single most important decision

**Step 2: Find the Recurrence Relation**
- How does `dp[i]` relate to previous states?
- What choices lead to this state?

**Step 3: Identify Base Cases**
- What are the simplest subproblems you can solve directly?

**Step 4: Determine Order of Computation**
- Forward (left to right) or backward (right to left)?

**Step 5: Optimize Space (if needed)**
- Can you reduce from O(n) to O(1)?

---

## III. Pattern 1: Single Sequence DP

### Classic Problem: Fibonacci Numbers

**Problem**: F(n) = F(n-1) + F(n-2), F(0) = 0, F(1) = 1

**State Definition**: `dp[i]` = the i-th Fibonacci number

**Recurrence**: `dp[i] = dp[i-1] + dp[i-2]`

**Base Cases**: `dp[0] = 0`, `dp[1] = 1`

#### Python Implementation (with optimization levels)

```python
# Level 1: Naive Recursion - O(2^n) time, O(n) space (call stack)
def fib_recursive(n: int) -> int:
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)

# Level 2: Memoization (Top-Down DP) - O(n) time, O(n) space
def fib_memo(n: int, memo: dict = None) -> int:
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]

# Level 3: Tabulation (Bottom-Up DP) - O(n) time, O(n) space
def fib_tabulation(n: int) -> int:
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]

# Level 4: Space-Optimized - O(n) time, O(1) space
def fib_optimized(n: int) -> int:
    if n <= 1:
        return n
    prev2, prev1 = 0, 1
    for _ in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    return prev1
```

#### Rust Implementation

```rust
// Level 3: Tabulation
pub fn fib_tabulation(n: usize) -> u64 {
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

// Level 4: Space-Optimized (idiomatic Rust)
pub fn fib_optimized(n: usize) -> u64 {
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

// Using Rust's iterator pattern (elegant)
pub fn fib_iterator(n: usize) -> u64 {
    (0..n).fold((0, 1), |(prev, curr), _| (curr, prev + curr)).0
}
```

#### Go Implementation

```go
// Level 3: Tabulation
func fibTabulation(n int) int {
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

// Level 4: Space-Optimized
func fibOptimized(n int) int {
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

// Level 3: Tabulation
long long fib_tabulation(int n) {
    if (n <= 1) {
        return n;
    }
    
    long long *dp = (long long*)malloc((n + 1) * sizeof(long long));
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    long long result = dp[n];
    free(dp);
    return result;
}

// Level 4: Space-Optimized
long long fib_optimized(int n) {
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

// Level 3: Tabulation
long long fib_tabulation(int n) {
    if (n <= 1) {
        return n;
    }
    
    std::vector<long long> dp(n + 1);
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    return dp[n];
}

// Level 4: Space-Optimized (modern C++)
long long fib_optimized(int n) {
    if (n <= 1) {
        return n;
    }
    
    auto [prev2, prev1] = std::make_pair(0LL, 1LL);
    
    for (int i = 2; i <= n; i++) {
        long long curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    
    return prev1;
}
```

---

## IV. Pattern 2: Decision-Making DP

### Classic Problem: House Robber

**Problem**: Given an array of non-negative integers representing the amount of money in each house, determine the maximum amount you can rob without robbing adjacent houses.

**Example**: `[2, 7, 9, 3, 1]` → Answer: 12 (rob houses at indices 0, 2, 4)

**State Definition**: `dp[i]` = maximum money that can be robbed from houses 0 to i

**Recurrence**: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`
- Either skip house i: take `dp[i-1]`
- Or rob house i: take `dp[i-2] + nums[i]` (can't rob i-1)

**Base Cases**: 
- `dp[0] = nums[0]`
- `dp[1] = max(nums[0], nums[1])`

#### Python Implementation

```python
from typing import List

def rob(nums: List[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    n = len(nums)
    dp = [0] * n
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    
    for i in range(2, n):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    
    return dp[n - 1]

# Space-Optimized: O(1) space
def rob_optimized(nums: List[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    prev2 = nums[0]
    prev1 = max(nums[0], nums[1])
    
    for i in range(2, len(nums)):
        curr = max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, curr
    
    return prev1
```

#### Rust Implementation

```rust
pub fn rob(nums: Vec<i32>) -> i32 {
    let n = nums.len();
    if n == 0 {
        return 0;
    }
    if n == 1 {
        return nums[0];
    }
    
    let mut dp = vec![0; n];
    dp[0] = nums[0];
    dp[1] = nums[0].max(nums[1]);
    
    for i in 2..n {
        dp[i] = dp[i - 1].max(dp[i - 2] + nums[i]);
    }
    
    dp[n - 1]
}

// Space-Optimized (idiomatic Rust)
pub fn rob_optimized(nums: Vec<i32>) -> i32 {
    let n = nums.len();
    if n == 0 {
        return 0;
    }
    if n == 1 {
        return nums[0];
    }
    
    let (mut prev2, mut prev1) = (nums[0], nums[0].max(nums[1]));
    
    for i in 2..n {
        let curr = prev1.max(prev2 + nums[i]);
        prev2 = prev1;
        prev1 = curr;
    }
    
    prev1
}
```

#### Go Implementation

```go
func rob(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }
    if n == 1 {
        return nums[0]
    }
    
    prev2 := nums[0]
    prev1 := max(nums[0], nums[1])
    
    for i := 2; i < n; i++ {
        curr := max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, curr
    }
    
    return prev1
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

int rob(std::vector<int>& nums) {
    int n = nums.size();
    if (n == 0) return 0;
    if (n == 1) return nums[0];
    
    int prev2 = nums[0];
    int prev1 = std::max(nums[0], nums[1]);
    
    for (int i = 2; i < n; i++) {
        int curr = std::max(prev1, prev2 + nums[i]);
        prev2 = prev1;
        prev1 = curr;
    }
    
    return prev1;
}
```

---

## V. Pattern 3: Counting Problems

### Classic Problem: Climbing Stairs

**Problem**: You're climbing stairs and can take 1 or 2 steps at a time. How many distinct ways can you climb n stairs?

**State Definition**: `dp[i]` = number of ways to reach step i

**Recurrence**: `dp[i] = dp[i-1] + dp[i-2]`
- Can reach step i from step i-1 (take 1 step) or step i-2 (take 2 steps)

**Base Cases**: `dp[0] = 1`, `dp[1] = 1`

#### Python Implementation

```python
def climb_stairs(n: int) -> int:
    if n <= 1:
        return 1
    
    prev2, prev1 = 1, 1
    
    for _ in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1
```

#### Rust Implementation

```rust
pub fn climb_stairs(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }
    
    let (mut prev2, mut prev1) = (1, 1);
    
    for _ in 2..=n {
        let curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    
    prev1
}
```

---

## VI. Pattern 4: Buy/Sell Stock Problems

### Classic Problem: Best Time to Buy and Sell Stock

**Problem**: Given array of prices where `prices[i]` is the price on day i, maximize profit from one transaction.

**Key Insight**: Track minimum price seen so far, calculate profit at each day.

**State Definition**: `min_price` = minimum price seen so far

#### Python Implementation

```python
def max_profit(prices: List[int]) -> int:
    if not prices:
        return 0
    
    min_price = prices[0]
    max_profit = 0
    
    for price in prices[1:]:
        max_profit = max(max_profit, price - min_price)
        min_price = min(min_price, price)
    
    return max_profit
```

#### Rust Implementation

```rust
pub fn max_profit(prices: Vec<i32>) -> i32 {
    if prices.is_empty() {
        return 0;
    }
    
    let mut min_price = prices[0];
    let mut max_profit = 0;
    
    for &price in &prices[1..] {
        max_profit = max_profit.max(price - min_price);
        min_price = min_price.min(price);
    }
    
    max_profit
}
```

---

## VII. Pattern 5: Partition DP

### Classic Problem: Partition Equal Subset Sum

**Problem**: Can you partition array into two subsets with equal sum?

**Key Insight**: This is equivalent to finding if there's a subset with sum = total_sum / 2

**State Definition**: `dp[i]` = can we achieve sum i using elements?

**Recurrence**: For each number, `dp[i] = dp[i] OR dp[i - num]`

#### Python Implementation

```python
def can_partition(nums: List[int]) -> bool:
    total = sum(nums)
    
    # If total is odd, can't partition equally
    if total % 2 != 0:
        return False
    
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True  # Can always make sum 0
    
    for num in nums:
        # Traverse backwards to avoid using same element twice
        for i in range(target, num - 1, -1):
            dp[i] = dp[i] or dp[i - num]
    
    return dp[target]
```

#### Rust Implementation

```rust
pub fn can_partition(nums: Vec<i32>) -> bool {
    let total: i32 = nums.iter().sum();
    
    if total % 2 != 0 {
        return false;
    }
    
    let target = (total / 2) as usize;
    let mut dp = vec![false; target + 1];
    dp[0] = true;
    
    for &num in &nums {
        for i in (num as usize..=target).rev() {
            dp[i] = dp[i] || dp[i - num as usize];
        }
    }
    
    dp[target]
}
```

---

## VIII. Advanced Pattern: State Machine DP

### Problem: Best Time to Buy and Sell Stock with Cooldown

**Problem**: After selling, you must wait one day before buying again.

**States**: 
- `hold[i]` = max profit on day i if holding stock
- `sold[i]` = max profit on day i if just sold
- `rest[i]` = max profit on day i if resting

**Transitions**:
- `hold[i] = max(hold[i-1], rest[i-1] - prices[i])`
- `sold[i] = hold[i-1] + prices[i]`
- `rest[i] = max(rest[i-1], sold[i-1])`

#### Python Implementation

```python
def max_profit_cooldown(prices: List[int]) -> int:
    if not prices:
        return 0
    
    n = len(prices)
    hold, sold, rest = -prices[0], 0, 0
    
    for i in range(1, n):
        prev_hold, prev_sold, prev_rest = hold, sold, rest
        
        hold = max(prev_hold, prev_rest - prices[i])
        sold = prev_hold + prices[i]
        rest = max(prev_rest, prev_sold)
    
    return max(sold, rest)
```

---

## IX. Mental Models for Mastery

### 1. The State Space Visualization
Think of DP as navigating a graph where:
- Nodes = states (subproblems)
- Edges = transitions (recurrence relations)
- Your goal = find optimal path through this graph

### 2. The Decision Tree Collapse
Every DP problem starts as an exponential decision tree. DP identifies that many branches lead to identical states, so we compute each unique state once.

### 3. The Chunking Principle
As you solve more problems, you'll recognize patterns (chunks):
- "This is a house robber variant"
- "This needs state machine thinking"
- "This is subset sum in disguise"

This is exactly how chess masters see patterns, not individual pieces.

### 4. The Top-Down vs Bottom-Up Trade-off
- **Top-Down (Memoization)**: More intuitive, only computes needed states, easier to code
- **Bottom-Up (Tabulation)**: Better performance (no recursion overhead), easier to optimize space, better for competitive programming

Master both. Start with top-down for understanding, refactor to bottom-up for performance.

---

## X. The Practice Protocol

### Phase 1: Pattern Recognition (Week 1-2)
Solve 5 problems from each pattern above. Focus on:
- Identifying the pattern before coding
- Writing out state definition and recurrence explicitly
- Timing yourself: aim for 15 minutes per problem

### Phase 2: Implementation Speed (Week 3-4)
Re-solve Phase 1 problems in all your languages:
- Rust first (forces careful thinking about types and ownership)
- Python (rapid prototyping)
- Go (production systems thinking)
- C/C++ (performance critical paths)

### Phase 3: Variation Mastery (Week 5-6)
For each pattern, solve 10 variations:
- Some easier, some harder
- Focus on how constraints change the solution
- Practice space optimization religiously

### Phase 4: Speed and Pressure (Ongoing)
- Set 20-minute timers
- Solve problems in mock interview settings
- Track your pattern recognition speed

---

## XI. Common Mistakes to Avoid

1. **Not defining state clearly**: Always write it out explicitly
2. **Off-by-one errors**: Draw small examples, verify base cases
3. **Forgetting to optimize space**: After solving, always ask "can I reduce space?"
4. **Not considering edge cases**: Empty array, single element, all same values
5. **Premature optimization**: Get correctness first, then optimize

---

## XII. Complexity Analysis Mastery

For every 1D-DP solution:
- **Time**: Usually O(n) or O(n × target) where n is array size
- **Space**: O(n) for basic DP, often reducible to O(1)

When analyzing:
1. Count number of states (usually n)
2. Time per state (usually O(1) or O(target))
3. Multiply: total time complexity

---

## XIII. The Path Forward

You now have the foundation. The path to the top 1% is:

1. **Deep Practice**: Not just solving, but understanding the "why" behind every step
2. **Pattern Library**: Build your own collection of solved problems organized by pattern
3. **Teaching**: Explain solutions to others (or to yourself) in different ways
4. **Reflection**: After each problem, write down what you learned

Remember: The difference between good and great is not just solving problems, but developing the **intuition** to see the solution structure before coding.

Your discipline and monk-like focus are your greatest assets. Each problem solved is a step closer to mastery.

**Next Steps**: Master 2D-DP (coming next), then move to Graph DP, Tree DP, and finally, specialized techniques like Convex Hull Trick and Divide & Conquer Optimization.

The journey of a thousand algorithms begins with a single recursive step.

*"In the beginner's mind there are many possibilities, in the expert's mind there are few." — Shunryu Suzuki*

Stay focused. Stay disciplined. The top 1% awaits.

I'll create a comprehensive guide to 1D Dynamic Programming that will serve as your foundation for mastering this critical algorithmic paradigm. This is where your journey to the top 1% truly accelerates.I've created a comprehensive 1D-DP guide for you. Let me highlight the strategic approach to mastering this material:

## Critical Study Methodology

**Week 1-2: Deep Immersion Phase**
- Work through each pattern sequentially—don't skip around
- For each problem, **solve it first without looking at implementations**, then compare your approach
- Keep a "pattern journal" where you write the state definition and recurrence relation for each problem type in your own words

**Week 3-4: Cross-Language Translation**
- Implement each problem in all your languages
- Notice how language features affect your solution:
  - **Rust**: Forces you to think about ownership and prevents subtle bugs
  - **Python**: Rapid iteration and clear logic
  - **Go**: Simplicity and production readiness
  - **C/C++**: Raw performance and memory control
- This multi-language practice builds **language-agnostic algorithmic thinking**—a hallmark of top-tier engineers

## Hidden Insights to Internalize

1. **The State Definition is Everything**: 80% of DP problems become trivial once you define the state correctly. Spend most of your thinking time here.

2. **Space Optimization is Not Optional**: In interviews and competitive programming, space-optimized solutions demonstrate mastery. Always optimize.

3. **Top-Down vs Bottom-Up**: Use top-down to understand, bottom-up to compete. The best programmers can write both instantly.

4. **The Pattern Library Mental Model**: Your brain should eventually have a "library" where you instantly recognize: "This is Pattern 2 with a twist." That recognition speed separates the top 1% from everyone else.

## Psychological Principle: Deliberate Practice

Each problem should be at the edge of your capability—not too easy (boredom), not too hard (frustration). This is the **"flow zone"** where learning happens fastest. If you're solving problems in under 5 minutes, increase difficulty. If taking over 40 minutes, drop down a level.

## Next Actions

1. **Today**: Read through all patterns, understand the mental models
2. **Tomorrow**: Solve Fibonacci, House Robber, and Climbing Stairs in all languages
3. **This Week**: Complete Phase 1 of the practice protocol
4. **Track Progress**: Keep a spreadsheet of problems solved, time taken, and patterns recognized

The material is dense by design—this is the intellectual challenge you sought. Take your time, but be consistent. **30 minutes of focused practice daily beats 4 hours on weekends.**

What pattern or problem would you like to dive deeper into first?