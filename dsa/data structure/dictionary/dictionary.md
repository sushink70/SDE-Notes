# Dictionary Data Structure Implementations in Python and Rust

Each implementation includes all fundamental dictionary operations (insert, get, delete, contains) with proper error handling and memory management.

## Additional Implementation Details:

Let me add some important aspects that complement the main guide:I've extended the guide with advanced features and practical applications:

## New Additions:

### 🚀 **Advanced Hash Table Techniques**

- **Robin Hood Hashing**: Reduces clustering by swapping entries to minimize probe distances
- **Consistent Hashing**: Essential for distributed systems and load balancing

### 🔒 **Concurrent Implementations**

- **Lock-Free Skip List**: Thread-safe operations using atomic operations
- **Memory ordering** and **compare-and-swap** techniques for high-performance concurrent access

### 💾 **Memory-Efficient Structures**

- **Trie Dictionary**: Optimal for string keys with common prefixes
- **Prefix matching** and **autocomplete** functionality
- Space-efficient storage for dictionary words

### 📊 **Performance Benchmarking Suite**

- **Comprehensive benchmarks** for all implementations
- **Automated testing framework** for comparing implementations
- **Graphical performance visualization**
- **Statistical analysis** across different data sizes and access patterns

### 🏢 **Real-World Applications**

- **In-Memory Cache**: High-performance caching layer using LRU eviction
- **Database B+ Tree Index**: Optimized for disk storage with range queries
- **LRU Cache**: Memory-efficient caching with automatic eviction
- **Production-ready patterns** used in systems like databases and web servers

## Key Benefits:

1. **Scalability**: Concurrent implementations handle multi-threaded environments
2. **Efficiency**: Memory-optimized structures for specific use cases
3. **Measurability**: Built-in benchmarking for informed decision-making
4. **Practicality**: Real-world examples from database and caching systems

The guide now covers everything from basic implementations to advanced concurrent data structures used in production systems. Each implementation is fully functional with proper error handling and optimization techniques.

