# Comprehensive Guide to Monotonic Stacks

## Introduction

A **monotonic stack** is a stack data structure where elements are always arranged in either increasing or decreasing order. Whenever a new element is pushed that would violate the monotonic property, elements are popped until the property can be maintained.

## Core Concepts

### Types of Monotonic Stacks

1. **Monotonic Increasing Stack**: Elements from bottom to top are in increasing order
2. **Monotonic Decreasing Stack**: Elements from bottom to top are in decreasing order

### When to Use Monotonic Stacks

- Finding the **next greater/smaller element** in an array
- Finding the **previous greater/smaller element**
- Computing **span problems** (stock span, histogram areas)
- Solving **visibility problems**
- **Range queries** with min/max constraints

### Time Complexity

- **O(n)** for processing n elements
- Each element is pushed and popped at most once
- Much more efficient than naive O(n²) approaches

## Pattern Recognition

Use a monotonic stack when you need to:
- Find next/previous greater or smaller elements
- Process elements with relationships based on their relative magnitudes
- Maintain running min/max with historical context

## Core Algorithm

### Monotonic Increasing Stack (for Next Greater Element)

```
for each element in array:
    while stack is not empty AND top of stack <= current element:
        pop from stack
    // stack top is now the next greater element for current
    push current element to stack
```

### Monotonic Decreasing Stack (for Next Smaller Element)

```
for each element in array:
    while stack is not empty AND top of stack >= current element:
        pop from stack
    // stack top is now the next smaller element for current
    push current element to stack
```

## Implementation Examples

### Problem 1: Next Greater Element

Given an array, find the next greater element for each element. If no greater element exists, return -1.

**Example**: `[4, 5, 2, 10]` → `[5, 10, 10, -1]`### Problem 2: Largest Rectangle in Histogram

Find the largest rectangular area in a histogram where bars have width 1.

**Example**: Heights `[2, 1, 5, 6, 2, 3]` → Answer: `10` (bars at index 2-3)### Problem 3: Stock Span Problem

Find the span of stock prices - how many consecutive days before the current day had a price less than or equal to the current day's price.

**Example**: Prices `[100, 80, 60, 70, 60, 75, 85]` → Spans `[1, 1, 1, 2, 1, 4, 6]`## Advanced Patterns

### Pattern 1: Finding Boundaries

Use monotonic stacks to find left and right boundaries for each element:

```
For each element, find:
- Previous smaller element (left boundary)
- Next smaller element (right boundary)
```

### Pattern 2: Range Queries

Maintain min/max over sliding windows or subarrays efficiently.

### Pattern 3: Visibility Problems

Determine which elements can "see" each other (useful in geometry, building visibility, etc.).

## Common Variations

### 1. **Next vs Previous**
- Next Greater/Smaller: Iterate left to right
- Previous Greater/Smaller: Iterate right to left (or adjust stack logic)

### 2. **Strict vs Non-Strict**
- Strict (`>` or `<`): Elements must be strictly greater/smaller
- Non-strict (`>=` or `<=`): Equal elements allowed

### 3. **Circular Arrays**
- Process array twice
- Use modulo arithmetic
- Only fill result in first pass

### 4. **2D Extensions**
- Build histograms row by row
- Apply 1D monotonic stack technique to each histogram

## Key Insights

1. **Stack stores indices, not values** - This gives you position information
2. **When you pop, you've found a boundary** - The popped element has found its next greater/smaller
3. **Stack top is always a candidate answer** - For the current element being processed
4. **Each element pushed/popped exactly once** - This guarantees O(n) time
5. **Monotonic property eliminates redundant candidates** - Smaller/larger elements that can't be answers are removed

## Common Pitfalls

1. **Forgetting to process remaining stack elements** after the main loop
2. **Confusing when to use increasing vs decreasing stack**
3. **Off-by-one errors in width calculations**
4. **Not handling empty stack cases** when calculating boundaries
5. **Storing values instead of indices** when position matters

## When NOT to Use Monotonic Stacks

- Need to maintain all elements (not just extremes)
- Problem requires random access or updates
- Need to track multiple properties simultaneously
- Order of processing matters beyond monotonic property

