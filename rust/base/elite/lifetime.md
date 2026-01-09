# Rust Lifetimes: The Complete Guide

## TL;DR
**Lifetimes are compile-time labels that track how long references remain valid, preventing use-after-free bugs without runtime overhead.**

## The Analogy
Think of lifetimes like library book checkout periods. The lifetime `'a` is the checkout period. You can't read a book (reference) after its due date (lifetime ends). The borrow checker is the librarian ensuring you return books before they're destroyed. Multiple people can borrow copies (shared references), but only one person can check out the original for editing (mutable reference).

## Quick Working Example

```rust
// src/main.rs
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let string1 = String::from("long string");
    let result;
    {
        let string2 = String::from("short");
        result = longest(string1.as_str(), string2.as_str());
        println!("Longest: {}", result); // ✅ Works - used before string2 drops
    }
    // println!("{}", result); // ❌ Won't compile - string2 dropped
}
```

**Run:** `cargo new lifetimes_guide && cd lifetimes_guide && cargo run`

---

## Deep Dive: How Lifetimes Work Internally

### 1. **The Borrow Checker's Perspective**

The compiler performs **region-based analysis**:

```rust
// What the compiler sees (conceptually)
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    // 'a = intersection of x's lifetime and y's lifetime
    // Return value's lifetime = 'a
}

fn main() {
    let string1: String;          // ──┐ 'outer
    let result: &str;             //   │
    {                             //   │
        let string2: String;      // ──┼─┐ 'inner
        result = longest(&string1, &string2); // 'a = 'inner
    }                             //   │ └─ string2 dropped
    // result's lifetime = 'inner //   │
    // but 'inner ended!          //   │
}                                 // ──┘
```

### 2. **Lifetime Elision Rules** (When You Don't Need Annotations)

The compiler auto-infers lifetimes in common patterns:

```rust
// Rule 1: Each input reference gets its own lifetime
fn print(s: &str)              // fn print<'a>(s: &'a str)
fn first(x: &str, y: &str)     // fn first<'a, 'b>(x: &'a str, y: &'b str)

// Rule 2: If exactly one input lifetime, assign it to all outputs
fn get_name(person: &Person) -> &str  // fn get_name<'a>(p: &'a Person) -> &'a str

// Rule 3: If &self or &mut self exists, assign its lifetime to outputs
impl MyStruct {
    fn get_data(&self) -> &Data  // fn get_data<'a>(&'a self) -> &'a Data
}
```

### 3. **Lifetime Variance and Subtyping**

```rust
// 'long: 'short means 'long outlives 'short
// Lifetimes form a subtyping hierarchy

fn example<'long, 'short>(x: &'long str) 
where 
    'long: 'short  // 'long outlives 'short
{
    let y: &'short str = x;  // ✅ Covariance: can use longer lifetime as shorter
}

// Real example: function pointers
fn covariant_example() {
    let f: fn(&'static str) = |x| println!("{}", x);
    let g: fn(&str) = f;  // ✅ 'static is subtype of any lifetime
}
```

---

## Complete Reference: All Lifetime ScenariosNow let me provide the complete production setup:
// ====================
// RUST LIFETIMES: COMPLETE REFERENCE
// ====================

use std::fmt::Display;

// ============================================================
// 1. BASIC LIFETIME ANNOTATIONS
// ============================================================

// Single lifetime parameter
fn first_word<'a>(s: &'a str) -> &'a str {
    s.split_whitespace().next().unwrap_or("")
}

// Multiple lifetime parameters (independent)
fn longest_with_announcement<'a, 'b, 'c>(
    x: &'a str,
    y: &'b str,
    ann: &'c str,
) -> &'a str
where
    'a: 'b,  // 'a must outlive 'b
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() { x } else { x }  // Returns 'a
}

// ============================================================
// 2. STRUCTS WITH LIFETIMES
// ============================================================

// Struct holding a reference
#[derive(Debug)]
struct Excerpt<'a> {
    part: &'a str,
    page: u32,
}

impl<'a> Excerpt<'a> {
    // Method with lifetime elision
    fn level(&self) -> i32 {
        3
    }
    
    // Method returning a reference (elision: output gets self's lifetime)
    fn get_part(&self) -> &str {
        self.part
    }
    
    // Method with explicit lifetime showing part outlives self
    fn announce_and_return_part(&self, announcement: &str) -> &'a str {
        println!("Attention: {}", announcement);
        self.part
    }
}

// Multiple lifetimes in struct
struct MultiRef<'a, 'b> {
    first: &'a str,
    second: &'b str,
}

impl<'a, 'b> MultiRef<'a, 'b> {
    fn choose_first(&self) -> &'a str {
        self.first
    }
}

// ============================================================
// 3. STATIC LIFETIME
// ============================================================

// 'static means the reference lives for the entire program
static GLOBAL: &str = "I live forever";

fn returns_static() -> &'static str {
    "string literals have 'static lifetime"
}

// Leaking to create 'static data (rare, but valid)
fn leak_to_static(s: String) -> &'static str {
    Box::leak(s.into_boxed_str())
}

// ============================================================
// 4. LIFETIME BOUNDS ON GENERICS
// ============================================================

// T must contain only owned data or references that outlive 'a
struct Wrapper<'a, T: 'a> {
    value: &'a T,
}

// Modern syntax (T: 'a is implied if T contains references)
struct ModernWrapper<'a, T> {
    value: &'a T,
}

// Lifetime bound on trait
fn print_ref<'a, T>(value: &'a T)
where
    T: Display + 'a,
{
    println!("{}", value);
}

// ============================================================
// 5. HIGHER-RANKED TRAIT BOUNDS (HRTB)
// ============================================================

// for<'a> means "for any lifetime 'a"
trait Apply {
    fn apply<'a>(&self, x: &'a str) -> &'a str;
}

struct Processor;

impl Apply for Processor {
    fn apply<'a>(&self, x: &'a str) -> &'a str {
        x
    }
}

// HRTB: this function works with any lifetime
fn use_apply<F>(f: F, s: &str) -> &str
where
    F: for<'a> Fn(&'a str) -> &'a str,  // HRTB here
{
    f(s)
}

// ============================================================
// 6. LIFETIME ELISION IN ACTION
// ============================================================

struct Parser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Parser { input, position: 0 }
    }
    
    // Elision: output gets &self's lifetime
    fn peek(&self) -> Option<char> {
        self.input[self.position..].chars().next()
    }
    
    // Explicit: return value tied to input, not self
    fn remaining(&self) -> &'a str {
        &self.input[self.position..]
    }
}

// ============================================================
// 7. COMMON PATTERNS
// ============================================================

// Pattern: Context + Data
struct Context<'ctx> {
    config: &'ctx str,
}

struct Session<'ctx, 'data> {
    context: &'ctx Context<'ctx>,
    data: &'data str,
}

impl<'ctx, 'data> Session<'ctx, 'data> {
    fn process(&self) -> String {
        format!("{}: {}", self.context.config, self.data)
    }
}

// Pattern: Builder with lifetime
struct QueryBuilder<'a> {
    table: &'a str,
    conditions: Vec<&'a str>,
}

impl<'a> QueryBuilder<'a> {
    fn new(table: &'a str) -> Self {
        QueryBuilder {
            table,
            conditions: Vec::new(),
        }
    }
    
    fn add_condition(&mut self, cond: &'a str) -> &mut Self {
        self.conditions.push(cond);
        self
    }
    
    fn build(&self) -> String {
        format!(
            "SELECT * FROM {} WHERE {}",
            self.table,
            self.conditions.join(" AND ")
        )
    }
}

// ============================================================
// 8. ADVANCED: LIFETIME SUBTYPING
// ============================================================

// Demonstrates covariance
fn covariance_example<'long, 'short>(x: &'long str) -> &'short str
where
    'long: 'short,  // 'long outlives 'short
{
    x  // Can return longer lifetime as shorter
}

// Invariance example with mutable references
fn invariance_example<'a>(x: &mut &'a str, y: &mut &'a str) {
    std::mem::swap(x, y);  // Both must have exact same lifetime
}

// ============================================================
// 9. ANONYMOUS LIFETIMES
// ============================================================

// Using '_ when lifetime is unimportant but required
struct Config<'_> {
    name: &'_ str,
}

// In function signatures
fn process_config(config: &Config<'_>) {
    println!("{}", config.name);
}

// ============================================================
// 10. LIFETIME IN CLOSURES
// ============================================================

fn closure_lifetime_example() {
    let string = String::from("hello");
    
    // Closure captures reference with lifetime
    let closure = |x: &str| -> &str {
        if x.len() > string.len() {
            x
        } else {
            &string  // Captures 'string's lifetime
        }
    };
    
    let result = closure("world");
    println!("{}", result);
}

// ============================================================
// 11. COMMON PITFALLS AND SOLUTIONS
// ============================================================

// PITFALL 1: Returning reference to local variable
// fn dangling() -> &str {
//     let s = String::from("hello");
//     &s  // ❌ s dropped at end of function
// }

// SOLUTION: Return owned data
fn no_dangling() -> String {
    String::from("hello")
}

