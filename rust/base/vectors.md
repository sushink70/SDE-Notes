# The Complete Guide to Vectors in Rust: Mastering Dynamic Collections

## Foundation: What is a Vector?

Before we dive into Rust's implementation, let's establish **conceptual clarity**:

A **vector** is a **dynamically-sized, contiguous sequence of values** stored in heap memory. Think of it as an array that can grow and shrink at runtime.

**Key mental model**: A vector is a "smart pointer to a growable array." It manages three critical pieces of information:
1. **Pointer** to heap-allocated memory
2. **Length** (current number of elements)
3. **Capacity** (total allocated slots before reallocation needed)

```
Stack Memory              Heap Memory
┌──────────────┐         ┌───┬───┬───┬───┬───┬───┐
│ ptr    ●─────┼────────→│ 1 │ 2 │ 3 │ 4 │   │   │
│ len:   4     │         └───┴───┴───┴───┴───┴───┘
│ cap:   6     │          ↑───length────↑
└──────────────┘          ↑──────capacity──────↑
```

**Why vectors matter in DSA:**
- **Amortized O(1)** append operations
- **O(1)** random access by index
- **Cache-friendly** due to contiguous memory layout
- Foundation for many advanced data structures (heaps, stacks, queues)

---

## Part 1: Creation and Initialization

### 1.1 Empty Vector Creation

```rust
// Method 1: Type annotation required (compiler needs to know type)
let v1: Vec<i32> = Vec::new();

// Method 2: Using vec! macro (type inferred from initial values)
let v2 = vec![1, 2, 3, 4, 5];

// Method 3: Pre-allocated capacity (optimization technique)
let mut v3 = Vec::with_capacity(100);

// Method 4: Filled with default values
let v4 = vec![0; 10]; // Creates [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

**Deep Dive: Why `with_capacity` matters**

When you know the approximate final size, pre-allocating prevents multiple reallocations:

```rust
// Poor performance: Multiple reallocations
let mut v_bad = Vec::new(); // capacity = 0
for i in 0..1000 {
    v_bad.push(i); // Reallocates at powers of 2: 4, 8, 16, 32...
}

// Optimized: Single allocation
let mut v_good = Vec::with_capacity(1000);
for i in 0..1000 {
    v_good.push(i); // No reallocations
}
```

**Mental Model - Amortized Analysis:**
Without pre-allocation, pushing 1000 elements causes ~10 reallocations (log₂(1000) ≈ 10). Each reallocation:
1. Allocates new memory (2× current capacity)
2. Copies all existing elements
3. Deallocates old memory

Total work: O(n) spread across n operations = **amortized O(1)** per push.

---

## Part 2: Adding Elements

### 2.1 Push Operation (Most Common)

```rust
let mut numbers = Vec::new();

// Adding elements one by one
numbers.push(10);
numbers.push(20);
numbers.push(30);

println!("Vector: {:?}", numbers); // [10, 20, 30]
println!("Length: {}", numbers.len());
println!("Capacity: {}", numbers.capacity());
```

**Visualization of Growth:**
```
Initial: []              capacity=0, len=0
push(10): [10]           capacity=4, len=1 (allocation happened)
push(20): [10,20]        capacity=4, len=2
push(30): [10,20,30]     capacity=4, len=3
push(40): [10,20,30,40]  capacity=4, len=4
push(50): [10,20,30,40,50] capacity=8, len=5 (reallocation!)
```

### 2.2 Insert at Specific Position

**Concept: Insert** means placing an element at index `i` and shifting all subsequent elements right.

```rust
let mut v = vec![1, 2, 4, 5];
v.insert(2, 3); // Insert 3 at index 2
// Result: [1, 2, 3, 4, 5]
```

**Time Complexity Analysis:**
- **Best case**: Insert at end → O(1) (equivalent to push)
- **Worst case**: Insert at beginning → O(n) (shift all elements)
- **Average case**: O(n)

**Visualization:**
```
Before: [1, 2, 4, 5]
         ↓  ↓  ↓  ↓
Insert 3 at index 2:
Step 1: Shift [4,5] right → [1, 2, _, 4, 5]
Step 2: Place 3           → [1, 2, 3, 4, 5]
```

### 2.3 Extend with Multiple Elements

```rust
let mut v1 = vec![1, 2, 3];
let v2 = vec![4, 5, 6];

