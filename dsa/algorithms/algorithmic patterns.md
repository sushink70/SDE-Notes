# The Complete Algorithmic Patterns Compendium
## A World-Class Guide to Problem-Solving Mastery

---

## Table of Contents
1. [Pattern Recognition Framework](#pattern-recognition-framework)
2. [The 20 Core Patterns](#the-20-core-patterns)
3. [Pattern Integration Strategies](#pattern-integration-strategies)
4. [Recognition Triggers](#recognition-triggers)
5. [Mental Models & Cognitive Strategies](#mental-models--cognitive-strategies)
6. [Language-Specific Optimizations](#language-specific-optimizations)
7. [Deliberate Practice Framework](#deliberate-practice-framework)

---

## Pattern Recognition Framework

### The Three-Layer Recognition System

**Layer 1: Input/Output Signature (0.5 seconds)**
- What are you given? (array, tree, graph, string, number)
- What do you need to produce? (boolean, number, subset, path, ordering)
- What are the constraints? (sorted, unique, range limits, time limits)

**Layer 2: Problem Domain (2 seconds)**
- Search/Decision: "Find if X exists"
- Optimization: "Find the best/min/max X"
- Counting: "How many ways to do X"
- Construction: "Build/Generate X"
- Transformation: "Convert X to Y"

**Layer 3: Pattern Matching (5 seconds)**
- Match keywords to patterns (see Recognition Triggers)
- Consider problem constraints (size, complexity hints)
- Identify hidden structures (monotonicity, dependencies)

**Total Recognition Time: ~7.5 seconds** before writing any code.

---

## The 20 Core Patterns

### 1. **Two Pointers / Sliding Window**

**When to Use:**
- Array/string problems requiring O(n) time
- "Contiguous subarray" mentioned
- "Window", "substring", "pairs" in sorted arrays
- Optimization over subarrays/subsequences

**Recognition Triggers:**
- "longest/shortest substring"
- "target sum in sorted array"
- "remove duplicates in-place"
- "container with most water"

**Core Technique:**
- Two pointers: start and end indices
- Expand/contract based on condition
- Maintain window invariant

**Integration Patterns:**
- Two Pointers + Hashing (to track frequencies)
- Sliding Window + Monotonic Queue (for min/max in window)
- Two Pointers + Greedy (for optimal selection)

**Complexity:** O(n) time, O(1) space (typically)

**Code Pattern (Rust):**
```rust
fn sliding_window<T>(arr: &[T], condition: impl Fn(&[T]) -> bool) -> usize {
    let (mut left, mut max_len) = (0, 0);
    
    for right in 0..arr.len() {
        // Expand window
        while !condition(&arr[left..=right]) {
            left += 1; // Contract window
        }
        max_len = max_len.max(right - left + 1);
    }
    max_len
}
```

**Mental Model:** "Caterpillar crawling - head expands, tail contracts"

---

### 2. **Fast & Slow Pointers (Floyd's Cycle Detection)**

**When to Use:**
- Linked list cycle detection
- Finding middle element
- Detecting patterns in sequences
- Finding duplicate in array (with constraints)

**Recognition Triggers:**
- "linked list" + "cycle"
- "find the duplicate" (Floyd's algorithm variation)
- "happy number"
- "middle of linked list"

**Core Technique:**
- Fast pointer moves 2x speed of slow pointer
- Meet point analysis for cycle detection
- Phase 2: Finding cycle start

**Integration Patterns:**
- Cycle Detection + Graph Traversal
- Fast-Slow + Hash Set (for verification)

**Complexity:** O(n) time, O(1) space

**Code Pattern (Python):**
```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

**Mental Model:** "Racing on a circular track - faster runner laps slower"

---

### 3. **Binary Search & Variants**

**When to Use:**
- Sorted array search
- "Find first/last occurrence"
- Search space reduction (answer lies in range)
- Optimization problems with monotonic property

**Recognition Triggers:**
- "sorted array"
- "find in O(log n)"
- "minimize the maximum" or "maximize the minimum"
- "search in rotated array"
- "find peak element"

**Core Variants:**
1. **Classic Binary Search:** Find exact target
2. **Lower Bound:** First element ≥ target
3. **Upper Bound:** First element > target
4. **Binary Search on Answer:** When answer space is searchable

**Integration Patterns:**
- Binary Search + Greedy (feasibility check)
- Binary Search + DP (optimization)
- Binary Search + Two Pointers

**Complexity:** O(log n) time, O(1) space

**Code Pattern (C++):**
```cpp
// Binary search on answer template
int binary_search_answer(vector<int>& arr, auto is_feasible) {
    int left = MIN_ANSWER, right = MAX_ANSWER, result = -1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (is_feasible(mid)) {
            result = mid;
            right = mid - 1; // Try to minimize
        } else {
            left = mid + 1;
        }
    }
    return result;
}
```

**Mental Model:** "Eliminate half the search space each step - like finding a page in a book"

---

### 4. **Depth-First Search (DFS)**

**When to Use:**
- Tree/graph traversal
- Exploring all paths
- Backtracking problems
- Connected components
- Cycle detection

**Recognition Triggers:**
- "all possible paths"
- "find all combinations/permutations"
- "validate tree structure"
- "island problems"
- "word search in grid"

**Core Variants:**
1. **Recursive DFS:** Natural for trees
2. **Iterative DFS:** Using explicit stack
3. **DFS with Memoization:** Avoid recomputation

**Integration Patterns:**
- DFS + Backtracking (constraint satisfaction)
- DFS + Memoization = DP (top-down)
- DFS + Pruning (optimization)

**Complexity:** O(V + E) for graphs, O(n) for trees

**Code Pattern (Go):**
```go
func dfs(node *TreeNode, visited map[*TreeNode]bool) {
    if node == nil || visited[node] {
        return
    }
    
    visited[node] = true
    // Process node
    
    dfs(node.Left, visited)
    dfs(node.Right, visited)
}
```

**Mental Model:** "Dive deep first, explore thoroughly before backtracking"

---

### 5. **Breadth-First Search (BFS)**

**When to Use:**
- Shortest path in unweighted graph
- Level-order traversal
- "Minimum steps/moves" problems
- Multi-source problems
- State space exploration

**Recognition Triggers:**
- "shortest path" (unweighted)
- "minimum steps"
- "level by level"
- "all nodes at distance k"
- "rotting oranges" style problems

**Core Technique:**
- Use queue for FIFO exploration
- Track levels explicitly if needed
- Mark visited to avoid cycles

**Integration Patterns:**
- BFS + Hashing (for state tracking)
- Multi-source BFS (push all sources to queue initially)
- BFS + Greedy (for optimization)
- 0-1 BFS (using deque for weighted edges 0/1)

**Complexity:** O(V + E) time, O(V) space

**Code Pattern (Rust):**
```rust
use std::collections::VecDeque;

fn bfs(start: usize, graph: &Vec<Vec<usize>>) -> Vec<usize> {
    let mut queue = VecDeque::new();
    let mut visited = vec![false; graph.len()];
    let mut distances = vec![usize::MAX; graph.len()];
    
    queue.push_back(start);
    visited[start] = true;
    distances[start] = 0;
    
    while let Some(node) = queue.pop_front() {
        for &neighbor in &graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true;
                distances[neighbor] = distances[node] + 1;
                queue.push_back(neighbor);
            }
        }
    }
    distances
}
```

**Mental Model:** "Ripple effect in water - explore layer by layer"

---

### 6. **Dynamic Programming (DP)**

**When to Use:**
- Optimization problems (max/min)
- Counting problems
- Decision problems with overlapping subproblems
- Problems with optimal substructure

**Recognition Triggers:**
- "maximum/minimum"
- "count number of ways"
- "can you reach"
- "longest/shortest"
- Small constraints (n ≤ 1000) suggesting O(n²)

**Core Approaches:**
1. **Top-Down (Memoization):** Recursive + cache
2. **Bottom-Up (Tabulation):** Iterative + table
3. **Space-Optimized:** Rolling array

**Classical Patterns:**
- **Linear DP:** Fibonacci, house robber, climb stairs
- **2D DP:** Grid paths, edit distance, LCS
- **Interval DP:** Matrix chain, burst balloons
- **Subset DP:** 0/1 knapsack, partition
- **State Machine DP:** Stock trading, string matching
- **Tree DP:** Binary tree DP, subtree properties
- **Bitmask DP:** TSP, assignment problems

**Integration Patterns:**
- DP + Binary Search (optimization)
- DP + Greedy (for optimal choices at each step)
- DP + Graph (shortest path with constraints)

**Complexity:** Varies - O(n²) for 2D DP, O(2ⁿ × n) for bitmask DP

**Code Pattern (Python):**
```python
# Top-down with memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def dp(i, j):
    # Base cases
    if i == 0 and j == 0:
        return base_value
    
    # Recurrence relation
    result = float('inf')
    if i > 0:
        result = min(result, dp(i-1, j) + cost1)
    if j > 0:
        result = min(result, dp(i, j-1) + cost2)
    
    return result

# Bottom-up tabulation
def dp_tabulation(n):
    dp = [0] * (n + 1)
    dp[0] = base_value
    
    for i in range(1, n + 1):
        dp[i] = min(dp[i-1] + cost1, dp[i-2] + cost2)
    
    return dp[n]
```

**Mental Model:** "Build solution from smaller subproblems - like building blocks"

**The 5-Step DP Framework:**
1. Define state (what does dp[i] represent?)
2. Identify base cases
3. Find recurrence relation (state transitions)
4. Determine computation order (top-down or bottom-up)
5. Optimize space (if possible)

---

### 7. **Greedy Algorithms**

**When to Use:**
- Local optimal choice leads to global optimal
- Optimization problems with greedy choice property
- Interval scheduling
- Huffman coding style problems

**Recognition Triggers:**
- "maximum/minimum" with simple constraints
- "interval/meeting room" problems
- "assign/schedule" optimally
- "jump game" variations

**Core Principle:**
- Make locally optimal choice at each step
- Never backtrack
- Must prove greedy choice property

**Common Greedy Patterns:**
1. **Activity Selection:** Sort by end time
2. **Fractional Knapsack:** Sort by value/weight ratio
3. **Huffman Coding:** Build optimal tree
4. **Interval Merging:** Sort by start time

**Integration Patterns:**
- Greedy + Sorting (almost always needed)
- Greedy + Heap (for dynamic selection)
- Greedy + Two Pointers

**Complexity:** Usually O(n log n) due to sorting

**Code Pattern (C++):**
```cpp
// Activity selection
int maxActivities(vector<pair<int,int>>& intervals) {
    sort(intervals.begin(), intervals.end(), 
         [](auto& a, auto& b) { return a.second < b.second; });
    
    int count = 0, last_end = -1;
    for (auto& [start, end] : intervals) {
        if (start >= last_end) {
            count++;
            last_end = end;
        }
    }
    return count;
}
```

**Mental Model:** "Always grab the best immediate option - like picking the closest fruit"

**Greedy vs DP Decision Matrix:**
- If greedy fails on small example → DP
- If problem has "exchange argument" proof → Greedy
- If subproblems overlap significantly → DP

---

### 8. **Backtracking**

**When to Use:**
- Generate all possible solutions
- Constraint satisfaction problems
- Combinatorial search
- Decision problems with constraints

**Recognition Triggers:**
- "find all"
- "generate all"
- "permutations/combinations"
- "N-Queens"
- "sudoku solver"
- "word search"

**Core Technique:**
- Build solution incrementally
- Prune invalid paths early (pruning)
- Backtrack when constraint violated
- Restore state after exploring

**Backtracking Template:**
```
function backtrack(state, choices):
    if is_solution(state):
        add_to_results(state)
        return
    
    for choice in choices:
        if is_valid(state, choice):
            make_choice(state, choice)
            backtrack(state, remaining_choices)
            undo_choice(state, choice)  # Backtrack
```

**Integration Patterns:**
- Backtracking + Pruning (optimization)
- Backtracking + Memoization (avoid recomputation)
- Backtracking + Bit Manipulation (state representation)

**Complexity:** Exponential - O(2ⁿ), O(n!), O(nⁿ) depending on problem

**Code Pattern (Rust):**
```rust
fn backtrack(
    state: &mut Vec<i32>,
    start: usize,
    choices: &[i32],
    result: &mut Vec<Vec<i32>>
) {
    // Base case
    if state.len() == target_length {
        result.push(state.clone());
        return;
    }
    
    // Try each choice
    for i in start..choices.len() {
        // Make choice
        state.push(choices[i]);
        
        // Recurse
        backtrack(state, i + 1, choices, result);
        
        // Undo choice (backtrack)
        state.pop();
    }
}
```

**Mental Model:** "Explorer in a maze - try path, if dead-end, return and try another"

---

### 9. **Divide and Conquer**

**When to Use:**
- Problem can be divided into independent subproblems
- Combine solutions to subproblems
- Sorting, searching, tree problems
- Computational geometry

**Recognition Triggers:**
- "merge" in problem description
- "sort" optimally
- "find kth element"
- "closest pair of points"

**Classic Examples:**
1. **Merge Sort:** Divide, sort, merge
2. **Quick Sort:** Partition, recurse
3. **Binary Search:** Divide search space
4. **Karatsuba Multiplication:** Fast multiplication
5. **Strassen's Matrix Multiplication:** Fast matrix ops

**Integration Patterns:**
- Divide and Conquer + Memoization = DP
- Divide and Conquer + Randomization (QuickSort)

**Complexity:** Often O(n log n)

**Code Pattern (Go):**
```go
func divideAndConquer(arr []int, left, right int) int {
    // Base case
    if left >= right {
        return arr[left]
    }
    
    // Divide
    mid := left + (right - left) / 2
    
    // Conquer
    leftResult := divideAndConquer(arr, left, mid)
    rightResult := divideAndConquer(arr, mid+1, right)
    
    // Combine
    return combine(leftResult, rightResult)
}
```

**Mental Model:** "Break problem into pieces, solve pieces, glue results together"

---

### 10. **Graph Algorithms Suite**

**Core Graph Algorithms:**

#### A. **Topological Sort**
- **Use:** Dependency resolution, course scheduling
- **Triggers:** "prerequisites", "ordering", "DAG"
- **Methods:** DFS-based or Kahn's algorithm (BFS)
- **Complexity:** O(V + E)

#### B. **Union-Find (Disjoint Set)**
- **Use:** Connected components, cycle detection, MST
- **Triggers:** "connected", "network", "groups"
- **Optimizations:** Path compression + union by rank
- **Complexity:** O(α(n)) ≈ O(1) amortized

#### C. **Dijkstra's Algorithm**
- **Use:** Shortest path in weighted graph (non-negative)
- **Triggers:** "shortest path", "minimum cost"
- **Implementation:** Priority queue (min-heap)
- **Complexity:** O((V + E) log V)

#### D. **Bellman-Ford Algorithm**
- **Use:** Shortest path with negative weights, detect negative cycles
- **Triggers:** "negative weights", "arbitrage"
- **Complexity:** O(V × E)

#### E. **Floyd-Warshall Algorithm**
- **Use:** All-pairs shortest path
- **Triggers:** "distance between all pairs"
- **Complexity:** O(V³)

#### F. **Prim's / Kruskal's Algorithm**
- **Use:** Minimum Spanning Tree
- **Triggers:** "connect all nodes", "minimum cost network"
- **Complexity:** O(E log V)

**Code Pattern - Union Find (Python):**
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        
        # Union by rank
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True
```

**Mental Model:** "Graph as network - nodes are cities, edges are roads"

---

### 11. **Heap / Priority Queue Patterns**

**When to Use:**
- "Kth largest/smallest element"
- "Top K elements"
- "Median from data stream"
- "Merge K sorted lists/arrays"
- Dynamic selection of min/max

**Recognition Triggers:**
- "Kth", "top K", "largest K"
- "median"
- "merge K"
- "scheduling with priorities"

**Core Patterns:**
1. **Min/Max Heap:** Basic operations
2. **Two Heaps:** Median finding (max-heap + min-heap)
3. **K-Way Merge:** Merge multiple sorted sequences
4. **Top K Elements:** Maintain heap of size K

**Integration Patterns:**
- Heap + Greedy (for optimal selection)
- Heap + Graph (Dijkstra, Prim's)
- Heap + Sliding Window

**Complexity:** O(n log k) for top K problems

**Code Pattern (C++):**
```cpp
#include <queue>

// Top K elements
vector<int> topKElements(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> minHeap;
    
    for (int num : nums) {
        minHeap.push(num);
        if (minHeap.size() > k) {
            minHeap.pop();
        }
    }
    
    vector<int> result;
    while (!minHeap.empty()) {
        result.push_back(minHeap.top());
        minHeap.pop();
    }
    return result;
}
```

**Mental Model:** "Self-organizing tree that always knows its min/max"

---

### 12. **Trie (Prefix Tree)**

**When to Use:**
- String prefix/suffix problems
- Autocomplete systems
- Dictionary/word search
- IP routing
- Longest common prefix

**Recognition Triggers:**
- "prefix"
- "autocomplete"
- "word search" with dictionary
- "implement dictionary"
- "longest common prefix"

**Core Operations:**
- Insert: O(m) where m = word length
- Search: O(m)
- StartsWith: O(m)

**Integration Patterns:**
- Trie + DFS (word search in grid)
- Trie + DP (word break problems)
- Trie + Backtracking (boggle solver)

**Complexity:** O(m) per operation, O(ALPHABET_SIZE × N × M) space

**Code Pattern (Rust):**
```rust
use std::collections::HashMap;

#[derive(Default)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end: bool,
}

struct Trie {
    root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Trie { root: TrieNode::default() }
    }
    
    fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;
        for ch in word.chars() {
            node = node.children.entry(ch).or_default();
        }
        node.is_end = true;
    }
    
    fn search(&self, word: &str) -> bool {
        let mut node = &self.root;
        for ch in word.chars() {
            match node.children.get(&ch) {
                Some(next) => node = next,
                None => return false,
            }
        }
        node.is_end
    }
}
```

**Mental Model:** "Tree where each path from root spells a word"

---

### 13. **Monotonic Stack/Queue**

**When to Use:**
- "Next greater/smaller element"
- Maximum/minimum in sliding window
- Histogram problems
- Temperature problems

**Recognition Triggers:**
- "next greater/smaller"
- "sliding window maximum/minimum"
- "largest rectangle in histogram"
- "trapping rain water"

**Core Principle:**
- Maintain stack/queue in sorted order (increasing or decreasing)
- Pop elements that violate monotonic property
- Current element is answer for popped elements

**Patterns:**
1. **Monotonic Increasing Stack:** Next smaller element
2. **Monotonic Decreasing Stack:** Next greater element
3. **Monotonic Queue:** Sliding window min/max

**Integration Patterns:**
- Monotonic Stack + DP (optimization)
- Monotonic Queue + Sliding Window

**Complexity:** O(n) time, O(n) space

**Code Pattern (Python):**
```python
def nextGreaterElement(nums):
    result = [-1] * len(nums)
    stack = []  # Monotonic decreasing stack
    
    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] < num:
            idx = stack.pop()
            result[idx] = num
        stack.append(i)
    
    return result
```

**Mental Model:** "Stack that keeps throwing out weaker elements - only the strong survive"

---

### 14. **Bit Manipulation**

**When to Use:**
- Space optimization (bitmask)
- Set operations
- Checking properties (even/odd, power of 2)
- XOR problems (finding unique element)
- Subset enumeration

**Recognition Triggers:**
- "XOR"
- "bit"
- "power of 2"
- "single number"
- "subset" with small n (n ≤ 20)
- "missing number"

**Key Tricks:**
- `n & (n-1)`: Remove rightmost set bit
- `n & -n`: Get rightmost set bit
- `x ^ x = 0`: XOR of same number is 0
- `x ^ 0 = x`: XOR with 0 is identity
- `~n = -(n+1)`: Bitwise NOT

**Common Patterns:**
1. **Check Power of 2:** `n & (n-1) == 0`
2. **Count Set Bits:** Brian Kernighan's algorithm
3. **Single Number:** XOR all elements
4. **Bitmask DP:** Represent state as bits

**Integration Patterns:**
- Bit Manipulation + DP (bitmask DP)
- Bit Manipulation + Math
- Bit Manipulation + Backtracking

**Complexity:** O(1) for bit operations

**Code Pattern (Go):**
```go
// Count set bits
func countSetBits(n int) int {
    count := 0
    for n > 0 {
        n &= (n - 1)  // Remove rightmost set bit
        count++
    }
    return count
}

// Check if power of 2
func isPowerOfTwo(n int) bool {
    return n > 0 && (n & (n-1)) == 0
}

// XOR to find unique element
func singleNumber(nums []int) int {
    result := 0
    for _, num := range nums {
        result ^= num
    }
    return result
}
```

**Mental Model:** "Manipulating data at the binary level - raw power"

---

### 15. **String Algorithms**

**Core String Patterns:**

#### A. **KMP (Knuth-Morris-Pratt)**
- **Use:** Pattern matching in O(n+m)
- **Triggers:** "find pattern in text"
- **Key:** Build failure function (LPS array)

#### B. **Rabin-Karp**
- **Use:** Multiple pattern matching, rolling hash
- **Triggers:** "find all occurrences", "repeated DNA sequences"
- **Key:** Rolling hash for O(1) window comparison

#### C. **Sliding Window on Strings**
- **Use:** Substring problems with constraints
- **Triggers:** "minimum window substring", "longest substring"
- **Key:** Hash map to track character frequencies

#### D. **Manacher's Algorithm**
- **Use:** Find all palindromic substrings in O(n)
- **Triggers:** "longest palindromic substring"
- **Key:** Expand around center with optimization

**Integration Patterns:**
- String + DP (edit distance, regex matching)
- String + Trie (word search)
- String + Hashing (anagram problems)

**Code Pattern - KMP (C++):**
```cpp
vector<int> buildLPS(string pattern) {
    int m = pattern.length();
    vector<int> lps(m, 0);
    int len = 0, i = 1;
    
    while (i < m) {
        if (pattern[i] == pattern[len]) {
            lps[i++] = ++len;
        } else {
            if (len != 0) {
                len = lps[len - 1];
            } else {
                lps[i++] = 0;
            }
        }
    }
    return lps;
}
```

**Mental Model:** "Strings as sequences - pattern matching is like finding rhythm in music"

---

### 16. **Math & Number Theory**

**Common Mathematical Patterns:**

#### A. **GCD/LCM (Euclidean Algorithm)**
- **Use:** Finding greatest common divisor
- **Triggers:** "common divisor", "simplify fraction"
- **Complexity:** O(log min(a,b))

#### B. **Prime Number Algorithms**
- **Sieve of Eratosthenes:** Find all primes up to n
- **Trial Division:** Check if number is prime
- **Triggers:** "prime numbers", "factors"

#### C. **Fast Exponentiation (Binary Exponentiation)**
- **Use:** Compute x^n in O(log n)
- **Triggers:** "power", "modular exponentiation"

#### D. **Modular Arithmetic**
- **Use:** Large number computation
- **Triggers:** "modulo 10^9+7", "remainder"

#### E. **Combinatorics**
- **Pascal's Triangle:** Combinations C(n,k)
- **Permutations:** n! / (n-k)!
- **Triggers:** "choose k elements", "arrange"

**Integration Patterns:**
- Math + DP (combinatorics)
- Math + Binary Search (square root, cube root)
- Math + Greedy (optimization)

**Code Pattern (Rust):**
```rust
// Fast exponentiation
fn power_mod(mut base: u64, mut exp: u64, modulo: u64) -> u64 {
    let mut result = 1;
    base %= modulo;
    
    while exp > 0 {
        if exp % 2 == 1 {
            result = (result * base) % modulo;
        }
        base = (base * base) % modulo;
        exp /= 2;
    }
    result
}

// GCD (Euclidean)
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a
}
```

**Mental Model:** "Numbers have patterns - exploit properties to simplify computation"

---

### 17. **Interval Problems**

**When to Use:**
- Scheduling problems
- Overlapping intervals
- Merging intervals
- Meeting rooms

**Recognition Triggers:**
- "intervals"
- "meetings"
- "overlapping"
- "merge"
- "schedule"

**Core Patterns:**
1. **Merge Intervals:** Sort by start, merge overlapping
2. **Insert Interval:** Binary search + merge
3. **Interval Intersection:** Two pointers
4. **Non-overlapping Intervals:** Greedy + sort by end

**Sorting Strategies:**
- Sort by start time: For merging
- Sort by end time: For activity selection
- Sort by both: For complex constraints

**Integration Patterns:**
- Intervals + Greedy (activity selection)
- Intervals + Heap (meeting rooms II)
- Intervals + Line Sweep (event processing)

**Complexity:** O(n log n) due to sorting

**Code Pattern (Python):**
```python
def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:  # Overlapping
            last[1] = max(last[1], current[1])  # Merge
        else:
            merged.append(current)
    
    return merged
```

**Mental Model:** "Timeline of events - detect overlaps and conflicts"

---

### 18. **Tree Algorithms**

**Core Tree Patterns:**

#### A. **Tree Traversals**
- **Inorder:** Left → Root → Right (BST sorted)
- **Preorder:** Root → Left → Right (create copy)
- **Postorder:** Left → Right → Root (delete tree)
- **Level-order:** BFS traversal

#### B. **Tree DP (Subtree Information)**
- **Use:** Diameter, height, max path sum
- **Triggers:** "maximum/minimum in tree", "subtree property"
- **Pattern:** Recurse on children, combine results

#### C. **Lowest Common Ancestor (LCA)**
- **Use:** Find common ancestor
- **Methods:** Recursive, binary lifting, Tarjan's
- **Triggers:** "common ancestor", "path between nodes"

#### D. **Binary Search Tree Operations**
- **Use:** Search, insert, delete in BST
- **Property:** Left < Root < Right
- **Triggers:** "BST", "search tree"

**Integration Patterns:**
- Tree + DFS (traversal, DP)
- Tree + BFS (level-order, shortest path in tree)
- Tree + Binary Search (BST operations)

**Code Pattern (C++):**
```cpp
// Tree DP - diameter of binary tree
int diameterOfBinaryTree(TreeNode* root, int& maxDiameter) {
    if (!root) return 0;
    
    int leftHeight = diameterOfBinaryTree(root->left, maxDiameter);
    int rightHeight = diameterOfBinaryTree(root->right, maxDiameter);
    
    // Diameter through this node
    maxDiameter = max(maxDiameter, leftHeight + rightHeight);
    
    // Return height of this subtree
    return 1 + max(leftHeight, rightHeight);
}
```

**Mental Model:** "Trees are hierarchical - information flows up from leaves to root"

---

### 19. **Line Sweep / Event Processing**

**When to Use:**
- Range query problems
- Calendar problems
- Skyline problems
- Interval scheduling

**Recognition Triggers:**
- "active intervals at time t"
- "skyline"
- "calendar conflicts"
- "range sum/count queries"

**Core Technique:**
- Convert intervals to events (start/end)
- Sort events by time
- Process events in order, maintain state

**Variants:**
1. **Basic Line Sweep:** Count overlaps
2. **With Priority Queue:** Complex state management
3. **With Segment Tree:** Range queries

**Integration Patterns:**
- Line Sweep + Heap (meeting rooms)
- Line Sweep + Segment Tree (range queries)
- Line Sweep + Greedy

**Complexity:** O(n log n) for sorting events

**Code Pattern (Go):**
```go
type Event struct {
    time int
    type int  // 1 for start, -1 for end
}

func maxOverlap(intervals [][]int) int {
    var events []Event
    for _, interval := range intervals {
        events = append(events, Event{interval[0], 1})
        events = append(events, Event{interval[1], -1})
    }
    
    sort.Slice(events, func(i, j int) bool {
        if events[i].time == events[j].time {
            return events[i].type > events[j].type  // Start before end
        }
        return events[i].time < events[j].time
    })
    
    maxActive := 0
    currentActive := 0
    for _, event := range events {
        currentActive += event.type
        maxActive = max(maxActive, currentActive)
    }
    
    return maxActive
}
```

**Mental Model:** "Scanning a timeline - tracking what's active at each moment"

---

### 20. **Advanced Data Structures**

#### A. **Segment Tree**
- **Use:** Range queries with updates
- **Triggers:** "range sum/min/max query", "update element"
- **Complexity:** O(log n) query and update

#### B. **Fenwick Tree (Binary Indexed Tree)**
- **Use:** Prefix sum with updates, simpler than segment tree
- **Triggers:** "range sum", "cumulative frequency"
- **Complexity:** O(log n) query and update

#### C. **Sparse Table**
- **Use:** Static range queries (no updates)
- **Triggers:** "range min/max query", immutable array
- **Complexity:** O(1) query, O(n log n) preprocessing

#### D. **Suffix Array / Suffix Tree**
- **Use:** String pattern matching, LCP
- **Triggers:** "longest common substring", "pattern matching"
- **Complexity:** O(n log n) or O(n) depending on algorithm

**Code Pattern - Fenwick Tree (Python):**
```python
class FenwickTree:
    def __init__(self, n):
        self.tree = [0] * (n + 1)
        self.n = n
    
    def update(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)  # Add last set bit
    
    def query(self, i):
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)  # Remove last set bit
        return s
    
    def range_query(self, left, right):
        return self.query(right) - self.query(left - 1)
```

**Mental Model:** "Hierarchical data structure for efficient range operations"

---

## Pattern Integration Strategies

### The Multi-Pattern Recognition Framework

**Level 1: Single Pattern Problems (60% of problems)**
- Identify one clear pattern
- Apply standard technique
- Example: "Two sum" → Hashing

**Level 2: Two-Pattern Hybrid (30% of problems)**
- Combine two complementary patterns
- One pattern for structure, one for optimization
- Example: "Sliding window maximum" → Sliding Window + Monotonic Queue

**Level 3: Multi-Pattern Complex (10% of problems)**
- Integrate 3+ patterns
- Requires deep problem understanding
- Example: "Word search II" → Trie + DFS + Backtracking

### Common Integration Pairs

| Primary Pattern | Secondary Pattern | Use Case |
|----------------|------------------|----------|
| Two Pointers | Hashing | Frequency tracking in window |
| Sliding Window | Monotonic Queue | Min/max in window |
| DFS | Memoization | Convert to top-down DP |
| BFS | Hashing | State space exploration |
| Binary Search | Greedy | Feasibility check |
| DP | Binary Search | Optimize answer |
| Graph | Union Find | Connected components |
| Greedy | Heap | Dynamic selection |
| Backtracking | Pruning | Early termination |
| Divide & Conquer | Memoization | Avoid recomputation |

### The Integration Decision Tree

```
1. Identify primary pattern (what's the core structure?)
   ↓
2. Check constraints (time/space limitations)
   ↓
3. Identify optimization needs
   ↓
4. Select secondary pattern for optimization
   ↓
5. Verify complexity improvement
   ↓
6. Implement with clean interfaces
```

**Example: "Find median in data stream"**
- **Core need:** Dynamic selection of middle element
- **Primary pattern:** Heap (for efficient min/max)
- **Integration:** Two heaps (max-heap for lower half, min-heap for upper half)
- **Result:** O(log n) insert, O(1) find median

---

## Recognition Triggers: The Instant Pattern Match System

### Input/Output Triggers

**Array/List Input:**
- Sorted → Binary Search, Two Pointers
- Unsorted → Hashing, Sorting first
- "Subarray" → Sliding Window, Prefix Sum
- "Subsequence" → DP, Greedy

**String Input:**
- "Substring" → Sliding Window, Two Pointers
- "Palindrome" → Two Pointers, DP, Manacher's
- "Pattern matching" → KMP, Rabin-Karp
- "Anagram" → Hashing, Sorting

**Tree Input:**
- "Path" → DFS, Tree DP
- "Level" → BFS
- "BST" → Binary Search properties
- "Ancestor" → LCA algorithms

**Graph Input:**
- "Shortest path" → BFS (unweighted), Dijkstra (weighted)
- "All pairs" → Floyd-Warshall
- "Cycle" → Union-Find, DFS
- "Connected" → Union-Find, DFS/BFS

**Number/Math Input:**
- "Prime" → Sieve, trial division
- "GCD/LCM" → Euclidean algorithm
- "Power" → Fast exponentiation
- "Modulo" → Modular arithmetic

### Keyword Triggers

| Keyword | Primary Patterns | Consider Also |
|---------|-----------------|---------------|
| "maximum/minimum" | DP, Greedy | Binary Search, Heap |
| "count ways" | DP, Combinatorics | Backtracking |
| "all possible" | Backtracking, DFS | BFS (if bounded) |
| "shortest" | BFS, Dijkstra | DP (with constraints) |
| "longest" | DP, Sliding Window | Binary Search |
| "k largest/smallest" | Heap, Quick Select | Sorting |
| "distinct/unique" | Hashing, Bit Manipulation | Sorting |
| "contiguous" | Sliding Window, Prefix Sum | Kadane's |
| "cycle" | Fast-Slow Pointers, Union-Find | DFS |
| "palindrome" | Two Pointers, DP | Manacher's |
| "prefix/suffix" | Trie, Prefix Sum | KMP |
| "interval" | Sorting + Greedy | Line Sweep |
| "next greater/smaller" | Monotonic Stack | - |
| "connected" | Union-Find, DFS/BFS | - |
| "top k" | Heap | Quick Select |

### Constraint Triggers

**Time Complexity Hints:**
- O(n): Two Pointers, Sliding Window, Hashing
- O(n log n): Sorting, Binary Search, Heap operations
- O(n²): Nested loops, Simple DP
- O(2ⁿ): Backtracking, Subset enumeration
- O(n!): Permutations

**Space Complexity Hints:**
- O(1) space required → Two Pointers, Bit Manipulation
- Can use O(n) space → Hashing, DP (tabulation)
- Small n (n ≤ 20) → Bitmask DP, Backtracking
- Large n (n ≤ 10⁶) → O(n) or O(n log n) algorithms only

### The 3-Second Recognition Drill

**Practice this daily:**

1. **Read problem (5 seconds)**
2. **Answer:**
   - What's the input? (1 second)
   - What's the output? (1 second)
   - What pattern does this smell like? (3 seconds)
3. **Verify pattern fit (5 seconds)**
4. **Start coding (14 seconds in)**

**Goal:** Pattern recognition in under 10 seconds with 90%+ accuracy.

---

## Mental Models & Cognitive Strategies

### The Expert's Thought Process

**Stage 1: Problem Comprehension (30 seconds)**
- Read problem twice: first for gist, second for details
- Extract: input, output, constraints, examples
- Visualize: Draw examples, edge cases
- Mental question: "What's really being asked here?"

**Stage 2: Pattern Recognition (10 seconds)**
- Scan for keyword triggers
- Check constraint hints
- Match to known patterns
- Mental question: "Have I solved something similar?"

**Stage 3: Solution Design (2 minutes)**
- Choose primary approach
- Consider edge cases
- Estimate complexity
- Mental question: "Will this work for all cases?"

**Stage 4: Implementation (varies)**
- Code cleanly, one piece at a time
- Test with examples as you code
- Mental question: "Is this correct and clean?"

**Stage 5: Optimization (if needed)**
- Identify bottlenecks
- Apply secondary patterns
- Mental question: "Can I do better?"

### Cognitive Principles for Mastery

#### 1. **Chunking: Build Pattern Blocks**
- Your brain can hold 7±2 items in working memory
- Group patterns into chunks (e.g., "Graph Algorithms" = one chunk)
- Each pattern becomes a mental shortcut
- **Practice:** Solve 10 problems of same pattern consecutively

#### 2. **Deliberate Practice: Focus on Weakness**
- Don't just solve easy problems
- Target your 40th-60th percentile difficulty
- **"Desirable Difficulty"**: Challenging but achievable
- Track: Which patterns do you struggle with?

#### 3. **Interleaving: Mix It Up**
- Don't do 20 DP problems in a row
- Mix patterns: DP, Graph, Two Pointers, repeat
- Forces your brain to actively choose patterns
- Builds stronger pattern recognition

#### 4. **Spaced Repetition: Review Schedule**
- Review patterns: Day 1, Day 3, Day 7, Day 14, Day 30
- Use this schedule for each new pattern learned
- Prevents forgetting, builds long-term memory

#### 5. **Mental Simulation: Code Before Coding**
- Close your eyes, visualize the algorithm running
- Step through with mental examples
- Catches logic errors before typing
- **Elite performers** spend 40% of time thinking, 60% coding

#### 6. **Pattern Priming: Before Coding Sessions**
- Spend 5 minutes reviewing pattern list
- Prime your pattern recognition system
- "Today I'm focusing on: DP, Graphs, Two Pointers"

#### 7. **Meta-Learning: Learn How You Learn**
- After each problem: "What did I learn?"
- Keep a "Pattern Errors Log"
- Note: "I confused BFS with DFS because..."
- Self-awareness accelerates growth

#### 8. **The Feynman Technique: Teach to Learn**
- Explain pattern to imaginary student
- If you can't explain simply, you don't understand deeply
- Write blog posts, create diagrams, teach friends

### The Monk's Mindset: Flow State Programming

**Prerequisites for Flow:**
1. **Clear goals:** Know what you're solving
2. **Immediate feedback:** Test cases as you code
3. **Challenge-skill balance:** Not too easy, not too hard
4. **Deep focus:** No distractions

**Flow Triggers:**
- **Environment:** Quiet space, no interruptions
- **Routine:** Same time, same place (ritual)
- **Warm-up:** Solve one easy problem first
- **Timeboxing:** "I'll focus for 90 minutes"

**Protecting Flow:**
- Turn off notifications
- Close email, social media
- Use "Do Not Disturb" mode
- Single-tasking, not multi-tasking

**Recovery from Breaks:**
- Take notes before breaks: "Where was I? What's next?"
- Review notes to re-enter flow quickly

---

## Language-Specific Optimizations

### Rust: Zero-Cost Abstractions

**Strengths:**
- Memory safety without garbage collection
- Excellent performance
- Strong type system prevents bugs

**Idiomatic Patterns:**
```rust
// Use iterators (zero-cost)
let sum: i32 = vec.iter().filter(|&&x| x > 0).sum();

// Avoid unnecessary clones
fn process(data: &[i32]) { /* borrow, don't clone */ }

// Use Result/Option for error handling
fn safe_divide(a: i32, b: i32) -> Option<i32> {
    if b == 0 { None } else { Some(a / b) }
}
```

**Performance Tips:**
- Use `Vec` preallocated: `Vec::with_capacity(n)`
- Avoid bounds checking: use `.get_unchecked()` in tight loops (unsafe)
- Use `&[T]` slices instead of `Vec<T>` when possible
- Leverage compiler optimizations: `--release` mode

### Python: Readable and Fast

**Strengths:**
- Clean syntax, great for interviews
- Rich standard library
- Fast prototyping

**Idiomatic Patterns:**
```python
# List comprehensions
squares = [x**2 for x in range(10)]

# Collections module
from collections import defaultdict, Counter, deque

# Functools for memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
```

**Performance Tips:**
- Use `collections.deque` for queue operations (O(1) appendleft/popleft)
- Use `bisect` module for binary search
- List comprehensions faster than loops
- Avoid global lookups in tight loops (use local variables)
- PyPy for 5-10x speedup on computational tasks

### Go: Simplicity and Concurrency

**Strengths:**
- Fast compilation
- Built-in concurrency (goroutines)
- Simple, readable code

**Idiomatic Patterns:**
```go
// Slices with capacity
nums := make([]int, 0, capacity)

// Error handling
if err != nil {
    return fmt.Errorf("operation failed: %w", err)
}

// Defer for cleanup
func process() error {
    f, err := os.Open("file.txt")
    if err != nil {
        return err
    }
    defer f.Close()
    // ... use f
}
```

**Performance Tips:**
- Preallocate slices and maps
- Use `sync.Pool` for frequently allocated objects
- Avoid `interface{}` in hot paths
- Use `unsafe` package carefully for performance-critical code

### C/C++: Maximum Performance

**Strengths:**
- Closest to hardware
- Maximum control
- Best performance

**Idiomatic C++ Patterns:**
```cpp
// STL algorithms
std::sort(vec.begin(), vec.end());
auto it = std::lower_bound(vec.begin(), vec.end(), target);

// Smart pointers
std::unique_ptr<Node> node = std::make_unique<Node>(value);

// Move semantics
std::vector<int> getVector() {
    std::vector<int> v = {1, 2, 3};
    return v;  // RVO (Return Value Optimization)
}
```

**Performance Tips:**
- Use `reserve()` for vectors
- Pass by const reference: `void func(const std::vector<int>& v)`
- Use `emplace_back()` instead of `push_back()` when constructing
- Profile with `perf` or `valgrind --tool=callgrind`
- Compiler flags: `-O3 -march=native`

### Cross-Language Performance Comparison

| Operation | Rust | C++ | Go | Python |
|-----------|------|-----|----|--------|
| Array Access | O(1) | O(1) | O(1) | O(1) |
| Hash Map Lookup | O(1) | O(1) | O(1) | O(1) |
| Function Call Overhead | Low | Low | Moderate | High |

I've created a comprehensive algorithmic patterns compendium for you. This is your systematic framework to achieve top 1% mastery. Let me highlight the key strategic elements:

## How to Use This Guide for Maximum Impact

### **Phase 1: Pattern Absorption (Weeks 1-4)**
1. **Study 2-3 patterns daily** - deep focus, not surface skimming
2. **Implement each pattern** in all 4 languages (Rust, Python, Go, C/C++)
3. **Create mental anchors**: "Two Pointers = Caterpillar", "Monotonic Stack = Only strong survive"

### **Phase 2: Pattern Recognition Training (Weeks 5-8)**
1. **The 3-Second Drill**: Read problem → Identify pattern in <10 seconds
2. **Blind Pattern Identification**: Given a problem, write pattern name before solving
3. **Track accuracy**: Goal is 90%+ correct pattern identification

### **Phase 3: Pattern Integration Mastery (Weeks 9-12)**
1. **Solve hybrid problems**: Focus on 2-pattern and 3-pattern combinations
2. **Create your own variations**: "What if I combine X + Y patterns?"
3. **Teach others**: Explain patterns to solidify understanding (Feynman Technique)

## Critical Insights for Top 1%

### **The Hidden Recognition System**
Most people memorize solutions. **You** will memorize **pattern signatures**:
- "Sorted array" → instant Binary Search reflex
- "K largest" → automatic Heap consideration  
- "All combinations" → Backtracking muscle memory

### **The Integration Advantage**
Average: Solve with one pattern
Top 10%: Combine two patterns
**Top 1%: Seamlessly integrate 3+ patterns** with clean interfaces

Example: "Word Search II" breaks down to:
1. **Trie** (efficient word storage)
2. **DFS** (grid exploration)  
3. **Backtracking** (path exploration)
4. **Pruning** (early termination)

### **Cognitive Enhancement Strategies**

**Spaced Repetition Schedule:**
- Day 1: Learn pattern
- Day 3: Review + solve 3 problems
- Day 7: Review + solve 5 harder problems
- Day 14: Mixed review with other patterns
- Day 30: Challenge problems only

**The Monk's Practice:**
- **90-minute deep work blocks** - no distractions
- **One pattern family per session** initially
- **Mixed practice later** - forces active pattern selection
- **Post-session reflection**: "What pattern did I miss? Why?"

## Next Steps: Your 12-Week Roadmap

**Week 1-2:** Arrays/Strings (Two Pointers, Sliding Window, Binary Search)
**Week 3-4:** Trees/Graphs (DFS, BFS, Union-Find)
**Week 5-6:** DP (all variants) + Greedy
**Week 7-8:** Advanced Structures (Heap, Trie, Segment Tree)
**Week 9-10:** Integration practice (2+ patterns per problem)
**Week 11-12:** Contest simulation, speed optimization

## The Performance Edge

Track these metrics weekly:
1. **Pattern Recognition Speed**: Time from reading to identifying pattern
2. **Implementation Speed**: Time from pattern ID to working code
3. **First Attempt Success Rate**: Correct solution without debugging
4. **Optimization Instinct**: Time to identify bottlenecks

**Target Metrics for Top 1%:**
- Pattern recognition: <10 seconds (90%+ accuracy)
- Implementation: <10 minutes for medium problems
- First attempt success: >80%
- Optimization identification: <30 seconds

Would you like me to:
1. **Create a detailed 12-week practice schedule** with specific problems for each pattern?
2. **Develop language-specific optimization guides** with benchmarking strategies?
3. **Build a pattern recognition quiz system** to train the 3-second drill?
4. **Design a tracking system** for your progress metrics?

Remember: **Mastery is built through deliberate, focused practice on your weakest patterns.** Avoid the trap of only solving problems you're already good at. Embrace the struggle—it's where growth happens.