# Comprehensive Guide to Processing Series of Items with Iterators in Rust

Iterators are the **soul of Rust's performance-oriented, zero-cost abstraction philosophy**. Mastering them is non-negotiable for reaching the top 1%. This guide will forge your intuition from first principles to advanced patterns.

---

## I. Foundational Mental Model: What Are Iterators?

### The Core Abstraction
An iterator is a **stateful producer** of values. It answers one question repeatedly:
```rust
fn next(&mut self) -> Option<T>
```

**Key Insight**: Iterators are *lazy* — they produce values on demand, enabling composition without intermediate allocations.

### The Iterator Trait
```rust
pub trait Iterator {
    type Item;
    
    fn next(&mut self) -> Option<Self::Item>;
    
    // 70+ default methods built on `next`
    fn size_hint(&self) -> (usize, Option<usize>) { (0, None) }
    // ... map, filter, fold, etc.
}
```

**Mental Model**: `Iterator` is a *protocol*. `next` is the minimal contract; everything else is *derived functionality*.

---

## II. The Three Fundamental Patterns

### 1. **IntoIterator** - Creating Iterators

Every collection can be consumed in three ways:

```rust
let vec = vec![1, 2, 3, 4, 5];

// 1. By value - consumes the collection
for x in vec { }  // vec is moved

// 2. By immutable reference
for x in &vec { }  // &i32

// 3. By mutable reference  
for x in &mut vec { }  // &mut i32
```

**Under the hood**:
```rust
pub trait IntoIterator {
    type Item;
    type IntoIter: Iterator<Item = Self::Item>;
    
    fn into_iter(self) -> Self::IntoIter;
}

// Vec implements all three:
impl<T> IntoIterator for Vec<T> { /* by value */ }
impl<'a, T> IntoIterator for &'a Vec<T> { /* by ref */ }
impl<'a, T> IntoIterator for &'a mut Vec<T> { /* by mut ref */ }
```

**Cognitive Principle**: This trichotomy mirrors Rust's ownership system. Choose based on whether you need to *consume*, *observe*, or *modify*.

---

### 2. **Iterator Adapters** - Lazy Transformations

Adapters are **zero-cost builders** that create new iterators without executing:

```rust
let vec = vec![1, 2, 3, 4, 5];

// No work happens here - just iterator construction
let iter = vec.iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * x);

// Work happens only during consumption
for x in iter {
    println!("{}", x);  // 4, 16
}
```

**Critical Adapters** (Master These First):

#### a) **map** - Transform Each Element
```rust
// Type transformation
let squared: Vec<i32> = (1..=5)
    .map(|x| x * x)
    .collect();

// Complexity: O(1) space (lazy), O(n) when collected
```

#### b) **filter** - Conditional Selection
```rust
let evens: Vec<i32> = (1..=10)
    .filter(|&x| x % 2 == 0)
    .collect();

// Pattern: Use `&x` in closure when iterating over references
```

#### c) **filter_map** - Map + Filter in One Pass
```rust
// Instead of map().filter_map() - do both atomically
let results: Vec<i32> = vec!["1", "two", "3"]
    .iter()
    .filter_map(|s| s.parse::<i32>().ok())
    .collect();  // [1, 3]

// Superior to: .map(parse).filter(is_ok).map(unwrap)
```

#### d) **flat_map** - Flatten Nested Structures
```rust
// Generate all pairs
let pairs: Vec<(i32, i32)> = (1..=3)
    .flat_map(|i| (1..=3).map(move |j| (i, j)))
    .collect();
// [(1,1), (1,2), (1,3), (2,1), (2,2), (2,3), (3,1), (3,2), (3,3)]
```

#### e) **take** / **skip** - Slicing
```rust
let middle: Vec<i32> = (0..10)
    .skip(3)     // Skip first 3
    .take(4)     // Take next 4
    .collect();  // [3, 4, 5, 6]
```

