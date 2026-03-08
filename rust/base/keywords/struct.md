I'll craft this as a comprehensive document. Let me build it out fully.The container is temporarily rate-limited. I'll deliver the full guide directly — this is the kind of deep material that deserves your full focus.

---

# The Complete Guide to `struct` in Rust
### From Fundamentals to Expert-Level Mastery

---

## Table of Contents
1. Mental Model First — What is a Struct?
2. The Three Forms of Structs
3. Instantiation, Field Access & Mutability
4. Methods and `impl` Blocks
5. Associated Functions & Constructor Patterns
6. Struct Update Syntax
7. Ownership, Borrowing & Moves Inside Structs
8. Lifetimes in Structs
9. Derived Traits & `#[derive]`
10. Manual Trait Implementations
11. Visibility & Encapsulation
12. Generics in Structs
13. Memory Layout & Representation
14. Pattern Matching with Structs
15. Advanced Design Patterns
16. Real-World Implementations

---

## 1. Mental Model First — What is a Struct?

Before you write a single line, think like a systems programmer:

> A **struct** is a **named, heterogeneous, contiguous (by default) collection of values** stored together under one type identity.

Compare across languages you know:

```c
// C: raw struct — no methods, no ownership, no safety
typedef struct {
    int x;
    int y;
} Point;
```

```go
// Go: struct with methods via receivers — no encapsulation enforcement
type Point struct {
    X, Y int
}
func (p Point) Distance() float64 { ... }
```

```rust
// Rust: struct with ownership semantics, lifetime tracking, zero-cost abstractions
struct Point {
    x: i32,
    y: i32,
}
impl Point {
    fn distance(&self) -> f64 { ... }
}
```

**The critical insight**: In Rust, a struct is not just data. It is a **type that participates in the ownership system**. When you define a struct, you are defining:
- How memory is laid out
- Who owns the data
- How long references to it are valid
- What operations are legal

---

## 2. The Three Forms of Structs

Rust has three syntactic variants. Each serves a distinct purpose.

### 2.1 Named-Field Structs (Most Common)

```rust
struct NetworkPacket {
    source_ip:   [u8; 4],
    dest_ip:     [u8; 4],
    payload:     Vec<u8>,
    ttl:         u8,
    checksum:    u16,
}
```

Fields are accessed by name. This is the workhorse — use it whenever fields have semantic meaning distinct from their position.

### 2.2 Tuple Structs

```rust
struct Meters(f64);
struct Kilograms(f64);
struct Color(u8, u8, u8);
```

Fields are accessed by index: `.0`, `.1`, `.2`.

**Why this matters**: `Meters(5.0)` and `Kilograms(5.0)` are **different types** even though both wrap `f64`. This is the **Newtype Pattern** — it enforces type safety at zero runtime cost.

```rust
fn calculate_force(mass: Kilograms, accel: f64) -> f64 {
    mass.0 * accel
}

let m = Meters(100.0);
// calculate_force(m, 9.8); // ← COMPILE ERROR. Cannot pass Meters where Kilograms expected.
```

This is something Go and C cannot express without overhead or convention.

### 2.3 Unit Structs (Zero-Size Types)

```rust
struct Marker;
struct DatabaseConnected;
struct Uninitialized;
```

Unit structs occupy **zero bytes** at runtime. They are purely type-level constructs. Their power emerges in:
- Typestate programming (encoding state in the type system)
- Trait objects for marker traits
- Zero-cost phantom state

```rust
// Typestate pattern — state machine enforced at compile time
struct Connection<State> {
    stream: TcpStream,
    _state: std::marker::PhantomData<State>,
}

struct Disconnected;
struct Connected;
struct Authenticated;

impl Connection<Disconnected> {
    fn connect(addr: &str) -> Connection<Connected> { ... }
}
impl Connection<Connected> {
    fn authenticate(self, creds: &Credentials) -> Connection<Authenticated> { ... }
}
impl Connection<Authenticated> {
    fn send_query(&self, sql: &str) -> Result<Rows, Error> { ... }
}

// conn.send_query("SELECT *") on a Disconnected connection → COMPILE ERROR
```

---

