# Comprehensive Guide to Advanced Hashes in Rust & Python

## Table of Contents
1. [Hash Fundamentals](#hash-fundamentals)
2. [Rust Implementation](#rust-implementation)
3. [Python Implementation](#python-implementation)
4. [Comparisons & Best Practices](#comparisons)

---

## Hash Fundamentals

### What is a Hash?
A hash is a data structure that maps keys to values using a hash function. It provides O(1) average-case lookup, insertion, and deletion.

**Key Concepts:**
- **Hash Function**: Converts keys into array indices
- **Collision Resolution**: Handles cases where multiple keys hash to the same index
- **Load Factor**: Ratio of elements to buckets (affects performance)

---

## Rust Implementation

### 1. Using Built-in HashMap

```rust
use std::collections::HashMap;

fn using_hashmap() {
    // Create a new HashMap
    let mut scores: HashMap<String, i32> = HashMap::new();
    
    // Insert values
    scores.insert(String::from("Blue"), 10);
    scores.insert(String::from("Red"), 50);
    
    // Access values
    let team_name = String::from("Blue");
    let score = scores.get(&team_name);
    
    match score {
        Some(s) => println!("Score: {}", s),
        None => println!("Team not found"),
    }
    
    // Iterate over key-value pairs
    for (key, value) in &scores {
        println!("{}: {}", key, value);
    }
    
    // Update or insert
    scores.entry(String::from("Yellow")).or_insert(50);
    
    // Update based on old value
    let text = "hello world wonderful world";
    let mut map = HashMap::new();
    
    for word in text.split_whitespace() {
        let count = map.entry(word).or_insert(0);
        *count += 1;
    }
    
    println!("{:?}", map);
}
```

**Benefits of Using HashMap:**
- Type safety at compile time
- Memory safety guaranteed by Rust's ownership system
- No runtime overhead for bounds checking after compilation
- Thread-safe options available (Arc<Mutex<HashMap>>)

### 2. Custom Hash Implementation

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::mem;

const INITIAL_CAPACITY: usize = 16;
const LOAD_FACTOR: f64 = 0.75;

#[derive(Clone)]
struct Entry<K, V> {
    key: K,
    value: V,
    hash: u64,
}

pub struct CustomHashMap<K, V> {
    buckets: Vec<Vec<Entry<K, V>>>,
    size: usize,
}

impl<K, V> CustomHashMap<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new() -> Self {
        CustomHashMap {
            buckets: vec![Vec::new(); INITIAL_CAPACITY],
            size: 0,
        }
    }
    
    fn hash_key(&self, key: &K) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }
    
    fn bucket_index(&self, hash: u64) -> usize {
        (hash as usize) % self.buckets.len()
    }
    
    pub fn insert(&mut self, key: K, value: V) {
        if self.load_factor() > LOAD_FACTOR {
            self.resize();
        }
        
        let hash = self.hash_key(&key);
        let index = self.bucket_index(hash);
        
        // Check if key exists and update
        for entry in &mut self.buckets[index] {
            if entry.hash == hash && entry.key == key {
                entry.value = value;
                return;
            }
        }
        
        // Insert new entry
        self.buckets[index].push(Entry { key, value, hash });
        self.size += 1;
    }
    
    pub fn get(&self, key: &K) -> Option<&V> {
        let hash = self.hash_key(key);
        let index = self.bucket_index(hash);
        
        for entry in &self.buckets[index] {
            if entry.hash == hash && entry.key == *key {
                return Some(&entry.value);
            }
        }
        None
    }
    
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let hash = self.hash_key(key);
        let index = self.bucket_index(hash);
        
        if let Some(pos) = self.buckets[index]
            .iter()
            .position(|e| e.hash == hash && e.key == *key)
        {
            self.size -= 1;
            return Some(self.buckets[index].remove(pos).value);
        }
        None
    }
    
    fn load_factor(&self) -> f64 {
        self.size as f64 / self.buckets.len() as f64
    }
    
    fn resize(&mut self) {
        let new_capacity = self.buckets.len() * 2;
        let mut new_buckets = vec![Vec::new(); new_capacity];
        
        for bucket in &self.buckets {
            for entry in bucket {
                let index = (entry.hash as usize) % new_capacity;
                new_buckets[index].push(entry.clone());
            }
        }
        
        self.buckets = new_buckets;
    }
    
    pub fn len(&self) -> usize {
        self.size
    }
    
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}

// Example usage
fn custom_hashmap_example() {
    let mut map = CustomHashMap::new();
    
    map.insert("apple", 1);
    map.insert("banana", 2);
    map.insert("cherry", 3);
    
    if let Some(value) = map.get(&"banana") {
        println!("Found: {}", value);
    }
    
    map.remove(&"apple");
    println!("Size: {}", map.len());
}
```

### 3. Errors Without Using HashMap

```rust
// ❌ INCORRECT: Using Vec for key-value lookups
fn without_hashmap_bad() {
    let mut data: Vec<(String, i32)> = Vec::new();
    
    // O(n) insertion (need to check for duplicates)
    let key = String::from("test");
    let mut found = false;
    for (k, v) in data.iter_mut() {
        if k == &key {
            *v = 100;
            found = true;
            break;
        }
    }
    if !found {
        data.push((key, 100));
    }
    
    // O(n) lookup - very slow for large datasets
    let search_key = String::from("test");
    for (k, v) in &data {
        if k == &search_key {
            println!("Found: {}", v);
            break;
        }
    }
}

// ⚠️ WARNING: No compile-time errors, but performance issues!
// - Linear search instead of O(1) lookup
// - Memory not optimized
// - No hash-based indexing
```

### 4. Common Rust Hash Errors

```rust
use std::collections::HashMap;

fn common_errors() {
    let mut map = HashMap::new();
    map.insert("key", 42);
    
    // ❌ ERROR: Borrow checker violation
    // let value = map.get("key").unwrap();
    // map.insert("key2", 100); // Can't borrow mutably while immutably borrowed
    
    // ✅ CORRECT: Drop the reference first
    {
        let value = map.get("key").unwrap();
        println!("{}", value);
    }
    map.insert("key2", 100);
    
    // ❌ ERROR: Key doesn't implement Hash or Eq
    // struct BadKey { x: f64 }
    // let mut bad_map: HashMap<BadKey, i32> = HashMap::new(); // Won't compile
    
    // ✅ CORRECT: Implement Hash and Eq
    #[derive(Hash, Eq, PartialEq)]
    struct GoodKey { x: i32 }
    let mut good_map: HashMap<GoodKey, i32> = HashMap::new();
    good_map.insert(GoodKey { x: 1 }, 100);
}
```

---

## Python Implementation

### 1. Using Built-in Dictionary

```python
def using_dict():
    # Create a dictionary
    scores = {"Blue": 10, "Red": 50}
    
    # Access values
    score = scores.get("Blue")
    print(f"Score: {score}")
    
    # Safe access with default
    yellow_score = scores.get("Yellow", 0)
    
    # Update or insert
    scores["Yellow"] = 50
    
    # Update based on old value
    text = "hello world wonderful world"
    word_count = {}
    
    for word in text.split():
        word_count[word] = word_count.get(word, 0) + 1
    
    print(word_count)
    
    # Using defaultdict for cleaner code
    from collections import defaultdict
    word_count2 = defaultdict(int)
    
    for word in text.split():
        word_count2[word] += 1
    
    print(dict(word_count2))
    
    # Using Counter (specialized dict for counting)
    from collections import Counter
    word_count3 = Counter(text.split())
    print(word_count3)
```

**Benefits of Using Dict:**
- Dynamic typing (flexible but less safe)
- Built-in optimizations in CPython
- Rich standard library (defaultdict, Counter, OrderedDict)
- Easy to use with minimal boilerplate

### 2. Custom Hash Implementation

```python
class Entry:
    def __init__(self, key, value, hash_value):
        self.key = key
        self.value = value
        self.hash = hash_value
        self.next = None

class CustomHashMap:
    INITIAL_CAPACITY = 16
    LOAD_FACTOR = 0.75
    
    def __init__(self):
        self.buckets = [None] * self.INITIAL_CAPACITY
        self.size = 0
    
    def _hash_key(self, key):
        """Generate hash for key"""
        return hash(key)
    
    def _bucket_index(self, hash_value):
        """Get bucket index from hash"""
        return hash_value % len(self.buckets)
    
    def insert(self, key, value):
        """Insert or update key-value pair"""
        if self._load_factor() > self.LOAD_FACTOR:
            self._resize()
        
        hash_value = self._hash_key(key)
        index = self._bucket_index(hash_value)
        
        # Check if key exists and update
        current = self.buckets[index]
        while current:
            if current.hash == hash_value and current.key == key:
                current.value = value
                return
            current = current.next
        
        # Insert new entry at the beginning of the chain
        new_entry = Entry(key, value, hash_value)
        new_entry.next = self.buckets[index]
        self.buckets[index] = new_entry
        self.size += 1
    
    def get(self, key):
        """Get value by key"""
        hash_value = self._hash_key(key)
        index = self._bucket_index(hash_value)
        
        current = self.buckets[index]
        while current:
            if current.hash == hash_value and current.key == key:
                return current.value
            current = current.next
        
        return None
    
    def remove(self, key):
        """Remove key-value pair"""
        hash_value = self._hash_key(key)
        index = self._bucket_index(hash_value)
        
        current = self.buckets[index]
        prev = None
        
        while current:
            if current.hash == hash_value and current.key == key:
                if prev:
                    prev.next = current.next
                else:
                    self.buckets[index] = current.next
                self.size -= 1
                return current.value
            prev = current
            current = current.next
        
        return None
    
    def _load_factor(self):
        """Calculate current load factor"""
        return self.size / len(self.buckets)
    
    def _resize(self):
        """Resize the hash table"""
        old_buckets = self.buckets
        self.buckets = [None] * (len(old_buckets) * 2)
        self.size = 0
        
        for bucket in old_buckets:
            current = bucket
            while current:
                self.insert(current.key, current.value)
                current = current.next
    
    def __len__(self):
        return self.size
    
    def __contains__(self, key):
        return self.get(key) is not None
    
    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key, value):
        self.insert(key, value)
    
    def __delitem__(self, key):
        value = self.remove(key)
        if value is None:
            raise KeyError(key)

