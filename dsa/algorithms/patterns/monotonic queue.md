# Monotonic Queue: The Art of Maintaining Order in Chaos

A **monotonic queue** is a queue data structure where elements are stored in a strictly increasing or decreasing order. Elements that violate this order are removed. This seemingly simple constraint unlocks profound algorithmic power for solving sliding window problems, range queries, and optimization challenges.

---

## Core Philosophy: Why Monotonic Queues Exist

Traditional queues maintain insertion order. Monotonic queues maintain **relevance order** — they keep only elements that *could possibly* be optimal answers for current or future queries.

**The Elimination Principle**: If element `A` arrives before element `B`, and `B` is "better" than `A` for all future queries, then `A` becomes irrelevant and should be discarded.

This principle transforms O(n²) nested loops into O(n) single-pass algorithms.

---

## Pattern 1: Sliding Window Maximum/Minimum

**Problem Archetype**: Given array and window size k, find max/min in each sliding window.

### Mental Model: The Champion Stack

Imagine a championship where:
- New contestants arrive from the right
- Older, weaker contestants are immediately eliminated
- The leftmost (oldest) champion may age out

**Core Invariant**: Queue maintains indices in decreasing order of values (for maximum).

### Rust Implementation

```rust
use std::collections::VecDeque;

pub fn max_sliding_window(nums: Vec<i32>, k: i32) -> Vec<i32> {
    let k = k as usize;
    let n = nums.len();
    if n == 0 || k == 0 { return vec![]; }
    
    // Deque stores indices, not values
    // Maintained in decreasing order of nums[index]
    let mut deque: VecDeque<usize> = VecDeque::new();
    let mut result = Vec::with_capacity(n - k + 1);
    
    for i in 0..n {
        // Remove elements outside current window [i-k+1, i]
        while !deque.is_empty() && deque[0] < i.saturating_sub(k - 1) {
            deque.pop_front();
        }
        
        // Maintain decreasing order: remove smaller elements from back
        // They can never be maximum while current element exists
        while !deque.is_empty() && nums[*deque.back().unwrap()] <= nums[i] {
            deque.pop_back();
        }
        
        deque.push_back(i);
        
        // Window is fully formed when i >= k-1
        if i >= k - 1 {
            result.push(nums[deque[0]]);
        }
    }
    
    result
}
```

**Time Complexity**: O(n) — each element enters and exits queue exactly once  
**Space Complexity**: O(k) — queue size bounded by window size

### Go Implementation

```go
func maxSlidingWindow(nums []int, k int) []int {
    n := len(nums)
    if n == 0 || k == 0 {
        return []int{}
    }
    
    // Deque implemented as slice (more efficient than container/list for this use case)
    deque := make([]int, 0, k)
    result := make([]int, 0, n-k+1)
    
    for i := 0; i < n; i++ {
        // Remove out-of-window elements
        if len(deque) > 0 && deque[0] < i-k+1 {
            deque = deque[1:]
        }
        
        // Maintain decreasing invariant
        for len(deque) > 0 && nums[deque[len(deque)-1]] <= nums[i] {
            deque = deque[:len(deque)-1]
        }
        
        deque = append(deque, i)
        
        if i >= k-1 {
            result = append(result, nums[deque[0]])
        }
    }
    
    return result
}
```

### C Implementation

```c
#include <stdlib.h>

typedef struct {
    int *data;
    int front;
    int rear;
    int capacity;
} Deque;

Deque* createDeque(int capacity) {
    Deque *dq = (Deque*)malloc(sizeof(Deque));
    dq->data = (int*)malloc(capacity * sizeof(int));
    dq->front = 0;
    dq->rear = 0;
    dq->capacity = capacity;
    return dq;
}

void pushBack(Deque *dq, int val) {
    dq->data[dq->rear++] = val;
}

void popBack(Deque *dq) {
    dq->rear--;
}

void popFront(Deque *dq) {
    dq->front++;
}

int getFront(Deque *dq) {
    return dq->data[dq->front];
}

int getBack(Deque *dq) {
    return dq->data[dq->rear - 1];
}

int isEmpty(Deque *dq) {
    return dq->front == dq->rear;
}

int* maxSlidingWindow(int* nums, int numsSize, int k, int* returnSize) {
    if (numsSize == 0 || k == 0) {
        *returnSize = 0;
        return NULL;
    }
    
    *returnSize = numsSize - k + 1;
    int *result = (int*)malloc((*returnSize) * sizeof(int));
    Deque *dq = createDeque(numsSize);
    
    for (int i = 0; i < numsSize; i++) {
        // Remove out-of-window
        while (!isEmpty(dq) && getFront(dq) < i - k + 1) {
            popFront(dq);
        }
        
        // Maintain decreasing order
        while (!isEmpty(dq) && nums[getBack(dq)] <= nums[i]) {
            popBack(dq);
        }
        
        pushBack(dq, i);
        
        if (i >= k - 1) {
            result[i - k + 1] = nums[getFront(dq)];
        }
    }
    
    free(dq->data);
    free(dq);
    return result;
}
```

