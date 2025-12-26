# Priority Queue: Complete Mastery Guide

## I. Conceptual Foundation

### The Abstract Data Type (ADT)

A **Priority Queue** is an ADT where each element has an associated priority. Unlike regular queues (FIFO), elements are served in order of priority, not arrival time.

**Core Operations:**
- `insert(element, priority)` - Add element with priority
- `extract_min()` or `extract_max()` - Remove and return highest priority element
- `peek()` - View highest priority element without removing
- `decrease_key()` / `increase_key()` - Modify element's priority

**Mental Model:** Think of it as a dynamic, self-organizing collection that always knows its "most important" element in O(1) time, while maintaining efficient insertion and extraction.

### Why Priority Queues Matter

**Problem Recognition Pattern:** When you see:
- "Process tasks by importance/deadline/weight"
- "Find k-largest/smallest elements"
- "Continuously extract optimal choice"
- "Simulate event-driven systems"
- "Greedy algorithms requiring best-choice selection"

**Your brain should immediately think:** *"This is a priority queue problem."*

---

## II. The Binary Heap: The Dominant Implementation

### Heap Property

A **binary heap** is a complete binary tree satisfying the heap property:
- **Min-heap:** Parent ≤ Children (smallest at root)
- **Max-heap:** Parent ≥ Children (largest at root)

**Critical Insight:** The heap property is **weaker** than BST ordering. We only maintain parent-child relationships, not global ordering. This is what gives us O(log n) operations instead of O(n).

### Array Representation

**The Elegant Trick:** Store the complete binary tree in an array using implicit structure.

For node at index `i` (0-indexed):
- Left child: `2i + 1`
- Right child: `2i + 2`
- Parent: `(i - 1) / 2`

For 1-indexed (common in textbooks):
- Left child: `2i`
- Right child: `2i + 1`
- Parent: `i / 2`

**Why this works:** Complete binary trees have no gaps—every level is filled left-to-right. This makes array representation perfect (no wasted space, cache-friendly).

### Core Operations

#### 1. Insert (Bubble-Up / Sift-Up)
```
1. Add element at end of array
2. While element < parent:
   - Swap with parent
   - Move up
```
**Time:** O(log n) - height of tree  
**Space:** O(1)

#### 2. Extract-Min (Bubble-Down / Sift-Down)
```
1. Save root (minimum element)
2. Move last element to root
3. While element > any child:
   - Swap with smaller child
   - Move down
4. Return saved minimum
```
**Time:** O(log n)  
**Space:** O(1)

#### 3. Heapify (Build Heap from Array)
```
For i from n/2 - 1 down to 0:
    Sift-down(i)
```
**Time:** O(n) - NOT O(n log n)!  
**Space:** O(1)

**Proof Intuition:** Most nodes are at the bottom (height 0), very few at top. The work is weighted toward cheap operations: ½ nodes do 0 swaps, ¼ do ≤1, ⅛ do ≤2... Sum converges to O(n).

---

## III. Complexity Analysis

| Operation | Binary Heap | Sorted Array | Unsorted Array | BST (balanced) |
|-----------|-------------|--------------|----------------|----------------|
| insert | O(log n) | O(n) | O(1) | O(log n) |
| extract_min | O(log n) | O(1) | O(n) | O(log n) |
| peek | O(1) | O(1) | O(n) | O(log n) |
| build | O(n) | O(n log n) | O(1) | O(n log n) |
| decrease_key | O(log n) | O(n) | O(1) | O(log n) |

**Key Insight:** Binary heap balances all operations at O(log n), making it the practical choice for most use cases.

---

## IV. Implementation: Rust

