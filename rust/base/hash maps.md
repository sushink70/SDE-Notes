# Comprehensive Guide to Storing Keys with Associated Values in Hash Maps in Rust

## Table of Contents
1. Introduction to Hash Maps
2. Creating and Initializing Hash Maps
3. Inserting and Updating Values
4. Retrieving Values
5. Ownership and Borrowing in Hash Maps
6. Iteration Patterns
7. Hash Map Performance and Internal Mechanics
8. Custom Types as Keys
9. Advanced Patterns and Techniques
10. Real-World Use Cases
11. Common Pitfalls and Best Practices

---

## 1. Introduction to Hash Maps

A HashMap in Rust is a collection that stores key-value pairs using a hashing algorithm for fast lookup, insertion, and deletion. It's part of the standard library's `std::collections` module.

```rust
use std::collections::HashMap;

// Basic structure: HashMap<K, V>
// K = Key type (must implement Eq and Hash)
// V = Value type (can be any type)
```

### Why Hash Maps Matter

Hash maps provide O(1) average-case complexity for insertion, deletion, and lookup operations, making them ideal for scenarios requiring fast data access by key.

**Hidden Knowledge:** Rust's HashMap uses a cryptographically secure hashing algorithm (SipHash 1-3) by default to prevent hash collision attacks (HashDoS). This makes it slightly slower than some other languages' hash maps but more secure.

---

## 2. Creating and Initializing Hash Maps

### Basic Creation

```rust
use std::collections::HashMap;

fn main() {
    // Method 1: Using new()
    let mut scores: HashMap<String, i32> = HashMap::new();
    
    // Method 2: With type inference
    let mut scores = HashMap::new();
    scores.insert(String::from("Blue"), 10); // Type inferred here
    
    // Method 3: With capacity hint (optimization)
    let mut scores: HashMap<String, i32> = HashMap::with_capacity(10);
}
```

### Creating from Iterators

```rust
use std::collections::HashMap;

fn main() {
    // From vectors using collect()
    let teams = vec![String::from("Blue"), String::from("Red")];
    let initial_scores = vec![10, 50];
    
    let scores: HashMap<_, _> = teams.iter()
        .zip(initial_scores.iter())
        .collect();
    
    // Using from_iter
    let scores: HashMap<_, _> = HashMap::from_iter([
        ("Blue", 10),
        ("Red", 50),
    ]);
    
    // Using from() with arrays (Rust 2021+)
    let scores = HashMap::from([
        ("Blue", 10),
        ("Red", 50),
    ]);
}
```

**Hidden Knowledge:** When using `collect()` to create a HashMap, you often need the turbofish syntax `HashMap<_, _>` because `collect()` can create many different collection types. The underscores let the compiler infer the key and value types.

---

## 3. Inserting and Updating Values

### Basic Insertion

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();
    
    // insert() returns Option<V> - the old value if key existed
    let old_value = scores.insert(String::from("Blue"), 10);
    println!("{:?}", old_value); // None
    
    let old_value = scores.insert(String::from("Blue"), 25);
    println!("{:?}", old_value); // Some(10)
}
```

### Conditional Insertion - Entry API

The Entry API is one of Rust's most powerful HashMap features:

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();
    
    // Only insert if key doesn't exist
    scores.entry(String::from("Blue")).or_insert(10);
    scores.entry(String::from("Blue")).or_insert(50); // Doesn't overwrite
    
    println!("{:?}", scores); // {"Blue": 10}
}
```

### Advanced Entry API Patterns

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();
    
    // or_insert_with: lazy evaluation
    scores.entry(String::from("Blue"))
        .or_insert_with(|| {
            println!("Computing expensive default");
            expensive_computation()
        });
    
    // and_modify: update existing value
    scores.entry(String::from("Blue"))
        .and_modify(|score| *score += 10)
        .or_insert(50);
    
    // or_insert returns mutable reference
    let score = scores.entry(String::from("Red")).or_insert(0);
    *score += 10;
    
    println!("{:?}", scores);
}

fn expensive_computation() -> i32 {
    42
}
```

**Hidden Knowledge:** The Entry API is designed to avoid double-lookup. Without it, checking if a key exists and then inserting would require two hash computations. The Entry API does it in one.

### Updating Based on Old Value

```rust
use std::collections::HashMap;

fn count_words(text: &str) -> HashMap<String, usize> {
    let mut word_count = HashMap::new();
    
    for word in text.split_whitespace() {
        let count = word_count.entry(word.to_string()).or_insert(0);
        *count += 1;
    }
    
    word_count
}