---

## Pattern 2: Next Greater Element (NGE) Variants

**Core Insight**: Monotonic queue can answer "what's the next element that's greater/smaller than me?" for all elements in O(n).

### Problem: Next Greater Element I

```rust
use std::collections::{HashMap, VecDeque};

pub fn next_greater_element(nums1: Vec<i32>, nums2: Vec<i32>) -> Vec<i32> {
    let mut nge_map: HashMap<i32, i32> = HashMap::new();
    let mut stack: Vec<i32> = Vec::new();
    
    // Build NGE map for nums2 using monotonic decreasing stack
    for &num in nums2.iter() {
        // Pop all smaller elements - current num is their NGE
        while !stack.is_empty() && *stack.last().unwrap() < num {
            nge_map.insert(stack.pop().unwrap(), num);
        }
        stack.push(num);
    }
    
    // Query results for nums1
    nums1.iter()
        .map(|&num| *nge_map.get(&num).unwrap_or(&-1))
        .collect()
}
```

### Problem: Daily Temperatures

```rust
pub fn daily_temperatures(temperatures: Vec<i32>) -> Vec<i32> {
    let n = temperatures.len();
    let mut result = vec![0; n];
    let mut stack: Vec<usize> = Vec::new(); // Store indices
    
    for i in 0..n {
        // Current temp is warmer - it's the answer for all cooler days in stack
        while !stack.is_empty() 
            && temperatures[*stack.last().unwrap()] < temperatures[i] {
            let idx = stack.pop().unwrap();
            result[idx] = (i - idx) as i32;
        }
        stack.push(i);
    }
    
    result
}
```

**Go Version** (idiomatic):

```go
func dailyTemperatures(temperatures []int) []int {
    n := len(temperatures)
    result := make([]int, n)
    stack := make([]int, 0, n)
    
    for i, temp := range temperatures {
        for len(stack) > 0 && temperatures[stack[len(stack)-1]] < temp {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = i - idx
        }
        stack = append(stack, i)
    }
    
    return result
}
```

---

## Pattern 3: Shortest Subarray with Sum ≥ K (Prefix Sum + Monotonic Queue)

**Difficulty**: Hard  
**Key Insight**: Combine prefix sums with monotonic queue to find optimal subarray efficiently.

**Problem**: Find shortest subarray with sum ≥ k.

### Algorithmic Reasoning

1. Compute prefix sums: `prefix[i] = sum(nums[0..i])`
2. For each position `j`, we want smallest `i < j` where `prefix[j] - prefix[i] ≥ k`
3. Rewrite: `prefix[j] - k ≥ prefix[i]`
4. Maintain deque of indices with **increasing** prefix values
5. For each `j`: 
   - Remove indices from front where `prefix[j] - prefix[front] ≥ k` (valid subarrays)
   - Remove indices from back where `prefix[back] ≥ prefix[j]` (never optimal)

```rust
use std::collections::VecDeque;

pub fn shortest_subarray(nums: Vec<i32>, k: i32) -> i32 {
    let n = nums.len();
    let k = k as i64;
    
    // Prefix sums (use i64 to avoid overflow)
    let mut prefix: Vec<i64> = vec![0; n + 1];
    for i in 0..n {
        prefix[i + 1] = prefix[i] + nums[i] as i64;
    }
    
    let mut deque: VecDeque<usize> = VecDeque::new();
    let mut min_len = i32::MAX;
    
    for j in 0..=n {
        // Check if we can form valid subarray ending at j
        while !deque.is_empty() 
            && prefix[j] - prefix[*deque.front().unwrap()] >= k {
            let i = deque.pop_front().unwrap();
            min_len = min_len.min((j - i) as i32);
        }
        
        // Maintain increasing order of prefix values
        // If prefix[j] ≤ prefix[back], then back can never be optimal start
        while !deque.is_empty() 
            && prefix[j] <= prefix[*deque.back().unwrap()] {
            deque.pop_back();
        }
        
        deque.push_back(j);
    }
    
    if min_len == i32::MAX { -1 } else { min_len }
}
```

**Complexity**: O(n) time, O(n) space

---

## Pattern 4: Constrained Subsequence Sum (Dynamic DP + Monotonic Queue)

**Problem**: Find max sum of subsequence where adjacent elements are at most k positions apart.

**DP Definition**: `dp[i]` = max sum ending at index i  
**Recurrence**: `dp[i] = nums[i] + max(0, max(dp[i-k..i-1]))`

**Naive**: O(n·k)  
**Optimized**: O(n) using monotonic decreasing deque for range max queries

