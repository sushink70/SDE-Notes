I'll create a comprehensive guide covering Linear Search implementations in both Python and Rust, including theory, multiple variants, and practical examples.I've created a comprehensive guide to Linear Search implementations in both Python and Rust. The guide covers:

## What's Included

**Theory & Fundamentals:**

- Algorithm explanation and pseudocode
- Time/space complexity analysis
- When to use linear search

**Python Implementations:**

- Basic linear search
- Pythonic approaches using built-ins
- Custom comparators and key functions
- Finding multiple occurrences
- Generic class-based implementation

**Rust Implementations:**

- Basic implementations with proper error handling
- Generic implementations with traits
- Custom comparators and predicates
- Complete module with comprehensive functionality

**Advanced Topics:**

- Performance benchmarking code for both languages
- Variants like sentinel search and jump search
- String pattern searching
- Best practices for each language

**Practical Examples:**

- Working with custom objects (Person class)
- Type-safe implementations
- Error handling patterns
- Memory-efficient approaches

The guide demonstrates idiomatic code in both languages - Python's simplicity and built-in functions versus Rust's type safety and zero-cost abstractions. Each implementation includes proper documentation, examples, and test cases where appropriate.

Would you like me to expand on any particular section or add additional variants like parallel linear search implementations?

# Complete Linear Search Guide: Python & Rust

## Table of Contents

