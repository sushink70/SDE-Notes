I've completed the comprehensive guide to Queue implementations! The guide now includes:

## What's Covered:

### **Core Implementations (Both Python & Rust):**
- Array-based queues with dynamic resizing
- Linked list-based queues 
- Priority queues using heaps
- Double-ended queues (deques)

### **Advanced Topics:**
- **Thread-safe queues** with proper synchronization
- **Circular buffers** for fixed-size streaming data
- **Performance benchmarking** code for both languages
- **Memory management** best practices

### **Practical Elements:**
- Complete working code examples with tests
- Performance comparisons and time complexities
- Real-world use cases for each queue type
- Best practices for choosing implementations
- Error handling patterns

### **Key Features:**
- **Production-ready code** with proper error handling
- **Comprehensive testing** examples
- **Performance benchmarking** tools
- **Thread-safety** implementations
- **Memory-efficient** designs

The implementations are designed to be both educational and practical - you can use them directly in projects or as learning references. Each implementation includes detailed comments explaining the algorithms and design decisions.

Would you like me to expand on any particular section, add more specialized queue types (like lock-free queues), or provide additional examples for specific use cases?

# Comprehensive Guide to Queue Implementations

## Table of Contents
1. [Introduction to Queues](#introduction-to-queues)
2. [Types of Queues](#types-of-queues)
3. [Python Implementations](#python-implementations)
4. [Rust Implementations](#rust-implementations)
5. [Performance Comparison](#performance-comparison)
6. [Use Cases and Applications](#use-cases-and-applications)
7. [Best Practices](#best-practices)

## Introduction to Queues

A **Queue** is a linear data structure that follows the First-In-First-Out (FIFO) principle. Elements are added to the rear (enqueue) and removed from the front (dequeue). Queues are fundamental in computer science and have numerous practical applications.

### Key Operations
- **Enqueue**: Add an element to the rear of the queue
- **Dequeue**: Remove and return the element from the front
- **Front/Peek**: View the front element without removing it
- **Is_empty**: Check if the queue is empty
- **Size**: Get the number of elements in the queue

### Time Complexities
- Enqueue: O(1) amortized
- Dequeue: O(1)
- Front/Peek: O(1)
- Is_empty: O(1)
- Size: O(1)

## Types of Queues

### 1. Simple Queue (Linear Queue)
Basic FIFO queue with front and rear pointers.

### 2. Circular Queue
Uses a circular array to efficiently utilize space, wrapping around when reaching the end.

### 3. Priority Queue
Elements are served based on priority rather than insertion order.

### 4. Double-ended Queue (Deque)
Allows insertion and deletion from both ends.

## Python Implementations

### 1. Array-based Queue Implementation

```python
class ArrayQueue:
    """Array-based queue implementation with dynamic resizing."""
    
    def __init__(self, capacity=10):
        self._data = [None] * capacity
        self._size = 0
        self._front = 0
    
    def __len__(self):
        return self._size
    
    def is_empty(self):
        return self._size == 0
    
    def enqueue(self, item):
        """Add item to the rear of the queue."""
        if self._size == len(self._data):
            self._resize(2 * len(self._data))
        
        rear = (self._front + self._size) % len(self._data)
        self._data[rear] = item
        self._size += 1
    
    def dequeue(self):
        """Remove and return item from front of queue."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self._data[self._front]
        self._data[self._front] = None  # Help garbage collection
        self._front = (self._front + 1) % len(self._data)
        self._size -= 1
        
        # Shrink array if needed
        if 0 < self._size < len(self._data) // 4:
            self._resize(len(self._data) // 2)
        
        return item
    
    def front(self):
        """Return front item without removing it."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._data[self._front]
    
    def _resize(self, capacity):
        """Resize the underlying array."""
        old_data = self._data
        self._data = [None] * capacity
        walk = self._front
        
        for i in range(self._size):
            self._data[i] = old_data[walk]
            walk = (walk + 1) % len(old_data)
        
        self._front = 0
    
    def __str__(self):
        if self.is_empty():
            return "Queue([])"
        
        items = []
        walk = self._front
        for _ in range(self._size):
            items.append(str(self._data[walk]))
            walk = (walk + 1) % len(self._data)
        
        return f"Queue([{', '.join(items)}])"


# Example usage and testing
if __name__ == "__main__":
    queue = ArrayQueue()
    
    # Test enqueue
    for i in range(1, 6):
        queue.enqueue(i)
        print(f"Enqueued {i}: {queue}")
    
    # Test dequeue
    while not queue.is_empty():
        item = queue.dequeue()
        print(f"Dequeued {item}: {queue}")
```

### 2. Linked List-based Queue Implementation

```python
class Node:
    """Node class for linked list implementation."""
    
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedQueue:
    """Linked list-based queue implementation."""
    
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0
    
    def __len__(self):
        return self._size
    
    def is_empty(self):
        return self._head is None
    
    def enqueue(self, item):
        """Add item to the rear of the queue."""
        new_node = Node(item)
        
        if self.is_empty():
            self._head = new_node
        else:
            self._tail.next = new_node
        
        self._tail = new_node
        self._size += 1
    
    def dequeue(self):
        """Remove and return item from front of queue."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        
        item = self._head.data
        self._head = self._head.next
        self._size -= 1
        
        if self.is_empty():
            self._tail = None
        
        return item
    
    def front(self):
        """Return front item without removing it."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self._head.data
    
    def __str__(self):
        if self.is_empty():
            return "Queue([])"
        
        items = []
        current = self._head
        while current:
            items.append(str(current.data))
            current = current.next
        
        return f"Queue([{', '.join(items)}])"


# Example usage
if __name__ == "__main__":
    queue = LinkedQueue()
    
    # Test operations
    for i in range(1, 6):
        queue.enqueue(i)
        print(f"Enqueued {i}: {queue}")
    
    print(f"Front element: {queue.front()}")
    
    while not queue.is_empty():
        item = queue.dequeue()
        print(f"Dequeued {item}: {queue}")
```

### 3. Priority Queue Implementation

```python
import heapq
from typing import Any, Tuple


class PriorityQueue:
    """Priority queue implementation using a binary heap."""
    
    def __init__(self):
        self._heap = []
        self._counter = 0  # For handling items with same priority
    
    def __len__(self):
        return len(self._heap)
    
    def is_empty(self):
        return len(self._heap) == 0
    
    def enqueue(self, item: Any, priority: int):
        """Add item with given priority (lower number = higher priority)."""
        # Use counter to break ties and maintain insertion order
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1
    
    def dequeue(self) -> Any:
        """Remove and return highest priority item."""
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        
        priority, counter, item = heapq.heappop(self._heap)
        return item
    
    def front(self) -> Any:
        """Return highest priority item without removing it."""
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        
        priority, counter, item = self._heap[0]
        return item
    
    def __str__(self):
        if self.is_empty():
            return "PriorityQueue([])"
        
        items = [(priority, item) for priority, counter, item in self._heap]
        return f"PriorityQueue({items})"


# Example usage
if __name__ == "__main__":
    pq = PriorityQueue()
    
    # Enqueue items with priorities
    pq.enqueue("Low priority task", 3)
    pq.enqueue("High priority task", 1)
    pq.enqueue("Medium priority task", 2)
    pq.enqueue("Another high priority", 1)
    
    print(f"Priority Queue: {pq}")
    
    # Dequeue items (should come out in priority order)
    while not pq.is_empty():
        item = pq.dequeue()
        print(f"Dequeued: {item}")
```

### 4. Double-ended Queue (Deque) Implementation

```python
from collections import deque as built_in_deque


class Deque:
    """Double-ended queue implementation using Python's built-in deque."""
    
    def __init__(self):
        self._data = built_in_deque()
    
    def __len__(self):
        return len(self._data)
    
    def is_empty(self):
        return len(self._data) == 0
    
    def add_front(self, item):
        """Add item to the front of the deque."""
        self._data.appendleft(item)
    
    def add_rear(self, item):
        """Add item to the rear of the deque."""
        self._data.append(item)
    
    def remove_front(self):
        """Remove and return item from front of deque."""
        if self.is_empty():
            raise IndexError("Deque is empty")
        return self._data.popleft()
    
    def remove_rear(self):
        """Remove and return item from rear of deque."""
        if self.is_empty():
            raise IndexError("Deque is empty")
        return self._data.pop()
    
    def front(self):
        """Return front item without removing it."""
        if self.is_empty():
            raise IndexError("Deque is empty")
        return self._data[0]
    
    def rear(self):
        """Return rear item without removing it."""
        if self.is_empty():
            raise IndexError("Deque is empty")
        return self._data[-1]
    
    def __str__(self):
        return f"Deque({list(self._data)})"


# Example usage
if __name__ == "__main__":
    dq = Deque()
    
    # Test adding to both ends
    dq.add_rear(1)
    dq.add_rear(2)
    dq.add_front(0)
    dq.add_front(-1)
    
    print(f"Deque after additions: {dq}")
    
    # Test removing from both ends
    print(f"Remove front: {dq.remove_front()}")
    print(f"Remove rear: {dq.remove_rear()}")
    print(f"Final deque: {dq}")
```

## Rust Implementations

### 1. Array-based Queue Implementation

```rust
use std::fmt;

pub struct ArrayQueue<T> {
    data: Vec<Option<T>>,
    front: usize,
    size: usize,
}

impl<T> ArrayQueue<T> {
    pub fn new() -> Self {
        Self::with_capacity(10)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        ArrayQueue {
            data: vec![None; capacity],
            front: 0,
            size: 0,
        }
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    pub fn enqueue(&mut self, item: T) {
        if self.size == self.data.len() {
            self.resize(2 * self.data.len());
        }
        
        let rear = (self.front + self.size) % self.data.len();
        self.data[rear] = Some(item);
        self.size += 1;
    }
    
    pub fn dequeue(&mut self) -> Option<T> {
        if self.is_empty() {
            return None;
        }
        
        let item = self.data[self.front].take();
        self.front = (self.front + 1) % self.data.len();
        self.size -= 1;
        
        // Shrink if needed
        if self.size > 0 && self.size < self.data.len() / 4 {
            self.resize(self.data.len() / 2);
        }
        
        item
    }
    
    pub fn front(&self) -> Option<&T> {
        if self.is_empty() {
            None
        } else {
            self.data[self.front].as_ref()
        }
    }
    
    fn resize(&mut self, new_capacity: usize) {
        let mut new_data = vec![None; new_capacity];
        let mut walk = self.front;
        
        for i in 0..self.size {
            new_data[i] = self.data[walk].take();
            walk = (walk + 1) % self.data.len();
        }
        
        self.data = new_data;
        self.front = 0;
    }
}

impl<T: fmt::Display> fmt::Display for ArrayQueue<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_empty() {
            write!(f, "Queue([])")
        } else {
            write!(f, "Queue([")?;
            let mut walk = self.front;
            for i in 0..self.size {
                if let Some(ref item) = self.data[walk] {
                    if i > 0 { write!(f, ", ")?; }
                    write!(f, "{}", item)?;
                }
                walk = (walk + 1) % self.data.len();
            }
            write!(f, "])")
        }
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_array_queue() {
        let mut queue = ArrayQueue::new();
        
        // Test enqueue
        for i in 1..=5 {
            queue.enqueue(i);
        }
        assert_eq!(queue.len(), 5);
        assert_eq!(queue.front(), Some(&1));
        
        // Test dequeue
        assert_eq!(queue.dequeue(), Some(1));
        assert_eq!(queue.dequeue(), Some(2));
        assert_eq!(queue.len(), 3);
        
        // Test empty queue
        while !queue.is_empty() {
            queue.dequeue();
        }
        assert_eq!(queue.dequeue(), None);
        assert_eq!(queue.front(), None);
    }
}

fn main() {
    let mut queue = ArrayQueue::new();
    
    // Test enqueue
    for i in 1..=5 {
        queue.enqueue(i);
        println!("Enqueued {}: {}", i, queue);
    }
    
    // Test dequeue
    while !queue.is_empty() {
        if let Some(item) = queue.dequeue() {
            println!("Dequeued {}: {}", item, queue);
        }
    }
}
```

### 2. Linked List-based Queue Implementation

```rust
use std::fmt;

type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    data: T,
    next: Link<T>,
}

impl<T> Node<T> {
    fn new(data: T) -> Box<Node<T>> {
        Box::new(Node { data, next: None })
    }
}

pub struct LinkedQueue<T> {
    head: Link<T>,
    tail: *mut Node<T>,
    size: usize,
}

impl<T> LinkedQueue<T> {
    pub fn new() -> Self {
        LinkedQueue {
            head: None,
            tail: std::ptr::null_mut(),
            size: 0,
        }
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.head.is_none()
    }
    
    pub fn enqueue(&mut self, item: T) {
        let new_node = Node::new(item);
        let raw_node: *mut Node<T> = Box::into_raw(new_node);
        
        if self.is_empty() {
            self.head = Some(unsafe { Box::from_raw(raw_node) });
            self.tail = raw_node;
        } else {
            unsafe {
                (*self.tail).next = Some(Box::from_raw(raw_node));
                self.tail = raw_node;
            }
        }
        
        self.size += 1;
    }
    
    pub fn dequeue(&mut self) -> Option<T> {
        self.head.take().map(|old_head| {
            self.head = old_head.next;
            self.size -= 1;
            
            if self.is_empty() {
                self.tail = std::ptr::null_mut();
            }
            
            old_head.data
        })
    }
    
    pub fn front(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.data)
    }
}

impl<T: fmt::Display> fmt::Display for LinkedQueue<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_empty() {
            write!(f, "Queue([])")
        } else {
            write!(f, "Queue([")?;
            let mut current = self.head.as_ref();
            let mut first = true;
            
            while let Some(node) = current {
                if !first { write!(f, ", ")?; }
                write!(f, "{}", node.data)?;
                current = node.next.as_ref();
                first = false;
            }
            
            write!(f, "])")
        }
    }
}

impl<T> Drop for LinkedQueue<T> {
    fn drop(&mut self) {
        while self.dequeue().is_some() {}
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_linked_queue() {
        let mut queue = LinkedQueue::new();
        
        // Test enqueue
        for i in 1..=5 {
            queue.enqueue(i);
        }
        assert_eq!(queue.len(), 5);
        assert_eq!(queue.front(), Some(&1));
        
        // Test dequeue
        assert_eq!(queue.dequeue(), Some(1));
        assert_eq!(queue.dequeue(), Some(2));
        assert_eq!(queue.len(), 3);
        
        // Test empty queue
        while !queue.is_empty() {
            queue.dequeue();
        }
        assert_eq!(queue.dequeue(), None);
    }
}

fn main() {
    let mut queue = LinkedQueue::new();
    
    // Test operations
    for i in 1..=5 {
        queue.enqueue(i);
        println!("Enqueued {}: {}", i, queue);
    }
    
    if let Some(front) = queue.front() {
        println!("Front element: {}", front);
    }
    
    while !queue.is_empty() {
        if let Some(item) = queue.dequeue() {
            println!("Dequeued {}: {}", item, queue);
        }
    }
}
```

### 3. Priority Queue Implementation

```rust
use std::collections::BinaryHeap;
use std::cmp::{Ordering, Reverse};
use std::fmt;

#[derive(Debug, Eq, PartialEq)]
struct PriorityItem<T> {
    priority: i32,
    counter: usize,
    item: T,
}

impl<T> Ord for PriorityItem<T> {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse ordering for min-heap behavior (lower number = higher priority)
        other.priority.cmp(&self.priority)
            .then_with(|| other.counter.cmp(&self.counter))
    }
}

impl<T> PartialOrd for PriorityItem<T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct PriorityQueue<T> {
    heap: BinaryHeap<PriorityItem<T>>,
    counter: usize,
}

impl<T> PriorityQueue<T> {
    pub fn new() -> Self {
        PriorityQueue {
            heap: BinaryHeap::new(),
            counter: 0,
        }
    }
    
    pub fn len(&self) -> usize {
        self.heap.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
    
    pub fn enqueue(&mut self, item: T, priority: i32) {
        let priority_item = PriorityItem {
            priority,
            counter: self.counter,
            item,
        };
        
        self.heap.push(priority_item);
        self.counter += 1;
    }
    
    pub fn dequeue(&mut self) -> Option<T> {
        self.heap.pop().map(|priority_item| priority_item.item)
    }
    
    pub fn front(&self) -> Option<&T> {
        self.heap.peek().map(|priority_item| &priority_item.item)
    }
}

impl<T: fmt::Display> fmt::Display for PriorityQueue<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_empty() {
            write!(f, "PriorityQueue([])")
        } else {
            write!(f, "PriorityQueue([")?;
            let mut items: Vec<_> = self.heap.iter().collect();
            items.sort_by_key(|item| (item.priority, item.counter));
            
            for (i, item) in items.iter().enumerate() {
                if i > 0 { write!(f, ", ")?; }
                write!(f, "({}, {})", item.priority, item.item)?;
            }
            write!(f, "])")
        }
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_priority_queue() {
        let mut pq = PriorityQueue::new();
        
        pq.enqueue("Low priority", 3);
        pq.enqueue("High priority", 1);
        pq.enqueue("Medium priority", 2);
        
        assert_eq!(pq.dequeue(), Some("High priority"));
        assert_eq!(pq.dequeue(), Some("Medium priority"));
        assert_eq!(pq.dequeue(), Some("Low priority"));
        assert_eq!(pq.dequeue(), None);
    }
}

fn main() {
    let mut pq = PriorityQueue::new();
    
    // Enqueue items with priorities
    pq.enqueue("Low priority task", 3);
    pq.enqueue("High priority task", 1);
    pq.enqueue("Medium priority task", 2);
    pq.enqueue("Another high priority", 1);
    
    println!("Priority Queue: {}", pq);
    
    // Dequeue items (should come out in priority order)
    while !pq.is_empty() {
        if let Some(item) = pq.dequeue() {
            println!("Dequeued: {}", item);
        }
    }
}
```

### 4. Double-ended Queue (Deque) Implementation

```rust
use std::collections::VecDeque;
use std::fmt;

pub struct Deque<T> {
    data: VecDeque<T>,
}

impl<T> Deque<T> {
    pub fn new() -> Self {
        Deque {
            data: VecDeque::new(),
        }
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        Deque {
            data: VecDeque::with_capacity(capacity),
        }
    }
    
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    pub fn add_front(&mut self, item: T) {
        self.data.push_front(item);
    }
    
    pub fn add_rear(&mut self, item: T) {
        self.data.push_back(item);
    }
    
    pub fn remove_front(&mut self) -> Option<T> {
        self.data.pop_front()
    }
    
    pub fn remove_rear(&mut self) -> Option<T> {
        self.data.pop_back()
    }
    
    pub fn front(&self) -> Option<&T> {
        self.data.front()
    }
    
    pub fn rear(&self) -> Option<&T> {
        self.data.back()
    }
}

impl<T: fmt::Display> fmt::Display for Deque<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Deque([")?;
        for (i, item) in self.data.iter().enumerate() {
            if i > 0 { write!(f, ", ")?; }
            write!(f, "{}", item)?;
        }
        write!(f, "])")
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_deque() {
        let mut dq = Deque::new();
        
        dq.add_rear(1);
        dq.add_rear(2);
        dq.add_front(0);
        dq.add_front(-1);
        
        assert_eq!(dq.len(), 4);
        assert_eq!(dq.front(), Some(&-1));
        assert_eq!(dq.rear(), Some(&2));
        
        assert_eq!(dq.remove_front(), Some(-1));
        assert_eq!(dq.remove_rear(), Some(2));
        assert_eq!(dq.len(), 2);
    }
}

fn main() {
    let mut dq = Deque::new();
    
    // Test adding to both ends
    dq.add_rear(1);
    dq.add_rear(2);
    dq.add_front(0);
    dq.add_front(-1);
    
    println!("Deque after additions: {}", dq);
    
    // Test removing from both ends
    if let Some(front) = dq.remove_front() {
        println!("Remove front: {}", front);
    }
    
    if let Some(rear) = dq.remove_rear() {
        println!("Remove rear: {}", rear);
    }
    
    println!("Final deque: {}", dq);
}
```

## Performance Comparison

### Time Complexities

| Operation | Array-based | Linked List | Priority Queue | Deque |
|-----------|-------------|-------------|----------------|-------|
| Enqueue   | O(1)*       | O(1)        | O(log n)       | O(1)  |
| Dequeue   | O(1)*       | O(1)        | O(log n)       | O(1)  |
| Front     | O(1)        | O(1)        | O(1)           | O(1)  |

*Amortized time complexity due to dynamic resizing

### Space Complexities

| Implementation | Space Complexity | Notes |
|----------------|------------------|-------|
| Array-based    | O(n)             | May have unused space due to resizing |
| Linked List    | O(n)             | Extra memory for pointers |
| Priority Queue | O(n)             | Heap structure overhead |
| Deque          | O(n)             | Similar to array-based |

### Memory Usage Comparison

**Array-based Queue:**
- Pros: Cache-friendly, predictable memory layout
- Cons: May waste space during resizing, requires copying during resize

**Linked List Queue:**
- Pros: No wasted space, no copying needed
- Cons: Poor cache locality, extra memory for pointers

**Priority Queue:**
- Pros: Efficient for priority-based operations
- Cons: Higher overhead per operation, more complex

**Deque:**
- Pros: Versatile, efficient for both ends
- Cons: More complex implementation

## Use Cases and Applications

### Simple Queue
- **Task scheduling** in operating systems
- **Breadth-First Search** algorithms
- **Print job management**
- **Buffer for producer-consumer** problems
- **Handling requests** in web servers

### Priority Queue
- **Dijkstra's shortest path** algorithm
- **Huffman coding** for data compression
- **A* pathfinding** algorithm
- **Process scheduling** with priorities
- **Merge k sorted lists**

### Deque
- **Palindrome checking**
- **Sliding window maximum** problems
- **Undo operations** in applications
- **Browser history** navigation
- **Implementing other data structures**

## Best Practices

### Choosing the Right Implementation

1. **Use Array-based Queue when:**
   - You need predictable performance
   - Memory usage is a concern
   - Cache performance is important

2. **Use Linked List Queue when:**
   - Queue size varies significantly
   - You want to avoid copying overhead
   - Memory is fragmented

3. **Use Priority Queue when:**
   - Elements need to be processed by priority
   - Implementing graph algorithms
   - Task scheduling with priorities

4. **Use Deque when:**
   - You need insertion/deletion from both ends
   - Implementing sliding window algorithms
   - Building other data structures

### Performance Optimization Tips

1. **Pre-allocate capacity** when possible to avoid resizing
2. **Use appropriate data types** for your use case
3. **Consider thread safety** requirements for concurrent applications
4. **Profile your application** to identify bottlenecks
5. **Choose built-in implementations** when they meet your needs

### Error Handling

1. **Always check for empty queues** before dequeue operations
2. **Handle memory allocation failures** gracefully
3. **Use Result/Option types** in Rust for safe error handling
4. **Provide clear error messages** for debugging

### Memory Management

1. **Clean up resources** properly (especially in manual memory management)
2. **Avoid memory leaks** in linked list implementations
3. **Consider using smart pointers** in C++/Rust
4. **Monitor memory usage** in production applications

## Advanced Queue Concepts

### Thread-Safe Queues

For concurrent programming, queues need to be thread-safe. Here are implementations for both languages:

#### Python Thread-Safe Queue

```python
import threading
from collections import deque
from typing import Any, Optional


class ThreadSafeQueue:
    """Thread-safe queue implementation using locks."""
    
    def __init__(self, maxsize: int = 0):
        self._queue = deque()
        self._maxsize = maxsize
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    def qsize(self) -> int:
        """Return the approximate size of the queue."""
        with self._lock:
            return len(self._queue)
    
    def empty(self) -> bool:
        """Return True if the queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def full(self) -> bool:
        """Return True if the queue is full."""
        with self._lock:
            if self._maxsize <= 0:
                return False
            return len(self._queue) >= self._maxsize
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """Put an item into the queue."""
        with self._not_full:
            if self._maxsize > 0:
                if not block:
                    if len(self._queue) >= self._maxsize:
                        raise Exception("Queue is full")
                elif timeout is None:
                    while len(self._queue) >= self._maxsize:
                        self._not_full.wait()
                else:
                    if not self._not_full.wait_for(lambda: len(self._queue) < self._maxsize, timeout):
                        raise Exception("Queue is full")
            
            self._queue.append(item)
            self._not_empty.notify()
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Remove and return an item from the queue."""
        with self._not_empty:
            if not block:
                if len(self._queue) == 0:
                    raise Exception("Queue is empty")
            elif timeout is None:
                while len(self._queue) == 0:
                    self._not_empty.wait()
            else:
                if not self._not_empty.wait_for(lambda: len(self._queue) > 0, timeout):
                    raise Exception("Queue is empty")
            
            item = self._queue.popleft()
            self._not_full.notify()
            return item
    
    def put_nowait(self, item: Any) -> None:
        """Put an item without blocking."""
        self.put(item, block=False)
    
    def get_nowait(self) -> Any:
        """Get an item without blocking."""
        return self.get(block=False)


# Example usage
import time
import threading

def producer(queue, name, items):
    """Producer function for testing."""
    for item in items:
        queue.put(f"{name}: {item}")
        print(f"Produced: {name}: {item}")
        time.sleep(0.1)

def consumer(queue, name, count):
    """Consumer function for testing."""
    for _ in range(count):
        item = queue.get()
        print(f"Consumed by {name}: {item}")
        time.sleep(0.15)

if __name__ == "__main__":
    # Test thread-safe queue
    queue = ThreadSafeQueue(maxsize=5)
    
    # Create producer and consumer threads
    producer_thread1 = threading.Thread(target=producer, args=(queue, "Producer1", range(5)))
    producer_thread2 = threading.Thread(target=producer, args=(queue, "Producer2", range(5, 10)))
    consumer_thread1 = threading.Thread(target=consumer, args=(queue, "Consumer1", 5))
    consumer_thread2 = threading.Thread(target=consumer, args=(queue, "Consumer2", 5))
    
    # Start threads
    threads = [producer_thread1, producer_thread2, consumer_thread1, consumer_thread2]
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
```

#### Rust Thread-Safe Queue

```rust
use std::collections::VecDeque;
use std::sync::{Arc, Condvar, Mutex};
use std::time::Duration;

pub struct ThreadSafeQueue<T> {
    inner: Arc<ThreadSafeQueueInner<T>>,
}

struct ThreadSafeQueueInner<T> {
    queue: Mutex<VecDeque<T>>,
    not_empty: Condvar,
    not_full: Condvar,
    max_size: Option<usize>,
}

impl<T> ThreadSafeQueue<T> {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(ThreadSafeQueueInner {
                queue: Mutex::new(VecDeque::new()),
                not_empty: Condvar::new(),
                not_full: Condvar::new(),
                max_size: None,
            }),
        }
    }
    
    pub fn with_capacity(max_size: usize) -> Self {
        Self {
            inner: Arc::new(ThreadSafeQueueInner {
                queue: Mutex::new(VecDeque::with_capacity(max_size)),
                not_empty: Condvar::new(),
                not_full: Condvar::new(),
                max_size: Some(max_size),
            }),
        }
    }
    
    pub fn push(&self, item: T) -> Result<(), &'static str> {
        let mut queue = self.inner.queue.lock().unwrap();
        
        // Wait if queue is full
        if let Some(max_size) = self.inner.max_size {
            while queue.len() >= max_size {
                queue = self.inner.not_full.wait(queue).unwrap();
            }
        }
        
        queue.push_back(item);
        self.inner.not_empty.notify_one();
        Ok(())
    }
    
    pub fn pop(&self) -> Result<T, &'static str> {
        let mut queue = self.inner.queue.lock().unwrap();
        
        // Wait if queue is empty
        while queue.is_empty() {
            queue = self.inner.not_empty.wait(queue).unwrap();
        }
        
        let item = queue.pop_front().unwrap();
        self.inner.not_full.notify_one();
        Ok(item)
    }
    
    pub fn try_push(&self, item: T) -> Result<(), &'static str> {
        let mut queue = self.inner.queue.lock().unwrap();
        
        if let Some(max_size) = self.inner.max_size {
            if queue.len() >= max_size {
                return Err("Queue is full");
            }
        }
        
        queue.push_back(item);
        self.inner.not_empty.notify_one();
        Ok(())
    }
    
    pub fn try_pop(&self) -> Result<T, &'static str> {
        let mut queue = self.inner.queue.lock().unwrap();
        
        if queue.is_empty() {
            return Err("Queue is empty");
        }
        
        let item = queue.pop_front().unwrap();
        self.inner.not_full.notify_one();
        Ok(item)
    }
    
    pub fn len(&self) -> usize {
        let queue = self.inner.queue.lock().unwrap();
        queue.len()
    }
    
    pub fn is_empty(&self) -> bool {
        let queue = self.inner.queue.lock().unwrap();
        queue.is_empty()
    }
}

impl<T> Clone for ThreadSafeQueue<T> {
    fn clone(&self) -> Self {
        Self {
            inner: Arc::clone(&self.inner),
        }
    }
}

// Example usage
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn main() {
    let queue = ThreadSafeQueue::with_capacity(5);
    let mut handles = vec![];
    
    // Producer threads
    for i in 0..2 {
        let q = queue.clone();
        let handle = thread::spawn(move || {
            for j in 0..5 {
                let item = format!("Producer{}-Item{}", i, j);
                q.push(item.clone()).unwrap();
                println!("Produced: {}", item);
                thread::sleep(Duration::from_millis(100));
            }
        });
        handles.push(handle);
    }
    
    // Consumer threads
    for i in 0..2 {
        let q = queue.clone();
        let handle = thread::spawn(move || {
            for _ in 0..5 {
                match q.pop() {
                    Ok(item) => {
                        println!("Consumer{} consumed: {}", i, item);
                        thread::sleep(Duration::from_millis(150));
                    }
                    Err(e) => println!("Error: {}", e),
                }
            }
        });
        handles.push(handle);
    }
    
    // Wait for all threads to complete
    for handle in handles {
        handle.join().unwrap();
    }
}
```

### Circular Buffer Implementation

A circular buffer is a fixed-size queue that wraps around when full, making it ideal for streaming data.

#### Python Circular Buffer

```python
class CircularBuffer:
    """Fixed-size circular buffer implementation."""
    
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self._buffer = [None] * capacity
        self._capacity = capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._full = False
    
    def __len__(self):
        return self._size
    
    def __bool__(self):
        return self._size > 0
    
    @property
    def capacity(self):
        return self._capacity
    
    @property
    def is_full(self):
        return self._full
    
    @property
    def is_empty(self):
        return self._size == 0
    
    def enqueue(self, item):
        """Add item to buffer. Overwrites oldest if full."""
        self._buffer[self._tail] = item
        
        if self._full:
            self._head = (self._head + 1) % self._capacity
        else:
            self._size += 1
            if self._size == self._capacity:
                self._full = True
        
        self._tail = (self._tail + 1) % self._capacity
    
    def dequeue(self):
        """Remove and return oldest item."""
        if self.is_empty:
            raise IndexError("Buffer is empty")
        
        item = self._buffer[self._head]
        self._buffer[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        self._full = False
        
        return item
    
    def peek(self):
        """Return oldest item without removing it."""
        if self.is_empty:
            raise IndexError("Buffer is empty")
        return self._buffer[self._head]
    
    def to_list(self):
        """Convert buffer contents to list in order."""
        if self.is_empty:
            return []
        
        result = []
        idx = self._head
        for _ in range(self._size):
            result.append(self._buffer[idx])
            idx = (idx + 1) % self._capacity
        
        return result
    
    def __str__(self):
        return f"CircularBuffer({self.to_list()})"


# Example usage
if __name__ == "__main__":
    buffer = CircularBuffer(5)
    
    # Fill buffer
    for i in range(7):  # More than capacity
        buffer.enqueue(i)
        print(f"Enqueued {i}: {buffer} (full: {buffer.is_full})")
    
    # Empty buffer
    while buffer:
        item = buffer.dequeue()
        print(f"Dequeued {item}: {buffer}")
```

#### Rust Circular Buffer

```rust
use std::fmt;

pub struct CircularBuffer<T: Clone> {
    buffer: Vec<Option<T>>,
    capacity: usize,
    head: usize,
    tail: usize,
    size: usize,
    full: bool,
}

impl<T: Clone> CircularBuffer<T> {
    pub fn new(capacity: usize) -> Self {
        if capacity == 0 {
            panic!("Capacity must be greater than 0");
        }
        
        CircularBuffer {
            buffer: vec![None; capacity],
            capacity,
            head: 0,
            tail: 0,
            size: 0,
            full: false,
        }
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn capacity(&self) -> usize {
        self.capacity
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    pub fn is_full(&self) -> bool {
        self.full
    }
    
    pub fn enqueue(&mut self, item: T) {
        self.buffer[self.tail] = Some(item);
        
        if self.full {
            self.head = (self.head + 1) % self.capacity;
        } else {
            self.size += 1;
            if self.size == self.capacity {
                self.full = true;
            }
        }
        
        self.tail = (self.tail + 1) % self.capacity;
    }
    
    pub fn dequeue(&mut self) -> Option<T> {
        if self.is_empty() {
            return None;
        }
        
        let item = self.buffer[self.head].take();
        self.head = (self.head + 1) % self.capacity;
        self.size -= 1;
        self.full = false;
        
        item
    }
    
    pub fn peek(&self) -> Option<&T> {
        if self.is_empty() {
            None
        } else {
            self.buffer[self.head].as_ref()
        }
    }
    
    pub fn to_vec(&self) -> Vec<T> {
        if self.is_empty() {
            return Vec::new();
        }
        
        let mut result = Vec::with_capacity(self.size);
        let mut idx = self.head;
        
        for _ in 0..self.size {
            if let Some(ref item) = self.buffer[idx] {
                result.push(item.clone());
            }
            idx = (idx + 1) % self.capacity;
        }
        
        result
    }
}

impl<T: Clone + fmt::Display> fmt::Display for CircularBuffer<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let items = self.to_vec();
        write!(f, "CircularBuffer([")?;
        for (i, item) in items.iter().enumerate() {
            if i > 0 { write!(f, ", ")?; }
            write!(f, "{}", item)?;
        }
        write!(f, "])")
    }
}

// Example usage
fn main() {
    let mut buffer = CircularBuffer::new(5);
    
    // Fill buffer (more than capacity)
    for i in 0..7 {
        buffer.enqueue(i);
        println!("Enqueued {}: {} (full: {})", i, buffer, buffer.is_full());
    }
    
    // Empty buffer
    while !buffer.is_empty() {
        if let Some(item) = buffer.dequeue() {
            println!("Dequeued {}: {}", item, buffer);
        }
    }
}
```

### Benchmarking and Performance Testing

#### Python Benchmarking

```python
import time
import random
from collections import deque
import matplotlib.pyplot as plt
import numpy as np

def benchmark_queue_implementations():
    """Benchmark different queue implementations."""
    
    # Test different sizes
    sizes = [100, 1000, 10000, 100000]
    operations_per_size = 10000
    
    results = {
        'Array Queue': [],
        'Linked Queue': [],
        'Python deque': [],
        'List (inefficient)': []
    }
    
    for size in sizes:
        print(f"Testing with size: {size}")
        
        # Test Array Queue
        start_time = time.time()
        array_queue = ArrayQueue()
        
        # Fill queue
        for i in range(size):
            array_queue.enqueue(i)
        
        # Mixed operations
        for _ in range(operations_per_size):
            if random.random() < 0.5:
                array_queue.enqueue(random.randint(1, 1000))
            else:
                if not array_queue.is_empty():
                    array_queue.dequeue()
        
        array_time = time.time() - start_time
        results['Array Queue'].append(array_time)
        
        # Test Linked Queue
        start_time = time.time()
        linked_queue = LinkedQueue()
        
        for i in range(size):
            linked_queue.enqueue(i)
        
        for _ in range(operations_per_size):
            if random.random() < 0.5:
                linked_queue.enqueue(random.randint(1, 1000))
            else:
                if not linked_queue.is_empty():
                    linked_queue.dequeue()
        
        linked_time = time.time() - start_time
        results['Linked Queue'].append(linked_time)
        
        # Test Python deque
        start_time = time.time()
        python_deque = deque()
        
        for i in range(size):
            python_deque.append(i)
        
        for _ in range(operations_per_size):
            if random.random() < 0.5:
                python_deque.append(random.randint(1, 1000))
            else:
                if python_deque:
                    python_deque.popleft()
        
        deque_time = time.time() - start_time
        results['Python deque'].append(deque_time)
        
        # Test inefficient list implementation
        start_time = time.time()
        list_queue = []
        
        for i in range(size):
            list_queue.append(i)
        
        for _ in range(operations_per_size):
            if random.random() < 0.5:
                list_queue.append(random.randint(1, 1000))
            else:
                if list_queue:
                    list_queue.pop(0)  # Inefficient O(n) operation
        
        list_time = time.time() - start_time
        results['List (inefficient)'].append(list_time)
    
    return sizes, results

def plot_benchmark_results(sizes, results):
    """Plot benchmark results."""
    plt.figure(figsize=(12, 8))
    
    for implementation, times in results.items():
        plt.plot(sizes, times, marker='o', label=implementation, linewidth=2)
    
    plt.xlabel('Queue Size')
    plt.ylabel('Time (seconds)')
    plt.title('Queue Implementation Performance Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.xscale('log')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Note: This requires the ArrayQueue and LinkedQueue classes from earlier
    sizes, results = benchmark_queue_implementations()
    plot_benchmark_results(sizes, results)
    
    # Print numerical results
    print("\nBenchmark Results:")
    print("-" * 50)
    for impl, times in results.items():
        print(f"{impl:20} : {times}")
```

#### Rust Benchmarking

```rust
// Add to Cargo.toml:
// [dev-dependencies]
// criterion = "0.3"

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use std::collections::VecDeque;

// Include your queue implementations here

fn benchmark_enqueue_dequeue(c: &mut Criterion) {
    let mut group = c.benchmark_group("queue_operations");
    
    // Benchmark Array Queue
    group.bench_function("array_queue", |b| {
        b.iter(|| {
            let mut queue = ArrayQueue::new();
            for i in 0..1000 {
                queue.enqueue(black_box(i));
            }
            while !queue.is_empty() {
                queue.dequeue();
            }
        })
    });
    
    // Benchmark Linked Queue
    group.bench_function("linked_queue", |b| {
        b.iter(|| {
            let mut queue = LinkedQueue::new();
            for i in 0..1000 {
                queue.enqueue(black_box(i));
            }
            while !queue.is_empty() {
                queue.dequeue();
            }
        })
    });
    
    // Benchmark VecDeque
    group.bench_function("vec_deque", |b| {
        b.iter(|| {
            let mut queue = VecDeque::new();
            for i in 0..1000 {
                queue.push_back(black_box(i));
            }
            while !queue.is_empty() {
                queue.pop_front();
            }
        })
    });
    
    group.finish();
}

fn benchmark_mixed_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("mixed_operations");
    
    group.bench_function("array_queue_mixed", |b| {
        b.iter(|| {
            let mut queue = ArrayQueue::new();
            for i in 0..500 {
                queue.enqueue(black_box(i));
                if i % 3 == 0 && !queue.is_empty() {
                    queue.dequeue();
                }
            }
        })
    });
    
    group.bench_function("linked_queue_mixed", |b| {
        b.iter(|| {
            let mut queue = LinkedQueue::new();
            for i in 0..500 {
                queue.enqueue(black_box(i));
                if i % 3 == 0 && !queue.is_empty() {
                    queue.dequeue();
                }
            }
        })
    });
    
    group.finish();
}

criterion_group!(benches, benchmark_enqueue_dequeue, benchmark_mixed_operations);
criterion_main!(benches);
```

## Conclusion

Queues are fundamental data structures with wide-ranging applications. The choice of implementation depends on your specific requirements:

- **Array-based queues** offer excellent cache performance and are ideal for most general-purpose applications
- **Linked list queues** provide dynamic sizing without the need for reallocation
- **Priority queues** are essential for algorithms that need to process elements by importance
- **Deques** offer flexibility for algorithms that need access to both ends
- **Thread-safe queues** are crucial for concurrent programming
- **Circular buffers** are perfect for streaming data and fixed-size applications

### Key Takeaways

1. **Performance matters**: Choose the right implementation based on your performance requirements and usage patterns
2. **Thread safety**: Consider concurrency requirements early in your design
3. **Memory management**: Be aware of memory allocation patterns and their impact on performance
4. **Built-in solutions**: Often, language-provided implementations (like Python's `deque` or Rust's `VecDeque`) are optimized and battle-tested
5. **Profiling**: Always measure performance in your specific use case rather than relying solely on theoretical complexities

### Further Reading

- **Algorithm textbooks**: "Introduction to Algorithms" by CLRS for theoretical foundations
- **Language documentation**: Official documentation for built-in queue implementations
- **Research papers**: Academic papers on lock-free and wait-free queue implementations
- **Performance analysis**: Papers on cache-friendly data structure design
- **Concurrent programming**: Books on thread-safe data structure design

This comprehensive guide provides you with the knowledge and implementations needed to effectively use queues in your projects, whether you're building simple applications or complex concurrent systems.

I'll create a detailed ASCII diagram showing how queues work with step-by-step operations.I've created a comprehensive ASCII diagram showing how queues work step by step! The diagram illustrates:

1. **Queue Basics** - Shows the FIFO (First In, First Out) principle with clear FRONT and REAR pointers
2. **Step-by-Step Operations** - Demonstrates enqueue and dequeue operations with visual state changes
3. **Index Tracking** - Shows how front and rear indices move as elements are added and removed
4. **Circular Implementation** - Explains how queues can wrap around to utilize space efficiently
5. **Operation Summaries** - Visual representations of the three main queue operations
6. **Practical Information** - Time complexity and real-world applications

The diagram uses clear ASCII art with arrows, boxes, and step-by-step explanations to make the queue concept easy to understand. Each step shows the exact state of the queue, including which positions are occupied, empty, or marked as removed (X).

# Queue Data Structure - Step by Step Operations

## What is a Queue?
A Queue is a linear data structure that follows **FIFO (First In, First Out)** principle.
- Elements are added at the **REAR** (back)
- Elements are removed from the **FRONT** (front)

---

## Step 1: Empty Queue
```
FRONT                           REAR
  ↓                               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│     │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Status**: Queue is empty  
**Front Index**: 0  
**Rear Index**: 0  
**Size**: 0

---

## Step 2: Enqueue(10) - Add first element
```
FRONT                           REAR
  ↓                               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ 10  │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operation**: enqueue(10)  
**Front Index**: 0  
**Rear Index**: 0  
**Size**: 1

---

## Step 3: Enqueue(20) - Add second element
```
FRONT                           REAR
  ↓                               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ 10  │ 20  │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operation**: enqueue(20)  
**Front Index**: 0  
**Rear Index**: 1  
**Size**: 2

---

## Step 4: Enqueue(30) and Enqueue(40)
```
FRONT                           REAR
  ↓                               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ 10  │ 20  │ 30  │ 40  │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operations**: enqueue(30), enqueue(40)  
**Front Index**: 0  
**Rear Index**: 3  
**Size**: 4

---

## Step 5: Dequeue() - Remove first element
```
      FRONT                     REAR
        ↓                         ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  X  │ 20  │ 30  │ 40  │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operation**: dequeue() → returns 10  
**Front Index**: 1  
**Rear Index**: 3  
**Size**: 3

---

## Step 6: Enqueue(50) and Enqueue(60)
```
      FRONT                           REAR
        ↓                               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  X  │ 20  │ 30  │ 40  │ 50  │ 60  │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operations**: enqueue(50), enqueue(60)  
**Front Index**: 1  
**Rear Index**: 5  
**Size**: 5

---

## Step 7: Multiple Dequeue Operations
```
                  FRONT           REAR
                    ↓               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  X  │  X  │  X  │ 40  │ 50  │ 60  │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operations**: dequeue() → 20, dequeue() → 30  
**Front Index**: 3  
**Rear Index**: 5  
**Size**: 3

---

## Circular Queue Implementation
When rear reaches the end, it wraps around to the beginning:

### Before Enqueue(70) - Queue Full?
```
                  FRONT           REAR
                    ↓               ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  X  │  X  │  X  │ 40  │ 50  │ 60  │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```

### After Enqueue(70) - Circular Wrap
```
REAR            FRONT                 
  ↓               ↓                   
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ 70  │  X  │  X  │ 40  │ 50  │ 60  │
└─────┴─────┴─────┴─────┴─────┴─────┘
  0     1     2     3     4     5
```
**Operation**: enqueue(70) - wraps to index 0  
**Front Index**: 3  
**Rear Index**: 0  
**Size**: 4

---

## Key Queue Operations Summary

### 1. Enqueue (Insert)
```
┌─ REAR moves forward ─────────────┐
│                                  │
│  ┌─────┬─────┬─────┬─────┐      │
│  │  A  │  B  │  C  │ NEW │ ←────┘
│  └─────┴─────┴─────┴─────┘
│    ↑
└─ FRONT stays same
```

### 2. Dequeue (Remove)
```
┌─ FRONT moves forward ────────────┐
│                                  ↓
│  ┌─────┬─────┬─────┬─────┐
└→ │  X  │  B  │  C  │  D  │
   └─────┴─────┴─────┴─────┘
          ↑
    REAR stays same
```

### 3. Peek/Front (View first element)
```
   ┌─ Returns this value ─┐
   │                      ↓
   │  ┌─────┬─────┬─────┬─────┐
   └→ │  A  │  B  │  C  │  D  │
      └─────┴─────┴─────┴─────┘
        ↑                 ↑
     FRONT             REAR
```

---

## Time Complexity
- **Enqueue**: O(1)
- **Dequeue**: O(1)  
- **Peek**: O(1)
- **IsEmpty**: O(1)

## Common Applications
- Task scheduling in operating systems
- Breadth-First Search (BFS)
- Print job management
- Call center systems
- Buffer for data streams