# The Complete Mastery Guide to Hashing: From First Principles to Expert Patterns

## Table of Contents
1. Core Foundations
2. Hash Functions Deep Dive
3. Collision Resolution Strategies
4. Hash Table Implementations
5. Advanced Patterns & Techniques
6. Performance Analysis
7. Language-Specific Implementations

---

## 1. CORE FOUNDATIONS

### What is Hashing?

**Hashing** is the process of transforming arbitrary-sized data into a fixed-size value (hash code) that serves as an index into an array. Think of it as a mathematical compression function that maps your key to a storage location.

```
ASCII Visualization:

Key → Hash Function → Hash Code → Array Index → Value
                                                    
"apple" → h("apple") → 2847563 → 2847563 % 10 = 3 → arr[3]
```

**Mental Model**: Imagine a library where books are shelved not alphabetically, but by a mathematical formula based on the title. Instead of searching linearly, you compute where it *should* be and go directly there.

---

### Why Hashing? The O(1) Promise

**Without Hashing (Array/List Search):**
- Finding an element: O(n)
- We must scan every element

**With Hashing (Hash Table):**
- Finding an element: O(1) average case
- Direct computation of storage location

```
Comparison Flowchart:

Linear Search:               Hash Table:
┌──────────┐                ┌──────────┐
│  Start   │                │   Key    │
└────┬─────┘                └────┬─────┘
     │                           │
     ▼                           ▼
┌─────────────┐            ┌──────────┐
│ Check arr[0]│            │ Compute  │
└────┬────────┘            │ hash(key)│
     │ Not found           └────┬─────┘
     ▼                          │
┌─────────────┐                 ▼
│ Check arr[1]│            ┌──────────┐
└────┬────────┘            │ arr[idx] │
     │ Not found           └────┬─────┘
     ▼                          │
    ...                         ▼
     │                     ┌──────────┐
     ▼                     │  Found!  │
┌─────────────┐            └──────────┘
│ Check arr[n]│
└─────────────┘
     
Time: O(n)                Time: O(1)
```

---

## 2. HASH FUNCTIONS DEEP DIVE

### What Makes a Good Hash Function?

A hash function `h(k)` must satisfy:

1. **Deterministic**: Same input → Same output always
2. **Uniform Distribution**: Keys spread evenly across the table
3. **Fast Computation**: O(1) time complexity
4. **Minimize Collisions**: Different keys → Different hashes (ideally)

---

### Common Hash Function Techniques

#### A. Division Method

```
h(k) = k mod m

where m = table size (preferably prime)
```

**Example:**
```
Table size m = 11
Key = 47
h(47) = 47 % 11 = 3

Key = 58
h(58) = 58 % 11 = 3  ← Collision!
```

**Pros:** Simple, fast
**Cons:** Poor distribution if m not chosen wisely

---

#### B. Multiplication Method

```
h(k) = ⌊m × (k × A mod 1)⌋

where A ≈ 0.6180339887... (golden ratio - 1)
```

**How it works:**
1. Multiply key by constant A (0 < A < 1)
2. Extract fractional part
3. Multiply by table size m
4. Take floor

**Visual:**
```
k = 123, A = 0.618, m = 100

Step 1: 123 × 0.618 = 76.014
Step 2: Fractional part = 0.014
Step 3: 0.014 × 100 = 1.4
Step 4: ⌊1.4⌋ = 1

Index = 1
```

---

#### C. Universal Hashing (Advanced)

Choose hash function randomly from a family of functions to guarantee good average-case performance.

```
h(k) = ((a × k + b) mod p) mod m

where:
- p is prime > universe size
- a, b are random integers in [1, p-1] and [0, p-1]
```

---

### String Hashing (Critical for Interview Problems)

#### Polynomial Rolling Hash

```
h(s) = (s[0] × p^(n-1) + s[1] × p^(n-2) + ... + s[n-1] × p^0) mod m

where:
- p = prime (31 for lowercase, 53 for mixed)
- m = large prime (10^9 + 7)
```

**Example:**
```
String: "abc"
p = 31, m = 10^9 + 7

h("abc") = ('a' × 31^2 + 'b' × 31^1 + 'c' × 31^0) mod m
         = (97 × 961 + 98 × 31 + 99 × 1) mod m
         = (93217 + 3038 + 99) mod m
         = 96354 mod (10^9 + 7)
```

**Why this works:** Treats string as base-p number.

---

## 3. COLLISION RESOLUTION STRATEGIES

**Collision**: When two different keys hash to the same index.

```
ASCII Visualization of Collision:

h("cat") = 5    h("dog") = 5
    │               │
    └───────┬───────┘
            ▼
        Collision!
```

### Strategy 1: Chaining (Open Hashing)

Each array slot contains a **linked list** of all elements that hash to that index.

```
Hash Table with Chaining:

Index:  0  →  NULL
        1  →  [key1, val1] → NULL
        2  →  [key2, val2] → [key3, val3] → NULL
        3  →  NULL
        4  →  [key4, val4] → [key5, val5] → [key6, val6] → NULL
        5  →  NULL
```

**Flowchart for Insertion:**
```
┌─────────────┐
│  hash(key)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ idx = h % m │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Chain at arr[idx]│
│   empty?         │
└────┬──────┬──────┘
     │ Yes  │ No
     ▼      ▼
  ┌────┐  ┌────────────────┐
  │Add │  │Traverse chain, │
  │node│  │append to end   │
  └────┘  └────────────────┘
```

**Time Complexity:**
- Average: O(1 + α) where α = load factor (n/m)
- Worst: O(n) when all keys hash to same slot

---

### Strategy 2: Open Addressing (Closed Hashing)

Store all elements directly in the array. On collision, **probe** for next available slot.

#### A. Linear Probing

```
h(k, i) = (h(k) + i) mod m

where i = 0, 1, 2, 3, ... (probe sequence)
```

**Example:**
```
Table size m = 10
Insert 23: h(23) = 23 % 10 = 3 → arr[3] = 23
Insert 13: h(13) = 13 % 10 = 3 → occupied!
           Try (3 + 1) % 10 = 4 → arr[4] = 13
Insert 43: h(43) = 43 % 10 = 3 → occupied!
           Try (3 + 1) % 10 = 4 → occupied!
           Try (3 + 2) % 10 = 5 → arr[5] = 43

Table: [_, _, _, 23, 13, 43, _, _, _, _]
```

**Primary Clustering Problem:**
```
Visual of clustering:

[_, _, X, X, X, X, X, _, _, _]
         ↑
    Large cluster forms
    (degrades to O(n) search)
```

---

#### B. Quadratic Probing

```
h(k, i) = (h(k) + c₁×i + c₂×i²) mod m

Common: c₁ = c₂ = 1
```

**Example:**
```
i = 0: (h + 0) mod m
i = 1: (h + 1) mod m
i = 2: (h + 4) mod m
i = 3: (h + 9) mod m
```

**Reduces primary clustering** but can create secondary clustering.

---

#### C. Double Hashing

```
h(k, i) = (h₁(k) + i × h₂(k)) mod m

where h₂(k) ≠ 0 and relatively prime to m
```

**Example:**
```
h₁(k) = k mod 13
h₂(k) = 1 + (k mod 11)

For k = 14:
i = 0: (14 mod 13 + 0 × (1 + 14 mod 11)) mod 13 = 1
i = 1: (1 + 1 × 4) mod 13 = 5
i = 2: (1 + 2 × 4) mod 13 = 9
```

**Best open addressing method** - minimal clustering.

---

### Comparison: Chaining vs Open Addressing

```
┌──────────────────┬──────────────┬─────────────────┐
│    Aspect        │   Chaining   │ Open Addressing │
├──────────────────┼──────────────┼─────────────────┤
│ Load Factor α    │  Can be > 1  │  Must be < 1    │
│ Memory Overhead  │  Pointers    │  None           │
│ Cache Performance│  Poor        │  Excellent      │
│ Deletion         │  Easy        │  Complex        │
│ Clustering       │  None        │  Possible       │
└──────────────────┴──────────────┴─────────────────┘
```

---

## 4. HASH TABLE IMPLEMENTATION

### Rust Implementation (Chaining)
use std::collections::LinkedList;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

