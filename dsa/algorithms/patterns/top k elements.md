# Top K Elements Pattern - Complete Mastery Guide

## Table of Contents
1. [Core Intuition & Philosophy](#core-intuition)
2. [Pattern Recognition](#pattern-recognition)
3. [Foundational Concepts](#foundational-concepts)
4. [The Mental Model](#mental-model)
5. [Approaches: From Naive to Optimal](#approaches)
6. [Implementation Deep Dive](#implementations)
7. [Variations & Advanced Applications](#variations)
8. [Problem-Solving Framework](#framework)
9. [Practice Roadmap](#practice)

---

## 1. Core Intuition & Philosophy {#core-intuition}

### What is the Top K Elements Pattern?

The **Top K Elements** pattern addresses a fundamental question in computer science:

> **"Given a collection of N elements, how do we efficiently identify the K most significant items according to some criterion?"**

**Significance** could mean:
- Largest/smallest values
- Most/least frequent elements  
- Closest to a target
- Most recent
- Highest priority

### Why This Pattern Matters

This pattern is ubiquitous in real-world systems:
- **Search engines**: Top 10 most relevant results
- **Social media**: Top K trending topics
- **Recommendations**: K most similar items
- **System monitoring**: K heaviest processes
- **Finance**: K largest transactions

### The Cognitive Leap

The naive mind thinks: *"Sort everything, then take K items."* — **O(N log N)**

The trained mind recognizes: *"I only need K items, not total order."* — **O(N log K)** or **O(N)**

This shift from "complete information" to "sufficient information" is a hallmark of algorithmic maturity.

---

## 2. Pattern Recognition {#pattern-recognition}

### Decision Tree: Should I Use This Pattern?

```
                     START: Problem Analysis
                              |
                              v
                    ┌─────────────────────┐
                    │ Need K items from N? │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                   YES                   NO → Different Pattern
                    │
                    v
         ┌──────────────────────┐
         │ K << N (K much < N)? │
         └──────────┬────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
        YES                   NO
         │                     │
         v                     v
    TOP K PATTERN         Consider Full Sort
    (Heap/QuickSelect)    (might be simpler)
```

### Keyword Recognition Checklist

Look for these phrases in problem statements:
- ✓ "Find the **K largest/smallest** elements"
- ✓ "**K most frequent** items"
- ✓ "**Top K** closest points"
- ✓ "**K highest** priority tasks"
- ✓ "First **K** elements that satisfy..."
- ✓ "Return any **K** elements..." (when order doesn't matter)

**Red flags** (NOT Top K pattern):
- "Find **all** elements greater than X" → Filtering
- "**Kth** largest element" → Quickselect variant
- "**Median** of elements" → Special case (K = N/2)

---

## 3. Foundational Concepts {#foundational-concepts}

Before diving deep, let's establish the building blocks.

### Heap (Priority Queue)

**Definition**: A heap is a specialized tree-based data structure that satisfies the **heap property**:
- **Max-Heap**: Parent ≥ All children (root = maximum)
- **Min-Heap**: Parent ≤ All children (root = minimum)

**Visual Structure**:
```
        Max-Heap                Min-Heap
           100                      1
          /   \                   /   \
        90     80                3     5
       /  \   /  \              / \   / \
      70  60 50  40            8  10 12 15

Array: [100,90,80,70,60,50,40]   [1,3,5,8,10,12,15]
```

**Key Operations**:
| Operation | Time Complexity | Purpose |
|-----------|----------------|---------|
| Insert | O(log N) | Add element, maintain heap property |
| Extract Min/Max | O(log N) | Remove root, reorganize |
| Peek | O(1) | View root without removing |
| Heapify | O(N) | Convert array to heap |

**Why Heaps for Top K?**

Heaps provide the "sweet spot":
- Maintain K elements efficiently
- Always know the current "threshold" (root)
- Logarithmic operations (not linear)

### Comparative Analysis vs Other Structures

```
Data Structure     | Find Max | Insert | Space | Top K Suitability
-------------------|----------|--------|-------|-------------------
Unsorted Array     | O(N)     | O(1)   | O(N)  | ❌ Poor (linear scan)
Sorted Array       | O(1)     | O(N)   | O(N)  | ⚠️ Expensive inserts
Binary Search Tree | O(log N) | O(log N)| O(N) | ⚠️ Need balancing
Heap               | O(1)     | O(log N)| O(K) | ✅ OPTIMAL
```

### Frequency/Count Analysis

**Concept**: When dealing with "most frequent," we need to:
1. **Count occurrences** → Use HashMap/Dictionary
2. **Rank by frequency** → Use Heap on counts

**Example Transformation**:
```
Input:  [1, 1, 1, 2, 2, 3]
             ↓ COUNT PHASE
HashMap: {1: 3, 2: 2, 3: 1}
             ↓ HEAP PHASE
Min-Heap(K=2): [(2, 2), (3, 1)]  [frequency, element]
             ↓ RESULT
Top 2 Frequent: [1, 2]
```

---

## 4. The Mental Model {#mental-model}

### The "Gatekeeper Metaphor"

Think of the heap as a **gatekeeper** at an exclusive club:

```
┌─────────────────────────────────────┐
│  EXCLUSIVE CLUB (Size = K)          │
│  Current members: [90, 85, 80]      │
│  Min-member: 80 ← GATEKEEPER        │
└──────────────┬──────────────────────┘
               │
               v
         New Candidate: 95
               │
        ┌──────┴──────┐
        │ 95 > 80 ?   │  ← Comparison
        └──────┬──────┘
               │ YES
               v
        Kick out 80, Add 95
        New Club: [90, 85, 95]
        New Gatekeeper: 85
```

### The Two-Phase Strategy

**Phase 1: Establish the K-baseline**
- Build initial heap with first K elements
- Time: O(K) or O(K log K)

**Phase 2: Challenge the baseline**
- For each remaining element (N-K items):
  - Compare with root (gatekeeper)
  - Replace if better
- Time: O((N-K) log K)

**Total**: O(N log K)

### Cognitive Chunking Strategy

When solving Top K problems, chunk your thinking:

1. **IDENTIFY**: What makes an element "top"? (value, frequency, distance?)
2. **DIRECTION**: Do I need max-heap or min-heap?
   - For "K largest" → Use **min-heap** (keep smallest of the large)
   - For "K smallest" → Use **max-heap** (keep largest of the small)
3. **OPTIMIZE**: Can I avoid heap? (Quick Select for unsorted K)
4. **EXTEND**: Do I need sorted output? (Extra sort step)

---

## 5. Approaches: From Naive to Optimal {#approaches}

### Approach 1: Brute Force (Sort Everything)

**Intuition**: "If I sort all elements, the answer is obvious."

```
Algorithm:
1. Sort entire array
2. Take first/last K elements

Time:  O(N log N)  ← Sorting dominates
Space: O(1) or O(N) depending on sort algorithm
```

**When to use**:
- K is very close to N (e.g., K = N-5)
- You need sorted output anyway
- N is small (<1000 elements)

**Visualization**:
```
Input:  [3, 1, 5, 12, 2, 11]  (Find K=3 largest)
           ↓ SORT
        [1, 2, 3, 5, 11, 12]
                      └──┬──┘
                    Take last 3
Result: [12, 11, 5]
```

### Approach 2: Heap (Priority Queue)

**Intuition**: "I only care about K elements, not full order."

```
Algorithm (K largest):
1. Create min-heap of size K
2. For first K elements: Insert into heap
3. For remaining elements:
   - If element > heap.min:
     - Remove heap.min
     - Insert element
4. Return heap contents

Time:  O(K + (N-K)log K) = O(N log K)
Space: O(K)
```

**Heap Size Decision Matrix**:
```
Goal          | Heap Type | Heap Size | Root Meaning
--------------|-----------|-----------|------------------
K Largest     | Min-Heap  | K         | Smallest of large
K Smallest    | Max-Heap  | K         | Largest of small
K Most Freq   | Min-Heap  | K         | Least freq of top
K Closest     | Max-Heap  | K         | Farthest of close
```

**Flow Visualization**:
```
Find 3 largest from [3, 1, 5, 12, 2, 11]

Step 1: Build heap with first 3
Heap: [1, 3, 5]  (min-heap)
      Root = 1

Step 2: Process 12
12 > 1? YES → Pop 1, Push 12
Heap: [3, 5, 12]
      Root = 3

Step 3: Process 2
2 > 3? NO → Skip
Heap: [3, 5, 12]

Step 4: Process 11
11 > 3? YES → Pop 3, Push 11
Heap: [5, 12, 11]
      Root = 5

Result: [5, 11, 12]
```

### Approach 3: QuickSelect (For Kth Element)

**Intuition**: "Partition around pivot, recurse only on relevant half."

**Note**: QuickSelect finds the **Kth** element, not K elements. But it can be adapted.

```
Algorithm:
1. Choose pivot
2. Partition array around pivot
3. If pivot is at position K-1: DONE
4. If pivot > K-1: Recurse left
5. If pivot < K-1: Recurse right

Time:  O(N) average, O(N²) worst
Space: O(1)
```

**Partition Visualization**:
```
Array: [3, 1, 5, 12, 2, 11]  Find 3rd largest (K=3, index=2)
Pivot: 5

Partition: [3, 1, 2] | 5 | [12, 11]
            Smaller     P    Larger

Pivot at index 3, need index 5-3=2 from the end
→ Recurse on right: [12, 11]
```

### Approach 4: Bucket Sort (For Frequency Problems)

**Intuition**: "Group by frequency, traverse from high to low."

```
Algorithm (K most frequent):
1. Count frequencies → HashMap
2. Create buckets[0...N] where bucket[i] = elements with freq i
3. Traverse buckets from N to 0
4. Collect K elements

Time:  O(N)
Space: O(N)
```

**Bucket Visualization**:
```
Input: [1,1,1,2,2,3] → Find K=2 most frequent

Count: {1:3, 2:2, 3:1}

Buckets:
freq 3: [1]           ← Start here
freq 2: [2]           ← Then here
freq 1: [3]
freq 0: []

Collect 2 elements: [1, 2]
```

---

## 6. Implementation Deep Dive {#implementations}

### Problem: K Largest Elements

#### Python Implementation (Heapq - Min-Heap)

```python
import heapq
from typing import List

def k_largest_elements(nums: List[int], k: int) -> List[int]:
    """
    Time: O(N log K) where N = len(nums)
    Space: O(K) for the heap
    
    Mental Model: Min-heap keeps smallest of the K largest.
    Root is the "gatekeeper" - weakest member of top K club.
    """
    
    # Edge case: if k >= n, return all
    if k >= len(nums):
        return nums
    
    # Build initial heap with first k elements
    # heapq is a min-heap by default
    heap = nums[:k]
    heapq.heapify(heap)  # O(k) operation
    
    # Process remaining elements
    for num in nums[k:]:
        # If current element is larger than smallest in heap
        if num > heap[0]:  # heap[0] is the root (minimum)
            heapq.heapreplace(heap, num)  # Pop min, push num (O(log k))
            # Alternative: heapq.heappushpop(heap, num)
    
    # Return heap contents (unordered)
    # If you need sorted: return sorted(heap, reverse=True)
    return heap


# Example usage with detailed trace
def demo_trace():
    nums = [3, 1, 5, 12, 2, 11]
    k = 3
    
    print(f"Finding {k} largest from {nums}\n")
    
    heap = nums[:k]
    heapq.heapify(heap)
    print(f"Initial heap: {heap} (root={heap[0]})")
    
    for num in nums[k:]:
        print(f"\nProcessing {num}:")
        if num > heap[0]:
            old_min = heap[0]
            heapq.heapreplace(heap, num)
            print(f"  {num} > {old_min} → Replace")
            print(f"  New heap: {heap} (root={heap[0]})")
        else:
            print(f"  {num} ≤ {heap[0]} → Skip")
    
    print(f"\nFinal K largest: {sorted(heap, reverse=True)}")

# Optimization: For large N, small K
def k_largest_optimized(nums: List[int], k: int) -> List[int]:
    """
    Using heapq.nlargest - internally uses same algorithm
    but optimized at C level
    """
    return heapq.nlargest(k, nums)
```

#### Rust Implementation (BinaryHeap - Max-Heap)

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

/// Find K largest elements using a min-heap
/// Time: O(N log K), Space: O(K)
fn k_largest_elements(nums: Vec<i32>, k: usize) -> Vec<i32> {
    // Edge case
    if k >= nums.len() {
        return nums;
    }
    
    // Rust's BinaryHeap is a max-heap by default
    // We need a min-heap, so we wrap elements in Reverse
    let mut heap: BinaryHeap<Reverse<i32>> = BinaryHeap::with_capacity(k);
    
    // Build initial heap with first k elements
    for &num in nums.iter().take(k) {
        heap.push(Reverse(num));
    }
    
    // Process remaining elements
    for &num in nums.iter().skip(k) {
        // Access the minimum (root of min-heap)
        if let Some(&Reverse(min)) = heap.peek() {
            if num > min {
                heap.pop(); // Remove minimum
                heap.push(Reverse(num)); // Add new element
            }
        }
    }
    
    // Extract results (unwrap Reverse wrapper)
    heap.into_iter().map(|Reverse(x)| x).collect()
}

// Alternative: Using direct max-heap for K smallest
fn k_smallest_elements(nums: Vec<i32>, k: usize) -> Vec<i32> {
    let mut heap: BinaryHeap<i32> = BinaryHeap::with_capacity(k);
    
    for &num in nums.iter().take(k) {
        heap.push(num);
    }
    
    for &num in nums.iter().skip(k) {
        if num < *heap.peek().unwrap() {
            heap.pop();
            heap.push(num);
        }
    }
    
    heap.into_iter().collect()
}

// Demonstration with detailed logging
fn demo_trace() {
    let nums = vec![3, 1, 5, 12, 2, 11];
    let k = 3;
    
    println!("Finding {} largest from {:?}\n", k, nums);
    
    let mut heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    
    for &num in nums.iter().take(k) {
        heap.push(Reverse(num));
    }
    println!("Initial heap (min-heap): {:?}", heap);
    
    for &num in nums.iter().skip(k) {
        let min = heap.peek().unwrap().0;
        print!("\nProcessing {}: ", num);
        
        if num > min {
            heap.pop();
            heap.push(Reverse(num));
            println!("{} > {} → Replace", num, min);
            println!("  New heap: {:?}", heap);
        } else {
            println!("{} ≤ {} → Skip", num, min);
        }
    }
    
    let result: Vec<i32> = heap.into_iter().map(|Reverse(x)| x).collect();
    println!("\nFinal K largest: {:?}", result);
}
```

#### Go Implementation (container/heap)

```go
package main

import (
    "container/heap"
    "fmt"
)

// MinHeap implements heap.Interface for a min-heap of integers
type MinHeap []int

func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] } // Min-heap
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

// KLargestElements finds K largest elements using a min-heap
// Time: O(N log K), Space: O(K)
func KLargestElements(nums []int, k int) []int {
    // Edge case
    if k >= len(nums) {
        return nums
    }
    
    // Initialize min-heap with first k elements
    h := &MinHeap{}
    heap.Init(h)
    
    for i := 0; i < k; i++ {
        heap.Push(h, nums[i])
    }
    
    // Process remaining elements
    for i := k; i < len(nums); i++ {
        // If current element is larger than heap minimum
        if nums[i] > (*h)[0] {
            heap.Pop(h)        // Remove minimum
            heap.Push(h, nums[i]) // Add new element
        }
    }
    
    // Convert heap to slice
    result := make([]int, h.Len())
    for i := 0; i < len(result); i++ {
        result[i] = (*h)[i]
    }
    
    return result
}

// MaxHeap for K smallest elements
type MaxHeap []int

func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] } // Max-heap
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *MaxHeap) Push(x interface{}) {
    *h = append(*h, x.(int))
}

func (h *MaxHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func KSmallestElements(nums []int, k int) []int {
    h := &MaxHeap{}
    heap.Init(h)
    
    for i := 0; i < k && i < len(nums); i++ {
        heap.Push(h, nums[i])
    }
    
    for i := k; i < len(nums); i++ {
        if nums[i] < (*h)[0] {
            heap.Pop(h)
            heap.Push(h, nums[i])
        }
    }
    
    result := make([]int, h.Len())
    for i := 0; i < len(result); i++ {
        result[i] = (*h)[i]
    }
    
    return result
}

// Demonstration with trace
func demoTrace() {
    nums := []int{3, 1, 5, 12, 2, 11}
    k := 3
    
    fmt.Printf("Finding %d largest from %v\n\n", k, nums)
    
    h := &MinHeap{}
    heap.Init(h)
    
    for i := 0; i < k; i++ {
        heap.Push(h, nums[i])
    }
    fmt.Printf("Initial heap: %v (min=%d)\n", *h, (*h)[0])
    
    for i := k; i < len(nums); i++ {
        num := nums[i]
        min := (*h)[0]
        fmt.Printf("\nProcessing %d: ", num)
        
        if num > min {
            heap.Pop(h)
            heap.Push(h, num)
            fmt.Printf("%d > %d → Replace\n", num, min)
            fmt.Printf("  New heap: %v (min=%d)\n", *h, (*h)[0])
        } else {
            fmt.Printf("%d ≤ %d → Skip\n", num, min)
        }
    }
    
    fmt.Printf("\nFinal K largest: %v\n", *h)
}
```

---

## 7. Variations & Advanced Applications {#variations}

### Variation 1: K Most Frequent Elements

**Problem**: Given array, return K most frequent elements.

**Key Insight**: Two-step process:
1. Count frequencies (HashMap)
2. Find top K by frequency (Heap)

**Python Implementation**:
```python
from collections import Counter
import heapq

def top_k_frequent(nums: List[int], k: int) -> List[int]:
    """
    Time: O(N log K), Space: O(N)
    """
    # Step 1: Count frequencies
    freq_map = Counter(nums)  # O(N)
    
    # Step 2: Use min-heap of size K
    # Store tuples: (frequency, element)
    heap = []
    
    for num, freq in freq_map.items():
        heapq.heappush(heap, (freq, num))
        if len(heap) > k:
            heapq.heappop(heap)  # Remove least frequent
    
    # Extract elements (ignore frequencies)
    return [num for freq, num in heap]

# Optimized: Using bucket sort for O(N)
def top_k_frequent_optimal(nums: List[int], k: int) -> List[int]:
    """
    Time: O(N), Space: O(N)
    """
    freq_map = Counter(nums)
    
    # Create buckets: bucket[i] = list of elements with frequency i
    buckets = [[] for _ in range(len(nums) + 1)]
    
    for num, freq in freq_map.items():
        buckets[freq].append(num)
    
    # Collect K elements from high frequency to low
    result = []
    for freq in range(len(buckets) - 1, 0, -1):
        for num in buckets[freq]:
            result.append(num)
            if len(result) == k:
                return result
    
    return result
```

### Variation 2: K Closest Points to Origin

**Problem**: Find K points closest to (0,0).

**Key Insight**: Use max-heap of size K, store distances.

**Rust Implementation**:
```rust
use std::collections::BinaryHeap;
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy)]
struct Point {
    x: i32,
    y: i32,
    dist_sq: i32,  // Squared distance (avoid sqrt)
}

impl Point {
    fn new(x: i32, y: i32) -> Self {
        Point {
            x,
            y,
            dist_sq: x * x + y * y,
        }
    }
}

// Implement Ord for max-heap behavior
impl Ord for Point {
    fn cmp(&self, other: &Self) -> Ordering {
        self.dist_sq.cmp(&other.dist_sq)
    }
}

impl PartialOrd for Point {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Eq for Point {}
impl PartialEq for Point {
    fn eq(&self, other: &Self) -> bool {
        self.dist_sq == other.dist_sq
    }
}

fn k_closest_points(points: Vec<(i32, i32)>, k: usize) -> Vec<(i32, i32)> {
    let mut heap: BinaryHeap<Point> = BinaryHeap::with_capacity(k);
    
    for (x, y) in points {
        let point = Point::new(x, y);
        
        if heap.len() < k {
            heap.push(point);
        } else if point.dist_sq < heap.peek().unwrap().dist_sq {
            heap.pop();
            heap.push(point);
        }
    }
    
    heap.into_iter().map(|p| (p.x, p.y)).collect()
}
```

### Variation 3: Kth Largest Element in Stream

**Problem**: Design a class to find Kth largest in a stream.

**Key Insight**: Maintain min-heap of size K.

**Go Implementation**:
```go
type KthLargest struct {
    k    int
    heap *MinHeap
}

func Constructor(k int, nums []int) KthLargest {
    h := &MinHeap{}
    heap.Init(h)
    
    kth := KthLargest{k: k, heap: h}
    
    for _, num := range nums {
        kth.Add(num)
    }
    
    return kth
}

func (this *KthLargest) Add(val int) int {
    if this.heap.Len() < this.k {
        heap.Push(this.heap, val)
    } else if val > (*this.heap)[0] {
        heap.Pop(this.heap)
        heap.Push(this.heap, val)
    }
    
    return (*this.heap)[0]  // Kth largest is always at root
}
```

### Variation 4: Sliding Window Top K

**Problem**: For each window of size W, find top K.

**Approach**: Maintain heap, remove stale elements.

**Complexity**: O(N log K) with lazy deletion

---

## 8. Problem-Solving Framework {#framework}

### The 5-Step Analysis Protocol

```
┌─────────────────────────────────────────────┐
│ STEP 1: DECODE THE REQUIREMENT              │
│ - What defines "top"?                       │
│ - Is K fixed or variable?                   │
│ - Sorted output required?                   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ STEP 2: CHOOSE DATA STRUCTURE               │
│ - Heap if K << N                            │
│ - Sort if K ≈ N                             │
│ - Bucket if frequency-based                 │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ STEP 3: DETERMINE HEAP TYPE                 │
│ K Largest   → Min-Heap (small gatekeeper)   │
│ K Smallest  → Max-Heap (large gatekeeper)   │
│ K Closest   → Max-Heap (far gatekeeper)     │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ STEP 4: IMPLEMENT CORE LOGIC                │
│ - Build initial K-heap                      │
│ - Process remaining elements                │
│ - Maintain invariant: heap size ≤ K         │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ STEP 5: OPTIMIZE & VALIDATE                 │
│ - Edge cases: K=0, K=N, K>N                 │
│ - Post-process: sort if needed              │
│ - Verify complexity matches constraints     │
└─────────────────────────────────────────────┘
```

### Complexity Analysis Checklist

**Time Complexity**:
- Building initial heap: O(K) or O(K log K)
- Processing N-K elements: O((N-K) log K)
- **Total**: O(N log K)

**Space Complexity**:
- Heap: O(K)
- Auxiliary (hashmaps, etc.): Problem-specific

**Comparison with alternatives**:
- Sort: O(N log N) time, O(1) space
- QuickSelect: O(N) average time, O(1) space (for Kth, not K elements)

---

## 9. Practice Roadmap {#practice}

### Difficulty Progression

**Beginner** (Foundation):
1. ✓ Kth Largest Element in Array (LC 215)
2. ✓ Top K Frequent Elements (LC 347)
3. ✓ K Closest Points to Origin (LC 973)

**Intermediate** (Variations):
4. ✓ Find K Pairs with Smallest Sums (LC 373)
5. ✓ Kth Largest Element in Stream (LC 703)
6. ✓ Sort Characters by Frequency (LC 451)
7. ✓ Reorganize String (LC 767)

**Advanced** (Complex Applications):
8. ✓ Sliding Window Median (LC 480)
9. ✓ IPO (LC 502)
10. ✓ Maximum Performance of Team (LC 1383)
11. ✓ Split Array into Consecutive Subsequences (LC 659)

---

## Cognitive Strategies for Mastery

### Mental Rehearsal Protocol

Before coding, visualize:
1. **The heap state** after each operation
2. **The comparison** that triggers changes
3. **The invariant** you're maintaining (size K, heap property)

### Deliberate Practice Techniques

**Pattern Drilling**:
- Solve same problem in all 3 languages
- Compare idiomatic approaches
- Benchmark performance differences

**Variant Generation**:
- "What if K is large (K = 0.9N)?"
- "What if elements are streamed, not batched?"
- "What if I need K from multiple arrays?"

**Complexity Meditation**:
- Close your eyes and recite: "N log K vs N log N"
- Visualize the difference at scale: N=10^6, K=10
- **Feel** why partial sorting wins

### Meta-Learning Insight

The Top K pattern teaches a broader lesson:

> **"Optimization often comes from asking: 'Do I need complete information or sufficient information?'"**

This applies beyond algorithms:
- Database queries: LIMIT K vs full scan
- Machine learning: Top K predictions vs full distribution
- Decision making: Satisficing vs maximizing

---

## Final Wisdom

The path to the top 1% is paved with:
1. **Deep understanding** over memorization
2. **Pattern recognition** over brute force
3. **Iterative refinement** over perfection

Each problem you solve with the Top K pattern strengthens your ability to:
- Recognize when "good enough" is optimal
- Choose the right tool (heap, sort, select)
- Think in terms of complexity trade-offs

*"The master has failed more times than the beginner has tried."* — Keep practicing, keep refining, keep pushing the boundaries.

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│ TOP K ELEMENTS - QUICK DECISION TREE             │
├──────────────────────────────────────────────────┤
│                                                  │
│  K << N? → HEAP (O(N log K))                    │
│  K ≈ N?  → SORT (O(N log N))                    │
│                                                  │
│  Find K Largest?   → Min-Heap size K             │
│  Find K Smallest?  → Max-Heap size K             │
│  Find K Frequent?  → Count + Min-Heap            │
│  Find K Closest?   → Distance + Max-Heap         │
│                                                  │
│  Need sorted output? → sort(heap_result)         │
│  Stream input?       → Maintain heap online      │
│                                                  │
│  Space critical?   → QuickSelect (O(1) space)    │
│  Time critical?    → Heap (O(N log K))           │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Remember**: The heap is your gatekeeper. Choose wisely, maintain diligently, extract confidently.

# **Top K Elements Pattern: The Complete Mastery Guide**

*"In the pursuit of excellence, understanding when to seek the 'best few' rather than examining 'all' is the mark of an efficient mind."*---

## **Your Journey Begins Here, Future Master**

I've crafted a comprehensive guide that will serve as your foundation for conquering the Top K Elements pattern. This is not just a collection of algorithms—it's a **mental operating system** for efficient problem-solving.

### **What Makes This Pattern Profound**

The Top K pattern teaches you something that transcends coding: **the art of intelligent selection**. In a world drowning in data, the ability to efficiently identify "what matters most" is invaluable.

Consider this cognitive shift:
- **Novice thinking**: "I need to examine everything to find the best."
- **Expert thinking**: "I only need to maintain the best K, not total order."

This mental leap—from exhaustive analysis to selective optimization—is what separates good engineers from exceptional ones.

### **The Three Pillars of Mastery You'll Build**

1. **Structural Intuition** (Understanding WHY heaps work)
   - The heap as a "living filter"
   - The root as a "threshold guardian"
   - The logarithmic sweet spot (not linear, not constant)

2. **Pattern Recognition** (Knowing WHEN to apply)
   - Spotting "K from N" signatures instantly
   - Distinguishing between "Kth" vs "K elements"
   - Recognizing frequency, distance, and priority variations

3. **Implementation Fluency** (Coding EFFORTLESSLY)
   - Muscle memory across Rust, Python, Go
   - Language-specific idioms (heapq vs BinaryHeap vs container/heap)
   - Edge case handling without conscious thought

### **Immediate Action Plan**

Here's your structured path over the next 2 weeks:

**Week 1: Foundation**
- **Days 1-2**: Read the entire guide, trace examples by hand
- **Day 3**: Implement "K Largest Elements" in all 3 languages
- **Day 4**: Solve LC 215 (Kth Largest) - time yourself
- **Days 5-7**: Solve LC 347 (Top K Frequent) and LC 973 (K Closest Points)

**Week 2: Variation & Speed**
- **Days 8-10**: Tackle stream-based problems (LC 703, sliding windows)
- **Days 11-12**: Speed drills - solve previous problems in <15 minutes each
- **Days 13-14**: Teach-back exercise - explain the pattern to someone (or write it out)

### **The Psychological Edge: Flow State Triggers**

To enter deep focus when practicing:

1. **Clear Goal Setting**: "I will implement K Largest in Rust in 20 minutes"
2. **Immediate Feedback**: Run test cases after each function
3. **Challenge-Skill Balance**: Start easy, progressively increase difficulty
4. **Eliminate Distractions**: Phone off, single tab, timer visible

### **Cognitive Techniques for Pattern Internalization**

**Visualization Practice** (5 minutes before coding):
- Close your eyes
- Imagine the heap structure
- Visualize elements entering, being compared, some being rejected
- See the root changing as new elements challenge it

**Spaced Repetition**:
- Day 1: Solve problem
- Day 3: Resolve same problem (should be faster)
- Day 7: Resolve again (should be effortless)
- Day 30: Final mastery check

**The Feynman Technique**:
After solving each problem, explain out loud:
- "I used a min-heap because..."
- "The time complexity is O(N log K) because..."
- "This beats sorting because..."

### **Language-Specific Performance Notes**

**Python** (heapq):
- ✅ Simplest syntax, great for interviews
- ⚠️ Min-heap only (use negative values for max-heap)
- 🎯 Best for: Rapid prototyping

**Rust** (BinaryHeap):
- ✅ Max-heap by default, memory safe
- ⚠️ Need `Reverse<T>` for min-heap
- 🎯 Best for: Production systems, performance-critical code

**Go** (container/heap):
- ✅ Explicit interface, full control
- ⚠️ More boilerplate (implement 5 methods)
- 🎯 Best for: System programming, concurrent applications

### **Common Pitfalls to Avoid**

1. **Using wrong heap type**: K largest needs MIN-heap (counterintuitive!)
2. **Forgetting K bounds**: Always check if K > N
3. **Premature sorting**: Don't sort unless output must be sorted
4. **Ignoring space constraints**: Sometimes O(K) space is a dealbreaker

### **The 1% Mindset**

Remember these principles:

**Compound Growth**: Every problem solved makes the next easier. You're building neural pathways for pattern recognition.

**Deliberate Struggle**: When stuck, stay there for 30 minutes before checking solutions. The struggle builds the muscle.

**Active Reflection**: After each problem, journal:
- What was my initial approach?
- What pattern did I recognize?
- What would I do differently next time?

**Teaching Solidifies**: The best way to master is to teach. Explain these concepts to others (even imaginary ones).

---

### **Your Next Steps Right Now**

1. **Read the artifact completely** (bookmark it for reference)
2. **Implement the basic "K Largest" in Python** (start with the language you're most comfortable with)
3. **Trace through the example by hand** with [3,1,5,12,2,11], K=3
4. **Solve your first LeetCode problem**: #215 - Kth Largest Element

The path to the top 1% starts with this single pattern. Master it deeply, and you'll find that many other problems become mere variations of what you already know.

**Your potential is limitless. The only variable is your dedication to deliberate practice.**

Ready to begin? Pick up your keyboard. The clock starts now. 🚀