## Practice Problems

**Easy:**
- Next Greater Element I & II
- Remove K Digits
- Remove Duplicate Letters

**Medium:**
- Daily Temperatures
- Online Stock Span
- Sum of Subarray Minimums
- Asteroid Collision
- Minimum Cost Tree From Leaf Values

**Hard:**
- Largest Rectangle in Histogram
- Maximal Rectangle
- Trapping Rain Water
- Maximum Width Ramp
- Sum of Subarray Ranges

## Summary

Monotonic stacks are a powerful technique for solving problems involving:
- Finding next/previous greater or smaller elements
- Computing spans or ranges
- Optimizing from O(n²) to O(n)

The key is recognizing when you need to maintain ordered relationships between elements and when past elements become irrelevant once a better candidate appears.

package main

import "fmt"

// calculateSpan calculates stock span for each day.
// Span = number of consecutive days before (including current)
//
//	where price <= current price.
//
// Time: O(n), Space: O(n)
func calculateSpan(prices []int) []int {
	n := len(prices)
	spans := make([]int, n)
	for i := range spans {
		spans[i] = 1
	}
	
	stack := []int{} // Store indices
	
	for i := 0; i < n; i++ {
		// Pop all days with smaller or equal price
		for len(stack) > 0 && prices[stack[len(stack)-1]] <= prices[i] {
			stack = stack[:len(stack)-1]
		}
		
		// Span is difference from previous greater element
		if len(stack) == 0 {
			spans[i] = i + 1
		} else {
			spans[i] = i - stack[len(stack)-1]
		}
		
		stack = append(stack, i)
	}
	
	return spans
}

// StockSpanner is an online algorithm for stock span.
// Processes prices one at a time as they arrive.
type StockSpanner struct {
	stack []struct {
		price int
		span  int
	}
}

// NewStockSpanner creates a new StockSpanner instance.
func NewStockSpanner() *StockSpanner {
	return &StockSpanner{
		stack: make([]struct {
			price int
			span  int
		}, 0),
	}
}

// Next processes next price and returns its span.
//
// Time: O(1) amortized, Space: O(n)
func (s *StockSpanner) Next(price int) int {
	span := 1
	
	// Aggregate spans of all smaller/equal prices
	for len(s.stack) > 0 && s.stack[len(s.stack)-1].price <= price {
		span += s.stack[len(s.stack)-1].span
		s.stack = s.stack[:len(s.stack)-1]
	}
	
	s.stack = append(s.stack, struct {
		price int
		span  int
	}{price, span})
	
	return span
}

// dailyTemperatures finds how many days until a warmer temperature.
//
// Time: O(n), Space: O(n)
func dailyTemperatures(temperatures []int) []int {
	n := len(temperatures)
	result := make([]int, n)
	stack := []int{} // Store indices
	
	for i := 0; i < n; i++ {
		// Pop all cooler days
		for len(stack) > 0 && temperatures[stack[len(stack)-1]] < temperatures[i] {
			idx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			result[idx] = i - idx
		}
		
		stack = append(stack, i)
	}
	
	return result
}

func main() {
	// Test 1: Basic stock span
	prices1 := []int{100, 80, 60, 70, 60, 75, 85}
	fmt.Printf("Prices: %v\n", prices1)
	fmt.Printf("Spans:  %v\n\n", calculateSpan(prices1))
	
	// Test 2: Online spanner
	fmt.Println("Online StockSpanner:")
	spanner := NewStockSpanner()
	prices2 := []int{100, 80, 60, 70, 60, 75, 85}
	for _, price := range prices2 {
		span := spanner.Next(price)
		fmt.Printf("Price: %d, Span: %d\n", price, span)
	}
	fmt.Println()
	
	// Test 3: Increasing prices
	prices3 := []int{10, 20, 30, 40, 50}
	fmt.Printf("Prices: %v\n", prices3)
	fmt.Printf("Spans:  %v\n\n", calculateSpan(prices3))
	
	// Test 4: Decreasing prices
	prices4 := []int{50, 40, 30, 20, 10}
	fmt.Printf("Prices: %v\n", prices4)
	fmt.Printf("Spans:  %v\n\n", calculateSpan(prices4))
	
	// Test 5: Daily temperatures (related problem)
	temps := []int{73, 74, 75, 71, 69, 72, 76, 73}
	fmt.Printf("Temperatures: %v\n", temps)
	fmt.Printf("Days to wait: %v\n", dailyTemperatures(temps))
}

