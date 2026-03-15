# Rust Operators Are Trait-Based

Before we dive in, let's build up from absolute zero.

---

## What Is a Trait?

A **trait** in Rust is a contract — a named set of behaviors (methods) that a type can promise to implement. Think of it like an interface in other languages, but more powerful.

```rust
trait Greet {
    fn hello(&self) -> String;
}
```

Any type that *implements* this trait must define `hello()`. That's the contract.

---

## What Does "Operators Are Trait-Based" Mean?

In most languages, `+`, `-`, `==`, `<`, etc. are baked into the compiler — hardcoded for numbers. In Rust, **every operator is syntactic sugar for a trait method call**. When you write `a + b`, the compiler silently rewrites it as `a.add(b)` where `add` comes from the `Add` trait.

This means: **you can make any operator work on any type** — as long as you implement the corresponding trait.

```
a + b    ──→   std::ops::Add::add(a, b)
a == b   ──→   std::cmp::PartialEq::eq(&a, &b)
a < b    ──→   std::cmp::PartialOrd::lt(&a, &b)
-a       ──→   std::ops::Neg::neg(a)
a[i]     ──→   std::ops::Index::index(&a, i)
```

This is the architecture:---

## The Full Trait Signatures

Let's read the actual standard library definitions. These are important to understand before using them:

```rust
// std::ops::Add — the + operator
pub trait Add<Rhs = Self> {
    type Output;                    // ← what type does a+b produce?
    fn add(self, rhs: Rhs) -> Self::Output;
}

// std::ops::Neg — the unary - operator (negation)
pub trait Neg {
    type Output;
    fn neg(self) -> Self::Output;
}

// std::cmp::PartialEq — the == and != operators
pub trait PartialEq<Rhs = Self> {
    fn eq(&self, other: &Rhs) -> bool;
    fn ne(&self, other: &Rhs) -> bool { !self.eq(other) } // default impl
}

// std::cmp::PartialOrd — the <, >, <=, >= operators
pub trait PartialOrd<Rhs = Self>: PartialEq<Rhs> {
    fn partial_cmp(&self, other: &Rhs) -> Option<Ordering>;
    // lt, gt, le, ge all have default impls calling partial_cmp
}
```

> **Key concepts to notice:**
> - `Rhs = Self` means "by default, the right-hand side is the same type as Self" — but you can make `Point + f64` work by setting `Rhs = f64`.
> - `type Output` is an *associated type* — the return type of the operation. Adding two `Meters` could produce `Meters`. Adding two `Vec<T>` produces `Vec<T>`.
> - `PartialOrd` *requires* `PartialEq` — you see `: PartialEq<Rhs>` as a supertrait constraint.

---

## Your First Implementation — Step by Step

Let's implement arithmetic for a `Point` struct, thinking like an expert:

**Expert reasoning before writing code:**
1. What is my type? A 2D point `(x, y)`.
2. What should `+` mean? Vector addition: `(x1+x2, y1+y2)`.
3. What should `==` mean? Both coordinates match.
4. What should `-` (unary) mean? Negate both components.
5. Can I avoid boilerplate? Yes — use `#[derive]` for `PartialEq`/`Eq`.

```rust
use std::ops::{Add, Sub, Mul, Neg};
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq)]  // derive handles ==
struct Point {
    x: f64,
    y: f64,
}

// Implement the + operator
impl Add for Point {
    type Output = Point;  // Point + Point = Point

    fn add(self, rhs: Point) -> Point {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
        }
    }
}

// Implement the - operator (binary subtraction)
impl Sub for Point {
    type Output = Point;

    fn sub(self, rhs: Point) -> Point {
        Point {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
        }
    }
}

// Implement scalar multiplication: Point * f64
impl Mul<f64> for Point {        // ← Rhs is f64, NOT Self
    type Output = Point;

    fn mul(self, scalar: f64) -> Point {
        Point {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

// Implement unary negation: -point
impl Neg for Point {
    type Output = Point;

    fn neg(self) -> Point {
        Point { x: -self.x, y: -self.y }
    }
}

fn main() {
    let a = Point { x: 1.0, y: 2.0 };
    let b = Point { x: 3.0, y: 4.0 };

    println!("{:?}", a + b);    // Point { x: 4.0, y: 6.0 }
    println!("{:?}", a - b);    // Point { x: -2.0, y: -2.0 }
    println!("{:?}", a * 3.0);  // Point { x: 3.0, y: 6.0 }
    println!("{:?}", -a);       // Point { x: -1.0, y: -2.0 }
    println!("{}", a == a);     // true  (from #[derive(PartialEq)])
}
```

