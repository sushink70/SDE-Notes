I'll create a comprehensive ASCII diagram showing how different selection algorithms work step by step, including linear search, binary search, and selection sort.I've created a comprehensive ASCII diagram showing how different selection algorithms work step by step. The diagram covers four important algorithms:

1. **Linear Search** - Shows how to sequentially scan through an array to find a target element
2. **Binary Search** - Demonstrates the divide-and-conquer approach on sorted arrays
3. **Selection Sort** - Illustrates how to repeatedly find minimum elements and build a sorted array
4. **QuickSelect** - Shows how to find the Kth smallest element using partitioning

Each algorithm includes:
- Visual step-by-step progression with ASCII arrays
- Pointer positions and comparisons
- Time and space complexity analysis
- Clear annotations explaining each decision point

The diagram uses symbols like arrows (→, ↑) to show movement and current positions, checkmarks (✓) for processed elements, and brackets ([]) to highlight pivot elements. This makes it easy to follow the logic flow of each algorithm and understand how they differ in their approaches to selection problems.

SELECTION ALGORITHMS - STEP BY STEP ASCII DIAGRAMS
========================================================

1. LINEAR SEARCH (Sequential Search)
====================================
Goal: Find element "7" in array [3, 8, 7, 2, 9, 1]

Step 1: Start at index 0
┌───┬───┬───┬───┬───┬───┐
│ 3 │ 8 │ 7 │ 2 │ 9 │ 1 │
└───┴───┴───┴───┴───┴───┘
  ↑
  i=0  Check: 3 ≠ 7? Continue

Step 2: Move to index 1
┌───┬───┬───┬───┬───┬───┐
│ 3 │ 8 │ 7 │ 2 │ 9 │ 1 │
└───┴───┴───┴───┴───┴───┘
      ↑
      i=1  Check: 8 ≠ 7? Continue

Step 3: Move to index 2
┌───┬───┬───┬───┬───┬───┐
│ 3 │ 8 │ 7 │ 2 │ 9 │ 1 │
└───┴───┴───┴───┴───┴───┘
          ↑
          i=2  Check: 7 = 7? FOUND! Return index 2

Time Complexity: O(n)
Space Complexity: O(1)


2. BINARY SEARCH (Requires sorted array)
=========================================
Goal: Find element "7" in sorted array [1, 2, 3, 7, 8, 9]

Initial state:
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5    (indices)
  ↑               ↑       ↑
left=0           mid=2   right=5

Step 1: Check middle element
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
          ↑
        mid=2, value=3
        3 < 7? Search right half

Step 2: Update left boundary
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
              ↑       ↑
            left=3   right=5
            mid=4, value=8

Step 3: Check new middle
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
                  ↑
                mid=4, value=8
                8 > 7? Search left half

Step 4: Update right boundary
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
              ↑   ↑
            left=3 right=3
            mid=3, value=7

Step 5: Found target!
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 7 │ 8 │ 9 │
└───┴───┴───┴───┴───┴───┘
              ↑
            FOUND at index 3

Time Complexity: O(log n)
Space Complexity: O(1)


3. SELECTION SORT (Finding and placing elements)
===============================================
Goal: Sort array [64, 25, 12, 22, 11]

Initial Array:
┌────┬────┬────┬────┬────┐
│ 64 │ 25 │ 12 │ 22 │ 11 │
└────┴────┴────┴────┴────┘
  0    1    2    3    4

Pass 1: Find minimum in range [0-4]
┌────┬────┬────┬────┬────┐
│ 64 │ 25 │ 12 │ 22 │ 11 │ ← Scan all elements
└────┴────┴────┴────┴────┘
 min   ↓    ↓         ↓
      25 < 64  12 < 25  11 < 12
                          ↑
                    minimum = 11

Swap 64 and 11:
┌────┬────┬────┬────┬────┐
│ 11 │ 25 │ 12 │ 22 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ←── unsorted ──→

Pass 2: Find minimum in range [1-4]
┌────┬────┬────┬────┬────┐
│ 11 │ 25 │ 12 │ 22 │ 64 │
└────┴────┴────┴────┴────┘
  ✓   min   ↓    ↓    ↓
           12 < 25  22 > 12
                    ↑
              minimum = 12

Swap 25 and 12:
┌────┬────┬────┬────┬────┐
│ 11 │ 12 │ 25 │ 22 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ✓   ←─ unsorted ─→

Pass 3: Find minimum in range [2-4]
┌────┬────┬────┬────┬────┐
│ 11 │ 12 │ 25 │ 22 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ✓   min   ↓    ↓
                22 < 25
                  ↑
            minimum = 22

Swap 25 and 22:
┌────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ✓    ✓   ←─unsorted─→

Pass 4: Find minimum in range [3-4]
┌────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ✓    ✓   min   ↓
                     64 > 25
                minimum = 25 (no swap needed)

Final Sorted Array:
┌────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 64 │
└────┴────┴────┴────┴────┘
  ✓    ✓    ✓    ✓    ✓

Time Complexity: O(n²)
Space Complexity: O(1)


4. QUICKSELECT (Finding Kth smallest element)
============================================
Goal: Find 3rd smallest element in [3, 6, 8, 10, 1, 2, 1]

Initial Array (k=3, find 3rd smallest):
┌───┬───┬───┬───┬───┬───┬───┐
│ 3 │ 6 │ 8 │10 │ 1 │ 2 │ 1 │
└───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6

