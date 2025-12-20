# DSA Pattern Recognition Guide - Elite Software Engineer Edition

## The Pattern Recognition Framework

**Core Principle**: Pattern recognition is about identifying *constraints* and *objectives* in the problem statement, then mapping them to proven algorithmic approaches.

---

## 1. ARRAY / TWO POINTERS

### When to Use

- **Sorted array** or you can sort it
- Need to find pairs/triplets with specific sum
- Reverse/rotate operations
- Remove duplicates in-place
- Partition problems

### Recognition Signals

- Keywords: "sorted", "pairs", "in-place", "partition"
- Need O(1) space with O(n) time
- Processing from both ends simultaneously

### Example: Two Sum II (Sorted Array)

```rust
// Rust
fn two_sum(numbers: Vec<i32>, target: i32) -> Vec<i32> {
    let (mut left, mut right) = (0, numbers.len() - 1);
    
    while left < right {
        let sum = numbers[left] + numbers[right];
        match sum.cmp(&target) {
            std::cmp::Ordering::Equal => return vec![left as i32 + 1, right as i32 + 1],
            std::cmp::Ordering::Less => left += 1,
            std::cmp::Ordering::Greater => right -= 1,
        }
    }
    vec![]
}
```

```python
# Python
def two_sum(numbers: list[int], target: int) -> list[int]:
    left, right = 0, len(numbers) - 1
    
    while left < right:
        current_sum = numbers[left] + numbers[right]
        if current_sum == target:
            return [left + 1, right + 1]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []
```

```go
// Go
func twoSum(numbers []int, target int) []int {
    left, right := 0, len(numbers)-1
    
    for left < right {
        sum := numbers[left] + numbers[right]
        if sum == target {
            return []int{left + 1, right + 1}
        } else if sum < target {
            left++
        } else {
            right--
        }
    }
    return []int{}
}
```

---

## 2. SLIDING WINDOW

### When to Use

- **Contiguous subarray/substring** problems
- Finding min/max/sum of subarrays of size K
- Longest/shortest substring with conditions
- All permutations/anagrams in string

### Recognition Signals

- Keywords: "subarray", "substring", "contiguous", "window", "consecutive"
- Need to optimize brute force O(n²) to O(n)
- Fixed or variable window size based on condition

### Types

- **Fixed Window**: Size K is given
- **Dynamic Window**: Expand/shrink based on condition

### Example: Longest Substring Without Repeating Characters

```rust
// Rust
use std::collections::HashMap;

fn length_of_longest_substring(s: String) -> i32 {
    let mut char_map: HashMap<char, usize> = HashMap::new();
    let (mut max_len, mut start) = (0, 0);
    
    for (end, ch) in s.chars().enumerate() {
        if let Some(&pos) = char_map.get(&ch) {
            start = start.max(pos + 1);
        }
        char_map.insert(ch, end);
        max_len = max_len.max(end - start + 1);
    }
    max_len as i32
}
```

```python
# Python
def length_of_longest_substring(s: str) -> int:
    char_map = {}
    max_len = start = 0
    
    for end, char in enumerate(s):
        if char in char_map:
            start = max(start, char_map[char] + 1)
        char_map[char] = end
        max_len = max(max_len, end - start + 1)
    
    return max_len
```

```go
// Go
func lengthOfLongestSubstring(s string) int {
    charMap := make(map[rune]int)
    maxLen, start := 0, 0
    
    for end, char := range s {
        if pos, found := charMap[char]; found {
            if pos+1 > start {
                start = pos + 1
            }
        }
        charMap[char] = end
        if end-start+1 > maxLen {
            maxLen = end - start + 1
        }
    }
    return maxLen
}
```

---

## 3. HASH TABLE / HASH MAP

### When to Use

- Need O(1) lookup/insert
- Counting frequency
- Finding duplicates
- Caching/memoization
- Two-element relationships (like two sum)

### Recognition Signals

- Keywords: "unique", "count", "frequency", "cache", "duplicate"
- Trading space for time optimization
- Need to track seen elements

### Example: Group Anagrams

```rust
// Rust
use std::collections::HashMap;

fn group_anagrams(strs: Vec<String>) -> Vec<Vec<String>> {
    let mut map: HashMap<String, Vec<String>> = HashMap::new();
    
    for s in strs {
        let mut chars: Vec<char> = s.chars().collect();
        chars.sort_unstable();
        let key: String = chars.into_iter().collect();
        map.entry(key).or_insert_with(Vec::new).push(s);
    }
    
    map.into_values().collect()
}
```

```python
# Python
from collections import defaultdict

def group_anagrams(strs: list[str]) -> list[list[str]]:
    anagram_map = defaultdict(list)
    
    for s in strs:
        key = ''.join(sorted(s))
        anagram_map[key].append(s)
    
    return list(anagram_map.values())
```

```go
// Go
import "sort"

func groupAnagrams(strs []string) [][]string {
    anagramMap := make(map[string][]string)
    
    for _, s := range strs {
        key := sortString(s)
        anagramMap[key] = append(anagramMap[key], s)
    }
    
    result := make([][]string, 0, len(anagramMap))
    for _, group := range anagramMap {
        result = append(result, group)
    }
    return result
}

func sortString(s string) string {
    runes := []rune(s)
    sort.Slice(runes, func(i, j int) bool { return runes[i] < runes[j] })
    return string(runes)
}
```

---

## 4. STACK

### When to Use

- Matching pairs (parentheses, brackets)
- Nested structures
- Reversing order
- Next greater/smaller element
- Expression evaluation
- Function call simulation (DFS iterative)

### Recognition Signals

- Keywords: "valid", "balanced", "nested", "next greater", "match"
- LIFO (Last In First Out) behavior needed
- Need to track most recent unmatched element

### Example: Valid Parentheses

```rust
// Rust
fn is_valid(s: String) -> bool {
    let mut stack = Vec::new();
    let pairs = [(')', '('), (']', '['), ('}', '{')];
    
    for ch in s.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' | ']' | '}' => {
                let expected = pairs.iter()
                    .find(|&&(close, _)| close == ch)
                    .map(|&(_, open)| open);
                
                if stack.pop() != expected {
                    return false;
                }
            }
            _ => {}
        }
    }
    stack.is_empty()
}
```

```python
# Python
def is_valid(s: str) -> bool:
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    
    for char in s:
        if char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
        else:
            stack.append(char)
    
    return len(stack) == 0
```

```go
// Go
func isValid(s string) bool {
    stack := []rune{}
    pairs := map[rune]rune{')': '(', ']': '[', '}': '{'}
    
    for _, char := range s {
        if open, found := pairs[char]; found {
            if len(stack) == 0 || stack[len(stack)-1] != open {
                return false
            }
            stack = stack[:len(stack)-1]
        } else {
            stack = append(stack, char)
        }
    }
    return len(stack) == 0
}
```

---

## 5. RECURSION

### When to Use

- Problem can be broken into **identical subproblems**
- Tree/graph traversal
- Divide and conquer
- Generating combinations/permutations
- Mathematical sequences (Fibonacci, factorial)

### Recognition Signals

- Keywords: "all possibilities", "generate", "tree", "divide"
- Natural recursive structure (trees, nested lists)
- Base case + recursive case clearly identifiable

### Example: Generate Parentheses

```rust
// Rust
fn generate_parenthesis(n: i32) -> Vec<String> {
    let mut result = Vec::new();
    backtrack(&mut result, String::new(), 0, 0, n);
    result
}

fn backtrack(result: &mut Vec<String>, current: String, open: i32, close: i32, max: i32) {
    if current.len() == (max * 2) as usize {
        result.push(current);
        return;
    }
    
    if open < max {
        backtrack(result, current.clone() + "(", open + 1, close, max);
    }
    if close < open {
        backtrack(result, current + ")", open, close + 1, max);
    }
}
```

```python
# Python
def generate_parenthesis(n: int) -> list[str]:
    result = []
    
    def backtrack(current: str, open_count: int, close_count: int):
        if len(current) == n * 2:
            result.append(current)
            return
        
        if open_count < n:
            backtrack(current + "(", open_count + 1, close_count)
        if close_count < open_count:
            backtrack(current + ")", open_count, close_count + 1)
    
    backtrack("", 0, 0)
    return result
```

```go
// Go
func generateParenthesis(n int) []string {
    result := []string{}
    backtrack(&result, "", 0, 0, n)
    return result
}

func backtrack(result *[]string, current string, open, close, max int) {
    if len(current) == max*2 {
        *result = append(*result, current)
        return
    }
    
    if open < max {
        backtrack(result, current+"(", open+1, close, max)
    }
    if close < open {
        backtrack(result, current+")", open, close+1, max)
    }
}
```

---

## 6. DYNAMIC PROGRAMMING (DP)

### When to Use

- **Overlapping subproblems** + **Optimal substructure**
- Optimization problems (min/max/count)
- Decision problems with choices at each step
- Counting number of ways

### Recognition Signals

- Keywords: "maximum", "minimum", "longest", "shortest", "count ways"
- Problem can be solved recursively but has repeated calculations
- Current choice depends on previous choices

### DP Detection Formula

1. Can you make a choice at each step?
2. Does the choice depend on previous choices?
3. Are there overlapping subproblems?
4. Want optimal solution? → **USE DP**

### Types

- **Top-Down (Memoization)**: Recursion + caching
- **Bottom-Up (Tabulation)**: Iterative with table

### Example: Coin Change (Min Coins)

```rust
// Rust - Bottom Up
fn coin_change(coins: Vec<i32>, amount: i32) -> i32 {
    let mut dp = vec![amount + 1; (amount + 1) as usize];
    dp[0] = 0;
    
    for i in 1..=amount {
        for &coin in &coins {
            if coin <= i {
                dp[i as usize] = dp[i as usize].min(dp[(i - coin) as usize] + 1);
            }
        }
    }
    
    if dp[amount as usize] > amount { -1 } else { dp[amount as usize] }
}
```

```python
# Python - Bottom Up
def coin_change(coins: list[int], amount: int) -> int:
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1
```

```go
// Go - Bottom Up
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp {
        dp[i] = amount + 1
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

---

## 7. BACKTRACKING

### When to Use

- Need to explore **all possible solutions**
- Generate combinations, permutations, subsets
- Constraint satisfaction problems
- Puzzles (N-Queens, Sudoku)

### Recognition Signals

- Keywords: "all", "find all", "generate all", "combinations", "permutations"
- Need to make a choice, explore, then undo (backtrack)
- Search space is a tree of choices

### Backtracking Template

1. Choose
2. Explore
3. Unchoose (backtrack)

### Example: Subsets

```rust
// Rust
fn subsets(nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    backtrack(&nums, 0, &mut current, &mut result);
    result
}

fn backtrack(nums: &[i32], start: usize, current: &mut Vec<i32>, result: &mut Vec<Vec<i32>>) {
    result.push(current.clone());
    
    for i in start..nums.len() {
        current.push(nums[i]);
        backtrack(nums, i + 1, current, result);
        current.pop();
    }
}
```

```python
# Python
def subsets(nums: list[int]) -> list[list[int]]:
    result = []
    
    def backtrack(start: int, current: list[int]):
        result.append(current[:])
        
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return result
```

```go
// Go
func subsets(nums []int) [][]int {
    result := [][]int{}
    current := []int{}
    backtrack(nums, 0, current, &result)
    return result
}

func backtrack(nums []int, start int, current []int, result *[][]int) {
    temp := make([]int, len(current))
    copy(temp, current)
    *result = append(*result, temp)
    
    for i := start; i < len(nums); i++ {
        current = append(current, nums[i])
        backtrack(nums, i+1, current, result)
        current = current[:len(current)-1]
    }
}
```

---

## 8. GREEDY

### When to Use

- **Local optimal choice leads to global optimal**
- Scheduling problems
- Interval problems
- Minimum spanning tree
- Huffman coding

### Recognition Signals

- Keywords: "maximize", "minimize", "earliest", "latest", "most", "least"
- Sorting often helps
- Can prove that greedy choice is safe

### Greedy vs DP

- **Greedy**: Local choice, no looking back
- **DP**: Consider all choices, optimal substructure

### Example: Jump Game

```rust
// Rust
fn can_jump(nums: Vec<i32>) -> bool {
    let mut max_reach = 0;
    
    for (i, &num) in nums.iter().enumerate() {
        if i > max_reach {
            return false;
        }
        max_reach = max_reach.max(i + num as usize);
        if max_reach >= nums.len() - 1 {
            return true;
        }
    }
    true
}
```

```python
# Python
def can_jump(nums: list[int]) -> bool:
    max_reach = 0
    
    for i, num in enumerate(nums):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + num)
        if max_reach >= len(nums) - 1:
            return True
    
    return True
