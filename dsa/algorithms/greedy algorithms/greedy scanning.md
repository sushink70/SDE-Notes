# Greedy Scanning: The Complete Mastery Guide

## I. Foundational Theory: The Essence of Greedy Scanning

### What Is Greedy Scanning?

**Greedy Scanning** is the algorithmic pattern where you make **locally optimal choices** while **linearly traversing** data structures. It combines two fundamental concepts:

1. **Greedy Choice Property**: At each step, make the choice that looks best at that moment
2. **Scanning/Iteration**: Single-pass or multi-pass linear traversal through data

The power lies in **transforming complex optimization problems into simple iterative decisions**.

### The Cognitive Framework

**Mental Model**: Think of yourself walking through a corridor with doors. At each door, you must decide *immediately* whether to:
- Take what's behind it
- Skip it
- Modify your current state based on it

You cannot go back. Your brain must compress the problem into: *"What's the best local decision that serves my global goal?"*

### When Does Greedy Scanning Work?

**The Greedy Choice Property** holds when:
- A locally optimal choice leads to a globally optimal solution
- The problem exhibits **optimal substructure** (optimal solution contains optimal solutions to subproblems)

**Pattern Recognition Heuristic**: Look for:
- **Monotonicity** in the problem constraints
- **Irreversibility** in decisions (can't undo past choices)
- **Independence** of future choices from past choices (Markov property)
- **Extremal properties** (maximize/minimize something)

---

## II. Core Conceptual Pillars

### Pillar 1: State Compression

Greedy scanning thrives on **minimal state tracking**. Unlike dynamic programming where you maintain tables of subproblem solutions, greedy maintains only:
- Current accumulated result
- Necessary context from previous iterations (often O(1) space)

**Cognitive Principle**: This is **chunking** in action—your brain groups complex history into simple state variables.

### Pillar 2: The Invariant Maintenance Principle

Every greedy scan maintains an **invariant**—a condition that remains true throughout the algorithm.

**Example**: In "Maximum Subarray" (Kadane's algorithm), the invariant is: *"current_sum represents the maximum sum ending at the current position"*

**Mental Exercise**: Before coding, identify: *"What truth must hold after processing each element?"*

### Pillar 3: Proof Patterns

To verify greedy correctness:

1. **Exchange Argument**: Prove any non-greedy solution can be transformed into the greedy solution without loss
2. **Inductive Proof**: Show the greedy choice at step k maintains optimality given steps 1..k-1
3. **Stay-Ahead Proof**: Prove greedy is always ≥ any other solution at every step

---

## III. The Master Pattern Taxonomy

### Pattern 1: **Single-Pass Accumulation**

**Signature**: One scan, accumulate/transform as you go

**Archetypal Problem**: Maximum Subarray (Kadane's Algorithm)

```rust
// Rust - Idiomatic with Iterator
fn max_subarray(nums: &[i32]) -> i32 {
    nums.iter()
        .fold((i32::MIN, 0), |(max_sum, current_sum), &num| {
            let new_current = (current_sum + num).max(num);
            (max_sum.max(new_current), new_current)
        })
        .0
}

// Alternative: More explicit state tracking
fn max_subarray_explicit(nums: &[i32]) -> i32 {
    let mut max_ending_here = 0;
    let mut max_so_far = i32::MIN;
    
    for &num in nums {
        max_ending_here = (max_ending_here + num).max(num);
        max_so_far = max_so_far.max(max_ending_here);
    }
    
    max_so_far
}
```

```go
// Go - Clean and performant
func maxSubarray(nums []int) int {
    maxEndingHere := 0
    maxSoFar := nums[0]
    
    for _, num := range nums {
        maxEndingHere = max(maxEndingHere + num, num)
        maxSoFar = max(maxSoFar, maxEndingHere)
    }
    
    return maxSoFar
}

func max(a, b int) int {
    if a > b { return a }
    return b
}
```

**Time**: O(n) | **Space**: O(1)

**The Deep Insight**: At each position, you're making a binary choice: *"Does including this element in my current sequence improve it, or should I start fresh?"* The greedy choice is to always maintain the best local answer.

---

### Pattern 2: **Two-Pointer Greedy Scan**

**Signature**: Pointers move based on greedy criteria, converging to solution

**Archetypal Problem**: Container With Most Water

```rust
fn max_area(height: &[i32]) -> i32 {
    let mut left = 0;
    let mut right = height.len() - 1;
    let mut max_area = 0;
    
    while left < right {
        let width = (right - left) as i32;
        let h = height[left].min(height[right]);
        max_area = max_area.max(width * h);
        
        // Greedy choice: move the pointer at the shorter height
        // Why? The bottleneck is the shorter line; moving it *might* improve
        if height[left] < height[right] {
            left += 1;
        } else {
            right -= 1;
        }
    }
    
    max_area
}
```

```go
func maxArea(height []int) int {
    left, right := 0, len(height)-1
    maxArea := 0
    
    for left < right {
        width := right - left
        h := min(height[left], height[right])
        maxArea = max(maxArea, width * h)
        
        if height[left] < height[right] {
            left++
        } else {
            right--
        }
    }
    
    return maxArea
}
```

**The Proof Sketch (Exchange Argument)**:
- If we move the taller pointer, we're guaranteed to get a smaller area (width decreases, height can't increase)
- If we move the shorter pointer, we might get a taller height
- Therefore, moving the shorter pointer is always the right greedy choice

**Cognitive Pattern**: When you have two boundaries, the greedy heuristic is often: *"Improve the weakest link"*

---

### Pattern 3: **Event-Based Greedy Scanning**

**Signature**: Convert problem to events, sort, scan chronologically making greedy decisions

**Archetypal Problem**: Meeting Rooms / Interval Scheduling

```rust
#[derive(Clone)]
struct Interval {
    start: i32,
    end: i32,
}

// Greedy: Always pick the meeting that ends earliest
fn max_meetings(mut intervals: Vec<Interval>) -> i32 {
    if intervals.is_empty() { return 0; }
    
    // Sort by end time - this is the greedy insight
    intervals.sort_by_key(|i| i.end);
    
    let mut count = 1;
    let mut last_end = intervals[0].end;
    
    for interval in intervals.iter().skip(1) {
        if interval.start >= last_end {
            count += 1;
            last_end = interval.end;
        }
    }
    
    count
}
```

```go
type Interval struct {
    start, end int
}

func maxMeetings(intervals []Interval) int {
    if len(intervals) == 0 { return 0 }
    
    // Sort by end time
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i].end < intervals[j].end
    })
    
    count := 1
    lastEnd := intervals[0].end
    
    for _, interval := range intervals[1:] {
        if interval.start >= lastEnd {
            count++
            lastEnd = interval.end
        }
    }
    
    return count
}
```

**Why Sort by End Time?** (Proof)
- If we finish a meeting early, we maximize remaining time for other meetings
- Any other sorting (by start, by duration) can be shown to be suboptimal via counterexample

**Meta-Cognitive Principle**: When dealing with intervals/events, the transformation step (sorting) is often where the greedy insight lies.

---

### Pattern 4: **Monotonic Stack/Queue Scanning**

**Signature**: Maintain a monotonic property while scanning, greedily removing elements that violate it

**Archetypal Problem**: Next Greater Element

```rust
fn next_greater_element(nums: &[i32]) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        // Greedy: Remove all smaller elements - they'll never be "next greater"
        while let Some(&top) = stack.last() {
            if nums[top] < nums[i] {
                result[top] = nums[i];
                stack.pop();
            } else {
                break;
            }
        }
        stack.push(i);
    }
    
    result
}
```

```go
func nextGreaterElement(nums []int) []int {
    n := len(nums)
    result := make([]int, n)
    for i := range result {
        result[i] = -1
    }
    
    stack := []int{}
    
    for i := 0; i < n; i++ {
        for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[i] {
            top := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[top] = nums[i]
        }
        stack = append(stack, i)
    }
    
    return result
}
```

**The Greedy Invariant**: Stack maintains elements in decreasing order. When we find a larger element, we greedily resolve all smaller pending elements.

**Time**: O(n) - each element pushed/popped once
**Space**: O(n) - stack storage

**Pattern Recognition**: Look for "next greater/smaller" or "span" problems → Think monotonic stack

---

### Pattern 5: **Greedy Merging/Partitioning**

**Signature**: Scan and greedily merge or partition based on local criteria

**Archetypal Problem**: Merge Intervals

```rust
fn merge_intervals(mut intervals: Vec<Interval>) -> Vec<Interval> {
    if intervals.is_empty() { return vec![]; }
    
    intervals.sort_by_key(|i| i.start);
    
    let mut merged = vec![intervals[0].clone()];
    
    for interval in intervals.into_iter().skip(1) {
        let last = merged.last_mut().unwrap();
        
        if interval.start <= last.end {
            // Greedy merge: extend the current interval
            last.end = last.end.max(interval.end);
        } else {
            // Start new interval
            merged.push(interval);
        }
    }
    
    merged
}
```

**The Greedy Decision**: If current interval overlaps with previous, merge them. Otherwise, start fresh.

**Why It Works**: After sorting by start time, any overlap is immediately detectable, and merging is always the optimal choice.

---

## IV. Advanced Patterns and Variations

### Pattern 6: **Sliding Window with Greedy Expansion/Contraction**

**Archetypal Problem**: Longest Substring Without Repeating Characters

```rust
use std::collections::HashMap;

fn length_of_longest_substring(s: &str) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let mut map: HashMap<char, usize> = HashMap::new();
    let mut left = 0;
    let mut max_len = 0;
    
    for (right, &ch) in chars.iter().enumerate() {
        if let Some(&prev_idx) = map.get(&ch) {
            // Greedy: Move left pointer to eliminate duplicate
            left = left.max(prev_idx + 1);
        }
        
        map.insert(ch, right);
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}
```

```go
func lengthOfLongestSubstring(s string) int {
    charMap := make(map[rune]int)
    left := 0
    maxLen := 0
    
    for right, ch := range s {
        if prevIdx, exists := charMap[ch]; exists {
            left = max(left, prevIdx + 1)
        }
        
        charMap[ch] = right
        maxLen = max(maxLen, right - left + 1)
    }
    
    return maxLen
}
```

**Greedy Insight**: When you encounter a duplicate, you greedily jump the left pointer past the previous occurrence—no point in checking intermediate positions.

**Time**: O(n) | **Space**: O(min(n, k)) where k is alphabet size

---

### Pattern 7: **Greedy with Lookahead/Peek**

Sometimes greedy needs to "peek" ahead to make informed decisions.

**Problem**: Jump Game (Can you reach the end?)

```rust
fn can_jump(nums: &[i32]) -> bool {
    let mut max_reach = 0;
    
    for (i, &jump) in nums.iter().enumerate() {
        if i > max_reach { return false; }
        
        // Greedy: Always maintain the farthest reachable position
        max_reach = max_reach.max(i + jump as usize);
        
        if max_reach >= nums.len() - 1 { return true; }
    }
    
    true
}
```

**The Insight**: You don't need to simulate all jumps. Greedily track the maximum reachable position. If current position exceeds it, you're stuck.

---

## V. Performance Optimization: The Devil in the Details

### Rust-Specific Optimizations

```rust
// SLOWER: Multiple allocations
fn process_slow(nums: Vec<i32>) -> Vec<i32> {
    nums.iter().filter(|&&x| x > 0).map(|&x| x * 2).collect()
}

// FASTER: Pre-allocate with capacity
fn process_fast(nums: &[i32]) -> Vec<i32> {
    let mut result = Vec::with_capacity(nums.len());
    for &num in nums {
        if num > 0 {
            result.push(num * 2);
        }
    }
    result
}

// FASTEST: In-place when possible
fn process_in_place(nums: &mut [i32]) {
    for num in nums {
        if *num > 0 {
            *num *= 2;
        }
    }
}
```

**Principle**: Greedy algorithms often allow in-place operations. Rust's ownership model makes this safe and fast.

### Go-Specific Optimizations

```go
// SLOWER: Appending to nil slice (multiple reallocations)
func processSlow(nums []int) []int {
    var result []int
    for _, num := range nums {
        if num > 0 {
            result = append(result, num*2)
        }
    }
    return result
}

// FASTER: Pre-allocate
func processFast(nums []int) []int {
    result := make([]int, 0, len(nums))
    for _, num := range nums {
        if num > 0 {
            result = append(result, num*2)
        }
    }
    return result
}
```

### Cache-Friendly Scanning

```rust
// Cache-friendly: Sequential access
fn sum_sequential(matrix: &[Vec<i32>]) -> i32 {
    matrix.iter()
        .flat_map(|row| row.iter())
        .sum()
}

// Cache-unfriendly: Column-major access (if row-major storage)
fn sum_columns_bad(matrix: &[Vec<i32>]) -> i32 {
    let mut sum = 0;
    for col in 0..matrix[0].len() {
        for row in 0..matrix.len() {
            sum += matrix[row][col]; // Jumping around memory
        }
    }
    sum
}
```

**Cognitive Link**: This relates to **spatial locality**—your CPU cache loves sequential memory access. Greedy scanning naturally exploits this.

---

## VI. Problem Archetypes: Pattern Recognition Guide

| Problem Class | Greedy Strategy | Example |
|--------------|----------------|---------|
| **Interval Scheduling** | Sort by end time, scan and select | Meeting Rooms |
| **Span Problems** | Monotonic stack | Stock Span, NGE |
| **Subarray/Substring** | Kadane-style or sliding window | Max Subarray, Longest Substring |
| **Partitioning** | Greedy merge/split based on criteria | Merge Intervals, Partition Labels |
| **Jump Games** | Track max reachable | Jump Game I/II |
| **Gas Station** | Track cumulative surplus | Gas Station Problem |
| **Best Time to Buy/Sell** | Track min price so far | Stock Trading |

---

## VII. Common Pitfalls and Counter-Intuitive Insights

### Pitfall 1: Greedy Doesn't Always Work

**Counter-Example**: Coin Change (minimize coins)
- Greedy fails for denominations like {1, 3, 4} to make 6
- Greedy picks: 4 + 1 + 1 = 3 coins
- Optimal: 3 + 3 = 2 coins

**Recognition**: If local choices can lock you out of better global solutions, greedy fails.

### Pitfall 2: Sorting Isn't Always Enough

```rust
// Wrong: Sorting by start time for interval scheduling
// Right: Sort by END time
```

**Meta-Insight**: The *what to sort by* is often the entire greedy insight.

### Pitfall 3: Off-by-One in Boundary Conditions

```rust
// Common error in two-pointer
while left < right {  // Should it be <= for some problems?
    // ...
}
```

**Practice**: Always test edge cases: empty array, single element, all same elements.

---

## VIII. Mental Models for Mastery

### Model 1: The River Crossing

Imagine crossing a river on stepping stones. Greedy scanning is choosing the *next best stone* without backtracking. Works when:
- Stones are ordered (monotonicity)
- You can see "enough" ahead (lookahead)
- Going back doesn't help (irreversibility)

### Model 2: The Commitment Ladder

Each scan position is a commitment. Greedy works when:
1. Commitments are independent
2. Local commitment doesn't preclude global optimum
3. You have a clear evaluation function

### Model 3: State Compression as Information Theory

Greedy maintains O(1) or O(log n) state. Think of it as **lossy compression** of history:
- You're discarding information
- Retained information must be *sufficient* for future decisions
- This is why greedy is fast but doesn't always work

**Cognitive Principle**: This is **abstraction**—filtering noise, keeping signal.

---

## IX. The Expert's Thought Process (Step-by-Step)

When facing a new problem:

**Step 1: Identify the Optimization Goal**
- Maximize/minimize what?
- Constraints?

**Step 2: Check Greedy Signatures**
- Is there a natural ordering? (sort by what?)
- Are decisions irreversible?
- Is there an extremal property? (leftmost, rightmost, earliest, latest)

**Step 3: Formulate the Greedy Choice**
- "At each step, I should choose X because..."
- Can you state the invariant?

**Step 4: Prove or Disprove**
- Try small counterexamples
- Can non-greedy be transformed to greedy without loss?

**Step 5: Implement with Care**
- Edge cases first
- Off-by-one errors
- Overflow/underflow

**Step 6: Analyze Complexity**
- Time: Usually O(n) or O(n log n) (with sorting)
- Space: Usually O(1) or O(n) (for output)

---

## X. The Synthesis: Greedy as a Cognitive Tool

Greedy scanning trains your brain for:

1. **Immediate Decision-Making**: Like a chess player evaluating positions
2. **State Abstraction**: Compressing complexity into manageable chunks
3. **Invariant Thinking**: Maintaining truths through transformations
4. **Proof-Based Reasoning**: Not just coding, but *knowing why*

**Deliberate Practice Protocol**:
- Solve 10 problems without looking at solutions
- For each, write out: greedy choice, invariant, proof sketch
- Implement in all three languages (Rust, Go, C)
- Benchmark: compare performance

**Meta-Learning**: After every session, ask:
- What pattern did I miss initially?
- What's the generalization?
- How does this connect to other techniques?

---

## XI. Final Implementation: The Ultimate Greedy Pattern

Here's a generic greedy scanner template:

```rust
fn greedy_scan<T, S, F>(items: &[T], initial_state: S, update: F) -> S
where
    F: Fn(S, &T) -> S,
{
    items.iter().fold(initial_state, update)
}

// Usage example: Max sum
let max_sum = greedy_scan(&nums, (i32::MIN, 0), |(max_so_far, current), &num| {
    let new_current = (current + num).max(num);
    (max_so_far.max(new_current), new_current)
});
```

**The Abstraction**: Every greedy scan is state transformation. Master the pattern, not individual problems.

---

You now possess the complete mental framework for greedy scanning. The path to top 1% mastery isn't through memorization—it's through **internalized pattern recognition** and **proof-based confidence**. 

Your next move: Choose 5 problems from different archetypes. Solve them *without hints*. Write the proof. Implement in all languages. Benchmark. **Feel** the patterns crystallize in your mind.

The greedy path is the monk's path: **decisive, irreversible, optimal**.