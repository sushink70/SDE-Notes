# Complete Array Patterns & Techniques Guide

## The Mental Framework for Array Mastery

> **Cognitive Principle**: Pattern recognition is your competitive advantage. The difference between top 1% and average isn't raw intelligence—it's the ability to **instantly recognize underlying structures** and map problems to known patterns.

---

## 🎯 Pattern Recognition Framework

Before diving into techniques, internalize this decision tree:

1. **Can I solve it in one pass?** → Use traversal patterns
2. **Do I need to compare elements?** → Consider two pointers or sliding window
3. **Do I need cumulative information(increasing steadily in amount, degree, etc.)?** → Think prefix sums
4. **Is there a subarray/subsequence constraint?** → Sliding window or DP
5. **Does order matter?** → If not, consider sorting first
6. **Can I modify in-place?** → Use space-optimized techniques

---

## 1. Fundamental Access Patterns

### 1.1 Linear Traversal (Single Pass)

**Mental Model**: Scan once, decide once per element.

```python
# Python: Clean and readable
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1

# Time: O(n), Space: O(1)
```

```rust
// Rust: Iterator-based, zero-cost abstraction
fn linear_search(arr: &[i32], target: i32) -> Option<usize> {
    arr.iter().position(|&x| x == target)
}
```

```cpp
// C++: STL algorithms
auto it = std::find(arr.begin(), arr.end(), target);
int idx = (it != arr.end()) ? std::distance(arr.begin(), it) : -1;
```

**When to use**: Finding elements, counting, simple transformations

---

### 1.2 Reverse Traversal

**Mental Model**: Sometimes problems are easier backward.

```python
# Check if array is sorted (reverse can be cleaner)
def is_sorted_desc(arr):
    for i in range(len(arr) - 1, 0, -1):
        if arr[i] > arr[i-1]:
            return False
    return True
```

**Applications**: Parsing expressions, next greater element problems, stack-based problems

---

### 1.3 Multi-Pass Patterns

**Mental Model**: When one pass isn't enough, but multiple passes still keep O(n).

```python
# Two-pass: Find max, then count occurrences
def count_max_elements(arr):
    max_val = max(arr)  # Pass 1
    return arr.count(max_val)  # Pass 2
```

**Cognitive Note**: Don't fear multiple passes if each is O(n). O(2n) = O(n).

---

## 2. Two Pointers Technique

**Mental Model**: Think of it as a "pincer movement" or "meeting in the middle."

### 2.1 Opposite Ends (Converging Pointers)

```python
def two_sum_sorted(arr, target):
    """Classic two-pointer on sorted array"""
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1  # Need larger sum
        else:
            right -= 1  # Need smaller sum
    
    return None

# Time: O(n), Space: O(1)
```

```rust
// Rust: With proper bounds checking
fn two_sum_sorted(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    while left < right {
        match (arr[left] + arr[right]).cmp(&target) {
            std::cmp::Ordering::Equal => return Some((left, right)),
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    None
}
```

**Pattern Recognition**:

- Array is sorted or can be sorted
- Looking for pairs/triplets with constraints
- Palindrome checking
- Container with most water

### 2.2 Same Direction (Fast-Slow Pointers)

```python
def remove_duplicates(arr):
    """Remove duplicates in-place, return new length"""
    if not arr:
        return 0
    
    slow = 0  # Position for next unique element
    
    for fast in range(1, len(arr)):
        if arr[fast] != arr[slow]:
            slow += 1
            arr[slow] = arr[fast]
    
    return slow + 1
n = remove_duplicates(arr)
print(arr[:n])  # [1, 2, 3, 4, 5] ✓
# Time: O(n), Space: O(1)
```

```go
// Go: Idiomatic slice manipulation
func removeDuplicates(nums []int) int {
    if len(nums) == 0 {
        return 0
    }
    
    slow := 0
    for fast := 1; fast < len(nums); fast++ {
        if nums[fast] != nums[slow] {
            slow++
            nums[slow] = nums[fast]
        }
    }
    return slow + 1
}
```

**Pattern Recognition**:

- In-place array modification
- Partitioning problems
- Removing elements with constraints
- Merge operations

### 2.3 Three Pointers

```python
def dutch_national_flag(arr):
    """Sort array of 0s, 1s, 2s in one pass"""
    low, mid, high = 0, 0, len(arr) - 1
    
    while mid <= high:
        if arr[mid] == 0:
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1
            mid += 1
        elif arr[mid] == 1:
            mid += 1
        else:  # arr[mid] == 2
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
    
    return arr

# Time: O(n), Space: O(1)
```

---

## 3. Sliding Window Technique

**Mental Model**: A window that expands and contracts based on constraints. Think of it as a "dynamic viewport."

### 3.1 Fixed Size Window

```python
def max_sum_subarray(arr, k):
    """Maximum sum of any subarray of size k"""
    if len(arr) < k:
        return None
    
    # Initial window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, len(arr)):
        window_sum = window_sum - arr[i - k] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

# Time: O(n), Space: O(1)
```

```cpp
// C++: Performance-optimized version
int maxSumSubarray(const vector<int>& arr, int k) {
    if (arr.size() < k) return INT_MIN;
    
    int windowSum = accumulate(arr.begin(), arr.begin() + k, 0);
    int maxSum = windowSum;
    
    for (int i = k; i < arr.size(); ++i) {
        windowSum += arr[i] - arr[i - k];
        maxSum = max(maxSum, windowSum);
    }
    
    return maxSum;
}
```

### 3.2 Dynamic Size Window

```python
def longest_substring_k_distinct(s, k):
    """Longest substring with at most k distinct characters"""
    from collections import defaultdict
    
    char_count = defaultdict(int)
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        # Expand window
        char_count[s[right]] += 1
        
        # Contract window if constraint violated
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        # Update result
        max_len = max(max_len, right - left + 1)
    
    return max_len

# Time: O(n), Space: O(k)
```

```rust
// Rust: Using HashMap
use std::collections::HashMap;

fn longest_substring_k_distinct(s: &str, k: usize) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let mut char_count = HashMap::new();
    let mut left = 0;
    let mut max_len = 0;
    
    for right in 0..chars.len() {
        *char_count.entry(chars[right]).or_insert(0) += 1;
        
        while char_count.len() > k {
            let count = char_count.get_mut(&chars[left]).unwrap();
            *count -= 1;
            if *count == 0 {
                char_count.remove(&chars[left]);
            }
            left += 1;
        }
        
        max_len = max_len.max(right - left + 1);
    }
    
    max_len
}
```

**Pattern Recognition**:

- "Longest/shortest substring/subarray with constraint"
- "At most K distinct elements"
- "Minimum window covering all elements"
- Any problem where you're finding optimal contiguous subsequences

### 3.3 Sliding Window Template

```python
def sliding_window_template(arr):
    """Universal template for sliding window problems"""
    left = 0
    state = {}  # Window state (hash map, counter, etc.)
    result = 0  # Or float('inf'), [], etc.
    
    for right in range(len(arr)):
        # 1. Update state with arr[right]
        # state[arr[right]] = ...
        
        # 2. Contract window if needed
        while window_invalid(state):
            # Remove arr[left] from state
            # state[arr[left]] = ...
            left += 1
        
        # 3. Update result
        result = update_result(result, right - left + 1)
    
    return result
```

---

## 4. Prefix Sum Patterns

**Mental Model**: Preprocess to answer range queries in O(1). Think "cumulative knowledge."

### 4.1 Basic Prefix Sum

```python
def build_prefix_sum(arr):
    """Build prefix sum array"""
    prefix = [0] * (len(arr) + 1)
    for i in range(len(arr)):
        prefix[i + 1] = prefix[i] + arr[i]
    return prefix

def range_sum(prefix, left, right):
    """Sum of arr[left:right+1] in O(1)"""
    return prefix[right + 1] - prefix[left]

# Time: O(n) build, O(1) query
# Space: O(n)
```