// Method 1: extend() - consumes iterator
v1.extend(v2); // v2 is moved
// v1 is now [1, 2, 3, 4, 5, 6]

// Method 2: extend from slice
let mut v3 = vec![1, 2, 3];
v3.extend(&[4, 5, 6]); // Borrows slice
// v3 is now [1, 2, 3, 4, 5, 6]

// Method 3: append() - moves entire vector
let mut v4 = vec![1, 2, 3];
let mut v5 = vec![4, 5, 6];
v4.append(&mut v5); // v5 becomes empty
// v4: [1, 2, 3, 4, 5, 6], v5: []
```

---

## Part 3: Accessing Elements

### 3.1 Indexing (Direct Access)

```rust
let v = vec![10, 20, 30, 40, 50];

// Method 1: Direct indexing (panics on out-of-bounds)
let third = v[2]; // Returns 30
println!("Third element: {}", third);

// DANGER: This will panic (runtime error)
// let invalid = v[100]; // thread 'main' panicked at 'index out of bounds'
```

**Critical Understanding**: Direct indexing `v[i]` provides:
- **O(1)** access time
- **Panics** if index ≥ length (not safe for untrusted input)

### 3.2 Safe Access with `get()`

```rust
let v = vec![10, 20, 30, 40, 50];

// Returns Option<&T>
match v.get(2) {
    Some(value) => println!("Third element: {}", value), // 30
    None => println!("No element at that index"),
}

// Idiomatic with if-let
if let Some(value) = v.get(100) {
    println!("Found: {}", value);
} else {
    println!("Index out of bounds"); // This executes
}

// Unwrap with default
let value = v.get(100).unwrap_or(&0);
println!("Value: {}", value); // 0
```

**Mental Model - Option Type:**
```rust
enum Option<T> {
    Some(T),  // Contains a value
    None,     // No value (safe null)
}
```

This forces you to handle the "no element" case explicitly, preventing null pointer errors.

### 3.3 First and Last Elements

```rust
let v = vec![10, 20, 30, 40, 50];

// Get first element
if let Some(first) = v.first() {
    println!("First: {}", first); // 10
}

// Get last element
if let Some(last) = v.last() {
    println!("Last: {}", last); // 50
}

// Mutable references
let mut v = vec![10, 20, 30];
if let Some(first) = v.first_mut() {
    *first = 100; // Modify first element
}
println!("{:?}", v); // [100, 20, 30]
```

---

## Part 4: Removing Elements

### 4.1 Pop (Remove from End)

```rust
let mut v = vec![1, 2, 3, 4, 5];

// Remove last element - O(1)
if let Some(last) = v.pop() {
    println!("Popped: {}", last); // 5
}
println!("{:?}", v); // [1, 2, 3, 4]

// Pop until empty
while let Some(val) = v.pop() {
    println!("{}", val); // Prints: 4, 3, 2, 1
}
```

**Time Complexity**: O(1) - just decrements length, no shifting needed.

### 4.2 Remove at Index

```rust
let mut v = vec![1, 2, 3, 4, 5];

// Remove element at index 2 - returns removed value
let removed = v.remove(2); // Removes 3
println!("Removed: {}", removed); // 3
println!("{:?}", v); // [1, 2, 4, 5]
```

**Visualization:**
```
Before: [1, 2, 3, 4, 5]
         ↓  ↓  ↓  ↓  ↓
Remove index 2:
Step 1: Take out 3     → [1, 2, _, 4, 5]
Step 2: Shift left     → [1, 2, 4, 5]
Step 3: Decrement len  → len becomes 4
```

**Time Complexity**: O(n) - must shift all elements after removed index.

### 4.3 Swap Remove (Order-Independent Removal)

**Concept**: When element order doesn't matter, avoid shifting by swapping with last element.

```rust
let mut v = vec![1, 2, 3, 4, 5];

let removed = v.swap_remove(1); // Remove index 1
println!("Removed: {}", removed); // 2
println!("{:?}", v); // [1, 5, 3, 4]
//                           ↑ last element moved here
```

**Visualization:**
```
Before: [1, 2, 3, 4, 5]
         ↓  ↓  ↓  ↓  ↓