```

```go
// Go
func canJump(nums []int) bool {
    maxReach := 0
    
    for i, num := range nums {
        if i > maxReach {
            return false
        }
        if i+num > maxReach {
            maxReach = i + num
        }
        if maxReach >= len(nums)-1 {
            return true
        }
    }
    return true
}
```

---

## 9. GRAPH ALGORITHMS

### When to Use

- Relationships between entities
- Networks, dependencies, paths
- Social networks, map navigation

### Types

#### BFS (Breadth-First Search)

- **Use for**: Shortest path (unweighted), level-order, minimum steps
- **Recognition**: "shortest", "minimum moves", "level by level"

#### DFS (Depth-First Search)

- **Use for**: Path existence, cycles, topological sort, connected components
- **Recognition**: "all paths", "cycle detection", "connected"

### Example: Number of Islands (DFS)

```rust
// Rust
fn num_islands(mut grid: Vec<Vec<char>>) -> i32 {
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut count = 0;
    
    fn dfs(grid: &mut Vec<Vec<char>>, r: usize, c: usize) {
        if r >= grid.len() || c >= grid[0].len() || grid[r][c] == '0' {
            return;
        }
        grid[r][c] = '0';
        dfs(grid, r + 1, c);
        if r > 0 { dfs(grid, r - 1, c); }
        dfs(grid, r, c + 1);
        if c > 0 { dfs(grid, r, c - 1); }
    }
    
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == '1' {
                count += 1;
                dfs(&mut grid, r, c);
            }
        }
    }
    count
}
```

```python
# Python
def num_islands(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    count = 0
    
    def dfs(r: int, c: int):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return
        grid[r][c] = '0'
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    
    return count
```

```go
// Go
func numIslands(grid [][]byte) int {
    if len(grid) == 0 {
        return 0
    }
    
    rows, cols := len(grid), len(grid[0])
    count := 0
    
    var dfs func(r, c int)
    dfs = func(r, c int) {
        if r < 0 || r >= rows || c < 0 || c >= cols || grid[r][c] == '0' {
            return
        }
        grid[r][c] = '0'
        dfs(r+1, c)
        dfs(r-1, c)
        dfs(r, c+1)
        dfs(r, c-1)
    }
    
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            if grid[r][c] == '1' {
                count++
                dfs(r, c)
            }
        }
    }
    return count
}
```

---

## 10. BINARY SEARCH

### When to Use

- **Sorted array** (or can be modeled as sorted)
- Search in O(log n)
- Finding boundaries
- Optimization problems on monotonic functions

### Recognition Signals

- Keywords: "sorted", "find", "search"
- Need better than O(n)
- Answer space is ordered/monotonic

### Types

- **Find exact value**
- **Find first/last occurrence**
- **Binary search on answer** (for optimization)

### Example: Binary Search on Answer

```rust
// Rust - Find minimum in rotated sorted array
fn find_min(nums: Vec<i32>) -> i32 {
    let (mut left, mut right) = (0, nums.len() - 1);
    
    while left < right {
        let mid = left + (right - left) / 2;
        if nums[mid] > nums[right] {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    nums[left]
}
```

```python
# Python
def find_min(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    
    return nums[left]
```

```go
// Go
func findMin(nums []int) int {
    left, right := 0, len(nums)-1
    
    for left < right {
        mid := left + (right-left)/2
        if nums[mid] > nums[right] {
            left = mid + 1
        } else {
            right = mid
        }
    }
    return nums[left]
}
```

---

## Pattern Combination Decision Tree

```
Problem Analysis
├─ Need ALL solutions? → BACKTRACKING
├─ Optimization (min/max/count)?
│  ├─ Overlapping subproblems? → DYNAMIC PROGRAMMING
│  └─ Local optimal = global? → GREEDY
├─ Search in sorted space? → BINARY SEARCH
├─ Contiguous subarray/substring? → SLIDING WINDOW
├─ Need fast lookup? → HASH TABLE
├─ Matching/nesting? → STACK
├─ Two endpoints? → TWO POINTERS
├─ Graph/tree structure? → DFS/BFS
└─ Can break into subproblems? → RECURSION
```

---

## Quick Reference: Time & Space Complexity

| Pattern | Time | Space | When Space Matters |
|---------|------|-------|-------------------|
| Two Pointers | O(n) | O(1) | Always optimal |
| Sliding Window | O(n) | O(k) | Use when contiguous |
| Hash Table | O(n) | O(n) | Trade space for speed |
| Stack | O(n) | O(n) | LIFO operations |
| Recursion | O(2^n) typical | O(n) stack | Avoid if iterative possible |
| DP Memoization | O(n×m) | O(n×m) | Top-down approach |
| DP Tabulation | O(n×m) | O(n×m) | Bottom-up, can optimize |
| Backtracking | O(2^n) | O(n) | Generate all solutions |
| Greedy | O(n log n) | O(1) | Prove correctness |
| BFS | O(V+E) | O(V) | Shortest path |
| DFS | O(V+E) | O(V) | Path finding |
| Binary Search | O(log n) | O(1) | Sorted input |

---

## Elite Problem-Solving Workflow

1. **Understand**: Read twice, identify input/output, constraints
2. **Pattern Match**: Use recognition signals above
3. **Brute Force First**: Get correct solution
4. **Optimize**: Apply appropriate pattern
5. **Edge Cases**: Empty, single element, duplicates, negatives
6. **Test**: Walk through with example
7. **Analyze**: Time and space complexity

---

## Common Pattern Combinations

1. **Sliding Window + Hash Table**: Longest substring without repeating characters
2. **DFS + Memoization**: Tree problems with repeated subtrees
3. **Binary Search + Greedy**: Capacity to ship packages
4. **Two Pointers + Hash Table**: Three sum problem
5. **BFS + Hash Table**: Word ladder
6. **DP + Binary Search**: Longest increasing subsequence (O(n log n))
7. **Backtracking + Pruning**: N-Queens with early termination

---

## Pro Tips

1. **Always start with brute force** - get correctness first
2. **Draw it out** - visualize the problem
3. **Look for sorted property** - enables binary search
4. **Count frequency?** - probably need hash table
5. **All combinations?** - likely backtracking
6. **Optimal substructure?** - check for DP
7. **Can you sort?** - often unlocks simpler solutions
8. **Space-time tradeoff** - hash tables trade space for speed
9. **Monotonic property** - enables binary search on answer
10. **Practice pattern recognition** - the more you see, the faster you identify

---

## Key Insight

> **The pattern is not about the data structure alone, but about the PROBLEM STRUCTURE:**

> - Recursion is about problem decomposition
> - DP is about overlapping subproblems
> - Greedy is about optimal local choices
> - Backtracking is about exploring all paths
> - The data structure (array, hash, stack) is just the tool to implement the pattern.

I'll create a comprehensive pattern recognition guide for elite software engineers. This will help you instantly identify which algorithmic approach to use for any problem.I've created a comprehensive pattern recognition guide for you! This is the framework elite engineers use to instantly identify the right approach.

## Key Insights to Master:

### **The Recognition Hierarchy**

1. **First**: Look for the data structure (sorted → binary search, contiguous → sliding window)
2. **Second**: Identify the problem type (optimization → DP/Greedy, all solutions → backtracking)
3. **Third**: Check constraints (time limits, space limits)

### **The 5-Second Pattern Test**

Ask yourself:

- Is it sorted? → **Binary Search or Two Pointers**
- Is it contiguous? → **Sliding Window**
- Need all answers? → **Backtracking**
- Need optimal answer with choices? → **DP or Greedy**
- Need fast lookup? → **Hash Table**

### **Real-World Mapping**

- **Navigation systems** → Graph (Dijkstra/A*)
- **Flight routes** → Graph (Dijkstra)
- **Social network connections** → Graph (BFS/DFS)
- **Rate limiting/caching** → Hash Table + Queue
- **Autocomplete** → Trie (specialized tree)
- **Load balancing** → Heap + Hash Table
- **Undo functionality** → Stack
- **Shortest path in maps** → BFS/Dijkstra
- **Dependency resolution** → Topological Sort (DFS)
- **Data pipelines** → Sliding Window

### **The Debug Checklist**

When stuck:

1. Did you consider the sorted property?
2. Can you trade space for time?
3. Is there a greedy choice?
4. Are you recalculating the same thing? (memoize it)
5. Can you use two pointers instead of nested loops?

### **Language-Specific Notes**

- **Rust**: Ownership helps prevent bugs but requires careful borrowing in recursive solutions
- **Python**: Clean syntax, use `collections` module heavily (defaultdict, Counter, deque)
- **Go**: Explicit but fast, remember to handle slice/map initialization carefully

The guide includes working examples in all three languages for each pattern. Practice recognizing the signals, and you'll solve problems 10x faster! 🚀

This is the **holy grail question** of problem solving, Sushin: *how do elite engineers know which paradigm to reach for—recursion, DP, backtracking, greedy, hash tables, sliding window, arrays, matrices, or combinations?*  

Let’s build a **battle-tested guide** that you can use as a **decision compass** in real-world coding.  

---

## Elite Software Engineer's DSA Pattern Recognition Guide

## 🎯 Core Philosophy

**Pattern recognition in problem-solving is about mapping problem characteristics to algorithmic approaches, not memorizing solutions.**

---

## 📋 Table of Contents

1. [Keyword → Pattern Mapping](#keyword-pattern-mapping)
2. [Problem Classification Framework](#problem-classification-framework)
3. [Pattern Recognition Checklist](#pattern-recognition-checklist)
4. [Essential Patterns with Implementations](#essential-patterns)
5. [Decision Trees](#decision-trees)
6. [Real-World Problem Mappings](#real-world-mappings)

---

## 🔑 Keyword → Pattern Mapping

### **Array/Sequence Keywords**

| Keywords | Pattern | Data Structure | Time Complexity |
|----------|---------|----------------|-----------------|
| "subarray sum", "contiguous elements" | Sliding Window / Prefix Sum | Array, HashMap | O(n) |
| "k largest/smallest", "top k" | Heap / QuickSelect | Heap, Priority Queue | O(n log k) |
| "merge sorted", "k-way merge" | Merge K Sorted | Min Heap | O(n log k) |
| "find pair/triplet sum" | Two Pointers / HashMap | HashMap, Sorted Array | O(n) to O(n²) |
| "longest sequence", "substring without repeating" | Sliding Window | HashMap, Set | O(n) |
| "maximum/minimum in range" | Monotonic Stack/Queue | Deque, Stack | O(n) |

### **Graph/Tree Keywords**

| Keywords | Pattern | Algorithm | Time Complexity |
|----------|---------|-----------|-----------------|
| "shortest path", "minimum cost" | BFS / Dijkstra / Bellman-Ford | Graph Traversal | O(V+E) to O(V²) |
| "all paths", "detect cycle" | DFS / Backtracking | Graph Traversal | O(V+E) |
| "minimum spanning tree" | Kruskal / Prim | Union-Find, Heap | O(E log V) |
| "topological order", "prerequisites" | Topological Sort | DFS / BFS + In-degree | O(V+E) |
| "connected components" | Union-Find / DFS | Union-Find | O(n α(n)) |
| "lowest common ancestor" | Binary Lifting / Tarjan | Tree DP | O(log n) per query |
| "level-order", "breadth-first" | BFS | Queue | O(n) |

### **Dynamic Programming Keywords**

| Keywords | Pattern | Approach | Time Complexity |
|----------|---------|----------|-----------------|
| "optimize", "maximize/minimize", "count ways" | DP | Memoization / Tabulation | Varies |
| "knapsack", "subset sum", "partition" | 0/1 or Unbounded Knapsack | DP Array | O(n × capacity) |
| "longest common", "edit distance" | String DP | 2D DP | O(n × m) |
| "best time to", "stock prices" | State Machine DP | 1D/2D DP | O(n) |
| "coin change", "ways to make" | Unbounded Knapsack | DP Array | O(n × amount) |
| "break into words", "valid partition" | String DP + Trie | DP + DFS | O(n²) |

### **Search & Sort Keywords**

| Keywords | Pattern | Technique | Time Complexity |
|----------|---------|-----------|-----------------|
| "sorted array", "search in rotated" | Binary Search | Modified BS | O(log n) |
| "kth element", "median" | QuickSelect / Heap | Partitioning | O(n) average |
| "find peak", "local maximum" | Binary Search | Modified BS | O(log n) |
| "search in 2D matrix" | Binary Search | Row-wise + BS | O(log(m×n)) |
| "frequency counting", "most common" | HashMap / Counting Sort | Hash Table | O(n) |

### **String Keywords**

| Keywords | Pattern | Algorithm | Time Complexity |
|----------|---------|-----------|-----------------|
| "pattern matching", "find substring" | KMP / Rabin-Karp | String Matching | O(n+m) |
| "palindrome", "longest palindromic" | Expand from Center / Manacher | String DP | O(n²) or O(n) |
| "anagram", "permutation" | Sliding Window + HashMap | Hash Table | O(n) |
| "prefix matching", "autocomplete" | Trie | Trie | O(m) per operation |
| "lexicographic order" | DFS / Sorting | Backtracking | Varies |

### **Design Keywords**

| Keywords | Data Structure | Use Case |
|----------|----------------|----------|
| "LRU cache", "least recently used" | HashMap + Doubly Linked List | O(1) operations |
| "range queries", "update range" | Segment Tree / Fenwick Tree | O(log n) operations |
| "insert/delete/getRandom" | HashMap + Array | O(1) operations |
| "stream of data", "running median" | Two Heaps | O(log n) insert |
| "autocomplete", "prefix search" | Trie | O(m) search |
| "time-based", "version control" | TreeMap / Binary Search | O(log n) lookup |

---

## 🧩 Problem Classification Framework

### **1. Input Characteristics**

```
└─ Data Structure?
   ├─ Array/List
   │  ├─ Sorted? → Binary Search, Two Pointers
   │  ├─ Unsorted? → Sorting, HashMap, Sliding Window
   │  └─ Contains duplicates? → Set operations, Frequency counting
   │
   ├─ String
   │  ├─ Pattern matching? → KMP, Rabin-Karp
   │  ├─ Subsequence? → DP, Two Pointers
   │  └─ Transformation? → DP (Edit Distance)
   │
   ├─ Graph/Tree
   │  ├─ Weighted? → Dijkstra, Bellman-Ford, Prim
   │  ├─ Unweighted? → BFS, DFS
   │  ├─ Directed? → Topological Sort, SCC
   │  └─ Tree? → DFS, BFS, Tree DP
   │
   └─ Matrix/Grid
      ├─ Path finding? → BFS, DFS, Dijkstra
      ├─ Island counting? → DFS, Union-Find
      └─ Range queries? → 2D Prefix Sum, Sparse Table
```

### **2. Problem Type Classification**

**Optimization Problems**

- **Keywords**: maximize, minimize, optimal, best
- **Approach**: DP, Greedy, Binary Search on Answer
- **Questions to ask**:
  - Can I break it into subproblems? → DP
  - Does greedy choice work? → Greedy
  - Can I optimize brute force? → Pruning, Memoization

**Counting Problems**

- **Keywords**: count ways, number of, how many
- **Approach**: DP, Combinatorics, Math
- **Questions to ask**:
  - Is order important? → Permutations vs Combinations
  - Are there constraints? → DP with state
  - Can I use math formula? → Direct calculation

**Search Problems**

- **Keywords**: find, search, exists, locate
- **Approach**: Binary Search, DFS, BFS, Hashing
- **Questions to ask**:
  - Is input sorted? → Binary Search
  - Need all occurrences? → Complete search
  - Need just existence? → Hashing, Early termination

**Construction Problems**

- **Keywords**: build, construct, generate, create
- **Approach**: Backtracking, Greedy, Simulation
- **Questions to ask**:
  - Need all solutions? → Backtracking
  - One valid solution? → Greedy/Constructive
  - Specific order? → Topological Sort, Simulation

---

## ✅ Pattern Recognition Checklist

### **Before Coding - Ask These Questions**

1. **What are the constraints?**
   - n ≤ 20: O(2ⁿ) - Backtracking, Bitmask DP
   - n ≤ 100: O(n³) or O(n⁴) - Cubic algorithms
   - n ≤ 1,000: O(n²) - Nested loops acceptable
   - n ≤ 100,000: O(n log n) - Sorting, Heap, Divide & Conquer
   - n ≤ 1,000,000: O(n) - Linear algorithms only
   - n ≤ 10⁹: O(log n) or O(1) - Binary Search, Math

2. **What's the output?**
   - Single value? → Optimization, Search
   - Count? → DP, Combinatorics
   - Collection? → Backtracking, Construction
   - Yes/No? → Greedy, Validation

3. **Is there a simpler brute force?**
   - Can I enumerate all solutions? → Start here, then optimize
   - What's preventing me? → Identify bottleneck

4. **Can I transform the problem?**
   - Reverse the problem?
   - Solve for complement?
   - Change representation? (Graph → Matrix, Array → Tree)

5. **What state do I need to track?**
   - Position? → Index-based DP
   - Multiple dimensions? → Multi-dimensional DP
   - Previous choices? → State machine DP

---

## 💎 Essential Patterns with Implementations

### **Pattern 1: Sliding Window**

**Use When**: Contiguous subarray/substring, "maximum/minimum in window"

**Python**

```python
def max_sum_subarray(arr, k):
    """Maximum sum of subarray of size k"""
    if len(arr) < k:
        return 0
    
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

def longest_substring_without_repeating(s):
    """Longest substring without repeating characters"""
    char_index = {}
    max_length = start = 0
    
    for end, char in enumerate(s):
        if char in char_index and char_index[char] >= start:
            start = char_index[char] + 1
        char_index[char] = end
        max_length = max(max_length, end - start + 1)
    
    return max_length
```

**Rust**

```rust
use std::collections::HashMap;

fn max_sum_subarray(arr: &[i32], k: usize) -> i32 {
    if arr.len() < k {
        return 0;
    }
    
    let mut window_sum: i32 = arr[..k].iter().sum();
    let mut max_sum = window_sum;
    
    for i in k..arr.len() {
        window_sum += arr[i] - arr[i - k];
        max_sum = max_sum.max(window_sum);
    }
    
    max_sum
}

fn longest_substring_without_repeating(s: &str) -> usize {
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_length = 0;
    let mut start = 0;
    
    for (end, ch) in s.chars().enumerate() {
        if let Some(&idx) = char_index.get(&ch) {
            if idx >= start {
                start = idx + 1;
            }
        }
        char_index.insert(ch, end);
        max_length = max_length.max(end - start + 1);
    }
    
    max_length
}
```

**Go**

```go
func maxSumSubarray(arr []int, k int) int {
    if len(arr) < k {
        return 0
    }
    
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += arr[i]
    }
    
    maxSum := windowSum
    for i := k; i < len(arr); i++ {
        windowSum += arr[i] - arr[i-k]
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    
    return maxSum
}

func longestSubstringWithoutRepeating(s string) int {
    charIndex := make(map[rune]int)
    maxLength := 0
    start := 0
    
    for end, ch := range s {
        if idx, found := charIndex[ch]; found && idx >= start {
            start = idx + 1
        }
        charIndex[ch] = end
        if length := end - start + 1; length > maxLength {
            maxLength = length
        }
    }
    
    return maxLength
}
```

---

### **Pattern 2: Two Pointers**

**Use When**: Sorted array, pair finding, palindrome checking

**Python**

```python
def two_sum_sorted(arr, target):
    """Find pair with given sum in sorted array"""
    left, right = 0, len(arr) - 1
    
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return [-1, -1]

def remove_duplicates(arr):
    """Remove duplicates from sorted array in-place"""
    if not arr:
        return 0
    
    write = 1
    for read in range(1, len(arr)):
        if arr[read] != arr[read - 1]:
            arr[write] = arr[read]
            write += 1
    
    return write
```

**Rust**

```rust
fn two_sum_sorted(arr: &[i32], target: i32) -> (i32, i32) {
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    while left < right {
        let current_sum = arr[left] + arr[right];
        if current_sum == target {
            return (left as i32, right as i32);
        } else if current_sum < target {
            left += 1;
        } else {
            right -= 1;
        }
    }
    
    (-1, -1)
}

fn remove_duplicates(arr: &mut Vec<i32>) -> usize {
    if arr.is_empty() {
        return 0;
    }
    
    let mut write = 1;
    for read in 1..arr.len() {
        if arr[read] != arr[read - 1] {
            arr[write] = arr[read];
            write += 1;
        }
    }
    
    write
}
```

**Go**

```go
func twoSumSorted(arr []int, target int) [2]int {
    left, right := 0, len(arr)-1
    
    for left < right {
        currentSum := arr[left] + arr[right]
        if currentSum == target {
            return [2]int{left, right}
        } else if currentSum < target {
            left++
        } else {
            right--
        }
    }
    
    return [2]int{-1, -1}
}

func removeDuplicates(arr []int) int {
    if len(arr) == 0 {
        return 0
    }
    
    write := 1
    for read := 1; read < len(arr); read++ {
        if arr[read] != arr[read-1] {
            arr[write] = arr[read]
            write++
        }
    }
    
    return write
}
```

---

### **Pattern 3: Fast & Slow Pointers (Floyd's Cycle Detection)**

**Use When**: Linked list cycle, finding middle, palindrome

**Python**

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def has_cycle(head):
    """Detect cycle in linked list"""
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    
    return False

def find_middle(head):
    """Find middle of linked list"""
    slow = fast = head
    
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    return slow
```

**Rust**

```rust
use std::rc::Rc;
use std::cell::RefCell;

#[derive(Debug)]
struct ListNode {
    val: i32,
    next: Option<Rc<RefCell<ListNode>>>,
}

fn has_cycle(head: Option<Rc<RefCell<ListNode>>>) -> bool {
    let mut slow = head.clone();
    let mut fast = head;
    
    while let (Some(f), Some(f_next)) = (fast.clone(), fast.and_then(|n| n.borrow().next.clone())) {
        slow = slow.and_then(|n| n.borrow().next.clone());
        fast = f_next.borrow().next.clone();
        
        if let (Some(s), Some(f)) = (slow.clone(), fast.clone()) {
            if Rc::ptr_eq(&s, &f) {
                return true;
            }
        }
    }
    
    false
}
```

**Go**

```go
type ListNode struct {
    Val  int
    Next *ListNode
}

func hasCycle(head *ListNode) bool {
    slow, fast := head, head
    
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            return true
        }
    }
    
    return false
}

func findMiddle(head *ListNode) *ListNode {
    slow, fast := head, head
    
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    
    return slow
}
```

---

### **Pattern 4: Binary Search**

**Use When**: Sorted input, "search in O(log n)", optimization problems

**Python**

```python
def binary_search(arr, target):
    """Standard binary search"""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def find_first_occurrence(arr, target):
    """Find first occurrence of target"""
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

def binary_search_on_answer(arr, k):
    """
    Binary search on answer space
    Example: Find minimum capacity to ship packages in k days
    """
    def can_ship(capacity):
        days = 1
        current_load = 0
        for weight in arr:
            if current_load + weight > capacity:
                days += 1
                current_load = weight
            else:
                current_load += weight
        return days <= k
    
    left, right = max(arr), sum(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        if can_ship(mid):
            right = mid
        else:
            left = mid + 1
    
    return left
```

**Rust**

```rust
fn binary_search(arr: &[i32], target: i32) -> i32 {
    let mut left = 0;
    let mut right = arr.len() as i32 - 1;
    
    while left <= right {
        let mid = left + (right - left) / 2;
        match arr[mid as usize].cmp(&target) {
            std::cmp::Ordering::Equal => return mid,
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid - 1,
        }
    }
    
    -1
}

fn find_first_occurrence(arr: &[i32], target: i32) -> i32 {
    let mut left = 0;
    let mut right = arr.len() as i32 - 1;
    let mut result = -1;
    
    while left <= right {
        let mid = left + (right - left) / 2;
        match arr[mid as usize].cmp(&target) {
            std::cmp::Ordering::Equal => {
                result = mid;
                right = mid - 1;
            }
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid - 1,
        }
    }
    
    result
}
```

**Go**

```go
func binarySearch(arr []int, target int) int {
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

func findFirstOccurrence(arr []int, target int) int {
    left, right := 0, len(arr)-1
    result := -1
    
    for left <= right {
        mid := left + (right-left)/2
        if arr[mid] == target {
            result = mid
            right = mid - 1
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    
    return result
}
```

---

### **Pattern 5: Top K Elements (Heap)**

**Use When**: "k largest/smallest", "top k frequent"

**Python**

```python
import heapq

def k_largest_elements(arr, k):
    """Find k largest elements using min heap"""
    if k >= len(arr):
        return arr
    
    # Min heap of size k
    heap = arr[:k]
    heapq.heapify(heap)
    
    for num in arr[k:]:
        if num > heap[0]:
            heapq.heapreplace(heap, num)
    
    return heap

def top_k_frequent(nums, k):
    """Top k frequent elements"""
    from collections import Counter
    count = Counter(nums)
    return [num for num, _ in count.most_common(k)]

def kth_largest(arr, k):
    """Kth largest element - QuickSelect approach"""
    import random
    
    def partition(left, right, pivot_index):
        pivot = arr[pivot_index]
        arr[pivot_index], arr[right] = arr[right], arr[pivot_index]
        store_index = left
        
        for i in range(left, right):
            if arr[i] < pivot:
                arr[store_index], arr[i] = arr[i], arr[store_index]
                store_index += 1
        
        arr[right], arr[store_index] = arr[store_index], arr[right]
        return store_index
    
    def select(left, right, k_smallest):
        if left == right:
            return arr[left]
        
        pivot_index = random.randint(left, right)
        pivot_index = partition(left, right, pivot_index)
        
        if k_smallest == pivot_index:
            return arr[k_smallest]
        elif k_smallest < pivot_index:
            return select(left, pivot_index - 1, k_smallest)
        else:
            return select(pivot_index + 1, right, k_smallest)
    
    return select(0, len(arr) - 1, len(arr) - k)
```

**Rust**

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn k_largest_elements(arr: &[i32], k: usize) -> Vec<i32> {
    if k >= arr.len() {
        return arr.to_vec();
    }
    
    let mut heap = BinaryHeap::new();
    
    for &num in arr {
        if heap.len() < k {
            heap.push(Reverse(num));
        } else if let Some(&Reverse(min)) = heap.peek() {
            if num > min {
                heap.pop();
                heap.push(Reverse(num));
            }
        }
    }
    
    heap.into_iter().map(|Reverse(x)| x).collect()
}
```

**Go**

```go
import (
    "container/heap"
)

type MinHeap []int

func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MinHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func kLargestElements(arr []int, k int) []int {
    if k >= len(arr) {
        return arr
    }
    
    h := &MinHeap{}
    heap.Init(h)
    
    for _, num := range arr {
        if h.Len() < k {
            heap.Push(h, num)
        } else if num > (*h)[0] {
            heap.Pop(h)
            heap.Push(h, num)
        }
    }
    
    result := make([]int, h.Len())
    for i := 0; i < len(result); i++ {
        result[i] = (*h)[i]
    }
    
    return result
}
```

---

### **Pattern 6: Dynamic Programming**

**Use When**: "optimize", "maximize/minimize", "count ways", overlapping subproblems

**Python**

```python
def fibonacci(n):
    """Classic DP example - bottom-up"""
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

def coin_change(coins, amount):
    """Minimum coins to make amount"""
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

def longest_common_subsequence(text1, text2):
    """LCS - 2D DP"""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]

def knapsack_01(weights, values, capacity):
    """0/1 Knapsack problem"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i - 1][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
            else:
                dp[i][w] = dp[i - 1][w]
    
    return dp[n][capacity]
```

**Rust**

```rust
fn fibonacci(n: usize) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    
    let mut dp = vec![0u64; n + 1];
    dp[1] = 1;
    
    for i in 2..=n {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    
    dp[n]
}

fn coin_change(coins: &[i32], amount: i32) -> i32 {
    let mut dp = vec![i32::MAX; (amount + 1) as usize];
    dp[0] = 0;
    
    for i in 1..=amount as usize {
        for &coin in coins {
            if coin as usize <= i && dp[i - coin as usize] != i32::MAX {
                dp[i] = dp[i].min(dp[i - coin as usize] + 1);
            }
        }
    }
    
    if dp[amount as usize] == i32::MAX { -1 } else { dp[amount as usize] }
}

fn longest_common_subsequence(text1: &str, text2: &str) -> usize {
    let (m, n) = (text1.len(), text2.len());
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = dp[i - 1][j].max(dp[i][j - 1]);
            }
        }
    }
    
    dp[m][n]
}
```

**Go**

```go
func fibonacci(n int) int {
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
        dp[i] = amount + 1
    }
    dp[0] = 0
    
    for i := 1; i <= amount; i++ {
        for _, coin := range coins {
            if coin <= i {
                if dp[i-coin]+1 < dp[i] {
                    dp[i] = dp[i-coin] + 1
                }
            }
        }
    }
    
    if dp[amount] > amount {
        return -1
    }
    return dp[amount]
}

func longestCommonSubsequence(text1, text2 string) int {
    m, n := len(text1), len(text2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if text1[i-1] == text2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    
    return dp[m][n]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}
```

---

### **Pattern 7: Graph Traversal (BFS/DFS)**

**Use When**: Graph/tree problems, shortest path, connected components

**Python**

```python
from collections import deque, defaultdict

def bfs_shortest_path(graph, start, end):
    """BFS for shortest path in unweighted graph"""
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        node, path = queue.popleft()
        if node == end:
            return path
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None

def dfs_recursive(graph, node, visited=None):
    """DFS recursive traversal"""
    if visited is None:
        visited = set()
    
    visited.add(node)
    print(node, end=' ')
    
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs_recursive(graph, neighbor, visited)
    
    return visited

def count_islands(grid):
    """Count islands using DFS"""
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    count = 0
    
    def dfs(r, c):
        if (r < 0 or r >= rows or c < 0 or c >= cols or 
            grid[r][c] == '0'):
            return
        
        grid[r][c] = '0'  # Mark as visited
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                dfs(r, c)
                count += 1
    
    return count

def topological_sort(graph, n):
    """Topological sort using DFS"""
    visited = set()
    stack = []
    
    def dfs(node):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)
        stack.append(node)
    
    for i in range(n):
        if i not in visited:
            dfs(i)
    
    return stack[::-1]
```

**Rust**

```rust
use std::collections::{HashMap, HashSet, VecDeque};

fn bfs_shortest_path(
    graph: &HashMap<i32, Vec<i32>>,
    start: i32,
    end: i32
) -> Option<Vec<i32>> {
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    queue.push_back((start, vec![start]));
    visited.insert(start);
    
    while let Some((node, path)) = queue.pop_front() {
        if node == end {
            return Some(path);
        }
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    let mut new_path = path.clone();
                    new_path.push(neighbor);
                    queue.push_back((neighbor, new_path));
                }
            }
        }
    }
    
    None
}

fn count_islands(grid: &mut Vec<Vec<char>>) -> i32 {
    if grid.is_empty() {
        return 0;
    }
    
    let (rows, cols) = (grid.len(), grid[0].len());
    let mut count = 0;
    
    fn dfs(grid: &mut Vec<Vec<char>>, r: i32, c: i32, rows: usize, cols: usize) {
        if r < 0 || r >= rows as i32 || c < 0 || c >= cols as i32 || 
           grid[r as usize][c as usize] == '0' {
            return;
        }
        
        grid[r as usize][c as usize] = '0';
        dfs(grid, r + 1, c, rows, cols);
        dfs(grid, r - 1, c, rows, cols);
        dfs(grid, r, c + 1, rows, cols);
        dfs(grid, r, c - 1, rows, cols);
    }
    
    for r in 0..rows {
        for c in 0..cols {
            if grid[r][c] == '1' {
                dfs(grid, r as i32, c as i32, rows, cols);
                count += 1;
            }
        }
    }
    
    count
}
```

**Go**

```go
func bfsShortestPath(graph map[int][]int, start, end int) []int {
    type item struct {
        node int
        path []int
    }
    
    queue := []item{{start, []int{start}}}
    visited := make(map[int]bool)
    visited[start] = true
    
    for len(queue) > 0 {
        current := queue[0]
        queue = queue[1:]
        
        if current.node == end {
            return current.path
        }
        
        for _, neighbor := range graph[current.node] {
            if !visited[neighbor] {
                visited[neighbor] = true
                newPath := append([]int{}, current.path...)
                newPath = append(newPath, neighbor)
                queue = append(queue, item{neighbor, newPath})
            }
        }
    }
    
    return nil
}

func countIslands(grid [][]byte) int {
    if len(grid) == 0 {
        return 0
    }
    
    rows, cols := len(grid), len(grid[0])
    count := 0
    
    var dfs func(r, c int)
    dfs = func(r, c int) {
        if r < 0 || r >= rows || c < 0 || c >= cols || grid[r][c] == '0' {
            return
        }
        
        grid[r][c] = '0'
        dfs(r+1, c)
        dfs(r-1, c)
        dfs(r, c+1)
        dfs(r, c-1)
    }
    
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            if grid[r][c] == '1' {
                dfs(r, c)
                count++
            }
        }
    }
    
    return count
}
```

---

## 🌳 Decision Trees

### **Choosing Between Approaches**

```
Problem: Find element in array
│
├─ Is array sorted?
│  ├─ YES → Binary Search O(log n)
│  └─ NO → Linear Search O(n) or Hash for multiple queries
│
├─ Need to find multiple elements?
│  ├─ YES → Build HashMap O(n) space, O(1) lookup
│  └─ NO → Single pass sufficient
│
└─ Space constraints?
   ├─ Tight → In-place algorithms
   └─ Flexible → Use extra space for optimization
```

```
Problem: Optimize/Maximize/Minimize
│
├─ Can be broken into subproblems?
│  ├─ YES → Dynamic Programming
│  │  ├─ Overlapping subproblems? → Memoization
│  │  └─ Optimal substructure? → Tabulation
│  │
│  └─ NO → Consider other approaches
│
├─ Does greedy choice work?
│  ├─ YES → Greedy Algorithm
│  │  └─ Always verify with proof/examples
│  │
│  └─ NO → Need exhaustive search
│
└─ Can binary search on answer space?
   ├─ YES → Binary Search on Answer
   └─ NO → Full DP/Backtracking needed
```

---

## 🌍 Real-World Problem Mappings

### **System Design → DSA**

| Real-World Problem | DSA Pattern | Implementation |
|-------------------|-------------|----------------|
| **Rate Limiter** | Sliding Window / Token Bucket | Queue + Timestamp |
| **LRU Cache** | HashMap + Doubly Linked List | O(1) get/put |
| **Autocomplete** | Trie | Prefix tree |
| **URL Shortener** | Hashing | Base62 encoding |
| **Load Balancer** | Consistent Hashing | Hash Ring |
| **File System** | Tree / Graph | DFS for traversal |
| **Task Scheduler** | Priority Queue / Topological Sort | Heap + Dependencies |
| **Database Indexing** | B-Tree / Hash Index | Balanced tree |
| **Social Network** | Graph | BFS for connections |
| **Recommendation** | Collaborative Filtering | Matrix factorization |

### **Backend Engineering → DSA**

| Problem | Pattern | Example |
|---------|---------|---------|
| **API Request Deduplication** | Sliding Window + Hash | Recent requests cache |
| **Database Query Optimization** | Index (B-Tree) | Range queries |
| **Session Management** | LRU Cache | Evict old sessions |
| **Distributed Lock** | Consensus Algorithm | Raft, Paxos |
| **Log Aggregation** | Merge K Sorted | Merge sorted logs |
| **Circuit Breaker** | State Machine | Closed/Open/Half-Open |
| **Job Queue** | Priority Queue | Task prioritization |

### **Frontend Engineering → DSA**

| Problem | Pattern | Example |
|---------|---------|---------|
| **Virtual Scrolling** | Sliding Window | Render visible items |
| **Debounce/Throttle** | Timing + State | Event optimization |
| **Undo/Redo** | Stack | Command pattern |
| **Route Matching** | Trie / Regex | URL routing |
| **State Management** | Graph (State Machine) | Redux, Zustand |
| **DOM Diffing** | Tree Diff Algorithm | React reconciliation |
| **Autocomplete Search** | Trie + Ranking | Search suggestions |

---

## 🎓 Expert Tips

### **1. Pattern Recognition Shortcuts**

- **"All pairs/triplets"** → Usually O(n²) or O(n³), consider if optimization possible
- **"Contiguous"** → Sliding window, Kadane's algorithm
- **"Subsequence" (not contiguous)** → DP
- **"Substring" (contiguous)** → Sliding window
- **"Parentheses/brackets"** → Stack
- **"Nested structures"** → Recursion/Stack
- **"Distance/path"** → BFS (unweighted), Dijkstra (weighted)
- **"In-order/pre-order/post-order"** → Tree traversal patterns

### **2. Complexity Analysis Shortcuts**

- Nested loops over same input → Usually O(n²)
- Loop with halving → O(log n)
- Visiting each element once → O(n)
- Sorting involved → At least O(n log n)
- Recursion with branching → Could be exponential
- Memoization → Reduces to O(states × transition)

### **3. Common Pitfalls**

❌ **Using wrong data structure**: HashMap vs TreeMap (unordered vs ordered)
❌ **Off-by-one errors**: Especially in binary search, sliding window
❌ **Not handling edge cases**: Empty input, single element, duplicates
❌ **Forgetting to check bounds**: Array access, string indices
❌ **Incorrect time complexity**: Hidden operations in loops

### **4. Optimization Strategies**

1. **Brute force first** → Understand the problem
2. **Identify bottleneck** → What takes most time?
3. **Can I avoid recalculation?** → Memoization, prefix sums
4. **Can I trade space for time?** → HashMap, DP table
5. **Can I sort/preprocess?** → Sometimes O(n log n) preprocessing enables O(log n) queries
6. **Can I use better data structure?** → Heap instead of sorting repeatedly

---

## 📚 Study Path for Elite Engineers

### **Phase 1: Foundations (Weeks 1-4)**

- Arrays: Two pointers, sliding window, prefix sum
- Strings: KMP, Rabin-Karp, sliding window
- Hashing: HashMap patterns, frequency counting
- Sorting: QuickSort, MergeSort, counting sort

### **Phase 2: Core Structures (Weeks 5-8)**

- Linked Lists: Fast/slow pointers, reversal
- Stacks & Queues: Monotonic stack, deque
- Trees: DFS, BFS, traversals
- Heaps: Priority queue patterns, k-th element

### **Phase 3: Advanced (Weeks 9-12)**

- Graphs: BFS, DFS, Dijkstra, Union-Find
- Dynamic Programming: 1D, 2D, optimization
- Binary Search: On array, on answer space
- Backtracking: Permutations, combinations, N-Queens

### **Phase 4: Mastery (Weeks 13+)**

- Advanced DP: Bitmask, digit, tree DP
- Advanced Graphs: Bellman-Ford, Floyd-Warshall, MST
- Segment Trees, Fenwick Trees
- Trie, Suffix Arrays
- System design integration

---

## 🔍 Quick Reference Cheat Sheet

```
SORTED ARRAY → Binary Search
TWO SUM → HashMap or Two Pointers (if sorted)
SUBARRAY SUM → Sliding Window or Prefix Sum
K ELEMENTS → Heap (size k) or QuickSelect
SHORTEST PATH → BFS (unweighted) / Dijkstra (weighted)
CONNECTED COMPONENTS → Union-Find or DFS
PARENTHESES → Stack
PALINDROME → Two pointers or Expand from center
ANAGRAM → Sort or Frequency count
TREE TRAVERSAL → DFS (pre/in/post) or BFS (level)
OPTIMIZE → DP or Greedy
COUNT WAYS → DP or Combinatorics
RANGE QUERY → Prefix Sum or Segment Tree
PATTERN MATCH → KMP or Rabin-Karp
PREFIX SEARCH → Trie
```

---

## 💡 Final Wisdom

> **"The key to mastering DSA is not memorizing solutions, but recognizing patterns and understanding why certain approaches work."**

1. **Always start with brute force** - Understand the problem fully
2. **Identify the pattern** - Use this guide's keyword mappings
3. **Consider constraints** - They guide your approach
4. **Think about edge cases** - Empty, single, duplicates, negatives
5. **Analyze complexity** - Time and space trade-offs
6. **Write clean code** - Readable, maintainable, testable
7. **Practice deliberately** - Focus on weak areas

**Remember**: Real-world engineering is about choosing the right tool for the job, not always the most complex one. Simple, maintainable solutions often beat over-engineered ones.

I'll create a comprehensive guide for recognizing DSA patterns and choosing the right approach for real-world problems. This is essential for elite software engineering.I've created a comprehensive guide that elite software engineers can use to master DSA pattern recognition. Here's what makes this guide powerful:

## **Key Features:**

### **1. Keyword Recognition System**

The guide includes extensive tables mapping problem keywords to specific patterns. For example:

- "find duplicate" → Hash Set
- "longest substring" → Sliding Window
- "two sum" → Two Pointers or Hash Map
- "subarray sum" → Sliding Window
- "k largest" → Heap pattern
- "shortest path" → BFS/Dijkstra

### **2. Complete Implementations**

Every pattern includes production-ready code in **Python, Rust, and Go**, covering:

- Arrays/Strings
- Hash Maps/Sets
- Sliding Window (variable and fixed size)
- Two Pointers
- Fast/Slow Pointers
- Binary Search (including "binary search on answer space")
- Top K Elements (Heap and QuickSelect)
- Dynamic Programming (1D, 2D, optimization)
- Graph Traversal (BFS/DFS)

### **3. Decision Framework**

A flowchart-style decision tree helps you choose the right approach based on problem characteristics.
Before coding, the guide teaches you to ask:

- What are the keywords?
- What data structures are implied?
- What are the constraints? (This determines your time complexity target)
- Is the input sorted?
- What type of output is needed?
- Can I transform the problem?

### **4. Real-World Mappings**

It connects DSA to actual engineering:

- **Rate Limiter** → Sliding Window
- **LRU Cache** → HashMap + Doubly Linked List
- **Autocomplete** → Trie
- **Load Balancer** → Consistent Hashing

### **5. Complexity Shortcuts**

Quick rules like:

- n ≤ 20 → Exponential algorithms OK
- n ≤ 10⁶ → Must be O(n) or O(n log n)
- "Contiguous" → Think sliding window
- "Subsequence" → Think DP

The guide emphasizes **pattern recognition over memorization** - teaching you to think like an elite engineer who can quickly identify the right approach for any problem.

## Elite Software Engineer's Guide: Keyword-to-DSA Pattern Recognition

## Table of Contents

1. [Core Pattern Recognition Framework](#core-pattern-recognition-framework)
2. [Keyword Mapping Matrix](#keyword-mapping-matrix)
3. [Domain-Specific Patterns](#domain-specific-patterns)
4. [Decision Framework](#decision-framework)
5. [Implementation Examples](#implementation-examples)

---

## Core Pattern Recognition Framework

### The 3-Step Analysis Method

**Step 1: IDENTIFY - Extract Signal Keywords**

- Data operation keywords (find, sort, count, path, optimize)
- Action verbs (find, count, maximize, minimize, track)
- Constraint words (unique, consecutive, overlapping, distinct)
- Structure hints (tree, graph, sequence, stream, interval)
- Performance requirements (real-time, concurrent, distributed)

**Step 2: CLASSIFY - Map to Pattern Family**

- What data structure fits? (array, linked list, tree, graph, hash)
- What operation dominates? (insert, delete, lookup, update)
- What's the access pattern? (sequential, random, range-based)
- What's the cardinality? (bounded, unbounded, streaming)
- What are the trade-offs? (time vs space, consistency vs availability)

**Step 3: OPTIMIZE - Select Best-Fit DSA**

- Analyze time/space complexity needs
- Consider your domain constraints
- Evaluate concurrency requirements
- Assess scalability needs
- Factor in operational complexity

---

## Keyword Mapping Matrix

### 🔍 Search & Retrieval Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **find, search, lookup, query** | Hash Map/Set | O(1) lookups needed | O(1) avg |
| **find in sorted, binary search** | Binary Search, B-Tree | Sorted data queries | O(log n) |
| **find nearest, closest** | KD-Tree, Ball Tree | Spatial/metric queries | O(log n) |
| **find top-k, k-largest** | Heap, Priority Queue | Bounded ranking | O(n log k) |
| **find pattern, substring** | KMP, Rabin-Karp, Aho-Corasick | String matching | O(n+m) |
| **find cycle, detect loop** | Floyd's Cycle, Union-Find | Graph cycles | O(n) |

### 📊 Ordering & Ranking Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **sort, order, arrange** | QuickSort, MergeSort, Radix | General sorting | O(n log n) |
| **maintain sorted, dynamic sort** | Balanced BST, Heap | Online sorting | O(log n) insert |
| **rank, kth element** | QuickSelect, Median of Medians | Order statistics | O(n) avg |
| **priority, schedule, deadline** | Priority Queue, Heap | Task scheduling | O(log n) |
| **median, percentile** | Two Heaps, Order Statistics Tree | Streaming statistics | O(log n) |

### 🔢 Counting & Frequency Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **count, frequency, occurrence** | Hash Map, Counter | Frequency tracking | O(1) per op |
| **count unique, distinct** | Hash Set, Bloom Filter | Cardinality estimation | O(1) / approx |
| **count inversions** | Modified MergeSort, BIT | Array analysis | O(n log n) |
| **rolling count, sliding window** | Deque, Hash Map | Window statistics | O(1) amortized |

### 🌐 Graph & Network Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **path, route, navigate** | BFS, DFS, Dijkstra, A* | Path finding | O(V+E) to O(E log V) |
| **shortest path, minimum cost** | Dijkstra, Bellman-Ford, Floyd-Warshall | Network routing | O(E log V) to O(V³) |
| **connectivity, reachability** | Union-Find, DFS/BFS | Network components | O(α(n)) |
| **flow, capacity, bandwidth** | Max-Flow (Ford-Fulkerson, Dinic) | Network optimization | O(V²E) |
| **dependency, topological** | Topological Sort, Kahn's Algorithm | Build systems, task ordering | O(V+E) |
| **spanning tree, minimum connection** | Kruskal's, Prim's | Network design | O(E log V) |
| **strongly connected** | Tarjan's, Kosaraju's | Network analysis | O(V+E) |

### 🔄 Stream & Sequence Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **stream, continuous, real-time** | Sliding Window, Reservoir Sampling | Online processing | O(1) per element |
| **consecutive, continuous, subarray** | Sliding Window, Kadane's | Contiguous sequences | O(n) |
| **subsequence, subset** | DP, Two Pointers | Non-contiguous patterns | O(n²) or O(n) |
| **prefix, suffix** | Prefix Sum, Trie | Range queries | O(1) query |
| **interval, range, segment** | Segment Tree, Interval Tree | Range operations | O(log n) |

### 🎯 Optimization Keywords

| Keywords | DSA Pattern | Use Case | Time Complexity |
|----------|-------------|----------|-----------------|
| **maximize, minimize, optimal** | Dynamic Programming, Greedy | Optimization problems | O(n²) or O(n) |
| **knapsack, capacity, weight** | DP (0/1 or Unbounded) | Resource allocation | O(nW) |
| **partition, distribute, balance** | DP, Greedy, Load Balancing | Distribution problems | Varies |
| **schedule, assign, allocate** | Greedy, Hungarian Algorithm | Assignment problems | O(n³) |

### 🔒 Security & Concurrency Keywords

| Keywords | DSA Pattern | Use Case | Notes |
|----------|-------------|----------|-------|
| **concurrent, parallel, thread-safe** | Lock-Free DS, RWLock, Mutex | Concurrent access | Use concurrent collections |
| **rate-limit, throttle, quota** | Token Bucket, Leaky Bucket | Rate limiting | O(1) check |
| **cache, memoize, expire** | LRU/LFU Cache, TTL Map | Caching strategies | O(1) ops |
| **access control, permission** | Trie, Hash Map, RBAC Tree | Authorization | O(log n) or O(1) |
| **audit, log, trace** | Append-Only Log, Ring Buffer | Monitoring | O(1) append |
| **isolation, sandbox, namespace** | Tree (hierarchical), Graph | Resource isolation | Domain-specific |

### 🌍 Distributed Systems Keywords

| Keywords | DSA Pattern | Use Case | CAP Trade-off |
|----------|-------------|----------|---------------|
| **distributed, replicated, consistent** | Consensus (Raft, Paxos), CRDT | Distributed coordination | CP or AP |
| **shard, partition, horizontal** | Consistent Hashing, Range Partitioning | Data distribution | Availability |
| **gossip, epidemic, eventual** | Gossip Protocol, Merkle Tree | Eventual consistency | AP |
| **quorum, majority, consensus** | Quorum-based algorithms | Strong consistency | CP |
| **vector clock, causal** | Vector Clocks, Lamport Timestamps | Ordering events | Causality |

---

## Domain-Specific Patterns

### ☁️ Cloud & Infrastructure

#### Resource Management

- **Problem**: VM allocation with resource constraints
- **Keywords**: allocate, capacity, constraint, optimize
- **Pattern**: Bin Packing (First-Fit, Best-Fit) + Priority Queue
- **DSA**: Heap + Greedy Algorithm

#### Load Balancing

- **Problem**: Distribute requests across servers
- **Keywords**: balance, distribute, weight, health
- **Pattern**: Consistent Hashing + Weighted Round Robin
- **DSA**: Hash Ring + Priority Queue

#### Auto-scaling

- **Problem**: Scale resources based on metrics
- **Keywords**: threshold, monitor, scale, trend
- **Pattern**: Time Series Analysis + Sliding Window
- **DSA**: Circular Buffer + Moving Average

### 🌐 Networking

#### Packet Routing

- **Problem**: Route packets through network
- **Keywords**: route, path, latency, hop
- **Pattern**: Shortest Path with Constraints
- **DSA**: Dijkstra's with modifications, A*

#### Traffic Shaping

- **Problem**: Control bandwidth usage
- **Keywords**: rate, bandwidth, burst, limit
- **Pattern**: Token Bucket + Leaky Bucket
- **DSA**: Queue + Counter

#### DNS Resolution

- **Problem**: Resolve domain names efficiently
- **Keywords**: lookup, cache, TTL, hierarchy
- **Pattern**: Multi-level Cache + Trie
- **DSA**: LRU Cache + Trie

### 🔐 Security

#### Firewall Rules

- **Problem**: Match packets against rules efficiently
- **Keywords**: match, filter, rule, priority
- **Pattern**: Rule Matching + Priority Ordering
- **DSA**: Trie (for IP prefixes), Priority Queue

#### Intrusion Detection

- **Problem**: Detect anomalous patterns
- **Keywords**: pattern, anomaly, threshold, signature
- **Pattern**: Pattern Matching + Statistical Analysis
- **DSA**: Aho-Corasick, Bloom Filter, Sliding Window

#### Access Control

- **Problem**: Check permissions efficiently
- **Keywords**: permission, role, hierarchy, grant
- **Pattern**: RBAC Tree + Bitset
- **DSA**: Tree (for role hierarchy), Hash Map

### 📦 Sandboxing & Virtualization

#### Resource Isolation

- **Problem**: Isolate resource access
- **Keywords**: isolate, namespace, limit, quota
- **Pattern**: Hierarchical Namespaces + Resource Tracking
- **DSA**: Tree + Hash Map

#### Process Management

- **Problem**: Schedule and track processes
- **Keywords**: schedule, priority, deadline, preempt
- **Pattern**: Multi-level Feedback Queue
- **DSA**: Priority Queue + Round Robin

---

## Decision Framework

### The CASER Framework

**C - Constraints**

- What are the size limits? (n < 10³, 10⁶, 10⁹?)
- What are the time limits? (real-time, batch, interactive?)
- What are the space limits? (memory-constrained, distributed?)

**A - Access Pattern**

- Random or sequential?
- Read-heavy or write-heavy?
- Point queries or range queries?

**S - Scalability**

- Single-threaded or concurrent?
- Single-node or distributed?
- Static or dynamic data?

**E - Error Tolerance**

- Exact or approximate?
- Best-effort or guaranteed?
- Fault-tolerant requirements?

**R - Requirements**

- Latency requirements (p50, p95, p99)?
- Throughput requirements?
- Consistency requirements?

---

## Implementation Examples

### Example 1: Rate Limiter (Token Bucket)

**Keywords**: rate-limit, requests-per-second, burst, throttle
**Pattern**: Token Bucket Algorithm
**Use Case**: API rate limiting in cloud services

#### Rust Implementation

```rust
use std::time::{Duration, Instant};
use std::sync::{Arc, Mutex};

struct TokenBucket {
    capacity: u32,
    tokens: f64,
    rate: f64, // tokens per second
    last_refill: Instant,
}

impl TokenBucket {
    fn new(capacity: u32, rate: f64) -> Self {
        Self {
            capacity,
            tokens: capacity as f64,
            rate,
            last_refill: Instant::now(),
        }
    }

    fn refill(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        
        self.tokens = (self.tokens + elapsed * self.rate).min(self.capacity as f64);
        self.last_refill = now;
    }

    fn try_consume(&mut self, tokens: u32) -> bool {
        self.refill();
        
        if self.tokens >= tokens as f64 {
            self.tokens -= tokens as f64;
            true
        } else {
            false
        }
    }
}

// Thread-safe version
type SafeTokenBucket = Arc<Mutex<TokenBucket>>;

fn create_rate_limiter(capacity: u32, rate: f64) -> SafeTokenBucket {
    Arc::new(Mutex::new(TokenBucket::new(capacity, rate)))
}

// Usage
fn handle_request(limiter: &SafeTokenBucket) -> Result<(), &'static str> {
    let mut bucket = limiter.lock().unwrap();
    if bucket.try_consume(1) {
        Ok(())
    } else {
        Err("Rate limit exceeded")
    }
}
```

#### Python Implementation

```python
import time
import threading
from typing import Optional

class TokenBucket:
    def __init__(self, capacity: int, rate: float):
        """
        capacity: maximum tokens
        rate: tokens per second
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.rate = rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_refill = now
    
    def try_consume(self, tokens: int = 1) -> bool:
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1) -> None:
        """Blocking call that waits until tokens available"""
        while not self.try_consume(tokens):
            time.sleep(0.01)

# Usage for API rate limiting
class APIRateLimiter:
    def __init__(self, requests_per_second: int, burst: int):
        self.bucket = TokenBucket(burst, requests_per_second)
    
    def allow_request(self) -> bool:
        return self.bucket.try_consume(1)

# Example usage
limiter = APIRateLimiter(requests_per_second=100, burst=150)

def handle_api_request():
    if limiter.allow_request():
        # Process request
        return {"status": "success"}
    else:
        return {"status": "rate_limited", "error": "Too many requests"}
```

#### Go Implementation

```go
package main

import (
    "sync"
    "time"
)

type TokenBucket struct {
    capacity    float64
    tokens      float64
    rate        float64 // tokens per second
    lastRefill  time.Time
    mu          sync.Mutex
}

func NewTokenBucket(capacity int, rate float64) *TokenBucket {
    return &TokenBucket{
        capacity:   float64(capacity),
        tokens:     float64(capacity),
        rate:       rate,
        lastRefill: time.Now(),
    }
}

func (tb *TokenBucket) refill() {
    now := time.Now()
    elapsed := now.Sub(tb.lastRefill).Seconds()
    
    tb.tokens = min(tb.capacity, tb.tokens+elapsed*tb.rate)
    tb.lastRefill = now
}

func (tb *TokenBucket) TryConsume(tokens int) bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()
    
    tb.refill()
    
    if tb.tokens >= float64(tokens) {
        tb.tokens -= float64(tokens)
        return true
    }
    return false
}

