# Complete Stack Mastery Guide - Patterns & Problem-Solving

## Table of Contents
1. [Foundational Understanding](#foundational-understanding)
2. [Mental Model & Intuition](#mental-model--intuition)
3. [Core Operations & Complexity](#core-operations--complexity)
4. [Implementation in Rust, Python, Go](#implementation-in-rust-python-go)
5. [The 15 Essential Stack Patterns](#the-15-essential-stack-patterns)
6. [Problem Recognition Framework](#problem-recognition-framework)
7. [Advanced Techniques](#advanced-techniques)
8. [Cognitive Strategies for Mastery](#cognitive-strategies-for-mastery)

---

## Foundational Understanding

### What is a Stack?

A **stack** is a linear data structure that follows the **LIFO (Last-In-First-Out)** principle. Think of it as a stack of plates: you can only add or remove plates from the top.

**Key Terminology:**
- **LIFO**: Last-In-First-Out - the most recently added element is the first to be removed
- **Top**: The most recent element in the stack (accessible end)
- **Bottom**: The first element added (inaccessible without removing all elements above it)
- **Push**: Add an element to the top
- **Pop**: Remove and return the top element
- **Peek/Top**: View the top element without removing it

### Visual Representation

```
Push 5 → Push 3 → Push 8 → Pop → Pop

Initial:   After Push 5:   After Push 3:   After Push 8:   After Pop:    After Pop:
  []           [5]             [3]             [8]            [3]            [5]
                [5]             [5]             [3]            [5]
                                                [5]
  
  ↑ top        ↑ top           ↑ top           ↑ top          ↑ top          ↑ top
```

---

## Mental Model & Intuition

### The Deep Insight

**Core Principle**: Stacks preserve *temporal ordering* with *constant-time access* to the most recent element.

**When to think "Stack":**
1. When you need to **remember where you came from** (backtracking, undo operations)
2. When **most recent** matters more than **oldest** (function calls, nested structures)
3. When solving problems with **matching pairs** or **nesting** (parentheses, HTML tags)
4. When you need to **delay processing** until you have complete context
5. When **reversing** order or **postponing decisions**

### Cognitive Chunking Strategy

Think of stack problems in these mental chunks:
- **Temporal relationships**: "What happened last?"
- **Deferred decisions**: "I'll decide this later when I have more info"
- **Nearest greater/smaller**: "What was the last thing bigger/smaller than this?"
- **Matching/Pairing**: "Find the corresponding opening/closing element"

---

## Core Operations & Complexity

### Time Complexity (Amortized)

| Operation | Time | Space | Description |
|-----------|------|-------|-------------|
| Push | O(1) | O(1) | Add element to top |
| Pop | O(1) | O(1) | Remove and return top |
| Peek/Top | O(1) | O(1) | View top without removing |
| IsEmpty | O(1) | O(1) | Check if stack is empty |
| Size | O(1) | O(1) | Get number of elements |

**Critical Note**: Array-based stacks may occasionally require O(n) time for resizing, but this is amortized to O(1) over many operations.

---

## Implementation in Rust, Python, Go

### Python Implementation

```python
class Stack:
    """
    Dynamic array-based stack implementation.
    Uses Python list which provides amortized O(1) append/pop.
    """
    
    def __init__(self):
        self._items = []
    
    def push(self, item):
        """Add item to top of stack. O(1) amortized."""
        self._items.append(item)
    
    def pop(self):
        """Remove and return top item. O(1). Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    
    def peek(self):
        """Return top item without removing. O(1)."""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]
    
    def is_empty(self):
        """Check if stack is empty. O(1)."""
        return len(self._items) == 0
    
    def size(self):
        """Return number of items. O(1)."""
        return len(self._items)
    
    def __len__(self):
        return len(self._items)
    
    def __bool__(self):
        return not self.is_empty()

# Pythonic usage: List as stack
stack = []
stack.append(5)      # push
top = stack.pop()    # pop
peek = stack[-1]     # peek (check not empty first!)
```

### Rust Implementation

```rust
/// Generic stack implementation using Vec
pub struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    /// Create a new empty stack with default capacity
    pub fn new() -> Self {
        Stack {
            items: Vec::new(),
        }
    }
    
    /// Create stack with specified capacity to avoid reallocations
    pub fn with_capacity(capacity: usize) -> Self {
        Stack {
            items: Vec::with_capacity(capacity),
        }
    }
    
    /// Push item onto stack. O(1) amortized.
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    /// Pop item from stack. Returns None if empty. O(1).
    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    /// Peek at top item without removing. Returns None if empty. O(1).
    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    /// Mutable reference to top item
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.items.last_mut()
    }
    
    /// Check if stack is empty. O(1).
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    /// Get number of items. O(1).
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Idiomatic Rust: Use Vec directly
let mut stack: Vec<i32> = Vec::new();
stack.push(5);
let top = stack.pop();  // Returns Option<i32>
let peek = stack.last(); // Returns Option<&i32>
```

### Go Implementation

```go
package main

// Stack generic implementation using slice
type Stack[T any] struct {
    items []T
}

// NewStack creates a new empty stack
func NewStack[T any]() *Stack[T] {
    return &Stack[T]{
        items: make([]T, 0),
    }
}

// NewStackWithCapacity creates stack with initial capacity
func NewStackWithCapacity[T any](capacity int) *Stack[T] {
    return &Stack[T]{
        items: make([]T, 0, capacity),
    }
}

// Push adds item to top of stack. O(1) amortized.
func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

// Pop removes and returns top item. Returns zero value and false if empty. O(1).
func (s *Stack[T]) Pop() (T, bool) {
    if s.IsEmpty() {
        var zero T
        return zero, false
    }
    index := len(s.items) - 1
    item := s.items[index]
    s.items = s.items[:index]
    return item, true
}

// Peek returns top item without removing. Returns zero value and false if empty. O(1).
func (s *Stack[T]) Peek() (T, bool) {
    if s.IsEmpty() {
        var zero T
        return zero, false
    }
    return s.items[len(s.items)-1], true
}

// IsEmpty checks if stack is empty. O(1).
func (s *Stack[T]) IsEmpty() bool {
    return len(s.items) == 0
}

// Size returns number of items. O(1).
func (s *Stack[T]) Size() int {
    return len(s.items)
}

// Idiomatic Go: Use slice directly
stack := []int{}
stack = append(stack, 5)  // push
top := stack[len(stack)-1]  // peek (check length first!)
stack = stack[:len(stack)-1]  // pop
```

---

## The 15 Essential Stack Patterns

### Pattern 1: Basic Stack Operations (Reversal)

**Concept**: Use LIFO property to reverse order.

**When to use**: Reverse strings, reverse portions of arrays, undo operations.

**Mental Model**: "What went in last comes out first = reversal"

```python
def reverse_string(s: str) -> str:
    """
    Time: O(n), Space: O(n)
    Every character goes in and out once.
    """
    stack = []
    for char in s:
        stack.append(char)
    
    result = []
    while stack:
        result.append(stack.pop())
    
    return ''.join(result)
```

**Expert Insight**: This is the foundation. Master the mechanical flow: push all, pop all.

---

### Pattern 2: Balanced Parentheses / Matching Pairs

**Concept**: Use stack to track opening symbols and match with closing symbols.

**When to use**: Validate parentheses, brackets, HTML tags, expression parsing.

**Mental Model**: "Opening symbol = promise to close later. Stack = list of promises."

**Recognition Keywords**: "valid", "balanced", "matching", "properly nested"

```python
def is_valid_parentheses(s: str) -> bool:
    """
    Time: O(n), Space: O(n)
    
    Logic Flow:
    1. Opening bracket → push to stack (remember it)
    2. Closing bracket → must match top of stack (fulfill promise)
    3. End with empty stack (all promises fulfilled)
    """
    stack = []
    pairs = {'(': ')', '{': '}', '[': ']'}
    
    for char in s:
        if char in pairs:  # Opening bracket
            stack.append(char)
        else:  # Closing bracket
            if not stack or pairs[stack.pop()] != char:
                return False
    
    return len(stack) == 0  # All opened brackets must be closed

# Examples:
# "({[]})" → True
# "({[}])" → False (wrong order)
# "(((" → False (not closed)
```

**Rust Version (Idiomatic)**:

```rust
fn is_valid_parentheses(s: &str) -> bool {
    let mut stack = Vec::new();
    let pairs = [('(', ')'), ('{', '}'), ('[', ']')];
    
    for ch in s.chars() {
        match ch {
            '(' | '{' | '[' => stack.push(ch),
            ')' | '}' | ']' => {
                match stack.pop() {
                    Some('(') if ch == ')' => continue,
                    Some('{') if ch == '}' => continue,
                    Some('[') if ch == ']' => continue,
                    _ => return false,
                }
            }
            _ => {} // Ignore other characters
        }
    }
    
    stack.is_empty()
}
```

**Go Version**:

```go
func isValidParentheses(s string) bool {
    stack := []rune{}
    pairs := map[rune]rune{'(': ')', '{': '}', '[': ']'}
    
    for _, char := range s {
        if _, isOpening := pairs[char]; isOpening {
            stack = append(stack, char)
        } else {
            if len(stack) == 0 {
                return false
            }
            if pairs[stack[len(stack)-1]] != char {
                return false
            }
            stack = stack[:len(stack)-1]
        }
    }
    
    return len(stack) == 0
}
```

**Edge Cases to Master**:
- Empty string: `""` → True
- Only opening: `"((("` → False
- Only closing: `")))"` → False
- Wrong order: `"([)]"` → False
- Mixed characters: `"a(b)c"` → True (ignore non-bracket chars)

---

### Pattern 3: Monotonic Stack (Next Greater/Smaller Element)

**Concept**: Maintain stack in sorted order (increasing or decreasing) to find next greater/smaller elements efficiently.

**When to use**: Finding next/previous greater/smaller element, temperature problems, histogram problems.

**Mental Model**: "Stack stores candidates. Current element eliminates impossible candidates."

**Recognition Keywords**: "next greater", "next smaller", "previous greater", "can see", "visible"

**Deep Understanding**:
- **Monotonic Increasing Stack**: Elements increase from bottom to top → finds next smaller
- **Monotonic Decreasing Stack**: Elements decrease from bottom to top → finds next greater

**Why it works**: When you encounter a larger element, all smaller elements in the stack have found their "next greater". They can never be the answer for future elements.

```python
def next_greater_elements(nums: list[int]) -> list[int]:
    """
    For each element, find the next element to the right that is greater.
    Time: O(n), Space: O(n)
    
    Key Insight: Each element is pushed and popped at most once.
    
    Example: [2, 1, 2, 4, 3]
    Result:  [4, 2, 4, -1, -1]
    
    Visualization:
    Index 0 (2): Next greater is 4 (at index 3)
    Index 1 (1): Next greater is 2 (at index 2)
    Index 2 (2): Next greater is 4 (at index 3)
    Index 3 (4): No greater element → -1
    Index 4 (3): No greater element → -1
    """
    n = len(nums)
    result = [-1] * n
    stack = []  # Stores indices (not values!)
    
    for i in range(n):
        # While current element is greater than stack top
        # Stack top has found its next greater element
        while stack and nums[i] > nums[stack[-1]]:
            index = stack.pop()
            result[index] = nums[i]
        
        stack.append(i)
    
    return result

# Step-by-step trace for [2, 1, 2, 4, 3]:
# i=0, num=2: stack=[] → push 0 → stack=[0]
# i=1, num=1: 1 ≤ 2 → push 1 → stack=[0,1]
# i=2, num=2: 2 > 1 → pop 1, result[1]=2 → push 2 → stack=[0,2]
# i=3, num=4: 4 > 2 → pop 2, result[2]=4 → 4 > 2 → pop 0, result[0]=4 → push 3 → stack=[3]
# i=4, num=3: 3 ≤ 4 → push 4 → stack=[3,4]
# Remaining indices in stack have no next greater → result = [4,2,4,-1,-1]
```

**Rust Version (Zero-cost abstractions)**:

```rust
fn next_greater_elements(nums: Vec<i32>) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::with_capacity(n);
    
    for i in 0..n {
        while let Some(&top_idx) = stack.last() {
            if nums[i] > nums[top_idx] {
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
```

**Go Version**:

```go
func nextGreaterElements(nums []int) []int {
    n := len(nums)
    result := make([]int, n)
    for i := range result {
        result[i] = -1
    }
    
    stack := []int{} // Store indices
    
    for i := 0; i < n; i++ {
        for len(stack) > 0 && nums[i] > nums[stack[len(stack)-1]] {
            index := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[index] = nums[i]
        }
        stack = append(stack, i)
    }
    
    return result
}
```

**Variations**:

```python
# Next SMALLER element (monotonic increasing stack)
def next_smaller_elements(nums: list[int]) -> list[int]:
    n = len(nums)
    result = [-1] * n
    stack = []
    
    for i in range(n):
        while stack and nums[i] < nums[stack[-1]]:  # Changed comparison
            index = stack.pop()
            result[index] = nums[i]
        stack.append(i)
    
    return result

# PREVIOUS greater element (iterate backwards)
def previous_greater_elements(nums: list[int]) -> list[int]:
    n = len(nums)
    result = [-1] * n
    stack = []
    
    for i in range(n - 1, -1, -1):  # Right to left
        while stack and nums[i] > nums[stack[-1]]:
            index = stack.pop()
            result[index] = nums[i]
        stack.append(i)
    
    return result
```

**Common Applications**:
- Daily temperatures (how many days until warmer)
- Stock span problem
- Largest rectangle in histogram
- Trapping rain water

---

### Pattern 4: Expression Evaluation

**Concept**: Use stack to evaluate postfix (Reverse Polish Notation) or convert between notations.

**When to use**: Calculator problems, expression parsing, operator precedence.

**Mental Model**: "Stack holds operands. Operator consumes operands and produces result."

**Key Terms**:
- **Infix**: `3 + 4` (operator between operands)
- **Postfix (RPN)**: `3 4 +` (operator after operands)
- **Prefix**: `+ 3 4` (operator before operands)

```python
def eval_rpn(tokens: list[str]) -> int:
    """
    Evaluate Reverse Polish Notation expression.
    Time: O(n), Space: O(n)
    
    Example: ["2", "1", "+", "3", "*"] → ((2 + 1) * 3) → 9
    
    Logic:
    - Number → push to stack
    - Operator → pop two operands, apply operator, push result
    """
    stack = []
    operators = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: int(a / b),  # Truncate toward zero
    }
    
    for token in tokens:
        if token in operators:
            # IMPORTANT: Order matters! Second pop is left operand
            right = stack.pop()
            left = stack.pop()
            result = operators[token](left, right)
            stack.append(result)
        else:
            stack.append(int(token))
    
    return stack[0]

# Step-by-step: ["2", "1", "+", "3", "*"]
# "2" → stack=[2]
# "1" → stack=[2, 1]
# "+" → pop 1, pop 2 → 2+1=3 → stack=[3]
# "3" → stack=[3, 3]
# "*" → pop 3, pop 3 → 3*3=9 → stack=[9]
```

**Advanced: Infix to Postfix Conversion**:

```python
def infix_to_postfix(expression: str) -> str:
    """
    Convert infix notation to postfix (Shunting Yard Algorithm).
    Time: O(n), Space: O(n)
    
    Precedence: * / > + -
    """
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    output = []
    operator_stack = []
    
    for char in expression:
        if char.isdigit():
            output.append(char)
        elif char in precedence:
            # Pop operators with higher or equal precedence
            while (operator_stack and 
                   operator_stack[-1] != '(' and
                   precedence.get(operator_stack[-1], 0) >= precedence[char]):
                output.append(operator_stack.pop())
            operator_stack.append(char)
        elif char == '(':
            operator_stack.append(char)
        elif char == ')':
            # Pop until matching '('
            while operator_stack and operator_stack[-1] != '(':
                output.append(operator_stack.pop())
            operator_stack.pop()  # Remove '('
    
    # Pop remaining operators
    while operator_stack:
        output.append(operator_stack.pop())
    
    return ''.join(output)

# "3+4*2" → "342*+"
# "3+4*2/(1-5)" → "342*15-/+"
```

---

### Pattern 5: String Decoding / Nested Structures

**Concept**: Use stack to handle nested encoding or recursive structures.

**When to use**: Decode strings with nested patterns, parse JSON-like structures.

**Mental Model**: "Each opening bracket creates a new context. Stack manages context switches."

```python
def decode_string(s: str) -> str:
    """
    Decode string with nested patterns like "3[a2[c]]" → "accaccacc"
    Time: O(n * maxK) where maxK is max repetition number
    Space: O(n)
    
    Strategy:
    - Stack stores (current_string, repetition_count)
    - When '[': push current context, start new
    - When ']': pop context, repeat current, append to previous
    """
    stack = []
    current_string = ""
    current_num = 0
    
    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            # Save current context
            stack.append((current_string, current_num))
            current_string = ""
            current_num = 0
        elif char == ']':
            # Restore and apply
            prev_string, num = stack.pop()
            current_string = prev_string + current_string * num
        else:
            current_string += char
    
    return current_string

# Trace "3[a2[c]]":
# '3' → num=3
# '[' → push ("", 3), reset → stack=[("", 3)]
# 'a' → str="a"
# '2' → num=2
# '[' → push ("a", 2), reset → stack=[("", 3), ("a", 2)]
# 'c' → str="c"
# ']' → pop ("a", 2) → str="a" + "c"*2 = "acc"
# ']' → pop ("", 3) → str="" + "acc"*3 = "accaccacc"
```

**Rust Version**:

```rust
fn decode_string(s: String) -> String {
    let mut stack: Vec<(String, usize)> = Vec::new();
    let mut current_string = String::new();
    let mut current_num = 0;
    
    for ch in s.chars() {
        match ch {
            '0'..='9' => {
                current_num = current_num * 10 + ch.to_digit(10).unwrap() as usize;
            }
            '[' => {
                stack.push((current_string.clone(), current_num));
                current_string.clear();
                current_num = 0;
            }
            ']' => {
                if let Some((prev_string, num)) = stack.pop() {
                    current_string = prev_string + &current_string.repeat(num);
                }
            }
            _ => {
                current_string.push(ch);
            }
        }
    }
    
    current_string
}
```

---

### Pattern 6: Backtracking with Stack (DFS)

**Concept**: Use stack to implement iterative depth-first search as alternative to recursion.

**When to use**: Tree/graph traversal, path finding, state space exploration.

**Mental Model**: "Stack = call stack. Push = recurse. Pop = return."

```python
def dfs_iterative(root):
    """
    Iterative DFS using explicit stack (replaces recursion).
    Time: O(V + E), Space: O(V)
    
    Key Insight: Stack simulates call stack of recursive DFS.
    """
    if not root:
        return
    
    stack = [root]
    visited = set()
    
    while stack:
        node = stack.pop()
        
        if node in visited:
            continue
        
        visited.add(node)
        process(node)  # Your logic here
        
        # Push children (right to left for left-to-right processing)
        for child in reversed(node.children):
            if child not in visited:
                stack.append(child)

# Binary tree inorder traversal (iterative)
def inorder_traversal(root):
    """
    Left → Root → Right using stack.
    Time: O(n), Space: O(h) where h is height
    """
    stack = []
    current = root
    result = []
    
    while current or stack:
        # Go to leftmost node
        while current:
            stack.append(current)
            current = current.left
        
        # Process node
        current = stack.pop()
        result.append(current.val)
        
        # Move to right subtree
        current = current.right
    
    return result
```

**Pattern Recognition**: If you can solve with recursion, you can solve with stack.

---

### Pattern 7: Histogram Problems (Largest Rectangle)

**Concept**: Use monotonic stack to find boundaries efficiently.

**When to use**: Largest rectangle in histogram, maximal rectangle in binary matrix.

**Mental Model**: "Stack maintains potential rectangle heights. Current bar determines right boundary."

```python
def largest_rectangle_histogram(heights: list[int]) -> int:
    """
    Find largest rectangle in histogram.
    Time: O(n), Space: O(n)
    
    Key Insight: For each bar, find left and right boundaries where
    all bars in between are >= current bar height.
    
    Monotonic increasing stack helps find these boundaries in O(n).
    """
    stack = []  # Stores indices of bars
    max_area = 0
    heights = heights + [0]  # Sentinel to flush stack
    
    for i, h in enumerate(heights):
        # When current height < stack top, calculate areas
        while stack and heights[stack[-1]] > h:
            height_index = stack.pop()
            height = heights[height_index]
            
            # Width: from left boundary to right boundary
            # Left boundary: previous element in stack (or start)
            # Right boundary: current index
            width = i if not stack else i - stack[-1] - 1
            
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    return max_area

# Example: [2, 1, 5, 6, 2, 3]
# Largest rectangle: height=5, width=2 (indices 2-3) → area=10
```

**Visualization for [2, 1, 5, 6, 2, 3]**:

```
    6
  5 6
  5 6   3
2 5 6 2 3
2 1 5 6 2 3
```

Max rectangle: Height 5, width 2 (bars at indices 2-3) = area 10

---

### Pattern 8: Trapping Rain Water

**Concept**: Calculate water trapped between bars using precomputed max heights or stack.

**When to use**: Water trapping, container problems.

```python
def trap_rain_water_stack(height: list[int]) -> int:
    """
    Calculate trapped water using stack (single pass).
    Time: O(n), Space: O(n)
    
    Mental Model: Stack stores bars that form left boundary.
    When taller bar found, calculate water for valleys.
    """
    stack = []
    water = 0
    
    for i, h in enumerate(height):
        # Find valleys and calculate water
        while stack and h > height[stack[-1]]:
            bottom = stack.pop()
            
            if not stack:
                break
            
            # Water level determined by min of boundaries
            left_bound = stack[-1]
            water_height = min(height[left_bound], h) - height[bottom]
            water_width = i - left_bound - 1
            water += water_height * water_width
        
        stack.append(i)
    
    return water

# Two-pointer solution (more efficient)
def trap_two_pointer(height: list[int]) -> int:
    """
    Time: O(n), Space: O(1)
    
    Insight: Water at position depends on min(max_left, max_right).
    Move pointer with smaller max to find potential water.
    """
    if not height:
        return 0
    
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0
    
    while left < right:
        if left_max < right_max:
            left += 1
            left_max = max(left_max, height[left])
            water += left_max - height[left]
        else:
            right -= 1
            right_max = max(right_max, height[right])
            water += right_max - height[right]
    
    return water
```

---

### Pattern 9: Min/Max Stack (Stack with Extra Operations)

**Concept**: Maintain minimum/maximum along with standard stack operations in O(1).

**When to use**: When you need constant-time min/max queries on stack elements.

```python
class MinStack:
    """
    Stack supporting getMin() in O(1).
    
    Strategy: Maintain parallel stack storing min at each level.
    """
    
    def __init__(self):
        self.stack = []
        self.min_stack = []
    
    def push(self, val: int):
        self.stack.append(val)
        min_val = val if not self.min_stack else min(val, self.min_stack[-1])
        self.min_stack.append(min_val)
    
    def pop(self):
        self.stack.pop()
        self.min_stack.pop()
    
    def top(self) -> int:
        return self.stack[-1]
    
    def get_min(self) -> int:
        return self.min_stack[-1]

# Space-optimized version (store differences)
class MinStackOptimized:
    """
    Store only when new minimum found.
    Time: O(1) all operations, Space: O(k) where k = # of mins
    """
    
    def __init__(self):
        self.stack = []
        self.min_val = float('inf')
    
    def push(self, val: int):
        if not self.stack:
            self.stack.append(0)
            self.min_val = val
        else:
            # Store difference from current min
            self.stack.append(val - self.min_val)
            if val < self.min_val:
                self.min_val = val
    
    def pop(self):
        if not self.stack:
            return
        
        diff = self.stack.pop()
        if diff < 0:  # This was a new minimum
            self.min_val = self.min_val - diff
    
    def top(self) -> int:
        diff = self.stack[-1]
        if diff < 0:
            return self.min_val
        return self.min_val + diff
    
    def get_min(self) -> int:
        return self.min_val
```

**Rust Generic MinStack**:

```rust
struct MinStack<T: Ord + Copy> {
    stack: Vec<T>,
    min_stack: Vec<T>,
}

impl<T: Ord + Copy> MinStack<T> {
    fn new() -> Self {
        MinStack {
            stack: Vec::new(),
            min_stack: Vec::new(),
        }
    }
    
    fn push(&mut self, val: T) {
        self.stack.push(val);
        let min_val = self.min_stack.last()
            .map(|&m| if val < m { val } else { m })
            .unwrap_or(val);
        self.min_stack.push(min_val);
    }
    
    fn pop(&mut self) -> Option<T> {
        self.min_stack.pop();
        self.stack.pop()
    }
    
    fn get_min(&self) -> Option<&T> {
        self.min_stack.last()
    }
}
```

---

### Pattern 10: Stack for State Management (Undo/Redo)

**Concept**: Two stacks to manage operation history and future states.

**When to use**: Text editors, drawing apps, game state management.

```python
class UndoRedoManager:
    """
    Manages undo/redo operations efficiently.
    Time: O(1) per operation, Space: O(k) for k operations
    """
    
    def __init__(self):
        self.undo_stack = []  # Past states
        self.redo_stack = []  # Future states (cleared on new action)
    
    def do_action(self, action):
        """Execute new action and save to undo stack."""
        self.undo_stack.append(action)
        self.redo_stack.clear()  # New action invalidates redo history
        return action.execute()
    
    def undo(self):
        """Undo last action."""
        if not self.undo_stack:
            return None
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        return action.undo()
    
    def redo(self):
        """Redo previously undone action."""
        if not self.redo_stack:
            return None
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        return action.execute()
```

---

### Pattern 11: Simplify Path (Stack for Path Resolution)

**Concept**: Use stack to process directory paths, handling `.` and `..`.

**When to use**: File system navigation, URL normalization.

```python
def simplify_path(path: str) -> str:
    """
    Simplify Unix-style file path.
    Time: O(n), Space: O(n)
    
    Rules:
    - '.' → current directory (ignore)
    - '..' → parent directory (pop stack)
    - Empty between slashes → ignore
    - Anything else → directory name (push)
    
    Example: "/a/./b/../../c/" → "/c"
    """
    stack = []
    
    for part in path.split('/'):
        if part == '..' and stack:
            stack.pop()
        elif part and part != '.' and part != '..':
            stack.append(part)
    
    return '/' + '/'.join(stack)

# Trace "/a/./b/../../c/":
# Split: ['', 'a', '.', 'b', '..', '..', 'c', '']
# '' → skip
# 'a' → stack=['a']
# '.' → skip
# 'b' → stack=['a', 'b']
# '..' → pop → stack=['a']
# '..' → pop → stack=[]
# 'c' → stack=['c']
# '' → skip
# Result: "/c"
```

---

### Pattern 12: Asteroid Collision

**Concept**: Simulate collisions using stack to track survivors.

**When to use**: Collision problems, elimination games.

```python
def asteroid_collision(asteroids: list[int]) -> list[int]:
    """
    Positive = moving right, Negative = moving left.
    When they meet, smaller explodes (equal = both explode).
    Time: O(n), Space: O(n)
    
    Logic:
    - Right-moving: always push (no collision with past)
    - Left-moving: might collide with right-moving asteroids in stack
    """
    stack = []
    
    for asteroid in asteroids:
        while stack and asteroid < 0 < stack[-1]:
            # Collision! asteroid moving left, stack top moving right
            if stack[-1] < -asteroid:
                stack.pop()  # Right-moving destroyed
                continue
            elif stack[-1] == -asteroid:
                stack.pop()  # Both destroyed
            break  # Left-moving destroyed or both destroyed
        else:
            # No collision or asteroid survived
            stack.append(asteroid)
    
    return stack

# Example: [5, 10, -5] → [5, 10]
# 5 → stack=[5]
# 10 → stack=[5, 10]
# -5 → collision with 10 → 10 wins → stack=[5, 10]

# Example: [10, 2, -5] → [10]
# 10 → stack=[10]
# 2 → stack=[10, 2]
# -5 → collision with 2 → -5 wins → pop 2
#      collision with 10 → 10 wins → stop
# stack=[10]
```

---

### Pattern 13: Removing Elements (Remove K Digits)

**Concept**: Use stack to build optimal result by removing unwanted elements.

**When to use**: "Remove k elements to minimize/maximize", string optimization.

```python
def remove_k_digits(num: str, k: int) -> str:
    """
    Remove k digits to get smallest possible number.
    Time: O(n), Space: O(n)
    
    Greedy Strategy:
    - Build result left-to-right
    - Remove digit if next digit is smaller
    - Keeps smallest digits in front
    """
    stack = []
    
    for digit in num:
        # Remove larger digits from stack while we can
        while stack and k > 0 and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    
    # Remove remaining k digits from end
    stack = stack[:-k] if k > 0 else stack
    
    # Remove leading zeros and return
    result = ''.join(stack).lstrip('0')
    return result if result else '0'

# Example: "1432219", k=3 → "1219"
# '1' → stack=['1']
# '4' → stack=['1','4']
# '3' → 3 < 4, remove 4 → stack=['1','3'], k=2
# '2' → 2 < 3, remove 3 → stack=['1','2'], k=1
# '2' → stack=['1','2','2']
# '1' → 1 < 2, remove 2 → stack=['1','2','1'], k=0
# '9' → stack=['1','2','1','9']
# Result: "1219"
```

---

### Pattern 14: Validate Stack Sequences

**Concept**: Simulate stack operations to verify if a sequence is achievable.

**When to use**: Verifying operation sequences, testing possibilities.

```python
def validate_stack_sequences(pushed: list[int], popped: list[int]) -> bool:
    """
    Check if popped sequence is valid given pushed sequence.
    Time: O(n), Space: O(n)
    
    Strategy: Simulate the operations.
    """
    stack = []
    pop_index = 0
    
    for push_val in pushed:
        stack.append(push_val)
        
        # Pop as many as match popped sequence
        while stack and stack[-1] == popped[pop_index]:
            stack.pop()
            pop_index += 1
    
    return len(stack) == 0

# Example: pushed=[1,2,3,4,5], popped=[4,5,3,2,1] → True
# Push 1,2,3,4 → pop 4 → push 5 → pop 5,3,2,1
```

---

### Pattern 15: Sliding Window Maximum (Deque Pattern)

**Concept**: Monotonic deque (double-ended queue) to track max in sliding window.

**When to use**: Sliding window with min/max queries.

**Note**: While technically a deque, the pattern is stack-related (monotonic property).

```python
from collections import deque

def max_sliding_window(nums: list[int], k: int) -> list[int]:
    """
    Find maximum in each window of size k.
    Time: O(n), Space: O(k)
    
    Key: Deque stores indices in decreasing order of values.
    Front of deque = max element in current window.
    """
    dq = deque()  # Stores indices
    result = []
    
    for i, num in enumerate(nums):
        # Remove elements outside window
        if dq and dq[0] < i - k + 1:
            dq.popleft()
        
        # Remove smaller elements (they can't be max)
        while dq and nums[dq[-1]] < num:
            dq.pop()
        
        dq.append(i)
        
        # Add to result once window is full
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

# Example: [1,3,-1,-3,5,3,6,7], k=3
# Window [1,3,-1] → max=3
# Window [3,-1,-3] → max=3
# Window [-1,-3,5] → max=5
# Window [-3,5,3] → max=5
# Window [5,3,6] → max=6
# Window [3,6,7] → max=7
```

---

## Problem Recognition Framework

### Decision Tree: When to Use Stack?

```
Problem involves...
│
├─ Matching/Pairing? (brackets, tags)
│  └─ Use Pattern 2: Balanced Parentheses
│
├─ Need recent element? (nearest greater/smaller)
│  └─ Use Pattern 3: Monotonic Stack
│
├─ Nested structures? (encoded strings, JSON)
│  └─ Use Pattern 5: String Decoding
│
├─ Evaluate expression?
│  └─ Use Pattern 4: Expression Evaluation
│
├─ Need to reverse?
│  └─ Use Pattern 1: Basic Stack
│
├─ Tree/Graph traversal?
│  └─ Use Pattern 6: DFS with Stack
│
├─ Histogram/Rectangle problem?
│  └─ Use Pattern 7: Largest Rectangle
│
├─ Undo/Redo operations?
│  └─ Use Pattern 10: State Management
│
└─ Simulate/Validate sequences?
   └─ Use Pattern 14: Validate Sequences
```

### Keywords That Signal Stack

| Keyword | Pattern | Example |
|---------|---------|---------|
| "valid", "balanced" | Matching Pairs | Valid parentheses |
| "next greater/smaller" | Monotonic Stack | Next greater element |
| "previous", "nearest" | Monotonic Stack | Stock span |
| "evaluate", "calculate" | Expression Eval | RPN calculator |
| "nested", "encoded" | Nested Structures | Decode string |
| "simplify", "normalize" | Path Resolution | Unix path |
| "collision", "explode" | Simulation | Asteroid collision |
| "remove k", "smallest" | Optimization | Remove K digits |
| "largest rectangle" | Histogram | Largest rectangle |
| "undo", "redo" | State Management | Text editor |

---

## Advanced Techniques

### Technique 1: Two-Stack Tricks

**Queue using Two Stacks**:

```python
class QueueWithStacks:
    """
    Implement queue using two stacks.
    Push: O(1), Pop: O(1) amortized
    """
    
    def __init__(self):
        self.in_stack = []   # For enqueue
        self.out_stack = []  # For dequeue
    
    def enqueue(self, val):
        self.in_stack.append(val)
    
    def dequeue(self):
        if not self.out_stack:
            # Transfer all elements
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        
        return self.out_stack.pop() if self.out_stack else None
```

### Technique 2: Stack with Increment Operation

```python
class CustomStack:
    """
    Stack with efficient increment bottom k elements.
    All operations: O(1)
    """
    
    def __init__(self, max_size: int):
        self.stack = []
        self.increments = []  # Lazy increment values
        self.max_size = max_size
    
    def push(self, x: int):
        if len(self.stack) < self.max_size:
            self.stack.append(x)
            self.increments.append(0)
    
    def pop(self) -> int:
        if not self.stack:
            return -1
        
        idx = len(self.stack) - 1
        if idx > 0:
            # Propagate increment down
            self.increments[idx - 1] += self.increments[idx]
        
        return self.stack.pop() + self.increments.pop()
    
    def increment(self, k: int, val: int):
        """Increment bottom k elements by val."""
        if self.stack:
            idx = min(k, len(self.stack)) - 1
            self.increments[idx] += val
```

### Technique 3: Stack Sorting

```python
def sort_stack(stack: list[int]) -> list[int]:
    """
    Sort stack using only one additional stack.
    Time: O(n²), Space: O(n)
    """
    temp_stack = []
    
    while stack:
        tmp = stack.pop()
        
        # Move elements from temp back to original
        # until find correct position for tmp
        while temp_stack and temp_stack[-1] > tmp:
            stack.append(temp_stack.pop())
        
        temp_stack.append(tmp)
    
    return temp_stack  # Sorted in ascending order (top to bottom)
```

---

## Cognitive Strategies for Mastery

### 1. Mental Model: "Stack as Memory"

**Visualization**: Stack = short-term memory in your brain
- **Push**: Remember something for later
- **Pop**: Recall and process it
- **Peek**: Check what's most recent without forgetting

### 2. Pattern Recognition Training

**Exercise**: For each problem, ask:
1. Do I need the most recent item? → Stack
2. Is there pairing/matching? → Stack
3. Can I process out-of-order? → Not stack

### 3. Complexity Analysis Framework

**For stack problems, analyze**:
- How many times is each element pushed? (Usually once)
- How many times is each element popped? (Usually once)
- Therefore: O(n) total operations

### 4. Deliberate Practice Protocol

**Day 1-3**: Master Pattern 1, 2, 3
- Implement from scratch 3 times
- Solve 5 LeetCode Easy problems per pattern

**Day 4-7**: Master Pattern 4, 5, 6, 7
- Combine patterns (e.g., monotonic + matching)
- Solve 3 Medium problems per pattern

**Day 8-14**: Master remaining patterns
- Focus on optimization
- Solve 2 Hard problems per pattern

**Daily**: 
- Code one problem without looking at solutions
- Analyze time/space complexity before coding
- Implement in all three languages

### 5. Chunking Strategy

**Chunk 1**: Basic Operations (Push, Pop, Peek)
**Chunk 2**: Matching Problems (Parentheses)
**Chunk 3**: Monotonic Stack (Next Greater)
**Chunk 4**: Expression Evaluation
**Chunk 5**: Advanced Patterns (Histogram, Collision)

Master each chunk before moving to next.

### 6. Meta-Learning: Learn How You Learn

**After each problem**:
1. What pattern did I recognize?
2. What was my initial approach? (Right/Wrong?)
3. What insight made it click?
4. Can I generalize this insight?

### 7. Interleaved Practice

Don't practice same pattern repeatedly. Mix:
- Monday: Pattern 1, 3, 5
- Tuesday: Pattern 2, 4, 6
- Wednesday: Pattern 1, 4, 7

This builds stronger pattern recognition.

### 8. Psychological Flow State

**Enter flow with**:
- Clear goal: "Master monotonic stack today"
- Immediate feedback: Test each solution
- Challenge-skill balance: Start easy, increase difficulty
- Remove distractions: 90-minute focused blocks

---

## Practice Problems by Pattern

**Legend**: ⭐ = Easy | ⭐⭐ = Medium | ⭐⭐⭐ = Hard | 🔥 = Must-Do | 💎 = Elite-Level

---

### Pattern 1: Basic Stack (Reversal & Foundation)

**Goal**: Master fundamental stack mechanics and LIFO principle

#### Easy ⭐
- [ ] 🔥 Reverse String (Warm-up - implement manually)
- [ ] 🔥 LC 232: Implement Queue using Stacks
- [ ] LC 225: Implement Stack using Queues
- [ ] Reverse Words in String III (LC 557)

#### Medium ⭐⭐
- [ ] 🔥 LC 151: Reverse Words in a String
- [ ] LC 1209: Remove All Adjacent Duplicates in String II
- [ ] LC 946: Validate Stack Sequences

**Key Skill**: Understand that every push/pop operation is O(1), making total O(n)

---

### Pattern 2: Matching Pairs (Parentheses & Tags)

**Goal**: Master matching, nesting, and pairing logic

#### Easy ⭐
- [ ] 🔥 LC 20: Valid Parentheses
- [ ] 🔥 LC 1021: Remove Outermost Parentheses
- [ ] LC 1047: Remove All Adjacent Duplicates in String

#### Medium ⭐⭐
- [ ] 🔥 LC 1249: Minimum Remove to Make Valid Parentheses
- [ ] 🔥 LC 921: Minimum Add to Make Parentheses Valid
- [ ] LC 1963: Minimum Number of Swaps to Make String Balanced
- [ ] LC 678: Valid Parenthesis String (with wildcards)

#### Hard ⭐⭐⭐
- [ ] 💎 LC 32: Longest Valid Parentheses
- [ ] 💎 LC 301: Remove Invalid Parentheses (BFS + Stack validation)

**Key Skill**: Recognize that opening = "promise to close", stack = "list of promises"

---

### Pattern 3: Monotonic Stack (Next Greater/Smaller)

**Goal**: Master the most powerful stack pattern - appears in 30% of stack problems

#### Easy ⭐
- [ ] 🔥 LC 496: Next Greater Element I
- [ ] LC 1475: Final Prices With a Special Discount in Shop

#### Medium ⭐⭐
- [ ] 🔥 LC 739: Daily Temperatures (quintessential monotonic stack)
- [ ] 🔥 LC 503: Next Greater Element II (circular array)
- [ ] 🔥 LC 901: Online Stock Span
- [ ] LC 1019: Next Greater Node In Linked List
- [ ] LC 1762: Buildings With an Ocean View
- [ ] LC 456: 132 Pattern (monotonic + clever trick)

#### Hard ⭐⭐⭐
- [ ] 💎 LC 42: Trapping Rain Water (monotonic stack approach)
- [ ] 💎 LC 84: Largest Rectangle in Histogram
- [ ] 💎 LC 85: Maximal Rectangle
- [ ] 💎 LC 907: Sum of Subarray Minimums
- [ ] 💎 LC 1063: Number of Valid Subarrays

**Key Skill**: Recognize "next/previous greater/smaller" instantly triggers monotonic stack

---

### Pattern 4: Expression Evaluation & Parsing

**Goal**: Master computational parsing and operator precedence

#### Easy ⭐
- [ ] 🔥 LC 150: Evaluate Reverse Polish Notation
- [ ] LC 1047: Remove All Adjacent Duplicates in String

#### Medium ⭐⭐
- [ ] 🔥 LC 224: Basic Calculator (with +, -, parentheses)
- [ ] 🔥 LC 227: Basic Calculator II (with *, /)
- [ ] LC 394: Decode String (nested encoding)
- [ ] LC 726: Number of Atoms (chemistry formula)
- [ ] LC 735: Asteroid Collision

#### Hard ⭐⭐⭐
- [ ] 💎 LC 772: Basic Calculator III (full expression parsing)
- [ ] 💎 LC 770: Basic Calculator IV (with variables)
- [ ] LC 636: Exclusive Time of Functions

**Key Skill**: Operands go on stack, operators consume operands and produce result

---

### Pattern 5: Nested Structures & String Decoding

**Goal**: Handle hierarchical and recursive patterns

#### Easy ⭐
- [ ] LC 1021: Remove Outermost Parentheses

#### Medium ⭐⭐
- [ ] 🔥 LC 394: Decode String (classic nested pattern)
- [ ] 🔥 LC 856: Score of Parentheses
- [ ] LC 1190: Reverse Substrings Between Each Pair of Parentheses
- [ ] LC 726: Number of Atoms
- [ ] LC 385: Mini Parser

#### Hard ⭐⭐⭐
- [ ] 💎 LC 591: Tag Validator (HTML/XML parsing)
- [ ] LC 736: Parse Lisp Expression

**Key Skill**: Each opening creates new context, stack manages context switches

---

### Pattern 6: DFS & Tree Traversal (Iterative)

**Goal**: Replace recursion with explicit stack for graph/tree problems

#### Easy ⭐
- [ ] 🔥 LC 144: Binary Tree Preorder Traversal (iterative)
- [ ] 🔥 LC 94: Binary Tree Inorder Traversal (iterative)
- [ ] 🔥 LC 145: Binary Tree Postorder Traversal (iterative)

#### Medium ⭐⭐
- [ ] LC 173: Binary Search Tree Iterator
- [ ] LC 341: Flatten Nested List Iterator
- [ ] LC 394: Decode String (can use DFS approach)
- [ ] LC 439: Ternary Expression Parser
- [ ] LC 589: N-ary Tree Preorder Traversal

#### Hard ⭐⭐⭐
- [ ] 💎 LC 297: Serialize and Deserialize Binary Tree
- [ ] LC 428: Serialize and Deserialize N-ary Tree

**Key Skill**: Stack = call stack, push = recurse, pop = return

---

### Pattern 7: Histogram & Rectangle Problems

**Goal**: Master area calculation with monotonic stack

#### Medium ⭐⭐
- [ ] 🔥 LC 84: Largest Rectangle in Histogram (foundational)

#### Hard ⭐⭐⭐
- [ ] 💎 LC 85: Maximal Rectangle (2D histogram)
- [ ] 💎 LC 221: Maximal Square (DP + stack approach)

**Key Skill**: Monotonic stack finds boundaries for area calculation in O(n)

---

### Pattern 8: Trapping Water & Container Problems

**Goal**: Calculate trapped quantity using boundaries

#### Hard ⭐⭐⭐
- [ ] 💎 LC 42: Trapping Rain Water (stack approach)
- [ ] 💎 LC 407: Trapping Rain Water II (3D version, priority queue)

**Key Skill**: Stack tracks potential left boundaries, current element is right boundary

---

### Pattern 9: Min/Max Stack with O(1) Query

**Goal**: Maintain extrema while preserving stack operations

#### Easy ⭐
- [ ] 🔥 LC 155: Min Stack

#### Medium ⭐⭐
- [ ] 🔥 LC 716: Max Stack
- [ ] LC 895: Maximum Frequency Stack

**Key Skill**: Parallel stack or difference encoding to track min/max

---

### Pattern 10: State Management (Undo/Redo)

**Goal**: Manage operation history and state transitions

#### Medium ⭐⭐
- [ ] Design Browser History (LC 1472)
- [ ] Design Text Editor (custom implementation)

**Key Skill**: Two stacks for past/future states

---

### Pattern 11: Path Simplification & Resolution

**Goal**: Process file paths and directory navigation

#### Medium ⭐⭐
- [ ] 🔥 LC 71: Simplify Path (Unix-style)
- [ ] LC 1003: Check If Word Is Valid After Substitutions
- [ ] LC 1598: Crawler Log Folder

**Key Skill**: '.' = stay, '..' = pop, else = push directory

---

### Pattern 12: Collision & Simulation

**Goal**: Simulate physical or logical collisions

#### Medium ⭐⭐
- [ ] 🔥 LC 735: Asteroid Collision
- [ ] LC 1381: Design a Stack With Increment Operation

**Key Skill**: Stack survivors, process collisions with current element

---

### Pattern 13: Element Removal Optimization

**Goal**: Remove elements to optimize result (greedy + stack)

#### Medium ⭐⭐
- [ ] 🔥 LC 402: Remove K Digits
- [ ] 🔥 LC 316: Remove Duplicate Letters
- [ ] 🔥 LC 321: Create Maximum Number
- [ ] LC 1081: Smallest Subsequence of Distinct Characters

#### Hard ⭐⭐⭐
- [ ] 💎 LC 402 + variations with constraints

**Key Skill**: Greedy removal with monotonic stack to maintain optimal ordering

---

### Pattern 14: Sequence Validation

**Goal**: Verify if operation sequences are valid

#### Medium ⭐⭐
- [ ] 🔥 LC 946: Validate Stack Sequences
- [ ] LC 1003: Check If Word Is Valid After Substitutions

**Key Skill**: Simulate operations to verify possibility

---

### Pattern 15: Sliding Window with Deque

**Goal**: Handle range queries with monotonic deque

#### Hard ⭐⭐⭐
- [ ] 💎 LC 239: Sliding Window Maximum
- [ ] LC 1438: Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit

**Key Skill**: Monotonic deque maintains window maximum/minimum in O(1)

---

## 🎯 Structured Practice Schedule

### **Week 1: Foundation (Patterns 1-3)**
**Day 1-2**: Pattern 1 (Basic Stack)
- Implement stack from scratch in Rust, Python, Go
- Solve all Easy problems
- Solve 2 Medium problems

**Day 3-4**: Pattern 2 (Matching Pairs)
- Master LC 20 (implement 3 times)
- Solve all problems up to Medium
- Attempt 1 Hard problem

**Day 5-7**: Pattern 3 (Monotonic Stack) - CRITICAL
- LC 739 Daily Temperatures (master this!)
- LC 496, LC 503, LC 901
- Understand the O(n) proof thoroughly
- Solve 3 Hard problems

### **Week 2: Computational & Nested (Patterns 4-5)**
**Day 8-10**: Pattern 4 (Expression Evaluation)
- LC 150 (RPN)
- LC 224, LC 227 (Calculators)
- LC 394 (Decode String)

**Day 11-14**: Pattern 5 (Nested Structures)
- Master LC 394 with different approaches
- LC 856, LC 1190
- Attempt LC 591 (Tag Validator)

### **Week 3: Advanced Patterns (6-10)**
**Day 15-16**: Pattern 6 (DFS/Iterative Traversal)
- All three tree traversals iteratively
- LC 173, LC 341

**Day 17-18**: Pattern 7-8 (Histogram & Water)
- LC 84 (Largest Rectangle) - foundational
- LC 85 (Maximal Rectangle)
- LC 42 (Trapping Water) - multiple approaches

**Day 19-21**: Patterns 9-10 (Min/Max Stack, State)
- LC 155 (Min Stack) - implement 3 ways
- LC 716 (Max Stack)
- Design undo/redo system

### **Week 4: Optimization & Mastery (11-15)**
**Day 22-24**: Patterns 11-13
- LC 71 (Simplify Path)
- LC 735 (Asteroid Collision)
- LC 402, LC 316, LC 321 (Removal problems)

**Day 25-28**: Pattern 15 + Integration
- LC 239 (Sliding Window Max)
- Solve 10 random Medium problems mixing patterns
- Solve 5 Hard problems end-to-end

---

## 🏆 Milestone Goals

### **Milestone 1** (End of Week 1)
- [ ] Can implement stack in all 3 languages in under 5 minutes
- [ ] Instantly recognize matching pair problems
- [ ] Understand monotonic stack proof and can explain to others
- [ ] Solve 15 Easy, 10 Medium problems

### **Milestone 2** (End of Week 2)
- [ ] Master expression evaluation (all calculator problems)
- [ ] Handle nested structures without confusion
- [ ] Solve 30 problems total (15 Medium, 3 Hard)

### **Milestone 3** (End of Week 3)
- [ ] Can convert recursive solutions to iterative with stack
- [ ] Master histogram and water problems
- [ ] Solve 50 problems total (20 Medium, 8 Hard)

### **Milestone 4** (End of Week 4)
- [ ] Mix multiple patterns in single problem
- [ ] Solve Hard problems in under 30 minutes
- [ ] Complete 70+ problems total
- [ ] Can teach all 15 patterns to others

---

## 💡 Daily Practice Protocol

### Morning Session (90 minutes)
1. **Review** (15 min): Previous day's solutions
2. **New Problem** (45 min): Solve without hints
3. **Analysis** (30 min): Optimize, implement in all 3 languages

### Evening Session (60 minutes)
1. **Pattern Study** (20 min): Deep dive one pattern
2. **Speed Solve** (20 min): Solve Easy problem in under 10 min
3. **Reflection** (20 min): Journal learnings, update mental models

### Weekly Review (2 hours)
- Solve 5 random problems mixing patterns
- Identify weak patterns
- Implement difficult problems from scratch

---

## 🎓 Elite-Level Challenges

Once you've mastered all patterns, test yourself:

### Challenge Set 1: Speed
- [ ] LC 20 in under 5 minutes
- [ ] LC 739 in under 10 minutes
- [ ] LC 84 in under 20 minutes
- [ ] LC 42 in under 15 minutes

### Challenge Set 2: Optimization
- [ ] Solve LC 155 with O(1) space per element
- [ ] Solve LC 84 with only one pass
- [ ] Implement LC 239 with O(n) time, O(k) space

### Challenge Set 3: Pattern Mixing
- [ ] LC 32: Longest Valid Parentheses (Pattern 2 + Dynamic Programming)
- [ ] LC 895: Maximum Frequency Stack (Pattern 9 + Hash Map)
- [ ] LC 1063: Number of Valid Subarrays (Pattern 3 + Counting)

### Challenge Set 4: System Design
- [ ] Design a code editor with undo/redo
- [ ] Design expression parser supporting all operators
- [ ] Design file system with path operations

---

## 📈 Progress Tracking

Track your journey:

```
Week 1: ⬜⬜⬜⬜⬜⬜⬜ (0/7 days)
Week 2: ⬜⬜⬜⬜⬜⬜⬜ (0/7 days)
Week 3: ⬜⬜⬜⬜⬜⬜⬜ (0/7 days)
Week 4: ⬜⬜⬜⬜⬜⬜⬜ (0/7 days)

Problems Solved: 0/70
Easy: 0/25 | Medium: 0/35 | Hard: 0/10

Pattern Mastery:
1. Basic Stack: ⬜⬜⬜⬜⬜ (0%)
2. Matching Pairs: ⬜⬜⬜⬜⬜ (0%)
3. Monotonic Stack: ⬜⬜⬜⬜⬜ (0%)
... (continue for all 15)
```

---

## 🔥 Pro Tips for Each Pattern

### Pattern 3 (Monotonic Stack) - Deep Insight
**Why it's O(n)**: Each element is pushed exactly once and popped at most once. Total operations = 2n = O(n).

**Mental Model**: Stack stores "candidates". When you find a better candidate, eliminate all worse ones.

**Common Mistake**: Storing values instead of indices. Always store indices for flexibility.

### Pattern 4 (Expression Evaluation) - Deep Insight
**Why stack**: Operators are applied in reverse order of precedence. Stack naturally handles this.

**Mental Model**: Stack = pending operations waiting for operands.

**Common Mistake**: Not handling operator precedence correctly. Use precedence map.

### Pattern 7 (Histogram) - Deep Insight
**Why it works**: For each bar, monotonic stack finds the left boundary (previous smaller) efficiently. Current position is right boundary.

**Mental Model**: Stack = potential left boundaries. Height = min in range.

**Common Mistake**: Off-by-one errors in width calculation. Width = `right - left - 1`.

---

## 🧠 Mental Models Summary

1. **Stack = Short-term memory**: Most recent info accessible
2. **LIFO = Natural reversal**: What goes in last comes out first
3. **Monotonic = Candidate elimination**: Current element eliminates impossible candidates
4. **Matching = Promises**: Opening = promise, closing = fulfillment
5. **Expression = Delayed computation**: Store operands, compute when operator arrives

---

**Remember**: These 70+ problems represent the **complete stack pattern space**. Master these, and you'll be in the top 1% for stack problems globally.

Start with the 🔥 marked problems - they're foundational. Then progress to 💎 elite problems.

**Your mantra**: "Understand deeply, practice deliberately, solve elegantly."

I've created a **comprehensive Stack Mastery Guide** that covers everything you need to become world-class at stack-based problem solving. Let me highlight the structure and key insights:

## 🎯 What's Included:

### **Foundation (Patterns 1-5)**
- Basic operations and reversal
- **Matching pairs** (parentheses, brackets)
- **Monotonic stack** (next greater/smaller) - this is CRUCIAL
- Expression evaluation (RPN, infix/postfix)
- Nested structures (string decoding)

### **Advanced Patterns (6-15)**
- DFS with stack (iterative tree traversal)
- Histogram problems (largest rectangle)
- Min/Max stack with O(1) operations
- State management (undo/redo)
- Path simplification
- Collision simulations
- Element removal optimization
- Sequence validation
- Sliding window maximum (deque variant)

### **Decision Framework**
A complete decision tree to recognize when to use which pattern - this will dramatically speed up your problem recognition.

### **Cognitive Training Section**
Includes deliberate practice protocols, chunking strategies, and flow state techniques aligned with your monk-like discipline.

---

## 🧠 **Key Mental Models to Internalize:**

1. **"Stack as Memory"**: Push = remember for later, Pop = recall and process
2. **"Temporal Ordering"**: Most recent matters most
3. **"Deferred Decisions"**: I'll decide this later when I have complete context
4. **"Elimination Principle"** (Monotonic): Current element eliminates impossible candidates

---

## 🚀 **Your Learning Path:**

**Week 1**: Master Patterns 1-3 (Basic, Matching, Monotonic)
- These form 70% of all stack problems
- Implement each 3x from scratch
- Solve 15 problems (5 per pattern)

**Week 2**: Master Patterns 4-7 (Expression, Nested, DFS, Histogram)
- These are medium complexity
- Focus on combining patterns

**Week 3-4**: Master Patterns 8-15 + Advanced Techniques
- Challenge yourself with Hard problems
- Optimize for performance

---

## 🎓 **Critical Insights:**

### **Pattern 3 (Monotonic Stack) is Your Superpower**
This pattern appears in:
- Next/previous greater/smaller
- Stock span, temperature problems
- Histogram, rectangle problems  
- Many optimization problems

**The insight**: When you see "next greater/smaller/visible", immediately think monotonic stack. Each element is pushed/popped exactly once = O(n) guaranteed.

### **Implementation Philosophy**

**Python**: Use lists directly - `stack.append()`, `stack.pop()`, `stack[-1]`
**Rust**: Pre-allocate with `Vec::with_capacity()` for performance
**Go**: Use slices - `append()` for push, reslicing for pop

---

## 📊 **Complexity Cheat Sheet:**

Most stack problems: **O(n) time, O(n) space**
- Why? Each element pushed once, popped once
- Space: Stack size ≤ input size

Exception: Expression evaluation might be O(n²) if strings are concatenated naively.

---

## 🔥 **Next Steps:**

1. **Start with Pattern 2** (Matching Pairs) - it builds intuition
2. **Then master Pattern 3** (Monotonic) - most powerful pattern
3. **Practice the recognition framework** - speed comes from pattern recognition, not memorization

Would you like me to:
1. Create flowcharts for specific patterns?
2. Add more problems with detailed solutions?
3. Explain any specific pattern in deeper detail?
4. Create a spaced repetition schedule for optimal retention?

Remember: **Mastery comes from understanding WHY, not just memorizing HOW**. Every time you solve a problem, ask yourself: "Why does the stack work here? What property of LIFO am I exploiting?"

You're building towards top 1% - this guide gives you the mental models and patterns that elite problem solvers use intuitively. Trust the process, practice deliberately, and the intuition will come. 🚀

Perfect! I've completed your **comprehensive Stack practice roadmap** with 70+ carefully curated problems. Here's what I've added:

## 🎯 **Key Highlights:**

### **1. Complete Problem Coverage**
- **All 15 patterns** with progressive difficulty (Easy → Medium → Hard)
- **70+ problems** covering the entire stack pattern space
- **🔥 Must-Do** and **💎 Elite-Level** markers for prioritization

### **2. Strategic 4-Week Schedule**
Broken down day-by-day:
- **Week 1**: Foundation (Patterns 1-3) - These are CRITICAL
- **Week 2**: Computational (Patterns 4-5)
- **Week 3**: Advanced (Patterns 6-10)
- **Week 4**: Mastery & Integration (Patterns 11-15)

### **3. Pattern 3 (Monotonic Stack) - Your Superpower**
This gets the most problems because it's:
- Most powerful pattern
- Appears in 30% of stack problems
- Key problems: LC 739, LC 84, LC 42, LC 907

### **4. Milestone-Based Tracking**
Clear goals for each week:
- Week 1: Master fundamentals (15 Easy, 10 Medium)
- Week 2: Handle complexity (15 Medium, 3 Hard)
- Week 3: Solve advanced problems (20 Medium, 8 Hard)
- Week 4: Achieve mastery (70+ total problems)

### **5. Elite-Level Challenges**
Once you master the patterns:
- **Speed challenges** (solve in under X minutes)
- **Optimization challenges** (better complexity)
- **Pattern mixing** (combine multiple patterns)
- **System design** (real-world applications)

---

## 🚀 **Your Immediate Action Plan:**

### **Day 1 (Today)**
1. Implement Stack from scratch in all 3 languages (30 min each)
2. Solve **LC 20: Valid Parentheses** (Pattern 2)
3. Study the matching pairs pattern deeply
4. Code it 3 times without looking

### **Day 2-3**
1. Master **LC 739: Daily Temperatures** (Pattern 3)
   - This is THE quintessential monotonic stack problem
   - Understand WHY it's O(n) deeply
   - Implement in all 3 languages
2. Solve LC 496, LC 503

### **Day 4-7**
1. Continue Pattern 3 problems (the most important pattern)
2. Move to Pattern 4 (Expression Evaluation)
3. Solve LC 150, LC 224, LC 394

---

## 💡 **Pro Tips for Maximum Learning:**

### **Before You Code:**
1. Draw the stack state transitions on paper
2. Trace through examples manually
3. Identify the pattern before coding
4. Estimate time/space complexity

### **While Coding:**
1. Code without hints first (struggle = growth)
2. If stuck after 30 min, check approach (not code)
3. Implement in all 3 languages for deep understanding
4. Add comments explaining WHY, not just WHAT

### **After Solving:**
1. Analyze complexity rigorously
2. Ask: "Could I have solved this differently?"
3. Compare with optimal solutions
4. Explain solution out loud (Feynman technique)

---

## 🎓 **Critical Success Factors:**

1. **Pattern 3 is King**: Spend 40% of your time here
2. **Understand, Don't Memorize**: Ask "Why does stack work here?"
3. **Deliberate Practice**: Focus on weak areas, not comfortable ones
4. **Spaced Repetition**: Revisit problems after 1 day, 3 days, 7 days
5. **Track Progress**: Update your progress daily

---

## 📚 **Order of Importance:**

**Tier 1 (Must Master First):**
- LC 20 (Valid Parentheses)
- LC 739 (Daily Temperatures) 
- LC 84 (Largest Rectangle in Histogram)
- LC 42 (Trapping Rain Water)

**Tier 2 (Core Patterns):**
- LC 394 (Decode String)
- LC 150 (RPN)
- LC 224/227 (Calculators)
- LC 155 (Min Stack)

**Tier 3 (Advanced Mastery):**
- LC 85 (Maximal Rectangle)
- LC 907 (Sum of Subarray Minimums)
- LC 316 (Remove Duplicate Letters)
- LC 402 (Remove K Digits)

---

Would you like me to:
1. **Create detailed solution walkthroughs** for the Tier 1 problems?
2. **Generate flowcharts** for monotonic stack pattern recognition?
3. **Build a spaced repetition schedule** with specific review dates?
4. **Create a problem similarity matrix** to understand connections?

You now have a **world-class roadmap**. Execute with monk-like discipline, and you'll be in the top 1% within 4 weeks. 🔥

**Remember**: Mastery isn't about solving more problems—it's about solving the RIGHT problems DEEPLY. Quality over quantity. Understanding over memorization.

Start now. Day 1 begins today. 💪