I'll create a comprehensive guide to digit-wise sorting algorithms with complete implementations in both Python and Rust. This will cover the main algorithms like Radix Sort, Counting Sort, and Bucket Sort.I've created a comprehensive guide to digit-wise sorting algorithms with complete implementations in both Python and Rust. The guide covers:

## Key Features:

1. **Three Major Algorithms**:
   - **Radix Sort**: Processes digits from least to most significant, handles both integers and strings
   - **Counting Sort**: Perfect for small ranges of values, often used as a subroutine
   - **Bucket Sort**: Distributes elements into buckets, great for uniformly distributed data

2. **Complete Implementations**:
   - **Python**: Includes basic versions, enhanced versions for strings, stable variants, and generic versions
   - **Rust**: Memory-safe implementations with generic programming features and proper error handling

3. **Advanced Features**:
   - Negative number handling in radix sort
   - String sorting capabilities
   - Stable sorting variants
   - Generic implementations for custom data types
   - Object sorting with key functions

4. **Practical Guidance**:
   - Performance analysis with time/space complexity
   - When to use each algorithm
   - Real-world usage scenarios
   - Cache performance considerations

## Highlights:

- **Radix Sort**: O(d×n) time complexity, great for fixed-width integers and strings
- **Counting Sort**: O(n + k) time complexity, perfect when the range of values is small
- **Bucket Sort**: O(n + k) average case, excellent for uniformly distributed floating-point numbers

The implementations include error handling, support for edge cases, and are optimized for real-world usage. Each algorithm includes both basic and advanced versions to suit different needs.

Would you like me to expand on any particular algorithm or add additional features like parallel processing implementations?

# Comprehensive Guide to Digit-Wise Sorting Algorithms