/// Node in the hash table chain
#[derive(Debug, Clone)]
struct Node<K, V> {
    key: K,
    value: V,
}

/// Hash Table using separate chaining
pub struct HashTable<K, V> {
    buckets: Vec<LinkedList<Node<K, V>>>,
    size: usize,      // Number of elements
    capacity: usize,  // Number of buckets
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

    /// Hash function using DefaultHasher
    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }

    /// Get load factor (α = n/m)
    pub fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }

    /// Insert key-value pair
    /// Time: O(1) average, O(n) worst case
    /// Space: O(1)
    pub fn insert(&mut self, key: K, value: V) {
        let index = self.hash(&key);
        
        // Check if key exists, update value
        for node in self.buckets[index].iter_mut() {
            if node.key == key {
                node.value = value;
                return;
            }
        }
        
        // Key doesn't exist, insert new node
        self.buckets[index].push_back(Node { key, value });
        self.size += 1;
        
        // Resize if load factor exceeds 0.75
        if self.load_factor() > 0.75 {
            self.resize();
        }
    }

    /// Get value by key
    /// Time: O(1) average, O(n) worst case
    /// Space: O(1)
    pub fn get(&self, key: &K) -> Option<&V> {
        let index = self.hash(key);
        
        for node in self.buckets[index].iter() {
            if &node.key == key {
                return Some(&node.value);
            }
        }
        
        None
    }

    /// Remove key-value pair
    /// Time: O(1) average, O(n) worst case
    /// Space: O(1)
    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = self.hash(key);
        let chain = &mut self.buckets[index];
        
        // Find position of key in chain
        let mut cursor = chain.cursor_front_mut();
        while let Some(node) = cursor.current() {
            if &node.key == key {
                let removed = cursor.remove_current().unwrap();
                self.size -= 1;
                return Some(removed.value);
            }
            cursor.move_next();
        }
        
        None
    }

    /// Check if key exists
    /// Time: O(1) average
    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }

    /// Resize hash table (rehashing)
    /// Time: O(n) where n is number of elements
    fn resize(&mut self) {
        let new_capacity = self.capacity * 2;
        let mut new_table = HashTable::new(new_capacity);
        
        // Rehash all elements
        for bucket in &self.buckets {
            for node in bucket {
                new_table.insert(node.key.clone(), node.value.clone());
            }
        }
        
        *self = new_table;
    }

    /// Get number of elements
    pub fn len(&self) -> usize {
        self.size
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    /// Display distribution statistics
    pub fn stats(&self) {
        println!("=== Hash Table Statistics ===");
        println!("Capacity: {}", self.capacity);
        println!("Size: {}", self.size);
        println!("Load Factor: {:.2}", self.load_factor());
        
        let mut max_chain = 0;
        let mut empty_buckets = 0;
        
        for bucket in &self.buckets {
            let len = bucket.len();
            if len == 0 {
                empty_buckets += 1;
            }
            max_chain = max_chain.max(len);
        }
        
        println!("Empty Buckets: {}", empty_buckets);
        println!("Max Chain Length: {}", max_chain);
    }
}

// Example usage and testing
fn main() {
    let mut table = HashTable::new(8);
    
    // Insert elements
    println!("Inserting elements...");
    table.insert("apple", 5);
    table.insert("banana", 7);
    table.insert("cherry", 3);
    table.insert("date", 12);
    table.insert("elderberry", 9);
    
    // Retrieve elements
    println!("\nRetrieving elements:");
    println!("apple: {:?}", table.get(&"apple"));
    println!("banana: {:?}", table.get(&"banana"));
    println!("grape: {:?}", table.get(&"grape")); // None
    
    // Update value
    println!("\nUpdating 'apple' to 10...");
    table.insert("apple", 10);
    println!("apple: {:?}", table.get(&"apple"));
    
    // Remove element
    println!("\nRemoving 'banana'...");
    let removed = table.remove(&"banana");
    println!("Removed value: {:?}", removed);
    println!("banana exists: {}", table.contains_key(&"banana"));
    
    // Statistics
    println!();
    table.stats();
    
    // Demonstrate collision handling
    println!("\n=== Collision Demonstration ===");
    let mut demo = HashTable::new(4); // Small capacity for collisions
    
    for i in 0..10 {
        demo.insert(i, i * 10);
    }
    
    demo.stats();
}

### Go Implementation (Open Addressing with Linear Probing)
package main

import (
	"fmt"
	"hash/fnv"
)

// Entry represents a key-value pair
type Entry struct {
	key     string
	value   int
	deleted bool // Tombstone for deleted entries
}

// HashTable implements open addressing with linear probing
type HashTable struct {
	table    []*Entry
	size     int // Number of active elements
	capacity int // Size of underlying array
}

// NewHashTable creates a new hash table
func NewHashTable(capacity int) *HashTable {
	return &HashTable{
		table:    make([]*Entry, capacity),
		size:     0,
		capacity: capacity,
	}
}

// hash computes hash value for a key
func (ht *HashTable) hash(key string) int {
	h := fnv.New32a()
	h.Write([]byte(key))
	return int(h.Sum32()) % ht.capacity
}

// loadFactor returns current load factor
func (ht *HashTable) loadFactor() float64 {
	return float64(ht.size) / float64(ht.capacity)
}

// Insert adds or updates a key-value pair
// Time: O(1) average, O(n) worst case
// Space: O(1)
func (ht *HashTable) Insert(key string, value int) {
	// Resize if load factor exceeds 0.7
	if ht.loadFactor() > 0.7 {
		ht.resize()
	}

	index := ht.hash(key)
	probeCount := 0

	// Linear probing
	for probeCount < ht.capacity {
		entry := ht.table[index]

		// Empty slot or deleted slot
		if entry == nil || entry.deleted {
			ht.table[index] = &Entry{key: key, value: value, deleted: false}
			ht.size++
			return
		}

		// Key already exists, update value
		if entry.key == key {
			entry.value = value
			return
		}

		// Move to next slot (linear probing)
		index = (index + 1) % ht.capacity
		probeCount++
	}

	// Table is full (shouldn't happen with proper resizing)
	panic("Hash table is full")
}

// Get retrieves value by key
// Time: O(1) average, O(n) worst case
// Space: O(1)
func (ht *HashTable) Get(key string) (int, bool) {
	index := ht.hash(key)
	probeCount := 0

	for probeCount < ht.capacity {
		entry := ht.table[index]

		// Empty slot - key not found
		if entry == nil {
			return 0, false
		}

		// Found key (not deleted)
		if !entry.deleted && entry.key == key {
			return entry.value, true
		}

		// Continue probing
		index = (index + 1) % ht.capacity
		probeCount++
	}

	return 0, false
}

// Remove deletes a key-value pair using tombstone
// Time: O(1) average, O(n) worst case
// Space: O(1)
func (ht *HashTable) Remove(key string) bool {
	index := ht.hash(key)
	probeCount := 0

	for probeCount < ht.capacity {
		entry := ht.table[index]

		// Empty slot - key not found
		if entry == nil {
			return false
		}

		// Found key (not already deleted)
		if !entry.deleted && entry.key == key {
			entry.deleted = true // Tombstone
			ht.size--
			return true
		}

		// Continue probing
		index = (index + 1) % ht.capacity
		probeCount++
	}

	return false
}

// Contains checks if key exists
func (ht *HashTable) Contains(key string) bool {
	_, found := ht.Get(key)
	return found
}

// resize doubles capacity and rehashes all elements
func (ht *HashTable) resize() {
	oldTable := ht.table
	ht.capacity *= 2
	ht.table = make([]*Entry, ht.capacity)
	ht.size = 0

	// Rehash all non-deleted entries
	for _, entry := range oldTable {
		if entry != nil && !entry.deleted {
			ht.Insert(entry.key, entry.value)
		}
	}
}