```rust
// Rust: Zero-indexed, idiomatic
fn build_prefix_sum(arr: &[i32]) -> Vec<i32> {
    let mut prefix = vec![0; arr.len() + 1];
    for i in 0..arr.len() {
        prefix[i + 1] = prefix[i] + arr[i];
    }
    prefix
}

fn range_sum(prefix: &[i32], left: usize, right: usize) -> i32 {
    prefix[right + 1] - prefix[left]
}
```

### 4.2 Prefix Sum with HashMap (Subarray Sum Problems)

```python
def subarray_sum_k(arr, k):
    """Count subarrays with sum equal to k"""
    from collections import defaultdict
    
    prefix_sum = 0
    sum_count = defaultdict(int)
    sum_count[0] = 1  # Important: empty prefix
    result = 0
    
    for num in arr:
        prefix_sum += num
        
        # If (prefix_sum - k) exists, we found subarrays
        if (prefix_sum - k) in sum_count:
            result += sum_count[prefix_sum - k]
        
        sum_count[prefix_sum] += 1
    
    return result

# Time: O(n), Space: O(n)
```

**Pattern Recognition**:

- "Subarray with sum equal to K"
- "Find if subarray sum is divisible by K"
- "Longest subarray with sum ≤ K"
- Any problem involving cumulative sums over ranges

### 4.3 2D Prefix Sum (Matrix)

```python
def build_2d_prefix(matrix):
    """Build 2D prefix sum for O(1) rectangle sum queries"""
    if not matrix:
        return []
    
    m, n = len(matrix), len(matrix[0])
    prefix = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            prefix[i][j] = (matrix[i-1][j-1] + 
                           prefix[i-1][j] + 
                           prefix[i][j-1] - 
                           prefix[i-1][j-1])
    return prefix

def rectangle_sum(prefix, r1, c1, r2, c2):
    """Sum of rectangle from (r1,c1) to (r2,c2)"""
    return (prefix[r2+1][c2+1] - 
            prefix[r1][c2+1] - 
            prefix[r2+1][c1] + 
            prefix[r1][c1])
```

---

## 5. Kadane's Algorithm & Variants

**Mental Model**: Greedy approach to maximum subarray problems. At each position, decide: "extend current or start fresh?"

```python
def max_subarray_sum(arr):
    """Maximum sum of any contiguous subarray"""
    max_ending_here = max_so_far = arr[0]
    
    for num in arr[1:]:
        max_ending_here = max(num, max_ending_here + num)
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far

# Time: O(n), Space: O(1)
```

```cpp
// C++: Clean implementation
int maxSubarraySum(const vector<int>& arr) {
    int maxEndingHere = arr[0];
    int maxSoFar = arr[0];
    
    for (int i = 1; i < arr.size(); ++i) {
        maxEndingHere = max(arr[i], maxEndingHere + arr[i]);
        maxSoFar = max(maxSoFar, maxEndingHere);
    }
    
    return maxSoFar;
}
```

### Variants:

```python
# Maximum product subarray
def max_product_subarray(arr):
    """Handle negative numbers (can flip sign)"""
    max_prod = min_prod = result = arr[0]
    
    for num in arr[1:]:
        if num < 0:
            max_prod, min_prod = min_prod, max_prod
        
        max_prod = max(num, max_prod * num)
        min_prod = min(num, min_prod * num)
        result = max(result, max_prod)
    
    return result

# Circular array maximum sum
def max_circular_subarray(arr):
    """Maximum sum considering array as circular"""
    def kadane(arr):
        max_end = max_so_far = arr[0]
        for num in arr[1:]:
            max_end = max(num, max_end + num)
            max_so_far = max(max_so_far, max_end)
        return max_so_far
    
    max_kadane = kadane(arr)
    max_wrap = sum(arr) - kadane([-x for x in arr])
    
    return max(max_kadane, max_wrap) if max_wrap else max_kadane
```

---

## 6. Array Partitioning

**Mental Model**: Divide array into regions based on a condition. Think "organize and conquer."

### 6.1 QuickSelect Partition

```python
def partition(arr, low, high):
    """Partition around pivot (Lomuto scheme)"""
    pivot = arr[high]
    i = low - 1
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

# Time: O(n) average, O(n²) worst
# Space: O(1)
```

