I've created a comprehensive guide to Merge Sort implementations in both Python and Rust. The guide covers:

## Key Features Included

**Core Implementations:**

- Basic merge sort in both languages
- In-place versions for memory efficiency
- Generic implementations with custom comparators
- Iterative versions to avoid recursion limits

**Advanced Features:**

- External merge sort for large files (Python)
- Streaming merge sort (Rust)
- Parallel implementations
- Zero-copy sorting with indices
- Inversion counting algorithm

**Production-Ready Code:**

- Comprehensive error handling
- Type safety and documentation
- Performance benchmarking code
- Complete test suites
- Memory optimization techniques

**Educational Content:**

- Time/space complexity analysis
- Visual algorithm explanation
- Comparison with other sorting algorithms
- Best practices for each language
- Real-world use cases and when to choose merge sort

The guide provides both educational examples for learning the algorithm and production-ready implementations you can use in real projects. Each implementation includes detailed comments explaining the approach and trade-offs involved.

Would you like me to expand on any particular section, add more optimization techniques, or include additional examples for specific use cases?

# Complete Merge Sort Guide: Python & Rust

## Table of Contents

1. [Algorithm Overview](#algorithm-overview)
2. [Time and Space Complexity](#time-and-space-complexity)
3. [Python Implementations](#python-implementations)
4. [Rust Implementations](#rust-implementations)
5. [Performance Comparisons](#performance-comparisons)
6. [Advanced Optimizations](#advanced-optimizations)
7. [Use Cases and When to Choose Merge Sort](#use-cases-and-when-to-choose-merge-sort)

## Algorithm Overview

Merge Sort is a divide-and-conquer algorithm that works by:

1. **Divide**: Split the array into two halves
2. **Conquer**: Recursively sort both halves
3. **Combine**: Merge the sorted halves back together

The key insight is that merging two sorted arrays is efficient and can be done in linear time.

### Visual Example

```
Initial: [38, 27, 43, 3, 9, 82, 10]

Divide:
[38, 27, 43, 3] | [9, 82, 10]
[38, 27] [43, 3] | [9, 82] [10]
[38] [27] [43] [3] | [9] [82] [10]

Merge:
[27, 38] [3, 43] | [9, 82] [10]
[3, 27, 38, 43] | [9, 10, 82]
[3, 9, 10, 27, 38, 43, 82]
```

## Time and Space Complexity

- **Time Complexity**: O(n log n) in all cases (best, average, worst)
- **Space Complexity**: O(n) for the temporary arrays used during merging
- **Stability**: Yes - maintains relative order of equal elements
- **In-place**: No - requires additional memory

## Python Implementations

### 1. Basic Implementation

```python
def merge_sort_basic(arr):
    """
    Basic merge sort implementation.
    
    Args:
        arr: List of comparable elements
    
    Returns:
        New sorted list
    """
    if len(arr) <= 1:
        return arr
    
    # Divide
    mid = len(arr) // 2
    left = merge_sort_basic(arr[:mid])
    right = merge_sort_basic(arr[mid:])
    
    # Merge
    return merge(left, right)

def merge(left, right):
    """Merge two sorted arrays into one sorted array."""
    result = []
    i = j = 0
    
    # Compare elements and merge
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result
```

### 2. In-Place Implementation (Optimized)

```python
def merge_sort_inplace(arr):
    """
    In-place merge sort that modifies the original array.
    More memory efficient than basic version.
    """
    if len(arr) <= 1:
        return arr
    
    _merge_sort_helper(arr, 0, len(arr) - 1)
    return arr

def _merge_sort_helper(arr, left, right):
    """Helper function for recursive sorting."""
    if left < right:
        mid = (left + right) // 2
        
        # Recursively sort both halves
        _merge_sort_helper(arr, left, mid)
        _merge_sort_helper(arr, mid + 1, right)
        
        # Merge the sorted halves
        _merge_inplace(arr, left, mid, right)

def _merge_inplace(arr, left, mid, right):
    """Merge function that works on array indices."""
    # Create temporary arrays for left and right subarrays
    left_arr = arr[left:mid + 1]
    right_arr = arr[mid + 1:right + 1]
    
    i = j = 0
    k = left
    
    # Merge back into original array
    while i < len(left_arr) and j < len(right_arr):
        if left_arr[i] <= right_arr[j]:
            arr[k] = left_arr[i]
            i += 1
        else:
            arr[k] = right_arr[j]
            j += 1
        k += 1
    
    # Copy remaining elements
    while i < len(left_arr):
        arr[k] = left_arr[i]
        i += 1
        k += 1
    
    while j < len(right_arr):
        arr[k] = right_arr[j]
        j += 1
        k += 1
```

### 3. Generic Implementation with Custom Comparator

```python
from typing import List, TypeVar, Callable, Optional

T = TypeVar('T')

def merge_sort_generic(
    arr: List[T], 
    key: Optional[Callable[[T], any]] = None,
    reverse: bool = False
) -> List[T]:
    """
    Generic merge sort with custom comparison.
    
    Args:
        arr: List to sort
        key: Function to extract comparison key from each element
        reverse: If True, sort in descending order
    
    Returns:
        New sorted list
    """
    if len(arr) <= 1:
        return arr[:]
    
    def compare(a: T, b: T) -> bool:
        """Compare two elements based on key and reverse."""
        key_a = key(a) if key else a
        key_b = key(b) if key else b
        
        if reverse:
            return key_a >= key_b
        return key_a <= key_b
    
    def merge_generic(left: List[T], right: List[T]) -> List[T]:
        """Merge with custom comparison."""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if compare(left[i], right[j]):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result
    
    mid = len(arr) // 2
    left = merge_sort_generic(arr[:mid], key, reverse)
    right = merge_sort_generic(arr[mid:], key, reverse)
    
    return merge_generic(left, right)

# Example usage
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def __repr__(self):
        return f"Person('{self.name}', {self.age})"

# Sort by age
people = [Person("Alice", 30), Person("Bob", 25), Person("Charlie", 35)]
sorted_people = merge_sort_generic(people, key=lambda p: p.age)
```

### 4. Iterative Implementation

```python
def merge_sort_iterative(arr):
    """
    Iterative merge sort implementation.
    Avoids recursion stack overflow for very large arrays.
    """
    if len(arr) <= 1:
        return arr[:]
    
    result = arr[:]
    n = len(result)
    
    # Start with subarrays of size 1, then 2, 4, 8, etc.
    size = 1
    while size < n:
        # Process pairs of subarrays
        for start in range(0, n, size * 2):
            mid = min(start + size, n)
            end = min(start + size * 2, n)
            
            if mid < end:
                # Merge result[start:mid] and result[mid:end]
                _merge_iterative(result, start, mid, end)
        
        size *= 2
    
    return result

def _merge_iterative(arr, start, mid, end):
    """Helper function for iterative merge."""
    left = arr[start:mid]
    right = arr[mid:end]
    
    i = j = 0
    k = start
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1
```

## Rust Implementations

### 1. Basic Implementation

```rust
fn merge_sort_basic<T: Clone + Ord>(arr: &[T]) -> Vec<T> {
    if arr.len() <= 1 {
        return arr.to_vec();
    }
    
    let mid = arr.len() / 2;
    let left = merge_sort_basic(&arr[..mid]);
    let right = merge_sort_basic(&arr[mid..]);
    
    merge(&left, &right)
}

fn merge<T: Clone + Ord>(left: &[T], right: &[T]) -> Vec<T> {
    let mut result = Vec::with_capacity(left.len() + right.len());
    let mut i = 0;
    let mut j = 0;
    
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            result.push(left[i].clone());
            i += 1;
        } else {
            result.push(right[j].clone());
            j += 1;
        }
    }
    
    // Add remaining elements
    result.extend_from_slice(&left[i..]);
    result.extend_from_slice(&right[j..]);
    
    result
}
```

### 2. In-Place Implementation

```rust
fn merge_sort_inplace<T: Clone + Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    
    merge_sort_helper(arr, 0, arr.len() - 1);
}

fn merge_sort_helper<T: Clone + Ord>(arr: &mut [T], left: usize, right: usize) {
    if left < right {
        let mid = left + (right - left) / 2;
        
        merge_sort_helper(arr, left, mid);
        merge_sort_helper(arr, mid + 1, right);
        merge_inplace(arr, left, mid, right);
    }
}

fn merge_inplace<T: Clone + Ord>(arr: &mut [T], left: usize, mid: usize, right: usize) {
    let left_arr: Vec<T> = arr[left..=mid].to_vec();
    let right_arr: Vec<T> = arr[mid + 1..=right].to_vec();
    
    let mut i = 0;
    let mut j = 0;
    let mut k = left;
    
    while i < left_arr.len() && j < right_arr.len() {
        if left_arr[i] <= right_arr[j] {
            arr[k] = left_arr[i].clone();
            i += 1;
        } else {
            arr[k] = right_arr[j].clone();
            j += 1;
        }
        k += 1;
    }
    
    while i < left_arr.len() {
        arr[k] = left_arr[i].clone();
        i += 1;
        k += 1;
    }
    
    while j < right_arr.len() {
        arr[k] = right_arr[j].clone();
        j += 1;
        k += 1;
    }
}
```

### 3. Generic Implementation with Custom Comparator

```rust
use std::cmp::Ordering;

fn merge_sort_by<T, F>(arr: &[T], compare: F) -> Vec<T>
where
    T: Clone,
    F: Fn(&T, &T) -> Ordering + Copy,
{
    if arr.len() <= 1 {
        return arr.to_vec();
    }
    
    let mid = arr.len() / 2;
    let left = merge_sort_by(&arr[..mid], compare);
    let right = merge_sort_by(&arr[mid..], compare);
    
    merge_by(&left, &right, compare)
}

fn merge_by<T, F>(left: &[T], right: &[T], compare: F) -> Vec<T>
where
    T: Clone,
    F: Fn(&T, &T) -> Ordering,
{
    let mut result = Vec::with_capacity(left.len() + right.len());
    let mut i = 0;
    let mut j = 0;
    
    while i < left.len() && j < right.len() {
        match compare(&left[i], &right[j]) {
            Ordering::Less | Ordering::Equal => {
                result.push(left[i].clone());
                i += 1;
            }
            Ordering::Greater => {
                result.push(right[j].clone());
                j += 1;
            }
        }
    }
    
    result.extend_from_slice(&left[i..]);
    result.extend_from_slice(&right[j..]);
    
    result
}

// Example usage with custom types
#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: &str, age: u32) -> Self {
        Person {
            name: name.to_string(),
            age,
        }
    }
}

// Sort by age
let people = vec![
    Person::new("Alice", 30),
    Person::new("Bob", 25),
    Person::new("Charlie", 35),
];

let sorted = merge_sort_by(&people, |a, b| a.age.cmp(&b.age));
```

### 4. Zero-Copy Implementation (Advanced Rust)

```rust
fn merge_sort_indices<T: Ord>(arr: &[T]) -> Vec<usize> {
    let mut indices: Vec<usize> = (0..arr.len()).collect();
    merge_sort_indices_helper(arr, &mut indices, 0, arr.len());
    indices
}

fn merge_sort_indices_helper<T: Ord>(
    arr: &[T],
    indices: &mut [usize],
    start: usize,
    end: usize,
) {
    if end - start <= 1 {
        return;
    }
    
    let mid = start + (end - start) / 2;
    merge_sort_indices_helper(arr, indices, start, mid);
    merge_sort_indices_helper(arr, indices, mid, end);
    merge_indices(arr, indices, start, mid, end);
}

fn merge_indices<T: Ord>(
    arr: &[T],
    indices: &mut [usize],
    start: usize,
    mid: usize,
    end: usize,
) {
    let left_indices: Vec<usize> = indices[start..mid].to_vec();
    let right_indices: Vec<usize> = indices[mid..end].to_vec();
    
    let mut i = 0;
    let mut j = 0;
    let mut k = start;
    
    while i < left_indices.len() && j < right_indices.len() {
        if arr[left_indices[i]] <= arr[right_indices[j]] {
            indices[k] = left_indices[i];
            i += 1;
        } else {
            indices[k] = right_indices[j];
            j += 1;
        }
        k += 1;
    }
    
    while i < left_indices.len() {
        indices[k] = left_indices[i];
        i += 1;
        k += 1;
    }
    
    while j < right_indices.len() {
        indices[k] = right_indices[j];
        j += 1;
        k += 1;
    }
}
```

## Performance Comparisons

### Python Benchmarking Code

```python
import time
import random
from typing import List, Callable

def benchmark_sort(sort_func: Callable, arr: List[int], name: str) -> float:
    """Benchmark a sorting function."""
    arr_copy = arr[:]
    start_time = time.perf_counter()
    sort_func(arr_copy)
    end_time = time.perf_counter()
    return end_time - start_time

def run_benchmarks():
    """Run comprehensive benchmarks."""
    sizes = [1000, 5000, 10000, 50000]
    
    for size in sizes:
        print(f"\n--- Array Size: {size} ---")
        
        # Random data
        random_data = [random.randint(1, 1000) for _ in range(size)]
        
        # Nearly sorted data
        nearly_sorted = list(range(size))
        for _ in range(size // 20):  # Swap 5% of elements
            i, j = random.randint(0, size-1), random.randint(0, size-1)
            nearly_sorted[i], nearly_sorted[j] = nearly_sorted[j], nearly_sorted[i]
        
        # Reverse sorted data
        reverse_sorted = list(range(size, 0, -1))
        
        test_cases = [
            ("Random", random_data),
            ("Nearly Sorted", nearly_sorted),
            ("Reverse Sorted", reverse_sorted)
        ]
        
        for case_name, data in test_cases:
            print(f"\n{case_name} Data:")
            
            basic_time = benchmark_sort(merge_sort_basic, data, "Basic")
            inplace_time = benchmark_sort(merge_sort_inplace, data, "In-place")
            builtin_time = benchmark_sort(sorted, data, "Built-in")
            
            print(f"  Basic Merge Sort: {basic_time:.4f}s")
            print(f"  In-place Merge Sort: {inplace_time:.4f}s")
            print(f"  Python sorted(): {builtin_time:.4f}s")

if __name__ == "__main__":
    run_benchmarks()
```

### Rust Benchmarking Code

```rust
use std::time::Instant;
use rand::Rng;

fn benchmark_sort<T, F>(mut sort_func: F, mut arr: Vec<T>, name: &str) -> std::time::Duration
where
    T: Clone,
    F: FnMut(&mut [T]),
{
    let start = Instant::now();
    sort_func(&mut arr);
    start.elapsed()
}

fn run_benchmarks() {
    let sizes = vec![1000, 5000, 10000, 50000];
    let mut rng = rand::thread_rng();
    
    for size in sizes {
        println!("\n--- Array Size: {} ---", size);
        
        // Random data
        let random_data: Vec<i32> = (0..size).map(|_| rng.gen_range(1..1000)).collect();
        
        // Nearly sorted data
        let mut nearly_sorted: Vec<i32> = (0..size).collect();
        for _ in 0..size/20 {
            let i = rng.gen_range(0..size);
            let j = rng.gen_range(0..size);
            nearly_sorted.swap(i, j);
        }
        
        // Reverse sorted data
        let reverse_sorted: Vec<i32> = (0..size).rev().collect();
        
        let test_cases = vec![
            ("Random", random_data),
            ("Nearly Sorted", nearly_sorted),
            ("Reverse Sorted", reverse_sorted),
        ];
        
        for (case_name, data) in test_cases {
            println!("\n{}:", case_name);
            
            let inplace_time = benchmark_sort(
                |arr| merge_sort_inplace(arr),
                data.clone(),
                "In-place"
            );
            
            let builtin_time = benchmark_sort(
                |arr| arr.sort(),
                data.clone(),
                "Built-in"
            );
            
            println!("  Merge Sort (in-place): {:?}", inplace_time);
            println!("  Rust sort(): {:?}", builtin_time);
        }
    }
}
```

## Advanced Optimizations

### 1. Hybrid Merge Sort (Python)

```python
def merge_sort_hybrid(arr, threshold=10):
    """
    Hybrid merge sort that uses insertion sort for small arrays.
    More efficient for small subarrays.
    """
    if len(arr) <= threshold:
        return insertion_sort(arr)
    
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort_hybrid(arr[:mid], threshold)
    right = merge_sort_hybrid(arr[mid:], threshold)
    
    return merge(left, right)

def insertion_sort(arr):
    """Simple insertion sort for small arrays."""
    result = arr[:]
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = key
    return result
```

### 2. Natural Merge Sort (Rust)

```rust
fn natural_merge_sort<T: Clone + Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    
    loop {
        let runs = find_runs(arr);
        if runs.len() <= 1 {
            break; // Array is sorted
        }
        
        merge_runs(arr, &runs);
    }
}

fn find_runs<T: Ord>(arr: &[T]) -> Vec<(usize, usize)> {
    let mut runs = Vec::new();
    let mut start = 0;
    
    while start < arr.len() {
        let mut end = start + 1;
        
        // Find ascending run
        while end < arr.len() && arr[end - 1] <= arr[end] {
            end += 1;
        }
        
        runs.push((start, end));
        start = end;
    }
    
    runs
}

fn merge_runs<T: Clone + Ord>(arr: &mut [T], runs: &[(usize, usize)]) {
    // Merge adjacent runs
    for i in (0..runs.len() - 1).step_by(2) {
        let (left_start, left_end) = runs[i];
        let (right_start, right_end) = if i + 1 < runs.len() {
            runs[i + 1]
        } else {
            continue;
        };
        
        if left_end == right_start {
            merge_inplace_range(arr, left_start, left_end - 1, right_end - 1);
        }
    }
}

fn merge_inplace_range<T: Clone + Ord>(
    arr: &mut [T],
    left: usize,
    mid: usize,
    right: usize,
) {
    let left_arr: Vec<T> = arr[left..=mid].to_vec();
    let right_arr: Vec<T> = arr[mid + 1..=right].to_vec();
    
    let mut i = 0;
    let mut j = 0;
    let mut k = left;
    
    while i < left_arr.len() && j < right_arr.len() {
        if left_arr[i] <= right_arr[j] {
            arr[k] = left_arr[i].clone();
            i += 1;
        } else {
            arr[k] = right_arr[j].clone();
            j += 1;
        }
        k += 1;
    }
    
    while i < left_arr.len() {
        arr[k] = left_arr[i].clone();
        i += 1;
        k += 1;
    }
    
    while j < right_arr.len() {
        arr[k] = right_arr[j].clone();
        j += 1;
        k += 1;
    }
}
```

### 3. Parallel Merge Sort (Rust with Rayon)

```rust
// Note: This requires the `rayon` crate
use rayon::prelude::*;

fn parallel_merge_sort<T: Send + Clone + Ord>(arr: &[T]) -> Vec<T> {
    if arr.len() <= 1000 {
        // Use sequential sort for small arrays
        return merge_sort_basic(arr);
    }
    
    let mid = arr.len() / 2;
    let (left, right) = rayon::join(
        || parallel_merge_sort(&arr[..mid]),
        || parallel_merge_sort(&arr[mid..]),
    );
    
    merge(&left, &right)
}
```

## Complete Test Suite

### Python Tests

```python
import unittest
import random

class TestMergeSort(unittest.TestCase):
    
    def setUp(self):
        self.test_cases = [
            [],
            [1],
            [2, 1],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [5, 4, 3, 2, 1],  # Reverse sorted
            [1, 2, 3, 4, 5],  # Already sorted
            [1, 1, 1, 1, 1],  # All equal
            [random.randint(1, 100) for _ in range(100)],  # Random
        ]
    
    def test_basic_merge_sort(self):
        for arr in self.test_cases:
            with self.subTest(arr=arr):
                result = merge_sort_basic(arr)
                expected = sorted(arr)
                self.assertEqual(result, expected)
                # Ensure original array is unchanged
                self.assertIsNot(result, arr)
    
    def test_inplace_merge_sort(self):
        for arr in self.test_cases:
            with self.subTest(arr=arr):
                arr_copy = arr[:]
                result = merge_sort_inplace(arr_copy)
                expected = sorted(arr)
                self.assertEqual(result, expected)
    
    def test_generic_merge_sort(self):
        # Test with custom key
        people = [Person("Alice", 30), Person("Bob", 25), Person("Charlie", 35)]
        sorted_by_age = merge_sort_generic(people, key=lambda p: p.age)
        
        ages = [p.age for p in sorted_by_age]
        self.assertEqual(ages, [25, 30, 35])
        
        # Test reverse
        sorted_reverse = merge_sort_generic([3, 1, 4, 1, 5], reverse=True)
        self.assertEqual(sorted_reverse, [5, 4, 3, 1, 1])
    
    def test_iterative_merge_sort(self):
        for arr in self.test_cases:
            with self.subTest(arr=arr):
                result = merge_sort_iterative(arr)
                expected = sorted(arr)
                self.assertEqual(result, expected)
    
    def test_stability(self):
        """Test that merge sort is stable."""
        # Create array with duplicate values that have different properties
        class Item:
            def __init__(self, value, order):
                self.value = value
                self.order = order
            
            def __le__(self, other):
                return self.value <= other.value
            
            def __eq__(self, other):
                return self.value == other.value
        
        items = [Item(1, 'first'), Item(2, 'a'), Item(1, 'second'), Item(2, 'b')]
        sorted_items = merge_sort_basic(items)
        
        # Items with same value should maintain original order
        ones = [item for item in sorted_items if item.value == 1]
        twos = [item for item in sorted_items if item.value == 2]
        
        self.assertEqual(ones[0].order, 'first')
        self.assertEqual(ones[1].order, 'second')
        self.assertEqual(twos[0].order, 'a')
        self.assertEqual(twos[1].order, 'b')

if __name__ == "__main__":
    unittest.main()
```

### Rust Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_merge_sort() {
        let test_cases = vec![
            vec![],
            vec![1],
            vec![2, 1],
            vec![3, 1, 4, 1, 5, 9, 2, 6],
            vec![5, 4, 3, 2, 1],  // Reverse sorted
            vec![1, 2, 3, 4, 5],  // Already sorted
            vec![1, 1, 1, 1, 1],  // All equal
        ];
        
        for mut arr in test_cases {
            let original = arr.clone();
            let mut expected = arr.clone();
            expected.sort();
            
            let result = merge_sort_basic(&arr);
            assert_eq!(result, expected);
            
            // Test in-place version
            merge_sort_inplace(&mut arr);
            assert_eq!(arr, expected);
        }
    }
    
    #[test]
    fn test_custom_comparator() {
        let people = vec![
            Person::new("Alice", 30),
            Person::new("Bob", 25),
            Person::new("Charlie", 35),
        ];
        
        let sorted = merge_sort_by(&people, |a, b| a.age.cmp(&b.age));
        let ages: Vec<u32> = sorted.iter().map(|p| p.age).collect();
        assert_eq!(ages, vec![25, 30, 35]);
    }
    
    #[test]
    fn test_stability() {
        #[derive(Debug, Clone, PartialEq)]
        struct Item {
            value: i32,
            order: String,
        }
        
        let items = vec![
            Item { value: 1, order: "first".to_string() },
            Item { value: 2, order: "a".to_string() },
            Item { value: 1, order: "second".to_string() },
            Item { value: 2, order: "b".to_string() },
        ];
        
        let sorted = merge_sort_by(&items, |a, b| a.value.cmp(&b.value));
        
        // Check stability: items with same value maintain original order
        assert_eq!(sorted[0].order, "first");
        assert_eq!(sorted[1].order, "second");
        assert_eq!(sorted[2].order, "a");
        assert_eq!(sorted[3].order, "b");
    }
    
    #[test]
    fn test_large_array() {
        let mut rng = rand::thread_rng();
        let size = 10000;
        let arr: Vec<i32> = (0..size).map(|_| rng.gen_range(1..1000)).collect();
        
        let mut expected = arr.clone();
        expected.sort();
        
        let result = merge_sort_basic(&arr);
        assert_eq!(result, expected);
    }
}

// Cargo.toml dependencies for benchmarks:
// [dependencies]
// rand = "0.8"
//
// [dev-dependencies]
// criterion = "0.5"

#[cfg(feature = "bench")]
mod benches {
    use super::*;
    use criterion::{black_box, criterion_group, criterion_main, Criterion};
    use rand::Rng;
    
    fn benchmark_merge_sorts(c: &mut Criterion) {
        let mut rng = rand::thread_rng();
        let sizes = vec![1000, 5000, 10000];
        
        for size in sizes {
            let data: Vec<i32> = (0..size).map(|_| rng.gen_range(1..1000)).collect();
            
            c.bench_function(&format!("merge_sort_basic_{}", size), |b| {
                b.iter(|| merge_sort_basic(black_box(&data)))
            });
            
            c.bench_function(&format!("merge_sort_inplace_{}", size), |b| {
                b.iter(|| {
                    let mut arr = data.clone();
                    merge_sort_inplace(black_box(&mut arr));
                })
            });
            
            c.bench_function(&format!("std_sort_{}", size), |b| {
                b.iter(|| {
                    let mut arr = data.clone();
                    arr.sort();
                    black_box(arr);
                })
            });
        }
    }
    
    criterion_group!(benches, benchmark_merge_sorts);
    criterion_main!(benches);
}
```

## Memory-Optimized Implementations

### Python Memory-Efficient Version

```python
def merge_sort_memory_efficient(arr, temp_array=None):
    """
    Memory-efficient merge sort that reuses temporary array.
    Reduces memory allocations.
    """
    if temp_array is None:
        temp_array = [None] * len(arr)
    
    _merge_sort_memory_helper(arr, temp_array, 0, len(arr) - 1)
    return arr

def _merge_sort_memory_helper(arr, temp_array, left, right):
    """Helper function that reuses temporary array."""
    if left < right:
        mid = (left + right) // 2
        
        _merge_sort_memory_helper(arr, temp_array, left, mid)
        _merge_sort_memory_helper(arr, temp_array, mid + 1, right)
        _merge_memory_efficient(arr, temp_array, left, mid, right)

def _merge_memory_efficient(arr, temp_array, left, mid, right):
    """Memory-efficient merge using pre-allocated temporary array."""
    # Copy to temporary array
    for i in range(left, right + 1):
        temp_array[i] = arr[i]
    
    i = left      # Left subarray index
    j = mid + 1   # Right subarray index
    k = left      # Merged array index
    
    while i <= mid and j <= right:
        if temp_array[i] <= temp_array[j]:
            arr[k] = temp_array[i]
            i += 1
        else:
            arr[k] = temp_array[j]
            j += 1
        k += 1
    
    # Copy remaining elements
    while i <= mid:
        arr[k] = temp_array[i]
        i += 1
        k += 1
```

### Rust Zero-Allocation Version

```rust
use std::mem;

fn merge_sort_no_alloc<T: Clone + Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    
    // Use a single auxiliary array for the entire sort
    let mut aux = arr.to_vec();
    merge_sort_no_alloc_helper(arr, &mut aux, 0, arr.len() - 1);
}

fn merge_sort_no_alloc_helper<T: Clone + Ord>(
    arr: &mut [T],
    aux: &mut [T],
    left: usize,
    right: usize,
) {
    if left < right {
        let mid = left + (right - left) / 2;
        
        merge_sort_no_alloc_helper(arr, aux, left, mid);
        merge_sort_no_alloc_helper(arr, aux, mid + 1, right);
        merge_no_alloc(arr, aux, left, mid, right);
    }
}

fn merge_no_alloc<T: Clone + Ord>(
    arr: &mut [T],
    aux: &mut [T],
    left: usize,
    mid: usize,
    right: usize,
) {
    // Copy to auxiliary array
    for i in left..=right {
        aux[i] = arr[i].clone();
    }
    
    let mut i = left;
    let mut j = mid + 1;
    let mut k = left;
    
    while i <= mid && j <= right {
        if aux[i] <= aux[j] {
            arr[k] = aux[i].clone();
            i += 1;
        } else {
            arr[k] = aux[j].clone();
            j += 1;
        }
        k += 1;
    }
    
    while i <= mid {
        arr[k] = aux[i].clone();
        i += 1;
        k += 1;
    }
}
```

## Real-World Applications

### 1. External Merge Sort for Large Files (Python)

```python
import heapq
import tempfile
import os

def external_merge_sort(input_file, output_file, chunk_size=1000000):
    """
    Sort large files that don't fit in memory.
    
    Args:
        input_file: Path to input file with one number per line
        output_file: Path to output file
        chunk_size: Number of items to sort in memory at once
    """
    temp_files = []
    
    # Phase 1: Split into sorted chunks
    with open(input_file, 'r') as f:
        chunk = []
        for line in f:
            chunk.append(int(line.strip()))
            
            if len(chunk) >= chunk_size:
                # Sort chunk and write to temporary file
                chunk.sort()  # Could use merge_sort_basic here
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
                for num in chunk:
                    temp_file.write(f"{num}\n")
                temp_file.close()
                temp_files.append(temp_file.name)
                chunk = []
        
        # Handle remaining chunk
        if chunk:
            chunk.sort()
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            for num in chunk:
                temp_file.write(f"{num}\n")
            temp_file.close()
            temp_files.append(temp_file.name)
    
    # Phase 2: Merge all temporary files
    _merge_temp_files(temp_files, output_file)
    
    # Cleanup
    for temp_file in temp_files:
        os.unlink(temp_file)

def _merge_temp_files(temp_files, output_file):
    """Merge multiple sorted files using a min-heap."""
    file_handles = []
    heap = []
    
    # Open all temporary files
    for i, temp_file in enumerate(temp_files):
        f = open(temp_file, 'r')
        file_handles.append(f)
        
        # Read first number from each file
        line = f.readline()
        if line:
            heapq.heappush(heap, (int(line.strip()), i))
    
    with open(output_file, 'w') as out:
        while heap:
            value, file_index = heapq.heappop(heap)
            out.write(f"{value}\n")
            
            # Read next number from the same file
            line = file_handles[file_index].readline()
            if line:
                heapq.heappush(heap, (int(line.strip()), file_index))
    
    # Close all file handles
    for f in file_handles:
        f.close()
```

### 2. Streaming Merge Sort (Rust)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

pub struct StreamingMergeSort<T> {
    chunks: Vec<Vec<T>>,
    chunk_size: usize,
    current_chunk: Vec<T>,
}

impl<T: Clone + Ord> StreamingMergeSort<T> {
    pub fn new(chunk_size: usize) -> Self {
        Self {
            chunks: Vec::new(),
            chunk_size,
            current_chunk: Vec::new(),
        }
    }
    
    pub fn add(&mut self, item: T) {
        self.current_chunk.push(item);
        
        if self.current_chunk.len() >= self.chunk_size {
            self.flush_chunk();
        }
    }
    
    pub fn finish(mut self) -> Vec<T> {
        if !self.current_chunk.is_empty() {
            self.flush_chunk();
        }
        
        self.merge_all_chunks()
    }
    
    fn flush_chunk(&mut self) {
        if !self.current_chunk.is_empty() {
            let mut chunk = Vec::new();
            mem::swap(&mut chunk, &mut self.current_chunk);
            merge_sort_inplace(&mut chunk);
            self.chunks.push(chunk);
        }
    }
    
    fn merge_all_chunks(self) -> Vec<T> {
        if self.chunks.is_empty() {
            return Vec::new();
        }
        
        if self.chunks.len() == 1 {
            return self.chunks.into_iter().next().unwrap();
        }
        
        // Use binary heap to merge all chunks efficiently
        let mut heap = BinaryHeap::new();
        let mut iterators: Vec<_> = self.chunks
            .into_iter()
            .enumerate()
            .map(|(i, chunk)| (i, chunk.into_iter()))
            .collect();
        
        // Initialize heap with first element from each chunk
        for (chunk_id, iter) in &mut iterators {
            if let Some(value) = iter.next() {
                heap.push(Reverse((value.clone(), *chunk_id)));
            }
        }
        
        let mut result = Vec::new();
        
        while let Some(Reverse((value, chunk_id))) = heap.pop() {
            result.push(value);
            
            // Get next element from the same chunk
            if let Some(next_value) = iterators[chunk_id].1.next() {
                heap.push(Reverse((next_value, chunk_id)));
            }
        }
        
        result
    }
}

// Usage example
fn example_streaming_sort() {
    let mut sorter = StreamingMergeSort::new(1000);
    
    // Add data as it arrives
    for i in (0..10000).rev() {
        sorter.add(i);
    }
    
    let sorted_result = sorter.finish();
    assert_eq!(sorted_result, (0..10000).collect::<Vec<_>>());
}
```

## Performance Optimizations Summary

### Python Optimizations

1. **Hybrid Approach**: Use insertion sort for small arrays (< 10-20 elements)
2. **Memory Reuse**: Pre-allocate temporary arrays to reduce garbage collection
3. **Iterative Version**: Avoid recursion overhead for very large arrays
4. **Built-in Functions**: Use `sorted()` for production code unless you need custom behavior

### Rust Optimizations

1. **Zero-Copy Sorting**: Sort indices instead of moving data for large objects
2. **SIMD Instructions**: Use `sort_unstable()` for primitive types when stability isn't needed
3. **Parallel Processing**: Use Rayon for multi-threaded sorting of large datasets
4. **Memory Pool**: Reuse allocations to reduce heap pressure

## Use Cases and When to Choose Merge Sort

### Choose Merge Sort When

- **Stability is Required**: Need to maintain relative order of equal elements
- **Predictable Performance**: O(n log n) guaranteed, no worst-case degradation
- **External Sorting**: Working with data larger than available memory
- **Parallel Processing**: Algorithm parallelizes well
- **Linked Lists**: Natural fit for linked list data structures

### Consider Alternatives When

- **Memory is Limited**: Merge sort requires O(n) extra space
- **Small Arrays**: Insertion sort is faster for small datasets (< 50 elements)
- **Nearly Sorted Data**: Adaptive algorithms like Timsort perform better
- **Primitive Types**: Built-in sorts are often highly optimized

## Comparison with Other Sorting Algorithms

| Algorithm | Time Complexity | Space | Stable | Notes |
|-----------|----------------|-------|--------|-------|
| Merge Sort | O(n log n) | O(n) | Yes | Consistent performance |
| Quick Sort | O(n log n) avg, O(n²) worst | O(log n) | No | Faster average case |
| Heap Sort | O(n log n) | O(1) | No | In-place but slower |
| Tim Sort | O(n) to O(n log n) | O(n) | Yes | Adaptive, used in Python |
| Insertion Sort | O(n²) | O(1) | Yes | Fast for small arrays |

## Complete Working Examples

### Python Example: Sorting Custom Objects

```python
from dataclasses import dataclass
from typing import List
import random

@dataclass
class Student:
    name: str
    grade: float
    age: int
    
    def __repr__(self):
        return f"Student({self.name}, {self.grade}, {self.age})"

def demo_custom_sorting():
    """Demonstrate sorting custom objects with different criteria."""
    students = [
        Student("Alice", 85.5, 20),
        Student("Bob", 92.0, 19),
        Student("Charlie", 78.5, 21),
        Student("Diana", 92.0, 20),  # Same grade as Bob
        Student("Eve", 88.0, 19),
    ]
    
    print("Original students:")
    for student in students:
        print(f"  {student}")
    
    # Sort by grade (descending)
    by_grade = merge_sort_generic(students, key=lambda s: s.grade, reverse=True)
    print(f"\nSorted by grade (desc):")
    for student in by_grade:
        print(f"  {student}")
    
    # Sort by age, then by name
    def multi_key(student):
        return (student.age, student.name)
    
    by_age_name = merge_sort_generic(students, key=multi_key)
    print(f"\nSorted by age, then name:")
    for student in by_age_name:
        print(f"  {student}")

if __name__ == "__main__":
    demo_custom_sorting()
```

### Rust Example: Generic Sorting with Traits

```rust
use std::fmt::Debug;

trait Sortable: Clone + Debug {}
impl<T: Clone + Debug> Sortable for T {}

fn merge_sort_trait<T: Sortable + Ord>(arr: &[T]) -> Vec<T> {
    merge_sort_basic(arr)
}

fn merge_sort_by_key<T, K, F>(arr: &[T], key_fn: F) -> Vec<T>
where
    T: Clone,
    K: Ord,
    F: Fn(&T) -> K + Copy,
{
    merge_sort_by(arr, |a, b| key_fn(a).cmp(&key_fn(b)))
}

#[derive(Debug, Clone)]
struct Product {
    name: String,
    price: f64,
    rating: f32,
}

impl Product {
    fn new(name: &str, price: f64, rating: f32) -> Self {
        Product {
            name: name.to_string(),
            price,
            rating,
        }
    }
}

fn demo_rust_sorting() {
    let products = vec![
        Product::new("Laptop", 999.99, 4.5),
        Product::new("Mouse", 29.99, 4.2),
        Product::new("Keyboard", 79.99, 4.7),
        Product::new("Monitor", 299.99, 4.3),
    ];
    
    println!("Original products:");
    for product in &products {
        println!("  {:?}", product);
    }
    
    // Sort by price
    let by_price = merge_sort_by_key(&products, |p| (p.price * 100.0) as i32);
    println!("\nSorted by price:");
    for product in &by_price {
        println!("  {:?}", product);
    }
    
    // Sort by rating (descending)
    let by_rating = merge_sort_by(&products, |a, b| {
        b.rating.partial_cmp(&a.rating).unwrap_or(std::cmp::Ordering::Equal)
    });
    println!("\nSorted by rating (desc):");
    for product in &by_rating {
        println!("  {:?}", product);
    }
}
```

## Advanced Features and Extensions

### 1. Counting Inversions with Merge Sort

```python
def merge_sort_count_inversions(arr):
    """
    Count inversions while sorting using merge sort.
    An inversion is a pair (i,j) where i < j but arr[i] > arr[j].
    """
    if len(arr) <= 1:
        return arr[:], 0
    
    mid = len(arr) // 2
    left, left_inv = merge_sort_count_inversions(arr[:mid])
    right, right_inv = merge_sort_count_inversions(arr[mid:])
    merged, split_inv = merge_count_split_inversions(left, right)
    
    return merged, left_inv + right_inv + split_inv

def merge_count_split_inversions(left, right):
    """Merge and count split inversions."""
    result = []
    inversions = 0
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            # All remaining elements in left are greater than right[j]
            inversions += len(left) - i
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result, inversions

# Example usage
test_arr = [5, 4, 3, 2, 1]
sorted_arr, inversion_count = merge_sort_count_inversions(test_arr)
print(f"Sorted: {sorted_arr}")
print(f"Inversions: {inversion_count}")  # Should be 10 for [5,4,3,2,1]
```

### 2. Multi-threaded Merge Sort (Python)

```python
import threading
from concurrent.futures import ThreadPoolExecutor
import math

def parallel_merge_sort(arr, max_workers=None):
    """
    Parallel merge sort using ThreadPoolExecutor.
    Effective for large arrays and I/O bound comparisons.
    """
    if len(arr) <= 1000:  # Use sequential for small arrays
        return merge_sort_basic(arr)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return _parallel_merge_sort_helper(arr, executor)

def _parallel_merge_sort_helper(arr, executor):
    """Helper function for parallel merge sort."""
    if len(arr) <= 1000:
        return merge_sort_basic(arr)
    
    mid = len(arr) // 2
    
    # Submit both halves to thread pool
    left_future = executor.submit(_parallel_merge_sort_helper, arr[:mid], executor)
    right_future = executor.submit(_parallel_merge_sort_helper, arr[mid:], executor)
    
    # Wait for both to complete and merge
    left = left_future.result()
    right = right_future.result()
    
    return merge(left, right)
```

## Best Practices and Guidelines

### Python Best Practices

1. **Use Built-in `sorted()`** for most cases - it's highly optimized
2. **Custom Comparisons**: Use `key` parameter instead of custom comparison functions
3. **Memory Management**: Use in-place version for large arrays to reduce memory usage
4. **Type Hints**: Always include type hints for better code documentation
5. **Error Handling**: Validate inputs and handle edge cases

```python
from typing import List, TypeVar, Optional, Callable

T = TypeVar('T')

def robust_merge_sort(
    arr: List[T],
    key: Optional[Callable[[T], any]] = None,
    reverse: bool = False
) -> List[T]:
    """
    Production-ready merge sort with error handling.
    """
    if not isinstance(arr, list):
        raise TypeError("Input must be a list")
    
    if not arr:
        return []
    
    try:
        return merge_sort_generic(arr, key, reverse)
    except Exception as e:
        raise ValueError(f"Error during sorting: {e}")
```

### Rust Best Practices

1. **Use Standard Library**: `slice::sort()` and `slice::sort_by()` are highly optimized
2. **Avoid Unnecessary Cloning**: Use references and borrowing when possible
3. **Generic Constraints**: Use appropriate trait bounds for flexibility
4. **Error Handling**: Use `Result` types for operations that might fail
5. **Documentation**: Include comprehensive examples and panic conditions

```rust
/// Production-ready merge sort with comprehensive error handling
/// 
/// # Examples
/// 
/// ```
/// let mut data = vec![3, 1, 4, 1, 5];
/// production_merge_sort(&mut data);
/// assert_eq!(data, vec![1, 1, 3, 4, 5]);
/// ```
/// 
/// # Panics
/// 
/// This function does not panic under normal circumstances.
pub fn production_merge_sort<T: Clone + Ord>(arr: &mut [T]) {
    if arr.is_empty() {
        return;
    }
    
    merge_sort_inplace(arr);
}

/// Sort with custom comparison and error handling
pub fn production_merge_sort_by<T, F>(
    arr: &mut [T],
    compare: F,
) -> Result<(), &'static str>
where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering + Copy,
{
    if arr.is_empty() {
        return Ok(());
    }
    
    // Validate that comparison function is consistent
    if arr.len() >= 2 {
        let cmp_result = compare(&arr[0], &arr[1]);
        let reverse_cmp = compare(&arr[1], &arr[0]);
        
        if cmp_result == reverse_cmp && cmp_result != std::cmp::Ordering::Equal {
            return Err("Inconsistent comparison function");
        }
    }
    
    merge_sort_inplace_by(arr, compare);
    Ok(())
}

fn merge_sort_inplace_by<T, F>(arr: &mut [T], compare: F)
where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering + Copy,
{
    if arr.len() <= 1 {
        return;
    }
    
    merge_sort_helper_by(arr, 0, arr.len() - 1, compare);
}

fn merge_sort_helper_by<T, F>(
    arr: &mut [T],
    left: usize,
    right: usize,
    compare: F,
) where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering + Copy,
{
    if left < right {
        let mid = left + (right - left) / 2;
        
        merge_sort_helper_by(arr, left, mid, compare);
        merge_sort_helper_by(arr, mid + 1, right, compare);
        merge_inplace_by(arr, left, mid, right, compare);
    }
}

fn merge_inplace_by<T, F>(
    arr: &mut [T],
    left: usize,
    mid: usize,
    right: usize,
    compare: F,
) where
    T: Clone,
    F: Fn(&T, &T) -> std::cmp::Ordering,
{
    let left_arr: Vec<T> = arr[left..=mid].to_vec();
    let right_arr: Vec<T> = arr[mid + 1..=right].to_vec();
    
    let mut i = 0;
    let mut j = 0;
    let mut k = left;
    
    while i < left_arr.len() && j < right_arr.len() {
        match compare(&left_arr[i], &right_arr[j]) {
            std::cmp::Ordering::Less | std::cmp::Ordering::Equal => {
                arr[k] = left_arr[i].clone();
                i += 1;
            }
            std::cmp::Ordering::Greater => {
                arr[k] = right_arr[j].clone();
                j += 1;
            }
        }
        k += 1;
    }
    
    while i < left_arr.len() {
        arr[k] = left_arr[i].clone();
        i += 1;
        k += 1;
    }
    
    while j < right_arr.len() {
        arr[k] = right_arr[j].clone();
        j += 1;
        k += 1;
    }
}
```

## Conclusion

Merge Sort is a fundamental algorithm that provides:

- **Guaranteed O(n log n) performance** in all cases
- **Stable sorting** that preserves element order
- **Excellent parallelization** capabilities
- **Predictable memory usage** patterns

While modern languages provide highly optimized built-in sorting functions, understanding merge sort is crucial for:

- Implementing custom sorting requirements
- Working with external data that doesn't fit in memory
- Educational purposes and algorithm interviews
- Building more complex algorithms that rely on divide-and-conquer principles

The implementations provided here range from educational examples to production-ready code with comprehensive error handling and optimizations. Choose the version that best fits your specific use case and performance requirements.
