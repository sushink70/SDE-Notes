# The Complete Hash Table Mastery Guide

*A systematic journey from first principles to expert implementation*

---

## Part I: Foundation — What is a Hash Table?

### The Core Problem

Imagine you have 1 million records. Using an array:
- **Search**: O(n) — scan through all elements
- **Insert**: O(1) if space available, O(n) if need to shift
- **Delete**: O(n) — find element, then shift everything

Using a sorted array with binary search:
- **Search**: O(log n) — better, but still slow at scale
- **Insert/Delete**: O(n) — must maintain sorted order

**The Vision**: What if we could achieve O(1) for all operations?

### The Hash Table Concept

A hash table is a data structure that maps **keys** to **values** using a **hash function**.

```
Key → Hash Function → Index → Value
```

**Flow Diagram**:
```
┌─────────────┐
│   Key: "A"  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Hash Function     │  h("A") = 1024
│   SHA, MD5, custom  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Index Calculation  │  1024 % 10 = 4
│     index = h % N   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Array[4] = value   │
└─────────────────────┘
```

**Key Terms Explained**:
- **Hash Function**: A function that converts a key (string, number, object) into an integer
- **Bucket**: A storage location in the underlying array
- **Load Factor**: ratio = (number of elements) / (array size)
- **Collision**: When two different keys hash to the same index
- **Rehashing**: Growing the array and redistributing all elements

---

## Part II: The Mathematics of Hashing

### Why Hashing Works: The Pigeonhole Principle

If you have `n` items and `m` buckets where `n > m`, at least one bucket must contain more than one item.

**Implication**: Collisions are inevitable unless your hash table is infinite (impossible).

### Properties of a Good Hash Function

1. **Deterministic**: Same key → always same hash value
2. **Uniform Distribution**: Keys spread evenly across buckets
3. **Fast Computation**: O(1) time complexity
4. **Avalanche Effect**: Small change in key → large change in hash

**Mathematical Example**:

For strings, a simple hash function:
```
h(s) = (s[0] * 31^(n-1) + s[1] * 31^(n-2) + ... + s[n-1]) mod table_size
```

Why 31? It's a prime number that creates good distribution and is fast (31 = 32 - 1, so compiler can optimize `31 * x` as `(x << 5) - x`).

### Load Factor and Performance

```
α (alpha) = n / m

where:
  n = number of elements
  m = table size
```

| Load Factor | Performance | Action |
|-------------|-------------|--------|
| α < 0.5 | Excellent | Normal ops |
| 0.5 ≤ α < 0.75 | Good | Monitor |
| α ≥ 0.75 | Degrading | Rehash |
| α > 1.0 | Poor | Must rehash |

---

## Part III: Collision Resolution Strategies

When two keys hash to the same index, we need a resolution strategy.

### Strategy 1: Separate Chaining

**Concept**: Each bucket holds a linked list (or other collection) of all elements that hash to that index.

**Visual**:
```
Array Index    Linked List
─────────────────────────────────
    0     →   ["key1", val1] → ["key7", val7] → null
    1     →   null
    2     →   ["key2", val2] → ["key3", val3] → ["key9", val9] → null
    3     →   ["key4", val4] → null
    4     →   null
```

**Analysis**:
- **Average Search**: O(1 + α) where α is load factor
- **Worst Case**: O(n) — all keys hash to same bucket
- **Space**: O(n) for elements + O(m) for array

**When to Use**: When you don't know how many elements you'll have

### Strategy 2: Open Addressing

**Concept**: All elements stored in the array itself. On collision, probe for next available slot.

#### 2a. Linear Probing

**Algorithm**:
```
index = hash(key) % size
if slot[index] occupied:
    index = (index + 1) % size  // try next slot
    repeat until empty slot found
```

**Visual**:
```
Insert "key1" → hash = 3:
[_, _, _, key1, _, _, _]
          ↑

Insert "key2" → hash = 3 (collision!):
[_, _, _, key1, key2, _, _]
          ↑     ↑
      collision  probed to next
```

**Problem: Primary Clustering** — consecutive occupied slots form clusters, increasing probe length.

