# Type Systems in Go vs Rust — A Deep, Comprehensive Guide

> "A type system is not just a bug checker. It is a formal language for expressing your intentions to both the compiler and to future readers of your code." — *Expert Practitioner Insight*

---

## Table of Contents

1. [What Is a Type System?](#1-what-is-a-type-system)
2. [Philosophy: Go's Simplicity vs Rust's Expressiveness](#2-philosophy)
3. [Primitive Types — The Atoms of a Language](#3-primitive-types)
4. [Type Inference — Let the Compiler Think](#4-type-inference)
5. [Composite Types — Structs, Arrays, Slices, Tuples](#5-composite-types)
6. [Interfaces (Go) vs Traits (Rust)](#6-interfaces-vs-traits)
7. [Enums — Go's iota vs Rust's Algebraic Types](#7-enums)
8. [Null Safety — nil vs Option<T>](#8-null-safety)
9. [Error Handling — (T, error) vs Result<T, E>](#9-error-handling)
10. [Generics — Parameterizing Over Types](#10-generics)
11. [Type Aliases and the Newtype Pattern](#11-type-aliases-and-newtype)
12. [Ownership — Rust's Type-Level Memory Model](#12-ownership-type-system)
13. [Lifetimes — Encoding Time Into Types](#13-lifetimes)
14. [Type Coercion and Casting](#14-type-coercion-and-casting)
15. [Pattern Matching](#15-pattern-matching)
16. [Zero-Cost Abstractions](#16-zero-cost-abstractions)
17. [Advanced Trait System — Rust Deep Dive](#17-advanced-trait-system)
18. [Type System Comparison Table](#18-comparison-table)
19. [Real-World Design Patterns](#19-real-world-design-patterns)
20. [Mental Models & Cognitive Strategies](#20-mental-models)

---

## 1. What Is a Type System?

### Conceptual Definition

A **type system** is a set of rules a programming language uses to assign a property called a **type** to every expression and value. The compiler then uses these rules to:

- **Prevent programs from doing wrong things** (e.g., treating a number as a pointer)
- **Guide the programmer** by making intentions explicit
- **Enable optimizations** because the compiler knows memory layout
- **Document code** — types are machine-checked documentation

Think of types like **contracts**. When you say a variable is of type `u32`, you're making a contract: "This memory will always hold an unsigned 32-bit integer." The compiler enforces that contract at compile time.

```
TAXONOMY OF TYPE SYSTEMS
─────────────────────────────────────────────────────────
                    Type Systems
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Static          Dynamic        Gradual
    (checked at       (checked at    (mix of both)
    compile time)     runtime)
          │
    ┌─────┴─────┐
    │           │
  Strong       Weak
(strict       (implicit
 coercion)     coercion)
    │
    ├── Nominal   → Go structs (identity by name)
    └── Structural → Go interfaces (identity by shape)

Rust = Static + Strong + Nominal (+ Structural for traits)
Go   = Static + Strong + Structural interfaces + Nominal structs
─────────────────────────────────────────────────────────
```

### Key Vocabulary You Must Know

| Term | Definition | Example |
|------|-----------|---------|
| **Static Typing** | Types checked before program runs | Both Go and Rust |
| **Dynamic Typing** | Types checked at runtime | Python, JavaScript |
| **Type Inference** | Compiler deduces type automatically | `let x = 5;` → x is i32 |
| **Nominal Type System** | Types matched by name | Two structs named differently are different types even with same fields |
| **Structural Type System** | Types matched by shape/structure | If it has the right methods, it satisfies the interface |
| **Algebraic Data Types (ADT)** | Types formed by combining other types | `enum Result<T, E> { Ok(T), Err(E) }` |
| **Coercion** | Implicit type conversion | C: `int x = 3.7;` silently truncates |
| **Casting** | Explicit type conversion | Rust: `3.7f64 as i32` |
| **Subtyping** | A type is a subtype of another | Rust lifetimes; Go interfaces |

---

## 2. Philosophy

### Go's Design Philosophy: "Simplicity is Sophistication"

Go was designed at Google in 2007 by Rob Pike, Ken Thompson, and Robert Griesemer. Their goals:

- **Fast compilation** (no slow template instantiation like C++)
- **Readable code** — a newcomer should read Go quickly
- **Pragmatic, not academic** — solve real production problems
- **Garbage collected** — programmer doesn't manage memory

Go's type system is **deliberately limited**. It avoids features like:
- Inheritance (no `extends`)
- Method overloading
- Implicit type conversions
- Exceptions (uses explicit error values)
- (Initially) Generics — added only in Go 1.18 (2022)

```
GO'S TYPE SYSTEM DESIGN AXIS
─────────────────────────────────────────────────────────
Simplicity ◄──────────────────────────► Expressiveness
                         Go sits HERE
                         (left-center)
─────────────────────────────────────────────────────────
```

### Rust's Design Philosophy: "Safety Without Sacrifice"

Rust was designed at Mozilla by Graydon Hoare starting ~2006. Goals:

- **Memory safety WITHOUT garbage collection**
- **Zero-cost abstractions** — high-level code should compile to the same speed as hand-written C
- **Fearless concurrency** — the type system prevents data races
- **Expressiveness** — the type system should be rich enough to model domain logic precisely

Rust's type system is **extraordinarily rich**. It includes:
- Generics with trait bounds
- Algebraic data types (enums with data)
- Lifetimes (encoding memory validity into types)
- Ownership types (encoding memory ownership into types)
- Higher-Kinded Type patterns (via associated types)

```
RUST'S TYPE SYSTEM DESIGN AXIS
─────────────────────────────────────────────────────────
Simplicity ◄──────────────────────────► Expressiveness
                                    Rust sits HERE
                                    (right-center)
─────────────────────────────────────────────────────────
```

### The Fundamental Tradeoff

```
                    GO vs RUST TYPE SYSTEM TRADEOFFS
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Go                              Rust                       │
│  ──────────────────              ──────────────────         │
│  ✅ Learn in days                ✅ Express complex logic    │
│  ✅ Fast compilation             ✅ No GC pauses             │
│  ✅ Less boilerplate             ✅ Compile-time safety      │
│  ❌ Less expressive              ✅ Zero-cost abstractions   │
│  ❌ nil panics possible          ✅ No null pointer bugs     │
│  ❌ Implicit nil interface       ❌ Steep learning curve     │
│  ❌ Runtime type assertions      ❌ Verbose sometimes        │
│                                  ❌ Slower compile times     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Primitive Types — The Atoms of a Language

### What is a Primitive Type?

A **primitive type** (also called a **scalar type**) is the most basic building block — a type that holds a single, indivisible value. Think of it as an atom. Everything else is made from these.

### Go Primitive Types

```go
package main

import "fmt"

func main() {
    // ── INTEGERS ──────────────────────────────────────────────
    // Signed integers (can be negative or positive)
    var a int8  = 127          // 8-bit:  -128 to 127
    var b int16 = 32767        // 16-bit: -32768 to 32767
    var c int32 = 2147483647   // 32-bit  (also written as 'rune' for Unicode)
    var d int64 = 9223372036854775807 // 64-bit

    // Platform-dependent integer (32-bit on 32-bit OS, 64-bit on 64-bit OS)
    var e int = 42  // Most common integer type in Go

    // Unsigned integers (only positive)
    var f uint8  = 255   // 8-bit: 0 to 255 (also 'byte')
    var g uint16 = 65535
    var h uint32 = 4294967295
    var i uint64 = 18446744073709551615
    var j uint   = 100   // platform-dependent

    // Alias types (important — these ARE the same type)
    var k byte = 65    // byte is EXACTLY uint8 (used for raw data)
    var l rune = '🔥'  // rune is EXACTLY int32 (used for Unicode code points)

    // ── FLOATING POINT ─────────────────────────────────────────
    var m float32 = 3.14159          // IEEE-754 single precision
    var n float64 = 3.141592653589793 // IEEE-754 double precision (use this by default)

    // ── COMPLEX NUMBERS ────────────────────────────────────────
    var o complex64  = 1 + 2i
    var p complex128 = 3.14 + 2.71i

    // ── BOOLEAN ────────────────────────────────────────────────
    var q bool = true   // only true or false — NOT 0/1 like C

    // ── STRING ─────────────────────────────────────────────────
    // IMPORTANT: In Go, string is a PRIMITIVE-like type but it's actually
    // an immutable sequence of bytes (UTF-8 encoded). It is NOT a char array.
    var r string = "Hello, 世界"  // UTF-8 by default

    // uintptr — used for pointer arithmetic (advanced, low-level)
    var s uintptr = 0xDEADBEEF

    // Suppress unused variable warnings for this demo
    _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = 
        a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s

    fmt.Println("Go primitive types demonstrated")
}
```

```
GO INTEGER TYPE MEMORY LAYOUT
─────────────────────────────────────────────────────────
Type     Bits  Bytes   Range
──────── ───── ──────  ──────────────────────────────────
int8       8     1     -128 to 127
int16     16     2     -32,768 to 32,767
int32     32     4     -2,147,483,648 to 2,147,483,647
int64     64     8     -9.2 × 10^18 to 9.2 × 10^18
uint8      8     1     0 to 255
uint16    16     2     0 to 65,535
uint32    32     4     0 to 4,294,967,295
uint64    64     8     0 to 1.8 × 10^19
float32   32     4     ~7 decimal digits precision
float64   64     8     ~15 decimal digits precision
─────────────────────────────────────────────────────────
```

### Rust Primitive Types

```rust
fn main() {
    // ── SIGNED INTEGERS ────────────────────────────────────────
    let a: i8  = 127;
    let b: i16 = 32_767;        // underscores for readability (Rust feature)
    let c: i32 = 2_147_483_647; // DEFAULT integer type in Rust (not i64!)
    let d: i64 = 9_223_372_036_854_775_807;
    let e: i128 = 170_141_183_460_469_231_731_687_303_715_884_105_727;
    let f: isize = 42;  // platform-dependent (like Go's int)

    // ── UNSIGNED INTEGERS ──────────────────────────────────────
    let g: u8   = 255;
    let h: u16  = 65_535;
    let i: u32  = 4_294_967_295;
    let j: u64  = 18_446_744_073_709_551_615;
    let k: u128 = 340_282_366_920_938_463_463_374_607_431_768_211_455;
    let l: usize = 100; // platform-dependent, used for indexing/lengths

    // ── FLOATING POINT ─────────────────────────────────────────
    let m: f32 = 3.14159_f32;
    let n: f64 = 3.141_592_653_589_793; // DEFAULT float type in Rust

    // ── BOOLEAN ────────────────────────────────────────────────
    let o: bool = true;

    // ── CHARACTER ──────────────────────────────────────────────
    // CRITICAL DIFFERENCE: Rust has a CHAR primitive (Go does not — Go uses rune which is int32)
    // Rust's char is always 4 bytes and represents a Unicode Scalar Value
    let p: char = '🔥'; // Valid! Rust char is Unicode-native
    let q: char = 'A';
    let r: char = '中';

    // ── TUPLES ─────────────────────────────────────────────────
    // Tuples are primitive compound types (fixed-size, mixed types)
    let t: (i32, f64, bool) = (42, 3.14, true);
    let (x, y, z) = t; // destructuring
    let first = t.0;   // index access

    // ── ARRAYS ─────────────────────────────────────────────────
    // Fixed-size, stack-allocated, single type
    let arr: [i32; 5] = [1, 2, 3, 4, 5];
    let zeros: [i32; 100] = [0; 100]; // [value; count] syntax

    // ── UNIT TYPE ──────────────────────────────────────────────
    // () is the "unit type" — equivalent to void in C but it IS a real type
    // Functions that return nothing actually return ()
    let unit: () = ();

    // ── NEVER TYPE ─────────────────────────────────────────────
    // ! (never) type — a function that NEVER returns (infinite loop, panic, etc.)
    // fn infinite_loop() -> ! { loop {} }

    println!("Rust primitive types: x={}, y={}, z={}", x, y, z);
    println!("char: {}, array[0]: {}, arr len: {}", p, arr[0], arr.len());
}
```

### Critical Differences in Primitives

```
GO vs RUST PRIMITIVE COMPARISON
─────────────────────────────────────────────────────────────────
Feature                    Go              Rust
──────────────────────    ──────────────  ─────────────────────
Native char type          ❌ (uses rune)  ✅ char (4 bytes, Unicode)
128-bit integers          ❌              ✅ i128, u128
isize/usize               ✅ (int/uint)   ✅ (isize/usize)
Default integer type      int             i32
Default float type        float64         f64
Complex numbers built-in  ✅              ❌ (use crate)
String as primitive       ✅ (sort of)    ❌ (&str, String are separate)
Tuple type                ❌ (use struct) ✅ (first-class)
Unit type ()              ❌              ✅
Never type !              ❌              ✅
Numeric separators        ❌              ✅ (1_000_000)
Integer overflow          panic (debug)   panic (debug), wraps (release)
─────────────────────────────────────────────────────────────────
```

### Integer Overflow — A Critical Safety Difference

```rust
// RUST: Integer overflow behavior
fn main() {
    let x: u8 = 255;

    // In DEBUG mode: this PANICS (program crashes with error)
    // let y = x + 1; // thread 'main' panicked at 'attempt to add with overflow'

    // Rust provides EXPLICIT overflow methods:
    let wrapped = x.wrapping_add(1);    // 0   (wraps around)
    let saturated = x.saturating_add(1); // 255 (stays at max)
    let checked = x.checked_add(1);      // None (returns Option<u8>)
    let overflowed = x.overflowing_add(1); // (0, true) (value, did_overflow)

    println!("wrapped: {}, saturated: {}, checked: {:?}, overflowed: {:?}",
        wrapped, saturated, checked, overflowed);
}
```

```go
// GO: Integer overflow silently wraps (no panic)
package main

import "fmt"

func main() {
    var x uint8 = 255
    y := x + 1  // SILENTLY wraps to 0 — no panic, no error!
    fmt.Println(y) // prints 0

    // This is a common source of bugs in Go
    // You must manually check for overflow if needed
}
```

> **Expert Insight:** Rust's explicit overflow handling forces you to think about edge cases. Go's silent wrapping is a potential bug source. In security-critical code (e.g., cryptography, buffer management), this difference matters enormously.

---

## 4. Type Inference — Let the Compiler Think

### What is Type Inference?

**Type inference** is the compiler's ability to automatically deduce the type of a variable from context, so you don't have to write it explicitly. It was invented by Robin Milner (Hindley-Milner type inference, 1978).

```
TYPE INFERENCE — HOW THE COMPILER THINKS
─────────────────────────────────────────────────────────
You write:     let x = 42;
               ────┬────
                   │
              Compiler looks at
              the literal 42
                   │
              Default integer type
              in Rust is i32
                   │
              Compiler infers:
              x: i32 = 42
─────────────────────────────────────────────────────────
```

### Go Type Inference

```go
package main

import "fmt"

func main() {
    // ── SHORT VARIABLE DECLARATION (:=) ──────────────────────
    // The := operator declares AND assigns, inferring the type

    x := 42           // inferred as int (not int32, not int64 — platform int)
    y := 3.14         // inferred as float64 (always float64 for decimals)
    z := true         // inferred as bool
    s := "hello"      // inferred as string
    b := byte(65)     // explicit: you're controlling the type

    fmt.Printf("x: %T = %v\n", x, x) // %T prints the type
    fmt.Printf("y: %T = %v\n", y, y)

    // ── FUNCTION RETURN INFERENCE ─────────────────────────────
    // Go infers the type of a variable from function return values
    result := add(3, 4) // result is inferred as int

    // ── COMPOSITE LITERAL INFERENCE ───────────────────────────
    // Slice — Go can infer element types
    nums := []int{1, 2, 3, 4, 5}

    // Map literal
    ages := map[string]int{
        "Alice": 30,
        "Bob":   25,
    }

    // ── LIMITATIONS OF GO'S TYPE INFERENCE ───────────────────
    // Go CANNOT infer types across assignments:
    var a int32 = 42
    // b := a + 1  // b is int32, fine
    // But if you try to pass 'a' to a func expecting int, you must cast

    _ = result
    _ = nums
    _ = ages
    _ = a

    // Go inference is LOCAL — only within expressions, not globally
}

func add(a, b int) int { return a + b }
```

### Rust Type Inference (Much More Powerful)

```rust
fn main() {
    // Rust uses Hindley-Milner type inference — it can infer types
    // across ENTIRE EXPRESSIONS, even backwards from usage!

    // ── BASIC INFERENCE ────────────────────────────────────────
    let x = 42;           // i32 by default
    let y = 3.14;         // f64 by default
    let z = true;         // bool
    let s = "hello";      // &str (a string slice reference)

    // ── BACKWARD INFERENCE (Go cannot do this!) ───────────────
    // Rust can infer based on HOW the variable is USED LATER
    let mut v = Vec::new(); // Rust doesn't know element type yet...
    v.push(1_i32);          // NOW it knows! v is Vec<i32>
    // This backward inference is extremely powerful

    // Another example: collecting into a specific collection
    let numbers = vec![1, 2, 3, 4, 5];
    let doubled: Vec<i32> = numbers.iter().map(|x| x * 2).collect();
    // The :Vec<i32> annotation tells collect() what to produce

    // Without annotation — Rust infers from context:
    let sum: i64 = numbers.iter().map(|&x| x as i64).sum();

    // ── INFERENCE WITH GENERICS ────────────────────────────────
    // Rust infers generic type parameters!
    fn identity<T>(x: T) -> T { x }
    let n = identity(42_i32);    // T inferred as i32
    let s = identity("hello");   // T inferred as &str

    // ── INFERENCE ACROSS BRANCHES ──────────────────────────────
    let condition = true;
    let number = if condition { 5_i32 } else { 10_i32 };
    // Both branches must return the SAME type — enforced at compile time

    // ── WHERE INFERENCE FAILS (you must annotate) ─────────────
    // When multiple types are possible and none is default:
    let parsed: i64 = "42".parse().expect("valid number");
    // Without : i64, compiler asks: "parse into WHAT type?"
    // This is called a "type annotation is needed" error

    println!("x={}, y={}, z={}, s={}, sum={}, parsed={}", x, y, z, s, sum, parsed);
    println!("doubled: {:?}", doubled);
}
```

```
INFERENCE POWER COMPARISON
─────────────────────────────────────────────────────────
                              Go        Rust
──────────────────────────    ───────   ──────
Basic literal inference        ✅        ✅
Function return inference      ✅        ✅
Backward inference from use    ❌        ✅
Generic type inference         ✅        ✅ (more powerful)
Cross-function inference       ❌        ✅ (lifetime inference)
Closure arg inference          ❌        ✅
─────────────────────────────────────────────────────────
```

---

## 5. Composite Types — Structs, Arrays, Slices, Tuples

### What are Composite Types?

**Composite types** are types built by combining other types. They are the "molecules" of a type system. Examples: a `Person` struct combining name (string) + age (int).

### Structs

Structs are the primary way to group related data in both languages.

```go
// ── GO STRUCTS ─────────────────────────────────────────────────
package main

import "fmt"

// A struct definition — a new named type
// This is a NOMINAL type: its identity is its NAME "Person"
type Person struct {
    Name    string
    Age     int
    Email   string
    address string // lowercase = unexported (private to this package)
}

// Method on Person
func (p Person) String() string {
    return fmt.Sprintf("%s (age %d)", p.Name, p.Age)
}

// Pointer receiver — modifies the original
func (p *Person) Birthday() {
    p.Age++
}

// ── EMBEDDED STRUCTS (Go's alternative to inheritance) ────────
type Employee struct {
    Person  // embedded — promotes Person's fields and methods
    Company string
    Salary  float64
}

// ── ANONYMOUS STRUCTS ─────────────────────────────────────────
// Useful for one-off groupings (e.g., JSON responses, test cases)
type Point struct {
    X, Y float64 // two fields, same type — shorthand
}

func main() {
    // ── STRUCT LITERALS ───────────────────────────────────────
    // Named fields (preferred — order doesn't matter, self-documenting)
    p1 := Person{
        Name:  "Alice",
        Age:   30,
        Email: "alice@example.com",
    }

    // Positional (avoid — fragile, breaks if fields reordered)
    p2 := Person{"Bob", 25, "bob@example.com", ""}

    // Zero value — all fields get their zero value
    var p3 Person // Name="", Age=0, Email=""

    // ── STRUCT ACCESS ─────────────────────────────────────────
    fmt.Println(p1.Name) // direct field access
    p1.Birthday()        // method call (pointer receiver, auto-dereferenced)
    fmt.Println(p1.Age)  // now 31

    // ── EMBEDDED STRUCT ───────────────────────────────────────
    emp := Employee{
        Person:  Person{Name: "Charlie", Age: 35, Email: "c@corp.com"},
        Company: "Acme",
        Salary:  75000,
    }
    fmt.Println(emp.Name)    // promoted from Person — NO need for emp.Person.Name
    fmt.Println(emp.String()) // promoted method from Person

    // ── ANONYMOUS STRUCT ──────────────────────────────────────
    config := struct {
        Host string
        Port int
    }{
        Host: "localhost",
        Port: 8080,
    }
    fmt.Println(config.Host, config.Port)

    // ── STRUCT COMPARISON ─────────────────────────────────────
    // Structs are comparable if ALL their fields are comparable
    pt1 := Point{1.0, 2.0}
    pt2 := Point{1.0, 2.0}
    fmt.Println(pt1 == pt2) // true — value comparison

    _ = p2
    _ = p3
}
```

```rust
// ── RUST STRUCTS ───────────────────────────────────────────────
use std::fmt;

// Named-field struct (most common)
#[derive(Debug, Clone, PartialEq)] // derive macros auto-implement traits
struct Person {
    name: String,       // owned String (heap-allocated)
    age: u32,
    email: String,
}

impl Person {
    // Associated function (like a static method / constructor)
    fn new(name: &str, age: u32, email: &str) -> Self {
        Person {
            name: name.to_string(),
            age,  // field shorthand when variable name matches field name
            email: email.to_string(),
        }
    }

    // Method (takes &self — immutable borrow)
    fn greeting(&self) -> String {
        format!("Hi, I'm {} and I'm {} years old.", self.name, self.age)
    }

    // Mutable method (takes &mut self)
    fn birthday(&mut self) {
        self.age += 1;
    }
}

// Display trait (like Go's String() method)
impl fmt::Display for Person {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} (age {})", self.name, self.age)
    }
}

// ── TUPLE STRUCTS (unnamed fields) ───────────────────────────
// Great for newtype pattern (see section 11)
struct Point(f64, f64);
struct Meters(f64); // newtype — wraps f64 but is a distinct type

// ── UNIT STRUCT (no fields) ────────────────────────────────
struct Marker; // useful as a zero-sized type for type-level logic

// ── STRUCT WITH REFERENCES (needs lifetime) ──────────────────
// (covered in section 13)
// struct Important<'a> { part: &'a str }

// ── STRUCT UPDATE SYNTAX ──────────────────────────────────────
fn demonstrate_update() {
    let p1 = Person::new("Alice", 30, "alice@example.com");
    let p2 = Person {
        name: "Alice-Clone".to_string(),
        ..p1  // copy remaining fields from p1
              // NOTE: p1 is MOVED here if fields are non-Copy
              // (name and email are String, which is not Copy)
    };
    // p1 is now partially moved — cannot use p1.name anymore
    // but p1.age (u32, Copy type) is still fine
    println!("{}", p2);
}

fn main() {
    let mut p = Person::new("Bob", 25, "bob@example.com");
    println!("{}", p);         // uses Display
    println!("{:?}", p);       // uses Debug (from #[derive(Debug)])
    p.birthday();
    println!("After birthday: {}", p.greeting());

    let pt = Point(3.0, 4.0);
    println!("Point: ({}, {})", pt.0, pt.1); // access tuple fields by index

    let dist = Meters(42.5);
    println!("Distance: {} meters", dist.0);

    let _marker = Marker; // zero-sized type

    demonstrate_update();
}
```

### Arrays vs Slices

```
ARRAY vs SLICE MENTAL MODEL
─────────────────────────────────────────────────────────
Array  = fixed-size box with N items
         [■■■■■] size known at compile time, stack allocated

Slice  = a VIEW into an array (or part of it)
         ┌──────────────────────┐
         │ pointer → data       │ points to actual data
         │ length               │ how many items visible
         │ capacity             │ how many items available
         └──────────────────────┘
─────────────────────────────────────────────────────────
```

```go
// ── GO ARRAYS AND SLICES ───────────────────────────────────────
package main

import "fmt"

func main() {
    // ── ARRAYS (fixed size, value type) ──────────────────────
    arr1 := [5]int{1, 2, 3, 4, 5}
    arr2 := [...]int{1, 2, 3} // ... = let compiler count
    var arr3 [3]int            // zero value: [0, 0, 0]

    // Arrays are VALUE types — copying an array copies all data
    arr4 := arr1 // arr4 is a FULL COPY
    arr4[0] = 99
    fmt.Println(arr1[0], arr4[0]) // 1, 99 — independent

    // ── SLICES (dynamic size, reference type) ─────────────────
    // Slice literal — backed by an anonymous array
    s1 := []int{1, 2, 3, 4, 5}

    // Slice from array
    s2 := arr1[1:4] // elements at index 1, 2, 3 (NOT including 4)
                    // s2 = [2, 3, 4]

    // make(type, length, capacity)
    s3 := make([]int, 3, 5) // length=3, capacity=5

    // append — creates new backing array if capacity exceeded
    s4 := append(s1, 6, 7, 8)

    // ── SLICE HEADER STRUCTURE ────────────────────────────────
    // A slice is: {pointer, length, capacity}
    fmt.Printf("s1: len=%d, cap=%d\n", len(s1), cap(s1))

    // ── MODIFYING THROUGH SLICE ───────────────────────────────
    s2[0] = 99       // modifies arr1[1] — they share backing array!
    fmt.Println(arr1) // [1 99 3 4 5] — arr1 changed!

    // ── 2D SLICES ─────────────────────────────────────────────
    matrix := [][]int{
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9},
    }
    fmt.Println(matrix[1][2]) // 6

    // ── COPY ──────────────────────────────────────────────────
    dst := make([]int, len(s1))
    copy(dst, s1) // copies min(len(dst), len(s1)) elements
    dst[0] = 999
    fmt.Println(s1[0], dst[0]) // 1, 999 — independent after copy

    _ = arr2; _ = arr3; _ = s3; _ = s4
}
```

```rust
// ── RUST ARRAYS AND SLICES ─────────────────────────────────────
fn main() {
    // ── ARRAYS (fixed size, known at compile time) ────────────
    let arr1: [i32; 5] = [1, 2, 3, 4, 5];
    let arr2 = [0_i32; 100]; // 100 zeros
    let arr3 = [1, 2, 3];    // type inferred: [i32; 3]

    // Arrays are VALUE types (implement Copy if element is Copy)
    let arr4 = arr1; // full copy (i32 is Copy)
    // arr1 is still valid!

    // ── SLICES (&[T]) ─────────────────────────────────────────
    // A slice is a REFERENCE — it borrows a portion of a collection
    let slice1: &[i32] = &arr1[1..4]; // [2, 3, 4]
    let slice2: &[i32] = &arr1[..];   // entire array as slice

    // You can also have mutable slices
    let mut arr5 = [1, 2, 3, 4, 5];
    {
        let slice_mut: &mut [i32] = &mut arr5[1..4];
        slice_mut[0] = 99; // modifies arr5[1]
    }
    println!("arr5: {:?}", arr5); // [1, 99, 3, 4, 5]

    // ── Vec<T> (Go's equivalent to []T slices) ────────────────
    // Vec = heap-allocated, growable, owned collection
    let mut v1: Vec<i32> = Vec::new();
    v1.push(1);
    v1.push(2);
    v1.push(3);

    let v2 = vec![1, 2, 3, 4, 5]; // macro shorthand

    // Vec can be converted to a slice:
    let as_slice: &[i32] = &v2;

    // ── KEY MENTAL MODEL ──────────────────────────────────────
    // [T; N]     = array (stack, fixed size, value type)
    // &[T]       = slice reference (pointer + length, borrowed)
    // &mut [T]   = mutable slice reference
    // Vec<T>     = heap-allocated dynamic array (owned)

    // ── ITERATION ─────────────────────────────────────────────
    for (i, val) in v2.iter().enumerate() {
        print!("[{}]={} ", i, val);
    }
    println!();

    // ── FUNCTIONAL OPERATIONS (very idiomatic in Rust) ────────
    let doubled: Vec<i32> = v2.iter().map(|&x| x * 2).collect();
    let evens: Vec<&i32>  = v2.iter().filter(|&&x| x % 2 == 0).collect();
    let total: i32        = v2.iter().sum();

    println!("doubled: {:?}, evens: {:?}, total: {}", doubled, evens, total);
    println!("arr1: {:?}, slice1: {:?}", arr1, slice1);
    let _ = (arr2, arr3, arr4, slice2, v1, as_slice);
}
```

---

## 6. Interfaces (Go) vs Traits (Rust)

### What are Interfaces / Traits?

Both interfaces (Go) and traits (Rust) are mechanisms for **polymorphism** — writing code that works with multiple different types.

**Polymorphism** means: "one form, multiple implementations." For example, a `Draw()` function that works for both `Circle` and `Rectangle`.

```
POLYMORPHISM — THE CORE IDEA
─────────────────────────────────────────────────────────
function draw(shape ???) {
    shape.render()  ← This works for BOTH:
}                       ┌── Circle.render()
                        └── Rectangle.render()

The ??? is filled by:
  Go:   an interface type
  Rust: a trait bound (generic) or trait object
─────────────────────────────────────────────────────────
```

### Go Interfaces — Structural, Implicit Satisfaction

```go
package main

import (
    "fmt"
    "math"
)

// ── INTERFACE DEFINITION ──────────────────────────────────────
// An interface specifies a set of METHOD SIGNATURES
// Any type that has these methods AUTOMATICALLY satisfies the interface
// This is called STRUCTURAL TYPING or "duck typing" with static checking
type Shape interface {
    Area() float64
    Perimeter() float64
    String() string
}

// IMPORTANT: There is NO explicit declaration like "implements Shape"
// If Circle has Area(), Perimeter(), and String() → it IS a Shape

// ── CONCRETE TYPES ────────────────────────────────────────────
type Circle struct {
    Radius float64
}

func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }
func (c Circle) String() string     { return fmt.Sprintf("Circle(r=%.2f)", c.Radius) }

type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64      { return r.Width * r.Height }
func (r Rectangle) Perimeter() float64 { return 2 * (r.Width + r.Height) }
func (r Rectangle) String() string {
    return fmt.Sprintf("Rect(%v×%v)", r.Width, r.Height)
}

// ── FUNCTION ACCEPTING INTERFACE ──────────────────────────────
func printShapeInfo(s Shape) {
    fmt.Printf("%s: area=%.2f, perimeter=%.2f\n", s, s.Area(), s.Perimeter())
}

// ── MULTIPLE INTERFACES ───────────────────────────────────────
type Drawable interface {
    Draw()
}

type Resizable interface {
    Resize(factor float64)
}

// Combining interfaces (interface composition)
type Widget interface {
    Drawable
    Resizable
    String() string
}

// ── EMPTY INTERFACE — The Universal Type ─────────────────────
// interface{} (or 'any' in Go 1.18+) accepts ANY type
// This is Go's escape hatch from the type system
func printAny(v interface{}) {
    fmt.Printf("Type: %T, Value: %v\n", v, v)
}

// ── TYPE ASSERTIONS ───────────────────────────────────────────
// Extracting the underlying concrete type from an interface
func describe(s Shape) {
    // Type assertion with comma-ok idiom (safe, no panic)
    if c, ok := s.(Circle); ok {
        fmt.Printf("It's a circle with radius %.2f\n", c.Radius)
    } else if r, ok := s.(Rectangle); ok {
        fmt.Printf("It's a rectangle %v×%v\n", r.Width, r.Height)
    }
}

// ── TYPE SWITCH ───────────────────────────────────────────────
func typeSwitch(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int: %d", v)
    case string:
        return fmt.Sprintf("string: %q", v)
    case Circle:
        return fmt.Sprintf("circle area: %.2f", v.Area())
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
}

// ── INTERFACE NIL TRAP ────────────────────────────────────────
// This is a notorious Go gotcha!
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func mightReturnError(fail bool) error {
    var err *MyError // typed nil pointer
    if fail {
        err = &MyError{"something went wrong"}
    }
    return err // ← BUG: returns a non-nil interface with nil value!
}

func main() {
    shapes := []Shape{
        Circle{Radius: 5},
        Rectangle{Width: 3, Height: 4},
    }

    for _, s := range shapes {
        printShapeInfo(s)
        describe(s)
    }

    printAny(42)
    printAny("hello")
    printAny(Circle{1.0})

    // Interface nil trap demonstration
    err := mightReturnError(false)
    if err != nil { // This is TRUE even though *MyError is nil!
        fmt.Println("BUG: this prints even though no error occurred!")
        // An interface value is nil ONLY when BOTH its type AND value are nil
    }

    fmt.Println(typeSwitch(42))
    fmt.Println(typeSwitch("test"))
}
```

```
GO INTERFACE INTERNAL REPRESENTATION
─────────────────────────────────────────────────────────
An interface value has TWO components:

interface{}
┌──────────────────────────────┐
│  type pointer → Circle       │  Which concrete type is stored
│  data pointer → {Radius: 5}  │  Pointer to actual data
└──────────────────────────────┘

A nil interface: BOTH pointers are nil
┌──────────────────────────────┐
│  type pointer → nil          │
│  data pointer → nil          │
└──────────────────────────────┘

The nil interface trap:
┌──────────────────────────────┐
│  type pointer → *MyError     │  type is NOT nil!
│  data pointer → nil          │  value IS nil
└──────────────────────────────┘
← This is NOT a nil interface! err != nil is true!
─────────────────────────────────────────────────────────
```

### Rust Traits — Nominal, Explicit Implementation

```rust
use std::fmt;

// ── TRAIT DEFINITION ──────────────────────────────────────────
// A trait defines a set of methods types must implement
// Unlike Go interfaces, satisfaction is EXPLICIT (nominal)
trait Shape {
    fn area(&self) -> f64;
    fn perimeter(&self) -> f64;

    // DEFAULT METHOD IMPLEMENTATIONS — Go interfaces cannot do this!
    fn describe(&self) -> String {
        format!("Shape with area {:.2} and perimeter {:.2}",
            self.area(), self.perimeter())
    }

    // Default method that calls other trait methods
    fn is_large(&self) -> bool {
        self.area() > 100.0
    }
}

// ── CONCRETE TYPES ────────────────────────────────────────────
#[derive(Debug, Clone)]
struct Circle {
    radius: f64,
}

#[derive(Debug, Clone)]
struct Rectangle {
    width: f64,
    height: f64,
}

// EXPLICIT implementation — you must say "impl Shape for Circle"
// This is NOMINAL: the compiler checks you declared this, not just "has the methods"
impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
    fn perimeter(&self) -> f64 { 2.0 * std::f64::consts::PI * self.radius }
    // describe() and is_large() are inherited from default implementation
}

impl fmt::Display for Circle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Circle(r={:.2})", self.radius)
    }
}

impl Shape for Rectangle {
    fn area(&self) -> f64 { self.width * self.height }
    fn perimeter(&self) -> f64 { 2.0 * (self.width + self.height) }

    // Override default method
    fn describe(&self) -> String {
        format!("Rectangle {}×{}: area={:.2}", self.width, self.height, self.area())
    }
}

// ── TWO WAYS TO USE TRAITS ────────────────────────────────────

// WAY 1: Static dispatch with generics (impl Trait / T: Trait)
// The compiler generates specialized code for EACH concrete type → FAST
// This is called MONOMORPHIZATION (creating one specific version per type)
fn print_shape_static(shape: &impl Shape) {
    println!("{}", shape.describe());
}

// Equivalent with full generic syntax:
fn print_shape_generic<S: Shape>(shape: &S) {
    println!("area = {:.2}", shape.area());
}

// With where clause (cleaner for complex bounds):
fn print_two_shapes<S, T>(s1: &S, s2: &T)
where
    S: Shape + fmt::Debug,  // S must implement BOTH Shape AND Debug
    T: Shape,
{
    println!("Shape1: {:?} area={:.2}", s1, s1.area());
    println!("Shape2: area={:.2}", s2.area());
}

// WAY 2: Dynamic dispatch with trait objects (dyn Trait)
// Runtime polymorphism — the compiler doesn't know the type at compile time
// Uses a vtable (virtual table) like C++ virtual functions → small overhead
fn print_shape_dynamic(shape: &dyn Shape) {
    println!("Dynamic: {}", shape.describe());
}

// Storing different shapes in a collection (REQUIRES dyn Trait)
fn process_shapes(shapes: &[Box<dyn Shape>]) {
    for shape in shapes {
        println!("{}", shape.describe());
    }
}

// ── TRAIT OBJECTS INTERNALS ───────────────────────────────────
// &dyn Shape is a "fat pointer": 2 pointers in size
//   1. Pointer to the data (the actual Circle or Rectangle)
//   2. Pointer to the vtable (table of function pointers for that type)

// ── TRAIT BOUNDS ON STRUCTS ──────────────────────────────────
struct Pair<T> {
    first: T,
    second: T,
}

impl<T: PartialOrd + fmt::Display> Pair<T> {
    fn cmp_display(&self) {
        if self.first >= self.second {
            println!("The largest member is first = {}", self.first);
        } else {
            println!("The largest member is second = {}", self.second);
        }
    }
}

// ── BLANKET IMPLEMENTATIONS ──────────────────────────────────
// Implement a trait for ALL types that satisfy some other trait
// This is like "for every T that is Display, also implement ToString"
// The standard library does: impl<T: fmt::Display> ToString for T { ... }

// ── SUPERTRAIT (Trait that requires another Trait) ────────────
trait PrintableShape: Shape + fmt::Display {
    fn print(&self) {
        println!("{}: {}", self, self.describe());
    }
}
impl PrintableShape for Circle {}  // Circle already implements Shape + Display

fn main() {
    let circle = Circle { radius: 5.0 };
    let rect = Rectangle { width: 3.0, height: 4.0 };

    // Static dispatch
    print_shape_static(&circle);
    print_shape_generic(&rect);
    print_two_shapes(&circle, &rect);

    // Dynamic dispatch — heterogeneous collection
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 1.0 }),
        Box::new(Rectangle { width: 2.0, height: 3.0 }),
        Box::new(Circle { radius: 10.0 }),
    ];
    process_shapes(&shapes);

    // Default method usage
    println!("Large? {}", circle.is_large()); // area = ~78.5, so false
    println!("Large? {}", Circle { radius: 20.0 }.is_large()); // area = ~1256.6, true

    // Supertrait
    circle.print();

    let pair = Pair { first: 5, second: 10 };
    pair.cmp_display();
}
```

```
STATIC vs DYNAMIC DISPATCH — DECISION FLOWCHART
─────────────────────────────────────────────────────────
Do you know ALL types at compile time?
           │
    ┌──────┴──────┐
    YES            NO
    │              │
    │         Do you need a
    │         heterogeneous collection?
    │         (Vec of mixed types)
    │              │
    │         ┌────┴────┐
    │         YES       NO
    │         │         │
    │    dyn Trait   impl Trait
    │    (dynamic    (static, but
    │     dispatch)   one at a time)
    │
impl Trait / T: Trait
(static dispatch → fastest)
─────────────────────────────────────────────────────────
```

```
INTERFACE (GO) vs TRAIT (RUST) COMPARISON
─────────────────────────────────────────────────────────────────
Feature                    Go Interface      Rust Trait
──────────────────────    ──────────────    ──────────────────
Satisfaction               Implicit          Explicit (impl)
Default methods            ❌                ✅
Static dispatch            ❌ (always dyn)   ✅ (impl Trait)
Dynamic dispatch           ✅ (always)       ✅ (dyn Trait)
Data in interface          ❌                ❌
Type system nil trap       ✅ (exists!)      ❌ (no null)
Multiple trait objects     ❌                ✅ (dyn A + B)
Trait composition          ✅ (embedding)    ✅ (supertraits)
Blanket impl               ❌                ✅
─────────────────────────────────────────────────────────────────
```

---

## 7. Enums — Go's iota vs Rust's Algebraic Types

### What are Enums?

**Enumeration (enum)** is a type that can be one of several named values. Example: a direction can be North, South, East, or West — exactly one of these at any time.

```
ENUM MENTAL MODEL
─────────────────────────────────────────────────────────
A variable of enum type is like a container that can hold
EXACTLY ONE of its variants at any given time.

Direction: [North | South | East | West]
           ← EXACTLY ONE is "active"

Rust enums are more powerful — each variant can CARRY DATA:
Shape: Circle(radius: f64)
     | Rectangle(w: f64, h: f64)
     | Triangle(a: f64, b: f64, c: f64)
─────────────────────────────────────────────────────────
```

### Go — iota-based Enums (Simple, Limited)

```go
package main

import "fmt"

// ── BASIC ENUM WITH iota ──────────────────────────────────────
// iota is a compile-time counter that resets to 0 at each const block
type Direction int // Go enums are just named integer types

const (
    North Direction = iota // 0
    South                  // 1
    East                   // 2
    West                   // 3
)

func (d Direction) String() string {
    switch d {
    case North: return "North"
    case South: return "South"
    case East:  return "East"
    case West:  return "West"
    default:    return fmt.Sprintf("Direction(%d)", int(d))
    }
}

// ── IOTA TRICKS ───────────────────────────────────────────────
type ByteSize float64

const (
    _           = iota             // skip first value (ignore 0)
    KB ByteSize = 1 << (10 * iota) // 1 << 10 = 1024
    MB                             // 1 << 20 = 1,048,576
    GB                             // 1 << 30
    TB                             // 1 << 40
)

// ── ENUM STATES (common Go pattern) ──────────────────────────
type OrderStatus int

const (
    OrderPending   OrderStatus = iota
    OrderConfirmed
    OrderShipped
    OrderDelivered
    OrderCancelled
)

func (s OrderStatus) IsTerminal() bool {
    return s == OrderDelivered || s == OrderCancelled
}

func (s OrderStatus) CanTransitionTo(next OrderStatus) bool {
    transitions := map[OrderStatus][]OrderStatus{
        OrderPending:   {OrderConfirmed, OrderCancelled},
        OrderConfirmed: {OrderShipped, OrderCancelled},
        OrderShipped:   {OrderDelivered},
    }
    for _, allowed := range transitions[s] {
        if allowed == next {
            return true
        }
    }
    return false
}

// ── GO'S LIMITATION: No Algebraic Enums ──────────────────────
// In Go, an enum CANNOT carry different data per variant.
// To simulate a "sum type" (tagged union), you use interfaces:

type Shape interface {
    Area() float64
}

type CircleShape struct{ Radius float64 }
type RectShape struct{ Width, Height float64 }

func (c CircleShape) Area() float64 { return 3.14159 * c.Radius * c.Radius }
func (r RectShape) Area() float64   { return r.Width * r.Height }

// This works but has downsides:
// 1. No exhaustiveness checking — if you add a new type, no warning
// 2. Less ergonomic than Rust pattern matching
// 3. Requires type assertions to access the inner data

func processShape(s Shape) {
    switch v := s.(type) {
    case CircleShape:
        fmt.Printf("Circle: r=%.2f, area=%.2f\n", v.Radius, v.Area())
    case RectShape:
        fmt.Printf("Rect: %v×%v, area=%.2f\n", v.Width, v.Height, v.Area())
    // If you add Triangle tomorrow and forget this switch → silent bug!
    }
}

func main() {
    fmt.Println(North, South, East, West)
    fmt.Printf("KB=%.0f, MB=%.0f, GB=%.0f\n", float64(KB), float64(MB), float64(GB))

    status := OrderPending
    fmt.Println(status.CanTransitionTo(OrderConfirmed)) // true
    fmt.Println(status.CanTransitionTo(OrderDelivered)) // false

    shapes := []Shape{
        CircleShape{Radius: 5},
        RectShape{Width: 3, Height: 4},
    }
    for _, s := range shapes {
        processShape(s)
    }
}
```

### Rust — Algebraic Data Types (ADTs)

```rust
// ── RUST ENUMS ARE ALGEBRAIC DATA TYPES ───────────────────────
// Each variant can hold DIFFERENT types and amounts of data
// This is called a "sum type" or "discriminated union"

#[derive(Debug)]
enum Direction {
    North,
    South,
    East,
    West,
}

// ── ENUM WITH DIFFERENT DATA PER VARIANT ─────────────────────
#[derive(Debug)]
enum Shape {
    Circle { radius: f64 },           // named fields (like a struct)
    Rectangle { width: f64, height: f64 },
    Triangle(f64, f64, f64),          // tuple-style (sides a, b, c)
    Point,                            // no data (unit variant)
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
            Shape::Rectangle { width, height } => width * height,
            Shape::Triangle(a, b, c) => {
                // Heron's formula
                let s = (a + b + c) / 2.0;
                (s * (s - a) * (s - b) * (s - c)).sqrt()
            }
            Shape::Point => 0.0,
        }
    }

    fn perimeter(&self) -> f64 {
        match self {
            Shape::Circle { radius } => 2.0 * std::f64::consts::PI * radius,
            Shape::Rectangle { width, height } => 2.0 * (width + height),
            Shape::Triangle(a, b, c) => a + b + c,
            Shape::Point => 0.0,
        }
    }
}

// ── REAL WORLD: A MESSAGE PROTOCOL ───────────────────────────
// This is where Rust enums SHINE — modeling protocol messages
#[derive(Debug)]
enum Message {
    Quit,                       // no data
    Move { x: i32, y: i32 },   // named fields
    Write(String),              // single String
    ChangeColor(u8, u8, u8),   // RGB tuple
}

fn process_message(msg: Message) {
    match msg {
        Message::Quit => {
            println!("Quitting.");
        }
        Message::Move { x, y } => {
            println!("Moving to ({}, {})", x, y);
        }
        Message::Write(text) => {
            println!("Writing: {}", text);
        }
        Message::ChangeColor(r, g, b) => {
            println!("Color: rgb({}, {}, {})", r, g, b);
        }
        // The compiler ENFORCES exhaustiveness!
        // If you add a new variant and forget to handle it → compile error
    }
}

// ── ENUM AS STATE MACHINE ─────────────────────────────────────
#[derive(Debug, PartialEq)]
enum TrafficLight {
    Red,
    Yellow,
    Green,
}

impl TrafficLight {
    fn next(&self) -> TrafficLight {
        match self {
            TrafficLight::Red    => TrafficLight::Green,
            TrafficLight::Green  => TrafficLight::Yellow,
            TrafficLight::Yellow => TrafficLight::Red,
        }
    }

    fn duration_seconds(&self) -> u32 {
        match self {
            TrafficLight::Red    => 60,
            TrafficLight::Yellow => 5,
            TrafficLight::Green  => 45,
        }
    }
}

// ── RECURSIVE ENUMS (LINKED LIST) ────────────────────────────
// An enum variant can contain the same enum type — creates recursive structure
// Needs Box<> to make the size known at compile time
#[derive(Debug)]
enum LinkedList {
    Cons(i32, Box<LinkedList>), // a node: value + pointer to rest
    Nil,                        // end of list
}

impl LinkedList {
    fn sum(&self) -> i32 {
        match self {
            LinkedList::Cons(val, rest) => val + rest.sum(),
            LinkedList::Nil => 0,
        }
    }
}

fn main() {
    // Shape matching
    let shapes = vec![
        Shape::Circle { radius: 5.0 },
        Shape::Rectangle { width: 3.0, height: 4.0 },
        Shape::Triangle(3.0, 4.0, 5.0),
        Shape::Point,
    ];

    for shape in &shapes {
        println!("{:?}: area={:.2}, perimeter={:.2}", shape, shape.area(), shape.perimeter());
    }

    // Messages
    let messages = vec![
        Message::Quit,
        Message::Move { x: 10, y: 20 },
        Message::Write(String::from("hello")),
        Message::ChangeColor(255, 0, 128),
    ];
    for msg in messages {
        process_message(msg);
    }

    // Traffic light state machine
    let mut light = TrafficLight::Red;
    for _ in 0..6 {
        println!("{:?}: {}s", light, light.duration_seconds());
        light = light.next();
    }

    // Linked list
    let list = LinkedList::Cons(1,
        Box::new(LinkedList::Cons(2,
            Box::new(LinkedList::Cons(3,
                Box::new(LinkedList::Nil))))));
    println!("List sum: {}", list.sum()); // 6
}
```

```
ENUM VARIANT MEMORY LAYOUT IN RUST
─────────────────────────────────────────────────────────
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
    Point,
}

Memory layout (tagged union):
┌─────────────┬──────────────────────────┐
│  tag (u8)   │  data (max variant size) │
│  0=Circle   │  radius: f64             │
│  1=Rect     │  width: f64, height: f64 │
│  2=Point    │  (empty)                 │
└─────────────┴──────────────────────────┘

Total size = tag + max(sizeof(Circle), sizeof(Rectangle), 0)
           = 1 + max(8, 16, 0) = 1 + 16 = 17 bytes
           (with alignment padding: 24 bytes)

Special case: Option<Box<T>> is the SAME SIZE as *T
because Rust knows a Box can never be zero, so
None = null pointer → no extra tag needed!
─────────────────────────────────────────────────────────
```

---

## 8. Null Safety — nil vs Option\<T\>

### What is the Null Problem?

Tony Hoare (inventor of null references) called it his "billion-dollar mistake" — null pointers have caused countless crashes and security vulnerabilities. When a variable can be null AND a non-null value, and you forget to check, you get a **null pointer dereference** — immediate crash.

```
THE NULL PROBLEM
─────────────────────────────────────────────────────────
Without null safety:

   User user = database.findUser(id);
   // user could be null if not found!
   user.getName(); // ← CRASH if user is null
   // The compiler doesn't warn you!

With null safety (Rust's approach):

   let user: Option<User> = database.find_user(id);
   // The type FORCES you to handle the None case
   match user {
       Some(u) => u.get_name(),
       None    => "Unknown".to_string(),
   }
─────────────────────────────────────────────────────────
```

### Go — nil (the dangerous way)

```go
package main

import (
    "errors"
    "fmt"
)

// ── NIL IN GO ─────────────────────────────────────────────────
// nil is Go's null value. These types can be nil:
// - pointers (*T)
// - interfaces
// - slices
// - maps
// - channels
// - functions

type User struct {
    Name  string
    Email string
}

func findUser(id int) *User {
    if id == 1 {
        return &User{Name: "Alice", Email: "alice@example.com"}
    }
    return nil // user not found
}

// ── NIL MUST BE MANUALLY CHECKED ─────────────────────────────
func getUserName(id int) string {
    user := findUser(id)
    if user == nil {
        return "Unknown" // must remember to check
    }
    return user.Name
}

// ── NIL PANIC ─────────────────────────────────────────────────
func badGetUserName(id int) string {
    user := findUser(id)
    return user.Name // PANIC if user == nil: "invalid memory address or nil pointer dereference"
}

// ── OPTIONAL PATTERN IN GO (workaround) ──────────────────────
// Go doesn't have Option<T>, but you can simulate with:

// 1. Pointer + nil check (most common)
type Config struct {
    Timeout *int // optional: nil means "use default"
}

// 2. ok pattern (like map access)
func lookupUser(cache map[int]User, id int) (User, bool) {
    user, ok := cache[id] // ok is false if key not found
    return user, ok
}

// 3. Sentinel values (fragile)
func findScore(scores map[string]int, name string) int {
    score, ok := scores[name]
    if !ok {
        return -1 // sentinel: -1 means "not found" — but what if valid score is -1?
    }
    return score
}

// ── INTERFACE NIL TRAP (revisited) ────────────────────────────
type ErrNotFound struct{ ID int }
func (e *ErrNotFound) Error() string { return fmt.Sprintf("user %d not found", e.ID) }

func riskyFunction(returnErr bool) error {
    var e *ErrNotFound
    if returnErr {
        e = &ErrNotFound{ID: 42}
    }
    return e // TRAP: non-nil interface even when e == nil!
}

func main() {
    fmt.Println(getUserName(1)) // "Alice"
    fmt.Println(getUserName(2)) // "Unknown"

    // Safe map lookup
    cache := map[int]User{1: {Name: "Alice"}}
    if user, ok := lookupUser(cache, 1); ok {
        fmt.Println("Found:", user.Name)
    }
    if _, ok := lookupUser(cache, 99); !ok {
        fmt.Println("Not found")
    }

    // The nil interface trap
    err := riskyFunction(false)
    if err != nil {
        // This prints — but shouldn't!
        fmt.Println("Bug: unexpected non-nil:", err)
    }
    // Correct fix: always return untyped nil: return nil

    _ = errors.New("just showing imports work")
}
```

### Rust — Option\<T\> (The Safe Way)

```rust
// ── OPTION<T> IN RUST ─────────────────────────────────────────
// Option<T> is a standard library enum:
// enum Option<T> { Some(T), None }
// This is the ONLY way to express "this value might not exist"
// NULL DOES NOT EXIST in safe Rust!

#[derive(Debug)]
struct User {
    name: String,
    email: String,
}

fn find_user(id: u32) -> Option<User> {
    if id == 1 {
        Some(User {
            name: "Alice".to_string(),
            email: "alice@example.com".to_string(),
        })
    } else {
        None // user not found — EXPLICIT, type-safe
    }
}

// ── WORKING WITH OPTION ───────────────────────────────────────
fn demonstrate_option() {
    let user = find_user(1);
    let missing = find_user(99);

    // 1. match — most explicit
    match user {
        Some(u) => println!("Found: {}", u.name),
        None    => println!("Not found"),
    }

    // 2. if let — when you only care about Some
    if let Some(u) = find_user(1) {
        println!("Name: {}", u.name);
    }

    // 3. unwrap() — panics if None (use only when you KNOW it's Some)
    let u = find_user(1).unwrap(); // panics if None!
    println!("Unwrapped: {}", u.name);

    // 4. unwrap_or() — provide a default value
    let name = find_user(99)
        .map(|u| u.name)
        .unwrap_or_else(|| "Unknown".to_string());
    println!("Name or default: {}", name);

    // 5. ? operator — propagate None up the call stack
    // (see section 9 for more on ?)

    // 6. map() — transform the inner value if Some
    let email: Option<String> = find_user(1).map(|u| u.email);
    println!("Email: {:?}", email);

    // 7. and_then() — chain operations that might fail (flatMap)
    let user_id: Option<u32> = Some(1);
    let user_data: Option<String> = user_id
        .and_then(|id| find_user(id))        // Option<User>
        .and_then(|u| {                      // Option<String>
            if u.email.contains('@') {
                Some(u.email)
            } else {
                None
            }
        });
    println!("User data: {:?}", user_data);

    // 8. filter() — convert Some to None based on condition
    let adult_user = find_user(1).filter(|u| u.name.len() > 3);
    println!("Adult user: {:?}", adult_user.map(|u| u.name));

    // 9. or() / or_else() — fallback if None
    let result = find_user(99)
        .or_else(|| find_user(1))  // try user 1 if 99 not found
        .map(|u| u.name)
        .unwrap_or("totally unknown".to_string());
    println!("Fallback result: {}", result);

    // 10. is_some() / is_none()
    println!("User 1 exists: {}", find_user(1).is_some()); // true
    println!("User 99 exists: {}", find_user(99).is_some()); // false

    let _ = missing;
}

// ── OPTION IN STRUCTS ─────────────────────────────────────────
#[derive(Debug)]
struct Config {
    host: String,
    port: u16,
    timeout: Option<u64>,    // optional timeout
    proxy: Option<String>,   // optional proxy URL
}

impl Config {
    fn effective_timeout(&self) -> u64 {
        self.timeout.unwrap_or(30) // default 30 seconds
    }
}

// ── ? OPERATOR WITH OPTION ────────────────────────────────────
fn get_user_email(id: u32) -> Option<String> {
    // ? unwraps Some, or returns None early from this function
    let user = find_user(id)?; // if None, immediately return None
    let email = if user.email.is_empty() { return None; } else { user.email };
    Some(email)
}

fn main() {
    demonstrate_option();

    let config = Config {
        host: "localhost".to_string(),
        port: 8080,
        timeout: Some(60),
        proxy: None,
    };
    println!("Timeout: {}", config.effective_timeout());

    println!("Email for user 1: {:?}", get_user_email(1));
    println!("Email for user 99: {:?}", get_user_email(99));
}
```

```
OPTION<T> CHAINING — RAILROAD MODEL
─────────────────────────────────────────────────────────
Think of Option as a train track with TWO rails:

    Some(value)  ●━━━━map()━━━━●━━━and_then()━━━●  Some(result)
                  \            |                /
    None         ●──────────────────────────────●  None
                 (skips ALL operations — passes through)

This is called "railway-oriented programming"
─────────────────────────────────────────────────────────
```

---

## 9. Error Handling — (T, error) vs Result\<T, E\>

### Philosophy of Error Handling

Errors come in two flavors:
1. **Recoverable errors**: file not found, network timeout — the program can handle these
2. **Unrecoverable errors**: out of memory, assertion failed — the program should stop

```
ERROR HANDLING PHILOSOPHIES
─────────────────────────────────────────────────────────
C:        Return codes (int error codes) — easy to ignore
Java/C#:  Exceptions — invisible control flow
Go:       Explicit (T, error) return — verbose but visible
Rust:     Result<T, E> type — unignorable by type system
─────────────────────────────────────────────────────────
```

### Go Error Handling

```go
package main

import (
    "errors"
    "fmt"
    "strconv"
)

// ── GO ERROR INTERFACE ────────────────────────────────────────
// error is a built-in interface:
// type error interface { Error() string }
// Any type with Error() string method is an error

// ── CUSTOM ERROR TYPES ────────────────────────────────────────
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error: %s - %s", e.Field, e.Message)
}

type NotFoundError struct {
    Resource string
    ID       int
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s with ID %d not found", e.Resource, e.ID)
}

// ── FUNCTIONS RETURNING ERRORS ────────────────────────────────
func parseAge(s string) (int, error) {
    age, err := strconv.Atoi(s)
    if err != nil {
        return 0, fmt.Errorf("parseAge: invalid age string %q: %w", s, err) // %w wraps the error
    }
    if age < 0 || age > 150 {
        return 0, &ValidationError{Field: "age", Message: "must be between 0 and 150"}
    }
    return age, nil
}

// ── ERROR PROPAGATION ─────────────────────────────────────────
func processUser(ageStr string) (string, error) {
    age, err := parseAge(ageStr)
    if err != nil {
        return "", fmt.Errorf("processUser: %w", err) // wrap to add context
    }
    return fmt.Sprintf("User is %d years old", age), nil
}

// ── SENTINEL ERRORS ───────────────────────────────────────────
var ErrNotFound = errors.New("not found")
var ErrPermission = errors.New("permission denied")

func lookupItem(id int) (string, error) {
    if id < 0 {
        return "", ErrPermission
    }
    if id > 100 {
        return "", ErrNotFound
    }
    return fmt.Sprintf("item-%d", id), nil
}

// ── ERRORS.AS / ERRORS.IS ─────────────────────────────────────
// Check for specific error types through a chain of wrapping
func handleErrors() {
    _, err := processUser("not-a-number")
    if err != nil {
        // errors.Is: check if error chain contains a specific value
        if errors.Is(err, strconv.ErrSyntax) {
            // Note: needs to unwrap through processUser's wrapping
        }

        // errors.As: extract specific error type from chain
        var valErr *ValidationError
        if errors.As(err, &valErr) {
            fmt.Printf("Validation failed on field: %s\n", valErr.Field)
        }

        fmt.Println(err)
    }
}

// ── MULTIPLE RETURN VALUES EVERYWHERE ─────────────────────────
// The Go pattern forces verbose but explicit error checking
func multiStep() (int, error) {
    a, err := parseAge("25")
    if err != nil {
        return 0, fmt.Errorf("step1: %w", err)
    }

    b, err := parseAge("30")
    if err != nil {
        return 0, fmt.Errorf("step2: %w", err)
    }

    // "if err != nil { return err }" repeats constantly — Go criticism
    return a + b, nil
}

func main() {
    // Success case
    if result, err := processUser("25"); err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Println(result)
    }

    // Error case
    if _, err := processUser("invalid"); err != nil {
        fmt.Println("Error:", err)
    }

    handleErrors()

    item, err := lookupItem(50)
    if err == nil {
        fmt.Println("Found:", item)
    }

    _, err = lookupItem(200)
    if errors.Is(err, ErrNotFound) {
        fmt.Println("Item not found (using sentinel)")
    }

    sum, _ := multiStep()
    fmt.Println("Sum:", sum)
}
```

### Rust — Result\<T, E\> (Type-Safe Errors)

```rust
use std::num::ParseIntError;
use std::fmt;

// ── RESULT<T, E> IS AN ENUM ───────────────────────────────────
// enum Result<T, E> { Ok(T), Err(E) }
// T = success type, E = error type
// The ERROR TYPE IS EXPLICIT — you know what errors a function can produce

// ── CUSTOM ERROR TYPES ────────────────────────────────────────
#[derive(Debug)]
enum AppError {
    ParseError(ParseIntError),
    ValidationError { field: String, message: String },
    NotFound { resource: String, id: u32 },
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::ParseError(e) => write!(f, "parse error: {}", e),
            AppError::ValidationError { field, message } =>
                write!(f, "validation error: {} - {}", field, message),
            AppError::NotFound { resource, id } =>
                write!(f, "{} with ID {} not found", resource, id),
        }
    }
}

// Implement From trait for automatic conversion (powers the ? operator)
impl From<ParseIntError> for AppError {
    fn from(e: ParseIntError) -> Self {
        AppError::ParseError(e)
    }
}

// ── FUNCTIONS RETURNING RESULT ────────────────────────────────
fn parse_age(s: &str) -> Result<u32, AppError> {
    // str::parse returns Result<u32, ParseIntError>
    // The ? converts ParseIntError → AppError using From<ParseIntError>
    let age: u32 = s.parse()?; // ? = unwrap Ok, or convert Err and return early

    if age > 150 {
        return Err(AppError::ValidationError {
            field: "age".to_string(),
            message: "must be between 0 and 150".to_string(),
        });
    }
    Ok(age) // wrap success value in Ok
}

fn process_user(age_str: &str) -> Result<String, AppError> {
    let age = parse_age(age_str)?; // ? propagates error up
    Ok(format!("User is {} years old", age))
}

// ── THE ? OPERATOR IN DETAIL ──────────────────────────────────
// fn foo() -> Result<T, E> {
//     let value = some_result?;  is EQUIVALENT to:
//     let value = match some_result {
//         Ok(v) => v,
//         Err(e) => return Err(e.into()), // .into() converts using From
//     };
// }

// ── MULTI-STEP OPERATIONS — CLEAN COMPARED TO GO ─────────────
fn multi_step() -> Result<u32, AppError> {
    let a = parse_age("25")?;  // propagates on error
    let b = parse_age("30")?;  // propagates on error
    let c = parse_age("45")?;
    Ok(a + b + c)
    // No "if err != nil" boilerplate — each ? handles it
}

// ── COMBINATORS ON RESULT ─────────────────────────────────────
fn demonstrate_combinators() {
    // map — transform Ok value
    let doubled = parse_age("20").map(|age| age * 2);
    println!("Doubled age: {:?}", doubled);

    // map_err — transform Err value
    let stringified = parse_age("bad").map_err(|e| format!("Error: {}", e));
    println!("String error: {:?}", stringified);

    // and_then — chain fallible operations (flatMap for Result)
    let result = parse_age("25")
        .and_then(|age| {
            if age >= 18 {
                Ok(format!("Adult user, age {}", age))
            } else {
                Err(AppError::ValidationError {
                    field: "age".to_string(),
                    message: "must be adult".to_string(),
                })
            }
        });
    println!("Chain result: {:?}", result);

    // unwrap_or / unwrap_or_else
    let age = parse_age("bad").unwrap_or(0);
    let age2 = parse_age("bad").unwrap_or_else(|_| 18); // default 18
    println!("Fallback ages: {}, {}", age, age2);

    // ok() — convert Result<T,E> to Option<T> (discards error)
    let as_option: Option<u32> = parse_age("25").ok();
    println!("As option: {:?}", as_option);
}

// ── REAL WORLD: FILE PROCESSING WITH ERRORS ──────────────────
use std::fs;
use std::io;

fn read_config(path: &str) -> Result<String, io::Error> {
    let content = fs::read_to_string(path)?; // propagate io::Error
    Ok(content.trim().to_string())
}

// ── COLLECTING RESULTS ────────────────────────────────────────
fn demonstrate_collect_results() {
    let strings = vec!["1", "2", "bad", "4"];

    // Collect into Result<Vec<i32>, ParseIntError>
    // Stops at first error
    let result: Result<Vec<i32>, _> = strings.iter()
        .map(|s| s.parse::<i32>())
        .collect();
    println!("Collected result: {:?}", result); // Err(ParseIntError)

    // Only collect the successful ones using filter_map
    let successes: Vec<i32> = strings.iter()
        .filter_map(|s| s.parse::<i32>().ok())
        .collect();
    println!("Successes only: {:?}", successes); // [1, 2, 4]
}

// ── PANIC (unrecoverable errors) ──────────────────────────────
fn demonstrate_panic() {
    // panic! = immediate crash (like assertion failure)
    // Used for programmer errors, not expected runtime errors

    // panic!("something went horribly wrong");

    // assert! / assert_eq! / assert_ne! also panic on failure
    let x = 5;
    assert!(x > 0, "x must be positive");
    assert_eq!(x, 5, "x should be 5");

    // unwrap() and expect() panic on None/Err
    let v = vec![1, 2, 3];
    let _ = v.get(0).expect("vector should have elements"); // .expect(msg) = unwrap with message
}

fn main() {
    match process_user("25") {
        Ok(msg) => println!("{}", msg),
        Err(e) => println!("Error: {}", e),
    }

    match process_user("invalid") {
        Ok(msg) => println!("{}", msg),
        Err(e) => println!("Error: {}", e),
    }

    match multi_step() {
        Ok(sum) => println!("Multi-step sum: {}", sum),
        Err(e) => println!("Multi-step error: {}", e),
    }

    demonstrate_combinators();
    demonstrate_collect_results();
    demonstrate_panic();
}
```

```
RESULT<T,E> RAILROAD MODEL
─────────────────────────────────────────────────────────
function chain using ?:

parse_age("25")  ──── Ok(25) ───── process_user ──── Ok("User is 25") → caller
                 \                              \
parse_age("bad") ──── Err(e) ────────────────────────────────────────→ Err(e) returned

Each ? is a "track switch" — on success, keep going; on error, jump to the error track
─────────────────────────────────────────────────────────
```

---

## 10. Generics — Parameterizing Over Types

### What are Generics?

**Generics** allow you to write code that works for multiple types, with the type specified by the caller. Like a template where the type is a parameter.

```
GENERIC MENTAL MODEL
─────────────────────────────────────────────────────────
Without generics: write separate functions for each type
  fn max_int(a: i32, b: i32) -> i32
  fn max_float(a: f64, b: f64) -> f64
  fn max_str(a: &str, b: &str) -> &str

With generics: write ONE function
  fn max<T: PartialOrd>(a: T, b: T) -> T
  ↑ T is a TYPE PARAMETER — filled in by the compiler
─────────────────────────────────────────────────────────
```

### Go Generics (since Go 1.18)

```go
package main

import "fmt"

// ── GENERIC FUNCTIONS ─────────────────────────────────────────
// [T any] means "T can be any type"
// 'any' is an alias for 'interface{}'
func Map[T, U any](slice []T, f func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = f(v)
    }
    return result
}

func Filter[T any](slice []T, f func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if f(v) {
            result = append(result, v)
        }
    }
    return result
}

func Reduce[T, U any](slice []T, initial U, f func(U, T) U) U {
    result := initial
    for _, v := range slice {
        result = f(result, v)
    }
    return result
}

// ── TYPE CONSTRAINTS ──────────────────────────────────────────
// Constraints limit what types T can be

// Built-in constraints from golang.org/x/exp/constraints:
// comparable — can use == and !=
// ordered     — can use <, <=, >, >=

// Custom constraint — union of types using |
type Number interface {
    int | int8 | int16 | int32 | int64 |
    uint | uint8 | uint16 | uint32 | uint64 |
    float32 | float64
}

// ~int means "int OR any type whose UNDERLYING type is int"
type Integer interface {
    ~int | ~int32 | ~int64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

func Max[T interface{ ~int | ~float64 | ~string }](a, b T) T {
    if a > b {
        return a
    }
    return b
}

// ── GENERIC STRUCTS ───────────────────────────────────────────
// A generic Stack (LIFO data structure)
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
    if len(s.items) == 0 {
        var zero T
        return zero, false
    }
    last := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return last, true
}

func (s *Stack[T]) Peek() (T, bool) {
    if len(s.items) == 0 {
        var zero T
        return zero, false
    }
    return s.items[len(s.items)-1], true
}

func (s *Stack[T]) Len() int { return len(s.items) }

// ── GENERIC BINARY SEARCH ─────────────────────────────────────
type Ordered interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~float32 | ~float64 | ~string
}

func BinarySearch[T Ordered](sorted []T, target T) int {
    low, high := 0, len(sorted)-1
    for low <= high {
        mid := (low + high) / 2
        if sorted[mid] == target {
            return mid
        } else if sorted[mid] < target {
            low = mid + 1
        } else {
            high = mid - 1
        }
    }
    return -1
}

// ── MULTIPLE TYPE PARAMETERS ──────────────────────────────────
type Pair[K comparable, V any] struct {
    Key   K
    Value V
}

func NewPair[K comparable, V any](k K, v V) Pair[K, V] {
    return Pair[K, V]{Key: k, Value: v}
}

func main() {
    // Map
    nums := []int{1, 2, 3, 4, 5}
    doubled := Map(nums, func(n int) int { return n * 2 })
    strs := Map(nums, func(n int) string { return fmt.Sprintf("num%d", n) })
    fmt.Println("Doubled:", doubled)
    fmt.Println("Strings:", strs)

    // Filter
    evens := Filter(nums, func(n int) bool { return n%2 == 0 })
    fmt.Println("Evens:", evens)

    // Reduce
    sum := Reduce(nums, 0, func(acc, n int) int { return acc + n })
    fmt.Println("Sum:", sum)

    // Generic Sum with constraint
    floats := []float64{1.1, 2.2, 3.3}
    fmt.Printf("Float sum: %.1f\n", Sum(floats))
    fmt.Printf("Int sum: %d\n", Sum(nums))

    // Max
    fmt.Println("Max int:", Max(3, 7))
    fmt.Println("Max str:", Max("apple", "banana"))

    // Stack
    var intStack Stack[int]
    intStack.Push(1)
    intStack.Push(2)
    intStack.Push(3)
    if val, ok := intStack.Pop(); ok {
        fmt.Println("Popped:", val) // 3
    }

    // BinarySearch
    sorted := []int{1, 3, 5, 7, 9, 11, 13}
    fmt.Println("Found 7 at index:", BinarySearch(sorted, 7)) // 3
    fmt.Println("Found 6 at index:", BinarySearch(sorted, 6)) // -1

    // Pair
    p := NewPair("name", "Alice")
    fmt.Printf("Pair: %v -> %v\n", p.Key, p.Value)
}
```

### Rust Generics (More Powerful, Established Since Day 1)

```rust
use std::fmt;

// ── GENERIC FUNCTIONS ─────────────────────────────────────────
fn map_vec<T, U, F>(v: &[T], f: F) -> Vec<U>
where
    F: Fn(&T) -> U,
{
    v.iter().map(f).collect()
}

// ── TRAIT BOUNDS AS CONSTRAINTS ───────────────────────────────
// T: PartialOrd means "T must implement PartialOrd (supports <, >)"
fn max_val<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

// Multiple bounds with + syntax
fn print_and_compare<T: fmt::Display + PartialOrd>(a: T, b: T) {
    println!("{} vs {}: ", a, b);
    if a > b { println!("{} wins", a); }
    else { println!("{} wins", b); }
}

// ── GENERIC STRUCTS ───────────────────────────────────────────
#[derive(Debug)]
struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self {
        Stack { items: Vec::new() }
    }

    fn push(&mut self, item: T) {
        self.items.push(item);
    }

    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }

    fn peek(&self) -> Option<&T> {
        self.items.last()
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    fn len(&self) -> usize {
        self.items.len()
    }
}

