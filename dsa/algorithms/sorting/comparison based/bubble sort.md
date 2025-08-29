# Bubble Sort Complexity Analysis

## 1. Bubble Sort

### Python Implementation

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
print(f"Original: {numbers}")
print(f"Sorted: {bubble_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn bubble_sort<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    for i in 0..len {
        for j in 0..(len - i - 1) {
            if arr[j] > arr[j + 1] {
                arr.swap(j, j + 1);
            }
        }
    }
}

// Example usage
fn main() {
    let mut numbers = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original: {:?}", numbers);
    bubble_sort(&mut numbers);
    println!("Sorted: {:?}", numbers);
}
```

Bubble sort is a simple comparison-based sorting algorithm that repeatedly steps through the list, compares adjacent elements, and swaps them if they are in the wrong order. The implementations provided in Python and Rust are equivalent in terms of algorithmic behavior: both perform nested loops over the array, making pairwise comparisons and swaps without any optimizations like early termination (e.g., a flag to stop if no swaps occur in a pass). This affects the time complexity across cases.

Below is a summary of the complexities. Note that time complexity refers to the number of comparisons and swaps (dominant operations), and space complexity accounts for auxiliary space used beyond the input array.

Here's the complexity analysis for the bubble sort implementations you provided:

## Time Complexity

### **Best Case: O(n)**

- Occurs when the array is already sorted
- With an optimization (early termination when no swaps occur), bubble sort can detect this in one pass
- Note: Your current implementations don't include this optimization, so they would still be O(n²) even for sorted arrays

### **Average Case: O(n²)**

- On average, elements need to "bubble" through about half the array
- Still requires nested loops with quadratic comparisons (Quadratic comparisons means that the number of comparisons made by the algorithm grows proportionally to the square of the input size, or O(n²). For bubble sort, if you have n elements, it compares pairs of elements about n × n times (specifically, about n(n-1)/2 times in the worst case). This is called "quadratic" because the dominant term is n². So, as the input size doubles, the number of comparisons increases by about four times.)

### **Worst Case: O(n²)**

- Occurs when the array is sorted in reverse order
- Every element must be compared with every other element
- Maximum number of swaps needed

## Space Complexity

### **O(1) - Constant Space**

- Bubble sort is an in-place sorting algorithm
- Only uses a constant amount of extra memory for temporary variables (like loop counters)
- The input array is sorted in place without requiring additional storage proportional to input size

## Stability

### **Stable: Yes**

- Bubble sort maintains the relative order of equal elements
- When `arr[j] > arr[j + 1]`, it only swaps if the left element is strictly greater
- Equal elements are never swapped, preserving their original relative positions

## Summary Table

| Metric            | Complexity/Property |
|--------           |-------------------  |
| Best Case Time    | O(n)*               |
| Average Case Time | O(n²)               |
| Worst Case Time   | O(n²)               |
| Space Complexity  | O(1)                |
| Stable            | Yes                 |

*Note: O(n) best case requires an optimization to detect when no swaps occur in a complete pass, allowing early termination. Your current implementations would be O(n²) even for sorted arrays.

## Optimization Note

To achieve O(n) best case, you could add a flag to track if any swaps occurred:

```python
def optimized_bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:  # No swaps means array is sorted
            break
    return arr