# Example usage
def custom_hashmap_example():
    map = CustomHashMap()
    
    map.insert("apple", 1)
    map.insert("banana", 2)
    map.insert("cherry", 3)
    
    print(f"Found: {map.get('banana')}")
    
    map.remove("apple")
    print(f"Size: {len(map)}")
    
    # Using dict-like syntax
    map["date"] = 4
    print(f"Date: {map['date']}")
    print(f"Contains cherry: {'cherry' in map}")
```

### 3. Errors Without Using Dict

```python
# ❌ INCORRECT: Using list of tuples for key-value lookups
def without_dict_bad():
    data = []
    
    # O(n) insertion (need to check for duplicates)
    key = "test"
    found = False
    for i, (k, v) in enumerate(data):
        if k == key:
            data[i] = (key, 100)
            found = True
            break
    if not found:
        data.append((key, 100))
    
    # O(n) lookup - very slow for large datasets
    search_key = "test"
    for k, v in data:
        if k == search_key:
            print(f"Found: {v}")
            break

# ⚠️ WARNING: No errors, but severe performance issues!
# - Linear search O(n) instead of O(1) lookup
# - Inefficient memory usage
# - No built-in hash optimization
```

### 4. Common Python Hash Errors

```python
def common_errors():
    # ❌ ERROR: Using mutable objects as keys
    try:
        bad_dict = {[1, 2, 3]: "value"}  # TypeError: unhashable type: 'list'
    except TypeError as e:
        print(f"Error: {e}")
    
    # ✅ CORRECT: Use immutable objects
    good_dict = {(1, 2, 3): "value"}  # Tuples are hashable
    
    # ❌ ERROR: KeyError when accessing non-existent key
    scores = {"Blue": 10}
    try:
        score = scores["Red"]  # KeyError: 'Red'
    except KeyError as e:
        print(f"Error: {e}")
    
    # ✅ CORRECT: Use get() with default value
    score = scores.get("Red", 0)
    print(f"Red score: {score}")
    
    # ❌ WARNING: Modifying dict during iteration
    data = {"a": 1, "b": 2, "c": 3}
    try:
        for key in data:
            if key == "b":
                del data[key]  # RuntimeError in Python 3.8+
    except RuntimeError as e:
        print(f"Error: {e}")
    
    # ✅ CORRECT: Iterate over a copy
    data = {"a": 1, "b": 2, "c": 3}
    for key in list(data.keys()):
        if key == "b":
            del data[key]
    
    # ❌ ERROR: Custom class without __hash__ and __eq__
    class BadKey:
        def __init__(self, x):
            self.x = x
    
    # This works but uses identity hash (memory address)
    k1 = BadKey(1)
    k2 = BadKey(1)
    test_dict = {k1: "value1"}
    print(k2 in test_dict)  # False (different objects)
    
    # ✅ CORRECT: Implement __hash__ and __eq__
    class GoodKey:
        def __init__(self, x):
            self.x = x
        
        def __hash__(self):
            return hash(self.x)
        
        def __eq__(self, other):
            return isinstance(other, GoodKey) and self.x == other.x
    
    k1 = GoodKey(1)
    k2 = GoodKey(1)
    test_dict = {k1: "value1"}
    print(k2 in test_dict)  # True (same hash and equality)