#### f) **enumerate** - Add Indices
```rust
for (idx, val) in vec.iter().enumerate() {
    println!("Index {}: {}", idx, val);
}
```

#### g) **zip** - Parallel Iteration
```rust
let a = vec![1, 2, 3];
let b = vec!['a', 'b', 'c'];

let pairs: Vec<(i32, char)> = a.iter()
    .zip(b.iter())
    .map(|(&x, &y)| (x, y))
    .collect();
```

#### h) **chain** - Concatenate Iterators
```rust
let combined: Vec<i32> = (1..=3)
    .chain(10..=12)
    .collect();  // [1, 2, 3, 10, 11, 12]
```

---

### 3. **Consumers** - Materializing Results

Consumers **execute** the iterator pipeline and produce final values:

#### a) **collect** - Universal Materializer
```rust
use std::collections::{HashSet, HashMap};

let vec: Vec<i32> = (1..=5).collect();
let set: HashSet<i32> = (1..=5).collect();
let map: HashMap<i32, i32> = (1..=5)
    .map(|x| (x, x * x))
    .collect();

// Turbofish when type inference fails
let vec = (1..=5).collect::<Vec<_>>();
```

#### b) **fold** - The Universal Reducer
```rust
// Sum
let sum = (1..=5).fold(0, |acc, x| acc + x);  // 15

// Product
let product = (1..=5).fold(1, |acc, x| acc * x);  // 120

// Custom accumulation
let result = vec![1, 2, 3, 4, 5]
    .iter()
    .fold(Vec::new(), |mut acc, &x| {
        if x % 2 == 0 {
            acc.push(x);
        }
        acc
    });
```

**Complexity Analysis**: O(n) time, O(1) space (depends on accumulator).

#### c) **reduce** - Like fold, but uses first element
```rust
let max = (1..=5).reduce(|a, b| a.max(b));  // Some(5)

// Empty iterator returns None
let empty: Option<i32> = std::iter::empty().reduce(|a, b| a + b);  // None
```

#### d) **for_each** - Side Effects
```rust
(1..=5).for_each(|x| println!("{}", x));

// Equivalent to for-loop but signals intent
```

#### e) **count** / **sum** / **product**
```rust
let count = (1..=100).filter(|&x| x % 2 == 0).count();
let sum: i32 = (1..=100).sum();
let product: i32 = (1..=5).product();
```

#### f) **find** / **position**
```rust
let first_even = (1..=10).find(|&x| x % 2 == 0);  // Some(2)
let pos = (1..=10).position(|x| x % 2 == 0);      // Some(1)
```

#### g) **any** / **all**
```rust
let has_even = (1..=10).any(|x| x % 2 == 0);   // true
let all_positive = (1..=10).all(|x| x > 0);    // true
```

#### h) **min** / **max**
```rust
let min = (1..=10).min();  // Some(1)
let max = (1..=10).max();  // Some(10)

// Custom comparison
let min_by = vec![1, -5, 3, -2]
    .iter()
    .min_by_key(|&&x| x.abs());  // Some(&1)
```

---

## III. Performance Characteristics & Zero-Cost Abstractions

### The Guarantee
Iterator chains compile to **tight loops** equivalent to hand-written code:

```rust
// This high-level code...
let sum: i32 = (1..=1000000)
    .filter(|&x| x % 2 == 0)
    .map(|x| x * 2)
    .sum();

// ...compiles to roughly:
let mut sum = 0;
for x in 1..=1000000 {
    if x % 2 == 0 {
        sum += x * 2;
    }
}
```

**Benchmark Insight**: Use `cargo asm` or `cargo llvm-ir` to verify optimizations.

### Common Pitfalls

#### 1. Unnecessary Collect
```rust
// ❌ Inefficient - double iteration
let sum: i32 = vec
    .iter()
    .filter(|&&x| x % 2 == 0)
    .collect::<Vec<_>>()  // Allocates!
    .iter()
    .sum();

// ✅ Optimal - single pass
let sum: i32 = vec
    .iter()
    .filter(|&&x| x % 2 == 0)
    .sum();
```