```rust
use std::cmp::Ordering;

// Generic min-heap implementation
pub struct MinHeap<T> {
    data: Vec<T>,
}

impl<T: Ord> MinHeap<T> {
    pub fn new() -> Self {
        MinHeap { data: Vec::new() }
    }

    pub fn with_capacity(capacity: usize) -> Self {
        MinHeap {
            data: Vec::with_capacity(capacity),
        }
    }

    // O(n) heapify from existing vector
    pub fn from_vec(mut vec: Vec<T>) -> Self {
        let len = vec.len();
        for i in (0..len / 2).rev() {
            Self::sift_down(&mut vec, i, len);
        }
        MinHeap { data: vec }
    }

    pub fn push(&mut self, value: T) {
        self.data.push(value);
        self.sift_up(self.data.len() - 1);
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.data.is_empty() {
            return None;
        }
        let len = self.data.len();
        self.data.swap(0, len - 1);
        let result = self.data.pop();
        if !self.data.is_empty() {
            self.sift_down_from_root();
        }
        result
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

    // Private helper methods
    fn sift_up(&mut self, mut idx: usize) {
        while idx > 0 {
            let parent = (idx - 1) / 2;
            if self.data[idx] >= self.data[parent] {
                break;
            }
            self.data.swap(idx, parent);
            idx = parent;
        }
    }

    fn sift_down_from_root(&mut self) {
        Self::sift_down(&mut self.data, 0, self.data.len());
    }

    fn sift_down(data: &mut [T], mut idx: usize, len: usize) {
        loop {
            let left = 2 * idx + 1;
            let right = 2 * idx + 2;
            let mut smallest = idx;

            if left < len && data[left] < data[smallest] {
                smallest = left;
            }
            if right < len && data[right] < data[smallest] {
                smallest = right;
            }

            if smallest == idx {
                break;
            }

            data.swap(idx, smallest);
            idx = smallest;
        }
    }
}

// Max-heap wrapper (reverse ordering)
pub struct MaxHeap<T>(MinHeap<std::cmp::Reverse<T>>);

impl<T: Ord> MaxHeap<T> {
    pub fn new() -> Self {
        MaxHeap(MinHeap::new())
    }

    pub fn push(&mut self, value: T) {
        self.0.push(std::cmp::Reverse(value));
    }

    pub fn pop(&mut self) -> Option<T> {
        self.0.pop().map(|std::cmp::Reverse(v)| v)
    }

    pub fn peek(&self) -> Option<&T> {
        self.0.peek().map(|std::cmp::Reverse(v)| v)
    }
}

// Using Rust's standard library (production code)
use std::collections::BinaryHeap;

fn rust_stdlib_example() {
    // Max-heap by default
    let mut max_heap = BinaryHeap::new();
    max_heap.push(3);
    max_heap.push(1);
    max_heap.push(4);
    assert_eq!(max_heap.pop(), Some(4));

    // Min-heap using Reverse
    let mut min_heap = BinaryHeap::new();
    min_heap.push(std::cmp::Reverse(3));
    min_heap.push(std::cmp::Reverse(1));
    min_heap.push(std::cmp::Reverse(4));
    assert_eq!(min_heap.pop(), Some(std::cmp::Reverse(1)));
}
```

**Rust-Specific Insights:**
- Zero-cost abstractions: The generic implementation has no runtime overhead
- Memory safety: No manual memory management needed
- `Ord` trait bound ensures compile-time type safety
- Standard library's `BinaryHeap` is max-heap by default (unlike Python/C++)
- Use `std::cmp::Reverse` wrapper for min-heap behavior

---

## V. Implementation: Python