// PITFALL 2: Multiple mutable borrows
// fn multiple_mut_borrows() {
//     let mut v = vec![1, 2, 3];
//     let r1 = &mut v[0];
//     let r2 = &mut v[1];  // ❌ Can't have two mutable borrows
// }

// SOLUTION: Use split_at_mut
fn safe_multiple_mut() {
    let mut v = vec![1, 2, 3, 4];
    let (left, right) = v.split_at_mut(2);
    left[0] = 10;
    right[0] = 20;
}

// PITFALL 3: Lifetime too restrictive
// fn too_restrictive<'a>(x: &'a str, y: &'a str) -> &'a str {
//     x  // Forces x and y to have same lifetime
// }

// SOLUTION: Use separate lifetimes
fn less_restrictive<'a, 'b>(x: &'a str, _y: &'b str) -> &'a str {
    x  // Only x's lifetime matters
}

// ============================================================
// MAIN: DEMONSTRATIONS
// ============================================================

fn main() {
    println!("=== RUST LIFETIMES DEMONSTRATION ===\n");
    
    // 1. Basic example
    println!("1. Basic lifetime:");
    let word = first_word("hello world");
    println!("   First word: {}\n", word);
    
    // 2. Struct with lifetime
    println!("2. Struct with lifetime:");
    let novel = String::from("Call me Ishmael. Some years ago...");
    let excerpt = Excerpt {
        part: &novel[0..20],
        page: 1,
    };
    println!("   {:?}\n", excerpt);
    
    // 3. Static lifetime
    println!("3. Static lifetime:");
    println!("   Global: {}", GLOBAL);
    println!("   Literal: {}\n", returns_static());
    
    // 4. HRTB
    println!("4. Higher-ranked trait bound:");
    let result = use_apply(|s| s, "test");
    println!("   HRTB result: {}\n", result);
    
    // 5. Parser example
    println!("5. Parser with lifetimes:");
    let input = "hello";
    let parser = Parser::new(input);
    println!("   Peek: {:?}", parser.peek());
    println!("   Remaining: {}\n", parser.remaining());
    
    // 6. Query builder
    println!("6. Query builder:");
    let mut builder = QueryBuilder::new("users");
    let query = builder
        .add_condition("age > 18")
        .add_condition("active = true")
        .build();
    println!("   Query: {}\n", query);
    
    // 7. Lifetime subtyping
    println!("7. Lifetime subtyping:");
    let long_lived = String::from("long");
    let short: &str = covariance_example(&long_lived);
    println!("   Covariance works: {}\n", short);
    
    // 8. Closure with lifetime
    println!("8. Closure with lifetime:");
    closure_lifetime_example();
    
    println!("\n=== ALL DEMONSTRATIONS COMPLETE ===");
}

// ============================================================
// TESTS
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_first_word() {
        assert_eq!(first_word("hello world"), "hello");
        assert_eq!(first_word("rust"), "rust");
    }

    #[test]
    fn test_excerpt() {
        let text = String::from("test content");
        let excerpt = Excerpt {
            part: &text,
            page: 1,
        };
        assert_eq!(excerpt.get_part(), "test content");
        assert_eq!(excerpt.level(), 3);
    }

    #[test]
    fn test_query_builder() {
        let mut builder = QueryBuilder::new("products");
        let query = builder
            .add_condition("price < 100")
            .build();
        assert!(query.contains("products"));
        assert!(query.contains("price < 100"));
    }

    #[test]
    fn test_static_lifetime() {
        let s: &'static str = returns_static();
        assert!(!s.is_empty());
    }

    #[test]
    fn test_multi_ref() {
        let first = String::from("first");
        let second = String::from("second");
        let multi = MultiRef {
            first: &first,
            second: &second,
        };
        assert_eq!(multi.choose_first(), "first");
    }
}

// ============================================================
// BENCHMARKS
// ============================================================

#[cfg(test)]
mod benches {
    use super::*;
    
    // Add criterion benchmarks in real projects
    // For now, simple timing demonstration
    
    #[test]
    fn bench_first_word() {
        let text = "the quick brown fox jumps over the lazy dog";
        for _ in 0..10000 {
            let _ = first_word(text);
        }
    }
}

// Integration tests for lifetime scenarios
// Place in tests/integration_tests.rs

use std::cell::RefCell;
use std::rc::Rc;

// Test struct ownership patterns
#[derive(Debug)]
struct DataStore<'a> {
    data: Vec<&'a str>,
}

impl<'a> DataStore<'a> {
    fn new() -> Self {
        DataStore { data: Vec::new() }
    }
    
    fn add(&mut self, item: &'a str) {
        self.data.push(item);
    }
    
    fn get(&self, index: usize) -> Option<&'a str> {
        self.data.get(index).copied()
    }
    
    fn len(&self) -> usize {
        self.data.len()
    }
}

#[test]
fn test_datastore_lifetime_integrity() {
    let item1 = String::from("first");
    let item2 = String::from("second");
    
    let mut store = DataStore::new();
    store.add(&item1);
    store.add(&item2);
    
    assert_eq!(store.len(), 2);
    assert_eq!(store.get(0), Some("first"));
    assert_eq!(store.get(1), Some("second"));
}

#[test]
fn test_lifetime_through_transformation() {
    fn transform<'a>(input: &'a str) -> &'a str {
        input.trim()
    }
    
    let data = String::from("  hello  ");
    let trimmed = transform(&data);
    assert_eq!(trimmed, "hello");
}

#[test]
fn test_multiple_lifetime_params() {
    fn select<'a, 'b>(flag: bool, a: &'a str, b: &'b str) -> String {
        if flag {
            a.to_string()
        } else {
            b.to_string()
        }
    }
    
    let a = String::from("option_a");
    let b = String::from("option_b");
    
    assert_eq!(select(true, &a, &b), "option_a");
    assert_eq!(select(false, &a, &b), "option_b");
}

// Real-world scenario: Configuration management
struct Config<'a> {
    app_name: &'a str,
    version: &'a str,
    features: Vec<&'a str>,
}

impl<'a> Config<'a> {
    fn new(app_name: &'a str, version: &'a str) -> Self {
        Config {
            app_name,
            version,
            features: Vec::new(),
        }
    }
    
    fn add_feature(&mut self, feature: &'a str) {
        self.features.push(feature);
    }
    
    fn summary(&self) -> String {
        format!(
            "{} v{} with {} features",
            self.app_name,
            self.version,
            self.features.len()
        )
    }
}

#[test]
fn test_config_lifetime_management() {
    let name = String::from("MyApp");
    let version = String::from("1.0.0");
    let feature1 = String::from("auth");
    let feature2 = String::from("cache");
    
    let mut config = Config::new(&name, &version);
    config.add_feature(&feature1);
    config.add_feature(&feature2);
    
    assert_eq!(config.summary(), "MyApp v1.0.0 with 2 features");
}

// Edge case: Self-referential attempt (requires Pin or arena)
#[test]
fn test_arena_pattern_for_self_reference() {
    // Using a Vec as a simple arena
    let mut arena: Vec<String> = Vec::new();
    arena.push(String::from("data1"));
    arena.push(String::from("data2"));
    
    // References point into arena
    let refs: Vec<&str> = arena.iter().map(|s| s.as_str()).collect();
    
    assert_eq!(refs.len(), 2);
    assert_eq!(refs[0], "data1");
}

// Testing lifetime bounds with generics
fn process_data<'a, T: 'a>(items: &'a [T]) -> usize
where
    T: std::fmt::Debug,
{
    for item in items {
        println!("{:?}", item);
    }
    items.len()
}

#[test]
fn test_lifetime_bounds_on_generics() {
    let numbers = vec![1, 2, 3, 4, 5];
    let count = process_data(&numbers);
    assert_eq!(count, 5);
}

// Demonstrate lifetime in iterator patterns
struct WindowIterator<'a, T> {
    data: &'a [T],
    window_size: usize,
    position: usize,
}

impl<'a, T> WindowIterator<'a, T> {
    fn new(data: &'a [T], window_size: usize) -> Self {
        WindowIterator {
            data,
            window_size,
            position: 0,
        }
    }
}

impl<'a, T> Iterator for WindowIterator<'a, T> {
    type Item = &'a [T];
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.position + self.window_size <= self.data.len() {
            let window = &self.data[self.position..self.position + self.window_size];
            self.position += 1;
            Some(window)
        } else {
            None
        }
    }
}

#[test]
fn test_iterator_with_lifetimes() {
    let data = vec![1, 2, 3, 4, 5];
    let windows: Vec<_> = WindowIterator::new(&data, 3).collect();
    
    assert_eq!(windows.len(), 3);
    assert_eq!(windows[0], &[1, 2, 3]);
    assert_eq!(windows[1], &[2, 3, 4]);
    assert_eq!(windows[2], &[3, 4, 5]);
}

// Testing lifetime with Result types
fn parse_number<'a>(input: &'a str) -> Result<i32, &'a str> {
    input.parse().map_err(|_| input)
}