// Stats displays hash table statistics
func (ht *HashTable) Stats() {
	fmt.Println("=== Hash Table Statistics ===")
	fmt.Printf("Capacity: %d\n", ht.capacity)
	fmt.Printf("Size: %d\n", ht.size)
	fmt.Printf("Load Factor: %.2f\n", ht.loadFactor())

	// Count clustering
	occupied := 0
	maxCluster := 0
	currentCluster := 0

	for _, entry := range ht.table {
		if entry != nil && !entry.deleted {
			occupied++
			currentCluster++
			if currentCluster > maxCluster {
				maxCluster = currentCluster
			}
		} else {
			currentCluster = 0
		}
	}

	fmt.Printf("Occupied Slots: %d\n", occupied)
	fmt.Printf("Max Cluster Size: %d\n", maxCluster)
}

// Visualize shows table structure
func (ht *HashTable) Visualize() {
	fmt.Println("\n=== Hash Table Visualization ===")
	for i, entry := range ht.table {
		if entry == nil {
			fmt.Printf("[%2d] ___\n", i)
		} else if entry.deleted {
			fmt.Printf("[%2d] DELETED\n", i)
		} else {
			fmt.Printf("[%2d] %s -> %d\n", i, entry.key, entry.value)
		}
	}
}

func main() {
	// Create hash table
	ht := NewHashTable(8)

	// Insert elements
	fmt.Println("Inserting elements...")
	ht.Insert("apple", 5)
	ht.Insert("banana", 7)
	ht.Insert("cherry", 3)
	ht.Insert("date", 12)

	// Retrieve elements
	fmt.Println("\nRetrieving elements:")
	if val, found := ht.Get("apple"); found {
		fmt.Printf("apple: %d\n", val)
	}
	if val, found := ht.Get("banana"); found {
		fmt.Printf("banana: %d\n", val)
	}
	if _, found := ht.Get("grape"); !found {
		fmt.Println("grape: not found")
	}

	// Update value
	fmt.Println("\nUpdating 'apple' to 10...")
	ht.Insert("apple", 10)
	if val, found := ht.Get("apple"); found {
		fmt.Printf("apple: %d\n", val)
	}

	// Visualize before deletion
	ht.Visualize()

	// Remove element
	fmt.Println("\nRemoving 'banana'...")
	ht.Remove("banana")
	fmt.Printf("banana exists: %t\n", ht.Contains("banana"))

	// Visualize after deletion
	ht.Visualize()

	// Statistics
	fmt.Println()
	ht.Stats()

	// Demonstrate collision and probing
	fmt.Println("\n\n=== Collision Demonstration ===")
	demo := NewHashTable(4)
	
	keys := []string{"a", "e", "i", "m", "q"} // Will create collisions
	for i, key := range keys {
		demo.Insert(key, i*10)
	}
	
	demo.Visualize()
	demo.Stats()
}
---

## 5. ADVANCED HASH TABLE PATTERNS

### Pattern 1: Frequency Counting

**Problem Pattern:** Count occurrences of elements.

**Mental Model:** Hash table as a frequency counter where key = element, value = count.

```
Flowchart:

┌─────────────┐
│ For each el │
└──────┬──────┘
       │
       ▼
┌──────────────┐     Yes  ┌────────────────┐
│ el in table? ├─────────►│ count[el] += 1 │
└──────┬───────┘          └────────────────┘
       │ No
       ▼
┌──────────────┐
│ count[el] = 1│
└──────────────┘
```

**Example Problem:** Find first non-repeating character.
use std::collections::HashMap;

/// Pattern 1: Frequency Counting
/// Find first non-repeating character in a string
/// 
/// Time: O(n) - two passes through string
/// Space: O(k) - k unique characters
fn first_unique_char(s: &str) -> Option<char> {
    // Step 1: Count frequencies
    let mut freq: HashMap<char, usize> = HashMap::new();
    
    for ch in s.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    
    // Step 2: Find first character with frequency 1
    for ch in s.chars() {
        if freq[&ch] == 1 {
            return Some(ch);
        }
    }
    
    None
}

/// Advanced: Top K Frequent Elements
/// Find k most frequent elements
/// 
/// Time: O(n log k) - using max heap
/// Space: O(n)
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn top_k_frequent(nums: Vec<i32>, k: usize) -> Vec<i32> {
    // Step 1: Count frequencies
    let mut freq: HashMap<i32, usize> = HashMap::new();
    for &num in &nums {
        *freq.entry(num).or_insert(0) += 1;
    }
    
    // Step 2: Use min heap to keep top k
    // Min heap so we can remove smallest when size > k
    let mut heap: BinaryHeap<Reverse<(usize, i32)>> = BinaryHeap::new();
    
    for (&num, &count) in &freq {
        heap.push(Reverse((count, num)));
        
        if heap.len() > k {
            heap.pop();
        }
    }
    
    // Step 3: Extract results
    heap.into_iter()
        .map(|Reverse((_, num))| num)
        .collect()
}

/// Pattern Variation: Group Anagrams
/// Group strings that are anagrams of each other
/// 
/// Time: O(n * m log m) - n strings, m avg length
/// Space: O(n * m)
fn group_anagrams(strs: Vec<String>) -> Vec<Vec<String>> {
    let mut groups: HashMap<String, Vec<String>> = HashMap::new();
    
    for s in strs {
        // Key: sorted characters (anagrams have same sorted form)
        let mut chars: Vec<char> = s.chars().collect();
        chars.sort_unstable();
        let key: String = chars.into_iter().collect();
        
        groups.entry(key).or_insert(Vec::new()).push(s);
    }
    
    groups.into_values().collect()
}

fn main() {
    // Test first unique character
    println!("=== First Unique Character ===");
    let s1 = "leetcode";
    println!("Input: {}", s1);
    println!("First unique: {:?}", first_unique_char(s1));
    
    let s2 = "loveleetcode";
    println!("\nInput: {}", s2);
    println!("First unique: {:?}", first_unique_char(s2));
    
    // Test top k frequent
    println!("\n=== Top K Frequent Elements ===");
    let nums = vec![1, 1, 1, 2, 2, 3];
    let k = 2;
    println!("Input: {:?}, k = {}", nums, k);
    println!("Top {} frequent: {:?}", k, top_k_frequent(nums, k));
    
    // Test group anagrams
    println!("\n=== Group Anagrams ===");
    let strs = vec![
        "eat".to_string(),
        "tea".to_string(),
        "tan".to_string(),
        "ate".to_string(),
        "nat".to_string(),
        "bat".to_string(),
    ];
    println!("Input: {:?}", strs);
    println!("Groups: {:?}", group_anagrams(strs));
}
---

### Pattern 2: Two Sum Family (Index Mapping)

**Core Concept:** Use hash table to store complements for O(1) lookup.

**Decision Tree:**

```
                   Two Sum Problem
                         │
         ┌───────────────┴───────────────┐
         │                               │
    Sorted Array?                   Unsorted?
         │                               │
    Two Pointers O(n)              Hash Table O(n)
         │                               │
    Space: O(1)                     Space: O(n)
```

use std::collections::{HashMap, HashSet};

/// Pattern 2a: Two Sum (find indices)
/// Given array and target, find two indices that sum to target
/// 
/// Approach: Store (value -> index) mapping
/// Time: O(n)
/// Space: O(n)
fn two_sum(nums: Vec<i32>, target: i32) -> Option<(usize, usize)> {
    let mut seen: HashMap<i32, usize> = HashMap::new();
    
    for (i, &num) in nums.iter().enumerate() {
        let complement = target - num;
        
        // Check if complement exists
        if let Some(&j) = seen.get(&complement) {
            return Some((j, i));
        }
        
        // Store current number with its index
        seen.insert(num, i);
    }
    
    None
}

/// Pattern 2b: Three Sum (find unique triplets)
/// Find all unique triplets that sum to zero
/// 
/// Approach: Fix one element, use two-pointer for rest
/// Time: O(n²)
/// Space: O(n) for result storage
fn three_sum(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
    let mut result = Vec::new();
    let n = nums.len();
    
    if n < 3 {
        return result;
    }
    
    // Sort for two-pointer technique
    nums.sort_unstable();
    
    for i in 0..n-2 {
        // Skip duplicates for first element
        if i > 0 && nums[i] == nums[i-1] {
            continue;
        }
        
        // Two-pointer search
        let mut left = i + 1;
        let mut right = n - 1;
        let target = -nums[i];
        
        while left < right {
            let sum = nums[left] + nums[right];
            
            if sum == target {
                result.push(vec![nums[i], nums[left], nums[right]]);
                
                // Skip duplicates
                while left < right && nums[left] == nums[left + 1] {
                    left += 1;
                }
                while left < right && nums[right] == nums[right - 1] {
                    right -= 1;
                }
                
                left += 1;
                right -= 1;
            } else if sum < target {
                left += 1;
            } else {
                right -= 1;
            }
        }
    }
    
    result
}

