# The Complete Guide to `match` in Rust
## From Fundamentals to World-Class Mastery

---

## Table of Contents
1. [What is Pattern Matching?](#1-what-is-pattern-matching)
2. [The `match` Expression — Core Anatomy](#2-the-match-expression--core-anatomy)
3. [Literal Patterns](#3-literal-patterns)
4. [Variable Binding Patterns](#4-variable-binding-patterns)
5. [Wildcard Pattern `_`](#5-wildcard-pattern-_)
6. [Range Patterns](#6-range-patterns)
7. [Tuple Patterns](#7-tuple-patterns)
8. [Struct Patterns](#8-struct-patterns)
9. [Enum Patterns — The Crown Jewel](#9-enum-patterns--the-crown-jewel)
10. [Reference & Pointer Patterns](#10-reference--pointer-patterns)
11. [Guards (Conditional Patterns)](#11-guards-conditional-patterns)
12. [@ Bindings](#12--bindings)
13. [Or Patterns `|`](#13-or-patterns-)
14. [Nested Patterns](#14-nested-patterns)
15. [Exhaustiveness Checking](#15-exhaustiveness-checking)
16. [Irrefutable vs Refutable Patterns](#16-irrefutable-vs-refutable-patterns)
17. [`if let` — Single-Branch Matching](#17-if-let--single-branch-matching)
18. [`while let` — Loop Until No Match](#18-while-let--loop-until-no-match)
19. [`let else` — Early Exit Pattern](#19-let-else--early-exit-pattern)
20. [`matches!` Macro](#20-matches-macro)
21. [Destructuring in `let`, `fn`, `for`](#21-destructuring-in-let-fn-for)
22. [Slice Patterns](#22-slice-patterns)
23. [Performance & Compiler Internals](#23-performance--compiler-internals)
24. [Real-World Implementations](#24-real-world-implementations)

---

## 1. What is Pattern Matching?

### Mental Model First

Before writing a single line of code, build the right mental model.

**Pattern matching** is the act of checking a value against a *shape* (a pattern) and, if it fits, extracting parts of it. Think of it like a cookie cutter — the cutter (pattern) either fits the dough (value) or it doesn't.

In most languages, you write:
```
if x == 5 { ... }
if x is a String { ... }
if x is a Some(y) { ... }
```

Rust unifies ALL of this into one powerful, compile-time-checked mechanism: `match`.

### Why Rust's `match` is Different

| Feature | C `switch` | Java `switch` | Rust `match` |
|---|---|---|---|
| Exhaustiveness check | ❌ No | ❌ No | ✅ Yes — compile error |
| Structural decomposition | ❌ No | ❌ No | ✅ Yes |
| Type-safe | ❌ No | Partial | ✅ Full |
| Works on any type | ❌ int only | Limited | ✅ Any type |
| Returns a value | ❌ No | ❌ No | ✅ Yes (expression) |
| Fall-through | ✅ (implicit!) | ✅ (implicit!) | ❌ Never |

### Cognitive Principle: Chunking

When you learn `match`, your brain forms *chunks* — stored patterns of recognition. Every new pattern you learn becomes a chunk. Eventually, reading `if let Some(x) = foo { ... }` costs you zero mental effort — you recognize it instantly. This guide is designed to build those chunks systematically.

---

## 2. The `match` Expression — Core Anatomy

### Vocabulary (Learn these terms exactly)

- **Match expression**: The entire `match value { ... }` construct
- **Scrutinee**: The value being matched — the thing AFTER the `match` keyword
- **Arm**: One branch in the match — `pattern => expression`
- **Pattern**: The left side of `=>`
- **Body/Consequence**: The right side of `=>`
- **Guard**: An optional `if condition` after a pattern

### Basic Syntax Diagram

```
match  <scrutinee>  {
  ^^^^^^ keyword    ^^ open brace

    <pattern>  =>  <body>,
    ^^^^^^^^^      ^^^^^^
    what to       what to
    match         execute

    <pattern>  =>  <body>,   // more arms...

}
^^ close brace
```

### A Complete Example

```rust
fn classify_http_status(code: u16) -> &'static str {
    match code {
        100..=199 => "Informational",
        200..=299 => "Success",
        300..=399 => "Redirection",
        400..=499 => "Client Error",
        500..=599 => "Server Error",
        _         => "Unknown",
    }
}
```

### Key Rules

1. **Arms are checked top-to-bottom** — first match wins
2. **No fall-through** — unlike C, matching one arm does NOT execute the next
3. **Every arm must return the same type** — this is enforced at compile time
4. **The match IS an expression** — it produces a value you can assign
5. **Exhaustiveness is mandatory** — all possible values must be covered

---

## 3. Literal Patterns

### What is a Literal Pattern?

A literal pattern matches an exact, specific value. The word *literal* means "the value written directly in source code."

```rust
fn day_type(day: &str) -> &'static str {
    match day {
        "Saturday" | "Sunday" => "Weekend",  // OR pattern (covered later)
        "Monday"
        | "Tuesday"
        | "Wednesday"
        | "Thursday"
        | "Friday" => "Weekday",
        _ => "Unknown day",
    }
}

fn categorize_score(score: i32) -> &'static str {
    match score {
        100        => "Perfect",
        90..=99    => "Excellent",   // range literal
        0          => "Zero — try again",
        i32::MIN..=-1 => "Negative — invalid",
        _          => "Normal range",
    }
}
```

### Boolean Patterns

```rust
fn describe_flag(enabled: bool) -> &'static str {
    match enabled {
        true  => "Feature is active",
        false => "Feature is disabled",
        // NOTE: No _ needed — bool only has two values, fully exhausted
    }
}
```

**Key insight**: `true` and `false` are literal patterns. The compiler KNOWS bool has exactly two values, so no `_` is needed. This is exhaustiveness checking working for you.

---

## 4. Variable Binding Patterns

### What is a Variable Binding Pattern?

When a pattern is a **name** (not a keyword, not a type), it always matches AND binds the matched value to that name. This is one of the most important pattern types.

```rust
fn describe_number(n: i32) -> String {
    match n {
        0           => String::from("zero"),
        1           => String::from("one"),
        other       => format!("some other number: {}", other),
        //  ^^^^^
        //  This is a BINDING — "other" is now a variable holding n's value
    }
}
```

### Critical Warning: Variable vs Constant

This is a **very common mistake** for beginners and even intermediates:

```rust
const MAGIC: i32 = 42;

fn example(x: i32) {
    match x {
        MAGIC => println!("It's the magic number!"),  // matches constant
        other => println!("Got {}", other),            // binds to variable
    }
}
```

- **UPPERCASE names** → treated as constants (value comparison)
- **lowercase names** → treated as bindings (always matches, captures value)

If you write a lowercase name that happens to be a variable in scope, Rust does NOT compare — it SHADOWS the outer variable with a new binding!

```rust
fn broken_example(x: i32) {
    let expected = 42;
    match x {
        expected => println!("matched!"),  // BUG: this ALWAYS matches!
        // ^^^^^^^^ this shadows the outer `expected`, not compares to it
        _ => println!("no match"),  // This arm is unreachable! Compiler warns.
    }
}
```

**Fix**: Use a guard for comparison against runtime values:
```rust
fn correct_example(x: i32) {
    let expected = 42;
    match x {
        n if n == expected => println!("matched: {}", n),
        _ => println!("no match"),
    }
}
```

---

## 5. Wildcard Pattern `_`

### What is a Wildcard?

The underscore `_` is the "I don't care" pattern. It matches ANYTHING but does NOT bind the value to a name.

```rust
fn handle_command(cmd: &str, arg: Option<i32>) {
    match (cmd, arg) {
        ("quit", _)         => println!("Quitting"),
        //               ^
        //               Don't care what arg is — ignore it
        ("move", Some(n))   => println!("Moving by {}", n),
        ("move", None)      => println!("Move needs an argument"),
        (other, _)          => println!("Unknown command: {}", other),
    }
}
```

### `_` vs `_name`

```rust
fn example(x: i32) {
    match x {
        _         => (),  // Matches and DROPS — ownership transferred and released
        _ignored  => (),  // Matches, binds to _ignored (ownership held briefly), but not used
    }
}
```

**Performance insight**: Using `_` in a pattern causes the compiler to drop the value immediately. Using `_name` holds the binding until end of scope. For types with destructors (implementing `Drop`), this matters.

---

## 6. Range Patterns

### Inclusive Ranges `..=`

```rust
fn ascii_classify(c: char) -> &'static str {
    match c {
        'a'..='z'          => "lowercase letter",
        'A'..='Z'          => "uppercase letter",
        '0'..='9'          => "digit",
        ' ' | '\t' | '\n'  => "whitespace",
        '!'..='/'          => "special (punctuation group 1)",
        _                  => "other",
    }
}
```

### Important: Exclusive ranges `..` are NOT supported in patterns

```rust
// THIS DOES NOT COMPILE:
match x {
    0..10 => ...,   // ERROR: only `..=` (inclusive) allowed in patterns
}

// CORRECT:
match x {
    0..=9 => ...,
}
```

### Why only inclusive? 

Exclusive ranges `0..10` means "0 to 9". But `..=` (0..=9) is explicit about both endpoints. This eliminates off-by-one errors in pattern matching at the language level — a beautiful design decision.

---

## 7. Tuple Patterns

### What is a Tuple?

A tuple is a fixed-size, ordered collection of values of (potentially) different types. Example: `(1, "hello", true)` is a tuple of `(i32, &str, bool)`.

A **tuple pattern** matches a tuple by matching each element positionally.

```rust
fn quadrant(x: i32, y: i32) -> &'static str {
    match (x.signum(), y.signum()) {
        //  ^^^^^^^^^^^^^^^^^^^^^^^^ we create a tuple on-the-fly as scrutinee
        ( 1,  1) => "Quadrant I",
        (-1,  1) => "Quadrant II",
        (-1, -1) => "Quadrant III",
        ( 1, -1) => "Quadrant IV",
        ( 0,  _) => "On Y-axis",
        ( _,  0) => "On X-axis",
        _        => unreachable!("signum only returns -1, 0, or 1"),
    }
}
```

### Tuple Struct Patterns

A tuple struct is a struct that uses positional fields instead of named fields:

```rust
struct Point(f64, f64);
struct Color(u8, u8, u8);

fn describe_color(c: Color) -> String {
    match c {
        Color(0, 0, 0)         => String::from("Black"),
        Color(255, 255, 255)   => String::from("White"),
        Color(r, 0, 0)         => format!("Red shade: {}", r),
        Color(0, g, 0)         => format!("Green shade: {}", g),
        Color(0, 0, b)         => format!("Blue shade: {}", b),
        Color(r, g, b)         => format!("Mixed: ({}, {}, {})", r, g, b),
    }
}
```

---

## 8. Struct Patterns

### What is a Struct Pattern?

Struct patterns match structs by their **field names**, not positions. You can match some fields and ignore others.

```rust
#[derive(Debug)]
struct HttpRequest {
    method: String,
    path:   String,
    version: u8,
    body:   Option<Vec<u8>>,
}

fn route_request(req: &HttpRequest) -> String {
    match req {
        HttpRequest { method, path, .. } if method == "GET" && path == "/" => {
            //                        ^^
            //                        `..` means "ignore remaining fields"
            String::from("Serve homepage")
        }
        HttpRequest { method, path, body: Some(_), .. } if method == "POST" => {
            format!("Handle POST to {}", path)
        }
        HttpRequest { method, path, body: None, .. } if method == "POST" => {
            format!("POST to {} has no body — reject", path)
        }
        HttpRequest { method, .. } => {
            format!("Unhandled method: {}", method)
        }
    }
}
```

### Field Shorthand

When you bind a field to a variable of the SAME name:

```rust
struct Point { x: f64, y: f64 }

fn example(p: Point) {
    match p {
        Point { x, y } => println!("({}, {})", x, y),
        //       ^  ^
        //       Shorthand for x: x, y: y
    }
}
```

### Renaming Fields

```rust
fn example(p: Point) {
    match p {
        Point { x: horizontal, y: vertical } => {
            println!("horizontal={}, vertical={}", horizontal, vertical)
        }
    }
}
```

---

## 9. Enum Patterns — The Crown Jewel

### What is an Enum?

An **enum** (enumeration) is a type that can be one of several **variants**. Each variant can optionally carry data. This is called a *sum type* or *tagged union* in type theory.

Rust's enums are far more powerful than C enums:

```
C enum:      just a named integer
Rust enum:   a type that can BE different shapes, each with its own data
```

### Basic Enum Pattern

```rust
#[derive(Debug)]
enum Direction {
    North,
    South,
    East,
    West,
}

fn opposite(dir: Direction) -> Direction {
    match dir {
        Direction::North => Direction::South,
        Direction::South => Direction::North,
        Direction::East  => Direction::West,
        Direction::West  => Direction::East,
    }
}
```

### Enum with Data — The Power Move

```rust
#[derive(Debug)]
enum NetworkEvent {
    Connected { peer_id: u64, address: String },
    Disconnected { peer_id: u64, reason: String },
    DataReceived { peer_id: u64, bytes: Vec<u8> },
    Error(String),
    Timeout,
}

fn handle_event(event: NetworkEvent) {
    match event {
        NetworkEvent::Connected { peer_id, address } => {
            println!("Peer {} connected from {}", peer_id, address);
        }
        NetworkEvent::Disconnected { peer_id, reason } => {
            println!("Peer {} disconnected: {}", peer_id, reason);
        }
        NetworkEvent::DataReceived { peer_id, bytes } => {
            println!("Peer {} sent {} bytes", peer_id, bytes.len());
        }
        NetworkEvent::Error(msg) => {
            eprintln!("Network error: {}", msg);
        }
        NetworkEvent::Timeout => {
            println!("Connection timed out");
        }
    }
}
```

### `Option<T>` — Built-in Enum

`Option<T>` is just an enum defined in std:
```rust
enum Option<T> {
    Some(T),
    None,
}
```

```rust
fn safe_divide(a: f64, b: f64) -> Option<f64> {
    match b {
        0.0 => None,
        _   => Some(a / b),
    }
}

fn use_result() {
    match safe_divide(10.0, 2.0) {
        Some(result) => println!("Result: {}", result),
        None         => println!("Division by zero"),
    }
}
```

### `Result<T, E>` — Built-in Enum for Error Handling

```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

```rust
use std::num::ParseIntError;

fn parse_and_double(s: &str) -> Result<i32, ParseIntError> {
    match s.trim().parse::<i32>() {
        Ok(n)    => Ok(n * 2),
        Err(e)   => Err(e),
    }
}

// Production pattern: chain results with `?` operator
// (which is syntax sugar for match on Result)
fn parse_and_double_idiomatic(s: &str) -> Result<i32, ParseIntError> {
    let n: i32 = s.trim().parse()?;  // `?` = match { Ok(v) => v, Err(e) => return Err(e) }
    Ok(n * 2)
}
```

---

## 10. Reference & Pointer Patterns

### The `ref` Keyword and `&` Patterns

When you match a value, by default you **move** it (take ownership). But sometimes you want to **borrow** it instead.

```rust
fn count_vowels(text: &str) -> usize {
    text.chars().filter(|&c| {
        //              ^^
        // `&c` is a reference pattern — we dereference the char
        match c {
            'a' | 'e' | 'i' | 'o' | 'u'
            | 'A' | 'E' | 'I' | 'O' | 'U' => true,
            _ => false,
        }
    }).count()
}
```

### Matching References Explicitly

```rust
fn describe_ref(value: &Option<String>) {
    match value {
        &Some(ref s) => println!("Got string: {}", s),
        //      ^^^
        //      `ref s` borrows from inside the Option
        //      without moving out of the reference
        &None        => println!("Nothing"),
    }

    // Idiomatic modern Rust (since match ergonomics):
    match value {
        Some(s) => println!("Got string: {}", s),  // auto-deref
        None    => println!("Nothing"),
    }
}
```

### Match Ergonomics (Rust 2018+)

Modern Rust has "match ergonomics" — when you match a reference, patterns automatically adjust:

```rust
let v: Option<String> = Some(String::from("hello"));
let r: &Option<String> = &v;

// Old way (explicit):
match r {
    &Some(ref s) => println!("{}", s),
    &None => {},
}

// Modern ergonomic way (same behavior):
match r {
    Some(s) => println!("{}", s),  // s is &String, inferred from context
    None => {},
}
```

---

## 11. Guards (Conditional Patterns)

### What is a Guard?

A **guard** is an additional `if condition` after a pattern that must ALSO be true for the arm to match. The pattern matches the SHAPE, the guard matches extra CONDITIONS.

```
pattern  if  condition  =>  body
^^^^^^^  ^^  ^^^^^^^^^
shape    guard keyword  runtime check
```

```rust
fn classify_temperature(temp: f64) -> &'static str {
    match temp {
        t if t < -273.15 => "Below absolute zero — physically impossible",
        t if t < 0.0     => "Below freezing",
        t if t < 20.0    => "Cold",
        t if t < 37.0    => "Comfortable",
        t if t < 100.0   => "Hot",
        _                => "Boiling or above",
    }
}
```

### Guards with Enum Variants

```rust
#[derive(Debug)]
enum Packet {
    Data { size: usize, payload: Vec<u8> },
    Control(u8),
    Heartbeat,
}

const MAX_PACKET_SIZE: usize = 65535;
const VALID_CONTROL_CODES: [u8; 3] = [0x01, 0x02, 0x03];

fn validate_packet(pkt: &Packet) -> bool {
    match pkt {
        Packet::Data { size, .. } if *size == 0 => {
            eprintln!("Empty data packet");
            false
        }
        Packet::Data { size, payload } if *size > MAX_PACKET_SIZE => {
            eprintln!("Packet too large: {} bytes", size);
            false
        }
        Packet::Data { size, payload } if *size != payload.len() => {
            eprintln!("Size mismatch: claimed {} but actual {}", size, payload.len());
            false
        }
        Packet::Data { .. } => true,
        Packet::Control(code) if VALID_CONTROL_CODES.contains(code) => true,
        Packet::Control(code) => {
            eprintln!("Invalid control code: 0x{:02X}", code);
            false
        }
        Packet::Heartbeat => true,
    }
}
```

### Critical: Guards and `|` (Or Patterns)

The guard applies to the ENTIRE or-pattern, not just the last alternative:

```rust
match x {
    1 | 2 | 3 if x % 2 == 0 => println!("even among 1,2,3"),
    // Guard applies to the entire `1 | 2 | 3`, not just `3`
}
```

---

## 12. `@` Bindings

### What is `@`?

The `@` operator lets you **test** a value against a pattern AND **bind** it to a name at the same time.

**Problem without @**: You can check a range OR bind a name, but not both simultaneously.

```rust
// Problem: can't get the value from a range pattern directly
match score {
    90..=100 => println!("High score!"),  // But what WAS the score?
    n        => println!("Score was {}", n),  // No range check here
}
```

**Solution with @**:

```rust
fn grade(score: u32) -> String {
    match score {
        n @ 90..=100 => format!("A — score: {}", n),
        //^^^^^^^^^^ bind AND check range
        n @ 80..=89  => format!("B — score: {}", n),
        n @ 70..=79  => format!("C — score: {}", n),
        n @ 60..=69  => format!("D — score: {}", n),
        n            => format!("F — score: {}", n),
    }
}
```

### `@` in Enum Patterns

```rust
#[derive(Debug)]
enum Message {
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(u8, u8, u8),
}

fn process(msg: &Message) {
    match msg {
        Message::Move { x: x_pos @ 0..=100, y: y_pos @ 0..=100 } => {
            println!("Valid move to ({}, {})", x_pos, y_pos);
        }
        Message::Move { x, y } => {
            println!("Out-of-bounds move to ({}, {})", x, y);
        }
        Message::Write(text @ s) if s.len() > 0 => {
            println!("Writing: {}", text);
        }
        _ => println!("Other message"),
    }
}
```

---

## 13. Or Patterns `|`

### What is an Or Pattern?

The `|` symbol means "match THIS pattern OR THAT pattern." It's a way to handle multiple cases with the same body.

```rust
fn is_punctuation(c: char) -> bool {
    match c {
        '.' | ',' | '!' | '?' | ';' | ':' => true,
        _                                   => false,
    }
}
```

### Or Patterns in Nested Context (Rust 2021+)

Before Rust 2021, `|` only worked at the top level of a match arm. Now it works anywhere inside a pattern:

```rust
#[derive(Debug)]
enum Expr {
    Num(i64),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
    Neg(Box<Expr>),
}

fn is_commutative(expr: &Expr) -> bool {
    match expr {
        Expr::Add(..) | Expr::Mul(..) => true,
        // Or pattern at top level — matches Add OR Mul
        _ => false,
    }
}

// Nested or pattern (Rust 2021):
fn classify(opt: Option<i32>) -> &'static str {
    match opt {
        Some(0 | 1 | 2) => "small positive",
        //       ^^^^^
        //       Or pattern INSIDE Some(...)
        Some(n) if n < 0 => "negative",
        Some(_)           => "large positive",
        None              => "absent",
    }
}
```

---

## 14. Nested Patterns

### What is a Nested Pattern?

Patterns can be nested arbitrarily deep. Match the shape of complex data structures recursively.

```rust
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Box<Tree>, i32, Box<Tree>),
}

fn sum_leaves(tree: &Tree) -> i32 {
    match tree {
        Tree::Leaf(value) => *value,
        Tree::Node(left, _, right) => sum_leaves(left) + sum_leaves(right),
        //         ^^^^       ^^^^^
        //         Recursive nested match — each is also a Tree
    }
}

// Complex nested pattern
fn find_pattern(data: &Option<Result<Vec<i32>, String>>) -> String {
    match data {
        None => String::from("no data"),
        Some(Err(msg)) => format!("error: {}", msg),
        Some(Ok(v)) if v.is_empty() => String::from("empty vector"),
        Some(Ok(v)) if v.len() == 1 => format!("single: {}", v[0]),
        Some(Ok(v)) => format!("vector of {} elements, first={}", v.len(), v[0]),
    }
}
```

---

## 15. Exhaustiveness Checking

### What is Exhaustiveness?

The Rust compiler GUARANTEES that every possible value of the scrutinee is covered by at least one arm. This is called **exhaustiveness checking** and it's one of Rust's most powerful safety features.

```rust
enum Color { Red, Green, Blue }

fn name(c: Color) -> &'static str {
    match c {
        Color::Red   => "red",
        Color::Green => "green",
        // COMPILE ERROR: pattern `Color::Blue` not covered
    }
}
```

### Why This Matters for Real Systems

```rust
// Scenario: You add a new payment method to an existing system

enum PaymentMethod {
    CreditCard { number: String, cvv: u16 },
    BankTransfer { iban: String },
    Crypto { address: String, currency: String },
    // NEW: added 6 months later
    PayPal { email: String },
}

fn process_payment(method: PaymentMethod, amount_cents: u64) {
    match method {
        PaymentMethod::CreditCard { number, cvv }    => { /* ... */ }
        PaymentMethod::BankTransfer { iban }          => { /* ... */ }
        PaymentMethod::Crypto { address, currency }  => { /* ... */ }
        // If you forget PayPal, the COMPILER catches it — not a production incident
        PaymentMethod::PayPal { email }              => { /* ... */ }
    }
}
```

This is the "make illegal states unrepresentable" principle. The type system enforces correctness.

### Using `_` to Opt Out of Exhaustiveness

```rust
fn process_if_important(event: NetworkEvent) {
    match event {
        NetworkEvent::Error(msg) => eprintln!("CRITICAL: {}", msg),
        _ => { /* deliberately ignore all others */ }
    }
}
```

**Warning**: Using `_` means adding new variants won't trigger a compile error. Use wisely.

### `#[non_exhaustive]` Attribute

For library authors — marks an enum/struct so external code MUST use `_`:

```rust
#[non_exhaustive]
pub enum ApiError {
    NotFound,
    Unauthorized,
    RateLimit,
    // Future variants can be added without breaking callers
}
```

---

## 16. Irrefutable vs Refutable Patterns

### Key Definitions

- **Irrefutable pattern**: Always matches, no matter what value is given. Example: `x` (a variable binding matches everything)
- **Refutable pattern**: Might NOT match. Example: `Some(x)` — what if the value is `None`?

```
Irrefutable: let x = 5;        // always works
             let (a, b) = pair; // always works for a tuple

Refutable:   if let Some(x) = opt { ... }   // might be None
             while let Ok(n) = iter.next()   // might be Err
```

### Why This Distinction Matters

Rust enforces:
- `let` statements MUST use irrefutable patterns
- `if let` / `while let` are for refutable patterns
- `match` arms can be refutable (but together must be exhaustive)

```rust
// COMPILE ERROR: refutable pattern in `let`
let Some(x) = some_option;  // ERROR: pattern `None` not covered

// CORRECT:
let x = some_option.unwrap();               // panics if None
let x = some_option.unwrap_or(0);          // default value
if let Some(x) = some_option { /* ... */ } // safe conditional
let Some(x) = some_option else { return }; // let-else (Rust 1.65+)
```

---

## 17. `if let` — Single-Branch Matching

### What is `if let`?

`if let` is sugar for a `match` with one interesting arm and one ignored arm. Use it when you only care about ONE pattern and want to ignore the rest.

```rust
// Full match (verbose when you only care about one case):
match config.get("timeout") {
    Some(value) => println!("Timeout set to {}", value),
    None        => { /* nothing */ }
}

// Equivalent if let (concise):
if let Some(value) = config.get("timeout") {
    println!("Timeout set to {}", value);
}
```

### `if let` with `else`

```rust
fn parse_port(s: &str) -> u16 {
    if let Ok(port) = s.parse::<u16>() {
        if port > 0 {
            return port;
        }
    }
    // else falls through to default
    8080  // default port
}
```

### `if let` Chains (Rust 1.64+)

```rust
fn process(user_id: Option<u64>, permissions: Option<Vec<String>>) {
    if let Some(uid) = user_id
        && let Some(perms) = permissions
        && perms.contains(&String::from("admin"))
    {
        println!("User {} has admin access", uid);
    }
}
```

### Production Usage

```rust
use std::collections::HashMap;

fn get_user_setting(
    settings: &HashMap<String, String>,
    key: &str,
    default: &str,
) -> String {
    if let Some(value) = settings.get(key) {
        value.clone()
    } else {
        default.to_string()
    }
    // Idiomatic one-liner: settings.get(key).cloned().unwrap_or_else(|| default.to_string())
}
```

---

## 18. `while let` — Loop Until No Match

### What is `while let`?

`while let` loops as long as the pattern matches. When it doesn't match, the loop exits.

```rust
fn drain_stack(stack: &mut Vec<i32>) {
    while let Some(top) = stack.pop() {
        println!("Processing: {}", top);
    }
    // Stops when stack is empty (pop() returns None)
}
```

### Real-World: Processing a Channel

```rust
use std::sync::mpsc;

fn consume_messages(receiver: mpsc::Receiver<String>) {
    while let Ok(message) = receiver.recv() {
        println!("Received: {}", message);
        // Loop exits when sender is dropped (recv() returns Err)
    }
    println!("Channel closed, all messages processed");
}
```

### Parsing Until Failure

```rust
fn parse_integers(tokens: &[&str]) -> Vec<i32> {
    let mut result = Vec::new();
    let mut iter = tokens.iter();

    while let Some(&token) = iter.next() {
        if let Ok(n) = token.parse::<i32>() {
            result.push(n);
        }
        // Non-integer tokens are silently skipped
    }
    result
}
```

---

## 19. `let else` — Early Exit Pattern

### What is `let else`?

Introduced in Rust 1.65. `let else` is the "or else we bail out" pattern. It lets you unwrap a pattern, and if it doesn't match, execute a diverging block (return, panic, continue, break).

```rust
fn process_request(raw: &str) -> Result<String, String> {
    let Some(parts) = raw.split_once(':') else {
        return Err(String::from("Invalid format: expected 'key:value'"));
    };
    let (key, value) = parts;
    Ok(format!("key={}, value={}", key, value))
}
```

### vs Alternatives

```rust
// Option 1: match (verbose)
let value = match some_option {
    Some(v) => v,
    None => return Err("missing value".into()),
};

// Option 2: unwrap_or_else (ok for simple cases)
let value = some_option.ok_or("missing value")?;

// Option 3: let else (best readability for complex patterns)
let Some(value) = some_option else {
    return Err("missing value".into());
};
```

### Production: Config Parsing

```rust
fn load_database_config(env: &std::collections::HashMap<String, String>)
    -> Result<DatabaseConfig, String>
{
    let Some(host) = env.get("DB_HOST") else {
        return Err(String::from("DB_HOST is required"));
    };
    let Some(port_str) = env.get("DB_PORT") else {
        return Err(String::from("DB_PORT is required"));
    };
    let Ok(port) = port_str.parse::<u16>() else {
        return Err(format!("DB_PORT must be a valid port number, got: {}", port_str));
    };
    let Some(name) = env.get("DB_NAME") else {
        return Err(String::from("DB_NAME is required"));
    };

    Ok(DatabaseConfig {
        host: host.clone(),
        port,
        name: name.clone(),
    })
}

struct DatabaseConfig {
    host: String,
    port: u16,
    name: String,
}
```

---

## 20. `matches!` Macro

### What is `matches!`?

`matches!` is a convenience macro that returns `bool` instead of producing a value. Perfect for filter predicates and conditions.

```rust
fn is_vowel(c: char) -> bool {
    matches!(c, 'a' | 'e' | 'i' | 'o' | 'u' | 'A' | 'E' | 'I' | 'O' | 'U')
}

fn is_error(result: &Result<i32, String>) -> bool {
    matches!(result, Err(_))
}

fn is_admin(role: &str) -> bool {
    matches!(role, "admin" | "superuser" | "root")
}
```

### `matches!` with Guards

```rust
fn is_valid_score(score: i32) -> bool {
    matches!(score, 0..=100)
}

fn is_large_error(result: &Result<Vec<u8>, String>) -> bool {
    matches!(result, Err(msg) if msg.len() > 50)
}
```

### Filtering Collections

```rust
fn count_errors(results: &[Result<i32, String>]) -> usize {
    results.iter().filter(|r| matches!(r, Err(_))).count()
}

fn get_valid_scores(scores: &[Option<i32>]) -> Vec<i32> {
    scores.iter()
          .filter_map(|s| if let &Some(n) = s { Some(n) } else { None })
          .filter(|&n| matches!(n, 0..=100))
          .collect()
}
```

---

## 21. Destructuring in `let`, `fn`, `for`

### Patterns Everywhere

Patterns don't only appear in `match` — they appear in ANY `let` binding, function parameters, and `for` loops.

### `let` Destructuring

```rust
// Tuple destructuring
let (x, y, z) = (1.0, 2.0, 3.0);

// Struct destructuring
struct Point3D { x: f64, y: f64, z: f64 }
let p = Point3D { x: 1.0, y: 2.0, z: 3.0 };
let Point3D { x, y, z } = p;

// Nested destructuring
let ((a, b), c) = ((1, 2), 3);

// Ignore parts with _
let (first, _, third) = (1, 2, 3);
```

### Function Parameter Destructuring

```rust
fn add_points(&(x1, y1): &(f64, f64), &(x2, y2): &(f64, f64)) -> (f64, f64) {
    //         ^^^^^^^^^^              ^^^^^^^^^^
    //         Pattern in function signature!
    (x1 + x2, y1 + y2)
}

fn print_pair((key, value): (&str, i32)) {
    println!("{}: {}", key, value);
}
```

### `for` Loop Destructuring

```rust
fn main() {
    let pairs = vec![(1, "one"), (2, "two"), (3, "three")];

    for (number, name) in &pairs {
        println!("{} = {}", number, name);
    }

    // Enumerate with destructuring
    for (index, (number, name)) in pairs.iter().enumerate() {
        println!("[{}] {} = {}", index, number, name);
    }

    // HashMap iteration
    use std::collections::HashMap;
    let mut map = HashMap::new();
    map.insert("a", 1);
    map.insert("b", 2);

    for (key, value) in &map {
        println!("{} => {}", key, value);
    }
}
```

---

## 22. Slice Patterns

### What is a Slice Pattern?

Slice patterns match arrays and slices by their structure — including their length and specific element positions.

```rust
fn describe_slice(data: &[i32]) -> String {
    match data {
        []           => String::from("empty"),
        [x]          => format!("single element: {}", x),
        [x, y]       => format!("pair: {} and {}", x, y),
        [first, ..]  => format!("starts with {}, then {} more", first, data.len() - 1),
        //        ^^
        //        `..` matches zero or more elements (rest)
    }
}
```

### Matching Head and Tail

```rust
fn sum_recursive(data: &[i32]) -> i32 {
    match data {
        []              => 0,
        [head, tail @ ..] => head + sum_recursive(tail),
        //      ^^^^^^^^^
        //      `tail @` binds the REST to a variable `tail`
    }
}
```

### First, Middle, Last

```rust
fn first_and_last(data: &[i32]) -> Option<(i32, i32)> {
    match data {
        []                     => None,
        [only]                 => Some((*only, *only)),
        [first, .., last]      => Some((*first, *last)),
        //           ^^^^
        //           `..` skips everything in between
    }
}
```

### Fixed-Length Array Patterns

```rust
fn rgb_to_grayscale([r, g, b]: [u8; 3]) -> u8 {
    // Pattern in function signature for fixed-size array
    ((r as u16 * 299 + g as u16 * 587 + b as u16 * 114) / 1000) as u8
}

fn is_sorted(data: &[i32]) -> bool {
    match data {
        [] | [_]                    => true,
        [a, b, rest @ ..] if a <= b => is_sorted(&data[1..]),
        _                           => false,
    }
}
```

---

## 23. Performance & Compiler Internals

### How `match` Compiles

The Rust/LLVM compiler applies sophisticated optimizations to match expressions:

#### 1. Jump Tables (for integer ranges)
When matching contiguous integers, the compiler generates an O(1) jump table:

```rust
// This compiles to a jump table in assembly — O(1) dispatch
fn opcode_name(op: u8) -> &'static str {
    match op {
        0x00 => "NOP",
        0x01 => "MOV",
        0x02 => "ADD",
        // ... more contiguous opcodes
        _    => "UNKNOWN",
    }
}
```

Assembly equivalent:
```
; jump_table[op] -> handler_address
mov    eax, [jump_table + op*8]
jmp    eax
```

#### 2. Binary Search (for sparse patterns)
For non-contiguous values, the compiler may generate binary search — O(log n).

#### 3. Decision Trees
For enum patterns, the compiler generates minimal decision trees using the **tag** (discriminant) of the enum.

```
match event {                    ; Assembly roughly:
    Event::A(...) => ...,        cmp  discriminant, 0
    Event::B(...) => ...,        je   handle_A
    Event::C(...) => ...,        cmp  discriminant, 1
}                                je   handle_B
                                 jmp  handle_C
```

### Cache Behavior

```rust
// CACHE-FRIENDLY: Enum with small variants stored inline
enum SmallEvent {
    Move(i16, i16),    // 4 bytes
    Click(i16, i16),   // 4 bytes
    Key(char),         // 4 bytes
}
// Total enum size = tag (1 byte) + max_variant = 5 bytes
// Many fit in a cache line (64 bytes) = ~12 events per cache line

// CACHE-UNFRIENDLY: Enum with heap-allocated data
enum BigEvent {
    Move(Vec<f64>),    // 24 bytes (pointer + len + cap) + heap allocation
    Click(String),     // 24 bytes + heap allocation
}
// Each match arm may trigger a cache miss to follow the pointer
```

### Memory Layout of Enums

```rust
enum Option<T> {
    None,           // discriminant = 0
    Some(T),        // discriminant = 1
}

// NICHE OPTIMIZATION: For Box<T>, Option<Box<T>> has the SAME size as Box<T>
// because null pointer is used as the None discriminant
use std::mem::size_of;

fn layout_demo() {
    println!("{}", size_of::<Option<Box<i32>>>());  // == size_of::<Box<i32>>() !
    println!("{}", size_of::<Option<i32>>());        // i32 + discriminant byte
}
```

### Zero-Cost Abstractions

Pattern matching in Rust compiles to the same code as hand-written C-style switch/if chains — there is **no runtime overhead** from using Rust's pattern matching compared to manual dispatch.

---

## 24. Real-World Implementations

### Implementation 1: A Complete Expression Parser

```rust
/// A simple arithmetic expression evaluator using match throughout
#[derive(Debug, Clone)]
enum Token {
    Number(f64),
    Plus,
    Minus,
    Star,
    Slash,
    LeftParen,
    RightParen,
    End,
}

#[derive(Debug)]
enum EvalError {
    DivisionByZero,
    UnexpectedToken(Token),
    UnmatchedParenthesis,
    EmptyExpression,
}

impl std::fmt::Display for EvalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EvalError::DivisionByZero      => write!(f, "Division by zero"),
            EvalError::UnexpectedToken(t)  => write!(f, "Unexpected token: {:?}", t),
            EvalError::UnmatchedParenthesis => write!(f, "Unmatched parenthesis"),
            EvalError::EmptyExpression     => write!(f, "Empty expression"),
        }
    }
}

fn tokenize(input: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let mut chars = input.chars().peekable();

    while let Some(&c) = chars.peek() {
        match c {
            ' ' | '\t' | '\n' => { chars.next(); }
            '+' => { tokens.push(Token::Plus);       chars.next(); }
            '-' => { tokens.push(Token::Minus);      chars.next(); }
            '*' => { tokens.push(Token::Star);       chars.next(); }
            '/' => { tokens.push(Token::Slash);      chars.next(); }
            '(' => { tokens.push(Token::LeftParen);  chars.next(); }
            ')' => { tokens.push(Token::RightParen); chars.next(); }
            '0'..='9' | '.' => {
                let mut num_str = String::new();
                while let Some(&d) = chars.peek() {
                    if d.is_ascii_digit() || d == '.' {
                        num_str.push(d);
                        chars.next();
                    } else {
                        break;
                    }
                }
                if let Ok(n) = num_str.parse::<f64>() {
                    tokens.push(Token::Number(n));
                }
            }
            _ => { chars.next(); } // skip unknown
        }
    }
    tokens.push(Token::End);
    tokens
}
```

### Implementation 2: State Machine

```rust
/// A TCP connection state machine — classic systems programming pattern
#[derive(Debug, Clone, PartialEq)]
enum TcpState {
    Closed,
    Listen,
    SynSent,
    SynReceived,
    Established,
    FinWait1,
    FinWait2,
    CloseWait,
    Closing,
    LastAck,
    TimeWait,
}

#[derive(Debug)]
enum TcpEvent {
    PassiveOpen,
    ActiveOpen,
    SynReceived,
    SynAckReceived,
    AckReceived,
    ApplicationClose,
    FinReceived,
    Timeout,
    Reset,
}

#[derive(Debug)]
enum TransitionError {
    InvalidTransition { from: TcpState, event: TcpEvent },
}

impl TcpState {
    fn transition(self, event: TcpEvent) -> Result<TcpState, TransitionError> {
        match (&self, &event) {
            (TcpState::Closed,       TcpEvent::PassiveOpen)   => Ok(TcpState::Listen),
            (TcpState::Closed,       TcpEvent::ActiveOpen)    => Ok(TcpState::SynSent),
            (TcpState::Listen,       TcpEvent::SynReceived)   => Ok(TcpState::SynReceived),
            (TcpState::SynSent,      TcpEvent::SynAckReceived)=> Ok(TcpState::Established),
            (TcpState::SynReceived,  TcpEvent::AckReceived)   => Ok(TcpState::Established),
            (TcpState::Established,  TcpEvent::ApplicationClose) => Ok(TcpState::FinWait1),
            (TcpState::Established,  TcpEvent::FinReceived)   => Ok(TcpState::CloseWait),
            (TcpState::FinWait1,     TcpEvent::AckReceived)   => Ok(TcpState::FinWait2),
            (TcpState::FinWait1,     TcpEvent::FinReceived)   => Ok(TcpState::Closing),
            (TcpState::FinWait2,     TcpEvent::FinReceived)   => Ok(TcpState::TimeWait),
            (TcpState::CloseWait,    TcpEvent::ApplicationClose) => Ok(TcpState::LastAck),
            (TcpState::Closing,      TcpEvent::AckReceived)   => Ok(TcpState::TimeWait),
            (TcpState::LastAck,      TcpEvent::AckReceived)   => Ok(TcpState::Closed),
            (TcpState::TimeWait,     TcpEvent::Timeout)       => Ok(TcpState::Closed),
            (_, TcpEvent::Reset)                              => Ok(TcpState::Closed),
            _ => Err(TransitionError::InvalidTransition {
                from: self,
                event,
            }),
        }
    }

    fn is_active(&self) -> bool {
        !matches!(self, TcpState::Closed | TcpState::Listen)
    }
}
```

### Implementation 3: Command Dispatch System

```rust
/// Production-grade CLI command dispatcher
use std::collections::HashMap;

#[derive(Debug)]
enum CliArg {
    Flag(String),
    Option { name: String, value: String },
    Positional(String),
}

#[derive(Debug)]
struct ParsedCommand {
    name:      String,
    args:      Vec<CliArg>,
    flags:     Vec<String>,
    options:   HashMap<String, String>,
    positional: Vec<String>,
}

#[derive(Debug)]
enum CommandError {
    UnknownCommand(String),
    MissingArgument { command: String, arg: String },
    InvalidArgument { arg: String, reason: String },
    IoError(std::io::Error),
}

impl std::fmt::Display for CommandError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CommandError::UnknownCommand(cmd) =>
                write!(f, "Unknown command: '{}'", cmd),
            CommandError::MissingArgument { command, arg } =>
                write!(f, "Command '{}' requires argument '{}'", command, arg),
            CommandError::InvalidArgument { arg, reason } =>
                write!(f, "Invalid argument '{}': {}", arg, reason),
            CommandError::IoError(e) =>
                write!(f, "I/O error: {}", e),
        }
    }
}

fn dispatch_command(cmd: &ParsedCommand) -> Result<(), CommandError> {
    match cmd.name.as_str() {
        "help" | "h" | "?" => {
            print_help();
            Ok(())
        }
        "version" | "v" => {
            println!("v1.0.0");
            Ok(())
        }
        "add" => {
            let Some(file) = cmd.positional.first() else {
                return Err(CommandError::MissingArgument {
                    command: String::from("add"),
                    arg:     String::from("file"),
                });
            };
            let force = cmd.flags.contains(&String::from("force"));
            handle_add(file, force)
        }
        "remove" | "rm" => {
            match (cmd.positional.first(), cmd.flags.contains(&String::from("recursive"))) {
                (None, _)         => Err(CommandError::MissingArgument {
                    command: String::from("remove"),
                    arg: String::from("path"),
                }),
                (Some(path), true)  => handle_remove_recursive(path),
                (Some(path), false) => handle_remove(path),
            }
        }
        "set" => {
            match (
                cmd.options.get("key"),
                cmd.options.get("value"),
            ) {
                (Some(k), Some(v)) => handle_set(k, v),
                (None, _)          => Err(CommandError::MissingArgument {
                    command: String::from("set"),
                    arg: String::from("--key"),
                }),
                (_, None)          => Err(CommandError::MissingArgument {
                    command: String::from("set"),
                    arg: String::from("--value"),
                }),
            }
        }
        other => Err(CommandError::UnknownCommand(String::from(other))),
    }
}

fn print_help() { println!("Available commands: help, version, add, remove, set"); }
fn handle_add(file: &str, force: bool) -> Result<(), CommandError> { Ok(()) }
fn handle_remove(path: &str) -> Result<(), CommandError> { Ok(()) }
fn handle_remove_recursive(path: &str) -> Result<(), CommandError> { Ok(()) }
fn handle_set(key: &str, value: &str) -> Result<(), CommandError> { Ok(()) }
```

### Implementation 4: Type-Safe Builder with Match

```rust
/// Validated configuration builder
#[derive(Debug)]
enum BuildError {
    MissingField(&'static str),
    InvalidValue { field: &'static str, value: String, reason: &'static str },
}

#[derive(Debug)]
struct ServerConfig {
    host:           String,
    port:           u16,
    max_connections: u32,
    tls_enabled:    bool,
    timeout_secs:   u64,
}

#[derive(Default)]
struct ServerConfigBuilder {
    host:            Option<String>,
    port:            Option<u16>,
    max_connections: Option<u32>,
    tls_enabled:     Option<bool>,
    timeout_secs:    Option<u64>,
}

impl ServerConfigBuilder {
    fn new() -> Self {
        Self::default()
    }

    fn host(mut self, host: impl Into<String>) -> Self {
        self.host = Some(host.into());
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }

    fn max_connections(mut self, n: u32) -> Self {
        self.max_connections = Some(n);
        self
    }

    fn tls(mut self, enabled: bool) -> Self {
        self.tls_enabled = Some(enabled);
        self
    }

    fn timeout(mut self, secs: u64) -> Self {
        self.timeout_secs = Some(secs);
        self
    }

    fn build(self) -> Result<ServerConfig, BuildError> {
        // Pattern matching on tuple of Options — elegant multi-field validation
        let host = match self.host {
            Some(h) if !h.is_empty() => h,
            Some(_) => return Err(BuildError::InvalidValue {
                field: "host",
                value: String::from("(empty)"),
                reason: "host cannot be empty",
            }),
            None => return Err(BuildError::MissingField("host")),
        };

        let port = match self.port {
            Some(0) => return Err(BuildError::InvalidValue {
                field: "port",
                value: String::from("0"),
                reason: "port 0 is reserved",
            }),
            Some(p) => p,
            None    => 8080, // sensible default
        };

        let max_connections = match self.max_connections {
            Some(0) => return Err(BuildError::InvalidValue {
                field: "max_connections",
                value: String::from("0"),
                reason: "must allow at least one connection",
            }),
            Some(n) => n,
            None    => 1024, // default
        };

        Ok(ServerConfig {
            host,
            port,
            max_connections,
            tls_enabled:  self.tls_enabled.unwrap_or(false),
            timeout_secs: self.timeout_secs.unwrap_or(30),
        })
    }
}

fn main() {
    let config = ServerConfigBuilder::new()
        .host("0.0.0.0")
        .port(443)
        .tls(true)
        .max_connections(10_000)
        .timeout(60)
        .build();

    match config {
        Ok(cfg)  => println!("Server configured: {:?}", cfg),
        Err(e)   => match e {
            BuildError::MissingField(f)        => eprintln!("Missing: {}", f),
            BuildError::InvalidValue { field, value, reason } =>
                eprintln!("Invalid {}: '{}' — {}", field, value, reason),
        },
    }
}
```

---

## Master Reference: Pattern Syntax Cheat Sheet

```
Pattern Type          Syntax                     Matches
─────────────────────────────────────────────────────────────
Literal               42, 'a', "hello", true     Exact value
Variable binding      x, name, value             Anything, binds to name
Wildcard              _                           Anything, ignores value
Range (inclusive)     1..=9, 'a'..='z'           Value in range
Tuple                 (a, b, c)                  Tuple of matching elements
Struct                Point { x, y }             Struct with named fields
Struct ignore rest    Point { x, .. }            Struct, ignore remaining
Enum variant (unit)   Direction::North           Specific variant
Enum variant (tuple)  Some(x), Ok(v)             Variant with payload
Enum variant (struct) Err { code, msg }          Variant with named fields
Or pattern            A | B | C                  Any of the alternatives
Reference             &x, ref x                  Dereference/borrow
@ binding             n @ 1..=9                  Match AND bind
Guard                 pat if condition            Pattern + extra condition
Slice (exact)         [a, b, c]                  Exactly 3 elements
Slice (head)          [head, ..]                 One+ elements, bind first
Slice (tail)          [.., last]                 One+ elements, bind last
Slice (both)          [first, .., last]          Two+ elements, bind ends
Rest binding          tail @ ..                  Bind rest of slice
Nested                Some((a, b))               Deeply nested structure
```

---

## Summary: Mental Models for Mastery

1. **Pattern = Shape** — A pattern describes the shape of data, not just its value
2. **Exhaustiveness = Safety Net** — The compiler catches every missed case
3. **match = Expression** — Always produces a value, usable anywhere
4. **Left of `=>` = Pattern, Right of `=>` = Code**
5. **Guards refine patterns** — When shape alone isn't enough
6. **@ binds AND tests** — The only way to test a range and get the value
7. **`if let` = one-arm match** — Use when only one case matters
8. **`let else` = early exit** — Use for validation with clean error paths
9. **`_` drops, `_name` binds** — Subtle but matters for Drop types
10. **Match compiles to jumps** — Zero overhead, maximally optimized

---

# The Complete `match` Guide — Rust Pattern Matching Mastery

Here is the full breakdown. Every concept is self-contained and builds on the last.

---

## 1. What is Pattern Matching?

**Pattern matching** is checking a value against a *shape* and extracting parts of it if it fits. Rust unifies every comparison, destructuring, and conditional dispatch into one compile-time-guaranteed mechanism: `match`.

The critical differences from C/Java `switch`:

| Feature | C `switch` | Rust `match` |
|---|---|---|
| Exhaustiveness check | ❌ No | ✅ Compile error if incomplete |
| Structural decomposition | ❌ No | ✅ Full |
| Fall-through | ✅ (implicit bug trap) | ❌ Never |
| Returns a value | ❌ | ✅ It's an expression |
| Works on any type | ❌ integers only | ✅ Any type |

---

## 2. The `match` Expression — Core Anatomy

```
match  <scrutinee>  {
    <pattern>  =>  <body>,
    <pattern>  =>  <body>,
}
```

**Vocabulary you must know cold:**
- **Scrutinee** — the value being matched (after the `match` keyword)
- **Arm** — one branch: `pattern => body`
- **Pattern** — the LEFT side of `=>`
- **Guard** — optional `if condition` after a pattern
- **Exhaustiveness** — ALL possible values must be covered, or it won't compile

**Key rules:**
1. Arms are checked **top-to-bottom** — first match wins
2. **No fall-through** — ever
3. All arms must return **the same type**
4. `match` is an **expression** — it produces a value

---

## 3. Literal Patterns

Matches an exact, hard-coded value:

```rust
fn classify_http_status(code: u16) -> &'static str {
    match code {
        100..=199 => "Informational",
        200..=299 => "Success",
        300..=399 => "Redirection",
        400..=499 => "Client Error",
        500..=599 => "Server Error",
        _         => "Unknown",
    }
}
```

Booleans are fully exhaustible — no `_` needed:
```rust
fn describe_flag(enabled: bool) -> &'static str {
    match enabled {
        true  => "Feature is active",
        false => "Feature is disabled",
        // No `_` needed — bool has exactly 2 values
    }
}
```

---

## 4. Variable Binding Patterns

A **lowercase name** in a pattern ALWAYS matches AND binds the value. It never does a comparison.

```rust
fn describe_number(n: i32) -> String {
    match n {
        0     => String::from("zero"),
        1     => String::from("one"),
        other => format!("some other number: {}", other),
        //  ^^^^^  This is a binding — `other` holds n's value
    }
}
```

### ⚠️ The Classic Trap

```rust
let expected = 42;
match x {
    expected => println!("matched!"),  // BUG: always matches! Shadows outer `expected`
    _ => println!("no match"),         // Unreachable — compiler warns
}

// CORRECT: use a guard
match x {
    n if n == expected => println!("matched: {}", n),
    _ => println!("no match"),
}
```

**Rule:** UPPERCASE = constant comparison. lowercase = binding (always matches).

---

## 5. Wildcard `_`, Range `..=`, Or `|`

```rust
// Wildcard: matches anything, discards value
match x {
    42 => println!("the answer"),
    _  => println!("something else"),  // `_` drops the value
}

// Range (inclusive only — exclusive `..` is NOT valid in patterns):
match score {
    90..=100 => "A",
    80..=89  => "B",
    _        => "F",
}

// Or pattern:
fn is_vowel(c: char) -> bool {
    match c {
        'a' | 'e' | 'i' | 'o' | 'u'
        | 'A' | 'E' | 'I' | 'O' | 'U' => true,
        _ => false,
    }
}
```

**Why only `..=`?** Exclusive ranges like `0..10` create off-by-one ambiguity. Rust forces you to be explicit at both ends. This is a language-level off-by-one prevention.

---

## 6. Tuple Patterns

Match a tuple by destructuring each element positionally:

```rust
fn quadrant(x: i32, y: i32) -> &'static str {
    match (x.signum(), y.signum()) {
        ( 1,  1) => "Quadrant I",
        (-1,  1) => "Quadrant II",
        (-1, -1) => "Quadrant III",
        ( 1, -1) => "Quadrant IV",
        ( 0,  _) => "On Y-axis",
        ( _,  0) => "On X-axis",
        _        => unreachable!(),
    }
}
```

---

## 7. Struct Patterns

Match structs by **field names**. Use `..` to ignore remaining fields:

```rust
struct HttpRequest { method: String, path: String, version: u8, body: Option<Vec<u8>> }

fn route(req: &HttpRequest) -> String {
    match req {
        HttpRequest { method, path, .. } if method == "GET" && path == "/" => {
            String::from("Serve homepage")
        }
        HttpRequest { method, path, body: Some(_), .. } if method == "POST" => {
            format!("POST to {}", path)
        }
        HttpRequest { method, .. } => {
            format!("Unhandled: {}", method)
        }
    }
}
```

Field shorthand — when binding to same name: `Point { x, y }` means `Point { x: x, y: y }`.

---

## 8. Enum Patterns — The Crown Jewel

This is where Rust's `match` truly shines. Enums are *sum types* — they can BE one of multiple shapes, each with its own data.

```rust
#[derive(Debug)]
enum NetworkEvent {
    Connected   { peer_id: u64, address: String },
    Disconnected{ peer_id: u64, reason: String  },
    DataReceived{ peer_id: u64, bytes: Vec<u8>  },
    Error(String),
    Timeout,
}

fn handle_event(event: NetworkEvent) {
    match event {
        NetworkEvent::Connected    { peer_id, address }  => println!("{} connected from {}", peer_id, address),
        NetworkEvent::Disconnected { peer_id, reason }   => println!("{} disconnected: {}", peer_id, reason),
        NetworkEvent::DataReceived { peer_id, bytes }    => println!("{} sent {} bytes", peer_id, bytes.len()),
        NetworkEvent::Error(msg)                         => eprintln!("Error: {}", msg),
        NetworkEvent::Timeout                            => println!("Timed out"),
    }
}
```

**Exhaustiveness at work:** Add a new variant to `NetworkEvent`, and every `match` on it in your entire codebase becomes a compile error. This catches whole classes of bugs that would be silent in any other language.

---

## 9. Guards — Conditional Patterns

A **guard** adds an `if condition` after a pattern. The pattern checks shape; the guard checks logic:

```rust
fn classify_temp(temp: f64) -> &'static str {
    match temp {
        t if t < -273.15 => "Physically impossible",
        t if t < 0.0     => "Below freezing",
        t if t < 37.0    => "Normal range",
        t if t < 100.0   => "Hot",
        _                => "Boiling or above",
    }
}

// Guards with enum data:
const MAX_PACKET: usize = 65535;

fn validate(pkt: &Packet) -> bool {
    match pkt {
        Packet::Data { size, payload } if *size != payload.len() => {
            eprintln!("Size mismatch: claimed {} actual {}", size, payload.len());
            false
        }
        Packet::Data { size, .. } if *size > MAX_PACKET => false,
        _ => true,
    }
}
```

**Critical:** Guard applies to the ENTIRE arm, including or-patterns: `1 | 2 | 3 if x % 2 == 0` applies the guard to all three.

---

## 10. `@` Bindings — Bind AND Test

`@` lets you match a range/pattern AND capture the value simultaneously — the only way to do both:

```rust
fn grade(score: u32) -> String {
    match score {
        n @ 90..=100 => format!("A — score: {}", n),
        //^^^^^^^^^^ bind n AND verify it's in 90..=100
        n @ 80..=89  => format!("B — score: {}", n),
        n @ 70..=79  => format!("C — score: {}", n),
        n            => format!("F — score: {}", n),
    }
}
```

Without `@`, you'd have a range pattern (no binding) OR a variable binding (no range check), never both.

---

## 11. Slice Patterns

Match arrays and slices by structure — length and position:

```rust
fn describe_slice(data: &[i32]) -> String {
    match data {
        []               => String::from("empty"),
        [x]              => format!("single: {}", x),
        [x, y]           => format!("pair: {} and {}", x, y),
        [first, .., last]=> format!("from {} to {}, total: {}", first, last, data.len()),
        //              ^^  `..` skips any number of middle elements
    }
}

// Bind the tail:
fn sum_recursive(data: &[i32]) -> i32 {
    match data {
        []                 => 0,
        [head, tail @ ..] => head + sum_recursive(tail),
        //      ^^^^^^^^^  bind the REST to `tail`
    }
}
```

---

## 12. Irrefutable vs Refutable Patterns

**Irrefutable** — always matches. Used in `let`, function args, `for`:
```rust
let (x, y) = (1, 2);          // always works
let Point { x, y } = point;   // always works
```

**Refutable** — might not match. Used in `if let`, `while let`, `match`:
```rust
// COMPILE ERROR: `let Some(x) = opt` — what if it's None?
let Some(x) = some_option;   // ERROR

// CORRECT:
if let Some(x) = some_option { ... }
let Some(x) = some_option else { return };  // let-else
```

---

## 13. `if let`, `while let`, `let else`

```rust
// if let — one-arm match, ignore other cases
if let Some(value) = config.get("timeout") {
    println!("Timeout: {}", value);
}

// while let — loop until pattern fails
fn drain(stack: &mut Vec<i32>) {
    while let Some(top) = stack.pop() {
        println!("Processing: {}", top);
    }
}

// let else (Rust 1.65+) — unwrap or bail out
fn load_config(env: &std::collections::HashMap<String, String>) -> Result<(), String> {
    let Some(host) = env.get("HOST") else {
        return Err(String::from("HOST is required"));
    };
    let Some(port_str) = env.get("PORT") else {
        return Err(String::from("PORT is required"));
    };
    let Ok(port) = port_str.parse::<u16>() else {
        return Err(format!("Invalid PORT: {}", port_str));
    };
    println!("{}:{}", host, port);
    Ok(())
}
```

`let else` is the cleanest pattern for sequential validation. Far more readable than nested `match` or `if let`.

---

## 14. `matches!` Macro

Returns a `bool` — ideal for predicates and filters:

```rust
fn is_vowel(c: char) -> bool {
    matches!(c, 'a' | 'e' | 'i' | 'o' | 'u' | 'A' | 'E' | 'I' | 'O' | 'U')
}

fn count_errors(results: &[Result<i32, String>]) -> usize {
    results.iter().filter(|r| matches!(r, Err(_))).count()
}

// With guards:
fn is_large_error(r: &Result<Vec<u8>, String>) -> bool {
    matches!(r, Err(msg) if msg.len() > 50)
}
```

---

## 15. Destructuring in `let`, `fn`, `for`

Patterns appear everywhere, not just `match`:

```rust
// let
let (x, y, z) = (1.0, 2.0, 3.0);
let Point { x, y } = point;
let [first, _, third] = [1, 2, 3];

// Function parameters
fn add_points(&(x1, y1): &(f64, f64), &(x2, y2): &(f64, f64)) -> (f64, f64) {
    (x1 + x2, y1 + y2)
}

// for loops
let pairs = vec![(1, "one"), (2, "two")];
for (number, name) in &pairs {
    println!("{} = {}", number, name);
}
for (i, (num, name)) in pairs.iter().enumerate() {
    println!("[{}] {} = {}", i, num, name);
}
```

---

## 16. Performance — What the Compiler Does

**Jump table** — for contiguous integers, `match` compiles to O(1) dispatch:
```rust
// This becomes a hardware jump table — constant time
fn opcode_name(op: u8) -> &'static str {
    match op {
        0x00 => "NOP", 0x01 => "MOV", 0x02 => "ADD", /* ... */ _ => "UNK",
    }
}
```

**Niche optimization** — `Option<Box<T>>` is the same size as `Box<T>`. Rust uses the null pointer as the `None` discriminant — zero overhead:
```rust
use std::mem::size_of;
assert_eq!(size_of::<Option<Box<i32>>>(), size_of::<Box<i32>>());  // true!
```

**Zero-cost abstraction** — pattern matching compiles to the exact same code as hand-written C if-chains. There is no abstraction penalty.

**Cache behavior** — prefer small enum variants (stored inline) over variants with heap-allocated data, since each pointer dereference in a match arm is a potential cache miss.

---

## 17. State Machine — Canonical Real-World Pattern

```rust
#[derive(Debug, Clone, PartialEq)]
enum TcpState { Closed, Listen, SynSent, SynReceived, Established,
                FinWait1, FinWait2, CloseWait, Closing, LastAck, TimeWait }

#[derive(Debug)]
enum TcpEvent { PassiveOpen, ActiveOpen, SynReceived, SynAckReceived,
                AckReceived, ApplicationClose, FinReceived, Timeout, Reset }

impl TcpState {
    fn transition(self, event: TcpEvent) -> Result<TcpState, String> {
        match (&self, &event) {
            (TcpState::Closed,      TcpEvent::PassiveOpen)      => Ok(TcpState::Listen),
            (TcpState::Closed,      TcpEvent::ActiveOpen)       => Ok(TcpState::SynSent),
            (TcpState::SynSent,     TcpEvent::SynAckReceived)   => Ok(TcpState::Established),
            (TcpState::Established, TcpEvent::ApplicationClose) => Ok(TcpState::FinWait1),
            (TcpState::Established, TcpEvent::FinReceived)      => Ok(TcpState::CloseWait),
            (TcpState::FinWait1,    TcpEvent::AckReceived)      => Ok(TcpState::FinWait2),
            (TcpState::FinWait2,    TcpEvent::FinReceived)      => Ok(TcpState::TimeWait),
            (_,                     TcpEvent::Reset)            => Ok(TcpState::Closed),
            _ => Err(format!("Invalid: {:?} + {:?}", self, event)),
        }
    }
}
```

The state machine pattern is where `match` eliminates entire classes of state-transition bugs. Every legal transition is explicit. Every illegal one returns `Err`. The type system enforces the protocol.

---

## Master Pattern Reference

```
Pattern              Syntax                Meaning
─────────────────────────────────────────────────────────────────────
Literal              42, 'a', true         Exact value comparison
Binding              name                  Always matches, captures value
Wildcard             _                     Always matches, discards value
Range                1..=9, 'a'..='z'      Value within inclusive range
Or                   A | B | C             Any of the alternatives
Tuple                (a, b, c)             Positional element matching
Struct               Point { x, y }        Named field matching
Struct ignore rest   Point { x, .. }       Named fields + ignore rest
Enum unit            Color::Red            Exact variant
Enum tuple           Some(x), Ok(v)        Variant with payload
Enum struct          Err { code }          Variant with named fields
Guard                pat if cond           Pattern AND runtime condition
@ binding            n @ 1..=9             Match range AND bind name
Slice exact          [a, b, c]             Exactly N elements
Slice head           [head, ..]            First + ignore rest
Slice tail           [.., last]            Ignore + last element
Slice both ends      [first, .., last]     First + last, skip middle
Rest binding         tail @ ..             Bind remaining slice
Nested               Some((a, b))          Recursive composition
Reference            &x                    Dereference in pattern
```

---

## Cognitive Principle: The Chunking Map

When you first see `match`, you parse it symbol by symbol. After deliberate practice across all 24 patterns above, your brain *chunks* the entire construct — you see `Some(n @ 1..=100) if n % 2 == 0` and instantly read it as "even number between 1 and 100, bound to n." That's the chunking effect. The guide above is structured so each new pattern you learn becomes a reusable mental chunk, compounding in complexity until you can read and write any combination fluently.

The downloadable guide above contains all four real-world implementations (expression parser, TCP state machine, CLI dispatcher, validated builder) with full production-grade code.