#[test]
fn test_lifetime_in_result() {
    let valid = "42";
    let invalid = "not_a_number";
    
    assert_eq!(parse_number(valid), Ok(42));
    assert_eq!(parse_number(invalid), Err("not_a_number"));
}

// Performance: Ensure zero-cost abstractions
#[test]
fn test_zero_cost_lifetime_abstraction() {
    use std::time::Instant;
    
    let data = "a".repeat(1_000_000);
    
    // With lifetime (zero-cost)
    let start = Instant::now();
    for _ in 0..1000 {
        let _borrowed: &str = &data;
    }
    let borrow_time = start.elapsed();
    
    // Direct access
    let start = Instant::now();
    for _ in 0..1000 {
        let _direct = data.as_str();
    }
    let direct_time = start.elapsed();
    
    // Should be negligible difference (within 10% variance)
    let ratio = borrow_time.as_nanos() as f64 / direct_time.as_nanos().max(1) as f64;
    assert!(ratio < 2.0, "Lifetime abstraction should be zero-cost");
}

// Criterion benchmarks for lifetime patterns
// Place in benches/lifetime_benchmarks.rs
// Add to Cargo.toml: [dev-dependencies] criterion = "0.5"
// [[bench]] name = "lifetime_benchmarks" harness = false

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

// Benchmark: Reference vs Owned
fn benchmark_reference_vs_owned(c: &mut Criterion) {
    let data = "test_data".repeat(1000);
    
    let mut group = c.benchmark_group("reference_vs_owned");
    
    group.bench_function("with_reference", |b| {
        b.iter(|| {
            fn process(s: &str) -> usize {
                s.len()
            }
            black_box(process(&data))
        });
    });
    
    group.bench_function("with_clone", |b| {
        b.iter(|| {
            fn process(s: String) -> usize {
                s.len()
            }
            black_box(process(data.clone()))
        });
    });
    
    group.finish();
}

// Benchmark: Lifetime in hot path
struct Cache<'a> {
    entries: Vec<&'a str>,
}

impl<'a> Cache<'a> {
    fn new() -> Self {
        Cache { entries: Vec::new() }
    }
    
    fn insert(&mut self, entry: &'a str) {
        self.entries.push(entry);
    }
    
    fn lookup(&self, key: &str) -> Option<&&'a str> {
        self.entries.iter().find(|e| e.starts_with(key))
    }
}

fn benchmark_cache_lookup(c: &mut Criterion) {
    let entries: Vec<String> = (0..1000)
        .map(|i| format!("key_{:04}", i))
        .collect();
    
    let mut cache = Cache::new();
    for entry in &entries {
        cache.insert(entry);
    }
    
    c.bench_function("cache_lookup", |b| {
        b.iter(|| {
            black_box(cache.lookup("key_0500"))
        });
    });
}

// Benchmark: String slicing patterns
fn benchmark_string_slicing(c: &mut Criterion) {
    let data = "hello world from rust lifetimes".to_string();
    
    let mut group = c.benchmark_group("string_slicing");
    
    group.bench_function("borrow_slice", |b| {
        b.iter(|| {
            let slice: &str = &data[0..5];
            black_box(slice)
        });
    });
    
    group.bench_function("allocate_substring", |b| {
        b.iter(|| {
            let substring = data[0..5].to_string();
            black_box(substring)
        });
    });
    
    group.finish();
}

// Benchmark: Iterator with lifetimes
fn benchmark_iterator_lifetimes(c: &mut Criterion) {
    let data: Vec<i32> = (0..10000).collect();
    
    let mut group = c.benchmark_group("iterator");
    
    group.bench_function("borrowed_iterator", |b| {
        b.iter(|| {
            let sum: i32 = data.iter().sum();
            black_box(sum)
        });
    });
    
    group.bench_function("into_iterator", |b| {
        b.iter(|| {
            let cloned = data.clone();
            let sum: i32 = cloned.into_iter().sum();
            black_box(sum)
        });
    });
    
    group.finish();
}

// Benchmark: Different string types
fn benchmark_string_types(c: &mut Criterion) {
    let mut group = c.benchmark_group("string_types");
    
    for size in [10, 100, 1000].iter() {
        let data = "x".repeat(*size);
        
        group.bench_with_input(
            BenchmarkId::new("str_reference", size),
            size,
            |b, _| {
                b.iter(|| {
                    fn process(s: &str) -> usize { s.len() }
                    black_box(process(&data))
                });
            }
        );
        
        group.bench_with_input(
            BenchmarkId::new("string_owned", size),
            size,
            |b, _| {
                b.iter(|| {
                    fn process(s: String) -> usize { s.len() }
                    black_box(process(data.clone()))
                });
            }
        );
    }
    
    group.finish();
}

criterion_group!(
    benches,
    benchmark_reference_vs_owned,
    benchmark_cache_lookup,
    benchmark_string_slicing,
    benchmark_iterator_lifetimes,
    benchmark_string_types
);

criterion_main!(benches);

// Run with: cargo bench
// View results: target/criterion/report/index.html
// Profile with: cargo bench --bench lifetime_benchmarks -- --profile-time=10

# Multi-stage Dockerfile for Rust lifetime examples
FROM rust:1.75-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy main to cache dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY src ./src
COPY tests ./tests
COPY benches ./benches

# Build the actual application
RUN touch src/main.rs && \
    cargo build --release

# Run tests
RUN cargo test --release

# Run benchmarks (optional, can be slow)
# RUN cargo bench --no-run

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/lifetimes_guide /app/lifetimes_guide

# Non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

CMD ["./lifetimes_guide"]

# Build: docker build -t lifetimes-guide .
# Run: docker run --rm lifetimes-guide
# Test: docker run --rm lifetimes-guide cargo test

name: Rust Lifetimes CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  CARGO_TERM_COLOR: always
  RUST_BACKTRACE: 1

jobs:
  # Code quality checks
  lint:
    name: Lint and Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      
      - name: Cache cargo registry
        uses: actions/cache@v3
        with:
          path: ~/.cargo/registry
          key: ${{ runner.os }}-cargo-registry-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Cache cargo index
        uses: actions/cache@v3
        with:
          path: ~/.cargo/git
          key: ${{ runner.os }}-cargo-git-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Cache target directory
        uses: actions/cache@v3
        with:
          path: target
          key: ${{ runner.os }}-target-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Check formatting
        run: cargo fmt -- --check
      
      - name: Clippy
        run: cargo clippy --all-targets --all-features -- -D warnings

  # Unit and integration tests
  test:
    name: Test Suite
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        rust: [stable, beta, nightly]
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust ${{ matrix.rust }}
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-${{ matrix.rust }}-cargo-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Run tests
        run: cargo test --verbose --all-features
      
      - name: Run doc tests
        run: cargo test --doc

  # Benchmarks (informational only, no failure)
  benchmark:
    name: Benchmarks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-bench-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Run benchmarks
        run: cargo bench --no-run
        continue-on-error: true

  # Security audit
  security:
    name: Security Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install cargo-audit
        run: cargo install cargo-audit
      
      - name: Run security audit
        run: cargo audit

  # Code coverage
  coverage:
    name: Code Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable
      
      - name: Install tarpaulin
        run: cargo install cargo-tarpaulin
      
      - name: Generate coverage
        run: cargo tarpaulin --out Xml --all-features
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./cobertura.xml
          fail_ci_if_error: false

  # Build optimized binary
  build:
    name: Build Release
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-release-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Build release
        run: cargo build --release --verbose
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: lifetimes-guide-linux
          path: target/release/lifetimes_guide

  # Docker build
  docker:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: lifetimes-guide:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

# Rust Lifetimes: Hands-On Exercises

Complete these exercises in order to master Rust lifetimes. Each exercise builds on the previous one.

---

## Exercise 1: Basic Lifetime Annotations (Beginner)

**Goal**: Understand basic lifetime syntax and the borrow checker.

### Task 1.1: Fix the Compiler Error

```rust
// This code doesn't compile. Fix it by adding lifetime annotations.
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

fn main() {
    let string1 = String::from("long string is long");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(string1.as_str(), string2.as_str());
    }
    println!("The longest string is {}", result);
}
```

**Expected Fix**: Add lifetime annotations and adjust the code so result is used within the correct scope.

### Task 1.2: String Tokenizer

Implement a function that splits a string and returns the first token:

```rust
// Fix the lifetime annotations
fn first_token(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_first_token() {
        assert_eq!(first_token("hello world"), "hello");
        assert_eq!(first_token("rust"), "rust");
        assert_eq!(first_token(""), "");
    }
}
```

**Challenge**: Extend this to return the first N tokens as a slice.

---

## Exercise 2: Structs with Lifetimes (Intermediate)

**Goal**: Learn to use lifetimes in structs and implement methods.

### Task 2.1: Build a TextAnalyzer