fn main() {
    let text = "hello world hello rust world";
    let counts = count_words(text);
    println!("{:?}", counts);
}
```

---

## 4. Retrieving Values

### Basic Retrieval

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::from([
        (String::from("Blue"), 10),
        (String::from("Red"), 50),
    ]);
    
    // get() returns Option<&V>
    match scores.get("Blue") {
        Some(score) => println!("Blue team score: {}", score),
        None => println!("Blue team not found"),
    }
    
    // Using if let
    if let Some(score) = scores.get("Blue") {
        println!("Score: {}", score);
    }
    
    // copied() for Copy types
    let score: Option<i32> = scores.get("Blue").copied();
    
    // cloned() for Clone types
    let team: Option<String> = scores.get_key_value("Blue")
        .map(|(k, _)| k.clone());
}
```

### Direct Access with Indexing

```rust
use std::collections::HashMap;

fn main() {
    let scores = HashMap::from([
        (String::from("Blue"), 10),
    ]);
    
    // Using index notation - panics if key doesn't exist!
    let score = &scores[&String::from("Blue")];
    println!("{}", score);
    
    // This would panic:
    // let score = &scores[&String::from("Green")];
}
```

**Hidden Knowledge:** Using index notation `[]` on a HashMap is generally discouraged in production code because it panics on missing keys. Always prefer `get()` which returns an `Option`.

### Getting Mutable References

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::from([
        (String::from("Blue"), 10),
    ]);
    
    // get_mut() returns Option<&mut V>
    if let Some(score) = scores.get_mut(&String::from("Blue")) {
        *score += 5;
    }
    
    println!("{:?}", scores); // {"Blue": 15}
}
```

### Removing Values

```rust
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::from([
        (String::from("Blue"), 10),
        (String::from("Red"), 50),
    ]);
    
    // remove() returns Option<V>
    let removed = scores.remove(&String::from("Blue"));
    println!("Removed: {:?}", removed); // Some(10)
    
    // remove_entry() returns Option<(K, V)>
    let removed = scores.remove_entry(&String::from("Red"));
    println!("Removed: {:?}", removed); // Some(("Red", 50))
    
    // retain() - keep only entries matching predicate
    scores.insert(String::from("Green"), 30);
    scores.insert(String::from("Yellow"), 15);
    scores.retain(|_key, value| *value >= 20);
    println!("{:?}", scores); // Only scores >= 20 remain
}
```

---

## 5. Ownership and Borrowing in Hash Maps

### Ownership Transfer

```rust
use std::collections::HashMap;

fn main() {
    let mut map = HashMap::new();
    
    let key = String::from("color");
    let value = String::from("blue");
    
    // Both key and value are moved into the map
    map.insert(key, value);
    
    // This would error - values are moved:
    // println!("{}", key);
    // println!("{}", value);
    
    // For Copy types, no move occurs
    let mut numbers = HashMap::new();
    let k = 1;
    let v = 100;
    numbers.insert(k, v);
    println!("{}, {}", k, v); // Works fine - i32 is Copy
}
```

### Borrowing with References

```rust
use std::collections::HashMap;

fn main() {
    let mut map: HashMap<&str, i32> = HashMap::new();
    
    // String slices don't transfer ownership
    map.insert("color", 1);
    
    // But be careful with lifetimes
    let key = String::from("color");
    // This would error - key doesn't live long enough:
    // map.insert(&key, 2);
}
```

**Hidden Knowledge:** When using references as keys or values, the HashMap doesn't own the data. The original data must outlive the HashMap, which the borrow checker enforces through lifetimes.

### Lifetime Considerations

```rust
use std::collections::HashMap;

// HashMap with lifetime parameter
fn create_map<'a>(keys: &'a [&str]) -> HashMap<&'a str, i32> {
    let mut map = HashMap::new();
    for (i, &key) in keys.iter().enumerate() {
        map.insert(key, i as i32);
    }
    map
}

fn main() {
    let keys = vec!["one", "two", "three"];
    let map = create_map(&keys);
    println!("{:?}", map);
}
```

### Interior Mutability Patterns

```rust
use std::collections::HashMap;
use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    // Using Rc for shared ownership
    let mut map: HashMap<String, Rc<String>> = HashMap::new();
    
    let value = Rc::new(String::from("shared"));
    map.insert(String::from("key1"), Rc::clone(&value));
    map.insert(String::from("key2"), Rc::clone(&value));
    
    println!("Reference count: {}", Rc::strong_count(&value)); // 3
    
    // Using RefCell for interior mutability
    let mut cache: HashMap<String, RefCell<Vec<i32>>> = HashMap::new();
    cache.insert(String::from("data"), RefCell::new(vec![1, 2, 3]));
    
    // Can mutate through shared reference
    if let Some(cell) = cache.get("data") {
        cell.borrow_mut().push(4);
    }
    
    println!("{:?}", cache.get("data").unwrap().borrow());
}
```

---

## 6. Iteration Patterns

### Basic Iteration

```rust
use std::collections::HashMap;

