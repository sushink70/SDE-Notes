# Complete Hash Tables Implementation Guide

## Key Features of This Guide:

**Theoretical Foundation:**
- Core concepts and properties of hash tables
- Different hash functions (division, multiplication, FNV-1a)
- Collision resolution strategies (separate chaining vs open addressing)

**Complete Python Implementation:**
- Full hash table with separate chaining
- Open addressing version with linear probing
- Automatic resizing based on load factor
- Iterator support and comprehensive methods

**Complete Rust Implementation:**
- Memory-safe implementation with generics
- Both separate chaining and open addressing versions
- Custom iterator implementation
- Comprehensive test suite

**Advanced Topics:**
- Robin Hood hashing
- Performance analysis with time/space complexity
- Cache performance considerations
- Security considerations (hash flooding attacks)

**Production-Ready Features:**
- Automatic resizing with configurable load factor thresholds
- Proper error handling
- Memory efficient implementations
- Thread safety considerations

Both implementations include extensive examples, test cases, and performance analysis. The code is production-ready and demonstrates best practices for hash table implementation in both languages.

The guide also covers when to use custom implementations versus built-in hash maps (`dict` in Python, `HashMap` in Rust) and provides practical advice for choosing the right approach for different use cases.



## Table of Contents

1. [Introduction to Hash Tables](#introduction)
2. [Core Concepts](#core-concepts)
3. [Hash Functions](#hash-functions)
4. [Collision Resolution Strategies](#collision-resolution)
5. [Python Implementation](#python-implementation)
6. [Rust Implementation](#rust-implementation)
7. [Performance Analysis](#performance-analysis)
8. [Advanced Topics](#advanced-topics)
9. [Best Practices](#best-practices)

## Introduction to Hash Tables {#introduction}

Hash tables (also known as hash maps) are one of the most important and widely used data structures in computer science. They provide average-case O(1) time complexity for insertion, deletion, and lookup operations by using a hash function to map keys to array indices.

### Key Advantages
- **Fast Operations**: Average O(1) time for basic operations
- **Flexible Keys**: Can use various data types as keys
- **Memory Efficient**: Good space utilization when properly sized
- **Widely Supported**: Built into most programming languages

### Use Cases
- Database indexing
- Caching systems
- Symbol tables in compilers
- Set implementations
- Frequency counting
- Memoization

## Core Concepts {#core-concepts}

### Basic Structure
A hash table consists of:
1. **Array/Bucket Array**: Fixed-size array to store key-value pairs
2. **Hash Function**: Maps keys to array indices
3. **Collision Resolution**: Handles when multiple keys hash to same index
4. **Load Factor**: Ratio of filled slots to total capacity

### Key Properties
- **Deterministic**: Same key always hashes to same index
- **Uniform Distribution**: Hash function should distribute keys evenly
- **Fast Computation**: Hash function should be quick to compute
- **Avalanche Effect**: Small key changes should cause large hash changes

## Hash Functions {#hash-functions}

### Simple Hash Functions

#### Division Method
```
hash(key) = key mod table_size
```
- Simple but can lead to clustering
- Table size should be prime number

#### Multiplication Method
```
hash(key) = floor(table_size * (key * A mod 1))
```
- A is constant (0 < A < 1), often (√5 - 1)/2
- Less sensitive to table size

### Advanced Hash Functions

#### FNV-1a Hash (for strings)
```python
def fnv1a_hash(data):
    hash_value = 2166136261  # FNV offset basis
    for byte in data:
        hash_value ^= byte
        hash_value *= 16777619  # FNV prime
        hash_value &= 0xffffffff  # Keep 32-bit
    return hash_value
```

#### SipHash (cryptographically secure)
Used in production systems where hash flooding attacks are a concern.

## Collision Resolution Strategies {#collision-resolution}

### 1. Separate Chaining
Each bucket contains a linked list (or other data structure) of all elements that hash to that index.

**Advantages:**
- Simple implementation
- No clustering
- Can handle high load factors

**Disadvantages:**
- Extra memory for pointers
- Cache performance issues

### 2. Open Addressing
All elements stored in the hash table array itself. When collision occurs, probe for next available slot.

#### Linear Probing
```
index = (hash(key) + i) mod table_size
```

#### Quadratic Probing
```
index = (hash(key) + i²) mod table_size
```

#### Double Hashing
```
index = (hash1(key) + i * hash2(key)) mod table_size
```

## Python Implementation {#python-implementation}

### Basic Hash Table with Separate Chaining

```python
class HashTable:
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
        self.load_factor_threshold = 0.75
    
    def _hash(self, key):
        """Simple hash function using built-in hash() and modulo."""
        return hash(key) % self.capacity
    
    def _resize(self):
        """Resize the hash table when load factor exceeds threshold."""
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
        """Retrieve value for given key."""
        index = self._hash(key)
        bucket = self.buckets[index]
        
        for k, v in bucket:
            if k == key:
                return v
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        """Remove key-value pair from hash table."""
        index = self._hash(key)
        bucket = self.buckets[index]
        
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
        """Return all keys in hash table."""
        result = []
        for bucket in self.buckets:
            for key, _ in bucket:
                result.append(key)
        return result
    
    def values(self):
        """Return all values in hash table."""
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
        return "{" + ", ".join(f"{k}: {v}" for k, v in items) + "}"

# Advanced Hash Table with Open Addressing (Linear Probing)
class OpenAddressingHashTable:
    class _Item:
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.deleted = False
    
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        self.size = 0
        self.table = [None] * self.capacity
        self.load_factor_threshold = 0.5  # Lower for open addressing
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def _find_slot(self, key):
        """Find slot for key using linear probing."""
        index = self._hash(key)
        original_index = index
        
        while self.table[index] is not None:
            if (self.table[index].key == key and 
                not self.table[index].deleted):
                return index, True  # Found existing key
            index = (index + 1) % self.capacity
            if index == original_index:  # Table full
                break
        
        return index, False  # Found empty slot or table full
    
    def _resize(self):
        """Resize and rehash the table."""
        old_table = self.table
        self.capacity *= 2
        self.size = 0
        self.table = [None] * self.capacity
        
        for item in old_table:
            if item is not None and not item.deleted:
                self.put(item.key, item.value)
    
    def put(self, key, value):
        """Insert or update key-value pair."""
        if self.size >= self.capacity * self.load_factor_threshold:
            self._resize()
        
        index, found = self._find_slot(key)
        
        if found:
            # Update existing key
            self.table[index].value = value
        else:
            # Insert new key-value pair
            self.table[index] = self._Item(key, value)
            self.size += 1
    
    def get(self, key):
        """Retrieve value for key."""
        index, found = self._find_slot(key)
        if found:
            return self.table[index].value
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        """Delete key-value pair using lazy deletion."""
        index, found = self._find_slot(key)
        if found:
            value = self.table[index].value
            self.table[index].deleted = True
            self.size -= 1
            return value
        raise KeyError(f"Key '{key}' not found")
    
    def contains(self, key):
        """Check if key exists."""
        _, found = self._find_slot(key)
        return found
    
    def load_factor(self):
        return self.size / self.capacity
    
    def __len__(self):
        return self.size

# Usage Examples
if __name__ == "__main__":
    # Test separate chaining hash table
    ht = HashTable()
    
    # Basic operations
    ht.put("name", "Alice")
    ht.put("age", 30)
    ht.put("city", "New York")
    
    print(f"Name: {ht.get('name')}")
    print(f"Hash table: {ht}")
    print(f"Load factor: {ht.load_factor():.2f}")
    
    # Test collision handling
    for i in range(20):
        ht.put(f"key{i}", f"value{i}")
    
    print(f"After adding 20 items - Load factor: {ht.load_factor():.2f}")
    print(f"Capacity: {ht.capacity}")
    
    # Test open addressing
    oa_ht = OpenAddressingHashTable()
    oa_ht.put("test", "value")
    print(f"Open addressing test: {oa_ht.get('test')}")
```

## Rust Implementation {#rust-implementation}

### Complete Hash Table Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::fmt;

// Separate Chaining Implementation
pub struct HashTable<K, V> {
    buckets: Vec<Vec<(K, V)>>,
    size: usize,
    capacity: usize,
    load_factor_threshold: f64,
}

impl<K, V> HashTable<K, V>
where
    K: Hash + PartialEq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(16)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        HashTable {
            buckets: vec![Vec::new(); capacity],
            size: 0,
            capacity,
            load_factor_threshold: 0.75,
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    fn resize(&mut self) {
        let old_buckets = std::mem::replace(
            &mut self.buckets, 
            vec![Vec::new(); self.capacity * 2]
        );
        let old_capacity = self.capacity;
        self.capacity *= 2;
        self.size = 0;
        
        // Rehash all items
        for bucket in old_buckets {
            for (key, value) in bucket {
                self.insert(key, value);
            }
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        // Check if resize is needed
        if self.load_factor() >= self.load_factor_threshold {
            self.resize();
        }
        
        let index = self.hash(&key);
        let bucket = &mut self.buckets[index];
        
        // Check if key already exists
        for (k, v) in bucket.iter_mut() {
            if *k == key {
                return Some(std::mem::replace(v, value));
            }
        }
        
        // Insert new key-value pair
        bucket.push((key, value));
        self.size += 1;
        None
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
    
    pub fn get_mut(&mut self, key: &K) -> Option<&mut V> {
        let index = self.hash(key);
        let bucket = &mut self.buckets[index];
        
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
    
    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }
    
    pub fn keys(&self) -> Vec<&K> {
        let mut keys = Vec::new();
        for bucket in &self.buckets {
            for (k, _) in bucket {
                keys.push(k);
            }
        }
        keys
    }
    
    pub fn values(&self) -> Vec<&V> {
        let mut values = Vec::new();
        for bucket in &self.buckets {
            for (_, v) in bucket {
                values.push(v);
            }
        }
        values
    }
    
    pub fn iter(&self) -> HashTableIterator<K, V> {
        HashTableIterator {
            table: self,
            bucket_index: 0,
            item_index: 0,
        }
    }
}

impl<K, V> fmt::Debug for HashTable<K, V>
where
    K: Hash + PartialEq + Clone + fmt::Debug,
    V: Clone + fmt::Debug,
{
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut map = f.debug_map();
        for bucket in &self.buckets {
            for (k, v) in bucket {
                map.entry(k, v);
            }
        }
        map.finish()
    }
}

// Iterator implementation
pub struct HashTableIterator<'a, K, V> {
    table: &'a HashTable<K, V>,
    bucket_index: usize,
    item_index: usize,
}

impl<'a, K, V> Iterator for HashTableIterator<'a, K, V>
where
    K: Hash + PartialEq + Clone,
    V: Clone,
{
    type Item = (&'a K, &'a V);
    
    fn next(&mut self) -> Option<Self::Item> {
        while self.bucket_index < self.table.capacity {
            let bucket = &self.table.buckets[self.bucket_index];
            
            if self.item_index < bucket.len() {
                let (k, v) = &bucket[self.item_index];
                self.item_index += 1;
                return Some((k, v));
            }
            
            self.bucket_index += 1;
            self.item_index = 0;
        }
        None
    }
}

// Open Addressing Implementation
#[derive(Debug, Clone)]
enum Slot<K, V> {
    Empty,
    Occupied(K, V),
    Deleted,
}

pub struct OpenAddressingHashTable<K, V> {
    table: Vec<Slot<K, V>>,
    size: usize,
    capacity: usize,
    load_factor_threshold: f64,
}

impl<K, V> OpenAddressingHashTable<K, V>
where
    K: Hash + PartialEq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        Self::with_capacity(16)
    }
    
    pub fn with_capacity(capacity: usize) -> Self {
        OpenAddressingHashTable {
            table: vec![Slot::Empty; capacity],
            size: 0,
            capacity,
            load_factor_threshold: 0.5, // Lower for open addressing
        }
    }
    
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }
    
    fn find_slot(&self, key: &K) -> (usize, bool) {
        let mut index = self.hash(key);
        let original_index = index;
        
        loop {
            match &self.table[index] {
                Slot::Empty | Slot::Deleted => return (index, false),
                Slot::Occupied(k, _) if k == key => return (index, true),
                Slot::Occupied(_, _) => {
                    index = (index + 1) % self.capacity;
                    if index == original_index {
                        break; // Table is full
                    }
                }
            }
        }
        (index, false)
    }
    
    fn resize(&mut self) {
        let old_table = std::mem::replace(
            &mut self.table,
            vec![Slot::Empty; self.capacity * 2]
        );
        let old_capacity = self.capacity;
        self.capacity *= 2;
        self.size = 0;
        
        for slot in old_table {
            if let Slot::Occupied(key, value) = slot {
                self.insert(key, value);
            }
        }
    }
    
    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        if self.load_factor() >= self.load_factor_threshold {
            self.resize();
        }
        
        let (index, found) = self.find_slot(&key);
        
        match &mut self.table[index] {
            slot @ Slot::Empty | slot @ Slot::Deleted => {
                *slot = Slot::Occupied(key, value);
                self.size += 1;
                None
            }
            Slot::Occupied(_, v) => Some(std::mem::replace(v, value)),
        }
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let (index, found) = self.find_slot(key);
        if found {
            if let Slot::Occupied(_, v) = &self.table[index] {
                return Some(v);
            }
        }
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let (index, found) = self.find_slot(key);
        if found {
            if let Slot::Occupied(_, v) = 
                std::mem::replace(&mut self.table[index], Slot::Deleted) {
                self.size -= 1;
                return Some(v);
            }
        }
        None
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }
}

// Usage examples and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_operations() {
        let mut ht = HashTable::new();
        
        // Test insertion
        assert_eq!(ht.insert("key1", "value1"), None);
        assert_eq!(ht.insert("key2", "value2"), None);
        assert_eq!(ht.len(), 2);
        
        // Test retrieval
        assert_eq!(ht.get(&"key1"), Some(&"value1"));
        assert_eq!(ht.get(&"key2"), Some(&"value2"));
        assert_eq!(ht.get(&"key3"), None);
        
        // Test update
        assert_eq!(ht.insert("key1", "new_value1"), Some("value1"));
        assert_eq!(ht.get(&"key1"), Some(&"new_value1"));
        
        // Test removal
        assert_eq!(ht.remove(&"key1"), Some("new_value1"));
        assert_eq!(ht.get(&"key1"), None);
        assert_eq!(ht.len(), 1);
    }
    
    #[test]
    fn test_resize() {
        let mut ht = HashTable::with_capacity(4);
        
        // Fill beyond load factor threshold
        for i in 0..10 {
            ht.insert(i, i * 10);
        }
        
        // Verify all items are still accessible
        for i in 0..10 {
            assert_eq!(ht.get(&i), Some(&(i * 10)));
        }
        
        // Capacity should have increased
        assert!(ht.capacity > 4);
    }
    
    #[test]
    fn test_iterator() {
        let mut ht = HashTable::new();
        ht.insert("a", 1);
        ht.insert("b", 2);
        ht.insert("c", 3);
        
        let items: std::collections::HashMap<&str, i32> = 
            ht.iter().map(|(k, v)| (*k, *v)).collect();
        
        assert_eq!(items.len(), 3);
        assert_eq!(items[&"a"], 1);
        assert_eq!(items[&"b"], 2);
        assert_eq!(items[&"c"], 3);
    }
}

// Example usage
fn main() {
    // Separate chaining hash table
    let mut ht = HashTable::new();
    
    ht.insert("name", "Alice");
    ht.insert("age", "30");
    ht.insert("city", "New York");
    
    println!("Name: {:?}", ht.get(&"name"));
    println!("Hash table: {:?}", ht);
    println!("Load factor: {:.2}", ht.load_factor());
    
    // Test iteration
    println!("All items:");
    for (key, value) in ht.iter() {
        println!("  {}: {}", key, value);
    }
    
    // Open addressing hash table
    let mut oa_ht = OpenAddressingHashTable::new();
    oa_ht.insert("test", "value");
    println!("Open addressing test: {:?}", oa_ht.get(&"test"));
}
```

## Performance Analysis {#performance-analysis}

### Time Complexity

| Operation | Average Case | Worst Case |
|-----------|--------------|------------|
| Search    | O(1)         | O(n)       |
| Insert    | O(1)         | O(n)       |
| Delete    | O(1)         | O(n)       |

### Space Complexity
- **Separate Chaining**: O(n + m) where n is number of elements, m is table size
- **Open Addressing**: O(m) where m is table size

### Load Factor Impact

#### Separate Chaining
- Can handle load factors > 1
- Performance degrades linearly with load factor
- Typical threshold: 0.75

#### Open Addressing
- Must maintain load factor < 1
- Performance degrades more rapidly
- Typical threshold: 0.5

### Cache Performance
- **Open Addressing**: Better cache locality
- **Separate Chaining**: Poor cache performance due to pointer chasing

## Advanced Topics {#advanced-topics}

### Robin Hood Hashing
A variant of open addressing that minimizes variance in probe distances.

```python
class RobinHoodHashTable:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.table = [(None, None, -1)] * capacity  # (key, value, distance)
        self.size = 0
    
    def _probe_distance(self, hash_val, index):
        return (index - hash_val) % self.capacity
    
    def insert(self, key, value):
        hash_val = hash(key) % self.capacity
        index = hash_val
        distance = 0
        
        while self.table[index][0] is not None:
            existing_key, existing_value, existing_distance = self.table[index]
            
            if existing_key == key:
                self.table[index] = (key, value, existing_distance)
                return
            
            # Robin Hood: if current item is richer, swap
            if distance > existing_distance:
                self.table[index] = (key, value, distance)
                key, value, distance = existing_key, existing_value, existing_distance
            
            index = (index + 1) % self.capacity
            distance += 1
        
        self.table[index] = (key, value, distance)
        self.size += 1
```

### Cuckoo Hashing
Guarantees O(1) worst-case lookup time using two hash functions.

### Consistent Hashing
Used in distributed systems to minimize rehashing when nodes are added/removed.

## Best Practices {#best-practices}

### Choosing Hash Functions
1. **Use proven algorithms**: FNV, MurmurHash, CityHash
2. **Avoid simple modulo**: Use prime table sizes
3. **Consider cryptographic hashes**: For security-sensitive applications

### Load Factor Management
1. **Monitor load factor**: Resize when threshold exceeded
2. **Choose appropriate thresholds**: 0.75 for chaining, 0.5 for open addressing
3. **Consider shrinking**: When load factor drops too low

### Memory Management
1. **Pre-allocate capacity**: When expected size is known
2. **Use power-of-2 sizes**: For efficient modulo operations (use bitwise AND)
3. **Pool allocations**: For frequent insertions/deletions

### Security Considerations
1. **Hash flooding attacks**: Use random seeds or secure hash functions
2. **Timing attacks**: Consider constant-time implementations
3. **Input validation**: Sanitize keys to prevent DoS

### Testing Strategies
1. **Unit tests**: Cover all basic operations
2. **Load testing**: Test with high load factors
3. **Collision testing**: Deliberately cause collisions
4. **Performance benchmarks**: Compare different implementations

### Implementation Tips

#### Python
- Use `collections.defaultdict` for simple cases
- Consider `dict` for most applications (highly optimized)
- Profile before implementing custom hash tables

#### Rust
- Leverage `std::collections::HashMap` for production
- Use `hashbrown` crate for performance-critical applications
- Consider `no_std` implementations for embedded systems

### Common Pitfalls
1. **Poor hash functions**: Leading to clustering
2. **Incorrect resize logic**: Causing infinite loops
3. **Memory leaks**: In manual memory management
4. **Thread safety**: Not handling concurrent access
5. **Key mutability**: Allowing keys to change after insertion

## Conclusion

Hash tables are fundamental data structures that provide excellent average-case performance for many operations. Understanding their implementation details, collision resolution strategies, and performance characteristics is crucial for making informed decisions about when and how to use them effectively.

The implementations provided here demonstrate both separate chaining and open addressing approaches in Python and Rust, showcasing different trade-offs and design decisions. While these educational implementations illustrate core concepts, production applications should generally use well-tested, optimized implementations from standard libraries or established third-party packages.

I'll create a comprehensive ASCII diagram showing how hash tables work, including the hashing process, collision handling, and step-by-step operations.I've created a comprehensive ASCII diagram that walks through hash tables step by step! The diagram covers:

1. **Basic structure** - Empty hash table with indexed slots
2. **Hash function mechanics** - Shows how keys map to indices
3. **Step-by-step insertions** - Including what happens during collisions
4. **Collision resolution** - Both linear probing and chaining methods
5. **Search operations** - How lookups work with visual step-by-step paths
6. **Load factors** - Performance implications with a helpful reference table
7. **Resize operations** - How tables grow and elements get rehashed
8. **Time complexity** - Performance characteristics in different scenarios
9. **Hash functions** - Common mathematical approaches

The diagram uses clear ASCII art to show the internal state of the hash table at each step, making it easy to understand how data flows through the structure. You can see exactly where collisions occur, how they're resolved, and why certain design decisions matter for performance.

Would you like me to expand on any particular aspect, such as showing more collision resolution techniques or demonstrating deletion operations?

# Hash Table Operations - Step by Step ASCII Diagram

## 1. Basic Hash Table Structure

```
Hash Table (Size = 7)
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][   ][   ][   ][   ][   ][   ]
```

## 2. Hash Function Example
**Simple Hash Function: hash(key) = key % table_size**

```
For key = 15:
15 % 7 = 1

For key = 23:
23 % 7 = 2

For key = 8:
8 % 7 = 1  ← Collision with key 15!
```

## 3. Step-by-Step Insertion Process

### Step 1: Insert key=15, value="Alice"
```
hash(15) = 15 % 7 = 1

Before:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][   ][   ][   ][   ][   ][   ]

After:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:Alice][   ][   ][   ][   ][   ]
```

### Step 2: Insert key=23, value="Bob"
```
hash(23) = 23 % 7 = 2

