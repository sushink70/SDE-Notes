# Comprehensive Guide to Heap Data Structure Implementation

## Table of Contents
1. [Introduction to Heaps](#introduction-to-heaps)
2. [Types of Heaps](#types-of-heaps)
3. [Heap Properties](#heap-properties)
4. [Array Representation](#array-representation)
5. [Core Operations](#core-operations)
6. [Python Implementation](#python-implementation)
7. [Rust Implementation](#rust-implementation)
8. [Time and Space Complexity](#time-and-space-complexity)
9. [Use Cases and Applications](#use-cases-and-applications)
10. [Advanced Variations](#advanced-variations)

## Introduction to Heaps

A **heap** is a specialized tree-based data structure that satisfies the heap property. It's commonly implemented as a complete binary tree and is fundamental to many algorithms, including heap sort and priority queues.

### Key Characteristics:
- **Complete Binary Tree**: All levels are fully filled except possibly the last level, which is filled from left to right
- **Heap Property**: Parent nodes maintain a specific ordering relationship with their children
- **Efficient Operations**: Insertion and deletion in O(log n) time
- **Array-Based Storage**: Can be efficiently stored in an array without explicit pointers

## Types of Heaps

### 1. Max Heap
- **Property**: Parent ≥ Children
- **Root**: Contains the maximum element
- **Use Case**: Priority queues where highest priority items are processed first

### 2. Min Heap
- **Property**: Parent ≤ Children
- **Root**: Contains the minimum element
- **Use Case**: Priority queues where lowest priority items are processed first

## Heap Properties

### Structural Property
- Must be a **complete binary tree**
- All levels filled except possibly the last
- Last level filled from left to right

### Ordering Property
- **Max Heap**: Every parent node is greater than or equal to its children
- **Min Heap**: Every parent node is less than or equal to its children

## Array Representation

Heaps are efficiently represented using arrays where:
- **Root**: Index 0
- **Parent of node i**: Index `(i-1)//2`
- **Left child of node i**: Index `2*i + 1`
- **Right child of node i**: Index `2*i + 2`

```
Array: [90, 80, 70, 40, 30, 20, 60]

Tree Representation:
       90
      /  \
    80    70
   / \   /  \
  40 30 20  60
```

## Core Operations

### 1. Insert (Push)
1. Add element at the end of the array
2. **Heapify Up**: Compare with parent and swap if heap property is violated
3. Repeat until heap property is satisfied or reach root

### 2. Extract Max/Min (Pop)
1. Store root value (max/min element)
2. Replace root with last element
3. Remove last element
4. **Heapify Down**: Compare with children and swap with appropriate child
5. Repeat until heap property is satisfied or reach leaf

### 3. Peek
- Return root element without removing it
- O(1) operation

### 4. Build Heap
- Convert arbitrary array into heap
- Start from last non-leaf node and heapify down

## Python Implementation

```python
class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def parent(self, i):
        return (i - 1) // 2
    
    def left_child(self, i):
        return 2 * i + 1
    
    def right_child(self, i):
        return 2 * i + 2
    
    def has_parent(self, i):
        return self.parent(i) >= 0
    
    def has_left_child(self, i):
        return self.left_child(i) < len(self.heap)
    
    def has_right_child(self, i):
        return self.right_child(i) < len(self.heap)
    
    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
    
    def insert(self, value):
        """Insert a new element into the heap"""
        self.heap.append(value)
        self.heapify_up(len(self.heap) - 1)
    
    def heapify_up(self, i):
        """Restore heap property by moving element up"""
        while (self.has_parent(i) and 
               self.heap[self.parent(i)] < self.heap[i]):
            self.swap(i, self.parent(i))
            i = self.parent(i)
    
    def extract_max(self):
        """Remove and return the maximum element"""
        if not self.heap:
            raise IndexError("Heap is empty")
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        max_value = self.heap[0]
        self.heap[0] = self.heap.pop()  # Replace root with last element
        self.heapify_down(0)
        return max_value
    
    def heapify_down(self, i):
        """Restore heap property by moving element down"""
        while self.has_left_child(i):
            larger_child_idx = self.left_child(i)
            
            # Find the larger child
            if (self.has_right_child(i) and 
                self.heap[self.right_child(i)] > self.heap[larger_child_idx]):
                larger_child_idx = self.right_child(i)
            
            # If heap property is satisfied, break
            if self.heap[i] >= self.heap[larger_child_idx]:
                break
            
            self.swap(i, larger_child_idx)
            i = larger_child_idx
    
    def peek(self):
        """Return the maximum element without removing it"""
        if not self.heap:
            raise IndexError("Heap is empty")
        return self.heap[0]
    
    def size(self):
        return len(self.heap)
    
    def is_empty(self):
        return len(self.heap) == 0
    
    def build_heap(self, arr):
        """Build heap from arbitrary array"""
        self.heap = arr[:]
        # Start from last non-leaf node and heapify down
        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self.heapify_down(i)

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def parent(self, i):
        return (i - 1) // 2
    
    def left_child(self, i):
        return 2 * i + 1
    
    def right_child(self, i):
        return 2 * i + 2
    
    def has_parent(self, i):
        return self.parent(i) >= 0
    
    def has_left_child(self, i):
        return self.left_child(i) < len(self.heap)
    
    def has_right_child(self, i):
        return self.right_child(i) < len(self.heap)
    
    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
    
    def insert(self, value):
        """Insert a new element into the heap"""
        self.heap.append(value)
        self.heapify_up(len(self.heap) - 1)
    
    def heapify_up(self, i):
        """Restore heap property by moving element up"""
        while (self.has_parent(i) and 
               self.heap[self.parent(i)] > self.heap[i]):
            self.swap(i, self.parent(i))
            i = self.parent(i)
    
    def extract_min(self):
        """Remove and return the minimum element"""
        if not self.heap:
            raise IndexError("Heap is empty")
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        min_value = self.heap[0]
        self.heap[0] = self.heap.pop()
        self.heapify_down(0)
        return min_value
    
    def heapify_down(self, i):
        """Restore heap property by moving element down"""
        while self.has_left_child(i):
            smaller_child_idx = self.left_child(i)
            
            # Find the smaller child
            if (self.has_right_child(i) and 
                self.heap[self.right_child(i)] < self.heap[smaller_child_idx]):
                smaller_child_idx = self.right_child(i)
            
            # If heap property is satisfied, break
            if self.heap[i] <= self.heap[smaller_child_idx]:
                break
            
            self.swap(i, smaller_child_idx)
            i = smaller_child_idx
    
    def peek(self):
        """Return the minimum element without removing it"""
        if not self.heap:
            raise IndexError("Heap is empty")
        return self.heap[0]
    
    def size(self):
        return len(self.heap)
    
    def is_empty(self):
        return len(self.heap) == 0
    
    def build_heap(self, arr):
        """Build heap from arbitrary array"""
        self.heap = arr[:]
        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self.heapify_down(i)

# Example usage and testing
def test_heap_implementations():
    print("Testing Max Heap:")
    max_heap = MaxHeap()
    
    # Test insertions
    elements = [10, 20, 15, 40, 50, 100, 25, 45]
    for elem in elements:
        max_heap.insert(elem)
        print(f"Inserted {elem}, heap: {max_heap.heap}")
    
    print(f"Max element (peek): {max_heap.peek()}")
    
    # Test extractions
    print("\nExtracting elements:")
    while not max_heap.is_empty():
        max_val = max_heap.extract_max()
        print(f"Extracted: {max_val}, remaining heap: {max_heap.heap}")
    
    print("\n" + "="*50)
    print("Testing Min Heap:")
    min_heap = MinHeap()
    
    # Test build_heap
    arr = [4, 10, 3, 5, 1, 6, 2, 7, 8, 9]
    min_heap.build_heap(arr)
    print(f"Built heap from {arr}")
    print(f"Resulting heap: {min_heap.heap}")
    
    # Test extractions
    print("\nExtracting elements:")
    extracted = []
    while not min_heap.is_empty():
        min_val = min_heap.extract_min()
        extracted.append(min_val)
    print(f"Extracted in order: {extracted}")

if __name__ == "__main__":
    test_heap_implementations()
```

## Rust Implementation

```rust
use std::cmp::Ordering;
use std::fmt::Debug;

#[derive(Debug)]
pub struct MaxHeap<T> {
    data: Vec<T>,
}

impl<T: Ord + Clone + Debug> MaxHeap<T> {
    pub fn new() -> Self {
        MaxHeap { data: Vec::new() }
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        MaxHeap {
            data: Vec::with_capacity(capacity),
        }
    }
    
    pub fn from_vec(mut vec: Vec<T>) -> Self {
        let mut heap = MaxHeap { data: vec };
        heap.build_heap();
        heap
    }
    
    fn parent(&self, i: usize) -> Option<usize> {
        if i == 0 { None } else { Some((i - 1) / 2) }
    }
    
    fn left_child(&self, i: usize) -> Option<usize> {
        let left = 2 * i + 1;
        if left < self.data.len() { Some(left) } else { None }
    }
    
    fn right_child(&self, i: usize) -> Option<usize> {
        let right = 2 * i + 2;
        if right < self.data.len() { Some(right) } else { None }
    }
    
    pub fn push(&mut self, value: T) {
        self.data.push(value);
        self.heapify_up(self.data.len() - 1);
    }
    
    fn heapify_up(&mut self, mut i: usize) {
        while let Some(parent_idx) = self.parent(i) {
            if self.data[i] <= self.data[parent_idx] {
                break;
            }
            self.data.swap(i, parent_idx);
            i = parent_idx;
        }
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() {
            return None;
        }
        
        if self.data.len() == 1 {
            return self.data.pop();
        }
        
        let max_value = self.data.swap_remove(0);
        self.heapify_down(0);
        Some(max_value)
    }
    
    fn heapify_down(&mut self, mut i: usize) {
        loop {
            let mut largest = i;
            
            if let Some(left) = self.left_child(i) {
                if self.data[left] > self.data[largest] {
                    largest = left;
                }
            }
            
            if let Some(right) = self.right_child(i) {
                if self.data[right] > self.data[largest] {
                    largest = right;
                }
            }
            
            if largest == i {
                break;
            }
            
            self.data.swap(i, largest);
            i = largest;
        }
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }
    
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    pub fn capacity(&self) -> usize {
        self.data.capacity()
    }
    
    fn build_heap(&mut self) {
        if self.data.len() <= 1 {
            return;
        }
        
        // Start from the last non-leaf node
        let start = (self.data.len() - 2) / 2;
        for i in (0..=start).rev() {
            self.heapify_down(i);
        }
    }
    
    pub fn clear(&mut self) {
        self.data.clear();
    }
    
    // Convert to sorted vector (heap sort)
    pub fn into_sorted_vec(mut self) -> Vec<T> {
        let mut sorted = Vec::with_capacity(self.data.len());
        while let Some(max) = self.pop() {
            sorted.push(max);
        }
        sorted
    }
}

#[derive(Debug)]
pub struct MinHeap<T> {
    data: Vec<T>,
}

impl<T: Ord + Clone + Debug> MinHeap<T> {
    pub fn new() -> Self {
        MinHeap { data: Vec::new() }
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        MinHeap {
            data: Vec::with_capacity(capacity),
        }
    }
    
    pub fn from_vec(mut vec: Vec<T>) -> Self {
        let mut heap = MinHeap { data: vec };
        heap.build_heap();
        heap
    }
    
    fn parent(&self, i: usize) -> Option<usize> {
        if i == 0 { None } else { Some((i - 1) / 2) }
    }
    
    fn left_child(&self, i: usize) -> Option<usize> {
        let left = 2 * i + 1;
        if left < self.data.len() { Some(left) } else { None }
    }
    
    fn right_child(&self, i: usize) -> Option<usize> {
        let right = 2 * i + 2;
        if right < self.data.len() { Some(right) } else { None }
    }
    
    pub fn push(&mut self, value: T) {
        self.data.push(value);
        self.heapify_up(self.data.len() - 1);
    }
    
    fn heapify_up(&mut self, mut i: usize) {
        while let Some(parent_idx) = self.parent(i) {
            if self.data[i] >= self.data[parent_idx] {
                break;
            }
            self.data.swap(i, parent_idx);
            i = parent_idx;
        }
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() {
            return None;
        }
        
        if self.data.len() == 1 {
            return self.data.pop();
        }
        
        let min_value = self.data.swap_remove(0);
        self.heapify_down(0);
        Some(min_value)
    }
    
    fn heapify_down(&mut self, mut i: usize) {
        loop {
            let mut smallest = i;
            
            if let Some(left) = self.left_child(i) {
                if self.data[left] < self.data[smallest] {
                    smallest = left;
                }
            }
            
            if let Some(right) = self.right_child(i) {
                if self.data[right] < self.data[smallest] {
                    smallest = right;
                }
            }
            
            if smallest == i {
                break;
            }
            
            self.data.swap(i, smallest);
            i = smallest;
        }
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }
    
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    
    pub fn capacity(&self) -> usize {
        self.data.capacity()
    }
    
    fn build_heap(&mut self) {
        if self.data.len() <= 1 {
            return;
        }
        
        let start = (self.data.len() - 2) / 2;
        for i in (0..=start).rev() {
            self.heapify_down(i);
        }
    }
    
    pub fn clear(&mut self) {
        self.data.clear();
    }
    
    pub fn into_sorted_vec(mut self) -> Vec<T> {
        let mut sorted = Vec::with_capacity(self.data.len());
        while let Some(min) = self.pop() {
            sorted.push(min);
        }
        sorted
    }
}

// Priority Queue implementation using MinHeap
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Task {
    priority: i32,
    name: String,
}

impl Task {
    pub fn new(priority: i32, name: String) -> Self {
        Task { priority, name }
    }
}

impl Ord for Task {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse ordering for min-heap behavior with priorities
        // Lower priority number = higher priority
        other.priority.cmp(&self.priority)
    }
}

impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

// Example usage and tests
fn main() {
    println!("Testing Rust Heap Implementation");
    println!("================================");
    
    // Test MaxHeap
    println!("\n--- Max Heap Test ---");
    let mut max_heap = MaxHeap::new();
    
    let elements = vec![10, 20, 15, 40, 50, 100, 25, 45];
    for elem in &elements {
        max_heap.push(*elem);
        println!("Inserted {}, heap: {:?}", elem, max_heap.data);
    }
    
    println!("Max element (peek): {:?}", max_heap.peek());
    
    println!("\nExtracting elements:");
    let mut extracted_max = Vec::new();
    while let Some(max_val) = max_heap.pop() {
        extracted_max.push(max_val);
        println!("Extracted: {}, remaining: {:?}", max_val, max_heap.data);
    }
    println!("Extracted sequence: {:?}", extracted_max);
    
    // Test MinHeap
    println!("\n--- Min Heap Test ---");
    let arr = vec![4, 10, 3, 5, 1, 6, 2, 7, 8, 9];
    let mut min_heap = MinHeap::from_vec(arr.clone());
    println!("Built min heap from {:?}", arr);
    println!("Resulting heap: {:?}", min_heap.data);
    
    println!("\nExtracting elements:");
    let mut extracted_min = Vec::new();
    while let Some(min_val) = min_heap.pop() {
        extracted_min.push(min_val);
    }
    println!("Extracted sequence: {:?}", extracted_min);
    
    // Test Priority Queue
    println!("\n--- Priority Queue Test ---");
    let mut pq = MinHeap::new();
    
    pq.push(Task::new(3, "Low priority task".to_string()));
    pq.push(Task::new(1, "High priority task".to_string()));
    pq.push(Task::new(2, "Medium priority task".to_string()));
    pq.push(Task::new(1, "Another high priority".to_string()));
    
    println!("Processing tasks by priority:");
    while let Some(task) = pq.pop() {
        println!("Processing: {} (priority: {})", task.name, task.priority);
    }
    
    // Test heap sort
    println!("\n--- Heap Sort Test ---");
    let unsorted = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original: {:?}", unsorted);
    
    let max_heap = MaxHeap::from_vec(unsorted.clone());
    let sorted_desc = max_heap.into_sorted_vec();
    println!("Sorted (descending): {:?}", sorted_desc);
    
    let min_heap = MinHeap::from_vec(unsorted);
    let sorted_asc = min_heap.into_sorted_vec();
    println!("Sorted (ascending): {:?}", sorted_asc);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_max_heap_operations() {
        let mut heap = MaxHeap::new();
        assert!(heap.is_empty());
        
        heap.push(5);
        heap.push(10);
        heap.push(3);
        heap.push(8);
        
        assert_eq!(heap.len(), 4);
        assert_eq!(heap.peek(), Some(&10));
        
        assert_eq!(heap.pop(), Some(10));
        assert_eq!(heap.pop(), Some(8));
        assert_eq!(heap.pop(), Some(5));
        assert_eq!(heap.pop(), Some(3));
        assert_eq!(heap.pop(), None);
    }
    
    #[test]
    fn test_min_heap_operations() {
        let mut heap = MinHeap::new();
        
        heap.push(5);
        heap.push(10);
        heap.push(3);
        heap.push(8);
        
        assert_eq!(heap.peek(), Some(&3));
        
        assert_eq!(heap.pop(), Some(3));
        assert_eq!(heap.pop(), Some(5));
        assert_eq!(heap.pop(), Some(8));
        assert_eq!(heap.pop(), Some(10));
    }
    
    #[test]
    fn test_build_heap() {
        let arr = vec![4, 10, 3, 5, 1];
        let heap = MinHeap::from_vec(arr);
        assert_eq!(heap.peek(), Some(&1));
    }
}
```

## Time and Space Complexity

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| **Insert** | O(log n) | O(1) |
| **Extract Max/Min** | O(log n) | O(1) |
| **Peek** | O(1) | O(1) |
| **Build Heap** | O(n) | O(1) |
| **Heapify** | O(log n) | O(1) |
| **Delete** | O(log n) | O(1) |

### Space Complexity
- **Overall**: O(n) where n is the number of elements
- **Auxiliary**: O(1) for iterative implementation, O(log n) for recursive

## Use Cases and Applications

### 1. Priority Queues
- **Task scheduling** in operating systems
- **Event simulation** systems
- **A* pathfinding** algorithm

### 2. Heap Sort
- **In-place sorting** algorithm
- **Guaranteed O(n log n)** time complexity
- **Not stable** but memory efficient

### 3. Graph Algorithms
- **Dijkstra's shortest path** algorithm
- **Prim's minimum spanning tree**
- **Huffman coding** for data compression

### 4. Top-K Problems
- **Finding K largest/smallest** elements
- **Median finding** in streaming data
- **Merge K sorted lists**

### 5. Memory Management
- **Garbage collection** algorithms
- **Cache replacement** policies (LRU approximation)

## Advanced Variations

### 1. Binary Heap Variations
- **d-ary Heap**: Each node has d children instead of 2
- **Weak Heap**: Relaxed heap property for specific applications

### 2. Mergeable Heaps
- **Binomial Heap**: Supports efficient merge operation
- **Fibonacci Heap**: Optimal for decrease-key operations
- **Leftist Heap**: Supports efficient merging

### 3. Specialized Heaps
- **Min-Max Heap**: Supports both min and max operations
- **Interval Heap**: Double-ended priority queue
- **Skew Heap**: Self-adjusting heap with amortized efficiency

### Implementation Notes

#### Python Considerations
- Uses Python's built-in list for dynamic array
- Implements both max and min heap explicitly
- Includes comprehensive error handling
- Supports building heap from existing array

#### Rust Considerations
- Leverages Rust's type system and ownership model
- Uses generic types with trait bounds (`Ord + Clone + Debug`)
- Memory-safe implementation with no risk of buffer overflows
- Includes comprehensive test suite
- Supports custom types (demonstrated with Task priority queue)

### Performance Tips

1. **Pre-allocate capacity** when possible to avoid reallocations
2. **Use build_heap** instead of repeated insertions for better performance
3. **Consider d-ary heaps** for specific cache performance requirements
4. **Profile memory usage** for very large heaps

### Common Pitfalls

1. **Forgetting to maintain heap property** after modifications
2. **Index calculation errors** in array representation
3. **Not handling empty heap cases** properly
4. **Confusing min and max heap implementations**

This comprehensive guide provides both theoretical understanding and practical implementations of heap data structures in Python and Rust, covering everything from basic operations to advanced applications and performance considerations.

I'll create a detailed ASCII diagram showing how heap data structures work, including insertion, deletion, and heapify operations.I've created a comprehensive ASCII diagram showing how heap data structures work step by step. The diagram covers:

1. **Building a Max Heap** - Shows how elements are inserted and how heapify-up operations maintain the heap property
2. **Extract Maximum** - Demonstrates how the root is removed and heapify-down restores the heap
3. **Detailed Heapify Operations** - Step-by-step bubble up and bubble down processes
4. **Min Heap Example** - Complete walkthrough of building a min heap from an unsorted array
5. **Key Relationships** - Visual representation of parent-child index relationships

The diagrams use clear ASCII art to show both the array representation and the tree structure, making it easy to understand how heaps work internally. Each operation is broken down into individual steps with before/after states, helping visualize exactly how the heap property is maintained through insertions and deletions.

# Heap Data Structure - Step by Step ASCII Guide

## What is a Heap?
A heap is a complete binary tree that satisfies the heap property:
- **Max Heap**: Parent ≥ Children (root is maximum)
- **Min Heap**: Parent ≤ Children (root is minimum)

## Array Representation
For node at index `i`:
- Left child: `2i + 1`
- Right child: `2i + 2`
- Parent: `(i-1)/2`

---

## Step 1: Building a Max Heap from Empty

### Insert 50
```
Array: [50]
Index:  0

Tree:
    50
```

### Insert 30
```
Array: [50, 30]
Index:  0   1

Tree:
    50
   /
  30
```

### Insert 70 (Heapify Up Required!)
```
Before heapify:
Array: [50, 30, 70]
Index:  0   1   2

Tree:
    50
   /  \
  30   70

After heapify up (70 > 50):
Array: [70, 30, 50]
Index:  0   1   2

Tree:
    70
   /  \
  30   50
```

### Insert 20
```
Array: [70, 30, 50, 20]
Index:  0   1   2   3

Tree:
      70
     /  \
    30   50
   /
  20
```

### Insert 60 (Heapify Up Required!)
```
Before heapify:
Array: [70, 30, 50, 20, 60]
Index:  0   1   2   3   4

Tree:
      70
     /  \
    30   50
   /  \
  20   60

After heapify up (60 > 30):
Array: [70, 60, 50, 20, 30]
Index:  0   1   2   3   4

Tree:
      70
     /  \
    60   50
   /  \
  20   30
```

### Insert 80 (Multiple Heapify Up!)
```
Step 1 - Insert at end:
Array: [70, 60, 50, 20, 30, 80]
Index:  0   1   2   3   4   5

Tree:
      70
     /  \
    60   50
   /  \  /
  20  30 80

Step 2 - Heapify up (80 > 50):
Array: [70, 60, 80, 20, 30, 50]
Index:  0   1   2   3   4   5

Tree:
      70
     /  \
    60   80
   /  \  /
  20  30 50

Step 3 - Heapify up (80 > 70):
Array: [80, 60, 70, 20, 30, 50]
Index:  0   1   2   3   4   5

Tree:
      80
     /  \
    60   70
   /  \  /
  20  30 50
```

---

## Step 2: Extract Maximum (Heap Delete)

### Remove Root (80)
```
Step 1 - Replace root with last element:
Array: [50, 60, 70, 20, 30, --]
Index:  0   1   2   3   4

Tree:
      50
     /  \
    60   70
   /  \
  20  30

Step 2 - Heapify down from root:
Compare 50 with children (60, 70)
70 is largest, swap with 50

Array: [70, 60, 50, 20, 30]
Index:  0   1   2   3   4

Tree:
      70
     /  \
    60   50
   /  \
  20  30

Result: Maximum 80 extracted!
```

---

## Step 3: Detailed Heapify Operations

### Heapify Up Example (Bubble Up)
```
Insert 75 into existing heap:
Array: [70, 60, 50, 20, 30, 75]

Step-by-step:
Index 5: 75 > parent(50) at index 2 → SWAP
Array: [70, 60, 75, 20, 30, 50]

      70
     /  \
    60   75  ← 75 moved up
   /  \  /
  20  30 50

Index 2: 75 > parent(70) at index 0 → SWAP
Array: [75, 60, 70, 20, 30, 50]

      75  ← 75 is now root
     /  \
    60   70
   /  \  /
  20  30 50
```

### Heapify Down Example (Bubble Down)
```
After removing root 75:
Array: [50, 60, 70, 20, 30]

Step-by-step from index 0:
Compare 50 with children 60(index 1) and 70(index 2)
70 is largest → SWAP

Array: [70, 60, 50, 20, 30]

      70
     /  \
    60   50  ← 50 moved down
   /  \
  20  30

Index 2: 50 has no children → DONE
```

---

## Step 4: Complete Example - Min Heap

### Building Min Heap: [4, 1, 3, 2, 16, 9, 10, 14, 8, 7]

```
Step 1 - Array representation:
[4, 1, 3, 2, 16, 9, 10, 14, 8, 7]

Step 2 - Tree representation (before heapify):
        4
      /   \
     1     3
   /  \   / \
  2   16  9  10
 / \  /
14 8 7

Step 3 - Heapify from last non-leaf (index 4):

Index 4 (16): min(16, 7) = 7 → SWAP
[4, 1, 3, 2, 7, 9, 10, 14, 8, 16]

        4
      /   \
     1     3
   /  \   / \
  2   7   9  10
 / \  /
14 8 16

Index 3 (2): min(2, 14, 8) = 2 → NO SWAP

Index 2 (3): min(3, 9, 10) = 3 → NO SWAP

Index 1 (1): min(1, 2, 7) = 1 → NO SWAP

Index 0 (4): min(4, 1, 3) = 1 → SWAP
[1, 4, 3, 2, 7, 9, 10, 14, 8, 16]

        1
      /   \
     4     3
   /  \   / \
  2   7   9  10
 / \  /
14 8 16

Index 1 (4): min(4, 2, 7) = 2 → SWAP
[1, 2, 3, 4, 7, 9, 10, 14, 8, 16]

Final Min Heap:
        1
      /   \
     2     3
   /  \   / \
  4   7   9  10
 / \  /
14 8 16
```

---

## Key Operations Summary

### Insert Operation:
1. Add element at end of array
2. Heapify up until heap property satisfied

### Extract Min/Max:
1. Replace root with last element
2. Remove last element
3. Heapify down from root

### Time Complexities:
- Insert: O(log n)
- Extract: O(log n)
- Peek: O(1)
- Build heap: O(n)

### Parent-Child Relationships:
```
Array: [a, b, c, d, e, f, g, h, i, j]
Index:  0  1  2  3  4  5  6  7  8  9

Tree Structure:
        a(0)
      /       \
    b(1)      c(2)
   /   \     /   \
 d(3)  e(4) f(5) g(6)
 / \   /
h(7)i(8)j(9)

For any index i:
- Parent: (i-1)/2
- Left child: 2i+1
- Right child: 2i+2
```

```
Stack (LIFO - Last In, First Out)
Fixed size, fast access, no search needed.

+-------------------+   <-- Top of Stack (latest push)
| Function Local Var|   (popped first)
+-------------------+
| Argument Pointer  |   (points to heap data)
+-------------------+
| Previous Frame    |
+-------------------+
| ... Older Data    |
+-------------------+   <-- Bottom of Stack

Heap (Dynamic Allocation)
Unorganized, variable size, slower access via pointers.

[Scattered Memory Blocks]
Address 0x123: +-------------------+
               | Heap Data Block 1 |
               +-------------------+

Address 0xABC: +-------------------+
               | Heap Data Block 2 |
               +-------------------+

Pointer from Stack: ----> 0x123 (follow to access data)

Analogy:
- Stack: Stack of plates - add/remove from top only.
- Heap: Restaurant seating - request space, get assigned a spot (pointer leads you there).
```