fn main() {
    let scores = HashMap::from([
        (String::from("Blue"), 10),
        (String::from("Red"), 50),
    ]);
    
    // Iterate over references to key-value pairs
    for (key, value) in &scores {
        println!("{}: {}", key, value);
    }
    
    // Iterate over keys only
    for key in scores.keys() {
        println!("Key: {}", key);
    }
    
    // Iterate over values only
    for value in scores.values() {
        println!("Value: {}", value);
    }
    
    // Mutable iteration
    let mut scores = scores;
    for (_key, value) in &mut scores {
        *value *= 2;
    }
    
    // Consuming iteration - takes ownership
    for (key, value) in scores {
        println!("{}: {}", key, value);
        // scores is consumed here
    }
}
```

**Hidden Knowledge:** HashMap iteration order is not guaranteed and will appear random. It depends on the internal hashing algorithm and may change between runs. Never rely on iteration order.

### Advanced Iteration Patterns

```rust
use std::collections::HashMap;

fn main() {
    let scores = HashMap::from([
        (String::from("Blue"), 10),
        (String::from("Red"), 50),
        (String::from("Green"), 30),
    ]);
    
    // Filter and collect
    let high_scores: HashMap<_, _> = scores.iter()
        .filter(|(_, &score)| score > 20)
        .map(|(k, v)| (k.clone(), *v))
        .collect();
    
    // Transform values
    let doubled: HashMap<_, _> = scores.iter()
        .map(|(k, v)| (k.clone(), v * 2))
        .collect();
    
    // Find maximum value
    let max_score = scores.values().max();
    println!("Max score: {:?}", max_score);
    
    // Find key with maximum value
    let max_entry = scores.iter()
        .max_by_key(|(_k, &v)| v);
    if let Some((team, score)) = max_entry {
        println!("Highest scoring team: {} with {}", team, score);
    }
}
```

### Parallel Iteration with Rayon

```rust
use std::collections::HashMap;
// Note: This requires adding rayon to Cargo.toml
// rayon = "1.7"

#[cfg(feature = "rayon")]
fn parallel_example() {
    use rayon::prelude::*;
    
    let scores: HashMap<i32, i32> = (0..1000)
        .map(|i| (i, i * 2))
        .collect();
    
    // Parallel iteration
    let sum: i32 = scores.par_iter()
        .map(|(_, &v)| v)
        .sum();
    
    println!("Sum: {}", sum);
}
```

---

## 7. Hash Map Performance and Internal Mechanics

### Understanding Hashing

```rust
use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

fn main() {
    // See how a value is hashed
    let mut hasher = DefaultHasher::new();
    "hello".hash(&mut hasher);
    let hash_value = hasher.finish();
    println!("Hash of 'hello': {}", hash_value);
}
```

### Capacity and Memory Management

```rust
use std::collections::HashMap;

fn main() {
    let mut map: HashMap<i32, i32> = HashMap::new();
    
    println!("Initial capacity: {}", map.capacity());
    
    // Pre-allocate to avoid reallocations
    map.reserve(100);
    println!("After reserve(100): {}", map.capacity());
    
    // Insert many elements
    for i in 0..50 {
        map.insert(i, i * 2);
    }
    
    println!("After 50 inserts: {}", map.capacity());
    println!("Length: {}", map.len());
    
    // Shrink to fit actual usage
    map.shrink_to_fit();
    println!("After shrink_to_fit: {}", map.capacity());
    
    // Shrink to specific capacity
    map.shrink_to(10);
    println!("After shrink_to(10): {}", map.capacity());
}
```

**Hidden Knowledge:** HashMap grows by powers of 2. When it reaches about 90% capacity (the load factor), it doubles in size and rehashes all entries. This is expensive, so pre-allocating with `with_capacity()` or `reserve()` can significantly improve performance for large maps.

### Custom Hash Functions

```rust
use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use std::hash::Hasher;

// A simple (bad) custom hasher for demonstration
struct IdentityHasher {
    hash: u64,
}

impl Hasher for IdentityHasher {
    fn write(&mut self, bytes: &[u8]) {
        for &byte in bytes {
            self.hash = self.hash.wrapping_add(byte as u64);
        }
    }
    
    fn finish(&self) -> u64 {
        self.hash
    }
}

impl Default for IdentityHasher {
    fn default() -> Self {
        IdentityHasher { hash: 0 }
    }
}

fn main() {
    // Using custom hasher
    let mut map: HashMap<String, i32, BuildHasherDefault<IdentityHasher>> = 
        HashMap::default();
    
    map.insert(String::from("key"), 42);
    println!("{:?}", map);
}
```

**Real-World Use Case:** For integer keys with good distribution, you might use `FxHashMap` from the `rustc-hash` crate, which is faster than the default but not resistant to HashDoS attacks. Only use in trusted environments.

```rust
// In Cargo.toml: rustc-hash = "1.1"
// use rustc_hash::FxHashMap;
// 
// fn main() {
//     let mut map: FxHashMap<i32, String> = FxHashMap::default();
//     map.insert(1, String::from("one"));
// }
```

---

## 8. Custom Types as Keys

### Requirements for Keys

For a type to be used as a HashMap key, it must implement:
1. `Eq` (equality)
2. `Hash`

```rust
use std::collections::HashMap;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
}

