# Fibonacci Memoization Simulation Table: `fib_memo(5)`

## Call Trace Table

| Step | Call | Depth | Action | Memo State | Return Value | Notes |
|------|------|-------|--------|------------|--------------|-------|
| 1 | `fib(5)` | 0 | Check memo → miss | `{}` | pending | Start: need fib(5) |
| 2 | `fib(4)` | 1 | Check memo → miss | `{}` | pending | Recursive call from fib(5) |
| 3 | `fib(3)` | 2 | Check memo → miss | `{}` | pending | Recursive call from fib(4) |
| 4 | `fib(2)` | 3 | Check memo → miss | `{}` | pending | Recursive call from fib(3) |
| 5 | `fib(1)` | 4 | Base case | `{}` | **1** | First return! |
| 6 | `fib(0)` | 4 | Base case | `{}` | **0** | Second base case |
| 7 | `fib(2)` | 3 | Compute & store | `{2: 1}` | **1** | 1 + 0 = 1 |
| 8 | `fib(1)` | 3 | Base case | `{2: 1}` | **1** | No recursion needed |
| 9 | `fib(3)` | 2 | Compute & store | `{2: 1, 3: 2}` | **2** | 1 + 1 = 2 |
| 10 | `fib(2)` | 2 | Check memo → **HIT** | `{2: 1, 3: 2}` | **1** | 🎯 Cache hit! |
| 11 | `fib(4)` | 1 | Compute & store | `{2: 1, 3: 2, 4: 3}` | **3** | 2 + 1 = 3 |
| 12 | `fib(3)` | 1 | Check memo → **HIT** | `{2: 1, 3: 2, 4: 3}` | **2** | 🎯 Cache hit! |
| 13 | `fib(5)` | 0 | Compute & store | `{2: 1, 3: 2, 4: 3, 5: 5}` | **5** | 3 + 2 = 5 |

---

## Recursion Tree Visualization

```
                    fib(5)
                   /      \
              fib(4)      fib(3) [CACHED]
             /      \
        fib(3)      fib(2) [CACHED]
       /      \
   fib(2)    fib(1)
   /    \
fib(1) fib(0)
```

**Key Insight**: Without memoization, fib(3) would be computed TWICE, fib(2) THREE times, etc.
With memoization: each subproblem computed exactly ONCE.

---

## Cache Evolution Timeline