## 3. Instantiation, Field Access & Mutability

### Basic Instantiation

```rust
struct Rectangle {
    width:  f64,
    height: f64,
    label:  String,
}

// All fields must be specified
let rect = Rectangle {
    width:  10.0,
    height: 5.0,
    label:  String::from("Viewport"),
};
```

**Critical rule**: Rust has no default zero-initialization like C. Every field must be explicitly set unless a `Default` implementation exists.

### Field Access

```rust
println!("{}", rect.width);   // 10.0
println!("{}", rect.label);   // Viewport
```

### Mutability — All or Nothing

```rust
let mut rect = Rectangle { width: 10.0, height: 5.0, label: String::from("R1") };
rect.width = 20.0; // OK — entire binding is mutable
```

**Crucial insight**: In Rust, mutability is a property of the **binding**, not individual fields. You cannot do `let rect.width = mut 10.0`. This is a deliberate design choice — it keeps ownership reasoning tractable.

If you need partial mutability, reach for `Cell<T>` or `RefCell<T>` (interior mutability — covered in advanced section).

### Field Init Shorthand

When a local variable shares a name with a field:

```rust
fn build_rect(width: f64, height: f64) -> Rectangle {
    Rectangle {
        width,          // shorthand for width: width
        height,         // shorthand for height: height
        label: String::from("default"),
    }
}
```

---

## 4. Methods and `impl` Blocks

Methods are defined in `impl` (implementation) blocks. This separates data definition from behavior — a conscious design choice that enables multiple `impl` blocks, trait implementations, and cleaner organization.

```rust
struct Circle {
    radius: f64,
    center: (f64, f64),
}

impl Circle {
    // &self — immutable borrow of the instance
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }

    fn circumference(&self) -> f64 {
        2.0 * std::f64::consts::PI * self.radius
    }

    // &mut self — mutable borrow
    fn scale(&mut self, factor: f64) {
        self.radius *= factor;
    }

    // self — consumes the value (moves it)
    fn into_point(self) -> (f64, f64) {
        self.center // self is consumed, cannot be used after this
    }
}
```

### The Three `self` Signatures — Deep Understanding

| Signature     | Meaning                                | Use When                              |
|---------------|----------------------------------------|---------------------------------------|
| `&self`       | Borrow immutably                       | Reading data, non-mutating operations |
| `&mut self`   | Borrow mutably                         | Modifying fields                      |
| `self`        | Take ownership (move)                  | Consuming the struct (builder, into)  |

```rust
let mut c = Circle { radius: 5.0, center: (0.0, 0.0) };

println!("{}", c.area());     // &self — c still usable
c.scale(2.0);                 // &mut self — c still usable, radius now 10.0
let pt = c.into_point();      // self — c MOVED, no longer accessible
// println!("{}", c.radius);  // ← COMPILE ERROR: use of moved value
```

### Multiple `impl` Blocks

Rust allows multiple `impl` blocks for the same type. This is useful for organization and required when implementing traits from other crates.

```rust
impl Circle {
    fn area(&self) -> f64 { ... }
}

impl Circle {
    fn is_unit_circle(&self) -> bool {
        self.radius == 1.0
    }
}
```

Both blocks contribute methods to the same type.

---

## 5. Associated Functions & Constructor Patterns

Associated functions don't take `self`. They are called on the type, not an instance. `String::new()`, `Vec::with_capacity()` — these are all associated functions.

### The `new` Convention

```rust
impl Circle {
    pub fn new(radius: f64, center: (f64, f64)) -> Self {
        // Self refers to the implementing type — Circle in this case
        assert!(radius > 0.0, "Radius must be positive");
        Self { radius, center }
    }

    pub fn unit() -> Self {
        Self { radius: 1.0, center: (0.0, 0.0) }
    }
}

let c = Circle::new(5.0, (1.0, 2.0));
let u = Circle::unit();
```

**Expert insight**: Using `Self` instead of the concrete type name means the code works correctly if you rename the struct or use it in trait implementations.

### The Builder Pattern

When a struct has many fields, optional fields, or complex initialization logic:

