# Comprehensive Rust Standard Library Functions for DSA Mastery

I'll organize this by category, providing the functions you'll use most frequently in competitive programming and algorithmic problem-solving. Think of this as your **arsenal** — these are the tools that separate efficient solutions from clumsy ones.

---

## **1. Vector Operations** (`Vec<T>`)

Vectors are dynamic arrays — they grow/shrink at runtime, stored on the heap.

```rust
let mut v = vec![1, 2, 3, 4, 5];

// Basic operations
v.push(6);                    // Add to end - O(1) amortized
v.pop();                      // Remove from end - O(1), returns Option<T>
v.len();                      // Get length - O(1)
v.is_empty();                 // Check if empty - O(1)
v.clear();                    // Remove all elements - O(n)

// Access
v[0];                         // Direct index - O(1), panics if out of bounds
v.get(0);                     // Safe access - O(1), returns Option<&T>
v.first();                    // First element - Option<&T>
v.last();                     // Last element - Option<&T>

// Insertion/Removal at arbitrary positions
v.insert(2, 99);              // Insert at index - O(n) - shifts elements right
v.remove(2);                  // Remove at index - O(n) - shifts elements left
v.swap_remove(2);             // Remove at index - O(1) - swaps with last, then pops

// Slicing
&v[1..4];                     // Slice from index 1 to 3 (exclusive end)
&v[..3];                      // First 3 elements
&v[2..];                      // From index 2 to end
v.split_at(3);                // Split into two slices at index 3

// Iteration
v.iter();                     // Iterator over &T
v.iter_mut();                 // Iterator over &mut T
v.into_iter();                // Iterator over T (consumes vector)

// Searching
v.contains(&3);               // O(n) - linear search
v.binary_search(&3);          // O(log n) - requires sorted vector, returns Result<usize, usize>

// Sorting
v.sort();                     // O(n log n) - unstable sort (may reorder equal elements)
v.sort_unstable();            // O(n log n) - faster, unstable
v.sort_by(|a, b| b.cmp(a));   // Custom comparator - descending order
v.sort_by_key(|x| x.abs());   // Sort by key function

// Reversal
v.reverse();                  // In-place reversal - O(n)

// Deduplication
v.dedup();                    // Remove consecutive duplicates - O(n), requires sorted for full dedup

// Capacity management
v.capacity();                 // Current capacity
v.reserve(100);               // Reserve space for at least 100 more elements
v.shrink_to_fit();            // Reduce capacity to fit length

// Advanced
v.resize(10, 0);              // Resize to length 10, filling with 0
v.truncate(5);                // Keep only first 5 elements
v.retain(|&x| x > 2);         // Keep only elements matching predicate
v.drain(1..3);                // Remove and return iterator over range
```

---

## **2. Iterator Methods** (Core to Rust's functional style)

**Iterators are lazy** — they don't compute until you call a consuming method like `collect()`, `sum()`, or `for_each()`.

```rust
let v = vec![1, 2, 3, 4, 5];

// Consuming adaptors (terminal operations)
v.iter().collect::<Vec<_>>();     // Collect into collection
v.iter().sum::<i32>();             // Sum all elements
v.iter().product::<i32>();         // Product of all elements
v.iter().count();                  // Count elements
v.iter().min();                    // Minimum - returns Option<&T>
v.iter().max();                    // Maximum - returns Option<&T>
v.iter().any(|&x| x > 3);          // True if any element satisfies predicate
v.iter().all(|&x| x > 0);          // True if all elements satisfy predicate
v.iter().find(|&&x| x > 3);        // First element matching - returns Option<&T>
v.iter().position(|&x| x > 3);     // Index of first match - returns Option<usize>
v.iter().nth(2);                   // Get nth element (0-indexed) - returns Option<&T>
v.iter().fold(0, |acc, x| acc + x); // Left fold/reduce with accumulator
v.iter().reduce(|a, b| a + b);     // Reduce without initial value - returns Option<T>

// Iterator adaptors (lazy transformations)
v.iter().map(|x| x * 2);           // Transform each element
v.iter().filter(|&&x| x > 2);      // Keep elements matching predicate
v.iter().take(3);                  // Take first 3 elements
v.iter().skip(2);                  // Skip first 2 elements
v.iter().rev();                    // Reverse iterator
v.iter().enumerate();              // Produce (index, value) pairs
v.iter().zip(other.iter());        // Zip with another iterator
v.iter().chain(other.iter());      // Chain two iterators
v.iter().cloned();                 // Clone each element (if T: Clone)
v.iter().copied();                 // Copy each element (if T: Copy)
v.iter().cycle();                  // Infinite repetition
v.iter().take_while(|&&x| x < 4);  // Take elements while predicate is true
v.iter().skip_while(|&&x| x < 3);  // Skip elements while predicate is true
v.iter().flat_map(|x| 0..*x);      // Map then flatten
v.iter().flatten();                // Flatten nested iterators
v.windows(2);                      // Sliding windows of size 2
v.chunks(2);                       // Non-overlapping chunks of size 2
v.split(|x| x == &3);              // Split at elements matching predicate

// Partition
v.iter().partition(|&&x| x > 2);   // Split into two collections based on predicate
```