## Table of Contents
1. [Introduction](#introduction)
2. [Radix Sort](#radix-sort)
3. [Counting Sort](#counting-sort)
4. [Bucket Sort](#bucket-sort)
5. [Performance Analysis](#performance-analysis)
6. [When to Use Each Algorithm](#when-to-use-each-algorithm)

## Introduction

Digit-wise sorting algorithms are non-comparative sorting algorithms that sort data by processing individual digits or characters. Unlike comparison-based algorithms (like quicksort or mergesort), these algorithms can achieve linear time complexity under certain conditions.

**Key Characteristics:**
- **Time Complexity**: Often O(d × n) where d is the number of digits and n is the number of elements
- **Space Complexity**: Usually O(n + k) where k is the range of possible values
- **Stability**: Most digit-wise sorts are stable (maintain relative order of equal elements)
- **Best Use Cases**: Integers, strings, or data with limited range of values

## Radix Sort

Radix Sort processes digits from least significant to most significant (LSD) or vice versa (MSD). It uses a stable sorting algorithm (typically counting sort) as a subroutine.

### Python Implementation

```python
def radix_sort(arr):
    """
    Radix sort implementation for non-negative integers.
    
    Time Complexity: O(d × (n + k)) where d is number of digits,
                     n is number of elements, k is range of digits (10)
    Space Complexity: O(n + k)
    """
    if not arr:
        return arr
    
    # Handle negative numbers by separating them
    negative = []
    positive = []
    
    for num in arr:
        if num < 0:
            negative.append(-num)  # Convert to positive for processing
        else:
            positive.append(num)
    
    # Sort positive numbers
    positive = _radix_sort_positive(positive)
    
    # Sort negative numbers and convert back
    if negative:
        negative = _radix_sort_positive(negative)
        negative = [-num for num in reversed(negative)]
    
    return negative + positive

def _radix_sort_positive(arr):
    """Helper function to sort positive integers using radix sort."""
    if not arr:
        return arr
    
    # Find the maximum number to know number of digits
    max_num = max(arr)
    
    # Do counting sort for every digit
    exp = 1
    while max_num // exp > 0:
        arr = _counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr

def _counting_sort_by_digit(arr, exp):
    """Counting sort based on the digit represented by exp."""
    n = len(arr)
    output = [0] * n
    count = [0] * 10  # Count array for digits 0-9
    
    # Store count of occurrences of each digit
    for num in arr:
        digit = (num // exp) % 10
        count[digit] += 1
    
    # Change count[i] so it contains actual position of digit in output
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    # Build output array (process from right to left to maintain stability)
    for i in range(n - 1, -1, -1):
        digit = (arr[i] // exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit] -= 1
    
    return output

# Enhanced version with string support
def radix_sort_strings(strings, max_length=None):
    """
    Radix sort for strings of equal length.
    
    Args:
        strings: List of strings to sort
        max_length: Maximum length of strings (if None, calculated automatically)
    
    Returns:
        Sorted list of strings
    """
    if not strings:
        return strings
    
    if max_length is None:
        max_length = max(len(s) for s in strings)
    
    # Pad strings to equal length
    padded_strings = [s.ljust(max_length) for s in strings]
    
    # Sort from rightmost character to leftmost
    for pos in range(max_length - 1, -1, -1):
        padded_strings = _counting_sort_strings_by_position(padded_strings, pos)
    
    # Remove padding
    return [s.rstrip() for s in padded_strings]

def _counting_sort_strings_by_position(strings, pos):
    """Counting sort for strings based on character at given position."""
    count = [0] * 256  # ASCII characters
    output = [''] * len(strings)
    
    # Count occurrences
    for s in strings:
        char_code = ord(s[pos]) if pos < len(s) else 0
        count[char_code] += 1
    
    # Calculate positions
    for i in range(1, 256):
        count[i] += count[i - 1]
    
    # Build output array
    for i in range(len(strings) - 1, -1, -1):
        char_code = ord(strings[i][pos]) if pos < len(strings[i]) else 0
        output[count[char_code] - 1] = strings[i]
        count[char_code] -= 1
    
    return output
```

### Rust Implementation

```rust
pub fn radix_sort(mut arr: Vec<i32>) -> Vec<i32> {
    if arr.is_empty() {
        return arr;
    }
    
    // Separate negative and positive numbers
    let mut negative: Vec<u32> = Vec::new();
    let mut positive: Vec<u32> = Vec::new();
    
    for num in arr {
        if num < 0 {
            negative.push((-num) as u32);
        } else {
            positive.push(num as u32);
        }
    }
    
    // Sort positive numbers
    positive = radix_sort_positive(positive);
    
    // Sort negative numbers and convert back
    if !negative.is_empty() {
        negative = radix_sort_positive(negative);
        negative.reverse();
    }
    
    // Combine results
    let mut result = Vec::new();
    for num in negative {
        result.push(-(num as i32));
    }
    for num in positive {
        result.push(num as i32);
    }
    
    result
}

fn radix_sort_positive(mut arr: Vec<u32>) -> Vec<u32> {
    if arr.is_empty() {
        return arr;
    }
    
    // Find maximum number to determine number of digits
    let max_num = *arr.iter().max().unwrap();
    
    // Do counting sort for every digit
    let mut exp = 1;
    while max_num / exp > 0 {
        arr = counting_sort_by_digit(arr, exp);
        exp *= 10;
    }
    
    arr
}

fn counting_sort_by_digit(arr: Vec<u32>, exp: u32) -> Vec<u32> {
    let n = arr.len();
    let mut output = vec![0; n];
    let mut count = vec![0; 10];
    
    // Store count of occurrences of each digit
    for &num in &arr {
        let digit = (num / exp) % 10;
        count[digit as usize] += 1;
    }
    
    // Change count[i] so it contains actual position
    for i in 1..10 {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for i in (0..n).rev() {
        let digit = (arr[i] / exp) % 10;
        output[count[digit as usize] - 1] = arr[i];
        count[digit as usize] -= 1;
    }
    
    output
}

// String radix sort implementation
pub fn radix_sort_strings(strings: Vec<String>) -> Vec<String> {
    if strings.is_empty() {
        return strings;
    }
    
    let max_length = strings.iter().map(|s| s.len()).max().unwrap_or(0);
    
    // Pad strings to equal length
    let mut padded_strings: Vec<String> = strings
        .into_iter()
        .map(|s| format!("{:<width$}", s, width = max_length))
        .collect();
    
    // Sort from rightmost character to leftmost
    for pos in (0..max_length).rev() {
        padded_strings = counting_sort_strings_by_position(padded_strings, pos);
    }
    
    // Remove padding
    padded_strings
        .into_iter()
        .map(|s| s.trim_end().to_string())
        .collect()
}

fn counting_sort_strings_by_position(strings: Vec<String>, pos: usize) -> Vec<String> {
    let mut count = vec![0; 256]; // ASCII characters
    let mut output = vec![String::new(); strings.len()];
    
    // Count occurrences
    for s in &strings {
        let char_code = s.chars().nth(pos).unwrap_or('\0') as usize;
        count[char_code] += 1;
    }
    
    // Calculate positions
    for i in 1..256 {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for i in (0..strings.len()).rev() {
        let char_code = strings[i].chars().nth(pos).unwrap_or('\0') as usize;
        output[count[char_code] - 1] = strings[i].clone();
        count[char_code] -= 1;
    }
    
    output
}
```

## Counting Sort

Counting Sort is often used as a subroutine in Radix Sort. It works well when the range of possible values is small.

### Python Implementation

```python
def counting_sort(arr, max_val=None):
    """
    Counting sort implementation.
    
    Time Complexity: O(n + k) where k is the range of values
    Space Complexity: O(k)
    
    Args:
        arr: List of non-negative integers
        max_val: Maximum value in array (if None, calculated automatically)
    
    Returns:
        Sorted array
    """
    if not arr:
        return arr
    
    if max_val is None:
        max_val = max(arr)
    
    # Create count array
    count = [0] * (max_val + 1)
    
    # Count occurrences
    for num in arr:
        count[num] += 1
    
    # Build sorted array
    result = []
    for value in range(max_val + 1):
        result.extend([value] * count[value])
    
    return result

def counting_sort_stable(arr, max_val=None):
    """
    Stable version of counting sort that preserves relative order.
    """
    if not arr:
        return arr
    
    if max_val is None:
        max_val = max(arr)
    
    count = [0] * (max_val + 1)
    output = [0] * len(arr)
    
    # Count occurrences
    for num in arr:
        count[num] += 1
    
    # Transform count array to position array
    for i in range(1, max_val + 1):
        count[i] += count[i - 1]
    
    # Build output array (stable)
    for i in range(len(arr) - 1, -1, -1):
        output[count[arr[i]] - 1] = arr[i]
        count[arr[i]] -= 1
    
    return output

def counting_sort_objects(objects, key_func, max_val=None):
    """
    Counting sort for objects with a key function.
    
    Args:
        objects: List of objects to sort
        key_func: Function to extract sort key from object
        max_val: Maximum key value
    """
    if not objects:
        return objects
    
    keys = [key_func(obj) for obj in objects]
    if max_val is None:
        max_val = max(keys)
    
    count = [0] * (max_val + 1)
    output = [None] * len(objects)
    
    # Count occurrences
    for key in keys:
        count[key] += 1
    
    # Transform to position array
    for i in range(1, max_val + 1):
        count[i] += count[i - 1]
    
    # Build output array
    for i in range(len(objects) - 1, -1, -1):
        key = keys[i]
        output[count[key] - 1] = objects[i]
        count[key] -= 1
    
    return output
```

### Rust Implementation

```rust
pub fn counting_sort(arr: Vec<usize>, max_val: Option<usize>) -> Vec<usize> {
    if arr.is_empty() {
        return arr;
    }
    
    let max_val = max_val.unwrap_or_else(|| *arr.iter().max().unwrap());
    let mut count = vec![0; max_val + 1];
    
    // Count occurrences
    for &num in &arr {
        count[num] += 1;
    }
    
    // Build sorted array
    let mut result = Vec::new();
    for (value, &freq) in count.iter().enumerate() {
        result.extend(vec![value; freq]);
    }
    
    result
}

pub fn counting_sort_stable(arr: Vec<usize>, max_val: Option<usize>) -> Vec<usize> {
    if arr.is_empty() {
        return arr;
    }
    
    let max_val = max_val.unwrap_or_else(|| *arr.iter().max().unwrap());
    let mut count = vec![0; max_val + 1];
    let mut output = vec![0; arr.len()];
    
    // Count occurrences
    for &num in &arr {
        count[num] += 1;
    }
    
    // Transform to position array
    for i in 1..=max_val {
        count[i] += count[i - 1];
    }
    
    // Build output array (stable)
    for i in (0..arr.len()).rev() {
        output[count[arr[i]] - 1] = arr[i];
        count[arr[i]] -= 1;
    }
    
    output
}

// Generic counting sort for objects with key function
pub fn counting_sort_by_key<T, F>(
    objects: Vec<T>, 
    key_func: F, 
    max_val: Option<usize>
) -> Vec<T> 
where
    F: Fn(&T) -> usize,
    T: Clone,
{
    if objects.is_empty() {
        return objects;
    }
    
    let keys: Vec<usize> = objects.iter().map(&key_func).collect();
    let max_val = max_val.unwrap_or_else(|| *keys.iter().max().unwrap());
    
    let mut count = vec![0; max_val + 1];
    let mut output = vec![None; objects.len()];
    
    // Count occurrences
    for &key in &keys {
        count[key] += 1;
    }
    
    // Transform to position array
    for i in 1..=max_val {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for i in (0..objects.len()).rev() {
        let key = keys[i];
        output[count[key] - 1] = Some(objects[i].clone());
        count[key] -= 1;
    }
    
    output.into_iter().map(|x| x.unwrap()).collect()
}
```

## Bucket Sort

Bucket Sort distributes elements into buckets, sorts each bucket individually, then concatenates the results.

### Python Implementation

```python
import math

def bucket_sort(arr, bucket_count=None):
    """
    Bucket sort implementation for floating point numbers in range [0, 1).
    
    Time Complexity: O(n + k) average case, O(n²) worst case
    Space Complexity: O(n + k)
    
    Args:
        arr: List of numbers to sort
        bucket_count: Number of buckets (if None, uses sqrt(n))
    
    Returns:
        Sorted array
    """
    if not arr or len(arr) <= 1:
        return arr
    
    if bucket_count is None:
        bucket_count = int(math.sqrt(len(arr)))
    
    # Find min and max values
    min_val = min(arr)
    max_val = max(arr)
    
    # Handle case where all elements are equal
    if min_val == max_val:
        return arr
    
    # Create buckets
    buckets = [[] for _ in range(bucket_count)]
    
    # Distribute elements into buckets
    range_val = max_val - min_val
    for num in arr:
        # Calculate bucket index
        bucket_idx = min(int((num - min_val) / range_val * bucket_count), 
                        bucket_count - 1)
        buckets[bucket_idx].append(num)
    
    # Sort individual buckets and concatenate
    result = []
    for bucket in buckets:
        if bucket:
            bucket.sort()  # Using built-in sort for each bucket
            result.extend(bucket)
    
    return result

def bucket_sort_integers(arr, bucket_count=None):
    """
    Bucket sort optimized for integers.
    
    Args:
        arr: List of integers to sort
        bucket_count: Number of buckets
    
    Returns:
        Sorted array
    """
    if not arr or len(arr) <= 1:
        return arr
    
    min_val = min(arr)
    max_val = max(arr)
    
    if min_val == max_val:
        return arr
    
    if bucket_count is None:
        bucket_count = min(len(arr), max_val - min_val + 1)
    
    # Create buckets
    buckets = [[] for _ in range(bucket_count)]
    
    # Distribute elements
    range_val = max_val - min_val + 1
    for num in arr:
        bucket_idx = min((num - min_val) * bucket_count // range_val, 
                        bucket_count - 1)
        buckets[bucket_idx].append(num)
    
    # Sort and concatenate
    result = []
    for bucket in buckets:
        if bucket:
            bucket.sort()
            result.extend(bucket)
    
    return result

def bucket_sort_custom(arr, bucket_func, sort_func=None):
    """
    Generic bucket sort with custom bucket assignment and sorting functions.
    
    Args:
        arr: Array to sort
        bucket_func: Function that returns bucket index for each element
        sort_func: Function to sort individual buckets (default: built-in sort)
    
    Returns:
        Sorted array
    """
    if not arr:
        return arr
    
    if sort_func is None:
        sort_func = sorted
    
    # Determine number of buckets
    bucket_indices = [bucket_func(x) for x in arr]
    max_bucket = max(bucket_indices)
    
    # Create buckets
    buckets = [[] for _ in range(max_bucket + 1)]
    
    # Distribute elements
    for i, element in enumerate(arr):
        buckets[bucket_indices[i]].append(element)
    
    # Sort and concatenate
    result = []
    for bucket in buckets:
        if bucket:
            sorted_bucket = sort_func(bucket)
            result.extend(sorted_bucket)
    
    return result
```

### Rust Implementation

```rust
use std::cmp::Ordering;

pub fn bucket_sort_f64(mut arr: Vec<f64>, bucket_count: Option<usize>) -> Vec<f64> {
    if arr.len() <= 1 {
        return arr;
    }
    
    let bucket_count = bucket_count.unwrap_or((arr.len() as f64).sqrt() as usize).max(1);
    
    // Find min and max
    let min_val = arr.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let max_val = arr.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
    
    if (max_val - min_val).abs() < f64::EPSILON {
        return arr;
    }
    
    // Create buckets
    let mut buckets: Vec<Vec<f64>> = vec![Vec::new(); bucket_count];
    
    // Distribute elements
    let range = max_val - min_val;
    for num in arr {
        let bucket_idx = ((num - min_val) / range * bucket_count as f64) as usize;
        let bucket_idx = bucket_idx.min(bucket_count - 1);
        buckets[bucket_idx].push(num);
    }
    
    // Sort individual buckets and concatenate
    let mut result = Vec::new();
    for mut bucket in buckets {
        if !bucket.is_empty() {
            bucket.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));
            result.extend(bucket);
        }
    }
    
    result
}

pub fn bucket_sort_integers(arr: Vec<i32>, bucket_count: Option<usize>) -> Vec<i32> {
    if arr.len() <= 1 {
        return arr;
    }
    
    let min_val = *arr.iter().min().unwrap();
    let max_val = *arr.iter().max().unwrap();
    
    if min_val == max_val {
        return arr;
    }
    
    let bucket_count = bucket_count.unwrap_or(
        (arr.len()).min((max_val - min_val + 1) as usize)
    ).max(1);
    
    // Create buckets
    let mut buckets: Vec<Vec<i32>> = vec![Vec::new(); bucket_count];
    
    // Distribute elements
    let range = max_val - min_val + 1;
    for num in arr {
        let bucket_idx = ((num - min_val) as usize * bucket_count / range as usize)
            .min(bucket_count - 1);
        buckets[bucket_idx].push(num);
    }
    
    // Sort and concatenate
    let mut result = Vec::new();
    for mut bucket in buckets {
        if !bucket.is_empty() {
            bucket.sort();
            result.extend(bucket);
        }
    }
    
    result
}

// Generic bucket sort
pub fn bucket_sort_generic<T, F, G>(
    arr: Vec<T>,
    bucket_func: F,
    sort_func: G,
) -> Vec<T>
where
    F: Fn(&T) -> usize,
    G: Fn(&mut Vec<T>),
    T: Clone,
{
    if arr.is_empty() {
        return arr;
    }
    
    // Find maximum bucket index
    let max_bucket = arr.iter().map(&bucket_func).max().unwrap_or(0);
    
    // Create buckets
    let mut buckets: Vec<Vec<T>> = vec![Vec::new(); max_bucket + 1];
    
    // Distribute elements
    for element in arr {
        let bucket_idx = bucket_func(&element);
        buckets[bucket_idx].push(element);
    }
    
    // Sort and concatenate
    let mut result = Vec::new();
    for mut bucket in buckets {
        if !bucket.is_empty() {
            sort_func(&mut bucket);
            result.extend(bucket);
        }
    }
    
    result
}
```

## Performance Analysis

### Time Complexity Comparison

| Algorithm | Best Case | Average Case | Worst Case | Space Complexity |
|-----------|-----------|--------------|------------|------------------|
| Radix Sort | O(d×n) | O(d×n) | O(d×n) | O(n + k) |
| Counting Sort | O(n + k) | O(n + k) | O(n + k) | O(k) |
| Bucket Sort | O(n + k) | O(n + k) | O(n²) | O(n + k) |

Where:
- `n` = number of elements
- `k` = range of values
- `d` = number of digits

### Space Complexity Details

- **Radix Sort**: O(n + k) where k is typically 10 (for decimal digits)
- **Counting Sort**: O(k) where k is the range of values
- **Bucket Sort**: O(n + k) where k is the number of buckets

### Practical Performance Considerations

1. **Cache Performance**: These algorithms often have better cache locality than comparison-based sorts
2. **Parallelization**: Bucket sort can be easily parallelized
3. **Memory Usage**: Can use significant memory for large ranges of values
4. **Integer vs Float**: Integer sorting is generally faster and more cache-friendly

## When to Use Each Algorithm

### Radix Sort
**Best for:**
- Large datasets of integers with limited number of digits
- Strings of equal length
- When stability is required
- When you want consistent O(d×n) performance

**Avoid when:**
- Data has very large range (many digits)
- Working with floating-point numbers with high precision
- Memory is very limited

### Counting Sort
**Best for:**
- Small range of integer values (k is small relative to n)
- When you need stable sorting
- As a subroutine for other algorithms
- Histograms and frequency counting

**Avoid when:**
- Range of values is very large
- Working with floating-point numbers
- Memory usage is a primary concern

### Bucket Sort
**Best for:**
- Uniformly distributed floating-point numbers
- When you can define good bucket boundaries
- Parallel processing scenarios
- Large datasets where comparison-based sorts are too slow

**Avoid when:**
- Data is not uniformly distributed
- You can't define good bucket boundaries
- Working with discrete values with small range (use counting sort instead)

### Example Usage Scenarios

```python
# Use Radix Sort for:
employee_ids = [12345, 54321, 98765, 11111, 99999]  # Fixed-width integers
sorted_ids = radix_sort(employee_ids)

# Use Counting Sort for:
grades = [85, 92, 78, 85, 90, 88, 92, 85]  # Small range (0-100)
sorted_grades = counting_sort(grades, max_val=100)

# Use Bucket Sort for:
measurements = [0.23, 0.87, 0.34, 0.65, 0.12, 0.98]  # Uniform floats [0,1)
sorted_measurements = bucket_sort(measurements)
```

This comprehensive guide provides you with production-ready implementations of all major digit-wise sorting algorithms, along with the knowledge to choose the right algorithm for your specific use case.

I'll create a detailed ASCII diagram showing how radix sort (a digit-wise sorting algorithm) works step by step. This will demonstrate the process of sorting numbers by examining each digit position.This ASCII diagram shows the complete process of radix sort, a digit-wise sorting algorithm. Here's what makes it special:

**How it works**: Instead of comparing entire numbers, radix sort examines one digit position at a time, starting from the rightmost (ones place) and moving left. Numbers are distributed into buckets (0-9) based on the current digit, then collected back in order.

**Why it's efficient**: By processing digits systematically, it avoids the comparisons that other sorting algorithms require, making it particularly effective for sorting integers or strings of fixed length.

**The stability factor**: Notice how numbers with the same digit maintain their relative order from the previous step - this "stable" property is crucial for the algorithm's correctness.

The diagram traces through each step with the same set of numbers, showing how the partial ordering from each digit position contributes to the final sorted result. The bucket visualization makes it clear how the distribution and collection process works at each stage.

RADIX SORT (DIGIT-WISE SORTING) ALGORITHM VISUALIZATION
========================================================

Initial Array: [170, 45, 75, 90, 2, 802, 24, 66]

STEP 1: Sort by ONES place (rightmost digit)
-------------------------------------------
Original:  [ 170,  45,  75,  90,   2, 802,  24,  66]
           [  0̲,   5̲,   5̲,   0̲,   2̲,   2̲,   4̲,   6̲]  ← Focus on ones digit

Buckets (0-9):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ 170 │     │  2  │     │ 24  │ 45  │ 66  │     │     │     │
│ 90  │     │ 802 │     │     │ 75  │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

After Step 1: [170, 90, 2, 802, 24, 45, 75, 66]

STEP 2: Sort by TENS place (middle digit)
----------------------------------------
Current:   [ 170,  90,   2, 802,  24,  45,  75,  66]
           [  7̲0,   9̲0,   0̲2,   0̲2,   2̲4,   4̲5,   7̲5,   6̲6]  ← Focus on tens digit

Buckets (0-9):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  2  │     │ 24  │     │ 45  │     │ 66  │ 170 │     │ 90  │
│ 802 │     │     │     │     │     │     │ 75  │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

After Step 2: [2, 802, 24, 45, 66, 170, 75, 90]

STEP 3: Sort by HUNDREDS place (leftmost digit)
----------------------------------------------
Current:   [   2, 802,  24,  45,  66, 170,  75,  90]
           [   0̲,   8̲,   0̲,   0̲,   0̲,   1̲,   0̲,   0̲]  ← Focus on hundreds digit

Buckets (0-9):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  2  │ 170 │     │     │     │     │     │     │ 802 │     │
│ 24  │     │     │     │     │     │     │     │     │     │
│ 45  │     │     │     │     │     │     │     │     │     │
│ 66  │     │     │     │     │     │     │     │     │     │
│ 75  │     │     │     │     │     │     │     │     │     │
│ 90  │     │     │     │     │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

FINAL SORTED ARRAY: [2, 24, 45, 66, 75, 90, 170, 802]

ALGORITHM EXPLANATION:
=====================

1. FIND MAXIMUM: Determine the number with most digits (802 = 3 digits)
2. ITERATE: Process each digit position from right to left
3. DISTRIBUTE: Place numbers into buckets based on current digit
4. COLLECT: Gather numbers from buckets in order (0→9)
5. REPEAT: Continue until all digit positions are processed

KEY PROPERTIES:
==============
• Time Complexity: O(d × (n + k)) where d=digits, n=elements, k=range
• Space Complexity: O(n + k)
• Stable: Maintains relative order of equal elements
• Non-comparative: Doesn't compare elements directly

DIGIT EXTRACTION FORMULA:
========================
For digit at position 'pos' (0=ones, 1=tens, 2=hundreds):
digit = (number / 10^pos) % 10

Examples:
- 802 ones place:     (802 / 1) % 10 = 2
- 802 tens place:     (802 / 10) % 10 = 0  
- 802 hundreds place: (802 / 100) % 10 = 8

VISUAL FLOW:
===========
Unsorted → Sort by 1s → Sort by 10s → Sort by 100s → Sorted
  ↓           ↓            ↓             ↓           ↓
[170,45]   [170,90]     [2,802]      [2,24]    [2,24,45]
[75,90]    [2,802]      [24,45]      [45,66]   [66,75,90]
[2,802]    [24,45]      [66,170]     [170,75]  [170,802]
[24,66]    [75,66]      [75,90]      [90,802]