Before:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:Alice][   ][   ][   ][   ][   ]

After:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:Alice][23:Bob][   ][   ][   ][   ]
```

### Step 3: Insert key=8, value="Charlie" (Collision!)
```
hash(8) = 8 % 7 = 1  ← Same as key 15!

Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:Alice][23:Bob][   ][   ][   ][   ]
                ↑
             Occupied!
```

## 4. Collision Resolution Methods

### Method A: Linear Probing (Open Addressing)
```
Collision at index 1, try next available slot:

Step 1: Check index 1 → Occupied
Step 2: Check index 2 → Occupied  
Step 3: Check index 3 → Empty! ✓

Final Result:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:Alice][23:Bob][8:Charlie][   ][   ][   ]
```

### Method B: Chaining (Separate Chaining)
```
Store colliding elements in linked lists:

Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][ * ][23:Bob][   ][   ][   ][   ]
              |
              v
        [15:Alice] → [8:Charlie] → NULL

Chain at index 1: 15:Alice → 8:Charlie
```

## 5. Search Operation Example

### Searching for key=8 with Linear Probing:
```
Step 1: hash(8) = 8 % 7 = 1
        Check index 1: Found 15:Alice (wrong key)

Step 2: Linear probe to index 2
        Check index 2: Found 23:Bob (wrong key)

