# Fenwick Tree (Binary Indexed Tree) — Complete Mastery Guide

## Table of Contents
1. Foundational Concepts & Motivation
2. Core Theory & Mathematical Foundation
3. Implementation in Rust, Python, and Go
4. Advanced Techniques & Patterns
5. Problem-Solving Framework
6. Practice Problems & Solutions

---

## 1. Foundational Concepts & Motivation

### What Problem Are We Solving?

Imagine you have an array of numbers and need to:
- **Update** a single element (change `arr[i]`)
- **Query** the sum of elements from index 0 to k (prefix sum)

**Naive Approach:**
- Update: O(1) — just change the element
- Query: O(n) — sum all elements from 0 to k

**Prefix Sum Array:**
- Update: O(n) — must recalculate all prefix sums
- Query: O(1) — direct lookup

**Fenwick Tree Solution:**
- Update: O(log n)
- Query: O(log n)

**The Challenge:** Can we do BOTH operations efficiently?

### Mental Model: The Core Insight

A Fenwick Tree exploits **binary representation** of indices to create a hierarchical structure where each node is responsible for a specific range of elements.

```
Think of it like a management hierarchy:
- CEO knows total company revenue
- VPs know their division's revenue
- Managers know their team's revenue
- Individual contributors know their own revenue

To get any division's total, you ask the right combination of managers!
```

---

## 2. Core Theory & Mathematical Foundation

### Key Concept: "Responsibility Range"

Each index in a Fenwick Tree is responsible for a specific range determined by the **rightmost set bit** in its binary representation.

**Definition of Terms:**
- **Index i**: Position in the tree (1-indexed for mathematical elegance)
- **Rightmost set bit**: The least significant 1 in binary representation
- **Responsibility**: How many elements this index "summarizes"

### The Magic Formula: `i & (-i)`

This operation isolates the rightmost set bit.

```
Example: i = 6
Binary:  6 = 0110
      -6 = 1010 (two's complement)
   6 & -6 = 0010 = 2

So index 6 is responsible for 2 elements: arr[5] and arr[6] (in 0-indexed terms)
```

### ASCII Visualization: Tree Structure

```
Array indices (1-indexed):  1   2   3   4   5   6   7   8   9  10  11  12
Original array:           [a1  a2  a3  a4  a5  a6  a7  a8  a9 a10 a11 a12]

Fenwick Tree Structure:

Level 3:                                    [1-8]
                                             tree[8]
                                               |
Level 2:                    [1-4]            [5-8]            [9-12]
                            tree[4]          tree[8]          tree[12]
                              |                                 |
Level 1:        [1-2]       [3-4]       [5-6]     [7-8]   [9-10]    [11-12]
               tree[2]     tree[4]     tree[6]   tree[8]  tree[10]  tree[12]
                 |           |           |         |        |         |
Level 0:    [1] [2]     [3] [4]     [5] [6]   [7] [8]  [9] [10]  [11][12]
          tree[1] tree[2] tree[3] tree[4] ...

Responsibility of each index:
tree[1] = a1              (covers 1 element)
tree[2] = a1 + a2         (covers 2 elements)
tree[3] = a3              (covers 1 element)
tree[4] = a1+a2+a3+a4     (covers 4 elements)
tree[5] = a5              (covers 1 element)
tree[6] = a5 + a6         (covers 2 elements)
tree[7] = a7              (covers 1 element)
tree[8] = a1+...+a8       (covers 8 elements)
```

### Why This Works: The Mathematical Proof Sketch

**Claim:** Any prefix sum can be decomposed into at most log(n) disjoint ranges.

**Proof Intuition:**
- The binary representation of any number has at most log(n) bits
- Each bit corresponds to a power of 2
- Each power of 2 corresponds to a range in our tree
- Therefore, we need at most log(n) lookups

Example: Sum(13) = Sum(1101 in binary)
```
13 = 8 + 4 + 1
So Sum(13) = tree[8] + tree[12] + tree[13]
            [1-8]   + [9-12]  + [13]
```

---

## 3. Implementation in Rust, Python, and Go

### Rust Implementation (Zero-Cost Abstraction)
/// Fenwick Tree (Binary Indexed Tree) - Production-Ready Implementation
/// 
/// Time Complexity: O(log n) for both update and query
/// Space Complexity: O(n)
/// 
/// Principles demonstrated:
/// - Zero-cost abstractions with generics
/// - Type safety with trait bounds
/// - Idiomatic Rust patterns

use std::ops::{AddAssign, Sub};

/// Generic Fenwick Tree supporting any additive type
pub struct FenwickTree<T> {
    tree: Vec<T>,
    size: usize,
}

