# Essential Rust Built-in Functions for DSA Problems

## 1. **Vector Methods**

### `Vec::new()` and `vec![]` macro
```rust
let mut v1 = Vec::new();
let mut v2 = vec![1, 2, 3];
```
**Use when:** You need a dynamic array for any DSA problem.
**Applicable to:** All array-based problems, stacks, queues, dynamic programming.

### `push()` and `pop()`
```rust
let mut stack = vec![];
stack.push(5);           // Adds to end - O(1)
let val = stack.pop();   // Removes from end, returns Option<T> - O(1)
```
**Use when:** Implementing stacks, building arrays dynamically.
**Not applicable to:** When you need O(1) front insertion (use VecDeque instead).
**Important:** `pop()` returns `Option<T>`, so handle with `if let Some(x) = stack.pop()` or `.unwrap()`.

### `insert()` and `remove()`
```rust
let mut v = vec![1, 2, 4];
v.insert(2, 3);        // Insert 3 at index 2 - O(n)
v.remove(1);           // Remove element at index 1 - O(n)
```
**Use when:** You need to insert/remove at specific positions.
**Avoid when:** Performance matters - both are O(n). Use for small arrays only.

### `len()` and `is_empty()`
```rust
let v = vec![1, 2, 3];
println!("{}", v.len());        // 3 - O(1)
println!("{}", v.is_empty());   // false - O(1)
```
**Use when:** Always use these instead of manual tracking.
**Common in:** Loop conditions, base cases in recursion.

### `get()` vs indexing `[]`
```rust
let v = vec![1, 2, 3];
let x = v[1];           // Panics if out of bounds
let y = v.get(1);       // Returns Option<&T> - safe
```
**Use `get()` when:** You're not sure if index exists (returns `Some(&T)` or `None`).
**Use `[]` when:** You're certain index is valid and want cleaner code.

### `first()`, `last()`, `first_mut()`, `last_mut()`
```rust
let v = vec![1, 2, 3];
if let Some(&first) = v.first() {  // Returns Option<&T>
    println!("{}", first);
}
```
**Use when:** Accessing endpoints without risk of panic.
**Common in:** Queue/stack peek operations, two-pointer problems.

### `sort()`, `sort_unstable()`, `sort_by()`
```rust
let mut v = vec![3, 1, 2];
v.sort();                          // Stable sort - O(n log n)
v.sort_unstable();                 // Faster, unstable - O(n log n)
v.sort_by(|a, b| b.cmp(a));       // Custom comparator (descending)
v.sort_by_key(|x| -x);            // Sort by key function
```
**Use when:** Need sorted data for binary search, greedy algorithms.
**`sort()` vs `sort_unstable()`:** Use unstable for primitives (faster), stable when order of equal elements matters.

### `binary_search()` and `binary_search_by()`
```rust
let v = vec![1, 2, 3, 4, 5];
match v.binary_search(&3) {
    Ok(idx) => println!("Found at {}", idx),    // Returns index
    Err(idx) => println!("Would insert at {}", idx), // Insertion point
}
```
**Prerequisite:** Array MUST be sorted.
**Use when:** Searching in sorted arrays - O(log n).
**Returns:** `Result<usize, usize>` - Ok with index or Err with insertion point.

### `reverse()`
```rust
let mut v = vec![1, 2, 3];
v.reverse();  // In-place - O(n)
```
**Use when:** Two-pointer problems, palindrome checks.

### `split_at()`, `split_at_mut()`
```rust
let v = vec![1, 2, 3, 4, 5];
let (left, right) = v.split_at(2);  // ([1, 2], [3, 4, 5])
```
**Use when:** Divide and conquer algorithms, merge sort.

### `windows()` and `chunks()`
```rust
let v = vec![1, 2, 3, 4];
for window in v.windows(2) {  // Sliding window - overlapping
    println!("{:?}", window); // [1,2], [2,3], [3,4]
}

for chunk in v.chunks(2) {    // Non-overlapping
    println!("{:?}", chunk);  // [1,2], [3,4]
}
```
**Use when:** Sliding window problems, subarray processing.
**Difference:** `windows()` overlaps, `chunks()` doesn't.

### `iter()`, `iter_mut()`, `into_iter()`
```rust
let v = vec![1, 2, 3];
for &x in v.iter() {}        // Borrow elements
for x in v.iter_mut() {}     // Mutable borrow
for x in v.into_iter() {}    // Takes ownership (consumes vector)
```
**Use `iter()`:** When you need to read values without ownership.
**Use `iter_mut()`:** When you need to modify values in place.
**Use `into_iter()`:** When you're done with the vector.

---

## 2. **HashMap and HashSet Methods**

### `HashMap::new()` and insertion
```rust
use std::collections::HashMap;

let mut map = HashMap::new();
map.insert("key", 1);              // O(1) average
let val = map.get("key");          // Returns Option<&V>
```
**Use when:** Frequency counting, caching, memoization, graph adjacency lists.