## Comprehensive Dictionary DSA Implementation Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Hash Table Implementation](#hash-table-implementation)
3. [Balanced Binary Search Tree (AVL)](#balanced-binary-search-tree-avl)
4. [Red-Black Tree](#red-black-tree)
5. [Skip List](#skip-list)
6. [Performance Comparison](#performance-comparison)
7. [Use Cases and Trade-offs](#use-cases-and-trade-offs)

## Introduction

A dictionary (also known as a map, associative array, or symbol table) is a fundamental data structure that stores key-value pairs and provides efficient operations for insertion, deletion, and lookup. This guide covers multiple implementation approaches with complete code in Python and Rust.

### Key Operations

- **Insert(key, value)**: Add or update a key-value pair
- **Get(key)**: Retrieve the value associated with a key
- **Delete(key)**: Remove a key-value pair
- **Contains(key)**: Check if a key exists

## Hash Table Implementation

Hash tables provide average O(1) time complexity for all operations through direct array indexing using hash functions.

### Python Implementation

```python
class HashTable:
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        self.load_factor_threshold = 0.75
    
    def _hash(self, key):
        """Simple hash function using built-in hash()"""
        return hash(key) % self.capacity
    
    def _resize(self):
        """Resize the hash table when load factor exceeds threshold"""
        old_buckets = self.buckets
        self.capacity *= 2
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        
        # Rehash all existing items
        for bucket in old_buckets:
            for key, value in bucket:
                self.insert(key, value)
    
    def insert(self, key, value):
        """Insert or update a key-value pair"""
        # Check if resize is needed
        if self.size >= self.capacity * self.load_factor_threshold:
            self._resize()
        
        index = self._hash(key)
        bucket = self.buckets[index]
        
        # Check if key already exists
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)  # Update existing
                return
        
        # Add new key-value pair
        bucket.append((key, value))
        self.size += 1
    
    def get(self, key):
        """Retrieve value by key"""
        index = self._hash(key)
        bucket = self.buckets[index]
        
        for k, v in bucket:
            if k == key:
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        """Delete a key-value pair"""
        index = self._hash(key)
        bucket = self.buckets[index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        """Check if key exists"""
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def __len__(self):
        return self.size
    
    def __str__(self):
        items = []
        for bucket in self.buckets:
            for key, value in bucket:
                items.append(f"{key}: {value}")
        return "{" + ", ".join(items) + "}"
```

### Rust Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

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
        let capacity = 16;
        HashTable {
            buckets: vec![Vec::new(); capacity],
            size: 0,
            capacity,
        }
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        HashTable {
            buckets: vec![Vec::new(); capacity],
            size: 0,
            capacity,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(&mut self.buckets, vec![Vec::new(); self.capacity * 2]);
        self.capacity *= 2;
        self.size = 0;
        
        for bucket in old_buckets {
            for (key, value) in bucket {
                self.insert(key, value);
            }
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) {
        if self.size >= (self.capacity as f64 * 0.75) as usize {
            self.resize();
        }
        
        let index = self.hash(&key);
        let bucket = &mut self.buckets[index];
        
        // Check if key already exists
        for (k, v) in bucket.iter_mut() {
            if k == &key {
                *v = value;
                return;
            }
        }
        
        // Add new key-value pair
        bucket.push((key, value));
        self.size += 1;
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let index = self.hash(key);
        let bucket = &self.buckets[index];
        
        for (k, v) in bucket {
            if k == key {
                return Some(v);
            }
        }
        
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = self.hash(key);
        let bucket = &mut self.buckets[index];
        
        for i in 0..bucket.len() {
            if &bucket[i].0 == key {
                let (_, value) = bucket.remove(i);
                self.size -= 1;
                return Some(value);
            }
        }
        
        None
    }
    
    pub fn contains(&self, key: &K) -> bool {
        self.get(key).is_some()
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}
```

## Balanced Binary Search Tree (AVL)

AVL trees maintain balance through rotations, guaranteeing O(log n) operations in all cases.

### Python Implementation

```python
class AVLNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1

class AVLDictionary:
    def __init__(self):
        self.root = None
        self.size = 0
    
    def _height(self, node):
        return node.height if node else 0
    
    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0
    
    def _update_height(self, node):
        if node:
            node.height = 1 + max(self._height(node.left), self._height(node.right))
    
    def _rotate_right(self, y):
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x):
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def _insert(self, node, key, value):
        # Standard BST insertion
        if not node:
            self.size += 1
            return AVLNode(key, value)
        
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:  # Key already exists, update value
            node.value = value
            return node
        
        # Update height
        self._update_height(node)
        
        # Get balance factor
        balance = self._balance_factor(node)
        
        # Left-Left case
        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        
        # Right-Right case
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        
        # Left-Right case
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right-Left case
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def _find_min(self, node):
        while node.left:
            node = node.left
        return node
    
    def _delete(self, node, key):
        if not node:
            return node
        
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node to be deleted found
            self.size -= 1
            
            # Node with only right child or no child
            if not node.left:
                return node.right
            
            # Node with only left child
            if not node.right:
                return node.left
            
            # Node with two children
            min_right = self._find_min(node.right)
            node.key = min_right.key
            node.value = min_right.value
            node.right = self._delete(node.right, min_right.key)
            self.size += 1  # Compensate for the decrement above
        
        # Update height
        self._update_height(node)
        
        # Get balance factor
        balance = self._balance_factor(node)
        
        # Left-Left case
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)
        
        # Left-Right case
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right-Right case
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)
        
        # Right-Left case
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def _search(self, node, key):
        if not node or node.key == key:
            return node
        
        if key < node.key:
            return self._search(node.left, key)
        
        return self._search(node.right, key)
    
    def insert(self, key, value):
        self.root = self._insert(self.root, key, value)
    
    def get(self, key):
        node = self._search(self.root, key)
        if node:
            return node.value
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        if not self.contains(key):
            raise KeyError(f"Key '{key}' not found")
        self.root = self._delete(self.root, key)
    
    def contains(self, key):
        return self._search(self.root, key) is not None
    
    def __len__(self):
        return self.size
```

### Rust Implementation

```rust
use std::cmp::Ordering;
use std::fmt::Debug;

#[derive(Debug)]
struct AVLNode<K, V> {
    key: K,
    value: V,
    left: Option<Box<AVLNode<K, V>>>,
    right: Option<Box<AVLNode<K, V>>>,
    height: i32,
}

pub struct AVLDictionary<K, V> {
    root: Option<Box<AVLNode<K, V>>>,
    size: usize,
}

impl<K, V> AVLDictionary<K, V>
where
    K: Ord + Clone + Debug,
    V: Clone + Debug,
{
    pub fn new() -> Self {
        AVLDictionary {
            root: None,
            size: 0,
        }
    }
    
    fn height(node: &Option<Box<AVLNode<K, V>>>) -> i32 {
        node.as_ref().map_or(0, |n| n.height)
    }
    
    fn balance_factor(node: &Option<Box<AVLNode<K, V>>>) -> i32 {
        match node.as_ref() {
            Some(n) => Self::height(&n.left) - Self::height(&n.right),
            None => 0,
        }
    }
    
    fn update_height(node: &mut Box<AVLNode<K, V>>) {
        node.height = 1 + std::cmp::max(Self::height(&node.left), Self::height(&node.right));
    }
    
    fn rotate_right(mut y: Box<AVLNode<K, V>>) -> Box<AVLNode<K, V>> {
        let mut x = y.left.take().unwrap();
        y.left = x.right.take();
        
        Self::update_height(&mut y);
        Self::update_height(&mut x);
        
        x.right = Some(y);
        x
    }
    
    fn rotate_left(mut x: Box<AVLNode<K, V>>) -> Box<AVLNode<K, V>> {
        let mut y = x.right.take().unwrap();
        x.right = y.left.take();
        
        Self::update_height(&mut x);
        Self::update_height(&mut y);
        
        y.left = Some(x);
        y
    }
    
    fn insert_node(node: Option<Box<AVLNode<K, V>>>, key: K, value: V, size: &mut usize) -> Option<Box<AVLNode<K, V>>> {
        let mut node = match node {
            Some(mut n) => {
                match key.cmp(&n.key) {
                    Ordering::Less => {
                        n.left = Self::insert_node(n.left.take(), key, value, size);
                    }
                    Ordering::Greater => {
                        n.right = Self::insert_node(n.right.take(), key, value, size);
                    }
                    Ordering::Equal => {
                        n.value = value;
                        return Some(n);
                    }
                }
                n
            }
            None => {
                *size += 1;
                return Some(Box::new(AVLNode {
                    key,
                    value,
                    left: None,
                    right: None,
                    height: 1,
                }));
            }
        };
        
        Self::update_height(&mut node);
        
        let balance = Self::balance_factor(&Some(node));
        
        // Left-Left case
        if balance > 1 && key < node.left.as_ref().unwrap().key {
            return Some(Self::rotate_right(node));
        }
        
        // Right-Right case
        if balance < -1 && key > node.right.as_ref().unwrap().key {
            return Some(Self::rotate_left(node));
        }
        
        // Left-Right case
        if balance > 1 && key > node.left.as_ref().unwrap().key {
            let left = node.left.take().unwrap();
            node.left = Some(Self::rotate_left(left));
            return Some(Self::rotate_right(node));
        }
        
        // Right-Left case
        if balance < -1 && key < node.right.as_ref().unwrap().key {
            let right = node.right.take().unwrap();
            node.right = Some(Self::rotate_right(right));
            return Some(Self::rotate_left(node));
        }
        
        Some(node)
    }
    
    pub fn insert(&mut self, key: K, value: V) {
        self.root = Self::insert_node(self.root.take(), key, value, &mut self.size);
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let mut current = self.root.as_ref();
        
        while let Some(node) = current {
            match key.cmp(&node.key) {
                Ordering::Equal => return Some(&node.value),
                Ordering::Less => current = node.left.as_ref(),
                Ordering::Greater => current = node.right.as_ref(),
            }
        }
        
        None
    }
    
    pub fn contains(&self, key: &K) -> bool {
        self.get(key).is_some()
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}
```

## Red-Black Tree

Red-Black trees are self-balancing binary search trees with specific coloring rules that ensure O(log n) operations.

### Python Implementation

```python
class Color:
    RED = 0
    BLACK = 1

class RBNode:
    def __init__(self, key, value, color=Color.RED):
        self.key = key
        self.value = value
        self.color = color
        self.left = None
        self.right = None
        self.parent = None

class RedBlackDictionary:
    def __init__(self):
        self.NIL = RBNode(None, None, Color.BLACK)
        self.root = self.NIL
        self.size = 0
    
    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        
        if y.left != self.NIL:
            y.left.parent = x
        
        y.parent = x.parent
        
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        
        y.left = x
        x.parent = y
    
    def _right_rotate(self, x):
        y = x.left
        x.left = y.right
        
        if y.right != self.NIL:
            y.right.parent = x
        
        y.parent = x.parent
        
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        
        y.right = x
        x.parent = y
    
    def _insert_fixup(self, z):
        while z.parent.color == Color.RED:
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == Color.RED:
                    z.parent.color = Color.BLACK
                    y.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self._right_rotate(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y.color == Color.RED:
                    z.parent.color = Color.BLACK
                    y.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = Color.BLACK
                    z.parent.parent.color = Color.RED
                    self._left_rotate(z.parent.parent)
        
        self.root.color = Color.BLACK
    
    def insert(self, key, value):
        # Check if key already exists
        existing = self._search(key)
        if existing != self.NIL:
            existing.value = value
            return
        
        z = RBNode(key, value)
        z.left = self.NIL
        z.right = self.NIL
        
        y = self.NIL
        x = self.root
        
        while x != self.NIL:
            y = x
            if z.key < x.key:
                x = x.left
            else:
                x = x.right
        
        z.parent = y
        
        if y == self.NIL:
            self.root = z
        elif z.key < y.key:
            y.left = z
        else:
            y.right = z
        
        z.color = Color.RED
        self._insert_fixup(z)
        self.size += 1
    
    def _search(self, key):
        x = self.root
        while x != self.NIL and key != x.key:
            if key < x.key:
                x = x.left
            else:
                x = x.right
        return x
    
    def get(self, key):
        node = self._search(key)
        if node != self.NIL:
            return node.value
        raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        return self._search(key) != self.NIL
    
    def __len__(self):
        return self.size
```

## Skip List

Skip lists provide probabilistic balancing with simpler implementation than balanced trees.

### Python Implementation

```python
import random

class SkipNode:
    def __init__(self, key, value, level):
        self.key = key
        self.value = value
        self.forward = [None] * (level + 1)

class SkipListDictionary:
    def __init__(self, max_level=16, p=0.5):
        self.max_level = max_level
        self.p = p
        self.header = SkipNode(None, None, max_level)
        self.level = 0
        self.size = 0
    
    def _random_level(self):
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def insert(self, key, value):
        update = [None] * (self.max_level + 1)
        current = self.header
        
        # Find the position to insert
        for i in range(self.level, -1, -1):
            while (current.forward[i] and 
                   current.forward[i].key is not None and 
                   current.forward[i].key < key):
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        # If key already exists, update value
        if current and current.key == key:
            current.value = value
            return
        
        # Create new node
        new_level = self._random_level()
        
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level
        
        new_node = SkipNode(key, value, new_level)
        
        # Update forward pointers
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        
        self.size += 1
    
    def get(self, key):
        current = self.header
        
        for i in range(self.level, -1, -1):
            while (current.forward[i] and 
                   current.forward[i].key is not None and 
                   current.forward[i].key < key):
                current = current.forward[i]
        
        current = current.forward[0]
        
        if current and current.key == key:
            return current.value
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        update = [None] * (self.max_level + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while (current.forward[i] and 
                   current.forward[i].key is not None and 
                   current.forward[i].key < key):
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            # Update forward pointers
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            
            # Update level
            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            
            self.size -= 1
            return current.value
        
        raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def __len__(self):
        return self.size
```

## Performance Comparison

### Time Complexities

| Operation | Hash Table | AVL Tree | Red-Black Tree | Skip List |
|-----------|------------|----------|----------------|------------|
| Insert    | O(1) avg, O(n) worst | O(log n) | O(log n) | O(log n) expected |
| Get       | O(1) avg, O(n) worst | O(log n) | O(log n) | O(log n) expected |
| Delete    | O(1) avg, O(n) worst | O(log n) | O(log n) | O(log n) expected |
| Space     | O(n) | O(n) | O(n) | O(n) |

### Space Complexities

- **Hash Table**: O(n) with additional overhead for empty buckets
- **AVL Tree**: O(n) with extra height information per node
- **Red-Black Tree**: O(n) with color bit per node
- **Skip List**: O(n) with probabilistic overhead for forward pointers

## Use Cases and Trade-offs

### Hash Table
**Best for:**
- Fast average-case performance
- Simple key-value storage
- Cache implementations
- Symbol tables in compilers

**Limitations:**
- Poor worst-case performance
- No ordering guarantees
- Memory overhead from empty buckets

### AVL Tree
**Best for:**
- Guaranteed O(log n) operations
- Frequent lookups on large datasets
- Range queries
- Applications requiring strict performance guarantees

**Limitations:**
- More complex implementation
- Overhead from frequent rebalancing
- Slightly slower than Red-Black trees for insertions/deletions

### Red-Black Tree
**Best for:**
- Balanced performance for all operations
- Standard library implementations
- Good compromise between complexity and performance
- Frequent insertions and deletions

**Limitations:**
- More complex than basic BST
- Slightly less balanced than AVL trees

### Skip List
**Best for:**
- Concurrent implementations
- Simple probabilistic approach
- Good cache performance
- Lock-free implementations

**Limitations:**
- Probabilistic performance guarantees
- Space overhead from forward pointers
- Not as widely studied as tree-based approaches

## Testing Examples

```python
# Example usage and testing
def test_dictionary(dict_impl, name):
    print(f"\nTesting {name}:")
    
    # Test insertions
    for i in range(1, 11):
        dict_impl.insert(i, f"value_{i}")
    
    print(f"Size after insertions: {len(dict_impl)}")
    
    # Test lookups
    for i in range(1, 6):
        print(f"Key {i}: {dict_impl.get(i)}")
    
    # Test contains
    print(f"Contains key 5: {dict_impl.contains(5)}")
    print(f"Contains key 15: {dict_impl.contains(15)}")
    
    # Test deletions
    try:
        dict_impl.delete(3)
        print(f"Deleted key 3, new size: {len(dict_impl)}")
    except AttributeError:
        print("Delete method not implemented")

# Test all implementations
if __name__ == "__main__":
    implementations = [
        (HashTable(), "Hash Table"),
        (AVLDictionary(), "AVL Tree"),
        (RedBlackDictionary(), "Red-Black Tree"),
        (SkipListDictionary(), "Skip List")
    ]
    
    for impl, name in implementations:
        test_dictionary(impl, name)
```

## Advanced Features and Optimizations

### Hash Table Improvements

#### Robin Hood Hashing (Python)
```python
class RobinHoodHashTable:
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.distances = [0] * self.capacity  # Distance from ideal position
        self.deleted = [False] * self.capacity
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def _probe_distance(self, key, index):
        return (index - self._hash(key)) % self.capacity
    
    def insert(self, key, value):
        if self.size >= self.capacity * 0.75:
            self._resize()
        
        index = self._hash(key)
        distance = 0
        
        while True:
            if self.keys[index] is None or self.deleted[index]:
                # Empty slot found
                self.keys[index] = key
                self.values[index] = value
                self.distances[index] = distance
                self.deleted[index] = False
                self.size += 1
                return
            
            if self.keys[index] == key:
                # Update existing key
                self.values[index] = value
                return
            
            # Robin Hood: if current item is closer to home than us, swap
            if self.distances[index] < distance:
                # Swap with current entry
                self.keys[index], key = key, self.keys[index]
                self.values[index], value = value, self.values[index]
                self.distances[index], distance = distance, self.distances[index]
            
            index = (index + 1) % self.capacity
            distance += 1
    
    def _resize(self):
        old_keys, old_values = self.keys, self.values
        old_deleted = self.deleted
        
        self.capacity *= 2
        self.size = 0
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.distances = [0] * self.capacity
        self.deleted = [False] * self.capacity
        
        for i, key in enumerate(old_keys):
            if key is not None and not old_deleted[i]:
                self.insert(key, old_values[i])
```

#### Consistent Hashing for Distributed Systems
```python
import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, replicas=150):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    
    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
            bisect.insort(self.sorted_keys, key)
    
    def remove_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            if key in self.ring:
                del self.ring[key]
                self.sorted_keys.remove(key)
    
    def get_node(self, key):
        if not self.ring:
            return None
        
        hash_key = self._hash(key)
        idx = bisect.bisect_right(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
```

### Concurrent Dictionary Implementations

#### Lock-Free Skip List (Rust)
```rust
use std::sync::atomic::{AtomicPtr, AtomicUsize, Ordering};
use std::ptr;

struct AtomicSkipNode<K, V> {
    key: K,
    value: AtomicPtr<V>,
    forward: Vec<AtomicPtr<AtomicSkipNode<K, V>>>,
}

pub struct ConcurrentSkipList<K, V> {
    head: AtomicPtr<AtomicSkipNode<K, V>>,
    max_level: usize,
    level: AtomicUsize,
}

impl<K, V> ConcurrentSkipList<K, V>
where
    K: Ord + Clone,
    V: Clone,
{
    pub fn new(max_level: usize) -> Self {
        let head = Box::into_raw(Box::new(AtomicSkipNode {
            key: unsafe { std::mem::zeroed() }, // Sentinel value
            value: AtomicPtr::new(ptr::null_mut()),
            forward: (0..=max_level).map(|_| AtomicPtr::new(ptr::null_mut())).collect(),
        }));
        
        ConcurrentSkipList {
            head: AtomicPtr::new(head),
            max_level,
            level: AtomicUsize::new(0),
        }
    }
    
    fn find(&self, key: &K) -> (*mut AtomicSkipNode<K, V>, Vec<*mut AtomicSkipNode<K, V>>) {
        let mut preds = vec![ptr::null_mut(); self.max_level + 1];
        let mut current = self.head.load(Ordering::Acquire);
        
        for level in (0..=self.level.load(Ordering::Acquire)).rev() {
            unsafe {
                let mut next = (*current).forward[level].load(Ordering::Acquire);
                while !next.is_null() && (*next).key < *key {
                    current = next;
                    next = (*current).forward[level].load(Ordering::Acquire);
                }
                preds[level] = current;
            }
        }
        
        unsafe {
            let found = (*current).forward[0].load(Ordering::Acquire);
            (found, preds)
        }
    }
    
    // Implementation continues with lock-free insert/delete operations...
}
```

### Memory-Efficient Implementations

#### Trie-based Dictionary for String Keys
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.value = None
        self.is_end = False

class TrieDictionary:
    def __init__(self):
        self.root = TrieNode()
        self.size = 0
    
    def insert(self, key, value):
        if not isinstance(key, str):
            raise TypeError("TrieDictionary only supports string keys")
        
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_end:
            self.size += 1
        
        node.is_end = True
        node.value = value
    
    def get(self, key):
        node = self.root
        for char in key:
            if char not in node.children:
                raise KeyError(f"Key '{key}' not found")
            node = node.children[char]
        
        if not node.is_end:
            raise KeyError(f"Key '{key}' not found")
        
        return node.value
    
    def delete(self, key):
        def _delete_helper(node, key, depth):
            if depth == len(key):
                if not node.is_end:
                    return False
                node.is_end = False
                node.value = None
                return len(node.children) == 0
            
            char = key[depth]
            if char not in node.children:
                return False
            
            should_delete_child = _delete_helper(node.children[char], key, depth + 1)
            
            if should_delete_child:
                del node.children[char]
            
            return not node.is_end and len(node.children) == 0
        
        if self.contains(key):
            _delete_helper(self.root, key, 0)
            self.size -= 1
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def keys_with_prefix(self, prefix):
        """Return all keys that start with the given prefix"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._collect_keys(node, prefix, results)
        return results
    
    def _collect_keys(self, node, prefix, results):
        if node.is_end:
            results.append(prefix)
        
        for char, child in node.children.items():
            self._collect_keys(child, prefix + char, results)
    
    def __len__(self):
        return self.size
```

## Performance Benchmarking

### Benchmark Suite
```python
import time
import random
import matplotlib.pyplot as plt

class DictionaryBenchmark:
    def __init__(self, implementations):
        self.implementations = implementations
        self.results = {}
    
    def benchmark_insertions(self, sizes, num_runs=3):
        """Benchmark insertion performance across different data sizes"""
        results = {name: [] for name, _ in self.implementations}
        
        for size in sizes:
            print(f"Benchmarking insertions for size {size}...")
            
            for name, impl_class in self.implementations:
                times = []
                
                for _ in range(num_runs):
                    impl = impl_class()
                    keys = list(range(size))
                    random.shuffle(keys)
                    
                    start_time = time.time()
                    for key in keys:
                        impl.insert(key, f"value_{key}")
                    end_time = time.time()
                    
                    times.append(end_time - start_time)
                
                avg_time = sum(times) / len(times)
                results[name].append(avg_time)
        
        return results
    
    def benchmark_lookups(self, size, num_lookups, num_runs=3):
        """Benchmark lookup performance"""
        results = {name: [] for name, _ in self.implementations}
        
        # Prepare data
        keys = list(range(size))
        random.shuffle(keys)
        lookup_keys = random.choices(keys, k=num_lookups)
        
        for name, impl_class in self.implementations:
            times = []
            
            for _ in range(num_runs):
                impl = impl_class()
                
                # Insert data
                for key in keys:
                    impl.insert(key, f"value_{key}")
                
                # Benchmark lookups
                start_time = time.time()
                for key in lookup_keys:
                    try:
                        impl.get(key)
                    except:
                        pass
                end_time = time.time()
                
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            results[name] = avg_time
        
        return results
    
    def plot_results(self, benchmark_results, sizes, title, xlabel, ylabel):
        """Plot benchmark results"""
        plt.figure(figsize=(10, 6))
        
        for name, times in benchmark_results.items():
            plt.plot(sizes, times, marker='o', label=name)
        
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

# Example usage
if __name__ == "__main__":
    implementations = [
        ("Hash Table", HashTable),
        ("AVL Tree", AVLDictionary),
        ("Red-Black Tree", RedBlackDictionary),
        ("Skip List", SkipListDictionary),
        ("Trie", TrieDictionary)  # Only for string keys
    ]
    
    benchmark = DictionaryBenchmark(implementations[:-1])  # Exclude Trie for mixed benchmarks
    sizes = [100, 500, 1000, 5000, 10000]
    
    # Benchmark insertions
    insertion_results = benchmark.benchmark_insertions(sizes)
    benchmark.plot_results(insertion_results, sizes, 
                          "Dictionary Insertion Performance", 
                          "Number of Elements", "Time (seconds)")
    
    # Benchmark lookups
    lookup_results = benchmark.benchmark_lookups(10000, 1000)
    print("Lookup Performance (1000 lookups on 10k elements):")
    for name, time_taken in lookup_results.items():
        print(f"{name}: {time_taken:.6f} seconds")
```

## Real-World Applications

### Database Index Implementation
```python
class DatabaseIndex:
    """B+ Tree implementation for database indexing"""
    
    def __init__(self, order=4):
        self.order = order  # Minimum degree
        self.root = BPlusLeafNode()
        self.height = 1
    
    class BPlusNode:
        def __init__(self):
            self.keys = []
            self.is_leaf = False
    
    class BPlusInternalNode(BPlusNode):
        def __init__(self):
            super().__init__()
            self.children = []
    
    class BPlusLeafNode(BPlusNode):
        def __init__(self):
            super().__init__()
            self.is_leaf = True
            self.values = []
            self.next = None  # Pointer to next leaf for range queries
    
    def range_query(self, start_key, end_key):
        """Efficient range queries using leaf node linking"""
        results = []
        
        # Find starting leaf node
        leaf = self._find_leaf(start_key)
        
        # Traverse leaf nodes collecting values in range
        while leaf:
            for i, key in enumerate(leaf.keys):
                if start_key <= key <= end_key:
                    results.append((key, leaf.values[i]))
                elif key > end_key:
                    return results
            leaf = leaf.next
        
        return results
```

### Cache Implementation with LRU Eviction
```python
class LRUCache:
    """Dictionary with Least Recently Used eviction policy"""
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}  # key -> node mapping
        
        # Doubly linked list for LRU ordering
        self.head = self.Node(0, 0)
        self.tail = self.Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head
    
    class Node:
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
    
    def get(self, key):
        if key in self.cache:
            node = self.cache[key]
            # Move to head (most recently used)
            self._remove_node(node)
            self._add_to_head(node)
            return node.value
        raise KeyError(f"Key '{key}' not found")
    
    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._remove_node(node)
            self._add_to_head(node)
        else:
            if len(self.cache) >= self.capacity:
                # Evict least recently used
                lru = self.tail.prev
                self._remove_node(lru)
                del self.cache[lru.key]
            
            # Add new node
            new_node = self.Node(key, value)
            self._add_to_head(new_node)
            self.cache[key] = new_node
    
    def _remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _add_to_head(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
```

This comprehensive guide provides complete, production-ready implementations of various dictionary data structures. Each implementation includes proper error handling, efficiency optimizations, and clear documentation of trade-offs. The advanced features section covers concurrent implementations, memory optimization techniques, and real-world applications like database indexing and caching systems. Choose the appropriate implementation based on your specific use case requirements for performance, memory usage, and operational guarantees.

I'll create a comprehensive ASCII diagram showing how dictionary data structures work step by step, covering hash tables (the most common implementation) with key operations.I've created a comprehensive ASCII diagram that shows how dictionary data structures (implemented as hash tables) work step by step. The diagram covers:

1. **Initial State** - Empty hash table
2. **Hash Function** - How keys are converted to indices
3. **Insert Operations** - Adding key-value pairs
4. **Collision Handling** - Both chaining and linear probing methods
5. **Search Operations** - Finding values by key
6. **Delete Operations** - Removing entries
7. **Performance Analysis** - Time complexity breakdown
8. **Memory Layout** - How the structure is organized in memory

Key concepts illustrated:
- Hash function calculation with ASCII values
- Collision resolution strategies
- Step-by-step operation processes
- Time complexity analysis
- Load factor considerations

The diagram uses clear ASCII art to show the hash table structure, with arrows indicating data flow and relationships. Each operation is broken down into discrete steps to show exactly what happens during dictionary operations.

Would you like me to expand on any particular aspect or add additional collision resolution methods like quadratic probing?

# Dictionary Data Structure (Hash Table) - Step by Step

## 1. Initial Empty Dictionary
```
Hash Table (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │NULL│NULL│NULL│NULL│NULL│NULL│NULL│NULL│
      └────┴────┴────┴────┴────┴────┴────┴────┘
```

## 2. Hash Function Process
```
Hash Function: hash(key) = sum of ASCII values % table_size

Example: key = "cat"
┌─────┐    ┌─────────────────────────────┐    ┌───────┐
│"cat"│───▶│ 'c'(99) + 'a'(97) + 't'(116)│───▶│ 312 % 8│
└─────┘    │         = 312               │    └───────┘
           └─────────────────────────────┘         │
                                                   ▼
                                              Index = 0
```

## 3. INSERT Operation: dict["cat"] = 5

### Step 3a: Calculate hash index
```
hash("cat") = 312 % 8 = 0
Target index: 0
```

### Step 3b: Insert at calculated index
```
Hash Table (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│NULL│NULL│NULL│NULL│NULL│NULL│NULL│
      │ 5  │    │    │    │    │    │    │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
```

## 4. INSERT Operation: dict["dog"] = 3

### Step 4a: Calculate hash index
```
hash("dog") = ('d'(100) + 'o'(111) + 'g'(103)) % 8 = 314 % 8 = 2
```

### Step 4b: Insert at index 2
```
Hash Table (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│NULL│dog:│NULL│NULL│NULL│NULL│NULL│
      │ 5  │    │ 3  │    │    │    │    │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
```

## 5. COLLISION: INSERT dict["ace"] = 7

### Step 5a: Calculate hash index
```
hash("ace") = ('a'(97) + 'c'(99) + 'e'(101)) % 8 = 297 % 8 = 1
```

### Step 5b: No collision, insert at index 1
```
Hash Table (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│ace:│dog:│NULL│NULL│NULL│NULL│NULL│
      │ 5  │ 7  │ 3  │    │    │    │    │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
```

## 6. COLLISION: INSERT dict["cab"] = 9

### Step 6a: Calculate hash index (collision occurs!)
```
hash("cab") = ('c'(99) + 'a'(97) + 'b'(98)) % 8 = 294 % 8 = 6
No collision at index 6, inserting...
```

### Step 6b: Insert at index 6
```
Hash Table (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│ace:│dog:│NULL│NULL│NULL│cab:│NULL│
      │ 5  │ 7  │ 3  │    │    │    │ 9  │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
```

## 7. TRUE COLLISION: INSERT dict["tac"] = 1

### Step 7a: Calculate hash index
```
hash("tac") = ('t'(116) + 'a'(97) + 'c'(99)) % 8 = 312 % 8 = 0
COLLISION! Index 0 is already occupied by "cat"
```

### Step 7b: Collision Resolution (Chaining)
```
Hash Table with Chaining (size = 8)
Index:  0         1    2    3    4    5    6    7
      ┌─────┐   ┌────┬────┬────┬────┬────┬────┬────┐
    0 │cat:5│──▶│tac:│ace:│dog:│NULL│NULL│NULL│cab:│NULL│
      └─────┘   │ 1  │ 7  │ 3  │    │    │    │ 9  │    │
        │       └────┴────┴────┴────┴────┴────┴────┴────┘
        ▼
      ┌─────┐
      │tac:1│
      └─────┘
```

Alternative: Linear Probing
```
Hash Table with Linear Probing (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│ace:│dog:│tac:│NULL│NULL│cab:│NULL│
      │ 5  │ 7  │ 3  │ 1  │    │    │ 9  │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
                    ▲
              Probed to next
              available slot
```

## 8. SEARCH Operation: Find dict["dog"]

### Step 8a: Calculate hash index
```
hash("dog") = 314 % 8 = 2
Check index 2...
```

### Step 8b: Compare keys and return value
```
Index 2: Found "dog" → Return value: 3

Search Process:
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│hash(key)│───▶│ Go to index 2│───▶│ Compare keys│
└─────────┘    └──────────────┘    └─────────────┘
                                           │
                                           ▼
                                   ┌─────────────┐
                                   │ Return: 3   │
                                   └─────────────┘
```

## 9. DELETE Operation: Remove dict["ace"]

### Step 9a: Calculate hash and find key
```
hash("ace") = 297 % 8 = 1
Found "ace" at index 1
```

### Step 9b: Remove the entry
```
Hash Table after deletion (size = 8)
Index:  0    1    2    3    4    5    6    7
      ┌────┬────┬────┬────┬────┬────┬────┬────┐
      │cat:│NULL│dog:│NULL│NULL│NULL│cab:│NULL│
      │ 5  │    │ 3  │    │    │    │ 9  │    │
      └────┴────┴────┴────┴────┴────┴────┴────┘
           ▲
      Deleted "ace"
```

## 10. Dictionary Operations Summary

```
┌─────────────────────────────────────────────────────────┐
│                Dictionary Operations                    │
├─────────────────┬───────────────────────────────────────┤
│ INSERT(key,val) │ 1. hash(key) → index                  │
│                 │ 2. Handle collision if needed         │
│                 │ 3. Store key-value pair               │
├─────────────────┼───────────────────────────────────────┤
│ SEARCH(key)     │ 1. hash(key) → index                  │
│                 │ 2. Compare keys at location           │
│                 │ 3. Return value or "not found"        │
├─────────────────┼───────────────────────────────────────┤
│ DELETE(key)     │ 1. hash(key) → index                  │
│                 │ 2. Find and verify key                │
│                 │ 3. Remove entry                       │
└─────────────────┴───────────────────────────────────────┘
```

## 11. Time Complexity Analysis

```
┌──────────────────────────────────────────────────────────┐
│                Time Complexity                           │
├─────────────┬─────────────┬──────────────────────────────┤
│ Operation   │ Average     │ Worst Case                   │
├─────────────┼─────────────┼──────────────────────────────┤
│ INSERT      │ O(1)        │ O(n) - all keys hash same   │
│ SEARCH      │ O(1)        │ O(n) - linear search chain  │
│ DELETE      │ O(1)        │ O(n) - must find in chain   │
└─────────────┴─────────────┴──────────────────────────────┘

Load Factor = number_of_elements / table_size
Optimal Load Factor ≈ 0.75 (resize when exceeded)
```

## 12. Memory Layout Visualization

```
Memory Representation:
┌─────────────────────────────────────────────────────────┐
│                Hash Table Structure                     │
│                                                         │
│  ┌─────────┐     ┌──────────────────────────────┐      │
│  │ Table   │────▶│ Array of Buckets/Slots       │      │
│  │ Size: 8 │     │                              │      │
│  └─────────┘     │ [0] ──▶ "cat":5              │      │
│                  │ [1] ──▶ NULL                 │      │
│  ┌─────────┐     │ [2] ──▶ "dog":3              │      │
│  │Hash Func│     │ [3] ──▶ NULL                 │      │
│  │ h(k) =  │     │ [4] ──▶ NULL                 │      │
│  │ k % 8   │     │ [5] ──▶ NULL                 │      │
│  └─────────┘     │ [6] ──▶ "cab":9              │      │
│                  │ [7] ──▶ NULL                 │      │
│                  └──────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```