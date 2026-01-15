# The Complete Heap Mastery Guide

### *A Journey from First Principles to Advanced Mastery*

---

## Table of Contents

1. Foundation: What is a Heap?
2. The Binary Heap Structure
3. Heap Property & Invariants
4. Core Operations (with Multi-Language Implementation)
5. Building a Heap (Heapify)
6. Heap Sort
7. Priority Queue Applications
8. Advanced Heap Variants
9. Problem-Solving Patterns
10. Practice Problems & Mental Models

---

## 1. Foundation: What is a Heap?

### The Core Insight

A **heap** is a specialized **tree-based data structure** that maintains a specific ordering property. Think of it as a "partially sorted" structure—not fully sorted like a sorted array, but organized enough to give us efficient access to the maximum (or minimum) element.

**Key Mental Model:** Imagine a company hierarchy where the CEO is at the top, and every manager must be more senior than their direct reports. You don't care about the ordering between managers at the same level—only that the parent-child relationship is maintained.

### Why Heaps Matter

Heaps solve a fundamental problem: **"Give me the most important element repeatedly, efficiently."**

**Real-world analogy:** 

- Emergency room triage (highest priority patient first)
- Task scheduling in operating systems
- Dijkstra's shortest path algorithm
- Huffman coding for compression

### Time Complexity Overview (Spoiler Alert)

```
Operation          | Array | Sorted Array | BST (balanced) | Heap
-------------------|-------|--------------|----------------|-------
Find Max/Min       | O(n)  | O(1)         | O(log n)       | O(1)
Insert             | O(1)  | O(n)         | O(log n)       | O(log n)
Delete Max/Min     | O(n)  | O(n)         | O(log n)       | O(log n)
Build from n items | O(n)  | O(n log n)   | O(n log n)     | O(n) ⭐
```

---

## 2. The Binary Heap Structure

### Visual Understanding

A **binary heap** is a **complete binary tree** stored in an array. Let me break this down:

**Complete Binary Tree**: Every level is fully filled except possibly the last, which is filled from left to right.

```
        Valid Complete Binary Tree:
                 16
               /    \
              14     10
             /  \   /
            8    7  9

        NOT Complete (gap in last level):
                 16
               /    \
              14     10
             /      /
            8      9
```

**The Breakthrough Insight:** We can represent this tree using just an array!

```
Array representation: [16, 14, 10, 8, 7, 9]
Index:                 0   1   2   3  4  5

        16 (index 0)
       /  \
     14    10 (indices 1, 2)
    / \    /
   8   7  9  (indices 3, 4, 5)
```

### Array-to-Tree Index Mathematics

This is **critical** to understand:

For any element at index `i`:

- **Left child**: `2*i + 1`
- **Right child**: `2*i + 2`
- **Parent**: `(i - 1) / 2` (integer division)

**Why this works:** Think of the tree as being labeled level by level, left to right. The mathematical relationship emerges from the binary nature of the tree (each parent has 2 children).

```
Parent index: i
├─ Left child:  2i + 1
└─ Right child: 2i + 2

Example: Parent at index 1
├─ Left child:  2(1) + 1 = 3
└─ Right child: 2(1) + 2 = 4
```

---

## 3. Heap Property & Invariants

### Two Types of Heaps

**Max-Heap Property:** Every parent ≥ its children
```
         50 ✓
        /  \
      30    40 ✓
     / \
   10  20 ✓
```

**Min-Heap Property:** Every parent ≤ its children
```
         10 ✓
        /  \
      20    30 ✓
     / \
   40  50 ✓
```

**Critical Understanding:** 

- Heaps are **NOT fully sorted**
- We only guarantee the parent-child relationship
- Siblings have **no ordering requirement**

```
This is a valid Max-Heap:
         50
        /  \
      40    30  ← 40 and 30 have no ordering between them
     / \
   10  20
```

### The Invariant Concept

**Invariant** (in computer science): A condition that remains true throughout the execution of a program.

**Heap Invariant:** At every moment, every parent satisfies the heap property with respect to its children.

**Mental Model:** Like a contract that must never be broken. When we insert or delete, we might temporarily violate this, but we must restore it before the operation completes.

---

## 4. Core Operations (Multi-Language Implementation)

### Operation 1: Peek (Get Maximum/Minimum)

**Concept:** Simply return the root element.

**Time Complexity:** O(1)

**Why O(1)?** The root is always at index 0 in our array representation.

```
Max-Heap: [50, 30, 40, 10, 20]
Maximum is at index 0: 50 ✓
```

#### Implementation Across Languages

**Python:**

```python
def peek(heap):
    """Return the maximum element without removing it."""
    if not heap:
        raise IndexError("Heap is empty")
    return heap[0]
```

**Rust:**

```rust
impl<T: Ord> MaxHeap<T> {
    pub fn peek(&self) -> Option<&T> {
        self.data.first()
    }
}
```

**C:**
```c
int peek(int* heap, int size) {
    if (size == 0) {
        fprintf(stderr, "Heap is empty\n");
        exit(1);
    }
    return heap[0];
}
```