### `get()`, `get_mut()`, `contains_key()`
```rust
if let Some(&count) = map.get(&key) {
    // Use count
}
if map.contains_key(&key) {        // O(1) average
    // Key exists
}
```
**Use when:** Checking existence or retrieving values safely.

### `entry()` API - Most powerful for DSA
```rust
*map.entry(key).or_insert(0) += 1;  // Frequency counter pattern

map.entry(key)
   .and_modify(|v| *v += 1)
   .or_insert(1);
```
**Use when:** Frequency counting, grouping, building adjacency lists.
**Why powerful:** Avoids double lookup (get + insert).

### `remove()` and `take()`
```rust
map.remove(&key);           // Returns Option<V>
let val = map.remove(&key).unwrap_or(0);
```
**Use when:** Cleaning up, implementing LRU cache.

### HashSet operations
```rust
use std::collections::HashSet;

let mut set = HashSet::new();
set.insert(1);              // Returns bool (true if new)
set.contains(&1);           // O(1) average
set.remove(&1);             // Returns bool

// Set operations
let a: HashSet<_> = [1, 2, 3].iter().collect();
let b: HashSet<_> = [2, 3, 4].iter().collect();
let union: HashSet<_> = a.union(&b).collect();
let intersection: HashSet<_> = a.intersection(&b).collect();
```
**Use when:** Deduplication, checking membership, set operations.

---

## 3. **VecDeque (Double-ended queue)**

```rust
use std::collections::VecDeque;

let mut deque = VecDeque::new();
deque.push_back(1);      // Add to back - O(1)
deque.push_front(2);     // Add to front - O(1)
deque.pop_back();        // Remove from back - O(1)
deque.pop_front();       // Remove from front - O(1)
```
**Use when:** BFS queues, sliding window maximum, implementing deques.
**Advantage over Vec:** O(1) operations at both ends.
**Use in loops:**
```rust
while let Some(node) = deque.pop_front() {
    // BFS processing
}
```

---

## 4. **BinaryHeap (Priority Queue)**

```rust
use std::collections::BinaryHeap;

let mut heap = BinaryHeap::new();  // Max heap by default
heap.push(5);                       // O(log n)
let max = heap.pop();               // Returns Option<T> - O(log n)
let peek = heap.peek();             // Returns Option<&T> - O(1)

// Min heap using Reverse
use std::cmp::Reverse;
let mut min_heap = BinaryHeap::new();
min_heap.push(Reverse(5));
```
**Use when:** Dijkstra's algorithm, finding kth largest, merge k sorted lists.
**Important:** Default is max heap. Use `Reverse` for min heap.
**In loops:**
```rust
while let Some(Reverse(dist)) = min_heap.pop() {
    // Process smallest distance
}
```

---

## 5. **BTreeMap and BTreeSet (Sorted structures)**

```rust
use std::collections::BTreeMap;

let mut map = BTreeMap::new();
map.insert(3, "c");
map.insert(1, "a");
// Maintains sorted order by keys

for (key, val) in &map {  // Iterates in sorted order
    println!("{}: {}", key, val);
}

// Range queries
for (k, v) in map.range(2..5) {  // Keys from 2 to 5
    println!("{}", k);
}
```
**Use when:** Need sorted iteration, range queries, ordered statistics.
**Operations:** O(log n) for insert/remove/search.
**Advantage over HashMap:** Maintains order, supports range operations.

---

## 6. **String Methods**

### Basic operations
```rust
let s = String::from("hello");
let len = s.len();              // Byte length, not char count!
let is_empty = s.is_empty();
s.push('!');                    // Add char
s.push_str(" world");           // Add str
```
**Important:** `len()` returns bytes, not characters. For char count: `s.chars().count()`.

### `chars()` and `bytes()`
```rust
for c in s.chars() {            // Iterate over characters
    println!("{}", c);
}
for b in s.bytes() {            // Iterate over bytes
    println!("{}", b);
}
```
**Use `chars()` when:** Working with Unicode text.
**Use `bytes()` when:** ASCII-only problems (faster).

### String to Vec and back
```rust
let s = "hello".to_string();
let chars: Vec<char> = s.chars().collect();
let back: String = chars.into_iter().collect();
```
**Use when:** Need to modify string (strings are immutable in Rust).

### Splitting and parsing
```rust
let s = "1,2,3,4";
let nums: Vec<i32> = s.split(',')
    .filter_map(|x| x.parse().ok())
    .collect();
```
**Use when:** Parsing input, tokenization problems.

---

## 7. **Iterator Methods (Critical for DSA)**

### `collect()`
```rust
let v: Vec<i32> = (0..10).collect();
let set: HashSet<i32> = v.into_iter().collect();
```
**Use when:** Converting between collections.

