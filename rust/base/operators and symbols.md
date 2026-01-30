# Comprehensive Guide to Rust Operators and Symbols

This guide covers all operators and symbols in Rust, organized by category with production-ready examples and real-world use cases.

---

## 1. Arithmetic Operators

### Basic Arithmetic
```rust
let a = 10;
let b = 3;

let sum = a + b;        // 13
let diff = a - b;       // 7
let prod = a * b;       // 30
let quot = a / b;       // 3 (integer division)
let rem = a % b;        // 1 (modulo/remainder)
```

### Compound Assignment
```rust
let mut x = 10;
x += 5;   // x = x + 5  → 15
x -= 3;   // x = x - 3  → 12
x *= 2;   // x = x * 2  → 24
x /= 4;   // x = x / 4  → 6
x %= 4;   // x = x % 4  → 2
```

**Production Pattern: Safe Math Operations**
```rust
// Prevent overflow panics in production
fn safe_add(a: u32, b: u32) -> Option<u32> {
    a.checked_add(b)
}

fn saturating_multiply(a: u32, b: u32) -> u32 {
    a.saturating_mul(b) // Clamps at max value instead of overflowing
}
```

---

## 2. Comparison Operators

```rust
let x = 5;
let y = 10;

x == y   // false (equality)
x != y   // true  (inequality)
x < y    // true  (less than)
x > y    // false (greater than)
x <= y   // true  (less than or equal)
x >= y   // false (greater than or equal)
```

**Key Insight:** Comparison operators require both operands to implement the `PartialEq` and `PartialOrd` traits.

```rust
#[derive(Debug, PartialEq, PartialOrd)]
struct Version {
    major: u32,
    minor: u32,
    patch: u32,
}

let v1 = Version { major: 1, minor: 0, patch: 0 };
let v2 = Version { major: 2, minor: 0, patch: 0 };

assert!(v1 < v2); // Lexicographic comparison
```

---

## 3. Logical Operators

```rust
let t = true;
let f = false;

!t        // false (logical NOT)
t && f    // false (logical AND, short-circuits)
t || f    // true  (logical OR, short-circuits)
```

**Short-Circuit Evaluation:**
```rust
fn expensive_check() -> bool {
    println!("This is expensive!");
    true
}

// expensive_check() is NEVER called because false && ... always returns false
if false && expensive_check() {
    println!("Won't print");
}

// expensive_check() is NEVER called because true || ... always returns true
if true || expensive_check() {
    println!("Will print without calling expensive_check");
}
```

---

## 4. Bitwise Operators

```rust
let a = 0b1010; // 10 in binary
let b = 0b1100; // 12 in binary

a & b     // 0b1000 (8)  - AND
a | b     // 0b1110 (14) - OR
a ^ b     // 0b0110 (6)  - XOR
!a        // Bitwise NOT (depends on type size)
a << 1    // 0b10100 (20) - Left shift
a >> 1    // 0b0101 (5)   - Right shift

// Compound assignment
let mut x = 0b1010;
x &= 0b1100;  // x = x & 0b1100
x |= 0b0011;  // x = x | 0b0011
x ^= 0b1111;  // x = x ^ 0b1111
x <<= 2;      // x = x << 2
x >>= 1;      // x = x >> 1
```

**Production Use Case: Bit Flags**
```rust
bitflags::bitflags! {
    struct Permissions: u32 {
        const READ    = 0b0001;
        const WRITE   = 0b0010;
        const EXECUTE = 0b0100;
        const ADMIN   = 0b1000;
    }
}

let user_perms = Permissions::READ | Permissions::WRITE;
if user_perms.contains(Permissions::WRITE) {
    println!("User can write");
}

// Toggle a permission
let mut perms = Permissions::READ;
perms ^= Permissions::WRITE; // Toggle write permission
```

---

## 5. Dereference and Reference Operators

### Reference (`&`) and Mutable Reference (`&mut`)
```rust
let x = 5;
let r = &x;      // Immutable reference
let mr = &mut x; // ERROR: x is not mutable

let mut y = 10;
let mr = &mut y; // Mutable reference
*mr += 5;        // Dereference and modify
```

### Dereference (`*`)
```rust
let x = 5;
let r = &x;
let val = *r; // Dereference to get the value

let mut y = Box::new(10);
*y += 5; // Dereference Box to modify inner value
```