**C++:**
```cpp
template<typename T>
T peek(const std::vector<T>& heap) {
    if (heap.empty()) {
        throw std::runtime_error("Heap is empty");
    }
    return heap[0];
}
```

**Go:**
```go
func (h *MaxHeap) Peek() (int, error) {
    if len(h.data) == 0 {
        return 0, errors.New("heap is empty")
    }
    return h.data[0], nil
}
```

---

### Operation 2: Insert (Bubble Up / Sift Up)

**The Challenge:** When we add a new element, we might violate the heap property.

**Solution Strategy:** "Bubble Up" (also called Sift Up, Percolate Up, Heapify Up)

**Mental Model:** Like a bubble rising in water—the element keeps moving up until it finds its correct position.

#### The Algorithm (Max-Heap)

```
Step-by-step process:

1. Insert new element at the end of array (maintain complete tree property)
2. Compare with parent
3. If child > parent, swap them
4. Repeat step 2-3 until heap property is restored

Termination conditions:
- Element reaches root (index 0), OR
- Element ≤ parent (heap property satisfied)
```

#### Visual Example

```
Initial Max-Heap:        Insert 45:
      50                       50
     /  \                     /  \
   30    40                 30    40
   /                        / \
  10                      10  45 ← New element

Compare 45 with parent 30:
45 > 30, so SWAP:
      50
     /  \
   45    40
   / \
 10  30

Compare 45 with parent 50:
45 ≤ 50, STOP ✓
```

#### ASCII Visualization Flow

```
Insertion Process for value 60:

Step 0: Initial heap
         50
        /  \
      30    40
     / \
   10  20

Step 1: Add 60 at end
         50
        /  \
      30    40
     / \   /
   10  20 60  ← Added here

Step 2: Compare with parent (40)
60 > 40, SWAP!
         50
        /  \
      30    60  ← Moved up
     / \   /
   10  20 40

Step 3: Compare with parent (50)
60 > 50, SWAP!
         60  ← Moved to root
        /  \
      30    50
     / \   /
   10  20 40

DONE! ✓
```

#### Time Complexity Analysis

**Worst Case:** O(log n)

**Why?** In the worst case, we bubble up from the bottom to the root. The height of a complete binary tree with n nodes is ⌊log₂(n)⌋.

**Best Case:** O(1) - when the new element is smaller than its parent and doesn't need to move.

#### Implementation

**Python (Max-Heap):**
```python
def insert(heap, value):
    """Insert a value into the max-heap."""
    # Step 1: Add to end
    heap.append(value)
    
    # Step 2: Bubble up
    _bubble_up(heap, len(heap) - 1)

def _bubble_up(heap, index):
    """Restore heap property by bubbling element up."""
    # Base case: reached root
    if index == 0:
        return
    
    parent_index = (index - 1) // 2
    
    # If heap property violated, swap and continue
    if heap[index] > heap[parent_index]:
        heap[index], heap[parent_index] = heap[parent_index], heap[index]
        _bubble_up(heap, parent_index)
```

**Rust (Max-Heap):**
```rust
pub struct MaxHeap<T: Ord> {
    data: Vec<T>,
}

impl<T: Ord> MaxHeap<T> {
    pub fn insert(&mut self, value: T) {
        // Add to end
        self.data.push(value);
        
        // Bubble up from last position
        self.bubble_up(self.data.len() - 1);
    }
    
    fn bubble_up(&mut self, mut index: usize) {
        while index > 0 {
            let parent_index = (index - 1) / 2;
            
            // Compare and potentially swap
            if self.data[index] > self.data[parent_index] {
                self.data.swap(index, parent_index);
                index = parent_index;
            } else {
                break;
            }
        }
    }
}
```

**C (Max-Heap):**
```c
void insert(int* heap, int* size, int capacity, int value) {
    if (*size >= capacity) {
        fprintf(stderr, "Heap overflow\n");
        return;
    }
    
    // Add to end
    heap[*size] = value;
    int index = *size;
    (*size)++;
    
    // Bubble up
    while (index > 0) {
        int parent_index = (index - 1) / 2;
        
        if (heap[index] > heap[parent_index]) {
            // Swap
            int temp = heap[index];
            heap[index] = heap[parent_index];
            heap[parent_index] = temp;
            
            index = parent_index;
        } else {
            break;
        }
    }
}
```

**C++ (Max-Heap):**
```cpp
template<typename T>
class MaxHeap {
private:
    std::vector<T> data;
    
    void bubbleUp(size_t index) {
        while (index > 0) {
            size_t parent_index = (index - 1) / 2;
            
            if (data[index] > data[parent_index]) {
                std::swap(data[index], data[parent_index]);
                index = parent_index;
            } else {
                break;
            }
        }
    }
    
public:
    void insert(const T& value) {
        data.push_back(value);
        bubbleUp(data.size() - 1);
    }
};
```

