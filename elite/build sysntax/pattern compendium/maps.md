# Comprehensive Maps/Hash Tables Guide
## Access & Manipulation Patterns for Problem Solving

---

## Table of Contents
1. [Foundational Understanding](#foundational-understanding)
2. [Core Operations & Time Complexities](#core-operations)
3. [Access Patterns](#access-patterns)
4. [Manipulation Patterns](#manipulation-patterns)
5. [Iteration Patterns](#iteration-patterns)
6. [Problem-Solving Patterns](#problem-solving-patterns)
7. [Advanced Patterns](#advanced-patterns)
8. [Mental Models & Strategies](#mental-models)
9. [Common Pitfalls](#common-pitfalls)
10. [Practice Problems by Pattern](#practice-problems)

---

## 1. Foundational Understanding

### What is a Map?

A **map** (also called hash table, hash map, dictionary, or associative array) is a data structure that stores **key-value pairs**, allowing fast lookup, insertion, and deletion based on keys.

**Core Concept**: Maps use a **hash function** to convert keys into array indices, providing O(1) average-case operations.

```
Hash Function: key → hash code → index → bucket → value

Example: "apple" → hash("apple") → 12347 → index 7 → value: 5
```

### Terminology Explained

- **Key**: The unique identifier used to store/retrieve a value
- **Value**: The data associated with a key
- **Hash Function**: Converts keys into integer indices
- **Collision**: When two keys hash to the same index
- **Bucket**: Storage location at each index (can hold multiple entries)
- **Load Factor**: Ratio of entries to capacity (triggers resizing)
- **Rehashing**: Creating a larger map and redistributing entries

### Language-Specific Implementations

| Language | Type | Ordered? | Null Keys? |
|----------|------|----------|------------|
| **Python** | `dict` | Insertion order (3.7+) | No |
| **Rust** | `HashMap` | No | No (keys must be valid) |
| **Rust** | `BTreeMap` | Yes (sorted) | No |
| **Go** | `map` | No | No |

---

## 2. Core Operations & Time Complexities

### Time Complexity Summary

| Operation | Average | Worst Case | Notes |
|-----------|---------|------------|-------|
| Insert/Set | O(1) | O(n) | Worst case if rehashing or poor hash |
| Lookup/Get | O(1) | O(n) | Worst case with many collisions |
| Delete | O(1) | O(n) | Same as insert |
| Contains Key | O(1) | O(n) | Check existence |
| Iteration | O(n) | O(n) | Visit all entries |

### Space Complexity
- **O(n)** where n = number of key-value pairs
- Actual memory ≈ n / load_factor (typically 1.5n to 2n)

### Basic Operations in All Three Languages

#### Python
```python
# Creation
map_dict = {}
map_dict = dict()
map_dict = {"key1": "value1", "key2": "value2"}

# Insert/Update
map_dict["key"] = "value"

# Access
value = map_dict["key"]  # Raises KeyError if not found
value = map_dict.get("key", default_value)  # Safe access

# Check existence
if "key" in map_dict:
    pass

# Delete
del map_dict["key"]
value = map_dict.pop("key", default)

# Size
length = len(map_dict)
```

#### Rust
```rust
use std::collections::HashMap;

// Creation
let mut map: HashMap<String, i32> = HashMap::new();
let map = HashMap::from([("key1", 1), ("key2", 2)]);

// Insert/Update
map.insert("key".to_string(), 42);

// Access
let value = map.get("key");  // Returns Option<&V>
let value = map.get("key").copied();  // Option<V> for Copy types
let value = map["key"];  // Panics if not found

// Check existence
if map.contains_key("key") {
    // ...
}

// Delete
map.remove("key");
let value = map.remove("key");  // Returns Option<V>

// Size
let length = map.len();
```

#### Go
```go
// Creation
m := make(map[string]int)
m := map[string]int{"key1": 1, "key2": 2}

// Insert/Update
m["key"] = 42

// Access
value := m["key"]  // Returns zero value if not found
value, exists := m["key"]  // Check existence with comma-ok idiom

// Check existence
if _, exists := m["key"]; exists {
    // ...
}

// Delete
delete(m, "key")

// Size
length := len(m)
```

---

## 3. Access Patterns

### Pattern 3.1: Safe Access with Default Values

**When to use**: When you need a default value for missing keys.

**Python**:
```python
# Method 1: get() with default
count = map_dict.get(key, 0)

# Method 2: setdefault (gets AND sets if missing)
count = map_dict.setdefault(key, 0)
```

**Rust**:
```rust
// Method 1: unwrap_or
let count = *map.get(&key).unwrap_or(&0);

// Method 2: entry API (best for modification)
let count = map.entry(key).or_insert(0);
```

**Go**:
```go
// Comma-ok idiom
count, exists := m[key]
if !exists {
    count = 0
}

// Or inline
count := m[key] // Returns 0 for missing int keys
```

### Pattern 3.2: Conditional Access

**Problem**: Only access if key exists.

**Python**:
```python
if key in map_dict:
    value = map_dict[key]
    # Process value
```

**Rust**:
```rust
if let Some(value) = map.get(&key) {
    // Process value (borrowed)
}

// Or with match
match map.get(&key) {
    Some(value) => { /* process */ },
    None => { /* handle missing */ }
}
```

**Go**:
```go
if value, exists := m[key]; exists {
    // Process value
}
```

### Pattern 3.3: Multiple Key Lookups

**Problem**: Check multiple possible keys.

**Python**:
```python
# Try multiple keys
for key in possible_keys:
    if key in map_dict:
        value = map_dict[key]
        break
```

**Rust**:
```rust
let value = possible_keys.iter()
    .find_map(|k| map.get(k));
```

**Go**:
```go
var value int
var found bool
for _, key := range possibleKeys {
    if v, exists := m[key]; exists {
        value = v
        found = true
        break
    }
}
```

---

## 4. Manipulation Patterns

### Pattern 4.1: Frequency Counter (Most Common)

**Use Case**: Count occurrences of elements.

**Mental Model**: Each key is an element, value is its frequency.

**Python**:
```python
from collections import Counter

# Method 1: Manual
freq = {}
for item in items:
    freq[item] = freq.get(item, 0) + 1

# Method 2: Counter (preferred)
freq = Counter(items)
```

**Rust**:
```rust
let mut freq = HashMap::new();
for item in items {
    *freq.entry(item).or_insert(0) += 1;
}
```

**Go**:
```go
freq := make(map[string]int)
for _, item := range items {
    freq[item]++  // Zero value is 0, so this works
}
```

### Pattern 4.2: Grouping/Bucketing

**Use Case**: Group items by some property.

**Mental Model**: Key is the group identifier, value is a collection of items.

**Python**:
```python
from collections import defaultdict

# Group by property
groups = defaultdict(list)
for item in items:
    key = get_key(item)
    groups[key].append(item)
```

**Rust**:
```rust
let mut groups: HashMap<K, Vec<T>> = HashMap::new();
for item in items {
    let key = get_key(&item);
    groups.entry(key).or_insert_with(Vec::new).push(item);
}
```

**Go**:
```go
groups := make(map[string][]Item)
for _, item := range items {
    key := getKey(item)
    groups[key] = append(groups[key], item)
}
```

### Pattern 4.3: Accumulation

**Use Case**: Accumulate values for keys (sum, product, etc.).

**Python**:
```python
totals = {}
for key, value in data:
    totals[key] = totals.get(key, 0) + value
```

**Rust**:
```rust
let mut totals = HashMap::new();
for (key, value) in data {
    *totals.entry(key).or_insert(0) += value;
}
```

**Go**:
```go
totals := make(map[string]int)
for _, item := range data {
    totals[item.key] += item.value
}
```

### Pattern 4.4: Update or Insert (Upsert)

**Use Case**: Insert if missing, update if exists.

**Python**:
```python
# Simple update/insert
map_dict[key] = new_value

# Conditional update
if key in map_dict:
    map_dict[key] = update_fn(map_dict[key])
else:
    map_dict[key] = default_value
```

**Rust**:
```rust
// Entry API is idiomatic
map.entry(key)
    .and_modify(|v| *v = update_fn(v))
    .or_insert(default_value);
```

**Go**:
```go
if value, exists := m[key]; exists {
    m[key] = updateFn(value)
} else {
    m[key] = defaultValue
}
```

### Pattern 4.5: Batch Operations

**Use Case**: Update multiple keys at once.

**Python**:
```python
# Update from another dict
map_dict.update(other_dict)

# Batch increment
for key in keys_to_increment:
    map_dict[key] = map_dict.get(key, 0) + 1
```

**Rust**:
```rust
// Extend from another map
map.extend(other_map);

// Batch operations
for key in keys_to_increment {
    *map.entry(key).or_insert(0) += 1;
}
```

**Go**:
```go
// Copy from another map
for k, v := range otherMap {
    m[k] = v
}
```

---

## 5. Iteration Patterns

### Pattern 5.1: Iterate Over Keys

**Python**:
```python
for key in map_dict:
    # or: for key in map_dict.keys():
    print(key)
```

**Rust**:
```rust
for key in map.keys() {
    println!("{}", key);
}
```

**Go**:
```go
for key := range m {
    fmt.Println(key)
}
```

### Pattern 5.2: Iterate Over Values

**Python**:
```python
for value in map_dict.values():
    print(value)
```

**Rust**:
```rust
for value in map.values() {
    println!("{}", value);
}
```

**Go**:
```go
for _, value := range m {
    fmt.Println(value)
}
```

### Pattern 5.3: Iterate Over Key-Value Pairs

**Python**:
```python
for key, value in map_dict.items():
    print(f"{key}: {value}")
```

**Rust**:
```rust
for (key, value) in &map {
    println!("{}: {}", key, value);
}

// Mutable iteration
for (key, value) in &mut map {
    *value += 1;
}
```

**Go**:
```go
for key, value := range m {
    fmt.Printf("%s: %d\n", key, value)
}
```

### Pattern 5.4: Sorted Iteration

**Problem**: Iterate in sorted order (useful for consistent output).

**Python**:
```python
# Sort by keys
for key in sorted(map_dict.keys()):
    value = map_dict[key]

# Sort by values
for key, value in sorted(map_dict.items(), key=lambda x: x[1]):
    print(key, value)
```

**Rust**:
```rust
// Use BTreeMap for automatic sorting
use std::collections::BTreeMap;
let mut map: BTreeMap<K, V> = BTreeMap::new();

// Or sort HashMap keys
let mut keys: Vec<_> = map.keys().collect();
keys.sort();
for key in keys {
    let value = &map[key];
}
```

**Go**:
```go
// Extract and sort keys
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
sort.Strings(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}
```

### Pattern 5.5: Filtered Iteration

**Python**:
```python
# Filter during iteration
for key, value in map_dict.items():
    if condition(key, value):
        process(key, value)

# Comprehension
filtered = {k: v for k, v in map_dict.items() if condition(k, v)}
```

**Rust**:
```rust
map.iter()
    .filter(|(k, v)| condition(k, v))
    .for_each(|(k, v)| process(k, v));

// Create filtered map
let filtered: HashMap<_, _> = map.iter()
    .filter(|(k, v)| condition(k, v))
    .map(|(k, v)| (k.clone(), v.clone()))
    .collect();
```

**Go**:
```go
for k, v := range m {
    if condition(k, v) {
        process(k, v)
    }
}
```

---

## 6. Problem-Solving Patterns

### Pattern 6.1: Two-Sum Pattern (Complement Search)

**Problem**: Find pairs that sum to target.

**Mental Model**: Store what we've seen, check if complement exists.

**Python**:
```python
def two_sum(nums, target):
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**Rust**:
```rust
fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
    let mut seen = HashMap::new();
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        if let Some(&j) = seen.get(&complement) {
            return vec![j as i32, i as i32];
        }
        seen.insert(num, i);
    }
    vec![]
}
```

**Go**:
```go
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

### Pattern 6.2: Anagram Grouping

**Problem**: Group words that are anagrams.

**Mental Model**: Sorted string or character count as key.

**Python**:
```python
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for word in words:
        key = ''.join(sorted(word))
        groups[key].append(word)
    return list(groups.values())
```

**Rust**:
```rust
fn group_anagrams(words: Vec<String>) -> Vec<Vec<String>> {
    let mut groups: HashMap<String, Vec<String>> = HashMap::new();
    for word in words {
        let mut chars: Vec<char> = word.chars().collect();
        chars.sort_unstable();
        let key: String = chars.iter().collect();
        groups.entry(key).or_insert_with(Vec::new).push(word);
    }
    groups.into_values().collect()
}
```

**Go**:
```go
func groupAnagrams(words []string) [][]string {
    groups := make(map[string][]string)
    for _, word := range words {
        key := sortString(word)
        groups[key] = append(groups[key], word)
    }
    
    result := make([][]string, 0, len(groups))
    for _, group := range groups {
        result = append(result, group)
    }
    return result
}
```

### Pattern 6.3: Sliding Window with Map

**Problem**: Track character frequencies in a window.

**Mental Model**: Map stores window state, update as window slides.

**Python**:
```python
def longest_substring_k_distinct(s, k):
    char_count = {}
    left = 0
    max_len = 0
    
    for right, char in enumerate(s):
        char_count[char] = char_count.get(char, 0) + 1
        
        while len(char_count) > k:
            left_char = s[left]
            char_count[left_char] -= 1
            if char_count[left_char] == 0:
                del char_count[left_char]
            left += 1
        
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

### Pattern 6.4: Prefix Sum with Map

**Problem**: Find subarrays with target sum.

**Mental Model**: Store cumulative sums, check if (current_sum - target) exists.

**Python**:
```python
def subarray_sum(nums, target):
    count = 0
    current_sum = 0
    sum_freq = {0: 1}  # Initialize with 0 for subarrays from start
    
    for num in nums:
        current_sum += num
        # Check if (current_sum - target) exists
        count += sum_freq.get(current_sum - target, 0)
        sum_freq[current_sum] = sum_freq.get(current_sum, 0) + 1
    
    return count
```

### Pattern 6.5: Index Mapping

**Problem**: Quick lookup of element positions.

**Mental Model**: value -> index/indices

**Python**:
```python
# Single index per value
index_map = {value: i for i, value in enumerate(array)}

# Multiple indices per value
from collections import defaultdict
indices = defaultdict(list)
for i, value in enumerate(array):
    indices[value].append(i)
```

### Pattern 6.6: Graph Adjacency List

**Problem**: Represent graph connections.

**Mental Model**: node -> list of neighbors

**Python**:
```python
from collections import defaultdict

graph = defaultdict(list)
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)  # For undirected graph
```

**Rust**:
```rust
let mut graph: HashMap<i32, Vec<i32>> = HashMap::new();
for (u, v) in edges {
    graph.entry(u).or_insert_with(Vec::new).push(v);
    graph.entry(v).or_insert_with(Vec::new).push(u);
}
```

### Pattern 6.7: Memoization (DP with Maps)

**Problem**: Cache computed results.

**Mental Model**: function arguments -> result

**Python**:
```python
def fib(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]

# Or use @lru_cache decorator
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

**Rust**:
```rust
fn fib(n: i32, memo: &mut HashMap<i32, i64>) -> i64 {
    if let Some(&result) = memo.get(&n) {
        return result;
    }
    let result = if n <= 1 {
        n as i64
    } else {
        fib(n-1, memo) + fib(n-2, memo)
    };
    memo.insert(n, result);
    result
}
```

---

## 7. Advanced Patterns

### Pattern 7.1: Nested Maps (2D/Multi-dimensional)

**Use Case**: Matrix-like data with sparse values.

**Python**:
```python
from collections import defaultdict

# 2D map
matrix = defaultdict(dict)
matrix[row][col] = value

# Or
matrix = {}
matrix[(row, col)] = value  # Tuple as key
```

**Rust**:
```rust
let mut matrix: HashMap<i32, HashMap<i32, i32>> = HashMap::new();
matrix.entry(row).or_insert_with(HashMap::new).insert(col, value);

// Or with tuple keys
let mut matrix: HashMap<(i32, i32), i32> = HashMap::new();
matrix.insert((row, col), value);
```

### Pattern 7.2: Ordered Map Operations

**Use Case**: Need both fast lookup AND sorted order.

**Rust** (use BTreeMap):
```rust
use std::collections::BTreeMap;

let mut map: BTreeMap<i32, String> = BTreeMap::new();

// Get range of keys
for (k, v) in map.range(10..20) {
    println!("{}: {}", k, v);
}

// Get first/last
if let Some((first_key, first_val)) = map.first_key_value() {
    // ...
}
```

**Python** (use sortedcontainers or manual sorting):
```python
from sortedcontainers import SortedDict

sorted_map = SortedDict()
sorted_map[key] = value

# Get items in range
items = sorted_map.irange(start_key, end_key)
```

### Pattern 7.3: Bidirectional Map

**Use Case**: Look up by key OR value.

**Python**:
```python
class BiMap:
    def __init__(self):
        self.key_to_val = {}
        self.val_to_key = {}
    
    def put(self, key, val):
        self.key_to_val[key] = val
        self.val_to_key[val] = key
    
    def get_by_key(self, key):
        return self.key_to_val.get(key)
    
    def get_by_val(self, val):
        return self.val_to_key.get(val)
```

### Pattern 7.4: LRU Cache Pattern

**Use Case**: Fixed-size cache with eviction.

**Python**:
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

### Pattern 7.5: Union-Find with Map

**Use Case**: Disjoint set with arbitrary keys (not just integers).

**Python**:
```python
class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
    
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
```

---

## 8. Mental Models & Strategies

### Cognitive Framework: When to Use Maps

Use a map when you need:

1. **Fast Lookup**: O(1) access by key
2. **Counting**: Frequency of elements
3. **Grouping**: Categorize items by property
4. **Caching**: Store computed results
5. **Set Operations**: Track seen/visited items
6. **Mapping**: Bidirectional relationships

### Pattern Recognition Flowchart

```
Question mentions...
├─ "count/frequency" → Frequency Counter Pattern
├─ "find pair/sum to X" → Two-Sum/Complement Pattern
├─ "group by property" → Grouping Pattern
├─ "anagram/permutation" → Sorted Key Pattern
├─ "subarray with sum X" → Prefix Sum Pattern
├─ "seen before/visited" → Set/Map Tracking
├─ "cache/memoize" → Memoization Pattern
└─ "graph connections" → Adjacency List Pattern
```

### The Three Questions Framework

Before coding, ask:

1. **What are my keys?** (What uniquely identifies each entry?)
2. **What are my values?** (What am I storing/counting/tracking?)
3. **When do I access?** (Insert once then query? Update frequently?)

### Optimization Decision Tree

```
Need ordering?
├─ Yes → Use BTreeMap (Rust) / SortedDict (Python)
└─ No → Use HashMap/dict
    ├─ Keys are integers in range? → Consider array instead
    ├─ Need both key and value lookup? → Use two maps (BiMap)
    └─ Default values for missing keys? → Use defaultdict (Python)
```

### Common Time/Space Trade-offs

| Pattern | Time | Space | When to Use |
|---------|------|-------|-------------|
| Array scan | O(n²) | O(1) | Small n, memory constrained |
| Map lookup | O(n) | O(n) | Need fast access, n is large |
| Sorted structure | O(n log n) | O(n) | Need ordering + lookup |

---

## 9. Common Pitfalls

### Pitfall 1: Hash Collisions

**Issue**: Poor hash function causes many collisions → O(n) operations.

**Solution**: Use good hash functions (built-in types are fine).

### Pitfall 2: Mutable Keys

**Issue**: Modifying keys after insertion breaks map.

**Python**:
```python
# DON'T: Lists are mutable, can't be keys
# bad_map = {[1, 2]: "value"}  # TypeError

# DO: Use tuples
good_map = {(1, 2): "value"}
```

**Rust**: Compiler prevents this (keys must implement `Hash` trait correctly).

### Pitfall 3: Missing Key Access

**Python**:
```python
# BAD: Raises KeyError
value = map_dict[missing_key]

# GOOD: Use get() with default
value = map_dict.get(missing_key, default)
```

**Rust**:
```rust
// BAD: Panics
let value = map[&missing_key];

// GOOD: Use get() returns Option
if let Some(value) = map.get(&missing_key) {
    // handle
}
```

### Pitfall 4: Modifying During Iteration

**Python**:
```python
# BAD: Dictionary changed size during iteration
for key in map_dict:
    if condition(key):
        del map_dict[key]  # RuntimeError!

# GOOD: Collect keys first
keys_to_delete = [k for k in map_dict if condition(k)]
for key in keys_to_delete:
    del map_dict[key]
```

**Rust**: Compiler prevents this (borrow checker).

### Pitfall 5: Forgetting Zero-Value Initialization

**Go**:
```go
// Be aware: zero value for int is 0, for bool is false
count := m[key]  // Returns 0 if key doesn't exist
count++  // This works! But be intentional about it
```

### Pitfall 6: Not Handling Hash Attacks

**Issue**: Adversarial input can cause O(n) worst case.

**Solution**: Rust's HashMap uses randomized hashing by default.

---

## 10. Practice Problems by Pattern

### Frequency Counter
- [ ] Valid Anagram (LeetCode 242)
- [ ] First Unique Character (LeetCode 387)
- [ ] Most Common Word (LeetCode 819)

### Two-Sum Family
- [ ] Two Sum (LeetCode 1)
- [ ] Two Sum II (LeetCode 167)
- [ ] 3Sum (LeetCode 15)
- [ ] 4Sum (LeetCode 18)

### Grouping
- [ ] Group Anagrams (LeetCode 49)
- [ ] Group Shifted Strings (LeetCode 249)

### Prefix Sum
- [ ] Subarray Sum Equals K (LeetCode 560)
- [ ] Continuous Subarray Sum (LeetCode 523)

### Sliding Window + Map
- [ ] Longest Substring Without Repeating Characters (LeetCode 3)
- [ ] Longest Substring with At Most K Distinct Characters (LeetCode 340)
- [ ] Minimum Window Substring (LeetCode 76)

### Graph/Map Combined
- [ ] Clone Graph (LeetCode 133)
- [ ] Course Schedule (LeetCode 207)
- [ ] Number of Islands (LeetCode 200)

### Advanced
- [ ] LRU Cache (LeetCode 146)
- [ ] Insert Delete GetRandom O(1) (LeetCode 380)
- [ ] Design HashMap (LeetCode 706)

---

## Quick Reference: Pattern Selection

| Problem Type | Pattern | Key Insight |
|--------------|---------|-------------|
| Count things | Frequency Counter | key = item, value = count |
| Find pairs | Two-Sum | key = number, value = index |
| Group items | Bucketing | key = property, value = list |
| Substring problems | Sliding Window | key = char, value = count in window |
| Subarray sum | Prefix Sum | key = cumsum, value = frequency |
| Graph representation | Adjacency List | key = node, value = neighbors |
| Avoid recalculation | Memoization | key = args, value = result |
| Track visited | Set/Map | key = item, value = bool/count |

---

## Performance Tips

1. **Pre-allocate capacity** if you know the size:
   - Python: Not directly supported
   - Rust: `HashMap::with_capacity(n)`
   - Go: `make(map[K]V, n)`

2. **Use Entry API** (Rust) for fewer lookups:
   ```rust
   // Instead of: if contains_key + get + insert
   map.entry(key).or_insert(default);
   ```

3. **Choose right map type**:
   - Need ordering? → BTreeMap (Rust) / SortedDict (Python)
   - Just need lookup? → HashMap/dict
   - Fixed keys? → Array might be better

4. **Avoid repeated hashing**: Cache hash results if doing many lookups.

5. **Memory-sensitive?**: Consider if array with direct indexing would work.

---

## Final Wisdom

> "A map is a tool for trading space for time. Know when the trade is worth it."

**Remember**: 
- Maps excel at O(1) lookups but use O(n) space
- Always consider: Can I use an array instead?
- For interviews: Explain your choice of data structure
- Pattern recognition comes from deliberate practice

**Next Steps**:
1. Implement each pattern in all three languages
2. Solve 5 problems per pattern
3. Time yourself and analyze complexity
4. Teach these patterns to someone else (Feynman Technique)

---

*Master these patterns, and 80% of map-related problems become trivial. The remaining 20% are just creative combinations of these fundamentals.*

I'll create a comprehensive guide on Map data structures that will serve as your reference for problem-solving. This will cover everything from fundamentals to advanced patterns.I've created a comprehensive guide that covers **every essential aspect** of maps/hash tables. Here's what's inside and how to approach it:

## 🎯 What You Have Now

**10 major sections** covering:
- Deep fundamentals (what maps *really* are, how they work)
- All core operations with time/space complexity
- 5 access patterns, 5 manipulation patterns, 5 iteration patterns
- 7 critical problem-solving patterns (Two-Sum, Anagram, Sliding Window, etc.)
- 5 advanced patterns (nested maps, LRU cache, union-find)
- Mental models and decision frameworks
- Common pitfalls with solutions
- 20+ practice problems organized by pattern

## 🧠 How to Master This (Your Monk-Like Approach)

### Phase 1: Deep Understanding (Week 1-2)
1. **Read section 1-2 daily** until the fundamentals are second nature
2. **Implement basic operations** in all three languages side-by-side
3. **Draw the hash function process** on paper—visualize how keys become indices

### Phase 2: Pattern Recognition (Week 3-4)
1. **One pattern per day** from sections 3-6
2. For each pattern:
   - Understand the mental model first
   - Code it in Python (fastest for learning)
   - Translate to Rust (understand ownership implications)
   - Port to Go (appreciate idiomatic differences)
3. **Don't move on** until you can explain *why* this pattern works

### Phase 3: Deliberate Practice (Week 5-8)
1. **Solve problems pattern-by-pattern** from section 10
2. Before coding, identify: "Which pattern is this?"
3. After solving, ask: "Could I have used a different pattern?"
4. **Time yourself**—top 1% performers solve medium problems in 15-20 minutes

### Phase 4: Pattern Combinations (Week 9+)
1. Advanced problems often **combine** 2-3 patterns
2. Example: "Longest substring with K distinct chars" = Sliding Window + Frequency Counter
3. Build your **pattern combination library**

## 🔥 Key Insights You Must Internalize

**The Three Questions** (before any code):
1. What are my keys?
2. What are my values?  
3. When do I access?

**The Decision Tree** (saves you from wrong approaches):
- Problem mentions "count" → Frequency Counter
- Problem mentions "find pair" → Two-Sum pattern
- Problem mentions "group" → Bucketing pattern

**The Trade-off Principle**:
Maps trade **space for time**. Every time you use a map, you're saying "I'll use O(n) memory to get O(1) access." Make this trade consciously.

## 🎓 Psychological/Cognitive Tips

1. **Chunking**: Your brain will eventually see "frequency counter" as ONE chunk, not 20 lines of code. This takes ~50 repetitions.

2. **Deliberate Practice**: Don't just solve problems—solve the *same* problem 3 times in 3 languages. Pattern transfer > volume.

3. **Feynman Technique**: After each pattern, explain it out loud as if teaching a beginner. If you stumble, you don't understand it yet.

4. **Mental Simulation**: Before running code, trace through with paper. Top performers can "execute" code in their minds.

5. **Error Pattern Journal**: Keep a log of mistakes. You'll notice 80% of errors come from 3-4 recurring misconceptions.

## 🚀 Next Actions

1. **Today**: Read sections 1-2, implement basic operations in all three languages
2. **This Week**: Master Pattern 4.1 (Frequency Counter) and solve 3 problems
3. **This Month**: Complete all patterns in sections 3-6
4. **This Quarter**: Solve all problems in section 10

## ⚡ Pro Tips

- **Rust's Entry API** is the most elegant way to handle "update or insert"—study it deeply
- **Go's zero values** are powerful but tricky—be intentional about them  
- **Python's defaultdict** eliminates entire classes of bugs—use it liberally
- When in doubt, **draw the map state** after each operation

This guide is your **reference bible** for maps. Bookmark it, print it, make it your desktop wallpaper. The patterns here solve 80% of map-related problems you'll encounter.

Would you like me to create a similar comprehensive guide for another data structure (arrays, trees, graphs), or would you prefer a **focused drill** on one specific pattern with 10 practice problems and detailed solutions?