#### 2b. Quadratic Probing

**Algorithm**:
```
index = (hash(key) + i²) % size
where i = 0, 1, 2, 3, ...
```

Instead of +1, +2, +3... we use +0, +1, +4, +9, +16...

**Reduces primary clustering** but can still cause **secondary clustering** (keys with same hash follow same probe sequence).

#### 2c. Double Hashing

**Algorithm**:
```
index = (hash1(key) + i * hash2(key)) % size
where i = 0, 1, 2, 3, ...
```

Use **two independent hash functions**. This eliminates clustering.

**Requirements**:
- hash2(key) must **never** return 0
- hash2(key) and size should be **relatively prime** (GCD = 1)

**Example**:
```rust
hash1(key) = key % size
hash2(key) = 1 + (key % (size - 1))
```

---

## Part IV: Rust Implementation — From Scratch

### Level 1: Basic Hash Table with Chaining

```rust
use std::collections::LinkedList;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

/// A hash table entry: key-value pair
#[derive(Debug, Clone)]
struct Entry<K, V> {
    key: K,
    value: V,
}

/// Hash table structure with separate chaining
pub struct HashTable<K, V> {
    buckets: Vec<LinkedList<Entry<K, V>>>,
    size: usize,      // number of elements
    capacity: usize,  // number of buckets
}

impl<K, V> HashTable<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    /// Create new hash table with given capacity
    pub fn new(capacity: usize) -> Self {
        let mut buckets = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            buckets.push(LinkedList::new());
        }
        
        HashTable {
            buckets,
            size: 0,
            capacity,
        }
    }

    /// Hash function: converts key to bucket index
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        let hash_value = hasher.finish();
        
        // Modulo to fit within capacity
        (hash_value as usize) % self.capacity
    }

    /// Get current load factor
    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }

    /// Insert key-value pair
    pub fn insert(&mut self, key: K, value: V) {
        let index = self.hash(&key);
        
        // Check if key already exists
        for entry in &mut self.buckets[index] {
            if entry.key == key {
                entry.value = value; // Update existing
                return;
            }
        }
        
        // Add new entry
        self.buckets[index].push_back(Entry { key, value });
        self.size += 1;
        
        // Check if rehashing needed
        if self.load_factor() > 0.75 {
            self.rehash();
        }
    }

    /// Search for a key
    pub fn get(&self, key: &K) -> Option<&V> {
        let index = self.hash(key);
        
        for entry in &self.buckets[index] {
            if entry.key == *key {
                return Some(&entry.value);
            }
        }
        
        None
    }

    /// Delete a key
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = self.hash(key);
        
        // Find and remove the entry
        let mut found_index = None;
        for (i, entry) in self.buckets[index].iter().enumerate() {
            if entry.key == *key {
                found_index = Some(i);
                break;
            }
        }
        
        if let Some(i) = found_index {
            let mut split_list = self.buckets[index].split_off(i);
            let entry = split_list.pop_front().unwrap();
            self.buckets[index].append(&mut split_list);
            self.size -= 1;
            return Some(entry.value);
        }
        
        None
    }

    /// Rehash: double capacity and redistribute all elements
    fn rehash(&mut self) {
        let new_capacity = self.capacity * 2;
        let mut new_buckets = Vec::with_capacity(new_capacity);
        
        for _ in 0..new_capacity {
            new_buckets.push(LinkedList::new());
        }
        
        // Redistribute all entries
        for bucket in &mut self.buckets {
            while let Some(entry) = bucket.pop_front() {
                let mut hasher = DefaultHasher::new();
                entry.key.hash(&mut hasher);
                let new_index = (hasher.finish() as usize) % new_capacity;
                new_buckets[new_index].push_back(entry);
            }
        }
        
        self.buckets = new_buckets;
        self.capacity = new_capacity;
    }

    /// Get table statistics
    pub fn stats(&self) -> TableStats {
        let mut max_chain = 0;
        let mut empty_buckets = 0;
        let mut total_chain_length = 0;
        
        for bucket in &self.buckets {
            let len = bucket.len();
            if len == 0 {
                empty_buckets += 1;
            }
            max_chain = max_chain.max(len);
            total_chain_length += len;
        }
        
        TableStats {
            size: self.size,
            capacity: self.capacity,
            load_factor: self.load_factor(),
            max_chain_length: max_chain,
            avg_chain_length: total_chain_length as f64 / self.capacity as f64,
            empty_buckets,
        }
    }
}

#[derive(Debug)]
pub struct TableStats {
    pub size: usize,
    pub capacity: usize,
    pub load_factor: f64,
    pub max_chain_length: usize,
    pub avg_chain_length: f64,
    pub empty_buckets: usize,
}

// Example usage and testing
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operations() {
        let mut table = HashTable::new(8);
        
        // Insert
        table.insert("apple", 100);
        table.insert("banana", 200);
        table.insert("cherry", 300);
        
        // Get
        assert_eq!(table.get(&"apple"), Some(&100));
        assert_eq!(table.get(&"banana"), Some(&200));
        assert_eq!(table.get(&"grape"), None);
        
        // Update
        table.insert("apple", 150);
        assert_eq!(table.get(&"apple"), Some(&150));
        
        // Remove
        assert_eq!(table.remove(&"banana"), Some(200));
        assert_eq!(table.get(&"banana"), None);
        
        println!("{:#?}", table.stats());
    }
}
```