**Go (Max-Heap):**
```go
type MaxHeap struct {
    data []int
}

func (h *MaxHeap) Insert(value int) {
    // Add to end
    h.data = append(h.data, value)
    
    // Bubble up
    h.bubbleUp(len(h.data) - 1)
}

func (h *MaxHeap) bubbleUp(index int) {
    for index > 0 {
        parentIndex := (index - 1) / 2
        
        if h.data[index] > h.data[parentIndex] {
            h.data[index], h.data[parentIndex] = h.data[parentIndex], h.data[index]
            index = parentIndex
        } else {
            break
        }
    }
}
```

---

### Operation 3: Extract Max/Min (Bubble Down / Sift Down)

**The Challenge:** Removing the root creates a hole and violates the complete tree property.

**Solution Strategy:** Replace root with last element, then "bubble down" to restore heap property.

**Mental Model:** Like a stone sinking in water—it falls until it finds its proper level.

#### The Algorithm (Max-Heap)

```
Step-by-step process:

1. Save root value (this is what we'll return)
2. Move LAST element to root position
3. Remove last element
4. Start at root, compare with children
5. Swap with LARGER child if parent < child
6. Repeat until heap property restored

Termination conditions:
- Reach a leaf node (no children), OR
- Parent ≥ both children (heap property satisfied)
```

#### Visual Example

```
Initial Max-Heap:        Extract max (50):
      50 ← Remove              10 ← Last element moves here
     /  \                     /  \
   45    40                 45    40
   / \                      /
  10  30                  30

Now bubble down 10:

Compare 10 with children (45, 40):
10 < 45 (larger child), SWAP:
      45
     /  \
   10    40
   /
  30

Compare 10 with children (30):
10 < 30, SWAP:
      45
     /  \
   30    40
   /
  10

DONE! ✓
```

#### Decision Tree for Bubble Down

```
                Start at current node
                        |
            ┌───────────┴───────────┐
            │                       │
       Has children?               No children
            │                       │
           Yes                   STOP ✓
            |
            ├─ One child? Compare with that child
            │
            └─ Two children? Compare with LARGER child
                        |
            ┌───────────┴───────────┐
            │                       │
    Parent < Child?          Parent ≥ Child
            │                       │
           Yes                    STOP ✓
            │
          SWAP
            │
    Move to child's position
            │
       (Repeat process)
```

#### Time Complexity Analysis

**Worst Case:** O(log n)

**Why?** We might bubble down from root to a leaf, traversing the height of the tree.

**Best Case:** O(log n) - We always need to at least check children, so even if no swaps occur, we still traverse down.

#### Implementation

**Python (Max-Heap):**
```python
def extract_max(heap):
    """Remove and return the maximum element."""
    if not heap:
        raise IndexError("Heap is empty")
    
    if len(heap) == 1:
        return heap.pop()
    
    # Save max value
    max_value = heap[0]
    
    # Move last element to root
    heap[0] = heap.pop()
    
    # Bubble down from root
    _bubble_down(heap, 0)
    
    return max_value

def _bubble_down(heap, index):
    """Restore heap property by bubbling element down."""
    n = len(heap)
    largest = index
    left = 2 * index + 1
    right = 2 * index + 2
    
    # Find largest among parent, left child, right child
    if left < n and heap[left] > heap[largest]:
        largest = left
    
    if right < n and heap[right] > heap[largest]:
        largest = right
    
    # If largest is not parent, swap and continue
    if largest != index:
        heap[index], heap[largest] = heap[largest], heap[index]
        _bubble_down(heap, largest)
```

**Rust (Max-Heap):**
```rust
impl<T: Ord> MaxHeap<T> {
    pub fn extract_max(&mut self) -> Option<T> {
        if self.data.is_empty() {
            return None;
        }
        
        if self.data.len() == 1 {
            return self.data.pop();
        }
        
        // Save max, move last to root
        let max_value = self.data.swap_remove(0);
        
        // Bubble down from root
        self.bubble_down(0);
        
        Some(max_value)
    }
    
    fn bubble_down(&mut self, mut index: usize) {
        let len = self.data.len();
        
        loop {
            let left = 2 * index + 1;
            let right = 2 * index + 2;
            let mut largest = index;
            
            if left < len && self.data[left] > self.data[largest] {
                largest = left;
            }
            
            if right < len && self.data[right] > self.data[largest] {
                largest = right;
            }
            
            if largest != index {
                self.data.swap(index, largest);
                index = largest;
            } else {
                break;
            }
        }
    }
}
```

**C (Max-Heap):**
```c
int extract_max(int* heap, int* size) {
    if (*size == 0) {
        fprintf(stderr, "Heap is empty\n");
        exit(1);
    }
    
    int max_value = heap[0];
    
    // Move last element to root
    heap[0] = heap[*size - 1];
    (*size)--;
    
    // Bubble down
    bubble_down(heap, 0, *size);
    
    return max_value;
}

void bubble_down(int* heap, int index, int size) {
    while (1) {
        int left = 2 * index + 1;
        int right = 2 * index + 2;
        int largest = index;
        
        if (left < size && heap[left] > heap[largest]) {
            largest = left;
        }
        
        if (right < size && heap[right] > heap[largest]) {
            largest = right;
        }
        
        if (largest != index) {
            // Swap
            int temp = heap[index];
            heap[index] = heap[largest];
            heap[largest] = temp;
            
            index = largest;
        } else {
            break;
        }
    }
}
```