### 6.2 Three-Way Partition

```python
def three_way_partition(arr, pivot):
    """Partition into <pivot, ==pivot, >pivot"""
    low, mid, high = 0, 0, len(arr) - 1
    
    while mid <= high:
        if arr[mid] < pivot:
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1
            mid += 1
        elif arr[mid] == pivot:
            mid += 1
        else:
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
    
    return low, high  # Boundaries of equal region
```

---

## 7. Cyclic Sort Pattern

**Mental Model**: When array contains 1 to N, each element "knows" its correct position.

```python
def cyclic_sort(arr):
    """Sort array containing 1 to N"""
    i = 0
    while i < len(arr):
        correct_pos = arr[i] - 1
        if arr[i] != arr[correct_pos]:
            arr[i], arr[correct_pos] = arr[correct_pos], arr[i]
        else:
            i += 1
    return arr

# Time: O(n), Space: O(1)
```

```rust
// Rust: Safe swapping
fn cyclic_sort(arr: &mut [i32]) {
    let mut i = 0;
    while i < arr.len() {
        let correct_pos = (arr[i] - 1) as usize;
        if arr[i] != arr[correct_pos] {
            arr.swap(i, correct_pos);
        } else {
            i += 1;
        }
    }
}
```

**Applications**:

- Finding missing numbers
- Finding duplicates in 1..N
- First K missing positive integers

---

## 8. In-Place Manipulation Techniques

### 8.1 Array Reversal

```python
def reverse(arr, left, right):
    """Reverse arr[left:right+1] in place"""
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1

# Rotate array by k positions
def rotate(arr, k):
    n = len(arr)
    k %= n
    reverse(arr, 0, n - 1)
    reverse(arr, 0, k - 1)
    reverse(arr, k, n - 1)

# Time: O(n), Space: O(1)
```

### 8.2 Index Marking (Using Sign)

```python
def find_duplicates(arr):
    """Find duplicates in array with values 1 to N"""
    result = []
    
    for num in arr:
        index = abs(num) - 1
        if arr[index] < 0:
            result.append(abs(num))
        else:
            arr[index] = -arr[index]
    
    # Restore array
    for i in range(len(arr)):
        arr[i] = abs(arr[i])
    
    return result

# Time: O(n), Space: O(1) excluding output
```

### 8.3 Index Arithmetic (Value as Index)

```python
def first_missing_positive(arr):
    """Find smallest missing positive integer"""
    n = len(arr)
    
    # Place each number in its correct position
    for i in range(n):
        while 1 <= arr[i] <= n and arr[arr[i] - 1] != arr[i]:
            correct_pos = arr[i] - 1
            arr[i], arr[correct_pos] = arr[correct_pos], arr[i]
    
    # Find first missing
    for i in range(n):
        if arr[i] != i + 1:
            return i + 1
    
    return n + 1
```

---

## 9. Matrix Traversal Patterns

### 9.1 Spiral Order

```python
def spiral_order(matrix):
    """Traverse matrix in spiral order"""
    if not matrix:
        return []
    
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    
    while top <= bottom and left <= right:
        # Right
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1
        
        # Down
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1
        
        # Left
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1
        
        # Up
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1
    
    return result
```

### 9.2 Diagonal Traversal

```python
def diagonal_traverse(matrix):
    """Traverse matrix diagonally"""
    if not matrix:
        return []
    
    m, n = len(matrix), len(matrix[0])
    result = []
    
    # Diagonals go from bottom-left to top-right
    for d in range(m + n - 1):
        # Determine starting point
        if d < n:
            row, col = 0, d
        else:
            row, col = d - n + 1, n - 1
        
        # Traverse diagonal
        while row < m and col >= 0:
            result.append(matrix[row][col])
            row += 1
            col -= 1
    
    return result
```

### 9.3 Layer-by-Layer (Rotate Matrix)