**Smart Pointer Dereferencing:**
```rust
use std::ops::Deref;

struct MyBox<T>(T);

impl<T> Deref for MyBox<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

let x = MyBox(String::from("Rust"));
let len = x.len(); // Auto-deref: MyBox<String> -> String -> str
```

---

## 6. Range Operators

```rust
// Inclusive range (start..=end)
for i in 1..=5 {
    print!("{} ", i); // 1 2 3 4 5
}

// Exclusive range (start..end)
for i in 1..5 {
    print!("{} ", i); // 1 2 3 4
}

// Unbounded ranges
let arr = [1, 2, 3, 4, 5];
let slice1 = &arr[..3];    // [1, 2, 3]
let slice2 = &arr[2..];    // [3, 4, 5]
let slice3 = &arr[..];     // [1, 2, 3, 4, 5]
let slice4 = &arr[1..=3];  // [2, 3, 4]
```

**Production Pattern: Range-Based Iteration**
```rust
// Efficient iteration over indices
fn process_batch(data: &[u32], batch_size: usize) {
    for start in (0..data.len()).step_by(batch_size) {
        let end = (start + batch_size).min(data.len());
        let batch = &data[start..end];
        // Process batch
    }
}
```

---

## 7. Pattern Matching Symbols

### Match Arms (`=>`)
```rust
let number = 7;
match number {
    1 => println!("One"),
    2 | 3 | 5 | 7 | 11 => println!("Prime"),
    13..=19 => println!("Teen"),
    _ => println!("Other"),
}
```

### Pattern Binding (`@`)
```rust
enum Message {
    Hello { id: i32 },
}

let msg = Message::Hello { id: 5 };

match msg {
    Message::Hello { id: id_var @ 3..=7 } => {
        println!("Found an id in range: {}", id_var);
    }
    Message::Hello { id: 10..=12 } => {
        println!("Found an id in another range");
    }
    Message::Hello { id } => {
        println!("Found some other id: {}", id);
    }
}
```

### Ignore Patterns (`_`)
```rust
let (x, _, z) = (1, 2, 3); // Ignore second element

let numbers = (1, 2, 3, 4, 5);
match numbers {
    (first, .., last) => {
        println!("First: {}, Last: {}", first, last);
    }
}
```

---

## 8. Path and Type Operators

### Path Separator (`::`)
```rust
use std::collections::HashMap;
use std::io::{self, Write};

let map = HashMap::new();
std::mem::drop(map);
```

### Type Annotation (`:`)
```rust
let x: i32 = 5;
let v: Vec<String> = Vec::new();

fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

### Turbofish (`::<>`)
```rust
let numbers: Vec<i32> = vec![1, 2, 3];
let doubled = numbers.iter().map(|x| x * 2).collect::<Vec<i32>>();

// Generic function disambiguation
fn parse_value() -> i32 {
    "42".parse::<i32>().unwrap()
}
```

---

## 9. Trait Bounds and Lifetimes

### Trait Bounds (`+`)
```rust
use std::fmt::Debug;

fn print_debug<T: Debug + Clone>(item: T) {
    println!("{:?}", item);
}

// Alternative syntax
fn print_debug_alt<T>(item: T) 
where 
    T: Debug + Clone 
{
    println!("{:?}", item);
}
```

### Lifetime Annotations (`'`)
```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

struct ImportantExcerpt<'a> {
    part: &'a str,
}
```

---

## 10. Closure Syntax

```rust
// No parameters
let print_hello = || println!("Hello");

// Single parameter (can omit parens)
let double = |x| x * 2;

// Multiple parameters
let add = |x, y| x + y;

// With type annotations
let multiply = |x: i32, y: i32| -> i32 { x * y };

// Move semantics
let name = String::from("Rust");
let greet = move || println!("Hello, {}", name);
```

**Production Pattern: Functional Pipelines**
```rust
let numbers = vec![1, 2, 3, 4, 5];

let result: i32 = numbers
    .iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * x)
    .sum();

assert_eq!(result, 20); // 2² + 4² = 4 + 16 = 20
```

---

## 11. Error Handling Operators

### Try Operator (`?`)
```rust
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let mut file = File::open("username.txt")?;
    let mut username = String::new();
    file.read_to_string(&mut username)?;
    Ok(username)
}

// Chaining
fn get_first_line() -> Option<String> {
    let content = std::fs::read_to_string("file.txt").ok()?;
    content.lines().next().map(String::from)
}
```

