// ============================================================================
// COMPREHENSIVE GUIDE TO 'self' KEYWORD IN RUST
// ============================================================================

// TABLE OF CONTENTS:
// 1. Basic Understanding: self vs Self
// 2. Method Receivers: Different Forms of self
// 3. Without self - Associated Functions
// 4. Common Errors and Warnings
// 5. Correct vs Incorrect Usage
// 6. Benefits and Control
// 7. Advanced Patterns

// ============================================================================
// 1. BASIC UNDERSTANDING: self vs Self
// ============================================================================

// 'Self' (capital S) - Type alias for the implementing type
// 'self' (lowercase s) - Instance of the type

struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // 'Self' refers to the Rectangle type itself
    fn new(width: u32, height: u32) -> Self {  // Self = Rectangle
        Self { width, height }  // Same as Rectangle { width, height }
    }
    
    // 'self' refers to the instance
    fn area(&self) -> u32 {
        self.width * self.height
    }
}

// ============================================================================
// 2. METHOD RECEIVERS: Different Forms of self
// ============================================================================

#[derive(Debug, Clone)]
struct Point {
    x: i32,
    y: i32,
}

impl Point {
    // A) &self - Immutable borrow (most common)
    // Use when: Reading data without modifying
    fn display(&self) {
        println!("Point({}, {})", self.x, self.y);
    }
    
    fn distance_from_origin(&self) -> f64 {
        ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
    }
    
    // B) &mut self - Mutable borrow
    // Use when: Modifying the instance
    fn translate(&mut self, dx: i32, dy: i32) {
        self.x += dx;
        self.y += dy;
    }
    
    fn reset(&mut self) {
        self.x = 0;
        self.y = 0;
    }
    
    // C) self - Takes ownership (consumes the value)
    // Use when: Transforming into something else or preventing further use
    fn into_tuple(self) -> (i32, i32) {
        (self.x, self.y)  // Point is consumed here
    }
    
    fn consume_and_print(self) {
        println!("Consuming point: {:?}", self);
        // self is dropped here, can't be used after this method
    }
    
    // D) Self - Return type (not a receiver)
    fn origin() -> Self {
        Self { x: 0, y: 0 }
    }
}

// ============================================================================
// 3. WITHOUT self - ASSOCIATED FUNCTIONS
// ============================================================================

struct Counter {
    count: u32,
}

impl Counter {
    // Associated function (no self) - like static methods in other languages
    // Called using Counter::new(), not instance.new()
    fn new() -> Self {
        Self { count: 0 }
    }
    
    fn with_initial(count: u32) -> Self {
        Self { count }
    }
    
    // Method (has self) - called on instances
    fn increment(&mut self) {
        self.count += 1;
    }
    
    fn get_count(&self) -> u32 {
        self.count
    }
}

// ============================================================================
// 4. COMMON ERRORS AND WARNINGS
// ============================================================================

struct ErrorExamples {
    value: i32,
}

impl ErrorExamples {
    // ERROR 1: Trying to use self in associated function
    /*
    fn bad_constructor() -> Self {
        self.value = 10;  // ERROR: `self` value is not available
        Self { value: 0 }
    }
    */
    
    // ERROR 2: Moving out of borrowed content
    /*
    fn bad_getter(&self) -> i32 {
        self.value  // This is OK
    }
    
    fn bad_move(&self) -> Self {
        *self  // ERROR: cannot move out of `*self` which is behind a shared reference
    }
    */
    
    // ERROR 3: Modifying through immutable reference
    /*
    fn bad_modify(&self) {
        self.value += 1;  // ERROR: cannot assign to `self.value` as `self` is not mutable
    }
    */
    
    // CORRECT: Proper signatures
    fn correct_modify(&mut self) {
        self.value += 1;  // OK with &mut self
    }
    
    fn correct_move(self) -> Self {
        self  // OK when consuming self
    }
}

// ============================================================================
// 5. CORRECT vs INCORRECT USAGE
// ============================================================================

#[derive(Debug, Clone)]
struct BankAccount {
    balance: f64,
    account_id: String,
}

impl BankAccount {
    // ✅ CORRECT: Constructor without self
    fn new(account_id: String) -> Self {
        Self {
            balance: 0.0,
            account_id,
        }
    }
    
    // ✅ CORRECT: Read-only method with &self
    fn get_balance(&self) -> f64 {
        self.balance
    }
    