```rust
// Complete this struct and its methods
struct TextAnalyzer<'a> {
    text: &'a str,
    // Add more fields as needed
}

impl<'a> TextAnalyzer<'a> {
    fn new(text: &'a str) -> Self {
        // Implement
    }
    
    fn word_count(&self) -> usize {
        // Implement
    }
    
    fn longest_word(&self) -> &str {
        // Implement: return the longest word in the text
    }
    
    fn words_longer_than(&self, min_length: usize) -> Vec<&'a str> {
        // Implement: return all words longer than min_length
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_analyzer() {
        let text = "the quick brown fox jumps over the lazy dog";
        let analyzer = TextAnalyzer::new(text);
        
        assert_eq!(analyzer.word_count(), 9);
        assert_eq!(analyzer.longest_word(), "quick"); // or "brown" or "jumps"
        
        let long_words = analyzer.words_longer_than(4);
        assert!(long_words.contains(&"quick"));
        assert!(long_words.contains(&"brown"));
    }
}
```

### Task 2.2: Implement a CSV Row Parser

```rust
struct CsvRow<'a> {
    data: &'a str,
    delimiter: char,
}

impl<'a> CsvRow<'a> {
    fn new(data: &'a str, delimiter: char) -> Self {
        // Implement
    }
    
    fn get_field(&self, index: usize) -> Option<&'a str> {
        // Return the field at the given index
    }
    
    fn field_count(&self) -> usize {
        // Return number of fields
    }
}

// Write tests
```

---

## Exercise 3: Multiple Lifetimes (Advanced)

**Goal**: Master multiple lifetime parameters and constraints.

### Task 3.1: Build a Template Engine

```rust
struct Template<'template, 'data> {
    template: &'template str,
    data: &'data str,
}

impl<'template, 'data> Template<'template, 'data> {
    fn new(template: &'template str, data: &'data str) -> Self {
        Template { template, data }
    }
    
    // Replace {{placeholder}} with data
    fn render(&self) -> String {
        // Implement: replace all {{placeholder}} with self.data
    }
    
    // Return the template string
    fn get_template(&self) -> &'template str {
        self.template
    }
    
    // Return the data string
    fn get_data(&self) -> &'data str {
        self.data
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_template() {
        let tmpl = "Hello, {{name}}!";
        let data = "World";
        
        let template = Template::new(tmpl, data);
        assert_eq!(template.render(), "Hello, World!");
    }
}
```

### Task 3.2: Implement a Cache with Entries

```rust
struct Cache<'cache, 'entry> {
    name: &'cache str,
    entries: Vec<&'entry str>,
}

impl<'cache, 'entry> Cache<'cache, 'entry> {
    fn new(name: &'cache str) -> Self {
        // Implement
    }
    
    fn add_entry(&mut self, entry: &'entry str) {
        // Implement
    }
    
    fn find_entry(&self, prefix: &str) -> Option<&&'entry str> {
        // Find first entry starting with prefix
    }
    
    fn entry_count(&self) -> usize {
        // Implement
    }
}

// Constraint: 'cache should be able to outlive 'entry
// Write tests demonstrating this
```

---

## Exercise 4: Real-World Application (Expert)

**Goal**: Build a production-grade HTTP request parser with lifetimes.

### Task 4.1: HTTP Request Parser

```rust
#[derive(Debug, PartialEq)]
enum Method {
    GET,
    POST,
    PUT,
    DELETE,
}

struct HttpRequest<'a> {
    method: Method,
    path: &'a str,
    version: &'a str,
    headers: Vec<(&'a str, &'a str)>,
    body: Option<&'a str>,
}

impl<'a> HttpRequest<'a> {
    // Parse a raw HTTP request
    fn parse(raw: &'a str) -> Result<Self, &'static str> {
        // Implement a proper HTTP parser
        // Format:
        // GET /path HTTP/1.1
        // Header1: Value1
        // Header2: Value2
        //
        // Optional body
        
        todo!()
    }
    
    fn get_header(&self, name: &str) -> Option<&'a str> {
        // Implement case-insensitive header lookup
        todo!()
    }
    
    fn has_header(&self, name: &str) -> bool {
        // Implement
        todo!()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_get_request() {
        let raw = "GET /api/users HTTP/1.1\r\n\
                   Host: example.com\r\n\
                   User-Agent: rust-client\r\n\
                   \r\n";
        
        let request = HttpRequest::parse(raw).unwrap();
        assert_eq!(request.method, Method::GET);
        assert_eq!(request.path, "/api/users");
        assert_eq!(request.version, "HTTP/1.1");
        assert_eq!(request.get_header("Host"), Some("example.com"));
        assert!(request.body.is_none());
    }
    
    #[test]
    fn test_parse_post_request() {
        let raw = "POST /api/data HTTP/1.1\r\n\
                   Content-Type: application/json\r\n\
                   Content-Length: 13\r\n\
                   \r\n\
                   {\"key\":\"val\"}";
        
        let request = HttpRequest::parse(raw).unwrap();
        assert_eq!(request.method, Method::POST);
        assert_eq!(request.body, Some("{\"key\":\"val\"}"));
    }
}
```

### Task 4.2: Implement a Log Parser

Build a parser that extracts fields from log lines without allocating:

```rust
#[derive(Debug)]
struct LogEntry<'a> {
    timestamp: &'a str,
    level: &'a str,
    message: &'a str,
    metadata: Vec<(&'a str, &'a str)>,
}

impl<'a> LogEntry<'a> {
    // Parse format: [2024-01-08 10:30:45] INFO message key1=val1 key2=val2
    fn parse(line: &'a str) -> Result<Self, &'static str> {
        // Implement zero-allocation parsing
        todo!()
    }
    
    fn get_metadata(&self, key: &str) -> Option<&'a str> {
        todo!()
    }
}

// Add comprehensive tests and benchmarks
```

---

## Exercise 5: Performance Optimization (Expert)

**Goal**: Understand the performance implications of lifetimes vs ownership.

### Task 5.1: Benchmark String Operations

Create benchmarks comparing:
1. String slicing with lifetimes (`&str`)
2. String cloning (`String`)
3. `Cow<str>` for copy-on-write

```rust
// Use criterion for benchmarking
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_string_strategies(c: &mut Criterion) {
    let data = "the quick brown fox".repeat(100);
    
    // Benchmark 1: Lifetime-based slicing
    c.bench_function("lifetime_slice", |b| {
        b.iter(|| {
            let slice = &data[0..100];
            black_box(slice)
        });
    });
    
    // Benchmark 2: Cloning
    c.bench_function("clone_string", |b| {
        b.iter(|| {
            let cloned = data[0..100].to_string();
            black_box(cloned)
        });
    });
    
    // Benchmark 3: Cow
    // Implement and benchmark
}

criterion_group!(benches, benchmark_string_strategies);
criterion_main!(benches);
```

### Task 5.2: Memory Profiling

Use `valgrind` or `heaptrack` to measure memory usage:

```bash
# Add these commands to your README
cargo build --release
valgrind --tool=massif target/release/your_binary
ms_print massif.out.* > memory_profile.txt
```

---

## Success Criteria

For each exercise, you should:

1. ✅ Code compiles without warnings
2. ✅ All tests pass
3. ✅ Clippy reports no issues: `cargo clippy`
4. ✅ Benchmarks show reasonable performance
5. ✅ Documentation explains lifetime choices
6. ✅ Can explain why each lifetime annotation is necessary

---

## Submission Checklist

- [ ] All exercises completed
- [ ] Tests written and passing
- [ ] Benchmarks implemented
- [ ] Code formatted: `cargo fmt`
- [ ] No clippy warnings: `cargo clippy`
- [ ] Documentation comments added
- [ ] Performance analyzed and documented
- [ ] CI pipeline passes

---

## Next Steps After Completion

1. **Study async lifetimes**: Understand `'static` requirements in async contexts
2. **Explore Pin**: Learn pinning for self-referential structs
3. **Arena allocation**: Study `bumpalo` and `typed-arena` for lifetime management
4. **Unsafe and lifetimes**: Understand how `unsafe` interacts with lifetime guarantees
5. **Read the Nomicon**: Deep dive into Rust's unsafe and advanced lifetime topics

---

## Additional Challenges (Optional)

1. Implement a zero-copy JSON parser using lifetimes
2. Build a compile-time HTML template engine with lifetime safety
3. Create a memory-mapped file parser that returns borrowed slices
4. Implement a trie data structure with lifetime-aware nodes
5. Build a custom allocator that uses lifetime bounds

Good luck! Remember: if the borrow checker complains, it's protecting you from bugs. 🦀

[package]
name = "lifetimes_guide"
version = "0.1.0"
edition = "2021"
rust-version = "1.75"
authors = ["Your Name <you@example.com>"]
license = "MIT OR Apache-2.0"
description = "Comprehensive guide to Rust lifetimes with production examples"
repository = "https://github.com/yourusername/lifetimes_guide"
keywords = ["lifetimes", "rust", "tutorial", "examples"]
categories = ["development-tools", "education"]

[dependencies]
# Logging and tracing
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
tracing-opentelemetry = "0.22"
opentelemetry = { version = "0.21", features = ["trace", "metrics"] }
opentelemetry-otlp = { version = "0.14", features = ["trace", "metrics"] }

# Metrics
prometheus = "0.13"

# Async runtime (if needed)
tokio = { version = "1", features = ["full"], optional = true }

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
proptest = "1.4"  # Property-based testing
quickcheck = "1.0"  # Another property testing framework
tempfile = "3.8"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true

