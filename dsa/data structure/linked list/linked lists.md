

# Comprehensive Guide to Linked Lists

## Table of Contents
1. [Introduction](#introduction)
2. [Theory and Concepts](#theory-and-concepts)
3. [Types of Linked Lists](#types-of-linked-lists)
4. [Python Implementations](#python-implementations)
5. [Rust Implementations](#rust-implementations)
6. [Performance Analysis](#performance-analysis)
7. [Common Use Cases](#common-use-cases)
8. [Practice Problems](#practice-problems)

## Introduction

A **Linked List** is a fundamental linear data structure where elements (nodes) are stored in sequence, but unlike arrays, elements are not stored in contiguous memory locations. Instead, each node contains data and a reference (or pointer) to the next node in the sequence.

### Key Characteristics

- **Dynamic size**: Can grow or shrink during runtime
- **Sequential access**: Must traverse from head to reach a specific element
- **Non-contiguous memory**: Nodes can be scattered throughout memory
- **Efficient insertion/deletion**: O(1) at known positions

## Theory and Concepts

### Node Structure

Each node in a linked list typically contains:

- **Data**: The actual value stored
- **Next**: Reference/pointer to the next node

### Memory Layout

```
Array:     [A][B][C][D]  (contiguous memory)
           ↑  ↑  ↑  ↑
          100 104 108 112

Linked List: [A|●]→[B|●]→[C|●]→[D|NULL]  (scattered memory)
             ↑     ↑     ↑     ↑
            100   200   150   300
```

### Advantages vs Disadvantages

**Advantages:**
- Dynamic size allocation
- Efficient insertion/deletion at beginning (O(1))
- Memory efficient (only allocates what's needed)
- No memory waste

**Disadvantages:**
- No random access (O(n) to reach nth element)
- Extra memory overhead for pointers
- Not cache-friendly due to non-contiguous memory
- No backward traversal (in singly linked lists)

## Types of Linked Lists

### 1. Singly Linked List
- Each node points to the next node
- Traversal only in forward direction
- Last node points to NULL

### 2. Doubly Linked List
- Each node has pointers to both next and previous nodes
- Bidirectional traversal
- More memory overhead

### 3. Circular Linked List
- Last node points back to the first node
- Can be singly or doubly circular
- No NULL termination

## Python Implementations

### Singly Linked List

```python
class Node:
    """A single node in a linked list."""
    def __init__(self, data):
        self.data = data
        self.next = None
    
    def __str__(self):
        return str(self.data)

class SinglyLinkedList:
    """Implementation of a singly linked list."""
    
    def __init__(self):
        self.head = None
        self.size = 0
    
    def is_empty(self):
        """Check if the list is empty."""
        return self.head is None
    
    def __len__(self):
        """Return the size of the list."""
        return self.size
    
    def prepend(self, data):
        """Add element at the beginning - O(1)"""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
    
    def append(self, data):
        """Add element at the end - O(n)"""
        new_node = Node(data)
        if self.is_empty():
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1
    
    def insert(self, index, data):
        """Insert element at specific index - O(n)"""
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            self.prepend(data)
            return
        
        new_node = Node(data)
        current = self.head
        for i in range(index - 1):
            current = current.next
        
        new_node.next = current.next
        current.next = new_node
        self.size += 1
    
    def delete_first(self):
        """Delete first element - O(1)"""
        if self.is_empty():
            raise ValueError("List is empty")
        
        data = self.head.data
        self.head = self.head.next
        self.size -= 1
        return data
    
    def delete_last(self):
        """Delete last element - O(n)"""
        if self.is_empty():
            raise ValueError("List is empty")
        
        if self.head.next is None:
            data = self.head.data
            self.head = None
            self.size -= 1
            return data
        
        current = self.head
        while current.next.next:
            current = current.next
        
        data = current.next.data
        current.next = None
        self.size -= 1
        return data
    
    def delete(self, index):
        """Delete element at specific index - O(n)"""
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        if index == 0:
            return self.delete_first()
        
        current = self.head
        for i in range(index - 1):
            current = current.next
        
        data = current.next.data
        current.next = current.next.next
        self.size -= 1
        return data
    
    def find(self, data):
        """Find first occurrence of data - O(n)"""
        current = self.head
        index = 0
        while current:
            if current.data == data:
                return index
            current = current.next
            index += 1
        return -1
    
    def get(self, index):
        """Get element at specific index - O(n)"""
        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")
        
        current = self.head
        for i in range(index):
            current = current.next
        return current.data
    
    def reverse(self):
        """Reverse the linked list in-place - O(n)"""
        prev = None
        current = self.head
        
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        
        self.head = prev
    
    def to_list(self):
        """Convert to Python list - O(n)"""
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result
    
    def __str__(self):
        """String representation of the list."""
        if self.is_empty():
            return "[]"
        
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        
        return " -> ".join(elements) + " -> NULL"
    
    def __iter__(self):
        """Make the list iterable."""
        current = self.head
        while current:
            yield current.data
            current = current.next

# Example usage and testing
if __name__ == "__main__":
    # Create a new linked list
    ll = SinglyLinkedList()
    
    # Test basic operations
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.prepend(0)
    print(f"List: {ll}")  # Output: 0 -> 1 -> 2 -> 3 -> NULL
    print(f"Length: {len(ll)}")  # Output: 4
    
    # Test insertion
    ll.insert(2, 1.5)
    print(f"After insert: {ll}")  # Output: 0 -> 1 -> 1.5 -> 2 -> 3 -> NULL
    
    # Test deletion
    ll.delete(0)  # Remove first
    ll.delete_last()  # Remove last
    print(f"After deletions: {ll}")  # Output: 1 -> 1.5 -> 2 -> NULL
    
    # Test find and get
    print(f"Index of 2: {ll.find(2)}")  # Output: 2
    print(f"Element at index 1: {ll.get(1)}")  # Output: 1.5
    
    # Test reverse
    ll.reverse()
    print(f"Reversed: {ll}")  # Output: 2 -> 1.5 -> 1 -> NULL
    
    # Test iteration
    print("Elements:", [x for x in ll])  # Output: [2, 1.5, 1]
```

### Doubly Linked List

```python
class DoublyNode:
    """A node in a doubly linked list."""
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None
    
    def __str__(self):
        return str(self.data)

class DoublyLinkedList:
    """Implementation of a doubly linked list."""
    
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
    
    def is_empty(self):
        return self.head is None
    
    def __len__(self):
        return self.size
    
    def prepend(self, data):
        """Add element at the beginning - O(1)"""
        new_node = DoublyNode(data)
        
        if self.is_empty():
            self.head = self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        
        self.size += 1
    
    def append(self, data):
        """Add element at the end - O(1)"""
        new_node = DoublyNode(data)
        
        if self.is_empty():
            self.head = self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        
        self.size += 1
    
    def delete_first(self):
        """Delete first element - O(1)"""
        if self.is_empty():
            raise ValueError("List is empty")
        
        data = self.head.data
        
        if self.head == self.tail:  # Only one element
            self.head = self.tail = None
        else:
            self.head = self.head.next
            self.head.prev = None
        
        self.size -= 1
        return data
    
    def delete_last(self):
        """Delete last element - O(1)"""
        if self.is_empty():
            raise ValueError("List is empty")
        
        data = self.tail.data
        
        if self.head == self.tail:  # Only one element
            self.head = self.tail = None
        else:
            self.tail = self.tail.prev
            self.tail.next = None
        
        self.size -= 1
        return data
    
    def __str__(self):
        if self.is_empty():
            return "[]"
        
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        
        return " <-> ".join(elements)
    
    def reverse_traverse(self):
        """Traverse from tail to head."""
        result = []
        current = self.tail
        while current:
            result.append(current.data)
            current = current.prev
        return result

# Example usage
if __name__ == "__main__":
    dll = DoublyLinkedList()
    dll.append(1)
    dll.append(2)
    dll.append(3)
    dll.prepend(0)
    
    print(f"Forward: {dll}")  # 0 <-> 1 <-> 2 <-> 3
    print(f"Backward: {dll.reverse_traverse()}")  # [3, 2, 1, 0]
```

### Circular Linked List

```python
class CircularLinkedList:
    """Implementation of a circular singly linked list."""
    
    def __init__(self):
        self.head = None
        self.size = 0
    
    def is_empty(self):
        return self.head is None
    
    def __len__(self):
        return self.size
    
    def append(self, data):
        """Add element to the list - O(n)"""
        new_node = Node(data)
        
        if self.is_empty():
            self.head = new_node
            new_node.next = new_node  # Point to itself
        else:
            current = self.head
            while current.next != self.head:
                current = current.next
            current.next = new_node
            new_node.next = self.head
        
        self.size += 1
    
    def prepend(self, data):
        """Add element at the beginning - O(n)"""
        new_node = Node(data)
        
        if self.is_empty():
            self.head = new_node
            new_node.next = new_node
        else:
            current = self.head
            while current.next != self.head:
                current = current.next
            current.next = new_node
            new_node.next = self.head
            self.head = new_node
        
        self.size += 1
    
    def __str__(self):
        if self.is_empty():
            return "[]"
        
        elements = []
        current = self.head
        elements.append(str(current.data))
        current = current.next
        
        while current != self.head:
            elements.append(str(current.data))
            current = current.next
        
        return " -> ".join(elements) + " -> (back to head)"

# Example usage
if __name__ == "__main__":
    cll = CircularLinkedList()
    cll.append(1)
    cll.append(2)
    cll.append(3)
    
    print(f"Circular List: {cll}")  # 1 -> 2 -> 3 -> (back to head)
```

## Rust Implementations

### Singly Linked List

```rust
use std::fmt;

#[derive(Debug)]
pub struct Node<T> {
    pub data: T,
    pub next: Option<Box<Node<T>>>,
}

impl<T> Node<T> {
    fn new(data: T) -> Self {
        Node {
            data,
            next: None,
        }
    }
}

#[derive(Debug)]
pub struct SinglyLinkedList<T> {
    head: Option<Box<Node<T>>>,
    size: usize,
}

impl<T> SinglyLinkedList<T> {
    /// Create a new empty linked list
    pub fn new() -> Self {
        SinglyLinkedList {
            head: None,
            size: 0,
        }
    }
    
    /// Check if the list is empty
    pub fn is_empty(&self) -> bool {
        self.head.is_none()
    }
    
    /// Get the size of the list
    pub fn len(&self) -> usize {
        self.size
    }
    
    /// Add element at the beginning - O(1)
    pub fn prepend(&mut self, data: T) {
        let mut new_node = Box::new(Node::new(data));
        new_node.next = self.head.take();
        self.head = Some(new_node);
        self.size += 1;
    }
    
    /// Add element at the end - O(n)
    pub fn append(&mut self, data: T) {
        let new_node = Box::new(Node::new(data));
        
        match &mut self.head {
            None => self.head = Some(new_node),
            Some(head) => {
                let mut current = head;
                while current.next.is_some() {
                    current = current.next.as_mut().unwrap();
                }
                current.next = Some(new_node);
            }
        }
        self.size += 1;
    }
    
    /// Insert element at specific index - O(n)
    pub fn insert(&mut self, index: usize, data: T) -> Result<(), &'static str> {
        if index > self.size {
            return Err("Index out of bounds");
        }
        
        if index == 0 {
            self.prepend(data);
            return Ok(());
        }
        
        let mut new_node = Box::new(Node::new(data));
        let mut current = &mut self.head;
        
        for _ in 0..(index - 1) {
            current = &mut current.as_mut().unwrap().next;
        }
        
        let next = current.as_mut().unwrap().next.take();
        new_node.next = next;
        current.as_mut().unwrap().next = Some(new_node);
        self.size += 1;
        
        Ok(())
    }
    
    /// Delete first element - O(1)
    pub fn delete_first(&mut self) -> Option<T> {
        if let Some(node) = self.head.take() {
            self.head = node.next;
            self.size -= 1;
            Some(node.data)
        } else {
            None
        }
    }
    
    /// Delete last element - O(n)
    pub fn delete_last(&mut self) -> Option<T> {
        match self.head.take() {
            None => None,
            Some(node) if node.next.is_none() => {
                self.size -= 1;
                Some(node.data)
            }
            Some(mut node) => {
                while node.next.as_ref().unwrap().next.is_some() {
                    node = node.next.unwrap();
                }
                let last_node = node.next.take().unwrap();
                self.head = Some(node);
                self.size -= 1;
                Some(last_node.data)
            }
        }
    }
    
    /// Get element at specific index - O(n)
    pub fn get(&self, index: usize) -> Option<&T> {
        if index >= self.size {
            return None;
        }
        
        let mut current = &self.head;
        for _ in 0..index {
            current = &current.as_ref().unwrap().next;
        }
        
        Some(&current.as_ref().unwrap().data)
    }
    
    /// Reverse the linked list - O(n)
    pub fn reverse(&mut self) {
        let mut prev = None;
        let mut current = self.head.take();
        
        while let Some(mut node) = current {
            let next = node.next.take();
            node.next = prev;
            prev = Some(node);
            current = next;
        }
        
        self.head = prev;
    }
    
    /// Convert to vector - O(n)
    pub fn to_vec(&self) -> Vec<&T> {
        let mut result = Vec::new();
        let mut current = &self.head;
        
        while let Some(node) = current {
            result.push(&node.data);
            current = &node.next;
        }
        
        result
    }
}

impl<T: PartialEq> SinglyLinkedList<T> {
    /// Find first occurrence of data - O(n)
    pub fn find(&self, data: &T) -> Option<usize> {
        let mut current = &self.head;
        let mut index = 0;
        
        while let Some(node) = current {
            if node.data == *data {
                return Some(index);
            }
            current = &node.next;
            index += 1;
        }
        
        None
    }
}

impl<T: fmt::Display> fmt::Display for SinglyLinkedList<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_empty() {
            return write!(f, "[]");
        }
        
        let mut current = &self.head;
        let mut elements = Vec::new();
        
        while let Some(node) = current {
            elements.push(format!("{}", node.data));
            current = &node.next;
        }
        
        write!(f, "{} -> NULL", elements.join(" -> "))
    }
}

impl<T> Iterator for SinglyLinkedList<T> {
    type Item = T;
    
    fn next(&mut self) -> Option<Self::Item> {
        self.delete_first()
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_operations() {
        let mut list = SinglyLinkedList::new();
        
        // Test empty list
        assert!(list.is_empty());
        assert_eq!(list.len(), 0);
        
        // Test append
        list.append(1);
        list.append(2);
        list.append(3);
        assert_eq!(list.len(), 3);
        assert_eq!(list.get(0), Some(&1));
        assert_eq!(list.get(2), Some(&3));
        
        // Test prepend
        list.prepend(0);
        assert_eq!(list.len(), 4);
        assert_eq!(list.get(0), Some(&0));
        
        // Test insert
        list.insert(2, 10).unwrap();
        assert_eq!(list.len(), 5);
        assert_eq!(list.get(2), Some(&10));
        
        // Test find
        assert_eq!(list.find(&10), Some(2));
        assert_eq!(list.find(&99), None);
        
        // Test deletion
        assert_eq!(list.delete_first(), Some(0));
        assert_eq!(list.len(), 4);
        
        let last = list.delete_last();
        assert_eq!(list.len(), 3);
        
        // Test reverse
        list.reverse();
        println!("Reversed list: {}", list);
    }
}

fn main() {
    let mut list = SinglyLinkedList::new();
    
    // Add elements
    list.append(1);
    list.append(2);
    list.append(3);
    list.prepend(0);
    
    println!("Original list: {}", list); // 0 -> 1 -> 2 -> 3 -> NULL
    println!("Length: {}", list.len());  // 4
    
    // Insert at index 2
    list.insert(2, 99).unwrap();
    println!("After insert: {}", list); // 0 -> 1 -> 99 -> 2 -> 3 -> NULL
    
    // Find element
    if let Some(index) = list.find(&99) {
        println!("Found 99 at index: {}", index); // 2
    }
    
    // Delete elements
    if let Some(first) = list.delete_first() {
        println!("Deleted first: {}", first); // 0
    }
    
    if let Some(last) = list.delete_last() {
        println!("Deleted last: {}", last); // 3
    }
    
    println!("After deletions: {}", list); // 1 -> 99 -> 2 -> NULL
    
    // Reverse the list
    list.reverse();
    println!("Reversed: {}", list); // 2 -> 99 -> 1 -> NULL
    
    // Convert to vector
    let vec = list.to_vec();
    println!("As vector: {:?}", vec); // [2, 99, 1]
}
```

### Doubly Linked List (Rust)

```rust
use std::fmt;
use std::rc::{Rc, Weak};
use std::cell::RefCell;

type NodeRef<T> = Rc<RefCell<DoublyNode<T>>>;
type WeakNodeRef<T> = Weak<RefCell<DoublyNode<T>>>;

#[derive(Debug)]
pub struct DoublyNode<T> {
    pub data: T,
    pub next: Option<NodeRef<T>>,
    pub prev: Option<WeakNodeRef<T>>,
}

impl<T> DoublyNode<T> {
    fn new(data: T) -> NodeRef<T> {
        Rc::new(RefCell::new(DoublyNode {
            data,
            next: None,
            prev: None,
        }))
    }
}

#[derive(Debug)]
pub struct DoublyLinkedList<T> {
    head: Option<NodeRef<T>>,
    tail: Option<WeakNodeRef<T>>,
    size: usize,
}

impl<T> DoublyLinkedList<T> {
    pub fn new() -> Self {
        DoublyLinkedList {
            head: None,
            tail: None,
            size: 0,
        }
    }
    
    pub fn is_empty(&self) -> bool {
        self.head.is_none()
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn prepend(&mut self, data: T) {
        let new_node = DoublyNode::new(data);
        
        match &self.head {
            None => {
                self.tail = Some(Rc::downgrade(&new_node));
                self.head = Some(new_node);
            }
            Some(head) => {
                head.borrow_mut().prev = Some(Rc::downgrade(&new_node));
                new_node.borrow_mut().next = Some(head.clone());
                self.head = Some(new_node);
            }
        }
        
        self.size += 1;
    }
    
    pub fn append(&mut self, data: T) {
        let new_node = DoublyNode::new(data);
        
        match &self.tail {
            None => {
                self.tail = Some(Rc::downgrade(&new_node));
                self.head = Some(new_node);
            }
            Some(tail) => {
                if let Some(tail_node) = tail.upgrade() {
                    tail_node.borrow_mut().next = Some(new_node.clone());
                    new_node.borrow_mut().prev = Some(tail.clone());
                    self.tail = Some(Rc::downgrade(&new_node));
                }
            }
        }
        
        self.size += 1;
    }
    
    pub fn delete_first(&mut self) -> Option<T> {
        if let Some(head) = self.head.take() {
            self.size -= 1;
            
            if let Some(next) = head.borrow().next.clone() {
                next.borrow_mut().prev = None;
                self.head = Some(next);
            } else {
                self.tail = None;
            }
            
            let data = Rc::try_unwrap(head).ok()?.into_inner().data;
            Some(data)
        } else {
            None
        }
    }
    
    pub fn delete_last(&mut self) -> Option<T> {
        if let Some(tail) = &self.tail {
            if let Some(tail_node) = tail.upgrade() {
                self.size -= 1;
                
                if let Some(prev) = &tail_node.borrow().prev {
                    if let Some(prev_node) = prev.upgrade() {
                        prev_node.borrow_mut().next = None;
                        self.tail = Some(prev.clone());
                    }
                } else {
                    self.head = None;
                    self.tail = None;
                }
                
                let data = Rc::try_unwrap(tail_node).ok()?.into_inner().data;
                return Some(data);
            }
        }
        None
    }
}

impl<T: fmt::Display> fmt::Display for DoublyLinkedList<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_empty() {
            return write!(f, "[]");
        }
        
        let mut elements = Vec::new();
        let mut current = self.head.as_ref();
        
        while let Some(node) = current {
            elements.push(format!("{}", node.borrow().data));
            current = node.borrow().next.as_ref();
        }
        
        write!(f, "{}", elements.join(" <-> "))
    }
}

fn main() {
    let mut dll = DoublyLinkedList::new();
    
    dll.append(1);
    dll.append(2);
    dll.append(3);
    dll.prepend(0);
    
    println!("List: {}", dll); // 0 <-> 1 <-> 2 <-> 3
    println!("Length: {}", dll.len()); // 4
    
    if let Some(first) = dll.delete_first() {
        println!("Deleted first: {}", first); // 0
    }
    
    if let Some(last) = dll.delete_last() {
        println!("Deleted last: {}", last); // 3
    }
    
    println!("After deletions: {}", dll); // 1 <-> 2
}
```

## Performance Analysis

### Time Complexities

| Operation | Singly LL | Doubly LL | Array | Dynamic Array |
|-----------|-----------|-----------|--------|---------------|
| Access nth element | O(n) | O(n) | O(1) | O(1) |
| Search | O(n) | O(n) | O(n) | O(n) |
| Insert at beginning | O(1) | O(1) | O(n) | O(n) |
| Insert at end | O(n) | O(1) | O(1)* | O(1)* |
| Insert at middle | O(n) | O(n) | O(n) | O(n) |
| Delete at beginning | O(1) | O(1) | O(n) | O(n) |
| Delete at end | O(n) | O(1) | O(1) | O(1) |
| Delete at middle | O(n) | O(n) | O(n) | O(n) |

*Amortized time complexity

### Space Complexity
- **Singly Linked List**: O(n) - one pointer per node
- **Doubly Linked List**: O(n) - two pointers per node
- **Arrays**: O(n) - no extra pointers needed

## Common Use Cases

### When to Use Linked Lists
1. **Dynamic size requirements**: When you don't know the size in advance
2. **Frequent insertions/deletions**: At the beginning or middle of the data structure
3. **Memory-constrained environments**: No need to pre-allocate large blocks
4. **Implementation of other data structures**: Stacks, queues, graphs

### When NOT to Use Linked Lists
1. **Random access needed**: Frequent access to elements by index
2. **Cache performance critical**: Arrays have better cache locality
3. **Memory overhead concerns**: Extra pointer storage per node
4. **Binary search required**: Need sorted, indexable data structure

### Real-world Applications
1. **Music/Video playlists**: Easy insertion/deletion of songs
2. **Browser history**: Forward/backward navigation (doubly linked)
3. **Undo functionality**: Chain of operations in editors
4. **Memory management**: Free block lists in allocators
5. **Implementation of stacks/queues**: When dynamic size is needed

## Practice Problems

### 1. Reverse a Linked List
```python
def reverse_iterative(head):
    """Reverse linked list iteratively."""
    prev = None
    current = head
    
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    
    return prev

def reverse_recursive(head):
    """Reverse linked list recursively."""
    if not head or not head.next:
        return head
    
    reversed_head = reverse_recursive(head.next)
    head.next.next = head
    head.next = None
    
    return reversed_head
```

### 2. Detect Cycle in Linked List (Floyd's Algorithm)
```python
def has_cycle(head):
    """Detect cycle using two pointers."""
    if not head or not head.next:
        return False
    
    slow = head
    fast = head.next
    
    while fast and fast.next:
        if slow == fast:
            return True
        slow = slow.next
        fast = fast.next.next
    
    return False
```

### 3. Find Middle Element
```python
def find_middle(head):
    """Find middle element using two pointers."""
    if not head:
        return None
    
    slow = fast = head
    
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow
```

### 4. Merge Two Sorted Lists
```python
def merge_sorted_lists(l1, l2):
    """Merge two sorted linked lists."""
    dummy = Node(0)
    current = dummy
    
    while l1 and l2:
        if l1.data <= l2.data:
            current.next = l1
            l1 = l1.next
        else:
            current.next = l2
            l2 = l2.next
        current = current.next
    
    # Attach remaining nodes
    current.next = l1 or l2
    
    return dummy.next
```

### 5. Remove Nth Node from End
```python
def remove_nth_from_end(head, n):
    """Remove nth node from end using two pointers."""
    dummy = Node(0)
    dummy.next = head
    first = second = dummy
    
    # Move first pointer n+1 steps ahead
    for _ in range(n + 1):
        first = first.next
    
    # Move both pointers until first reaches end
    while first:
        first = first.next
        second = second.next
    
    # Remove the nth node
    second.next = second.next.next
    
    return dummy.next
```

### Rust Solutions

```rust
// Reverse linked list in Rust
impl<T> SinglyLinkedList<T> {
    pub fn reverse_recursive(&mut self) {
        fn reverse_helper<T>(node: Option<Box<Node<T>>>) -> Option<Box<Node<T>>> {
            match node {
                None => None,
                Some(mut current) => {
                    if current.next.is_none() {
                        return Some(current);
                    }
                    
                    let reversed = reverse_helper(current.next.take());
                    // This is complex in Rust due to ownership rules
                    // The iterative approach is preferred
                    reversed
                }
            }
        }
        
        self.head = reverse_helper(self.head.take());
    }
}

// Detect cycle using Floyd's algorithm
pub fn has_cycle<T>(head: &Option<Box<Node<T>>>) -> bool {
    let mut slow = head;
    let mut fast = head;
    
    loop {
        // Move fast pointer two steps
        if let Some(fast_node) = fast {
            if let Some(fast_next) = &fast_node.next {
                fast = &fast_next.next;
            } else {
                return false;
            }
        } else {
            return false;
        }
        
        // Move slow pointer one step
        if let Some(slow_node) = slow {
            slow = &slow_node.next;
        } else {
            return false;
        }
        
        // Check if they meet (this is conceptually what we want,
        // but Rust's ownership model makes this difficult)
        // In practice, you'd need to use Rc<RefCell<>> or raw pointers
    }
}
```

## Advanced Topics

### Memory-Efficient Techniques

#### 1. XOR Linked List
A doubly linked list using only one pointer per node by XORing addresses:

```python
class XORNode:
    def __init__(self, data):
        self.data = data
        self.npx = 0  # XOR of next and previous addresses

# Note: This technique is mostly theoretical in high-level languages
# due to garbage collection and memory management restrictions
```

#### 2. Skip List
A probabilistic data structure that allows O(log n) search:

```python
import random

class SkipListNode:
    def __init__(self, data, level):
        self.data = data
        self.forward = [None] * (level + 1)

class SkipList:
    def __init__(self, max_level=16):
        self.max_level = max_level
        self.header = SkipListNode(None, max_level)
        self.level = 0
    
    def random_level(self):
        level = 0
        while random.random() < 0.5 and level < self.max_level:
            level += 1
        return level
    
    def search(self, key):
        current = self.header
        
        for i in range(self.level, -1, -1):
            while (current.forward[i] and 
                   current.forward[i].data < key):
                current = current.forward[i]
        
        current = current.forward[0]
        return current and current.data == key
```

### Thread-Safe Linked Lists

#### Lock-Free Stack (Rust)
```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }
    
    pub fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));
        
        loop {
            let head = self.head.load(Ordering::Acquire);
            unsafe {
                (*new_node).next = head;
            }
            
            if self.head.compare_exchange_weak(
                head,
                new_node,
                Ordering::Release,
                Ordering::Relaxed
            ).is_ok() {
                break;
            }
        }
    }
    
    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() {
                return None;
            }
            
            let next = unsafe { (*head).next };
            
            if self.head.compare_exchange_weak(
                head,
                next,
                Ordering::Release,
                Ordering::Relaxed
            ).is_ok() {
                unsafe {
                    let data = ptr::read(&(*head).data);
                    Box::from_raw(head);
                    return Some(data);
                }
            }
        }
    }
}
```

## Best Practices

### Design Principles
1. **Consistent Interface**: Provide clear, predictable method names
2. **Error Handling**: Handle edge cases gracefully
3. **Memory Management**: Prevent memory leaks and dangling pointers
4. **Iterator Support**: Make your list iterable
5. **Generic Implementation**: Support different data types

### Common Pitfalls
1. **Forgetting to update size**: Always maintain accurate count
2. **Memory leaks**: Properly deallocate nodes in manual memory management
3. **Null pointer dereference**: Check for null/None before accessing
4. **Off-by-one errors**: Be careful with index calculations
5. **Circular references**: Can cause memory leaks in reference-counted systems

### Testing Strategy
```python
def test_linked_list():
    """Comprehensive test suite for linked list."""
    ll = SinglyLinkedList()
    
    # Test empty list
    assert ll.is_empty()
    assert len(ll) == 0
    
    # Test single element
    ll.append(1)
    assert not ll.is_empty()
    assert len(ll) == 1
    assert ll.get(0) == 1
    
    # Test multiple elements
    ll.append(2)
    ll.append(3)
    ll.prepend(0)
    assert len(ll) == 4
    assert ll.to_list() == [0, 1, 2, 3]
    
    # Test insertion
    ll.insert(2, 99)
    assert ll.to_list() == [0, 1, 99, 2, 3]
    
    # Test deletion
    assert ll.delete(0) == 0
    assert ll.delete_last() == 3
    assert ll.to_list() == [1, 99, 2]
    
    # Test edge cases
    try:
        ll.get(10)  # Should raise exception
        assert False, "Should have raised IndexError"
    except IndexError:
        pass
    
    # Test find
    assert ll.find(99) == 1
    assert ll.find(404) == -1
    
    # Test reverse
    ll.reverse()
    assert ll.to_list() == [2, 99, 1]
    
    print("All tests passed!")

if __name__ == "__main__":
    test_linked_list()
```

## Conclusion

Linked lists are fundamental data structures that offer dynamic sizing and efficient insertion/deletion operations. While they have limitations like poor cache performance and lack of random access, they remain valuable tools in many scenarios.

**Key Takeaways:**
- Choose the right type of linked list for your use case
- Understand the trade-offs between time and space complexity
- Implement proper error handling and memory management
- Consider alternatives like dynamic arrays for better cache performance
- Practice common algorithms and patterns with linked lists

The implementations provided here offer a solid foundation for understanding and using linked lists in both Python and Rust, demonstrating different approaches to memory management and ownership models in these languages.

I'll create a comprehensive ASCII diagram showing how linked lists work, including their structure, basic operations, and step-by-step examples.I've created a comprehensive ASCII diagram that shows how linked lists work step by step! The diagram covers:

**Core Concepts:**
- Basic node structure with data and pointer fields
- How nodes connect to form a chain
- The role of the HEAD pointer

**Step-by-Step Operations:**
- **Insertion at beginning** - Shows the 3-step process of creating, linking, and updating the head
- **Insertion in middle** - Demonstrates traversal, creation, and pointer manipulation  
- **Deletion** - Shows how to bypass and remove nodes safely
- **Traversal** - Illustrates how to visit each node sequentially

**Additional Features:**
- Memory layout comparison between arrays and linked lists
- Time complexity analysis for common operations
- Common variations (doubly linked and circular lists)

The diagrams use boxes to represent nodes, arrows for pointers, and step-by-step breakdowns to show exactly how the data structure changes during each operation. This visual approach makes it easier to understand the pointer manipulation that's central to linked list operations.

Would you like me to expand on any particular aspect or add diagrams for other linked list operations like searching or reversing?

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

# Linked Lists: Comprehensive Guide with Python and Rust Implementations

**Core Content:**
- Theory and fundamental concepts
- Three types of linked lists (singly, doubly, circular)
- Complete implementations in both Python and Rust
- Performance analysis with time/space complexities

**Advanced Topics:**
- Memory-efficient techniques (XOR lists, Skip lists)
- Thread-safe implementations
- Lock-free data structures in Rust

**Practical Elements:**
- Common interview problems and solutions
- Best practices and design principles
- Comprehensive testing strategies
- Real-world use cases and applications

**Key Features of the Implementations:**

**Python:**
- Object-oriented design with clean interfaces
- Full error handling and edge case management
- Iterator support for Pythonic usage
- Comprehensive test suites

**Rust:**
- Memory-safe implementations using Rust's ownership system
- Generic implementations supporting any data type
- Advanced patterns like Rc<RefCell<>> for doubly linked lists
- Lock-free concurrent data structures

The guide serves as both a learning resource and a practical reference, with working code that you can run and modify. Each implementation includes detailed comments explaining the logic and complexity analysis for better understanding.

---

## Understanding the `is_empty` Method in a Linked List

Let’s break down your function step by step 👇

```python
def is_empty(self):
    """Check if the list is empty."""
    return self.head is None
```

---

### 🔍 Step 1: Context

This method is most likely **part of a class for a linked list**, for example:

```python
class LinkedList:
    def __init__(self):
        self.head = None
```

* Here, `self.head` is a reference (or pointer) to the **first node** in the linked list.
* When the list is **empty**, `self.head` has no node to point to, so it’s set to `None`.

---

### ⚙️ Step 2: What the method does

The method:

```python
return self.head is None
```

is checking whether the linked list’s `head` is `None`.

The expression:

```python
self.head is None
```

returns a **boolean value** (`True` or `False`):

* ✅ `True` → means the list **is empty** (because `head` doesn’t point to anything)
* ❌ `False` → means the list **is not empty** (because `head` points to some node)

---

### 🧠 Step 3: How `return` works here

The `return` statement simply **sends the result of the expression** (`self.head is None`) back to the code that called this function.

So for example:

```python
my_list = LinkedList()
print(my_list.is_empty())  # ✅ True, because head is None

# Add one node
my_list.head = Node(10)
print(my_list.is_empty())  # ❌ False, because head now points to a node
```

---

### ⚡Summary

| Expression                 | Meaning                              | Result                    |
| -------------------------- | ------------------------------------ | ------------------------- |
| `self.head is None`        | head does not point to any node      | `True`                    |
| `self.head is not None`    | head points to a valid node          | `False`                   |
| `return self.head is None` | return boolean indicating empty list | returns `True` or `False` |

---

Would you like me to visually show how this looks in memory (like a small diagram of the linked list with `head → Node` or `head → None`)?