    // ✅ CORRECT: Modifying method with &mut self
    fn deposit(&mut self, amount: f64) {
        if amount > 0.0 {
            self.balance += amount;
        }
    }
    
    // ✅ CORRECT: Consuming method with self
    fn close_account(self) -> String {
        println!("Closing account {} with balance: {}", self.account_id, self.balance);
        self.account_id
    }
    
    // ❌ INCORRECT: Should use &self instead of self for read-only
    /*
    fn bad_get_balance(self) -> f64 {
        self.balance  // This consumes the account!
    }
    */
    
    // ❌ INCORRECT: Should use &mut self instead of &self
    /*
    fn bad_deposit(&self, amount: f64) {
        self.balance += amount;  // ERROR: cannot mutate
    }
    */
}

// ============================================================================
// 6. BENEFITS AND CONTROL
// ============================================================================

// BENEFIT 1: Memory Safety - Compile-time borrow checking
struct SafeExample {
    data: Vec<i32>,
}

impl SafeExample {
    fn new() -> Self {
        Self { data: vec![1, 2, 3] }
    }
    
    // With &self: Multiple simultaneous reads are safe
    fn read_data(&self) -> &[i32] {
        &self.data
    }
    
    // With &mut self: Exclusive access for modification
    fn modify_data(&mut self) {
        self.data.push(4);
    }
    
    // With self: Prevents use-after-move bugs
    fn consume(self) -> Vec<i32> {
        self.data
    }
}

// BENEFIT 2: Clear Ownership Semantics
struct OwnershipExample {
    resource: String,
}

impl OwnershipExample {
    // Method signature tells you everything about ownership
    
    fn borrow(&self) -> &str {  // Borrows, returns borrowed data
        &self.resource
    }
    
    fn borrow_mut(&mut self) -> &mut String {  // Mutable borrow
        &mut self.resource
    }
    
    fn take_ownership(self) -> String {  // Consumes self
        self.resource
    }
}

// ============================================================================
// 7. ADVANCED PATTERNS
// ============================================================================

// Builder Pattern with self
struct HttpRequest {
    url: String,
    method: String,
    headers: Vec<(String, String)>,
}

impl HttpRequest {
    fn new(url: String) -> Self {
        Self {
            url,
            method: "GET".to_string(),
            headers: Vec::new(),
        }
    }
    
    // Method chaining: consumes self and returns Self
    fn method(mut self, method: String) -> Self {
        self.method = method;
        self
    }
    
    fn header(mut self, key: String, value: String) -> Self {
        self.headers.push((key, value));
        self
    }
    
    fn send(self) {
        println!("Sending {} request to {}", self.method, self.url);
        for (key, value) in self.headers {
            println!("  {}: {}", key, value);
        }
    }
}

// Smart pointers and custom self types
use std::rc::Rc;
use std::sync::Arc;

struct Node {
    value: i32,
}

impl Node {
    // Can use different smart pointer types as self
    fn new(value: i32) -> Rc<Self> {
        Rc::new(Self { value })
    }
    
    // Method taking Rc<Self>
    fn shared_method(self: Rc<Self>) -> i32 {
        self.value
    }
    
    // Method with Arc<Self> for thread-safe sharing
    fn thread_safe_method(self: Arc<Self>) -> i32 {
        self.value
    }
}

// ============================================================================
// COMPARISON EXAMPLES
// ============================================================================

fn demonstrate_differences() {
    println!("=== Demonstrating self usage ===\n");
    
    // Point examples
    let mut point = Point { x: 5, y: 10 };
    point.display();  // &self - just borrows
    point.translate(3, 4);  // &mut self - mutable borrow
    point.display();  // Can still use point
    
    let tuple = point.into_tuple();  // self - consumes point
    println!("Tuple: {:?}", tuple);
    // point.display();  // ERROR: point was moved
    
    println!();
    
    // Counter examples
    let mut counter = Counter::new();  // Associated function
    counter.increment();  // Method
    println!("Count: {}", counter.get_count());
    
    println!();
    
    // Builder pattern
    HttpRequest::new("https://api.example.com".to_string())
        .method("POST".to_string())
        .header("Content-Type".to_string(), "application/json".to_string())
        .header("Authorization".to_string(), "Bearer token".to_string())
        .send();
    
    println!();
    
    // BankAccount example showing ownership
    let mut account = BankAccount::new("ACC123".to_string());
    account.deposit(100.0);
    println!("Balance: {}", account.get_balance());  // &self
    let id = account.close_account();  // self - consumes
    println!("Closed account: {}", id);
    // account.get_balance();  // ERROR: account was moved
}