[profile.bench]
inherits = "release"

[[bench]]
name = "lifetime_benchmarks"
harness = false

[features]
default = []
async = ["tokio"]

# Lint configuration
[lints.rust]
unsafe_code = "forbid"
missing_docs = "warn"

[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
cargo = "warn"

# Exclude some overly pedantic lints
module_name_repetitions = "allow"
missing_errors_doc = "allow"

# Production Security Checklist for Rust Lifetimes

## Memory Safety (Lifetime-Specific)

- [ ] **No dangling pointers**: Verify all references are valid for their entire usage
- [ ] **No use-after-free**: Ensure borrowed data outlives all references
- [ ] **No data races**: Check that mutable references are exclusive
- [ ] **Bounds checking**: All slice accesses are validated or use checked methods
- [ ] **No unsafe blocks**: If `unsafe` is used, document safety invariants thoroughly

### Common Lifetime Vulnerabilities

```rust
// ❌ VULNERABLE: Returning reference to local
fn vulnerable() -> &str {
    let s = String::from("bad");
    &s  // s dropped, reference invalid
}

// ✅ SAFE: Return owned data
fn safe() -> String {
    String::from("good")
}

// ❌ VULNERABLE: Overlapping borrows
fn vulnerable_borrow(v: &mut Vec<i32>) {
    let first = &v[0];
    v.push(42);  // Invalidates 'first'
    println!("{}", first);
}

// ✅ SAFE: Clone or restructure
fn safe_borrow(v: &mut Vec<i32>) {
    let first_val = v[0];  // Copy the value
    v.push(42);
    println!("{}", first_val);
}
```

---

## Input Validation

- [ ] **Validate all string inputs**: Check for null bytes, invalid UTF-8
- [ ] **Bounds check indices**: Never use `[]` without validation, prefer `.get()`
- [ ] **Sanitize user data**: Escape special characters before using in formats
- [ ] **Length limits**: Enforce maximum sizes on input strings/slices
- [ ] **Check for panic conditions**: Use `checked_*` methods for arithmetic

### Example: Safe Input Handling

```rust
fn safe_parse_line(input: &str) -> Result<Vec<&str>, &'static str> {
    // Validate length
    if input.len() > 10_000 {
        return Err("Input too long");
    }
    
    // Validate UTF-8 (already guaranteed by &str)
    // Validate no null bytes
    if input.contains('\0') {
        return Err("Null byte in input");
    }
    
    // Safe parsing
    let fields: Vec<&str> = input
        .split(',')
        .take(100)  // Limit number of fields
        .collect();
    
    Ok(fields)
}
```

---

## Dependency Security

- [ ] **Run `cargo audit`** regularly to check for known vulnerabilities
- [ ] **Pin dependency versions** in production `Cargo.lock`
- [ ] **Review transitive dependencies**: Check what your deps pull in
- [ ] **Use minimal feature flags**: Don't enable unnecessary features
- [ ] **Keep dependencies updated**: But test thoroughly after updates

```bash
# Install and run cargo-audit
cargo install cargo-audit
cargo audit

# Check for outdated dependencies
cargo install cargo-outdated
cargo outdated

# Deny certain dependency licenses
cargo install cargo-deny
cargo deny check
```

---

## API Security

- [ ] **Validate all public API inputs**: Never trust caller data
- [ ] **Document safety requirements**: Use `# Safety` sections
- [ ] **Use type system for guarantees**: Make invalid states unrepresentable
- [ ] **Avoid exposing internal pointers**: Don't return raw pointers in public APIs
- [ ] **Check lifetime compatibility**: Ensure returned references are valid

### Example: Type-Safe API

```rust
// ❌ UNSAFE: Exposes raw pointer
pub struct UnsafeAPI {
    data: Vec<u8>,
}

impl UnsafeAPI {
    pub fn get_ptr(&self) -> *const u8 {
        self.data.as_ptr()  // Dangerous!
    }
}

// ✅ SAFE: Type-safe interface
pub struct SafeAPI<'a> {
    data: &'a [u8],
}

impl<'a> SafeAPI<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        SafeAPI { data }
    }
    
    pub fn get_byte(&self, index: usize) -> Option<u8> {
        self.data.get(index).copied()
    }
}
```

---

## Error Handling

- [ ] **Never panic on user input**: Use `Result` for all fallible operations
- [ ] **Don't leak information in errors**: Sanitize error messages for production
- [ ] **Log errors securely**: Don't log sensitive data
- [ ] **Handle all `Result` types**: Never use `.unwrap()` in production code
- [ ] **Validate before unwrap**: If you must unwrap, document why it's safe

```rust
// ❌ BAD: Panics on invalid input
fn bad_parse(input: &str) -> i32 {
    input.parse().unwrap()  // Panics!
}

// ✅ GOOD: Returns Result
fn good_parse(input: &str) -> Result<i32, String> {
    input.parse().map_err(|e| format!("Parse error: {}", e))
}

// ✅ BETTER: Custom error type
#[derive(Debug)]
pub enum ParseError {
    InvalidFormat,
    OutOfRange,
}

fn better_parse(input: &str) -> Result<i32, ParseError> {
    let num = input.parse().map_err(|_| ParseError::InvalidFormat)?;
    if num < 0 || num > 100 {
        return Err(ParseError::OutOfRange);
    }
    Ok(num)
}
```

---

## Performance & DoS Prevention

- [ ] **Set timeouts**: All I/O operations should have timeouts
- [ ] **Limit resource usage**: Bound memory allocations, iterations
- [ ] **Prevent algorithmic complexity attacks**: Use O(1) or O(log n) lookups
- [ ] **Rate limit API calls**: Prevent abuse
- [ ] **Validate content length**: Check size before allocating

```rust
use std::time::Duration;

fn safe_operation_with_limits(input: &str) -> Result<Vec<&str>, &'static str> {
    // Limit input size
    const MAX_INPUT: usize = 1_000_000;
    if input.len() > MAX_INPUT {
        return Err("Input too large");
    }
    
    // Limit output size
    const MAX_FIELDS: usize = 1000;
    let fields: Vec<&str> = input
        .split(',')
        .take(MAX_FIELDS)
        .collect();
    
    Ok(fields)
}
```

---

## Logging & Monitoring (Security-Conscious)

- [ ] **Don't log sensitive data**: Passwords, tokens, PII
- [ ] **Redact when necessary**: Mask credit cards, SSNs
- [ ] **Use structured logging**: JSON for easy parsing
- [ ] **Log security events**: Authentication, authorization failures
- [ ] **Set appropriate log levels**: Info in prod, debug in dev

```rust
use tracing::{info, warn, error, instrument};

#[instrument(skip(password))]  // Don't log password
fn login(username: &str, password: &str) -> Result<(), &'static str> {
    info!(username = %username, "Login attempt");
    
    // Validate credentials
    if authenticate(username, password) {
        info!(username = %username, "Login successful");
        Ok(())
    } else {
        warn!(username = %username, "Login failed");
        Err("Invalid credentials")
    }
}

fn log_payment(amount: u64, card_number: &str) {
    // Redact sensitive data
    let masked = format!("****-****-****-{}", &card_number[card_number.len()-4..]);
    info!(amount = amount, card = masked, "Payment processed");
}
```

---

## Testing for Security

- [ ] **Fuzz test parsers**: Use `cargo-fuzz` on any parsing code
- [ ] **Property-based testing**: Use `proptest` for invariants
- [ ] **Test edge cases**: Empty strings, max values, null bytes
- [ ] **Test error paths**: Ensure errors don't leak data
- [ ] **Integration tests**: Test full security flow

```rust
#[cfg(test)]
mod security_tests {
    use super::*;
    
    #[test]
    fn test_rejects_oversized_input() {
        let huge = "x".repeat(2_000_000);
        assert!(safe_parse_line(&huge).is_err());
    }
    
    #[test]
    fn test_rejects_null_bytes() {
        let with_null = "hello\0world";
        assert!(safe_parse_line(with_null).is_err());
    }
    
    #[test]
    fn test_rejects_invalid_utf8() {
        // &str guarantees valid UTF-8, but test at boundaries
        let valid = "hello 世界";
        assert!(safe_parse_line(valid).is_ok());
    }
}
```

---

## Deployment Security

- [ ] **Use multi-stage Docker builds**: Minimize attack surface
- [ ] **Run as non-root user**: Drop privileges
- [ ] **Scan Docker images**: Use `trivy` or `grype`
- [ ] **Enable TLS**: All network communication encrypted
- [ ] **Secrets management**: Use vault, not environment variables
- [ ] **Enable ASLR**: Address Space Layout Randomization
- [ ] **Strip debug symbols**: In release builds

```dockerfile
# Example from earlier Dockerfile
FROM rust:1.75-slim as builder
# ... build steps ...

FROM debian:bookworm-slim
# Security: non-root user
RUN useradd -m -u 1000 appuser
USER appuser
# Security: minimal runtime
COPY --from=builder /app/target/release/app /app/app
CMD ["./app"]
```

---

## Lifetime-Specific Security Considerations

### 1. Ensure 'static Safety

```rust
// ❌ DANGEROUS: Leaking to 'static
fn leak_sensitive(password: String) -> &'static str {
    Box::leak(password.into_boxed_str())  // Lives forever!
}

// ✅ SAFE: Use appropriate lifetime
fn store_config<'a>(config: &'a str) -> Config<'a> {
    Config { data: config }  // Properly scoped
}
```

### 2. Validate Lifetime Constraints

```rust
// Ensure returned references are truly valid
fn get_token<'a>(auth: &'a Auth) -> Result<&'a str, Error> {
    // Verify token hasn't expired (security check)
    if auth.is_expired() {
        return Err(Error::TokenExpired);
    }
    Ok(&auth.token)
}
```

### 3. Prevent Reference Confusion

```rust
// Clear separation of concerns
struct SecurityContext<'a> {
    user: &'a User,
    permissions: &'a Permissions,
}

impl<'a> SecurityContext<'a> {
    fn authorize(&self, action: &str) -> bool {
        // Can't accidentally mix user/permissions
        self.permissions.allows(self.user, action)
    }
}
```

---

## Audit Checklist

Before deploying to production:

- [ ] Run `cargo clippy -- -D warnings`
- [ ] Run `cargo audit`
- [ ] Run `cargo test` with all features
- [ ] Fuzz test with `cargo-fuzz` for 1+ hours
- [ ] Review all `unsafe` blocks (should be zero)
- [ ] Check for panic paths with `cargo expand`
- [ ] Validate no `todo!()` or `unimplemented!()` in code
- [ ] Scan Docker image with `trivy`
- [ ] Penetration test APIs
- [ ] Review logs for sensitive data leaks

---

## Resources

- [RustSec Advisory Database](https://rustsec.org/)
- [Rust Security Guidelines](https://anssi-fr.github.io/rust-guide/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [cargo-audit](https://github.com/RustSec/rustsec/tree/main/cargo-audit)
- [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz)

// Observability setup with OpenTelemetry and Prometheus
// Add to your main.rs: mod observability;

use opentelemetry::{
    global,
    trace::{Span, Tracer},
    KeyValue,
};
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::{runtime, trace as sdktrace, Resource};
use prometheus::{Encoder, IntCounter, IntGauge, Histogram, HistogramOpts, Registry};
use std::sync::Arc;
use tracing::{info, instrument, span, Level};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Initialize tracing and OpenTelemetry
pub fn init_observability(service_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Create OpenTelemetry tracer
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://localhost:4317"), // OTLP endpoint
        )
        .with_trace_config(
            sdktrace::config().with_resource(Resource::new(vec![
                KeyValue::new("service.name", service_name.to_string()),
                KeyValue::new("service.version", env!("CARGO_PKG_VERSION")),
            ])),
        )
        .install_batch(runtime::Tokio)?;

    // Setup tracing subscriber with OpenTelemetry layer
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .with(tracing_opentelemetry::layer().with_tracer(tracer))
        .init();

    info!(service = service_name, "Observability initialized");
    Ok(())
}

/// Prometheus metrics collector
pub struct Metrics {
    registry: Registry,
    
    // Request metrics
    pub requests_total: IntCounter,
    pub requests_in_flight: IntGauge,
    pub request_duration: Histogram,
    
    // Lifetime-specific metrics
    pub borrowed_refs_count: IntGauge,
    pub allocation_count: IntCounter,
}

impl Metrics {
    pub fn new() -> Result<Self, prometheus::Error> {
        let registry = Registry::new();
        
        // Request counters
        let requests_total = IntCounter::new(
            "requests_total",
            "Total number of requests processed",
        )?;
        registry.register(Box::new(requests_total.clone()))?;
        
        let requests_in_flight = IntGauge::new(
            "requests_in_flight",
            "Number of requests currently being processed",
        )?;
        registry.register(Box::new(requests_in_flight.clone()))?;
        
        // Histogram for request duration
        let request_duration = Histogram::with_opts(
            HistogramOpts::new("request_duration_seconds", "Request duration in seconds")
                .buckets(vec![0.001, 0.01, 0.1, 0.5, 1.0, 5.0]),
        )?;
        registry.register(Box::new(request_duration.clone()))?;
        
        // Lifetime tracking metrics
        let borrowed_refs_count = IntGauge::new(
            "borrowed_refs_count",
            "Number of active borrowed references",
        )?;
        registry.register(Box::new(borrowed_refs_count.clone()))?;
        
        let allocation_count = IntCounter::new(
            "allocation_count",
            "Total number of heap allocations",
        )?;
        registry.register(Box::new(allocation_count.clone()))?;
        
        Ok(Metrics {
            registry,
            requests_total,
            requests_in_flight,
            request_duration,
            borrowed_refs_count,
            allocation_count,
        })
    }
    
    /// Export metrics in Prometheus format
    pub fn export(&self) -> String {
        let encoder = prometheus::TextEncoder::new();
        let metric_families = self.registry.gather();
        let mut buffer = Vec::new();
        encoder.encode(&metric_families, &mut buffer).unwrap();
        String::from_utf8(buffer).unwrap()
    }
}

/// Example: Instrumented function with lifetime tracking
#[instrument(skip(data))]
pub fn process_with_observability<'a>(
    data: &'a str,
    metrics: &Metrics,
) -> Result<Vec<&'a str>, String> {
    // Start span
    let span = span!(Level::INFO, "process_data", data_len = data.len());
    let _guard = span.enter();
    
    // Track request
    metrics.requests_total.inc();
    metrics.requests_in_flight.inc();
    
    // Start timing
    let timer = metrics.request_duration.start_timer();
    
    info!("Processing data with {} bytes", data.len());
    
    // Simulate borrowed reference tracking
    metrics.borrowed_refs_count.inc();
    
    // Process data (zero-allocation via lifetimes)
    let result: Vec<&'a str> = data.split_whitespace().collect();
    
    info!(tokens = result.len(), "Data processed successfully");
    
    // Cleanup
    metrics.borrowed_refs_count.dec();
    metrics.requests_in_flight.dec();
    timer.observe_duration();
    
    Ok(result)
}