**C++ (Max-Heap):**
```cpp
template<typename T>
class MaxHeap {
private:
    std::vector<T> data;
    
    void bubbleDown(size_t index) {
        size_t size = data.size();
        
        while (true) {
            size_t left = 2 * index + 1;
            size_t right = 2 * index + 2;
            size_t largest = index;
            
            if (left < size && data[left] > data[largest]) {
                largest = left;
            }
            
            if (right < size && data[right] > data[largest]) {
                largest = right;
            }
            
            if (largest != index) {
                std::swap(data[index], data[largest]);
                index = largest;
            } else {
                break;
            }
        }
    }
    
public:
    T extractMax() {
        if (data.empty()) {
            throw std::runtime_error("Heap is empty");
        }
        
        T max_value = data[0];
        data[0] = data.back();
        data.pop_back();
        
        if (!data.empty()) {
            bubbleDown(0);
        }
        
        return max_value;
    }
};
```

**Go (Max-Heap):**
```go
func (h *MaxHeap) ExtractMax() (int, error) {
    if len(h.data) == 0 {
        return 0, errors.New("heap is empty")
    }
    
    maxValue := h.data[0]
    
    // Move last to root
    h.data[0] = h.data[len(h.data)-1]
    h.data = h.data[:len(h.data)-1]
    
    // Bubble down
    if len(h.data) > 0 {
        h.bubbleDown(0)
    }
    
    return maxValue, nil
}

func (h *MaxHeap) bubbleDown(index int) {
    size := len(h.data)
    
    for {
        left := 2*index + 1
        right := 2*index + 2
        largest := index
        
        if left < size && h.data[left] > h.data[largest] {
            largest = left
        }
        
        if right < size && h.data[right] > h.data[largest] {
            largest = right
        }
        
        if largest != index {
            h.data[index], h.data[largest] = h.data[largest], h.data[index]
            index = largest
        } else {
            break
        }
    }
}
```

---

## 5. Building a Heap (Heapify) - The O(n) Miracle

### The Problem

Given an unsorted array, convert it into a valid heap.

**Naive Approach:** Insert elements one by one

- Time Complexity: O(n log n)

**Optimal Approach:** Build from bottom-up

- Time Complexity: O(n) ⭐

### Why O(n) is Surprising

**Intuition that seems wrong:** "We need to bubble down n/2 nodes, each taking O(log n) time, so shouldn't it be O(n log n)?"

**The Breakthrough:** Most nodes are near the bottom! They have very short bubble-down distances.

### The Algorithm: Floyd's Heap Construction

```
Insight: Start from the LAST non-leaf node and bubble down.

Why last non-leaf? 
- Leaf nodes are already valid heaps (trivially)
- We only need to fix internal nodes

Last non-leaf node index: (n/2) - 1

Process:
1. Start from index (n/2) - 1
2. Bubble down current node
3. Move to previous index
4. Repeat until index 0
```

#### Visual Example

```
Input array: [4, 10, 3, 5, 1]

Array visualization:
Index:  0   1  2  3  4
Value: [4, 10, 3, 5, 1]

As a tree (not yet a heap):
        4
       / \
     10   3
     / \
    5   1

Step 1: Start at last non-leaf = (5/2)-1 = 1 (value 10)
Bubble down 10:
  10's children: 5, 1
  10 > both, no swap needed

Step 2: Move to index 0 (value 4)
Bubble down 4:
  4's children: 10, 3
  10 > 4, SWAP with larger child (10)
  
        10
       / \
      4   3
     / \
    5   1

  Continue bubble down 4:
  4's children: 5, 1
  5 > 4, SWAP
  
        10
       / \
      5   3
     / \
    4   1

DONE! Valid Max-Heap ✓
```

### Time Complexity Proof (Intuitive)

```
Height | Nodes at height | Max bubbledowns per node | Work
-------|-----------------|-------------------------|------
  0    |     n/2         |           0             |  0
  1    |     n/4         |           1             | n/4
  2    |     n/8         |           2             | n/4
  3    |     n/16        |           3             | 3n/16
  ...  |     ...         |          ...            | ...

Total work = n/4 + n/4 + 3n/16 + ... 
           = n * (1/4 + 1/4 + 3/16 + ...)
           = n * (sum of series that converges to a constant)
           = O(n) ✓
```

**Key Insight:** The sum of (nodes at level) × (distance to bottom) is bounded by 2n, giving us O(n).

### Implementation

**Python:**
```python
def heapify(arr):
    """Convert array into a max-heap in-place."""
    n = len(arr)
    
    # Start from last non-leaf node
    for i in range(n // 2 - 1, -1, -1):
        _bubble_down(arr, i, n)

def _bubble_down(heap, index, heap_size):
    """Bubble down for heapify operation."""
    while True:
        largest = index
        left = 2 * index + 1
        right = 2 * index + 2
        
        if left < heap_size and heap[left] > heap[largest]:
            largest = left
        
        if right < heap_size and heap[right] > heap[largest]:
            largest = right
        
        if largest != index:
            heap[index], heap[largest] = heap[largest], heap[index]
            index = largest
        else:
            break

# Example usage:
arr = [4, 10, 3, 5, 1]
heapify(arr)
print(arr)  # [10, 5, 3, 4, 1]
```