impl<T> FenwickTree<T>
where
    T: Default + Copy + AddAssign + Sub<Output = T>,
{
    /// Creates a new Fenwick Tree with given size
    /// 
    /// # Arguments
    /// * `size` - Number of elements (internally uses 1-indexed)
    pub fn new(size: usize) -> Self {
        FenwickTree {
            tree: vec![T::default(); size + 1], // +1 for 1-indexing
            size,
        }
    }

    /// Creates Fenwick Tree from existing array
    /// 
    /// Optimization: O(n) construction instead of O(n log n)
    pub fn from_vec(arr: Vec<T>) -> Self {
        let n = arr.len();
        let mut tree = vec![T::default(); n + 1];
        
        // Copy original array (1-indexed)
        for i in 0..n {
            tree[i + 1] = arr[i];
        }
        
        // Build tree in O(n) using parent-child relationship
        // Key insight: Each node contributes to its parent
        for i in 1..=n {
            let parent = i + Self::lsb(i);
            if parent <= n {
                tree[parent] += tree[i];
            }
        }
        
        FenwickTree { tree, size: n }
    }

    /// Least Significant Bit (LSB) - isolates rightmost set bit
    /// 
    /// Mathematical foundation: i & (-i)
    /// - Works because -i = !i + 1 (two's complement)
    /// - Only the rightmost set bit position is preserved
    #[inline]
    fn lsb(i: usize) -> usize {
        i & i.wrapping_neg() // Handle potential overflow gracefully
    }

    /// Updates value at index (0-indexed for user, 1-indexed internally)
    /// 
    /// # Arguments
    /// * `idx` - 0-indexed position
    /// * `delta` - Value to add (can be negative for subtraction)
    /// 
    /// # Algorithm Flow:
    /// 1. Convert to 1-indexed
    /// 2. Add delta to current node
    /// 3. Move to parent: idx += lsb(idx)
    /// 4. Repeat until out of bounds
    pub fn update(&mut self, idx: usize, delta: T) {
        let mut i = idx + 1; // Convert to 1-indexed
        while i <= self.size {
            self.tree[i] += delta;
            i += Self::lsb(i); // Move to parent
        }
    }

    /// Queries prefix sum [0, idx] (0-indexed)
    /// 
    /// # Returns
    /// Sum of elements from index 0 to idx (inclusive)
    /// 
    /// # Algorithm Flow:
    /// 1. Convert to 1-indexed
    /// 2. Add current node to sum
    /// 3. Move to previous range: idx -= lsb(idx)
    /// 4. Repeat until idx becomes 0
    pub fn query(&self, idx: usize) -> T {
        let mut sum = T::default();
        let mut i = idx + 1; // Convert to 1-indexed
        
        while i > 0 {
            sum += self.tree[i];
            i -= Self::lsb(i); // Move to previous range
        }
        sum
    }

    /// Range query: sum of elements from [left, right] (inclusive, 0-indexed)
    /// 
    /// Key insight: range_sum(l, r) = prefix_sum(r) - prefix_sum(l-1)
    pub fn range_query(&self, left: usize, right: usize) -> T {
        if left == 0 {
            self.query(right)
        } else {
            self.query(right) - self.query(left - 1)
        }
    }

    /// Sets value at index (not just increment)
    /// 
    /// Strategy: Calculate delta and use update
    pub fn set(&mut self, idx: usize, value: T) {
        let current = self.range_query(idx, idx);
        let delta = value - current;
        self.update(idx, delta);
    }
}

// Example usage and test cases
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operations() {
        let mut ft = FenwickTree::new(10);
        
        // Build array: [3, 2, -1, 6, 5, 4, -3, 3, 7, 2]
        let values = vec![3, 2, -1, 6, 5, 4, -3, 3, 7, 2];
        for (i, &val) in values.iter().enumerate() {
            ft.update(i, val);
        }
        
        // Test prefix sums
        assert_eq!(ft.query(0), 3);           // [3]
        assert_eq!(ft.query(3), 10);          // [3,2,-1,6]
        assert_eq!(ft.query(6), 16);          // sum of first 7 elements
        
        // Test range queries
        assert_eq!(ft.range_query(2, 5), 14); // [-1,6,5,4]
        
        // Test update
        ft.update(3, 4);  // arr[3] = 6 + 4 = 10
        assert_eq!(ft.query(3), 14);          // [3,2,-1,10]
    }

    #[test]
    fn test_from_vec() {
        let arr = vec![1, 3, 5, 7, 9, 11];
        let ft = FenwickTree::from_vec(arr);
        
        assert_eq!(ft.query(2), 9);   // 1 + 3 + 5
        assert_eq!(ft.query(5), 36);  // sum of all
    }
}

