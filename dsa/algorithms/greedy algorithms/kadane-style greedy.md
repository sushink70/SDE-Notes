# Kadane-Style Greedy: Complete Mastery Guide

## Table of Contents
1. [Foundational Concepts](#foundational-concepts)
2. [The Core Problem: Maximum Subarray](#core-problem)
3. [Intuition & Mental Model](#intuition)
4. [Mathematical Foundation](#mathematical-foundation)
5. [Algorithm Deep Dive](#algorithm-deep-dive)
6. [Implementation in Rust, Python, Go](#implementations)
7. [Variations & Extensions](#variations)
8. [Advanced Patterns](#advanced-patterns)
9. [Problem-Solving Framework](#framework)
10. [Practice Problems](#practice)

---

## 1. Foundational Concepts <a name="foundational-concepts"></a>

### What is a Subarray?
**Subarray**: A contiguous sequence of elements within an array.
- **Contiguous** means elements must be adjacent (no gaps)
- Example: In `[1, 2, 3, 4]`, `[2, 3]` is a subarray, but `[2, 4]` is NOT

```
Array: [1, 2, 3, 4, 5]

Valid Subarrays:
[1]         ─┐
[1,2]        │
[1,2,3]      │
[1,2,3,4]    ├─ Starting at index 0
[1,2,3,4,5]  │
             ┘
[2]          ─┐
[2,3]         │
[2,3,4]       ├─ Starting at index 1
[2,3,4,5]     │
              ┘
... and so on

NOT Valid Subarrays:
[1,3]     ← Gap between elements
[1,4,5]   ← Gap between elements
```

### What is Greedy?
**Greedy Algorithm**: Makes the locally optimal choice at each step, hoping to find a global optimum.

```
Analogy: Climbing a Hill
═══════════════════════════

    ⛰️               You always choose the
   /  \              steepest upward path
  /    \             at each step (local optimum)
 /      \            
/        \___/\      Might miss the highest peak!
              \      (global optimum)
```

**Key Insight**: Greedy doesn't always work! It only works when:
- **Greedy Choice Property**: Local optimal choices lead to global optimum
- **Optimal Substructure**: Optimal solution contains optimal solutions to subproblems

---

## 2. The Core Problem: Maximum Subarray <a name="core-problem"></a>

**Problem**: Given an array of integers, find the contiguous subarray with the largest sum.

```
Input:  [-2, 1, -3, 4, -1, 2, 1, -5, 4]
                    └────────┘
Output: 6  (subarray [4, -1, 2, 1])
```

### Why This Matters
This pattern appears in:
- Stock trading (max profit in a time window)
- Signal processing (strongest signal period)
- Data analysis (peak performance period)
- Many other real-world scenarios

---

## 3. Intuition & Mental Model <a name="intuition"></a>

### The Naïve Approach (Brute Force)

```
Check EVERY possible subarray:

Array: [a, b, c, d]

Subarrays:
[a]           sum = a
[a,b]         sum = a+b
[a,b,c]       sum = a+b+c
[a,b,c,d]     sum = a+b+c+d
[b]           sum = b
[b,c]         sum = b+c
[b,c,d]       sum = b+c+d
[c]           sum = c
[c,d]         sum = c+d
[d]           sum = d

Total: n(n+1)/2 subarrays → O(n²) time
```

### The Key Insight (Kadane's Breakthrough)

**Question**: At each position, should we extend the current subarray or start fresh?

```
Visual Decision Making:
═══════════════════════════

Current position: arr[i]
Current subarray sum: current_sum

Decision Point:
┌─────────────────────────────────┐
│ current_sum + arr[i]            │ ← Extend current subarray
│         vs                       │
│ arr[i]                          │ ← Start new subarray
└─────────────────────────────────┘
         Choose MAX

Why? If current_sum is negative, it drags us down!
Better to start fresh from current element.
```

### The Mental Model: "Water Flowing Downhill"

```
Array:  [5, -3, 5, -2, 4]
         ↓   ↓  ↓   ↓  ↓

Think of positive numbers as uphill slopes
and negative numbers as downhill slopes:

     5
    ╱ ╲
   ╱   ╲-3
  ╱     ╲   5
 ╱       ╲ ╱ ╲
╱         ╲   ╲-2  4
           ╲   ╲ ╱╲
            ╲   ╱  ╲
             ╲ ╱    ╲

If water level (cumulative sum) goes below zero,
"drain it" and start collecting fresh water.
```

---

## 4. Mathematical Foundation <a name="mathematical-foundation"></a>

### Formal Definition

Let `f(i)` = maximum sum of subarray ending at index `i`

**Recurrence Relation**:
```
f(i) = max(arr[i], f(i-1) + arr[i])
       └──────┘  └──────────────┘
       start     extend current
       fresh     subarray

Base case: f(0) = arr[0]
```

**Answer**: `max(f(0), f(1), f(2), ..., f(n-1))`

### Proof of Correctness

**Claim**: For any position `i`, the maximum subarray ending at `i` is either:
1. Just `arr[i]` itself, OR
2. `arr[i]` added to the maximum subarray ending at `i-1`

**Proof by Contradiction**:
Suppose there's a better subarray ending at `i` that doesn't fit these cases.
- If it doesn't include `arr[i]`, it doesn't "end" at `i` → contradiction
- If it includes elements before `i`, it must connect through `i-1`
- If connecting through `i-1` is worse than starting fresh, we proved f(i-1) < 0
- Therefore, f(i) = max(arr[i], f(i-1) + arr[i]) is optimal ∎

---

## 5. Algorithm Deep Dive <a name="algorithm-deep-dive"></a>

### The Core Algorithm

```
KADANE'S ALGORITHM
══════════════════

Initialize:
  current_max = arr[0]    ← Best sum ending at current position
  global_max = arr[0]     ← Best sum seen so far

For each element arr[i] from index 1 to n-1:
  ┌─────────────────────────────────────────┐
  │ Decision: Extend or Start Fresh?        │
  │                                          │
  │ current_max = max(arr[i],                │
  │                   current_max + arr[i])  │
  │                                          │
  │ Update global best:                     │
  │ global_max = max(global_max, current_max)│
  └─────────────────────────────────────────┘

Return global_max
```

### Step-by-Step Execution Trace

```
Array: [-2, 1, -3, 4, -1, 2, 1, -5, 4]

i=0: arr[0]=-2
     current_max = -2
     global_max = -2
     ┌───┐
     │-2 │
     └───┘

i=1: arr[1]=1
     current_max = max(1, -2+1) = max(1, -1) = 1  ← Start fresh!
     global_max = max(-2, 1) = 1
         ┌───┐
         │ 1 │
         └───┘

i=2: arr[2]=-3
     current_max = max(-3, 1+(-3)) = max(-3, -2) = -2  ← Extend (least bad)
     global_max = max(1, -2) = 1
         ┌────────┐
         │ 1  -3  │
         └────────┘

i=3: arr[3]=4
     current_max = max(4, -2+4) = max(4, 2) = 4  ← Start fresh!
     global_max = max(1, 4) = 4
                 ┌───┐
                 │ 4 │
                 └───┘

i=4: arr[4]=-1
     current_max = max(-1, 4+(-1)) = max(-1, 3) = 3  ← Extend
     global_max = max(4, 3) = 4
                 ┌────────┐
                 │ 4  -1  │
                 └────────┘

i=5: arr[5]=2
     current_max = max(2, 3+2) = max(2, 5) = 5  ← Extend
     global_max = max(4, 5) = 5
                 ┌─────────────┐
                 │ 4  -1   2   │
                 └─────────────┘

i=6: arr[6]=1
     current_max = max(1, 5+1) = max(1, 6) = 6  ← Extend
     global_max = max(5, 6) = 6
                 ┌──────────────────┐
                 │ 4  -1   2   1    │
                 └──────────────────┘

i=7: arr[7]=-5
     current_max = max(-5, 6+(-5)) = max(-5, 1) = 1  ← Extend
     global_max = max(6, 1) = 6
                 ┌───────────────────────┐
                 │ 4  -1   2   1   -5    │
                 └───────────────────────┘

i=8: arr[8]=4
     current_max = max(4, 1+4) = max(4, 5) = 5  ← Extend
     global_max = max(6, 5) = 6
                 ┌────────────────────────────┐
                 │ 4  -1   2   1   -5   4     │
                 └────────────────────────────┘

ANSWER: 6 (from subarray [4, -1, 2, 1])
```

### Visual Flow Chart

```
                    START
                      │
                      ▼
            ┌─────────────────────┐
            │ Initialize:         │
            │ current_max = arr[0]│
            │ global_max = arr[0] │
            └─────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │  i = 1              │
            └─────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │  i < n ?            │
            └─────────────────────┘
                  │         │
                Yes        No
                  │         │
                  ▼         └────────────┐
    ┌─────────────────────────┐          │
    │ current_max = max(      │          │
    │   arr[i],               │          │
    │   current_max + arr[i]  │          │
    │ )                       │          │
    └─────────────────────────┘          │
                  │                      │
                  ▼                      │
    ┌─────────────────────────┐          │
    │ global_max = max(       │          │
    │   global_max,           │          │
    │   current_max           │          │
    │ )                       │          │
    └─────────────────────────┘          │
                  │                      │
                  ▼                      │
    ┌─────────────────────────┐          │
    │  i = i + 1              │          │
    └─────────────────────────┘          │
                  │                      │
                  └──────────┐           │
                             │           │
                             ▼           ▼
                    ┌─────────────────────┐
                    │ Return global_max   │
                    └─────────────────────┘
                             │
                             ▼
                           END
```

---

## 6. Implementation in Rust, Python, Go <a name="implementations"></a>

### Python Implementation

```python
def kadane(arr: list[int]) -> int:
    """
    Find maximum subarray sum using Kadane's algorithm.
    
    Time Complexity: O(n) - single pass through array
    Space Complexity: O(1) - only two variables
    
    Args:
        arr: List of integers (can contain negatives)
    
    Returns:
        Maximum sum of any contiguous subarray
    """
    # Edge case: empty array
    if not arr:
        return 0
    
    # Initialize with first element
    current_max = global_max = arr[0]
    
    # Scan through rest of array
    for num in arr[1:]:
        # Key decision: extend or start fresh?
        current_max = max(num, current_max + num)
        
        # Update global best if needed
        global_max = max(global_max, current_max)
    
    return global_max


# Enhanced version with subarray tracking
def kadane_with_indices(arr: list[int]) -> tuple[int, int, int]:
    """
    Returns: (max_sum, start_index, end_index)
    """
    if not arr:
        return 0, -1, -1
    
    current_max = global_max = arr[0]
    current_start = global_start = global_end = 0
    
    for i in range(1, len(arr)):
        # If starting fresh, update start index
        if arr[i] > current_max + arr[i]:
            current_max = arr[i]
            current_start = i
        else:
            current_max = current_max + arr[i]
        
        # Update global best
        if current_max > global_max:
            global_max = current_max
            global_start = current_start
            global_end = i
    
    return global_max, global_start, global_end


# Test
arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
print(f"Max sum: {kadane(arr)}")  # 6

max_sum, start, end = kadane_with_indices(arr)
print(f"Max sum: {max_sum}")  # 6
print(f"Subarray: {arr[start:end+1]}")  # [4, -1, 2, 1]
```

### Rust Implementation

```rust
/// Find maximum subarray sum using Kadane's algorithm
/// 
/// Time Complexity: O(n)
/// Space Complexity: O(1)
pub fn kadane(arr: &[i32]) -> i32 {
    // Handle empty slice
    if arr.is_empty() {
        return 0;
    }
    
    let mut current_max = arr[0];
    let mut global_max = arr[0];
    
    // Iterate through remaining elements
    for &num in &arr[1..] {
        // Greedy decision: extend or start fresh?
        current_max = num.max(current_max + num);
        
        // Update global maximum
        global_max = global_max.max(current_max);
    }
    
    global_max
}

/// Returns (max_sum, start_index, end_index)
pub fn kadane_with_indices(arr: &[i32]) -> (i32, usize, usize) {
    if arr.is_empty() {
        return (0, 0, 0);
    }
    
    let mut current_max = arr[0];
    let mut global_max = arr[0];
    let mut current_start = 0;
    let mut global_start = 0;
    let mut global_end = 0;
    
    for i in 1..arr.len() {
        // Decide: extend or start fresh?
        if arr[i] > current_max + arr[i] {
            current_max = arr[i];
            current_start = i;
        } else {
            current_max = current_max + arr[i];
        }
        
        // Update global best
        if current_max > global_max {
            global_max = current_max;
            global_start = current_start;
            global_end = i;
        }
    }
    
    (global_max, global_start, global_end)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kadane() {
        let arr = vec![-2, 1, -3, 4, -1, 2, 1, -5, 4];
        assert_eq!(kadane(&arr), 6);
        
        let (sum, start, end) = kadane_with_indices(&arr);
        assert_eq!(sum, 6);
        assert_eq!(&arr[start..=end], &[4, -1, 2, 1]);
    }
}
```

### Go Implementation

```go
package main

import "math"

// Kadane finds maximum subarray sum
// Time: O(n), Space: O(1)
func Kadane(arr []int) int {
    // Handle empty slice
    if len(arr) == 0 {
        return 0
    }
    
    currentMax := arr[0]
    globalMax := arr[0]
    
    // Scan through array
    for i := 1; i < len(arr); i++ {
        // Greedy choice: extend or start fresh?
        currentMax = max(arr[i], currentMax + arr[i])
        
        // Update global best
        globalMax = max(globalMax, currentMax)
    }
    
    return globalMax
}

// KadaneWithIndices returns (maxSum, startIndex, endIndex)
func KadaneWithIndices(arr []int) (int, int, int) {
    if len(arr) == 0 {
        return 0, -1, -1
    }
    
    currentMax := arr[0]
    globalMax := arr[0]
    currentStart := 0
    globalStart := 0
    globalEnd := 0
    
    for i := 1; i < len(arr); i++ {
        // Decide: extend or start fresh?
        if arr[i] > currentMax + arr[i] {
            currentMax = arr[i]
            currentStart = i
        } else {
            currentMax = currentMax + arr[i]
        }
        
        // Update global best
        if currentMax > globalMax {
            globalMax = currentMax
            globalStart = currentStart
            globalEnd = i
        }
    }
    
    return globalMax, globalStart, globalEnd
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

// Example usage
func main() {
    arr := []int{-2, 1, -3, 4, -1, 2, 1, -5, 4}
    
    maxSum := Kadane(arr)
    println("Max sum:", maxSum) // 6
    
    sum, start, end := KadaneWithIndices(arr)
    println("Max sum:", sum)    // 6
    println("From index", start, "to", end)  // 3 to 6
}
```

### Performance Comparison

```
Complexity Analysis:
══════════════════

Time Complexity:  O(n)
Space Complexity: O(1)

Comparison with Brute Force:
┌─────────────┬─────────┬──────────┐
│ Approach    │ Time    │ Space    │
├─────────────┼─────────┼──────────┤
│ Brute Force │ O(n³)   │ O(1)     │
│ Prefix Sum  │ O(n²)   │ O(n)     │
│ Kadane      │ O(n)    │ O(1)     │ ✓ Optimal
└─────────────┴─────────┴──────────┘

For n = 10,000:
- Brute Force: ~1 trillion operations
- Kadane:      ~10,000 operations
                └─ 100 million times faster!
```

---

## 7. Variations & Extensions <a name="variations"></a>

### Variation 1: Minimum Subarray Sum

```
Problem: Find minimum sum subarray

Solution: Apply Kadane but reverse the logic!

def min_kadane(arr):
    current_min = global_min = arr[0]
    
    for num in arr[1:]:
        # Choose MINIMUM instead of maximum
        current_min = min(num, current_min + num)
        global_min = min(global_min, current_min)
    
    return global_min

Visual:
Array: [3, -4, 2, -3, -1, 7, -5]
        ↓   ↓  ↓   ↓   ↓  ↓   ↓
We're looking for the deepest valley!

        3
       / \
      /   \  2
     /    -4 \
    /         \ -3
   /           \-1   7
  /               \ / \
                   /   -5

Min = -8 (subarray [-4, 2, -3, -1])
```

### Variation 2: Maximum Circular Subarray

```
Problem: Array is circular (last element connects to first)

Array: [5, -3, 5]  could be: [5, -3, 5] OR [-3, 5, 5] OR [5, 5, -3]

Circular visualization:
        5
       ╱ ╲
     -3   5
      ╲ ╱
       ●  ← They connect!

Solution Strategy:
Two cases:
1. Max subarray doesn't wrap around → Normal Kadane
2. Max subarray wraps around → Total sum - Min subarray

      [a, b, c, d, e]
       └────┘   └──┘
       include  include
         (wraps around)
         
      = Total - [  b, c  ]
                └────────┘
              (middle excluded part)
```

```python
def max_circular_subarray(arr):
    n = len(arr)
    
    # Case 1: Normal Kadane (no wrap)
    max_kadane_result = kadane(arr)
    
    # Case 2: Wrap around
    # Find minimum subarray, subtract from total
    total_sum = sum(arr)
    min_subarray = min_kadane(arr)
    max_wrap = total_sum - min_subarray
    
    # Edge case: all negative (would choose empty subarray)
    if max_wrap == 0:
        return max_kadane_result
    
    return max(max_kadane_result, max_wrap)

# Example
arr = [5, -3, 5]
print(max_circular_subarray(arr))  # 10 ([5, 5] wrapping around)
```

### Variation 3: K-Concatenation Maximum Sum

```
Problem: Array is concatenated k times. Find max subarray.

Array: [1, -2, 1]
k=3: [1, -2, 1, 1, -2, 1, 1, -2, 1]

Strategy:
Consider 3 cases:
1. Max in first copy
2. Max in last copy  
3. Max spanning multiple copies (if total sum > 0)

If total_sum > 0:
  answer = max(prefix_max, suffix_max) + (k-2) * total_sum
```

### Variation 4: Maximum Product Subarray

```
Problem: Find maximum PRODUCT (not sum) of subarray

Array: [2, 3, -2, 4]

Why is this different?
- Negative × Negative = Positive!
- We need to track BOTH max and min

Example:
[2, 3, -2, 4]
 ↓  ↓   ↓  ↓

At -2: 
  max_so_far = 6
  min_so_far = 2
  
  New candidates:
  - Just -2
  - 6 × -2 = -12  ← This is now our MIN
  - 2 × -2 = -4
  
  At next element (4):
  - -12 × 4 = -48
  - -4 × 4 = -16
  - 4
  
  The minimum (-12) becomes valuable!
```

```python
def max_product_subarray(arr):
    if not arr:
        return 0
    
    # Track both max and min (for negative numbers)
    max_prod = min_prod = result = arr[0]
    
    for num in arr[1:]:
        # Save current max (it might be overwritten)
        temp_max = max_prod
        
        # Update max (consider swapping with min due to negative)
        max_prod = max(num, max_prod * num, min_prod * num)
        
        # Update min
        min_prod = min(num, temp_max * num, min_prod * num)
        
        # Update global result
        result = max(result, max_prod)
    
    return result
```

---

## 8. Advanced Patterns <a name="advanced-patterns"></a>

### Pattern 1: Kadane with Constraints

**Problem**: Maximum sum with at most k elements

```python
def max_sum_k_elements(arr, k):
    """
    Find maximum sum subarray with at most k elements
    
    Approach: Use sliding window + tracking
    """
    n = len(arr)
    max_sum = float('-inf')
    
    # Try all window sizes from 1 to k
    for size in range(1, min(k + 1, n + 1)):
        window_sum = sum(arr[:size])
        max_sum = max(max_sum, window_sum)
        
        for i in range(size, n):
            window_sum += arr[i] - arr[i - size]
            max_sum = max(max_sum, window_sum)
    
    return max_sum
```

### Pattern 2: Maximum Sum with Exactly One Deletion

```
Problem: Find max subarray sum after deleting at most 1 element

Array: [1, -2, 0, 3]
Options:
- No deletion: [3] → 3
- Delete -2: [1, 0, 3] → 4 ✓ Best

Strategy: Track TWO states at each position
1. max_no_delete[i] = max sum ending at i with no deletions
2. max_one_delete[i] = max sum ending at i with one deletion
```

```python
def max_sum_one_deletion(arr):
    n = len(arr)
    if n == 0:
        return 0
    if n == 1:
        return max(0, arr[0])
    
    # max_no_del[i] = max sum ending at i, 0 deletions used
    # max_one_del[i] = max sum ending at i, 1 deletion used
    max_no_del = arr[0]
    max_one_del = 0  # Can delete first element
    result = max(arr[0], 0)
    
    for i in range(1, n):
        # With one deletion: either
        # 1. Extend previous one-deletion subarray
        # 2. Delete current element (extend no-deletion)
        max_one_del = max(
            max_one_del + arr[i],    # Extend with deletion used
            max_no_del               # Delete current, use previous
        )
        
        # No deletion: normal Kadane
        max_no_del = max(arr[i], max_no_del + arr[i])
        
        result = max(result, max_no_del, max_one_del)
    
    return result
```

### Pattern 3: Maximum Sum Subarray with Sliding Window

```
Problem: Maximum sum subarray of length EXACTLY k

This becomes a pure sliding window problem!

def max_sum_fixed_window(arr, k):
    n = len(arr)
    if n < k:
        return 0
    
    # Initial window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, n):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

Visual:
Array: [1, 4, 2, 10, 2, 3, 1, 0, 20]  k=4

Step 1: [1,4,2,10] → sum=17
         └──────┘
         
Step 2:  [4,2,10,2] → sum=18
           └──────┘
           
Step 3:   [2,10,2,3] → sum=17
             └──────┘
             
And so on...
```

---

## 9. Problem-Solving Framework <a name="framework"></a>

### Mental Checklist for Kadane-Style Problems

```
┌─────────────────────────────────────────────────────┐
│ RECOGNITION PATTERNS                                 │
├─────────────────────────────────────────────────────┤
│ ✓ Keywords: "maximum/minimum", "subarray",          │
│   "contiguous"                                       │
│ ✓ Need to find: optimal sum/product in sequence     │
│ ✓ Looking for: range [i, j] with best property      │
│ ✓ Constraints: elements can be negative             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ DECISION TREE                                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│      Is it about contiguous elements?                │
│               ╱        ╲                             │
│             YES         NO                           │
│              │           └→ Not Kadane pattern       │
│              ▼                                       │
│      Are you maximizing/minimizing?                  │
│               ╱        ╲                             │
│             YES         NO                           │
│              │           └→ Different approach       │
│              ▼                                       │
│      Sum or Product?                                 │
│         ╱        ╲                                   │
│       SUM      PRODUCT                               │
│        │          └→ Track max AND min               │
│        ▼                                             │
│   Standard Kadane!                                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### The Expert's Thought Process

```
Step 1: UNDERSTAND THE CONSTRAINT SPACE
═══════════════════════════════════════

Q1: What makes a subarray "valid"?
    - Contiguous? ✓
    - Fixed length? (→ sliding window)
    - At most k elements? (→ modified approach)
    - Can delete elements? (→ DP states)

Q2: What are we optimizing?
    - Sum? → Standard Kadane
    - Product? → Track min/max
    - Count? → Different technique

Step 2: IDENTIFY THE DECISION POINT
════════════════════════════════════

At each position i, ask:
"What's the optimal way to END a subarray here?"

Options:
A. Start fresh from arr[i]
B. Extend previous subarray

Step 3: STATE TRANSITION
════════════════════════

Define: f(i) = best result ending at position i

Standard: f(i) = max(arr[i], f(i-1) + arr[i])

With constraint: 
  f(i, state) = max over valid transitions

Step 4: TRACK GLOBAL OPTIMUM
═════════════════════════════

answer = max(f(0), f(1), ..., f(n-1))

Don't forget to update this!
```

### Common Pitfalls & Debugging

```
PITFALL #1: Forgetting to update global_max
───────────────────────────────────────────
❌ Wrong:
   current_max = max(arr[i], current_max + arr[i])
   # Forgot to update global_max!

✓ Correct:
   current_max = max(arr[i], current_max + arr[i])
   global_max = max(global_max, current_max)


PITFALL #2: Wrong initialization
─────────────────────────────────
❌ Wrong:
   global_max = 0  # What if all numbers are negative?

✓ Correct:
   global_max = arr[0]


PITFALL #3: Off-by-one with indices
────────────────────────────────────
When tracking subarray bounds:
- Remember: Python uses [start:end+1] for slicing
- Rust uses [start..=end] for inclusive range
- Go uses [start:end+1]


PITFALL #4: Integer overflow
─────────────────────────────
In languages like C++/Java/Rust:
- Be careful with i32::MAX + positive number
- Consider using i64 for intermediate sums
```

---

## 10. Practice Problems <a name="practice"></a>

### Level 1: Foundation

**Problem 1: Basic Kadane**
```
Input: [5, 4, -1, 7, 8]
Output: 23

Solution approach:
- Pure Kadane application
- No tricks needed
```

**Problem 2: All Negative**
```
Input: [-2, -3, -1, -4]
Output: -1  (single element)

Key insight: Best is "least negative"
```

### Level 2: Variations

**Problem 3: Maximum Circular Subarray**
```
Input: [1, -2, 3, -2]
Output: 3

Cases to consider:
1. Normal: [3] → 3
2. Wrap: [3, -2, 1] → 2
3. Full circle: sum(arr) → 0

Answer: max(case1, case2) = 3
```

**Problem 4: Maximum Product Subarray**
```
Input: [2, 3, -2, 4]
Output: 6  (subarray [2, 3])

Watch out for:
- Negatives × Negatives
- Zeros reset everything
```

### Level 3: Advanced

**Problem 5: Maximum Sum with At Most K Operations**
```
You can flip the sign of at most k elements.
Find maximum subarray sum.

Input: [-1, -2, 3, 4], k = 2
Output: 10  (flip -1 and -2 → [1, 2, 3, 4])

Approach:
- DP with state: f(i, flips_used)
- Transition: flip or don't flip current element
```

**Problem 6: Maximum Alternating Subarray**
```
Find max sum where elements alternate positive/negative

Input: [4, -5, 4, -5, 9, -9, 3]
Output: 12  ([4, -5, 4, -5, 9, -9, 3])

Insight:
Track two states:
- ending_positive[i]
- ending_negative[i]
```

---

## Mastery Roadmap

```
LEVEL 1: FOUNDATION (Week 1-2)
═══════════════════════════════
□ Understand why greedy works here
□ Implement basic Kadane in all 3 languages
□ Solve 10 standard max subarray problems
□ Debug without looking at solution

LEVEL 2: VARIATIONS (Week 3-4)
═══════════════════════════════
□ Circular subarray
□ Product instead of sum
□ With constraints (length, deletions)
□ Minimum subarray
□ Practice recognizing pattern in new problems

LEVEL 3: SYNTHESIS (Week 5-6)
══════════════════════════════
□ Combine with other techniques:
  - Kadane + Binary Search
  - Kadane + Hashing
  - Kadane + DP
□ Create your own variations
□ Teach the concept to someone else

LEVEL 4: MASTERY (Ongoing)
═══════════════════════════
□ Solve in 5 min with eyes closed
□ Generate new problem variations
□ Recognize in interview settings
□ Optimize for specific constraints
```

---

## Key Takeaways

```
┌──────────────────────────────────────────┐
│ THE CORE INSIGHT                         │
├──────────────────────────────────────────┤
│ At each position, locally optimal        │
│ choice (extend or start fresh)           │
│ leads to globally optimal solution.      │
│                                           │
│ Why? Because negative cumulative         │
│ sums only drag us down.                  │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ THE MENTAL MODEL                         │
├──────────────────────────────────────────┤
│ "Am I better off with what I have,       │
│  or should I abandon it and start over?" │
│                                           │
│ Life lesson: Sunk cost fallacy!          │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ THE PATTERN                              │
├──────────────────────────────────────────┤
│ 1. State: "best ending here"             │
│ 2. Transition: extend vs start fresh     │
│ 3. Answer: max over all positions        │
└──────────────────────────────────────────┘
```

---

**Remember**: True mastery comes from:
1. **Understanding WHY** it works (proof)
2. **Recognizing WHEN** to apply it (pattern matching)
3. **Adapting HOW** for variations (problem transformation)

Keep practicing with the monk's mindset: focused, deliberate, and deeply engaged. Each problem is a meditation on the pattern.

# **Kadane-Style Greedy: From First Principles to Mastery**

I'll guide you through the Kadane-Style Greedy approach as a **foundational algorithmic pattern** that will sharpen your problem-solving intuition. This technique is elegant, powerful, and appears in countless variations.## Your Path to Kadane Mastery

I've created a comprehensive guide that builds from first principles to advanced applications. Here's how to approach this material with a monk's discipline:

### 🧘 **Study Strategy** (Deliberate Practice Framework)

**Week 1-2: Deep Understanding Phase**
- **Morning** (30 min): Read one section deeply. Hand-trace the algorithm on paper with your own examples
- **Afternoon** (45 min): Implement in all three languages (Rust, Python, Go) without looking at the code
- **Evening** (15 min): Reflect on what clicked and what still feels unclear

**Week 3-4: Pattern Recognition**
- Solve 2-3 problems daily
- Before coding, spend 5 minutes asking: "Is this Kadane? What's the decision point?"
- After solving, identify: "What variation was this? What made it different?"

**Week 5+: Synthesis & Teaching**
- Create your own variations
- Explain to someone (even a rubber duck) why the greedy choice works
- Challenge yourself: "Can I solve this in a different way?"

### 🧠 **Cognitive Principles at Play**

1. **Chunking**: The guide breaks Kadane into "decision at each step" → "track local vs global" → "pattern variations"
   
2. **Mental Models**: Think of it as "water flowing downhill" or "sunk cost decision making"

3. **Interleaving**: Don't master Python implementation before moving to Rust. Switch between languages to strengthen understanding

4. **Retrieval Practice**: Close the guide and reconstruct the algorithm from memory. This builds permanent neural pathways.

### 🎯 **Key Mental Models to Internalize**

**The Local-to-Global Principle**
```
Every position asks: "What's optimal ending HERE?"
Global optimum = max of all local optima
This generalizes beyond Kadane!
```

**The Greedy Choice Property**
```
"When does local optimal → global optimal?"
Answer: When no future decision benefits from 
        a suboptimal current choice
```

### 📊 **Progress Tracking**

After each problem, rate yourself (1-5) on:
- ✓ Recognition (Did I see it was Kadane?)
- ✓ Implementation (Could I code it cleanly?)
- ✓ Optimization (Did I find the O(n) solution first try?)
- ✓ Variation (Did I identify the twist?)

Track in a simple log. Watch these scores trend upward over 2-3 weeks.

### 💡 **When You're Stuck**

1. **Draw it**: Visualize the array and cumulative sums
2. **Simplify**: Try with array of 3 elements
3. **Ask**: "What's the decision at position i?"
4. **Connect**: "How is this similar to a problem I've solved?"

### 🔥 **Advanced Challenge** (After Week 4)

Implement a **generalized Kadane framework** that handles:
- Sum/Product/Custom operation
- Min/Max
- Fixed/Variable length
- With/Without constraints

This meta-implementation will cement your understanding at the architectural level.

---

**Remember**: You're not just learning an algorithm—you're developing the intuition to recognize **when local greedy choices compound into optimal solutions**. This pattern appears everywhere from dynamic programming to graph algorithms to system design.

Approach each section with **beginner's mind** but **expert's rigor**. The mastery is in the details and the connections.

What section would you like to dive deeper into first? Or shall we tackle a specific problem together to see the thought process in action?