// ============================================================================
// KEY TAKEAWAYS
// ============================================================================

/*
SUMMARY:

1. SELF (capital) vs self (lowercase):
   - Self = Type alias for the implementing type
   - self = Instance of the type

2. THREE FORMS OF self RECEIVER:
   - &self      → Immutable borrow (read-only)
   - &mut self  → Mutable borrow (can modify)
   - self       → Takes ownership (consumes)

3. NO self (Associated Functions):
   - Used for constructors and utility functions
   - Called on type: Type::function()
   - Not called on instance

4. BENEFITS:
   - Compile-time memory safety
   - Clear ownership semantics
   - Prevents use-after-free bugs
   - Enables zero-cost abstractions

5. COMMON PATTERNS:
   - new() → Associated function returning Self
   - getters → Use &self
   - setters → Use &mut self
   - builders → Use self for chaining
   - converters → Use self when consuming

6. WARNINGS TO AVOID:
   - Don't use self when you need &self (unnecessary moves)
   - Don't use &self when you need &mut self (won't compile)
   - Don't use self in associated functions (no instance exists)
   - Don't forget to use &self/&mut self when you need instance data
*/

fn main() {
    demonstrate_differences();
}

I'll create a comprehensive guide to the `self` keyword in Rust, covering all its aspects with complete implementations.

I've created a comprehensive guide covering all aspects of the `self` keyword in Rust. Here's what's included:

## **Key Sections:**

1. **Self vs self** - Understanding the difference between the type alias (Self) and instance (self)

2. **Method Receivers** - Four forms:
   - `&self` - immutable borrow (read-only)
   - `&mut self` - mutable borrow (modify)
   - `self` - takes ownership (consumes)
   - `Self` - return type

3. **Associated Functions** - Functions without `self` (like static methods)

4. **Common Errors** - Real examples of what goes wrong:
   - Using self in associated functions
   - Moving out of borrowed content
   - Modifying through immutable references

5. **Correct vs Incorrect Usage** - Side-by-side comparisons with explanations

6. **Benefits** - Why this system matters:
   - Compile-time memory safety
   - Clear ownership semantics
   - Prevention of use-after-free bugs

7. **Advanced Patterns** - Builder pattern and smart pointer usage

## **Control & Benefits:**

**With `self`:**
- Compiler enforces memory safety at compile time
- Clear API contracts (signature tells you everything)
- Zero runtime overhead
- Prevents entire classes of bugs

**Without `self` (Associated Functions):**
- Constructors and factory methods
- Utility functions that don't need instance data
- Type-level operations

The guide includes complete, runnable examples demonstrating every concept. You can copy and run it in your Rust environment to see all the patterns in action!

Great question, Sushin! You're touching on a core concept in object-oriented programming, and it applies slightly differently depending on the language you're working with. Since you've been exploring both Python and Rust, I’ll explain how `self` works in **Python**, and then contrast it with **Rust**, where the concept is similar but the syntax and semantics differ.

---

## 🐍 Python: `self` in Class Methods

In Python, `self` is **not a keyword**, but a **convention** used to refer to the instance of the class on which a method is called.

### 🔧 How it works:
- When you define a method inside a class, the first parameter is typically named `self`.
- This parameter gives access to the instance’s attributes and other methods.

### 📦 Example:
```python
class Car:
    def __init__(self, brand):
        self.brand = brand  # 'self' refers to the instance

    def honk(self):
        print(f"{self.brand} goes honk!")

my_car = Car("Rolls-Royce")
my_car.honk()  # Internally calls Car.honk(my_car)
```

### 🧠 Behind the scenes:
When you call `my_car.honk()`, Python translates it to:
```python
Car.honk(my_car)
```
So `self` is just a reference to `my_car`.

---

## 🦀 Rust: `self` in Struct Methods

Rust uses a similar concept, but it's more explicit and type-safe.

### 🔧 How it works:
- Methods are defined using `impl` blocks.
- The first parameter can be `self`, `&self`, or `&mut self`, depending on how you want to access the instance.

### 📦 Example:
```rust
struct Car {
    brand: String,
}

impl Car {
    fn honk(&self) {
        println!("{} goes honk!", self.brand);
    }
}
```

