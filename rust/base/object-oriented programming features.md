# **Comprehensive Guide to Object-Oriented Programming in Rust**

*A rigorous exploration from first principles to mastery*

---

## **📋 Table of Contents**

1. [Foundational Philosophy: OOP vs Rust's Paradigm](#1-foundational-philosophy)
2. [Encapsulation](#2-encapsulation)
3. [Structs and Methods](#3-structs-and-methods)
4. [Traits: Rust's Interface System](#4-traits)
5. [Polymorphism Through Traits](#5-polymorphism)
6. [Trait Objects and Dynamic Dispatch](#6-trait-objects)
7. [Inheritance-like Patterns](#7-inheritance-patterns)
8. [Advanced Trait Patterns](#8-advanced-traits)
9. [Real-World Design Patterns](#9-design-patterns)
10. [Performance Implications](#10-performance)

---

## **1. Foundational Philosophy: OOP vs Rust's Paradigm** {#1-foundational-philosophy}

### **Mental Model: Composition Over Inheritance**

Before diving in, understand this crucial distinction:

**Traditional OOP (Java/C++):**
```
Object = Data + Methods + Inheritance Hierarchy
```

**Rust's Approach:**
```
Type = Data (Structs/Enums)
Behavior = Traits (Interfaces)
Polymorphism = Trait Bounds + Trait Objects
```

**ASCII Visualization:**

```
Traditional OOP Hierarchy:
┌─────────────┐
│   Animal    │ (base class)
└─────────────┘
       △
       │
   ┌───┴───┐
   │       │
┌──┴──┐ ┌──┴──┐
│ Dog │ │ Cat │
└─────┘ └─────┘

Rust's Trait-Based Approach:
┌─────────────┐     ┌─────────────┐
│    Dog      │────▶│   Animal    │ (trait)
│  (struct)   │impl │  (behavior) │
└─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐
│    Cat      │────▶│   Animal    │ (trait)
│  (struct)   │impl │  (behavior) │
└─────────────┘     └─────────────┘
```

**Why This Matters:**
- **Flexibility**: Types can implement multiple traits (no diamond problem)
- **Performance**: Zero-cost abstractions with static dispatch
- **Safety**: Ownership prevents common OOP bugs (null references, use-after-free)

---

## **2. Encapsulation: Privacy and Information Hiding** {#2-encapsulation}

**Concept: Encapsulation** means bundling data and controlling access to it. In Rust, this is achieved through **visibility modifiers**.

### **Visibility Rules**

```
┌─────────────────────────────────────────────────┐
│         Rust Visibility Hierarchy               │
├─────────────────────────────────────────────────┤
│ pub            → Public to all                  │
│ pub(crate)     → Public within current crate    │
│ pub(super)     → Public to parent module        │
│ pub(in path)   → Public to specific path        │
│ (no modifier)  → Private to current module      │
└─────────────────────────────────────────────────┘
```

### **Example: Bank Account with Encapsulation**

```rust
// src/lib.rs
pub mod banking {
    // Public struct, but fields are private by default
    pub struct BankAccount {
        account_number: u64,      // private field
        balance: f64,             // private field
        pub owner: String,        // public field (not recommended)
    }

    impl BankAccount {
        // Constructor (associated function)
        pub fn new(account_number: u64, owner: String) -> Self {
            Self {
                account_number,
                balance: 0.0,
                owner,
            }
        }

        // Public method - controlled access
        pub fn deposit(&mut self, amount: f64) -> Result<(), String> {
            if amount <= 0.0 {
                return Err("Amount must be positive".to_string());
            }
            self.balance += amount;
            Ok(())
        }

        // Public method - controlled access
        pub fn withdraw(&mut self, amount: f64) -> Result<(), String> {
            if amount <= 0.0 {
                return Err("Amount must be positive".to_string());
            }
            if amount > self.balance {
                return Err("Insufficient funds".to_string());
            }
            self.balance -= amount;
            Ok(())
        }

        // Getter - read-only access
        pub fn balance(&self) -> f64 {
            self.balance
        }

        // Private helper method
        fn validate_transaction(&self, amount: f64) -> bool {
            amount > 0.0 && amount <= self.balance
        }
    }
}

// Usage
use banking::BankAccount;

fn main() {
    let mut account = BankAccount::new(12345, "Alice".to_string());
    
    // This works:
    account.deposit(100.0).unwrap();
    println!("Balance: {}", account.balance());
    
    // This would fail at compile time:
    // account.balance = 1000000.0;  // ERROR: field is private
    // account.account_number;        // ERROR: field is private
}
```

**Key Insights:**
1. **Default privacy**: Unlike C++/Java, struct fields are private by default
2. **Explicit public API**: You choose what to expose with `pub`
3. **Compile-time enforcement**: No runtime overhead for access control

---

## **3. Structs and Methods: Data + Behavior** {#3-structs-and-methods}

### **The Three Types of Methods**

```
┌──────────────────────────────────────────────────────┐
│              Method Types in Rust                    │
├──────────────────────────────────────────────────────┤
│ &self        → Borrows immutably (read-only)        │
│ &mut self    → Borrows mutably (can modify)         │
│ self         → Takes ownership (consumes)            │
│ (no self)    → Associated function (like static)    │
└──────────────────────────────────────────────────────┘
```

### **Comprehensive Example: Rectangle**

```rust
#[derive(Debug, Clone)]
pub struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    // Associated function (constructor pattern)
    pub fn new(width: f64, height: f64) -> Self {
        assert!(width > 0.0 && height > 0.0, "Dimensions must be positive");
        Self { width, height }
    }

    // Another associated function (named constructor)
    pub fn square(size: f64) -> Self {
        Self::new(size, size)
    }

    // Method with immutable borrow
    pub fn area(&self) -> f64 {
        self.width * self.height
    }

    // Method with immutable borrow
    pub fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }

    // Method with mutable borrow
    pub fn scale(&mut self, factor: f64) {
        assert!(factor > 0.0, "Scale factor must be positive");
        self.width *= factor;
        self.height *= factor;
    }

    // Method that takes ownership (consumes self)
    pub fn into_square(self) -> Rectangle {
        let avg = (self.width + self.height) / 2.0;
        Rectangle::square(avg)
    }

    // Method that takes another reference
    pub fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
}

// Multiple impl blocks are allowed (for organization)
impl Rectangle {
    // Getter methods
    pub fn width(&self) -> f64 {
        self.width
    }

    pub fn height(&self) -> f64 {
        self.height
    }
}

// Usage examples
fn main() {
    // Using associated function
    let mut rect = Rectangle::new(10.0, 20.0);
    
    // Using &self methods
    println!("Area: {}", rect.area());
    println!("Perimeter: {}", rect.perimeter());
    
    // Using &mut self method
    rect.scale(2.0);
    println!("After scaling: {:?}", rect);
    
    // Using self method (consumes rect)
    let square = rect.into_square();
    // rect is now moved, cannot be used
    // println!("{:?}", rect); // ERROR: value borrowed after move
    
    println!("Square: {:?}", square);
}
```

**Decision Tree: Which Self Type?**

```
                    ┌───────────────┐
                    │ Need to use   │
                    │ self in       │
                    │ method?       │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
              ┌─▼─┐                   ┌─▼─┐
              │YES│                   │NO │
              └─┬─┘                   └─┬─┘
                │                       │
        ┌───────▼────────┐              │
        │ Will you modify│              │
        │ the struct?    │              │
        └───────┬────────┘              │
                │                       │
        ┌───────┴────────┐              │
        │                │              │
      ┌─▼─┐            ┌─▼─┐            │
      │YES│            │NO │            │
      └─┬─┘            └─┬─┘            │
        │                │              │
        │                │              │
 ┌──────▼──────┐  ┌──────▼──────┐  ┌───▼────────┐
 │  &mut self  │  │    &self    │  │ Associated │
 │             │  │             │  │ Function   │
 │ Can modify  │  │ Read-only   │  │ (no self)  │
 └─────────────┘  └─────────────┘  └────────────┘

        Special case:
        ┌─────────────────┐
        │ Need to consume │
        │ and transform?  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │      self       │
        │  (by value)     │
        └─────────────────┘
```

---

## **4. Traits: Rust's Interface System** {#4-traits}

**Concept: Trait** - A collection of methods that types can implement. Think of it as a contract or interface.

### **Basic Trait Definition**

```rust
// Define a trait
pub trait Drawable {
    // Required method (must be implemented)
    fn draw(&self);
    
    // Provided method (default implementation)
    fn describe(&self) {
        println!("This is a drawable object");
    }
    
    // Required method with return value
    fn position(&self) -> (i32, i32);
}

// Implement trait for a type
struct Circle {
    x: i32,
    y: i32,
    radius: f64,
}

impl Drawable for Circle {
    fn draw(&self) {
        println!("Drawing circle at ({}, {}) with radius {}", 
                 self.x, self.y, self.radius);
    }
    
    fn position(&self) -> (i32, i32) {
        (self.x, self.y)
    }
    
    // describe() uses default implementation
}

struct Rectangle {
    x: i32,
    y: i32,
    width: f64,
    height: f64,
}

impl Drawable for Rectangle {
    fn draw(&self) {
        println!("Drawing rectangle at ({}, {})", self.x, self.y);
    }
    
    fn position(&self) -> (i32, i32) {
        (self.x, self.y)
    }
    
    // Override default implementation
    fn describe(&self) {
        println!("Rectangle: {}x{}", self.width, self.height);
    }
}
```

### **Trait Bounds: Constraining Generic Types**

```rust
// Function that works with any Drawable type
fn render<T: Drawable>(item: &T) {
    item.describe();
    item.draw();
}

// Multiple trait bounds
fn render_and_clone<T: Drawable + Clone>(item: &T) -> T {
    item.draw();
    item.clone()
}

// Alternative syntax with where clause (more readable)
fn complex_render<T>(item: &T) 
where
    T: Drawable + Clone + std::fmt::Debug,
{
    println!("{:?}", item);
    item.draw();
}

// Usage
fn main() {
    let circle = Circle { x: 10, y: 20, radius: 5.0 };
    let rect = Rectangle { x: 0, y: 0, width: 30.0, height: 40.0 };
    
    render(&circle);
    render(&rect);
}
```

**Visualization: Trait Bounds**

```
Without Trait Bounds:
┌──────────────┐
│  Function    │
│      │       │
│      ▼       │
│   accepts    │
│   any T      │
│   (limited)  │
└──────────────┘

With Trait Bounds:
┌──────────────┐
│  Function    │
│   <T: Trait> │
│      │       │
│      ▼       │
│   accepts    │
│   only types │
│   that impl  │
│   Trait      │
└──────────────┘

┌─────────────────────────────────────┐
│ Compiler verifies at compile time   │
│ that T has required methods         │
│ → Zero runtime cost                 │
└─────────────────────────────────────┘
```

---

## **5. Polymorphism Through Traits** {#5-polymorphism}

**Concept: Polymorphism** - The ability to treat different types uniformly when they share common behavior.

Rust provides **two types** of polymorphism:

1. **Static Dispatch** (compile-time, zero-cost)
2. **Dynamic Dispatch** (runtime, slight overhead)

### **Static Dispatch with Generics**

```rust
trait Animal {
    fn make_sound(&self) -> &str;
    fn name(&self) -> &str;
}

struct Dog {
    name: String,
}

struct Cat {
    name: String,
}

impl Animal for Dog {
    fn make_sound(&self) -> &str {
        "Woof!"
    }
    
    fn name(&self) -> &str {
        &self.name
    }
}

impl Animal for Cat {
    fn make_sound(&self) -> &str {
        "Meow!"
    }
    
    fn name(&self) -> &str {
        &self.name
    }
}

// Static dispatch - compiler generates separate code for each type
fn interact<T: Animal>(animal: &T) {
    println!("{} says: {}", animal.name(), animal.make_sound());
}

// Equivalent to writing:
// fn interact_dog(animal: &Dog) { ... }
// fn interact_cat(animal: &Cat) { ... }

fn main() {
    let dog = Dog { name: "Buddy".to_string() };
    let cat = Cat { name: "Whiskers".to_string() };
    
    interact(&dog);  // Calls generated Dog version
    interact(&cat);  // Calls generated Cat version
}
```

**Flow Chart: Static Dispatch**

```
Source Code:
interact(&dog)  ─┐
                 │
interact(&cat)  ─┤
                 │
                 ▼
        ┌─────────────────┐
        │   Compiler      │
        │   Monomorphizes │
        └────────┬────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
┌─────────────────┐  ┌─────────────────┐
│ interact_dog()  │  │ interact_cat()  │
│ (specialized)   │  │ (specialized)   │
└─────────────────┘  └─────────────────┘

Performance: Direct function call (no overhead)
Binary Size: Larger (code duplication)
```

---

## **6. Trait Objects and Dynamic Dispatch** {#6-trait-objects}

**Concept: Trait Object** - A pointer to any type that implements a trait, enabling runtime polymorphism.

Syntax: `dyn Trait`

### **Dynamic Dispatch Example**

```rust
trait Animal {
    fn make_sound(&self) -> &str;
    fn name(&self) -> &str;
}

// Same Dog and Cat implementations as before...
struct Dog { name: String }
struct Cat { name: String }

impl Animal for Dog {
    fn make_sound(&self) -> &str { "Woof!" }
    fn name(&self) -> &str { &self.name }
}

impl Animal for Cat {
    fn make_sound(&self) -> &str { "Meow!" }
    fn name(&self) -> &str { &self.name }
}

// Dynamic dispatch - single function handles all types at runtime
fn interact(animal: &dyn Animal) {
    println!("{} says: {}", animal.name(), animal.make_sound());
}

// Storing different types in a collection
fn main() {
    let dog = Dog { name: "Buddy".to_string() };
    let cat = Cat { name: "Whiskers".to_string() };
    
    // Heterogeneous collection using trait objects
    let animals: Vec<Box<dyn Animal>> = vec![
        Box::new(dog),
        Box::new(cat),
    ];
    
    for animal in &animals {
        interact(animal.as_ref());
    }
}
```

**Flow Chart: Dynamic Dispatch**

```
Runtime:
animal.make_sound()
        │
        ▼
┌───────────────┐
│ Trait Object  │
│  (fat pointer)│
├───────────────┤
│ data ptr  ────┼──▶ Actual object (Dog/Cat)
│ vtable ptr────┼──▶ Virtual table
└───────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   VTable     │
              ├──────────────┤
              │ make_sound() │──▶ Dog::make_sound
              │ name()       │──▶ Dog::name
              │ drop()       │──▶ Dog::drop
              └──────────────┘

Cost: One indirection (vtable lookup)
Benefit: Runtime flexibility
```

### **Detailed Trait Object Rules**

**Object Safety** - A trait can be made into a trait object if:

```
✓ Methods don't have generic type parameters
✓ Methods don't return Self
✓ Trait doesn't use Sized bound

Example - Object Safe:
trait Drawable {
    fn draw(&self);           // ✓
    fn position(&self) -> (i32, i32);  // ✓
}

Example - NOT Object Safe:
trait Cloneable {
    fn clone(&self) -> Self;  // ✗ Returns Self
}

trait Generic {
    fn process<T>(&self, item: T);  // ✗ Generic method
}
```

### **Box<dyn Trait> vs &dyn Trait**

```rust
// Stack allocated reference
fn process_ref(animal: &dyn Animal) {
    animal.make_sound();
}

// Heap allocated, owned
fn process_box(animal: Box<dyn Animal>) {
    animal.make_sound();
    // animal is dropped here
}

// In collections
let animals: Vec<&dyn Animal> = vec![&dog, &cat];  // References
let animals: Vec<Box<dyn Animal>> = vec![Box::new(dog), Box::new(cat)];  // Owned

// Arc for shared ownership across threads
use std::sync::Arc;
let animals: Vec<Arc<dyn Animal>> = vec![Arc::new(dog), Arc::new(cat)];
```

---

## **7. Inheritance-like Patterns** {#7-inheritance-patterns}

Rust doesn't have inheritance, but provides powerful alternatives:

### **Pattern 1: Trait Inheritance (Supertraits)**

```rust
// Base trait
trait Animal {
    fn make_sound(&self) -> &str;
}

// Derived trait - any type implementing Mammal MUST implement Animal
trait Mammal: Animal {
    fn fur_color(&self) -> &str;
    
    // Can call methods from supertrait
    fn describe(&self) {
        println!("This mammal says {} and has {} fur", 
                 self.make_sound(), self.fur_color());
    }
}

struct Dog {
    fur: String,
}

// Must implement both traits
impl Animal for Dog {
    fn make_sound(&self) -> &str {
        "Woof!"
    }
}

impl Mammal for Dog {
    fn fur_color(&self) -> &str {
        &self.fur
    }
}

// Can require Mammal (which implies Animal)
fn pet_mammal<T: Mammal>(animal: &T) {
    animal.describe();
}
```

**Visualization:**

```
Trait Inheritance Hierarchy:

        ┌─────────────┐
        │   Animal    │ (supertrait)
        │  (required) │
        └──────┬──────┘
               │
               │ requires
               │
        ┌──────▼──────┐
        │   Mammal    │ (subtrait)
        │ (+ methods) │
        └──────┬──────┘
               │
               │ implements
               │
        ┌──────▼──────┐
        │     Dog     │
        │  (struct)   │
        └─────────────┘
```

### **Pattern 2: Composition (Preferred)**

```rust
// Reusable components
struct Position {
    x: f64,
    y: f64,
}

struct Velocity {
    dx: f64,
    dy: f64,
}

struct Health {
    current: u32,
    max: u32,
}

// Compose into complex types
struct Player {
    position: Position,
    velocity: Velocity,
    health: Health,
    name: String,
}

struct Enemy {
    position: Position,
    velocity: Velocity,
    health: Health,
    damage: u32,
}

// Shared behavior through traits
trait Movable {
    fn position(&self) -> &Position;
    fn velocity(&self) -> &Velocity;
    
    fn update_position(&mut self, dt: f64) {
        let pos = self.position_mut();
        let vel = self.velocity();
        pos.x += vel.dx * dt;
        pos.y += vel.dy * dt;
    }
    
    fn position_mut(&mut self) -> &mut Position;
    fn velocity_mut(&mut self) -> &mut Velocity;
}

impl Movable for Player {
    fn position(&self) -> &Position { &self.position }
    fn velocity(&self) -> &Velocity { &self.velocity }
    fn position_mut(&mut self) -> &mut Position { &mut self.position }
    fn velocity_mut(&mut self) -> &mut Velocity { &mut self.velocity }
}

impl Movable for Enemy {
    fn position(&self) -> &Position { &self.position }
    fn velocity(&self) -> &Velocity { &self.velocity }
    fn position_mut(&mut self) -> &mut Position { &mut self.position }
    fn velocity_mut(&mut self) -> &mut Velocity { &mut self.velocity }
}
```

### **Pattern 3: Delegated Implementation (Deref)**

```rust
use std::ops::Deref;

// Wrapper type
struct SmartString {
    inner: String,
    access_count: usize,
}

impl SmartString {
    fn new(s: String) -> Self {
        Self { inner: s, access_count: 0 }
    }
}

// Delegate String methods automatically
impl Deref for SmartString {
    type Target = String;
    
    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

// Now SmartString can use all String methods!
fn main() {
    let smart = SmartString::new("Hello".to_string());
    
    // These work via Deref coercion:
    println!("Length: {}", smart.len());  // calls String::len
    println!("Upper: {}", smart.to_uppercase());  // calls String::to_uppercase
}
```

---

## **8. Advanced Trait Patterns** {#8-advanced-traits}

### **Associated Types**

**Concept: Associated Type** - A type placeholder within a trait that implementing types must specify.

```rust
// Instead of generics, use associated types when:
// - There's ONE logical type per implementation
// - You want cleaner syntax

trait Iterator {
    type Item;  // Associated type
    
    fn next(&mut self) -> Option<Self::Item>;
}

// Implementation specifies the associated type
struct Counter {
    count: u32,
    max: u32,
}

impl Iterator for Counter {
    type Item = u32;  // Specify what Item means for Counter
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.count < self.max {
            self.count += 1;
            Some(self.count)
        } else {
            None
        }
    }
}

// Usage is cleaner (no need for Iterator<Item=u32>)
fn process_iter<I: Iterator>(iter: &mut I) 
where
    I::Item: std::fmt::Display,  // Constrain the associated type
{
    while let Some(item) = iter.next() {
        println!("{}", item);
    }
}
```

**Associated Types vs Generic Types:**

```rust
// Generic version (more flexible, but verbose)
trait Container<T> {
    fn add(&mut self, item: T);
    fn get(&self, index: usize) -> Option<&T>;
}

// Can implement multiple times for same type
impl Container<i32> for MyVec { ... }
impl Container<String> for MyVec { ... }

// Associated type version (one implementation per type)
trait Container {
    type Item;
    fn add(&mut self, item: Self::Item);
    fn get(&self, index: usize) -> Option<&Self::Item>;
}

// Only one implementation allowed
impl Container for MyVec {
    type Item = i32;
    ...
}

Decision Tree:
┌─────────────────────────────────┐
│ Will a type have multiple       │
│ implementations of this trait?  │
└────────────┬────────────────────┘
             │
      ┌──────┴──────┐
      │             │
    ┌─▼─┐         ┌─▼─┐
    │YES│         │NO │
    └─┬─┘         └─┬─┘
      │             │
      ▼             ▼
 Use Generic   Use Associated
   <T>            Type
```

### **Default Trait Implementations**

```rust
trait Summarizable {
    fn content(&self) -> &str;
    
    // Default implementation using other trait methods
    fn summary(&self) -> String {
        format!("{}...", &self.content()[..50.min(self.content().len())])
    }
    
    // Another default
    fn full_text(&self) -> &str {
        self.content()
    }
}

struct Article {
    title: String,
    body: String,
}

impl Summarizable for Article {
    fn content(&self) -> &str {
        &self.body
    }
    
    // summary() uses default implementation
    // Can override if needed:
    fn summary(&self) -> String {
        format!("{}: {}", self.title, &self.body[..100.min(self.body.len())])
    }
}
```

### **Blanket Implementations**

**Concept: Blanket Implementation** - Implementing a trait for all types that satisfy certain bounds.

```rust
// Example from standard library:
// ToString is implemented for all types that implement Display

trait MyToString {
    fn my_to_string(&self) -> String;
}

// Blanket implementation: all types with Display get MyToString for free
impl<T: std::fmt::Display> MyToString for T {
    fn my_to_string(&self) -> String {
        format!("{}", self)
    }
}

// Now any type with Display automatically has my_to_string()
fn main() {
    let num = 42;
    println!("{}", num.my_to_string());  // Works!
    
    let s = "hello";
    println!("{}", s.my_to_string());  // Works!
}
```

### **Marker Traits**

**Concept: Marker Trait** - A trait with no methods, used to mark types with certain properties.

```rust
// Standard library examples: Send, Sync, Copy

// Custom marker trait
trait Persistent {}  // Types that can be saved to disk

struct User {
    id: u64,
    name: String,
}

struct TempData {
    cache: Vec<u8>,
}

impl Persistent for User {}
// TempData doesn't implement Persistent

// Use markers in bounds
fn save_to_disk<T: Persistent>(item: &T) {
    // Only types marked Persistent can be saved
    println!("Saving persistent data...");
}

fn main() {
    let user = User { id: 1, name: "Alice".to_string() };
    save_to_disk(&user);  // ✓
    
    let temp = TempData { cache: vec![1, 2, 3] };
    // save_to_disk(&temp);  // ✗ Compile error: TempData doesn't implement Persistent
}
```

---

## **9. Real-World Design Patterns** {#9-design-patterns}

### **Strategy Pattern**

```rust
// Define strategy trait
trait SortStrategy {
    fn sort(&self, data: &mut [i32]);
}

// Concrete strategies
struct BubbleSort;
struct QuickSort;
struct MergeSort;

impl SortStrategy for BubbleSort {
    fn sort(&self, data: &mut [i32]) {
        let n = data.len();
        for i in 0..n {
            for j in 0..n - i - 1 {
                if data[j] > data[j + 1] {
                    data.swap(j, j + 1);
                }
            }
        }
    }
}

impl SortStrategy for QuickSort {
    fn sort(&self, data: &mut [i32]) {
        // QuickSort implementation
        if data.len() <= 1 {
            return;
        }
        // ... (simplified for brevity)
    }
}

// Context that uses strategies
struct Sorter {
    strategy: Box<dyn SortStrategy>,
}

impl Sorter {
    fn new(strategy: Box<dyn SortStrategy>) -> Self {
        Self { strategy }
    }
    
    fn set_strategy(&mut self, strategy: Box<dyn SortStrategy>) {
        self.strategy = strategy;
    }
    
    fn sort(&self, data: &mut [i32]) {
        self.strategy.sort(data);
    }
}

fn main() {
    let mut data = vec![5, 2, 8, 1, 9];
    
    let mut sorter = Sorter::new(Box::new(BubbleSort));
    sorter.sort(&mut data);
    
    // Change strategy at runtime
    sorter.set_strategy(Box::new(QuickSort));
    sorter.sort(&mut data);
}
```

### **Builder Pattern**

```rust
#[derive(Debug, Default)]
struct HttpRequest {
    method: String,
    url: String,
    headers: Vec<(String, String)>,
    body: Option<String>,
}

struct HttpRequestBuilder {
    request: HttpRequest,
}

impl HttpRequestBuilder {
    fn new() -> Self {
        Self {
            request: HttpRequest::default(),
        }
    }
    
    fn method(mut self, method: &str) -> Self {
        self.request.method = method.to_string();
        self
    }
    
    fn url(mut self, url: &str) -> Self {
        self.request.url = url.to_string();
        self
    }
    
    fn header(mut self, key: &str, value: &str) -> Self {
        self.request.headers.push((key.to_string(), value.to_string()));
        self
    }
    
    fn body(mut self, body: &str) -> Self {
        self.request.body = Some(body.to_string());
        self
    }
    
    fn build(self) -> HttpRequest {
        self.request
    }
}

fn main() {
    let request = HttpRequestBuilder::new()
        .method("POST")
        .url("https://api.example.com/users")
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer token123")
        .body(r#"{"name": "Alice"}"#)
        .build();
    
    println!("{:?}", request);
}
```

### **Type State Pattern** (Advanced)

**Concept: Type State** - Use the type system to enforce state transitions at compile time.

```rust
// Different states as types
struct Locked;
struct Unlocked;

// Door with type parameter tracking state
struct Door<State> {
    state: std::marker::PhantomData<State>,
}

impl Door<Locked> {
    fn new() -> Self {
        println!("Door created in locked state");
        Door { state: std::marker::PhantomData }
    }
    
    // Only locked doors can be unlocked
    fn unlock(self) -> Door<Unlocked> {
        println!("Door unlocked");
        Door { state: std::marker::PhantomData }
    }
}

impl Door<Unlocked> {
    // Only unlocked doors can be opened
    fn open(&self) {
        println!("Door opened");
    }
    
    // Only unlocked doors can be locked
    fn lock(self) -> Door<Locked> {
        println!("Door locked");
        Door { state: std::marker::PhantomData }
    }
}

fn main() {
    let door = Door::<Locked>::new();
    // door.open();  // ✗ Compile error: method not available for Door<Locked>
    
    let door = door.unlock();
    door.open();  // ✓
    
    let door = door.lock();
    // door.open();  // ✗ Compile error again
}
```

**Flow Visualization:**

```
Type State Pattern Flow:

Door<Locked>
     │
     │ .unlock()
     ▼
Door<Unlocked>
     │
     │ .open()  ✓
     │
     │ .lock()
     ▼
Door<Locked>

Compile-time enforcement:
┌──────────────────────────────┐
│ Door<Locked>.open()    ✗     │
│ Door<Unlocked>.open()  ✓     │
│ Door<Locked>.unlock()  ✓     │
│ Door<Unlocked>.unlock() ✗    │
└──────────────────────────────┘
```

---

## **10. Performance Implications** {#10-performance}

### **Memory Layout**

```rust
// Struct layout
struct Point {
    x: f64,  // 8 bytes
    y: f64,  // 8 bytes
}  // Total: 16 bytes, aligned

// Trait object layout
let p: Box<dyn Drawable> = Box::new(circle);
// Fat pointer: 16 bytes (2 * usize)
//   - 8 bytes: pointer to data
//   - 8 bytes: pointer to vtable

println!("Size of Point: {}", std::mem::size_of::<Point>());
println!("Size of &dyn Drawable: {}", std::mem::size_of::<&dyn Drawable>());
```

### **Dispatch Cost Comparison**

```
Static Dispatch (Monomorphization):
┌─────────────────────────────────┐
│ Source Code:                    │
│ fn process<T: Trait>(x: &T)     │
└────────────┬────────────────────┘
             │ Compiler
             ▼
┌─────────────────────────────────┐
│ Machine Code:                   │
│ process_TypeA(x: &TypeA)        │
│ process_TypeB(x: &TypeB)        │
│                                 │
│ Direct calls, inlined           │
│ Performance: ★★★★★              │
│ Code size: Larger               │
└─────────────────────────────────┘

Dynamic Dispatch (Trait Objects):
┌─────────────────────────────────┐
│ Source Code:                    │
│ fn process(x: &dyn Trait)       │
└────────────┬────────────────────┘
             │ Compiler
             ▼
┌─────────────────────────────────┐
│ Machine Code:                   │
│ process(x: fat_pointer)         │
│   vtable_lookup()               │
│   indirect_call()               │
│                                 │
│ Indirect calls, not inlined     │
│ Performance: ★★★★☆              │
│ Code size: Smaller              │
└─────────────────────────────────┘
```

### **Benchmark Example**

```rust
use std::time::Instant;

trait Calculator {
    fn calculate(&self, a: i64, b: i64) -> i64;
}

struct Adder;
impl Calculator for Adder {
    fn calculate(&self, a: i64, b: i64) -> i64 {
        a + b
    }
}

// Static dispatch
fn benchmark_static<T: Calculator>(calc: &T, iterations: usize) {
    let start = Instant::now();
    let mut sum = 0i64;
    for i in 0..iterations {
        sum += calc.calculate(i as i64, (i + 1) as i64);
    }
    println!("Static dispatch: {:?}, sum: {}", start.elapsed(), sum);
}

// Dynamic dispatch
fn benchmark_dynamic(calc: &dyn Calculator, iterations: usize) {
    let start = Instant::now();
    let mut sum = 0i64;
    for i in 0..iterations {
        sum += calc.calculate(i as i64, (i + 1) as i64);
    }
    println!("Dynamic dispatch: {:?}, sum: {}", start.elapsed(), sum);
}

fn main() {
    let adder = Adder;
    let iterations = 100_000_000;
    
    benchmark_static(&adder, iterations);
    benchmark_dynamic(&adder, iterations);
}

// Typical results:
// Static dispatch: ~80ms
// Dynamic dispatch: ~120ms (30-50% slower for simple operations)
```

### **When to Use Each**

```
Use Static Dispatch When:
✓ Performance is critical
✓ Types known at compile time
✓ Small number of implementations
✓ Can afford larger binary size

Use Dynamic Dispatch When:
✓ Need runtime polymorphism
✓ Collections of heterogeneous types
✓ Plugin systems
✓ Many implementations (reduce code bloat)
✓ Indirect cost is acceptable
```

---

## **Summary: OOP in Rust - Key Insights**

```
┌────────────────────────────────────────────────────┐
│              OOP Feature Mapping                   │
├────────────────────────────────────────────────────┤
│ Encapsulation  → pub/private modifiers            │
│ Polymorphism   → Traits + Generics/Trait Objects  │
│ Inheritance    → Composition + Trait bounds        │
│ Interfaces     → Traits                            │
│ Abstract Class → Trait with default methods       │
└────────────────────────────────────────────────────┘
```

**Mental Models to Master:**

1. **Ownership-First Design**: Types own their data; traits define shared behavior
2. **Composition Over Inheritance**: Build complex types from simple ones
3. **Zero-Cost Abstractions**: High-level code compiles to efficient machine code
4. **Explicit Over Implicit**: Rust makes you choose dispatch type explicitly

**Practice Path** (Monk's Journey):

```
Week 1: Master structs, methods, basic traits
Week 2: Generic functions, trait bounds
Week 3: Trait objects, dynamic dispatch
Week 4: Advanced patterns (associated types, blanket impls)
Week 5-6: Build real project using all concepts
```

---

Would you like me to:
1. **Dive deeper** into any specific topic (e.g., advanced trait patterns, performance optimization)?
2. **Provide exercises** with detailed solutions for each concept?
3. **Compare** Rust's approach with C++/Python/Go implementations?
4. **Explore** specific design patterns (Command, Observer, Factory, etc.)?

Your mastery journey awaits! 🔥