# Rust Intermediate Interview Guide
### Complete, In-Depth Reference for Systems Engineers

---

## Table of Contents

1. [Ownership, Borrowing & Lifetimes — Deep Dive](#1-ownership-borrowing--lifetimes--deep-dive)
2. [The Type System — Generics, Traits, Associated Types](#2-the-type-system--generics-traits-associated-types)
3. [Trait Objects & Dynamic Dispatch vs Static Dispatch](#3-trait-objects--dynamic-dispatch-vs-static-dispatch)
4. [Smart Pointers — Box, Rc, Arc, Cell, RefCell, Mutex, RwLock](#4-smart-pointers--box-rc-arc-cell-refcell-mutex-rwlock)
5. [Closures, Function Pointers & Higher-Order Functions](#5-closures-function-pointers--higher-order-functions)
6. [Iterators — Lazy Evaluation & Iterator Adapters](#6-iterators--lazy-evaluation--iterator-adapters)
7. [Error Handling — Result, Option, Custom Errors, Propagation](#7-error-handling--result-option-custom-errors-propagation)
8. [Concurrency — Threads, Channels, Send/Sync](#8-concurrency--threads-channels-sendsync)
9. [Async/Await & the Executor Model](#9-asyncawait--the-executor-model)
10. [Memory Layout, Unsafe Rust & FFI](#10-memory-layout-unsafe-rust--ffi)
11. [Pattern Matching — Exhaustive, Destructuring, Guards](#11-pattern-matching--exhaustive-destructuring-guards)
12. [Lifetimes — Advanced: Variance, Higher-Ranked Trait Bounds (HRTBs)](#12-lifetimes--advanced-variance-higher-ranked-trait-bounds-hrtbs)
13. [Macros — Declarative (macro_rules!) & Procedural](#13-macros--declarative-macro_rules--procedural)
14. [String Types, Slices & Text Handling](#14-string-types-slices--text-handling)
15. [Collections, Algorithms & Data Structures in Rust](#15-collections-algorithms--data-structures-in-rust)
16. [Module System, Visibility & Crate Architecture](#16-module-system-visibility--crate-architecture)
17. [Testing — Unit, Integration, Fuzzing, Benchmarking](#17-testing--unit-integration-fuzzing-benchmarking)
18. [Performance — Profiling, Optimization, Zero-Cost Abstractions](#18-performance--profiling-optimization-zero-cost-abstractions)
19. [Compiler Internals — MIR, Borrow Checker, LLVM](#19-compiler-internals--mir-borrow-checker-llvm)
20. [Production Patterns — Builder, State Machine, Newtype, Typestate](#20-production-patterns--builder-state-machine-newtype-typestate)

---

## 1. Ownership, Borrowing & Lifetimes — Deep Dive

### Mental Model First

Rust's ownership model is the **compile-time memory safety guarantee**. No GC, no runtime overhead. The borrow checker enforces three invariants at compile time:

```
┌─────────────────────────────────────────────────────────────────┐
│                    OWNERSHIP INVARIANTS                         │
│                                                                 │
│  1. Every value has exactly ONE owner (variable binding)        │
│  2. When the owner goes out of scope, the value is DROPPED      │
│  3. Ownership can be MOVED or BORROWED — never both at once     │
│                                                                 │
│  BORROW RULES (enforced at compile time):                       │
│  ┌─────────────────────────────────────┐                        │
│  │  At any given time, you can have:   │                        │
│  │   EITHER  N shared refs (&T)        │                        │
│  │   OR      1 exclusive ref (&mut T)  │                        │
│  │   NEVER   both simultaneously       │                        │
│  └─────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### Move Semantics vs Copy Semantics

```rust
// MOVE: ownership transferred, original invalidated
let s1 = String::from("hello");
let s2 = s1;           // s1 moved into s2
// println!("{}", s1); // ERROR: value borrowed after move

// COPY: stack-allocated types implement Copy trait
let x: i32 = 5;
let y = x;             // x is copied (i32 is Copy)
println!("{} {}", x, y); // both valid

// Clone: explicit deep copy
let s1 = String::from("hello");
let s2 = s1.clone();   // deep copy — heap data duplicated
println!("{} {}", s1, s2); // both valid
```

**Why does this matter?**  
Types that implement `Copy` are entirely stack-allocated (or primitives). Types that own heap data (`String`, `Vec`, `Box`) cannot be `Copy` — moving them transfers the heap pointer without freeing it twice.

### Memory Layout: Stack vs Heap

```
Stack Frame (function call)          Heap
┌────────────────────────┐          ┌──────────────────────────┐
│  s: String             │          │  h e l l o               │
│  ┌────────────────────┐│          │  ^                        │
│  │ ptr ───────────────┼┼──────────┘                          │
│  │ len: 5             ││                                      │
│  │ cap: 8             ││                                      │
│  └────────────────────┘│          (heap allocation)           │
│                        │                                      │
│  x: i32 = 42           │          (nothing on heap for i32)  │
│  y: bool = true        │                                      │
└────────────────────────┘          └──────────────────────────┘
```

A `String` is 3 words on the stack: pointer, length, capacity. The actual bytes live on the heap.

### Borrowing: Shared vs Exclusive

```rust
fn main() {
    let mut data = vec![1, 2, 3];

    // Shared borrow — multiple allowed simultaneously
    let r1 = &data;
    let r2 = &data;
    println!("{:?} {:?}", r1, r2); // ok

    // Exclusive borrow — only one allowed, no shared borrows active
    let r3 = &mut data;
    r3.push(4);
    // println!("{:?}", r1); // ERROR: r1 still alive, r3 is exclusive
    println!("{:?}", r3);    // ok after r1, r2 are no longer used (NLL)
}
```

**NLL (Non-Lexical Lifetimes):** Since Rust 2018 edition, the borrow checker reasons about the *last use* of a borrow, not its lexical scope. This allows borrows to end earlier than their enclosing block.

### Lifetime Annotations

Lifetimes are about *relating* the lifetime of references. They do not change how long things live — they describe existing relationships to the compiler.

```rust
// Without annotation — compiler cannot infer which input lifetime
// the output reference is tied to
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// The output reference lives at most as long as the SHORTER of x, y
fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xy");
        result = longest(s1.as_str(), s2.as_str());
        println!("{}", result); // ok — result used within s2's scope
    }
    // println!("{}", result); // ERROR: s2 dropped, result could dangle
}
```

### Lifetime Elision Rules

The compiler applies three rules to infer lifetimes without explicit annotations:

```
Rule 1: Each reference parameter gets its own lifetime parameter
        fn foo(x: &str, y: &str)  →  fn foo<'a,'b>(x: &'a str, y: &'b str)

Rule 2: If exactly ONE input lifetime, it's assigned to all outputs
        fn foo(x: &str) -> &str  →  fn foo<'a>(x: &'a str) -> &'a str

Rule 3: If one input is &self or &mut self, its lifetime is assigned to output
        fn foo(&self, x: &str) -> &str  →  output gets self's lifetime
```

If none of these rules resolve the lifetimes, the compiler errors.

### Lifetime in Structs

```rust
// Struct holds a reference — must be explicit about lifetime
struct Parser<'a> {
    input: &'a str,  // Parser cannot outlive the str it references
    pos: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Parser { input, pos: 0 }
    }

    fn peek(&self) -> Option<char> {
        self.input[self.pos..].chars().next()
    }

    // Returns a slice of the original input — lifetime tied to 'a, not self
    fn consume_while<F: Fn(char) -> bool>(&mut self, pred: F) -> &'a str {
        let start = self.pos;
        while let Some(c) = self.peek() {
            if pred(c) { self.pos += c.len_utf8(); }
            else { break; }
        }
        &self.input[start..self.pos]
    }
}
```

---

## 2. The Type System — Generics, Traits, Associated Types

### Generics and Monomorphization

Rust generics are **zero-cost** via monomorphization: the compiler generates specialized code for every concrete type used.

```rust
// Generic function
fn max<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

// Compiler generates (conceptually):
// fn max_i32(a: i32, b: i32) -> i32 { ... }
// fn max_f64(a: f64, b: f64) -> f64 { ... }
// No runtime dispatch — fully inlined/optimized
```

**Cost:** Binary size grows. For deeply generic systems code with many instantiations, compile times increase and binary can bloat. Tradeoff vs dynamic dispatch.

### Traits: Defining Behavior

A trait is an interface + optional default implementations.

```rust
trait Serialize {
    fn serialize(&self) -> Vec<u8>;

    // Default method — can be overridden
    fn serialize_to_string(&self) -> String {
        String::from_utf8(self.serialize())
            .unwrap_or_else(|_| "<invalid utf8>".to_string())
    }
}

trait Deserialize: Sized {
    type Error;
    fn deserialize(bytes: &[u8]) -> Result<Self, Self::Error>;
}

// Implementing for a type
#[derive(Debug)]
struct Point { x: f64, y: f64 }

impl Serialize for Point {
    fn serialize(&self) -> Vec<u8> {
        format!("{},{}", self.x, self.y).into_bytes()
    }
}
```

### Associated Types vs Generic Parameters

This is a critical distinction for designing clean APIs.

```rust
// Generic parameter — caller chooses Item each time
trait Container<T> {
    fn get(&self, idx: usize) -> Option<&T>;
}
// Can implement: impl Container<i32> for Foo AND impl Container<String> for Foo

// Associated type — implementor fixes Item ONCE
trait Iterator {
    type Item;  // implementor decides
    fn next(&mut self) -> Option<Self::Item>;
}
// Can only implement once per type — impl Iterator for Foo { type Item = u8; }
```

**Rule of thumb:** Use associated types when there's a logical one-to-one relationship between the implementing type and the output type. Use generic parameters when the same type should be able to implement the trait for multiple type parameters.

### Trait Bounds — Where Clauses

```rust
// Inline bound (simple cases)
fn print_all<T: Display + Debug>(items: &[T]) { ... }

// Where clause (complex cases — preferred for readability)
fn process<K, V, E>(map: &HashMap<K, V>) -> Result<Vec<V>, E>
where
    K: Hash + Eq + Debug,
    V: Clone + Serialize,
    E: From<SerializeError>,
{
    ...
}

// Bounds on associated types
fn sum_items<I>(iter: I) -> I::Item
where
    I: Iterator,
    I::Item: std::ops::Add<Output = I::Item> + Default,
{
    iter.fold(I::Item::default(), |acc, x| acc + x)
}
```

### Object Safety

A trait is **object-safe** if it can be used as `dyn Trait`. Rules:

```
Object-safe trait requirements:
┌─────────────────────────────────────────────────────────────┐
│  1. No methods returning Self                                │
│  2. No methods with generic type parameters                 │
│  3. No associated constants (in practice)                   │
│  4. All methods must be dispatchable through a vtable       │
└─────────────────────────────────────────────────────────────┘

NOT object-safe:
  trait Clone { fn clone(&self) -> Self; }  // returns Self
  trait Foo { fn bar<T>(&self, t: T); }     // generic method

Object-safe:
  trait Draw { fn draw(&self); }
  trait Serialize { fn serialize(&self) -> Vec<u8>; }
```

```rust
// Making a non-object-safe trait usable as object via wrapper
trait Animal: AnimalClone {
    fn name(&self) -> &str;
}

trait AnimalClone {
    fn clone_box(&self) -> Box<dyn Animal>;
}

impl<T: Animal + Clone + 'static> AnimalClone for T {
    fn clone_box(&self) -> Box<dyn Animal> {
        Box::new(self.clone())
    }
}
```

---

## 3. Trait Objects & Dynamic Dispatch vs Static Dispatch

### The Two Dispatch Models

```
STATIC DISPATCH (monomorphization)               DYNAMIC DISPATCH (vtable)
─────────────────────────────────               ──────────────────────────

  fn draw<T: Shape>(s: &T)                         fn draw(s: &dyn Shape)
         │                                                  │
         ▼ (compiler)                                       ▼ (runtime)
  fn draw_circle(s: &Circle) ◄─ Circle      ┌──────── fat pointer ────────┐
  fn draw_rect(s: &Rect)     ◄─ Rect        │  data ptr │  vtable ptr     │
                                             └─────┬─────┴──────┬──────────┘
  Binary: N copies                                 │             │
  Call: direct (inlineable)                        ▼             ▼
  Heterogeneous collections: NO            heap data       ┌─────────────┐
                                                           │ type_id     │
                                                           │ drop fn     │
                                                           │ size/align  │
                                                           │ draw fn ptr │
                                                           └─────────────┘

  Binary: 1 copy
  Call: indirect via function pointer (NOT inlineable)
  Heterogeneous collections: YES  Vec<Box<dyn Shape>>
```

### When to Use Each

```rust
// Static dispatch — zero-cost, prefer when:
//   - Type is known at compile time
//   - You want inlining/optimization
//   - Performance-critical hot path
fn process<W: Write>(writer: &mut W, data: &[u8]) -> io::Result<()> {
    writer.write_all(data)
}

// Dynamic dispatch — runtime flexibility, prefer when:
//   - Heterogeneous collections needed
//   - Plugin/extension architecture
//   - Binary size matters more than perf
//   - Return type must be erased
fn make_logger(cfg: &Config) -> Box<dyn Log> {
    match cfg.log_target {
        Target::File => Box::new(FileLogger::new(&cfg.path)),
        Target::Stderr => Box::new(StderrLogger::new()),
        Target::Syslog => Box::new(SyslogLogger::new()),
    }
}
```

### impl Trait — The Middle Ground

`impl Trait` in return position is static dispatch with type erasure (RPIT — Return Position impl Trait):

```rust
// Caller gets ONE concrete type, doesn't need to know which
// No vtable, no allocation — compiler knows the concrete type
fn make_adder(x: i32) -> impl Fn(i32) -> i32 {
    move |y| x + y  // closure type is anonymous, but it IS a concrete type
}

// In argument position — syntactic sugar for generic parameter
fn apply(f: impl Fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}
// equivalent to:
fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}
```

---

## 4. Smart Pointers — Box, Rc, Arc, Cell, RefCell, Mutex, RwLock

### The Full Smart Pointer Taxonomy

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SMART POINTER DECISION TREE                       │
│                                                                      │
│  Single owner?  ──YES──► Box<T>        (heap alloc, unique owner)   │
│       │                                                              │
│       NO                                                             │
│       │                                                              │
│  Single-threaded?                                                    │
│       │                                                              │
│    YES─►  Shared ownership?                                          │
│           ├─ YES ─► Rc<T>             (reference counted, !Send)    │
│           └─ Need mutation?                                          │
│                 └─► RefCell<T>        (runtime borrow check, !Send) │
│                     (use with Rc<RefCell<T>> for shared mutation)    │
│       │                                                              │
│    NO (multi-threaded)                                               │
│       ├─ Shared ownership ─► Arc<T>   (atomic ref count, Send+Sync) │
│       └─ Need mutation?                                              │
│               ├─ Exclusive ─► Mutex<T>   (lock, one writer)         │
│               └─ Read-heavy ─► RwLock<T> (many readers, one writer) │
│                                                                      │
│  Interior mutability (single field) ─► Cell<T>  (Copy types only)   │
│  UnsafeCell<T>  ─► foundation of all interior mutability            │
└──────────────────────────────────────────────────────────────────────┘
```

### Box<T>

```rust
// Use Box when:
// 1. Recursive types (DSTs require pointer)
// 2. Trait objects (dyn Trait must be behind pointer)
// 3. Large data you want heap-allocated to avoid stack overflow
// 4. Transferring ownership without copying

#[derive(Debug)]
enum List<T> {
    Cons(T, Box<List<T>>),  // without Box: infinite size!
    Nil,
}

let list = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));

// Box deref-coerces: *box gives T
let b: Box<i32> = Box::new(42);
let x: i32 = *b;  // Deref<Target = i32>
```

**Memory:** `Box<T>` is a single pointer on the stack. Dropping it calls `drop(T)` then `dealloc`.

### Rc<T> and Weak<T>

```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

// Shared ownership — counted with usize (not atomic — !Send)
let a = Rc::new(5);
let b = Rc::clone(&a);  // increments ref count
println!("count = {}", Rc::strong_count(&a)); // 2

// Weak<T> — does NOT keep alive, breaks reference cycles
struct Node {
    value: i32,
    children: Vec<Rc<RefCell<Node>>>,
    parent: Option<Weak<RefCell<Node>>>,  // weak to avoid cycle
}

// Upgrading weak reference — returns Option<Rc<T>>
if let Some(parent) = node.parent.as_ref().and_then(|w| w.upgrade()) {
    println!("parent value: {}", parent.borrow().value);
}
```

### Arc<T> — Atomic Reference Counting

```rust
use std::sync::Arc;
use std::thread;

let data = Arc::new(vec![1, 2, 3]);

let handles: Vec<_> = (0..4).map(|i| {
    let data = Arc::clone(&data);
    thread::spawn(move || {
        println!("thread {}: {:?}", i, data);
    })
}).collect();

for h in handles { h.join().unwrap(); }
// Arc uses atomic operations — safe across threads, small overhead vs Rc
```

### Cell<T> and RefCell<T> — Interior Mutability

Interior mutability lets you mutate data through shared references. This **moves borrow checking to runtime**.

```rust
use std::cell::{Cell, RefCell};

// Cell<T> — for Copy types, no borrow, just get/set
struct Counter {
    count: Cell<u32>,
}
impl Counter {
    fn increment(&self) {  // takes &self, not &mut self!
        self.count.set(self.count.get() + 1);
    }
}

// RefCell<T> — runtime borrow checking, panics on violation
let data = RefCell::new(vec![1, 2, 3]);

{
    let r1 = data.borrow();      // runtime shared borrow
    let r2 = data.borrow();      // ok — multiple shared
    println!("{:?} {:?}", r1, r2);
}   // borrows released here

{
    let mut w = data.borrow_mut();   // runtime exclusive borrow
    w.push(4);
    // let r = data.borrow();       // PANIC at runtime: already mutably borrowed
}

// try_borrow / try_borrow_mut return Result instead of panicking
match data.try_borrow_mut() {
    Ok(mut v) => v.push(5),
    Err(e) => eprintln!("borrow failed: {}", e),
}
```

### Mutex<T> and RwLock<T>

```rust
use std::sync::{Arc, Mutex, RwLock};
use std::thread;

// Mutex<T> — mutual exclusion, one thread at a time
let counter = Arc::new(Mutex::new(0u64));

let handles: Vec<_> = (0..8).map(|_| {
    let counter = Arc::clone(&counter);
    thread::spawn(move || {
        let mut lock = counter.lock().unwrap();
        *lock += 1;
        // MutexGuard drops here — releases lock
    })
}).collect();

for h in handles { h.join().unwrap(); }
println!("final: {}", counter.lock().unwrap());

// RwLock<T> — multiple readers OR one writer
let cache = Arc::new(RwLock::new(std::collections::HashMap::<String, String>::new()));

// Many concurrent readers:
let r = cache.read().unwrap();
let _ = r.get("key");
drop(r);

// Exclusive write:
let mut w = cache.write().unwrap();
w.insert("key".to_string(), "value".to_string());
```

**Poisoning:** If a thread panics while holding a `Mutex` lock, the mutex is "poisoned." `lock()` returns `Err(PoisonError)`. Use `.unwrap()` only if you accept panic on poisoned mutex, or handle with `.unwrap_or_else(|e| e.into_inner())`.

---

## 5. Closures, Function Pointers & Higher-Order Functions

### Closure Traits: Fn, FnMut, FnOnce

```
┌─────────────────────────────────────────────────────────────┐
│                   CLOSURE TRAIT HIERARCHY                   │
│                                                             │
│   FnOnce ◄─── FnMut ◄─── Fn                               │
│   (can call  (can call    (can call                         │
│    once)      multiple,    multiple,                        │
│               with &mut)   with &)                          │
│                                                             │
│   Captured by MOVE + consumed:  FnOnce                      │
│   Captured by &mut:             FnMut                       │
│   Captured by &:                Fn                          │
└─────────────────────────────────────────────────────────────┘
```

```rust
// FnOnce — consumes captured variable, can call ONCE
let s = String::from("hello");
let consume = move || drop(s);  // s moved into closure
consume();
// consume();  // ERROR: cannot call FnOnce twice

// FnMut — mutates captured variable
let mut count = 0;
let mut increment = || { count += 1; count };  // captures &mut count
println!("{}", increment()); // 1
println!("{}", increment()); // 2

// Fn — only reads captured variable
let base = 10;
let add = |x| base + x;    // captures &base
println!("{}", add(5));     // 15
println!("{}", add(3));     // 13

// Returning closures — must be boxed or impl Fn
fn make_multiplier(factor: i32) -> impl Fn(i32) -> i32 {
    move |x| x * factor
}

fn make_boxed_fn(flag: bool) -> Box<dyn Fn(i32) -> i32> {
    if flag {
        Box::new(|x| x * 2)
    } else {
        Box::new(|x| x + 1)
    }
}
```

### Function Pointers vs Closures

```rust
// fn pointer — no captured state, coercible from non-capturing closures
fn double(x: i32) -> i32 { x * 2 }

let f: fn(i32) -> i32 = double;
let g: fn(i32) -> i32 = |x| x * 2;  // non-capturing closure → fn ptr
// let h: fn(i32) -> i32 = |x| x * factor; // ERROR: captures, cannot be fn ptr

// Function pointers are useful in FFI and C-compatible callbacks
extern "C" fn my_callback(x: i32) -> i32 { x }
```

### Practical Higher-Order Patterns

```rust
// Composing transformations — idiomatic Rust pipeline
fn process_events(events: Vec<Event>) -> Vec<ProcessedEvent> {
    events
        .into_iter()
        .filter(|e| e.priority > 3)
        .filter_map(|e| e.parse().ok())
        .map(|e| e.enrich())
        .collect()
}

// Generic HOF — strategy pattern via closure
fn retry<F, T, E>(mut f: F, attempts: usize) -> Result<T, E>
where
    F: FnMut() -> Result<T, E>,
{
    let mut last_err = None;
    for _ in 0..attempts {
        match f() {
            Ok(v) => return Ok(v),
            Err(e) => last_err = Some(e),
        }
    }
    Err(last_err.unwrap())
}
```

---

## 6. Iterators — Lazy Evaluation & Iterator Adapters

### The Iterator Trait

```rust
pub trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;

    // All adapters are provided default implementations built on next()
    // map, filter, flat_map, take, skip, enumerate, zip, chain, etc.
}
```

Iterators are **lazy** — no computation happens until consumed (by `collect()`, `for`, `fold()`, `sum()`, etc.).

### Implementing a Custom Iterator

```rust
struct Fibonacci {
    a: u64,
    b: u64,
}

impl Fibonacci {
    fn new() -> Self {
        Fibonacci { a: 0, b: 1 }
    }
}

impl Iterator for Fibonacci {
    type Item = u64;

    fn next(&mut self) -> Option<u64> {
        let result = self.a;
        let next = self.a + self.b;
        self.a = self.b;
        self.b = next;
        Some(result)  // infinite iterator — always Some
    }
}

// Usage
let first_ten: Vec<u64> = Fibonacci::new().take(10).collect();
let sum_of_evens: u64 = Fibonacci::new()
    .take(20)
    .filter(|n| n % 2 == 0)
    .sum();
```

### Iterator Adapter Deep Dive

```rust
// flat_map — iterator of iterables flattened
let words = vec!["hello world", "foo bar baz"];
let chars: Vec<&str> = words.iter()
    .flat_map(|s| s.split_whitespace())
    .collect();

// scan — like fold but yields intermediate state
let running_sum: Vec<i32> = (1..=5)
    .scan(0, |acc, x| { *acc += x; Some(*acc) })
    .collect();  // [1, 3, 6, 10, 15]

// zip — pair up two iterators
let keys = vec!["a", "b", "c"];
let vals = vec![1, 2, 3];
let pairs: Vec<(&&str, &i32)> = keys.iter().zip(vals.iter()).collect();

// chain — concatenate iterators
let all: Vec<i32> = (1..=3).chain(7..=9).collect(); // [1,2,3,7,8,9]

// peekable — look ahead without consuming
let mut iter = vec![1, 2, 3].into_iter().peekable();
if iter.peek() == Some(&1) {
    println!("starts with 1: {}", iter.next().unwrap());
}

// windows / chunks on slices
let data = [1u8, 2, 3, 4, 5];
for window in data.windows(3) {
    println!("{:?}", window); // [1,2,3], [2,3,4], [3,4,5]
}
for chunk in data.chunks(2) {
    println!("{:?}", chunk);  // [1,2], [3,4], [5]
}
```

### IntoIterator, FromIterator

```rust
// IntoIterator — types that can produce an iterator
// Automatically used by for loops:
// for x in collection  ≡  for x in IntoIterator::into_iter(collection)

// Three forms:
for x in vec![1,2,3]       {}  // into_iter, consumes
for x in &vec![1,2,3]      {}  // iter(), borrows (&T)
for x in &mut vec![1,2,3]  {}  // iter_mut(), mutable borrow (&mut T)

// FromIterator — build a collection from an iterator
// Used by .collect()
let doubled: Vec<i32> = (1..=5).map(|x| x * 2).collect();
let set: HashSet<i32> = vec![1,2,2,3,3].into_iter().collect();
let result: Result<Vec<i32>, _> = vec![Ok(1), Ok(2), Err("bad")].into_iter().collect();
// collect on Result<Vec> — short-circuits on first Err
```

---

## 7. Error Handling — Result, Option, Custom Errors, Propagation

### The Result and Option Type Anatomy

```rust
// Standard library definitions
enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

### The ? Operator

`?` is syntactic sugar that either unwraps `Ok`/`Some`, or returns the `Err`/`None` from the current function after applying `From::from` for error conversion.

```rust
// Desugars from:
let val = some_result?;

// To (approximately):
let val = match some_result {
    Ok(v) => v,
    Err(e) => return Err(From::from(e)),
};
```

### Custom Error Types

```rust
use std::fmt;

// Manual implementation — maximum control
#[derive(Debug)]
pub enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    Custom(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Io(e) => write!(f, "IO error: {}", e),
            AppError::Parse(e) => write!(f, "Parse error: {}", e),
            AppError::Custom(msg) => write!(f, "Error: {}", msg),
        }
    }
}

impl std::error::Error for AppError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            AppError::Io(e) => Some(e),
            AppError::Parse(e) => Some(e),
            AppError::Custom(_) => None,
        }
    }
}

// From implementations enable ? operator conversion
impl From<std::io::Error> for AppError {
    fn from(e: std::io::Error) -> Self { AppError::Io(e) }
}
impl From<std::num::ParseIntError> for AppError {
    fn from(e: std::num::ParseIntError) -> Self { AppError::Parse(e) }
}

// Usage — ? automatically converts via From
fn load_config(path: &str) -> Result<Config, AppError> {
    let content = std::fs::read_to_string(path)?;   // io::Error → AppError::Io
    let port: u16 = content.trim().parse()?;          // ParseIntError → AppError::Parse
    Ok(Config { port })
}
```

### Using thiserror (production-grade)

```rust
// Cargo.toml: thiserror = "1"
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ServiceError {
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("configuration invalid: {field} — {reason}")]
    Config { field: String, reason: String },

    #[error("resource not found: {0}")]
    NotFound(String),

    #[error(transparent)]    // delegates Display and source to inner error
    Unexpected(#[from] anyhow::Error),
}
```

### Using anyhow (application-level, quick error wrapping)

```rust
// Cargo.toml: anyhow = "1"
use anyhow::{anyhow, bail, Context, Result};

fn read_config(path: &str) -> Result<Config> {  // anyhow::Result = Result<T, anyhow::Error>
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read config file: {}", path))?;

    let config: Config = serde_json::from_str(&content)
        .context("failed to parse config JSON")?;

    if config.port == 0 {
        bail!("port cannot be zero");  // shorthand for return Err(anyhow!(...))
    }

    Ok(config)
}
```

**thiserror vs anyhow decision:**
- `thiserror`: library crates — typed errors, callers can pattern-match
- `anyhow`: application/binary crates — convenience, rich context, no type matching needed

---

## 8. Concurrency — Threads, Channels, Send/Sync

### Send and Sync — The Marker Traits

These are the foundation of Rust's fearless concurrency:

```
┌─────────────────────────────────────────────────────────────┐
│  Send: safe to TRANSFER ownership to another thread         │
│  Sync: safe to ACCESS from multiple threads simultaneously  │
│         (T: Sync  ↔  &T: Send)                              │
│                                                             │
│  Auto-implemented by compiler based on fields:              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Type          │ Send  │ Sync │ Reason             │       │
│  ├───────────────┼───────┼──────┼────────────────────┤       │
│  │ i32, f64, etc │  ✓   │  ✓   │ primitive          │       │
│  │ String, Vec   │  ✓   │  ✓   │ owned data         │       │
│  │ Arc<T>        │  ✓   │  ✓   │ if T: Send+Sync    │       │
│  │ Rc<T>         │  ✗   │  ✗   │ non-atomic count   │       │
│  │ RefCell<T>    │  ✓   │  ✗   │ runtime borrows    │       │
│  │ Mutex<T>      │  ✓   │  ✓   │ if T: Send         │       │
│  │ *mut T        │  ✗   │  ✗   │ raw pointer        │       │
│  │ MutexGuard    │  ✗   │  ✓   │ not movable        │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Threads and move Closures

```rust
use std::thread;
use std::time::Duration;

// thread::spawn requires closure to be Send + 'static
// 'static because thread can outlive the calling scope
let data = vec![1, 2, 3];
let handle = thread::spawn(move || {  // 'move' required to transfer ownership
    println!("{:?}", data);
    42  // thread::JoinHandle<i32>
});

let result = handle.join().unwrap();  // blocks until thread finishes, returns i32
println!("thread returned: {}", result);

// Scoped threads (std::thread::scope) — can borrow from enclosing scope
let numbers = vec![1, 2, 3, 4, 5];
thread::scope(|s| {
    for chunk in numbers.chunks(2) {
        s.spawn(|| {  // chunk borrow is valid — scope ensures join before return
            println!("{:?}", chunk);
        });
    }
}); // all spawned threads joined here
```

### Channels — mpsc

```rust
use std::sync::mpsc;  // Multiple Producer, Single Consumer

// Synchronous (bounded) vs Asynchronous (unbounded)
let (tx, rx) = mpsc::channel();          // unbounded
let (tx, rx) = mpsc::sync_channel(100); // bounded — sender blocks when full

// Multiple producers via clone
let tx2 = tx.clone();

thread::spawn(move || {
    tx.send("from thread 1").unwrap();
});
thread::spawn(move || {
    tx2.send("from thread 2").unwrap();
});

// Drain all messages
for msg in rx {  // rx implements Iterator — exits when all senders dropped
    println!("{}", msg);
}

// Non-blocking receive
match rx.try_recv() {
    Ok(msg) => println!("got: {}", msg),
    Err(mpsc::TryRecvError::Empty) => println!("no message yet"),
    Err(mpsc::TryRecvError::Disconnected) => println!("sender gone"),
}
```

### Crossbeam — Production Channel

```rust
// Cargo.toml: crossbeam = "0.8"
use crossbeam::channel;

// Select over multiple channels — like Go's select
let (s1, r1) = channel::bounded(10);
let (s2, r2) = channel::bounded(10);

channel::select! {
    recv(r1) -> msg => println!("r1: {:?}", msg),
    recv(r2) -> msg => println!("r2: {:?}", msg),
    default(Duration::from_millis(100)) => println!("timeout"),
}

// Work-stealing deque, barriers, epoch-based reclamation in crossbeam
```

### Atomic Operations

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};
use std::sync::Arc;

let counter = Arc::new(AtomicU64::new(0));
let stop = Arc::new(AtomicBool::new(false));

// Ordering semantics — CRITICAL for correctness
// Relaxed: no ordering guarantees (counters, metrics)
counter.fetch_add(1, Ordering::Relaxed);

// Release/Acquire: establishes happens-before
// Writer uses Release, reader uses Acquire
stop.store(true, Ordering::Release);
if stop.load(Ordering::Acquire) { /* see all writes before the Release */ }

// SeqCst: total global order (strongest, most expensive)
// AcqRel: both acquire and release in one (for RMW operations)

// Compare-and-swap — lock-free primitive
let old = counter.compare_exchange(
    0,                  // expected
    1,                  // new
    Ordering::AcqRel,  // success ordering
    Ordering::Acquire,  // failure ordering
);
```

---

## 9. Async/Await & the Executor Model

### The Mental Model: Futures are State Machines

```
SYNCHRONOUS:                     ASYNC:
                                 
fn read() -> Bytes {             async fn read() -> Bytes {
    // blocks thread                 // yields control, resumes later
    syscall_read()               }
}                                
                                 Future<Output = Bytes>
Thread blocked:                  
┌─────────────────────┐         Thread can do other work:
│ Thread              │         ┌─────────────────────────┐
│ [BLOCKED on I/O]    │         │ Thread / Executor        │
│                     │         │ ┌──────┐ ┌──────┐ ┌─────┐│
│ (wasting resources) │         │ │task A│ │task B│ │... ││
└─────────────────────┘         │ └──────┘ └──────┘ └─────┘│
                                │ (cooperative multitasking) │
                                └─────────────────────────────┘
```

### The Future Trait

```rust
use std::task::{Context, Poll};
use std::pin::Pin;

pub trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

pub enum Poll<T> {
    Ready(T),    // computation complete
    Pending,     // not ready, executor will re-poll when Waker fires
}
```

The executor calls `poll()`. If `Pending`, the future registers a `Waker` — when the resource is ready (I/O complete, timer fired), the waker notifies the executor to re-poll.

### async/await Desugaring

```rust
// What you write:
async fn fetch(url: &str) -> Result<String, Error> {
    let response = http_get(url).await?;
    let body = response.text().await?;
    Ok(body)
}

// What the compiler generates (conceptually):
// An anonymous struct (state machine) that implements Future
// Each .await point becomes a state
enum FetchStateMachine<'a> {
    State0 { url: &'a str },                    // before first await
    State1 { future: HttpGetFuture },           // waiting on http_get
    State2 { future: TextFuture, ... },         // waiting on .text()
    Done,
}
impl<'a> Future for FetchStateMachine<'a> {
    type Output = Result<String, Error>;
    fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<Self::Output> {
        loop {
            match self.get_mut() {
                State0 { url } => {
                    let fut = http_get(url);
                    *self = State1 { future: fut };
                }
                State1 { future } => {
                    match Pin::new(future).poll(cx) {
                        Poll::Pending => return Poll::Pending,
                        Poll::Ready(resp) => { *self = State2 { future: resp.text(), ... }; }
                    }
                }
                // ...
            }
        }
    }
}
```

### Executor Architecture (Tokio)

```
┌──────────────────────────────────────────────────────────────────┐
│                        TOKIO RUNTIME                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Worker Threads (N = CPU cores)        │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │
│  │  │  Worker 0  │  │  Worker 1  │  │  Worker N  │        │    │
│  │  │ Local Queue│  │ Local Queue│  │ Local Queue│        │    │
│  │  │  [task][..]│  │  [task][..]│  │  [task][..]│        │    │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │    │
│  │         │  work-steal ◄──┘               │               │    │
│  │         └────────────────────────────────┘               │    │
│  │                          │                               │    │
│  │              Global Queue (overflow)                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────┐    ┌─────────────────────────────────┐    │
│  │  I/O Driver      │    │  Timer Driver                   │    │
│  │  (epoll/kqueue/  │    │  (time-wheel, sleep, interval)  │    │
│  │   io_uring)      │    │                                 │    │
│  │  Waker registry  │    │  Fires wakers on expiry         │    │
│  └──────────────────┘    └─────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Practical Async Patterns

```rust
use tokio::time::{sleep, timeout, Duration};
use tokio::sync::{mpsc, Semaphore};

// Concurrent futures — join vs select
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // join! — wait for ALL, run concurrently
    let (r1, r2) = tokio::join!(fetch("url1"), fetch("url2"));

    // select! — take the FIRST to complete
    tokio::select! {
        res = fetch("primary")  => handle(res),
        res = fetch("fallback") => handle(res),
        _ = sleep(Duration::from_secs(5)) => eprintln!("timeout"),
    }

    // Spawn independent task — detached
    let handle = tokio::spawn(async move {
        heavy_work().await
    });
    let result = handle.await?;  // JoinHandle<T>

    // Bounded concurrency — rate limiting
    let sem = Arc::new(Semaphore::new(10));  // max 10 concurrent
    let tasks: Vec<_> = urls.iter().map(|url| {
        let sem = sem.clone();
        let url = url.clone();
        tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap();
            fetch(&url).await
        })
    }).collect();

    for task in tasks {
        task.await??;
    }

    Ok(())
}
```

### Pin and Unpin

```
Why Pin?
Futures contain self-referential structs (state machine with pointers to own fields).
If the future is moved in memory, those pointers dangle.
Pin<P> guarantees the pointee will NOT move.

┌──────────────────────────────────────────────────────────┐
│  Future state machine in memory:                         │
│                                                          │
│  ┌─────────────────────────────────────┐                 │
│  │ MyFuture {                          │                 │
│  │   data: [1, 2, 3],                  │◄────┐           │
│  │   slice: &data[1..],  ─────────────────────┘           │
│  │   state: Waiting,                   │                 │
│  │ }                                   │                 │
│  └─────────────────────────────────────┘                 │
│                                                          │
│  If moved: slice pointer dangles! Pin prevents the move. │
└──────────────────────────────────────────────────────────┘
```

```rust
use std::pin::Pin;

// Most types are Unpin — moving is fine, Pin<&mut T> acts like &mut T
// Self-referential types implement !Unpin

// Box::pin — heap-pin a future
let pinned: Pin<Box<dyn Future<Output = i32>>> = Box::pin(async { 42 });

// pin_mut! macro from futures crate — stack-pin
use futures::pin_mut;
async fn example() {
    let fut = some_future();
    pin_mut!(fut);  // now fut: Pin<&mut impl Future>
    fut.await
}
```

---

## 10. Memory Layout, Unsafe Rust & FFI

### Rust Memory Layout Rules

```
Default: compiler may reorder fields for optimal alignment

Struct layout:
┌──────────────────────────────────────────────────────────┐
│  struct Foo { a: u8, b: u32, c: u16 }                   │
│                                                          │
│  Rust layout (may reorder):                              │
│  ┌──┬──────┬────┬────────┐                              │
│  │b │b │b │b│ c │ c │ a  │ (+ 1 byte padding)          │
│  └──┴──────┴────┴────────┘                              │
│   0   1   2   3   4   5   6   (7 bytes, padded to 8)   │
│                                                          │
│  C layout (#[repr(C)]): field order preserved            │
│  ┌───┬───┬───┬─────────────┬──────┐                     │
│  │ a │pad│pad│pad│  b (u32)│ c(u16│pad│              │  │
│  └───┴───┴───┴─────────────┴──────┘                     │
│   0   1   2   3   4   5   6   7   8   9 (10 bytes)      │
└──────────────────────────────────────────────────────────┘

#[repr(C)]     — C-compatible, field order preserved
#[repr(packed)] — no padding, unaligned access (unsafe to take refs!)
#[repr(transparent)] — single-field struct, same layout as inner type
#[repr(u8)]    — for enums, discriminant is u8
#[repr(align(N))] — force alignment to N bytes
```

```rust
// Checking sizes and offsets
use std::mem;

#[repr(C)]
struct Header {
    magic: u32,
    version: u8,
    flags: u8,
    length: u16,
}

println!("size: {}", mem::size_of::<Header>());   // 8
println!("align: {}", mem::align_of::<Header>());  // 4
println!("offset of length: {}", memoffset::offset_of!(Header, length)); // 6
```

### Unsafe Rust — What It Unlocks

```rust
// unsafe enables 5 capabilities (and ONLY these):
// 1. Dereference raw pointers
// 2. Call unsafe functions/methods
// 3. Access/modify mutable static variables
// 4. Implement unsafe traits
// 5. Access fields of unions

unsafe fn dangerous() {
    let raw: *mut i32 = &mut 42 as *mut i32;
    *raw = 100;  // dereference raw pointer
}

// Safe abstraction over unsafe code — the idiom
pub fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
    let len = slice.len();
    let ptr = slice.as_mut_ptr();
    assert!(mid <= len);
    unsafe {
        // SAFETY: mid <= len, two non-overlapping slices of valid memory
        (
            std::slice::from_raw_parts_mut(ptr, mid),
            std::slice::from_raw_parts_mut(ptr.add(mid), len - mid),
        )
    }
}
```

### FFI — Calling C from Rust

```rust
// Declare C function signatures
extern "C" {
    fn abs(x: i32) -> i32;
    fn strlen(s: *const std::os::raw::c_char) -> usize;
    fn malloc(size: usize) -> *mut std::os::raw::c_void;
    fn free(ptr: *mut std::os::raw::c_void);
}

fn safe_strlen(s: &std::ffi::CStr) -> usize {
    unsafe { strlen(s.as_ptr()) }
}

// Expose Rust to C
#[no_mangle]  // prevent name mangling
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

// CString / CStr for string interop
use std::ffi::{CString, CStr};
use std::os::raw::c_char;

pub fn call_c_with_string(input: &str) {
    let c_string = CString::new(input).expect("CString::new failed"); // null-terminated
    unsafe {
        some_c_function(c_string.as_ptr());
    }
}

pub unsafe fn read_c_string(ptr: *const c_char) -> String {
    CStr::from_ptr(ptr).to_string_lossy().into_owned()
}
```

### Raw Pointers and Provenance

```rust
// *const T — immutable raw pointer
// *mut T   — mutable raw pointer
// Neither enforces aliasing or lifetime!

// Creating raw pointers — safe
let mut x = 5;
let raw = &x as *const i32;
let raw_mut = &mut x as *mut i32;

// Dereferencing — unsafe
unsafe {
    println!("{}", *raw);
    *raw_mut = 10;
}

// Pointer arithmetic — unsafe, must stay within valid allocation
let arr = [1i32, 2, 3, 4, 5];
let ptr = arr.as_ptr();
unsafe {
    let third = *ptr.add(2);  // ptr.add(2) = ptr + 2*sizeof(i32)
    println!("{}", third);    // 3
}
```

---

## 11. Pattern Matching — Exhaustive, Destructuring, Guards

### Exhaustive Matching — The Power of enum

```rust
#[derive(Debug)]
enum Command {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(u8, u8, u8),
}

fn process(cmd: Command) {
    match cmd {
        Command::Quit => std::process::exit(0),
        Command::Move { x, y } => println!("move to {},{}", x, y),
        Command::Write(msg) => println!("write: {}", msg),
        Command::ChangeColor(r, g, b) => println!("color: {},{},{}", r, g, b),
        // Compiler error if any variant missing — exhaustiveness guaranteed
    }
}
```

### Pattern Varieties

```rust
// Literal patterns
match x {
    0 => println!("zero"),
    1 | 2 | 3 => println!("small"),  // OR patterns
    4..=9 => println!("medium"),      // range (inclusive)
    _ => println!("large"),           // wildcard
}

// Destructuring structs
struct Point { x: f64, y: f64 }
let p = Point { x: 3.0, y: 4.0 };
let Point { x, y } = p;  // field shorthand
let Point { x: px, y: py } = p;  // rename

// Destructuring tuples and enums
let (a, b, c) = (1, "hello", 3.14);
if let Some(value) = optional { /* use value */ }

// Nested patterns
let nested = Some(Some(42));
if let Some(Some(x)) = nested {
    println!("{}", x);
}

// Guard conditions
let pair = (2, -3);
match pair {
    (x, y) if x == y => println!("equal"),
    (x, y) if x + y == 0 => println!("sum zero"),
    (x, _) if x > 0 => println!("positive first"),
    _ => println!("other"),
}

// Binding with @
match num {
    n @ 1..=9 => println!("single digit: {}", n),
    n @ 10..=99 => println!("double digit: {}", n),
    _ => println!("large"),
}

// Slice patterns
match slice {
    [] => println!("empty"),
    [x] => println!("one: {}", x),
    [first, .., last] => println!("first={}, last={}", first, last),
    [a, b, rest @ ..] => println!("a={}, b={}, rest={:?}", a, b, rest),
}
```

### let-else and matches!

```rust
// let-else (Rust 1.65+) — early return on pattern mismatch
fn parse_config(input: &str) -> Option<Config> {
    let Some(port_str) = input.split(':').nth(1) else {
        return None;  // diverge (return, break, panic, etc.)
    };
    let Ok(port) = port_str.parse::<u16>() else {
        return None;
    };
    Some(Config { port })
}

// matches! macro — pattern as boolean
let is_ready = matches!(state, State::Ready | State::Running);
let has_error = matches!(result, Err(e) if e.is_fatal());
```

---

## 12. Lifetimes — Advanced: Variance, Higher-Ranked Trait Bounds (HRTBs)

### Variance Explained

Variance determines how subtyping relationships of generic parameters relate to subtyping of the containing type. In Rust, this applies to lifetimes.

```
'long is a subtype of 'short  (longer lifetime is more specific)

Variance of T in Foo<T>:
┌───────────────────────────────────────────────────────────────┐
│  COVARIANT:     Foo<'long>  can be used as  Foo<'short>       │
│                 &'a T is covariant in 'a                      │
│                 (can shorten the lifetime)                    │
│                                                               │
│  CONTRAVARIANT: Foo<'short> can be used as  Foo<'long>        │
│                 fn(&'a T) is contravariant in 'a             │
│                 (function that takes shorter lives longer)    │
│                                                               │
│  INVARIANT:     No subtyping in either direction              │
│                 &'a mut T is invariant in T                   │
│                 (cannot change T through mutable ref)         │
└───────────────────────────────────────────────────────────────┘
```

```rust
// Covariant example — &'long T can be used where &'short T needed
fn covariant<'short, 'long: 'short>(x: &'long str) -> &'short str {
    x  // ok — 'long outlives 'short, covariant in 'a
}

// Invariance example — &mut T is invariant in T
fn invariant_demo<'a>(v: &mut Vec<&'a str>, s: &'a str) {
    v.push(s);
    // If Vec<&'a str> were covariant in 'a, you could push short-lived refs
    // into a Vec expecting long-lived ones — invariance prevents this
}
```

### PhantomData — Expressing Ownership for the Borrow Checker

```rust
use std::marker::PhantomData;

// Slice pointer with lifetime — without PhantomData the borrow checker
// doesn't know we "own" data of type T with lifetime 'a
struct Slice<'a, T: 'a> {
    ptr: *const T,
    len: usize,
    _marker: PhantomData<&'a T>,  // tells compiler: acts like &'a T
}

// Variance and Send/Sync implications of PhantomData:
// PhantomData<T>       — covariant in T, owns T for drop purposes
// PhantomData<*mut T>  — invariant in T, !Send, !Sync
// PhantomData<fn() -> T> — covariant in T (return position)
// PhantomData<fn(T)>   — contravariant in T (argument position)
```

### Higher-Ranked Trait Bounds (HRTBs)

HRTBs express "for any lifetime 'a, this bound holds."

```rust
// Ordinary bound — lifetime must be concrete/known
fn takes_fn_with_lifetime<'a, F>(f: F, s: &'a str)
where
    F: Fn(&'a str) -> &'a str,
{
    println!("{}", f(s));
}
// Problem: F is tied to one specific lifetime 'a

// HRTB — F must work for ANY lifetime
fn takes_any_str_fn<F>(f: F, s: &str)
where
    F: for<'a> Fn(&'a str) -> &'a str,  // "for<'a>" = for any 'a
{
    println!("{}", f(s));
}
// F is not tied to a specific lifetime — far more flexible

// Practical HRTB: closure traits
// Fn(&str) desugars to for<'a> Fn(&'a str)
// This is why you can pass closures taking borrowed args to generic functions

// HRTB with trait objects
trait Parser {
    fn parse<'a>(&self, input: &'a str) -> (&'a str, &'a str);
}

// Box<dyn for<'a> Fn(&'a str) -> &'a str>  — works for any input lifetime
```

---

## 13. Macros — Declarative (macro_rules!) & Procedural

### Declarative Macros (macro_rules!)

Pattern matching on token trees.

```rust
// Simple macro
macro_rules! say_hello {
    () => { println!("Hello!"); };
    ($name:expr) => { println!("Hello, {}!", $name); };
}

say_hello!();         // Hello!
say_hello!("Alice");  // Hello, Alice!

// Repetition — * (zero or more), + (one or more)
macro_rules! vec_of_strings {
    ($($x:expr),* $(,)?) => {  // $(,)? = optional trailing comma
        vec![$($x.to_string()),*]
    };
}
let v = vec_of_strings!["hello", "world"];

// Macro metavariable types:
// expr    — any expression
// ident   — identifier (variable name, function name)
// ty      — type
// pat     — pattern
// stmt    — statement
// block   — block { ... }
// item    — item (fn, struct, impl, ...)
// tt      — single token tree
// literal — literal value
// meta    — attribute contents
// path    — path (a::b::c)
// vis     — visibility qualifier

// More complex: implement a simple HashMap literal
macro_rules! map {
    ($($key:expr => $val:expr),* $(,)?) => {{
        let mut m = std::collections::HashMap::new();
        $(m.insert($key, $val);)*
        m
    }};
}
let m = map!{"a" => 1, "b" => 2, "c" => 3};
```

### Procedural Macros

Three kinds: custom derive, attribute macros, function-like macros.

```rust
// Custom derive — the most common
// In a separate crate (proc-macro = true in Cargo.toml):

use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyDebug)]
pub fn my_debug_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl std::fmt::Debug for #name {
            fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                write!(f, stringify!(#name))
            }
        }
    };
    TokenStream::from(expanded)
}

// Usage in another crate:
// #[derive(MyDebug)]
// struct Foo;

// Attribute macro — transform any item
#[proc_macro_attribute]
pub fn retry(attr: TokenStream, item: TokenStream) -> TokenStream {
    // Parse attr for retry count, item is the function
    // Return modified function with retry logic wrapped
    todo!()
}

// Function-like macro — called like a function
#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    // Parse SQL string at compile time, validate, return type-safe query
    todo!()
}
```

---

## 14. String Types, Slices & Text Handling

### String Type Hierarchy

```
┌──────────────────────────────────────────────────────────────────┐
│                      RUST STRING TYPES                           │
│                                                                  │
│  str          — UTF-8 string slice, unsized, always behind ptr   │
│  &str         — borrowed string slice (ptr + len), !owned        │
│  String       — owned, heap-allocated, growable UTF-8            │
│                                                                  │
│  OsStr        — OS string slice (platform encoding)              │
│  OsString     — owned OS string                                  │
│                                                                  │
│  Path         — OS path slice (thin wrapper over OsStr)          │
│  PathBuf      — owned path                                       │
│                                                                  │
│  CStr         — null-terminated C string slice                   │
│  CString      — owned null-terminated C string                   │
│                                                                  │
│  Relationship: String : &str  ==  Vec<u8> : &[u8]               │
│                (owned)  (borrowed slice)                         │
└──────────────────────────────────────────────────────────────────┘
```

```rust
// str vs String
let s1: &str = "hello";           // string literal — 'static lifetime, in binary
let s2: String = String::from("hello");  // heap allocated
let s3: &str = &s2;               // borrow String as &str — deref coercion

// Deref coercion chain: String → &String → &str
// This is why fn takes_str(s: &str) accepts both &str and &String

// Conversions
let owned: String = s1.to_string();        // &str → String
let owned: String = s1.to_owned();         // &str → String
let slice: &str = &s2;                     // String → &str
let bytes: Vec<u8> = s2.into_bytes();      // String → Vec<u8> (no copy)
let from_bytes = String::from_utf8(bytes); // Vec<u8> → Result<String>

// String operations
let mut s = String::new();
s.push_str("hello");
s.push(' ');
s += "world";                // uses Add<&str>

// Slicing — must be on char boundaries!
let hello = &s[0..5];       // ok — 'h','e','l','l','o' are all 1 byte
// &"héllo"[0..2]           // PANIC: 'é' is 2 bytes, byte 2 is mid-char

// Safe slicing
let chars: Vec<char> = "héllo".chars().collect();
let first_two: String = "héllo".chars().take(2).collect();
```

---

## 15. Collections, Algorithms & Data Structures in Rust

### Standard Collections

```
Collection         │ Use case                            │ Key complexity
───────────────────┼─────────────────────────────────────┼──────────────
Vec<T>             │ Growable array, cache-friendly       │ O(1) push, O(n) insert
VecDeque<T>        │ Double-ended queue                   │ O(1) push/pop front&back
LinkedList<T>      │ Rarely needed in Rust                │ O(1) insert if you have iter
HashMap<K,V>       │ Hash table (random order)            │ O(1) avg get/insert
BTreeMap<K,V>      │ Sorted by key, range queries         │ O(log n) get/insert
HashSet<T>         │ Unique elements (hash)               │ O(1) contains
BTreeSet<T>        │ Sorted unique elements               │ O(log n) contains
BinaryHeap<T>      │ Priority queue (max-heap by default) │ O(log n) push/pop
```

```rust
use std::collections::{HashMap, BTreeMap, BinaryHeap, VecDeque};
use std::cmp::Reverse;

// HashMap — Entry API for conditional insert
let mut scores: HashMap<String, Vec<i32>> = HashMap::new();
scores.entry("Alice".to_string())
    .or_insert_with(Vec::new)
    .push(42);

// or_default, or_insert, and_modify
scores.entry("Bob".to_string())
    .and_modify(|v| v.push(1))
    .or_insert_with(|| vec![0]);

// BinaryHeap — min-heap via Reverse
let mut min_heap = BinaryHeap::new();
min_heap.push(Reverse(5));
min_heap.push(Reverse(1));
min_heap.push(Reverse(3));
while let Some(Reverse(val)) = min_heap.pop() {
    print!("{} ", val);  // 1 3 5
}

// VecDeque — efficient sliding window
let mut window: VecDeque<i32> = VecDeque::with_capacity(3);
for x in 0..10 {
    if window.len() == 3 { window.pop_front(); }
    window.push_back(x);
}
```

### Implementing Common Data Structures

```rust
// Lock-free stack using AtomicPtr (simplified)
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Stack<T> {
    head: AtomicPtr<Node<T>>,
}

struct Node<T> {
    val: T,
    next: *mut Node<T>,
}

impl<T> Stack<T> {
    fn new() -> Self {
        Stack { head: AtomicPtr::new(ptr::null_mut()) }
    }

    fn push(&self, val: T) {
        let node = Box::into_raw(Box::new(Node {
            val,
            next: ptr::null_mut(),
        }));
        loop {
            let head = self.head.load(Ordering::Acquire);
            unsafe { (*node).next = head; }
            match self.head.compare_exchange(
                head, node, Ordering::Release, Ordering::Relaxed
            ) {
                Ok(_) => return,
                Err(_) => continue,  // retry
            }
        }
    }
}
```

---

## 16. Module System, Visibility & Crate Architecture

### Module and Visibility Rules

```
Visibility modifiers:
  pub            — visible everywhere
  pub(crate)     — visible within the crate
  pub(super)     — visible to parent module
  pub(in path)   — visible within path
  (nothing)      — private to current module
```

```rust
// src/lib.rs
pub mod network {
    pub mod http {
        pub struct Request {
            pub method: String,
            pub(crate) raw_bytes: Vec<u8>,  // crate-internal
            url: String,                     // private
        }

        impl Request {
            pub fn new(method: &str, url: &str) -> Self { ... }
            fn parse_internal(&self) -> ... { ... }  // private
        }

        pub(super) fn internal_helper() { ... }  // only network module sees this
    }

    // Can use http::internal_helper here
    pub use http::Request;  // re-export — ergonomic public API
}

// Workspace and crate structure:
// ┌─ Cargo.toml (workspace)
// ├─ my-api/       (binary crate)
// ├─ my-core/      (library crate)
// ├─ my-proto/     (library crate)
// └─ my-crypto/    (library crate)
```

### Cargo Features and Conditional Compilation

```toml
# Cargo.toml
[features]
default = ["std"]
std = []
metrics = ["prometheus"]
tls = ["rustls", "tokio-rustls"]
full = ["metrics", "tls"]

[dependencies]
prometheus = { version = "0.13", optional = true }
rustls = { version = "0.21", optional = true }
```

```rust
// Conditional compilation based on features
#[cfg(feature = "metrics")]
mod metrics {
    pub fn record_latency(ms: u64) { ... }
}

#[cfg(not(feature = "std"))]
mod no_std_impl { ... }

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
fn linux_specific() { ... }

#[cfg(test)]
mod tests { ... }  // only compiled during testing
```

---

## 17. Testing — Unit, Integration, Fuzzing, Benchmarking

### Unit Tests

```rust
// In src/lib.rs or any module file — compiled only with --test
#[cfg(test)]
mod tests {
    use super::*;  // import from parent module

    #[test]
    fn test_add() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    #[should_panic(expected = "divide by zero")]
    fn test_panic() {
        divide(1, 0);
    }

    #[test]
    fn test_result() -> Result<(), Box<dyn std::error::Error>> {
        let val = parse_value("42")?;
        assert_eq!(val, 42);
        Ok(())
    }

    // Property-based testing with proptest
    use proptest::prelude::*;
    proptest! {
        #[test]
        fn test_reverse_reverse(s in "\\PC*") {  // any string
            let double_reversed: String = s.chars().rev().collect::<String>()
                .chars().rev().collect();
            prop_assert_eq!(s, double_reversed);
        }
    }
}
```

### Integration Tests

```
src/
  lib.rs
tests/              ← integration tests, each file is its own crate
  integration_test.rs
  helpers/
    mod.rs
```

```rust
// tests/integration_test.rs
use my_crate::Config;

#[test]
fn test_full_flow() {
    let config = Config::from_str("port=8080").unwrap();
    assert_eq!(config.port, 8080);
}
```

### Fuzzing with cargo-fuzz

```bash
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add my_parser
```

```rust
// fuzz/fuzz_targets/my_parser.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        // Parser must never panic on arbitrary input
        let _ = my_crate::parse(s);
    }
});
```

```bash
cargo fuzz run my_parser -- -max_total_time=60
```

### Benchmarking with criterion

```rust
// benches/my_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn bench_parse(c: &mut Criterion) {
    let inputs = vec!["short", "a medium length string", "a much longer string that exercises more code"];

    let mut group = c.benchmark_group("parse");
    for input in &inputs {
        group.bench_with_input(
            BenchmarkId::from_parameter(input.len()),
            input,
            |b, i| b.iter(|| my_crate::parse(black_box(i)))
        );
    }
    group.finish();
}

criterion_group!(benches, bench_parse);
criterion_main!(benches);
```

```bash
cargo bench
# Results in target/criterion/report/ — HTML with statistical analysis
```

### Test Utilities: mockall, wiremock

```rust
// cargo add mockall
use mockall::{automock, predicate::*};

#[automock]
trait Database {
    fn get_user(&self, id: u64) -> Option<User>;
    fn save_user(&mut self, user: &User) -> Result<(), DbError>;
}

#[test]
fn test_with_mock_db() {
    let mut mock_db = MockDatabase::new();
    mock_db.expect_get_user()
        .with(eq(42u64))
        .times(1)
        .returning(|_| Some(User { id: 42, name: "Alice".into() }));

    let service = UserService::new(mock_db);
    let user = service.get_user(42).unwrap();
    assert_eq!(user.name, "Alice");
}
```

---

## 18. Performance — Profiling, Optimization, Zero-Cost Abstractions

### Zero-Cost Abstractions

The Rust promise: abstractions compile to the same code as hand-written low-level code. Verified via:

```bash
# Inspect generated assembly
cargo install cargo-asm
cargo asm my_crate::my_function

# Or via godbolt.org — paste Rust, see x86-64 output
```

```rust
// Iterator chains compile to tight loops — no allocations
fn sum_squares(data: &[f64]) -> f64 {
    data.iter().map(|x| x * x).sum()
    // Compiles to a single loop: for i in 0..len { acc += data[i] * data[i] }
    // The compiler also auto-vectorizes with SIMD if target supports it
}

// Newtype is zero-cost
struct Meters(f64);
struct Kilograms(f64);
// At runtime: identical to f64. At compile time: type-checked.
```

### Profiling Tools

```bash
# Linux perf
cargo build --release
perf record --call-graph=dwarf ./target/release/my_binary
perf report

# Flamegraph
cargo install flamegraph
cargo flamegraph

# Valgrind / cachegrind (cache analysis)
valgrind --tool=cachegrind ./target/release/my_binary
cg_annotate cachegrind.out.*

# Heap profiling — heaptrack
heaptrack ./target/release/my_binary
heaptrack_gui heaptrack.my_binary.*.gz
```

### Key Optimization Patterns

```rust
// 1. Avoid unnecessary allocations
// BAD:
fn process_names(names: &[&str]) -> Vec<String> {
    names.iter().map(|s| s.to_uppercase()).collect()
}
// BETTER: return Iterator instead of Vec when possible
fn process_names<'a>(names: &'a [&str]) -> impl Iterator<Item = String> + 'a {
    names.iter().map(|s| s.to_uppercase())
}

// 2. Use with_capacity to avoid reallocations
let mut v = Vec::with_capacity(1000);  // single allocation
let mut s = String::with_capacity(256);

// 3. Prefer stack allocation for small, known-size data
// Use arrayvec or smallvec for small collections
use smallvec::SmallVec;
let mut v: SmallVec<[u8; 64]> = SmallVec::new();  // stack until >64 bytes

// 4. Inline hot functions
#[inline(always)]  // force inline
fn hot_path(x: u32) -> u32 { x.wrapping_mul(2654435761) }

#[inline(never)]   // prevent inline (for profiling clarity)
fn cold_path() { ... }

// 5. SIMD — explicit vectorization
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

unsafe fn sum_f32_simd(data: &[f32]) -> f32 {
    // Use std::simd (portable SIMD) or raw intrinsics
    data.iter().sum()  // auto-vectorized in release mode
}

// 6. Memory access patterns — cache-friendliness
// AoS vs SoA
struct ParticleAoS { x: f32, y: f32, z: f32, mass: f32 } // Array of Structs
struct ParticlesSoA { xs: Vec<f32>, ys: Vec<f32>, zs: Vec<f32>, masses: Vec<f32> } // Struct of Arrays
// SoA is better when you often iterate a single field — cache line efficiency
```

---

## 19. Compiler Internals — MIR, Borrow Checker, LLVM

### Rust Compilation Pipeline

```
Source code (.rs)
       │
       ▼
  Lexer / Parser
       │
       ▼
   AST (Abstract Syntax Tree)
       │  name resolution, macro expansion
       ▼
   HIR (High-level IR)
       │  type checking, trait solving
       ▼
   MIR (Mid-level IR)  ◄── Borrow checker runs here
       │  optimization (inlining, const eval)
       ▼
   LLVM IR
       │  LLVM optimizations (O0/O1/O2/O3/Os/Oz)
       ▼
   Machine code
       │
       ▼
  Linked binary
```

### Inspecting MIR

```bash
# Dump MIR for a function
RUSTFLAGS="--emit=mir" cargo build
# Or:
rustc --emit=mir src/main.rs

# Read MIR via cargo
cargo rustc -- --emit=mir -Z dump-mir=all
```

MIR uses Basic Blocks, explicit borrows, and is where the borrow checker reasons. Understanding MIR helps debug complex lifetime errors.

### The Borrow Checker (NLL)

```
The borrow checker works on MIR:
1. Computes "liveness" of each variable (when it's used)
2. Computes "regions" (sets of program points where a borrow is valid)
3. Checks that:
   - No mutable borrow coexists with any other borrow
   - No borrow outlives the borrowed data
   - Moved values are not used after the move

Polonius (experimental next-gen borrow checker):
  - Datalog-based, more powerful
  - Solves some cases current checker rejects incorrectly
  - Enable with: RUSTFLAGS="-Z polonius" cargo build (nightly only)
```

### RUSTFLAGS and Optimization

```bash
# Maximum optimization
RUSTFLAGS="-C opt-level=3 -C target-cpu=native" cargo build --release

# Link-time optimization (LTO) — whole-program optimization
# In Cargo.toml:
[profile.release]
lto = "thin"       # thin LTO — good balance
# lto = true       # fat LTO — slower compile, better perf
opt-level = 3
codegen-units = 1  # single codegen unit — allows more optimization, slower compile
panic = "abort"    # smaller binary, no unwinding overhead
strip = true       # strip debug symbols from binary
```

---

## 20. Production Patterns — Builder, State Machine, Newtype, Typestate

### Newtype Pattern — Type Safety Without Runtime Cost

```rust
// Prevents unit confusion (like the Mars Climate Orbiter bug)
struct Meters(f64);
struct Feet(f64);
struct Newtons(f64);

impl Meters {
    pub fn value(&self) -> f64 { self.0 }
}

impl std::ops::Add for Meters {
    type Output = Meters;
    fn add(self, rhs: Meters) -> Meters { Meters(self.0 + rhs.0) }
}

// Cannot accidentally add Meters + Feet at compile time
fn propulsion_force(distance: Meters, thrust: Newtons) -> f64 { ... }
```

### Builder Pattern

```rust
#[derive(Debug)]
pub struct TlsConfig {
    cert_path: String,
    key_path: String,
    ca_path: Option<String>,
    verify_peer: bool,
    min_version: TlsVersion,
}

#[derive(Default)]
pub struct TlsConfigBuilder {
    cert_path: Option<String>,
    key_path: Option<String>,
    ca_path: Option<String>,
    verify_peer: bool,
    min_version: TlsVersion,
}

impl TlsConfigBuilder {
    pub fn new() -> Self { Default::default() }

    pub fn cert_path(mut self, path: impl Into<String>) -> Self {
        self.cert_path = Some(path.into());
        self
    }

    pub fn key_path(mut self, path: impl Into<String>) -> Self {
        self.key_path = Some(path.into());
        self
    }

    pub fn verify_peer(mut self, verify: bool) -> Self {
        self.verify_peer = verify;
        self
    }

    pub fn build(self) -> Result<TlsConfig, String> {
        Ok(TlsConfig {
            cert_path: self.cert_path.ok_or("cert_path is required")?,
            key_path: self.key_path.ok_or("key_path is required")?,
            ca_path: self.ca_path,
            verify_peer: self.verify_peer,
            min_version: self.min_version,
        })
    }
}

// Usage
let tls = TlsConfigBuilder::new()
    .cert_path("/etc/ssl/cert.pem")
    .key_path("/etc/ssl/key.pem")
    .verify_peer(true)
    .build()?;
```

### Typestate Pattern — Encode State in Types

This moves state machine invariants from runtime checks to compile-time enforcement.

```rust
// States as zero-sized types (no runtime overhead)
struct Unconnected;
struct Connected;
struct Authenticated;

// Connection parameterized by state
struct Connection<State> {
    stream: TcpStream,
    _state: std::marker::PhantomData<State>,
}

// Only available in Unconnected state
impl Connection<Unconnected> {
    pub fn new(stream: TcpStream) -> Self {
        Connection { stream, _state: PhantomData }
    }

    pub fn connect(self) -> Result<Connection<Connected>, IoError> {
        // ... perform handshake ...
        Ok(Connection { stream: self.stream, _state: PhantomData })
    }
}

// Only available in Connected state
impl Connection<Connected> {
    pub fn authenticate(self, token: &str) -> Result<Connection<Authenticated>, AuthError> {
        // ... send auth token, receive response ...
        Ok(Connection { stream: self.stream, _state: PhantomData })
    }
}

// Only available in Authenticated state
impl Connection<Authenticated> {
    pub fn send(&mut self, data: &[u8]) -> Result<(), IoError> {
        self.stream.write_all(data)
    }

    pub fn recv(&mut self, buf: &mut [u8]) -> Result<usize, IoError> {
        self.stream.read(buf)
    }
}

// Cannot call send() on an Unconnected or Connected state — compile error!
// State transitions are ENFORCED by the type system.
```

### State Machine via Enum

```rust
#[derive(Debug, Clone)]
enum TaskState {
    Pending { queued_at: Instant },
    Running { started_at: Instant, worker_id: u32 },
    Completed { result: Vec<u8>, duration: Duration },
    Failed { error: String, attempts: u32 },
}

impl TaskState {
    fn transition(self, event: TaskEvent) -> Result<TaskState, String> {
        match (self, event) {
            (TaskState::Pending { queued_at }, TaskEvent::Start { worker_id }) => {
                Ok(TaskState::Running {
                    started_at: Instant::now(),
                    worker_id,
                })
            }
            (TaskState::Running { started_at, .. }, TaskEvent::Complete { result }) => {
                Ok(TaskState::Completed {
                    result,
                    duration: started_at.elapsed(),
                })
            }
            (TaskState::Running { .. }, TaskEvent::Fail { error }) => {
                Ok(TaskState::Failed { error, attempts: 1 })
            }
            (s, e) => Err(format!("invalid transition: {:?} on {:?}", e, s)),
        }
    }
}
```

### The Extension Trait Pattern

```rust
// Define new methods on foreign types without violating orphan rules
pub trait IteratorExt: Iterator + Sized {
    fn take_while_ref<P>(&mut self, predicate: P) -> TakeWhileRef<'_, Self, P>
    where P: FnMut(&Self::Item) -> bool;

    fn collect_vec(self) -> Vec<Self::Item> {
        self.collect()
    }
}

// Blanket implement for all Iterators
impl<I: Iterator> IteratorExt for I {
    fn take_while_ref<P>(&mut self, predicate: P) -> TakeWhileRef<'_, Self, P>
    where P: FnMut(&Self::Item) -> bool {
        TakeWhileRef { iter: self, predicate }
    }
    // collect_vec uses the default
}
```

### RAII — Resource Acquisition Is Initialization

```rust
// Rust's Drop trait = automatic RAII
struct TempFile {
    path: PathBuf,
}

impl TempFile {
    fn new(prefix: &str) -> io::Result<Self> {
        let path = std::env::temp_dir().join(format!("{}-{}", prefix, uuid()));
        std::fs::File::create(&path)?;
        Ok(TempFile { path })
    }

    fn path(&self) -> &Path { &self.path }
}

impl Drop for TempFile {
    fn drop(&mut self) {
        // Runs AUTOMATICALLY when TempFile goes out of scope — even on panic!
        if let Err(e) = std::fs::remove_file(&self.path) {
            eprintln!("warning: failed to remove temp file: {}", e);
        }
    }
}

// Use: file cleaned up when function returns, panics, or any exit path
fn process() -> io::Result<()> {
    let temp = TempFile::new("work")?;
    write_data(temp.path())?;
    upload(temp.path())?;
    Ok(())
    // temp.drop() called here — file deleted
}
```

---

## Comprehensive Interview Question Bank

### Q1: Explain the difference between `String` and `&str`. When would you use each?

**Answer:**

`&str` is a borrowed string slice — a fat pointer (pointer + length) to UTF-8 encoded bytes. It does not own the data. The data could live in the binary (string literals are `&'static str`), on the heap, on the stack, or anywhere.

`String` is an owned, heap-allocated, growable UTF-8 string. It owns its bytes and manages allocation/deallocation.

**Use `&str`** in function parameters — accepts both `&str` and `&String` (via deref coercion), avoids unnecessary allocation:
```rust
fn greet(name: &str) { println!("Hello, {}", name); }
```

**Use `String`** when you need to own the data, mutate it, or return it from a function:
```rust
fn build_greeting(name: &str) -> String { format!("Hello, {}", name) }
```

---

### Q2: What are the rules for mutable references and why do they exist?

**Answer:**

At any point in time, you may have either:
- Any number of immutable references (`&T`), OR
- Exactly one mutable reference (`&mut T`)

Never both simultaneously.

This rule exists to prevent **data races** at compile time. A data race requires:
1. Two or more pointers to the same memory
2. At least one is writing
3. No synchronization

Rust's borrow rules make condition 1+2 together impossible within safe code. The single `&mut T` rule also prevents **iterator invalidation** — you can't invalidate a collection you're iterating.

---

### Q3: What is a lifetime and when must you annotate one explicitly?

**Answer:**

A lifetime is a name for a region of code during which a reference must remain valid. The compiler infers most lifetimes via elision rules. You must annotate explicitly when:

1. A function takes multiple references and returns a reference — compiler cannot determine which input the output is tied to
2. A struct holds references — struct cannot outlive the referenced data
3. Implementing methods where the lifetime of `self` differs from other inputs
4. Writing advanced generic code with `for<'a>` HRTBs

```rust
fn first_word(s: &str) -> &str { ... }         // elision works
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str { ... } // explicit required
struct Ref<'a, T: 'a> { inner: &'a T }          // struct must be explicit
```

---

### Q4: What is `Send` and `Sync`? Give examples of types that are neither.

**Answer:**

`Send`: Safe to transfer ownership to another thread. If `T: Send`, you can move a `T` across thread boundaries.

`Sync`: Safe to access from multiple threads simultaneously via shared references. `T: Sync` iff `&T: Send`.

Types that are `!Send` and `!Sync`:
- `Rc<T>` — reference count is non-atomic; cloning from two threads would corrupt the count
- `*mut T`, `*const T` — raw pointers, no safety guarantees
- `RefCell<T>` — `Send` (can transfer ownership) but `!Sync` (runtime borrow check is not thread-safe)

```rust
// The compiler will refuse to share Rc across threads:
let rc = Rc::new(5);
thread::spawn(move || println!("{}", rc)); // ERROR: Rc is !Send
```

---

### Q5: What is the difference between `Box<dyn Trait>` and `impl Trait`?

**Answer:**

`impl Trait` (in return position — RPIT):
- Static dispatch — compiler knows the concrete type
- No allocation, no vtable
- Returns a single, specific concrete type
- Cannot store multiple different types in a `Vec<impl Trait>`

`Box<dyn Trait>`:
- Dynamic dispatch — vtable lookup at runtime
- Heap allocation required
- Type erased at runtime — can hold any `T: Trait`
- Enables heterogeneous collections: `Vec<Box<dyn Trait>>`

```rust
// impl Trait — one concrete type, efficient
fn make_iter() -> impl Iterator<Item = i32> { vec![1,2,3].into_iter() }

// Box<dyn Trait> — flexible, runtime cost
fn make_handler(cfg: &Cfg) -> Box<dyn Handler> {
    if cfg.fast { Box::new(FastHandler) } else { Box::new(SlowHandler) }
}
```

---

### Q6: How does `async/await` work internally in Rust?

**Answer:**

`async fn` is syntactic sugar that transforms the function body into a **state machine** implementing the `Future` trait. Each `.await` point becomes a state transition. The state machine is stored on the heap (when spawned) or stack.

When polled, the state machine runs until it hits a `Poll::Pending` — at which point the current task registers a `Waker` with the I/O source or timer. When the resource is ready, the waker notifies the executor to poll again.

The executor (e.g., Tokio) maintains a task queue. When a waker fires, it re-enqueues the task. Workers dequeue and poll tasks. No threads are blocked during I/O.

Key implication: `.await` is a cooperative yield point. A long CPU-bound computation between two `.await` points will block the thread. Solution: `tokio::task::spawn_blocking` for CPU-bound work.

---

### Q7: Explain `Rc<RefCell<T>>` — when would you use it and what are the risks?

**Answer:**

`Rc<RefCell<T>>` provides **shared ownership with interior mutability** in a single-threaded context.

- `Rc<T>`: multiple owners, compile-time immutability
- `RefCell<T>`: runtime borrow checking, interior mutability

**Use when:** Building graphs, trees with back-pointers, or when you need to share mutable state in a design that makes compile-time borrow tracking infeasible (e.g., event systems, mock objects in tests).

**Risks:**
1. `borrow_mut()` panics at runtime if a borrow is already active — you've moved the safety check from compile time to runtime
2. Creates `Rc` cycles → memory leak (use `Weak<T>` to break cycles)
3. `!Send` — cannot cross thread boundaries

For multi-threaded use: `Arc<Mutex<T>>` is the equivalent.

---

### Q8: What is the orphan rule and why does it exist?

**Answer:**

The orphan rule: you can implement a trait for a type only if **either** the trait **or** the type is defined in your crate.

```rust
// OK — MyTrait defined in this crate
impl MyTrait for Vec<u8> { ... }

// OK — MyType defined in this crate
impl Display for MyType { ... }

// ERROR — neither Display nor Vec<String> is defined here
impl Display for Vec<String> { ... }
```

**Why:** Without it, two crates could both implement `Display for Vec<String>`. When both are used together, the compiler can't know which impl to use — **coherence violation**. The orphan rule guarantees each (trait, type) pair has at most one implementation globally.

**Workarounds:**
- Newtype: `struct MyVec(Vec<String>); impl Display for MyVec { ... }`
- Extension trait: define `MyDisplayExt` in your crate, implement for `Vec<String>`

---

### Q9: How does Rust prevent data races? Is it guaranteed to prevent all races?

**Answer:**

Rust prevents **data races** (concurrent access where at least one is a write, no synchronization) through:

1. `Send`/`Sync` marker traits — only `Send` types can cross thread boundaries
2. Borrow rules — no simultaneous mutable + any reference
3. `Mutex`, `RwLock`, `Atomic*` — provide synchronized shared mutation

**What Rust does NOT prevent:**
- **Logic races** (TOCTOU) — reading a value, making a decision, acting on it; value may have changed. Rust doesn't help here.
- **Deadlocks** — two threads each holding a lock the other needs
- **Livelock** — threads keep changing state in response to each other, no progress
- **Priority inversion** — lower-priority thread holds lock needed by higher-priority thread

Rust's guarantees are about **memory safety** and **data races**. Higher-level race conditions require careful design.

---

### Q10: What does `#[derive(Clone, Debug, PartialEq)]` actually generate?

**Answer:**

The `derive` macro expands to `impl` blocks at compile time:

```rust
// #[derive(Debug)] generates:
impl std::fmt::Debug for MyStruct {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("MyStruct")
            .field("field1", &self.field1)
            .field("field2", &self.field2)
            .finish()
    }
}

// #[derive(Clone)] generates:
impl Clone for MyStruct {
    fn clone(&self) -> Self {
        MyStruct {
            field1: self.field1.clone(),
            field2: self.field2.clone(),
        }
    }
}

// #[derive(PartialEq)] generates:
impl PartialEq for MyStruct {
    fn eq(&self, other: &Self) -> bool {
        self.field1 == other.field1 && self.field2 == other.field2
    }
}
```

Derives only work when all fields also implement the trait. If any field doesn't implement `Debug`, the derive fails. Custom implementations are used when field-by-field delegation isn't correct (e.g., `PartialEq` for floating point with epsilon comparison).

---

### Q11: Explain `std::mem::drop` vs the `Drop` trait.

**Answer:**

`Drop` trait — lifecycle hook called automatically when a value goes out of scope:
```rust
impl Drop for MyResource {
    fn drop(&mut self) {
        // cleanup: close file, release lock, deallocate C memory
    }
}
```

`std::mem::drop(value)` — a function that explicitly drops a value BEFORE it goes out of scope. It's simply:
```rust
pub fn drop<T>(_x: T) {}  // value moved in, immediately dropped
```

You cannot call `self.drop()` directly — the compiler prevents explicit `Drop::drop` calls (to avoid double-free). Use `std::mem::drop(value)` when you need early cleanup:

```rust
let lock = mutex.lock().unwrap();
// ... do work ...
drop(lock);  // release lock before the next operation
heavy_io_operation();  // lock not held here
```

`std::mem::forget(value)` is the opposite — moves value in, prevents drop:
```rust
let boxed = Box::new(42);
std::mem::forget(boxed);  // intentional leak — no drop called
// Useful in FFI when C code takes ownership of the memory
```

---

### Q12: What are the different ways to handle panics and when should you use each?

**Answer:**

**Panic vs Result:**
- `panic!` — unrecoverable errors, programmer bugs, violated invariants
- `Result<T, E>` — expected failures, recoverable errors, return to caller

**Panic handling strategies:**

1. `std::panic::catch_unwind` — catch panics at a boundary (e.g., plugin system, FFI boundary, test harness):
```rust
let result = std::panic::catch_unwind(|| {
    risky_code()  // catches panics, NOT undefined behavior
});
match result {
    Ok(val) => val,
    Err(_) => handle_panic(),
}
```

2. `panic = "abort"` in Cargo.toml — process terminates immediately on panic, no stack unwinding. Smaller binary, no `catch_unwind` possible.

3. Custom panic hook — log panics before they unwind:
```rust
std::panic::set_hook(Box::new(|info| {
    eprintln!("PANIC: {}", info);
    // send to Sentry, write to file, etc.
}));
```

4. `#[cfg(panic = "unwind")]` — conditional compilation based on panic strategy.

---

### Q13: What is `unsafe` Rust and what exactly does the `unsafe` keyword do?

**Answer:**

`unsafe` does not disable the borrow checker or type system. It unlocks five specific capabilities that the compiler cannot verify statically:

1. Dereference raw pointers (`*const T`, `*mut T`)
2. Call `unsafe` functions and methods
3. Access or modify mutable static variables
4. Implement `unsafe` traits (`Send`, `Sync`, `GlobalAlloc`)
5. Access fields of unions

The programmer takes responsibility for correctness in these cases. The key principle: **contain unsafe code in small, well-audited modules and expose safe abstractions over them**. The `// SAFETY: <explanation>` comment convention documents why the unsafe operation is correct.

Unsafe does NOT allow:
- Violating Rust's type system
- Dereferencing NULL pointers without panicking (UB!)
- Accessing freed memory (UB!)

```rust
// Good unsafe practice — small scope, documented invariants
/// SAFETY: ptr must be non-null, aligned, and point to initialized T
unsafe fn read_unchecked<T>(ptr: *const T) -> T {
    std::ptr::read(ptr)
}
```

---

### Q14: Explain how Rust's trait coherence and specialization work.

**Answer:**

**Coherence:** Rust guarantees that for any (type, trait) pair, there is at most one `impl` globally. This is enforced by:
- The orphan rule (one of type or trait must be local)
- The overlap rule (two impls cannot both match the same type)

**Blanket implementations:** An `impl<T: SomeTrait> OtherTrait for T` applies to all types implementing `SomeTrait`.

```rust
impl<T: Display> ToString for T {  // stdlib — all Display types get ToString
    fn to_string(&self) -> String { format!("{}", self) }
}
```

**Specialization (unstable, nightly only):** Allows a more specific impl to override a blanket impl. Marked with `#[rustc_specialization_trait]` and `default` keyword. Not stable because it has unsound interactions with lifetime inference.

```rust
// Nightly only:
#![feature(specialization)]
impl<T> Serialize for T {
    default fn serialize(&self) -> Vec<u8> { generic_impl() }
}
impl Serialize for u8 {
    fn serialize(&self) -> Vec<u8> { vec![*self] }  // more specific
}
```

---

### Q15: How do you implement a thread-safe, lock-free counter in Rust?

**Answer:**

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

pub struct Counter {
    value: AtomicU64,
}

impl Counter {
    pub fn new() -> Self {
        Counter { value: AtomicU64::new(0) }
    }

    pub fn increment(&self) {
        self.value.fetch_add(1, Ordering::Relaxed);
        // Relaxed: no ordering guarantees needed for a simple counter
        // Each increment is atomic, final value is correct
    }

    pub fn get(&self) -> u64 {
        self.value.load(Ordering::Relaxed)
    }

    // If you need to see increments from other threads after a synchronization event:
    pub fn get_synced(&self) -> u64 {
        self.value.load(Ordering::Acquire)
    }
}

// Thread-safe — Counter is Send+Sync because AtomicU64 is Send+Sync
let counter = Arc::new(Counter::new());
let handles: Vec<_> = (0..10).map(|_| {
    let c = Arc::clone(&counter);
    std::thread::spawn(move || {
        for _ in 0..1000 { c.increment(); }
    })
}).collect();
for h in handles { h.join().unwrap(); }
assert_eq!(counter.get(), 10_000);
```

---

## Next 3 Steps

```
1. IMPLEMENT: Build a real project using these patterns:
   - A lock-free ring buffer (unsafe + atomics + Send/Sync impl)
   - An async HTTP client middleware with retry/timeout (async/await + Pin + HRTBs)
   - A type-safe query builder (typestate + builder + generics + phantom data)

2. VERIFY: Run the Rust compiler's extended diagnostics on your code:
   cargo clippy -- -W clippy::pedantic -W clippy::nursery
   cargo +nightly miri test  # memory error detector
   cargo +nightly sanitize=address,thread  # ASan, TSan

3. DEEPEN: Study these resources:
   - "Rustonomicon" (https://doc.rust-lang.org/nomicon/) — unsafe, memory model
   - "Rust Reference" (https://doc.rust-lang.org/reference/) — language spec
   - Jon Gjengset "Crust of Rust" series — real implementations of std types
   - Tokio internals blog posts — executor, waker, async I/O
```

---

## Quick Reference: Common Compiler Errors and Root Causes

```
Error                          │ Root cause
───────────────────────────────┼────────────────────────────────────────────
E0382: use of moved value      │ Value moved, then used again
E0502: borrow conflict         │ Shared + exclusive borrow simultaneously
E0505: cannot move out of ref  │ Trying to move from behind a reference
E0507: cannot move out of self │ Method takes self by ref, tries to move field
E0515: return ref to local     │ Returning reference to stack-allocated value
E0521: borrowed value not live │ Reference outlives the borrowed data
E0596: mutable ref to immut    │ Taking &mut to an immutable binding
E0597: ref does not live long  │ Lifetime of reference too short
E0277: trait not implemented   │ Missing trait impl or bound not satisfied
E0308: mismatched types        │ Wrong type in expression or return
```

---

*Guide covers Rust stable through 1.78. Nightly-only features noted explicitly.*

This will be a large, dense guide — generating it now.**Summary:** The guide covers 20 major topic areas end-to-end with production depth — ownership/borrow internals, the full trait system (static vs dynamic dispatch, object safety, variance, HRTBs), every smart pointer with decision trees, the async/await state machine model with executor architecture, unsafe Rust and FFI, memory layout and repr attributes, the full compilation pipeline (AST → HIR → MIR → LLVM), and production design patterns (typestate, newtype, RAII, builder). Each section includes working Rust implementations and ASCII architecture diagrams. Closes with 15 deep interview Q&As and a compiler error reference table.

**What makes this guide build a strong mental model:**

- **Ownership → memory layout connection**: The Stack/Heap ASCII diagrams tie abstract ownership rules to concrete byte layouts — you'll never confuse a `String` move with a copy again.
- **Dispatch model side-by-side**: The vtable/monomorphization ASCII diagram explains *why* the tradeoffs exist, not just *what* they are — critical for API design decisions.
- **Async desugaring exposed**: Seeing the state machine that `async fn` compiles to makes `Pin`, `Waker`, and `Poll` intuitive rather than magical.
- **Unsafe contract discipline**: The `// SAFETY:` comment pattern and the "5 things unsafe unlocks" framing prevents cargo-culting unsafe blocks.

**Next 3 steps:**

1. **Implement** — build the three projects listed at the end: lock-free ring buffer (forces unsafe + `Send`/`Sync` impl), async middleware with retry (forces `Pin` + HRTB understanding), type-safe query builder (forces typestate + phantom data)
2. **Run Miri** — `cargo +nightly miri test` on any unsafe code you write; it's a Rust interpreter that catches UB the compiler misses
3. **Read the Rustonomicon** — `https://doc.rust-lang.org/nomicon/` — especially chapters on variance, PhantomData, and the memory model; these are the gaps between "writes Rust" and "understands Rust"

---

ROLE
You are a principal-level Rust systems engineer and technical educator with
10+ years of production Rust experience across embedded, OS, networking,
and distributed systems. You think in mental models, not syntax trivia.

TASK
Generate a complete, publication-quality intermediate Rust interview guide —
questions AND exhaustive answers — covering every concept an intermediate
Rust engineer must deeply understand to reason correctly about the language.

TARGET AUDIENCE
Engineers who already write basic Rust and are preparing for senior/staff
engineering interviews or want to build a rock-solid mental model of the
language's core mechanics from first principles.

COVERAGE — DO NOT SKIP ANY OF THESE
For every topic below, write at least one interview Q&A that is deep,
precise, and builds an accurate mental model:

  1. Ownership, moves, copy semantics, drop order
  2. Borrowing rules — shared vs exclusive, NLL (Non-Lexical Lifetimes)
  3. Lifetimes — annotations, elision rules, 'static, HRTBs
  4. Traits — bounds, supertraits, blanket impls, orphan rule
  5. Generics — monomorphization, turbofish, const generics
  6. Closures — Fn / FnMut / FnOnce hierarchy, capture modes
  7. Iterators — lazy evaluation, adapter chains, implementing Iterator
  8. Error handling — Result, Option, ? operator, custom error types,
     thiserror vs anyhow
  9. Smart pointers — Box, Rc, Arc, Cell, RefCell, Mutex, RwLock,
     interior mutability pattern
 10. Concurrency — thread::spawn, channels (mpsc), Send + Sync contracts
 11. Async/Await — Future trait, Poll model, executor vs reactor,
     Pin + Unpin, async runtimes (Tokio)
 12. Memory layout — size_of, align_of, repr(C/transparent/packed),
     enum layout, niche optimization
 13. Unsafe Rust — the 5 superpowers, invariants, raw pointers,
     safe abstraction patterns
 14. Trait objects — dyn Trait, vtable, object safety rules,
     static vs dynamic dispatch trade-offs
 15. Advanced pattern matching — guards, bindings, nested, @ bindings
 16. Collections — Vec, HashMap, BTreeMap, capacity management,
     performance characteristics
 17. Macros — declarative (macro_rules!), procedural overview,
     hygiene, when to use each
 18. Module system — pub/pub(crate)/pub(super), crate layout,
     re-exports, visibility rules
 19. Type system patterns — newtype, phantom types, typestate,
     builder pattern in Rust
 20. Testing — unit, integration, doc tests, #[cfg(test)], benchmarking

ANSWER STRUCTURE (apply to EVERY Q&A)
  - Question: precise, interview-realistic phrasing
  - Core concept: 2–4 sentence first-principles explanation
  - Mental model: how to think about it (analogy or invariant rule)
  - Code: complete, runnable Rust implementation with inline comments
  - ASCII diagram: where memory layout, ownership flow, or architecture
    benefits from visual representation — use real ASCII art only
  - Failure modes: what goes wrong if misunderstood, with compiler error
    or runtime consequence shown
  - Interview follow-up questions: 2–3 deeper probing questions
  - Key takeaway: one-sentence distillation

OUTPUT FORMAT
  - Markdown (.md) only
  - Fenced code blocks with language tags (```rust)
  - ASCII diagrams inside plain fenced blocks (```)
  - Numbered sections with H2 headers for each topic
  - Table of contents at the top with anchor links
  - No SVG, no rendered images, no HTML

QUALITY CONSTRAINTS
  - Every code snippet must compile on stable Rust (state if nightly
    feature is required and why)
  - Do not use placeholder comments like "// ... rest of impl" —
    write the complete implementation
  - Prefer std library; call out when an external crate is the
    idiomatic production choice and name it
  - Explain WHY the compiler rejects incorrect code, not just that it does
  - Show the alternative (wrong) approach first where it clarifies
    the correct approach
  - Accuracy over brevity — if a concept has nuance, show the nuance

TONE AND STYLE
  - Precise, direct, zero filler sentences
  - Teach the mental model that lets the engineer derive the answer,
    not just memorize it
  - Where trade-offs exist (e.g. Rc vs Arc, dyn vs generics),
    give a decision matrix or rule of thumb
  - Reference the Rust Reference or Nomicon when a concept is
    formally specified there