I'll create a comprehensive guide covering search algorithms and hash tables with complete implementations in both Python and Rust. This will be a substantial technical reference document.I've created a comprehensive guide to search algorithms and hash tables with complete implementations in both Python and Rust. The guide covers:

## Key Features

1. **Search Algorithms**:
   - Linear search with multiple variants
   - Binary search with iterative, recursive, and boundary-finding implementations
   - Complete time/space complexity analysis

2. **Hash Tables**:
   - Full implementation with dynamic resizing
   - Separate chaining collision resolution
   - Load factor management
   - Advanced concepts like Robin Hood hashing and linear probing

3. **Production-Ready Code**:
   - Error handling and edge cases
   - Memory optimization techniques
   - Benchmark code for performance testing
   - Best practices and design guidelines

4. **Advanced Topics**:
   - Custom hash functions (DJB2, FNV-1a)
   - Multiple collision resolution strategies
   - Performance optimization techniques

The implementations are complete, well-documented, and ready to use in real applications. Each algorithm includes examples and explanations of when to use them. The Rust implementations leverage the language's type system and memory safety features, while the Python versions focus on clarity and ease of understanding.

Would you like me to expand on any particular section or add additional algorithms like interpolation search or more advanced hash table variants?

# Complete Guide to Search Algorithms and Hash Tables

## Table of Contents