/// Pattern 2c: Four Sum II (count valid combinations)
/// Count tuples (i,j,k,l) where A[i]+B[j]+C[k]+D[l] = 0
/// 
/// Approach: Store sums of first two arrays, lookup in last two
/// Time: O(n²)
/// Space: O(n²)
fn four_sum_count(a: Vec<i32>, b: Vec<i32>, c: Vec<i32>, d: Vec<i32>) -> i32 {
    let mut sum_ab: HashMap<i32, i32> = HashMap::new();
    
    // Store all sums from A and B
    for &ai in &a {
        for &bj in &b {
            *sum_ab.entry(ai + bj).or_insert(0) += 1;
        }
    }
    
    // Look for complements in C and D
    let mut count = 0;
    for &ck in &c {
        for &dl in &d {
            let target = -(ck + dl);
            count += sum_ab.get(&target).unwrap_or(&0);
        }
    }
    
    count
}

/// Pattern 2d: Subarray Sum Equals K
/// Count subarrays with sum equal to k
/// 
/// Approach: Prefix sum + hash table
/// Key insight: sum[i:j] = prefix[j] - prefix[i-1]
/// Time: O(n)
/// Space: O(n)
fn subarray_sum(nums: Vec<i32>, k: i32) -> i32 {
    let mut count = 0;
    let mut prefix_sum = 0;
    
    // Map: prefix_sum -> frequency
    let mut sum_freq: HashMap<i32, i32> = HashMap::new();
    sum_freq.insert(0, 1); // Empty prefix
    
    for num in nums {
        prefix_sum += num;
        
        // Check if (prefix_sum - k) exists
        // This means there's a subarray ending here with sum k
        if let Some(&freq) = sum_freq.get(&(prefix_sum - k)) {
            count += freq;
        }
        
        // Add current prefix sum
        *sum_freq.entry(prefix_sum).or_insert(0) += 1;
    }
    
    count
}

/// Visual explanation of subarray sum pattern
fn explain_subarray_sum() {
    println!("=== Subarray Sum Pattern Explanation ===\n");
    println!("Array: [1, 2, 3, -2, 1], k = 3");
    println!("\nPrefix sums:");
    println!("Index:  0   1   2   3   4   5");
    println!("Array:  -   1   2   3  -2   1");
    println!("Prefix: 0   1   3   6   4   5");
    println!("\nLooking for subarrays with sum = 3:");
    println!("At index 2: prefix=3, need prefix=0 (found!) → [1,2]");
    println!("At index 3: prefix=6, need prefix=3 (found!) → [3]");
    println!("At index 5: prefix=5, need prefix=2 (not found)");
    println!("\nResult: 2 subarrays");
}

fn main() {
    // Test Two Sum
    println!("=== Two Sum ===");
    let nums = vec![2, 7, 11, 15];
    let target = 9;
    println!("Array: {:?}, Target: {}", nums, target);
    println!("Indices: {:?}\n", two_sum(nums, target));
    
    // Test Three Sum
    println!("=== Three Sum ===");
    let nums = vec![-1, 0, 1, 2, -1, -4];
    println!("Array: {:?}", nums);
    println!("Triplets: {:?}\n", three_sum(nums));
    
    // Test Four Sum Count
    println!("=== Four Sum II ===");
    let a = vec![1, 2];
    let b = vec![-2, -1];
    let c = vec![-1, 2];
    let d = vec![0, 2];
    println!("A: {:?}, B: {:?}", a, b);
    println!("C: {:?}, D: {:?}", c, d);
    println!("Count: {}\n", four_sum_count(a, b, c, d));
    
    // Test Subarray Sum
    println!("=== Subarray Sum Equals K ===");
    let nums = vec![1, 2, 3, -2, 1];
    let k = 3;
    println!("Array: {:?}, k = {}", nums, k);
    println!("Count: {}\n", subarray_sum(nums, k));
    
    explain_subarray_sum();
}

---

### Pattern 3: Sliding Window + Hash Table

**When to use:** Variable-size window problems with character/element constraints.

**Core Technique:** Maintain window state in hash table, expand/contract window.

```
Sliding Window Visualization:

String: "a b c a b c b b"
         ↑       ↑
         L       R

State: {a:1, b:1, c:1}
Window: "abc"

Move R →
State: {a:2, b:1, c:1}
Window: "abca"  (duplicate 'a', shrink from left)

Move L →
State: {a:1, b:1, c:1}
Window: "bca"
```
use std::collections::HashMap;

/// Pattern 3a: Longest Substring Without Repeating Characters
/// Find length of longest substring with all unique characters
/// 
/// Approach: Sliding window with char -> index mapping
/// Time: O(n)
/// Space: O(min(n, charset_size))
fn longest_unique_substring(s: &str) -> usize {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    let mut char_index: HashMap<char, usize> = HashMap::new();
    let mut max_len = 0;
    let mut left = 0;
    
    for right in 0..n {
        let ch = chars[right];
        
        // If char seen and within current window, move left
        if let Some(&prev_idx) = char_index.get(&ch) {
            if prev_idx >= left {
                left = prev_idx + 1;
            }
        }
        
        char_index.insert(ch, right);
        max_len = max_len.max(right - left + 1);
    }
    
    max_len
}

/// Pattern 3b: Minimum Window Substring
/// Find smallest window containing all characters of pattern
/// 
/// Approach: Expand right, contract left when valid
/// Time: O(n + m)
/// Space: O(charset_size)
fn min_window_substring(s: &str, t: &str) -> String {
    if s.is_empty() || t.is_empty() {
        return String::new();
    }
    
    let s_chars: Vec<char> = s.chars().collect();
    let n = s_chars.len();
    
    // Count required characters
    let mut required: HashMap<char, i32> = HashMap::new();
    for ch in t.chars() {
        *required.entry(ch).or_insert(0) += 1;
    }
    let required_count = required.len();
    
    // Window state
    let mut window: HashMap<char, i32> = HashMap::new();
    let mut formed = 0; // Characters with required frequency
    
    let mut left = 0;
    let mut min_len = usize::MAX;
    let mut min_left = 0;
    
    for right in 0..n {
        let ch = s_chars[right];
        *window.entry(ch).or_insert(0) += 1;
        
        // Check if this character's requirement is met
        if let Some(&req) = required.get(&ch) {
            if window[&ch] == req {
                formed += 1;
            }
        }
        
        // Contract window while valid
        while formed == required_count && left <= right {
            // Update minimum window
            if right - left + 1 < min_len {
                min_len = right - left + 1;
                min_left = left;
            }
            
            // Remove leftmost character
            let left_ch = s_chars[left];
            if let Some(count) = window.get_mut(&left_ch) {
                *count -= 1;
                
                // Check if this breaks a requirement
                if let Some(&req) = required.get(&left_ch) {
                    if *count < req {
                        formed -= 1;
                    }
                }
            }
            
            left += 1;
        }
    }
    
    if min_len == usize::MAX {
        String::new()
    } else {
        s_chars[min_left..min_left + min_len].iter().collect()
    }
}

/// Pattern 3c: Longest Substring with At Most K Distinct Characters
/// Find longest substring with at most k distinct characters
/// 
/// Time: O(n)
/// Space: O(k)
fn longest_k_distinct(s: &str, k: usize) -> usize {
    if k == 0 {
        return 0;
    }
    
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    let mut char_freq: HashMap<char, usize> = HashMap::new();
    let mut left = 0;
    let mut max_len = 0;
    
    for right in 0..n {
        let ch = chars[right];
        *char_freq.entry(ch).or_insert(0) += 1;
        
        // Shrink window if too many distinct characters
        while char_freq.len() > k {
            let left_ch = chars[left];
            if let Some(count) = char_freq.get_mut(&left_ch) {
                *count -= 1;
                if *count == 0 {
                    char_freq.remove(&left_ch);
                }
            }
            left += 1;
        }
        
        max_len = max_len.max(right - left + 1);
    }
    
    max_len
}