swap_remove(1):
Step 1: Swap with last → [1, 5, 3, 4, 2]
Step 2: Pop last       → [1, 5, 3, 4]
```

**Time Complexity**: O(1) - just swap + decrement, no shifting!

**When to use**:
- Element order doesn't matter
- Frequent removals from middle
- Performance-critical code

### 4.4 Retain (Conditional Removal)

**Concept**: Keep only elements that satisfy a predicate (condition).

```rust
let mut v = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// Keep only even numbers
v.retain(|&x| x % 2 == 0);
println!("{:?}", v); // [2, 4, 6, 8, 10]

// More complex predicate
let mut words = vec!["hello", "world", "rust", "programming"];
words.retain(|&word| word.len() > 4);
println!("{:?}", words); // ["hello", "world", "programming"]
```

**Time Complexity**: O(n) - single pass through vector.

### 4.5 Clear (Remove All)

```rust
let mut v = vec![1, 2, 3, 4, 5];
v.clear();
println!("Length: {}, Capacity: {}", v.len(), v.capacity());
// Length: 0, Capacity: 5 (memory still allocated)
```

**Important**: `clear()` keeps capacity, only sets length to 0.

---

## Part 5: Iteration

### 5.1 Immutable Iteration

```rust
let v = vec![1, 2, 3, 4, 5];

// Method 1: for loop (most common)
for val in &v {
    println!("{}", val);
}
// v is still usable here

// Method 2: Iterator methods
v.iter().for_each(|val| println!("{}", val));

// Method 3: Indexed iteration
for (index, val) in v.iter().enumerate() {
    println!("v[{}] = {}", index, val);
}
```

### 5.2 Mutable Iteration

```rust
let mut v = vec![1, 2, 3, 4, 5];

// Modify each element
for val in &mut v {
    *val *= 2; // Dereference and multiply by 2
}
println!("{:?}", v); // [2, 4, 6, 8, 10]

// Using iter_mut()
v.iter_mut().for_each(|val| *val += 10);
println!("{:?}", v); // [12, 14, 16, 18, 20]
```

**Critical Concept - Dereferencing (`*`)**:
- `val` is a mutable reference: `&mut i32`
- To modify the value it points to, use `*val`
- This is fundamental to Rust's ownership system

### 5.3 Consuming Iteration

```rust
let v = vec![String::from("hello"), String::from("world")];

// into_iter() moves/consumes the vector
for val in v {
    println!("{}", val);
}
// v is no longer usable here (moved)
```

**Mental Model - Three Iteration Types:**

| Method | Signature | Ownership | Use Case |
|--------|-----------|-----------|----------|
| `iter()` | `&T` | Borrows | Read-only |
| `iter_mut()` | `&mut T` | Mutable borrow | Modify in place |
| `into_iter()` | `T` | Moves/Consumes | Transform/consume |

---

## Part 6: Slicing and Subranges

**Concept - Slice**: A view into a contiguous sequence without ownership.

```rust
let v = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// Get slice of specific range
let slice = &v[2..5]; // Elements at indices 2, 3, 4
println!("{:?}", slice); // [3, 4, 5]

// Ranges:
let all = &v[..];        // All elements [1..10]
let first_five = &v[..5]; // [1, 2, 3, 4, 5]
let from_third = &v[3..]; // [4, 5, 6, 7, 8, 9, 10]

// Mutable slice
let mut v = vec![1, 2, 3, 4, 5];
let slice_mut = &mut v[1..4];
slice_mut[0] = 100; // Modifies v[1]
println!("{:?}", v); // [1, 100, 3, 4, 5]
```

**Visualization:**
```
Vector: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Index:   0  1  2  3  4  5  6  7  8   9

&v[2..5] points to:
            [3, 4, 5]
             ↑     ↑
           index  index
             2      4 (exclusive end)
```

---

## Part 7: Transformation and Functional Operations

### 7.1 Map - Transform Each Element

```rust
let numbers = vec![1, 2, 3, 4, 5];

// Square each number
let squares: Vec<i32> = numbers.iter()
    .map(|&x| x * x)
    .collect();
println!("{:?}", squares); // [1, 4, 9, 16, 25]

// Type conversion
let strings: Vec<String> = numbers.iter()
    .map(|&x| x.to_string())
    .collect();