---

## The `Rhs` Generic Parameter — Cross-Type Operators

This is where it gets powerful and subtle. Consider: what if you want `Point * 3.0` AND `3.0 * Point` both to work? They require **two separate impls**:

```rust
// Point * f64  (already done above)
impl Mul<f64> for Point { ... }

// f64 * Point  — you must implement Mul<Point> FOR f64
// BUT: you cannot impl foreign traits on foreign types (the "orphan rule")
// SOLUTION: implement Mul<Point> for a NEWTYPE wrapper around f64
```

This reveals Rust's **orphan rule**: you can only implement a trait for a type if either the *trait* or the *type* is defined in your crate. You cannot implement `std::ops::Mul` for `f64` because both are foreign to you.

The standard workaround:

```rust
// Instead, implement in the other direction by making YOUR type handle both
impl Mul<f64> for Point {
    type Output = Point;
    fn mul(self, s: f64) -> Point { Point { x: self.x * s, y: self.y * s } }
}

// For 3.0 * p syntax, you need a newtype or you do it differently
// Most libraries just document: "scalar must go on the right"
```

---

## PartialEq vs Eq — A Critical Distinction

These look similar but encode different mathematical properties:

```
PartialEq → defines ==, but NOT reflexive for all values
            WHY? f64::NAN != f64::NAN   (NaN is not equal to itself)
            So f64 only implements PartialEq, NOT Eq

Eq        → supertrait of PartialEq; promises FULL reflexivity
            a == a is ALWAYS true for all values
            integers, strings, booleans implement Eq
```

```rust
// Compiler will REFUSE this:
fn find<T: PartialEq>(slice: &[T], target: &T) -> Option<usize> {
    slice.iter().position(|x| x == target)
}

// If you need to use T as a HashMap key, you need Eq + Hash:
use std::collections::HashMap;
fn count<T: Eq + std::hash::Hash>(items: &[T]) -> HashMap<&T, usize> {
    let mut map = HashMap::new();
    for item in items { *map.entry(item).or_insert(0) += 1; }
    map
}
```

Similarly, `PartialOrd` vs `Ord`:

```
PartialOrd → partial_cmp returns Option<Ordering>
             (could be None if comparison is undefined, e.g. NaN)

Ord        → total ordering; cmp always returns Ordering (never None)
             Required for: BTreeMap keys, sort(), binary search
```

---

## The Operator-Trait Map (Complete Reference)

```
ARITHMETIC (std::ops)
┌─────────────┬─────────────────┬───────────────────────────┐
│  Syntax     │  Trait          │  Required method          │
├─────────────┼─────────────────┼───────────────────────────┤
│  a + b      │  Add<Rhs>       │  fn add(self, rhs) → Out  │
│  a - b      │  Sub<Rhs>       │  fn sub(self, rhs) → Out  │
│  a * b      │  Mul<Rhs>       │  fn mul(self, rhs) → Out  │
│  a / b      │  Div<Rhs>       │  fn div(self, rhs) → Out  │
│  a % b      │  Rem<Rhs>       │  fn rem(self, rhs) → Out  │
│  -a         │  Neg            │  fn neg(self) → Out       │
│  a += b     │  AddAssign<Rhs> │  fn add_assign(&mut self) │
│  a &  b     │  BitAnd<Rhs>    │  fn bitand(self, rhs)     │
│  a |  b     │  BitOr<Rhs>     │  fn bitor(self, rhs)      │
│  a ^  b     │  BitXor<Rhs>    │  fn bitxor(self, rhs)     │
│  a << b     │  Shl<Rhs>       │  fn shl(self, rhs)        │
│  a >> b     │  Shr<Rhs>       │  fn shr(self, rhs)        │
│  !a         │  Not            │  fn not(self) → Out       │
└─────────────┴─────────────────┴───────────────────────────┘

COMPARISON (std::cmp)
┌─────────────┬─────────────────┬───────────────────────────┐
│  a == b     │  PartialEq      │  fn eq(&self, &Rhs) → bool│
│  a != b     │  PartialEq      │  fn ne (default impl)     │
│  a <  b     │  PartialOrd     │  fn partial_cmp(...)      │
│  a >  b     │  PartialOrd     │  (default via partial_cmp)│
│  total ord  │  Ord            │  fn cmp(&self, &Self)     │
└─────────────┴─────────────────┴───────────────────────────┘

INDEXING (std::ops)
┌─────────────┬─────────────────┬───────────────────────────┐
│  a[i]       │  Index<Idx>     │  fn index(&self, i) → &Out│
│  a[i] = x   │  IndexMut<Idx>  │  fn index_mut(&mut self)  │
└─────────────┴─────────────────┴───────────────────────────┘

DEREFERENCING (std::ops)
┌─────────────┬─────────────────┬───────────────────────────┐
│  *a         │  Deref          │  fn deref(&self) → &Out   │
│  *a = x     │  DerefMut       │  fn deref_mut(&mut self)  │
└─────────────┴─────────────────┴───────────────────────────┘
```