```

## 12. **Bubble Sort Classification**

Based on the above categories, **Bubble Sort** is:

- ✅ **Ascending/Descending**: Can do both
- ✅ **In-Place**: O(1) extra space
- ✅ **Stable**: Maintains relative order of equal elements
- ✅ **Comparison-Based**: Uses element comparisons
- ✅ **Adaptive**: Can be optimized for partially sorted data
- ✅ **Exchange-Based**: Works by swapping adjacent elements
- ✅ **Online**: Can work as data arrives
- ✅ **Internal**: Works in main memory
- ✅ **Iterative**: Uses nested loops
- ✅ **Sequential**: Single-threaded
- ✅ **Array-Based**: Works on arrays/lists

# Comprehensive Bubble Sort Implementations

## 1. Basic Bubble Sort (Ascending)

```python
def bubble_sort_basic(arr):
    """
    Basic bubble sort implementation - ascending order
    Time: O(n²), Space: O(1)
    """
    n = len(arr)
    
    # Traverse through all array elements
    for i in range(n):
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            # Swap if the element found is greater than the next element
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
print("Original:", arr)
sorted_arr = bubble_sort_basic(arr.copy())
print("Sorted (Ascending):", sorted_arr)
```

## 2. Descending Order Bubble Sort

```python
def bubble_sort_descending(arr):
    """
    Bubble sort for descending order
    """
    n = len(arr)
    
    for i in range(n):
        for j in range(0, n - i - 1):
            # Change comparison for descending order
            if arr[j] < arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr

# Example usage
arr = [64, 34, 25, 12, 22, 11, 90]
print("Sorted (Descending):", bubble_sort_descending(arr.copy()))
```

## 3. Optimized Adaptive Bubble Sort

```python
def bubble_sort_optimized(arr):
    """
    Optimized bubble sort - stops early if array becomes sorted
    Best case: O(n) for already sorted arrays
    """
    n = len(arr)
    
    for i in range(n):
        swapped = False  # Flag to detect if any swap occurred
        
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        # If no swapping occurred, array is sorted
        if not swapped:
            break
    
    return arr

# Example with partially sorted array
partially_sorted = [1, 2, 3, 5, 4, 6, 7, 8]
print("Partially sorted:", partially_sorted)
print("Optimized sort:", bubble_sort_optimized(partially_sorted.copy()))
```

## 4. Stable Bubble Sort with Custom Objects

```python
class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
    
    def __repr__(self):
        return f"Student('{self.name}', {self.grade})"

def bubble_sort_stable(arr, key_func):
    """
    Stable bubble sort for custom objects
    Maintains relative order of equal elements
    """
    n = len(arr)
    
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            # Use <= to maintain stability (don't swap equal elements)
            if key_func(arr[j]) > key_func(arr[j + 1]):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        if not swapped:
            break
    
    return arr

# Example demonstrating stability
students = [
    Student("Alice", 85),
    Student("Bob", 90),
    Student("Charlie", 85),  # Same grade as Alice
    Student("Diana", 92),
    Student("Eve", 85)       # Same grade as Alice and Charlie
]

print("Original order:")
for student in students:
    print(f"  {student}")

sorted_students = bubble_sort_stable(students.copy(), lambda s: s.grade)
print("\nSorted by grade (stable - maintains original order for equal grades):")
for student in sorted_students:
    print(f"  {student}")
```

## 5. Generic Bubble Sort with Custom Comparator

```python
def bubble_sort_generic(arr, compare_func=None, reverse=False):
    """
    Generic bubble sort with custom comparison function
    """
    if compare_func is None:
        compare_func = lambda a, b: a > b
    
    n = len(arr)
    
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            # Apply comparison based on parameters
            should_swap = compare_func(arr[j], arr[j + 1])
            if reverse:
                should_swap = not should_swap
            
            if should_swap:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        
        if not swapped:
            break
    
    return arr

# Examples
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
print("Numbers ascending:", bubble_sort_generic(numbers.copy()))
print("Numbers descending:", bubble_sort_generic(numbers.copy(), reverse=True))

# Sort strings by length
words = ["hello", "a", "world", "python", "bubble", "sort"]
print("Words by length:", bubble_sort_generic(words.copy(), lambda a, b: len(a) > len(b)))
```

## 6. Online Bubble Sort (Processing Data as it Arrives)

```python
class OnlineBubbleSort:
    """
    Online bubble sort - processes elements as they arrive
    Maintains a sorted array that can accept new elements
    """
    def __init__(self):
        self.data = []
    
    def add_element(self, element):
        """Add a new element and maintain sorted order"""
        self.data.append(element)
        
        # Bubble the new element to its correct position
        i = len(self.data) - 1
        while i > 0 and self.data[i] < self.data[i - 1]:
            self.data[i], self.data[i - 1] = self.data[i - 1], self.data[i]
            i -= 1
    
    def get_sorted_data(self):
        """Return the current sorted array"""
        return self.data.copy()
    
    def sort_existing(self):
        """Apply full bubble sort to existing data"""
        bubble_sort_optimized(self.data)