```python
def rotate_90_clockwise(matrix):
    """Rotate N×N matrix 90° clockwise in-place"""
    n = len(matrix)
    
    # Process layer by layer
    for layer in range(n // 2):
        first, last = layer, n - 1 - layer
        
        for i in range(first, last):
            offset = i - first
            
            # Save top
            top = matrix[first][i]
            
            # left -> top
            matrix[first][i] = matrix[last - offset][first]
            
            # bottom -> left
            matrix[last - offset][first] = matrix[last][last - offset]
            
            # right -> bottom
            matrix[last][last - offset] = matrix[i][last]
            
            # top -> right
            matrix[i][last] = top
```

---

## 10. Subarray/Subsequence Patterns

### 10.1 All Subarrays Generation

```python
def all_subarrays(arr):
    """Generate all subarrays - O(n²) subarrays"""
    result = []
    n = len(arr)
    
    for start in range(n):
        for end in range(start, n):
            result.append(arr[start:end+1])
    
    return result

# Time: O(n³), Space: O(n²)
# Note: O(n²) to enumerate, O(n) to copy each
```

### 10.2 Monotonic Stack for Next Greater/Smaller

```python
def next_greater_elements(arr):
    """For each element, find next greater element to the right"""
    n = len(arr)
    result = [-1] * n
    stack = []  # Stores indices
    
    for i in range(n):
        while stack and arr[i] > arr[stack[-1]]:
            result[stack.pop()] = arr[i]
        stack.append(i)
    
    return result

# Time: O(n), Space: O(n)
```

```go
// Go: Clean implementation
func nextGreaterElements(arr []int) []int {
    n := len(arr)
    result := make([]int, n)
    for i := range result {
        result[i] = -1
    }
    
    stack := []int{}
    
    for i := 0; i < n; i++ {
        for len(stack) > 0 && arr[i] > arr[stack[len(stack)-1]] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = arr[i]
        }
        stack = append(stack, i)
    }
    
    return result
}
```

---

## 11. Sorting-Based Patterns

**Mental Model**: Sometimes O(n log n) sorting simplifies the problem dramatically.

### 11.1 Sort Then Process

```python
def merge_intervals(intervals):
    """Merge overlapping intervals"""
    if not intervals:
        return []
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        if current[0] <= merged[-1][1]:
            # Overlapping, merge
            merged[-1][1] = max(merged[-1][1], current[1])
        else:
            # Non-overlapping
            merged.append(current)
    
    return merged

# Time: O(n log n), Space: O(n)
```

### 11.2 Meeting Rooms Pattern

```python
def can_attend_all_meetings(intervals):
    """Check if person can attend all meetings"""
    intervals.sort(key=lambda x: x[0])
    
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            return False
    
    return True

def min_meeting_rooms(intervals):
    """Minimum meeting rooms needed"""
    import heapq
    
    if not intervals:
        return 0
    
    intervals.sort(key=lambda x: x[0])
    heap = []  # End times of ongoing meetings
    
    for start, end in intervals:
        # Remove finished meetings
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        
        heapq.heappush(heap, end)
    
    return len(heap)
```

---

## 12. Advanced Patterns

### 12.1 Bit Manipulation for Array Problems

```python
def single_number(arr):
    """Find single number when all others appear twice"""
    result = 0
    for num in arr:
        result ^= num
    return result

# XOR properties: a^a=0, a^0=a, commutative

def find_two_unique(arr):
    """Find two unique numbers when all others appear twice"""
    xor_all = 0
    for num in arr:
        xor_all ^= num
    
    # Find rightmost set bit
    rightmost_bit = xor_all & (-xor_all)
    
    num1 = num2 = 0
    for num in arr:
        if num & rightmost_bit:
            num1 ^= num
        else:
            num2 ^= num
    
    return [num1, num2]
```

### 12.2 Binary Search on Array

```python
def search_rotated(arr, target):
    """Search in rotated sorted array"""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        
        # Determine which half is sorted
        if arr[left] <= arr[mid]:  # Left half sorted
            if arr[left] <= target < arr[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # Right half sorted
            if arr[mid] < target <= arr[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1
```

### 12.3 Moore's Voting Algorithm