// Only available when T: fmt::Display
impl<T: fmt::Display> Stack<T> {
    fn print_all(&self) {
        for item in &self.items {
            print!("{} ", item);
        }
        println!();
    }
}

// ── GENERIC ENUMS (stdlib uses this pattern) ─────────────────
// Option<T> and Result<T,E> are just generic enums in std library!
// enum Option<T> { Some(T), None }
// enum Result<T, E> { Ok(T), Err(E) }

// ── ASSOCIATED TYPES — A Powerful Pattern ────────────────────
// Instead of type parameters, a trait can have ASSOCIATED TYPES
// These are type parameters defined by the implementor, not the caller

trait Iterator {
    type Item;  // associated type
    fn next(&mut self) -> Option<Self::Item>;
}

// This matters because:
// - fn foo<T, I: Iterator<Item=T>>(...) — with type parameter
// - fn foo<I: Iterator>(...) — simpler! I::Item is inferred

// ── CONST GENERICS — Types Parameterized by Values ───────────
// A type that is generic over a CONSTANT VALUE (not a type)
struct Matrix<T, const ROWS: usize, const COLS: usize> {
    data: [[T; COLS]; ROWS],  // fixed-size 2D array
}

impl<T: Default + Copy, const ROWS: usize, const COLS: usize>
    Matrix<T, ROWS, COLS>
{
    fn new() -> Self {
        Matrix {
            data: [[T::default(); COLS]; ROWS],
        }
    }

    fn get(&self, row: usize, col: usize) -> &T {
        &self.data[row][col]
    }

    fn set(&mut self, row: usize, col: usize, val: T) {
        self.data[row][col] = val;
    }
}