# Example of online sorting
online_sorter = OnlineBubbleSort()
stream_data = [5, 2, 8, 1, 9, 3, 7, 4, 6]

print("Online Bubble Sort - Processing stream:")
for element in stream_data:
    online_sorter.add_element(element)
    print(f"Added {element}: {online_sorter.get_sorted_data()}")
```

## 7. In-Place Verification and Space Complexity Demo

```python
import sys

def bubble_sort_in_place_demo(arr):
    """
    Demonstrates in-place sorting with space complexity tracking
    """
    original_id = id(arr)  # Track original array object
    n = len(arr)
    comparisons = 0
    swaps = 0
    
    print(f"Original array ID: {original_id}")
    print(f"Array before sorting: {arr}")
    
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            comparisons += 1
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swaps += 1
                swapped = True
        
        if not swapped:
            break
    
    print(f"Array after sorting: {arr}")
    print(f"Final array ID: {id(arr)} (same object: {id(arr) == original_id})")
    print(f"Comparisons: {comparisons}, Swaps: {swaps}")
    print(f"Extra space used: O(1) - only variables i, j, swapped, etc.")
    
    return arr

# Demonstrate in-place sorting
test_array = [64, 34, 25, 12, 22, 11, 90]
bubble_sort_in_place_demo(test_array)
```

## 8. Iterative vs Recursive Implementations

```python
def bubble_sort_recursive(arr, n=None):
    """
    Recursive implementation of bubble sort
    Less common but demonstrates the concept
    """
    if n is None:
        n = len(arr)
    
    # Base case: if array has 1 or 0 elements
    if n <= 1:
        return arr
    
    # One pass of bubble sort
    swapped = False
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
            swapped = True
    
    # If no swapping occurred, array is sorted
    if not swapped:
        return arr
    
    # Recursively sort the remaining unsorted portion
    return bubble_sort_recursive(arr, n - 1)

# Compare iterative vs recursive
arr1 = [64, 34, 25, 12, 22, 11, 90]
arr2 = arr1.copy()

print("Iterative result:", bubble_sort_optimized(arr1))
print("Recursive result:", bubble_sort_recursive(arr2))
```

## 9. Performance Analysis and Benchmarking

```python
import time
import random

def benchmark_bubble_sort():
    """
    Benchmark different bubble sort implementations
    """
    sizes = [100, 500, 1000]
    implementations = {
        'Basic': bubble_sort_basic,
        'Optimized': bubble_sort_optimized,
        'Recursive': bubble_sort_recursive
    }
    
    print("Bubble Sort Performance Benchmark")
    print("=" * 50)
    
    for size in sizes:
        print(f"\nArray Size: {size}")
        
        # Generate test data
        random_data = [random.randint(1, 1000) for _ in range(size)]
        sorted_data = sorted(random_data)
        reverse_data = sorted(random_data, reverse=True)
        
        test_cases = {
            'Random': random_data,
            'Already Sorted': sorted_data,
            'Reverse Sorted': reverse_data
        }
        
        for case_name, test_data in test_cases.items():
            print(f"\n  {case_name} Data:")
            
            for impl_name, impl_func in implementations.items():
                data_copy = test_data.copy()
                start_time = time.time()
                impl_func(data_copy)
                end_time = time.time()
                
                print(f"    {impl_name}: {end_time - start_time:.4f} seconds")