fn main() {
    // Demonstration
    let mut ft = FenwickTree::new(8);
    
    println!("=== Fenwick Tree Demonstration ===\n");
    
    // Build array
    let arr = vec![1, 2, 3, 4, 5, 6, 7, 8];
    for (i, &val) in arr.iter().enumerate() {
        ft.update(i, val);
    }
    
    println!("Array: {:?}", arr);
    println!("\nPrefix Sums:");
    for i in 0..8 {
        println!("  Sum[0..{}] = {}", i, ft.query(i));
    }
    
    println!("\nRange Queries:");
    println!("  Sum[2..5] = {}", ft.range_query(2, 5)); // 3+4+5+6 = 18
    println!("  Sum[0..3] = {}", ft.range_query(0, 3)); // 1+2+3+4 = 10
    
    println!("\nUpdate arr[3] += 10");
    ft.update(3, 10);
    println!("  New Sum[0..3] = {}", ft.query(3)); // 1+2+3+14 = 20
    println!("  New Sum[3..5] = {}", ft.range_query(3, 5)); // 14+5+6 = 25
}

### Python Implementation (Clean & Pythonic)
"""
Fenwick Tree (Binary Indexed Tree) - Python Implementation

Time Complexity: O(log n) for update and query
Space Complexity: O(n)

Design Principles:
- Pythonic API with clear method names
- Type hints for clarity
- Comprehensive docstrings
- Both functional and OOP styles demonstrated
"""

from typing import List, Optional


class FenwickTree:
    """
    Binary Indexed Tree for efficient prefix sum queries and point updates.
    
    Uses 1-based indexing internally for mathematical elegance.
    """
    
    def __init__(self, size: int):
        """
        Initialize Fenwick Tree with given size.
        
        Args:
            size: Number of elements in the array (0-indexed)
        """
        self.size = size
        self.tree = [0] * (size + 1)  # +1 for 1-indexing
    
    @classmethod
    def from_list(cls, arr: List[int]) -> 'FenwickTree':
        """
        Construct Fenwick Tree from existing array in O(n) time.
        
        Algorithm:
        1. Copy array to tree (1-indexed)
        2. For each node, add its value to parent
        3. Parent index: i + lowbit(i)
        
        Args:
            arr: Input array (0-indexed)
            
        Returns:
            FenwickTree instance
        """
        n = len(arr)
        ft = cls(n)
        
        # Copy array with 1-indexing
        for i in range(n):
            ft.tree[i + 1] = arr[i]
        
        # Build tree: each node contributes to parent
        for i in range(1, n + 1):
            parent = i + cls._lowbit(i)
            if parent <= n:
                ft.tree[parent] += ft.tree[i]
        
        return ft
    
    @staticmethod
    def _lowbit(x: int) -> int:
        """
        Extract the rightmost set bit (LSB).
        
        Mathematical foundation:
        - x & (-x) isolates lowest set bit
        - -x is two's complement: flip bits and add 1
        
        Examples:
            6 (0110) & -6 (1010) = 0010 = 2
            12 (1100) & -12 (0100) = 0100 = 4
        
        Args:
            x: Positive integer
            
        Returns:
            Value of rightmost set bit
        """
        return x & (-x)
    
    def update(self, idx: int, delta: int) -> None:
        """
        Add delta to element at index (0-indexed).
        
        Algorithm visualization for idx=3, delta=5:
        
        Step 1: i=4 (1-indexed)  -> tree[4] += 5
        Step 2: i=8 (4+4)        -> tree[8] += 5
        Step 3: i=16 (8+8)       -> out of bounds, stop
        
        Args:
            idx: 0-indexed position to update
            delta: Value to add (negative for subtraction)
        """
        i = idx + 1  # Convert to 1-indexed
        while i <= self.size:
            self.tree[i] += delta
            i += self._lowbit(i)  # Jump to parent
    
    def query(self, idx: int) -> int:
        """
        Get prefix sum from index 0 to idx (inclusive, 0-indexed).
        
        Algorithm visualization for idx=6 (query position 7 in 1-indexed):
        
        Step 1: i=7, sum += tree[7]  (covers [7])
        Step 2: i=6, sum += tree[6]  (covers [5-6])
        Step 3: i=4, sum += tree[4]  (covers [1-4])
        Step 4: i=0, stop
        
        Result: tree[7] + tree[6] + tree[4] = sum[0..6]
        
        Args:
            idx: 0-indexed position (inclusive)
            
        Returns:
            Sum of elements from 0 to idx
        """
        total = 0
        i = idx + 1  # Convert to 1-indexed
        while i > 0:
            total += self.tree[i]
            i -= self._lowbit(i)  # Jump to previous range
        return total
    
    def range_query(self, left: int, right: int) -> int:
        """
        Get sum of elements in range [left, right] (inclusive, 0-indexed).
        
        Key insight: sum[l..r] = prefix_sum[r] - prefix_sum[l-1]
        
        Args:
            left: Start index (0-indexed, inclusive)
            right: End index (0-indexed, inclusive)
            
        Returns:
            Sum of elements in range
        """
        if left == 0:
            return self.query(right)
        return self.query(right) - self.query(left - 1)
    
    def set_value(self, idx: int, value: int) -> None:
        """
        Set element at index to specific value (not increment).
        
        Strategy: Calculate difference and use update.
        
        Args:
            idx: 0-indexed position
            value: New value to set
        """
        current = self.range_query(idx, idx)
        delta = value - current
        self.update(idx, delta)
    
    def visualize(self) -> None:
        """Print tree structure for debugging."""
        print("Fenwick Tree Internal Structure (1-indexed):")
        print(f"Size: {self.size}")
        print(f"Tree: {self.tree[1:]}")
        print("\nResponsibility of each index:")
        for i in range(1, min(self.size + 1, 17)):  # Limit output
            lowbit = self._lowbit(i)
            start = i - lowbit + 1
            print(f"  tree[{i:2d}] covers range [{start:2d}, {i:2d}] "
                  f"(responsibility: {lowbit})")