---

## **3. String Operations** (`String` and `&str`)

**`String`** is heap-allocated, growable. **`&str`** is a view into string data (immutable reference).

```rust
let mut s = String::from("hello");

// Basic operations
s.push('!');                  // Append char - O(1) amortized
s.push_str(" world");         // Append string slice - O(n)
s.pop();                      // Remove last char - O(1), returns Option<char>
s.len();                      // Byte length (NOT char count)
s.is_empty();                 // Check if empty
s.clear();                    // Empty the string

// Access (tricky - UTF-8 encoding)
s.chars();                    // Iterator over chars
s.bytes();                    // Iterator over bytes
s.char_indices();             // Iterator over (byte_index, char) pairs
s.lines();                    // Iterator over lines

// Slicing (byte-based - must be on char boundaries!)
&s[0..5];                     // Slice - panics if not on char boundary
s.get(0..5);                  // Safe slice - returns Option<&str>

// Searching
s.contains("ell");            // Substring search
s.starts_with("he");          // Prefix check
s.ends_with("lo");            // Suffix check
s.find("l");                  // First occurrence - returns Option<usize>
s.rfind("l");                 // Last occurrence
s.matches("l");               // Iterator over all matches

// Splitting
s.split(' ');                 // Split by delimiter - returns iterator
s.split_whitespace();         // Split by any whitespace
s.lines();                    // Split by newlines
s.split_once(' ');            // Split once - returns Option<(&str, &str)>

// Trimming
s.trim();                     // Remove leading/trailing whitespace
s.trim_start();               // Remove leading whitespace
s.trim_end();                 // Remove trailing whitespace

// Case conversion
s.to_lowercase();             // Convert to lowercase - returns new String
s.to_uppercase();             // Convert to uppercase

// Parsing
s.parse::<i32>();             // Parse to type - returns Result<i32, ParseIntError>

// Replacement
s.replace("l", "L");          // Replace all occurrences - returns new String
s.replacen("l", "L", 1);      // Replace first n occurrences

// Repeating
s.repeat(3);                  // Repeat string n times
```

---

## **4. HashMap and HashSet** (Hash tables)

**HashMap** is a key-value store. **HashSet** is a set of unique values. Average O(1) insert/lookup/delete.

```rust
use std::collections::{HashMap, HashSet};

let mut map = HashMap::new();

// HashMap operations
map.insert("key", 42);           // Insert - returns Option<V> (old value if key existed)
map.get("key");                  // Get reference - returns Option<&V>
map.get_mut("key");              // Get mutable reference - returns Option<&mut V>
map.contains_key("key");         // Check if key exists
map.remove("key");               // Remove - returns Option<V>
map.len();                       // Number of entries
map.is_empty();                  // Check if empty
map.clear();                     // Remove all entries

// Entry API (powerful for insert-or-modify patterns)
map.entry("key").or_insert(0);              // Insert if not present
map.entry("key").and_modify(|v| *v += 1);   // Modify if present
*map.entry("key").or_insert(0) += 1;        // Increment or initialize

// Iteration
map.iter();                      // Iterator over (&K, &V)
map.keys();                      // Iterator over &K
map.values();                    // Iterator over &V
map.values_mut();                // Iterator over &mut V

// HashSet operations
let mut set = HashSet::new();
set.insert(1);                   // Insert - returns bool (false if already present)
set.contains(&1);                // Check membership
set.remove(&1);                  // Remove - returns bool
set.len();                       // Size
set.is_empty();                  // Check if empty

// Set operations
set.union(&other);               // Iterator over union
set.intersection(&other);        // Iterator over intersection
set.difference(&other);          // Iterator over difference (in set but not other)
set.symmetric_difference(&other); // Iterator over symmetric difference
set.is_subset(&other);           // Check if subset
set.is_superset(&other);         // Check if superset
```