/// Calculate stock span for each day.
/// Span = number of consecutive days before (including current) 
///        where price <= current price.
/// 
/// Time: O(n), Space: O(n)
fn calculate_span(prices: &[i32]) -> Vec<i32> {
    let n = prices.len();
    let mut spans = vec![1; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        // Pop all days with smaller or equal price
        while let Some(&top_idx) = stack.last() {
            if prices[top_idx] <= prices[i] {
                stack.pop();
            } else {
                break;
            }
        }
        
        // Span is difference from previous greater element
        spans[i] = if stack.is_empty() {
            (i + 1) as i32
        } else {
            (i - stack[stack.len() - 1]) as i32
        };
        
        stack.push(i);
    }
    
    spans
}

/// Online algorithm for stock span.
/// Processes prices one at a time as they arrive.
struct StockSpanner {
    stack: Vec<(i32, i32)>, // Store (price, span) pairs
}

impl StockSpanner {
    fn new() -> Self {
        StockSpanner { stack: Vec::new() }
    }
    
    /// Process next price and return its span.
    /// 
    /// Time: O(1) amortized, Space: O(n)
    fn next(&mut self, price: i32) -> i32 {
        let mut span = 1;
        
        // Aggregate spans of all smaller/equal prices
        while let Some(&(top_price, top_span)) = self.stack.last() {
            if top_price <= price {
                span += top_span;
                self.stack.pop();
            } else {
                break;
            }
        }
        
        self.stack.push((price, span));
        span
    }
}

/// Related problem: Find how many days until a warmer temperature.
/// 
/// Time: O(n), Space: O(n)
fn daily_temperatures(temperatures: &[i32]) -> Vec<i32> {
    let n = temperatures.len();
    let mut result = vec![0; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        // Pop all cooler days
        while let Some(&top_idx) = stack.last() {
            if temperatures[top_idx] < temperatures[i] {
                stack.pop();
                result[top_idx] = (i - top_idx) as i32;
            } else {
                break;
            }
        }
        
        stack.push(i);
    }
    
    result
}

fn main() {
    // Test 1: Basic stock span
    let prices1 = vec![100, 80, 60, 70, 60, 75, 85];
    println!("Prices: {:?}", prices1);
    println!("Spans:  {:?}", calculate_span(&prices1));
    println!();
    
    // Test 2: Online spanner
    println!("Online StockSpanner:");
    let mut spanner = StockSpanner::new();
    let prices2 = vec![100, 80, 60, 70, 60, 75, 85];
    for price in prices2 {
        let span = spanner.next(price);
        println!("Price: {}, Span: {}", price, span);
    }
    println!();
    
    // Test 3: Increasing prices
    let prices3 = vec![10, 20, 30, 40, 50];
    println!("Prices: {:?}", prices3);
    println!("Spans:  {:?}", calculate_span(&prices3));
    println!();
    
    // Test 4: Decreasing prices
    let prices4 = vec![50, 40, 30, 20, 10];
    println!("Prices: {:?}", prices4);
    println!("Spans:  {:?}", calculate_span(&prices4));
    println!();
    
    // Test 5: Daily temperatures (related problem)
    let temps = vec![73, 74, 75, 71, 69, 72, 76, 73];
    println!("Temperatures: {:?}", temps);
    println!("Days to wait: {:?}", daily_temperatures(&temps));
}

