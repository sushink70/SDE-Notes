# The Complete Guide to Generic Data Types in Rust

## I. Foundational Philosophy: Why Generics Exist

Generics enable **zero-cost abstraction** — the ability to write code that works with multiple types while maintaining compile-time type safety and runtime performance identical to hand-written type-specific code. Rust's generics are monomorphized at compile time, meaning the compiler generates specialized versions of your code for each concrete type used.

This is **fundamentally different** from runtime polymorphism (vtables/dynamic dispatch). Understanding this distinction is critical for top-tier systems programming.

---

## II. Core Syntax and Mechanics

### 2.1 Basic Generic Functions

```rust
// Simple generic function
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    largest
}

// Multiple type parameters
fn mix<T, U>(x: T, y: U) -> (T, U) {
    (x, y)
}

// Generic with lifetime parameters
fn longest<'a, T: PartialOrd>(x: &'a T, y: &'a T) -> &'a T {
    if x > y { x } else { y }
}
```

**Mental Model**: The `<T>` declaration introduces a type variable. The compiler will generate a separate function for each concrete type you use (monomorphization).

### 2.2 Generic Structs

```rust
struct Point<T> {
    x: T,
    y: T,
}

// Different types for x and y
struct MixedPoint<T, U> {
    x: T,
    y: U,
}

// Implementation block for generic struct
impl<T> Point<T> {
    fn x(&self) -> &T {
        &self.x
    }
}

// Implementation for SPECIFIC type
impl Point<f64> {
    fn distance_from_origin(&self) -> f64 {
        (self.x.powi(2) + self.y.powi(2)).sqrt()
    }
}

// Generic methods with additional type parameters
impl<T> Point<T> {
    fn mixup<U>(self, other: Point<U>) -> Point<(T, U)> {
        Point {
            x: (self.x, other.x),
            y: (self.y, other.y),
        }
    }
}
```

**Critical Insight**: When you write `impl<T>`, you're saying "this implementation works for ANY type T". When you write `impl Point<f64>`, you're specializing for `f64` only.

### 2.3 Generic Enums

```rust
// The canonical example
enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}

// Custom generic enum
enum TreeNode<T> {
    Leaf(T),
    Branch {
        value: T,
        left: Box<TreeNode<T>>,
        right: Box<TreeNode<T>>,
    },
}
```

---

## III. Trait Bounds: The Heart of Generic Constraints

### 3.1 Basic Trait Bounds

```rust
use std::fmt::Display;

// Trait bound syntax
fn print_largest<T: PartialOrd + Display>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    println!("The largest value is: {}", largest);
    largest
}

// Where clause syntax (preferred for complex bounds)
fn complex_function<T, U>(t: &T, u: &U) -> i32
where
    T: Display + Clone,
    U: Clone + Debug,
{
    println!("t: {}", t);
    0
}
```

**Why Where Clauses Matter**: They improve readability when you have multiple bounds, and they're required for certain advanced patterns like conditional trait implementations.

### 3.2 Multiple Bounds and Combining Traits

```rust
use std::fmt::Debug;
use std::cmp::PartialOrd;

fn compare_and_print<T>(a: &T, b: &T) -> &T
where
    T: PartialOrd + Debug,
{
    let result = if a > b { a } else { b };
    println!("Comparing: {:?} and {:?}", a, b);
    result
}

// Using + operator for multiple bounds
fn notify<T: Display + Clone>(item: &T) {
    println!("Breaking news! {}", item);
}
```

### 3.3 Return Position impl Trait

```rust
use std::fmt::Display;

// Return "some type that implements Display"
fn returns_summarizable() -> impl Display {
    String::from("Hello, world!")
}

// Useful for closures and iterators
fn make_adder(x: i32) -> impl Fn(i32) -> i32 {
    move |y| x + y
}

// Iterator example
fn double_positives(numbers: &[i32]) -> impl Iterator<Item = i32> + '_ {
    numbers.iter()
        .filter(|x| **x > 0)
        .map(|x| x * 2)
}
```

**Critical Limitation**: You can only return ONE concrete type with `impl Trait`. You cannot conditionally return different types.

---

## IV. Advanced Trait Bound Patterns

### 4.1 Conditional Method Implementation

```rust
use std::fmt::Display;

struct Pair<T> {
    x: T,
    y: T,
}

// Methods available for ALL types
impl<T> Pair<T> {
    fn new(x: T, y: T) -> Self {
        Self { x, y }
    }
}

// Methods ONLY for types implementing Display + PartialOrd
impl<T: Display + PartialOrd> Pair<T> {
    fn cmp_display(&self) {
        if self.x >= self.y {
            println!("The largest member is x = {}", self.x);
        } else {
            println!("The largest member is y = {}", self.y);
        }
    }
}
```