# Functional helpers for competitive programming
def lowbit(x: int) -> int:
    """Standalone lowbit function."""
    return x & (-x)


def build_fenwick(arr: List[int]) -> List[int]:
    """Build Fenwick tree from array (functional style)."""
    n = len(arr)
    tree = [0] * (n + 1)
    
    for i in range(n):
        tree[i + 1] = arr[i]
    
    for i in range(1, n + 1):
        parent = i + lowbit(i)
        if parent <= n:
            tree[parent] += tree[i]
    
    return tree


def fenwick_update(tree: List[int], idx: int, delta: int) -> None:
    """Update Fenwick tree (functional style, 0-indexed input)."""
    i = idx + 1
    while i < len(tree):
        tree[i] += delta
        i += lowbit(i)


def fenwick_query(tree: List[int], idx: int) -> int:
    """Query Fenwick tree (functional style, 0-indexed input)."""
    total = 0
    i = idx + 1
    while i > 0:
        total += tree[i]
        i -= lowbit(i)
    return total


# Demonstration and testing
if __name__ == "__main__":
    print("=== Fenwick Tree Python Demonstration ===\n")
    
    # Example 1: Basic operations
    print("Example 1: Building from scratch")
    ft = FenwickTree(8)
    arr = [1, 2, 3, 4, 5, 6, 7, 8]
    
    for i, val in enumerate(arr):
        ft.update(i, val)
    
    print(f"Array: {arr}")
    print("\nPrefix Sums:")
    for i in range(8):
        print(f"  Sum[0..{i}] = {ft.query(i)}")
    
    print("\nRange Queries:")
    print(f"  Sum[2..5] = {ft.range_query(2, 5)}")  # 3+4+5+6 = 18
    print(f"  Sum[0..3] = {ft.range_query(0, 3)}")  # 1+2+3+4 = 10
    
    # Example 2: Building from list (O(n) construction)
    print("\n\nExample 2: Building from list")
    arr2 = [3, 2, -1, 6, 5, 4, -3, 3, 7, 2]
    ft2 = FenwickTree.from_list(arr2)
    
    print(f"Array: {arr2}")
    print(f"Sum[0..6] = {ft2.query(6)}")  # Sum of first 7 elements
    print(f"Sum[2..5] = {ft2.range_query(2, 5)}")  # -1+6+5+4 = 14
    
    # Example 3: Updates
    print("\n\nExample 3: Dynamic updates")
    print("Before update:")
    print(f"  arr[3] contribution to Sum[0..3]: {ft2.range_query(3, 3)}")
    print(f"  Sum[0..3] = {ft2.query(3)}")
    
    ft2.update(3, 10)  # Add 10 to arr[3]
    print("\nAfter update (arr[3] += 10):")
    print(f"  New Sum[0..3] = {ft2.query(3)}")
    
    # Visualization
    print("\n\nExample 4: Tree Visualization")
    small_ft = FenwickTree.from_list([1, 2, 3, 4, 5, 6, 7, 8])
    small_ft.visualize()
    
    # Performance note
    print("\n\n=== Performance Characteristics ===")
    print("Update: O(log n)")
    print("Query: O(log n)")
    print("Space: O(n)")
    print("Build from array: O(n)")

