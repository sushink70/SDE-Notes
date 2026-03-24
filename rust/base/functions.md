# 🦀 Rust Functions — Comprehensive Master Guide
> *"The function is the atom of thought. Master it and you master the universe of computation."*

---

## Table of Contents

1. [What is a Function? (First Principles)](#1-what-is-a-function)
2. [Basic Syntax & Anatomy](#2-basic-syntax--anatomy)
3. [Parameters & Arguments](#3-parameters--arguments)
4. [Return Types & the `->` Operator](#4-return-types--the---operator)
5. [Expressions vs Statements — Rust's Core Distinction](#5-expressions-vs-statements)
6. [Multiple Return Values via Tuples](#6-multiple-return-values-via-tuples)
7. [The Unit Type `()`](#7-the-unit-type-)
8. [Diverging Functions with `!`](#8-diverging-functions-with-)
9. [Nested Functions](#9-nested-functions)
10. [Function Pointers](#10-function-pointers)
11. [Closures — Anonymous Functions](#11-closures--anonymous-functions)
12. [Higher-Order Functions (HOF)](#12-higher-order-functions)
13. [Iterator Adapters & Functional Pipelines](#13-iterator-adapters--functional-pipelines)
14. [Generic Functions](#14-generic-functions)
15. [Trait Bounds on Functions](#15-trait-bounds-on-functions)
16. [Lifetime Parameters in Functions](#16-lifetime-parameters-in-functions)
17. [Methods & Associated Functions (`impl` blocks)](#17-methods--associated-functions)
18. [`const fn` — Compile-Time Functions](#18-const-fn--compile-time-functions)
19. [`async fn` — Asynchronous Functions](#19-async-fn--asynchronous-functions)
20. [`unsafe fn` — Unsafe Functions](#20-unsafe-fn--unsafe-functions)
21. [Extern Functions & FFI](#21-extern-functions--ffi)
22. [Pattern Matching in Parameters](#22-pattern-matching-in-parameters)
23. [Recursion & Tail Calls](#23-recursion--tail-calls)
24. [Function Dispatch — Static vs Dynamic](#24-function-dispatch--static-vs-dynamic)
25. [Monomorphization & Zero-Cost Abstractions](#25-monomorphization--zero-cost-abstractions)
26. [Error Handling in Functions](#26-error-handling-in-functions)
27. [Advanced Closure Patterns](#27-advanced-closure-patterns)
28. [Variadic-Like Patterns in Rust](#28-variadic-like-patterns-in-rust)
29. [Performance Mental Models](#29-performance-mental-models)
30. [DSA Patterns Using Functions](#30-dsa-patterns-using-functions)

---

## 1. What is a Function?

### First Principles

A **function** is a named, reusable block of computation that:
- Accepts zero or more **inputs** (parameters)
- Performs a sequence of **operations**
- Returns an **output** (or nothing — the unit type `()`)

Mathematically, a function `f: A → B` maps every element from domain `A` to exactly one element in codomain `B`.

In Rust, functions are **first-class citizens** — they can be:
- Passed as arguments
- Returned from other functions
- Stored in variables
- Stored in data structures

### Mental Model: The Black Box

```
          ┌─────────────────────────┐
Input(s)  │                         │  Output
─────────►│     FUNCTION (fn)       │─────────►
(params)  │   named computation     │  (return value)
          └─────────────────────────┘
```

### Why Functions Matter in DSA

| Concern             | How Functions Help                          |
|---------------------|---------------------------------------------|
| **Abstraction**     | Hide complexity behind a clean interface    |
| **Reuse**           | Sort once, call everywhere                  |
| **Testability**     | Isolated input/output = easy to verify      |
| **Recursion**       | Functions calling themselves = elegant DSA  |
| **HOF patterns**    | `map`, `filter`, `fold` = expressive DSA    |

---

## 2. Basic Syntax & Anatomy

### The `fn` Keyword

```
fn  function_name  ( parameter_list )  -> return_type  { body }
▲        ▲                ▲                   ▲            ▲
│        │                │                   │            │
keyword  name          inputs             output type    statements
```

### Simplest Function

```rust
fn greet() {
    println!("Hello, World!");
}

fn main() {
    greet(); // call the function
}
```

### ASCII Anatomy Breakdown

```
fn add(x: i32, y: i32) -> i32 {
│  │   │  │    │  │      │  │   │
│  │   │  │    │  │      │  │   └── body (block expression)
│  │   │  │    │  │      │  └────── return type
│  │   │  │    │  │      └───────── return arrow (->)
│  │   │  │    │  └──────────────── type annotation for y
│  │   │  │    └─────────────────── second parameter
│  │   │  └──────────────────────── type annotation for x
│  │   └─────────────────────────── first parameter
│  └─────────────────────────────── function name
└────────────────────────────────── fn keyword
    x + y    ← implicit return (no semicolon!)
}
```

### Full Example with All Parts Labeled

```rust
fn multiply(a: i64, b: i64) -> i64 {  // signature
    let product = a * b;               // statement (binding)
    product                            // expression (implicit return)
}
```

### Naming Conventions

| Convention    | Usage                          | Example               |
|---------------|--------------------------------|-----------------------|
| `snake_case`  | Functions, variables           | `fn binary_search()`  |
| `SCREAMING`   | Constants                      | `const MAX_SIZE: i32` |
| `CamelCase`   | Types, Structs, Enums          | `struct BinaryTree`   |

---

## 3. Parameters & Arguments

> **Key Distinction:**
> - **Parameter** = the variable declared in the function signature
> - **Argument** = the actual value passed when calling the function

```rust
fn square(n: i32) -> i32 {  // `n` is a PARAMETER
    n * n
}

fn main() {
    let result = square(5);  // `5` is an ARGUMENT
    println!("{}", result);  // prints 25
}
```

### Type Annotations Are Mandatory

Unlike Python, Rust **requires explicit type annotations** on every parameter. This is intentional — it enables:
1. **Zero-cost abstractions** (compiler knows sizes at compile time)
2. **Type safety** (no silent coercions)
3. **Better error messages**

```rust
// ✅ Correct — every parameter has a type
fn add(x: i32, y: i32) -> i32 {
    x + y
}

// ❌ Compile error — missing types
// fn add(x, y) { x + y }
```

### Multiple Parameters

```rust
fn describe_point(x: f64, y: f64, label: &str) {
    println!("Point '{}' is at ({}, {})", label, x, y);
}

fn main() {
    describe_point(3.0, 4.5, "Origin offset");
}
```

### Passing by Value vs by Reference

This is one of Rust's most critical distinctions. It connects directly to ownership.

#### By Value (moves or copies ownership)

```rust
fn consume(s: String) {  // s is MOVED into the function
    println!("Consumed: {}", s);
}   // s is dropped here

fn main() {
    let name = String::from("Alice");
    consume(name);
    // println!("{}", name); // ❌ ERROR: name was moved
}
```

#### By Immutable Reference (borrow, read-only)

```rust
fn print_len(s: &String) {  // borrow s, don't take ownership
    println!("Length: {}", s.len());
}

fn main() {
    let name = String::from("Alice");
    print_len(&name);
    println!("{}", name);  // ✅ name still usable
}
```

#### By Mutable Reference (borrow, can mutate)

```rust
fn double_values(v: &mut Vec<i32>) {
    for x in v.iter_mut() {
        *x *= 2;  // dereference with * to mutate
    }
}

fn main() {
    let mut nums = vec![1, 2, 3, 4];
    double_values(&mut nums);
    println!("{:?}", nums);  // [2, 4, 6, 8]
}
```

### Ownership Flow Diagram

```
Pass by Value            Pass by &ref             Pass by &mut ref
─────────────────        ─────────────────        ──────────────────
   caller                    caller                   caller
   [owns data]               [owns data]              [owns data]
       │                         │                        │
       │ move                    │ borrow                 │ mut borrow
       ▼                         ▼                        ▼
   function                  function                 function
   [takes ownership]         [can read only]          [can read+write]
   [drops on return]         [returns borrow]         [returns borrow]
                             [caller still owns]      [caller still owns]
```

### Copy Types vs Move Types

| Category        | Examples                          | Behavior      |
|-----------------|-----------------------------------|---------------|
| **Copy types**  | `i32`, `f64`, `bool`, `char`, `&T`| Copied silently|
| **Move types**  | `String`, `Vec<T>`, `Box<T>`      | Moved (not copied)|

```rust
fn increment(n: i32) -> i32 {  // i32 is Copy — n is duplicated
    n + 1
}

fn main() {
    let x = 10;
    let y = increment(x);
    println!("x={}, y={}", x, y);  // ✅ x still usable — it was copied
}
```

---

## 4. Return Types & the `->` Operator

### Syntax

```rust
fn function_name(params) -> ReturnType {
    // ...
    value  // last expression = return value (NO semicolon)
}
```

### Implicit vs Explicit Return

Rust favors **implicit return** — the last expression in a block becomes the return value automatically. This is idiomatic Rust.

```rust
// Idiomatic (implicit return)
fn cube(n: i32) -> i32 {
    n * n * n   // no semicolon → this is the return value
}

// Also valid (explicit return keyword)
fn cube_explicit(n: i32) -> i32 {
    return n * n * n;  // semicolon here is fine
}
```

### When to Use `return` Explicitly

Use `return` for **early exits** — analogous to `break` in loops:

```rust
fn find_first_negative(nums: &[i32]) -> Option<i32> {
    for &n in nums {
        if n < 0 {
            return Some(n);  // early exit
        }
    }
    None  // implicit return if no negative found
}
```

### Decision Tree: Semicolon or Not?

```
Is this the LAST expression in the function body?
    │
    ├── YES → Do you want it to be the return value?
    │              ├── YES → NO semicolon  ✅ (expression)
    │              └── NO  → ADD semicolon ✅ (becomes statement, returns ())
    │
    └── NO  → ADD semicolon (it's a statement, discards value)
```

```rust
fn demo() -> i32 {
    let a = 5;         // statement — semicolon required
    let b = 10;        // statement — semicolon required
    a + b              // expression — NO semicolon = return value
}
```

### Common Mistake: Accidental Semicolon

```rust
// ❌ Bug: semicolon converts expression to statement → returns ()
fn bad_add(x: i32, y: i32) -> i32 {
    x + y;  // WRONG: semicolon discards the value, returns ()
}           // Compiler error: expected i32, found ()

// ✅ Correct:
fn good_add(x: i32, y: i32) -> i32 {
    x + y   // No semicolon
}
```

---

## 5. Expressions vs Statements

This is **the most important conceptual distinction** in Rust — it governs return values, blocks, closures, and everything else.

### Definitions

| Term           | Definition                                  | Has a Value? |
|----------------|---------------------------------------------|--------------|
| **Expression** | Evaluates to a value                        | ✅ Yes        |
| **Statement**  | Performs an action, discards any value      | ❌ No         |

### Everything in Rust is (mostly) an Expression

```rust
fn main() {
    // if is an EXPRESSION — it returns a value
    let x = if true { 42 } else { 0 };
    println!("{}", x);  // 42

    // Block {} is an EXPRESSION
    let y = {
        let a = 10;
        let b = 20;
        a + b   // last expression = block's value
    };
    println!("{}", y);  // 30

    // match is an EXPRESSION
    let grade = 85;
    let letter = match grade {
        90..=100 => 'A',
        80..=89  => 'B',
        70..=79  => 'C',
        _        => 'F',
    };
    println!("{}", letter);  // B
}
```

### Expression vs Statement Visual

```
Expressions (have value, can be used):       Statements (no value):
─────────────────────────────────────        ──────────────────────
  5 + 3           → 8                          let x = 5;
  "hello"         → &str                       fn foo() {}
  if cond {..}    → value of branch            use std::io;
  { ... }         → last expr's value          loop { break; }
  func_call()     → return value
  match x { ... } → matched arm value
```

---

## 6. Multiple Return Values via Tuples

Rust does not support multiple return values natively like Go, but **tuples** achieve the same goal perfectly.

### What is a Tuple?

A **tuple** is a fixed-size, heterogeneous (different types allowed) ordered collection.

```
(value1, value2, value3)
   │        │       │
   ▼        ▼       ▼
 type1    type2   type3
```

### Returning a Tuple

```rust
fn min_max(nums: &[i32]) -> (i32, i32) {
    let mut min = nums[0];
    let mut max = nums[0];
    for &n in nums.iter() {
        if n < min { min = n; }
        if n > max { max = n; }
    }
    (min, max)  // return both values as a tuple
}

fn main() {
    let data = vec![3, 1, 7, 2, 9, 4];
    let (lo, hi) = min_max(&data);  // destructure the tuple
    println!("min={}, max={}", lo, hi);  // min=1, max=9
}
```

### Destructuring (Unpacking) Tuples

```rust
fn divide_with_remainder(a: i32, b: i32) -> (i32, i32) {
    (a / b, a % b)
}

fn main() {
    // Method 1: Destructure directly
    let (quotient, remainder) = divide_with_remainder(17, 5);
    println!("17 / 5 = {} remainder {}", quotient, remainder);

    // Method 2: Access by index
    let result = divide_with_remainder(17, 5);
    println!("quotient={}, remainder={}", result.0, result.1);
}
```

### Tuple Access by Index

```
let t = (10, "hello", 3.14);
         │      │       │
         ▼      ▼       ▼
        t.0    t.1     t.2
       (i32) (&str)  (f64)
```

---

## 7. The Unit Type `()`

### What is `()`?

`()` (pronounced "unit") is Rust's equivalent of `void` in C/C++. It is:
- A type with exactly **one value**: `()`
- The return type when a function "returns nothing"
- An empty tuple

```rust
fn say_hello() {          // implicitly returns ()
    println!("Hello!");
}

fn say_hello_explicit() -> () {  // same as above
    println!("Hello!");
}
```

### () in DSA Context

```rust
// Side-effect functions return ()
fn swap(a: &mut i32, b: &mut i32) {
    let temp = *a;
    *a = *b;
    *b = temp;
    // implicitly returns ()
}

fn main() {
    let mut x = 5;
    let mut y = 10;
    swap(&mut x, &mut y);
    println!("x={}, y={}", x, y);  // x=10, y=5
}
```

---

## 8. Diverging Functions with `!`

### What is a Diverging Function?

A **diverging function** never returns to its caller. It either:
- Panics
- Loops forever
- Exits the process

The return type `!` (called "never" type) signals this to the compiler.

```rust
fn panic_always() -> ! {
    panic!("This function never returns!");
}

fn infinite_loop() -> ! {
    loop {
        // spin forever
    }
}

fn exit_program() -> ! {
    std::process::exit(1);
}
```

### Why `!` is Useful in DSA

The `!` type satisfies **any type constraint** — it coerces to any type. This allows:

```rust
fn find_or_panic(arr: &[i32], target: i32) -> usize {
    for (i, &val) in arr.iter().enumerate() {
        if val == target {
            return i;
        }
    }
    panic!("Target {} not found", target)
    // panic! returns !, which coerces to usize here
    // so the compiler is satisfied
}
```

```rust
// With match — useful for unreachable branches
fn classify(n: i32) -> &'static str {
    match n {
        0      => "zero",
        1..=9  => "single digit",
        10..=99 => "double digit",
        _      => unreachable!("out of expected range")
        //         ^^^^^^^^^^^^^ returns !, compiles fine
    }
}
```

---

## 9. Nested Functions

### Functions Inside Functions

Rust allows defining functions inside other functions. The inner function is local in scope.

```rust
fn compute_stats(data: &[f64]) -> (f64, f64) {
    // Inner helper — only visible inside compute_stats
    fn mean(nums: &[f64]) -> f64 {
        nums.iter().sum::<f64>() / nums.len() as f64
    }

    fn variance(nums: &[f64], avg: f64) -> f64 {
        nums.iter()
            .map(|x| (x - avg).powi(2))
            .sum::<f64>()
            / nums.len() as f64
    }

    let avg = mean(data);
    let var = variance(data, avg);
    (avg, var)
}

fn main() {
    let data = vec![2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];
    let (mean, variance) = compute_stats(&data);
    println!("Mean={}, Variance={}", mean, variance);
}
```

> **Key Difference from Closures:** Nested `fn` items cannot capture variables from the enclosing scope (unlike closures). They are full function items.

---

## 10. Function Pointers

### What is a Function Pointer?

A **function pointer** is a variable that holds the **address** (memory location) of a function. It lets you:
- Choose which function to call at runtime
- Pass functions as data

```
MEMORY:
┌───────────┐
│ fn add()  │◄── function pointer `fp` points here
│   code    │
└───────────┘
```

### Syntax: `fn(T1, T2) -> R`

```rust
fn add(x: i32, y: i32) -> i32 { x + y }
fn sub(x: i32, y: i32) -> i32 { x - y }
fn mul(x: i32, y: i32) -> i32 { x * y }

fn apply(op: fn(i32, i32) -> i32, a: i32, b: i32) -> i32 {
    op(a, b)  // call the function through the pointer
}

fn main() {
    println!("{}", apply(add, 10, 3));  // 13
    println!("{}", apply(sub, 10, 3));  // 7
    println!("{}", apply(mul, 10, 3));  // 30

    // Store in a variable
    let operation: fn(i32, i32) -> i32 = add;
    println!("{}", operation(5, 6));  // 11
}
```

### Array of Function Pointers (Strategy Pattern)

```rust
fn bubble_sort(arr: &mut Vec<i32>) {
    let n = arr.len();
    for i in 0..n {
        for j in 0..n-i-1 {
            if arr[j] > arr[j+1] {
                arr.swap(j, j+1);
            }
        }
    }
}

fn selection_sort(arr: &mut Vec<i32>) {
    let n = arr.len();
    for i in 0..n {
        let mut min_idx = i;
        for j in i+1..n {
            if arr[j] < arr[min_idx] {
                min_idx = j;
            }
        }
        arr.swap(i, min_idx);
    }
}

fn main() {
    // Table of sorting strategies
    let strategies: Vec<(&str, fn(&mut Vec<i32>))> = vec![
        ("bubble",    bubble_sort),
        ("selection", selection_sort),
    ];

    for (name, sort_fn) in &strategies {
        let mut data = vec![5, 2, 8, 1, 9];
        sort_fn(&mut data);
        println!("{}: {:?}", name, data);
    }
}
```

### Function Pointers vs Closures

| Feature              | `fn` pointer         | Closure (`Fn`/`FnMut`/`FnOnce`) |
|----------------------|----------------------|----------------------------------|
| Captures environment | ❌ No                | ✅ Yes                           |
| Size                 | Pointer (8 bytes)    | Varies (size of captured data)   |
| Can use as trait obj | Less ergonomic       | `Box<dyn Fn(...)>`               |
| Performance          | Fastest              | Near zero-cost (monomorphized)   |

---

## 11. Closures — Anonymous Functions

### What is a Closure?

A **closure** is an anonymous (unnamed) function that can **capture variables from its surrounding environment (scope)**.

```
CLOSURE ANATOMY:

|param1, param2| expression_or_block
│     │         │
│     │         └── body (expression or block)
│     └──────────── parameters
└──────────────────── pipe delimiters (no `fn` keyword needed)
```

### Basic Closure

```rust
fn main() {
    // Simple closure
    let square = |x: i32| x * x;
    println!("{}", square(5));  // 25

    // Closure with a block body
    let add_and_print = |a: i32, b: i32| {
        let sum = a + b;
        println!("Sum = {}", sum);
        sum
    };
    add_and_print(3, 7);  // prints "Sum = 10", returns 10
}
```

### Capturing the Environment

This is what makes closures different from regular functions:

```rust
fn main() {
    let threshold = 5;  // variable in outer scope

    // Closure CAPTURES `threshold` from the environment
    let is_above = |x: i32| x > threshold;

    println!("{}", is_above(3));   // false
    println!("{}", is_above(7));   // true
    println!("{}", is_above(5));   // false
}
```

### The Three Closure Traits

Rust uses three traits to describe how closures interact with captured values:

```
┌──────────────────────────────────────────────────────────┐
│                   Closure Capture Hierarchy              │
│                                                          │
│   FnOnce  ── can be called once (moves out of captured) │
│      ▲                                                   │
│      │  is also                                          │
│   FnMut   ── can be called multiple times (mutates)     │
│      ▲                                                   │
│      │  is also                                          │
│   Fn      ── can be called any times (immutable borrow) │
└──────────────────────────────────────────────────────────┘
```

#### `Fn` — Immutable Capture (most common)

```rust
fn apply_twice<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(f(x))
}

fn main() {
    let double = |x| x * 2;
    println!("{}", apply_twice(double, 3));  // 12 (3 -> 6 -> 12)
}
```

#### `FnMut` — Mutably Captures Environment

```rust
fn main() {
    let mut count = 0;
    let mut increment = || {
        count += 1;   // mutates captured variable
        count
    };

    println!("{}", increment()); // 1
    println!("{}", increment()); // 2
    println!("{}", increment()); // 3
}
```

#### `FnOnce` — Consumes Captured Value (called once)

```rust
fn consume_once<F: FnOnce() -> String>(f: F) -> String {
    f()
}

fn main() {
    let name = String::from("Alice");
    let greet = move || format!("Hello, {}!", name);  // moves `name` into closure
    println!("{}", consume_once(greet));
    // greet cannot be called again — it consumed `name`
}
```

### The `move` Keyword

`move` forces the closure to **take ownership** of captured variables:

```rust
fn main() {
    let data = vec![1, 2, 3];

    // Without move: borrows data
    let print_data = || println!("{:?}", data);
    print_data();
    println!("{:?}", data);  // still accessible

    // With move: takes ownership of data
    let owned_print = move || println!("{:?}", data);
    owned_print();
    // println!("{:?}", data);  ❌ data was moved into the closure
}
```

### Type Inference in Closures

Rust infers closure parameter types from usage — types are optional:

```rust
fn main() {
    // Explicit types
    let add_explicit = |x: i32, y: i32| -> i32 { x + y };

    // Inferred types (same function, shorter)
    let add_inferred = |x, y| x + y;

    // Even shorter for single expressions
    let add_short = |x: i32, y: i32| x + y;

    println!("{}", add_short(3, 4));  // 7
}
```

---

## 12. Higher-Order Functions

### Definition

A **higher-order function** (HOF) is a function that either:
1. Takes one or more functions as arguments, OR
2. Returns a function as its result

### Taking Functions as Arguments

```rust
fn apply_to_all(v: &[i32], f: impl Fn(i32) -> i32) -> Vec<i32> {
    v.iter().map(|&x| f(x)).collect()
}

fn main() {
    let nums = vec![1, 2, 3, 4, 5];

    let doubled = apply_to_all(&nums, |x| x * 2);
    println!("{:?}", doubled);  // [2, 4, 6, 8, 10]

    let squared = apply_to_all(&nums, |x| x * x);
    println!("{:?}", squared);  // [1, 4, 9, 16, 25]
}
```

### Returning Functions (Closures)

```rust
// Returns a closure that adds `n` to its argument
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n   // `move` captures `n` by value
}

fn main() {
    let add5  = make_adder(5);
    let add10 = make_adder(10);

    println!("{}", add5(3));   // 8
    println!("{}", add10(3));  // 13
    println!("{}", add5(add10(2))); // 17  (composition!)
}
```

### Function Composition

```rust
fn compose<A, B, C>(
    f: impl Fn(A) -> B,
    g: impl Fn(B) -> C,
) -> impl Fn(A) -> C {
    move |x| g(f(x))
}

fn main() {
    let double   = |x: i32| x * 2;
    let add_one  = |x: i32| x + 1;

    let double_then_add = compose(double, add_one);
    println!("{}", double_then_add(5));  // (5*2)+1 = 11
}
```

### Memoization (HOF Pattern for DSA)

```rust
use std::collections::HashMap;

fn memoize<A, R>(mut f: impl FnMut(A) -> R) -> impl FnMut(A) -> R
where
    A: Eq + std::hash::Hash + Copy,
    R: Copy,
{
    let mut cache: HashMap<A, R> = HashMap::new();
    move |arg| {
        if let Some(&cached) = cache.get(&arg) {
            cached
        } else {
            let result = f(arg);
            cache.insert(arg, result);
            result
        }
    }
}
```

---

## 13. Iterator Adapters & Functional Pipelines

### Iterator Mental Model

```
SOURCE → adapter1 → adapter2 → ... → CONSUMER
  │                                       │
  │ lazy (nothing runs yet)               │ triggers execution
  └───────────────────────────────────────┘
```

Iterators in Rust are **lazy** — they don't compute anything until consumed.

### The Core Three: `map`, `filter`, `fold`

```rust
fn main() {
    let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    // MAP: transform each element
    let doubled: Vec<i32> = numbers.iter()
        .map(|&x| x * 2)
        .collect();
    println!("Doubled: {:?}", doubled);

    // FILTER: keep only matching elements
    let evens: Vec<&i32> = numbers.iter()
        .filter(|&&x| x % 2 == 0)
        .collect();
    println!("Evens: {:?}", evens);

    // FOLD (= reduce): accumulate into single value
    let sum: i32 = numbers.iter()
        .fold(0, |acc, &x| acc + x);
    println!("Sum: {}", sum);  // 55
}
```

### Pipeline: DSA Example — Find Top-3 Even Squares

```rust
fn top_k_even_squares(nums: &[i32], k: usize) -> Vec<i32> {
    let mut result: Vec<i32> = nums.iter()
        .filter(|&&x| x % 2 == 0)        // keep evens
        .map(|&x| x * x)                  // square them
        .collect();
    result.sort_unstable_by(|a, b| b.cmp(a)); // sort descending
    result.truncate(k);                   // keep only top k
    result
}

fn main() {
    let data = vec![1, 4, 3, 8, 2, 6, 5, 10];
    println!("{:?}", top_k_even_squares(&data, 3));  // [100, 64, 36]
}
```

### Common Iterator Adapters

| Adapter             | What it does                                       |
|---------------------|----------------------------------------------------|
| `.map(f)`           | Transform each element                             |
| `.filter(pred)`     | Keep elements where predicate is true              |
| `.fold(init, f)`    | Accumulate into a single value                     |
| `.enumerate()`      | Adds index: `(index, value)`                       |
| `.zip(iter)`        | Pair elements from two iterators                   |
| `.flat_map(f)`      | Map then flatten one level                         |
| `.take(n)`          | First n elements                                   |
| `.skip(n)`          | Skip first n elements                              |
| `.chain(iter)`      | Concatenate two iterators                          |
| `.any(pred)`        | True if any element matches                        |
| `.all(pred)`        | True if all elements match                         |
| `.count()`          | Count elements                                     |
| `.sum()`            | Sum all elements                                   |
| `.max()` / `.min()` | Maximum / minimum element                          |
| `.peekable()`       | Allows peeking at next without consuming           |
| `.windows(n)`       | Overlapping slices of size n                       |
| `.chunks(n)`        | Non-overlapping slices                             |

---

## 14. Generic Functions

### What is a Generic Function?

A **generic function** is parameterized over one or more types. Instead of writing the same function for `i32`, `f64`, `u8`, etc., you write it once and the compiler generates specialized versions.

```
WITHOUT GENERICS:               WITH GENERICS:
fn max_i32(a: i32, b: i32)     fn max<T>(a: T, b: T) -> T
fn max_f64(a: f64, b: f64)     // one function, works for all T
fn max_u8 (a: u8,  b: u8 )     // where T: PartialOrd
```

### Syntax: Type Parameters `<T>`

```rust
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list.iter() {
        if item > largest {
            largest = item;
        }
    }
    largest
}

fn main() {
    let numbers = vec![34, 50, 25, 100, 65];
    println!("Largest number: {}", largest(&numbers));  // 100

    let chars = vec!['y', 'm', 'a', 'q'];
    println!("Largest char: {}", largest(&chars));  // y
}
```

### Multiple Type Parameters

```rust
fn pair_up<A, B>(first: A, second: B) -> (A, B) {
    (first, second)
}

fn main() {
    let p = pair_up(42, "hello");
    println!("{:?}", p);  // (42, "hello")
}
```

### Generic with Struct

```rust
struct Stack<T> {
    elements: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self {
        Stack { elements: Vec::new() }
    }

    fn push(&mut self, item: T) {
        self.elements.push(item);
    }

    fn pop(&mut self) -> Option<T> {
        self.elements.pop()
    }

    fn peek(&self) -> Option<&T> {
        self.elements.last()
    }

    fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    fn size(&self) -> usize {
        self.elements.len()
    }
}

fn main() {
    let mut stack: Stack<i32> = Stack::new();
    stack.push(1);
    stack.push(2);
    stack.push(3);

    while let Some(top) = stack.pop() {
        println!("{}", top);  // 3, 2, 1
    }
}
```

---

## 15. Trait Bounds on Functions

### What is a Trait Bound?

A **trait bound** constrains which types a generic parameter can be. It says: "T must implement this trait (set of behaviors)."

```
fn function<T: Trait1 + Trait2>(arg: T)
                │         │
                │         └── T must ALSO implement Trait2
                └────────────── T must implement Trait1
```

### The `+` Syntax (Multiple Bounds)

```rust
use std::fmt::{Display, Debug};

fn print_both<T: Display + Debug>(item: T) {
    println!("Display: {}", item);
    println!("Debug:   {:?}", item);
}

fn main() {
    print_both(42);
    print_both("hello");
}
```

### The `where` Clause (Readable Alternative)

For complex bounds, use `where` for readability:

```rust
// Hard to read:
fn compare_and_display<T: PartialOrd + Display, U: Display>(t: T, u: U) {
    // ...
}

// Cleaner with `where`:
fn compare_and_display<T, U>(t: T, u: U)
where
    T: PartialOrd + Display,
    U: Display,
{
    if t > t { // just example
        println!("{} > itself? No.", t);
    }
    println!("U is: {}", u);
}
```

### `impl Trait` Syntax (Sugar)

```rust
// Equivalent ways to express "takes something that implements Display"

// 1. Generic with bound
fn print_generic<T: Display>(item: T) { println!("{}", item); }

// 2. impl Trait (syntactic sugar, same thing)
fn print_impl(item: impl Display) { println!("{}", item); }

// impl Trait in return position (→ anonymous generic return type)
fn make_greeting(name: &str) -> impl Display {
    format!("Hello, {}!", name)
}
```

### `dyn Trait` — Dynamic Dispatch (Runtime Polymorphism)

```rust
trait Shape {
    fn area(&self) -> f64;
}

struct Circle { radius: f64 }
struct Square { side: f64 }

impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
}

impl Shape for Square {
    fn area(&self) -> f64 { self.side * self.side }
}

// dyn Shape = "some shape, determined at runtime"
fn print_area(shape: &dyn Shape) {
    println!("Area: {:.2}", shape.area());
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 3.0 }),
        Box::new(Square { side: 4.0 }),
    ];

    for shape in &shapes {
        print_area(shape.as_ref());
    }
}
```

### `impl Trait` vs `dyn Trait`

```
                 impl Trait                     dyn Trait
                 ──────────                     ─────────
Dispatch:        Static (compile-time)          Dynamic (runtime vtable)
Performance:     Faster (no indirection)        Slower (vtable lookup)
Code size:       Larger (monomorphized)         Smaller (one copy)
Heterogeneous    ❌ No                          ✅ Yes (Box<dyn Trait>)
  collections:
Return type:     Single concrete type           Any type implementing trait
```

---

## 16. Lifetime Parameters in Functions

### What is a Lifetime?

A **lifetime** is Rust's way of tracking how long a reference is valid. It prevents **dangling references** (pointers to freed memory) at compile time.

```
Reference valid:   ──────────────────►
Data exists:       ────────────────────────────►
                              ▲
                              │ reference outlives data = BUG (use-after-free)
                              Rust PREVENTS this at compile time
```

### Lifetime Annotation Syntax

```rust
//  'a = lifetime parameter name (convention: 'a, 'b, 'c, 'static)
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
//         ^^   ^^^               ^^^     ^^^
//         │    │                 │       └── return ref lives as long as 'a
//         │    └─────────────────┘────────── both params live at least 'a
//         └─────────────────────────────────── declare lifetime parameter
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xyz");
        result = longest(s1.as_str(), s2.as_str());
        println!("Longest: {}", result);  // ✅ both alive here
    }
    // println!("{}", result);  ❌ s2 dropped, result would dangle
}
```

### Lifetime Elision Rules

Rust can often infer lifetimes automatically. This is called **lifetime elision**:

```rust
// Rule 1: each input reference gets its own lifetime
fn foo(x: &str) -> &str { ... }
// Compiler sees: fn foo<'a>(x: &'a str) -> &'a str

// Rule 2: if one input, output gets that lifetime
fn first_word(s: &str) -> &str {
    let bytes = s.as_bytes();
    for (i, &b) in bytes.iter().enumerate() {
        if b == b' ' { return &s[..i]; }
    }
    s
}
// No explicit lifetimes needed! Compiler infers them.
```

### Struct with Lifetime

```rust
struct StrSplit<'a> {
    remainder: &'a str,
    delimiter: &'a str,
}

impl<'a> StrSplit<'a> {
    fn new(s: &'a str, delim: &'a str) -> Self {
        StrSplit { remainder: s, delimiter: delim }
    }
}
```

### `'static` Lifetime

`'static` means "lives for the entire program duration":

```rust
// String literals have 'static lifetime (baked into binary)
let s: &'static str = "I live forever";

fn static_str() -> &'static str {
    "constant string"  // OK — string literals are 'static
}
```

---

## 17. Methods & Associated Functions

### `impl` Block

Methods are functions defined **inside an `impl` block** for a type.

```rust
struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    // ASSOCIATED FUNCTION (no `self`) — called with ::
    fn new(width: f64, height: f64) -> Self {
        Rectangle { width, height }
    }

    // METHOD — takes `self` (or &self / &mut self)
    fn area(&self) -> f64 {
        self.width * self.height
    }

    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }

    fn is_square(&self) -> bool {
        (self.width - self.height).abs() < f64::EPSILON
    }

    // Mutable method
    fn scale(&mut self, factor: f64) {
        self.width  *= factor;
        self.height *= factor;
    }

    // Consuming method (takes ownership)
    fn into_square(self) -> Rectangle {
        let side = self.width.max(self.height);
        Rectangle { width: side, height: side }
    }
}

fn main() {
    let mut r = Rectangle::new(4.0, 3.0);  // :: for associated fn
    println!("Area: {}", r.area());         // . for methods
    println!("Perimeter: {}", r.perimeter());
    r.scale(2.0);
    println!("Scaled: {}x{}", r.width, r.height);
    let sq = r.into_square();               // consumes r
    println!("Square side: {}", sq.width);
}
```

### `self` Variants

| Receiver        | Meaning                                    | When to use                     |
|-----------------|--------------------------------------------|---------------------------------|
| `&self`         | Immutable borrow of self                   | Reading data (most common)      |
| `&mut self`     | Mutable borrow of self                     | Modifying data                  |
| `self`          | Takes ownership of self                    | Consuming/converting the object |
| `self: Box<Self>`| Called on boxed self                      | Rarely needed                   |

### Builder Pattern (Chained Methods)

```rust
struct QueryBuilder {
    table: String,
    limit: Option<usize>,
    conditions: Vec<String>,
}

impl QueryBuilder {
    fn new(table: &str) -> Self {
        QueryBuilder {
            table: table.to_string(),
            limit: None,
            conditions: Vec::new(),
        }
    }

    // Each method returns Self to enable chaining
    fn limit(mut self, n: usize) -> Self {
        self.limit = Some(n);
        self
    }

    fn where_clause(mut self, condition: &str) -> Self {
        self.conditions.push(condition.to_string());
        self
    }

    fn build(&self) -> String {
        let cond = if self.conditions.is_empty() {
            String::new()
        } else {
            format!(" WHERE {}", self.conditions.join(" AND "))
        };
        let limit = self.limit
            .map(|n| format!(" LIMIT {}", n))
            .unwrap_or_default();
        format!("SELECT * FROM {}{}{}", self.table, cond, limit)
    }
}

fn main() {
    let query = QueryBuilder::new("users")
        .where_clause("age > 18")
        .where_clause("active = true")
        .limit(10)
        .build();
    println!("{}", query);
    // SELECT * FROM users WHERE age > 18 AND active = true LIMIT 10
}
```

---

## 18. `const fn` — Compile-Time Functions

### What is `const fn`?

A `const fn` is a function that can be **evaluated at compile time**, embedding the result directly into the binary. This enables:
- Zero runtime cost
- Compile-time lookup tables
- Compile-time validation

```rust
const fn factorial(n: u64) -> u64 {
    if n == 0 { 1 } else { n * factorial(n - 1) }
}

// Computed at COMPILE TIME — no runtime cost
const FACT_10: u64 = factorial(10);

fn main() {
    println!("10! = {}", FACT_10);  // 3628800 — baked into binary
}
```

### Compile-Time Lookup Tables

```rust
const fn build_powers_of_two() -> [u64; 16] {
    let mut table = [0u64; 16];
    let mut i = 0;
    while i < 16 {
        table[i] = 1u64 << i;
        i += 1;
    }
    table
}

const POWERS_OF_TWO: [u64; 16] = build_powers_of_two();

fn main() {
    for (i, &p) in POWERS_OF_TWO.iter().enumerate() {
        println!("2^{} = {}", i, p);
    }
}
```

### Restrictions on `const fn`

As of stable Rust, `const fn` cannot use:
- `unsafe` (partially lifted)
- Heap allocation
- Trait objects (`dyn`)
- Floating point operations (some exceptions)
- Some loop forms (while/for are now allowed)

---

## 19. `async fn` — Asynchronous Functions

### Concept: What is Async?

**Asynchronous functions** allow tasks to be paused (at `await` points) while waiting for I/O or other operations, without blocking the thread. This is critical for high-performance network/IO code.

```
SYNC:          ASYNC:
────────────   ─────────────────────────
task A runs    task A starts
task A waits   task A awaits (paused)
task A waits       task B runs
task A resumes     task B completes
task A done    task A resumes
               task A done
```

### Basic `async fn`

```rust
use tokio; // add to Cargo.toml: tokio = { version = "1", features = ["full"] }

async fn fetch_data(id: u32) -> String {
    // Simulate async work (in real code: HTTP request, DB query, etc.)
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    format!("Data for id={}", id)
}

async fn process() {
    let result = fetch_data(42).await;
    println!("{}", result);
}

#[tokio::main]
async fn main() {
    process().await;
}
```

### What `async fn` Returns

`async fn` always returns a **Future** — a value representing a computation that hasn't completed yet:

```rust
// These two are equivalent:
async fn foo() -> i32 { 42 }

fn foo_explicit() -> impl std::future::Future<Output = i32> {
    async { 42 }
}
```

### Concurrent Execution with `join!`

```rust
use tokio::join;

async fn task_a() -> i32 { 1 }
async fn task_b() -> i32 { 2 }

#[tokio::main]
async fn main() {
    // Run both concurrently, wait for both
    let (a, b) = join!(task_a(), task_b());
    println!("{}", a + b);  // 3
}
```

---

## 20. `unsafe fn` — Unsafe Functions

### What is Unsafe?

Rust's safety guarantees come from its type system and borrow checker. `unsafe` code opts out of certain checks — you take responsibility for correctness.

### Unsafe Operations Allowed Inside `unsafe`

1. Dereference raw pointers
2. Call unsafe functions
3. Access mutable static variables
4. Implement unsafe traits

```rust
// Declaring an unsafe function
unsafe fn raw_copy(src: *const i32, dst: *mut i32, count: usize) {
    for i in 0..count {
        // Unsafe: dereferencing raw pointers
        *dst.add(i) = *src.add(i);
    }
}

fn main() {
    let src = vec![1, 2, 3, 4, 5];
    let mut dst = vec![0i32; 5];

    unsafe {
        // Must mark the call site as unsafe
        raw_copy(src.as_ptr(), dst.as_mut_ptr(), src.len());
    }

    println!("{:?}", dst);  // [1, 2, 3, 4, 5]
}
```

### Safe Wrapper Pattern (Best Practice)

```rust
// Public safe API wraps unsafe internals
pub fn safe_memcpy(src: &[i32], dst: &mut [i32]) {
    assert_eq!(src.len(), dst.len(), "Length mismatch");
    unsafe {
        raw_copy(src.as_ptr(), dst.as_mut_ptr(), src.len());
    }
}
```

---

## 21. Extern Functions & FFI

### What is FFI?

**Foreign Function Interface** (FFI) allows Rust to call functions written in other languages (primarily C) and vice versa.

### Calling C from Rust

```rust
// Declare C functions using `extern "C"`
extern "C" {
    fn abs(x: i32) -> i32;
    fn sqrt(x: f64) -> f64;
}

fn main() {
    unsafe {
        println!("abs(-5) = {}", abs(-5));    // 5
        println!("sqrt(9.0) = {}", sqrt(9.0)); // 3.0
    }
}
```

### Exporting Rust Functions to C

```rust
// No name mangling — callable from C
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}
```

### Calling Conventions

```
"C"       — Standard C calling convention (most common)
"system"  — OS default (WinAPI on Windows, same as "C" elsewhere)
"Rust"    — Default Rust calling convention (not stable ABI)
"cdecl"   — Legacy 32-bit C
"stdcall" — Windows 32-bit API
```

---

## 22. Pattern Matching in Parameters

### Destructuring in Function Parameters

Rust allows you to destructure complex types **directly in the parameter list**:

```rust
// Destructure a tuple parameter
fn add_pair((x, y): (i32, i32)) -> i32 {
    x + y
}

// Destructure a struct parameter
struct Point { x: f64, y: f64 }

fn distance_from_origin(&Point { x, y }: &Point) -> f64 {
    (x * x + y * y).sqrt()
}

fn main() {
    println!("{}", add_pair((3, 4)));  // 7

    let p = Point { x: 3.0, y: 4.0 };
    println!("{}", distance_from_origin(&p));  // 5.0
}
```

### Ignoring Parameters with `_`

```rust
fn always_zero(_: i32, _: i32) -> i32 {
    0
}

// Useful in trait implementations when you don't need the param
fn first_of_three(a: i32, _: i32, _: i32) -> i32 {
    a
}
```

### Slice Patterns

```rust
fn describe_slice(s: &[i32]) -> String {
    match s {
        []           => "empty".to_string(),
        [x]          => format!("single: {}", x),
        [x, y]       => format!("pair: {}, {}", x, y),
        [first, .., last] => format!("multi: {} .. {}", first, last),
    }
}

fn main() {
    println!("{}", describe_slice(&[]));          // empty
    println!("{}", describe_slice(&[42]));        // single: 42
    println!("{}", describe_slice(&[1, 2]));      // pair: 1, 2
    println!("{}", describe_slice(&[1,2,3,4,5])); // multi: 1 .. 5
}
```

---

## 23. Recursion & Tail Calls

### What is Recursion?

A function is **recursive** when it calls itself. Every recursive function needs:
1. **Base case** — the condition where it stops
2. **Recursive case** — calls itself with a simpler input, progressing toward the base case

```
Recursion Call Stack (factorial(4)):

factorial(4)
    └── 4 * factorial(3)
              └── 3 * factorial(2)
                        └── 2 * factorial(1)
                                  └── 1 * factorial(0)
                                              └── returns 1  ← BASE CASE
                                  └── returns 1*1 = 1
                        └── returns 2*1 = 2
              └── returns 3*2 = 6
    └── returns 4*6 = 24
```

### Basic Recursion

```rust
fn factorial(n: u64) -> u64 {
    match n {
        0 | 1 => 1,          // base cases
        _ => n * factorial(n - 1),  // recursive case
    }
}

fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn main() {
    println!("5! = {}", factorial(5));  // 120
    println!("fib(10) = {}", fibonacci(10));  // 55
}
```

### The Stack Overflow Problem

Naive recursion uses **stack frames** — each call pushes a new frame. For large inputs, this overflows the stack.

```
Stack grows downward:
┌────────────────┐ ← Stack top
│ factorial(1000)│
│ factorial(999) │
│ factorial(998) │
│ ...            │
│ factorial(1)   │
└────────────────┘ ← OVERFLOW if too deep!
```

### Tail Recursion (TCO)

A **tail call** is when the recursive call is the **last operation** in the function. Some languages optimize this to reuse the current stack frame.

> ⚠️ **Important:** Rust does NOT guarantee tail-call optimization (TCO). You must manually convert to iteration for large inputs.

```rust
// Tail-recursive factorial (last op is recursive call)
fn factorial_tail(n: u64, acc: u64) -> u64 {
    match n {
        0 | 1 => acc,
        _ => factorial_tail(n - 1, n * acc),  // tail call
    }
}

// But in Rust, this STILL might overflow for very large n
// Use the iterative version instead:
fn factorial_iter(n: u64) -> u64 {
    (1..=n).product()
}
```

### Converting Recursion to Iteration (Pattern)

```rust
// Recursive DFS on a tree
fn dfs_recursive(node: usize, graph: &Vec<Vec<usize>>, visited: &mut Vec<bool>) {
    visited[node] = true;
    println!("Visited: {}", node);
    for &neighbor in &graph[node] {
        if !visited[neighbor] {
            dfs_recursive(neighbor, graph, visited);
        }
    }
}

// Iterative DFS (explicit stack — avoids stack overflow)
fn dfs_iterative(start: usize, graph: &Vec<Vec<usize>>) {
    let n = graph.len();
    let mut visited = vec![false; n];
    let mut stack = vec![start];

    while let Some(node) = stack.pop() {
        if visited[node] { continue; }
        visited[node] = true;
        println!("Visited: {}", node);
        for &neighbor in &graph[node] {
            if !visited[neighbor] {
                stack.push(neighbor);
            }
        }
    }
}
```

---

## 24. Function Dispatch — Static vs Dynamic

### What is Dispatch?

**Dispatch** is the process of deciding *which function implementation to call* for a given call site.

### Static Dispatch (Monomorphization)

At compile time, the compiler generates a **concrete version** of the function for each type used:

```rust
fn print_it<T: Display>(item: T) {
    println!("{}", item);
}

// Compiler generates:
// fn print_it_i32(item: i32) { println!("{}", item); }
// fn print_it_str(item: &str) { println!("{}", item); }
// fn print_it_f64(item: f64) { println!("{}", item); }
```

```
STATIC DISPATCH:

print_it::<i32>(42)  ───► print_it_i32 (concrete code)
print_it::<&str>("hi") ──► print_it_str (concrete code)

No runtime cost — direct function calls
```

### Dynamic Dispatch (vtable)

At runtime, a **vtable** (virtual table of function pointers) is used to dispatch:

```rust
trait Animal {
    fn sound(&self) -> &str;
}

struct Dog;
struct Cat;

impl Animal for Dog { fn sound(&self) -> &str { "woof" } }
impl Animal for Cat { fn sound(&self) -> &str { "meow" } }

fn make_sound(animal: &dyn Animal) {
    println!("{}", animal.sound());
}
```

```
DYNAMIC DISPATCH:

Box<dyn Animal>
┌───────────────┐
│ data ptr ─────┼──► object in memory
│ vtable ptr ───┼──► ┌─────────────────────────┐
└───────────────┘    │ vtable for Dog           │
                     │  .sound = Dog::sound ────┼──► fn() { "woof" }
                     │  .drop  = Dog::drop  ────┼──► drop code
                     └─────────────────────────┘
```

### When to Choose Which

| Situation                              | Use          |
|----------------------------------------|--------------|
| Known types at compile time            | `impl Trait` (static) |
| Heterogeneous collection (e.g., Vec)   | `dyn Trait`  (dynamic)|
| Maximum performance                    | `impl Trait` (static) |
| Plugin/extension systems               | `dyn Trait`  (dynamic)|
| Small binary size needed               | `dyn Trait`  (dynamic)|

---

## 25. Monomorphization & Zero-Cost Abstractions

### Monomorphization Explained

When you write a generic function `fn foo<T>`, Rust **generates a unique copy** of that function for every concrete type `T` that you actually use. This process is called **monomorphization**.

```
SOURCE CODE:                AFTER MONOMORPHIZATION:

fn double<T: Add>(x: T)    fn double_i32(x: i32) -> i32 { x + x }
    -> T { x + x }         fn double_f64(x: f64) -> f64 { x + x }
                            fn double_str → compile error (str can't Add)
```

### Zero-Cost Abstractions

This is Rust's core design philosophy:
> *"What you don't use, you don't pay for. What you do use, you couldn't hand-code any better."*
> — Bjarne Stroustrup (C++ motto, adopted by Rust)

```rust
// This iterator pipeline...
let sum: i32 = (0..1000)
    .filter(|x| x % 2 == 0)
    .map(|x| x * x)
    .sum();

// ...compiles to essentially the same assembly as:
let mut sum = 0i32;
let mut x = 0i32;
while x < 1000 {
    if x % 2 == 0 { sum += x * x; }
    x += 1;
}
```

---

## 26. Error Handling in Functions

### The `Result<T, E>` Type

Functions that can fail should return `Result<T, E>`:
- `Ok(T)` — success with value of type T
- `Err(E)` — failure with error of type E

```rust
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err(String::from("Division by zero"))
    } else {
        Ok(a / b)
    }
}

fn main() {
    match divide(10.0, 2.0) {
        Ok(result) => println!("Result: {}", result),
        Err(e)     => println!("Error: {}", e),
    }
}
```

### The `?` Operator (Propagate Errors)

The `?` operator is syntactic sugar for "return Err early if this failed":

```rust
use std::num::ParseIntError;

fn parse_and_double(s: &str) -> Result<i32, ParseIntError> {
    let n = s.trim().parse::<i32>()?;  // ? = return Err if parse fails
    Ok(n * 2)
}

fn pipeline(input: &str) -> Result<i32, ParseIntError> {
    let doubled = parse_and_double(input)?;  // propagate errors
    let tripled = doubled.checked_mul(3)
        .ok_or("overflow".parse::<i32>().unwrap_err())?;
    Ok(tripled)
}
```

### The `Option<T>` Type

For functions that might return "nothing" (not an error):

```rust
fn find_first_even(nums: &[i32]) -> Option<i32> {
    nums.iter().find(|&&x| x % 2 == 0).copied()
}

fn main() {
    let v = vec![1, 3, 5, 4, 7];
    match find_first_even(&v) {
        Some(n) => println!("First even: {}", n),
        None    => println!("No even number found"),
    }
}
```

### Custom Error Types

```rust
use std::fmt;

#[derive(Debug)]
enum MathError {
    DivisionByZero,
    NegativeSqrt(f64),
    Overflow,
}

impl fmt::Display for MathError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            MathError::DivisionByZero   => write!(f, "Division by zero"),
            MathError::NegativeSqrt(n)  => write!(f, "sqrt of negative: {}", n),
            MathError::Overflow         => write!(f, "Arithmetic overflow"),
        }
    }
}

fn safe_sqrt(x: f64) -> Result<f64, MathError> {
    if x < 0.0 {
        Err(MathError::NegativeSqrt(x))
    } else {
        Ok(x.sqrt())
    }
}
```

---

## 27. Advanced Closure Patterns

### Returning Closures from Functions

```rust
// impl Fn (concrete, efficient, stack-allocated if possible)
fn adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n
}

// Box<dyn Fn> (for dynamic dispatch or when size unknown)
fn dynamic_multiplier(n: i32) -> Box<dyn Fn(i32) -> i32> {
    Box::new(move |x| x * n)
}

fn main() {
    let add3 = adder(3);
    println!("{}", add3(10));  // 13

    let mul5 = dynamic_multiplier(5);
    println!("{}", mul5(10));  // 50
}
```

### Closure as State Machine

```rust
fn counter(start: i32, step: i32) -> impl FnMut() -> i32 {
    let mut current = start;
    move || {
        let value = current;
        current += step;
        value
    }
}

fn main() {
    let mut c = counter(0, 5);
    println!("{}", c());  // 0
    println!("{}", c());  // 5
    println!("{}", c());  // 10
    println!("{}", c());  // 15
}
```

### Closure Combinators

```rust
fn pipe<A, B, C>(f: impl Fn(A) -> B, g: impl Fn(B) -> C) -> impl Fn(A) -> C {
    move |x| g(f(x))
}

fn main() {
    let to_upper = |s: String| s.to_uppercase();
    let add_exclaim = |s: String| s + "!";
    let shout = pipe(to_upper, add_exclaim);
    println!("{}", shout("hello".to_string()));  // HELLO!
}
```

---

## 28. Variadic-Like Patterns in Rust

Rust doesn't have C-style variadic functions for safe code (only for FFI). Instead, use these patterns:

### 1. Slices (most idiomatic)

```rust
fn sum_all(nums: &[i32]) -> i32 {
    nums.iter().sum()
}

fn main() {
    println!("{}", sum_all(&[1, 2, 3, 4, 5]));  // 15
    println!("{}", sum_all(&[10, 20]));           // 30
}
```

### 2. Iterators

```rust
fn sum_iter(iter: impl Iterator<Item = i32>) -> i32 {
    iter.sum()
}

fn main() {
    println!("{}", sum_iter(vec![1, 2, 3].into_iter()));
    println!("{}", sum_iter(1..=100));
}
```

### 3. The `vec![]` Macro Pattern

```rust
// Use a macro for true variadic feel
macro_rules! log_all {
    ($($msg:expr),*) => {
        $(println!("[LOG] {}", $msg);)*
    };
}

fn main() {
    log_all!("Starting", "Processing", "Done");
}
```

### 4. C Variadic (for FFI only)

```rust
use std::ffi::c_int;

extern "C" {
    fn printf(format: *const i8, ...) -> c_int;
}
```

---

## 29. Performance Mental Models

### Function Call Overhead

```
COST HIERARCHY (fastest to slowest):

1. Inline function         → 0 overhead (code folded in-place)
2. Static dispatch (impl)  → direct call, predictable branch prediction
3. Function pointer (fn)   → indirect call, may miss branch prediction
4. Dynamic dispatch (dyn)  → vtable lookup + indirect call (2 indirections)
```

### Inlining with `#[inline]`

```rust
#[inline(always)]  // Force inlining
fn fast_abs(x: i32) -> i32 {
    if x < 0 { -x } else { x }
}

#[inline(never)]   // Prevent inlining (for profiling)
fn do_not_inline(x: i32) -> i32 {
    x * x
}

#[inline]           // Hint to inline (compiler decides)
fn maybe_inline(x: i32) -> i32 {
    x + 1
}
```

### Stack vs Heap in Functions

```
STACK (automatic, fast):        HEAP (manual, slower):
────────────────────────        ──────────────────────
function parameters             Box<T>
local variables                 Vec<T>
return addresses                String
fixed-size arrays [T; N]        Rc<T>, Arc<T>
references (&T)                 Closures that capture heap data
```

### Branch Prediction Hints

```rust
// These are unstable features showing the concept
// In stable Rust, trust the compiler or use likely/unlikely crates

fn classify_fast(n: i32) -> &'static str {
    if n > 0 {        // Common case first — better branch prediction
        "positive"
    } else if n < 0 {
        "negative"
    } else {          // Rare case last
        "zero"
    }
}
```

### Avoiding Allocations in Hot Paths

```rust
// BAD: allocates String in hot loop
fn process_v1(items: &[i32]) -> Vec<String> {
    items.iter()
        .map(|&x| x.to_string())  // allocation per element
        .collect()
}

// BETTER: use iterators, defer allocation
fn process_v2(items: &[i32]) {
    for &x in items {
        print!("{} ", x);  // write directly, no String allocation
    }
}
```

---

## 30. DSA Patterns Using Functions

### Binary Search (Functional Style)

```rust
fn binary_search<T: Ord>(arr: &[T], target: &T) -> Option<usize> {
    let (mut lo, mut hi) = (0usize, arr.len());
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        match arr[mid].cmp(target) {
            std::cmp::Ordering::Equal   => return Some(mid),
            std::cmp::Ordering::Less    => lo = mid + 1,
            std::cmp::Ordering::Greater => hi = mid,
        }
    }
    None
}

fn main() {
    let arr = vec![1, 3, 5, 7, 9, 11, 13, 15];
    println!("{:?}", binary_search(&arr, &7));   // Some(3)
    println!("{:?}", binary_search(&arr, &6));   // None
}
```

### Merge Sort (Recursive + Functional)

```rust
fn merge_sort(arr: &mut Vec<i32>) {
    let n = arr.len();
    if n <= 1 { return; }

    let mid = n / 2;
    let mut left  = arr[..mid].to_vec();
    let mut right = arr[mid..].to_vec();

    merge_sort(&mut left);
    merge_sort(&mut right);

    merge(arr, &left, &right);
}

fn merge(result: &mut Vec<i32>, left: &[i32], right: &[i32]) {
    let (mut i, mut j, mut k) = (0, 0, 0);
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            result[k] = left[i];  i += 1;
        } else {
            result[k] = right[j]; j += 1;
        }
        k += 1;
    }
    while i < left.len()  { result[k] = left[i];  i += 1; k += 1; }
    while j < right.len() { result[k] = right[j]; j += 1; k += 1; }
}
```

### Graph Algorithms Using HOF

```rust
type Graph = Vec<Vec<usize>>;

fn bfs(graph: &Graph, start: usize, on_visit: impl Fn(usize)) {
    let mut visited = vec![false; graph.len()];
    let mut queue = std::collections::VecDeque::new();
    queue.push_back(start);
    visited[start] = true;

    while let Some(node) = queue.pop_front() {
        on_visit(node);  // HOF: user controls what happens at each node
        for &neighbor in &graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true;
                queue.push_back(neighbor);
            }
        }
    }
}

fn main() {
    let graph = vec![
        vec![1, 2],    // 0 → 1, 2
        vec![0, 3],    // 1 → 0, 3
        vec![0, 3],    // 2 → 0, 3
        vec![1, 2],    // 3 → 1, 2
    ];

    let mut order = Vec::new();
    bfs(&graph, 0, |node| order.push(node));
    println!("BFS order: {:?}", order);  // [0, 1, 2, 3]
}
```

### Dynamic Programming with Memoization (HashMap Cache)

```rust
use std::collections::HashMap;

fn fibonacci_memo(n: u64, memo: &mut HashMap<u64, u64>) -> u64 {
    if n <= 1 { return n; }
    if let Some(&cached) = memo.get(&n) { return cached; }
    let result = fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo);
    memo.insert(n, result);
    result
}

fn fib(n: u64) -> u64 {
    let mut memo = HashMap::new();
    fibonacci_memo(n, &mut memo)
}

fn main() {
    for i in 0..=10 {
        print!("{} ", fib(i));
    }
    // 0 1 1 2 3 5 8 13 21 34 55
}
```

### Generic Sorting with Custom Comparator

```rust
fn partition<T, F>(arr: &mut [T], compare: &F) -> usize
where F: Fn(&T, &T) -> bool
{
    let len = arr.len();
    let pivot_idx = len - 1;
    let mut store = 0;

    for i in 0..pivot_idx {
        if compare(&arr[i], &arr[pivot_idx]) {
            arr.swap(i, store);
            store += 1;
        }
    }
    arr.swap(store, pivot_idx);
    store
}

fn quicksort<T, F>(arr: &mut [T], compare: &F)
where F: Fn(&T, &T) -> bool
{
    if arr.len() <= 1 { return; }
    let p = partition(arr, compare);
    quicksort(&mut arr[..p], compare);
    if p + 1 < arr.len() {
        quicksort(&mut arr[p+1..], compare);
    }
}

fn main() {
    let mut nums = vec![3, 6, 8, 10, 1, 2, 1];
    quicksort(&mut nums, &|a, b| a < b);
    println!("Asc: {:?}", nums);  // [1, 1, 2, 3, 6, 8, 10]

    quicksort(&mut nums, &|a, b| a > b);
    println!("Desc: {:?}", nums); // [10, 8, 6, 3, 2, 1, 1]
}
```

---

## Appendix A: Quick Reference Card

```
FUNCTION TYPES DECISION TREE:
──────────────────────────────────────────────────────────────────

Start: What kind of callable do I need?
│
├─► Simple named, reusable logic?
│       └─► fn foo() {}                  ← regular function
│
├─► Need to capture environment?
│       └─► |x| x + captured_val        ← closure
│
├─► Execute at compile time?
│       └─► const fn foo() {}           ← const fn
│
├─► I/O or concurrency?
│       └─► async fn foo() {}           ← async fn
│
├─► Unsafe memory operations?
│       └─► unsafe fn foo() {}          ← unsafe fn
│
├─► Object behavior (methods)?
│       └─► impl Type { fn method(&self) {} }  ← method
│
├─► Factory / constructor?
│       └─► impl Type { fn new() -> Self {} }  ← associated fn
│
└─► Call function through variable?
        ├─► fn(i32)->i32                ← function pointer (no capture)
        └─► Box<dyn Fn(i32)->i32>       ← closure object (with capture)
```

---

## Appendix B: Common Patterns Summary

| Pattern                    | Code Snippet                                | Use Case                     |
|----------------------------|---------------------------------------------|------------------------------|
| Identity function          | `fn id<T>(x: T) -> T { x }`                | Generic pass-through         |
| Predicate function         | `fn is_even(n: i32) -> bool { n % 2 == 0 }`| Filter conditions            |
| Transformer function       | `fn double(x: i32) -> i32 { x * 2 }`       | Map operations               |
| Accumulator function       | `fn sum(a: i32, b: i32) -> i32 { a + b }`  | Fold/reduce operations       |
| Factory function           | `fn new_vec() -> Vec<i32> { vec![] }`       | Constructors                 |
| Curried function           | `fn add(n: i32) -> impl Fn(i32)->i32 {...}` | Partial application          |
| Memoized function          | `HashMap` cache pattern                     | Dynamic programming          |
| Recursive + base case      | `match n { 0 => base, _ => recurse }`       | Tree/list algorithms         |
| Early return               | `if cond { return val; } ... default`       | Guard clauses                |
| Callback/HOF               | `fn process(f: impl Fn(i32)->i32)`          | Strategy pattern             |

---

## Appendix C: Cognitive Mastery Framework

### Deliberate Practice for Functions

1. **Chunking** — Group related patterns (closures, HOF, generics) and practice each cluster until automatic
2. **Varied Practice** — Implement the same algorithm (binary search, merge sort) using: plain functions → generics → closures → HOF pipelines
3. **Retrieval Practice** — Write functions from memory, then check against the reference
4. **Interleaving** — Mix pattern types in practice sessions rather than blocking

### Mental Models to Build

```
MODEL 1: "Function as Transformation"
  Input set → [black box] → Output set
  Think about: What is the input space? What is the output space?

MODEL 2: "Ownership Flow"
  Who owns data entering a function? Who owns it leaving?
  &T (borrow) vs T (move) vs &mut T (exclusive borrow)

MODEL 3: "Lazy vs Eager"
  When does computation happen?
  Closures + iterators = lazy (no work until consumed)
  Regular function calls = eager (work happens immediately)

MODEL 4: "Stack vs Heap Decision"
  Fixed size + short-lived = stack (fast)
  Dynamic size + long-lived = heap (flexible but slower)
```

### The Expert's Pre-Coding Checklist

Before writing any function:
1. What is the **exact input type** and its ownership semantics?
2. What is the **exact output type** — does it own data or borrow?
3. Can this **fail** → Result/Option?
4. Can this be **generic** over types?
5. What is the **time complexity** of each branch?
6. Are there **edge cases** (empty input, overflow, negative numbers)?
7. Can this be **expressed as a pipeline** of simpler functions?

---

*"The master programmer is not one who memorizes syntax — but one who sees functions as mathematical transformations, composes them effortlessly, and reasons about their behavior the way a chess grandmaster sees the board."*

---

**End of Guide** | Rust Functions — Complete Reference
*Total coverage: 30 major topics, full implementations, DSA patterns, performance mental models*

Now let me build the full guide. This will be deeply comprehensive — give it a moment.Here's your complete Rust Functions master guide. Here's what's covered across **30 deep topics**:

**Foundations** — First-principles definition of functions, anatomy, naming conventions, the critical expressions-vs-statements distinction (with the semicolon trap), and the unit type `()`.

**Ownership & Parameters** — Pass-by-value vs `&T` vs `&mut T` with ownership flow diagrams, Copy vs Move types, and why Rust's mandatory type annotations are a feature not a burden.

**Advanced Function Types** — Every kind of callable: `const fn` (compile-time), `async fn` (futures), `unsafe fn` (raw power), `extern fn` (FFI/C interop), diverging functions (`!`), and nested functions.

**Closures** — The three closure traits (`Fn` / `FnMut` / `FnOnce`), the `move` keyword, returning closures, closure-as-state-machine, and function composition.

**Generics & Traits** — Generic functions, multiple trait bounds (`+`), `where` clauses, `impl Trait` vs `dyn Trait` with a dispatch cost table, and the monomorphization / zero-cost abstraction model.

**Lifetimes** — Lifetime annotation syntax, elision rules, `'static`, and lifetime in structs.

**DSA Patterns** — Generic binary search, merge sort, quicksort with custom comparator, BFS with HOF callback, memoized Fibonacci, and the iterative-DFS stack-overflow prevention technique.

**Mental Models** — Appendix C gives you the expert's pre-coding checklist, 4 core mental models, and a cognitive mastery framework (chunking, retrieval practice, interleaving) for accelerating mastery.