// Manual implementation for fine control
impl PartialEq for Person {
    fn eq(&self, other: &Self) -> bool {
        self.name == other.name && self.age == other.age
    }
}

impl Eq for Person {}

impl Hash for Person {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.name.hash(state);
        self.age.hash(state);
    }
}

fn main() {
    let mut people_info = HashMap::new();
    
    let person1 = Person {
        name: String::from("Alice"),
        age: 30,
    };
    
    people_info.insert(person1.clone(), "Engineer");
    
    let person2 = Person {
        name: String::from("Alice"),
        age: 30,
    };
    
    // This works because person1 == person2
    if let Some(job) = people_info.get(&person2) {
        println!("Job: {}", job);
    }
}
```

### Deriving Hash and Eq

```rust
use std::collections::HashMap;

// Using derive - simpler but less control
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let mut grid: HashMap<Point, String> = HashMap::new();
    
    grid.insert(Point { x: 0, y: 0 }, String::from("origin"));
    grid.insert(Point { x: 1, y: 1 }, String::from("diagonal"));
    
    let lookup = Point { x: 0, y: 0 };
    println!("{:?}", grid.get(&lookup));
}
```

**Hidden Knowledge:** The order in which you hash fields in a custom Hash implementation matters for collision distribution. Hash fields that vary most first for better distribution.

### Careful with Mutable Keys

```rust
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct MutableKey {
    id: i32,
    // Other mutable fields...
}

fn main() {
    let mut map = HashMap::new();
    let key = MutableKey { id: 1 };
    map.insert(key.clone(), "value");
    
    // DON'T DO THIS in real code:
    // If you could mutate the key while it's in the map,
    // the hash would be invalidated and you couldn't find the value
    
    // This is safe because we're using a clone
    println!("{:?}", map.get(&key));
}
```

**Critical Warning:** Never mutate a value that's being used as a HashMap key. If the hash changes, the HashMap won't be able to find the entry. Always use immutable keys or only hash immutable fields.

### Using Composite Keys

```rust
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct CompositeKey {
    user_id: u64,
    session_id: String,
}

fn main() {
    let mut sessions: HashMap<CompositeKey, Vec<String>> = HashMap::new();
    
    let key = CompositeKey {
        user_id: 12345,
        session_id: String::from("abc-def-ghi"),
    };
    
    sessions.insert(key.clone(), vec![
        String::from("login"),
        String::from("view_page"),
    ]);
    
    if let Some(events) = sessions.get(&key) {
        println!("Session events: {:?}", events);
    }
}
```

### Float Keys - Don't!

```rust
use std::collections::HashMap;

fn main() {
    // f32 and f64 don't implement Eq or Hash
    // This won't compile:
    // let mut map: HashMap<f64, String> = HashMap::new();
    
    // If you need floating-point keys, use a wrapper
    use ordered_float::OrderedFloat;
    // Cargo.toml: ordered-float = "3.0"
    
    // let mut map: HashMap<OrderedFloat<f64>, String> = HashMap::new();
    // map.insert(OrderedFloat(3.14), String::from("pi"));
}
```

**Hidden Knowledge:** Floats don't implement `Eq` or `Hash` because of NaN (Not a Number). NaN != NaN, violating equality requirements. If you need float keys, use a library like `ordered-float` that provides wrappers.

---

## 9. Advanced Patterns and Techniques

### Caching and Memoization

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

fn main() {
    let mut fib = Fibonacci::new();
    println!("Fib(10) = {}", fib.calculate(10));
    println!("Fib(50) = {}", fib.calculate(50));
    println!("Cache size: {}", fib.cache.len());
}
```

### Multi-Value Storage

```rust
use std::collections::HashMap;

fn main() {
    // Storing multiple values per key using Vec
    let mut tag_system: HashMap<String, Vec<String>> = HashMap::new();
    
    tag_system.entry(String::from("rust"))
        .or_insert_with(Vec::new)
        .push(String::from("article1"));
    
    tag_system.entry(String::from("rust"))
        .or_insert_with(Vec::new)
        .push(String::from("article2"));
    
    tag_system.entry(String::from("python"))
        .or_insert_with(Vec::new)
        .push(String::from("article3"));
    
    println!("{:?}", tag_system);
}
```

### Grouping Data