#### 2. Clone in Map
```rust
// ❌ Clones every element
let owned: Vec<String> = vec
    .iter()
    .map(|s| s.clone())
    .collect();

// ✅ Use cloned() adapter
let owned: Vec<String> = vec
    .iter()
    .cloned()
    .collect();
```

---

## IV. Advanced Patterns

### 1. **Custom Iterators**

```rust
struct Fibonacci {
    curr: u64,
    next: u64,
}

impl Fibonacci {
    fn new() -> Self {
        Fibonacci { curr: 0, next: 1 }
    }
}

impl Iterator for Fibonacci {
    type Item = u64;
    
    fn next(&mut self) -> Option<Self::Item> {
        let current = self.curr;
        self.curr = self.next;
        self.next = current + self.next;
        Some(current)
    }
}

// Usage
let fibs: Vec<u64> = Fibonacci::new()
    .take(10)
    .collect();
```

### 2. **scan** - Stateful Mapping
```rust
// Running sum
let running_sum: Vec<i32> = vec![1, 2, 3, 4, 5]
    .iter()
    .scan(0, |state, &x| {
        *state += x;
        Some(*state)
    })
    .collect();  // [1, 3, 6, 10, 15]
```

### 3. **windows** & **chunks**
```rust
let vec = vec![1, 2, 3, 4, 5];

// Sliding windows
for window in vec.windows(3) {
    println!("{:?}", window);  // [1,2,3], [2,3,4], [3,4,5]
}

// Non-overlapping chunks
for chunk in vec.chunks(2) {
    println!("{:?}", chunk);  // [1,2], [3,4], [5]
}
```

### 4. **partition** - Split by Predicate
```rust
let (evens, odds): (Vec<i32>, Vec<i32>) = (1..=10)
    .partition(|&x| x % 2 == 0);
```

### 5. **group_by** (requires itertools crate)
```rust
use itertools::Itertools;

let groups: Vec<Vec<i32>> = vec![1, 1, 2, 2, 2, 3, 4, 4]
    .into_iter()
    .group_by(|&x| x)
    .into_iter()
    .map(|(_, group)| group.collect())
    .collect();  // [[1,1], [2,2,2], [3], [4,4]]
```

---

## V. Iterator Combinators - Problem-Solving Patterns

### Pattern 1: Two-Pointer Technique
```rust
fn two_sum(nums: Vec<i32>, target: i32) -> Option<(usize, usize)> {
    nums.iter()
        .enumerate()
        .flat_map(|(i, &a)| {
            nums.iter()
                .enumerate()
                .skip(i + 1)
                .filter_map(move |(j, &b)| {
                    if a + b == target {
                        Some((i, j))
                    } else {
                        None
                    }
                })
        })
        .next()
}
```

### Pattern 2: Cartesian Product
```rust
// All pairs (i, j) where i < j
let pairs: Vec<(i32, i32)> = (1..=5)
    .flat_map(|i| ((i+1)..=5).map(move |j| (i, j)))
    .collect();
```

### Pattern 3: Frequency Counting
```rust
use std::collections::HashMap;

let freq: HashMap<char, usize> = "hello"
    .chars()
    .fold(HashMap::new(), |mut map, c| {
        *map.entry(c).or_insert(0) += 1;
        map
    });
```

### Pattern 4: Early Termination
```rust
// Find first element satisfying condition
let first = vec
    .iter()
    .find(|&&x| x > 100);

// Take while condition holds
let prefix: Vec<i32> = vec
    .iter()
    .take_while(|&&x| x < 10)
    .copied()
    .collect();
```

---

## VI. Performance Deep Dive

### Complexity Table

