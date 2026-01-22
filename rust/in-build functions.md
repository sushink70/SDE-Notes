# Comprehensive Guide to Rust's Built-in Functions and Methods

I'll provide you with a systematic breakdown of Rust's core built-in functions, methods, and traits. This is organized by category for deep understanding.

---

## 1. **Fundamental Concepts First**

Before we dive in, let me clarify some terminology:

- **Function**: A standalone piece of code (e.g., `std::mem::size_of()`)
- **Method**: A function associated with a type (e.g., `vec.push()`)
- **Trait**: A collection of methods that types can implement (like an interface)
- **Associated Function**: A function tied to a type but doesn't take `self` (e.g., `String::new()`)

---

## 2. **Core Primitive Type Methods**

### **Integer Types** (`i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize`)

```rust
// Mathematical operations
let n: i32 = -42;
n.abs()              // Absolute value → 42
n.pow(2)             // Power → 1764
n.checked_add(5)     // Safe addition, returns Option<i32>
n.saturating_mul(2)  // Multiply without overflow (saturates at max)
n.wrapping_sub(10)   // Subtract with wrapping on overflow

// Bit operations
n.count_ones()       // Number of 1 bits
n.leading_zeros()    // Number of leading zero bits
n.rotate_left(2)     // Rotate bits left
n.swap_bytes()       // Swap byte order

// Conversions
n.to_be_bytes()      // Convert to big-endian byte array
n.to_string()        // Convert to String
```

**Key Performance Note**: `checked_*` variants are safer but slightly slower. `wrapping_*` and `saturating_*` have predictable behavior on overflow.

---

### **Floating Point** (`f32`, `f64`)

```rust
let x: f64 = 3.14159;

// Mathematical
x.abs()              // Absolute value
x.ceil()             // Round up
x.floor()            // Round down
x.round()            // Round to nearest
x.sqrt()             // Square root
x.powf(2.0)          // Power (float exponent)
x.sin()              // Sine
x.cos()              // Cosine
x.ln()               // Natural logarithm
x.exp()              // e^x

// Classification
x.is_nan()           // Check if Not a Number
x.is_infinite()      // Check if infinite
x.is_finite()        // Check if finite
x.is_sign_positive() // Check sign
```

---

### **Boolean** (`bool`)

```rust
let b = true;
b.then(|| expensive_computation())  // Execute closure only if true
b.then_some(42)                     // Return Some(42) if true, None otherwise
```

---

### **Character** (`char`)

```rust
let c = 'A';

c.is_alphabetic()    // Check if letter
c.is_numeric()       // Check if digit
c.is_alphanumeric()  // Check if letter or digit
c.is_lowercase()     // Check case
c.is_uppercase()
c.is_whitespace()    // Check if whitespace
c.to_lowercase()     // Returns iterator of lowercase chars
c.to_uppercase()     // Returns iterator of uppercase chars
c.is_ascii()         // Check if ASCII
```

---

## 3. **String Types**

### **String** (heap-allocated, growable)

```rust
let mut s = String::new();          // Create empty
let s = String::from("hello");      // From literal
let s = String::with_capacity(100); // Pre-allocate

// Modification
s.push('!');              // Append char
s.push_str(" world");     // Append string
s.insert(0, 'H');         // Insert char at index
s.insert_str(5, "XYZ");   // Insert string at index
s.pop();                  // Remove last char, returns Option<char>
s.remove(0);              // Remove char at index
s.clear();                // Empty the string

// Inspection
s.len()                   // Byte length (not char count!)
s.is_empty()              // Check if empty
s.capacity()              // Allocated capacity
s.chars()                 // Iterator over Unicode chars
s.bytes()                 // Iterator over bytes
s.as_bytes()              // View as byte slice

// Searching
s.contains("world")       // Check substring
s.starts_with("he")       // Check prefix
s.ends_with("ld")         // Check suffix
s.find("ll")              // First occurrence → Option<usize>

// Splitting
s.split_whitespace()      // Iterator over words
s.split(',')              // Split by delimiter
s.lines()                 // Iterator over lines

// Transformation
s.to_lowercase()          // New lowercase string
s.to_uppercase()          // New uppercase string
s.trim()                  // Remove leading/trailing whitespace
s.replace("old", "new")   // Replace all occurrences
```