```rust
use std::collections::HashMap;

#[derive(Debug)]
struct Employee {
    name: String,
    department: String,
    salary: u32,
}

fn group_by_department(employees: Vec<Employee>) -> HashMap<String, Vec<Employee>> {
    let mut grouped = HashMap::new();
    
    for employee in employees {
        grouped.entry(employee.department.clone())
            .or_insert_with(Vec::new)
            .push(employee);
    }
    
    grouped
}

fn main() {
    let employees = vec![
        Employee { name: "Alice".into(), department: "Engineering".into(), salary: 100000 },
        Employee { name: "Bob".into(), department: "Sales".into(), salary: 80000 },
        Employee { name: "Charlie".into(), department: "Engineering".into(), salary: 110000 },
    ];
    
    let by_dept = group_by_department(employees);
    
    for (dept, emps) in &by_dept {
        println!("{}: {} employees", dept, emps.len());
    }
}
```

### Bidirectional Maps

```rust
use std::collections::HashMap;

struct BidirectionalMap<K, V> 
where
    K: Eq + std::hash::Hash + Clone,
    V: Eq + std::hash::Hash + Clone,
{
    forward: HashMap<K, V>,
    reverse: HashMap<V, K>,
}

impl<K, V> BidirectionalMap<K, V>
where
    K: Eq + std::hash::Hash + Clone,
    V: Eq + std::hash::Hash + Clone,
{
    fn new() -> Self {
        BidirectionalMap {
            forward: HashMap::new(),
            reverse: HashMap::new(),
        }
    }
    
    fn insert(&mut self, key: K, value: V) {
        self.forward.insert(key.clone(), value.clone());
        self.reverse.insert(value, key);
    }
    
    fn get_by_key(&self, key: &K) -> Option<&V> {
        self.forward.get(key)
    }
    
    fn get_by_value(&self, value: &V) -> Option<&K> {
        self.reverse.get(value)
    }
}

fn main() {
    let mut bimap = BidirectionalMap::new();
    bimap.insert("user123", 12345);
    bimap.insert("user456", 67890);
    
    println!("ID for user123: {:?}", bimap.get_by_key(&"user123"));
    println!("Username for 12345: {:?}", bimap.get_by_value(&12345));
}
```

### Counting and Frequency Analysis

```rust
use std::collections::HashMap;

fn character_frequency(text: &str) -> HashMap<char, usize> {
    let mut freq = HashMap::new();
    
    for ch in text.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    
    freq
}

fn top_n_frequent<T: Eq + std::hash::Hash + Clone>(
    items: &[T],
    n: usize,
) -> Vec<(T, usize)> {
    let mut freq = HashMap::new();
    
    for item in items {
        *freq.entry(item.clone()).or_insert(0) += 1;
    }
    
    let mut freq_vec: Vec<_> = freq.into_iter().collect();
    freq_vec.sort_by(|a, b| b.1.cmp(&a.1));
    freq_vec.into_iter().take(n).collect()
}

fn main() {
    let text = "hello world";
    let freq = character_frequency(text);
    println!("Character frequencies: {:?}", freq);
    
    let words = vec!["apple", "banana", "apple", "cherry", "banana", "apple"];
    let top_words = top_n_frequent(&words, 2);
    println!("Top 2 words: {:?}", top_words);
}
```

### Default Values Pattern

```rust
use std::collections::HashMap;

#[derive(Debug)]
struct Config {
    settings: HashMap<String, String>,
}

impl Config {
    fn new() -> Self {
        Config {
            settings: HashMap::new(),
        }
    }
    
    fn get(&self, key: &str) -> String {
        self.settings.get(key)
            .cloned()
            .unwrap_or_else(|| self.default_value(key))
    }
    
    fn default_value(&self, key: &str) -> String {
        match key {
            "theme" => "dark".to_string(),
            "language" => "en".to_string(),
            _ => "".to_string(),
        }
    }
}

fn main() {
    let mut config = Config::new();
    config.settings.insert("theme".to_string(), "light".to_string());
    
    println!("Theme: {}", config.get("theme")); // "light"
    println!("Language: {}", config.get("language")); // "en" (default)
}
```

---

## 10. Real-World Use Cases

### 1. Web Request Router

```rust
use std::collections::HashMap;

type Handler = fn(&str) -> String;

struct Router {
    routes: HashMap<String, Handler>,
}

impl Router {
    fn new() -> Self {
        Router {
            routes: HashMap::new(),
        }
    }
    
    fn add_route(&mut self, path: String, handler: Handler) {
        self.routes.insert(path, handler);
    }
    
    fn handle_request(&self, path: &str) -> String {
        match self.routes.get(path) {
            Some(handler) => handler(path),
            None => "404 Not Found".to_string(),
        }
    }
}

fn home_handler(_path: &str) -> String {
    "Welcome to the home page!".to_string()
}

fn about_handler(_path: &str) -> String {
    "About us page".to_string()
}

fn main() {
    let mut router = Router::new();
    router.add_route("/".to_string(), home_handler);
    router.add_route("/about".to_string(), about_handler);
    
    println!("{}", router.handle_request("/"));
    println!("{}", router.handle_request("/about"));
    println!("{}", router.handle_request("/unknown"));
}
```

