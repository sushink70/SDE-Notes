# Complete Guide to Queue Problem Patterns

## Table of Contents
1. [Introduction](#introduction)
2. [Basic Queue Operations](#basic-queue-operations)
3. [Pattern 1: Basic BFS Traversal](#pattern-1-basic-bfs-traversal)
4. [Pattern 2: Level Order Traversal](#pattern-2-level-order-traversal)
5. [Pattern 3: Multi-Source BFS](#pattern-3-multi-source-bfs)
6. [Pattern 4: Sliding Window Maximum](#pattern-4-sliding-window-maximum)
7. [Pattern 5: Monotonic Queue](#pattern-5-monotonic-queue)
8. [Pattern 6: Queue Reconstruction](#pattern-6-queue-reconstruction)
9. [Pattern 7: Circular Queue](#pattern-7-circular-queue)
10. [Pattern 8: Priority Queue (Heap)](#pattern-8-priority-queue-heap)
11. [Pattern 9: Stack Using Queues](#pattern-9-stack-using-queues)
12. [Pattern 10: Queue Using Stacks](#pattern-10-queue-using-stacks)

## Introduction

Queues follow the First-In-First-Out (FIFO) principle and are fundamental data structures used in various algorithms. This guide covers essential queue patterns with complete implementations in Python and Rust.

## Basic Queue Operations

### Python Implementation
```python
from collections import deque

class MyStack:
    """Stack using two queues"""
    def __init__(self):
        self.q1 = deque()
        self.q2 = deque()
    
    def push(self, x):
        # Add to q2, then move all from q1 to q2, then swap
        self.q2.append(x)
        while self.q1:
            self.q2.append(self.q1.popleft())
        self.q1, self.q2 = self.q2, self.q1
    
    def pop(self):
        if not self.q1:
            raise IndexError("Stack is empty")
        return self.q1.popleft()
    
    def top(self):
        if not self.q1:
            raise IndexError("Stack is empty")
        return self.q1[0]
    
    def empty(self):
        return len(self.q1) == 0

class MyStackSingleQueue:
    """Stack using single queue"""
    def __init__(self):
        self.queue = deque()
    
    def push(self, x):
        self.queue.append(x)
        # Rotate queue so new element is at front
        for _ in range(len(self.queue) - 1):
            self.queue.append(self.queue.popleft())
    
    def pop(self):
        if not self.queue:
            raise IndexError("Stack is empty")
        return self.queue.popleft()
    
    def top(self):
        if not self.queue:
            raise IndexError("Stack is empty")
        return self.queue[0]
    
    def empty(self):
        return len(self.queue) == 0
```

### Rust Implementation
```rust
use std::collections::VecDeque;

struct MyStack {
    q1: VecDeque<i32>,
    q2: VecDeque<i32>,
}

impl MyStack {
    fn new() -> Self {
        MyStack {
            q1: VecDeque::new(),
            q2: VecDeque::new(),
        }
    }
    
    fn push(&mut self, x: i32) {
        self.q2.push_back(x);
        while let Some(item) = self.q1.pop_front() {
            self.q2.push_back(item);
        }
        std::mem::swap(&mut self.q1, &mut self.q2);
    }
    
    fn pop(&mut self) -> i32 {
        self.q1.pop_front().unwrap()
    }
    
    fn top(&self) -> i32 {
        *self.q1.front().unwrap()
    }
    
    fn empty(&self) -> bool {
        self.q1.is_empty()
    }
}

struct MyStackSingleQueue {
    queue: VecDeque<i32>,
}

impl MyStackSingleQueue {
    fn new() -> Self {
        MyStackSingleQueue {
            queue: VecDeque::new(),
        }
    }
    
    fn push(&mut self, x: i32) {
        self.queue.push_back(x);
        let len = self.queue.len();
        for _ in 0..len - 1 {
            if let Some(item) = self.queue.pop_front() {
                self.queue.push_back(item);
            }
        }
    }
    
    fn pop(&mut self) -> i32 {
        self.queue.pop_front().unwrap()
    }
    
    fn top(&self) -> i32 {
        *self.queue.front().unwrap()
    }
    
    fn empty(&self) -> bool {
        self.queue.is_empty()
    }
}
```

## Pattern 10: Queue Using Stacks

**Problem**: Implement queue operations using only stack operations.

**Time Complexity**: O(1) amortized for all operations
**Space Complexity**: O(n)

### Python Implementation
```python
class MyQueue:
    """Queue using two stacks"""
    def __init__(self):
        self.input_stack = []
        self.output_stack = []
    
    def push(self, x):
        self.input_stack.append(x)
    
    def pop(self):
        self.peek()  # Ensure output_stack has elements
        return self.output_stack.pop()
    
    def peek(self):
        if not self.output_stack:
            while self.input_stack:
                self.output_stack.append(self.input_stack.pop())
        
        if not self.output_stack:
            raise IndexError("Queue is empty")
        
        return self.output_stack[-1]
    
    def empty(self):
        return len(self.input_stack) == 0 and len(self.output_stack) == 0

class MyQueueOptimized:
    """Optimized queue using stacks with lazy transfer"""
    def __init__(self):
        self.newest = []  # For enqueue
        self.oldest = []  # For dequeue
    
    def push(self, x):
        self.newest.append(x)
    
    def pop(self):
        self._shift_stacks()
        if not self.oldest:
            raise IndexError("Queue is empty")
        return self.oldest.pop()
    
    def peek(self):
        self._shift_stacks()
        if not self.oldest:
            raise IndexError("Queue is empty")
        return self.oldest[-1]
    
    def empty(self):
        return len(self.newest) == 0 and len(self.oldest) == 0
    
    def _shift_stacks(self):
        if not self.oldest:
            while self.newest:
                self.oldest.append(self.newest.pop())
```

### Rust Implementation
```rust
struct MyQueue {
    input_stack: Vec<i32>,
    output_stack: Vec<i32>,
}

impl MyQueue {
    fn new() -> Self {
        MyQueue {
            input_stack: Vec::new(),
            output_stack: Vec::new(),
        }
    }
    
    fn push(&mut self, x: i32) {
        self.input_stack.push(x);
    }
    
    fn pop(&mut self) -> i32 {
        self.peek();
        self.output_stack.pop().unwrap()
    }
    
    fn peek(&mut self) -> i32 {
        if self.output_stack.is_empty() {
            while let Some(item) = self.input_stack.pop() {
                self.output_stack.push(item);
            }
        }
        
        *self.output_stack.last().unwrap()
    }
    
    fn empty(&self) -> bool {
        self.input_stack.is_empty() && self.output_stack.is_empty()
    }
}

struct MyQueueOptimized {
    newest: Vec<i32>,
    oldest: Vec<i32>,
}

impl MyQueueOptimized {
    fn new() -> Self {
        MyQueueOptimized {
            newest: Vec::new(),
            oldest: Vec::new(),
        }
    }
    
    fn push(&mut self, x: i32) {
        self.newest.push(x);
    }
    
    fn pop(&mut self) -> i32 {
        self.shift_stacks();
        self.oldest.pop().unwrap()
    }
    
    fn peek(&mut self) -> i32 {
        self.shift_stacks();
        *self.oldest.last().unwrap()
    }
    
    fn empty(&self) -> bool {
        self.newest.is_empty() && self.oldest.is_empty()
    }
    
    fn shift_stacks(&mut self) {
        if self.oldest.is_empty() {
            while let Some(item) = self.newest.pop() {
                self.oldest.push(item);
            }
        }
    }
}
```

## Common Problem-Solving Strategies

### 1. When to Use BFS vs DFS
- **Use BFS**: Finding shortest path, level-by-level processing, minimum steps
- **Use DFS**: Exploring all paths, backtracking, detecting cycles

### 2. Queue Optimization Techniques
- **Monotonic Queue**: Maintain elements in specific order for sliding window problems
- **Circular Buffer**: Efficient memory usage for fixed-size queues
- **Priority Queue**: When elements need to be processed by priority

### 3. Common Patterns Recognition
- **Level Order**: Process tree/graph level by level
- **Multi-Source BFS**: Multiple starting points (rotting oranges, shortest distance)
- **Sliding Window**: Fixed-size window moving through data
- **Queue Reconstruction**: Rebuild original structure from conditions

### 4. Time and Space Complexity Analysis
- **Standard Queue Operations**: O(1) for enqueue/dequeue
- **BFS Traversal**: O(V + E) time, O(V) space
- **Priority Queue**: O(log n) for insert/extract
- **Circular Queue**: O(1) for all operations

### 5. Implementation Tips
- Use `collections.deque` in Python for efficient queue operations
- Consider `VecDeque` in Rust for double-ended queue functionality
- Be careful with index management in circular queues
- Handle edge cases (empty queue, single element)

## Practice Problems by Pattern

### Basic BFS
1. Binary Tree Level Order Traversal
2. Word Ladder
3. Minimum Depth of Binary Tree

### Multi-Source BFS
1. Rotting Oranges
2. Walls and Gates
3. As Far from Land as Possible

### Sliding Window Maximum
1. Sliding Window Maximum
2. Shortest Subarray with Sum at Least K
3. Jump Game VI

### Monotonic Queue
1. Largest Rectangle in Histogram
2. Maximal Rectangle
3. Sum of Subarray Minimums

### Queue Implementation
1. Design Circular Queue
2. Implement Stack using Queues
3. Implement Queue using Stacks

This comprehensive guide covers the most important queue patterns and their implementations. Each pattern includes detailed explanations, complexity analysis, and working code in both Python and Rust.
```python
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        self.items.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.popleft()
    
    def front(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
```

### Rust Implementation
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

#[derive(Eq, PartialEq)]
struct PriorityItem<T> {
    priority: i32,
    index: usize,
    item: T,
}

impl<T> Ord for PriorityItem<T> {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // Min heap: reverse the comparison
        other.priority.cmp(&self.priority)
            .then_with(|| other.index.cmp(&self.index))
    }
}

impl<T> PartialOrd for PriorityItem<T> {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

struct PriorityQueue<T> {
    heap: BinaryHeap<PriorityItem<T>>,
    index: usize,
}

impl<T> PriorityQueue<T> {
    fn new() -> Self {
        PriorityQueue {
            heap: BinaryHeap::new(),
            index: 0,
        }
    }
    
    fn push(&mut self, priority: i32, item: T) {
        self.heap.push(PriorityItem {
            priority,
            index: self.index,
            item,
        });
        self.index += 1;
    }
    
    fn pop(&mut self) -> Option<T> {
        self.heap.pop().map(|item| item.item)
    }
    
    fn peek(&self) -> Option<&T> {
        self.heap.peek().map(|item| &item.item)
    }
    
    fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
    
    fn len(&self) -> usize {
        self.heap.len()
    }
}

struct MaxPriorityQueue<T> {
    heap: BinaryHeap<(i32, usize, T)>,
    index: usize,
}

impl<T> MaxPriorityQueue<T> {
    fn new() -> Self {
        MaxPriorityQueue {
            heap: BinaryHeap::new(),
            index: 0,
        }
    }
    
    fn push(&mut self, priority: i32, item: T) {
        self.heap.push((priority, self.index, item));
        self.index += 1;
    }
    
    fn pop(&mut self) -> Option<T> {
        self.heap.pop().map(|(_, _, item)| item)
    }
    
    fn peek(&self) -> Option<&T> {
        self.heap.peek().map(|(_, _, item)| item)
    }
    
    fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }
}

fn find_kth_largest(nums: Vec<i32>, k: i32) -> i32 {
    let mut heap = BinaryHeap::new();
    let k = k as usize;
    
    for num in nums {
        heap.push(Reverse(num));
        if heap.len() > k {
            heap.pop();
        }
    }
    
    heap.peek().unwrap().0
}
```

## Pattern 9: Stack Using Queues

**Problem**: Implement stack operations using only queue operations.

**Time Complexity**: O(n) for push, O(1) for pop
**Space Complexity**: O(n)

### Python Implementation
```rust
use std::collections::VecDeque;

struct Queue<T> {
    items: VecDeque<T>,
}

impl<T> Queue<T> {
    fn new() -> Self {
        Queue {
            items: VecDeque::new(),
        }
    }
    
    fn enqueue(&mut self, item: T) {
        self.items.push_back(item);
    }
    
    fn dequeue(&mut self) -> Option<T> {
        self.items.pop_front()
    }
    
    fn front(&self) -> Option<&T> {
        self.items.front()
    }
    
    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    fn size(&self) -> usize {
        self.items.len()
    }
}
```

## Pattern 1: Basic BFS Traversal

**Problem**: Traverse a graph or tree using breadth-first search.

**Time Complexity**: O(V + E) for graphs, O(n) for trees
**Space Complexity**: O(V) for the queue

### Python Implementation
```python
from collections import deque

def bfs_graph(graph, start):
    """BFS traversal of a graph"""
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            
            # Add neighbors to queue
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
    
    return result

def bfs_tree(root):
    """BFS traversal of a binary tree"""
    if not root:
        return []
    
    queue = deque([root])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node.val)
        
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    
    return result
```

### Rust Implementation
```rust
use std::collections::{HashMap, HashSet, VecDeque};

fn bfs_graph(graph: &HashMap<i32, Vec<i32>>, start: i32) -> Vec<i32> {
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    let mut result = Vec::new();
    
    queue.push_back(start);
    
    while let Some(node) = queue.pop_front() {
        if !visited.contains(&node) {
            visited.insert(node);
            result.push(node);
            
            if let Some(neighbors) = graph.get(&node) {
                for &neighbor in neighbors {
                    if !visited.contains(&neighbor) {
                        queue.push_back(neighbor);
                    }
                }
            }
        }
    }
    
    result
}

#[derive(Debug)]
struct TreeNode {
    val: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

fn bfs_tree(root: Option<Box<TreeNode>>) -> Vec<i32> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }
    
    let mut queue = VecDeque::new();
    queue.push_back(root);
    
    while let Some(node_opt) = queue.pop_front() {
        if let Some(node) = node_opt {
            result.push(node.val);
            
            if node.left.is_some() {
                queue.push_back(node.left);
            }
            if node.right.is_some() {
                queue.push_back(node.right);
            }
        }
    }
    
    result
}
```

## Pattern 2: Level Order Traversal

**Problem**: Process nodes level by level in a tree.

**Time Complexity**: O(n)
**Space Complexity**: O(w) where w is the maximum width of the tree

### Python Implementation
```python
from collections import deque

def level_order(root):
    """Level order traversal returning list of levels"""
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        current_level = []
        
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(current_level)
    
    return result

def level_order_zigzag(root):
    """Zigzag level order traversal"""
    if not root:
        return []
    
    result = []
    queue = deque([root])
    left_to_right = True
    
    while queue:
        level_size = len(queue)
        current_level = deque()
        
        for _ in range(level_size):
            node = queue.popleft()
            
            if left_to_right:
                current_level.append(node.val)
            else:
                current_level.appendleft(node.val)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        result.append(list(current_level))
        left_to_right = not left_to_right
    
    return result
```

### Rust Implementation
```rust
use std::collections::VecDeque;

fn level_order(root: Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }
    
    let mut queue = VecDeque::new();
    queue.push_back(root);
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut current_level = Vec::new();
        
        for _ in 0..level_size {
            if let Some(Some(node)) = queue.pop_front() {
                current_level.push(node.val);
                
                if node.left.is_some() {
                    queue.push_back(node.left);
                }
                if node.right.is_some() {
                    queue.push_back(node.right);
                }
            }
        }
        
        result.push(current_level);
    }
    
    result
}

fn level_order_zigzag(root: Option<Box<TreeNode>>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    if root.is_none() {
        return result;
    }
    
    let mut queue = VecDeque::new();
    queue.push_back(root);
    let mut left_to_right = true;
    
    while !queue.is_empty() {
        let level_size = queue.len();
        let mut current_level = VecDeque::new();
        
        for _ in 0..level_size {
            if let Some(Some(node)) = queue.pop_front() {
                if left_to_right {
                    current_level.push_back(node.val);
                } else {
                    current_level.push_front(node.val);
                }
                
                if node.left.is_some() {
                    queue.push_back(node.left);
                }
                if node.right.is_some() {
                    queue.push_back(node.right);
                }
            }
        }
        
        result.push(current_level.into_iter().collect());
        left_to_right = !left_to_right;
    }
    
    result
}
```

## Pattern 3: Multi-Source BFS

**Problem**: Start BFS from multiple sources simultaneously (e.g., rotting oranges).

**Time Complexity**: O(m * n)
**Space Complexity**: O(m * n)

### Python Implementation
```python
from collections import deque

def oranges_rotting(grid):
    """
    Calculate time to rot all oranges
    0 = empty, 1 = fresh orange, 2 = rotten orange
    """
    if not grid or not grid[0]:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh_count = 0
    
    # Find all initially rotten oranges and count fresh ones
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c))
            elif grid[r][c] == 1:
                fresh_count += 1
    
    if fresh_count == 0:
        return 0
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    minutes = 0
    
    while queue and fresh_count > 0:
        minutes += 1
        
        # Process all rotten oranges at current time
        for _ in range(len(queue)):
            row, col = queue.popleft()
            
            # Check all 4 directions
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                
                if (0 <= nr < rows and 0 <= nc < cols and 
                    grid[nr][nc] == 1):
                    grid[nr][nc] = 2  # Make it rotten
                    fresh_count -= 1
                    queue.append((nr, nc))
    
    return minutes if fresh_count == 0 else -1
```

### Rust Implementation
```rust
use std::collections::VecDeque;

fn oranges_rotting(mut grid: Vec<Vec<i32>>) -> i32 {
    if grid.is_empty() || grid[0].is_empty() {
        return 0;
    }
    
    let rows = grid.len();
    let cols = grid[0].len();
    let mut queue = VecDeque::new();
    let mut fresh_count = 0;
    
    // Find all initially rotten oranges and count fresh ones
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == 2 {
                queue.push_back((r, c));
            } else if grid[r][c] == 1 {
                fresh_count += 1;
            }
        }
    }
    
    if fresh_count == 0 {
        return 0;
    }
    
    let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];
    let mut minutes = 0;
    
    while !queue.is_empty() && fresh_count > 0 {
        minutes += 1;
        let queue_size = queue.len();
        
        for _ in 0..queue_size {
            if let Some((row, col)) = queue.pop_front() {
                for &(dr, dc) in &directions {
                    let nr = row as i32 + dr;
                    let nc = col as i32 + dc;
                    
                    if nr >= 0 && nr < rows as i32 && 
                       nc >= 0 && nc < cols as i32 {
                        let nr = nr as usize;
                        let nc = nc as usize;
                        
                        if grid[nr][nc] == 1 {
                            grid[nr][nc] = 2;
                            fresh_count -= 1;
                            queue.push_back((nr, nc));
                        }
                    }
                }
            }
        }
    }
    
    if fresh_count == 0 { minutes } else { -1 }
}
```

## Pattern 4: Sliding Window Maximum

**Problem**: Find the maximum element in every sliding window of size k.

**Time Complexity**: O(n)
**Space Complexity**: O(k)

### Python Implementation
```python
from collections import deque

def sliding_window_maximum(nums, k):
    """Find maximum in each sliding window of size k"""
    if not nums or k == 0:
        return []
    
    dq = deque()  # Store indices
    result = []
    
    for i in range(len(nums)):
        # Remove indices outside current window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove indices whose corresponding values are smaller
        while dq and nums[dq[-1]] <= nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add to result when window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

def sliding_window_minimum(nums, k):
    """Find minimum in each sliding window of size k"""
    if not nums or k == 0:
        return []
    
    dq = deque()  # Store indices
    result = []
    
    for i in range(len(nums)):
        # Remove indices outside current window
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # Remove indices whose values are greater (for minimum)
        while dq and nums[dq[-1]] >= nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add to result when window is complete
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result
```

### Rust Implementation
```rust
use std::collections::VecDeque;

fn sliding_window_maximum(nums: Vec<i32>, k: i32) -> Vec<i32> {
    if nums.is_empty() || k == 0 {
        return vec![];
    }
    
    let k = k as usize;
    let mut dq: VecDeque<usize> = VecDeque::new();
    let mut result = Vec::new();
    
    for i in 0..nums.len() {
        // Remove indices outside current window
        while let Some(&front) = dq.front() {
            if front <= i.saturating_sub(k) {
                dq.pop_front();
            } else {
                break;
            }
        }
        
        // Remove indices whose values are smaller
        while let Some(&back) = dq.back() {
            if nums[back] <= nums[i] {
                dq.pop_back();
            } else {
                break;
            }
        }
        
        dq.push_back(i);
        
        // Add to result when window is complete
        if i >= k - 1 {
            if let Some(&front) = dq.front() {
                result.push(nums[front]);
            }
        }
    }
    
    result
}

fn sliding_window_minimum(nums: Vec<i32>, k: i32) -> Vec<i32> {
    if nums.is_empty() || k == 0 {
        return vec![];
    }
    
    let k = k as usize;
    let mut dq: VecDeque<usize> = VecDeque::new();
    let mut result = Vec::new();
    
    for i in 0..nums.len() {
        // Remove indices outside current window
        while let Some(&front) = dq.front() {
            if front <= i.saturating_sub(k) {
                dq.pop_front();
            } else {
                break;
            }
        }
        
        // Remove indices whose values are greater (for minimum)
        while let Some(&back) = dq.back() {
            if nums[back] >= nums[i] {
                dq.pop_back();
            } else {
                break;
            }
        }
        
        dq.push_back(i);
        
        // Add to result when window is complete
        if i >= k - 1 {
            if let Some(&front) = dq.front() {
                result.push(nums[front]);
            }
        }
    }
    
    result
}
```

## Pattern 5: Monotonic Queue

**Problem**: Maintain elements in monotonic order for optimization.

**Time Complexity**: O(n)
**Space Complexity**: O(k)

### Python Implementation
```python
from collections import deque

class MonotonicQueue:
    """Monotonic decreasing queue for maximum queries"""
    def __init__(self):
        self.dq = deque()
    
    def push(self, val):
        # Remove smaller elements from back
        while self.dq and self.dq[-1] < val:
            self.dq.pop()
        self.dq.append(val)
    
    def pop(self, val):
        # Only pop if it's the maximum element
        if self.dq and self.dq[0] == val:
            self.dq.popleft()
    
    def max_value(self):
        return self.dq[0] if self.dq else float('-inf')

def constrained_subset_sum(nums, k):
    """Maximum sum of non-adjacent elements with constraint k"""
    n = len(nums)
    dp = [0] * n
    dp[0] = nums[0]
    
    # Monotonic queue to track maximum in sliding window
    dq = deque([0])
    
    for i in range(1, n):
        # Remove indices outside window
        while dq and dq[0] < i - k:
            dq.popleft()
        
        # Current max sum ending at i
        dp[i] = nums[i] + (dp[dq[0]] if dq else 0)
        
        # Maintain decreasing order in queue
        while dq and dp[dq[-1]] <= dp[i]:
            dq.pop()
        
        dq.append(i)
    
    return max(dp)
```

### Rust Implementation
```rust
use std::collections::VecDeque;

struct MonotonicQueue {
    dq: VecDeque<i32>,
}

impl MonotonicQueue {
    fn new() -> Self {
        MonotonicQueue {
            dq: VecDeque::new(),
        }
    }
    
    fn push(&mut self, val: i32) {
        // Remove smaller elements from back
        while let Some(&back) = self.dq.back() {
            if back < val {
                self.dq.pop_back();
            } else {
                break;
            }
        }
        self.dq.push_back(val);
    }
    
    fn pop(&mut self, val: i32) {
        // Only pop if it's the maximum element
        if let Some(&front) = self.dq.front() {
            if front == val {
                self.dq.pop_front();
            }
        }
    }
    
    fn max_value(&self) -> i32 {
        self.dq.front().copied().unwrap_or(i32::MIN)
    }
}

fn constrained_subset_sum(nums: Vec<i32>, k: i32) -> i32 {
    let n = nums.len();
    let mut dp = vec![0; n];
    dp[0] = nums[0];
    
    let mut dq: VecDeque<usize> = VecDeque::new();
    dq.push_back(0);
    
    for i in 1..n {
        // Remove indices outside window
        while let Some(&front) = dq.front() {
            if front < i.saturating_sub(k as usize) {
                dq.pop_front();
            } else {
                break;
            }
        }
        
        // Current max sum ending at i
        let prev_max = if let Some(&front) = dq.front() {
            dp[front]
        } else {
            0
        };
        dp[i] = nums[i] + prev_max;
        
        // Maintain decreasing order in queue
        while let Some(&back) = dq.back() {
            if dp[back] <= dp[i] {
                dq.pop_back();
            } else {
                break;
            }
        }
        
        dq.push_back(i);
    }
    
    *dp.iter().max().unwrap()
}
```

## Pattern 6: Queue Reconstruction

**Problem**: Reconstruct original queue from given conditions.

**Time Complexity**: O(n²)
**Space Complexity**: O(n)

### Python Implementation
```python
def reconstruct_queue(people):
    """
    Reconstruct queue based on [height, number_of_taller_people_in_front]
    """
    # Sort by height (desc), then by count (asc)
    people.sort(key=lambda x: (-x[0], x[1]))
    
    result = []
    for person in people:
        # Insert at position equal to count of taller people
        result.insert(person[1], person)
    
    return result

def queue_reconstruction_by_height(people):
    """Alternative approach using list operations"""
    if not people:
        return []
    
    # Sort by height descending, then by k ascending
    people.sort(key=lambda x: (-x[0], x[1]))
    
    queue = []
    for h, k in people:
        queue.insert(k, [h, k])
    
    return queue
```

### Rust Implementation
```rust
fn reconstruct_queue(mut people: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    // Sort by height (desc), then by count (asc)
    people.sort_by(|a, b| {
        if a[0] != b[0] {
            b[0].cmp(&a[0])  // Height descending
        } else {
            a[1].cmp(&b[1])  // Count ascending
        }
    });
    
    let mut result = Vec::new();
    for person in people {
        let k = person[1] as usize;
        if k >= result.len() {
            result.push(person);
        } else {
            result.insert(k, person);
        }
    }
    
    result
}

fn queue_reconstruction_by_height(mut people: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    if people.is_empty() {
        return vec![];
    }
    
    // Sort by height descending, then by k ascending
    people.sort_by(|a, b| {
        match b[0].cmp(&a[0]) {
            std::cmp::Ordering::Equal => a[1].cmp(&b[1]),
            other => other,
        }
    });
    
    let mut queue = Vec::new();
    for person in people {
        let k = person[1] as usize;
        queue.insert(k, person);
    }
    
    queue
}
```

## Pattern 7: Circular Queue

**Problem**: Implement a circular buffer with fixed capacity.

**Time Complexity**: O(1) for all operations
**Space Complexity**: O(k) where k is capacity

### Python Implementation
```python
class MyCircularQueue:
    def __init__(self, k):
        self.capacity = k
        self.queue = [0] * k
        self.head = -1
        self.tail = -1
        self.size = 0
    
    def enQueue(self, value):
        if self.isFull():
            return False
        
        if self.isEmpty():
            self.head = 0
        
        self.tail = (self.tail + 1) % self.capacity
        self.queue[self.tail] = value
        self.size += 1
        return True
    
    def deQueue(self):
        if self.isEmpty():
            return False
        
        if self.size == 1:
            self.head = -1
            self.tail = -1
        else:
            self.head = (self.head + 1) % self.capacity
        
        self.size -= 1
        return True
    
    def Front(self):
        return -1 if self.isEmpty() else self.queue[self.head]
    
    def Rear(self):
        return -1 if self.isEmpty() else self.queue[self.tail]
    
    def isEmpty(self):
        return self.size == 0
    
    def isFull(self):
        return self.size == self.capacity

class CircularBuffer:
    """Alternative implementation with automatic overwrite"""
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0
    
    def put(self, item):
        self.buffer[self.tail] = item
        if self.size < self.capacity:
            self.size += 1
        else:
            self.head = (self.head + 1) % self.capacity
        self.tail = (self.tail + 1) % self.capacity
    
    def get(self):
        if self.size == 0:
            return None
        
        item = self.buffer[self.head]
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return item
    
    def is_full(self):
        return self.size == self.capacity
    
    def is_empty(self):
        return self.size == 0
```

### Rust Implementation
```rust
struct MyCircularQueue {
    capacity: usize,
    queue: Vec<i32>,
    head: i32,
    tail: i32,
    size: usize,
}

impl MyCircularQueue {
    fn new(k: i32) -> Self {
        MyCircularQueue {
            capacity: k as usize,
            queue: vec![0; k as usize],
            head: -1,
            tail: -1,
            size: 0,
        }
    }
    
    fn en_queue(&mut self, value: i32) -> bool {
        if self.is_full() {
            return false;
        }
        
        if self.is_empty() {
            self.head = 0;
        }
        
        self.tail = (self.tail + 1) % self.capacity as i32;
        self.queue[self.tail as usize] = value;
        self.size += 1;
        true
    }
    
    fn de_queue(&mut self) -> bool {
        if self.is_empty() {
            return false;
        }
        
        if self.size == 1 {
            self.head = -1;
            self.tail = -1;
        } else {
            self.head = (self.head + 1) % self.capacity as i32;
        }
        
        self.size -= 1;
        true
    }
    
    fn front(&self) -> i32 {
        if self.is_empty() {
            -1
        } else {
            self.queue[self.head as usize]
        }
    }
    
    fn rear(&self) -> i32 {
        if self.is_empty() {
            -1
        } else {
            self.queue[self.tail as usize]
        }
    }
    
    fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    fn is_full(&self) -> bool {
        self.size == self.capacity
    }
}

struct CircularBuffer<T> {
    capacity: usize,
    buffer: Vec<Option<T>>,
    head: usize,
    tail: usize,
    size: usize,
}

impl<T> CircularBuffer<T> {
    fn new(capacity: usize) -> Self {
        CircularBuffer {
            capacity,
            buffer: (0..capacity).map(|_| None).collect(),
            head: 0,
            tail: 0,
            size: 0,
        }
    }
    
    fn put(&mut self, item: T) {
        self.buffer[self.tail] = Some(item);
        if self.size < self.capacity {
            self.size += 1;
        } else {
            self.head = (self.head + 1) % self.capacity;
        }
        self.tail = (self.tail + 1) % self.capacity;
    }
    
    fn get(&mut self) -> Option<T> {
        if self.size == 0 {
            return None;
        }
        
        let item = self.buffer[self.head].take();
        self.head = (self.head + 1) % self.capacity;
        self.size -= 1;
        item
    }
    
    fn is_full(&self) -> bool {
        self.size == self.capacity
    }
    
    fn is_empty(&self) -> bool {
        self.size == 0
    }
}
```

## Pattern 8: Priority Queue (Heap)

**Problem**: Implement priority-based queue operations.

**Time Complexity**: O(log n) for insert/extract, O(1) for peek
**Space Complexity**: O(n)

### Python Implementation
```python
import heapq
from typing import Any

class PriorityQueue:
    def __init__(self):
        self.heap = []
        self.index = 0
    
    def push(self, priority, item):
        # Use negative priority for max heap behavior
        heapq.heappush(self.heap, (priority, self.index, item))
        self.index += 1
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        return heapq.heappop(self.heap)[2]
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        return self.heap[0][2]
    
    def is_empty(self):
        return len(self.heap) == 0
    
    def size(self):
        return len(self.heap)

class MaxPriorityQueue:
    def __init__(self):
        self.heap = []
        self.index = 0
    
    def push(self, priority, item):
        # Negate priority for max heap
        heapq.heappush(self.heap, (-priority, self.index, item))
        self.index += 1
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        return heapq.heappop(self.heap)[2]
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Priority queue is empty")
        return self.heap[0][2]
    
    def is_empty(self):
        return len(self.heap) == 0

def merge_k_sorted_lists(lists):
    """Merge k sorted linked lists using priority queue"""
    heap = []
    
    # Add first node from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst.val, i, lst))
    
    dummy = ListNode(0)
    current = dummy
    
    while heap:
        val, list_idx, node = heapq.heappop(heap)
        current.next = node
        current = current.next
        
        # Add next node from the same list
        if node.next:
            heapq.heappush(heap, (node.next.val, list_idx, node.next))
    
    return dummy.next

def find_kth_largest(nums, k):
    """Find kth largest element using min heap"""
    heap = []
    
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    
    return heap[0]

### Rust Implementation
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct PriorityQueue {
    heap: BinaryHeap<(Reverse<i32>, usize)>,
    index: usize,
}

impl PriorityQueue {
    fn new() -> Self {
        PriorityQueue {
            heap: BinaryHeap::new(),
            index: 0,
        }
    }

    fn push(&mut self, priority: i32, item: i32) {
        self.heap.push((Reverse(priority), self.index));
        self.index += 1;
    }

    fn pop(&mut self) -> Option<i32> {
        self.heap.pop().map(|(Reverse(priority), _)| priority)
    }

    fn peek(&self) -> Option<i32> {
        self.heap.peek().map(|(Reverse(priority), _)| *priority)
    }

    fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }

    fn size(&self) -> usize {
        self.heap.len()
    }
}
struct MaxPriorityQueue {
    heap: BinaryHeap<(i32, usize)>,
    index: usize,
}

impl MaxPriorityQueue {
    fn new() -> Self {
        MaxPriorityQueue {
            heap: BinaryHeap::new(),
            index: 0,
        }
    }

    fn push(&mut self, priority: i32, item: i32) {
        self.heap.push((priority, self.index));
        self.index += 1;
    }

    fn pop(&mut self) -> Option<i32> {
        self.heap.pop().map(|(priority, _)| priority)
    }

    fn peek(&self) -> Option<i32> {
        self.heap.peek().map(|(priority, _)| *priority)
    }

    fn is_empty(&self) -> bool {
        self.heap.is_empty()
    }

    fn size(&self) -> usize {
        self.heap.len()
    }
}
fn find_kth_largest(nums: Vec<i32>, k: i32) -> i32 {
    let mut heap = BinaryHeap::new();
    let k = k as usize;

    for num in nums {
        heap.push(Reverse(num));
        if heap.len() > k {
            heap.pop();
        }
    }

    heap.peek().unwrap().0
}
```
I've created a comprehensive guide to queue problem patterns with complete implementations in both Python and Rust. The guide covers 10 essential patterns:

1. **Basic BFS Traversal** - Foundation for graph and tree traversal
2. **Level Order Traversal** - Processing nodes level by level
3. **Multi-Source BFS** - Starting from multiple points simultaneously
4. **Sliding Window Maximum** - Finding extremes in sliding windows
5. **Monotonic Queue** - Maintaining ordered elements for optimization
6. **Queue Reconstruction** - Rebuilding structures from conditions
7. **Circular Queue** - Fixed-capacity circular buffer implementation
8. **Priority Queue** - Priority-based processing using heaps
9. **Stack Using Queues** - Implementing stack with queue operations
10. **Queue Using Stacks** - Implementing queue with stack operations

Each pattern includes:
- **Problem description** and use cases
- **Time and space complexity** analysis
- **Complete Python implementation** with detailed comments
- **Complete Rust implementation** with proper error handling
- **Real-world examples** and applications

The guide also provides problem-solving strategies, complexity analysis tips, and a curated list of practice problems organized by pattern. This should serve as a comprehensive reference for mastering queue-based algorithms in coding interviews and competitive programming.