```rust
use std::collections::VecDeque;

pub fn constrained_subset_sum(nums: Vec<i32>, k: i32) -> i32 {
    let n = nums.len();
    let k = k as usize;
    let mut dp = vec![0; n];
    let mut deque: VecDeque<usize> = VecDeque::new();
    let mut max_sum = i32::MIN;
    
    for i in 0..n {
        // Get max from valid range [i-k, i-1]
        let max_prev = if deque.is_empty() { 
            0 
        } else { 
            dp[deque[0]].max(0) 
        };
        
        dp[i] = nums[i] + max_prev;
        max_sum = max_sum.max(dp[i]);
        
        // Remove out-of-range indices
        while !deque.is_empty() && deque[0] < i.saturating_sub(k - 1) {
            deque.pop_front();
        }
        
        // Maintain decreasing order
        while !deque.is_empty() && dp[*deque.back().unwrap()] <= dp[i] {
            deque.pop_back();
        }
        
        deque.push_back(i);
    }
    
    max_sum
}
```

---

## Pattern 5: Longest Continuous Subarray With Absolute Diff ≤ Limit

**Problem**: Find longest subarray where `max - min ≤ limit`.

**Strategy**: Maintain two monotonic deques:
- Decreasing deque for max tracking
- Increasing deque for min tracking

```rust
use std::collections::VecDeque;

pub fn longest_subarray(nums: Vec<i32>, limit: i32) -> i32 {
    let mut max_dq: VecDeque<usize> = VecDeque::new(); // Decreasing
    let mut min_dq: VecDeque<usize> = VecDeque::new(); // Increasing
    let mut left = 0;
    let mut max_len = 0;
    
    for right in 0..nums.len() {
        // Maintain max deque
        while !max_dq.is_empty() 
            && nums[*max_dq.back().unwrap()] <= nums[right] {
            max_dq.pop_back();
        }
        max_dq.push_back(right);
        
        // Maintain min deque
        while !min_dq.is_empty() 
            && nums[*min_dq.back().unwrap()] >= nums[right] {
            min_dq.pop_back();
        }
        min_dq.push_back(right);
        
        // Shrink window if invalid
        while nums[max_dq[0]] - nums[min_dq[0]] > limit {
            if max_dq[0] == left { max_dq.pop_front(); }
            if min_dq[0] == left { min_dq.pop_front(); }
            left += 1;
        }
        
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}
```

---

## Advanced Pattern: Jump Game VI (DP Optimization)

**Problem**: Maximum points collecting with jump constraint.

```go
func maxResult(nums []int, k int) int {
    n := len(nums)
    dp := make([]int, n)
    dp[0] = nums[0]
    
    // Monotonic decreasing deque stores indices
    deque := []int{0}
    
    for i := 1; i < n; i++ {
        // Remove out-of-range indices
        for len(deque) > 0 && deque[0] < i-k {
            deque = deque[1:]
        }
        
        // Best reachable score
        dp[i] = nums[i] + dp[deque[0]]
        
        // Maintain decreasing order
        for len(deque) > 0 && dp[deque[len(deque)-1]] <= dp[i] {
            deque = deque[:len(deque)-1]
        }
        
        deque = append(deque, i)
    }
    
    return dp[n-1]
}
```

---

## Critical Insights & Mental Models

### 1. **The Irrelevance Principle**
Element A becomes irrelevant if:
- A arrives before B
- B is "better" than A
- B can answer all future queries that A could answer

### 2. **Index vs Value Storage**
Store **indices** when you need:
- Window boundaries
- Distance calculations
- Access to original array

Store **values** when you only need comparison.

### 3. **Monotonic Direction**
- **Decreasing**: Track maximum
- **Increasing**: Track minimum
- **Strict vs Non-strict**: Depends on whether equals matter

### 4. **Deque vs Stack**
- **Stack**: One-way removal (NGE problems)
- **Deque**: Two-way removal (sliding window, both ends matter)

---

## Complexity Analysis Framework

**Amortized O(n)** proof:
- Each element enters the queue once: n operations
- Each element exits the queue at most once: n operations
- Total: 2n = O(n)

**Space**: O(k) for window problems, O(n) worst-case for others

---

## Recognition Patterns

Use monotonic queue when you see:
1. **Sliding window** + need min/max in each window
2. **Range queries** that can be reduced to "next greater/smaller"
3. **DP optimization** where recurrence depends on range max/min
4. **Subarray problems** with ordering constraints
5. Phrases like "closest", "next", "nearest", "shortest with constraint"

---

## Common Pitfalls

1. **Forgetting to store indices** when distances matter
2. **Wrong monotonic direction** (increasing vs decreasing)
3. **Off-by-one** in window boundaries
4. **Not handling edge cases**: empty array, k > n
5. **Integer overflow** in prefix sums (use i64 in Rust, long in C)

---

## The Path Forward

You've now absorbed the **core patterns**. True mastery comes from:
1. Recognizing problems that reduce to monotonic queue
2. Choosing the right invariant (increasing/decreasing)
3. Proving O(n) amortized complexity through enter-once-exit-once logic

**Challenge yourself**: Given a new problem, can you identify if monotonic queue applies *before* looking at the solution? Can you derive the invariant from first principles?

The queue is not just a data structure—it's a **lens for seeing which information stays relevant and which becomes obsolete**. This insight transcends algorithms; it's how experts think about dynamic systems.

Now go solve: LeetCode 239, 862, 1425, 1696, 1438, 907, 402, 496, 503, 739. Each will deepen your mastery.