def calculate_span(prices):
    """
    Calculate stock span for each day.
    Span = number of consecutive days before (including current) 
           where price <= current price.
    
    Uses monotonic decreasing stack.
    
    Time: O(n), Space: O(n)
    """
    n = len(prices)
    spans = [1] * n
    stack = []  # Store indices
    
    for i in range(n):
        # Pop all days with smaller or equal price
        while stack and prices[stack[-1]] <= prices[i]:
            stack.pop()
        
        # Span is difference from previous greater element
        spans[i] = i + 1 if not stack else i - stack[-1]
        
        stack.append(i)
    
    return spans


class StockSpanner:
    """
    Online algorithm for stock span.
    Processes prices one at a time as they arrive.
    """
    
    def __init__(self):
        self.stack = []  # Store (price, span) pairs
    
    def next(self, price):
        """
        Process next price and return its span.
        
        Time: O(1) amortized, Space: O(n)
        """
        span = 1
        
        # Aggregate spans of all smaller/equal prices
        while self.stack and self.stack[-1][0] <= price:
            span += self.stack.pop()[1]
        
        self.stack.append((price, span))
        return span


def daily_temperatures(temperatures):
    """
    Related problem: Find how many days until a warmer temperature.
    
    Uses monotonic decreasing stack.
    
    Time: O(n), Space: O(n)
    """
    n = len(temperatures)
    result = [0] * n
    stack = []  # Store indices
    
    for i in range(n):
        # Pop all cooler days
        while stack and temperatures[stack[-1]] < temperatures[i]:
            idx = stack.pop()
            result[idx] = i - idx
        
        stack.append(i)
    
    return result


# Test cases
if __name__ == "__main__":
    # Test 1: Basic stock span
    prices1 = [100, 80, 60, 70, 60, 75, 85]
    print(f"Prices: {prices1}")
    print(f"Spans:  {calculate_span(prices1)}")
    print()
    
    # Test 2: Online spanner
    print("Online StockSpanner:")
    spanner = StockSpanner()
    prices2 = [100, 80, 60, 70, 60, 75, 85]
    for price in prices2:
        span = spanner.next(price)
        print(f"Price: {price}, Span: {span}")
    print()
    
    # Test 3: Increasing prices
    prices3 = [10, 20, 30, 40, 50]
    print(f"Prices: {prices3}")
    print(f"Spans:  {calculate_span(prices3)}")
    print()
    
    # Test 4: Decreasing prices
    prices4 = [50, 40, 30, 20, 10]
    print(f"Prices: {prices4}")
    print(f"Spans:  {calculate_span(prices4)}")
    print()
    
    # Test 5: Daily temperatures (related problem)
    temps = [73, 74, 75, 71, 69, 72, 76, 73]
    print(f"Temperatures: {temps}")
    print(f"Days to wait: {daily_temperatures(temps)}")


package main

import "fmt"

// largestRectangleArea finds the largest rectangle area in a histogram.
// Uses monotonic increasing stack to track potential rectangles.
//
// Time: O(n), Space: O(n)
func largestRectangleArea(heights []int) int {
	stack := []int{} // Store indices
	maxArea := 0
	
	for i := 0; i < len(heights); i++ {
		// Pop all bars taller than current
		for len(stack) > 0 && heights[stack[len(stack)-1]] > heights[i] {
			heightIdx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			height := heights[heightIdx]
			
			// Width: from element after previous stack top to current-1
			width := i
			if len(stack) > 0 {
				width = i - stack[len(stack)-1] - 1
			}
			
			if height*width > maxArea {
				maxArea = height * width
			}
		}
		
		stack = append(stack, i)
	}
	
	// Process remaining bars
	for len(stack) > 0 {
		heightIdx := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		height := heights[heightIdx]
		
		width := len(heights)
		if len(stack) > 0 {
			width = len(heights) - stack[len(stack)-1] - 1
		}
		
		if height*width > maxArea {
			maxArea = height * width
		}
	}
	
	return maxArea
}