### 🧠 Behind the scenes:
- `&self` means you're borrowing the instance immutably.
- `self` means you're taking ownership.
- `&mut self` means you're borrowing it mutably.

When you call:
```rust
let my_car = Car { brand: String::from("Rolls-Royce") };
my_car.honk();  // Rust automatically passes &my_car as self
```

Rust uses **method syntax sugar** to automatically pass the instance as the first argument.

---

## 🧩 Summary Table

| Language | Keyword | Meaning of `self` | Passed Automatically? |
|----------|---------|-------------------|------------------------|
| Python   | `self`  | Reference to instance | ✅ Yes |
| Rust     | `self`, `&self`, `&mut self` | Ownership or borrow of instance | ✅ Yes |

---

Want to dive deeper into how method dispatch works under the hood in either language? Or maybe explore how `self` behaves in traits in Rust?

You're on the right track, Sushin! Let's break this down precisely so you can see **how memory and references work in Rust** when calling a method like `my_car.honk()`.

---

## 🧠 What Happens in Memory

When you write:
```rust
let my_car = Car { brand: String::from("Rolls-Royce") };
```

### 🔹 Step 1: Struct Allocation
- `my_car` is a variable of type `Car`.
- Inside it, `brand` is a `String`, which is a **heap-allocated** type in Rust.
- So:
  - `my_car` lives on the **stack**.
  - `my_car.brand` points to a **heap** location where `"Rolls-Royce"` is stored.

### 🔹 Step 2: Method Call
```rust
my_car.honk();
```
- Rust desugars this to:
```rust
Car::honk(&my_car);
```
- The method `honk(&self)` receives a **shared reference** (`&Car`) to `my_car`.

---

## 🔍 Inside the Method

```rust
fn honk(&self) {
    println!("{} goes honk!", self.brand);
}
```

- `self` is a reference to the entire `Car` struct.
- `self.brand` accesses the `brand` field.
- Since `self` is `&Car`, `self.brand` is of type `&String`.
- The `String` itself holds:
  - A pointer to the heap where `"Rolls-Royce"` is stored.
  - The length and capacity of the string.

So yes—**ultimately, you're referencing the heap memory** where `"Rolls-Royce"` is stored, but you're doing it through a chain:
```
&Car → &String → heap memory
```

---

## 🧩 Visual Breakdown

```text
Stack:
┌────────────┐
│ my_car     │ ──┐
│ brand:     │   │
│  String    │   │
└────────────┘   │
                 ▼
Heap:
┌────────────────────────────┐
│ "Rolls-Royce"              │
└────────────────────────────┘
```

---

Would you like to explore how this changes if you use `self` instead of `&self`, or how ownership and borrowing rules affect method design in Rust?

Got it, Sushin—I'll remember that you want **visual breakdowns** whenever I explain something. That’s now part of how I’ll tailor responses for you. ✅

Now let’s dive into your question:

---

## 🔗 What Is a Shared Reference in Rust?

In Rust, a **shared reference** means multiple parts of your code can **read** the same data **without owning or modifying it**.

### 🧠 Syntax:
```rust
&T  // Shared reference to a value of type T
```

- You can **read** from `&T`.
- You **cannot modify** `T` through `&T`.
- Multiple `&T` references can exist at the same time.

---

## 🧩 Visual Breakdown

Let’s say you have this:

```rust
let name = String::from("Sushin");
let ref1 = &name;
let ref2 = &name;
```

Here’s how memory looks:

```text
Stack:
┌────────────┐
│ name       │ ──┐
│ String     │   │
└────────────┘   │
                 ▼
Heap:
┌────────────────────────────┐
│ "Sushin"                   │
└────────────────────────────┘
       ▲         ▲
       │         │
┌──────┴───┐ ┌────┴────┐
│ ref1     │ │ ref2    │
│ &String  │ │ &String │
└──────────┘ └─────────┘
```

- `name` owns the string `"Sushin"` on the heap.
- `ref1` and `ref2` are **shared references** to `name`.
- Both can **read** the data, but **neither can change it**.

---

## 🔒 Why Use Shared References?

- They’re **safe**: Rust guarantees no data races.
- They’re **efficient**: You avoid copying large data.
- They’re **flexible**: You can pass data around without giving up ownership.

---

Would you like a breakdown of **mutable references** next, or maybe how Rust enforces borrowing rules at compile time?