---

## A Real-World Example: Dimensional Analysis

This is where trait-based operators truly shine — you can encode **type safety** into arithmetic:

```rust
use std::ops::{Add, Mul};

#[derive(Debug, Clone, Copy)] struct Meters(f64);
#[derive(Debug, Clone, Copy)] struct Seconds(f64);
#[derive(Debug, Clone, Copy)] struct MetersPerSec(f64);
#[derive(Debug, Clone, Copy)] struct SquareMeters(f64);

impl Add for Meters {
    type Output = Meters;
    fn add(self, rhs: Meters) -> Meters { Meters(self.0 + rhs.0) }
}

// distance / time = velocity
impl std::ops::Div<Seconds> for Meters {
    type Output = MetersPerSec;
    fn div(self, t: Seconds) -> MetersPerSec { MetersPerSec(self.0 / t.0) }
}

// meters * meters = square meters
impl Mul for Meters {
    type Output = SquareMeters;
    fn mul(self, rhs: Meters) -> SquareMeters { SquareMeters(self.0 * rhs.0) }
}

fn main() {
    let d = Meters(100.0);
    let t = Seconds(9.58);
    let v = d / t;                       // MetersPerSec — correct type!
    println!("{:.2} m/s", v.0);          // 10.44 m/s

    // This would FAIL to compile — you cannot add Meters + Seconds:
    // let wrong = Meters(1.0) + Seconds(1.0);  // ERROR ✗
}
```

The compiler becomes your physics teacher. Wrong units = compile error. **Zero runtime cost.**

---

## The `derive` Macro — When to Use vs When to Implement Manually

```
USE #[derive] WHEN:                   IMPLEMENT MANUALLY WHEN:
──────────────────────────────────    ──────────────────────────────────
All fields already impl the trait     Custom comparison logic needed
Default field-by-field behavior fits  Some fields should be excluded
You want quick boilerplate            Performance optimization needed
Prototyping                           Domain-specific semantics (NaN, ∞)

#[derive(PartialEq, Eq,               impl PartialEq for FloatPoint {
         PartialOrd, Ord,               fn eq(&self, other: &Self) -> bool {
         Clone, Copy,                     (self.x - other.x).abs() < 1e-9
         Debug, Hash)]                    && (self.y - other.y).abs() < 1e-9
struct Point { x: i32, y: i32 }        }
                                      }
```

---

## Deep Insight: Zero-Cost Abstraction

A critical mental model: **trait-based operators in Rust have zero runtime overhead**. The compiler *monomorphizes* them — it generates specialized machine code for each concrete type at compile time. There is no virtual dispatch, no function pointer, no indirection.

```
Python:   a + b  →  type(a).__add__(a, b)  [runtime lookup, boxing]
Java:     a + b  →  compiled for each primitive separately [special-cased]
Rust:     a + b  →  Point::add(a, b)       [inlined at compile time]
                    ≡ machine code: ADDSD xmm0, xmm1 (literally one instruction)
```

This is why Rust can have the ergonomics of high-level operator overloading with **C-level performance**.

---

## Mental Model to Carry Forward

Think of Rust's type system as a **capability system**: a type only has the capabilities you explicitly grant it through trait implementations. The `+` operator is not magic — it's just a named function. When you see `a + b`, always mentally expand it to its trait call. This mental expansion will make generic programming, trait bounds, and compiler errors instantly readable.

> **Deliberate Practice Prompt:** Implement a `Matrix2x2` type with `Add`, `Mul` (matrix × matrix), and `Mul<f64>` (scalar multiplication). Then add `PartialEq` with an epsilon tolerance for floating point. This single exercise covers: associated types, cross-type `Rhs`, and the `PartialEq` vs `Eq` distinction simultaneously.