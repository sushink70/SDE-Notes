# Comprehensive Guide to HashMap in Rust

HashMap is one of the most commonly used data structures in Rust, providing efficient key-value storage with average O(1) lookup time. This guide covers everything you need to know about HashMap.

## Table of Contents
1. Basic Concepts
2. Creating HashMaps
3. Inserting and Accessing Data
4. Updating Values
5. Removing Entries
6. Iteration
7. Ownership and Borrowing
8. Entry API
9. Custom Hash Functions
10. Performance Considerations
11. Common Patterns and Best Practices

## 1. Basic Concepts

HashMap stores data as key-value pairs where each key is unique. It uses hashing to determine where to store each entry, providing fast lookups.

```rust
use std::collections::HashMap;

// HashMap<K, V> where K is the key type and V is the value type
let map: HashMap<String, i32> = HashMap::new();
```

## 2. Creating HashMaps

### Using `new()`
```rust
use std::collections::HashMap;

let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Yellow"), 50);
```

### Using `with_capacity()`
```rust
// Pre-allocate space for performance
let mut map = HashMap::with_capacity(10);
```

### From Iterator
```rust
let teams = vec![String::from("Blue"), String::from("Yellow")];
let initial_scores = vec![10, 50];

let scores: HashMap<_, _> = teams.into_iter()
    .zip(initial_scores.into_iter())
    .collect();
```

### Using `from()` (Rust 2021+)
```rust
let map = HashMap::from([
    ("key1", "value1"),
    ("key2", "value2"),
]);
```

## 3. Inserting and Accessing Data

### Insert
```rust
let mut map = HashMap::new();
map.insert("name", "Alice");
map.insert("age", "30");
```

### Get (returns Option)
```rust
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);

// Returns Option<&V>
let score = scores.get("Blue"); // Some(&10)
let score = scores.get("Red");  // None

// With pattern matching
match scores.get("Blue") {
    Some(score) => println!("Score: {}", score),
    None => println!("Team not found"),
}

// Using unwrap_or
let score = scores.get("Red").unwrap_or(&0);
```

### Get Mutable Reference
```rust
let mut map = HashMap::new();
map.insert("count", 1);

if let Some(value) = map.get_mut("count") {
    *value += 1;
}
```

### Index Access (panics if key doesn't exist)
```rust
let mut map = HashMap::new();
map.insert("key", "value");

let value = &map["key"]; // Returns &V, panics if key not found
```

## 4. Updating Values

### Overwriting
```rust
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Blue"), 25); // Overwrites previous value
```

### Only Insert if Key Doesn't Exist
```rust
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);

scores.entry(String::from("Blue")).or_insert(50);    // Won't insert
scores.entry(String::from("Yellow")).or_insert(50);  // Will insert
```

### Update Based on Old Value
```rust
let text = "hello world wonderful world";
let mut map = HashMap::new();

for word in text.split_whitespace() {
    let count = map.entry(word).or_insert(0);
    *count += 1;
}
// map = {"hello": 1, "world": 2, "wonderful": 1}
```

## 5. Removing Entries

### Remove
```rust
let mut map = HashMap::new();
map.insert("key", "value");

// Returns Option<V>
let removed = map.remove("key"); // Some("value")
let removed = map.remove("nonexistent"); // None
```

### Remove Entry (returns key and value)
```rust
let mut map = HashMap::new();
map.insert("key", "value");

// Returns Option<(K, V)>
let removed = map.remove_entry("key"); // Some(("key", "value"))
```

### Clear All
```rust
let mut map = HashMap::new();
map.insert("key1", "value1");
map.insert("key2", "value2");

map.clear(); // Removes all entries
```

### Retain
```rust
let mut map = HashMap::from([
    ("a", 1),
    ("b", 2),
    ("c", 3),
]);

// Keep only entries where value > 1
map.retain(|_key, value| *value > 1);
// map = {"b": 2, "c": 3}
```

## 6. Iteration

### Iterate Over Key-Value Pairs
```rust
let mut map = HashMap::new();
map.insert("color", "red");
map.insert("size", "large");

for (key, value) in &map {
    println!("{}: {}", key, value);
}
```

### Iterate Over Keys
```rust
for key in map.keys() {
    println!("{}", key);
}
```

### Iterate Over Values
```rust
for value in map.values() {
    println!("{}", value);
}
```

### Iterate Over Mutable Values
```rust
for value in map.values_mut() {
    *value = value.to_uppercase();
}
```

### Consuming Iteration
```rust
let map = HashMap::from([("a", 1), ("b", 2)]);

for (key, value) in map { // map is moved here
    println!("{}: {}", key, value);
}
// map is no longer available
```

