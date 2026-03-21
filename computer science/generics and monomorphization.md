# Generics and Monomorphization
## A World-Class DSA Deep Dive — Rust · Go · C

---

> *"The measure of intelligence is the ability to change."* — Albert Einstein  
> Generics are how a language lets one piece of code adapt to many types — intelligently, safely, and (in the best cases) without any runtime cost.

---

## Table of Contents

1. [The Problem Generics Solve](#1-the-problem-generics-solve)
2. [Core Vocabulary — Every Term Defined](#2-core-vocabulary)
3. [What Are Generics?](#3-what-are-generics)
4. [What Is Monomorphization?](#4-what-is-monomorphization)
5. [The Two Strategies: Static vs Dynamic Dispatch](#5-the-two-strategies-static-vs-dynamic-dispatch)
6. [Generics in Rust — Deep Dive](#6-generics-in-rust)
7. [Generics in Go — Deep Dive](#7-generics-in-go)
8. [Generics in C — Deep Dive](#8-generics-in-c)
9. [Memory Layout Comparison](#9-memory-layout-comparison)
10. [Performance Analysis](#10-performance-analysis)
11. [Decision Tree: Which Approach to Use](#11-decision-tree)
12. [Advanced Patterns](#12-advanced-patterns)
13. [Common Pitfalls](#13-common-pitfalls)
14. [Mental Models and Cognitive Strategies](#14-mental-models)

---

## 1. The Problem Generics Solve

Before generics existed, programmers faced a painful dilemma.

### The Dilemma — Concrete Example

Suppose you want a function that returns the **maximum** of two values.

**Without generics, you must write one function per type:**

```c
// C — without generics
int   max_int(int a, int b)       { return a > b ? a : b; }
float max_float(float a, float b) { return a > b ? a : b; }
char  max_char(char a, char b)    { return a > b ? a : b; }
// ... and so on for every type
```

```
PROBLEM SPACE (without generics)
─────────────────────────────────────────────────────────────
  Types:       int   float   char   double   int64  ...
  Operations:  max   min     swap   sort     find   ...

  Functions needed = |Types| × |Operations|
                   =    5   ×     5
                   =   25   functions  ← CODE EXPLOSION
─────────────────────────────────────────────────────────────
```

This violates **DRY** (Don't Repeat Yourself) — one of the most foundational principles in software engineering.

**The three bad alternatives (before generics):**

```
┌─────────────────────────────────────────────────────────────┐
│  OPTION 1: Copy-paste per type                              │
│  → Code duplication, maintenance nightmare, bugs multiply   │
├─────────────────────────────────────────────────────────────┤
│  OPTION 2: Use void* (C style) — one function, any pointer  │
│  → Type safety GONE, runtime errors, hard to debug          │
├─────────────────────────────────────────────────────────────┤
│  OPTION 3: Use a dynamic dispatch (virtual table / vtable)  │
│  → Runtime overhead, pointer indirection, cache misses      │
└─────────────────────────────────────────────────────────────┘
```

**Generics are the fourth option** — write once, compile to specialized code per type, zero runtime overhead, full type safety.

---

## 2. Core Vocabulary

Before going further, every term you will encounter is defined here precisely.

| Term | Plain English Definition |
|------|--------------------------|
| **Generic** | A placeholder for a type that is filled in later — like a variable, but for types |
| **Type Parameter** | The name of the placeholder (e.g., `T`, `U`, `K`) |
| **Instantiation** | The act of filling in a concrete type for a type parameter |
| **Monomorphization** | The compiler generating a *separate* specialized copy of code for each concrete type used |
| **Polymorphism** | One interface, many behaviors. Generics are *parametric polymorphism* |
| **Parametric Polymorphism** | Code that works uniformly for ANY type (generics) |
| **Ad-hoc Polymorphism** | Code that has different behavior per type (function overloading, traits, interfaces) |
| **Trait / Interface / Concept** | A contract that a type must fulfill to be used as a type parameter |
| **Bound / Constraint** | A restriction on what types a type parameter accepts (e.g., `T: Ord` means T must be orderable) |
| **Static Dispatch** | The compiler decides at compile time which code to call — zero runtime cost |
| **Dynamic Dispatch** | A pointer decides at runtime which code to call — small runtime cost |
| **Vtable** | A table of function pointers used for dynamic dispatch |
| **Type Erasure** | Discarding type info at compile time, keeping only behavior (Go interfaces, Java generics) |
| **Concrete Type** | An actual type like `i32`, `f64`, `String` — not a placeholder |
| **Code Bloat** | Monomorphization's downside: binary size grows because many specialized copies are compiled |
| **Zero-Cost Abstraction** | An abstraction that compiles down to code as efficient as handwritten specialized code |

---

## 3. What Are Generics?

A **generic** is a way to write code that is *parameterized over types*.

Think of it like a **template** or a **stencil** — the shape of the logic is fixed, but the type it operates on is left as a variable.

```
                    ANALOGY: Generic as a Stencil
    ┌───────────────────────────────────────────────────────────┐
    │                                                           │
    │   Stencil (generic code):   fn max<T>(a: T, b: T) -> T   │
    │                                      ↑                    │
    │                               type parameter              │
    │                               (the "hole" in stencil)     │
    │                                                           │
    │   Usage 1: max::<i32>(3, 5)  → fills hole with i32       │
    │   Usage 2: max::<f64>(3.0, 5.0) → fills hole with f64    │
    │   Usage 3: max::<char>('a','z') → fills hole with char   │
    │                                                           │
    └───────────────────────────────────────────────────────────┘
```

### The Generic Syntax Pattern (Universal)

Across all languages, generics follow the same conceptual pattern:

```
function_name<TypeParameter: Constraint>(arg: TypeParameter) -> TypeParameter
                ↑              ↑                ↑                    ↑
           placeholder    restriction      use the type         return it
```

---

## 4. What Is Monomorphization?

**Monomorphization** literally means: *"turning many morphs (shapes) into one morph."*

Wait — that sounds backwards. Let me explain:

- Your generic function is **polymorphic** (many shapes) — it works for many types
- The compiler creates **monomorphic** (one shape) versions for each concrete type you use
- The *process* of doing this is called **monomorphization**

### Visual Flow of Monomorphization

```
                        MONOMORPHIZATION FLOW
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │   SOURCE CODE (you write once):                             │
    │                                                              │
    │   fn add<T: Add>(a: T, b: T) -> T { a + b }                │
    │                                                              │
    │   fn main() {                                                │
    │       add(1_i32, 2_i32);      ← uses T = i32               │
    │       add(1.5_f64, 2.5_f64);  ← uses T = f64               │
    │       add(1_u8, 2_u8);        ← uses T = u8                │
    │   }                                                          │
    │                                                              │
    └──────────────────────────┬───────────────────────────────────┘
                               │
                               │  COMPILER RUNS
                               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │   COMPILED BINARY (compiler generates 3 functions):         │
    │                                                              │
    │   add_i32(a: i32, b: i32) -> i32 { a + b }  ← specialized  │
    │   add_f64(a: f64, b: f64) -> f64 { a + b }  ← specialized  │
    │   add_u8 (a: u8,  b: u8 ) -> u8  { a + b }  ← specialized  │
    │                                                              │
    │   Each call site is wired to its exact specialized version   │
    │   No runtime type checks. No indirection. Pure speed.        │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

### The Key Insight

> **Monomorphization = compile-time specialization.**  
> You pay the cost (larger binary, longer compile time) *once* at compile time.  
> At runtime, it's as if you had written separate functions by hand.

This is what Rust calls a **zero-cost abstraction** — the abstraction costs nothing at runtime.

---

## 5. The Two Strategies: Static vs Dynamic Dispatch

These are the two fundamental approaches to polymorphism. You must understand both before writing generics in any language.

```
                    ┌───────────────────────────────────────┐
                    │        POLYMORPHISM STRATEGIES        │
                    └──────────────────┬────────────────────┘
                                       │
                    ┌──────────────────┴────────────────────┐
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │  STATIC DISPATCH │                   │ DYNAMIC DISPATCH  │
           │  (Monomorphism)  │                   │  (Type Erasure)   │
           └────────┬─────────┘                   └─────────┬────────┘
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │ Resolved at:     │                   │ Resolved at:     │
           │ COMPILE TIME     │                   │ RUNTIME          │
           └────────┬─────────┘                   └─────────┬────────┘
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │ Mechanism:       │                   │ Mechanism:       │
           │ Separate machine │                   │ Vtable pointer   │
           │ code per type    │                   │ lookup           │
           └────────┬─────────┘                   └─────────┬────────┘
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │ Runtime cost:    │                   │ Runtime cost:    │
           │ ZERO             │                   │ 1 pointer deref  │
           └────────┬─────────┘                   └─────────┬────────┘
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │ Binary size:     │                   │ Binary size:     │
           │ LARGER           │                   │ SMALLER          │
           └────────┬─────────┘                   └─────────┬────────┘
                    │                                        │
           ┌────────▼─────────┐                   ┌─────────▼────────┐
           │ Example:         │                   │ Example:         │
           │ Rust generics    │                   │ Rust trait obj   │
           │ Go generics      │                   │ Go interfaces    │
           │ C macros         │                   │ C void*          │
           └──────────────────┘                   └──────────────────┘
```

### Dynamic Dispatch — How the Vtable Works

A **vtable** (virtual table) is a compiler-generated array of function pointers. Here is what it looks like in memory:

```
    OBJECT IN MEMORY (with dynamic dispatch):
    ┌─────────────────────────────────────────────────────────┐
    │  data pointer  │  vtable pointer ──────────────────────►│
    └────────────────┴────────────────                        │
                                                              ▼
                                              ┌───────────────────────────┐
                                              │         VTABLE            │
                                              ├───────────────────────────┤
                                              │  ptr to method_1()        │
                                              │  ptr to method_2()        │
                                              │  ptr to method_3()        │
                                              └───────────────────────────┘
    CALL SEQUENCE:
    1. Load vtable pointer from fat pointer
    2. Index into vtable to find function pointer
    3. Dereference function pointer
    4. Call the function
    Steps 1-3 are EXTRA work vs static dispatch
```

---

## 6. Generics in Rust — Deep Dive

Rust generics are **the most powerful** of the three languages covered here. They are:
- Fully monomorphized (zero runtime cost)
- Checked against **trait bounds** at compile time
- Can be used with structs, enums, functions, and `impl` blocks

### 6.1 Generic Functions

```rust
// ─────────────────────────────────────────────────────────────────
// BASIC GENERIC FUNCTION
// T is the type parameter
// PartialOrd is the TRAIT BOUND — T must support < and > comparison
// ─────────────────────────────────────────────────────────────────

fn largest<T: PartialOrd>(list: &[T]) -> &T {
//         ↑               ↑
//    type param     trait bound (constraint)
    let mut largest = &list[0];
    for item in list {
        if item > largest {  // only works because T: PartialOrd
            largest = item;
        }
    }
    largest
}

fn main() {
    let numbers = vec![10, 40, 25, 3, 99];
    println!("Largest number: {}", largest(&numbers));  // T = i32

    let chars = vec!['y', 'm', 'a', 'q'];
    println!("Largest char: {}", largest(&chars));  // T = char
}
```

**What the compiler generates (monomorphization):**

```
  SOURCE           COMPILER            BINARY
  ────────         ─────────           ──────────────────────────────────
  largest<T>  ──►  monomorphize  ──►   largest_i32(&[i32]) -> &i32
                                       largest_char(&[char]) -> &char
```

### 6.2 Generic Structs

```rust
// ─────────────────────────────────────────────────────────────────
// GENERIC STRUCT
// Point<T> works for any type T
// ─────────────────────────────────────────────────────────────────

#[derive(Debug)]
struct Point<T> {
    x: T,
    y: T,
}

// impl block also has type parameter
impl<T> Point<T> {
    fn new(x: T, y: T) -> Self {
        Point { x, y }
    }

    fn x(&self) -> &T {
        &self.x
    }
}

// You can also add methods ONLY for specific concrete types
impl Point<f64> {
    // This method ONLY exists for Point<f64>, not Point<i32>
    fn distance_from_origin(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}

fn main() {
    let int_point = Point::new(5, 10);         // T inferred as i32
    let float_point = Point::new(1.0, 4.0);    // T inferred as f64
    
    println!("int_point: {:?}", int_point);
    println!("float_point distance: {}", float_point.distance_from_origin());
    // int_point.distance_from_origin(); // ERROR: only exists for f64
}
```

### 6.3 Multiple Type Parameters

```rust
// A struct with TWO independent type parameters
#[derive(Debug)]
struct Pair<A, B> {
    first: A,
    second: B,
}

impl<A, B> Pair<A, B> {
    fn new(first: A, second: B) -> Self {
        Pair { first, second }
    }
}

// Works for completely different types
let pair = Pair::new(42_i32, "hello");  // A=i32, B=&str
let pair2 = Pair::new(true, 3.14_f64); // A=bool, B=f64
```

### 6.4 Generic Enums

You've already used these! The most famous generic enums in Rust:

```rust
// ─────────────────────────────────────────────────────────────────
// FROM THE RUST STANDARD LIBRARY (simplified)
// ─────────────────────────────────────────────────────────────────

enum Option<T> {
    Some(T),   // holds a value of type T
    None,      // holds no value
}
// Option<i32>::Some(5)     → T = i32
// Option<String>::Some(..) → T = String
// Option<T>::None          → works for any T

enum Result<T, E> {
    Ok(T),    // success value of type T
    Err(E),   // error value of type E
}
// Result<i32, String>   → success=i32, error=String
// Result<Vec<u8>, io::Error> → success=Vec<u8>, error=io::Error
```

### 6.5 Trait Bounds — The Constraint System

A **trait bound** tells the compiler: *"T must implement this trait."*

Think of traits as contracts — a guarantee that certain operations exist on T.

```rust
// ─────────────────────────────────────────────────────────────────
// MULTIPLE TRAIT BOUNDS with + syntax
// ─────────────────────────────────────────────────────────────────

use std::fmt::{Debug, Display};

fn print_and_compare<T: Debug + Display + PartialOrd>(a: T, b: T) {
//                      ↑         ↑            ↑
//                   can print  can format   can compare
    println!("Debug:   {:?}", a);
    println!("Display: {}", a);
    if a > b {
        println!("a is larger");
    }
}

// ─────────────────────────────────────────────────────────────────
// WHERE CLAUSE — cleaner syntax for complex bounds
// ─────────────────────────────────────────────────────────────────

fn complex_function<T, U>(t: &T, u: &U) -> String
where
    T: Display + Clone,
    U: Debug + Clone,
{
    format!("t={}, u={:?}", t, u)
}
```

### 6.6 The `where` Clause Flow

```
    FUNCTION SIGNATURE DECISION FLOW
    ──────────────────────────────────────────────────────────────
    
    Q: How many type parameters?
         │
         ├── 1 type param, 1-2 bounds?
         │       └── Use inline: fn f<T: Bound1 + Bound2>(...)
         │
         └── 2+ type params or 3+ bounds?
                 └── Use where clause:
                     fn f<T, U>(...)
                     where
                         T: Bound1 + Bound2,
                         U: Bound3,
                     {...}
    ──────────────────────────────────────────────────────────────
```

### 6.7 Generic Functions with Lifetimes (Advanced)

```rust
// ─────────────────────────────────────────────────────────────────
// LIFETIME PARAMETER 'a + GENERIC TYPE PARAMETER T
// 'a = a lifetime (how long a reference is valid)
// ─────────────────────────────────────────────────────────────────

fn longest_with_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() { x } else { y }
}
```

### 6.8 Monomorphization Proof — Inspect with `cargo expand`

```rust
// What you write:
fn double<T: std::ops::Mul<Output = T> + Copy>(x: T) -> T {
    x * x
}

fn main() {
    double(3_i32);
    double(2.5_f64);
}

// ─────────────────────────────────────────────────────────────────
// What the compiler effectively produces (pseudo-code):
// ─────────────────────────────────────────────────────────────────
//
// fn double_i32(x: i32) -> i32 { x * x }
// fn double_f64(x: f64) -> f64 { x * x }
//
// fn main() {
//     double_i32(3);
//     double_f64(2.5);
// }
// ─────────────────────────────────────────────────────────────────
```

### 6.9 Dynamic Dispatch — The Alternative (`dyn Trait`)

When you do NOT want monomorphization, use trait objects:

```rust
// ─────────────────────────────────────────────────────────────────
// STATIC DISPATCH (monomorphized, zero runtime cost)
// ─────────────────────────────────────────────────────────────────
fn static_speak<T: Animal>(animal: &T) {
    animal.speak();  // resolved at compile time
}

// ─────────────────────────────────────────────────────────────────
// DYNAMIC DISPATCH (vtable, small runtime cost, smaller binary)
// ─────────────────────────────────────────────────────────────────
fn dynamic_speak(animal: &dyn Animal) {
    animal.speak();  // resolved at runtime via vtable
}

// ─────────────────────────────────────────────────────────────────
// WHEN TO USE EACH:
// ─────────────────────────────────────────────────────────────────
//
//  Use static (generics):        Use dynamic (dyn Trait):
//  ─────────────────────         ───────────────────────
//  Performance critical          Heterogeneous collections
//  Types known at compile time   Types not known at compile time
//  No heap allocation needed     Plugin systems / extensibility
//  Tight inner loops             Binary size matters more
```

### 6.10 The Rust Generics Memory Model

```
    STATIC DISPATCH — MEMORY MODEL
    ──────────────────────────────────────────────────────────────
    
    Call: largest(&[1, 2, 3])   → calls largest_i32 directly
    
    Stack frame:
    ┌──────────────────────────────┐
    │  largest_i32                 │
    │  ┌──────────────────────┐    │
    │  │ list: &[i32]         │    │  ← concrete type, known at compile
    │  │ largest: &i32        │    │
    │  └──────────────────────┘    │
    └──────────────────────────────┘
    
    NO indirection. NO vtable. NO heap allocation.
    
    ──────────────────────────────────────────────────────────────
    
    DYNAMIC DISPATCH — MEMORY MODEL
    ──────────────────────────────────────────────────────────────
    
    Call: dynamic_speak(animal)  → fat pointer lookup
    
    Fat pointer (2 words):
    ┌────────────────┬──────────────────┐
    │  data ptr ────►│ actual struct    │
    │                │ in memory        │
    ├────────────────┴──────────────────┘
    │  vtable ptr ──►┌──────────────────┐
    │                │  speak() ptr     │
    │                │  drop() ptr      │
    │                │  size/align      │
    └────────────────└──────────────────┘
```

---

## 7. Generics in Go — Deep Dive

Go added generics in **version 1.18 (March 2022)** — a major milestone after years of debate. Go's generics use **type parameters with constraints**.

### 7.1 Basic Generic Function

```go
package main

import "fmt"

// ─────────────────────────────────────────────────────────────────
// GENERIC FUNCTION IN GO
// [T comparable] is the type parameter list
// comparable = built-in constraint: T supports == and !=
// ─────────────────────────────────────────────────────────────────

func Contains[T comparable](slice []T, item T) bool {
//           ↑↑↑↑↑↑↑↑↑↑↑↑↑
//           type parameter list in square brackets
    for _, v := range slice {
        if v == item {  // works because T: comparable
            return true
        }
    }
    return false
}

func main() {
    ints := []int{1, 2, 3, 4, 5}
    fmt.Println(Contains(ints, 3))        // T inferred as int
    fmt.Println(Contains(ints, 6))

    strs := []string{"go", "rust", "c"}
    fmt.Println(Contains(strs, "rust"))   // T inferred as string
}
```

### 7.2 Type Constraints — The `constraints` Package and Custom Interfaces

In Go, **constraints are interfaces**. An interface used as a constraint specifies which types T can be.

```go
package main

import (
    "fmt"
    "golang.org/x/exp/constraints"  // experimental package
)

// ─────────────────────────────────────────────────────────────────
// USING BUILT-IN CONSTRAINTS
// constraints.Ordered = all types that support < > <= >=
// ─────────────────────────────────────────────────────────────────

func Min[T constraints.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

// ─────────────────────────────────────────────────────────────────
// DEFINING YOUR OWN CONSTRAINT
// Use a union of types with |
// ─────────────────────────────────────────────────────────────────

type Number interface {
    int | int8 | int16 | int32 | int64 |
    float32 | float64
}

func Sum[T Number](nums []T) T {
    var total T  // zero value of T
    for _, n := range nums {
        total += n
    }
    return total
}

// ─────────────────────────────────────────────────────────────────
// TILDE ~ means "underlying type is T"
// This allows user-defined types based on int to also qualify
// ─────────────────────────────────────────────────────────────────

type Celsius float64     // user-defined type with underlying float64
type Fahrenheit float64

type Temperature interface {
    ~float64  // T's underlying type must be float64
}

func AbsTemp[T Temperature](t T) T {
    if t < 0 {
        return -t
    }
    return t
}

func main() {
    fmt.Println(Min(3, 5))              // T = int
    fmt.Println(Min(3.14, 2.71))       // T = float64
    fmt.Println(Sum([]int{1, 2, 3}))   // T = int

    var c Celsius = -37.5
    fmt.Println(AbsTemp(c))  // T = Celsius, works because ~float64
}
```

### 7.3 Generic Structs in Go

```go
// ─────────────────────────────────────────────────────────────────
// GENERIC STACK DATA STRUCTURE
// ─────────────────────────────────────────────────────────────────

type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
    if len(s.items) == 0 {
        var zero T  // return zero value of T
        return zero, false
    }
    top := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return top, true
}

func (s *Stack[T]) Peek() (T, bool) {
    if len(s.items) == 0 {
        var zero T
        return zero, false
    }
    return s.items[len(s.items)-1], true
}

func (s *Stack[T]) Size() int {
    return len(s.items)
}

func main() {
    // Stack of integers
    intStack := &Stack[int]{}
    intStack.Push(1)
    intStack.Push(2)
    intStack.Push(3)
    
    if top, ok := intStack.Pop(); ok {
        fmt.Println("Popped:", top)  // 3
    }
    
    // Stack of strings — same code, different type
    strStack := &Stack[string]{}
    strStack.Push("hello")
    strStack.Push("world")
    
    if top, ok := strStack.Pop(); ok {
        fmt.Println("Popped:", top)  // "world"
    }
}
```

### 7.4 Multiple Type Parameters in Go

```go
// ─────────────────────────────────────────────────────────────────
// GENERIC MAP FUNCTION (functional programming style)
// Takes a slice of one type, returns slice of another type
// ─────────────────────────────────────────────────────────────────

func Map[A, B any](slice []A, f func(A) B) []B {
//       ↑  ↑
//  two type parameters: A (input type), B (output type)
    result := make([]B, len(slice))
    for i, v := range slice {
        result[i] = f(v)
    }
    return result
}

// ─────────────────────────────────────────────────────────────────
// GENERIC FILTER FUNCTION
// ─────────────────────────────────────────────────────────────────

func Filter[T any](slice []T, predicate func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if predicate(v) {
            result = append(result, v)
        }
    }
    return result
}

// ─────────────────────────────────────────────────────────────────
// GENERIC REDUCE FUNCTION
// ─────────────────────────────────────────────────────────────────

func Reduce[T, Acc any](slice []T, initial Acc, f func(Acc, T) Acc) Acc {
    acc := initial
    for _, v := range slice {
        acc = f(acc, v)
    }
    return acc
}

func main() {
    nums := []int{1, 2, 3, 4, 5}
    
    // Map: int → string
    strs := Map(nums, func(n int) string {
        return fmt.Sprintf("(%d)", n)
    })
    fmt.Println(strs)  // [(1) (2) (3) (4) (5)]
    
    // Filter: keep even numbers
    evens := Filter(nums, func(n int) bool { return n%2 == 0 })
    fmt.Println(evens)  // [2 4]
    
    // Reduce: sum
    sum := Reduce(nums, 0, func(acc, n int) int { return acc + n })
    fmt.Println(sum)  // 15
}
```

### 7.5 Go's Approach: GC Shapes and Partial Monomorphization

Go does NOT do full monomorphization like Rust. Instead, Go uses a hybrid approach called **GC shapes (Garbage Collector shapes)**:

```
    GO's GC SHAPE STRATEGY
    ──────────────────────────────────────────────────────────────
    
    All pointer types share ONE instantiation:
    
        Stack[*Dog]    ──►  shared code (pointer-shaped)
        Stack[*Cat]    ──►  shared code (pointer-shaped)
        Stack[*int]    ──►  shared code (pointer-shaped)
    
    Primitive types get separate instantiations:
    
        Stack[int]     ──►  separate code (int-shaped, 8 bytes)
        Stack[float64] ──►  separate code (float64-shaped, 8 bytes)
        Stack[int32]   ──►  separate code (int32-shaped, 4 bytes)
    
    ──────────────────────────────────────────────────────────────
    
    WHY?
    All pointers are the same size (8 bytes on 64-bit).
    Sharing the code for all pointer types = less code bloat.
    A runtime "dictionary" carries type info for pointer types.
    
    RESULT:
    Go trades some performance (dictionary overhead for pointers)
    for smaller binary size.
    Rust trades binary size for maximum performance.
    
    ──────────────────────────────────────────────────────────────
```

### 7.6 Go Interfaces vs Go Generics — When to Use Which

```
    DECISION: Interface OR Generic?
    ──────────────────────────────────────────────────────────────
    
    You need to store different types in one collection?
         ├── YES → Interface (dynamic dispatch)
         └── NO  → Continue...
    
    You need runtime polymorphism (type unknown until runtime)?
         ├── YES → Interface
         └── NO  → Continue...
    
    You're writing a type-safe algorithm that works on any T?
         ├── YES → Generic
         └── NO  → Continue...
    
    You need performance in a hot path?
         ├── YES → Generic (avoids interface boxing overhead)
         └── NO  → Either works; interface may be simpler
    
    ──────────────────────────────────────────────────────────────
    
    CONCRETE EXAMPLES:
    
    Use Interface:
        io.Reader — heterogeneous: files, bytes, network
        sort.Interface — different types, sorted differently
        http.Handler — different handler structs, one behavior
    
    Use Generic:
        Min[T]/Max[T] — same algorithm, different numeric types
        Stack[T] — container type parameterized on element type
        Map/Filter/Reduce — functional combinators
    
    ──────────────────────────────────────────────────────────────
```

---

## 8. Generics in C — Deep Dive

C has no native generic system. Instead, it offers **three mechanisms** to simulate generics, each with different trade-offs.

### 8.1 Mechanism 1: Function-like Macros

Macros do **textual substitution** before compilation. They are the most primitive form of "generics" in C.

```c
#include <stdio.h>

// ─────────────────────────────────────────────────────────────────
// MACRO-BASED GENERIC MAX
// Works for any type that supports the > operator
// ─────────────────────────────────────────────────────────────────

#define MAX(a, b) ((a) > (b) ? (a) : (b))
// ↑ parentheses around everything prevent operator precedence bugs

// Usage:
int main() {
    printf("%d\n", MAX(3, 5));          // int
    printf("%f\n", MAX(3.14, 2.71));    // double
    printf("%c\n", MAX('a', 'z'));      // char

    // ─────────────────────────────────────────────────────────────
    // WARNING: MACRO PITFALL — double evaluation
    // ─────────────────────────────────────────────────────────────
    int x = 5;
    int result = MAX(x++, 3);
    // Expands to: ((x++) > (3) ? (x++) : (3))
    //                                ↑
    //               x gets incremented TWICE! Bug!
    printf("x = %d\n", x);  // x = 7, not 6 as you might expect
    return 0;
}
```

**Macro expansion visualization:**

```
    SOURCE:        MAX(x++, 3)
    
    EXPANSION:     ((x++) > (3) ? (x++) : (3))
                     ↑                ↑
                 1st eval          2nd eval (side effect runs twice!)
    
    THIS IS NOT TRUE GENERICS — it's text substitution.
    The compiler never sees "MAX", only the expanded form.
```

### 8.2 Mechanism 2: `void*` — Type-Erased Generics

`void*` is a pointer to "unknown type". It can point to anything.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ─────────────────────────────────────────────────────────────────
// GENERIC SWAP using void* and element size
// ─────────────────────────────────────────────────────────────────

void generic_swap(void *a, void *b, size_t size) {
    void *temp = malloc(size);   // allocate temporary buffer
    if (!temp) return;
    memcpy(temp, a, size);       // temp = *a
    memcpy(a, b, size);          // *a = *b
    memcpy(b, temp, size);       // *b = temp
    free(temp);
}

// ─────────────────────────────────────────────────────────────────
// GENERIC ARRAY FIND using void* and a comparator function
// qsort-style: takes a function pointer for comparison
// ─────────────────────────────────────────────────────────────────

void* generic_find(
    const void *array,      // pointer to first element
    size_t count,           // number of elements
    size_t elem_size,       // size of each element in bytes
    const void *target,     // what to find
    int (*cmp)(const void*, const void*)  // comparator function pointer
) {
    const char *ptr = (const char*)array;  // byte pointer for arithmetic
    for (size_t i = 0; i < count; i++) {
        if (cmp(ptr + i * elem_size, target) == 0) {
            return (void*)(ptr + i * elem_size);  // found
        }
    }
    return NULL;  // not found
}

// Comparator for int
int cmp_int(const void *a, const void *b) {
    return *(const int*)a - *(const int*)b;
}

int main() {
    int a = 10, b = 20;
    printf("Before swap: a=%d, b=%d\n", a, b);
    generic_swap(&a, &b, sizeof(int));
    printf("After swap:  a=%d, b=%d\n", a, b);

    double x = 3.14, y = 2.71;
    generic_swap(&x, &y, sizeof(double));
    printf("After swap:  x=%f, y=%f\n", x, y);

    int arr[] = {10, 20, 30, 40, 50};
    int target = 30;
    int *found = (int*)generic_find(arr, 5, sizeof(int), &target, cmp_int);
    if (found) printf("Found: %d\n", *found);

    return 0;
}
```

**The `void*` memory model:**

```
    void* LAYOUT
    ──────────────────────────────────────────────────────────────
    
    int array[3] = {10, 20, 30};
    void *ptr = array;
    
    Memory:
    ┌────────┬────────┬────────┐
    │  10    │  20    │  30    │  ← int values (4 bytes each)
    └────────┴────────┴────────┘
    ↑
    ptr (void*)  — the compiler has FORGOTTEN this is int*
    
    To access element 1, you MUST know elem_size:
    char *byte_ptr = (char*)ptr;
    int *elem1 = (int*)(byte_ptr + 1 * sizeof(int));  // manual arithmetic
    
    ── The type info is GONE from the pointer. You carry it yourself.
    ── This is "type erasure" in C — manual and dangerous.
    ──────────────────────────────────────────────────────────────
```

### 8.3 Mechanism 3: `_Generic` — Compile-Time Type Selection (C11)

`_Generic` is a **compile-time switch on type**. It was introduced in C11.

```c
#include <stdio.h>
#include <math.h>

// ─────────────────────────────────────────────────────────────────
// _Generic SYNTAX:
//   _Generic(expression, type1: result1, type2: result2, default: resultN)
//
// The expression is NOT evaluated — only its TYPE matters.
// Think of it as a compile-time if-else on type.
// ─────────────────────────────────────────────────────────────────

// Generic absolute value — selects the right function at compile time
#define ABS(x) _Generic((x),    \
    int:    abs,                 \
    long:   labs,                \
    float:  fabsf,               \
    double: fabs                 \
)(x)
// ↑ The selected function name is immediately called with (x)

// Generic type name (useful for debugging)
#define TYPE_NAME(x) _Generic((x),  \
    int:    "int",                   \
    float:  "float",                 \
    double: "double",                \
    char:   "char",                  \
    default:"unknown"                \
)

// Generic print
#define PRINT(x) _Generic((x),       \
    int:    printf("%d\n", (x)),     \
    float:  printf("%f\n", (x)),     \
    double: printf("%lf\n", (x)),    \
    char:   printf("%c\n", (x)),     \
    char*:  printf("%s\n", (x))      \
)

int main() {
    printf("ABS(-5)   = %d\n",    ABS(-5));        // calls abs()
    printf("ABS(-3.14) = %f\n",   ABS(-3.14));     // calls fabs()
    printf("ABS(-2.5f) = %f\n",   ABS(-2.5f));     // calls fabsf()

    printf("Type of 5:   %s\n",   TYPE_NAME(5));
    printf("Type of 5.0: %s\n",   TYPE_NAME(5.0));
    printf("Type of 'a': %s\n",   TYPE_NAME('a'));

    PRINT(42);          // prints "42"
    PRINT(3.14);        // prints "3.140000"
    PRINT("hello");     // prints "hello"
    return 0;
}
```

### 8.4 Mechanism 4: X-Macros for Type-Stamped Code Generation

This is an advanced C pattern that generates separate typed functions via the preprocessor.

```c
// ─────────────────────────────────────────────────────────────────
// X-MACRO PATTERN: define a list of types once, use it everywhere
// ─────────────────────────────────────────────────────────────────

// Step 1: Define your "type list"
#define TYPE_LIST \
    X(int,    Int)    \
    X(double, Double) \
    X(float,  Float)

// Step 2: Generate a stack struct for each type
#define STACK_SIZE 100

#define X(type, Name)              \
typedef struct {                   \
    type items[STACK_SIZE];        \
    int top;                       \
} Stack_##Name;                    \
                                   \
void Stack_##Name##_push(Stack_##Name *s, type item) { \
    if (s->top < STACK_SIZE) s->items[s->top++] = item; \
}                                  \
                                   \
type Stack_##Name##_pop(Stack_##Name *s) { \
    return s->items[--s->top];     \
}

TYPE_LIST
#undef X

// After preprocessing, this generates:
//   typedef struct { int    items[100]; int top; } Stack_Int;
//   typedef struct { double items[100]; int top; } Stack_Double;
//   typedef struct { float  items[100]; int top; } Stack_Float;
//   ... plus push/pop for each

int main() {
    Stack_Int si = {.top = 0};
    Stack_Int_push(&si, 42);
    printf("Popped: %d\n", Stack_Int_pop(&si));

    Stack_Double sd = {.top = 0};
    Stack_Double_push(&sd, 3.14);
    printf("Popped: %f\n", Stack_Double_pop(&sd));
    return 0;
}
```

### 8.5 C Generics Comparison Table

```
    C GENERICS MECHANISM COMPARISON
    ──────────────────────────────────────────────────────────────────
    Mechanism    │ Type Safe │ Readable │ Debug  │ Overhead │ Use When
    ─────────────┼───────────┼──────────┼────────┼──────────┼─────────
    Macros       │ NO        │ OK       │ Hard   │ None     │ Simple ops
    void*        │ NO        │ Verbose  │ Hard   │ Runtime  │ C stdlib style
    _Generic     │ YES       │ Good     │ OK     │ None     │ Type dispatch
    X-Macros     │ YES       │ Strange  │ Medium │ None     │ Code gen
    ──────────────────────────────────────────────────────────────────
```

---

## 9. Memory Layout Comparison

Understanding how generics affect memory is crucial for writing high-performance code.

### 9.1 Stack vs Heap for Generic Types

```
    RUST — Generic<i32> on stack (no heap allocation needed)
    ──────────────────────────────────────────────────────────────
    
    let p: Point<i32> = Point { x: 3, y: 7 };
    
    Stack:
    ┌─────────────────────────────┐
    │  x: i32 = 3  (4 bytes)      │
    │  y: i32 = 7  (4 bytes)      │
    └─────────────────────────────┘
    Total: 8 bytes, NO heap, NO indirection
    
    ──────────────────────────────────────────────────────────────
    
    RUST — Box<dyn Trait> — fat pointer on stack, data on heap
    ──────────────────────────────────────────────────────────────
    
    let animal: Box<dyn Animal> = Box::new(Dog { ... });
    
    Stack (fat pointer, 16 bytes):
    ┌─────────────────────────────┐
    │  data ptr (8 bytes) ──────────────────────────────►┐ heap
    │  vtable ptr (8 bytes) ────────────────────────►┐   │
    └─────────────────────────────┘                  │   │
                                                     │   ▼
                                 vtable:             │  ┌────────────┐
                                 ┌──────────────┐    │  │ Dog { ... }│
                                 │ speak() ─────┼────┘  └────────────┘
                                 │ drop()       │
                                 │ size = N     │
                                 └──────────────┘
    
    Total: 16 bytes on stack + heap allocation + vtable
    
    ──────────────────────────────────────────────────────────────
```

### 9.2 Code Size Impact of Monomorphization

```
    BINARY SIZE GROWTH WITH MONOMORPHIZATION
    ──────────────────────────────────────────────────────────────
    
    Generic function: largest<T>()  (let's say 50 bytes of machine code)
    
    Used with: i32, f64, u8, String, char (5 types)
    
    Binary contains:
    ┌──────────────────────┬──────────────┐
    │ largest_i32          │  50 bytes    │
    ├──────────────────────┼──────────────┤
    │ largest_f64          │  50 bytes    │
    ├──────────────────────┼──────────────┤
    │ largest_u8           │  50 bytes    │
    ├──────────────────────┼──────────────┤
    │ largest_String       │  60 bytes    │  (String comparison is bigger)
    ├──────────────────────┼──────────────┤
    │ largest_char         │  50 bytes    │
    └──────────────────────┴──────────────┘
    Total: ~260 bytes for one generic function used 5 times
    
    With dyn Trait (dynamic dispatch):
    ┌──────────────────────┬──────────────┐
    │ dynamic_largest      │  55 bytes    │  (+ vtable lookup overhead)
    └──────────────────────┴──────────────┘
    Total: ~55 bytes (but runtime cost per call)
    
    ── This is the CORE TRADE-OFF: binary size vs runtime speed
    ──────────────────────────────────────────────────────────────
```

---

## 10. Performance Analysis

### 10.1 Benchmarking Monomorphized vs Dynamic Dispatch

```rust
// ─────────────────────────────────────────────────────────────────
// BENCHMARK: Static (monomorphized) vs Dynamic dispatch
// ─────────────────────────────────────────────────────────────────

trait Compute {
    fn compute(&self, x: f64) -> f64;
}

struct Square;
impl Compute for Square {
    fn compute(&self, x: f64) -> f64 { x * x }
}

// STATIC — compiler inlines the call, may SIMD-vectorize
fn run_static<C: Compute>(c: &C, values: &[f64]) -> f64 {
    values.iter().map(|&x| c.compute(x)).sum()
}

// DYNAMIC — vtable lookup per call, cannot inline, no vectorization
fn run_dynamic(c: &dyn Compute, values: &[f64]) -> f64 {
    values.iter().map(|&x| c.compute(x)).sum()
}

// In hot loops with millions of iterations:
// run_static can be 3-10x faster due to:
//   1. No vtable indirection
//   2. Inlining (compute() body merged into caller)
//   3. Auto-vectorization (SIMD instructions)
//   4. Better cache behavior (no data pointer derefs)
```

### 10.2 Assembly Difference (Conceptual)

```
    STATIC DISPATCH — x86-64 assembly (simplified)
    ──────────────────────────────────────────────────────────────
    ; compute() is INLINED — no function call overhead
    vmulsd  xmm0, xmm0, xmm0    ; x * x directly in register
    addsd   xmm1, xmm0           ; accumulate
    ; The entire loop body fits in ~3-5 instructions
    ; CPU can pipeline and predict perfectly
    ──────────────────────────────────────────────────────────────
    
    DYNAMIC DISPATCH — x86-64 assembly (simplified)
    ──────────────────────────────────────────────────────────────
    mov     rax, [rdi + 8]       ; load vtable pointer
    mov     rax, [rax]           ; load function pointer from vtable
    call    rax                  ; indirect call (branch predictor struggles)
    ; The indirect call means:
    ;   - Cannot inline
    ;   - Branch misprediction possible
    ;   - CPU stall waiting for pointer value
    ──────────────────────────────────────────────────────────────
```

### 10.3 When Does the Trade-off Matter?

```
    PERFORMANCE IMPACT SCALE
    ──────────────────────────────────────────────────────────────
    
    SITUATION                      IMPACT OF DYNAMIC DISPATCH
    ─────────────────────────────  ───────────────────────────
    Single call                    Negligible (~1-5 ns)
    Thousands of calls             Small (~1% slower)
    Millions of calls in hot loop  Significant (5-40% slower)
    SIMD-critical math loops       Very significant (2-10x slower)
    
    ── Rule of thumb: Optimize generics to static dispatch ONLY
    ── when profiling shows the vtable overhead is a bottleneck.
    ── Premature optimization kills readability first.
    ──────────────────────────────────────────────────────────────
```

---

## 11. Decision Tree

Use this decision tree to choose your approach for any generic programming situation.

```
    GENERIC PROGRAMMING DECISION TREE
    ══════════════════════════════════════════════════════════════
    
    START: I need code that works with multiple types
    │
    ├── Am I writing in RUST?
    │   │
    │   ├── Is the concrete type known at compile time?
    │   │   ├── YES: Use fn foo<T: Bound>(...)
    │   │   │           → Monomorphized, zero-cost
    │   │   │
    │   │   └── NO: Do I need a heterogeneous collection?
    │   │           ├── YES: Use Vec<Box<dyn Trait>>
    │   │           │           → Dynamic dispatch, heap alloc
    │   │           │
    │   │           └── NO: Return value of unknown type?
    │   │                   ├── YES: Use Box<dyn Trait> return
    │   │                   └── NO:  Re-evaluate the problem
    │   │
    │   └── Do I need different behavior per type?
    │           └── YES: Implement separate trait impls for each type
    │
    ├── Am I writing in GO?
    │   │
    │   ├── Can I express the constraint as a type union?
    │   │   ├── YES: Use generics [T int|float64|...]
    │   │   └── NO:
    │   │
    │   ├── Is this a container/algorithm (same behavior, any type)?
    │   │   ├── YES: Use generics [T any] or [T comparable]
    │   │   └── NO:
    │   │
    │   └── Is this behavior-based (different types, same method)?
    │           ├── YES: Use interface (dynamic dispatch)
    │           └── NO:  Rethink your abstraction
    │
    └── Am I writing in C?
        │
        ├── Simple arithmetic ops (max/min/swap)?
        │   └── Use function-like macros (watch for side effects!)
        │
        ├── Need type-safe dispatch at compile time (C11)?
        │   └── Use _Generic
        │
        ├── Need a generic container (stack/queue/list)?
        │   └── Use void* + size OR X-macros
        │
        └── Need full type safety in a generic container?
                └── X-macros (generates typed code per type)
    
    ══════════════════════════════════════════════════════════════
```

---

## 12. Advanced Patterns

### 12.1 Rust — Const Generics (Generics over Values)

Rust supports generics not just over types, but over **constant values** (integers, booleans).

```rust
// ─────────────────────────────────────────────────────────────────
// CONST GENERICS: N is a compile-time constant integer
// ─────────────────────────────────────────────────────────────────

struct Matrix<T, const ROWS: usize, const COLS: usize> {
    data: [[T; COLS]; ROWS],
}

impl<T: Copy + Default, const ROWS: usize, const COLS: usize>
    Matrix<T, ROWS, COLS>
{
    fn new() -> Self {
        Matrix {
            data: [[T::default(); COLS]; ROWS],
        }
    }

    fn get(&self, row: usize, col: usize) -> T {
        self.data[row][col]
    }
}

// ─────────────────────────────────────────────────────────────────
// DIFFERENT SIZES = DIFFERENT TYPES at compile time
// Cannot accidentally add a 3x3 matrix to a 2x4 matrix
// ─────────────────────────────────────────────────────────────────

fn main() {
    let m1: Matrix<f64, 3, 3> = Matrix::new();  // 3×3 matrix of f64
    let m2: Matrix<i32, 2, 4> = Matrix::new();  // 2×4 matrix of i32
    // m1 and m2 are incompatible types — cannot mix them up!
}
```

**The power here:**

```
    Matrix<f64, 3, 3>   ──► monomorphized as a completely separate type
    Matrix<f64, 2, 4>   ──► another type — cannot be accidentally confused
    
    This gives you COMPILE-TIME DIMENSIONAL ANALYSIS:
    adding a 3x3 + 4x4 matrix = COMPILE ERROR, not a runtime bug
```

### 12.2 Rust — Higher-Kinded Types via Associated Types

```rust
// ─────────────────────────────────────────────────────────────────
// ASSOCIATED TYPES — a cleaner way to bind output types to traits
// ─────────────────────────────────────────────────────────────────

trait Transform {
    type Input;   // associated type (like a generic within the trait)
    type Output;

    fn transform(&self, input: Self::Input) -> Self::Output;
}

struct Doubler;

impl Transform for Doubler {
    type Input = i32;
    type Output = i64;

    fn transform(&self, input: i32) -> i64 {
        input as i64 * 2
    }
}

struct Stringifier;

impl Transform for Stringifier {
    type Input = f64;
    type Output = String;

    fn transform(&self, input: f64) -> String {
        format!("{:.2}", input)
    }
}

fn apply<T: Transform>(transformer: &T, value: T::Input) -> T::Output {
    transformer.transform(value)
}
```

### 12.3 Go — Generic Ordered Map

```go
// ─────────────────────────────────────────────────────────────────
// A sorted map using generics
// ─────────────────────────────────────────────────────────────────

import "golang.org/x/exp/constraints"

type SortedMap[K constraints.Ordered, V any] struct {
    keys   []K
    values map[K]V
}

func NewSortedMap[K constraints.Ordered, V any]() *SortedMap[K, V] {
    return &SortedMap[K, V]{
        values: make(map[K]V),
    }
}

func (m *SortedMap[K, V]) Set(key K, value V) {
    if _, exists := m.values[key]; !exists {
        // Insert key in sorted order
        i := sort.Search(len(m.keys), func(i int) bool {
            return m.keys[i] >= key
        })
        m.keys = append(m.keys, key)
        copy(m.keys[i+1:], m.keys[i:])
        m.keys[i] = key
    }
    m.values[key] = value
}

func (m *SortedMap[K, V]) Keys() []K {
    return m.keys
}
```

### 12.4 C — Type-Safe Generic Vector with X-Macros

```c
// ─────────────────────────────────────────────────────────────────
// FULL GENERIC DYNAMIC ARRAY (VECTOR) IN C
// Using X-macros to generate typed implementations
// ─────────────────────────────────────────────────────────────────

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define DEFINE_VECTOR(Type, Name)                               \
                                                                \
typedef struct {                                                \
    Type *data;                                                 \
    size_t size;                                                \
    size_t capacity;                                            \
} Vector_##Name;                                               \
                                                                \
Vector_##Name Vector_##Name##_new() {                          \
    Vector_##Name v;                                            \
    v.data = NULL; v.size = 0; v.capacity = 0;                 \
    return v;                                                   \
}                                                               \
                                                                \
void Vector_##Name##_push(Vector_##Name *v, Type item) {       \
    if (v->size == v->capacity) {                               \
        size_t new_cap = v->capacity == 0 ? 4 : v->capacity*2; \
        v->data = realloc(v->data, new_cap * sizeof(Type));     \
        v->capacity = new_cap;                                  \
    }                                                           \
    v->data[v->size++] = item;                                  \
}                                                               \
                                                                \
Type Vector_##Name##_get(const Vector_##Name *v, size_t i) {   \
    return v->data[i];                                          \
}                                                               \
                                                                \
void Vector_##Name##_free(Vector_##Name *v) {                   \
    free(v->data);                                              \
    v->data = NULL; v->size = 0; v->capacity = 0;              \
}

// Instantiate for specific types:
DEFINE_VECTOR(int, Int)
DEFINE_VECTOR(double, Double)
DEFINE_VECTOR(float, Float)

int main() {
    Vector_Int vi = Vector_Int_new();
    for (int i = 0; i < 10; i++) Vector_Int_push(&vi, i * i);
    for (size_t i = 0; i < vi.size; i++) printf("%d ", vi.data[i]);
    printf("\n");
    Vector_Int_free(&vi);

    Vector_Double vd = Vector_Double_new();
    Vector_Double_push(&vd, 3.14);
    Vector_Double_push(&vd, 2.71);
    printf("%f %f\n", vd.data[0], vd.data[1]);
    Vector_Double_free(&vd);
    return 0;
}
```

---

## 13. Common Pitfalls

```
    PITFALL MAP
    ══════════════════════════════════════════════════════════════
    
    RUST PITFALLS:
    
    1. Forgetting bounds
       fn max<T>(a: T, b: T) -> T { if a > b { a } else { b } }
       ERROR: binary operation `>` cannot be applied to type `T`
       FIX:   fn max<T: PartialOrd>(...)
    
    2. Recursive generic bounds (trait solver loop)
       trait Foo: Bar where Self: Baz { ... }
       → Use concrete associated types to break cycles
    
    3. Using generics when you need dyn Trait
       fn make_animals() -> Vec<impl Animal>  // ERROR if types differ
       FIX: Vec<Box<dyn Animal>>
    
    4. Code bloat in release builds
       Monitor with: cargo bloat --release
       Mitigation: Use dyn Trait for rarely-called code paths
    
    ──────────────────────────────────────────────────────────────
    
    GO PITFALLS:
    
    1. Expecting full monomorphization (Go doesn't fully do it)
       Benchmarks may show unexpected overhead for pointer types
    
    2. Trying to use operators on `any` constraint
       func add[T any](a, b T) T { return a + b }  // ERROR
       FIX: use Number or a custom numeric constraint
    
    3. Method calls on type parameters require interface constraints
       func foo[T any](x T) { x.Method() }  // ERROR: any has no methods
       FIX: Define an interface with Method() and constrain T to it
    
    4. Cannot use generic types as map keys without `comparable`
       map[T]V requires T: comparable, not just T: any
    
    ──────────────────────────────────────────────────────────────
    
    C PITFALLS:
    
    1. Macro double-evaluation (side effects run twice)
       MAX(x++, y) → x incremented twice
       FIX: Use inline functions where possible
    
    2. void* loses type information permanently
       void *p = &some_int;
       // You must NEVER forget what type p points to
    
    3. X-Macros make compilation errors nearly unreadable
       The error points to expanded code, not your definition
    
    4. _Generic doesn't work with typedef'd types in some cases
       (implementation-defined behavior in some edge cases)
    
    ══════════════════════════════════════════════════════════════
```

---

## 14. Mental Models and Cognitive Strategies

### The Three Levels of Generic Thinking

As you develop expertise with generics, your thinking will evolve through three levels:

```
    LEVEL 1 — SYNTACTIC (Beginner)
    "I know the syntax to write generics."
    Focus: How to write <T>, how to add bounds, how it compiles.
    ──────────────────────────────────────────────────────────────
    
    LEVEL 2 — SEMANTIC (Intermediate)
    "I understand what the compiler is doing underneath."
    Focus: Monomorphization, vtables, binary size, dispatch cost.
    ──────────────────────────────────────────────────────────────
    
    LEVEL 3 — DESIGN (Expert)
    "I know when to use generics and when NOT to."
    Focus: Abstractions that are easy to use, hard to misuse.
          Choosing static vs dynamic dispatch based on use case.
          Recognizing when generics add complexity without value.
    ──────────────────────────────────────────────────────────────
```

### Deliberate Practice Strategy

Generics mastery requires **abstraction-building** — one of the hardest cognitive skills.

Practice exercises in this order:

```
    EXERCISE PROGRESSION
    ──────────────────────────────────────────────────────────────
    Week 1: Implement generic versions of basic data structures
            → Generic Stack, Queue, LinkedList
            → Builds: "type as variable" intuition
    
    Week 2: Implement functional combinators
            → Generic Map, Filter, Reduce, Zip, FlatMap
            → Builds: multi-type-parameter thinking
    
    Week 3: Implement generic algorithms
            → Generic sort (needs Ord bound), binary search
            → Builds: constraint reasoning
    
    Week 4: Design a generic trait/interface hierarchy
            → Iterator, Collection, Serializable
            → Builds: abstraction design skill
    
    Week 5: Benchmark static vs dynamic dispatch yourself
            → Implement both versions of a hot algorithm
            → Build: empirical performance intuition
    ──────────────────────────────────────────────────────────────
```

### The Chunking Model for Generics

**Chunking** (a cognitive psychology concept by Chase & Simon) is how experts compress related information into single mental units.

For generics, build these chunks:

```
    CHUNK 1: "Generic = stencil for types"
    ─── Contains: syntax, type params, instantiation
    
    CHUNK 2: "Monomorphization = compile-time copy per type"
    ─── Contains: zero runtime cost, code bloat, inlining
    
    CHUNK 3: "Dynamic dispatch = vtable + fat pointer"
    ─── Contains: runtime cost, heap, heterogeneous collections
    
    CHUNK 4: "Constraint = contract the type must fulfill"
    ─── Contains: Rust traits, Go interfaces, C concepts
    
    CHUNK 5: "Static vs dynamic = binary size vs runtime speed"
    ─── Contains: trade-off analysis, use-case matching
```

Once these chunks are solid, generic programming reasoning becomes automatic.

### The Meta-Learning Principle

> **Transfer learning** — the insights from Rust generics directly illuminate Go generics, and both illuminate C's limitations. Study all three together, not in isolation.

When you understand WHY Rust monomorphizes (zero-cost abstractions, ownership rules), you understand WHY Go took a hybrid approach (GC compatibility, build time), and you understand WHAT C is missing (type information at compile time).

Understanding the *design space* of solutions — not just the solutions themselves — is what separates the top 1% from the rest.

---

## Summary Table

```
    COMPLETE COMPARISON
    ══════════════════════════════════════════════════════════════════════
    Feature            │ Rust              │ Go                │ C
    ───────────────────┼───────────────────┼───────────────────┼─────────
    Generics           │ Full              │ Full (1.18+)       │ Simulated
    Monomorphization   │ Full (all types)  │ Partial (GC shape) │ Via macros
    Constraints        │ Trait bounds      │ Interface unions   │ None/manual
    Static dispatch    │ Yes (default)     │ Yes (default)      │ Yes (macros)
    Dynamic dispatch   │ dyn Trait         │ Interface          │ void* + fnptr
    Const generics     │ Yes               │ No                 │ No
    Type inference     │ Excellent         │ Good               │ None
    Compile time       │ Longer (mono)     │ Fast (GC shape)    │ Fast (text sub)
    Binary size        │ Larger            │ Medium             │ Small
    Runtime overhead   │ Zero (static)     │ Near-zero          │ Zero (macros)
    Type safety        │ Excellent         │ Good               │ Poor (void*)
    Error messages     │ Detailed          │ Good               │ Cryptic
    ══════════════════════════════════════════════════════════════════════
```

---

> **Final Principle for the Monk-Coder:**  
> Generics are not about writing less code. They are about writing code that is *correct by construction* — where the type system enforces invariants that would otherwise require runtime checks, documentation, or discipline.  
> The goal is not cleverness. The goal is code where **incorrect usage is impossible to express.**  
> Master this, and you have mastered one of the deepest ideas in programming language design.

Here's your complete deep-dive reference. Here's what the document covers at a glance:

**Structure (14 Chapters):**

1. **The Problem** — why copy-pasting per type is catastrophic, the three bad alternatives before generics
2. **Vocabulary** — every single term defined (monomorphization, vtable, type erasure, bounds, dispatch, etc.)
3. **What Generics Are** — the stencil mental model
4. **Monomorphization** — full visual flow of how the compiler specializes code
5. **Static vs Dynamic Dispatch** — side-by-side comparison with memory layout diagrams
6. **Rust** — generic functions, structs, enums, multiple type params, `where` clauses, const generics, trait objects, assembly comparison
7. **Go** — type parameter syntax, `constraints` package, `~` tilde operator (underlying types), GC shapes (Go's partial monomorphization strategy), interface vs generics decision guide
8. **C** — all 4 mechanisms: macros (with pitfall warnings), `void*`, `_Generic` (C11), and X-Macros for code generation
9. **Memory Layout** — stack vs heap for generic types, fat pointers visualized
10. **Performance Analysis** — assembly-level difference, when overhead actually matters
11. **Decision Tree** — flowchart for choosing between all approaches
12. **Advanced Patterns** — const generics, associated types, generic ordered maps
13. **Pitfalls** — per-language gotcha map
14. **Mental Models** — deliberate practice plan, chunking framework, meta-learning principles

**Key insight to internalize:** Rust does *full* monomorphization (max performance, larger binary). Go does *partial* monomorphization via GC shapes (all pointer types share one copy). C simulates it via preprocessor (text substitution, no type safety). Understanding *why* each language made its trade-off is the mark of Level 3 thinking.