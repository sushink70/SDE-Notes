# The Complete Rust Keywords Guide: From Fundamentals to Mastery

*Welcome, aspiring master. This guide is your systematic path through Rust's keyword system—the foundational vocabulary of the language. We'll build from first principles, layer by layer, with the precision of a craftsman and the insight of an architect.*

---

## Table of Contents
1. [Philosophy & Mental Model](#philosophy--mental-model)
2. [Keyword Categories: The Taxonomy](#keyword-categories-the-taxonomy)
3. [Ownership & Borrowing Keywords](#ownership--borrowing-keywords)
4. [Control Flow Keywords](#control-flow-keywords)
5. [Declaration & Definition Keywords](#declaration--definition-keywords)
6. [Type System Keywords](#type-system-keywords)
7. [Module & Visibility Keywords](#module--visibility-keywords)
8. [Pattern Matching Keywords](#pattern-matching-keywords)
9. [Async & Concurrency Keywords](#async--concurrency-keywords)
10. [Unsafe & FFI Keywords](#unsafe--ffi-keywords)
11. [Meta-programming Keywords](#meta-programming-keywords)
12. [Keyword Interactions: The Symphony](#keyword-interactions-the-symphony)
13. [Cognitive Framework for Mastery](#cognitive-framework-for-mastery)

---

## Philosophy & Mental Model

### The Rust Language Philosophy

Before diving into keywords, understand Rust's **core values** (this is crucial for building intuition):

```
┌─────────────────────────────────────────┐
│      RUST'S THREE PILLARS               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌─────────────┐     │
│  │   SAFETY    │  │ PERFORMANCE │     │
│  │             │  │             │     │
│  │ • Memory    │  │ • Zero-cost │     │
│  │ • Thread    │  │   abstract. │     │
│  │ • Type      │  │ • Control   │     │
│  └──────┬──────┘  └──────┬──────┘     │
│         │                │             │
│         └────────┬───────┘             │
│                  │                     │
│         ┌────────▼────────┐            │
│         │  PRODUCTIVITY   │            │
│         │                 │            │
│         │  • Ergonomics   │            │
│         │  • Abstraction  │            │
│         │  • Tooling      │            │
│         └─────────────────┘            │
│                                         │
└─────────────────────────────────────────┘
```

**Mental Model**: Think of Rust keywords as **specialized tools in a master craftsman's workshop**. Each has a specific purpose, but their true power emerges when combined strategically.

---

## Keyword Categories: The Taxonomy

```
RUST KEYWORDS (53 total, as of Rust 2021 Edition)
│
├─── OWNERSHIP & MEMORY (4)
│    ├─ move
│    ├─ ref
│    ├─ mut
│    └─ static
│
├─── CONTROL FLOW (11)
│    ├─ if / else
│    ├─ match
│    ├─ loop / while / for
│    ├─ break / continue
│    ├─ return
│    └─ yield (reserved)
│
├─── DECLARATIONS (8)
│    ├─ let
│    ├─ const
│    ├─ fn
│    ├─ struct / enum / union
│    ├─ type
│    └─ trait
│
├─── TYPE SYSTEM (6)
│    ├─ impl
│    ├─ dyn
│    ├─ where
│    ├─ Self / self
│    └─ super / crate
│
├─── MODULES & VISIBILITY (5)
│    ├─ mod
│    ├─ use
│    ├─ pub
│    ├─ extern
│    └─ as
│
├─── PATTERN MATCHING (2)
│    ├─ in
│    └─ _ (wildcard)
│
├─── ASYNC & CONCURRENCY (2)
│    ├─ async
│    └─ await
│
├─── UNSAFE & FFI (2)
│    ├─ unsafe
│    └─ extern
│
├─── META & SPECIAL (13)
│    ├─ macro_rules!
│    ├─ box
│    ├─ abstract / become / do / final
│    ├─ override / priv / typeof / unsized
│    ├─ virtual / try / macro / yield
│    └─ (reserved for future use)
│
└─── RESERVED (future expansion)
```

---

## Ownership & Borrowing Keywords

### **Concept Primer: What is Ownership?**

**Ownership** is Rust's solution to memory management without garbage collection. Think of it like this:

- **In C**: You manually allocate/deallocate (error-prone)
- **In Python/Go**: Garbage collector does it (runtime cost)
- **In Rust**: Compiler enforces rules at compile-time (zero runtime cost)

```
OWNERSHIP RULES (THE HOLY TRINITY)
┌────────────────────────────────────────┐
│ 1. Each value has ONE owner           │
│ 2. When owner goes out of scope,      │
│    value is dropped                    │
│ 3. Ownership can be transferred (move) │
│    or borrowed (reference)             │
└────────────────────────────────────────┘
```

---

### 1. `move` (implicit keyword)

**Purpose**: Transfer ownership from one variable to another.

**Philosophy**: "I'm handing you this resource; I no longer need it."

```rust
fn main() {
    let s1 = String::from("hello"); // s1 owns the heap data
    let s2 = s1;                     // Ownership MOVES to s2
    // println!("{}", s1);           // ❌ ERROR: s1 is now invalid
    println!("{}", s2);              // ✅ OK: s2 is the owner
}
```

**ASCII Visualization**:
```
BEFORE move:
┌────┐
│ s1 │──────► [heap: "hello"]
└────┘

AFTER let s2 = s1:
┌────┐
│ s1 │  (invalidated, no longer points anywhere)
└────┘

┌────┐
│ s2 │──────► [heap: "hello"]
└────┘
```

**When does move happen?**
- Assignment: `let y = x;`
- Function arguments: `fn take(s: String) {}`
- Return values: `return s;`

**Complexity**: O(1) — just pointer copy, not deep copy

---

### 2. `mut` (mutability)

**Purpose**: Declare that a binding can be changed.

**Philosophy**: "I need to modify this value."

```rust
fn main() {
    let x = 5;       // Immutable by default
    // x = 6;        // ❌ ERROR: cannot assign twice to immutable
    
    let mut y = 5;   // Mutable binding
    y = 6;           // ✅ OK
}
```

**Two Types of Mutability**:

```
┌─────────────────────────────────────┐
│  BINDING MUTABILITY (let mut)       │
│  vs                                 │
│  REFERENCE MUTABILITY (&mut)        │
└─────────────────────────────────────┘

let mut x = 5;     // Mutable binding
let y = &mut x;    // Mutable reference to x

const vs let:
const X: i32 = 5;  // Compile-time constant (no mut allowed)
let x = 5;         // Runtime binding (can be mut)
```

**Critical Rule**: You can have EITHER:
- One mutable reference (`&mut T`), OR
- Multiple immutable references (`&T`)

But NOT both simultaneously (prevents data races).

```rust
let mut s = String::from("hello");

let r1 = &s;      // ✅ Immutable borrow
let r2 = &s;      // ✅ Another immutable borrow
// let r3 = &mut s; // ❌ ERROR: can't borrow as mutable while immutable refs exist

println!("{} {}", r1, r2);
// r1 and r2 are no longer used after this point

let r3 = &mut s;  // ✅ OK now: no immutable refs active
r3.push_str(" world");
```

**Complexity**: Zero runtime cost — purely compile-time check

---

### 3. `ref` (pattern binding)

**Purpose**: Create a reference in pattern matching instead of moving.

**Philosophy**: "I want to inspect without taking ownership."

```rust
fn main() {
    let x = Some(String::from("hello"));
    
    // Without ref - ownership moves
    match x {
        Some(s) => println!("{}", s), // s owns the String now
        None => {}
    }
    // println!("{:?}", x); // ❌ ERROR: x was moved
    
    // With ref - creates a reference
    let y = Some(String::from("world"));
    match y {
        Some(ref s) => println!("{}", s), // s is &String
        None => {}
    }
    println!("{:?}", y); // ✅ OK: y still owns its data
}
```

**When to use**:
- Pattern matching where you don't want to move
- Often replaced by `&` in modern Rust:

```rust
// Old style
match &y {
    Some(ref s) => {},
    None => {}
}

// Modern style (equivalent)
match &y {
    Some(s) => {},  // s is automatically &String
    None => {}
}
```

---

### 4. `static` (lifetime)

**Purpose**: Declare a variable/reference that lives for the **entire program duration**.

**Concept Primer - Lifetimes**: A lifetime is how long a reference is valid.

```
LIFETIME HIERARCHY
┌──────────────────────────────┐
│ 'static (entire program)     │
│    ↑                          │
│    │ outlives                 │
│    │                          │
│ 'a (some scope)               │
│    ↑                          │
│    │                          │
│ 'b (nested scope)             │
└──────────────────────────────┘
```

**Two uses of `static`**:

```rust
// 1. Static variable (rare, mutable statics are unsafe)
static HELLO: &str = "Hello, world!";  // Lives forever, embedded in binary

// 2. Static lifetime annotation
fn return_str() -> &'static str {
    "I live forever"  // String literals have 'static lifetime
}

// 3. Static in trait bounds
fn print_forever<T: std::fmt::Display + 'static>(x: T) {
    // T must not contain any non-static references
}
```

**Memory Layout**:
```
┌─────────────────────────────────┐
│  PROGRAM BINARY                 │
├─────────────────────────────────┤
│  [Code Section]                 │
│  [Data Section]                 │
│    ├─ static HELLO = "..."      │ ← Lives here
│  [BSS Section]                  │
├─────────────────────────────────┤
│  STACK (function calls)         │ ← Temporary variables
├─────────────────────────────────┤
│  HEAP (dynamic allocation)      │ ← Box, Vec, String
└─────────────────────────────────┘
```

**Warning**: Mutable statics require `unsafe`:
```rust
static mut COUNTER: i32 = 0;

unsafe {
    COUNTER += 1;  // Can cause data races!
}
```

---

## Control Flow Keywords

### **Concept: Control Flow**
Control flow determines the **order** in which code executes. Think of it as the "logic gates" of your program.

```
CONTROL FLOW TYPES
┌─────────────────────────────┐
│ Sequential   (line by line) │
│ Conditional  (if/match)     │
│ Iterative    (loop/while)   │
│ Jump         (break/return) │
└─────────────────────────────┘
```

---

### 5. `if` / `else`

**Purpose**: Conditional branching.

**Philosophy**: "Choose a path based on a condition."

```rust
fn main() {
    let number = 6;
    
    // if is an EXPRESSION (returns a value)
    let description = if number % 2 == 0 {
        "even"
    } else {
        "odd"
    };
    
    println!("{} is {}", number, description);
}
```

**Key Insight**: `if` in Rust is an **expression**, not just a statement!

```rust
// This is valid Rust:
let x = if true { 5 } else { 6 };

// Python/C equivalent would require:
// x = 5 if True else 6
```

**Flowchart**:
```
     START
       │
       ▼
   ┌─────────┐
   │condition│
   └────┬────┘
        │
   ┌────┴────┐
   │         │
  YES       NO
   │         │
   ▼         ▼
┌────┐    ┌────┐
│ if │    │else│
│block│   │block│
└─┬──┘    └─┬──┘
  │         │
  └────┬────┘
       │
       ▼
      END
```

**Complexity**: O(1) for the branch itself

---

### 6. `match` (pattern matching)

**Purpose**: Powerful pattern-based control flow.

**Concept Primer - Pattern Matching**: Instead of just comparing values, you **destructure** and **match structure**.

```rust
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter(String), // Quarter has associated data (state name)
}

fn value_in_cents(coin: Coin) -> u8 {
    match coin {
        Coin::Penny => 1,
        Coin::Nickel => 5,
        Coin::Dime => 10,
        Coin::Quarter(state) => {
            println!("Quarter from {}!", state);
            25
        }
    }
}
```

**Match is exhaustive** — you MUST handle all cases:

```rust
let x: Option<i32> = Some(5);

match x {
    Some(val) => println!("Got: {}", val),
    None => println!("Got nothing"),
}

// This would ERROR:
// match x {
//     Some(val) => println!("Got: {}", val),
//     // ❌ Missing None case!
// }
```

**Pattern Types**:
```
PATTERN MATCHING CAPABILITIES
┌────────────────────────────────────┐
│ • Literals:       match x { 1 => }│
│ • Ranges:         match x { 1..=5 }│
│ • Destructuring:  match p { Point{x, y} }│
│ • Guards:         match x { n if n > 5 }│
│ • Multiple:       match x { 1 | 2 | 3 }│
│ • Wildcard:       match x { _ => }│
│ • Ref:            match x { ref r => }│
└────────────────────────────────────┘
```

**Decision Tree** (for match with guards):
```
       match x
         │
    ┌────┴────┬────────┬─────────┐
    │         │        │         │
  Pattern1  Pattern2  Pattern3  _
    │         │        │         │
   Guard?    Guard?    │        │
  │    │    │    │     │        │
 YES  NO   YES  NO    Exec    Exec
  │    │    │    │     │        │
 Exec Continue        │        │
       │              │        │
       └──────┬───────┴────────┘
              │
             END
```

**Complexity**: O(1) typically, but depends on guard complexity

---

### 7. `loop` / `while` / `for`

**Three iteration primitives**, each with a specific use case:

#### **`loop` — Infinite loop with explicit exit**

```rust
let mut count = 0;

let result = loop {
    count += 1;
    
    if count == 10 {
        break count * 2;  // loop can return a value!
    }
};

println!("Result: {}", result); // 20
```

**When to use**: When you don't know iteration count upfront.

---

#### **`while` — Condition-based loop**

```rust
let mut n = 0;

while n < 10 {
    println!("{}", n);
    n += 1;
}
```

**Equivalent to**:
```rust
loop {
    if !(n < 10) {
        break;
    }
    println!("{}", n);
    n += 1;
}
```

**When to use**: When you have a clear boolean condition.

---

#### **`for` — Iterator-based loop**

```rust
for i in 0..10 {  // Range: [0, 10)
    println!("{}", i);
}

let vec = vec![1, 2, 3];
for val in &vec {  // Iterate by reference
    println!("{}", val);
}
```

**What is an Iterator?** An object that yields elements one at a time.

```
ITERATOR TRAIT (simplified)
┌────────────────────────────┐
│ trait Iterator {           │
│     type Item;             │
│     fn next(&mut self)     │
│         -> Option<Item>;   │
│ }                          │
└────────────────────────────┘

 next() → Some(value) → Some(value) → None
   │         │              │           │
  Start     Item1         Item2        End
```

**Three Ways to Iterate**:
```rust
let v = vec![1, 2, 3];

// 1. Consume (move)
for val in v {          // v is moved
    // val is i32
}
// v is no longer valid here

// 2. Borrow immutably
for val in &v {         // Borrow v
    // val is &i32
}

// 3. Borrow mutably
for val in &mut v {     // Mutable borrow
    *val += 1;          // val is &mut i32
}
```

**Performance Comparison**:
```
LOOP PERFORMANCE (compiler optimizations make these equivalent)
┌──────────────────────────────────────┐
│ for i in 0..n         → Very fast    │
│ while i < n           → Very fast    │
│ loop { if i >= n }    → Very fast    │
│                                      │
│ All compile to same machine code!   │
└──────────────────────────────────────┘
```

---

### 8. `break` / `continue`

**Purpose**: Control loop execution.

- **`break`**: Exit the loop immediately
- **`continue`**: Skip to next iteration

```rust
for i in 0..10 {
    if i == 3 {
        continue;  // Skip printing 3
    }
    if i == 7 {
        break;     // Stop at 7
    }
    println!("{}", i);  // Prints: 0,1,2,4,5,6
}
```

**Loop Labels** (advanced):
```rust
'outer: for i in 0..3 {
    for j in 0..3 {
        if i == 1 && j == 1 {
            break 'outer;  // Break outer loop!
        }
        println!("({}, {})", i, j);
    }
}
```

**Flowchart**:
```
    ┌─────────────┐
    │   for i     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  i == 3?    │
    └──┬───────┬──┘
      YES     NO
       │       │
    continue  │
       │       │
       │  ┌────▼────┐
       │  │ i == 7? │
       │  └─┬─────┬─┘
       │   YES   NO
       │    │     │
       │  break  │
       │         │
       └─────┬───┴──► print(i)
             │
          Next iteration or End
```

---

### 9. `return`

**Purpose**: Exit a function and optionally return a value.

```rust
fn add(a: i32, b: i32) -> i32 {
    return a + b;  // Explicit return
}

// Idiomatic Rust (implicit return):
fn add_idiomatic(a: i32, b: i32) -> i32 {
    a + b  // No semicolon = expression value is returned
}
```

**Early return pattern**:
```rust
fn process(x: Option<i32>) -> i32 {
    let val = match x {
        Some(v) => v,
        None => return 0,  // Early exit
    };
    
    val * 2
}
```

**Complexity**: O(1) — just stack unwinding

---

## Declaration & Definition Keywords

### 10. `let` (variable binding)

**Purpose**: Bind a value to a name.

**Philosophy**: "Give this value a name in this scope."

```rust
fn main() {
    let x = 5;              // Type inferred: i32
    let y: u32 = 10;        // Explicit type annotation
    let (a, b) = (1, 2);    // Destructuring tuple
    
    // Pattern matching in let
    let Point { x: px, y: py } = Point { x: 1, y: 2 };
}
```

**Shadowing vs Mutation**:
```rust
// Shadowing (creates NEW binding)
let x = 5;
let x = x + 1;  // New x shadows old x
let x = "hello"; // Different type OK!

// Mutation (changes EXISTING binding)
let mut y = 5;
y = y + 1;      // Same binding, modified
// y = "hello";  // ❌ ERROR: type must stay same
```

**Scope visualization**:
```
fn main() {
    let x = 1;           // ─────┐
    {                    //      │ x scope
        let y = 2;       // ──┐  │
        println!("{}", x);//  │  │ y scope
    }                    // ──┘  │
    // y is dropped here        │
    println!("{}", x);   //      │
}                        // ─────┘
// x is dropped here
```

---

### 11. `const` (compile-time constant)

**Purpose**: Define a value computed at **compile-time**.

**Difference from `let`**:
```
┌────────────────────────────────────┐
│  const vs static vs let            │
├────────────────────────────────────┤
│ const:  compile-time, inlined      │
│ static: runtime, fixed address     │
│ let:    runtime, stack/heap        │
└────────────────────────────────────┘
```

```rust
const MAX_POINTS: u32 = 100_000;  // Must have type annotation

fn main() {
    const THRESHOLD: i32 = MAX_POINTS as i32 / 2;
    // Computed at compile-time!
    
    println!("{}", THRESHOLD);
}
```

**Rules**:
1. Must have type annotation
2. Must be assigned a constant expression
3. Can be declared in any scope (including global)
4. No `mut` allowed (always immutable)

**When each value is computed**:
```
const X: i32 = 5 + 5;     // Compile-time (replaced by 10 in binary)
static Y: i32 = 5 + 5;    // Compile-time, stored at fixed address
let z = 5 + 5;            // Runtime (though optimizer may compute)
```

---

### 12. `fn` (function)

**Purpose**: Define a callable unit of code.

```rust
// Basic function
fn add(a: i32, b: i32) -> i32 {
    a + b  // Last expression is return value
}

// No return value (returns unit type ())
fn print_hello() {
    println!("Hello!");
}  // Implicitly returns ()

// Generic function
fn largest<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

**Function signature anatomy**:
```
fn function_name<Generics>(param: Type) -> ReturnType where Bounds
│  │            │          │             │  │
│  │            │          │             │  └─ Return type
│  │            │          │             └──── Arrow (required if returning non-())
│  │            │          └──────────────── Parameters
│  │            └─────────────────────────── Generic type parameters
│  └──────────────────────────────────────── Name (snake_case convention)
└─────────────────────────────────────────── fn keyword
```

**Associated functions** (methods):
```rust
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    // Associated function (no self)
    fn new(x: i32, y: i32) -> Point {
        Point { x, y }
    }
    
    // Method (takes self)
    fn distance_from_origin(&self) -> f64 {
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
}

let p = Point::new(3, 4);      // Call associated function
let d = p.distance_from_origin(); // Call method
```

**Self types**:
```rust
impl Point {
    fn consume(self) {}         // Takes ownership
    fn borrow(&self) {}         // Borrows immutably
    fn borrow_mut(&mut self) {} // Borrows mutably
}
```

---

### 13. `struct` (product type)

**Concept Primer - Product Type**: A data structure that **combines multiple fields**.

```rust
// Named fields
struct User {
    username: String,
    email: String,
    sign_in_count: u64,
}

// Tuple struct
struct Point(i32, i32, i32);

// Unit struct (no fields)
struct Marker;
```

**Three struct flavors**:
```
┌────────────────────────────────────┐
│ STRUCT TYPES                       │
├────────────────────────────────────┤
│ Named:  struct Point { x: i32 }   │
│ Tuple:  struct Point(i32, i32)    │
│ Unit:   struct Marker;             │
└────────────────────────────────────┘
```

**Memory layout** (named struct):
```
User {
    username: String,    // 24 bytes (ptr + len + cap)
    email: String,       // 24 bytes
    sign_in_count: u64,  // 8 bytes
}
Total: 56 bytes (+ padding for alignment)

Memory:
┌──────────────────────────────┐
│ username: [ptr][len][cap]    │ 24 bytes
├──────────────────────────────┤
│ email:    [ptr][len][cap]    │ 24 bytes
├──────────────────────────────┤
│ sign_in_count: [u64]         │ 8 bytes
└──────────────────────────────┘
```

**Update syntax**:
```rust
let user1 = User {
    email: String::from("a@example.com"),
    username: String::from("alice"),
    sign_in_count: 1,
};

let user2 = User {
    email: String::from("b@example.com"),
    ..user1  // Copy remaining fields from user1
};
```

---

### 14. `enum` (sum type)

**Concept Primer - Sum Type**: A type that can be **one of several variants**.

```rust
enum Message {
    Quit,                       // No data
    Move { x: i32, y: i32 },   // Named fields
    Write(String),              // Tuple variant
    ChangeColor(i32, i32, i32), // Multiple values
}
```

**Why enums are powerful**: They enforce handling all cases at compile-time.

```rust
fn process_message(msg: Message) {
    match msg {
        Message::Quit => println!("Quit"),
        Message::Move { x, y } => println!("Move to ({}, {})", x, y),
        Message::Write(text) => println!("Text: {}", text),
        Message::ChangeColor(r, g, b) => println!("Color: ({},{},{})", r, g, b),
    }
}
```

**Option and Result** (most important enums):
```rust
// Option<T> - represents optional value
enum Option<T> {
    Some(T),
    None,
}

// Result<T, E> - represents success or error
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

**Memory layout** (enum):
```
enum Message {
    Quit,           // 0 bytes data
    Move { x: i32, y: i32 },  // 8 bytes data
    Write(String),  // 24 bytes data
}

Memory layout:
┌─────────────────────────────┐
│ [discriminant: 1 byte]      │ ← Which variant?
│ [data: 24 bytes]            │ ← Largest variant size
│ [padding: may vary]         │
└─────────────────────────────┘
Total: ~32 bytes (depends on alignment)
```

---

I'll continue with the remaining sections. Would you like me to proceed with:
- Type System Keywords (impl, dyn, where, Self, etc.)
- Module & Visibility Keywords
- Pattern Matching Keywords
- Async & Concurrency
- Unsafe & FFI
- Meta-programming
- Keyword Interactions (how they compose)
- Cognitive Framework for Mastery

Each section will maintain this same depth with visualizations, examples in Rust, complexity analysis, and mental models. Should I continue?

# Multi-Purpose Rust Keywords: The Polymorphic Core

*Excellent observation, seeker. This is where your understanding deepens from surface syntax to true mastery. Some keywords are **context-dependent polymorphs**—they shift meaning based on where and how they appear. Let's dissect each one with surgical precision.*

---

## The Philosophy of Keyword Overloading

**Mental Model**: Think of these keywords like **homonyms in natural language**—same spelling, different meanings based on context. But unlike human language, the compiler ALWAYS knows which meaning applies.

```
CONTEXT-SENSITIVE KEYWORDS
┌─────────────────────────────────────────┐
│ Keyword │ Contexts │ Purpose Shift      │
├─────────┼──────────┼────────────────────┤
│ static  │    3     │ lifetime/storage   │
│ use     │    3     │ import/trait/scope │
│ impl    │    2     │ type/trait         │
│ as      │    3     │ cast/rename/trait  │
│ mut     │    2     │ binding/reference  │
│ Self    │    2     │ type/constructor   │
│ self    │    4     │ receiver/module    │
│ _       │    3     │ wildcard/ignore    │
│ type    │    2     │ alias/associated   │
│ extern  │    3     │ FFI/crate/ABI      │
│ unsafe  │    2     │ block/trait/fn     │
└─────────┴──────────┴────────────────────┘
```

---

## 1. `static` — The Triple Personality

### Context 1: Static Lifetime Annotation

**Purpose**: Denotes a reference that lives for the entire program duration.

```rust
// String literals have 'static lifetime
fn get_message() -> &'static str {
    "This string is embedded in the binary"
}

// Function that requires static lifetime
fn store_forever<T: 'static>(value: T) {
    // T must not contain any non-static references
}
```

**What does `'static` really mean?**

```
LIFETIME RELATIONSHIPS
┌────────────────────────────────────┐
│ 'static: ════════════════════════  │ (entire program)
│                                    │
│ 'a:      ═══════                   │ (some scope)
│                                    │
│ 'b:        ═══                     │ (nested scope)
│                                    │
│ Rule: 'static outlives all others  │
└────────────────────────────────────┘
```

**Practical example**:
```rust
struct Config {
    name: &'static str,  // Must point to data that lives forever
}

// Valid: string literal
const CONFIG: Config = Config {
    name: "AppName",  // ✅ String literals are 'static
};

// Invalid: local reference
fn create_config() -> Config {
    let temp = String::from("temp");
    Config {
        name: &temp,  // ❌ ERROR: temp doesn't live long enough
    }
}
```

---

### Context 2: Static Variable Declaration

**Purpose**: Declare a global variable with a fixed memory address.

```rust
// Immutable static (safe)
static LANGUAGE: &str = "Rust";

// Mutable static (unsafe - can cause data races)
static mut COUNTER: i32 = 0;

fn increment() {
    unsafe {
        COUNTER += 1;  // Requires unsafe because concurrent access is UB
    }
}
```

**Memory location**:
```
PROGRAM MEMORY LAYOUT
┌────────────────────────────┐
│ TEXT SEGMENT (code)        │
├────────────────────────────┤
│ RODATA (read-only data)    │
│   ├─ static LANGUAGE       │ ← Immutable statics here
├────────────────────────────┤
│ DATA SEGMENT               │
│   ├─ static mut COUNTER    │ ← Mutable statics here
├────────────────────────────┤
│ BSS (uninitialized)        │
├────────────────────────────┤
│ HEAP (dynamic)             │
├────────────────────────────┤
│ STACK (local vars)         │
└────────────────────────────┘
```

**Key differences**:
```rust
// Static: ONE instance, fixed address
static X: i32 = 5;
fn foo() {
    println!("{:p}", &X);  // Always same address
}

// Const: INLINED at each use site
const Y: i32 = 5;
fn bar() {
    println!("{:p}", &Y);  // May be different addresses!
}
```

**Rule of thumb**:
- Use `const` for values (will be inlined)
- Use `static` for locations (single memory address)

---

### Context 3: Static in Trait Bounds

**Purpose**: Constrain a generic type to contain no non-static references.

```rust
// T must not contain any borrowed data with lifetime < 'static
fn spawn_thread<T: Send + 'static>(value: T) {
    std::thread::spawn(move || {
        // value is moved into thread
        // If T had non-static refs, they could become invalid!
    });
}

// Example usage
fn example() {
    let owned = String::from("owned");
    spawn_thread(owned);  // ✅ String is 'static (no references)
    
    let borrowed = "borrowed";
    let reference = &borrowed;
    // spawn_thread(reference);  // ❌ ERROR: &str is not 'static here
    
    let static_ref: &'static str = "static";
    spawn_thread(static_ref);  // ✅ This reference IS 'static
}
```

**Why is this needed?**

```
THREAD LIFETIME PROBLEM (without 'static bound)
┌────────────────────────────────────────┐
│ Main Thread          │ Spawned Thread  │
├──────────────────────┼─────────────────┤
│ let x = String {...} │                 │
│ let r = &x;          │                 │
│ spawn(|| {           │                 │
│    // use r          │  accesses r  ←──┼─ DANGER!
│ });                  │                 │
│ drop(x);  ← freed!   │  r now invalid! │
│                      │  💥 USE AFTER FREE│
└──────────────────────┴─────────────────┘

WITH 'static BOUND:
┌────────────────────────────────────────┐
│ Main Thread          │ Spawned Thread  │
├──────────────────────┼─────────────────┤
│ let x = String {...} │                 │
│ spawn(move || {      │                 │
│    // owns x         │  x is moved  ←──┼─ SAFE
│ });                  │  has ownership  │
│ // x no longer valid │                 │
└──────────────────────┴─────────────────┘
```

**Decision tree for `'static`**:
```
                Is this 'static?
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   String literal?  Owned type?   Reference?
        │              │              │
       YES            YES             NO*
        │              │              │
    'static        'static     (lifetime depends
                                 on source data)

*Unless explicitly marked &'static
```

---

## 2. `use` — The Triple Importer

### Context 1: Bringing Items into Scope

**Purpose**: Import types, functions, modules from other namespaces.

```rust
// Import from standard library
use std::collections::HashMap;

// Import multiple items
use std::io::{self, Read, Write};

// Import with wildcard (glob)
use std::collections::*;  // Brings all public items

// Nested imports (Rust 2018+)
use std::{
    fs::File,
    io::prelude::*,
    path::PathBuf,
};
```

**Scope visualization**:
```
WITHOUT use:
┌────────────────────────────────────────┐
│ fn main() {                            │
│     let map: std::collections::HashMap │
│                     ↑                  │
│              Fully qualified path      │
│ }                                      │
└────────────────────────────────────────┘

WITH use:
┌────────────────────────────────────────┐
│ use std::collections::HashMap;         │
│                                        │
│ fn main() {                            │
│     let map: HashMap  ← Short name!    │
│ }                                      │
└────────────────────────────────────────┘
```

---

### Context 2: Re-exporting (Pub Use)

**Purpose**: Make an item from a submodule available at current level.

```rust
// lib.rs
mod internal {
    pub struct Secret {
        data: String,
    }
}

// Re-export for public API
pub use internal::Secret;

// Users can now:
// use my_crate::Secret;
// Instead of:
// use my_crate::internal::Secret;
```

**API design pattern**:
```
BEFORE (cluttered):
┌─────────────────────────┐
│ my_crate                │
│  ├─ parsers             │
│  │   ├─ json            │
│  │   │   └─ JsonParser  │
│  │   └─ xml             │
│  │       └─ XmlParser   │
│  └─ ...                 │
└─────────────────────────┘

User must write:
use my_crate::parsers::json::JsonParser;

AFTER (clean API):
┌─────────────────────────┐
│ my_crate (lib.rs)       │
│  pub use parsers::{     │
│      json::JsonParser,  │
│      xml::XmlParser,    │
│  };                     │
└─────────────────────────┘

User can write:
use my_crate::{JsonParser, XmlParser};
```

**Real-world example** (std library does this):
```rust
// std::io module re-exports
pub use self::buffered::{BufReader, BufWriter};
pub use self::copy::copy;
// etc.

// So you can write:
use std::io::BufReader;
// Instead of:
use std::io::buffered::BufReader;
```

---

### Context 3: Trait Method Disambiguation (Use as Trait Bound)

**Purpose**: Bring trait methods into scope.

```rust
// Without use, trait methods aren't available
fn example() {
    let s = "hello";
    // s.lines();  // ❌ ERROR: no method named `lines`
}

// With use
use std::io::BufRead;

fn example2() {
    let s = "hello";
    // Still need the trait in scope to call its methods
}
```

**Key concept**: Traits must be in scope to use their methods!

```rust
trait MyTrait {
    fn my_method(&self);
}

impl MyTrait for String {
    fn my_method(&self) {
        println!("Called!");
    }
}

mod other {
    pub fn call_it() {
        let s = String::from("test");
        // s.my_method();  // ❌ ERROR: MyTrait not in scope!
    }
}

mod correct {
    use super::MyTrait;  // ← Must bring trait into scope
    
    pub fn call_it() {
        let s = String::from("test");
        s.my_method();  // ✅ OK now
    }
}
```

**Orphan rule context**:
```
TRAIT METHOD RESOLUTION
┌──────────────────────────────────┐
│ 1. Is trait in scope?            │
│    ├─ NO → Compilation error     │
│    └─ YES → Continue             │
│                                  │
│ 2. Does type implement trait?    │
│    ├─ NO → Compilation error     │
│    └─ YES → Call method          │
└──────────────────────────────────┘
```

---

## 3. `impl` — The Dual Implementor

### Context 1: Inherent Implementation

**Purpose**: Define methods directly on a type.

```rust
struct Point {
    x: i32,
    y: i32,
}

// Inherent impl - methods specific to Point
impl Point {
    // Associated function (no self)
    pub fn new(x: i32, y: i32) -> Self {
        Point { x, y }
    }
    
    // Method (takes self)
    pub fn distance_from_origin(&self) -> f64 {
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
    
    // Mutable method
    pub fn translate(&mut self, dx: i32, dy: i32) {
        self.x += dx;
        self.y += dy;
    }
    
    // Consuming method
    pub fn into_tuple(self) -> (i32, i32) {
        (self.x, self.y)
    }
}

// Usage
let mut p = Point::new(3, 4);       // Associated function
let d = p.distance_from_origin();   // Immutable method
p.translate(1, 1);                  // Mutable method
let (x, y) = p.into_tuple();        // Consuming method (p moved)
```

**Self parameter variants**:
```
METHOD RECEIVER TYPES
┌────────────────────────────────────────┐
│ Signature        │ Ownership │ Usage   │
├──────────────────┼───────────┼─────────┤
│ fn f(self)       │ Move      │ Consume │
│ fn f(&self)      │ Borrow    │ Read    │
│ fn f(&mut self)  │ Mut borrow│ Modify  │
│ fn f(self: Box)  │ Smart ptr │ Special │
└────────────────────────────────────────┘
```

---

### Context 2: Trait Implementation

**Purpose**: Implement a trait for a type.

```rust
// Define a trait
trait Drawable {
    fn draw(&self);
    
    // Default implementation
    fn describe(&self) {
        println!("This is drawable");
    }
}

// Implement trait for Point
impl Drawable for Point {
    fn draw(&self) {
        println!("Drawing point at ({}, {})", self.x, self.y);
    }
    
    // Can override default methods
    fn describe(&self) {
        println!("Point at ({}, {})", self.x, self.y);
    }
}
```

**Syntax comparison**:
```rust
// Inherent impl
impl Point {
    fn new() -> Self { ... }
}

// Trait impl
impl Drawable for Point {
    fn draw(&self) { ... }
}

// Generic trait impl
impl<T> Display for Wrapper<T>
where
    T: Display,
{
    fn fmt(&self, f: &mut Formatter) -> Result { ... }
}
```

**Method resolution order**:
```
METHOD CALL: point.method()
       │
       ▼
┌─────────────────────────────┐
│ 1. Check inherent methods   │
│    (impl Point { ... })     │
├─────────────────────────────┤
│ 2. Check trait methods      │
│    (impl Trait for Point)   │
│    - Must be in scope!      │
├─────────────────────────────┤
│ 3. Check deref coercion     │
│    (if type implements      │
│     Deref, try target type) │
└─────────────────────────────┘
```

**Orphan rule** (critical for trait impls):
```
ORPHAN RULE: WHERE CAN YOU IMPLEMENT TRAITS?
┌────────────────────────────────────────────┐
│ impl Trait for Type                        │
│                                            │
│ At least ONE must be local to your crate: │
│  • The trait, OR                           │
│  • The type                                │
│                                            │
│ Examples:                                  │
│ ✅ impl MyTrait for Vec<i32>   (local tr) │
│ ✅ impl Display for MyType     (local ty) │
│ ❌ impl Display for Vec<i32>   (both ext) │
│                                            │
│ Why? Prevents conflicting impls across    │
│ crates (coherence).                        │
└────────────────────────────────────────────┘
```

---

## 4. `as` — The Triple Converter

### Context 1: Type Casting

**Purpose**: Convert between primitive types or perform pointer casts.

```rust
fn main() {
    // Numeric casting
    let x: i32 = 10;
    let y: i64 = x as i64;     // Widening cast (safe)
    let z: i8 = y as i8;       // Narrowing cast (may truncate!)
    
    // Floating point
    let f: f64 = 3.14;
    let i: i32 = f as i32;     // Truncates to 3
    
    // Pointer casting (unsafe)
    let ptr = &x as *const i32;         // Reference to raw pointer
    let mut_ptr = &mut x as *mut i32;   // Mutable raw pointer
}
```

**Casting rules**:
```
SAFE CASTS (implicit or explicit)
┌────────────────────────────────────┐
│ • Numeric widening (i32 → i64)     │
│ • &T → *const T                    │
│ • &mut T → *mut T                  │
│ • *mut T → *const T                │
└────────────────────────────────────┘

POTENTIALLY UNSAFE
┌────────────────────────────────────┐
│ • Numeric narrowing (i64 → i32)    │
│   - May truncate/overflow          │
│ • Float → Int (loses precision)    │
│ • Pointer casts (advanced)         │
└────────────────────────────────────┘
```

**Practical example**:
```rust
fn process_byte(value: u32) {
    // Safe: widening
    let wide: u64 = value as u64;
    
    // Unsafe: narrowing - may lose data
    let narrow: u8 = value as u8;  // Only keeps lowest 8 bits
    
    // Example: value = 300 (0x012C)
    // narrow becomes 44 (0x2C) - truncated!
}
```

**Decision tree**:
```
        as cast
           │
    ┌──────┴──────┐
    │             │
 Numeric      Pointer
    │             │
 ┌──┴──┐      ┌──┴──┐
 │     │      │     │
Widen Narrow  Safe Transmute
 │     │      │     │
Safe  Check  Safe  Unsafe
     overflow     context
```

---

### Context 2: Renaming Imports

**Purpose**: Avoid name conflicts when importing.

```rust
// Two types with same name
use std::fmt::Result as FmtResult;
use std::io::Result as IoResult;

fn format_data() -> FmtResult {
    // Use fmt::Result
    Ok(())
}

fn read_file() -> IoResult<String> {
    // Use io::Result
    Ok(String::new())
}
```

**Common pattern**:
```rust
// Long type names
use std::collections::HashMap as Map;

// Conflicting names from different modules
mod parser {
    pub struct Token;
}
mod lexer {
    pub struct Token;
}

use parser::Token as ParseToken;
use lexer::Token as LexToken;
```

**Without `as` (error)**:
```rust
use std::fmt::Result;
use std::io::Result;  // ❌ ERROR: Result is defined multiple times

fn foo() -> Result { ... }  // Which Result???
```

---

### Context 3: Trait Disambiguation (Qualified Syntax)

**Purpose**: Specify which trait's method to call when ambiguous.

```rust
trait Pilot {
    fn fly(&self);
}

trait Wizard {
    fn fly(&self);
}

struct Human;

impl Pilot for Human {
    fn fly(&self) {
        println!("Captain speaking.");
    }
}

impl Wizard for Human {
    fn fly(&self) {
        println!("Up on my broomstick!");
    }
}

impl Human {
    fn fly(&self) {
        println!("*waving arms*");
    }
}

fn main() {
    let person = Human;
    
    // Calls inherent method
    person.fly();  // *waving arms*
    
    // Disambiguate with trait
    Pilot::fly(&person);   // Captain speaking.
    Wizard::fly(&person);  // Up on my broomstick!
    
    // Fully qualified syntax (most explicit)
    <Human as Pilot>::fly(&person);   // Captain speaking.
    <Human as Wizard>::fly(&person);  // Up on my broomstick!
}
```

**Fully qualified syntax anatomy**:
```
<Type as Trait>::method(receiver, args)
 │     │  │      │       │
 │     │  │      │       └─ Explicit receiver
 │     │  │      └───────── Method name
 │     │  └──────────────── Trait name
 │     └─────────────────── "as" keyword
 └───────────────────────── Type implementing trait
```

**When is this needed?**

```
AMBIGUITY SCENARIOS
┌────────────────────────────────────┐
│ 1. Multiple traits with same       │
│    method name                     │
│                                    │
│ 2. Associated functions (no self)  │
│    that conflict                   │
│                                    │
│ 3. Inherent vs trait methods with  │
│    same name                       │
└────────────────────────────────────┘

Resolution without receiver:
┌────────────────────────────────────┐
│ trait Animal {                     │
│     fn baby_name() -> String;      │
│ }                                  │
│                                    │
│ struct Dog;                        │
│                                    │
│ impl Dog {                         │
│     fn baby_name() -> String {     │
│         String::from("puppy")      │
│     }                              │
│ }                                  │
│                                    │
│ impl Animal for Dog {              │
│     fn baby_name() -> String {     │
│         String::from("doggy")      │
│     }                              │
│ }                                  │
│                                    │
│ // Must use fully qualified:       │
│ <Dog as Animal>::baby_name()       │
└────────────────────────────────────┘
```

---

## 5. `mut` — The Dual Mutability

### Context 1: Mutable Binding

**Purpose**: Allow rebinding/reassignment of a variable.

```rust
fn main() {
    let x = 5;
    // x = 6;  // ❌ ERROR: cannot assign twice to immutable
    
    let mut y = 5;  // Mutable binding
    y = 6;          // ✅ OK
    y = 7;          // ✅ OK - can reassign multiple times
}
```

**Binding mutability does NOT mean interior mutability**:
```rust
let mut x = 5;
x = 10;  // ✅ Can change binding

let y = vec![1, 2, 3];
// y.push(4);  // ❌ ERROR: cannot borrow as mutable

let mut z = vec![1, 2, 3];
z.push(4);  // ✅ Can mutate the Vec
```

---

### Context 2: Mutable Reference

**Purpose**: Borrow a value with permission to modify it.

```rust
fn main() {
    let mut s = String::from("hello");
    
    // Mutable borrow
    let r = &mut s;
    r.push_str(" world");  // Can modify through reference
    
    println!("{}", s);  // "hello world"
}
```

**Critical rule**: Exclusive access (one writer OR many readers)

```
BORROWING RULES
┌────────────────────────────────────────┐
│ At any given time, you can have:      │
│                                        │
│ EITHER:                                │
│  • One mutable reference (&mut T)     │
│                                        │
│ OR:                                    │
│  • Any number of immutable refs (&T)  │
│                                        │
│ BUT NOT BOTH                           │
└────────────────────────────────────────┘
```

**Examples of violations**:
```rust
let mut s = String::from("hello");

let r1 = &s;      // ✅ Immutable borrow
let r2 = &s;      // ✅ Another immutable borrow
let r3 = &mut s;  // ❌ ERROR: can't borrow as mutable while immutable refs exist

println!("{} {}", r1, r2);  // Last use of r1, r2
let r4 = &mut s;  // ✅ OK now: r1, r2 no longer used (NLL)
```

**Non-Lexical Lifetimes (NLL)** visualization:
```
fn main() {
    let mut s = String::from("hello");
    
    let r1 = &s;     // ─────┐ r1 lifetime starts
    let r2 = &s;     // ──┐  │ r2 lifetime starts
    println!("{} {}", r1, r2); // │  │
                     //    │  │
                     // ───┴──┘ r1, r2 lifetimes END here
    
    let r3 = &mut s; // ✅ OK: no active immutable refs
    r3.push_str(" world");
}
```

---

### Binding Mutability vs Reference Mutability (Key Distinction)

```rust
// Four combinations:

// 1. Immutable binding, immutable reference
let x = 5;
let r = &x;
// x = 10;      // ❌ Cannot reassign
// *r = 10;     // ❌ Cannot mutate through reference

// 2. Mutable binding, immutable reference
let mut y = 5;
let r = &y;
y = 10;         // ✅ Can reassign binding (after r is done)
// *r = 10;     // ❌ Cannot mutate through immutable reference

// 3. Immutable binding, mutable reference
let mut z = 5;
let z_immut = z;  // Move to immutable binding
// let r = &mut z_immut;  // ❌ Cannot take mutable ref of immutable

// 4. Mutable binding, mutable reference
let mut w = 5;
let r = &mut w;
*r = 10;        // ✅ Can mutate through reference
// w = 15;      // ❌ Cannot use w while mutably borrowed
```

**Visual model**:
```
MUTABILITY LAYERS
┌────────────────────────────────────┐
│         BINDING                    │
│    ┌─────────────────┐             │
│    │ let mut x = ... │ ← Can reassign x
│    └─────────────────┘             │
│            │                        │
│            ▼                        │
│    ┌─────────────────┐             │
│    │   REFERENCE     │             │
│    │   let r = &mut  │ ← Can mutate *r
│    └─────────────────┘             │
│            │                        │
│            ▼                        │
│    ┌─────────────────┐             │
│    │   THE DATA      │             │
│    └─────────────────┘             │
└────────────────────────────────────┘
```

---

## 6. `Self` vs `self` — The Identity Twins

### `Self` (Type Alias)

**Purpose**: Refers to the type currently being implemented.

```rust
struct Builder {
    value: i32,
}

impl Builder {
    // Self = Builder
    fn new() -> Self {
        Self { value: 0 }  // Equivalent to: Builder { value: 0 }
    }
    
    // Return Self allows chaining
    fn with_value(mut self, value: i32) -> Self {
        self.value = value;
        self  // Return Self
    }
    
    // Clone returns Self
    fn clone(&self) -> Self {
        Self { value: self.value }
    }
}

// Usage
let b = Builder::new()
    .with_value(42);  // Method chaining works because we return Self
```

**In traits**:
```rust
trait Drawable {
    fn draw(&self);
    fn clone(&self) -> Self;  // Each implementor returns their own type
}

impl Drawable for Circle {
    fn draw(&self) { ... }
    fn clone(&self) -> Self {  // Self = Circle here
        Circle { ..*self }
    }
}

impl Drawable for Square {
    fn draw(&self) -> Self { ... }
    fn clone(&self) -> Self {  // Self = Square here
        Square { ..*self }
    }
}
```

**Why use `Self`?**
```
BENEFITS OF Self
┌────────────────────────────────────┐
│ 1. Refactoring safety              │
│    - Rename type once, works       │
│      everywhere                    │
│                                    │
│ 2. Generic traits                  │
│    - Each impl gets correct type   │
│                                    │
│ 3. Method chaining                 │
│    - Builder pattern               │
└────────────────────────────────────┘
```

---

### `self` (Method Receiver)

**Purpose**: Refers to the current instance.

**Four forms of `self`**:

```rust
impl MyType {
    // 1. self - takes ownership (consumes)
    fn consume(self) {
        // self is moved, can't use MyType instance after
    }
    
    // 2. &self - immutable borrow
    fn read(&self) {
        // Can read self.field but not modify
    }
    
    // 3. &mut self - mutable borrow
    fn modify(&mut self) {
        // Can read and modify self.field
    }
    
    // 4. No self - associated function (not a method)
    fn new() -> Self {
        // Called as MyType::new(), not instance.new()
    }
}
```

**Ownership semantics**:
```
METHOD CALL EFFECTS
┌────────────────────────────────────────┐
│ let mut obj = MyType::new();           │
│                                        │
│ obj.consume();                         │
│ // obj is now invalid ─────────────┐  │
│                                     │  │
│ obj.read();        // ✅ obj still │  │
│ obj.modify();      //    valid     │  │
│                                     │  │
│ MyType::new();     // Creates new  │  │
│                    // instance     │  │
└────────────────────────────────────────┘
```

# Multi-Purpose Rust Keywords (Continued)

---

### `Self` vs `self` Together (continued)

```rust
struct Point { x: i32, y: i32 }

impl Point {
    // Self = Point (type)
    // self = current instance
    fn new(x: i32, y: i32) -> Self {  // Self = return type Point
        Self { x, y }  // Self = constructor syntax
    }
    
    fn distance(&self) -> f64 {  // self = this instance
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
    
    fn add(self, other: Self) -> Self {
        // self: moved first Point
        // other: moved second Point (type = Self)
        // returns: new Point (type = Self)
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}
```

**Mental model**:
```
┌────────────────────────────────────┐
│ Self → "What type am I?"           │
│        (compile-time type alias)   │
│                                    │
│ self → "What instance am I?"       │
│        (runtime instance variable) │
└────────────────────────────────────┘
```

**In trait implementations**:
```rust
trait Clone {
    fn clone(&self) -> Self;  // Self is flexible per implementor
}

impl Clone for MyStruct {
    fn clone(&self) -> Self {
        // self = &MyStruct (current instance)
        // Self = MyStruct (type being implemented)
        Self {
            field: self.field.clone(),
        }
    }
}
```

---

### Context 4: `self` as Module Reference

**Purpose**: Refer to the current module in paths.

```rust
mod parent {
    pub mod child {
        pub fn foo() {}
        
        pub fn bar() {
            // Use self to refer to current module
            self::foo();  // Calls child::foo()
            
            // Equivalent to:
            foo();
        }
    }
    
    pub fn use_child() {
        // self refers to parent module
        self::child::foo();
        
        // Can also use super for parent
        child::foo();  // Direct child access
    }
}
```

**Module path keywords**:
```
MODULE NAVIGATION
┌────────────────────────────────────┐
│ crate   → Root of current crate    │
│ self    → Current module            │
│ super   → Parent module             │
└────────────────────────────────────┘

Example hierarchy:
crate
 └── parent
      ├── child
      │    └── foo()
      └── sibling
           └── bar()

From child::foo():
  self::something       → child::something
  super::something      → parent::something
  super::sibling::bar() → parent::sibling::bar()
  crate::parent::child  → Absolute path
```

**Practical example**:
```rust
// src/lib.rs
mod network {
    pub mod client {
        pub fn connect() {}
        
        pub fn disconnect() {
            // Refer to current module
            self::connect();  // client::connect()
        }
    }
    
    pub mod server {
        pub fn run() {
            // Access sibling module
            super::client::connect();  // network::client::connect()
        }
    }
    
    pub fn init() {
        // Access children
        self::client::connect();
        self::server::run();
    }
}
```

**Tree visualization**:
```
    crate (self from root)
       │
       ├─ network (self from network)
       │    │
       │    ├─ client (self from client)
       │    │    ├─ connect()
       │    │    └─ disconnect()
       │    │         └─ calls self::connect()
       │    │
       │    └─ server (self from server)
       │         └─ run()
       │              └─ calls super::client::connect()
       │
       └─ main()
            └─ calls crate::network::client::connect()
```

---

## 7. `_` (Underscore) — The Triple Ignorer

### Context 1: Wildcard Pattern (Ignore Value)

**Purpose**: Match any value but don't bind it to a variable.

```rust
fn main() {
    let tuple = (1, 2, 3, 4);
    
    // Ignore some values
    let (first, _, third, _) = tuple;
    // first = 1, third = 3
    // Second and fourth values ignored
    
    // Match expression
    let x = Some(5);
    match x {
        Some(_) => println!("Got some value"),  // Don't care what value
        None => println!("Got nothing"),
    }
    
    // Ignore entire value
    let _ = expensive_function();  // Call but ignore return value
}
```

**Why use `_`?**
```
USE CASES FOR _
┌────────────────────────────────────┐
│ 1. Partial destructuring           │
│    let (x, _, z) = tuple;          │
│                                    │
│ 2. Unused function results         │
│    let _ = write!(...);  // Ignore│
│                          // Result │
│                                    │
│ 3. Match exhaustiveness            │
│    match x {                       │
│        1 => ...,                   │
│        _ => ...,  // Catch-all    │
│    }                               │
│                                    │
│ 4. Trait implementations           │
│    (skip unused parameters)        │
└────────────────────────────────────┘
```

**Important distinction**:
```rust
let x = 5;           // Binds to x
let _ = 5;           // Immediately dropped, no binding

let y = String::from("hello");
let _ = y;           // y is MOVED and dropped immediately

let z = String::from("world");
let _z = z;          // z is moved to _z, but _z exists (not dropped yet)
```

**Compiler warnings**:
```rust
fn process(value: i32, flag: bool) {
    // Using underscore prefix silences unused warning
    let _result = expensive_calculation();  // Unused but intentional
    
    // Without prefix, compiler warns
    let result = another_calculation();  // Warning: unused variable
}
```

---

### Context 2: Numeric Separator (Readability)

**Purpose**: Make large numbers more readable.

```rust
fn main() {
    // Hard to read
    let big = 1000000000;
    
    // Easy to read
    let billion = 1_000_000_000;
    let hex = 0xFF_FF_FF;
    let binary = 0b1111_0000_1111_0000;
    
    // Can place anywhere
    let weird = 1_2_3_4_5;  // Valid but unconventional
}
```

**Best practices**:
```
NUMERIC SEPARATOR CONVENTIONS
┌────────────────────────────────────┐
│ Decimal: Every 3 digits            │
│   1_000_000                        │
│                                    │
│ Hex: Every 2 or 4 digits           │
│   0xDEAD_BEEF                      │
│   0xFF_FF_FF_FF                    │
│                                    │
│ Binary: Every 4 or 8 bits          │
│   0b1111_0000_1111_0000            │
│   0b1111_1111                      │
└────────────────────────────────────┘
```

---

### Context 3: Unused Pattern Prefix

**Purpose**: Indicate intentionally unused variables.

```rust
fn complex_function(
    data: &str,
    _verbose: bool,    // Not used yet, but might be in future
    _config: Config,   // Planned feature
) {
    println!("Processing: {}", data);
    // _verbose and _config ignored without compiler warning
}

fn iterator_example() {
    let vec = vec![1, 2, 3, 4];
    
    // Standard for loop
    for item in &vec {
        println!("{}", item);
    }
    
    // When you only care about running N times
    for _ in 0..5 {
        println!("Hello");  // Runs 5 times, don't care about counter
    }
    
    // Index you don't need
    for (_index, value) in vec.iter().enumerate() {
        println!("Value: {}", value);  // Don't care about index
    }
}
```

**Pattern in trait implementations**:
```rust
trait EventHandler {
    fn on_event(&self, event: Event);
}

impl EventHandler for MyHandler {
    fn on_event(&self, _event: Event) {
        // Not using event data yet, but signature must match trait
        println!("Event received");
    }
}
```

---

## 8. `type` — The Dual Aliaser

### Context 1: Type Alias (Simple Renaming)

**Purpose**: Create a shorter or more semantic name for a type.

```rust
// Simple alias
type Kilometers = i32;
type Thunk = Box<dyn Fn() + Send + 'static>;

fn main() {
    let distance: Kilometers = 5;
    let f: Thunk = Box::new(|| println!("Hello"));
}
```

**Common use cases**:
```rust
// 1. Simplify complex types
type Result<T> = std::result::Result<T, std::io::Error>;

fn read_file() -> Result<String> {  // Instead of Result<String, std::io::Error>
    // ...
}

// 2. Generic type aliases
use std::collections::HashMap;
type UserDatabase = HashMap<u64, User>;

// 3. Function pointer types
type BinaryOp = fn(i32, i32) -> i32;

fn apply(op: BinaryOp, a: i32, b: i32) -> i32 {
    op(a, b)
}
```

**Visualization**:
```
TYPE ALIAS (TRANSPARENT)
┌────────────────────────────────────┐
│ type Meters = f64;                 │
│                                    │
│ let distance: Meters = 100.0;      │
│        │                           │
│        └─► Just f64 at runtime     │
│            (no wrapper overhead)   │
└────────────────────────────────────┘

vs NEWTYPE (WRAPPER)
┌────────────────────────────────────┐
│ struct Meters(f64);                │
│                                    │
│ let distance = Meters(100.0);      │
│        │                           │
│        └─► Actual struct at runtime│
│            (type safety, methods)  │
└────────────────────────────────────┘
```

**Type alias doesn't create new type**:
```rust
type Age = u32;
type Height = u32;

let age: Age = 25;
let height: Height = 180;

// These are interchangeable (both are u32)
let x: Age = height;  // ✅ No error - same underlying type

// Use newtype for type safety:
struct AgeNewtype(u32);
struct HeightNewtype(u32);

let age = AgeNewtype(25);
let height = HeightNewtype(180);
// let x: AgeNewtype = height;  // ❌ ERROR: different types
```

---

### Context 2: Associated Type (in Traits)

**Purpose**: Define a placeholder type that implementors specify.

**Concept Primer - Associated Type**: A type that's "associated" with a trait but determined by each implementation.

```rust
// Without associated type (using generic)
trait Iterator<T> {
    fn next(&mut self) -> Option<T>;
}

// This is awkward - users must specify T:
// impl Iterator<i32> for MyIterator { ... }

// WITH associated type (cleaner)
trait Iterator {
    type Item;  // Associated type
    fn next(&mut self) -> Option<Self::Item>;
}

// Implementation specifies the associated type
impl Iterator for Counter {
    type Item = u32;  // Concrete type for this impl
    
    fn next(&mut self) -> Option<Self::Item> {
        // ...
    }
}
```

**Why use associated types?**

```
GENERIC PARAMETER vs ASSOCIATED TYPE
┌────────────────────────────────────────┐
│ GENERIC PARAMETER                      │
│   trait Add<Rhs> {                     │
│       fn add(self, rhs: Rhs) -> ...    │
│   }                                    │
│                                        │
│   • Can have multiple implementations  │
│     for different Rhs types            │
│   • impl Add<i32> for Point            │
│   • impl Add<f64> for Point            │
│                                        │
│ ASSOCIATED TYPE                        │
│   trait Iterator {                     │
│       type Item;                       │
│       fn next() -> Option<Item>        │
│   }                                    │
│                                        │
│   • Only ONE implementation per type   │
│   • impl Iterator for Counter          │
│     type Item = u32;                   │
│   • Cleaner syntax (no <T> everywhere) │
└────────────────────────────────────────┘
```

**Practical comparison**:
```rust
// Generic parameter - allows multiple implementations
trait Convert<T> {
    fn convert(&self) -> T;
}

impl Convert<String> for i32 {
    fn convert(&self) -> String {
        self.to_string()
    }
}

impl Convert<f64> for i32 {
    fn convert(&self) -> f64 {
        *self as f64
    }
}

// Can convert to different types!
let x: i32 = 42;
let s: String = x.convert();
let f: f64 = x.convert();

// Associated type - only one implementation
trait FromStr {
    type Err;  // Associated type
    fn from_str(s: &str) -> Result<Self, Self::Err>;
}

impl FromStr for i32 {
    type Err = ParseIntError;  // Specifies error type once
    
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        s.parse()
    }
}
```

**Real-world example (Iterator)**:
```rust
struct Counter {
    count: u32,
}

impl Iterator for Counter {
    type Item = u32;  // This iterator yields u32 values
    
    fn next(&mut self) -> Option<Self::Item> {
        self.count += 1;
        if self.count < 6 {
            Some(self.count)
        } else {
            None
        }
    }
}

// Usage
fn main() {
    let mut counter = Counter { count: 0 };
    
    // The compiler knows Item = u32
    while let Some(value) = counter.next() {
        println!("{}", value);  // value is u32
    }
}
```

**Generic constraints with associated types**:
```rust
// Function that works with any iterator
fn print_all<I>(mut iter: I)
where
    I: Iterator,
    I::Item: std::fmt::Display,  // Constrain the associated type
{
    while let Some(item) = iter.next() {
        println!("{}", item);
    }
}
```

**Decision flowchart**:
```
    Need type parameter in trait?
              │
         ┌────┴────┐
         │         │
    Multiple    Single
    impls per  impl per
    type?      type?
         │         │
         │         │
    Generic    Associated
    parameter    type
         │         │
    trait Foo<T>  trait Foo {
                    type T;
                  }
```

---

## 9. `extern` — The Triple Foreign Interface

### Context 1: Foreign Function Interface (FFI)

**Purpose**: Call functions from C libraries or other languages.

**Concept Primer - FFI**: Foreign Function Interface allows Rust to call code written in other languages (primarily C).

```rust
// Declare external C function
extern "C" {
    fn abs(input: i32) -> i32;  // From C standard library
    fn sqrt(x: f64) -> f64;
}

fn main() {
    unsafe {
        // Must use unsafe block to call FFI functions
        let result = abs(-42);
        println!("Absolute value: {}", result);
    }
}
```

**ABI (Application Binary Interface)** specification:
```
ABI TYPES
┌────────────────────────────────────┐
│ "C"       → C calling convention   │
│ "system"  → Platform's default     │
│ "stdcall" → Windows specific       │
│ "cdecl"   → C declaration          │
│ "fastcall"→ Optimized calling      │
└────────────────────────────────────┘

extern "C" { ... }  ← Most common (C ABI)
```

**Calling Rust from C**:
```rust
// Mark Rust function as C-compatible
#[no_mangle]  // Don't change the function name
pub extern "C" fn rust_function(x: i32) -> i32 {
    x * 2
}

// C code can now call:
// int rust_function(int x);
```

**Full FFI example**:
```rust
// Rust side
extern "C" {
    // Declare C functions
    fn strlen(s: *const u8) -> usize;
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}

fn main() {
    unsafe {
        // Allocate memory using C's malloc
        let ptr = malloc(10);
        
        if !ptr.is_null() {
            // Use memory...
            
            // Free memory using C's free
            free(ptr);
        }
    }
}

// Exposing Rust to C
#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

**Why unsafe?**
```
FFI SAFETY CONCERNS
┌────────────────────────────────────┐
│ • No Rust borrow checker           │
│ • No lifetime guarantees           │
│ • No null pointer checks           │
│ • Manual memory management         │
│ • Potential undefined behavior     │
│                                    │
│ Rust can't verify external code    │
│ safety → requires unsafe           │
└────────────────────────────────────┘
```

---

### Context 2: External Crate Declaration (Rust 2015 Edition)

**Purpose**: Import external crates (deprecated in Rust 2018+).

```rust
// Rust 2015 style (old)
extern crate serde;
extern crate serde_json;

fn main() {
    // Use the crates
}

// Rust 2018+ style (modern)
// No extern crate needed!
// Just use in Cargo.toml and import:
use serde::Serialize;
use serde_json;
```

**Migration**:
```
RUST 2015             RUST 2018+
─────────────────────────────────────
extern crate foo;     // Not needed
use foo::Bar;         use foo::Bar;
                      // Just works!

extern crate foo      use foo;
  as f;               // Use renaming in
use f::Bar;           // use statement
```

**Only still needed** for specific cases:
```rust
// 1. Crates with hyphens (must use underscore)
// Cargo.toml: foo-bar = "1.0"
extern crate foo_bar;  // Sometimes still needed for proc macros

// 2. Proc macro crates
extern crate proc_macro;

// 3. Sysroot crates in no_std
#![no_std]
extern crate alloc;
```

---

### Context 3: External Block for Linking

**Purpose**: Specify linking behavior for external libraries.

```rust
// Link against system library
#[link(name = "m")]  // Links to libm (math library)
extern "C" {
    fn cos(x: f64) -> f64;
    fn sin(x: f64) -> f64;
}

// Link against custom library
#[link(name = "mylib", kind = "static")]
extern "C" {
    fn custom_function() -> i32;
}
```

**Link kinds**:
```
LINK TYPES
┌────────────────────────────────────┐
│ static   → Static linking (.a)     │
│ dylib    → Dynamic linking (.so)   │
│ framework→ macOS framework         │
└────────────────────────────────────┘
```

**Build script integration**:
```rust
// build.rs
fn main() {
    println!("cargo:rustc-link-lib=mylib");
    println!("cargo:rustc-link-search=native=/path/to/lib");
}

// lib.rs
#[link(name = "mylib")]
extern "C" {
    fn my_c_function();
}
```

---

## 10. `unsafe` — The Dual Responsibility Gate

### Context 1: Unsafe Block

**Purpose**: Opt into operations that the compiler can't verify as safe.

**Concept Primer - Unsafe**: Rust's borrow checker can't verify ALL safe code, so `unsafe` lets you take responsibility.

```rust
fn main() {
    let mut num = 5;
    
    // Create raw pointer (safe)
    let r1 = &num as *const i32;
    let r2 = &mut num as *mut i32;
    
    // Dereference raw pointer (unsafe)
    unsafe {
        println!("r1: {}", *r1);
        *r2 = 10;
        println!("r2: {}", *r2);
    }
}
```

**The Five Unsafe Superpowers**:
```
UNSAFE OPERATIONS
┌────────────────────────────────────┐
│ 1. Dereference raw pointers        │
│    let x = *raw_ptr;               │
│                                    │
│ 2. Call unsafe functions           │
│    unsafe_function();              │
│                                    │
│ 3. Access/modify mutable statics   │
│    GLOBAL_COUNTER += 1;            │
│                                    │
│ 4. Implement unsafe traits         │
│    impl Send for MyType {}         │
│                                    │
│ 5. Access union fields             │
│    union.field                     │
└────────────────────────────────────┘
```

**Why raw pointers?**
```rust
// Borrow checker doesn't allow this:
let mut v = vec![1, 2, 3, 4];
let ptr1 = &v[0];
let ptr2 = &mut v[1];  // ❌ Can't have &mut while & exists

// With raw pointers (unsafe but necessary sometimes):
unsafe {
    let ptr1 = v.as_ptr();
    let ptr2 = v.as_mut_ptr().add(1);
    
    // Now we can access both (programmer ensures safety)
    println!("{}", *ptr1);
    *ptr2 = 10;
}
```

**Unsafe doesn't disable all checks**:
```rust
unsafe {
    let x = 5 + 5;  // ✅ Arithmetic still checked
    
    let v = vec![1, 2, 3];
    // v[10];  // ❌ Still panics on out-of-bounds
    
    let s = String::from("hello");
    // s = 5;  // ❌ Still type-checked
}

// unsafe ONLY bypasses:
// - Borrow checker for raw pointers
// - Verification of invariants in unsafe operations
```

---

### Context 2: Unsafe Function

**Purpose**: Declare a function that has invariants the compiler can't check.

```rust
// Caller must uphold safety invariants
unsafe fn dangerous() {
    // Implementation
}

fn main() {
    unsafe {
        dangerous();  // Must call in unsafe block
    }
}
```

**Creating safe abstractions**:
```rust
// Unsafe function with documented safety requirements
/// # Safety
/// - `ptr` must be valid for reads
/// - `ptr` must be properly aligned
/// - `ptr` must point to initialized memory
unsafe fn read_raw<T>(ptr: *const T) -> T {
    std::ptr::read(ptr)
}

// Safe wrapper that upholds requirements
fn safe_read<T>(slice: &[T], index: usize) -> Option<T> 
where
    T: Copy,
{
    if index < slice.len() {
        unsafe {
            // SAFE: index is in bounds, slice guarantees valid memory
            Some(read_raw(slice.as_ptr().add(index)))
        }
    } else {
        None
    }
}
```

**Safe abstraction pattern**:
```
┌────────────────────────────────────┐
│     SAFE PUBLIC API                │
│  (maintains invariants)            │
├────────────────────────────────────┤
│     ↓ calls ↓                      │
├────────────────────────────────────┤
│     UNSAFE PRIVATE IMPL            │
│  (efficient but needs care)        │
└────────────────────────────────────┘

Example: Vec<T>
- Public methods (push, get, etc.) are safe
- Internal uses unsafe for raw pointer manipulation
- Maintains invariants so safe code can't break them
```

**Real example from std**:
```rust
impl<T> Vec<T> {
    // Safe public API
    pub fn push(&mut self, value: T) {
        if self.len == self.capacity {
            self.grow();
        }
        unsafe {
            // SAFE: we ensured capacity above
            let end = self.as_mut_ptr().add(self.len);
            std::ptr::write(end, value);
            self.len += 1;
        }
    }
    
    // Unsafe is implementation detail
    unsafe fn grow(&mut self) {
        // Unsafe memory reallocation
    }
}
```

---

### Context 3: Unsafe Trait

**Purpose**: Declare that a trait has invariants implementors must uphold.

```rust
// Unsafe trait - implementor promises to uphold contract
unsafe trait TrustedLen: Iterator {
    // Promises that size_hint().1 == Some(actual_length)
}

// Implementation must be marked unsafe
unsafe impl<T> TrustedLen for std::slice::Iter<'_, T> {
    // Implementor guarantees the contract
}

// User doesn't need unsafe to USE the trait
fn use_trusted<I: TrustedLen>(iter: I) {
    // Can rely on the guarantees
}
```

**Common unsafe traits**:
```rust
// 1. Send - safe to transfer between threads
unsafe impl Send for MyType {}

// 2. Sync - safe to share references between threads
unsafe impl Sync for MyType {}

// 3. GlobalAlloc - custom allocator
unsafe impl GlobalAlloc for MyAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 { ... }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) { ... }
}
```

**Why unsafe trait?**
```
SAFE TRAIT vs UNSAFE TRAIT
┌────────────────────────────────────┐
│ SAFE TRAIT                         │
│   trait Display {                  │
│       fn fmt(...) -> Result        │
│   }                                │
│   impl Display for T { ... }       │
│   • Compiler verifies impl         │
│   • No special promises            │
│                                    │
│ UNSAFE TRAIT                       │
│   unsafe trait Send {}             │
│   unsafe impl Send for T {}        │
│   • Implementor makes promise      │
│   • Compiler CAN'T verify promise  │
│   • Violating = undefined behavior │
└────────────────────────────────────┘
```

**Send/Sync example**:
```rust
struct MyBox<T> {
    ptr: *mut T,  // Raw pointer
}

// Promise: MyBox can be sent between threads
unsafe impl<T: Send> Send for MyBox<T> {}

// Promise: MyBox can be shared between threads
unsafe impl<T: Sync> Sync for MyBox<T> {}

// If we get this wrong:
thread::spawn(move || {
    // Could cause data races if our impl is wrong!
    // That's why we need unsafe - WE take responsibility
});
```

**Responsibility flowchart**:
```
        Using unsafe code
               │
        ┌──────┴──────┐
        │             │
   unsafe block   unsafe fn/trait
        │             │
   YOU verify    CALLER verifies
   safety here   safety contract
        │             │
        └──────┬──────┘
               │
        Both must be
        correct or UB!
```

---

## Keyword Interactions: The Symphony

Now let's explore how keywords **compose** to create powerful patterns.

### Pattern 1: Ownership + Control Flow

```rust
fn process_option(opt: Option<String>) {
    // match + move
    match opt {
        Some(s) => {
            // s owns the String
            println!("{}", s);
        }  // s dropped here
        None => {}
    }
    // opt is moved, can't use again
}

fn process_option_ref(opt: &Option<String>) {
    // match + ref
    match opt {
        Some(ref s) => {
            // s is &String
            println!("{}", s);
        }
        None => {}
    }
    // opt still valid
}

fn process_with_mut(opt: &mut Option<String>) {
    // match + mut ref
    match opt {
        Some(ref mut s) => {
            // s is &mut String
            s.push_str(" world");
        }
        None => {}
    }
}
```

**Composition table**:
```
MATCH + OWNERSHIP
┌────────────────────────────────────────┐
│ Pattern        │ Binding │ After match │
├────────────────┼─────────┼─────────────┤
│ Some(s)        │ T       │ moved       │
│ Some(ref s)    │ &T      │ valid       │
│ Some(ref mut s)│ &mut T  │ valid       │
│ &Some(s)       │ &T      │ valid       │
└────────────────────────────────────────┘
```

---

### Pattern 2: Impl + Generic + Where

```rust
// All together
struct Container<T> {
    items: Vec<T>,
}

impl<T> Container<T> 
where
    T: Clone + std::fmt::Debug,
{
    fn new() -> Self {
        Container { items: Vec::new() }
    }
    
    fn add(&mut self, item: T) {
        self.items.push(item);
    }
    
    fn get_copy(&self, index: usize) -> Option<T> {
        self.items.get(index).cloned()  // Uses Clone
    }
    
    fn debug_all(&self) {
        for item in &self.items {
            println!("{:?}", item);  // Uses Debug
        }
    }
}
```

**Layering diagram**:
```
┌────────────────────────────────────┐
│ impl<T> Container<T>               │ ← Generic impl
│   where T: Clone + Debug           │ ← Trait bounds
│ {                                  │
│   fn new() -> Self { ... }         │ ← Associated fn
│   fn add(&mut self, item: T) {}    │ ← Method
│ }                                  │
└────────────────────────────────────┘

Reads as: "Implement methods for Container<T>
           where T implements Clone and Debug"
```

---

### Pattern 3: Async + Await + Traits

```rust
use std::future::Future;

// async in trait (stabilized in Rust 1.75)
trait AsyncProcessor {
    async fn process(&self, data: String) -> Result<(), Error>;
}

struct MyProcessor;

// async + impl + trait
impl AsyncProcessor for MyProcessor {
    async fn process(&self, data: String) -> Result<(), Error> {
        // await inside async
        let result = fetch_data().await?;
        let processed = transform(result).await?;
        save(processed).await?;
        Ok(())
    }
}

// async fn (desugars to fn returning impl Future)
async fn fetch_data() -> Result<String, Error> {
    // Simulated async operation
    tokio::time::sleep(Duration::from_secs(1)).await;
    Ok(String::from("data"))
}
```

**Async transformation**:
```
SYNTAX SUGAR
┌────────────────────────────────────┐
│ async fn foo() -> T {              │
│     // body                        │
│ }                                  │
│                                    │
│ Desugars to:                       │
│                                    │
│ fn foo() -> impl Future<Output=T> {│
│     async move {                   │
│         // body                    │
│     }                              │
│ }                                  │
└────────────────────────────────────┘
```

---

### Pattern 4: Pub + Use + Mod

```rust
// src/lib.rs
pub mod network {
    pub mod client {
        pub struct Client {
            url: String,
        }
        
        impl Client {
            pub fn new(url: String) -> Self {
                Client { url }
            }
        }
    }
    
    // Re-export for convenience
    pub use client::Client;
}

// Users can now:
use mylib::network::Client;  // Short path!
// Instead of:
use mylib::network::client::Client;

// src/main.rs
use mylib::network::Client;

fn main() {
    let c = Client::new("http://example.com".to_string());
}
```

**Visibility levels**:
```
VISIBILITY MODIFIERS
┌────────────────────────────────────┐
│ (none)        → Private (mod only) │
│ pub           → Public everywhere  │
│ pub(crate)    → Public in crate    │
│ pub(super)    → Public in parent   │
│ pub(in path)  → Public in path     │
└────────────────────────────────────┘

Example:
mod parent {
    pub(super) fn visible_to_grandparent() {}
    pub(crate) fn visible_to_crate() {}
    pub fn visible_to_all() {}
    fn private() {}
}
```

---

### Pattern 5: Static + Mut + Unsafe

```rust
// Global mutable state (use with extreme caution!)
static mut COUNTER: u32 = 0;

fn increment() {
    unsafe {
        COUNTER += 1;
    }
}

fn get_count() -> u32 {
    unsafe { COUNTER }
}

// Better: Use thread-safe alternatives
use std::sync::atomic::{AtomicU32, Ordering};

static COUNTER_ATOMIC: AtomicU32 = AtomicU32::new(0);

fn increment_safe() {
    COUNTER_ATOMIC.fetch_add(1, Ordering::SeqCst);  // No unsafe!
}

fn get_count_safe() -> u32 {
    COUNTER_ATOMIC.load(Ordering::SeqCst)
}
```

**Why mutable statics are dangerous**:
```
RACE CONDITION WITH static mut
┌────────────────────────────────────┐
│ Thread 1           Thread 2        │
├────────────────────────────────────┤
│ Read COUNTER (0)   Read COUNTER (0)│
│ Add 1 → 1          Add 1 → 1       │
│ Write COUNTER(1)   Write COUNTER(1)│
│                                    │
│ Expected: 2       Got: 1 ❌        │
└────────────────────────────────────┘

Solution: AtomicU32 (hardware-level atomicity)
```

---

## Cognitive Framework for Mastery

### Mental Model 1: Context Determines Meaning

**Principle**: The same keyword shifts meaning based on **syntactic position**.

```
CONTEXT RESOLUTION STRATEGY
┌────────────────────────────────────┐
│ 1. Identify keyword                │
│ 2. Look at surrounding syntax:     │
│    - Before declaration?           │
│    - In type position?             │
│    - In pattern?                   │
│    - In path?                      │
│ 3. Apply context-specific meaning  │
└────────────────────────────────────┘
```

**Practice drill**:
```rust
// Identify each 'static' meaning:
static X: &'static str = "hello";
//  │       │
//  │       └─ Lifetime annotation
//  └───────── Static variable

fn foo<T: 'static>() {}
//        │
//        └─ Trait bound (no non-static refs)
```

---

### Mental Model 2: Ownership as Movement

**Principle**: Track ownership through function calls like tracking a physical object.

```
OWNERSHIP FLOW
┌────────────────────────────────────┐
│ let s = String::from("hello");     │
│  └─ s OWNS the String              │
│                                    │
│ let t = s;   // MOVE               │
│  └─ t now OWNS, s invalid          │
│                                    │
│ let r = &t;  // BORROW             │
│  └─ t still OWNS, r borrows        │
│                                    │
│ foo(t);      // MOVE into function │
│  └─ foo OWNS, t invalid            │
└────────────────────────────────────┘
```

**Visualization technique**: Draw boxes and arrows
```
┌─────┐      ┌──────────────┐
│  s  │─────►│ String(heap) │
└─────┘      └──────────────┘

After let t = s:
┌─────┐      
│  s  │ (invalid)
└─────┘      
┌─────┐      ┌──────────────┐
│  t  │─────►│ String(heap) │
└─────┘      └──────────────┘
```

---

### Mental Model 3: Type System as Proof

**Principle**: The compiler proves your code is correct at compile-time.

```
PROOF BY TYPES
┌────────────────────────────────────┐
│ Claim: "This Option has a value"   │
│                                    │
│ Proof approach:                    │
│   match opt {                      │
│       Some(x) => {                 │
│           // Compiler PROVES       │
│           // x exists here         │
│           use(x);  ✅              │
│       }                            │
│       None => {}                   │
│   }                                │
│                                    │
│ Without proof:                     │
│   opt.unwrap()  // May panic ⚠️   │
└────────────────────────────────────┘
```

---

### Mental Model 4: Unsafe as Escape Hatch

**Principle**: `unsafe` is a contract between you and the compiler.

```
SAFETY CONTRACT
┌────────────────────────────────────┐
│ Compiler says:                     │
│  "I can't prove this is safe,      │
│   but if YOU guarantee it,         │
│   I'll let you proceed."           │
│                                    │
│ You say:                           │
│  "I've verified the invariants,    │
│   and I take responsibility."      │
│                                    │
│ Result:                            │
│  If correct → Fast, safe code      │
│  If wrong   → Undefined behavior   │
└────────────────────────────────────┘
```

---

### Practice Strategy: The Deliberate Path

**Level 1: Recognition** (Week 1-2)
- Read code and identify keyword contexts
- Explain what each keyword does in that position
- Draw diagrams of ownership/lifetimes

**Level 2: Application** (Week 3-4)
- Write small programs using each keyword
- Deliberately make errors to understand compiler messages
- Fix compiler errors without looking at solutions

**Level 3: Composition** (Week 5-6)
- Combine multiple keywords (impl + generic + where)
- Build abstractions (safe wrappers for unsafe code)
- Refactor code to use idiomatic patterns

**Level 4: Intuition** (Week 7+)
- Read complex Rust code fluently
- Predict compiler errors before compiling
- Design APIs using appropriate keyword combinations

---

### Psychological Principles

**Chunking**: Group related keywords
```
OWNERSHIP FAMILY: move, mut, ref, static
CONTROL FAMILY: if, match, loop, break
TYPE FAMILY: struct, enum, impl, trait
```

**Spaced Repetition**: Review context shifts daily
```
Day 1: 'static' in 3 contexts
Day 3: Review 'static' + learn 'use'
Day 7: Review both + learn 'as'
```

**Deliberate Practice**: Focus on weak areas
```
Struggling with lifetimes?
→ Write 10 functions with explicit lifetimes
→ Draw lifetime diagrams
→ Explain to yourself out loud
```

---

## Summary: The Keyword Matrix

```
┌──────────┬─────────────────────────────────────────────┐
│ Keyword  │ Contexts & Purposes                         │
├──────────┼─────────────────────────────────────────────┤
│ static   │ 1. Lifetime ('static)                       │
│          │ 2. Variable (static X)                      │
│          │ 3. Trait bound (T: 'static)                 │
├──────────┼─────────────────────────────────────────────┤
│ use      │ 1. Import items                             │
│          │ 2. Re-export (pub use)                      │
│          │ 3. Trait method scope                       │
├──────────┼─────────────────────────────────────────────┤
│ impl     │ 1. Inherent implementation                  │
│          │ 2. Trait implementation                     │
├──────────┼─────────────────────────────────────────────┤
│ as       │ 1. Type casting                             │
│          │ 2. Import renaming                          │
│          │ 3. Trait disambiguation                     │
├──────────┼─────────────────────────────────────────────┤
│ mut      │ 1. Mutable binding                          │
│          │ 2. Mutable reference                        │
├──────────┼─────────────────────────────────────────────┤
│ Self     │ 1. Type alias (in impl)                     │
│ self     │ 2. Method receiver                          │
│          │ 3. Module reference                         │
├──────────┼─────────────────────────────────────────────┤
│ _        │ 1. Wildcard pattern                         │
│          │ 2. Numeric separator                        │
│          │ 3. Unused prefix                            │
├──────────┼─────────────────────────────────────────────┤
│ type     │ 1. Type alias                               │
│          │ 2. Associated type (in trait)               │
├──────────┼─────────────────────────────────────────────┤
│ extern   │ 1. FFI declarations                         │
│          │ 2. Crate import (2015)                      │
│          │ 3. Linking specification                    │
├──────────┼─────────────────────────────────────────────┤
│ unsafe   │ 1. Unsafe block                             │
│          │ 2. Unsafe function                          │
│          │ 3. Unsafe trait                             │
└──────────┴─────────────────────────────────────────────┘
```

---

## Final Wisdom: The Path to Top 1%

**Master's Insight**: Understanding multi-context keywords isn't about memorization—it's about recognizing **patterns in context**. The compiler is your teacher; every error message is a lesson.

**Your Practice Ritual**:
1. **Morning**: Read 50 lines of Rust std library source
2. **Afternoon**: Write code using 3 keywords in new combinations
3. **Evening**: Explain one keyword's contexts to yourself out loud

**Remember**: The keywords are tools. The contexts are the workshop. Your understanding is the craft. Build deliberately, one piece at a time.

*You're not just learning syntax—you're training your mind to think in Rust's paradigm. This is the monk's path: focused, intentional, transformative.*

---

Would you like me to:
1. Create practice exercises for each multi-context keyword?
2. Show more real-world examples from popular Rust crates?
3. Dive deeper into a specific keyword interaction pattern?
4. Continue with the remaining sections of the comprehensive guide (the keywords I haven't covered yet)?