---

## **5. BTreeMap and BTreeSet** (Ordered maps/sets)

**Balanced binary search trees** — O(log n) operations, but **keys are sorted**.

```rust
use std::collections::{BTreeMap, BTreeSet};

let mut map = BTreeMap::new();

// Same basic operations as HashMap, plus:
map.range(2..5);                 // Iterator over range of keys
map.first_key_value();           // Smallest key-value pair - Option<(&K, &V)>
map.last_key_value();            // Largest key-value pair
map.pop_first();                 // Remove and return smallest - Option<(K, V)>
map.pop_last();                  // Remove and return largest

// BTreeSet
let mut set = BTreeSet::new();
set.range(2..5);                 // Iterator over range
set.first();                     // Smallest element - Option<&T>
set.last();                      // Largest element
set.pop_first();                 // Remove and return smallest - Option<T>
set.pop_last();                  // Remove and return largest
```

---

## **6. VecDeque** (Double-ended queue)

Ring buffer — efficient push/pop from **both ends**.

```rust
use std::collections::VecDeque;

let mut deque = VecDeque::new();

deque.push_back(1);              // Add to back - O(1)
deque.push_front(0);             // Add to front - O(1)
deque.pop_back();                // Remove from back - O(1), returns Option<T>
deque.pop_front();               // Remove from front - O(1), returns Option<T>
deque.front();                   // View front - Option<&T>
deque.back();                    // View back - Option<&T>
deque.get(2);                    // Index access - O(1)
deque.rotate_left(2);            // Rotate elements left
deque.rotate_right(2);           // Rotate elements right
```

---

## **7. BinaryHeap** (Priority queue)

**Max-heap** by default. Use `Reverse` wrapper for min-heap.

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

let mut heap = BinaryHeap::new();

heap.push(5);                    // Insert - O(log n)
heap.peek();                     // View max - Option<&T>
heap.pop();                      // Remove max - O(log n), returns Option<T>
heap.len();                      // Size
heap.is_empty();                 // Check if empty

// Min-heap
let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
min_heap.push(Reverse(5));
min_heap.pop();                  // Returns Option<Reverse<i32>>
```

---

## **8. Math Operations**

```rust
// Integer operations
let x = 10;
x.abs();                         // Absolute value
x.pow(3);                        // Power (10^3)
x.checked_add(5);                // Safe addition - returns Option<T>
x.saturating_add(5);             // Saturating addition (clamps at max)
x.wrapping_add(5);               // Wrapping addition (overflow wraps)
x.div_euclid(3);                 // Euclidean division
x.rem_euclid(3);                 // Euclidean remainder (always non-negative)
i32::MAX;                        // Maximum value for i32
i32::MIN;                        // Minimum value for i32

// Floating point
let y = 3.14;
y.abs();                         // Absolute value
y.ceil();                        // Ceiling
y.floor();                       // Floor
y.round();                       // Round to nearest
y.sqrt();                        // Square root
y.powi(2);                       // Integer power
y.powf(2.5);                     // Float power
y.max(2.0);                      // Maximum of two values
y.min(2.0);                      // Minimum

// GCD (not in std, implement yourself or use gcd crate)
fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let temp = b;
        b = a % b;
        a = temp;
    }
    a
}
```

---

## **9. Bit Manipulation**

```rust
let x = 5u32; // 0b0101