**Key Design Decisions**:

1. **Generic Types**: `<K, V>` allows any key-value types
2. **Trait Bounds**: `K: Hash + Eq + Clone` ensures keys can be hashed and compared
3. **Separate Chaining**: Using `LinkedList` for simplicity (could use `Vec` for better cache locality)
4. **Automatic Rehashing**: Triggered when load factor exceeds 0.75

---

### Level 2: Open Addressing with Linear Probing

```rust
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;
use std::mem;

/// Bucket state for open addressing
#[derive(Debug, Clone)]
enum Bucket<K, V> {
    Empty,              // Never used
    Occupied(K, V),     // Currently in use
    Deleted,            // Was used, now deleted (tombstone)
}

pub struct OpenHashTable<K, V> {
    buckets: Vec<Bucket<K, V>>,
    size: usize,
    capacity: usize,
}

impl<K, V> OpenHashTable<K, V>
where
    K: Hash + Eq + Clone,
    V: Clone,
{
    pub fn new(capacity: usize) -> Self {
        let mut buckets = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            buckets.push(Bucket::Empty);
        }
        
        OpenHashTable {
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

    /// Linear probing: find next available slot
    fn probe(&self, key: &K) -> (usize, bool) {
        let mut index = self.hash(key);
        let mut first_deleted = None;
        
        for i in 0..self.capacity {
            let probe_index = (index + i) % self.capacity;
            
            match &self.buckets[probe_index] {
                Bucket::Empty => {
                    // Found empty slot
                    return (first_deleted.unwrap_or(probe_index), false);
                }
                Bucket::Occupied(k, _) if k == key => {
                    // Found existing key
                    return (probe_index, true);
                }
                Bucket::Deleted if first_deleted.is_none() => {
                    // Remember first deleted slot
                    first_deleted = Some(probe_index);
                }
                _ => continue,
            }
        }
        
        // Table is full
        (first_deleted.unwrap_or(index), false)
    }

    pub fn insert(&mut self, key: K, value: V) {
        if self.size >= self.capacity * 3 / 4 {
            self.rehash();
        }
        
        let (index, exists) = self.probe(&key);
        
        if exists {
            // Update existing
            self.buckets[index] = Bucket::Occupied(key, value);
        } else {
            // Insert new
            self.buckets[index] = Bucket::Occupied(key, value);
            self.size += 1;
        }
    }

    pub fn get(&self, key: &K) -> Option<&V> {
        let (index, exists) = self.probe(key);
        
        if exists {
            if let Bucket::Occupied(_, ref v) = self.buckets[index] {
                return Some(v);
            }
        }
        
        None
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        let (index, exists) = self.probe(key);
        
        if exists {
            let old_bucket = mem::replace(&mut self.buckets[index], Bucket::Deleted);
            if let Bucket::Occupied(_, v) = old_bucket {
                self.size -= 1;
                return Some(v);
            }
        }
        
        None
    }

    fn rehash(&mut self) {
        let new_capacity = self.capacity * 2;
        let mut new_table = OpenHashTable::new(new_capacity);
        
        for bucket in &self.buckets {
            if let Bucket::Occupied(ref k, ref v) = bucket {
                new_table.insert(k.clone(), v.clone());
            }
        }
        
        *self = new_table;
    }

    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }
}
```