func min(a, b float64) float64 {
    if a < b {
        return a
    }
    return b
}

// Middleware example
func RateLimitMiddleware(limiter *TokenBucket) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if !limiter.TryConsume(1) {
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}
```

---

### Example 2: LRU Cache with TTL (Cloud Caching)

**Keywords**: cache, expire, evict, most-recent, TTL
**Pattern**: LRU Cache + Time-based Expiration
**Use Case**: DNS caching, API response caching

#### Rust Implementation

```rust
use std::collections::{HashMap, VecDeque};
use std::time::{Duration, Instant};
use std::hash::Hash;

struct CacheEntry<V> {
    value: V,
    expires_at: Instant,
}

struct LRUCache<K, V> {
    capacity: usize,
    cache: HashMap<K, CacheEntry<V>>,
    order: VecDeque<K>,
    default_ttl: Duration,
}

impl<K: Eq + Hash + Clone, V: Clone> LRUCache<K, V> {
    fn new(capacity: usize, default_ttl: Duration) -> Self {
        Self {
            capacity,
            cache: HashMap::new(),
            order: VecDeque::new(),
            default_ttl,
        }
    }

    fn get(&mut self, key: &K) -> Option<V> {
        // Check if key exists and not expired
        if let Some(entry) = self.cache.get(key) {
            if Instant::now() < entry.expires_at {
                // Move to front (most recently used)
                self.order.retain(|k| k != key);
                self.order.push_front(key.clone());
                return Some(entry.value.clone());
            } else {
                // Expired, remove it
                self.cache.remove(key);
                self.order.retain(|k| k != key);
            }
        }
        None
    }