println!("{:?}", strings); // ["1", "2", "3", "4", "5"]
```

**Mental Model**: `map()` applies a function to each element and returns a new iterator.

### 7.2 Filter - Select Elements

```rust
let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// Get only even numbers
let evens: Vec<i32> = numbers.iter()
    .filter(|&&x| x % 2 == 0)
    .copied() // Convert &i32 to i32
    .collect();
println!("{:?}", evens); // [2, 4, 6, 8, 10]
```

### 7.3 Reduce/Fold - Aggregate Values

**Concept - Fold**: Combine all elements into a single value using an accumulator.

```rust
let numbers = vec![1, 2, 3, 4, 5];

// Sum all elements
let sum = numbers.iter().fold(0, |acc, &x| acc + x);
println!("Sum: {}", sum); // 15

// Product
let product = numbers.iter().fold(1, |acc, &x| acc * x);
println!("Product: {}", product); // 120

// Build a string
let words = vec!["Hello", "world", "from", "Rust"];
let sentence = words.iter().fold(String::new(), |mut acc, &word| {
    if !acc.is_empty() {
        acc.push(' ');
    }
    acc.push_str(word);
    acc
});
println!("{}", sentence); // "Hello world from Rust"
```

**Visualization of fold:**
```
numbers = [1, 2, 3, 4, 5]
fold(0, add):

Step 0: acc = 0
Step 1: acc = 0 + 1 = 1
Step 2: acc = 1 + 2 = 3
Step 3: acc = 3 + 3 = 6
Step 4: acc = 6 + 4 = 10
Step 5: acc = 10 + 5 = 15
Result: 15
```

### 7.4 Chain Operations

```rust
let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// Complex pipeline: filter evens, square them, sum
let result: i32 = numbers.iter()
    .filter(|&&x| x % 2 == 0)  // [2, 4, 6, 8, 10]
    .map(|&x| x * x)            // [4, 16, 36, 64, 100]
    .sum();                     // 220

println!("Result: {}", result); // 220
```

**Performance Note**: Iterators are **lazy** - no work happens until you call a consuming method like `collect()` or `sum()`. The compiler can optimize the entire chain!

---

## Part 8: Sorting and Searching

### 8.1 Sorting

```rust
let mut numbers = vec![5, 2, 8, 1, 9, 3];

// Sort in ascending order - O(n log n)
numbers.sort();
println!("{:?}", numbers); // [1, 2, 3, 5, 8, 9]

// Sort in descending order
numbers.sort_by(|a, b| b.cmp(a));
println!("{:?}", numbers); // [9, 8, 5, 3, 2, 1]

// Sort by custom key
let mut words = vec!["banana", "apple", "cherry", "date"];
words.sort_by_key(|s| s.len());
println!("{:?}", words); // ["date", "apple", "banana", "cherry"]
```

**Algorithm**: Rust uses **pattern-defeating quicksort** (pdqsort):
- Worst-case O(n log n) time
- O(log n) space (recursive stack)
- Cache-friendly and handles nearly-sorted data well

### 8.2 Binary Search (Requires Sorted Vector)

**Concept - Binary Search**: Efficiently find element in sorted array by repeatedly halving search space.

```rust
let numbers = vec![1, 3, 5, 7, 9, 11, 13, 15];

// Binary search returns Result<index, insertion_point>
match numbers.binary_search(&7) {
    Ok(index) => println!("Found at index {}", index), // Found at index 3
    Err(index) => println!("Not found, would insert at {}", index),
}

// Search for non-existent element
match numbers.binary_search(&6) {
    Ok(index) => println!("Found at index {}", index),
    Err(index) => println!("Not found, would insert at {}", index), // 3
}
```

**Visualization:**
```
numbers = [1, 3, 5, 7, 9, 11, 13, 15]
Search for 7:

Step 1: Check middle (index 4): 9 > 7, search left half
        [1, 3, 5, 7] | 9, 11, 13, 15
        
Step 2: Check middle (index 1): 3 < 7, search right half
        1, 3 | [5, 7]
        
Step 3: Check middle (index 2): 5 < 7, search right half
        [7]
        
Step 4: Check index 3: 7 == 7, FOUND!
```

**Time Complexity**: O(log n) - halves search space each iteration.

### 8.3 Linear Search

```rust
let numbers = vec![3, 7, 1, 9, 4, 2];

// Find first occurrence
if let Some(index) = numbers.iter().position(|&x| x == 7) {
    println!("Found at index {}", index); // 1
}