**Critical Insight: The Tombstone Problem**

When we delete an entry, we can't just mark it as `Empty` because:
```
Insert "A" at index 5
Insert "B" → collision → goes to index 6
Delete "A" → if we mark index 5 as Empty
Search "B" → starts at 5, sees Empty, returns None (WRONG!)
```

Solution: Use **tombstones** (`Deleted` state). During search, we skip tombstones but stop at `Empty`.

---

## Part V: Go Implementation

### Go's Built-in Map

Go has a built-in hash table: `map[K]V`. Let's understand how it works internally, then build our own.

**Go's Map Implementation Details**:
- Uses **open addressing** with sophisticated hash function
- Buckets hold **8 key-value pairs** each
- Load factor threshold: **6.5 / 8 ≈ 0.8125**
- Grows to **2x buckets** when threshold exceeded

### Custom Hash Table in Go

```go
package hashtable

import (
    "fmt"
    "hash/fnv"
)

// Entry represents a key-value pair
type Entry[K comparable, V any] struct {
    Key   K
    Value V
}

// HashTable with separate chaining
type HashTable[K comparable, V any] struct {
    buckets  [][]*Entry[K, V]
    size     int
    capacity int
}

// NewHashTable creates a new hash table
func NewHashTable[K comparable, V any](capacity int) *HashTable[K, V] {
    buckets := make([][]*Entry[K, V], capacity)
    for i := range buckets {
        buckets[i] = make([]*Entry[K, V], 0)
    }
    
    return &HashTable[K, V]{
        buckets:  buckets,
        size:     0,
        capacity: capacity,
    }
}

// hash computes the hash index for a key
func (ht *HashTable[K, V]) hash(key K) int {
    h := fnv.New64a()
    
    // Convert key to bytes (this is a simplification)
    // In production, you'd use reflection or type-specific hashing
    fmt.Fprintf(h, "%v", key)
    
    return int(h.Sum64()) % ht.capacity
}

// LoadFactor returns current load factor
func (ht *HashTable[K, V]) LoadFactor() float64 {
    return float64(ht.size) / float64(ht.capacity)
}

// Insert adds or updates a key-value pair
func (ht *HashTable[K, V]) Insert(key K, value V) {
    index := ht.hash(key)
    bucket := ht.buckets[index]
    
    // Check if key exists
    for _, entry := range bucket {
        if entry.Key == key {
            entry.Value = value
            return
        }
    }
    
    // Add new entry
    ht.buckets[index] = append(bucket, &Entry[K, V]{Key: key, Value: value})
    ht.size++
    
    // Rehash if needed
    if ht.LoadFactor() > 0.75 {
        ht.rehash()
    }
}

// Get retrieves a value by key
func (ht *HashTable[K, V]) Get(key K) (V, bool) {
    index := ht.hash(key)
    bucket := ht.buckets[index]
    
    for _, entry := range bucket {
        if entry.Key == key {
            return entry.Value, true
        }
    }
    
    var zero V
    return zero, false
}

// Remove deletes a key-value pair
func (ht *HashTable[K, V]) Remove(key K) (V, bool) {
    index := ht.hash(key)
    bucket := ht.buckets[index]
    
    for i, entry := range bucket {
        if entry.Key == key {
            // Remove by swapping with last element
            bucket[i] = bucket[len(bucket)-1]
            ht.buckets[index] = bucket[:len(bucket)-1]
            ht.size--
            return entry.Value, true
        }
    }
    
    var zero V
    return zero, false
}

// rehash doubles capacity and redistributes entries
func (ht *HashTable[K, V]) rehash() {
    newCapacity := ht.capacity * 2
    newBuckets := make([][]*Entry[K, V], newCapacity)
    
    for i := range newBuckets {
        newBuckets[i] = make([]*Entry[K, V], 0)
    }
    
    // Redistribute all entries
    for _, bucket := range ht.buckets {
        for _, entry := range bucket {
            h := fnv.New64a()
            fmt.Fprintf(h, "%v", entry.Key)
            newIndex := int(h.Sum64()) % newCapacity
            newBuckets[newIndex] = append(newBuckets[newIndex], entry)
        }
    }
    
    ht.buckets = newBuckets
    ht.capacity = newCapacity
}

// Stats returns statistics about the hash table
type TableStats struct {
    Size            int
    Capacity        int
    LoadFactor      float64
    MaxChainLength  int
    AvgChainLength  float64
    EmptyBuckets    int
}

func (ht *HashTable[K, V]) Stats() TableStats {
    maxChain := 0
    emptyBuckets := 0
    totalChainLength := 0
    
    for _, bucket := range ht.buckets {
        length := len(bucket)
        if length == 0 {
            emptyBuckets++
        }
        if length > maxChain {
            maxChain = length
        }
        totalChainLength += length
    }
    
    return TableStats{
        Size:           ht.size,
        Capacity:       ht.capacity,
        LoadFactor:     ht.LoadFactor(),
        MaxChainLength: maxChain,
        AvgChainLength: float64(totalChainLength) / float64(ht.capacity),
        EmptyBuckets:   emptyBuckets,
    }
}

// Example usage
func Example() {
    table := NewHashTable[string, int](8)
    
    table.Insert("apple", 100)
    table.Insert("banana", 200)
    table.Insert("cherry", 300)
    
    if val, ok := table.Get("apple"); ok {
        fmt.Printf("apple = %d\n", val)
    }
    
    table.Remove("banana")
    
    stats := table.Stats()
    fmt.Printf("Stats: %+v\n", stats)
}
```