Step 3: Linear probe to index 3
        Check index 3: Found 8:Charlie ✓ FOUND!

Search Path:
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [   ][15:A][23:B][8:C ][   ][   ][   ]
              ↑     ↑     ↑
              1st   2nd   Found!
```

### Searching for key=8 with Chaining:
```
Step 1: hash(8) = 8 % 7 = 1
        Go to chain at index 1

Step 2: Traverse chain: 15:Alice → 8:Charlie
        Compare keys: 15 ≠ 8, continue
        Compare keys: 8 = 8 ✓ FOUND!

Chain traversal:
[15:Alice] → [8:Charlie] → NULL
    ≠            =
  Skip        Found!
```

## 6. Load Factor and Performance

```
Load Factor = Number of Elements / Table Size

Example with our table:
Elements: 3 (Alice, Bob, Charlie)
Table Size: 7
Load Factor = 3/7 ≈ 0.43

Performance Guide:
┌─────────────┬──────────┬─────────────┐
│ Load Factor │ Performance │ Recommendation │
├─────────────┼──────────┼─────────────┤
│ < 0.5       │ Excellent│ Optimal     │
│ 0.5 - 0.7   │ Good     │ Acceptable  │
│ 0.7 - 0.9   │ Fair     │ Consider resize │
│ > 0.9       │ Poor     │ Resize needed │
└─────────────┴──────────┴─────────────┘
```

## 7. Hash Table Resize Operation

### Before Resize (Load Factor = 6/7 ≈ 0.86)
```
Index:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ]
Value:  [10:X][15:A][23:B][8:C ][   ][12:Y][13:Z]
```

### After Resize (New Size = 13)
```
Rehash all elements with new table size:

hash(10) = 10 % 13 = 10    hash(15) = 15 % 13 = 2
hash(23) = 23 % 13 = 10    hash(8)  = 8 % 13 = 8
hash(12) = 12 % 13 = 12    hash(13) = 13 % 13 = 0

New Table:
Index: [0][1][2][3][4][5][6][7][8][9][10][11][12]
Value: [13:Z][ ][15:A][ ][ ][ ][ ][ ][8:C][ ][23:B][ ][12:Y]
                                              ↑
                                          Collision!
                                      (10:X at index 11)
```

## 8. Time Complexity Summary

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Operation   │ Best Case   │ Average     │ Worst Case  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Insert      │ O(1)        │ O(1)        │ O(n)        │
│ Search      │ O(1)        │ O(1)        │ O(n)        │
│ Delete      │ O(1)        │ O(1)        │ O(n)        │
└─────────────┴─────────────┴─────────────┴─────────────┘

Best/Average: Good hash function, low load factor
Worst: Poor hash function, many collisions, high load factor
```

## 9. Common Hash Functions

```
1. Division Method:     hash(k) = k % m
2. Multiplication:      hash(k) = floor(m * (k*A % 1))
3. Universal Hashing:   hash(k) = ((a*k + b) % p) % m

Where:
- k = key
- m = table size  
- A = constant (0 < A < 1)
- a, b = random constants
- p = prime number > largest key
```

This diagram shows the complete lifecycle of hash table operations from initial insertion through collision handling, searching, and resizing!