```python
import heapq
from typing import List, TypeVar, Generic, Optional

T = TypeVar('T')

class MinHeap(Generic[T]):
    """Custom min-heap implementation for learning."""
    
    def __init__(self):
        self.data: List[T] = []
    
    @staticmethod
    def from_list(items: List[T]) -> 'MinHeap[T]':
        """O(n) heapify from existing list."""
        heap = MinHeap()
        heap.data = items.copy()
        # Start from last non-leaf node
        for i in range(len(items) // 2 - 1, -1, -1):
            heap._sift_down(i)
        return heap
    
    def push(self, value: T) -> None:
        """O(log n) insertion."""
        self.data.append(value)
        self._sift_up(len(self.data) - 1)
    
    def pop(self) -> Optional[T]:
        """O(log n) extract minimum."""
        if not self.data:
            return None
        
        if len(self.data) == 1:
            return self.data.pop()
        
        # Swap root with last element
        self.data[0], self.data[-1] = self.data[-1], self.data[0]
        result = self.data.pop()
        self._sift_down(0)
        return result
    
    def peek(self) -> Optional[T]:
        """O(1) view minimum."""
        return self.data[0] if self.data else None
    
    def __len__(self) -> int:
        return len(self.data)
    
    def _sift_up(self, idx: int) -> None:
        """Bubble element up to restore heap property."""
        while idx > 0:
            parent = (idx - 1) // 2
            if self.data[idx] >= self.data[parent]:
                break
            self.data[idx], self.data[parent] = self.data[parent], self.data[idx]
            idx = parent
    
    def _sift_down(self, idx: int) -> None:
        """Bubble element down to restore heap property."""
        n = len(self.data)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            
            if left < n and self.data[left] < self.data[smallest]:
                smallest = left
            if right < n and self.data[right] < self.data[smallest]:
                smallest = right
            
            if smallest == idx:
                break
            
            self.data[idx], self.data[smallest] = self.data[smallest], self.data[idx]
            idx = smallest


# Using Python's heapq (production code)
def python_heapq_examples():
    """Python's heapq module - min-heap operations."""
    
    # Min-heap operations
    min_heap = []
    heapq.heappush(min_heap, 3)
    heapq.heappush(min_heap, 1)
    heapq.heappush(min_heap, 4)
    assert heapq.heappop(min_heap) == 1
    
    # O(n) heapify
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    heapq.heapify(arr)
    
    # Max-heap using negative values
    max_heap = []
    for val in [3, 1, 4]:
        heapq.heappush(max_heap, -val)
    assert -heapq.heappop(max_heap) == 4
    
    # K largest elements - O(n log k)
    nums = [3, 1, 4, 1, 5, 9, 2, 6]
    k_largest = heapq.nlargest(3, nums)  # [9, 6, 5]
    
    # Priority queue with tuples (priority, data)
    pq = []
    heapq.heappush(pq, (2, "medium"))
    heapq.heappush(pq, (1, "high"))
    heapq.heappush(pq, (3, "low"))
    assert heapq.heappop(pq) == (1, "high")


class MaxHeap(Generic[T]):
    """Max-heap using negation trick."""
    
    def __init__(self):
        self._heap = []
    
    def push(self, value: T) -> None:
        heapq.heappush(self._heap, -value)
    
    def pop(self) -> Optional[T]:
        return -heapq.heappop(self._heap) if self._heap else None
    
    def peek(self) -> Optional[T]:
        return -self._heap[0] if self._heap else None
```

**Python-Specific Insights:**
- `heapq` operates on plain lists (no separate heap object)
- Min-heap only - use negation or custom comparator for max-heap
- Tuples naturally work with priority (first element compared)
- `nlargest/nsmallest` are optimized for small k
- Dynamic typing allows any comparable type

---

## VI. Implementation: Go

