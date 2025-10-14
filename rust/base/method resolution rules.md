# Comprehensive Guide to Rust's Method Resolution Rules

## Table of Contents
1. [Introduction](#introduction)
2. [Method Resolution Fundamentals](#fundamentals)
3. [The Resolution Algorithm](#algorithm)
4. [Receiver Types and Auto-Dereferencing](#receivers)
5. [Trait Methods vs Inherent Methods](#trait-vs-inherent)
6. [Fully Qualified Syntax](#qualified-syntax)
7. [Advanced Examples](#advanced-examples)
8. [Common Pitfalls](#pitfalls)

## Introduction {#introduction}

Rust's method resolution is a sophisticated system that determines which method to call when you write `value.method()`. Understanding these rules is crucial for writing idiomatic Rust code and avoiding confusing compiler errors.

## Method Resolution Fundamentals {#fundamentals}

When you call a method in Rust, the compiler follows a specific set of rules to determine which method to invoke. The process involves:

1. **Type checking** - Determining the type of the receiver
2. **Auto-referencing/dereferencing** - Adjusting the receiver type
3. **Method lookup** - Searching for matching methods
4. **Trait resolution** - Considering trait methods in scope

### Key Principles

- **Inherent methods take precedence** over trait methods
- **Auto-referencing and auto-dereferencing** happen automatically
- **Trait methods must be in scope** to be called
- **Multiple applicable methods** result in ambiguity errors

## The Resolution Algorithm {#algorithm}

When you write `receiver.method()`, Rust follows this algorithm:

### Step 1: Determine the Receiver Type

The compiler first determines the type `T` of the receiver expression.

### Step 2: Build Candidate Receiver Types

Rust constructs a list of candidate receiver types by applying these transformations in order:

1. `T` (the value itself)
2. `&T` (immutable reference)
3. `&mut T` (mutable reference)
4. `T` dereferenced through `Deref` → produces `U`, then try `U`, `&U`, `&mut U`
5. Continue dereferencing through `Deref` chains

### Step 3: Search for Methods

For each candidate receiver type, Rust searches for methods in this order:

1. **Inherent methods** defined directly on the type
2. **Trait methods** from traits in scope that are implemented for the type

### Step 4: Select the Best Match

- If exactly one method matches, use it
- If multiple methods match, report an ambiguity error
- If no methods match, report a "method not found" error

## Receiver Types and Auto-Dereferencing {#receivers}

Rust automatically adjusts receiver types to make method calls ergonomic.

### Basic Auto-Referencing

```rust
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    // Takes &self
    fn distance_from_origin(&self) -> f64 {
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
    
    // Takes &mut self
    fn shift(&mut self, dx: i32, dy: i32) {
        self.x += dx;
        self.y += dy;
    }
    
    // Takes self (consumes)
    fn into_tuple(self) -> (i32, i32) {
        (self.x, self.y)
    }
}

fn main() {
    let mut point = Point { x: 3, y: 4 };
    
    // All of these work due to auto-referencing:
    point.distance_from_origin();  // Auto-borrows as &point
    (&point).distance_from_origin(); // Explicit borrow
    
    point.shift(1, 1);  // Auto-borrows as &mut point
    (&mut point).shift(1, 1); // Explicit mutable borrow
    
    point.into_tuple();  // Takes ownership (no auto-ref needed)
}
```

### Auto-Dereferencing with Smart Pointers

```rust
use std::rc::Rc;
use std::ops::Deref;

struct MyBox<T>(T);

impl<T> MyBox<T> {
    fn new(x: T) -> MyBox<T> {
        MyBox(x)
    }
}

impl<T> Deref for MyBox<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

struct Person {
    name: String,
}

impl Person {
    fn greet(&self) {
        println!("Hello, I'm {}", self.name);
    }
}

fn main() {
    let person = Person { name: "Alice".to_string() };
    let boxed = MyBox::new(person);
    let rc = Rc::new(Person { name: "Bob".to_string() });
    
    // Auto-dereferencing happens:
    boxed.greet();  // MyBox<Person> -> &Person -> greet()
    rc.greet();     // Rc<Person> -> &Person -> greet()
}
```

### Complex Dereferencing Chains

```rust
use std::rc::Rc;
use std::sync::Arc;

struct Data {
    value: i32,
}

impl Data {
    fn display(&self) {
        println!("Value: {}", self.value);
    }
}

fn main() {
    // Multiple levels of smart pointers
    let data = Data { value: 42 };
    let rc = Rc::new(data);
    let arc = Arc::new(rc);
    
    // Rust dereferences through: Arc -> Rc -> Data
    arc.display();
}
```

## Trait Methods vs Inherent Methods {#trait-vs-inherent}

Inherent methods always take precedence over trait methods.

### Precedence Example

```rust
struct Number(i32);

// Inherent implementation
impl Number {
    fn display(&self) {
        println!("Inherent: {}", self.0);
    }
}

// Trait implementation
trait Show {
    fn display(&self);
}

impl Show for Number {
    fn display(&self) {
        println!("Trait: {}", self.0);
    }
}

fn main() {
    let num = Number(42);
    
    // Calls the inherent method (takes precedence)
    num.display();  // Output: "Inherent: 42"
    
    // To call the trait method, use fully qualified syntax
    Show::display(&num);  // Output: "Trait: 42"
}
```

### Trait Scope Requirements

```rust
mod my_trait {
    pub trait Greet {
        fn greet(&self);
    }
    
    impl Greet for String {
        fn greet(&self) {
            println!("Hello from {}", self);
        }
    }
}

fn main() {
    let name = String::from("Rust");
    
    // This won't work - trait not in scope:
    // name.greet();  // ERROR: method not found
    
    // Bring trait into scope:
    use my_trait::Greet;
    name.greet();  // Now it works!
}
```

## Fully Qualified Syntax {#qualified-syntax}

When method calls are ambiguous, use fully qualified syntax to specify exactly which method to call.

### Basic Fully Qualified Syntax

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
        println!("This is your captain speaking.");
    }
}

impl Wizard for Human {
    fn fly(&self) {
        println!("Up!");
    }
}

impl Human {
    fn fly(&self) {
        println!("*waving arms furiously*");
    }
}

fn main() {
    let person = Human;
    
    // Calls inherent method
    person.fly();  // Output: "*waving arms furiously*"
    
    // Call specific trait methods
    Pilot::fly(&person);  // Output: "This is your captain speaking."
    Wizard::fly(&person); // Output: "Up!"
    
    // Alternative fully qualified syntax
    <Human as Pilot>::fly(&person);
    <Human as Wizard>::fly(&person);
}
```

### Associated Functions (No Receiver)

```rust
trait Animal {
    fn baby_name() -> String;
}

struct Dog;

impl Dog {
    fn baby_name() -> String {
        String::from("puppy")
    }
}

impl Animal for Dog {
    fn baby_name() -> String {
        String::from("baby dog")
    }
}

fn main() {
    // Calls inherent associated function
    println!("A baby dog is called a {}", Dog::baby_name());
    // Output: "A baby dog is called a puppy"
    
    // This doesn't work - which trait?
    // println!("A baby dog is called a {}", Animal::baby_name());  // ERROR
    
    // Must use fully qualified syntax:
    println!("A baby dog is called a {}", <Dog as Animal>::baby_name());
    // Output: "A baby dog is called a baby dog"
}
```

### Universal Function Call Syntax (UFCS)

```rust
struct Counter {
    count: i32,
}

impl Counter {
    fn increment(&mut self) {
        self.count += 1;
    }
    
    fn get(&self) -> i32 {
        self.count
    }
}

fn main() {
    let mut counter = Counter { count: 0 };
    
    // Normal method call
    counter.increment();
    
    // UFCS - equivalent
    Counter::increment(&mut counter);
    
    // For getting the value
    let value = counter.get();
    let value2 = Counter::get(&counter);
    
    assert_eq!(value, value2);
}
```

## Advanced Examples {#advanced-examples}

### Example 1: Method Resolution with Generic Types

```rust
struct Container<T> {
    value: T,
}

impl<T> Container<T> {
    fn new(value: T) -> Self {
        Container { value }
    }
    
    fn get(&self) -> &T {
        &self.value
    }
}

// Specialized implementation for String
impl Container<String> {
    fn len(&self) -> usize {
        self.value.len()
    }
}

// Trait implementation
trait Display {
    fn show(&self);
}

impl<T: std::fmt::Debug> Display for Container<T> {
    fn show(&self) {
        println!("{:?}", self.value);
    }
}

fn main() {
    let num_container = Container::new(42);
    let str_container = Container::new(String::from("Hello"));
    
    // Generic method available on both
    println!("{}", num_container.get());
    
    // Specialized method only on Container<String>
    println!("Length: {}", str_container.len());
    // num_container.len(); // ERROR: method not found
    
    // Trait method available on both (requires Display in scope)
    num_container.show();
    str_container.show();
}
```

### Example 2: Deref Coercion in Method Calls

```rust
use std::ops::Deref;

struct MyString {
    data: String,
}

impl Deref for MyString {
    type Target = String;
    
    fn deref(&self) -> &Self::Target {
        &self.data
    }
}

impl MyString {
    fn new(s: &str) -> Self {
        MyString { data: s.to_string() }
    }
    
    // Custom method on MyString
    fn custom_method(&self) {
        println!("Custom method on MyString");
    }
}

fn main() {
    let my_string = MyString::new("Hello");
    
    // Calls inherent method on MyString
    my_string.custom_method();
    
    // These call methods on String (via Deref)
    println!("Length: {}", my_string.len());
    println!("Uppercase: {}", my_string.to_uppercase());
    
    // Can also call methods on str (String derefs to str)
    println!("Starts with H: {}", my_string.starts_with("H"));
}
```

### Example 3: Multiple Trait Bounds and Method Resolution

```rust
trait Reader {
    fn read(&self) -> String;
}

trait Writer {
    fn write(&mut self, data: &str);
}

struct File {
    content: String,
}

impl Reader for File {
    fn read(&self) -> String {
        self.content.clone()
    }
}

impl Writer for File {
    fn write(&mut self, data: &str) {
        self.content.push_str(data);
    }
}

// Generic function with trait bounds
fn process<T>(mut item: T) 
where 
    T: Reader + Writer 
{
    let content = item.read();
    println!("Read: {}", content);
    item.write(" - processed");
}

fn main() {
    let mut file = File {
        content: String::from("Initial content"),
    };
    
    // Both trait methods can be called
    file.write(" more text");
    println!("{}", file.read());
    
    process(file);
}
```

### Example 4: Extension Traits Pattern

```rust
// Common pattern in Rust: extending existing types with traits

trait IteratorExt: Iterator {
    fn collect_vec(self) -> Vec<Self::Item>
    where
        Self: Sized,
    {
        self.collect()
    }
    
    fn sum_if_numbers(self) -> Option<i32>
    where
        Self: Sized,
        Self::Item: Into<i32>,
    {
        Some(self.map(|x| x.into()).sum())
    }
}

// Blanket implementation
impl<T: Iterator> IteratorExt for T {}

fn main() {
    let numbers = vec![1, 2, 3, 4, 5];
    
    // Standard iterator methods work
    let doubled: Vec<_> = numbers.iter().map(|x| x * 2).collect();
    
    // Extension methods also work (trait must be in scope)
    let collected = numbers.iter().copied().collect_vec();
    
    println!("{:?}", collected);
}
```

### Example 5: Associated Type Disambiguation

```rust
trait Graph {
    type Node;
    type Edge;
    
    fn has_edge(&self, from: Self::Node, to: Self::Node) -> bool;
}

struct DirectedGraph {
    edges: Vec<(usize, usize)>,
}

impl Graph for DirectedGraph {
    type Node = usize;
    type Edge = (usize, usize);
    
    fn has_edge(&self, from: Self::Node, to: Self::Node) -> bool {
        self.edges.contains(&(from, to))
    }
}

// Using associated types explicitly
fn check_connection<G: Graph>(graph: &G, from: G::Node, to: G::Node) -> bool {
    graph.has_edge(from, to)
}

fn main() {
    let graph = DirectedGraph {
        edges: vec![(0, 1), (1, 2), (2, 0)],
    };
    
    println!("Has edge 0->1: {}", graph.has_edge(0, 1));
    println!("Has edge 1->0: {}", graph.has_edge(1, 0));
    
    println!("Connected: {}", check_connection(&graph, 0, 1));
}
```

## Common Pitfalls {#pitfalls}

### Pitfall 1: Trait Not In Scope

```rust
mod traits {
    pub trait Double {
        fn double(&self) -> Self;
    }
    
    impl Double for i32 {
        fn double(&self) -> Self {
            self * 2
        }
    }
}

fn main() {
    let x = 5;
    
    // ERROR: method not found
    // let y = x.double();
    
    // Solution: bring trait into scope
    use traits::Double;
    let y = x.double();
    println!("{}", y);
}
```

### Pitfall 2: Ambiguous Method Calls

```rust
trait A {
    fn method(&self) -> &str {
        "A"
    }
}

trait B {
    fn method(&self) -> &str {
        "B"
    }
}

struct S;

impl A for S {}
impl B for S {}

fn main() {
    let s = S;
    
    // ERROR: multiple applicable items in scope
    // println!("{}", s.method());
    
    // Solution: use fully qualified syntax
    println!("{}", <S as A>::method(&s));
    println!("{}", <S as B>::method(&s));
}
```

### Pitfall 3: Confusion with Deref Coercion

```rust
use std::ops::Deref;

struct Wrapper<T>(T);

impl<T> Deref for Wrapper<T> {
    type Target = T;
    fn deref(&self) -> &T {
        &self.0
    }
}

impl<T> Wrapper<T> {
    fn value(&self) -> &T {
        &self.0
    }
}

impl Wrapper<String> {
    // This shadows String's len() method
    fn len(&self) -> usize {
        100  // Always returns 100
    }
}

fn main() {
    let wrapped = Wrapper(String::from("Hello"));
    
    // Calls Wrapper's len, not String's!
    println!("Length: {}", wrapped.len());  // Output: 100
    
    // To call String's len:
    println!("Actual length: {}", wrapped.deref().len());  // Output: 5
    println!("Or: {}", (*wrapped).len());  // Output: 5
}
```

### Pitfall 4: Method Resolution with Box<dyn Trait>

```rust
trait Animal {
    fn speak(&self);
    fn name(&self) -> &str;
}

struct Dog {
    name: String,
}

impl Animal for Dog {
    fn speak(&self) {
        println!("Woof!");
    }
    
    fn name(&self) -> &str {
        &self.name
    }
}

impl Dog {
    // This method is NOT available through Box<dyn Animal>
    fn fetch(&self) {
        println!("{} is fetching!", self.name);
    }
}

fn main() {
    let dog = Dog { name: "Buddy".to_string() };
    let animal: Box<dyn Animal> = Box::new(dog);
    
    // These work:
    animal.speak();
    println!("Name: {}", animal.name());
    
    // This doesn't work - fetch is not in the Animal trait:
    // animal.fetch();  // ERROR: method not found
    
    // To call fetch, need concrete type:
    let concrete_dog = Dog { name: "Max".to_string() };
    concrete_dog.fetch();
}
```

### Pitfall 5: Self Type in Traits

```rust
trait Clone2 {
    fn clone2(&self) -> Self;
}

// This won't work for trait objects
impl Clone2 for String {
    fn clone2(&self) -> Self {
        self.clone()
    }
}

fn main() {
    let s = String::from("hello");
    let cloned = s.clone2();
    
    // This would fail:
    // let trait_obj: Box<dyn Clone2> = Box::new(s);
    // ERROR: the trait `Clone2` cannot be made into an object
    
    // Reason: Self has unknown size at compile time for trait objects
}
```

## Summary

Rust's method resolution follows a clear but sophisticated set of rules:

1. **Inherent methods** are checked first, before trait methods
2. **Auto-referencing and dereferencing** happen automatically through `Deref` chains
3. **Trait methods must be in scope** to be called
4. **Fully qualified syntax** resolves ambiguity
5. The compiler tries `T`, `&T`, `&mut T`, then dereferences and repeats

Understanding these rules helps you:
- Write more idiomatic Rust code
- Debug method resolution errors efficiently
- Design better APIs that work naturally with method calls
- Avoid common pitfalls with traits and smart pointers

The key is remembering that Rust's method resolution is designed to be ergonomic while maintaining type safety and zero-cost abstractions.

Excellent question — you’re asking how `s.push()` or `s.push_str()` works **internally in Rust’s standard library**. Let’s break it down carefully.

Your example:

```rust
let mut s = String::from("hello");
s.push_str(", world!");
println!("{s}");
```

### 1. Conceptual overview

A Rust `String` is essentially a **wrapper around a `Vec<u8>`**, which stores UTF-8 bytes.

Internally:

```rust
pub struct String {
    vec: Vec<u8>,
}
```

So, when you call `s.push_str("...")`, it’s basically appending bytes to that internal vector.

---

### 2. The actual implementation (simplified from `rust/src/liballoc/string.rs`)

Here’s the real source (simplified and formatted for clarity):

```rust
// In the Rust standard library (alloc crate)
impl String {
    #[inline]
    pub fn push_str(&mut self, string: &str) {
        self.vec.extend_from_slice(string.as_bytes());
    }

    #[inline]
    pub fn push(&mut self, ch: char) {
        // Each char is converted to UTF-8 bytes
        let mut buf = [0u8; 4];
        let encoded = ch.encode_utf8(&mut buf);
        self.push_str(encoded);
    }
}
```

---

### 3. Breaking it down

**For `push_str`:**

* `string.as_bytes()` converts the `&str` to a UTF-8 byte slice (`&[u8]`).
* `self.vec.extend_from_slice(...)` calls the `Vec` method to copy the bytes to the end of the existing buffer.
* If the capacity is insufficient, `Vec` automatically reallocates to make room.

**For `push`:**

* A `char` in Rust is a Unicode scalar value (4 bytes max).
* It’s encoded into UTF-8 bytes via `encode_utf8(&mut buf)`.
* Then it calls `push_str` to actually append those bytes.

---

### 4. Deep dive: `extend_from_slice`

Inside `alloc/src/vec/mod.rs`, the relevant part:

```rust
impl<T: Copy> Vec<T> {
    pub fn extend_from_slice(&mut self, other: &[T]) {
        let len = self.len();
        let additional = other.len();

        self.reserve(additional);
        unsafe {
            let dst = self.as_mut_ptr().add(len);
            std::ptr::copy_nonoverlapping(other.as_ptr(), dst, additional);
            self.set_len(len + additional);
        }
    }
}
```

So it:

1. Reserves extra space if needed (`reserve` reallocates if full),
2. Copies bytes into memory directly with `ptr::copy_nonoverlapping`,
3. Updates the vector’s length.

---

### 5. So your line:

```rust
s.push_str(", world!");
```

Expands into roughly:

```rust
// Conceptually:
let bytes = ", world!".as_bytes();
s.vec.reserve(bytes.len());
copy bytes into s.vec memory at s.vec.len();
update s.vec.len += bytes.len();
```

---

### 6. Source links (Rust 1.80+)

If you want to explore the **actual current code**, you can read it here:

* [`impl String` in alloc/string.rs](https://doc.rust-lang.org/src/alloc/string.rs.html#1124-1135)
* [`Vec::extend_from_slice` in alloc/vec/mod.rs](https://doc.rust-lang.org/src/alloc/vec/mod.rs.html#2447-2470)

---

Would you like me to show you the **actual memory layout and capacity growth behavior** of `String` (how it reallocates under the hood when pushing text)?


Excellent — you’re asking a **deep Rust ownership and type question**:
How does

```rust
let mut s = String::from("hello");
s.push_str(", world!");
```

actually work?
How does `s` “become” something that has a method like `push_str`?

Let’s unpack this step-by-step, from **types → values → method resolution → ownership.**

---

### 🧩 Step 1: `String::from("hello")`

This line calls the **associated function** `from` defined for `String`:

```rust
impl From<&str> for String {
    fn from(s: &str) -> String {
        String::from_utf8_lossy(s.as_bytes()).into_owned()
    }
}
```

So this returns a new **heap-allocated `String`** that contains `"hello"`.

Now you have:

```rust
let mut s: String = String::from("hello");
```

At this moment:

* `s` is a **mutable variable** (that’s what `mut` does),
* The type of `s` is **`String`** (not `&str`).

---

### 🧠 Step 2: Difference between `String` and `&str`

| Type     | Description                                       | Ownership |
| -------- | ------------------------------------------------- | --------- |
| `&str`   | A *string slice* — borrowed view into UTF-8 bytes | Borrowed  |
| `String` | An *owned, growable heap-allocated string buffer* | Owned     |

So `"hello"` (a string literal) is a `&'static str`,
but `String::from("hello")` *copies* it into a new `String` you own.

---

### 🧱 Step 3: Why `s.push_str` works

In Rust, **method call syntax**:

```rust
s.push_str(", world!");
```

is actually *syntactic sugar* for:

```rust
String::push_str(&mut s, ", world!");
```

That means:

* Rust sees that `s` has type `String`.
* It looks up the `impl String` block for a method named `push_str`.
* Then it automatically passes `&mut s` as the **first argument** (the “receiver”).

You can confirm this equivalence:

```rust
let mut s = String::from("hello");
String::push_str(&mut s, ", world!");
```

→ exact same thing!

---

### ⚙️ Step 4: Ownership & mutability in action

Because `push_str` takes `&mut self`, you must declare:

```rust
let mut s = ...
```

If you didn’t, Rust would error:

```
cannot borrow as mutable
```

`mut` means:

> “I allow this variable’s *contents* to change.”

So the variable binding itself is mutable — you can modify the owned data through it.

---

### 🔍 Step 5: How `s` “becomes” `s.push_str`

Actually, `s` doesn’t “become” `push_str`.
Rather:

* `s` is a `String`.
* The compiler knows `String` has methods like `push_str`, `push`, `len`, etc.
* So when you call `s.push_str(...)`, Rust translates it to a static function call on the type `String` passing `&mut s` automatically.

This is part of Rust’s **method resolution** rules — it’s just syntactic sugar for a regular function call.

---

### 🧩 Visual Summary

```
"hello"  (type: &str)
   │
   ▼
String::from("hello")   // allocates heap buffer
   │
   ▼
let mut s: String = ... // owns "hello"
   │
   ▼
s.push_str(", world!")  // expands to String::push_str(&mut s, ", world!")
   │
   ▼
println!("{s}")         // uses Display trait to print the final string
```

---

If you’d like, I can **show memory layout (stack + heap)** diagram for this exact snippet — how `"hello"` moves into heap memory and what `s` points to.
Would you like that visualization?


🔥 Excellent — you’re asking one of the **most powerful and underrated** questions in learning Rust deeply:

> “How can I *see* what a method call like `s.push_str()` actually expands into — and how do I inspect Rust’s **method resolution rules** in an IDE?”

Let’s break this down into **two goals** and then show the **tools & techniques** (in VS Code, Rust Analyzer, and CLI).

---

## 🧭 Goal 1 — See what method calls expand into

When you write:

```rust
s.push_str(", world!");
```

Rust actually turns that into:

```rust
String::push_str(&mut s, ", world!");
```

To *see or confirm* that inside your IDE:

### ✅ Option 1: Hover / Go to Definition (VS Code + Rust Analyzer)

Rust Analyzer (RA) is the key tool here.

1. Install the **Rust Analyzer** extension.
2. Hover over `push_str`.

   * It will show the **full signature**:

     ```
     pub fn push_str(&mut self, string: &str)
     ```
3. Right-click → **Go to Definition** (or `F12`).

   * This jumps straight to the standard library’s implementation in `alloc::string::String`.
   * You can see that it’s just:

     ```rust
     pub fn push_str(&mut self, string: &str) {
         self.vec.extend_from_slice(string.as_bytes());
     }
     ```

You’re literally looking at what the compiler will call.

---

### ✅ Option 2: Type and method inference (VS Code command)

You can check what the compiler *thinks* `s` is and what method it’s calling:

1. Place your cursor on `s`.

2. Run command:

   ```
   Rust Analyzer: Show Type
   ```

   → will show `String`.

3. Place your cursor on `.push_str` and run:

   ```
   Rust Analyzer: Show References or Go to Definition
   ```

   → shows exactly which `impl` block it resolves to.

---

### ✅ Option 3: `cargo expand` (to see macro expansions)

If you want to see **macro expansions** (e.g., `println!`, `vec!`, `format!`):

```bash
cargo install cargo-expand
cargo expand
```

But note — this shows *macro* expansions, not method desugarings (like `s.push_str` → `String::push_str(&mut s)`), because that transformation happens after macro expansion, in the compiler’s lowering phase.

---

## 🧭 Goal 2 — Understand Method Resolution Rules

Rust has a very strict, layered method resolution system (in `rustc`), and you can **inspect or trace** it using these tools.

### 🧩 Summary of Rust method resolution order

When you call:

```rust
s.push_str("x");
```

The compiler looks for methods in this order:

1. **Inherent methods** — methods defined directly on the type (`impl String { ... }`).
2. **Trait methods** where:

   * The trait is **in scope** (via `use`).
   * And the trait is **implemented** for the receiver type.
3. **Auto-dereferencing**:

   * If `s` is `&String`, Rust tries `String`’s methods.
   * Then `Deref` and `DerefMut` are applied recursively.
4. **Autoref**:

   * Rust may insert `&` or `&mut` automatically as needed to match method signatures.

So:

```rust
let mut s = String::from("hi");
s.push_str("!");
```

→ `s` is a `String`.
→ Compiler finds `impl String` → `push_str(&mut self, ...)`.
→ Automatically passes `&mut s`.

---

### ✅ Option 4: Use `rust-analyzer` “Find Implementations”

In VS Code:

* Right-click on the type name (`String`).
* Choose **"Find all implementations"**.
* You’ll see every `impl String` and every trait implemented for `String`.

That’s the set of all methods that `s` can legally call.

---

### ✅ Option 5: CLI inspection via `rustdoc`

You can explore the actual implementation tree:

```bash
rustup doc --std
```

or open [https://doc.rust-lang.org/std/string/struct.String.html](https://doc.rust-lang.org/std/string/struct.String.html)

* Scroll to “Methods from Deref<Target = str>”.
* These are the *inherited methods* from `&str`.
* Methods directly on `String` are “Inherent methods”.

That’s the same lookup chain the compiler uses.

---

## ⚙️ Bonus — See compiler internals (advanced)

If you ever want to **see the compiler’s lowered code**:

```bash
rustc --edition=2021 -Zunpretty=hir yourfile.rs
```

(`hir` = High-level Intermediate Representation — it shows the desugared form.)

Requires nightly:

```bash
rustup default nightly
```

Then:

```bash
cargo rustc -- -Zunpretty=hir
```

You’ll see:

```rust
String::push_str(&mut s, ", world!");
```

---

## 🧠 TL;DR — How to see expansions & method resolution

| Tool                                 | What it shows                        | Command / Shortcut                 |
| ------------------------------------ | ------------------------------------ | ---------------------------------- |
| **Rust Analyzer Hover**              | Method signature                     | Hover over method                  |
| **Go to Definition (F12)**           | Actual implementation                | F12                                |
| **Find Implementations**             | All `impl`s in scope                 | Right-click → Find Implementations |
| **cargo expand**                     | Macro expansions                     | `cargo expand`                     |
| **rustup doc --std**                 | See all methods and inherited traits | Built-in docs                      |
| **rustc -Zunpretty=hir** *(nightly)* | Desugared method call form           | Compiler internal                  |

---

Would you like me to show you a **screenshot-style breakdown of what Rust Analyzer displays** for `s.push_str()` (type, method, impl, docs, etc.) — like a mini IDE tour of that call?