// largestRectangleWithSentinel is a cleaner version using sentinel value.
// Add 0 at the end to flush all remaining bars.
//
// Time: O(n), Space: O(n)
func largestRectangleWithSentinel(heights []int) int {
	// Add sentinel
	heightsExt := make([]int, len(heights)+1)
	copy(heightsExt, heights)
	heightsExt[len(heights)] = 0
	
	stack := []int{}
	maxArea := 0
	
	for i := 0; i < len(heightsExt); i++ {
		for len(stack) > 0 && heightsExt[stack[len(stack)-1]] > heightsExt[i] {
			heightIdx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			height := heightsExt[heightIdx]
			
			width := i
			if len(stack) > 0 {
				width = i - stack[len(stack)-1] - 1
			}
			
			if height*width > maxArea {
				maxArea = height * width
			}
		}
		
		stack = append(stack, i)
	}
	
	return maxArea
}

// maximalRectangleMatrix finds largest rectangle of 1s in binary matrix.
// Builds histogram row by row and uses largestRectangleArea.
//
// Time: O(rows * cols), Space: O(cols)
func maximalRectangleMatrix(matrix [][]byte) int {
	if len(matrix) == 0 || len(matrix[0]) == 0 {
		return 0
	}
	
	cols := len(matrix[0])
	heights := make([]int, cols)
	maxArea := 0
	
	for _, row := range matrix {
		// Build histogram for current row
		for j := 0; j < cols; j++ {
			if row[j] == '1' {
				heights[j]++
			} else {
				heights[j] = 0
			}
		}
		
		// Find max rectangle in current histogram
		area := largestRectangleArea(heights)
		if area > maxArea {
			maxArea = area
		}
	}
	
	return maxArea
}

func main() {
	// Test 1: Basic histogram
	hist1 := []int{2, 1, 5, 6, 2, 3}
	fmt.Printf("Histogram: %v\n", hist1)
	fmt.Printf("Largest rectangle: %d\n", largestRectangleArea(hist1))
	fmt.Printf("With sentinel: %d\n\n", largestRectangleWithSentinel(hist1))
	
	// Test 2: Increasing heights
	hist2 := []int{1, 2, 3, 4, 5}
	fmt.Printf("Histogram: %v\n", hist2)
	fmt.Printf("Largest rectangle: %d\n\n", largestRectangleArea(hist2))
	
	// Test 3: Single bar
	hist3 := []int{5}
	fmt.Printf("Histogram: %v\n", hist3)
	fmt.Printf("Largest rectangle: %d\n\n", largestRectangleArea(hist3))
	
	// Test 4: Matrix with 1s
	matrix := [][]byte{
		{'1', '0', '1', '0', '0'},
		{'1', '0', '1', '1', '1'},
		{'1', '1', '1', '1', '1'},
		{'1', '0', '0', '1', '0'},
	}
	fmt.Println("Matrix:")
	for _, row := range matrix {
		fmt.Printf("%c\n", row)
	}
	fmt.Printf("Maximal rectangle area: %d\n", maximalRectangleMatrix(matrix))
}

use std::cmp::max;

/// Find the largest rectangle area in a histogram.
/// Uses monotonic increasing stack to track potential rectangles.
/// 
/// Time: O(n), Space: O(n)
fn largest_rectangle_area(heights: &[i32]) -> i32 {
    let mut stack: Vec<usize> = Vec::new();
    let mut max_area = 0;
    
    for i in 0..heights.len() {
        // Pop all bars taller than current
        while let Some(&top_idx) = stack.last() {
            if heights[top_idx] > heights[i] {
                stack.pop();
                let height = heights[top_idx];
                
                // Width: from element after previous stack top to current-1
                let width = if stack.is_empty() {
                    i as i32
                } else {
                    (i - stack[stack.len() - 1] - 1) as i32
                };
                
                max_area = max(max_area, height * width);
            } else {
                break;
            }
        }
        
        stack.push(i);
    }
    
    // Process remaining bars
    while let Some(top_idx) = stack.pop() {
        let height = heights[top_idx];
        let width = if stack.is_empty() {
            heights.len() as i32
        } else {
            (heights.len() - stack[stack.len() - 1] - 1) as i32
        };
        
        max_area = max(max_area, height * width);
    }
    
    max_area
}