**Rust:**
```rust
pub fn heapify<T: Ord>(data: &mut [T]) {
    let n = data.len();
    
    // Start from last non-leaf node
    if n > 1 {
        for i in (0..=n/2 - 1).rev() {
            bubble_down(data, i, n);
        }
    }
}

fn bubble_down<T: Ord>(data: &mut [T], mut index: usize, heap_size: usize) {
    loop {
        let left = 2 * index + 1;
        let right = 2 * index + 2;
        let mut largest = index;
        
        if left < heap_size && data[left] > data[largest] {
            largest = left;
        }
        
        if right < heap_size && data[right] > data[largest] {
            largest = right;
        }
        
        if largest != index {
            data.swap(index, largest);
            index = largest;
        } else {
            break;
        }
    }
}
```

**C:**
```c
void heapify(int* arr, int n) {
    // Start from last non-leaf node
    for (int i = n / 2 - 1; i >= 0; i--) {
        bubble_down(arr, i, n);
    }
}

// bubble_down function same as shown earlier
```

**C++:**
```cpp
template<typename T>
void heapify(std::vector<T>& data) {
    int n = data.size();
    
    // Start from last non-leaf
    for (int i = n / 2 - 1; i >= 0; i--) {
        bubbleDown(data, i, n);
    }
}
```

**Go:**
```go
func Heapify(data []int) {
    n := len(data)
    
    // Start from last non-leaf
    for i := n/2 - 1; i >= 0; i-- {
        bubbleDown(data, i, n)
    }
}
```

---

## 6. Heap Sort

### The Beautiful Algorithm

Heap Sort combines the heap data structure with a clever in-place sorting technique.

**The Strategy:**
1. Build a max-heap from the array: O(n)
2. Repeatedly extract max and place it at the end: O(n log n)

**Total Time:** O(n log n)
**Space:** O(1) - In-place!

### The Algorithm Flow

```
Phase 1: Heapify
Input: [4, 10, 3, 5, 1]
After heapify: [10, 5, 3, 4, 1]

Phase 2: Extract and place
Iteration 1:
  Swap root with last element: [1, 5, 3, 4, 10]
  Heap portion: [1, 5, 3, 4] | Sorted: [10]
  Bubble down in heap: [5, 4, 3, 1] | Sorted: [10]

Iteration 2:
  Swap root with last: [1, 4, 3, 5, 10]
  Heap portion: [1, 4, 3] | Sorted: [5, 10]
  Bubble down: [4, 1, 3] | Sorted: [5, 10]

Iteration 3:
  Swap: [3, 1, 4, 5, 10]
  Heap portion: [3, 1] | Sorted: [4, 5, 10]
  Bubble down: [3, 1] | Sorted: [4, 5, 10]

Iteration 4:
  Swap: [1, 3, 4, 5, 10]
  Heap portion: [1] | Sorted: [3, 4, 5, 10]

Final: [1, 3, 4, 5, 10] ✓
```

### ASCII Visualization

```
Initial array: [4, 10, 3, 5, 1]

┌─────────────────────────────┐
│  Phase 1: Build Max-Heap    │
└─────────────────────────────┘
Result: [10, 5, 3, 4, 1]
        └─┬─┘
         Max at root

┌─────────────────────────────┐
│  Phase 2: Sort              │
└─────────────────────────────┘

Pass 1:
[10, 5, 3, 4, | 1]  → Swap 10 with last
[1, 5, 3, 4, | 10]  → Bubble down 1
[5, 4, 3, 1, | 10]  ✓

Pass 2:
[5, 4, 3, | 1, 10]  → Swap 5 with last
[1, 4, 3, | 5, 10]  → Bubble down 1
[4, 1, 3, | 5, 10]  ✓

Pass 3:
[4, 1, | 3, 5, 10]  → Swap 4 with last
[3, 1, | 4, 5, 10]  → Bubble down 3
[3, 1, | 4, 5, 10]  ✓

Pass 4:
[3, | 1, 4, 5, 10]  → Swap 3 with last
[1, | 3, 4, 5, 10]  ✓

Final sorted: [1, 3, 4, 5, 10]
```

### Implementation

**Python:**
```python
def heap_sort(arr):
    """Sort array in ascending order usingheap sort."""
    n = len(arr)
    
    # Phase 1: Build max-heap
    heapify(arr)
    
    # Phase 2: Extract elements one by one
    for i in range(n - 1, 0, -1):
        # Move current root to end
        arr[0], arr[i] = arr[i], arr[0]
        
        # Bubble down in reduced heap
        _bubble_down(arr, 0, i)

# Example:
arr = [4, 10, 3, 5, 1]
heap_sort(arr)
print(arr)  # [1, 3, 4, 5, 10]
```

**Rust:**
```rust
pub fn heap_sort<T: Ord>(data: &mut [T]) {
    let n = data.len();
    
    // Phase 1: Heapify
    heapify(data);
    
    // Phase 2: Sort
    for i in (1..n).rev() {
        data.swap(0, i);
        bubble_down(data, 0, i);
    }
}
```