### Go Implementation (Performance-Oriented)

package main

import (
	"fmt"
)

/*
Fenwick Tree (Binary Indexed Tree) - Go Implementation

Time Complexity: O(log n) for update and query
Space Complexity: O(n)

Design Philosophy:
- Idiomatic Go with simple, efficient code
- Value semantics where appropriate
- Clear separation of concerns
*/

// FenwickTree represents a Binary Indexed Tree for prefix sum queries
type FenwickTree struct {
	tree []int
	size int
}

// NewFenwickTree creates a new Fenwick Tree with given size
func NewFenwickTree(size int) *FenwickTree {
	return &FenwickTree{
		tree: make([]int, size+1), // +1 for 1-based indexing
		size: size,
	}
}

// FromSlice constructs a Fenwick Tree from existing slice in O(n) time
// This is more efficient than n individual updates which would be O(n log n)
func FromSlice(arr []int) *FenwickTree {
	n := len(arr)
	ft := &FenwickTree{
		tree: make([]int, n+1),
		size: n,
	}

	// Copy array with 1-based indexing
	for i := 0; i < n; i++ {
		ft.tree[i+1] = arr[i]
	}

	// Build tree: each node contributes to its parent
	// Parent index = i + lowbit(i)
	for i := 1; i <= n; i++ {
		parent := i + lowbit(i)
		if parent <= n {
			ft.tree[parent] += ft.tree[i]
		}
	}

	return ft
}

// lowbit extracts the rightmost set bit (LSB)
// This is the key operation that makes Fenwick Trees work
//
// Mathematical insight:
// - x & (-x) isolates the lowest set bit
// - In two's complement: -x = ^x + 1
// - Only the rightmost '1' bit survives the AND operation
//
// Examples:
//   6 (binary: 0110) & -6 (binary: 1010) = 2 (binary: 0010)
//   12 (binary: 1100) & -12 (binary: 0100) = 4 (binary: 0100)
func lowbit(x int) int {
	return x & (-x)
}

// Update adds delta to the element at index idx (0-indexed)
//
// Algorithm walkthrough for idx=3, delta=5:
//   Start: i = 4 (convert to 1-indexed)
//   Step 1: tree[4] += 5, then i = 4 + lowbit(4) = 4 + 4 = 8
//   Step 2: tree[8] += 5, then i = 8 + lowbit(8) = 8 + 8 = 16
//   Step 3: i > size, stop
//
// Why it works:
// - Each index is responsible for a range determined by its lowbit
// - We update the current node and all ancestors that contain it
// - Moving to parent: i += lowbit(i)
func (ft *FenwickTree) Update(idx int, delta int) {
	i := idx + 1 // Convert to 1-indexed
	for i <= ft.size {
		ft.tree[i] += delta
		i += lowbit(i) // Jump to parent node
	}
}

// Query returns the prefix sum from index 0 to idx (inclusive, 0-indexed)
//
// Algorithm walkthrough for idx=6 (7 in 1-indexed):
//   Start: i = 7, sum = 0
//   Step 1: sum += tree[7] (covers [7]), i = 7 - lowbit(7) = 7 - 1 = 6
//   Step 2: sum += tree[6] (covers [5-6]), i = 6 - lowbit(6) = 6 - 2 = 4
//   Step 3: sum += tree[4] (covers [1-4]), i = 4 - lowbit(4) = 4 - 4 = 0
//   Step 4: i = 0, stop
//
// Result: sum = tree[7] + tree[6] + tree[4] = complete sum from 1 to 7
//
// Why it works:
// - Each query decomposes the range into O(log n) disjoint segments
// - Moving to previous segment: i -= lowbit(i)
func (ft *FenwickTree) Query(idx int) int {
	sum := 0
	i := idx + 1 // Convert to 1-indexed
	for i > 0 {
		sum += ft.tree[i]
		i -= lowbit(i) // Jump to previous range
	}
	return sum
}

// RangeQuery returns the sum of elements in range [left, right] (inclusive, 0-indexed)
//
// Key mathematical insight:
//   sum(left, right) = prefix_sum(right) - prefix_sum(left - 1)
//
// This works because:
//   prefix_sum(right) = arr[0] + arr[1] + ... + arr[right]
//   prefix_sum(left-1) = arr[0] + arr[1] + ... + arr[left-1]
//   Difference = arr[left] + arr[left+1] + ... + arr[right]
func (ft *FenwickTree) RangeQuery(left, right int) int {
	if left == 0 {
		return ft.Query(right)
	}
	return ft.Query(right) - ft.Query(left-1)
}