// ── MONOMORPHIZATION — HOW GENERICS COMPILE ──────────────────
// When you call max_val(3_i32, 5_i32), the compiler generates:
//   fn max_val_i32(a: i32, b: i32) -> i32 { ... }
// When you call max_val(3.0_f64, 5.0_f64):
//   fn max_val_f64(a: f64, b: f64) -> f64 { ... }
// ZERO runtime cost! Unlike Java's type erasure.

// ── WHERE CLAUSES FOR COMPLEX BOUNDS ─────────────────────────
fn complex_function<T, U, F>(items: &[T], transform: F) -> Vec<U>
where
    T: Clone + fmt::Debug,
    U: fmt::Display + Default,
    F: Fn(T) -> U,
{
    items.iter().cloned().map(transform).collect()
}

fn main() {
    // map_vec
    let nums = vec![1, 2, 3, 4, 5];
    let doubled = map_vec(&nums, |&x| x * 2);
    let as_strs = map_vec(&nums, |&x| x.to_string());
    println!("Doubled: {:?}", doubled);
    println!("Strings: {:?}", as_strs);

    // max_val with different types
    println!("Max i32: {}", max_val(3_i32, 7_i32));
    println!("Max f64: {}", max_val(3.14_f64, 2.71_f64));
    println!("Max str: {}", max_val("apple", "banana"));

    // Stack
    let mut stack: Stack<i32> = Stack::new();
    stack.push(1);
    stack.push(2);
    stack.push(3);
    stack.print_all();
    println!("Popped: {:?}", stack.pop()); // Some(3)
    println!("Peek: {:?}", stack.peek());  // Some(&2)

    // Const generics
    let mut mat: Matrix<f64, 3, 3> = Matrix::new();
    mat.set(0, 0, 1.0);
    mat.set(1, 1, 5.0);
    mat.set(2, 2, 9.0);
    println!("Matrix[1][1] = {}", mat.get(1, 1)); // 5.0
}
```

```
GENERICS: GO vs RUST
─────────────────────────────────────────────────────────────────
Feature                   Go (1.18+)           Rust
──────────────────────   ──────────────────   ──────────────────
Since version            1.18 (2022)          1.0 (2015)
Type constraints         Interface unions     Trait bounds
Const generics           ❌                   ✅ (const N: usize)
Associated types         ❌ (use type param)  ✅
Default type params      ❌                   ❌ (partial support)
Specialization           ❌                   ❌ (planned)
Monomorphization         ✅                   ✅ (static dispatch)
Type erasure             ❌                   ✅ (dyn Trait = erasure)
HKT (Higher-Kinded)      ❌                   Partial (via GATs)
Complexity               Low                  High
─────────────────────────────────────────────────────────────────
```

---

## 11. Type Aliases and the Newtype Pattern

### Type Aliases — New Name, Same Type

A **type alias** gives an existing type a new name. Both names refer to the SAME type — they are interchangeable.

```go
// ── GO TYPE ALIASES ───────────────────────────────────────────
package main

