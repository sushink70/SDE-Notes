# 🎯 Ultimate DSA Pattern Recognition Guide
## The Mental Framework for Top 1% Problem Solvers

> "Pattern recognition is not memorization - it's building a mental index of problem structures that allows instant retrieval of solution templates."

---

## 📋 Table of Contents
1. [The Pattern Recognition Framework](#framework)
2. [Sequential Data Patterns](#sequential)
3. [Search & Optimization Patterns](#search)
4. [Graph & Tree Patterns](#graph)
5. [Combinatorial Patterns](#combinatorial)
6. [Data Structure Patterns](#datastructure)
7. [Pattern Identification Flowchart](#flowchart)

---

## <a name="framework"></a>🧠 The Pattern Recognition Framework

### Mental Model: The 3-Question Method
Before coding, ask these questions in order:

```
┌─────────────────────────────────────────────┐
│ Q1: What is the INPUT structure?           │
│     → Array? Tree? Graph? String?          │
├─────────────────────────────────────────────┤
│ Q2: What is the CONSTRAINT?                │
│     → Range? Sorted? Time limit?           │
├─────────────────────────────────────────────┤
│ Q3: What is the GOAL?                      │
│     → Find one? Find all? Optimize?        │
└─────────────────────────────────────────────┘
         ↓
    PATTERN EMERGES
```

### Cognitive Principle: Chunking
**Chunking** = Grouping information into meaningful units. Expert problem-solvers don't see individual operations - they see "chunks" (patterns). Your goal: build these chunks through deliberate practice.

---

## <a name="sequential"></a>📊 1. SEQUENTIAL DATA PATTERNS

### Pattern 1A: PREFIX SUM / CUMULATIVE SUM

#### 🎯 When to Identify:
- **Trigger words**: "sum of subarray", "range sum query", "contiguous elements"
- **Key signal**: Asked to calculate sum/product of **ranges** repeatedly
- **Time complexity hint**: If naive O(n²) solution involves recalculating sums

#### 🧩 Core Concept:
**Prefix Sum** = Running total from start to index i
```
Array:  [3, 1, 4, 1, 5]
Prefix: [3, 4, 8, 9, 14]
         ↑  ↑ 
         |  sum from 0 to index 1 = 4
         sum from 0 to index 0 = 3

Range sum [L, R] = prefix[R] - prefix[L-1]
```

#### 📐 Visualization:
```
Calculate sum of elements from index 2 to 4:

Array:    [3,  1,  4,  1,  5]
Index:     0   1   2   3   4
           └───────┘   └──────┘
           prefix[1]   prefix[4]
           = 4         = 14

Sum[2:4] = prefix[4] - prefix[1] = 14 - 4 = 10
Verify: 4 + 1 + 5 = 10 ✓
```

#### 💻 Implementation:

**Python:**
```python
def prefix_sum_example(arr):
    """
    Time: O(n) preprocessing + O(1) per query
    Space: O(n)
    """
    n = len(arr)
    prefix = [0] * (n + 1)  # Extra space to avoid index handling
    
    # Build prefix sum array
    for i in range(n):
        prefix[i + 1] = prefix[i] + arr[i]
    
    def range_sum(left, right):
        """Query sum from index left to right (inclusive)"""
        return prefix[right + 1] - prefix[left]
    
    return range_sum

# Example usage
arr = [3, 1, 4, 1, 5]
query = prefix_sum_example(arr)
print(query(2, 4))  # Output: 10
```

**Rust:**
```rust
fn prefix_sum_example(arr: &[i32]) -> Vec<i32> {
    // Time: O(n), Space: O(n)
    let mut prefix = vec![0; arr.len() + 1];
    
    for i in 0..arr.len() {
        prefix[i + 1] = prefix[i] + arr[i];
    }
    
    prefix
}

fn range_sum(prefix: &[i32], left: usize, right: usize) -> i32 {
    // O(1) query
    prefix[right + 1] - prefix[left]
}

fn main() {
    let arr = vec![3, 1, 4, 1, 5];
    let prefix = prefix_sum_example(&arr);
    println!("{}", range_sum(&prefix, 2, 4)); // Output: 10
}
```

**Go:**
```go
func prefixSumExample(arr []int) []int {
    // Time: O(n), Space: O(n)
    n := len(arr)
    prefix := make([]int, n+1)
    
    for i := 0; i < n; i++ {
        prefix[i+1] = prefix[i] + arr[i]
    }
    
    return prefix
}

func rangeSum(prefix []int, left, right int) int {
    // O(1) query
    return prefix[right+1] - prefix[left]
}

// Usage:
// arr := []int{3, 1, 4, 1, 5}
// prefix := prefixSumExample(arr)
// fmt.Println(rangeSum(prefix, 2, 4)) // Output: 10
```

#### 🔍 Pattern Recognition Training:
**Problem**: "Find number of subarrays with sum = K"
- ❌ Naive: Check all subarrays O(n²)
- ✅ Pattern: Prefix sum + Hash map (for count of each prefix sum)

---

### Pattern 1B: SLIDING WINDOW

#### 🎯 When to Identify:
- **Trigger words**: "contiguous", "subarray", "substring", "consecutive"
- **Key signal**: Need to find **optimal subarray/substring** with constraint
- **Window types**: 
  - Fixed size: "subarray of size k"
  - Variable size: "longest/shortest subarray with sum ≤ k"

#### 🧩 Core Concept:
**Sliding Window** = Maintain a "window" over array, expand/shrink to satisfy constraint

#### 📐 Visualization:
```
Find longest substring with at most 2 distinct characters: "eceba"

Step 1: Expand window
[e c e] b a  → window valid (2 distinct: e, c)
 ↑   ↑
 L   R

Step 2: Expand until invalid
[e c e b] a  → window invalid (3 distinct: e, c, b)
 ↑     ↑
 L     R

Step 3: Shrink from left
  [c e b] a  → window valid again (2 distinct: c, e, b)
   ↑   ↑
   L   R
```

#### 💻 Implementation:

**Python:**
```python
def sliding_window_max_length(s: str, k: int) -> int:
    """
    Find longest substring with at most k distinct characters
    Time: O(n), Space: O(k) for hash map
    """
    char_count = {}
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Expand window: add right character
        char_count[s[right]] = char_count.get(s[right], 0) + 1
        
        # Shrink window: remove from left while invalid
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        # Update result
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Example: longest substring with at most 2 distinct chars
print(sliding_window_max_length("eceba", 2))  # Output: 3 ("ece")
```

**Rust:**
```rust
use std::collections::HashMap;

fn sliding_window_max_length(s: &str, k: usize) -> usize {
    // Time: O(n), Space: O(k)
    let chars: Vec<char> = s.chars().collect();
    let mut char_count: HashMap<char, i32> = HashMap::new();
    let mut left = 0;
    let mut max_length = 0;
    
    for right in 0..chars.len() {
        // Expand window
        *char_count.entry(chars[right]).or_insert(0) += 1;
        
        // Shrink window while invalid
        while char_count.len() > k {
            if let Some(count) = char_count.get_mut(&chars[left]) {
                *count -= 1;
                if *count == 0 {
                    char_count.remove(&chars[left]);
                }
            }
            left += 1;
        }
        
        max_length = max_length.max(right - left + 1);
    }
    
    max_length
}
```

**Go:**
```go
func slidingWindowMaxLength(s string, k int) int {
    // Time: O(n), Space: O(k)
    charCount := make(map[rune]int)
    left := 0
    maxLength := 0
    runes := []rune(s)
    
    for right := 0; right < len(runes); right++ {
        // Expand window
        charCount[runes[right]]++
        
        // Shrink window while invalid
        for len(charCount) > k {
            charCount[runes[left]]--
            if charCount[runes[left]] == 0 {
                delete(charCount, runes[left])
            }
            left++
        }
        
        // Update result
        if right-left+1 > maxLength {
            maxLength = right - left + 1
        }
    }
    
    return maxLength
}
```

#### 🎓 Mental Model:
```
SLIDING WINDOW DECISION TREE:

Is window valid?
├── YES → Try to expand (move right pointer)
└── NO  → Must shrink (move left pointer)

Result tracking happens at VALID state
```

---

### Pattern 1C: TWO POINTERS

#### 🎯 When to Identify:
- **Trigger words**: "pair", "two elements", "sorted array", "remove duplicates"
- **Key signal**: Need to find **pair/combination** satisfying condition
- **Pre-condition**: Often works on **sorted arrays**

#### 🧩 Core Concept:
**Two Pointers** = Use two indices moving toward/away from each other based on logic

#### 📐 Visualization:
```
Find pair with sum = 9 in sorted array: [1, 2, 3, 4, 6]

Step 1: Start from ends
[1, 2, 3, 4, 6]
 ↑           ↑
 L           R
sum = 1 + 6 = 7 < 9 → move L right (need larger sum)

Step 2:
[1, 2, 3, 4, 6]
    ↑        ↑
    L        R
sum = 2 + 6 = 8 < 9 → move L right

Step 3:
[1, 2, 3, 4, 6]
       ↑     ↑
       L     R
sum = 3 + 6 = 9 ✓ FOUND
```

#### 💻 Implementation:

**Python:**
```python
def two_sum_sorted(arr: list[int], target: int) -> tuple[int, int] | None:
    """
    Find pair that sums to target in sorted array
    Time: O(n), Space: O(1)
    """
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        
        if current_sum == target:
            return (left, right)  # or (arr[left], arr[right])
        elif current_sum < target:
            left += 1  # Need larger sum
        else:
            right -= 1  # Need smaller sum
    
    return None  # No pair found

# Example
arr = [1, 2, 3, 4, 6]
result = two_sum_sorted(arr, 9)
print(result)  # Output: (2, 4) - indices of 3 and 6
```

**Rust:**
```rust
fn two_sum_sorted(arr: &[i32], target: i32) -> Option<(usize, usize)> {
    // Time: O(n), Space: O(1)
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    while left < right {
        let current_sum = arr[left] + arr[right];
        
        match current_sum.cmp(&target) {
            std::cmp::Ordering::Equal => return Some((left, right)),
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    
    None
}
```

**Go:**
```go
func twoSumSorted(arr []int, target int) (int, int, bool) {
    // Time: O(n), Space: O(1)
    left, right := 0, len(arr)-1
    
    for left < right {
        currentSum := arr[left] + arr[right]
        
        if currentSum == target {
            return left, right, true
        } else if currentSum < target {
            left++
        } else {
            right--
        }
    }
    
    return 0, 0, false // Not found
}
```

#### 🔍 Pattern Variants:
1. **Opposite direction**: Start from both ends (pair sum)
2. **Same direction**: Fast/slow pointers (cycle detection)
3. **Three pointers**: 3Sum problem

---

### Pattern 1D: MONOTONIC STACK

#### 🎯 When to Identify:
- **Trigger words**: "next greater", "next smaller", "previous larger", "histogram"
- **Key signal**: Need to find **nearest** element with certain property
- **Classic problems**: Stock span, largest rectangle in histogram

#### 🧩 Core Concept:
**Monotonic Stack** = Stack maintaining elements in increasing/decreasing order
- **Monotonic Increasing**: Each element ≥ previous (bottom to top)
- **Monotonic Decreasing**: Each element ≤ previous (bottom to top)

#### 📐 Visualization:
```
Find next greater element for each element: [4, 5, 2, 10, 8]

Stack (decreasing): Stores indices

Process i=0, val=4:
Stack: [0]  (index of 4)

Process i=1, val=5:
5 > 4 → 4's next greater = 5
Pop 0, push 1
Stack: [1]

Process i=2, val=2:
2 < 5 → just push
Stack: [1, 2]  (indices of 5, 2)

Process i=3, val=10:
10 > 2 → 2's next greater = 10
10 > 5 → 5's next greater = 10
Pop all, push 3
Stack: [3]

Process i=4, val=8:
8 < 10 → just push
Stack: [3, 4]

Result: [5, 10, 10, -1, -1]
```

#### 💻 Implementation:

**Python:**
```python
def next_greater_elements(arr: list[int]) -> list[int]:
    """
    Find next greater element for each element
    Time: O(n) - each element pushed/popped once
    Space: O(n) - for stack
    """
    n = len(arr)
    result = [-1] * n
    stack = []  # Stack of indices
    
    for i in range(n):
        # While current element is greater than stack top
        while stack and arr[i] > arr[stack[-1]]:
            idx = stack.pop()
            result[idx] = arr[i]
        
        stack.append(i)
    
    return result

# Example
arr = [4, 5, 2, 10, 8]
print(next_greater_elements(arr))  # [5, 10, 10, -1, -1]
```

**Rust:**
```rust
fn next_greater_elements(arr: &[i32]) -> Vec<i32> {
    // Time: O(n), Space: O(n)
    let n = arr.len();
    let mut result = vec![-1; n];
    let mut stack: Vec<usize> = Vec::new();
    
    for i in 0..n {
        while !stack.is_empty() && arr[i] > arr[*stack.last().unwrap()] {
            if let Some(idx) = stack.pop() {
                result[idx] = arr[i];
            }
        }
        stack.push(i);
    }
    
    result
}
```

**Go:**
```go
func nextGreaterElements(arr []int) []int {
    // Time: O(n), Space: O(n)
    n := len(arr)
    result := make([]int, n)
    for i := range result {
        result[i] = -1
    }
    
    stack := []int{} // Stack of indices
    
    for i := 0; i < n; i++ {
        for len(stack) > 0 && arr[i] > arr[stack[len(stack)-1]] {
            idx := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            result[idx] = arr[i]
        }
        stack = append(stack, i)
    }
    
    return result
}
```

#### 🎓 Mental Model:
```
Monotonic Stack Logic:

Current element vs Stack top:
├── Current > Top → Found answer for top, POP
└── Current ≤ Top → No answer yet, PUSH current

Key insight: Elements in stack are "waiting" for their answer
```

---

## <a name="search"></a>🔍 2. SEARCH & OPTIMIZATION PATTERNS

### Pattern 2A: BINARY SEARCH

#### 🎯 When to Identify:
- **Trigger words**: "sorted", "find target", "search in rotated", "first/last occurrence"
- **Key signal**: Data has **monotonic property** (sorted or can be evaluated as True/False)
- **Hidden binary search**: "Find minimum X such that condition(X) is true"

#### 🧩 Core Concept:
**Binary Search** = Eliminate half of search space each iteration by checking middle

**Standard Definition**: In a sorted array, value at index `mid` tells us which half contains target.

#### 📐 Visualization:
```
Search 7 in [1, 3, 5, 7, 9, 11, 13]

Step 1: Check middle
[1, 3, 5, 7, 9, 11, 13]
        ↑
       mid=7
7 == 7 → FOUND!

But if searching for 9:
Step 1:
[1, 3, 5, 7, 9, 11, 13]
 ↑      ↑           ↑
 L     mid=7        R
9 > 7 → search right half

Step 2:
[1, 3, 5, 7, 9, 11, 13]
            ↑  ↑    ↑
            L mid=11 R
9 < 11 → search left half

Step 3:
[1, 3, 5, 7, 9, 11, 13]
            ↑
           mid=9
9 == 9 → FOUND!
```

#### 💻 Implementation:

**Python:**
```python
def binary_search(arr: list[int], target: int) -> int:
    """
    Standard binary search
    Time: O(log n), Space: O(1)
    Returns: index if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Avoid overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1  # Search right half
        else:
            right = mid - 1  # Search left half
    
    return -1  # Not found

# Advanced: Find first occurrence
def binary_search_first(arr: list[int], target: int) -> int:
    """Find leftmost occurrence of target"""
    left, right = 0, len(arr) - 1
    result = -1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            result = mid
            right = mid - 1  # Continue searching left
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return result

# Example
arr = [1, 3, 5, 7, 9, 11, 13]
print(binary_search(arr, 9))  # Output: 4
```

**Rust:**
```rust
fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    // Time: O(log n), Space: O(1)
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

// Rust also has built-in: arr.binary_search(&target)
```

**Go:**
```go
func binarySearch(arr []int, target int) int {
    // Time: O(log n), Space: O(1)
    left, right := 0, len(arr)-1
    
    for left <= right {
        mid := left + (right-left)/2
        
        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return -1
}

// Go also has: sort.SearchInts(arr, target)
```

#### 🎓 Advanced Pattern: Binary Search on Answer

**Problem**: "Find minimum speed to eat all bananas in H hours"
- Not searching in array, but searching for **optimal value**!

```python
def binary_search_on_answer(condition_func, low, high):
    """
    Find minimum value where condition becomes True
    Template for binary search on answer space
    """
    result = -1
    
    while low <= high:
        mid = low + (high - low) // 2
        
        if condition_func(mid):  # Can we achieve goal with 'mid'?
            result = mid
            high = mid - 1  # Try smaller value
        else:
            low = mid + 1  # Need larger value
    
    return result
```

---

## <a name="graph"></a>🌳 3. GRAPH & TREE PATTERNS

### Pattern 3A: DFS (Depth-First Search)

#### 🎯 When to Identify:
- **Trigger words**: "path", "connected components", "explore all", "backtrack"
- **Key signal**: Need to explore **as deep as possible** before backtracking
- **Use cases**: Finding paths, cycles, connectivity

#### 🧩 Core Concept:
**DFS** = Explore one branch completely before trying other branches
- Uses **stack** (or recursion which uses call stack)
- Goes **deep** first

#### 📐 Visualization:
```
Tree:        1
           /   \
          2     3
         / \   /
        4   5 6

DFS Traversal (preorder):
Visit order: 1 → 2 → 4 → 5 → 3 → 6

Stack evolution:
[1]           → Visit 1
[2, 3]        → Visit 2 (pop 1, push children)
[4, 5, 3]     → Visit 4 (pop 2, push children)
[5, 3]        → Visit 5 (pop 4, no children)
[3]           → Visit 3 (pop 5, no children)
[6]           → Visit 6 (pop 3, push children)
[]            → Done
```

#### 💻 Implementation:

**Python:**
```python
# Recursive DFS (most common)
def dfs_recursive(graph: dict[int, list[int]], start: int, visited: set[int]):
    """
    Time: O(V + E) where V=vertices, E=edges
    Space: O(V) for recursion stack + visited set
    """
    visited.add(start)
    print(start, end=' ')  # Process node
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)

# Iterative DFS using explicit stack
def dfs_iterative(graph: dict[int, list[int]], start: int):
    """
    Time: O(V + E), Space: O(V)
    """
    visited = set()
    stack = [start]
    
    while stack:
        node = stack.pop()
        
        if node in visited:
            continue
        
        visited.add(node)
        print(node, end=' ')
        
        # Add neighbors in reverse order for same traversal as recursive
        for neighbor in reversed(graph[node]):
            if neighbor not in visited:
                stack.append(neighbor)

# Example usage
graph = {
    1: [2, 3],
    2: [4, 5],
    3: [6],
    4: [],
    5: [],
    6: []
}

visited = set()
dfs_recursive(graph, 1, visited)  # Output: 1 2 4 5 3 6
```

**Rust:**
```rust
use std::collections::{HashSet, HashMap};

fn dfs_recursive(
    graph: &HashMap<i32, Vec<i32>>,
    node: i32,
    visited: &mut HashSet<i32>
) {
    // Time: O(V + E), Space: O(V)
    visited.insert(node);
    print!("{} ", node);
    
    if let Some(neighbors) = graph.get(&node) {
        for &neighbor in neighbors {
            if !visited.contains(&neighbor) {
                dfs_recursive(graph, neighbor, visited);
            }
        }
    }
}

fn dfs_iterative(graph: &HashMap<i32, Vec<i32>>, start: i32) {
    let mut visited = HashSet::new();
    let mut stack = vec![start];
    
    while let Some(node) = stack.pop() {
        if visited.contains(&node) {
            continue;
        }
        
        visited.insert(node);
        print!("{} ", node);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors.iter().rev() {
                if !visited.contains(&neighbor) {
                    stack.push(neighbor);
                }
            }
        }
    }
}
```

**Go:**
```go
func dfsRecursive(graph map[int][]int, node int, visited map[int]bool) {
    // Time: O(V + E), Space: O(V)
    visited[node] = true
    fmt.Printf("%d ", node)
    
    for _, neighbor := range graph[node] {
        if !visited[neighbor] {
            dfsRecursive(graph, neighbor, visited)
        }
    }
}

func dfsIterative(graph map[int][]int, start int) {
    visited := make(map[int]bool)
    stack := []int{start}
    
    for len(stack) > 0 {
        // Pop from stack
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        
        if visited[node] {
            continue
        }
        
        visited[node] = true
        fmt.Printf("%d ", node)
        
        // Add neighbors in reverse order
        neighbors := graph[node]
        for i := len(neighbors) - 1; i >= 0; i-- {
            if !visited[neighbors[i]] {
                stack = append(stack, neighbors[i])
            }
        }
    }
}
```

---

### Pattern 3B: BFS (Breadth-First Search)

#### 🎯 When to Identify:
- **Trigger words**: "shortest path", "level-order", "minimum steps", "distance"
- **Key signal**: Need to explore **layer by layer** (all neighbors before going deeper)
- **Guarantee**: BFS finds **shortest path** in unweighted graphs

#### 🧩 Core Concept:
**BFS** = Explore all neighbors at current depth before going deeper
- Uses **queue** (FIFO)
- Goes **wide** first

#### 📐 Visualization:
```
Same tree:   1
           /   \
          2     3
         / \   /
        4   5 6

BFS Traversal (level-order):
Visit order: 1 → 2 → 3 → 4 → 5 → 6

Queue evolution:
[1]              → Visit 1
[2, 3]           → Visit 2 (dequeue 1, enqueue children)
[3, 4, 5]        → Visit 3 (dequeue 2, enqueue children)
[4, 5, 6]        → Visit 4 (dequeue 3, enqueue children)
[5, 6]           → Visit 5 (dequeue 4, no children)
[6]              → Visit 6 (dequeue 5, no children)
[]               → Done

Level tracking:
Level 0: [1]
Level 1: [2, 3]
Level 2: [4, 5, 6]
```

#### 💻 Implementation:

**Python:**
```python
from collections import deque

def bfs(graph: dict[int, list[int]], start: int):
    """
    Time: O(V + E), Space: O(V)
    """
    visited = set([start])
    queue = deque([start])
    
    while queue:
        node = queue.popleft()  # FIFO
        print(node, end=' ')
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

# BFS with level tracking (common pattern)
def bfs_with_levels(graph: dict[int, list[int]], start: int):
    """Track distance/level of each node from start"""
    visited = {start: 0}  # node -> level
    queue = deque([(start, 0)])  # (node, level)
    
    while queue:
        node, level = queue.popleft()
        print(f"Node {node} at level {level}")
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited[neighbor] = level + 1
                queue.append((neighbor, level + 1))
    
    return visited

# Example
graph = {
    1: [2, 3],
    2: [4, 5],
    3: [6],
    4: [],
    5: [],
    6: []
}

bfs(graph, 1)  # Output: 1 2 3 4 5 6
```

**Rust:**
```rust
use std::collections::{HashSet, HashMap, VecDeque};

fn bfs(graph: &HashMap<i32, Vec<i32>>, start: i32) {
    // Time: O(V + E), Space: O(V)
    let mut visited = HashSet::new();
    let mut queue = VecDeque::new();
    
    visited.insert(start);
    queue.push_back(start);
    
    while let Some(node) = queue.pop_front() {
        print!("{} ", node);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    queue.push_back(neighbor);
                }
            }
        }
    }
}

fn bfs_with_levels(graph: &HashMap<i32, Vec<i32>>, start: i32) -> HashMap<i32, i32> {
    let mut levels = HashMap::new();
    let mut queue = VecDeque::new();
    
    levels.insert(start, 0);
    queue.push_back((start, 0));
    
    while let Some((node, level)) = queue.pop_front() {
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !levels.contains_key(&neighbor) {
                    levels.insert(neighbor, level + 1);
                    queue.push_back((neighbor, level + 1));
                }
            }
        }
    }
    
    levels
}
```

**Go:**
```go
func bfs(graph map[int][]int, start int) {
    // Time: O(V + E), Space: O(V)
    visited := make(map[int]bool)
    queue := []int{start}
    visited[start] = true
    
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:] // Dequeue (inefficient but simple)
        
        fmt.Printf("%d ", node)
        
        for _, neighbor := range graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true
                queue = append(queue, neighbor)
            }
        }
    }
}

// More efficient with circular buffer or container/list
```

#### 🎓 Mental Model - DFS vs BFS:
```
Choose DFS when:
✓ Finding ANY path (not shortest)
✓ Detecting cycles
✓ Topological sort
✓ Less memory for deep graphs

Choose BFS when:
✓ Finding SHORTEST path
✓ Level-order traversal
✓ Minimum steps problems
✓ Better for wide graphs
```

---

## <a name="combinatorial"></a>🎲 4. COMBINATORIAL PATTERNS

### Pattern 4A: BACKTRACKING

#### 🎯 When to Identify:
- **Trigger words**: "all combinations", "all permutations", "all subsets", "generate all"
- **Key signal**: Need to explore **all possibilities** with choices
- **Classic problems**: N-Queens, Sudoku solver, combination sum

#### 🧩 Core Concept:
**Backtracking** = Try all possibilities by making choice, exploring, then undoing choice (backtrack)

**Decision Tree**: Each level = one decision, branches = choices

#### 📐 Visualization:
```
Generate all subsets of [1, 2, 3]:

Decision tree (include or exclude each element):

                     []
                  /      \
            [1]              []
           /    \          /    \
      [1,2]    [1]     [2]      []
      /  \     / \     / \      / \
  [1,2,3][1,2][1,3][1][2,3][2][3][]

Result: [[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]
```

#### 💻 Implementation:

**Python:**
```python
def generate_subsets(nums: list[int]) -> list[list[int]]:
    """
    Generate all subsets (power set)
    Time: O(2^n * n) - 2^n subsets, O(n) to copy each
    Space: O(n) for recursion depth
    """
    result = []
    
    def backtrack(start: int, current: list[int]):
        # Add current subset to result
        result.append(current[:])  # Make a copy!
        
        # Try adding each remaining element
        for i in range(start, len(nums)):
            # Make choice
            current.append(nums[i])
            
            # Explore with this choice
            backtrack(i + 1, current)
            
            # Undo choice (backtrack)
            current.pop()
    
    backtrack(0, [])
    return result

# More complex: Generate all permutations
def generate_permutations(nums: list[int]) -> list[list[int]]:
    """
    Time: O(n! * n), Space: O(n)
    """
    result = []
    
    def backtrack(current: list[int]):
        if len(current) == len(nums):
            result.append(current[:])
            return
        
        for num in nums:
            if num in current:  # Already used
                continue
            
            # Make choice
            current.append(num)
            
            # Explore
            backtrack(current)
            
            # Undo choice
            current.pop()
    
    backtrack([])
    return result

# Example
print(generate_subsets([1, 2, 3]))
# Output: [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]
```

**Rust:**
```rust
fn generate_subsets(nums: &[i32]) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    
    fn backtrack(
        nums: &[i32],
        start: usize,
        current: &mut Vec<i32>,
        result: &mut Vec<Vec<i32>>
    ) {
        result.push(current.clone());
        
        for i in start..nums.len() {
            current.push(nums[i]);
            backtrack(nums, i + 1, current, result);
            current.pop();
        }
    }
    
    backtrack(nums, 0, &mut current, &mut result);
    result
}

fn generate_permutations(nums: &[i32]) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    let mut used = vec![false; nums.len()];
    
    fn backtrack(
        nums: &[i32],
        current: &mut Vec<i32>,
        used: &mut Vec<bool>,
        result: &mut Vec<Vec<i32>>
    ) {
        if current.len() == nums.len() {
            result.push(current.clone());
            return;
        }
        
        for i in 0..nums.len() {
            if used[i] {
                continue;
            }
            
            current.push(nums[i]);
            used[i] = true;
            
            backtrack(nums, current, used, result);
            
            current.pop();
            used[i] = false;
        }
    }
    
    backtrack(nums, &mut current, &mut used, &mut result);
    result
}
```

**Go:**
```go
func generateSubsets(nums []int) [][]int {
    var result [][]int
    var current []int
    
    var backtrack func(start int)
    backtrack = func(start int) {
        // Make copy of current
        temp := make([]int, len(current))
        copy(temp, current)
        result = append(result, temp)
        
        for i := start; i < len(nums); i++ {
            current = append(current, nums[i])
            backtrack(i + 1)
            current = current[:len(current)-1] // Pop
        }
    }
    
    backtrack(0)
    return result
}
```

#### 🎓 Backtracking Template:
```python
def backtracking_template(choices, constraints):
    result = []
    
    def backtrack(current_state):
        # Base case: reached goal
        if is_goal(current_state):
            result.append(copy(current_state))
            return
        
        # Try each choice
        for choice in get_choices(current_state):
            # Pruning: skip invalid choices early
            if not is_valid(choice, constraints):
                continue
            
            # Make choice
            make_choice(current_state, choice)
            
            # Recurse
            backtrack(current_state)
            
            # Undo choice (backtrack)
            undo_choice(current_state, choice)
    
    backtrack(initial_state)
    return result
```

---

### Pattern 4B: DYNAMIC PROGRAMMING (DP)

#### 🎯 When to Identify:
- **Trigger words**: "maximum", "minimum", "count ways", "optimal"
- **Key signals**:
  1. **Optimal substructure**: Optimal solution contains optimal solutions to subproblems
  2. **Overlapping subproblems**: Same subproblems computed multiple times
- **Questions to ask**: "Can I break this into smaller identical problems?"

#### 🧩 Core Concept:
**Dynamic Programming** = Store solutions to subproblems to avoid recomputation

**Two approaches**:
1. **Memoization** (Top-down): Recursion + cache
2. **Tabulation** (Bottom-up): Iterative + table

#### 📐 Visualization - Fibonacci Example:
```
Naive recursion (exponential time):
fib(5) calls:
                fib(5)
              /        \
          fib(4)      fib(3)
         /     \      /    \
     fib(3) fib(2) fib(2) fib(1)
     /   \
  fib(2) fib(1)

Notice: fib(3) computed twice, fib(2) computed 3 times!

DP solution: Store results in memo/table
fib(0)=0, fib(1)=1, fib(2)=1, fib(3)=2, fib(4)=3, fib(5)=5
Each computed once!
```

#### 💻 Implementation:

**Python:**
```python
# Approach 1: Memoization (Top-down)
def fib_memo(n: int) -> int:
    """
    Time: O(n), Space: O(n)
    """
    memo = {}
    
    def helper(n: int) -> int:
        if n <= 1:
            return n
        
        if n in memo:
            return memo[n]
        
        memo[n] = helper(n - 1) + helper(n - 2)
        return memo[n]
    
    return helper(n)

# Approach 2: Tabulation (Bottom-up)
def fib_tab(n: int) -> int:
    """
    Time: O(n), Space: O(n)
    """
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

# Optimized: Space O(1) using rolling variables
def fib_optimized(n: int) -> int:
    """
    Time: O(n), Space: O(1)
    """
    if n <= 1:
        return n
    
    prev2, prev1 = 0, 1
    
    for _ in range(2, n + 1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    
    return prev1

# Classic DP: Coin Change (minimum coins to make amount)
def coin_change(coins: list[int], amount: int) -> int:
    """
    Time: O(amount * len(coins)), Space: O(amount)
    """
    # dp[i] = minimum coins needed to make amount i
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case: 0 coins for amount 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

# Example
print(coin_change([1, 2, 5], 11))  # Output: 3 (5+5+1)
```

**Rust:**
```rust
use std::collections::HashMap;

fn fib_memo(n: i32) -> i32 {
    fn helper(n: i32, memo: &mut HashMap<i32, i32>) -> i32 {
        if n <= 1 {
            return n;
        }
        
        if let Some(&result) = memo.get(&n) {
            return result;
        }
        
        let result = helper(n - 1, memo) + helper(n - 2, memo);
        memo.insert(n, result);
        result
    }
    
    let mut memo = HashMap::new();
    helper(n, &mut memo)
}

fn fib_tab(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    
    let mut dp = vec![0; (n + 1) as usize];
    dp[1] = 1;
    
    for i in 2..=n as usize {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n as usize]
}

fn coin_change(coins: &[i32], amount: i32) -> i32 {
    let amount_usize = amount as usize;
    let mut dp = vec![i32::MAX; amount_usize + 1];
    dp[0] = 0;
    
    for i in 1..=amount_usize {
        for &coin in coins {
            let coin_usize = coin as usize;
            if coin_usize <= i && dp[i - coin_usize] != i32::MAX {
                dp[i] = dp[i].min(dp[i - coin_usize] + 1);
            }
        }
    }
    
    if dp[amount_usize] == i32::MAX { -1 } else { dp[amount_usize] }
}
```

**Go:**
```go
func fibMemo(n int) int {
    memo := make(map[int]int)
    
    var helper func(int) int
    helper = func(n int) int {
        if n <= 1 {
            return n
        }
        
        if val, ok := memo[n]; ok {
            return val
        }
        
        memo[n] = helper(n-1) + helper(n-2)
        return memo[n]
    }
    
    return helper(n)
}

func fibTab(n int) int {
    if n <= 1 {
        return n
    }
    
    dp := make([]int, n+1)
    dp[1] = 1
    
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    
    return dp[n]
}

func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp {
        dp[i] = amount + 1 // Initialize with impossible value
    }
    dp[0] = 0
    
    for i := 1; i <= amount; i++ {
        for _, coin := range coins {
            if coin <= i {
                dp[i] = min(dp[i], dp[i-coin]+1)
            }
        }
    }
    
    if dp[amount] > amount {
        return -1
    }
    return dp[amount]
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

#### 🎓 DP Problem-Solving Framework:
```
Step 1: Identify DP problem
├── Optimization (max/min)?
├── Counting ways?
└── Overlapping subproblems?

Step 2: Define state
dp[i] = ?
dp[i][j] = ?

Step 3: Find recurrence relation
dp[i] = f(dp[i-1], dp[i-2], ...)

Step 4: Base cases
dp[0] = ?

Step 5: Order of computation
Which dp values needed first?

Step 6: Optimize space if possible
Can we use O(1) instead of O(n)?
```

---

## <a name="datastructure"></a>🗄️ 5. DATA STRUCTURE PATTERNS

### Pattern 5A: HEAP (Priority Queue)

#### 🎯 When to Identify:
- **Trigger words**: "top K", "Kth largest", "Kth smallest", "merge K sorted"
- **Key signal**: Need **dynamic** access to min/max element
- **When NOT to use**: If need to access middle elements or maintain order

#### 🧩 Core Concept:
**Heap** = Complete binary tree where parent is larger/smaller than children
- **Max Heap**: Parent ≥ children (root = maximum)
- **Min Heap**: Parent ≤ children (root = minimum)

**Key operations**:
- Insert: O(log n)
- Extract min/max: O(log n)
- Peek min/max: O(1)

#### 📐 Visualization:
```
Min Heap structure:
         1
       /   \
      3     5
     / \   /
    7   9 8

Array representation: [1, 3, 5, 7, 9, 8]
Index:                 0  1  2  3  4  5

Parent-child relationships:
- Parent of index i: (i-1)//2
- Left child of i: 2*i + 1
- Right child of i: 2*i + 2

Insert 2:
Step 1: Add to end
         1
       /   \
      3     5
     / \   / \
    7   9 8   2
    
Step 2: Bubble up (2 < 5)
         1
       /   \
      3     2
     / \   / \
    7   9 8   5
```

#### 💻 Implementation:

**Python:**
```python
import heapq

# Python uses min heap by default
def top_k_elements(nums: list[int], k: int) -> list[int]:
    """
    Find K largest elements
    Time: O(n log k), Space: O(k)
    
    Strategy: Maintain min heap of size k
    If element > heap top, replace it
    """
    # For k largest, use min heap
    heap = nums[:k]
    heapq.heapify(heap)  # O(k)
    
    for num in nums[k:]:
        if num > heap[0]:  # num larger than smallest in heap
            heapq.heapreplace(heap, num)  # Pop and push in one operation
    
    return heap

# For max heap, negate values
def top_k_smallest(nums: list[int], k: int) -> list[int]:
    """K smallest using max heap (negate trick)"""
    heap = [-x for x in nums[:k]]
    heapq.heapify(heap)
    
    for num in nums[k:]:
        if num < -heap[0]:
            heapq.heapreplace(heap, -num)
    
    return [-x for x in heap]

# Merge K sorted lists (classic heap problem)
def merge_k_sorted(lists: list[list[int]]) -> list[int]:
    """
    Time: O(N log k) where N = total elements, k = number of lists
    Space: O(k) for heap
    """
    heap = []
    result = []
    
    # Initialize heap with first element from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))  # (value, list_idx, element_idx)
    
    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        
        # Add next element from same list
        if elem_idx + 1 < len(lists[list_idx]):
            next_val = lists[list_idx][elem_idx + 1]
            heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))
    
    return result

# Example
nums = [3, 2, 1, 5, 6, 4]
print(top_k_elements(nums, 2))  # [5, 6] or [6, 5] (heap doesn't maintain order)

lists = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
print(merge_k_sorted(lists))  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

**Rust:**
```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn top_k_elements(nums: &[i32], k: usize) -> Vec<i32> {
    // Time: O(n log k), Space: O(k)
    // BinaryHeap is max heap, so use Reverse for min heap
    let mut heap: BinaryHeap<Reverse<i32>> = nums[..k]
        .iter()
        .map(|&x| Reverse(x))
        .collect();
    
    for &num in &nums[k..] {
        if let Some(&Reverse(min)) = heap.peek() {
            if num > min {
                heap.pop();
                heap.push(Reverse(num));
            }
        }
    }
    
    heap.into_iter().map(|Reverse(x)| x).collect()
}

fn merge_k_sorted(lists: Vec<Vec<i32>>) -> Vec<i32> {
    let mut heap = BinaryHeap::new();
    let mut result = Vec::new();
    
    // Initialize heap
    for (list_idx, list) in lists.iter().enumerate() {
        if !list.is_empty() {
            heap.push(Reverse((list[0], list_idx, 0)));
        }
    }
    
    while let Some(Reverse((val, list_idx, elem_idx))) = heap.pop() {
        result.push(val);
        
        if elem_idx + 1 < lists[list_idx].len() {
            let next_val = lists[list_idx][elem_idx + 1];
            heap.push(Reverse((next_val, list_idx, elem_idx + 1)));
        }
    }
    
    result
}
```

**Go:**
```go
import "container/heap"

// Implement heap interface for min heap
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

func topKElements(nums []int, k int) []int {
    h := &MinHeap{}
    heap.Init(h)
    
    // Add first k elements
    for i := 0; i < k && i < len(nums); i++ {
        heap.Push(h, nums[i])
    }
    
    // For remaining elements
    for i := k; i < len(nums); i++ {
        if nums[i] > (*h)[0] {
            heap.Pop(h)
            heap.Push(h, nums[i])
        }
    }
    
    return []int(*h)
}

// For merge k sorted, define custom heap element
type HeapElement struct {
    val      int
    listIdx  int
    elemIdx  int
}

type ElementHeap []HeapElement

func (h ElementHeap) Len() int           { return len(h) }
func (h ElementHeap) Less(i, j int) bool { return h[i].val < h[j].val }
func (h ElementHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *ElementHeap) Push(x interface{}) {
    *h = append(*h, x.(HeapElement))
}

func (h *ElementHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func mergeKSorted(lists [][]int) []int {
    h := &ElementHeap{}
    heap.Init(h)
    
    // Initialize heap
    for i, list := range lists {
        if len(list) > 0 {
            heap.Push(h, HeapElement{list[0], i, 0})
        }
    }
    
    result := []int{}
    
    for h.Len() > 0 {
        elem := heap.Pop(h).(HeapElement)
        result = append(result, elem.val)
        
        if elem.elemIdx+1 < len(lists[elem.listIdx]) {
            nextVal := lists[elem.listIdx][elem.elemIdx+1]
            heap.Push(h, HeapElement{nextVal, elem.listIdx, elem.elemIdx + 1})
        }
    }
    
    return result
}
```

#### 🎓 Mental Model - When to Use Heap:
```
Question: Do I need to repeatedly access min/max?
├── YES → Heap is likely the answer
│   └── Typical scenarios:
│       ├── Find K largest/smallest
│       ├── Running median
│       ├── Merge K sorted
│       └── Scheduling problems
│
└── NO → Consider:
    ├── Simple max/min → Just track variable
    ├── Access middle elements → Sorted array or balanced BST
    └── Maintain insertion order → Queue or list
```

---

### Pattern 5B: HASH MAP / HASH SET

#### 🎯 When to Identify:
- **Trigger words**: "count frequency", "find pair", "check existence", "unique elements"
- **Key signal**: Need **O(1) lookup** or need to **track seen elements**
- **Classic use cases**: Two Sum, group anagrams, longest substring

#### 🧩 Core Concept:
**Hash Map** = Key-value store with O(1) average lookup
**Hash Set** = Collection of unique elements with O(1) lookup

**Trade-off**: Speed vs Space (use extra space for faster lookup)

#### 📐 Visualization:
```
Problem: Find two numbers that sum to target

Array: [2, 7, 11, 15], target = 9

Naive approach O(n²):
Check all pairs: (2,7), (2,11), (2,15), (7,11), (7,15), (11,15)

Hash map approach O(n):
seen = {}

i=0, num=2:
  complement = 9-2 = 7
  7 not in seen
  seen[2] = 0

i=1, num=7:
  complement = 9-7 = 2
  2 in seen! ✓
  return [seen[2], 1] = [0, 1]
```

#### 💻 Implementation:

**Python:**
```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Find indices of two numbers that sum to target
    Time: O(n), Space: O(n)
    """
    seen = {}  # value -> index
    
    for i, num in enumerate(nums):
        complement = target - num
        
        if complement in seen:
            return [seen[complement], i]
        
        seen[num] = i
    
    return []

# Pattern: Count frequency
def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """
    Find k most frequent elements
    Time: O(n log k) or O(n) with bucket sort, Space: O(n)
    """
    from collections import Counter
    import heapq
    
    # Count frequencies
    freq = Counter(nums)
    
    # Use heap to get top k
    return heapq.nlargest(k, freq.keys(), key=freq.get)

# Pattern: Group by property
def group_anagrams(strs: list[str]) -> list[list[str]]:
    """
    Group strings that are anagrams
    Time: O(n * k log k) where k = max string length
    Space: O(n * k)
    """
    groups = {}
    
    for s in strs:
        # Sorted string as key (anagrams have same sorted form)
        key = ''.join(sorted(s))
        
        if key not in groups:
            groups[key] = []
        groups[key].append(s)
    
    return list(groups.values())

# Pattern: Longest substring without repeating characters
def longest_unique_substring(s: str) -> int:
    """
    Time: O(n), Space: O(min(n, charset_size))
    """
    char_index = {}  # char -> last seen index
    max_length = 0
    start = 0
    
    for i, char in enumerate(s):
        # If char seen and in current window
        if char in char_index and char_index[char] >= start:
            start = char_index[char] + 1
        
        char_index[char] = i
        max_length = max(max_length, i - start + 1)
    
    return max_length

# Examples
print(two_sum([2, 7, 11, 15], 9))  # [0, 1]
print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))
# [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
print(longest_unique_substring("abcabcbb"))  # 3 ("abc")
```

**Rust:**
```rust
use std::collections::HashMap;

fn two_sum(nums: &[i32], target: i32) -> Option<(usize, usize)> {
    let mut seen = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        
        if let Some(&j) = seen.get(&complement) {
            return Some((j, i));
        }
        
        seen.insert(num, i);
    }
    
    None
}

fn group_anagrams(strs: Vec<String>) -> Vec<Vec<String>> {
    let mut groups: HashMap<String, Vec<String>> = HashMap::new();
    
    for s in strs {
        let mut chars: Vec<char> = s.chars().collect();
        chars.sort_unstable();
        let key: String = chars.into_iter().collect();
        
        groups.entry(key).or_insert_with(Vec::new).push(s);
    }
    
    groups.into_values().collect()
}

fn longest_unique_substring(s: &str) -> usize {
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_length = 0;
    let mut start = 0;
    
    for (i, c) in s.chars().enumerate() {
        if let Some(&last_index) = char_index.get(&c) {
            if last_index >= start {
                start = last_index + 1;
            }
        }
        
        char_index.insert(c, i);
        max_length = max_length.max(i - start + 1);
    }
    
    max_length
}
```

**Go:**
```go
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int)
    
    for i, num := range nums {
        complement := target - num
        
        if j, ok := seen[complement]; ok {
            return []int{j, i}
        }
        
        seen[num] = i
    }
    
    return []int{}
}

func groupAnagrams(strs []string) [][]string {
    groups := make(map[string][]string)
    
    for _, s := range strs {
        // Convert to rune slice, sort, convert back
        runes := []rune(s)
        sort.Slice(runes, func(i, j int) bool {
            return runes[i] < runes[j]
        })
        key := string(runes)
        
        groups[key] = append(groups[key], s)
    }
    
    result := make([][]string, 0, len(groups))
    for _, group := range groups {
        result = append(result, group)
    }
    
    return result
}

func longestUniqueSubstring(s string) int {
    charIndex := make(map[rune]int)
    maxLength := 0
    start := 0
    
    for i, c := range s {
        if lastIndex, ok := charIndex[c]; ok && lastIndex >= start {
            start = lastIndex + 1
        }
        
        charIndex[c] = i
        if i-start+1 > maxLength {
            maxLength = i - start + 1
        }
    }
    
    return maxLength
}
```

---

### Pattern 5C: UNION-FIND (Disjoint Set)

#### 🎯 When to Identify:
- **Trigger words**: "connected components", "groups", "cycles in undirected graph"
- **Key signal**: Need to **merge groups** and **check connectivity**
- **Classic problems**: Number of islands (alternate approach), redundant connections

#### 🧩 Core Concept:
**Union-Find** = Data structure for tracking disjoint sets with two operations:
1. **Find**: Which set does element belong to? (find representative/root)
2. **Union**: Merge two sets

**Optimizations**:
- **Path compression**: Make all nodes point directly to root during find
- **Union by rank**: Attach smaller tree under larger tree

#### 📐 Visualization:
```
Initial state: {0}, {1}, {2}, {3}, {4}

Union(0, 1):
  0     2   3   4
  |
  1

Union(2, 3):
  0     2   4
  |     |
  1     3

Union(0, 2):
      0     4
    /   \
   1     2
         |
         3

Find(3) with path compression:
Before:           After:
    0                 0
  /   \             / | \
 1     2           1  2  3
       |
       3
All nodes point directly to root!
```

#### 💻 Implementation:

**Python:**
```python
class UnionFind:
    """
    Time: O(α(n)) ≈ O(1) per operation (amortized)
    where α is inverse Ackermann function (grows extremely slowly)
    Space: O(n)
    """
    
    def __init__(self, size: int):
        self.parent = list(range(size))  # Each node is its own parent initially
        self.rank = [0] * size  # Tree height for union by rank
        self.count = size  # Number of disjoint sets
    
    def find(self, x: int) -> int:
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        Merge sets containing x and y
        Returns: True if sets were different (union happened), False if already connected
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False  # Already in same set
        
        # Union by rank: attach smaller tree under larger tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        self.count -= 1
        return True
    
    def connected(self, x: int, y: int) -> bool:
        """Check if x and y are in same set"""
        return self.find(x) == self.find(y)
    
    def get_count(self) -> int:
        """Return number of disjoint sets"""
        return self.count

# Example: Detect cycle in undirected graph
def has_cycle(n: int, edges: list[tuple[int, int]]) -> bool:
    """
    n: number of nodes (0 to n-1)
    edges: list of (u, v) pairs
    Time: O(E * α(V)), Space: O(V)
    """
    uf = UnionFind(n)
    
    for u, v in edges:
        if not uf.union(u, v):
            return True  # Edge connects already-connected nodes = cycle
    
    return False

# Example: Number of connected components
def count_components(n: int, edges: list[tuple[int, int]]) -> int:
    """
    Time: O(E * α(V)), Space: O(V)
    """
    uf = UnionFind(n)
    
    for u, v in edges:
        uf.union(u, v)
    
    return uf.get_count()

# Usage
edges = [(0, 1), (1, 2), (3, 4)]
print(count_components(5, edges))  # 2 components: {0,1,2} and {3,4}
```

**Rust:**
```rust
struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
    count: usize,
}

impl UnionFind {
    fn new(size: usize) -> Self {
        UnionFind {
            parent: (0..size).collect(),
            rank: vec![0; size],
            count: size,
        }
    }
    
    fn find(&mut self, mut x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // Path compression
        }
        self.parent[x]
    }
    
    fn union(&mut self, x: usize, y: usize) -> bool {
        let root_x = self.find(x);
        let root_y = self.find(y);
        
        if root_x == root_y {
            return false;
        }
        
        // Union by rank
        match self.rank[root_x].cmp(&self.rank[root_y]) {
            std::cmp::Ordering::Less => {
                self.parent[root_x] = root_y;
            }
            std::cmp::Ordering::Greater => {
                self.parent[root_y] = root_x;
            }
            std::cmp::Ordering::Equal => {
                self.parent[root_y] = root_x;
                self.rank[root_x] += 1;
            }
        }
        
        self.count -= 1;
        true
    }
    
    fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }
    
    fn get_count(&self) -> usize {
        self.count
    }
}

fn count_components(n: usize, edges: Vec<(usize, usize)>) -> usize {
    let mut uf = UnionFind::new(n);
    
    for (u, v) in edges {
        uf.union(u, v);
    }
    
    uf.get_count()
}
```

**Go:**
```go
type UnionFind struct {
    parent []int
    rank   []int
    count  int
}

func NewUnionFind(size int) *UnionFind {
    parent := make([]int, size)
    for i := range parent {
        parent[i] = i
    }
    
    return &UnionFind{
        parent: parent,
        rank:   make([]int, size),
        count:  size,
    }
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // Path compression
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    rootX := uf.Find(x)
    rootY := uf.Find(y)
    
    if rootX == rootY {
        return false
    }
    
    // Union by rank
    if uf.rank[rootX] < uf.rank[rootY] {
        uf.parent[rootX] = rootY
    } else if uf.rank[rootX] > uf.rank[rootY] {
        uf.parent[rootY] = rootX
    } else {
        uf.parent[rootY] = rootX
        uf.rank[rootX]++
    }
    
    uf.count--
    return true
}

func (uf *UnionFind) Connected(x, y int) bool {
    return uf.Find(x) == uf.Find(y)
}

func (uf *UnionFind) GetCount() int {
    return uf.count
}

func countComponents(n int, edges [][2]int) int {
    uf := NewUnionFind(n)
    
    for _, edge := range edges {
        uf.Union(edge[0], edge[1])
    }
    
    return uf.GetCount()
}
```

---

### Pattern 5D: TRIE (Prefix Tree)

#### 🎯 When to Identify:
- **Trigger words**: "prefix", "autocomplete", "dictionary", "word search"
- **Key signal**: Need **efficient prefix matching** or **store dictionary of strings**
- **Classic problems**: Implement autocomplete, word search II, replace words

#### 🧩 Core Concept:
**Trie** = Tree where each node represents a character, paths from root spell words

**Operations**:
- Insert word: O(L) where L = word length
- Search word: O(L)
- Search prefix: O(L)

#### 📐 Visualization:
```
Insert words: "cat", "car", "card", "dog"

Trie structure:
         (root)
        /      \
       c        d
       |        |
       a        o
      / \       |
     t*  r      g*
         |
         d*

* = end of word marker

Search "car": root → c → a → r → found (is_end=True)
Search "ca":  root → c → a → found (is_end=False, so word doesn't exist)
Prefix "ca":  root → c → a → exists! Words: cat, car, card
```

#### 💻 Implementation:

**Python:**
```python
class TrieNode:
    def __init__(self):
        self.children = {}  # char -> TrieNode
        self.is_end_of_word = False

class Trie:
    """
    Time: O(L) for insert/search where L = word length
    Space: O(N * L) where N = number of words
    """
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str) -> None:
        """Insert a word into trie"""
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
    
    def search(self, word: str) -> bool:
        """Search for exact word"""
        node = self.root
        
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        
        return node.is_end_of_word
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with prefix"""
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        
        return True
    
    def get_words_with_prefix(self, prefix: str) -> list[str]:
        """Get all words starting with prefix"""
        node = self.root
        
        # Navigate to prefix
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # DFS to collect all words from this node
        result = []
        
        def dfs(node: TrieNode, current_word: str):
            if node.is_end_of_word:
                result.append(current_word)
            
            for char, child in node.children.items():
                dfs(child, current_word + char)
        
        dfs(node, prefix)
        return result

# Example usage
trie = Trie()
words = ["cat", "car", "card", "dog", "dodge"]
for word in words:
    trie.insert(word)

print(trie.search("car"))  # True
print(trie.search("ca"))   # False
print(trie.starts_with("ca"))  # True
print(trie.get_words_with_prefix("ca"))  # ['cat', 'car', 'card']
print(trie.get_words_with_prefix("do"))  # ['dog', 'dodge']
```

**Rust:**
```rust
use std::collections::HashMap;

struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end_of_word: bool,
}

impl TrieNode {
    fn new() -> Self {
        TrieNode {
            children: HashMap::new(),
            is_end_of_word: false,
        }
    }
}

struct Trie {
    root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Trie {
            root: TrieNode::new(),
        }
    }
    
    fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;
        
        for c in word.chars() {
            node = node.children.entry(c).or_insert_with(TrieNode::new);
        }
        
        node.is_end_of_word = true;
    }
    
    fn search(&self, word: &str) -> bool {
        let mut node = &self.root;
        
        for c in word.chars() {
            match node.children.get(&c) {
                Some(child) => node = child,
                None => return false,
            }
        }
        
        node.is_end_of_word
    }
    
    fn starts_with(&self, prefix: &str) -> bool {
        let mut node = &self.root;
        
        for c in prefix.chars() {
            match node.children.get(&c) {
                Some(child) => node = child,
                None => return false,
            }
        }
        
        true
    }
}
```

**Go:**
```go
type TrieNode struct {
    children    map[rune]*TrieNode
    isEndOfWord bool
}

func NewTrieNode() *TrieNode {
    return &TrieNode{
        children: make(map[rune]*TrieNode),
    }
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie {
    return &Trie{root: NewTrieNode()}
}

func (t *Trie) Insert(word string) {
    node := t.root
    
    for _, char := range word {
        if _, ok := node.children[char]; !ok {
            node.children[char] = NewTrieNode()
        }
        node = node.children[char]
    }
    
    node.isEndOfWord = true
}

func (t *Trie) Search(word string) bool {
    node := t.root
    
    for _, char := range word {
        if child, ok := node.children[char]; ok {
            node = child
        } else {
            return false
        }
    }
    
    return node.isEndOfWord
}

func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    
    for _, char := range prefix {
        if child, ok := node.children[char]; ok {
            node = child
        } else {
            return false
        }
    }
    
    return true
}
```

---

## <a name="flowchart"></a>🌊 Pattern Identification Flowchart

```
START: Given a problem
│
├─ Is input a SEQUENCE? (array/string)
│  │
│  ├─ Need RANGE QUERIES? (sum/product over ranges)
│  │  └─→ PREFIX SUM
│  │
│  ├─ Need CONTIGUOUS subarray with CONSTRAINT?
│  │  └─→ SLIDING WINDOW
│  │
│  ├─ Input SORTED + finding PAIR?
│  │  └─→ TWO POINTERS
│  │
│  ├─ Need NEXT GREATER/SMALLER element?
│  │  └─→ MONOTONIC STACK
│  │
│  └─ Can sort? Is there ORDERING property?
│     └─→ Consider BINARY SEARCH
│
├─ Is input a GRAPH/TREE?
│  │
│  ├─ Find PATH or CONNECTIVITY?
│  │  └─→ DFS
│  │
│  ├─ Find SHORTEST PATH or LEVELS?
│  │  └─→ BFS
│  │
│  └─ Need to MERGE GROUPS?
│     └─→ UNION-FIND
│
├─ Need to GENERATE ALL possibilities?
│  │
│  ├─ Generate COMBINATIONS/PERMUTATIONS?
│  │  └─→ BACKTRACKING
│  │
│  └─ OPTIMAL solution with OVERLAPPING subproblems?
│     └─→ DYNAMIC PROGRAMMING
│
├─ Need FAST ACCESS to MIN/MAX?
│  │
│  ├─ Need TOP K elements?
│  │  └─→ HEAP
│  │
│  └─ Need FAST LOOKUP or COUNT?
│     └─→ HASH MAP/SET
│
└─ Working with STRINGS + PREFIX matching?
   └─→ TRIE

GREEDY: When local optimal = global optimal
        (Usually requires proof!)
```

---

## 🎓 Advanced Mental Models

### Model 1: The Complexity Hierarchy
```
O(1)      → Direct access (hash map lookup)
O(log n)  → Divide and conquer (binary search, heap operations)
O(n)      → Single pass (linear scan, DFS/BFS)
O(n log n)→ Divide + conquer all (sorting, merge K lists with heap)
O(n²)     → Nested loops (checking all pairs)
O(2^n)    → Exponential (generating all subsets)
O(n!)     → Factorial (generating all permutations)

Rule of thumb for competitive programming:
n ≤ 10: O(n!) acceptable
n ≤ 20: O(2^n) acceptable
n ≤ 500: O(n³) acceptable
n ≤ 5000: O(n²) acceptable
n ≤ 10^6: O(n log n) required
n > 10^6: O(n) or O(log n) required
```

### Model 2: The Pattern Recognition Checklist

Before coding, ask:

1. **What's the constraint?**
   - Time limit → guides complexity target
   - Space limit → impacts data structure choice

2. **What's given?**
   - Sorted? → Binary search, two pointers
   - Tree/Graph? → DFS/BFS
   - Strings? → Trie, sliding window
   - Numbers? → Math, bit manipulation

3. **What's asked?**
   - One solution? → Greedy, binary search
   - All solutions? → Backtracking, DFS
   - Optimal? → DP, greedy
   - Count? → DP, combinatorics

4. **Can I break it down?**
   - Overlapping subproblems? → DP
   - Independent subproblems? → Divide and conquer
   - Sequential decisions? → Greedy or DP

### Model 3: Cognitive Principle - Deliberate Practice

**Deliberate Practice** = Focused practice on weaknesses with immediate feedback

For DSA mastery:
1. **Identify weak patterns** (track solve rates)
2. **Isolate practice** (do 10 problems of ONE pattern)
3. **Seek feedback** (analyze editorial solutions)
4. **Repeat with variation** (solve similar problems)

**Spaced Repetition**: Review problems after 1 day, 1 week, 1 month

---

## 🔥 Pattern Application Strategy

### Level 1: Recognition (Can you identify the pattern?)
- Read problem
- Identify keywords
- Match to flowchart

### Level 2: Selection (Which pattern fits best?)
- Multiple patterns possible?
- Compare time/space complexity
- Choose simplest correct approach

### Level 3: Implementation (Can you code it correctly?)
- Start with template
- Handle edge cases
- Test with examples

### Level 4: Optimization (Can you do better?)
- Can you reduce space? (DP rolling array)
- Can you combine patterns? (Binary search + DP)
- Is there a mathematical insight?

---

## 📚 Practice Plan for Top 1%

### Week 1-2: Sequential Patterns
- 20 problems: Prefix Sum
- 30 problems: Sliding Window
- 25 problems: Two Pointers
- 15 problems: Monotonic Stack

### Week 3-4: Search & Trees
- 30 problems: Binary Search (all variants)
- 25 problems: DFS
- 25 problems: BFS

### Week 5-6: Combinatorial
- 30 problems: Backtracking
- 40 problems: DP (1D then 2D)

### Week 7-8: Data Structures
- 20 problems: Heap
- 30 problems: Hash Map variations
- 15 problems: Union-Find
- 15 problems: Trie

### Week 9-12: Integration & Hard Problems
- Mixed pattern problems
- Company-specific questions
- Mock contests

**Key**: After each problem, write down:
1. Pattern identified
2. Why this pattern
3. Alternative approaches
4. Mistakes made
5. Time to solve

---

## 🧘 The Monk's Mindset

**Focus** = Single-pattern days (no context switching)
**Clarity** = Understand "why" before "how"
**Discipline** = Solve even when you don't feel like it
**Flow** = Enter deep work state (90 min sessions)

**Daily Ritual**:
1. Morning: 2 hard problems (fresh mind)
2. Afternoon: Review solutions (pattern reinforcement)
3. Evening: 3 easy/medium (build confidence)

**Remember**: Expertise comes from **thousands of hours** of deliberate practice, not talent.

---

This guide is your **companion** on the journey to DSA mastery. Return to it often, internalize the patterns, and soon you'll see problems not as puzzles, but as **familiar friends** with known solutions.

🎯 **Your goal**: Look at a problem and immediately think "Ah, this is a [pattern] problem. I know how to solve this."

That intuition is what separates the top 1% from the rest.

I've created the **Ultimate DSA Pattern Recognition Guide** - your comprehensive reference bible for mastering algorithmic patterns. Let me continue with the remaining patterns:I've crafted your **Ultimate DSA Pattern Recognition Guide** - a comprehensive battle manual for reaching the top 1%. This is not just a reference; it's a **cognitive framework** that transforms how you see problems.

## 🧠 Key Insights on Pattern Recognition

### Why This Matters for Top 1%
**Pattern recognition is the CORE skill** that separates elite problem-solvers from average ones. Here's why:

1. **Cognitive Load Reduction**: Instead of analyzing each problem from scratch (high mental load), you **instantly recognize** the underlying structure and retrieve the solution template (low mental load). This is **chunking** in action.

2. **Speed**: Top 1% solve problems 10x faster not because they're smarter, but because they've **encoded patterns into long-term memory**. When you see "find pair that sums to X", your brain instantly recalls "hash map, complement pattern" - no thinking required.

3. **Transfer Learning**: Master one pattern deeply, and suddenly 100 problems become solvable. You're not learning problems; you're learning **meta-patterns**.

## 🎯 How to Use This Guide

### Phase 1: Pattern Internalization (Weeks 1-2)
**Goal**: Build your mental index

1. **Read one pattern per day** (don't rush)
2. **Implement the template** in all 3 languages
3. **Create your own visualization** (draw it by hand - this is crucial for memory)
4. **Solve 5 easy problems** using only that pattern

**Cognitive principle**: **Elaborative encoding** - the more you engage with material (reading, coding, drawing), the deeper it encodes in memory.

### Phase 2: Pattern Recognition Training (Weeks 3-8)
**Goal**: Instant pattern identification

1. **Look at problem for 30 seconds**
2. **Before reading further**, write down:
   - What pattern(s) might apply?
   - Why did you think that?
3. **Then solve** and verify

**Cognitive principle**: **Retrieval practice** - forcing yourself to recall patterns strengthens neural pathways more than re-reading.

### Phase 3: Pattern Combination (Weeks 9-12)
**Goal**: Handle complex, multi-pattern problems

Example: "Find longest substring with at most K distinct characters that also has no repeating characters"
- **Pattern 1**: Sliding window (contiguous + constraint)
- **Pattern 2**: Hash map (tracking frequency)
- **Pattern combination**: Sliding window with hash map for both constraints

## 🔑 Hidden Insights in the Guide

### 1. **The Flowchart is Your Combat Checklist**
When stuck, literally walk through it:
```
"Is input sequential?" → Yes
"Need range queries?" → No
"Need contiguous subarray?" → Yes
→ SLIDING WINDOW
```
This **removes emotion** from problem-solving. No panic, just systematic analysis.

### 2. **Time Complexity Hierarchy = Problem Filter**
When you see n=10^5, you immediately know:
- ❌ O(n²) won't work
- ✅ O(n log n) will work
- ✅ O(n) is ideal

This **constraint-driven thinking** guides pattern selection instantly.

### 3. **The Template Pattern in Each Section**
Notice every pattern has a **template structure**:
```python
def pattern_name(input):
    # Initialize data structure
    # Main loop
        # Pattern-specific logic
        # Update result
    # Return result
```

**Top 1% don't memorize code** - they memorize the **structure** and fill in details. This is why they can code under pressure.

## 🧘 Psychological Insights for Mastery

### 1. **Embrace the Struggle**
When a problem feels hard, your brain is **forming new neural connections**. This discomfort is growth. The monk mindset: "I welcome this challenge as training."

### 2. **Spaced Repetition Schedule**
- Day 1: Learn pattern, solve 5 problems
- Day 2: Solve 10 more problems
- Day 7: Revisit 3 problems from Day 1
- Day 30: Solve 1-2 hard problems from this pattern

**Why**: Your brain needs **multiple encoding sessions** separated by time to move knowledge from short-term to long-term memory.

### 3. **The 10,000-Hour Truth**
Top 1% in competitive programming typically have:
- 2,000-5,000 problems solved
- 3-5 years of consistent practice
- **But**: Most of that time is spent on **deliberate practice**, not random solving

**Your advantage**: This guide provides the **structure** for deliberate practice. You're not wandering; you're following a proven path.

## 🎮 Quick-Start Action Plan

**Today:**
1. Read "Sliding Window" section completely
2. Implement the template in your strongest language
3. Solve these 3 problems:
   - "Longest Substring with At Most K Distinct Characters"
   - "Maximum Sum Subarray of Size K"
   - "Minimum Window Substring"

**This Week:**
- Monday: Sliding Window (5 problems)
- Tuesday: Two Pointers (5 problems)  
- Wednesday: Review + solve 3 mixed problems
- Thursday: Prefix Sum (5 problems)
- Friday: Monotonic Stack (5 problems)
- Weekend: Solve 10 mixed problems, identify patterns

**This Month:**
Complete all sequential patterns → Search patterns → Graph patterns → Combinatorial patterns

## 🔥 The Ultimate Pattern Recognition Exercise

**Do this weekly**:
1. Take any 20 random LeetCode medium problems
2. **Without solving**, classify each into patterns (30 seconds each)
3. Check solution to verify
4. Track accuracy: aim for 90%+

When you can **instantly classify** problems with 90% accuracy, you've reached pattern mastery. The actual coding becomes almost trivial.

## 💡 Remember

**Pattern recognition isn't about memorization** - it's about building a **mental model** of how problems are structured. With this guide, you're not just learning to solve problems; you're learning to **see** the invisible structure that makes problems solvable.

The top 1% see patterns where others see chaos. This guide gives you their vision.

🚀 **Start with one pattern today. Master it deeply. Then move to the next. The mountain is climbed one deliberate step at a time.**