```rust
#[derive(Debug)]
struct HttpRequest {
    url:         String,
    method:      String,
    headers:     Vec<(String, String)>,
    body:        Option<Vec<u8>>,
    timeout_ms:  u64,
    follow_redirects: bool,
}

struct HttpRequestBuilder {
    url:         String,
    method:      String,
    headers:     Vec<(String, String)>,
    body:        Option<Vec<u8>>,
    timeout_ms:  u64,
    follow_redirects: bool,
}

impl HttpRequestBuilder {
    pub fn new(url: impl Into<String>) -> Self {
        Self {
            url: url.into(),
            method: String::from("GET"),
            headers: Vec::new(),
            body: None,
            timeout_ms: 30_000,
            follow_redirects: true,
        }
    }

    pub fn method(mut self, method: impl Into<String>) -> Self {
        self.method = method.into();
        self
    }

    pub fn header(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.headers.push((key.into(), value.into()));
        self
    }

    pub fn body(mut self, data: Vec<u8>) -> Self {
        self.body = Some(data);
        self
    }

    pub fn timeout(mut self, ms: u64) -> Self {
        self.timeout_ms = ms;
        self
    }

    pub fn build(self) -> Result<HttpRequest, String> {
        if self.url.is_empty() {
            return Err(String::from("URL cannot be empty"));
        }
        Ok(HttpRequest {
            url:              self.url,
            method:           self.method,
            headers:          self.headers,
            body:             self.body,
            timeout_ms:       self.timeout_ms,
            follow_redirects: self.follow_redirects,
        })
    }
}

// Usage — reads like a sentence
let request = HttpRequestBuilder::new("https://api.example.com/data")
    .method("POST")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token123")
    .body(b"{\"key\": \"value\"}".to_vec())
    .timeout(5_000)
    .build()
    .expect("Valid request");
```

**Why this works**: Each builder method takes `self` by value and returns `Self` — this is method chaining via ownership transfer. The compiler eliminates the intermediate allocations.

---

## 6. Struct Update Syntax

Create a new struct instance using another as a template:

```rust
#[derive(Debug)]
struct Config {
    debug:       bool,
    log_level:   u8,
    max_threads: usize,
    timeout_ms:  u64,
}

let default_config = Config {
    debug:       false,
    log_level:   2,
    max_threads: 4,
    timeout_ms:  5000,
};

// Override only what changes
let dev_config = Config {
    debug:     true,
    log_level: 5,
    ..default_config  // remaining fields from default_config
};
```

**Ownership warning**: The `..other` syntax **moves** fields that don't implement `Copy`. If `default_config` had a `String` field and you used `..default_config`, that `String` would be moved and `default_config` would become partially moved (unusable unless all non-Copy fields were explicitly overridden).

---

## 7. Ownership, Borrowing & Moves Inside Structs

This is where Rust structs diverge fundamentally from every other language.

### Structs Own Their Fields

```rust
struct Employee {
    name:   String,    // owned — Employee is responsible for this memory
    salary: f64,
}

let emp = Employee {
    name:   String::from("Alice"),
    salary: 95_000.0,
};
// When emp is dropped, emp.name's heap memory is freed automatically
```

### Moving Out of a Struct

```rust
let emp = Employee { name: String::from("Alice"), salary: 95_000.0 };
let name = emp.name;   // moves emp.name OUT of emp
// emp.name is now invalid. emp.salary is still valid.
// println!("{}", emp.name);   // ← COMPILE ERROR
println!("{}", emp.salary);    // OK — salary is Copy (f64)
```

### Partial Moves

Rust tracks **field-level** moves. This is more granular than most type systems:

```rust
struct Pair {
    a: String,
    b: String,
}

let p = Pair { a: String::from("hello"), b: String::from("world") };
let a = p.a;  // partial move of p.a
// p.b is still valid, p.a is not
println!("{}", p.b); // OK
// println!("{}", p.a); // ERROR
// println!("{:?}", p);  // ERROR — p is partially moved
```

### Storing References: You Need Lifetimes

If a struct field is a reference, the compiler demands a lifetime annotation:

```rust
// This does NOT compile
struct Parser {
    input: &str,  // error: missing lifetime specifier
}

// This compiles — 'a ties the struct's validity to the referenced data
struct Parser<'a> {
    input:    &'a str,
    position: usize,
}
```

