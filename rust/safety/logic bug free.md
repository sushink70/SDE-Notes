# Writing Logic Bug-Free Code in Rust
## A Complete, In-Depth Guide

---

## Table of Contents

1. [The Mental Model: What Is a Logic Bug?](#1-the-mental-model-what-is-a-logic-bug)
2. [The Spectrum of Guarantees](#2-the-spectrum-of-guarantees)
3. [Make Illegal States Unrepresentable](#3-make-illegal-states-unrepresentable)
4. [The Type System as a Logic Enforcer](#4-the-type-system-as-a-logic-enforcer)
5. [Enums: The Most Powerful Logic Tool in Rust](#5-enums-the-most-powerful-logic-tool-in-rust)
6. [The Typestate Pattern](#6-the-typestate-pattern)
7. [Phantom Types](#7-phantom-types)
8. [Newtype Pattern](#8-newtype-pattern)
9. [Parse, Don't Validate](#9-parse-dont-validate)
10. [Total Functions vs. Partial Functions](#10-total-functions-vs-partial-functions)
11. [Invariants: The Core Concept](#11-invariants-the-core-concept)
12. [Error Handling as Logic Correctness](#12-error-handling-as-logic-correctness)
13. [Traits as Logical Contracts](#13-traits-as-logical-contracts)
14. [State Machines in Rust](#14-state-machines-in-rust)
15. [Domain Modeling for Correctness](#15-domain-modeling-for-correctness)
16. [Builder Pattern for Invariant Construction](#16-builder-pattern-for-invariant-construction)
17. [Assertions, Contracts, and Defensive Programming](#17-assertions-contracts-and-defensive-programming)
18. [Property-Based Testing](#18-property-based-testing)
19. [Formal Verification Tools for Rust](#19-formal-verification-tools-for-rust)
20. [Concurrency Logic Correctness](#20-concurrency-logic-correctness)
21. [Algorithm Correctness Patterns](#21-algorithm-correctness-patterns)
22. [Anti-Patterns That Introduce Logic Bugs](#22-anti-patterns-that-introduce-logic-bugs)
23. [The Mental Checklist: A Systematic Thinking Process](#23-the-mental-checklist-a-systematic-thinking-process)

---

## 1. The Mental Model: What Is a Logic Bug?

Before you can eliminate logic bugs, you need a sharp definition of what they are.

### Memory Bug vs. Logic Bug

Rust already eliminates **memory bugs** at compile time:
- Use-after-free
- Double-free
- Buffer overflow
- Data races

A **logic bug** is fundamentally different. It is a situation where:
- The program compiles cleanly
- The program does not crash
- The program produces an incorrect result or enters an invalid state

```
MEMORY BUG:           LOGIC BUG:
Program crashes   vs  Program runs fine but does the WRONG thing
Rust catches it   vs  Rust cannot catch it (it doesn't know what "right" means)
```

### Categories of Logic Bugs

```
Logic Bugs
├── Semantic Errors
│   ├── Off-by-one (< vs <=, 0-indexed confusion)
│   ├── Wrong formula (e.g., area = l + w instead of l * w)
│   └── Wrong units (meters vs. kilometers, radians vs. degrees)
│
├── State Errors
│   ├── Invalid state reached (e.g., "connected" before "authenticated")
│   ├── Stale state (reading old data after update)
│   └── Partial update (updating field A but forgetting field B)
│
├── Boundary / Edge Case Errors
│   ├── Empty input not handled
│   ├── Single-element input treated as multi-element
│   └── Integer overflow (wrapping, saturating, panicking)
│
├── Assumption Violations
│   ├── Assuming sorted input when it isn't
│   ├── Assuming unique input when duplicates exist
│   └── Assuming non-null/non-empty when it is
│
└── Concurrency Logic Errors
    ├── Wrong ordering of operations (not data race — logic race)
    ├── Missed event / notification
    └── TOCTOU (Time-of-Check-Time-of-Use)
```

### The Core Insight

The goal is to move bug detection **left** on this timeline:

```
RUNTIME (worst)  →  TEST TIME  →  COMPILE TIME (best)
       crash/wrong result     test fails     won't compile
```

Rust gives you the tools to move logic guarantees toward compile time. This guide is about using every one of those tools.

---

## 2. The Spectrum of Guarantees

Different techniques give different levels of confidence. Understand this spectrum:

```
STRONGEST                                                    WEAKEST
    │                                                            │
    ▼                                                            ▼
Dependent   Typestate   Refinement   Property    Unit/          None
 Types      Pattern      Types       Testing   Integration
(Idris)    (Rust ✓)   (Prusti ✓)  (proptest)   Tests
```

In Rust, you can achieve:
- **Compile-time guarantees** via the type system (typestate, phantom types, newtypes, enums)
- **Near-compile-time guarantees** via formal verification tools (Prusti, Kani)
- **High-confidence runtime guarantees** via property-based testing (proptest)
- **Reasonable confidence** via assertions and contracts (debug_assert!, invariant checks)

This guide covers all of these layers. A robust system uses **all layers together**.

---

## 3. Make Illegal States Unrepresentable

This is the single most important principle for logic-correct code. It comes from typed functional programming and translates perfectly to Rust.

### The Idea

If an invalid state **cannot be expressed in the type system**, it literally cannot exist at runtime.

### Bad Example: Representable Invalid States

```rust
// BAD: This struct can represent invalid combinations
struct User {
    email: Option<String>,
    email_verified: bool,  // LOGIC BUG WAITING: verified=true but email=None is possible!
    is_guest: bool,
    username: Option<String>,  // LOGIC BUG WAITING: non-guest with no username is possible!
}
```

This allows:
- `email = None, email_verified = true` — logically impossible
- `is_guest = false, username = None` — logically impossible

Both invalid states compile and run with no error.

### Good Example: Invalid States Cannot Be Constructed

```rust
// GOOD: The type system encodes what's valid

enum EmailStatus {
    Unverified(String),  // has email, not yet verified
    Verified(String),    // has email, verified
}

enum UserKind {
    Guest,
    Registered {
        username: String,
        email: EmailStatus,
    },
}

struct User {
    kind: UserKind,
}
```

Now:
- A guest cannot have a username (the type doesn't allow it)
- A registered user MUST have a username (required by the type)
- Email verification status is tied to the email string — you can't have `verified` without an email address

This is not just documentation — the **compiler enforces it**.

### The General Principle

Ask yourself about every struct and enum:
> "What combinations of fields represent invalid application states? Can I restructure the types so those combinations cannot be expressed?"

```
PROCESS:
1. List all the rules / invariants of your domain
2. For each rule, ask: "Is this rule expressible in the type system?"
3. If yes: encode it in types
4. If no: encode it with a constructor + private fields + assertions
```

---

## 4. The Type System as a Logic Enforcer

Rust's type system is more expressive than most mainstream languages. Here is how each feature enforces logic.

### 4.1 Strong Static Typing

Unlike C, Rust does not silently coerce types.

```rust
// This is a COMPILE ERROR — Rust won't silently convert
fn add_meters(a: f64, b: f64) -> f64 { a + b }

let distance_km: f64 = 5.0;
let distance_m: f64 = 3000.0;
let result = add_meters(distance_km, distance_m); // compiles but WRONG LOGIC
```

The fix is to use the type system to distinguish them (see Newtype Pattern, section 8).

### 4.2 No Implicit Null

In Rust, `null` does not exist. Every value that might be absent is wrapped in `Option<T>`.

```rust
// You CANNOT do this — it's a compile error:
let x: String = None;  // ERROR

// You MUST do this:
let x: Option<String> = None;  // explicit absence

// And you MUST handle the None case:
match x {
    Some(s) => println!("{}", s),
    None => println!("absent"),
}
```

This eliminates the entire class of null-pointer logic bugs.

### 4.3 Exhaustive Pattern Matching

When you match on an enum, Rust **requires** you to handle every variant. You cannot accidentally forget a case.

```rust
enum TrafficLight {
    Red,
    Yellow,
    Green,
}

fn should_stop(light: TrafficLight) -> bool {
    match light {
        TrafficLight::Red => true,
        TrafficLight::Yellow => true,
        // COMPILE ERROR if you forget TrafficLight::Green
        TrafficLight::Green => false,
    }
}
```

If you later add a new variant `TrafficLight::BlinkingRed`, every `match` on `TrafficLight` in your codebase will **fail to compile** until you handle the new case. This is a logic-correctness superpower.

### 4.4 The Borrow Checker as a Logic Tool

The borrow checker isn't just about memory — it also prevents certain logic bugs around aliasing:

```rust
// This prevents a class of logic bugs where you modify a collection
// while iterating it — a classic bug in many languages
let mut v = vec![1, 2, 3];
let first = &v[0];
v.push(4);         // COMPILE ERROR: cannot borrow `v` as mutable
println!("{}", first); // because `first` still holds an immutable borrow
```

This catches the "iterator invalidation" logic bug at compile time.

---

## 5. Enums: The Most Powerful Logic Tool in Rust

Rust's enums are **algebraic data types** (sum types). They are fundamentally different from C/Java enums. Each variant can carry different data, and the type system tracks which variant you have.

### 5.1 Sum Types vs. Product Types

```
PRODUCT TYPE (struct): ALL fields exist simultaneously
    User { name: String, age: u32 }
    → name AND age, always

SUM TYPE (enum): EXACTLY ONE variant exists at a time
    Shape { Circle(f64), Rectangle(f64, f64), Triangle(f64, f64, f64) }
    → Circle OR Rectangle OR Triangle, never two at once
```

This distinction is critical for logic correctness. Many bugs come from using product types when sum types are appropriate.

### 5.2 Modeling Mutually Exclusive States

```rust
// BAD: Using a struct with flags — allows invalid combinations
struct Connection {
    is_connecting: bool,
    is_connected: bool,
    is_closed: bool,
    // What if all three are true? Undefined behavior in your logic.
}

// GOOD: Enum makes states mutually exclusive by construction
enum ConnectionState {
    Connecting,
    Connected { session_id: u64 },
    Closed { reason: CloseReason },
}
```

With the enum, it is **impossible** to be simultaneously connecting and connected.

### 5.3 Carrying State-Specific Data

Each variant carries only the data that makes sense for that state:

```rust
enum PaymentResult {
    Success {
        transaction_id: String,
        amount_charged: f64,
    },
    Declined {
        reason: DeclineReason,
        retry_allowed: bool,
    },
    Pending {
        confirmation_url: String,
        expires_at: Instant,
    },
}
```

You can only access `transaction_id` when the payment succeeded. Accessing it on a `Declined` result is a compile error. Compare this to a struct with lots of `Option` fields where the developer must mentally track which combinations are valid.

### 5.4 The Never Type (`!`)

The `!` (never) type represents computations that never complete (they diverge — panic, exit, or loop forever). It is used to encode logical impossibility:

```rust
fn unreachable_branch(x: u32) -> String {
    match x % 3 {
        0 => "fizz".to_string(),
        1 => "one".to_string(),
        2 => "two".to_string(),
        _ => unreachable!("x % 3 is always 0, 1, or 2"),
    }
}
```

`unreachable!()` has type `!`, which is a subtype of everything — so it satisfies the match arm type. If the branch IS reached at runtime, it panics loudly rather than silently producing wrong output.

### 5.5 Option<T> — Absence as a Type

`Option<T>` is just an enum:
```rust
enum Option<T> {
    Some(T),
    None,
}
```

**Key insight**: the type system forces you to handle the `None` case before you can use the `Some` value. This is different from nullable references in other languages where you can forget to check.

```rust
// The compiler won't let you use the value without handling None:
fn get_username(id: u64) -> Option<String> { /* ... */ }

let name = get_username(42);
// println!("{}", name);  // COMPILE ERROR: can't print Option directly

// You must handle both cases:
match name {
    Some(n) => println!("Hello, {}", n),
    None => println!("User not found"),
}

// Or use combinators that are safe:
let upper = name.map(|n| n.to_uppercase());
let length = name.as_deref().map(str::len).unwrap_or(0);
```

### 5.6 Result<T, E> — Failure as a Type

`Result<T, E>` is similarly an enum:
```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Unlike exceptions in other languages, errors in Rust are **values**. They are part of the function signature. You cannot accidentally ignore an error:

```rust
fn read_config(path: &str) -> Result<Config, ConfigError> { /* ... */ }

// If you ignore the result entirely, rustc warns:
// warning: unused `Result` that must be used
let _ = read_config("config.toml");  // suppresses warning but still explicit

// Correct: handle the error
match read_config("config.toml") {
    Ok(config) => use_config(config),
    Err(e) => eprintln!("Failed to load config: {}", e),
}
```

---

## 6. The Typestate Pattern

This is arguably the most powerful pattern for encoding **protocol correctness** at compile time. It ensures operations happen in the correct order.

### 6.1 The Problem

Many systems have operations that must occur in a specific sequence:
- You must `connect()` before `send()`
- You must `authenticate()` before `query()`
- You must `lock()` before `read_protected_data()`
- A builder must have all required fields set before `build()`

Without typestate, these constraints exist only in documentation. Calling them in the wrong order compiles fine.

### 6.2 The Solution: Types Encode State

The core idea: **use different types for different states**, and only implement methods on the correct types.

```rust
// State types — these are zero-sized (no runtime cost!)
struct Unconnected;
struct Connected;
struct Authenticated;

// The connection struct is generic over its state
struct DbConnection<State> {
    host: String,
    port: u16,
    // _state is a phantom field — holds no data at runtime
    _state: std::marker::PhantomData<State>,
}

// You can only call connect() on an Unconnected connection
impl DbConnection<Unconnected> {
    pub fn new(host: String, port: u16) -> Self {
        DbConnection {
            host,
            port,
            _state: std::marker::PhantomData,
        }
    }

    pub fn connect(self) -> Result<DbConnection<Connected>, ConnectionError> {
        // perform actual connection...
        Ok(DbConnection {
            host: self.host,
            port: self.port,
            _state: std::marker::PhantomData,
        })
    }
}

// You can only call authenticate() on a Connected connection
impl DbConnection<Connected> {
    pub fn authenticate(self, credentials: Credentials)
        -> Result<DbConnection<Authenticated>, AuthError>
    {
        // perform authentication...
        Ok(DbConnection {
            host: self.host,
            port: self.port,
            _state: std::marker::PhantomData,
        })
    }
}

// You can only call query() on an Authenticated connection
impl DbConnection<Authenticated> {
    pub fn query(&self, sql: &str) -> Result<Rows, QueryError> {
        // perform query...
        todo!()
    }
}
```

Now try to use the API incorrectly:

```rust
let conn = DbConnection::new("localhost".into(), 5432);
conn.query("SELECT 1");  // COMPILE ERROR: method `query` not found for DbConnection<Unconnected>

let conn = conn.connect()?;
conn.query("SELECT 1");  // COMPILE ERROR: method `query` not found for DbConnection<Connected>

let conn = conn.authenticate(creds)?;
conn.query("SELECT 1");  // OK — this compiles and works
```

The entire protocol is enforced at **compile time**, with zero runtime overhead.

### 6.3 ASCII Diagram: Typestate Transitions

```
                ┌──────────────────────────────────────────────────────┐
                │              TYPE-LEVEL STATE MACHINE                │
                └──────────────────────────────────────────────────────┘

  DbConnection<Unconnected>
         │
         │  .connect() → consumes self, returns new type
         │
         ▼
  DbConnection<Connected>
         │
         │  .authenticate(creds) → consumes self, returns new type
         │
         ▼
  DbConnection<Authenticated>
         │
         │  .query()      ← ONLY available here
         │  .execute()    ← ONLY available here
         │  .transaction() ← ONLY available here
         │
         ▼
      (result)

  ┌──────────────────────────────────────────────────────────────────┐
  │ KEY INSIGHT: Each transition CONSUMES the old state.             │
  │ You cannot hold onto DbConnection<Unconnected> after connecting. │
  │ The borrow checker enforces this automatically.                  │
  └──────────────────────────────────────────────────────────────────┘
```

### 6.4 Real-World Example: Email Sending

```rust
use std::marker::PhantomData;

struct Draft;
struct ReadyToSend;
struct Sent;

struct Email<State> {
    to: Vec<String>,
    subject: Option<String>,
    body: Option<String>,
    _state: PhantomData<State>,
}

impl Email<Draft> {
    pub fn new() -> Self {
        Email {
            to: vec![],
            subject: None,
            body: None,
            _state: PhantomData,
        }
    }

    pub fn add_recipient(mut self, email: String) -> Self {
        self.to.push(email);
        self
    }

    pub fn set_subject(mut self, subject: String) -> Self {
        self.subject = Some(subject);
        self
    }

    pub fn set_body(mut self, body: String) -> Self {
        self.body = Some(body);
        self
    }

    // Can only finalize if all required fields are set
    pub fn finalize(self) -> Result<Email<ReadyToSend>, DraftError> {
        if self.to.is_empty() {
            return Err(DraftError::NoRecipients);
        }
        if self.subject.is_none() {
            return Err(DraftError::NoSubject);
        }
        if self.body.is_none() {
            return Err(DraftError::NoBody);
        }
        Ok(Email {
            to: self.to,
            subject: self.subject,
            body: self.body,
            _state: PhantomData,
        })
    }
}

impl Email<ReadyToSend> {
    pub fn send(self, mailer: &Mailer) -> Result<Email<Sent>, SendError> {
        mailer.send(
            &self.to,
            self.subject.as_deref().unwrap(),  // safe: validated in finalize()
            self.body.as_deref().unwrap(),     // safe: validated in finalize()
        )?;
        Ok(Email {
            to: self.to,
            subject: self.subject,
            body: self.body,
            _state: PhantomData,
        })
    }
}

impl Email<Sent> {
    pub fn tracking_id(&self) -> String {
        // Only a sent email has a tracking ID
        todo!()
    }
}
```

---

## 7. Phantom Types

Phantom types are types that appear in the type signature but carry no data at runtime. They are `PhantomData<T>` at the field level.

### 7.1 Why Phantom Types?

They allow you to add **type-level information** (tags, units, permissions, state) to a struct without any runtime cost.

### 7.2 Units of Measure

This is the classic use case — preventing unit confusion bugs:

```rust
use std::marker::PhantomData;

// Unit marker types — zero-sized, no runtime cost
struct Meters;
struct Feet;
struct Kilograms;
struct Pounds;

// A distance that knows its unit at the type level
struct Distance<Unit> {
    value: f64,
    _unit: PhantomData<Unit>,
}

impl<Unit> Distance<Unit> {
    fn value(&self) -> f64 {
        self.value
    }
}

impl Distance<Meters> {
    fn new_meters(value: f64) -> Self {
        Distance { value, _unit: PhantomData }
    }

    fn to_feet(self) -> Distance<Feet> {
        Distance { value: self.value * 3.28084, _unit: PhantomData }
    }
}

impl Distance<Feet> {
    fn new_feet(value: f64) -> Self {
        Distance { value, _unit: PhantomData }
    }
}

// This function only accepts meters — compile-time enforced!
fn calculate_area_sq_meters(
    length: Distance<Meters>,
    width: Distance<Meters>
) -> f64 {
    length.value() * width.value()
}

fn main() {
    let length = Distance::new_meters(10.0);
    let width_in_feet = Distance::new_feet(30.0);

    // COMPILE ERROR: expected Distance<Meters>, found Distance<Feet>
    // calculate_area_sq_meters(length, width_in_feet);

    // Correct usage — must convert first:
    let width_in_meters = width_in_feet.to_feet(); // wait, this shows the api
    // Actually:
    let length = Distance::new_meters(10.0);
    let width = Distance::new_meters(5.0);
    let area = calculate_area_sq_meters(length, width); // OK
}
```

This is the Mars Climate Orbiter bug (metric vs. imperial units, $327M spacecraft lost) — prevented at compile time.

### 7.3 Capability / Permission Tokens

```rust
struct ReadOnly;
struct ReadWrite;

struct FileHandle<Permission> {
    fd: i32,
    _perm: PhantomData<Permission>,
}

impl<P> FileHandle<P> {
    pub fn read(&self, buf: &mut [u8]) -> usize {
        // reading is always allowed
        todo!()
    }
}

impl FileHandle<ReadWrite> {
    pub fn write(&mut self, data: &[u8]) -> usize {
        // writing only allowed on ReadWrite handles — enforced at compile time
        todo!()
    }

    pub fn truncate(&mut self) {
        // also only on ReadWrite
        todo!()
    }
}

fn open_readonly(path: &str) -> FileHandle<ReadOnly> { todo!() }
fn open_readwrite(path: &str) -> FileHandle<ReadWrite> { todo!() }

fn process(handle: FileHandle<ReadOnly>) {
    // handle.write(b"data");  // COMPILE ERROR — no write() on ReadOnly
    let mut buf = [0u8; 1024];
    handle.read(&mut buf);  // OK
}
```

### 7.4 Validated vs. Unvalidated Data

```rust
struct Unvalidated;
struct Validated;

struct EmailAddress<State> {
    raw: String,
    _state: PhantomData<State>,
}

impl EmailAddress<Unvalidated> {
    pub fn new(raw: String) -> Self {
        EmailAddress { raw, _state: PhantomData }
    }

    pub fn validate(self) -> Result<EmailAddress<Validated>, ValidationError> {
        if self.raw.contains('@') && self.raw.contains('.') {
            Ok(EmailAddress { raw: self.raw, _state: PhantomData })
        } else {
            Err(ValidationError::InvalidFormat)
        }
    }
}

impl EmailAddress<Validated> {
    pub fn as_str(&self) -> &str {
        &self.raw
    }
}

// This function only accepts validated emails — impossible to pass unvalidated
fn send_email(to: EmailAddress<Validated>, body: &str) {
    println!("Sending to {}: {}", to.as_str(), body);
}
```

---

## 8. Newtype Pattern

The newtype pattern wraps a primitive in a struct to give it a distinct type. This is one of the simplest and most effective ways to prevent logic bugs.

### 8.1 The Problem with Primitives

Primitives like `u64`, `String`, `f64` are too generic. When multiple domain concepts are represented as the same primitive, the type system cannot distinguish them.

```rust
// BAD: user_id and product_id are both u64
fn get_order(user_id: u64, product_id: u64) -> Order { todo!() }

// This compiles but is logically wrong — args are swapped!
let order = get_order(product_id, user_id);
```

### 8.2 Newtype Solution

```rust
// Create distinct types for each concept
struct UserId(u64);
struct ProductId(u64);
struct OrderId(u64);

fn get_order(user_id: UserId, product_id: ProductId) -> Order { todo!() }

let uid = UserId(42);
let pid = ProductId(17);

// This now COMPILE ERRORS — types don't match:
// let order = get_order(pid, uid);  // ERROR: expected UserId, found ProductId

// Only the correct order compiles:
let order = get_order(uid, pid);  // OK
```

### 8.3 Newtype with Validation

The newtype pattern shines when combined with validation at construction:

```rust
#[derive(Debug, Clone)]
pub struct Port(u16);

impl Port {
    pub fn new(value: u16) -> Result<Self, PortError> {
        if value == 0 {
            return Err(PortError::ReservedZero);
        }
        Ok(Port(value))
    }

    // Specific known-valid ports
    pub fn http() -> Self { Port(80) }
    pub fn https() -> Self { Port(443) }

    pub fn value(&self) -> u16 {
        self.0
    }
}

// Once you have a Port, you know it's valid — no need to re-validate
fn connect(host: &str, port: Port) {
    println!("Connecting to {}:{}", host, port.value());
}
```

### 8.4 Non-Empty Collections

A very common logic bug: treating a potentially-empty collection as if it has at least one element.

```rust
use std::fmt;

#[derive(Debug, Clone)]
pub struct NonEmptyVec<T> {
    head: T,
    tail: Vec<T>,
}

impl<T> NonEmptyVec<T> {
    pub fn new(first: T) -> Self {
        NonEmptyVec { head: first, tail: vec![] }
    }

    pub fn from_vec(v: Vec<T>) -> Option<Self> {
        let mut iter = v.into_iter();
        Some(NonEmptyVec {
            head: iter.next()?,
            tail: iter.collect(),
        })
    }

    // This is ALWAYS safe — no panicking unwrap needed
    pub fn first(&self) -> &T {
        &self.head
    }

    pub fn last(&self) -> &T {
        self.tail.last().unwrap_or(&self.head)
    }

    pub fn len(&self) -> usize {
        1 + self.tail.len()
    }
}

// This function signature guarantees non-empty input at the type level
fn process_items(items: NonEmptyVec<Item>) {
    let first = items.first(); // no panicking unwrap()
    // ...
}
```

---

## 9. Parse, Don't Validate

This is a principle from Alexis King's famous essay that is deeply relevant to logic-correct Rust.

### 9.1 The Core Idea

**Validation** checks if data is valid and returns a boolean (or throws). The data remains in its original, unconstrained type.

**Parsing** checks if data is valid and, if so, **converts it to a richer type** that encodes the validity. After parsing, you can never access the raw data without going through the validated type.

```
VALIDATE:                          PARSE:
raw_string: String                 raw_string: String
    │                                  │
    ▼                                  ▼
is_valid_email(&raw_string)        parse_email(raw_string)
    │                                  │
    ▼                                  ▼
  true/false                       Ok(Email) or Err(...)
    │                                  │
raw_string is STILL a String       Email is a DISTINCT TYPE
(unconstrained, any code can use   (only valid email strings
 the raw string anywhere)           can be represented)
```

### 9.2 The Validation Anti-Pattern

```rust
// BAD: Validate-then-use — the validation and use are disconnected
fn send_welcome_email(email: &str) {
    // This check can be forgotten, removed, or bypassed
    if !is_valid_email(email) {
        return;
    }
    // At this point, we know email is valid, but the TYPE says nothing
    // Someone can call send_welcome_email with any string, bypassing intent
    actually_send_email(email);
}

fn register_user(email: &str) {
    // Someone forgot to validate here — logic bug!
    // They assumed it was already validated somewhere upstream
    actually_send_email(email);  // could be "not-an-email" at runtime
}
```

### 9.3 The Parse Pattern

```rust
// GOOD: Parse into a type that encodes validity
#[derive(Debug, Clone)]
pub struct ValidEmail(String);

impl ValidEmail {
    // The ONLY way to construct a ValidEmail
    pub fn parse(raw: String) -> Result<ValidEmail, EmailError> {
        // validation logic
        if !raw.contains('@') {
            return Err(EmailError::MissingAtSign);
        }
        let parts: Vec<&str> = raw.splitn(2, '@').collect();
        if parts[1].is_empty() || !parts[1].contains('.') {
            return Err(EmailError::InvalidDomain);
        }
        Ok(ValidEmail(raw))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

// Now functions that need valid emails say so in their signature
fn send_welcome_email(email: ValidEmail) {
    // No need to re-validate — the TYPE GUARANTEES it's valid
    actually_send_email(email.as_str());
}

fn register_user(raw_email: String) -> Result<User, RegistrationError> {
    // Parsing happens ONCE at the boundary
    let email = ValidEmail::parse(raw_email)?;
    // From here on, email is provably valid — no logic bugs possible
    send_welcome_email(email.clone());
    Ok(User { email })
}
```

### 9.4 Parse at the Boundary

The key architectural insight: **parse at the system boundary, not deep inside business logic**.

```
         SYSTEM BOUNDARY
              │
              ▼
┌─────────────────────────────────┐
│   RAW INPUT (String, JSON, etc) │
│   - Untrusted                   │
│   - Unvalidated                 │
│   - Unconstrained               │
└──────────────┬──────────────────┘
               │
               │  PARSE HERE (once)
               │
               ▼
┌─────────────────────────────────┐
│   DOMAIN TYPES                  │
│   - Validated                   │
│   - Constrained                 │
│   - Safe to use anywhere        │
└─────────────────────────────────┘
               │
               │  Business logic works with
               │  domain types — no re-validation
               ▼
          CORE LOGIC
```

---

## 10. Total Functions vs. Partial Functions

### 10.1 Definitions

A **total function** is defined for ALL possible inputs — it always produces a valid output.

A **partial function** is only defined for SOME inputs — for others, it panics, returns garbage, or has undefined behavior.

```
Total function:   every input → valid output
Partial function: some inputs → valid output
                  other inputs → panic / undefined / wrong answer
```

### 10.2 Partial Functions Are Logic Bug Sources

```rust
// PARTIAL FUNCTION: panics if the slice is empty
fn first_element(items: &[i32]) -> i32 {
    items[0]  // panics on empty slice — logic bug waiting
}

// PARTIAL FUNCTION: panics if None
fn user_name(id: u64) -> String {
    get_user(id).unwrap()  // panics if user doesn't exist — logic bug
}
```

### 10.3 Making Functions Total

**Strategy 1: Expand the return type to handle failure**
```rust
fn first_element(items: &[i32]) -> Option<i32> {
    items.first().copied()
}
```

**Strategy 2: Restrict the input type so failure is impossible**
```rust
fn first_element(items: &NonEmptyVec<i32>) -> i32 {
    items.first()  // guaranteed: NonEmptyVec is always non-empty
}
```

**Strategy 3: Use a default**
```rust
fn first_element_or_default(items: &[i32], default: i32) -> i32 {
    items.first().copied().unwrap_or(default)
}
```

### 10.4 The `unwrap()` Problem

`unwrap()` is a partial function application — it turns a total type (`Option<T>`, `Result<T, E>`) back into a partial one by panicking on the bad case.

**Rule**: `unwrap()` is only safe when you have a **local proof** that the value is `Some`/`Ok`. If you cannot immediately justify it in a comment, it's a logic bug waiting to happen.

```rust
// BAD: unwrap without justification
let config = load_config().unwrap();

// OK: unwrap with local proof
let digits: Vec<char> = "12345".chars().collect();
// SAFE: we know digits is non-empty because the string literal is non-empty
let first_digit = digits.first().unwrap();

// BETTER: use expect() with a meaningful message
let config = load_config()
    .expect("config.toml must exist — copy from config.toml.example");
```

### 10.5 The `#[must_use]` Attribute

Use `#[must_use]` to force callers to handle return values:

```rust
#[must_use]
fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

// The compiler warns if you ignore a #[must_use] return value:
divide(10.0, 0.0);  // warning: unused return value of `divide` that must be used
```

`Result` is `#[must_use]` by default in Rust. This is why you get warnings for ignored `Result`s.

---

## 11. Invariants: The Core Concept

An **invariant** is a condition that must be true throughout the lifetime of a value. Logic bugs often occur when invariants are violated.

### 11.1 Types of Invariants

```
INVARIANTS
├── Structural Invariants
│   └── "The left child of a BST node has a smaller value"
│   └── "A sorted Vec is always sorted"
│   └── "A HashMap's length equals the number of key-value pairs"
│
├── State Invariants
│   └── "A Connected socket has a valid file descriptor"
│   └── "An Authenticated session has a non-null token"
│
└── Business Invariants
    └── "Account balance is never negative"
    └── "Order total matches sum of line items"
    └── "User age is between 0 and 150"
```

### 11.2 Encoding Invariants with Private Fields

The pattern: **private fields + public constructor + invariant-preserving methods**.

```rust
pub mod sorted_vec {
    #[derive(Debug, Clone)]
    pub struct SortedVec<T: Ord> {
        // PRIVATE: external code cannot mutate this directly
        // Invariant: inner is always sorted
        inner: Vec<T>,
    }

    impl<T: Ord> SortedVec<T> {
        // Constructor: only way to create a SortedVec
        pub fn new() -> Self {
            SortedVec { inner: vec![] }
        }

        pub fn from_vec(mut v: Vec<T>) -> Self {
            v.sort();  // establish the invariant
            SortedVec { inner: v }
        }

        // Insert preserves the invariant
        pub fn insert(&mut self, value: T) {
            let pos = self.inner.partition_point(|x| x < &value);
            self.inner.insert(pos, value);
            // Invariant still holds: we inserted at the correct sorted position
        }

        // Binary search is always valid — we know it's sorted!
        pub fn contains(&self, value: &T) -> bool {
            self.inner.binary_search(value).is_ok()
        }

        // Read-only access: users can see the data but not corrupt the order
        pub fn as_slice(&self) -> &[T] {
            &self.inner
        }

        pub fn len(&self) -> usize {
            self.inner.len()
        }
    }
}
```

External code cannot construct a `SortedVec` with an unsorted inner vec. The invariant is **structurally enforced**.

### 11.3 Invariant Verification in Debug Builds

For complex invariants, write an `assert_invariants()` method and call it in debug mode:

```rust
impl<T: Ord> SortedVec<T> {
    #[cfg(debug_assertions)]
    fn assert_invariants(&self) {
        for window in self.inner.windows(2) {
            assert!(
                window[0] <= window[1],
                "SortedVec invariant violated: {:?} > {:?}",
                window[0], window[1]
            );
        }
    }

    pub fn insert(&mut self, value: T) {
        let pos = self.inner.partition_point(|x| x < &value);
        self.inner.insert(pos, value);

        #[cfg(debug_assertions)]
        self.assert_invariants();  // catch bugs during development
    }
}
```

### 11.4 The `debug_assert!` Macro

`debug_assert!` is evaluated only in debug builds (compiled away in release builds — zero cost in production):

```rust
fn binary_search<T: Ord>(sorted: &[T], target: &T) -> Option<usize> {
    // Check that our assumption (sorted input) holds — only in debug
    debug_assert!(
        sorted.windows(2).all(|w| w[0] <= w[1]),
        "binary_search requires sorted input"
    );

    let mut low = 0;
    let mut high = sorted.len();

    while low < high {
        let mid = low + (high - low) / 2;
        match sorted[mid].cmp(target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => low = mid + 1,
            std::cmp::Ordering::Greater => high = mid,
        }
    }
    None
}
```

---

## 12. Error Handling as Logic Correctness

How you handle errors is a major source of logic bugs. Rust's error handling model is designed to make correct behavior the path of least resistance.

### 12.1 The Error Handling Hierarchy

```
                   SEVERITY / RECOVERABILITY
      ────────────────────────────────────────────►
      │
      │   panic!()           — programming error, bug in code
      │                        (invariant violation, wrong index)
      │
      │   Result<T, E>       — expected failure, caller must handle
      │   with rich errors     (network error, parse failure, not found)
      │
      │   Option<T>          — absence of a value, not an error
      ▼                        (user not found, key missing in map)
```

**Rule of thumb**:
- `panic!` for bugs (things that should never happen — if they do, it's a programming error)
- `Result` for expected failures (I/O, user input, network)
- `Option` for optional values

### 12.2 Designing Error Types

```rust
// BAD: stringly-typed errors — impossible to handle programmatically
fn parse_config(s: &str) -> Result<Config, String> {
    Err("missing field 'host'".to_string())
    // Callers can't distinguish error types — forced to parse the string!
}

// GOOD: structured error types
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("missing required field: {field}")]
    MissingField { field: String },

    #[error("invalid value for field '{field}': {reason}")]
    InvalidValue { field: String, reason: String },

    #[error("failed to read config file: {0}")]
    Io(#[from] std::io::Error),
}

fn parse_config(s: &str) -> Result<Config, ConfigError> {
    Err(ConfigError::MissingField { field: "host".to_string() })
}

// Now callers can handle errors programmatically:
match parse_config(input) {
    Ok(config) => use_config(config),
    Err(ConfigError::MissingField { field }) => {
        eprintln!("Please add '{}' to your config", field);
    }
    Err(ConfigError::Io(e)) => {
        eprintln!("Could not read config file: {}", e);
    }
    Err(e) => {
        eprintln!("Config error: {}", e);
    }
}
```

### 12.3 The `?` Operator and Error Propagation

The `?` operator propagates errors up the call stack. It is equivalent to:
```rust
let value = some_result?;
// is equivalent to:
let value = match some_result {
    Ok(v) => v,
    Err(e) => return Err(e.into()),
};
```

**Logic bug prevention**: `?` makes error paths explicit and non-optional. You cannot accidentally ignore an error when using `?`.

```rust
fn load_user_config(user_id: UserId) -> Result<UserConfig, AppError> {
    let path = config_path_for_user(user_id)?;  // propagates PathError
    let contents = std::fs::read_to_string(&path)?;  // propagates io::Error
    let config: UserConfig = serde_json::from_str(&contents)?;  // propagates JsonError
    Ok(config)
}
```

Each `?` is a place where a failure is explicitly acknowledged and propagated. There are no "swallowed" errors.

### 12.4 Never Swallow Errors

```rust
// BAD: swallowed error — the failure is silently ignored
fn save_data(data: &Data) {
    let _ = write_to_disk(data);  // if this fails, we don't know
}

// GOOD: log at minimum, propagate when possible
fn save_data(data: &Data) -> Result<(), SaveError> {
    write_to_disk(data).map_err(|e| {
        log::error!("Failed to save data: {}", e);
        e
    })?;
    Ok(())
}
```

### 12.5 `Option` Combinators for Logic Clarity

Instead of nested `match`/`if let`, use combinators that make the logic linear and explicit:

```rust
// MESSY: nested matches
fn get_user_city(db: &Db, user_id: u64) -> Option<String> {
    match db.get_user(user_id) {
        Some(user) => match user.address {
            Some(addr) => Some(addr.city),
            None => None,
        },
        None => None,
    }
}

// CLEAN: chained combinators
fn get_user_city(db: &Db, user_id: u64) -> Option<String> {
    db.get_user(user_id)
        .and_then(|user| user.address)
        .map(|addr| addr.city)
}

// ALSO CLEAN: using ?
fn get_user_city(db: &Db, user_id: u64) -> Option<String> {
    let user = db.get_user(user_id)?;
    let addr = user.address?;
    Some(addr.city)
}
```

---

## 13. Traits as Logical Contracts

Traits in Rust encode **behavioral contracts**. Implementing a trait is a promise that your type behaves in a specific, specified way.

### 13.1 Trait Bounds as Preconditions

Trait bounds on function parameters express preconditions:

```rust
// This function works on anything that can be compared for ordering
// The Ord bound is a LOGICAL PRECONDITION: "input must be sortable"
fn find_max<T: Ord>(items: &[T]) -> Option<&T> {
    items.iter().max()
}

// This function works on anything that can be displayed and debugged
// These bounds encode what operations the function needs
fn log_value<T: std::fmt::Display + std::fmt::Debug>(value: &T) {
    println!("Display: {}", value);
    println!("Debug: {:?}", value);
}
```

### 13.2 Marker Traits for Logic Tags

Marker traits (traits with no methods) encode logical properties of types:

```rust
// Mark types that are safe to store in a database
pub trait Persistable: serde::Serialize + serde::de::DeserializeOwned {}

// Mark types that represent validated domain objects
pub trait Validated {}

// Once an EmailAddress is validated, mark it
impl Validated for EmailAddress<Validated> {}

// Only accept validated, persistable objects
fn save_to_db<T: Persistable + Validated>(item: &T) {
    // We know at compile time that:
    // 1. T can be serialized/deserialized (Persistable)
    // 2. T has been validated (Validated)
    todo!()
}
```

### 13.3 Sealed Traits

Sealed traits prevent external code from implementing a trait, giving you control over which types can use an API:

```rust
// The seal — private module, not exported
mod sealed {
    pub trait Sealed {}
}

// DatabaseType is a public trait, but only types in this crate can implement it
// because Sealed is private
pub trait DatabaseType: sealed::Sealed {
    fn to_sql(&self) -> String;
}

// Only these implementations are allowed:
impl sealed::Sealed for String {}
impl DatabaseType for String {
    fn to_sql(&self) -> String {
        format!("'{}'", self.replace('\'', "''"))
    }
}

impl sealed::Sealed for i64 {}
impl DatabaseType for i64 {
    fn to_sql(&self) -> String {
        self.to_string()
    }
}

// External code CANNOT implement DatabaseType for their own types,
// preventing SQL injection through custom implementations
```

### 13.4 The `From`/`Into` Conversion Contracts

Use `From`/`Into` to encode valid conversions — they express that a conversion is **total** (always succeeds):

```rust
// From expresses: converting from Celsius to Fahrenheit always works
impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

// TryFrom expresses: converting might fail (partial conversion)
impl TryFrom<f64> for Port {
    type Error = PortError;

    fn try_from(value: f64) -> Result<Self, Self::Error> {
        if value < 0.0 || value > 65535.0 || value.fract() != 0.0 {
            Err(PortError::InvalidValue(value))
        } else {
            Ok(Port(value as u16))
        }
    }
}
```

---

## 14. State Machines in Rust

State machines are one of the best tools for eliminating logic bugs in systems with complex sequential behavior. Rust offers two main approaches.

### 14.1 Typestate State Machine (Compile-Time)

Covered in section 6. Best when: the state space is small, transitions are known at compile time, and you want zero-cost abstractions.

### 14.2 Enum-Based State Machine (Runtime)

When states and transitions are dynamic (determined at runtime), use enums:

```rust
#[derive(Debug, Clone, PartialEq)]
enum OrderState {
    Draft,
    Submitted { submitted_at: chrono::DateTime<chrono::Utc> },
    Processing { assigned_to: WorkerId },
    Shipped { tracking_number: String, carrier: Carrier },
    Delivered { delivered_at: chrono::DateTime<chrono::Utc> },
    Cancelled { reason: CancellationReason },
}

struct Order {
    id: OrderId,
    items: NonEmptyVec<OrderItem>,
    state: OrderState,
}

impl Order {
    // Only valid transitions are implemented — invalid transitions
    // are compile errors or return Result::Err
    pub fn submit(&mut self) -> Result<(), OrderError> {
        match &self.state {
            OrderState::Draft => {
                self.state = OrderState::Submitted {
                    submitted_at: chrono::Utc::now()
                };
                Ok(())
            }
            other => Err(OrderError::InvalidTransition {
                from: format!("{:?}", other),
                to: "Submitted".to_string(),
            }),
        }
    }

    pub fn assign_to_worker(&mut self, worker: WorkerId) -> Result<(), OrderError> {
        match &self.state {
            OrderState::Submitted { .. } => {
                self.state = OrderState::Processing { assigned_to: worker };
                Ok(())
            }
            other => Err(OrderError::InvalidTransition {
                from: format!("{:?}", other),
                to: "Processing".to_string(),
            }),
        }
    }

    pub fn ship(&mut self, tracking: String, carrier: Carrier) -> Result<(), OrderError> {
        match &self.state {
            OrderState::Processing { .. } => {
                self.state = OrderState::Shipped {
                    tracking_number: tracking,
                    carrier,
                };
                Ok(())
            }
            other => Err(OrderError::InvalidTransition {
                from: format!("{:?}", other),
                to: "Shipped".to_string(),
            }),
        }
    }
}
```

### 14.3 ASCII Diagram: State Machine for Order

```
                    ┌──────────────────────────────────┐
                    │         ORDER STATE MACHINE       │
                    └──────────────────────────────────┘

         ┌─────────┐
         │  Draft  │
         └────┬────┘
              │ submit()
              ▼
         ┌──────────┐
         │Submitted │◄──────────────────────────┐
         └────┬─────┘                           │
              │ assign_to_worker()              │ (no going back — only forward
              ▼                                 │  or to Cancelled)
         ┌────────────┐
         │ Processing │
         └─────┬──────┘
               │ ship()
               ▼
         ┌─────────┐
         │ Shipped │
         └────┬────┘
              │ confirm_delivery()
              ▼
         ┌───────────┐
         │ Delivered │  ◄── terminal state
         └───────────┘

  From Draft, Submitted, Processing, or Shipped:
         │ cancel()
         ▼
    ┌──────────┐
    │Cancelled │  ◄── terminal state
    └──────────┘

  INVALID TRANSITIONS (enforced by returning Err):
  - Delivered → anything
  - Cancelled → anything
  - Draft → Shipped (skipping steps)
```

### 14.4 The State Machine Transition Table

It's good practice to document the full transition table:

```rust
// Transition table:
// ┌──────────────┬──────────────────┬────────────────┐
// │ FROM         │ EVENT            │ TO             │
// ├──────────────┼──────────────────┼────────────────┤
// │ Draft        │ submit()         │ Submitted      │
// │ Submitted    │ assign()         │ Processing     │
// │ Processing   │ ship()           │ Shipped        │
// │ Shipped      │ deliver()        │ Delivered      │
// │ Any (except  │ cancel()         │ Cancelled      │
// │  terminal)   │                  │                │
// └──────────────┴──────────────────┴────────────────┘
```

---

## 15. Domain Modeling for Correctness

Domain modeling is the practice of designing your types to **mirror the real-world domain** as closely and accurately as possible. When your types match your domain, logic bugs become structurally impossible.

### 15.1 The Anemic Model (Anti-Pattern)

```rust
// BAD: Anemic model — data without logic, primitives everywhere
struct User {
    id: u64,
    email: String,          // is it valid? is it verified?
    age: u32,               // is it a valid age? in years? months?
    role: String,           // "admin"? "user"? any string?
    balance: f64,           // can it be negative? what currency?
}
```

### 15.2 The Rich Domain Model (Correct Pattern)

```rust
// GOOD: Rich model — types encode domain rules

#[derive(Debug, Clone)]
pub struct UserId(u64);

#[derive(Debug, Clone)]
pub struct VerifiedEmail(String);

#[derive(Debug, Clone)]
pub struct Age(u8);  // u8 naturally caps at 255, sufficient for age

impl Age {
    pub fn new(years: u8) -> Result<Self, AgeError> {
        if years > 150 {
            return Err(AgeError::Unrealistic(years));
        }
        Ok(Age(years))
    }
}

#[derive(Debug, Clone, Copy)]
pub enum UserRole {
    Guest,
    Member,
    Admin,
    SuperAdmin,
}

impl UserRole {
    pub fn can_delete_users(&self) -> bool {
        matches!(self, UserRole::Admin | UserRole::SuperAdmin)
    }

    pub fn can_access_admin_panel(&self) -> bool {
        matches!(self, UserRole::Admin | UserRole::SuperAdmin)
    }
}

#[derive(Debug, Clone, Copy)]
pub struct Usd(i64);  // in cents — never use float for money!

impl Usd {
    pub fn from_cents(cents: i64) -> Self { Usd(cents) }
    pub fn cents(&self) -> i64 { self.0 }

    pub fn checked_add(self, other: Usd) -> Option<Usd> {
        self.0.checked_add(other.0).map(Usd)
    }

    pub fn is_negative(&self) -> bool { self.0 < 0 }
}

// The user struct — much harder to misuse
pub struct User {
    id: UserId,
    email: VerifiedEmail,  // ONLY verified emails stored here
    age: Age,
    role: UserRole,
    balance: Usd,          // in cents, no float confusion
}
```

### 15.3 Money: Never Use Float

This deserves special emphasis. Floating-point numbers have precision errors:

```
0.1 + 0.2 = 0.30000000000000004  (in floating point)
```

For monetary calculations, always use integer cents (or the smallest currency unit):

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Cents(i64);

impl Cents {
    pub fn from_dollars_and_cents(dollars: i64, cents: i64) -> Result<Self, MoneyError> {
        if cents < 0 || cents >= 100 {
            return Err(MoneyError::InvalidCents(cents));
        }
        Ok(Cents(dollars * 100 + cents))
    }

    pub fn dollars(&self) -> i64 { self.0 / 100 }
    pub fn cents_part(&self) -> i64 { self.0 % 100 }

    pub fn checked_add(self, other: Cents) -> Option<Cents> {
        self.0.checked_add(other.0).map(Cents)
    }
}

impl std::fmt::Display for Cents {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "${}.{:02}", self.dollars(), self.cents_part().abs())
    }
}
```

### 15.4 Integer Overflow as a Logic Bug

Rust integers do not overflow silently in debug builds (they panic). In release builds, they wrap. Neither is "correct" for most business logic. Use checked arithmetic:

```rust
fn charge_account(balance: Cents, charge: Cents) -> Result<Cents, ChargeError> {
    // checked_sub returns None on underflow — prevents negative balance silently
    balance.0.checked_sub(charge.0)
        .map(Cents)
        .ok_or_else(|| ChargeError::InsufficientFunds {
            balance,
            charge,
        })
}

// In hot paths where you've already bounds-checked, you can use:
// saturating_add — saturates at max/min instead of overflowing
// wrapping_add — explicit wrap (e.g., for hashing)
// checked_add — returns Option
```

---

## 16. Builder Pattern for Invariant Construction

When constructing complex objects with multiple required fields and inter-field invariants, the builder pattern ensures all invariants hold before the object is created.

### 16.1 The Standard Builder

```rust
#[derive(Debug)]
pub struct ServerConfig {
    host: String,
    port: Port,
    max_connections: usize,
    tls: Option<TlsConfig>,
    timeout_seconds: u64,
}

#[derive(Debug, Default)]
pub struct ServerConfigBuilder {
    host: Option<String>,
    port: Option<Port>,
    max_connections: Option<usize>,
    tls: Option<TlsConfig>,
    timeout_seconds: Option<u64>,
}

#[derive(Debug)]
pub enum BuildError {
    MissingHost,
    MissingPort,
    InvalidMaxConnections,
    TlsRequiredOnPort443,
}

impl ServerConfigBuilder {
    pub fn new() -> Self { Self::default() }

    pub fn host(mut self, host: String) -> Self {
        self.host = Some(host);
        self
    }

    pub fn port(mut self, port: Port) -> Self {
        self.port = Some(port);
        self
    }

    pub fn max_connections(mut self, max: usize) -> Self {
        self.max_connections = Some(max);
        self
    }

    pub fn tls(mut self, tls: TlsConfig) -> Self {
        self.tls = Some(tls);
        self
    }

    pub fn timeout_seconds(mut self, seconds: u64) -> Self {
        self.timeout_seconds = Some(seconds);
        self
    }

    pub fn build(self) -> Result<ServerConfig, BuildError> {
        let host = self.host.ok_or(BuildError::MissingHost)?;
        let port = self.port.ok_or(BuildError::MissingPort)?;

        // Cross-field invariant: port 443 requires TLS
        if port.value() == 443 && self.tls.is_none() {
            return Err(BuildError::TlsRequiredOnPort443);
        }

        let max_connections = self.max_connections.unwrap_or(100);
        let timeout_seconds = self.timeout_seconds.unwrap_or(30);

        Ok(ServerConfig {
            host,
            port,
            max_connections,
            tls: self.tls,
            timeout_seconds,
        })
    }
}

// Usage — reads like a sentence, invariants enforced at build()
let config = ServerConfigBuilder::new()
    .host("localhost".to_string())
    .port(Port::https())
    .tls(tls_config)
    .max_connections(50)
    .build()?;
```

### 16.2 Typestate Builder (Required Fields at Compile Time)

For required fields, you can use typestate to enforce them at compile time rather than runtime:

```rust
use std::marker::PhantomData;

struct Missing;
struct Present<T>(T);

struct RequestBuilder<HostState, PathState> {
    host: HostState,
    path: PathState,
    headers: Vec<(String, String)>,
}

impl RequestBuilder<Missing, Missing> {
    pub fn new() -> Self {
        RequestBuilder {
            host: Missing,
            path: Missing,
            headers: vec![],
        }
    }
}

impl<P> RequestBuilder<Missing, P> {
    pub fn host(self, host: String) -> RequestBuilder<Present<String>, P> {
        RequestBuilder {
            host: Present(host),
            path: self.path,
            headers: self.headers,
        }
    }
}

impl<H> RequestBuilder<H, Missing> {
    pub fn path(self, path: String) -> RequestBuilder<H, Present<String>> {
        RequestBuilder {
            host: self.host,
            path: Present(path),
            headers: self.headers,
        }
    }
}

// build() is ONLY available when BOTH host and path are Present
impl RequestBuilder<Present<String>, Present<String>> {
    pub fn add_header(mut self, key: String, value: String) -> Self {
        self.headers.push((key, value));
        self
    }

    pub fn build(self) -> Request {
        Request {
            host: self.host.0,
            path: self.path.0,
            headers: self.headers,
        }
    }
}

// This compiles:
let req = RequestBuilder::new()
    .host("example.com".into())
    .path("/api/v1".into())
    .build();

// This DOES NOT compile — missing path:
// let req = RequestBuilder::new()
//     .host("example.com".into())
//     .build();  // ERROR: build() not found for RequestBuilder<Present<String>, Missing>
```

---

## 17. Assertions, Contracts, and Defensive Programming

Even when types cannot encode all invariants, you can enforce them with runtime checks.

### 17.1 `assert!` vs `debug_assert!`

```rust
// assert!: always runs — use for invariants that MUST hold in production
fn withdraw(balance: &mut Cents, amount: Cents) {
    assert!(amount.0 >= 0, "Cannot withdraw a negative amount: {:?}", amount);
    assert!(balance.0 >= amount.0, "Insufficient funds");
    balance.0 -= amount.0;
}

// debug_assert!: only runs in debug builds
// Use for expensive checks or for verifying assumptions in hot paths
fn binary_search<T: Ord>(data: &[T], target: &T) -> Option<usize> {
    debug_assert!(
        data.windows(2).all(|w| w[0] <= w[1]),
        "binary_search requires sorted input"
    );
    // ... search implementation
    todo!()
}
```

### 17.2 Preconditions, Postconditions, and Invariants

Document and enforce these three types of contracts:

```rust
/// Calculates the average of a non-empty slice.
///
/// # Preconditions
/// - `data` must be non-empty
///
/// # Postconditions  
/// - Result is within [min(data), max(data)]
/// - Result is finite (not NaN or infinity)
fn average(data: &[f64]) -> f64 {
    // Precondition check
    assert!(!data.is_empty(), "average() requires non-empty input");

    let sum: f64 = data.iter().sum();
    let result = sum / data.len() as f64;

    // Postcondition check (in debug mode — this is expensive)
    debug_assert!(result.is_finite(), "average produced non-finite result");
    debug_assert!(
        result >= *data.iter().cloned().reduce(f64::min).unwrap(),
        "average below minimum"
    );

    result
}
```

### 17.3 The `invariant` Crate (or DIY)

You can build a simple invariant-checking macro:

```rust
macro_rules! invariant {
    ($condition:expr, $($arg:tt)*) => {
        if !$condition {
            panic!("Invariant violated: {}", format!($($arg)*));
        }
    };
}

// Usage:
invariant!(
    self.items.len() == self.count,
    "item count mismatch: {} items but count is {}",
    self.items.len(), self.count
);
```

### 17.4 Panicking vs. Returning Errors

Know when to panic and when to return errors:

```
PANIC when:                         RETURN Err WHEN:
- Invariant violated                - External failure (I/O, network)
  (bug in your code)                - User input is invalid
- Unreachable code is reached       - Resource not found
- Precondition not met              - Permission denied
  (caller's bug)                    - Rate limited / quota exceeded
- Index out of bounds in            - Recoverable runtime conditions
  internal data structure
```

```rust
// Panicking is appropriate here — it's a programming error
fn get_node(&self, idx: usize) -> &Node {
    assert!(idx < self.nodes.len(), "Node index {} out of bounds", idx);
    &self.nodes[idx]
}

// Returning Err is appropriate here — it's user input
fn parse_user_age(input: &str) -> Result<Age, ParseError> {
    let n: u8 = input.parse().map_err(|_| ParseError::NotANumber)?;
    Age::new(n).map_err(ParseError::InvalidAge)
}
```

---

## 18. Property-Based Testing

Unit tests check specific cases. Property-based tests check **universal properties** across thousands of randomly generated inputs. This is one of the most effective ways to find logic bugs that your manual test cases missed.

### 18.1 What Is a Property?

A **property** is a rule that must hold for ALL valid inputs. Examples:
- "Sorting a list and then reversing it gives the same result as sorting in reverse"
- "Encoding then decoding gives back the original value"
- "Adding an element to a SortedVec keeps it sorted"
- "Withdrawing more than the balance always fails"

### 18.2 `proptest` — The Primary Tool

Add to `Cargo.toml`:
```toml
[dev-dependencies]
proptest = "1"
```

```rust
use proptest::prelude::*;

// The function under test
fn reverse_and_sort(mut v: Vec<i32>) -> Vec<i32> {
    v.sort();
    v.reverse();
    v
}

proptest! {
    #[test]
    fn test_reverse_sort_length_preserved(v: Vec<i32>) {
        // Property 1: length doesn't change
        let result = reverse_and_sort(v.clone());
        prop_assert_eq!(result.len(), v.len());
    }

    #[test]
    fn test_reverse_sort_is_descending(v: Vec<i32>) {
        // Property 2: result is always sorted descending
        let result = reverse_and_sort(v);
        for window in result.windows(2) {
            prop_assert!(window[0] >= window[1],
                "Not sorted descending: {} < {}", window[0], window[1]);
        }
    }

    #[test]
    fn test_idempotent(v: Vec<i32>) {
        // Property 3: applying twice gives same result
        let once = reverse_and_sort(v.clone());
        let twice = reverse_and_sort(once.clone());
        // Note: this property would FAIL, showing us the function is not idempotent
        // — which is a USEFUL discovery!
    }
}
```

### 18.3 Testing Invariants with proptest

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn sorted_vec_stays_sorted_after_insert(
        items in prop::collection::vec(0i32..1000, 0..50),
        new_item in 0i32..1000
    ) {
        let mut sv = SortedVec::from_vec(items);
        sv.insert(new_item);

        // Invariant: always sorted after insert
        let slice = sv.as_slice();
        for window in slice.windows(2) {
            prop_assert!(window[0] <= window[1],
                "Not sorted: {} > {}", window[0], window[1]);
        }
    }

    #[test]
    fn sorted_vec_contains_inserted_item(
        items in prop::collection::vec(0i32..1000, 0..50),
        new_item in 0i32..1000
    ) {
        let mut sv = SortedVec::from_vec(items);
        sv.insert(new_item);

        // Property: inserted item is always findable
        prop_assert!(sv.contains(&new_item));
    }
}
```

### 18.4 Round-Trip Properties

The most powerful property class: encode → decode → same value.

```rust
proptest! {
    #[test]
    fn json_roundtrip(user in arbitrary_user()) {
        let serialized = serde_json::to_string(&user).unwrap();
        let deserialized: User = serde_json::from_str(&serialized).unwrap();
        prop_assert_eq!(user, deserialized);
    }

    #[test]
    fn base64_roundtrip(data: Vec<u8>) {
        let encoded = base64::encode(&data);
        let decoded = base64::decode(&encoded).unwrap();
        prop_assert_eq!(data, decoded);
    }
}
```

### 18.5 Defining Custom Strategies (Generators)

```rust
use proptest::prelude::*;

// Generate valid Email addresses
fn valid_email_strategy() -> impl Strategy<Value = String> {
    // local part: 1-64 alphanumeric chars
    // domain: 1-63 alphanumeric chars + "." + 2-6 alpha chars
    (
        "[a-z][a-z0-9]{0,63}",
        "[a-z][a-z0-9]{0,62}",
        "[a-z]{2,6}"
    ).prop_map(|(local, domain, tld)| {
        format!("{}@{}.{}", local, domain, tld)
    })
}

proptest! {
    #[test]
    fn valid_email_always_parses(raw in valid_email_strategy()) {
        let result = ValidEmail::parse(raw);
        prop_assert!(result.is_ok(), "Valid email failed to parse: {:?}", result);
    }
}
```

---

## 19. Formal Verification Tools for Rust

These tools provide the strongest guarantees — they can mathematically prove properties about your code.

### 19.1 Prusti — Contract-Based Verification

Prusti is a static verifier for Rust from ETH Zurich. It uses the Viper verification infrastructure to prove that your contracts hold.

```rust
use prusti_contracts::*;

#[requires(n >= 0)]
#[ensures(result >= 0)]
#[ensures(result * result <= n)]
#[ensures((result + 1) * (result + 1) > n)]
fn integer_sqrt(n: i64) -> i64 {
    let mut i = 0;
    while (i + 1) * (i + 1) <= n {
        i += 1;
    }
    i
}
```

Prusti proves AT COMPILE TIME that:
1. The precondition (`n >= 0`) must be satisfied by callers
2. The postconditions (about the result being a valid floor square root) always hold

If the implementation has a bug, Prusti refuses to verify it.

### 19.2 Kani — Bounded Model Checking

Kani is developed by AWS. It uses bounded model checking to verify properties:

```rust
#[cfg(kani)]
mod verification {
    use super::*;

    #[kani::proof]
    fn verify_binary_search() {
        // Create a symbolic sorted array
        let arr: [i32; 4] = kani::any();
        kani::assume(arr[0] <= arr[1]);
        kani::assume(arr[1] <= arr[2]);
        kani::assume(arr[2] <= arr[3]);

        let target: i32 = kani::any();

        match binary_search(&arr, &target) {
            Some(idx) => {
                // PROVE: if we found it, it's actually there
                assert_eq!(arr[idx], target);
            }
            None => {
                // PROVE: if not found, it's actually absent
                assert!(!arr.contains(&target));
            }
        }
    }
}
```

Run with: `cargo kani`

### 19.3 MIRI — Undefined Behavior Detector

MIRI is an interpreter for Rust's mid-level IR. It detects:
- Undefined behavior (UB)
- Invalid memory access
- Logic bugs in unsafe code

```
cargo +nightly miri test
```

MIRI runs your tests under an interpreter that checks every operation for correctness. It catches subtle UB that even Rust's borrow checker misses in `unsafe` blocks.

### 19.4 Cargo Fuzz — Coverage-Guided Fuzzing

Fuzzing finds edge cases by generating random inputs and tracking code coverage:

```
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add my_fuzzer
```

```rust
// fuzz/fuzz_targets/my_fuzzer.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        // Fuzzer will explore all code paths through parse_config
        // If it panics, the fuzzer captures the input
        let _ = parse_config(s);
    }
});
```

---

## 20. Concurrency Logic Correctness

Rust's type system prevents data races (memory-level), but logic races are still possible. A **logic race** is when two concurrent operations produce a wrong result even without a data race.

### 20.1 Time-of-Check-Time-of-Use (TOCTOU)

```rust
// LOGIC BUG: TOCTOU
// Between checking and using, another thread can change the state
async fn transfer_funds(from: &Mutex<Account>, to: &Mutex<Account>, amount: Cents) {
    // Check
    let balance = from.lock().await.balance;  // lock released after this line!
    if balance >= amount {
        // ANOTHER TASK COULD WITHDRAW HERE — balance might be insufficient now
        // Use — might be incorrect!
        from.lock().await.balance -= amount;
        to.lock().await.balance += amount;
    }
}

// FIX: Hold the lock across the entire check-and-use
async fn transfer_funds_correct(from: &Mutex<Account>, to: &Mutex<Account>, amount: Cents) {
    let mut from_account = from.lock().await;  // hold the lock
    if from_account.balance >= amount {
        from_account.balance -= amount;
        drop(from_account);  // release before acquiring the next lock (deadlock prevention)
        to.lock().await.balance += amount;
    }
}
```

### 20.2 Deadlock Prevention

Deadlocks are logic bugs — the program enters a state where it can never progress.

**Rule**: Always acquire locks in a consistent global order.

```rust
// DEADLOCK RISK: Thread 1 locks A then B, Thread 2 locks B then A
fn transfer(a: &Mutex<Account>, b: &Mutex<Account>) {
    let _a = a.lock();
    let _b = b.lock();  // Thread 2 might hold B and be waiting for A → deadlock
}

// FIX: Order locks by a stable identifier (e.g., memory address)
fn transfer_safe(acc1: &Mutex<Account>, acc2: &Mutex<Account>) {
    let (first, second) = if (acc1 as *const _) < (acc2 as *const _) {
        (acc1, acc2)
    } else {
        (acc2, acc1)
    };
    let _first = first.lock();
    let _second = second.lock();
    // Both threads always lock in the same order → no deadlock
}
```

### 20.3 `Arc<Mutex<T>>` Logic Patterns

```rust
use std::sync::{Arc, Mutex};
use std::thread;

// Pattern: keep the lock scope minimal
fn increment_counter(counter: Arc<Mutex<u64>>, times: u64) {
    for _ in 0..times {
        // Lock is held only for the increment, not for the entire loop
        let mut c = counter.lock().unwrap();
        *c += 1;
        // Lock is released here (RAII drop)
    }
}

// Pattern: never call external functions while holding a lock
// (they might try to acquire the same lock → deadlock)
fn bad_pattern(data: Arc<Mutex<Vec<Item>>>, callback: impl Fn(Item)) {
    let items = data.lock().unwrap();
    for item in items.iter() {
        callback(item.clone());  // DANGEROUS: callback might lock `data` too
    }
}

fn good_pattern(data: Arc<Mutex<Vec<Item>>>, callback: impl Fn(Item)) {
    // Collect items with lock held, then call callback without lock
    let items: Vec<Item> = data.lock().unwrap().clone();
    for item in items {
        callback(item);  // Safe: lock is not held
    }
}
```

### 20.4 Channels for Message Passing

Channels are often safer than shared state for concurrency logic:

```rust
use std::sync::mpsc;
use std::thread;

enum WorkerMessage {
    Process(Data),
    Shutdown,
}

fn spawn_worker() -> mpsc::Sender<WorkerMessage> {
    let (tx, rx) = mpsc::channel::<WorkerMessage>();

    thread::spawn(move || {
        loop {
            match rx.recv() {
                Ok(WorkerMessage::Process(data)) => {
                    process_data(data);
                }
                Ok(WorkerMessage::Shutdown) | Err(_) => {
                    break;
                }
            }
        }
    });

    tx
}
```

With message passing:
- No shared mutable state → no TOCTOU
- Channel ordering is guaranteed → no reordering bugs
- The worker owns its data exclusively → no aliasing bugs

---

## 21. Algorithm Correctness Patterns

### 21.1 Loop Invariants

A **loop invariant** is a property that holds:
1. Before the loop starts (initialization)
2. After each iteration (maintenance)
3. When the loop ends (termination — the invariant + exit condition = what you want)

Document your loop invariants explicitly:

```rust
fn binary_search<T: Ord>(data: &[T], target: &T) -> Option<usize> {
    let mut low: usize = 0;
    let mut high: usize = data.len();

    // LOOP INVARIANT:
    // - If target is in data, it is in data[low..high]
    // - low <= high
    // - low <= data.len(), high <= data.len()

    while low < high {
        // Invariant holds here (established before loop, maintained each iteration)

        let mid = low + (high - low) / 2;  // avoids overflow vs (low+high)/2

        match data[mid].cmp(target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => {
                low = mid + 1;
                // Invariant maintained: target is still in data[low..high]
            }
            std::cmp::Ordering::Greater => {
                high = mid;
                // Invariant maintained: target is still in data[low..high]
            }
        }
        // Both branches reduce (high - low) → loop terminates
    }

    // low == high, invariant: if target exists, it's in data[low..high] = empty
    // Therefore: target is not in data
    None
}
```

### 21.2 Off-by-One Error Prevention

Off-by-one errors are the most common logic bug in algorithms. Use these patterns:

```
RULE: Use half-open intervals [low, high) consistently.
      Never mix open/closed intervals.

HALF-OPEN [low, high):
  - low is INCLUSIVE (first element in range)
  - high is EXCLUSIVE (one past the last element)
  - Length = high - low
  - Empty when low == high
  - Consistent with Rust slices: data[low..high]

CLOSED [low, high]:
  - Both inclusive
  - Length = high - low + 1
  - Empty when low > high
  - Inconsistent — requires +1/-1 adjustments
```

```rust
// Using half-open intervals consistently — clean and bug-free:
fn sum_range(data: &[i32], start: usize, end: usize) -> i32 {
    // Range is [start, end) — end is exclusive
    // This matches how Rust slices work
    data[start..end].iter().sum()
}

// If you must use closed intervals, be explicit:
fn sum_inclusive(data: &[i32], first: usize, last: usize) -> i32 {
    // Range is [first, last] — last is INCLUSIVE
    // Convert to half-open for the slice:
    data[first..=last].iter().sum()
}
```

### 21.3 Overflow-Safe Arithmetic

```rust
// DANGEROUS: can overflow in release builds
fn average_slow(a: usize, b: usize) -> usize {
    (a + b) / 2  // if a + b > usize::MAX, this overflows!
}

// SAFE: avoids overflow
fn average_safe(a: usize, b: usize) -> usize {
    a + (b - a) / 2  // assumes a <= b, still has issues if a > b
}

// ALSO SAFE and clearer:
fn average_also_safe(a: usize, b: usize) -> usize {
    a / 2 + b / 2 + (a % 2 + b % 2) / 2
}

// For the binary search mid calculation:
let mid = low + (high - low) / 2;  // SAFE — difference first, then divide
// NOT: (low + high) / 2          // DANGEROUS — sum can overflow
```

### 21.4 Recursion Correctness

Every recursive function needs:
1. A **base case** (termination)
2. **Progress** toward the base case on each call

```rust
fn factorial(n: u64) -> Option<u64> {
    match n {
        0 | 1 => Some(1),                        // BASE CASE
        _ => {
            factorial(n - 1)                      // PROGRESS: n - 1 < n
                .and_then(|f| f.checked_mul(n))   // checked: no overflow
        }
    }
}

// Better: use iteration for tail recursion (Rust doesn't guarantee TCO)
fn factorial_iterative(n: u64) -> Option<u64> {
    (1..=n).try_fold(1u64, |acc, x| acc.checked_mul(x))
}
```

---

## 22. Anti-Patterns That Introduce Logic Bugs

### 22.1 Boolean Blindness

Using `bool` where an enum would be clearer:

```rust
// BAD: what does true mean? What does false mean?
fn set_user_active(user: &mut User, active: bool) { ... }
set_user_active(&mut user, true);   // what is true? Active? Verified? Admin?

// GOOD: self-documenting
enum UserStatus { Active, Inactive, Banned }
fn set_user_status(user: &mut User, status: UserStatus) { ... }
set_user_status(&mut user, UserStatus::Active);
```

### 22.2 Stringly Typed Code

Using `String` for anything that has a constrained set of values:

```rust
// BAD: any string is accepted — "admine", "ADMIN", "superuser" all compile
fn set_role(user: &mut User, role: &str) {
    user.role = role.to_string();
}

// GOOD: only valid roles exist
enum Role { Admin, Moderator, User, Guest }
fn set_role(user: &mut User, role: Role) {
    user.role = role;
}
```

### 22.3 Magic Numbers

```rust
// BAD: what is 86400? what is 7?
fn session_expires_at(created: Instant) -> Instant {
    created + Duration::from_secs(86400 * 7)
}

// GOOD: named constants with clear types
const SECONDS_PER_DAY: u64 = 24 * 60 * 60;  // compiler computes this
const SESSION_DURATION_DAYS: u64 = 7;

fn session_expires_at(created: Instant) -> Instant {
    created + Duration::from_secs(SECONDS_PER_DAY * SESSION_DURATION_DAYS)
}
```

### 22.4 Flag Fields on Structs

```rust
// BAD: fields that are conditionally meaningful — classic source of logic bugs
struct Request {
    method: String,
    url: String,
    body: Option<String>,
    has_body: bool,      // redundant with body.is_some() — can be inconsistent!
    is_multipart: bool,  // only meaningful if has_body is true — invisible coupling
}

// GOOD: encode the relationship in the type
enum RequestBody {
    None,
    Text(String),
    Multipart(Vec<FormField>),
}

struct Request {
    method: Method,
    url: Url,
    body: RequestBody,
}
```

### 22.5 Shared Mutable Global State

```rust
// BAD: global mutable state — any code can corrupt it, order-dependent, impossible to test
static mut GLOBAL_COUNTER: u64 = 0;

fn increment() {
    unsafe { GLOBAL_COUNTER += 1; }  // requires unsafe, no concurrency safety
}

// GOOD: explicit state passed through or wrapped in Arc<Mutex<>>
fn increment(counter: &mut u64) {
    *counter += 1;
}

// Or for shared state:
fn increment_shared(counter: Arc<Mutex<u64>>) {
    *counter.lock().unwrap() += 1;
}
```

### 22.6 Premature Optimization That Breaks Invariants

```rust
// BAD: cache is not invalidated when data changes
struct Cache {
    data: Vec<Item>,
    sorted_cache: Vec<Item>,  // cached sorted version
    is_sorted_valid: bool,    // if someone forgets to set this to false...
}

impl Cache {
    fn add_item(&mut self, item: Item) {
        self.data.push(item);
        // LOGIC BUG: forgot to invalidate the cache!
        // is_sorted_valid should be set to false here
    }
}

// GOOD: compute on demand, or use a type that maintains the invariant
struct DataStore {
    // Private: maintains sorted invariant
    sorted_items: SortedVec<Item>,
}
```

### 22.7 Silent Error Swallowing

```rust
// BAD: ignoring errors that represent real failures
fn process(items: Vec<Item>) {
    for item in items {
        if let Ok(result) = heavy_computation(item) {
            store(result);
        }
        // If heavy_computation fails, we silently skip — is that right?
        // This might be fine, or it might be a logic bug
    }
}

// GOOD: be explicit about what failure means
fn process(items: Vec<Item>) -> Result<ProcessStats, ProcessError> {
    let mut successes = 0;
    let mut failures = vec![];

    for item in items {
        match heavy_computation(item) {
            Ok(result) => {
                store(result);
                successes += 1;
            }
            Err(e) => {
                log::warn!("Failed to process item: {}", e);
                failures.push(e);
            }
        }
    }

    if failures.len() > successes {
        return Err(ProcessError::TooManyFailures { failures });
    }

    Ok(ProcessStats { successes, failures: failures.len() })
}
```

---

## 23. The Mental Checklist: A Systematic Thinking Process

Use this checklist when designing any new data structure or function.

### 23.1 Type Design Checklist

```
When designing a TYPE (struct, enum):

□ Can I represent invalid states with this type?
  → If yes: restructure until invalid states are inexpressible

□ Are any fields optional that shouldn't be?
  → Make them required, or split into separate types

□ Are any fields primitive that represent domain concepts?
  → Use newtype wrappers

□ Do multiple fields have an implied relationship?
  → Encode that relationship in the type (typestate, enums)

□ Is the type constructed with many optional fields?
  → Use the Builder pattern with invariant checking in build()

□ Could the type ever be in an "uninitialized" state?
  → Use Option<T> or typestate to make initialization explicit
```

### 23.2 Function Design Checklist

```
When designing a FUNCTION:

□ Is this function total? (defined for all valid inputs)
  → If not: either restrict inputs (change parameter types)
             or expand outputs (return Option or Result)

□ What are the preconditions?
  → Encode them in parameter types, or assert! them at the start

□ What are the postconditions?
  → Can you express them as tests? Can Prusti verify them?

□ What are the side effects?
  → Are they reflected in the type signature? (Result for fallibility,
    &mut for mutation, async for async I/O)

□ Does this function do ONE thing?
  → If it takes a bool parameter that switches behavior, split it into
    two functions

□ Are there any partial operations (indexing, unwrap, division)?
  → Either prove they're safe with a comment, or replace with safe
    alternatives (get(), checked_div(), etc.)
```

### 23.3 Invariant Design Checklist

```
When maintaining INVARIANTS:

□ Have I identified all invariants of this data structure?
□ Are invariants documented in comments above the struct?
□ Are fields private to prevent external invariant violation?
□ Is the constructor the only way to create a valid instance?
□ Does every mutation method preserve all invariants?
□ Is there an assert_invariants() method for debug builds?
□ Are the invariants tested with property-based tests?
```

### 23.4 The ACID Thinking Process for Logic

Borrow from database theory — apply to your code logic:

```
ATOMICITY:   Does this operation complete fully or not at all?
             → Use transactions, rollback on error

CONSISTENCY: Does this operation leave all invariants intact?
             → Check all invariants after mutation

ISOLATION:   Can concurrent operations corrupt each other's logic?
             → Use locks, channels, or atomic operations

DURABILITY:  If this operation succeeds, is the result permanent?
             → Flush to disk, confirm persistence before returning Ok
```

### 23.5 The "What Can Go Wrong" Brainstorm

Before implementing any function, ask:

```
1. Empty input?       → What if the slice/collection/string is empty?
2. Single element?    → Does the algorithm behave correctly for n=1?
3. Maximum input?     → What if integers are at max value? Collections are huge?
4. Duplicate values?  → Are duplicates handled or assumed unique?
5. Sorted/unsorted?   → Is sorting assumed? What if it's violated?
6. Null/None values?  → Every Option must be handled
7. Concurrent access? → Is this called from multiple threads?
8. Order dependency?  → Must A happen before B?
9. Type overflow?     → Are integer operations overflow-safe?
10. Edge geometry?    → For geometric/index math: what about boundary cases?
```

---

## Summary: The Layered Defense

Logic-correct Rust code uses multiple layers of defense simultaneously:

```
LAYER 1 — TYPE SYSTEM (compile time)
  ├── Make illegal states unrepresentable
  ├── Typestate pattern for protocol correctness
  ├── Phantom types for units and capabilities
  ├── Newtype pattern for domain concepts
  ├── Parse, don't validate
  └── Total functions (Option/Result return types)

LAYER 2 — ASSERTIONS (debug runtime)
  ├── debug_assert! for invariant checking
  ├── assert! for preconditions in public APIs
  └── Invariant checking methods called after mutations

LAYER 3 — PROPERTY-BASED TESTING
  ├── proptest / quickcheck
  ├── Testing loop invariants
  ├── Round-trip properties
  └── Metamorphic properties

LAYER 4 — FORMAL VERIFICATION (optional, highest confidence)
  ├── Prusti for contract proving
  ├── Kani for bounded model checking
  └── MIRI for undefined behavior detection

LAYER 5 — SYSTEMATIC CODE REVIEW
  ├── Anti-pattern checklist
  ├── Invariant checklist
  └── Function design checklist
```

The strongest code uses **all five layers**. At minimum, any production Rust codebase should use Layers 1, 2, and 3.

---

## Further Reading

- **"Parse, Don't Validate"** — Alexis King (lexi-lambda.github.io)
- **"Type-Driven Development with Idris"** — Edwin Brady (concepts transfer to Rust)
- **"Programming Language Foundations in Agda"** — Philip Wadler (formal methods foundations)
- **Rust Reference — Type System** — https://doc.rust-lang.org/reference/types.html
- **Prusti User Guide** — https://viperproject.github.io/prusti-dev/
- **Kani Documentation** — https://model-checking.github.io/kani/
- **proptest Documentation** — https://proptest-rs.github.io/proptest/
- **"Designing Data-Intensive Applications"** — Martin Kleppmann (for concurrency patterns)
- **"Software Abstractions"** — Daniel Jackson (Alloy modeling, applicable to domain modeling)