**Critical Performance Insight**: `String` uses UTF-8 encoding. Indexing by byte position is O(1), but indexing by character position requires O(n) scanning. Always use iterators when possible.

---

### **&str** (string slice, borrowed view)

```rust
let s: &str = "hello";

// Most String methods work on &str too
s.len()
s.chars()
s.split(',')
// etc.

// Conversion
s.to_string()             // Convert to owned String
s.to_owned()              // Same as to_string()
```

---

## 4. **Collection Types**

### **Vec<T>** (dynamic array)

```rust
let mut v: Vec<i32> = Vec::new();
let v = vec![1, 2, 3];                // Macro for initialization
let v = Vec::with_capacity(100);      // Pre-allocate

// Adding elements
v.push(4);                // Append to end - O(1) amortized
v.insert(0, 99);          // Insert at index - O(n)
v.extend([5, 6, 7]);      // Append multiple

// Removing elements
v.pop();                  // Remove last - O(1), returns Option<T>
v.remove(0);              // Remove at index - O(n), returns T
v.swap_remove(0);         // Remove by swapping with last - O(1)
v.clear();                // Remove all

// Accessing
v[0]                      // Panics if out of bounds
v.get(0)                  // Returns Option<&T>
v.first()                 // First element → Option<&T>
v.last()                  // Last element → Option<&T>

// Information
v.len()                   // Number of elements
v.is_empty()              // Check if empty
v.capacity()              // Allocated capacity

// Iteration
v.iter()                  // Immutable iterator
v.iter_mut()              // Mutable iterator
v.into_iter()             // Consuming iterator (moves values)

// Searching
v.contains(&3)            // Check if contains value
v.binary_search(&3)       // Binary search (must be sorted) → Result<usize, usize>

// Sorting
v.sort()                  // In-place sort
v.sort_unstable()         // Faster unstable sort
v.reverse()               // Reverse in-place

// Slicing
&v[1..3]                  // Slice from index 1 to 2
v.split_at(2)             // Split into two slices
```

**Performance Deep Dive**:
- `push()` is O(1) amortized because Vec doubles capacity when full
- `insert()` and `remove()` are O(n) because they shift elements
- `swap_remove()` is O(1) but doesn't preserve order
- Pre-allocating with `with_capacity()` eliminates reallocation overhead

---

### **HashMap<K, V>** (hash table)

```rust
use std::collections::HashMap;

let mut map = HashMap::new();
let mut map = HashMap::with_capacity(100);

// Insertion
map.insert("key", 42);              // Insert/update - O(1) average
map.entry("key").or_insert(0);      // Insert if absent

// Accessing
map.get("key")                      // Returns Option<&V>
map.get_mut("key")                  // Returns Option<&mut V>
map["key"]                          // Panics if missing

// Removal
map.remove("key")                   // Remove and return Option<V>

// Information
map.len()                           // Number of entries
map.is_empty()
map.contains_key("key")             // Check if key exists

// Iteration
map.iter()                          // Iterator over (&K, &V)
map.keys()                          // Iterator over &K
map.values()                        // Iterator over &V
map.values_mut()                    // Iterator over &mut V
```

**Hash Function Note**: Rust uses SipHash by default (cryptographically secure but slower). For non-adversarial cases, consider `rustc_hash::FxHashMap` for better performance.

---

### **HashSet<T>** (unique values)

```rust
use std::collections::HashSet;

let mut set = HashSet::new();

set.insert(1);                // Add element - O(1) average
set.remove(&1);               // Remove - O(1) average
set.contains(&1);             // Check membership - O(1) average

// Set operations
set.union(&other)             // Union iterator
set.intersection(&other)      // Intersection iterator
set.difference(&other)        // Difference iterator
```

---

### **VecDeque<T>** (double-ended queue)