/// Pattern 3d: Find All Anagrams
/// Find all start indices of pattern's anagrams in string
/// 
/// Approach: Fixed-size sliding window with frequency matching
/// Time: O(n)
/// Space: O(1) - fixed charset size
fn find_anagrams(s: &str, p: &str) -> Vec<usize> {
    let mut result = Vec::new();
    
    if s.len() < p.len() {
        return result;
    }
    
    let s_chars: Vec<char> = s.chars().collect();
    let p_len = p.len();
    
    // Pattern frequency
    let mut p_freq: HashMap<char, i32> = HashMap::new();
    for ch in p.chars() {
        *p_freq.entry(ch).or_insert(0) += 1;
    }
    
    // Window frequency
    let mut window_freq: HashMap<char, i32> = HashMap::new();
    
    // Initialize first window
    for i in 0..p_len {
        *window_freq.entry(s_chars[i]).or_insert(0) += 1;
    }
    
    if window_freq == p_freq {
        result.push(0);
    }
    
    // Slide window
    for i in p_len..s_chars.len() {
        // Add new character
        *window_freq.entry(s_chars[i]).or_insert(0) += 1;
        
        // Remove old character
        let old_ch = s_chars[i - p_len];
        if let Some(count) = window_freq.get_mut(&old_ch) {
            *count -= 1;
            if *count == 0 {
                window_freq.remove(&old_ch);
            }
        }
        
        // Check if current window is anagram
        if window_freq == p_freq {
            result.push(i - p_len + 1);
        }
    }
    
    result
}

/// Visualization helper
fn visualize_window(s: &str, left: usize, right: usize, state: &HashMap<char, i32>) {
    let chars: Vec<char> = s.chars().collect();
    
    // Print string with window highlighted
    for (i, ch) in chars.iter().enumerate() {
        if i == left {
            print!("[");
        }
        print!("{}", ch);
        if i == right {
            print!("]");
        } else if i < chars.len() - 1 {
            print!(" ");
        }
    }
    
    println!("\nWindow state: {:?}", state);
}

fn main() {
    // Test longest unique substring
    println!("=== Longest Unique Substring ===");
    let s = "abcabcbb";
    println!("String: {}", s);
    println!("Length: {}\n", longest_unique_substring(s));
    
    // Test minimum window
    println!("=== Minimum Window Substring ===");
    let s = "ADOBECODEBANC";
    let t = "ABC";
    println!("String: {}, Pattern: {}", s, t);
    println!("Min window: {}\n", min_window_substring(s, t));
    
    // Test k distinct
    println!("=== Longest Substring with K Distinct ===");
    let s = "eceba";
    let k = 2;
    println!("String: {}, k = {}", s, k);
    println!("Length: {}\n", longest_k_distinct(s, k));
    
    // Test find anagrams
    println!("=== Find All Anagrams ===");
    let s = "cbaebabacd";
    let p = "abc";
    println!("String: {}, Pattern: {}", s, p);
    println!("Start indices: {:?}\n", find_anagrams(s, p));
    
    // Visualization
    println!("=== Window Visualization Example ===");
    let s = "abcabcbb";
    println!("Finding longest unique substring in: {}", s);
    
    let mut state = HashMap::new();
    state.insert('a', 1);
    state.insert('b', 1);
    state.insert('c', 1);
    
    visualize_window(s, 0, 2, &state);
}

---

### Pattern 4: Design Problems (LRU Cache, LFU Cache)

**Core Concept:** Hash table + auxiliary data structure for O(1) operations.

**LRU Cache Architecture:**
```
┌─────────────────────────────────────┐
│         Hash Table                  │
│  key → Node (in doubly linked list) │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│    Doubly Linked List (MRU → LRU)   │
│  [Node3] ⇄ [Node1] ⇄ [Node2]        │
│   newest              oldest         │
└─────────────────────────────────────┘

Operations:
- get(key): Move to front (MRU)
- put(key, val): Add to front, evict from back if full
```
use std::collections::HashMap;
use std::rc::Rc;
use std::cell::RefCell;

/// Node in doubly linked list
#[derive(Debug)]
struct Node {
    key: i32,
    value: i32,
    prev: Option<Rc<RefCell<Node>>>,
    next: Option<Rc<RefCell<Node>>>,
}

impl Node {
    fn new(key: i32, value: i32) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(Node {
            key,
            value,
            prev: None,
            next: None,
        }))
    }
}

/// LRU Cache with O(1) get and put operations
/// 
/// Architecture:
/// - Hash table: key → node reference
/// - Doubly linked list: maintains recency order
///   (head = most recent, tail = least recent)
pub struct LRUCache {
    capacity: usize,
    cache: HashMap<i32, Rc<RefCell<Node>>>,
    head: Option<Rc<RefCell<Node>>>, // Most recently used
    tail: Option<Rc<RefCell<Node>>>, // Least recently used
}

impl LRUCache {
    /// Create new LRU cache with given capacity
    pub fn new(capacity: usize) -> Self {
        LRUCache {
            capacity,
            cache: HashMap::new(),
            head: None,
            tail: None,
        }
    }

    /// Get value by key
    /// Time: O(1)
    /// Side effect: Moves accessed node to front (most recent)
    pub fn get(&mut self, key: i32) -> Option<i32> {
        if let Some(node) = self.cache.get(&key).cloned() {
            let value = node.borrow().value;
            self.move_to_front(node);
            Some(value)
        } else {
            None
        }
    }

    /// Put key-value pair
    /// Time: O(1)
    /// Side effect: Evicts LRU item if at capacity
    pub fn put(&mut self, key: i32, value: i32) {
        // If key exists, update and move to front
        if let Some(node) = self.cache.get(&key).cloned() {
            node.borrow_mut().value = value;
            self.move_to_front(node);
            return;
        }

        // Create new node
        let new_node = Node::new(key, value);

        // Add to front of list
        self.add_to_front(new_node.clone());

        // Add to hash table
        self.cache.insert(key, new_node);

        // Evict LRU if over capacity
        if self.cache.len() > self.capacity {
            if let Some(tail) = self.tail.clone() {
                let evict_key = tail.borrow().key;
                self.remove_node(tail);
                self.cache.remove(&evict_key);
            }
        }
    }

    /// Move node to front (mark as most recently used)
    fn move_to_front(&mut self, node: Rc<RefCell<Node>>) {
        self.remove_node(node.clone());
        self.add_to_front(node);
    }

    /// Add node to front of list
    fn add_to_front(&mut self, node: Rc<RefCell<Node>>) {
        match self.head.clone() {
            Some(old_head) => {
                // Link new node to old head
                node.borrow_mut().next = Some(old_head.clone());
                node.borrow_mut().prev = None;
                old_head.borrow_mut().prev = Some(node.clone());
                self.head = Some(node);
            }
            None => {
                // First node in list
                node.borrow_mut().prev = None;
                node.borrow_mut().next = None;
                self.head = Some(node.clone());
                self.tail = Some(node);
            }
        }
    }

    /// Remove node from list
    fn remove_node(&mut self, node: Rc<RefCell<Node>>) {
        let prev = node.borrow().prev.clone();
        let next = node.borrow().next.clone();

        match (prev, next) {
            (Some(p), Some(n)) => {
                // Middle node
                p.borrow_mut().next = Some(n.clone());
                n.borrow_mut().prev = Some(p);
            }
            (None, Some(n)) => {
                // Head node
                n.borrow_mut().prev = None;
                self.head = Some(n);
            }
            (Some(p), None) => {
                // Tail node
                p.borrow_mut().next = None;
                self.tail = Some(p);
            }
            (None, None) => {
                // Only node
                self.head = None;
                self.tail = None;
            }
        }
    }

    /// Display cache state (for debugging)
    pub fn display(&self) {
        print!("Cache (MRU → LRU): ");
        
        let mut current = self.head.clone();
        while let Some(node) = current {
            let n = node.borrow();
            print!("[{}:{}] ", n.key, n.value);
            current = n.next.clone();
        }
        println!();
    }
}

/// Simpler LRU implementation using VecDeque (for learning)
use std::collections::VecDeque;