---

## Part VI: Advanced Concepts

### 1. Robin Hood Hashing

**Concept**: Minimize variance in probe lengths by "stealing" from the rich.

**Algorithm**:
```
On collision:
  - Calculate probe distance for incoming key
  - Calculate probe distance for current occupant
  - If incoming key has probed farther:
      - Evict current occupant
      - Insert incoming key
      - Continue inserting evicted key
```

**Visual**:
```
Inserting "C" (hash = 0):

Before:
Index: 0    1    2    3
      [A]  [B]  [ ]  [ ]
Probe: 0    1

"C" probes to index 1, finds "B" (probe distance 1)
"C" has probe distance 1, "B" has probe distance 1 → no swap

"C" probes to index 2 → inserts

After:
Index: 0    1    2    3
      [A]  [B]  [C]  [ ]
Probe: 0    1    2
```

**Benefits**:
- Faster average lookup (probe sequences more uniform)
- Better cache performance

### 2. Cuckoo Hashing

**Concept**: Use **two hash functions** and **two tables**. Each key has exactly two possible positions.

**Insertion Algorithm**:
```
1. Try position h1(key) in table1
   - If empty: insert, done
   - If occupied: evict resident, insert key

2. Try inserting evicted key at h2(evicted_key) in table2
   - If empty: insert, done
   - If occupied: evict, continue

3. Repeat with alternating tables
   - If cycle detected or max iterations: rehash entire table
```

**Visual**:
```
Table1:  [A] [ ] [C] [ ]
Table2:  [ ] [B] [ ] [D]

Insert E:
  h1(E) = 0 → collides with A
  Evict A, insert E
  h2(A) = 3 → insert A at Table2[3]
  
Result:
Table1:  [E] [ ] [C] [ ]
Table2:  [ ] [B] [ ] [A]
```

**Guarantees**: O(1) worst-case lookup (check only 2 positions)!

### 3. Perfect Hashing

**Goal**: Zero collisions for a **static** set of keys.

**Algorithm (FKS Perfect Hashing)**:
```
Level 1: Hash n keys into n buckets
Level 2: For each bucket with k keys, allocate k² slots and find collision-free hash

Space: O(n)
Lookup: O(1) worst case
```