**C:**
```c
void heap_sort(int* arr, int n) {
    // Phase 1: Heapify
    heapify(arr, n);
    
    // Phase 2: Sort
    for (int i = n - 1; i > 0; i--) {
        // Swap
        int temp = arr[0];
        arr[0] = arr[i];
        arr[i] = temp;
        
        // Bubble down
        bubble_down(arr, 0, i);
    }
}
```

**C++:**
```cpp
template<typename T>
void heapSort(std::vector<T>& data) {
    int n = data.size();
    
    // Heapify
    heapify(data);
    
    // Sort
    for (int i = n - 1; i > 0; i--) {
        std::swap(data[0], data[i]);
        bubbleDown(data, 0, i);
    }
}
```

**Go:**
```go
func HeapSort(data []int) {
    n := len(data)
    
    // Heapify
    Heapify(data)
    
    // Sort
    for i := n - 1; i > 0; i-- {
        data[0], data[i] = data[i], data[0]
        bubbleDown(data, 0, i)
    }
}
```

### Heap Sort Characteristics

| Property | Value | Notes |
|----------|-------|-------|
| Time (Best) | O(n log n) | Always n log n, no best case |
| Time (Average) | O(n log n) | Consistent performance |
| Time (Worst) | O(n log n) | Unlike quicksort |
| Space | O(1) | In-place ⭐ |
| Stable? | No | Relative order not preserved |
| Cache-friendly? | No | Poor locality of reference |

**When to use Heap Sort:**
- When you need guaranteed O(n log n) time
- When memory is constrained (in-place)
- When you want to avoid quicksort's worst case

**When NOT to use:**
- When you need stability
- When cache performance matters (use merge sort or quicksort instead)

---

## 7. Priority Queue Applications

### What is a Priority Queue?

**Abstract Data Type (ADT):** A queue where each element has a "priority," and elements are dequeued in priority order.

**Heap is the perfect implementation** for a priority queue!

```
Operations:
- insert(element, priority): Add with priority
- extract_max/min(): Remove highest priority element
- peek(): View highest priority element
- update_priority(): Change element's priority
```

### Real-World Applications

#### 1. Dijkstra's Shortest Path Algorithm

**Problem:** Find shortest path from source to all vertices in a weighted graph.

**Why Priority Queue?** We always want to explore the vertex with the shortest known distance next.

```
Algorithm sketch:
1. Start with source vertex (distance 0)
2. While priority queue not empty:
   a. Extract vertex with minimum distance
   b. For each neighbor:
      - Calculate new distance through current vertex
      - If shorter, update distance and add to queue

Priority Queue ensures we always process closest vertex first!
```

**Python example:**
```python
import heapq

def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # Min-heap: (distance, node)
    pq = [(0, start)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        # Skip if we've found better path
        if current_dist > distances[current]:
            continue
        
        # Explore neighbors
        for neighbor, weight in graph[current]:
            distance = current_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances
```

#### 2. Task Scheduling (Operating Systems)

**Problem:** CPU needs to decide which process/thread to run next.

**Priority factors:** 
- Process priority level
- Waiting time
- I/O vs CPU-bound
- Real-time requirements

```python
class Task:
    def __init__(self, name, priority, arrival_time):
        self.name = name
        self.priority = priority
        self.arrival_time = arrival_time
    
    def __lt__(self, other):
        # Higher priority value = higher priority
        return self.priority > other.priority

# Scheduler using heap
import heapq

ready_queue = []
heapq.heappush(ready_queue, Task("Process1", 10, 0))
heapq.heappush(ready_queue, Task("Process2", 5, 1))
heapq.heappush(ready_queue, Task("Process3", 15, 2))

# Execute highest priority task
next_task = heapq.heappop(ready_queue)
print(f"Executing: {next_task.name}")  # Process3
```

#### 3. Median Maintenance (Running Median)

**Problem:** Maintain median of a stream of numbers.

**Brilliant Solution:** Use TWO heaps!
- Max-heap for smaller half
- Min-heap for larger half

```
Example stream: 5, 15, 1, 3

After 5:
  Max-heap (smaller): [5]
  Min-heap (larger): []
  Median: 5

After 15:
  Max-heap: [5]
  Min-heap: [15]
  Median: (5+15)/2 = 10

After 1:
  Max-heap: [5, 1]
  Min-heap: [15]
  Median: 5 (middle of max-heap)

After 3:
  Max-heap: [3, 1]
  Min-heap: [5, 15]
  Median: (3+5)/2 = 4
```

**Implementation:**
```python
import heapq

class MedianFinder:
    def __init__(self):
        # Max-heap (negate for max behavior)
        self.small = []  
        # Min-heap
        self.large = []
    
    def add_num(self, num):
        # Add to max-heap (small)
        heapq.heappush(self.small, -num)
        
        # Balance: ensure all small <= all large
        heapq.heappush(self.large, -heapq.heappop(self.small))
        
        # Balance sizes
        if len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))
    
    def find_median(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        else:
            return (-self.small[0] + self.large[0]) / 2
```

