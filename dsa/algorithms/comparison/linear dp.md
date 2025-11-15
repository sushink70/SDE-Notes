# Linear DP: Building Your Foundation for Top 1% Mastery

Linear Dynamic Programming is where your DP journey truly begins—the fundamental pattern that unlocks a universe of optimization problems. Let's build this understanding from first principles with the rigor and depth worthy of your ambitions.

---

## **I. The Philosophical Core: What IS Linear DP?**

Before code, understand the **mental model**:

**Linear DP** solves problems where:
1. **State space is one-dimensional** (indexed by a single variable, typically position `i`)
2. **Decisions flow in one direction** (left→right, bottom→top)
3. **Optimal substructure exists**: `dp[i]` depends only on previous states `dp[i-1], dp[i-2], ...`

Think of it as **intelligent exhaustive search with memoization**—you're collapsing exponential decision trees into linear time by recognizing overlapping subproblems.

---

## **II. The Canonical Mental Framework**

### **The Five-Question Protocol** (Ask BEFORE coding):

1. **What does `dp[i]` represent?** (Be precise—this is your state definition)
2. **What's the base case?** (Smallest solvable subproblem)
3. **What's the recurrence relation?** (How does `dp[i]` relate to previous states?)
4. **What's the final answer?** (Often `dp[n]`, but not always)
5. **Can I optimize space?** (Most linear DP can use O(1) space—rolling variables)

**Master this framework.** Top 1% engineers don't jump to code—they crystallize the logic first.

---

## **III. The Foundational Problem: Climbing Stairs**

**Problem**: Climb `n` stairs, taking 1 or 2 steps. How many distinct ways?

### **Phase 1: Expert Thinking Process** (Before Code)

```
Q1: What is dp[i]?
    → Number of ways to reach stair i

Q2: Base cases?
    → dp[0] = 1 (one way: stay at ground)
    → dp[1] = 1 (one way: take 1 step)

Q3: Recurrence?
    → To reach stair i, I came from:
      - stair i-1 (take 1 step) → contributes dp[i-1] ways
      - stair i-2 (take 2 steps) → contributes dp[i-2] ways
    → dp[i] = dp[i-1] + dp[i-2]  (Fibonacci!)

Q4: Final answer?
    → dp[n]

Q5: Space optimization?
    → Only need last 2 values → O(1) space
```

**Cognitive principle**: **Chunking**—recognize this is Fibonacci in disguise. Pattern recognition separates good from great.

---

### **Phase 2: Implementation (All Three Languages)**

#### **Python: Clarity First**
```python
def climb_stairs(n: int) -> int:
    """
    Time: O(n), Space: O(1)
    Pattern: Linear DP with rolling variables
    """
    if n <= 1:
        return 1
    
    # Rolling variables (space optimization)
    prev2, prev1 = 1, 1
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1
```

**Python insight**: Use tuple unpacking for clean rolling updates. Avoid list allocation when possible.

---

#### **Rust: Zero-Cost Abstractions**
```rust
pub fn climb_stairs(n: u32) -> u64 {
    // Time: O(n), Space: O(1)
    // Note: u64 to handle large Fibonacci values
    
    if n <= 1 {
        return 1;
    }
    
    let (mut prev2, mut prev1) = (1u64, 1u64);
    
    for _ in 2..=n {
        let current = prev1.checked_add(prev2)
            .expect("Overflow: n too large");
        prev2 = prev1;
        prev1 = current;
    }
    
    prev1
}
```

**Rust insight**: 
- Use `checked_add` for safety (no silent overflow)
- Explicit type annotations for numeric overflow awareness
- `u64` handles up to ~93 stairs before overflow

---

#### **Go: Simplicity and Performance**
```go
func climbStairs(n int) int {
    // Time: O(n), Space: O(1)
    
    if n <= 1 {
        return 1
    }
    
    prev2, prev1 := 1, 1
    
    for i := 2; i <= n; i++ {
        current := prev1 + prev2
        prev2, prev1 = prev1, current
    }
    
    return prev1
}
```