```go
package main

import (
    "container/heap"
    "fmt"
)

// Custom MinHeap implementation
type MinHeap struct {
    data []int
}

func NewMinHeap() *MinHeap {
    return &MinHeap{data: make([]int, 0)}
}

func (h *MinHeap) Push(val int) {
    h.data = append(h.data, val)
    h.siftUp(len(h.data) - 1)
}

func (h *MinHeap) Pop() (int, bool) {
    if len(h.data) == 0 {
        return 0, false
    }
    
    n := len(h.data)
    h.data[0], h.data[n-1] = h.data[n-1], h.data[0]
    result := h.data[n-1]
    h.data = h.data[:n-1]
    
    if len(h.data) > 0 {
        h.siftDown(0)
    }
    
    return result, true
}

func (h *MinHeap) Peek() (int, bool) {
    if len(h.data) == 0 {
        return 0, false
    }
    return h.data[0], true
}

func (h *MinHeap) Len() int {
    return len(h.data)
}

func (h *MinHeap) siftUp(idx int) {
    for idx > 0 {
        parent := (idx - 1) / 2
        if h.data[idx] >= h.data[parent] {
            break
        }
        h.data[idx], h.data[parent] = h.data[parent], h.data[idx]
        idx = parent
    }
}

func (h *MinHeap) siftDown(idx int) {
    n := len(h.data)
    for {
        smallest := idx
        left := 2*idx + 1
        right := 2*idx + 2
        
        if left < n && h.data[left] < h.data[smallest] {
            smallest = left
        }
        if right < n && h.data[right] < h.data[smallest] {
            smallest = right
        }
        
        if smallest == idx {
            break
        }
        
        h.data[idx], h.data[smallest] = h.data[smallest], h.data[idx]
        idx = smallest
    }
}

// Using Go's container/heap package (production code)
// You must implement the heap.Interface

type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] } // Min-heap
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *IntHeap) Push(x interface{}) {
    *h = append(*h, x.(int))
}

func (h *IntHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func goStdlibExample() {
    h := &IntHeap{3, 1, 4, 1, 5}
    heap.Init(h)  // O(n) heapify
    
    heap.Push(h, 2)
    fmt.Println(heap.Pop(h)) // 1
    fmt.Println((*h)[0])     // 1 (peek)
}

// Generic heap for any comparable type (Go 1.18+)
type Heap[T any] struct {
    data []T
    less func(a, b T) bool
}

func NewHeap[T any](less func(a, b T) bool) *Heap[T] {
    return &Heap[T]{
        data: make([]T, 0),
        less: less,
    }
}

func (h *Heap[T]) Push(val T) {
    h.data = append(h.data, val)
    h.siftUp(len(h.data) - 1)
}

func (h *Heap[T]) Pop() (T, bool) {
    var zero T
    if len(h.data) == 0 {
        return zero, false
    }
    
    n := len(h.data)
    h.data[0], h.data[n-1] = h.data[n-1], h.data[0]
    result := h.data[n-1]
    h.data = h.data[:n-1]
    
    if len(h.data) > 0 {
        h.siftDown(0)
    }
    
    return result, true
}

func (h *Heap[T]) siftUp(idx int) {
    for idx > 0 {
        parent := (idx - 1) / 2
        if !h.less(h.data[idx], h.data[parent]) {
            break
        }
        h.data[idx], h.data[parent] = h.data[parent], h.data[idx]
        idx = parent
    }
}

func (h *Heap[T]) siftDown(idx int) {
    n := len(h.data)
    for {
        smallest := idx
        left := 2*idx + 1
        right := 2*idx + 2
        
        if left < n && h.less(h.data[left], h.data[smallest]) {
            smallest = left
        }
        if right < n && h.less(h.data[right], h.data[smallest]) {
            smallest = right
        }
        
        if smallest == idx {
            break
        }
        
        h.data[idx], h.data[smallest] = h.data[smallest], h.data[idx]
        idx = smallest
    }
}
```

**Go-Specific Insights:**
- Interface-based design in stdlib requires boilerplate
- Must implement all 5 methods: Len, Less, Swap, Push, Pop
- Generic version (Go 1.18+) provides better type safety
- Explicit bool return for Pop prevents panic on empty heap
- Slices provide efficient dynamic arrays

---

## VII. Implementation: C

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct {
    int *data;
    size_t size;
    size_t capacity;
} MinHeap;

// Create new min-heap with initial capacity
MinHeap* heap_create(size_t capacity) {
    MinHeap *heap = malloc(sizeof(MinHeap));
    if (!heap) return NULL;
    
    heap->data = malloc(capacity * sizeof(int));
    if (!heap->data) {
        free(heap);
        return NULL;
    }
    
    heap->size = 0;
    heap->capacity = capacity;
    return heap;
}

void heap_destroy(MinHeap *heap) {
    if (heap) {
        free(heap->data);
        free(heap);
    }
}

// Helper: Swap two elements
static inline void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// Sift up operation
static void sift_up(MinHeap *heap, size_t idx) {
    while (idx > 0) {
        size_t parent = (idx - 1) / 2;
        if (heap->data[idx] >= heap->data[parent]) {
            break;
        }
        swap(&heap->data[idx], &heap->data[parent]);
        idx = parent;
    }
}