# Run benchmark (uncomment to execute)
# benchmark_bubble_sort()
```

## 10. Complete Feature Demo

```python
def bubble_sort_complete(arr, ascending=True, stable=True, adaptive=True):
    """
    Complete bubble sort implementation with all features
    
    Parameters:
    - arr: array to sort
    - ascending: True for ascending, False for descending
    - stable: maintain relative order of equal elements
    - adaptive: optimize for partially sorted data
    """
    if not arr:
        return arr
    
    n = len(arr)
    comparisons = 0
    swaps = 0
    passes = 0
    
    for i in range(n):
        passes += 1
        swapped = False
        
        for j in range(0, n - i - 1):
            comparisons += 1
            
            # Determine if we should swap based on sort order
            should_swap = (arr[j] > arr[j + 1]) if ascending else (arr[j] < arr[j + 1])
            
            # For stability, use > (not >=) to avoid swapping equal elements
            if should_swap:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swaps += 1
                swapped = True
        
        # Adaptive optimization: stop if no swaps occurred
        if adaptive and not swapped:
            break
    
    return {
        'sorted_array': arr,
        'statistics': {
            'comparisons': comparisons,
            'swaps': swaps,
            'passes': passes,
            'early_termination': passes < n
        }
    }

# Comprehensive test
test_data = [64, 34, 25, 12, 22, 11, 90, 25]  # Note: duplicate 25 for stability test
print("Original array:", test_data)

# Test all features
result = bubble_sort_complete(test_data.copy(), ascending=True, adaptive=True)
print("Ascending sort:", result['sorted_array'])
print("Statistics:", result['statistics'])

result = bubble_sort_complete(test_data.copy(), ascending=False, adaptive=True)
print("Descending sort:", result['sorted_array'])
print("Statistics:", result['statistics'])
```

## Key Characteristics Demonstrated

1. **✅ Ascending/Descending**: Multiple implementations for both orders
2. **✅ In-Place**: All implementations use O(1) extra space
3. **✅ Stable**: Maintains relative order of equal elements
4. **✅ Comparison-Based**: Uses element comparisons throughout
5. **✅ Adaptive**: Optimized versions perform better on partially sorted data
6. **✅ Exchange-Based**: All implementations work by swapping adjacent elements
7. **✅ Online**: Demonstrates processing data as it arrives
8. **✅ Internal**: All implementations work in main memory
9. **✅ Iterative**: Primary implementations use nested loops
10. **✅ Sequential**: Single-threaded implementations
11. **✅ Array-Based**: Works on arrays and lists

## Complexity Analysis

- **Time Complexity**:
  - Worst/Average: O(n²)
  - Best (optimized): O(n) for nearly sorted data
- **Space Complexity**: O(1) - truly in-place
- **Stability**: Yes - equal elements maintain their relative order
- **Adaptivity**: Yes - performs better on partially sorted data when optimized

I'll provide comprehensive code implementations of Bubble Sort covering all the characteristics you mentioned.I've provided a comprehensive collection of Bubble Sort implementations that demonstrate all the characteristics you mentioned. Here's what's included:

**Core Implementations:**

- Basic ascending/descending bubble sort
- Optimized adaptive version (early termination)
- Stable sorting with custom objects
- Generic version with custom comparators

**Advanced Features:**

- Online bubble sort (processes streaming data)
- In-place verification with memory tracking
- Recursive implementation (for comparison)
- Performance benchmarking tools
- Complete feature-rich implementation

**Key Highlights:**

- **In-Place**: All versions use O(1) extra space, modifying the original array
- **Stable**: Maintains relative order of equal elements using `>` instead of `>=`
- **Adaptive**: Optimized versions detect when array becomes sorted and terminate early
- **Online**: Demonstrates processing elements as they arrive in a data stream
- **Flexible**: Supports both ascending/descending order with custom comparison functions

The code includes detailed examples, performance analysis, and demonstrates how Bubble Sort maintains all the characteristics you listed while being practical for educational purposes and small datasets.

## Bubble Sort - How It Works (ASCII Diagrams)

## Overview: The "Bubbling" Effect

```ascii
Large elements "bubble up" to the right like air bubbles rising in water
Small elements "sink down" to the left