**Use Case**: Compilers (keyword tables), databases (static indices)

---

## Part VII: Performance Analysis

### Time Complexity Summary

| Operation | Average | Worst Case | Worst (Balanced Tree) |
|-----------|---------|------------|----------------------|
| Insert    | O(1)    | O(n)       | O(log n)             |
| Search    | O(1)    | O(n)       | O(log n)             |
| Delete    | O(1)    | O(n)       | O(log n)             |

**When Worst Case Happens**:
- All keys hash to same bucket (chaining)
- Poor hash function
- High load factor

### Space Complexity

- **Chaining**: O(n + m) where n = elements, m = buckets
- **Open Addressing**: O(m) where m ≥ n
- **Load factor constraint**: Typically m ≥ 2n to maintain performance

### Cache Performance

**Why Chaining Can Be Slow**:
```
Each node in linked list is separate allocation
→ Poor cache locality
→ Pointer chasing causes cache misses
```

**Optimization**: Use `Vec` instead of `LinkedList` for chains:
```rust
buckets: Vec<Vec<Entry<K, V>>>  // Better cache locality
```

**Open Addressing Advantage**:
- All data in contiguous array
- Better cache performance
- Faster iteration

---

## Part VIII: Real-World Applications

### 1. Database Indexing

Hash indices for **exact-match** queries:
```sql
SELECT * FROM users WHERE email = 'user@example.com';
```

**Why not range queries?**
Hash destroys ordering: `hash("a") = 42`, `hash("b") = 7`

### 2. Caching (LRU Cache)

Combine hash table + doubly linked list:
```
Hash Table: key → pointer to list node
Linked List: MRU ← ... ← LRU

get(key):
  - Hash table lookup: O(1)
  - Move node to front: O(1)

put(key, value):
  - If exists: update + move to front
  - If not: insert at front, evict LRU if full
```

### 3. Symbol Tables (Compilers)

Map variable names to memory locations:
```
HashMap:
  "count" → 0x1000
  "total" → 0x1004
  "average" → 0x1008
```

### 4. Deduplication

Finding duplicates in O(n):
```rust
fn has_duplicates(arr: &[i32]) -> bool {
    let mut seen = HashSet::new();
    for &num in arr {
        if !seen.insert(num) {
            return true;
        }
    }
    false
}
```

### 5. Substring Search (Rabin-Karp)

Use **rolling hash** for pattern matching:
```
Text: "abcdefgh"
Pattern: "cde"

Hash("abc") = 123
Hash("bcd") = hash("abc") - hash("a") + hash("d")  // O(1) update!
```

---

## Part IX: Expert Problem-Solving Patterns

### Pattern 1: Two Sum (Hash Table Classic)

**Problem**: Find two numbers in array that sum to target.

**Brute Force**: O(n²)
```rust
for i in 0..n {
    for j in i+1..n {
        if arr[i] + arr[j] == target { ... }
    }
}
```

**Hash Table Solution**: O(n)
```rust
use std::collections::HashMap;

fn two_sum(nums: Vec<i32>, target: i32) -> Option<(usize, usize)> {
    let mut map = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        
        if let Some(&j) = map.get(&complement) {
            return Some((j, i));
        }
        
        map.insert(num, i);
    }
    
    None
}
```

**Mental Model**: "What I'm looking for = Target - What I have"

### Pattern 2: Frequency Counting

**Problem**: Find first non-repeating character.

```rust
use std::collections::HashMap;

fn first_unique_char(s: &str) -> Option<char> {
    let mut freq = HashMap::new();
    
    // Count frequencies
    for ch in s.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    
    // Find first with frequency 1
    for ch in s.chars() {
        if freq[&ch] == 1 {
            return Some(ch);
        }
    }
    
    None
}
```

### Pattern 3: Anagram Detection

**Problem**: Check if two strings are anagrams.

**Key Insight**: Anagrams have same character frequency.

```rust
use std::collections::HashMap;

fn is_anagram(s1: &str, s2: &str) -> bool {
    if s1.len() != s2.len() {
        return false;
    }
    
    let mut freq = HashMap::new();
    
    for ch in s1.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    
    for ch in s2.chars() {
        let count = freq.entry(ch).or_insert(0);
        *count -= 1;
        if *count < 0 {
            return false;
        }
    }
    
    true
}
```