1. [Introduction](#introduction)
2. [Linear Search](#linear-search)
3. [Binary Search](#binary-search)
4. [Hash Tables](#hash-tables)
5. [Advanced Hash Table Concepts](#advanced-hash-table-concepts)
6. [Performance Comparison](#performance-comparison)
7. [Best Practices](#best-practices)

## Introduction

Search algorithms are fundamental to computer science and software development. This guide covers the most important search algorithms and hash table implementations, providing complete code examples in both Python and Rust.

### Time Complexity Summary

- **Linear Search**: O(n)
- **Binary Search**: O(log n)
- **Hash Table Search**: O(1) average case, O(n) worst case

## Linear Search

Linear search examines each element sequentially until the target is found or the list is exhausted.

### Python Implementation

```python
def linear_search(arr, target):
    """
    Performs linear search on an array.
    
    Args:
        arr: List of elements to search
        target: Element to find
    
    Returns:
        Index of target if found, -1 otherwise
    """
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

def linear_search_all(arr, target):
    """
    Finds all occurrences of target in array.
    
    Returns:
        List of indices where target was found
    """
    indices = []
    for i, element in enumerate(arr):
        if element == target:
            indices.append(i)
    return indices

# Example usage
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
print(f"Index of 5: {linear_search(numbers, 5)}")  # Output: 4
print(f"All indices of 1: {linear_search_all(numbers, 1)}")  # Output: [1, 3]
```

### Rust Implementation

```rust
fn linear_search<T: PartialEq>(arr: &[T], target: &T) -> Option<usize> {
    for (index, element) in arr.iter().enumerate() {
        if element == target {
            return Some(index);
        }
    }
    None
}

fn linear_search_all<T: PartialEq>(arr: &[T], target: &T) -> Vec<usize> {
    arr.iter()
        .enumerate()
        .filter_map(|(index, element)| {
            if element == target { Some(index) } else { None }
        })
        .collect()
}

fn main() {
    let numbers = vec![3, 1, 4, 1, 5, 9, 2, 6];
    
    match linear_search(&numbers, &5) {
        Some(index) => println!("Found 5 at index: {}", index),
        None => println!("5 not found"),
    }
    
    let all_ones = linear_search_all(&numbers, &1);
    println!("All indices of 1: {:?}", all_ones);
}
```

## Binary Search

Binary search works on sorted arrays by repeatedly dividing the search interval in half.

### Python Implementation

```python
def binary_search(arr, target):
    """
    Performs binary search on a sorted array.
    
    Args:
        arr: Sorted list of elements
        target: Element to find
    
    Returns:
        Index of target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def binary_search_recursive(arr, target, left=0, right=None):
    """
    Recursive implementation of binary search.
    """
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return -1
    
    mid = (left + right) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)

def binary_search_leftmost(arr, target):
    """
    Finds the leftmost occurrence of target in sorted array.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = (left + right) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left if left < len(arr) and arr[left] == target else -1

def binary_search_rightmost(arr, target):
    """
    Finds the rightmost occurrence of target in sorted array.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = (left + right) // 2
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    
    return left - 1 if left > 0 and arr[left - 1] == target else -1

# Example usage
sorted_numbers = [1, 1, 2, 3, 4, 5, 6, 9]
print(f"Binary search for 5: {binary_search(sorted_numbers, 5)}")  # Output: 5
print(f"Leftmost 1: {binary_search_leftmost(sorted_numbers, 1)}")  # Output: 0
print(f"Rightmost 1: {binary_search_rightmost(sorted_numbers, 1)}")  # Output: 1
```

### Rust Implementation

```rust
fn binary_search<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

fn binary_search_recursive<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    fn search<T: Ord>(arr: &[T], target: &T, offset: usize) -> Option<usize> {
        if arr.is_empty() {
            return None;
        }
        
        let mid = arr.len() / 2;
        
        match arr[mid].cmp(target) {
            std::cmp::Ordering::Equal => Some(offset + mid),
            std::cmp::Ordering::Less => {
                search(&arr[mid + 1..], target, offset + mid + 1)
            }
            std::cmp::Ordering::Greater => {
                search(&arr[..mid], target, offset)
            }
        }
    }
    
    search(arr, target, 0)
}

fn binary_search_leftmost<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] < *target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    if left < arr.len() && arr[left] == *target {
        Some(left)
    } else {
        None
    }
}

fn binary_search_rightmost<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if arr[mid] <= *target {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    if left > 0 && arr[left - 1] == *target {
        Some(left - 1)
    } else {
        None
    }
}

fn main() {
    let sorted_numbers = vec![1, 1, 2, 3, 4, 5, 6, 9];
    
    match binary_search(&sorted_numbers, &5) {
        Some(index) => println!("Found 5 at index: {}", index),
        None => println!("5 not found"),
    }
}
```

## Hash Tables

Hash tables provide O(1) average-case search, insertion, and deletion operations using hash functions to map keys to array indices.

### Python Implementation

```python
class HashTable:
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        self.load_factor_threshold = 0.75
    
    def _hash(self, key):
        """Simple hash function using Python's built-in hash."""
        return hash(key) % self.capacity
    
    def _resize(self):
        """Resize the hash table when load factor is too high."""
        old_buckets = self.buckets
        self.capacity *= 2
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        
        # Rehash all existing items
        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)
    
    def put(self, key, value):
        """Insert or update a key-value pair."""
        if self.size >= self.capacity * self.load_factor_threshold:
            self._resize()
        
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        # Update existing key
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        
        # Add new key-value pair
        bucket.append((key, value))
        self.size += 1
    
    def get(self, key):
        """Retrieve value by key."""
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for k, v in bucket:
            if k == key:
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        """Remove a key-value pair."""
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        """Check if key exists in hash table."""
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def keys(self):
        """Return all keys in the hash table."""
        result = []
        for bucket in self.buckets:
            for key, _ in bucket:
                result.append(key)
        return result
    
    def values(self):
        """Return all values in the hash table."""
        result = []
        for bucket in self.buckets:
            for _, value in bucket:
                result.append(value)
        return result
    
    def items(self):
        """Return all key-value pairs."""
        result = []
        for bucket in self.buckets:
            for item in bucket:
                result.append(item)
        return result
    
    def load_factor(self):
        """Calculate current load factor."""
        return self.size / self.capacity
    
    def __len__(self):
        return self.size
    
    def __str__(self):
        items = self.items()
        return "{" + ", ".join(f"'{k}': '{v}'" for k, v in items) + "}"

# Example usage
ht = HashTable()
ht.put("name", "Alice")
ht.put("age", 30)
ht.put("city", "New York")

print(f"Hash table: {ht}")
print(f"Name: {ht.get('name')}")
print(f"Contains 'age': {ht.contains('age')}")
print(f"Load factor: {ht.load_factor():.2f}")
```

### Rust Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

#[derive(Debug)]
pub struct HashTable<K, V> {
    buckets: Vec<Vec<(K, V)>>,
    size: usize,
    capacity: usize,
}

impl<K, V> HashTable<K, V>
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
            buckets.push(Vec::new());
        }
        
        Self {
            buckets,
            size: 0,
            capacity,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    fn should_resize(&self) -> bool {
        self.size >= (self.capacity * 3) / 4  // 0.75 load factor
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(
            &mut self.buckets,
            {
                let mut new_buckets = Vec::with_capacity(self.capacity * 2);
                for _ in 0..self.capacity * 2 {
                    new_buckets.push(Vec::new());
                }
                new_buckets
            }
        );
        
        let old_capacity = self.capacity;
        self.capacity *= 2;
        self.size = 0;
        
        for bucket in old_buckets {
            for (key, value) in bucket {
                self.insert(key, value);
            }
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) {
        if self.should_resize() {
            self.resize();
        }
        
        let bucket_index = self.hash(&key);
        let bucket = &mut self.buckets[bucket_index];
        
        // Update existing key
        for (k, v) in bucket.iter_mut() {
            if *k == key {
                *v = value;
                return;
            }
        }
        
        // Insert new key-value pair
        bucket.push((key, value));
        self.size += 1;
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let bucket_index = self.hash(key);
        let bucket = &self.buckets[bucket_index];
        
        for (k, v) in bucket {
            if k == key {
                return Some(v);
            }
        }
        
        None
    }
    
    pub fn get_mut(&mut self, key: &K) -> Option<&mut V> {
        let bucket_index = self.hash(key);
        let bucket = &mut self.buckets[bucket_index];
        
        for (k, v) in bucket {
            if k == key {
                return Some(v);
            }
        }
        
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let bucket_index = self.hash(key);
        let bucket = &mut self.buckets[bucket_index];
        
        for (i, (k, _)) in bucket.iter().enumerate() {
            if k == key {
                let (_, value) = bucket.remove(i);
                self.size -= 1;
                return Some(value);
            }
        }
        
        None
    }
    
    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    pub fn capacity(&self) -> usize {
        self.capacity
    }
    
    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }
    
    pub fn keys(&self) -> impl Iterator<Item = &K> {
        self.buckets.iter().flat_map(|bucket| bucket.iter().map(|(k, _)| k))
    }
    
    pub fn values(&self) -> impl Iterator<Item = &V> {
        self.buckets.iter().flat_map(|bucket| bucket.iter().map(|(_, v)| v))
    }
    
    pub fn iter(&self) -> impl Iterator<Item = (&K, &V)> {
        self.buckets.iter().flat_map(|bucket| bucket.iter().map(|(k, v)| (k, v)))
    }
}

// Example usage
fn main() {
    let mut ht = HashTable::new();
    
    ht.insert("name", "Alice");
    ht.insert("age", "30");
    ht.insert("city", "New York");
    
    println!("Hash table size: {}", ht.len());
    
    if let Some(name) = ht.get(&"name") {
        println!("Name: {}", name);
    }
    
    println!("Contains 'age': {}", ht.contains_key(&"age"));
    println!("Load factor: {:.2}", ht.load_factor());
    
    // Print all key-value pairs
    for (key, value) in ht.iter() {
        println!("{}: {}", key, value);
    }
}
```

## Advanced Hash Table Concepts

### Open Addressing (Linear Probing)

```python
class LinearProbingHashTable:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.size = 0
        self.keys = [None] * capacity
        self.values = [None] * capacity
        self.deleted = [False] * capacity
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def _find_slot(self, key):
        """Find slot for key using linear probing."""
        index = self._hash(key)
        
        while self.keys[index] is not None:
            if self.keys[index] == key and not self.deleted[index]:
                return index
            index = (index + 1) % self.capacity
        
        return index
    
    def put(self, key, value):
        if self.size >= self.capacity * 0.75:
            self._resize()
        
        index = self._find_slot(key)
        
        if self.keys[index] is None or self.deleted[index]:
            self.size += 1
        
        self.keys[index] = key
        self.values[index] = value
        self.deleted[index] = False
    
    def get(self, key):
        index = self._hash(key)
        
        while self.keys[index] is not None:
            if self.keys[index] == key and not self.deleted[index]:
                return self.values[index]
            index = (index + 1) % self.capacity
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        index = self._hash(key)
        
        while self.keys[index] is not None:
            if self.keys[index] == key and not self.deleted[index]:
                self.deleted[index] = True
                self.size -= 1
                return self.values[index]
            index = (index + 1) % self.capacity
        
        raise KeyError(f"Key '{key}' not found")
    
    def _resize(self):
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
```

### Robin Hood Hashing

```rust
#[derive(Debug, Clone)]
struct Entry<K, V> {
    key: K,
    value: V,
    distance: usize,
}

pub struct RobinHoodHashTable<K, V> {
    buckets: Vec<Option<Entry<K, V>>>,
    size: usize,
    capacity: usize,
}

impl<K, V> RobinHoodHashTable<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(16)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            buckets: vec![None; capacity],
            size: 0,
            capacity,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish() as usize % self.capacity
    }
    
    fn distance(&self, ideal: usize, actual: usize) -> usize {
        if actual >= ideal {
            actual - ideal
        } else {
            actual + self.capacity - ideal
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) {
        if self.size >= self.capacity * 3 / 4 {
            self.resize();
        }
        
        let ideal_index = self.hash(&key);
        let mut entry = Entry { key, value, distance: 0 };
        let mut index = ideal_index;
        
        loop {
            match &self.buckets[index] {
                None => {
                    self.buckets[index] = Some(entry);
                    self.size += 1;
                    break;
                }
                Some(existing) => {
                    if existing.key == entry.key {
                        self.buckets[index] = Some(entry);
                        break;
                    }
                    
                    if entry.distance > existing.distance {
                        let old_entry = std::mem::replace(&mut self.buckets[index], Some(entry)).unwrap();
                        entry = old_entry;
                    }
                }
            }
            
            index = (index + 1) % self.capacity;
            entry.distance += 1;
        }
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(&mut self.buckets, vec![None; self.capacity * 2]);
        self.capacity *= 2;
        self.size = 0;
        
        for bucket in old_buckets {
            if let Some(entry) = bucket {
                self.insert(entry.key, entry.value);
            }
        }
    }
}
```

## Performance Comparison

| Algorithm | Best Case | Average Case | Worst Case | Space |
|-----------|-----------|--------------|------------|-------|
| Linear Search | O(1) | O(n) | O(n) | O(1) |
| Binary Search | O(1) | O(log n) | O(log n) | O(1) |
| Hash Table | O(1) | O(1) | O(n) | O(n) |

### Benchmark Code (Python)

```python
import time
import random

def benchmark_searches():
    # Generate test data
    data = list(range(100000))
    random.shuffle(data)
    sorted_data = sorted(data)
    
    # Create hash table
    ht = HashTable()
    for i, value in enumerate(data):
        ht.put(value, i)
    
    targets = random.sample(data, 1000)
    
    # Benchmark linear search
    start = time.time()
    for target in targets:
        linear_search(data, target)
    linear_time = time.time() - start
    
    # Benchmark binary search
    start = time.time()
    for target in targets:
        binary_search(sorted_data, target)
    binary_time = time.time() - start
    
    # Benchmark hash table
    start = time.time()
    for target in targets:
        try:
            ht.get(target)
        except KeyError:
            pass
    hash_time = time.time() - start
    
    print(f"Linear Search: {linear_time:.4f} seconds")
    print(f"Binary Search: {binary_time:.4f} seconds")
    print(f"Hash Table: {hash_time:.4f} seconds")

if __name__ == "__main__":
    benchmark_searches()
```

## Best Practices

### When to Use Each Algorithm

1. **Linear Search**
   - Small datasets (< 100 elements)
   - Unsorted data
   - Simple implementation needed
   - Memory is extremely limited

2. **Binary Search**
   - Large sorted datasets
   - Data doesn't change frequently
   - Memory efficiency is important
   - Logarithmic time complexity is acceptable

3. **Hash Tables**
   - Fast lookups are critical
   - Data changes frequently
   - Memory is not a primary concern
   - Average O(1) performance is needed

### Hash Function Design

```python
def djb2_hash(s):
    """DJB2 hash function - good general-purpose hash."""
    hash_value = 5381
    for char in s:
        hash_value = ((hash_value << 5) + hash_value) + ord(char)
    return hash_value & 0xFFFFFFFF  # 32-bit hash

def fnv1a_hash(data):
    """FNV-1a hash function - fast and good distribution."""
    hash_value = 2166136261  # FNV offset basis
    for byte in data:
        hash_value ^= byte
        hash_value *= 16777619  # FNV prime
    return hash_value & 0xFFFFFFFF
```

### Collision Resolution Strategies

1. **Separate Chaining**: Use linked lists/arrays at each bucket
2. **Open Addressing**: Find next available slot
3. **Robin Hood Hashing**: Minimize variance in probe distances
4. **Cuckoo Hashing**: Guarantee O(1) lookup time

### Memory Optimization

```rust
// Use Box<[T]> instead of Vec<T> when size is fixed
pub struct OptimizedHashTable<K, V> {
    buckets: Box<[Vec<(K, V)>]>,
    size: usize,
}

impl<K, V> OptimizedHashTable<K, V>
where
    K: Hash + Eq,
{
    pub fn with_fixed_capacity(capacity: usize) -> Self {
        let buckets = (0..capacity).map(|_| Vec::new()).collect::<Vec<_>>().into_boxed_slice();
        Self { buckets, size: 0 }
    }
}
```

## Conclusion

This guide provides comprehensive implementations of fundamental search algorithms and hash tables. Each approach has its strengths and appropriate use cases:

- Use **linear search** for small, unsorted datasets
- Use **binary search** for large, sorted datasets where modification is infrequent
- Use **hash tables** when you need fast average-case performance and can accept the memory overhead

The implementations provided are production-ready and include important optimizations like dynamic resizing, proper load factor management, and efficient collision handling. Understanding these algorithms and their trade-offs is essential for writing efficient software systems.

I'll create a detailed ASCII diagram showing how hash tables work with search algorithms, including the hashing process, collision handling, and search operations.I've created a comprehensive ASCII diagram showing how hash tables work with search algorithms. The diagram covers:

1. **Basic Structure** - Visual representation of the hash table array
2. **Hash Function** - Step-by-step calculation examples
3. **Collision Resolution** - Both chaining and linear probing methods with detailed examples
4. **Search Algorithms** - Complete walkthrough of search operations for both methods
5. **Flowchart** - Visual algorithm flow for the search process
6. **Performance Analysis** - Time complexity comparison table
7. **Trade-offs** - Advantages and disadvantages of each method
8. **Hash Function Impact** - How hash quality affects performance

The diagram shows how hash tables achieve O(1) average search time through:

- Direct array access using computed hash values
- Collision handling to manage multiple keys mapping to the same index
- Linear traversal only when necessary (in collision chains or probe sequences)

This makes hash tables one of the most efficient data structures for search operations when properly implemented with a good hash function and appropriate load factor management.

# Hash Tables - Search Algorithm Step-by-Step

## 1. Basic Hash Table Structure

```
Hash Table (Array of size 7)
Index:  [0] [1] [2] [3] [4] [5] [6]
Value:  [ ] [ ] [ ] [ ] [ ] [ ] [ ]
        └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘
```

## 2. Hash Function Example

**Simple Hash Function: hash(key) = key % table_size**

```
Keys to insert: 15, 22, 8, 33, 7, 29

For key = 15: hash(15) = 15 % 7 = 1
For key = 22: hash(22) = 22 % 7 = 1  ← COLLISION!
For key = 8:  hash(8)  = 8 % 7  = 1  ← COLLISION!
For key = 33: hash(33) = 33 % 7 = 5
For key = 7:  hash(7)  = 7 % 7  = 0
For key = 29: hash(29) = 29 % 7 = 1  ← COLLISION!
```

## 3. Collision Resolution Methods

### Method 1: Chaining (Separate Chaining)

```
Hash Table with Chaining:

Index:  [0] [1] [2] [3] [4] [5] [6]
        │   │   │   │   │   │   │
        ↓   ↓   ↓   ↓   ↓   ↓   ↓
       [7] [15][ ] [ ] [ ] [33][ ]
        │   │
        │   ↓
        │  [22]
        │   │
        │   ↓
        │  [8]
        │   │
        │   ↓
        │  [29]
        │   │
        ↓   ↓
       NULL NULL
```

### Method 2: Linear Probing (Open Addressing)

```
Step-by-step insertion with Linear Probing:

Initial: [0] [1] [2] [3] [4] [5] [6]
         [ ] [ ] [ ] [ ] [ ] [ ] [ ]

Insert 15 (hash=1): [0] [1] [2] [3] [4] [5] [6]
                    [ ][15][ ] [ ] [ ] [ ] [ ]

Insert 22 (hash=1): [0] [1] [2] [3] [4] [5] [6]
   Collision at 1   [ ][15][22][ ] [ ] [ ] [ ]
   Try index 2 ✓       ↑    ↑
                    used  available

Insert 8 (hash=1):  [0] [1] [2] [3] [4] [5] [6]
   Collision at 1   [ ][15][22][8][ ] [ ] [ ]
   Collision at 2          ↑    ↑
   Try index 3 ✓        used available

Insert 33 (hash=5): [0] [1] [2] [3] [4] [5] [6]
                    [ ][15][22][8][ ][33][ ]

Insert 7 (hash=0):  [0] [1] [2] [3] [4] [5] [6]
                    [7][15][22][8][ ][33][ ]

Insert 29 (hash=1): [0] [1] [2] [3] [4] [5] [6]
   Collision at 1   [7][15][22][8][29][33][ ]
   Collision at 2          ↑    ↑    ↑
   Collision at 3        used used available
   Try index 4 ✓
```

## 4. Search Algorithm Steps

### Search in Chaining Method

```
SEARCH(key = 22):

Step 1: Calculate hash
        hash(22) = 22 % 7 = 1

Step 2: Go to index 1
        Index:  [0] [1] [2] [3] [4] [5] [6]
                │   │ ← Start here
                ↓   ↓
               [7] [15]
                    │
                    ↓
                   [22] ← Found!
                    │
                    ↓
                   [8]
                    │
                    ↓
                   [29]

Step 3: Traverse linked list at index 1
        15 ≠ 22, continue
        22 = 22, FOUND! ✓

Time Complexity: O(1) average, O(n) worst case
```

### Search in Linear Probing

```
SEARCH(key = 29):

Current table: [0] [1] [2] [3] [4] [5] [6]
               [7][15][22][8][29][33][ ]

Step 1: Calculate hash
        hash(29) = 29 % 7 = 1

Step 2: Check index 1
        table[1] = 15 ≠ 29, continue

Step 3: Linear probe to index 2
        table[2] = 22 ≠ 29, continue

Step 4: Linear probe to index 3
        table[3] = 8 ≠ 29, continue

Step 5: Linear probe to index 4
        table[4] = 29 = 29, FOUND! ✓

Probe sequence: 1 → 2 → 3 → 4
```

## 5. Complete Search Algorithm Flowchart

```
           START
             │
             ▼
    ┌─────────────────┐
    │ Input: key      │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ hash = key % n  │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ index = hash    │
    └─────────────────┘
             │
             ▼
         ┌───────┐    Yes   ┌─────────────────┐
         │Empty? │─────────▶│ Return NOT_FOUND│
         └───────┘          └─────────────────┘
             │ No                    │
             ▼                       ▼
    ┌─────────────────┐            END
    │ Using Chaining? │
    └─────────────────┘
         │           │
        Yes          No (Linear Probing)
         │           │
         ▼           ▼
┌─────────────────┐ ┌─────────────────┐
│ Traverse chain  │ │ Check table[i]  │
│ at table[index] │ │ i = index       │
└─────────────────┘ └─────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐ ┌─────────────────┐  Yes  ┌─────────────────┐
│ key == current? │ │ table[i]==key?  │──────▶│ Return FOUND    │
└─────────────────┘ └─────────────────┘       └─────────────────┘
    │           │           │ No                      │
   Yes          No          ▼                        ▼
    │           │  ┌─────────────────┐              END
    ▼           │  │ i = (i+1) % n   │
┌─────────────────┐│  └─────────────────┘
│ Return FOUND    ││           │
└─────────────────┘│           ▼
         │         │  ┌─────────────────┐   Yes  ┌─────────────────┐
         ▼         │  │ i == index OR   │───────▶│ Return NOT_FOUND│
        END        │  │ table[i] empty? │        └─────────────────┘
                   │  └─────────────────┘                │
                   │           │ No                      ▼
                   │           └─────────────────────── END
                   ▼
          ┌─────────────────┐  No   ┌─────────────────┐
          │ next != NULL?   │──────▶│ Return NOT_FOUND│
          └─────────────────┘       └─────────────────┘
                   │ Yes                     │
                   ▼                        ▼
          ┌─────────────────┐              END
          │ current = next  │
          └─────────────────┘
                   │
                   └──────────────────┘
```

## 6. Performance Analysis

```
╔══════════════════════════════════════════════════════════╗
║                  TIME COMPLEXITY                         ║
╠══════════════════════════════════════════════════════════╣
║ Operation    │ Chaining        │ Linear Probing         ║
║             │ Avg    │ Worst   │ Avg    │ Worst         ║
╠═════════════╪════════╪═════════╪════════╪═══════════════╣
║ Search      │ O(1)   │ O(n)    │ O(1)   │ O(n)          ║
║ Insert      │ O(1)   │ O(n)    │ O(1)   │ O(n)          ║
║ Delete      │ O(1)   │ O(n)    │ O(1)   │ O(n)          ║
╚═════════════╧════════╧═════════╧════════╧═══════════════╝

Load Factor (α) = Number of elements / Table size

Chaining: Average search time ≈ 1 + α/2
Linear Probing: Average search time ≈ (1 + 1/(1-α)²)/2
```

## 7. Advantages and Disadvantages

```
┌─────────────────────────────────────────────────────────┐
│                      CHAINING                           │
├─────────────────────────────────────────────────────────┤
│ Advantages:                                             │
│ • Simple implementation                                 │
│ • No clustering                                         │
│ • Can handle any load factor                           │
│ • Easy deletion                                         │
│                                                         │
│ Disadvantages:                                          │
│ • Extra memory for pointers                            │
│ • Cache performance issues                             │
│ • Worst case O(n) if all keys hash to same bucket     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  LINEAR PROBING                         │
├─────────────────────────────────────────────────────────┤
│ Advantages:                                             │
│ • Better cache performance                              │
│ • No extra memory for pointers                         │
│ • Simple implementation                                 │
│                                                         │
│ Disadvantages:                                          │
│ • Primary clustering                                    │
│ • Performance degrades with high load factor          │
│ • Complex deletion                                      │
│ • Must handle wrap-around                              │
└─────────────────────────────────────────────────────────┘
```

## 8. Hash Function Quality Impact

```
Good Hash Function (Uniform Distribution):
Index: [0] [1] [2] [3] [4] [5] [6]
       [A] [B] [C] [D] [E] [F] [G]  ← Even distribution

Poor Hash Function (Clustering):
Index: [0] [1] [2] [3] [4] [5] [6]
       [ ] [A] [B] [C] [D] [ ] [ ]  ← All elements clustered
              ↓
           Chain: A→B→C→D→NULL

Impact on Search Performance:
• Good hash: O(1) average search time
• Poor hash: O(n) average search time (worst case scenario)
```