[64] [34] [25] [12] [22] [11] [90]
 ↑                               ↑
heavy                          light
(sinks)                     (bubbles up)
```

## Complete Step-by-Step Example

### Initial Array: [64, 34, 25, 12, 22, 11, 90]

```ascii
Pass 1: Bubble the largest element to the end
========================================

Step 1: Compare 64 and 34
[64] [34] [25] [12] [22] [11] [90]
  ↑    ↑
64 > 34? YES → SWAP

[34] [64] [25] [12] [22] [11] [90]
      ↓    ↓
     swapped

Step 2: Compare 64 and 25
[34] [64] [25] [12] [22] [11] [90]
      ↑    ↑
64 > 25? YES → SWAP

[34] [25] [64] [12] [22] [11] [90]
           ↓    ↓
          swapped

Step 3: Compare 64 and 12
[34] [25] [64] [12] [22] [11] [90]
           ↑    ↑
64 > 12? YES → SWAP

[34] [25] [12] [64] [22] [11] [90]
                ↓    ↓
               swapped

Step 4: Compare 64 and 22
[34] [25] [12] [64] [22] [11] [90]
                ↑    ↑
64 > 22? YES → SWAP

[34] [25] [12] [22] [64] [11] [90]
                     ↓    ↓
                    swapped

Step 5: Compare 64 and 11
[34] [25] [12] [22] [64] [11] [90]
                     ↑    ↑
64 > 11? YES → SWAP

[34] [25] [12] [22] [11] [64] [90]
                          ↓    ↓
                         swapped

Step 6: Compare 64 and 90
[34] [25] [12] [22] [11] [64] [90]
                          ↑    ↑
64 > 90? NO → NO SWAP

Result after Pass 1:
[34] [25] [12] [22] [11] [64] [90]
                               ↑
                          largest element
                         is now in place
```

```ascii
Pass 2: Bubble the second largest to its position
================================================

[34] [25] [12] [22] [11] [64] [90]
 ↑    ↑                     │    │
                      already sorted

Step 1: 34 > 25? YES → SWAP
[25] [34] [12] [22] [11] [64] [90]

Step 2: 34 > 12? YES → SWAP
[25] [12] [34] [22] [11] [64] [90]

Step 3: 34 > 22? YES → SWAP
[25] [12] [22] [34] [11] [64] [90]

Step 4: 34 > 11? YES → SWAP
[25] [12] [22] [11] [34] [64] [90]

Step 5: 34 > 64? NO → NO SWAP
[25] [12] [22] [11] [34] [64] [90]
                     ↑    │    │
              second largest  │    │
                 in place  sorted region
```

```ascii
Pass 3: Continue the process
===========================

[25] [12] [22] [11] [34] [64] [90]
 ↑    ↑              │    │    │
                  sorted region

Step 1: 25 > 12? YES → SWAP
[12] [25] [22] [11] [34] [64] [90]

Step 2: 25 > 22? YES → SWAP
[12] [22] [25] [11] [34] [64] [90]

Step 3: 25 > 11? YES → SWAP
[12] [22] [11] [25] [34] [64] [90]

Step 4: 25 > 34? NO → NO SWAP
[12] [22] [11] [25] [34] [64] [90]
                 ↑    │    │    │
            third largest  │    │    │
               in place  sorted region
```

```ascii
Pass 4: Getting closer to completion
===================================

[12] [22] [11] [25] [34] [64] [90]
 ↑    ↑         │    │    │    │
              sorted region

Step 1: 12 > 22? NO → NO SWAP
[12] [22] [11] [25] [34] [64] [90]

Step 2: 22 > 11? YES → SWAP
[12] [11] [22] [25] [34] [64] [90]

Step 3: 22 > 25? NO → NO SWAP
[12] [11] [22] [25] [34] [64] [90]
           ↑    │    │    │    │
      fourth largest  │    │    │
         in place  sorted region
```

```ascii
Pass 5: Almost done
==================

