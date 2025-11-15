# Comprehensive Guide to Kadane's Algorithm

## Overview

Kadane's Algorithm is an elegant dynamic programming solution for the **Maximum Subarray Problem**: finding the contiguous subarray within a one-dimensional numeric array that has the largest sum.

**Time Complexity:** O(n)  
**Space Complexity:** O(1)

## The Problem

Given an array of integers (which may include negative numbers), find the contiguous subarray with the maximum sum.

**Example:**
```
Array: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
Maximum subarray: [4, -1, 2, 1]
Maximum sum: 6
```

## Core Intuition

The algorithm is based on a simple observation: at each position, we decide whether to:
1. **Extend** the existing subarray by adding the current element
2. **Start fresh** from the current element

We make this choice by comparing:
- `current_sum + arr[i]` (extend)
- `arr[i]` (start fresh)

We take whichever is larger. Additionally, we track the maximum sum seen so far across all positions.

## Mathematical Foundation

The algorithm maintains two values:
- **max_ending_here**: Maximum sum of subarray ending at current position
- **max_so_far**: Maximum sum found so far (global maximum)

At each index `i`:
```
max_ending_here = max(arr[i], max_ending_here + arr[i])
max_so_far = max(max_so_far, max_ending_here)
```

## Step-by-Step Example

Let's trace through `[-2, 1, -3, 4, -1, 2, 1, -5, 4]`:

```
Index | Value | max_ending_here          | max_so_far
------|-------|--------------------------|------------
  0   |  -2   | max(-2, -2) = -2        | -2
  1   |   1   | max(1, -2+1) = 1        | 1
  2   |  -3   | max(-3, 1-3) = -2       | 1
  3   |   4   | max(4, -2+4) = 4        | 4
  4   |  -1   | max(-1, 4-1) = 3        | 4
  5   |   2   | max(2, 3+2) = 5         | 5
  6   |   1   | max(1, 5+1) = 6         | 6
  7   |  -5   | max(-5, 6-5) = 1        | 6
  8   |   4   | max(4, 1+4) = 5         | 6

Result: 6
```