#### 4. Huffman Coding (Data Compression)

**Problem:** Build optimal prefix-free encoding for data compression.

**Algorithm:** Repeatedly combine two lowest-frequency nodes.

```python
import heapq

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq

def huffman_encoding(frequencies):
    """
    frequencies: dict of char -> frequency
    Returns: Huffman tree root
    """
    heap = [Node(char, freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        # Extract two minimum frequency nodes
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        # Create internal node
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        
        heapq.heappush(heap, merged)
    
    return heap[0]
```

---

## 8. Advanced Heap Variants

### 1. D-ary Heap

**Concept:** Instead of 2 children, each node has d children.

**Trade-off:**
- Shallower tree → faster bubble up
- More children to compare → slower bubble down

**Index formulas:**
```
Parent of node at index i: (i - 1) / d
k-th child of node at index i: d*i + k + 1  (k = 0, 1, ..., d-1)
```

**When to use:**
- More insertions than deletions → use larger d
- More deletions than insertions → use smaller d (binary)

### 2. Fibonacci Heap

**Key Innovation:** Lazy consolidation - defer work until necessary.

**Operations:**
```
Insert: O(1) amortized ⭐
Extract-min: O(log n) amortized
Decrease-key: O(1) amortized ⭐
Merge: O(1) ⭐
```

**Why it matters:** Theoretical improvement for Dijkstra's algorithm from O(E log V) to O(E + V log V).

**Reality check:** Constant factors are large, often slower in practice than binary heap for small graphs.

### 3. Binomial Heap

**Structure:** Collection of binomial trees with specific properties.

**Key property:** At most one binomial tree of each order.

**Advantages:**
- Efficient merge: O(log n)
- All operations O(log n)

```
Binomial tree B_k:
- B_0: Single node
- B_1: Two nodes (one parent, one child)
- B_2: Root with children B_1, B_0
- B_k: Root with children B_{k-1}, B_{k-2}, ..., B_0
```

---

## 9. Problem-Solving Patterns

### Pattern 1: Top K Elements

**Signature:** "Find K largest/smallest elements"

**Solution:** Use heap of size K!

**Mental Model:** Keep a "sliding window" of best K elements seen so far.

```python
def k_largest(nums, k):
    """Find k largest elements using min-heap of size k."""
    import heapq
    
    # Min-heap of size k
    heap = []
    
    for num in nums:
        if len(heap) < k:
            heapq.heappush(heap, num)
        elif num > heap[0]:
            heapq.heapreplace(heap, num)
    
    return heap

# Time: O(n log k), Space: O(k)
```

**Why this works:**
- We maintain the K largest seen so far
- Min-heap ensures smallest of the K is at top
- If new element > smallest of K, replace it

### Pattern 2: K-Way Merge

**Signature:** "Merge K sorted arrays/lists"

**Solution:** Use min-heap to track frontiers!

```python
def merge_k_sorted(arrays):
    """Merge k sorted arrays."""
    import heapq
    
    # Heap: (value, array_index, element_index)
    heap = []
    
    # Initialize with first element of each array
    for i, arr in enumerate(arrays):
        if arr:
            heapq.heappush(heap, (arr[0], i, 0))
    
    result = []
    
    while heap:
        val, arr_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        
        # Add next element from same array
        if elem_idx + 1 < len(arrays[arr_idx]):
            next_val = arrays[arr_idx][elem_idx + 1]
            heapq.heappush(heap, (next_val, arr_idx, elem_idx + 1))
    
    return result

# Time: O(N log k) where N = total elements, k = number of arrays
```

### Pattern 3: Interval Scheduling

**Signature:** "Meeting rooms, resource allocation"

**Example:** Minimum meeting rooms needed

```python
def min_meeting_rooms(intervals):
    """Find minimum meeting rooms needed for overlapping intervals."""
    import heapq
    
    if not intervals:
        return 0
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    # Min-heap of end times
    heap = []
    
    for start, end in intervals:
        # If earliest ending meeting finishes before this starts
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        
        heapq.heappush(heap, end)
    
    return len(heap)

# Example:
intervals = [(0, 30), (5, 10), (15, 20)]
print(min_meeting_rooms(intervals))  # 2
```

### Pattern 4: Sliding Window Maximum/Minimum

**Problem:** Find max/min in each window of size k.

**Naive:** Scan each window: O(n*k)
**Optimized with heap:** O(n log k)

```python
def sliding_window_maximum(nums, k):
    """Find maximum in each sliding window of size k."""
    import heapq
    from collections import deque
    
    # Max-heap: (negative value, index)
    heap = []
    result = []
    
    for i, num in enumerate(nums):
        heapq.heappush(heap, (-num, i))
        
        # Remove elements outside window
        while heap[0][1] <= i - k:
            heapq.heappop(heap)
        
        if i >= k - 1:
            result.append(-heap[0][0])
    
    return result
```

---

## 10. Mental Models & Advanced Insights

### Cognitive Chunking for Heaps

**Chunk 1: "Peek is free"**
- Root access: O(1)
- Useful for algorithms that need frequent "what's best?" queries