**Production Pattern: Custom Error Types**
```rust
use std::error::Error;
use std::fmt;

#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    Custom(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::Io(e) => write!(f, "IO error: {}", e),
            AppError::Parse(e) => write!(f, "Parse error: {}", e),
            AppError::Custom(s) => write!(f, "{}", s),
        }
    }
}

impl Error for AppError {}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::Io(err)
    }
}
```

---

## 12. Attribute and Macro Symbols

### Attributes (`#[...]` and `#![...]`)
```rust
#![allow(dead_code)] // Crate-level attribute

#[derive(Debug, Clone)]
#[cfg(target_os = "linux")]
struct Config {
    #[serde(rename = "apiKey")]
    api_key: String,
}

#[test]
fn test_something() {
    assert_eq!(2 + 2, 4);
}
```

### Macros (`!`)
```rust
println!("Hello, {}!", name);
vec![1, 2, 3];
panic!("Something went wrong!");

// Declarative macro
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
}
```

---

## 13. Unsafe and Raw Pointers

### Unsafe Block (`unsafe`)
```rust
let mut num = 5;

let r1 = &num as *const i32;  // Raw pointer
let r2 = &mut num as *mut i32;

unsafe {
    println!("r1 is: {}", *r1);
    *r2 = 10;
}
```

**Production Use Case: FFI**
```rust
extern "C" {
    fn abs(input: i32) -> i32;
}

fn safe_abs(x: i32) -> i32 {
    unsafe { abs(x) }
}
```

---

## 14. Associated Types and Traits

### Associated Type (`type`)
```rust
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}

impl Iterator for Counter {
    type Item = u32;
    
    fn next(&mut self) -> Option<Self::Item> {
        // Implementation
        None
    }
}
```

### Trait Implementation (`impl Trait for Type`)
```rust
trait Summary {
    fn summarize(&self) -> String;
}

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{} by {}", self.title, self.author)
    }
}
```

---

## 15. Advanced Patterns

### Struct Update Syntax (`..`)
```rust
struct User {
    username: String,
    email: String,
    active: bool,
}

let user1 = User {
    username: String::from("user1"),
    email: String::from("user1@example.com"),
    active: true,
};

let user2 = User {
    email: String::from("user2@example.com"),
    ..user1 // Copy remaining fields
};
```

### Field Shorthand
```rust
fn build_user(email: String, username: String) -> User {
    User {
        email,    // Instead of email: email
        username, // Instead of username: username
        active: true,
    }
}
```

---

## Production-Grade Best Practices

### 1. **Operator Overloading**
```rust
use std::ops::Add;

#[derive(Debug, Clone, Copy)]
struct Point {
    x: i32,
    y: i32,
}

impl Add for Point {
    type Output = Point;
    
    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

let p1 = Point { x: 1, y: 2 };
let p2 = Point { x: 3, y: 4 };
let p3 = p1 + p2; // Now we can use +
```

### 2. **Index Operator**
```rust
use std::ops::Index;

struct Matrix {
    data: Vec<Vec<i32>>,
}

impl Index<(usize, usize)> for Matrix {
    type Output = i32;
    
    fn index(&self, idx: (usize, usize)) -> &Self::Output {
        &self.data[idx.0][idx.1]
    }
}

let matrix = Matrix { 
    data: vec![vec![1, 2], vec![3, 4]] 
};
let val = matrix[(0, 1)]; // 2
```

### 3. **Iterator Chaining**
```rust
let result: Vec<String> = vec!["rust", "go", "python", "javascript"]
    .into_iter()
    .filter(|s| s.len() > 3)
    .map(|s| s.to_uppercase())
    .collect();

// ["RUST", "PYTHON", "JAVASCRIPT"]
```

---

## Key Takeaways

1. **Operators are traits**: Most operators can be overloaded by implementing the corresponding trait from `std::ops`
2. **Short-circuit evaluation**: `&&` and `||` don't evaluate the right side if not needed
3. **Type inference**: Rust infers types aggressively, but turbofish (`::<>`) disambiguates when needed
4. **Zero-cost abstractions**: Operator overloading and iterators compile to efficient machine code
5. **Ownership rules apply**: References (`&`, `&mut`) and dereferencing (`*`) must respect Rust's ownership system
6. **Pattern matching is powerful**: Use `@`, `|`, `..`, and ranges for expressive patterns

This covers all operators and symbols in Rust with enterprise-level understanding and real-world applications.