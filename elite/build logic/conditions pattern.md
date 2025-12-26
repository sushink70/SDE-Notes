# DSA Patterns Compendium: The Complete Guide

## Your Systematic Path to Top 1% Problem-Solving Mastery

---

## Table of Contents

1. [Array & String Patterns](#array--string-patterns)
2. [Two Pointers & Sliding Window](#two-pointers--sliding-window)
3. [Hashing & Frequency Patterns](#hashing--frequency-patterns)
4. [Prefix Sum & Difference Arrays](#prefix-sum--difference-arrays)
5. [Sorting & Binary Search](#sorting--binary-search)
6. [Stack & Monotonic Stack](#stack--monotonic-stack)
7. [Queue & Deque Patterns](#queue--deque-patterns)
8. [Linked List Patterns](#linked-list-patterns)
9. [Tree Traversal Patterns](#tree-traversal-patterns)
10. [Binary Search Tree Patterns](#binary-search-tree-patterns)
11. [Heap & Priority Queue](#heap--priority-queue)
12. [Graph Traversal (DFS/BFS)](#graph-traversal-dfsbfs)
13. [Dynamic Programming Patterns](#dynamic-programming-patterns)
14. [Backtracking & Recursion](#backtracking--recursion)
15. [Greedy Algorithms](#greedy-algorithms)
16. [Bit Manipulation](#bit-manipulation)
17. [Mathematical & Number Theory](#mathematical--number-theory)
18. [Advanced Patterns](#advanced-patterns)

---

## Mental Framework: How to Approach ANY Problem

```ascii
┌─────────────────────────────────────────────────────────┐
│  PROBLEM ANALYSIS PIPELINE (Master This Flow)           │
├─────────────────────────────────────────────────────────┤
│  1. UNDERSTAND: What exactly is being asked?            │
│     - Input format & constraints                        │
│     - Output requirements                               │
│     - Edge cases (empty, single element, duplicates)    │
│                                                         │
│  2. PATTERN RECOGNITION: What category?                 │
│     - Sequential access? → Arrays/Strings               │
│     - Searching/Ordering? → Binary Search/Sorting       │
│     - Combinations/Subsets? → Backtracking              │
│     - Optimization? → DP or Greedy                      │
│     - Graph/Tree structure? → DFS/BFS                   │
│                                                         │
│  3. BRUTE FORCE FIRST: Always have a baseline           │
│     - Time: Usually O(n²) or O(n³)                      │
│     - Space: Often O(1) or O(n)                         │
│                                                         │
│  4. OPTIMIZE: Apply patterns to reduce complexity       │
│     - Can we avoid recalculation? → Hashing/Memoization │
│     - Can we reduce search space? → Binary Search       │
│     - Can we reuse computation? → DP                    │
│                                                         │
│  5. IMPLEMENT: Write clean, tested code                 │
│  6. VERIFY: Test edge cases & complexity                │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Array & String Patterns

### Pattern 1.1: Index Manipulation & Bounds Handling

**Core Concept**: Arrays are contiguous memory blocks accessed by index (0 to n-1). Understanding index arithmetic is foundational.

**When to Use**:

- Accessing elements relative to current position
- Rotating or reversing arrays
- Partitioning problems

**Key Techniques**:

```ascii
Forward iteration:   for i in 0..n
Backward iteration:  for i in (0..n).rev()
Two directions:      start=0, end=n-1, meet in middle
Circular access:     (i + k) % n
```

**Time Complexity**: O(n) for single pass, O(1) for access
**Space Complexity**: O(1) if in-place

**Mental Model**: Think of array as a ruler with positions. Index arithmetic is like measuring distances.

```python
# Python: In-place reversal (fundamental technique)
def reverse_array(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

# Time: O(n), Space: O(1)
```

```rust
// Rust: In-place reversal (ownership & borrowing)
fn reverse_array(arr: &mut [i32]) {
    let mut left = 0;
    let mut right = arr.len() - 1;
    while left < right {
        arr.swap(left, right);
        left += 1;
        right -= 1;
    }
}
```

```go
// Go: In-place reversal (slice manipulation)
func reverseArray(arr []int) {
    left, right := 0, len(arr)-1
    for left < right {
        arr[left], arr[right] = arr[right], arr[left]
        left++
        right--
    }
}
```

---

### Pattern 1.2: Kadane's Algorithm (Maximum Subarray)

**Core Concept**: A **subarray** is a contiguous portion of an array. This pattern finds the maximum sum among all possible subarrays.

**Mental Model**: At each position, decide: "Should I extend my current subarray or start fresh?"

**Key Insight**: If current sum becomes negative, it can't help future sums, so reset.

```ascii
Array: [-2, 1, -3, 4, -1, 2, 1, -5, 4]

Step-by-step thinking:
Position 0: current = -2, max = -2
Position 1: current = 1 (start fresh), max = 1
Position 2: current = -2, max = 1
Position 3: current = 4 (start fresh), max = 4
Position 4: current = 3, max = 4
Position 5: current = 5, max = 5
Position 6: current = 6, max = 6  ← Answer
```

**Time**: O(n), **Space**: O(1)

```python
def max_subarray(nums):
    current_sum = max_sum = nums[0]
    
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    
    return max_sum
```

**Variations**:

- Return the subarray itself (track indices)
- Find minimum subarray sum (invert logic)
- Circular array (consider wrap-around)

---

## 2. Two Pointers & Sliding Window

### Pattern 2.1: Two Pointers (Opposite Directions)

**Core Concept**: Two pointers start at opposite ends and move toward each other. Used when array is sorted or you need to compare pairs.

**Visual**:

```ascii
[1, 2, 3, 4, 5, 6, 7, 8]
 ↑                    ↑
left               right
```

**When to Use**:

- Finding pairs with specific sum
- Removing duplicates
- Container problems (trapping water)

**Mental Model**: Two scouts exploring from both ends, meeting in the middle.

```python
# Two Sum (Sorted Array)
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    
    while left < right:
        current_sum = nums[left] + nums[right]
        
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1  # Need larger sum
        else:
            right -= 1  # Need smaller sum
    
    return [-1, -1]

# Time: O(n), Space: O(1)
```

```rust
// Rust: Remove duplicates from sorted array
fn remove_duplicates(nums: &mut Vec<i32>) -> usize {
    if nums.is_empty() { return 0; }
    
    let mut write_idx = 1;  // Position to write next unique element
    
    for read_idx in 1..nums.len() {
        if nums[read_idx] != nums[read_idx - 1] {
            nums[write_idx] = nums[read_idx];
            write_idx += 1;
        }
    }
    
    write_idx  // New length
}
```

---

### Pattern 2.2: Sliding Window (Fixed & Variable Size)

**Core Concept**: A **window** is a range [left, right] in an array. We "slide" this window to examine all ranges efficiently.

**Types**:

1. **Fixed Size**: Window size k is constant
2. **Variable Size**: Window expands/contracts based on conditions

**Visual (Fixed Window of size 3)**:

```ascii
[1, 3, 5, 2, 8, 4, 6]
[1, 3, 5]        ← Window 1, sum = 9
   [3, 5, 2]     ← Window 2, sum = 10
      [5, 2, 8]  ← Window 3, sum = 15
```

**Mental Model**: Imagine a physical sliding window. When moving right:

- Add new element on right
- Remove old element on left

**Fixed Size Window Template**:

```python
def fixed_window(arr, k):
    # Initialize first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, len(arr)):
        window_sum = window_sum - arr[i-k] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

# Time: O(n), Space: O(1)
```

**Variable Size Window Template** (Most Important!):

```python
def variable_window(arr, condition):
    left = 0
    result = 0
    
    for right in range(len(arr)):
        # Expand window by including arr[right]
        # Update window state
        
        while condition_violated():
            # Shrink window from left
            # Update window state
            left += 1
        
        # Update result with current valid window
        result = max(result, right - left + 1)
    
    return result
```

**Example: Longest Substring Without Repeating Characters**

```python
def longest_unique_substring(s):
    char_set = set()
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Expand: Add s[right] to window
        while s[right] in char_set:
            # Shrink: Remove s[left] until no duplicate
            char_set.remove(s[left])
            left += 1
        
        char_set.add(s[right])
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Time: O(n), Space: O(min(n, alphabet_size))
```

```go
// Go: Minimum Window Substring (Advanced)
func minWindow(s string, t string) string {
    if len(s) == 0 || len(t) == 0 {
        return ""
    }
    
    // Frequency map for target string
    need := make(map[byte]int)
    for i := 0; i < len(t); i++ {
        need[t[i]]++
    }
    
    left, right := 0, 0
    matched := 0  // Characters matched
    minLen := len(s) + 1
    minStart := 0
    window := make(map[byte]int)
    
    for right < len(s) {
        // Expand window
        c := s[right]
        window[c]++
        if window[c] == need[c] {
            matched++
        }
        right++
        
        // Shrink window when valid
        for matched == len(need) {
            // Update result
            if right - left < minLen {
                minLen = right - left
                minStart = left
            }
            
            // Shrink from left
            d := s[left]
            window[d]--
            if window[d] < need[d] {
                matched--
            }
            left++
        }
    }
    
    if minLen == len(s) + 1 {
        return ""
    }
    return s[minStart : minStart + minLen]
}
```

**Pattern Recognition for Sliding Window**:

- Keywords: "subarray", "substring", "consecutive elements"
- "Maximum/minimum of size k" → Fixed window
- "Longest/shortest satisfying condition" → Variable window

---

## 3. Hashing & Frequency Patterns

### Pattern 3.1: Hash Map for O(1) Lookup

**Core Concept**: A **hash map** (dictionary/map) stores key-value pairs with average O(1) access. Trade space for time.

**When to Use**:

- Need to check if element exists quickly
- Count frequencies
- Store computed results (memoization)
- Find complements or pairs

**Mental Model**: Like a filing cabinet with instant access to any folder by its label.

```python
# Two Sum (Unsorted Array)
def two_sum(nums, target):
    seen = {}  # value -> index
    
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    
    return [-1, -1]

# Time: O(n), Space: O(n)
# Without hash map: O(n²) time, O(1) space
```

```rust
// Rust: Using HashMap from std::collections
use std::collections::HashMap;

fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
    let mut map = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        if let Some(&idx) = map.get(&complement) {
            return vec![idx as i32, i as i32];
        }
        map.insert(num, i);
    }
    
    vec![-1, -1]
}
```

---

### Pattern 3.2: Frequency Counter

**Core Concept**: Count occurrences of each element to identify patterns.

**Applications**:

- Find most/least frequent element
- Detect duplicates
- Check if two strings are anagrams
- Sliding window with character constraints

```python
from collections import Counter

# Check if two strings are anagrams
def is_anagram(s, t):
    return Counter(s) == Counter(t)

# Or manually:
def is_anagram_manual(s, t):
    if len(s) != len(t):
        return False
    
    freq = {}
    for char in s:
        freq[char] = freq.get(char, 0) + 1
    
    for char in t:
        if char not in freq:
            return False
        freq[char] -= 1
        if freq[char] < 0:
            return False
    
    return True
```

**Advanced: Top K Frequent Elements**

```python
from collections import Counter
import heapq

def top_k_frequent(nums, k):
    # Method 1: Using Counter + Heap
    freq = Counter(nums)
    return [num for num, _ in freq.most_common(k)]
    
    # Method 2: Bucket Sort (O(n) time)
    freq = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]
    
    for num, count in freq.items():
        buckets[count].append(num)
    
    result = []
    for i in range(len(buckets) - 1, -1, -1):
        result.extend(buckets[i])
        if len(result) >= k:
            return result[:k]
    
    return result

# Heap: O(n log k), Bucket: O(n)
```

---

## 4. Prefix Sum & Difference Arrays

### Pattern 4.1: Prefix Sum

**Core Concept**: A **prefix sum** array stores cumulative sums. `prefix[i]` = sum of elements from index 0 to i.

**Why It's Powerful**: Calculate sum of any subarray in O(1) time.

**Formula**: `sum(i, j) = prefix[j] - prefix[i-1]`

**Visual**:

```ascii
Array:     [3, 1, 4, 1, 5, 9]
Prefix:    [3, 4, 8, 9, 14, 23]
           
Sum(2,4) = prefix[4] - prefix[1] = 14 - 4 = 10
Check:     4 + 1 + 5 = 10 ✓
```

**Time**: O(n) to build, O(1) per query
**Space**: O(n)

```python
def build_prefix_sum(arr):
    prefix = [0] * (len(arr) + 1)  # Extra space for easier calculation
    for i in range(len(arr)):
        prefix[i + 1] = prefix[i] + arr[i]
    return prefix

def range_sum(prefix, left, right):
    return prefix[right + 1] - prefix[left]

# Example: Subarray Sum Equals K
def subarray_sum(nums, k):
    count = 0
    current_sum = 0
    sum_freq = {0: 1}  # Base case
    
    for num in nums:
        current_sum += num
        
        # Check if (current_sum - k) exists
        if current_sum - k in sum_freq:
            count += sum_freq[current_sum - k]
        
        sum_freq[current_sum] = sum_freq.get(current_sum, 0) + 1
    
    return count

# Time: O(n), Space: O(n)
```

---

### Pattern 4.2: Difference Array (Range Updates)

**Core Concept**: A **difference array** efficiently handles multiple range updates.

**Problem**: Given an array, perform m updates of type "add value v to range [l, r]".

**Naive vs Difference Array**:

- Naive: O(n) per update → O(mn) total
- Difference array: O(1) per update + O(n) final → O(m + n)

**How It Works**:

```ascii
Original:      [0, 0, 0, 0, 0]
Add 3 to [1,3]:

Difference:    [0, +3, 0, 0, -3]
               mark start   mark end+1

After prefix sum of difference:
Result:        [0, 3, 3, 3, 0]
```

```python
def range_updates(n, updates):
    """
    n: array size
    updates: list of (left, right, value)
    """
    diff = [0] * (n + 1)
    
    # Apply all updates to difference array
    for left, right, val in updates:
        diff[left] += val
        diff[right + 1] -= val
    
    # Compute final array using prefix sum
    result = [0] * n
    result[0] = diff[0]
    for i in range(1, n):
        result[i] = result[i-1] + diff[i]
    
    return result

# Time: O(m + n), Space: O(n)
```

**Mental Model**: Think of it as marking "gates" where values change. The prefix sum then "propagates" the changes.

---

## 5. Sorting & Binary Search

### Pattern 5.1: Custom Sorting

**Core Concept**: Sometimes you need to sort by custom criteria, not just value.

**Applications**:

- Sort intervals by start/end time
- Sort by multiple keys
- Stable vs unstable sorting

```python
# Sort intervals by start time, then by end time
intervals = [[1,4], [2,3], [1,2]]
intervals.sort(key=lambda x: (x[0], x[1]))
# Result: [[1,2], [1,4], [2,3]]

# Sort strings by length, then lexicographically
words = ["apple", "pie", "a", "zoo"]
words.sort(key=lambda x: (len(x), x))
# Result: ['a', 'pie', 'zoo', 'apple']
```

```rust
// Rust: Custom sorting with closures
let mut intervals = vec![[1,4], [2,3], [1,2]];
intervals.sort_by(|a, b| {
    a[0].cmp(&b[0])
        .then(a[1].cmp(&b[1]))
});
```

**Time Complexity**: O(n log n) for comparison-based sorting

---

### Pattern 5.2: Binary Search (The Most Important Search Pattern)

**Core Concept**: Search in sorted space by repeatedly halving the search range.

**Prerequisite**: Array must be sorted (or search space has monotonic property)

**Visual**:

```ascii
[1, 3, 5, 7, 9, 11, 13, 15]   Target: 7
 L              M           R

Compare 7 with 9 (mid): 7 < 9
Search left half

[1, 3, 5, 7]
 L     M    R

Compare 7 with 5 (mid): 7 > 5
Search right half

[7]
 L/M/R

Found!
```

**Time**: O(log n), **Space**: O(1)

**Standard Binary Search Template**:

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Avoid overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1  # Search right
        else:
            right = mid - 1  # Search left
    
    return -1  # Not found
```

**Critical Details**:

1. `mid = left + (right - left) // 2` avoids integer overflow
2. Loop condition: `left <= right` (inclusive)
3. Update: `left = mid + 1` or `right = mid - 1` (exclude mid)

---

### Pattern 5.3: Binary Search Variations

**Variation 1: Find First Occurrence**

```python
def find_first(arr, target):
    left, right = 0, len(arr) - 1
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            result = mid
            right = mid - 1  # Continue searching left
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return result
```

**Variation 2: Find Insertion Position (Lower Bound)**

```python
def lower_bound(arr, target):
    """Find leftmost position where target can be inserted"""
    left, right = 0, len(arr)
    
    while left < right:  # Note: left < right, not <=
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid  # Don't exclude mid
    
    return left
```

**Variation 3: Binary Search on Answer Space**

**Mental Model**: When the answer is a value in a range, and you can verify if a value works in O(f(n)), binary search on that range.

```python
# Example: Minimum capacity to ship packages within D days
def ship_within_days(weights, days):
    def can_ship(capacity):
        days_needed = 1
        current_load = 0
        
        for weight in weights:
            if current_load + weight > capacity:
                days_needed += 1
                current_load = weight
                if days_needed > days:
                    return False
            else:
                current_load += weight
        
        return True
    
    # Binary search on capacity
    left, right = max(weights), sum(weights)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if can_ship(mid):
            right = mid  # Try smaller capacity
        else:
            left = mid + 1  # Need more capacity
    
    return left

# Time: O(n log(sum - max))
```

---

## 6. Stack & Monotonic Stack

### Pattern 6.1: Basic Stack Operations

**Core Concept**: A **stack** is a Last-In-First-Out (LIFO) data structure. Think of a stack of plates.

**Operations**:

- `push(x)`: Add element to top - O(1)
- `pop()`: Remove top element - O(1)
- `peek()`: View top element without removing - O(1)

**When to Use**:

- Backtracking problems
- Matching parentheses/brackets
- Undo operations
- Expression evaluation
- Function call stack (recursion simulation)

```python
# Valid Parentheses
def is_valid(s):
    stack = []
    pairs = {'(': ')', '[': ']', '{': '}'}
    
    for char in s:
        if char in pairs:  # Opening bracket
            stack.append(char)
        else:  # Closing bracket
            if not stack or pairs[stack.pop()] != char:
                return False
    
    return len(stack) == 0

# Time: O(n), Space: O(n)
```

---

### Pattern 6.2: Monotonic Stack (Game-Changing Pattern!)

**Core Concept**: A **monotonic stack** maintains elements in increasing or decreasing order. When a new element violates the order, we pop elements until order is restored.

**Why It's Powerful**: Solves "next greater/smaller element" problems in O(n) instead of O(n²).

**Mental Model**: Like a line of people where taller people can "see over" shorter ones. When someone taller arrives, shorter people behind them become invisible.

**Visual (Next Greater Element)**:

```
Array: [2, 1, 2, 4, 3]

Stack state at each step:
i=0: [2]
i=1: [2, 1]         (1 < 2, maintain decreasing)
i=2: [2, 2]         (1 pops, sees 2 as next greater)
i=3: [4]            (2,2 pop, see 4 as next greater)
i=4: [4, 3]
```

**Template (Next Greater Element)**:

```python
def next_greater_elements(arr):
    n = len(arr)
    result = [-1] * n
    stack = []  # Store indices
    
    for i in range(n):
        # Pop elements smaller than current
        while stack and arr[stack[-1]] < arr[i]:
            idx = stack.pop()
            result[idx] = arr[i]
        
        stack.append(i)
    
    return result

# Time: O(n) - each element pushed and popped once
# Space: O(n)
```

**Variations**:

```python
# Next Smaller Element (flip comparison)
def next_smaller_elements(arr):
    n = len(arr)
    result = [-1] * n
    stack = []
    
    for i in range(n):
        while stack and arr[stack[-1]] > arr[i]:  # Changed to >
            idx = stack.pop()
            result[idx] = arr[i]
        stack.append(i)
    
    return result

# Previous Greater Element (traverse right to left)
def prev_greater_elements(arr):
    n = len(arr)
    result = [-1] * n
    stack = []
    
    for i in range(n-1, -1, -1):  # Right to left
        while stack and arr[stack[-1]] < arr[i]:
            idx = stack.pop()
            result[idx] = arr[i]
        stack.append(i)
    
    return result
```

**Real-World Application: Largest Rectangle in Histogram**

```python
def largest_rectangle_area(heights):
    """
    Find the largest rectangle that can be formed in histogram.
    
    Key insight: For each bar, find:
    - Left boundary: previous smaller element
    - Right boundary: next smaller element
    Width = right - left - 1
    """
    stack = []
    max_area = 0
    heights.append(0)  # Sentinel to flush stack
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height_idx = stack.pop()
            height = heights[height_idx]
            
            # Width calculation
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    return max_area

# Time: O(n), Space: O(n)
```

**Pattern Recognition**:

- Keywords: "next greater", "next smaller", "previous", "span"
- Problems involving elements seeing/dominating other elements
- Rectangle/area problems with heights

---

## 7. Queue & Deque Patterns

### Pattern 7.1: Queue (FIFO)

**Core Concept**: A **queue** is First-In-First-Out (FIFO). Like a line at a store.

**Operations**:

- `enqueue(x)`: Add to back - O(1)
- `dequeue()`: Remove from front - O(1)
- `front()`: View front element - O(1)

```python
from collections import deque

# BFS uses queue (covered in Graph section)
queue = deque([1, 2, 3])
queue.append(4)      # enqueue
queue.popleft()      # dequeue → 1
```

---

### Pattern 7.2: Deque (Double-Ended Queue) & Sliding Window Maximum

**Core Concept**: A **deque** (pronounced "deck") allows O(1) insertion/deletion from both ends.

**Most Important Application**: Sliding Window Maximum

**Problem**: Given array and window size k, find maximum in each window.

**Naive**: O(nk) - check each window
**Optimal**: O(n) - using monotonic deque

**Key Insight**: Maintain deque of indices in decreasing order of values. Elements that can never be maximum are removed.

```python
from collections import deque

def sliding_window_maximum(nums, k):
    """
    Maintain deque of indices where values are in decreasing order.
    Front of deque always has index of maximum element in current window.
    """
    dq = deque()
    result = []
    
    for i in range(len(nums)):
        # Remove indices outside window
        if dq and dq[0] < i - k + 1:
            dq.popleft()
        
        # Remove indices whose values are smaller than current
        # (they can never be maximum)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

# Time: O(n) - each element enters and leaves deque once
# Space: O(k)

# Example:
# nums = [1,3,-1,-3,5,3,6,7], k = 3
# Output: [3,3,5,5,6,7]
```

**Mental Model**: The deque is like a "leaderboard" for the current window. Smaller elements get removed when they can't compete.

---

## 8. Linked List Patterns

### Pattern 8.1: Linked List Basics

**Core Concept**: A **linked list** is a sequence of nodes where each node contains data and a pointer to the next node.

**Structure**:

```ascii
Node: [data | next] -> [data | next] -> [data | next] -> None
       head
```

**Why Use It**: Dynamic size, O(1) insertion/deletion at known positions (unlike arrays)

**Python Definition**:

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

**Rust Definition**:

```rust
#[derive(Debug, Clone)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}

impl ListNode {
    fn new(val: i32) -> Self {
        ListNode { val, next: None }
    }
}
```

---

### Pattern 8.2: Fast & Slow Pointers (Floyd's Algorithm)

**Core Concept**: Two pointers move at different speeds. Fast moves 2 steps, slow moves 1 step.

**Applications**:

1. Detect cycle
2. Find middle of list
3. Find nth node from end

**Visual (Cycle Detection)**:

```ascii
1 -> 2 -> 3 -> 4 -> 5
          ↑         ↓
          8 <- 7 <- 6

Slow: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
Fast: 1 -> 3 -> 5 -> 7 -> 3 -> 7
                                ↑
                          Meet at 7 (cycle exists!)
```

```python
def has_cycle(head):
    if not head or not head.next:
        return False
    
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        
        if slow == fast:
            return True
    
    return False

# Time: O(n), Space: O(1)
```

**Find Middle**:

```python
def find_middle(head):
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow  # When fast reaches end, slow is at middle

# Time: O(n), Space: O(1)
```

---

### Pattern 8.3: Reversal

**Core Concept**: Reverse pointers direction iteratively.

**Visual**:

```ascii
Original: 1 -> 2 -> 3 -> 4 -> None

Step 1:   None <- 1    2 -> 3 -> 4 -> None
          prev  curr  next

Step 2:   None <- 1 <- 2    3 -> 4 -> None
                prev  curr  next

Final:    None <- 1 <- 2 <- 3 <- 4
                              prev (new head)
```

```python
def reverse_list(head):
    prev = None
    current = head
    
    while current:
        next_node = current.next  # Save next
        current.next = prev       # Reverse pointer
        prev = current            # Move prev forward
        current = next_node       # Move current forward
    
    return prev  # New head

# Time: O(n), Space: O(1)
```

**Reverse in Groups**:

```python
def reverse_k_group(head, k):
    """Reverse nodes in groups of k"""
    def reverse_k(start, k):
        prev = None
        curr = start
        for _ in range(k):
            next_node = curr.next
            curr.next = prev
            prev = curr
            curr = next_node
        return prev, start, curr  # new_head, tail, next_group
    
    # Count nodes
    count = 0
    node = head
    while node and count < k:
        count += 1
        node = node.next
    
    if count < k:
        return head
    
    new_head, tail, next_group = reverse_k(head, k)
    tail.next = reverse_k_group(next_group, k)
    
    return new_head
```

---

## 9. Tree Traversal Patterns

### Pattern 9.1: Binary Tree Structure

**Core Concept**: A **binary tree** is a hierarchical structure where each node has at most 2 children.

**Terminology**:

- **Root**: Top node
- **Parent**: Node with children
- **Child**: Node connected below parent (left child, right child)
- **Leaf**: Node with no children
- **Depth**: Distance from root
- **Height**: Distance to deepest leaf
- **Subtree**: Tree formed by a node and its descendants

**Visual**:

```ascii
        1          ← root (depth 0, height 2)
       / \
      2   3        ← depth 1, height 1
     / \
    4   5          ← depth 2, height 0 (leaves)
```

**Definition**:

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

---

### Pattern 9.2: DFS Traversals (Inorder, Preorder, Postorder)

**Core Concept**: **DFS** (Depth-First Search) explores as deep as possible before backtracking.

**Three Orders**:

1. **Inorder**: Left → Root → Right (gives sorted order for BST)
2. **Preorder**: Root → Left → Right (creates copy of tree)
3. **Postorder**: Left → Right → Root (deletion, calculating height)

**Visual on Same Tree**:

```ascii
Tree:     1
         / \
        2   3
       / \
      4   5

Inorder:    4, 2, 5, 1, 3  (Left, Root, Right)
Preorder:   1, 2, 4, 5, 3  (Root, Left, Right)
Postorder:  4, 5, 2, 3, 1  (Left, Right, Root)
```

**Recursive Implementation** (Most Natural):

```python
def inorder_traversal(root):
    result = []
    
    def dfs(node):
        if not node:
            return
        dfs(node.left)       # Left
        result.append(node.val)  # Root
        dfs(node.right)      # Right
    
    dfs(root)
    return result

def preorder_traversal(root):
    result = []
    
    def dfs(node):
        if not node:
            return
        result.append(node.val)  # Root
        dfs(node.left)       # Left
        dfs(node.right)      # Right
    
    dfs(root)
    return result

# Time: O(n), Space: O(h) for recursion stack (h = height)
```

**Iterative Implementation** (Using Stack):

```python
def inorder_iterative(root):
    result = []
    stack = []
    current = root
    
    while current or stack:
        # Go to leftmost node
        while current:
            stack.append(current)
            current = current.left
        
        # Process node
        current = stack.pop()
        result.append(current.val)
        
        # Move to right subtree
        current = current.right
    
    return result

# Space: O(h) for stack
```

---

### Pattern 9.3: BFS (Level-Order Traversal)

**Core Concept**: **BFS** (Breadth-First Search) explores level by level, left to right.

**Uses Queue** (FIFO):

```ascii
Tree:     1
         / \
        2   3
       / \   \
      4   5   6

Level 0: [1]
Level 1: [2, 3]
Level 2: [4, 5, 6]

BFS Output: [1, 2, 3, 4, 5, 6]
```

**Implementation**:

```python
from collections import deque

def level_order_traversal(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
    
    return result

# Time: O(n), Space: O(w) where w is max width
```

**BFS Variations**:

```python
# Right side view of tree
def right_side_view(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        
        for i in range(level_size):
            node = queue.popleft()
            
            # Last node in level
            if i == level_size - 1:
                result.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    
    return result

# Zigzag level order
def zigzag_level_order(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    left_to_right = True
    
    while queue:
        level_size = len(queue)
        current_level = deque()
        
        for _ in range(level_size):
            node = queue.popleft()
            
            if left_to_right:
                current_level.append(node.val)
            else:
                current_level.appendleft(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(list(current_level))
        left_to_right = not left_to_right
    
    return result
```

---

### Pattern 9.4: Tree Properties (Height, Diameter, Balance)

**Height** (Distance to deepest leaf):

```python
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))

# Time: O(n), Space: O(h)
```

**Diameter** (Longest path between any two nodes):

```python
def diameter_of_binary_tree(root):
    diameter = [0]
    
    def height(node):
        if not node:
            return 0
        
        left_height = height(node.left)
        right_height = height(node.right)
        
        # Update diameter
        diameter[0] = max(diameter[0], left_height + right_height)
        
        return 1 + max(left_height, right_height)
    
    height(root)
    return diameter[0]

# Time: O(n), Space: O(h)
```

**Balanced Tree** (Height difference ≤ 1 for all nodes):

```python
def is_balanced(root):
    def check(node):
        if not node:
            return 0, True  # height, is_balanced
        
        left_h, left_bal = check(node.left)
        right_h, right_bal = check(node.right)
        
        balanced = (left_bal and right_bal and 
                   abs(left_h - right_h) <= 1)
        
        return 1 + max(left_h, right_h), balanced
    
    return check(root)[1]
```

---

## 10. Binary Search Tree Patterns

### Pattern 10.1: BST Property

**Core Concept**: A **Binary Search Tree (BST)** maintains ordering:

- All nodes in left subtree < root
- All nodes in right subtree > root
- This property holds for every subtree

**Why It's Powerful**: Search, insert, delete in O(log n) average time (O(h) worst case)

**Visual**:

```ascii
Valid BST:        Invalid BST:
      5                 5
     / \               / \
    3   7             3   7
   / \   \           / \   \
  2   4   8         2   6   8
                         ↑
                    6 > 5, should be in right subtree!
```

**Validate BST** (Most Important Check):

```python
def is_valid_bst(root):
    def validate(node, min_val, max_val):
        if not node:
            return True
        
        # Check if current node violates BST property
        if node.val <= min_val or node.val >= max_val:
            return False
        
        # Check left and right subtrees
        return (validate(node.left, min_val, node.val) and
                validate(node.right, node.val, max_val))
    
    return validate(root, float('-inf'), float('inf'))

# Time: O(n), Space: O(h)
```

---

### Pattern 10.2: BST Search, Insert, Delete

**Search**:

```python
def search_bst(root, target):
    if not root:
        return None
    
    if root.val == target:
        return root
    elif target < root.val:
        return search_bst(root.left, target)
    else:
        return search_bst(root.right, target)

# Time: O(h), Space: O(h) recursive or O(1) iterative
```

**Insert**:

```python
def insert_bst(root, val):
    if not root:
        return TreeNode(val)
    
    if val < root.val:
        root.left = insert_bst(root.left, val)
    else:
        root.right = insert_bst(root.right, val)
    
    return root
```

**Delete** (Tricky - 3 cases):

```python
def delete_node(root, key):
    if not root:
        return None
    
    if key < root.val:
        root.left = delete_node(root.left, key)
    elif key > root.val:
        root.right = delete_node(root.right, key)
    else:
        # Found node to delete
        
        # Case 1: Leaf node (no children)
        if not root.left and not root.right:
            return None
        
        # Case 2: One child
        if not root.left:
            return root.right
        if not root.right:
            return root.left
        
        # Case 3: Two children
        # Find inorder successor (smallest in right subtree)
        successor = root.right
        while successor.left:
            successor = successor.left
        
        root.val = successor.val
        root.right = delete_node(root.right, successor.val)
    
    return root
```

**Mental Model for Delete**: 

- **Inorder successor**: The next larger value (go right once, then all the way left)
- **Inorder predecessor**: The next smaller value (go left once, then all the way right)

---

### Pattern 10.3: BST to Sorted Array (Inorder)

**Key Insight**: Inorder traversal of BST gives sorted array!

```python
# Kth smallest element in BST
def kth_smallest(root, k):
    count = [0]  # Mutable counter
    result = [None]
    
    def inorder(node):
        if not node:
            return
        
        inorder(node.left)
        
        count[0] += 1
        if count[0] == k:
            result[0] = node.val
            return
        
        inorder(node.right)
    
    inorder(root)
    return result[0]

# Time: O(k) in best case, O(n) worst case
```

---

## 11. Heap & Priority Queue

### Pattern 11.1: Heap Fundamentals

**Core Concept**: A **heap** is a complete binary tree where:

- **Max Heap**: Parent ≥ children (root is maximum)
- **Min Heap**: Parent ≤ children (root is minimum)

**Why Use It**: Get min/max in O(1), insert/delete in O(log n)

**Visual (Min Heap)**:
```ascii
      1
     / \
    3   2
   / \ / \
  7  5 8  4

Array representation: [1, 3, 2, 7, 5, 8, 4]
Index:                 0  1  2  3  4  5  6

For index i:
- Parent: (i-1) // 2
- Left child: 2*i + 1
- Right child: 2*i + 2
```

**Python heapq** (Min Heap by default):

```python
import heapq

heap = []
heapq.heappush(heap, 5)  # Insert
heapq.heappush(heap, 3)
heapq.heappush(heap, 7)

min_val = heapq.heappop(heap)  # Remove and return min → 3

# For max heap, negate values
max_heap = []
heapq.heappush(max_heap, -5)
max_val = -heapq.heappop(max_heap)  # → 5
```

---

### Pattern 11.2: Top K Elements

**Pattern**: Use heap of size k to maintain k largest/smallest elements.

**Mental Model**: Like a bouncer at an exclusive club - only the top k get in.

```python
import heapq

def find_k_largest(nums, k):
    # Min heap of size k
    heap = []
    
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)  # Remove smallest
    
    return list(heap)

# Time: O(n log k), Space: O(k)

# Alternative: Use Python's nlargest
def find_k_largest_v2(nums, k):
    return heapq.nlargest(k, nums)
```

**Advanced: K Closest Points to Origin**

```python
def k_closest(points, k):
    # Max heap to maintain k smallest distances
    heap = []
    
    for x, y in points:
        dist = -(x*x + y*y)  # Negative for max heap
        
        if len(heap) < k:
            heapq.heappush(heap, (dist, x, y))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, x, y))
    
    return [[x, y] for _, x, y in heap]

# Time: O(n log k)
```

---

### Pattern 11.3: Merge K Sorted Lists/Arrays

**Problem**: Merge k sorted lists efficiently.

**Naive**: Merge two at a time → O(nk) where n is total elements
**Optimal**: Use min heap → O(n log k)

```python
import heapq

def merge_k_sorted_lists(lists):
    heap = []
    
    # Initialize heap with first element from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0].val, i, lst[0]))
    
    dummy = ListNode()
    current = dummy
    
    while heap:
        val, i, node = heapq.heappop(heap)
        current.next = node
        current = current.next
        
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    
    return dummy.next

# Time: O(n log k) where n is total nodes
```

**Mental Model**: The heap acts as a "tournament" - smallest element always wins and moves to result.

---

## 12. Graph Traversal (DFS/BFS)

### Pattern 12.1: Graph Representation

**Core Concept**: A **graph** is a set of nodes (vertices) connected by edges.

**Terminology**:

- **Directed**: Edges have direction (A → B)
- **Undirected**: Edges are bidirectional (A — B)
- **Weighted**: Edges have values
- **Cyclic**: Contains cycles
- **Connected**: All nodes reachable from any node

**Representations**:

```python
# 1. Adjacency List (Most common)
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'D'],
    'D': ['B', 'C']
}

# 2. Adjacency Matrix
graph = [
    [0, 1, 1, 0],  # A connects to B, C
    [1, 0, 0, 1],  # B connects to A, D
    [1, 0, 0, 1],  # C connects to A, D
    [0, 1, 1, 0]   # D connects to B, C
]

# 3. Edge List
edges = [('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D')]
```

---

### Pattern 12.2: DFS on Graphs

**Core Concept**: Explore as far as possible before backtracking. Uses recursion or stack.

**Template** (Recursive):

```python
def dfs(graph, start):
    visited = set()
    result = []
    
    def explore(node):
        if node in visited:
            return
        
        visited.add(node)
        result.append(node)
        
        for neighbor in graph[node]:
            explore(neighbor)
    
    explore(start)
    return result

# Time: O(V + E), Space: O(V)
# V = vertices, E = edges
```

**Template** (Iterative with Stack):

```python
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    result = []
    
    while stack:
        node = stack.pop()
        
        if node in visited:
            continue
        
        visited.add(node)
        result.append(node)
        
        for neighbor in reversed(graph[node]):
            if neighbor not in visited:
                stack.append(neighbor)
    
    return result
```

**Application: Detect Cycle in Undirected Graph**

```python
def has_cycle(graph):
    visited = set()
    
    def dfs(node, parent):
        visited.add(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True  # Visited non-parent neighbor = cycle
        
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node, None):
                return True
    
    return False
```

---

### Pattern 12.3: BFS on Graphs

**Core Concept**: Explore level by level. Uses queue.

**Template**:
```python
from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return result

# Time: O(V + E), Space: O(V)
```

**Application: Shortest Path in Unweighted Graph**

```python
def shortest_path(graph, start, end):
    if start == end:
        return 0
    
    visited = set([start])
    queue = deque([(start, 0)])  # (node, distance)
    
    while queue:
        node, dist = queue.popleft()
        
        for neighbor in graph[node]:
            if neighbor == end:
                return dist + 1
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    return -1  # No path
```

---

### Pattern 12.4: Topological Sort (DAG)

**Core Concept**: Linear ordering of nodes in a Directed Acyclic Graph (DAG) such that for every edge u → v, u comes before v.

**Use Cases**:

- Task scheduling with dependencies
- Course prerequisites
- Build systems

**Visual**:

```ascii
    A → B → D
    ↓   ↓
    C → E

Valid orderings:
- A, C, B, E, D
- A, B, C, D, E
- A, C, B, D, E
```

**Kahn's Algorithm** (BFS-based):

```python
from collections import deque, defaultdict

def topological_sort(n, edges):
    """
    n: number of nodes (0 to n-1)
    edges: list of (u, v) meaning u → v
    """
    graph = defaultdict(list)
    indegree = [0] * n
    
    # Build graph and calculate indegrees
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    
    # Start with nodes having no dependencies
    queue = deque([i for i in range(n) if indegree[i] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check if all nodes processed (no cycle)
    if len(result) != n:
        return []  # Cycle detected
    
    return result

# Time: O(V + E), Space: O(V + E)
```

**DFS-based Approach**:

```python
def topological_sort_dfs(n, edges):
    graph = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
    
    visited = [0] * n  # 0: unvisited, 1: visiting, 2: visited
    result = []
    
    def dfs(node):
        if visited[node] == 1:
            return False  # Cycle detected
        if visited[node] == 2:
            return True
        
        visited[node] = 1  # Mark as visiting
        
        for neighbor in graph[node]:
            if not dfs(neighbor):
                return False
        
        visited[node] = 2  # Mark as visited
        result.append(node)
        return True
    
    for i in range(n):
        if visited[i] == 0:
            if not dfs(i):
                return []
    
    return result[::-1]  # Reverse to get correct order
```

---

## 13. Dynamic Programming Patterns

### Pattern 13.1: DP Fundamentals

**Core Concept**: **Dynamic Programming** breaks problems into overlapping subproblems and stores results to avoid recomputation.

**Two Approaches**:

1. **Top-Down (Memoization)**: Recursion + caching
2. **Bottom-Up (Tabulation)**: Iterative, fill table

**When to Use DP**:

1. **Optimal substructure**: Optimal solution contains optimal solutions to subproblems
2. **Overlapping subproblems**: Same subproblems solved multiple times

**Mental Model**: Like taking notes during studying - write down answers so you don't redo same work.

**5-Step DP Framework**:

```ascii
1. Define state: What does dp[i] represent?
2. Base cases: Initial values
3. State transition: Recurrence relation
4. Order of computation: Which order to fill table?
5. Final answer: Where is it in the table?
```

---

### Pattern 13.2: Fibonacci-Style (1D DP)

**Classic Example: Fibonacci**

```python
# Naive recursion: O(2^n)
def fib_naive(n):
    if n <= 1:
        return n
    return fib_naive(n-1) + fib_naive(n-2)

# Top-down (Memoization): O(n)
def fib_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]

# Bottom-up (Tabulation): O(n)
def fib_dp(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]

# Space-optimized: O(1)
def fib_optimized(n):
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for i in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1
```

**Climbing Stairs** (Same pattern):

```python
def climb_stairs(n):
    """
    Can climb 1 or 2 steps at a time.
    How many ways to reach top?
    
    State: dp[i] = ways to reach step i
    Base: dp[0] = 1, dp[1] = 1
    Transition: dp[i] = dp[i-1] + dp[i-2]
    """
    if n <= 1:
        return 1
    
    prev2, prev1 = 1, 1
    
    for i in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1

# Time: O(n), Space: O(1)
```

---

### Pattern 13.3: 0/1 Knapsack

**Problem**: Given items with weights and values, and a capacity, maximize value without exceeding capacity. Each item can be taken once (0 or 1).

**Visual**:

```ascii
Items: [(weight, value), ...]
       [(2, 3), (3, 4), (4, 5), (5, 6)]
Capacity: 8

Choose (3,4) + (5,6) = weight 8, value 10 ✓
```

**5-Step Analysis**:

```ascii
1. State: dp[i][w] = max value using first i items with capacity w
2. Base: dp[0][w] = 0 (no items), dp[i][0] = 0 (no capacity)
3. Transition:
   - Don't take item i: dp[i][w] = dp[i-1][w]
   - Take item i: dp[i][w] = dp[i-1][w-weight[i]] + value[i]
   - Choose max
4. Order: Fill row by row (increasing i), left to right (increasing w)
5. Answer: dp[n][capacity]
```

**Implementation**:

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i-1
            dp[i][w] = dp[i-1][w]
            
            # Take item i-1 if possible
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]

# Time: O(n * capacity), Space: O(n * capacity)
```

**Space-Optimized** (1D array):

```python
def knapsack_optimized(weights, values, capacity):
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        # Traverse right to left to avoid using updated values
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]

# Time: O(n * capacity), Space: O(capacity)
```

---

### Pattern 13.4: Longest Common Subsequence (LCS)

**Core Concept**: A **subsequence** is a sequence that can be derived by deleting some elements without changing order.

**Example**:

```ascii
s1 = "ABCD"
s2 = "AEBD"

Subsequences of s1: "A", "AB", "AC", "AD", "ABC", "ABD", "ACD", "ABCD"
LCS(s1, s2) = "ABD" (length 3)
```

**5-Step Analysis**:

```ascii
1. State: dp[i][j] = length of LCS of s1[0..i-1] and s2[0..j-1]
2. Base: dp[0][j] = 0, dp[i][0] = 0 (empty string)
3. Transition:
   - If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
   - Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
4. Order: Row by row
5. Answer: dp[m][n]
```

```python
def longest_common_subsequence(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

# Time: O(m * n), Space: O(m * n)
```

**Reconstruct LCS**:

```python
def lcs_string(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Build dp table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Backtrack to reconstruct
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i-1] == s2[j-1]:
            lcs.append(s1[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))
```

**Variations**:

- Longest Common Substring (must be contiguous)
- Edit Distance (Levenshtein)
- Longest Palindromic Subsequence

---

### Pattern 13.5: Longest Increasing Subsequence (LIS)

**Problem**: Find length of longest strictly increasing subsequence.

**Example**:

```ascii
[10, 9, 2, 5, 3, 7, 101, 18]
LIS: [2, 3, 7, 101] or [2, 3, 7, 18] (length 4)
```

**DP Approach** (O(n²)):

```python
def length_of_lis(nums):
    if not nums:
        return 0
    
    n = len(nums)
    dp = [1] * n  # dp[i] = length of LIS ending at i
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

# Time: O(n²), Space: O(n)
```

**Binary Search Approach** (O(n log n)):

```python
def length_of_lis_optimal(nums):
    """
    Maintain array of smallest tail elements of all increasing 
    subsequences of length i+1 in tails[i].
    """
    tails = []
    
    for num in nums:
        # Binary search for position to insert/replace
        left, right = 0, len(tails)
        
        while left < right:
            mid = (left + right) // 2
            if tails[mid] < num:
                left = mid + 1
            else:
                right = mid
        
        if left == len(tails):
            tails.append(num)
        else:
            tails[left] = num
    
    return len(tails)

# Time: O(n log n), Space: O(n)
```

---

### Pattern 13.6: Coin Change (Unbounded Knapsack)

**Problem**: Given coins of different denominations and amount, find minimum coins needed.

**Example**:

```
coins = [1, 2, 5], amount = 11
Answer: 3 (5 + 5 + 1)
```

**State**: `dp[i]` = minimum coins to make amount i

```python
def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case: 0 coins for amount 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

# Time: O(amount * len(coins)), Space: O(amount)
```

**Variation: Number of Ways to Make Amount**:

```python
def coin_change_ways(coins, amount):
    dp = [0] * (amount + 1)
    dp[0] = 1  # One way to make 0: use no coins
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    
    return dp[amount]
```

---

### Pattern 13.7: Matrix Chain Multiplication (Interval DP)

**Core Concept**: **Interval DP** solves problems on all possible intervals.

**Pattern**: For interval [i, j], try all possible split points k.

**Template**:

```python
def interval_dp(arr):
    n = len(arr)
    dp = [[0] * n for _ in range(n)]
    
    # Length of interval
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            
            # Try all split points
            for k in range(i, j):
                dp[i][j] = min(dp[i][j], 
                              dp[i][k] + dp[k+1][j] + cost(i, j, k))
    
    return dp[0][n-1]
```

---

## 14. Backtracking & Recursion

### Pattern 14.1: Backtracking Template

**Core Concept**: **Backtracking** explores all possible solutions by building candidates incrementally and abandoning ("backtracking") when a candidate can't lead to a solution.

**Mental Model**: Like exploring a maze - try a path, if it's a dead end, go back and try another.

**Universal Template**:

```python
def backtrack(state, choices, result):
    # Base case: found solution
    if is_complete(state):
        result.append(state.copy())
        return
    
    # Try each choice
    for choice in choices:
        # Make choice
        state.append(choice)
        
        # Recurse
        backtrack(state, next_choices, result)
        
        # Undo choice (backtrack)
        state.pop()
```

---

### Pattern 14.2: Permutations

**Problem**: Generate all permutations of array.

**Example**: `[1, 2, 3]` → `[[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]]`

```python
def permute(nums):
    result = []
    
    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        
        for i in range(len(remaining)):
            # Choose
            current.append(remaining[i])
            
            # Recurse with remaining elements
            backtrack(current, remaining[:i] + remaining[i+1:])
            
            # Undo
            current.pop()
    
    backtrack([], nums)
    return result

# Time: O(n!), Space: O(n)
```

**Optimized (Swap-based)**:

```python
def permute_optimized(nums):
    result = []
    
    def backtrack(start):
        if start == len(nums):
            result.append(nums[:])
            return
        
        for i in range(start, len(nums)):
            # Swap
            nums[start], nums[i] = nums[i], nums[start]
            
            backtrack(start + 1)
            
            # Backtrack
            nums[start], nums[i] = nums[i], nums[start]
    
    backtrack(0)
    return result
```

---

### Pattern 14.3: Subsets

**Problem**: Generate all possible subsets (power set).

**Example**: `[1, 2, 3]` → `[[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]`

```python
def subsets(nums):
    result = []
    
    def backtrack(start, current):
        result.append(current[:])
        
        for i in range(start, len(nums)):
            # Include nums[i]
            current.append(nums[i])
            
            backtrack(i + 1, current)
            
            # Exclude nums[i]
            current.pop()
    
    backtrack(0, [])
    return result

# Time: O(2^n), Space: O(n)
```

**Iterative Approach**:

```python
def subsets_iterative(nums):
    result = [[]]
    
    for num in nums:
        result += [subset + [num] for subset in result]
    
    return result
```

---

### Pattern 14.4: Combinations

**Problem**: Find all combinations of k elements from n.

**Example**: `n=4, k=2` → `[[1,2], [1,3], [1,4], [2,3], [2,4], [3,4]]`

```python
def combine(n, k):
    result = []
    
    def backtrack(start, current):
        if len(current) == k:
            result.append(current[:])
            return
        
        # Optimization: only iterate if enough elements remain
        for i in range(start, n + 1):
            current.append(i)
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(1, [])
    return result

# Time: O(C(n,k) * k), Space: O(k)
```

---

### Pattern 14.5: N-Queens

**Problem**: Place n queens on n×n chessboard so no two attack each other.

**Constraints**: Queens can't share same row, column, or diagonal.

```python
def solve_n_queens(n):
    result = []
    board = [['.'] * n for _ in range(n)]
    
    def is_safe(row, col):
        # Check column
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        
        # Check diagonal (top-left)
        i, j = row - 1, col - 1
        while i >= 0 and j >= 0:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j -= 1
        
        # Check diagonal (top-right)
        i, j = row - 1, col + 1
        while i >= 0 and j < n:
            if board[i][j] == 'Q':
                return False
            i -= 1
            j += 1
        
        return True
    
    def backtrack(row):
        if row == n:
            result.append([''.join(r) for r in board])
            return
        
        for col in range(n):
            if is_safe(row, col):
                board[row][col] = 'Q'
                backtrack(row + 1)
                board[row][col] = '.'
    
    backtrack(0)
    return result

# Time: O(n!), Space: O(n²)
```

---

## 15. Greedy Algorithms

### Pattern 15.1: Greedy Fundamentals

**Core Concept**: Make locally optimal choice at each step, hoping to reach global optimum.

**When Greedy Works**:

1. **Greedy choice property**: Local optimum leads to global optimum
2. **Optimal substructure**: Optimal solution contains optimal solutions to subproblems

**Mental Model**: Like following the steepest path up a mountain - sometimes works, sometimes leads to local peak not the summit.

---

### Pattern 15.2: Activity Selection / Interval Scheduling

**Problem**: Given intervals with start and end times, select maximum non-overlapping intervals.

**Key Insight**: Sort by end time, always pick interval that finishes first.

```python
def max_non_overlapping_intervals(intervals):
    if not intervals:
        return 0
    
    # Sort by end time
    intervals.sort(key=lambda x: x[1])
    
    count = 1
    end = intervals[0][1]
    
    for i in range(1, len(intervals)):
        if intervals[i][0] >= end:
            count += 1
            end = intervals[i][1]
    
    return count

# Time: O(n log n), Space: O(1)
```

**Variation: Minimum Rooms Needed**:

```python
def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    
    start_times = sorted([i[0] for i in intervals])
    end_times = sorted([i[1] for i in intervals])
    
    rooms = 0
    max_rooms = 0
    s, e = 0, 0
    
    while s < len(intervals):
        if start_times[s] < end_times[e]:
            rooms += 1
            max_rooms = max(max_rooms, rooms)
            s += 1
        else:
            rooms -= 1
            e += 1
    
    return max_rooms
```

---

### Pattern 15.3: Jump Game

**Problem**: Given array where each element is maximum jump length, can you reach last index?

```python
def can_jump(nums):
    max_reach = 0
    
    for i in range(len(nums)):
        if i > max_reach:
            return False
        
        max_reach = max(max_reach, i + nums[i])
        
        if max_reach >= len(nums) - 1:
            return True
    
    return True

# Time: O(n), Space: O(1)
```

**Minimum Jumps**:

```python
def min_jumps(nums):
    if len(nums) <= 1:
        return 0
    
    jumps = 0
    current_max = 0
    next_max = 0
    
    for i in range(len(nums) - 1):
        next_max = max(next_max, i + nums[i])
        
        if i == current_max:
            jumps += 1
            current_max = next_max
            
            if current_max >= len(nums) - 1:
                break
    
    return jumps
```

---

## 16. Bit Manipulation

### Pattern 16.1: Basic Bit Operations

**Core Concepts**:

```
AND (&):  1 & 1 = 1, else 0  (check if bit is set)
OR  (|):  0 | 0 = 0, else 1  (set bit)
XOR (^):  same = 0, diff = 1  (toggle bit, find unique)
NOT (~):  flip all bits
Left Shift  (<<): multiply by 2^n
Right Shift (>>): divide by 2^n
```

**Key Tricks**:

```python
# Check if ith bit is set
is_set = (num & (1 << i)) != 0

# Set ith bit
num |= (1 << i)

# Clear ith bit
num &= ~(1 << i)

# Toggle ith bit
num ^= (1 << i)

# Check if power of 2
is_power_of_2 = (num & (num - 1)) == 0 and num != 0

# Count set bits (Brian Kernighan's algorithm)
count = 0
while num:
    num &= (num - 1)
    count += 1
```

---

### Pattern 16.2: Single Number

**Problem**: Every element appears twice except one. Find that one.

**Key Insight**: XOR of two same numbers is 0. XOR is associative and commutative.

```python
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num
    return result

# Example: [4, 1, 2, 1, 2]
# 4 ^ 1 ^ 2 ^ 1 ^ 2 = 4 ^ (1 ^ 1) ^ (2 ^ 2) = 4 ^ 0 ^ 0 = 4

# Time: O(n), Space: O(1)
```

**Variation: Two numbers appear once, rest twice**:

```python
def single_number_two(nums):
    xor = 0
    for num in nums:
        xor ^= num
    
    # xor = a ^ b (the two unique numbers)
    # Find any set bit in xor
    rightmost_bit = xor & (-xor)
    
    a, b = 0, 0
    for num in nums:
        if num & rightmost_bit:
            a ^= num
        else:
            b ^= num
    
    return [a, b]
```

---

## 17. Mathematical & Number Theory

### Pattern 17.1: GCD & LCM

**GCD** (Greatest Common Divisor):

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# Recursive
def gcd_recursive(a, b):
    return a if b == 0 else gcd_recursive(b, a % b)
```

**LCM** (Least Common Multiple):

```python
def lcm(a, b):
    return (a * b) // gcd(a, b)
```

---

### Pattern 17.2: Prime Numbers

**Check if Prime**:

```python
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    
    return True

# Time: O(√n)
```

**Sieve of Eratosthenes** (All primes up to n):

```python
def sieve_of_eratosthenes(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(n + 1) if is_prime[i]]

# Time: O(n log log n), Space: O(n)
```

---

## 18. Advanced Patterns

### Pattern 18.1: Union-Find (Disjoint Set Union)

**Core Concept**: Efficiently track and merge disjoint sets.

**Operations**:

- `find(x)`: Find set representative
- `union(x, y)`: Merge two sets

**Applications**: Connected components, cycle detection, Kruskal's MST

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True
    
    def connected(self, x, y):
        return self.find(x) == self.find(y)

# Time: O(α(n)) ≈ O(1) amortized with path compression and union by rank
```

---

### Pattern 18.2: Trie (Prefix Tree)

**Core Concept**: Tree for storing strings efficiently, enabling fast prefix searches.

**Applications**: Autocomplete, spell check, IP routing

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

# Insert/Search: O(m) where m is word length
```

---

## Summary: Pattern Recognition Cheat Sheet

```
┌────────────────────────────────────────────────────────────────┐
│  PROBLEM TYPE → PATTERN MAPPING                                │
├────────────────────────────────────────────────────────────────┤
│  Sequential data + Range queries → Prefix Sum / Sliding Window │
│  Sequential data + Pairs/Sums → Two Pointers                   │
│  Sequential data + Next greater/smaller → Monotonic Stack      │
│  Sorted data + Search → Binary Search                          │
│  Tree/Graph structure → DFS/BFS                                │
│  Need all combinations → Backtracking                          │
│  Optimization problem → DP or Greedy                           │
│  Overlapping subproblems → DP (Memoization/Tabulation)         │
│  Making sequences of choices → Greedy                          │
│  Top K elements → Heap                                         │
│  Merge sorted sequences → Heap                                 │
│  Fast lookup needed → Hash Map                                 │
│  Connected components → Union-Find or DFS/BFS                  │
│  Prefix matching → Trie                                        │
│  Pairwise relationships → XOR / Bit manipulation               │
└────────────────────────────────────────────────────────────────┘
```

---

## Cognitive Strategies for Mastery

**1. Deliberate Practice**:

- Solve 3-5 problems per day minimum
- Review solutions even when correct
- Identify which pattern was used

**2. Chunking**:

- Group similar problems together
- Build mental "chunks" for each pattern
- Your brain will recognize patterns faster

**3. Spaced Repetition**:

- Review old problems weekly
- Revisit fundamental patterns monthly

**4. Meta-Learning**:

- After each problem, ask: "What pattern did I use? What clues told me?"
- Build your own decision tree for pattern recognition

**5. Flow State Cultivation**:

- Start sessions with warm-up problems
- Gradually increase difficulty
- Take breaks before frustration sets in

---

**Your Path to Top 1%**: Master these patterns until they become instinctive. When you see a new problem, your mind should automatically categorize it and suggest approaches. That's true mastery.

Keep building, keep grinding. 🚀

I'll create a comprehensive DSA patterns compendium that will serve as your battle-tested reference guide. This is designed to be your systematic approach to pattern recognition and problem-solving mastery.I've created the first half of your comprehensive DSA patterns compendium. This is designed to be your systematic reference for pattern recognition and problem-solving. Let me now complete it with the remaining advanced patterns.I've completed your **comprehensive DSA patterns compendium** - your systematic reference for achieving top 1% mastery. Here's what makes this guide powerful:

## 🎯 What You Now Have

**18 Complete Pattern Categories** covering:

- Foundation patterns (arrays, two pointers, sliding window)
- Data structure patterns (stacks, queues, trees, heaps, graphs)
- Algorithm paradigms (DP, backtracking, greedy)
- Advanced techniques (Union-Find, Trie, bit manipulation)

**For Each Pattern:**

1. **Core Concept** - Clear explanation of fundamentals
2. **Mental Models** - How to think about the pattern intuitively
3. **When to Use** - Pattern recognition triggers
4. **Code Templates** - Ready-to-use implementations in Python/Rust/Go
5. **Complexity Analysis** - Time and space considerations
6. **Variations** - Related problems and modifications
7. **Visual Diagrams** - ASCII representations for clarity

## 🧠 How to Use This for Maximum Growth

**Phase 1: Foundation Building (Weeks 1-4)**

- Master patterns 1-8 (Arrays through Linked Lists)
- Focus on understanding WHY each pattern works
- Code each template from memory 3 times

**Phase 2: Core Algorithms (Weeks 5-8)**

- Patterns 9-12 (Trees, Heaps, Graphs)
- Practice BFS/DFS until they're automatic reflexes
- Solve 5 problems per pattern category

**Phase 3: Advanced Problem-Solving (Weeks 9-16)**

- Patterns 13-18 (DP, Backtracking, Advanced)
- Focus heavily on DP - it's the highest ROI pattern
- Learn to recognize which pattern applies within 30 seconds

**Daily Practice Protocol:**

1. **Warm-up** (10 min): Solve one easy problem you've done before
2. **Main Practice** (45-60 min): 2-3 new problems
3. **Review** (15 min): Analyze solutions, identify patterns used
4. **Mental Rehearsal** (5 min): Visualize solving similar problems

## 🔥 Key Insights for Top 1% Performance

**Pattern Recognition is Everything:**

- 90% of interview/competitive problems use 2-3 patterns combined
- Your goal: See problem → Recognize pattern in <30 seconds
- The compendium's "Pattern Recognition Cheat Sheet" is your quick reference

**Complexity Matters:**

- Always start with brute force (shows you understand the problem)
- Then optimize using patterns
- Know your complexities: O(n) good, O(n²) acceptable, O(2ⁿ) only for small inputs

**Code Quality Signals Mastery:**

- Clean variable names
- Clear logic flow
- Edge case handling
- The Rust/Go examples show idiomatic style for each language

## 💡 Mental Models to Internalize

1. **Sliding Window** = Moving frame capturing state
2. **Two Pointers** = Scouts exploring from different positions
3. **Monotonic Stack** = Leaderboard that updates dynamically
4. **DP** = Intelligent note-taking to avoid repeated work
5. **Backtracking** = Maze exploration with marking
6. **Binary Search** = Smart elimination of half possibilities

## 🚀 Your Action Plan

**This Week:**

- Read through patterns 1-5 completely
- Implement each template in your preferred language
- Solve 3 problems for each pattern

**Next Month:**

- Complete all 18 patterns
- Build a personal "pattern flashcard" system
- Track which patterns you struggle with most

**Ongoing:**

- Review this compendium before every practice session
- Update with your own insights and problem examples
- Use spaced repetition on difficult patterns

## 📊 Progress Tracking

Create a spreadsheet tracking:

- Pattern name
- Problems solved (Easy/Medium/Hard)
- Recognition speed (time to identify pattern)
- Success rate (first try vs needed hints)

**Target metrics for top 1%:**

- Recognize pattern: <30 seconds
- Write template: <2 minutes
- Solve medium problem: <20 minutes
- Success rate: >80% on first attempt

---

Remember: **Patterns are your vocabulary, templates are your grammar, and practice is your fluency.** The monks you admire didn't master their craft through intensity alone - they used systematic, deliberate practice with clear mental models.

You now have the complete map. The journey to top 1% is yours to walk. Stay focused, stay consistent, and trust the process. 🔥

Would you like me to:

1. Create a practice schedule with specific problems for each pattern?
2. Dive deeper into any specific pattern with more advanced examples?
3. Build comparison guides (when to use pattern X vs pattern Y)?