**Go insight**: Parallel assignment keeps it clean. Go's `int` is platform-dependent (32/64-bit)—use `int64` if guaranteed large values.

---

## **IV. The Progression: Three Levels of Mastery**

### **Level 1: House Robber** (Constraint Handling)

**Problem**: Rob houses in a line, can't rob adjacent. Maximize loot.

**New complexity**: Decision at each house (rob vs skip)

```python
def rob(nums: list[int]) -> int:
    """
    dp[i] = max money robbing houses 0..i
    Recurrence: dp[i] = max(dp[i-1], nums[i] + dp[i-2])
                        (skip i    , rob i + skip i-1)
    """
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    prev2, prev1 = 0, nums[0]
    
    for i in range(1, len(nums)):
        current = max(prev1, nums[i] + prev2)
        prev2, prev1 = prev1, current
    
    return prev1
```

**Mental model shift**: DP doesn't always "accumulate"—sometimes it's about **choosing the best path**.

---

### **Level 2: Longest Increasing Subsequence (LIS)** (Classic)

**Problem**: Find length of longest strictly increasing subsequence.

**Array**: `[10, 9, 2, 5, 3, 7, 101, 18]` → Answer: `4` ([2,3,7,101])

#### **Approach 1: O(n²) DP** (Foundation)
```rust
pub fn length_of_lis(nums: Vec<i32>) -> usize {
    let n = nums.len();
    if n == 0 { return 0; }
    
    // dp[i] = length of LIS ending at index i
    let mut dp = vec![1; n];
    let mut max_len = 1;
    
    for i in 1..n {
        for j in 0..i {
            if nums[j] < nums[i] {
                dp[i] = dp[i].max(dp[j] + 1);
            }
        }
        max_len = max_len.max(dp[i]);
    }
    
    max_len
}
```

**Key insight**: `dp[i]` is **local** (ending at `i`), answer is **global** (`max(dp)`).

---

#### **Approach 2: O(n log n) with Binary Search** (Top 1% Knowledge)
```python
from bisect import bisect_left

def length_of_lis(nums: list[int]) -> int:
    """
    Patience sorting approach
    tails[i] = smallest tail of all increasing subsequences of length i+1
    """
    tails = []
    
    for num in nums:
        pos = bisect_left(tails, num)  # Find insertion point
        if pos == len(tails):
            tails.append(num)  # Extend longest sequence
        else:
            tails[pos] = num  # Replace to keep tail minimal
    
    return len(tails)
```

**Profound insight**: This maintains an **implicit DP structure** via binary search. Understanding WHY this works separates competent from exceptional.

**Why it works**: `tails` is always sorted. Replacing `tails[pos]` with a smaller value creates MORE opportunities for future extensions.

---

### **Level 3: Best Time to Buy/Sell Stock with Cooldown** (State Machine DP)

**Problem**: Buy/sell stock once per day, after selling must cooldown 1 day. Maximize profit.

**This is where Linear DP becomes multidimensional thinking:**

```go
func maxProfit(prices []int) int {
    n := len(prices)
    if n <= 1 {
        return 0
    }
    
    // Three states at day i:
    // hold: max profit while holding stock
    // sold: max profit after selling today
    // rest: max profit while resting (not holding)
    
    hold := -prices[0]  // Buy on day 0
    sold := 0
    rest := 0
    
    for i := 1; i < n; i++ {
        prevHold, prevSold, prevRest := hold, sold, rest
        
        hold = max(prevHold, prevRest - prices[i])  // Keep holding or buy today
        sold = prevHold + prices[i]                  // Sell today
        rest = max(prevRest, prevSold)               // Rest (or cooldown from sell)
        
        // Note: prevSold not used in hold → cooldown enforced
    }
    
    return max(sold, rest)  // Can't end while holding
}

func max(a, b int) int {
    if a > b { return a }
    return b
}
```

