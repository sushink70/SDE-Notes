# Complete Guide to Runtime Analysis in Data Structures and Algorithms

## Table of Contents
1. [Introduction to Runtime Analysis](#introduction)
2. [Big O Notation Fundamentals](#big-o-fundamentals)
3. [Common Time Complexities](#common-complexities)
4. [Space Complexity Analysis](#space-complexity)
5. [Array Operations Analysis](#array-operations)
6. [Linked List Operations Analysis](#linked-list-operations)
7. [Stack and Queue Operations Analysis](#stack-queue-operations)
8. [Tree Operations Analysis](#tree-operations)
9. [Graph Algorithms Analysis](#graph-algorithms)
10. [Sorting Algorithms Analysis](#sorting-algorithms)
11. [Searching Algorithms Analysis](#searching-algorithms)
12. [Dynamic Programming Analysis](#dynamic-programming)
13. [Practical Benchmarking](#practical-benchmarking)

## 1. Introduction to Runtime Analysis {#introduction}

Runtime analysis is the process of determining how the execution time and memory usage of an algorithm scales with input size. It helps us:

- Compare algorithm efficiency
- Predict performance for large inputs
- Choose optimal algorithms for specific constraints
- Identify bottlenecks in code

### Key Concepts

**Time Complexity**: How execution time grows with input size
**Space Complexity**: How memory usage grows with input size
**Best Case**: Minimum time/space required
**Average Case**: Expected time/space for typical inputs
**Worst Case**: Maximum time/space required

## 2. Big O Notation Fundamentals {#big-o-fundamentals}

Big O notation describes the upper bound of algorithm complexity, focusing on the dominant term as input size approaches infinity.

### Common Big O Classes

| Notation | Name | Example |
|----------|------|---------|
| O(1) | Constant | Array access |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Linear search |
| O(n log n) | Linearithmic | Merge sort |
| O(n²) | Quadratic | Bubble sort |
| O(n³) | Cubic | Triple nested loops |
| O(2ⁿ) | Exponential | Recursive Fibonacci |
| O(n!) | Factorial | Traveling salesman (brute force) |

### Rules for Big O Analysis

1. **Drop constants**: O(2n) → O(n)
2. **Drop non-dominant terms**: O(n² + n) → O(n²)
3. **Consider worst case** unless specified otherwise
4. **Different inputs use different variables**: O(a + b), not O(n)

## 3. Common Time Complexities {#common-complexities}

### O(1) - Constant Time
```python
def get_first_element(arr):
    return arr[0] if arr else None
```

### O(log n) - Logarithmic Time
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

### O(n) - Linear Time
```python
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
```

### O(n log n) - Linearithmic Time
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)
```

### O(n²) - Quadratic Time
```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
```

## 4. Space Complexity Analysis {#space-complexity}

Space complexity measures additional memory used by an algorithm, excluding input storage.

### Types of Space Usage

1. **Auxiliary Space**: Extra space used by algorithm
2. **Input Space**: Space required to store input
3. **Total Space**: Auxiliary + Input space

### Examples

```python
# O(1) space - iterative factorial
def factorial_iterative(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

# O(n) space - recursive factorial
def factorial_recursive(n):
    if n <= 1:
        return 1
    return n * factorial_recursive(n - 1)
```

## 5. Array Operations Analysis {#array-operations}

### Python Implementation

```python
class DynamicArray:
    def __init__(self):
        self.capacity = 1
        self.size = 0
        self.data = [None] * self.capacity
    
    def get(self, index):
        """O(1) time, O(1) space"""
        if 0 <= index < self.size:
            return self.data[index]
        raise IndexError("Index out of bounds")
    
    def set(self, index, value):
        """O(1) time, O(1) space"""
        if 0 <= index < self.size:
            self.data[index] = value
        else:
            raise IndexError("Index out of bounds")
    
    def append(self, value):
        """Amortized O(1) time, O(1) space"""
        if self.size == self.capacity:
            self._resize()
        self.data[self.size] = value
        self.size += 1
    
    def insert(self, index, value):
        """O(n) time, O(1) space"""
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")
        
        if self.size == self.capacity:
            self._resize()
        
        # Shift elements to the right
        for i in range(self.size, index, -1):
            self.data[i] = self.data[i - 1]
        
        self.data[index] = value
        self.size += 1
    
    def delete(self, index):
        """O(n) time, O(1) space"""
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        # Shift elements to the left
        for i in range(index, self.size - 1):
            self.data[i] = self.data[i + 1]
        
        self.size -= 1
    
    def _resize(self):
        """O(n) time, O(n) space"""
        old_data = self.data
        self.capacity *= 2
        self.data = [None] * self.capacity
        
        for i in range(self.size):
            self.data[i] = old_data[i]

# Analysis demonstration
def analyze_array_operations():
    arr = DynamicArray()
    
    # O(1) operations
    print("Appending elements...")
    for i in range(5):
        arr.append(i)
    
    # O(1) access
    print(f"Element at index 2: {arr.get(2)}")
    
    # O(n) insertion
    arr.insert(2, 99)
    print("After insertion at index 2")
    
    # O(n) deletion
    arr.delete(1)
    print("After deletion at index 1")
```

### Rust Implementation

```rust
pub struct DynamicArray<T> {
    capacity: usize,
    size: usize,
    data: Vec<Option<T>>,
}

impl<T: Clone> DynamicArray<T> {
    pub fn new() -> Self {
        DynamicArray {
            capacity: 1,
            size: 0,
            data: vec![None; 1],
        }
    }
    
    /// O(1) time, O(1) space
    pub fn get(&self, index: usize) -> Result<&T, String> {
        if index < self.size {
            match &self.data[index] {
                Some(value) => Ok(value),
                None => Err("Empty slot".to_string()),
            }
        } else {
            Err("Index out of bounds".to_string())
        }
    }
    
    /// O(1) time, O(1) space
    pub fn set(&mut self, index: usize, value: T) -> Result<(), String> {
        if index < self.size {
            self.data[index] = Some(value);
            Ok(())
        } else {
            Err("Index out of bounds".to_string())
        }
    }
    
    /// Amortized O(1) time, O(1) space
    pub fn append(&mut self, value: T) {
        if self.size == self.capacity {
            self.resize();
        }
        self.data[self.size] = Some(value);
        self.size += 1;
    }
    
    /// O(n) time, O(1) space
    pub fn insert(&mut self, index: usize, value: T) -> Result<(), String> {
        if index > self.size {
            return Err("Index out of bounds".to_string());
        }
        
        if self.size == self.capacity {
            self.resize();
        }
        
        // Shift elements to the right
        for i in (index..self.size).rev() {
            self.data[i + 1] = self.data[i].clone();
        }
        
        self.data[index] = Some(value);
        self.size += 1;
        Ok(())
    }
    
    /// O(n) time, O(1) space
    pub fn delete(&mut self, index: usize) -> Result<T, String> {
        if index >= self.size {
            return Err("Index out of bounds".to_string());
        }
        
        let value = self.data[index].take().unwrap();
        
        // Shift elements to the left
        for i in index..self.size - 1 {
            self.data[i] = self.data[i + 1].clone();
        }
        
        self.size -= 1;
        Ok(value)
    }
    
    /// O(n) time, O(n) space
    fn resize(&mut self) {
        self.capacity *= 2;
        self.data.resize(self.capacity, None);
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
}
```

## 6. Linked List Operations Analysis {#linked-list-operations}

### Python Implementation

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0
    
    def prepend(self, val):
        """O(1) time, O(1) space"""
        new_node = ListNode(val)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
    
    def append(self, val):
        """O(n) time, O(1) space"""
        new_node = ListNode(val)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:  # O(n) traversal
                current = current.next
            current.next = new_node
        self.size += 1
    
    def insert(self, index, val):
        """O(n) time, O(1) space"""
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            self.prepend(val)
            return
        
        new_node = ListNode(val)
        current = self.head
        
        # Traverse to position index-1
        for _ in range(index - 1):
            current = current.next
        
        new_node.next = current.next
        current.next = new_node
        self.size += 1
    
    def delete(self, index):
        """O(n) time, O(1) space"""
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            deleted_val = self.head.val
            self.head = self.head.next
            self.size -= 1
            return deleted_val
        
        current = self.head
        # Traverse to position index-1
        for _ in range(index - 1):
            current = current.next
        
        deleted_val = current.next.val
        current.next = current.next.next
        self.size -= 1
        return deleted_val
    
    def search(self, val):
        """O(n) time, O(1) space"""
        current = self.head
        index = 0
        
        while current:
            if current.val == val:
                return index
            current = current.next
            index += 1
        
        return -1
    
    def reverse(self):
        """O(n) time, O(1) space"""
        prev = None
        current = self.head
        
        while current:
            next_temp = current.next
            current.next = prev
            prev = current
            current = next_temp
        
        self.head = prev
```

### Rust Implementation

```rust
use std::rc::Rc;
use std::cell::RefCell;

type NodeRef<T> = Rc<RefCell<Node<T>>>;

#[derive(Debug)]
struct Node<T> {
    val: T,
    next: Option<NodeRef<T>>,
}

impl<T> Node<T> {
    fn new(val: T) -> NodeRef<T> {
        Rc::new(RefCell::new(Node { val, next: None }))
    }
}

pub struct LinkedList<T> {
    head: Option<NodeRef<T>>,
    size: usize,
}

impl<T: Clone + PartialEq> LinkedList<T> {
    pub fn new() -> Self {
        LinkedList {
            head: None,
            size: 0,
        }
    }
    
    /// O(1) time, O(1) space
    pub fn prepend(&mut self, val: T) {
        let new_node = Node::new(val);
        new_node.borrow_mut().next = self.head.take();
        self.head = Some(new_node);
        self.size += 1;
    }
    
    /// O(n) time, O(1) space
    pub fn append(&mut self, val: T) {
        let new_node = Node::new(val);
        
        if self.head.is_none() {
            self.head = Some(new_node);
        } else {
            let mut current = self.head.as_ref().unwrap().clone();
            
            // Traverse to the end
            while current.borrow().next.is_some() {
                let next = current.borrow().next.as_ref().unwrap().clone();
                current = next;
            }
            
            current.borrow_mut().next = Some(new_node);
        }
        self.size += 1;
    }
    
    /// O(n) time, O(1) space
    pub fn insert(&mut self, index: usize, val: T) -> Result<(), String> {
        if index > self.size {
            return Err("Index out of bounds".to_string());
        }
        
        if index == 0 {
            self.prepend(val);
            return Ok(());
        }
        
        let new_node = Node::new(val);
        let mut current = self.head.as_ref().unwrap().clone();
        
        // Traverse to position index-1
        for _ in 0..index - 1 {
            let next = current.borrow().next.as_ref().unwrap().clone();
            current = next;
        }
        
        let next = current.borrow_mut().next.take();
        new_node.borrow_mut().next = next;
        current.borrow_mut().next = Some(new_node);
        self.size += 1;
        Ok(())
    }
    
    /// O(n) time, O(1) space
    pub fn delete(&mut self, index: usize) -> Result<T, String> {
        if index >= self.size {
            return Err("Index out of bounds".to_string());
        }
        
        if index == 0 {
            let head = self.head.take().unwrap();
            let val = head.borrow().val.clone();
            self.head = head.borrow_mut().next.take();
            self.size -= 1;
            return Ok(val);
        }
        
        let mut current = self.head.as_ref().unwrap().clone();
        
        // Traverse to position index-1
        for _ in 0..index - 1 {
            let next = current.borrow().next.as_ref().unwrap().clone();
            current = next;
        }
        
        let to_delete = current.borrow_mut().next.take().unwrap();
        let val = to_delete.borrow().val.clone();
        current.borrow_mut().next = to_delete.borrow_mut().next.take();
        self.size -= 1;
        Ok(val)
    }
    
    /// O(n) time, O(1) space
    pub fn search(&self, val: T) -> Option<usize> {
        let mut current = self.head.as_ref()?.clone();
        let mut index = 0;
        
        loop {
            if current.borrow().val == val {
                return Some(index);
            }
            
            match &current.borrow().next {
                Some(next) => {
                    current = next.clone();
                    index += 1;
                },
                None => break,
            }
        }
        
        None
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
}
```

## 7. Stack and Queue Operations Analysis {#stack-queue-operations}

### Stack Implementation

#### Python Stack

```python
class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """O(1) time, O(1) space"""
        self.items.append(item)
    
    def pop(self):
        """O(1) time, O(1) space"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        """O(1) time, O(1) space"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        """O(1) time, O(1) space"""
        return len(self.items) == 0
    
    def size(self):
        """O(1) time, O(1) space"""
        return len(self.items)

# Example: Balanced parentheses checker
def is_balanced(expression):
    """O(n) time, O(n) space"""
    stack = Stack()
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in expression:
        if char in mapping:  # Closing bracket
            if stack.is_empty() or stack.pop() != mapping[char]:
                return False
        elif char in mapping.values():  # Opening bracket
            stack.push(char)
    
    return stack.is_empty()
```

#### Rust Stack

```rust
pub struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Stack {
            items: Vec::new(),
        }
    }
    
    /// O(1) time, O(1) space
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    /// O(1) time, O(1) space
    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    /// O(1) time, O(1) space
    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    /// O(1) time, O(1) space
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    /// O(1) time, O(1) space
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Example: Balanced parentheses checker
pub fn is_balanced(expression: &str) -> bool {
    let mut stack = Stack::new();
    let mut mapping = std::collections::HashMap::new();
    mapping.insert(')', '(');
    mapping.insert('}', '{');
    mapping.insert(']', '[');
    
    for char in expression.chars() {
        if let Some(&expected) = mapping.get(&char) {
            // Closing bracket
            match stack.pop() {
                Some(top) if top == expected => continue,
                _ => return false,
            }
        } else if mapping.values().any(|&v| v == char) {
            // Opening bracket
            stack.push(char);
        }
    }
    
    stack.is_empty()
}
```

### Queue Implementation

#### Python Queue

```python
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        """O(1) time, O(1) space"""
        self.items.append(item)
    
    def dequeue(self):
        """O(1) time, O(1) space"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.popleft()
    
    def front(self):
        """O(1) time, O(1) space"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        """O(1) time, O(1) space"""
        return len(self.items) == 0
    
    def size(self):
        """O(1) time, O(1) space"""
        return len(self.items)

# Example: BFS implementation
def bfs_traversal(graph, start):
    """O(V + E) time, O(V) space"""
    visited = set()
    queue = Queue()
    result = []
    
    queue.enqueue(start)
    visited.add(start)
    
    while not queue.is_empty():
        vertex = queue.dequeue()
        result.append(vertex)
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.enqueue(neighbor)
    
    return result
```

#### Rust Queue

```rust
use std::collections::VecDeque;

pub struct Queue<T> {
    items: VecDeque<T>,
}

impl<T> Queue<T> {
    pub fn new() -> Self {
        Queue {
            items: VecDeque::new(),
        }
    }
    
    /// O(1) time, O(1) space
    pub fn enqueue(&mut self, item: T) {
        self.items.push_back(item);
    }
    
    /// O(1) time, O(1) space
    pub fn dequeue(&mut self) -> Option<T> {
        self.items.pop_front()
    }
    
    /// O(1) time, O(1) space
    pub fn front(&self) -> Option<&T> {
        self.items.front()
    }
    
    /// O(1) time, O(1) space
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    /// O(1) time, O(1) space
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

// Example: BFS implementation
use std::collections::{HashMap, HashSet};

pub fn bfs_traversal<T: Clone + Eq + std::hash::Hash>(
    graph: &HashMap<T, Vec<T>>,
    start: T
) -> Vec<T> {
    let mut visited = HashSet::new();
    let mut queue = Queue::new();
    let mut result = Vec::new();
    
    queue.enqueue(start.clone());
    visited.insert(start);
    
    while !queue.is_empty() {
        let vertex = queue.dequeue().unwrap();
        result.push(vertex.clone());
        
        if let Some(neighbors) = graph.get(&vertex) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    visited.insert(neighbor.clone());
                    queue.enqueue(neighbor.clone());
                }
            }
        }
    }
    
    result
}
```

## 8. Tree Operations Analysis {#tree-operations}

### Binary Search Tree Implementation

#### Python BST

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class BinarySearchTree:
    def __init__(self):
        self.root = None
    
    def insert(self, val):
        """Average O(log n), Worst O(n) time; O(log n) space"""
        self.root = self._insert_recursive(self.root, val)
    
    def _insert_recursive(self, node, val):
        if not node:
            return TreeNode(val)
        
        if val < node.val:
            node.left = self._insert_recursive(node.left, val)
        elif val > node.val:
            node.right = self._insert_recursive(node.right, val)
        
        return node
    
    def search(self, val):
        """Average O(log n), Worst O(n) time; O(log n) space"""
        return self._search_recursive(self.root, val)
    
    def _search_recursive(self, node, val):
        if not node or node.val == val:
            return node
        
        if val < node.val:
            return self._search_recursive(node.left, val)
        else:
            return self._search_recursive(node.right, val)
    
    def delete(self, val):
        """Average O(log n), Worst O(n) time; O(log n) space"""
        self.root = self._delete_recursive(self.root, val)
    
    def _delete_recursive(self, node, val):
        if not node:
            return node
        
        if val < node.val:
            node.left = self._delete_recursive(node.left, val)
        elif val > node.val:
            node.right = self._delete_recursive(node.right, val)
        else:
            # Node to delete found
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            else:
                # Node has two children
                successor = self._find_min(node.right)
                node.val = successor.val
                node.right = self._delete_recursive(node.right, successor.val)
        
        return node
    
    def _find_min(self, node):
        while node.left:
            node = node.left
        return node
    
    def inorder_traversal(self):
        """O(n) time, O(h) space where h is height"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.val)
            self._inorder_recursive(node.right, result)
    
    def level_order_traversal(self):
        """O(n) time, O(w) space where w is max width"""
        if not self.root:
            return []
        
        result = []
        queue = [self.root]
        
        while queue:
            level_size = len(queue)
            level = []
            
            for _ in range(level_size):
                node = queue.pop(0)
                level.append(node.val)
                
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
            
            result.append(level)
        
        return result
```

#### Rust BST

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::collections::VecDeque;

type TreeNodeRef<T> = Rc<RefCell<TreeNode<T>>>;

#[derive(Debug)]
struct TreeNode<T> {
    val: T,
    left: Option<TreeNodeRef<T>>,
    right: Option<TreeNodeRef<T>>,
}

impl<T> TreeNode<T> {
    fn new(val: T) -> TreeNodeRef<T> {
        Rc::new(RefCell::new(TreeNode {
            val,
            left: None,
            right: None,
        }))
    }
}

pub struct BinarySearchTree<T> {
    root: Option<TreeNodeRef<T>>,
}

impl<T: Ord + Clone> BinarySearchTree<T> {
    pub fn new() -> Self {
        BinarySearchTree { root: None }
    }
    
    /// Average O(log n), Worst O(n) time; O(log n) space
    pub fn insert(&mut self, val: T) {
        if self.root.is_none() {
            self.root = Some(TreeNode::new(val));
        } else {
            Self::insert_recursive(&self.root, val);
        }
    }
    
    fn insert_recursive(node: &Option<TreeNodeRef<T>>, val: T) {
        if let Some(node_ref) = node {
            let mut node_borrow = node_ref.borrow_mut();
            
            if val < node_borrow.val {
                if node_borrow.left.is_none() {
                    node_borrow.left = Some(TreeNode::new(val));
                } else {
                    Self::insert_recursive(&node_borrow.left, val);
                }
            } else if val > node_borrow.val {
                if node_borrow.right.is_none() {
                    node_borrow.right = Some(TreeNode::new(val));
                } else {
                    Self::insert_recursive(&node_borrow.right, val);
                }
            }
        }
    }
    
    /// Average O(log n), Worst O(n) time; O(log n) space
    pub fn search(&self, val: T) -> bool {
        Self::search_recursive(&self.root, val)
    }
    
    fn search_recursive(node: &Option<TreeNodeRef<T>>, val: T) -> bool {
        match node {
            None => false,
            Some(node_ref) => {
                let node_borrow = node_ref.borrow();
                if val == node_borrow.val {
                    true
                } else if val < node_borrow.val {
                    Self::search_recursive(&node_borrow.left, val)
                } else {
                    Self::search_recursive(&node_borrow.right, val)
                }
            }
        }
    }
    
    /// O(n) time, O(h) space where h is height
    pub fn inorder_traversal(&self) -> Vec<T> {
        let mut result = Vec::new();
        Self::inorder_recursive(&self.root, &mut result);
        result
    }
    
    fn inorder_recursive(node: &Option<TreeNodeRef<T>>, result: &mut Vec<T>) {
        if let Some(node_ref) = node {
            let node_borrow = node_ref.borrow();
            Self::inorder_recursive(&node_borrow.left, result);
            result.push(node_borrow.val.clone());
            Self::inorder_recursive(&node_borrow.right, result);
        }
    }
    
    /// O(n) time, O(w) space where w is max width
    pub fn level_order_traversal(&self) -> Vec<Vec<T>> {
        let mut result = Vec::new();
        if self.root.is_none() {
            return result;
        }
        
        let mut queue = VecDeque::new();
        queue.push_back(self.root.as_ref().unwrap().clone());
        
        while !queue.is_empty() {
            let level_size = queue.len();
            let mut level = Vec::new();
            
            for _ in 0..level_size {
                let node = queue.pop_front().unwrap();
                let node_borrow = node.borrow();
                level.push(node_borrow.val.clone());
                
                if let Some(left) = &node_borrow.left {
                    queue.push_back(left.clone());
                }
                if let Some(right) = &node_borrow.right {
                    queue.push_back(right.clone());
                }
            }
            
            result.push(level);
        }
        
        result
    }
}

## 9. Graph Algorithms Analysis {#graph-algorithms}

### Graph Representations and Basic Operations

#### Python Graph Implementation

```python
from collections import defaultdict, deque

class Graph:
    def __init__(self, directed=False):
        self.graph = defaultdict(list)
        self.directed = directed
    
    def add_edge(self, u, v, weight=1):
        """O(1) time, O(1) space"""
        self.graph[u].append((v, weight))
        if not self.directed:
            self.graph[v].append((u, weight))
    
    def dfs(self, start):
        """O(V + E) time, O(V) space"""
        visited = set()
        result = []
        
        def dfs_recursive(vertex):
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor, _ in self.graph[vertex]:
                if neighbor not in visited:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start)
        return result
    
    def bfs(self, start):
        """O(V + E) time, O(V) space"""
        visited = set()
        queue = deque([start])
        result = []
        
        visited.add(start)
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor, _ in self.graph[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return result
    
    def dijkstra(self, start):
        """O((V + E) log V) time, O(V) space"""
        import heapq
        
        distances = {vertex: float('infinity') for vertex in self.graph}
        distances[start] = 0
        pq = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current_dist > distances[current]:
                continue
            
            for neighbor, weight in self.graph[current]:
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(pq, (distance, neighbor))
        
        return distances
    
    def topological_sort(self):
        """O(V + E) time, O(V) space"""
        if not self.directed:
            raise ValueError("Topological sort only works on directed graphs")
        
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for vertex in self.graph:
            for neighbor, _ in self.graph[vertex]:
                in_degree[neighbor] += 1
        
        # Find vertices with no incoming edges
        queue = deque([vertex for vertex in self.graph if in_degree[vertex] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor, _ in self.graph[vertex]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(self.graph) else None
    
    def has_cycle(self):
        """O(V + E) time, O(V) space"""
        if not self.directed:
            return self._has_cycle_undirected()
        else:
            return self._has_cycle_directed()
    
    def _has_cycle_undirected(self):
        visited = set()
        
        def dfs(vertex, parent):
            visited.add(vertex)
            
            for neighbor, _ in self.graph[vertex]:
                if neighbor not in visited:
                    if dfs(neighbor, vertex):
                        return True
                elif neighbor != parent:
                    return True
            return False
        
        for vertex in self.graph:
            if vertex not in visited:
                if dfs(vertex, -1):
                    return True
        return False
    
    def _has_cycle_directed(self):
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(int)
        
        def dfs(vertex):
            if color[vertex] == GRAY:
                return True
            if color[vertex] == BLACK:
                return False
            
            color[vertex] = GRAY
            
            for neighbor, _ in self.graph[vertex]:
                if dfs(neighbor):
                    return True
            
            color[vertex] = BLACK
            return False
        
        for vertex in self.graph:
            if color[vertex] == WHITE:
                if dfs(vertex):
                    return True
        return False

# Example usage and analysis
def analyze_graph_operations():
    # Create a weighted directed graph
    g = Graph(directed=True)
    edges = [(0, 1, 4), (0, 2, 2), (1, 2, 1), (1, 3, 5), (2, 3, 3)]
    
    for u, v, w in edges:
        g.add_edge(u, v, w)
    
    print("DFS from 0:", g.dfs(0))  # O(V + E)
    print("BFS from 0:", g.bfs(0))  # O(V + E)
    print("Dijkstra from 0:", g.dijkstra(0))  # O((V + E) log V)
    print("Topological sort:", g.topological_sort())  # O(V + E)
    print("Has cycle:", g.has_cycle())  # O(V + E)
```

#### Rust Graph Implementation

```rust
use std::collections::{HashMap, HashSet, VecDeque, BinaryHeap};
use std::cmp::{Ordering, Reverse};

#[derive(Clone, Debug)]
pub struct Graph<T> {
    adjacency_list: HashMap<T, Vec<(T, i32)>>,
    directed: bool,
}

impl<T: Clone + Eq + std::hash::Hash + Ord> Graph<T> {
    pub fn new(directed: bool) -> Self {
        Graph {
            adjacency_list: HashMap::new(),
            directed,
        }
    }
    
    /// O(1) time, O(1) space
    pub fn add_edge(&mut self, u: T, v: T, weight: i32) {
        self.adjacency_list.entry(u.clone()).or_insert_with(Vec::new).push((v.clone(), weight));
        if !self.directed {
            self.adjacency_list.entry(v).or_insert_with(Vec::new).push((u, weight));
        }
    }
    
    /// O(V + E) time, O(V) space
    pub fn dfs(&self, start: T) -> Vec<T> {
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        
        self.dfs_recursive(start, &mut visited, &mut result);
        result
    }
    
    fn dfs_recursive(&self, vertex: T, visited: &mut HashSet<T>, result: &mut Vec<T>) {
        visited.insert(vertex.clone());
        result.push(vertex.clone());
        
        if let Some(neighbors) = self.adjacency_list.get(&vertex) {
            for (neighbor, _) in neighbors {
                if !visited.contains(neighbor) {
                    self.dfs_recursive(neighbor.clone(), visited, result);
                }
            }
        }
    }
    
    /// O(V + E) time, O(V) space
    pub fn bfs(&self, start: T) -> Vec<T> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        let mut result = Vec::new();
        
        queue.push_back(start.clone());
        visited.insert(start);
        
        while let Some(vertex) = queue.pop_front() {
            result.push(vertex.clone());
            
            if let Some(neighbors) = self.adjacency_list.get(&vertex) {
                for (neighbor, _) in neighbors {
                    if !visited.contains(neighbor) {
                        visited.insert(neighbor.clone());
                        queue.push_back(neighbor.clone());
                    }
                }
            }
        }
        
        result
    }
    
    /// O((V + E) log V) time, O(V) space
    pub fn dijkstra(&self, start: T) -> HashMap<T, i32> {
        let mut distances = HashMap::new();
        let mut pq = BinaryHeap::new();
        
        // Initialize distances
        for vertex in self.adjacency_list.keys() {
            distances.insert(vertex.clone(), i32::MAX);
        }
        distances.insert(start.clone(), 0);
        
        pq.push(Reverse((0, start)));
        
        while let Some(Reverse((current_dist, current))) = pq.pop() {
            if current_dist > *distances.get(&current).unwrap_or(&i32::MAX) {
                continue;
            }
            
            if let Some(neighbors) = self.adjacency_list.get(&current) {
                for (neighbor, weight) in neighbors {
                    let distance = current_dist + weight;
                    
                    if distance < *distances.get(neighbor).unwrap_or(&i32::MAX) {
                        distances.insert(neighbor.clone(), distance);
                        pq.push(Reverse((distance, neighbor.clone())));
                    }
                }
            }
        }
        
        distances
    }
    
    /// O(V + E) time, O(V) space
    pub fn topological_sort(&self) -> Option<Vec<T>> {
        if !self.directed {
            return None; // Only works on directed graphs
        }
        
        let mut in_degree = HashMap::new();
        
        // Initialize in-degrees
        for vertex in self.adjacency_list.keys() {
            in_degree.insert(vertex.clone(), 0);
        }
        
        // Calculate in-degrees
        for neighbors in self.adjacency_list.values() {
            for (neighbor, _) in neighbors {
                *in_degree.entry(neighbor.clone()).or_insert(0) += 1;
            }
        }
        
        // Find vertices with no incoming edges
        let mut queue = VecDeque::new();
        for (vertex, &degree) in &in_degree {
            if degree == 0 {
                queue.push_back(vertex.clone());
            }
        }
        
        let mut result = Vec::new();
        
        while let Some(vertex) = queue.pop_front() {
            result.push(vertex.clone());
            
            if let Some(neighbors) = self.adjacency_list.get(&vertex) {
                for (neighbor, _) in neighbors {
                    if let Some(degree) = in_degree.get_mut(neighbor) {
                        *degree -= 1;
                        if *degree == 0 {
                            queue.push_back(neighbor.clone());
                        }
                    }
                }
            }
        }
        
        if result.len() == self.adjacency_list.len() {
            Some(result)
        } else {
            None // Graph has a cycle
        }
    }
}

## 10. Sorting Algorithms Analysis {#sorting-algorithms}

### Comparison-based Sorting Algorithms

#### Python Sorting Implementations

```python
import random
import time

def bubble_sort(arr):
    """
    Time: O(n²) average and worst case, O(n) best case
    Space: O(1)
    Stable: Yes
    """
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:  # Optimization for best case
            break
    return arr

def selection_sort(arr):
    """
    Time: O(n²) all cases
    Space: O(1)
    Stable: No
    """
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

def insertion_sort(arr):
    """
    Time: O(n²) average and worst case, O(n) best case
    Space: O(1)
    Stable: Yes
    """
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

def merge_sort(arr):
    """
    Time: O(n log n) all cases
    Space: O(n)
    Stable: Yes
    """
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def quick_sort(arr):
    """
    Time: O(n log n) average case, O(n²) worst case
    Space: O(log n) average case, O(n) worst case
    Stable: No
    """
    if len(arr) <= 1:
        return arr
    
    pivot = partition(arr, 0, len(arr) - 1)
    return quick_sort(arr[:pivot]) + [arr[pivot]] + quick_sort(arr[pivot + 1:])

def partition(arr, low, high):
    # Randomized pivot for better average performance
    random_idx = random.randint(low, high)
    arr[random_idx], arr[high] = arr[high], arr[random_idx]
    
    pivot = arr[high]
    i = low - 1
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def heap_sort(arr):
    """
    Time: O(n log n) all cases
    Space: O(1)
    Stable: No
    """
    n = len(arr)
    
    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    
    return arr

def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

# Non-comparison based sorting
def counting_sort(arr):
    """
    Time: O(n + k) where k is the range of input
    Space: O(k)
    Stable: Yes
    """
    if not arr:
        return arr
    
    max_val = max(arr)
    min_val = min(arr)
    range_size = max_val - min_val + 1
    
    count = [0] * range_size
    output = [0] * len(arr)
    
    # Count occurrences
    for num in arr:
        count[num - min_val] += 1
    
    # Cumulative count
    for i in range(1, range_size):
        count[i] += count[i - 1]
    
    # Build output array
    for i in range(len(arr) - 1, -1, -1):
        output[count[arr[i] - min_val] - 1] = arr[i]
        count[arr[i] - min_val] -= 1
    
    return output

def radix_sort(arr):
    """
    Time: O(d * (n + k)) where d is number of digits, k is range of digits
    Space: O(n + k)
    Stable: Yes
    """
    if not arr:
        return arr
    
    max_num = max(arr)
    exp = 1
    
    while max_num // exp > 0:
        arr = counting_sort_by_digit(arr, exp)
        exp *= 10
    
    return arr

def counting_sort_by_digit(arr, exp):
    output = [0] * len(arr)
    count = [0] * 10
    
    for num in arr:
        digit = (num // exp) % 10
        count[digit] += 1
    
    for i in range(1, 10):
        count[i] += count[i - 1]
    
    for i in range(len(arr) - 1, -1, -1):
        digit = (arr[i] // exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit] -= 1
    
    return output

# Performance analysis function
def analyze_sorting_performance():
    algorithms = [
        ("Bubble Sort", bubble_sort),
        ("Selection Sort", selection_sort),
        ("Insertion Sort", insertion_sort),
        ("Merge Sort", merge_sort),
        ("Quick Sort", quick_sort),
        ("Heap Sort", heap_sort),
        ("Counting Sort", counting_sort),
        ("Radix Sort", radix_sort)
    ]
    
    sizes = [100, 1000, 5000]
    
    for size in sizes:
        print(f"\nArray size: {size}")
        print("-" * 50)
        
        # Generate test data
        random_data = [random.randint(0, 1000) for _ in range(size)]
        
        for name, algorithm in algorithms:
            test_data = random_data.copy()
            start_time = time.time()
            
            try:
                algorithm(test_data)
                end_time = time.time()
                print(f"{name:15}: {end_time - start_time:.6f} seconds")
            except Exception as e:
                print(f"{name:15}: Error - {e}")
```

#### Rust Sorting Implementations

```rust
use std::time::Instant;
use rand::Rng;

pub fn bubble_sort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    for i in 0..n {
        let mut swapped = false;
        for j in 0..n - i - 1 {
            if arr[j] > arr[j + 1] {
                arr.swap(j, j + 1);
                swapped = true;
            }
        }
        if !swapped {
            break;
        }
    }
}

pub fn selection_sort<T: Ord>(arr: &mut [T]) {
    let n = arr.len();
    for i in 0..n {
        let mut min_idx = i;
        for j in i + 1..n {
            if arr[j] < arr[min_idx] {
                min_idx = j;
            }
        }
        arr.swap(i, min_idx);
    }
}

pub fn insertion_sort<T: Ord>(arr: &mut [T]) {
    for i in 1..arr.len() {
        let mut j = i;
        while j > 0 && arr[j - 1] > arr[j] {
            arr.swap(j - 1, j);
            j -= 1;
        }
    }
}

pub fn merge_sort<T: Ord + Clone>(arr: &mut [T]) {
    let len = arr.len();
    if len <= 1 {
        return;
    }
    
    let mid = len / 2;
    let mut left = arr[..mid].to_vec();
    let mut right = arr[mid..].to_vec();
    
    merge_sort(&mut left);
    merge_sort(&mut right);
    
    merge(&left, &right, arr);
}

fn merge<T: Ord + Clone>(left: &[T], right: &[T], result: &mut [T]) {
    let mut i = 0;
    let mut j = 0;
    let mut k = 0;
    
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            result[k] = left[i].clone();
            i += 1;
        } else {
            result[k] = right[j].clone();
            j += 1;
        }
        k += 1;
    }
    
    while i < left.len() {
        result[k] = left[i].clone();
        i += 1;
        k += 1;
    }
    
    while j < right.len() {
        result[k] = right[j].clone();
        j += 1;
        k += 1;
    }
}

pub fn quick_sort<T: Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    
    let pivot_idx = partition(arr);
    quick_sort(&mut arr[..pivot_idx]);
    quick_sort(&mut arr[pivot_idx + 1..]);
}

fn partition<T: Ord>(arr: &mut [T]) -> usize {
    let len = arr.len();
    let pivot_idx = len - 1;
    let mut i = 0;
    
    for j in 0..pivot_idx {
        if arr[j] <= arr[pivot_idx] {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, pivot_idx);
    i
}

pub fn heap_sort<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    
    // Build max heap
    for i in (0..len / 2).rev() {
        heapify(arr, len, i);
    }
    
    // Extract elements from heap
    for i in (1..len).rev() {
        arr.swap(0, i);
        heapify(arr, i, 0);
    }
}

fn heapify<T: Ord>(arr: &mut [T], n: usize, i: usize) {
    let mut largest = i;
    let left = 2 * i + 1;
    let right = 2 * i + 2;
    
    if left < n && arr[left] > arr[largest] {
        largest = left;
    }
    
    if right < n && arr[right] > arr[largest] {
        largest = right;
    }
    
    if largest != i {
        arr.swap(i, largest);
        heapify(arr, n, largest);
    }
}

pub fn counting_sort(arr: &mut [i32]) {
    if arr.is_empty() {
        return;
    }
    
    let max_val = *arr.iter().max().unwrap();
    let min_val = *arr.iter().min().unwrap();
    let range = (max_val - min_val + 1) as usize;
    
    let mut count = vec![0; range];
    let mut output = vec![0; arr.len()];
    
    // Count occurrences
    for &num in arr.iter() {
        count[(num - min_val) as usize] += 1;
    }
    
    // Cumulative count
    for i in 1..range {
        count[i] += count[i - 1];
    }
    
    // Build output array
    for &num in arr.iter().rev() {
        let idx = (num - min_val) as usize;
        output[count[idx] - 1] = num;
        count[idx] -= 1;
    }
    
    arr.copy_from_slice(&output);
}

pub fn radix_sort(arr: &mut [i32]) {
    if arr.is_empty() {
        return;
    }
    
    let max_num = *arr.iter().max().unwrap();
    let mut exp = 1;
    
    while max_num / exp > 0 {
        counting_sort_by_digit(arr, exp);
        exp *= 10;
    }
}

fn counting_sort_by_digit(arr: &mut [i32], exp: i32) {
    let mut output = vec![0; arr.len()];
    let mut count = vec![0; 10];
    
    for &num in arr.iter() {
        let digit = ((num / exp) % 10) as usize;
        count[digit] += 1;
    }
    
    for i in 1..10 {
        count[i] += count[i - 1];
    }
    
    for &num in arr.iter().rev() {
        let digit = ((num / exp) % 10) as usize;
        output[count[digit] - 1] = num;
        count[digit] -= 1;
    }
    
    arr.copy_from_slice(&output);
}

// Performance analysis
pub fn analyze_sorting_performance() {
    let algorithms: Vec<(&str, fn(&mut [i32]))> = vec![
        ("Bubble Sort", bubble_sort),
        ("Selection Sort", selection_sort),
        ("Insertion Sort", insertion_sort),
        ("Merge Sort", merge_sort),
        ("Quick Sort", quick_sort),
        ("Heap Sort", heap_sort),
        ("Counting Sort", counting_sort),
        ("Radix Sort", radix_sort),
    ];
    
    let sizes = [100, 1000, 5000];
    
    for size in sizes {
        println!("\nArray size: {}", size);
        println!("{}", "-".repeat(50));
        
        let mut rng = rand::thread_rng();
        let random_data: Vec<i32> = (0..size).map(|_| rng.gen_range(0..1000)).collect();
        
        for (name, algorithm) in &algorithms {
            let mut test_data = random_data.clone();
            let start = Instant::now();
            
            algorithm(&mut test_data);
            
            let duration = start.elapsed();
            println!("{:15}: {:?}", name, duration);
        }
    }
}

## 11. Searching Algorithms Analysis {#searching-algorithms}

### Linear and Binary Search

#### Python Search Implementations

```python
def linear_search(arr, target):
    """
    Time: O(n) worst case, O(1) best case
    Space: O(1)
    Works on: Any array (sorted or unsorted)
    """
    for i, value in enumerate(arr):
        if value == target:
            return i
    return -1

def binary_search_iterative(arr, target):
    """
    Time: O(log n)
    Space: O(1)
    Works on: Sorted arrays only
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def binary_search_recursive(arr, target, left=None, right=None):
    """
    Time: O(log n)
    Space: O(log n) due to recursion stack
    Works on: Sorted arrays only
    """
    if left is None:
        left = 0
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)
```

## 12. Dynamic Programming Analysis {#dynamic-programming}

### Characteristics of DP Problems

- Overlapping subproblems
- Optimal substructure
- State transitions

### Space-Time Tradeoffs

```python
# O(n) space approach
def fibonacci_dp(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]

# O(1) space approach
def fibonacci_optimized(n):
    if n <= 1:
        return n
    prev, curr = 0, 1
    
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr
```

## 13. Practical Benchmarking {#practical-benchmarking}

### Python Benchmarking

```python
import timeit
import statistics

def benchmark_function(func, *args):
    times = []
    for _ in range(100):
        start = timeit.default_timer()
        func(*args)
        times.append(timeit.default_timer() - start)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times)
    }
```

### Rust Benchmarking

```rust
use std::time::Instant;
use std::collections::HashMap;

fn benchmark_function<F, T>(func: F, args: T) -> HashMap<String, f64>
where
    F: Fn(T) -> (),
{
    let mut times = Vec::new();
    
    for _ in 0..100 {
        let start = Instant::now();
        func(args);
        times.push(start.elapsed().as_secs_f64());
    }
    
    let mut results = HashMap::new();
    results.insert("mean".to_string(), mean(&times));
    results.insert("median".to_string(), median(&times));
    results.insert("std_dev".to_string(), std_dev(&times));
    
    results
}
```

## Summary

- Time complexity measures execution time growth
- Space complexity measures memory usage growth
- Big O notation describes worst-case scenarios
- Different data structures have different performance characteristics
- Algorithm choice depends on:
  - Input size
  - Data characteristics
  - Hardware constraints
  - Space vs time tradeoffs

## Best Practices

1. Always consider both time and space complexity
2. Profile code in real-world conditions
3. Consider constant factors for small inputs
4. Use appropriate data structures
5. Balance readability with performance
6. Benchmark with realistic data sets

This completes our comprehensive guide to runtime analysis in data structures and algorithms.

I'll create a comprehensive ASCII diagram showing how runtime analysis in Data Structures and Algorithms works step by step.This comprehensive ASCII diagram walks through the complete process of runtime analysis for Data Structures and Algorithms using Bubble Sort as an example. Here's what each step accomplishes:

**Steps 1-3** establish the foundation by identifying the algorithm, counting basic operations, and expressing the count as a function of input size.

**Steps 4-5** perform the mathematical analysis, converting the operation count into a mathematical formula and then applying asymptotic analysis to determine Big-O complexity.

**Steps 6-7** analyze different cases (best, worst, average) and examine space complexity alongside time complexity.

**Steps 8-9** provide practical context by showing how the algorithm scales with input size and comparing it with other sorting algorithms.

The diagram also includes:
- A visual representation of common complexity classes
- A practical performance scaling table
- A comprehensive algorithm comparison chart
- A checklist for systematic runtime analysis

This systematic approach can be applied to analyze any algorithm, helping you understand not just what the time complexity is, but *why* it is that complexity and how it compares to alternatives.

# Runtime Analysis in Data Structures & Algorithms - Step by Step

```
                    RUNTIME ANALYSIS WORKFLOW
                    ========================

Step 1: IDENTIFY THE ALGORITHM
┌─────────────────────────────────────────────────────────────────┐
│  Input: Algorithm/Code to Analyze                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  function bubbleSort(arr):                              │    │
│  │      for i = 0 to n-1:                                 │    │
│  │          for j = 0 to n-i-2:                           │    │
│  │              if arr[j] > arr[j+1]:                     │    │
│  │                  swap(arr[j], arr[j+1])                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 2: COUNT BASIC OPERATIONS
┌─────────────────────────────────────────────────────────────────┐
│  Identify Elementary Operations:                                │
│  • Comparisons: arr[j] > arr[j+1]                              │
│  • Assignments: i = 0, j = 0                                   │
│  • Arithmetic: j+1, n-i-2                                      │
│  • Array Access: arr[j], arr[j+1]                              │
│  • Function Calls: swap()                                      │
│                                                                 │
│  Focus on MOST FREQUENT operation → Comparisons                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 3: EXPRESS AS FUNCTION OF INPUT SIZE
┌─────────────────────────────────────────────────────────────────┐
│  Input Size: n (array length)                                  │
│                                                                 │
│  Operation Count Analysis:                                      │
│  Outer loop: runs n times                                      │
│  Inner loop: runs (n-i-1) times for each i                    │
│                                                                 │
│  Total comparisons:                                             │
│  i=0: (n-1) comparisons                                        │
│  i=1: (n-2) comparisons                                        │
│  i=2: (n-3) comparisons                                        │
│  ...                                                            │
│  i=n-1: 0 comparisons                                          │
│                                                                 │
│  T(n) = (n-1) + (n-2) + (n-3) + ... + 1 + 0                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 4: MATHEMATICAL ANALYSIS
┌─────────────────────────────────────────────────────────────────┐
│  Sum Formula: T(n) = Σ(k=1 to n-1) k                          │
│                                                                 │
│  Using arithmetic series formula:                               │
│  T(n) = (n-1) × n / 2                                          │
│  T(n) = (n² - n) / 2                                           │
│  T(n) = n²/2 - n/2                                             │
│                                                                 │
│  Expanded: T(n) = 0.5n² - 0.5n                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 5: ASYMPTOTIC ANALYSIS (Big-O)
┌─────────────────────────────────────────────────────────────────┐
│                    Growth Rate Analysis                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  T(n) = 0.5n² - 0.5n                                   │    │
│  │                                                         │    │
│  │  As n → ∞:                                              │    │
│  │  • n² term dominates                                   │    │
│  │  • Constants and lower-order terms become negligible   │    │
│  │                                                         │    │
│  │  Therefore: T(n) ∈ O(n²)                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 6: ANALYZE DIFFERENT CASES
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┬─────────────┬──────────────┬─────────────────┐  │
│  │    Case     │ Input Type  │ Comparisons  │ Time Complexity │  │
│  ├─────────────┼─────────────┼──────────────┼─────────────────┤  │
│  │ Best Case   │ Already     │ n²/2 - n/2   │     O(n²)       │  │
│  │             │ Sorted      │              │                 │  │
│  ├─────────────┼─────────────┼──────────────┼─────────────────┤  │
│  │ Worst Case  │ Reverse     │ n²/2 - n/2   │     O(n²)       │  │
│  │             │ Sorted      │              │                 │  │
│  ├─────────────┼─────────────┼──────────────┼─────────────────┤  │
│  │ Average     │ Random      │ n²/2 - n/2   │     O(n²)       │  │
│  │ Case        │ Order       │              │                 │  │
│  └─────────────┴─────────────┴──────────────┴─────────────────┘  │
│                                                                 │
│  Note: Bubble Sort has same complexity for all cases!          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 7: SPACE COMPLEXITY ANALYSIS
┌─────────────────────────────────────────────────────────────────┐
│  Memory Usage Analysis:                                         │
│  • Input array: n elements                                     │
│  • Loop variables (i, j): constant space                       │
│  • Temporary variables in swap: constant space                 │
│  • No additional data structures                               │
│                                                                 │
│  Space Complexity: O(1) - Constant extra space                │
│  (Not counting input array)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 8: PRACTICAL IMPLICATIONS
┌─────────────────────────────────────────────────────────────────┐
│                    Performance Scaling                          │
│                                                                 │
│  Input Size │ Operations  │ Relative Time │ Real Time Est.     │
│  ───────────┼─────────────┼───────────────┼────────────────    │
│     n=10    │    45       │      1x       │    0.001ms         │
│     n=100   │   4,950     │    110x       │    0.1ms           │
│     n=1,000 │  499,500    │  11,100x      │    10ms            │
│     n=10,000│ 49,995,000  │1,110,000x     │    1 second        │
│                                                                 │
│  Conclusion: Algorithm becomes impractical for large inputs    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼

Step 9: COMPARISON WITH OTHER ALGORITHMS
┌─────────────────────────────────────────────────────────────────┐
│  ┌────────────────┬─────────────┬──────────────┬──────────────┐  │
│  │   Algorithm    │ Best Case   │ Average Case │ Worst Case   │  │
│  ├────────────────┼─────────────┼──────────────┼──────────────┤  │
│  │ Bubble Sort    │   O(n²)     │    O(n²)     │    O(n²)     │  │
│  │ Selection Sort │   O(n²)     │    O(n²)     │    O(n²)     │  │
│  │ Insertion Sort │   O(n)      │    O(n²)     │    O(n²)     │  │
│  │ Merge Sort     │  O(n log n) │  O(n log n)  │  O(n log n)  │  │
│  │ Quick Sort     │  O(n log n) │  O(n log n)  │    O(n²)     │  │
│  │ Heap Sort      │  O(n log n) │  O(n log n)  │  O(n log n)  │  │
│  └────────────────┴─────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘

COMMON BIG-O COMPLEXITIES (from best to worst):
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  O(1)      ■                           Constant                │
│  O(log n)  ■■                          Logarithmic             │
│  O(n)      ■■■■■■■■                    Linear                  │
│  O(n log n)■■■■■■■■■■■■■■■■             Linearithmic           │
│  O(n²)     ■■■■■■■■■■■■■■■■■■■■■■■■■    Quadratic              │
│  O(n³)     ■■■■■■■■■■■■■■■■■■■■■■■■■■■  Cubic                  │
│  O(2ⁿ)     ████████████████████████████ Exponential            │
│                                                                 │
│            Growth Rate Visualization                            │
└─────────────────────────────────────────────────────────────────┘

ANALYSIS CHECKLIST:
┌─────────────────────────────────────────────────────────────────┐
│  ✓ Identify basic operations                                    │
│  ✓ Count operations as function of input size                  │
│  ✓ Apply mathematical analysis                                 │
│  ✓ Determine dominant term                                     │
│  ✓ Express in Big-O notation                                  │
│  ✓ Analyze best, average, worst cases                         │
│  ✓ Calculate space complexity                                  │
│  ✓ Consider practical implications                             │
│  ✓ Compare with alternative algorithms                        │
└─────────────────────────────────────────────────────────────────┘
```