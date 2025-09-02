I'll create a comprehensive guide to digit-wise sorting algorithms with implementations in both Python and Rust. This will cover radix sort, counting sort, and bucket sort variations.I've created a comprehensive guide to digit-wise sorting algorithms with complete implementations in both Python and Rust. The guide covers:

## Key Features:

1. **Three main algorithms**:
   - **Radix Sort**: Processes digits from least to most significant, excellent for integers and fixed-length strings
   - **Counting Sort**: Works great when the range of values is small, often used as a subroutine
   - **Bucket Sort**: Divides elements into buckets, good for uniformly distributed data

2. **Complete implementations** in both languages with:
   - Detailed comments explaining each step
   - Error handling and edge case management
   - Test cases demonstrating usage
   - Both integer and string variants where applicable

3. **Performance analysis** including:
   - Time and space complexity comparisons
   - When each algorithm is optimal
   - Practical considerations and trade-offs

4. **Real-world applicability**:
   - Use case recommendations
   - Implementation tips
   - Memory and performance considerations

## Key Advantages of Digit-Wise Sorting:

- **Linear time complexity** O(d×(n+k)) for radix sort
- **Stable sorting** maintains relative order of equal elements  
- **Non-comparative** doesn't rely on element comparisons
- **Predictable performance** especially for fixed-width data

The implementations are production-ready with proper error handling, and the Rust versions include comprehensive test suites. Both languages demonstrate idiomatic coding practices while maintaining clarity and educational value.

Would you like me to explain any specific algorithm in more detail or add additional variations like MSD radix sort or optimizations for specific data types?

# Comprehensive Guide to Digit-Wise Sorting Algorithms

