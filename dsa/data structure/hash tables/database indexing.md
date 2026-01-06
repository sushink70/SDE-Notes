# Database Indexing Guide with Implementations in Python and Rust

I'll create a comprehensive guide to database indexing with complete implementations in both Python and Rust. This will cover the theory, different index types, and practical implementations.

## Comprehensive Database Indexing Guide

## Table of Contents

1. [Introduction to Database Indexing](#introduction)
2. [Types of Database Indexes](#types)
3. [B-Tree Index Implementation](#btree)
4. [Hash Index Implementation](#hash)
5. [Bitmap Index Implementation](#bitmap)
6. [LSM Tree Index Implementation](#lsm)
7. [Performance Analysis](#performance)
8. [Best Practices](#best-practices)

## Introduction to Database Indexing {#introduction}

Database indexing is a data structure technique used to quickly locate and access data in a database. Indexes create shortcuts to data, dramatically improving query performance at the cost of additional storage space and write overhead.

### Key Concepts:

- **Index Key**: The column(s) on which the index is built
- **Clustered Index**: Data rows are stored in order based on the index key
- **Non-clustered Index**: Index structure is separate from data storage
- **Composite Index**: Index on multiple columns
- **Unique Index**: Ensures uniqueness of indexed values
- **Partial Index**: Index on a subset of table rows

### Performance Trade-offs:

- **Read Performance**: Indexes dramatically improve SELECT query speed
- **Write Performance**: INSERT/UPDATE/DELETE operations become slower
- **Storage Overhead**: Indexes require additional disk space
- **Memory Usage**: Indexes consume RAM for caching

## Types of Database Indexes {#types}

### 1. B-Tree Indexes

- Most common type
- Balanced tree structure
- Excellent for range queries
- Logarithmic time complexity O(log n)

### 2. Hash Indexes

- Fast equality lookups O(1)
- Poor for range queries
- Memory-efficient for exact matches

### 3. Bitmap Indexes

- Uses bit arrays to represent indexed values
- Efficient for low-cardinality data
- Excellent for analytical queries
- Space-efficient with compression

### 4. LSM Tree Indexes

- Log-Structured Merge Trees
- Optimized for write-heavy workloads
- Used in modern NoSQL databases
- Good compression ratios

## B-Tree Index Implementation {#btree}

### Python Implementation

```python
import bisect
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class BTreeNode:
    keys: List[Any]
    values: List[Any]
    children: List['BTreeNode']
    is_leaf: bool
    
    def __init__(self, is_leaf: bool = True):
        self.keys = []
        self.values = []
        self.children = []
        self.is_leaf = is_leaf

class BTreeIndex:
    def __init__(self, degree: int = 3):
        """
        Initialize B-Tree with given minimum degree.
        A node can have at most 2*degree-1 keys.
        """
        self.degree = degree
        self.root = BTreeNode(is_leaf=True)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the B-Tree."""
        return self._search_node(self.root, key)
    
    def _search_node(self, node: BTreeNode, key: Any) -> Optional[Any]:
        # Find the first key greater than or equal to the search key
        i = bisect.bisect_left(node.keys, key)
        
        # If key found
        if i < len(node.keys) and node.keys[i] == key:
            return node.values[i]
        
        # If leaf node, key not found
        if node.is_leaf:
            return None
        
        # Recursively search appropriate child
        return self._search_node(node.children[i], key)
    
    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the B-Tree."""
        root = self.root
        
        # If root is full, create new root
        if len(root.keys) == 2 * self.degree - 1:
            new_root = BTreeNode(is_leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key, value)
    
    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any) -> None:
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert into leaf node
            node.keys.append(None)
            node.values.append(None)
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            # Find child to insert into
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            # Split child if full
            if len(node.children[i].keys) == 2 * self.degree - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)
    
    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """Split a full child node."""
        full_child = parent.children[index]
        new_child = BTreeNode(is_leaf=full_child.is_leaf)
        
        mid_index = self.degree - 1
        
        # Move half the keys to new child
        new_child.keys = full_child.keys[mid_index + 1:]
        new_child.values = full_child.values[mid_index + 1:]
        full_child.keys = full_child.keys[:mid_index]
        full_child.values = full_child.values[:mid_index]
        
        # Move children if not leaf
        if not full_child.is_leaf:
            new_child.children = full_child.children[mid_index + 1:]
            full_child.children = full_child.children[:mid_index + 1]
        
        # Insert new child into parent
        parent.children.insert(index + 1, new_child)
        parent.keys.insert(index, full_child.keys[mid_index])
        parent.values.insert(index, full_child.values[mid_index])
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Perform range query between start_key and end_key (inclusive)."""
        results = []
        self._range_query_node(self.root, start_key, end_key, results)
        return results
    
    def _range_query_node(self, node: BTreeNode, start_key: Any, end_key: Any, results: List) -> None:
        i = 0
        while i < len(node.keys):
            if not node.is_leaf:
                if node.keys[i] >= start_key:
                    self._range_query_node(node.children[i], start_key, end_key, results)
            
            if start_key <= node.keys[i] <= end_key:
                results.append((node.keys[i], node.values[i]))
            
            if node.keys[i] > end_key:
                break
            
            i += 1
        
        # Check last child
        if not node.is_leaf and i < len(node.children):
            if len(node.keys) == 0 or node.keys[-1] < end_key:
                self._range_query_node(node.children[i], start_key, end_key, results)

# Example usage
def demo_btree():
    btree = BTreeIndex(degree=3)
    
    # Insert data
    data = [(10, "ten"), (20, "twenty"), (30, "thirty"), (40, "forty"), (50, "fifty")]
    for key, value in data:
        btree.insert(key, value)
    
    # Search
    print(f"Search 30: {btree.search(30)}")
    
    # Range query
    print(f"Range 20-40: {btree.range_query(20, 40)}")
```

### Rust Implementation

```rust
use std::cmp::Ordering;

#[derive(Debug, Clone)]
pub struct BTreeNode<K, V> 
where 
    K: Ord + Clone,
    V: Clone,
{
    keys: Vec<K>,
    values: Vec<V>,
    children: Vec<Box<BTreeNode<K, V>>>,
    is_leaf: bool,
}

impl<K, V> BTreeNode<K, V>
where
    K: Ord + Clone,
    V: Clone,
{
    fn new(is_leaf: bool) -> Self {
        BTreeNode {
            keys: Vec::new(),
            values: Vec::new(),
            children: Vec::new(),
            is_leaf,
        }
    }
}

#[derive(Debug)]
pub struct BTreeIndex<K, V>
where
    K: Ord + Clone,
    V: Clone,
{
    root: Box<BTreeNode<K, V>>,
    degree: usize,
}

impl<K, V> BTreeIndex<K, V>
where
    K: Ord + Clone,
    V: Clone,
{
    pub fn new(degree: usize) -> Self {
        BTreeIndex {
            root: Box::new(BTreeNode::new(true)),
            degree,
        }
    }

    pub fn search(&self, key: &K) -> Option<&V> {
        self.search_node(&self.root, key)
    }

    fn search_node(&self, node: &BTreeNode<K, V>, key: &K) -> Option<&V> {
        let mut i = 0;
        while i < node.keys.len() && key > &node.keys[i] {
            i += 1;
        }

        if i < node.keys.len() && key == &node.keys[i] {
            return Some(&node.values[i]);
        }

        if node.is_leaf {
            return None;
        }

        self.search_node(&node.children[i], key)
    }

    pub fn insert(&mut self, key: K, value: V) {
        if self.root.keys.len() == 2 * self.degree - 1 {
            let mut new_root = BTreeNode::new(false);
            let old_root = std::mem::replace(&mut self.root, Box::new(new_root));
            self.root.children.push(old_root);
            self.split_child(&mut self.root, 0);
        }

        self.insert_non_full(&mut self.root, key, value);
    }

    fn insert_non_full(&mut self, node: &mut BTreeNode<K, V>, key: K, value: V) {
        let mut i = node.keys.len() as i32 - 1;

        if node.is_leaf {
            node.keys.push(key.clone());
            node.values.push(value);
            
            while i >= 0 && key < node.keys[i as usize] {
                node.keys.swap((i + 1) as usize, i as usize);
                node.values.swap((i + 1) as usize, i as usize);
                i -= 1;
            }
        } else {
            while i >= 0 && key < node.keys[i as usize] {
                i -= 1;
            }
            i += 1;

            if node.children[i as usize].keys.len() == 2 * self.degree - 1 {
                self.split_child(node, i as usize);
                if key > node.keys[i as usize] {
                    i += 1;
                }
            }

            self.insert_non_full(&mut node.children[i as usize], key, value);
        }
    }

    fn split_child(&mut self, parent: &mut BTreeNode<K, V>, index: usize) {
        let mut new_child = BTreeNode::new(parent.children[index].is_leaf);
        let full_child = &mut parent.children[index];

        let mid_index = self.degree - 1;

        // Split keys and values
        new_child.keys = full_child.keys.split_off(mid_index + 1);
        new_child.values = full_child.values.split_off(mid_index + 1);

        // Split children if not leaf
        if !full_child.is_leaf {
            new_child.children = full_child.children.split_off(mid_index + 1);
        }

        // Move middle key up to parent
        let middle_key = full_child.keys.pop().unwrap();
        let middle_value = full_child.values.pop().unwrap();

        parent.children.insert(index + 1, Box::new(new_child));
        parent.keys.insert(index, middle_key);
        parent.values.insert(index, middle_value);
    }

    pub fn range_query(&self, start_key: &K, end_key: &K) -> Vec<(&K, &V)> {
        let mut results = Vec::new();
        self.range_query_node(&self.root, start_key, end_key, &mut results);
        results
    }

    fn range_query_node(&self, node: &BTreeNode<K, V>, start_key: &K, end_key: &K, results: &mut Vec<(&K, &V)>) {
        let mut i = 0;
        
        while i < node.keys.len() {
            if !node.is_leaf && &node.keys[i] >= start_key {
                self.range_query_node(&node.children[i], start_key, end_key, results);
            }

            if start_key <= &node.keys[i] && &node.keys[i] <= end_key {
                results.push((&node.keys[i], &node.values[i]));
            }

            if &node.keys[i] > end_key {
                break;
            }

            i += 1;
        }

        if !node.is_leaf && i < node.children.len() {
            if node.keys.is_empty() || &node.keys[node.keys.len() - 1] < end_key {
                self.range_query_node(&node.children[i], start_key, end_key, results);
            }
        }
    }
}

// Example usage
fn demo_btree() {
    let mut btree = BTreeIndex::new(3);
    
    // Insert data
    btree.insert(10, "ten");
    btree.insert(20, "twenty");
    btree.insert(30, "thirty");
    btree.insert(40, "forty");
    btree.insert(50, "fifty");
    
    // Search
    println!("Search 30: {:?}", btree.search(&30));
    
    // Range query
    println!("Range 20-40: {:?}", btree.range_query(&20, &40));
}
```

## Hash Index Implementation {#hash}

### Python Implementation

```python
import hashlib
from typing import Any, List, Optional, Tuple

class HashBucket:
    def __init__(self):
        self.items: List[Tuple[Any, Any]] = []
    
    def get(self, key: Any) -> Optional[Any]:
        for k, v in self.items:
            if k == key:
                return v
        return None
    
    def put(self, key: Any, value: Any) -> None:
        for i, (k, v) in enumerate(self.items):
            if k == key:
                self.items[i] = (key, value)
                return
        self.items.append((key, value))
    
    def remove(self, key: Any) -> bool:
        for i, (k, v) in enumerate(self.items):
            if k == key:
                del self.items[i]
                return True
        return False

class HashIndex:
    def __init__(self, initial_size: int = 16, load_factor: float = 0.75):
        self.size = initial_size
        self.load_factor = load_factor
        self.count = 0
        self.buckets: List[HashBucket] = [HashBucket() for _ in range(self.size)]
    
    def _hash(self, key: Any) -> int:
        """Simple hash function using Python's built-in hash."""
        return hash(key) % self.size
    
    def _should_resize(self) -> bool:
        return self.count / self.size > self.load_factor
    
    def _resize(self) -> None:
        """Double the hash table size and rehash all elements."""
        old_buckets = self.buckets
        self.size *= 2
        self.count = 0
        self.buckets = [HashBucket() for _ in range(self.size)]
        
        # Rehash all existing elements
        for bucket in old_buckets:
            for key, value in bucket.items:
                self.insert(key, value)
    
    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the hash index."""
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        old_value = bucket.get(key)
        bucket.put(key, value)
        
        if old_value is None:  # New key
            self.count += 1
            if self._should_resize():
                self._resize()
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the hash index."""
        bucket_index = self._hash(key)
        return self.buckets[bucket_index].get(key)
    
    def delete(self, key: Any) -> bool:
        """Delete a key from the hash index."""
        bucket_index = self._hash(key)
        if self.buckets[bucket_index].remove(key):
            self.count -= 1
            return True
        return False
    
    def get_stats(self) -> dict:
        """Get hash table statistics."""
        non_empty_buckets = sum(1 for bucket in self.buckets if bucket.items)
        max_bucket_size = max(len(bucket.items) for bucket in self.buckets)
        
        return {
            'size': self.size,
            'count': self.count,
            'load_factor': self.count / self.size,
            'non_empty_buckets': non_empty_buckets,
            'max_bucket_size': max_bucket_size,
        }

# Example usage
def demo_hash_index():
    hash_idx = HashIndex()
    
    # Insert data
    data = [("apple", 1), ("banana", 2), ("cherry", 3), ("date", 4)]
    for key, value in data:
        hash_idx.insert(key, value)
    
    # Search
    print(f"Search 'banana': {hash_idx.search('banana')}")
    
    # Statistics
    print(f"Hash index stats: {hash_idx.get_stats()}")
```

### Rust Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
struct HashBucket<K, V> {
    items: Vec<(K, V)>,
}

impl<K, V> HashBucket<K, V>
where
    K: PartialEq + Clone,
    V: Clone,
{
    fn new() -> Self {
        HashBucket { items: Vec::new() }
    }

    fn get(&self, key: &K) -> Option<&V> {
        self.items.iter()
            .find(|(k, _)| k == key)
            .map(|(_, v)| v)
    }

    fn put(&mut self, key: K, value: V) -> Option<V> {
        if let Some(pos) = self.items.iter().position(|(k, _)| k == &key) {
            let old_value = self.items[pos].1.clone();
            self.items[pos] = (key, value);
            Some(old_value)
        } else {
            self.items.push((key, value));
            None
        }
    }

    fn remove(&mut self, key: &K) -> Option<V> {
        if let Some(pos) = self.items.iter().position(|(k, _)| k == key) {
            Some(self.items.remove(pos).1)
        } else {
            None
        }
    }

    fn len(&self) -> usize {
        self.items.len()
    }
}

#[derive(Debug)]
pub struct HashIndex<K, V> {
    buckets: Vec<HashBucket<K, V>>,
    size: usize,
    count: usize,
    load_factor: f64,
}

impl<K, V> HashIndex<K, V>
where
    K: Hash + PartialEq + Clone,
    V: Clone,
{
    pub fn new(initial_size: usize, load_factor: f64) -> Self {
        let mut buckets = Vec::with_capacity(initial_size);
        for _ in 0..initial_size {
            buckets.push(HashBucket::new());
        }

        HashIndex {
            buckets,
            size: initial_size,
            count: 0,
            load_factor,
        }
    }

    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.size
    }

    fn should_resize(&self) -> bool {
        (self.count as f64) / (self.size as f64) > self.load_factor
    }

    fn resize(&mut self) {
        let old_buckets = std::mem::replace(&mut self.buckets, Vec::new());
        self.size *= 2;
        self.count = 0;
        
        self.buckets = Vec::with_capacity(self.size);
        for _ in 0..self.size {
            self.buckets.push(HashBucket::new());
        }

        // Rehash all existing elements
        for bucket in old_buckets {
            for (key, value) in bucket.items {
                self.insert(key, value);
            }
        }
    }

    pub fn insert(&mut self, key: K, value: V) {
        let bucket_index = self.hash(&key);
        let old_value = self.buckets[bucket_index].put(key, value);

        if old_value.is_none() {
            self.count += 1;
            if self.should_resize() {
                self.resize();
            }
        }
    }

    pub fn search(&self, key: &K) -> Option<&V> {
        let bucket_index = self.hash(key);
        self.buckets[bucket_index].get(key)
    }

    pub fn delete(&mut self, key: &K) -> Option<V> {
        let bucket_index = self.hash(key);
        if let Some(value) = self.buckets[bucket_index].remove(key) {
            self.count -= 1;
            Some(value)
        } else {
            None
        }
    }

    pub fn get_stats(&self) -> HashIndexStats {
        let non_empty_buckets = self.buckets.iter().filter(|b| b.len() > 0).count();
        let max_bucket_size = self.buckets.iter().map(|b| b.len()).max().unwrap_or(0);

        HashIndexStats {
            size: self.size,
            count: self.count,
            load_factor: (self.count as f64) / (self.size as f64),
            non_empty_buckets,
            max_bucket_size,
        }
    }
}

#[derive(Debug)]
pub struct HashIndexStats {
    pub size: usize,
    pub count: usize,
    pub load_factor: f64,
    pub non_empty_buckets: usize,
    pub max_bucket_size: usize,
}

// Example usage
fn demo_hash_index() {
    let mut hash_idx = HashIndex::new(16, 0.75);
    
    // Insert data
    hash_idx.insert("apple", 1);
    hash_idx.insert("banana", 2);
    hash_idx.insert("cherry", 3);
    hash_idx.insert("date", 4);
    
    // Search
    println!("Search 'banana': {:?}", hash_idx.search(&"banana"));
    
    // Statistics
    println!("Hash index stats: {:?}", hash_idx.get_stats());
}
```

## Bitmap Index Implementation {#bitmap}

### Python Implementation

```python
import struct
from typing import Any, Dict, List, Set
from bitarray import bitarray

class BitmapIndex:
    def __init__(self):
        self.bitmaps: Dict[Any, bitarray] = {}
        self.row_count = 0
    
    def add_value(self, row_id: int, value: Any) -> None:
        """Add a value for a specific row."""
        # Ensure we have enough capacity
        if row_id >= self.row_count:
            self._expand_capacity(row_id + 1)
        
        # Create bitmap for value if it doesn't exist
        if value not in self.bitmaps:
            self.bitmaps[value] = bitarray(self.row_count)
            self.bitmaps[value].setall(False)
        
        # Set bit for this row and value
        self.bitmaps[value][row_id] = True
    
    def _expand_capacity(self, new_size: int) -> None:
        """Expand all bitmaps to accommodate more rows."""
        old_size = self.row_count
        self.row_count = new_size
        
        for bitmap in self.bitmaps.values():
            bitmap.extend([False] * (new_size - old_size))
    
    def query_equal(self, value: Any) -> bitarray:
        """Query for rows where column equals value."""
        if value in self.bitmaps:
            return self.bitmaps[value].copy()
        else:
            # Return empty bitmap
            result = bitarray(self.row_count)
            result.setall(False)
            return result
    
    def query_in(self, values: Set[Any]) -> bitarray:
        """Query for rows where column is in set of values."""
        result = bitarray(self.row_count)
        result.setall(False)
        
        for value in values:
            if value in self.bitmaps:
                result |= self.bitmaps[value]
        
        return result
    
    def query_not_equal(self, value: Any) -> bitarray:
        """Query for rows where column does not equal value."""
        result = bitarray(self.row_count)
        result.setall(True)
        
        if value in self.bitmaps:
            result &= ~self.bitmaps[value]
        
        return result
    
    def get_cardinality(self) -> Dict[Any, int]:
        """Get count of rows for each value."""
        return {value: bitmap.count() for value, bitmap in self.bitmaps.items()}
    
    def get_storage_info(self) -> Dict[str, int]:
        """Get storage information about the bitmap index."""
        total_bits = sum(len(bitmap) for bitmap in self.bitmaps.values())
        return {
            'unique_values': len(self.bitmaps),
            'total_bits': total_bits,
            'total_bytes': total_bits // 8,
            'row_count': self.row_count,
        }

class CompressedBitmapIndex:
    """Run-Length Encoded Bitmap Index for better compression."""
    
    def __init__(self):
        self.compressed_bitmaps: Dict[Any, List[int]] = {}
        self.row_count = 0
    
    def _compress_bitmap(self, bitmap: bitarray) -> List[int]:
        """Convert bitmap to run-length encoding."""
        if len(bitmap) == 0:
            return []
        
        runs = []
        current_bit = bitmap[0]
        current_run = 1
        
        for i in range(1, len(bitmap)):
            if bitmap[i] == current_bit:
                current_run += 1
            else:
                runs.append(current_run if current_bit else -current_run)
                current_bit = bitmap[i]
                current_run = 1
        
        runs.append(current_run if current_bit else -current_run)
        return runs
    
    def _decompress_bitmap(self, runs: List[int], length: int) -> bitarray:
        """Convert run-length encoding back to bitmap."""
        bitmap = bitarray(length)
        bitmap.setall(False)
        
        position = 0
        for run in runs:
            if run > 0:  # Run of 1s
                for i in range(position, position + run):
                    if i < length:
                        bitmap[i] = True
            position += abs(run)
        
        return bitmap
    
    def add_batch(self, column_data: List[Any]) -> None:
        """Add a batch of column data."""
        self.row_count = len(column_data)
        
        # Create temporary bitmaps
        temp_bitmaps = {}
        for row_id, value in enumerate(column_data):
            if value not in temp_bitmaps:
                temp_bitmaps[value] = bitarray(self.row_count)
                temp_bitmaps[value].setall(False)
            temp_bitmaps[value][row_id] = True
        
        # Compress bitmaps
        for value, bitmap in temp_bitmaps.items():
            self.compressed_bitmaps[value] = self._compress_bitmap(bitmap)
    
    def query_equal(self, value: Any) -> bitarray:
        """Query for rows where column equals value."""
        if value in self.compressed_bitmaps:
            return self._decompress_bitmap(self.compressed_bitmaps[value], self.row_count)
        else:
            result = bitarray(self.row_count)
            result.setall(False)
            return result

# Example usage
def demo_bitmap_index():
    # Regular bitmap index
    bitmap_idx = BitmapIndex()
    
    # Sample data: colors of cars
    cars = ['red', 'blue', 'red', 'green', 'blue', 'red', 'yellow']
    for row_id, color in enumerate(cars):
        bitmap_idx.add_value(row_id, color)
    
    # Query examples
    red_cars = bitmap_idx.query_equal('red')
    print(f"Red cars (rows): {[i for i, bit in enumerate(red_cars) if bit]}")
    
    blue_or_green = bitmap_idx.query_in({'blue', 'green'})
    print(f"Blue or green cars: {[i for i, bit in enumerate(blue_or_green) if bit]}")
    
    # Compressed bitmap index
    compressed_idx = CompressedBitmapIndex()
    compressed_idx.add_batch(cars)
    
    red_cars_compressed = compressed_idx.query_equal('red')
    print(f"Red cars (compressed): {[i for i, bit in enumerate(red_cars_compressed) if bit]}")
    
    print(f"Storage info: {bitmap_idx.get_storage_info()}")
```

### Rust Implementation

```rust
use std::collections::HashMap;
use bit_vec::BitVec;

#[derive(Debug, Clone)]
pub struct BitmapIndex<T> 
where 
    T: std::hash::Hash + Eq + Clone,
{
    bitmaps: HashMap<T, BitVec>,
    row_count: usize,
}

impl<T> BitmapIndex<T>
where
    T: std::hash::Hash + Eq + Clone,
{
    pub fn new() -> Self {
        BitmapIndex {
            bitmaps: HashMap::new(),
            row_count: 0,
        }
    }

    pub fn add_value(&mut self, row_id: usize, value: T) {
        // Expand capacity if needed
        if row_id >= self.row_count {
            self.expand_capacity(row_id + 1);
        }

        // Create bitmap for value if it doesn't exist
        let bitmap = self.bitmaps.entry(value).or_insert_with(|| {
            let mut bv = BitVec::from_elem(self.row_count, false);
            bv
        });

        // Ensure bitmap is large enough
        if bitmap.len() <= row_id {
            bitmap.grow(row_id + 1 - bitmap.len(), false);
        }

        bitmap.set(row_id, true);
    }

    fn expand_capacity(&mut self, new_size: usize) {
        let old_size = self.row_count;
        self.row_count = new_size;

        for bitmap in self.bitmaps.values_mut() {
            bitmap.grow(new_size - old_size, false);
        }
    }

    pub fn query_equal(&self, value: &T) -> BitVec {
        if let Some(bitmap) = self.bitmaps.get(value) {
            bitmap.clone()
        } else {
            BitVec::from_elem(self.row_count, false)
        }
    }

    pub fn query_in(&self, values: &[T]) -> BitVec {
        let mut result = BitVec::from_elem(self.row_count, false);
        
        for value in values {
            if let Some(bitmap) = self.bitmaps.get(value) {
                result.or(bitmap);
            }
        }
        
        result
    }

    pub fn query_not_equal(&self, value: &T) -> BitVec {
        let mut result = BitVec::from_elem(self.row_count, true);
        
        if let Some(bitmap) = self.bitmaps.get(value) {
            for i in 0..self.row_count {
                if bitmap.get(i).unwrap_or(false) {
                    result.set(i, false);
                }
            }
        }
        
        result
    }

    pub fn get_cardinality(&self) -> HashMap<T, usize> {
        self.bitmaps.iter()
            .map(|(value, bitmap)| (value.clone(), bitmap.iter().filter(|&b| b).count()))
            .collect()
    }

    pub fn get_storage_info(&self) -> BitmapIndexStats {
        let total_bits: usize = self.bitmaps.values().map(|b| b.len()).sum();
        BitmapIndexStats {
            unique_values: self.bitmaps.len(),
            total_bits,
            total_bytes: total_bits / 8,
            row_count: self.row_count,
        }
    }
}

#[derive(Debug)]
pub struct BitmapIndexStats {
    pub unique_values: usize,
    pub total_bits: usize,
    pub total_bytes: usize,
    pub row_count: usize,
}

// Run-Length Encoded Bitmap Index
#[derive(Debug, Clone)]
pub struct CompressedBitmapIndex<T>
where
    T: std::hash::Hash + Eq + Clone,
{
    compressed_bitmaps: HashMap<T, Vec<i32>>,
    row_count: usize,
}

impl<T> CompressedBitmapIndex<T>
where
    T: std::hash::Hash + Eq + Clone,
{
    pub fn new() -> Self {
        CompressedBitmapIndex {
            compressed_bitmaps: HashMap::new(),
            row_count: 0,
        }
    }

    fn compress_bitmap(&self, bitmap: &BitVec) -> Vec<i32> {
        if bitmap.is_empty() {
            return Vec::new();
        }

        let mut runs = Vec::new();
        let mut current_bit = bitmap.get(0).unwrap_or(false);
        let mut current_run = 1i32;

        for i in 1..bitmap.len() {
            let bit = bitmap.get(i).unwrap_or(false);
            if bit == current_bit {
                current_run += 1;
            } else {
                runs.push(if current_bit { current_run } else { -current_run });
                current_bit = bit;
                current_run = 1;
            }
        }

        runs.push(if current_bit { current_run } else { -current_run });
        runs
    }

    fn decompress_bitmap(&self, runs: &[i32], length: usize) -> BitVec {
        let mut bitmap = BitVec::from_elem(length, false);
        let mut position = 0usize;

        for &run in runs {
            if run > 0 {
                // Run of 1s
                for i in position..position + (run as usize) {
                    if i < length {
                        bitmap.set(i, true);
                    }
                }
            }
            position += run.abs() as usize;
        }

        bitmap
    }

    pub fn add_batch(&mut self, column_data: &[T]) {
        self.row_count = column_data.len();
        let mut temp_bitmaps: HashMap<T, BitVec> = HashMap::new();

        // Create temporary bitmaps
        for (row_id, value) in column_data.iter().enumerate() {
            let bitmap = temp_bitmaps.entry(value.clone()).or_insert_with(|| {
                BitVec::from_elem(self.row_count, false)
            });
            bitmap.set(row_id, true);
        }

        // Compress bitmaps
        for (value, bitmap) in temp_bitmaps {
            let compressed = self.compress_bitmap(&bitmap);
            self.compressed_bitmaps.insert(value, compressed);
        }
    }

    pub fn query_equal(&self, value: &T) -> BitVec {
        if let Some(runs) = self.compressed_bitmaps.get(value) {
            self.decompress_bitmap(runs, self.row_count)
        } else {
            BitVec::from_elem(self.row_count, false)
        }
    }
}

// Example usage
fn demo_bitmap_index() {
    let mut bitmap_idx = BitmapIndex::new();
    
    // Sample data: colors of cars
    let cars = vec!["red", "blue", "red", "green", "blue", "red", "yellow"];
    for (row_id, &color) in cars.iter().enumerate() {
        bitmap_idx.add_value(row_id, color.to_string());
    }
    
    // Query examples
    let red_cars = bitmap_idx.query_equal(&"red".to_string());
    let red_indices: Vec<usize> = red_cars.iter().enumerate()
        .filter_map(|(i, b)| if b { Some(i) } else { None })
        .collect();
    println!("Red cars (rows): {:?}", red_indices);
    
    let blue_or_green = bitmap_idx.query_in(&["blue".to_string(), "green".to_string()]);
    let blue_green_indices: Vec<usize> = blue_or_green.iter().enumerate()
        .filter_map(|(i, b)| if b { Some(i) } else { None })
        .collect();
    println!("Blue or green cars: {:?}", blue_green_indices);
    
    // Compressed bitmap index
    let mut compressed_idx = CompressedBitmapIndex::new();
    let cars_owned: Vec<String> = cars.iter().map(|s| s.to_string()).collect();
    compressed_idx.add_batch(&cars_owned);
    
    let red_cars_compressed = compressed_idx.query_equal(&"red".to_string());
    let red_compressed_indices: Vec<usize> = red_cars_compressed.iter().enumerate()
        .filter_map(|(i, b)| if b { Some(i) } else { None })
        .collect();
    println!("Red cars (compressed): {:?}", red_compressed_indices);
    
    println!("Storage info: {:?}", bitmap_idx.get_storage_info());
}
```

## LSM Tree Index Implementation {#lsm}

### Python Implementation

```python
import heapq
import os
import pickle
import threading
from typing import Any, Iterator, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SSTableEntry:
    key: Any
    value: Any
    timestamp: int
    deleted: bool = False

class MemTable:
    def __init__(self, max_size: int = 1000):
        self.data: dict = {}
        self.max_size = max_size
        self.size = 0
    
    def put(self, key: Any, value: Any, timestamp: int) -> None:
        if key not in self.data:
            self.size += 1
        self.data[key] = SSTableEntry(key, value, timestamp)
    
    def get(self, key: Any) -> Optional[SSTableEntry]:
        return self.data.get(key)
    
    def delete(self, key: Any, timestamp: int) -> None:
        if key not in self.data:
            self.size += 1
        self.data[key] = SSTableEntry(key, None, timestamp, deleted=True)
    
    def is_full(self) -> bool:
        return self.size >= self.max_size
    
    def get_sorted_entries(self) -> List[SSTableEntry]:
        return sorted(self.data.values(), key=lambda x: x.key)

class SSTable:
    def __init__(self, filename: str, entries: List[SSTableEntry]):
        self.filename = filename
        self.min_key = entries[0].key if entries else None
        self.max_key = entries[-1].key if entries else None
        self._write_to_disk(entries)
    
    def _write_to_disk(self, entries: List[SSTableEntry]) -> None:
        with open(self.filename, 'wb') as f:
            pickle.dump(entries, f)
    
    def read_all(self) -> List[SSTableEntry]:
        try:
            with open(self.filename, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []
    
    def get(self, key: Any) -> Optional[SSTableEntry]:
        # In a real implementation, this would use binary search
        # or bloom filters for efficiency
        entries = self.read_all()
        for entry in entries:
            if entry.key == key:
                return entry
        return None
    
    def cleanup(self) -> None:
        if os.path.exists(self.filename):
            os.remove(self.filename)

class LSMTreeIndex:
    def __init__(self, base_path: str = "./lsm_data", memtable_size: int = 100):
        self.base_path = base_path
        self.memtable_size = memtable_size
        self.memtable = MemTable(memtable_size)
        self.sstables: List[SSTable] = []
        self.next_sstable_id = 0
        self.timestamp = 0
        self.lock = threading.RLock()
        
        # Create directory if it doesn't exist
        os.makedirs(base_path, exist_ok=True)
    
    def _get_next_timestamp(self) -> int:
        self.timestamp += 1
        return self.timestamp
    
    def _flush_memtable(self) -> None:
        """Flush memtable to disk as SSTable."""
        if self.memtable.size == 0:
            return
        
        entries = self.memtable.get_sorted_entries()
        filename = os.path.join(self.base_path, f"sstable_{self.next_sstable_id}.dat")
        sstable = SSTable(filename, entries)
        
        self.sstables.append(sstable)
        self.next_sstable_id += 1
        self.memtable = MemTable(self.memtable_size)
        
        # Trigger compaction if needed
        self._maybe_compact()
    
    def _maybe_compact(self) -> None:
        """Simple compaction strategy: compact when we have too many SSTables."""
        if len(self.sstables) > 4:
            self._compact_sstables()
    
    def _compact_sstables(self) -> None:
        """Compact multiple SSTables into one."""
        if len(self.sstables) < 2:
            return
        
        # Merge all SSTables
        all_entries = []
        for sstable in self.sstables:
            all_entries.extend(sstable.read_all())
        
        # Group by key and keep only the latest version
        latest_entries = {}
        for entry in all_entries:
            if entry.key not in latest_entries or entry.timestamp > latest_entries[entry.key].timestamp:
                latest_entries[entry.key] = entry
        
        # Remove deleted entries
        final_entries = [entry for entry in latest_entries.values() if not entry.deleted]
        final_entries.sort(key=lambda x: x.key)
        
        # Clean up old SSTables
        for sstable in self.sstables:
            sstable.cleanup()
        
        # Create new compacted SSTable
        if final_entries:
            filename = os.path.join(self.base_path, f"sstable_compacted_{self.next_sstable_id}.dat")
            new_sstable = SSTable(filename, final_entries)
            self.sstables = [new_sstable]
            self.next_sstable_id += 1
        else:
            self.sstables = []
    
    def put(self, key: Any, value: Any) -> None:
        """Insert or update a key-value pair."""
        with self.lock:
            timestamp = self._get_next_timestamp()
            self.memtable.put(key, value, timestamp)
            
            if self.memtable.is_full():
                self._flush_memtable()
    
    def get(self, key: Any) -> Optional[Any]:
        """Retrieve value for a key."""
        with self.lock:
            # Check memtable first
            entry = self.memtable.get(key)
            if entry:
                return None if entry.deleted else entry.value
            
            # Check SSTables (newest first)
            for sstable in reversed(self.sstables):
                if sstable.min_key <= key <= sstable.max_key:
                    entry = sstable.get(key)
                    if entry:
                        return None if entry.deleted else entry.value
            
            return None
    
    def delete(self, key: Any) -> None:
        """Delete a key (tombstone)."""
        with self.lock:
            timestamp = self._get_next_timestamp()
            self.memtable.delete(key, timestamp)
            
            if self.memtable.is_full():
                self._flush_memtable()
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Perform range query."""
        with self.lock:
            # Collect all entries from memtable and SSTables
            all_entries = []
            
            # From memtable
            for entry in self.memtable.get_sorted_entries():
                if start_key <= entry.key <= end_key:
                    all_entries.append(entry)
            
            # From SSTables
            for sstable in self.sstables:
                if sstable.max_key >= start_key and sstable.min_key <= end_key:
                    for entry in sstable.read_all():
                        if start_key <= entry.key <= end_key:
                            all_entries.append(entry)
            
            # Keep only latest version of each key
            latest_entries = {}
            for entry in all_entries:
                if entry.key not in latest_entries or entry.timestamp > latest_entries[entry.key].timestamp:
                    latest_entries[entry.key] = entry
            
            # Filter out deleted entries and return
            result = []
            for entry in sorted(latest_entries.values(), key=lambda x: x.key):
                if not entry.deleted:
                    result.append((entry.key, entry.value))
            
            return result
    
    def cleanup(self) -> None:
        """Clean up all files."""
        for sstable in self.sstables:
            sstable.cleanup()

# Example usage
def demo_lsm_tree():
    lsm = LSMTreeIndex(memtable_size=3)  # Small size for demo
    
    try:
        # Insert data
        data = [(10, "ten"), (30, "thirty"), (20, "twenty"), (40, "forty"), (50, "fifty")]
        for key, value in data:
            lsm.put(key, value)
        
        # This should trigger flushes due to small memtable size
        print(f"Search 30: {lsm.get(30)}")
        print(f"Range 20-40: {lsm.range_query(20, 40)}")
        
        # Test deletion
        lsm.delete(30)
        print(f"Search 30 after deletion: {lsm.get(30)}")
        
    finally:
        lsm.cleanup()
```

### Rust Implementation

```rust
use std::collections::{BTreeMap, HashMap};
use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::{Path, PathBuf};
use std::sync::{Arc, RwLock};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SSTableEntry<K, V> {
    pub key: K,
    pub value: Option<V>,
    pub timestamp: u64,
    pub deleted: bool,
}

#[derive(Debug)]
pub struct MemTable<K, V> 
where
    K: Ord + Clone,
    V: Clone,
{
    data: BTreeMap<K, SSTableEntry<K, V>>,
    max_size: usize,
}

impl<K, V> MemTable<K, V>
where
    K: Ord + Clone,
    V: Clone,
{
    pub fn new(max_size: usize) -> Self {
        MemTable {
            data: BTreeMap::new(),
            max_size,
        }
    }

    pub fn put(&mut self, key: K, value: V, timestamp: u64) {
        let entry = SSTableEntry {
            key: key.clone(),
            value: Some(value),
            timestamp,
            deleted: false,
        };
        self.data.insert(key, entry);
    }

    pub fn get(&self, key: &K) -> Option<&SSTableEntry<K, V>> {
        self.data.get(key)
    }

    pub fn delete(&mut self, key: K, timestamp: u64) {
        let entry = SSTableEntry {
            key: key.clone(),
            value: None,
            timestamp,
            deleted: true,
        };
        self.data.insert(key, entry);
    }

    pub fn is_full(&self) -> bool {
        self.data.len() >= self.max_size
    }

    pub fn get_sorted_entries(&self) -> Vec<SSTableEntry<K, V>> {
        self.data.values().cloned().collect()
    }

    pub fn clear(&mut self) {
        self.data.clear();
    }

    pub fn range_entries(&self, start: &K, end: &K) -> Vec<SSTableEntry<K, V>> {
        self.data
            .range(start..=end)
            .map(|(_, v)| v.clone())
            .collect()
    }
}

#[derive(Debug)]
pub struct SSTable<K, V> 
where
    K: Ord + Clone + Serialize + for<'de> Deserialize<'de>,
    V: Clone + Serialize + for<'de> Deserialize<'de>,
{
    filename: PathBuf,
    min_key: Option<K>,
    max_key: Option<K>,
}

impl<K, V> SSTable<K, V>
where
    K: Ord + Clone + Serialize + for<'de> Deserialize<'de>,
    V: Clone + Serialize + for<'de> Deserialize<'de>,
{
    pub fn new(filename: PathBuf, entries: &[SSTableEntry<K, V>]) -> Result<Self, Box<dyn std::error::Error>> {
        let min_key = entries.first().map(|e| e.key.clone());
        let max_key = entries.last().map(|e| e.key.clone());
        
        // Write entries to disk
        let file = File::create(&filename)?;
        let writer = BufWriter::new(file);
        bincode::serialize_into(writer, entries)?;
        
        Ok(SSTable {
            filename,
            min_key,
            max_key,
        })
    }

    pub fn read_all(&self) -> Result<Vec<SSTableEntry<K, V>>, Box<dyn std::error::Error>> {
        let file = File::open(&self.filename)?;
        let reader = BufReader::new(file);
        let entries = bincode::deserialize_from(reader)?;
        Ok(entries)
    }

    pub fn get(&self, key: &K) -> Result<Option<SSTableEntry<K, V>>, Box<dyn std::error::Error>> {
        let entries = self.read_all()?;
        // In a real implementation, this would use binary search
        Ok(entries.into_iter().find(|entry| entry.key == *key))
    }

    pub fn cleanup(&self) -> Result<(), std::io::Error> {
        if self.filename.exists() {
            fs::remove_file(&self.filename)?;
        }
        Ok(())
    }

    pub fn min_key(&self) -> Option<&K> {
        self.min_key.as_ref()
    }

    pub fn max_key(&self) -> Option<&K> {
        self.max_key.as_ref()
    }

    pub fn range_entries(&self, start: &K, end: &K) -> Result<Vec<SSTableEntry<K, V>>, Box<dyn std::error::Error>> {
        let entries = self.read_all()?;
        Ok(entries.into_iter()
            .filter(|entry| entry.key >= *start && entry.key <= *end)
            .collect())
    }
}

#[derive(Debug)]
pub struct LSMTreeIndex<K, V>
where
    K: Ord + Clone + Serialize + for<'de> Deserialize<'de>,
    V: Clone + Serialize + for<'de> Deserialize<'de>,
{
    memtable: Arc<RwLock<MemTable<K, V>>>,
    sstables: Arc<RwLock<Vec<SSTable<K, V>>>>,
    base_path: PathBuf,
    memtable_size: usize,
    next_sstable_id: Arc<RwLock<u64>>,
    timestamp: Arc<RwLock<u64>>,
}

impl<K, V> LSMTreeIndex<K, V>
where
    K: Ord + Clone + Serialize + for<'de> Deserialize<'de> + std::fmt::Debug,
    V: Clone + Serialize + for<'de> Deserialize<'de> + std::fmt::Debug,
{
    pub fn new<P: AsRef<Path>>(base_path: P, memtable_size: usize) -> Result<Self, Box<dyn std::error::Error>> {
        let base_path = base_path.as_ref().to_path_buf();
        fs::create_dir_all(&base_path)?;

        Ok(LSMTreeIndex {
            memtable: Arc::new(RwLock::new(MemTable::new(memtable_size))),
            sstables: Arc::new(RwLock::new(Vec::new())),
            base_path,
            memtable_size,
            next_sstable_id: Arc::new(RwLock::new(0)),
            timestamp: Arc::new(RwLock::new(0)),
        })
    }

    fn get_next_timestamp(&self) -> u64 {
        let mut timestamp = self.timestamp.write().unwrap();
        *timestamp += 1;
        *timestamp
    }

    fn flush_memtable(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut memtable = self.memtable.write().unwrap();
        
        if memtable.data.is_empty() {
            return Ok(());
        }

        let entries = memtable.get_sorted_entries();
        let mut next_id = self.next_sstable_id.write().unwrap();
        let filename = self.base_path.join(format!("sstable_{}.dat", *next_id));
        
        let sstable = SSTable::new(filename, &entries)?;
        
        let mut sstables = self.sstables.write().unwrap();
        sstables.push(sstable);
        *next_id += 1;
        
        memtable.clear();
        drop(memtable);
        drop(sstables);
        drop(next_id);

        self.maybe_compact()?;
        Ok(())
    }

    fn maybe_compact(&self) -> Result<(), Box<dyn std::error::Error>> {
        let sstables = self.sstables.read().unwrap();
        if sstables.len() > 4 {
            drop(sstables);
            self.compact_sstables()?;
        }
        Ok(())
    }

    fn compact_sstables(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut sstables = self.sstables.write().unwrap();
        
        if sstables.len() < 2 {
            return Ok(());
        }

        // Read all entries from all SSTables
        let mut all_entries = Vec::new();
        for sstable in &*sstables {
            let entries = sstable.read_all()?;
            all_entries.extend(entries);
        }

        // Group by key and keep only the latest version
        let mut latest_entries: HashMap<K, SSTableEntry<K, V>> = HashMap::new();
        for entry in all_entries {
            match latest_entries.get(&entry.key) {
                Some(existing) if existing.timestamp >= entry.timestamp => {},
                _ => {
                    latest_entries.insert(entry.key.clone(), entry);
                }
            }
        }

        // Filter out deleted entries and sort
        let mut final_entries: Vec<_> = latest_entries
            .into_values()
            .filter(|entry| !entry.deleted)
            .collect();
        final_entries.sort_by(|a, b| a.key.cmp(&b.key));

        // Clean up old SSTables
        for sstable in &*sstables {
            let _ = sstable.cleanup();
        }

        // Create new compacted SSTable
        if !final_entries.is_empty() {
            let mut next_id = self.next_sstable_id.write().unwrap();
            let filename = self.base_path.join(format!("sstable_compacted_{}.dat", *next_id));
            let new_sstable = SSTable::new(filename, &final_entries)?;
            *sstables = vec![new_sstable];
            *next_id += 1;
        } else {
            sstables.clear();
        }

        Ok(())
    }

    pub fn put(&self, key: K, value: V) -> Result<(), Box<dyn std::error::Error>> {
        let timestamp = self.get_next_timestamp();
        
        {
            let mut memtable = self.memtable.write().unwrap();
            memtable.put(key, value, timestamp);
            
            if memtable.is_full() {
                drop(memtable);
                self.flush_memtable()?;
            }
        }
        
        Ok(())
    }

    pub fn get(&self, key: &K) -> Result<Option<V>, Box<dyn std::error::Error>> {
        // Check memtable first
        {
            let memtable = self.memtable.read().unwrap();
            if let Some(entry) = memtable.get(key) {
                return Ok(if entry.deleted { None } else { entry.value.clone() });
            }
        }

        // Check SSTables (newest first)
        let sstables = self.sstables.read().unwrap();
        for sstable in sstables.iter().rev() {
            if let (Some(min), Some(max)) = (sstable.min_key(), sstable.max_key()) {
                if key >= min && key <= max {
                    if let Some(entry) = sstable.get(key)? {
                        return Ok(if entry.deleted { None } else { entry.value });
                    }
                }
            }
        }

        Ok(None)
    }

    pub fn delete(&self, key: K) -> Result<(), Box<dyn std::error::Error>> {
        let timestamp = self.get_next_timestamp();
        
        {
            let mut memtable = self.memtable.write().unwrap();
            memtable.delete(key, timestamp);
            
            if memtable.is_full() {
                drop(memtable);
                self.flush_memtable()?;
            }
        }
        
        Ok(())
    }

    pub fn range_query(&self, start: &K, end: &K) -> Result<Vec<(K, V)>, Box<dyn std::error::Error>> {
        let mut all_entries = Vec::new();

        // From memtable
        {
            let memtable = self.memtable.read().unwrap();
            all_entries.extend(memtable.range_entries(start, end));
        }

        // From SSTables
        {
            let sstables = self.sstables.read().unwrap();
            for sstable in sstables.iter().rev() {
                if let (Some(min), Some(max)) = (sstable.min_key(), sstable.max_key()) {
                    if start >= min && end <= max {
                        all_entries.extend(sstable.range_entries(start, end));
                    }
                }
            }
        }

        Ok(all_entries)
    }
    pub fn cleanup(&self) -> Result<(), Box<dyn std::error::Error>> {
        let sstables = self.sstables.read().unwrap();
        for sstable in &*sstables {
            sstable.cleanup()?;
        }
        Ok(())
    }
}

    """Add a value for a specific row."""
        # Ensure we have enough capacity
        if row_id >= self.row_count:
            self._expand_capacity(row_id + 1)
        
        # Create bitmap for value if it doesn't exist
        if value not in self.bitmaps:
            self.bitmaps[value] = bitarray(self.row_count)
            self.bitmaps[value].setall(False)
        
        # Set bit for this row and value
        self.bitmaps[value][row_id] = True
    
    def _expand_capacity(self, new_size: int) -> None:
        """Expand all bitmaps to accommodate more rows."""
        old_size = self.row_count
        self.row_count = new_size
        
        for bitmap in self.bitmaps.values():
            bitmap.extend([False] * (new_size - old_size))
    
    def query_equal(self, value: Any) -> bitarray:
        """Query for rows where column equals value."""
        if value in self.bitmaps:
            return self.bitmaps[value].copy()
        else:
            # Return empty bitmap
            result = bitarray(self.row_count)
            result.setall(False)
            return result
    
    def query_in(self, values: Set[Any]) -> bitarray:
        """Query for rows where column is in set of values."""
        result = bitarray(self.row_count)
        result.setall(False)
        
        for value in values:
            if value in self.bitmaps:
                result |= self.bitmaps[value]
        
        return result
    
    def query_not_equal(self, value: Any) -> bitarray:
        """Query for rows where column does not equal value."""
        result = bitarray(self.row_count)
        result.setall(True)
        
        if value in self.bitmaps:
            result &= ~self.bitmaps[value]
        
        return result
    
    def get_cardinality(self) -> Dict[Any, int]:
        """Get count of rows for each value."""
        return {value: bitmap.count() for value, bitmap in self.bitmaps.items()}
    
    def get_storage_info(self) -> Dict[str, int]:
        """Get storage information about the bitmap index."""
        total_bits = sum(len(bitmap) for bitmap in self.bitmaps.values())
        return {
            'unique_values': len(self.bitmaps),
            'total_bits': total_bits,
            'total_bytes': total_bits // 8,
            'row_count': self.row_count,
        }

I'll create a comprehensive ASCII diagram showing how database indexing works step by step, from table structure to index creation and query execution.I've created a comprehensive ASCII diagram that walks through database indexing step by step. The diagram covers:

1. **Original table structure** - Shows how queries work without indexes (full table scan)
2. **Index creation process** - Demonstrates how the database extracts and sorts values
3. **B-tree structure** - Visualizes the hierarchical index organization
4. **Indexed query execution** - Shows the dramatic performance improvement
5. **Performance comparison** - Quantifies the speed benefits with real numbers
6. **Different index types** - Explains clustered, non-clustered, and composite indexes
7. **Index maintenance** - Covers how INSERT, UPDATE, and DELETE operations affect indexes

The key takeaway is that indexes transform query performance from O(n) linear search to O(log n) logarithmic search, which can mean the difference between checking 50,000 rows versus just 17 rows in a 100,000 record table. However, this comes with trade-offs in storage space and write performance, which is why understanding when and how to use indexes is crucial for database optimization.

# Database Indexing: Step-by-Step ASCII Diagram

## Step 1: Original Table Structure (Without Index)

```
EMPLOYEES TABLE
┌─────────────────────────────────────────────────────────────┐
│ ROW_ID │ EMP_ID │   NAME    │ DEPARTMENT │   SALARY   │ AGE │
├────────┼────────┼───────────┼────────────┼────────────┼─────┤
│   1    │  1001  │   Alice   │     HR     │   50000    │ 28  │
│   2    │  1002  │    Bob    │     IT     │   75000    │ 32  │
│   3    │  1003  │  Charlie  │  Finance   │   60000    │ 45  │
│   4    │  1004  │   Diana   │     IT     │   80000    │ 29  │
│   5    │  1005  │    Eve    │     HR     │   55000    │ 35  │
│   6    │  1006  │   Frank   │  Finance   │   65000    │ 41  │
│   7    │  1007  │   Grace   │     IT     │   70000    │ 26  │
│   8    │  1008  │   Henry   │  Finance   │   58000    │ 38  │
└────────┴────────┴───────────┴────────────┴────────────┴─────┘

WITHOUT INDEX: Query "SELECT * FROM EMPLOYEES WHERE EMP_ID = 1005"
┌─────────────────────────────────────────────────────────────┐
│                     FULL TABLE SCAN                         │
│  ↓ Check Row 1: EMP_ID = 1001 ❌ (Not Found)                │
│  ↓ Check Row 2: EMP_ID = 1002 ❌ (Not Found)                │
│  ↓ Check Row 3: EMP_ID = 1003 ❌ (Not Found)                │
│  ↓ Check Row 4: EMP_ID = 1004 ❌ (Not Found)                │
│  ↓ Check Row 5: EMP_ID = 1005 ✅ (FOUND!)                   │
│  ↓ Check Row 6: EMP_ID = 1006 ❌ (Continue...)              │
│  ↓ Check Row 7: EMP_ID = 1007 ❌ (Continue...)              │
│  ↓ Check Row 8: EMP_ID = 1008 ❌ (End of Table)             │
└─────────────────────────────────────────────────────────────┘
Time Complexity: O(n) - Must check every row in worst case
```

## Step 2: Index Creation Process

```
CREATE INDEX idx_emp_id ON EMPLOYEES(EMP_ID);

INDEX CREATION PROCESS:
┌─────────────────────────────────────────────────────────────┐
│ STEP A: Extract EMP_ID values and ROW_IDs                   │
│ ┌───────────┬───────────┬───────────┬───────────┐           │
│ │ EMP_ID    │ ROW_ID    │ EMP_ID    │ ROW_ID    │           │
│ │  1001  →  │    1      │  1005  →  │    5      │           │
│ │  1002  →  │    2      │  1006  →  │    6      │           │
│ │  1003  →  │    3      │  1007  →  │    7      │           │
│ │  1004  →  │    4      │  1008  →  │    8      │           │
│ └───────────┴───────────┴───────────┴───────────┘           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP B: Sort by EMP_ID values (Ascending Order)             │
│ ┌───────────┬───────────┬───────────┬───────────┐           │
│ │ EMP_ID    │ ROW_ID    │ EMP_ID    │ ROW_ID    │           │
│ │  1001  →  │    1      │  1005  →  │    5      │           │
│ │  1002  →  │    2      │  1006  →  │    6      │           │
│ │  1003  →  │    3      │  1007  →  │    7      │           │
│ │  1004  →  │    4      │  1008  →  │    8      │           │
│ └───────────┴───────────┴───────────┴───────────┘           │
│                    (Already sorted in this case)            │
└─────────────────────────────────────────────────────────────┘
```

## Step 3: B-Tree Index Structure

```
B-TREE INDEX ON EMP_ID
                    ┌─────────────┐
                    │ ROOT NODE   │
                    │   1004      │ ← Split point
                    └──────┬──────┘
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
    ┌─────────────┐                   ┌─────────────┐
    │ LEAF NODE 1 │                   │ LEAF NODE 2 │
    │             │                   │             │
    │ 1001 → 1    │                   │ 1005 → 5    │
    │ 1002 → 2    │                   │ 1006 → 6    │
    │ 1003 → 3    │                   │ 1007 → 7    │
    │ 1004 → 4    │                   │ 1008 → 8    │
    └─────────────┘                   └─────────────┘
         ↑                                     ↑
         │                                     │
    EMP_ID ≤ 1004                        EMP_ID > 1004

INDEX STRUCTURE EXPLANATION:
┌─────────────────────────────────────────────────────────────┐
│ • Root Node: Contains split values to navigate tree         │
│ • Leaf Nodes: Contain actual EMP_ID → ROW_ID mappings       │
│ • Sorted Order: Enables binary search (O(log n))            │
│ • Balanced Tree: Ensures consistent performance             │
└─────────────────────────────────────────────────────────────┘
```

## Step 4: Index-Based Query Execution

```
WITH INDEX: Query "SELECT * FROM EMPLOYEES WHERE EMP_ID = 1005"

STEP 1: INDEX TRAVERSAL
┌─────────────────────────────────────────────────────────────┐
│                    ┌─────────────┐                          │
│                    │ ROOT NODE   │                          │
│    Search 1005 →   │   1004      │ → 1005 > 1004            │
│                    └──────┬──────┘   Go RIGHT               │
│                           │                                 │
│          ┌────────────────┴────────────────┐                │
│          ▼                                 ▼                │
│    ┌─────────────┐                   ┌─────────────┐        │
│    │ LEAF NODE 1 │                   │ LEAF NODE 2 │        │
│    │             │       ✅          │             │        │
│    │ 1001 → 1    │   Found Here!     │ 1005 → 5    │ ←───   │
│    │ 1002 → 2    │                   │ 1006 → 6    │        │
│    │ 1003 → 3    │                   │ 1007 → 7    │        │
│    │ 1004 → 4    │                   │ 1008 → 8    │        │
│    └─────────────┘                   └─────────────┘        │
└─────────────────────────────────────────────────────────────┘

STEP 2: DIRECT ROW ACCESS
┌─────────────────────────────────────────────────────────────┐
│ Index found: EMP_ID 1005 → ROW_ID 5                         │
│ Direct access to Row 5 in main table:                       │
│                                                             │
│ EMPLOYEES TABLE                                             │
│ ┌────────┬────────┬───────────┬────────────┬────────┬─────┐ │
│ │ROW_ID 5│  1005  │    Eve    │     HR     │ 55000  │ 35  │ │
│ └────────┴────────┴───────────┴────────────┴────────┴─────┘ │
│                           ↑                                 │
│                    RESULT FOUND!                            │
└─────────────────────────────────────────────────────────────┘

Time Complexity: O(log n) - Logarithmic search time
Steps Required: 2 (instead of potentially 8 with full scan)
```

## Step 5: Performance Comparison

```
PERFORMANCE ANALYSIS

WITHOUT INDEX (Full Table Scan):
┌─────────────────────────────────────────────────────────────┐
│ Records │ Average Comparisons │ Worst Case │ Time Complexity│
├─────────┼─────────────────────┼────────────┼────────────────┤
│    8    │         4.5         │     8      │     O(n)       │
│   100   │         50          │    100     │     O(n)       │
│  1000   │        500          │   1000     │     O(n)       │
│ 10000   │       5000          │  10000     │     O(n)       │
│100000   │      50000          │ 100000     │     O(n)       │
└─────────┴─────────────────── ─┴────────────┴────────────────┘

WITH INDEX (B-Tree Search):
┌─────────────────────────────────────────────────────────────┐
│ Records │ Tree Depth │ Max Comparisons │ Time Complexity    │
├─────────┼────────────┼─────────────────┼────────────────────┤
│    8    │     3      │       3         │    O(log n)        │
│   100   │     7      │       7         │    O(log n)        │
│  1000   │    10      │      10         │    O(log n)        │
│ 10000   │    14      │      14         │    O(log n)        │
│100000   │    17      │      17         │    O(log n)        │
└─────────┴────────────┴─────────────────┴────────────────────┘

SPEED IMPROVEMENT VISUALIZATION:
For 100,000 records searching for last item:

Without Index: ████████████████████████████████████████████████ 50,000 ops
With Index:    █                                                    17 ops

Improvement Factor: ~2,941x faster!
```

## Step 6: Index Types and Use Cases

```
COMMON INDEX TYPES:

1. PRIMARY INDEX (Clustered)
┌─────────────────────────────────────────────────────────────┐
│ • Data physically sorted by index key                      │
│ • One per table (usually on primary key)                   │
│ • Fastest for range queries                                │
│                                                             │
│ TABLE DATA STORED AS:                                       │
│ [1001][Alice][HR][50000] → [1002][Bob][IT][75000] →       │
│ [1003][Charlie][Finance][60000] → ...                      │
└─────────────────────────────────────────────────────────────┘

2. SECONDARY INDEX (Non-Clustered)
┌─────────────────────────────────────────────────────────────┐
│ • Separate structure pointing to table rows                │
│ • Multiple allowed per table                               │
│ • Additional lookup required                               │
│                                                             │
│ INDEX: [Salary][ROW_ID] → [50000][1] → [55000][5] →       │
│        [58000][8] → [60000][3] → ...                       │
└─────────────────────────────────────────────────────────────┘

3. COMPOSITE INDEX (Multi-Column)
┌─────────────────────────────────────────────────────────────┐
│ CREATE INDEX idx_dept_salary ON EMPLOYEES(DEPARTMENT, SALARY)│
│                                                             │
│ INDEX STRUCTURE:                                            │
│ [Finance][58000] → ROW_ID 8                                │
│ [Finance][60000] → ROW_ID 3                                │
│ [Finance][65000] → ROW_ID 6                                │
│ [HR][50000] → ROW_ID 1                                     │
│ [HR][55000] → ROW_ID 5                                     │
│ [IT][70000] → ROW_ID 7                                     │
│ [IT][75000] → ROW_ID 2                                     │
│ [IT][80000] → ROW_ID 4                                     │
└─────────────────────────────────────────────────────────────┘
```

## Step 7: Index Maintenance

```
INDEX MAINTENANCE OPERATIONS:

INSERT Operation:
┌─────────────────────────────────────────────────────────────┐
│ INSERT INTO EMPLOYEES VALUES (1009, 'Ivy', 'IT', 72000, 30)│
│                                                             │
│ 1. Insert into main table → New ROW_ID = 9                 │
│ 2. Update index structure:                                  │
│                                                             │
│    Before:                        After:                   │
│    [1007 → 7]                    [1007 → 7]                │
│    [1008 → 8]                    [1008 → 8]                │
│                                  [1009 → 9] ← NEW          │
│                                                             │
│ 3. Rebalance B-tree if necessary                           │
└─────────────────────────────────────────────────────────────┘

UPDATE Operation:
┌─────────────────────────────────────────────────────────────┐
│ UPDATE EMPLOYEES SET EMP_ID = 1010 WHERE EMP_ID = 1005     │
│                                                             │
│ 1. Update main table row                                    │
│ 2. Remove old index entry: [1005 → 5]                      │
│ 3. Insert new index entry: [1010 → 5]                      │
│ 4. Maintain sorted order in index                          │
└─────────────────────────────────────────────────────────────┘

DELETE Operation:
┌─────────────────────────────────────────────────────────────┐
│ DELETE FROM EMPLOYEES WHERE EMP_ID = 1003                  │
│                                                             │
│ 1. Delete from main table (ROW_ID 3)                       │
│ 2. Remove from index: [1003 → 3]                           │
│ 3. Rebalance tree structure if needed                      │
└─────────────────────────────────────────────────────────────┘

INDEX OVERHEAD:
┌─────────────────────────────────────────────────────────────┐
│ PROS:                        │ CONS:                        │
│ • Fast SELECT queries        │ • Extra storage space        │
│ • Efficient WHERE clauses    │ • Slower INSERT/UPDATE/DELETE│
│ • Quick ORDER BY operations  │ • Index maintenance overhead │
│ • Improved JOIN performance  │ • Memory usage               │
└─────────────────────────────────────────────────────────────┘
```

This diagram illustrates the complete process of database indexing, from the initial table structure through index creation, query execution, and maintenance operations. The B-tree structure enables logarithmic search time, dramatically improving query performance for large datasets.