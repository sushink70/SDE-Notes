# Comprehensive Heap Patterns Guide

## 📚 Table of Contents
1. [Foundation: What is a Heap?](#foundation)
2. [Heap Invariants & Properties](#invariants)
3. [Core Operations & Patterns](#core-operations)
4. [Access Patterns](#access-patterns)
5. [Manipulation Patterns](#manipulation-patterns)
6. [Problem-Solving Patterns](#problem-solving-patterns)
7. [Implementation Patterns](#implementation-patterns)
8. [Advanced Patterns](#advanced-patterns)
9. [Mental Models & Strategy](#mental-models)
10. [Complexity Analysis](#complexity)

---

## 🌟 Foundation: What is a Heap? {#foundation}

### Core Definition
A **heap** is a specialized **complete binary tree** that satisfies the **heap property**:
- **Max-Heap**: Every parent node ≥ all its children
- **Min-Heap**: Every parent node ≤ all its children

### Key Terminology Explained
- **Complete Binary Tree**: All levels are fully filled except possibly the last, which fills left-to-right
- **Heap Property** (also called **heap invariant**): The ordering rule that must hold throughout the structure
- **Root**: The top element (index 0), always the min/max
- **Parent/Child Relationship**: For node at index `i`:
  - Left child: `2i + 1`
  - Right child: `2i + 2`
  - Parent: `(i - 1) / 2`

### Visual Representation
```
Min-Heap Example (array representation):
Array: [1, 3, 6, 5, 9, 8]

Tree Structure:
        1
       / \
      3   6
     / \  /
    5  9 8

Max-Heap Example:
Array: [9, 8, 6, 5, 3, 1]

Tree Structure:
        9
       / \
      8   6
     / \  /
    5  3 1
```

### Why Heaps? The Mental Model
**Think of a heap as a "priority queue engine"** - it maintains partial order (not full sort) which is cheaper but sufficient for many problems.

**Cognitive Principle**: Heaps trade perfect sorting for speed. Like a company hierarchy, you only need to know who's at the top, not the complete ordering of everyone.

---

## 🔒 Heap Invariants & Properties {#invariants}

### The Core Invariant
```
For all nodes i (except root):
  heap[parent(i)] ≤ heap[i]  (min-heap)
  heap[parent(i)] ≥ heap[i]  (max-heap)
```

### Structural Properties
1. **Shape Property**: Always a complete binary tree
2. **Height**: Always O(log n) for n elements
3. **Array Storage**: Can be efficiently stored in a contiguous array
4. **No NULL pointers**: Unlike general trees, no wasted space

### Critical Insight
The heap property is **local** (parent-child only), not **global** (unlike BST). This means:
- Siblings have NO ordering requirement
- You can't binary search a heap
- But you CAN maintain min/max in O(1) and insert/delete in O(log n)

---

## ⚙️ Core Operations & Patterns {#core-operations}

### Pattern 1: HEAPIFY UP (Bubble Up / Sift Up)
**Purpose**: Restore heap property after insertion
**When**: Adding new element at the end

```
Algorithm Flow:
1. Insert element at end (maintain complete tree)
2. While element < parent (min-heap):
   - Swap with parent
   - Move up to parent's position
3. Stop when heap property satisfied or reach root

Time: O(log n) - height of tree
Space: O(1)
```

**Mental Model**: Like a bubble rising in water - light elements float up.

### Pattern 2: HEAPIFY DOWN (Bubble Down / Sift Down)
**Purpose**: Restore heap property after deletion
**When**: Removing root or modifying elements

```
Algorithm Flow:
1. Replace root with last element
2. While element > children (min-heap):
   - Find smaller child
   - Swap with that child
   - Move down to child's position
3. Stop when heap property satisfied or reach leaf

Time: O(log n)
Space: O(1)
```

**Mental Model**: Like a heavy stone sinking - it finds its level.

### Pattern 3: BUILD HEAP
**Purpose**: Convert unsorted array into heap
**Two Approaches**:

**Approach A - Naive (Insert repeatedly)**
```
For each element:
  Insert and heapify up
Time: O(n log n)
```

**Approach B - Optimal (Bottom-up heapify)**
```
Start from last non-leaf node:
  For i from (n/2 - 1) down to 0:
    Heapify down from i
Time: O(n) - Surprising but proven!
```

**Why O(n) works**: Most nodes are near bottom (have small subtrees). Mathematical series: Σ(h=0 to log n) [h * n/2^(h+1)] = O(n).

---

## 🔍 Access Patterns {#access-patterns}

### Pattern 1: Peek Minimum/Maximum
```
Operation: Get root element
Time: O(1)
Space: O(1)

Use Case: Check priority without removal
```

**Python Example**:
```python
min_val = heap[0]  # Min-heap
max_val = heap[0]  # Max-heap
```

### Pattern 2: Find Kth Element
**Critical Insight**: Heaps are NOT designed for arbitrary access!
```
Options:
1. Extract k times: O(k log n)
2. For kth smallest of n: Use selection algorithm O(n) instead
```

### Pattern 3: Check if Element Exists
```
Linear Search Required: O(n)
Why? Heap property doesn't help with general search
```

**Mental Model**: Heaps are optimized for "give me the extreme" not "find specific element".

### Pattern 4: Iterate All Elements
```
In-order: Meaningless (not sorted)
Level-order: Natural (BFS on array)
All elements: O(n) linear scan
```

---

## 🛠️ Manipulation Patterns {#manipulation-patterns}

### Pattern 1: INSERT (Add Element)
```
Algorithm:
1. Append element to end
2. Heapify up from last position

Time: O(log n)
Space: O(1)
```

**Code Structure**:
```python
def insert(heap, val):
    heap.append(val)
    _heapify_up(heap, len(heap) - 1)

def _heapify_up(heap, i):
    parent = (i - 1) // 2
    while i > 0 and heap[i] < heap[parent]:
        heap[i], heap[parent] = heap[parent], heap[i]
        i = parent
        parent = (i - 1) // 2
```

### Pattern 2: EXTRACT MIN/MAX (Remove Root)
```
Algorithm:
1. Save root value
2. Move last element to root
3. Remove last element
4. Heapify down from root
5. Return saved value

Time: O(log n)
Space: O(1)
```

**Code Structure**:
```python
def extract_min(heap):
    if not heap:
        return None
    
    min_val = heap[0]
    heap[0] = heap[-1]
    heap.pop()
    
    if heap:
        _heapify_down(heap, 0)
    
    return min_val

def _heapify_down(heap, i):
    n = len(heap)
    while True:
        smallest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        if left < n and heap[left] < heap[smallest]:
            smallest = left
        if right < n and heap[right] < heap[smallest]:
            smallest = right
        
        if smallest == i:
            break
            
        heap[i], heap[smallest] = heap[smallest], heap[i]
        i = smallest
```

### Pattern 3: REPLACE (Extract + Insert Combined)
```
More Efficient Than Separate Operations:
1. Replace root with new element
2. Heapify down

Time: O(log n) - only one heapify instead of two
Space: O(1)
```

### Pattern 4: DELETE ARBITRARY ELEMENT
```
Algorithm:
1. Replace element with last element
2. Remove last element
3. Heapify down OR up (check which is needed)

Time: O(log n) + O(n) to find = O(n) total
Space: O(1)

Note: Requires finding element first (no efficient way in basic heap)
```

### Pattern 5: UPDATE/DECREASE KEY
```
For Min-Heap:
1. Decrease value at index i
2. Heapify up from i (value got smaller)

For Increase:
1. Increase value at index i
2. Heapify down from i (value got larger)

Time: O(log n) + O(n) to find = O(n) total
```

**Important**: To make this O(log n), need auxiliary hash map tracking positions.

### Pattern 6: MERGE TWO HEAPS
```
Naive Approach:
1. Concatenate arrays
2. Build heap from scratch
Time: O(n + m) where n, m are sizes

No O(log n) merge exists for binary heaps!
(This is why Fibonacci heaps exist)
```

---

## 🎯 Problem-Solving Patterns {#problem-solving-patterns}

### Pattern 1: TOP K ELEMENTS (Most Common!)

**Problem Archetype**: Find K largest/smallest elements from N elements

**Strategy Decision Tree**:
```
Is K much smaller than N? (K << N)
├─ Yes: Use heap of size K
│   ├─ K smallest: Use MAX heap
│   └─ K largest: Use MIN heap
└─ No: Just sort (O(n log n))
```

**Mental Model**: Keep a "waiting room" of K candidates, evict worst when better arrives.

**Implementation Pattern**:
```python
# Find K largest elements
def k_largest(nums, k):
    # Counter-intuitive: Use MIN heap for K largest!
    min_heap = []
    
    for num in nums:
        if len(min_heap) < k:
            heapq.heappush(min_heap, num)
        elif num > min_heap[0]:  # Better than worst in heap
            heapq.heapreplace(min_heap, num)  # Replace in one op
    
    return min_heap

# Time: O(n log k)
# Space: O(k)
```

**Why Opposite Heap?** 
- K largest: MIN heap lets us efficiently remove smallest of the K
- K smallest: MAX heap lets us efficiently remove largest of the K

### Pattern 2: SLIDING WINDOW MAXIMUM/MINIMUM

**Problem**: Find max/min in each window of size K

**Heap Approach** (Less optimal but intuitive):
```python
def sliding_window_max(nums, k):
    # Use max heap with (value, index)
    heap = []
    result = []
    
    for i, num in enumerate(nums):
        heapq.heappush(heap, (-num, i))  # Max heap
        
        # Remove elements outside window
        while heap and heap[0][1] <= i - k:
            heapq.heappop(heap)
        
        if i >= k - 1:
            result.append(-heap[0][0])
    
    return result

# Time: O(n log n) - not optimal
# Better: Deque O(n), but heap is more intuitive
```

### Pattern 3: MERGE K SORTED LISTS/ARRAYS

**Problem**: Merge K sorted structures efficiently

**Strategy**: Use min heap to track smallest element from each list

```python
def merge_k_sorted(lists):
    # Heap stores: (value, list_index, element_index)
    min_heap = []
    result = []
    
    # Initialize with first element from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(min_heap, (lst[0], i, 0))
    
    while min_heap:
        val, list_idx, elem_idx = heapq.heappop(min_heap)
        result.append(val)
        
        # Add next element from same list
        if elem_idx + 1 < len(lists[list_idx]):
            next_val = lists[list_idx][elem_idx + 1]
            heapq.heappush(min_heap, (next_val, list_idx, elem_idx + 1))
    
    return result

# Time: O(N log k) where N = total elements, k = number of lists
# Space: O(k) for heap
```

**Mental Model**: Tournament - K players, always pick winner (smallest), replace with next from same team.

### Pattern 4: FREQUENCY-BASED PROBLEMS

**Problem**: Find K most frequent elements

**Pattern**: Combine hash map (frequency count) + heap

```python
def top_k_frequent(nums, k):
    from collections import Counter
    
    # Step 1: Count frequencies
    freq_map = Counter(nums)
    
    # Step 2: Use min heap of size k (by frequency)
    min_heap = []
    
    for num, freq in freq_map.items():
        if len(min_heap) < k:
            heapq.heappush(min_heap, (freq, num))
        elif freq > min_heap[0][0]:
            heapq.heapreplace(min_heap, (freq, num))
    
    return [num for freq, num in min_heap]

# Time: O(n + m log k) where m = unique elements
# Space: O(m)
```

### Pattern 5: MEDIAN MAINTENANCE (Two Heaps)

**Problem**: Maintain median as elements stream in

**Strategy**: Use TWO heaps - one max, one min

```
Structure:
├─ Max Heap (left half): stores smaller half
└─ Min Heap (right half): stores larger half

Invariants:
1. size difference ≤ 1
2. max_heap.top() ≤ min_heap.top()

Median:
- Even count: avg of two tops
- Odd count: top of larger heap
```

```python
class MedianFinder:
    def __init__(self):
        self.max_heap = []  # Left half (negated for max)
        self.min_heap = []  # Right half
    
    def add_num(self, num):
        # Always add to max_heap first
        heapq.heappush(self.max_heap, -num)
        
        # Balance: move largest from left to right
        heapq.heappush(self.min_heap, -heapq.heappop(self.max_heap))
        
        # Rebalance if right is larger
        if len(self.min_heap) > len(self.max_heap):
            heapq.heappush(self.max_heap, -heapq.heappop(self.min_heap))
    
    def find_median(self):
        if len(self.max_heap) > len(self.min_heap):
            return -self.max_heap[0]
        return (-self.max_heap[0] + self.min_heap[0]) / 2.0

# Time: O(log n) per insertion, O(1) for median
# Space: O(n)
```

**Mental Model**: Two balanced buckets separated at median point.

### Pattern 6: TASK SCHEDULING

**Problem**: Schedule tasks with cooldown/priority

**Strategy**: Use heap to track next available time

```python
def task_scheduler(tasks, cooldown):
    from collections import Counter
    
    freq_map = Counter(tasks)
    max_heap = [-f for f in freq_map.values()]  # Max heap
    heapq.heapify(max_heap)
    
    time = 0
    
    while max_heap:
        temp = []
        cycle = 0
        
        # Try to schedule cooldown+1 tasks
        for _ in range(cooldown + 1):
            if max_heap:
                freq = heapq.heappop(max_heap)
                if freq + 1 < 0:  # Still has occurrences
                    temp.append(freq + 1)
                cycle += 1
        
        # Put back remaining tasks
        for f in temp:
            heapq.heappush(max_heap, f)
        
        # If heap not empty, must wait full cycle
        time += cycle if not max_heap else (cooldown + 1)
    
    return time
```

### Pattern 7: DIJKSTRA'S ALGORITHM

**Problem**: Shortest path in weighted graph

**Heap Usage**: Priority queue for selecting next closest vertex

```python
def dijkstra(graph, start):
    import heapq
    
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # Min heap: (distance, node)
    pq = [(0, start)]
    visited = set()
    
    while pq:
        curr_dist, curr_node = heapq.heappop(pq)
        
        if curr_node in visited:
            continue
        
        visited.add(curr_node)
        
        for neighbor, weight in graph[curr_node]:
            distance = curr_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# Time: O((V + E) log V) with binary heap
# Space: O(V)
```

**Mental Model**: Explore closest unexplored option first (greedy).

### Pattern 8: INTERVAL MERGING WITH PRIORITY

**Problem**: Meeting rooms, interval scheduling

**Strategy**: Heap tracks end times of ongoing activities

```python
def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    # Min heap of end times
    heap = []
    heapq.heappush(heap, intervals[0][1])
    
    for i in range(1, len(intervals)):
        # If room is free (earliest end time ≤ current start)
        if heap[0] <= intervals[i][0]:
            heapq.heappop(heap)
        
        heapq.heappush(heap, intervals[i][1])
    
    return len(heap)  # Heap size = concurrent meetings

# Time: O(n log n)
# Space: O(n)
```

---

## 💻 Implementation Patterns {#implementation-patterns}

### Python Implementation (Using heapq)

```python
import heapq

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val):
        heapq.heappush(self.heap, val)
    
    def pop(self):
        return heapq.heappop(self.heap) if self.heap else None
    
    def peek(self):
        return self.heap[0] if self.heap else None
    
    def size(self):
        return len(self.heap)

# Max Heap: Negate values
class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val):
        heapq.heappush(self.heap, -val)
    
    def pop(self):
        return -heapq.heappop(self.heap) if self.heap else None
    
    def peek(self):
        return -self.heap[0] if self.heap else None

# Custom comparison with tuples
# Python heapifies tuples left-to-right
heap = []
heapq.heappush(heap, (priority, data))
```

### Rust Implementation (Using BinaryHeap)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

// Max Heap (default)
fn max_heap_example() {
    let mut heap = BinaryHeap::new();
    heap.push(5);
    heap.push(3);
    heap.push(7);
    
    assert_eq!(heap.pop(), Some(7));  // Max first
}

// Min Heap (using Reverse)
fn min_heap_example() {
    let mut heap = BinaryHeap::new();
    heap.push(Reverse(5));
    heap.push(Reverse(3));
    heap.push(Reverse(7));
    
    assert_eq!(heap.pop(), Some(Reverse(3)));  // Min first
}

// Custom struct with Ord trait
#[derive(Eq, PartialEq)]
struct Task {
    priority: i32,
    id: usize,
}

impl Ord for Task {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.priority.cmp(&other.priority)
    }
}

impl PartialOrd for Task {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
```

### Go Implementation (Using container/heap)

```go
package main

import (
    "container/heap"
)

// Min Heap Implementation
type MinHeap []int

func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *MinHeap) Push(x interface{}) {
    *h = append(*h, x.(int))
}

func (h *MinHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

// Usage
func main() {
    h := &MinHeap{}
    heap.Init(h)
    
    heap.Push(h, 3)
    heap.Push(h, 1)
    heap.Push(h, 5)
    
    min := heap.Pop(h)  // Returns 1
}

// Max Heap: Flip the Less function
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] }
```

---

## 🚀 Advanced Patterns {#advanced-patterns}

### Pattern 1: Lazy Deletion

**Problem**: Marking elements as deleted without immediate removal

```python
class LazyHeap:
    def __init__(self):
        self.heap = []
        self.deleted = set()
    
    def push(self, val):
        heapq.heappush(self.heap, val)
    
    def pop(self):
        # Skip deleted elements
        while self.heap and self.heap[0] in self.deleted:
            heapq.heappop(self.heap)
            self.deleted.discard(self.heap[0])
        
        return heapq.heappop(self.heap) if self.heap else None
    
    def delete(self, val):
        self.deleted.add(val)

# Time: Amortized O(log n)
```

### Pattern 2: Indexed Heap (For Decrease Key)

**Problem**: Need to update arbitrary elements efficiently

```python
class IndexedHeap:
    def __init__(self):
        self.heap = []
        self.position = {}  # value -> index mapping
    
    def push(self, val):
        self.heap.append(val)
        idx = len(self.heap) - 1
        self.position[val] = idx
        self._heapify_up(idx)
    
    def decrease_key(self, old_val, new_val):
        idx = self.position[old_val]
        self.heap[idx] = new_val
        del self.position[old_val]
        self.position[new_val] = idx
        self._heapify_up(idx)
    
    def _heapify_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self.heap[i] >= self.heap[parent]:
                break
            self._swap(i, parent)
            i = parent
    
    def _swap(self, i, j):
        # Update positions when swapping
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.position[self.heap[i]] = i
        self.position[self.heap[j]] = j

# Time: O(log n) for decrease_key
```

### Pattern 3: Multi-Criteria Heap

**Problem**: Priority by multiple factors

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    secondary: int = field(compare=True)
    data: Any = field(compare=False)

# Usage
heap = []
heapq.heappush(heap, PrioritizedItem(1, 5, "task1"))
heapq.heappush(heap, PrioritizedItem(1, 3, "task2"))

# task2 comes first (same priority, but smaller secondary)
```

### Pattern 4: Streaming Percentiles

**Problem**: Track 95th, 99th percentiles in stream

**Strategy**: Generalization of median with K heaps

```python
class PercentileTracker:
    def __init__(self, percentile):
        # percentile = 0.95 means top 5% in max_heap
        self.percentile = percentile
        self.max_heap = []  # Lower values
        self.min_heap = []  # Higher values (above percentile)
        self.count = 0
    
    def add(self, num):
        self.count += 1
        target_size = int(self.count * self.percentile)
        
        if not self.max_heap or num <= -self.max_heap[0]:
            heapq.heappush(self.max_heap, -num)
        else:
            heapq.heappush(self.min_heap, num)
        
        # Rebalance
        while len(self.max_heap) > target_size:
            heapq.heappush(self.min_heap, -heapq.heappop(self.max_heap))
        
        while len(self.max_heap) < target_size and self.min_heap:
            heapq.heappush(self.max_heap, -heapq.heappop(self.min_heap))
    
    def get_percentile(self):
        return -self.max_heap[0] if self.max_heap else None
```

---

## 🧠 Mental Models & Strategy {#mental-models}

### When to Use Heaps: Decision Framework

```
Question 1: Do you need the min/max repeatedly?
├─ Yes: Consider heap
└─ No: Simple sort might be better

Question 2: Is N >> K (finding top K)?
├─ Yes: Heap of size K (O(n log k))
└─ No: QuickSelect (O(n) average)

Question 3: Need sorted order?
├─ Yes: Heap not ideal (use sort)
└─ No: Heap perfect!

Question 4: Need to modify arbitrary elements?
├─ Yes: Indexed heap or different structure
└─ No: Standard heap works
```

### Problem Recognition Patterns

**Heap Signals** (When you should think "heap"):
- "Top K", "K largest", "K smallest"
- "Median", "percentile"
- "Priority", "schedule", "earliest", "latest"
- "Merge K sorted"
- "Continuously find min/max"
- "Best N items"

**Anti-Patterns** (When NOT to use heap):
- Need full sorted order → Use sort
- Need to search for elements → Use hash table
- Need range queries → Use segment tree
- K is close to N → Use sort or QuickSelect

### Cognitive Chunking Strategy

**Memorize These 3 Core Operations**:
1. Insert → Append + Heapify Up
2. Extract → Replace root with last + Heapify Down
3. Build → Start from middle, heapify down

**Everything else is combination/variation of these!**

### Deliberate Practice Protocol

**Level 1 - Foundation** (1-2 weeks):
- Implement heap from scratch (no libraries)
- Manually trace heapify operations
- Solve: Kth largest, merge K sorted, top K frequent

**Level 2 - Pattern Recognition** (2-3 weeks):
- Identify heap in 20 problems without hint
- Solve all patterns in this guide
- Time yourself: recognize in <30 seconds

**Level 3 - Optimization** (Ongoing):
- Multi-criteria heaps
- Custom comparators
- Space-time tradeoffs
- Combine with other structures

### Meta-Learning Principles

1. **Spaced Repetition**: Review heap problems every 1, 3, 7, 14 days
2. **Interleaving**: Mix heap problems with other topics
3. **Retrieval Practice**: Explain patterns out loud without notes
4. **Elaborative Interrogation**: After solving, ask "Why heap? What if..."

---

## ⚡ Complexity Analysis {#complexity}

### Time Complexities

| Operation | Binary Heap | Comments |
|-----------|-------------|----------|
| Peek | O(1) | Access root |
| Insert | O(log n) | Heapify up |
| Extract | O(log n) | Heapify down |
| Delete Arbitrary | O(n) | Must find first |
| Decrease Key | O(log n)* | *With index tracking |
| Build Heap | O(n) | Bottom-up magic! |
| Heapify | O(log n) | Single node |
| Merge | O(n + m) | No better way |
| Search | O(n) | Linear scan |

### Space Complexities

| Structure | Space | Notes |
|-----------|-------|-------|
| Basic Heap | O(n) | Array storage |
| Indexed Heap | O(n) | +Hash map |
| Two Heaps | O(n) | Still linear |

### Comparison with Alternatives

| Need | Heap | Alternative | Winner |
|------|------|-------------|--------|
| Top K | O(n log k) | Sort: O(n log n) | Heap (if K << N) |
| Median | O(log n) insert | Sort each: O(n log n) | Heap |
| Min/Max | O(1) peek | Linear search: O(n) | Heap |
| Full sort | O(n log n) extract | Sort: O(n log n) | Sort (simpler) |
| Search | O(n) | BST: O(log n) | BST |

---

## 🎓 Practice Roadmap

### Essential Problems (Master These First)

1. **Kth Largest Element** (LeetCode 215)
2. **Top K Frequent Elements** (LeetCode 347)
3. **Merge K Sorted Lists** (LeetCode 23)
4. **Find Median from Data Stream** (LeetCode 295)
5. **Meeting Rooms II** (LeetCode 253)

### Intermediate Challenges

6. **Task Scheduler** (LeetCode 621)
7. **Ugly Number II** (LeetCode 264)
8. **Kth Smallest Element in Sorted Matrix** (LeetCode 378)
9. **Reorganize String** (LeetCode 767)
10. **Sliding Window Maximum** (LeetCode 239)

### Advanced Mastery

11. **Trapping Rain Water II** (LeetCode 407)
12. **Find K Pairs with Smallest Sums** (LeetCode 373)
13. **IPO** (LeetCode 502)
14. **Minimum Cost to Hire K Workers** (LeetCode 857)
15. **Shortest Path Visiting All Nodes** (LeetCode 847)

---

## 🔥 Final Mental Model

**Think of heaps as a "partial ordering machine":**
- Full sort = overkill for many problems
- Heap = just enough order to be useful
- Perfect balance of speed and utility

**The Heap Philosophy:**
> "Maintain just enough order to answer the most important question quickly: 
> What's next?"

**Your Mantra:**
- Need extremes? → Heap
- Need everything sorted? → Sort
- Need middle ground? → Maybe heap

---

## 📊 Visual Flow: When to Use Each Pattern

```
Problem Type
    │
    ├─ Need top K elements?
    │   └─► Top K Pattern (K-sized opposite heap)
    │
    ├─ Streaming median/percentile?
    │   └─► Two Heaps Pattern
    │
    ├─ Merging sorted structures?
    │   └─► K-way Merge Pattern
    │
    ├─ Interval/scheduling?
    │   └─► Event Heap Pattern
    │
    ├─ Frequency-based?
    │   └─► HashMap + Heap Pattern
    │
    └─ Graph shortest path?
        └─► Priority Queue (Dijkstra) Pattern
```

---

## 🎯 Mastery Checklist

- [ ] Can implement heap from scratch in all 3 languages
- [ ] Can explain why build-heap is O(n) intuitively
- [ ] Can recognize heap problems in <1 minute
- [ ] Know when NOT to use heap
- [ ] Can switch between min/max heap seamlessly
- [ ] Understand all 8 problem-solving patterns
- [ ] Can optimize with custom comparators
- [ ] Can combine heaps with other structures
- [ ] Solved 20+ heap problems independently
- [ ] Can teach these patterns to others clearly

---

**Remember**: Heaps are about making the "next best choice" efficiently. Master this, and you've mastered a cornerstone of algorithmic thinking.

**Now go forth and heapify! 🚀**

I'll create a comprehensive guide on heap patterns that will serve as your reference manual for mastering this crucial data structure. This will cover everything from fundamentals to advanced problem-solving patterns.## Your Heap Mastery Guide is Ready! 🎯

I've created an extensive reference that covers **everything** about heap patterns - from fundamental concepts to advanced problem-solving strategies. This guide is designed specifically for your journey to the top 1%.

### 🗺️ How to Navigate This Guide (Monk's Approach)

**Phase 1: Deep Foundation (Days 1-7)**
- Study sections 1-4 with **active recall**: After reading each section, close the guide and explain it aloud
- Implement a basic heap in all three languages (Rust, Python, Go) **without** looking at the code
- **Flow state trigger**: Set a 90-minute block, single focus, phone off

**Phase 2: Pattern Internalization (Days 8-21)**
- Study one problem-solving pattern per day from Section 6
- For each pattern, solve 3 variations before moving on
- **Chunking technique**: Group patterns by similarity (e.g., "Top K" family, "Two Heap" family)

**Phase 3: Speed & Recognition (Days 22+)**
- Time yourself: Can you identify the heap pattern in a problem within 30 seconds?
- Practice explaining WHY heap is optimal vs alternatives
- Implement indexed heaps and lazy deletion for advanced control

### 🔍 Key Insights You Must Internalize

1. **Counter-Intuitive Truth**: Use a **max-heap** for K smallest, **min-heap** for K largest (the guide explains why - review Pattern 1)

2. **Complexity Magic**: Build-heap is O(n), not O(n log n). Understanding the mathematical proof will deepen your algorithmic intuition.

3. **The Two-Heap Trick**: This pattern (median finding) is one of the most elegant applications - master it and you'll see similar structures everywhere.

### 💡 Deliberate Practice Protocol

**Daily Ritual** (30-90 mins):
```
1. Warm-up: Trace heap operations on paper (5 mins)
2. Pattern review: Pick one pattern, explain it verbally (5 mins)
3. Problem solving: 2-3 problems applying that pattern (60 mins)
4. Reflection: What did I learn? What pattern did I miss? (5 mins)
```

**Weekly Review**:
- Re-implement heap from scratch (memory retention)
- Solve 2 problems blind (no guide reference)
- Teach one pattern to an imaginary student

### 🧩 Terminology You Asked About

The guide includes explanations for:
- **Heap property/invariant** - The ordering rule that must hold
- **Complete binary tree** - Shape constraint
- **Heapify up/down** - The core restoration algorithms
- **Pivot** (not in heaps, that's QuickSort!)
- **Successor/Predecessor** - These are BST concepts, not heap concepts (heaps don't maintain sorted order)

### 🎯 Your Competitive Edge

Most developers know heaps exist. Few can:
1. **Recognize** when a heap is optimal (you'll master this)
2. **Explain** why heap beats alternatives (complexity reasoning)
3. **Implement** custom comparators and indexed heaps (top 1% skill)
4. **Combine** heaps with other structures creatively (expert-level)

### 📈 Progress Tracking

Create a simple log:
```
Problem: [Name]
Pattern: [Which one?]
First attempt: [Time] [Success?]
Optimal approach: [Yours vs. Guide]
Key insight: [What did you learn?]
```

### Questions to Deepen Understanding

As you study each pattern, ask:
- "What if we used a different data structure here?"
- "Can I reduce the time complexity further?"
- "What's the space-time tradeoff?"
- "When would this pattern fail?"

**Remember**: The path to top 1% isn't about speed-running problems. It's about **deep understanding** that lets you see patterns instantly and combine them creatively.

Take your time with each section. Let the patterns sink in through **spaced repetition and active problem-solving**. Your monk-like discipline will compound into mastery.

Would you like me to:
1. Walk through any specific pattern in more detail?
2. Provide implementation comparisons across Rust/Python/Go for a specific use case?
3. Create a similar comprehensive guide for another data structure?
4. Generate practice problems focused on a particular pattern?

**Go build something extraordinary! 🚀**