---

## 8. Lifetimes in Structs

Lifetimes in structs express a contract: **"this struct cannot outlive the data it references."**

```rust
struct Tokenizer<'src> {
    source:   &'src str,
    position: usize,
    line:     usize,
}

impl<'src> Tokenizer<'src> {
    pub fn new(source: &'src str) -> Self {
        Self { source, position: 0, line: 1 }
    }

    pub fn next_token(&mut self) -> Option<&'src str> {
        // Returns a slice of the original source — same lifetime
        let start = self.position;
        while self.position < self.source.len() {
            if self.source.as_bytes()[self.position] == b' ' {
                break;
            }
            self.position += 1;
        }
        if start == self.position {
            None
        } else {
            let token = &self.source[start..self.position];
            self.position += 1; // skip space
            Some(token)
        }
    }
}

fn main() {
    let source = String::from("hello world foo bar");
    let mut tokenizer = Tokenizer::new(&source);
    while let Some(tok) = tokenizer.next_token() {
        println!("{}", tok);
    }
    // tokenizer cannot outlive source — enforced at compile time
}
```

### Multiple Lifetimes

```rust
struct Diff<'a, 'b> {
    original: &'a str,
    modified: &'b str,
}

// 'a and 'b can be different lifetimes — original and modified
// don't need to live the same amount of time
```

### The `'static` Lifetime

```rust
struct AppConfig {
    db_url: &'static str,  // must point to data that lives forever
}

// String literals are 'static
let config = AppConfig { db_url: "postgres://localhost/mydb" };
```

---

## 9. Derived Traits & `#[derive]`

The `#[derive]` attribute instructs the compiler to auto-generate trait implementations:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Default)]
struct Point {
    x: i32,
    y: i32,
}
```

### What Each Derives

| Trait        | What it gives you                                      | Requirement                    |
|--------------|--------------------------------------------------------|--------------------------------|
| `Debug`      | `{:?}` formatting                                      | All fields implement `Debug`   |
| `Clone`      | `.clone()` — deep copy                                 | All fields implement `Clone`   |
| `Copy`       | Implicit bitwise copy instead of move                  | All fields implement `Copy`    |
| `PartialEq`  | `==` and `!=` operators                                | All fields implement `PartialEq`|
| `Eq`         | Total equality (reflexive) — marker                    | `PartialEq` required           |
| `Hash`       | Can be used in `HashMap`/`HashSet`                     | All fields implement `Hash`    |
| `PartialOrd` | `<`, `>`, `<=`, `>=` operators                         | All fields implement `PartialOrd`|
| `Ord`        | Total ordering — sort, min, max                        | `Eq` + `PartialOrd`            |
| `Default`    | `Point::default()` → `Point { x: 0, y: 0 }`           | All fields implement `Default` |

### Copy vs Clone — The Key Distinction

```rust
#[derive(Clone, Copy, Debug)]
struct Vec2 {
    x: f32,
    y: f32,
}

let a = Vec2 { x: 1.0, y: 2.0 };
let b = a;       // Copy — a is still valid because f32 is Copy
println!("{:?}", a); // Works!

// If Vec2 had a String field, Copy would be impossible (String is not Copy)
```

**Expert rule**: Implement `Copy` when a type is small, stack-only, and cheap to duplicate. Avoid `Copy` for types wrapping heap allocations.

---

## 10. Manual Trait Implementations

Deriving is convenient but manual implementations give you control.

### `Display` — Human-Readable Output

```rust
use std::fmt;

struct Matrix {
    data: [[f64; 3]; 3],
}

impl fmt::Display for Matrix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for row in &self.data {
            write!(f, "[ ")?;
            for val in row {
                write!(f, "{:8.3} ", val)?;
            }
            writeln!(f, "]")?;
        }
        Ok(())
    }
}
```

### `Drop` — Custom Cleanup

```rust
struct FileHandle {
    path: String,
    fd:   i32,
}

impl Drop for FileHandle {
    fn drop(&mut self) {
        println!("Closing file: {} (fd: {})", self.path, self.fd);
        // In real code: unsafe { libc::close(self.fd); }
    }
}