1. [Introduction](#introduction)
2. [Algorithm Theory](#algorithm-theory)
3. [Python Implementations](#python-implementations)
4. [Rust Implementations](#rust-implementations)
5. [Performance Analysis](#performance-analysis)
6. [Variants and Extensions](#variants-and-extensions)
7. [Best Practices](#best-practices)
8. [Conclusion](#conclusion)

## Introduction

Linear Search (also known as Sequential Search) is the simplest searching algorithm that finds a target element by checking each element in a collection sequentially until the target is found or the entire collection has been searched.

### Key Characteristics

- **Time Complexity**: O(n) - worst case, average case
- **Space Complexity**: O(1) - constant extra space
- **Stability**: Stable (maintains relative order)
- **Use Cases**: Unsorted data, small datasets, finding first/last occurrence

## Algorithm Theory

### How Linear Search Works

1. Start from the first element of the collection
2. Compare the current element with the target value
3. If they match, return the index/position
4. If they don't match, move to the next element
5. Repeat until element is found or end of collection is reached
6. If end is reached without finding target, return "not found" indicator

### Pseudocode

```
function linearSearch(array, target):
    for i from 0 to length(array) - 1:
        if array[i] equals target:
            return i
    return -1  // Not found
```

## Python Implementations

### 1. Basic Linear Search

```python
def linear_search_basic(arr, target):
    """
    Basic linear search implementation.
    
    Args:
        arr: List of elements to search
        target: Element to find
        
    Returns:
        int: Index of target if found, -1 otherwise
    """
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
result = linear_search_basic(numbers, 22)
print(f"Element found at index: {result}")  # Output: 4
```

### 2. Pythonic Linear Search

```python
def linear_search_pythonic(arr, target):
    """
    Pythonic implementation using enumerate and next.
    
    Args:
        arr: List of elements to search
        target: Element to find
        
    Returns:
        int: Index of target if found, -1 otherwise
    """
    try:
        return next(i for i, item in enumerate(arr) if item == target)
    except StopIteration:
        return -1

# Alternative using list comprehension
def linear_search_list_comp(arr, target):
    """Linear search using list comprehension."""
    indices = [i for i, item in enumerate(arr) if item == target]
    return indices[0] if indices else -1
```

### 3. Linear Search with Custom Comparator

```python
def linear_search_custom(arr, target, key_func=None, compare_func=None):
    """
    Linear search with custom key function and comparator.
    
    Args:
        arr: List of elements to search
        target: Element to find
        key_func: Function to extract comparison key from elements
        compare_func: Custom comparison function
        
    Returns:
        int: Index of target if found, -1 otherwise
    """
    if key_func is None:
        key_func = lambda x: x
    
    if compare_func is None:
        compare_func = lambda a, b: a == b
    
    target_key = key_func(target)
    
    for i, item in enumerate(arr):
        if compare_func(key_func(item), target_key):
            return i
    return -1

# Example with custom objects
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def __repr__(self):
        return f"Person('{self.name}', {self.age})"

people = [Person("Alice", 30), Person("Bob", 25), Person("Charlie", 35)]
result = linear_search_custom(people, Person("Bob", 25), key_func=lambda p: p.name)
```

### 4. Linear Search for Multiple Occurrences

```python
def linear_search_all(arr, target):
    """
    Find all occurrences of target in array.
    
    Args:
        arr: List of elements to search
        target: Element to find
        
    Returns:
        list: List of indices where target is found
    """
    return [i for i, item in enumerate(arr) if item == target]

def linear_search_first_last(arr, target):
    """
    Find first and last occurrence of target.
    
    Returns:
        tuple: (first_index, last_index) or (-1, -1) if not found
    """
    first = last = -1
    
    for i, item in enumerate(arr):
        if item == target:
            if first == -1:
                first = i
            last = i
    
    return first, last

# Example usage
arr_with_duplicates = [1, 3, 5, 3, 7, 3, 9]
all_indices = linear_search_all(arr_with_duplicates, 3)
print(f"All occurrences: {all_indices}")  # [1, 3, 5]

first, last = linear_search_first_last(arr_with_duplicates, 3)
print(f"First: {first}, Last: {last}")  # First: 1, Last: 5
```

### 5. Generic Linear Search Class

```python
from typing import List, TypeVar, Optional, Callable

T = TypeVar('T')

class LinearSearch:
    """A comprehensive linear search implementation."""
    
    @staticmethod
    def search(arr: List[T], target: T) -> int:
        """Basic linear search."""
        for i, item in enumerate(arr):
            if item == target:
                return i
        return -1
    
    @staticmethod
    def search_with_key(arr: List[T], target: T, 
                       key: Callable[[T], any]) -> int:
        """Search with key function."""
        target_key = key(target)
        for i, item in enumerate(arr):
            if key(item) == target_key:
                return i
        return -1
    
    @staticmethod
    def search_all(arr: List[T], target: T) -> List[int]:
        """Find all occurrences."""
        return [i for i, item in enumerate(arr) if item == target]
    
    @staticmethod
    def search_condition(arr: List[T], 
                        condition: Callable[[T], bool]) -> int:
        """Search for first element matching condition."""
        for i, item in enumerate(arr):
            if condition(item):
                return i
        return -1

# Example usage
searcher = LinearSearch()
numbers = [10, 20, 30, 20, 40]

# Basic search
idx = searcher.search(numbers, 20)
print(f"First occurrence of 20: {idx}")

# Search with condition
idx = searcher.search_condition(numbers, lambda x: x > 25)
print(f"First element > 25: {idx}")
```

## Rust Implementations

### 1. Basic Linear Search

```rust
fn linear_search_basic<T: PartialEq>(arr: &[T], target: &T) -> Option<usize> {
    for (index, item) in arr.iter().enumerate() {
        if item == target {
            return Some(index);
        }
    }
    None
}

// Alternative implementation returning -1 for not found (C-style)
fn linear_search_index<T: PartialEq>(arr: &[T], target: &T) -> isize {
    for (index, item) in arr.iter().enumerate() {
        if item == target {
            return index as isize;
        }
    }
    -1
}

fn main() {
    let numbers = vec![64, 34, 25, 12, 22, 11, 90];
    
    match linear_search_basic(&numbers, &22) {
        Some(index) => println!("Element found at index: {}", index),
        None => println!("Element not found"),
    }
}
```

### 2. Generic Linear Search with Traits

```rust
use std::fmt::Debug;

trait LinearSearchable<T> {
    fn linear_search(&self, target: &T) -> Option<usize>;
    fn linear_search_all(&self, target: &T) -> Vec<usize>;
}

impl<T: PartialEq> LinearSearchable<T> for Vec<T> {
    fn linear_search(&self, target: &T) -> Option<usize> {
        self.iter().position(|item| item == target)
    }
    
    fn linear_search_all(&self, target: &T) -> Vec<usize> {
        self.iter()
            .enumerate()
            .filter_map(|(i, item)| if item == target { Some(i) } else { None })
            .collect()
    }
}

impl<T: PartialEq> LinearSearchable<T> for [T] {
    fn linear_search(&self, target: &T) -> Option<usize> {
        self.iter().position(|item| item == target)
    }
    
    fn linear_search_all(&self, target: &T) -> Vec<usize> {
        self.iter()
            .enumerate()
            .filter_map(|(i, item)| if item == target { Some(i) } else { None })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_linear_search() {
        let numbers = vec![1, 3, 5, 7, 3, 9, 3];
        
        assert_eq!(numbers.linear_search(&5), Some(2));
        assert_eq!(numbers.linear_search(&10), None);
        assert_eq!(numbers.linear_search_all(&3), vec![1, 4, 6]);
    }
}
```

### 3. Linear Search with Custom Comparator

```rust
fn linear_search_with_key<T, K, F>(arr: &[T], target: &K, key_fn: F) -> Option<usize>
where
    K: PartialEq,
    F: Fn(&T) -> K,
{
    arr.iter()
       .enumerate()
       .find(|(_, item)| &key_fn(item) == target)
       .map(|(index, _)| index)
}

fn linear_search_with_predicate<T, F>(arr: &[T], predicate: F) -> Option<usize>
where
    F: Fn(&T) -> bool,
{
    arr.iter()
       .enumerate()
       .find(|(_, item)| predicate(item))
       .map(|(index, _)| index)
}

#[derive(Debug, PartialEq)]
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

fn example_custom_search() {
    let people = vec![
        Person::new("Alice", 30),
        Person::new("Bob", 25),
        Person::new("Charlie", 35),
    ];
    
    // Search by name
    if let Some(index) = linear_search_with_key(&people, &"Bob".to_string(), |p| &p.name) {
        println!("Found Bob at index: {}", index);
    }
    
    // Search by age condition
    if let Some(index) = linear_search_with_predicate(&people, |p| p.age > 30) {
        println!("Found person over 30 at index: {}", index);
    }
}
```

### 4. Complete Linear Search Module

```rust
pub mod linear_search {
    use std::cmp::PartialEq;
    
    pub struct LinearSearch;
    
    impl LinearSearch {
        /// Basic linear search returning Option<usize>
        pub fn search<T: PartialEq>(arr: &[T], target: &T) -> Option<usize> {
            arr.iter().position(|item| item == target)
        }
        
        /// Search returning all indices
        pub fn search_all<T: PartialEq>(arr: &[T], target: &T) -> Vec<usize> {
            arr.iter()
                .enumerate()
                .filter_map(|(i, item)| {
                    if item == target { Some(i) } else { None }
                })
                .collect()
        }
        
        /// Search with custom key function
        pub fn search_by_key<T, K, F>(arr: &[T], target: &K, key_fn: F) -> Option<usize>
        where
            K: PartialEq,
            F: Fn(&T) -> K,
        {
            arr.iter()
                .enumerate()
                .find(|(_, item)| &key_fn(item) == target)
                .map(|(index, _)| index)
        }
        
        /// Search with predicate function
        pub fn search_by<T, F>(arr: &[T], predicate: F) -> Option<usize>
        where
            F: Fn(&T) -> bool,
        {
            arr.iter()
                .enumerate()
                .find(|(_, item)| predicate(item))
                .map(|(index, _)| index)
        }
        
        /// Find first and last occurrence
        pub fn search_first_last<T: PartialEq>(arr: &[T], target: &T) -> (Option<usize>, Option<usize>) {
            let mut first = None;
            let mut last = None;
            
            for (i, item) in arr.iter().enumerate() {
                if item == target {
                    if first.is_none() {
                        first = Some(i);
                    }
                    last = Some(i);
                }
            }
            
            (first, last)
        }
        
        /// Count occurrences
        pub fn count<T: PartialEq>(arr: &[T], target: &T) -> usize {
            arr.iter().filter(|&item| item == target).count()
        }
    }
}

// Usage example
use linear_search::LinearSearch;

fn main() {
    let numbers = vec![1, 3, 5, 3, 7, 3, 9];
    
    // Basic search
    if let Some(index) = LinearSearch::search(&numbers, &5) {
        println!("Found 5 at index: {}", index);
    }
    
    // Search all occurrences
    let all_indices = LinearSearch::search_all(&numbers, &3);
    println!("Found 3 at indices: {:?}", all_indices);
    
    // Search with predicate
    if let Some(index) = LinearSearch::search_by(&numbers, |&x| x > 6) {
        println!("First element > 6 at index: {}", index);
    }
    
    // Count occurrences
    let count = LinearSearch::count(&numbers, &3);
    println!("Number 3 appears {} times", count);
}
```

## Performance Analysis

### Time Complexity Analysis

| Case | Time Complexity | Description |
|------|----------------|-------------|
| Best Case | O(1) | Element is at the first position |
| Average Case | O(n/2) ≈ O(n) | Element is in the middle |
| Worst Case | O(n) | Element is at the last position or not present |

### Space Complexity

- **Space Complexity**: O(1) - Only uses a constant amount of extra space

### Performance Comparison: Python vs Rust

#### Python Performance Test

```python
import time
import random

def benchmark_linear_search():
    sizes = [1000, 10000, 100000]
    
    for size in sizes:
        arr = list(range(size))
        target = size - 1  # Worst case: last element
        
        start_time = time.time()
        result = linear_search_basic(arr, target)
        end_time = time.time()
        
        print(f"Size: {size}, Time: {(end_time - start_time)*1000:.2f}ms")

benchmark_linear_search()
```

#### Rust Performance Test

```rust
use std::time::Instant;

fn benchmark_linear_search() {
    let sizes = vec![1000, 10000, 100000];
    
    for size in sizes {
        let arr: Vec<i32> = (0..size).collect();
        let target = size - 1; // Worst case: last element
        
        let start = Instant::now();
        let _result = linear_search_basic(&arr, &target);
        let duration = start.elapsed();
        
        println!("Size: {}, Time: {:.2?}", size, duration);
    }
}
```

## Variants and Extensions

### 1. Sentinel Linear Search

```python
def sentinel_linear_search(arr, target):
    """
    Linear search with sentinel to eliminate boundary checking.
    """
    if not arr:
        return -1
    
    # Store the last element
    last = arr[-1]
    
    # Set target as sentinel
    arr[-1] = target
    
    i = 0
    while arr[i] != target:
        i += 1
    
    # Restore the last element
    arr[-1] = last
    
    # Check if target was found or if we reached the sentinel
    if i < len(arr) - 1 or last == target:
        return i
    return -1
```

### 2. Jump Search (Optimized Linear Search)

```python
import math

def jump_search(arr, target):
    """
    Jump search: Linear search with jumping steps.
    """
    n = len(arr)
    step = int(math.sqrt(n))
    prev = 0
    
    # Jump through the array
    while arr[min(step, n) - 1] < target:
        prev = step
        step += int(math.sqrt(n))
        if prev >= n:
            return -1
    
    # Linear search in the identified block
    while arr[prev] < target:
        prev += 1
        if prev == min(step, n):
            return -1
    
    if arr[prev] == target:
        return prev
    
    return -1
```

### 3. Linear Search on Strings

```python
def linear_search_substring(text, pattern):
    """
    Find all occurrences of pattern in text using linear search.
    """
    occurrences = []
    text_len = len(text)
    pattern_len = len(pattern)
    
    for i in range(text_len - pattern_len + 1):
        if text[i:i + pattern_len] == pattern:
            occurrences.append(i)
    
    return occurrences

# Example
text = "hello world hello universe hello"
pattern = "hello"
results = linear_search_substring(text, pattern)
print(f"Pattern found at indices: {results}")  # [0, 12, 27]
```

## Best Practices

### When to Use Linear Search

1. **Small datasets** (< 1000 elements)
2. **Unsorted data** where sorting would be more expensive
3. **Single search** operations
4. **Memory-constrained environments**
5. **Simple implementation requirements**

### Python Best Practices

```python
# Use built-in functions when possible
def find_element(arr, target):
    try:
        return arr.index(target)
    except ValueError:
        return -1

# Use generator expressions for memory efficiency
def search_large_dataset(data, target):
    return next((i for i, item in enumerate(data) if item == target), -1)

# Type hints for better code documentation
from typing import List, Optional, TypeVar

T = TypeVar('T')

def linear_search_typed(arr: List[T], target: T) -> Optional[int]:
    """Type-safe linear search implementation."""
    for i, item in enumerate(arr):
        if item == target:
            return i
    return None
```

### Rust Best Practices

```rust
// Use iterators for idiomatic Rust
fn linear_search_idiomatic<T: PartialEq>(slice: &[T], target: &T) -> Option<usize> {
    slice.iter().position(|item| item == target)
}

// Error handling with Result type
#[derive(Debug)]
enum SearchError {
    EmptyArray,
    InvalidIndex,
}

fn linear_search_with_error<T: PartialEq>(
    slice: &[T], 
    target: &T
) -> Result<usize, SearchError> {
    if slice.is_empty() {
        return Err(SearchError::EmptyArray);
    }
    
    slice.iter()
         .position(|item| item == target)
         .ok_or(SearchError::InvalidIndex)
}

// Generic implementation with bounds
fn linear_search_generic<T>(slice: &[T], target: &T) -> Option<usize>
where
    T: PartialEq + std::fmt::Debug,
{
    slice.iter().position(|item| item == target)
}
```

## Conclusion

Linear Search is a fundamental algorithm that, while simple, remains important in computer science and practical programming. Key takeaways:

### Advantages

- Simple to implement and understand
- Works with unsorted data
- Stable and predictable performance
- Low memory overhead
- No preprocessing required

### Disadvantages

- O(n) time complexity - inefficient for large datasets
- Not suitable for frequent searches on the same dataset
- Better alternatives exist for sorted data (Binary Search)

### Language-Specific Insights

**Python:**

- Leverage built-in functions like `list.index()` and `enumerate()`
- Use generators for memory efficiency
- Take advantage of list comprehensions for multiple results

**Rust:**

- Utilize iterator methods like `position()` and `find()`
- Embrace the type system for safe, generic implementations
- Use `Option` types for elegant error handling

Both implementations showcase the power of their respective languages while maintaining the core simplicity that makes linear search an excellent learning algorithm and practical tool for appropriate use cases.

I'll create a detailed ASCII diagram that visually demonstrates how Linear Search works step by step, showing the algorithm's progression through an array.I've created a comprehensive ASCII diagram that visually demonstrates how Linear Search works step by step. The visualization includes:

## Key Features of the Diagram

1. **Step-by-Step Execution**: Shows each comparison operation with detailed boxes showing the current state
2. **Two Scenarios**:
   - Success case (finding target 22 at index 4)
   - Failure case (searching for 99 which doesn't exist)

3. **Visual Elements**:
   - Array representation with indices
   - Current position indicators (↑)
   - Status markers (✓ for found, ✗ for checked and not matched)
   - Progress tracking through the search

4. **Algorithm Flow Chart**: Complete flowchart showing the decision-making process

5. **Memory Layout Visualization**: Shows how the algorithm progresses through memory

6. **Performance Analysis**: Visual representation of best, average, and worst-case scenarios

7. **Summary Box**: Quick reference with key characteristics

## The diagram effectively shows

- How the algorithm starts at index 0
- Sequential checking of each element
- The comparison operation at each step
- What happens when target is found vs. not found
- The linear progression through the array
- Time complexity implications visually

This visual representation makes it easy to understand why it's called "linear" search - you can see the straight-line progression through the array elements, one by one, until the target is found or the array is exhausted.

The ASCII format makes it accessible and easy to include in documentation, code comments, or educational materials!

# Linear Search Algorithm - Step-by-Step ASCII Visualization

## Example: Searching for target value **22** in array [64, 34, 25, 12, 22, 11, 90]

```
INITIAL STATE
=============
Target: 22
Array:  [64] [34] [25] [12] [22] [11] [90]
Index:   0    1    2    3    4    5    6
         ↑
    Current Position
```

---

## STEP 1: Check Index 0

```
┌─────────────────────────────────────────────────────────┐
│                    LINEAR SEARCH - STEP 1               │
│                                                         │
│ Current Index: 0                                        │
│ Current Value: 64                                       │
│ Target Value:  22                                       │
│ Comparison:    64 == 22 ? FALSE                         │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ↑                                               │
│      CHECKING                                           │
│                                                         │
│ Action: Move to next position                           │
└─────────────────────────────────────────────────────────┘
```

---

## STEP 2: Check Index 1

```
┌─────────────────────────────────────────────────────────┐
│                    LINEAR SEARCH - STEP 2               │
│                                                         │
│ Current Index: 1                                        │
│ Current Value: 34                                       │
│ Target Value:  22                                       │
│ Comparison:    34 == 22 ? FALSE                         │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ✗    ↑                                          │
│      DONE  CHECKING                                     │
│                                                         │
│ Action: Move to next position                           │
└─────────────────────────────────────────────────────────┘
```

---

## STEP 3: Check Index 2

```
┌─────────────────────────────────────────────────────────┐
│                    LINEAR SEARCH - STEP 3               │
│                                                         │
│ Current Index: 2                                        │
│ Current Value: 25                                       │
│ Target Value:  22                                       │
│ Comparison:    25 == 22 ? FALSE                         │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ✗    ✗    ↑                                     │
│      DONE  DONE CHECKING                                │
│                                                         │
│ Action: Move to next position                           │
└─────────────────────────────────────────────────────────┘
```

---

## STEP 4: Check Index 3

```
┌─────────────────────────────────────────────────────────┐
│                    LINEAR SEARCH - STEP 4               │
│                                                         │
│ Current Index: 3                                        │
│ Current Value: 12                                       │
│ Target Value:  22                                       │
│ Comparison:    12 == 22 ? FALSE                         │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ✗    ✗    ✗    ↑                                │
│      DONE  DONE  DONE CHECKING                          │
│                                                         │
│ Action: Move to next position                           │
└─────────────────────────────────────────────────────────┘
```

---

## STEP 5: Check Index 4 - TARGET FOUND

```
┌─────────────────────────────────────────────────────────┐
│                    LINEAR SEARCH - STEP 5               │
│                     *** SUCCESS! ***                    │
│                                                         │
│ Current Index: 4                                        │
│ Current Value: 22                                       │
│ Target Value:  22                                       │
│ Comparison:    22 == 22 ? TRUE ✓                        │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ✗    ✗    ✗    ✗    ✓                           │
│      DONE  DONE  DONE  DONE FOUND!                      │
│                                                         │
│ Result: Return index 4                                  │
└─────────────────────────────────────────────────────────┘
```

---

# Alternative Scenario: Target NOT FOUND

## Example: Searching for target value **99** in array [64, 34, 25, 12, 22, 11, 90]

```
PROGRESSION THROUGH ENTIRE ARRAY
================================

Step 1: [64] [34] [25] [12] [22] [11] [90]
         ↑     64 ≠ 99, continue...
         
Step 2: [64] [34] [25] [12] [22] [11] [90]
         ✗    ↑     34 ≠ 99, continue...
         
Step 3: [64] [34] [25] [12] [22] [11] [90]
         ✗    ✗    ↑     25 ≠ 99, continue...
         
Step 4: [64] [34] [25] [12] [22] [11] [90]
         ✗    ✗    ✗    ↑     12 ≠ 99, continue...
         
Step 5: [64] [34] [25] [12] [22] [11] [90]
         ✗    ✗    ✗    ✗    ↑     22 ≠ 99, continue...
         
Step 6: [64] [34] [25] [12] [22] [11] [90]
         ✗    ✗    ✗    ✗    ✗    ↑     11 ≠ 99, continue...
         
Step 7: [64] [34] [25] [12] [22] [11] [90]
         ✗    ✗    ✗    ✗    ✗    ✗    ↑     90 ≠ 99, continue...
```

```
┌─────────────────────────────────────────────────────────┐
│                   SEARCH COMPLETED                      │
│                   *** NOT FOUND ***                     │
│                                                         │
│ Searched entire array without finding target            │
│ Target Value: 99                                        │
│ Elements Checked: 7/7                                   │
│                                                         │
│ Array: [64] [34] [25] [12] [22] [11] [90]              │
│         ✗    ✗    ✗    ✗    ✗    ✗    ✗                │
│      NONE  NONE  NONE  NONE  NONE  NONE  NONE           │
│                                                         │
│ Result: Return -1 (NOT FOUND)                          │
└─────────────────────────────────────────────────────────┘
```

---

# Detailed Algorithm Flow Chart

```
                    START LINEAR SEARCH
                           │
                           ▼
                  ┌─────────────────┐
                  │ Initialize:     │
                  │ index = 0       │
                  │ target = value  │
                  │ array = data    │
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ index < length? │◄─────┐
                  └─────────────────┘      │
                           │               │
                       YES │               │ NO
                           ▼               │
                  ┌─────────────────┐      │
                  │ array[index]    │      │
                  │ == target?      │      │
                  └─────────────────┘      │
                           │               │
                       YES │               │ NO
                           ▼               │
                  ┌─────────────────┐      │
                  │ FOUND!          │      │
                  │ Return index    │      │
                  └─────────────────┘      │
                           │               │
                           ▼               │
                      ┌────────┐           │
                      │  END   │           │
                      └────────┘           │
                                          │
          ┌───────────────────────────────┘
          │
          ▼
  ┌─────────────────┐
  │ index = index+1 │
  └─────────────────┘
          │
          └─────────────────┐
                           ▼
                  ┌─────────────────┐
                  │ NOT FOUND       │
                  │ Return -1       │
                  └─────────────────┘
                           │
                           ▼
                      ┌────────┐
                      │  END   │
                      └────────┘
```

---

# Memory Layout Visualization

```
MEMORY REPRESENTATION
=====================

Array in Memory:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ 64  │ 34  │ 25  │ 12  │ 22  │ 11  │ 90  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
  ↑     ↑     ↑     ↑     ↑     ↑     ↑
  0     1     2     3     4     5     6    ← Indices

Search Process:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  ❌  │     │     │     │     │     │     │ Step 1: Check 64
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  ❌  │  ❌  │     │     │     │     │     │ Step 2: Check 34
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  ❌  │  ❌  │  ❌  │     │     │     │     │ Step 3: Check 25
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  ❌  │  ❌  │  ❌  │  ❌  │     │     │     │ Step 4: Check 12
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  ❌  │  ❌  │  ❌  │  ❌  │  ✅  │     │     │ Step 5: Found 22!
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

---

# Performance Analysis Visualization

```
BEST CASE: O(1) - Target at first position
═══════════════════════════════════════════
[TARGET] [  ?  ] [  ?  ] [  ?  ] [  ?  ]
    ↑
  FOUND IN 1 COMPARISON

AVERAGE CASE: O(n/2) - Target in middle
═══════════════════════════════════════
[  ✗  ] [  ✗  ] [TARGET] [  ?  ] [  ?  ]
   1       2       3     Found in 3 comparisons

WORST CASE: O(n) - Target at last position or not found
═══════════════════════════════════════════════════════
[  ✗  ] [  ✗  ] [  ✗  ] [  ✗  ] [TARGET]
   1       2       3       4       5     Found in n comparisons

NOT FOUND: O(n) - Must check entire array
═══════════════════════════════════════════
[  ✗  ] [  ✗  ] [  ✗  ] [  ✗  ] [  ✗  ]
   1       2       3       4       5     All n elements checked
```

---

# Summary

```
╔══════════════════════════════════════════════════════════════╗
║                    LINEAR SEARCH SUMMARY                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ Algorithm: Sequential search through array                   ║
║ Method:    Compare each element with target                  ║
║                                                              ║
║ Time Complexity:                                             ║
║   • Best Case:    O(1)   - Found immediately                ║
║   • Average Case: O(n/2) - Found in middle                  ║
║   • Worst Case:   O(n)   - Found at end or not found        ║
║                                                              ║
║ Space Complexity: O(1)   - No additional space needed       ║
║                                                              ║
║ Characteristics:                                             ║
║   ✓ Simple implementation                                    ║
║   ✓ Works on unsorted data                                   ║
║   ✓ Stable algorithm                                         ║
║   ✗ Inefficient for large datasets                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```
