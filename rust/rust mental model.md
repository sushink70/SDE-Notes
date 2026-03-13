# Rust From the Ground Up — Types, Keywords, Crates, and Implementations

> *"Confusion is not a sign of weakness. It is a sign that your mental model needs upgrading.
> Every expert was once lost in the same fog. The path out is systematic."*

---

## How to Use This Guide

Read every section in order. Do not skip. Each section builds on the one before it.
For every code example: read it, TYPE it by hand (do not copy-paste), and run it.
The physical act of typing forces your brain to process every character.

---

## Table of Contents

1. [The Mental Model — How Rust Thinks](#1-mental-model)
2. [Every Keyword Explained](#2-keywords)
3. [Types — Reading and Writing Them](#3-types)
4. [Ownership — The One Rule That Explains Everything](#4-ownership)
5. [Functions — Every Form](#5-functions)
6. [Structs — Building Your Own Types](#6-structs)
7. [Enums — Types That Are One of Several Things](#7-enums)
8. [Traits — Defining Shared Behavior](#8-traits)
9. [impl — Attaching Behavior to Types](#9-impl)
10. [Generics — Writing Code for Any Type](#10-generics)
11. [Error Handling — Result and Option](#11-errors)
12. [The Borrow Checker — Why Rust Fights You](#12-borrow-checker)
13. [Lifetimes — Annotating How Long References Live](#13-lifetimes)
14. [Closures — Functions That Capture Their Environment](#14-closures)
15. [Iterators — Processing Sequences](#15-iterators)
16. [Crates and Modules — Organizing Code](#16-crates)
17. [Common Patterns You Will See Everywhere](#17-patterns)
18. [Reading Compiler Errors — A Systematic Method](#18-errors)
19. [Building a Real Program Step by Step](#19-real-program)

---

## 1. The Mental Model — How Rust Thinks {#1-mental-model}

Before any syntax, you need the correct mental model. Most confusion in Rust comes
from applying a Python or C++ mental model to a language built on completely different rules.

### Rust's Core Guarantee

Rust makes one promise: **if your code compiles, it will not have memory bugs, data races,
or undefined behavior.** The price you pay for this promise is that you must tell the
compiler more information than other languages require.

### The Three Questions Rust Always Asks

For every value in your program, Rust tracks three things:

```
1. WHO OWNS this value?        (exactly one owner at a time)
2. HOW LONG does it live?      (lifetime — when does it get dropped/freed?)
3. WHAT CAN BE DONE WITH IT?   (type — what operations are valid?)
```

Every confusing error message is the compiler asking one of these three questions
and finding that your code doesn't answer it clearly enough.

### Values, Variables, and Bindings

In Python: variables are labels attached to objects. Multiple labels can point to the same object.
In Rust: variables are **bindings** — they own a value. Only one binding owns a value at a time.

```rust
fn main() {
    // 'x' OWNS the value 5
    let x = 5;

    // 'y' OWNS its OWN copy of 5 (integers are Copy)
    let y = x;

    println!("{} {}", x, y); // Both valid — integers are copied

    // 's1' OWNS a String (heap-allocated)
    let s1 = String::from("hello");

    // MOVE: s2 takes ownership. s1 is now invalid.
    let s2 = s1;

    // println!("{}", s1); // ERROR: s1's value was moved
    println!("{}", s2);     // OK: s2 owns the string now
}
```

This is the foundation. Everything else in Rust follows from this.

---

## 2. Every Keyword Explained {#2-keywords}

Rust has 38 keywords. Here is every one, explained clearly with examples.

### Declaration Keywords

```rust
// let — bind a value to a name (immutable by default)
let x = 5;
let name: &str = "alice";  // with explicit type annotation

// let mut — bind a value that can be changed
let mut count = 0;
count += 1;

// const — compile-time constant, must have type, lives for entire program
const MAX_SIZE: usize = 1024;
const PI: f64 = 3.14159265358979;

// static — global variable, lives for entire program
// Unlike const, has a fixed memory address
static GREETING: &str = "hello";
static mut COUNTER: i32 = 0; // mutable globals require unsafe

// fn — define a function
fn add(a: i32, b: i32) -> i32 {
    a + b  // last expression without semicolon = return value
}

// struct — define a new type with named fields
struct Point {
    x: f64,
    y: f64,
}

// enum — define a type that can be one of several variants
enum Direction {
    North,
    South,
    East,
    West,
}

// trait — define a set of methods a type can implement
trait Greet {
    fn hello(&self) -> String;
}

// impl — implement methods on a type, or implement a trait for a type
impl Point {
    fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
}

// type — create a type alias (new name for existing type)
type Meters = f64;
type Result<T> = std::result::Result<T, String>;

// use — bring a name into scope
use std::collections::HashMap;
use std::fmt::{self, Display};

// mod — define a module (namespace for organizing code)
mod math {
    pub fn square(x: i32) -> i32 {
        x * x
    }
}
```

### Control Flow Keywords

```rust
fn control_flow_examples() {
    let number = 7;

    // if / else if / else
    if number < 5 {
        println!("small");
    } else if number < 10 {
        println!("medium");
    } else {
        println!("large");
    }

    // if is an EXPRESSION — it returns a value
    let description = if number % 2 == 0 { "even" } else { "odd" };

    // loop — infinite loop (exits with break)
    let mut i = 0;
    let result = loop {
        i += 1;
        if i == 10 {
            break i * 2; // break can return a value from loop
        }
    };

    // while — loop while condition is true
    let mut n = 0;
    while n < 5 {
        n += 1;
    }

    // for — iterate over a range or collection
    for x in 0..5 {         // 0, 1, 2, 3, 4
        print!("{} ", x);
    }
    for x in 0..=5 {        // 0, 1, 2, 3, 4, 5
        print!("{} ", x);
    }
    for item in vec![1, 2, 3] {
        print!("{} ", item);
    }

    // match — pattern matching (like switch but much more powerful)
    let direction = Direction::North;
    match direction {
        Direction::North => println!("going north"),
        Direction::South | Direction::East => println!("south or east"),
        _ => println!("west"),  // _ = wildcard, matches anything
    }

    // return — early return from function
    fn find_positive(nums: &[i32]) -> Option<i32> {
        for &n in nums {
            if n > 0 {
                return Some(n); // exit immediately
            }
        }
        None // implicit return
    }

    // continue — skip to next iteration
    for i in 0..10 {
        if i % 2 == 0 { continue; }
        println!("{}", i); // only odd numbers
    }

    // break — exit loop
    for i in 0..100 {
        if i == 5 { break; }
        println!("{}", i);
    }
}
```

### Type and Memory Keywords

```rust
// Self — refers to the type currently being implemented
struct Counter {
    value: i32,
}

impl Counter {
    fn new() -> Self {        // Self = Counter here
        Self { value: 0 }     // Self { } constructs a Counter
    }
    fn increment(&mut self) -> &Self {
        self.value += 1;
        self
    }
}

// self — the instance the method is called on (like 'this' in other languages)
// &self    — borrow self immutably (read-only access)
// &mut self — borrow self mutably (read-write access)
// self      — take ownership of self (consumes the instance)
impl Counter {
    fn value(&self) -> i32 {          // borrows: self still usable after call
        self.value
    }
    fn reset(&mut self) {             // mutably borrows: can change fields
        self.value = 0;
    }
    fn into_value(self) -> i32 {      // consumes: Counter is dropped after call
        self.value
    }
}

// where — put trait bounds in a clause (for readability)
fn print_all<T>(items: &[T])
where
    T: std::fmt::Display,   // T must implement Display
{
    for item in items {
        println!("{}", item);
    }
}

// as — type casting
let x: i32 = 42;
let y: f64 = x as f64;    // cast i32 to f64
let z: u8 = 300_i32 as u8; // truncating cast: z = 44 (300 % 256)
let ptr = &x as *const i32; // cast reference to raw pointer

// ref — create a reference in a pattern
let value = 42;
let ref r = value;      // r is &i32, same as: let r = &value;

// in match patterns:
match Some(42) {
    Some(ref n) => println!("got reference to {}", n),
    None => {}
}

// dyn — dynamic dispatch (trait object, runtime polymorphism)
fn make_animal(name: &str) -> Box<dyn Animal> {
    Box::new(Dog { name: name.to_string() })
}

// impl (in type position) — static dispatch (opaque concrete type)
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n
}
```

### Access and Safety Keywords

```rust
// pub — make something public (visible outside its module)
pub struct PublicStruct {
    pub public_field: i32,
        private_field: i32, // no pub = private to module
}

// pub(crate) — visible anywhere in this crate, not outside
pub(crate) fn internal_helper() {}

// pub(super) — visible in parent module
pub(super) fn parent_visible() {}

// unsafe — operations that bypass Rust's safety guarantees
// Required for: raw pointers, FFI, manually implementing certain traits
unsafe fn dangerous() {
    let raw: *const i32 = &42;
    println!("{}", *raw); // dereferencing raw pointer = unsafe
}

// Call an unsafe function:
unsafe {
    dangerous();
}

// extern — interact with code from other languages (C FFI)
extern "C" {
    fn printf(format: *const i8, ...) -> i32; // declare C function
}

// move — force a closure to take ownership of captured variables
let name = String::from("alice");
let greet = move || println!("Hello, {}", name);
// name is now owned by the closure, not the enclosing scope
```

### Advanced Keywords

```rust
// async — marks a function as asynchronous (returns a Future)
async fn fetch_data(url: &str) -> String {
    // ... network call ...
    String::from("data")
}

// await — suspend async function until a Future resolves
async fn process() {
    let data = fetch_data("https://example.com").await;
    println!("{}", data);
}

// in — used in for loops and range patterns
for i in 0..10 {}
if let 1..=5 = value {}

// @ — bind a value while also pattern matching
match number {
    n @ 1..=10 => println!("got {} (between 1 and 10)", n),
    n @ 11..=20 => println!("got {} (between 11 and 20)", n),
    _ => println!("out of range"),
}

// super — refers to the parent module
mod child {
    pub fn call_parent() {
        super::parent_function(); // access parent module
    }
}

// crate — refers to the root of the current crate
use crate::utils::helper; // absolute path from crate root
```

---

## 3. Types — Reading and Writing Them {#3-types}

### How to Read a Type Signature

A type signature is a **contract** written in the type system. Learning to read them
fluently is the single most important skill in Rust.

```rust
// Read left to right: "a function that takes a reference to a slice of i32
// and returns an i32"
fn sum(numbers: &[i32]) -> i32

// "a function that takes T (any type implementing Display) and returns nothing"
fn print<T: std::fmt::Display>(val: T)

// "a vector containing elements of type String"
Vec<String>

// "a hashmap mapping String keys to i32 values"
HashMap<String, i32>

// "either Some value of type T, or None"
Option<T>

// "either Ok with value T, or Err with value E"
Result<T, E>

// "a reference to T that lives as long as lifetime 'a"
&'a T

// "a heap-allocated, owned T (no borrowing)"
Box<T>

// "an atomically reference-counted T (shared ownership, thread-safe)"
Arc<T>

// "a reference-counted T (shared ownership, single-threaded)"
Rc<T>

// "a pointer to a type implementing Trait, resolved at runtime"
Box<dyn Trait>

// "a closure that takes i32 and returns bool"
impl Fn(i32) -> bool
```

### Type Annotations — When to Write Them

Rust has type inference — it can often figure out types automatically.
But sometimes you must annotate:

```rust
fn main() {
    // Inference works: compiler sees you push i32 values
    let mut v = Vec::new();
    v.push(1_i32);   // compiler infers Vec<i32>

    // Annotation needed: compiler can't determine the type
    let v: Vec<i32> = Vec::new(); // annotate here

    // Or use the turbofish ::<> syntax
    let v = Vec::<i32>::new();
    let parsed = "42".parse::<i32>().unwrap();

    // Annotation in let:
    let x: f64 = 1.0;
    let name: &str = "alice";
    let flag: bool = true;

    // Annotation in function parameters (always required):
    fn double(x: i32) -> i32 { x * 2 }

    // Annotation in struct fields (always required):
    struct Config {
        timeout: u64,
        retries: u32,
        debug: bool,
    }
}
```

---

## 4. Ownership — The One Rule That Explains Everything {#4-ownership}

### The Three Rules

```
Rule 1: Every value has exactly ONE owner.
Rule 2: When the owner goes out of scope, the value is dropped (memory freed).
Rule 3: There can be EITHER multiple immutable references OR one mutable reference,
        but NOT both at the same time.
```

### Scope and Drop

```rust
fn main() {
    {                          // scope begins
        let s = String::from("hello");
        println!("{}", s);
    }                          // scope ends — s is DROPPED here, memory freed

    // println!("{}", s);      // ERROR: s no longer exists
}
```

### Move vs Copy

```rust
fn main() {
    // COPY types — simple stack values, duplicated automatically
    // i8, i16, i32, i64, i128, isize
    // u8, u16, u32, u64, u128, usize
    // f32, f64
    // bool
    // char
    // Tuples of Copy types: (i32, bool)
    // Arrays of Copy types: [i32; 4]

    let a = 42_i32;
    let b = a;         // a is COPIED — both a and b are valid
    println!("{} {}", a, b);

    // MOVE types — heap-allocated or complex types
    // String, Vec<T>, HashMap<K,V>, Box<T>, most user-defined structs

    let s1 = String::from("hello");
    let s2 = s1;       // s1 is MOVED to s2 — s1 is now invalid
    // println!("{}", s1); // ERROR: value moved
    println!("{}", s2); // OK

    // CLONE — explicitly make a deep copy
    let s1 = String::from("hello");
    let s2 = s1.clone(); // s2 is a COPY of s1 — both valid
    println!("{} {}", s1, s2);
}
```

### References and Borrowing

```rust
fn main() {
    let s = String::from("hello");

    // Immutable borrow — s is lent, not moved
    let len = calculate_length(&s);   // pass a reference
    println!("{} has length {}", s, len); // s still valid

    // Mutable borrow
    let mut s = String::from("hello");
    change(&mut s);
    println!("{}", s); // "hello, world"
}

fn calculate_length(s: &String) -> usize {
    s.len()
    // s goes out of scope, but because it's a reference,
    // the original String is NOT dropped here
}

fn change(s: &mut String) {
    s.push_str(", world");
}
```

### The Borrow Rules in Practice

```rust
fn main() {
    let mut v = vec![1, 2, 3];

    // RULE VIOLATION: cannot borrow as mutable while immutable borrow exists
    let first = &v[0];          // immutable borrow
    // v.push(4);               // ERROR: mutable borrow
    println!("{}", first);      // immutable borrow ends here

    v.push(4);                  // OK: no more immutable borrows
    println!("{:?}", v);
}
```

---

## 5. Functions — Every Form {#5-functions}

```rust
// Basic function
fn greet(name: &str) -> String {
    format!("Hello, {}!", name) // no semicolon = return value
}

// Multiple return values via tuple
fn min_max(nums: &[i32]) -> (i32, i32) {
    let min = *nums.iter().min().unwrap();
    let max = *nums.iter().max().unwrap();
    (min, max)
}
let (lo, hi) = min_max(&[3, 1, 4, 1, 5]);

// Unit return type (implicit — both are identical)
fn log(msg: &str) { println!("{}", msg); }
fn log2(msg: &str) -> () { println!("{}", msg); }

// Never type — function never returns (panics or loops forever)
fn crash(msg: &str) -> ! {
    panic!("{}", msg);
}

// Generic function
fn first<T>(slice: &[T]) -> Option<&T> {
    slice.first()
}

// Function with where clause
fn print_pair<A, B>(a: A, b: B)
where
    A: std::fmt::Display,
    B: std::fmt::Debug,
{
    println!("Display: {}, Debug: {:?}", a, b);
}

// Associated function (no self — like a static method)
struct Circle {
    radius: f64,
}
impl Circle {
    fn new(radius: f64) -> Self {   // associated function = constructor
        Circle { radius }
    }
}
let c = Circle::new(5.0);  // called with ::

// Method (has self — called with .)
impl Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
}
let area = c.area();  // called with .
```

---

## 6. Structs — Building Your Own Types {#6-structs}

Structs are how you create your own types that group related data.

```rust
// ── Unit struct — no fields, used as a marker
struct Marker;
let m = Marker;

// ── Tuple struct — fields accessed by position
struct Point2D(f64, f64);
let p = Point2D(1.0, 2.0);
println!("{} {}", p.0, p.1);  // access by index

// ── Named struct — most common form
#[derive(Debug, Clone)]       // auto-implement Debug and Clone
struct User {
    username: String,
    email: String,
    age: u32,
    active: bool,
}

// Constructing a struct
let user1 = User {
    username: String::from("alice"),
    email: String::from("alice@example.com"),
    age: 30,
    active: true,
};

// Struct update syntax — copy remaining fields from another instance
let user2 = User {
    email: String::from("bob@example.com"),
    username: String::from("bob"),
    ..user1   // fill remaining fields (age, active) from user1
              // NOTE: this MOVES user1 if any non-Copy fields are used
};

// Accessing fields
println!("{}", user2.username);
println!("{}", user2.age);

// ── impl block — attach methods to the struct
impl User {
    // Associated function (constructor pattern)
    pub fn new(username: &str, email: &str, age: u32) -> Self {
        Self {
            username: username.to_string(),
            email: email.to_string(),
            age,
            active: true,
        }
    }

    // Immutable method — borrows self, doesn't change it
    pub fn display_name(&self) -> &str {
        &self.username
    }

    // Mutable method — can change fields
    pub fn deactivate(&mut self) {
        self.active = false;
    }

    // Consuming method — takes ownership of self
    pub fn into_username(self) -> String {
        self.username   // returns the owned String, drops rest of User
    }
}

let mut user = User::new("alice", "alice@example.com", 30);
println!("{}", user.display_name());
user.deactivate();
let name = user.into_username(); // user is consumed here
```

### Struct Visibility

```rust
// In a library crate:
pub struct Config {
    pub host: String,      // readable and writable from outside
    pub port: u16,         // readable and writable from outside
    password: String,      // private — only accessible inside this module
}

impl Config {
    // Constructor is the only way to create Config from outside (controls password)
    pub fn new(host: &str, port: u16, password: &str) -> Self {
        Config {
            host: host.to_string(),
            port,
            password: password.to_string(),
        }
    }

    // Controlled access to private field
    pub fn verify_password(&self, attempt: &str) -> bool {
        self.password == attempt
    }
}
```

---

## 7. Enums — Types That Are One of Several Things {#7-enums}

Enums are one of Rust's most powerful features. They are far more expressive than
C-style enums — each variant can carry its own data.

```rust
// Simple enum — C-style
#[derive(Debug)]
enum Direction {
    North,
    South,
    East,
    West,
}

// Enum with data — each variant can hold different types
#[derive(Debug)]
enum Shape {
    Circle(f64),                          // one f64: radius
    Rectangle(f64, f64),                  // two f64s: width, height
    Triangle { base: f64, height: f64 }, // named fields
    Point,                                // no data
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle(r) => std::f64::consts::PI * r * r,
            Shape::Rectangle(w, h) => w * h,
            Shape::Triangle { base, height } => 0.5 * base * height,
            Shape::Point => 0.0,
        }
    }
}

let shapes = vec![
    Shape::Circle(5.0),
    Shape::Rectangle(4.0, 6.0),
    Shape::Triangle { base: 3.0, height: 8.0 },
];
for s in &shapes {
    println!("{:?} has area {:.2}", s, s.area());
}

// ── Option<T> — the standard way to represent "maybe a value"
// enum Option<T> { Some(T), None }
// NEVER use null in Rust. Use Option.

fn find_user(id: u32) -> Option<String> {
    if id == 1 {
        Some(String::from("alice"))
    } else {
        None
    }
}

// Handling Option
match find_user(1) {
    Some(name) => println!("Found: {}", name),
    None => println!("Not found"),
}

// Shortcut methods on Option
let name = find_user(1).unwrap();               // panics if None
let name = find_user(1).unwrap_or("unknown".to_string());
let name = find_user(1).unwrap_or_else(|| compute_default());
let has_user = find_user(1).is_some();
let len = find_user(1).map(|n| n.len());       // Option<usize>

// if let — handle one variant, ignore the rest
if let Some(name) = find_user(1) {
    println!("Hello, {}", name);
}

// while let — loop while pattern matches
let mut stack = vec![1, 2, 3];
while let Some(top) = stack.pop() {
    println!("{}", top);
}

// ── Result<T, E> — the standard way to represent "success or failure"
// enum Result<T, E> { Ok(T), Err(E) }

#[derive(Debug)]
enum AppError {
    NotFound(String),
    PermissionDenied,
    IoError(String),
}

fn read_config(path: &str) -> Result<String, AppError> {
    if path.is_empty() {
        return Err(AppError::NotFound("empty path".to_string()));
    }
    Ok(String::from("config content"))
}

// Handling Result
match read_config("config.toml") {
    Ok(content) => println!("Config: {}", content),
    Err(AppError::NotFound(msg)) => println!("Not found: {}", msg),
    Err(e) => println!("Error: {:?}", e),
}

// The ? operator — propagate errors automatically
fn load_app() -> Result<(), AppError> {
    let config = read_config("config.toml")?; // returns Err if read_config fails
    println!("Loaded: {}", config);
    Ok(())
}
```

---

## 8. Traits — Defining Shared Behavior {#8-traits}

A trait is an **interface** — it says "any type implementing this trait can do these things."

```rust
// Define a trait
trait Animal {
    // Required method — implementors MUST provide this
    fn name(&self) -> &str;
    fn sound(&self) -> &str;

    // Default method — implementors CAN override this
    fn describe(&self) {
        println!("I am {} and I say {}", self.name(), self.sound());
    }
}

// Implement the trait for Dog
struct Dog {
    name: String,
}

impl Animal for Dog {
    fn name(&self) -> &str {
        &self.name
    }
    fn sound(&self) -> &str {
        "woof"
    }
    // describe() uses the default implementation
}

// Implement the trait for Cat
struct Cat {
    name: String,
}

impl Animal for Cat {
    fn name(&self) -> &str {
        &self.name
    }
    fn sound(&self) -> &str {
        "meow"
    }
    // Override the default describe()
    fn describe(&self) {
        println!("{} the cat says {}", self.name(), self.sound());
    }
}

let dog = Dog { name: "Rex".to_string() };
let cat = Cat { name: "Whiskers".to_string() };
dog.describe(); // uses default
cat.describe(); // uses custom

// ── Important standard library traits ────────────────────────────────

// Display — how to print with {}
use std::fmt;
struct Point { x: f64, y: f64 }

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
println!("{}", Point { x: 1.0, y: 2.0 }); // (1, 2)

// Debug — how to print with {:?}
// Usually derived automatically:
#[derive(Debug)]
struct Color { r: u8, g: u8, b: u8 }
println!("{:?}", Color { r: 255, g: 0, b: 0 });

// Clone — explicit deep copy
#[derive(Clone)]
struct Config { host: String, port: u16 }
let c1 = Config { host: "localhost".to_string(), port: 8080 };
let c2 = c1.clone(); // explicit copy

// Copy — implicit copy (for small, stack-only types)
// Implement automatically with derive, but ONLY if all fields are Copy
#[derive(Copy, Clone)]
struct Coordinate { x: f32, y: f32 }

// PartialEq / Eq — comparison with ==
#[derive(PartialEq)]
struct Version { major: u32, minor: u32 }
let v1 = Version { major: 1, minor: 0 };
let v2 = Version { major: 1, minor: 0 };
assert!(v1 == v2);

// PartialOrd / Ord — comparison with <, >, <=, >=
#[derive(PartialOrd, PartialEq)]
struct Score(f64);

// Hash — for use as HashMap/HashSet keys
use std::hash::Hash;
#[derive(Hash, Eq, PartialEq)]
struct UserId(u64);
```

---

## 9. impl — Attaching Behavior to Types {#9-impl}

`impl` is how you attach methods and trait implementations to types.

```rust
// ── Form 1: Inherent impl — methods that belong to a type ────────────

struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    // Associated function (no self) — called as Rectangle::new(...)
    pub fn new(width: f64, height: f64) -> Self {
        Rectangle { width, height }
    }

    // Method (&self) — called as rect.area()
    pub fn area(&self) -> f64 {
        self.width * self.height
    }

    // Mutable method (&mut self)
    pub fn scale(&mut self, factor: f64) {
        self.width *= factor;
        self.height *= factor;
    }

    // Multiple impl blocks are allowed (same as one big block)
}

impl Rectangle {
    // This is the same as being in the block above
    pub fn is_square(&self) -> bool {
        (self.width - self.height).abs() < f64::EPSILON
    }
}

// ── Form 2: Trait impl — implement a trait for a type ─────────────────

use std::fmt;

impl fmt::Display for Rectangle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Rectangle({}x{})", self.width, self.height)
    }
}

// ── Form 3: Generic impl — implement for a generic type ──────────────

struct Wrapper<T> {
    value: T,
}

// Methods available for ALL Wrapper<T>
impl<T> Wrapper<T> {
    pub fn new(value: T) -> Self {
        Wrapper { value }
    }
    pub fn inner(&self) -> &T {
        &self.value
    }
    pub fn into_inner(self) -> T {
        self.value
    }
}

// Methods available ONLY when T: Display
impl<T: fmt::Display> Wrapper<T> {
    pub fn print(&self) {
        println!("Wrapper contains: {}", self.value);
    }
}

// Implement a trait for a generic type
impl<T: fmt::Display> fmt::Display for Wrapper<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Wrapper({})", self.value)
    }
}

let w = Wrapper::new(42);
w.print();            // OK: i32 implements Display
println!("{}", w);    // OK: Display is implemented

let w2 = Wrapper::new(vec![1, 2, 3]);
// w2.print();        // ERROR: Vec<i32> doesn't implement Display
```

---

## 10. Generics — Writing Code for Any Type {#10-generics}

Generics let you write code that works with many different types while remaining type-safe.

```rust
// ── Generic function ──────────────────────────────────────────────────

fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list.iter() {
        if item > largest {
            largest = item;
        }
    }
    largest
}

println!("{}", largest(&[1, 5, 3, 2, 4]));        // 5
println!("{}", largest(&[1.5, 3.2, 2.8, 0.1]));   // 3.2

// ── Generic struct ────────────────────────────────────────────────────

struct Pair<T> {
    first: T,
    second: T,
}

impl<T: PartialOrd + fmt::Display> Pair<T> {
    fn new(first: T, second: T) -> Self {
        Pair { first, second }
    }
    fn larger(&self) -> &T {
        if self.first > self.second { &self.first } else { &self.second }
    }
}

let p = Pair::new(5, 10);
println!("Larger: {}", p.larger());

// ── Multiple type parameters ──────────────────────────────────────────

struct KeyValue<K, V> {
    key: K,
    value: V,
}

impl<K: fmt::Display, V: fmt::Display> fmt::Display for KeyValue<K, V> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.key, self.value)
    }
}

let kv = KeyValue { key: "age", value: 30 };
println!("{}", kv); // age: 30

// ── Turbofish syntax — when you need to specify types explicitly ───────

let numbers = vec![1_i32, 2, 3];
let sum = numbers.iter().sum::<i32>();            // specify T for sum()
let collected: Vec<_> = (0..5).collect::<Vec<_>>(); // specify for collect()
```

---

## 11. Error Handling — Result and Option {#11-errors}

```rust
use std::fmt;
use std::num::ParseIntError;

// ── Define your error type ────────────────────────────────────────────

#[derive(Debug)]
enum MyError {
    Parse(ParseIntError),
    NegativeNumber(i32),
    TooBig(i32),
}

// Implement Display so the error can be printed
impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MyError::Parse(e) => write!(f, "parse error: {}", e),
            MyError::NegativeNumber(n) => write!(f, "{} is negative", n),
            MyError::TooBig(n) => write!(f, "{} is too big (max 100)", n),
        }
    }
}

// Implement From to enable automatic conversion with ?
impl From<ParseIntError> for MyError {
    fn from(e: ParseIntError) -> Self {
        MyError::Parse(e)
    }
}

// ── Use ? for ergonomic error propagation ─────────────────────────────

fn parse_positive(s: &str) -> Result<i32, MyError> {
    let n: i32 = s.parse()?; // ParseIntError auto-converts to MyError via From
    if n < 0 {
        return Err(MyError::NegativeNumber(n));
    }
    if n > 100 {
        return Err(MyError::TooBig(n));
    }
    Ok(n)
}

fn main() {
    let inputs = ["42", "-5", "200", "abc"];
    for input in inputs {
        match parse_positive(input) {
            Ok(n) => println!("{} -> OK: {}", input, n),
            Err(e) => println!("{} -> Error: {}", input, e),
        }
    }
}

// ── Option chaining ───────────────────────────────────────────────────

struct Config {
    database: Option<DatabaseConfig>,
}
struct DatabaseConfig {
    host: Option<String>,
}

fn get_db_host(config: &Config) -> Option<&str> {
    config
        .database
        .as_ref()?           // returns None if database is None
        .host
        .as_deref()          // Option<String> -> Option<&str>
}
```

---

## 12. The Borrow Checker — Why Rust Fights You {#12-borrow-checker}

The borrow checker enforces the ownership rules automatically. Understanding its
logic turns error messages from frustrating to informative.

```rust
// ── Problem 1: Using after move ───────────────────────────────────────

fn main() {
    let s = String::from("hello");
    let s2 = s;          // MOVE — s is invalid
    // println!("{}", s); // ERROR: borrow of moved value: `s`
    println!("{}", s2);   // OK

    // Fix: clone if you need both
    let s = String::from("hello");
    let s2 = s.clone();
    println!("{} {}", s, s2); // OK
}

// ── Problem 2: Mutable and immutable borrow at same time ──────────────

fn problem2() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];     // immutable borrow
    // v.push(4);           // ERROR: cannot borrow `v` as mutable
                            // because it is also borrowed as immutable
    println!("{}", first);  // immutable borrow used here
    v.push(4);              // OK: immutable borrow is over
}

// ── Problem 3: Dangling reference ────────────────────────────────────

// fn dangle() -> &String { // ERROR: missing lifetime specifier
//     let s = String::from("hello");
//     &s  // s is dropped here — reference would dangle
// }

// Fix: return the owned String
fn no_dangle() -> String {
    String::from("hello")
}

// ── Problem 4: The "cannot borrow as mutable more than once" ─────────

fn problem4() {
    let mut s = String::from("hello");
    let r1 = &mut s;
    // let r2 = &mut s;    // ERROR: cannot borrow `s` as mutable more than once
    r1.push_str(" world");
    // r2 is never created, so this is fine
}

// ── The NLL (Non-Lexical Lifetimes) rule — borrows end at last use ────

fn nll_example() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];         // immutable borrow starts
    println!("{}", first);     // last use of 'first' — borrow ENDS HERE
    v.push(4);                 // OK: immutable borrow already ended
}
```

---

## 13. Lifetimes — Annotating How Long References Live {#13-lifetimes}

Lifetimes are Rust's way of tracking how long references are valid.
In most code, the compiler infers them. You only write them when it can't.

```rust
// When do you need lifetime annotations?
// When a function takes multiple references AND returns a reference —
// the compiler needs to know WHICH input the output reference comes from.

// Without annotation — ERROR: compiler can't figure out the lifetime
// fn longest(x: &str, y: &str) -> &str { ... }

// With annotation — 'a says "the output lives as long as the shorter of x and y"
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xyz");
        result = longest(s1.as_str(), s2.as_str());
        println!("{}", result); // OK: both s1 and s2 are alive here
    }
    // println!("{}", result); // ERROR: s2 is dropped — result might point to s2
}

// ── Lifetime annotations on structs ──────────────────────────────────

// This struct HOLDS a reference — must annotate how long it's valid
struct Important<'a> {
    content: &'a str,  // must live at least as long as Important<'a>
}

impl<'a> Important<'a> {
    fn announce(&self) -> &str {
        self.content
    }
}

fn use_important() {
    let text = String::from("critical information");
    let i = Important { content: &text };
    println!("{}", i.announce());
    // i cannot outlive text
}

// ── Lifetime elision rules — when you don't need to write lifetimes ───

// Rule 1: each input reference gets its own lifetime
fn first_word(s: &str) -> &str {  // compiler reads as: fn first_word<'a>(s: &'a str) -> &'a str
    let bytes = s.as_bytes();
    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }
    &s[..]
}
// Rule 2: if there's exactly one input reference, it propagates to output
// Rule 3: if one input is &self or &mut self, its lifetime goes to output
```

---

## 14. Closures — Functions That Capture Their Environment {#14-closures}

```rust
fn main() {
    // Basic closure syntax
    let add = |a, b| a + b;
    println!("{}", add(3, 4));   // 7

    // With type annotations (usually not needed)
    let multiply = |a: i32, b: i32| -> i32 { a * b };

    // Multi-line closure
    let process = |x: i32| {
        let doubled = x * 2;
        let increased = doubled + 1;
        increased  // return value
    };

    // ── Capturing environment ─────────────────────────────────────────

    let threshold = 10;

    // Captures 'threshold' by reference (immutable borrow)
    let is_over = |x| x > threshold;
    println!("{}", is_over(15)); // true
    println!("{}", threshold);   // threshold still usable

    // Captures mutably
    let mut count = 0;
    let mut increment = || {
        count += 1;  // mutably borrows count
        count
    };
    println!("{}", increment()); // 1
    println!("{}", increment()); // 2
    // println!("{}", count);    // ERROR: count is mutably borrowed

    // move — transfer ownership into closure
    let name = String::from("alice");
    let greet = move || println!("Hello, {}", name);
    // name is moved — greet owns it
    greet();
    // println!("{}", name); // ERROR: name was moved into closure

    // ── Closures as function parameters ──────────────────────────────

    fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 { f(x) }
    fn apply_mut<F: FnMut() -> i32>(mut f: F) -> i32 { f() }
    fn apply_once<F: FnOnce() -> String>(f: F) -> String { f() }

    println!("{}", apply(|x| x * 2, 5));   // 10

    // ── Common closure patterns ───────────────────────────────────────

    let numbers = vec![1, 2, 3, 4, 5, 6];

    let evens: Vec<i32> = numbers.iter().copied()
        .filter(|&x| x % 2 == 0)
        .collect();

    let doubled: Vec<i32> = numbers.iter()
        .map(|&x| x * 2)
        .collect();

    let sum: i32 = numbers.iter().sum();

    // Sort with custom comparator
    let mut words = vec!["banana", "apple", "cherry"];
    words.sort_by(|a, b| a.len().cmp(&b.len())); // sort by length
}
```

---

## 15. Iterators — Processing Sequences {#15-iterators}

Iterators are lazy sequences. They don't compute until you consume them.

```rust
fn main() {
    let v = vec![1, 2, 3, 4, 5];

    // ── Creating iterators ────────────────────────────────────────────

    let iter = v.iter();          // yields &i32 — borrows v
    let iter = v.iter_mut();      // yields &mut i32 — mutably borrows v
    let iter = v.into_iter();     // yields i32 — consumes v (moves out)

    // ── Adapters (lazy — chain operations without computing) ──────────

    let result: Vec<i32> = v.iter()
        .filter(|&&x| x % 2 == 0)    // keep even numbers
        .map(|&x| x * 10)            // multiply by 10
        .take(2)                     // take only first 2
        .collect();                  // consume iterator into Vec
    println!("{:?}", result);        // [20, 40]

    // ── Consumers (force computation) ────────────────────────────────

    let sum: i32 = v.iter().sum();
    let product: i32 = v.iter().product();
    let max = v.iter().max();
    let count = v.iter().filter(|&&x| x > 2).count();
    let any_even = v.iter().any(|&x| x % 2 == 0);
    let all_positive = v.iter().all(|&x| x > 0);

    let first_even = v.iter().find(|&&x| x % 2 == 0);
    let first_even_pos = v.iter().position(|&x| x % 2 == 0);

    // fold — reduce to single value (most general)
    let sum = v.iter().fold(0, |acc, &x| acc + x);

    // ── Common iterator patterns ──────────────────────────────────────

    // Enumerate — add index
    for (i, val) in v.iter().enumerate() {
        println!("{}: {}", i, val);
    }

    // Zip — combine two iterators
    let names = vec!["Alice", "Bob", "Carol"];
    let scores = vec![95, 87, 92];
    let combined: Vec<_> = names.iter().zip(scores.iter()).collect();

    // Chain — concatenate iterators
    let a = [1, 2, 3];
    let b = [4, 5, 6];
    let together: Vec<_> = a.iter().chain(b.iter()).collect();

    // Flatten — flatten nested iterators
    let nested = vec![vec![1, 2], vec![3, 4], vec![5, 6]];
    let flat: Vec<_> = nested.into_iter().flatten().collect();

    // flat_map — map then flatten
    let words = vec!["hello world", "foo bar"];
    let chars: Vec<&str> = words.iter()
        .flat_map(|s| s.split_whitespace())
        .collect();

    // ── Implementing Iterator for your own type ───────────────────────

    struct Counter {
        count: u32,
        max: u32,
    }

    impl Counter {
        fn new(max: u32) -> Self { Counter { count: 0, max } }
    }

    impl Iterator for Counter {
        type Item = u32;

        fn next(&mut self) -> Option<Self::Item> {
            if self.count < self.max {
                self.count += 1;
                Some(self.count)
            } else {
                None
            }
        }
    }

    // Now your Counter gets ALL iterator methods for free
    let sum: u32 = Counter::new(5).sum();                    // 15
    let doubled: Vec<u32> = Counter::new(5).map(|x| x * 2).collect();
    let pairs: Vec<_> = Counter::new(3).zip(Counter::new(3)).collect();
}
```

---

## 16. Crates and Modules — Organizing Code {#16-crates}

### Understanding Crates

A **crate** is a compilation unit in Rust — either a binary (executable) or a library.
A **package** is a collection of one or more crates, managed by Cargo.

```
my_project/
├── Cargo.toml          ← package manifest (name, version, dependencies)
├── src/
│   ├── main.rs         ← binary crate root
│   ├── lib.rs          ← library crate root (optional)
│   └── utils/
│       ├── mod.rs      ← module file
│       └── helpers.rs  ← submodule
└── tests/
    └── integration.rs  ← integration tests
```

### Cargo.toml — Your Project Manifest

```toml
[package]
name = "my_app"
version = "0.1.0"
edition = "2021"

[dependencies]
# External crate from crates.io
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["full"] }
anyhow = "1.0"
clap = { version = "4", features = ["derive"] }

[dev-dependencies]
# Only used in tests
criterion = "0.5"

[profile.release]
opt-level = 3
```

### Adding and Using Dependencies

```bash
# Add a dependency (updates Cargo.toml automatically)
cargo add serde --features derive
cargo add tokio --features full
cargo add anyhow

# Build your project
cargo build

# Run your project
cargo run

# Run tests
cargo test

# Build documentation
cargo doc --open
```

### The `use` Statement — Bringing Names Into Scope

```rust
// Bring a single item into scope
use std::collections::HashMap;
use std::fmt::Display;

// Bring multiple items from the same path
use std::fmt::{self, Display, Debug};
//             ^^^^ also brings fmt itself in scope

// Bring all public items (glob import — use sparingly)
use std::collections::*;

// Rename on import
use std::collections::HashMap as Map;

// Nested paths
use std::{
    collections::HashMap,
    fmt::{Display, Debug},
    io::{self, Read, Write},
};

// Re-export — make an item part of YOUR public API
pub use std::collections::HashMap;
// Now users of YOUR crate can do: use your_crate::HashMap;
```

### Modules — Namespaces for Organization

```rust
// src/lib.rs

// Inline module definition
mod math {
    // Private by default — only accessible within this module
    fn private_helper(x: i32) -> i32 { x * 2 }

    // Public — accessible from outside
    pub fn square(x: i32) -> i32 { x * x }
    pub fn cube(x: i32) -> i32 { x * x * x }

    // Nested module
    pub mod trigonometry {
        pub fn sin(x: f64) -> f64 { x.sin() }
        pub fn cos(x: f64) -> f64 { x.cos() }
    }
}

// Using the module
use math::square;
use math::trigonometry::sin;

fn demo() {
    println!("{}", square(5));     // 25
    println!("{}", math::cube(3)); // 27 — full path
    println!("{}", sin(1.0));      // via use
}

// File-based modules — put module in a file
// mod utils;  ← looks for src/utils.rs or src/utils/mod.rs

// src/utils.rs
pub fn format_bytes(bytes: u64) -> String {
    if bytes < 1024 { return format!("{} B", bytes); }
    if bytes < 1024 * 1024 { return format!("{:.1} KB", bytes as f64 / 1024.0); }
    format!("{:.1} MB", bytes as f64 / 1024.0 / 1024.0)
}
```

### Most Important Crates — What They Do and How to Use Them

```rust
// ── serde — Serialization/Deserialization ─────────────────────────────
// Cargo.toml: serde = { version = "1.0", features = ["derive"] }
//             serde_json = "1.0"

use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
struct Person {
    name: String,
    age: u32,
    email: Option<String>,
}

let person = Person { name: "Alice".to_string(), age: 30, email: None };

// Serialize to JSON string
let json = serde_json::to_string(&person).unwrap();
println!("{}", json); // {"name":"Alice","age":30,"email":null}

// Pretty-print JSON
let pretty = serde_json::to_string_pretty(&person).unwrap();

// Deserialize from JSON string
let parsed: Person = serde_json::from_str(&json).unwrap();

// ── anyhow — Easy error handling for applications ─────────────────────
// Cargo.toml: anyhow = "1.0"

use anyhow::{Context, Result};

fn read_config(path: &str) -> Result<String> {
    // Context adds helpful message to errors
    std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read config from {}", path))
}

fn main() -> Result<()> {
    let config = read_config("config.toml")?;
    println!("{}", config);
    Ok(())
}

// ── thiserror — Define error types without boilerplate ────────────────
// Cargo.toml: thiserror = "1.0"

use thiserror::Error;

#[derive(Error, Debug)]
enum DatabaseError {
    #[error("connection failed: {0}")]
    Connection(String),

    #[error("query failed: {query}")]
    Query { query: String },

    #[error("record not found: id={id}")]
    NotFound { id: u64 },
}

// ── clap — Command-line argument parsing ──────────────────────────────
// Cargo.toml: clap = { version = "4", features = ["derive"] }

use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "myapp", about = "Does something useful")]
struct Args {
    #[arg(short, long)]
    input: String,

    #[arg(short, long, default_value_t = 8080)]
    port: u16,

    #[arg(short, long)]
    verbose: bool,
}

fn main() {
    let args = Args::parse();
    println!("Input: {}, Port: {}, Verbose: {}", args.input, args.port, args.verbose);
}

// ── tokio — Async runtime for concurrent programming ──────────────────
// Cargo.toml: tokio = { version = "1", features = ["full"] }

use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    let handle1 = tokio::spawn(async {
        sleep(Duration::from_millis(100)).await;
        println!("Task 1 done");
    });
    let handle2 = tokio::spawn(async {
        sleep(Duration::from_millis(50)).await;
        println!("Task 2 done");
    });
    handle1.await.unwrap();
    handle2.await.unwrap();
}

// ── rayon — Data parallelism ──────────────────────────────────────────
// Cargo.toml: rayon = "1.10"

use rayon::prelude::*;

fn parallel_example() {
    let numbers: Vec<i64> = (0..1_000_000).collect();

    // Change .iter() to .par_iter() — that's it. Runs on all CPU cores.
    let sum: i64 = numbers.par_iter().sum();
    println!("{}", sum);

    let doubled: Vec<i64> = numbers.par_iter().map(|&x| x * 2).collect();
}
```

---

## 17. Common Patterns You Will See Everywhere {#17-patterns}

### The Builder Pattern

```rust
#[derive(Debug)]
struct HttpRequest {
    url: String,
    method: String,
    headers: Vec<(String, String)>,
    body: Option<String>,
    timeout_ms: u64,
}

struct HttpRequestBuilder {
    url: String,
    method: String,
    headers: Vec<(String, String)>,
    body: Option<String>,
    timeout_ms: u64,
}

impl HttpRequestBuilder {
    pub fn new(url: &str) -> Self {
        HttpRequestBuilder {
            url: url.to_string(),
            method: "GET".to_string(),
            headers: Vec::new(),
            body: None,
            timeout_ms: 30_000,
        }
    }

    pub fn method(mut self, method: &str) -> Self {
        self.method = method.to_string();
        self
    }

    pub fn header(mut self, key: &str, value: &str) -> Self {
        self.headers.push((key.to_string(), value.to_string()));
        self
    }

    pub fn body(mut self, body: &str) -> Self {
        self.body = Some(body.to_string());
        self
    }

    pub fn timeout(mut self, ms: u64) -> Self {
        self.timeout_ms = ms;
        self
    }

    pub fn build(self) -> HttpRequest {
        HttpRequest {
            url: self.url,
            method: self.method,
            headers: self.headers,
            body: self.body,
            timeout_ms: self.timeout_ms,
        }
    }
}

// Usage — fluent API
let request = HttpRequestBuilder::new("https://api.example.com/users")
    .method("POST")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token123")
    .body(r#"{"name": "alice"}"#)
    .timeout(5000)
    .build();
```

### The Newtype Pattern

```rust
// Wrap a type to give it distinct identity and prevent misuse
struct Meters(f64);
struct Seconds(f64);
struct UserId(u64);
struct EmailAddress(String);

impl EmailAddress {
    pub fn new(s: &str) -> Option<Self> {
        if s.contains('@') {
            Some(EmailAddress(s.to_string()))
        } else {
            None
        }
    }
    pub fn as_str(&self) -> &str { &self.0 }
}

// Now you CANNOT accidentally pass Meters where Seconds is expected
fn travel_time(distance: Meters, speed: Meters) -> Seconds {
    Seconds(distance.0 / speed.0)
}
```

### The State Machine Pattern

```rust
struct Locked;
struct Unlocked;

struct Safe<State> {
    cash: u32,
    _state: std::marker::PhantomData<State>,
}

impl Safe<Locked> {
    pub fn new(cash: u32) -> Self {
        Safe { cash, _state: std::marker::PhantomData }
    }
    pub fn unlock(self, password: &str) -> Result<Safe<Unlocked>, Safe<Locked>> {
        if password == "secret" {
            Ok(Safe { cash: self.cash, _state: std::marker::PhantomData })
        } else {
            Err(self)
        }
    }
}

impl Safe<Unlocked> {
    pub fn take_cash(self) -> (u32, Safe<Locked>) {
        let cash = self.cash;
        let locked = Safe { cash: 0, _state: std::marker::PhantomData };
        (cash, locked)
    }
    pub fn lock(self) -> Safe<Locked> {
        Safe { cash: self.cash, _state: std::marker::PhantomData }
    }
}

// Cannot call take_cash() on a Locked safe — compile error
let safe = Safe::new(1000);
// safe.take_cash(); // ERROR: method not found in Safe<Locked>
if let Ok(unlocked) = safe.unlock("secret") {
    let (cash, locked_again) = unlocked.take_cash();
    println!("Got {} dollars", cash);
}
```

---

## 18. Reading Compiler Errors — A Systematic Method {#18-errors}

The Rust compiler has the best error messages of any language. Learn to read them.

### Error Anatomy

```
error[E0382]: borrow of moved value: `s`
  --> src/main.rs:6:20
   |
3  |     let s = String::from("hello");
   |         - move occurs because `s` has type `String`
4  |     let s2 = s;
   |              - value moved here
5  |     
6  |     println!("{}", s);
   |                    ^ value borrowed here after move
   |
help: consider cloning the value if the intent is to keep both
   |
4  |     let s2 = s.clone();
   |               ++++++++
```

The structure is always:
1. **Error code** `[E0382]` — look this up at `doc.rust-lang.org/error_codes/`
2. **Message** — plain English description of the problem
3. **Location** — file, line, column
4. **Context** — arrows pointing to relevant lines, explaining what happened where
5. **Help** — often suggests the exact fix

### The Most Common Errors and Their Fixes

```rust
// E0382: borrow of moved value
// Fix: clone, or restructure to avoid needing both

// E0499: cannot borrow as mutable more than once
// Fix: ensure mutable borrows don't overlap in time

// E0502: cannot borrow as mutable because also borrowed as immutable
// Fix: ensure immutable borrows are done before mutable borrows

// E0308: mismatched types
fn example_308() {
    // ERROR: expected i32, found f64
    // let x: i32 = 1.5;
    // Fix: cast or use correct type
    let x: i32 = 1;
    let y: f64 = 1.5;
    let z = x as f64 + y; // explicit cast
}

// E0277: trait bound not satisfied
// You're using a type that doesn't implement a required trait
// Fix: implement the trait, add #[derive(...)], or add bounds

// E0515: cannot return reference to local variable
// Fix: return owned value instead of reference

// The compiler often suggests the fix with "help:" or "note:"
// ALWAYS read the full error output
```

---

## 19. Building a Real Program Step by Step {#19-real-program}

Let's build a small but complete program: a task manager.
This demonstrates every concept working together.

```rust
// src/main.rs
use std::collections::HashMap;
use std::fmt;

// ── Data Model ────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
enum Priority {
    Low,
    Medium,
    High,
}

impl fmt::Display for Priority {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Priority::Low => write!(f, "LOW"),
            Priority::Medium => write!(f, "MED"),
            Priority::High => write!(f, "HIGH"),
        }
    }
}

#[derive(Debug, Clone)]
struct Task {
    id: u64,
    title: String,
    done: bool,
    priority: Priority,
    tags: Vec<String>,
}

impl Task {
    fn new(id: u64, title: &str, priority: Priority) -> Self {
        Task {
            id,
            title: title.to_string(),
            done: false,
            priority,
            tags: Vec::new(),
        }
    }

    fn complete(&mut self) {
        self.done = true;
    }

    fn add_tag(&mut self, tag: &str) {
        self.tags.push(tag.to_string());
    }
}

impl fmt::Display for Task {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let status = if self.done { "✓" } else { "○" };
        write!(f, "[{}] #{} [{}] {}", status, self.id, self.priority, self.title)?;
        if !self.tags.is_empty() {
            write!(f, " ({})", self.tags.join(", "))?;
        }
        Ok(())
    }
}

// ── Error Type ────────────────────────────────────────────────────────

#[derive(Debug)]
enum TaskError {
    NotFound(u64),
    AlreadyDone(u64),
}

impl fmt::Display for TaskError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TaskError::NotFound(id) => write!(f, "task #{} not found", id),
            TaskError::AlreadyDone(id) => write!(f, "task #{} is already done", id),
        }
    }
}

// ── Task Store ────────────────────────────────────────────────────────

struct TaskStore {
    tasks: HashMap<u64, Task>,
    next_id: u64,
}

impl TaskStore {
    fn new() -> Self {
        TaskStore {
            tasks: HashMap::new(),
            next_id: 1,
        }
    }

    fn add(&mut self, title: &str, priority: Priority) -> u64 {
        let id = self.next_id;
        self.tasks.insert(id, Task::new(id, title, priority));
        self.next_id += 1;
        id
    }

    fn complete(&mut self, id: u64) -> Result<(), TaskError> {
        match self.tasks.get_mut(&id) {
            None => Err(TaskError::NotFound(id)),
            Some(task) if task.done => Err(TaskError::AlreadyDone(id)),
            Some(task) => {
                task.complete();
                Ok(())
            }
        }
    }

    fn tag(&mut self, id: u64, tag: &str) -> Result<(), TaskError> {
        self.tasks.get_mut(&id)
            .ok_or(TaskError::NotFound(id))
            .map(|task| task.add_tag(tag))
    }

    fn all(&self) -> Vec<&Task> {
        let mut tasks: Vec<&Task> = self.tasks.values().collect();
        tasks.sort_by_key(|t| t.id);
        tasks
    }

    fn pending(&self) -> Vec<&Task> {
        self.all().into_iter().filter(|t| !t.done).collect()
    }

    fn by_priority(&self, p: Priority) -> Vec<&Task> {
        self.all().into_iter().filter(|t| t.priority == p).collect()
    }
}

// ── Main ──────────────────────────────────────────────────────────────

fn main() {
    let mut store = TaskStore::new();

    let id1 = store.add("Write unit tests", Priority::High);
    let id2 = store.add("Update README", Priority::Low);
    let id3 = store.add("Fix login bug", Priority::High);
    let id4 = store.add("Add dark mode", Priority::Medium);

    store.tag(id1, "testing").unwrap();
    store.tag(id3, "bug").unwrap();
    store.tag(id3, "auth").unwrap();

    store.complete(id1).unwrap();

    // Try to complete an already-done task
    match store.complete(id1) {
        Ok(_) => println!("Completed"),
        Err(e) => println!("Error: {}", e),
    }

    // Try to complete a non-existent task
    match store.complete(999) {
        Ok(_) => println!("Completed"),
        Err(e) => println!("Error: {}", e),
    }

    println!("\n=== All Tasks ===");
    for task in store.all() {
        println!("{}", task);
    }

    println!("\n=== Pending Tasks ===");
    for task in store.pending() {
        println!("{}", task);
    }

    println!("\n=== High Priority ===");
    for task in store.by_priority(Priority::High) {
        println!("{}", task);
    }
}
```

---

## The Path Forward

Now that you have the foundations, the path to mastery is clear:

**Week 1–2**: Types, ownership, borrowing. Write small programs.
Focus: Can you explain to yourself WHY each error message appears?

**Week 3–4**: Traits, generics, iterators. Rewrite your HashMap without looking.
Focus: Can you design your own trait hierarchies?

**Week 5–6**: Error handling, lifetimes, closures. Build a CLI tool with clap + anyhow.
Focus: Can you handle all error cases without panic?

**Week 7–8**: Crates ecosystem, async with tokio. Build a small web API.
Focus: Can you read any crate's documentation and use it immediately?

**The permanent practice**: After every problem you solve, ask:
"What is the most minimal set of types and traits that correctly models this problem?"
That question, asked daily, is what separates a top 1% Rust programmer from the rest.

The guide is 19 sections covering everything systematically. Here is the most important thing to understand about your current confusion:

**You are not confused about syntax. You are confused about the mental model.**

Most beginners struggle because they try to memorize syntax before they have internalized the three questions Rust asks about every value: *who owns it, how long does it live, and what can be done with it.* Every single error message — 100% of them — is the compiler telling you that one of those three questions is unanswered.

**The immediate prescription:**

Start with Section 4 (Ownership) and Section 9 (impl). These two sections unlock everything else. Do not move forward until you can, without looking, explain in plain language:
- Why `let s2 = s1` invalidates `s1` when `s1` is a `String` but not when it's an `i32`
- What `&self`, `&mut self`, and `self` mean and when to use each
- What the difference is between an associated function and a method

Then build the task manager in Section 19 from scratch — do not copy it. Every line you type by hand creates a neuromuscular memory pattern. When you get an error, read the full output, locate which of the three ownership questions it is raising, and fix that specific thing.

The confusion you feel right now is not permanent. It is the exact feeling that precedes the moment when the mental model clicks into place. Every Rust programmer has been exactly where you are. The ones who broke through did so by writing code daily, reading errors carefully, and asking "why does the compiler need this?" instead of "how do I make the error go away."