// Drop is called automatically when FileHandle goes out of scope
// You cannot call .drop() manually — use std::mem::drop(handle) instead
```

### `From` / `Into` — Type Conversions

```rust
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

// From gives you Into for free
let boiling = Celsius(100.0);
let f: Fahrenheit = boiling.into();  // uses From<Celsius> impl
println!("{}", f.0); // 212.0
```

### `Index` / `IndexMut` — `[]` Operator

```rust
use std::ops::Index;

struct Grid {
    data: Vec<Vec<i32>>,
    cols: usize,
}

impl Index<(usize, usize)> for Grid {
    type Output = i32;

    fn index(&self, (row, col): (usize, usize)) -> &i32 {
        &self.data[row][col]
    }
}

let grid = Grid { data: vec![vec![1,2,3], vec![4,5,6]], cols: 3 };
println!("{}", grid[(1, 2)]);  // 6
```

---

## 11. Visibility & Encapsulation

Rust's module system enforces information hiding at a granular level.

```rust
// src/geometry.rs
pub struct Circle {
    pub radius:  f64,    // public — accessible everywhere
    center:      (f64, f64), // private — only accessible within this module
}

impl Circle {
    pub fn new(radius: f64, x: f64, y: f64) -> Self {
        Self { radius, center: (x, y) }
    }

    pub fn center(&self) -> (f64, f64) {
        self.center  // controlled read access
    }

    // No setter for center — by design
}

// src/main.rs
use crate::geometry::Circle;

let c = Circle::new(5.0, 0.0, 0.0);
println!("{}", c.radius);   // OK — pub field
// println!("{:?}", c.center); // ERROR — private field
println!("{:?}", c.center()); // OK — through pub method
```

### Visibility Levels

```rust
pub struct Config {
    pub name:           String,   // visible everywhere
    pub(crate) version: u32,      // visible within this crate only
    pub(super) debug:   bool,     // visible in parent module
    internal_id:        u64,      // private to this module
}
```

---

## 12. Generics in Structs

Generics allow you to write struct definitions that work across multiple types without code duplication and without runtime overhead (monomorphization).

```rust
struct Stack<T> {
    elements: Vec<T>,
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Self { elements: Vec::new() }
    }

    pub fn push(&mut self, item: T) {
        self.elements.push(item);
    }

    pub fn pop(&mut self) -> Option<T> {
        self.elements.pop()
    }

    pub fn peek(&self) -> Option<&T> {
        self.elements.last()
    }

    pub fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    pub fn len(&self) -> usize {
        self.elements.len()
    }
}

// Works for any T
let mut int_stack: Stack<i32> = Stack::new();
int_stack.push(1);
int_stack.push(2);

let mut str_stack: Stack<&str> = Stack::new();
str_stack.push("hello");
```

### Trait Bounds on Generics

```rust
use std::fmt::Display;

struct MinMax<T: PartialOrd + Display + Clone> {
    min: T,
    max: T,
}

impl<T: PartialOrd + Display + Clone> MinMax<T> {
    pub fn new(a: T, b: T) -> Self {
        if a <= b {
            Self { min: a, max: b }
        } else {
            Self { min: b, max: a }
        }
    }

    pub fn range_display(&self) {
        println!("[{}, {}]", self.min, self.max);
    }
}
```

### Where Clauses (Cleaner Syntax for Complex Bounds)

```rust
struct Processor<I, O>
where
    I: Iterator,
    I::Item: Into<O>,
    O: Default + Clone,
{
    source:  I,
    output:  Vec<O>,
}
```

### PhantomData — Zero-Size Type Parameters

When a type parameter is used logically but not stored directly:

```rust
use std::marker::PhantomData;

struct TypedId<T> {
    value: u64,
    _marker: PhantomData<T>,  // zero size, tells the type system T is relevant
}

struct User;
struct Product;

type UserId = TypedId<User>;
type ProductId = TypedId<Product>;

fn find_user(id: UserId) -> Option<User> { ... }

