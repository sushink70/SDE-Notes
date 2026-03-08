# 🦀 The Complete Guide to `type` in Rust
### From Fundamentals to Mastery — A World-Class DSA & Systems Mentor Series

---

## 📚 Table of Contents

1. [What is the `type` Keyword?](#1-what-is-the-type-keyword)
2. [Type Aliases — The Foundation](#2-type-aliases--the-foundation)
3. [Why Type Aliases Exist — The Mental Model](#3-why-type-aliases-exist--the-mental-model)
4. [Generic Type Aliases](#4-generic-type-aliases)
5. [Associated Types in Traits](#5-associated-types-in-traits)
6. [Associated Types vs Generic Parameters](#6-associated-types-vs-generic-parameters)
7. [The `Self` Type](#7-the-self-type)
8. [Type Aliases in `impl` Blocks](#8-type-aliases-in-impl-blocks)
9. [The Newtype Pattern vs Type Alias](#9-the-newtype-pattern-vs-type-alias)
10. [Type Aliases in FFI (C Interop)](#10-type-aliases-in-ffi-c-interop)
11. [Type Aliases for Complex Closures & Function Pointers](#11-type-aliases-for-complex-closures--function-pointers)
12. [`type` in Error Handling Patterns](#12-type-in-error-handling-patterns)
13. [`type` with Lifetimes](#13-type-with-lifetimes)
14. [Type Aliases in the Standard Library](#14-type-aliases-in-the-standard-library)
15. [Real-World System Design with `type`](#15-real-world-system-design-with-type)
16. [Performance & Zero-Cost Abstractions](#16-performance--zero-cost-abstractions)
17. [Common Mistakes & Pitfalls](#17-common-mistakes--pitfalls)
18. [Mental Models & Expert Intuition](#18-mental-models--expert-intuition)

---

## 1. What is the `type` Keyword?

Before we dive in, let's build crystal-clear mental models.

### Concept: What is a "Type" in Programming?

A **type** is a **label** the compiler uses to understand:
- How much memory a value occupies
- What operations are valid on that value
- How to interpret raw bits in memory

```
Raw Memory (bits):   0100 0001
                         |
              Without type context --> meaningless
                         |
         With type u8  --+---> integer 65
         With type char --+--> character 'A'
```

### Concept: What is a "Type Alias"?

A **type alias** is like a **nickname** or **label** you give to an existing type.
It does NOT create a new type. It is purely a compile-time name substitution.

```
+----------------------------------------------------------+
|                    TYPE ALIAS                            |
|                                                          |
|   Original Type ---------> Alias Name                   |
|   HashMap<String, Vec<u64>> --> UserScoreMap             |
|                                                          |
|   The compiler sees BOTH as IDENTICAL                    |
|   No runtime overhead. Zero cost.                        |
+----------------------------------------------------------+
```

### Syntax

```rust
type AliasName = ExistingType;
type AliasName<T> = ExistingType<T>;          // with generics
type AliasName<'a> = ExistingType<'a>;        // with lifetimes
type AliasName<T: Trait> = ExistingType<T>;   // with bounds (unstable)
```

---

## 2. Type Aliases — The Foundation

### 2.1 Simple Scalar Aliases

```rust
// ---- Primitive aliases ----------------------------------------
type Meters    = f64;
type Kilograms = f64;
type Seconds   = f64;
type NodeId    = u64;
type EdgeId    = u64;
type Weight    = f32;

fn calculate_velocity(distance: Meters, time: Seconds) -> f64 {
    distance / time
}

fn main() {
    let d: Meters  = 100.0;
    let t: Seconds = 9.58;  // Usain Bolt's 100m world record

    println!("Velocity: {:.2} m/s", calculate_velocity(d, t));
    // Output: Velocity: 10.44 m/s
}
```

> CRITICAL INSIGHT: Even though `Meters` and `Kilograms` are both aliases for `f64`,
> Rust does NOT prevent you from mixing them! A type alias provides NO type safety.
> (We'll see the solution — Newtype Pattern — in Section 9)

```rust
let m: Meters     = 100.0;
let kg: Kilograms = 75.0;

// This COMPILES -- Rust sees both as f64!
let nonsense: Meters = m + kg; // <-- bug, no compiler error
```

### 2.2 Complex Type Aliases

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

// ---- Without aliases ------------------------------------------
fn process(
    db: HashMap<String, Vec<HashMap<String, Arc<Mutex<Vec<u8>>>>>>,
) { /* ... */ }

// ---- With aliases ---------------------------------------------
type RawData    = Vec<u8>;
type SharedData = Arc<Mutex<RawData>>;
type Record     = HashMap<String, SharedData>;
type RecordList = Vec<Record>;
type Database   = HashMap<String, RecordList>;

fn process(db: Database) {
    // Now both the function signature and the body are readable
}
```

**Visual: Nesting Depth Without vs With Aliases**

```
WITHOUT aliases (reading a nested type):
HashMap<String, Vec<HashMap<String, Arc<Mutex<Vec<u8>>>>>>
|       |        |  |       |      |   |    |    |
|       |        |  |       |      |   +----+    +-- level 6
|       |        |  |       |      +-- level 5
|       |        |  |       +-- level 4
|       |        |  +-- level 3
|       |        +-- level 2
|       +-- level 1
+-- top

WITH aliases (flat, readable):
Database   = HashMap<String, RecordList>
RecordList = Vec<Record>
Record     = HashMap<String, SharedData>
SharedData = Arc<Mutex<RawData>>
RawData    = Vec<u8>

Each level reads like English prose.
```

---

## 3. Why Type Aliases Exist — The Mental Model

### The 4 Core Purposes

```
+------------------------------------------------------------------+
|                   WHY USE TYPE ALIASES?                          |
|                                                                  |
|  1. READABILITY    --- Give domain meaning to raw types          |
|                        (NodeId vs u64)                           |
|                                                                  |
|  2. MAINTAINABILITY -- Change one definition, update everywhere  |
|                        (change f32->f64 in one place)            |
|                                                                  |
|  3. DRY PRINCIPLE  --- Don't Repeat complex type expressions     |
|                        (HashMap<String, Vec<Arc<Mutex<...>>>>)   |
|                                                                  |
|  4. API DESIGN     --- Hide implementation details in libraries  |
|                        (users see Result<T> not full path)       |
+------------------------------------------------------------------+
```

### 3.1 Maintainability — The "Single Point of Change" Principle

```rust
// ---- Version 1: using f32 for coordinates --------------------
type Coordinate = f32;
type Point2D    = (Coordinate, Coordinate);
type Point3D    = (Coordinate, Coordinate, Coordinate);

fn distance(a: Point2D, b: Point2D) -> Coordinate {
    let dx = a.0 - b.0;
    let dy = a.1 - b.1;
    (dx * dx + dy * dy).sqrt()
}

// ---- Version 2: switching to f64 for precision ---------------
// Change ONE LINE. Everything else stays the same:
type Coordinate = f64;  // <-- the ONLY change needed

// distance(), Point2D, Point3D all automatically updated
```

---

## 4. Generic Type Aliases

### Concept: Generics

A **generic** type is a type that has a **placeholder** `<T>` for "some type to be decided later."
Think of it like a function parameter, but for types.

```
fn add(x: i32, y: i32) -> i32   <-- concrete function, works only for i32
fn add<T>(x: T, y: T) -> T      <-- generic function, works for ANY type T

Similarly:
Vec<i32>        <-- concrete: vector of i32s
Vec<T>          <-- generic: vector of SOME type T
```

### 4.1 Generic Alias Syntax

```rust
use std::collections::HashMap;

// Generic alias: "a map from K to a vector of V"
type MultiMap<K, V> = HashMap<K, Vec<V>>;

// Partial application: fix one type, keep one generic
type StringMap<V>   = HashMap<String, V>;
type IntMap<V>      = HashMap<i64, V>;

fn main() {
    // MultiMap<String, i32> expands to HashMap<String, Vec<i32>>
    let mut scores: MultiMap<String, i32> = HashMap::new();
    scores.entry("Alice".to_string()).or_default().push(95);
    scores.entry("Alice".to_string()).or_default().push(87);
    scores.entry("Bob".to_string()).or_default().push(72);

    for (name, score_list) in &scores {
        let avg: f64 = score_list.iter().sum::<i32>() as f64
                       / score_list.len() as f64;
        println!("{name}: avg = {avg:.1}");
    }
}
```

### 4.2 Generic Aliases in Graph Algorithms (DSA)

```rust
use std::collections::HashMap;

// ---- Graph representation types ------------------------------
type VertexId        = usize;
type EdgeWeight      = i64;
type AdjacencyList   = Vec<Vec<(VertexId, EdgeWeight)>>;
type AdjacencyMatrix = Vec<Vec<EdgeWeight>>;
type DistanceMap     = HashMap<VertexId, EdgeWeight>;
type ParentMap       = HashMap<VertexId, Option<VertexId>>;

// ---- Dijkstra's algorithm -- signature is now crystal-clear --
fn dijkstra(
    graph: &AdjacencyList,
    source: VertexId,
) -> (DistanceMap, ParentMap) {
    let n = graph.len();
    let mut dist:   DistanceMap = HashMap::new();
    let mut parent: ParentMap   = HashMap::new();

    for v in 0..n {
        dist.insert(v, i64::MAX);
        parent.insert(v, None);
    }
    dist.insert(source, 0);

    // ... (rest of Dijkstra)
    (dist, parent)
}
```

**Flow: How the Compiler Resolves Generic Aliases**

```
User writes:    let dist: DistanceMap = HashMap::new();
                              |
                              v
Compiler expands:  HashMap<VertexId, EdgeWeight>
                              |
                              v
Expands again:     HashMap<usize, i64>
                              |
                              v
Final type:        HashMap<usize, i64>   <-- what lives in memory
```

---

## 5. Associated Types in Traits

This is one of the most powerful uses of `type` in Rust.

### Concept: What is a Trait?

A **trait** is a contract -- it says: "Any type that implements this trait MUST provide
these functions/behaviors."

```
trait Drawable {
    fn draw(&self);     // every Drawable must have a draw() method
}

struct Circle;
impl Drawable for Circle {
    fn draw(&self) { println!("Drawing circle"); }
}
```

### Concept: Associated Type

An **associated type** is a `type` placeholder *inside* a trait definition.
When a struct implements the trait, it must specify what that type IS.

```
+----------------------------------------------------------------+
|                    ASSOCIATED TYPE                             |
|                                                                |
|  In trait definition:                                          |
|    type Output;   <-- "defined by the implementor"            |
|                                                                |
|  In implementation:                                            |
|    type Output = i32;   <-- concrete type specified here      |
+----------------------------------------------------------------+
```

### 5.1 Basic Associated Type

```rust
// ---- Trait with associated type ------------------------------
trait Container {
    type Item;              // <-- associated type declaration

    fn first(&self) -> Option<&Self::Item>;
    fn last(&self)  -> Option<&Self::Item>;
    fn len(&self)   -> usize;
    fn is_empty(&self) -> bool {
        self.len() == 0     // default implementation
    }
}

// ---- Implement for a Stack -----------------------------------
struct Stack<T> {
    data: Vec<T>,
}

impl<T> Container for Stack<T> {
    type Item = T;          // <-- here we specify what Item IS

    fn first(&self) -> Option<&T> { self.data.first() }
    fn last(&self)  -> Option<&T> { self.data.last()  }
    fn len(&self)   -> usize      { self.data.len()   }
}

fn main() {
    let s: Stack<i32> = Stack { data: vec![1, 2, 3] };
    println!("First: {:?}", s.first()); // Some(1)
    println!("Last: {:?}",  s.last());  // Some(3)
    println!("Len: {}",     s.len());   // 3
}
```

### 5.2 The Standard Library's `Iterator` Trait

The most famous associated type in Rust:

```rust
// ---- Simplified Iterator trait (from std) --------------------
trait Iterator {
    type Item;                              // <-- associated type

    fn next(&mut self) -> Option<Self::Item>;

    // All these are provided using just `next` and `Item`:
    fn map<B, F: Fn(Self::Item) -> B>(self, f: F) -> Map<Self, F> { ... }
    fn filter<P: Fn(&Self::Item) -> bool>(self, p: P) -> Filter<Self, P> { ... }
    fn collect<B: FromIterator<Self::Item>>(self) -> B { ... }
}

// ---- Custom range iterator -----------------------------------
struct CountUp {
    current: u64,
    max:     u64,
}

impl Iterator for CountUp {
    type Item = u64;    // <-- our iterator yields u64 values

    fn next(&mut self) -> Option<u64> {
        if self.current <= self.max {
            let val = self.current;
            self.current += 1;
            Some(val)
        } else {
            None
        }
    }
}

fn main() {
    let counter = CountUp { current: 1, max: 5 };

    // All of Iterator's methods work automatically!
    let sum: u64 = counter.sum(); // 15

    let evens: Vec<u64> = CountUp { current: 1, max: 10 }
        .filter(|x| x % 2 == 0)
        .collect();
    // evens = [2, 4, 6, 8, 10]
}
```

### 5.3 The `Add` Trait — Operator Overloading

```rust
use std::ops::Add;

// std::ops::Add looks like:
// trait Add<Rhs = Self> {
//     type Output;
//     fn add(self, rhs: Rhs) -> Self::Output;
// }

#[derive(Debug, Clone, Copy)]
struct Vector2D {
    x: f64,
    y: f64,
}

impl Add for Vector2D {
    type Output = Vector2D;   // <-- adding two Vector2D gives a Vector2D

    fn add(self, other: Vector2D) -> Vector2D {
        Vector2D {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

// ---- Mixed type addition -------------------------------------
impl Add<f64> for Vector2D {
    type Output = Vector2D;

    fn add(self, scalar: f64) -> Vector2D {
        Vector2D {
            x: self.x + scalar,
            y: self.y + scalar,
        }
    }
}

fn main() {
    let a = Vector2D { x: 1.0, y: 2.0 };
    let b = Vector2D { x: 3.0, y: 4.0 };
    let c = a + b;        // Vector2D { x: 4.0, y: 6.0 }
    let d = a + 10.0;     // Vector2D { x: 11.0, y: 12.0 }
    println!("{:?}", c);
    println!("{:?}", d);
}
```

---

## 6. Associated Types vs Generic Parameters

This is one of the subtlest and most important distinctions in Rust design.

### The Core Question

When should you use an **associated type** vs a **generic parameter**?

```rust
trait Converter<T> {          // <-- T is a GENERIC PARAMETER
    fn convert(&self) -> T;
}

trait Converter {             // <-- no generic; uses associated type
    type Output;
    fn convert(&self) -> Self::Output;
}
```

### Decision Flowchart

```
+--------------------------------------------------------------+
|         ASSOCIATED TYPE vs GENERIC PARAMETER?                |
|                                                              |
|  Ask: "For a given implementor, can there be MULTIPLE        |
|         valid versions of this type?"                        |
|                         |                                    |
|            +------------+------------+                       |
|           YES                        NO                      |
|            |                          |                      |
|   Use GENERIC PARAMETER       Use ASSOCIATED TYPE            |
|                                                              |
|  Example:                     Example:                       |
|  impl Converter<i32> for Foo  impl Iterator for CountUp      |
|  impl Converter<f64> for Foo  <- only ONE Item makes sense   |
|  <- multiple conversions OK   type Item = u64;               |
+--------------------------------------------------------------+
```

### Side-by-Side Comparison

```rust
// ---- GENERIC PARAMETER version (one-to-many) -----------------
// A type CAN implement this multiple times for different T
trait From<T> {
    fn from(t: T) -> Self;
}

struct Wrapper(i64);

impl From<i32> for Wrapper {
    fn from(x: i32) -> Self { Wrapper(x as i64) }
}
impl From<f64> for Wrapper {
    fn from(x: f64) -> Self { Wrapper(x as i64) }
}

// ---- ASSOCIATED TYPE version (one-to-one) --------------------
// A type can only implement this ONCE (one concrete Output)
trait IntoString {
    type Output;
    fn stringify(&self) -> Self::Output;
}

struct Point { x: i32, y: i32 }

impl IntoString for Point {
    type Output = String;        // exactly ONE output type
    fn stringify(&self) -> String {
        format!("({}, {})", self.x, self.y)
    }
}
```

### Practical Implication Table

```
+---------------------+--------------------+----------------------+
| Property            | Generic Parameter  | Associated Type      |
+---------------------+--------------------+----------------------+
| Implementations     | Many per type      | One per type         |
| per struct          |                    |                      |
+---------------------+--------------------+----------------------+
| Type inference      | Must often specify | Inferred from impl   |
| at call site        | with turbofish     | automatically        |
+---------------------+--------------------+----------------------+
| Conceptual fit      | Relationship is    | Type is uniquely     |
|                     | one-to-many        | determined           |
+---------------------+--------------------+----------------------+
| Example in std      | From<T>, Into<T>   | Iterator::Item       |
|                     | PartialEq<Rhs>     | Add::Output          |
+---------------------+--------------------+----------------------+
```

---

## 7. The `Self` Type

### Concept: What is `Self`?

`Self` (capital S) is a special **type alias** that always means "the type that is
currently implementing this trait or being defined in this impl block."

```
+--------------------------------------------------------------+
|                      Self TYPE                               |
|                                                              |
|  In a trait:                                                 |
|    Self --- the CONCRETE type that will implement it         |
|                                                              |
|  In an impl block:                                           |
|    Self --- the type being impl'd                            |
|                                                              |
|  In impl Foo:                                                |
|    Self == Foo                                               |
|                                                              |
|  In impl<T> Bar<T>:                                          |
|    Self == Bar<T>   (T is still generic)                     |
+--------------------------------------------------------------+
```

### 7.1 `Self` in Trait Definitions — Builder Pattern

```rust
// ---- Builder Pattern using Self ------------------------------
trait Builder: Sized {
    fn new() -> Self;

    // Returns Self to enable method chaining
    fn with_name(self, name: &str) -> Self;
    fn with_value(self, value: i32) -> Self;
    fn build(self) -> String;
}

#[derive(Default, Debug)]
struct Config {
    name:  String,
    value: i32,
}

impl Builder for Config {
    fn new() -> Self { Config::default() }  // Self = Config

    fn with_name(mut self, name: &str) -> Self {
        self.name = name.to_string();
        self
    }

    fn with_value(mut self, value: i32) -> Self {
        self.value = value;
        self
    }

    fn build(self) -> String {
        format!("Config {{ name: {}, value: {} }}", self.name, self.value)
    }
}

fn main() {
    // Method chaining works because each step returns Self
    let result = Config::new()
        .with_name("database_pool")
        .with_value(10)
        .build();

    println!("{result}");
    // Output: Config { name: database_pool, value: 10 }
}
```

**Method Chaining Flow**

```
Config::new()          --> Config { name: "", value: 0 }
    |
    v
.with_name("db_pool")  --> Config { name: "db_pool", value: 0 }
    |
    v
.with_value(10)        --> Config { name: "db_pool", value: 10 }
    |
    v
.build()               --> "Config { name: db_pool, value: 10 }"
```

---

## 8. Type Aliases in `impl` Blocks

```rust
// ---- Trait with associated types used in impl ----------------
trait LinearAlgebra {
    type Scalar;
    type Row;

    fn multiply_scalar(&self, s: Self::Scalar) -> Self;
    fn get_row(&self, i: usize) -> &Self::Row;
}

struct Matrix {
    data: Vec<Vec<f64>>,
    rows: usize,
    cols: usize,
}

impl Matrix {
    fn new(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![vec![0.0; cols]; rows],
            rows,
            cols,
        }
    }
}

impl LinearAlgebra for Matrix {
    type Scalar = f64;
    type Row    = Vec<f64>;

    fn multiply_scalar(&self, s: f64) -> Matrix {
        let data = self.data.iter()
            .map(|row| row.iter().map(|&x| x * s).collect())
            .collect();
        Matrix { data, rows: self.rows, cols: self.cols }
    }

    fn get_row(&self, i: usize) -> &Vec<f64> {
        &self.data[i]
    }
}
```

---

## 9. The Newtype Pattern vs Type Alias

### Concept: The Newtype Pattern

A **newtype** is a thin wrapper struct around an existing type.
Unlike a type alias, it creates a TRULY NEW TYPE.

```
+--------------------------------------------------------------+
|              TYPE ALIAS  vs  NEWTYPE PATTERN                 |
|                                                              |
|  TYPE ALIAS                    NEWTYPE                       |
|  ----------                    -------                       |
|  type Meters = f64;            struct Meters(f64);           |
|                                                              |
|  . Same type as f64            . Distinct type from f64      |
|  . Can mix with f64            . Cannot mix with f64         |
|  . No impl needed              . Must impl ops manually      |
|  . Zero overhead               . Zero overhead               |
|  . No type safety              . Full type safety            |
+--------------------------------------------------------------+
```

### 9.1 The Problem Type Aliases Cannot Solve

```rust
type Meters    = f64;
type Kilograms = f64;

fn add_distance(a: Meters, b: Meters) -> Meters { a + b }

let dist:   Meters    = 100.0;
let weight: Kilograms = 75.0;

// BUG: compiles without error! Alias provides no safety.
let result = add_distance(dist, weight);
```

### 9.2 Newtype Provides Compile-Time Safety

```rust
use std::ops::Add;

#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
struct Meters(f64);

#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
struct Kilograms(f64);

impl Add for Meters {
    type Output = Meters;
    fn add(self, other: Meters) -> Meters {
        Meters(self.0 + other.0)
    }
}

fn add_distance(a: Meters, b: Meters) -> Meters { a + b }

fn main() {
    let dist:   Meters    = Meters(100.0);
    let weight: Kilograms = Kilograms(75.0);

    // add_distance(dist, weight);
    // ^^^ COMPILE ERROR: mismatched types
    //     expected Meters, found Kilograms <-- SAFETY ENFORCED

    let total = add_distance(Meters(50.0), Meters(30.0));
    println!("{:?}", total); // Meters(80.0)
}
```

### 9.3 Decision Guide

```
+--------------------------------------------------------------+
|  Use TYPE ALIAS when:                                        |
|  . You want shorter names for long types                     |
|  . You want documentation/readability only                   |
|  . You're working with trait associated types                |
|                                                              |
|  Use NEWTYPE when:                                           |
|  . You need compiler-enforced unit/domain separation         |
|  . You want to implement traits on external types            |
|    (the "orphan rule" workaround)                            |
|  . You want to restrict which operations are valid           |
|  . You're modeling domain concepts (Money, UserId, etc.)     |
+--------------------------------------------------------------+
```

---

## 10. Type Aliases in FFI (C Interop)

### Concept: FFI

FFI (Foreign Function Interface) is how Rust communicates with C/C++ code.
C types may differ in size across platforms.

```rust
use std::os::raw::{c_int, c_char, c_void, c_double};

// ---- C-compatible type aliases --------------------------------
type CInt     = c_int;          // platform-dependent int
type CDouble  = c_double;       // 64-bit float
type CString  = *const c_char;  // null-terminated C string pointer
type CVoid    = *mut c_void;    // void* -- raw untyped pointer

// ---- Declare external C functions ----------------------------
extern "C" {
    fn strlen(s: CString) -> usize;
    fn sqrt(x: CDouble) -> CDouble;
}

// ---- Real-world FFI: binding to a C library ------------------
type LibHandle  = *mut c_void;
type ErrorCode  = c_int;
type BufferPtr  = *mut u8;
type BufferSize = usize;

extern "C" {
    fn lib_init(config: CString) -> LibHandle;
    fn lib_process(handle: LibHandle, buf: BufferPtr, sz: BufferSize) -> ErrorCode;
    fn lib_destroy(handle: LibHandle);
}
```

### Platform-Conditional Aliases

```rust
#[cfg(target_pointer_width = "64")]
type PlatformInt = i64;

#[cfg(target_pointer_width = "32")]
type PlatformInt = i32;

// PlatformInt now always matches the pointer size of the target
type Address = PlatformInt;
```

---

## 11. Type Aliases for Complex Closures & Function Pointers

### Concept: Function Pointers

A **function pointer** holds the memory address of a function.
In Rust, `fn(i32) -> bool` is the type of a function that takes `i32` and returns `bool`.

```
Memory:
+-----------------+
|  Code Segment   |
|                 |
|  0x1000: fn_a  |<-- function_ptr_1 (holds value 0x1000)
|  0x2000: fn_b  |<-- function_ptr_2 (holds value 0x2000)
|                 |
+-----------------+
```

### 11.1 Function Pointer Aliases

```rust
type Transform  = fn(i32) -> i32;
type Predicate  = fn(i32) -> bool;
type Comparator = fn(i32, i32) -> std::cmp::Ordering;

fn apply(data: Vec<i32>, f: Transform) -> Vec<i32> {
    data.into_iter().map(f).collect()
}

fn filter_data(data: Vec<i32>, pred: Predicate) -> Vec<i32> {
    data.into_iter().filter(pred).collect()
}

fn double(x: i32) -> i32  { x * 2 }
fn is_even(x: i32) -> bool { x % 2 == 0 }

fn main() {
    let data = vec![3, 1, 4, 1, 5, 9, 2, 6];

    let doubled = apply(data.clone(), double);
    let evens   = filter_data(data.clone(), is_even);

    println!("Doubled: {:?}", doubled); // [6, 2, 8, 2, 10, 18, 4, 12]
    println!("Evens: {:?}",   evens);   // [4, 2, 6]
}
```

### 11.2 Closure Aliases (Box<dyn Fn>)

```rust
// Box<dyn Fn(...)> = heap-allocated closure (can capture environment)
type EventHandler = Box<dyn Fn(String)>;
type Middleware   = Box<dyn Fn(Vec<u8>) -> Vec<u8>>;

use std::collections::HashMap;

struct EventBus {
    handlers: HashMap<String, Vec<EventHandler>>,
}

impl EventBus {
    fn new() -> Self { EventBus { handlers: HashMap::new() } }

    fn subscribe(&mut self, event: &str, handler: EventHandler) {
        self.handlers
            .entry(event.to_string())
            .or_default()
            .push(handler);
    }

    fn emit(&self, event: &str, data: String) {
        if let Some(handlers) = self.handlers.get(event) {
            for handler in handlers {
                handler(data.clone());
            }
        }
    }
}

fn main() {
    let mut bus = EventBus::new();

    bus.subscribe("user_login", Box::new(|user| {
        println!("Audit log: {} logged in", user);
    }));

    bus.subscribe("user_login", Box::new(|user| {
        println!("Welcome email sent to: {}", user);
    }));

    bus.emit("user_login", "alice@example.com".to_string());
    // Audit log: alice@example.com logged in
    // Welcome email sent to: alice@example.com
}
```

---

## 12. `type` in Error Handling Patterns

### Concept: Result<T, E>

`Result<T, E>` is Rust's type for fallible operations.
`T` = success value type, `E` = error type.

```
Result<T, E>
    |
    +-- Ok(T)  -- success, contains value of type T
    +-- Err(E) -- failure, contains error of type E
```

### 12.1 Module-Scoped Error Type Alias

```rust
use std::num::ParseIntError;
use std::fmt;

#[derive(Debug)]
enum AppError {
    ParseError(ParseIntError),
    DivisionByZero,
    NegativeInput(i64),
    IoError(std::io::Error),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::ParseError(e)    => write!(f, "Parse error: {e}"),
            AppError::DivisionByZero   => write!(f, "Division by zero"),
            AppError::NegativeInput(n) => write!(f, "Negative input: {n}"),
            AppError::IoError(e)       => write!(f, "IO error: {e}"),
        }
    }
}

// ---- THE KEY PATTERN: module-level Result alias ---------------
// Now Result<T> means std::result::Result<T, AppError>
type Result<T> = std::result::Result<T, AppError>;

fn parse_positive(s: &str) -> Result<u64> {
    let n: i64 = s.parse().map_err(AppError::ParseError)?;
    if n < 0 {
        return Err(AppError::NegativeInput(n));
    }
    Ok(n as u64)
}

fn safe_divide(a: u64, b: u64) -> Result<u64> {
    if b == 0 {
        return Err(AppError::DivisionByZero);
    }
    Ok(a / b)
}

fn calculate(input: &str, divisor: &str) -> Result<u64> {
    let a = parse_positive(input)?;    // ? propagates AppError
    let b = parse_positive(divisor)?;
    safe_divide(a, b)
}

fn main() {
    match calculate("100", "5") {
        Ok(v)  => println!("Result: {v}"),        // Result: 20
        Err(e) => println!("Error: {e}"),
    }
    match calculate("100", "0") {
        Ok(v)  => println!("Result: {v}"),
        Err(e) => println!("Error: {e}"),          // Error: Division by zero
    }
}
```

### Error Propagation Flow

```
calculate("100", "0")
        |
        v
parse_positive("100") --> Ok(100)
        |
        v
parse_positive("0")   --> Ok(0)
        |
        v
safe_divide(100, 0)
        |
        v
    b == 0? YES
        |
        v
Err(AppError::DivisionByZero)
        |   (? operator propagates upward)
        v
calculate returns Err(...)
        |
        v
main: "Error: Division by zero"
```

---

## 13. `type` with Lifetimes

### Concept: Lifetimes

A **lifetime** tracks how long a reference remains valid. `'a` is a lifetime annotation.

```
                +--- 'a starts here
                |
let data = vec![1, 2, 3];
let r: &'a Vec<i32> = &data;   // r borrows data
//     ---- 'a -------------------->
                                 ^
                                 +--- 'a must end before data drops
```

### 13.1 Lifetime Aliases

```rust
type StrSlice<'a>     = &'a str;
type ByteSlice<'a>    = &'a [u8];
type MutByteSlice<'a> = &'a mut [u8];

// Parser combinator type: returns (remaining_input, parsed_value)
type ParseResult<'a, T> = Result<(&'a str, T), &'a str>;

fn parse_u32(input: &str) -> ParseResult<'_, u32> {
    let end = input.find(|c: char| !c.is_ascii_digit())
        .unwrap_or(input.len());

    if end == 0 {
        return Err(input); // no digits found
    }

    let (digits, rest) = input.split_at(end);
    let value = digits.parse::<u32>().map_err(|_| input)?;
    Ok((rest, value))
}

fn main() {
    match parse_u32("123 abc") {
        Ok((rest, n)) => println!("Parsed: {n}, remaining: '{rest}'"),
        Err(e)        => println!("Failed on: '{e}'"),
    }
    // Output: Parsed: 123, remaining: ' abc'
}
```

### 13.2 Static Lifetime

```rust
// 'static means valid for the entire program duration
type StaticStr  = &'static str;
type StaticData = &'static [u8];

struct ErrorMessage {
    code:    u32,
    message: StaticStr,  // must be a compile-time string literal
}

const ERRORS: &[ErrorMessage] = &[
    ErrorMessage { code: 404, message: "Not Found" },
    ErrorMessage { code: 500, message: "Internal Server Error" },
];

fn lookup_error(code: u32) -> Option<StaticStr> {
    ERRORS.iter()
        .find(|e| e.code == code)
        .map(|e| e.message)
}
```

---

## 14. Type Aliases in the Standard Library

### Key Standard Library `type` Aliases

```rust
// From std::io
// pub type Result<T> = std::result::Result<T, std::io::Error>;
use std::io;
fn read_file(path: &str) -> io::Result<String> { todo!() }

// From std::fmt
// pub type Result = std::result::Result<(), Error>;
use std::fmt;
impl fmt::Display for MyType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { todo!() }
    //                                              ^^^^^^^^^^
    //             = std::result::Result<(), fmt::Error>
}
```

### Standard Traits Using Associated Types

```
Trait             | Associated Type | Meaning
------------------+-----------------+-------------------------------
Iterator          | Item            | type of element yielded
IntoIterator      | Item, IntoIter  | element and iterator types
Add               | Output          | result of a + b
Sub               | Output          | result of a - b
Mul               | Output          | result of a * b
Div               | Output          | result of a / b
Index             | Output          | type returned by a[i]
Deref             | Target          | type you deref to (*x)
Future            | Output          | value produced when complete
```

---

## 15. Real-World System Design with `type`

### 15.1 Complete Dijkstra's Algorithm

```rust
use std::collections::{HashMap, BinaryHeap};
use std::cmp::Reverse;

type NodeId     = usize;
type EdgeWeight = i64;
type Distance   = i64;

const INFINITY: Distance = i64::MAX;

type Neighbors  = Vec<(NodeId, EdgeWeight)>;
type Graph      = Vec<Neighbors>;
type DistVec    = Vec<Distance>;
type PathResult = Option<(Distance, Vec<NodeId>)>;

fn build_graph(n: usize, edges: &[(NodeId, NodeId, EdgeWeight)]) -> Graph {
    let mut graph: Graph = vec![vec![]; n];
    for &(u, v, w) in edges {
        graph[u].push((v, w));
    }
    graph
}

fn dijkstra(graph: &Graph, src: NodeId, dst: NodeId) -> PathResult {
    let n = graph.len();
    let mut dist: DistVec = vec![INFINITY; n];
    let mut prev: Vec<Option<NodeId>> = vec![None; n];
    let mut heap: BinaryHeap<Reverse<(Distance, NodeId)>> = BinaryHeap::new();

    dist[src] = 0;
    heap.push(Reverse((0, src)));

    while let Some(Reverse((d, u))) = heap.pop() {
        if d > dist[u] { continue; }   // stale entry
        if u == dst    { break;  }     // found destination

        for &(v, w) in &graph[u] {
            let new_dist = dist[u].saturating_add(w);
            if new_dist < dist[v] {
                dist[v] = new_dist;
                prev[v] = Some(u);
                heap.push(Reverse((new_dist, v)));
            }
        }
    }

    if dist[dst] == INFINITY { return None; }

    // Reconstruct path
    let mut path: Vec<NodeId> = Vec::new();
    let mut cur = dst;
    while let Some(p) = prev[cur] {
        path.push(cur);
        cur = p;
    }
    path.push(src);
    path.reverse();

    Some((dist[dst], path))
}

fn main() {
    //  0 --(1)--> 1 --(2)--> 3
    //  |          |
    //  (4)       (1)
    //  v          v
    //  2 --(1)--> 3
    let edges: &[(NodeId, NodeId, EdgeWeight)] = &[
        (0, 1, 1),
        (0, 2, 4),
        (1, 2, 1),
        (1, 3, 2),
        (2, 3, 1),
    ];
    let graph = build_graph(4, edges);

    match dijkstra(&graph, 0, 3) {
        Some((dist, path)) => {
            println!("Shortest distance: {dist}");
            println!("Path: {:?}", path);
        }
        None => println!("No path found"),
    }
    // Shortest distance: 3
    // Path: [0, 1, 2, 3]
}
```

### 15.2 Type-Safe Event Bus

```rust
use std::collections::HashMap;

type StatusCode = u16;
type HeaderMap  = HashMap<String, String>;
type Body       = Vec<u8>;
type Handler    = Box<dyn Fn(&str) + Send + Sync>;

struct EventBus {
    handlers: HashMap<String, Vec<Handler>>,
}

impl EventBus {
    fn new() -> Self { EventBus { handlers: HashMap::new() } }

    fn on(&mut self, event: &str, h: Handler) {
        self.handlers.entry(event.to_string()).or_default().push(h);
    }

    fn emit(&self, event: &str, data: &str) {
        if let Some(hs) = self.handlers.get(event) {
            for h in hs { h(data); }
        }
    }
}
```

---

## 16. Performance & Zero-Cost Abstractions

### The Fundamental Truth

```
+------------------------------------------------------------------+
|              TYPE ALIASES ARE ZERO-COST                          |
|                                                                  |
|  type Kilometers = f64;                                          |
|  let k: Kilometers = 42.0;                                       |
|                                                                  |
|  Assembly:  movsd xmm0, [42.0]   IDENTICAL to:                   |
|                                                                  |
|  let k: f64 = 42.0;                                              |
|  Assembly:  movsd xmm0, [42.0]   same instruction!               |
|                                                                  |
|  The alias is ERASED at compile time.                            |
|  It exists only during type checking.                            |
+------------------------------------------------------------------+
```

### Compile-Time vs Runtime

```
Source:     type NodeId = usize;
            let n: NodeId = 42;
                  |
           [compile time]
                  |
           Type alias expanded
           type check: NodeId == usize OK
                  |
           [code generation]
                  |
Machine:    mov rax, 42     <-- pure usize, no trace of "NodeId"
```

---

## 17. Common Mistakes & Pitfalls

### Mistake 1: Expecting Type Safety from Aliases

```rust
// WRONG expectation:
type UserId = u64;
type PostId = u64;

fn get_user(id: UserId) -> String { format!("user_{id}") }

let post_id: PostId = 42;
get_user(post_id);   // Compiles! BUG -- no compiler error

// FIX: Use newtypes if you need safety:
struct UserId(u64);
struct PostId(u64);
// get_user(PostId(42)); // ERROR: type mismatch
```

### Mistake 2: Trying to `impl` a Type Alias

```rust
type Pair = (i32, i32);

// impl Pair {              // ERROR: cannot impl a type alias
//     fn sum(&self) -> i32 { self.0 + self.1 }
// }

// FIX:
struct Pair(i32, i32);
impl Pair {
    fn sum(&self) -> i32 { self.0 + self.1 }  // OK
}
```

### Mistake 3: Shadowing `std::result::Result`

```rust
// This shadows the standard Result in your module!
type Result<T> = std::result::Result<T, MyError>;

// Use full path if you need the original:
fn needs_std_result() -> std::result::Result<i32, String> { Ok(42) }
```

### Mistake 4: Thinking Aliases Enable New Impls (Orphan Rule)

```rust
use std::fmt;
type DebugVec = Vec<i32>;

// Cannot add Display to Vec<i32> via its alias:
// impl fmt::Display for DebugVec { ... }
// ERROR: can only impl traits from current crate on types from current crate

// FIX: Use newtype:
struct DebugVec(Vec<i32>);
impl fmt::Display for DebugVec {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self.0)
    }
}
```

---

## 18. Mental Models & Expert Intuition

### The "Vocabulary" Mental Model

Type aliases create **domain vocabulary**. When you write:

```rust
type TransactionId  = uuid::Uuid;
type AccountBalance = rust_decimal::Decimal;
type Timestamp      = chrono::DateTime<chrono::Utc>;
```

You're establishing a **shared language** between code and human reader.
The compiler speaks in `Uuid`, `Decimal`, `DateTime` — but *you* think in
`TransactionId`, `AccountBalance`, `Timestamp`.

This is **cognitive chunking** (from cognitive science): grouping related
information under a single label reduces working memory load.

### The "Layer of Abstraction" Mental Model

```
Level 3 (Business):  type Result<T> = std::result::Result<T, AppError>
                     type UserId = uuid::Uuid
                           |
                     [compile-time erasure]
                           |
Level 2 (Library):   std::result::Result<T, AppError>, uuid::Uuid
                           |
                     [compile-time erasure]
                           |
Level 1 (Primitives): u64, u8 arrays, etc.
                           |
                           v
Level 0 (Machine):   Assembly / machine code
```

### The "Contract" Mental Model for Associated Types

```
Trait = CONTRACT that says:
"Anyone who signs this contract MUST specify:
 - What their Item type is
 - How to implement next()

 In return, I (the trait) give you for FREE:
 - map(), filter(), collect(), sum(), take(), skip(), ..."

This is polymorphism through contracts.
```

### Summary Diagram: All Uses of `type`

```
+--------------------------------------------------------------+
|                THE type KEYWORD IN RUST                      |
|                                                              |
|  1. TYPE ALIAS                                               |
|     type Name = ExistingType;                                |
|     --> Readability, maintainability, DRY                    |
|     --> Zero runtime cost                                    |
|     --> No type safety (alias == original)                   |
|                                                              |
|  2. GENERIC TYPE ALIAS                                       |
|     type Name<T> = Container<T>;                             |
|     --> Partial application of generic types                 |
|     --> Shorthand for complex nested generics                |
|                                                              |
|  3. ASSOCIATED TYPE (in traits)                              |
|     trait Foo { type Bar; }                                  |
|     --> One concrete type per implementation                 |
|     --> Enables generic algorithms (Iterator, Add, etc.)     |
|                                                              |
|  4. Self TYPE                                                |
|     fn method(&self) -> Self                                 |
|     --> Refers to "the implementing type"                    |
|     --> Enables builder patterns, fluent APIs                |
|                                                              |
|  5. LIFETIME ALIASES                                         |
|     type StrRef<'a> = &'a str;                               |
|     --> Cleaner borrow expressions                           |
|     --> Useful in parsers, streaming APIs                    |
|                                                              |
|  6. ERROR RESULT ALIAS                                       |
|     type Result<T> = std::result::Result<T, MyError>;        |
|     --> Standard Rust idiom for error handling               |
|                                                              |
|  7. FFI ALIASES                                              |
|     type CInt = std::os::raw::c_int;                         |
|     --> Platform portability, safe C bindings                |
+--------------------------------------------------------------+
```

---

## Deliberate Practice Exercises

Attempt these in order — each builds on the last:

**Level 1 — Foundational**
1. Create a graph module with complete type aliases (NodeId, EdgeId, Weight, AdjList)
2. Implement `Iterator` for a Fibonacci sequence using associated type `Item = u64`

**Level 2 — Intermediate**
3. Build a unit system (Meters, Kilograms, Seconds) using both aliases AND newtypes; write a comment explaining the tradeoffs of each
4. Create a module-level `Result<T>` alias and build a multi-step parser using `?`

**Level 3 — Advanced**
5. Design a trait `Graph` with associated types `Node`, `Edge`, `Weight` — implement it for both adjacency list and adjacency matrix
6. Build a middleware pipeline using `Box<dyn Fn>` aliases (input -> transformed output)

**Level 4 — Expert**
7. Implement a type-safe state machine where state transitions are encoded using associated types and PhantomData
8. Create a zero-copy parser using lifetime-annotated type aliases

---

*"The expert doesn't just know what `type` does — they instinctively know which pattern
solves which problem. That intuition comes from deliberate practice and deep reflection
on why each design choice was made."*

Here is your comprehensive guide to the `type` keyword in Rust — 18 deep sections covering every dimension of the topic.

**What's inside, by mastery tier:**

**Foundational** — You learn that `type` is a compile-time nickname with zero runtime cost, and the 4 core reasons it exists: readability, maintainability, DRY, and API design. Every concept (generics, traits, lifetimes) is explained from scratch before being used.

**Intermediate** — Generic type aliases, the complete `Iterator`/`Add` associated type patterns, the critical `Associated Type vs Generic Parameter` decision flowchart (one of Rust's most underrated design choices), and the `Self` type for builder patterns.

**Advanced** — The Newtype Pattern tradeoff analysis, lifetime-annotated aliases for parsers, FFI bindings, closure and function pointer aliases for event-driven systems, and the idiomatic module-level `Result<T>` error pattern seen in every major crate.

**Expert** — Full Dijkstra's algorithm with a complete type-aliased graph layer, an event bus with `Box<dyn Fn>` aliases, the orphan rule interaction, and the 4 most dangerous pitfalls that trip up even experienced Rust developers.

**Key mental models to internalize:**
- Type aliases are **vocabulary** — they speak to the human, not the machine
- Associated types = **one-to-one** relationship; generic parameters = **one-to-many**
- `Self` is itself a type alias — it just points inward at the implementing type
- The alias layer disappears at codegen; only the primitive survives in machine code