```rust
use std::collections::VecDeque;

let mut deque = VecDeque::new();

deque.push_front(1);          // Add to front - O(1)
deque.push_back(2);           // Add to back - O(1)
deque.pop_front();            // Remove from front - O(1)
deque.pop_back();             // Remove from back - O(1)
```

**Use Case**: Ideal for BFS, sliding window problems, or any scenario requiring efficient operations at both ends.

---

## 5. **Option<T>** (handles absence of value)

```rust
let opt: Option<i32> = Some(5);
let none: Option<i32> = None;

// Checking
opt.is_some()                 // Returns true if Some
opt.is_none()                 // Returns true if None

// Extracting
opt.unwrap()                  // Panics if None
opt.expect("error msg")       // Panics with custom message
opt.unwrap_or(0)              // Default value if None
opt.unwrap_or_else(|| 0)      // Compute default lazily

// Transforming
opt.map(|x| x * 2)            // Apply function if Some
opt.and_then(|x| Some(x + 1)) // Chain operations (flatMap)
opt.filter(|&x| x > 3)        // Keep only if predicate true

// Pattern matching
match opt {
    Some(x) => println!("{}", x),
    None => println!("nothing"),
}
```

**Design Philosophy**: Rust forces you to handle the `None` case explicitly, eliminating null pointer errors at compile time.

---

## 6. **Result<T, E>** (error handling)

```rust
let res: Result<i32, String> = Ok(42);
let err: Result<i32, String> = Err("failed".to_string());

// Checking
res.is_ok()
res.is_err()

// Extracting
res.unwrap()                  // Panics if Err
res.expect("msg")             // Panics with message
res.unwrap_or(0)              // Default if Err
res.unwrap_or_else(|e| 0)     // Compute default from error

// Transforming
res.map(|x| x * 2)            // Transform Ok value
res.map_err(|e| format!("Error: {}", e))  // Transform Err value
res.and_then(|x| Ok(x + 1))   // Chain fallible operations

// The ? operator
fn divide(a: i32, b: i32) -> Result<i32, String> {
    if b == 0 {
        return Err("division by zero".to_string());
    }
    Ok(a / b)
}

fn compute() -> Result<i32, String> {
    let x = divide(10, 2)?;   // Auto-propagates error
    Ok(x * 2)
}
```

**Error Propagation**: The `?` operator is syntactic sugar for early return on error. It's the idiomatic way to handle errors in Rust.

---

## 7. **Slice Operations** (`[T]`)

```rust
let arr = [1, 2, 3, 4, 5];
let slice: &[i32] = &arr[1..4];  // [2, 3, 4]

// Accessing
slice[0]                      // Index access
slice.get(0)                  // Safe access → Option<&T>
slice.first()                 // First element
slice.last()                  // Last element

// Information
slice.len()
slice.is_empty()

// Iteration
slice.iter()
slice.windows(2)              // Sliding window iterator
slice.chunks(2)               // Non-overlapping chunks

// Searching
slice.contains(&3)
slice.binary_search(&3)       // Must be sorted

// Sorting (for mutable slices)
let mut arr = [3, 1, 2];
arr.sort();
arr.sort_unstable();          // Faster but doesn't preserve equal element order
arr.reverse();

// Splitting
slice.split(|&x| x == 3)      // Split by predicate
slice.split_at(2)             // Split at index
```

---

## 8. **Iterator Methods** (the most powerful feature)

```rust
let v = vec![1, 2, 3, 4, 5];

// Consuming operations (return a value)
v.iter().sum::<i32>()         // Sum all elements
v.iter().product::<i32>()     // Product of all elements
v.iter().count()              // Count elements
v.iter().min()                // Minimum → Option<&T>
v.iter().max()                // Maximum
v.iter().any(|&x| x > 3)      // Check if any satisfy predicate
v.iter().all(|&x| x > 0)      // Check if all satisfy predicate
v.iter().find(|&&x| x == 3)   // First matching element
v.iter().position(|&x| x == 3) // Index of first match
v.iter().nth(2)               // Get nth element

// Transforming operations (return new iterator)
v.iter().map(|x| x * 2)       // Transform each element
v.iter().filter(|&&x| x > 2)  // Keep only matching elements
v.iter().take(3)              // Take first n elements
v.iter().skip(2)              // Skip first n elements
v.iter().enumerate()          // Add index → (usize, &T)
v.iter().zip(&other)          // Combine two iterators
v.iter().flat_map(|x| vec![x, x])  // Map and flatten
v.iter().rev()                // Reverse order
v.iter().cycle()              // Repeat infinitely

// Collecting
v.iter().collect::<Vec<_>>()  // Collect into Vec
v.iter().cloned().collect()   // Clone and collect
```