let user_id = TypedId::<User> { value: 42, _marker: PhantomData };
let product_id = TypedId::<Product> { value: 42, _marker: PhantomData };

// find_user(product_id);  // COMPILE ERROR — type mismatch!
```

---

## 13. Memory Layout & Representation

This is where Rust knowledge separates experts from everyone else.

### Default Layout: Compiler-Optimized

By default, Rust **does not guarantee field order**. The compiler reorders fields to minimize padding:

```rust
struct Naive {
    a: u8,   // 1 byte
    b: u64,  // 8 bytes — compiler may insert 7 bytes padding after a!
    c: u8,   // 1 byte
}
// sizeof(Naive) might be 24 bytes without optimization

struct Optimized {
    b: u64,  // 8 bytes
    a: u8,   // 1 byte
    c: u8,   // 1 byte
    // 6 bytes padding at end for alignment
}
// sizeof(Optimized) = 16 bytes
```

Check sizes at compile time:

```rust
use std::mem;
println!("{}", mem::size_of::<Optimized>()); // 16
```

### `#[repr(C)]` — C-Compatible Layout

For FFI, networking protocols, or guaranteed field ordering:

```rust
#[repr(C)]
struct IpHeader {
    version_ihl:  u8,
    dscp_ecn:     u8,
    total_length: u16,
    id:           u16,
    flags_offset: u16,
    ttl:          u8,
    protocol:     u8,
    checksum:     u16,
    src_addr:     [u8; 4],
    dst_addr:     [u8; 4],
}
// Fields are guaranteed to be in declaration order, C-compatible
```

### `#[repr(packed)]` — No Padding

```rust
#[repr(C, packed)]
struct PackedHeader {
    magic:   u32,
    version: u8,
    length:  u16,
}
// No padding — unsafe to take references to fields!
// Accessing unaligned fields requires unsafe
```

### `#[repr(align(N))]` — Force Alignment

```rust
#[repr(align(64))]  // Align to cache line — avoids false sharing in concurrent code
struct CacheAligned {
    counter: std::sync::atomic::AtomicU64,
}
```

---

## 14. Pattern Matching with Structs

Structs integrate fully with Rust's pattern matching system.

### Destructuring in `let`

```rust
struct Point3D { x: f64, y: f64, z: f64 }

let p = Point3D { x: 1.0, y: 2.0, z: 3.0 };

let Point3D { x, y, z } = p;
println!("{} {} {}", x, y, z);

// Rename during destructuring
let Point3D { x: px, y: py, z: pz } = Point3D { x: 4.0, y: 5.0, z: 6.0 };

// Ignore some fields
let Point3D { x, .. } = Point3D { x: 7.0, y: 8.0, z: 9.0 };
```

### In `match` Expressions

```rust
enum Shape {
    Circle  { radius: f64 },
    Rect    { width: f64, height: f64 },
    Triangle { base: f64, height: f64 },
}

fn area(shape: &Shape) -> f64 {
    match shape {
        Shape::Circle { radius }            => std::f64::consts::PI * radius * radius,
        Shape::Rect { width, height }       => width * height,
        Shape::Triangle { base, height }    => 0.5 * base * height,
    }
}
```

### Guards in Match

```rust
match shape {
    Shape::Circle { radius } if *radius > 100.0 => println!("Very large circle"),
    Shape::Circle { radius }                     => println!("Circle r={}", radius),
    _                                            => println!("Other shape"),
}
```

### In Function Parameters

```rust
fn print_point(&Point { x, y }: &Point) {
    println!("({}, {})", x, y);
}

// Or in closures:
let points = vec![Point { x: 1.0, y: 2.0 }, Point { x: 3.0, y: 4.0 }];
points.iter().for_each(|&Point { x, y }| println!("{} {}", x, y));
```

---

## 15. Advanced Design Patterns

### 15.1 Newtype Pattern (Type Safety Without Cost)

```rust
struct EmailAddress(String);
struct PhoneNumber(String);

impl EmailAddress {
    pub fn new(s: String) -> Result<Self, String> {
        if s.contains('@') {
            Ok(Self(s))
        } else {
            Err(format!("{} is not a valid email", s))
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// Now functions can accept EmailAddress instead of String
// Can't accidentally pass a PhoneNumber where an EmailAddress is expected
fn send_email(to: &EmailAddress, subject: &str) { ... }
```