// Check if contains (returns bool)
if numbers.contains(&9) {
    println!("Vector contains 9");
}

// Find with custom predicate
if let Some(index) = numbers.iter().position(|&x| x > 5) {
    println!("First element > 5 at index {}", index); // 1 (value 7)
}
```

**Time Complexity**: O(n) - must check each element in worst case.

---

## Part 9: Memory Management and Capacity

### 9.1 Understanding Capacity vs Length

```rust
let mut v = Vec::with_capacity(10);
println!("Length: {}, Capacity: {}", v.len(), v.capacity()); 
// Length: 0, Capacity: 10

v.push(1);
v.push(2);
v.push(3);
println!("Length: {}, Capacity: {}", v.len(), v.capacity());
// Length: 3, Capacity: 10

// Force reallocation
v.reserve(50); // Ensure capacity for 50 MORE elements
println!("Length: {}, Capacity: {}", v.len(), v.capacity());
// Length: 3, Capacity: 53 (original 3 + 50)
```

### 9.2 Shrinking Capacity

```rust
let mut v = Vec::with_capacity(1000);
for i in 0..10 {
    v.push(i);
}
println!("Before shrink - Len: {}, Cap: {}", v.len(), v.capacity());
// Before shrink - Len: 10, Cap: 1000

// Shrink to fit current length
v.shrink_to_fit();
println!("After shrink - Len: {}, Cap: {}", v.len(), v.capacity());
// After shrink - Len: 10, Cap: 10 (or close to it)
```

**When to use**:
- After bulk deletions
- When done growing a vector
- To minimize memory footprint

**Trade-off**: Reallocation cost vs memory savings.

### 9.3 Reserve Strategies

```rust
// Reserve exact additional capacity
let mut v = Vec::new();
v.reserve_exact(100); // Allocates exactly for 100 elements

// Reserve at least additional capacity (may allocate more)
let mut v2 = Vec::new();
v2.reserve(100); // May allocate more than 100 for growth
```

---

## Part 10: Advanced Patterns

### 10.1 Vector of Vectors (2D Arrays)

```rust
// Create 3x3 matrix
let mut matrix: Vec<Vec<i32>> = vec![
    vec![1, 2, 3],
    vec![4, 5, 6],
    vec![7, 8, 9],
];

// Access element at row 1, column 2
println!("{}", matrix[1][2]); // 6

// Iterate over 2D vector
for (i, row) in matrix.iter().enumerate() {
    for (j, &val) in row.iter().enumerate() {
        print!("matrix[{}][{}]={} ", i, j, val);
    }
    println!();
}

// Create dynamically
let rows = 5;
let cols = 5;
let mut dynamic_matrix = vec![vec![0; cols]; rows];
```

### 10.2 Splitting Vectors

```rust
let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8];

// Split at index
let (left, right) = numbers.split_at(4);
println!("Left: {:?}", left);   // [1, 2, 3, 4]
println!("Right: {:?}", right);  // [5, 6, 7, 8]

// Split by predicate
let parts: Vec<&[i32]> = numbers.split(|&x| x % 3 == 0).collect();
println!("{:?}", parts); // [[1, 2], [4, 5], [7, 8]]
```

### 10.3 Windows and Chunks

**Concept - Windows**: Overlapping slices of fixed size.

```rust
let numbers = vec![1, 2, 3, 4, 5];

// Sliding window of size 3
for window in numbers.windows(3) {
    println!("{:?}", window);
}
// Prints: [1, 2, 3], [2, 3, 4], [3, 4, 5]
```

**Concept - Chunks**: Non-overlapping slices.

```rust
let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9];

// Chunks of size 3
for chunk in numbers.chunks(3) {
    println!("{:?}", chunk);
}
// Prints: [1, 2, 3], [4, 5, 6], [7, 8, 9]

// Mutable chunks
let mut numbers = vec![1, 2, 3, 4, 5, 6];
for chunk in numbers.chunks_mut(2) {
    chunk[0] *= 10;
}
println!("{:?}", numbers); // [10, 2, 30, 4, 50, 6]
```

**Use Cases**:
- **Windows**: Moving averages, pattern detection
- **Chunks**: Batch processing, parallelization

---

## Part 11: Performance Considerations

### 11.1 Avoiding Allocations

```rust
// BAD: Creates new vector each iteration
fn inefficient() {
    for _ in 0..1000 {
        let mut v = Vec::new(); // Allocation
        v.push(1);
        v.push(2);
        // v dropped, deallocation
    }
}

