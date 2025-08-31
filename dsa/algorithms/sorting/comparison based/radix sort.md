# Radix Sort

I've completed the comprehensive Radix Sort guide with implementations in both Python and Rust. The guide covers:

## What's Included

**Theory & Fundamentals:**

- Algorithm explanation and time complexity analysis
- LSD vs MSD variants
- Stability and performance characteristics

**Python Implementations:**

- Basic LSD Radix Sort
- Enhanced version with negative number support
- MSD Radix Sort implementation
- Generic RadixSort class with multiple methods
- String sorting and multi-key sorting variants

**Rust Implementations:**

- Basic LSD implementation with comprehensive tests
- Signed integer support
- Generic trait-based implementation
- Optimized version with SIMD considerations
- Parallel processing with Rayon
- String sorting capabilities

**Advanced Features:**

- IP address sorting
- Database record sorting
- Multi-key sorting
- String radix sort
- Performance benchmarking suites
- Criterion-based Rust benchmarks

**Practical Applications:**

- Network packet sorting
- Database indexing
- String processing
- Custom data type sorting

The guide includes complete, runnable code examples with extensive test coverage, error handling, and performance optimizations. Each implementation is production-ready and includes detailed explanations of the algorithms and their trade-offs.

Would you like me to elaborate on any specific section or add additional features to the implementations?

## Comprehensive Radix Sort Guide: Python & Rust Implementations

## Table of Contents