### 15.2 State Machine via Typestates

Encode valid state transitions at the type level — invalid transitions become compile errors:

```rust
struct Document<State> {
    content: String,
    author:  String,
    _state:  std::marker::PhantomData<State>,
}

struct Draft;
struct UnderReview;
struct Published;

impl Document<Draft> {
    pub fn new(author: String) -> Self {
        Document { content: String::new(), author, _state: PhantomData }
    }

    pub fn edit(&mut self, new_content: String) {
        self.content = new_content;
    }

    pub fn submit_for_review(self) -> Document<UnderReview> {
        Document { content: self.content, author: self.author, _state: PhantomData }
    }
}

impl Document<UnderReview> {
    pub fn approve(self) -> Document<Published> {
        Document { content: self.content, author: self.author, _state: PhantomData }
    }

    pub fn reject(self) -> Document<Draft> {
        Document { content: self.content, author: self.author, _state: PhantomData }
    }
}

impl Document<Published> {
    pub fn content(&self) -> &str {
        &self.content
    }
    // No edit() method — published docs are immutable
}
```

### 15.3 Interior Mutability

When you need mutation through a shared reference:

```rust
use std::cell::RefCell;
use std::rc::Rc;

struct SharedCache {
    data: RefCell<std::collections::HashMap<String, String>>,
}

impl SharedCache {
    pub fn new() -> Self {
        Self { data: RefCell::new(std::collections::HashMap::new()) }
    }

    // Takes &self (not &mut self) but can mutate internally
    pub fn insert(&self, key: String, value: String) {
        self.data.borrow_mut().insert(key, value);
    }

    pub fn get(&self, key: &str) -> Option<String> {
        self.data.borrow().get(key).cloned()
    }
}
```

For multi-threaded: use `Mutex<T>` instead of `RefCell<T>`.

### 15.4 RAII — Resource Acquisition Is Initialization

Structs are perfect RAII handles:

```rust
struct DatabaseTransaction<'conn> {
    conn:      &'conn mut DbConnection,
    committed: bool,
}

impl<'conn> DatabaseTransaction<'conn> {
    pub fn begin(conn: &'conn mut DbConnection) -> Result<Self, DbError> {
        conn.execute("BEGIN")?;
        Ok(Self { conn, committed: false })
    }

    pub fn commit(mut self) -> Result<(), DbError> {
        self.conn.execute("COMMIT")?;
        self.committed = true;
        Ok(())
    }
}

impl<'conn> Drop for DatabaseTransaction<'conn> {
    fn drop(&mut self) {
        if !self.committed {
            // Automatically rollback if not committed — even on panic
            let _ = self.conn.execute("ROLLBACK");
        }
    }
}
```

---

## 16. Real-World Implementations

### 16.1 A Lock-Free Ring Buffer

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::cell::UnsafeCell;

pub struct RingBuffer<T, const N: usize> {
    data:  [UnsafeCell<Option<T>>; N],
    head:  AtomicUsize,
    tail:  AtomicUsize,
}

unsafe impl<T: Send, const N: usize> Send for RingBuffer<T, N> {}
unsafe impl<T: Send, const N: usize> Sync for RingBuffer<T, N> {}

impl<T, const N: usize> RingBuffer<T, N> {
    pub fn new() -> Self {
        // Safe: UnsafeCell<Option<T>> with None is valid
        Self {
            data: std::array::from_fn(|_| UnsafeCell::new(None)),
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }

    pub fn push(&self, item: T) -> bool {
        let tail = self.tail.load(Ordering::Relaxed);
        let next_tail = (tail + 1) % N;
        if next_tail == self.head.load(Ordering::Acquire) {
            return false; // buffer full
        }
        unsafe { *self.data[tail].get() = Some(item); }
        self.tail.store(next_tail, Ordering::Release);
        true
    }

    pub fn pop(&self) -> Option<T> {
        let head = self.head.load(Ordering::Relaxed);
        if head == self.tail.load(Ordering::Acquire) {
            return None; // buffer empty
        }
        let item = unsafe { (*self.data[head].get()).take() };
        self.head.store((head + 1) % N, Ordering::Release);
        item
    }
}
```

### 16.2 Interval Tree for Range Queries

```rust
#[derive(Debug, Clone)]
struct Interval {
    low:  i64,
    high: i64,
}

#[derive(Debug)]
struct IntervalNode {
    interval: Interval,
    max:      i64,   // maximum endpoint in subtree
    left:     Option<Box<IntervalNode>>,
    right:    Option<Box<IntervalNode>>,
}

impl IntervalNode {
    fn new(interval: Interval) -> Self {
        let max = interval.high;
        Self { interval, max, left: None, right: None }
    }