**Zero-Cost Abstraction**: Iterators compile down to the same machine code as hand-written loops, but are more composable and expressive.

---

## 9. **Memory and Type Utilities**

```rust
use std::mem;

mem::size_of::<i32>()         // Size of type in bytes
mem::align_of::<i32>()        // Alignment requirement
mem::swap(&mut a, &mut b)     // Swap two values
mem::replace(&mut x, new_val) // Replace and return old value
mem::take(&mut x)             // Replace with default, return old
mem::drop(x)                  // Explicitly drop value

use std::cmp;

cmp::min(a, b)                // Minimum of two values
cmp::max(a, b)                // Maximum
```

---

## 10. **Important Traits and Their Methods**

### **Clone** (create deep copy)
```rust
let v = vec![1, 2, 3];
let v2 = v.clone();           // Deep copy
```

### **Copy** (implicit bitwise copy)
```rust
let x: i32 = 5;
let y = x;                    // x is still usable (Copy type)
```

### **Default** (default value)
```rust
let v: Vec<i32> = Default::default();  // Empty vec
let n: i32 = Default::default();        // 0
```

### **Debug** (formatted debug output)
```rust
println!("{:?}", vec![1, 2, 3]);
```

### **Display** (user-facing output)
```rust
println!("{}", 42);
```

---

## 11. **Conversion Traits**

```rust
// From/Into (infallible conversion)
let s = String::from("hello");
let s: String = "hello".into();

// TryFrom/TryInto (fallible conversion)
use std::convert::TryInto;
let n: i32 = 1000;
let b: Result<i8, _> = n.try_into();  // May fail (overflow)

// AsRef/AsMut (borrowing conversion)
fn takes_str(s: &str) { }
takes_str("hello");               // &str
takes_str(&String::from("hello")); // &String → &str via AsRef
```

---

## 12. **Commonly Used Macros**

```rust
vec![1, 2, 3]                 // Create Vec
println!("x = {}", x)         // Print to stdout
eprintln!("error: {}", e)     // Print to stderr
format!("x = {}", x)          // Create String
assert!(condition)            // Panic if false
assert_eq!(a, b)              // Panic if not equal
dbg!(x)                       // Debug print and return value
panic!("error message")       // Immediate panic
unimplemented!()              // Placeholder panic
todo!()                       // Mark unfinished code
```

---

## **Mental Model for Mastery**

To reach top 1%, understand these layers:

1. **Memory Model**: Every operation either moves, borrows, or copies. Know which.
2. **Time Complexity**: Know the Big-O of every operation (I've noted key ones above)
3. **Zero-Cost Abstractions**: Iterators, generics, and traits compile to the same assembly as C
4. **Ownership**: The borrow checker enforces memory safety at compile time

---

## **Flow Diagram: Choosing the Right Collection**

```
Need to store elements?
├─ Order matters?
│  ├─ YES → Need fast random access?
│  │  ├─ YES → Vec<T>
│  │  └─ NO → Need both ends? → VecDeque<T>
│  └─ NO → Need uniqueness?
│     ├─ YES → HashSet<T>
│     └─ NO → Need key-value? → HashMap<K, V>
└─ Fixed size known at compile time? → Array [T; N]
```

---

This is your reference arsenal. Master these, and you'll have the tools to implement any algorithm efficiently in Rust. **Next step**: Pick a specific domain (graphs, trees, dynamic programming) and I'll show you how these primitives compose into elegant solutions.

What area shall we conquer first?