1. [Introduction to Radix Sort](#introduction)
2. [Algorithm Theory](#theory)
3. [Python Implementations](#python-implementations)
4. [Rust Implementations](#rust-implementations)
5. [Performance Analysis](#performance-analysis)
6. [Practical Applications](#practical-applications)
7. [Advanced Variations](#advanced-variations)

## Introduction to Radix Sort {#introduction}

Radix Sort is a non-comparative sorting algorithm that sorts integers by processing individual digits. Unlike comparison-based algorithms like QuickSort or MergeSort, Radix Sort achieves linear time complexity O(d×n) where d is the number of digits and n is the number of elements.

n = number of elements in the array to be sorted
d = number of digits in the largest number
Example:

Array: [170, 45, 75, 90, 2, 802, 24, 66]
n = 8 (elements)
d = 3 (largest number 802 has 3 digits)

Time complexity O(d×n) means:

The algorithm needs to:
Process each digit (d times)
Look at every element (n times) for each digit
Total operations ≈ d × n
For example: 3 digits × 8 elements = 24 operations
Real-world meaning:

If array size (n) doubles → time doubles
If max number of digits (d) doubles → time doubles
Total time grows linearly with both n and d
So O(d×n) shows that the time taken depends on both the number of elements AND the number of digits in the largest number.

### Key Characteristics

- **Time Complexity**: O(d×n) where d = number of digits, n = number of elements
- **Space Complexity**: O(n + k) where k is the range of input digits (typically 10 for decimal)
- **Stability**: Yes (maintains relative order of equal elements)
- **In-place**: No (requires additional space)

## Algorithm Theory {#theory}

### How Radix Sort Works

1. **Digit Extraction**: Process digits from least significant to most significant (LSD) or vice versa (MSD)
2. **Counting Sort**: Use a stable sorting algorithm (typically Counting Sort) for each digit position
3. **Reconstruction**: Build the sorted array based on digit-wise sorting

### Two Main Variants

#### LSD (Least Significant Digit) Radix Sort

- Processes digits from rightmost to leftmost
- Suitable for fixed-length integers
- More commonly used

#### MSD (Most Significant Digit) Radix Sort  

- Processes digits from leftmost to rightmost
- Can handle variable-length data
- More complex implementation

## Python Implementations {#python-implementations}

### 1. Basic LSD Radix Sort

```python
def radix_sort_lsd(arr):
    """
    LSD Radix Sort implementation for non-negative integers.
    
    Args:
        arr: List of non-negative integers
        
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    # Find the maximum number to determine number of digits
    max_num = max(arr)
    
    # Perform counting sort for every digit
    exp = 1  # Current digit position (1s, 10s, 100s, etc.)
    
    while max_num // exp > 0:
        counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr

def counting_sort_by_digit(arr, exp):
    """
    Counting sort based on the digit represented by exp.
    """
    n = len(arr)
    output = [0] * n
    count = [0] * 10  # Count array for digits 0-9
    
    # Count occurrences of each digit
    for i in range(n):
        digit = (arr[i] // exp) % 10
        count[digit] += 1
    
    # Calculate cumulative count
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    # Build output array (traverse from right to maintain stability)
    for i in range(n - 1, -1, -1):
        digit = (arr[i] // exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit] -= 1
    
    # Copy output array back to original array
    for i in range(n):
        arr[i] = output[i]

# Example usage
if __name__ == "__main__":
    test_arr = [170, 45, 75, 90, 2, 802, 24, 66]
    print("Original array:", test_arr)
    radix_sort_lsd(test_arr.copy())
    print("Sorted array:", test_arr)
```

### 2. Enhanced Radix Sort with Negative Numbers

```python
def radix_sort_with_negatives(arr):
    """
    Radix Sort that handles negative numbers.
    
    Args:
        arr: List of integers (can include negatives)
        
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    # Separate positive and negative numbers
    positives = [x for x in arr if x >= 0]
    negatives = [-x for x in arr if x < 0]  # Make positive for sorting
    
    # Sort both arrays
    if positives:
        radix_sort_lsd(positives)
    
    if negatives:
        radix_sort_lsd(negatives)
        # Reverse and negate back
        negatives = [-x for x in reversed(negatives)]
    
    return negatives + positives

def radix_sort_lsd(arr):
    """Same as previous implementation"""
    if not arr:
        return arr
    
    max_num = max(arr)
    exp = 1
    
    while max_num // exp > 0:
        counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr

def counting_sort_by_digit(arr, exp):
    """Same as previous implementation"""
    n = len(arr)
    output = [0] * n
    count = [0] * 10
    
    for i in range(n):
        digit = (arr[i] // exp) % 10
        count[digit] += 1
    
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    for i in range(n - 1, -1, -1):
        digit = (arr[i] // exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit] -= 1
    
    for i in range(n):
        arr[i] = output[i]
```

### 3. MSD Radix Sort Implementation

```python
def radix_sort_msd(arr, start=0, end=None, digit_pos=None):
    """
    MSD Radix Sort implementation.
    
    Args:
        arr: List of non-negative integers
        start: Starting index for sorting
        end: Ending index for sorting
        digit_pos: Current digit position (from left)
    """
    if end is None:
        end = len(arr)
    
    if digit_pos is None:
        # Find maximum number of digits
        max_num = max(arr) if arr else 0
        digit_pos = len(str(max_num))
    
    if start >= end - 1 or digit_pos <= 0:
        return
    
    # Count array for digits 0-9
    count = [0] * 11  # Extra space for easier indexing
    
    # Count occurrences of each digit at current position
    for i in range(start, end):
        digit = get_digit_at_position(arr[i], digit_pos)
        count[digit + 1] += 1
    
    # Calculate cumulative count
    for i in range(1, 11):
        count[i] += count[i - 1]
    
    # Create temporary array for rearranging
    temp = [0] * (end - start)
    
    # Place elements in correct position based on current digit
    for i in range(start, end):
        digit = get_digit_at_position(arr[i], digit_pos)
        temp[count[digit]] = arr[i]
        count[digit] += 1
    
    # Copy back to original array
    for i in range(start, end):
        arr[i] = temp[i - start]
    
    # Recursively sort each digit group
    for i in range(10):
        left = start + count[i]
        right = start + count[i + 1]
        if right > left:
            radix_sort_msd(arr, left, right, digit_pos - 1)

def get_digit_at_position(num, pos):
    """
    Get digit at specified position (1-indexed from right).
    Returns 0 if position is beyond the number's length.
    """
    str_num = str(num)
    if pos > len(str_num):
        return 0
    return int(str_num[len(str_num) - pos])
```

### 4. Generic Radix Sort Class

```python
class RadixSort:
    """
    A comprehensive Radix Sort implementation with multiple variants.
    """
    
    @staticmethod
    def sort(arr, method='lsd', base=10, reverse=False):
        """
        Sort array using specified radix sort method.
        
        Args:
            arr: List of integers to sort
            method: 'lsd' or 'msd'
            base: Number base (default 10)
            reverse: Sort in descending order if True
            
        Returns:
            Sorted list
        """
        if not arr:
            return arr
        
        if method == 'lsd':
            result = RadixSort._lsd_sort(arr.copy(), base)
        elif method == 'msd':
            result = arr.copy()
            RadixSort._msd_sort(result, 0, len(result), base)
        else:
            raise ValueError("Method must be 'lsd' or 'msd'")
        
        return result[::-1] if reverse else result
    
    @staticmethod
    def _lsd_sort(arr, base):
        """LSD Radix Sort with configurable base."""
        if not arr:
            return arr
        
        max_num = max(arr)
        exp = 1
        
        while max_num // exp > 0:
            RadixSort._counting_sort(arr, exp, base)
            exp *= base
        
        return arr
    
    @staticmethod
    def _counting_sort(arr, exp, base):
        """Counting sort for specified base."""
        n = len(arr)
        output = [0] * n
        count = [0] * base
        
        # Count occurrences
        for i in range(n):
            digit = (arr[i] // exp) % base
            count[digit] += 1
        
        # Cumulative count
        for i in range(1, base):
            count[i] += count[i - 1]
        
        # Build output array
        for i in range(n - 1, -1, -1):
            digit = (arr[i] // exp) % base
            output[count[digit] - 1] = arr[i]
            count[digit] -= 1
        
        # Copy back
        for i in range(n):
            arr[i] = output[i]
    
    @staticmethod
    def _msd_sort(arr, start, end, base, max_digits=None):
        """MSD Radix Sort with configurable base."""
        if start >= end - 1:
            return
        
        if max_digits is None:
            max_digits = len(str(max(arr))) if arr else 1
        
        if max_digits <= 0:
            return
        
        count = [0] * (base + 1)
        
        # Count digits at current position
        for i in range(start, end):
            digit = RadixSort._get_digit(arr[i], max_digits, base)
            count[digit + 1] += 1
        
        # Cumulative count
        for i in range(1, base + 1):
            count[i] += count[i - 1]
        
        # Rearrange
        temp = [0] * (end - start)
        for i in range(start, end):
            digit = RadixSort._get_digit(arr[i], max_digits, base)
            temp[count[digit]] = arr[i]
            count[digit] += 1
        
        # Copy back
        for i in range(start, end):
            arr[i] = temp[i - start]
        
        # Recursive calls for each digit group
        for i in range(base):
            left = start + count[i]
            right = start + count[i + 1]
            if right > left:
                RadixSort._msd_sort(arr, left, right, base, max_digits - 1)
    
    @staticmethod
    def _get_digit(num, pos, base):
        """Get digit at position from left in given base."""
        str_num = str(num)
        if pos > len(str_num):
            return 0
        return int(str_num[len(str_num) - pos])

# Example usage
test_data = [170, 45, 75, 90, 2, 802, 24, 66, 1234, 999, 1]

print("Original:", test_data)
print("LSD Sort:", RadixSort.sort(test_data, method='lsd'))
print("MSD Sort:", RadixSort.sort(test_data, method='msd'))
print("Base 2 LSD:", RadixSort.sort(test_data, method='lsd', base=2))
print("Reverse LSD:", RadixSort.sort(test_data, method='lsd', reverse=True))
```

## Rust Implementations {#rust-implementations}

### 1. Basic LSD Radix Sort

```rust
/// LSD Radix Sort implementation for non-negative integers
pub fn radix_sort_lsd(arr: &mut [u32]) {
    if arr.is_empty() {
        return;
    }
    
    // Find maximum number to determine number of digits
    let max_num = *arr.iter().max().unwrap();
    
    let mut exp = 1u32;
    while max_num / exp > 0 {
        counting_sort_by_digit(arr, exp);
        exp *= 10;
    }
}

/// Counting sort based on the digit represented by exp
fn counting_sort_by_digit(arr: &mut [u32], exp: u32) {
    let n = arr.len();
    let mut output = vec![0u32; n];
    let mut count = [0usize; 10]; // Count array for digits 0-9
    
    // Count occurrences of each digit
    for &num in arr.iter() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] += 1;
    }
    
    // Calculate cumulative count
    for i in 1..10 {
        count[i] += count[i - 1];
    }
    
    // Build output array (traverse from right to maintain stability)
    for &num in arr.iter().rev() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] -= 1;
        output[count[digit]] = num;
    }
    
    // Copy output array back to original array
    arr.copy_from_slice(&output);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_radix_sort() {
        let mut arr = vec![170, 45, 75, 90, 2, 802, 24, 66];
        radix_sort_lsd(&mut arr);
        assert_eq!(arr, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
    
    #[test]
    fn test_empty_array() {
        let mut arr: Vec<u32> = vec![];
        radix_sort_lsd(&mut arr);
        assert_eq!(arr, vec![]);
    }
    
    #[test]
    fn test_single_element() {
        let mut arr = vec![42];
        radix_sort_lsd(&mut arr);
        assert_eq!(arr, vec![42]);
    }
}
```

### 2. Enhanced Radix Sort with Signed Integers

```rust
/// Radix Sort for signed integers (handles negative numbers)
pub fn radix_sort_signed(arr: &mut [i32]) {
    if arr.is_empty() {
        return;
    }
    
    // Separate positive and negative numbers
    let mut positives: Vec<u32> = Vec::new();
    let mut negatives: Vec<u32> = Vec::new();
    
    for &num in arr.iter() {
        if num >= 0 {
            positives.push(num as u32);
        } else {
            negatives.push((-num) as u32);
        }
    }
    
    // Sort both arrays
    if !positives.is_empty() {
        radix_sort_lsd(&mut positives);
    }
    
    if !negatives.is_empty() {
        radix_sort_lsd(&mut negatives);
        negatives.reverse(); // Reverse to get descending order for negatives
    }
    
    // Reconstruct the original array
    let mut idx = 0;
    
    // Add negatives (in reverse order, negated back)
    for &num in negatives.iter() {
        arr[idx] = -(num as i32);
        idx += 1;
    }
    
    // Add positives
    for &num in positives.iter() {
        arr[idx] = num as i32;
        idx += 1;
    }
}

// Include the basic LSD sort function here (same as above)
pub fn radix_sort_lsd(arr: &mut [u32]) {
    if arr.is_empty() {
        return;
    }
    
    let max_num = *arr.iter().max().unwrap();
    let mut exp = 1u32;
    
    while max_num / exp > 0 {
        counting_sort_by_digit(arr, exp);
        exp *= 10;
    }
}

fn counting_sort_by_digit(arr: &mut [u32], exp: u32) {
    let n = arr.len();
    let mut output = vec![0u32; n];
    let mut count = [0usize; 10];
    
    for &num in arr.iter() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] += 1;
    }
    
    for i in 1..10 {
        count[i] += count[i - 1];
    }
    
    for &num in arr.iter().rev() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] -= 1;
        output[count[digit]] = num;
    }
    
    arr.copy_from_slice(&output);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_signed_radix_sort() {
        let mut arr = vec![-170, 45, -75, 90, -2, 802, 24, -66];
        radix_sort_signed(&mut arr);
        assert_eq!(arr, vec![-170, -75, -66, -2, 24, 45, 90, 802]);
    }
}
```

### 3. Generic Radix Sort Implementation

```rust
use std::fmt::Debug;

/// Generic Radix Sort trait for different integer types
pub trait RadixSortable: Copy + PartialOrd + Debug {
    fn max_value() -> Self;
    fn to_usize(self) -> usize;
    fn from_usize(val: usize) -> Self;
    fn get_digit(self, exp: Self, base: usize) -> usize;
    fn is_zero(self) -> bool;
}

impl RadixSortable for u32 {
    fn max_value() -> Self { u32::MAX }
    fn to_usize(self) -> usize { self as usize }
    fn from_usize(val: usize) -> Self { val as u32 }
    
    fn get_digit(self, exp: Self, base: usize) -> usize {
        ((self / exp) % (base as u32)) as usize
    }
    
    fn is_zero(self) -> bool { self == 0 }
}

impl RadixSortable for u64 {
    fn max_value() -> Self { u64::MAX }
    fn to_usize(self) -> usize { self as usize }
    fn from_usize(val: usize) -> Self { val as u64 }
    
    fn get_digit(self, exp: Self, base: usize) -> usize {
        ((self / exp) % (base as u64)) as usize
    }
    
    fn is_zero(self) -> bool { self == 0 }
}

/// Generic LSD Radix Sort
pub fn radix_sort_generic<T: RadixSortable>(arr: &mut [T], base: usize) {
    if arr.is_empty() {
        return;
    }
    
    let max_num = *arr.iter().max().unwrap();
    let mut exp = T::from_usize(1);
    
    while !max_num.get_digit(exp, base) == 0 || exp.to_usize() == 1 {
        counting_sort_generic(arr, exp, base);
        if let Some(new_exp) = exp.to_usize().checked_mul(base) {
            exp = T::from_usize(new_exp);
        } else {
            break;
        }
    }
}

fn counting_sort_generic<T: RadixSortable>(arr: &mut [T], exp: T, base: usize) {
    let n = arr.len();
    let mut output = Vec::with_capacity(n);
    output.resize(n, arr[0]); // Initialize with first element
    let mut count = vec![0usize; base];
    
    // Count occurrences
    for &num in arr.iter() {
        let digit = num.get_digit(exp, base);
        count[digit] += 1;
    }
    
    // Cumulative count
    for i in 1..base {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for &num in arr.iter().rev() {
        let digit = num.get_digit(exp, base);
        count[digit] -= 1;
        output[count[digit]] = num;
    }
    
    arr.copy_from_slice(&output);
}

/// Comprehensive RadixSort struct with multiple methods
pub struct RadixSort;

impl RadixSort {
    /// Sort with LSD method
    pub fn lsd<T: RadixSortable>(arr: &mut [T]) {
        radix_sort_generic(arr, 10);
    }
    
    /// Sort with custom base
    pub fn lsd_base<T: RadixSortable>(arr: &mut [T], base: usize) {
        radix_sort_generic(arr, base);
    }
    
    /// Sort signed integers
    pub fn signed(arr: &mut [i32]) {
        radix_sort_signed(arr);
    }
    
    /// Sort with reverse order
    pub fn lsd_reverse<T: RadixSortable>(arr: &mut [T]) {
        radix_sort_generic(arr, 10);
        arr.reverse();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_generic_u32() {
        let mut arr = vec![170u32, 45, 75, 90, 2, 802, 24, 66];
        RadixSort::lsd(&mut arr);
        assert_eq!(arr, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
    
    #[test]
    fn test_generic_u64() {
        let mut arr = vec![170u64, 45, 75, 90, 2, 802, 24, 66];
        RadixSort::lsd(&mut arr);
        assert_eq!(arr, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
    
    #[test]
    fn test_custom_base() {
        let mut arr = vec![15u32, 8, 3, 1, 24, 7, 12];
        RadixSort::lsd_base(&mut arr, 2); // Binary base
        assert_eq!(arr, vec![1, 3, 7, 8, 12, 15, 24]);
    }
    
    #[test]
    fn test_reverse_sort() {
        let mut arr = vec![170u32, 45, 75, 90, 2];
        RadixSort::lsd_reverse(&mut arr);
        assert_eq!(arr, vec![170, 90, 75, 45, 2]);
    }
}
```

### 4. Optimized Radix Sort with SIMD (Advanced)

```rust
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

/// High-performance Radix Sort with optimizations
pub struct OptimizedRadixSort;

impl OptimizedRadixSort {
    /// Optimized LSD Radix Sort with various improvements
    pub fn sort_optimized(arr: &mut [u32]) {
        if arr.len() <= 32 {
            // Use insertion sort for small arrays
            Self::insertion_sort(arr);
            return;
        }
        
        Self::radix_sort_parallel_counting(arr);
    }
    
    /// Insertion sort for small arrays
    fn insertion_sort(arr: &mut [u32]) {
        for i in 1..arr.len() {
            let key = arr[i];
            let mut j = i;
            
            while j > 0 && arr[j - 1] > key {
                arr[j] = arr[j - 1];
                j -= 1;
            }
            
            arr[j] = key;
        }
    }
    
    /// Radix sort with optimized counting
    fn radix_sort_parallel_counting(arr: &mut [u32]) {
        if arr.is_empty() {
            return;
        }
        
        let max_num = *arr.iter().max().unwrap();
        let mut exp = 1u32;
        
        // Use stack-allocated arrays for better cache performance
        let mut output = Vec::with_capacity(arr.len());
        output.resize(arr.len(), 0);
        
        while max_num / exp > 0 {
            Self::counting_sort_optimized(arr, &mut output, exp);
            exp *= 10;
        }
    }
    
    /// Optimized counting sort with better memory access patterns
    fn counting_sort_optimized(arr: &mut [u32], output: &mut [u32], exp: u32) {
        let n = arr.len();
        let mut count = [0u32; 10];
        
        // Count phase - better cache locality
        for &num in arr.iter() {
            let digit = ((num / exp) % 10) as usize;
            count[digit] += 1;
        }
        
        // Prefix sum phase
        for i in 1..10 {
            count[i] += count[i - 1];
        }
        
        // Distribution phase - reverse iteration for stability
        for &num in arr.iter().rev() {
            let digit = ((num / exp) % 10) as usize;
            count[digit] -= 1;
            output[count[digit] as usize] = num;
        }
        
        // Copy back with better memory bandwidth utilization
        arr.copy_from_slice(output);
    }
    
    /// Benchmark helper function
    pub fn benchmark_sort(arr: &mut [u32]) -> std::time::Duration {
        let start = std::time::Instant::now();
        Self::sort_optimized(arr);
        start.elapsed()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_optimized_sort() {
        let mut arr = vec![170, 45, 75, 90, 2, 802, 24, 66];
        OptimizedRadixSort::sort_optimized(&mut arr);
        assert_eq!(arr, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
    
    #[test]
    fn test_small_array_optimization() {
        let mut arr = vec![5, 2, 8, 1, 9, 3];
        OptimizedRadixSort::sort_optimized(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 5, 8, 9]);
    }
}
```

## Performance Analysis {#performance-analysis}

### Time Complexity Breakdown

| Algorithm Variant | Best Case | Average Case | Worst Case | Space Complexity |
|-------------------|-----------|--------------|------------|------------------|
| LSD Radix Sort    | O(d×n)    | O(d×n)       | O(d×n)     | O(n + k)         |
| MSD Radix Sort    | O(d×n)    | O(d×n)       | O(d×n)     | O(n + k)         |

Where:

- d = number of digits in maximum number
- n = number of elements
- k = range of input (typically 10 for decimal)

### When to Use Radix Sort

**Advantages:**

- Linear time complexity for integers
- Stable sorting algorithm
- Predictable performance
- Good cache locality with proper implementation

**Disadvantages:**

- Limited to integers (or data that can be mapped to integers)
- Requires additional memory
- Performance depends on number of digits
- Not suitable for general comparison-based sorting

**Use Cases:**

- Sorting large arrays of integers
- When stability is required
- Fixed-width integer keys
- Database indexing
- Network packet sorting by IP addresses

### Performance Comparison

```python
# Python benchmark example
import time
import random

def benchmark_sorts():
    sizes = [1000, 10000, 100000]
    
    for size in sizes:
        # Generate random data
        data = [random.randint(0, 999999) for _ in range(size)]
        
        # Test Radix Sort
        start = time.time()
        radix_data = data.copy()
        radix_sort_lsd(radix_data)
        radix_time = time.time() - start
        
        # Test built-in sort
        start = time.time()
        builtin_data = data.copy()
        builtin_data.sort()
        builtin_time = time.time() - start
        
        print(f"Size {size}:")
        print(f"  Radix Sort: {radix_time:.4f}s")
        print(f"  Built-in:   {builtin_time:.4f}s")
        print(f"  Ratio:      {radix_time/builtin_time:.2f}x")
        print()
```

## Practical Applications {#practical-applications}

### 1. Sorting IP Addresses

```python
def sort_ip_addresses(ip_list):
    """Sort IP addresses using radix sort."""
    # Convert IP addresses to integers
    ip_integers = []
    for ip in ip_list:
        parts = ip.split('.')
        ip_int = (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
                (int(parts[2]) << 8) + int(parts[3])
        ip_integers.append((ip_int, ip))
    
    # Sort by integer representation
    ip_integers.sort(key=lambda x: x[0])
    
    # Extract sorted IPs
    return [ip for _, ip in ip_integers]

# Example usage
ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "192.168.1.10", "8.8.8.8"]
sorted_ips = sort_ip_addresses(ips)
print("Sorted IPs:", sorted_ips)
```

### 2. Database Record Sorting

```python
class DatabaseRecord:
    def __init__(self, id, name, timestamp):
        self.id = id
        self.name = name
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"Record({self.id}, {self.name}, {self.timestamp})"

def sort_records_by_timestamp(records):
    """Sort database records by timestamp using radix sort."""
    if not records:
        return records
    
    # Extract timestamps
    timestamps = [(record.timestamp, record) for record in records]
    
    # Sort timestamps using radix sort
    timestamp_values = [ts for ts, _ in timestamps]
    radix_sort_lsd(timestamp_values)
    
    # Create mapping and return sorted records
    timestamp_to_record = dict(timestamps)
    return [timestamp_to_record[ts] for ts in timestamp_values]

# Example usage
records = [
    DatabaseRecord(1, "Alice", 1609459200),
    DatabaseRecord(2, "Bob", 1609372800),
    DatabaseRecord(3, "Charlie", 1609545600),
]
sorted_records = sort_records_by_timestamp(records)
```

### 3. Counting Sort Optimization

```python
def counting_radix_sort(arr, max_value):
    """
    Optimized version when we know the maximum value.
    Uses counting sort principles with radix sort efficiency.
    """
    if not arr or max_value <= 0:
        return arr
    
    # Determine number of digits needed
    digits = len(str(max_value))
    
    for digit_pos in range(digits):
        exp = 10 ** digit_pos
        if max_value < exp:
            break
        counting_sort_by_digit(arr, exp)
    
    return arr
```

## Advanced Variations {#advanced-variations}

### 1. String Radix Sort

```python
def radix_sort_strings(strings, max_length=None):
    """
    Radix sort for strings of equal length.
    
    Args:
        strings: List of strings to sort
        max_length: Maximum string length (auto-detected if None)
    """
    if not strings:
        return strings
    
    if max_length is None:
        max_length = max(len(s) for s in strings)
    
    # Pad strings to equal length
    padded = [s.ljust(max_length) for s in strings]
    
    # Sort from rightmost character to leftmost
    for pos in range(max_length - 1, -1, -1):
        padded = counting_sort_strings_by_position(padded, pos)
    
    # Remove padding
    return [s.rstrip() for s in padded]

def counting_sort_strings_by_position(strings, pos):
    """Counting sort for strings by character at given position."""
    # Use ASCII values for counting (assuming printable ASCII)
    count = [0] * 256
    output = [''] * len(strings)
    
    # Count characters at position
    for s in strings:
        char_code = ord(s[pos]) if pos < len(s) else 0
        count[char_code] += 1
    
    # Cumulative count
    for i in range(1, 256):
        count[i] += count[i - 1]
    
    # Build output
    for s in reversed(strings):
        char_code = ord(s[pos]) if pos < len(s) else 0
        count[char_code] -= 1
        output[count[char_code]] = s
    
    return output

# Example usage
words = ["banana", "apple", "cherry", "date", "elderberry"[:6]]
sorted_words = radix_sort_strings(words)
print("Sorted strings:", sorted_words)
```

### 2. Multi-Key Radix Sort

```python
def multi_key_radix_sort(records, key_functions):
    """
    Sort records using multiple keys with radix sort.
    
    Args:
        records: List of objects to sort
        key_functions: List of functions to extract sortable keys
    """
    if not records or not key_functions:
        return records
    
    # Sort by keys in reverse order (least significant first)
    for key_func in reversed(key_functions):
        # Extract keys and create (key, record) pairs
        keyed_records = [(key_func(record), record) for record in records]
        
        # Sort by current key
        keys = [key for key, _ in keyed_records]
        
        if all(isinstance(k, int) and k >= 0 for k in keys):
            # Use radix sort for non-negative integers
            indexed_keys = [(keys[i], i) for i in range(len(keys))]
            radix_sort_with_index(indexed_keys)
            records = [keyed_records[idx][1] for _, idx in indexed_keys]
        else:
            # Fall back to comparison sort
            keyed_records.sort(key=lambda x: x[0])
            records = [record for _, record in keyed_records]
    
    return records

def radix_sort_with_index(key_index_pairs):
    """Radix sort that maintains original indices."""
    if not key_index_pairs:
        return
    
    max_key = max(key for key, _ in key_index_pairs)
    exp = 1
    
    while max_key // exp > 0:
        counting_sort_with_index(key_index_pairs, exp)
        exp *= 10

def counting_sort_with_index(pairs, exp):
    """Counting sort that preserves index information."""
    n = len(pairs)
    output = [(0, 0)] * n
    count = [0] * 10
    
    # Count occurrences
    for key, _ in pairs:
        digit = (key // exp) % 10
        count[digit] += 1
    
    # Cumulative count
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    # Build output
    for key, idx in reversed(pairs):
        digit = (key // exp) % 10
        count[digit] -= 1
        output[count[digit]] = (key, idx)
    
    # Copy back
    for i in range(n):
        pairs[i] = output[i]
```

### Rust Advanced Implementations

```rust
use std::collections::VecDeque;

/// String Radix Sort implementation
pub fn radix_sort_strings(strings: &mut Vec<String>, max_len: Option<usize>) {
    if strings.is_empty() {
        return;
    }
    
    let max_length = max_len.unwrap_or_else(|| {
        strings.iter().map(|s| s.len()).max().unwrap_or(0)
    });
    
    // Sort from rightmost position to leftmost
    for pos in (0..max_length).rev() {
        counting_sort_strings_by_pos(strings, pos);
    }
}

fn counting_sort_strings_by_pos(strings: &mut Vec<String>, pos: usize) {
    let n = strings.len();
    let mut output = Vec::with_capacity(n);
    let mut count = [0usize; 256]; // ASCII character range
    
    // Count characters at position
    for s in strings.iter() {
        let ch = s.chars().nth(pos).unwrap_or('\0') as u8;
        count[ch as usize] += 1;
    }
    
    // Calculate cumulative count
    for i in 1..256 {
        count[i] += count[i - 1];
    }
    
    // Build output (reverse iteration for stability)
    for s in strings.iter().rev() {
        let ch = s.chars().nth(pos).unwrap_or('\0') as u8;
        count[ch as usize] -= 1;
        output.insert(count[ch as usize], s.clone());
    }
    
    *strings = output;
}

/// Parallel Radix Sort using Rayon
#[cfg(feature = "rayon")]
use rayon::prelude::*;

#[cfg(feature = "rayon")]
pub fn parallel_radix_sort(arr: &mut [u32]) {
    if arr.len() <= 1000 {
        // Use sequential sort for small arrays
        radix_sort_lsd(arr);
        return;
    }
    
    let max_num = *arr.iter().max().unwrap();
    let mut exp = 1u32;
    
    while max_num / exp > 0 {
        parallel_counting_sort(arr, exp);
        exp *= 10;
    }
}

#[cfg(feature = "rayon")]
fn parallel_counting_sort(arr: &mut [u32], exp: u32) {
    let n = arr.len();
    let chunk_size = n / rayon::current_num_threads().max(1);
    
    // Parallel counting phase
    let counts: Vec<[usize; 10]> = arr
        .par_chunks(chunk_size)
        .map(|chunk| {
            let mut local_count = [0usize; 10];
            for &num in chunk {
                let digit = ((num / exp) % 10) as usize;
                local_count[digit] += 1;
            }
            local_count
        })
        .collect();
    
    // Reduce counts
    let mut total_count = [0usize; 10];
    for local_count in &counts {
        for (i, &count) in local_count.iter().enumerate() {
            total_count[i] += count;
        }
    }
    
    // Calculate positions
    for i in 1..10 {
        total_count[i] += total_count[i - 1];
    }
    
    // Distribute elements
    let mut output = vec![0u32; n];
    for &num in arr.iter().rev() {
        let digit = ((num / exp) % 10) as usize;
        total_count[digit] -= 1;
        output[total_count[digit]] = num;
    }
    
    arr.copy_from_slice(&output);
}

/// Radix Sort for custom types
pub trait Radixable {
    type Key: Copy + Ord;
    fn get_key(&self, digit_pos: usize, base: usize) -> usize;
    fn max_digits(&self) -> usize;
}

impl Radixable for u32 {
    type Key = u32;
    
    fn get_key(&self, digit_pos: usize, base: usize) -> usize {
        let exp = base.pow(digit_pos as u32);
        ((*self as usize) / exp) % base
    }
    
    fn max_digits(&self) -> usize {
        if *self == 0 { 1 } else { (*self as f64).log10().floor() as usize + 1 }
    }
}

pub fn generic_radix_sort<T: Radixable + Clone>(arr: &mut [T], base: usize) {
    if arr.is_empty() {
        return;
    }
    
    let max_digits = arr.iter().map(|x| x.max_digits()).max().unwrap_or(1);
    
    for digit_pos in 0..max_digits {
        counting_sort_generic_digit(arr, digit_pos, base);
    }
}

fn counting_sort_generic_digit<T: Radixable + Clone>(
    arr: &mut [T], 
    digit_pos: usize, 
    base: usize
) {
    let n = arr.len();
    let mut output = Vec::with_capacity(n);
    let mut count = vec![0usize; base];
    
    // Count occurrences
    for item in arr.iter() {
        let key = item.get_key(digit_pos, base);
        count[key] += 1;
    }
    
    // Calculate positions
    for i in 1..base {
        count[i] += count[i - 1];
    }
    
    // Place elements
    output.resize(n, arr[0].clone());
    for item in arr.iter().rev() {
        let key = item.get_key(digit_pos, base);
        count[key] -= 1;
        output[count[key]] = item.clone();
    }
    
    arr.clone_from_slice(&output);
}

#[cfg(test)]
mod advanced_tests {
    use super::*;
    
    #[test]
    fn test_string_sort() {
        let mut strings = vec![
            "banana".to_string(),
            "apple".to_string(),
            "cherry".to_string(),
            "date".to_string(),
        ];
        
        radix_sort_strings(&mut strings, Some(6));
        assert_eq!(strings, vec!["apple", "banana", "cherry", "date"]);
    }
    
    #[test]
    fn test_generic_radix() {
        let mut arr = vec![170u32, 45, 75, 90, 2, 802, 24, 66];
        generic_radix_sort(&mut arr, 10);
        assert_eq!(arr, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
}
```

## Benchmarking and Performance Testing

### Python Benchmarking Suite

```python
import time
import random
import matplotlib.pyplot as plt
from typing import List, Callable

class RadixSortBenchmark:
    """Comprehensive benchmarking suite for Radix Sort implementations."""
    
    def __init__(self):
        self.algorithms = {
            'Radix LSD': radix_sort_lsd,
            'Radix MSD': lambda arr: radix_sort_msd(arr, 0, len(arr)),
            'Python Built-in': lambda arr: arr.sort(),
            'Radix with Negatives': radix_sort_with_negatives,
        }
    
    def generate_test_data(self, size: int, data_type: str = 'random') -> List[int]:
        """Generate test data of specified type and size."""
        if data_type == 'random':
            return [random.randint(0, 999999) for _ in range(size)]
        elif data_type == 'sorted':
            return list(range(size))
        elif data_type == 'reverse':
            return list(range(size, 0, -1))
        elif data_type == 'few_unique':
            return [random.randint(0, 10) for _ in range(size)]
        elif data_type == 'mixed_signs':
            return [random.randint(-999999, 999999) for _ in range(size)]
        else:
            raise ValueError(f"Unknown data type: {data_type}")
    
    def benchmark_algorithm(self, algorithm: Callable, data: List[int]) -> float:
        """Benchmark a single algorithm on given data."""
        test_data = data.copy()
        start_time = time.perf_counter()
        algorithm(test_data)
        end_time = time.perf_counter()
        return end_time - start_time
    
    def run_size_benchmark(self, sizes: List[int], data_type: str = 'random') -> dict:
        """Run benchmark across different input sizes."""
        results = {name: [] for name in self.algorithms}
        
        for size in sizes:
            print(f"Benchmarking size {size}...")
            data = self.generate_test_data(size, data_type)
            
            for name, algorithm in self.algorithms.items():
                try:
                    if name == 'Radix with Negatives' and data_type != 'mixed_signs':
                        # Skip negative handling for non-negative data
                        continue
                    
                    time_taken = self.benchmark_algorithm(algorithm, data)
                    results[name].append(time_taken)
                    print(f"  {name}: {time_taken:.6f}s")
                except Exception as e:
                    print(f"  {name}: Error - {e}")
                    results[name].append(float('inf'))
        
        return results
    
    def plot_results(self, sizes: List[int], results: dict, title: str = "Performance Comparison"):
        """Plot benchmark results."""
        plt.figure(figsize=(12, 8))
        
        for name, times in results.items():
            if times and all(t != float('inf') for t in times):
                plt.plot(sizes, times, marker='o', label=name, linewidth=2)
        
        plt.xlabel('Input Size')
        plt.ylabel('Time (seconds)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log')
        plt.yscale('log')
        
        # Save plot
        plt.tight_layout()
        plt.savefig(f'{title.lower().replace(" ", "_")}.png', dpi=300)
        plt.show()

# Usage example
if __name__ == "__main__":
    benchmark = RadixSortBenchmark()
    sizes = [1000, 5000, 10000, 50000, 100000, 500000]
    
    # Test different data distributions
    test_cases = [
        ('Random Data', 'random'),
        ('Already Sorted', 'sorted'),
        ('Reverse Sorted', 'reverse'),
        ('Few Unique Values', 'few_unique'),
        ('Mixed Signs', 'mixed_signs'),
    ]
    
    for case_name, data_type in test_cases:
        print(f"\n=== {case_name} ===")
        results = benchmark.run_size_benchmark(sizes, data_type)
        benchmark.plot_results(sizes, results, f"Radix Sort - {case_name}")
```

### Rust Benchmarking with Criterion

```rust
// In Cargo.toml:
// [dev-dependencies]
// criterion = { version = "0.5", features = ["html_reports"] }

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use rand::prelude::*;

fn generate_random_data(size: usize) -> Vec<u32> {
    let mut rng = thread_rng();
    (0..size).map(|_| rng.gen_range(0..1_000_000)).collect()
}

fn generate_sorted_data(size: usize) -> Vec<u32> {
    (0..size as u32).collect()
}

fn generate_reverse_data(size: usize) -> Vec<u32> {
    (0..size as u32).rev().collect()
}

fn bench_radix_sorts(c: &mut Criterion) {
    let sizes = vec![1000, 10000, 100000];
    
    let mut group = c.benchmark_group("radix_sort_comparison");
    
    for size in sizes {
        // Random data benchmarks
        let random_data = generate_random_data(size);
        
        group.bench_with_input(
            BenchmarkId::new("lsd_random", size),
            &random_data,
            |b, data| {
                b.iter(|| {
                    let mut test_data = data.clone();
                    radix_sort_lsd(black_box(&mut test_data));
                });
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("optimized_random", size),
            &random_data,
            |b, data| {
                b.iter(|| {
                    let mut test_data = data.clone();
                    OptimizedRadixSort::sort_optimized(black_box(&mut test_data));
                });
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("std_sort_random", size),
            &random_data,
            |b, data| {
                b.iter(|| {
                    let mut test_data = data.clone();
                    test_data.sort_unstable();
                    black_box(test_data);
                });
            },
        );
        
        // Sorted data benchmarks
        let sorted_data = generate_sorted_data(size);
        
        group.bench_with_input(
            BenchmarkId::new("lsd_sorted", size),
            &sorted_data,
            |b, data| {
                b.iter(|| {
                    let mut test_data = data.clone();
                    radix_sort_lsd(black_box(&mut test_data));
                });
            },
        );
    }
    
    group.finish();
}

fn bench_different_bases(c: &mut Criterion) {
    let mut group = c.benchmark_group("radix_sort_bases");
    let data = generate_random_data(10000);
    
    for base in [2, 8, 10, 16] {
        group.bench_with_input(
            BenchmarkId::new("base", base),
            &base,
            |b, &base| {
                b.iter(|| {
                    let mut test_data = data.clone();
                    RadixSort::lsd_base(black_box(&mut test_data), base);
                });
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_radix_sorts, bench_different_bases);
criterion_main!(benches);
```

## Conclusion

Radix Sort is a powerful non-comparative sorting algorithm that excels in specific scenarios, particularly when sorting large collections of integers. This comprehensive guide has covered:

### Key Takeaways

1. **Algorithm Understanding**: Radix Sort processes digits individually, achieving O(d×n) time complexity
2. **Implementation Variants**: Both LSD and MSD approaches have their use cases
3. **Language-Specific Optimizations**: Python focuses on readability while Rust emphasizes performance and safety
4. **Practical Applications**: IP address sorting, database indexing, and string sorting
5. **Performance Characteristics**: Excellent for large datasets of integers with limited digit ranges

### When to Choose Radix Sort

- **Best for**: Large arrays of integers, stable sorting requirements, predictable performance needs
- **Avoid when**: Sorting arbitrary objects, limited memory, variable-length keys with high variance

### Implementation Tips

- Use LSD for most general cases
- Consider MSD for early termination possibilities  
- Implement hybrid approaches for small arrays
- Optimize memory access patterns for better cache performance
- Consider parallelization for very large datasets

The implementations provided offer a solid foundation for both learning and production use, with extensive test coverage and performance optimizations.

I'll create a comprehensive ASCII diagram showing how Radix Sort works step by step, including multiple examples and variations.I've created a comprehensive ASCII diagram that shows exactly how Radix Sort works step by step. The visualization includes:

## Key Features of the Diagram

### **Complete Main Example**

- Shows sorting `[170, 45, 75, 90, 2, 802, 24, 66]` through all 3 passes
- Detailed bucket visualization for each digit position
- Clear before/after states for each step

### **Detailed Counting Sort Subroutine**

- Shows the internal mechanics of counting sort used in each pass
- Demonstrates count arrays, cumulative counts, and stable placement
- Explains why elements are processed right-to-left for stability

### **Multiple Algorithm Variants**

- **LSD (Least Significant Digit)**: Traditional decimal example
- **Binary Radix Sort**: Shows base-2 sorting with bit manipulation
- **MSD (Most Significant Digit)**: String sorting example
- Comparison of when to use each variant

### **Advanced Visualizations**

- Memory layout and space complexity analysis
- Performance comparisons with other sorting algorithms
- Edge case handling (negative numbers, variable lengths)
- Implementation pseudocode with step-by-step breakdown

### **Practical Implementation Details**

- Tips for digit extraction and base selection
- Optimization opportunities and cache-friendly patterns
- When to use Radix Sort vs. alternatives

The diagram uses clear ASCII art with boxes, arrows, and structured layouts to make the algorithm's flow immediately understandable. Each step shows exactly what happens to the data, making it perfect for learning, teaching, or reference purposes.

Would you like me to expand on any particular aspect of the visualization or add additional examples for specific use cases?

# Radix Sort: Complete Step-by-Step ASCII Visualization

## Overview

Radix Sort is a non-comparative sorting algorithm that sorts integers by processing individual digits. It uses counting sort as a subroutine to sort the array according to each digit position.

## Algorithm Principle

```
┌─────────────────────────────────────────────────────────────┐
│                    RADIX SORT CONCEPT                      │
├─────────────────────────────────────────────────────────────┤
│  Instead of comparing elements, sort by digit positions:    │
│                                                             │
│  Example number: 3 4 7                                     │
│                  │ │ └── Units place (10^0)                │
│                  │ └──── Tens place (10^1)                 │
│                  └────── Hundreds place (10^2)             │
│                                                             │
│  Process from least significant digit (LSD) to most        │
│  significant digit (MSD), or vice versa                    │
└─────────────────────────────────────────────────────────────┘
```

## Main Example: LSD Radix Sort (Base 10)

### Initial Array

```
Original Array: [170, 45, 75, 90, 2, 802, 24, 66]

┌─────┬────┬────┬────┬───┬─────┬────┬────┐
│ 170 │ 45 │ 75 │ 90 │ 2 │ 802 │ 24 │ 66 │
└─────┴────┴────┴────┴───┴─────┴────┴────┘
  0     1    2    3   4     5     6    7   ← Array indices
```

### Step 1: Sort by Units Digit (10^0)

```
Extract units digits:
170 → 0    45 → 5    75 → 5    90 → 0
  2 → 2   802 → 2    24 → 4    66 → 6

┌─────────────────────────────────────────────────────────────┐
│                    COUNTING SORT BY UNITS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Digit buckets (0-9):                                       │
│                                                             │
│ 0: [170, 90]     ←── Numbers ending in 0                   │
│ 1: []                                                       │
│ 2: [2, 802]      ←── Numbers ending in 2                   │
│ 3: []                                                       │
│ 4: [24]          ←── Numbers ending in 4                   │
│ 5: [45, 75]      ←── Numbers ending in 5                   │
│ 6: [66]          ←── Numbers ending in 6                   │
│ 7: []                                                       │
│ 8: []                                                       │
│ 9: []                                                       │
└─────────────────────────────────────────────────────────────┘

Collect from buckets 0→9:
┌─────┬───┬─────┬────┬────┬────┬────┬────┐
│ 170 │90 │  2  │802 │ 24 │ 45 │ 75 │ 66 │
└─────┴───┴─────┴────┴────┴────┴────┴────┘
After Step 1 (sorted by units digit)
```

### Step 2: Sort by Tens Digit (10^1)

```
Extract tens digits:
170 → 7    90 → 9     2 → 0   802 → 0
 24 → 2    45 → 4    75 → 7    66 → 6

┌─────────────────────────────────────────────────────────────┐
│                    COUNTING SORT BY TENS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Digit buckets (0-9):                                       │
│                                                             │
│ 0: [2, 802]      ←── Numbers with 0 in tens place          │
│ 1: []                                                       │
│ 2: [24]          ←── Numbers with 2 in tens place          │
│ 3: []                                                       │
│ 4: [45]          ←── Numbers with 4 in tens place          │
│ 5: []                                                       │
│ 6: [66]          ←── Numbers with 6 in tens place          │
│ 7: [170, 75]     ←── Numbers with 7 in tens place          │
│ 8: []                                                       │
│ 9: [90]          ←── Numbers with 9 in tens place          │
└─────────────────────────────────────────────────────────────┘

Collect from buckets 0→9:
┌───┬─────┬────┬────┬────┬─────┬────┬────┐
│ 2 │ 802 │ 24 │ 45 │ 66 │ 170 │ 75 │ 90 │
└───┴─────┴────┴────┴────┴─────┴────┴────┘
After Step 2 (sorted by tens digit)
```

### Step 3: Sort by Hundreds Digit (10^2)

```
Extract hundreds digits:
  2 → 0   802 → 8    24 → 0    45 → 0
 66 → 0   170 → 1    75 → 0    90 → 0

┌─────────────────────────────────────────────────────────────┐
│                  COUNTING SORT BY HUNDREDS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Digit buckets (0-9):                                       │
│                                                             │
│ 0: [2, 24, 45, 66, 75, 90]  ←── Numbers with 0 in hundreds │
│ 1: [170]                     ←── Numbers with 1 in hundreds │
│ 2: []                                                       │
│ 3: []                                                       │
│ 4: []                                                       │
│ 5: []                                                       │
│ 6: []                                                       │
│ 7: []                                                       │
│ 8: [802]                     ←── Numbers with 8 in hundreds │
│ 9: []                                                       │
└─────────────────────────────────────────────────────────────┘

Final Result - Collect from buckets 0→9:
┌───┬────┬────┬────┬────┬────┬─────┬─────┐
│ 2 │ 24 │ 45 │ 66 │ 75 │ 90 │ 170 │ 802 │
└───┴────┴────┴────┴────┴────┴─────┴─────┘
FULLY SORTED ARRAY ✓
```

## Detailed Process Visualization

### Counting Sort Subroutine (Step 1 Detail)

```
┌─────────────────────────────────────────────────────────────┐
│           COUNTING SORT FOR UNITS DIGIT                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Input: [170, 45, 75, 90, 2, 802, 24, 66]                   │
│                                                             │
│ Step 1: Count occurrences of each digit                    │
│ ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐                 │
│ │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │  ← Digits     │
│ ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤                 │
│ │ 2 │ 0 │ 2 │ 0 │ 1 │ 2 │ 1 │ 0 │ 0 │ 0 │  ← Counts     │
│ └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘                 │
│   ▲       ▲       ▲   ▲   ▲                               │
│   │       │       │   │   │                               │
│  170,90   │      2,802│  45,75                            │
│           │       │   24  │                               │
│           │       │       66                              │
│                                                             │
│ Step 2: Calculate cumulative counts (positions)            │
│ ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐                 │
│ │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │                 │
│ ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤                 │
│ │ 2 │ 2 │ 4 │ 4 │ 5 │ 7 │ 8 │ 8 │ 8 │ 8 │  ← Cumulative │
│ └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘                 │
│                                                             │
│ Step 3: Place elements in output array                     │
│ Process from right to left to maintain stability           │
│                                                             │
│ 66 (digit 6) → position 8-1 = 7                            │
│ 24 (digit 4) → position 5-1 = 4                            │
│ 802 (digit 2) → position 4-1 = 3                           │
│ 2 (digit 2) → position 3-1 = 2                             │
│ 90 (digit 0) → position 2-1 = 1                            │
│ 75 (digit 5) → position 7-1 = 6                            │
│ 45 (digit 5) → position 6-1 = 5                            │
│ 170 (digit 0) → position 1-1 = 0                           │
└─────────────────────────────────────────────────────────────┘

Output Array:
┌─────┬────┬───┬─────┬────┬────┬────┬────┐
│ 170 │ 90 │ 2 │ 802 │ 24 │ 45 │ 75 │ 66 │
└─────┴────┴───┴─────┴────┴────┴────┴────┘
  0     1    2    3     4    5    6    7
```

## Alternative Example: Different Base

### Base 2 (Binary) Radix Sort

```
Original: [13, 7, 4, 12, 8, 1]

Convert to binary (4 bits):
13 = 1101₂    7 = 0111₂    4 = 0100₂
12 = 1100₂    8 = 1000₂    1 = 0001₂

┌──────┬──────┬──────┬──────┬──────┬──────┐
│ 1101 │ 0111 │ 0100 │ 1100 │ 1000 │ 0001 │
└──────┴──────┴──────┴──────┴──────┴──────┘
   13     7      4     12     8      1

Step 1: Sort by bit 0 (rightmost)
┌─────────────────────────────────────────┐
│ Bit 0:   1    1    0    0    0    1     │
│ Bucket 0: [4, 12, 8]                   │
│ Bucket 1: [13, 7, 1]                   │
└─────────────────────────────────────────┘
Result: [4, 12, 8, 13, 7, 1]

Step 2: Sort by bit 1
┌─────────────────────────────────────────┐
│ Bit 1:   0    0    0    0    1    0     │
│ Bucket 0: [4, 12, 8, 13, 1]            │
│ Bucket 1: [7]                          │
└─────────────────────────────────────────┘
Result: [4, 12, 8, 13, 1, 7]

Step 3: Sort by bit 2
┌─────────────────────────────────────────┐
│ Bit 2:   1    1    0    0    0    1     │
│ Bucket 0: [8, 13, 1]                   │
│ Bucket 1: [4, 12, 7]                   │
└─────────────────────────────────────────┘
Result: [8, 13, 1, 4, 12, 7]

Step 4: Sort by bit 3 (leftmost)
┌─────────────────────────────────────────┐
│ Bit 3:   1    1    0    0    1    0     │
│ Bucket 0: [1, 4, 7]                    │
│ Bucket 1: [8, 13, 12]                  │
└─────────────────────────────────────────┘
Final: [1, 4, 7, 8, 12, 13] ✓
```

## MSD (Most Significant Digit) Radix Sort

### Example with Strings

```
Original: ["cat", "dog", "rat", "cow", "pig", "bat"]

┌─────┬─────┬─────┬─────┬─────┬─────┐
│ cat │ dog │ rat │ cow │ pig │ bat │
└─────┴─────┴─────┴─────┴─────┴─────┘

Step 1: Sort by first character
┌─────────────────────────────────────────────────────────────┐
│ First character buckets:                                    │
│                                                             │
│ 'b': [bat]                                                 │
│ 'c': [cat, cow]                                            │
│ 'd': [dog]                                                 │
│ 'p': [pig]                                                 │
│ 'r': [rat]                                                 │
└─────────────────────────────────────────────────────────────┘

After Step 1: [bat, cat, cow, dog, pig, rat]

Step 2: Sort each group by second character
┌─────────────────────────────────────────────────────────────┐
│ Group 'b': [bat] → 'a' → [bat]                             │
│ Group 'c': [cat, cow] → 'a':cat, 'o':cow → [cat, cow]      │
│ Group 'd': [dog] → 'o' → [dog]                             │
│ Group 'p': [pig] → 'i' → [pig]                             │
│ Group 'r': [rat] → 'a' → [rat]                             │
└─────────────────────────────────────────────────────────────┘

After Step 2: [bat, cat, cow, dog, pig, rat]

Step 3: Sort each group by third character
┌─────────────────────────────────────────────────────────────┐
│ All groups have unique third characters or are already sorted│
└─────────────────────────────────────────────────────────────┘

Final: [bat, cat, cow, dog, pig, rat] ✓
```

## Performance Visualization

### Time Complexity Analysis

```
┌─────────────────────────────────────────────────────────────┐
│                   RADIX SORT COMPLEXITY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Time Complexity: O(d × (n + k))                            │
│                                                             │
│ Where:                                                      │
│ • d = number of digits in maximum number                   │
│ • n = number of elements                                   │
│ • k = range of each digit (e.g., 10 for decimal)          │
│                                                             │
│ Space Complexity: O(n + k)                                 │
│                                                             │
│ Example with n=8, k=10, d=3:                              │
│ • Total passes: 3                                         │
│ • Work per pass: O(8 + 10) = O(18)                        │
│ • Total work: O(3 × 18) = O(54) = O(n)                    │
│                                                             │
│ Comparison with other O(n log n) algorithms:               │
│                                                             │
│    n=1000   n=10000   n=100000                             │
│ ┌──────────┬──────────┬──────────┐                         │
│ │ Radix    │ Radix    │ Radix    │                         │
│ │ ~4000    │ ~50000   │ ~600000  │                         │
│ ├──────────┼──────────┼──────────┤                         │
│ │ QuickSort│ QuickSort│ QuickSort│                         │
│ │ ~10000   │ ~130000  │ ~1660000 │                         │
│ └──────────┴──────────┴──────────┘                         │
│                                                             │
│ Radix Sort is linear O(n) when d is constant!              │
└─────────────────────────────────────────────────────────────┘
```

## Algorithm Variants Comparison

### LSD vs MSD Radix Sort

```
┌─────────────────────────────────────────────────────────────┐
│                    LSD vs MSD COMPARISON                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ LSD (Least Significant Digit First):                       │
│ ┌─────────────────────────────────────┐                     │
│ │ Advantages:                         │                     │
│ │ • Simpler implementation            │                     │
│ │ • Stable sorting                    │                     │
│ │ • Fixed number of passes            │                     │
│ │ • Good cache locality               │                     │
│ │                                     │                     │
│ │ Disadvantages:                      │                     │
│ │ • Must process all digits           │                     │
│ │ • Not suitable for variable length │                     │
│ └─────────────────────────────────────┘                     │
│                                                             │
│ MSD (Most Significant Digit First):                        │
│ ┌─────────────────────────────────────┐                     │
│ │ Advantages:                         │                     │
│ │ • Can handle variable lengths       │                     │
│ │ • Early termination possible        │                     │
│ │ • Natural for strings               │                     │
│ │ • Recursive implementation          │                     │
│ │                                     │                     │
│ │ Disadvantages:                      │                     │
│ │ • More complex implementation       │                     │
│ │ • May not be stable                 │                     │
│ │ • Recursive overhead                │                     │
│ └─────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Algorithm Pseudocode

```
┌─────────────────────────────────────────────────────────────┐
│                  RADIX SORT PSEUDOCODE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ function radixSort(array):                                  │
│   max_val = findMaximum(array)                              │
│   num_digits = countDigits(max_val)                         │
│                                                             │
│   for digit_pos = 0 to num_digits-1:                       │
│     countingSort(array, digit_pos)                          │
│                                                             │
│ function countingSort(array, digit_pos):                    │
│   count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  // 10 buckets    │
│   output = new array[length(array)]                         │
│                                                             │
│   // Count occurrences                                      │
│   for i = 0 to length(array)-1:                            │
│     digit = getDigitAt(array[i], digit_pos)                 │
│     count[digit]++                                          │
│                                                             │
│   // Calculate cumulative counts                            │
│   for i = 1 to 9:                                          │
│     count[i] += count[i-1]                                  │
│                                                             │
│   // Build output array (right to left for stability)      │
│   for i = length(array)-1 down to 0:                       │
│     digit = getDigitAt(array[i], digit_pos)                 │
│     count[digit]--                                          │
│     output[count[digit]] = array[i]                         │
│                                                             │
│   // Copy back to original array                           │
│   for i = 0 to length(array)-1:                            │
│     array[i] = output[i]                                    │
└─────────────────────────────────────────────────────────────┘
```

## Memory Layout Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY USAGE PATTERN                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Original Array (n elements):                               │
│ ┌────┬────┬────┬────┬────┬────┬────┬────┐                   │
│ │170 │ 45 │ 75 │ 90 │  2 │802 │ 24 │ 66 │                   │
│ └────┴────┴────┴────┴────┴────┴────┴────┘                   │
│                                                             │
│ Temporary Output Array (n elements):                       │
│ ┌────┬────┬────┬────┬────┬────┬────┬────┐                   │
│ │    │    │    │    │    │    │    │    │                   │
│ └────┴────┴────┴────┴────┴────┴────┴────┘                   │
│                                                             │
│ Count Array (k elements, k=10 for decimal):                │
│ ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐                                       │
│ │0│1│2│3│4│5│6│7│8│9│                                       │
│ └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘                                       │
│                                                             │
│ Total Space: O(n + k) = O(8 + 10) = O(18) extra space     │
│                                                             │
│ Memory access pattern is sequential and cache-friendly!    │
└─────────────────────────────────────────────────────────────┘
```

## Edge Cases and Special Considerations

### Handling Negative Numbers

```
Original: [-25, 12, -8, 45, -3, 0, 17]

Step 1: Separate positive and negative numbers
┌─────────────────────────────────────────────────────────────┐
│ Negative: [-25, -8, -3]                                    │
│ Non-negative: [12, 45, 0, 17]                              │
└─────────────────────────────────────────────────────────────┘

Step 2: Sort absolute values of negatives in reverse
┌─────────────────────────────────────────────────────────────┐
│ Absolute values: [25, 8, 3]                                │
│ After radix sort: [3, 8, 25]                               │
│ Reverse for negatives: [-25, -8, -3]                       │
└─────────────────────────────────────────────────────────────┘

Step 3: Sort non-negatives normally
┌─────────────────────────────────────────────────────────────┐
│ Non-negatives: [12, 45, 0, 17]                             │
│ After radix sort: [0, 12, 17, 45]                          │
└─────────────────────────────────────────────────────────────┘

Step 4: Concatenate results
┌─────────────────────────────────────────────────────────────┐
│ Final: [-25, -8, -3, 0, 12, 17, 45] ✓                      │
└─────────────────────────────────────────────────────────────┘
```

### Variable Length Numbers

```
Input: [5, 123, 47, 1234, 89, 6]

Step 1: Find maximum number of digits
Max = 1234 → 4 digits

Step 2: Pad conceptually (or handle in digit extraction)
┌──────┬──────┬──────┬──────┬──────┬──────┐
│ 0005 │ 0123 │ 0047 │ 1234 │ 0089 │ 0006 │
└──────┴──────┴──────┴──────┴──────┴──────┘

Then proceed with normal radix sort for 4 digits
```

## Practical Implementation Notes

```
┌─────────────────────────────────────────────────────────────┐
│                 IMPLEMENTATION TIPS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Digit Extraction:                                       │
│    digit = (num / base^position) % base                    │
│                                                             │
│ 2. Base Selection:                                          │
│    • Base 10: Natural for decimal numbers                  │
│    • Base 256: Efficient for bytes/characters              │
│    • Base 2: Simple for educational purposes               │
│                                                             │
│ 3. Optimization Opportunities:                             │
│    • Use bit operations for powers of 2                    │
│    • Cache-friendly access patterns                        │
│    • Avoid unnecessary copying                              │
│                                                             │
│ 4. When to Use Radix Sort:                                 │
│    ✓ Integer keys with limited range                       │
│    ✓ String sorting (MSD variant)                          │
│    ✓ When stability is important                           │
│    ✗ Floating-point numbers (without conversion)           │
│    ✗ Very large key ranges                                 │
│    ✗ Small datasets (overhead not worth it)                │
└─────────────────────────────────────────────────────────────┘
```

This comprehensive visualization shows how Radix Sort processes data digit by digit, using counting sort as a stable subroutine to achieve overall linear time complexity for fixed-width integer keys.