### 2. Database Connection Pool

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[derive(Clone, Debug)]
struct Connection {
    id: usize,
    active: bool,
}

struct ConnectionPool {
    connections: Arc<Mutex<HashMap<usize, Connection>>>,
    next_id: Arc<Mutex<usize>>,
}

impl ConnectionPool {
    fn new() -> Self {
        ConnectionPool {
            connections: Arc::new(Mutex::new(HashMap::new())),
            next_id: Arc::new(Mutex::new(0)),
        }
    }
    
    fn acquire(&self) -> Option<usize> {
        let mut conns = self.connections.lock().unwrap();
        
        // Try to find an inactive connection
        for (id, conn) in conns.iter_mut() {
            if !conn.active {
                conn.active = true;
                return Some(*id);
            }
        }
        
        // Create new connection
        let mut next_id = self.next_id.lock().unwrap();
        let id = *next_id;
        *next_id += 1;
        
        conns.insert(id, Connection { id, active: true });
        Some(id)
    }
    
    fn release(&self, id: usize) {
        let mut conns = self.connections.lock().unwrap();
        if let Some(conn) = conns.get_mut(&id) {
            conn.active = false;
        }
    }
    
    fn stats(&self) -> (usize, usize) {
        let conns = self.connections.lock().unwrap();
        let total = conns.len();
        let active = conns.values().filter(|c| c.active).count();
        (total, active)
    }
}

fn main() {
    let pool = ConnectionPool::new();
    
    let conn1 = pool.acquire().unwrap();
    let conn2 = pool.acquire().unwrap();
    println!("Acquired connections: {} and {}", conn1, conn2);
    
    let (total, active) = pool.stats();
    println!("Pool stats: {} total, {} active", total, active);
    
    pool.release(conn1);
    
    let (total, active) = pool.stats();
    println!("Pool stats: {} total, {} active", total, active);
}
```

### 3. Dependency Injection Container

```rust
use std::collections::HashMap;
use std::any::{Any, TypeId};
use std::sync::Arc;

struct Container {
    services: HashMap<TypeId, Arc<dyn Any + Send + Sync>>,
}

impl Container {
    fn new() -> Self {
        Container {
            services: HashMap::new(),
        }
    }
    
    fn register<T: 'static + Send + Sync>(&mut self, service: T) {
        self.services.insert(
            TypeId::of::<T>(),
            Arc::new(service),
        );
    }
    
    fn resolve<T: 'static>(&self) -> Option<Arc<T>> {
        self.services
            .get(&TypeId::of::<T>())
            .and_then(|service| service.clone().downcast::<T>().ok())
    }
}

// Example services
struct Database {
    connection_string: String,
}

struct Logger {
    log_level: String,
}

fn main() {
    let mut container = Container::new();
    
    container.register(Database {
        connection_string: "localhost:5432".to_string(),
    });
    
    container.register(Logger {
        log_level: "INFO".to_string(),
    });
    
    // Resolve services
    if let Some(db) = container.resolve::<Database>() {
        println!("Database: {}", db.connection_string);
    }
    
    if let Some(logger) = container.resolve::<Logger>() {
        println!("Logger level: {}", logger.log_level);
    }
}
```

### 4. Rate Limiter

```rust
use std::collections::HashMap;
use std::time::{Duration, Instant};

struct RateLimiter {
    requests: HashMap<String, Vec<Instant>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    fn new(max_requests: usize, window: Duration) -> Self {
        RateLimiter {
            requests: HashMap::new(),
            max_requests,
            window,
        }
    }
    
    fn allow(&mut self, client_id: &str) -> bool {
        let now = Instant::now();
        let cutoff = now - self.window;
        
        let timestamps = self.requests.entry(client_id.to_string())
            .or_insert_with(Vec::new);
        
        // Remove old timestamps
        timestamps.retain(|&timestamp| timestamp > cutoff);
        
        if timestamps.len() < self.max_requests {
            timestamps.push(now);
            true
        } else {
            false
        }
    }
    
    fn reset(&mut self, client_id: &str) {
        self.requests.remove(client_id);
    }
}

fn main() {
    let mut limiter = RateLimiter::new(3, Duration::from_secs(10));
    
    for i in 0..5 {
        if limiter.allow("client1") {
            println!("Request {} allowed", i + 1);
        } else {
            println!("Request {} denied - rate limit exceeded", i + 1);
        }
    }
}
```

### 5. LRU Cache Implementation

```rust
use std::collections::HashMap;
use std::collections::VecDeque;

struct LRUCache<K, V> {
    capacity: usize,
    cache: HashMap<K, V>,
    order: VecDeque<K>,
}

impl<K: Clone + Eq + std::hash::Hash, V> LRUCache<K, V> {
    fn new(capacity: usize) -> Self {
        LRUCache {
            capacity,
            cache: HashMap::new(),
            order: VecDeque::new(),
        }
    }
    