```

---

## Comparisons & Best Practices

### Performance Comparison

#### Rust HashMap vs Vec
```rust
use std::collections::HashMap;
use std::time::Instant;

fn performance_comparison() {
    let n = 100_000;
    
    // HashMap: O(1) average lookup
    let start = Instant::now();
    let mut map = HashMap::new();
    for i in 0..n {
        map.insert(i, i * 2);
    }
    for i in 0..n {
        let _ = map.get(&i);
    }
    let duration = start.elapsed();
    println!("HashMap: {:?}", duration);
    
    // Vec: O(n) lookup
    let start = Instant::now();
    let mut vec: Vec<(i32, i32)> = Vec::new();
    for i in 0..n {
        vec.push((i, i * 2));
    }
    for i in 0..n {
        let _ = vec.iter().find(|(k, _)| *k == i);
    }
    let duration = start.elapsed();
    println!("Vec: {:?}", duration);
}
```

#### Python Dict vs List
```python
import time

def performance_comparison():
    n = 100_000
    
    # Dict: O(1) average lookup
    start = time.time()
    d = {}
    for i in range(n):
        d[i] = i * 2
    for i in range(n):
        _ = d.get(i)
    print(f"Dict: {time.time() - start:.4f}s")
    
    # List: O(n) lookup
    start = time.time()
    lst = []
    for i in range(n):
        lst.append((i, i * 2))
    for i in range(n):
        _ = next((v for k, v in lst if k == i), None)
    print(f"List: {time.time() - start:.4f}s")