// Set changes the value at index to a specific value (not increment)
// Strategy: Calculate the difference and use Update
func (ft *FenwickTree) Set(idx int, value int) {
	current := ft.RangeQuery(idx, idx)
	delta := value - current
	ft.Update(idx, delta)
}

// Visualize prints the tree structure for debugging
func (ft *FenwickTree) Visualize() {
	fmt.Println("Fenwick Tree Internal Structure (1-indexed):")
	fmt.Printf("Size: %d\n", ft.size)
	fmt.Printf("Tree: %v\n", ft.tree[1:])
	fmt.Println("\nResponsibility of each index:")
	
	limit := ft.size
	if limit > 16 {
		limit = 16 // Limit output for readability
	}
	
	for i := 1; i <= limit; i++ {
		lb := lowbit(i)
		start := i - lb + 1
		fmt.Printf("  tree[%2d] covers range [%2d, %2d] (responsibility: %d)\n",
			i, start, i, lb)
	}
}

// Demonstration and testing
func main() {
	fmt.Println("=== Fenwick Tree Go Demonstration ===\n")

	// Example 1: Building from scratch
	fmt.Println("Example 1: Building from scratch")
	ft := NewFenwickTree(8)
	arr := []int{1, 2, 3, 4, 5, 6, 7, 8}

	for i, val := range arr {
		ft.Update(i, val)
	}

	fmt.Printf("Array: %v\n", arr)
	fmt.Println("\nPrefix Sums:")
	for i := 0; i < 8; i++ {
		fmt.Printf("  Sum[0..%d] = %d\n", i, ft.Query(i))
	}

	fmt.Println("\nRange Queries:")
	fmt.Printf("  Sum[2..5] = %d\n", ft.RangeQuery(2, 5)) // 3+4+5+6 = 18
	fmt.Printf("  Sum[0..3] = %d\n", ft.RangeQuery(0, 3)) // 1+2+3+4 = 10

	// Example 2: Building from slice (O(n) construction)
	fmt.Println("\n\nExample 2: Building from slice")
	arr2 := []int{3, 2, -1, 6, 5, 4, -3, 3, 7, 2}
	ft2 := FromSlice(arr2)

	fmt.Printf("Array: %v\n", arr2)
	fmt.Printf("Sum[0..6] = %d\n", ft2.Query(6))          // Sum of first 7 elements
	fmt.Printf("Sum[2..5] = %d\n", ft2.RangeQuery(2, 5)) // -1+6+5+4 = 14

	// Example 3: Dynamic updates
	fmt.Println("\n\nExample 3: Dynamic updates")
	fmt.Println("Before update:")
	fmt.Printf("  arr[3] = %d\n", ft2.RangeQuery(3, 3))
	fmt.Printf("  Sum[0..3] = %d\n", ft2.Query(3))

	ft2.Update(3, 10) // Add 10 to arr[3]
	fmt.Println("\nAfter update (arr[3] += 10):")
	fmt.Printf("  New Sum[0..3] = %d\n", ft2.Query(3))

	// Example 4: Visualization
	fmt.Println("\n\nExample 4: Tree Visualization")
	smallFt := FromSlice([]int{1, 2, 3, 4, 5, 6, 7, 8})
	smallFt.Visualize()

	// Performance notes
	fmt.Println("\n\n=== Performance Characteristics ===")
	fmt.Println("Update: O(log n)")
	fmt.Println("Query: O(log n)")
	fmt.Println("Space: O(n)")
	fmt.Println("Build from slice: O(n)")

	// Example 5: Lowbit demonstration
	fmt.Println("\n\nExample 5: Lowbit Function")
	testValues := []int{1, 2, 3, 4, 5, 6, 7, 8, 12, 16}
	for _, val := range testValues {
		fmt.Printf("lowbit(%2d) = %2d  (binary: %08b -> %08b)\n",
			val, lowbit(val), val, lowbit(val))
	}
}

---

## 4. Advanced Techniques & Patterns

### Pattern 1: Range Update with Point Query

**Problem:** Can we do the *reverse* — update ranges in O(log n) but only query single points?

**Solution:** Use a **difference array** with Fenwick Tree!

**Concept - Difference Array:**
- Instead of storing values, store differences between consecutive elements
- `diff[i] = arr[i] - arr[i-1]`
- To get `arr[i]`, compute prefix sum of differences: `arr[i] = Σ(diff[0..i])`