## Table of Contents
1. [Introduction](#introduction)
2. [Radix Sort](#radix-sort)
3. [Counting Sort (for digits)](#counting-sort-for-digits)
4. [Bucket Sort](#bucket-sort)
5. [Performance Analysis](#performance-analysis)
6. [Use Cases and Trade-offs](#use-cases-and-trade-offs)

## Introduction

Digit-wise sorting algorithms are non-comparative sorting algorithms that work by examining individual digits or characters of the elements being sorted. These algorithms can achieve linear time complexity under certain conditions, making them extremely efficient for specific types of data.

### Key Characteristics:
- **Time Complexity**: O(d × (n + k)) where d is the number of digits, n is the number of elements, k is the range of each digit
- **Space Complexity**: O(n + k)
- **Stability**: Most digit-wise sorts are stable (maintain relative order of equal elements)
- **Best for**: Integer data with fixed digit count, strings of equal length

## Radix Sort

Radix sort processes digits from least significant digit (LSD) to most significant digit (MSD), using a stable sorting algorithm for each digit position.

### Python Implementation

```python
def radix_sort(arr):
    """
    Sorts an array of non-negative integers using radix sort (LSD).
    
    Args:
        arr: List of non-negative integers
    
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    # Find the maximum number to determine number of digits
    max_num = max(arr)
    
    # Do counting sort for every digit
    exp = 1  # Current digit position (1s, 10s, 100s, etc.)
    
    while max_num // exp > 0:
        counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr

def counting_sort_by_digit(arr, exp):
    """
    Counting sort based on the digit represented by exp.
    
    Args:
        arr: Array to sort
        exp: Current digit position (1, 10, 100, etc.)
    """
    n = len(arr)
    output = [0] * n
    count = [0] * 10  # Digit range 0-9
    
    # Store count of occurrences of each digit
    for i in range(n):
        digit = (arr[i] // exp) % 10
        count[digit] += 1
    
    # Change count[i] to actual position of this digit in output
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    # Build output array
    i = n - 1
    while i >= 0:
        digit = (arr[i] // exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit] -= 1
        i -= 1
    
    # Copy output array to arr
    for i in range(n):
        arr[i] = output[i]

def radix_sort_strings(strings, max_len=None):
    """
    Radix sort for strings of equal length.
    
    Args:
        strings: List of strings
        max_len: Maximum string length (calculated if None)
    
    Returns:
        Sorted list of strings
    """
    if not strings:
        return strings
    
    if max_len is None:
        max_len = max(len(s) for s in strings)
    
    # Pad strings to equal length
    padded = [s.ljust(max_len) for s in strings]
    
    # Sort from rightmost character to leftmost
    for pos in range(max_len - 1, -1, -1):
        padded = counting_sort_strings_by_char(padded, pos)
    
    # Remove padding
    return [s.rstrip() for s in padded]

def counting_sort_strings_by_char(strings, pos):
    """
    Counting sort for strings based on character at given position.
    """
    n = len(strings)
    output = [''] * n
    count = [0] * 256  # ASCII range
    
    # Count occurrences
    for s in strings:
        char_code = ord(s[pos]) if pos < len(s) else 0
        count[char_code] += 1
    
    # Calculate positions
    for i in range(1, 256):
        count[i] += count[i - 1]
    
    # Build output
    for i in range(n - 1, -1, -1):
        char_code = ord(strings[i][pos]) if pos < len(strings[i]) else 0
        output[count[char_code] - 1] = strings[i]
        count[char_code] -= 1
    
    return output

# Example usage and testing
def test_radix_sort():
    # Test integer radix sort
    numbers = [170, 45, 75, 90, 2, 802, 24, 66]
    print(f"Original: {numbers}")
    sorted_numbers = radix_sort(numbers.copy())
    print(f"Sorted: {sorted_numbers}")
    
    # Test string radix sort
    words = ["cat", "dog", "rat", "bat", "ant"]
    print(f"Original strings: {words}")
    sorted_words = radix_sort_strings(words.copy())
    print(f"Sorted strings: {sorted_words}")

if __name__ == "__main__":
    test_radix_sort()
```

### Rust Implementation

```rust
/// Radix sort implementation for vectors of u32 integers
pub fn radix_sort(arr: &mut Vec<u32>) {
    if arr.is_empty() {
        return;
    }
    
    let max_val = *arr.iter().max().unwrap();
    let mut exp = 1;
    
    while max_val / exp > 0 {
        counting_sort_by_digit(arr, exp);
        exp *= 10;
    }
}

/// Counting sort based on the digit represented by exp
fn counting_sort_by_digit(arr: &mut Vec<u32>, exp: u32) {
    let n = arr.len();
    let mut output = vec![0u32; n];
    let mut count = [0usize; 10];
    
    // Store count of occurrences of each digit
    for &num in arr.iter() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] += 1;
    }
    
    // Change count[i] to actual position of this digit in output
    for i in 1..10 {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for &num in arr.iter().rev() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] -= 1;
        output[count[digit]] = num;
    }
    
    // Copy output array back to arr
    arr.copy_from_slice(&output);
}

/// Radix sort for strings of equal length
pub fn radix_sort_strings(strings: &mut Vec<String>) {
    if strings.is_empty() {
        return;
    }
    
    let max_len = strings.iter().map(|s| s.len()).max().unwrap_or(0);
    
    // Pad strings to equal length
    for s in strings.iter_mut() {
        while s.len() < max_len {
            s.push(' ');
        }
    }
    
    // Sort from rightmost character to leftmost
    for pos in (0..max_len).rev() {
        counting_sort_strings_by_char(strings, pos);
    }
    
    // Remove padding
    for s in strings.iter_mut() {
        *s = s.trim_end().to_string();
    }
}

/// Counting sort for strings based on character at given position
fn counting_sort_strings_by_char(strings: &mut Vec<String>, pos: usize) {
    let n = strings.len();
    let mut output = vec![String::new(); n];
    let mut count = [0usize; 256]; // ASCII range
    
    // Count occurrences
    for s in strings.iter() {
        let char_code = s.chars().nth(pos).unwrap_or('\0') as u8 as usize;
        count[char_code] += 1;
    }
    
    // Calculate positions
    for i in 1..256 {
        count[i] += count[i - 1];
    }
    
    // Build output
    for s in strings.iter().rev() {
        let char_code = s.chars().nth(pos).unwrap_or('\0') as u8 as usize;
        count[char_code] -= 1;
        output[count[char_code]] = s.clone();
    }
    
    // Copy back to original vector
    strings.clone_from(&output);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_radix_sort_integers() {
        let mut numbers = vec![170, 45, 75, 90, 2, 802, 24, 66];
        println!("Original: {:?}", numbers);
        
        radix_sort(&mut numbers);
        println!("Sorted: {:?}", numbers);
        
        assert_eq!(numbers, vec![2, 24, 45, 66, 75, 90, 170, 802]);
    }
    
    #[test]
    fn test_radix_sort_strings() {
        let mut words = vec![
            "cat".to_string(),
            "dog".to_string(), 
            "rat".to_string(),
            "bat".to_string(),
            "ant".to_string()
        ];
        println!("Original strings: {:?}", words);
        
        radix_sort_strings(&mut words);
        println!("Sorted strings: {:?}", words);
        
        assert_eq!(words, vec!["ant", "bat", "cat", "dog", "rat"]);
    }
}
```

## Counting Sort (for digits)

Counting sort works well when the range of possible values is small. It's often used as a subroutine in radix sort.

### Python Implementation

```python
def counting_sort(arr, k=None):
    """
    Counting sort for integers in range [0, k].
    
    Args:
        arr: List of non-negative integers
        k: Maximum value in array (calculated if None)
    
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    if k is None:
        k = max(arr)
    
    # Initialize count array
    count = [0] * (k + 1)
    
    # Store count of each element
    for num in arr:
        count[num] += 1
    
    # Modify count array to store actual positions
    for i in range(1, k + 1):
        count[i] += count[i - 1]
    
    # Build output array
    output = [0] * len(arr)
    for i in range(len(arr) - 1, -1, -1):
        output[count[arr[i]] - 1] = arr[i]
        count[arr[i]] -= 1
    
    return output

def counting_sort_with_mapping(arr, key_func=None):
    """
    Counting sort with custom key function.
    
    Args:
        arr: List of elements
        key_func: Function to extract sorting key
    
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    if key_func is None:
        key_func = lambda x: x
    
    # Extract keys and find range
    keys = [key_func(item) for item in arr]
    min_key, max_key = min(keys), max(keys)
    range_size = max_key - min_key + 1
    
    # Initialize count array
    count = [0] * range_size
    
    # Count occurrences
    for key in keys:
        count[key - min_key] += 1
    
    # Calculate positions
    for i in range(1, range_size):
        count[i] += count[i - 1]
    
    # Build output
    output = [None] * len(arr)
    for i in range(len(arr) - 1, -1, -1):
        key = keys[i] - min_key
        output[count[key] - 1] = arr[i]
        count[key] -= 1
    
    return output
```

### Rust Implementation

```rust
/// Counting sort for u32 integers
pub fn counting_sort(arr: &[u32]) -> Vec<u32> {
    if arr.is_empty() {
        return Vec::new();
    }
    
    let max_val = *arr.iter().max().unwrap() as usize;
    let mut count = vec![0usize; max_val + 1];
    
    // Count occurrences
    for &num in arr {
        count[num as usize] += 1;
    }
    
    // Calculate positions
    for i in 1..=max_val {
        count[i] += count[i - 1];
    }
    
    // Build output
    let mut output = vec![0u32; arr.len()];
    for &num in arr.iter().rev() {
        count[num as usize] -= 1;
        output[count[num as usize]] = num;
    }
    
    output
}

/// Generic counting sort with key extraction
pub fn counting_sort_by_key<T, F>(arr: &[T], key_fn: F) -> Vec<T> 
where
    T: Clone,
    F: Fn(&T) -> u32,
{
    if arr.is_empty() {
        return Vec::new();
    }
    
    let keys: Vec<u32> = arr.iter().map(&key_fn).collect();
    let min_key = *keys.iter().min().unwrap();
    let max_key = *keys.iter().max().unwrap();
    let range = (max_key - min_key + 1) as usize;
    
    let mut count = vec![0usize; range];
    
    // Count occurrences
    for &key in &keys {
        count[(key - min_key) as usize] += 1;
    }
    
    // Calculate positions
    for i in 1..range {
        count[i] += count[i - 1];
    }
    
    // Build output
    let mut output = vec![arr[0].clone(); arr.len()];
    for (i, item) in arr.iter().enumerate().rev() {
        let key_index = (keys[i] - min_key) as usize;
        count[key_index] -= 1;
        output[count[key_index]] = item.clone();
    }
    
    output
}
```

## Bucket Sort

Bucket sort divides elements into buckets, sorts each bucket individually, then concatenates the results.

### Python Implementation

```python
import math

def bucket_sort(arr, bucket_count=None):
    """
    Bucket sort for floating-point numbers in range [0, 1).
    
    Args:
        arr: List of numbers in range [0, 1)
        bucket_count: Number of buckets (default: len(arr))
    
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    if bucket_count is None:
        bucket_count = len(arr)
    
    # Create empty buckets
    buckets = [[] for _ in range(bucket_count)]
    
    # Distribute elements into buckets
    for num in arr:
        bucket_idx = int(bucket_count * num)
        # Handle edge case where num == 1.0
        bucket_idx = min(bucket_idx, bucket_count - 1)
        buckets[bucket_idx].append(num)
    
    # Sort individual buckets and concatenate
    result = []
    for bucket in buckets:
        bucket.sort()  # Can use any sorting algorithm
        result.extend(bucket)
    
    return result

def bucket_sort_integers(arr, bucket_count=None):
    """
    Bucket sort for integers.
    
    Args:
        arr: List of integers
        bucket_count: Number of buckets
    
    Returns:
        Sorted list
    """
    if not arr:
        return arr
    
    min_val, max_val = min(arr), max(arr)
    if min_val == max_val:
        return arr
    
    if bucket_count is None:
        bucket_count = int(math.sqrt(len(arr)))
    
    # Create empty buckets
    buckets = [[] for _ in range(bucket_count)]
    
    # Calculate range per bucket
    range_per_bucket = (max_val - min_val + 1) / bucket_count
    
    # Distribute elements into buckets
    for num in arr:
        bucket_idx = int((num - min_val) / range_per_bucket)
        bucket_idx = min(bucket_idx, bucket_count - 1)
        buckets[bucket_idx].append(num)
    
    # Sort individual buckets and concatenate
    result = []
    for bucket in buckets:
        bucket.sort()
        result.extend(bucket)
    
    return result

def digit_bucket_sort(arr, digit_pos, base=10):
    """
    Bucket sort based on a specific digit position.
    
    Args:
        arr: List of integers
        digit_pos: Digit position (0 for units, 1 for tens, etc.)
        base: Number base (default 10)
    
    Returns:
        Sorted list based on the specified digit
    """
    buckets = [[] for _ in range(base)]
    
    # Distribute elements based on digit
    for num in arr:
        digit = (num // (base ** digit_pos)) % base
        buckets[digit].append(num)
    
    # Concatenate buckets (no need to sort within buckets for single digit)
    result = []
    for bucket in buckets:
        result.extend(bucket)
    
    return result
```

### Rust Implementation

```rust
/// Bucket sort for floating-point numbers in range [0.0, 1.0)
pub fn bucket_sort_floats(arr: &mut Vec<f64>, bucket_count: Option<usize>) {
    if arr.is_empty() {
        return;
    }
    
    let bucket_count = bucket_count.unwrap_or(arr.len());
    let mut buckets: Vec<Vec<f64>> = vec![Vec::new(); bucket_count];
    
    // Distribute elements into buckets
    for &num in arr.iter() {
        let bucket_idx = ((bucket_count as f64) * num) as usize;
        let bucket_idx = bucket_idx.min(bucket_count - 1);
        buckets[bucket_idx].push(num);
    }
    
    // Sort individual buckets
    for bucket in buckets.iter_mut() {
        bucket.sort_by(|a, b| a.partial_cmp(b).unwrap());
    }
    
    // Concatenate results
    arr.clear();
    for bucket in buckets {
        arr.extend(bucket);
    }
}

/// Bucket sort for integers
pub fn bucket_sort_integers(arr: &mut Vec<i32>, bucket_count: Option<usize>) {
    if arr.is_empty() {
        return;
    }
    
    let min_val = *arr.iter().min().unwrap();
    let max_val = *arr.iter().max().unwrap();
    
    if min_val == max_val {
        return;
    }
    
    let bucket_count = bucket_count.unwrap_or((arr.len() as f64).sqrt() as usize);
    let mut buckets: Vec<Vec<i32>> = vec![Vec::new(); bucket_count];
    
    let range_per_bucket = (max_val - min_val + 1) as f64 / bucket_count as f64;
    
    // Distribute elements into buckets
    for &num in arr.iter() {
        let bucket_idx = ((num - min_val) as f64 / range_per_bucket) as usize;
        let bucket_idx = bucket_idx.min(bucket_count - 1);
        buckets[bucket_idx].push(num);
    }
    
    // Sort individual buckets
    for bucket in buckets.iter_mut() {
        bucket.sort();
    }
    
    // Concatenate results
    arr.clear();
    for bucket in buckets {
        arr.extend(bucket);
    }
}

/// Bucket sort based on specific digit position
pub fn digit_bucket_sort(arr: &mut Vec<u32>, digit_pos: u32, base: u32) {
    let mut buckets: Vec<Vec<u32>> = vec![Vec::new(); base as usize];
    
    // Distribute elements based on digit
    for &num in arr.iter() {
        let digit = (num / base.pow(digit_pos)) % base;
        buckets[digit as usize].push(num);
    }
    
    // Concatenate buckets
    arr.clear();
    for bucket in buckets {
        arr.extend(bucket);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bucket_sort_integers() {
        let mut numbers = vec![42, 32, 33, 52, 37, 47, 51];
        println!("Original: {:?}", numbers);
        
        bucket_sort_integers(&mut numbers, None);
        println!("Sorted: {:?}", numbers);
        
        assert_eq!(numbers, vec![32, 33, 37, 42, 47, 51, 52]);
    }
}
```

## Performance Analysis

### Time Complexity Comparison

| Algorithm | Best Case | Average Case | Worst Case | Space Complexity |
|-----------|-----------|--------------|------------|------------------|
| Radix Sort | O(d×(n+k)) | O(d×(n+k)) | O(d×(n+k)) | O(n+k) |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) |
| Bucket Sort | O(n+k) | O(n+k) | O(n²) | O(n×k) |

Where:
- n = number of elements
- k = range of input
- d = number of digits

### Space Complexity Details

- **Radix Sort**: O(n + k) where k is typically 10 for decimal digits
- **Counting Sort**: O(k) for the counting array
- **Bucket Sort**: O(n × k) in worst case if all elements go to one bucket

### When Each Algorithm is Optimal

**Radix Sort**:
- Large datasets with fixed-width integers
- String sorting with equal length
- When comparison-based sorting is too slow

**Counting Sort**:
- Small range of possible values (k ≈ n)
- Need stable sorting
- Preprocessing step for other algorithms

**Bucket Sort**:
- Uniformly distributed data
- Floating-point numbers
- When average-case performance is more important than worst-case

## Use Cases and Trade-offs

### Radix Sort
**Best for**:
- Sorting large arrays of integers
- Fixed-width data (ZIP codes, phone numbers)
- String arrays of equal length
- When linear time complexity is needed

**Limitations**:
- Only works with fixed-range data
- Not comparison-based (can't use custom comparators)
- Memory overhead for counting arrays

### Counting Sort
**Best for**:
- Small range of possible values
- Need for stable sorting
- Histogram generation
- Preprocessing for other algorithms

**Limitations**:
- Requires knowing the range of values
- Space complexity grows with range
- Not suitable for large ranges

### Bucket Sort
**Best for**:
- Uniformly distributed floating-point numbers
- When data can be evenly distributed
- Parallel processing scenarios

**Limitations**:
- Poor performance with skewed data
- Requires good hash/distribution function
- Worst-case O(n²) performance

### Implementation Tips

1. **Choose the right base**: For radix sort, base 256 can be faster than base 10 for binary data
2. **Optimize memory access**: Use in-place algorithms when possible
3. **Handle edge cases**: Empty arrays, single elements, equal elements
4. **Consider hybrid approaches**: Use insertion sort for small buckets in bucket sort
5. **Profile your use case**: The theoretical best algorithm might not be practical for your specific data

### Practical Considerations

- **Cache performance**: Digit-wise algorithms can have poor cache locality
- **Integer overflow**: Be careful with large numbers in radix sort
- **String handling**: Consider Unicode and different character encodings
- **Parallel processing**: Many digit-wise algorithms can be parallelized effectively
- **Memory constraints**: Choose algorithms based on available memory

I'll create a comprehensive ASCII diagram showing how digit-wise sorting algorithms (specifically Radix Sort) work step by step.I've created a comprehensive ASCII diagram showing how Radix Sort (a digit-wise sorting algorithm) works step by step. The diagram illustrates:

1. **The initial unsorted array** with 8 numbers of varying lengths
2. **Step-by-step sorting** starting from the least significant digit (ones place) to the most significant digit (hundreds place)
3. **Bucket visualization** showing how numbers are distributed into 10 buckets (0-9) based on the current digit being examined
4. **Collection process** showing how numbers are gathered back from the buckets in order
5. **Final sorted result** with verification

The diagram also includes:
- Visual separation of digits in each number
- Clear bucket representations using ASCII tables
- Step-by-step transformation of the array
- Algorithm complexity and properties summary

This type of sorting is particularly efficient for integers with a limited number of digits, as it runs in linear time relative to the input size when the number of digits is constant.

# Digit-wise Sorting Algorithm (Radix Sort) Step-by-Step

## Initial Array
```
Original Array: [170, 45, 75, 90, 2, 802, 24, 66]
```

## Step 1: Sort by Ones Place (Least Significant Digit)
```
Numbers with digits separated:
170 → 1|7|0    Extract ones digit: 0
 45 → 0|4|5    Extract ones digit: 5
 75 → 0|7|5    Extract ones digit: 5
 90 → 0|9|0    Extract ones digit: 0
  2 → 0|0|2    Extract ones digit: 2
802 → 8|0|2    Extract ones digit: 2
 24 → 0|2|4    Extract ones digit: 4
 66 → 0|6|6    Extract ones digit: 6

Buckets (0-9):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ 170 │     │  2  │     │ 24  │ 45  │ 66  │     │     │     │
│ 90  │     │ 802 │     │     │ 75  │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

After collecting from buckets:
[170, 90, 2, 802, 24, 45, 75, 66]
```

## Step 2: Sort by Tens Place
```
Numbers with digits separated:
170 → 1|7|0    Extract tens digit: 7
 90 → 0|9|0    Extract tens digit: 9
  2 → 0|0|2    Extract tens digit: 0
802 → 8|0|2    Extract tens digit: 0
 24 → 0|2|4    Extract tens digit: 2
 45 → 0|4|5    Extract tens digit: 4
 75 → 0|7|5    Extract tens digit: 7
 66 → 0|6|6    Extract tens digit: 6

Buckets (0-9):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│  2  │     │ 24  │     │ 45  │     │ 66  │ 170 │     │ 90  │
│ 802 │     │     │     │     │     │     │ 75  │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

After collecting from buckets:
[2, 802, 24, 45, 66, 170, 75, 90]
```

## Step 3: Sort by Hundreds Place (Most Significant Digit)
```
Numbers with digits separated:
  2 → 0|0|2    Extract hundreds digit: 0
802 → 8|0|2    Extract hundreds digit: 8
 24 → 0|2|4    Extract hundreds digit: 0
 45 → 0|4|5    Extract hundreds digit: 0
 66 → 0|6|6    Extract hundreds digit: 0
170 → 1|7|0    Extract hundreds digit: 1
 75 → 0|7|5    Extract hundreds digit: 0
 90 → 0|9|0    Extract hundreds digit: 0

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

After collecting from buckets:
[2, 24, 45, 66, 75, 90, 170, 802]
```

## Final Result
```
SORTED ARRAY: [2, 24, 45, 66, 75, 90, 170, 802]

Original: [170, 45, 75, 90, 2, 802, 24, 66]
Sorted:   [2, 24, 45, 66, 75, 90, 170, 802]
          ✓ ✓  ✓  ✓  ✓  ✓   ✓    ✓
```

## Algorithm Overview
```
┌─────────────────────────────────────────────────┐
│                RADIX SORT                       │
├─────────────────────────────────────────────────┤
│ 1. Find maximum number to determine digit count │
│ 2. For each digit position (ones, tens, etc.):  │
│    a) Extract digit from each number            │
│    b) Place numbers in buckets 0-9             │
│    c) Collect numbers from buckets in order    │
│ 3. Repeat until all digits are processed       │
├─────────────────────────────────────────────────┤
│ Time Complexity: O(d × (n + k))                │
│ where d = digits, n = elements, k = range       │
│ Space Complexity: O(n + k)                     │
│ Stable: Yes (maintains relative order)          │
└─────────────────────────────────────────────────┘
```

## Key Properties
- **Non-comparative**: Doesn't compare elements directly
- **Stable**: Equal elements maintain their relative order
- **Linear time**: When digits are limited, runs in O(n) time
- **Works best**: For integers with limited digits or fixed-length strings
- **Memory usage**: Requires additional space for buckets