import "fmt"

// type alias — MyInt IS int, completely interchangeable
type MyInt = int // (= means alias)

// type DEFINITION — UserID is a NEW type with underlying type int
// UserID is NOT the same as int — assignment requires explicit conversion
type UserID int
type ProductID int

func main() {
    var uid UserID = 42
    var pid ProductID = 42

    // Type safety: cannot mix UserID and ProductID even though both are int underneath
    // uid = pid  // COMPILE ERROR: cannot use pid (type ProductID) as type UserID

    // Must explicitly convert
    var raw int = int(uid) // explicit cast required
    fmt.Println(raw)

    // This prevents bugs like: processOrder(userId, productId) called as processOrder(productId, userId)
    // The compiler catches it!

    var alias MyInt = 100
    var regular int = alias // works! They are the SAME type
    fmt.Println(regular)
}
```

```rust
// ── RUST TYPE ALIASES ─────────────────────────────────────────
// type Alias = OriginalType — completely interchangeable
type Meters = f64;
type Kilometers = f64;
// Meters and Kilometers are BOTH f64 — no type safety!

fn add_distance(a: Meters, b: Meters) -> Meters { a + b }

fn type_alias_demo() {
    let m: Meters = 100.0;
    let km: Kilometers = 1.5;
    // These are BOTH f64, so this compiles fine — no safety!
    let wrong = add_distance(m, km); // km treated as Meters — bug!
    println!("{}", wrong);

    // Type aliases are mainly for READABILITY:
    type Result<T> = std::result::Result<T, String>; // shorter alias
    type Thunk = Box<dyn Fn() -> i32>; // complex type gets a short name
}

