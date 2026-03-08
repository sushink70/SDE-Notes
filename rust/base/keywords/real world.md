# Rust Keywords Reference — Comprehensive Guide
> *Precision. Performance. Ownership. Mastery.*

---

## Table of Contents

1. [Ownership & Memory Keywords](#1-ownership--memory-keywords)
2. [Control Flow Keywords](#2-control-flow-keywords)
3. [Type System Keywords](#3-type-system-keywords)
4. [Function & Closure Keywords](#4-function--closure-keywords)
5. [Module & Visibility Keywords](#5-module--visibility-keywords)
6. [Trait & Impl Keywords](#6-trait--impl-keywords)
7. [Pattern Matching Keywords](#7-pattern-matching-keywords)
8. [Concurrency & Async Keywords](#8-concurrency--async-keywords)
9. [Unsafe & FFI Keywords](#9-unsafe--ffi-keywords)
10. [Lifetime Keywords](#10-lifetime-keywords)
11. [Loop Control Keywords](#11-loop-control-keywords)
12. [Reserved & Future Keywords](#12-reserved--future-keywords)
13. [Full Keyword Quick Reference Table](#13-full-keyword-quick-reference-table)

---

## 1. Ownership & Memory Keywords

### `let`

Binds a value to an immutable variable by default. Immutability is the **default** — a deliberate design forcing you to think about mutation explicitly.

```rust
fn main() {
    let config_path = "/etc/app/config.toml";  // immutable binding
    // config_path = "/tmp/other.toml";         // ERROR: cannot assign twice

    let mut counter = 0usize;                   // mutable binding
    counter += 1;

    // Shadowing: re-use a name with a different type or computation
    let input = "42";
    let input: u32 = input.parse().expect("not a number"); // shadows previous binding
    println!("Parsed: {}", input);
}
```

**Real-world use case — builder pattern via shadowing:**

```rust
fn build_query(raw: &str) -> String {
    let raw = raw.trim();
    let raw = raw.to_lowercase();
    let raw = raw.replace(' ', "_");
    raw // final, clean value
}
```

**Mental model:** `let` is a *contract*: "this name refers to this value, and I promise not to change it." Shadowing is allowed because it creates a *new* binding, not a mutation of the old one.

---

### `mut`

Grants mutability to a binding or reference. Mutation must be *opted into* — Rust's type system enforces this at compile time, eliminating entire classes of bugs.

```rust
fn process_buffer(data: &[u8]) -> Vec<u8> {
    let mut output = Vec::with_capacity(data.len());
    for &byte in data {
        output.push(byte ^ 0xFF); // bitwise NOT
    }
    output
}
```

**Mutable references — exclusive access:**

```rust
fn increment_all(values: &mut [i32]) {
    for v in values.iter_mut() {
        *v += 1;
    }
}

fn main() {
    let mut nums = vec![1, 2, 3];
    increment_all(&mut nums);
    println!("{:?}", nums); // [2, 3, 4]
}
```

**Key rule:** At any given time, you can have *either* one mutable reference *or* any number of immutable references — never both. This is the **borrow checker's core invariant**.

---

### `move`

Transfers ownership of captured variables into a closure or thread. Without `move`, closures borrow from their environment; with `move`, they own it.

```rust
use std::thread;

fn spawn_worker(task_name: String, data: Vec<u8>) -> thread::JoinHandle<usize> {
    // `move` required: thread may outlive the current scope
    thread::spawn(move || {
        println!("Task '{}' processing {} bytes", task_name, data.len());
        data.len()
    })
}

fn main() {
    let name = String::from("compression");
    let payload = vec![0u8; 1024];
    let handle = spawn_worker(name, payload);
    // `name` and `payload` are moved — cannot use them here
    println!("Result: {}", handle.join().unwrap());
}
```

**Move semantics with iterators:**

```rust
fn filter_owned(items: Vec<String>, prefix: &str) -> Vec<String> {
    let prefix = prefix.to_owned(); // own it so closure can move it
    items.into_iter()
        .filter(move |s| s.starts_with(&prefix)) // closure owns `prefix`
        .collect()
}
```

---

### `ref`

Creates a reference to a value in a pattern. Useful when you want to *borrow* inside `match` or destructuring rather than move.

```rust
#[derive(Debug)]
struct Config {
    host: String,
    port: u16,
}

fn describe(cfg: &Config) {
    // Without `ref`, matching on a String field would try to move it
    match cfg {
        Config { host: ref h, port: p } => {
            println!("Connecting to {}:{}", h, p);
        }
    }
}

// More idiomatic modern Rust — match on reference directly
fn describe_v2(cfg: &Config) {
    let Config { host, port } = cfg; // `host` is `&String` automatically
    println!("{}:{}", host, port);
}
```

**In iterator patterns:**

```rust
fn find_long_words(words: &[String], min_len: usize) -> Vec<&str> {
    words.iter()
        .filter(|w| w.len() >= min_len)
        .map(|w| w.as_str())
        .collect()
}
```

---

### `static`

Declares a value with `'static` lifetime — lives for the entire program duration. Constants known at compile time.

```rust
static MAX_CONNECTIONS: usize = 1000;
static APP_NAME: &str = "RustDB";
static MAGIC_BYTES: [u8; 4] = [0x52, 0x55, 0x53, 0x54]; // "RUST"

// Mutable static requires unsafe (global mutable state is inherently dangerous)
static mut INSTANCE_COUNT: u32 = 0;

fn register_instance() {
    unsafe {
        INSTANCE_COUNT += 1; // requires unsafe block
    }
}
```

**Thread-safe global with `lazy_static` or `std::sync::OnceLock`:**

```rust
use std::sync::OnceLock;
use std::collections::HashMap;

static LOOKUP: OnceLock<HashMap<&str, u32>> = OnceLock::new();

fn get_lookup() -> &'static HashMap<&'static str, u32> {
    LOOKUP.get_or_init(|| {
        let mut m = HashMap::new();
        m.insert("alpha", 1);
        m.insert("beta", 2);
        m
    })
}
```

---

## 2. Control Flow Keywords

### `if` / `else`

Unlike C/Go, `if` in Rust is an **expression** — it returns a value. No parentheses required.

```rust
fn classify_score(score: u32) -> &'static str {
    if score >= 90 {
        "Excellent"
    } else if score >= 70 {
        "Good"
    } else if score >= 50 {
        "Average"
    } else {
        "Below average"
    }
}

// if as expression in let
fn parse_flag(s: &str) -> bool {
    let trimmed = s.trim();
    let result = if trimmed == "true" || trimmed == "1" { true } else { false };
    result
}

// Idiomatic: use if-let for Option/Result
fn find_user(id: u64, db: &[(u64, &str)]) {
    if let Some(&(_, name)) = db.iter().find(|&&(uid, _)| uid == id) {
        println!("Found: {}", name);
    } else {
        println!("User {} not found", id);
    }
}
```

---

### `match`

Rust's most powerful control flow construct. Exhaustive by default. Pattern-matching on structure, values, guards, and enums simultaneously.

```rust
#[derive(Debug)]
enum HttpStatus {
    Ok,
    NotFound,
    ServerError(u16),
    Custom { code: u16, message: String },
}

fn handle_response(status: HttpStatus) -> String {
    match status {
        HttpStatus::Ok => "Success".to_string(),
        HttpStatus::NotFound => "Resource missing".to_string(),
        HttpStatus::ServerError(500) => "Internal error".to_string(),
        HttpStatus::ServerError(code) if code >= 500 => {
            format!("Server error: {}", code)
        }
        HttpStatus::ServerError(code) => format!("Error: {}", code),
        HttpStatus::Custom { code, message } => {
            format!("[{}] {}", code, message)
        }
    }
}
```

**Multi-pattern matching:**

```rust
fn is_vowel(c: char) -> bool {
    matches!(c, 'a' | 'e' | 'i' | 'o' | 'u' | 'A' | 'E' | 'I' | 'O' | 'U')
}

fn categorize_byte(b: u8) -> &'static str {
    match b {
        0          => "null",
        1..=31     => "control",
        32..=126   => "printable ASCII",
        127        => "delete",
        128..=255  => "extended",
    }
}
```

---

### `if let` / `while let`

Sugar for matching a single pattern. Cleaner than a full `match` when you only care about one variant.

```rust
use std::collections::VecDeque;

fn process_queue(mut queue: VecDeque<String>) {
    // `while let` drains a queue
    while let Some(item) = queue.pop_front() {
        println!("Processing: {}", item);
    }
}

fn get_port(env_var: &str) -> u16 {
    if let Ok(val) = std::env::var(env_var) {
        if let Ok(port) = val.parse::<u16>() {
            return port;
        }
    }
    8080 // default
}
```

**`let-else` (Rust 1.65+) — the "guard clause" idiom:**

```rust
fn process_record(record: Option<&str>) -> Result<usize, &'static str> {
    let Some(data) = record else {
        return Err("no data provided");
    };
    // `data` is available here as &str
    Ok(data.len())
}
```

---

### `loop`

An infinite loop that can return a value. Rust's only loop construct that can be used as an expression.

```rust
use std::io::{self, BufRead};

fn read_valid_port() -> u16 {
    let stdin = io::stdin();
    loop {
        print!("Enter port (1-65535): ");
        let mut line = String::new();
        stdin.lock().read_line(&mut line).unwrap();
        match line.trim().parse::<u16>() {
            Ok(0) => println!("Port 0 is reserved, try again."),
            Ok(port) => break port, // `break` with value exits the loop
            Err(_) => println!("Invalid number, try again."),
        }
    }
}
```

**Retry pattern with exponential backoff:**

```rust
use std::time::Duration;

fn connect_with_retry(max_attempts: u32) -> Result<(), String> {
    let mut attempts = 0;
    loop {
        attempts += 1;
        match try_connect() {
            Ok(()) => break Ok(()),
            Err(e) if attempts >= max_attempts => break Err(e),
            Err(_) => {
                std::thread::sleep(Duration::from_millis(100 * 2u64.pow(attempts)));
            }
        }
    }
}

fn try_connect() -> Result<(), String> { Ok(()) } // stub
```

---

### `for`

Iterates over anything implementing `IntoIterator`. No index-based loops in idiomatic Rust.

```rust
fn sum_matrix(matrix: &[Vec<f64>]) -> f64 {
    let mut total = 0.0;
    for row in matrix {
        for &val in row {
            total += val;
        }
    }
    total
}

// Idiomatic: use iterator combinators
fn sum_matrix_v2(matrix: &[Vec<f64>]) -> f64 {
    matrix.iter().flat_map(|row| row.iter()).sum()
}

// With enumerate — when you need indices
fn find_first_negative(values: &[i64]) -> Option<usize> {
    for (i, &v) in values.iter().enumerate() {
        if v < 0 {
            return Some(i);
        }
    }
    None
}
```

---

### `while`

Condition-based loop. Use `loop` when you need to return a value; use `while` for simple condition loops.

```rust
fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let (mut lo, mut hi) = (0usize, arr.len());
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal   => return Some(mid),
            std::cmp::Ordering::Less    => lo = mid + 1,
            std::cmp::Ordering::Greater => hi = mid,
        }
    }
    None
}
```

---

### `return`

Explicit early return. In Rust, the last expression in a block is the implicit return — `return` is used for early exits.

```rust
fn validate_username(name: &str) -> Result<(), &'static str> {
    if name.is_empty() {
        return Err("username cannot be empty");
    }
    if name.len() > 32 {
        return Err("username too long");
    }
    if !name.chars().all(|c| c.is_alphanumeric() || c == '_') {
        return Err("username contains invalid characters");
    }
    Ok(()) // implicit return — no semicolon
}
```

---

## 3. Type System Keywords

### `struct`

Defines a named product type. Three forms: named fields, tuple structs, unit structs.

```rust
// Named-field struct
#[derive(Debug, Clone)]
struct NetworkPacket {
    source_ip:   [u8; 4],
    dest_ip:     [u8; 4],
    source_port: u16,
    dest_port:   u16,
    payload:     Vec<u8>,
    checksum:    u32,
}

// Tuple struct — wraps a type with a new name (newtype pattern)
struct Milliseconds(u64);
struct Bytes(usize);

// Unit struct — zero-size, used as marker types or with traits
struct Marker;
struct HttpGetMethod;

impl NetworkPacket {
    fn new(src: [u8; 4], dst: [u8; 4], data: Vec<u8>) -> Self {
        let checksum = data.iter().map(|&b| b as u32).sum();
        Self {
            source_ip: src,
            dest_ip: dst,
            source_port: 0,
            dest_port: 0,
            payload: data,
            checksum,
        }
    }

    fn payload_size(&self) -> Bytes {
        Bytes(self.payload.len())
    }
}
```

**Struct update syntax:**

```rust
#[derive(Debug, Clone)]
struct Config {
    host:    String,
    port:    u16,
    timeout: u64,
    retries: u32,
}

fn with_timeout(base: Config, timeout: u64) -> Config {
    Config { timeout, ..base } // copies all other fields from `base`
}
```

---

### `enum`

Defines a sum type — a value that can be one of several variants, each potentially carrying different data. Rust enums are **algebraic data types**.

```rust
#[derive(Debug)]
enum ParseError {
    UnexpectedEof,
    InvalidToken { line: usize, col: usize, got: char },
    IntegerOverflow(String),
}

#[derive(Debug)]
enum Token {
    Number(f64),
    Identifier(String),
    Operator(char),
    Eof,
}

// The canonical Result and Option are enums:
// enum Option<T> { Some(T), None }
// enum Result<T, E> { Ok(T), Err(E) }

fn tokenize(input: &str) -> Result<Vec<Token>, ParseError> {
    let mut tokens = Vec::new();
    let mut chars = input.chars().peekable();

    while let Some(&c) = chars.peek() {
        match c {
            ' ' | '\t' | '\n' => { chars.next(); }
            '0'..='9' => {
                let num: String = chars.by_ref()
                    .take_while(|c| c.is_ascii_digit())
                    .collect();
                tokens.push(Token::Number(num.parse().unwrap()));
            }
            'a'..='z' | 'A'..='Z' | '_' => {
                let ident: String = chars.by_ref()
                    .take_while(|c| c.is_alphanumeric() || *c == '_')
                    .collect();
                tokens.push(Token::Identifier(ident));
            }
            '+' | '-' | '*' | '/' => {
                tokens.push(Token::Operator(c));
                chars.next();
            }
            other => return Err(ParseError::InvalidToken {
                line: 0, col: 0, got: other
            }),
        }
    }
    tokens.push(Token::Eof);
    Ok(tokens)
}
```

---

### `type`

Creates a type alias. Does not create a new type — just a new name for an existing one.

```rust
// Simplify complex types
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
type NodeId   = u64;
type Weight   = f64;
type AdjList  = Vec<Vec<(NodeId, Weight)>>;

// Function pointer aliases
type TransformFn = fn(f64) -> f64;
type Predicate<T> = fn(&T) -> bool;

fn apply_transform(values: &[f64], transform: TransformFn) -> Vec<f64> {
    values.iter().map(|&v| transform(v)).collect()
}

fn main() {
    let data = vec![1.0, 4.0, 9.0, 16.0];
    let roots = apply_transform(&data, f64::sqrt);
    println!("{:?}", roots); // [1.0, 2.0, 3.0, 4.0]
}
```

---

### `const`

A compile-time constant. Unlike `static`, `const` is inlined at every use site. No fixed memory address.

```rust
const MAX_BUFFER_SIZE: usize = 64 * 1024;       // 64 KiB
const PI: f64 = std::f64::consts::PI;
const HASH_SEED: u64 = 0xDEAD_BEEF_CAFE_BABE;

// Const functions — evaluated at compile time
const fn kilobytes(n: usize) -> usize { n * 1024 }
const fn megabytes(n: usize) -> usize { kilobytes(n) * 1024 }

const STACK_SIZE: usize = megabytes(8);

// Const generics (Rust 1.51+)
fn zero_array<const N: usize>() -> [u8; N] {
    [0u8; N]
}

fn main() {
    let buf: [u8; 16] = zero_array::<16>();
    println!("Stack size: {} bytes", STACK_SIZE);
}
```

---

### `impl`

Implements methods and trait implementations on types.

```rust
#[derive(Debug)]
struct Matrix {
    rows: usize,
    cols: usize,
    data: Vec<f64>,
}

impl Matrix {
    // Associated function (no self) — acts like a constructor
    pub fn new(rows: usize, cols: usize) -> Self {
        Self { rows, cols, data: vec![0.0; rows * cols] }
    }

    pub fn identity(n: usize) -> Self {
        let mut m = Self::new(n, n);
        for i in 0..n { m[(i, i)] = 1.0; }
        m
    }

    // Immutable method
    pub fn get(&self, row: usize, col: usize) -> f64 {
        self.data[row * self.cols + col]
    }

    // Mutable method
    pub fn set(&mut self, row: usize, col: usize, val: f64) {
        self.data[row * self.cols + col] = val;
    }

    // Consuming method (takes ownership)
    pub fn transpose(self) -> Self {
        let mut result = Self::new(self.cols, self.rows);
        for r in 0..self.rows {
            for c in 0..self.cols {
                result.set(c, r, self.get(r, c));
            }
        }
        result
    }
}

impl std::ops::Index<(usize, usize)> for Matrix {
    type Output = f64;
    fn index(&self, (r, c): (usize, usize)) -> &f64 {
        &self.data[r * self.cols + c]
    }
}

impl std::ops::IndexMut<(usize, usize)> for Matrix {
    fn index_mut(&mut self, (r, c): (usize, usize)) -> &mut f64 {
        &mut self.data[r * self.cols + c]
    }
}
```

---

## 4. Function & Closure Keywords

### `fn`

Declares a function. Functions are first-class in Rust — they can be stored, passed, and returned.

```rust
// Basic function
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

// Generic function with trait bounds
fn max_of<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

// Higher-order function
fn apply_twice<T, F: Fn(T) -> T>(f: F, x: T) -> T {
    f(f(x))
}

// Returning a closure (must use `impl Fn` or `Box<dyn Fn>`)
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n
}

fn make_multiplier(n: i32) -> Box<dyn Fn(i32) -> i32> {
    Box::new(move |x| x * n)
}

fn main() {
    let double = make_adder(0); // just as example
    let add5 = make_adder(5);
    println!("{}", add5(10));  // 15

    let times3 = make_multiplier(3);
    println!("{}", apply_twice(|x| x + 1, 10)); // 12
    println!("{}", times3(7)); // 21
}
```

**Diverging functions — never return:**

```rust
fn fatal_error(msg: &str) -> ! {
    eprintln!("FATAL: {}", msg);
    std::process::exit(1);
}

fn unreachable_branch() -> ! {
    unreachable!("this path should never be taken")
}
```

---

### `extern`

Links to external code, defines FFI (Foreign Function Interface) blocks, or specifies calling conventions.

```rust
// C FFI — calling C from Rust
extern "C" {
    fn strlen(s: *const std::ffi::c_char) -> usize;
    fn malloc(size: usize) -> *mut std::ffi::c_void;
    fn free(ptr: *mut std::ffi::c_void);
}

// Exposing Rust functions to C
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

// System-level: using libc
unsafe fn get_string_length(s: *const std::ffi::c_char) -> usize {
    strlen(s)
}
```

**Extern crate (old-style, mostly implicit now):**

```rust
// In older Rust (pre-2018 edition) you'd write:
// extern crate serde;
// Modern Rust: just `use serde::...` — the extern is implicit
```

---

## 5. Module & Visibility Keywords

### `mod`

Declares a module — Rust's namespace and privacy unit.

```rust
// Inline module
mod geometry {
    pub struct Point { pub x: f64, pub y: f64 }

    pub fn distance(a: &Point, b: &Point) -> f64 {
        ((b.x - a.x).powi(2) + (b.y - a.y).powi(2)).sqrt()
    }

    // Private submodule
    mod internal {
        pub(super) fn validate(x: f64, y: f64) -> bool {
            x.is_finite() && y.is_finite()
        }
    }

    pub fn safe_point(x: f64, y: f64) -> Option<Point> {
        if internal::validate(x, y) {
            Some(Point { x, y })
        } else {
            None
        }
    }
}

// File-based module — Rust looks for `./network.rs` or `./network/mod.rs`
mod network;

// Path attribute — custom file location
#[path = "platform/linux.rs"]
mod platform;
```

---

### `use`

Brings items into scope. Can rename with `as`, glob-import with `*`, and group with `{}`.

```rust
use std::collections::{HashMap, HashSet, BTreeMap};
use std::io::{self, Read, Write, BufRead};
use std::sync::{Arc, Mutex, RwLock};

// Rename on import
use std::collections::HashMap as HMap;
use std::fmt::Display as Fmt;

// Re-export (pub use) — curate your public API
pub use crate::error::AppError;
pub use crate::types::{NodeId, Weight};

// Glob import (use sparingly — prefer explicit imports)
use std::prelude::*; // already imported by default in every file

// Nested paths
use std::{
    fs::File,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};
```

---

### `pub`

Controls visibility. Rust defaults to private — everything must be explicitly published.

```rust
pub mod api {
    // Visible everywhere
    pub struct Request {
        pub method: String,
        pub path:   String,
        body:       Vec<u8>, // private field
    }

    impl Request {
        // Public constructor — controls how the struct is built
        pub fn new(method: &str, path: &str) -> Self {
            Self {
                method: method.to_string(),
                path:   path.to_string(),
                body:   Vec::new(),
            }
        }

        pub fn body(&self) -> &[u8] { &self.body }

        pub fn with_body(mut self, data: Vec<u8>) -> Self {
            self.body = data;
            self
        }
    }

    mod internal {
        // pub(crate) — visible within the crate only
        pub(crate) fn parse_headers(raw: &str) -> Vec<(String, String)> {
            raw.lines()
                .filter_map(|line| line.split_once(": "))
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect()
        }

        // pub(super) — visible to parent module only
        pub(super) fn log(msg: &str) {
            eprintln!("[api::internal] {}", msg);
        }
    }
}
```

---

### `crate`

Refers to the root of the current crate. Used in paths and visibility modifiers.

```rust
// In lib.rs or any module:
pub(crate) struct InternalCache {
    entries: std::collections::HashMap<String, Vec<u8>>,
}

// Referencing items from crate root
mod utils {
    use crate::InternalCache; // absolute path from crate root

    pub fn create_cache() -> InternalCache {
        InternalCache { entries: Default::default() }
    }
}
```

---

### `super`

Refers to the parent module.

```rust
mod database {
    pub struct Connection { pub url: String }

    mod pool {
        use super::Connection; // parent module's item

        pub struct Pool {
            connections: Vec<Connection>,
        }

        impl Pool {
            pub fn new(url: &str, size: usize) -> Self {
                let connections = (0..size)
                    .map(|_| Connection { url: url.to_string() })
                    .collect();
                Self { connections }
            }
        }
    }
}
```

---

### `self`

Refers to the current module (in `use`), or the instance being operated on (in `impl`).

```rust
mod shapes {
    pub use self::circle::Circle;     // re-export from submodule
    pub use self::rectangle::Rect;

    mod circle {
        pub struct Circle { pub radius: f64 }
        impl Circle {
            pub fn area(&self) -> f64 {       // `self` = instance
                std::f64::consts::PI * self.radius.powi(2)
            }
            pub fn scale(mut self, factor: f64) -> Self { // consuming self
                self.radius *= factor;
                self // return modified self
            }
        }
    }
    mod rectangle {
        pub struct Rect { pub w: f64, pub h: f64 }
    }
}
```

---

## 6. Trait & Impl Keywords

### `trait`

Defines a shared interface — Rust's mechanism for polymorphism.

```rust
use std::fmt;

// Basic trait
trait Serialize {
    fn serialize(&self) -> Vec<u8>;
    fn type_name(&self) -> &'static str;
}

// Trait with default implementation
trait Summarize {
    fn content(&self) -> &str;

    // Default implementation — can be overridden
    fn summary(&self) -> String {
        let content = self.content();
        if content.len() > 100 {
            format!("{}...", &content[..100])
        } else {
            content.to_string()
        }
    }
}

// Supertrait — requires another trait
trait PrettyPrint: fmt::Display + fmt::Debug {
    fn pretty(&self) -> String {
        format!("Display: {}\nDebug: {:?}", self, self)
    }
}

// Generic trait — associated types
trait Container {
    type Item;
    fn get(&self, index: usize) -> Option<&Self::Item>;
    fn len(&self) -> usize;
    fn is_empty(&self) -> bool { self.len() == 0 }
}

// Trait objects — dynamic dispatch
fn print_all(items: &[Box<dyn Summarize>]) {
    for item in items {
        println!("{}", item.summary());
    }
}
```

---

### `for` (in trait impl)

Implements a trait for a type.

```rust
#[derive(Debug)]
struct Celsius(f64);

#[derive(Debug)]
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

impl From<Fahrenheit> for Celsius {
    fn from(f: Fahrenheit) -> Self {
        Celsius((f.0 - 32.0) * 5.0 / 9.0)
    }
}

impl std::fmt::Display for Celsius {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:.1}°C", self.0)
    }
}

fn main() {
    let boiling = Celsius(100.0);
    let f: Fahrenheit = boiling.into();
    println!("{:?}", f); // Fahrenheit(212.0)
}
```

---

### `where`

Moves trait bounds out of angle brackets for readability. Essential for complex generic constraints.

```rust
use std::fmt::{Debug, Display};
use std::hash::Hash;

// Without where — cramped
fn process<T: Debug + Display + Clone + Hash + Eq>(items: &[T]) { }

// With where — readable
fn process_clean<T>(items: &[T])
where
    T: Debug + Display + Clone + Hash + Eq,
{
    // ...
}

// Where clause with associated types
fn zip_and_collect<I, J>(a: I, b: J) -> Vec<(I::Item, J::Item)>
where
    I: IntoIterator,
    J: IntoIterator,
    I::Item: Clone,
    J::Item: Clone,
{
    a.into_iter().zip(b.into_iter()).collect()
}

// Higher-ranked trait bounds (HRTB)
fn apply_to_str<F>(f: F) -> String
where
    F: for<'a> Fn(&'a str) -> String,
{
    f("hello world")
}
```

---

### `dyn`

Creates a trait object — enables dynamic dispatch (runtime polymorphism).

```rust
use std::fmt;

trait Renderer: fmt::Debug {
    fn render(&self, width: u32, height: u32) -> Vec<u8>;
    fn name(&self) -> &str;
}

#[derive(Debug)] struct OpenGLRenderer;
#[derive(Debug)] struct VulkanRenderer;
#[derive(Debug)] struct SoftwareRenderer;

impl Renderer for OpenGLRenderer {
    fn render(&self, w: u32, h: u32) -> Vec<u8> { vec![0; (w * h * 4) as usize] }
    fn name(&self) -> &str { "OpenGL" }
}
impl Renderer for VulkanRenderer {
    fn render(&self, w: u32, h: u32) -> Vec<u8> { vec![0; (w * h * 4) as usize] }
    fn name(&self) -> &str { "Vulkan" }
}
impl Renderer for SoftwareRenderer {
    fn render(&self, w: u32, h: u32) -> Vec<u8> { vec![0; (w * h * 4) as usize] }
    fn name(&self) -> &str { "Software" }
}

struct Engine {
    renderer: Box<dyn Renderer>, // dynamic dispatch — runtime-chosen
}

impl Engine {
    fn new(renderer: Box<dyn Renderer>) -> Self { Self { renderer } }

    fn draw_frame(&self, w: u32, h: u32) -> Vec<u8> {
        println!("Rendering with {}", self.renderer.name());
        self.renderer.render(w, h)
    }
}

// dyn in function signatures
fn largest_render(renderers: &[&dyn Renderer], w: u32, h: u32) -> Vec<u8> {
    renderers.iter()
        .map(|r| r.render(w, h))
        .max_by_key(|frame| frame.len())
        .unwrap_or_default()
}
```

**`dyn` vs `impl` — the expert's mental model:**

| | `impl Trait` (static) | `dyn Trait` (dynamic) |
|---|---|---|
| Dispatch | Compile-time (monomorphized) | Runtime (vtable) |
| Performance | Zero-cost | Small overhead |
| Heterogeneous collection | ❌ | ✅ |
| Return from function | `impl Fn(...)` | `Box<dyn Fn(...)>` |

---

### `impl Trait` (in return position)

```rust
// Return an iterator without naming its type
fn even_squares(n: u64) -> impl Iterator<Item = u64> {
    (0..n).filter(|x| x % 2 == 0).map(|x| x * x)
}

// Return a closure
fn make_validator(min: usize, max: usize) -> impl Fn(&str) -> bool {
    move |s| s.len() >= min && s.len() <= max
}

fn main() {
    let squares: Vec<u64> = even_squares(10).collect();
    println!("{:?}", squares); // [0, 4, 16, 36, 64]

    let validate = make_validator(3, 20);
    println!("{}", validate("hello")); // true
}
```

---

## 7. Pattern Matching Keywords

### `match` guards — `if` in patterns

```rust
fn describe_number(n: i64) -> &'static str {
    match n {
        x if x < 0   => "negative",
        0             => "zero",
        x if x % 2 == 0 => "positive even",
        _             => "positive odd",
    }
}
```

### `@` bindings — binding and testing simultaneously

```rust
fn check_range(value: u32) {
    match value {
        n @ 1..=9   => println!("single digit: {}", n),
        n @ 10..=99 => println!("double digit: {}", n),
        n           => println!("large: {}", n),
    }
}

// Combining @ with guards
fn classify(x: i32) -> String {
    match x {
        n @ _ if n.abs() > 1000 => format!("extreme: {}", n),
        n @ 0..=100             => format!("in range: {}", n),
        n                       => format!("other: {}", n),
    }
}
```

### `..` (range and struct remainder patterns)

```rust
struct Point3D { x: f64, y: f64, z: f64 }

fn main() {
    let p = Point3D { x: 1.0, y: 2.0, z: 3.0 };

    // Ignore remaining fields
    let Point3D { x, .. } = p;
    println!("x = {}", x);

    // Range patterns
    let nums = (1, 2, 3, 4, 5);
    let (first, .., last) = nums;
    println!("{} {}", first, last); // 1 5

    // In slices
    let arr = [1, 2, 3, 4, 5];
    if let [first, middle @ .., last] = arr.as_slice() {
        println!("first={}, last={}, middle={:?}", first, last, middle);
    }
}
```

---

## 8. Concurrency & Async Keywords

### `async`

Marks a function or block as asynchronous — returns a `Future` instead of executing immediately.

```rust
use std::time::Duration;

// Async function — returns impl Future<Output = Result<String, ...>>
async fn fetch_data(url: &str) -> Result<String, Box<dyn std::error::Error>> {
    // In real code, use reqwest or similar:
    // let response = reqwest::get(url).await?;
    // Ok(response.text().await?)

    // Simulated:
    tokio::time::sleep(Duration::from_millis(100)).await;
    Ok(format!("data from {}", url))
}

// Async block — creates an anonymous future inline
async fn process_urls(urls: Vec<String>) -> Vec<String> {
    let mut results = Vec::new();
    for url in &urls {
        let data = fetch_data(url).await.unwrap_or_default();
        results.push(data);
    }
    results
}

// Concurrent execution with tokio::join!
async fn fetch_all_concurrent(urls: Vec<String>) -> Vec<String> {
    let futures: Vec<_> = urls.iter()
        .map(|url| fetch_data(url))
        .collect();

    futures::future::join_all(futures)
        .await
        .into_iter()
        .filter_map(Result::ok)
        .collect()
}
```

---

### `await`

Suspends an async function until the awaited `Future` resolves. The runtime can execute other tasks while waiting.

```rust
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

async fn send_request(addr: &str, data: &[u8]) -> std::io::Result<Vec<u8>> {
    let mut stream = TcpStream::connect(addr).await?;  // suspend until connected

    stream.write_all(data).await?;                     // suspend until written
    stream.flush().await?;

    let mut response = Vec::new();
    stream.read_to_end(&mut response).await?;          // suspend until read

    Ok(response)
}

// Async trait (requires `async-trait` crate or Rust 1.75+ RPITIT)
#[async_trait::async_trait]
trait DataStore {
    async fn get(&self, key: &str) -> Option<Vec<u8>>;
    async fn set(&self, key: &str, value: Vec<u8>) -> bool;
}
```

---

## 9. Unsafe & FFI Keywords

### `unsafe`

Opts out of Rust's safety guarantees for five specific operations. Used for raw pointers, FFI, accessing mutable statics, calling unsafe functions, and implementing unsafe traits.

```rust
// The five unsafe superpowers:
// 1. Dereference raw pointers
// 2. Call unsafe functions/methods
// 3. Access/modify mutable static variables
// 4. Implement unsafe traits
// 5. Access fields of `union`s

fn raw_memory_copy(src: *const u8, dst: *mut u8, count: usize) {
    unsafe {
        // 1. Dereference raw pointer
        // 2. Call unsafe function (ptr::copy_nonoverlapping)
        std::ptr::copy_nonoverlapping(src, dst, count);
    }
}

// Unsafe function — callers must uphold invariants
unsafe fn from_raw_parts<'a>(ptr: *const u8, len: usize) -> &'a [u8] {
    std::slice::from_raw_parts(ptr, len)
}

// Unsafe trait — implementing it requires care
unsafe trait Zeroable: Sized {
    fn zeroed() -> Self {
        unsafe { std::mem::zeroed() }
    }
}

// Safe abstraction over unsafe code — the idiomatic pattern
pub struct AlignedBuffer {
    ptr: *mut u8,
    len: usize,
    align: usize,
}

impl AlignedBuffer {
    /// Creates an aligned buffer. Returns None if allocation fails.
    pub fn new(size: usize, alignment: usize) -> Option<Self> {
        let layout = std::alloc::Layout::from_size_align(size, alignment).ok()?;
        let ptr = unsafe { std::alloc::alloc(layout) };
        if ptr.is_null() { return None; }
        Some(Self { ptr, len: size, align: alignment })
    }

    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }
}

impl Drop for AlignedBuffer {
    fn drop(&mut self) {
        let layout = std::alloc::Layout::from_size_align(self.len, self.align).unwrap();
        unsafe { std::alloc::dealloc(self.ptr, layout) }
    }
}
```

**Expert mental model:** `unsafe` is not "no safety" — it means *you* are responsible for safety invariants the compiler cannot verify. Always wrap unsafe code in a safe abstraction.

---

### `union`

A type where all fields share the same memory — C-union semantics. Useful for FFI and low-level bit manipulation.

```rust
#[repr(C)]
union FloatBits {
    float_val: f32,
    int_val:   u32,
}

fn float_to_bits(f: f32) -> u32 {
    let u = FloatBits { float_val: f };
    unsafe { u.int_val }
}

fn bits_to_float(bits: u32) -> f32 {
    let u = FloatBits { int_val: bits };
    unsafe { u.float_val }
}

fn main() {
    let pi_bits = float_to_bits(std::f32::consts::PI);
    println!("PI bits: 0x{:08X}", pi_bits); // 0x40490FDB
    println!("Reconstructed: {}", bits_to_float(pi_bits));
}
```

---

## 10. Lifetime Keywords

### `'a` (lifetime parameters)

Lifetimes annotate how long references are valid. They prevent dangling references at compile time — zero-cost safety.

```rust
// The compiler can usually infer lifetimes (lifetime elision rules)
// But explicit annotations are needed when the relationship is ambiguous

// This function: output lifetime tied to input lifetime
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct holding a reference — must annotate
struct StrSplit<'a> {
    remainder: &'a str,
    delimiter: &'a str,
}

impl<'a> Iterator for StrSplit<'a> {
    type Item = &'a str;

    fn next(&mut self) -> Option<&'a str> {
        if let Some(pos) = self.remainder.find(self.delimiter) {
            let part = &self.remainder[..pos];
            self.remainder = &self.remainder[pos + self.delimiter.len()..];
            Some(part)
        } else if !self.remainder.is_empty() {
            let part = self.remainder;
            self.remainder = "";
            Some(part)
        } else {
            None
        }
    }
}

// Multiple lifetime parameters
fn first_word<'a>(sentence: &'a str) -> &'a str {
    sentence.split_whitespace().next().unwrap_or(sentence)
}

// 'static — valid for the entire program
fn get_error_msg(code: u32) -> &'static str {
    match code {
        404 => "Not Found",
        500 => "Internal Server Error",
        _   => "Unknown Error",
    }
}
```

---

## 11. Loop Control Keywords

### `break`

Exits a loop. Can return a value from `loop`. Can target labeled loops.

```rust
fn find_pair(matrix: &[Vec<i32>], target: i32) -> Option<(usize, usize)> {
    'outer: for (i, row) in matrix.iter().enumerate() {
        for (j, &val) in row.iter().enumerate() {
            if val == target {
                break 'outer; // exit both loops
                // return Some((i, j)); -- more idiomatic
            }
        }
    }
    None
}

// break with value
fn parse_first_valid(inputs: &[&str]) -> Option<u32> {
    let result = 'search: loop {
        for &s in inputs {
            if let Ok(n) = s.trim().parse::<u32>() {
                break 'search Some(n);
            }
        }
        break 'search None;
    };
    result
}
```

---

### `continue`

Skips the rest of the current loop iteration.

```rust
fn process_lines(input: &str) -> Vec<String> {
    input.lines()
        .filter_map(|line| {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('#') {
                None // skip blank lines and comments
            } else {
                Some(trimmed.to_string())
            }
        })
        .collect()
}

// With labeled continue
fn process_pairs(data: &[(i32, i32)]) -> Vec<i32> {
    let mut results = Vec::new();
    'pair: for &(a, b) in data {
        if a == 0 { continue 'pair; } // skip this pair
        results.push(b / a);
    }
    results
}
```

---

### `in`

Used in `for` loops to specify the iterable.

```rust
// Three forms of iterating
fn iteration_forms(data: &[String]) {
    // Borrow
    for item in data {              // item: &String
        println!("{}", item);
    }

    // Borrow explicit
    for item in data.iter() {      // item: &String
        println!("{}", item);
    }

    // Mutable borrow
    let mut owned: Vec<String> = data.to_vec();
    for item in owned.iter_mut() { // item: &mut String
        item.push_str("!");
    }

    // Consume (by value)
    for item in owned.into_iter() { // item: String, owned consumed
        println!("{}", item);
    }
}
```

---

## 12. Reserved & Future Keywords

### `as`

Casts between numeric types or renames imports.

```rust
fn safe_cast_example() {
    let big: i64 = 300;
    let small = big as u8; // truncation: 300 % 256 = 44
    let safe = u8::try_from(big).unwrap_or(u8::MAX); // checked cast

    let f = 3.99f64;
    let i = f as i32; // truncation toward zero: 3
    let u = f as u64; // 3

    // Pointer casting (requires unsafe for dereferencing)
    let x: i32 = 42;
    let ptr = &x as *const i32;
    let addr = ptr as usize; // pointer as integer
}

// Import aliasing
use std::collections::HashMap as Map;
use std::io::Error as IoError;
```

---

### `do`, `final`, `override`, `priv`, `typeof`, `unsized`, `virtual`, `yield`, `abstract`, `become`, `box`

These are **reserved keywords** — not yet used by Rust but reserved for potential future use. Do not use them as identifiers.

```rust
// Raw identifiers — use reserved words as identifiers (rare but valid)
let r#type = "integer"; // `type` is a keyword, `r#type` bypasses it
let r#match = 42;
println!("{} {}", r#type, r#match);
```

---

### `macro_rules!` — the macro keyword

Not technically a keyword but fundamental. Declarative macro system.

```rust
macro_rules! vec_of_strings {
    ($($s:expr),* $(,)?) => {
        vec![$($s.to_string()),*]
    };
}

macro_rules! retry {
    ($n:expr, $body:expr) => {{
        let mut result = None;
        for _ in 0..$n {
            match $body {
                Ok(v) => { result = Some(v); break; }
                Err(_) => {}
            }
        }
        result
    }};
}

fn main() {
    let names = vec_of_strings!["Alice", "Bob", "Charlie"];
    println!("{:?}", names);
}
```

---

## 13. Full Keyword Quick Reference Table

| Keyword | Category | Core Purpose |
|---|---|---|
| `as` | Type / Import | Numeric cast or import rename |
| `async` | Concurrency | Declare async function/block |
| `await` | Concurrency | Suspend async execution |
| `break` | Control Flow | Exit loop (optionally with value) |
| `const` | Types | Compile-time constant |
| `continue` | Control Flow | Skip to next loop iteration |
| `crate` | Modules | Refer to crate root |
| `dyn` | Traits | Dynamic dispatch trait object |
| `else` | Control Flow | Alternative branch of `if` |
| `enum` | Types | Sum type / variant type |
| `extern` | FFI | Foreign function interface |
| `false` | Literals | Boolean false literal |
| `fn` | Functions | Declare a function |
| `for` | Control Flow / Traits | Iterate or implement a trait |
| `if` | Control Flow | Conditional expression |
| `impl` | Types / Traits | Implement methods or traits |
| `in` | Control Flow | Specify iterable in `for` |
| `let` | Bindings | Bind value to name |
| `loop` | Control Flow | Infinite loop (returns value) |
| `match` | Control Flow | Exhaustive pattern matching |
| `mod` | Modules | Declare a module |
| `move` | Closures | Transfer ownership into closure |
| `mut` | Bindings | Allow mutation |
| `pub` | Visibility | Make item publicly visible |
| `ref` | Patterns | Borrow in pattern |
| `return` | Functions | Early return |
| `Self` | Types | Alias for implementing type |
| `self` | Modules / Methods | Current module or instance |
| `static` | Memory | Program-lifetime storage |
| `struct` | Types | Product type / record |
| `super` | Modules | Parent module |
| `trait` | Traits | Define shared interface |
| `true` | Literals | Boolean true literal |
| `type` | Types | Type alias |
| `union` | Types | C-union (unsafe) |
| `unsafe` | Safety | Opt out of compile-time checks |
| `use` | Modules | Bring items into scope |
| `where` | Generics | Separate trait bound clauses |
| `while` | Control Flow | Condition-based loop |

---

## Cognitive Mastery Framework

### Keyword Mental Categories

```
OWNERSHIP (the Rust soul):
  let · mut · move · ref · static

ABSTRACTION (what you build):
  fn · struct · enum · trait · impl · type · const · union

NAVIGATION (how you flow):
  if · else · match · loop · while · for · break · continue · return

SCOPE (who can see what):
  mod · use · pub · crate · self · super

SAFETY CONTRACT:
  unsafe · extern

ASYNC MODEL:
  async · await

GENERICS & LIFETIMES:
  where · dyn · 'a (lifetime param)
```

### Expert Intuition Patterns

1. **Default to immutability** — add `mut` only when required.
2. **Prefer `match` over chains of `if-let`** — exhaustiveness is safety.
3. **`dyn` for runtime polymorphism, `impl` for compile-time** — understand the tradeoff.
4. **`unsafe` is a *contract*, not an escape hatch** — document the invariants.
5. **`async/await` composes, not blocks** — think in terms of futures as values.
6. **Lifetimes prevent aliasing bugs** — they're not annotations, they're *proofs*.
7. **`const` > `static`** — prefer compile-time evaluation when possible.

---

*"Master the keywords, and you master the language's philosophy. Each keyword is a statement about values: safety, concurrency, zero-cost abstractions, and explicit intent."*

Here's your complete Rust Keywords Reference — structured for deep understanding, not just syntax recall.

### What's covered across 13 sections:

**Ownership & Memory** — `let`, `mut`, `move`, `ref`, `static` with the borrow checker's core invariants explained through real patterns (builder, retry, aligned buffers).

**Control Flow** — every loop and branch construct, with the critical insight that `if` and `loop` are *expressions*, not statements — a distinction that shapes idiomatic Rust deeply.

**Type System** — `struct`, `enum`, `type`, `const`, `impl` with algebraic data types, newtype pattern, struct update syntax, and const generics.

**Traits** — `trait`, `dyn`, `where`, `impl Trait` with the static vs dynamic dispatch mental model table — this is where expert-level Rust thinking lives.

**Async** — `async`/`await` with the future-as-value mental model, concurrent execution patterns, and async traits.

**Unsafe** — the five unsafe superpowers, the safe-abstraction idiom, `union` for bit manipulation, and raw allocator usage.

**Lifetimes** — explicit annotations with the key insight: lifetimes are *proofs*, not annotations.

### The deeper insight to internalize:
Rust keywords aren't arbitrary — each one enforces a *philosophy*. `mut` is explicit mutation. `unsafe` is explicit contract. `pub` is explicit interface. `async` is explicit concurrency model. Learning them isn't memorization — it's internalizing Rust's design worldview.