pub struct SimpleLRU {
    capacity: usize,
    cache: HashMap<i32, i32>,
    order: VecDeque<i32>, // Front = MRU, Back = LRU
}

impl SimpleLRU {
    pub fn new(capacity: usize) -> Self {
        SimpleLRU {
            capacity,
            cache: HashMap::new(),
            order: VecDeque::new(),
        }
    }

    pub fn get(&mut self, key: i32) -> Option<i32> {
        if let Some(&value) = self.cache.get(&key) {
            // Move to front (remove then push)
            self.order.retain(|&k| k != key);
            self.order.push_front(key);
            Some(value)
        } else {
            None
        }
    }

    pub fn put(&mut self, key: i32, value: i32) {
        if self.cache.contains_key(&key) {
            // Update existing
            self.cache.insert(key, value);
            self.order.retain(|&k| k != key);
            self.order.push_front(key);
        } else {
            // Insert new
            if self.cache.len() >= self.capacity {
                // Evict LRU
                if let Some(lru_key) = self.order.pop_back() {
                    self.cache.remove(&lru_key);
                }
            }
            
            self.cache.insert(key, value);
            self.order.push_front(key);
        }
    }
}

fn main() {
    println!("=== LRU Cache Demonstration ===\n");
    
    let mut lru = LRUCache::new(3);
    
    println!("Operations:");
    println!("1. put(1, 10)");
    lru.put(1, 10);
    lru.display();
    
    println!("2. put(2, 20)");
    lru.put(2, 20);
    lru.display();
    
    println!("3. put(3, 30)");
    lru.put(3, 30);
    lru.display();
    
    println!("4. get(1) = {:?}", lru.get(1));
    lru.display();
    
    println!("5. put(4, 40) - should evict key 2");
    lru.put(4, 40);
    lru.display();
    
    println!("6. get(2) = {:?} (should be None)", lru.get(2));
    lru.display();
    
    println!("7. put(3, 33) - update existing");
    lru.put(3, 33);
    lru.display();
    
    println!("\n=== Visualization ===");
    println!("After operations, cache state:");
    println!("  MRU → [3:33] → [4:40] → [1:10] ← LRU");
    println!("  (If we add new item, [1:10] gets evicted)");
    
    // Test simple version
    println!("\n=== Simple LRU Version ===");
    let mut simple = SimpleLRU::new(2);
    simple.put(1, 1);
    simple.put(2, 2);
    println!("get(1): {:?}", simple.get(1));
    simple.put(3, 3); // Evicts key 2
    println!("get(2): {:?}", simple.get(2)); // None
    println!("get(3): {:?}", simple.get(3)); // Some(3)
}
---

### Pattern 5: Rolling Hash (Rabin-Karp Algorithm)

**Use Case:** Pattern matching, substring search, duplicate detection.

**Core Idea:** Compute hash for window, slide window in O(1) by removing old char and adding new char.

```
Rolling Hash Formula:

hash(s[i+1..j+1]) = (hash(s[i..j]) - s[i]×p^(j-i)) × p + s[j+1]
                     └─────────┬──────────┘   │      └────┬────┘
                          remove old        shift    add new

Example:
String: "abc" → "bcd"
p = 31, assume single-digit values for simplicity

hash("abc") = a×31² + b×31¹ + c×31⁰
hash("bcd") = (hash("abc") - a×31²) × 31 + d
```

/// Pattern 5: Rolling Hash for String Matching
/// 
/// Time: O(n + m) average, O(n*m) worst
/// Space: O(1)

const BASE: u64 = 31;
const MOD: u64 = 1_000_000_007;

/// Compute hash of string
fn compute_hash(s: &[char]) -> u64 {
    let mut hash = 0u64;
    let mut power = 1u64;
    
    for &ch in s.iter().rev() {
        hash = (hash + (ch as u64 * power) % MOD) % MOD;
        power = (power * BASE) % MOD;
    }
    
    hash
}

/// Rabin-Karp string matching
/// Find all occurrences of pattern in text
fn rabin_karp(text: &str, pattern: &str) -> Vec<usize> {
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    let n = text_chars.len();
    let m = pattern_chars.len();
    
    if m > n {
        return vec![];
    }
    
    let mut matches = Vec::new();
    
    // Compute pattern hash
    let pattern_hash = compute_hash(&pattern_chars);
    
    // Compute power: BASE^(m-1) mod MOD
    let mut power = 1u64;
    for _ in 0..m-1 {
        power = (power * BASE) % MOD;
    }
    
    // Compute initial window hash
    let mut window_hash = compute_hash(&text_chars[0..m]);
    
    // Check first window
    if window_hash == pattern_hash && &text_chars[0..m] == &pattern_chars[..] {
        matches.push(0);
    }
    
    // Slide window
    for i in 1..=n-m {
        // Remove leftmost character
        let old_char = text_chars[i - 1] as u64;
        window_hash = (window_hash + MOD - (old_char * power) % MOD) % MOD;
        
        // Shift and add new character
        window_hash = (window_hash * BASE) % MOD;
        let new_char = text_chars[i + m - 1] as u64;
        window_hash = (window_hash + new_char) % MOD;
        
        // Check if hashes match (with collision check)
        if window_hash == pattern_hash && 
           &text_chars[i..i+m] == &pattern_chars[..] {
            matches.push(i);
        }
    }
    
    matches
}

/// Find longest duplicate substring using rolling hash
/// 
/// Approach: Binary search on length + hash set
/// Time: O(n log n)
/// Space: O(n)
use std::collections::HashSet;

