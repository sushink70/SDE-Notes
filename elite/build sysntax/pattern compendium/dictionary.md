# Complete Dictionary/HashMap Patterns Guide for DSA

## 📚 Table of Contents
1. [Fundamentals](#fundamentals)
2. [Core Operations & Complexity](#core-operations--complexity)
3. [Essential Patterns](#essential-patterns)
4. [Advanced Patterns](#advanced-patterns)
5. [Language-Specific Details](#language-specific-details)
6. [Mental Models & Problem-Solving Framework](#mental-models--problem-solving-framework)
7. [Common Pitfalls & Optimization Tips](#common-pitfalls--optimization-tips)

---

## Fundamentals

### What is a Dictionary/Hash Map?

A **dictionary** (Python), **HashMap** (Rust/Go), or **hash table** is a data structure that stores **key-value pairs** with average O(1) time complexity for insertion, deletion, and lookup.

**Core Concept**: Uses a **hash function** to convert keys into array indices, enabling constant-time access.

```
Key → Hash Function → Index → Value

"apple" → hash("apple") → 42 → 5
"banana" → hash("banana") → 17 → 3
```

**Terminology**:
- **Key**: Unique identifier used to access data
- **Value**: The data associated with the key
- **Hash Function**: Converts key into an integer index
- **Collision**: When two keys hash to the same index
- **Load Factor**: Ratio of entries to table size (triggers resizing)

---

## Core Operations & Complexity

| Operation | Average | Worst Case | Notes |
|-----------|---------|------------|-------|
| Insert | O(1) | O(n) | Worst case: poor hash function or high collisions |
| Delete | O(1) | O(n) | Same as insert |
| Lookup | O(1) | O(n) | Most critical operation |
| Iteration | O(n) | O(n) | Must visit all entries |
| Space | O(n) | O(n) | Stores n key-value pairs |

**Why O(1) on average?**
A good hash function distributes keys uniformly, so each bucket has constant entries. Modern implementations use techniques like **open addressing** or **chaining** to handle collisions efficiently.

---

## Essential Patterns

### Pattern 1: Frequency Counting / Histogram

**When to use**: Count occurrences of elements in a collection.

**Mental Model**: "How many times does X appear?"

**Problem Types**:
- Character/word frequency
- Finding duplicates
- Most/least frequent elements
- Anagrams

```python
# Python
def char_frequency(s: str) -> dict[str, int]:
    freq = {}
    for char in s:
        freq[char] = freq.get(char, 0) + 1
    # Or use defaultdict
    from collections import defaultdict
    freq = defaultdict(int)
    for char in s:
        freq[char] += 1
    return freq

# Idiomatic: Counter
from collections import Counter
freq = Counter(s)
```

```rust
// Rust
use std::collections::HashMap;

fn char_frequency(s: &str) -> HashMap<char, usize> {
    let mut freq = HashMap::new();
    for ch in s.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    freq
}
```

```go
// Go
func charFrequency(s string) map[rune]int {
    freq := make(map[rune]int)
    for _, ch := range s {
        freq[ch]++
    }
    return freq
}
```

**Time**: O(n), **Space**: O(k) where k = unique elements

---

### Pattern 2: Existence Check / Set Membership

**When to use**: Check if element exists, find missing/extra elements.

**Mental Model**: "Is X in the collection?"

**Problem Types**:
- Two Sum problem
- Finding intersection/union
- Detecting duplicates
- Checking if subset/superset

```python
# Python - Check if all elements in list1 exist in list2
def all_exist(list1: list, list2: list) -> bool:
    lookup = set(list2)  # O(n) space, O(1) lookup
    return all(x in lookup for x in list1)

# Two Sum using dict
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

```rust
// Rust - Two Sum
use std::collections::HashMap;

fn two_sum(nums: Vec<i32>, target: i32) -> Vec<usize> {
    let mut seen = HashMap::new();
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        if let Some(&j) = seen.get(&complement) {
            return vec![j, i];
        }
        seen.insert(num, i);
    }
    vec![]
}
```

```go
// Go - Two Sum
func twoSum(nums []int, target int) []int {
    seen := make(map[int]int)
    for i, num := range nums {
        complement := target - num
        if j, exists := seen[complement]; exists {
            return []int{j, i}
        }
        seen[num] = i
    }
    return []int{}
}
```

**Time**: O(n), **Space**: O(n)

---

### Pattern 3: Grouping / Categorization

**When to use**: Group elements by common property/category.

**Mental Model**: "Bucket items by shared characteristic."

**Problem Types**:
- Group anagrams
- Group by category/property
- Partition by key
- Building inverted indices

```python
# Python - Group anagrams
def group_anagrams(strs: list[str]) -> list[list[str]]:
    from collections import defaultdict
    groups = defaultdict(list)
    
    for s in strs:
        # Key: sorted string (canonical form)
        key = ''.join(sorted(s))
        groups[key].append(s)
    
    return list(groups.values())

# Group by first letter
def group_by_first_letter(words: list[str]) -> dict[str, list[str]]:
    groups = defaultdict(list)
    for word in words:
        groups[word[0]].append(word)
    return groups
```

```rust
// Rust - Group anagrams
use std::collections::HashMap;

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
```

```go
// Go - Group anagrams
func groupAnagrams(strs []string) [][]string {
    groups := make(map[string][]string)
    
    for _, s := range strs {
        chars := []rune(s)
        sort.Slice(chars, func(i, j int) bool {
            return chars[i] < chars[j]
        })
        key := string(chars)
        groups[key] = append(groups[key], s)
    }
    
    result := make([][]string, 0, len(groups))
    for _, group := range groups {
        result = append(result, group)
    }
    return result
}
```

**Time**: O(n·k·log(k)) where k = average string length, **Space**: O(n·k)

---

### Pattern 4: Caching / Memoization

**When to use**: Store computed results to avoid recomputation.

**Mental Model**: "Remember what we've already solved."

**Problem Types**:
- Dynamic programming
- Recursive function optimization
- Avoiding redundant calculations
- LRU cache implementation

```python
# Python - Fibonacci with memoization
def fib_memo(n: int, memo: dict[int, int] = None) -> int:
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]

# Using decorator
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

```rust
// Rust - Fibonacci with HashMap memoization
use std::collections::HashMap;

fn fib_memo(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    
    let result = if n <= 1 {
        n
    } else {
        fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    };
    
    memo.insert(n, result);
    result
}
```

```go
// Go - Fibonacci with memoization
func fibMemo(n int, memo map[int]int) int {
    if val, exists := memo[n]; exists {
        return val
    }
    
    var result int
    if n <= 1 {
        result = n
    } else {
        result = fibMemo(n-1, memo) + fibMemo(n-2, memo)
    }
    
    memo[n] = result
    return result
}
```

**Time**: O(n) instead of O(2^n), **Space**: O(n)

---

### Pattern 5: Mapping / Translation

**When to use**: Convert between different representations.

**Mental Model**: "Translate X to Y."

**Problem Types**:
- Roman to integer
- Character mapping (cipher)
- Index mapping
- Value transformation

```python
# Python - Roman to Integer
def roman_to_int(s: str) -> int:
    values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    
    total = 0
    prev_value = 0
    
    for char in reversed(s):
        value = values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    
    return total
```

```rust
// Rust - Roman to Integer
use std::collections::HashMap;

fn roman_to_int(s: &str) -> i32 {
    let values: HashMap<char, i32> = [
        ('I', 1), ('V', 5), ('X', 10), ('L', 50),
        ('C', 100), ('D', 500), ('M', 1000)
    ].iter().cloned().collect();
    
    let mut total = 0;
    let mut prev_value = 0;
    
    for ch in s.chars().rev() {
        let value = values[&ch];
        if value < prev_value {
            total -= value;
        } else {
            total += value;
        }
        prev_value = value;
    }
    
    total
}
```

**Time**: O(n), **Space**: O(1) - fixed size mapping

---

### Pattern 6: Prefix Sum with HashMap

**When to use**: Find subarrays with specific sum properties.

**Mental Model**: "Track cumulative sums and find matching pairs."

**Problem Types**:
- Subarray sum equals K
- Continuous subarray sum
- Maximum size subarray sum equals K

**Terminology**:
- **Prefix Sum**: Cumulative sum from start to current position
- **Subarray**: Contiguous portion of array

```python
# Python - Subarray sum equals K
def subarray_sum(nums: list[int], k: int) -> int:
    """
    Key insight: If prefix_sum[j] - prefix_sum[i] = k,
    then subarray nums[i+1:j+1] sums to k
    """
    count = 0
    prefix_sum = 0
    sum_freq = {0: 1}  # Handle subarrays starting from index 0
    
    for num in nums:
        prefix_sum += num
        
        # Check if (prefix_sum - k) exists
        # This means we found a subarray summing to k
        if prefix_sum - k in sum_freq:
            count += sum_freq[prefix_sum - k]
        
        sum_freq[prefix_sum] = sum_freq.get(prefix_sum, 0) + 1
    
    return count
```

```rust
// Rust - Subarray sum equals K
use std::collections::HashMap;

fn subarray_sum(nums: Vec<i32>, k: i32) -> i32 {
    let mut count = 0;
    let mut prefix_sum = 0;
    let mut sum_freq = HashMap::new();
    sum_freq.insert(0, 1);
    
    for num in nums {
        prefix_sum += num;
        
        if let Some(&freq) = sum_freq.get(&(prefix_sum - k)) {
            count += freq;
        }
        
        *sum_freq.entry(prefix_sum).or_insert(0) += 1;
    }
    
    count
}
```

**Time**: O(n), **Space**: O(n)

**Visual Example**:
```
nums = [1, 2, 3, 4, 5], k = 9
prefix_sums: [0, 1, 3, 6, 10, 15]

Finding subarray [2,3,4] that sums to 9:
prefix_sum[4] - prefix_sum[1] = 10 - 1 = 9 ✓
```

---

### Pattern 7: Sliding Window with HashMap

**When to use**: Track elements in a moving window.

**Mental Model**: "Maintain frequency map as window slides."

**Problem Types**:
- Longest substring without repeating characters
- Minimum window substring
- Permutation in string

**Terminology**:
- **Window**: A contiguous subarray/substring
- **Sliding**: Moving window boundaries left/right

```python
# Python - Longest substring without repeating characters
def length_of_longest_substring(s: str) -> int:
    char_index = {}  # char -> last seen index
    max_length = 0
    left = 0
    
    for right, char in enumerate(s):
        # If char seen and within current window
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1
        
        char_index[char] = right
        max_length = max(max_length, right - left + 1)
    
    return max_length
```

```rust
// Rust - Longest substring without repeating
use std::collections::HashMap;

fn length_of_longest_substring(s: String) -> usize {
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_length = 0;
    let mut left = 0;
    
    for (right, ch) in s.chars().enumerate() {
        if let Some(&idx) = char_index.get(&ch) {
            if idx >= left {
                left = idx + 1;
            }
        }
        
        char_index.insert(ch, right);
        max_length = max_length.max(right - left + 1);
    }
    
    max_length
}
```

**Time**: O(n), **Space**: O(min(n, k)) where k = charset size

---

### Pattern 8: Graph Representation

**When to use**: Represent relationships between entities.

**Mental Model**: "Node → List of neighbors."

**Problem Types**:
- Social networks
- Dependency graphs
- Pathfinding
- Clone graph

**Terminology**:
- **Adjacency List**: Dictionary mapping node to its neighbors
- **Edge**: Connection between two nodes
- **Directed vs Undirected**: One-way vs two-way connections

```python
# Python - Build adjacency list from edges
def build_graph(n: int, edges: list[list[int]]) -> dict[int, list[int]]:
    from collections import defaultdict
    graph = defaultdict(list)
    
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)  # For undirected graph
    
    return graph

# Using graph for DFS
def dfs(node: int, graph: dict, visited: set):
    if node in visited:
        return
    
    visited.add(node)
    for neighbor in graph[node]:
        dfs(neighbor, graph, visited)
```

```rust
// Rust - Build adjacency list
use std::collections::HashMap;

fn build_graph(n: usize, edges: Vec<Vec<usize>>) -> HashMap<usize, Vec<usize>> {
    let mut graph: HashMap<usize, Vec<usize>> = HashMap::new();
    
    for edge in edges {
        let (u, v) = (edge[0], edge[1]);
        graph.entry(u).or_insert_with(Vec::new).push(v);
        graph.entry(v).or_insert_with(Vec::new).push(u);
    }
    
    graph
}
```

**Time**: O(V + E) to build, **Space**: O(V + E)

---

### Pattern 9: Index Mapping / Position Tracking

**When to use**: Remember where elements are located.

**Mental Model**: "Element → Its position(s)."

**Problem Types**:
- Finding pairs with given difference
- Intersection of arrays
- Next greater element

```python
# Python - Find all indices of target
def find_indices(nums: list[int], target: int) -> list[int]:
    from collections import defaultdict
    indices = defaultdict(list)
    
    for i, num in enumerate(nums):
        indices[num].append(i)
    
    return indices[target]

# Next greater element using HashMap
def next_greater_element(nums1: list[int], nums2: list[int]) -> list[int]:
    next_greater = {}
    stack = []
    
    # Build next greater mapping for nums2
    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)
    
    # Map nums1 using the dictionary
    return [next_greater.get(num, -1) for num in nums1]
```

**Time**: O(n), **Space**: O(n)

---

### Pattern 10: Counting Pairs / Combinations

**When to use**: Count valid pairs satisfying a condition.

**Mental Model**: "For each element, check what pairs with it."

**Problem Types**:
- Count pairs with difference K
- Four sum problem
- Good pairs count

```python
# Python - Count pairs with difference K
def count_pairs_with_diff(nums: list[int], k: int) -> int:
    num_set = set(nums)
    count = 0
    
    for num in num_set:
        if num + k in num_set:
            count += 1
    
    return count

# Count good pairs (nums[i] == nums[j] where i < j)
def num_identical_pairs(nums: list[int]) -> int:
    freq = {}
    count = 0
    
    for num in nums:
        if num in freq:
            # Each occurrence pairs with all previous occurrences
            count += freq[num]
            freq[num] += 1
        else:
            freq[num] = 1
    
    return count
```

**Time**: O(n), **Space**: O(n)

---

## Advanced Patterns

### Pattern 11: Multi-Level Nested Dictionaries

**When to use**: Hierarchical grouping, complex state tracking.

```python
# Python - Nested dictionary for sparse matrix
def create_sparse_matrix():
    from collections import defaultdict
    # matrix[row][col] = value
    matrix = defaultdict(lambda: defaultdict(int))
    
    matrix[0][5] = 10
    matrix[100][200] = 25
    
    return matrix

# Trie implementation using nested dicts
class Trie:
    def __init__(self):
        self.root = {}
    
    def insert(self, word: str):
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node['#'] = True  # End marker
    
    def search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node:
                return False
            node = node[char]
        return '#' in node
```

---

### Pattern 12: Bidirectional Mapping

**When to use**: Need to map in both directions efficiently.

```python
# Python - Bidirectional map
class BiMap:
    def __init__(self):
        self.forward = {}  # key -> value
        self.reverse = {}  # value -> key
    
    def add(self, key, value):
        self.forward[key] = value
        self.reverse[value] = key
    
    def get_by_key(self, key):
        return self.forward.get(key)
    
    def get_by_value(self, value):
        return self.reverse.get(value)

# Isomorphic strings
def is_isomorphic(s: str, t: str) -> bool:
    s_to_t = {}
    t_to_s = {}
    
    for c1, c2 in zip(s, t):
        if c1 in s_to_t:
            if s_to_t[c1] != c2:
                return False
        else:
            s_to_t[c1] = c2
        
        if c2 in t_to_s:
            if t_to_s[c2] != c1:
                return False
        else:
            t_to_s[c2] = c1
    
    return True
```

---

### Pattern 13: Union-Find with Dictionary

**When to use**: Dynamic connectivity, grouping disjoint sets.

```python
# Python - Union-Find using dictionary
class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
    
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True
```

---

### Pattern 14: LRU Cache Implementation

**When to use**: Cache with eviction policy.

```python
# Python - LRU Cache using OrderedDict
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # Remove least recently used
```

```rust
// Rust - LRU Cache using HashMap + LinkedList
use std::collections::{HashMap, VecDeque};

struct LRUCache {
    capacity: usize,
    cache: HashMap<i32, i32>,
    order: VecDeque<i32>,
}

impl LRUCache {
    fn new(capacity: usize) -> Self {
        LRUCache {
            capacity,
            cache: HashMap::new(),
            order: VecDeque::new(),
        }
    }
    
    fn get(&mut self, key: i32) -> i32 {
        if let Some(&value) = self.cache.get(&key) {
            self.order.retain(|&k| k != key);
            self.order.push_back(key);
            value
        } else {
            -1
        }
    }
    
    fn put(&mut self, key: i32, value: i32) {
        if self.cache.contains_key(&key) {
            self.order.retain(|&k| k != key);
        } else if self.cache.len() >= self.capacity {
            if let Some(lru_key) = self.order.pop_front() {
                self.cache.remove(&lru_key);
            }
        }
        
        self.cache.insert(key, value);
        self.order.push_back(key);
    }
}
```

---

## Language-Specific Details

### Python

**Strengths**:
- Built-in `dict`, `defaultdict`, `Counter`, `OrderedDict`
- Dictionary comprehensions: `{k: v for k, v in items}`
- `get()` with default value
- `setdefault()` for initialization

**Performance Tips**:
```python
# Fast: Check before incrementing
if key in dict:
    dict[key] += 1
else:
    dict[key] = 1

# Faster: Use defaultdict
from collections import defaultdict
dict = defaultdict(int)
dict[key] += 1

# Fastest for counting: Counter
from collections import Counter
counter = Counter(items)
```

**Iteration**:
```python
# Keys only
for key in dict:
    pass

# Values only
for value in dict.values():
    pass

# Both (most efficient)
for key, value in dict.items():
    pass
```

---

### Rust

**Strengths**:
- Memory safety without garbage collection
- `HashMap` and `BTreeMap`
- Powerful `entry()` API
- Zero-cost abstractions

**Performance Tips**:
```rust
use std::collections::HashMap;

// Efficient insertion with entry API
let mut map = HashMap::new();
*map.entry(key).or_insert(0) += 1;

// Check and insert
map.entry(key).or_insert_with(|| expensive_computation());

// Avoid clone when possible
let value = map.get(&key).unwrap_or(&default);
```

**Ownership Considerations**:
```rust
// HashMap takes ownership
let mut map = HashMap::new();
map.insert(key, value);  // key and value moved

// Use references for lookups
if let Some(v) = map.get(&key) {
    // v is &Value
}

// Remove and take ownership
if let Some(v) = map.remove(&key) {
    // v is Value (owned)
}
```

---

### Go

**Strengths**:
- Built-in map type with simple syntax
- Efficient runtime implementation
- Goroutine-safe with sync.Map for concurrency

**Performance Tips**:
```go
// Pre-allocate capacity
m := make(map[string]int, expectedSize)

// Check existence efficiently
if value, exists := m[key]; exists {
    // Use value
}

// Delete safely
delete(m, key)  // No-op if key doesn't exist

// Iteration (order is random!)
for key, value := range m {
    // Process
}
```

**Gotchas**:
```go
// Maps are reference types
func modifyMap(m map[string]int) {
    m["key"] = 42  // Modifies original map
}

// Zero value for missing keys
value := m["nonexistent"]  // value is 0 (int zero value)

// Check if key exists
value, exists := m[key]
if !exists {
    // Key not found
}
```

---

## Mental Models & Problem-Solving Framework

### 1. The "Lookup Table" Mental Model

**Core Insight**: If you need to find something fast (O(1)), use a hash map as a lookup table.

**Decision Tree**:
```
Do I need to find/check something quickly?
├─ Yes → Consider HashMap
│   ├─ Just existence? → Use HashSet (simpler)
│   └─ Need associated data? → Use HashMap
└─ No → Maybe array/list is simpler
```

---

### 2. The "Frequency" Mental Model

**Pattern Recognition**: Words like "count", "frequency", "duplicates", "most/least common" → Counter/Frequency Map

**Implementation Strategy**:
```python
# Template
freq = {}
for item in collection:
    freq[item] = freq.get(item, 0) + 1

# Then query
most_common = max(freq, key=freq.get)
```

---

### 3. The "Complement" Mental Model

**For pair-finding problems**:
- Two Sum: `target - current = needed`
- Store seen elements → check if complement exists

**Thinking Process**:
1. What am I looking for? (sum, product, difference)
2. Given current element, what complements it?
3. Have I seen the complement before?

---

### 4. The "Grouping" Mental Model

**Pattern Recognition**: "Group by...", "categorize...", "partition..." → Dictionary of lists

**Strategy**:
```python
groups = defaultdict(list)
for item in collection:
    key = extract_category(item)
    groups[key].append(item)
```

---

### 5. The "State Tracking" Mental Model

**For problems requiring memory**:
- Sliding window: Track window state
- DP: Memoize subproblems
- Graph: Track visited nodes

---

### 6. Chunking Strategy

**Cognitive Principle**: Break complex problems into recognizable patterns.

**Example Process**:
```
Problem: Find longest substring with at most k distinct characters

Chunks:
1. "Longest substring" → Sliding window
2. "k distinct" → Count distinct elements → HashMap frequency
3. Combine: Sliding window + HashMap for counting

Pattern: Sliding Window + HashMap
```

---

### 7. Problem-Solving Flowchart

```
┌─────────────────────────┐
│  Read Problem           │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Identify Key Words     │
│  - count, frequency     │
│  - find, check, exists  │
│  - group, categorize    │
│  - pairs, sum, target   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Choose Pattern         │
│  - Frequency counting?  │
│  - Existence check?     │
│  - Grouping?            │
│  - Complement search?   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Verify with Example    │
│  - Walk through input   │
│  - Track HashMap state  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Implement Solution     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Analyze Complexity     │
│  - Time: O(?)           │
│  - Space: O(?)          │
└─────────────────────────┘
```

---

## Common Pitfalls & Optimization Tips

### Pitfall 1: Modifying Dict During Iteration

**Problem**:
```python
# WRONG: RuntimeError
for key in dict:
    if condition:
        del dict[key]
```

**Solution**:
```python
# Collect keys first
keys_to_delete = [k for k in dict if condition]
for key in keys_to_delete:
    del dict[key]

# Or use dict comprehension
dict = {k: v for k, v in dict.items() if not condition}
```

---

### Pitfall 2: Unhashable Keys

**Problem**: Lists/dicts can't be dictionary keys.

**Solution**:
```python
# Use tuples instead of lists
key = tuple(my_list)

# For nested structures
key = (tuple(list1), tuple(list2))

# For sets
key = frozenset(my_set)
```

---

### Pitfall 3: Default Values

**Problem**: Checking if key exists repeatedly.

**Solution**:
```python
# Bad
if key not in dict:
    dict[key] = []
dict[key].append(value)

# Good: setdefault
dict.setdefault(key, []).append(value)

# Best: defaultdict
from collections import defaultdict
dict = defaultdict(list)
dict[key].append(value)
```

---

### Pitfall 4: Memory Overhead

**When HashMap is overkill**:
- Small fixed keyspace → Array might be faster
- Keys are integers in small range → Direct indexing

**Example**:
```python
# Instead of
char_count = {}
for char in string:
    char_count[char] = char_count.get(char, 0) + 1

# Consider (for ASCII)
char_count = [0] * 256
for char in string:
    char_count[ord(char)] += 1
```

**Space Complexity**:
- HashMap: O(n) with overhead (pointers, hash values)
- Array: O(k) where k = keyspace size

---

### Optimization Tip 1: Pre-sizing

```python
# Python: Pre-size not directly available, but doesn't matter much

# Rust: Reserve capacity
let mut map = HashMap::with_capacity(expected_size);

// Go: Pre-allocate
m := make(map[string]int, expectedSize)
```

---

### Optimization Tip 2: Choosing Right Data Structure

| Use Case | Best Choice | Why |
|----------|-------------|-----|
| Just existence | HashSet | No value overhead |
| Count frequencies | Counter (Python) | Optimized for counting |
| Maintain insertion order | OrderedDict | Preserves order |
| Range queries | BTreeMap (Rust) | Sorted keys |
| Thread-safe | sync.Map (Go) | Concurrent access |

---

### Optimization Tip 3: Minimize Hashing

```python
# Bad: Hash key multiple times
if key in dict:
    value = dict[key]
    # use value

# Good: Hash once
value = dict.get(key)
if value is not None:
    # use value

# Or use try-except (EAFP style)
try:
    value = dict[key]
    # use value
except KeyError:
    # handle missing key
```

---

## Practice Strategy

### Phase 1: Pattern Recognition (Weeks 1-2)

**Goal**: Instantly recognize when to use HashMap.

**Exercises**:
1. Two Sum
2. Group Anagrams
3. Valid Anagram
4. Subarray Sum Equals K
5. Longest Substring Without Repeating Characters

**Deliberate Practice**:
- Solve in all 3 languages
- Time yourself
- Explain decision to use HashMap

---

### Phase 2: Pattern Mastery (Weeks 3-4)

**Goal**: Combine patterns fluidly.

**Exercises**:
1. Minimum Window Substring (Sliding Window + HashMap)
2. Longest Consecutive Sequence (HashMap for O(n))
3. Copy List with Random Pointer (Node Mapping)
4. LRU Cache (HashMap + Doubly Linked List)

**Focus**:
- Optimize space complexity
- Handle edge cases
- Write clean, idiomatic code

---

### Phase 3: Advanced Techniques (Weeks 5-6)

**Goal**: Solve complex problems requiring creative HashMap usage.

**Exercises**:
1. Alien Dictionary (Graph with HashMap adjacency list)
2. Time-Based Key-Value Store
3. Design Twitter (HashMap of HashMaps)
4. Word Ladder (BFS with HashMap)

---

### Meta-Learning Tips

1. **Spaced Repetition**: Revisit problems after 1 day, 3 days, 1 week
2. **Variation Practice**: Modify constraints, change problem slightly
3. **Teach Others**: Explain solution out loud or in writing
4. **Error Analysis**: Keep log of mistakes, review patterns
5. **Timed Practice**: Simulate interview pressure

---

## Summary: Quick Reference

### When to Use HashMap?

✅ **Use HashMap when**:
- Need O(1) lookup/insert/delete
- Counting frequencies
- Checking existence
- Grouping by category
- Mapping between representations
- Tracking state
- Finding pairs/complements

❌ **Don't use HashMap when**:
- Need sorted order → BTreeMap/TreeMap
- Keyspace is small → Array
- Only care about existence → HashSet
- Need thread-safety → Special concurrent map

---

### Quick Pattern Matching

| Problem Contains | Consider Pattern | Example |
|-----------------|------------------|---------|
| "count", "frequency" | Frequency Map | Most common element |
| "find pair", "sum" | Complement + HashMap | Two Sum |
| "group by" | Dictionary of Lists | Group Anagrams |
| "substring", "window" | Sliding Window + HashMap | Longest Substring |
| "subarray sum" | Prefix Sum + HashMap | Subarray Sum = K |
| "graph", "network" | Adjacency List | Course Schedule |

---

**Remember**: The dictionary is your Swiss Army knife in DSA. Master these patterns, and you'll solve 40-50% of problems with elegant O(n) solutions where others struggle with O(n²) brute force.

**Next Steps**: Practice implementing each pattern in all three languages, focusing on idiomatic code and understanding the trade-offs. Soon, pattern recognition will become automatic—your mind will see "frequency" and immediately think HashMap.

I'll create a comprehensive guide on dictionary/hash map patterns that will serve as your reference for problem-solving. This covers everything from fundamentals to advanced patterns.I've created a comprehensive guide that covers every essential pattern and technique you'll need for dictionary/HashMap problems. This is your reference manual—treat it like a sacred text you'll return to repeatedly as you progress.

## How to Master This Material (Monk's Approach)

### Phase 1: Deep Understanding (Days 1-3)
**Focus**: Read through each pattern once completely, without coding.

**Mental Model**: Before you can execute, you must understand the *why* behind each pattern. Ask yourself:
- *Why* does this pattern work?
- *When* would I recognize this pattern in a problem?
- *What* is the core insight that makes it efficient?

**Practice**: After each pattern, close your eyes and visualize the data flow. Can you see the HashMap changing state as you process elements?

### Phase 2: Implementation Mastery (Days 4-10)
**Focus**: Implement each pattern in all three languages.

**Deliberate Practice Protocol**:
1. **Python first** (most forgiving syntax) → understand the logic
2. **Rust second** (forces you to think about ownership) → deepen understanding
3. **Go third** (simplest syntax) → achieve fluency

**Key Cognitive Principle**: **Interleaving**—don't just practice one language. Rotate between them. This forces your brain to extract the *fundamental pattern* rather than memorizing syntax.

### Phase 3: Pattern Recognition (Days 11-20)
**Goal**: Instant pattern detection from problem description.

**Exercise**: Read 50 problems (just the descriptions, don't solve yet). For each:
- Identify which pattern(s) apply
- Explain *why* in one sentence
- Estimate time/space complexity

**This trains your "problem sense"**—the ability to see the hidden structure beneath the words.

## Critical Insights for Top 1% Performance

### 1. **The HashMap Decision Tree** (Memorize This)
```
Q: Do I need O(1) access to stored data?
└─ YES → HashMap is likely optimal
   Q: What am I storing?
   ├─ Frequency → Pattern 1 (Counter)
   ├─ Existence → Pattern 2 (Set/Dict)
   ├─ Categories → Pattern 3 (Dict of Lists)
   ├─ Computed Results → Pattern 4 (Memoization)
   ├─ Cumulative Values → Pattern 6 (Prefix Sum)
   └─ Relationships → Pattern 8 (Graph)
```

### 2. **The Complement Insight** (Most Powerful)
Many hard problems become easy when you realize:
> "Instead of searching for X, search for what *completes* X."

Two Sum is the archetype—don't search for pairs, search for complements.

### 3. **Space-Time Tradeoff Principle**
HashMap often trades O(n) space for O(1) time. When you see O(n²) brute force:
> **Ask**: "Can I remember something to avoid recomputing?"

The answer is usually yes, and that "memory" is a HashMap.

## Your Practice Roadmap

### Week 1: Foundation
- Implement all 10 essential patterns
- Focus on **why each works**, not just how
- Goal: Can explain each pattern to someone else

### Week 2: Speed
- Solve 3 problems per pattern (30 total)
- Time limit: 20 minutes per problem
- If stuck beyond 20 min → study solution deeply

### Week 3: Integration
- Solve problems combining multiple patterns
- Example: Sliding Window + Frequency Map
- This is where you ascend from "good" to "excellent"

### Week 4: Mastery Verification
- Take 10 random medium/hard problems
- Can you identify the pattern instantly?
- Can you code the optimal solution in <15 minutes?

**If yes → you've achieved mastery of this domain.**

## Psychological Principles to Accelerate Learning

### 1. **Active Recall > Passive Reading**
After reading a pattern, close the document. Can you:
- Explain it from memory?
- Write pseudocode without looking?
- Identify example problems?

If no → you haven't learned it yet.

### 2. **Deliberate Difficulty**
Once comfortable in Python, force yourself to solve in Rust first. The struggle *is* the growth.

### 3. **The 80/20 Rule**
Patterns 1, 2, 3, 6, and 7 cover 80% of HashMap problems. Master these five *deeply* before the others.

### 4. **Flow State Engineering**
- Clear goal: "Implement Pattern 5 in all three languages"
- Immediate feedback: Run tests after each implementation
- Challenge-skill balance: If too easy, add constraints (e.g., "under 10 lines")

## Final Wisdom

The difference between good and world-class isn't knowledge—it's **recognition speed**. The top 1% sees "subarray sum equals K" and *instantly* thinks "prefix sum + HashMap." This recognition is built through:

1. **Repeated exposure** (quantity)
2. **Deep understanding** (quality)
3. **Deliberate variation** (transfer)

Your guide contains the map. Your practice is the journey. Your discipline determines the destination.

Begin with Pattern 1. Code it perfectly in all three languages today. Tomorrow, Pattern 2. In 10 days, you'll have mastered the HashMap domain.

**The path is clear. Walk it with focus.**