| After Call | Memo Dictionary |
|------------|-----------------|
| `fib(1)` | `{}` (base case doesn't cache) |
| `fib(0)` | `{}` |
| `fib(2)` | `{2: 1}` |
| `fib(3)` | `{2: 1, 3: 2}` |
| `fib(2)` cached | `{2: 1, 3: 2}` (no change - cache hit) |
| `fib(4)` | `{2: 1, 3: 2, 4: 3}` |
| `fib(3)` cached | `{2: 1, 3: 2, 4: 3}` (no change - cache hit) |
| `fib(5)` | `{2: 1, 3: 2, 4: 3, 5: 5}` |

---

## Performance Metrics

| Metric | Without Memo | With Memo |
|--------|--------------|-----------|
| **Function Calls** | 15 calls | 9 calls |
| **Unique Computations** | 15 | 5 (fib(2) through fib(5), plus base cases) |
| **Time Complexity** | O(2^n) | O(n) |
| **Space Complexity** | O(n) stack | O(n) memo + O(n) stack |

**Speedup Factor**: For fib(5): 15/9 = 1.67x faster
For fib(40): 331,160,281 vs 79 calls = **4.2 million times faster!**

# Top-Down Dynamic Programming: Mental Model & Framework

## 🎯 The Core Mental Model: "Ask Before You Compute"

### The Top-Down DP Mindset

```
                     ┌─────────────────┐
                     │  Problem P(n)   │
                     └────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Have I solved   │
                    │   this EXACT      │
                    │   problem before? │
                    └─────┬─────────┬───┘
                          │         │
                     YES  │         │  NO
                    ┌─────▼──┐  ┌───▼──────┐
                    │ Return │  │  Solve   │
                    │ cached │  │  it now  │
                    │ result │  │  & cache │
                    └────────┘  └──────────┘
```

**Key Principle**: "Lazy evaluation with perfect memory"
- Don't compute until needed (lazy)
- Never compute the same thing twice (memoization)

---

## 📋 Universal 5-Step Framework for ANY DP Problem

### Step 1: Define the State
**Question**: What information uniquely identifies a subproblem?

For Fibonacci: `n` (the position in sequence)

**Mental Exercise**: Can I distinguish one subproblem from another using just these parameters?

---

### Step 2: Identify Base Cases
**Question**: What are the simplest inputs I can answer without recursion?

For Fibonacci:
- `fib(0) = 0` 
- `fib(1) = 1`

**Mental Model**: These are your "axioms"—self-evident truths that need no proof.

---

### Step 3: Find the Recurrence Relation
**Question**: How can I express the solution using smaller subproblems?

For Fibonacci: `fib(n) = fib(n-1) + fib(n-2)`

**Critical Insight**: This is where the "dynamic" in Dynamic Programming comes from—
the solution to a larger problem DEPENDS ON solutions to smaller problems.

---

### Step 4: Determine Computation Order
**Question**: In what order should I solve subproblems to ensure dependencies are met?

**Top-Down (Memoization)**: Let recursion handle the order naturally
**Bottom-Up (Tabulation)**: Solve from smallest to largest explicitly

---

### Step 5: Optimize Space (Advanced)
**Question**: Do I need to store ALL previous results, or just a sliding window?

For Fibonacci: We only need the last TWO values, not all previous ones.

---

## 🎓 How to Create Simulation Tables for ANY Problem

### Template Structure

```
| Step | Call Stack | Input | Check Cache | Computation | Cache Update | Return |
|------|-----------|-------|-------------|-------------|--------------|--------|
```

### The Systematic Process

1. **Start with the initial call** (Step 1, Depth 0)
2. **Follow the execution path**:
   - Check if base case → return immediately
   - Check cache → return if hit
   - Make recursive calls → increase depth
   - Compute result when recursion returns
   - Update cache
   - Return value

3. **Track cache state changes** after each memoization
4. **Mark cache hits** prominently (these show the benefit!)
5. **Count total calls vs unique computations**

---

## 🔬 Cognitive Training Strategies

### 1. **Chunking Pattern Recognition**
Train yourself to recognize these patterns instantly:

- **Linear Recurrence**: `f(n) = f(n-1) + f(n-2)` → Fibonacci-style
- **Choice Pattern**: `max(f(n-1), f(n-2))` → Optimization problems
- **Multi-dimensional**: `f(i, j) = f(i-1, j) + f(i, j-1)` → Grid problems

**Practice**: Spend 10 minutes daily identifying recurrence patterns in new problems.

---

### 2. **Deliberate Practice Protocol**

```
Week 1-2: Master 1D DP (Fibonacci, Climbing Stairs, House Robber)
Week 3-4: 2D DP (Unique Paths, Longest Common Subsequence)
Week 5-6: State Machine DP (Buy/Sell Stock variations)
Week 7-8: Complex State DP (Knapsack, Subset Sum)
```

**Spaced Repetition**: Revisit problems at increasing intervals (1 day, 3 days, 1 week, 1 month).

---

### 3. **Meta-Learning: Learn How You Learn**

After solving each problem, document:
- **What pattern did I recognize?**
- **What mistake did I make initially?**
- **What was the "aha" moment?**
- **How would I explain this to my past self?**

**Psychological Principle**: Reflection enhances encoding and retrieval.

---

### 4. **The "Why Before How" Principle**

Before coding, answer:
1. **Why** does this problem have overlapping subproblems?
2. **Why** does the recurrence relation work?
3. **Why** is this better than the naive approach?

**Cognitive Benefit**: Understanding WHY builds mental models that transfer to new problems.

---

## 🚀 Tips, Tricks & Shortcuts

### Shortcut #1: The "Two Questions" Test
Can you answer YES to both?
1. **Optimal Substructure**: Can I build the solution from smaller solutions?
2. **Overlapping Subproblems**: Do I solve the same subproblem multiple times?

If YES → DP is applicable.

---

### Shortcut #2: State Space Estimation
Estimate time/space complexity BEFORE coding:
- **Number of unique states** = Size of memo dictionary
- **Time per state** = Work done per recursive call (excluding further recursion)
- **Total Time** = (Number of states) × (Time per state)

For Fibonacci: n states × O(1) work = O(n)

---

### Shortcut #3: Draw the Recursion Tree First
**Always** sketch the recursion tree for small inputs (n=3, n=4).
This reveals:
- Overlapping subproblems (nodes appearing multiple times)
- Base cases (leaf nodes)
- Cache hit opportunities

---

### Shortcut #4: Cache Key Design
Your cache key should be a tuple of ALL parameters that affect the result:

```python
# Single parameter
memo[n] = result

# Multiple parameters  
memo[(i, j, k)] = result

# Mutable state? Convert to immutable
memo[tuple(arr)] = result  # NOT memo[arr]
```

---

## 🧘 The Monk's Approach to Mastery

### Daily Practice Ritual (30-45 minutes)

1. **Warm-up (5 min)**: Review yesterday's problem WITHOUT code
2. **Deep Work (25 min)**: Solve one new problem, simulate it on paper first
3. **Reflection (10 min)**: Write in your "Pattern Journal"
4. **Spaced Review (5 min)**: Solve one problem from 1 week ago

### Weekly Review
- Identify 3 patterns you've mastered
- Identify 1 pattern that still confuses you
- Teach one concept to someone (even an imaginary student)

**Flow State Trigger**: Start with a problem slightly above your comfort zone.

---

## 🎯 Progression Checklist

- [ ] Can I trace execution without running code?
- [ ] Can I predict which calls will hit the cache?
- [ ] Can I estimate time/space complexity before coding?
- [ ] Can I spot DP opportunities in problem descriptions?
- [ ] Can I convert top-down to bottom-up (and vice versa)?
- [ ] Can I optimize space complexity?
- [ ] Can I explain the pattern to a beginner?

**When you check all boxes** → You're in the top 10%.
**When you can do this across 50+ problems** → Top 1%.

# ============================================================================
# PYTHON IMPLEMENTATION - Idiomatic & Multiple Approaches
# ============================================================================

from functools import lru_cache
from typing import Dict

# ---------------------- Approach 1: Manual Memoization ----------------------
def fib_memo_manual(n: int, memo: Dict[int, int] = None) -> int:
    """
    Manual memoization with explicit cache management.
    
    Time: O(n) - each value computed once
    Space: O(n) - memo dict + O(n) recursion stack = O(n)
    
    Use when: You need fine-grained control over cache behavior
    """
    if memo is None:
        memo = {}
    
    # Base cases
    if n <= 1:
        return n
    
    # Check cache
    if n in memo:
        return memo[n]
    
    # Compute and cache
    memo[n] = fib_memo_manual(n - 1, memo) + fib_memo_manual(n - 2, memo)
    return memo[n]


# ---------------------- Approach 2: @lru_cache Decorator ----------------------
@lru_cache(maxsize=None)  # maxsize=None → unlimited cache
def fib_lru(n: int) -> int:
    """
    Pythonic memoization using built-in decorator.
    
    Time: O(n)
    Space: O(n)
    
    Use when: You want clean, production-ready code
    Benefit: Thread-safe, cache statistics, automatic cleanup
    """
    if n <= 1:
        return n
    return fib_lru(n - 1) + fib_lru(n - 2)


# ---------------------- Approach 3: Bottom-Up (Optimal) ----------------------
def fib_dp(n: int) -> int:
    """
    Bottom-up DP with O(1) space optimization.
    
    Time: O(n) - single pass
    Space: O(1) - only two variables
    
    Use when: Space efficiency is critical (embedded systems, etc.)
    """
    if n <= 1:
        return n
    
    # Only need last two values
    prev2, prev1 = 0, 1
    
    for _ in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1


# ---------------------- Testing & Benchmarking ----------------------
if __name__ == "__main__":
    import time
    
    def benchmark(func, n: int, name: str):
        start = time.perf_counter()
        result = func(n)
        elapsed = time.perf_counter() - start
        print(f"{name:20} | n={n:2} | result={result:8} | time={elapsed*1e6:8.2f}μs")
        return result
    
    print("=" * 70)
    print("FIBONACCI MEMOIZATION BENCHMARK")
    print("=" * 70)
    
    for n in [10, 20, 30, 100]:
        print(f"\n--- Testing with n={n} ---")
        benchmark(fib_memo_manual, n, "Manual Memo")
        benchmark(fib_lru, n, "@lru_cache")
        benchmark(fib_dp, n, "Bottom-Up O(1)")
    
    # Cache statistics
    print("\n--- Cache Statistics ---")
    print(fib_lru.cache_info())
    
    # Manual simulation for teaching
    print("\n--- Manual Trace for n=5 ---")
    memo = {}
    
    def fib_trace(n: int, memo: dict, depth: int = 0) -> int:
        indent = "  " * depth
        print(f"{indent}→ fib({n})")
        
        if n <= 1:
            print(f"{indent}← base case: {n}")
            return n
        
        if n in memo:
            print(f"{indent}← cached: {memo[n]}")
            return memo[n]
        
        result = fib_trace(n - 1, memo, depth + 1) + fib_trace(n - 2, memo, depth + 1)
        memo[n] = result
        print(f"{indent}← computed: {result}, memo={memo}")
        return result
    
    fib_trace(5, memo)

// ============================================================================
// RUST IMPLEMENTATION - Zero-Cost Abstractions & Memory Safety
// ============================================================================

use std::collections::HashMap;
use std::time::Instant;

// ---------------------- Approach 1: Memoization with HashMap ----------------------
fn fib_memo(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    /*
    Top-down DP with explicit memoization.
    
    Time: O(n)
    Space: O(n) - HashMap + recursion stack
    
    Rust Idioms:
    - Pass memo as mutable reference (&mut) for zero-copy semantics
    - Use u64 for unsigned integers (Fibonacci values grow fast)
    - Entry API for efficient cache insertion
    */
    
    // Base cases
    if n <= 1 {
        return n;
    }
    
    // Check cache - Rust's entry API is optimal here
    if let Some(&cached) = memo.get(&n) {
        return cached;
    }
    
    // Compute recursively
    let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
    
    // Insert into cache
    memo.insert(n, result);
    
    result
}

// ---------------------- Approach 2: Bottom-Up (Space Optimized) ----------------------
fn fib_dp(n: u64) -> u64 {
    /*
    Bottom-up DP with O(1) space.
    
    Time: O(n)
    Space: O(1)
    
    Rust Advantage: Compiler optimizes this to register-only code
    */
    
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

// ---------------------- Approach 3: Wrapper with Internal State ----------------------
struct FibMemo {
    cache: HashMap<u64, u64>,
}

impl FibMemo {
    /*
    Object-oriented approach with persistent cache.
    Useful when computing multiple Fibonacci numbers.
    */
    
    fn new() -> Self {
        Self {
            cache: HashMap::new(),
        }
    }
    
    fn compute(&mut self, n: u64) -> u64 {
        if n <= 1 {
            return n;
        }
        
        // Rust's entry API - efficient upsert pattern
        *self.cache.entry(n).or_insert_with(|| {
            self.compute(n - 1) + self.compute(n - 2)
        })
    }
    
    fn cache_size(&self) -> usize {
        self.cache.len()
    }
}

// ---------------------- Approach 4: Iterative with Vector ----------------------
fn fib_vec(n: usize) -> u64 {
    /*
    Using Vec<u64> for cache - better cache locality than HashMap.
    
    Time: O(n)
    Space: O(n)
    
    Trade-off: Faster access but wastes space for sparse inputs
    */
    
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

// ---------------------- Testing & Benchmarking ----------------------
fn main() {
    println!("{}", "=".repeat(70));
    println!("RUST FIBONACCI MEMOIZATION");
    println!("{}", "=".repeat(70));
    
    // Test values
    let test_cases = vec![10, 20, 30, 50];
    
    for &n in &test_cases {
        println!("\n--- n = {} ---", n);
        
        // Approach 1: HashMap memoization
        let mut memo = HashMap::new();
        let start = Instant::now();
        let result1 = fib_memo(n, &mut memo);
        let elapsed1 = start.elapsed();
        println!("HashMap Memo  : {} (cache: {}) - {:?}", 
                 result1, memo.len(), elapsed1);
        
        // Approach 2: Bottom-up
        let start = Instant::now();
        let result2 = fib_dp(n);
        let elapsed2 = start.elapsed();
        println!("Bottom-Up O(1): {} - {:?}", result2, elapsed2);
        
        // Approach 3: Struct wrapper
        let mut fib_struct = FibMemo::new();
        let start = Instant::now();
        let result3 = fib_struct.compute(n);
        let elapsed3 = start.elapsed();
        println!("Struct Wrapper: {} (cache: {}) - {:?}", 
                 result3, fib_struct.cache_size(), elapsed3);
        
        // Approach 4: Vector DP
        let start = Instant::now();
        let result4 = fib_vec(n as usize);
        let elapsed4 = start.elapsed();
        println!("Vector DP     : {} - {:?}", result4, elapsed4);
    }
    
    // Trace execution for teaching
    println!("\n{}", "=".repeat(70));
    println!("EXECUTION TRACE FOR n=5");
    println!("{}", "=".repeat(70));
    
    fn fib_trace(n: u64, memo: &mut HashMap<u64, u64>, depth: usize) -> u64 {
        let indent = "  ".repeat(depth);
        println!("{}→ fib({})", indent, n);
        
        if n <= 1 {
            println!("{}← base case: {}", indent, n);
            return n;
        }
        
        if let Some(&cached) = memo.get(&n) {
            println!("{}← cached: {}", indent, cached);
            return cached;
        }
        
        let result = fib_trace(n - 1, memo, depth + 1) + 
                     fib_trace(n - 2, memo, depth + 1);
        memo.insert(n, result);
        println!("{}← computed: {}, memo size: {}", indent, result, memo.len());
        
        result
    }
    
    let mut trace_memo = HashMap::new();
    fib_trace(5, &mut trace_memo, 0);
    
    // Memory efficiency comparison
    println!("\n{}", "=".repeat(70));
    println!("MEMORY ANALYSIS");
    println!("{}", "=".repeat(70));
    println!("HashMap:  {} bytes per entry (approx)", 
             std::mem::size_of::<(u64, u64)>() + 24); // hash overhead
    println!("Vec:      {} bytes per entry", std::mem::size_of::<u64>());
    println!("Variables: {} bytes total", std::mem::size_of::<(u64, u64)>());
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_fibonacci_consistency() {
        let test_values = vec![0, 1, 2, 3, 5, 8, 10];
        
        for &n in &test_values {
            let mut memo = HashMap::new();
            let result1 = fib_memo(n, &mut memo);
            let result2 = fib_dp(n);
            let result3 = fib_vec(n as usize);
            
            assert_eq!(result1, result2);
            assert_eq!(result2, result3);
        }
    }
    
    #[test]
    fn test_known_values() {
        let expected = vec![0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
        
        for (n, &expected_val) in expected.iter().enumerate() {
            let mut memo = HashMap::new();
            assert_eq!(fib_memo(n as u64, &mut memo), expected_val);
        }
    }
}

// ============================================================================
// GO IMPLEMENTATION - Simplicity, Concurrency & Performance
// ============================================================================

package main

import (
	"fmt"
	"sync"
	"time"
)

// ---------------------- Approach 1: Map-based Memoization ----------------------
func fibMemo(n int, memo map[int]int) int {
	/*
		Top-down DP with explicit memoization.
		
		Time: O(n)
		Space: O(n) - map + recursion stack
		
		Go Idioms:
		- Pass map by reference (maps are reference types)
		- Use int for simplicity (int64 for larger values)
	*/
	
	// Base cases
	if n <= 1 {
		return n
	}
	
	// Check cache
	if val, exists := memo[n]; exists {
		return val
	}
	
	// Compute and cache
	result := fibMemo(n-1, memo) + fibMemo(n-2, memo)
	memo[n] = result
	
	return result
}

// ---------------------- Approach 2: Struct with Method ----------------------
type FibMemoizer struct {
	cache map[int]int
	mu    sync.RWMutex // For thread-safe access
}

func NewFibMemoizer() *FibMemoizer {
	/*
		Object-oriented approach with thread safety.
		Useful for concurrent computations.
	*/
	return &FibMemoizer{
		cache: make(map[int]int),
	}
}

func (f *FibMemoizer) Compute(n int) int {
	if n <= 1 {
		return n
	}
	
	// Read lock for checking cache
	f.mu.RLock()
	if val, exists := f.cache[n]; exists {
		f.mu.RUnlock()
		return val
	}
	f.mu.RUnlock()
	
	// Compute recursively
	result := f.Compute(n-1) + f.Compute(n-2)
	
	// Write lock for updating cache
	f.mu.Lock()
	f.cache[n] = result
	f.mu.Unlock()
	
	return result
}

func (f *FibMemoizer) CacheSize() int {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return len(f.cache)
}

// ---------------------- Approach 3: Bottom-Up (Space Optimized) ----------------------
func fibDP(n int) int {
	/*
		Bottom-up DP with O(1) space.
		
		Time: O(n)
		Space: O(1)
		
		Most efficient for single computations.
	*/
	
	if n <= 1 {
		return n
	}
	
	prev2, prev1 := 0, 1
	
	for i := 2; i <= n; i++ {
		current := prev1 + prev2
		prev2, prev1 = prev1, current
	}
	
	return prev1
}

// ---------------------- Approach 4: Slice-based DP ----------------------
func fibSlice(n int) int {
	/*
		Using slice for cache - better locality than map.
		
		Time: O(n)
		Space: O(n)
		
		Trade-off: Fast access, but allocates contiguous memory.
	*/
	
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

// ---------------------- Approach 5: Concurrent Computation ----------------------
func fibConcurrent(numbers []int) []int {
	/*
		Compute multiple Fibonacci numbers concurrently.
		Demonstrates Go's strength in concurrent programming.
	*/
	
	type result struct {
		index int
		value int
	}
	
	results := make(chan result, len(numbers))
	var wg sync.WaitGroup
	
	// Shared memoizer for all goroutines
	memoizer := NewFibMemoizer()
	
	// Launch goroutines
	for i, n := range numbers {
		wg.Add(1)
		go func(idx, num int) {
			defer wg.Done()
			results <- result{idx, memoizer.Compute(num)}
		}(i, n)
	}
	
	// Close results channel when all goroutines finish
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect results in order
	output := make([]int, len(numbers))
	for r := range results {
		output[r.index] = r.value
	}
	
	return output
}

// ---------------------- Execution Trace for Teaching ----------------------
func fibTrace(n int, memo map[int]int, depth int) int {
	indent := ""
	for i := 0; i < depth; i++ {
		indent += "  "
	}
	
	fmt.Printf("%s→ fib(%d)\n", indent, n)
	
	if n <= 1 {
		fmt.Printf("%s← base case: %d\n", indent, n)
		return n
	}
	
	if val, exists := memo[n]; exists {
		fmt.Printf("%s← cached: %d\n", indent, val)
		return val
	}
	
	result := fibTrace(n-1, memo, depth+1) + fibTrace(n-2, memo, depth+1)
	memo[n] = result
	fmt.Printf("%s← computed: %d, memo size: %d\n", indent, result, len(memo))
	
	return result
}

// ---------------------- Benchmarking ----------------------
func benchmark(name string, f func() int) time.Duration {
	start := time.Now()
	result := f()
	elapsed := time.Since(start)
	fmt.Printf("%-20s | result: %10d | time: %10v\n", name, result, elapsed)
	return elapsed
}

func main() {
	fmt.Println(strings("=", 70))
	fmt.Println("GO FIBONACCI MEMOIZATION")
	fmt.Println(strings("=", 70))
	
	testCases := []int{10, 20, 30, 40}
	
	for _, n := range testCases {
		fmt.Printf("\n--- n = %d ---\n", n)
		
		// Approach 1: Map memoization
		memo1 := make(map[int]int)
		benchmark("Map Memo", func() int {
			return fibMemo(n, memo1)
		})
		
		// Approach 2: Struct memoizer
		memoizer := NewFibMemoizer()
		benchmark("Struct Memo", func() int {
			return memoizer.Compute(n)
		})
		fmt.Printf("                      cache size: %d\n", memoizer.CacheSize())
		
		// Approach 3: Bottom-up
		benchmark("Bottom-Up O(1)", func() int {
			return fibDP(n)
		})
		
		// Approach 4: Slice-based
		benchmark("Slice DP", func() int {
			return fibSlice(n)
		})
	}
	
	// Concurrent computation demo
	fmt.Println("\n" + strings("=", 70))
	fmt.Println("CONCURRENT COMPUTATION")
	fmt.Println(strings("=", 70))
	
	numbers := []int{30, 31, 32, 33, 34, 35}
	start := time.Now()
	results := fibConcurrent(numbers)
	elapsed := time.Since(start)
	
	fmt.Printf("Computed fib(%v)\n", numbers)
	fmt.Printf("Results: %v\n", results)
	fmt.Printf("Total time: %v (with concurrency)\n", elapsed)
	
	// Execution trace
	fmt.Println("\n" + strings("=", 70))
	fmt.Println("EXECUTION TRACE FOR n=5")
	fmt.Println(strings("=", 70))
	
	traceMemo := make(map[int]int)
	fibTrace(5, traceMemo, 0)
	
	// Memory comparison
	fmt.Println("\n" + strings("=", 70))
	fmt.Println("MEMORY ANALYSIS")
	fmt.Println(strings("=", 70))
	fmt.Printf("Map entry:    ~%d bytes (key + value + overhead)\n", 16+8) // approx
	fmt.Printf("Slice entry:  %d bytes\n", 8)
	fmt.Printf("Variables:    %d bytes\n", 16) // two ints
}

// Helper function to repeat strings
func strings(s string, count int) string {
	result := ""
	for i := 0; i < count; i++ {
		result += s
	}
	return result
}

// ---------------------- Tests ----------------------
func testFibonacci() {
	fmt.Println("\n" + strings("=", 70))
	fmt.Println("RUNNING TESTS")
	fmt.Println(strings("=", 70))
	
	expected := []int{0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55}
	
	for n, expectedVal := range expected {
		memo := make(map[int]int)
		result1 := fibMemo(n, memo)
		result2 := fibDP(n)
		result3 := fibSlice(n)
		
		if result1 != expectedVal || result2 != expectedVal || result3 != expectedVal {
			fmt.Printf("❌ FAIL: fib(%d) expected %d, got %d, %d, %d\n",
				n, expectedVal, result1, result2, result3)
		} else {
			fmt.Printf("✓ PASS: fib(%d) = %d\n", n, expectedVal)
		}
	}
}

// ============================================================================
// C++ IMPLEMENTATION - Performance, Templates & Modern C++17/20
// ============================================================================

#include <iostream>
#include <unordered_map>
#include <vector>
#include <chrono>
#include <iomanip>
#include <string>
#include <functional>

using namespace std;
using namespace std::chrono;

// ---------------------- Approach 1: Map-based Memoization ----------------------
long long fibMemo(int n, unordered_map<int, long long>& memo) {
    /*
        Top-down DP with unordered_map.
        
        Time: O(n)
        Space: O(n)
        
        C++ Idioms:
        - Pass map by reference to avoid copies
        - Use long long for overflow safety
        - unordered_map for O(1) average lookup
    */
    
    // Base cases
    if (n <= 1) return n;
    
    // Check cache - C++20 style with structured binding
    auto it = memo.find(n);
    if (it != memo.end()) {
        return it->second;
    }
    
    // Compute and cache
    long long result = fibMemo(n - 1, memo) + fibMemo(n - 2, memo);
    memo[n] = result;
    
    return result;
}

// ---------------------- Approach 2: Class-based Memoizer ----------------------
class FibMemoizer {
private:
    unordered_map<int, long long> cache;
    
public:
    FibMemoizer() = default;
    
    long long compute(int n) {
        /*
            Object-oriented approach with persistent cache.
            Useful for multiple computations.
        */
        
        if (n <= 1) return n;
        
        // Try to find in cache
        auto it = cache.find(n);
        if (it != cache.end()) {
            return it->second;
        }
        
        // Compute recursively
        long long result = compute(n - 1) + compute(n - 2);
        cache[n] = result;
        
        return result;
    }
    
    size_t cacheSize() const {
        return cache.size();
    }
    
    void clear() {
        cache.clear();
    }
};

// ---------------------- Approach 3: Bottom-Up (Space Optimized) ----------------------
long long fibDP(int n) {
    /*
        Bottom-up DP with O(1) space.
        
        Time: O(n)
        Space: O(1)
        
        Compiler optimizations: likely uses only registers
    */
    
    if (n <= 1) return n;
    
    long long prev2 = 0, prev1 = 1;
    
    for (int i = 2; i <= n; ++i) {
        long long current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }
    
    return prev1;
}

// ---------------------- Approach 4: Vector-based DP ----------------------
long long fibVector(int n) {
    /*
        Using vector for cache - excellent cache locality.
        
        Time: O(n)
        Space: O(n)
        
        Performance: Often faster than map due to contiguous memory
    */
    
    if (n <= 1) return n;
    
    vector<long long> dp(n + 1);
    dp[0] = 0;
    dp[1] = 1;
    
    for (int i = 2; i <= n; ++i) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    return dp[n];
}

// ---------------------- Approach 5: Template Metaprogramming ----------------------
// Compile-time Fibonacci (just for demonstration)
template<int N>
struct FibCompileTime {
    static constexpr long long value = 
        FibCompileTime<N-1>::value + FibCompileTime<N-2>::value;
};

template<>
struct FibCompileTime<0> {
    static constexpr long long value = 0;
};

template<>
struct FibCompileTime<1> {
    static constexpr long long value = 1;
};

// ---------------------- Approach 6: std::function Wrapper ----------------------
class FibFunctional {
private:
    function<long long(int)> fib;
    unordered_map<int, long long> memo;
    
public:
    FibFunctional() {
        // Lambda with memoization
        fib = [this](int n) -> long long {
            if (n <= 1) return n;
            
            if (memo.count(n)) return memo[n];
            
            long long result = fib(n - 1) + fib(n - 2);
            memo[n] = result;
            return result;
        };
    }
    
    long long operator()(int n) {
        return fib(n);
    }
};

// ---------------------- Execution Trace ----------------------
long long fibTrace(int n, unordered_map<int, long long>& memo, int depth = 0) {
    string indent(depth * 2, ' ');
    cout << indent << "→ fib(" << n << ")" << endl;
    
    if (n <= 1) {
        cout << indent << "← base case: " << n << endl;
        return n;
    }
    
    auto it = memo.find(n);
    if (it != memo.end()) {
        cout << indent << "← cached: " << it->second << endl;
        return it->second;
    }
    
    long long result = fibTrace(n - 1, memo, depth + 1) + 
                       fibTrace(n - 2, memo, depth + 1);
    memo[n] = result;
    cout << indent << "← computed: " << result 
         << ", memo size: " << memo.size() << endl;
    
    return result;
}

// ---------------------- Benchmarking Utility ----------------------
template<typename Func>
void benchmark(const string& name, Func func, int n) {
    auto start = high_resolution_clock::now();
    long long result = func(n);
    auto end = high_resolution_clock::now();
    
    auto duration = duration_cast<microseconds>(end - start);
    
    cout << left << setw(20) << name 
         << " | n=" << setw(3) << n
         << " | result=" << setw(12) << result
         << " | time=" << setw(8) << duration.count() << "μs" << endl;
}

// ---------------------- Main Function ----------------------
int main() {
    cout << string(70, '=') << endl;
    cout << "C++ FIBONACCI MEMOIZATION" << endl;
    cout << string(70, '=') << endl;
    
    vector<int> testCases = {10, 20, 30, 40, 45};
    
    for (int n : testCases) {
        cout << "\n--- n = " << n << " ---" << endl;
        
        // Approach 1: Map memoization
        unordered_map<int, long long> memo1;
        benchmark("Map Memo", [&memo1](int x) { 
            return fibMemo(x, memo1); 
        }, n);
        
        // Approach 2: Class memoizer
        FibMemoizer memoizer;
        benchmark("Class Memo", [&memoizer](int x) { 
            return memoizer.compute(x); 
        }, n);
        cout << string(20, ' ') << " cache size: " << memoizer.cacheSize() << endl;
        
        // Approach 3: Bottom-up
        benchmark("Bottom-Up O(1)", fibDP, n);
        
        // Approach 4: Vector DP
        benchmark("Vector DP", fibVector, n);
        
        // Approach 5: Functional style
        FibFunctional fibFunc;
        benchmark("Functional", fibFunc, n);
    }
    
    // Compile-time computation demo
    cout << "\n" << string(70, '=') << endl;
    cout << "COMPILE-TIME COMPUTATION" << endl;
    cout << string(70, '=') << endl;
    cout << "fib(10) at compile time: " << FibCompileTime<10>::value << endl;
    cout << "fib(20) at compile time: " << FibCompileTime<20>::value << endl;
    
    // Execution trace
    cout << "\n" << string(70, '=') << endl;
    cout << "EXECUTION TRACE FOR n=5" << endl;
    cout << string(70, '=') << endl;
    
    unordered_map<int, long long> traceMemo;
    fibTrace(5, traceMemo);
    
    // Memory analysis
    cout << "\n" << string(70, '=') << endl;
    cout << "MEMORY ANALYSIS" << endl;
    cout << string(70, '=') << endl;
    cout << "sizeof(unordered_map<int, long long>): " 
         << sizeof(unordered_map<int, long long>) << " bytes" << endl;
    cout << "sizeof(vector<long long>): " 
         << sizeof(vector<long long>) << " bytes" << endl;
    cout << "sizeof(long long): " 
         << sizeof(long long) << " bytes" << endl;
    cout << "Estimated per-entry overhead (map): ~24-32 bytes" << endl;
    cout << "Estimated per-entry overhead (vector): ~8 bytes" << endl;
    
    // Testing
    cout << "\n" << string(70, '=') << endl;
    cout << "RUNNING TESTS" << endl;
    cout << string(70, '=') << endl;
    
    vector<long long> expected = {0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55};
    bool allPassed = true;
    
    for (size_t n = 0; n < expected.size(); ++n) {
        unordered_map<int, long long> memo;
        long long result1 = fibMemo(n, memo);
        long long result2 = fibDP(n);
        long long result3 = fibVector(n);
        
        if (result1 == expected[n] && result2 == expected[n] && result3 == expected[n]) {
            cout << "✓ PASS: fib(" << n << ") = " << expected[n] << endl;
        } else {
            cout << "✗ FAIL: fib(" << n << ") expected " << expected[n] 
                 << ", got " << result1 << ", " << result2 << ", " << result3 << endl;
            allPassed = false;
        }
    }
    
    cout << "\n" << (allPassed ? "All tests passed! ✓" : "Some tests failed ✗") << endl;
    
    return 0;
}

// ---------------------- Advanced: Matrix Exponentiation ----------------------
// O(log n) solution using matrix exponentiation (bonus)
struct Matrix {
    long long a[2][2];
    
    Matrix(long long a00 = 1, long long a01 = 0, 
           long long a10 = 0, long long a11 = 1) {
        a[0][0] = a00; a[0][1] = a01;
        a[1][0] = a10; a[1][1] = a11;
    }
    
    Matrix operator*(const Matrix& other) const {
        Matrix result;
        result.a[0][0] = a[0][0] * other.a[0][0] + a[0][1] * other.a[1][0];
        result.a[0][1] = a[0][0] * other.a[0][1] + a[0][1] * other.a[1][1];
        result.a[1][0] = a[1][0] * other.a[0][0] + a[1][1] * other.a[1][0];
        result.a[1][1] = a[1][0] * other.a[0][1] + a[1][1] * other.a[1][1];
        return result;
    }
};

Matrix matrixPow(Matrix base, int exp) {
    Matrix result; // identity matrix
    while (exp > 0) {
        if (exp & 1) result = result * base;
        base = base * base;
        exp >>= 1;
    }
    return result;
}

long long fibMatrix(int n) {
    /*
        O(log n) solution using matrix exponentiation.
        [[1,1],[1,0]]^n = [[F(n+1),F(n)],[F(n),F(n-1)]]
        
        Time: O(log n)
        Space: O(1)
    */
    if (n <= 1) return n;
    Matrix base(1, 1, 1, 0);
    Matrix result = matrixPow(base, n - 1);
    return result.a[0][0];
}

# Complete Dynamic Programming Workflow

## 🎯 The Universal Problem-Solving Template

### Phase 1: UNDERSTAND (5-10 minutes)

```
┌─────────────────────────────────────────────┐
│ 1. Read problem 3 times                    │
│ 2. Identify input/output                   │
│ 3. List constraints                        │
│ 4. Work through 2-3 small examples BY HAND │
└─────────────────────────────────────────────┘
```

**Critical Questions:**
- What am I optimizing? (min/max/count)
- What decisions am I making at each step?
- Can I break this into smaller similar problems?

---

### Phase 2: RECOGNIZE PATTERN (5-10 minutes)

```
IS THIS DP?
     ├── Does solution depend on smaller subproblems? ✓
     ├── Do subproblems overlap? ✓
     └── Can I express relation recursively? ✓
             │
             ▼
          IT'S DP!
```

**Pattern Recognition Checklist:**

| Pattern | Keywords | Example |
|---------|----------|---------|
| **Linear DP** | "sequence", "array", "previous" | Fibonacci, Climbing Stairs |
| **2D Grid DP** | "matrix", "path", "grid" | Unique Paths, Min Path Sum |
| **Knapsack** | "capacity", "weight", "value" | 0/1 Knapsack, Subset Sum |
| **LCS/Edit** | "matching", "alignment", "edit" | Longest Common Subsequence |
| **Intervals** | "merge", "non-overlapping" | Interval Scheduling |
| **State Machine** | "states", "transitions" | Buy/Sell Stock |

---

### Phase 3: DEFINE STATE (10-15 minutes)

This is the MOST CRITICAL step. Get this wrong, and everything fails.

```
WHAT INFORMATION UNIQUELY IDENTIFIES A SUBPROBLEM?

Bad State:  "current position"  (too vague)
Good State: "position i in array, sum so far = s"  (precise)
```

**State Design Questions:**
1. What changes as I make decisions?
2. What do I need to know to continue solving?
3. Can I reduce the number of dimensions?

**Example: House Robber**
- Problem: Rob houses, can't rob adjacent
- State: `dp[i]` = max money robbing houses 0 to i
- Why this works: Decision at i only depends on i-1 and i-2

---

### Phase 4: FIND RECURRENCE (10-15 minutes)

```
STEP 1: Base case (trivial inputs)
STEP 2: Recursive case (how to combine subproblems)
STEP 3: Express mathematically
```

**Template:**
```
dp[state] = {
    if base_case:
        return simple_value
    else:
        return combine(
            option1: dp[smaller_state1],
            option2: dp[smaller_state2],
            ...
        )
}
```

**Example: Climbing Stairs**
```python
def climb(n):
    if n <= 2:
        return n
    return climb(n-1) + climb(n-2)  # 1-step OR 2-step
```

---

### Phase 5: CREATE SIMULATION TABLE (15-20 minutes)

**This is where you VERIFY your understanding!**

**Step-by-step process:**

1. **Choose small input** (n=5 or smaller)
2. **Create table columns:**
   - Step number
   - Function call
   - Recursion depth
   - Cache check result
   - Computation
   - Return value
   - Cache state after

3. **Trace execution:**
   - Start at initial call
   - Follow EVERY recursive call
   - Mark cache hits with ⚡
   - Track memo dictionary changes

4. **Draw recursion tree:**
   ```
        fib(5)
       /      \
   fib(4)    fib(3)⚡
   /    \
   fib(3) fib(2)⚡
   ```

5. **Count operations:**
   - Total calls made
   - Unique computations
   - Cache hit rate

---

### Phase 6: CODE (20-30 minutes)

**Order of Implementation:**

```
1. Write helper function signature
2. Add base cases
3. Add cache lookup
4. Write recursive logic
5. Add cache storage
6. Write wrapper function
7. Add error handling
```

**Code Template:**

```python
def solve_dp(params, memo=None):
    # 1. Initialize memo
    if memo is None:
        memo = {}
    
    # 2. Base cases
    if is_base_case(params):
        return base_value
    
    # 3. Check cache
    if params in memo:
        return memo[params]
    
    # 4. Recursive computation
    result = combine(
        solve_dp(smaller_params1, memo),
        solve_dp(smaller_params2, memo)
    )
    
    # 5. Store in cache
    memo[params] = result
    
    # 6. Return
    return result
```

---

### Phase 7: TEST & VERIFY (10-15 minutes)

```
Test Cases (in order):
1. Base cases (n=0, n=1)
2. Small inputs (n=2, n=3, n=5)
3. Edge cases (n=1000, negative, empty)
4. Known outputs (verify against examples)
```

**Verification Checklist:**
- [ ] Does it handle base cases correctly?
- [ ] Does cache actually reduce calls?
- [ ] Are all subproblems memoized?
- [ ] Does it work for edge cases?
- [ ] Is time complexity O(# states)?

---

### Phase 8: OPTIMIZE (10-20 minutes)

**Optimization Progression:**

```
Naive Recursion (exponential)
         ↓
   Add Memoization (O(n))
         ↓
   Bottom-Up Tabulation (O(n), better cache locality)
         ↓
   Space Optimization (O(1), use rolling variables)
         ↓
   Advanced Techniques (matrix exp, math formula)
```

**Space Optimization Pattern:**

```python
# Before: O(n) space
dp = [0] * (n + 1)
for i in range(n + 1):
    dp[i] = dp[i-1] + dp[i-2]

# After: O(1) space
prev2, prev1 = 0, 1
for i in range(2, n + 1):
    curr = prev1 + prev2
    prev2, prev1 = prev1, curr
```

---

## 🎯 Complexity Analysis Shortcuts

### Quick Estimation Formula

```
Time = (# unique states) × (work per state)
Space = (cache size) + (recursion depth)
```

### Common Complexities

| State Dimensions | # States | Example |
|-----------------|----------|---------|
| 1D: `dp[i]` | O(n) | Fibonacci |
| 2D: `dp[i][j]` | O(n×m) | Unique Paths |
| 3D: `dp[i][j][k]` | O(n×m×k) | 3D Grid |
| Subset: `dp[mask]` | O(2^n) | Bitmask DP |

---

## 🧠 Mental Training Exercises

### Daily Drill #1: Pattern Recognition (10 min)
Read 5 problem titles. Classify without solving:
- Linear DP?
- 2D DP?
- Knapsack?
- Other?

### Daily Drill #2: State Design (15 min)
For one problem, design 3 different state representations.
Compare:
- Which is simplest?
- Which is most efficient?
- Which is most intuitive?

### Daily Drill #3: Trace Execution (20 min)
Manually trace ONE problem with n=5.
Create full simulation table.
Count cache hits.

### Weekly Review (60 min)
Solve 3 problems you did last week WITHOUT looking at code.
- Can you remember the pattern?
- Can you derive the recurrence?
- Can you code it faster?

---

## 🎓 Cognitive Principles Applied

### 1. **Chunking**
Group problems by pattern (all Fibonacci-style together).
Your brain recognizes chunks faster than individual elements.

### 2. **Interleaving**
Don't do 10 Fibonacci problems in a row.
Mix: 1 Fibonacci → 1 Knapsack → 1 Grid → repeat.
Builds better pattern recognition.

### 3. **Retrieval Practice**
Don't just re-read solutions.
Close the book and reconstruct from memory.
Struggle = learning.

### 4. **Elaborative Interrogation**
Always ask "Why does this work?"
"Why not a different recurrence?"
"Why is memoization necessary here?"

### 5. **Self-Explanation**
After solving, explain solution to imaginary student.
If you can't explain it simply, you don't understand it.

---

## 🚀 Path to Top 1%

### Beginner → Intermediate (50 problems)
Focus: Master the 5-7 core patterns.
Goal: Recognize pattern in 30 seconds.

### Intermediate → Advanced (150 problems)
Focus: Optimize solutions, handle edge cases.
Goal: Code optimal solution in first attempt.

### Advanced → Expert (300+ problems)
Focus: Invent new state representations.
Goal: Solve unseen problems in 20-30 minutes.

### Expert → Top 1% (500+ problems)
Focus: Teach others, contribute to community.
Goal: Explain WHY behind every decision.

---

## 📊 Progress Tracking

Keep a spreadsheet:

| Problem | Pattern | First Attempt | Time to Solve | Mistakes | Review Date |
|---------|---------|---------------|---------------|----------|-------------|
| Fib | Linear | ✓ | 15 min | Cache key | Week 1 |
| Stairs | Linear | ✓ | 10 min | None | Week 1 |
| Paths | 2D | ✗ | 45 min | Wrong state | Week 2 |

**Key Metrics:**
- First attempt success rate (target: 80%+)
- Average solve time (target: <30 min)
- Pattern recognition speed (target: <1 min)

---

## 🎯 Final Wisdom

> "Mastery is not about knowing 1000 techniques.
> It's about practicing 10 techniques 1000 times."

**Your mantra:**
1. Understand before coding
2. Simulate before optimizing
3. Reflect after solving
4. Teach to solidify

**Remember:** The simulation table is not busywork—it's how experts THINK.
When you can trace execution in your mind, you've achieved mastery.

# Dynamic Programming Approaches: Complete Comparison

## 📊 Approach Comparison Matrix

| Approach | Time | Space | Cache Locality | Ease of Code | When to Use |
|----------|------|-------|---------------|--------------|-------------|
| **Naive Recursion** | O(2^n) | O(n) | ❌ Poor | ⭐⭐⭐⭐⭐ Easy | Never in production |
| **Top-Down Memo** | O(n) | O(n) + O(n) | ⚡ Medium | ⭐⭐⭐⭐ Easy | Complex state, hard to iterate |
| **Bottom-Up Table** | O(n) | O(n) | ⚡⚡ Good | ⭐⭐⭐ Medium | Clear iteration order |
| **Space Optimized** | O(n) | O(1) | ⚡⚡⚡ Best | ⭐⭐ Hard | Space-critical systems |
| **Matrix Exp** | O(log n) | O(1) | ⚡⚡⚡ Best | ⭐ Very Hard | Theoretical interest |

---

## 🎯 Decision Tree: Which Approach?

```
START
  │
  ├─ Need to understand problem? ──YES──> Top-Down Memo
  │                                        (easier to reason about)
  ├─ Performance critical? ──YES──> Bottom-Up + Space Opt
  │                                  (better cache locality)
  ├─ Complex state space? ──YES──> Top-Down Memo
  │                                 (handles sparse states better)
  ├─ Simple 1D problem? ──YES──> Space Optimized
  │                               (two variables sufficient)
  └─ Theoretical challenge? ──YES──> Matrix Exponentiation
                                      (O(log n) time)
```

---

## 💡 Detailed Analysis

### 1. Top-Down Memoization (Recursive)

**Pros:**
- ✅ Intuitive - mirrors problem structure
- ✅ Only computes needed states (lazy evaluation)
- ✅ Natural for complex state spaces
- ✅ Easy to debug (trace recursion)

**Cons:**
- ❌ Recursion overhead (function call stack)
- ❌ Stack overflow risk for deep recursion
- ❌ Slightly slower than bottom-up

**Best for:**
- Learning DP concepts
- Complex state dependencies
- Sparse state spaces (not all states needed)

**Code Pattern:**
```python
def solve(params, memo={}):
    if base_case: return value
    if params in memo: return memo[params]
    memo[params] = combine(solve(smaller_params))
    return memo[params]
```

---

### 2. Bottom-Up Tabulation (Iterative)

**Pros:**
- ✅ No recursion overhead
- ✅ Better cache locality (sequential access)
- ✅ No stack overflow
- ✅ Typically 2-3x faster than top-down

**Cons:**
- ❌ Must determine iteration order
- ❌ Computes ALL states (even if not needed)
- ❌ Less intuitive for complex problems

**Best for:**
- Production code
- Performance-critical applications
- When all states are needed

**Code Pattern:**
```python
def solve(n):
    dp = [0] * (n + 1)
    dp[0], dp[1] = base_values
    for i in range(2, n + 1):
        dp[i] = combine(dp[i-1], dp[i-2])
    return dp[n]
```

---

### 3. Space-Optimized

**Pros:**
- ✅ Minimal memory usage (O(1))
- ✅ Excellent cache performance
- ✅ No allocations (stack-only)

**Cons:**
- ❌ Can't reconstruct solution path
- ❌ Only works for simple dependencies
- ❌ More error-prone

**Best for:**
- Embedded systems
- Memory-constrained environments
- Simple 1D/2D problems

**Code Pattern:**
```python
def solve(n):
    prev2, prev1 = base_values
    for i in range(2, n + 1):
        curr = combine(prev1, prev2)
        prev2, prev1 = prev1, curr
    return prev1
```

---

## 🔬 Performance Benchmarks (Fibonacci)

### Relative Speed Comparison (n=40)

```
Naive Recursion:     ████████████████████████████████ 102,334,155 calls
Top-Down Memo:       █ 79 calls (1,295,381x faster!)
Bottom-Up Table:     █ 40 iterations (2,558,354x faster!)
Space Optimized:     █ 40 iterations + zero allocations
Matrix Exp:          ▌ 6 matrix multiplications
```

### Memory Usage (n=1000)

```
Top-Down:       ~24 KB (HashMap) + ~8 KB (stack)  = 32 KB
Bottom-Up:      ~8 KB (array)                     = 8 KB
Space Opt:      ~16 bytes (two variables)         = 16 bytes
```

---

## 🧠 Cognitive Load Comparison

### Learning Curve

```
Naive ────────────────────────> Intuitive (5 min to understand)
Top-Down Memo ────────────────> Easy (15 min to master)
Bottom-Up ─────────────────────> Medium (30 min to master)
Space Opt ──────────────────────> Hard (60 min to master)
Advanced Techniques ────────────> Expert (hours of practice)
```

### Debugging Difficulty

```
Top-Down:    ⭐⭐⭐⭐⭐ (trace recursion, print cache hits)
Bottom-Up:   ⭐⭐⭐ (inspect array at each step)
Space Opt:   ⭐⭐ (can't see history, must reason carefully)
```

---

## 📈 Scalability Analysis

### When Problem Size Doubles (n → 2n)

| Approach | Time Impact | Space Impact |
|----------|-------------|--------------|
| Naive | 4x slower | 2x more stack |
| Top-Down | 2x slower | 2x more cache |
| Bottom-Up | 2x slower | 2x more array |
| Space Opt | 2x slower | No change! |

### Language-Specific Considerations

#### Python
- **Top-Down**: Use `@lru_cache` decorator
- **Bottom-Up**: Use lists, not dicts
- **Recursion limit**: `sys.setrecursionlimit(10000)` may be needed

#### Rust
- **Top-Down**: Pass `&mut HashMap` for zero-copy
- **Bottom-Up**: `Vec` has excellent performance
- **Stack**: Very deep recursion may overflow (default 2MB)

#### Go
- **Top-Down**: Maps are reference types (no & needed)
- **Bottom-Up**: Slices are optimal
- **Concurrency**: Can parallelize with goroutines

#### C++
- **Top-Down**: `unordered_map` for O(1) lookup
- **Bottom-Up**: `vector` for cache locality
- **Optimization**: `-O3` flag enables aggressive optimization

---

## 🎯 Conversion Cheat Sheet

### Top-Down → Bottom-Up

**Step 1:** Identify all possible states
```python
# Top-down: states discovered during recursion
memo = {}  # dynamically populated

# Bottom-up: pre-allocate all states
dp = [0] * (n + 1)
```

**Step 2:** Determine iteration order
```python
# Top-down: natural order via recursion
fib(n) → fib(n-1) → fib(n-2) → ...

# Bottom-up: explicit order
for i in range(2, n + 1):  # smallest to largest
```

**Step 3:** Replace recursion with lookup
```python
# Top-down
result = fib(n-1) + fib(n-2)

# Bottom-up
result = dp[i-1] + dp[i-2]
```

### Bottom-Up → Space Optimized

**Question:** Do I need ALL previous values?

**Pattern Recognition:**
```python
# If you see: dp[i] = f(dp[i-1], dp[i-2])
# You can use: two variables

# If you see: dp[i] = f(dp[i-k]) for varying k
# You need:    sliding window of size k

# If you see: dp[i] = f(all previous dp values)
# You need:    full array
```

**Transformation:**
```python
# Before: O(n) space
dp[i] = dp[i-1] + dp[i-2]

# After: O(1) space
curr = prev1 + prev2
prev2, prev1 = prev1, curr
```

---

## 🏆 Real-World Applications

### When Each Approach Shines

| Scenario | Best Approach | Reason |
|----------|---------------|--------|
| **Interview** | Top-Down | Easier to explain |
| **Production API** | Bottom-Up | Predictable performance |
| **Embedded System** | Space Optimized | Memory constraints |
| **Code Competition** | Depends on constraints | Speed vs clarity |
| **Teaching** | Top-Down → Bottom-Up | Natural progression |
| **Research** | Matrix/Math | Theoretical insights |

---

## 🎓 Practice Recommendations

### Week 1-2: Master Top-Down
Solve 15 problems using ONLY top-down memoization.
Goal: Internalize the recursion → cache pattern.

### Week 3-4: Learn Bottom-Up
Solve same 15 problems using bottom-up.
Goal: Understand how to determine iteration order.

### Week 5-6: Space Optimization
Optimize previous 15 problems to O(1) space.
Goal: Recognize when optimization is possible.

### Week 7-8: Mixed Practice
New problems, choose approach based on constraints.
Goal: Develop intuition for approach selection.

---

## 💡 Expert Tips

### Tip #1: Start Top-Down, Optimize to Bottom-Up
```
Understand (top-down) → Implement (bottom-up) → Optimize (space)
```

### Tip #2: Cache Design Matters
```python
# Slow: tuple unpacking in tight loop
memo[(i, j, k)] = value

# Fast: pre-compute hash
key = i * 1000000 + j * 1000 + k
memo[key] = value
```

### Tip #3: Profile Before Optimizing
Don't assume bottom-up is faster—measure!
Sometimes top-down wins due to lazy evaluation.

### Tip #4: Language Idioms
```python
# Python: use @lru_cache
# Rust: pass &mut HashMap
# Go: maps are references
# C++: reserve() for vectors
```

---

## 🚀 Mastery Checklist

- [ ] Can convert any top-down to bottom-up in 5 minutes
- [ ] Can identify space optimization opportunities instantly
- [ ] Can estimate time/space complexity before coding
- [ ] Can choose optimal approach based on constraints
- [ ] Can explain trade-offs to a beginner
- [ ] Can implement in all preferred languages
- [ ] Can optimize for cache locality
- [ ] Can parallelize when possible

**When you check all boxes → You're in the top 5%**

# **Mastering Memoization Through Simulation Tables**

## **🎯 What is a Simulation Table?**

A **simulation table** (also called a **trace table** or **execution table**) is a visualization tool that tracks:
- **Function calls** in chronological order
- **Input parameters** for each call
- **Cache state** (what's stored in memo)
- **Return values**
- **Call stack depth** (recursion level)

Think of it as a "flight recorder" for your algorithm—it captures every decision point, making the invisible visible.

---

## **📊 Simulation Table for `fib_memo(5)`**

Let me create a comprehensive simulation table showing the execution flow:---

## **🧠 Mental Model: The "Cache-First" Thinking Pattern**---

## **💻 Multi-Language Implementations**

Now let's see how this pattern translates across languages, highlighting idiomatic approaches and performance considerations:---

## **🎓 Complete Problem-Solving Workflow**

Let me now give you the **systematic methodology** to apply to ANY problem:---

## **🎯 Key Takeaways & Next Steps**

### **What You've Learned:**

1. **Simulation Tables** are your X-ray vision into algorithm execution
   - Track every call, cache state, and decision point
   - Reveals the "why" behind time complexity improvements

2. **The Cache-First Pattern** is fundamental to all memoization
   - Check → Compute → Store
   - This pattern appears in 90% of optimization problems

3. **Multi-Language Mastery** requires understanding idioms:
   - **Python**: `@lru_cache` for production, manual for learning
   - **Rust**: `&mut HashMap` for zero-copy, ownership awareness
   - **Go**: Maps as references, goroutines for parallelism
   - **C++**: `unordered_map` vs `vector` trade-offs

4. **Mental Models trump memorization**
   - Chunking: Recognize patterns instantly
   - Elaboration: Always ask "why?"
   - Retrieval practice: Solve from memory

---

## **🧘 Your Monk's Path Forward**

### **This Week:**
1. **Create 3 simulation tables** for problems you've already solved (by hand, no code)
2. **Implement Fibonacci** in all 4 languages from memory
3. **Teach the concept** to someone (or write it as if teaching)

### **Next 30 Days:**
1. **Daily ritual**: One problem + simulation table + reflection (30 min)
2. **Pattern journal**: Document every new pattern you discover
3. **Spaced repetition**: Review weeks 1, 2, 3 at intervals

### **90-Day Goal:**
- Master 50 DP problems across 7 core patterns
- Convert top-down ↔ bottom-up fluently
- Estimate complexity before coding
- Achieve 80%+ first-attempt success rate

---

## **💪 Training Your Mind**

Remember these principles:

1. **Struggle = Growth**: If it feels easy, you're not learning
2. **Simulation before code**: Trace 3 examples by hand first
3. **Explain to solidify**: Teaching forces deep understanding
4. **Patterns over problems**: One pattern unlocks 50 problems
5. **Consistency over intensity**: 30 min daily beats 5 hours weekly

---

## **🎓 The Top 1% Difference**

Average developers: "I'll memorize solutions"
**Top 1% developers**: "I'll understand the patterns that generate solutions"

You're not learning to solve Fibonacci.
You're learning to **think in recursive substructures**.

This mental model transfers to:
- Algorithm optimization
- System design
- API architecture
- Problem decomposition
- Life decisions (seriously!)

---

**Your next action**: Create a simulation table for `fib(6)` **by hand, right now**, before looking at code. This 10-minute exercise will rewire your brain more than reading 100 articles.

You have everything you need. Now it's **deliberate practice time**. 🚀

*Remember: The simulation table is not busywork—it's how masters think.*