| Adapter | Time | Space | Notes |
|---------|------|-------|-------|
| `map` | O(1) | O(1) | Lazy |
| `filter` | O(1) | O(1) | Lazy |
| `flat_map` | O(1) | O(1) | Lazy |
| `collect` | O(n) | O(n) | Materializes |
| `fold` | O(n) | O(1)* | *Depends on accumulator |
| `find` | O(n) | O(1) | Early exit |
| `zip` | O(1) | O(1) | Lazy |
| `enumerate` | O(1) | O(1) | Lazy |

### Optimization Checklist
1. **Avoid premature collect()** - keep chains lazy
2. **Use `copied()` / `cloned()` over `map(|x| *x)`**
3. **Prefer `filter_map` over `map().filter().map()`**
4. **Use `iter()` over `into_iter()` when possible** (avoid moves)
5. **Consider `par_iter()` from rayon for data parallelism**

---

## VII. Expert-Level Techniques

### 1. **Iterator Fusion**
```rust
// Compiler fuses these into single loop
let result: Vec<i32> = vec
    .iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * 2)
    .filter(|&x| x > 10)
    .map(|x| x + 1)
    .collect();
```

### 2. **Avoiding Allocations**
```rust
// ❌ Multiple allocations
fn process(data: &[i32]) -> Vec<i32> {
    data.iter()
        .filter(|&&x| x > 0)
        .map(|&x| x * 2)
        .collect()
}

// ✅ Single allocation with size_hint
fn process_optimized(data: &[i32]) -> Vec<i32> {
    let mut result = Vec::with_capacity(data.len());
    result.extend(
        data.iter()
            .filter(|&&x| x > 0)
            .map(|&x| x * 2)
    );
    result
}
```

### 3. **Custom Adapters via Extension Traits**
```rust
trait IteratorExt: Iterator {
    fn batched(self, size: usize) -> Batched<Self>
    where
        Self: Sized,
    {
        Batched {
            iter: self,
            size,
        }
    }
}

impl<T: Iterator> IteratorExt for T {}

struct Batched<I> {
    iter: I,
    size: usize,
}

impl<I: Iterator> Iterator for Batched<I> {
    type Item = Vec<I::Item>;
    
    fn next(&mut self) -> Option<Self::Item> {
        let batch: Vec<_> = self.iter.by_ref().take(self.size).collect();
        if batch.is_empty() {
            None
        } else {
            Some(batch)
        }
    }
}
```

---

## VIII. Mental Models for Mastery

### 1. **Think in Pipelines**
Visualize data flowing through transformations:
```
[1,2,3,4,5] → filter(even) → [2,4] → map(square) → [4,16] → sum → 20
```

### 2. **Composition Over Iteration**
Instead of thinking "loop over items", think "what transformations produce my result?"

### 3. **Lazy Evaluation**
No work happens until a consumer is called. This enables:
- **Infinite iterators** (e.g., Fibonacci)
- **Early termination**
- **Memory efficiency**

### 4. **Cognitive Chunking**
Master adapters in groups:
- **Filtering**: `filter`, `filter_map`, `take`, `skip`, `take_while`
- **Transformation**: `map`, `flat_map`, `scan`
- **Consumption**: `fold`, `reduce`, `collect`, `for_each`
- **Inspection**: `find`, `position`, `any`, `all`

---

## IX. Deliberate Practice Exercises

1. **Implement `flatten` manually** using `flat_map`
2. **Write `group_by`** without external crates
3. **Create a `cycle` iterator** that repeats forever
4. **Benchmark** iterator chains vs explicit loops
5. **Solve sliding window maximum** using iterators

---

## X. The Path Forward

**Week 1-2**: Master fundamental adapters (map, filter, fold)  
**Week 3-4**: Custom iterators + advanced patterns  
**Week 5+**: Apply to algorithmic problems (LeetCode with iterator-first thinking)

Iterators aren't just syntax — they're a **way of thinking**. The top 1% see problems as data transformations, not loops.

Now go forth and **transmute data with zero-cost elegance**.