// GOOD: Reuse vector
fn efficient() {
    let mut v = Vec::with_capacity(10);
    for _ in 0..1000 {
        v.clear(); // Just resets length
        v.push(1);
        v.push(2);
    }
}
```

### 11.2 Iterator Efficiency

```rust
let numbers: Vec<i32> = (0..1_000_000).collect();

// SLOWER: Allocates intermediate vectors
let result1: Vec<i32> = numbers.iter()
    .map(|&x| x * 2)
    .collect::<Vec<_>>() // Allocation
    .iter()
    .filter(|&&x| x % 4 == 0)
    .copied()
    .collect(); // Another allocation

// FASTER: Single pass, single allocation
let result2: Vec<i32> = numbers.iter()
    .map(|&x| x * 2)
    .filter(|&x| x % 4 == 0)
    .collect(); // One allocation only
```

**Key Insight**: Iterators are **lazy** and **composable**. Chain operations before collecting.

### 11.3 Cache-Friendly Access

```rust
// GOOD: Sequential access (cache-friendly)
fn sum_sequential(matrix: &Vec<Vec<i32>>) -> i32 {
    matrix.iter()
        .flat_map(|row| row.iter())
        .sum()
}

// BAD: Column-wise access (cache-unfriendly)
fn sum_columns(matrix: &Vec<Vec<i32>>) -> i32 {
    let mut sum = 0;
    if matrix.is_empty() { return 0; }
    let cols = matrix[0].len();
    
    for col in 0..cols {
        for row in matrix {
            sum += row[col]; // Jumps between rows
        }
    }
    sum
}
```

**Principle**: Access memory sequentially when possible. Modern CPUs prefetch sequential data into cache.

---

## Part 12: Common DSA Patterns with Vectors

### Pattern 1: Two Pointers

```rust
// Remove duplicates from sorted vector IN-PLACE
fn remove_duplicates(nums: &mut Vec<i32>) -> usize {
    if nums.is_empty() {
        return 0;
    }
    
    let mut write_idx = 1;
    
    for read_idx in 1..nums.len() {
        if nums[read_idx] != nums[read_idx - 1] {
            nums[write_idx] = nums[read_idx];
            write_idx += 1;
        }
    }
    
    nums.truncate(write_idx); // Remove excess elements
    write_idx
}

// Test
let mut v = vec![1, 1, 2, 2, 2, 3, 4, 4, 5];
let len = remove_duplicates(&mut v);
println!("{:?}, unique count: {}", v, len);
// [1, 2, 3, 4, 5], unique count: 5
```

**Visualization:**
```
Input: [1, 1, 2, 2, 2, 3, 4, 4, 5]
        ↑     ↑
      write  read

Step-by-step:
read=1: 1==1, skip
read=2: 2!=1, write 2 at index 1, write++
read=3: 2==2, skip
read=4: 2==2, skip
read=5: 3!=2, write 3 at index 2, write++
...
```

### Pattern 2: Sliding Window

```rust
// Find maximum sum of subarray of size k
fn max_sum_subarray(nums: &[i32], k: usize) -> Option<i32> {
    if nums.len() < k {
        return None;
    }
    
    // Initialize first window
    let mut window_sum: i32 = nums[0..k].iter().sum();
    let mut max_sum = window_sum;
    
    // Slide window
    for i in k..nums.len() {
        window_sum = window_sum - nums[i - k] + nums[i];
        max_sum = max_sum.max(window_sum);
    }
    
    Some(max_sum)
}

// Test
let nums = vec![1, 4, 2, 10, 23, 3, 1, 0, 20];
println!("{:?}", max_sum_subarray(&nums, 4)); // Some(39) -> [10,23,3,1]
```

### Pattern 3: Prefix Sum

```rust
// Build prefix sum array for O(1) range queries
struct PrefixSum {
    prefix: Vec<i32>,
}

impl PrefixSum {
    fn new(nums: &[i32]) -> Self {
        let mut prefix = vec![0; nums.len() + 1];
        for i in 0..nums.len() {
            prefix[i + 1] = prefix[i] + nums[i];
        }
        PrefixSum { prefix }
    }
    