    fn insert(&mut self, interval: Interval) {
        self.max = self.max.max(interval.high);
        if interval.low < self.interval.low {
            match &mut self.left {
                Some(node) => node.insert(interval),
                None       => self.left = Some(Box::new(IntervalNode::new(interval))),
            }
        } else {
            match &mut self.right {
                Some(node) => node.insert(interval),
                None       => self.right = Some(Box::new(IntervalNode::new(interval))),
            }
        }
    }

    fn overlaps(a: &Interval, b: &Interval) -> bool {
        a.low <= b.high && b.low <= a.high
    }

    fn search(&self, query: &Interval) -> Option<&Interval> {
        if Self::overlaps(&self.interval, query) {
            return Some(&self.interval);
        }
        if let Some(left) = &self.left {
            if left.max >= query.low {
                if let Some(result) = left.search(query) {
                    return Some(result);
                }
            }
        }
        if let Some(right) = &self.right {
            return right.search(query);
        }
        None
    }
}
```

### 16.3 Type-Safe HTTP Router

```rust
use std::collections::HashMap;

type Handler = Box<dyn Fn(&Request) -> Response + Send + Sync>;

struct Router {
    routes: HashMap<(Method, String), Handler>,
}

#[derive(Hash, Eq, PartialEq, Clone)]
enum Method { Get, Post, Put, Delete }

struct Request  { method: Method, path: String, body: Option<Vec<u8>> }
struct Response { status: u16,    body: Vec<u8> }

impl Router {
    pub fn new() -> Self {
        Self { routes: HashMap::new() }
    }

    pub fn route<F>(mut self, method: Method, path: &str, handler: F) -> Self
    where
        F: Fn(&Request) -> Response + Send + Sync + 'static,
    {
        self.routes.insert((method, path.to_string()), Box::new(handler));
        self
    }

    pub fn dispatch(&self, req: &Request) -> Response {
        self.routes
            .get(&(req.method.clone(), req.path.clone()))
            .map(|h| h(req))
            .unwrap_or_else(|| Response { status: 404, body: b"Not Found".to_vec() })
    }
}

// Usage
let router = Router::new()
    .route(Method::Get,  "/health", |_| Response { status: 200, body: b"OK".to_vec() })
    .route(Method::Post, "/users",  |req| {
        // process req.body
        Response { status: 201, body: b"Created".to_vec() }
    });
```

---

## Summary: The Expert's Mental Checklist

When you design a struct in Rust, ask these questions in order:

1. **What data does it own vs borrow?** → Determines if you need lifetime parameters
2. **Should it be `Copy`?** → Only for small, stack-only, cheap-to-duplicate types
3. **What invariants must always hold?** → Hide fields, validate in constructors
4. **What is its memory layout story?** → `#[repr(C)]` for FFI, default for performance
5. **Does it encode state?** → Consider typestate pattern with `PhantomData`
6. **Does it hold resources?** → Implement `Drop` for RAII
7. **What conversions make sense?** → Implement `From`/`Into`, `AsRef`, `Borrow`
8. **What traits should it derive?** → `Debug` always, `Clone`/`Copy` when appropriate, `PartialEq`/`Eq` for testing

---

> **The monk's insight**: A struct in Rust is not a passive container. It is an active participant in the language's safety guarantees. Every design decision you make at the struct level — ownership, visibility, traits, lifetimes — ripples through every piece of code that touches it. This is why designing structs well is the first discipline of a Rust master.