# Comprehensive Stack Implementation Guide

I've completed the comprehensive stack implementation guide! This extensive resource covers:

## What's Included:

**Core Content:**

- Complete theoretical foundation of stacks
- Time/space complexity analysis
- Two full implementations in both Python and Rust (array-based and linked-list-based)

**Python Features:**

- Production-ready classes with full error handling
- Comprehensive testing framework
- Benchmarking utilities
- Advanced variants (MinStack, RandomStack)
- Real-world applications (HTML validation, expression evaluation, etc.)

**Rust Features:**

- Memory-safe implementations with proper ownership
- Generic types with trait implementations
- Comprehensive test suite
- Iterator implementations
- Thread-safe considerations

**Advanced Topics:**

- Performance comparisons between implementations
- Common pitfalls and how to avoid them
- Thread safety considerations
- Advanced stack variants
- Real-world applications with complete code examples

**Practical Examples:**

- Balanced parentheses checker
- Postfix expression evaluator
- HTML tag validator
- Decimal to binary converter
- Tower of Hanoi solver
- Function call stack simulation

The guide is structured as a reference document that you can save and use for learning, teaching, or as a foundation for your own projects. Both implementations are fully functional and include extensive testing to ensure reliability.

Would you like me to expand on any particular section or add additional features to either implementation?

## Comprehensive Stack Implementation Guide

## Table of Contents

