I'll create a comprehensive, in-depth guide on Cyclic Sort that will serve as your foundational document for mastering this pattern. This will cover everything from first principles to advanced applications.## 🎯 Your Comprehensive Cyclic Sort Mastery Guide is Ready

I've crafted a **deep, rigorous, and complete** guide covering Cyclic Sort from absolute fundamentals to expert-level mastery. This is designed specifically for your journey to the top 1%.

### What's Inside:

**Foundation Layer:**
- First-principles explanation (no assumptions about prior knowledge)
- Core intuition with the "Parking Spot" mental model
- ASCII visualizations and flowcharts for every concept
- Complete mathematical proof of O(n) complexity

**Implementation Excellence:**
- Full implementations in all 5 languages (Python, Rust, C, C++, Go)
- Idiomatic style for each language
- Performance optimizations and safety considerations
- Verbose learning versions with step tracking

**Pattern Mastery:**
- 6 major problem patterns (missing numbers, duplicates, corrupt pairs, etc.)
- Decision tree for instant pattern recognition
- Template code for solving variations
- When to use vs when NOT to use

**Deep Understanding:**
- Step-by-step expert thought process
- Complexity analysis (why O(n), not O(n²))
- Comparison with other sorting algorithms
- Mathematical invariants and proofs

**Cognitive Strategies:**
- Mental models (Index-Value Mapping, Pigeonhole Principle)
- Deliberate practice schedules
- Flow state optimization techniques
- Meta-learning and pattern transfer principles

**Practice Roadmap:**
- 12 problems (Beginner → Expert)
- Common pitfalls with corrections
- Edge case handling
- Mastery checklist

This guide is **your complete reference**—return to it, practice from it, and use it as your foundation as you build toward top 1% mastery.

**Start with:** Read the mental model section, implement the basic algorithm in your preferred language, then solve the first 3 beginner problems. Build from there.

# Cyclic Sort - The Complete Mastery Guide
## From First Principles to Top 1% Understanding

---