## 7. Ownership and Borrowing

### Types with Copy Trait
```rust
let mut scores = HashMap::new();
let blue = 10;
scores.insert(String::from("Blue"), blue);

// blue is still valid (i32 implements Copy)
println!("blue: {}", blue);
```

### Types without Copy Trait
```rust
let mut map = HashMap::new();
let key = String::from("favorite");
let value = String::from("color");

map.insert(key, value);
// key and value are moved into the map
// println!("{}", key); // Error: key was moved
```

### Using References
```rust
let mut map = HashMap::new();
let key = String::from("favorite");
let value = String::from("color");

// HashMap will not own the data
// The values must live as long as the HashMap
map.insert(&key, &value);

println!("key: {}", key); // Still valid
```

## 8. Entry API

The Entry API provides efficient ways to work with HashMap entries without multiple lookups.

### Basic Entry Operations
```rust
use std::collections::hash_map::Entry;

let mut map = HashMap::new();

// or_insert returns a mutable reference
map.entry("key").or_insert("default");

// or_insert_with uses a closure (lazy evaluation)
map.entry("key").or_insert_with(|| expensive_computation());

// or_insert_with_key provides access to the key
map.entry("key").or_insert_with_key(|k| format!("default for {}", k));
```

### Pattern Matching on Entry
```rust
let mut map = HashMap::new();
map.insert("a", 1);

match map.entry("a") {
    Entry::Occupied(entry) => {
        println!("Occupied: {:?}", entry.key());
        // Can modify or remove
        *entry.into_mut() += 1;
    }
    Entry::Vacant(entry) => {
        println!("Vacant: {:?}", entry.key());
        entry.insert(42);
    }
}
```

### Occupied Entry Methods
```rust
let mut map = HashMap::from([("key", 1)]);

if let Entry::Occupied(mut entry) = map.entry("key") {
    entry.insert(2);           // Replace value
    entry.get();               // Get reference to value
    entry.get_mut();           // Get mutable reference
    entry.remove();            // Remove and return value
    entry.remove_entry();      // Remove and return (key, value)
}
```

### Vacant Entry Methods
```rust
let mut map = HashMap::new();

if let Entry::Vacant(entry) = map.entry("key") {
    entry.insert("value");     // Insert and return mutable reference
}
```

### Advanced Entry Patterns
```rust
// Modify existing or insert new
let count = map.entry("word").or_insert(0);
*count += 1;

// Complex update logic
map.entry("key")
    .and_modify(|v| *v += 1)
    .or_insert(1);
```

## 9. Custom Hash Functions

### Using a Different Hasher
```rust
use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use std::collections::hash_map::RandomState;

// Default hasher (SipHash for security)
let map: HashMap<i32, String> = HashMap::new();

// Custom hasher
use std::hash::Hasher;

#[derive(Default)]
struct MyHasher {
    state: u64,
}

impl Hasher for MyHasher {
    fn finish(&self) -> u64 {
        self.state
    }
    
    fn write(&mut self, bytes: &[u8]) {
        for &byte in bytes {
            self.state = self.state.wrapping_add(byte as u64);
        }
    }
}

type MyBuildHasher = BuildHasherDefault<MyHasher>;
let map: HashMap<i32, String, MyBuildHasher> = HashMap::default();
```

### Using FxHashMap (faster but not DOS-resistant)
```rust
// Add to Cargo.toml: rustc-hash = "1.1"
use rustc_hash::FxHashMap;

let mut map = FxHashMap::default();
map.insert("key", "value");
```

### Implementing Hash for Custom Types
```rust
use std::hash::{Hash, Hasher};

#[derive(Eq, PartialEq)]
struct Person {
    id: u32,
    name: String,
}

impl Hash for Person {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
        // Don't hash name if id is unique
    }
}

let mut map = HashMap::new();
let person = Person { id: 1, name: String::from("Alice") };
map.insert(person, "data");
```

## 10. Performance Considerations

### Capacity and Resizing
```rust
let mut map = HashMap::new();
println!("Capacity: {}", map.capacity()); // 0

map.insert("key", "value");
println!("Capacity: {}", map.capacity()); // 3 (or similar)

// Pre-allocate to avoid resizing
let mut map = HashMap::with_capacity(100);

// Reserve additional capacity
map.reserve(50);

// Shrink capacity to fit
map.shrink_to_fit();

// Shrink to at least this capacity
map.shrink_to(10);
```