    fn get(&mut self, key: &K) -> Option<&V> {
        if self.cache.contains_key(key) {
            // Move to front
            self.order.retain(|k| k != key);
            self.order.push_front(key.clone());
            self.cache.get(key)
        } else {
            None
        }
    }
    
    fn put(&mut self, key: K, value: V) {
        if self.cache.contains_key(&key) {
            // Update existing
            self.order.retain(|k| k != &key);
        } else if self.cache.len() >= self.capacity {
            // Evict least recently used
            if let Some(old_key) = self.order.pop_back() {
                self.cache.remove(&old_key);
            }
        }
        
        self.order.push_front(key.clone());
        self.cache.insert(key, value);
    }
}

fn main() {
    let mut cache = LRUCache::new(2);
    
    cache.put("a", 1);
    cache.put("b", 2);
    println!("Get a: {:?}", cache.get(&"a"));
    
    cache.put("c", 3); // Evicts "b"
    println!("Get b: {:?}", cache.get(&"b")); // None
    println!("Get c: {:?}", cache.get(&"c"));
}
```

### 6. Graph Representation (Adjacency List)

```rust
use std::collections::HashMap;

struct Graph {
    adjacency_list: HashMap<String, Vec<String>>,
}

impl Graph {
    fn new() -> Self {
        Graph {
            adjacency_list: HashMap::new(),
        }
    }
    
    fn add_edge(&mut self, from: String, to: String) {
        self.adjacency_list
            .entry(from)
            .or_insert_with(Vec::new)
            .push(to);
    }
    
    fn neighbors(&self, node: &str) -> Option<&Vec<String>> {
        self.adjacency_list.get(node)
    }
    
    fn has_path_dfs(&self, start: &str, end: &str) -> bool {
        let mut visited = HashMap::new();
        self.dfs_helper(start, end, &mut visited)
    }
    
    fn dfs_helper(&self, current: &str, target: &str, visited: &mut HashMap<String, bool>) -> bool {
        if current == target {
            return true;
        }
        
        visited.insert(current.to_string(), true);
        
        if let Some(neighbors) = self.adjacency_list.get(current) {
            for neighbor in neighbors {
                if !visited.contains_key(neighbor.as_str()) {
                    if self.dfs_helper(neighbor, target, visited) {
                        return true;
                    }
                }
            }
        }
        
        false
    }
}

fn main() {
    let mut graph = Graph::new();
    
    graph.add_edge("A".to_string(), "B".to_string());
    graph.add_edge("A".to_string(), "C".to_string());
    graph.add_edge("B".to_string(), "D".to_string());
    graph.add_edge("C".to_string(), "D".to_string());
    
    println!("Path from A to D exists: {}", graph.has_path_dfs("A", "D"));
    println!("Path from D to A exists: {}", graph.has_path_dfs("D", "A"));
}
```

### 7. JSON-like Data Structure

```rust
use std::collections::HashMap;

#[derive(Debug, Clone)]
enum JsonValue {
    Null,
    Bool(bool),
    Number(f64),
    String(String),
    Array(Vec<JsonValue>),
    Object(HashMap<String, JsonValue>),
}

impl JsonValue {
    fn get(&self, key: &str) -> Option<&JsonValue> {
        match self {
            JsonValue::Object(map) => map.get(key),
            _ => None,
        }
    }
    
    fn as_str(&self) -> Option<&str> {
        match self {
            JsonValue::String(s) => Some(s),
            _ => None,
        }
    }
}

fn main() {
    let mut person = HashMap::new();
    person.insert("name".to_string(), JsonValue::String("Alice".to_string()));
    person.insert("age".to_string(), JsonValue::Number(30.0));
    person.insert("active".to_string(), JsonValue::Bool(true));
    
    let mut hobbies = vec![
        JsonValue::String("reading".to_string()),
        JsonValue::String("coding".to_string()),
    ];
    person.insert("hobbies".to_string(), JsonValue::Array(hobbies));
    
    let json = JsonValue::Object(person);
    
    if let Some(name) = json.get("name").and_then(|v| v.as_str()) {
        println!("Name: {}", name);
    }
}
```

---

## 11. Common Pitfalls and Best Practices

### Pitfall 1: Not Checking for Existence

```rust
use std::collections::HashMap;

fn main() {
    let scores = HashMap::from([("Blue", 10)]);
    
    // BAD: Panics if key doesn't exist
    // let score = &scores[&"Red"];
    
    // GOOD: Use get() which returns Option
    if let Some(score) = scores.get(&"Red") {
        println!("Score: {}", score);
    } else {
        println!("Team not found");
    }
    
    // GOOD: Use entry API for insert-or-update
    let mut scores = scores;
    let score = scores.entry("Red").or_insert(0);
    *score += 5;
}
```

### Pitfall 2: Cloning Keys Unnecessarily

```rust
use std::collections::HashMap;