**How it works:**
```
Original: [3, 5, 2, 7, 1]
Diff:     [3, 2, -3, 5, -6]  (diff[i] = arr[i] - arr[i-1])

Range update [1, 3] += 4:
  Only modify diff[1] and diff[4]!
  diff[1] += 4  (start of range)
  diff[4] -= 4  (after end of range)

New diff: [3, 6, -3, 5, -10]
New arr:  [3, 9, 6, 11, 1]  (prefix sum of diff)
```

**Time Complexity:**
- Range update: O(log n) — just two point updates
- Point query: O(log n) — prefix sum query

### Pattern 2: 2D Fenwick Tree

For 2D prefix sums (think: sum of rectangle in matrix).

**Structure:**
- Tree is 2D: `tree[i][j]`
- Each dimension uses lowbit independently

**Update at (x, y):**
```python
def update_2d(x, y, delta):
    i = x + 1
    while i <= n:
        j = y + 1
        while j <= m:
            tree[i][j] += delta
            j += lowbit(j)
        i += lowbit(i)
```

**Query prefix sum to (x, y):**
```python
def query_2d(x, y):
    total = 0
    i = x + 1
    while i > 0:
        j = y + 1
        while j > 0:
            total += tree[i][j]
            j -= lowbit(j)
        i -= lowbit(i)
    return total
```

### Pattern 3: Finding kth Element

**Problem:** Find the kth smallest element in a multiset with updates.

**Solution:** Use Fenwick Tree as a frequency counter!

**Strategy:**
- Index represents value (or compressed value)
- tree[i] stores count of value i
- Finding kth element = binary search on prefix sums

```python
def find_kth(k):
    """Find kth element using binary search on Fenwick Tree"""
    pos = 0
    bit_mask = 1 << 20  # Highest bit for max_value
    
    while bit_mask > 0:
        if pos + bit_mask <= max_val:
            # Check if we can move to this position
            if tree[pos + bit_mask] < k:
                k -= tree[pos + bit_mask]
                pos += bit_mask
        bit_mask >>= 1
    
    return pos + 1
```

**Time Complexity:** O(log² n) or O(log n) with optimization

---

## 5. Problem-Solving Framework

### Mental Model: When to Use Fenwick Tree

**Decision Tree:**

```
Does problem involve dynamic array with queries?
├─ YES
│  └─ What type of queries?
│     ├─ Prefix sum / Range sum
│     │  └─ Use Fenwick Tree ✓
│     ├─ Range minimum/maximum
│     │  └─ Use Segment Tree
│     └─ Range updates + Range queries
│        └─ Use Fenwick Tree (advanced) or Segment Tree with lazy propagation
└─ NO
   └─ Consider other data structures
```

### Expert Problem-Solving Process

**Step 1: Pattern Recognition**
- Keywords: "prefix sum", "range sum", "dynamic updates", "frequency"
- Red flags: "range minimum", "range GCD" → Need Segment Tree instead

**Step 2: Problem Transformation**
Ask: Can I transform this into prefix sum queries?

**Examples:**
- "Count inversions" → For each element, count smaller elements to its right
- "Range XOR" → XOR is associative, use Fenwick with XOR instead of addition
- "Median queries" → Use two Fenwick Trees (one for lower half, one for upper half)

**Step 3: Implementation Strategy**

```
1. Identify what to store in tree
   - Values? Frequencies? Differences?

2. Determine index mapping
   - Direct mapping or coordinate compression?

3. Choose update/query semantics
   - Point update + range query (standard)
   - Range update + point query (difference array)

4. Handle edge cases
   - 0-indexing vs 1-indexing conversion
   - Empty ranges
   - Integer overflow
```

---

## 6. Practice Problems (Progressive Difficulty)

### Level 1: Foundation (Understanding Core Operations)

**Problem 1.1: Range Sum Query - Mutable**
```
Given array arr[], support:
- update(i, val): Set arr[i] = val
- sumRange(l, r): Return sum of arr[l..r]

Input: arr = [1,3,5], update(1,2), sumRange(0,2)
Output: 8
```

**Approach:**
- Direct Fenwick Tree application
- Use `set_value()` for updates

---

**Problem 1.2: Count Smaller Numbers After Self**
```
For each nums[i], count how many j > i where nums[j] < nums[i]

Input: [5,2,6,1]
Output: [2,1,1,0]
Explanation: 
  5: has 2 smaller (2,1)
  2: has 1 smaller (1)
  6: has 1 smaller (1)
  1: has 0 smaller
```

**Thought Process:**
1. Process array from right to left
2. For each element, query how many smaller elements we've seen
3. Add current element to Fenwick Tree

**Key Insight:** Coordinate compression needed if values are large!

---

### Level 2: Intermediate (Pattern Application)