// ── NEWTYPE PATTERN — True Type Safety in Rust ────────────────
// A tuple struct with ONE field creates a NEW DISTINCT type
// This is the "newtype pattern" — standard Rust idiom

struct Meters(f64);    // wraps f64 but is a DISTINCT type
struct Kilometers(f64);

impl Meters {
    fn value(&self) -> f64 { self.0 }

    fn to_kilometers(&self) -> Kilometers {
        Kilometers(self.0 / 1000.0)
    }
}

impl Kilometers {
    fn value(&self) -> f64 { self.0 }

    fn to_meters(&self) -> Meters {
        Meters(self.0 * 1000.0)
    }
}

impl std::fmt::Display for Meters {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} m", self.0)
    }
}

fn add_meters(a: Meters, b: Meters) -> Meters {
    Meters(a.0 + b.0)
}

// ── REAL WORLD NEWTYPE USE CASES ─────────────────────────────

// 1. Preventing ID confusion
struct UserId(u64);
struct OrderId(u64);
struct ProductId(u64);

fn create_order(user: UserId, product: ProductId, quantity: u32) -> OrderId {
    let _ = (user, product, quantity);
    OrderId(12345) // generated
}

// 2. Implementing external traits on external types (orphan rule)
// You can't impl Display for Vec<i32> (both are external)
// But you CAN create a wrapper:
struct DisplayableVec(Vec<i32>);