[12] [11] [22] [25] [34] [64] [90]
 ↑    ↑    │    │    │    │    │
        sorted region

Step 1: 12 > 11? YES → SWAP
[11] [12] [22] [25] [34] [64] [90]

Step 2: 12 > 22? NO → NO SWAP
[11] [12] [22] [25] [34] [64] [90]
      ↑    │    │    │    │    │
 fifth largest  │    │    │    │
    in place  sorted region
```

```ascii
Pass 6: Final check (optional with optimization)
===============================================

[11] [12] [22] [25] [34] [64] [90]
 ↑    │    │    │    │    │    │
   sorted region (all elements)

Step 1: 11 > 12? NO → NO SWAP
[11] [12] [22] [25] [34] [64] [90]

No swaps occurred → Array is fully sorted!
Early termination possible with optimization.
```

## Visual Representation of Each Pass

```ascii
Original:  [64] [34] [25] [12] [22] [11] [90]

Pass 1:    [34] [25] [12] [22] [11] [64] [90] ← 90 bubbled to end
            └─────── unsorted ───────┘  └─sorted─┘

Pass 2:    [25] [12] [22] [11] [34] [64] [90] ← 64 bubbled to position
            └───── unsorted ─────┘  └──sorted───┘

Pass 3:    [12] [22] [11] [25] [34] [64] [90] ← 34 bubbled to position
            └── unsorted ──┘  └─────sorted─────┘

Pass 4:    [12] [11] [22] [25] [34] [64] [90] ← 25 bubbled to position
            └unsorted┘  └────────sorted────────┘

Pass 5:    [11] [12] [22] [25] [34] [64] [90] ← 22 bubbled to position
            └─┘  └─────────sorted──────────────┘

Pass 6:    [11] [12] [22] [25] [34] [64] [90] ← All sorted!
            └──────────all sorted──────────────┘
```

## Comparison and Swap Pattern

```ascii
Adjacent Element Comparison Pattern:
====================================

For array of size n, we compare adjacent pairs:

Pass 1: (n-1) comparisons
[0,1] [1,2] [2,3] [3,4] [4,5] [5,6]
  ↑     ↑     ↑     ↑     ↑     ↑
  6 comparisons for 7 elements

Pass 2: (n-2) comparisons  
[0,1] [1,2] [2,3] [3,4] [4,5] [X,X]
  ↑     ↑     ↑     ↑     ↑    skip
  5 comparisons (last element already sorted)

Pass 3: (n-3) comparisons
[0,1] [1,2] [2,3] [3,4] [X,X] [X,X]
  ↑     ↑     ↑     ↑    skip  skip
  4 comparisons

...and so on until 1 comparison
```

## Swap Mechanism Visualization

```ascii
Before Swap:           After Swap:
============           ===========

arr[j] = 64            arr[j] = 34
arr[j+1] = 34          arr[j+1] = 64

Memory View:
[...] [64] [34] [...] → [...] [34] [64] [...]
       ↑    ↑                  ↑    ↑
      j   j+1                 j   j+1
      
Temporary Variable Method:
1. temp = arr[j]     (temp = 64)
2. arr[j] = arr[j+1] (arr[j] = 34)  
3. arr[j+1] = temp   (arr[j+1] = 64)

Python Tuple Method:
arr[j], arr[j+1] = arr[j+1], arr[j]
```

## Optimization: Early Termination

```ascii
Without Optimization:
====================
Always performs n-1 passes regardless of whether array is sorted

Pass 1: [5][4][3][2][1] → [4][3][2][1][5] ✓ (swaps occurred)
Pass 2: [4][3][2][1][5] → [3][2][1][4][5] ✓ (swaps occurred)  
Pass 3: [3][2][1][4][5] → [2][1][3][4][5] ✓ (swaps occurred)
Pass 4: [2][1][3][4][5] → [1][2][3][4][5] ✓ (swaps occurred)
Pass 5: [1][2][3][4][5] → [1][2][3][4][5] ✗ (no swaps needed!)