```

### Control & Safety Comparison

| Feature | Rust HashMap | Python Dict |
|---------|-------------|-------------|
| Type Safety | Compile-time | Runtime |
| Memory Safety | Guaranteed | GC managed |
| Null Safety | Option<T> | None checks |
| Performance | Zero-cost abstractions | Interpreted overhead |
| Concurrency | Thread-safe options | GIL limitations |
| Flexibility | Strict typing | Dynamic typing |

### When to Use Built-in vs Custom

**Use Built-in (HashMap/Dict):**
- Production code (99% of cases)
- Standard use cases
- Need reliability and testing
- Want optimal performance

**Use Custom Implementation:**
- Learning purposes
- Special requirements (custom hashing)
- Embedded systems (Rust)
- Algorithm research
- Interview preparation

### Best Practices

#### Rust
```rust
use std::collections::HashMap;

fn best_practices() {
    // 1. Use with_capacity for known sizes
    let mut map = HashMap::with_capacity(100);
    
    // 2. Use entry API for efficient updates
    map.entry("key").or_insert(0);
    *map.entry("key").or_insert(0) += 1;
    
    // 3. Use references when possible
    let key = String::from("test");
    map.insert(key.clone(), 42);
    if let Some(value) = map.get(&key) {
        println!("{}", value);
    }
    
    // 4. Implement Hash and Eq for custom keys
    #[derive(Hash, Eq, PartialEq)]
    struct CustomKey {
        id: u64,
    }
}
```

#### Python
```python
from collections import defaultdict, Counter