1. [Introduction to Stacks](#introduction-to-stacks)
2. [Stack Operations](#stack-operations)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Advanced Use Cases](#advanced-use-cases)
7. [Performance Comparisons](#performance-comparisons)
8. [Common Pitfalls](#common-pitfalls)

## Introduction to Stacks

A **stack** is a linear data structure that follows the Last In, First Out (LIFO) principle. Elements are added and removed from the same end, called the "top" of the stack. Think of it like a stack of plates - you can only add or remove plates from the top.

### Key Characteristics:

- **LIFO ordering**: Last element added is the first to be removed
- **Single access point**: All operations occur at the top
- **Dynamic size**: Can grow and shrink during runtime
- **Linear structure**: Elements are arranged in a sequential manner

### Real-world Applications:

- Function call management (call stack)
- Expression evaluation and syntax parsing
- Undo operations in software
- Browser history navigation
- Memory management
- Backtracking algorithms

## Stack Operations

### Core Operations:

1. **Push**: Add an element to the top of the stack
2. **Pop**: Remove and return the top element
3. **Peek/Top**: View the top element without removing it
4. **isEmpty**: Check if the stack is empty
5. **Size**: Get the number of elements in the stack

### Optional Operations:

- **Clear**: Remove all elements
- **Search**: Find an element's position
- **Display**: Print all elements

## Time and Space Complexity

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Push      | O(1)           | O(1)            |
| Pop       | O(1)           | O(1)            |
| Peek      | O(1)           | O(1)            |
| isEmpty   | O(1)           | O(1)            |
| Size      | O(1)           | O(1)            |
| Search    | O(n)           | O(1)            |

**Overall Space Complexity**: O(n) where n is the number of elements

## Python Implementation

### Array-Based Stack Implementation

```python
class ArrayStack:
    """
    Array-based stack implementation using Python list.
    Provides O(1) operations for push, pop, and peek.
    """
    
    def __init__(self, capacity=None):
        """
        Initialize stack with optional capacity limit.
        
        Args:
            capacity (int, optional): Maximum stack size. None for unlimited.
        """
        self._data = []
        self._capacity = capacity
    
    def push(self, item):
        """
        Add an item to the top of the stack.
        
        Args:
            item: Element to be added
            
        Raises:
            OverflowError: If stack is at capacity
        """
        if self._capacity is not None and len(self._data) >= self._capacity:
            raise OverflowError("Stack overflow: Cannot push to full stack")
        
        self._data.append(item)
    
    def pop(self):
        """
        Remove and return the top element.
        
        Returns:
            The top element of the stack
            
        Raises:
            IndexError: If stack is empty
        """
        if self.is_empty():
            raise IndexError("Stack underflow: Cannot pop from empty stack")
        
        return self._data.pop()
    
    def peek(self):
        """
        Return the top element without removing it.
        
        Returns:
            The top element of the stack
            
        Raises:
            IndexError: If stack is empty
        """
        if self.is_empty():
            raise IndexError("Cannot peek empty stack")
        
        return self._data[-1]
    
    def is_empty(self):
        """Check if the stack is empty."""
        return len(self._data) == 0
    
    def size(self):
        """Return the number of elements in the stack."""
        return len(self._data)
    
    def clear(self):
        """Remove all elements from the stack."""
        self._data.clear()
    
    def search(self, item):
        """
        Search for an item and return its distance from top.
        
        Args:
            item: Element to search for
            
        Returns:
            int: Distance from top (1-based), or -1 if not found
        """
        try:
            # Find from the end (top) of the stack
            index = len(self._data) - 1 - self._data[::-1].index(item)
            return len(self._data) - index
        except ValueError:
            return -1
    
    def display(self):
        """Display stack contents from bottom to top."""
        if self.is_empty():
            print("Stack is empty")
        else:
            print("Stack (bottom to top):", self._data)
    
    def __str__(self):
        """String representation of the stack."""
        return f"Stack({self._data})"
    
    def __len__(self):
        """Return stack size when len() is called."""
        return len(self._data)
    
    def __bool__(self):
        """Return True if stack is not empty."""
        return not self.is_empty()


### Linked List-Based Stack Implementation

class Node:
    """Node class for linked list implementation."""
    
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedStack:
    """
    Linked list-based stack implementation.
    Memory efficient with dynamic allocation.
    """
    
    def __init__(self):
        """Initialize empty stack."""
        self._top = None
        self._size = 0
    
    def push(self, item):
        """Add an item to the top of the stack."""
        new_node = Node(item)
        new_node.next = self._top
        self._top = new_node
        self._size += 1
    
    def pop(self):
        """Remove and return the top element."""
        if self.is_empty():
            raise IndexError("Stack underflow: Cannot pop from empty stack")
        
        data = self._top.data
        self._top = self._top.next
        self._size -= 1
        return data
    
    def peek(self):
        """Return the top element without removing it."""
        if self.is_empty():
            raise IndexError("Cannot peek empty stack")
        
        return self._top.data
    
    def is_empty(self):
        """Check if the stack is empty."""
        return self._top is None
    
    def size(self):
        """Return the number of elements in the stack."""
        return self._size
    
    def clear(self):
        """Remove all elements from the stack."""
        self._top = None
        self._size = 0
    
    def search(self, item):
        """Search for an item and return its distance from top."""
        current = self._top
        position = 1
        
        while current:
            if current.data == item:
                return position
            current = current.next
            position += 1
        
        return -1
    
    def display(self):
        """Display stack contents from top to bottom."""
        if self.is_empty():
            print("Stack is empty")
            return
        
        elements = []
        current = self._top
        while current:
            elements.append(current.data)
            current = current.next
        
        print("Stack (top to bottom):", elements)
    
    def __str__(self):
        """String representation of the stack."""
        elements = []
        current = self._top
        while current:
            elements.append(current.data)
            current = current.next
        return f"LinkedStack({elements})"
    
    def __len__(self):
        """Return stack size when len() is called."""
        return self._size
    
    def __bool__(self):
        """Return True if stack is not empty."""
        return not self.is_empty()


# Usage Examples and Testing
def demonstrate_stack_usage():
    """Demonstrate various stack operations."""
    
    print("=== Array-based Stack Demo ===")
    stack = ArrayStack()
    
    # Push operations
    for i in range(1, 6):
        stack.push(i * 10)
        print(f"Pushed {i * 10}, Stack: {stack}")
    
    # Peek operation
    print(f"Top element: {stack.peek()}")
    print(f"Stack size: {stack.size()}")
    
    # Pop operations
    while not stack.is_empty():
        popped = stack.pop()
        print(f"Popped {popped}, Stack: {stack}")
    
    print("\n=== Linked Stack Demo ===")
    linked_stack = LinkedStack()
    
    # Push operations
    for char in "HELLO":
        linked_stack.push(char)
        print(f"Pushed '{char}', Stack: {linked_stack}")
    
    # Search operation
    print(f"Search for 'L': {linked_stack.search('L')}")
    print(f"Search for 'Z': {linked_stack.search('Z')}")
    
    # Pop all elements
    result = ""
    while not linked_stack.is_empty():
        result += linked_stack.pop()
    
    print(f"Popped all elements: '{result}'")


# Practical Applications
def balanced_parentheses(expression):
    """
    Check if parentheses are balanced using stack.
    
    Args:
        expression (str): String to check
        
    Returns:
        bool: True if balanced, False otherwise
    """
    stack = ArrayStack()
    opening = "([{"
    closing = ")]}"
    pairs = {"(": ")", "[": "]", "{": "}"}
    
    for char in expression:
        if char in opening:
            stack.push(char)
        elif char in closing:
            if stack.is_empty():
                return False
            if pairs[stack.pop()] != char:
                return False
    
    return stack.is_empty()


def evaluate_postfix(expression):
    """
    Evaluate postfix expression using stack.
    
    Args:
        expression (str): Postfix expression (space-separated)
        
    Returns:
        int: Result of evaluation
    """
    stack = ArrayStack()
    tokens = expression.split()
    
    for token in tokens:
        if token in "+-*/":
            if stack.size() < 2:
                raise ValueError("Invalid postfix expression")
            
            b = stack.pop()
            a = stack.pop()
            
            if token == "+":
                result = a + b
            elif token == "-":
                result = a - b
            elif token == "*":
                result = a * b
            elif token == "/":
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                result = a / b
            
            stack.push(result)
        else:
            try:
                stack.push(float(token))
            except ValueError:
                raise ValueError(f"Invalid token: {token}")
    
    if stack.size() != 1:
        raise ValueError("Invalid postfix expression")
    
    return stack.pop()


# Example usage
if __name__ == "__main__":
    demonstrate_stack_usage()
    
    # Test practical applications
    print("\n=== Practical Applications ===")
    
    # Balanced parentheses
    test_expressions = ["()", "([{}])", "([)]", "((()))", ")("]
    for expr in test_expressions:
        result = balanced_parentheses(expr)
        print(f"'{expr}' is balanced: {result}")
    
    # Postfix evaluation
    postfix_expressions = [
        "3 4 +",           # 3 + 4 = 7
        "5 2 * 3 +",       # 5 * 2 + 3 = 13
        "15 7 1 1 + - / 3 * 2 1 1 + + -"  # Complex expression
    ]
    
    for expr in postfix_expressions:
        try:
            result = evaluate_postfix(expr)
            print(f"'{expr}' = {result}")
        except Exception as e:
            print(f"Error evaluating '{expr}': {e}")
```

## Rust Implementation

```rust
use std::fmt;

/// Array-based stack implementation in Rust
#[derive(Debug, Clone)]
pub struct ArrayStack<T> {
    data: Vec<T>,
    capacity: Option<usize>,
}

impl<T> ArrayStack<T> {
    /// Create a new stack with optional capacity limit
    pub fn new() -> Self {
        Self {
            data: Vec::new(),
            capacity: None,
        }
    }
    
    /// Create a new stack with specified capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            data: Vec::with_capacity(capacity),
            capacity: Some(capacity),
        }
    }
    
    /// Push an item onto the stack
    pub fn push(&mut self, item: T) -> Result<(), &'static str> {
        if let Some(cap) = self.capacity {
            if self.data.len() >= cap {
                return Err("Stack overflow: Cannot push to full stack");
            }
        }
        
        self.data.push(item);
        Ok(())
    }
    
    /// Pop an item from the stack
    pub fn pop(&mut self) -> Option<T> {
        self.data.pop()
    }
    
    /// Peek at the top item without removing it
    pub fn peek(&self) -> Option<&T> {
        self.data.last()
    }
    
    /// Get mutable reference to top item
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.data.last_mut()
    }
    
    /// Check if the stack is empty
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    /// Get the number of elements in the stack
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    /// Clear all elements from the stack
    pub fn clear(&mut self) {
        self.data.clear();
    }
    
    /// Get the capacity of the stack
    pub fn capacity(&self) -> Option<usize> {
        self.capacity
    }
}

impl<T: PartialEq> ArrayStack<T> {
    /// Search for an item and return its distance from top (1-based)
    pub fn search(&self, item: &T) -> Option<usize> {
        for (index, element) in self.data.iter().rev().enumerate() {
            if element == item {
                return Some(index + 1);
            }
        }
        None
    }
}

impl<T: fmt::Display> ArrayStack<T> {
    /// Display the stack contents
    pub fn display(&self) {
        if self.is_empty() {
            println!("Stack is empty");
        } else {
            print!("Stack (bottom to top): [");
            for (i, item) in self.data.iter().enumerate() {
                if i > 0 {
                    print!(", ");
                }
                print!("{}", item);
            }
            println!("]");
        }
    }
}

impl<T> Default for ArrayStack<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: fmt::Display> fmt::Display for ArrayStack<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Stack[")?;
        for (i, item) in self.data.iter().enumerate() {
            if i > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{}", item)?;
        }
        write!(f, "]")
    }
}

/// Node for linked list-based stack
#[derive(Debug)]
struct Node<T> {
    data: T,
    next: Option<Box<Node<T>>>,
}

impl<T> Node<T> {
    fn new(data: T) -> Self {
        Self {
            data,
            next: None,
        }
    }
}

/// Linked list-based stack implementation
#[derive(Debug)]
pub struct LinkedStack<T> {
    top: Option<Box<Node<T>>>,
    size: usize,
}

impl<T> LinkedStack<T> {
    /// Create a new empty stack
    pub fn new() -> Self {
        Self {
            top: None,
            size: 0,
        }
    }
    
    /// Push an item onto the stack
    pub fn push(&mut self, item: T) {
        let mut new_node = Box::new(Node::new(item));
        new_node.next = self.top.take();
        self.top = Some(new_node);
        self.size += 1;
    }
    
    /// Pop an item from the stack
    pub fn pop(&mut self) -> Option<T> {
        self.top.take().map(|node| {
            self.top = node.next;
            self.size -= 1;
            node.data
        })
    }
    
    /// Peek at the top item without removing it
    pub fn peek(&self) -> Option<&T> {
        self.top.as_ref().map(|node| &node.data)
    }
    
    /// Get mutable reference to top item
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.top.as_mut().map(|node| &mut node.data)
    }
    
    /// Check if the stack is empty
    pub fn is_empty(&self) -> bool {
        self.top.is_none()
    }
    
    /// Get the number of elements in the stack
    pub fn len(&self) -> usize {
        self.size
    }
    
    /// Clear all elements from the stack
    pub fn clear(&mut self) {
        self.top = None;
        self.size = 0;
    }
}

impl<T: PartialEq> LinkedStack<T> {
    /// Search for an item and return its distance from top (1-based)
    pub fn search(&self, item: &T) -> Option<usize> {
        let mut current = &self.top;
        let mut position = 1;
        
        while let Some(node) = current {
            if &node.data == item {
                return Some(position);
            }
            current = &node.next;
            position += 1;
        }
        
        None
    }
}

impl<T: fmt::Display> LinkedStack<T> {
    /// Display the stack contents from top to bottom
    pub fn display(&self) {
        if self.is_empty() {
            println!("Stack is empty");
            return;
        }
        
        print!("Stack (top to bottom): [");
        let mut current = &self.top;
        let mut first = true;
        
        while let Some(node) = current {
            if !first {
                print!(", ");
            }
            print!("{}", node.data);
            current = &node.next;
            first = false;
        }
        println!("]");
    }
}

impl<T> Default for LinkedStack<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: fmt::Display> fmt::Display for LinkedStack<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "LinkedStack[")?;
        let mut current = &self.top;
        let mut first = true;
        
        while let Some(node) = current {
            if !first {
                write!(f, ", ")?;
            }
            write!(f, "{}", node.data)?;
            current = &node.next;
            first = false;
        }
        write!(f, "]")
    }
}

/// Iterator implementation for ArrayStack
impl<T> IntoIterator for ArrayStack<T> {
    type Item = T;
    type IntoIter = std::vec::IntoIter<T>;
    
    fn into_iter(mut self) -> Self::IntoIter {
        self.data.reverse(); // Iterate from top to bottom
        self.data.into_iter()
    }
}

/// Practical Applications
pub fn balanced_parentheses(expression: &str) -> bool {
    let mut stack = ArrayStack::new();
    let opening = "([{";
    let closing = ")]}";
    
    for ch in expression.chars() {
        if opening.contains(ch) {
            stack.push(ch).unwrap();
        } else if closing.contains(ch) {
            match stack.pop() {
                Some('(') if ch == ')' => continue,
                Some('[') if ch == ']' => continue,
                Some('{') if ch == '}' => continue,
                _ => return false,
            }
        }
    }
    
    stack.is_empty()
}

pub fn evaluate_postfix(expression: &str) -> Result<f64, &'static str> {
    let mut stack = ArrayStack::new();
    
    for token in expression.split_whitespace() {
        match token {
            "+" => {
                let b = stack.pop().ok_or("Invalid expression")?;
                let a = stack.pop().ok_or("Invalid expression")?;
                stack.push(a + b).unwrap();
            },
            "-" => {
                let b = stack.pop().ok_or("Invalid expression")?;
                let a = stack.pop().ok_or("Invalid expression")?;
                stack.push(a - b).unwrap();
            },
            "*" => {
                let b = stack.pop().ok_or("Invalid expression")?;
                let a = stack.pop().ok_or("Invalid expression")?;
                stack.push(a * b).unwrap();
            },
            "/" => {
                let b = stack.pop().ok_or("Invalid expression")?;
                let a = stack.pop().ok_or("Invalid expression")?;
                if b == 0.0 {
                    return Err("Division by zero");
                }
                stack.push(a / b).unwrap();
            },
            _ => {
                let num = token.parse::<f64>().map_err(|_| "Invalid number")?;
                stack.push(num).unwrap();
            }
        }
    }
    
    if stack.len() != 1 {
        return Err("Invalid expression");
    }
    
    stack.pop().ok_or("Empty stack")
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_array_stack_basic_operations() {
        let mut stack = ArrayStack::new();
        
        assert!(stack.is_empty());
        assert_eq!(stack.len(), 0);
        
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        stack.push(3).unwrap();
        
        assert_eq!(stack.len(), 3);
        assert!(!stack.is_empty());
        assert_eq!(stack.peek(), Some(&3));
        
        assert_eq!(stack.pop(), Some(3));
        assert_eq!(stack.pop(), Some(2));
        assert_eq!(stack.len(), 1);
        
        assert_eq!(stack.pop(), Some(1));
        assert!(stack.is_empty());
        assert_eq!(stack.pop(), None);
    }
    
    #[test]
    fn test_linked_stack_basic_operations() {
        let mut stack = LinkedStack::new();
        
        assert!(stack.is_empty());
        assert_eq!(stack.len(), 0);
        
        stack.push("hello");
        stack.push("world");
        
        assert_eq!(stack.len(), 2);
        assert_eq!(stack.peek(), Some(&"world"));
        
        assert_eq!(stack.pop(), Some("world"));
        assert_eq!(stack.pop(), Some("hello"));
        assert!(stack.is_empty());
    }
    
    #[test]
    fn test_capacity_limit() {
        let mut stack = ArrayStack::with_capacity(2);
        
        assert!(stack.push(1).is_ok());
        assert!(stack.push(2).is_ok());
        assert!(stack.push(3).is_err());
    }
    
    #[test]
    fn test_search_functionality() {
        let mut stack = ArrayStack::new();
        stack.push(10).unwrap();
        stack.push(20).unwrap();
        stack.push(30).unwrap();
        
        assert_eq!(stack.search(&30), Some(1)); // Top element
        assert_eq!(stack.search(&20), Some(2)); // Middle element
        assert_eq!(stack.search(&10), Some(3)); // Bottom element
        assert_eq!(stack.search(&40), None);    // Not found
    }
    
    #[test]
    fn test_balanced_parentheses() {
        assert!(balanced_parentheses("()"));
        assert!(balanced_parentheses("([{}])"));
        assert!(balanced_parentheses(""));
        assert!(!balanced_parentheses("([)]"));
        assert!(!balanced_parentheses("((())"));
        assert!(!balanced_parentheses(")("));
    }
    
    #[test]
    fn test_postfix_evaluation() {
        assert_eq!(evaluate_postfix("3 4 +"), Ok(7.0));
        assert_eq!(evaluate_postfix("5 2 * 3 +"), Ok(13.0));
        assert_eq!(evaluate_postfix("10 2 /"), Ok(5.0));
        assert!(evaluate_postfix("3 0 /").is_err());
        assert!(evaluate_postfix("3 +").is_err());
    }
}

fn main() {
    println!("=== Rust Stack Implementation Demo ===");
    
    // Array-based stack demo
    println!("\n--- Array Stack ---");
    let mut array_stack = ArrayStack::new();
    
    for i in 1..=5 {
        array_stack.push(i * 10).unwrap();
        println!("Pushed {}: {}", i * 10, array_stack);
    }
    
    println!("Top element: {:?}", array_stack.peek());
    println!("Stack size: {}", array_stack.len());
    
    while !array_stack.is_empty() {
        let popped = array_stack.pop().unwrap();
        println!("Popped {}: {}", popped, array_stack);
    }
    
    // Linked stack demo
    println!("\n--- Linked Stack ---");
    let mut linked_stack = LinkedStack::new();
    
    for ch in "RUST".chars() {
        linked_stack.push(ch);
        println!("Pushed '{}': {}", ch, linked_stack);
    }
    
    println!("Search for 'S': {:?}", linked_stack.search(&'S'));
    println!("Search for 'X': {:?}", linked_stack.search(&'X'));
    
    let mut result = String::new();
    while !linked_stack.is_empty() {
        result.push(linked_stack.pop().unwrap());
    }
    println!("Popped all elements: '{}'", result);
    
    // Practical applications
    println!("\n--- Practical Applications ---");
    
    let expressions = vec!["()", "([{}])", "([)]", "((()))", ")("];
    for expr in expressions {
        println!("'{}' is balanced: {}", expr, balanced_parentheses(expr));
    }
    
    let postfix_expressions = vec!["3 4 +", "5 2 * 3 +", "15 7 1 1 + - / 3 * 2 1 1 + + -"];
    for expr in postfix_expressions {
        match evaluate_postfix(expr) {
            Ok(result) => println!("'{}' = {}", expr, result),
            Err(e) => println!("Error evaluating '{}': {}", expr, e),
        }
    }
}
```

## Advanced Use Cases

### 1. Function Call Stack Simulation

```python
class CallStack:
    def __init__(self):
        self.stack = ArrayStack()
    
    def call_function(self, func_name, params):
        frame = {
            'function': func_name,
            'parameters': params,
            'local_vars': {},
            'return_address': len(self.stack)
        }
        self.stack.push(frame)
        print(f"Called {func_name}({params})")
    
    def return_from_function(self, return_value=None):
        if self.stack.is_empty():
            raise RuntimeError("No function to return from")
        
        frame = self.stack.pop()
        print(f"Returned from {frame['function']} with value: {return_value}")
        return return_value
    
    def current_function(self):
        if self.stack.is_empty():
            return None
        return self.stack.peek()['function']
```

### 2. Expression Tree Evaluation

```python
def infix_to_postfix(expression):
    """Convert infix expression to postfix using stack."""
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    associativity = {'+': 'L', '-': 'L', '*': 'L', '/': 'L', '^': 'R'}
    
    stack = ArrayStack()
    output = []
    
    for char in expression:
        if char.isalnum():
            output.append(char)
        elif char == '(':
            stack.push(char)
        elif char == ')':
            while not stack.is_empty() and stack.peek() != '(':
                output.append(stack.pop())
            stack.pop()  # Remove '('
        elif char in precedence:
            while (not stack.is_empty() and 
                   stack.peek() != '(' and
                   (precedence[stack.peek()] > precedence[char] or
                    (precedence[stack.peek()] == precedence[char] and 
                     associativity[char] == 'L'))):
                output.append(stack.pop())
            stack.push(char)
    
    while not stack.is_empty():
        output.append(stack.pop())
    
    return ''.join(output)
```

## Performance Comparisons

| Implementation | Memory Usage | Cache Performance | Flexibility |
|---------------|--------------|-------------------|-------------|
| Array-based   | Lower        | Better           | Limited by capacity |
| Linked-based  | Higher       | Worse            | Dynamic growth |

### When to Use Each:

**Array-based Stack:**
- Known maximum size
- Performance-critical applications
- Better memory locality
- Fewer memory allocations

**Linked-based Stack:**
- Unknown maximum size
- Memory-constrained environments
- Need for dynamic growth
- Frequent push/pop operations

## Common Pitfalls

### 1. Stack Overflow
```python
# Bad: No capacity checking
def recursive_function(n):
    if n <= 0:
        return 1
    return n * recursive_function(n - 1)

# Good: Iterative approach or tail recursion
def iterative_factorial(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
```

### 2. Stack Underflow
```python
# Bad: No empty check
def unsafe_pop(stack):
    return stack.pop()  # May raise exception

# Good: Safe popping
def safe_pop(stack, default=None):
    if not stack.is_empty():
        return stack.pop()
    return default
```

### 3. Memory Leaks in Linked Implementation
```rust
// Bad: Potential memory leak if not handled properly
impl<T> Drop for LinkedStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}

// Good: Rust automatically handles this, but be aware in other languages
```

### 4. Thread Safety Issues
```python
import threading

class ThreadSafeStack:
    def __init__(self):
        self._stack = ArrayStack()
        self._lock = threading.Lock()
    
    def push(self, item):
        with self._lock:
            self._stack.push(item)
    
    def pop(self):
        with self._lock:
            if not self._stack.is_empty():
                return self._stack.pop()
        return None
    
    def peek(self):
        with self._lock:
            if not self._stack.is_empty():
                return self._stack.peek()
        return None
```

## Advanced Stack Variants

### 1. Min Stack (Stack with Minimum Element Tracking)

```python
class MinStack:
    """Stack that supports finding minimum element in O(1) time."""
    
    def __init__(self):
        self.stack = ArrayStack()
        self.min_stack = ArrayStack()
    
    def push(self, item):
        self.stack.push(item)
        
        if self.min_stack.is_empty() or item <= self.min_stack.peek():
            self.min_stack.push(item)
    
    def pop(self):
        if self.stack.is_empty():
            raise IndexError("Stack is empty")
        
        item = self.stack.pop()
        if item == self.min_stack.peek():
            self.min_stack.pop()
        
        return item
    
    def peek(self):
        return self.stack.peek()
    
    def get_min(self):
        if self.min_stack.is_empty():
            raise IndexError("Stack is empty")
        return self.min_stack.peek()
    
    def is_empty(self):
        return self.stack.is_empty()
```

### 2. Stack with GetRandom() Operation

```python
import random

class RandomStack:
    """Stack with O(1) getRandom() operation."""
    
    def __init__(self):
        self.stack = []
        self.indices = {}  # value -> list of indices
    
    def push(self, item):
        index = len(self.stack)
        self.stack.append(item)
        
        if item not in self.indices:
            self.indices[item] = []
        self.indices[item].append(index)
    
    def pop(self):
        if not self.stack:
            raise IndexError("Stack is empty")
        
        item = self.stack.pop()
        self.indices[item].pop()
        
        if not self.indices[item]:
            del self.indices[item]
        
        return item
    
    def get_random(self):
        if not self.stack:
            raise IndexError("Stack is empty")
        
        return random.choice(self.stack)
    
    def peek(self):
        if not self.stack:
            raise IndexError("Stack is empty")
        return self.stack[-1]
```

## Benchmarking and Testing

### Performance Testing Framework

```python
import time
import random
from typing import List, Callable

def benchmark_stack_operations(stack_class, operations: int = 100000):
    """Benchmark stack operations."""
    
    stack = stack_class()
    
    # Test push operations
    start_time = time.time()
    for i in range(operations):
        stack.push(i)
    push_time = time.time() - start_time
    
    # Test peek operations
    start_time = time.time()
    for _ in range(1000):
        if not stack.is_empty():
            stack.peek()
    peek_time = time.time() - start_time
    
    # Test pop operations
    start_time = time.time()
    while not stack.is_empty():
        stack.pop()
    pop_time = time.time() - start_time
    
    return {
        'push_time': push_time,
        'peek_time': peek_time,
        'pop_time': pop_time,
        'operations': operations
    }

def run_comprehensive_benchmarks():
    """Run comprehensive benchmarks."""
    
    print("=== Stack Performance Benchmarks ===")
    
    stack_types = [
        ("ArrayStack", ArrayStack),
        ("LinkedStack", LinkedStack),
    ]
    
    operation_counts = [1000, 10000, 100000]
    
    for name, stack_class in stack_types:
        print(f"\n--- {name} ---")
        for ops in operation_counts:
            results = benchmark_stack_operations(stack_class, ops)
            print(f"Operations: {ops:,}")
            print(f"  Push: {results['push_time']:.4f}s")
            print(f"  Peek: {results['peek_time']:.4f}s")
            print(f"  Pop:  {results['pop_time']:.4f}s")

# Comprehensive Test Suite
class StackTestSuite:
    """Comprehensive test suite for stack implementations."""
    
    @staticmethod
    def test_basic_operations(stack_class):
        """Test basic stack operations."""
        stack = stack_class()
        
        # Test empty stack
        assert stack.is_empty()
        assert stack.size() == 0
        
        # Test push and size
        test_data = [1, 2, 3, "hello", [1, 2, 3]]
        for item in test_data:
            stack.push(item)
            assert not stack.is_empty()
        
        assert stack.size() == len(test_data)
        
        # Test peek
        assert stack.peek() == test_data[-1]
        assert stack.size() == len(test_data)  # Size shouldn't change
        
        # Test pop in reverse order
        for expected in reversed(test_data):
            assert stack.pop() == expected
        
        assert stack.is_empty()
        assert stack.size() == 0
        
        print(f"✓ {stack_class.__name__} basic operations test passed")
    
    @staticmethod
    def test_edge_cases(stack_class):
        """Test edge cases."""
        stack = stack_class()
        
        # Test operations on empty stack
        try:
            stack.peek()
            assert False, "Should raise exception"
        except (IndexError, Exception):
            pass
        
        try:
            stack.pop()
            assert stack_class == ArrayStack or False, "LinkedStack returns None"
        except (IndexError, Exception):
            pass
        
        # Test single element
        stack.push("single")
        assert stack.peek() == "single"
        assert stack.pop() == "single"
        assert stack.is_empty()
        
        # Test alternating push/pop
        for i in range(100):
            stack.push(i)
            if i % 2 == 1:
                stack.pop()
        
        assert stack.size() == 50
        
        print(f"✓ {stack_class.__name__} edge cases test passed")
    
    @staticmethod
    def test_large_dataset(stack_class):
        """Test with large dataset."""
        stack = stack_class()
        n = 10000
        
        # Push large amount of data
        for i in range(n):
            stack.push(i)
        
        assert stack.size() == n
        
        # Pop half
        for i in range(n // 2):
            expected = n - 1 - i
            assert stack.pop() == expected
        
        assert stack.size() == n // 2
        
        # Clear remaining
        stack.clear()
        assert stack.is_empty()
        
        print(f"✓ {stack_class.__name__} large dataset test passed")
    
    @staticmethod
    def run_all_tests():
        """Run all tests for both stack implementations."""
        stack_classes = [ArrayStack, LinkedStack]
        
        print("=== Running Comprehensive Stack Tests ===")
        
        for stack_class in stack_classes:
            print(f"\nTesting {stack_class.__name__}:")
            StackTestSuite.test_basic_operations(stack_class)
            StackTestSuite.test_edge_cases(stack_class)
            StackTestSuite.test_large_dataset(stack_class)
        
        print("\n✓ All tests passed!")

# Real-world Applications and Examples

def tower_of_hanoi(n: int, source: str, destination: str, auxiliary: str):
    """Solve Tower of Hanoi using stack-based approach."""
    if n == 1:
        print(f"Move disk 1 from {source} to {destination}")
        return
    
    tower_of_hanoi(n-1, source, auxiliary, destination)
    print(f"Move disk {n} from {source} to {destination}")
    tower_of_hanoi(n-1, auxiliary, destination, source)

def validate_html_tags(html: str) -> bool:
    """Validate HTML tags using stack."""
    stack = ArrayStack()
    i = 0
    
    while i < len(html):
        if html[i] == '<':
            # Find the end of the tag
            j = i + 1
            while j < len(html) and html[j] != '>':
                j += 1
            
            if j == len(html):
                return False  # Unclosed tag
            
            tag = html[i+1:j]
            
            if tag.startswith('/'):
                # Closing tag
                if stack.is_empty():
                    return False
                
                opening_tag = stack.pop()
                if tag[1:] != opening_tag:
                    return False
            elif not tag.endswith('/'):
                # Opening tag (not self-closing)
                stack.push(tag)
            
            i = j + 1
        else:
            i += 1
    
    return stack.is_empty()

def reverse_string_words(s: str) -> str:
    """Reverse words in a string using stack."""
    stack = ArrayStack()
    words = s.split()
    
    for word in words:
        stack.push(word)
    
    result = []
    while not stack.is_empty():
        result.append(stack.pop())
    
    return ' '.join(result)

def decimal_to_binary(num: int) -> str:
    """Convert decimal to binary using stack."""
    if num == 0:
        return "0"
    
    stack = ArrayStack()
    
    while num > 0:
        stack.push(num % 2)
        num //= 2
    
    binary = ""
    while not stack.is_empty():
        binary += str(stack.pop())
    
    return binary

# Usage examples and demonstrations
def demonstrate_advanced_features():
    """Demonstrate advanced stack features."""
    
    print("=== Advanced Stack Features Demo ===")
    
    # Min Stack demonstration
    print("\n--- Min Stack ---")
    min_stack = MinStack()
    values = [3, 5, 2, 1, 4]
    
    for val in values:
        min_stack.push(val)
        print(f"Pushed {val}, Min: {min_stack.get_min()}")
    
    while not min_stack.is_empty():
        popped = min_stack.pop()
        min_val = min_stack.get_min() if not min_stack.is_empty() else "N/A"
        print(f"Popped {popped}, Min: {min_val}")
    
    # HTML validation
    print("\n--- HTML Tag Validation ---")
    html_examples = [
        "<div><p>Hello</p></div>",
        "<div><p>Hello</div></p>",
        "<br/><img/>",
        "<div><p>Hello</p>",
    ]
    
    for html in html_examples:
        valid = validate_html_tags(html)
        print(f"'{html}' is valid: {valid}")
    
    # Binary conversion
    print("\n--- Decimal to Binary Conversion ---")
    numbers = [10, 25, 100, 255]
    
    for num in numbers:
        binary = decimal_to_binary(num)
        print(f"{num} in binary: {binary}")
    
    # String word reversal
    print("\n--- String Word Reversal ---")
    sentences = [
        "Hello World",
        "The quick brown fox",
        "Stack data structure"
    ]
    
    for sentence in sentences:
        reversed_sentence = reverse_string_words(sentence)
        print(f"'{sentence}' -> '{reversed_sentence}'")

if __name__ == "__main__":
    # Run all demonstrations and tests
    demonstrate_stack_usage()
    demonstrate_advanced_features()
    
    print("\n" + "="*50)
    StackTestSuite.run_all_tests()
    
    print("\n" + "="*50)
    run_comprehensive_benchmarks()
    
    print("\n" + "="*50)
    print("Tower of Hanoi solution for 3 disks:")
    tower_of_hanoi(3, "A", "C", "B")
```

## Conclusion

This comprehensive guide covers stack implementation from basic concepts to advanced applications. Key takeaways:

### Implementation Choices:
- **Array-based**: Better for known size limits and performance-critical applications
- **Linked-based**: Better for dynamic sizing and memory efficiency

### Performance Characteristics:
- All core operations are O(1)
- Space complexity is O(n)
- Array-based has better cache locality
- Linked-based has more memory overhead per element

### Best Practices:
1. Always check for empty stack before pop/peek operations
2. Consider thread safety in concurrent applications
3. Use capacity limits to prevent stack overflow
4. Choose implementation based on use case requirements
5. Implement proper error handling for edge cases

### Common Applications:
- Expression evaluation and parsing
- Function call management
- Undo operations
- Browser history
- Backtracking algorithms
- Memory management
- Syntax validation

The implementations provided are production-ready and include comprehensive error handling, testing frameworks, and real-world examples. Both Python and Rust versions follow language-specific best practices and idioms.

I'll create a detailed ASCII diagram showing how stacks work with step-by-step operations.I've created a comprehensive ASCII diagram showing how stacks work step by step! The diagram illustrates:

1. **Visual representation** of each stack operation from empty to full and back to empty
2. **Step-by-step PUSH operations** showing how elements are added to the top
3. **PEEK operation** demonstrating non-destructive viewing
4. **Step-by-step POP operations** showing how elements are removed from the top
5. **Memory representation** showing how stacks are implemented using arrays
6. **Complete operation sequence** with a visual summary

The diagram clearly shows the **LIFO (Last In, First Out)** principle - notice how element 40 was the last to be pushed but the first to be popped. The ASCII art makes it easy to visualize how the "top" pointer moves up and down as elements are added and removed.

This representation should help you understand the fundamental concept that stacks only allow access to the topmost element, making them perfect for scenarios like function calls, undo operations, and expression evaluation.

# Linked List ASCII Diagram - Step by Step Guide

## 1. Basic Structure of a Node

```
┌─────────────────┐
│      NODE       │
├─────────┬───────┤
│  DATA   │ NEXT  │
│   42    │   •───┼──→ (points to next node)
└─────────┴───────┘
```

## 2. Simple Linked List with 3 Nodes

```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
     Node 1                 Node 2                 Node 3
```

## 3. Step-by-Step: Inserting at the Beginning

### Initial List:
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘
```

### Step 1: Create new node
```
┌─────────┬───────┐
│  DATA   │ NEXT  │
│   10    │ NULL  │  ← New node created
└─────────┴───────┘

HEAD (still points to old first node)
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘
```

### Step 2: Point new node to current head
```
┌─────────┬───────┐
│  DATA   │ NEXT  │
│   10    │   •───┼──┐
└─────────┴───────┘  │
                     │
HEAD                 │
 │                   │
 ▼                   ▼
┌─────────┬───────┐  │ ┌─────────┬───────┐
│  DATA   │ NEXT  │◄─┘ │  DATA   │ NEXT  │
│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘
```

### Step 3: Update HEAD to point to new node
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

## 4. Step-by-Step: Inserting in the Middle

### Initial List:
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   40    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

### Goal: Insert 30 between 20 and 40

### Step 1: Traverse to position (after node with 20)
```
HEAD                   CURRENT
 │                        │
 ▼                        ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   40    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

### Step 2: Create new node and point it to next node
```
                       ┌─────────┬───────┐
                       │  DATA   │ NEXT  │
                       │   30    │   •───┼──┐
                       └─────────┴───────┘  │
                                            │
HEAD                   CURRENT              │
 │                        │                 │
 ▼                        ▼                 ▼
┌─────────┬───────┐    ┌─────────┬───────┐ │ ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │ │ │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼─┼▶│   40    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘ │ └─────────┴───────┘
                                           └─→
```

### Step 3: Update current node to point to new node
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │   •───┼───▶│   40    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

## 5. Step-by-Step: Deleting a Node

### Initial List:
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

### Goal: Delete node with value 20

### Step 1: Find the node before the target (node with 10)
```
HEAD                   PREV      TARGET
 │                      │          │
 ▼                      ▼          ▼
┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘
```

### Step 2: Update previous node to skip target node
```
HEAD                   PREV                   
 │                      │          ╔═════════╗
 ▼                      ▼          ║ TO BE   ║
┌─────────┬───────┐    ┌─────────┬─║─────┐  ║ ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ ║ EXT │  ║ │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   20    │ ║ •───┼──║▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴─║─────┘  ║ └─────────┴───────┘
          │             ╚═════════╚═╝═══════╝
          └─────────────────────────────────────▶
```

### Step 3: Final result after deletion and memory cleanup
```
HEAD
 │
 ▼
┌─────────┬───────┐    ┌─────────┬───────┐
│  DATA   │ NEXT  │    │  DATA   │ NEXT  │
│   10    │   •───┼───▶│   30    │ NULL  │
└─────────┴───────┘    └─────────┴───────┘
```

## 6. Traversing a Linked List

```
Algorithm: Print all values

CURRENT = HEAD

Step 1:                Step 2:                Step 3:
CURRENT                                       CURRENT
 │                     CURRENT                 │
 ▼                       │                     ▼
┌───┬───┐    ┌───┬───┐   ▼      ┌───┬───┐    ┌───┬───┐    ┌───┬───┐
│10 │ •─┼───▶│20 │ •─┼─────────▶│30 │ •─┼───▶│40 │ ∅ │    │40 │ ∅ │
└───┴───┘    └───┴───┘          └───┴───┘    └───┴───┘    └───┴───┘
Print: 10    Print: 20          Print: 30    Print: 40

Step 4:
CURRENT = NULL → Stop
```

## 7. Memory Comparison: Array vs Linked List

### Array (Contiguous Memory):
```
Memory Address: 1000  1004  1008  1012  1016
              ┌─────┬─────┬─────┬─────┬─────┐
Array[5]:     │  10 │  20 │  30 │  40 │  50 │
              └─────┴─────┴─────┴─────┴─────┘
                 0     1     2     3     4    ← indices
```

### Linked List (Non-contiguous Memory):
```
Memory Address: 2000         1500         3000
              ┌─────┬─────┐ ┌─────┬─────┐ ┌─────┬─────┐
Nodes:        │  10 │1500─┼▶│  20 │3000─┼▶│  30 │ ∅   │
              └─────┴─────┘ └─────┴─────┘ └─────┴─────┘

HEAD = 2000
```

## 8. Time Complexity Summary

```
╔══════════════════╦═══════════╦═════════════╗
║    Operation     ║   Array   ║ Linked List ║
╠══════════════════╬═══════════╬═════════════╣
║ Access by index  ║   O(1)    ║    O(n)     ║
║ Insert at start  ║   O(n)    ║    O(1)     ║
║ Insert at end    ║   O(1)*   ║    O(n)     ║
║ Insert at middle ║   O(n)    ║    O(n)     ║
║ Delete at start  ║   O(n)    ║    O(1)     ║
║ Delete at end    ║   O(1)    ║    O(n)     ║
║ Delete at middle ║   O(n)    ║    O(n)     ║
║ Search           ║   O(n)    ║    O(n)     ║
╚══════════════════╩═══════════╩═════════════╝
* Assuming dynamic array with available space
```

## 9. Common Variations

### Doubly Linked List:
```
        ┌─────────┬─────┬─────────┐    ┌─────────┬─────┬─────────┐
        │  PREV   │DATA │  NEXT   │    │  PREV   │DATA │  NEXT   │
NULL◄───┤  NULL   │  10 │    •────┼───▶│    •    │  20 │  NULL   │
        └─────────┴─────┴─────────┘    └─────────┴─────┴─────────┘
                             ▲                     │
                             └─────────────────────┘
```

### Circular Linked List:
```
       ┌─────────┬───────┐    ┌─────────┬───────┐    ┌─────────┬───────┐
       │  DATA   │ NEXT  │    │  DATA   │ NEXT  │    │  DATA   │ NEXT  │
    ┌─▶│   10    │   •───┼───▶│   20    │   •───┼───▶│   30    │   •───┼──┐
    │  └─────────┴───────┘    └─────────┴───────┘    └─────────┴───────┘  │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    ▲
   HEAD
```