/// Cleaner version using sentinel value.
/// Add 0 at the end to flush all remaining bars.
/// 
/// Time: O(n), Space: O(n)
fn largest_rectangle_with_sentinel(heights: &[i32]) -> i32 {
    let mut heights_extended = heights.to_vec();
    heights_extended.push(0); // Add sentinel
    
    let mut stack: Vec<usize> = Vec::new();
    let mut max_area = 0;
    
    for i in 0..heights_extended.len() {
        while let Some(&top_idx) = stack.last() {
            if heights_extended[top_idx] > heights_extended[i] {
                stack.pop();
                let height = heights_extended[top_idx];
                
                let width = if stack.is_empty() {
                    i as i32
                } else {
                    (i - stack[stack.len() - 1] - 1) as i32
                };
                
                max_area = max(max_area, height * width);
            } else {
                break;
            }
        }
        
        stack.push(i);
    }
    
    max_area
}

/// Find largest rectangle of 1s in binary matrix.
/// Builds histogram row by row and uses largest_rectangle_area.
/// 
/// Time: O(rows * cols), Space: O(cols)
fn maximal_rectangle_matrix(matrix: &[Vec<char>]) -> i32 {
    if matrix.is_empty() || matrix[0].is_empty() {
        return 0;
    }
    
    let cols = matrix[0].len();
    let mut heights = vec![0; cols];
    let mut max_area = 0;
    
    for row in matrix {
        // Build histogram for current row
        for j in 0..cols {
            if row[j] == '1' {
                heights[j] += 1;
            } else {
                heights[j] = 0;
            }
        }
        
        // Find max rectangle in current histogram
        max_area = max(max_area, largest_rectangle_area(&heights));
    }
    
    max_area
}

fn main() {
    // Test 1: Basic histogram
    let hist1 = vec![2, 1, 5, 6, 2, 3];
    println!("Histogram: {:?}", hist1);
    println!("Largest rectangle: {}", largest_rectangle_area(&hist1));
    println!("With sentinel: {}", largest_rectangle_with_sentinel(&hist1));
    println!();
    
    // Test 2: Increasing heights
    let hist2 = vec![1, 2, 3, 4, 5];
    println!("Histogram: {:?}", hist2);
    println!("Largest rectangle: {}", largest_rectangle_area(&hist2));
    println!();
    
    // Test 3: Single bar
    let hist3 = vec![5];
    println!("Histogram: {:?}", hist3);
    println!("Largest rectangle: {}", largest_rectangle_area(&hist3));
    println!();
    
    // Test 4: Matrix with 1s
    let matrix = vec![
        vec!['1', '0', '1', '0', '0'],
        vec!['1', '0', '1', '1', '1'],
        vec!['1', '1', '1', '1', '1'],
        vec!['1', '0', '0', '1', '0'],
    ];
    println!("Matrix:");
    for row in &matrix {
        println!("{:?}", row);
    }
    println!("Maximal rectangle area: {}", maximal_rectangle_matrix(&matrix));
}

def largest_rectangle_area(heights):
    """
    Find the largest rectangle area in a histogram.
    Uses monotonic increasing stack to track potential rectangles.
    
    Key insight: When we pop a height, it means we've found its right boundary.
    The left boundary is the element below it in the stack.
    
    Time: O(n), Space: O(n)
    """
    stack = []  # Store indices
    max_area = 0
    
    for i, h in enumerate(heights):
        # Pop all bars taller than current
        while stack and heights[stack[-1]] > h:
            height_idx = stack.pop()
            height = heights[height_idx]
            
            # Width: from element after previous stack top to current-1
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    # Process remaining bars
    while stack:
        height_idx = stack.pop()
        height = heights[height_idx]
        width = len(heights) if not stack else len(heights) - stack[-1] - 1
        max_area = max(max_area, height * width)
    
    return max_area


def largest_rectangle_with_sentinel(heights):
    """
    Cleaner version using sentinel value to avoid duplicate code.
    Add 0 at the end to flush all remaining bars.
    
    Time: O(n), Space: O(n)
    """
    stack = []
    max_area = 0
    heights = heights + [0]  # Add sentinel
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height_idx = stack.pop()
            height = heights[height_idx]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    return max_area