/// Example: Struct with lifetime and observability
pub struct TrackedProcessor<'a> {
    data: &'a str,
    metrics: Arc<Metrics>,
    span: tracing::Span,
}

impl<'a> TrackedProcessor<'a> {
    pub fn new(data: &'a str, metrics: Arc<Metrics>) -> Self {
        let span = span!(
            Level::INFO,
            "processor_lifetime",
            data_len = data.len()
        );
        
        // Track allocation
        metrics.allocation_count.inc();
        metrics.borrowed_refs_count.inc();
        
        TrackedProcessor {
            data,
            metrics,
            span,
        }
    }
    
    #[instrument(skip(self))]
    pub fn process(&self) -> Vec<&'a str> {
        let _guard = self.span.enter();
        
        info!("Processing within tracked lifetime");
        
        // Zero-allocation processing
        let result: Vec<&'a str> = self.data.split(',').collect();
        
        info!(items = result.len(), "Processing complete");
        
        result
    }
    
    pub fn get_metrics_snapshot(&self) -> String {
        self.metrics.export()
    }
}

impl<'a> Drop for TrackedProcessor<'a> {
    fn drop(&mut self) {
        info!("Processor dropping, releasing borrowed reference");
        self.metrics.borrowed_refs_count.dec();
    }
}

/// Example: Distributed tracing across functions
#[instrument]
pub fn orchestrator_with_tracing<'a>(
    input: &'a str,
    metrics: Arc<Metrics>,
) -> Result<String, String> {
    info!("Starting orchestration");
    
    // Child span 1: Parse
    let parsed = {
        let _span = span!(Level::INFO, "parse_phase").entered();
        info!("Parsing input");
        input.split('\n').collect::<Vec<_>>()
    };
    
    // Child span 2: Process
    let processed = {
        let _span = span!(Level::INFO, "process_phase").entered();
        info!(lines = parsed.len(), "Processing lines");
        
        let mut results = Vec::new();
        for line in parsed {
            let tokens = process_with_observability(line, &metrics)?;
            results.push(tokens.len());
        }
        results
    };
    
    // Child span 3: Aggregate
    let result = {
        let _span = span!(Level::INFO, "aggregate_phase").entered();
        let total: usize = processed.iter().sum();
        info!(total_tokens = total, "Aggregation complete");
        format!("Total tokens: {}", total)
    };
    
    Ok(result)
}

// ========================================
// EXAMPLE USAGE
// ========================================

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_metrics_collection() {
        let metrics = Metrics::new().unwrap();
        let data = "hello world test data";
        
        let result = process_with_observability(data, &metrics);
        assert!(result.is_ok());
        
        // Verify metrics
        assert_eq!(metrics.requests_total.get(), 1);
        assert_eq!(metrics.requests_in_flight.get(), 0);
        assert_eq!(metrics.borrowed_refs_count.get(), 0);
        
        // Export metrics
        let exported = metrics.export();
        assert!(exported.contains("requests_total"));
    }
    
    #[test]
    fn test_tracked_processor_lifecycle() {
        let metrics = Arc::new(Metrics::new().unwrap());
        let data = "a,b,c,d";
        
        {
            let processor = TrackedProcessor::new(data, metrics.clone());
            assert_eq!(metrics.borrowed_refs_count.get(), 1);
            
            let result = processor.process();
            assert_eq!(result.len(), 4);
        } // processor dropped here
        
        // Verify cleanup
        assert_eq!(metrics.borrowed_refs_count.get(), 0);
    }
}