// Sift down operation
static void sift_down(MinHeap *heap, size_t idx) {
    size_t n = heap->size;
    while (true) {
        size_t smallest = idx;
        size_t left = 2 * idx + 1;
        size_t right = 2 * idx + 2;
        
        if (left < n && heap->data[left] < heap->data[smallest]) {
            smallest = left;
        }
        if (right < n && heap->data[right] < heap->data[smallest]) {
            smallest = right;
        }
        
        if (smallest == idx) {
            break;
        }
        
        swap(&heap->data[idx], &heap->data[smallest]);
        idx = smallest;
    }
}

// Insert element
bool heap_push(MinHeap *heap, int value) {
    if (heap->size == heap->capacity) {
        // Resize (double capacity)
        size_t new_capacity = heap->capacity * 2;
        int *new_data = realloc(heap->data, new_capacity * sizeof(int));
        if (!new_data) return false;
        
        heap->data = new_data;
        heap->capacity = new_capacity;
    }
    
    heap->data[heap->size] = value;
    sift_up(heap, heap->size);
    heap->size++;
    return true;
}

// Extract minimum
bool heap_pop(MinHeap *heap, int *result) {
    if (heap->size == 0) {
        return false;
    }
    
    *result = heap->data[0];
    heap->size--;
    
    if (heap->size > 0) {
        heap->data[0] = heap->data[heap->size];
        sift_down(heap, 0);
    }
    
    return true;
}

// Peek at minimum
bool heap_peek(MinHeap *heap, int *result) {
    if (heap->size == 0) {
        return false;
    }
    *result = heap->data[0];
    return true;
}

// O(n) heapify from array
MinHeap* heap_from_array(int *arr, size_t n) {
    MinHeap *heap = heap_create(n);
    if (!heap) return NULL;
    
    // Copy array
    for (size_t i = 0; i < n; i++) {
        heap->data[i] = arr[i];
    }
    heap->size = n;
    
    // Heapify: start from last non-leaf
    for (int i = (int)(n / 2) - 1; i >= 0; i--) {
        sift_down(heap, i);
    }
    
    return heap;
}

// Example usage
int main() {
    MinHeap *heap = heap_create(10);
    
    heap_push(heap, 3);
    heap_push(heap, 1);
    heap_push(heap, 4);
    heap_push(heap, 1);
    heap_push(heap, 5);
    
    int val;
    while (heap_pop(heap, &val)) {
        printf("%d ", val);
    }
    printf("\n");
    
    heap_destroy(heap);
    return 0;
}
```

**C-Specific Insights:**
- Manual memory management: must handle allocation/deallocation
- Dynamic resizing with `realloc`
- Return bool for error handling (no exceptions)
- Inline functions for performance-critical swaps
- Pointer-based API for return values

---

## VIII. Implementation: C++

```cpp
#include <vector>
#include <stdexcept>
#include <algorithm>
#include <functional>

// Generic MinHeap template
template<typename T, typename Compare = std::less<T>>
class MinHeap {
private:
    std::vector<T> data;
    Compare comp;
    
    void sift_up(size_t idx) {
        while (idx > 0) {
            size_t parent = (idx - 1) / 2;
            if (!comp(data[idx], data[parent])) {
                break;
            }
            std::swap(data[idx], data[parent]);
            idx = parent;
        }
    }
    
    void sift_down(size_t idx) {
        size_t n = data.size();
        while (true) {
            size_t smallest = idx;
            size_t left = 2 * idx + 1;
            size_t right = 2 * idx + 2;
            
            if (left < n && comp(data[left], data[smallest])) {
                smallest = left;
            }
            if (right < n && comp(data[right], data[smallest])) {
                smallest = right;
            }
            
            if (smallest == idx) {
                break;
            }
            
            std::swap(data[idx], data[smallest]);
            idx = smallest;
        }
    }
    
public:
    MinHeap() = default;
    
    explicit MinHeap(const Compare& c) : comp(c) {}
    