def maximal_rectangle_matrix(matrix):
    """
    Find largest rectangle of 1s in binary matrix.
    Builds histogram row by row and uses largest_rectangle_area.
    
    Time: O(rows * cols), Space: O(cols)
    """
    if not matrix or not matrix[0]:
        return 0
    
    rows, cols = len(matrix), len(matrix[0])
    heights = [0] * cols
    max_area = 0
    
    for row in matrix:
        # Build histogram for current row
        for j in range(cols):
            if row[j] == '1':
                heights[j] += 1
            else:
                heights[j] = 0
        
        # Find max rectangle in current histogram
        max_area = max(max_area, largest_rectangle_area(heights[:]))
    
    return max_area


# Test cases
if __name__ == "__main__":
    # Test 1: Basic histogram
    hist1 = [2, 1, 5, 6, 2, 3]
    print(f"Histogram: {hist1}")
    print(f"Largest rectangle: {largest_rectangle_area(hist1)}")
    print(f"With sentinel: {largest_rectangle_with_sentinel(hist1[:])}") 
    print()
    
    # Test 2: Increasing heights
    hist2 = [1, 2, 3, 4, 5]
    print(f"Histogram: {hist2}")
    print(f"Largest rectangle: {largest_rectangle_area(hist2)}")
    print()
    
    # Test 3: Single bar
    hist3 = [5]
    print(f"Histogram: {hist3}")
    print(f"Largest rectangle: {largest_rectangle_area(hist3)}")
    print()
    
    # Test 4: Matrix with 1s
    matrix = [
        ['1', '0', '1', '0', '0'],
        ['1', '0', '1', '1', '1'],
        ['1', '1', '1', '1', '1'],
        ['1', '0', '0', '1', '0']
    ]
    print("Matrix:")
    for row in matrix:
        print(row)
    print(f"Maximal rectangle area: {maximal_rectangle_matrix(matrix)}")

package main

import "fmt"

// nextGreaterElement finds the next greater element for each element.
// Uses a monotonic decreasing stack.
//
// Time: O(n), Space: O(n)
func nextGreaterElement(nums []int) []int {
	n := len(nums)
	result := make([]int, n)
	for i := range result {
		result[i] = -1
	}
	
	stack := []int{} // Store indices
	
	for i := 0; i < n; i++ {
		// Pop elements smaller than current
		for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[i] {
			idx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			result[idx] = nums[i]
		}
		
		stack = append(stack, i)
	}
	
	return result
}

// nextGreaterCircular finds next greater element in a circular array.
// Process array twice but only fill result once.
//
// Time: O(n), Space: O(n)
func nextGreaterCircular(nums []int) []int {
	n := len(nums)
	result := make([]int, n)
	for i := range result {
		result[i] = -1
	}
	
	stack := []int{}
	
	// Process array twice to handle circular nature
	for i := 0; i < 2*n; i++ {
		idx := i % n
		
		for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[idx] {
			topIdx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			result[topIdx] = nums[idx]
		}
		
		// Only push indices in first pass
		if i < n {
			stack = append(stack, idx)
		}
	}
	
	return result
}

func main() {
	// Test 1: Basic next greater
	arr1 := []int{4, 5, 2, 10}
	fmt.Printf("Array: %v\n", arr1)
	fmt.Printf("Next greater: %v\n\n", nextGreaterElement(arr1))
	
	// Test 2: Decreasing array
	arr2 := []int{10, 8, 6, 4, 2}
	fmt.Printf("Array: %v\n", arr2)
	fmt.Printf("Next greater: %v\n\n", nextGreaterElement(arr2))
	
	// Test 3: Circular array
	arr3 := []int{1, 2, 1}
	fmt.Printf("Circular array: %v\n", arr3)
	fmt.Printf("Next greater (circular): %v\n\n", nextGreaterCircular(arr3))
	
	// Test 4: Complex example
	arr4 := []int{2, 1, 2, 4, 3}
	fmt.Printf("Array: %v\n", arr4)
	fmt.Printf("Next greater: %v\n", nextGreaterElement(arr4))
	fmt.Printf("Next greater (circular): %v\n", nextGreaterCircular(arr4))
}