    fn put(&mut self, key: K, value: V) {
        self.put_with_ttl(key, value, self.default_ttl);
    }

    fn put_with_ttl(&mut self, key: K, value: V, ttl: Duration) {
        // Remove if already exists
        if self.cache.contains_key(&key) {
            self.order.retain(|k| k != &key);
        } else if self.cache.len() >= self.capacity {
            // Evict LRU item
            if let Some(lru_key) = self.order.pop_back() {
                self.cache.remove(&lru_key);
            }
        }

        let entry = CacheEntry {
            value,
            expires_at: Instant::now() + ttl,
        };

        self.cache.insert(key.clone(), entry);
        self.order.push_front(key);
    }

    fn cleanup_expired(&mut self) {
        let now = Instant::now();
        let expired: Vec<K> = self.cache
            .iter()
            .filter(|(_, entry)| now >= entry.expires_at)
            .map(|(k, _)| k.clone())
            .collect();

        for key in expired {
            self.cache.remove(&key);
            self.order.retain(|k| k != &key);
        }
    }
}

// Usage for DNS caching
fn dns_cache_example() {
    let mut cache = LRUCache::new(1000, Duration::from_secs(300));
    
    // Cache DNS response
    cache.put("example.com".to_string(), "93.184.216.34".to_string());
    
    // Retrieve
    if let Some(ip) = cache.get(&"example.com".to_string()) {
        println!("Cached IP: {}", ip);
    }
}
```

#### Python Implementation

```python
from collections import OrderedDict
from typing import Optional, Generic, TypeVar, Any
import time