## Implementation: Python
def kadane_basic(arr):
    """
    Basic Kadane's Algorithm - returns maximum sum only.
    
    Args:
        arr: List of integers
    
    Returns:
        Maximum subarray sum
    """
    if not arr:
        return 0
    
    max_ending_here = max_so_far = arr[0]
    
    for i in range(1, len(arr)):
        max_ending_here = max(arr[i], max_ending_here + arr[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far


def kadane_with_indices(arr):
    """
    Kadane's Algorithm with subarray indices tracking.
    
    Args:
        arr: List of integers
    
    Returns:
        Tuple of (max_sum, start_index, end_index)
    """
    if not arr:
        return 0, -1, -1
    
    max_ending_here = max_so_far = arr[0]
    start = end = 0
    temp_start = 0
    
    for i in range(1, len(arr)):
        # If starting fresh is better
        if arr[i] > max_ending_here + arr[i]:
            max_ending_here = arr[i]
            temp_start = i
        else:
            max_ending_here = max_ending_here + arr[i]
        
        # Update global maximum
        if max_ending_here > max_so_far:
            max_so_far = max_ending_here
            start = temp_start
            end = i
    
    return max_so_far, start, end


def kadane_all_negative(arr):
    """
    Handles case where all elements might be negative.
    Returns the least negative number if all are negative.
    
    Args:
        arr: List of integers
    
    Returns:
        Maximum subarray sum (or least negative if all negative)
    """
    if not arr:
        return 0
    
    max_ending_here = arr[0]
    max_so_far = arr[0]
    
    for i in range(1, len(arr)):
        max_ending_here = max(arr[i], max_ending_here + arr[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far


def kadane_circular(arr):
    """
    Kadane's for circular array (where end connects to beginning).
    Maximum subarray can wrap around.
    
    Strategy: 
    1. Find max subarray sum (normal Kadane's)
    2. Find min subarray sum (inverted Kadane's)
    3. Max circular = total_sum - min_subarray_sum
    4. Return max of (normal max, circular max)
    
    Args:
        arr: List of integers
    
    Returns:
        Maximum circular subarray sum
    """
    if not arr:
        return 0
    
    # Case 1: Maximum subarray sum using standard Kadane's
    max_kadane = kadane_basic(arr)
    
    # Case 2: Maximum subarray sum in circular manner
    # Find minimum subarray sum and subtract from total
    total_sum = sum(arr)
    
    # Invert array and find max (which gives us min of original)
    max_ending_here = min_so_far = arr[0]
    for i in range(1, len(arr)):
        max_ending_here = min(arr[i], max_ending_here + arr[i])
        min_so_far = min(min_so_far, max_ending_here)
    
    max_circular = total_sum - min_so_far
    
    # Edge case: if all numbers are negative, max_circular will be 0
    # In that case, return max_kadane
    if max_circular == 0:
        return max_kadane
    
    return max(max_kadane, max_circular)


# Test cases
if __name__ == "__main__":
    test_cases = [
        [-2, 1, -3, 4, -1, 2, 1, -5, 4],  # Expected: 6
        [1, 2, 3, 4, 5],                   # Expected: 15
        [-1, -2, -3, -4],                  # Expected: -1
        [5, -3, 5],                        # Expected: 7
        []                                 # Expected: 0
    ]
    
    for arr in test_cases:
        print(f"Array: {arr}")
        print(f"  Max sum: {kadane_basic(arr)}")
        max_sum, start, end = kadane_with_indices(arr)
        if start != -1:
            print(f"  Subarray: {arr[start:end+1]} (indices {start} to {end})")
        print()
    
    # Circular array test
    circular_arr = [8, -1, 3, 4]
    print(f"Circular array: {circular_arr}")
    print(f"  Max circular sum: {kadane_circular(circular_arr)}")  # Expected: 15 (4+8-1+3)
## Implementation: Rust
/// Basic Kadane's Algorithm - returns maximum sum only
fn kadane_basic(arr: &[i32]) -> i32 {
    if arr.is_empty() {
        return 0;
    }
    
    let mut max_ending_here = arr[0];
    let mut max_so_far = arr[0];
    
    for &num in arr.iter().skip(1) {
        max_ending_here = num.max(max_ending_here + num);
        max_so_far = max_so_far.max(max_ending_here);
    }
    
    max_so_far
}

/// Kadane's Algorithm with subarray indices tracking
/// Returns (max_sum, start_index, end_index)
fn kadane_with_indices(arr: &[i32]) -> (i32, usize, usize) {
    if arr.is_empty() {
        return (0, 0, 0);
    }
    
    let mut max_ending_here = arr[0];
    let mut max_so_far = arr[0];
    let mut start = 0;
    let mut end = 0;
    let mut temp_start = 0;
    
    for (i, &num) in arr.iter().enumerate().skip(1) {
        // If starting fresh is better
        if num > max_ending_here + num {
            max_ending_here = num;
            temp_start = i;
        } else {
            max_ending_here += num;
        }
        
        // Update global maximum
        if max_ending_here > max_so_far {
            max_so_far = max_ending_here;
            start = temp_start;
            end = i;
        }
    }
    
    (max_so_far, start, end)
}

/// Generic version that works with any numeric type
fn kadane_generic<T>(arr: &[T]) -> T 
where
    T: Copy + std::cmp::Ord + std::ops::Add<Output = T>,
{
    assert!(!arr.is_empty(), "Array cannot be empty");
    
    let mut max_ending_here = arr[0];
    let mut max_so_far = arr[0];
    
    for &num in arr.iter().skip(1) {
        max_ending_here = num.max(max_ending_here + num);
        max_so_far = max_so_far.max(max_ending_here);
    }
    
    max_so_far
}

/// Kadane's for circular array
fn kadane_circular(arr: &[i32]) -> i32 {
    if arr.is_empty() {
        return 0;
    }
    
    // Case 1: Maximum subarray sum using standard Kadane's
    let max_kadane = kadane_basic(arr);
    
    // Case 2: Maximum subarray sum in circular manner
    let total_sum: i32 = arr.iter().sum();
    
    // Find minimum subarray sum
    let mut max_ending_here = arr[0];
    let mut min_so_far = arr[0];
    
    for &num in arr.iter().skip(1) {
        max_ending_here = num.min(max_ending_here + num);
        min_so_far = min_so_far.min(max_ending_here);
    }
    
    let max_circular = total_sum - min_so_far;
    
    // Edge case: if all numbers are negative
    if max_circular == 0 {
        return max_kadane;
    }
    
    max_kadane.max(max_circular)
}

/// Iterator-based functional approach
fn kadane_functional(arr: &[i32]) -> i32 {
    if arr.is_empty() {
        return 0;
    }
    
    arr.iter()
        .skip(1)
        .fold((arr[0], arr[0]), |(max_here, max_so_far), &num| {
            let new_max_here = num.max(max_here + num);
            let new_max_so_far = max_so_far.max(new_max_here);
            (new_max_here, new_max_so_far)
        })
        .1
}

/// Returns the actual subarray with maximum sum
fn kadane_return_subarray(arr: &[i32]) -> Vec<i32> {
    if arr.is_empty() {
        return vec![];
    }
    
    let (_, start, end) = kadane_with_indices(arr);
    arr[start..=end].to_vec()
}

fn main() {
    let test_cases = vec![
        vec![-2, 1, -3, 4, -1, 2, 1, -5, 4],  // Expected: 6
        vec![1, 2, 3, 4, 5],                   // Expected: 15
        vec![-1, -2, -3, -4],                  // Expected: -1
        vec![5, -3, 5],                        // Expected: 7
    ];
    
    for arr in &test_cases {
        println!("Array: {:?}", arr);
        println!("  Max sum: {}", kadane_basic(arr));
        
        let (max_sum, start, end) = kadane_with_indices(arr);
        println!("  Subarray: {:?} (indices {} to {})", 
                 &arr[start..=end], start, end);
        
        println!("  Functional approach: {}", kadane_functional(arr));
        println!();
    }
    
    // Circular array test
    let circular_arr = vec![8, -1, 3, 4];
    println!("Circular array: {:?}", circular_arr);
    println!("  Max circular sum: {}", kadane_circular(&circular_arr)); // Expected: 15
    
    // Generic version with i64
    let arr_i64: Vec<i64> = vec![1, 2, 3, 4, 5];
    println!("\nGeneric i64: {:?}", arr_i64);
    println!("  Max sum: {}", kadane_generic(&arr_i64));
}
## Implementation: Go## Advanced Variations
package main

import (
	"fmt"
	"math"
)

// KadaneBasic returns the maximum subarray sum
func KadaneBasic(arr []int) int {
	if len(arr) == 0 {
		return 0
	}

	maxEndingHere := arr[0]
	maxSoFar := arr[0]

	for i := 1; i < len(arr); i++ {
		maxEndingHere = max(arr[i], maxEndingHere+arr[i])
		maxSoFar = max(maxSoFar, maxEndingHere)
	}

	return maxSoFar
}

// KadaneWithIndices returns the maximum sum and the start/end indices
func KadaneWithIndices(arr []int) (maxSum, start, end int) {
	if len(arr) == 0 {
		return 0, -1, -1
	}

	maxEndingHere := arr[0]
	maxSoFar := arr[0]
	start = 0
	end = 0
	tempStart := 0

	for i := 1; i < len(arr); i++ {
		// If starting fresh is better
		if arr[i] > maxEndingHere+arr[i] {
			maxEndingHere = arr[i]
			tempStart = i
		} else {
			maxEndingHere = maxEndingHere + arr[i]
		}

		// Update global maximum
		if maxEndingHere > maxSoFar {
			maxSoFar = maxEndingHere
			start = tempStart
			end = i
		}
	}

	return maxSoFar, start, end
}

// KadaneCircular finds maximum subarray sum in a circular array
func KadaneCircular(arr []int) int {
	if len(arr) == 0 {
		return 0
	}

	// Case 1: Maximum subarray sum using standard Kadane's
	maxKadane := KadaneBasic(arr)

	// Case 2: Maximum subarray sum in circular manner
	totalSum := 0
	for _, num := range arr {
		totalSum += num
	}

	// Find minimum subarray sum
	maxEndingHere := arr[0]
	minSoFar := arr[0]

	for i := 1; i < len(arr); i++ {
		maxEndingHere = min(arr[i], maxEndingHere+arr[i])
		minSoFar = min(minSoFar, maxEndingHere)
	}

	maxCircular := totalSum - minSoFar

	// Edge case: if all numbers are negative
	if maxCircular == 0 {
		return maxKadane
	}

	return max(maxKadane, maxCircular)
}

// KadaneReturnSubarray returns the actual subarray with maximum sum
func KadaneReturnSubarray(arr []int) []int {
	if len(arr) == 0 {
		return []int{}
	}

	_, start, end := KadaneWithIndices(arr)
	return arr[start : end+1]
}

// KadaneGeneric works with any numeric type using generics (Go 1.18+)
func KadaneGeneric[T int | int32 | int64 | float64](arr []T) T {
	if len(arr) == 0 {
		return 0
	}

	maxEndingHere := arr[0]
	maxSoFar := arr[0]

	for i := 1; i < len(arr); i++ {
		if arr[i] > maxEndingHere+arr[i] {
			maxEndingHere = arr[i]
		} else {
			maxEndingHere = maxEndingHere + arr[i]
		}

		if maxEndingHere > maxSoFar {
			maxSoFar = maxEndingHere
		}
	}

	return maxSoFar
}

// KadaneWithCallback allows custom processing during iteration
func KadaneWithCallback(arr []int, callback func(index, currentSum, maxSum int)) int {
	if len(arr) == 0 {
		return 0
	}

	maxEndingHere := arr[0]
	maxSoFar := arr[0]

	callback(0, maxEndingHere, maxSoFar)

	for i := 1; i < len(arr); i++ {
		maxEndingHere = max(arr[i], maxEndingHere+arr[i])
		maxSoFar = max(maxSoFar, maxEndingHere)
		callback(i, maxEndingHere, maxSoFar)
	}

	return maxSoFar
}

// KadaneMinSubarray finds the minimum subarray sum (inverse problem)
func KadaneMinSubarray(arr []int) int {
	if len(arr) == 0 {
		return 0
	}

	minEndingHere := arr[0]
	minSoFar := arr[0]

	for i := 1; i < len(arr); i++ {
		minEndingHere = min(arr[i], minEndingHere+arr[i])
		minSoFar = min(minSoFar, minEndingHere)
	}

	return minSoFar
}

// Helper functions
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	testCases := [][]int{
		{-2, 1, -3, 4, -1, 2, 1, -5, 4}, // Expected: 6
		{1, 2, 3, 4, 5},                  // Expected: 15
		{-1, -2, -3, -4},                 // Expected: -1
		{5, -3, 5},                       // Expected: 7
	}

	for _, arr := range testCases {
		fmt.Printf("Array: %v\n", arr)
		fmt.Printf("  Max sum: %d\n", KadaneBasic(arr))

		maxSum, start, end := KadaneWithIndices(arr)
		fmt.Printf("  Subarray: %v (indices %d to %d)\n",
			arr[start:end+1], start, end)

		fmt.Printf("  Min subarray sum: %d\n", KadaneMinSubarray(arr))
		fmt.Println()
	}

	// Circular array test
	circularArr := []int{8, -1, 3, 4}
	fmt.Printf("Circular array: %v\n", circularArr)
	fmt.Printf("  Max circular sum: %d\n", KadaneCircular(circularArr)) // Expected: 15

	// Generic version with float64
	arrFloat := []float64{1.5, 2.5, 3.5, 4.5, 5.5}
	fmt.Printf("\nGeneric float64: %v\n", arrFloat)
	fmt.Printf("  Max sum: %.1f\n", KadaneGeneric(arrFloat))

	// With callback example
	fmt.Println("\nWith callback (showing each step):")
	arr := []int{-2, 1, -3, 4}
	KadaneWithCallback(arr, func(index, currentSum, maxSum int) {
		fmt.Printf("  Index %d: current_sum=%d, max_sum=%d\n",
			index, currentSum, maxSum)
	})
}
### 1. **2D Kadane's (Maximum Sum Rectangle)**
Extends Kadane's to find maximum sum rectangle in a 2D matrix. Time: O(n²m) where n=rows, m=cols.

### 2. **Kadane's with K Elements**
Find maximum sum subarray with exactly K elements. Requires sliding window approach.

### 3. **Kadane's with Constraints**
- Maximum sum with no adjacent elements
- Maximum sum with at most K deletions
- Maximum sum with length constraints

### 4. **Multiple Subarrays**
Find K non-overlapping subarrays with maximum total sum.

## Common Pitfalls

1. **Empty Array Handling**: Always check if array is empty
2. **All Negative Numbers**: Basic implementation handles this correctly (returns the least negative)
3. **Integer Overflow**: Use appropriate data types for large sums
4. **Index Tracking**: When tracking indices, be careful with the logic for when to reset `temp_start`

## Performance Comparison

| Language | Basic Implementation | With Indices | Circular |
|----------|---------------------|--------------|----------|
| Python   | Clean, readable     | Simple       | Good     |
| Rust     | Most performant     | Zero-cost    | Fastest  |
| Go       | Fast, simple        | Efficient    | Fast     |

## Time & Space Analysis

- **Time Complexity**: O(n) - single pass through array
- **Space Complexity**: O(1) - only constant extra space
- **Optimal**: Yes, this is the optimal solution for the maximum subarray problem

## Real-World Applications

1. **Stock Trading**: Maximum profit from buying and selling stocks
2. **Data Analysis**: Finding trends in time-series data
3. **Image Processing**: Detecting regions of interest
4. **Genomics**: Finding significant gene sequences
5. **Business Analytics**: Identifying most profitable periods

## Key Takeaways

- Kadane's is a classic example of dynamic programming with O(n) time and O(1) space
- The core idea: at each position, decide whether to extend or start fresh
- Can be adapted for circular arrays, 2D matrices, and various constraints
- All three language implementations follow the same logical pattern with language-specific idioms