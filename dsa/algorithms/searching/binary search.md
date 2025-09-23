# Binary Search

## Complete Binary Search Guide - Python & Rust

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Binary Search](#basic-binary-search)
3. [Binary Search Variants](#binary-search-variants)
4. [Advanced Patterns](#advanced-patterns)
5. [Real-World Applications](#real-world-applications)
6. [Performance Analysis](#performance-analysis)
7. [Common Pitfalls](#common-pitfalls)
8. [Practice Problems](#practice-problems)

## Introduction

Binary Search is a fundamental algorithm that efficiently finds elements in sorted arrays by repeatedly dividing the search space in half. This guide provides complete implementations in both Python and Rust, covering everything from basic searches to advanced applications.

**Key Properties:**

- Time Complexity: O(log n)
- Space Complexity: O(1) iterative, O(log n) recursive
- Requires sorted input
- Eliminates half the search space each iteration

## Basic Binary Search

### Standard Binary Search

**Python Implementation:**

```python
def binary_search(arr, target):
    """
    Standard binary search - returns index if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Prevent overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Recursive version
def binary_search_recursive(arr, target, left=0, right=None):
    """
    Recursive binary search implementation
    """
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = left + (right - left) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)
```

**Rust Implementation:**

```rust
fn binary_search<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

// Recursive version
fn binary_search_recursive<T: Ord>(
    arr: &[T], 
    target: &T, 
    left: usize, 
    right: usize
) -> Option<usize> {
    if left >= right {
        return None;
    }
    
    let mid = left + (right - left) / 2;
    
    match arr[mid].cmp(target) {
        std::cmp::Ordering::Equal => Some(mid),
        std::cmp::Ordering::Less => {
            binary_search_recursive(arr, target, mid + 1, right)
        },
        std::cmp::Ordering::Greater => {
            binary_search_recursive(arr, target, left, mid)
        }
    }
}
```

## Binary Search Variants

### Lower Bound (First Occurrence)

Finds the first position where target could be inserted to maintain sorted order.

**Python:**

```python
def lower_bound(arr, target):
    """
    Find the first position where target could be inserted
    Returns the leftmost position of target if it exists
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left

def find_first_occurrence(arr, target):
    """
    Find the first occurrence of target
    """
    pos = lower_bound(arr, target)
    if pos < len(arr) and arr[pos] == target:
        return pos
    return -1
```

**Rust:**

```rust
fn lower_bound<T: Ord>(arr: &[T], target: &T) -> usize {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] < *target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    left
}

fn find_first_occurrence<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let pos = lower_bound(arr, target);
    if pos < arr.len() && arr[pos] == *target {
        Some(pos)
    } else {
        None
    }
}
```

### Upper Bound (Last Occurrence)

Finds the last position where target could be inserted.

**Python:**

```python
def upper_bound(arr, target):
    """
    Find the first position greater than target
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    
    return left

def find_last_occurrence(arr, target):
    """
    Find the last occurrence of target
    """
    pos = upper_bound(arr, target) - 1
    if pos >= 0 and arr[pos] == target:
        return pos
    return -1
```

**Rust:**

```rust
fn upper_bound<T: Ord>(arr: &[T], target: &T) -> usize {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] <= *target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    left
}

fn find_last_occurrence<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let pos = upper_bound(arr, target);
    if pos > 0 && arr[pos - 1] == *target {
        Some(pos - 1)
    } else {
        None
    }
}
```

### Count Occurrences

**Python:**

```python
def count_occurrences(arr, target):
    """
    Count total occurrences of target using binary search
    """
    first = lower_bound(arr, target)
    last = upper_bound(arr, target)
    
    if first < len(arr) and arr[first] == target:
        return last - first
    return 0
```

**Rust:**

```rust
fn count_occurrences<T: Ord>(arr: &[T], target: &T) -> usize {
    let first = lower_bound(arr, target);
    let last = upper_bound(arr, target);
    
    if first < arr.len() && arr[first] == *target {
        last - first
    } else {
        0
    }
}
```

## Advanced Patterns

### Binary Search on Answer

Used when we need to find the optimal value in a range where we can verify if a value works.

**Python:**

```python
def binary_search_on_answer(check_function, left, right):
    """
    Generic binary search on answer template
    check_function: returns True if value is feasible
    """
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if check_function(mid):
            result = mid
            right = mid - 1  # Try to find a better answer
        else:
            left = mid + 1
    
    return result

# Example: Find square root (integer part)
def sqrt_binary_search(x):
    def is_valid_sqrt(mid):
        return mid * mid <= x
    
    return binary_search_on_answer(is_valid_sqrt, 0, x)
```

**Rust:**

```rust
fn binary_search_on_answer<F>(mut check: F, mut left: i64, mut right: i64) -> Option<i64>
where
    F: FnMut(i64) -> bool,
{
    let mut result = None;
    
    while left <= right {
        let mid = left + (right - left) / 2;
        
        if check(mid) {
            result = Some(mid);
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    
    result
}

// Example: Find square root
fn sqrt_binary_search(x: i64) -> i64 {
    binary_search_on_answer(|mid| mid * mid <= x, 0, x).unwrap_or(0)
}
```

### Search in Rotated Sorted Array

**Python:**

```python
def search_rotated_array(arr, target):
    """
    Search in a rotated sorted array
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        
        # Check which half is sorted
        if arr[left] <= arr[mid]:  # Left half is sorted
            if arr[left] <= target < arr[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # Right half is sorted
            if arr[mid] < target <= arr[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1

def find_rotation_point(arr):
    """
    Find the index of the smallest element (rotation point)
    """
    left, right = 0, len(arr) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] > arr[right]:
            left = mid + 1
        else:
            right = mid
    
    return left
```

**Rust:**

```rust
fn search_rotated_array(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] == target {
            return Some(mid);
        }
        
        if arr[left] <= arr[mid] {
            if arr[left] <= target && target < arr[mid] {
                right = mid;
            } else {
                left = mid + 1;
            }
        } else {
            if arr[mid] < target && target <= arr[right - 1] {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
    }
    
    None
}

fn find_rotation_point(arr: &[i32]) -> usize {
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] > arr[right] {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    left
}
```

### Peak Finding

**Python:**

```python
def find_peak_element(arr):
    """
    Find a peak element (greater than or equal to neighbors)
    """
    left, right = 0, len(arr) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < arr[mid + 1]:
            left = mid + 1
        else:
            right = mid
    
    return left

def find_peak_2d(matrix):
    """
    Find peak in 2D array using binary search
    """
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, cols - 1
    
    while left <= right:
        mid_col = left + (right - left) // 2
        
        # Find max element in this column
        max_row = 0
        for i in range(1, rows):
            if matrix[i][mid_col] > matrix[max_row][mid_col]:
                max_row = i
        
        # Check if it's a peak
        left_val = matrix[max_row][mid_col - 1] if mid_col > 0 else -1
        right_val = matrix[max_row][mid_col + 1] if mid_col < cols - 1 else -1
        
        if matrix[max_row][mid_col] >= left_val and matrix[max_row][mid_col] >= right_val:
            return (max_row, mid_col)
        elif left_val > matrix[max_row][mid_col]:
            right = mid_col - 1
        else:
            left = mid_col + 1
    
    return (-1, -1)
```

## Real-World Applications

### Library Management System

**Python:**

```python
class Book:
    def __init__(self, isbn, title, author):
        self.isbn = isbn
        self.title = title
        self.author = author
    
    def __lt__(self, other):
        return self.isbn < other.isbn

class Library:
    def __init__(self):
        self.books = []
    
    def add_book(self, book):
        # Insert while maintaining sorted order
        pos = lower_bound([b.isbn for b in self.books], book.isbn)
        self.books.insert(pos, book)
    
    def find_book(self, isbn):
        book_isbns = [b.isbn for b in self.books]
        pos = binary_search(book_isbns, isbn)
        return self.books[pos] if pos != -1 else None
    
    def find_books_in_range(self, isbn_start, isbn_end):
        book_isbns = [b.isbn for b in self.books]
        start_pos = lower_bound(book_isbns, isbn_start)
        end_pos = upper_bound(book_isbns, isbn_end)
        return self.books[start_pos:end_pos]
```

### Capacity Planning

**Python:**

```python
def min_capacity_needed(weights, days):
    """
    Find minimum ship capacity to ship all weights within given days
    """
    def can_ship_in_days(capacity):
        current_weight = 0
        days_needed = 1
        
        for weight in weights:
            if current_weight + weight > capacity:
                days_needed += 1
                current_weight = weight
                if days_needed > days:
                    return False
            else:
                current_weight += weight
        
        return True
    
    left = max(weights)  # Minimum possible capacity
    right = sum(weights)  # Maximum possible capacity
    
    while left < right:
        mid = left + (right - left) // 2
        
        if can_ship_in_days(mid):
            right = mid
        else:
            left = mid + 1
    
    return left
```

**Rust:**

```rust
fn min_capacity_needed(weights: &[i32], days: i32) -> i32 {
    fn can_ship_in_days(weights: &[i32], capacity: i32, days: i32) -> bool {
        let mut current_weight = 0;
        let mut days_needed = 1;
        
        for &weight in weights {
            if current_weight + weight > capacity {
                days_needed += 1;
                current_weight = weight;
                if days_needed > days {
                    return false;
                }
            } else {
                current_weight += weight;
            }
        }
        
        true
    }
    
    let mut left = *weights.iter().max().unwrap();
    let mut right = weights.iter().sum();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if can_ship_in_days(weights, mid, days) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    
    left
}
```

## Performance Analysis

### Time Complexity Comparison

| Operation | Linear Search | Binary Search | Notes |
|-----------|---------------|---------------|-------|
| Best Case | O(1) | O(1) | Element at first position |
| Average Case | O(n) | O(log n) | Element in middle |
| Worst Case | O(n) | O(log n) | Element not found |

### Space Complexity

- **Iterative**: O(1) - constant extra space
- **Recursive**: O(log n) - call stack depth

### Benchmark Code

**Python:**

```python
import time
import random

def benchmark_searches():
    sizes = [1000, 10000, 100000, 1000000]
    
    for size in sizes:
        arr = sorted(random.randint(1, size * 2) for _ in range(size))
        target = random.choice(arr)
        
        # Binary Search
        start_time = time.time()
        for _ in range(1000):
            binary_search(arr, target)
        binary_time = time.time() - start_time
        
        # Linear Search
        start_time = time.time()
        for _ in range(1000):
            arr.index(target) if target in arr else -1
        linear_time = time.time() - start_time
        
        print(f"Size: {size:8d} | Binary: {binary_time:.6f}s | Linear: {linear_time:.6f}s | Speedup: {linear_time/binary_time:.2f}x")
```

## Common Pitfalls

### Integer Overflow

```python
# Wrong: Can cause overflow in other languages
mid = (left + right) // 2

# Correct: Prevents overflow
mid = left + (right - left) // 2
```

### Infinite Loops

```python
# Wrong: Can cause infinite loop
while left < right:
    mid = left + (right - left) // 2
    if condition:
        left = mid  # Should be mid + 1
    else:
        right = mid

# Correct: Ensure progress
while left < right:
    mid = left + (right - left) // 2
    if condition:
        left = mid + 1
    else:
        right = mid
```

### Off-by-One Errors

```python
# Template for exact match
def binary_search_exact(arr, target):
    left, right = 0, len(arr) - 1  # Inclusive bounds
    
    while left <= right:  # <= for inclusive
        mid = left + (right - left) // 2
        # ... rest of logic

# Template for bounds
def binary_search_bounds(arr, target):
    left, right = 0, len(arr)  # Exclusive right bound
    
    while left < right:  # < for exclusive
        mid = left + (right - left) // 2
        # ... rest of logic
```

## Practice Problems

1. **Basic**: Find element in sorted array
2. **Medium**: Find first/last occurrence of element
3. **Medium**: Search in rotated sorted array
4. **Medium**: Find peak element
5. **Hard**: Median of two sorted arrays
6. **Hard**: Find K-th smallest element in sorted matrix
7. **Application**: Aggressive cows problem
8. **Application**: Book allocation problem

### Complete Test Suite

**Python:**

```python
def test_binary_search():
    # Test cases
    test_cases = [
        ([1, 2, 3, 4, 5], 3, 2),
        ([1, 2, 3, 4, 5], 1, 0),
        ([1, 2, 3, 4, 5], 5, 4),
        ([1, 2, 3, 4, 5], 6, -1),
        ([], 1, -1),
        ([1], 1, 0),
        ([1], 2, -1),
    ]
    
    for arr, target, expected in test_cases:
        result = binary_search(arr, target)
        assert result == expected, f"Failed for {arr}, {target}: got {result}, expected {expected}"
    
    print("All tests passed!")

if __name__ == "__main__":
    test_binary_search()
    benchmark_searches()
```

This comprehensive guide covers all aspects of binary search from basic implementation to advanced applications. The key to mastering binary search is understanding the invariants and choosing the right template for each problem type.

I'll create a detailed ASCII diagram that visualizes how Binary Search works step by step, showing the algorithm in action.I've created a comprehensive ASCII diagram that visualizes Binary Search step by step! The diagram shows:

**Key Features:**

- **Step-by-step execution** searching for target 7 in array [1,3,5,7,9,11,13,15,17]
- **Visual representation** of how the search space gets eliminated each iteration
- **Detailed trace table** showing left, right, mid values at each step
- **Search space reduction visualization** showing how 9 elements → 5 → 2 → 1 → FOUND
- **Algorithm flow diagram** with decision points and actions
- **Memory access pattern** comparison with linear search
- **Edge cases** including empty arrays, single elements, and boundary conditions

**Educational Highlights:**

- Shows why it's O(log n) - each step eliminates half the remaining elements
- Demonstrates the "divide and conquer" approach visually
- Compares with linear search to show efficiency gains
- Includes proper mid-point calculation to prevent overflow
- Shows the complete algorithm flow from start to finish

The diagram makes it easy to understand how Binary Search works by following the actual execution path, seeing exactly which elements are compared, and how the algorithm intelligently eliminates large portions of the search space with each decision.

This visualization would be perfect for teaching Binary Search concepts or for reference when implementing the algorithm!

## Binary Search Step-by-Step ASCII Visualization

## Example: Searching for target = 7 in array [1, 3, 5, 7, 9, 11, 13, 15, 17]

```ascii
Array Indices:  0   1   2   3   4   5    6    7    8
Array Values:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
                                ^
                           TARGET = 7
```

---

## Step 1: Initialize Search Space

```ascii
Initial State:
left = 0, right = 8 (last index)

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         ^                                   ^
        left                               right
         |                                   |
         └─────────── Search Space ──────────┘

Calculate mid: mid = left + (right - left) / 2 = 0 + (8 - 0) / 2 = 4
```

---

## Step 2: First Comparison

```ascii
Mid element: arr[4] = 9
Compare: 9 vs 7 (target)
Result: 9 > 7, so target is in LEFT half

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         ^           ^   ^                   ^
        left      target mid              right
         |           |                       |
         └─── Keep ──┘   └── Eliminate ─────┘

Action: right = mid - 1 = 4 - 1 = 3
New search space: left = 0, right = 3
```

---

## Step 3: Second Iteration

```ascii
Current State:
left = 0, right = 3

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         ^           ^   X   X    X    X    X
        left       right
         |           |
         └─ Search ──┘

Calculate mid: mid = 0 + (3 - 0) / 2 = 1
Mid element: arr[1] = 3
Compare: 3 vs 7 (target)
Result: 3 < 7, so target is in RIGHT half
```

---

## Step 4: Second Comparison

```ascii
Mid element: arr[1] = 3
Compare: 3 vs 7 (target)
Result: 3 < 7, so target is in RIGHT half

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         X   ^       ^   X   X    X    X    X
           mid    right
             |       |
     Eliminate     Keep
             
Action: left = mid + 1 = 1 + 1 = 2
New search space: left = 2, right = 3
```

---

## Step 5: Third Iteration

```ascii
Current State:
left = 2, right = 3

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         X   X   ^   ^   X   X    X    X    X
               left right
                 |   |
                 └─┬─┘
            Search Space (2 elements)

Calculate mid: mid = 2 + (3 - 2) / 2 = 2
Mid element: arr[2] = 5
Compare: 5 vs 7 (target)
Result: 5 < 7, so target is in RIGHT half
```

---

## Step 6: Third Comparison

```ascii
Mid element: arr[2] = 5
Compare: 5 vs 7 (target)
Result: 5 < 7, so target is in RIGHT half

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         X   X   ^   ^   X   X    X    X    X
               mid right
                 |   |
         Eliminate   Keep
                 
Action: left = mid + 1 = 2 + 1 = 3
New search space: left = 3, right = 3
```

---

## Step 7: Fourth Iteration - FOUND

```ascii
Current State:
left = 3, right = 3

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Index:   0   1   2   3   4   5    6    7    8
         X   X   X   ^   X   X    X    X    X
                   left
                   right
                   mid
                     |
            Search Space (1 element)

Calculate mid: mid = 3 + (3 - 3) / 2 = 3
Mid element: arr[3] = 7
Compare: 7 vs 7 (target)
Result: MATCH FOUND! ✓

Return index: 3
```

---

## Complete Search Trace Summary

```ascii
┌─────┬─────┬──────┬─────────┬──────────┬──────────────┬────────────┐
│Step │Left │Right │  Mid    │arr[mid] │Comparison   │    Action   │
├─────┼─────┼──────┼─────────┼─────────┼─────────────┼─────────────┤
│  1  │  0  │  8   │    4    │    9    │  9 > 7      │right = 3    │
│  2  │  0  │  3   │    1    │    3    │  3 < 7      │left = 2     │
│  3  │  2  │  3   │    2    │    5    │  5 < 7      │left = 3     │
│  4  │  3  │  3   │    3    │    7    │  7 = 7      │FOUND! ✓     │
└─────┴─────┴──────┴─────────┴─────────┴─────────────┴─────────────┘

Total comparisons: 4
Maximum possible comparisons: ⌈log₂(9)⌉ = 4
Search space reduction: 9 → 5 → 2 → 1 → FOUND
```

---

## Search Space Visualization

```ascii
Initial:    [1,  3,  5,  7,  9, 11,  13,  15,  17]  (9 elements)
             ←─────────── Search Space ────────────→

After 1st:  [1,  3,  5,  7] [9, 11,  13,  15,  17]  (4 elements)
             ←─── Keep ───→  ←──── Eliminate ────→

After 2nd:  [1,  3] [5,  7] [9, 11,  13,  15,  17]  (2 elements)
             ←─ Elim→ ←Keep→ ←──── Eliminated ────→

After 3rd:  [1,  3] [5] [7] [9, 11,  13,  15,  17]  (1 element)
             ←─ Eliminated ─→ ↑   ←──── Eliminated ────→
                             Keep

Found:      [1,  3,  5] [7] [9, 11,  13,  15,  17]  (TARGET!)
             ←─ Eliminated ─→ ✓  ←──── Eliminated ────→
```

---

## Algorithm Flow Diagram

```ascii
    ┌─────────────────────────┐
    │     START SEARCH        │
    │   left=0, right=n-1     │
    └─────────┬───────────────┘
              │
              ▼
    ┌─────────────────────────┐
    │    left <= right?       │
    └─────────┬───────────────┘
              │
        ┌─────▼─────┐
        │    YES    │         ┌─────────┐
        └─────┬─────┘         │   NO    │
              │               └─────┬───┘
              ▼                     │
    ┌─────────────────────────┐     │
    │  mid = left +           │     │
    │  (right-left)/2         │     │
    └─────────┬───────────────┘     │
              │                     │
              ▼                     │
    ┌─────────────────────────┐     │
    │  Compare arr[mid]       │     │
    │  with target            │     │
    └─────────┬───────────────┘     │
              │                     │
      ┌───────▼───────┐             │
      │               │             │
   ┌──▼─┐ ┌──────┐ ┌──▼──┐          │
   │ <  │ │  =   │ │  >  │          │
   └─┬──┘ └──┬───┘ └──┬──┘          │
     │      │         │             │
     ▼      │         ▼             │
┌─────────┐ │  ┌──────────┐         │
│left =   │ │  │right =   │         │
│mid + 1  │ │  │mid - 1   │         │
└─────┬───┘ │  └─────┬────┘         │
      │     │        │              │
      │     │        │              │
      └─────┼────────┘              │
            │                       │
            ▼                       │
    ┌───────────────┐               │
    │  FOUND!       │◄────────────--┘
    │ Return mid    │
    └───────────────┘
            │
            ▼
    ┌───────────────┐
    │ NOT FOUND     │
    │ Return -1     │
    └───────────────┘
```

---

## Memory Access Pattern

```ascii
Memory Layout (conceptual):
┌───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ 1 │ 3 │ 5 │ 7 │ 9 │11 │13 │15 │17 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6   7   8

Access Pattern:
Step 1: Access index 4 → value 9     ████████████████████████████████████████
Step 2: Access index 1 → value 3     ████████
Step 3: Access index 2 → value 5     ████████████
Step 4: Access index 3 → value 7     ████████████████ ← FOUND!

Total Memory Accesses: 4
Linear Search would need: up to 4 accesses (best case for this example)
Worst case for Binary: ⌈log₂(9)⌉ = 4 accesses
Worst case for Linear: 9 accesses
```

---

## Comparison with Linear Search

```ascii
LINEAR SEARCH for target = 7:
Step 1: [1] ≠ 7, continue...
Step 2: [3] ≠ 7, continue...  
Step 3: [5] ≠ 7, continue...
Step 4: [7] = 7, FOUND! ✓

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Access:  ↑   ↑   ↑   ↑
         1   2   3   4 ← Found in 4 steps

BINARY SEARCH for target = 7:
Step 1: Check middle (index 4): [9] > 7, go left
Step 2: Check middle (index 1): [3] < 7, go right  
Step 3: Check middle (index 2): [5] < 7, go right
Step 4: Check middle (index 3): [7] = 7, FOUND! ✓

Array:  [1,  3,  5,  7,  9, 11,  13,  15,  17]
Access:             ↑   ↑    ↑
                   4   2    3   1 ← Found in 4 steps

For this example: Same number of steps!
But for target = 17: Linear = 9 steps, Binary = 4 steps
```

---

## Edge Cases Visualization

### Empty Array

```ascii
Array: []
Result: Element not found (immediate return)
```

### Single Element - Found

```ascii
Array: [7]
Index:  0
        ↑
     target=7

left=0, right=0, mid=0
arr[0] = 7 = target ✓
Result: Found at index 0
```

### Single Element - Not Found

```ascii
Array: [5]  
Index:  0   
        ↑   
     target=7

left=0, right=0, mid=0
arr[0] = 5 ≠ 7
Result: Not found
```

### Target at Beginning

```ascii
Array: [1,  3,  5,  7,  9]
        ↑
     target=1

Step 1: mid=2, arr[2]=5 > 1, go left
Step 2: mid=0, arr[0]=1 = 1 ✓
Result: Found at index 0 in 2 steps
```

### Target at End

```ascii
Array: [1,  3,  5,  7,  9]
                        ↑
                     target=9

Step 1: mid=2, arr[2]=5 < 9, go right
Step 2: mid=4, arr[4]=9 = 9 ✓
Result: Found at index 4 in 2 steps
```

This visualization shows how Binary Search efficiently narrows down the search space by half with each comparison, making it much more efficient than linear search for large datasets.

I'll create a comprehensive guide covering Binary Search implementations in both Python and Rust, including various patterns and real-world applications.I've created a comprehensive guide to Binary Search implementations in Python and Rust. The guide covers:

**Core Topics:**

- Basic binary search (iterative and recursive)
- All major variants (lower bound, upper bound, count occurrences)
- Advanced patterns (search on answer, rotated arrays, peak finding)
- Real-world applications (library systems, capacity planning)
- Performance analysis and benchmarking
- Common pitfalls and how to avoid them

**Key Features:**

- Complete, working implementations in both languages
- Detailed explanations of each variant
- Time/space complexity analysis
- Practical examples and use cases
- Test suites and benchmarking code
- Common mistakes and debugging tips

The guide emphasizes the different templates needed for different types of binary search problems:

- **Exact match**: Use inclusive bounds with `left <= right`
- **Bounds finding**: Use exclusive right bound with `left < right`
- **Search on answer**: Apply binary search to optimization problems

Each implementation includes proper overflow prevention and follows language-specific best practices. The Rust implementations leverage the type system and pattern matching for more robust code, while the Python versions focus on readability and ease of understanding.

Would you like me to expand on any particular section or add more specific examples for certain problem types?