Step 1: Choose pivot (let's use first element = 3)
┌───┬───┬───┬───┬───┬───┬───┐
│[3]│ 6 │ 8 │10 │ 1 │ 2 │ 1 │
└───┴───┴───┴───┴───┴───┴───┘
 pivot

Step 2: Partition around pivot (3)
Elements < 3: [1, 2, 1]  |  Pivot: [3]  |  Elements > 3: [6, 8, 10]

After partitioning:
┌───┬───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 1 │ 3 │ 6 │ 8 │10 │
└───┴───┴───┴───┴───┴───┴───┘
  0   1   2   3   4   5   6
← less →   ↑  ← greater →
           pivot at index 3

Step 3: Check position of pivot
Pivot is at index 3, we want 3rd smallest (index 2)
Since 3 > 2, search in left partition

Step 4: Recursively search left partition [1, 2, 1]
┌───┬───┬───┐
│ 1 │ 2 │ 1 │
└───┴───┴───┘
  0   1   2

Choose pivot = 1, partition:
┌───┬───┬───┐
│ 1 │ 1 │ 2 │  After partitioning
└───┴───┴───┘
  0   1   2
      ↑
   pivot at index 1

Since we want index 2 in original problem (3rd smallest),
and we're looking at indices 0-2, we want index 2 here.
The element at index 2 is 2.

Result: 3rd smallest element is 2

Average Time Complexity: O(n)
Worst Case Time Complexity: O(n²)
Space Complexity: O(log n) average


ALGORITHM COMPARISON SUMMARY
============================

┌─────────────────┬──────────────┬────────────┬─────────────┐
│   Algorithm     │ Time Complex │Space Complex│  Use Case   │
├─────────────────┼──────────────┼────────────┼─────────────┤
│ Linear Search   │    O(n)      │    O(1)    │ Unsorted    │
│ Binary Search   │  O(log n)    │    O(1)    │ Sorted only │
│ Selection Sort  │    O(n²)     │    O(1)    │ Small arrays│
│ Quick Select    │O(n) avg/O(n²)│  O(log n)  │ Kth element │
└─────────────────┴──────────────┴────────────┴─────────────┘

Legend:
→ : Direction of scanning/movement
↑ : Current position/pointer
✓ : Sorted/processed element
[ ]: Pivot element
min: Current minimum candidate

I'll create a comprehensive guide to selection algorithms with complete implementations in both Python and Rust. This will cover the theory, various approaches, and practical implementations.I've created a comprehensive guide to selection algorithms with complete implementations in both Python and Rust. The guide covers:

## Key Features:

1. **Four Different Algorithms:**
   - **QuickSelect**: O(n) average case, most commonly used
   - **Median of Medians**: O(n) guaranteed worst-case performance  
   - **Heap-based Selection**: Efficient for small k values
   - **Sorting-based**: Simple reference implementation

2. **Complete Implementations:**
   - **Python**: Full object-oriented implementation with type hints
   - **Rust**: Memory-safe implementation with proper error handling
   - Both include comprehensive test suites

3. **Advanced Features:**
   - Random pivot selection to avoid worst-case scenarios
   - Optimized heap-based selection for small k
   - Comprehensive error handling and edge case management
   - Performance benchmarking framework

4. **Practical Utilities:**
   - Median finding functions
   - k-th largest element functions  
   - Ready-to-use convenience methods

## Algorithm Performance Summary:

| Algorithm | Time Complexity | Space | Best For |
|-----------|----------------|--------|----------|
| QuickSelect | O(n) avg, O(n²) worst | O(log n) | General use |
| Median of Medians | O(n) guaranteed | O(log n) | Guaranteed performance |
| Heap Select (Optimized) | O(n log k) | O(k) | Small k values |
| Sort Select | O(n log n) | O(n) | Multiple statistics |

The implementations are production-ready with proper error handling, comprehensive testing, and performance analysis. You can use these directly in your projects or as a reference for understanding how selection algorithms work under the hood.

Would you like me to explain any specific part in more detail or add additional algorithms like randomized selection or parallel implementations

# Comprehensive Guide to Selection Algorithm Implementation

## Table of Contents
1. [Introduction](#introduction)
2. [Problem Definition](#problem-definition)
3. [Algorithm Overview](#algorithm-overview)
4. [QuickSelect Algorithm](#quickselect-algorithm)
5. [Median of Medians](#median-of-medians)
6. [Heap-Based Selection](#heap-based-selection)
7. [Sorting-Based Selection](#sorting-based-selection)
8. [Performance Analysis](#performance-analysis)
9. [Use Cases and Applications](#use-cases-and-applications)
10. [Testing Framework](#testing-framework)

## Introduction

Selection algorithms are fundamental algorithms in computer science that solve the problem of finding the k-th smallest (or largest) element in an unsorted collection. Unlike sorting algorithms that organize all elements, selection algorithms focus on finding a specific order statistic efficiently.

The most common variant is finding the median (the middle element), but selection algorithms can find any k-th order statistic. These algorithms are crucial in statistics, data analysis, and various optimization problems.

## Problem Definition

**Input:** 
- An array/collection of n comparable elements
- An integer k where 1 ≤ k ≤ n

**Output:** 
- The k-th smallest element in the collection

**Examples:**
- k=1: minimum element
- k=n: maximum element  
- k=(n+1)/2: median element (for odd n)

## Algorithm Overview

We'll implement four main approaches:

1. **QuickSelect**: Average O(n), worst-case O(n²)
2. **Median of Medians**: Guaranteed O(n)
3. **Heap-Based**: O(n log k) for min-heap approach
4. **Sorting-Based**: O(n log n) - simple but inefficient

## QuickSelect Algorithm

QuickSelect is based on the partitioning scheme of QuickSort but only recurses into one partition.

### Python Implementation

```python
import random
from typing import List, TypeVar, Optional

T = TypeVar('T')

class SelectionAlgorithms:
    """A collection of selection algorithms for finding k-th order statistics."""
    
    @staticmethod
    def quickselect(arr: List[T], k: int) -> T:
        """
        Find the k-th smallest element using QuickSelect algorithm.
        
        Args:
            arr: List of comparable elements
            k: Position (1-indexed) of desired element
            
        Returns:
            The k-th smallest element
            
        Time Complexity: O(n) average, O(n²) worst case
        Space Complexity: O(log n) average due to recursion
        """
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input: empty array or k out of bounds")
        
        def partition(arr: List[T], low: int, high: int, pivot_idx: int) -> int:
            """Partition array around pivot element."""
            # Move pivot to end
            arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
            pivot = arr[high]
            
            i = low
            for j in range(low, high):
                if arr[j] <= pivot:
                    arr[i], arr[j] = arr[j], arr[i]
                    i += 1
            
            arr[i], arr[high] = arr[high], arr[i]
            return i
        
        def quickselect_helper(arr: List[T], low: int, high: int, k: int) -> T:
            """Recursive helper for quickselect."""
            if low == high:
                return arr[low]
            
            # Choose random pivot to avoid worst-case on sorted arrays
            pivot_idx = random.randint(low, high)
            pivot_final_pos = partition(arr, low, high, pivot_idx)
            
            if k == pivot_final_pos:
                return arr[k]
            elif k < pivot_final_pos:
                return quickselect_helper(arr, low, pivot_final_pos - 1, k)
            else:
                return quickselect_helper(arr, pivot_final_pos + 1, high, k)
        
        # Make a copy to avoid modifying original array
        arr_copy = arr.copy()
        return quickselect_helper(arr_copy, 0, len(arr_copy) - 1, k - 1)
    
    @staticmethod
    def median_of_medians_select(arr: List[T], k: int) -> T:
        """
        Find k-th smallest element using Median of Medians algorithm.
        Guarantees O(n) worst-case time complexity.
        
        Args:
            arr: List of comparable elements
            k: Position (1-indexed) of desired element
            
        Returns:
            The k-th smallest element
            
        Time Complexity: O(n) guaranteed
        Space Complexity: O(log n)
        """
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input: empty array or k out of bounds")
        
        def median_of_medians(arr: List[T], low: int, high: int) -> T:
            """Find median of medians as pivot."""
            n = high - low + 1
            if n <= 5:
                # For small arrays, just sort and return median
                subarr = sorted(arr[low:high + 1])
                return subarr[n // 2]
            
            # Divide into groups of 5 and find medians
            medians = []
            for i in range(low, high + 1, 5):
                group_high = min(i + 4, high)
                group = sorted(arr[i:group_high + 1])
                medians.append(group[len(group) // 2])
            
            # Recursively find median of medians
            return median_of_medians_select(medians, (len(medians) + 1) // 2)
        
        def partition_around_pivot(arr: List[T], low: int, high: int, pivot: T) -> int:
            """Partition array around given pivot value."""
            # Find pivot index
            pivot_idx = -1
            for i in range(low, high + 1):
                if arr[i] == pivot:
                    pivot_idx = i
                    break
            
            # Move pivot to end
            arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
            
            i = low
            for j in range(low, high):
                if arr[j] <= pivot:
                    arr[i], arr[j] = arr[j], arr[i]
                    i += 1
            
            arr[i], arr[high] = arr[high], arr[i]
            return i
        
        def mom_select_helper(arr: List[T], low: int, high: int, k: int) -> T:
            """Recursive helper for median of medians selection."""
            if low == high:
                return arr[low]
            
            # Find median of medians as pivot
            pivot = median_of_medians(arr, low, high)
            pivot_pos = partition_around_pivot(arr, low, high, pivot)
            
            if k == pivot_pos:
                return arr[k]
            elif k < pivot_pos:
                return mom_select_helper(arr, low, pivot_pos - 1, k)
            else:
                return mom_select_helper(arr, pivot_pos + 1, high, k)
        
        arr_copy = arr.copy()
        return mom_select_helper(arr_copy, 0, len(arr_copy) - 1, k - 1)
    
    @staticmethod
    def heap_select(arr: List[T], k: int) -> T:
        """
        Find k-th smallest element using min-heap.
        
        Args:
            arr: List of comparable elements
            k: Position (1-indexed) of desired element
            
        Returns:
            The k-th smallest element
            
        Time Complexity: O(n + k log n)
        Space Complexity: O(n)
        """
        import heapq
        
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input: empty array or k out of bounds")
        
        # Build min-heap from array
        heap = arr.copy()
        heapq.heapify(heap)
        
        # Extract k smallest elements
        result = None
        for _ in range(k):
            result = heapq.heappop(heap)
        
        return result
    
    @staticmethod
    def heap_select_optimized(arr: List[T], k: int) -> T:
        """
        Optimized heap-based selection using max-heap of size k.
        More efficient for small k values.
        
        Args:
            arr: List of comparable elements
            k: Position (1-indexed) of desired element
            
        Returns:
            The k-th smallest element
            
        Time Complexity: O(n log k)
        Space Complexity: O(k)
        """
        import heapq
        
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input: empty array or k out of bounds")
        
        # Use max-heap (negate values) to keep k smallest elements
        max_heap = []
        
        for num in arr:
            if len(max_heap) < k:
                heapq.heappush(max_heap, -num)
            elif -max_heap[0] > num:
                heapq.heapreplace(max_heap, -num)
        
        return -max_heap[0]
    
    @staticmethod
    def sort_select(arr: List[T], k: int) -> T:
        """
        Find k-th smallest element by sorting (simple but inefficient).
        
        Args:
            arr: List of comparable elements
            k: Position (1-indexed) of desired element
            
        Returns:
            The k-th smallest element
            
        Time Complexity: O(n log n)
        Space Complexity: O(n)
        """
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input: empty array or k out of bounds")
        
        sorted_arr = sorted(arr)
        return sorted_arr[k - 1]

# Convenience functions for common use cases
def find_median(arr: List[T]) -> T:
    """Find median using QuickSelect."""
    n = len(arr)
    if n % 2 == 1:
        return SelectionAlgorithms.quickselect(arr, (n + 1) // 2)
    else:
        # For even length, return lower median
        return SelectionAlgorithms.quickselect(arr, n // 2)

def find_kth_largest(arr: List[T], k: int) -> T:
    """Find k-th largest element."""
    return SelectionAlgorithms.quickselect(arr, len(arr) - k + 1)
```

### Rust Implementation

```rust
use std::cmp::Ordering;
use rand::Rng;

/// A collection of selection algorithms for finding k-th order statistics
pub struct SelectionAlgorithms;

impl SelectionAlgorithms {
    /// Find the k-th smallest element using QuickSelect algorithm
    /// 
    /// # Arguments
    /// * `arr` - A mutable slice of comparable elements
    /// * `k` - Position (1-indexed) of desired element
    /// 
    /// # Returns
    /// The k-th smallest element
    /// 
    /// # Time Complexity
    /// O(n) average, O(n²) worst case
    /// 
    /// # Space Complexity
    /// O(log n) average due to recursion
    pub fn quickselect<T: Clone + Ord>(arr: &[T], k: usize) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input: empty array or k out of bounds".to_string());
        }
        
        let mut arr_copy = arr.to_vec();
        Ok(Self::quickselect_helper(&mut arr_copy, 0, arr_copy.len() - 1, k - 1))
    }
    
    fn quickselect_helper<T: Clone + Ord>(
        arr: &mut [T], 
        low: usize, 
        high: usize, 
        k: usize
    ) -> T {
        if low == high {
            return arr[low].clone();
        }
        
        let mut rng = rand::thread_rng();
        let pivot_idx = rng.gen_range(low..=high);
        let pivot_pos = Self::partition(arr, low, high, pivot_idx);
        
        match k.cmp(&pivot_pos) {
            Ordering::Equal => arr[k].clone(),
            Ordering::Less => Self::quickselect_helper(arr, low, pivot_pos - 1, k),
            Ordering::Greater => Self::quickselect_helper(arr, pivot_pos + 1, high, k),
        }
    }
    
    fn partition<T: Clone + Ord>(
        arr: &mut [T], 
        low: usize, 
        high: usize, 
        pivot_idx: usize
    ) -> usize {
        arr.swap(pivot_idx, high);
        let pivot = arr[high].clone();
        
        let mut i = low;
        for j in low..high {
            if arr[j] <= pivot {
                arr.swap(i, j);
                i += 1;
            }
        }
        
        arr.swap(i, high);
        i
    }
    
    /// Find k-th smallest element using Median of Medians algorithm
    /// Guarantees O(n) worst-case time complexity
    pub fn median_of_medians_select<T: Clone + Ord>(
        arr: &[T], 
        k: usize
    ) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input: empty array or k out of bounds".to_string());
        }
        
        let mut arr_copy = arr.to_vec();
        Ok(Self::mom_select_helper(&mut arr_copy, 0, arr_copy.len() - 1, k - 1))
    }
    
    fn mom_select_helper<T: Clone + Ord>(
        arr: &mut [T], 
        low: usize, 
        high: usize, 
        k: usize
    ) -> T {
        if low == high {
            return arr[low].clone();
        }
        
        let pivot = Self::median_of_medians(arr, low, high);
        let pivot_pos = Self::partition_around_pivot(arr, low, high, &pivot);
        
        match k.cmp(&pivot_pos) {
            Ordering::Equal => arr[k].clone(),
            Ordering::Less => Self::mom_select_helper(arr, low, pivot_pos - 1, k),
            Ordering::Greater => Self::mom_select_helper(arr, pivot_pos + 1, high, k),
        }
    }
    
    fn median_of_medians<T: Clone + Ord>(arr: &[T], low: usize, high: usize) -> T {
        let n = high - low + 1;
        if n <= 5 {
            let mut subarr: Vec<T> = arr[low..=high].to_vec();
            subarr.sort();
            return subarr[n / 2].clone();
        }
        
        let mut medians = Vec::new();
        let mut i = low;
        while i <= high {
            let group_high = std::cmp::min(i + 4, high);
            let mut group: Vec<T> = arr[i..=group_high].to_vec();
            group.sort();
            medians.push(group[group.len() / 2].clone());
            i += 5;
        }
        
        Self::median_of_medians_select(&medians, (medians.len() + 1) / 2)
            .unwrap()
    }
    
    fn partition_around_pivot<T: Clone + Ord>(
        arr: &mut [T], 
        low: usize, 
        high: usize, 
        pivot: &T
    ) -> usize {
        // Find pivot index
        let mut pivot_idx = None;
        for i in low..=high {
            if &arr[i] == pivot {
                pivot_idx = Some(i);
                break;
            }
        }
        let pivot_idx = pivot_idx.unwrap();
        
        arr.swap(pivot_idx, high);
        
        let mut i = low;
        for j in low..high {
            if arr[j] <= *pivot {
                arr.swap(i, j);
                i += 1;
            }
        }
        
        arr.swap(i, high);
        i
    }
    
    /// Find k-th smallest element using heap-based approach
    pub fn heap_select<T: Clone + Ord>(arr: &[T], k: usize) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input: empty array or k out of bounds".to_string());
        }
        
        use std::collections::BinaryHeap;
        use std::cmp::Reverse;
        
        // Use min-heap (reverse max-heap)
        let mut heap: BinaryHeap<Reverse<T>> = arr
            .iter()
            .map(|x| Reverse(x.clone()))
            .collect();
        
        let mut result = None;
        for _ in 0..k {
            if let Some(Reverse(val)) = heap.pop() {
                result = Some(val);
            }
        }
        
        result.ok_or_else(|| "Heap error".to_string())
    }
    
    /// Optimized heap-based selection using max-heap of size k
    pub fn heap_select_optimized<T: Clone + Ord>(
        arr: &[T], 
        k: usize
    ) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input: empty array or k out of bounds".to_string());
        }
        
        use std::collections::BinaryHeap;
        
        let mut max_heap = BinaryHeap::new();
        
        for item in arr {
            if max_heap.len() < k {
                max_heap.push(item.clone());
            } else if let Some(top) = max_heap.peek() {
                if item < top {
                    max_heap.pop();
                    max_heap.push(item.clone());
                }
            }
        }
        
        max_heap.pop().ok_or_else(|| "Heap error".to_string())
    }
    
    /// Find k-th smallest element by sorting (simple but inefficient)
    pub fn sort_select<T: Clone + Ord>(arr: &[T], k: usize) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input: empty array or k out of bounds".to_string());
        }
        
        let mut sorted_arr = arr.to_vec();
        sorted_arr.sort();
        Ok(sorted_arr[k - 1].clone())
    }
}

/// Convenience function to find median using QuickSelect
pub fn find_median<T: Clone + Ord>(arr: &[T]) -> Result<T, String> {
    let n = arr.len();
    if n == 0 {
        return Err("Cannot find median of empty array".to_string());
    }
    
    let k = if n % 2 == 1 {
        (n + 1) / 2
    } else {
        n / 2  // Return lower median for even length
    };
    
    SelectionAlgorithms::quickselect(arr, k)
}

/// Convenience function to find k-th largest element
pub fn find_kth_largest<T: Clone + Ord>(arr: &[T], k: usize) -> Result<T, String> {
    if arr.is_empty() || k == 0 || k > arr.len() {
        return Err("Invalid input".to_string());
    }
    
    SelectionAlgorithms::quickselect(arr, arr.len() - k + 1)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_quickselect() {
        let arr = vec![3, 6, 8, 10, 1, 2, 1];
        assert_eq!(SelectionAlgorithms::quickselect(&arr, 1).unwrap(), 1);
        assert_eq!(SelectionAlgorithms::quickselect(&arr, 3).unwrap(), 2);
        assert_eq!(SelectionAlgorithms::quickselect(&arr, 7).unwrap(), 10);
    }
    
    #[test]
    fn test_median_of_medians() {
        let arr = vec![3, 6, 8, 10, 1, 2, 1];
        assert_eq!(SelectionAlgorithms::median_of_medians_select(&arr, 1).unwrap(), 1);
        assert_eq!(SelectionAlgorithms::median_of_medians_select(&arr, 4).unwrap(), 3);
    }
    
    #[test]
    fn test_heap_select() {
        let arr = vec![3, 6, 8, 10, 1, 2, 1];
        assert_eq!(SelectionAlgorithms::heap_select(&arr, 1).unwrap(), 1);
        assert_eq!(SelectionAlgorithms::heap_select(&arr, 4).unwrap(), 3);
    }
    
    #[test]
    fn test_find_median() {
        let arr1 = vec![3, 1, 4, 1, 5];
        assert_eq!(find_median(&arr1).unwrap(), 3);
        
        let arr2 = vec![3, 1, 4, 1];
        assert_eq!(find_median(&arr2).unwrap(), 1);
    }
}
```

## Performance Analysis

### Time Complexity Comparison

| Algorithm | Best Case | Average Case | Worst Case | Space |
|-----------|-----------|--------------|------------|-------|
| QuickSelect | O(n) | O(n) | O(n²) | O(log n) |
| Median of Medians | O(n) | O(n) | O(n) | O(log n) |
| Heap Select | O(n log k) | O(n log k) | O(n log k) | O(n) |
| Heap Select Optimized | O(n log k) | O(n log k) | O(n log k) | O(k) |
| Sort Select | O(n log n) | O(n log n) | O(n log n) | O(n) |

### When to Use Each Algorithm

- **QuickSelect**: General purpose, good average performance
- **Median of Medians**: When worst-case guarantees are needed
- **Heap Select (Optimized)**: When k is small relative to n
- **Sort Select**: When you need multiple order statistics or the array is already partially sorted

## Use Cases and Applications

### 1. Statistics and Data Analysis
- Finding percentiles and quantiles
- Robust statistics (median is less sensitive to outliers)
- Data summarization

### 2. Computer Graphics
- Finding median for image processing filters
- Color palette reduction

### 3. Database Systems
- Query optimization (finding top-k results)
- Index construction

### 4. Machine Learning
- Feature selection based on importance scores
- Outlier detection

## Testing Framework

### Python Test Suite

```python
import unittest
import random
import time
from typing import List, Callable

class TestSelectionAlgorithms(unittest.TestCase):
    """Comprehensive test suite for selection algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.algorithms = [
            ("QuickSelect", SelectionAlgorithms.quickselect),
            ("Median of Medians", SelectionAlgorithms.median_of_medians_select),
            ("Heap Select", SelectionAlgorithms.heap_select),
            ("Heap Select Optimized", SelectionAlgorithms.heap_select_optimized),
            ("Sort Select", SelectionAlgorithms.sort_select),
        ]
        
        # Test cases
        self.test_cases = [
            ([3, 6, 8, 10, 1, 2, 1], 1, 1),
            ([3, 6, 8, 10, 1, 2, 1], 3, 2),
            ([3, 6, 8, 10, 1, 2, 1], 4, 3),
            ([3, 6, 8, 10, 1, 2, 1], 7, 10),
            ([5], 1, 5),
            ([1, 2], 1, 1),
            ([1, 2], 2, 2),
            ([5, 3, 8, 1, 9, 2], 3, 3),
        ]
    
    def test_correctness(self):
        """Test all algorithms for correctness."""
        for name, algorithm in self.algorithms:
            with self.subTest(algorithm=name):
                for arr, k, expected in self.test_cases:
                    result = algorithm(arr, k)
                    self.assertEqual(result, expected, 
                        f"{name} failed on {arr}, k={k}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        for name, algorithm in self.algorithms:
            with self.subTest(algorithm=name):
                # Empty array
                with self.assertRaises(ValueError):
                    algorithm([], 1)
                
                # k out of bounds
                with self.assertRaises(ValueError):
                    algorithm([1, 2, 3], 0)
                with self.assertRaises(ValueError):
                    algorithm([1, 2, 3], 4)
    
    def test_median_functions(self):
        """Test median finding functions."""
        test_cases = [
            ([1, 3, 5], 3),
            ([1, 2, 3, 4], 2),
            ([5, 1, 3, 9, 2], 3),
        ]
        
        for arr, expected in test_cases:
            result = find_median(arr)
            self.assertEqual(result, expected)
    
    def test_kth_largest(self):
        """Test k-th largest element finding."""
        arr = [3, 6, 8, 10, 1, 2, 1]
        # Sorted: [1, 1, 2, 3, 6, 8, 10]
        # 1st largest = 10, 2nd largest = 8, etc.
        self.assertEqual(find_kth_largest(arr, 1), 10)
        self.assertEqual(find_kth_largest(arr, 2), 8)
        self.assertEqual(find_kth_largest(arr, 3), 6)
    
    def performance_test(self):
        """Performance comparison of algorithms."""
        sizes = [100, 1000, 10000]
        k_values = [1, 0.25, 0.5, 0.75, 1.0]  # Fractions of n
        
        print("\nPerformance Test Results:")
        print("=" * 60)
        
        for size in sizes:
            print(f"\nArray size: {size}")
            arr = [random.randint(1, 1000) for _ in range(size)]
            
            for k_frac in k_values:
                k = max(1, int(size * k_frac))
                print(f"  k = {k} ({k_frac:.1%} of n):")
                
                for name, algorithm in self.algorithms:
                    start_time = time.time()
                    try:
                        result = algorithm(arr, k)
                        end_time = time.time()
                        elapsed = (end_time - start_time) * 1000  # Convert to ms
                        print(f"    {name:20}: {elapsed:6.2f}ms")
                    except Exception as e:
                        print(f"    {name:20}: ERROR - {e}")

def run_comprehensive_tests():
    """Run all tests including performance benchmarks."""
    # Run unit tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSelectionAlgorithms)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    
    # Run performance tests
    test_instance = TestSelectionAlgorithms()
    test_instance.setUp()
    test_instance.performance_test()

if __name__ == "__main__":
    run_comprehensive_tests()
```

## Advanced Optimizations and Extensions

### Iterative QuickSelect (Stack-Based)

To avoid recursion stack overflow for very large arrays, here's an iterative version:

```python
@staticmethod
def quickselect_iterative(arr: List[T], k: int) -> T:
    """
    Iterative version of QuickSelect to avoid stack overflow.
    """
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid input: empty array or k out of bounds")
    
    arr_copy = arr.copy()
    low, high = 0, len(arr_copy) - 1
    k = k - 1  # Convert to 0-indexed
    
    while low < high:
        # Choose random pivot
        pivot_idx = random.randint(low, high)
        
        # Partition
        arr_copy[pivot_idx], arr_copy[high] = arr_copy[high], arr_copy[pivot_idx]
        pivot = arr_copy[high]
        
        i = low
        for j in range(low, high):
            if arr_copy[j] <= pivot:
                arr_copy[i], arr_copy[j] = arr_copy[j], arr_copy[i]
                i += 1
        
        arr_copy[i], arr_copy[high] = arr_copy[high], arr_copy[i]
        pivot_pos = i
        
        # Update search range
        if k == pivot_pos:
            return arr_copy[k]
        elif k < pivot_pos:
            high = pivot_pos - 1
        else:
            low = pivot_pos + 1
    
    return arr_copy[low]
```

### Threaded/Parallel QuickSelect

For very large datasets, parallel processing can significantly improve performance:

```python
import concurrent.futures
from typing import List, TypeVar
import threading

class ParallelSelectionAlgorithms:
    """Parallel implementations of selection algorithms."""
    
    @staticmethod
    def parallel_quickselect(arr: List[T], k: int, max_workers: int = 4) -> T:
        """
        Parallel QuickSelect using divide-and-conquer with threading.
        
        Time Complexity: O(n/p) average where p is number of processors
        """
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input")
        
        if len(arr) < 1000:  # Use sequential for small arrays
            return SelectionAlgorithms.quickselect(arr, k)
        
        def parallel_partition(arr_segment, pivot):
            """Partition a segment of the array."""
            smaller = [x for x in arr_segment if x < pivot]
            equal = [x for x in arr_segment if x == pivot]
            larger = [x for x in arr_segment if x > pivot]
            return smaller, equal, larger
        
        # Choose pivot (use median of medians for better pivot selection)
        sample_size = min(len(arr), 1000)
        sample = random.sample(arr, sample_size)
        pivot = SelectionAlgorithms.quickselect(sample, len(sample) // 2)
        
        # Partition array in parallel
        chunk_size = len(arr) // max_workers
        chunks = [arr[i:i + chunk_size] for i in range(0, len(arr), chunk_size)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(parallel_partition, chunk, pivot) for chunk in chunks]
            results = [future.result() for future in futures]
        
        # Combine results
        all_smaller = []
        all_equal = []
        all_larger = []
        
        for smaller, equal, larger in results:
            all_smaller.extend(smaller)
            all_equal.extend(equal)
            all_larger.extend(larger)
        
        # Determine which partition contains k-th element
        if k <= len(all_smaller):
            return ParallelSelectionAlgorithms.parallel_quickselect(all_smaller, k, max_workers)
        elif k <= len(all_smaller) + len(all_equal):
            return pivot
        else:
            return ParallelSelectionAlgorithms.parallel_quickselect(
                all_larger, k - len(all_smaller) - len(all_equal), max_workers
            )
```

### Custom Comparison Functions

Support for custom comparison and key extraction:

```python
from typing import Callable, Any

class FlexibleSelectionAlgorithms:
    """Selection algorithms with custom comparison functions."""
    
    @staticmethod
    def quickselect_with_key(
        arr: List[Any], 
        k: int, 
        key: Callable[[Any], Any] = None,
        reverse: bool = False
    ) -> Any:
        """
        QuickSelect with custom key function and reverse ordering.
        
        Args:
            arr: List of elements
            k: Position (1-indexed)
            key: Function to extract comparison key from elements
            reverse: If True, find k-th largest instead of k-th smallest
        """
        if not arr or k < 1 or k > len(arr):
            raise ValueError("Invalid input")
        
        if key is None:
            key = lambda x: x
        
        def compare(a, b):
            key_a, key_b = key(a), key(b)
            if reverse:
                return key_a > key_b
            return key_a < key_b
        
        def partition_with_key(arr, low, high, pivot_idx):
            arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
            pivot = arr[high]
            
            i = low
            for j in range(low, high):
                if compare(arr[j], pivot) or key(arr[j]) == key(pivot):
                    arr[i], arr[j] = arr[j], arr[i]
                    i += 1
            
            arr[i], arr[high] = arr[high], arr[i]
            return i
        
        def helper(arr, low, high, k):
            if low == high:
                return arr[low]
            
            pivot_idx = random.randint(low, high)
            pivot_pos = partition_with_key(arr, low, high, pivot_idx)
            
            if k == pivot_pos:
                return arr[k]
            elif k < pivot_pos:
                return helper(arr, low, pivot_pos - 1, k)
            else:
                return helper(arr, pivot_pos + 1, high, k)
        
        arr_copy = arr.copy()
        return helper(arr_copy, 0, len(arr_copy) - 1, k - 1)

# Example usage:
# Find person with k-th highest salary
# people = [{"name": "Alice", "salary": 50000}, {"name": "Bob", "salary": 60000}]
# kth_highest_paid = quickselect_with_key(people, 1, key=lambda p: p["salary"], reverse=True)
```

### Multiple Selection (Finding Multiple Order Statistics)

When you need multiple order statistics, specialized algorithms can be more efficient:

```python
class MultipleSelectionAlgorithms:
    """Algorithms for finding multiple order statistics efficiently."""
    
    @staticmethod
    def multiple_quickselect(arr: List[T], ks: List[int]) -> List[T]:
        """
        Find multiple order statistics using a single pass approach.
        More efficient than calling quickselect multiple times.
        
        Args:
            arr: Input array
            ks: List of positions (1-indexed) to find
            
        Returns:
            List of k-th order statistics corresponding to ks
        """
        if not arr or not ks:
            raise ValueError("Invalid input")
        
        # Validate and sort ks
        for k in ks:
            if k < 1 or k > len(arr):
                raise ValueError(f"k={k} out of bounds")
        
        sorted_ks = sorted(set(ks))  # Remove duplicates and sort
        results = {}
        
        def helper(arr, low, high, remaining_ks):
            if not remaining_ks:
                return
            
            if low == high:
                # All remaining ks must equal low (0-indexed)
                for k in remaining_ks:
                    if k == low:
                        results[k + 1] = arr[low]  # Convert back to 1-indexed
                return
            
            # Partition
            pivot_idx = random.randint(low, high)
            pivot_pos = SelectionAlgorithms.partition(arr, low, high, pivot_idx)
            
            # Check if pivot position matches any k
            if pivot_pos + 1 in remaining_ks:  # Convert to 1-indexed
                results[pivot_pos + 1] = arr[pivot_pos]
            
            # Divide remaining ks
            left_ks = [k - 1 for k in remaining_ks if k - 1 < pivot_pos]
            right_ks = [k - 1 for k in remaining_ks if k - 1 > pivot_pos]
            
            # Recurse on both sides if needed
            if left_ks:
                helper(arr, low, pivot_pos - 1, left_ks)
            if right_ks:
                helper(arr, pivot_pos + 1, high, right_ks)
        
        arr_copy = arr.copy()
        helper(arr_copy, 0, len(arr_copy) - 1, [k - 1 for k in sorted_ks])
        
        # Return results in original order
        return [results[k] for k in ks]
    
    @staticmethod
    def quantiles(arr: List[T], q: int) -> List[T]:
        """
        Find q-quantiles (e.g., quartiles when q=4).
        
        Args:
            arr: Input array
            q: Number of quantiles
            
        Returns:
            List of q-1 quantile values
        """
        if not arr or q < 2:
            raise ValueError("Invalid input")
        
        n = len(arr)
        ks = []
        for i in range(1, q):
            k = int(i * n / q)
            if k == 0:
                k = 1
            ks.append(k)
        
        return MultipleSelectionAlgorithms.multiple_quickselect(arr, ks)
```

## Streaming and Online Algorithms

For data streams where you can't store all elements in memory:

```python
import heapq
from collections import deque

class StreamingSelectionAlgorithms:
    """Algorithms for finding order statistics in data streams."""
    
    def __init__(self, k: int):
        """Initialize for finding k-th smallest element in stream."""
        self.k = k
        self.max_heap = []  # For k smallest elements
        
    def add(self, value: T) -> Optional[T]:
        """
        Add new value to stream and return current k-th smallest.
        
        Returns None if fewer than k elements have been seen.
        """
        if len(self.max_heap) < self.k:
            heapq.heappush(self.max_heap, -value)  # Negate for max heap
        elif -self.max_heap[0] > value:
            heapq.heapreplace(self.max_heap, -value)
        
        if len(self.max_heap) == self.k:
            return -self.max_heap[0]
        return None
    
    def get_kth_smallest(self) -> Optional[T]:
        """Get current k-th smallest element."""
        if len(self.max_heap) == self.k:
            return -self.max_heap[0]
        return None

class ApproximateMedianFinder:
    """
    Approximate median finder for large streams using reservoir sampling.
    Provides approximate median with bounded memory usage.
    """
    
    def __init__(self, reservoir_size: int = 1000):
        self.reservoir_size = reservoir_size
        self.reservoir = []
        self.count = 0
        
    def add(self, value: T) -> T:
        """Add value and return approximate median."""
        self.count += 1
        
        if len(self.reservoir) < self.reservoir_size:
            self.reservoir.append(value)
        else:
            # Reservoir sampling: replace random element with probability k/n
            j = random.randint(0, self.count - 1)
            if j < self.reservoir_size:
                self.reservoir[j] = value
        
        # Return approximate median
        if self.reservoir:
            sorted_reservoir = sorted(self.reservoir)
            return sorted_reservoir[len(sorted_reservoir) // 2]
        return value
```

## Specialized Data Structures

### Order Statistics Tree

For dynamic scenarios where you need to frequently insert, delete, and query order statistics:

```python
class OrderStatisticsTree:
    """
    Balanced BST that supports order statistics queries in O(log n).
    Based on augmented Red-Black tree concept.
    """
    
    class Node:
        def __init__(self, value):
            self.value = value
            self.left = None
            self.right = None
            self.size = 1  # Size of subtree rooted at this node
    
    def __init__(self):
        self.root = None
    
    def insert(self, value: T):
        """Insert value into the tree."""
        self.root = self._insert(self.root, value)
    
    def _insert(self, node, value):
        if not node:
            return self.Node(value)
        
        if value <= node.value:
            node.left = self._insert(node.left, value)
        else:
            node.right = self._insert(node.right, value)
        
        node.size = 1 + self._size(node.left) + self._size(node.right)
        return node
    
    def _size(self, node):
        return node.size if node else 0
    
    def select(self, k: int) -> T:
        """Find k-th smallest element (1-indexed)."""
        if k < 1 or k > self._size(self.root):
            raise ValueError("k out of bounds")
        return self._select(self.root, k)
    
    def _select(self, node, k):
        if not node:
            raise ValueError("Invalid tree state")
        
        left_size = self._size(node.left)
        
        if k == left_size + 1:
            return node.value
        elif k <= left_size:
            return self._select(node.left, k)
        else:
            return self._select(node.right, k - left_size - 1)
    
    def rank(self, value: T) -> int:
        """Find rank (1-indexed position) of value."""
        return self._rank(self.root, value)
    
    def _rank(self, node, value):
        if not node:
            return 0
        
        if value < node.value:
            return self._rank(node.left, value)
        elif value > node.value:
            return 1 + self._size(node.left) + self._rank(node.right, value)
        else:
            return self._size(node.left) + 1
```

## Advanced Rust Implementations

Here are the Rust equivalents of the advanced features:

```rust
use std::sync::{Arc, Mutex};
use std::thread;
use rayon::prelude::*; // For parallel processing

impl SelectionAlgorithms {
    /// Iterative QuickSelect to avoid stack overflow
    pub fn quickselect_iterative<T: Clone + Ord>(
        arr: &[T], 
        k: usize
    ) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input".to_string());
        }
        
        let mut arr_copy = arr.to_vec();
        let mut low = 0;
        let mut high = arr_copy.len() - 1;
        let target_k = k - 1; // Convert to 0-indexed
        
        while low < high {
            let mut rng = rand::thread_rng();
            let pivot_idx = rng.gen_range(low..=high);
            let pivot_pos = Self::partition(&mut arr_copy, low, high, pivot_idx);
            
            match target_k.cmp(&pivot_pos) {
                std::cmp::Ordering::Equal => return Ok(arr_copy[target_k].clone()),
                std::cmp::Ordering::Less => high = pivot_pos - 1,
                std::cmp::Ordering::Greater => low = pivot_pos + 1,
            }
        }
        
        Ok(arr_copy[low].clone())
    }
    
    /// Parallel QuickSelect using Rayon
    pub fn parallel_quickselect<T: Clone + Ord + Send + Sync>(
        arr: &[T], 
        k: usize
    ) -> Result<T, String> {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input".to_string());
        }
        
        if arr.len() < 1000 {
            return Self::quickselect(arr, k);
        }
        
        let sample_size = std::cmp::min(arr.len(), 1000);
        let mut rng = rand::thread_rng();
        let sample: Vec<T> = arr.choose_multiple(&mut rng, sample_size)
            .cloned().collect();
        let pivot = Self::quickselect(&sample, sample.len() / 2)?;
        
        // Parallel partition
        let (smaller, equal, larger): (Vec<T>, Vec<T>, Vec<T>) = arr
            .par_iter()
            .fold(
                || (Vec::new(), Vec::new(), Vec::new()),
                |mut acc, item| {
                    match item.cmp(&pivot) {
                        std::cmp::Ordering::Less => acc.0.push(item.clone()),
                        std::cmp::Ordering::Equal => acc.1.push(item.clone()),
                        std::cmp::Ordering::Greater => acc.2.push(item.clone()),
                    }
                    acc
                },
            )
            .reduce(
                || (Vec::new(), Vec::new(), Vec::new()),
                |mut acc, item| {
                    acc.0.extend(item.0);
                    acc.1.extend(item.1);
                    acc.2.extend(item.2);
                    acc
                },
            );
        
        if k <= smaller.len() {
            Self::parallel_quickselect(&smaller, k)
        } else if k <= smaller.len() + equal.len() {
            Ok(pivot)
        } else {
            Self::parallel_quickselect(&larger, k - smaller.len() - equal.len())
        }
    }
    
    /// QuickSelect with custom key function
    pub fn quickselect_with_key<T, K, F>(
        arr: &[T], 
        k: usize, 
        key_fn: F
    ) -> Result<T, String> 
    where
        T: Clone,
        K: Ord,
        F: Fn(&T) -> K + Clone,
    {
        if arr.is_empty() || k == 0 || k > arr.len() {
            return Err("Invalid input".to_string());
        }
        
        let mut indexed_arr: Vec<_> = arr.iter().enumerate().collect();
        
        let result_idx = Self::quickselect_with_key_helper(
            &mut indexed_arr, 0, indexed_arr.len() - 1, k - 1, key_fn
        );
        
        Ok(arr[result_idx].clone())
    }
    
    fn quickselect_with_key_helper<T, K, F>(
        indexed_arr: &mut [(usize, &T)],
        low: usize,
        high: usize,
        k: usize,
        key_fn: F,
    ) -> usize
    where
        K: Ord,
        F: Fn(&T) -> K + Clone,
    {
        if low == high {
            return indexed_arr[low].0;
        }
        
        let mut rng = rand::thread_rng();
        let pivot_idx = rng.gen_range(low..=high);
        let pivot_pos = Self::partition_with_key(
            indexed_arr, low, high, pivot_idx, key_fn.clone()
        );
        
        match k.cmp(&pivot_pos) {
            std::cmp::Ordering::Equal => indexed_arr[k].0,
            std::cmp::Ordering::Less => {
                Self::quickselect_with_key_helper(
                    indexed_arr, low, pivot_pos - 1, k, key_fn
                )
            }
            std::cmp::Ordering::Greater => {
                Self::quickselect_with_key_helper(
                    indexed_arr, pivot_pos + 1, high, k, key_fn
                )
            }
        }
    }
    
    fn partition_with_key<T, K, F>(
        indexed_arr: &mut [(usize, &T)],
        low: usize,
        high: usize,
        pivot_idx: usize,
        key_fn: F,
    ) -> usize
    where
        K: Ord,
        F: Fn(&T) -> K,
    {
        indexed_arr.swap(pivot_idx, high);
        let pivot_key = key_fn(indexed_arr[high].1);
        
        let mut i = low;
        for j in low..high {
            if key_fn(indexed_arr[j].1) <= pivot_key {
                indexed_arr.swap(i, j);
                i += 1;
            }
        }
        
        indexed_arr.swap(i, high);
        i
    }
}

/// Streaming selection for finding k-th smallest in a stream
pub struct StreamingSelector<T> {
    k: usize,
    heap: std::collections::BinaryHeap<T>,
}

impl<T: Ord + Clone> StreamingSelector<T> {
    pub fn new(k: usize) -> Self {
        Self {
            k,
            heap: std::collections::BinaryHeap::new(),
        }
    }
    
    pub fn add(&mut self, value: T) -> Option<T> {
        if self.heap.len() < self.k {
            self.heap.push(value);
        } else if let Some(top) = self.heap.peek() {
            if &value < top {
                self.heap.pop();
                self.heap.push(value);
            }
        }
        
        if self.heap.len() == self.k {
            self.heap.peek().cloned()
        } else {
            None
        }
    }
}
```

## Benchmarking and Performance Analysis

### Comprehensive Benchmarking Suite

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class BenchmarkResult:
    algorithm: str
    array_size: int
    k_position: str  # "min", "25%", "median", "75%", "max"
    time_ms: float
    memory_mb: float

class SelectionBenchmark:
    """Comprehensive benchmarking suite for selection algorithms."""
    
    def __init__(self):
        self.algorithms = {
            "QuickSelect": SelectionAlgorithms.quickselect,
            "QuickSelect (Iterative)": SelectionAlgorithms.quickselect_iterative,
            "Median of Medians": SelectionAlgorithms.median_of_medians_select,
            "Heap Select": SelectionAlgorithms.heap_select,
            "Heap Select (Optimized)": SelectionAlgorithms.heap_select_optimized,
            "Sort Select": SelectionAlgorithms.sort_select,
        }
        
        if hasattr(ParallelSelectionAlgorithms, 'parallel_quickselect'):
            self.algorithms["Parallel QuickSelect"] = ParallelSelectionAlgorithms.parallel_quickselect
    
    def run_benchmark(
        self, 
        sizes: List[int] = [100, 500, 1000, 5000, 10000, 50000],
        k_positions: List[str] = ["min", "25%", "median", "75%", "max"],
        num_trials: int = 10
    ) -> List[BenchmarkResult]:
        """Run comprehensive benchmark across different array sizes and k positions."""
        
        results = []
        
        for size in sizes:
            print(f"Benchmarking size {size}...")
            
            # Generate test data
            test_arrays = []
            for _ in range(num_trials):
                arr = [random.randint(1, size * 10) for _ in range(size)]
                test_arrays.append(arr)
            
            for k_pos in k_positions:
                # Calculate actual k value
                if k_pos == "min":
                    k = 1
                elif k_pos == "25%":
                    k = max(1, size // 4)
                elif k_pos == "median":
                    k = size // 2
                elif k_pos == "75%":
                    k = max(1, 3 * size // 4)
                elif k_pos == "max":
                    k = size
                
                for alg_name, algorithm in self.algorithms.items():
                    times = []
                    
                    for arr in test_arrays:
                        start_time = time.perf_counter()
                        try:
                            result = algorithm(arr, k)
                            end_time = time.perf_counter()
                            times.append((end_time - start_time) * 1000)  # Convert to ms
                        except Exception as e:
                            print(f"Error in {alg_name}: {e}")
                            times.append(float('inf'))
                    
                    avg_time = np.mean([t for t in times if t != float('inf')])
                    
                    results.append(BenchmarkResult(
                        algorithm=alg_name,
                        array_size=size,
                        k_position=k_pos,
                        time_ms=avg_time,
                        memory_mb=0  # Would need memory profiling for actual values
                    ))
        
        return results
    
    def generate_report(self, results: List[BenchmarkResult]) -> str:
        """Generate comprehensive performance report."""
        
        df = pd.DataFrame([
            {
                'Algorithm': r.algorithm,
                'Size': r.array_size,
                'K Position': r.k_position,
                'Time (ms)': r.time_ms
            }
            for r in results
        ])
        
        report = "# Selection Algorithms Performance Report\n\n"
        
        # Summary statistics
        report += "## Performance Summary\n\n"
        for alg in df['Algorithm'].unique():
            alg_data = df[df['Algorithm'] == alg]['Time (ms)']
            report += f"**{alg}:**\n"
            report += f"- Mean: {alg_data.mean():.2f}ms\n"
            report += f"- Std: {alg_data.std():.2f}ms\n"
            report += f"- Min: {alg_data.min():.2f}ms\n"
            report += f"- Max: {alg_data.max():.2f}ms\n\n"
        
        # Best algorithm by category
        report += "## Best Algorithm by Category\n\n"
        
        for k_pos in df['K Position'].unique():
            k_data = df[df['K Position'] == k_pos]
            best_alg = k_data.groupby('Algorithm')['Time (ms)'].mean().idxmin()
            best_time = k_data.groupby('Algorithm')['Time (ms)'].mean().min()
            
            report += f"**{k_pos} element:** {best_alg} ({best_time:.2f}ms average)\n"
        
        return report
    
    def plot_results(self, results: List[BenchmarkResult]):
        """Generate performance visualization plots."""
        
        df = pd.DataFrame([
            {
                'Algorithm': r.algorithm,
                'Size': r.array_size,
                'K Position': r.k_position,
                'Time (ms)': r.time_ms
            }
            for r in results
        ])
        
        # Plot 1: Performance vs Array Size (for median)
        plt.figure(figsize=(12, 8))
        
        median_data = df[df['K Position'] == 'median']
        for alg in median_data['Algorithm'].unique():
            alg_data = median_data[median_data['Algorithm'] == alg]
            plt.plot(alg_data['Size'], alg_data['Time (ms)'], 
                    marker='o', label=alg, linewidth=2)
        
        plt.xlabel('Array Size')
        plt.ylabel('Time (milliseconds)')
        plt.title('Selection Algorithms Performance - Finding Median')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        plt.xscale('log')
        plt.show()
        
        # Plot 2: Performance vs K Position (for largest array size)
        plt.figure(figsize=(12, 8))
        
        max_size = df['Size'].max()
        size_data = df[df['Size'] == max_size]
        
        k_order = ["min", "25%", "median", "75%", "max"]
        width = 0.8 / len(size_data['Algorithm'].unique())
        
        for i, alg in enumerate(size_data['Algorithm'].unique()):
            alg_data = size_data[size_data['Algorithm'] == alg]
            x_pos = [k_order.index(k) + i * width for k in alg_data['K Position']]
            plt.bar(x_pos, alg_data['Time (ms)'], width, label=alg)
        
        plt.xlabel('K Position')
        plt.ylabel('Time (milliseconds)')
        plt.title(f'Performance vs K Position (Array Size: {max_size})')
        plt.xticks([i + width * len(size_data['Algorithm'].unique()) / 2 
                   for i in range(len(k_order))], k_order)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

# Usage example:
def run_comprehensive_benchmark():
    benchmark = SelectionBenchmark()
    results = benchmark.run_benchmark()
    report = benchmark.generate_report(results)
    print(report)
    benchmark.plot_results(results)
- Real-time analytics
- Network traffic analysis
# Selection Algorithms: Comprehensive Guide and Advanced Implementations
- Database query optimization (e.g., finding top-k elements)
- Machine learning feature selection
- Statistical analysis (e.g., finding medians, percentiles)

# Comprehensive Guide to Selection Algorithm Implementation

Selection algorithms are a class of algorithms designed to find the *k*-th smallest (or largest) element in an unordered list or array. This is useful in scenarios like finding medians, order statistics, or selecting top-k elements without fully sorting the data. Unlike sorting algorithms (e.g., quicksort, which takes O(n log n) time on average), efficient selection algorithms aim for O(n) average or worst-case time complexity.

In this guide, we'll cover:
- Key concepts and approaches.
- Time and space complexities.
- Complete implementations in Python and Rust for the most common methods.

We'll focus on finding the *k*-th smallest element (1-indexed, where k=1 is the smallest). Assumptions:
- Input is a list/array of comparable elements (e.g., integers).
- No duplicates handling unless specified.
- Edge cases: empty array, k out of bounds.

## 1. Key Approaches to Selection

### 1.1 Naive Approach: Sort and Pick
- **Description**: Fully sort the array and return the element at index k-1.
- **Pros**: Simple; works with any sorting algorithm.
- **Cons**: Inefficient for large n and small k, as sorting is O(n log n).
- **Time Complexity**: O(n log n) average/worst-case (using quicksort or heapsort).
- **Space Complexity**: O(1) auxiliary (in-place sort) or O(n) (not in-place).
- **When to Use**: Small datasets or when the array needs to be sorted anyway.

### 1.2 Quickselect (Hoare's Algorithm)
- **Description**: Based on quicksort's partitioning. Choose a pivot, partition the array into elements less than/greater than the pivot, and recurse on the relevant subarray containing the k-th element. Average-case linear time due to good pivot choices (randomized).
- **Pros**: Fast in practice; average O(n).
- **Cons**: Worst-case O(n²) if pivots are poor (e.g., sorted array); mitigated by randomization.
- **Time Complexity**: O(n) average, O(n²) worst-case.
- **Space Complexity**: O(1) auxiliary (in-place), but O(log n) recursion depth average.
- **When to Use**: Most practical scenarios; randomize pivot for reliability.

### 1.3 Median of Medians (Deterministic Quickselect)
- **Description**: Improves quickselect by selecting a better pivot: divide the array into groups of 5, find medians of each group, recursively find the median of those medians as the pivot. Guarantees worst-case O(n).
- **Pros**: Linear time in worst-case.
- **Cons**: Higher constant factors; more complex.
- **Time Complexity**: O(n) worst-case.
- **Space Complexity**: O(1) auxiliary, but deeper recursion (O(log n)).
- **When to Use**: When worst-case guarantees are needed (e.g., adversarial inputs).

### 1.4 Heap-Based Selection
- **Description**: Build a min-heap (for k-th smallest) with the first k elements, then iterate through the rest: if an element is larger than the heap root, replace the root and heapify. For large k, use a max-heap for the smallest n-k+1 elements.
- **Pros**: Simple with heap libraries; good for streaming data.
- **Cons**: O(n log k) time, which is worse than O(n) for k ≈ n/2 but better for small k.
- **Time Complexity**: O(n log k).
- **Space Complexity**: O(k).
- **When to Use**: Small k (e.g., top-10); or when memory is not an issue.

## 2. Python Implementations

Python's standard library has `heapq` for heaps and `random` for randomization. We'll implement all approaches.

### 2.1 Naive Approach (Using Sorted)
```python
def naive_select(arr, k):
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid k or empty array")
    sorted_arr = sorted(arr)
    return sorted_arr[k-1]
```

### 2.2 Quickselect (Randomized)
```python
import random

def quickselect(arr, k):
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid k or empty array")
    
    def partition(left, right, pivot_idx):
        pivot = arr[pivot_idx]
        arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]  # Move pivot to end
        store_idx = left
        for i in range(left, right):
            if arr[i] < pivot:
                arr[store_idx], arr[i] = arr[i], arr[store_idx]
                store_idx += 1
        arr[right], arr[store_idx] = arr[store_idx], arr[right]  # Move pivot to final pos
        return store_idx
    
    def select(left, right, k):
        if left == right:
            return arr[left]
        pivot_idx = random.randint(left, right)
        pivot_idx = partition(left, right, pivot_idx)
        if k-1 == pivot_idx:
            return arr[pivot_idx]
        elif k-1 < pivot_idx:
            return select(left, pivot_idx-1, k)
        else:
            return select(pivot_idx+1, right, k)
    
    return select(0, len(arr)-1, k)
```

### 2.3 Median of Medians
```python
def median_of_medians_select(arr, k):
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid k or empty array")
    
    def find_median(subarr):
        return sorted(subarr)[len(subarr)//2]
    
    def select(arr, k):
        n = len(arr)
        if n <= 5:
            return sorted(arr)[k-1]
        
        # Divide into groups of 5, find medians
        medians = []
        for i in range(0, n, 5):
            group = arr[i:i+5]
            medians.append(find_median(group))
        
        # Find median of medians recursively
        pivot = select(medians, len(medians)//2 + 1)
        
        # Partition around pivot
        low = [x for x in arr if x < pivot]
        high = [x for x in arr if x > pivot]
        equal = [x for x in arr if x == pivot]
        
        if k <= len(low):
            return select(low, k)
        elif k <= len(low) + len(equal):
            return pivot
        else:
            return select(high, k - len(low) - len(equal))
    
    return select(arr[:], k)  # Copy to avoid modifying original
```

**Note**: This implementation uses list comprehensions for partitioning (O(n) space). For O(1) space, adapt the quickselect partition.

### 2.4 Heap-Based (Using Min-Heap for k-th Smallest)
```python
import heapq

def heap_select(arr, k):
    if not arr or k < 1 or k > len(arr):
        raise ValueError("Invalid k or empty array")
    if k == 1:
        return min(arr)
    # Build max-heap for smallest k elements (negate for max-heap simulation)
    heap = [-x for x in arr[:k]]
    heapq.heapify(heap)
    for x in arr[k:]:
        if -heap[0] > x:  # If x < largest in heap
            heapq.heappop(heap)
            heapq.heappush(heap, -x)
    return -heap[0]  # Smallest in the "max-heap" is the k-th
```

**Note**: This uses a max-heap (simulated with negatives) to keep the smallest k elements. For k-th largest, use a min-heap directly.

## 3. Rust Implementations

Rust emphasizes safety and performance. We'll use `Vec<i32>` for arrays, `rand` crate for randomization (assume it's available; in practice, add `rand` dependency). For heaps, use `BinaryHeap` (max-heap by default).

### 3.1 Naive Approach (Using Sort)
```rust
fn naive_select(arr: &mut Vec<i32>, k: usize) -> i32 {
    if arr.is_empty() || k == 0 || k > arr.len() {
        panic!("Invalid k or empty array");
    }
    arr.sort();
    arr[k-1]
}
```

### 3.2 Quickselect (Randomized)
```rust
use rand::Rng;

fn quickselect(arr: &mut [i32], k: usize) -> i32 {
    if arr.is_empty() || k == 0 || k > arr.len() {
        panic!("Invalid k or empty array");
    }
    
    fn partition(arr: &mut [i32], left: usize, right: usize, pivot_idx: usize) -> usize {
        let pivot = arr[pivot_idx];
        arr.swap(pivot_idx, right);
        let mut store_idx = left;
        for i in left..right {
            if arr[i] < pivot {
                arr.swap(store_idx, i);
                store_idx += 1;
            }
        }
        arr.swap(right, store_idx);
        store_idx
    }
    
    fn select(arr: &mut [i32], mut left: usize, mut right: usize, k: usize) -> i32 {
        loop {
            if left == right {
                return arr[left];
            }
            let mut rng = rand::thread_rng();
            let pivot_idx = rng.gen_range(left..=right);
            let pivot_idx = partition(arr, left, right, pivot_idx);
            if k-1 == pivot_idx {
                return arr[pivot_idx];
            } else if k-1 < pivot_idx {
                right = pivot_idx - 1;
            } else {
                left = pivot_idx + 1;
            }
        }
    }
    
    select(arr, 0, arr.len()-1, k)
}
```

**Note**: Uses loop instead of recursion for better stack safety.

### 3.3 Median of Medians
```rust
fn median_of_medians_select(arr: &mut Vec<i32>, k: usize) -> i32 {
    if arr.is_empty() || k == 0 || k > arr.len() {
        panic!("Invalid k or empty array");
    }
    
    fn find_median(group: &mut [i32]) -> i32 {
        group.sort();
        group[group.len() / 2]
    }
    
    fn select(arr: &mut Vec<i32>, k: usize) -> i32 {
        let n = arr.len();
        if n <= 5 {
            arr.sort();
            return arr[k-1];
        }
        
        let mut medians = Vec::new();
        for chunk in arr.chunks_mut(5) {
            medians.push(find_median(chunk));
        }
        
        let pivot = select(&mut medians, medians.len() / 2 + 1);
        
        let mut low = Vec::new();
        let mut high = Vec::new();
        let mut equal = Vec::new();
        for &x in arr.iter() {
            if x < pivot {
                low.push(x);
            } else if x > pivot {
                high.push(x);
            } else {
                equal.push(x);
            }
        }
        
        if k <= low.len() {
            select(&mut low, k)
        } else if k <= low.len() + equal.len() {
            pivot
        } else {
            select(&mut high, k - low.len() - equal.len())
        }
    }
    
    select(arr, k)
}
```

**Note**: Uses vectors for partitioning (O(n) space). For in-place, implement a custom partition.

### 3.4 Heap-Based (Using Max-Heap for Smallest k)
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn heap_select(arr: Vec<i32>, k: usize) -> i32 {
    if arr.is_empty() || k == 0 || k > arr.len() {
        panic!("Invalid k or empty array");
    }
    let mut heap: BinaryHeap<Reverse<i32>> = arr[..k].iter().cloned().map(Reverse).collect();
    for &x in &arr[k..] {
        if x < heap.peek().unwrap().0 {
            heap.pop();
            heap.push(Reverse(x));
        }
    }
    heap.peek().unwrap().0
}
```

**Note**: Uses `BinaryHeap` (max-heap) with `Reverse` to simulate min-heap for smallest k. Pop the max (largest of smallest k) when adding smaller elements.

## 4. Usage Examples

### Python Example
```python
arr = [3, 1, 4, 1, 5, 9, 2, 6]
print(quickselect(arr[:], 3))  # Output: 2 (3rd smallest: 1,1,2,... -> 2)
```

### Rust Example
```rust
fn main() {
    let mut arr = vec![3, 1, 4, 1, 5, 9, 2, 6];
    println!("{}", quickselect(&mut arr, 3));  // Output: 2
}
```

## 5. Comparisons

| Approach          | Avg Time | Worst Time | Space | Best For              |
|-------------------|----------|------------|-------|-----------------------|
| Naive (Sort)     | O(n log n) | O(n log n) | O(1)/O(n) | Simplicity          |
| Quickselect      | O(n)     | O(n²)     | O(1)  | General use          |
| Median of Medians| O(n)     | O(n)      | O(n)  | Worst-case guarantee |
| Heap-Based       | O(n log k)| O(n log k)| O(k)  | Small k              |

## 6. Tips and Extensions
- **Handling Duplicates**: All methods work with duplicates; for unique, use a set first (O(n log n)).
- **k-th Largest**: Adjust by finding (n-k+1)-th smallest.
- **Optimization**: For quickselect, use median-of-3 pivot for better performance.
- **Testing**: Verify with sorted arrays, reverses, and random inputs.
- **Libraries**: Python's `numpy.partition` or Rust's crates like `rand` for production.
- **Edge Cases**: k=1 (min), k=n (max), all equal elements.

This guide provides a solid foundation. For deeper dives, explore CLRS (Introduction to Algorithms) chapter on order statistics.

## List of Selection Algorithms

Selection algorithms are designed to find the *k*-th smallest (or largest) element in an unordered list or array, also known as the *k*-th order statistic. Based on the comprehensive guide provided earlier, which focused on core methods for this problem, below is an expanded list of all major selection algorithms mentioned across standard references. This includes the ones from the guide (naive sorting, Quickselect, Median of Medians, and heap-based) as well as additional variants and advanced approaches derived from algorithmic literature.

I've categorized them for clarity: **Core Sequential Algorithms** (for general unsorted arrays), **Variants and Hybrids**, **Advanced/Deterministic Methods**, **Parallel Algorithms**, and **Specialized Data Structure-Based Methods**. Each entry includes a brief description, time complexity (where applicable), and relevant citations.

### Core Sequential Algorithms
These are the most commonly used for finding the *k*-th element in an unsorted array.

| Algorithm              | Description                                                                 | Time Complexity (Average/Worst) | Notes |
|------------------------|-----------------------------------------------------------------------------|---------------------------------|-------|
| Sorting-Based (Naive) | Sort the entire array using a comparison sort (e.g., quicksort or heapsort) and select the element at index *k*-1. | O(n log n) / O(n log n) | Simple but inefficient for large *n* and small *k*.      |
| Heapselect (Heap-Based) | Build a heap (min-heap for *k*-th smallest or max-heap for *k*-th largest) and perform partial heap operations to extract the desired element. Optimizes for small *k*. | O(n + k log n) / O(n log n) | Efficient when *k* is much smaller than *n*; can degenerate for median finding (*k* ≈ *n*/2).     |
| Quickselect (Hoare's Algorithm) | Partition the array around a pivot (often random) and recurse only on the subarray containing the *k*-th element. Related to quicksort. | O(n) / O(n²) | Average linear time; worst-case quadratic mitigated by random pivot. Widely used in practice.             |

### Variants and Hybrids
Extensions or improvements on core methods.

| Algorithm              | Description                                                                 | Time Complexity (Average/Worst) | Notes |
|------------------------|-----------------------------------------------------------------------------|---------------------------------|-------|
| Floyd-Rivest Algorithm | A variant of Quickselect that samples a subset to choose better pivots, reducing recursive calls and achieving near-linear performance with high probability. | O(n) / O(n) (high probability) | Uses sampling for pivot selection; expected comparisons close to n + min(k, n-k).  |
| Introselect            | Hybrid of Quickselect with a fallback to Median of Medians or heap methods to avoid worst-case scenarios. Used in libraries like C++ std::nth_element. | O(n) / O(n) | Combines practical speed of Quickselect with worst-case guarantees.  |

### Advanced/Deterministic Methods
Guarantee linear time without randomization.

| Algorithm              | Description                                                                 | Time Complexity (Average/Worst) | Notes |
|------------------------|-----------------------------------------------------------------------------|---------------------------------|-------|
| Median of Medians (BFPRT) | Divides the array into groups of 5, finds medians of each, then recursively selects the median of those as a pivot for partitioning. Ensures good partition sizes. | O(n) / O(n) | Deterministic linear time; higher constants but worst-case guarantee. Also known as Blum-Floyd-Pratt-Rivest-Tarjan algorithm.     |
| Factories (Partial Order-Based) | Builds partial orders on subsets using comparisons and combines them to identify the *k*-th element. Optimized for minimal comparisons. | O(n) / O(n) | Deterministic; uses at most ~2.942n comparisons for medians. Advanced and theoretical.  |
| Randomized Select      | Similar to Quickselect but with explicit randomization analysis for expected linear time. | O(n) / O(n²) | Focuses on probabilistic bounds; superexponentially small chance of exceeding linear comparisons.   |

### Parallel Algorithms
For parallel computing environments.

| Algorithm              | Description                                                                 | Time Complexity (Average/Worst) | Notes |
|------------------------|-----------------------------------------------------------------------------|---------------------------------|-------|
| Parallel Comparison Tree Models | Uses multiple processors to perform comparisons in parallel steps. | Ω(log log n) steps | Theoretical lower bounds; some algorithms achieve O(log log n) with linear comparisons.  |
| Parallel RAM (PRAM) Models | On EREW PRAM, selects in O(log n) time with O(n / log n) processors. Faster with concurrent access. | O(log n) / O(log n) | Optimal in time and processors for parallel machines.  |

### Specialized Data Structure-Based Methods
For preprocessed or structured data (not strictly for unsorted lists but related).

| Algorithm/Method       | Description                                                                 | Time Complexity (Query) | Notes |
|------------------------|-----------------------------------------------------------------------------|-------------------------|-------|
| Sorted Array Selection | Direct index access if the array is already sorted. | O(1) | Trivial case.  |
| Multi-Dimensional Sorted Structures | For 2D sorted matrices or multiple sorted arrays, use binary search or merging. | O(m log n) or similar | E.g., for sorted matrix: O(n log n) or better with heaps/binary search.   |
| Heap-Ordered Trees / Binary Heaps | Extract from a built heap. | O(k) | Independent of n for some cases.  |
| Order Statistic Trees | Augmented self-balancing BSTs for dynamic insertions/deletions and queries. | O(log n) per operation | Supports updates unlike static arrays.  |
| Limited Memory Selection | For streaming data with O(k) memory: buffer and partition. | O(n) | Useful for large datasets or external memory.  |

### Additional Notes
- **For Merged Sorted Arrays**: Specialized algorithms like binary search or merging for two or more sorted inputs, achieving O(m + n) or better (e.g., for two arrays). 
- **Proposed/New Algorithms**: Some research proposes custom methods (e.g., dividing into columns or new partitioning), but they often build on the above.  
- This list covers all major algorithms based on standard sources. For implementations, refer back to the original guide for Python and Rust examples of the core ones. If you need details on a specific algorithm, let me know!