**Problem 2.1: Range Addition**
```
Start with array of zeros, length n.
Perform m updates: add val to [l, r].
Return final array.

Input: n=5, updates=[[1,3,2], [2,4,3], [0,2,-2]]
Output: [-2,0,3,5,3]
```

**Solution Pattern:** Difference array + Fenwick Tree
- Use range update technique (Pattern 1 from above)

---

**Problem 2.2: Rectangle Sum Queries (2D)**
```
Given matrix, support:
- update(row, col, val): Set matrix[row][col] = val
- sumRegion(r1, c1, r2, c2): Sum of rectangle

Input: matrix = [[3,0,1,4,2],
                 [5,6,3,2,1],
                 [1,2,0,1,5]]
Query: sumRegion(1,1,2,2)
Output: 11
```

**Solution:** 2D Fenwick Tree (Pattern 2)

---

### Level 3: Advanced (Creative Transformation)

**Problem 3.1: Count of Range Sum**
```
Count number of range sums in [lower, upper]

Input: nums = [-2,5,-1], lower = -2, upper = 2
Output: 3
Explanation: Ranges [0,0], [2,2], [0,2] have sums in [-2,2]
```

**Solution Outline:**
1. Compute prefix sums
2. For each position, query Fenwick for count of prefix sums in valid range
3. Use coordinate compression for large values
4. Process with careful ordering to avoid counting same range twice

---

**Problem 3.2: Maximum Frequency Stack**
```
Design stack that supports:
- push(x): Push x
- pop(): Remove most frequent (if tie, remove most recent)
- getMaxFreq(): Return current max frequency

Constraint: All operations O(log n)
```

**Solution:** Multiple Fenwick Trees
- One for each frequency level
- Binary search on Fenwick to find kth element

---

## 7. Cognitive Principles for Mastery

### Mental Chunk: The "Fenwick Triple"

Memorize this as ONE mental unit:

```
1. lowbit(i) = i & (-i)      [extracts responsibility]
2. parent(i) = i + lowbit(i) [for updates, move up]
3. prev(i) = i - lowbit(i)   [for queries, move down]
```

### Deliberate Practice Strategy

**Week 1-2: Mechanical Mastery**
- Implement from scratch 10 times without reference
- Draw tree diagrams for sizes 8, 16, 32
- Hand-trace update/query for various indices

**Week 3-4: Pattern Recognition**
- Solve 20 standard problems
- For each: identify the transformation needed
- Practice coordinate compression separately

**Week 5-6: Creative Application**
- Attempt problems that DON'T obviously need Fenwick
- Transform them until they do
- Compare with Segment Tree solutions

### Meta-Learning: Building Intuition

**Visualization Exercise:**
Close your eyes and imagine:
1. Binary representation of index
2. Rightmost bit "lighting up"
3. Following parent pointers upward (update)
4. Following child pointers downward (query)

**Practice until this becomes automatic — like muscle memory.**

---

## 8. Comparison with Alternatives

### Fenwick Tree vs Segment Tree

| Aspect | Fenwick Tree | Segment Tree |
|--------|-------------|--------------|
| **Space** | N | 4N |
| **Code Complexity** | Simple (~20 lines) | Complex (~50 lines) |
| **Operations** | Sum, XOR, GCD | Any associative operation |
| **Range Updates** | Requires tricks | Native support |
| **Constants** | Very fast | Slower (4x memory) |
| **When to use** | Prefix sums, competitive programming | Complex range queries, when clarity matters |

**Rule of Thumb:**
- Can you express query as prefix operation? → Fenwick
- Need range min/max or complex lazy propagation? → Segment Tree

---

## Summary: The Path to Top 1%

**You now understand:**
1. ✓ Why Fenwick Trees exist (trade-off between time and space)
2. ✓ How they work (binary representation + responsibility ranges)
3. ✓ Three implementations (Rust, Python, Go)
4. ✓ Advanced patterns (2D, range updates, kth element)
5. ✓ Problem-solving framework (recognition → transformation → implementation)

**Next Steps:**
1. Implement all three versions from memory
2. Solve all practice problems above
3. Find 10 more problems on LeetCode/Codeforces tagged "Fenwick Tree"
4. Teach it to someone else (Feynman Technique)

**The monk's wisdom:** 
*Master one data structure deeply before moving to the next. A Fenwick Tree understood at the bit level will make Segment Trees trivial.*

You're on the path. Keep the focus. The clarity will come through practice.

Would you like me to:
1. Provide detailed solutions to any practice problem?
2. Explain a specific advanced pattern in more depth?
3. Create a spaced repetition schedule for these concepts?
4. Show you how to debug Fenwick Tree implementations effectively?