fn longest_duplicate_substring(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    // Binary search on length
    let mut left = 0;
    let mut right = n;
    let mut result_start = 0;
    let mut result_len = 0;
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        if let Some(start) = search_duplicate(&chars, mid) {
            // Found duplicate of length mid
            result_start = start;
            result_len = mid;
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    if result_len == 0 {
        String::new()
    } else {
        chars[result_start..result_start + result_len]
            .iter()
            .collect()
    }
}

/// Helper: Check if there's duplicate substring of given length
fn search_duplicate(chars: &[char], len: usize) -> Option<usize> {
    if len == 0 {
        return None;
    }
    
    let n = chars.len();
    if len > n {
        return None;
    }
    
    let mut seen: HashSet<u64> = HashSet::new();
    
    // Compute power
    let mut power = 1u64;
    for _ in 0..len-1 {
        power = (power * BASE) % MOD;
    }
    
    // Initial window hash
    let mut hash = compute_hash(&chars[0..len]);
    seen.insert(hash);
    
    // Slide window
    for i in 1..=n-len {
        // Rolling hash update
        let old_char = chars[i - 1] as u64;
        hash = (hash + MOD - (old_char * power) % MOD) % MOD;
        hash = (hash * BASE) % MOD;
        let new_char = chars[i + len - 1] as u64;
        hash = (hash + new_char) % MOD;
        
        // Check for duplicate
        if !seen.insert(hash) {
            return Some(i);
        }
    }
    
    None
}

/// Longest common substring using rolling hash
fn longest_common_substring(s1: &str, s2: &str) -> String {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();
    
    let n1 = chars1.len();
    let n2 = chars2.len();
    
    // Binary search on length
    let mut left = 0;
    let mut right = n1.min(n2);
    let mut result_len = 0;
    let mut result_start = 0;
    
    while left <= right {
        let mid = left + (right - left) / 2;
        
        // Get all hashes of length mid from s1
        let hashes1 = get_all_hashes(&chars1, mid);
        let hashes2 = get_all_hashes(&chars2, mid);
        
        // Find common hash
        if let Some((start, _)) = find_common_hash(&hashes1, &hashes2) {
            result_len = mid;
            result_start = start;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    if result_len == 0 {
        String::new()
    } else {
        chars1[result_start..result_start + result_len]
            .iter()
            .collect()
    }
}

fn get_all_hashes(chars: &[char], len: usize) -> Vec<(usize, u64)> {
    let n = chars.len();
    if len > n || len == 0 {
        return vec![];
    }
    
    let mut hashes = Vec::new();
    
    let mut power = 1u64;
    for _ in 0..len-1 {
        power = (power * BASE) % MOD;
    }
    
    let mut hash = compute_hash(&chars[0..len]);
    hashes.push((0, hash));
    
    for i in 1..=n-len {
        let old_char = chars[i - 1] as u64;
        hash = (hash + MOD - (old_char * power) % MOD) % MOD;
        hash = (hash * BASE) % MOD;
        let new_char = chars[i + len - 1] as u64;
        hash = (hash + new_char) % MOD;
        
        hashes.push((i, hash));
    }
    
    hashes
}

fn find_common_hash(
    hashes1: &[(usize, u64)],
    hashes2: &[(usize, u64)]
) -> Option<(usize, u64)> {
    let set2: HashSet<u64> = hashes2.iter().map(|&(_, h)| h).collect();
    
    for &(start, hash) in hashes1 {
        if set2.contains(&hash) {
            return Some((start, hash));
        }
    }
    
    None
}

fn main() {
    println!("=== Rabin-Karp Pattern Matching ===");
    let text = "ababcababc";
    let pattern = "abc";
    println!("Text: {}", text);
    println!("Pattern: {}", pattern);
    let matches = rabin_karp(text, pattern);
    println!("Matches at indices: {:?}\n", matches);
    
    println!("=== Longest Duplicate Substring ===");
    let s = "banana";
    println!("String: {}", s);
    println!("Longest duplicate: '{}'\n", longest_duplicate_substring(s));
    
    println!("=== Longest Common Substring ===");
    let s1 = "abcdefgh";
    let s2 = "xycdefwz";
    println!("String 1: {}", s1);
    println!("String 2: {}", s2);
    println!("Longest common: '{}'\n", longest_common_substring(s1, s2));
    
    // Visualization
    println!("=== Rolling Hash Visualization ===");
    println!("String: 'abc' → 'bcd'");
    println!("Window: [a b c] → [b c d]");
    println!("         ↑ remove    ↑ add");
    println!("\nHash update:");
    println!("1. Remove 'a': hash = (hash - a×31²) mod MOD");
    println!("2. Shift left: hash = hash × 31 mod MOD");
    println!("3. Add 'd':    hash = (hash + d) mod MOD");
    println!("\nTime: O(1) per slide!");
}

---

## 6. PERFORMANCE ANALYSIS

### Time Complexity Comparison

```
┌───────────────────┬──────────┬──────────┬──────────┐
│   Operation       │  Array   │ BST      │ Hash     │
├───────────────────┼──────────┼──────────┼──────────┤
│ Search            │  O(n)    │ O(log n) │ O(1)*    │
│ Insert            │  O(n)    │ O(log n) │ O(1)*    │
│ Delete            │  O(n)    │ O(log n) │ O(1)*    │
│ Min/Max           │  O(n)    │ O(log n) │ O(n)     │
│ Sorted Traversal  │  O(n)    │ O(n)     │ O(n lg n)│
│ Space             │  O(n)    │ O(n)     │ O(n)     │
└───────────────────┴──────────┴──────────┴──────────┘

* Average case with good hash function
```

### Load Factor Analysis

**Load Factor α = n/m** (elements / buckets)

```
Performance vs Load Factor (Chaining):

α       Expected Chain Length    Search Time
────────────────────────────────────────────
0.25           ~0.25                Excellent
0.50           ~0.50                Very Good
0.75           ~0.75                Good ← typical resize threshold
1.00           ~1.00                Acceptable
2.00           ~2.00                Degrading
5.00           ~5.00                Poor
```

**Resize Strategy:**
- Trigger: α > 0.75 (industry standard)
- New capacity: 2× current (exponential growth)
- Cost: O(n) rehashing
- Amortized: O(1) per insertion

---

### Space-Time Tradeoffs

```
Decision Tree:

Need O(1) lookup?
       │
   ┌───┴───┐
  Yes      No
   │        │
   ▼        ▼
Hash    Use Array/BST
Table      (save space)
   │
   ▼
Have memory?
   │
┌──┴──┐
│     │
Yes   No
│     │
▼     ▼
Chain Open
(safe) Addressing
       (compact)
```

---

## 7. LANGUAGE-SPECIFIC OPTIMIZATIONS

### Go: Map Best Practices

package main

import (
	"fmt"
)

// Go Map Best Practices and Idioms

// 1. Pre-allocate maps when size is known
func preallocateExample(n int) {
	// Bad: Default size, multiple reallocations
	m1 := make(map[int]int)
	for i := 0; i < n; i++ {
		m1[i] = i * 2
	}

	// Good: Pre-allocate with expected size
	m2 := make(map[int]int, n)
	for i := 0; i < n; i++ {
		m2[i] = i * 2
	}
	// Avoids reallocations, better performance
}

// 2. Safe access pattern with comma-ok idiom
func safeAccessPattern() {
	m := map[string]int{
		"apple":  5,
		"banana": 3,
	}

	// Bad: Zero value returned for missing key
	count := m["grape"] // Returns 0 (confusing)
	fmt.Println("Grapes:", count)

	// Good: Check existence
	if count, exists := m["grape"]; exists {
		fmt.Println("Grapes:", count)
	} else {
		fmt.Println("Grape not found")
	}
}

// 3. Default value pattern
func defaultValuePattern() {
	scores := make(map[string]int)

	// Pattern: Increment with default 0
	scores["Alice"]++
	scores["Alice"]++
	scores["Bob"]++

	fmt.Println(scores) // map[Alice:2 Bob:1]
}

// 4. Delete idiom
func deletePattern() {
	m := map[string]int{
		"a": 1,
		"b": 2,
		"c": 3,
	}

	// Safe to delete non-existent key
	delete(m, "d") // No error

	// Clear all entries (Go 1.21+)
	// clear(m) // Newer Go versions

	// Pre-1.21: Clear by making new map
	m = make(map[string]int)
}

// 5. Concurrent access (NOT thread-safe by default)
import "sync"

type SafeCounter struct {
	mu    sync.Mutex
	count map[string]int
}

func (c *SafeCounter) Inc(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.count[key]++
}

func (c *SafeCounter) Value(key string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.count[key]
}

// 6. Using sync.Map for concurrent access
func syncMapExample() {
	var m sync.Map

	// Store
	m.Store("key1", 100)
	m.Store("key2", 200)

	// Load
	if val, ok := m.Load("key1"); ok {
		fmt.Println("Value:", val)
	}

	// LoadOrStore
	actual, loaded := m.LoadOrStore("key3", 300)
	fmt.Println("Loaded:", loaded, "Value:", actual)

	// Range (iterate)
	m.Range(func(key, value interface{}) bool {
		fmt.Printf("%v: %v\n", key, value)
		return true // continue iteration
	})
}

// 7. Map as set
func mapAsSet() {
	// Using map[T]bool
	set := make(map[int]bool)
	set[1] = true
	set[2] = true
	set[3] = true

	if set[2] {
		fmt.Println("2 is in set")
	}

	// Using map[T]struct{} (zero memory overhead)
	type void struct{}
	var member void

	betterSet := make(map[int]void)
	betterSet[1] = member
	betterSet[2] = member

	if _, exists := betterSet[2]; exists {
		fmt.Println("2 is in better set")
	}
}

// 8. Custom hash key (must be comparable)
type Point struct {
	X, Y int
}

func customKeyExample() {
	visited := make(map[Point]bool)
	
	visited[Point{1, 2}] = true
	visited[Point{3, 4}] = true

	if visited[Point{1, 2}] {
		fmt.Println("Point (1,2) visited")
	}
}

// 9. Copy map (must be manual)
func copyMap(original map[string]int) map[string]int {
	copy := make(map[string]int, len(original))
	for k, v := range original {
		copy[k] = v
	}
	return copy
}

// 10. Common pattern: Frequency counter
func frequencyCounter(items []string) map[string]int {
	freq := make(map[string]int)
	
	for _, item := range items {
		freq[item]++
	}
	
	return freq
}

// 11. Pattern: Group by key
func groupBy(items []string) map[byte][]string {
	groups := make(map[byte][]string)
	
	for _, item := range items {
		if len(item) > 0 {
			firstChar := item[0]
			groups[firstChar] = append(groups[firstChar], item)
		}
	}
	
	return groups
}

// 12. Performance tip: Avoid unnecessary allocations
func efficientUpdate() {
	type Record struct {
		Count int
		Items []string
	}

	m := make(map[string]*Record)

	// Bad: Creates new Record each time
	// m["key"] = &Record{Count: m["key"].Count + 1}

	// Good: Update in place
	if rec, exists := m["key"]; exists {
		rec.Count++
	} else {
		m["key"] = &Record{Count: 1}
	}
}

// 13. Nil map vs empty map
func nilMapBehavior() {
	var nilMap map[string]int  // nil map
	emptyMap := make(map[string]int) // empty map

	// Reading from nil map: OK (returns zero value)
	_ = nilMap["key"] // 0

	// Writing to nil map: PANIC!
	// nilMap["key"] = 1 // panic: assignment to entry in nil map

	// Writing to empty map: OK
	emptyMap["key"] = 1
}

func main() {
	fmt.Println("=== Go Map Best Practices ===\n")

	fmt.Println("1. Safe Access Pattern:")
	safeAccessPattern()

	fmt.Println("\n2. Default Value Pattern:")
	defaultValuePattern()

	fmt.Println("\n3. Map as Set:")
	mapAsSet()

	fmt.Println("\n4. Custom Key:")
	customKeyExample()

	fmt.Println("\n5. Frequency Counter:")
	items := []string{"apple", "banana", "apple", "cherry", "banana", "apple"}
	fmt.Println(frequencyCounter(items))

	fmt.Println("\n6. Group By:")
	words := []string{"apple", "apricot", "banana", "blueberry", "cherry"}
	fmt.Println(groupBy(words))

	fmt.Println("\n=== Key Takeaways ===")
	fmt.Println("• Pre-allocate when size known")
	fmt.Println("• Use comma-ok idiom for safe access")
	fmt.Println("• Maps are NOT thread-safe by default")
	fmt.Println("• Use sync.Map or mutex for concurrency")
	fmt.Println("• map[T]struct{} for zero-overhead sets")
	fmt.Println("• Never write to nil map")
}

---

## 8. MENTAL MODELS FOR MASTERY

### Model 1: The Library Analogy

```
Linear Search Library:
Books on shelves A-Z
To find "Moby Dick" → Walk through every shelf
Time: Proportional to number of books

Hash Table Library:
Compute: hash("Moby Dick") = Shelf 42
Walk directly to Shelf 42
Time: Constant (one lookup)
```

### Model 2: The Pigeonhole Principle

**When designing hash functions:**

```
n items → m buckets

If n > m: Collisions GUARANTEED (Pigeonhole Principle)

Goal: Distribute items uniformly to minimize clustering
```

### Model 3: The Trade-off Spectrum

```
        Space ←────────────→ Time
                     │
     Arrays ───────────────── Hash Tables
     (compact)               (fast lookup)
                     │
                     ↓
              Choose based on:
              • Access pattern
              • Memory constraints
              • Required operations
```

---

## 9. ADVANCED TOPICS

### Consistent Hashing (Distributed Systems)

**Problem:** Distribute keys across n servers. When server added/removed, minimize reassignment.

**Traditional Approach:**
```
server = hash(key) % n

Problem: If n changes, almost ALL keys reassign!
```

**Consistent Hashing:**
```
Conceptual Model: Hash ring [0, 2^32)

┌────────────────────────────┐
│         Hash Ring          │
│                            │
│    S1 (100)                │
│       ↓                    │
│   ●───────●  S2 (250)      │
│  /         \               │
│ ●           ●  S3 (350)    │
│  \         /               │
│   ●───────●                │
│       ↑                    │
│    Keys hash to ring       │
│    Assign to next server   │
└────────────────────────────┘

Key at position 120 → Server S2 (next clockwise)
```

**Benefits:**
- Adding/removing server: Only K/n keys reassign (K = total keys)
- Traditional: Almost all K keys reassign

---

### Perfect Hashing (Theory)

**Perfect Hash Function:** Zero collisions for static set.

**Minimal Perfect Hash:** Zero collisions + exactly n buckets for n items.

**Use Cases:**
- Compilers (keyword lookup)
- Databases (static catalogs)
- Read-only caches

**Construction:** Complex, requires knowledge of all keys upfront.

---

## 10. COMPLETE PROBLEM PATTERNS SUMMARY

```
┌─────────────────────────────────────────────────────────┐
│                HASH TABLE PATTERN MAP                   │
├─────────────────────┬───────────────────────────────────┤
│ Pattern             │ When to Use                       │
├─────────────────────┼───────────────────────────────────┤
│ Frequency Count     │ Count occurrences, find          │
│                     │ duplicates, mode                  │
├─────────────────────┼───────────────────────────────────┤
│ Index Mapping       │ Two sum, complement search,       │
│ (Two Sum)           │ pair finding                      │
├─────────────────────┼───────────────────────────────────┤
│ Sliding Window +    │ Longest substring variants,       │
│ Hash                │ anagram finding                   │
├─────────────────────┼───────────────────────────────────┤
│ Prefix Sum + Hash   │ Subarray sum problems,            │
│                     │ continuous sums                   │
├─────────────────────┼───────────────────────────────────┤
│ Rolling Hash        │ Pattern matching, duplicate       │
│                     │ substring search                  │
├─────────────────────┼───────────────────────────────────┤
│ Group/Partition     │ Group anagrams, categorize        │
│                     │ by property                       │
├─────────────────────┼───────────────────────────────────┤
│ Cache Design        │ LRU, LFU, limited resources       │
│                     │ with fast access                  │
└─────────────────────┴───────────────────────────────────┘
```

---

## 11. CRITICAL INSIGHTS FOR MASTERY

### Insight 1: Hash Function Quality

**Bad hash function symptoms:**
- Many collisions
- Clustering in buckets
- Degraded to O(n) performance

**Good hash function properties:**
```
1. Deterministic
2. Uniform distribution
3. Fast to compute
4. Avalanche effect (small input change → large hash change)
```

### Insight 2: When NOT to Use Hash Tables

```
Decision Flowchart:

Need ordered data?
       │
      Yes → Use BST/TreeMap
       │
      No
       ▼
Need range queries?
       │
      Yes → Use BST
       │
      No
       ▼
Need min/max frequently?
       │
      Yes → Use Heap
       │
      No
       ▼
   Use Hash Table!
```

### Insight 3: The Hidden Cost of Resizing

```
Insertion Sequence Analysis:

Capacity: 4, Load Factor Trigger: 0.75

Insert #1: O(1) ────────────────────────┐
Insert #2: O(1)                         │
Insert #3: O(1)                         ├─ Fast
Insert #4: O(n) RESIZE! (rehash all)   ─┘
Insert #5: O(1)
Insert #6: O(1)
Insert #7: O(1)
Insert #8: O(n) RESIZE!

Amortized: O(1) per insertion
           (expensive ops spread across many cheap ops)
```

---

## 12. FINAL WISDOM

### The Hash Table Mindset

**Question to ask:** "Do I need direct access to elements by a unique identifier?"

If YES → Hash table is likely optimal

**Key Recognition Patterns:**
1. "Find pair/triplet that..." → Index mapping
2. "Count frequency of..." → Frequency counter
3. "Group by property..." → Hash grouping
4. "Longest/shortest substring with..." → Sliding window + hash
5. "Check if subarray exists with sum..." → Prefix sum + hash

### Complexity Analysis Framework

```
For any hash table solution:

Time Complexity:
├─ Average Case: O(1) operations × n iterations = O(n)
└─ Worst Case: O(n) collisions × n iterations = O(n²)

Space Complexity:
└─ O(n) for storing n elements
   + O(collision overhead) if chaining
```

### The 1% Mindset

To reach the top 1%, you must:

1. **Recognize patterns instantly** (< 30 seconds)
2. **Choose optimal collision strategy** for the problem
3. **Implement without bugs** in 10-15 minutes
4. **Analyze trade-offs** between solutions
5. **Optimize further** (space constants, cache locality)

---

**Remember:** Hash tables transform "search for X" from a journey through data into a direct mathematical computation. Master the hash function, and you master instant access.

This guide covers the complete landscape. Study each pattern deeply, implement in your language of choice, and build the intuition for when each technique applies. The difference between good and great is recognizing the pattern before writing the first line of code.