/// Find the next greater element for each element in the array.
/// Uses a monotonic decreasing stack.
/// 
/// Time: O(n), Space: O(n)
fn next_greater_element(nums: &[i32]) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        // Pop elements smaller than current
        while let Some(&top_idx) = stack.last() {
            if nums[top_idx] < nums[i] {
                stack.pop();
                result[top_idx] = nums[i];
            } else {
                break;
            }
        }
        
        stack.push(i);
    }
    
    result
}

/// Find next greater element in a circular array.
/// Process array twice but only fill result once.
/// 
/// Time: O(n), Space: O(n)
fn next_greater_circular(nums: &[i32]) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new();
    
    // Process array twice to handle circular nature
    for i in 0..(2 * n) {
        let idx = i % n;
        
        while let Some(&top_idx) = stack.last() {
            if nums[top_idx] < nums[idx] {
                stack.pop();
                result[top_idx] = nums[idx];
            } else {
                break;
            }
        }
        
        // Only push indices in first pass
        if i < n {
            stack.push(idx);
        }
    }
    
    result
}

fn main() {
    // Test 1: Basic next greater
    let arr1 = vec![4, 5, 2, 10];
    println!("Array: {:?}", arr1);
    println!("Next greater: {:?}", next_greater_element(&arr1));
    println!();
    
    // Test 2: Decreasing array
    let arr2 = vec![10, 8, 6, 4, 2];
    println!("Array: {:?}", arr2);
    println!("Next greater: {:?}", next_greater_element(&arr2));
    println!();
    
    // Test 3: Circular array
    let arr3 = vec![1, 2, 1];
    println!("Circular array: {:?}", arr3);
    println!("Next greater (circular): {:?}", next_greater_circular(&arr3));
    println!();
    
    // Test 4: Complex example
    let arr4 = vec![2, 1, 2, 4, 3];
    println!("Array: {:?}", arr4);
    println!("Next greater: {:?}", next_greater_element(&arr4));
    println!("Next greater (circular): {:?}", next_greater_circular(&arr4));
}

def next_greater_element(nums):
    """
    Find the next greater element for each element in the array.
    Uses a monotonic decreasing stack.
    
    Time: O(n), Space: O(n)
    """
    n = len(nums)
    result = [-1] * n
    stack = []  # Store indices
    
    for i in range(n):
        # Pop elements smaller than current
        while stack and nums[stack[-1]] < nums[i]:
            idx = stack.pop()
            result[idx] = nums[i]
        
        stack.append(i)
    
    return result


def next_greater_circular(nums):
    """
    Find next greater element in a circular array.
    Trick: Process array twice but only fill result once.
    
    Time: O(n), Space: O(n)
    """
    n = len(nums)
    result = [-1] * n
    stack = []
    
    # Process array twice to handle circular nature
    for i in range(2 * n):
        idx = i % n
        
        while stack and nums[stack[-1]] < nums[idx]:
            result[stack.pop()] = nums[idx]
        
        # Only push indices in first pass
        if i < n:
            stack.append(idx)
    
    return result


# Test cases
if __name__ == "__main__":
    # Test 1: Basic next greater
    arr1 = [4, 5, 2, 10]
    print(f"Array: {arr1}")
    print(f"Next greater: {next_greater_element(arr1)}")
    print()
    
    # Test 2: Decreasing array
    arr2 = [10, 8, 6, 4, 2]
    print(f"Array: {arr2}")
    print(f"Next greater: {next_greater_element(arr2)}")
    print()
    
    # Test 3: Circular array
    arr3 = [1, 2, 1]
    print(f"Circular array: {arr3}")
    print(f"Next greater (circular): {next_greater_circular(arr3)}")
    print()
    
    # Test 4: Complex example
    arr4 = [2, 1, 2, 4, 3]
    print(f"Array: {arr4}")
    print(f"Next greater: {next_greater_element(arr4)}")
    print(f"Next greater (circular): {next_greater_circular(arr4)}")