**Advanced pattern**: **State machine DP**—track multiple states simultaneously, transitions encode constraints.

---

## **V. Meta-Learning Strategies for Top 1% Mastery**

### **1. The Pattern Library** (Build Your Mental Database)
Create a **personal taxonomy** of DP patterns:
- **Accumulation**: (Climbing Stairs, Fibonacci)
- **Decision**: (House Robber, 0/1 Knapsack)
- **Optimal ending point**: (LIS, Maximum Subarray)
- **State machines**: (Stock problems, Paint House)

**Cognitive science**: **Deliberate practice** requires **immediate feedback**. After solving, ask:
- "What pattern was this?"
- "What was my mistake in initial approach?"
- "How would I recognize this pattern instantly next time?"

---

### **2. The Complexity Ladder**
For EVERY problem, train this reflex:
1. **Brute force**: What's the naive exponential solution?
2. **Memoization (Top-Down DP)**: Cache recursive calls
3. **Tabulation (Bottom-Up DP)**: Iterative with array
4. **Space optimization**: Rolling variables
5. **Mathematical insight**: Can DP be avoided entirely? (e.g., Kadane's for max subarray)

**Example: Fibonacci**
- Brute: O(2ⁿ) recursion
- Memo: O(n) time, O(n) space
- Tabulation: O(n) time, O(n) space
- Optimized: O(n) time, O(1) space
- Matrix exponentiation: O(log n) time

---

### **3. The Visualization Discipline**
For complex problems, **draw the DP table**. Trace transitions manually for small inputs.

**Example: House Robber with `[2,7,9,3,1]`**
```
Index:  0   1   2   3   4
Nums:   2   7   9   3   1
dp:     2   7  11  11  12
        ↑   ↑   ↑
     rob 0  skip rob+0 vs skip
```

**Flow state trigger**: Visualization moves problem-solving from "verbal/symbolic" to "spatial" brain regions—more intuitive for many.

---

## **VI. Your Training Regimen**

### **Week 1-2: Core Patterns** (10 problems minimum)
1. Climbing Stairs (basic recurrence)
2. Min Cost Climbing Stairs (cost variation)
3. House Robber (decision DP)
4. House Robber II (circular constraint)
5. Maximum Subarray (Kadane's algorithm)
6. Longest Increasing Subsequence (both O(n²) and O(n log n))
7. Decode Ways (counting variations)
8. Unique Paths (2D coordinates, but 1D DP)
9. Jump Game (reachability)
10. Best Time to Buy/Sell Stock (all variations)

### **Deliberate Practice Protocol**:
1. **Solve without looking** (even if takes 2 hours)
2. **Write all three language versions**
3. **Optimize space** (always attempt)
4. **Explain to yourself verbally** (Feynman technique)
5. **Review after 1 day, 1 week** (spaced repetition)

---

## **VII. The Psychological Edge**

**Flow triggers for DP mastery**:
1. **Clear goals**: Define state/recurrence before coding
2. **Immediate feedback**: Run on examples IMMEDIATELY
3. **Challenge-skill balance**: If too easy, solve in O(1) space or O(n log n)

**Monk mindset**: Linear DP is meditation. Each problem is one breath. The pattern recognition will come not through force, but through **calm, repeated exposure**.

---

## **Final Wisdom**

Linear DP is not about memorizing solutions—it's about **internalizing the thinking process**:

> "When you see a problem, your mind should automatically ask: *What does dp[i] represent? What's the recurrence?* This should be as natural as breathing."

You're not learning problems. You're **rewiring your pattern recognition**. 

The top 1% don't solve faster—they **recognize patterns instantly** and know which tool fits the problem.

---

**Your first challenge**: Solve **House Robber** in all three languages with O(1) space, then come back and explain YOUR thought process. I'll give you feedback that sharpens your intuition.

You're building something profound here. Stay disciplined. 🔥