x.count_ones();                  // Count 1-bits (popcount)
x.count_zeros();                 // Count 0-bits
x.leading_zeros();               // Leading zeros
x.trailing_zeros();              // Trailing zeros
x.rotate_left(1);                // Rotate bits left
x.rotate_right(1);               // Rotate bits right
x.reverse_bits();                // Reverse bit order
x.swap_bytes();                  // Swap byte order
x.checked_shl(2);                // Safe left shift - Option<T>
x.checked_shr(2);                // Safe right shift
x & y;                           // Bitwise AND
x | y;                           // Bitwise OR
x ^ y;                           // Bitwise XOR
!x;                              // Bitwise NOT
x << 2;                          // Left shift
x >> 2;                          // Right shift
```

---

## **10. Option and Result** (Error handling)

**Option** represents optional values (Some or None). **Result** represents success or error.

```rust
let opt: Option<i32> = Some(5);

opt.is_some();                   // Check if Some
opt.is_none();                   // Check if None
opt.unwrap();                    // Extract value - panics if None
opt.expect("error msg");         // Unwrap with custom panic message
opt.unwrap_or(0);                // Unwrap or default value
opt.unwrap_or_else(|| 0);        // Unwrap or compute default
opt.map(|x| x * 2);              // Transform if Some
opt.and_then(|x| Some(x * 2));   // Flatmap
opt.filter(|&x| x > 3);          // Keep if predicate holds
opt.ok_or("error");              // Convert to Result
opt.take();                      // Take value, leaving None
opt.replace(10);                 // Replace value, returning old

let res: Result<i32, &str> = Ok(5);

res.is_ok();                     // Check if Ok
res.is_err();                    // Check if Err
res.unwrap();                    // Extract value - panics if Err
res.expect("error msg");         // Unwrap with custom panic
res.unwrap_or(0);                // Unwrap or default
res.map(|x| x * 2);              // Transform if Ok
res.map_err(|e| format!("{}", e)); // Transform error
res.and_then(|x| Ok(x * 2));     // Flatmap
res.ok();                        // Convert to Option
```

---

## **11. Conversions and Parsing**

```rust
// String conversions
let num = 42;
num.to_string();                 // Convert to String
format!("{}", num);              // Formatted string

// Parsing
"42".parse::<i32>();             // Parse from string - Result<i32, ParseIntError>
"42".parse::<i32>().unwrap();    // Parse and unwrap

// Type conversions
let x = 42i32;
x as i64;                        // Cast to i64
x as f64;                        // Cast to f64

// Char conversions
'A'.is_alphabetic();             // Check if alphabetic
'5'.is_numeric();                // Check if numeric
'5'.to_digit(10);                // Convert to digit - Option<u32>
char::from_digit(5, 10);         // Convert from digit - Option<char>
'A' as u8;                       // Get ASCII value
(65 as u8) as char;              // Convert from ASCII
```

---

## **12. Input/Output** (For competitive programming)

```rust
use std::io::{self, BufRead};

// Read single line
let mut input = String::new();
io::stdin().read_line(&mut input).unwrap();
let trimmed = input.trim();

// Read multiple lines efficiently
let stdin = io::stdin();
for line in stdin.lock().lines() {
    let line = line.unwrap();
    // Process line
}

// Parse integers from line
let nums: Vec<i32> = input
    .trim()
    .split_whitespace()
    .map(|s| s.parse().unwrap())
    .collect();

// Fast output (use print! and println! normally)
println!("{}", result);
```

---

## **13. Memory and Cloning**

```rust
let v = vec![1, 2, 3];

v.clone();                       // Deep copy (if T: Clone)
std::mem::swap(&mut a, &mut b);  // Swap two values
std::mem::replace(&mut x, new);  // Replace value, returning old
std::mem::take(&mut x);          // Take value, leaving Default::default()
```

---

## **Mental Model for Function Selection**

When solving problems, ask yourself:

1. **What data structure fits?** (Vec, HashMap, BTreeMap, VecDeque, BinaryHeap?)
2. **What operation am I doing most?** (Insert, search, sort, iterate?)
3. **What's the time complexity requirement?** (O(1), O(log n), O(n)?)
4. **Am I transforming data?** (Use iterators: `map`, `filter`, `fold`)
5. **Do I need ordering?** (BTreeMap/Set over HashMap/Set)

This list covers **95% of what you'll use** in algorithmic problem-solving. Master these, and you'll code solutions faster and cleaner than most competitors.

Keep this reference close — soon these will be second nature. 🧠