### Choosing Key Types
```rust
// Good key types: small, cheap to hash and compare
// - Integers (i32, u64, etc.)
// - Small fixed-size types
// - References to strings (&str)

// Bad key types: large, expensive to hash
// - Very large structs
// - String (use &str if possible)

// Using &str as keys (with owned values)
let mut map: HashMap<&str, String> = HashMap::new();
map.insert("key", String::from("value"));
```

### Load Factor
```rust
// HashMap automatically resizes when load factor > 0.875
// Load factor = len() / capacity()

let mut map = HashMap::with_capacity(10);
// Will resize after ~8 insertions
```

## 11. Common Patterns and Best Practices

### Grouping Values
```rust
let data = vec![("a", 1), ("b", 2), ("a", 3), ("b", 4)];
let mut grouped: HashMap<&str, Vec<i32>> = HashMap::new();

for (key, value) in data {
    grouped.entry(key).or_insert(vec![]).push(value);
}
// {"a": [1, 3], "b": [2, 4]}
```

### Counting Occurrences
```rust
let words = vec!["apple", "banana", "apple", "cherry", "banana", "apple"];
let mut counts = HashMap::new();

for word in words {
    *counts.entry(word).or_insert(0) += 1;
}
```

### Caching/Memoization
```rust
use std::collections::HashMap;

struct Fibonacci {
    cache: HashMap<u64, u64>,
}

impl Fibonacci {
    fn new() -> Self {
        let mut cache = HashMap::new();
        cache.insert(0, 0);
        cache.insert(1, 1);
        Fibonacci { cache }
    }
    
    fn calculate(&mut self, n: u64) -> u64 {
        if let Some(&result) = self.cache.get(&n) {
            return result;
        }
        
        let result = self.calculate(n - 1) + self.calculate(n - 2);
        self.cache.insert(n, result);
        result
    }
}
```

### Merging HashMaps
```rust
let mut map1 = HashMap::from([("a", 1), ("b", 2)]);
let map2 = HashMap::from([("b", 3), ("c", 4)]);

// Simple merge (overwrites duplicates)
map1.extend(map2);

// Merge with custom logic
let mut map1 = HashMap::from([("a", 1), ("b", 2)]);
let map2 = HashMap::from([("b", 3), ("c", 4)]);

for (key, value) in map2 {
    map1.entry(key)
        .and_modify(|v| *v += value)
        .or_insert(value);
}
```

### Default Values with entry
```rust
#[derive(Default)]
struct Stats {
    count: i32,
    sum: i32,
}

let mut stats_map: HashMap<String, Stats> = HashMap::new();

// Automatically creates default if missing
stats_map.entry("player1".to_string())
    .or_default()
    .count += 1;
```

### Checking Membership
```rust
let map = HashMap::from([("a", 1), ("b", 2)]);

if map.contains_key("a") {
    println!("Found!");
}

// Length
println!("Length: {}", map.len());

// Is empty
if map.is_empty() {
    println!("Map is empty");
}
```

### Draining
```rust
let mut map = HashMap::from([("a", 1), ("b", 2), ("c", 3)]);

// Drain all elements
for (key, value) in map.drain() {
    println!("{}: {}", key, value);
}
// map is now empty but retains capacity
```

### Error Handling Patterns
```rust
fn get_config_value(key: &str) -> Result<String, String> {
    let config = HashMap::from([
        ("host", "localhost"),
        ("port", "8080"),
    ]);
    
    config.get(key)
        .map(|s| s.to_string())
        .ok_or_else(|| format!("Key '{}' not found", key))
}
```

## Key Requirements for HashMap Keys

For a type to be used as a HashMap key, it must implement:
- `Eq` - for equality comparison
- `Hash` - for computing hash values

```rust
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

#[derive(Eq, PartialEq, Hash)]
struct CustomKey {
    id: u32,
    category: String,
}

let mut map = HashMap::new();
let key = CustomKey { 
    id: 1, 
    category: String::from("A") 
};
map.insert(key, "value");
```

## Thread Safety

HashMap is not thread-safe. For concurrent access, use:
- `Arc<Mutex<HashMap<K, V>>>` for multiple readers/writers
- `Arc<RwLock<HashMap<K, V>>>` for many readers, few writers
- `DashMap` crate for concurrent HashMap

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let map = Arc::new(Mutex::new(HashMap::new()));
let map_clone = Arc::clone(&map);

thread::spawn(move || {
    let mut m = map_clone.lock().unwrap();
    m.insert("key", "value");
});
```

This comprehensive guide covers all major aspects of HashMap in Rust. Practice these patterns to become proficient with this essential data structure.