**Chunk 2: "Height = log n"**
- All operations bound by tree height
- Complete tree → guaranteed balance

**Chunk 3: "Build is faster than repeated insert"**
- Heapify: O(n)
- n insertions: O(n log n)
- **Lesson:** Batch operations when possible!

### The Hidden Structure Pattern

When you see problems involving:
- "K largest/smallest"
- "K most frequent"
- "Median"
- "Stream of data"
- "Online algorithm" (process data as it arrives)

→ **Think HEAP!**

### Problem Recognition Heuristics

```
Decision Tree for Heap Usage:

Do you need sorted order of ALL elements?
├─ Yes → Use sorting algorithm
└─ No → Continue

Do you need the top K or min/max repeatedly?
├─ Yes → HEAP! ⭐
└─ No → Continue

Do you need to process elements by priority?
├─ Yes → HEAP (Priority Queue)! ⭐
└─ No → Different structure

Is data arriving in a stream?
└─ Yes → Consider heap for online algorithms
```

### Practice Strategy (Deliberate Practice)

**Phase 1: Implementation Mastery** (Week 1-2)
1. Implement heap from scratch in all your languages
2. Write tests for edge cases
3. Visualize operations on paper

**Phase 2: Pattern Recognition** (Week 3-4)
1. Solve 20 "top K" problems
2. Solve 10 heap-sort variants
3. Solve 5 median-finding problems

**Phase 3: Advanced Applications** (Week 5-6)
1. Implement Dijkstra's with heap
2. K-way merge problems
3. Interval scheduling problems

**Phase 4: Speed & Intuition** (Week 7+)
1. Time yourself solving problems
2. Can you recognize heap problems instantly?
3. Practice explaining solutions out loud

---

## Complete Working Example: Priority Queue in All Languages

Let me provide a complete, production-ready priority queue implementation:

**Python (Using heapq):**
```python
import heapq

class PriorityQueue:
    def __init__(self, max_heap=False):
        self.heap = []
        self.max_heap = max_heap
    
    def push(self, item, priority):
        if self.max_heap:
            priority = -priority
        heapq.heappush(self.heap, (priority, item))
    
    def pop(self):
        if not self.heap:
            raise IndexError("pop from empty priority queue")
        priority, item = heapq.heappop(self.heap)
        if self.max_heap:
            priority = -priority
        return item, priority
    
    def peek(self):
        if not self.heap:
            return None
        priority, item = self.heap[0]
        if self.max_heap:
            priority = -priority
        return item, priority
    
    def __len__(self):
        return len(self.heap)
    
    def is_empty(self):
        return len(self.heap) == 0

# Usage:
pq = PriorityQueue(max_heap=True)
pq.push("Task A", 5)
pq.push("Task B", 10)
pq.push("Task C", 3)

while not pq.is_empty():
    task, priority = pq.pop()
    print(f"{task}: {priority}")
# Output:
# Task B: 10
# Task A: 5
# Task C: 3
```

**Rust (Complete Implementation):**
```rust
use std::collections::BinaryHeap;
use std::cmp::Ordering;

#[derive(Eq, PartialEq)]
struct Task {
    name: String,
    priority: i32,
}

impl Ord for Task {
    fn cmp(&self, other: &Self) -> Ordering {
        self.priority.cmp(&other.priority)
    }
}

impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn main() {
    let mut pq = BinaryHeap::new();
    
    pq.push(Task { name: "Task A".to_string(), priority: 5 });
    pq.push(Task { name: "Task B".to_string(), priority: 10 });
    pq.push(Task { name: "Task C".to_string(), priority: 3 });
    
    while let Some(task) = pq.pop() {
        println!("{}: {}", task.name, task.priority);
    }
}
```

---

## Final Wisdom: The Path to Mastery

### The Three Levels of Understanding

**Level 1: Mechanical** (Weeks 1-2)
- You can implement operations
- You follow algorithms step-by-step
- You need to think consciously

**Level 2: Intuitive** (Weeks 3-6)
- You recognize patterns instantly
- You see heap solutions naturally
- Operations feel "obvious"

**Level 3: Creative** (Weeks 7+)
- You modify heap for novel problems
- You combine heap with other structures
- You invent new applications

### Daily Practice Ritual

```
Morning (30 min):
├─ Review one concept deeply
└─ Implement from memory

Afternoon (60 min):
├─ Solve 2-3 problems
└─ Analyze time/space complexity

Evening (30 min):
├─ Review mistakes
└─ Visualize problem solutions mentally
```

### The Monk's Approach

**Focus:** One concept at a time, deeply
**Discipline:** Daily practice, no exceptions
**Reflection:** Why did this solution work? What did I miss?
**Flow:** Enter a state of absorbed concentration

**Remember:** Top 1% isn't about knowing more—it's about seeing patterns others miss, thinking clearly under pressure, and having solutions emerge naturally from deep understanding.

---

**You now have the complete foundation. The next step is deliberate practice. Start implementing, start solving, and watch your intuition grow.** 🚀

## Comprehensive Guide to Heap Data Structure Implementation

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