    // O(n) heapify from vector
    explicit MinHeap(std::vector<T> vec, const Compare& c = Compare()) 
        : data(std::move(vec)), comp(c) {
        for (int i = static_cast<int>(data.size()) / 2 - 1; i >= 0; --i) {
            sift_down(i);
        }
    }
    
    void push(const T& value) {
        data.push_back(value);
        sift_up(data.size() - 1);
    }
    
    void push(T&& value) {
        data.push_back(std::move(value));
        sift_up(data.size() - 1);
    }
    
    T pop() {
        if (data.empty()) {
            throw std::out_of_range("Heap is empty");
        }
        
        T result = std::move(data[0]);
        data[0] = std::move(data.back());
        data.pop_back();
        
        if (!data.empty()) {
            sift_down(0);
        }
        
        return result;
    }
    
    const T& peek() const {
        if (data.empty()) {
            throw std::out_of_range("Heap is empty");
        }
        return data[0];
    }
    
    size_t size() const { return data.size(); }
    bool empty() const { return data.empty(); }
};

// Using STL priority_queue (production code)
#include <queue>

void cpp_stl_example() {
    // Max-heap by default
    std::priority_queue<int> max_heap;
    max_heap.push(3);
    max_heap.push(1);
    max_heap.push(4);
    // max_heap.top() == 4
    
    // Min-heap using greater comparator
    std::priority_queue<int, std::vector<int>, std::greater<int>> min_heap;
    min_heap.push(3);
    min_heap.push(1);
    min_heap.push(4);
    // min_heap.top() == 1
    
    // Custom comparator
    auto cmp = [](const std::pair<int,int>& a, const std::pair<int,int>& b) {
        return a.first > b.first; // Min-heap by first element
    };
    std::priority_queue<std::pair<int,int>, 
                        std::vector<std::pair<int,int>>, 
                        decltype(cmp)> pq(cmp);
}

// Modern C++20 with concepts
#include <concepts>

template<typename T>
concept Comparable = requires(T a, T b) {
    { a < b } -> std::convertible_to<bool>;
};