def best_practices():
    # 1. Use get() with defaults
    scores = {"Blue": 10}
    score = scores.get("Red", 0)
    
    # 2. Use defaultdict for automatic initialization
    word_count = defaultdict(int)
    for word in ["hello", "world", "hello"]:
        word_count[word] += 1
    
    # 3. Use Counter for counting
    counts = Counter(["a", "b", "a", "c", "b", "a"])
    
    # 4. Use dict comprehensions
    squared = {x: x**2 for x in range(10)}
    
    # 5. Implement __hash__ and __eq__ for custom keys
    class CustomKey:
        def __init__(self, id):
            self.id = id
        
        def __hash__(self):
            return hash(self.id)
        
        def __eq__(self, other):
            return isinstance(other, CustomKey) and self.id == other.id
```

### Summary

**Rust Benefits:**
- Compile-time guarantees
- Zero runtime overhead
- Memory safety without GC
- Fearless concurrency

**Python Benefits:**
- Rapid development
- Dynamic flexibility
- Rich standard library
- Easier prototyping

Both languages provide excellent hash table implementations. Choose based on your requirements: Rust for systems programming and performance-critical applications, Python for rapid development and scripting.

I'll create a comprehensive guide to advanced hash implementations in both Rust and Python, covering hash tables, hash functions, and common patterns.I've created a comprehensive guide covering advanced hash implementations in both Rust and Python. Here's what's included:

## Key Highlights:

### **Rust Section:**
- **Built-in HashMap usage** with proper ownership patterns
- **Custom hash table implementation** with separate chaining
- **Common errors** like borrow checker violations and missing trait implementations
- **Performance optimizations** using entry API and capacity hints

### **Python Section:**
- **Built-in dict, defaultdict, and Counter** usage
- **Custom hash table** with linked list collision resolution
- **Common pitfalls** like unhashable types and KeyError handling
- **Best practices** for safe key access and iteration

### **Key Differences:**

**Control & Safety:**
- **Rust**: Compile-time type safety, ownership prevents data races, Option<T> for null safety
- **Python**: Runtime checks, easier to write but more prone to runtime errors

**Performance:**
- **Rust**: Zero-cost abstractions, no GC pauses, predictable performance
- **Python**: GC overhead, GIL for threading, but faster development

**When NOT Using Hash Tables:**
- Vec/List lookups are O(n) instead of O(1)
- Causes severe performance degradation with large datasets
- No automatic resizing or load balancing

The guide includes complete working examples, error demonstrations, and performance comparisons to help you understand when and how to use hash tables effectively in both languages!