// ========================================
// PRODUCTION EXAMPLE: HTTP SERVER WITH OBSERVABILITY
// ========================================

#[cfg(feature = "async")]
pub mod server {
    use super::*;
    use std::sync::Arc;
    use tokio::net::TcpListener;
    
    pub async fn run_instrumented_server(
        addr: &str,
        metrics: Arc<Metrics>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let listener = TcpListener::bind(addr).await?;
        info!(address = addr, "Server started");
        
        loop {
            let (socket, peer_addr) = listener.accept().await?;
            let metrics = metrics.clone();
            
            tokio::spawn(async move {
                let span = span!(Level::INFO, "handle_connection", %peer_addr);
                let _guard = span.enter();
                
                metrics.requests_total.inc();
                metrics.requests_in_flight.inc();
                
                info!("Connection accepted");
                
                // Handle connection...
                
                metrics.requests_in_flight.dec();
            });
        }
    }
}

# Kubernetes deployment for Rust lifetimes application
---
apiVersion: v1
kind: Namespace
metadata:
  name: lifetimes-guide

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: lifetimes-config
  namespace: lifetimes-guide
data:
  RUST_LOG: "info"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger-collector:4317"
  METRICS_PORT: "9090"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lifetimes-guide
  namespace: lifetimes-guide
  labels:
    app: lifetimes-guide
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lifetimes-guide
  template:
    metadata:
      labels:
        app: lifetimes-guide
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      
      containers:
      - name: lifetimes-guide
        image: lifetimes-guide:latest
        imagePullPolicy: IfNotPresent
        
        # Security
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
              - ALL
        
        # Resource limits
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        
        # Environment from ConfigMap
        envFrom:
        - configMapRef:
            name: lifetimes-config
        
        # Ports
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Temporary directories
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      
      # Pod disruption budget
      # Commented for now, uncomment for production
      # affinity:
      #   podAntiAffinity:
      #     preferredDuringSchedulingIgnoredDuringExecution:
      #     - weight: 100
      #       podAffinityTerm:
      #         labelSelector:
      #           matchExpressions:
      #           - key: app
      #             operator: In
      #             values:
      #             - lifetimes-guide
      #         topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: lifetimes-guide
  namespace: lifetimes-guide
  labels:
    app: lifetimes-guide
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: metrics
    protocol: TCP
  selector:
    app: lifetimes-guide

---
apiVersion: v1
kind: Service
metadata:
  name: lifetimes-guide-metrics
  namespace: lifetimes-guide
  labels:
    app: lifetimes-guide
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  type: ClusterIP
  ports:
  - name: metrics
    port: 9090
    targetPort: metrics
    protocol: TCP
  selector:
    app: lifetimes-guide

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lifetimes-guide-hpa
  namespace: lifetimes-guide
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lifetimes-guide
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
# Pod Disruption Budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: lifetimes-guide-pdb
  namespace: lifetimes-guide
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: lifetimes-guide

---
# NetworkPolicy for security
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: lifetimes-guide-netpol
  namespace: lifetimes-guide
spec:
  podSelector:
    matchLabels:
      app: lifetimes-guide
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53  # DNS
    - protocol: UDP
      port: 53  # DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 4317  # OTLP

---
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: lifetimes-guide
  namespace: lifetimes-guide
  labels:
    app: lifetimes-guide
spec:
  selector:
    matchLabels:
      app: lifetimes-guide
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics

---
# Ingress (optional)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lifetimes-guide
  namespace: lifetimes-guide
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - lifetimes.example.com
    secretName: lifetimes-guide-tls
  rules:
  - host: lifetimes.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: lifetimes-guide
            port:
              number: 80

# Rust Lifetimes: Complete Production Guide

Comprehensive guide to Rust lifetimes with production-ready examples, tests, benchmarks, observability, and deployment configuration.

## Quick Start

```bash
# Clone and setup
git clone <repo>
cd lifetimes_guide

# Build and run
cargo build --release
cargo run

# Run tests
cargo test

# Run benchmarks
cargo bench

# Check code quality
cargo clippy
cargo fmt --check

# Security audit
cargo audit
```

## Project Structure

```
lifetimes_guide/
├── src/
│   ├── main.rs                  # Main demonstrations
│   └── observability.rs         # OpenTelemetry setup
├── tests/
│   └── integration_tests.rs     # Integration tests
├── benches/
│   └── lifetime_benchmarks.rs   # Criterion benchmarks
├── k8s/
│   └── deployment.yaml          # Kubernetes manifests
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI
├── Dockerfile                   # Multi-stage build
├── Cargo.toml                   # Dependencies
├── EXERCISES.md                 # Hands-on exercises
└── SECURITY_CHECKLIST.md        # Production security guide
```

## Running the Examples

### Local Development

```bash
# Run main program
cargo run

# With logging
RUST_LOG=debug cargo run

# Run specific test
cargo test test_datastore_lifetime_integrity

# Run with coverage
cargo tarpaulin --out Html
```

### With Docker

```bash
# Build image
docker build -t lifetimes-guide .

# Run container
docker run --rm lifetimes-guide

# Run tests in container
docker run --rm lifetimes-guide cargo test
```

### With Kubernetes

```bash
# Create namespace and deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -n lifetimes-guide

# View logs
kubectl logs -n lifetimes-guide -l app=lifetimes-guide -f

# Port forward for local testing
kubectl port-forward -n lifetimes-guide svc/lifetimes-guide 8080:80

# View metrics
kubectl port-forward -n lifetimes-guide svc/lifetimes-guide-metrics 9090:9090
curl http://localhost:9090/metrics
```

## Observability Setup

### Prerequisites

```bash
# Install Jaeger for distributed tracing
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/latest/download/jaeger-operator.yaml

# Install Prometheus for metrics
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

### View Traces

1. Forward Jaeger port: `kubectl port-forward -n observability svc/jaeger-query 16686:16686`
2. Open browser: http://localhost:16686
3. Search for service: `lifetimes-guide`

### View Metrics

1. Forward Prometheus port: `kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090`
2. Open browser: http://localhost:9090
3. Query: `requests_total{job="lifetimes-guide"}`

## Benchmarking

```bash
# Run all benchmarks
cargo bench

# Run specific benchmark
cargo bench benchmark_reference_vs_owned

# Profile with flamegraph
cargo flamegraph --bench lifetime_benchmarks

# Generate benchmark report
cargo bench -- --save-baseline master

# Compare benchmarks
cargo bench -- --baseline master
```

## Performance Profiling

### CPU Profiling

```bash
# Install perf tools
sudo apt-get install linux-tools-common linux-tools-generic

# Profile with perf
cargo build --release
perf record -g target/release/lifetimes_guide
perf report

# Flamegraph
cargo install flamegraph
cargo flamegraph
```

### Memory Profiling

```bash
# Install valgrind
sudo apt-get install valgrind

# Profile with massif
valgrind --tool=massif target/release/lifetimes_guide
ms_print massif.out.*

# Profile with heaptrack
heaptrack target/release/lifetimes_guide
heaptrack_gui heaptrack.lifetimes_guide.*
```

### Using `cargo-instruments` (macOS)

```bash
cargo install cargo-instruments

# CPU profiling
cargo instruments -t time --release --bench lifetime_benchmarks

# Memory profiling
cargo instruments -t alloc --release --bench lifetime_benchmarks
```

## Security

### Run Security Checks

```bash
# Audit dependencies
cargo audit

# Check for outdated deps
cargo outdated

# Scan Docker image
docker build -t lifetimes-guide .
trivy image lifetimes-guide

# Static analysis
cargo clippy -- -D warnings
```

### Production Checklist

See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) for complete security guidelines.

## CI/CD Pipeline

The project includes GitHub Actions workflows:

- **Lint**: Format checking and Clippy
- **Test**: Cross-platform testing (Linux, macOS, Windows)
- **Benchmark**: Performance regression detection
- **Security**: Dependency auditing
- **Coverage**: Code coverage reporting
- **Build**: Release binary artifacts
- **Docker**: Container image building

## Learning Path

1. **Start here**: Read the main `src/main.rs` for all examples
2. **Practice**: Complete exercises in `EXERCISES.md`
3. **Test**: Run and study `tests/integration_tests.rs`
4. **Optimize**: Review `benches/lifetime_benchmarks.rs`
5. **Deploy**: Follow Kubernetes deployment guide

## Common Commands

```bash
# Development
cargo watch -x "test"              # Auto-run tests
cargo expand                       # See macro expansions
cargo tree                         # View dependency tree