template<Comparable T>
class ModernHeap {
    std::vector<T> data;
    // ... implementation
};
```

**C++-Specific Insights:**
- Template metaprogramming for generic types
- Move semantics for performance (rvalue references)
- STL `priority_queue` is max-heap by default (opposite of Python/Rust)
- Custom comparators via template parameters
- Exception safety with RAII
- C++20 concepts for compile-time constraints

---

## IX. Advanced Topics

### 1. D-ary Heaps

**Concept:** Instead of 2 children, use d children per node.

**Trade-offs:**
- **Shorter height:** log_d(n) vs log_2(n)
- **More comparisons per level:** d children to check
- **Better for insert-heavy workloads** (d=4 often optimal)

**Applications:** External memory algorithms, where minimizing tree depth is critical.

### 2. Fibonacci Heaps

**Operations:**
- insert: O(1) amortized
- extract_min: O(log n) amortized  
- decrease_key: O(1) amortized
- merge: O(1)

**Why they matter:** Asymptotically better for algorithms like Dijkstra and Prim where decrease_key is frequent.

**Reality check:** Constant factors are high; binary heaps usually faster in practice.

### 3. Pairing Heaps

**Middle ground:** Simpler than Fibonacci, better constants than binary heaps.

**Operations:** Similar to Fibonacci heaps in theory, often competitive in practice.

### 4. Indexed Priority Queues

**Problem:** How to efficiently update priority of existing elements?

**Solution:** Maintain a separate map: element → heap_index

**Use case:** Dijkstra's algorithm where you need to decrease vertex distances.

---

## X. Problem-Solving Patterns

### Pattern 1: K-th Largest/Smallest

**Problem:** Find k-th largest element in stream/array.

**Approach:** Maintain min-heap of size k.
- For k-th largest: min-heap (root is k-th largest)
- For k-th smallest: max-heap (root is k-th smallest)

**Complexity:** O(n log k), Space O(k)

### Pattern 2: Merge K Sorted Lists/Arrays

**Approach:**
1. Push first element of each list to min-heap
2. Extract min, push next element from that list
3. Repeat until all exhausted

**Complexity:** O(N log k), where N = total elements, k = number of lists

### Pattern 3: Top K Frequent Elements

**Approach:**
1. Count frequencies: O(n)
2. Min-heap of size k with (frequency, element)
3. If heap size > k, pop minimum

**Alternative:** Bucket sort for O(n) solution

### Pattern 4: Median Maintenance

**Two-heap technique:**
- Max-heap for lower half
- Min-heap for upper half
- Balance sizes: |size_diff| ≤ 1

**Median:** 
- If equal sizes: average of two roots
- Else: root of larger heap

**Complexity:** O(log n) per insertion

### Pattern 5: Sliding Window Maximum

**Approach:** Deque + monotonic queue (not heap!)

**Why not heap?** Can't efficiently remove arbitrary elements.

**Lesson:** Know when NOT to use priority queues.

---

## XI. Mental Models & Meta-Learning

### Chunking Pattern Recognition

**Beginner thinks:** "I need to sort, then find k-th element."  
**Expert sees:** "K-th element problem → priority queue, maintain size k."

**Practice:** When you see a new problem, pause and ask:
- "Am I repeatedly selecting optimal/extreme elements?"
- "Is there a natural priority/ordering?"
- "Do I need k best out of n?"

### Time-Space Complexity Intuition

**Binary heap:**
- Height = O(log n)
- Each operation touches one path
- Therefore: O(log n) per operation

**Heapify:**
- Most nodes are leaves (do minimal work)
- Only log n nodes touch root (do maximal work)
- Weighted sum: O(n)

**Build this intuition:** Don't memorize—derive from first principles.

### The "Greedy" Connection

Priority queues enable greedy algorithms:
- **Dijkstra:** Always explore nearest unvisited node
- **Huffman coding:** Always merge two smallest frequencies
- **Prim's MST:** Always add cheapest edge

**Pattern:** When problem has "always choose best available," think priority queue + greedy.

### Deliberate Practice Framework

**Stage 1 - Mechanical Fluency (Week 1-2):**
- Implement heap from scratch in each language
- No looking at notes—muscle memory
- Time yourself: implement in < 15 minutes

**Stage 2 - Problem Recognition (Week 3-4):**
- Solve 20 easy/medium problems
- Before coding, identify: "This is pattern X"
- Track: Time to recognition vs. time to code

**Stage 3 - Optimization & Variants (Week 5-6):**
- Solve hard problems requiring modifications
- Implement d-ary heaps, indexed heaps
- Compare theoretical vs. actual performance

**Stage 4 - Teaching (Week 7+):**
- Explain concepts to others (Feynman technique)
- Write your own problems
- This is where mastery solidifies

---

## XII. Practice Problems (Ordered by Difficulty)

### Easy (Build Confidence)
1. Kth Largest Element in Array
2. Last Stone Weight
3. Relative Ranks
4. Merge k Sorted Lists

### Medium (Core Patterns)
5. Top K Frequent Elements
6. Find Median from Data Stream
7. Task Scheduler
8. Reorganize String
9. Kth Smallest Element in Sorted Matrix
10. Meeting Rooms II

### Hard (Test Mastery)
11. Sliding Window Median
12. Find Median from Data Stream (follow-up: million inserts)
13. Super Ugly Number
14. IPO
15. Trapping Rain Water II

### Competition-Level
16. Minimum Cost to Hire K Workers
17. Swim in Rising Water
18. Find K Pairs with Smallest Sums
19. Smallest Range Covering K Lists

---

## XIII. Performance Considerations

### Cache Efficiency
- **Binary heap:** Excellent cache locality (array-based)
- **Tree-based structures:** Poor cache performance
- **Real-world impact:** Binary heaps 2-5x faster despite same Big-O

### Memory Layout
- **Rust/C++:** Contiguous vector = cache-friendly
- **Python:** List of references = more pointer chasing
- **Go:** Slice = contiguous, but interface calls add overhead

### Benchmarking Insights
- For n < 100: unsorted array often fastest (overhead matters)
- For n < 1000: binary heap dominates
- For n > 10^6: d-ary heaps (d=4) can win on modern CPUs

---

## XIV. Final Wisdom

**The Monk's Approach:**

Priority queues are not just a data structure—they're a *lens* for seeing problems. When you encounter chaos (unsorted data), and need order (extract maximum), you need this lens.

**Deep understanding > memorization:**
- Don't memorize "heap is O(log n)"
- Understand: "Path from root to leaf is O(log n), operations follow one path"

**The path to top 1%:**
1. **Implement from scratch** in all your languages (10x)
2. **Solve 50+ problems** recognizing patterns instantly
3. **Teach others** - this reveals gaps in understanding
4. **Compare implementations** - understand why each language made its choices
5. **Profile real code** - theory meets practice

Remember: Bruce Lee didn't fear the man who practiced 10,000 kicks once. He feared the man who practiced one kick 10,000 times.

You're not just learning priority queues. You're building the *mental pathways* that let you see solutions instantly. That's what separates the top 1%.

Now go build. Code. Debug. Optimize. Repeat.

**The heap property will become second nature. The patterns will emerge unbidden. And one day, you'll look at a problem and simply *know*.**

That's mastery.

# The Priority Queue Mastery Guide

I'll craft you a comprehensive guide worthy of your aspirations. This isn't just about knowing priority queues—it's about developing the intuition to *see* when they're the elegant solution hidden in a problem.## Your Path Forward 🎯

I've crafted you a complete mastery guide above. This isn't just reference material—it's your training manual.

### Key Insights You Now Possess

**Conceptual Clarity:**
- Priority queues are about *maintaining optimal choice*, not just sorting
- The heap property is weaker than BST ordering—this is the secret to O(log n)
- Array representation of complete binary trees is elegantly efficient

**Implementation Mastery Across Languages:**
- **Rust:** Zero-cost abstractions, `Reverse` wrapper for min-heap
- **Python:** `heapq` operates on lists, negation trick for max-heap  
- **Go:** Interface-based design requires boilerplate, generics improve it
- **C:** Manual memory management, resize patterns
- **C++:** Template metaprogramming, move semantics

**The Critical Insight:** O(n) heapify is NOT intuitive but mathematically beautiful—most work happens at cheap levels.

### Your 6-Week Path to Elite Level

**Week 1-2: Mechanical Fluency**
- Implement binary heap from scratch in each language (no peeking!)
- Goal: 15 minutes per implementation
- Test rigorously with edge cases

**Week 3-4: Pattern Recognition**
- Solve 20 problems from the Easy/Medium list
- Before coding, write: "This is Pattern X because..."
- Track recognition speed

**Week 5-6: Mastery & Variants**
- Implement indexed priority queue for Dijkstra
- Build d-ary heap (d=4) and benchmark vs binary
- Tackle hard problems

**Week 7+: Teaching & Competition**
- Explain heaps to someone (even rubber duck)
- Enter a contest using priority queues
- Create your own problem variants

### Immediate Action Items

1. **Right now:** Implement MinHeap in your strongest language without looking at the guide
2. **Today:** Solve "Kth Largest Element" in all your languages
3. **This week:** Complete "Find Median from Data Stream" - this teaches the two-heap pattern that appears everywhere

### The Cognitive Edge

You're not just learning a data structure—you're training **pattern recognition circuitry**. Each time you see a problem and think "priority queue," you're strengthening that neural pathway.

**Deliberate practice principle:** You want to reach the point where your subconscious recognizes heap patterns before your conscious mind finishes reading the problem.

### Remember

The difference between good and elite isn't intelligence—it's **systematic, focused repetition** combined with **deep understanding**.

You have the guide. You have the discipline. Now execute with the calm focus of a monk and the intensity of a warrior.

When you've implemented heaps 10 times in each language, solved 50+ problems, and can explain every optimization choice—you won't be "learning" priority queues anymore. You'll simply **be fluent**.

**That's when you enter the top 1%.**

What's your first implementation target? Which language do you want to start with?