K = TypeVar('K')
V = TypeVar('V')

class LRUCache(Generic[K, V]):
    def __init__(self, capacity: int, default_ttl: float = 300):
        """
        capacity: maximum number of items
        default_ttl: time-to-live in seconds
        """
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache: OrderedDict[K, tuple[V, float]] = OrderedDict()
    
    def get(self, key: K) -> Optional[V]:
        if key not in self.cache:
            return None
        
        value, expires_at = self.cache[key]
        
        # Check expiration
        if time.time() > expires_at:
            del self.cache[key]
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return value
    
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        if key in self.cache:
            # Update existing
            del self.cache[key]
        elif len(self.cache) >= self.capacity:
            # Evict LRU (first item)
            self.cache.popitem(last=False)
        
        self.cache[key] = (value, expires_at)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed"""
        now = time.time()
        expired = [k for k, (_, exp) in self.cache.items() if now > exp]
        for key in expired:
            del self.cache[key]
        return len(expired)

# Decorator for function result caching
def cached_with_ttl(cache: LRUCache, ttl: Optional[float] = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from args
            key = (args, tuple(sorted(kwargs.items())))
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.put(key, result, ttl)
            return result
        return wrapper
    return decorator

# Usage example: DNS resolver with caching
class DNSResolver:
    def __init__(self):
        self.cache = LRUCache[str, str](capacity=10000, default_ttl=300)
    
    def resolve(self, domain: str) -> Optional[str]:
        # Check cache
        cached = self.cache.get(domain)
        if cached:
            return cached
        
        # Actual DNS resolution (simulated)
        ip = self._actual_dns_lookup(domain)
        if ip:
            self.cache.put(domain, ip, ttl=300)
        return ip
    
    def _actual_dns_lookup(self, domain: str) -> Optional[str]:
        # Placeholder for actual DNS resolution
        import socket
        try:
            return socket.gethostbyname(domain)
        except:
            return None
```

#### Go Implementation

```go
package main

import (
    "container/list"
    "sync"
    "time"
)

type cacheEntry struct {
    key       interface{}
    value     interface{}
    expiresAt time.Time
}

type LRUCache struct {
    capacity   int
    cache      map[interface{}]*list.Element
    order      *list.List
    defaultTTL time.Duration
    mu         sync.RWMutex
}

func NewLRUCache(capacity int, defaultTTL time.Duration) *LRUCache {
    return &LRUCache{
        capacity:   capacity,
        cache:      make(map[interface{}]*list.Element),
        order:      list.New(),
        defaultTTL: defaultTTL,
    }
}

func (c *LRUCache) Get(key interface{}) (interface{}, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()

    if elem, ok := c.cache[key]; ok {
        entry := elem.Value.(*cacheEntry)
        
        // Check expiration
        if time.Now().After(entry.expiresAt) {
            c.removeElement(elem)
            return nil, false
        }
        
        // Move to front (most recently used)
        c.order.MoveToFront(elem)
        return entry.value, true
    }
    
    return nil, false
}

func (c *LRUCache) Put(key, value interface{}) {
    c.PutWithTTL(key, value, c.defaultTTL)
}

func (c *LRUCache) PutWithTTL(key, value interface{}, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()

    // Update existing
    if elem, ok := c.cache[key]; ok {
        c.order.MoveToFront(elem)
        entry := elem.Value.(*cacheEntry)
        entry.value = value
        entry.expiresAt = time.Now().Add(ttl)
        return
    }

    // Evict if at capacity
    if c.order.Len() >= c.capacity {
        c.removeOldest()
    }

    // Add new
    entry := &cacheEntry{
        key:       key,
        value:     value,
        expiresAt: time.Now().Add(ttl),
    }
    elem := c.order.PushFront(entry)
    c.cache[key] = elem
}

func (c *LRUCache) removeElement(elem *list.Element) {
    c.order.Remove(elem)
    entry := elem.Value.(*cacheEntry)
    delete(c.cache, entry.key)
}

func (c *LRUCache) removeOldest() {
    elem := c.order.Back()
    if elem != nil {
        c.removeElement(elem)
    }
}

func (c *LRUCache) CleanupExpired() int {
    c.mu.Lock()
    defer c.mu.Unlock()

    now := time.Now()
    count := 0
    
    for elem := c.order.Back(); elem != nil; {
        entry := elem.Value.(*cacheEntry)
        prev := elem.Prev()
        
        if now.After(entry.expiresAt) {
            c.removeElement(elem)
            count++
        }
        
        elem = prev
    }
    
    return count
}

// Usage example: DNS resolver
type DNSResolver struct {
    cache *LRUCache
}

func NewDNSResolver() *DNSResolver {
    return &DNSResolver{
        cache: NewLRUCache(10000, 5*time.Minute),
    }
}

func (r *DNSResolver) Resolve(domain string) (string, bool) {
    // Check cache
    if ip, ok := r.cache.Get(domain); ok {
        return ip.(string), true
    }
    
    // Actual DNS resolution
    ip := r.actualDNSLookup(domain)
    if ip != "" {
        r.cache.Put(domain, ip)
        return ip, true
    }
    
    return "", false
}

func (r *DNSResolver) actualDNSLookup(domain string) string {
    // Placeholder for actual DNS resolution
    return ""
}
```

---

### Example 3: Consistent Hashing (Load Balancing)

**Keywords**: distribute, balance, scale, partition, shard
**Pattern**: Consistent Hashing with Virtual Nodes
**Use Case**: Load balancing, distributed caching, data partitioning

#### Rust Implementation

```rust
use std::collections::{BTreeMap, HashSet};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

struct ConsistentHash {
    ring: BTreeMap<u64, String>,
    virtual_nodes: usize,
    nodes: HashSet<String>,
}

impl ConsistentHash {
    fn new(virtual_nodes: usize) -> Self {
        Self {
            ring: BTreeMap::new(),
            virtual_nodes,
            nodes: HashSet::new(),
        }
    }

    fn hash_key(&self, key: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }

    fn add_node(&mut self, node: String) {
        if self.nodes.insert(node.clone()) {
            // Add virtual nodes
            for i in 0..self.virtual_nodes {
                let virtual_key = format!("{}:{}", node, i);
                let hash = self.hash_key(&virtual_key);
                self.ring.insert(hash, node.clone());
            }
        }
    }

    fn remove_node(&mut self, node: &str) {
        if self.nodes.remove(node) {
            // Remove virtual nodes
            for i in 0..self.virtual_nodes {
                let virtual_key = format!("{}:{}", node, i);
                let hash = self.hash_key(&virtual_key);
                self.ring.remove(&hash);
            }
        }
    }

    fn get_node(&self, key: &str) -> Option<&String> {
        if self.ring.is_empty() {
            return None;
        }

        let hash = self.hash_key(key);
        
        // Find first node >= hash
        for (_, node) in self.ring.range(hash..) {
            return Some(node);
        }
        
        // Wrap around to first node
        self.ring.values().next()
    }

    fn get_n_nodes(&self, key: &str, n: usize) -> Vec<String> {
        if self.ring.is_empty() {
            return Vec::new();
        }

        let hash = self.hash_key(key);
        let mut result = Vec::new();
        let mut seen = HashSet::new();

        // Collect from hash position
        for (_, node) in self.ring.range(hash..) {
            if seen.insert(node.clone()) {
                result.push(node.clone());
                if result.len() >= n {
                    return result;
                }
            }
        }

        // Wrap around
        for (_, node) in &self.ring {
            if seen.insert(node.clone()) {
                result.push(node.clone());
                if result.len() >= n {
                    return result;
                }
            }
        }

        result
    }
}

// Usage for load balancing
fn load_balancer_example() {
    let mut lb = ConsistentHash::new(150); // 150 virtual nodes per server
    
    // Add servers
    lb.add_node("server1:8080".to_string());
    lb.add_node("server2:8080".to_string());
    lb.add_node("server3:8080".to_string());
    
    // Route request
    let user_id = "user12345";
    if let Some(server) = lb.get_node(user_id) {
        println!("Route {} to {}", user_id, server);
    }
    
    // For replicated data, get multiple nodes
    let replicas = lb.get_n_nodes(user_id, 3);
    println!("Replicate to: {:?}", replicas);
}
```

#### Python Implementation

```python
from bisect import bisect_right
from typing import List, Optional, Set
import hashlib

class ConsistentHash:
    def __init__(self, virtual_nodes: int = 150):
        """
        virtual_nodes: number of virtual nodes per physical node
        """
        self.virtual_nodes = virtual_nodes
        self.ring: List[int] = []
        self.ring_map: dict[int, str] = {}
        self.nodes: Set[str] = set()
    
    def _hash(self, key: str) -> int:
        """Hash function returning 32-bit integer"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str) -> None:
        """Add a physical node to the ring"""
        if node in self.nodes:
            return
        
        self.nodes.add(node)
        
        # Add virtual nodes
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            
            self.ring.append(hash_value)
            self.ring_map[hash_value] = node
        
        # Keep ring sorted
        self.ring.sort()
    
    def remove_node(self, node: str) -> None:
        """Remove a physical node from the ring"""
        if node not in self.nodes:
            return
        
        self.nodes.remove(node)
        
        # Remove virtual nodes
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            
            if hash_value in self.ring_map:
                del self.ring_map[hash_value]
                self.ring.remove(hash_value)
    
    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for this key"""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Find first node >= hash_value
        idx = bisect_right(self.ring, hash_value)
        
        # Wrap around if necessary
        if idx == len(self.ring):
            idx = 0
        
        return self.ring_map[self.ring[idx]]
    
    def get_n_nodes(self, key: str, n: int) -> List[str]:
        """Get n nodes for replication"""
        if not self.ring:
            return []
        
        hash_value = self._hash(key)
        idx = bisect_right(self.ring, hash_value)
        
        result = []
        seen = set()
        
        # Collect n unique physical nodes
        for i in range(len(self.ring)):
            pos = (idx + i) % len(self.ring)
            node = self.ring_map[self.ring[pos]]
            
            if node not in seen:
                seen.add(node)
                result.append(node)
                
                if len(result) >= n:
                    break
        
        return result

# Usage: Distributed cache with consistent hashing
class DistributedCache:
    def __init__(self):
        self.hasher = ConsistentHash(virtual_nodes=150)
        self.cache_nodes = {}  # node_id -> cache_instance
    
    def add_cache_node(self, node_id: str, cache_instance):
        self.hasher.add_node(node_id)
        self.cache_nodes[node_id] = cache_instance
    
    def get(self, key: str):
        node = self.hasher.get_node(key)
        if node and node in self.cache_nodes:
            return self.cache_nodes[node].get(key)
        return None
    
    def set(self, key: str, value, replicas: int = 2):
        nodes = self.hasher.get_n_nodes(key, replicas)
        for node in nodes:
            if node in self.cache_nodes:
                self.cache_nodes[node].set(key, value)

# Load balancer example
class LoadBalancer:
    def __init__(self):
        self.hasher = ConsistentHash(virtual_nodes=150)
    
    def add_server(self, server: str):
        self.hasher.add_node(server)
    
    def remove_server(self, server: str):
        self.hasher.remove_node(server)
    
    def get_server(self, request_id: str) -> Optional[str]:
        """Route request to server based on request ID"""
        return self.hasher.get_node(request_id)

# Example usage
lb = LoadBalancer()
lb.add_server("server1:8080")
lb.add_server("server2:8080")
lb.add_server("server3:8080")

# Route requests
for i in range(10):
    request_id = f"request-{i}"
    server = lb.get_server(request_id)
    print(f"Route {request_id} -> {server}")
```

#### Go Implementation

```go
package main

import (
    "crypto/md5"
    "encoding/binary"
    "fmt"
    "sort"
    "sync"
)

type ConsistentHash struct {
    ring         []uint32
    ringMap      map[uint32]string
    nodes        map[string]bool
    virtualNodes int
    mu           sync.RWMutex
}

func NewConsistentHash(virtualNodes int) *ConsistentHash {
    return &ConsistentHash{
        ring:         make([]uint32, 0),
        ringMap:      make(map[uint32]string),
        nodes:        make(map[string]bool),
        virtualNodes: virtualNodes,
    }
}

func (ch *ConsistentHash) hash(key string) uint32 {
    hash := md5.Sum([]byte(key))
    return binary.BigEndian.Uint32(hash[:4])
}

func (ch *ConsistentHash) AddNode(node string) {
    ch.mu.Lock()
    defer ch.mu.Unlock()

    if ch.nodes[node] {
        return
    }

    ch.nodes[node] = true

    // Add virtual nodes
    for i := 0; i < ch.virtualNodes; i++ {
        virtualKey := fmt.Sprintf("%s:%d", node, i)
        hash := ch.hash(virtualKey)
        
        ch.ring = append(ch.ring, hash)
        ch.ringMap[hash] = node
    }

    sort.Slice(ch.ring, func(i, j int) bool {
        return ch.ring[i] < ch.ring[j]
    })
}

func (ch *ConsistentHash) RemoveNode(node string) {
    ch.mu.Lock()
    defer ch.mu.Unlock()

    if !ch.nodes[node] {
        return
    }

    delete(ch.nodes, node)

    // Remove virtual nodes
    newRing := make([]uint32, 0)
    for i := 0; i < ch.virtualNodes; i++ {
        virtualKey := fmt.Sprintf("%s:%d", node, i)
        hash := ch.hash(virtualKey)
        delete(ch.ringMap, hash)
    }

    for _, h := range ch.ring {
        if _, ok := ch.ringMap[h]; ok {
            newRing = append(newRing, h)
        }
    }

    ch.ring = newRing
}

func (ch *ConsistentHash) GetNode(key string) string {
    ch.mu.RLock()
    defer ch.mu.RUnlock()

    if len(ch.ring) == 0 {
        return ""
    }

    hash := ch.hash(key)

    // Binary search for first node >= hash
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })

    // Wrap around if necessary
    if idx == len(ch.ring) {
        idx = 0
    }

    return ch.ringMap[ch.ring[idx]]
}

func (ch *ConsistentHash) GetNNodes(key string, n int) []string {
    ch.mu.RLock()
    defer ch.mu.RUnlock()

    if len(ch.ring) == 0 {
        return nil
    }

    hash := ch.hash(key)
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })

    result := make([]string, 0, n)
    seen := make(map[string]bool)

    for i := 0; i < len(ch.ring) && len(result) < n; i++ {
        pos := (idx + i) % len(ch.ring)
        node := ch.ringMap[ch.ring[pos]]

        if !seen[node] {
            seen[node] = true
            result = append(result, node)
        }
    }

    return result
}

// Load balancer implementation
type LoadBalancer struct {
    hasher *ConsistentHash
}

func NewLoadBalancer() *LoadBalancer {
    return &LoadBalancer{
        hasher: NewConsistentHash(150),
    }
}

func (lb *LoadBalancer) AddServer(server string) {
    lb.hasher.AddNode(server)
}

func (lb *LoadBalancer) RemoveServer(server string) {
    lb.hasher.RemoveNode(server)
}

func (lb *LoadBalancer) GetServer(requestID string) string {
    return lb.hasher.GetNode(requestID)
}

// Example usage
func main() {
    lb := NewLoadBalancer()
    
    // Add servers
    lb.AddServer("server1:8080")
    lb.AddServer("server2:8080")
    lb.AddServer("server3:8080")
    
    // Route requests
    for i := 0; i < 10; i++ {
        requestID := fmt.Sprintf("request-%d", i)
        server := lb.GetServer(requestID)
        fmt.Printf("Route %s -> %s\n", requestID, server)
    }
}
```

---

## Quick Reference Cheat Sheet

### Pattern Recognition Shortcuts

```
FIND + SORTED              → Binary Search
FIND + UNSORTED            → Hash Map
FIND + TOP-K               → Heap
FIND + RANGE               → Segment Tree / BIT

COUNT + FREQUENCY          → Hash Map / Counter
COUNT + UNIQUE             → Hash Set / Bloom Filter
COUNT + SLIDING            → Deque + Hash Map

PATH + UNWEIGHTED          → BFS
PATH + WEIGHTED            → Dijkstra / A*
PATH + NEGATIVE WEIGHTS    → Bellman-Ford
PATH + ALL PAIRS           → Floyd-Warshall

OPTIMIZE + SUBSTRUCTURE    → Dynamic Programming
OPTIMIZE + GREEDY CHOICE   → Greedy Algorithm
OPTIMIZE + CONSTRAINTS     → Backtracking / Branch & Bound

STREAM + FIXED WINDOW      → Circular Buffer
STREAM + SLIDING WINDOW    → Deque
STREAM + TOP-K             → Heap
STREAM + UNIQUE            → Sliding Hash Set

CONCURRENT + READ-HEAVY    → RWLock / Lock-Free
CONCURRENT + WRITE-HEAVY   → Sharded Locks
CONCURRENT + QUEUE         → Lock-Free Queue

DISTRIBUTED + PARTITION    → Consistent Hashing
DISTRIBUTED + CONSENSUS    → Raft / Paxos
DISTRIBUTED + CACHE        → DHT / Consistent Hash
```

### Complexity Quick Guide

| Operation | Array | Linked List | BST (balanced) | Hash Map | Heap |
|-----------|-------|-------------|----------------|----------|------|
| Search    | O(n)  | O(n)        | O(log n)       | O(1)     | O(n) |
| Insert    | O(n)  | O(1)        | O(log n)       | O(1)     | O(log n) |
| Delete    | O(n)  | O(1)*       | O(log n)       | O(1)     | O(log n) |
| Min/Max   | O(n)  | O(n)        | O(log n)       | O(n)     | O(1) |

*Assuming you have the node reference

---

## Advanced Pattern Recognition

### Composite Patterns

Many real-world problems require combining multiple patterns:

1. **Leaderboard System** = Heap + Hash Map
   - Heap for top-K rankings
   - Hash Map for O(1) user lookup
   - Update requires both structures

2. **Time-Series Database** = Segment Tree + LSM Tree
   - Segment Tree for range queries
   - LSM Tree for write-heavy workload
   - Compression for historical data

3. **API Gateway** = Trie + Rate Limiter + Load Balancer
   - Trie for route matching
   - Token Bucket for rate limiting
   - Consistent Hash for load balancing

4. **Distributed Lock** = Consensus + TTL + Fencing Token
   - Raft/Paxos for agreement
   - TTL for automatic release
   - Fencing token for safety

---

## Final Checklist for Elite Engineers

Before implementing, ask yourself:

✅ **Requirements Analysis**

- [ ] What is the exact problem statement?
- [ ] What are the input and output formats?
- [ ] What are the constraints (time, space, scale)?
- [ ] What are the edge cases?
- [ ] What are the performance requirements (latency, throughput)?

✅ **Pattern Recognition**

- [ ] What keywords appear in the problem?
- [ ] Which pattern family does this belong to?
- [ ] Are there multiple patterns to combine?
- [ ] What are the trade-offs between options?

✅ **Implementation Strategy**

- [ ] What's the simplest solution that works?
- [ ] How can I optimize it?
- [ ] How do I handle concurrency?
- [ ] How do I handle failures?

✅ **Validation**

- [ ] Does it handle edge cases?
- [ ] Does it meet performance requirements?
- [ ] Is it maintainable and testable?
- [ ] Does it scale to the required load?

✅ **Production Readiness**

- [ ] Monitoring and observability?
- [ ] Error handling and recovery?
- [ ] Resource cleanup and leak prevention?
- [ ] Documentation and runbooks?

---

## Resources for Continuous Learning

1. **Practice Platforms**
   - LeetCode (by pattern tags)
   - HackerRank (by domain)
   - System Design Primer (GitHub)

2. **Books**
   - "Designing Data-Intensive Applications" - Martin Kleppmann
   - "Introduction to Algorithms" - CLRS
   - "The Algorithm Design Manual" - Steven Skiena

3. **Real-world Systems**
   - Study open-source projects (Redis, Kafka, Kubernetes)
   - Read engineering blogs (Netflix, Uber, Facebook)
   - Analyze production incidents and post-mortems

Remember: **Pattern recognition is a skill built through practice.** Start with problems, identify patterns, implement solutions, and iterate. Over time, you'll develop intuition for mapping keywords to optimal DSA choices.

I'll create a comprehensive guide for recognizing problem patterns and selecting the right data structures and algorithms. This is essential for elite software engineering, especially in your domains.I've created a comprehensive guide for you! This is designed specifically for elite engineers working in cloud, networking, security, and infrastructure.

## Key Highlights:

**🎯 Pattern Recognition Framework**

- **IDENTIFY**: Extract keywords from problem statements
- **CLASSIFY**: Map to DSA pattern families
- **OPTIMIZE**: Select best-fit based on constraints

**📋 Extensive Keyword Matrices** covering:

- Search & Retrieval (hash maps, binary search, spatial queries)
- Graph & Network problems (routing, flow, connectivity)
- Concurrency & Security (rate limiting, caching, access control)
- Distributed Systems (consensus, partitioning, consistency)

**🏗️ Domain-Specific Patterns** for:

- Cloud resource management (bin packing, load balancing)
- Network operations (packet routing, traffic shaping, DNS)
- Security systems (firewall rules, intrusion detection, RBAC)
- Virtualization (resource isolation, process scheduling)

**💻 Three Complete Production-Ready Examples**:

1. **Rate Limiter** (Token Bucket) - for API throttling
2. **LRU Cache with TTL** - for distributed caching
3. **Consistent Hashing** - for load balancing & sharding

Each with full implementations in **Rust, Python, and Go**, including thread-safety and error handling.

**🧠 The CASER Decision Framework**:

- **C**onstraints (size, time, space limits)
- **A**ccess Pattern (random, sequential, range)
- **S**calability (concurrent, distributed, dynamic)
- **E**rror Tolerance (exact, approximate, fault-tolerant)
- **R**equirements (latency, throughput, consistency)

The guide includes quick-reference cheat sheets and a final checklist to ensure you always choose the optimal approach. Use it as your go-to reference when architecting systems or solving complex problems!

### 🧭 1. The Meta-Framework: How to Choose

Think of each technique as a **weapon in your arsenal**. The choice depends on:

| Problem Signal | Likely Technique | Mental Model |
|----------------|------------------|--------------|
| **Overlapping subproblems, optimal substructure** | Dynamic Programming (DP) | Crystal ball: reuse past solutions to predict future. |
| **Exploring all possibilities, constraints, undoing choices** | Backtracking | Maze explorer: try a path, backtrack if dead end. |
| **Divide into smaller identical subproblems** | Recursion | Fractal: self-similar structure. |
| **Need O(1) lookups, frequency counts, deduplication** | Hash Table | Magic ledger: instant membership check. |
| **Contiguous subarray / substring optimization** | Sliding Window | Telescope: adjust lens to capture moving range. |
| **Sequential data, fixed size** | Array | Straight road: indexed, cache-friendly. |
| **Grid/2D structure, adjacency** | Matrix / Graph traversal | Chessboard: moves constrained by neighbors. |
| **Locally optimal → globally optimal** | Greedy | Always grab the shiniest coin first. |
| **Combination of above** | Hybrid | Forge multiple weapons into one. |

---

### 🧠 2. Memory Model & Call Semantics

- **Recursion** → stack frames grow; risk of stack overflow. Rust requires explicit `Box`/`Rc` for heap recursion.  
- **DP** → can be top-down (recursion + memoization) or bottom-up (iterative, heap arrays).  
- **Backtracking** → stack-heavy; often exponential.  
- **Hash Table** → heap allocations, pointer chasing.  
- **Sliding Window** → stack variables for indices, heap for data.  
- **Greedy** → usually O(1) memory, stack-local.  
- **Matrix** → heap-allocated 2D arrays; cache locality matters.  

---

### ⚙️ 3. Language-Specific Idioms

### **Rust**

```rust
// Recursion
fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}

// DP (bottom-up)
fn fib(n: usize) -> u64 {
    let mut dp = vec![0; n+1];
    dp[0] = 0; dp[1] = 1;
    for i in 2..=n {
        dp[i] = dp[i-1] + dp[i-2];
    }
    dp[n]
}

// Hash table
use std::collections::HashMap;
let mut freq = HashMap::new();
for x in vec![1,2,2,3] {
    *freq.entry(x).or_insert(0) += 1;
}
```

---

### **Python**

```python
# Recursion
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)

# DP (memoization)
from functools import lru_cache
@lru_cache(None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

# Sliding window
def max_subarray_sum(nums, k):
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i-k]
        max_sum = max(max_sum, window_sum)
    return max_sum
```

---

### **Go**

```go
// Recursion
func factorial(n int) int {
    if n <= 1 { return 1 }
    return n * factorial(n-1)
}

// DP
func fib(n int) int {
    dp := make([]int, n+1)
    dp[0], dp[1] = 0, 1
    for i := 2; i <= n; i++ {
        dp[i] = dp[i-1] + dp[i-2]
    }
    return dp[n]
}

// Hash map
freq := make(map[int]int)
for _, x := range []int{1,2,2,3} {
    freq[x]++
}
```

---

### 🏆 4. Elite Heuristics

- **Ask the right meta-question**:  
  - *Do I need all possibilities?* → Backtracking.  
  - *Do I need optimal reuse?* → DP.  
  - *Do I need fast lookup?* → Hash table.  
  - *Do I need contiguous optimization?* → Sliding window.  
  - *Do I need local greedy choices?* → Greedy.  
  - *Do I need to traverse a grid/graph?* → Matrix/Graph BFS/DFS.  

- **Hybridization is common**:  
  - DP + Hashing (memoization).  
  - Backtracking + Pruning (branch & bound).  
  - Sliding window + Hash table (longest substring without repeats).  

- **Performance awareness**:  
  - Rust: prefer iterators and explicit ownership.  
  - Python: leverage built-ins (`set`, `dict`, `any`, `all`).  
  - Go: exploit slices and maps, avoid recursion for deep calls.  

- **Clarity > Cleverness**:  
  - Write the condition in domain terms (`is_valid_move`, `is_palindrome`) instead of raw checks.  

---

### 🌌 Fantasy Anchor

Imagine you’re a **celestial strategist**:

- **Recursion** → summoning fractal spirits.  
- **DP** → inscribing runes in a spellbook to reuse power.  
- **Backtracking** → wandering a labyrinth with chalk marks.  
- **Hash table** → a cosmic ledger of instant truths.  
- **Sliding window** → a telescope scanning the heavens.  
- **Greedy** → a dragon hoarding the brightest gems.  
- **Matrix** → a star map grid, each node a constellation.  

---

✅ **Summary for elite engineers**:

- Start with **problem signals** (overlap, optimality, exploration, lookup, contiguity).  
- Map to **technique** (DP, recursion, backtracking, hash, sliding window, greedy, matrix).  
- Use **language idioms** for clarity and performance.  
- Combine techniques when signals overlap.  
- Always optimize for **clarity, correctness, and maintainability** before micro-optimizing.  

---

Would you like me to now craft a **decision tree diagram** (problem signals → technique choice) so you can visually anchor this guide as a one-glance reference?