### `filter()`, `map()`, `filter_map()`
```rust
let evens: Vec<i32> = (0..10)
    .filter(|&x| x % 2 == 0)
    .collect();

let doubled: Vec<i32> = v.iter()
    .map(|&x| x * 2)
    .collect();

let parsed: Vec<i32> = strs.iter()
    .filter_map(|s| s.parse().ok())
    .collect();
```
**Use when:** Transforming data, filtering results.

### `fold()` and `reduce()`
```rust
let sum = v.iter().fold(0, |acc, &x| acc + x);
let product = v.iter().fold(1, |acc, &x| acc * x);

let max = v.iter().reduce(|a, b| if a > b { a } else { b });
```
**Use when:** Aggregating values, calculating running totals.
**Difference:** `fold()` needs initial value, `reduce()` returns `Option`.

### `any()`, `all()`, `find()`
```rust
let has_even = v.iter().any(|&x| x % 2 == 0);
let all_positive = v.iter().all(|&x| x > 0);
let first_even = v.iter().find(|&&x| x % 2 == 0);
```
**Use when:** Checking conditions, early termination.

### `zip()` and `enumerate()`
```rust
for (i, &val) in v.iter().enumerate() {  // (index, value)
    println!("{}: {}", i, val);
}

let pairs: Vec<_> = v1.iter().zip(v2.iter()).collect();
```
**Use when:** Need indices, combining two sequences.

### `take()`, `skip()`, `take_while()`, `skip_while()`
```rust
let first_5: Vec<_> = v.iter().take(5).collect();
let without_first_5: Vec<_> = v.iter().skip(5).collect();
```
**Use when:** Working with subsequences, sliding windows.

### `min()`, `max()`, `sum()`, `product()`
```rust
let min = v.iter().min();        // Returns Option<&T>
let max = v.iter().max();
let sum: i32 = v.iter().sum();
let product: i32 = v.iter().product();
```
**Use when:** Finding extremes, calculating totals.

---

## 8. **Range and Numeric Operations**

### Ranges
```rust
for i in 0..10 {}         // 0 to 9 (exclusive end)
for i in 0..=10 {}        // 0 to 10 (inclusive end)
for i in (0..10).rev() {} // Reverse: 9 to 0
for i in (0..10).step_by(2) {} // 0, 2, 4, 6, 8
```
**Use when:** Loops, generating sequences.

### `min()`, `max()`, `clamp()`
```rust
let x = 5.min(10);           // Returns 5
let y = 5.max(10);           // Returns 10
let z = 15.clamp(0, 10);     // Returns 10 (clamped to range)
```
**Use when:** Boundary checks, min/max comparisons.

### `abs()`, `pow()`, `sqrt()`
```rust
let x = (-5i32).abs();       // 5
let y = 2i32.pow(3);         // 8
let z = (16.0f64).sqrt();    // 4.0
```
**Use when:** Mathematical problems, distance calculations.

---

## 9. **Comparison and Ordering**

### `cmp()` and `Ordering`
```rust
use std::cmp::Ordering;

match a.cmp(&b) {
    Ordering::Less => println!("a < b"),
    Ordering::Equal => println!("a == b"),
    Ordering::Greater => println!("a > b"),
}
```
**Use when:** Custom sorting, binary search with custom logic.

### `partial_cmp()` for floats
```rust
if let Some(ord) = a.partial_cmp(&b) {
    // Use ord
}
```
**Use when:** Comparing floats (which can be NaN).

---

## 10. **Common DSA Patterns with Built-in Functions**

### Frequency Counter
```rust
let mut freq = HashMap::new();
for &num in &nums {
    *freq.entry(num).or_insert(0) += 1;
}
```

### Two Sum using HashMap
```rust
let mut map = HashMap::new();
for (i, &num) in nums.iter().enumerate() {
    if let Some(&j) = map.get(&(target - num)) {
        return vec![j, i];
    }
    map.insert(num, i);
}
```

### Sliding Window Maximum using VecDeque
```rust
let mut deque = VecDeque::new();
for i in 0..nums.len() {
    while !deque.is_empty() && nums[*deque.back().unwrap()] < nums[i] {
        deque.pop_back();
    }
    deque.push_back(i);
    if deque[0] <= i - k {
        deque.pop_front();
    }
}
```

### BFS using VecDeque
```rust
let mut queue = VecDeque::new();
queue.push_back(start);
while let Some(node) = queue.pop_front() {
    for neighbor in &graph[node] {
        queue.push_back(*neighbor);
    }
}
```

### Dijkstra using BinaryHeap
```rust
let mut heap = BinaryHeap::new();
heap.push(Reverse((0, start)));
while let Some(Reverse((dist, node))) = heap.pop() {
    // Process
}
```

This comprehensive guide covers the most important built-in Rust functions for DSA problems with practical usage patterns!