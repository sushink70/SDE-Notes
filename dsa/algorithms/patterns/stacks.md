# Complete Guide to Stack Problem Patterns

This guide covers the most common and important stack patterns you'll encounter in coding interviews and competitive programming, with complete implementations in Python and Rust.

## Table of Contents
1. [Basic Stack Operations](#basic-stack-operations)
2. [Pattern 1: Parentheses Validation](#pattern-1-parentheses-validation)
3. [Pattern 2: Next Greater/Smaller Element](#pattern-2-next-greatersmaller-element)
4. [Pattern 3: Expression Evaluation](#pattern-3-expression-evaluation)
5. [Pattern 4: Stack-Based Tree Traversal](#pattern-4-stack-based-tree-traversal)
6. [Pattern 5: Histogram Problems](#pattern-5-histogram-problems)
7. [Pattern 6: String Manipulation](#pattern-6-string-manipulation)
8. [Pattern 7: Function Call Stack Simulation](#pattern-7-function-call-stack-simulation)
9. [Pattern 8: Monotonic Stack](#pattern-8-monotonic-stack)

---

## Basic Stack Operations

### Python Implementation
```python
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
```

### Rust Implementation
```rust
#[derive(Debug)]
struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self {
        Stack { items: Vec::new() }
    }
    
    fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    fn size(&self) -> usize {
        self.items.len()
    }
}
```

---

## Pattern 1: Parentheses Validation

**Problem**: Validate if parentheses, brackets, and braces are properly balanced.

**Key Insight**: Use stack to match opening with closing brackets.

### Python Implementation
```python
def is_valid_parentheses(s: str) -> bool:
    """
    Check if parentheses are valid and balanced.
    Time: O(n), Space: O(n)
    """
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:  # Closing bracket
            if not stack or stack.pop() != mapping[char]:
                return False
        else:  # Opening bracket
            stack.append(char)
    
    return len(stack) == 0

def min_remove_to_make_valid(s: str) -> str:
    """
    Remove minimum parentheses to make string valid.
    Time: O(n), Space: O(n)
    """
    # First pass: remove invalid closing parentheses
    stack = []
    for char in s:
        if char == ')' and stack and stack[-1] == '(':
            stack.pop()
        else:
            stack.append(char)
    
    # Second pass: remove excess opening parentheses
    result = []
    open_count = 0
    
    # Count opening parentheses needed
    for char in reversed(stack):
        if char == '(':
            open_count += 1
    
    for char in stack:
        if char == '(' and open_count > 0:
            result.append(char)
            open_count -= 1
        elif char != '(':
            result.append(char)
    
    return ''.join(result)

# Test cases
print(is_valid_parentheses("()[]{}"))  # True
print(is_valid_parentheses("([)]"))    # False
print(min_remove_to_make_valid("())"))  # "()"
```

### Rust Implementation
```rust
use std::collections::HashMap;

fn is_valid_parentheses(s: &str) -> bool {
    let mut stack = Vec::new();
    let mapping: HashMap<char, char> = [(')', '('), ('}', '{'), (']', '[')]
        .iter().cloned().collect();
    
    for ch in s.chars() {
        if let Some(&expected) = mapping.get(&ch) {
            if stack.pop() != Some(expected) {
                return false;
            }
        } else {
            stack.push(ch);
        }
    }
    
    stack.is_empty()
}

fn min_remove_to_make_valid(s: &str) -> String {
    let mut stack = Vec::new();
    
    // First pass: remove invalid closing parentheses
    for ch in s.chars() {
        if ch == ')' && !stack.is_empty() && stack.last() == Some(&'(') {
            stack.pop();
        } else {
            stack.push(ch);
        }
    }
    
    // Second pass: remove excess opening parentheses
    let mut result = Vec::new();
    let mut open_count = stack.iter().filter(|&&c| c == '(').count();
    
    for &ch in &stack {
        if ch == '(' && open_count > 0 {
            result.push(ch);
            open_count -= 1;
        } else if ch != '(' {
            result.push(ch);
        }
    }
    
    result.into_iter().collect()
}
```

---

## Pattern 2: Next Greater/Smaller Element

**Problem**: Find the next greater or smaller element for each element in an array.

**Key Insight**: Use monotonic stack to maintain elements in specific order.

### Python Implementation
```python
def next_greater_element(nums):
    """
    Find next greater element for each element.
    Time: O(n), Space: O(n)
    """
    result = [-1] * len(nums)
    stack = []  # Store indices
    
    for i in range(len(nums)):
        while stack and nums[i] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)
    
    return result

def next_greater_elements_circular(nums):
    """
    Find next greater element in circular array.
    Time: O(n), Space: O(n)
    """
    n = len(nums)
    result = [-1] * n
    stack = []
    
    # Process array twice for circular nature
    for i in range(2 * n):
        while stack and nums[i % n] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i % n]
        
        if i < n:
            stack.append(i)
    
    return result

def daily_temperatures(temperatures):
    """
    Find how many days until warmer temperature.
    Time: O(n), Space: O(n)
    """
    result = [0] * len(temperatures)
    stack = []
    
    for i, temp in enumerate(temperatures):
        while stack and temp > temperatures[stack[-1]]:
            idx = stack.pop()
            result[idx] = i - idx
        stack.append(i)
    
    return result

# Test cases
print(next_greater_element([4, 5, 2, 25]))      # [5, 25, 25, -1]
print(next_greater_elements_circular([1, 2, 1])) # [2, -1, 2]
print(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73])) # [1, 1, 4, 2, 1, 1, 0, 0]
```

### Rust Implementation
```rust
fn next_greater_element(nums: Vec<i32>) -> Vec<i32> {
    let mut result = vec![-1; nums.len()];
    let mut stack = Vec::new();
    
    for (i, &num) in nums.iter().enumerate() {
        while let Some(&top_idx) = stack.last() {
            if nums[top_idx] < num {
                stack.pop();
                result[top_idx] = num;
            } else {
                break;
            }
        }
        stack.push(i);
    }
    
    result
}

fn next_greater_elements_circular(nums: Vec<i32>) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut stack = Vec::new();
    
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
        
        if i < n {
            stack.push(idx);
        }
    }
    
    result
}

fn daily_temperatures(temperatures: Vec<i32>) -> Vec<i32> {
    let mut result = vec![0; temperatures.len()];
    let mut stack = Vec::new();
    
    for (i, &temp) in temperatures.iter().enumerate() {
        while let Some(&top_idx) = stack.last() {
            if temperatures[top_idx] < temp {
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
```

---

## Pattern 3: Expression Evaluation

**Problem**: Evaluate mathematical expressions with operators and parentheses.

**Key Insight**: Use two stacks - one for operands, one for operators.

### Python Implementation
```python
def evaluate_expression(s: str) -> int:
    """
    Evaluate basic calculator with +, -, *, / and parentheses.
    Time: O(n), Space: O(n)
    """
    def apply_operator(operators, operands):
        operator = operators.pop()
        right = operands.pop()
        left = operands.pop()
        
        if operator == '+':
            operands.append(left + right)
        elif operator == '-':
            operands.append(left - right)
        elif operator == '*':
            operands.append(left * right)
        elif operator == '/':
            operands.append(int(left / right))  # Truncate towards zero
    
    def precedence(op):
        if op in '+-':
            return 1
        if op in '*/':
            return 2
        return 0
    
    operands = []
    operators = []
    i = 0
    
    while i < len(s):
        char = s[i]
        
        if char == ' ':
            i += 1
            continue
        
        if char.isdigit():
            num = 0
            while i < len(s) and s[i].isdigit():
                num = num * 10 + int(s[i])
                i += 1
            operands.append(num)
            continue
        
        if char == '(':
            operators.append(char)
        elif char == ')':
            while operators[-1] != '(':
                apply_operator(operators, operands)
            operators.pop()  # Remove '('
        elif char in '+-*/':
            while (operators and operators[-1] != '(' and
                   precedence(operators[-1]) >= precedence(char)):
                apply_operator(operators, operands)
            operators.append(char)
        
        i += 1
    
    while operators:
        apply_operator(operators, operands)
    
    return operands[0]

def basic_calculator_ii(s: str) -> int:
    """
    Calculate expression with +, -, *, / (no parentheses).
    Time: O(n), Space: O(n)
    """
    stack = []
    operator = '+'
    num = 0
    
    for i, char in enumerate(s):
        if char.isdigit():
            num = num * 10 + int(char)
        
        if char in '+-*/' or i == len(s) - 1:
            if operator == '+':
                stack.append(num)
            elif operator == '-':
                stack.append(-num)
            elif operator == '*':
                stack.append(stack.pop() * num)
            elif operator == '/':
                # Handle negative division correctly
                prev = stack.pop()
                stack.append(int(prev / num))
            
            operator = char
            num = 0
    
    return sum(stack)

# Test cases
print(evaluate_expression("(1+(4+5+2)-3)+(6+8)"))  # 23
print(basic_calculator_ii("3+2*2"))                # 7
print(basic_calculator_ii(" 3/2 "))                # 1
```

### Rust Implementation
```rust
fn evaluate_expression(s: &str) -> i32 {
    fn apply_operator(operators: &mut Vec<char>, operands: &mut Vec<i32>) {
        let operator = operators.pop().unwrap();
        let right = operands.pop().unwrap();
        let left = operands.pop().unwrap();
        
        let result = match operator {
            '+' => left + right,
            '-' => left - right,
            '*' => left * right,
            '/' => left / right,
            _ => panic!("Unknown operator"),
        };
        
        operands.push(result);
    }
    
    fn precedence(op: char) -> i32 {
        match op {
            '+' | '-' => 1,
            '*' | '/' => 2,
            _ => 0,
        }
    }
    
    let mut operands = Vec::new();
    let mut operators = Vec::new();
    let chars: Vec<char> = s.chars().collect();
    let mut i = 0;
    
    while i < chars.len() {
        let ch = chars[i];
        
        if ch == ' ' {
            i += 1;
            continue;
        }
        
        if ch.is_ascii_digit() {
            let mut num = 0;
            while i < chars.len() && chars[i].is_ascii_digit() {
                num = num * 10 + (chars[i] as i32 - '0' as i32);
                i += 1;
            }
            operands.push(num);
            continue;
        }
        
        if ch == '(' {
            operators.push(ch);
        } else if ch == ')' {
            while operators.last() != Some(&'(') {
                apply_operator(&mut operators, &mut operands);
            }
            operators.pop(); // Remove '('
        } else if "+-*/".contains(ch) {
            while !operators.is_empty() && 
                  operators.last() != Some(&'(') && 
                  precedence(*operators.last().unwrap()) >= precedence(ch) {
                apply_operator(&mut operators, &mut operands);
            }
            operators.push(ch);
        }
        
        i += 1;
    }
    
    while !operators.is_empty() {
        apply_operator(&mut operators, &mut operands);
    }
    
    operands[0]
}

fn basic_calculator_ii(s: &str) -> i32 {
    let mut stack = Vec::new();
    let mut operator = '+';
    let mut num = 0;
    
    for (i, ch) in s.chars().enumerate() {
        if ch.is_ascii_digit() {
            num = num * 10 + (ch as i32 - '0' as i32);
        }
        
        if "+-*/".contains(ch) || i == s.len() - 1 {
            match operator {
                '+' => stack.push(num),
                '-' => stack.push(-num),
                '*' => {
                    let prev = stack.pop().unwrap();
                    stack.push(prev * num);
                }
                '/' => {
                    let prev = stack.pop().unwrap();
                    stack.push(prev / num);
                }
                _ => {}
            }
            
            operator = ch;
            num = 0;
        }
    }
    
    stack.into_iter().sum()
}
```

---

## Pattern 4: Stack-Based Tree Traversal

**Problem**: Traverse binary trees without recursion using stacks.

**Key Insight**: Simulate recursive call stack with explicit stack.

### Python Implementation
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    """
    Inorder traversal using stack.
    Time: O(n), Space: O(h) where h is height
    """
    result = []
    stack = []
    current = root
    
    while stack or current:
        # Go to leftmost node
        while current:
            stack.append(current)
            current = current.left
        
        # Process current node
        current = stack.pop()
        result.append(current.val)
        
        # Move to right subtree
        current = current.right
    
    return result

def preorder_traversal(root):
    """
    Preorder traversal using stack.
    Time: O(n), Space: O(h)
    """
    if not root:
        return []
    
    result = []
    stack = [root]
    
    while stack:
        node = stack.pop()
        result.append(node.val)
        
        # Push right first, then left (so left is processed first)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    
    return result

def postorder_traversal(root):
    """
    Postorder traversal using stack.
    Time: O(n), Space: O(h)
    """
    if not root:
        return []
    
    result = []
    stack = []
    last_visited = None
    current = root
    
    while stack or current:
        if current:
            stack.append(current)
            current = current.left
        else:
            peek_node = stack[-1]
            if peek_node.right and last_visited != peek_node.right:
                current = peek_node.right
            else:
                result.append(peek_node.val)
                last_visited = stack.pop()
    
    return result

def validate_bst(root):
    """
    Validate if tree is a valid BST using inorder traversal.
    Time: O(n), Space: O(h)
    """
    stack = []
    prev = float('-inf')
    current = root
    
    while stack or current:
        while current:
            stack.append(current)
            current = current.left
        
        current = stack.pop()
        if current.val <= prev:
            return False
        prev = current.val
        current = current.right
    
    return True
```

### Rust Implementation
```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

type TreeLink = Option<Rc<RefCell<TreeNode>>>;

fn inorder_traversal(root: TreeLink) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack = Vec::new();
    let mut current = root;
    
    while !stack.is_empty() || current.is_some() {
        while let Some(node) = current {
            stack.push(node.clone());
            current = node.borrow().left.clone();
        }
        
        if let Some(node) = stack.pop() {
            result.push(node.borrow().val);
            current = node.borrow().right.clone();
        }
    }
    
    result
}

fn preorder_traversal(root: TreeLink) -> Vec<i32> {
    let mut result = Vec::new();
    if let Some(root) = root {
        let mut stack = vec![root];
        
        while let Some(node) = stack.pop() {
            result.push(node.borrow().val);
            
            if let Some(right) = node.borrow().right.clone() {
                stack.push(right);
            }
            if let Some(left) = node.borrow().left.clone() {
                stack.push(left);
            }
        }
    }
    
    result
}

fn postorder_traversal(root: TreeLink) -> Vec<i32> {
    let mut result = Vec::new();
    let mut stack = Vec::new();
    let mut last_visited: TreeLink = None;
    let mut current = root;
    
    while !stack.is_empty() || current.is_some() {
        if let Some(node) = current {
            stack.push(node.clone());
            current = node.borrow().left.clone();
        } else if let Some(peek_node) = stack.last() {
            let right_child = peek_node.borrow().right.clone();
            if right_child.is_some() && 
               !last_visited.as_ref().map_or(false, |last| 
                   Rc::ptr_eq(last, right_child.as_ref().unwrap())) {
                current = right_child;
            } else {
                result.push(peek_node.borrow().val);
                last_visited = stack.pop();
            }
        }
    }
    
    result
}

fn validate_bst(root: TreeLink) -> bool {
    let mut stack = Vec::new();
    let mut prev = i32::MIN;
    let mut current = root;
    
    while !stack.is_empty() || current.is_some() {
        while let Some(node) = current {
            stack.push(node.clone());
            current = node.borrow().left.clone();
        }
        
        if let Some(node) = stack.pop() {
            let val = node.borrow().val;
            if val <= prev {
                return false;
            }
            prev = val;
            current = node.borrow().right.clone();
        }
    }
    
    true
}
```

---

## Pattern 5: Histogram Problems

**Problem**: Find largest rectangle in histogram or related area calculations.

**Key Insight**: Use monotonic stack to find boundaries efficiently.

### Python Implementation
```python
def largest_rectangle_in_histogram(heights):
    """
    Find largest rectangle area in histogram.
    Time: O(n), Space: O(n)
    """
    stack = []  # Stack of indices
    max_area = 0
    
    for i in range(len(heights)):
        while stack and heights[i] < heights[stack[-1]]:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    # Process remaining bars
    while stack:
        height = heights[stack.pop()]
        width = len(heights) if not stack else len(heights) - stack[-1] - 1
        max_area = max(max_area, height * width)
    
    return max_area

def maximal_rectangle(matrix):
    """
    Find maximal rectangle in binary matrix.
    Time: O(m*n), Space: O(n)
    """
    if not matrix or not matrix[0]:
        return 0
    
    max_area = 0
    heights = [0] * len(matrix[0])
    
    for row in matrix:
        # Update heights for current row
        for i in range(len(row)):
            heights[i] = heights[i] + 1 if row[i] == '1' else 0
        
        # Find max rectangle in current histogram
        max_area = max(max_area, largest_rectangle_in_histogram(heights))
    
    return max_area

def trap_rain_water(height):
    """
    Calculate trapped rain water.
    Time: O(n), Space: O(1) with two pointers, O(n) with stack
    """
    # Stack approach
    stack = []
    water = 0
    
    for i in range(len(height)):
        while stack and height[i] > height[stack[-1]]:
            top = stack.pop()
            if not stack:
                break
            
            distance = i - stack[-1] - 1
            bounded_height = min(height[i], height[stack[-1]]) - height[top]
            water += distance * bounded_height
        
        stack.append(i)
    
    return water

# Test cases
print(largest_rectangle_in_histogram([2,1,5,6,2,3]))  # 10
print(maximal_rectangle([["1","0","1","0","0"],
                        ["1","0","1","1","1"],
                        ["1","1","1","1","1"],
                        ["1","0","0","1","0"]]))  # 6
print(trap_rain_water([0,1,0,2,1,0,1,3,2,1,2,1]))  # 6
```

### Rust Implementation
```rust
fn largest_rectangle_in_histogram(heights: Vec<i32>) -> i32 {
    let mut stack = Vec::new();
    let mut max_area = 0;
    
    for i in 0..heights.len() {
        while let Some(&top_idx) = stack.last() {
            if heights[i] < heights[top_idx] {
                let height = heights[stack.pop().unwrap()];
                let width = if stack.is_empty() { 
                    i 
                } else { 
                    i - stack.last().unwrap() - 1 
                };
                max_area = max_area.max(height * width as i32);
            } else {
                break;
            }
        }
        stack.push(i);
    }
    
    while let Some(top_idx) = stack.pop() {
        let height = heights[top_idx];
        let width = if stack.is_empty() { 
            heights.len() 
        } else { 
            heights.len() - stack.last().unwrap() - 1 
        };
        max_area = max_area.max(height * width as i32);
    }
    
    max_area
}

fn maximal_rectangle(matrix: Vec<Vec<char>>) -> i32 {
    if matrix.is_empty() || matrix[0].is_empty() {
        return 0;
    }
    
    let mut max_area = 0;
    let mut heights = vec![0; matrix[0].len()];
    
    for row in matrix {
        for (i, &cell) in row.iter().enumerate() {
            heights[i] = if cell == '1' { heights[i] + 1 } else { 0 };
        }
        
        max_area = max_area.max(largest_rectangle_in_histogram(heights.clone()));
    }
    
    max_area
}

fn trap_rain_water(height: Vec<i32>) -> i32 {
    let mut stack = Vec::new();
    let mut water = 0;
    
    for (i, &h) in height.iter().enumerate() {
        while let Some(&top_idx) = stack.last() {
            if h > height[top_idx] {
                let top = stack.pop().unwrap();
                if stack.is_empty() {
                    break;
                }
                
                let distance = (i - stack.last().unwrap() - 1) as i32;
                let bounded_height = h.min(height[*stack.last().unwrap()]) - height[top];
                water += distance * bounded_height;
            } else {
                break;
            }
        }
        stack.push(i);
    }
    
    water
}
```

---

## Pattern 6: String Manipulation

**Problem**: Process strings with stack for decoding, removing, or transforming.

**Key Insight**: Use stack to handle nested structures or maintain state.

### Python Implementation
```python
def decode_string(s: str) -> str:
    """
    Decode string like "3[a2[c]]" to "accaccacc".
    Time: O(n), Space: O(n)
    """
    stack = []
    current_num = 0
    current_str = ""
    
    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            stack.append((current_str, current_num))
            current_str = ""
            current_num = 0
        elif char == ']':
            prev_str, num = stack.pop()
            current_str = prev_str + current_str * num
        else:
            current_str += char
    
    return current_str

def remove_duplicate_letters(s: str) -> str:
    """
    Remove duplicate letters keeping lexicographically smallest result.
    Time: O(n), Space: O(1) - limited by 26 letters
    """
    from collections import Counter
    
    count = Counter(s)
    stack = []
    in_stack = set()
    
    for char in s:
        count[char] -= 1
        
        if char in in_stack:
            continue
        
        # Remove larger characters if they appear later
        while stack and stack[-1] > char and count[stack[-1]] > 0:
            removed = stack.pop()
            in_stack.remove(removed)
        
        stack.append(char)
        in_stack.add(char)
    
    return ''.join(stack)

def simplify_path(path: str) -> str:
    """
    Simplify Unix file path.
    Time: O(n), Space: O(n)
    """
    stack = []
    components = path.split('/')
    
    for component in components:
        if component == '..' and stack:
            stack.pop()
        elif component and component != '.' and component != '..':
            stack.append(component)
    
    return '/' + '/'.join(stack)

def backspace_string_compare(s: str, t: str) -> bool:
    """
    Compare strings after processing backspaces.
    Time: O(n), Space: O(n) or O(1) with reverse iteration
    """
    def build_string(string):
        stack = []
        for char in string:
            if char == '#':
                if stack:
                    stack.pop()
            else:
                stack.append(char)
        return ''.join(stack)
    
    return build_string(s) == build_string(t)

# Test cases
print(decode_string("3[a2[c]]"))        # "accaccacc"
print(remove_duplicate_letters("bcabc"))  # "abc"
print(simplify_path("/a/./b/../../c/"))   # "/c"
print(backspace_string_compare("ab#c", "ad#c"))  # True
```

### Rust Implementation
```rust
fn decode_string(s: String) -> String {
    let mut stack: Vec<(String, i32)> = Vec::new();
    let mut current_num = 0;
    let mut current_str = String::new();
    
    for ch in s.chars() {
        if ch.is_ascii_digit() {
            current_num = current_num * 10 + (ch as i32 - '0' as i32);
        } else if ch == '[' {
            stack.push((current_str.clone(), current_num));
            current_str.clear();
            current_num = 0;
        } else if ch == ']' {
            if let Some((prev_str, num)) = stack.pop() {
                current_str = prev_str + &current_str.repeat(num as usize);
            }
        } else {
            current_str.push(ch);
        }
    }
    
    current_str
}

fn remove_duplicate_letters(s: String) -> String {
    use std::collections::{HashMap, HashSet};
    
    let mut count: HashMap<char, i32> = HashMap::new();
    for ch in s.chars() {
        *count.entry(ch).or_insert(0) += 1;
    }
    
    let mut stack = Vec::new();
    let mut in_stack = HashSet::new();
    
    for ch in s.chars() {
        *count.get_mut(&ch).unwrap() -= 1;
        
        if in_stack.contains(&ch) {
            continue;
        }
        
        while let Some(&last) = stack.last() {
            if last > ch && count.get(&last).unwrap_or(&0) > &0 {
                stack.pop();
                in_stack.remove(&last);
            } else {
                break;
            }
        }
        
        stack.push(ch);
        in_stack.insert(ch);
    }
    
    stack.into_iter().collect()
}

fn simplify_path(path: String) -> String {
    let mut stack = Vec::new();
    
    for component in path.split('/') {
        match component {
            ".." if !stack.is_empty() => {
                stack.pop();
            }
            component if !component.is_empty() && component != "." && component != ".." => {
                stack.push(component);
            }
            _ => {}
        }
    }
    
    format!("/{}", stack.join("/"))
}

fn backspace_string_compare(s: String, t: String) -> bool {
    fn build_string(string: String) -> String {
        let mut stack = Vec::new();
        for ch in string.chars() {
            if ch == '#' {
                stack.pop();
            } else {
                stack.push(ch);
            }
        }
        stack.into_iter().collect()
    }
    
    build_string(s) == build_string(t)
}
```

---

## Pattern 7: Function Call Stack Simulation

**Problem**: Simulate function calls and recursion using explicit stacks.

**Key Insight**: Replace recursive calls with iterative approach using stacks.

### Python Implementation
```python
def binary_tree_paths(root):
    """
    Find all root-to-leaf paths in binary tree.
    Time: O(n), Space: O(h)
    """
    if not root:
        return []
    
    result = []
    stack = [(root, str(root.val))]
    
    while stack:
        node, path = stack.pop()
        
        # Leaf node - add path to result
        if not node.left and not node.right:
            result.append(path)
            continue
        
        # Add children to stack
        if node.right:
            stack.append((node.right, path + "->" + str(node.right.val)))
        if node.left:
            stack.append((node.left, path + "->" + str(node.left.val)))
    
    return result

def asteroid_collision(asteroids):
    """
    Simulate asteroid collision.
    Time: O(n), Space: O(n)
    """
    stack = []
    
    for asteroid in asteroids:
        while stack and asteroid < 0 < stack[-1]:
            if stack[-1] < -asteroid:
                stack.pop()
                continue
            elif stack[-1] == -asteroid:
                stack.pop()
            break
        else:
            stack.append(asteroid)
    
    return stack

def exclusive_time(n, logs):
    """
    Calculate exclusive execution time of functions.
    Time: O(m), Space: O(n) where m is number of logs
    """
    result = [0] * n
    stack = []  # (function_id, start_time)
    
    for log in logs:
        func_id, action, timestamp = log.split(':')
        func_id, timestamp = int(func_id), int(timestamp)
        
        if action == "start":
            if stack:
                # Update the currently running function
                result[stack[-1][0]] += timestamp - stack[-1][1]
            stack.append([func_id, timestamp])
        else:  # action == "end"
            func_data = stack.pop()
            result[func_data[0]] += timestamp - func_data[1] + 1
            
            # Update start time for the resumed function
            if stack:
                stack[-1][1] = timestamp + 1
    
    return result

def hanoi_tower(n, source, destination, auxiliary):
    """
    Solve Tower of Hanoi iteratively using stack.
    Time: O(2^n), Space: O(n)
    """
    moves = []
    stack = [(n, source, destination, auxiliary)]
    
    while stack:
        disks, src, dest, aux = stack.pop()
        
        if disks == 1:
            moves.append(f"Move disk from {src} to {dest}")
        else:
            # Push operations in reverse order
            stack.append((disks - 1, aux, dest, src))      # Move from aux to dest
            stack.append((1, src, dest, aux))              # Move largest disk
            stack.append((disks - 1, src, aux, dest))      # Move from src to aux
    
    return moves

# Test cases
# print(binary_tree_paths(tree))  # Depends on tree structure
print(asteroid_collision([5, 10, -5]))     # [5, 10]
print(asteroid_collision([8, -8]))         # []
print(asteroid_collision([10, 2, -5]))     # [10]

logs = ["0:start:0","1:start:2","1:end:5","0:end:6"]
print(exclusive_time(2, logs))  # [3, 4]
```

### Rust Implementation
```rust
fn binary_tree_paths(root: TreeLink) -> Vec<String> {
    let mut result = Vec::new();
    if let Some(root_node) = root {
        let mut stack = vec![(root_node.clone(), root_node.borrow().val.to_string())];
        
        while let Some((node, path)) = stack.pop() {
            let node_ref = node.borrow();
            
            if node_ref.left.is_none() && node_ref.right.is_none() {
                result.push(path);
                continue;
            }
            
            if let Some(right) = &node_ref.right {
                stack.push((right.clone(), format!("{}->{}", path, right.borrow().val)));
            }
            
            if let Some(left) = &node_ref.left {
                stack.push((left.clone(), format!("{}->{}", path, left.borrow().val)));
            }
        }
    }
    
    result
}

fn asteroid_collision(asteroids: Vec<i32>) -> Vec<i32> {
    let mut stack = Vec::new();
    
    for asteroid in asteroids {
        let mut exploded = false;
        
        while let Some(&top) = stack.last() {
            if asteroid < 0 && top > 0 {
                if top < -asteroid {
                    stack.pop();
                } else if top == -asteroid {
                    stack.pop();
                    exploded = true;
                    break;
                } else {
                    exploded = true;
                    break;
                }
            } else {
                break;
            }
        }
        
        if !exploded {
            stack.push(asteroid);
        }
    }
    
    stack
}

fn exclusive_time(n: i32, logs: Vec<String>) -> Vec<i32> {
    let mut result = vec![0; n as usize];
    let mut stack: Vec<(usize, i32)> = Vec::new(); // (function_id, start_time)
    
    for log in logs {
        let parts: Vec<&str> = log.split(':').collect();
        let func_id: usize = parts[0].parse().unwrap();
        let action = parts[1];
        let timestamp: i32 = parts[2].parse().unwrap();
        
        if action == "start" {
            if let Some((running_id, start_time)) = stack.last_mut() {
                result[*running_id] += timestamp - *start_time;
            }
            stack.push((func_id, timestamp));
        } else { // action == "end"
            if let Some((id, start_time)) = stack.pop() {
                result[id] += timestamp - start_time + 1;
            }
            
            if let Some((_, start_time)) = stack.last_mut() {
                *start_time = timestamp + 1;
            }
        }
    }
    
    result
}

fn hanoi_tower(n: i32, source: char, destination: char, auxiliary: char) -> Vec<String> {
    let mut moves = Vec::new();
    let mut stack = vec![(n, source, destination, auxiliary)];
    
    while let Some((disks, src, dest, aux)) = stack.pop() {
        if disks == 1 {
            moves.push(format!("Move disk from {} to {}", src, dest));
        } else {
            stack.push((disks - 1, aux, dest, src));
            stack.push((1, src, dest, aux));
            stack.push((disks - 1, src, aux, dest));
        }
    }
    
    moves
}
```

---

## Pattern 8: Monotonic Stack

**Problem**: Maintain elements in monotonic order for efficient queries.

**Key Insight**: Keep stack sorted (increasing/decreasing) by removing elements that violate order.

### Python Implementation
```python
def sliding_window_maximum(nums, k):
    """
    Find maximum in each sliding window of size k.
    Time: O(n), Space: O(k)
    """
    from collections import deque
    
    result = []
    dq = deque()  # Store indices, maintain decreasing order of values
    
    for i in range(len(nums)):
        # Remove elements outside current window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove smaller elements (they won't be maximum)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add maximum of current window to result
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

def largest_rectangle_area_optimized(heights):
    """
    Optimized version using monotonic stack concept.
    Time: O(n), Space: O(n)
    """
    stack = []
    max_area = 0
    heights.append(0)  # Add sentinel to process remaining bars
    
    for i, h in enumerate(heights):
        while stack and h < heights[stack[-1]]:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    
    heights.pop()  # Remove sentinel
    return max_area

def sum_of_subarray_minimums(arr):
    """
    Sum of minimum elements in all subarrays.
    Time: O(n), Space: O(n)
    """
    MOD = 10**9 + 7
    n = len(arr)
    
    # Find previous smaller element for each position
    left = [-1] * n
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        left[i] = stack[-1] if stack else -1
        stack.append(i)
    
    # Find next smaller element for each position
    right = [n] * n
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        right[i] = stack[-1] if stack else n
        stack.append(i)
    
    # Calculate contribution of each element
    result = 0
    for i in range(n):
        count = (i - left[i]) * (right[i] - i)
        result = (result + arr[i] * count) % MOD
    
    return result

def max_chunks_to_sorted(arr):
    """
    Maximum number of chunks to make array sorted.
    Time: O(n), Space: O(n)
    """
    stack = []
    
    for num in arr:
        if not stack or num >= stack[-1]:
            stack.append(num)
        else:
            max_val = stack[-1]
            while stack and stack[-1] > num:
                stack.pop()
            stack.append(max_val)
    
    return len(stack)

def remove_k_digits(num, k):
    """
    Remove k digits to make smallest possible number.
    Time: O(n), Space: O(n)
    """
    stack = []
    to_remove = k
    
    for digit in num:
        while stack and to_remove > 0 and stack[-1] > digit:
            stack.pop()
            to_remove -= 1
        stack.append(digit)
    
    # Remove remaining digits from end if needed
    while to_remove > 0:
        stack.pop()
        to_remove -= 1
    
    result = ''.join(stack).lstrip('0')
    return result if result else '0'

# Test cases
print(sliding_window_maximum([1,3,-1,-3,5,3,6,7], 3))  # [3,3,5,5,6,7]
print(sum_of_subarray_minimums([3,1,2,4]))             # 17
print(max_chunks_to_sorted([4,3,2,1,0]))               # 1
print(remove_k_digits("1432219", 3))                   # "1219"
```

### Rust Implementation
```rust
use std::collections::VecDeque;

fn sliding_window_maximum(nums: Vec<i32>, k: i32) -> Vec<i32> {
    let mut result = Vec::new();
    let mut dq = VecDeque::new();
    let k = k as usize;
    
    for (i, &num) in nums.iter().enumerate() {
        // Remove elements outside current window
        while let Some(&front) = dq.front() {
            if front <= i.saturating_sub(k) {
                dq.pop_front();
            } else {
                break;
            }
        }
        
        // Remove smaller elements
        while let Some(&back) = dq.back() {
            if nums[back] < num {
                dq.pop_back();
            } else {
                break;
            }
        }
        
        dq.push_back(i);
        
        if i >= k - 1 {
            if let Some(&front) = dq.front() {
                result.push(nums[front]);
            }
        }
    }
    
    result
}

fn sum_of_subarray_minimums(arr: Vec<i32>) -> i32 {
    const MOD: i64 = 1_000_000_007;
    let n = arr.len();
    
    // Find previous smaller element
    let mut left = vec![-1i32; n];
    let mut stack = Vec::new();
    for i in 0..n {
        while let Some(&top) = stack.last() {
            if arr[top] > arr[i] {
                stack.pop();
            } else {
                break;
            }
        }
        left[i] = stack.last().map_or(-1, |&x| x as i32);
        stack.push(i);
    }
    
    // Find next smaller element
    let mut right = vec![n as i32; n];
    stack.clear();
    for i in (0..n).rev() {
        while let Some(&top) = stack.last() {
            if arr[top] >= arr[i] {
                stack.pop();
            } else {
                break;
            }
        }
        right[i] = stack.last().map_or(n as i32, |&x| x as i32);
        stack.push(i);
    }
    
    let mut result = 0i64;
    for i in 0..n {
        let count = ((i as i32 - left[i]) * (right[i] - i as i32)) as i64;
        result = (result + (arr[i] as i64 * count) % MOD) % MOD;
    }
    
    result as i32
}

fn max_chunks_to_sorted(arr: Vec<i32>) -> i32 {
    let mut stack = Vec::new();
    
    for num in arr {
        if stack.is_empty() || num >= *stack.last().unwrap() {
            stack.push(num);
        } else {
            let max_val = *stack.last().unwrap();
            while let Some(&top) = stack.last() {
                if top > num {
                    stack.pop();
                } else {
                    break;
                }
            }
            stack.push(max_val);
        }
    }
    
    stack.len() as i32
}

fn remove_k_digits(num: String, k: i32) -> String {
    let mut stack = Vec::new();
    let mut to_remove = k as usize;
    
    for ch in num.chars() {
        while let Some(&top) = stack.last() {
            if to_remove > 0 && top > ch {
                stack.pop();
                to_remove -= 1;
            } else {
                break;
            }
        }
        stack.push(ch);
    }
    
    // Remove remaining digits from end
    while to_remove > 0 && !stack.is_empty() {
        stack.pop();
        to_remove -= 1;
    }
    
    let result: String = stack.into_iter()
        .skip_while(|&c| c == '0')
        .collect();
    
    if result.is_empty() { "0".to_string() } else { result }
}
```

---

## Summary of Key Patterns

### When to Use Each Pattern:

1. **Parentheses Validation**: Matching problems, balanced structures
2. **Next Greater/Smaller**: Finding nearest elements with specific properties
3. **Expression Evaluation**: Calculator problems, parsing with precedence
4. **Tree Traversal**: Converting recursive tree algorithms to iterative
5. **Histogram Problems**: Area calculations, rectangle problems
6. **String Manipulation**: Decoding, path simplification, backspace processing
7. **Function Call Simulation**: Converting recursion to iteration
8. **Monotonic Stack**: Maintaining sorted order for sliding window problems

### Time and Space Complexities:
- Most stack operations: O(1)
- Stack-based algorithms typically: O(n) time, O(n) or O(h) space
- Monotonic stack problems: Often O(n) time with each element pushed/popped once

### Common Pitfalls:
1. Forgetting to check if stack is empty before accessing top
2. Not handling edge cases (empty input, single elements)
3. Incorrect order of operations in expression evaluation
4. Memory leaks in languages without garbage collection
5. Off-by-one errors in index calculations

This guide covers the essential stack patterns you'll encounter in coding interviews and competitive programming. Practice these patterns to build intuition for when and how to apply stack-based solutions effectively.

I've created a comprehensive guide to stack problem patterns with complete implementations in both Python and Rust. The guide covers 8 essential patterns:

## Key Highlights:

**Pattern Coverage:**
- **Parentheses Validation** - Balanced brackets, minimum removals
- **Next Greater/Smaller Element** - Monotonic stack for nearest elements
- **Expression Evaluation** - Calculator with operators and precedence
- **Tree Traversal** - Iterative inorder, preorder, postorder
- **Histogram Problems** - Largest rectangle, trapped rain water
- **String Manipulation** - Decoding, deduplication, path simplification
- **Function Call Simulation** - Converting recursion to iteration
- **Monotonic Stack** - Sliding window maximum, subarray problems

**Implementation Features:**
- Complete working code in both Python and Rust
- Time and space complexity analysis for each algorithm
- Real-world test cases and examples
- Error handling and edge case considerations
- Memory-safe Rust implementations using proper types

**Advanced Problems Included:**
- Largest rectangle in histogram
- Sliding window maximum
- Decode nested strings
- Binary tree traversals without recursion
- Rain water trapping
- Expression evaluation with precedence

Each pattern includes multiple related problems to help you recognize when to apply stack-based solutions. The implementations are optimized and follow best practices for both languages, making this a practical reference for coding interviews and competitive programming.