impl std::fmt::Display for DisplayableVec {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[{}]", self.0.iter().map(|x| x.to_string())
            .collect::<Vec<_>>().join(", "))
    }
}

// 3. Zero-cost validation wrapper
struct Email(String);

impl Email {
    fn new(s: &str) -> Result<Email, String> {
        if s.contains('@') && s.contains('.') {
            Ok(Email(s.to_string()))
        } else {
            Err(format!("{:?} is not a valid email", s))
        }
    }

    fn as_str(&self) -> &str {
        &self.0
    }
}

// 4. Unit of measure enforcement
struct Celsius(f64);
struct Fahrenheit(f64);

impl Celsius {
    fn to_fahrenheit(&self) -> Fahrenheit {
        Fahrenheit(self.0 * 9.0 / 5.0 + 32.0)
    }
}

fn heat_object(temp: Celsius) {
    println!("Heating to {}°C ({:.1}°F)", temp.0, temp.to_fahrenheit().0);
}

fn main() {
    type_alias_demo();

    // Newtype for units
    let dist1 = Meters(100.0);
    let dist2 = Meters(50.0);
    let total = add_meters(dist1, dist2);
    println!("Total: {}", total); // "150 m"

    let km = Meters(5000.0).to_kilometers();
    println!("5000m = {} km", km.value());

    // IDs - compiler prevents mixing
    let uid = UserId(1);
    let pid = ProductId(42);
    let order = create_order(uid, pid, 3);
    println!("Order: {}", order.0);
    // create_order(pid, uid, 3); // COMPILE ERROR - types are wrong!

    // DisplayableVec
    let v = DisplayableVec(vec![1, 2, 3, 4, 5]);
    println!("{}", v); // [1, 2, 3, 4, 5]

    // Email validation
    match Email::new("user@example.com") {
        Ok(email) => println!("Valid email: {}", email.as_str()),
        Err(e) => println!("Error: {}", e),
    }

    // Temperature units
    heat_object(Celsius(100.0));
    // heat_object(Fahrenheit(212.0)); // COMPILE ERROR - wrong type!
}
```

---

## 12. Ownership — Rust's Type-Level Memory Model

### What is Ownership?

**Ownership** is Rust's most revolutionary feature. The TYPE SYSTEM encodes memory management rules. Every value has an **owner**, and when the owner goes out of scope, the value is automatically freed — NO garbage collector needed.

```
OWNERSHIP RULES (the three laws of Rust)
─────────────────────────────────────────────────────────
1. Every value has exactly ONE owner at any given time
2. When the owner goes out of scope, the value is dropped
3. Ownership can be TRANSFERRED (moved) but not copied
   (unless the type implements the Copy trait)
─────────────────────────────────────────────────────────
```

```
OWNERSHIP TRANSFER (MOVE)
─────────────────────────────────────────────────────────
let s1 = String::from("hello");
┌──────────────────────────────┐
│ s1 → ptr: ████████ │ len: 5  │
│          ▼                   │
│          [h,e,l,l,o]         │
└──────────────────────────────┘

let s2 = s1; // MOVE — s1 is now invalid!
┌──────────────────────────────┐
│ s2 → ptr: ████████ │ len: 5  │
│          ▼                   │
│          [h,e,l,l,o]         │  ← s2 now OWNS this
└──────────────────────────────┘
s1 = MOVED (cannot be used)

// println!("{}", s1); // COMPILE ERROR: value borrowed after move
─────────────────────────────────────────────────────────
```

```rust
// ── BORROWING — Temporary Access Without Transfer ─────────────
// Instead of moving, you can LEND access via references
// & = immutable borrow (read-only access, multiple allowed simultaneously)
// &mut = mutable borrow (read-write access, ONLY ONE at a time)

fn calculate_length(s: &String) -> usize {
    s.len() // s is borrowed — doesn't take ownership
} // s goes out of scope, but since it doesn't own the String, nothing is dropped

fn change_string(s: &mut String) {
    s.push_str(", world"); // can modify because &mut
}

fn demonstrate_borrowing() {
    let s1 = String::from("hello");

    // Immutable borrow — s1 remains the owner
    let len = calculate_length(&s1);
    println!("Length of '{}' is {}", s1, len); // s1 still valid!

    // Mutable borrow
    let mut s2 = String::from("hello");
    change_string(&mut s2);
    println!("{}", s2); // "hello, world"

    // Borrow checker rules:
    // Rule 1: You can have MANY immutable borrows at the same time
    let r1 = &s1;
    let r2 = &s1;
    let r3 = &s1;
    println!("{} {} {}", r1, r2, r3); // fine — all immutable

    // Rule 2: OR one mutable borrow — but NOT both at the same time
    let r4 = &mut s2;
    // let r5 = &s2; // COMPILE ERROR: cannot borrow as immutable while mutably borrowed
    r4.push('!');

    // Rule 3: References must not outlive the data they reference
    // (lifetimes — see section 13)
}

// ── THE BORROW CHECKER PREVENTS REAL BUGS ────────────────────
fn prevented_bug_example() {
    let mut v = vec![1, 2, 3];

    // In C++: invalidated iterator bug is common
    // for (auto it = v.begin(); it != v.end(); ++it) {
    //     v.push_back(*it * 2); // UNDEFINED BEHAVIOR: iterator invalidated!
    // }

    // In Rust: the borrow checker PREVENTS this at compile time
    // for &elem in v.iter() {
    //     v.push(elem * 2); // COMPILE ERROR: cannot borrow v as mutable
    //                       // while it is also borrowed as immutable
    // }

    // Correct approach: collect first, then modify
    let additions: Vec<i32> = v.iter().map(|&x| x * 2).collect();
    v.extend(additions);
    println!("{:?}", v); // [1, 2, 3, 2, 4, 6]
}

// ── COPY vs MOVE ──────────────────────────────────────────────
// Types that implement Copy are DUPLICATED on assignment (not moved)
// Primitives (i32, f64, bool, char, &T) implement Copy
// Heap types (String, Vec<T>) do NOT implement Copy (too expensive)

fn demonstrate_copy() {
    // i32 is Copy
    let x = 5_i32;
    let y = x; // COPY — both x and y are valid
    println!("{} {}", x, y);

    // bool is Copy
    let b1 = true;
    let b2 = b1; // COPY
    println!("{} {}", b1, b2);

    // Tuples of Copy types are Copy
    let t1 = (1_i32, 2.0_f64, true);
    let t2 = t1; // COPY
    println!("{:?} {:?}", t1, t2);

    // String is NOT Copy
    let s1 = String::from("hello");
    let s2 = s1.clone(); // explicit clone (deep copy)
    println!("{} {}", s1, s2); // both valid because we cloned

    // References (&T) are Copy! (copying a reference is cheap)
    let s3 = &s1;
    let s4 = s3; // copying the reference — both point to s1
    println!("{} {}", s3, s4);
}

fn main() {
    demonstrate_borrowing();
    prevented_bug_example();
    demonstrate_copy();
}
```

```
BORROW CHECKER STATE MACHINE
─────────────────────────────────────────────────────────
Value states:
  OWNED → can move, can borrow
  BORROWED (&T) → can read, can take more &T, cannot take &mut T
  MUT BORROWED (&mut T) → can read/write, NO other borrows allowed
  MOVED → cannot use at all

             move          clone
  OWNED ──────────→ dead  ──────→ new OWNED
     │
     │ &T borrow        &mut T borrow
     ↓                       ↓
  BORROWED             MUT BORROWED
  (shared,             (exclusive,
   many ok)             one only)