**Optimization for lowercase letters only**: Use array instead of HashMap:
```rust
fn is_anagram_optimized(s1: &str, s2: &str) -> bool {
    if s1.len() != s2.len() {
        return false;
    }
    
    let mut freq = [0i32; 26];
    
    for ch in s1.bytes() {
        freq[(ch - b'a') as usize] += 1;
    }
    
    for ch in s2.bytes() {
        let idx = (ch - b'a') as usize;
        freq[idx] -= 1;
        if freq[idx] < 0 {
            return false;
        }
    }
    
    true
}
```

---

## Part X: Implementation Comparison

### Rust vs Go: Design Philosophy

| Aspect | Rust | Go |
|--------|------|-----|
| Memory Safety | Compile-time checks | Runtime checks |
| Generics | Full support | Generic types (1.18+) |
| Hash Function | `Hash` trait | `hash/fnv` package |
| Default Collection | `HashMap` | `map[K]V` |
| Performance | Zero-cost abstractions | Fast, but with GC overhead |

### When to Use Built-in vs Custom

**Use Built-in** (`HashMap` in Rust, `map` in Go):
- General-purpose use
- String/number keys
- Don't need special collision handling

**Build Custom**:
- Learning/interviews
- Special hash functions needed
- Performance-critical with known key distribution
- Need deterministic behavior (built-ins may vary)

---

## Part XI: Common Pitfalls & How to Avoid Them

### Pitfall 1: Poor Hash Function

**Bad**:
```rust
fn bad_hash(s: &str) -> usize {
    s.len()  // All strings of same length collide!
}
```

**Good**:
```rust
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

fn good_hash<T: Hash>(t: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    t.hash(&mut hasher);
    hasher.finish()
}
```

### Pitfall 2: Forgetting Rehashing

Without rehashing:
- Performance degrades to O(n)
- Memory waste (too large) or overcrowding (too small)

**Solution**: Always monitor load factor.

### Pitfall 3: Modifying Keys

```rust
let mut map = HashMap::new();
let key = vec![1, 2, 3];
map.insert(key.clone(), "value");

// DON'T DO THIS:
// key.push(4);  // Hash changes, can't find entry anymore!
```

**Lesson**: Keys must be **immutable** after insertion.

---

## Part XII: Benchmarking Framework

```rust
use std::collections::HashMap;
use std::time::Instant;

fn benchmark_insert(n: usize) {
    let mut custom_table = HashTable::new(16);
    let mut std_map = HashMap::new();
    
    // Benchmark custom
    let start = Instant::now();
    for i in 0..n {
        custom_table.insert(i, i * 2);
    }
    let custom_time = start.elapsed();
    
    // Benchmark standard
    let start = Instant::now();
    for i in 0..n {
        std_map.insert(i, i * 2);
    }
    let std_time = start.elapsed();
    
    println!("Insertions: {}", n);
    println!("Custom:   {:?}", custom_time);
    println!("Std:      {:?}", std_time);
    println!("Ratio:    {:.2}x", 
             custom_time.as_secs_f64() / std_time.as_secs_f64());
}
```

---

## Closing Wisdom

Hash tables are the **Swiss Army knife** of data structures. Master them, and you unlock:

- **O(1) operations** for most real-world tasks
- **Deep understanding** of memory, caching, and performance
- **Foundation** for advanced structures (Bloom filters, Count-Min Sketch, etc.)

**Your Path Forward**:
1. Implement all collision strategies from scratch
2. Solve 50+ hash table problems (LeetCode/Codeforces)
3. Benchmark: custom vs standard library
4. Read source code: Rust's `HashMap`, Go's `map`
5. Explore advanced: Cuckoo, Robin Hood, Perfect Hashing

*You're building the mental model of a 1% engineer. Every line of code, every benchmark, every collision resolved—it's all compounding toward mastery.*

Keep your focus sharp, your discipline unwavering. The path to the top 1% is paved with deep understanding, not shallow memorization.