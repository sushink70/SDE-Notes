# Comprehensive Guide to Maps in Data Structures and Algorithms

## Table of Contents
1. [Introduction to Maps](#introduction)
2. [Hash Table Theory](#hash-table-theory)
3. [Python Implementation](#python-implementation)
4. [Rust Implementation](#rust-implementation)
5. [Common Operations and Complexity](#common-operations)
6. [Advanced Topics](#advanced-topics)
7. [Practice Problems](#practice-problems)

## Introduction to Maps {#introduction}

A **Map** (also called Dictionary, Hash Table, or Hash Map) is a data structure that stores key-value pairs and provides efficient lookup, insertion, and deletion operations. Maps are fundamental in computer science and are used extensively in real-world applications.

### Key Characteristics
- **Unordered**: Elements are not stored in any particular order
- **Unique Keys**: Each key appears at most once
- **Fast Access**: Average O(1) time complexity for basic operations
- **Dynamic Size**: Can grow or shrink as needed

### Use Cases
- Caching and memoization
- Database indexing
- Symbol tables in compilers
- Counting frequencies
- Graph representations (adjacency lists)
- Configuration management

## Hash Table Theory {#hash-table-theory}

### How Hash Tables Work

1. **Hash Function**: Converts keys into array indices
2. **Buckets**: Array positions where key-value pairs are stored
3. **Collision Resolution**: Handling when multiple keys hash to the same index

### Collision Resolution Strategies

#### 1. Chaining (Separate Chaining)
- Each bucket contains a linked list of entries
- Simple to implement but requires extra memory

#### 2. Open Addressing
- **Linear Probing**: Check next slot sequentially
- **Quadratic Probing**: Check slots at quadratic intervals
- **Double Hashing**: Use second hash function for probing

### Load Factor
- Ratio of filled slots to total slots
- Typical threshold: 0.75
- Triggers resizing when exceeded

## Python Implementation {#python-implementation}

### Basic Hash Map with Chaining

```python
class Node:
    """Node for linked list in chaining"""
    def __init__(self, key, value, next=None):
        self.key = key
        self.value = value
        self.next = next

class HashMap:
    """Hash Map implementation using separate chaining"""
    
    def __init__(self, initial_capacity=16, load_factor=0.75):
        self.capacity = initial_capacity
        self.size = 0
        self.load_factor = load_factor
        self.buckets = [None] * self.capacity
    
    def _hash(self, key):
        """Simple hash function"""
        return hash(key) % self.capacity
    
    def put(self, key, value):
        """Insert or update a key-value pair"""
        index = self._hash(key)
        
        if self.buckets[index] is None:
            # Empty bucket
            self.buckets[index] = Node(key, value)
            self.size += 1
        else:
            # Traverse the chain
            current = self.buckets[index]
            while current:
                if current.key == key:
                    # Update existing key
                    current.value = value
                    return
                if current.next is None:
                    break
                current = current.next
            # Add new node at end
            current.next = Node(key, value)
            self.size += 1
        
        # Check if resizing is needed
        if self.size > self.capacity * self.load_factor:
            self._resize()
    
    def get(self, key):
        """Retrieve value for a given key"""
        index = self._hash(key)
        current = self.buckets[index]
        
        while current:
            if current.key == key:
                return current.value
            current = current.next
        
        raise KeyError(f"Key '{key}' not found")
    
    def remove(self, key):
        """Remove a key-value pair"""
        index = self._hash(key)
        current = self.buckets[index]
        prev = None
        
        while current:
            if current.key == key:
                if prev is None:
                    # First node in chain
                    self.buckets[index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                return current.value
            prev = current
            current = current.next
        
        raise KeyError(f"Key '{key}' not found")
    
    def contains_key(self, key):
        """Check if key exists"""
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def _resize(self):
        """Resize the hash table when load factor is exceeded"""
        old_buckets = self.buckets
        self.capacity *= 2
        self.size = 0
        self.buckets = [None] * self.capacity
        
        # Rehash all existing entries
        for head in old_buckets:
            current = head
            while current:
                self.put(current.key, current.value)
                current = current.next
    
    def keys(self):
        """Return all keys"""
        result = []
        for head in self.buckets:
            current = head
            while current:
                result.append(current.key)
                current = current.next
        return result
    
    def values(self):
        """Return all values"""
        result = []
        for head in self.buckets:
            current = head
            while current:
                result.append(current.value)
                current = current.next
        return result
    
    def items(self):
        """Return all key-value pairs"""
        result = []
        for head in self.buckets:
            current = head
            while current:
                result.append((current.key, current.value))
                current = current.next
        return result
    
    def clear(self):
        """Remove all entries"""
        self.buckets = [None] * self.capacity
        self.size = 0
    
    def __len__(self):
        return self.size
    
    def __str__(self):
        items = self.items()
        return "{" + ", ".join(f"{k}: {v}" for k, v in items) + "}"


# Hash Map with Open Addressing (Linear Probing)
class OpenAddressHashMap:
    """Hash Map using open addressing with linear probing"""
    
    def __init__(self, initial_capacity=16, load_factor=0.75):
        self.capacity = initial_capacity
        self.size = 0
        self.load_factor = load_factor
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.deleted = [False] * self.capacity  # Tombstone markers
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def _find_slot(self, key):
        """Find slot for key using linear probing"""
        index = self._hash(key)
        
        while self.keys[index] is not None:
            if self.keys[index] == key and not self.deleted[index]:
                return index, True  # Key found
            index = (index + 1) % self.capacity
        
        return index, False  # Empty slot found
    
    def put(self, key, value):
        """Insert or update a key-value pair"""
        index, found = self._find_slot(key)
        
        if not found:
            # New key
            self.keys[index] = key
            self.values[index] = value
            self.deleted[index] = False
            self.size += 1
            
            if self.size > self.capacity * self.load_factor:
                self._resize()
        else:
            # Update existing key
            self.values[index] = value
    
    def get(self, key):
        """Retrieve value for a given key"""
        index, found = self._find_slot(key)
        
        if found:
            return self.values[index]
        raise KeyError(f"Key '{key}' not found")
    
    def remove(self, key):
        """Remove a key-value pair using tombstone"""
        index, found = self._find_slot(key)
        
        if found:
            value = self.values[index]
            self.deleted[index] = True
            self.size -= 1
            return value
        raise KeyError(f"Key '{key}' not found")
    
    def _resize(self):
        """Resize and rehash the table"""
        old_keys = self.keys
        old_values = self.values
        old_deleted = self.deleted
        
        self.capacity *= 2
        self.size = 0
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.deleted = [False] * self.capacity
        
        for i in range(len(old_keys)):
            if old_keys[i] is not None and not old_deleted[i]:
                self.put(old_keys[i], old_values[i])
    
    def __len__(self):
        return self.size


# Advanced: LRU Cache using OrderedDict
from collections import OrderedDict

class LRUCache:
    """Least Recently Used Cache implementation"""
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        if key not in self.cache:
            return -1
        # Move to end (most recent)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            # Update and move to end
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # Remove least recently used (first item)
            self.cache.popitem(last=False)


# Utility: Frequency Counter
class FrequencyCounter:
    """Count frequencies of elements"""
    
    def __init__(self):
        self.freq_map = {}
    
    def add(self, element):
        self.freq_map[element] = self.freq_map.get(element, 0) + 1
    
    def get_frequency(self, element):
        return self.freq_map.get(element, 0)
    
    def most_common(self, n=1):
        """Get n most common elements"""
        items = sorted(self.freq_map.items(), key=lambda x: x[1], reverse=True)
        return items[:n]
```

### Python Usage Examples

```python
# Example 1: Basic HashMap operations
hashmap = HashMap()
hashmap.put("apple", 5)
hashmap.put("banana", 3)
hashmap.put("orange", 7)

print(hashmap.get("apple"))  # 5
print(hashmap.contains_key("grape"))  # False
print(hashmap.keys())  # ['apple', 'banana', 'orange']

# Example 2: LRU Cache
lru = LRUCache(2)
lru.put(1, 1)
lru.put(2, 2)
print(lru.get(1))  # 1
lru.put(3, 3)  # Evicts key 2
print(lru.get(2))  # -1 (not found)

# Example 3: Frequency Counter
counter = FrequencyCounter()
for word in ["apple", "banana", "apple", "cherry", "apple", "banana"]:
    counter.add(word)
print(counter.most_common(2))  # [('apple', 3), ('banana', 2)]
```

## Rust Implementation {#rust-implementation}

### Basic Hash Map with Chaining

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::fmt::Debug;

// Node for linked list in chaining
#[derive(Debug, Clone)]
struct Node<K, V> {
    key: K,
    value: V,
    next: Option<Box<Node<K, V>>>,
}

// Hash Map with separate chaining
pub struct HashMap<K, V> {
    buckets: Vec<Option<Box<Node<K, V>>>>,
    size: usize,
    capacity: usize,
    load_factor: f64,
}

impl<K, V> HashMap<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(16)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        let mut buckets = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            buckets.push(None);
        }
        
        HashMap {
            buckets,
            size: 0,
            capacity,
            load_factor: 0.75,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        let index = self.hash(&key);
        
        match &mut self.buckets[index] {
            None => {
                // Empty bucket
                self.buckets[index] = Some(Box::new(Node {
                    key,
                    value,
                    next: None,
                }));
                self.size += 1;
                self.maybe_resize();
                None
            }
            Some(node) => {
                // Traverse the chain
                let mut current = node;
                loop {
                    if current.key == key {
                        // Update existing key
                        let old_value = current.value.clone();
                        current.value = value;
                        return Some(old_value);
                    }
                    
                    if current.next.is_none() {
                        // Add at end of chain
                        current.next = Some(Box::new(Node {
                            key,
                            value,
                            next: None,
                        }));
                        self.size += 1;
                        self.maybe_resize();
                        return None;
                    }
                    
                    current = current.next.as_mut().unwrap();
                }
            }
        }
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let index = self.hash(key);
        
        let mut current = &self.buckets[index];
        while let Some(node) = current {
            if node.key == *key {
                return Some(&node.value);
            }
            current = &node.next;
        }
        
        None
    }
    
    pub fn get_mut(&mut self, key: &K) -> Option<&mut V> {
        let index = self.hash(key);
        
        let mut current = &mut self.buckets[index];
        while let Some(node) = current {
            if node.key == *key {
                return Some(&mut node.value);
            }
            current = &mut node.next;
        }
        
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = self.hash(key);
        
        // Check if first node matches
        if let Some(node) = &self.buckets[index] {
            if node.key == *key {
                let mut node = self.buckets[index].take().unwrap();
                self.buckets[index] = node.next.take();
                self.size -= 1;
                return Some(node.value);
            }
        }
        
        // Search in the chain
        let mut current = &mut self.buckets[index];
        while let Some(node) = current {
            if let Some(next) = &mut node.next {
                if next.key == *key {
                    let mut removed = node.next.take().unwrap();
                    node.next = removed.next.take();
                    self.size -= 1;
                    return Some(removed.value);
                }
            }
            current = &mut node.next;
        }
        
        None
    }
    
    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }
    
    fn maybe_resize(&mut self) {
        if self.size as f64 > self.capacity as f64 * self.load_factor {
            self.resize();
        }
    }
    
    fn resize(&mut self) {
        let new_capacity = self.capacity * 2;
        let mut new_map = HashMap::with_capacity(new_capacity);
        
        // Move all entries to new map
        for bucket in self.buckets.drain(..) {
            let mut current = bucket;
            while let Some(mut node) = current {
                let next = node.next.take();
                new_map.insert(node.key, node.value);
                current = next;
            }
        }
        
        self.buckets = new_map.buckets;
        self.capacity = new_capacity;
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    pub fn clear(&mut self) {
        for bucket in &mut self.buckets {
            *bucket = None;
        }
        self.size = 0;
    }
    
    pub fn keys(&self) -> Vec<K> {
        let mut keys = Vec::with_capacity(self.size);
        for bucket in &self.buckets {
            let mut current = bucket;
            while let Some(node) = current {
                keys.push(node.key.clone());
                current = &node.next;
            }
        }
        keys
    }
    
    pub fn values(&self) -> Vec<V> {
        let mut values = Vec::with_capacity(self.size);
        for bucket in &self.buckets {
            let mut current = bucket;
            while let Some(node) = current {
                values.push(node.value.clone());
                current = &node.next;
            }
        }
        values
    }
}

// Open Addressing Hash Map
pub struct OpenAddressHashMap<K, V> {
    keys: Vec<Option<K>>,
    values: Vec<Option<V>>,
    deleted: Vec<bool>,
    size: usize,
    capacity: usize,
    load_factor: f64,
}

impl<K, V> OpenAddressHashMap<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(16)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        OpenAddressHashMap {
            keys: vec![None; capacity],
            values: vec![None; capacity],
            deleted: vec![false; capacity],
            size: 0,
            capacity,
            load_factor: 0.75,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    fn find_slot(&self, key: &K) -> (usize, bool) {
        let mut index = self.hash(key);
        
        while self.keys[index].is_some() {
            if let Some(k) = &self.keys[index] {
                if k == key && !self.deleted[index] {
                    return (index, true);
                }
            }
            index = (index + 1) % self.capacity;
        }
        
        (index, false)
    }
    
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        let (index, found) = self.find_slot(&key);
        
        if found {
            // Update existing
            let old = self.values[index].take();
            self.values[index] = Some(value);
            old
        } else {
            // Insert new
            self.keys[index] = Some(key);
            self.values[index] = Some(value);
            self.deleted[index] = false;
            self.size += 1;
            
            if self.size as f64 > self.capacity as f64 * self.load_factor {
                self.resize();
            }
            None
        }
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let (index, found) = self.find_slot(key);
        if found {
            self.values[index].as_ref()
        } else {
            None
        }
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let (index, found) = self.find_slot(key);
        if found {
            self.deleted[index] = true;
            self.size -= 1;
            self.values[index].take()
        } else {
            None
        }
    }
    
    fn resize(&mut self) {
        let new_capacity = self.capacity * 2;
        let mut new_map = OpenAddressHashMap::with_capacity(new_capacity);
        
        for i in 0..self.capacity {
            if self.keys[i].is_some() && !self.deleted[i] {
                if let (Some(k), Some(v)) = (self.keys[i].take(), self.values[i].take()) {
                    new_map.insert(k, v);
                }
            }
        }
        
        *self = new_map;
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
}

// LRU Cache Implementation
use std::collections::{HashMap as StdHashMap, VecDeque};

pub struct LRUCache<K, V> {
    capacity: usize,
    map: StdHashMap<K, V>,
    order: VecDeque<K>,
}

impl<K, V> LRUCache<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new(capacity: usize) -> Self {
        LRUCache {
            capacity,
            map: StdHashMap::new(),
            order: VecDeque::new(),
        }
    }
    
    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            // Move to front (most recent)
            self.order.retain(|k| k != key);
            self.order.push_back(key.clone());
            self.map.get(key)
        } else {
            None
        }
    }
    
    pub fn put(&mut self, key: K, value: V) {
        if self.map.contains_key(&key) {
            // Update existing
            self.order.retain(|k| k != &key);
        } else if self.map.len() >= self.capacity {
            // Remove least recently used
            if let Some(lru_key) = self.order.pop_front() {
                self.map.remove(&lru_key);
            }
        }
        
        self.order.push_back(key.clone());
        self.map.insert(key, value);
    }
}

// Frequency Counter
pub struct FrequencyCounter<T> {
    counts: StdHashMap<T, usize>,
}

impl<T> FrequencyCounter<T>
where
    T: Hash + Eq + Clone,
{
    pub fn new() -> Self {
        FrequencyCounter {
            counts: StdHashMap::new(),
        }
    }
    
    pub fn add(&mut self, item: T) {
        *self.counts.entry(item).or_insert(0) += 1;
    }
    
    pub fn get_frequency(&self, item: &T) -> usize {
        self.counts.get(item).copied().unwrap_or(0)
    }
    
    pub fn most_common(&self, n: usize) -> Vec<(T, usize)> {
        let mut items: Vec<_> = self.counts.iter()
            .map(|(k, v)| (k.clone(), *v))
            .collect();
        items.sort_by(|a, b| b.1.cmp(&a.1));
        items.into_iter().take(n).collect()
    }
}
```

### Rust Usage Examples

```rust
fn main() {
    // Example 1: Basic HashMap operations
    let mut map = HashMap::new();
    map.insert("apple", 5);
    map.insert("banana", 3);
    map.insert("orange", 7);
    
    println!("Apple: {:?}", map.get(&"apple")); // Some(5)
    println!("Contains grape: {}", map.contains_key(&"grape")); // false
    
    // Example 2: Open Addressing HashMap
    let mut open_map = OpenAddressHashMap::new();
    open_map.insert(1, "one");
    open_map.insert(2, "two");
    open_map.insert(3, "three");
    
    println!("Value at 2: {:?}", open_map.get(&2)); // Some("two")
    
    // Example 3: LRU Cache
    let mut lru = LRUCache::new(2);
    lru.put(1, "one");
    lru.put(2, "two");
    println!("Get 1: {:?}", lru.get(&1)); // Some("one")
    lru.put(3, "three"); // Evicts key 2
    println!("Get 2: {:?}", lru.get(&2)); // None
    
    // Example 4: Frequency Counter
    let mut counter = FrequencyCounter::new();
    for word in ["apple", "banana", "apple", "cherry", "apple", "banana"] {
        counter.add(word);
    }
    println!("Most common: {:?}", counter.most_common(2)); 
    // [("apple", 3), ("banana", 2)]
}
```

## Common Operations and Complexity {#common-operations}

### Time Complexity

| Operation | Average Case | Worst Case | Notes |
|-----------|-------------|------------|--------|
| Insert | O(1) | O(n) | Worst case when all keys hash to same bucket |
| Search | O(1) | O(n) | Depends on collision resolution |
| Delete | O(1) | O(n) | Similar to search |
| Resize | O(n) | O(n) | Rehashing all elements |

### Space Complexity
- O(n) where n is the number of key-value pairs
- Additional space for collision resolution structures

### Choosing Between Implementations

**Chaining**
- Pros: Simple, handles collisions well, never gets "full"
- Cons: Extra memory for pointers, poor cache locality
- Use when: Hash function quality is uncertain

**Open Addressing**
- Pros: Better cache performance, less memory overhead
- Cons: More complex deletion, clustering issues
- Use when: Memory is limited, good hash function available

## Advanced Topics {#advanced-topics}

### Custom Hash Functions

```python
# Python custom hash function
class CustomHashMap:
    def _hash(self, key):
        # Example: polynomial rolling hash for strings
        if isinstance(key, str):
            hash_value = 0
            p = 31
            p_pow = 1
            for char in key:
                hash_value = (hash_value + ord(char) * p_pow) % self.capacity
                p_pow = (p_pow * p) % self.capacity
            return hash_value
        return hash(key) % self.capacity
```

```rust
// Rust custom hash function
impl<K, V> HashMap<K, V> {
    fn custom_hash(&self, key: &str) -> usize {
        let mut hash = 0u64;
        let p = 31u64;
        let mut p_pow = 1u64;
        
        for byte in key.bytes() {
            hash = hash.wrapping_add((byte as u64).wrapping_mul(p_pow));
            p_pow = p_pow.wrapping_mul(p);
        }
        
        (hash as usize) % self.capacity
    }
}
```

### Thread-Safe Maps

```python
# Python thread-safe map using threading.Lock
import threading

class ThreadSafeHashMap:
    def __init__(self):
        self.map = {}
        self.lock = threading.RLock()
    
    def put(self, key, value):
        with self.lock:
            self.map[key] = value
    
    def get(self, key):
        with self.lock:
            return self.map.get(key)
```

```rust
// Rust thread-safe map using Arc and Mutex
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

type ThreadSafeMap<K, V> = Arc<Mutex<HashMap<K, V>>>;

fn create_thread_safe_map<K, V>() -> ThreadSafeMap<K, V> {
    Arc::new(Mutex::new(HashMap::new()))
}
```

### Consistent Hashing

```python
# Consistent hashing for distributed systems
import hashlib
import bisect

class ConsistentHash:
    def __init__(self, nodes=None, virtual_nodes=150):
        self.nodes = nodes or []
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        self._build_ring()
    
    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def _build_ring(self):
        self.ring = {}
        self.sorted_keys = []
        
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                virtual_key = f"{node}:{i}"
                hash_value = self._hash(virtual_key)
                self.ring[hash_value] = node
                self.sorted_keys.append(hash_value)
        
        self.sorted_keys.sort()
    
    def get_node(self, key):
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        index = bisect.bisect_right(self.sorted_keys, hash_value)
        
        if index == len(self.sorted_keys):
            index = 0
        
        return self.ring[self.sorted_keys[index]]
```

## Practice Problems {#practice-problems}

### 1. Two Sum
Find two numbers in an array that add up to a target.

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

### 2. Group Anagrams
Group strings that are anagrams of each other.

```python
def group_anagrams(strs):
    from collections import defaultdict
    anagrams = defaultdict(list)
    
    for s in strs:
        # Use sorted string as key
        key = tuple(sorted(s))
        anagrams[key].append(s)

    return list(anagrams.values())
```

I'll create a detailed ASCII diagram showing how the Map data structure works step-by-step, covering the key operations like insertion, lookup, and collision handling.I've created a comprehensive ASCII diagram showing how Map (Hash Map) data structures work step-by-step. The diagram covers:

1. **Initial empty state** - showing the underlying array structure
2. **First insertion** - demonstrating hash function and direct placement
3. **Second insertion** - showing placement in a different bucket
4. **Collision handling** - illustrating how separate chaining works when two keys hash to the same index
5. **Lookup operation** - step-by-step traversal to find a key
6. **Deletion** - removing an element from a chain
7. **Dynamic resizing** - how the map grows when load factor gets too high

The diagram shows the most common implementation using:
- **Array-based storage** with fixed-size buckets
- **Separate chaining** for collision resolution (linked lists)
- **Dynamic resizing** to maintain performance
- **Hash functions** that map keys to array indices

Key concepts illustrated:
- Hash functions convert keys to array indices
- Collisions are handled by chaining elements together
- Load factor management through resizing
- Time complexity analysis for different operations

This gives you a visual understanding of why maps provide O(1) average-case performance for insertions, lookups, and deletions, while also showing what happens in worst-case scenarios when many collisions occur.

# Map Data Structure - Step-by-Step Operation

## Overview: Hash Map Structure
```
Hash Map (using separate chaining for collision resolution)
┌─────────────────────────────────────────────────────────┐
│                    Hash Table Array                     │
├─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────────┤
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │   ...   │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────────┘
```

## Step 1: Initial Empty Map
```
Initial State: map = {}
Array Size: 8 (typical starting size)

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │NULL │NULL │NULL │NULL │NULL │NULL │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

## Step 2: Insert First Key-Value Pair
```
Operation: map.put("apple", 100)

Hash Function: hash("apple") = 5 (simplified)
Index: 5 % 8 = 5

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │NULL │NULL │NULL │  ●  │NULL │NULL │
└─────┴─────┴─────┴─────┴─────┴──│──┴─────┴─────┘
                                  │
                                  ▼
                            ┌─────────────┐
                            │"apple" : 100│
                            │   next: NULL│
                            └─────────────┘
```

## Step 3: Insert Second Key-Value Pair (No Collision)
```
Operation: map.put("banana", 200)

Hash Function: hash("banana") = 2
Index: 2 % 8 = 2

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │  ●  │NULL │NULL │  ●  │NULL │NULL │
└─────┴─────┴──│──┴─────┴─────┴──│──┴─────┴─────┘
                │                 │
                ▼                 ▼
         ┌──────────────┐   ┌─────────────┐
         │"banana" : 200│   │"apple" : 100│
         │   next: NULL │   │   next: NULL│
         └──────────────┘   └─────────────┘
```

## Step 4: Insert Third Key-Value Pair (Collision!)
```
Operation: map.put("cherry", 300)

Hash Function: hash("cherry") = 5 (same as "apple"!)
Index: 5 % 8 = 5 → COLLISION!

Collision Resolution using Separate Chaining:

┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │  ●  │NULL │NULL │  ●  │NULL │NULL │
└─────┴─────┴──│──┴─────┴─────┴──│──┴─────┴─────┘
                │                 │
                ▼                 ▼
         ┌──────────────┐   ┌─────────────┐
         │"banana" : 200│   │"cherry": 300│ ← New node
         │   next: NULL │   │   next:  ●  │
         └──────────────┘   └─────────│───┘
                                      │
                                      ▼
                                ┌─────────────┐
                                │"apple" : 100│ ← Existing node
                                │   next: NULL│
                                └─────────────┘
```

## Step 5: Lookup Operation
```
Operation: value = map.get("apple")

Step 5a: Calculate hash
hash("apple") = 5
index = 5 % 8 = 5

Step 5b: Traverse chain at index 5
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │  ●  │NULL │NULL │  ●  │NULL │NULL │
└─────┴─────┴──│──┴─────┴─────┴──│──┴─────┴─────┘
                │                 │
                ▼                 ▼
         ┌──────────────┐   ┌─────────────┐
         │"banana" : 200│   │"cherry": 300│ ← Check: "cherry" ≠ "apple"
         │   next: NULL │   │   next:  ●  │
         └──────────────┘   └─────────│───┘
                                      │
                                      ▼
                                ┌─────────────┐
                                │"apple" : 100│ ← Found! Return 100
                                │   next: NULL│
                                └─────────────┘

Result: value = 100
```

## Step 6: Delete Operation
```
Operation: map.remove("cherry")

Step 6a: Find the key
hash("cherry") = 5, index = 5
Traverse chain to find "cherry"

Step 6b: Remove node from chain
Before removal:
┌─────────────┐    ┌─────────────┐
│"cherry": 300│ →  │"apple" : 100│
│   next:  ●  │    │   next: NULL│
└─────────────┘    └─────────────┘

After removal:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ [0] │ [1] │ [2] │ [3] │ [4] │ [5] │ [6] │ [7] │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│NULL │NULL │  ●  │NULL │NULL │  ●  │NULL │NULL │
└─────┴─────┴──│──┴─────┴─────┴──│──┴─────┴─────┘
                │                 │
                ▼                 ▼
         ┌──────────────┐   ┌─────────────┐
         │"banana" : 200│   │"apple" : 100│ ← "cherry" removed
         │   next: NULL │   │   next: NULL│
         └──────────────┘   └─────────────┘
```

## Step 7: Dynamic Resizing (Load Factor > 0.75)
```
Current state: 2 elements in 8 slots
Load Factor = 2/8 = 0.25 (OK)

If we add more elements and reach load factor > 0.75:
- Create new array of size 16 (double the size)
- Rehash all existing elements to new positions
- Update internal array reference

Before resize (8 slots):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

After resize (16 slots):
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │ 10  │ 11  │ 12  │ 13  │ 14  │ 15  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Elements rehashed with new modulo (% 16) instead of (% 8)
```

## Key Operations Summary

### Time Complexities:
```
┌─────────────┬─────────────┬──────────────┬─────────────┐
│ Operation   │ Best Case   │ Average Case │ Worst Case  │
├─────────────┼─────────────┼──────────────┼─────────────┤
│ Insert      │    O(1)     │     O(1)     │    O(n)     │
│ Lookup      │    O(1)     │     O(1)     │    O(n)     │
│ Delete      │    O(1)     │     O(1)     │    O(n)     │
└─────────────┴─────────────┴──────────────┴─────────────┘
```

### Hash Function Properties:
1. **Deterministic**: Same input always produces same hash
2. **Uniform Distribution**: Spreads keys evenly across buckets  
3. **Fast Computation**: Efficient to calculate
4. **Avalanche Effect**: Small input changes cause large hash changes

### Collision Resolution Methods:
1. **Separate Chaining** (shown above): Use linked lists
2. **Open Addressing**: Linear probing, quadratic probing, double hashing
3. **Robin Hood Hashing**: Minimize variance in probe distances