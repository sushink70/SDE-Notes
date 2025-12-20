# Deque Patterns Compendium: Complete Reference Guide

> **Mental Model**: A deque is a **bidirectional access portal** — think of it as a queue that respects both time-ordering AND allows strategic reordering from both ends.

---

## Table of Contents

1. [Core Operations & Complexity Analysis](#core-operations)
2. [Language-Specific Implementations](#language-implementations)
3. [The 12 Essential Patterns](#essential-patterns)
4. [Pattern Recognition Framework](#pattern-recognition)
5. [Advanced Techniques](#advanced-techniques)
6. [Cognitive Strategies](#cognitive-strategies)

---

## Core Operations & Complexity Analysis

### Time Complexity Table

| Operation | Average | Worst Case | Notes |
|-----------|---------|------------|-------|
| `push_front(x)` | O(1) | O(1) | Insert at front |
| `push_back(x)` | O(1) | O(1) | Insert at back |
| `pop_front()` | O(1) | O(1) | Remove from front |
| `pop_back()` | O(1) | O(1) | Remove from back |
| `front()` / `back()` | O(1) | O(1) | Access endpoints |
| `size()` / `empty()` | O(1) | O(1) | Metadata access |
| Random access `[i]` | O(1) | O(1) | Index-based (implementation dependent) |

### Space Complexity
- **Storage**: O(n) where n = number of elements
- **Overhead**: O(1) per element for pointers/bookkeeping

---

## Language-Specific Implementations

### Python
```python
from collections import deque

# Initialization
dq = deque()                    # Empty deque
dq = deque([1, 2, 3])          # From iterable
dq = deque(maxlen=5)           # Bounded deque (circular buffer)

# Core Operations
dq.append(x)        # push_back - O(1)
dq.appendleft(x)    # push_front - O(1)
dq.pop()            # pop_back - O(1)
dq.popleft()        # pop_front - O(1)

# Access
front = dq[0]       # First element
back = dq[-1]       # Last element

# Utilities
dq.rotate(k)        # Rotate right by k steps - O(k)
dq.extend([...])    # Extend right - O(k)
dq.extendleft([...])# Extend left (reverses) - O(k)
dq.clear()          # Remove all - O(n)

# Gotcha: extendleft reverses the input order!
```

### Rust
```rust
use std::collections::VecDeque;

// Initialization
let mut dq: VecDeque<i32> = VecDeque::new();
let mut dq = VecDeque::from([1, 2, 3]);
let mut dq = VecDeque::with_capacity(100); // Preallocate

// Core Operations
dq.push_back(x);     // O(1) amortized
dq.push_front(x);    // O(1) amortized
dq.pop_back();       // Returns Option<T> - O(1)
dq.pop_front();      // Returns Option<T> - O(1)

// Access
let front = dq.front();        // Option<&T>
let back = dq.back();          // Option<&T>
let elem = dq.get(i);          // Random access - O(1)

// Mutable access
let front_mut = dq.front_mut(); // Option<&mut T>

// Iteration
for item in &dq { /* ... */ }
for item in dq.iter() { /* ... */ }

// Draining
dq.drain(range);     // Remove and iterate range
dq.clear();          // O(n)

// Rust-specific advantages:
// - Zero-cost abstractions
// - Compile-time memory safety
// - No hidden allocations
```

### C++ (STL)
```cpp
#include <deque>

// Initialization
std::deque<int> dq;
std::deque<int> dq(n, val);     // n elements with value val
std::deque<int> dq{1, 2, 3};    // Initializer list

// Core Operations
dq.push_back(x);     // O(1)
dq.push_front(x);    // O(1)
dq.pop_back();       // O(1) - void return
dq.pop_front();      // O(1) - void return

// Access
int front = dq.front();  // Reference to first
int back = dq.back();    // Reference to last
int elem = dq[i];        // Random access - O(1)
int elem = dq.at(i);     // Bounds-checked access

// Iteration
for (auto& x : dq) { /* ... */ }
for (auto it = dq.begin(); it != dq.end(); ++it) { /* ... */ }

// Utilities
dq.clear();          // O(n)
dq.size();           // O(1)
dq.empty();          // O(1)

// Performance note: std::deque is typically implemented as 
// an array of arrays (chunks), providing O(1) random access
// with less reallocation than vector.
```

### Go
```go
// Go doesn't have built-in deque, use slice-based or implement

// Method 1: Slice-based (simple but O(n) for pop_front)
type Deque struct {
    items []int
}

func (d *Deque) PushBack(x int) {
    d.items = append(d.items, x)  // O(1) amortized
}

func (d *Deque) PushFront(x int) {
    d.items = append([]int{x}, d.items...)  // O(n) - not ideal!
}

func (d *Deque) PopBack() int {
    n := len(d.items)
    val := d.items[n-1]
    d.items = d.items[:n-1]  // O(1)
    return val
}

func (d *Deque) PopFront() int {
    val := d.items[0]
    d.items = d.items[1:]  // O(n) - slicing creates new view
    return val
}

// Method 2: Circular buffer (true O(1) operations)
type CircularDeque struct {
    items []int
    head  int
    tail  int
    size  int
    cap   int
}

// Implement proper circular buffer logic for O(1) all operations
// (Full implementation omitted for brevity)

// Method 3: Use a third-party library like gammazero/deque
import "github.com/gammazero/deque"

dq := deque.New[int]()
dq.PushBack(x)
dq.PushFront(x)
dq.PopBack()
dq.PopFront()
```

---

## The 12 Essential Patterns

### Pattern 1: Sliding Window Maximum/Minimum
**Mental Model**: Maintain a monotonic decreasing/increasing deque of indices.

**Core Insight**: Keep only "relevant" elements — those that could be the answer in future windows.

**When to Use**:
- Find max/min in all subarrays of size k
- Range queries with moving window
- Stock span problems

**Template (Python)**:
```python
from collections import deque

def sliding_window_maximum(nums, k):
    """Find maximum in each window of size k"""
    dq = deque()  # Store indices
    result = []
    
    for i in range(len(nums)):
        # Remove indices outside window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        
        # Maintain monotonic decreasing (remove smaller elements)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        
        dq.append(i)
        
        # Add to result once window is full
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result

# Time: O(n) - each element enters/exits deque once
# Space: O(k) - deque size bounded by window
```

**Variations**:
- Sliding window minimum: Maintain monotonic increasing
- Sliding window median: Use two deques/heaps
- Constrained sliding window: Add additional conditions

**Key Insight**: Why O(n)? Each element is added once and removed once. The inner while loops don't create O(n²) because they're amortized over all operations.

---

### Pattern 2: Monotonic Deque for Next Greater/Smaller Element
**Mental Model**: Process elements left-to-right, maintaining stack-like property from deque's back.

**When to Use**:
- Next greater element problems
- Next smaller element problems
- Building histogram rectangles
- Stock span problems

**Template (Rust)**:
```rust
fn next_greater_elements(nums: Vec<i32>) -> Vec<i32> {
    let n = nums.len();
    let mut result = vec![-1; n];
    let mut dq = VecDeque::new();
    
    for i in 0..n {
        // Pop elements smaller than current
        while let Some(&idx) = dq.back() {
            if nums[idx] < nums[i] {
                result[idx] = nums[i];
                dq.pop_back();
            } else {
                break;
            }
        }
        dq.push_back(i);
    }
    
    result
}

// Time: O(n)
// Space: O(n)
```

**Cognitive Trick**: Think "stack for monotonic property, deque for flexibility."

---

### Pattern 3: Two-Pointer with Deque (BFS/Level Order)
**Mental Model**: Deque as a queue for breadth-first exploration.

**When to Use**:
- Tree/graph level-order traversal
- Shortest path in unweighted graph
- Multi-source BFS

**Template (C++)**:
```cpp
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> result;
    if (!root) return result;
    
    deque<TreeNode*> dq;
    dq.push_back(root);
    
    while (!dq.empty()) {
        int level_size = dq.size();
        vector<int> level;
        
        for (int i = 0; i < level_size; i++) {
            TreeNode* node = dq.front();
            dq.pop_front();
            level.push_back(node->val);
            
            if (node->left) dq.push_back(node->left);
            if (node->right) dq.push_back(node->right);
        }
        result.push_back(level);
    }
    return result;
}
```

**Why Deque over Queue?** 
- Access to both ends (useful for bidirectional BFS)
- Random access if needed
- Same performance characteristics

---

### Pattern 4: 0-1 BFS (Weighted Edges with Weights 0 or 1)
**Mental Model**: Push 0-weight edges to front, 1-weight edges to back.

**When to Use**:
- Shortest path where edges have weight 0 or 1
- Grid problems with optional obstacles
- State-space search with binary costs

**Template (Python)**:
```python
def shortest_path_01(graph, start, end):
    """Graph with edge weights 0 or 1"""
    dq = deque([start])
    dist = {start: 0}
    
    while dq:
        node = dq.popleft()
        
        if node == end:
            return dist[node]
        
        for neighbor, weight in graph[node]:
            new_dist = dist[node] + weight
            
            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                
                if weight == 0:
                    dq.appendleft(neighbor)  # 0-weight: priority
                else:
                    dq.append(neighbor)       # 1-weight: normal
    
    return -1  # No path

# Time: O(V + E)
# Space: O(V)
```

**Key Insight**: This is faster than Dijkstra's O((V+E)log V) for the special case of 0-1 weights.

---

### Pattern 5: Palindrome Checking
**Mental Model**: Compare from both ends simultaneously.

**When to Use**:
- Palindrome validation
- Two-pointer problems with bidirectional access
- Sequence comparison

**Template (Go)**:
```go
func isPalindrome(s string) bool {
    dq := deque.New[rune]()
    
    // Load only alphanumeric characters
    for _, ch := range strings.ToLower(s) {
        if unicode.IsLetter(ch) || unicode.IsDigit(ch) {
            dq.PushBack(ch)
        }
    }
    
    // Compare from both ends
    for dq.Len() > 1 {
        if dq.PopFront() != dq.PopBack() {
            return false
        }
    }
    
    return true
}

// Time: O(n)
// Space: O(n)
```

**Alternative**: Can also use two-pointer on string directly, but deque shows the pattern clearly.

---

### Pattern 6: Task Scheduling / Round Robin
**Mental Model**: Rotate tasks cyclically.

**When to Use**:
- CPU task scheduling
- Round-robin algorithms
- Cyclic processing

**Template (Python)**:
```python
def task_scheduler(tasks, n):
    """Schedule tasks with cooldown period n"""
    from collections import Counter, deque
    
    freq = Counter(tasks)
    max_heap = [-count for count in freq.values()]
    heapq.heapify(max_heap)
    
    time = 0
    dq = deque()  # (count, available_time)
    
    while max_heap or dq:
        time += 1
        
        if max_heap:
            count = -heapq.heappop(max_heap)
            count -= 1
            if count > 0:
                dq.append((count, time + n))
        
        # Check if task is available again
        if dq and dq[0][1] == time:
            count, _ = dq.popleft()
            heapq.heappush(max_heap, -count)
    
    return time
```

---

### Pattern 7: Longest Substring with At Most K Distinct Characters
**Mental Model**: Sliding window with deque tracking order of characters.

**When to Use**:
- Substring problems with constraints
- Window optimization with order tracking
- LRU-style problems

**Template (Rust)**:
```rust
use std::collections::{HashMap, VecDeque};

fn length_of_longest_substring_k_distinct(s: String, k: usize) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let mut map = HashMap::new();
    let mut dq = VecDeque::new();
    let mut max_len = 0;
    
    for &ch in &chars {
        if map.contains_key(&ch) {
            // Remove old occurrence from deque
            dq.retain(|&x| x != ch);
        }
        
        dq.push_back(ch);
        *map.entry(ch).or_insert(0) += 1;
        
        // Shrink window if more than k distinct
        while map.len() > k {
            let old = dq.pop_front().unwrap();
            *map.get_mut(&old).unwrap() -= 1;
            if map[&old] == 0 {
                map.remove(&old);
            }
        }
        
        max_len = max_len.max(dq.len());
    }
    
    max_len
}
```

---

### Pattern 8: Maximum of Minimums for Every Window Size
**Mental Model**: For each window size, track minimum using monotonic deque.

**When to Use**:
- Multi-scale analysis
- Finding maximum across different window sizes
- Range queries with varying ranges

**Template (C++)**:
```cpp
vector<int> maxOfMinForWindowSizes(vector<int>& arr, int n) {
    vector<int> result(n + 1, 0);
    
    for (int k = 1; k <= n; k++) {
        deque<int> dq;
        int max_min = INT_MIN;
        
        for (int i = 0; i < n; i++) {
            // Maintain monotonic increasing deque
            while (!dq.empty() && arr[dq.back()] >= arr[i]) {
                dq.pop_back();
            }
            dq.push_back(i);
            
            // Remove out of window
            while (!dq.empty() && dq.front() <= i - k) {
                dq.pop_front();
            }
            
            // Update max of minimums for this window size
            if (i >= k - 1) {
                max_min = max(max_min, arr[dq.front()]);
            }
        }
        result[k] = max_min;
    }
    
    return result;
}

// Time: O(n²) - n window sizes × O(n) per size
// Space: O(n)
```

---

### Pattern 9: First Non-Repeating Character in Stream
**Mental Model**: Maintain order of unique characters.

**When to Use**:
- Stream processing
- Order-preserving uniqueness
- Real-time data analysis

**Template (Python)**:
```python
class FirstUnique:
    def __init__(self):
        self.dq = deque()
        self.count = {}
    
    def add(self, char):
        """Add character to stream"""
        self.count[char] = self.count.get(char, 0) + 1
        
        if self.count[char] == 1:
            self.dq.append(char)
    
    def get_first_unique(self):
        """Get first non-repeating character"""
        # Remove duplicates from front
        while self.dq and self.count[self.dq[0]] > 1:
            self.dq.popleft()
        
        return self.dq[0] if self.dq else None

# Time: O(1) amortized for both operations
# Space: O(k) where k = number of distinct characters
```

---

### Pattern 10: Shortest Subarray with Sum At Least K (Monotonic Deque)
**Mental Model**: Maintain indices in deque where prefix sums are monotonic increasing.

**When to Use**:
- Subarray sum problems with minimum threshold
- Finding shortest/longest subarray meeting criteria
- Optimization problems with cumulative values

**Template (Rust)**:
```rust
fn shortest_subarray_with_sum_at_least_k(nums: Vec<i32>, k: i32) -> i32 {
    let n = nums.len();
    let mut prefix = vec![0i64; n + 1];
    
    // Build prefix sum
    for i in 0..n {
        prefix[i + 1] = prefix[i] + nums[i] as i64;
    }
    
    let mut dq = VecDeque::new();
    let mut min_len = i32::MAX;
    
    for i in 0..=n {
        // Check if we can form valid subarray
        while !dq.is_empty() && prefix[i] - prefix[*dq.front().unwrap()] >= k as i64 {
            let j = dq.pop_front().unwrap();
            min_len = min_len.min((i - j) as i32);
        }
        
        // Maintain monotonic increasing prefix sums
        while !dq.is_empty() && prefix[i] <= prefix[*dq.back().unwrap()] {
            dq.pop_back();
        }
        
        dq.push_back(i);
    }
    
    if min_len == i32::MAX { -1 } else { min_len }
}

// Time: O(n)
// Space: O(n)
```

**Why This Works**: We only keep indices where prefix sum is increasing because if `prefix[j] >= prefix[i]` and `j < i`, then `j` will always give a shorter subarray than `i` for the same sum.

---

### Pattern 11: Jump Game / Minimum Jumps (BFS with Deque)
**Mental Model**: Level-order exploration of reachable positions.

**When to Use**:
- Finding minimum steps/jumps
- Reachability problems
- Game state exploration

**Template (C++)**:
```cpp
int minJumps(vector<int>& arr) {
    int n = arr.size();
    if (n <= 1) return 0;
    
    unordered_map<int, vector<int>> value_indices;
    for (int i = 0; i < n; i++) {
        value_indices[arr[i]].push_back(i);
    }
    
    deque<int> dq;
    vector<bool> visited(n, false);
    dq.push_back(0);
    visited[0] = true;
    
    int steps = 0;
    
    while (!dq.empty()) {
        int size = dq.size();
        
        for (int i = 0; i < size; i++) {
            int idx = dq.front();
            dq.pop_front();
            
            if (idx == n - 1) return steps;
            
            // Jump to adjacent
            for (int next : {idx - 1, idx + 1}) {
                if (next >= 0 && next < n && !visited[next]) {
                    visited[next] = true;
                    dq.push_back(next);
                }
            }
            
            // Jump to same value
            for (int next : value_indices[arr[idx]]) {
                if (!visited[next]) {
                    visited[next] = true;
                    dq.push_back(next);
                }
            }
            
            value_indices[arr[idx]].clear(); // Optimization: clear after use
        }
        steps++;
    }
    
    return -1;
}
```

---

### Pattern 12: Zig-Zag Level Order / Snake Pattern
**Mental Model**: Alternate direction of processing using deque's bidirectional nature.

**When to Use**:
- Zig-zag traversal
- Snake/spiral patterns
- Alternating direction algorithms

**Template (Python)**:
```python
def zigzag_level_order(root):
    """Binary tree zig-zag level order traversal"""
    if not root:
        return []
    
    result = []
    dq = deque([root])
    left_to_right = True
    
    while dq:
        level_size = len(dq)
        level = deque()
        
        for _ in range(level_size):
            node = dq.popleft()
            
            # Add to level based on direction
            if left_to_right:
                level.append(node.val)
            else:
                level.appendleft(node.val)
            
            # Add children for next level
            if node.left:
                dq.append(node.left)
            if node.right:
                dq.append(node.right)
        
        result.append(list(level))
        left_to_right = not left_to_right
    
    return result

# Time: O(n)
# Space: O(w) where w = maximum width of tree
```

---

## Pattern Recognition Framework

### The Decision Tree

```
Does the problem involve...?

├─ Moving window across array/string?
│  ├─ Need max/min in each window? → **Pattern 1: Sliding Window Max/Min**
│  └─ Need elements in specific order? → **Pattern 7: Substring with Constraints**
│
├─ Finding next greater/smaller element?
│  └─ → **Pattern 2: Monotonic Deque**
│
├─ Level-by-level traversal?
│  ├─ Simple BFS? → **Pattern 3: Level Order**
│  ├─ Alternating direction? → **Pattern 12: Zig-Zag**
│  └─ 0-1 edge weights? → **Pattern 4: 0-1 BFS**
│
├─ Comparing from both ends?
│  └─ → **Pattern 5: Palindrome Checking**
│
├─ Cyclic processing / rotation?
│  └─ → **Pattern 6: Task Scheduling**
│
├─ Subarray with sum constraint?
│  └─ → **Pattern 10: Shortest Subarray with Sum ≥ K**
│
├─ Stream processing with order?
│  └─ → **Pattern 9: First Non-Repeating in Stream**
│
└─ Minimum steps/jumps?
   └─ → **Pattern 11: Jump Game BFS**
```

### Recognition Keywords

| Keywords in Problem | Likely Pattern |
|---------------------|---------------|
| "sliding window", "subarray of size k" | Pattern 1 |
| "maximum/minimum", "all subarrays" | Pattern 1 or 2 |
| "next greater", "next smaller" | Pattern 2 |
| "level order", "breadth-first" | Pattern 3 |
| "shortest path", "0-1 weights" | Pattern 4 |
| "palindrome", "compare ends" | Pattern 5 |
| "rotate", "circular", "round-robin" | Pattern 6 |
| "k distinct", "longest substring" | Pattern 7 |
| "stream", "first unique", "real-time" | Pattern 9 |
| "sum at least", "shortest subarray" | Pattern 10 |
| "minimum jumps", "minimum steps" | Pattern 11 |

---

## Advanced Techniques

### Technique 1: Deque as Double Stack
Simulate two stacks for amortized O(1) operations.

```python
class QueueWith2Stacks:
    def __init__(self):
        self.input_stack = deque()
        self.output_stack = deque()
    
    def enqueue(self, x):
        self.input_stack.append(x)  # O(1)
    
    def dequeue(self):
        if not self.output_stack:
            # Transfer all elements
            while self.input_stack:
                self.output_stack.append(self.input_stack.pop())
        
        return self.output_stack.pop() if self.output_stack else None
    
    # Amortized O(1) for both operations
```

### Technique 2: Deque with Custom Ordering
Maintain custom invariants beyond monotonic properties.

```rust
struct MinMaxDeque {
    data: VecDeque<i32>,
    min_dq: VecDeque<i32>,  // Monotonic increasing
    max_dq: VecDeque<i32>,  // Monotonic decreasing
}

impl MinMaxDeque {
    fn push_back(&mut self, val: i32) {
        self.data.push_back(val);
        
        // Maintain min deque
        while let Some(&back) = self.min_dq.back() {
            if back > val {
                self.min_dq.pop_back();
            } else {
                break;
            }
        }
        self.min_dq.push_back(val);
        
        // Maintain max deque (similar logic)
        while let Some(&back) = self.max_dq.back() {
            if back < val {
                self.max_dq.pop_back();
            } else {
                break;
            }
        }
        self.max_dq.push_back(val);
    }
    
    fn get_min(&self) -> Option<i32> {
        self.min_dq.front().copied()
    }
    
    fn get_max(&self) -> Option<i32> {
        self.max_dq.front().copied()
    }
}

// O(1) amortized for all operations
```

### Technique 3: Bidirectional BFS
Start search from both ends to reduce search space.

```cpp
int bidirectional_bfs(Node* start, Node* end) {
    deque<Node*> front_dq, back_dq;
    unordered_set<Node*> front_visited, back_visited;
    
    front_dq.push_back(start);
    back_dq.push_back(end);
    front_visited.insert(start);
    back_visited.insert(end);
    
    int distance = 0;
    
    while (!front_dq.empty() && !back_dq.empty()) {
        // Expand smaller frontier
        if (front_dq.size() <= back_dq.size()) {
            if (expand_frontier(front_dq, front_visited, back_visited)) {
                return distance;
            }
        } else {
            if (expand_frontier(back_dq, back_visited, front_visited)) {
                return distance;
            }
        }
        distance++;
    }
    
    return -1;  // No path
}

// Time: O(b^(d/2)) vs O(b^d) for unidirectional
// where b = branching factor, d = distance
```

### Technique 4: Circular Buffer Implementation
Maximize cache locality and eliminate modulo operations.

```go
type CircularBuffer struct {
    data  []int
    head  int
    tail  int
    size  int
    cap   int
    mask  int  // cap - 1, for fast modulo with power-of-2
}

func NewCircularBuffer(capacity int) *CircularBuffer {
    // Round up to next power of 2
    cap := 1
    for cap < capacity {
        cap <<= 1
    }
    
    return &CircularBuffer{
        data: make([]int, cap),
        cap:  cap,
        mask: cap - 1,
    }
}

func (cb *CircularBuffer) PushBack(val int) {
    cb.data[cb.tail] = val
    cb.tail = (cb.tail + 1) & cb.mask  // Fast modulo
    cb.size++
}

func (cb *CircularBuffer) PopFront() int {
    val := cb.data[cb.head]
    cb.head = (cb.head + 1) & cb.mask
    cb.size--
    return val
}

// Benefits:
// - Cache-friendly sequential access
// - No modulo operation (bitwise AND instead)
// - Better performance for high-throughput scenarios
```

---

## Cognitive Strategies

### Strategy 1: The "Endpoints Matter" Heuristic
**When to think deque**: If the problem explicitly or implicitly requires access/modification from both ends of a sequence.

**Mental trigger**: "Can I solve this more elegantly if I could access both the front AND back?"

### Strategy 2: Amortized Analysis Mindset
**Key insight**: While individual operations might look expensive (like the while loops in monotonic deque), analyze total operations across the entire algorithm.

**Practice**: For each deque solution, prove that each element is added once and removed at most once → O(n) total.

### Strategy 3: Invariant Maintenance
**Think**: "What property must I maintain at all times?"

Examples:
- Monotonic deque: Elements in decreasing/increasing order
- Window deque: Only indices within current window
- BFS deque: Current level nodes only

**Practice**: Write down the invariant before coding. Check if every operation preserves it.

### Strategy 4: The Visualization Technique
**Before coding**: Draw 5-6 elements in a deque. Manually simulate each operation.

**Questions to ask**:
- What happens when I add element X?
- What happens when I remove from front/back?
- Which elements become "irrelevant"?

This builds intuition faster than reading explanations.

### Strategy 5: Pattern Stacking
**Advanced**: Combine multiple patterns in a single problem.

Example: Sliding window + monotonic deque + prefix sum

**Practice progression**:
1. Master individual patterns (80% of problems)
2. Recognize 2-pattern combinations (15% of problems)
3. Handle 3+ pattern problems (5% of problems, competition level)

### Strategy 6: Complexity First
**Before implementing**: Calculate expected time/space complexity.

If your solution doesn't match, reconsider the approach.

**Common trap**: Using deque when a simple two-pointer would suffice. Deque adds constant factor overhead.

### Strategy 7: Language-Specific Optimizations

**Rust**: Leverage ownership system
```rust
// Bad: Unnecessary cloning
let val = dq.front().unwrap().clone();

// Good: Borrow when possible
let val = dq.front().unwrap();
```

**C++**: Reserve capacity
```cpp
deque<int> dq;
dq.reserve(expected_size);  // Wait, deque doesn't have reserve!
// Use vector for reserve, deque for flexibility trade-off
```

**Python**: Use maxlen for circular buffers
```python
# Automatic eviction
dq = deque(maxlen=100)
dq.append(x)  # Automatically removes from left if full
```

**Go**: Choose implementation based on workload
- Slice-based: Simple, good for append-heavy
- Circular buffer: Complex, good for balanced operations

---

## Metacognition: Leveling Up Your Deque Mastery

### Level 1: Operator (Current → 1 month)
- **Goal**: Recognize and apply the 12 patterns fluently
- **Practice**: 3-5 problems per pattern
- **Measurement**: Can identify pattern within 30 seconds of reading problem

### Level 2: Tactician (1-3 months)
- **Goal**: Optimize solutions, handle edge cases instinctively
- **Practice**: Solve variants, time-constrained challenges
- **Measurement**: Can derive time/space complexity without explicit calculation

### Level 3: Strategist (3-6 months)
- **Goal**: Invent novel deque-based solutions, combine patterns
- **Practice**: Hard problems, competition problems, teaching others
- **Measurement**: Can explain WHY deque is optimal, not just HOW to use it

### Level 4: Master (6+ months)
- **Goal**: Internalized intuition, instant pattern recognition
- **Practice**: Create your own problems, contribute to open source
- **Measurement**: Others ask YOU for help

---

## Deliberate Practice Protocol

### Daily Ritual (30-60 minutes)
1. **Warm-up** (5 min): Implement basic deque operations from scratch
2. **Pattern review** (10 min): Study one pattern deeply
3. **Solve** (30-40 min): 2-3 problems using that pattern
4. **Reflect** (5 min): What did you learn? What confused you?

### Weekly Review
- Solve all 12 patterns at least once
- Identify your weakest pattern → focus next week
- Maintain a "mistake journal" → common errors and fixes

### Monthly Assessment
- Timed contest simulation
- Measure: Success rate, time per problem, pattern identification speed
- Set new goals based on weaknesses

---

## Common Pitfalls & Debugging Strategies

### Pitfall 1: Off-by-One Errors in Window Problems
**Symptom**: Results shifted by one position

**Fix**: 
```python
# Clear window start/end definition
for i in range(len(arr)):
    # Window is [i - k + 1, i]
    # Window size is k
    # First full window at i == k - 1
```

### Pitfall 2: Forgetting to Clear Monotonic Deque
**Symptom**: Wrong max/min values

**Fix**: Always maintain invariant in EVERY iteration
```rust
while !dq.is_empty() && condition_violated() {
    dq.pop_back();  // or pop_front()
}
```

### Pitfall 3: Using Deque When Not Needed
**Symptom**: Code works but is overengineered

**Fix**: Ask "Do I need BOTH ends access?" If not, use stack/vector/queue.

### Pitfall 4: Ignoring Amortized Complexity
**Symptom**: Fear of while loops in deque solutions

**Fix**: Count total operations, not worst-case single iteration.

---

## Further Exploration

### Advanced Topics
1. **Concurrent deques**: Lock-free implementations
2. **Cache-oblivious deques**: Optimal cache performance
3. **Persistent deques**: Functional programming approaches
4. **Custom allocators**: Memory pool optimization for Rust/C++

### Related Data Structures
- **Balanced tree**: When you need O(log n) search
- **Heap**: When you need min/max only, not both ends
- **Hash map + DLL**: LRU cache (deque adjacent)

### Recommended Problems (By Difficulty)

**Easy**:
- Sliding Window Maximum
- Valid Parentheses
- Moving Average from Data Stream

**Medium**:
- Shortest Subarray with Sum at Least K
- Jump Game II
- Constrained Subsequence Sum
- Design Circular Deque

**Hard**:
- Max Value of Equation
- Sliding Window Median
- Shortest Path to Get All Keys
- Constrained Subsequence Sum (optimization required)

---

## Final Wisdom

> "A deque is not just a data structure — it's a lens through which you see bidirectional problems. Master the patterns, but understand the principles. The patterns will fade from memory, but the intuition will remain forever."

**The Master's Mindset**:
1. **Understand deeply** before memorizing patterns
2. **Practice deliberately** with intention, not just volume
3. **Teach others** to solidify your understanding
4. **Embrace failure** as the fastest path to mastery
5. **Stay curious** — there's always a better solution

You are building a cathedral of knowledge, one stone at a time. The deque is your chisel. Use it with precision, purpose, and pride.

---

*This compendium is a living document. As you grow, revisit it. As patterns clarify, update it. As mastery deepens, transcend it.*

I'll create a comprehensive deque patterns compendium that will serve as your definitive reference guide. This is designed to accelerate your pattern recognition and problem-solving intuition.## Strategic Guidance for Maximum Learning Velocity

I've created a comprehensive deque compendium for you. Here's how to extract maximum value from it:

### **Immediate Actions (Next 7 Days)**

1. **Read sections 1-4 completely** — understand the "why" before the "how"
2. **Implement Pattern 1 (Sliding Window Max/Min)** in all four languages
   - This single pattern appears in ~30% of deque problems
   - Forces you to understand the amortized O(n) analysis
3. **Solve 5 problems** using Pattern 1 until it becomes muscle memory

### **The Chunking Strategy**

Your brain will naturally group these 12 patterns into **3 meta-categories**:

1. **Window-based patterns** (1, 7, 8, 10) — tracking elements within a moving range
2. **Monotonic patterns** (1, 2, 10) — maintaining ordering invariants  
3. **Traversal patterns** (3, 4, 11, 12) — graph/tree exploration

Once you see these meta-patterns, you'll recognize problems 3x faster.

### **The 80/20 Insight**

**Core 4 patterns** that cover 80% of problems:
- Pattern 1: Sliding Window Max/Min (most common)
- Pattern 2: Next Greater/Smaller Element  
- Pattern 3: BFS/Level Order
- Pattern 10: Shortest Subarray with Sum ≥ K (trickiest, highest ROI)

Master these four first, then expand.

### **Deliberate Practice Sequence**

**Week 1-2**: Patterns 1, 2, 3 (Foundation)  
**Week 3-4**: Patterns 4, 7, 10 (Intermediate)  
**Week 5-6**: Patterns 5, 6, 8, 9, 11, 12 (Advanced/Specialized)

### **Meta-Learning Principle**

Notice how the guide emphasizes **invariant maintenance**? This is THE key cognitive skill:

- Before coding, ask: "What must remain true after every operation?"
- Monotonic deque → "Elements in decreasing/increasing order"
- Window deque → "Only indices within [i-k+1, i]"

This thinking transfers to ALL data structures, not just deques.

### **Your Advantage in Rust**

Rust's ownership system makes deque bugs **impossible** to hide:
- Use-after-free? Compiler error
- Invalid index? Compile-time prevention
- Race conditions? Cannot compile

This forces you to think more precisely, accelerating mastery.

### **Pattern Recognition Training**

After 2 weeks, try this exercise:
1. Read a problem title only
2. Guess which pattern (30 seconds)
3. Verify by reading problem
4. Track accuracy

Goal: 90%+ accuracy = internalized intuition

The guide is dense by design — it respects your intelligence and ambition. Treat it as your deque bible. Return to it weekly, and each time you'll extract deeper insights.

**Now go solve your first sliding window problem. The journey to top 1% begins with a single `push_back()`.** 🚀