### 4.2 Blanket Implementations

```rust
// From the standard library
trait ToString {
    fn to_string(&self) -> String;
}

// Blanket implementation: ANY type implementing Display gets ToString
impl<T: Display> ToString for T {
    fn to_string(&self) -> String {
        format!("{}", self)
    }
}
```

**This is profound**: Blanket implementations allow you to automatically provide trait implementations for entire categories of types.

### 4.3 Associated Types vs Generic Type Parameters

```rust
// Using generics - can implement Iterator multiple times for different types
trait Iterator<T> {
    fn next(&mut self) -> Option<T>;
}

// Using associated types - can only implement once per type
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}

// Real-world example with associated types
struct Counter {
    count: u32,
}

impl Iterator for Counter {
    type Item = u32;
    
    fn next(&mut self) -> Option<Self::Item> {
        self.count += 1;
        if self.count < 6 {
            Some(self.count)
        } else {
            None
        }
    }
}
```

**Decision Rule**: 
- Use **generic type parameters** when you want multiple implementations of a trait for the same type
- Use **associated types** when there's only one logical implementation per type

---

## V. Lifetime Parameters with Generics

### 5.1 Basic Lifetime with Generics

```rust
// Generic type with lifetime
struct ImportantExcerpt<'a, T> {
    part: &'a T,
}

impl<'a, T> ImportantExcerpt<'a, T> {
    fn level(&self) -> i32 {
        3
    }
}

// Lifetime elision doesn't work here
impl<'a, T> ImportantExcerpt<'a, T> {
    fn announce_and_return_part(&self, announcement: &str) -> &T {
        println!("Attention please: {}", announcement);
        self.part
    }
}
```

### 5.2 Complex Lifetime Bounds

```rust
use std::fmt::Display;

// T must outlive 'a
fn longest_with_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement! {}", ann);
    if x.len() > y.len() { x } else { y }
}

// Multiple lifetime parameters
struct DoubleRef<'a, 'b, T> {
    first: &'a T,
    second: &'b T,
}
```

---

## VI. Const Generics (Modern Rust)

### 6.1 Array Lengths as Generic Parameters

```rust
// OLD WAY (pre const generics): arrays of different sizes were different types
// NEW WAY: parametrize by length

struct ArrayWrapper<T, const N: usize> {
    data: [T; N],
}

impl<T: Default + Copy, const N: usize> ArrayWrapper<T, N> {
    fn new() -> Self {
        Self {
            data: [T::default(); N],
        }
    }
}

// Usage
let arr5: ArrayWrapper<i32, 5> = ArrayWrapper::new();
let arr10: ArrayWrapper<i32, 10> = ArrayWrapper::new();
```

### 6.2 Compile-Time Computation

```rust
fn print_array<T: std::fmt::Debug, const N: usize>(arr: [T; N]) {
    println!("Array of {} elements: {:?}", N, arr);
}

// Matrix with compile-time size checking
struct Matrix<T, const ROWS: usize, const COLS: usize> {
    data: [[T; COLS]; ROWS],
}

impl<T, const N: usize> Matrix<T, N, N> {
    // This method only exists for square matrices
    fn is_square(&self) -> bool {
        true
    }
}
```

**Performance Insight**: Const generics enable zero-cost abstractions for fixed-size data structures. The compiler knows the exact size at compile time, enabling optimal code generation.

---

## VII. Performance and Optimization Considerations

### 7.1 Monomorphization Cost

```rust
// This function will be compiled THREE times
fn process<T: Display>(x: T) {
    println!("{}", x);
}

fn main() {
    process(5i32);        // Generates process_i32
    process(5.0f64);      // Generates process_f64
    process("hello");     // Generates process_str
}
```

**Trade-off**: 
- **Binary size increases** with each concrete type used
- **Runtime performance is optimal** (no vtable lookups)
- For infrequently used types, consider `dyn Trait` instead

### 7.2 Dynamic Dispatch Alternative

```rust
use std::fmt::Display;

// Static dispatch (monomorphization)
fn static_print<T: Display>(x: &T) {
    println!("{}", x);
}

// Dynamic dispatch (trait objects)
fn dynamic_print(x: &dyn Display) {
    println!("{}", x);
}

// Performance comparison
fn benchmark() {
    let x = 42;
    static_print(&x);   // Faster, larger binary
    dynamic_print(&x);  // Slower (vtable), smaller binary
}
```