─────────────────────────────────────────────────────────
```

Go has **no ownership system** — it uses a garbage collector to manage memory. This makes Go simpler but adds GC pause latency and cannot be used in systems where GC is unacceptable (real-time systems, OS kernels, embedded systems).

---

## 13. Lifetimes — Encoding Time Into Types

### What are Lifetimes?

A **lifetime** is the scope for which a reference is valid. Rust's type system makes lifetimes EXPLICIT when they can't be inferred automatically. This prevents **dangling references** (references to freed memory) at compile time.

```
THE DANGLING REFERENCE PROBLEM (prevented by lifetimes)
─────────────────────────────────────────────────────────
{
    let reference;             // reference declared
    {
        let data = String::from("hello");  // data created
        reference = &data;                  // reference points to data
    }   // ← data DROPPED HERE (freed)
    // reference now points to freed memory — DANGLING REFERENCE!
    println!("{}", reference); // UNDEFINED BEHAVIOR in C, COMPILE ERROR in Rust
}
─────────────────────────────────────────────────────────
```

```rust
// ── LIFETIME ANNOTATIONS ──────────────────────────────────────
// 'a is a lifetime parameter (named with a tick + letter)
// It means "the reference lives AT LEAST as long as lifetime 'a"

// Without lifetimes: the compiler can't determine which reference is returned
// fn longest(x: &str, y: &str) -> &str { ... } // ERROR: missing lifetime

// With lifetime annotation:
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    // 'a means: the return value lives as long as the SHORTER of x and y's lifetimes
    if x.len() > y.len() { x } else { y }
}

// ── LIFETIME ELISION ──────────────────────────────────────────
// In many cases, Rust infers lifetimes automatically (elision rules)
fn first_word(s: &str) -> &str { // no explicit 'a needed — elision applies
    // Rule: if there's ONE input reference, output gets the same lifetime
    let bytes = s.as_bytes();
    for (i, &byte) in bytes.iter().enumerate() {
        if byte == b' ' {
            return &s[..i];
        }
    }
    s
}

// ── STRUCT WITH LIFETIME ──────────────────────────────────────
// This struct holds a REFERENCE — it must not outlive the referenced data
struct Excerpt<'a> {
    part: &'a str, // 'a: this reference must live as long as the struct
}

impl<'a> Excerpt<'a> {
    fn display(&self) -> &str { // output lifetime = self's lifetime (elision)
        self.part
    }

    fn announce(&self, announcement: &str) -> &str {
        println!("Attention: {}", announcement);
        self.part // returns part of self — output gets self's lifetime
    }
}

// ── STATIC LIFETIME ───────────────────────────────────────────
// 'static = the reference is valid for the ENTIRE program duration
// String literals are always 'static (they live in the binary's read-only memory)
fn static_example() {
    let s: &'static str = "I live forever!"; // always valid
    println!("{}", s);
}

// ── LIFETIME + GENERICS + TRAITS TOGETHER ─────────────────────
// This signature says:
// - T must implement Display
// - x and y must both live at least as long as 'a
// - the return value lives as long as 'a
fn longest_with_announcement<'a, T>(x: &'a str, y: &'a str, ann: T) -> &'a str
where
    T: std::fmt::Display,
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() { x } else { y }
}

fn main() {
    // Dangling reference example — compiler catches this:
    // let r;
    // {
    //     let x = 5;
    //     r = &x; // COMPILE ERROR: `x` does not live long enough
    // }
    // println!("{}", r); // would be dangling

    // Correct usage of longest
    let string1 = String::from("long string is long");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(string1.as_str(), string2.as_str());
        println!("Longest: {}", result); // must use result inside string2's scope
    }
    // println!("{}", result); // COMPILE ERROR: string2 doesn't live long enough

    // Struct with lifetime
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence = novel.split('.').next().expect("Could not find a '.'");
    let excerpt = Excerpt { part: first_sentence };
    println!("Excerpt: {}", excerpt.display());

    // First word
    let sentence = String::from("hello world");
    let word = first_word(&sentence);
    println!("First word: {}", word);

    static_example();

    let result2 = longest_with_announcement("long", "short", "today is fun");
    println!("{}", result2);
}
```

```
LIFETIME VISUALIZATION
─────────────────────────────────────────────────────────
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str

Time  ←───────── lifetime 'a ─────────→
       ┌─────────────────────────────┐
       │ x lives here                │
       └─────────────────────────────┘
           ┌─────────────────┐
           │ y lives here    │
           └─────────────────┘
               ┌─────────────┐
               │ return must │ ← can only be valid where BOTH x and y are valid
               │ live here   │   so 'a = min(x's lifetime, y's lifetime)
               └─────────────┘
─────────────────────────────────────────────────────────
```

---

## 14. Type Coercion and Casting

### What is Coercion vs Casting?

- **Coercion**: IMPLICIT conversion done automatically by the compiler
- **Casting**: EXPLICIT conversion you write in code

```go
// ── GO: EXPLICIT CASTING (almost no implicit coercion) ────────
package main

import "fmt"

func main() {
    var i int = 42
    var f float64 = float64(i) // explicit cast required
    var u uint = uint(f)

    // String conversions
    s := string(65)          // "A" — rune/int to Unicode char
    b := []byte("hello")     // string to byte slice
    back := string(b)        // byte slice back to string

    // Numeric string conversion needs strconv package (not a cast)
    // s := string(42)  // gives "∗" NOT "42"!

    fmt.Println(i, f, u, s, back)

    // Constants have implicit type flexibility (untyped constants)
    const pi = 3.14159      // untyped constant
    var x float32 = pi      // works! pi is untyped
    var y float64 = pi      // also works!
    fmt.Println(x, y)
}
```

```rust
// ── RUST: as KEYWORD FOR PRIMITIVE CASTING ────────────────────
fn main() {
    // as casts between primitives
    let i: i32 = 42;
    let f: f64 = i as f64;
    let u: u32 = f as u32;    // truncates decimal part
    let b: u8 = 300_u32 as u8; // 300 - 256 = 44 (wraps, no panic)

    println!("{}, {}, {}, {}", i, f, u, b);

    // DEREF COERCIONS (implicit, automatic)
    // Rust DOES have some implicit coercions — but only safe ones

    // 1. &String → &str (Deref coercion)
    let s = String::from("hello");
    let s_ref: &str = &s; // automatic deref coercion!
    fn takes_str(s: &str) { println!("{}", s); }
    takes_str(&s); // &String is automatically coerced to &str

    // 2. &Vec<T> → &[T] (Deref coercion)
    let v: Vec<i32> = vec![1, 2, 3];
    fn takes_slice(s: &[i32]) { println!("{:?}", s); }
    takes_slice(&v); // &Vec<i32> is automatically coerced to &[i32]

    // 3. &Box<T> → &T
    let boxed = Box::new(42_i32);
    let val: &i32 = &boxed; // auto-deref

    // ── From / Into TRAITS — Idiomatic Conversions ────────────
    // From and Into are type-safe conversion traits

    let s = String::from("hello"); // From<&str> for String
    let num = i32::from(42_i8);    // From<i8> for i32

    // Into is the reverse of From (auto-generated)
    let s2: String = "world".into(); // into() calls From under the hood
    let num2: i64 = 42_i32.into();

    // TryFrom / TryInto — conversions that might fail
    let big: i32 = 1000;
    let small: Result<u8, _> = u8::try_from(big); // 1000 doesn't fit in u8
    println!("{:?}", small); // Err(...)

    let ok: Result<u8, _> = u8::try_from(42_i32);
    println!("{:?}", ok); // Ok(42)

    println!("{}, {}, {:?}", s_ref, num, val);
    let _ = (s, num, s2, num2);
}
```

```
TYPE CONVERSION DECISION TREE
─────────────────────────────────────────────────────────
Do you need a conversion?
         │
    ┌────┴────┐
    │         │
Primitive   Complex type
    │           │
  use `as`   Is it safe/guaranteed?
              │
         ┌────┴────┐
         YES       NO
         │         │
    From/Into   TryFrom/TryInto
    (infallible) (returns Result)
─────────────────────────────────────────────────────────
```

---

## 15. Pattern Matching

### What is Pattern Matching?

**Pattern matching** is a mechanism to check a value against a pattern and optionally extract data from it. Rust's `match` is significantly more powerful than Go's `switch`.

```go
// ── GO PATTERN MATCHING ───────────────────────────────────────
package main

import "fmt"

func main() {
    // Go switch — limited pattern matching
    x := 5

    switch {
    case x < 0:
        fmt.Println("negative")
    case x == 0:
        fmt.Println("zero")
    case x > 0:
        fmt.Println("positive")
    }

    // Type switch (powerful for interface dispatch)
    var i interface{} = "hello"
    switch v := i.(type) {
    case int:
        fmt.Println("int:", v)
    case string:
        fmt.Println("string:", v)
    case bool:
        fmt.Println("bool:", v)
    }

    // Multiple values per case
    day := "Monday"
    switch day {
    case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
        fmt.Println("Weekday")
    case "Saturday", "Sunday":
        fmt.Println("Weekend")
    }
}
```

```rust
fn main() {
    // ── MATCHING LITERALS ─────────────────────────────────────
    let x = 5;
    let msg = match x {
        1 => "one",
        2 | 3 => "two or three",   // OR pattern
        4..=6 => "four to six",    // range pattern (inclusive)
        _ => "something else",     // wildcard (must be exhaustive)
    };
    println!("{}", msg);

    // ── MATCHING TUPLES ───────────────────────────────────────
    let point = (0, -2);
    match point {
        (0, 0) => println!("origin"),
        (x, 0) | (0, x) => println!("on an axis at {}", x),
        (x, y) => println!("point ({}, {})", x, y),
    }

    // ── MATCHING ENUMS WITH DATA ──────────────────────────────
    #[derive(Debug)]
    enum Command {
        Quit,
        Move { x: i32, y: i32 },
        Write(String),
        ChangeColor(u8, u8, u8),
    }

    let cmds = vec![
        Command::Move { x: 10, y: 20 },
        Command::Write(String::from("hello")),
        Command::ChangeColor(255, 0, 0),
        Command::Quit,
    ];

    for cmd in cmds {
        match cmd {
            Command::Quit => println!("Quit"),
            Command::Move { x, y } => println!("Move to ({}, {})", x, y),
            Command::Write(text) => println!("Write: {}", text),
            Command::ChangeColor(r, g, b) => println!("Color ({},{},{})", r, g, b),
        }
    }

    // ── MATCH GUARDS ──────────────────────────────────────────
    let num = Some(4);
    match num {
        Some(n) if n < 0 => println!("negative: {}", n),
        Some(n) if n == 0 => println!("zero"),
        Some(n) => println!("positive: {}", n),
        None => println!("nothing"),
    }

    // ── BINDING WITH @ ────────────────────────────────────────
    let score = 85;
    match score {
        n @ 90..=100 => println!("Excellent: {}", n),
        n @ 70..=89  => println!("Good: {}", n),
        n @ 50..=69  => println!("Average: {}", n),
        n            => println!("Needs improvement: {}", n),
    }

    // ── DESTRUCTURING STRUCTS ────────────────────────────────
    struct Point { x: i32, y: i32 }
    let p = Point { x: 3, y: -7 };

    let Point { x, y } = p; // destructuring let
    println!("x={}, y={}", x, y);

    match p {
        Point { x: 0, y } => println!("On y-axis at {}", y),
        Point { x, y: 0 } => println!("On x-axis at {}", x),
        Point { x, y } => println!("At ({}, {})", x, y),
    }

    // ── NESTED PATTERNS ───────────────────────────────────────
    let nested = Some(Some(5_i32));
    match nested {
        Some(Some(n)) if n > 0 => println!("nested positive: {}", n),
        Some(Some(n)) => println!("nested non-positive: {}", n),
        Some(None) => println!("Some(None)"),
        None => println!("None"),
    }

    // ── IF LET (single pattern match) ────────────────────────
    let opt = Some(42);
    if let Some(n) = opt {
        println!("Got: {}", n);
    }

    // ── WHILE LET ────────────────────────────────────────────
    let mut stack = vec![1, 2, 3];
    while let Some(top) = stack.pop() {
        println!("Popped: {}", top);
    }

    // ── LET CHAINS (Rust 2024) ────────────────────────────────
    // if let Some(x) = foo && x > 5 { ... } // multiple patterns

    // ── MATCHES! MACRO ────────────────────────────────────────
    let val = Some(5);
    let is_positive = matches!(val, Some(n) if n > 0);
    println!("Is positive: {}", is_positive);
}
```

---

## 16. Zero-Cost Abstractions

### What are Zero-Cost Abstractions?

The principle: **"You don't pay for what you don't use. And what you do use, you couldn't write better by hand."** — Bjarne Stroustrup (C++), also core to Rust.

In Rust, high-level abstractions (iterators, closures, generics) compile to the SAME machine code as manually written low-level loops.

```rust
// ── ITERATOR ZERO-COST ABSTRACTION ───────────────────────────
fn demonstrate_zero_cost() {
    let v: Vec<i32> = (0..1_000_000).collect();

    // HIGH LEVEL — using iterator combinators
    let sum_high: i64 = v.iter()
        .filter(|&&x| x % 2 == 0)  // keep evens
        .map(|&x| x as i64 * x as i64) // square them
        .sum();

    // LOW LEVEL — manual loop
    let mut sum_low: i64 = 0;
    for &x in &v {
        if x % 2 == 0 {
            sum_low += (x as i64) * (x as i64);
        }
    }

    // Both compile to nearly identical machine code!
    // The compiler INLINES the iterator methods and eliminates all overhead
    assert_eq!(sum_high, sum_low);
    println!("Sum: {}", sum_high);
}

// ── MONOMORPHIZATION = ZERO-COST GENERICS ────────────────────
fn generic_max<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

// When you call generic_max(3_i32, 5_i32), the compiler generates:
// fn generic_max_i32(a: i32, b: i32) -> i32 { if a > b { a } else { b } }
// — EXACTLY as fast as a hand-written i32 function!

fn main() {
    demonstrate_zero_cost();
    println!("{}", generic_max(3_i32, 5_i32));
}
```

Go's interfaces, on the other hand, always use **dynamic dispatch** (runtime vtable lookup), which has a small but non-zero cost. Rust's generics avoid this entirely via monomorphization.

---

## 17. Advanced Trait System — Rust Deep Dive

```rust
use std::ops::{Add, Mul, Neg};
use std::fmt;

// ── OPERATOR OVERLOADING VIA TRAITS ───────────────────────────
#[derive(Debug, Clone, Copy, PartialEq)]
struct Vec2 {
    x: f64,
    y: f64,
}

impl Vec2 {
    fn new(x: f64, y: f64) -> Self { Vec2 { x, y } }
    fn magnitude(&self) -> f64 { (self.x * self.x + self.y * self.y).sqrt() }
    fn dot(&self, other: &Vec2) -> f64 { self.x * other.x + self.y * other.y }
}

impl Add for Vec2 {
    type Output = Vec2;
    fn add(self, rhs: Vec2) -> Vec2 {
        Vec2::new(self.x + rhs.x, self.y + rhs.y)
    }
}