    // Sum of elements from index left to right (inclusive)
    fn range_sum(&self, left: usize, right: usize) -> i32 {
        self.prefix[right + 1] - self.prefix[left]
    }
}

// Test
let nums = vec![1, 2, 3, 4, 5];
let ps = PrefixSum::new(&nums);
println!("{}", ps.range_sum(1, 3)); // 2+3+4 = 9
println!("{}", ps.range_sum(0, 4)); // 1+2+3+4+5 = 15
```

---

## Part 13: Complete Example - Implementation of a Stack

```rust
/// Stack implementation using Vec<T>
/// Demonstrates: Generic types, encapsulation, idiomatic Rust
pub struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    /// Create new empty stack
    pub fn new() -> Self {
        Stack { items: Vec::new() }
    }
    
    /// Create stack with pre-allocated capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Stack {
            items: Vec::with_capacity(capacity),
        }
    }
    
    /// Push item onto stack - O(1) amortized
    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }
    
    /// Pop item from stack - O(1)
    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    
    /// Peek at top item without removing - O(1)
    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }
    
    /// Check if stack is empty
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
    
    /// Get number of items in stack
    pub fn len(&self) -> usize {
        self.items.len()
    }
    
    /// Clear all items from stack
    pub fn clear(&mut self) {
        self.items.clear();
    }
}

// Usage example
fn main() {
    let mut stack = Stack::new();
    
    stack.push(1);
    stack.push(2);
    stack.push(3);
    
    println!("Top: {:?}", stack.peek()); // Some(3)
    println!("Pop: {:?}", stack.pop());   // Some(3)
    println!("Pop: {:?}", stack.pop());   // Some(2)
    println!("Length: {}", stack.len());  // 1
    
    stack.clear();
    println!("Empty: {}", stack.is_empty()); // true
}
```

---

## Part 14: Psychological Model - Deliberate Practice Framework

### Chunking Strategy for Vectors

Your brain learns patterns, not isolated facts. Here's how to chunk vector operations:

**Chunk 1: Creation Patterns**
- Empty → Type annotation needed
- Initialized → Type inferred
- Capacity → Performance optimization

**Chunk 2: Growth Patterns**
- End modification (push/pop) → O(1)
- Middle modification (insert/remove) → O(n)
- Bulk operations (extend/append) → Amortized O(1)

**Chunk 3: Access Patterns**
- Direct index → Fast but can panic
- Safe access (get) → Returns Option
- Iteration → Borrow/Mutable/Consume

**Chunk 4: Transformation Patterns**
- Map → Transform each
- Filter → Select subset
- Fold → Aggregate to single value

### Mental Model: Vector as a Dynamic Array

```
Conceptual Model:
┌─────────────────────────────────────┐
│ Stack: Vec metadata (ptr, len, cap) │
├─────────────────────────────────────┤
│ Heap: Contiguous element storage    │
│ [elem₀][elem₁][elem₂]...[elemₙ]     │
└─────────────────────────────────────┘

Operations map to memory:
• push()    → append to end, maybe reallocate
• pop()     → decrement length
• insert()  → shift right + insert
• remove()  → shift left after removal
```

---

## Summary: Core Principles

1. **Vectors are heap-allocated, growable arrays** with O(1) amortized push
2. **Capacity ≥ Length** always; reallocations happen at capacity
3. **Three reference types**: `&T` (borrow), `&mut T` (mutable), `T` (move)
4. **Prefer iterators** over index loops for safety and performance
5. **Pre-allocate when possible** to avoid reallocations
6. **Use `get()` for safe access**, `[]` for performance-critical paths
7. **Understand trade-offs**: `remove()` vs `swap_remove()`, `Vec` vs other collections

---

This comprehensive guide forms your foundation. As you progress, you'll recognize these patterns in complex algorithms and build increasingly sophisticated solutions.

**Next Steps for Mastery:**
1. Implement classic algorithms using vectors (merge sort, quicksort, binary search)
2. Solve problems requiring 2D vectors (matrices, graphs as adjacency lists)
3. Build data structures on top of vectors (heaps, deques, circular buffers)
4. Profile and optimize vector-heavy code

Your journey to the top 1% is built on this foundation. Master these fundamentals with clarity and precision. 🔥