## Table of Contents
1. [What is Cyclic Sort?](#what-is-cyclic-sort)
2. [Core Intuition & Mental Model](#core-intuition--mental-model)
3. [The Fundamental Concept](#the-fundamental-concept)
4. [Visual Understanding](#visual-understanding)
5. [Step-by-Step Algorithm](#step-by-step-algorithm)
6. [Implementation Across Languages](#implementation-across-languages)
7. [Complexity Analysis](#complexity-analysis)
8. [Pattern Recognition Framework](#pattern-recognition-framework)
9. [Problem-Solving Methodology](#problem-solving-methodology)
10. [Common Problem Patterns](#common-problem-patterns)
11. [Advanced Variations](#advanced-variations)
12. [Mental Models & Cognitive Strategies](#mental-models--cognitive-strategies)
13. [Practice Problems (Beginner → Expert)](#practice-problems)
14. [Common Pitfalls & Edge Cases](#common-pitfalls--edge-cases)

---

## What is Cyclic Sort?

**Cyclic Sort** is an in-place sorting algorithm that operates on arrays containing numbers in a **given range**. It's not a general-purpose sorting algorithm like QuickSort or MergeSort. Instead, it's a **specialized technique** that exploits a specific constraint:

> **Key Constraint**: The array contains `n` numbers in the range `[1, n]` or `[0, n-1]` (or similar bounded ranges).

### Why This Matters

When you have this constraint, you can place each number at its **correct index** based on its value. For example:
- Number `1` should be at index `0`
- Number `2` should be at index `1`
- Number `n` should be at index `n-1`

This is the **core insight** that makes Cyclic Sort powerful.

---

## Core Intuition & Mental Model

### The "Parking Spot" Analogy

Imagine a parking lot with numbered spots 1 through n. Each car has a number on it (1 through n). Your job is to park each car in its designated spot.

**The Cyclic Sort Approach:**
1. Start at the first parking spot
2. If the car there belongs somewhere else, drive it to its correct spot
3. Take the car that was in that spot and drive it to its correct spot
4. Continue this "swap chain" until you find a car that belongs in the current spot
5. Move to the next spot and repeat

This creates "cycles" of swaps, hence the name **Cyclic Sort**.

### The Mathematical Invariant

**Invariant**: After processing position `i`, all positions from `0` to `i` contain their correct values.

This invariant is crucial for understanding why the algorithm works.

---

## The Fundamental Concept

### Problem Setup

Given: Array of `n` distinct integers in range `[1, n]`
Goal: Sort the array in O(n) time and O(1) space

### Key Definitions You Need

1. **Index**: The position in the array (0-based: 0, 1, 2, ..., n-1)
2. **Value**: The number stored at that index
3. **Correct Index**: Where a value should be placed
   - For value `x` in range `[1, n]`: correct index = `x - 1`
   - For value `x` in range `[0, n-1]`: correct index = `x`
4. **In-Place**: Algorithm uses constant extra space (no extra arrays)
5. **Cycle**: A sequence of swaps that eventually places an element correctly

---

## Visual Understanding

### ASCII Visualization

#### Initial State
```
Array:  [3, 1, 5, 4, 2]
Index:   0  1  2  3  4

Number 3 should be at index 2 (3-1=2)
Number 1 should be at index 0 (1-1=0)
Number 5 should be at index 4 (5-1=4)
etc.
```

#### Step-by-Step Process

```
Step 0: Start at index 0
Array:  [3, 1, 5, 4, 2]
         ^
         i=0, value=3, correct_index=2

Swap arr[0] with arr[2]:
Array:  [5, 1, 3, 4, 2]
         ^
         i=0, value=5, correct_index=4

Swap arr[0] with arr[4]:
Array:  [2, 1, 3, 4, 5]
         ^
         i=0, value=2, correct_index=1

Swap arr[0] with arr[1]:
Array:  [1, 2, 3, 4, 5]
         ^
         i=0, value=1 ✓ (correct position!)

Move to next index
```

```
Step 1: i=1
Array:  [1, 2, 3, 4, 5]
            ^
         i=1, value=2 ✓ (already correct!)

Move to next index
```

```
Continue for i=2,3,4... (all already correct)

Final:  [1, 2, 3, 4, 5]
```

### Flowchart of the Algorithm

```
                    START
                      |
                      v
              ┌───────────────┐
              │ i = 0         │
              └───────┬───────┘
                      |
                      v
              ┌───────────────────┐
          ┌───┤ i < n ?           │
          │   └───────┬───────────┘
          │           | Yes
          │           v
          │   ┌───────────────────────────┐
          │   │ correct_index =           │
          │   │ arr[i] - 1                │
          │   └───────┬───────────────────┘
          │           |
          │           v
          │   ┌───────────────────────────┐
          │   │ arr[i] != arr[correct]?   │◄─┐
          │   └───────┬───────────────────┘  │
          │           |                       │
          │      Yes  |  No                   │
          │           v                       │
          │   ┌───────────────────────────┐  │
          │   │ Swap arr[i] with          │  │
          │   │ arr[correct_index]        │──┘
          │   └───────────────────────────┘
          │           (loop while needed)
          │           |
          │           v
          │   ┌───────────────┐
          │   │ i = i + 1     │
          │   └───────┬───────┘
          │           |
          └───────────┘
              No      |
                      v
                  ┌───────┐
                  │  END  │
                  └───────┘
```

---

## Step-by-Step Algorithm

### Logical Reasoning Process (How Experts Think)

**Before coding, ask yourself:**

1. **What's the constraint?** Numbers are in range [1, n]
2. **What does that enable?** Each number knows its "home" index
3. **What's the strategy?** Place each number at its home before moving on
4. **Why does this work?** Each swap puts at least one number in its correct place
5. **What's the termination condition?** When we've visited all positions

### Algorithm Pseudocode

```
ALGORITHM CyclicSort(arr):
    n = length(arr)
    
    FOR i = 0 TO n-1:
        WHILE arr[i] is not at its correct position:
            correct_index = arr[i] - 1
            SWAP arr[i] WITH arr[correct_index]
        END WHILE
    END FOR
    
    RETURN arr
END ALGORITHM
```

### Detailed Step Breakdown

**Phase 1: Setup**
- Initialize index `i` to 0
- Determine array length `n`

**Phase 2: Iterate Through Array**
For each position `i` from 0 to n-1:

**Phase 3: Fix Current Position**
While the current element is not in its correct position:
- Calculate where current element should go: `correct_index = arr[i] - 1`
- Swap current element with the element at its correct position
- The new element at position `i` might also be out of place, so loop

**Phase 4: Move to Next Position**
- Once arr[i] is correct, increment i
- The inner while loop ensures we don't revisit positions

**Phase 5: Complete**
- After processing all positions, array is sorted

---

## Implementation Across Languages

### 1. Python Implementation (Most Readable)

```python
def cyclic_sort(arr):
    """
    Sorts an array containing numbers from 1 to n using cyclic sort.
    
    Time Complexity: O(n)
    Space Complexity: O(1)
    
    Args:
        arr: List of integers in range [1, n]
    
    Returns:
        Sorted list (in-place modification)
    """
    n = len(arr)
    i = 0
    
    while i < n:
        # Calculate where current number should be
        correct_index = arr[i] - 1
        
        # If current number is not at its correct position
        if arr[i] != arr[correct_index]:
            # Swap it to its correct position
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            # Current position is correct, move to next
            i += 1
    
    return arr


# Example usage with detailed tracking
def cyclic_sort_verbose(arr):
    """Version with step-by-step output for learning"""
    n = len(arr)
    i = 0
    step = 0
    
    print(f"Initial array: {arr}\n")
    
    while i < n:
        correct_index = arr[i] - 1
        
        if arr[i] != arr[correct_index]:
            print(f"Step {step}: Position {i}, Value {arr[i]}")
            print(f"  Should be at index {correct_index}")
            print(f"  Before swap: {arr}")
            
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
            
            print(f"  After swap:  {arr}\n")
            step += 1
        else:
            print(f"Position {i} is correct (value {arr[i]})\n")
            i += 1
    
    print(f"Final sorted array: {arr}")
    return arr


# Test
if __name__ == "__main__":
    test_arr = [3, 1, 5, 4, 2]
    cyclic_sort_verbose(test_arr.copy())
```

### 2. Rust Implementation (Performance-Focused)

```rust
/// Sorts an array containing numbers from 1 to n using cyclic sort.
/// 
/// # Arguments
/// * `arr` - A mutable slice of integers in range [1, n]
/// 
/// # Time Complexity: O(n)
/// # Space Complexity: O(1)
/// 
/// # Examples
/// ```
/// let mut arr = vec![3, 1, 5, 4, 2];
/// cyclic_sort(&mut arr);
/// assert_eq!(arr, vec![1, 2, 3, 4, 5]);
/// ```
pub fn cyclic_sort(arr: &mut [i32]) {
    let n = arr.len();
    let mut i = 0;
    
    while i < n {
        // Calculate correct index for current value
        let correct_index = (arr[i] - 1) as usize;
        
        // Check if current element is at wrong position
        if arr[i] != arr[correct_index] {
            // Swap to correct position
            arr.swap(i, correct_index);
        } else {
            // Element is at correct position, move forward
            i += 1;
        }
    }
}

// Generic version for different integer types
pub fn cyclic_sort_generic<T>(arr: &mut [T])
where
    T: Copy + Into<usize> + From<usize> + PartialEq,
{
    let n = arr.len();
    let mut i = 0;
    
    while i < n {
        let correct_index = arr[i].into() - 1;
        
        if arr[i] != arr[correct_index] {
            arr.swap(i, correct_index);
        } else {
            i += 1;
        }
    }
}

// Safe version with bounds checking
pub fn cyclic_sort_safe(arr: &mut [i32]) -> Result<(), &'static str> {
    let n = arr.len();
    let mut i = 0;
    
    while i < n {
        // Validate input: must be in range [1, n]
        if arr[i] < 1 || arr[i] > n as i32 {
            return Err("Array contains values outside range [1, n]");
        }
        
        let correct_index = (arr[i] - 1) as usize;
        
        if arr[i] != arr[correct_index] {
            arr.swap(i, correct_index);
        } else {
            i += 1;
        }
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_cyclic_sort() {
        let mut arr = vec![3, 1, 5, 4, 2];
        cyclic_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 4, 5]);
    }
    
    #[test]
    fn test_already_sorted() {
        let mut arr = vec![1, 2, 3, 4, 5];
        cyclic_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 4, 5]);
    }
}
```

### 3. C Implementation (Low-Level Control)

```c
#include <stdio.h>
#include <stdbool.h>

/**
 * Sorts an array containing numbers from 1 to n using cyclic sort.
 * 
 * @param arr: Pointer to integer array
 * @param n: Size of the array
 * 
 * Time Complexity: O(n)
 * Space Complexity: O(1)
 */
void cyclic_sort(int arr[], int n) {
    int i = 0;
    
    while (i < n) {
        // Calculate correct index (value - 1)
        int correct_index = arr[i] - 1;
        
        // Check if element is at wrong position
        if (arr[i] != arr[correct_index]) {
            // Swap elements
            int temp = arr[i];
            arr[i] = arr[correct_index];
            arr[correct_index] = temp;
        } else {
            // Element at correct position, move forward
            i++;
        }
    }
}

/**
 * Macro for swapping without temp variable (XOR swap)
 * Note: Only use when arr[i] and arr[j] are different locations
 */
#define SWAP_XOR(a, b) do { \
    if (&(a) != &(b)) { \
        (a) ^= (b); \
        (b) ^= (a); \
        (a) ^= (b); \
    } \
} while(0)

/**
 * Alternative implementation using XOR swap
 */
void cyclic_sort_xor(int arr[], int n) {
    int i = 0;
    
    while (i < n) {
        int correct_index = arr[i] - 1;
        
        if (arr[i] != arr[correct_index]) {
            SWAP_XOR(arr[i], arr[correct_index]);
        } else {
            i++;
        }
    }
}

/**
 * Utility function to print array
 */
void print_array(int arr[], int n) {
    printf("[");
    for (int i = 0; i < n; i++) {
        printf("%d", arr[i]);
        if (i < n - 1) printf(", ");
    }
    printf("]\n");
}

/**
 * Test function
 */
int main() {
    int arr[] = {3, 1, 5, 4, 2};
    int n = sizeof(arr) / sizeof(arr[0]);
    
    printf("Original array: ");
    print_array(arr, n);
    
    cyclic_sort(arr, n);
    
    printf("Sorted array:   ");
    print_array(arr, n);
    
    return 0;
}
```

### 4. C++ Implementation (Modern C++)

```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <stdexcept>

/**
 * Cyclic Sort implementation using modern C++ features
 * 
 * @tparam T: Integer type (int, long, etc.)
 * @param arr: Vector to sort in-place
 * 
 * Time Complexity: O(n)
 * Space Complexity: O(1)
 */
template<typename T>
void cyclic_sort(std::vector<T>& arr) {
    const size_t n = arr.size();
    size_t i = 0;
    
    while (i < n) {
        // Calculate correct index
        const size_t correct_index = static_cast<size_t>(arr[i] - 1);
        
        // Validate bounds (optional safety check)
        if (correct_index >= n) {
            throw std::out_of_range("Value out of valid range [1, n]");
        }
        
        // Swap if not at correct position
        if (arr[i] != arr[correct_index]) {
            std::swap(arr[i], arr[correct_index]);
        } else {
            ++i;
        }
    }
}

/**
 * C++20 Concepts version (requires -std=c++20)
 */
#if __cplusplus >= 202002L
#include <concepts>

template<std::integral T>
void cyclic_sort_concepts(std::vector<T>& arr) {
    const size_t n = arr.size();
    size_t i = 0;
    
    while (i < n) {
        const size_t correct_index = static_cast<size_t>(arr[i] - 1);
        
        if (arr[i] != arr[correct_index]) {
            std::swap(arr[i], arr[correct_index]);
        } else {
            ++i;
        }
    }
}
#endif

/**
 * Range-based implementation (C++20)
 */
#if __cplusplus >= 202002L
#include <ranges>

template<std::ranges::random_access_range R>
requires std::integral<std::ranges::range_value_t<R>>
void cyclic_sort_ranges(R& arr) {
    const auto n = std::ranges::size(arr);
    size_t i = 0;
    
    while (i < n) {
        const size_t correct_index = static_cast<size_t>(arr[i] - 1);
        
        if (arr[i] != arr[correct_index]) {
            std::ranges::iter_swap(arr.begin() + i, 
                                   arr.begin() + correct_index);
        } else {
            ++i;
        }
    }
}
#endif

/**
 * Utility function to print vector
 */
template<typename T>
void print_vector(const std::vector<T>& arr) {
    std::cout << "[";
    for (size_t i = 0; i < arr.size(); ++i) {
        std::cout << arr[i];
        if (i < arr.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";
}

/**
 * Test and demonstration
 */
int main() {
    std::vector<int> arr = {3, 1, 5, 4, 2};
    
    std::cout << "Original: ";
    print_vector(arr);
    
    cyclic_sort(arr);
    
    std::cout << "Sorted:   ";
    print_vector(arr);
    
    return 0;
}
```

### 5. Go Implementation (Idiomatic Go)

```go
package main

import "fmt"

// CyclicSort sorts an array containing numbers from 1 to n
// Time Complexity: O(n)
// Space Complexity: O(1)
func CyclicSort(arr []int) {
    n := len(arr)
    i := 0
    
    for i < n {
        // Calculate correct index for current value
        correctIndex := arr[i] - 1
        
        // Swap if element is not at correct position
        if arr[i] != arr[correctIndex] {
            arr[i], arr[correctIndex] = arr[correctIndex], arr[i]
        } else {
            i++
        }
    }
}

// CyclicSortWithValidation includes input validation
func CyclicSortWithValidation(arr []int) error {
    n := len(arr)
    i := 0
    
    for i < n {
        // Validate range
        if arr[i] < 1 || arr[i] > n {
            return fmt.Errorf("value %d at index %d is out of range [1, %d]", 
                            arr[i], i, n)
        }
        
        correctIndex := arr[i] - 1
        
        if arr[i] != arr[correctIndex] {
            arr[i], arr[correctIndex] = arr[correctIndex], arr[i]
        } else {
            i++
        }
    }
    
    return nil
}

// CyclicSortVerbose provides step-by-step output for learning
func CyclicSortVerbose(arr []int) {
    n := len(arr)
    i := 0
    step := 0
    
    fmt.Printf("Initial array: %v\n\n", arr)
    
    for i < n {
        correctIndex := arr[i] - 1
        
        if arr[i] != arr[correctIndex] {
            fmt.Printf("Step %d: Position %d, Value %d\n", step, i, arr[i])
            fmt.Printf("  Should be at index %d\n", correctIndex)
            fmt.Printf("  Before swap: %v\n", arr)
            
            arr[i], arr[correctIndex] = arr[correctIndex], arr[i]
            
            fmt.Printf("  After swap:  %v\n\n", arr)
            step++
        } else {
            fmt.Printf("Position %d is correct (value %d)\n\n", i, arr[i])
            i++
        }
    }
    
    fmt.Printf("Final sorted array: %v\n", arr)
}

func main() {
    arr := []int{3, 1, 5, 4, 2}
    
    fmt.Println("Original:", arr)
    CyclicSort(arr)
    fmt.Println("Sorted:  ", arr)
    
    fmt.Println("\n--- Verbose Version ---\n")
    arr2 := []int{3, 1, 5, 4, 2}
    CyclicSortVerbose(arr2)
}
```

---

## Complexity Analysis

### Time Complexity: O(n) - Linear

**Why is it O(n) and not O(n²)?**

This is a crucial insight that separates beginners from experts.

**Naive Analysis (Wrong):**
- Outer loop: O(n) iterations
- Inner while loop: Could run multiple times
- Total: O(n²)? **NO!**

**Correct Analysis:**

Each element is swapped **at most once** to its correct position.

**Proof:**
1. Array has `n` positions
2. Each swap places at least one element in its correct position
3. Once an element is in its correct position, it's never moved again
4. Maximum total swaps = `n - 1` (worst case: reverse sorted)
5. Total operations = O(n) loop iterations + O(n) swaps = O(n)

**Detailed Breakdown:**

```
Let's track swaps for arr = [5, 4, 3, 2, 1]:

Position 0: 
  - Swap 5 → index 4: [1, 4, 3, 2, 5]  (5 is now correct)
  - Swap 1 → index 0: [1, 4, 3, 2, 5]  (1 is now correct)
  
Position 1:
  - Swap 4 → index 3: [1, 2, 3, 4, 5]  (4 is now correct)
  - Swap 2 → index 1: [1, 2, 3, 4, 5]  (2 is now correct)
  
Position 2:
  - 3 is already correct ✓
  
Position 3:
  - 4 is already correct ✓
  
Position 4:
  - 5 is already correct ✓

Total swaps: 4 (which is n - 1)
Total comparisons: 5 + 4 + 1 + 1 + 1 = 12 ≈ 2n = O(n)
```

**Amortized Analysis:**
- Each element is touched at most twice:
  1. When swapped to its correct position
  2. When its index is checked in the outer loop
- Total touches = 2n = O(n)

### Space Complexity: O(1) - Constant

**What counts:**
- No extra arrays created
- Only loop variables (i, correct_index, temp)
- All operations in-place

**Memory Usage:**
- Fixed: 2-3 integer variables
- Independent of input size `n`
- Therefore: O(1)

### Comparison with Other Sorts

```
Algorithm      | Time (Best) | Time (Avg) | Time (Worst) | Space | Stable?
---------------|-------------|------------|--------------|-------|--------
Cyclic Sort    | O(n)        | O(n)       | O(n)         | O(1)  | No
Counting Sort  | O(n+k)      | O(n+k)     | O(n+k)       | O(k)  | Yes
Quicksort      | O(n log n)  | O(n log n) | O(n²)        | O(log n) | No
Mergesort      | O(n log n)  | O(n log n) | O(n log n)   | O(n)  | Yes
Heapsort       | O(n log n)  | O(n log n) | O(n log n)   | O(1)  | No

k = range of values
```

**Key Insight:** Cyclic Sort beats comparison-based sorts because it doesn't rely on comparisons—it uses the **values as indices**.

---

## Pattern Recognition Framework

### When to Use Cyclic Sort?

Learn to recognize these patterns **instantly**:

#### ✅ **USE Cyclic Sort When:**

1. **Array contains numbers in range [1, n] or [0, n-1]**
   - Example: [3, 1, 5, 4, 2] (n=5, range [1,5])

2. **Problem asks about "missing" or "duplicate" numbers**
   - "Find missing number"
   - "Find all duplicates"
   - "Find first k missing numbers"

3. **Array length equals the range of numbers**
   - len(arr) = 5, values in [1, 5]

4. **Problem mentions "without extra space"**
   - Cyclic Sort is O(1) space

5. **Numbers represent indices or positions**
   - Seat assignments, ID numbers, etc.

#### ❌ **DON'T Use Cyclic Sort When:**

1. **Numbers outside the range**
   - [1, 100, 3, 2] where n=4 but values up to 100

2. **Need stable sorting**
   - Cyclic Sort is not stable

3. **Floating-point or string sorting**
   - Only works with integers

4. **Range doesn't match array length**
   - [1, 2, 3] but range is [1, 100]

### Recognition Decision Tree

```
                    START
                      |
                      v
           ┌──────────────────────┐
           │ Problem involves     │
           │ finding missing/     │
           │ duplicate numbers?   │
           └──────┬───────────────┘
                  |
         Yes ┌────┴────┐ No
             v         v
      ┌──────────┐   Use other
      │ Array in │   approach
      │ range    │   (hash, sort)
      │ [1,n] or │
      │ [0,n-1]? │
      └────┬─────┘
           |
    Yes ┌──┴──┐ No
        v     v
    ┌────────┐ ┌──────────┐
    │ CYCLIC │ │ COUNTING │
    │  SORT  │ │ SORT or  │
    │ PATTERN│ │ HASH MAP │
    └────────┘ └──────────┘
```

---

## Problem-Solving Methodology

### The Expert's Thought Process

**Step 1: Identify the Pattern**
- Read the problem
- Look for keywords: "missing", "duplicate", "range [1, n]"
- Check constraints: array size vs value range

**Step 2: Choose the Approach**
- If matches cyclic sort pattern → Use it
- If close but not exact → Modify algorithm

**Step 3: Plan the Solution**
- What's being asked? (missing number, duplicate, etc.)
- How to detect it after sorting?
- Any edge cases?

**Step 4: Implement**
- Write cyclic sort
- Add detection logic
- Handle edge cases

**Step 5: Verify**
- Test with examples
- Check edge cases
- Analyze complexity

### Template for Solving Problems

```python
def solve_cyclic_pattern_problem(arr):
    """
    Template for cyclic sort pattern problems
    """
    n = len(arr)
    i = 0
    
    # Phase 1: Sort using cyclic sort
    while i < n:
        # Modify this based on range: [0,n-1] or [1,n]
        correct_index = arr[i] - 1  # For range [1, n]
        # correct_index = arr[i]    # For range [0, n-1]
        
        # Add condition to handle duplicates/missing
        if 0 <= correct_index < n and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Phase 2: Find what's asked (missing, duplicate, etc.)
    for i in range(n):
        # Check if element at index i is correct
        if arr[i] != i + 1:  # For range [1, n]
            # This position has wrong value
            # Return based on problem requirements
            pass
    
    return result
```

---

## Common Problem Patterns

### Pattern 1: Find Missing Number

**Problem:** Array contains n-1 numbers from [1, n]. Find the missing number.

**Example:** Input: [3, 1, 4, 2, 6, 7, 5] (n=8), Output: 8

**Solution Approach:**
1. Use cyclic sort (numbers in range [1, n])
2. After sorting, scan to find index where value doesn't match

```python
def find_missing_number(arr):
    """
    Find the missing number in range [1, n]
    Time: O(n), Space: O(1)
    """
    n = len(arr) + 1  # Total range is [1, n]
    i = 0
    
    # Cyclic sort (ignore numbers == n, they belong at end)
    while i < len(arr):
        correct_index = arr[i] - 1
        
        # Only swap if within bounds and not equal
        if arr[i] < n and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Find missing number
    for i in range(len(arr)):
        if arr[i] != i + 1:
            return i + 1  # Missing number found
    
    return n  # If all correct, missing is n


# Alternative: Mathematical approach (more elegant)
def find_missing_number_math(arr):
    """
    Using sum formula: sum(1..n) = n*(n+1)/2
    """
    n = len(arr) + 1
    expected_sum = n * (n + 1) // 2
    actual_sum = sum(arr)
    return expected_sum - actual_sum
```

**ASCII Visualization:**
```
Input:  [3, 1, 4, 2, 6, 7, 5]  (n=8, missing 8)
         0  1  2  3  4  5  6

After cyclic sort:
Array:  [1, 2, 3, 4, 5, 6, 7]
Index:   0  1  2  3  4  5  6
         ✓  ✓  ✓  ✓  ✓  ✓  ✓

Scan: All positions correct → missing number is n = 8
```

### Pattern 2: Find All Missing Numbers

**Problem:** Array contains numbers from [1, n]. Find all missing numbers.

**Example:** Input: [4, 3, 2, 7, 8, 2, 3, 1], Output: [5, 6]

```python
def find_all_missing_numbers(arr):
    """
    Find all missing numbers in range [1, n]
    Time: O(n), Space: O(1) (output doesn't count)
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort
    while i < n:
        correct_index = arr[i] - 1
        
        # Handle duplicates: don't swap if same value at target
        if 0 <= correct_index < n and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Find all positions with wrong values
    missing = []
    for i in range(n):
        if arr[i] != i + 1:
            missing.append(i + 1)
    
    return missing


# Example walkthrough
arr = [4, 3, 2, 7, 8, 2, 3, 1]
# After sort: [1, 2, 3, 4, 3, 2, 7, 8]
#              ✓  ✓  ✓  ✓  ✗  ✗  ✓  ✓
# Positions 5,6 have wrong values → missing [5, 6]
```

### Pattern 3: Find Duplicate Number

**Problem:** Array contains n+1 numbers from [1, n]. Find the duplicate.

**Example:** Input: [1, 3, 4, 2, 2], Output: 2

```python
def find_duplicate(arr):
    """
    Find the duplicate number in array of n+1 elements from [1, n]
    Time: O(n), Space: O(1)
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort (array has n+1 elements, values in [1, n])
    while i < n:
        correct_index = arr[i] - 1
        
        # If we find duplicate during sorting, return it
        if arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            # Same value at both positions → duplicate found
            if i != correct_index:
                return arr[i]
            i += 1
    
    # Alternative: scan after sorting
    for i in range(n):
        if arr[i] != i + 1:
            return arr[i]
    
    return -1  # No duplicate (shouldn't happen with valid input)


# Floyd's Cycle Detection (Advanced - different approach)
def find_duplicate_floyd(arr):
    """
    Using Floyd's cycle detection (tortoise and hare)
    Treats array as linked list where arr[i] points to arr[arr[i]]
    """
    # Phase 1: Find intersection point
    slow = fast = arr[0]
    
    while True:
        slow = arr[slow]
        fast = arr[arr[fast]]
        if slow == fast:
            break
    
    # Phase 2: Find entrance to cycle (duplicate number)
    slow = arr[0]
    while slow != fast:
        slow = arr[slow]
        fast = arr[fast]
    
    return slow
```

### Pattern 4: Find All Duplicates

**Problem:** Array contains numbers from [1, n]. Find all duplicates.

**Example:** Input: [4, 3, 2, 7, 8, 2, 3, 1], Output: [2, 3]

```python
def find_all_duplicates(arr):
    """
    Find all duplicate numbers
    Time: O(n), Space: O(1)
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort
    while i < n:
        correct_index = arr[i] - 1
        
        if arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Collect duplicates
    duplicates = []
    for i in range(n):
        if arr[i] != i + 1:
            duplicates.append(arr[i])
    
    return duplicates
```

### Pattern 5: Find Corrupt Pair

**Problem:** Array should have [1..n] but one number is corrupted (duplicated, causing another to go missing).

**Example:** Input: [3, 1, 2, 5, 2], Output: [2, 4] (2 is duplicate, 4 is missing)

```python
def find_corrupt_pair(arr):
    """
    Find the duplicate and missing number
    Returns: [duplicate, missing]
    Time: O(n), Space: O(1)
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort
    while i < n:
        correct_index = arr[i] - 1
        
        if arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Find the corrupt pair
    for i in range(n):
        if arr[i] != i + 1:
            return [arr[i], i + 1]  # [duplicate, missing]
    
    return [-1, -1]
```

### Pattern 6: First K Missing Positive Numbers

**Problem:** Find first k missing positive numbers.

**Example:** Input: arr = [3, -1, 4, 5, 5], k = 3, Output: [1, 2, 6]

```python
def find_first_k_missing(arr, k):
    """
    Find first k missing positive numbers
    Time: O(n + k), Space: O(k) for output
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort (only positive numbers in valid range)
    while i < n:
        correct_index = arr[i] - 1
        
        # Check if value is valid positive and in range [1, n]
        if 0 <= correct_index < n and arr[i] > 0 and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Collect missing numbers from [1, n]
    missing = []
    extra_numbers = set()
    
    for i in range(n):
        if arr[i] != i + 1:
            missing.append(i + 1)
            # Track numbers that are out of place (for extra missing)
            if arr[i] > 0:
                extra_numbers.add(arr[i])
    
    # If we need more than what's missing in [1, n]
    candidate = n + 1
    while len(missing) < k:
        if candidate not in extra_numbers:
            missing.append(candidate)
        candidate += 1
    
    return missing[:k]
```

---

## Advanced Variations

### Variation 1: Range [0, n-1] Instead of [1, n]

**Key Difference:** correct_index = arr[i] (not arr[i] - 1)

```python
def cyclic_sort_zero_indexed(arr):
    """
    For arrays with values in range [0, n-1]
    """
    n = len(arr)
    i = 0
    
    while i < n:
        correct_index = arr[i]  # Direct mapping
        
        if 0 <= correct_index < n and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    return arr
```

### Variation 2: Handling Negative Numbers

**Approach:** Ignore negative numbers during sorting

```python
def cyclic_sort_with_negatives(arr):
    """
    Sort positive numbers, ignore negatives
    """
    n = len(arr)
    i = 0
    
    while i < n:
        correct_index = arr[i] - 1
        
        # Only process positive numbers in valid range
        if 0 <= correct_index < n and arr[i] > 0 and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    return arr
```

### Variation 3: Finding Smallest Missing Positive

**Problem:** Find smallest missing positive integer (LeetCode 41)

```python
def first_missing_positive(arr):
    """
    Find smallest missing positive integer
    Input: [3, 4, -1, 1]  Output: 2
    Input: [1, 2, 0]      Output: 3
    """
    n = len(arr)
    i = 0
    
    # Cyclic sort for positive numbers
    while i < n:
        correct_index = arr[i] - 1
        
        if 0 <= correct_index < n and arr[i] > 0 and arr[i] != arr[correct_index]:
            arr[i], arr[correct_index] = arr[correct_index], arr[i]
        else:
            i += 1
    
    # Find first position with wrong value
    for i in range(n):
        if arr[i] != i + 1:
            return i + 1
    
    # All [1..n] are present, so return n+1
    return n + 1
```

### Variation 4: Optimized Space Using Marking

**Alternative:** Instead of swapping, mark visited numbers

```python
def find_duplicates_by_marking(arr):
    """
    Uses sign of numbers as marker (destructive)
    Works when all numbers are positive
    """
    duplicates = []
    
    for num in arr:
        index = abs(num) - 1
        
        # If already negative, we've seen this number before
        if arr[index] < 0:
            duplicates.append(abs(num))
        else:
            # Mark as seen by making negative
            arr[index] = -arr[index]
    
    return duplicates
```

---

## Mental Models & Cognitive Strategies

### 1. **The Index-Value Mapping Model**

**Core Principle:** When values represent valid indices, use them!

**Mental Image:** 
- Each number is a "key" to a specific "lock" (index)
- Cyclic sort is like sorting keys to their locks
- Once a key is in its lock, it's "home"

**Application:**
- Whenever you see bounded integers, think: "Can I use values as indices?"
- This is the foundation of many O(n) algorithms

### 2. **The Pigeonhole Principle**

**Cognitive Principle:** n items, n holes → duplicates mean missing

**How to Apply:**
- If array has n+1 elements in range [1, n] → must have duplicate
- If array has n elements but missing one → must be n distinct
- Use this to prove algorithm correctness

### 3. **Chunking Strategy**

**Definition:** Chunking = grouping related information into meaningful units

**For Cyclic Sort:**
- **Chunk 1:** "Place current element correctly"
- **Chunk 2:** "Move to next position"
- Don't think about individual swaps—think in chunks

**Deliberate Practice:**
- Solve 5 variations without looking
- Explain algorithm to yourself out loud
- Recognize pattern in <5 seconds when reading problem

### 4. **Meta-Learning: Pattern Transfer**

**Cyclic Sort teaches you:**
1. **Constraint exploitation:** When problem gives you constraints, USE them
2. **Index manipulation:** Many O(n) solutions use indices creatively
3. **In-place techniques:** Swapping is more powerful than you think

**Transfer to Other Problems:**
- Dutch National Flag (3-way partitioning)
- Array rearrangement problems
- Constant space solutions

### 5. **Flow State Optimization**

**To enter flow when solving:**
1. **Clear goal:** "Sort numbers to their indices"
2. **Immediate feedback:** After each swap, verify correctness
3. **Challenge-skill balance:** Start easy (basic sort), increase (find duplicates)

### 6. **Spaced Repetition Schedule**

**For mastering cyclic sort:**
- Day 1: Learn concept + basic implementation
- Day 3: Solve 5 problems
- Day 7: Solve harder variations
- Day 14: Teach it to someone
- Day 30: Speed solve (5 problems in 30 min)

---

## Practice Problems

### Beginner Level

1. **Cyclic Sort** (Basic)
   - Input: [3, 1, 5, 4, 2]
   - Output: [1, 2, 3, 4, 5]

2. **Missing Number** (LeetCode 268)
   - Input: [3, 0, 1]
   - Output: 2

3. **Find All Missing Numbers** (LeetCode 448)
   - Input: [4, 3, 2, 7, 8, 2, 3, 1]
   - Output: [5, 6]

### Intermediate Level

4. **Find Duplicate Number** (LeetCode 287)
   - Input: [1, 3, 4, 2, 2]
   - Output: 2

5. **Find All Duplicates** (LeetCode 442)
   - Input: [4, 3, 2, 7, 8, 2, 3, 1]
   - Output: [2, 3]

6. **Set Mismatch** (LeetCode 645)
   - Input: [1, 2, 2, 4]
   - Output: [2, 3]

### Advanced Level

7. **First Missing Positive** (LeetCode 41)
   - Input: [3, 4, -1, 1]
   - Output: 2

8. **Find First K Missing Positive**
   - Input: arr=[3, -1, 4, 5, 5], k=3
   - Output: [1, 2, 6]

9. **Find Smallest Missing in Sorted** (variation)
   - Input: [0, 1, 2, 6, 9, 11, 15]
   - Output: 3

### Expert Level Challenges

10. **Cyclic Sort on Linked List**
    - Adapt algorithm for linked list structure
    - Challenge: No random access

11. **Parallel Cyclic Sort**
    - Design thread-safe version
    - Handle race conditions

12. **Online Stream Missing Numbers**
    - Process stream of numbers
    - Report missing in real-time
    - Space constraint: O(1)

---

## Common Pitfalls & Edge Cases

### Pitfall 1: Infinite Loop

**Problem:** Forgetting to increment `i` when element is correct

```python
# ❌ WRONG - Infinite loop
while i < n:
    correct_index = arr[i] - 1
    if arr[i] != arr[correct_index]:
        arr[i], arr[correct_index] = arr[correct_index], arr[i]
    # Missing: else: i += 1

# ✅ CORRECT
while i < n:
    correct_index = arr[i] - 1
    if arr[i] != arr[correct_index]:
        arr[i], arr[correct_index] = arr[correct_index], arr[i]
    else:
        i += 1  # Must increment!
```

### Pitfall 2: Index Out of Bounds

**Problem:** Not validating calculated index

```python
# ❌ WRONG - Can crash
correct_index = arr[i] - 1
arr[i], arr[correct_index] = arr[correct_index], arr[i]

# ✅ CORRECT - Validate first
correct_index = arr[i] - 1
if 0 <= correct_index < n:
    arr[i], arr[correct_index] = arr[correct_index], arr[i]
else:
    i += 1
```

### Pitfall 3: Handling Duplicates

**Problem:** Swapping same values infinitely

```python
# ❌ WRONG - Infinite loop with duplicates [1, 1]
while i < n:
    correct_index = arr[i] - 1
    if arr[i] != arr[correct_index]:
        arr[i], arr[correct_index] = arr[correct_index], arr[i]

# ✅ CORRECT - Check if values are different
while i < n:
    correct_index = arr[i] - 1
    if arr[i] != arr[correct_index]:  # This check handles duplicates
        arr[i], arr[correct_index] = arr[correct_index], arr[i]
    else:
        i += 1
```

### Edge Cases to Test

1. **Empty Array:** `[]`
2. **Single Element:** `[1]`
3. **Already Sorted:** `[1, 2, 3, 4, 5]`
4. **Reverse Sorted:** `[5, 4, 3, 2, 1]`
5. **All Duplicates:** `[1, 1, 1, 1]`
6. **With Negatives:** `[-1, 0, 1, 2]`
7. **Out of Range:** `[1, 100, 3]` (100 > n)

---

## Summary: The Cyclic Sort Mastery Checklist

### Core Understanding ✓
- [ ] Can explain why it's O(n) not O(n²)
- [ ] Understand index-value mapping principle
- [ ] Know when to use vs when not to use
- [ ] Can derive the algorithm from first principles

### Implementation ✓
- [ ] Can implement in Python without reference
- [ ] Can implement in Rust without reference
- [ ] Can implement in C/C++ without reference
- [ ] Can implement in Go without reference
- [ ] Handle all edge cases correctly

### Pattern Recognition ✓
- [ ] Recognize cyclic sort problems in <10 seconds
- [ ] Know all 6+ common problem patterns
- [ ] Can modify base algorithm for variations
- [ ] Generate new problem variations

### Problem Solving ✓
- [ ] Solved 10+ cyclic sort problems
- [ ] Can solve in optimal time/space
- [ ] Explain solution to others clearly
- [ ] Create alternative approaches

### Deep Mastery ✓
- [ ] Understand mathematical proofs
- [ ] Can teach the concept effectively
- [ ] Apply pattern to new problem domains
- [ ] Contribute to optimal solutions

---

## Final Thoughts: The Path to Top 1%

**Remember:**
1. **Cyclic Sort is a pattern, not just an algorithm**
2. **The constraint [1, n] is the trigger—recognize it instantly**
3. **Every swap places at least one element correctly**
4. **Master the variations, not just the base case**
5. **Speed comes from pattern recognition + muscle memory**

**Your Next Steps:**
1. Implement the base algorithm in all 5 languages
2. Solve the beginner problems (3 problems)
3. Move to intermediate (3 problems)
4. Tackle advanced challenges (3 problems)
5. Time yourself—aim for <5 min per problem
6. Teach someone else—ultimate test of mastery

**The Monk's Approach:**
- Focus deeply on one variation at a time
- Understand WHY before memorizing HOW
- Practice with full presence
- Seek the elegant solution
- Build unshakeable fundamentals

---

*"The superior problem solver sees the pattern before the solution."*

**Your journey to the top 1% starts with mastering the fundamentals. Cyclic Sort is one such fundamental—simple in concept, powerful in application, essential in your toolkit.**

**Now go forth and practice with discipline, clarity, and purpose. 🚀**