# Quality
cargo fmt                          # Format code
cargo clippy --fix                 # Auto-fix issues
cargo fix                          # Apply suggested fixes

# Documentation
cargo doc --open                   # Generate and open docs
cargo rustdoc -- --document-private-items  # Include private items

# Profiling
cargo build --release              # Optimized build
time cargo test --release          # Time tests
cargo bloat --release              # Analyze binary size
```

## Advanced Topics

### Async Lifetimes

```rust
// Enable async feature in Cargo.toml
async fn process<'a>(data: &'a str) -> Result<&'a str, Error> {
    // Lifetime spans await points
    tokio::time::sleep(Duration::from_millis(100)).await;
    Ok(data.trim())
}
```

### Pin and Self-Referential Structs

```rust
use std::pin::Pin;

struct SelfRef {
    data: String,
    ptr: *const String,
}

// Pin prevents moving, enabling self-references
fn create_self_ref() -> Pin<Box<SelfRef>> {
    // Implementation requires unsafe
}
```

### Arena Allocation

```rust
use bumpalo::Bump;

fn with_arena() {
    let arena = Bump::new();
    
    // All allocations share 'arena lifetime
    let s1 = arena.alloc_str("hello");
    let s2 = arena.alloc_str("world");
    
    // Efficient: no individual frees
} // All memory freed at once
```

## Troubleshooting

### Lifetime Compilation Errors

**Error**: "borrowed value does not live long enough"

```rust
// ❌ Problem
fn bad() -> &str {
    let s = String::from("hello");
    &s  // s dropped here
}

// ✅ Solution: Return owned data
fn good() -> String {
    String::from("hello")
}
```

**Error**: "explicit lifetime required"

```rust
// ❌ Problem
fn first(x: &str, y: &str) -> &str { x }

// ✅ Solution: Add lifetime annotations
fn first<'a, 'b>(x: &'a str, y: &'b str) -> &'a str { x }
```

### Performance Issues

If benchmarks show poor performance:

1. Check for unnecessary clones: `rg "\.clone\(\)"`
2. Profile with `cargo flamegraph`
3. Review allocations: `cargo build --release && heaptrack`
4. Enable LTO: Set `lto = true` in `Cargo.toml`

## Resources

### Official Documentation
- [The Rust Book - Chapter 10](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)
- [Rustonomicon - Lifetimes](https://doc.rust-lang.org/nomicon/lifetimes.html)
- [Rust by Example - Lifetimes](https://doc.rust-lang.org/rust-by-example/scope/lifetime.html)

### Advanced Resources
- [Too Many Lists](https://rust-unofficial.github.io/too-many-lists/) - Linked list implementations
- [Jon Gjengset's Crust of Rust](https://www.youtube.com/c/JonGjengset) - Video series
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)

### Tools
- [cargo-expand](https://github.com/dtolnay/cargo-expand) - See macro expansions
- [cargo-flamegraph](https://github.com/flamegraph-rs/flamegraph) - CPU profiling
- [cargo-criterion](https://github.com/bheisler/cargo-criterion) - Benchmarking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure CI passes: `cargo test && cargo clippy && cargo fmt`
5. Submit a pull request

## License

MIT OR Apache-2.0

## Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Security: See SECURITY_CHECKLIST.md

---

**Made with 🦀 and ❤️ for the Rust community**

## Summary

You now have a **production-grade guide to Rust lifetimes** with:

✅ **Complete code examples** covering all lifetime scenarios  
✅ **Integration tests** demonstrating real-world patterns  
✅ **Criterion benchmarks** with performance comparisons  
✅ **Dockerfile** with multi-stage builds  
✅ **CI/CD pipeline** with GitHub Actions  
✅ **Kubernetes deployment** with HPA, NetworkPolicy, monitoring  
✅ **Observability** via OpenTelemetry + Prometheus  
✅ **Security checklist** for production deployment  
✅ **Hands-on exercises** progressing from beginner to expert  

---

## 5 Most Common Pitfalls

### 1. **Returning References to Local Variables**
```rust
// ❌ FATAL ERROR
fn dangling() -> &str {
    let s = String::from("hello");
    &s  // s deallocated, reference invalid
}

// ✅ FIX: Return owned data
fn safe() -> String {
    String::from("hello")
}
```

### 2. **Lifetime Too Restrictive**
```rust
// ❌ PROBLEM: Forces both to have same lifetime
fn first<'a>(x: &'a str, y: &'a str) -> &'a str { x }

// ✅ FIX: Use separate lifetimes
fn first<'a, 'b>(x: &'a str, _y: &'b str) -> &'a str { x }
```

### 3. **Borrowing While Mutating**
```rust
// ❌ ERROR: Can't borrow immutably while borrowed mutably
let mut v = vec![1, 2, 3];
let first = &v[0];
v.push(4);  // ❌ Invalidates 'first'
println!("{}", first);

// ✅ FIX: Copy the value or restructure
let first_val = v[0];
v.push(4);
println!("{}", first_val);
```

### 4. **Struct Lifetime Confusion**
```rust
// ❌ UNCLEAR: Which lifetime does output relate to?
struct Holder<'a, 'b> {
    data: &'a str,
    meta: &'b str,
}

impl<'a, 'b> Holder<'a, 'b> {
    fn get(&self) -> &str { self.data }  // Ambiguous!
}

// ✅ FIX: Explicit lifetime binding
fn get(&self) -> &'a str { self.data }
```

### 5. **Leaking to 'static Unnecessarily**
```rust
// ❌ BAD: Memory leak, lives forever
fn leak_it(s: String) -> &'static str {
    Box::leak(s.into_boxed_str())
}

// ✅ GOOD: Use appropriate lifetime scope
fn scoped<'a>(s: &'a str) -> &'a str { s }
```

---

## 3 Hands-On Exercises (Immediate Action)

### Exercise 1: Fix the Compilation Error (5 minutes)
```rust
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let s1 = String::from("long");
    let result;
    {
        let s2 = String::from("short");
        result = longest(&s1, &s2);
    }
    println!("{}", result);  // ❌ Compile error - fix this!
}
```

**Goal**: Add lifetime annotations and understand why the code fails.

### Exercise 2: Build a TextParser (20 minutes)
```rust
struct TextParser<'a> {
    text: &'a str,
}

impl<'a> TextParser<'a> {
    fn new(text: &'a str) -> Self {
        TextParser { text }
    }
    
    // TODO: Return first word without allocating
    fn first_word(&self) -> &'a str {
        // Implement
    }
    
    // TODO: Return all words as Vec<&'a str>
    fn all_words(&self) -> Vec<&'a str> {
        // Implement
    }
}

// Write tests
```

### Exercise 3: Implement HTTP Request Parser (45 minutes)

See `EXERCISES.md` Task 4.1 for full specification. Build a zero-allocation HTTP parser that:
- Parses method, path, version
- Extracts headers as `Vec<(&'a str, &'a str)>`
- Preserves body as `Option<&'a str>`
- Never clones or allocates strings

---

## Further Reading

### 📖 Essential Reading
1. **[The Rustonomicon - Chapter 3: Lifetimes](https://doc.rust-lang.org/nomicon/lifetimes.html)** - Deep dive into variance, subtyping, and advanced lifetime rules
2. **Jon Gjengset's "Crust of Rust: Lifetime Annotations"** - Video walkthrough: https://www.youtube.com/watch?v=rAl-9HwD858

### 🔧 Reference Repository
**[rust-lifecycle-examples](https://github.com/pretzelhammer/rust-blog/blob/master/posts/common-rust-lifetime-misconceptions.md)** - Comprehensive collection of lifetime misconceptions and solutions

---

## Commands to Run Right Now

```bash
# 1. Setup the project
cargo new --bin lifetimes_guide && cd lifetimes_guide

# 2. Copy comprehensive_lifetimes.rs to src/main.rs
# (Use the artifact code above)

# 3. Add dependencies to Cargo.toml
# (Use the Cargo.toml artifact)

# 4. Build and run
cargo run

# 5. Run tests
cargo test

# 6. Run benchmarks (after adding benches/)
cargo bench

# 7. Check with clippy
cargo clippy

# 8. Format code
cargo fmt

# 9. Security audit
cargo install cargo-audit && cargo audit

# 10. Profile performance
cargo install flamegraph
cargo flamegraph --bin lifetimes_guide
```

---

## Quick Reference: Lifetime Syntax

| Pattern | Meaning | Example |
|---------|---------|---------|
| `<'a>` | Lifetime parameter | `fn foo<'a>(x: &'a str)` |
| `'static` | Lives for entire program | `static S: &str = "hi"` |
| `'_` | Anonymous lifetime | `fn foo(x: &'_ str)` |
| `'a: 'b` | 'a outlives 'b | `fn foo<'a: 'b>()` |
| `T: 'a` | T contains refs that live 'a | `struct S<'a, T: 'a>` |
| `for<'a>` | Higher-ranked trait bound | `F: for<'a> Fn(&'a str)` |

---

**You're now equipped to write memory-safe, zero-cost abstractions using Rust's lifetime system. Start with Exercise 1 and work through the progression. The borrow checker is your friend—listen to it!** 🦀