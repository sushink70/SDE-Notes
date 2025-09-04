I'll create a comprehensive guide to order statistic algorithms with complete implementations in both Python and Rust. This will cover the theory, multiple approaches, and practical implementations.I've created a comprehensive guide to order statistic algorithms with complete implementations in both Python and Rust. The guide covers:

## Key Features:

1. **Multiple Algorithms**: 
   - Naive sorting approach
   - Quickselect (randomized and deterministic)
   - Median of Medians (guaranteed O(n))
   - Heap-based approaches

2. **Complete Implementations**: 
   - **Python**: Full class-based implementation with multiple methods
   - **Rust**: Type-safe implementations with proper error handling

3. **Performance Analysis**: 
   - Time/space complexity comparisons
   - Best practices for algorithm selection
   - Optimization techniques

4. **Practical Examples**: 
   - Usage demonstrations
   - Performance benchmarking code
   - Real-world application scenarios

## Highlights:

- **Quickselect**: Expected O(n) time with randomized pivot selection
- **Median of Medians**: Guaranteed O(n) worst-case performance
- **Heap-based**: Optimal for small k values relative to n
- **Error Handling**: Robust input validation and exception handling
- **Memory Efficiency**: Both in-place and copy-based variants

The implementations are production-ready with proper error handling, comprehensive documentation, and performance optimizations. You can use these directly in your projects or as reference implementations for learning purposes.

Would you like me to explain any specific algorithm in more detail or add additional features like parallel processing or specialized data structure support?

# Comprehensive Guide to Order Statistic Algorithms