fn main() {
    let mut map: HashMap<String, i32> = HashMap::new();
    let key = String::from("test");
    
    // BAD: Cloning unnecessarily
    // map.insert(key.clone(), 42);
    // if let Some(value) = map.get(&key.clone()) { }
    
    // GOOD: Use references for lookup
    map.insert(key.clone(), 42);
    if let Some(value) = map.get(&key) {
        println!("{}", value);
    }
    
    // GOOD: Or use &str keys if possible
    let mut map: HashMap<&str, i32> = HashMap::new();
    map.insert("test", 42);
}
```

### Pitfall 3: Ignoring Capacity

```rust
use std::collections::HashMap;

fn main() {
    // BAD: Multiple reallocations
    let mut map = HashMap::new();
    for i in 0..10000 {
        map.insert(i, i * 2);
    }
    
    // GOOD: Pre-allocate
    let mut map = HashMap::with_capacity(10000);
    for i in 0..10000 {
        map.insert(i, i * 2);
    }
}
```

### Pitfall 4: Inefficient Entry API Usage

```rust
use std::collections::HashMap;

fn main() {
    let mut map: HashMap<String, Vec<i32>> = HashMap::new();
    
    // BAD: Double lookup
    // if !map.contains_key("key") {
    //     map.insert("key".to_string(), Vec::new());
    // }
    // map.get_mut("key").unwrap().push(1);
    
    // GOOD: Single lookup with entry API
    map.entry("key".to_string())
        .or_insert_with(Vec::new)
        .push(1);
}
```

### Best Practice: Type Aliases for Complex Maps

```rust
use std::collections::HashMap;

// Makes code more readable
type UserCache = HashMap<u64, User>;
type SessionStore = HashMap<String, Session>;

#[derive(Debug)]
struct User {
    id: u64,
    name: String,
}

#[derive(Debug)]
struct Session {
    user_id: u64,
    expires_at: u64,
}

fn main() {
    let mut users: UserCache = HashMap::new();
    users.insert(1, User { id: 1, name: "Alice".to_string() });
    
    let mut sessions: SessionStore = HashMap::new();
    sessions.insert("abc123".to_string(), Session { user_id: 1, expires_at: 1000 });
}
```

### Best Practice: Error Handling

```rust
use std::collections::HashMap;

#[derive(Debug)]
enum CacheError {
    NotFound,
    InvalidData,
}

struct Cache {
    data: HashMap<String, String>,
}

impl Cache {
    fn get(&self, key: &str) -> Result<&String, CacheError> {
        self.data.get(key).ok_or(CacheError::NotFound)
    }
    
    fn parse_int(&self, key: &str) -> Result<i32, CacheError> {
        let value = self.get(key)?;
        value.parse().map_err(|_| CacheError::InvalidData)
    }
}

fn main() {
    let mut cache = Cache { data: HashMap::new() };
    cache.data.insert("count".to_string(), "42".to_string());
    
    match cache.parse_int("count") {
        Ok(n) => println!("Count: {}", n),
        Err(e) => println!("Error: {:?}", e),
    }
}
```

### Best Practice: Documentation

```rust
use std::collections::HashMap;

/// A user registry that maps user IDs to user profiles.
/// 
/// # Examples
/// 
/// ```
/// let mut registry = UserRegistry::new();
/// registry.add_user(1, "Alice");
/// assert_eq!(registry.get_user(1), Some(&"Alice".to_string()));
/// ```
struct UserRegistry {
    /// Internal storage mapping user IDs to usernames
    users: HashMap<u64, String>,
}

impl UserRegistry {
    /// Creates a new empty user registry.
    fn new() -> Self {
        UserRegistry {
            users: HashMap::new(),
        }
    }
    
    /// Adds a user to the registry.
    /// 
    /// Returns the old username if the user ID already existed.
    fn add_user(&mut self, id: u64, name: &str) -> Option<String> {
        self.users.insert(id, name.to_string())
    }
    
    /// Retrieves a user's name by ID.
    fn get_user(&self, id: u64) -> Option<&String> {
        self.users.get(&id)
    }
}
```

---

## Conclusion

Hash Maps in Rust are powerful, efficient data structures that form the backbone of many applications. Key takeaways:

1. **Always use `get()` over indexing** to avoid panics
2. **Leverage the Entry API** for efficient insert-or-update operations
3. **Pre-allocate capacity** when you know the size upfront
4. **Be careful with ownership** - keys and values are moved unless they're Copy
5. **Custom keys must implement Eq and Hash** correctly
6. **Never mutate keys** while they're in the map
7. **Consider FxHashMap** for trusted integer keys (performance)
8. **Use type aliases** for complex nested HashMaps

The HashMap is one of Rust's most versatile collections, and mastering it is essential for writing efficient, idiomatic Rust code.