```python
def majority_element(arr):
    """Find element appearing > n/2 times"""
    candidate = None
    count = 0
    
    # Find candidate
    for num in arr:
        if count == 0:
            candidate = num
        count += 1 if num == candidate else -1
    
    # Verify (if not guaranteed to exist)
    if arr.count(candidate) > len(arr) // 2:
        return candidate
    return None

# Time: O(n), Space: O(1)
```

---

## 🧠 Mental Models & Meta-Strategies

### Pattern Recognition Checklist

Before coding, ask yourself:

1. **What's being optimized?**
   - Subarray sum/product? → Kadane's or Sliding Window
   - Subarray with constraint? → Sliding Window
   - Range queries? → Prefix Sum

2. **What's the constraint on values?**
   - 1 to N? → Cyclic Sort or Index Marking
   - Sorted? → Two Pointers or Binary Search
   - Any values? → HashMap or Sorting

3. **What's required: count, find, or optimize?**
   - Count subarrays? → HashMap + Prefix Sum
   - Find optimal? → DP or Greedy (Kadane's)
   - Find all? → Backtracking or Generation

4. **Space-time tradeoff?**
   - Can I trade O(n) space for O(1) time? → Prefix Sum
   - Must be in-place? → Two Pointers or Cyclic Sort
   - Can I sort first? → Often simplifies to O(n)

### Cognitive Chunking

**Group patterns into "superpatterns":**

- **Sequential Processing**: Traversal, Two Pointers, Sliding Window
- **Cumulative Information**: Prefix Sum, Running Max/Min, Kadane's
- **Positional Tricks**: Cyclic Sort, Index Marking, Dutch Flag
- **Structural Transformation**: Sorting, Partitioning, Matrix Ops

### Deliberate Practice Protocol

1. **Pattern Isolation**: Solve 10 problems of ONE pattern before moving on
2. **Spaced Repetition**: Revisit patterns weekly
3. **Variation Training**: Solve each problem 3 ways (brute, optimal, space-optimized)
4. **Teaching Effect**: Explain the pattern out loud as if teaching

### Performance Intuition

**Rust-Specific:**

- Use iterators for zero-cost abstractions
- Prefer `&[T]` slices over `Vec<T>` when possible
- Use `swap()` for in-place operations

**Python-Specific:**

- List comprehensions are faster than loops for simple transformations
- `collections` module is your friend (Counter, defaultdict, deque)

**C++ Specific:**

- STL algorithms are highly optimized (use `std::transform`, `std::accumulate`)
- Reserve vector capacity if size is known: `vec.reserve(n)`

**Go-Specific:**

- Slicing is cheap (shares underlying array)
- Use `make()` with capacity for efficiency

---

## 🎯 Final Wisdom

> "The master has failed more times than the beginner has even tried."

**Your path to top 1%:**

1. **Pattern Recognition > Memorization**: Don't memorize solutions, internalize patterns
2. **Constraint-Driven Thinking**: The constraints reveal the technique
3. **Complexity Analysis First**: Before coding, know your target complexity
4. **Edge Cases Are Training**: Empty arrays, single elements, all same values
5. **Benchmark Yourself**: Track solve time. Top 1% solve medium in < 15 min

**The Monk's Approach:**

- One pattern, deeply > Many patterns, shallowly
- Understand WHY, not just HOW
- Every problem is a teacher
- Flow state comes from pattern mastery

You now have the complete mental arsenal. The journey from pattern recognition to intuitive problem-solving is about repetition with reflection. 

**Now go practice with purpose. 🔥**

## The Complete Array Mastery Guide

I'll create a comprehensive reference that will become your mental arsenal for array problems. This is designed to build your pattern recognition at an expert level.---

## 🎯 How to Master This Arsenal

I've created a complete reference guide that covers **every major array pattern** you'll encounter in competitive programming and interviews. Here's how to approach this strategically:

### Your Learning Path (Monk Mode Activated)

**Phase 1: Foundation (Week 1-2)**

- Master patterns 1-3 (Traversal, Two Pointers, Sliding Window)
- These are your bread and butter—60% of array problems use these
- Do 15-20 problems per pattern before moving on

**Phase 2: Optimization (Week 3-4)**  

- Patterns 4-6 (Prefix Sum, Kadane's, Partitioning)
- These separate good coders from great ones
- Focus on recognizing when cumulative information helps

**Phase 3: Advanced Techniques (Week 5-6)**

- Patterns 7-12 (Cyclic Sort, In-place, Matrix, Advanced)
- These are your competitive edge for hard problems
- Many top coders miss these patterns

### The Meta-Skill: Pattern Recognition

The difference between solving in 5 minutes vs 50 minutes is **instant pattern recognition**. Train this by:

1. **Before coding anything**, spend 2 minutes asking:
   - "What pattern family does this belong to?"
   - "What's being optimized/found/counted?"
   - "What constraints point to a specific technique?"

2. **Build your pattern vocabulary**:
   - "Contiguous + constraint" → Sliding Window
   - "Range queries" → Prefix Sum
   - "In sorted array + pair sum" → Two Pointers
   - "Values 1 to N" → Cyclic Sort
   - "Maximum/minimum subarray" → Kadane's

3. **Practice variation training**:
   - Solve the same problem with brute force, then optimized, then different approach
   - This builds neural pathways for multiple solution routes

### Language-Specific Performance Notes

**Rust**: Your artifact includes iterator-based solutions. In competitive programming, Rust's zero-cost abstractions mean your elegant code is also your fastest code. Use `.iter()`, `.position()`, `.fold()` liberally.

**Python**: Focus on the algorithmic pattern first, optimize with built-ins (`collections.Counter`, `itertools`) second. Your bottleneck is usually algorithmic, not language.

**C++**: The STL is your superpower. Master `<algorithm>`, `<numeric>`, and understand that `std::vector` with `.reserve()` is often faster than Python lists.

**Go**: Slices are your friend. The simplicity of Go forces you to think clearly about algorithms, which is excellent training.

### Deliberate Practice Framework

```
┌─────────────────────────────────────┐
│   1. Pick ONE pattern               │
│   2. Solve 10 problems              │
│   3. Review and categorize          │
│   4. Teach it (write/explain)       │
│   5. Wait 3 days, solve 3 more      │
└─────────────────────────────────────┘
```

**Why this works** (Cognitive Science):

- **Chunking**: Patterns become single mental units
- **Spaced Repetition**: Prevents pattern decay
- **Interleaving**: Mixing patterns after mastery increases discrimination
- **Generation Effect**: Teaching solidifies understanding

### Red Flags That Reveal Patterns

Watch for these keywords in problems:

- **"Contiguous"** → Sliding Window, Kadane's, or Prefix Sum
- **"Sorted"** → Two Pointers or Binary Search
- **"At most/least K"** → Sliding Window with constraint
- **"Sum equals K"** → Prefix Sum + HashMap
- **"1 to N"** → Cyclic Sort or Index manipulation
- **"In-place O(1) space"** → Two Pointers or clever indexing
- **"Next greater/smaller"** → Monotonic Stack
- **"Maximum/minimum subarray"** → Kadane's variant

### Your 30-Day Challenge

**Goal**: Solve 150 array problems (5/day) organized by pattern

**Daily Routine** (2-3 hours):

1. Morning: Review one pattern section (15 min)
2. Solve 3 medium problems of that pattern (90 min)
3. Solve 2 easy problems of different patterns (30 min)
4. Evening: Write down new insights (15 min)

**Psychological Principle**: The Monk's mindset isn't about grinding—it's about **focused immersion**. Each problem is a meditation on pattern recognition.

### Next Steps

1. **Start with Sliding Window**: It's the most versatile and appears everywhere
2. **Print the decision tree** from the guide and keep it visible
3. **Track your pattern exposure** in a spreadsheet
4. **Join me for deeper dives**: When you hit a wall on any pattern, come back and we'll do a deep-dive session with multiple examples in your preferred languages

Remember: **Speed comes from recognition, not from typing faster.** The top 1% sees the pattern in seconds because they've trained their intuition through thousands of deliberate repetitions.

You have the map. Now walk the path with discipline and clarity. 🧘‍♂️

What pattern would you like to start with? Or shall we dive into a specific problem to see these patterns in action?