---

## VIII. Real-World Generic Data Structures

### 8.1 Generic Binary Search Tree

```rust
use std::cmp::Ordering;

#[derive(Debug)]
struct BST<T: Ord> {
    root: Option<Box<Node<T>>>,
}

#[derive(Debug)]
struct Node<T: Ord> {
    value: T,
    left: Option<Box<Node<T>>>,
    right: Option<Box<Node<T>>>,
}

impl<T: Ord> BST<T> {
    fn new() -> Self {
        BST { root: None }
    }

    fn insert(&mut self, value: T) {
        match &mut self.root {
            None => self.root = Some(Box::new(Node {
                value,
                left: None,
                right: None,
            })),
            Some(node) => node.insert(value),
        }
    }

    fn contains(&self, value: &T) -> bool {
        match &self.root {
            None => false,
            Some(node) => node.contains(value),
        }
    }
}

impl<T: Ord> Node<T> {
    fn insert(&mut self, value: T) {
        match value.cmp(&self.value) {
            Ordering::Less => match &mut self.left {
                None => self.left = Some(Box::new(Node {
                    value,
                    left: None,
                    right: None,
                })),
                Some(node) => node.insert(value),
            },
            Ordering::Greater => match &mut self.right {
                None => self.right = Some(Box::new(Node {
                    value,
                    left: None,
                    right: None,
                })),
                Some(node) => node.insert(value),
            },
            Ordering::Equal => {} // Value already exists
        }
    }

    fn contains(&self, value: &T) -> bool {
        match value.cmp(&self.value) {
            Ordering::Equal => true,
            Ordering::Less => self.left.as_ref().map_or(false, |n| n.contains(value)),
            Ordering::Greater => self.right.as_ref().map_or(false, |n| n.contains(value)),
        }
    }
}
```

### 8.2 Generic Stack with Different Storage Strategies

```rust
// Generic stack with Vec backend
struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self {
        Stack { items: Vec::new() }
    }

    fn push(&mut self, item: T) {
        self.items.push(item);
    }

    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }

    fn peek(&self) -> Option<&T> {
        self.items.last()
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    fn len(&self) -> usize {
        self.items.len()
    }
}

// Fixed-capacity stack using const generics
struct FixedStack<T, const CAP: usize> {
    items: [Option<T>; CAP],
    len: usize,
}

impl<T: Copy, const CAP: usize> FixedStack<T, CAP> {
    fn new() -> Self {
        FixedStack {
            items: [None; CAP],
            len: 0,
        }
    }

    fn push(&mut self, item: T) -> Result<(), T> {
        if self.len < CAP {
            self.items[self.len] = Some(item);
            self.len += 1;
            Ok(())
        } else {
            Err(item) // Stack full
        }
    }

    fn pop(&mut self) -> Option<T> {
        if self.len > 0 {
            self.len -= 1;
            self.items[self.len].take()
        } else {
            None
        }
    }
}
```

---

## IX. Common Trait Bounds Reference

```rust
// Copyable types
fn duplicate<T: Copy>(x: T) -> (T, T) {
    (x, x)
}

// Cloneable types
fn clone_and_modify<T: Clone>(x: T) -> T {
    let mut y = x.clone();
    y
}

// Debug printing
fn debug_print<T: std::fmt::Debug>(x: T) {
    println!("{:?}", x);
}

// Default constructible
fn make_default<T: Default>() -> T {
    T::default()
}

// Comparable types
fn min<T: Ord>(a: T, b: T) -> T {
    if a < b { a } else { b }
}

// Partially comparable (allows NaN for floats)
fn partial_min<T: PartialOrd>(a: T, b: T) -> Option<T> {
    if a < b {
        Some(a)
    } else if a >= b {
        Some(b)
    } else {
        None // Uncomparable (e.g., NaN)
    }
}

// Sized types (most types are Sized by default)
fn sized<T: Sized>(x: T) {}

// Unsized types
fn unsized<T: ?Sized>(x: &T) {}
```

---

## X. Advanced Patterns and Idioms

### 10.1 PhantomData for Zero-Sized Type Parameters