impl Mul<f64> for Vec2 {
    type Output = Vec2;
    fn mul(self, scalar: f64) -> Vec2 {
        Vec2::new(self.x * scalar, self.y * scalar)
    }
}

impl Neg for Vec2 {
    type Output = Vec2;
    fn neg(self) -> Vec2 { Vec2::new(-self.x, -self.y) }
}

impl fmt::Display for Vec2 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.2}, {:.2})", self.x, self.y)
    }
}

// ── ITERATOR TRAIT IMPLEMENTATION ─────────────────────────────
struct Fibonacci {
    a: u64,
    b: u64,
}

impl Fibonacci {
    fn new() -> Self { Fibonacci { a: 0, b: 1 } }
}

impl Iterator for Fibonacci {
    type Item = u64;
    fn next(&mut self) -> Option<u64> {
        let result = self.a;
        let next = self.a + self.b;
        self.a = self.b;
        self.b = next;
        Some(result) // infinite iterator — always returns Some
    }
}

// ── BUILDER PATTERN USING TYPES ───────────────────────────────
// Type-state pattern: use TYPES to enforce correct builder usage
struct NoUrl;
struct HasUrl(String);
struct NoMethod;
struct HasMethod(String);

struct RequestBuilder<U, M> {
    url: U,
    method: M,
    headers: Vec<(String, String)>,
}

impl RequestBuilder<NoUrl, NoMethod> {
    fn new() -> Self {
        RequestBuilder { url: NoUrl, method: NoMethod, headers: vec![] }
    }
}

impl<M> RequestBuilder<NoUrl, M> {
    fn url(self, url: &str) -> RequestBuilder<HasUrl, M> {
        RequestBuilder {
            url: HasUrl(url.to_string()),
            method: self.method,
            headers: self.headers,
        }
    }
}

impl<U> RequestBuilder<U, NoMethod> {
    fn method(self, m: &str) -> RequestBuilder<U, HasMethod> {
        RequestBuilder {
            url: self.url,
            method: HasMethod(m.to_string()),
            headers: self.headers,
        }
    }
}

impl RequestBuilder<HasUrl, HasMethod> {
    fn header(mut self, key: &str, value: &str) -> Self {
        self.headers.push((key.to_string(), value.to_string()));
        self
    }

    // build() is ONLY available when BOTH url and method are set!
    fn build(self) -> String {
        format!("{} {}", self.method.0, self.url.0)
    }
}

fn main() {
    // Vector math
    let v1 = Vec2::new(1.0, 2.0);
    let v2 = Vec2::new(3.0, 4.0);
    println!("v1 + v2 = {}", v1 + v2);
    println!("v1 * 2 = {}", v1 * 2.0);
    println!("|v2| = {:.4}", v2.magnitude());
    println!("v1 · v2 = {}", v1.dot(&v2));

    // Fibonacci iterator — uses all iterator adaptors for free!
    let fibs: Vec<u64> = Fibonacci::new().take(10).collect();
    println!("Fibonacci: {:?}", fibs);

    let sum: u64 = Fibonacci::new()
        .take_while(|&n| n < 100)
        .filter(|n| n % 2 == 0)  // even Fibonacci
        .sum();
    println!("Even Fibonacci < 100, sum: {}", sum);

    // Type-state builder (compile error if you forget url or method)
    let request = RequestBuilder::new()
        .url("https://api.example.com/users")
        .method("GET")
        .header("Authorization", "Bearer token123")
        .build();
    println!("Request: {}", request);

    // This would NOT compile — missing url or method:
    // RequestBuilder::new().build(); // ERROR: method `build` not found
}
```

---

## 18. Comparison Table

```
COMPREHENSIVE GO vs RUST TYPE SYSTEM COMPARISON
═══════════════════════════════════════════════════════════════════════════
FEATURE                    GO                        RUST
───────────────────────── ─────────────────────── ─────────────────────────
TYPE SYSTEM STYLE          Static, Strong           Static, Strong
TYPING APPROACH            Nominal (structs)         Nominal (structs/traits)
                           Structural (interfaces)   Nominal (trait impl)
MEMORY MANAGEMENT          Garbage Collector         Ownership + Borrow Checker
NULL SAFETY                nil (unsafe)              Option<T> (safe)
ERROR HANDLING             (T, error) multi-return   Result<T,E> enum
ENUMS                      iota (simple constants)   ADT (with data per variant)
GENERICS                   Since 1.18                Since 1.0
TRAIT/INTERFACE DEFAULT    Not supported             Supported
STATIC DISPATCH            No (always vtable)        Yes (impl Trait / T: Trait)
DYNAMIC DISPATCH           Yes (interface)           Yes (dyn Trait)
LIFETIMES                  No (GC handles it)        Yes (compile-time)
OPERATOR OVERLOADING       No                        Yes (via traits)
PATTERN MATCHING           Limited (switch)           Exhaustive, rich (match)
ZERO-COST ABSTRACTIONS     Partial                   Full
CLOSURES                   Yes                       Yes (Fn, FnMut, FnOnce)
ALGEBRAIC DATA TYPES       No (use interfaces)       Yes (enum)
NEWTYPE PATTERN            Yes (type MyType int)     Yes (struct Wrapper(T))
TYPE INFERENCE             Local                     Global (Hindley-Milner)
CONST GENERICS             No                        Yes
ASSOCIATED TYPES           No                        Yes
BLANKET IMPLEMENTATIONS    No                        Yes
UNSAFE ESCAPE HATCH        No built-in unsafe        unsafe {} blocks
COMPILE TIME               Very fast                 Slower (more analysis)
LEARNING CURVE             Gentle                    Steep
═══════════════════════════════════════════════════════════════════════════
```

---

## 19. Real-World Design Patterns

### Pattern 1: State Machine (Rust's Type System Advantage)

```rust
// Encode valid state transitions IN THE TYPE SYSTEM
// Making invalid states unrepresentable

mod order_state_machine {
    use std::fmt;

    // Each state is its own type
    pub struct Pending { pub items: Vec<String>, pub user_id: u64 }
    pub struct Confirmed { pub items: Vec<String>, pub user_id: u64, pub order_id: u64 }
    pub struct Shipped { pub order_id: u64, pub tracking: String }
    pub struct Delivered { pub order_id: u64 }
    pub struct Cancelled { pub reason: String }

    // The Order is parameterized by state
    pub struct Order<State> {
        pub state: State,
    }

    impl Order<Pending> {
        pub fn new(user_id: u64, items: Vec<String>) -> Self {
            Order { state: Pending { items, user_id } }
        }

        // Only Pending orders can be confirmed
        pub fn confirm(self, order_id: u64) -> Order<Confirmed> {
            Order {
                state: Confirmed {
                    items: self.state.items,
                    user_id: self.state.user_id,
                    order_id,
                }
            }
        }

        pub fn cancel(self, reason: &str) -> Order<Cancelled> {
            Order { state: Cancelled { reason: reason.to_string() } }
        }
    }

    impl Order<Confirmed> {
        // Only Confirmed orders can be shipped
        pub fn ship(self, tracking: &str) -> Order<Shipped> {
            Order {
                state: Shipped {
                    order_id: self.state.order_id,
                    tracking: tracking.to_string(),
                }
            }
        }
    }

    impl Order<Shipped> {
        pub fn deliver(self) -> Order<Delivered> {
            Order { state: Delivered { order_id: self.state.order_id } }
        }
    }

    impl fmt::Display for Order<Delivered> {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "Order #{} delivered!", self.state.order_id)
        }
    }
}

use order_state_machine::*;

fn type_state_demo() {
    let order = Order::new(42, vec!["laptop".to_string(), "mouse".to_string()]);
    let confirmed = order.confirm(1001);
    let shipped = confirmed.ship("TRACK123456");
    let delivered = shipped.deliver();
    println!("{}", delivered);

    // This would be a COMPILE ERROR — cannot ship a Pending order:
    // let order2 = Order::new(43, vec![]);
    // order2.ship("TRACK"); // ERROR: method `ship` not found for Order<Pending>!
}

fn main() {
    type_state_demo();
}
```

### Pattern 2: Plugin System Comparison

```go
// ── GO PLUGIN SYSTEM ──────────────────────────────────────────
package main

import "fmt"

type Plugin interface {
    Name() string
    Execute(input string) string
}

type PluginRegistry struct {
    plugins map[string]Plugin
}

func NewRegistry() *PluginRegistry {
    return &PluginRegistry{plugins: make(map[string]Plugin)}
}

func (r *PluginRegistry) Register(p Plugin) {
    r.plugins[p.Name()] = p
}

func (r *PluginRegistry) Run(name, input string) (string, error) {
    p, ok := r.plugins[name]
    if !ok {
        return "", fmt.Errorf("plugin %q not found", name)
    }
    return p.Execute(input), nil
}

// Plugin implementations — implicit interface satisfaction
type UpperCasePlugin struct{}
func (p UpperCasePlugin) Name() string { return "uppercase" }
func (p UpperCasePlugin) Execute(s string) string {
    result := make([]byte, len(s))
    for i, c := range s {
        if c >= 'a' && c <= 'z' { result[i] = byte(c - 32) } else { result[i] = byte(c) }
    }
    return string(result)
}

type ReversePlugin struct{}
func (p ReversePlugin) Name() string { return "reverse" }
func (p ReversePlugin) Execute(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

func main() {
    registry := NewRegistry()
    registry.Register(UpperCasePlugin{})
    registry.Register(ReversePlugin{})

    if result, err := registry.Run("uppercase", "hello world"); err == nil {
        fmt.Println(result) // HELLO WORLD
    }
    if result, err := registry.Run("reverse", "hello"); err == nil {
        fmt.Println(result) // olleh
    }
}
```

---

## 20. Mental Models & Cognitive Strategies

### Mental Model 1: The Type as a Contract

Think of every type as a **contract** between:
- The **producer** (who creates values of that type)
- The **consumer** (who receives and uses those values)

The type system **enforces** that contract at compile time. In Rust, contracts are richer: `Option<T>` contracts say "I might not have a value," `Result<T,E>` says "I might fail in these specific ways."

### Mental Model 2: The Borrow Checker as a Loan Officer

Think of memory like money:
- **Ownership** = you own the money
- **Borrowing (&T)** = lending money; you can lend to multiple people to READ, but they can't spend it
- **Mutable Borrowing (&mut T)** = one exclusive loan; only ONE person can have it and they CAN spend it
- **Moving** = permanently transferring money to someone else

### Mental Model 3: Types as Sets

Every type is a **set of possible values**:
- `bool` = {true, false} — 2 elements
- `u8` = {0, 1, 2, ..., 255} — 256 elements
- `Option<bool>` = {None, Some(true), Some(false)} — 3 elements
- `Result<bool, String>` = {Ok(true), Ok(false), Err(any_string)} — infinite

Making invalid states unrepresentable = **shrink the set to only valid values**.

### Cognitive Strategy: Deliberate Practice Plan

```
30-DAY TYPE SYSTEM MASTERY PLAN
─────────────────────────────────────────────────────────
Week 1: Foundations
  Day 1-2:  Primitive types — implement a calculator in both Go and Rust
  Day 3-4:  Structs and methods — build a geometry library
  Day 5-7:  Interfaces/Traits — implement a plugin system

Week 2: Intermediate Patterns
  Day 8-9:  Enums and pattern matching — build a simple AST
  Day 10-11: Error handling — file parser with error propagation
  Day 12-14: Generics — implement generic collections (Stack, Queue, BST)

Week 3: Advanced Concepts
  Day 15-17: Option/Result chaining — HTTP client with error handling
  Day 18-20: Ownership and borrowing — implement a memory-efficient graph
  Day 21:   Lifetimes — build a string tokenizer with borrowing

Week 4: Mastery
  Day 22-24: Type-state patterns — implement a connection pool state machine
  Day 25-26: Trait objects vs generics — build a rendering engine
  Day 27-28: Newtype pattern — domain modeling for a banking system
  Day 29-30: Combine everything — build a mini HTTP server in both languages

Meta-learning principle: For each concept, do:
  1. Read (understand)      — 20%
  2. Implement (practice)   — 60%
  3. Teach/explain (recall) — 20%
─────────────────────────────────────────────────────────
```

### Psychological Principle: Chunking

Don't try to understand "the type system" as one monolith. **Chunk** it:
1. Primitives → a day's work
2. Structs/methods → two days
3. Traits/interfaces → a week
4. Generics → another week

Master each chunk before moving to the next. Your working memory can only hold ~7 items; chunking collapses complex concepts into single memorable units.

### The Expert Heuristic

When encountering a new type system question, ask:
1. **What set of values does this type represent?**
2. **What invalid states can this type accidentally represent?**
3. **How can I use the type system to make those invalid states unrepresentable?**

This is the move from "programmer who uses types" to "programmer who **designs with** types."

---

*"The best code is the code that the type system makes impossible to write incorrectly."*

Here's your complete, deeply structured guide. Let me walk you through the architecture of what's inside:

---

**What This Guide Covers (20 chapters, full implementations)**

**Fundamentals first:** The guide opens by defining what a type system *actually is* — a formal contract enforcer — and builds the full vocabulary (nominal vs structural, static vs dynamic, ADT, coercion, etc.) before using those terms anywhere.

**The core philosophical divide:**
- Go: *simplicity is sophistication* — deliberately limited, GC-backed, structural interfaces
- Rust: *safety without sacrifice* — rich expressive types, zero-cost, ownership-based

**The big conceptual pillars covered:**

| Topic | Key Insight |
|---|---|
| Primitives | Rust has `char`, `i128`, `!` (never type), `()` (unit) — Go doesn't |
| Type Inference | Rust uses Hindley-Milner (infers *backwards* from usage); Go is local-only |
| Enums | Go's `iota` is just integers; Rust's enums are *algebraic data types* — each variant carries different data |
| Null Safety | Go's `nil` can silently panic; Rust's `Option<T>` forces you to handle absence *in the type* |
| Error Handling | Go's `(T, error)` requires manual `if err != nil`; Rust's `Result<T,E>` + `?` operator is chainable and exhaustive |
| Ownership | Rust encodes memory management rules *into the type system itself* — no GC needed |
| Lifetimes | References carry compile-time proof of how long they live |
| Zero-cost abstractions | Rust iterators compile to identical machine code as hand-written loops |

**Advanced patterns included:**
- Type-state pattern (making invalid state transitions *unrepresentable at compile time*)
- Newtype pattern (unit-safe wrappers: `Meters` vs `Kilometers`)
- Builder pattern enforced by types
- Plugin system in both languages

**Mental models and 30-day mastery plan** at the end — structured around chunking and deliberate practice.

The core philosophy to internalize: **types are sets of possible values. Your job as a systems programmer is to shrink those sets until only valid states are representable.** Rust gives you far more tools to do that; Go trades that expressiveness for simplicity and fast compilation.