With Optimization:
=================
Stops when no swaps occur in a pass

Pass 1: [5][4][3][2][1] → [4][3][2][1][5] ✓ (swapped = true)
Pass 2: [4][3][2][1][5] → [3][2][1][4][5] ✓ (swapped = true)
Pass 3: [3][2][1][4][5] → [2][1][3][4][5] ✓ (swapped = true)  
Pass 4: [2][1][3][4][5] → [1][2][3][4][5] ✓ (swapped = true)
Pass 5: [1][2][3][4][5] → [1][2][3][4][5] ✗ (swapped = false)
                                             STOP! Array is sorted.
```

## Best vs Worst Case Scenarios

```ascii
Best Case - Already Sorted Array:
=================================
Input: [1] [2] [3] [4] [5]

Pass 1: Compare all adjacent pairs, no swaps needed
[1]<[2] ✓  [2]<[3] ✓  [3]<[4] ✓  [4]<[5] ✓

Result: [1] [2] [3] [4] [5] (no changes)
Swapped = false → STOP after 1 pass!
Time Complexity: O(n)

Worst Case - Reverse Sorted Array:
=================================
Input: [5] [4] [3] [2] [1]

Every comparison results in a swap:
Pass 1: [4] [3] [2] [1] [5] (4 swaps)
Pass 2: [3] [2] [1] [4] [5] (3 swaps)  
Pass 3: [2] [1] [3] [4] [5] (2 swaps)
Pass 4: [1] [2] [3] [4] [5] (1 swap)
Pass 5: [1] [2] [3] [4] [5] (0 swaps)

Total: 4+3+2+1 = 10 swaps = n(n-1)/2
Time Complexity: O(n²)
```

## Memory Usage Visualization

```ascii
Stack Memory Layout:
===================

Function bubble_sort(arr):
┌─────────────────────────┐
│ Local Variables:        │
│ ├─ n = 7                │ ← O(1) space
│ ├─ i = 0,1,2...         │ ← O(1) space  
│ ├─ j = 0,1,2...         │ ← O(1) space
│ └─ swapped = true/false │ ← O(1) space
└─────────────────────────┘

Heap Memory (Array):
===================
┌──┬──┬──┬──┬──┬──┬──┐
│64│34│25│12│22│11│90│ ← Original array modified in-place
└──┴──┴──┴──┴──┴──┴──┘
 ↑                   
 Same memory location throughout sorting

Total Space: O(1) auxiliary space + O(n) input space
```

I've created comprehensive ASCII diagrams showing exactly how Bubble Sort works! The diagrams cover:

**Key Visualizations:**

- **Complete step-by-step trace** of sorting [64, 34, 25, 12, 22, 11, 90]
- **Pass-by-pass progression** showing how elements "bubble" to their positions
- **Comparison and swap patterns** with memory visualization
- **Optimization techniques** (early termination)
- **Best vs worst case scenarios** with complexity analysis
- **Memory usage layout** showing O(1) space complexity

**Main Concepts Illustrated:**

1. **"Bubbling" effect** - large elements rise to the right like bubbles
2. **Adjacent comparisons** - only neighboring elements are compared
3. **In-place swapping** - elements exchange positions in the same array
4. **Sorted region growth** - the right side becomes sorted after each pass
5. **Early termination** - stops when no swaps occur in a pass

The diagrams show why it's called "Bubble Sort" - you can visually see how the largest elements bubble up to their final positions, just like air bubbles rising through water!

## 12. **By Practical Usage**

**Educational/Theoretical**

- Bubble Sort, Selection Sort (simple to understand)

**Production/Industrial**

- Quick Sort, Merge Sort, Tim Sort (efficient for real applications)

**Specialized**

- Counting Sort (for limited range integers)
- Radix Sort (for fixed-width data)

This comprehensive classification helps understand where bubble sort fits in the broader landscape of sorting algorithms and why it's primarily used for educational purposes rather than production systems.