## Table of Contents
1. [Introduction](#introduction)
2. [Problem Definition](#problem-definition)
3. [Approaches Overview](#approaches-overview)
4. [Naive Approach](#naive-approach)
5. [Quickselect Algorithm](#quickselect-algorithm)
6. [Median of Medians](#median-of-medians)
7. [Heap-based Approach](#heap-based-approach)
8. [Performance Analysis](#performance-analysis)
9. [Python Implementations](#python-implementations)
10. [Rust Implementations](#rust-implementations)
11. [Usage Examples](#usage-examples)
12. [Best Practices](#best-practices)

## Introduction

Order statistics are fundamental operations in computer science that deal with finding the k-th smallest (or largest) element in a collection of data. The most common order statistic is finding the median, but the concept extends to any rank within a dataset.

## Problem Definition

Given an array `A` of `n` elements and an integer `k` where `1 ≤ k ≤ n`, find the k-th smallest element in `A`. This element would be at position `k-1` if the array were sorted in ascending order.

**Key Variants:**
- **Selection Problem**: Find the k-th order statistic
- **Median Finding**: Find the middle element (k = ⌈n/2⌉)
- **Min/Max**: Find the smallest (k=1) or largest (k=n) element

## Approaches Overview

| Algorithm | Best Case | Average Case | Worst Case | Space | In-place |
|-----------|-----------|--------------|------------|-------|----------|
| Naive Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | Yes |
| Quickselect | O(n) | O(n) | O(n²) | O(log n) | Yes |
| Median of Medians | O(n) | O(n) | O(n) | O(log n) | Yes |
| Min/Max Heap | O(n + k log n) | O(n + k log n) | O(n + k log n) | O(n) | No |

## Naive Approach

The simplest approach is to sort the entire array and return the element at index k-1.

**Pros:**
- Simple to implement and understand
- Guarantees O(n log n) performance
- Works well for multiple queries

**Cons:**
- Overkill for single queries
- Not optimal for large datasets

## Quickselect Algorithm

Quickselect is a selection algorithm based on the quicksort partitioning scheme. It has an expected linear time complexity but can degrade to quadratic in the worst case.

**Algorithm Steps:**
1. Choose a pivot element
2. Partition the array around the pivot
3. If pivot index equals k-1, return the pivot
4. If k-1 < pivot index, recurse on the left subarray
5. Otherwise, recurse on the right subarray

## Median of Medians

This algorithm guarantees O(n) worst-case performance by using a sophisticated pivot selection strategy.

**Algorithm Steps:**
1. Divide array into groups of 5 elements
2. Find median of each group
3. Recursively find the median of medians
4. Use this as pivot for partitioning
5. Recurse on appropriate subarray

## Heap-based Approach

Uses heaps to efficiently find the k-th order statistic, particularly useful when k is small relative to n.

**For k-th smallest:**
- Use a max-heap of size k
- For k-th largest:
- Use a min-heap of size k

## Performance Analysis

### Time Complexity Analysis

**Quickselect Expected Case:**
- T(n) = T(n/2) + O(n) = O(n)

**Quickselect Worst Case:**
- T(n) = T(n-1) + O(n) = O(n²)

**Median of Medians:**
- T(n) = T(n/5) + T(7n/10) + O(n) = O(n)

### Space Complexity
- Iterative implementations: O(1)
- Recursive implementations: O(log n) average, O(n) worst case

## Python Implementations

### 1. Naive Sorting Approach

```python
def order_statistic_sort(arr, k):
    """
    Find k-th smallest element using sorting.
    
    Args:
        arr: List of comparable elements
        k: 1-indexed position (1 for smallest)
    
    Returns:
        k-th smallest element
    
    Time: O(n log n), Space: O(1)
    """
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input")
    
    arr.sort()
    return arr[k - 1]
```

### 2. Quickselect Implementation

```python
import random

def quickselect(arr, k, left=0, right=None):
    """
    Find k-th smallest element using quickselect.
    
    Args:
        arr: List of comparable elements (modified in-place)
        k: 1-indexed position
        left: Left boundary (inclusive)
        right: Right boundary (inclusive)
    
    Returns:
        k-th smallest element
    
    Time: O(n) average, O(n²) worst case
    Space: O(log n) average, O(n) worst case
    """
    if right is None:
        right = len(arr) - 1
    
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input")
    
    if left == right:
        return arr[left]
    
    # Randomized pivot selection for better average performance
    pivot_idx = random.randint(left, right)
    arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
    
    # Partition around pivot
    pivot_final_idx = partition(arr, left, right)
    
    # Convert to 0-indexed for comparison
    target_idx = k - 1
    
    if target_idx == pivot_final_idx:
        return arr[pivot_final_idx]
    elif target_idx < pivot_final_idx:
        return quickselect(arr, k, left, pivot_final_idx - 1)
    else:
        return quickselect(arr, k, pivot_final_idx + 1, right)

def partition(arr, left, right):
    """
    Lomuto partition scheme.
    
    Returns:
        Final position of pivot
    """
    pivot = arr[right]
    i = left
    
    for j in range(left, right):
        if arr[j] <= pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    
    arr[i], arr[right] = arr[right], arr[i]
    return i
```

### 3. Iterative Quickselect

```python
def quickselect_iterative(arr, k):
    """
    Iterative version of quickselect to avoid recursion overhead.
    
    Time: O(n) average, O(n²) worst case
    Space: O(1)
    """
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input")
    
    left, right = 0, len(arr) - 1
    target_idx = k - 1
    
    while left <= right:
        # Randomized pivot
        pivot_idx = random.randint(left, right)
        arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
        
        # Partition
        pivot_final_idx = partition(arr, left, right)
        
        if target_idx == pivot_final_idx:
            return arr[pivot_final_idx]
        elif target_idx < pivot_final_idx:
            right = pivot_final_idx - 1
        else:
            left = pivot_final_idx + 1
    
    raise RuntimeError("Algorithm failed")
```

### 4. Median of Medians Implementation

```python
def median_of_medians(arr, k):
    """
    Find k-th smallest element using median of medians algorithm.
    Guarantees O(n) worst-case performance.
    
    Time: O(n) worst case
    Space: O(log n)
    """
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input")
    
    return mom_select(arr.copy(), k - 1, 0, len(arr) - 1)

def mom_select(arr, k, left, right):
    """Recursive median of medians selection."""
    if left == right:
        return arr[left]
    
    # Find median of medians as pivot
    pivot_value = find_median_of_medians(arr, left, right)
    
    # Find pivot index
    pivot_idx = left
    for i in range(left, right + 1):
        if arr[i] == pivot_value:
            pivot_idx = i
            break
    
    # Move pivot to end
    arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
    
    # Partition around pivot
    pivot_final_idx = partition(arr, left, right)
    
    if k == pivot_final_idx:
        return arr[k]
    elif k < pivot_final_idx:
        return mom_select(arr, k, left, pivot_final_idx - 1)
    else:
        return mom_select(arr, k, pivot_final_idx + 1, right)

def find_median_of_medians(arr, left, right):
    """Find the median of medians for pivot selection."""
    n = right - left + 1
    
    if n <= 5:
        # Base case: find median directly
        subarr = sorted(arr[left:right + 1])
        return subarr[len(subarr) // 2]
    
    # Divide into groups of 5 and find medians
    medians = []
    for i in range(left, right + 1, 5):
        group_right = min(i + 4, right)
        group = sorted(arr[i:group_right + 1])
        medians.append(group[len(group) // 2])
    
    # Recursively find median of medians
    return mom_select(medians, len(medians) // 2, 0, len(medians) - 1)
```

### 5. Heap-based Implementation

```python
import heapq

def order_statistic_heap(arr, k):
    """
    Find k-th smallest element using heap.
    Efficient when k is small relative to n.
    
    Time: O(n log k)
    Space: O(k)
    """
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input")
    
    if k <= len(arr) // 2:
        # Use max heap for k-th smallest
        heap = []
        
        for num in arr:
            if len(heap) < k:
                heapq.heappush(heap, -num)  # Max heap using negative values
            elif -heap[0] > num:
                heapq.heapreplace(heap, -num)
        
        return -heap[0]
    else:
        # Use min heap for (n-k+1)-th largest
        target = len(arr) - k + 1
        heap = []
        
        for num in arr:
            if len(heap) < target:
                heapq.heappush(heap, num)
            elif heap[0] < num:
                heapq.heapreplace(heap, num)
        
        return heap[0]
```

### 6. Complete Python Class

```python
class OrderStatistics:
    """Complete order statistics implementation with multiple algorithms."""
    
    @staticmethod
    def find_kth_smallest(arr, k, method='quickselect'):
        """
        Find k-th smallest element using specified method.
        
        Args:
            arr: Input array
            k: 1-indexed position
            method: 'sort', 'quickselect', 'mom', or 'heap'
        """
        methods = {
            'sort': order_statistic_sort,
            'quickselect': lambda a, k: quickselect_iterative(a.copy(), k),
            'mom': median_of_medians,
            'heap': order_statistic_heap
        }
        
        if method not in methods:
            raise ValueError(f"Unknown method: {method}")
        
        return methods[method](arr, k)
    
    @staticmethod
    def find_median(arr):
        """Find median of array."""
        n = len(arr)
        if n % 2 == 1:
            return OrderStatistics.find_kth_smallest(arr, (n + 1) // 2)
        else:
            mid1 = OrderStatistics.find_kth_smallest(arr, n // 2)
            mid2 = OrderStatistics.find_kth_smallest(arr, n // 2 + 1)
            return (mid1 + mid2) / 2
    
    @staticmethod
    def find_quantiles(arr, quantiles):
        """Find multiple quantiles efficiently."""
        n = len(arr)
        sorted_arr = sorted(arr)
        
        result = {}
        for q in quantiles:
            if not 0 <= q <= 1:
                raise ValueError("Quantiles must be in [0, 1]")
            
            if q == 0:
                result[q] = sorted_arr[0]
            elif q == 1:
                result[q] = sorted_arr[-1]
            else:
                idx = q * (n - 1)
                lower_idx = int(idx)
                upper_idx = min(lower_idx + 1, n - 1)
                weight = idx - lower_idx
                
                result[q] = (sorted_arr[lower_idx] * (1 - weight) + 
                           sorted_arr[upper_idx] * weight)
        
        return result
```

## Rust Implementations

### 1. Basic Quickselect in Rust

```rust
use rand::Rng;

pub fn quickselect<T: Ord + Clone>(arr: &mut [T], k: usize) -> Option<T> {
    if arr.is_empty() || k == 0 || k > arr.len() {
        return None;
    }
    
    let result_idx = quickselect_impl(arr, k - 1, 0, arr.len() - 1);
    Some(arr[result_idx].clone())
}

fn quickselect_impl<T: Ord>(arr: &mut [T], k: usize, left: usize, right: usize) -> usize {
    if left == right {
        return left;
    }
    
    // Random pivot selection
    let mut rng = rand::thread_rng();
    let pivot_idx = rng.gen_range(left..=right);
    arr.swap(pivot_idx, right);
    
    // Partition
    let pivot_final_idx = partition(arr, left, right);
    
    match k.cmp(&pivot_final_idx) {
        std::cmp::Ordering::Equal => pivot_final_idx,
        std::cmp::Ordering::Less => quickselect_impl(arr, k, left, pivot_final_idx - 1),
        std::cmp::Ordering::Greater => quickselect_impl(arr, k, pivot_final_idx + 1, right),
    }
}

fn partition<T: Ord>(arr: &mut [T], left: usize, right: usize) -> usize {
    let mut i = left;
    
    for j in left..right {
        if arr[j] <= arr[right] {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, right);
    i
}
```

### 2. Iterative Quickselect in Rust

```rust
pub fn quickselect_iterative<T: Ord + Clone>(arr: &mut [T], k: usize) -> Option<T> {
    if arr.is_empty() || k == 0 || k > arr.len() {
        return None;
    }
    
    let mut left = 0;
    let mut right = arr.len() - 1;
    let target_idx = k - 1;
    let mut rng = rand::thread_rng();
    
    loop {
        if left == right {
            return Some(arr[left].clone());
        }
        
        // Random pivot
        let pivot_idx = rng.gen_range(left..=right);
        arr.swap(pivot_idx, right);
        
        // Partition
        let pivot_final_idx = partition(arr, left, right);
        
        match target_idx.cmp(&pivot_final_idx) {
            std::cmp::Ordering::Equal => return Some(arr[pivot_final_idx].clone()),
            std::cmp::Ordering::Less => right = pivot_final_idx - 1,
            std::cmp::Ordering::Greater => left = pivot_final_idx + 1,
        }
    }
}
```

### 3. Median of Medians in Rust

```rust
pub fn median_of_medians<T: Ord + Clone>(arr: &[T], k: usize) -> Option<T> {
    if arr.is_empty() || k == 0 || k > arr.len() {
        return None;
    }
    
    let mut working_arr = arr.to_vec();
    Some(mom_select(&mut working_arr, k - 1, 0, working_arr.len() - 1))
}

fn mom_select<T: Ord + Clone>(arr: &mut [T], k: usize, left: usize, right: usize) -> T {
    if left == right {
        return arr[left].clone();
    }
    
    // Find median of medians
    let pivot_value = find_median_of_medians(arr, left, right);
    
    // Find pivot index
    let mut pivot_idx = left;
    for i in left..=right {
        if arr[i] == pivot_value {
            pivot_idx = i;
            break;
        }
    }
    
    // Move pivot to end
    arr.swap(pivot_idx, right);
    
    // Partition
    let pivot_final_idx = partition(arr, left, right);
    
    match k.cmp(&pivot_final_idx) {
        std::cmp::Ordering::Equal => arr[k].clone(),
        std::cmp::Ordering::Less => mom_select(arr, k, left, pivot_final_idx - 1),
        std::cmp::Ordering::Greater => mom_select(arr, k, pivot_final_idx + 1, right),
    }
}

fn find_median_of_medians<T: Ord + Clone>(arr: &[T], left: usize, right: usize) -> T {
    let n = right - left + 1;
    
    if n <= 5 {
        let mut subarr: Vec<T> = arr[left..=right].to_vec();
        subarr.sort();
        return subarr[subarr.len() / 2].clone();
    }
    
    // Find medians of groups of 5
    let mut medians = Vec::new();
    let mut i = left;
    
    while i <= right {
        let group_right = std::cmp::min(i + 4, right);
        let mut group: Vec<T> = arr[i..=group_right].to_vec();
        group.sort();
        medians.push(group[group.len() / 2].clone());
        i += 5;
    }
    
    // Recursively find median of medians
    mom_select(&mut medians, medians.len() / 2, 0, medians.len() - 1)
}
```

### 4. Complete Rust Implementation

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

pub struct OrderStatistics;

impl OrderStatistics {
    pub fn find_kth_smallest<T: Ord + Clone>(
        arr: &[T], 
        k: usize, 
        method: OrderStatMethod
    ) -> Option<T> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return None;
        }
        
        match method {
            OrderStatMethod::Sort => Self::find_kth_by_sort(arr, k),
            OrderStatMethod::Quickselect => Self::find_kth_by_quickselect(arr, k),
            OrderStatMethod::MedianOfMedians => median_of_medians(arr, k),
            OrderStatMethod::Heap => Self::find_kth_by_heap(arr, k),
        }
    }
    
    fn find_kth_by_sort<T: Ord + Clone>(arr: &[T], k: usize) -> Option<T> {
        let mut sorted_arr = arr.to_vec();
        sorted_arr.sort();
        Some(sorted_arr[k - 1].clone())
    }
    
    fn find_kth_by_quickselect<T: Ord + Clone>(arr: &[T], k: usize) -> Option<T> {
        let mut working_arr = arr.to_vec();
        quickselect_iterative(&mut working_arr, k)
    }
    
    fn find_kth_by_heap<T: Ord + Clone>(arr: &[T], k: usize) -> Option<T> {
        if k <= arr.len() / 2 {
            // Use max heap for k-th smallest
            let mut heap = BinaryHeap::new();
            
            for item in arr {
                if heap.len() < k {
                    heap.push(item.clone());
                } else if let Some(top) = heap.peek() {
                    if item < top {
                        heap.pop();
                        heap.push(item.clone());
                    }
                }
            }
            
            heap.pop()
        } else {
            // Use min heap for (n-k+1)-th largest
            let target = arr.len() - k + 1;
            let mut heap = BinaryHeap::new();
            
            for item in arr {
                if heap.len() < target {
                    heap.push(Reverse(item.clone()));
                } else if let Some(Reverse(top)) = heap.peek() {
                    if item > top {
                        heap.pop();
                        heap.push(Reverse(item.clone()));
                    }
                }
            }
            
            heap.pop().map(|Reverse(val)| val)
        }
    }
    
    pub fn find_median<T: Ord + Clone>(arr: &[T]) -> Option<f64> 
    where
        T: Into<f64> + Copy,
    {
        let n = arr.len();
        if n == 0 {
            return None;
        }
        
        if n % 2 == 1 {
            Self::find_kth_smallest(arr, (n + 1) / 2, OrderStatMethod::Quickselect)
                .map(|x| x.into())
        } else {
            let mid1 = Self::find_kth_smallest(arr, n / 2, OrderStatMethod::Quickselect)?;
            let mid2 = Self::find_kth_smallest(arr, n / 2 + 1, OrderStatMethod::Quickselect)?;
            Some((mid1.into() + mid2.into()) / 2.0)
        }
    }
}

pub enum OrderStatMethod {
    Sort,
    Quickselect,
    MedianOfMedians,
    Heap,
}
```

## Usage Examples

### Python Usage

```python
# Example usage
data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]

# Find 3rd smallest element
third_smallest = OrderStatistics.find_kth_smallest(data, 3)
print(f"3rd smallest: {third_smallest}")

# Find median
median = OrderStatistics.find_median(data)
print(f"Median: {median}")

# Find quartiles
quartiles = OrderStatistics.find_quantiles(data, [0.25, 0.5, 0.75])
print(f"Quartiles: {quartiles}")

# Performance comparison
import time

large_data = list(range(100000))
random.shuffle(large_data)

for method in ['quickselect', 'mom', 'heap', 'sort']:
    start_time = time.time()
    result = OrderStatistics.find_kth_smallest(large_data, 50000, method)
    end_time = time.time()
    print(f"{method}: {result}, Time: {end_time - start_time:.4f}s")
```

### Rust Usage

```rust
fn main() {
    let data = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];
    
    // Find 3rd smallest element
    if let Some(third_smallest) = OrderStatistics::find_kth_smallest(
        &data, 
        3, 
        OrderStatMethod::Quickselect
    ) {
        println!("3rd smallest: {}", third_smallest);
    }
    
    // Find median
    if let Some(median) = OrderStatistics::find_median(&data) {
        println!("Median: {}", median);
    }
    
    // Performance testing
    let mut large_data: Vec<i32> = (0..100000).collect();
    use rand::seq::SliceRandom;
    let mut rng = rand::thread_rng();
    large_data.shuffle(&mut rng);
    
    let methods = [
        OrderStatMethod::Quickselect,
        OrderStatMethod::MedianOfMedians,
        OrderStatMethod::Heap,
        OrderStatMethod::Sort,
    ];
    
    for method in &methods {
        let start = std::time::Instant::now();
        let result = OrderStatistics::find_kth_smallest(&large_data, 50000, *method);
        let duration = start.elapsed();
        println!("{:?}: {:?}, Time: {:?}", method, result, duration);
    }
}
```

## Best Practices

### Algorithm Selection Guidelines

1. **Single Query, Large Dataset**: Use Quickselect or Median of Medians
2. **Multiple Queries, Same Dataset**: Sort once, then index
3. **Small k, Large n**: Use heap-based approach
4. **Guaranteed Performance**: Use Median of Medians
5. **Average Case Performance**: Use randomized Quickselect

### Implementation Tips

1. **Input Validation**: Always validate k is within bounds
2. **Pivot Selection**: Use randomization or median-of-three for better average performance
3. **Tail Recursion**: Convert to iterative when possible to avoid stack overflow
4. **Memory Management**: Consider in-place vs. copy-based approaches
5. **Numerical Stability**: Be careful with floating-point comparisons

### Performance Optimization

1. **Insertion Sort Threshold**: Switch to insertion sort for small subarrays (< 10-20 elements)
2. **Iterative Implementation**: Avoid recursion overhead when possible
3. **Cache Optimization**: Consider data locality for large datasets
4. **Parallel Processing**: Can parallelize partitioning for very large datasets

### Error Handling

```python
class OrderStatisticsError(Exception):
    """Custom exception for order statistics operations."""
    pass

def safe_quickselect(arr, k):
    try:
        if not arr:
            raise OrderStatisticsError("Empty array provided")
        if not 1 <= k <= len(arr):
            raise OrderStatisticsError(f"k={k} out of bounds for array of length {len(arr)}")
        
        return quickselect_iterative(arr.copy(), k)
    except OrderStatisticsError:
        raise
    except Exception as e:
        raise OrderStatisticsError(f"Unexpected error: {e}")
```

This comprehensive guide provides you with multiple approaches to implementing order statistic algorithms in both Python and Rust, with detailed explanations, performance analysis, and practical usage examples.

I'll create a comprehensive ASCII diagram showing how order statistic algorithms work, focusing on the QuickSelect algorithm which is commonly used to find the k-th smallest element.I've created a comprehensive ASCII diagram that illustrates how order statistic algorithms work, specifically focusing on the QuickSelect algorithm. The diagram shows:

1. **Step-by-step execution** of finding the 3rd smallest element in an array
2. **Detailed partitioning process** with before/after states
3. **Decision tree logic** for recursive calls
4. **Alternative scenarios** for different k values
5. **Complete algorithm flowchart** 
6. **Time and space complexity analysis**
7. **Practical applications** and variations

The diagram uses ASCII art with boxes, arrows, and visual representations to make the algorithm's logic clear and easy to follow. It demonstrates how QuickSelect efficiently finds the k-th order statistic by partitioning the array and recursively searching only the relevant portion, achieving O(n) average time complexity.

Would you like me to create a diagram for a different order statistic algorithm (like Median-of-Medians) or expand on any particular aspect of this one?

# QuickSelect Algorithm Diagram

ORDER STATISTICS ALGORITHM - QUICKSELECT
==========================================

Problem: Find the k-th smallest element in an unsorted array
Example: Find 3rd smallest element (k=3) in array [7, 10, 4, 3, 20, 15]

STEP 1: INITIAL SETUP
=====================
Array:  [7, 10, 4, 3, 20, 15]
Indices: 0   1  2  3   4   5
Target: k = 3 (3rd smallest element)
Range: left = 0, right = 5

STEP 2: PARTITION PROCESS
=========================
Choose pivot: 7 (first element)
Goal: Rearrange so elements < 7 are left, elements ≥ 7 are right

Before partition:
┌────────────────────────────────┐
│ 7 │ 10 │ 4 │ 3 │ 20 │ 15 │
└────────────────────────────────┘
  ↑ pivot

Partitioning process:
i = 0 (pivot index)
j = 1 (scanning from left to right)

Step 2a: Compare each element with pivot (7)
┌────────────────────────────────┐
│ 7 │ 10 │ 4 │ 3 │ 20 │ 15 │
└────────────────────────────────┘
  p    j
10 ≥ 7 → move j right

┌────────────────────────────────┐
│ 7 │ 10 │ 4 │ 3 │ 20 │ 15 │
└────────────────────────────────┘
  p         j
4 < 7 → swap with element after pivot region

┌────────────────────────────────┐
│ 7 │ 4 │ 10 │ 3 │ 20 │ 15 │
└────────────────────────────────┘
  p      j

Continue scanning...
3 < 7 → swap with next element in pivot region

┌────────────────────────────────┐
│ 7 │ 4 │ 3 │ 10 │ 20 │ 15 │
└────────────────────────────────┘

After partitioning:
┌────────────────────────────────┐
│ 3 │ 4 │ 7 │ 10 │ 20 │ 15 │
└────────────────────────────────┘
  ←─────→   ↑   ←──────────→
  < pivot  pivot   ≥ pivot
 (2 elements)    (3 elements)

Pivot final position: index 2
Elements smaller than pivot: 2
Pivot rank: 3rd position (index 2 + 1)

STEP 3: COMPARE WITH TARGET
===========================
Target: k = 3 (looking for 3rd smallest)
Pivot rank: 3

Since pivot rank == k:
┌────────────────────────────────┐
│ 3 │ 4 │ 7 │ 10 │ 20 │ 15 │
└────────────────────────────────┘
          ↑
      ANSWER!

The 3rd smallest element is 7.

ALTERNATIVE SCENARIOS:
=====================

Scenario A: If k < pivot_rank
-----------------------------
If we wanted k=2 (2nd smallest):
┌────────────────────────────────┐
│ 3 │ 4 │ 7 │ 10 │ 20 │ 15 │
└────────────────────────────────┘
      ↑   ↑
     k=2  pivot_rank=3

Recursively search LEFT partition: [3, 4]

Scenario B: If k > pivot_rank  
-----------------------------
If we wanted k=5 (5th smallest):
┌────────────────────────────────┐
│ 3 │ 4 │ 7 │ 10 │ 20 │ 15 │
└────────────────────────────────┘
              ↑         ↑
         pivot_rank=3   k=5

Recursively search RIGHT partition: [10, 20, 15]
Adjust k to k-3 = 2 (2nd smallest in right partition)

COMPLETE ALGORITHM FLOW:
========================

function quickselect(arr, left, right, k):
    ┌─────────────────────────┐
    │ Is left == right?       │
    │ (Single element)        │
    └─────────┬───────────────┘
              │ Yes
              ▼
         ┌─────────┐
         │ Return  │
         │ arr[left]│
         └─────────┘
              │ No
              ▼
    ┌─────────────────────────┐
    │ Partition array around  │
    │ chosen pivot            │
    └─────────┬───────────────┘
              ▼
    ┌─────────────────────────┐
    │ Get pivot final position│
    │ pivot_index             │
    └─────────┬───────────────┘
              ▼
         ┌─────────────┐
      ┌──│ k == pivot? │──┐
      │  └─────────────┘  │
      │ Yes            No │
      ▼                   ▼
 ┌─────────┐    ┌──────────────────┐
 │ Return  │    │ k < pivot_index? │
 │ arr[k]  │    └─────────┬────────┘
 └─────────┘              │
                      ┌───┴───┐
                   Yes│       │No
                      ▼       ▼
              ┌───────────┐ ┌─────────────────┐
              │ Recurse   │ │ Recurse right:  │
              │ left part │ │ k = k-pivot-1   │
              └───────────┘ └─────────────────┘

TIME COMPLEXITY ANALYSIS:
=========================
Best/Average Case: O(n)
- Each partition reduces problem size by ~half
- T(n) = T(n/2) + O(n) = O(n)

Worst Case: O(n²)
- Poor pivot choices lead to unbalanced partitions
- T(n) = T(n-1) + O(n) = O(n²)

SPACE COMPLEXITY: O(log n) average, O(n) worst case (recursion stack)

PRACTICAL EXAMPLE - COMPLETE TRACE:
==================================
Array: [7, 10, 4, 3, 20, 15], k=3

Call 1: quickselect(arr, 0, 5, 3)
├─ Partition around 7
├─ Result: [3, 4, 7, 10, 20, 15]
├─ Pivot at index 2, rank = 3
└─ k == rank → Return arr[2] = 7

Final Answer: 7 is the 3rd smallest element.

VARIATIONS:
===========
1. Randomized QuickSelect: Choose random pivot to avoid worst case
2. Median-of-Medians: Guaranteed O(n) worst case
3. Introselect: Hybrid approach switching to heapsort if recursion too deep

Applications:
- Finding median (k = n/2)
- Finding percentiles
- Top-k problems
- Selection in streaming data