```rust
use std::marker::PhantomData;

struct Meter;
struct Foot;

struct Distance<Unit> {
    value: f64,
    _marker: PhantomData<Unit>,
}

impl<Unit> Distance<Unit> {
    fn new(value: f64) -> Self {
        Distance {
            value,
            _marker: PhantomData,
        }
    }
}

// Type-safe conversions
impl Distance<Meter> {
    fn to_feet(self) -> Distance<Foot> {
        Distance::new(self.value * 3.28084)
    }
}

impl Distance<Foot> {
    fn to_meters(self) -> Distance<Meter> {
        Distance::new(self.value / 3.28084)
    }
}
```

**Use Case**: Compile-time enforcement of units, state machines, type-level programming.

### 10.2 Generic New Type Pattern

```rust
struct Wrapper<T>(T);

impl<T: std::fmt::Display> Wrapper<T> {
    fn print(&self) {
        println!("Wrapped value: {}", self.0);
    }
}

// Orphan rule circumvention
impl<T> std::fmt::Display for Wrapper<Vec<T>> 
where
    T: std::fmt::Display,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[")?;
        for (i, item) in self.0.iter().enumerate() {
            if i > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{}", item)?;
        }
        write!(f, "]")
    }
}
```

### 10.3 Generic Builder Pattern

```rust
struct ConfigBuilder<T, U> {
    value1: Option<T>,
    value2: Option<U>,
}

impl<T, U> ConfigBuilder<T, U> {
    fn new() -> Self {
        ConfigBuilder {
            value1: None,
            value2: None,
        }
    }

    fn value1(mut self, v: T) -> Self {
        self.value1 = Some(v);
        self
    }

    fn value2(mut self, v: U) -> Self {
        self.value2 = Some(v);
        self
    }

    fn build(self) -> Result<Config<T, U>, &'static str> {
        Ok(Config {
            value1: self.value1.ok_or("value1 not set")?,
            value2: self.value2.ok_or("value2 not set")?,
        })
    }
}

struct Config<T, U> {
    value1: T,
    value2: U,
}
```

---

## XI. Mental Models for Mastery

### Cognitive Framework 1: Type-Level Computation
Think of generics as **compile-time computation**. You're writing code that the compiler executes to generate more code. Every generic parameter is an input to this computation.

### Cognitive Framework 2: Constraint-Based Thinking
Generics without bounds are **too flexible** (can't do anything useful). Trait bounds are **constraints that unlock capabilities**. More specific bounds = more operations available.

### Cognitive Framework 3: Zero-Cost Mindset
Always remember: generics in Rust are **completely free at runtime**. Every abstraction cost is paid at compile time. This is your superpower compared to languages with runtime generics.

---

## XII. Common Pitfalls and Solutions

### Pitfall 1: Unnecessary Cloning

```rust
// INEFFICIENT
fn process_bad<T: Clone>(items: Vec<T>) -> Vec<T> {
    items.iter().map(|x| x.clone()).collect()
}

// EFFICIENT
fn process_good<T>(items: Vec<T>) -> Vec<T> {
    items // Just move it
}
```

### Pitfall 2: Over-Constraining

```rust
// TOO RESTRICTIVE - requires both Clone AND Copy
fn bad<T: Clone + Copy>(x: T) -> T {
    x // Copy is sufficient here
}

// BETTER
fn good<T: Copy>(x: T) -> T {
    x
}
```

### Pitfall 3: Type Inference Failures

```rust
// Compiler can't infer T
fn collect_into<T>() -> Vec<T> {
    vec![]
}

// FIX: Add context or turbofish
let v: Vec<i32> = collect_into();
let v = collect_into::<i32>();
```

---

## XIII. Benchmarking Generic vs Non-Generic Code

```rust
// Monomorphized version (fast)
#[inline]
fn add_generic<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
}

// Specialized version (same speed after compilation)
#[inline]
fn add_i32(a: i32, b: i32) -> i32 {
    a + b
}

// Both compile to identical assembly when called with i32
// Verify with: cargo rustc --release -- --emit asm
```

---

## Final Synthesis

Generics in Rust represent the pinnacle of **type-safe, zero-cost abstraction**. You write code once, and the compiler generates optimized machine code for every concrete type you use—with no runtime overhead.

**Master these principles:**
1. Generics are monomorphized (specialized) at compile time
2. Trait bounds define capabilities, not just restrictions
3. Associated types vs type parameters: one vs many implementations
4. Const generics enable compile-time array operations
5. PhantomData enables type-level state machines

**Your next step:** Implement a generic LRU cache with const-generic capacity, custom trait bounds for keys, and zero heap allocations. This will integrate everything you've learned.

You're building the foundation for world-class systems programming. Each generic you write correctly is a step toward the top 1%.