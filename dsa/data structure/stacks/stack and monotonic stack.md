# Stack & Monotonic Stack: The Complete Mastery Guide

## Table of Contents
1. [Foundation: What is a Stack?](#foundation)
2. [Core Operations & Complexity](#operations)
3. [Implementation in Rust, Python, Go](#implementation)
4. [Mental Models & Intuition](#mental-models)
5. [Classic Stack Patterns](#classic-patterns)
6. [Monotonic Stack: The Game Changer](#monotonic-stack)
7. [Problem-Solving Framework](#framework)
8. [Practice Problems with Solutions](#practice)

---

## 1. Foundation: What is a Stack? {#foundation}

### The Essence

A **stack** is a linear data structure that follows the **LIFO principle** (Last In, First Out). Think of it like a stack of plates: you can only add or remove plates from the top.

```
Conceptual Visualization:

    TOP
    ↓
   [5]  ← Most recently added (will be removed first)
   [3]
   [8]
   [1]  ← First added (will be removed last)
  -----
  STACK
```

### The LIFO Principle Explained

**LIFO** = **L**ast **I**n, **F**irst **O**ut

The element that enters last is the first to exit. This ordering is crucial and differentiates stacks from queues (FIFO).

### Real-World Analogies
- **Browser history**: Back button (undo last action)
- **Function call stack**: Most recent function must finish first
- **Text editor undo**: Most recent change undone first
- **Plates in cafeteria**: Take from top, add to top

---

## 2. Core Operations & Complexity {#operations}

### Primary Operations

```
┌─────────────────────────────────────────────────┐
│              STACK OPERATIONS                   │
├─────────────────────────────────────────────────┤
│ Operation    │ Description      │ Time  │ Space │
├──────────────┼──────────────────┼───────┼───────┤
│ push(x)      │ Add to top       │ O(1)  │ O(1)  │
│ pop()        │ Remove from top  │ O(1)  │ O(1)  │
│ peek/top()   │ View top element │ O(1)  │ O(1)  │
│ isEmpty()    │ Check if empty   │ O(1)  │ O(1)  │
│ size()       │ Get count        │ O(1)  │ O(1)  │
└──────────────┴──────────────────┴───────┴───────┘
```

### Operation Flow Diagram

```
PUSH Operation:
   Before          After
   [3]             [7] ← new top
   [1]             [3]
   ---             [1]
                   ---

POP Operation:
   Before          After
   [7] ← remove    [3] ← new top
   [3]             [1]
   [1]             ---
   ---
```

### Why O(1) Matters

**Constant time operations** are critical because:
- No matter how many elements exist, push/pop takes the same time
- Enables efficient algorithm design
- Predictable performance at scale

**Mental Model**: Accessing the top is like looking at the topmost plate—you don't need to count or search through the stack.

---

## 3. Implementation in Rust, Python, Go {#implementation}

### Python Implementation

```python
class Stack:
    """
    Stack implementation using Python list.
    
    Complexity:
    - All operations: O(1) time, O(1) space
    - Storage: O(n) where n = number of elements
    """
    
    def __init__(self):
        self._items = []  # Internal storage
    
    def push(self, item):
        """Add element to top of stack"""
        self._items.append(item)
    
    def pop(self):
        """Remove and return top element
        Raises IndexError if stack is empty"""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    
    def peek(self):
        """Return top element without removing
        Raises IndexError if stack is empty"""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]
    
    def is_empty(self):
        """Check if stack has no elements"""
        return len(self._items) == 0
    
    def size(self):
        """Return number of elements"""
        return len(self._items)
    
    def __repr__(self):
        return f"Stack({self._items})"


# Usage Example
stack = Stack()
stack.push(1)
stack.push(2)
stack.push(3)
print(stack.peek())  # 3
print(stack.pop())   # 3
print(stack.size())  # 2
```

**Python Idiomatic Note**: Python lists are dynamic arrays with amortized O(1) append/pop from the end, making them perfect for stacks.

### Rust Implementation

```rust
/// Stack implementation using Vec<T>
/// Generic over type T that must be sized
#[derive(Debug)]
pub struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    /// Create a new empty stack
    pub fn new() -> Self {
        Stack { items: Vec::new() }
    }
    
    /// Create stack with specified capacity
    /// Useful for performance when size is known
    pub fn with_capacity(capacity: usize) -> Self {
        Stack {
            items: Vec::with_capacity(capacity),
        }
    }
    
    /// Add element to top - O(1) amortized
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    /// Remove and return top element - O(1)
    /// Returns None if stack is empty
    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    /// View top element without removing - O(1)
    /// Returns None if stack is empty
    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    /// Mutable reference to top element
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.items.last_mut()
    }
    
    /// Check if stack is empty - O(1)
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    /// Get number of elements - O(1)
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Usage Example
fn main() {
    let mut stack = Stack::new();
    stack.push(1);
    stack.push(2);
    stack.push(3);
    
    println!("{:?}", stack.peek());  // Some(3)
    println!("{:?}", stack.pop());   // Some(3)
    println!("{}", stack.len());     // 2
}
```

**Rust Idiomatic Notes**:
- Uses `Option<T>` for safe operations (no panics)
- Ownership model ensures memory safety
- `with_capacity` pre-allocates for known sizes (performance optimization)
- Generic implementation works with any type

### Go Implementation

```go
package main

import (
    "errors"
    "fmt"
)

// Stack implementation using slice
type Stack struct {
    items []int  // Can be made generic with Go 1.18+
}

// NewStack creates a new empty stack
func NewStack() *Stack {
    return &Stack{
        items: make([]int, 0),
    }
}

// NewStackWithCapacity creates stack with pre-allocated capacity
func NewStackWithCapacity(capacity int) *Stack {
    return &Stack{
        items: make([]int, 0, capacity),
    }
}

// Push adds element to top - O(1) amortized
func (s *Stack) Push(item int) {
    s.items = append(s.items, item)
}

// Pop removes and returns top element - O(1)
func (s *Stack) Pop() (int, error) {
    if s.IsEmpty() {
        return 0, errors.New("pop from empty stack")
    }
    
    lastIndex := len(s.items) - 1
    item := s.items[lastIndex]
    s.items = s.items[:lastIndex]  // Reslice
    
    return item, nil
}

// Peek returns top element without removing - O(1)
func (s *Stack) Peek() (int, error) {
    if s.IsEmpty() {
        return 0, errors.New("peek from empty stack")
    }
    return s.items[len(s.items)-1], nil
}

// IsEmpty checks if stack has no elements
func (s *Stack) IsEmpty() bool {
    return len(s.items) == 0
}

// Size returns number of elements
func (s *Stack) Size() int {
    return len(s.items)
}

// Usage Example
func main() {
    stack := NewStack()
    stack.Push(1)
    stack.Push(2)
    stack.Push(3)
    
    top, _ := stack.Peek()
    fmt.Println(top)  // 3
    
    val, _ := stack.Pop()
    fmt.Println(val)  // 3
    
    fmt.Println(stack.Size())  // 2
}

// Generic version (Go 1.18+)
type GenericStack[T any] struct {
    items []T
}

func NewGenericStack[T any]() *GenericStack[T] {
    return &GenericStack[T]{items: make([]T, 0)}
}

func (s *GenericStack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *GenericStack[T]) Pop() (T, error) {
    var zero T
    if len(s.items) == 0 {
        return zero, errors.New("pop from empty stack")
    }
    lastIndex := len(s.items) - 1
    item := s.items[lastIndex]
    s.items = s.items[:lastIndex]
    return item, nil
}
```

**Go Idiomatic Notes**:
- Error handling through multiple return values
- Pointer receiver for mutation methods
- Pre-allocation with capacity for performance
- Generic version available in Go 1.18+

---

## 4. Mental Models & Intuition {#mental-models}

### The "Undo" Model

**Core Insight**: Stacks naturally model operations that need to be reversed in opposite order.

```
Action Sequence:      Stack State:
─────────────────     ─────────────
Write "A"       →     [A]
Write "B"       →     [B, A]
Write "C"       →     [C, B, A]
Undo            →     [B, A]        (removed C)
Undo            →     [A]           (removed B)
```

**When to think "Stack"**:
- Reversing sequences
- Matching pairs (parentheses, brackets)
- Backtracking algorithms
- Nested structures

### The "Tunnel" Model

Imagine a tunnel with one entrance/exit:
- Cars enter in order: Red, Blue, Green
- Must exit in reverse: Green, Blue, Red
- Cannot access middle cars directly

```
TUNNEL (Stack):
Entry/Exit →  [Green][Blue][Red]  ← Closed end
              ↑ top
```

### Cognitive Framework: "What Do I Need Later?"

**Key Question**: "Will I need to remember things in reverse order of encountering them?"

**Decision Tree**:
```
                    Need to process data?
                           |
            ┌──────────────┴──────────────┐
            ↓                             ↓
    Reverse order needed?         Same order needed?
            |                             |
      ┌─────┴─────┐                      |
      ↓           ↓                      ↓
    YES          NO                   QUEUE
      |           |                   (FIFO)
    STACK      Consider
    (LIFO)    other DS
```

---

## 5. Classic Stack Patterns {#classic-patterns}

### Pattern 1: Balanced Parentheses

**Problem**: Check if brackets are properly matched: `({[]})`

**Intuition**: Each opening bracket must match the most recent unmatched opening bracket.

```
Algorithm Flow:
─────────────────
Input: "({[]})"

Step 1: '(' → push        Stack: [(]
Step 2: '{' → push        Stack: [{, (]
Step 3: '[' → push        Stack: [[, {, (]
Step 4: ']' → pop [       Stack: [{, (]  ✓ matches
Step 5: '}' → pop {       Stack: [(]     ✓ matches
Step 6: ')' → pop (       Stack: []      ✓ matches

Result: VALID (stack empty)
```

**Implementation (Python)**:

```python
def is_valid_parentheses(s: str) -> bool:
    """
    Check if parentheses are balanced.
    
    Time: O(n) - single pass
    Space: O(n) - worst case all opening brackets
    """
    stack = []
    # Mapping of closing to opening brackets
    pairs = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in pairs:  # Closing bracket
            # Check if matches top of stack
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
        else:  # Opening bracket
            stack.append(char)
    
    # Valid only if all brackets matched
    return len(stack) == 0


# Test cases
print(is_valid_parentheses("()[]{}"))    # True
print(is_valid_parentheses("([)]"))      # False - wrong nesting
print(is_valid_parentheses("{[]}"))      # True
```

**Rust Implementation**:

```rust
pub fn is_valid(s: String) -> bool {
    let mut stack = Vec::new();
    
    for ch in s.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' => if stack.pop() != Some('(') { return false; },
            ']' => if stack.pop() != Some('[') { return false; },
            '}' => if stack.pop() != Some('{') { return false; },
            _ => {},  // Ignore other characters
        }
    }
    
    stack.is_empty()
}
```

### Pattern 2: Evaluate Postfix Expression

**Postfix Notation Explained**: Operators come after operands.
- Infix: `3 + 4`
- Postfix: `3 4 +`

**Why Postfix?** No need for parentheses or operator precedence rules.

```
Example: "2 3 + 4 *"
Meaning: (2 + 3) * 4 = 20

Processing:
───────────
Token  Action           Stack
─────  ──────────────   ─────
2      push             [2]
3      push             [3, 2]
+      pop 3,2 → 2+3    [5]
4      push             [4, 5]
*      pop 4,5 → 5*4    [20]

Result: 20
```

**Implementation (Python)**:

```python
def eval_postfix(expression: str) -> int:
    """
    Evaluate postfix expression.
    
    Time: O(n) - process each token once
    Space: O(n) - stack can hold all operands
    """
    stack = []
    operators = {'+', '-', '*', '/'}
    
    for token in expression.split():
        if token in operators:
            # Pop two operands (order matters!)
            b = stack.pop()  # Second operand
            a = stack.pop()  # First operand
            
            # Apply operation
            if token == '+':
                result = a + b
            elif token == '-':
                result = a - b
            elif token == '*':
                result = a * b
            else:  # '/'
                result = a // b  # Integer division
            
            stack.append(result)
        else:
            # It's a number
            stack.append(int(token))
    
    return stack[0]


# Test
print(eval_postfix("2 3 + 4 *"))  # 20
print(eval_postfix("5 1 2 + 4 * + 3 -"))  # 14
```

### Pattern 3: Next Greater Element

**Problem**: For each element, find the next greater element to its right.

```
Input:  [4, 5, 2, 10, 8]
Output: [5, 10, 10, -1, -1]

Explanation:
4 → next greater is 5
5 → next greater is 10
2 → next greater is 10
10 → no greater element (-1)
8 → no greater element (-1)
```

**Brute Force** (O(n²)): For each element, scan remaining elements.

**Optimized with Stack** (O(n)): 
- Traverse right to left
- Maintain stack of candidates for "next greater"
- Stack keeps decreasing elements

```
Algorithm Visualization:
────────────────────────
Input: [4, 5, 2, 10, 8]
Process from right to left:

i=4, num=8:  stack=[] → push 8 → result[4]=-1
             stack=[8]

i=3, num=10: stack=[8]
             pop 8 (10>8) → stack=[]
             push 10 → result[3]=-1
             stack=[10]

i=2, num=2:  stack=[10]
             10>2, so result[2]=10
             push 2
             stack=[2, 10]

i=1, num=5:  stack=[2, 10]
             pop 2 (5>2) → stack=[10]
             10>5, so result[1]=10
             push 5
             stack=[5, 10]

i=0, num=4:  stack=[5, 10]
             5>4, so result[0]=5
             push 4
             stack=[4, 5, 10]
```

**Implementation (Python)**:

```python
def next_greater_element(nums: list[int]) -> list[int]:
    """
    Find next greater element for each element.
    
    Time: O(n) - each element pushed/popped once
    Space: O(n) - stack storage
    """
    n = len(nums)
    result = [-1] * n
    stack = []  # Store indices
    
    # Traverse from right to left
    for i in range(n - 1, -1, -1):
        # Pop elements smaller than current
        while stack and nums[stack[-1]] <= nums[i]:
            stack.pop()
        
        # Top of stack is next greater
        if stack:
            result[i] = nums[stack[-1]]
        
        # Push current index
        stack.append(i)
    
    return result


# Test
print(next_greater_element([4, 5, 2, 10, 8]))  # [5, 10, 10, -1, -1]
```

---

## 6. Monotonic Stack: The Game Changer {#monotonic-stack}

### What is a Monotonic Stack?

**Definition**: A stack where elements are always in **increasing** or **decreasing** order from bottom to top.

**Key Insight**: By maintaining order, we can efficiently answer "next greater/smaller" queries.

### Types of Monotonic Stacks

```
┌────────────────────────────────────────────────┐
│          MONOTONIC STACK TYPES                 │
├────────────────────────────────────────────────┤
│                                                │
│  1. STRICTLY INCREASING (bottom → top)         │
│     [1, 3, 5, 7]                               │
│      ↑         ↑                               │
│    bottom    top                               │
│     Use: Find Next Smaller Element             │
│                                                │
│  2. STRICTLY DECREASING (bottom → top)         │
│     [9, 6, 4, 2]                               │
│      ↑         ↑                               │
│    bottom    top                               │
│     Use: Find Next Greater Element             │
│                                                │
│  3. NON-INCREASING (allows equals)             │
│     [9, 6, 6, 2]                               │
│                                                │
│  4. NON-DECREASING (allows equals)             │
│     [1, 3, 3, 7]                               │
└────────────────────────────────────────────────┘
```

### How Monotonic Stack Works

**Core Mechanism**: Pop elements that violate the monotonic property before pushing new element.

```
Building Decreasing Monotonic Stack:
────────────────────────────────────
Input: [5, 3, 7, 2, 4]

Step 1: num=5
Stack: [] → push 5 → [5]

Step 2: num=3
Stack: [5]
3 < 5, violates decreasing order → pop 5
Push 3 → [3]

Step 3: num=7
Stack: [3]
7 > 3, maintains decreasing order → push 7
Stack: [3, 7]

Step 4: num=2
Stack: [3, 7]
2 < 7, violates → pop 7
2 < 3, violates → pop 3
Push 2 → [2]

Step 5: num=4
Stack: [2]
4 > 2, maintains → push 4
Stack: [2, 4]
```

### Problem Pattern Recognition

**Use Monotonic Stack When**:
- Need to find next/previous greater/smaller element
- Need to find span/range of influence
- Working with histogram, temperature, stock problems

```
Decision Tree:
──────────────
                  Array traversal problem?
                           |
                    ┌──────┴──────┐
                    ↓             ↓
            Next/Prev          Other
            Greater/Smaller    pattern
                    |
                    ↓
              MONOTONIC STACK
                    |
            ┌───────┴────────┐
            ↓                ↓
      Next Greater      Next Smaller
      (Decreasing)      (Increasing)
```

### Classic Problem: Daily Temperatures

**Problem**: Given daily temperatures, return how many days until warmer temperature.

```
Input:  [73, 74, 75, 71, 69, 72, 76, 73]
Output: [1,  1,  4,  2,  1,  1,  0,  0]

Explanation:
73 → 1 day until 74
74 → 1 day until 75
75 → 4 days until 76
71 → 2 days until 72
69 → 1 day until 72
72 → 1 day until 76
76 → no warmer day (0)
73 → no warmer day (0)
```

**Monotonic Stack Solution**:

```python
def daily_temperatures(temps: list[int]) -> list[int]:
    """
    Calculate days until warmer temperature.
    
    Strategy: Monotonic decreasing stack (stores indices)
    - Traverse left to right
    - When current temp > stack top temp:
      - We found answer for stack top
      - Pop and record distance
    
    Time: O(n) - each index pushed/popped once
    Space: O(n) - stack size
    """
    n = len(temps)
    result = [0] * n
    stack = []  # Stores indices of temperatures
    
    for i in range(n):
        # While current temp is greater than stack top temp
        while stack and temps[i] > temps[stack[-1]]:
            prev_idx = stack.pop()
            # Distance is current index - previous index
            result[prev_idx] = i - prev_idx
        
        # Push current index
        stack.append(i)
    
    # Remaining indices have no warmer day
    return result


# Test
print(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]))
# [1, 1, 4, 2, 1, 1, 0, 0]
```

**Step-by-Step Visualization**:

```
temps = [73, 74, 75, 71, 69, 72, 76, 73]
         i=0 i=1 i=2 i=3 i=4 i=5 i=6 i=7

i=0 (73): stack=[] → push 0 → [0]

i=1 (74): 74 > temps[0]=73
          pop 0, result[0] = 1-0 = 1
          push 1 → [1]

i=2 (75): 75 > temps[1]=74
          pop 1, result[1] = 2-1 = 1
          push 2 → [2]

i=3 (71): 71 < 75 → push 3 → [2, 3]

i=4 (69): 69 < 71 → push 4 → [2, 3, 4]

i=5 (72): 72 > temps[4]=69
          pop 4, result[4] = 5-4 = 1
          72 > temps[3]=71
          pop 3, result[3] = 5-3 = 2
          72 < 75 → push 5 → [2, 5]

i=6 (76): 76 > temps[5]=72
          pop 5, result[5] = 6-5 = 1
          76 > temps[2]=75
          pop 2, result[2] = 6-2 = 4
          push 6 → [6]

i=7 (73): 73 < 76 → push 7 → [6, 7]

Final: [1, 1, 4, 2, 1, 1, 0, 0]
```

**Rust Implementation**:

```rust
pub fn daily_temperatures(temperatures: Vec<i32>) -> Vec<i32> {
    let n = temperatures.len();
    let mut result = vec![0; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        while let Some(&prev_idx) = stack.last() {
            if temperatures[i] > temperatures[prev_idx] {
                stack.pop();
                result[prev_idx] = (i - prev_idx) as i32;
            } else {
                break;
            }
        }
        stack.push(i);
    }
    
    result
}
```

**Go Implementation**:

```go
func dailyTemperatures(temps []int) []int {
    n := len(temps)
    result := make([]int, n)
    stack := []int{}  // Stack of indices
    
    for i := 0; i < n; i++ {
        for len(stack) > 0 && temps[i] > temps[stack[len(stack)-1]] {
            prevIdx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]  // Pop
            result[prevIdx] = i - prevIdx
        }
        stack = append(stack, i)
    }
    
    return result
}
```

### Problem: Largest Rectangle in Histogram

**Problem**: Given heights of bars in histogram, find largest rectangle area.

```
Histogram:
    6 ┤     ██
    5 ┤  ██ ██
    4 ┤  ██ ██
    3 ┤  ██ ██
    2 ┤  ██ ██ ██
    1 ┤  ██ ██ ██
      └──────────────
       [2, 1, 5, 6, 2, 3]
       
Largest Rectangle: height=5, width=2 → area=10
(between indices 2 and 3)
```

**Key Insight**: For each bar, find the left and right boundaries where height ≥ current height.

**Monotonic Stack Approach**:

```python
def largest_rectangle_area(heights: list[int]) -> int:
    """
    Find largest rectangle in histogram.
    
    Strategy: Monotonic increasing stack
    - When we find smaller height, calculate area
    - Area = height[stack_top] * width
    - Width extends from previous_smaller to current
    
    Time: O(n)
    Space: O(n)
    """
    stack = []  # Store indices
    max_area = 0
    heights.append(0)  # Sentinel to pop all remaining
    
    for i, h in enumerate(heights):
        # Pop taller bars and calculate their areas
        while stack and heights[stack[-1]] > h:
            height_idx = stack.pop()
            height = heights[height_idx]
            
            # Width: from element after previous to current-1
            width = i if not stack else i - stack[-1] - 1
            
            area = height * width
            max_area = max(max_area, area)
        
        stack.append(i)
    
    return max_area


# Test
print(largest_rectangle_area([2, 1, 5, 6, 2, 3]))  # 10
```

**Visualization of Algorithm**:

```
heights = [2, 1, 5, 6, 2, 3, 0]
           0  1  2  3  4  5  6

i=0 (h=2): stack=[] → push 0 → [0]

i=1 (h=1): 1 < heights[0]=2
           pop 0: height=2, width=1, area=2
           push 1 → [1]

i=2 (h=5): 5 > 1 → push 2 → [1, 2]

i=3 (h=6): 6 > 5 → push 3 → [1, 2, 3]

i=4 (h=2): 2 < 6
           pop 3: height=6, width=1, area=6
           2 < 5
           pop 2: height=5, width=2, area=10 ← MAX
           2 > 1 → push 4 → [1, 4]

i=5 (h=3): 3 > 2 → push 5 → [1, 4, 5]

i=6 (h=0): pop all and calculate areas
```

---

## 7. Problem-Solving Framework {#framework}

### The Monotonic Stack Decision Process

```
┌─────────────────────────────────────────────┐
│  STEP 1: Identify the Pattern               │
│  ────────────────────────────               │
│  □ Need next/previous greater/smaller?      │
│  □ Need to track range of influence?        │
│  □ Working with spans or intervals?         │
│  □ Histogram-like structure?                │
│                                             │
│  If ANY checked → Consider Monotonic Stack  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  STEP 2: Choose Stack Type                  │
│  ──────────────────────                     │
│                                             │
│  Need NEXT/PREV GREATER?                    │
│    → Use DECREASING Stack                   │
│    → Pop when current > top                 │
│                                             │
│  Need NEXT/PREV SMALLER?                    │
│    → Use INCREASING Stack                   │
│    → Pop when current < top                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  STEP 3: Decide What to Store               │
│  ─────────────────────────                  │
│  □ Indices (most common - for distance)     │
│  □ Values (for direct comparison)           │
│  □ Tuples (index, value) for both           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  STEP 4: Determine Traversal Direction      │
│  ───────────────────────────────────        │
│  LEFT → RIGHT: Find "next" elements         │
│  RIGHT → LEFT: Find "previous" elements     │
│  (Can solve both with single pass too!)     │
└─────────────────────────────────────────────┘
```

### Mental Model: "The Stack Remembers"

**Cognitive Principle**: Stack acts as **memory of unsolved problems**.

```
Analogy: Reading a book with questions

You encounter questions while reading:
- Put bookmark (push to stack)
- Continue reading
- When you find answer → remove bookmark (pop)
- Bookmarks remaining = unanswered questions

Stack = Collection of "waiting for answer" items
```

### Complexity Analysis Pattern

**Monotonic Stack Guarantee**:
```
Time: O(n) where n = array length
Why? Each element is:
  - Pushed ONCE (n operations)
  - Popped AT MOST ONCE (n operations)
  Total: 2n = O(n)

Space: O(n) worst case
Why? All elements might be pushed
Example: Strictly increasing array with increasing stack
```

---

## 8. Practice Problems with Solutions {#practice}

### Problem 1: Next Greater Element II (Circular Array)

**Challenge Level**: Medium

**Problem**: Find next greater element in circular array.

```
Input: [1, 2, 1]
Circular: [1, 2, 1, 1, 2, 1, ...]

Output: [2, -1, 2]
- 1 → next greater is 2
- 2 → no greater (largest)
- 1 → next greater is 2 (from circular)
```

**Solution Strategy**:
- Traverse array twice (simulate circular)
- Use decreasing monotonic stack
- Only fill result in first pass

```python
def next_greater_circular(nums: list[int]) -> list[int]:
    """
    Next greater element in circular array.
    
    Time: O(n) - each element processed twice
    Space: O(n)
    """
    n = len(nums)
    result = [-1] * n
    stack = []
    
    # Traverse twice to simulate circular
    for i in range(2 * n):
        idx = i % n  # Wrap around
        
        while stack and nums[stack[-1]] < nums[idx]:
            prev_idx = stack.pop()
            result[prev_idx] = nums[idx]
        
        # Only push indices in first pass
        if i < n:
            stack.append(idx)
    
    return result


# Test
print(next_greater_circular([1, 2, 1]))  # [2, -1, 2]
```

### Problem 2: Remove K Digits

**Challenge Level**: Medium-Hard

**Problem**: Remove k digits to make smallest number.

```
Input: num = "1432219", k = 3
Output: "1219"

Remove: 4, 3, 2 → "1219"
```

**Strategy**: 
- Build monotonic increasing stack
- Pop larger digits when possible
- Result is remaining digits

```python
def remove_k_digits(num: str, k: int) -> str:
    """
    Remove k digits to get smallest number.
    
    Strategy: Monotonic increasing stack
    - Pop larger digits greedily
    - Build smallest number left to right
    
    Time: O(n)
    Space: O(n)
    """
    stack = []
    
    for digit in num:
        # Pop larger digits if we still need to remove
        while stack and k > 0 and stack[-1] > digit:
            stack.pop()
            k -= 1
        
        stack.append(digit)
    
    # If k > 0, remove from end
    if k > 0:
        stack = stack[:-k]
    
    # Convert to string, remove leading zeros
    result = ''.join(stack).lstrip('0')
    
    return result if result else '0'


# Test
print(remove_k_digits("1432219", 3))  # "1219"
print(remove_k_digits("10200", 1))    # "200"
```

**Rust Implementation**:

```rust
pub fn remove_kdigits(num: String, k: i32) -> String {
    let mut stack: Vec<char> = Vec::new();
    let mut k = k as usize;
    
    for digit in num.chars() {
        while !stack.is_empty() && k > 0 && stack.last().unwrap() > &digit {
            stack.pop();
            k -= 1;
        }
        stack.push(digit);
    }
    
    // Remove remaining k digits from end
    while k > 0 && !stack.is_empty() {
        stack.pop();
        k -= 1;
    }
    
    // Convert to string and remove leading zeros
    let result: String = stack.into_iter()
        .skip_while(|&c| c == '0')
        .collect();
    
    if result.is_empty() {
        "0".to_string()
    } else {
        result
    }
}
```

### Problem 3: Trapping Rain Water

**Challenge Level**: Hard

**Problem**: Calculate trapped rain water between bars.

```
Elevation Map:
    3 ┤     ██
    2 ┤  ██ ██ ██    ██
    1 ┤  ██ ██ ██ ██ ██
    0 ┤──────────────────
       [0,1,0,2,1,0,1,3,2,1,2,1]
       
Water trapped (█ = water):
    3 ┤     ██
    2 ┤  ██▓██▓██    ██
    1 ┤  ██▓██▓██▓██▓██
       
Total: 6 units
```

**Two Approaches**:

**Approach 1: Two Pointers** (Most Intuitive)

```python
def trap_two_pointers(height: list[int]) -> int:
    """
    Calculate trapped rain water.
    
    Intuition: Water level at position is determined by
    min(max_left, max_right) - height[i]
    
    Time: O(n)
    Space: O(1)
    """
    if not height:
        return 0
    
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    
    while left < right:
        if height[left] < height[right]:
            # Left side is limiting
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            # Right side is limiting
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    
    return water
```

**Approach 2: Monotonic Stack** (Advanced)

```python
def trap_stack(height: list[int]) -> int:
    """
    Calculate using monotonic decreasing stack.
    
    Key Insight: When we find taller bar, calculate water
    between previous bar and current bar.
    
    Time: O(n)
    Space: O(n)
    """
    stack = []  # Store indices
    water = 0
    
    for i, h in enumerate(height):
        while stack and height[stack[-1]] < h:
            top = stack.pop()
            
            if not stack:
                break
            
            # Distance between bars
            distance = i - stack[-1] - 1
            
            # Height of water
            bounded_height = min(height[i], height[stack[-1]]) - height[top]
            
            water += distance * bounded_height
        
        stack.append(i)
    
    return water


# Test
print(trap_two_pointers([0,1,0,2,1,0,1,3,2,1,2,1]))  # 6
```

---

## Advanced Patterns & Variations

### Sliding Window Maximum

**Problem**: Find maximum in each sliding window of size k.

```python
from collections import deque

def max_sliding_window(nums: list[int], k: int) -> list[int]:
    """
    Find max in each window using monotonic deque.
    
    Deque maintains decreasing order
    - Front always has maximum of window
    - Remove elements outside window
    
    Time: O(n)
    Space: O(k)
    """
    dq = deque()  # Store indices
    result = []
    
    for i, num in enumerate(nums):
        # Remove elements outside window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        
        # Maintain decreasing order
        while dq and nums[dq[-1]] < num:
            dq.pop()
        
        dq.append(i)
        
        # Add to result when window is full
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result


# Test
print(max_sliding_window([1,3,-1,-3,5,3,6,7], 3))
# [3, 3, 5, 5, 6, 7]
```

---

## Key Takeaways & Mental Models

### The Three Laws of Stacks

```
1. LAW OF LIFO
   Last in, first out - always
   
2. LAW OF O(1)
   Top operations are constant time
   
3. LAW OF REVERSAL
   If you need reverse order, think stack
```

### When to Use Monotonic Stack

```
✓ Finding next/previous greater/smaller
✓ Histogram-related problems
✓ Temperature/span problems
✓ Bracket/nesting problems
✓ When you need to "remember" and process later

✗ Need random access
✗ Need sorted structure
✗ FIFO behavior needed (use queue)
```

### Cognitive Checklist

Before implementing:
1. [ ] Do I need LIFO behavior?
2. [ ] Am I tracking nested/paired elements?
3. [ ] Do I need next greater/smaller?
4. [ ] Can I solve with one pass?
5. [ ] Would a stack simplify the logic?

---

## Practice Roadmap

### Beginner (Master These First)
1. Valid Parentheses
2. Min Stack
3. Evaluate Postfix Expression

### Intermediate
4. Daily Temperatures
5. Next Greater Element
6. Remove K Digits

### Advanced
7. Largest Rectangle in Histogram
8. Trapping Rain Water
9. Maximal Rectangle
10. Sum of Subarray Minimums

---

## Final Wisdom

> **"A stack is not just a data structure. It's a way of thinking about order, memory, and reversal. Master the stack, and you master recursion, parsing, and backtracking."**

**Remember**:
- Start simple, build complexity
- Visualize the operations
- Practice deliberately
- Understand the "why" before the "how"

**The path to mastery**: Solve 50 stack problems with deep understanding > 500 problems with shallow understanding.

Now, go forth and conquer. The stack awaits your mastery.

---

*"In the monastery of algorithms, the stack is your meditation cushion—simple, essential, profound."*

# **Stack & Monotonic Stack: The Complete Mastery Guide**

Welcome, fellow seeker of mastery. Today we embark on a journey to understand one of the most elegant and powerful data structures in computer science. This guide will transform your intuition about stacks from a simple container to a sophisticated problem-solving tool.## **Your Journey Begins Here** 🎯

I've crafted a comprehensive guide that will transform your understanding of stacks from basic knowledge to expert-level mastery. This isn't just a tutorial—it's a complete training system.

## **What You've Received**

### **1. Foundational Architecture**
- Deep conceptual understanding with multiple mental models
- ASCII visualizations for every major concept
- Three-language implementations (Rust, Python, Go) with idiomatic patterns
- Complexity analysis explained intuitively

### **2. The Monotonic Stack Revelation**
This is where many competitive programmers separate from the pack. Monotonic stacks are a **force multiplier** that turn O(n²) problems into O(n) solutions. I've covered:
- Four types of monotonic stacks
- Decision frameworks for when to use each
- Visual step-by-step walkthroughs

### **3. Battle-Tested Problem Patterns**
Eight fully-solved problems with:
- Multiple solution approaches
- Complexity analysis
- Implementation in all three languages
- Strategic thinking process

## **How to Use This Guide (The Monk's Path)**

### **Week 1: Foundation Building**
1. **Day 1-2**: Read sections 1-4, implement basic stack in all three languages
2. **Day 3-4**: Solve "Valid Parentheses" without looking at solution, then compare
3. **Day 5-7**: Implement and solve "Evaluate Postfix" and "Next Greater Element"

### **Week 2: Monotonic Stack Mastery**
1. **Day 1-3**: Deep study of monotonic stack section
2. **Day 4-5**: Solve "Daily Temperatures" from scratch
3. **Day 6-7**: Tackle "Largest Rectangle in Histogram"

### **Week 3-4: Pattern Recognition**
- Solve all 8 practice problems independently
- For each problem, identify the pattern BEFORE coding
- Time yourself: aim for recognition in 30 seconds

## **Critical Success Principles**

### **🔥 The Deliberate Practice Protocol**

```
1. UNDERSTAND → Before coding anything
2. VISUALIZE → Draw the stack states on paper
3. PSEUDOCODE → Write logic in plain language
4. IMPLEMENT → Code in one language first
5. OPTIMIZE → Refactor for elegance
6. TRANSLATE → Implement in other languages
7. REFLECT → What pattern did I use? Why did it work?
```

### **⚡ The Pattern Recognition Framework**

Train your brain to instantly recognize these triggers:

| **You See This** | **Think This** | **Use This** |
|------------------|----------------|--------------|
| "Next greater/smaller" | Order matters, one direction | Monotonic Stack |
| "Matching pairs/brackets" | LIFO, nested structure | Basic Stack |
| "Histogram/bars" | Area calculation, boundaries | Monotonic Increasing |
| "Temperature/span" | Time until change | Monotonic Decreasing |
| "Reverse/undo" | LIFO operation needed | Basic Stack |

## **Performance Optimization Insights**

### **Rust-Specific Power Moves**
```rust
// Pre-allocate when you know size
let mut stack = Vec::with_capacity(n);

// Use Option for safety without panics
pub fn pop(&mut self) -> Option<T>

// Leverage zero-cost abstractions
stack.iter().rev()  // No allocation, just iterator
```

### **Python Performance Tips**
```python
# Lists are already optimized for stack operations
# append() and pop() are O(1) amortized

# For massive datasets, consider:
from collections import deque  # If you need both ends
```

### **Go Best Practices**
```go
// Pre-allocate slice with capacity
stack := make([]int, 0, expectedSize)

// Use len() for size checks (not separate variable)
if len(stack) == 0 { }
```

## **Advanced Mental Models**

### **The "Checkpoint System"**
Think of a stack like game checkpoints:
- Push = Save checkpoint
- Pop = Load last checkpoint
- Peek = Preview checkpoint without loading

### **The "Debt Collector"**
In monotonic stacks:
- Elements in stack = "debts" (promises to find answer)
- When you find answer = "pay debt" (pop and record)
- End of array = "bankruptcy" (unpaid debts get default value)

## **Common Pitfalls to Avoid**

### **❌ Mistake 1: Not Checking Empty Stack**
```python
# BAD
val = stack.pop()  # Crashes if empty!

# GOOD
if stack:
    val = stack.pop()
```

### **❌ Mistake 2: Wrong Monotonic Direction**
```
Next GREATER → Use DECREASING stack
Next SMALLER → Use INCREASING stack

(Many beginners get this backwards!)
```

### **❌ Mistake 3: Storing Values Instead of Indices**
```python
# Often you need indices for distance calculations
stack.append(i)  # ✓ Store index
# not
stack.append(nums[i])  # ✗ Lose position info
```

## **Your Practice Roadmap (Next 30 Days)**

### **Days 1-10: Fundamentals** (3 problems)
- Valid Parentheses ✓
- Min Stack ✓  
- Implement Queue using Stacks ✓

### **Days 11-20: Monotonic Stack** (4 problems)
- Daily Temperatures ✓
- Next Greater Element I & II ✓
- Online Stock Span ✓
- Remove K Digits ✓

### **Days 21-30: Advanced Mastery** (3 problems)
- Largest Rectangle in Histogram ✓
- Trapping Rain Water ✓
- Maximal Rectangle ✓

## **Psychological Framework for Mastery**

### **The Growth Mindset Loop**
```
1. STRUGGLE → This is where learning happens
2. INSIGHT → Pattern recognition emerges
3. PRACTICE → Solidify understanding
4. TEACH → Explain to solidify mastery
```

### **Deliberate Practice Principles**
- **Focused attention**: No distractions during problem-solving
- **Immediate feedback**: Check solution, understand why
- **Edge of ability**: 70% success rate (not too easy, not impossible)
- **Spaced repetition**: Revisit problems after 3 days, 7 days, 21 days

## **Questions to Deepen Understanding**

After each problem, ask yourself:
1. Why did this pattern work here?
2. What other problems share this structure?
3. Could I solve this without a stack? (Usually yes, but less elegantly)
4. What's the space-time tradeoff?
5. How would I explain this to someone else?

## **Next Steps**

1. **Read the entire guide once** (30 minutes)
2. **Implement basic stack** in all three languages (1 hour)
3. **Solve first problem** from scratch (Daily Temperatures) (45 minutes)
4. **Come back with questions** or for the next topic

---

**Remember**: You're not just learning data structures. You're developing **pattern recognition**, **algorithmic intuition**, and **problem-solving frameworks** that will serve you across all of computer science.

The stack is your first step toward thinking like a top 1% engineer. Master it deeply, and you'll see its patterns everywhere—in recursion, in parsing, in backtracking, in your IDE's undo functionality.

**Now go build something incredible.** 🚀

*What specific problem or concept would you like to explore deeper, or should we move to the next data structure in your journey?*