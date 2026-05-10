# Rust Advanced Interview Questions & Answers
## A Complete, Production-Grade Reference for Senior Engineers

---

> **Scope**: This guide covers every advanced Rust concept you need to reason about
> the language at the compiler/runtime level — ownership, lifetimes, type theory,
> unsafe, concurrency, async internals, macros, FFI, allocators, and more.
> Every section includes in-depth explanations, ASCII architecture diagrams,
> and production Rust implementations.

---

## Table of Contents

1. [Ownership Model & Memory Layout](#1-ownership-model--memory-layout)
2. [Borrowing, References & Aliasing XOR Mutability](#2-borrowing-references--aliasing-xor-mutability)
3. [Lifetimes — Advanced](#3-lifetimes--advanced)
4. [Type System — Traits, Generics, Associated Types, GATs](#4-type-system--traits-generics-associated-types-gats)
5. [Variance, Covariance, Contravariance](#5-variance-covariance-contravariance)
6. [Smart Pointers & Interior Mutability](#6-smart-pointers--interior-mutability)
7. [Unsafe Rust — The Full Picture](#7-unsafe-rust--the-full-picture)
8. [Concurrency — Send, Sync, Atomics, Mutexes](#8-concurrency--send-sync-atomics-mutexes)
9. [Async/Await — Internals, Executors, Wakers, Pin](#9-asyncawait--internals-executors-wakers-pin)
10. [Closures, Iterators & Zero-Cost Abstractions](#10-closures-iterators--zero-cost-abstractions)
11. [Macros — Declarative and Procedural](#11-macros--declarative-and-procedural)
12. [Error Handling Patterns](#12-error-handling-patterns)
13. [Memory Allocators & Custom Allocation](#13-memory-allocators--custom-allocation)
14. [FFI — Foreign Function Interface](#14-ffi--foreign-function-interface)
15. [Compiler Internals — MIR, Borrow Checker, Monomorphization](#15-compiler-internals--mir-borrow-checker-monomorphization)
16. [Performance, SIMD & Low-Level Optimization](#16-performance-simd--low-level-optimization)
17. [no_std & Embedded/Kernel Environments](#17-no_std--embeddedkernel-environments)
18. [Type-Level Programming & Phantom Types](#18-type-level-programming--phantom-types)
19. [Pin, Unpin & Self-Referential Structs](#19-pin-unpin--self-referential-structs)
20. [Testing, Fuzzing & Benchmarking](#20-testing-fuzzing--benchmarking)

---

## 1. Ownership Model & Memory Layout

### Q1.1 — Explain Rust's ownership model from first principles. What problem does it solve and how does the compiler enforce it?

**Answer:**

Rust's ownership model is a **static, affine type system** layered over a region-based memory discipline. It solves the fundamental tradeoff between safety and performance that plagues systems languages:

- **C/C++**: manual memory — fast, but use-after-free, double-free, dangling pointers
- **GC languages**: safe, but non-deterministic pause times, high heap pressure
- **Rust**: compile-time proof of memory safety with zero runtime cost

**The Three Rules (invariants the compiler enforces):**

```
1. Every value has exactly one owner (variable binding).
2. When the owner goes out of scope, the value is dropped (RAII).
3. There can be EITHER many immutable references OR exactly one mutable
   reference to a value at any given time — never both simultaneously.
```

**Why these rules work together:**

Rule 1 ensures deterministic deallocation — no GC needed, no manual free.
Rule 2 ties resource lifetime to lexical scope (RAII pattern).
Rule 3 eliminates the aliasing + mutability combination that causes data races and iterator invalidation.

```
OWNERSHIP TRANSFER (MOVE SEMANTICS)
====================================

  Stack Frame A          Stack Frame B
  ┌─────────────┐        ┌─────────────┐
  │ s1: String  │        │             │
  │  ptr ───────┼──┐     │             │
  │  len: 5     │  │     │             │
  │  cap: 8     │  │     │             │
  └─────────────┘  │     └─────────────┘
                   │
  let s2 = s1;     │  s1 is MOVED, compiler marks it
                   │  as "moved out", any use of s1
  Stack Frame A    │  is a compile error.
  ┌─────────────┐  │     Stack Frame B
  │ s1: MOVED   │  │     ┌─────────────┐
  │ (invalid)   │  │     │ s2: String  │
  └─────────────┘  │     │  ptr ───────┼──┘
                         │  len: 5     │
                         │  cap: 8     │
                         └─────────────┘
                               │
                         Heap: ┌─┬─┬─┬─┬─┐
                               │h│e│l│l│o│
                               └─┴─┴─┴─┴─┘

  When s2 goes out of scope: drop() is called → heap freed.
  No double-free because s1 was never a valid owner after move.
```

**Stack vs Heap — what gets moved vs copied:**

Types implementing `Copy` (all scalar types: `i32`, `bool`, `f64`, tuples of Copy types, arrays of Copy types) are **bitwise-copied** on assignment. The original remains valid because there is no heap resource to transfer.

Types NOT implementing `Copy` (String, Vec<T>, Box<T>, any heap-owning type) are **moved** — the stack representation is bitwise copied to the new location but the old binding is invalidated at compile time.

```rust
// COPY — both a and b are valid
let a: i32 = 42;
let b = a;          // bitwise copy of 4 bytes on stack
println!("{a} {b}"); // OK

// MOVE — only s2 is valid
let s1 = String::from("hello");
let s2 = s1;         // stack repr bitwise-copied, s1 invalidated
// println!("{s1}"); // COMPILE ERROR: value borrowed after move
println!("{s2}");    // OK
```

**Drop order:**

Variables are dropped in **reverse declaration order** within a scope. Fields of a struct are dropped in **declaration order**. This is deterministic and critical for RAII guards (mutex locks, file handles, etc.).

```rust
{
    let a = Resource::new("a"); // dropped 3rd
    let b = Resource::new("b"); // dropped 2nd
    let c = Resource::new("c"); // dropped 1st
} // c, b, a — reverse order
```

---

### Q1.2 — Describe the precise memory layout of common Rust types: `String`, `Vec<T>`, `Box<T>`, `Rc<T>`, `Arc<T>`.

**Answer:**

Understanding the exact byte layout is critical for FFI, unsafe code, and performance reasoning.

```
STRING LAYOUT (3 words on stack, 64-bit system)
================================================

Stack:
┌──────────────────────────────────┐
│ ptr: *mut u8  (8 bytes)          │──────────────────────┐
│ len: usize    (8 bytes)          │                      │
│ cap: usize    (8 bytes)          │                      │
└──────────────────────────────────┘                      │
Total stack size: 24 bytes                                │
                                                          ▼
Heap (allocated by GlobalAlloc):                    ┌─────────────┐
                                                    │ UTF-8 bytes │
                                                    │ (cap bytes  │
                                                    │  allocated) │
                                                    └─────────────┘

Vec<T> LAYOUT — identical structure to String
==============================================

Stack:
┌──────────────────────────────────┐
│ ptr: *mut T   (8 bytes)          │──► Heap: [T, T, T, ..., (uninit)]
│ len: usize    (8 bytes)          │    ↑len elements initialized
│ cap: usize    (8 bytes)          │    ↑cap elements allocated
└──────────────────────────────────┘

Box<T> LAYOUT — single heap pointer
=====================================

Stack:
┌─────────────┐
│ ptr: *mut T │──► Heap: T (exactly sizeof(T) bytes)
└─────────────┘
Stack size: 8 bytes (one pointer)

Box<T> is guaranteed non-null. The compiler can apply null-pointer
optimization: Option<Box<T>> is the same size as Box<T> (8 bytes).

Rc<T> LAYOUT — reference-counted, SINGLE THREAD
=================================================

Stack:
┌─────────────────────┐
│ ptr: NonNull<Inner> │──────────────────────────────────┐
└─────────────────────┘                                  │
Stack size: 8 bytes                                      ▼
                                              ┌─────────────────────┐
                                              │ strong_count: Cell  │ (usize)
                                              │ weak_count:   Cell  │ (usize)
                                              │ value: T            │
                                              └─────────────────────┘
                                              Cell<usize> = no atomic ops
                                              NOT Send, NOT Sync

Arc<T> LAYOUT — atomically reference-counted, MULTI THREAD
============================================================

Stack:
┌─────────────────────┐
│ ptr: NonNull<Inner> │──────────────────────────────────┐
└─────────────────────┘                                  │
                                                         ▼
                                              ┌─────────────────────────┐
                                              │ strong_count: AtomicUsize│
                                              │ weak_count:   AtomicUsize│
                                              │ value: T                 │
                                              └─────────────────────────┘
                                              Atomic ops = memory fence cost
                                              IS Send+Sync if T: Send+Sync
```

**Thin vs Fat Pointers:**

```
THIN POINTER: &T where T is Sized
Stack: [ptr: *const T] — 8 bytes

FAT POINTER: &dyn Trait or &[T]
Stack: [ptr: *const T | *const VTable] — 16 bytes
       data pointer     vtable pointer

SLICE FAT POINTER: &[T]
Stack: [ptr: *const T | len: usize] — 16 bytes

&str is literally &[u8] with UTF-8 guarantee:
Stack: [ptr: *const u8 | len: usize] — 16 bytes
```

**Null pointer optimization (NPO):**

Types with a niche (a bit pattern that can never legally occur) allow `Option<T>` to be the same size as `T`:

```rust
assert_eq!(size_of::<Option<Box<i32>>>(), size_of::<Box<i32>>()); // 8 == 8
assert_eq!(size_of::<Option<&i32>>(),     size_of::<&i32>());     // 8 == 8
assert_eq!(size_of::<Option<NonZeroU32>>(), size_of::<u32>());    // 4 == 4
// None is represented as the null/zero bit pattern
```

---

### Q1.3 — What is the Drop Check and how does the compiler reason about when it's safe to drop a value that holds references?

**Answer:**

**Drop check** (`dropck`) is the compiler's analysis ensuring that when a value's `Drop::drop` implementation runs, all the data it might access through references is still alive.

The problem: if a struct holds a reference and implements `Drop`, the drop impl could access the referenced data. The referenced data must therefore outlive the struct by at least one scope level — not just match its lifetime.

```rust
// PROBLEM WITHOUT DROPCK
struct Inspector<'a> {
    name: &'a str,
}

impl<'a> Drop for Inspector<'a> {
    fn drop(&mut self) {
        // This runs AFTER the scope closes.
        // Is `self.name` still valid here?
        println!("Inspecting: {}", self.name); // could be dangling!
    }
}

fn main() {
    let name = String::from("hello");
    let _i = Inspector { name: &name };
    // name dropped first? Or inspector? Order matters!
}
```

**How the compiler handles it:**

The compiler enforces that any type implementing `Drop` must have its type parameters and lifetime parameters **strictly outlive** the type itself. This is **drop check** — parameterized lifetime `'a` in a `Drop` impl must satisfy `'a: 'b` where `'b` is the scope of the value being dropped.

**`#[may_dangle]` — opt out of strict dropck:**

If your `Drop` impl provably does NOT access the referenced data (e.g., a custom allocator that just frees bytes), you can tell the compiler:

```rust
// UNSAFE: you promise drop() does not access T's data
unsafe impl<#[may_dangle] T> Drop for MyVec<T> {
    fn drop(&mut self) {
        // We only free the allocation, never read T values
        // (well, we do call T's drop, but that's handled separately)
        unsafe { dealloc(self.ptr, self.layout) }
    }
}
```

`Vec<T>` in std uses this pattern — it drops each element first (which the compiler tracks separately), then frees the buffer.

**`PhantomData` and dropck:**

If you hold a raw pointer to `T` but want dropck to treat it as owning `T`:

```rust
use std::marker::PhantomData;

struct Owns<T> {
    ptr: *mut T,
    _own: PhantomData<T>,  // tells compiler: we own T, apply dropck rules
}
```

Without `PhantomData<T>`, the compiler doesn't know you access `T` in drop. With it, it knows to enforce that `T` must outlive `Owns<T>`.

---

## 2. Borrowing, References & Aliasing XOR Mutability

### Q2.1 — Explain the "Aliasing XOR Mutability" invariant. Why is it the core correctness guarantee?

**Answer:**

The **AXM** (Aliasing XOR Mutability) invariant states:

```
At any point in time, for any memory location L:
  EITHER: any number of read-only (shared) references &T exist → no writes allowed
  OR:     exactly one mutable reference &mut T exists → exclusive access
  NEVER:  both simultaneously
```

This is the most fundamental safety invariant in Rust. It's not just about data races — it eliminates entire classes of bugs:

**Why aliased mutation is dangerous (even single-threaded):**

```rust
// Iterator invalidation — classic C++ bug, impossible in safe Rust
let mut v = vec![1, 2, 3];
for x in &v {          // shared reference to v
    v.push(*x);        // COMPILE ERROR: cannot borrow `v` as mutable
                       // because it is also borrowed as immutable
    // In C++: this is UB — push may reallocate, invalidating the iterator
}
```

```rust
// Use-after-free via aliased mut — impossible in safe Rust
let mut s = String::from("hello");
let r1 = &s;           // shared ref
let r2 = &mut s;       // COMPILE ERROR: cannot borrow as mutable
                       // while immutable borrow exists
// In C++: dropping s while r1 alive = dangling pointer
```

**The borrow checker enforces AXM as a flow-sensitive analysis:**

```
LIFETIME SCOPES (Non-Lexical Lifetimes, NLL):
=============================================

let mut data = vec![1, 2, 3];

let r1 = &data;        ──────────────────────────────────┐ 'r1 starts
let r2 = &data;        ────────────────────────────┐ 'r2 │
println!("{r1} {r2}"); ← both reads here            │     │
                                                    ┘ 'r2 ends
                                                          │
let r3 = &mut data;    ──────────────────────────┐ 'r3   │
                                                 │       ┘ 'r1 ends
                                                 │  ← r3 can exist because
r3.push(4);                                      │    r1 and r2 are dead
                                                 ┘ 'r3 ends

// NLL = lifetimes end at last use, not at end of block
// This allows: r1, r2 exist; then both end; then r3 exists
// Old lexical borrows would reject this pattern
```

**Two-phase borrows (2PB):**

A subtlety for method calls:

```rust
let mut v = vec![1, 2, 3];
// v.push(v.len()) — does this work?
// Desugared: Vec::push(&mut v, Vec::len(&v))
// Two-phase: &mut v is a "reservation" until push body runs
// &v for len() is allowed during the reservation phase
v.push(v.len()); // OK in Rust 2018+ due to 2PB
```

---

### Q2.2 — How does the borrow checker handle re-borrows? What is the difference between moving a &mut T and re-borrowing it?

**Answer:**

**Re-borrow:** Creating a shorter-lived `&mut` from an existing `&mut`. The original `&mut` is temporarily frozen (not moved).

```rust
fn takes_mut(x: &mut i32) {
    *x += 1;
}

let mut val = 0;
let r = &mut val;

// Re-borrow: r is temporarily "reborrowed" for the duration of takes_mut
takes_mut(r);   // equivalent to: takes_mut(&mut *r)
// r is usable again here — it was reborrowed, not moved
*r = 42;
println!("{r}"); // OK
```

**Move of &mut T:** Transfers the exclusive access. Original binding is gone.

```rust
fn consume_mut(x: &mut i32) -> &mut i32 { x }

let mut val = 0;
let r1 = &mut val;
let r2 = consume_mut(r1);  // r1 MOVED into consume_mut, returned as r2
// r1 is no longer valid
*r2 = 99;
```

**The critical rule for re-borrows:**

A re-borrow `&mut *r` (where `r: &mut T`) is valid when:
1. The re-borrow's lifetime is strictly contained within `r`'s lifetime.
2. During the re-borrow's lifetime, `r` itself cannot be used (it's frozen).

```
REBORROW TIMELINE:
==================

  r: &'a mut T  ───────────────────────────────────────────────────►
                │                                    │
                │                                    │
  reborrow      ├──── &'b mut T (shorter) ──────────┤
  active        │ r is FROZEN during 'b              │
                │                                    │
  r usable    ◄─┘                                    └──► r usable again
```

This is how `DerefMut` works internally — calling `deref_mut()` on `Box<T>` creates a re-borrow of the contents for the duration of the operation.

---

## 3. Lifetimes — Advanced

### Q3.1 — Explain lifetime elision rules. When does the compiler infer lifetimes and when must you annotate?

**Answer:**

Lifetime elision is syntactic sugar — the compiler fills in lifetime parameters according to deterministic rules. Understanding when to annotate requires knowing these rules precisely.

**The three elision rules (for functions):**

```
Rule 1: Each elided lifetime in input position gets a distinct lifetime.
Rule 2: If there is exactly one input lifetime position, that lifetime
        is assigned to all elided output lifetimes.
Rule 3: If there are multiple input lifetime positions but one is &self
        or &mut self, the lifetime of self is assigned to all elided
        output lifetimes.
```

**Examples:**

```rust
// Elided → explicit translation:

fn first(s: &str) -> &str
// becomes:
fn first<'a>(s: &'a str) -> &'a str  // Rule 2: one input → output

fn longest(s: &str, t: &str) -> &str  // COMPILE ERROR
// becomes:
fn longest<'a, 'b>(s: &'a str, t: &'b str) -> &??? str
// Cannot elide: two inputs, no self, ambiguous → must annotate

fn longest<'a>(s: &'a str, t: &'a str) -> &'a str  // explicit: output lives as long as shorter of s,t

impl MyStruct {
    fn get_ref(&self) -> &str  // Rule 3: self lifetime → output
    // becomes:
    fn get_ref<'a>(&'a self) -> &'a str
}
```

**Higher-Ranked Trait Bounds (HRTB):**

When a function must work for ALL lifetimes (not a specific one):

```rust
// "This function takes a closure that works for ANY lifetime 'a"
fn apply<F>(f: F, s: &str) -> &str
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    f(s)
}

// `for<'a>` is the universal quantifier — reads as "for all lifetimes 'a"
// This cannot be expressed with a simple named lifetime in the bound
```

HRTB is required for trait objects and closures that must be valid for arbitrary lifetimes:

```rust
// Common in async code and trait objects:
trait Parser {
    fn parse<'a>(&self, input: &'a str) -> &'a str;
}

// As a trait object bound:
fn run(p: &dyn for<'a> Parser, s: &str) -> &str { ... }
// shorthand: dyn Parser (the for<'a> is implicit for method lifetimes)
```

---

### Q3.2 — What is the `'static` lifetime? Explain all the ways a type can have `'static` bound and the implications.

**Answer:**

`'static` means the data can live for the **entire duration of the program**. It is the longest possible lifetime.

**Three distinct uses:**

**1. `'static` as a lifetime bound on a type parameter:**
```rust
fn store<T: 'static>(val: T) {
    // T must not contain any non-'static references
    // T can be: i32, String, Vec<i32>, Box<dyn Trait + 'static>
    // T cannot be: &'a str (unless 'a == 'static), Rc<&'b i32>
}
// This does NOT mean T lives forever — just that it CAN
```

**2. `'static` as a reference lifetime:**
```rust
let s: &'static str = "hello"; // string literal in binary's .rodata
static BYTES: [u8; 4] = [1,2,3,4];
let r: &'static [u8] = &BYTES;  // reference to static storage
```

**3. `'static` as a trait object lifetime bound:**
```rust
// Box<dyn Trait> defaults to Box<dyn Trait + 'static>
// i.e., the trait object cannot hold non-'static references
fn make_task() -> Box<dyn Fn() + 'static> {
    Box::new(|| println!("hello"))
}
```

**Why `'static` appears everywhere in async/thread code:**

```rust
// std::thread::spawn requires F: 'static
// because the thread may outlive the spawning scope
std::thread::spawn(move || {
    // 'static bound: closure must own all its data
    // or reference truly static data
});

// tokio::spawn requires F: Future + Send + 'static
// same reason — task may outlive caller's stack frame
```

**`'static` does not mean leaked or immortal:**

```rust
let s = String::from("hello"); // heap-allocated, will be dropped
// s itself can satisfy 'static if moved into a 'static context:
let boxed: Box<dyn std::fmt::Debug + 'static> = Box::new(s);
// s is moved into Box — no references involved — Box owns it
// Box will be dropped at end of its scope despite 'static bound
```

---

### Q3.3 — Explain lifetime subtyping and the lattice of lifetimes. What does `'a: 'b` mean formally?

**Answer:**

**`'a: 'b` reads as "'a outlives 'b" or "'a is a subtype of 'b".**

This seems backwards from intuition: `'static` is the *longest* lifetime but also the *subtype* of all lifetimes. The key insight: a longer lifetime is more useful — you can use a `'static` reference anywhere a shorter-lived reference is expected.

```
LIFETIME LATTICE (subtyping order):
=====================================

  'static  ← longest, most constrained to produce, most flexible to consume
     │
     │  'a: 'static means 'a outlives everything
     │
    'a  ← some named lifetime
     │
    'b  ← shorter lifetime ('a: 'b, 'a outlives 'b)
     │
    'c  ← even shorter
     │
   ... (all lifetimes ordered by duration)
     │
  'local  ← shortest (a tiny inner scope)

Subtype: if 'a: 'b, then &'a T is a subtype of &'b T
         i.e., you can use &'a T where &'b T is expected
         because 'a reference is valid for at least as long as 'b

The consumer gets MORE guarantee with a longer lifetime → it's a subtype.
```

```rust
fn accept_ref<'b>(r: &'b str) { /* ... */ }

fn caller() {
    let long_lived = String::from("hello");
    let r: &'static str = "world"; // 'static outlives everything
    accept_ref(r); // OK: 'static: 'b for any 'b
}

// Lifetime bounds on structs:
struct Important<'a> {
    data: &'a str,
}

impl<'a> Important<'a> {
    // Requires 'a: 'b — the data must outlive the announcement
    fn announce<'b>(&'b self, msg: &'b str) -> &'b str
    where 'a: 'b  // 'a outlives 'b — so &self.data is valid for 'b
    {
        self.data
    }
}
```

---

## 4. Type System — Traits, Generics, Associated Types, GATs

### Q4.1 — What is the difference between trait objects (`dyn Trait`) and generics with trait bounds? When should you use each?

**Answer:**

**Generics with trait bounds → static dispatch (monomorphization):**

```rust
fn process<T: Serialize + Send>(item: T) {
    // Compiler generates a separate copy of this function
    // for every concrete type T used at call sites.
    // Zero runtime overhead — calls are direct, inlinable.
}

// Monomorphized to:
// fn process_String(item: String) { ... }
// fn process_i32(item: i32) { ... }
// etc.
```

**Trait objects → dynamic dispatch (vtable):**

```rust
fn process(item: &dyn Serialize) {
    // One function in binary. Runtime dispatches via vtable.
    // Cannot inline. Pointer indirection. ~2-5ns overhead per call.
}
```

```
VTABLE LAYOUT for &dyn Trait:
==============================

Fat pointer on stack:
┌────────────────────┬────────────────────┐
│  data ptr: *const T│  vtable: *const VT │
└────────────────────┴────────────────────┘
        │                      │
        ▼                      ▼
    Concrete T          ┌──────────────────┐
    on heap/stack       │ drop_in_place: fn│
                        │ size: usize      │
                        │ align: usize     │
                        │ method_1: fn ptr │
                        │ method_2: fn ptr │
                        │ ...              │
                        └──────────────────┘

Each concrete type gets ONE vtable (static in binary).
Multiple dyn Trait pointers to the same concrete type
share the same vtable.
```

**Object Safety Rules** — a trait can only be used as `dyn Trait` if:

```
1. No associated functions/methods with `Self: Sized` bound
   (those cannot be dispatched through vtable)
2. No generic methods (would require monomorphization at call site)
3. Does not use `Self` as a function parameter or return type
   (except through &Self or Box<Self>)
4. No associated constants (at present)
```

```rust
// NOT object safe:
trait Bad {
    fn clone_self(&self) -> Self; // returns Self → not object safe
    fn compare<T>(&self, other: T) -> bool; // generic method
}

// Object safe:
trait Good {
    fn name(&self) -> &str;
    fn process(&self, data: &[u8]) -> Vec<u8>;
}
```

**When to use each:**

```
Use generics (static dispatch) when:
  ✓ Performance is critical (tight loops, hot paths)
  ✓ You know all types at compile time
  ✓ You want to enable inlining and cross-function optimization
  ✓ You need to use the concrete type's other methods after calling trait methods
  ✗ Binary size bloat from many monomorphized copies is a concern

Use trait objects (dynamic dispatch) when:
  ✓ Heterogeneous collections (Vec<Box<dyn Plugin>>)
  ✓ Plugin systems, runtime-loaded behavior
  ✓ Reducing binary size (one code path vs N monomorphized copies)
  ✓ Recursive types (dyn Trait avoids infinite-size structs)
  ✓ Returning different concrete types from the same function
  ✗ Performance-critical inner loops
```

---

### Q4.2 — Explain associated types vs generic parameters on traits. When is each the right choice?

**Answer:**

**Generic parameter on trait:**
```rust
trait Converter<Output> {
    fn convert(&self) -> Output;
}

// A type can implement this for MULTIPLE Output types:
impl Converter<String> for i32 { fn convert(&self) -> String { self.to_string() } }
impl Converter<f64>    for i32 { fn convert(&self) -> f64    { *self as f64 } }

// Caller must specify which Output:
let s: String = 42i32.convert::<String>(); // or via type inference
```

**Associated type on trait:**
```rust
trait Iterator {
    type Item;  // exactly one Item per implementing type
    fn next(&mut self) -> Option<Self::Item>;
}

// A type can implement Iterator for exactly ONE Item type:
impl Iterator for MyVec {
    type Item = i32;
    fn next(&mut self) -> Option<i32> { ... }
}

// Cannot implement Iterator<Item=String> AND Iterator<Item=i32> for same type
```

**The rule of thumb:**

```
Associated type:
  → There is exactly ONE natural "output" type for a given implementor.
  → The trait forms a "function" from implementor → associated type.
  → Iterator, IntoIterator, Deref (type Target), Add (type Output)

Generic parameter:
  → The implementor can meaningfully implement the trait for MULTIPLE
    type arguments simultaneously.
  → From<T>, Into<T>, AsRef<T>, PartialEq<Rhs>, PartialOrd<Rhs>
```

**Why iterators use associated type:**

If `Iterator` were `Iterator<Item>`, you'd need to write:
```rust
// Ugly: every call site needs to specify Item
fn sum<I: Iterator<i32>>(iter: I) -> i32 { ... }
// vs. clean:
fn sum<I: Iterator<Item=i32>>(iter: I) -> i32 { ... }
// Actually with associated type, you just write:
fn sum<I: Iterator<Item=i32>>(iter: I) -> i32 { ... }
// And there's no ambiguity about which Item — there can only be one.
```

---

### Q4.3 — What are Generic Associated Types (GATs)? Explain with a real use case.

**Answer:**

**GATs** (stabilized in Rust 1.65) allow associated types to have their own generic parameters — most importantly, lifetime parameters. This is needed for traits where the associated type's lifetime depends on a reference to `self`.

**The problem GATs solve:**

```rust
// BEFORE GATs: this doesn't compile
trait Lending {
    type Item; // Item cannot borrow from self — no lifetime param!
    fn get(&self) -> Self::Item;
}

// You want to implement this so get() returns a reference INTO self,
// but you cannot — Item has no lifetime to tie to &self.
```

**With GATs:**

```rust
// Lending iterator — yields items that BORROW from self
trait LendingIterator {
    type Item<'a> where Self: 'a;  // GAT: Item parameterized by lifetime
    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
}

// Now implement for a buffer reader:
struct ChunkReader<'buf> {
    data: &'buf [u8],
    pos: usize,
}

impl<'buf> LendingIterator for ChunkReader<'buf> {
    type Item<'a> = &'a [u8] where Self: 'a;

    fn next<'a>(&'a mut self) -> Option<&'a [u8]> {
        if self.pos >= self.data.len() { return None; }
        let chunk = &self.data[self.pos..self.pos+4];
        self.pos += 4;
        Some(chunk)
    }
}
```

**Real-world use case — database cursor (yields rows borrowing from internal buffer):**

```rust
trait Cursor {
    type Row<'a> where Self: 'a;
    fn fetch_row<'a>(&'a mut self) -> Option<Self::Row<'a>>;
}

struct PgCursor {
    buffer: Vec<u8>,
    offset: usize,
}

impl Cursor for PgCursor {
    type Row<'a> = ParsedRow<'a>;  // Row borrows from buffer

    fn fetch_row<'a>(&'a mut self) -> Option<ParsedRow<'a>> {
        parse_next(&self.buffer[self.offset..])
    }
}

struct ParsedRow<'a> {
    fields: Vec<&'a str>,  // borrows from PgCursor's buffer
}
```

**Without GATs**, the only workarounds were returning owned types (allocate on every call) or using `unsafe` to cast lifetimes — GATs make this sound and ergonomic.

---

## 5. Variance, Covariance, Contravariance

### Q5.1 — Explain variance in Rust. What is covariance, contravariance, and invariance? Why does it matter?

**Answer:**

Variance describes how subtyping relationships between types propagate through generic type constructors.

If `'long: 'short` (long outlives short), then for a type `F<'_>`:

```
COVARIANT:     F<'long> is a subtype of F<'short>
               (longer lifetime → subtype, safe to use where shorter expected)
               Example: &'a T, *const T, fn() -> T

CONTRAVARIANT: F<'short> is a subtype of F<'long>
               (shorter lifetime → subtype when in input position)
               Example: fn(T) — argument types are contravariant

INVARIANT:     No subtyping relationship in either direction
               Example: &'a mut T, *mut T, UnsafeCell<T>
```

```
VARIANCE TABLE FOR RUST TYPES:
================================

Type                Variance in 'a    Variance in T
─────────────────── ───────────────── ─────────────────
&'a T               covariant         covariant
&'a mut T           covariant         INVARIANT
*const T            —                 covariant
*mut T              —                 INVARIANT
Box<T>              —                 covariant
Vec<T>              —                 covariant
UnsafeCell<T>       —                 INVARIANT
Cell<T>             —                 INVARIANT
fn(T) -> U          —         T: contravariant, U: covariant
PhantomData<T>      —                 covariant
PhantomData<fn(T)>  —                 contravariant
PhantomData<fn()->T>—                 covariant
```

**Why `&mut T` is invariant in T:**

If `&mut T` were covariant, the following would be unsound:

```rust
// HYPOTHETICAL — if &mut T were covariant (IT IS NOT)
let mut big: &'static str = "hello";
{
    let small = String::from("world"); // shorter lifetime
    let r: &mut &'long str = &mut big;
    // If covariant: &mut &'long str "is" &mut &'short str
    let bad: &mut &'short str = r;    // would be allowed
    *bad = &small;                    // big now points to small!
}
// small dropped — big is now a dangling reference!
```

Invariance prevents this: you cannot coerce `&mut &'long str` to `&mut &'short str`.

**Why function arguments are contravariant:**

```rust
type Handler = fn(&'short str);

// A fn(&'long str) can be used where fn(&'short str) is needed:
// because fn(&'long str) is MORE restrictive (only accepts longer-lived strs)
// meaning it's SAFER than fn(&'short str) — wait, this is backwards...

// Actually: fn(T) is contravariant in T.
// fn(&'long str) <: fn(&'short str)
// because fn(&'long str) accepts 'long refs, but 'short: 'long is needed...

// The intuition: a function that can handle LESS (shorter lifetimes)
// can always be used where a function handling MORE is expected.
// Think of it as: contravariance flips the subtyping arrow.
```

**PhantomData variance patterns:**

```rust
// Custom type that owns T — should be covariant
struct MyBox<T> {
    ptr: *mut T,              // *mut T is invariant
    _marker: PhantomData<T>,  // add PhantomData<T> → covariant
}

// Custom type that acts like a function parameter — should be contravariant
struct Sink<T> {
    callback: *mut (),
    _marker: PhantomData<fn(T)>, // contravariant in T
}

// Custom type that needs invariance (interior mutability):
struct MyCell<T> {
    ptr: *mut T,
    _marker: PhantomData<*mut T>, // invariant in T (same as UnsafeCell)
}
```

---

## 6. Smart Pointers & Interior Mutability

### Q6.1 — Explain `Cell<T>`, `RefCell<T>`, `Mutex<T>`, `RwLock<T>`. When is each appropriate and what are the performance characteristics?

**Answer:**

All four implement **interior mutability** — allowing mutation through a shared reference (`&T`). They trade off between runtime cost, thread-safety, and access patterns.

```
INTERIOR MUTABILITY DECISION TREE:
====================================

                        Do you need thread safety?
                        /                         \
                      No                          Yes
                      │                            │
           Is T: Copy?                    Need concurrent reads?
           /         \                   /                    \
         Yes          No              No (exclusive)         Yes (shared)
          │            │                │                       │
       Cell<T>    RefCell<T>        Mutex<T>               RwLock<T>
       (zero cost) (runtime borrow  (exclusive lock)       (readers/writer lock)
                    checking)
```

**`Cell<T>` — for `Copy` types, single-threaded:**

```rust
use std::cell::Cell;

struct Counter {
    count: Cell<u32>,  // mutable through &Counter
}

impl Counter {
    fn increment(&self) {  // &self, not &mut self!
        self.count.set(self.count.get() + 1);
    }
}
// Mechanism: get() copies out the value, set() copies in
// Zero overhead — just wraps a value with UnsafeCell internally
// NOT Send, NOT Sync
```

**`RefCell<T>` — runtime borrow checking, single-threaded:**

```rust
use std::cell::RefCell;

struct Cache {
    data: RefCell<Vec<String>>,
}

impl Cache {
    fn add(&self, s: String) {
        self.data.borrow_mut().push(s);  // panics if already borrowed
    }
    fn read(&self) -> std::cell::Ref<Vec<String>> {
        self.data.borrow()  // shared borrow — can have multiple
    }
}
// Mechanism: stores isize borrow count in header
//   0        = unborrowed
//   positive = N shared borrows
//   -1       = one exclusive borrow
// Runtime cost: atomic-like counter update (no actual atomics — not thread-safe)
// NOT Send, NOT Sync
```

**`Mutex<T>` — exclusive lock, multi-threaded:**

```rust
use std::sync::{Mutex, Arc};

let m = Arc::new(Mutex::new(vec![1u32, 2, 3]));

let m2 = m.clone();
std::thread::spawn(move || {
    let mut guard = m2.lock().unwrap(); // blocks until lock acquired
    guard.push(4);
    // guard dropped → lock released
});

// Poisoning: if a thread panics while holding the lock,
// subsequent lock() calls return Err(PoisonError)
// .unwrap() propagates panic, or use .unwrap_or_else(|e| e.into_inner())
```

```
MUTEX INTERNALS (simplified pthread_mutex / futex):
====================================================

Mutex<T>:
┌──────────────────────────────────────┐
│ inner: UnsafeCell<T>                 │  ← the protected data
│ state: AtomicUsize (0=free, 1=locked)│  ← fast path: atomic CAS
│ waiters: OS primitive (futex/cond)   │  ← slow path: OS blocking
└──────────────────────────────────────┘

Fast path (uncontended):
  CAS(state, 0, 1) → succeeds immediately → no syscall

Slow path (contended):
  CAS fails → futex_wait() → thread de-scheduled by OS
  Unlock → futex_wake() → waiting thread re-scheduled

Cost: uncontended ~5-10ns (just atomic ops)
      contended: syscall + context switch ~1-10µs
```

**`RwLock<T>` — readers-writer lock:**

```rust
use std::sync::RwLock;

let lock = RwLock::new(vec![1, 2, 3]);

// Multiple concurrent readers:
let r1 = lock.read().unwrap();
let r2 = lock.read().unwrap();
println!("{:?} {:?}", *r1, *r2); // both valid simultaneously
drop(r1); drop(r2);

// Exclusive writer:
let mut w = lock.write().unwrap(); // waits for all readers
w.push(4);

// WARNING: RwLock can starve writers if readers are constant.
// std's RwLock does NOT guarantee writer priority — platform-dependent.
// parking_lot::RwLock has configurable fairness and is faster.
```

**Performance comparison:**

```
Operation           Cell<T>    RefCell<T>   Mutex<T>     RwLock<T>
─────────────────── ────────── ──────────── ─────────── ────────────
Overhead            0          1 atomic-ish  1 CAS        1-2 CAS
Thread safe         No         No            Yes          Yes
Concurrent reads    No*        Yes (Ref)     No           Yes
Panic on conflict   No         Yes           Deadlock     Yes/Deadlock
Send/Sync           No         No            Yes (T:Send) Yes (T:Send+Sync)
```

---

### Q6.2 — What is `UnsafeCell<T>` and why is it the only way to achieve interior mutability in Rust?

**Answer:**

`UnsafeCell<T>` is the **foundation** of all interior mutability. It is a lang item that tells the compiler:

> "The aliasing rules do not apply to the contents of this type.
> Do not optimize under the assumption that this data is immutable
> when accessed through shared references."

**Why it's necessary:**

The Rust compiler (and LLVM) optimize code based on the assumption that `&T` references are **read-only** — similar to C's `const` restrict semantics. Without `UnsafeCell`, the compiler could cache reads, reorder memory accesses, and eliminate stores because it "knows" shared references don't change the data.

```rust
// WITHOUT UnsafeCell — compiler can cache the read:
let x: i32 = 5;
let r: &i32 = &x;
println!("{}", *r);  // compiler reads x once
// ... lots of code ...
println!("{}", *r);  // compiler may use cached value — fine, x is immutable

// WITH UnsafeCell — compiler cannot cache:
let x: UnsafeCell<i32> = UnsafeCell::new(5);
let r: &UnsafeCell<i32> = &x;
// UnsafeCell tells compiler: behind this shared reference, writes may occur
// So compiler must actually load from memory each time
unsafe { *x.get() = 10; }
// The mutation is valid because UnsafeCell opts out of aliasing rules
```

**`UnsafeCell`'s role in LLVM IR:**

Rust/LLVM uses `noalias` attribute on function parameters to enable aggressive aliasing-based optimizations. `UnsafeCell` suppresses this attribute for the contained type. Without `UnsafeCell`, any interior mutation would be undefined behavior (from an optimization standpoint — the compiler could "prove" the mutation didn't happen).

```rust
// Cell<T> is literally:
pub struct Cell<T: ?Sized> {
    value: UnsafeCell<T>,
}

// RefCell<T> is literally:
pub struct RefCell<T: ?Sized> {
    borrow: Cell<BorrowFlag>,  // isize counter
    value: UnsafeCell<T>,
}

// Mutex<T> in std is literally:
pub struct Mutex<T: ?Sized> {
    inner: sys::Mutex,          // OS primitive
    poison: poison::Flag,
    data: UnsafeCell<T>,
}

// The pattern: OS/atomic mechanism for coordination + UnsafeCell for the data
```

---

## 7. Unsafe Rust — The Full Picture

### Q7.1 — What is the Rust safety model? What exactly does `unsafe` permit and what invariants must you uphold?

**Answer:**

**The safety model:**

```
SAFE RUST:    All memory safety invariants are enforced by the type system
              and borrow checker at compile time.

UNSAFE RUST:  You, the programmer, take responsibility for upholding
              memory safety invariants that the compiler cannot verify.
              The compiler still enforces type safety and most other rules.
```

**The five powers that `unsafe` unlocks:**

```rust
unsafe {
    // Power 1: Dereference raw pointers
    let ptr: *const i32 = &42 as *const i32;
    let val = *ptr;  // safe only if ptr is valid, aligned, and points to initialized data

    // Power 2: Call unsafe functions or methods
    unsafe_function();

    // Power 3: Access or modify static mut variables
    static mut COUNTER: u32 = 0;
    COUNTER += 1;  // UB if any other code runs concurrently!

    // Power 4: Implement unsafe traits (Send, Sync, GlobalAlloc)
    // (done at item level, not expression level)

    // Power 5: Access union fields
    union Bits { i: i32, f: f32 }
    let b = Bits { i: 42 };
    let float = b.f;  // interprets bit pattern — programmer's responsibility
}
```

**What `unsafe` does NOT bypass:**

```
✗ Type checking — still fully enforced
✗ Borrow checker for safe references — still enforced
✗ Lifetimes — still enforced
✗ Integer overflow in debug mode — still panics
✗ Pattern matching exhaustiveness
✗ Trait bounds resolution
```

**The Undefined Behavior (UB) table — what you must NEVER do:**

```
UB Category              Example
──────────────────────── ──────────────────────────────────────────────
Data race                Two threads, one writes, no synchronization
Dangling pointer deref   Accessing freed or out-of-scope memory
Misaligned pointer deref *ptr where ptr is not aligned for type T
Uninitialized memory     Reading MaybeUninit<T> before init
Broken aliasing          &mut T while other ref exists (even in unsafe)
Invalid bit patterns     bool with value 3, char with invalid codepoint
Calling wrong ABI        Rust fn called as C fn with different args
Stack overflow           Unbounded recursion without #[inline(never)]
Signed integer overflow  i32::MAX + 1 (wrapping ops: use wrapping_add)
Out-of-bounds access     Indexing beyond allocated memory
```

**The "Safety Contract" pattern:**

Every `unsafe` block must be justified by a comment explaining WHY it's sound:

```rust
fn get_unchecked<T>(slice: &[T], index: usize) -> &T {
    // SAFETY: Caller guarantees index < slice.len()
    // and slice is a valid reference (ensured by &[T] type).
    // Therefore the pointer arithmetic is in-bounds and
    // the returned reference has the same lifetime as slice.
    unsafe { &*slice.as_ptr().add(index) }
}
```

---

### Q7.2 — Explain raw pointers (`*const T` and `*mut T`). How do you safely create and use them? What are the aliasing rules for unsafe code (Stacked Borrows)?

**Answer:**

**Raw pointer properties:**

```
*const T / *mut T:
  ✓ Can be null
  ✓ No lifetime tracked by compiler
  ✓ No exclusive access guarantee
  ✓ Can alias freely (compiler makes no aliasing assumptions)
  ✓ Can be cast between types (use with extreme care)
  ✗ Cannot be dereferenced in safe code
  ✗ Not automatically dereferenced
```

**Valid ways to create raw pointers:**

```rust
// From references (always valid — reference guarantees are met):
let x = 42u32;
let ptr: *const u32 = &x as *const u32;  // or &x as *const _
let ptr: *const u32 = std::ptr::addr_of!(x); // preferred: avoids creating reference

let mut y = 42u32;
let mut_ptr: *mut u32 = &mut y as *mut u32;
let mut_ptr: *mut u32 = std::ptr::addr_of_mut!(y); // preferred

// From raw allocation:
let layout = std::alloc::Layout::new::<u32>();
let ptr: *mut u32 = unsafe { std::alloc::alloc(layout) as *mut u32 };

// Null pointer:
let null: *const u32 = std::ptr::null();
let null_mut: *mut u32 = std::ptr::null_mut();
```

**Safe dereference conditions:**

```
To safely dereference *const T or *mut T, ALL must be true:
1. Pointer is non-null
2. Pointer is properly aligned for T (ptr as usize % align_of::<T>() == 0)
3. Pointer points to initialized T value (not padding, not uninit)
4. Pointer is within a single allocated object (no out-of-bounds)
5. For *mut T deref: no other references (safe or unsafe) to same location
6. The pointed-to T is valid for 'a if you create &'a T from it
```

**Stacked Borrows — the aliasing model for unsafe:**

Stacked Borrows is a formal operational semantics for Rust's memory model (proposed by Ralf Jung, used in Miri). It tracks which pointers have "permission" to access memory at each location.

```
STACKED BORROWS MODEL:
========================

Each memory location has a "borrow stack":
  ┌─────────────────────────────────┐
  │ Top (most recent/innermost)     │
  │   &mut T  → SharedReadWrite(id) │ ← active exclusive access
  │   &T      → SharedReadOnly      │ ← pops above → read-only
  │   *mut T  → Raw(id)             │ ← raw pointer tag
  │ Bottom                          │
  └─────────────────────────────────┘

Rules:
- Creating &mut T from *mut T: push SharedReadWrite, invalidates items above
- Creating &T from *mut T: push SharedReadOnly, raw ptr loses write permission
- Accessing memory: must have valid tag at top of stack

Violation example:
  let raw: *mut i32 = ...;
  let r: &i32 = &*raw;      // push SharedReadOnly — raw loses write permission
  unsafe { *raw = 5; }     // STACKED BORROWS VIOLATION: raw has no write permission
```

**Miri — the runtime undefined behavior detector:**

```bash
# Install and run with Miri:
rustup component add miri
cargo miri test
cargo miri run

# Miri detects:
# - Stacked Borrows violations
# - Use of uninitialized memory
# - Data races (with -Zmiri-ignore-leaks)
# - Out-of-bounds access
# - Invalid enum/bool/char values
```

---

### Q7.3 — Write a sound implementation of a split_at_mut replacement for slices using raw pointers.

**Answer:**

```rust
/// Splits a mutable slice into two non-overlapping mutable slices at `mid`.
///
/// # Safety invariants we must uphold:
/// - Both returned slices must not overlap (they cover distinct memory regions)
/// - Both returned slices must have valid length and pointer
/// - Neither slice aliases the other (critical for &mut safety)
pub fn split_at_mut_unchecked<T>(slice: &mut [T], mid: usize) -> (&mut [T], &mut [T]) {
    let len = slice.len();
    let ptr = slice.as_mut_ptr();

    assert!(mid <= len, "mid ({mid}) must be <= len ({len})");

    // SAFETY:
    // 1. ptr is valid and non-null (derived from &mut [T], which is always valid)
    // 2. ptr.add(mid) is within bounds: mid <= len, so at most one-past-the-end
    // 3. The two slices [ptr, ptr+mid) and [ptr+mid, ptr+len) are non-overlapping
    //    because they cover disjoint index ranges with no overlap.
    // 4. Both pointers are properly aligned (T's alignment preserved by add())
    // 5. We consume the original &mut [T], so no aliasing with the source
    // 6. Both slices have lifetime tied to the original &mut [T]
    unsafe {
        (
            std::slice::from_raw_parts_mut(ptr, mid),
            std::slice::from_raw_parts_mut(ptr.add(mid), len - mid),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_at_mut() {
        let mut v = vec![1, 2, 3, 4, 5];
        let (left, right) = split_at_mut_unchecked(&mut v, 2);
        assert_eq!(left,  &[1, 2]);
        assert_eq!(right, &[3, 4, 5]);

        // Can mutate both independently:
        left[0]  = 10;
        right[0] = 30;
        assert_eq!(v, vec![10, 2, 30, 4, 5]);
    }

    #[test]
    fn test_split_at_empty() {
        let mut v: Vec<i32> = vec![];
        let (l, r) = split_at_mut_unchecked(&mut v, 0);
        assert!(l.is_empty());
        assert!(r.is_empty());
    }

    #[test]
    fn test_split_at_full_left() {
        let mut v = vec![1, 2, 3];
        let (l, r) = split_at_mut_unchecked(&mut v, 3);
        assert_eq!(l, &[1, 2, 3]);
        assert!(r.is_empty());
    }
}
```

---

## 8. Concurrency — Send, Sync, Atomics, Mutexes

### Q8.1 — What are `Send` and `Sync`? Explain their definitions precisely and give examples of types that are not Send or not Sync.

**Answer:**

`Send` and `Sync` are **marker traits** — they carry no methods, only semantics. They are the compiler's concurrency safety guarantee.

**Formal definitions:**

```
T: Send   ⟺  It is safe to TRANSFER ownership of T to another thread.
              i.e., moving T across thread boundaries is sound.

T: Sync   ⟺  It is safe to SHARE a reference to T across threads.
              i.e., &T: Send (shared reference can be sent to another thread).

Equivalently: T: Sync ⟺ &T: Send
```

**Auto-impl rules:**

```
The compiler AUTOMATICALLY implements Send and Sync for most types:
  - Struct is Send if ALL its fields are Send
  - Struct is Sync if ALL its fields are Sync
  - Raw pointers *const T, *mut T are NOT Send, NOT Sync (conservative)
```

**Types that are NOT Send:**

```rust
// Rc<T> — not Send (reference count is Cell<usize>, not atomic)
// Sending Rc across threads would allow two threads to increment the
// same non-atomic counter simultaneously → data race.
let rc = Rc::new(42);
// std::thread::spawn(move || { let _ = rc; }); // COMPILE ERROR

// MutexGuard<'_, T> — not Send
// The guard must be unlocked on the SAME thread that locked the mutex
// (on some OS implementations). Sending the guard to another thread
// and dropping it there would violate this.
let m = Mutex::new(0);
let guard = m.lock().unwrap();
// std::thread::spawn(move || drop(guard)); // COMPILE ERROR

// *mut T / *const T — not Send (raw pointers, no safety guarantee)
// Cell<T> — not Sync (but IS Send if T: Send)
```

**Types that are NOT Sync:**

```rust
// Cell<T> — not Sync
// Cell::set/get are NOT atomic. Two threads calling set() concurrently = data race.
// RefCell<T> — not Sync
// The borrow counter is Cell<isize>, non-atomic. Concurrent borrow() = data race.
// UnsafeCell<T> — not Sync (the foundation of interior mutability)
// Rc<T> — not Sync (and not Send)
```

**Implementing Send/Sync manually (unsafe):**

```rust
// A raw-pointer-based structure that IS safe to send across threads:
struct MySendablePtr {
    ptr: *mut u8,
    len: usize,
}

// SAFETY: We own the allocation uniquely (like Box<[u8]>)
// and do not share the pointer. Therefore sending to another
// thread transfers ownership — no concurrent access possible.
unsafe impl Send for MySendablePtr {}
unsafe impl Sync for MySendablePtr {} // &Self safe to share if we don't mutate without sync

// A type that wraps a thread-local handle — NOT safe to send:
struct ThreadLocalHandle {
    handle: *mut ffi::Handle, // must only be used on creating thread
}
// We explicitly opt OUT of auto-Send (raw ptr already does this automatically)
// But if we had safe fields that auto-derive Send:
// impl !Send for ThreadLocalHandle {}  // opt out (negative impl, unstable)
```

---

### Q8.2 — Explain Rust's memory ordering model. When would you use `Relaxed`, `Acquire`/`Release`, `AcqRel`, and `SeqCst`?

**Answer:**

Rust's atomic memory orderings map directly to the C++11 memory model, which in turn maps to hardware memory barriers.

**The problem: CPU and compiler reordering:**

```
WITHOUT synchronization, CPUs and compilers can reorder instructions:
  Thread 1              Thread 2
  ─────────────────     ─────────────────
  data = 42;            if ready.load() {
  ready.store(true);      println!("{}", data); // might see 0!
  }

The CPU may execute ready.store before data = 42 (store reordering).
Thread 2 may see ready=true but data=0. This is undefined behavior.
```

**Memory ordering levels:**

```
RELAXED (weakest — no ordering constraints):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Only guarantees atomicity of the operation itself.
  No ordering relative to other memory accesses.
  Use: counters where you only need the final value, not ordering.

  counter.fetch_add(1, Ordering::Relaxed); // fine for simple stats

ACQUIRE (load) + RELEASE (store):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RELEASE store: all writes BEFORE the store are visible to any
                 thread that does an ACQUIRE load of the same location.
  ACQUIRE load:  all reads AFTER the load see the writes that happened
                 before the RELEASE store.

  Establishes a happens-before relationship:
  [Release store of flag] → [Acquire load of flag]
  → all writes before release are visible after acquire

  Thread 1:                 Thread 2:
  data = 42;                if flag.load(Acquire) {
  flag.store(1, Release);     // guaranteed to see data=42
                            }

ACQREL (load+store, e.g., compare_exchange):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Both acquire and release semantics on a read-modify-write.
  Use for: compare-and-swap, fetch-add in lock-free algorithms.

SEQCST (strongest — total order):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  All SeqCst operations appear in a single global total order
  seen by ALL threads. Most expensive (full memory fence on x86,
  even more on ARM/POWER).
  Use: when you need a global ordering across MULTIPLE atomic variables.

  // Classic Dekker's algorithm requires SeqCst:
  flag1.store(true, SeqCst);
  if !flag2.load(SeqCst) { /* enter critical section */ }
  // Weaker ordering would allow both threads to enter simultaneously
```

**Hardware mapping:**

```
x86-64 (TSO — Total Store Order):
  Relaxed store = MOV (already release-like on TSO)
  Relaxed load  = MOV (already acquire-like on TSO)
  SeqCst store  = MOV + MFENCE (expensive)
  SeqCst load   = MOV (free on x86!)

ARM64 (weakly ordered):
  Relaxed store = STR
  Relaxed load  = LDR
  Release store = STLR (store-release)
  Acquire load  = LDAR (load-acquire)
  SeqCst        = STLR + LDAR (+ DMB ISH for full barrier)

On ARM, Acquire/Release is NOT free — it uses special instructions.
On x86, Acquire/Release is mostly free — TSO gives you it automatically.
```

**Production example — spinlock:**

```rust
use std::sync::atomic::{AtomicBool, Ordering};
use std::hint;

pub struct SpinLock {
    locked: AtomicBool,
}

impl SpinLock {
    pub const fn new() -> Self {
        Self { locked: AtomicBool::new(false) }
    }

    pub fn lock(&self) {
        let mut backoff = 1usize;
        loop {
            // Try to acquire: CAS false→true
            // On success: Acquire — we see all writes before the Release unlock
            if self.locked
                .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_ok()
            {
                return;
            }
            // Exponential backoff to reduce cache coherence traffic:
            for _ in 0..backoff {
                hint::spin_loop(); // PAUSE instruction on x86, YIELD on ARM
            }
            backoff = (backoff * 2).min(64);
        }
    }

    pub fn unlock(&self) {
        // Release: all our writes are visible to the next locker
        self.locked.store(false, Ordering::Release);
    }
}
```

---

## 9. Async/Await — Internals, Executors, Wakers, Pin

### Q9.1 — How does `async/await` work internally? Describe the state machine transformation and the role of `Future`.

**Answer:**

Async functions are transformed by the compiler into state machines that implement the `Future` trait. This is completely zero-cost — no heap allocation, no runtime threads for the state machine itself.

**The `Future` trait:**

```rust
pub trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

pub enum Poll<T> {
    Ready(T),    // computation is complete
    Pending,     // not ready, will call cx.waker().wake() when ready
}
```

**State machine transformation:**

```rust
// Source code:
async fn fetch_and_process(url: &str) -> String {
    let response = http_get(url).await;       // suspension point 1
    let body     = response.read_body().await; // suspension point 2
    process(body)
}

// Compiler transforms this to roughly:
enum FetchAndProcessFuture<'a> {
    // State 0: Initial — before any await
    Initial { url: &'a str },

    // State 1: Waiting for http_get to complete
    WaitingForGet {
        url: &'a str,
        fut: HttpGetFuture<'a>,
    },

    // State 2: Waiting for read_body to complete
    WaitingForBody {
        response_fut: ReadBodyFuture,
    },

    // State 3: Completed (terminal)
    Completed,
}

impl<'a> Future for FetchAndProcessFuture<'a> {
    type Output = String;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<String> {
        loop { // loop allows falling through states without returning
            match unsafe { self.get_unchecked_mut() } {
                Self::Initial { url } => {
                    let fut = http_get(url);
                    *self = Self::WaitingForGet { url, fut };
                    // Fall through to poll WaitingForGet
                }
                Self::WaitingForGet { url, fut } => {
                    match unsafe { Pin::new_unchecked(fut) }.poll(cx) {
                        Poll::Pending  => return Poll::Pending,
                        Poll::Ready(r) => {
                            let body_fut = r.read_body();
                            *self = Self::WaitingForBody { response_fut: body_fut };
                            // Fall through
                        }
                    }
                }
                Self::WaitingForBody { response_fut } => {
                    match unsafe { Pin::new_unchecked(response_fut) }.poll(cx) {
                        Poll::Pending  => return Poll::Pending,
                        Poll::Ready(b) => {
                            *self = Self::Completed;
                            return Poll::Ready(process(b));
                        }
                    }
                }
                Self::Completed => panic!("polled after completion"),
            }
        }
    }
}
```

**Async state machine memory layout:**

```
ASYNC TASK MEMORY LAYOUT:
===========================

Stack (executor's thread):           Heap (Task allocation):
┌────────────────────────┐           ┌────────────────────────────────────┐
│ poll() call frame       │           │ TaskHeader:                         │
│  cx: &Context           │           │   vtable: *const RawWakerVTable    │
│  future: Pin<&mut F>    │───────────│   state: AtomicUsize (running/etc) │
│                         │           │   queue_next: *mut Task            │
└────────────────────────┘           ├────────────────────────────────────┤
                                     │ Future state machine:               │
                                     │   FetchAndProcessFuture {           │
                                     │     state: WaitingForGet            │
                                     │     url: &str (fat ptr)             │
                                     │     http_fut: HttpGetFuture {       │
                                     │       conn: TcpStream               │
                                     │       buffer: [u8; 4096]            │
                                     │       ...                           │
                                     │     }                               │
                                     │   }                                 │
                                     └────────────────────────────────────┘

All intermediate state lives IN the future struct — no separate stack!
This is why async tasks are cheap: ~100-400 bytes per task typical,
vs ~4-8 KB for an OS thread stack.
```

---

### Q9.2 — Explain the `Waker` mechanism. How does an executor know when to re-poll a future?

**Answer:**

The `Waker` is the notification channel between a future and its executor. When a future returns `Poll::Pending`, it MUST arrange to call `waker.wake()` when progress can be made.

```
WAKER MECHANISM:
=================

Future (e.g., TcpStream read)      Executor
─────────────────────────────────  ─────────────────────────
poll(cx) called →                  Creates Context with Waker
  - registers waker with epoll/    ←  Waker tied to task queue
    io_uring/kqueue for readiness     
  - returns Poll::Pending          Sees Pending → parks task

OS notifies: socket is readable
  epoll_wait() returns             ← OS event
  Waker::wake() called             Wakes task: moves from
                                   "parked" → "ready queue"
                                   
                                   Executor re-polls the task
                                   
poll(cx) called again →            
  - reads from socket              
  - returns Poll::Ready(data)      Task complete

THE WAKER CONTRACT:
===================
  1. Future receives Waker via cx.waker()
  2. Future MUST store the Waker (clone it if needed)
  3. When external event occurs, future's notification handler calls wake()
  4. Waker::wake() is Send + 'static — safe to send to I/O threads
  5. wake() may be called BEFORE poll returns Pending (spurious wake OK)
  6. wake() must be idempotent and safe to call multiple times
```

**Manual waker implementation:**

```rust
use std::task::{RawWaker, RawWakerVTable, Waker};
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;

// A simple "channel waker" — wakes by pushing task index to a queue
struct TaskQueue {
    ready: Mutex<VecDeque<usize>>,
}

// The vtable defines how to clone, wake, and drop the waker
static VTABLE: RawWakerVTable = RawWakerVTable::new(
    // clone
    |ptr| {
        let arc = unsafe { Arc::from_raw(ptr as *const TaskQueue) };
        let cloned = arc.clone();
        std::mem::forget(arc); // don't drop the original
        RawWaker::new(Arc::into_raw(cloned) as *const (), &VTABLE)
    },
    // wake (consume self)
    |ptr| {
        let arc = unsafe { Arc::from_raw(ptr as *const TaskQueue) };
        // Notify: push current task to ready queue
        // (in real code, you'd pass the task ID)
        arc.ready.lock().unwrap().push_back(0);
    },
    // wake_by_ref (don't consume)
    |ptr| {
        let arc = unsafe { Arc::from_raw(ptr as *const TaskQueue) };
        arc.ready.lock().unwrap().push_back(0);
        std::mem::forget(arc);
    },
    // drop
    |ptr| {
        drop(unsafe { Arc::from_raw(ptr as *const TaskQueue) });
    },
);

fn make_waker(queue: Arc<TaskQueue>) -> Waker {
    let raw = RawWaker::new(Arc::into_raw(queue) as *const (), &VTABLE);
    unsafe { Waker::from_raw(raw) }
}
```

---

### Q9.3 — What is `Pin<P>` and `Unpin`? Why is it required for async/await?

**Answer:**

`Pin<P>` is a type that **guarantees the value behind the pointer will not be moved** in memory after it is pinned. This is required for async state machines that contain self-referential data.

**The self-referential problem:**

```rust
// The compiler generates this for an async function:
struct MyFuture {
    x: i32,
    x_ref: *const i32, // points to self.x — SELF-REFERENTIAL
}

// If we MOVE MyFuture (copy its bytes to new location):
// x_ref still points to OLD location → dangling pointer!

// Normal Rust prevents this automatically, but:
// - async state machines ARE self-referential (variables across await points
//   can be referenced by later code in the same state machine)
// - We need to run poll() on them through a pointer safely
```

**`Pin<P>` solution:**

```rust
// Pin<&mut T> guarantees: the T will NOT be moved while this Pin exists
// Once you have Pin<&mut T>, you cannot get &mut T (which would allow moves)

pub struct Pin<P> {
    pointer: P, // private — prevents direct access that could move the pointee
}

// Key API:
impl<'a, T: ?Sized> Pin<&'a mut T> {
    // Safe if T: Unpin (moving is fine for this type)
    pub fn get_mut(self) -> &'a mut T where T: Unpin { ... }

    // Unsafe — you promise NOT to move the T
    pub unsafe fn get_unchecked_mut(self) -> &'a mut T { ... }

    // Create a Pin from an existing &mut (safe if T: Unpin)
    pub fn new(pointer: &'a mut T) -> Self where T: Unpin { ... }

    // Unsafe creation — you promise pointee is already immovable
    pub unsafe fn new_unchecked(pointer: &'a mut T) -> Self { ... }
}
```

**`Unpin` — the opt-out:**

```rust
// Unpin is an auto-trait: most types implement it automatically
// Unpin means: "pinning me has no effect — I can be moved even when pinned"
// This is true for i32, String, Vec<T>, etc. — they have no self-references

// Types that do NOT implement Unpin:
// - async fn state machines (compiler-generated)
// - PhantomPinned (marker to explicitly opt out)

use std::marker::PhantomPinned;

struct SelfReferential {
    value: i32,
    self_ref: *const i32, // will point to self.value
    _pin: PhantomPinned,  // opt out of Unpin — prevents accidental moves
}
```

**Pinning to the heap (most common) vs stack:**

```rust
use std::pin::Pin;

// Heap pinning — simple and safe:
let future = Box::pin(async { 42 }); // Pin<Box<impl Future<Output=i32>>>
// Box::pin allocates on heap and pins. Future can never move.

// Stack pinning — requires pin! macro or manual unsafe:
// (std doesn't have pin! yet, but tokio::pin! and pin-utils exist)
tokio::pin!(future);
// future is now Pin<&mut impl Future>, valid for this scope

// In an executor — polling through Pin:
fn drive<F: Future>(mut fut: Pin<&mut F>) {
    let waker = noop_waker(); // simplified
    let mut cx = Context::from_waker(&waker);
    loop {
        match fut.as_mut().poll(&mut cx) {
            Poll::Ready(v) => { println!("Done: {:?}", v); break; }
            Poll::Pending  => { /* would block/sleep in real executor */ }
        }
    }
}
```

---

## 10. Closures, Iterators & Zero-Cost Abstractions

### Q10.1 — How are closures implemented in Rust? What is the difference between `Fn`, `FnMut`, `FnOnce`?

**Answer:**

Closures in Rust are **anonymous structs** that capture variables from their environment and implement one or more of the `Fn*` traits. They are fully statically typed — no dynamic dispatch unless you use `dyn Fn`.

**Closure desugaring:**

```rust
let mut count = 0i32;
let mut increment = || {
    count += 1;  // captured by mutable reference
    count
};
increment(); // → 1
increment(); // → 2

// Desugared to approximately:
struct ClosureCaptures<'a> {
    count: &'a mut i32,  // captured by &mut ref (because we mutate)
}

impl<'a> FnMut() -> i32 for ClosureCaptures<'a> {
    fn call_mut(&mut self) -> i32 {
        *self.count += 1;
        *self.count
    }
}
```

**Capture modes — determined by how variables are used:**

```
By reference (&T):      closure reads the variable
By mut reference (&mut T): closure mutates the variable
By move (T):            closure moved variable out, or `move` keyword used
```

**The three Fn traits:**

```
FnOnce — can be called AT MOST ONCE
  Implemented by: any closure (all closures implement FnOnce)
  Reason: takes `self` (consuming) — closure is consumed on call
  Use when: closure may move out of captured values

FnMut — can be called any number of times, MUTABLY
  Implemented by: closures that mutate captures (but don't consume)
  Takes: &mut self — exclusive access each call
  Superset of FnOnce (FnMut: FnOnce)

Fn — can be called any number of times, through shared reference
  Implemented by: closures that only read captures (or have no captures)
  Takes: &self — shared access
  Superset of FnMut (Fn: FnMut: FnOnce)

Hierarchy: Fn ⊂ FnMut ⊂ FnOnce
  (A Fn is also FnMut is also FnOnce)
```

```rust
// FnOnce — moves out of capture:
let s = String::from("hello");
let consume: impl FnOnce() = move || drop(s); // drops s, can only call once
consume();
// consume(); // COMPILE ERROR: value used after move

// FnMut — mutates capture:
let mut total = 0;
let mut add: impl FnMut(i32) = |x| { total += x; };
add(1); add(2); add(3); // fine, called multiple times

// Fn — reads only:
let greeting = String::from("hello");
let greet: impl Fn(&str) = |name| println!("{greeting}, {name}!");
greet("Alice"); greet("Bob"); // called any number of times
```

**Function pointers vs closures:**

```rust
// fn pointer: no captures, zero-size
fn add_one(x: i32) -> i32 { x + 1 }
let fp: fn(i32) -> i32 = add_one; // 8 bytes (pointer)

// Closure with captures: non-zero-size struct
let offset = 10i32;
let add_offset = |x: i32| x + offset; // sizeof = sizeof(i32) = 4 bytes (capture)
// add_offset is NOT fn(i32)->i32 — it's a unique anonymous type

// Every closure has a UNIQUE TYPE even if same signature:
let c1 = |x: i32| x + 1;
let c2 = |x: i32| x + 1;
// typeof(c1) != typeof(c2) — they are distinct monomorphized types!
```

---

### Q10.2 — Explain iterator adapters and how zero-cost abstractions work. What happens at the LLVM level?

**Answer:**

Rust's iterator adapters are **zero-cost** — the compiler inlines and fuses them into the same assembly as a hand-written loop. This is one of Rust's most impressive features.

**Iterator trait:**

```rust
pub trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;

    // All adapter methods have default implementations:
    fn map<B, F: FnMut(Self::Item) -> B>(self, f: F) -> Map<Self, F> { ... }
    fn filter<P: FnMut(&Self::Item) -> bool>(self, f: P) -> Filter<Self, P> { ... }
    fn take(self, n: usize) -> Take<Self> { ... }
    fn sum<S: Sum<Self::Item>>(self) -> S { ... }
    // ~80 more adapter methods...
}
```

**How adapter structs work:**

```rust
// map() returns a Map struct — no allocation, no heap:
pub struct Map<I, F> {
    iter: I,   // inner iterator (owns its state)
    f: F,      // the mapping closure (owns its captures)
}

impl<B, I: Iterator, F: FnMut(I::Item) -> B> Iterator for Map<I, F> {
    type Item = B;
    fn next(&mut self) -> Option<B> {
        // Pull one item from inner, apply f, return
        self.iter.next().map(|x| (self.f)(x))
    }
}

// A chain of adapters is a NESTED GENERIC TYPE:
// vec.iter().map(|x| x*2).filter(|x| x > 5).take(3).sum::<i32>()
// Type: Sum<Take<Filter<Map<std::slice::Iter<'_, i32>, fn>, fn>, i32>>
// This is ONE monomorphized type — compiler sees all the code
```

**Compiler optimization pipeline:**

```
SOURCE CODE:
  let sum: i32 = (0..100).filter(|x| x % 2 == 0).map(|x| x * x).sum();

AFTER MONOMORPHIZATION (compiler sees all types):
  Creates a single specialized function for this exact chain.

AFTER INLINING (all next() calls inlined):
  Equivalent to:
    let mut sum = 0i32;
    let mut i = 0i32;
    while i < 100 {
        if i % 2 == 0 {
            sum += i * i;
        }
        i += 1;
    }

AFTER LLVM OPTIMIZATIONS:
  - Loop unrolling
  - SIMD vectorization (processes 4-8 elements at once)
  - Strength reduction (eliminate redundant computations)
  - Output: tight vectorized machine code

ASM (approximate, x86-64 with AVX2):
  vmovdqu   ymm0, [rip+constants]  ; load 8 integers at once
  ; ... vectorized operations ...
  ; identical to hand-written SIMD intrinsics
```

**Verifying zero-cost — use godbolt.org or cargo-asm:**

```bash
cargo install cargo-show-asm
cargo asm --lib 'my_crate::my_fn'
# Shows the actual assembly generated
```

---

## 11. Macros — Declarative and Procedural

### Q11.1 — Explain how declarative macros (`macro_rules!`) work. What is the hygiene mechanism?

**Answer:**

Declarative macros (`macro_rules!`) perform **syntactic pattern matching and substitution** on the token tree of Rust source code. They operate before type-checking.

**Structure:**

```rust
macro_rules! vec_of_strings {
    // Each arm: (pattern) => { expansion }
    ( $( $x:expr ),* ) => {   // pattern: zero or more comma-separated expressions
        {
            let mut v = Vec::new();
            $(                        // repetition matching the * above
                v.push(String::from($x));
            )*
            v
        }
    };
}

let v = vec_of_strings!["hello", "world"];
// Expands to:
// { let mut v = Vec::new(); v.push(String::from("hello")); v.push(String::from("world")); v }
```

**Fragment specifiers (the type system of macro patterns):**

```
$x:expr      — any expression
$x:ident     — an identifier (variable/function name)
$x:ty        — a type
$x:path      — a path (std::collections::HashMap)
$x:pat       — a pattern (Ok(x), Some(y), ...)
$x:stmt      — a statement
$x:block     — a block { ... }
$x:item      — a top-level item (fn, struct, impl, ...)
$x:meta      — attribute contents (#[derive(Debug)])
$x:literal   — a literal value (42, "hello", 3.14)
$x:tt        — a single token tree (any single token or balanced brackets)
$x:lifetime  — a lifetime ('a, 'static)
$x:vis       — visibility qualifier (pub, pub(crate))
```

**Hygiene:**

Macro hygiene ensures that identifiers introduced inside a macro do NOT conflict with identifiers in the caller's scope:

```rust
macro_rules! make_var {
    ($val:expr) => {
        let x = $val;  // this 'x' is hygienic — does not interfere with
        x              // caller's 'x'
    };
}

fn main() {
    let x = 42;
    let y = make_var!(10); // expands with a DISTINCT 'x' internally
    println!("{x} {y}");   // prints "42 10" — no conflict
}
```

Hygiene works through **syntax contexts** — each identifier is tagged with the context (macro invocation site vs definition site) where it came from. Identifiers from different contexts are distinct even if they spell the same name.

**Breaking hygiene intentionally:**

```rust
// If you want the macro to define a variable accessible to caller:
macro_rules! define_x {
    () => {
        // Use $crate for module-level hygiene:
        // For local variables, hygiene cannot be broken in macro_rules!
        // (This is a limitation — use proc macros for fine-grained control)
    };
}
// Workaround: accept the identifier as a parameter:
macro_rules! define_var {
    ($name:ident, $val:expr) => {
        let $name = $val;  // caller provides the name → their scope
    };
}
define_var!(result, 42);
println!("{result}"); // works!
```

---

### Q11.2 — How do procedural macros work? Explain attribute macros, derive macros, and function-like macros.

**Answer:**

Procedural macros are **Rust programs that transform token streams** at compile time. They receive `TokenStream` input and produce `TokenStream` output, operating on the compiler's AST representation.

```
PROCEDURAL MACRO COMPILATION PIPELINE:
========================================

Source code → Lexer → Token stream
                           │
                    proc-macro crate
                    (compiled separately,
                     runs as plugin)
                           │
                           ▼
                    Transformed token stream
                           │
                    Main compilation continues
                    (type checking, borrow checking, etc.)
```

**Three types of procedural macros:**

**1. Derive macros (`#[derive(MyTrait)]`):**

```rust
// In proc-macro crate (separate crate with proc-macro = true in Cargo.toml):
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyDebug)]
pub fn my_debug_derive(input: TokenStream) -> TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let name = &ast.ident;

    let gen = quote! {
        impl std::fmt::Debug for #name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                write!(f, stringify!(#name))
            }
        }
    };
    gen.into()
}
```

**2. Attribute macros (`#[my_attribute]`):**

```rust
#[proc_macro_attribute]
pub fn retry(attr: TokenStream, item: TokenStream) -> TokenStream {
    let max_retries: usize = attr.to_string().parse().unwrap_or(3);
    let input = parse_macro_input!(item as syn::ItemFn);
    let fn_name = &input.sig.ident;
    let fn_body = &input.block;
    let fn_sig  = &input.sig;

    quote! {
        #fn_sig {
            let mut attempts = 0;
            loop {
                let result = (|| #fn_body)();
                if result.is_ok() || attempts >= #max_retries {
                    return result;
                }
                attempts += 1;
            }
        }
    }.into()
}

// Usage:
#[retry(5)]
fn flaky_operation() -> Result<(), Error> { ... }
```

**3. Function-like macros (`my_macro!(...)`):**

```rust
#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let sql_str = input.to_string();
    // Validate SQL at compile time, generate type-safe query code
    let validated = validate_sql(&sql_str); // compile-time SQL validation!
    quote! {
        Query::new(#validated)
    }.into()
}

// Usage: sql!(SELECT * FROM users WHERE id = ?)
```

**Key crates for proc macros:**

```toml
[dependencies]
syn  = { version = "2", features = ["full"] }  # Parse Rust syntax into AST
quote = "1"                                      # Quasi-quoting: generate token streams
proc-macro2 = "1"                               # TokenStream that works outside proc-macro context
```

---

## 12. Error Handling Patterns

### Q12.1 — Explain Rust's error handling philosophy and the full range of patterns: `Result`, `Option`, `?`, custom error types, `thiserror`, `anyhow`.

**Answer:**

Rust's approach: errors are **values**, not exceptions. They propagate explicitly, are type-checked, and require handling at each call site.

**The `?` operator — desugaring:**

```rust
fn read_config(path: &str) -> Result<Config, io::Error> {
    let content = std::fs::read_to_string(path)?;
    //                                           ^ desugars to:
    // match std::fs::read_to_string(path) {
    //     Ok(v) => v,
    //     Err(e) => return Err(From::from(e)), // applies From conversion
    // }
    Ok(parse_config(&content))
}
```

**Custom error types — two approaches:**

**Manual implementation:**

```rust
#[derive(Debug)]
pub enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    Config(String),
}

impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(e)     => write!(f, "I/O error: {e}"),
            Self::Parse(e)  => write!(f, "Parse error: {e}"),
            Self::Config(s) => write!(f, "Config error: {s}"),
        }
    }
}

impl std::error::Error for AppError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Io(e)    => Some(e),
            Self::Parse(e) => Some(e),
            Self::Config(_) => None,
        }
    }
}

impl From<std::io::Error> for AppError {
    fn from(e: std::io::Error) -> Self { Self::Io(e) }
}
impl From<std::num::ParseIntError> for AppError {
    fn from(e: std::num::ParseIntError) -> Self { Self::Parse(e) }
}
```

**Using `thiserror` (library errors — for libraries):**

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DatabaseError {
    #[error("connection failed: {0}")]
    Connection(#[from] std::io::Error),

    #[error("query failed: {query}, reason: {reason}")]
    Query { query: String, reason: String },

    #[error("row not found: id={id}")]
    NotFound { id: u64 },
}
// thiserror generates: Display, Error::source(), From impls — all via derive
```

**Using `anyhow` (application errors — for binaries):**

```rust
use anyhow::{Context, Result, anyhow, bail};

fn process() -> Result<()> {  // anyhow::Result = Result<T, anyhow::Error>
    let data = std::fs::read("file.txt")
        .context("failed to read file.txt")?;  // adds context to any error

    if data.is_empty() {
        bail!("file is empty");  // return Err(anyhow!(...))
    }

    if data.len() > 1024 {
        return Err(anyhow!("file too large: {} bytes", data.len()));
    }

    Ok(())
}

// anyhow::Error stores:
// - The original error (any Error impl)
// - A backtrace (if RUST_BACKTRACE=1)
// - Context chain for human-readable messages
```

**Error handling decision tree:**

```
Library code (published crate)?
  YES → Use thiserror for structured, typed errors
        Users of your library can pattern-match on variants
        Never use anyhow in library public API

Application code (binary)?
  YES → Use anyhow for convenience
        Rich context, backtrace, easy propagation
        Users won't pattern-match on your internal errors

Performance-critical hot path?
  YES → Avoid heap allocation in error path
        Use enum-based errors (no Box<dyn Error>)
        Consider returning raw i32 codes + decode later

Domain errors that callers must handle?
  YES → Typed Result<T, SpecificError>
        Force callers to acknowledge each error case

Best practice: Library returns typed errors, application converts to anyhow
```

---

## 13. Memory Allocators & Custom Allocation

### Q13.1 — Explain the `GlobalAlloc` trait. How do you write a custom allocator and set it as the global allocator?

**Answer:**

Rust's memory allocation is abstracted through the `GlobalAlloc` trait. The default is `System` (libc's malloc/free). You can replace it globally or use `Allocator` (nightly) for per-collection allocation.

**`GlobalAlloc` trait:**

```rust
pub unsafe trait GlobalAlloc {
    // Allocate memory: layout specifies size and alignment
    // Returns: null if OOM, otherwise pointer to usable memory
    unsafe fn alloc(&self, layout: Layout) -> *mut u8;

    // Deallocate memory: ptr must have been from alloc(), layout must match
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout);

    // Optional: zero-initialized allocation (default: alloc + memset 0)
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 { ... }

    // Optional: resize allocation in place (default: alloc new + memcpy + dealloc old)
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 { ... }
}
```

**Complete custom bump allocator example:**

```rust
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

/// A simple bump allocator for short-lived arena allocations.
/// Allocates from a fixed-size pool; dealloc is a no-op.
/// Free all memory at once by resetting the cursor.
pub struct BumpAllocator {
    pool: *mut u8,
    pool_size: usize,
    cursor: AtomicUsize,
}

impl BumpAllocator {
    pub const fn new() -> Self {
        Self {
            pool: std::ptr::null_mut(),
            pool_size: 0,
            cursor: AtomicUsize::new(0),
        }
    }

    /// Initialize with a pre-allocated pool.
    /// # Safety: pool must be valid and pool_size bytes large
    pub unsafe fn init(&mut self, pool: *mut u8, pool_size: usize) {
        self.pool = pool;
        self.pool_size = pool_size;
        self.cursor.store(0, Ordering::Relaxed);
    }

    pub fn reset(&self) {
        self.cursor.store(0, Ordering::Relaxed);
    }
}

unsafe impl GlobalAlloc for BumpAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let size  = layout.size();
        let align = layout.align();

        // Atomic bump: find next aligned position
        let mut current = self.cursor.load(Ordering::Relaxed);
        loop {
            // Align up current cursor:
            let aligned = (current + align - 1) & !(align - 1);
            let next    = aligned + size;

            if next > self.pool_size {
                return std::ptr::null_mut(); // OOM
            }

            // CAS: only one thread bumps to this slot
            match self.cursor.compare_exchange_weak(
                current, next, Ordering::AcqRel, Ordering::Relaxed
            ) {
                Ok(_)  => return self.pool.add(aligned),
                Err(c) => current = c,
            }
        }
    }

    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // Bump allocator: individual frees are no-ops
        // Memory reclaimed by reset() or allocator destruction
    }
}

// IMPORTANT: BumpAllocator needs to be safe to share across threads
// AtomicUsize handles concurrent alloc(); we need Sync:
unsafe impl Sync for BumpAllocator {}

// Production usage pattern — use system allocator for the backing pool:
static mut POOL: [u8; 1024 * 1024] = [0u8; 1024 * 1024]; // 1 MB static pool

#[global_allocator]
static ALLOCATOR: BumpAllocator = BumpAllocator::new();

// Initialize in main():
fn main() {
    unsafe {
        // In a real program, call init before ANY allocation
        // (tricky — std startup also allocates)
    }
}

// More practical: use as a SCOPED allocator, not global:
// Use the unstable `Allocator` trait for per-collection allocation.
```

**Using `jemalloc` or `mimalloc` as global allocator:**

```toml
# Cargo.toml
[dependencies]
tikv-jemallocator = "0.5"
# or
mimalloc = { version = "0.1", default-features = false }
```

```rust
// main.rs or lib.rs:
#[cfg(not(target_env = "msvc"))]
use tikv_jemallocator::Jemalloc;

#[cfg(not(target_env = "msvc"))]
#[global_allocator]
static GLOBAL: Jemalloc = Jemalloc;
```

---

## 14. FFI — Foreign Function Interface

### Q14.1 — How do you call C code from Rust and Rust code from C? What are the safety considerations?

**Answer:**

FFI bridges Rust and C at the ABI level. Unsafe is required because C has no memory safety guarantees.

**Calling C from Rust:**

```rust
// Declare external C functions:
extern "C" {
    fn malloc(size: usize) -> *mut std::ffi::c_void;
    fn free(ptr: *mut std::ffi::c_void);
    fn strlen(s: *const std::ffi::c_char) -> usize;
    fn printf(format: *const std::ffi::c_char, ...) -> std::ffi::c_int;
}

// Using C strings:
use std::ffi::{CStr, CString};

fn call_c_strlen(s: &str) -> usize {
    // CString: Rust String → C null-terminated string (heap-allocated)
    let c_str = CString::new(s).expect("null byte in string");
    // SAFETY: c_str.as_ptr() is valid, null-terminated, valid for lifetime of c_str
    unsafe { strlen(c_str.as_ptr()) }
}

// Reading C strings returned from C:
fn from_c_string(ptr: *const std::ffi::c_char) -> String {
    // SAFETY: ptr must be a valid null-terminated C string
    // with lifetime sufficient for this scope
    let c_str = unsafe { CStr::from_ptr(ptr) };
    c_str.to_string_lossy().into_owned()
}
```

**Calling Rust from C:**

```rust
// Mark functions with C ABI and no name mangling:
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn rust_process_data(
    data: *const u8,
    len: usize,
    out: *mut u8,
    out_len: *mut usize,
) -> i32 {  // return i32 error code (C convention)
    // SAFETY checks:
    if data.is_null() || out.is_null() || out_len.is_null() {
        return -1; // invalid argument
    }

    let input = unsafe { std::slice::from_raw_parts(data, len) };

    let result = process(input);
    let result_len = result.len();

    // SAFETY: caller must provide out buffer large enough
    let out_slice = unsafe { std::slice::from_raw_parts_mut(out, result_len) };
    out_slice.copy_from_slice(&result);

    unsafe { *out_len = result_len; }
    0 // success
}

fn process(data: &[u8]) -> Vec<u8> {
    data.iter().map(|&b| b.wrapping_add(1)).collect()
}
```

**C header for the above (generated by cbindgen):**

```c
// Use cbindgen to auto-generate this:
// cbindgen --config cbindgen.toml --crate my_crate --output include/my_crate.h
#include <stdint.h>
int32_t rust_add(int32_t a, int32_t b);
int32_t rust_process_data(const uint8_t* data, size_t len,
                           uint8_t* out, size_t* out_len);
```

**Repr and struct layout for FFI:**

```rust
// Must use #[repr(C)] for structs passed to/from C:
#[repr(C)]
pub struct Point {
    x: f64,  // C: double
    y: f64,  // C: double
}

// Equivalent C: struct Point { double x; double y; };
// Layout: 16 bytes, no padding (f64 is 8-byte aligned)

// Repr(C) for enums (must have explicit discriminants):
#[repr(C)]
pub enum Status {
    Ok    = 0,
    Error = 1,
    Retry = 2,
}

// Opaque pointer pattern (common for handles):
#[repr(C)]
pub struct MyHandle {
    _private: [u8; 0], // zero-size, prevents construction
}

#[no_mangle]
pub extern "C" fn create_handle() -> *mut MyHandle {
    let boxed = Box::new(InternalState::new());
    Box::into_raw(boxed) as *mut MyHandle  // caller owns the memory
}

#[no_mangle]
pub extern "C" fn destroy_handle(h: *mut MyHandle) {
    if !h.is_null() {
        unsafe { drop(Box::from_raw(h as *mut InternalState)); }
    }
}

struct InternalState { /* ... */ }
impl InternalState { fn new() -> Self { todo!() } }
```

**Panic safety across FFI:**

```rust
// Panics must NEVER unwind across FFI boundaries — it's undefined behavior!
// Use catch_unwind to prevent this:

#[no_mangle]
pub extern "C" fn safe_callback(data: *const u8, len: usize) -> i32 {
    let result = std::panic::catch_unwind(|| {
        // All Rust code here — panics are caught
        process_data(data, len)
    });

    match result {
        Ok(v)  => v,
        Err(_) => {
            eprintln!("Rust panic caught at FFI boundary");
            -1 // return error code
        }
    }
}
```

---

## 15. Compiler Internals — MIR, Borrow Checker, Monomorphization

### Q15.1 — Describe the Rust compilation pipeline. What are the intermediate representations and what happens at each stage?

**Answer:**

```
RUST COMPILATION PIPELINE:
============================

Source (.rs)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ LEXER/PARSER                                                  │
│  Source text → Token stream → Abstract Syntax Tree (AST)    │
│  Handles: syntax, macros (expanded here), attributes         │
└────────────────────────────┬─────────────────────────────────┘
                             │ AST
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ HIR — High-level Intermediate Representation                  │
│  Desugars: for loops, if-let, while-let, ? operator          │
│  Type inference runs here (Hindley-Milner-style)             │
│  Trait resolution happens here                               │
│  Name resolution, privacy checks                             │
└────────────────────────────┬─────────────────────────────────┘
                             │ HIR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ THIR — Typed HIR (introduced ~2021)                           │
│  Fully typed version of HIR                                  │
│  Pattern matching exhaustiveness check                       │
│  Unsafety checking (some checks here)                        │
└────────────────────────────┬─────────────────────────────────┘
                             │ THIR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ MIR — Mid-level Intermediate Representation                   │
│  Control Flow Graph (CFG) based                              │
│  Explicit: drops, moves, borrows, lifetimes                  │
│  BORROW CHECKER runs here (NLL — Non-Lexical Lifetimes)      │
│  Drop elaboration: insert explicit drop() calls              │
│  Const evaluation (CTFE — compile-time function evaluation)  │
│  Optimizations: inlining, copy propagation, dead code elim   │
└────────────────────────────┬─────────────────────────────────┘
                             │ MIR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ MONOMORPHIZATION                                              │
│  Generic functions instantiated for each concrete type       │
│  fn foo<T>(...) → fn foo_i32(...), fn foo_String(...), ...  │
│  Code size may grow significantly                            │
└────────────────────────────┬─────────────────────────────────┘
                             │ Monomorphized MIR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ LLVM IR GENERATION                                            │
│  MIR → LLVM IR                                               │
│  Rust-specific lowering: moves, panics, unwind tables        │
└────────────────────────────┬─────────────────────────────────┘
                             │ LLVM IR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ LLVM OPTIMIZATION PASSES                                      │
│  Inlining, vectorization, loop transforms, dead code elim    │
│  Alias analysis (informed by Rust's AXM → noalias attrs)    │
│  Profile-guided optimization (PGO) if enabled                │
└────────────────────────────┬─────────────────────────────────┘
                             │ Optimized LLVM IR
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ MACHINE CODE GENERATION                                       │
│  Target-specific: x86-64, aarch64, riscv64, wasm32, ...     │
│  Register allocation, instruction selection, scheduling      │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
                     Object files → Linker → Binary/Library
```

**Viewing MIR:**

```bash
# Dump MIR for a function:
rustc -Z dump-mir=all src/main.rs

# Or via cargo:
RUSTFLAGS="-Z dump-mir=my_function" cargo build

# View MIR for a simple function:
# fn add(a: i32, b: i32) -> i32 { a + b }
# MIR looks like:
# fn add(_1: i32, _2: i32) -> i32 {
#     let mut _0: i32;   // return place
#     bb0: {
#         _0 = Add(_1, _2);
#         return;
#     }
# }
```

---

### Q15.2 — How does the borrow checker (NLL) work? Explain the polonius model.

**Answer:**

**Non-Lexical Lifetimes (NLL)** — the current borrow checker:

NLL computes lifetimes as the **minimal set of program points** where a borrow must be live, rather than tying them to lexical scopes. It works on the MIR control flow graph.

```
NLL ALGORITHM:
===============

1. LIVENESS ANALYSIS:
   For each borrow 'a, compute the set of CFG nodes where
   'a must be "live" (the borrowed value might be used).
   This is a backwards dataflow analysis.

2. REGION INFERENCE:
   Each lifetime variable is a SET of CFG points.
   Constraints are generated:
     - 'a ⊆ 'b when a reference with lifetime 'a is stored
       in a place that holds lifetime 'b
     - 'a must include point P when 'a is live at P

3. SUBSET CONSTRAINTS SOLVED:
   Iteratively expand lifetime sets until fixed point.

4. ERROR CHECKING:
   If two borrows overlap (one mutable, one any), report error.
   If a borrow outlives the borrowed place, report error.

EXAMPLE — NLL allows this (lexical borrows would reject):

fn main() {
    let mut v = vec![1, 2, 3];
    let r = &v[0];          // borrow starts at line A
    println!("{r}");         // last use of r — borrow ENDS HERE (NLL)
    v.push(4);               // OK: r's borrow is dead, v is free
}
//                                 ▲ lexical borrow checker would keep
//                                 r alive until end of block — would reject v.push()
//                                 NLL correctly identifies r's last use
```

**Polonius — the next-generation borrow checker (in progress):**

Polonius reformulates borrow checking as a **Datalog** (logic programming) problem. Instead of "which lifetimes are live?", it asks "which loans could reach this program point?"

```
POLONIUS KEY IDEAS:
====================

1. "Loans" instead of "lifetimes":
   A loan is a specific borrow (e.g., &v at line 5).
   Polonius tracks where each loan's effects could flow.

2. Datalog facts and rules:
   loan_issued_at(r, p) — borrow r issued at point p
   loan_killed_at(r, p) — borrow r invalidated at p
   loan_live_at(r, p)   — borrow r may reach point p

3. More permissive than NLL:
   Polonius can accept some programs NLL rejects
   (specifically: non-lexical borrow patterns through loops
    and match expressions)

4. Better error messages:
   Can point to the exact conflicting loans

To test Polonius now:
  RUSTFLAGS="-Z polonius" cargo build  (nightly only)
```

---

## 16. Performance, SIMD & Low-Level Optimization

### Q16.1 — How do you write SIMD code in Rust? Explain portable SIMD vs platform intrinsics.

**Answer:**

Rust offers two approaches to SIMD:

**1. Platform-specific intrinsics (stable, target-specific):**

```rust
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

/// Sum 8 i32 values using AVX2 SIMD (256-bit = 8×32 lanes)
/// # Safety: CPU must support AVX2 (check with `is_x86_feature_detected!`)
#[target_feature(enable = "avx2")]
unsafe fn sum_8_avx2(data: &[i32; 8]) -> i32 {
    // Load 8 i32s into a 256-bit YMM register:
    let v = _mm256_loadu_si256(data.as_ptr() as *const __m256i);

    // Horizontal add: sum pairs → 4 values in lower 128 bits
    let sum128 = _mm_add_epi32(
        _mm256_extracti128_si256(v, 0),
        _mm256_extracti128_si256(v, 1),
    );
    // Further reduce:
    let sum64 = _mm_add_epi32(sum128, _mm_shuffle_epi32(sum128, 0b_10_11_00_01));
    let sum32 = _mm_add_epi32(sum64,  _mm_shuffle_epi32(sum64,  0b_00_00_10_10));
    _mm_cvtsi128_si32(sum32)
}

fn safe_sum_8(data: &[i32; 8]) -> i32 {
    if is_x86_feature_detected!("avx2") {
        unsafe { sum_8_avx2(data) }
    } else {
        data.iter().sum()
    }
}
```

**2. Portable SIMD (nightly, portable across architectures):**

```rust
#![feature(portable_simd)]
use std::simd::{Simd, SimdInt};

fn sum_slice_simd(data: &[i32]) -> i32 {
    const LANES: usize = 8;
    let (prefix, chunks, suffix) = data.as_simd::<LANES>();

    let mut sum_vec = Simd::<i32, LANES>::splat(0);
    for chunk in chunks {
        sum_vec += chunk;
    }

    // Horizontal sum of SIMD vector:
    let simd_sum: i32 = sum_vec.reduce_sum();

    // Handle non-SIMD prefix and suffix:
    prefix.iter().sum::<i32>() + simd_sum + suffix.iter().sum::<i32>()
}
```

---

### Q16.2 — What is `MaybeUninit<T>` and when must you use it?

**Answer:**

`MaybeUninit<T>` represents memory that may or may not contain a valid `T`. It prevents the compiler from assuming the memory is initialized, avoiding UB from reading uninitialized memory.

```rust
use std::mem::MaybeUninit;

/// Initialize an array element-by-element without requiring Default
fn init_array<T, F: Fn(usize) -> T>(f: F) -> [T; 10] {
    // WRONG: let mut arr: [T; 10] = unsafe { std::mem::zeroed() };
    // zeroed() = all-zeros bit pattern, which may not be a valid T

    // CORRECT:
    let mut arr: [MaybeUninit<T>; 10] = MaybeUninit::uninit_array();

    for (i, slot) in arr.iter_mut().enumerate() {
        slot.write(f(i));  // initialize each slot
    }

    // SAFETY: All 10 elements are now initialized (we wrote to each).
    // MaybeUninit::array_assume_init is the "I promise they're all init" call.
    unsafe { MaybeUninit::array_assume_init(arr) }
}

// Common pattern: read from FFI and wrap in MaybeUninit:
fn get_stat(path: &str) -> Option<libc::stat> {
    let mut stat_buf = MaybeUninit::<libc::stat>::uninit();
    let c_path = std::ffi::CString::new(path).ok()?;

    let ret = unsafe { libc::stat(c_path.as_ptr(), stat_buf.as_mut_ptr()) };
    if ret == 0 {
        // SAFETY: libc::stat returned 0 (success), so stat_buf is initialized
        Some(unsafe { stat_buf.assume_init() })
    } else {
        None
    }
}
```

---

## 17. no_std & Embedded/Kernel Environments

### Q17.1 — What is `no_std`? What is available and what is not? How do you write a `no_std` library?

**Answer:**

`#![no_std]` removes the dependency on the Rust standard library (`std`), leaving only `core` (always available) and optionally `alloc` (requires a heap allocator).

```
RUST LIBRARY LAYERS:
======================

┌─────────────────────────────────────────────────────────────┐
│ std (standard library)                                       │
│  File I/O, networking, threads, process, env variables      │
│  Depends on: OS services, libc, heap allocator              │
├─────────────────────────────────────────────────────────────┤
│ alloc                                                        │
│  Box, Vec, String, Rc, Arc, BTreeMap, HashMap (with hasher) │
│  Depends on: heap allocator (GlobalAlloc)                   │
├─────────────────────────────────────────────────────────────┤
│ core                                                         │
│  Primitive types, traits (Iterator, Clone, Copy, etc.)      │
│  Option, Result, mem, ptr, slice, intrinsics                │
│  NO heap, NO OS, runs anywhere                              │
└─────────────────────────────────────────────────────────────┘
```

**Writing a `no_std` library:**

```rust
#![no_std]  // Remove std
// If you need alloc:
extern crate alloc;  // User must provide a GlobalAlloc

use core::fmt;
use alloc::vec::Vec;  // Available if user provides allocator

/// A ring buffer that works in no_std environments.
pub struct RingBuffer<T, const N: usize> {
    buf:   [core::mem::MaybeUninit<T>; N],
    head:  usize,
    tail:  usize,
    count: usize,
}

impl<T, const N: usize> RingBuffer<T, N> {
    pub const fn new() -> Self {
        Self {
            // SAFETY: MaybeUninit arrays don't need initialization
            buf: unsafe { core::mem::MaybeUninit::uninit().assume_init() },
            head:  0,
            tail:  0,
            count: 0,
        }
    }

    pub fn push(&mut self, val: T) -> Result<(), T> {
        if self.count == N {
            return Err(val); // full
        }
        self.buf[self.tail].write(val);
        self.tail = (self.tail + 1) % N;
        self.count += 1;
        Ok(())
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.count == 0 {
            return None;
        }
        // SAFETY: head..tail range is initialized (invariant maintained by push/pop)
        let val = unsafe { self.buf[self.head].assume_init_read() };
        self.head = (self.head + 1) % N;
        self.count -= 1;
        Some(val)
    }

    pub fn len(&self) -> usize { self.count }
    pub fn is_empty(&self) -> bool { self.count == 0 }
}

impl<T, const N: usize> Drop for RingBuffer<T, N> {
    fn drop(&mut self) {
        // Drop all initialized elements:
        while self.pop().is_some() {}
    }
}
```

**`no_std` binary (embedded/kernel):**

```rust
#![no_std]
#![no_main]  // No Rust runtime startup — we provide main equivalent

use core::panic::PanicInfo;

// Must define panic handler:
#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    // On embedded: blink an LED, reset, or halt
    // On kernel: log and halt CPU
    loop {}
}

// Entry point via linker:
#[no_mangle]
pub extern "C" fn _start() -> ! {
    // Initialize BSS, set up stack, etc.
    main();
    loop {}
}

fn main() {
    // Your embedded/kernel code here
}
```

---

## 18. Type-Level Programming & Phantom Types

### Q18.1 — What are phantom types? How do you use them to encode state machines at the type level?

**Answer:**

Phantom types use `PhantomData<T>` to carry type-level information without runtime cost. This enables the compiler to enforce state machine transitions.

**Classic example — typestate pattern for a connection:**

```rust
use std::marker::PhantomData;

// State tokens — zero-sized, never constructed:
pub struct Disconnected;
pub struct Connected;
pub struct Authenticated;

// Connection parameterized by state:
pub struct Conn<State> {
    socket: std::net::TcpStream,
    _state: PhantomData<State>,
}

// Only available in Disconnected state:
impl Conn<Disconnected> {
    pub fn new(addr: &str) -> Result<Conn<Disconnected>, std::io::Error> {
        let socket = std::net::TcpStream::connect(addr)?;
        Ok(Conn { socket, _state: PhantomData })
    }

    // Consumes Disconnected, returns Connected — type transition!
    pub fn connect(self) -> Result<Conn<Connected>, std::io::Error> {
        // Perform TCP handshake, etc.
        Ok(Conn { socket: self.socket, _state: PhantomData })
    }
}

// Only available in Connected state:
impl Conn<Connected> {
    pub fn authenticate(self, token: &str) -> Result<Conn<Authenticated>, AuthError> {
        // Send auth token, verify response
        Ok(Conn { socket: self.socket, _state: PhantomData })
    }

    pub fn disconnect(self) -> Conn<Disconnected> {
        // Graceful shutdown
        Conn { socket: self.socket, _state: PhantomData }
    }
}

// Only available in Authenticated state:
impl Conn<Authenticated> {
    pub fn send_command(&mut self, cmd: &str) -> Result<String, std::io::Error> {
        // ... send and receive
        Ok(String::new())
    }
}

// Usage — compiler enforces correct state transitions:
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let conn = Conn::<Disconnected>::new("127.0.0.1:8080")?;
    let conn = conn.connect()?;        // now Connected
    let mut conn = conn.authenticate("token")?;  // now Authenticated
    let response = conn.send_command("PING")?;   // only valid here!

    // conn.connect() // COMPILE ERROR: connect() not on Conn<Authenticated>
    Ok(())
}

pub struct AuthError;
```

---

## 19. Pin, Unpin & Self-Referential Structs

### Q19.1 — Implement a safe self-referential struct using Pin.

**Answer:**

```rust
use std::pin::Pin;
use std::marker::PhantomPinned;
use std::ptr::NonNull;

/// A self-referential struct where `slice` points into `data`.
/// This is safe because Pin prevents the struct from moving.
pub struct SelfRef {
    data:   String,
    slice:  NonNull<str>,   // points into self.data — self-referential!
    _pin:   PhantomPinned,  // opt out of Unpin → compiler prevents moves
}

impl SelfRef {
    /// Create a new SelfRef pinned to the heap.
    pub fn new(data: String) -> Pin<Box<Self>> {
        let mut boxed = Box::pin(SelfRef {
            data,
            slice: NonNull::dangling(), // temporary placeholder
            _pin: PhantomPinned,
        });

        // SAFETY: We set up slice to point into data.
        // This is safe because:
        // 1. boxed is pinned — data will never move
        // 2. slice's lifetime is tied to self (same struct)
        // 3. We never expose &mut data or allow moves after this point
        let ptr: NonNull<str> = NonNull::from(boxed.data.as_str());
        unsafe {
            let mut_ref = Pin::as_mut(&mut boxed);
            Pin::get_unchecked_mut(mut_ref).slice = ptr;
        }

        boxed
    }

    /// Get the self-referential slice.
    pub fn get_slice(self: Pin<&Self>) -> &str {
        // SAFETY: slice is valid as long as self is pinned (invariant of construction)
        unsafe { self.slice.as_ref() }
    }

    pub fn get_data(self: Pin<&Self>) -> &str {
        &self.data
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_self_referential() {
        let pinned = SelfRef::new(String::from("hello world"));
        let pinned_ref = pinned.as_ref();

        assert_eq!(pinned_ref.get_data(),  "hello world");
        assert_eq!(pinned_ref.get_slice(), "hello world");

        // Verify they point to the same memory:
        let data_ptr  = pinned_ref.get_data().as_ptr();
        let slice_ptr = pinned_ref.get_slice().as_ptr();
        assert_eq!(data_ptr, slice_ptr);
    }
}
```

---

## 20. Testing, Fuzzing & Benchmarking

### Q20.1 — Describe the full testing story in Rust: unit tests, integration tests, property tests, fuzzing, and benchmarks.

**Answer:**

**Unit tests:**

```rust
// In the same file as the code:
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    #[should_panic(expected = "divide by zero")]
    fn test_panic() {
        divide(5, 0);
    }

    #[test]
    fn test_result() -> Result<(), Box<dyn std::error::Error>> {
        let v = parse_config("key=value")?;
        assert_eq!(v.get("key"), Some(&"value".to_string()));
        Ok(())
    }
}
```

**Integration tests:**

```
tests/
├── integration_test.rs   ← separate file, tests public API only
└── common/
    └── mod.rs             ← shared helpers
```

```rust
// tests/integration_test.rs
use my_crate::PublicApi;

#[test]
fn test_end_to_end() {
    let api = PublicApi::new();
    assert!(api.process("input").is_ok());
}
```

**Property-based testing with `proptest`:**

```rust
use proptest::prelude::*;

proptest! {
    // Test that sort is idempotent:
    #[test]
    fn test_sort_idempotent(mut v in prop::collection::vec(any::<i32>(), 0..100)) {
        v.sort();
        let sorted_once = v.clone();
        v.sort();
        assert_eq!(v, sorted_once); // sorting twice == sorting once
    }

    // Test that reverse(reverse(v)) == v:
    #[test]
    fn test_reverse_involution(v in prop::collection::vec(any::<u8>(), 0..256)) {
        let mut copy = v.clone();
        copy.reverse();
        copy.reverse();
        assert_eq!(v, copy);
    }
}
```

**Structure-aware fuzzing with `cargo-fuzz` (libFuzzer):**

```bash
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add my_target
```

```rust
// fuzz/fuzz_targets/my_target.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // Feed arbitrary bytes to your parser/deserializer:
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = my_crate::parse(s); // must not panic or UB
    }
});

// Structured fuzzing with arbitrary types:
fuzz_target!(|input: MyStruct| {
    // Derive Arbitrary on MyStruct:
    // #[derive(arbitrary::Arbitrary)]
    let _ = my_crate::process(input);
});
```

```bash
# Run fuzzer (will run until crash or Ctrl+C):
cargo fuzz run my_target

# Run with coverage-guided corpus:
cargo fuzz run my_target corpus/

# Generate coverage report:
cargo fuzz coverage my_target
```

**Benchmarking with Criterion:**

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "my_benchmark"
harness = false
```

```rust
// benches/my_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn bench_sort(c: &mut Criterion) {
    let mut group = c.benchmark_group("sort");

    for size in [100, 1000, 10000] {
        group.bench_with_input(
            BenchmarkId::new("std_sort", size),
            &size,
            |b, &size| {
                let data: Vec<i32> = (0..size).rev().collect();
                b.iter(|| {
                    let mut d = data.clone();
                    d.sort();
                    black_box(d) // prevent optimization
                });
            }
        );
    }
    group.finish();
}

criterion_group!(benches, bench_sort);
criterion_main!(benches);
```

```bash
cargo bench
# Generates HTML report at target/criterion/report/index.html
# Shows: mean, median, std dev, change from last run
```

**Memory and sanitizer testing:**

```bash
# AddressSanitizer — detect use-after-free, buffer overflow:
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu

# ThreadSanitizer — detect data races:
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu

# MemorySanitizer — detect use of uninitialized memory:
RUSTFLAGS="-Z sanitizer=memory" cargo +nightly test --target x86_64-unknown-linux-gnu

# Miri — UB detection (runs Rust interpreter):
cargo +nightly miri test

# Loom — concurrency model checker:
# (in Cargo.toml: loom = { version = "0.7", optional = true })
# RUSTFLAGS="--cfg loom" cargo test --lib
```

---

## Advanced Implementation: Lock-Free MPSC Queue

```rust
//! Lock-free multi-producer, single-consumer queue using atomics.
//! Demonstrates: Arc, atomics, unsafe, memory ordering in production context.

use std::sync::Arc;
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    value: Option<T>,       // None for sentinel/stub node
    next:  AtomicPtr<Node<T>>,
}

impl<T> Node<T> {
    fn new(value: T) -> *mut Self {
        Box::into_raw(Box::new(Self {
            value: Some(value),
            next:  AtomicPtr::new(ptr::null_mut()),
        }))
    }

    fn sentinel() -> *mut Self {
        Box::into_raw(Box::new(Self {
            value: None,
            next:  AtomicPtr::new(ptr::null_mut()),
        }))
    }
}

pub struct MpscSender<T> {
    tail: Arc<AtomicPtr<Node<T>>>,
}

pub struct MpscReceiver<T> {
    head: *mut Node<T>,
    tail: Arc<AtomicPtr<Node<T>>>,
}

// SAFETY: T: Send — values moved across thread boundary
unsafe impl<T: Send> Send for MpscSender<T>   {}
unsafe impl<T: Send> Send for MpscReceiver<T> {}

// Senders can be cloned (multi-producer):
impl<T> Clone for MpscSender<T> {
    fn clone(&self) -> Self {
        Self { tail: self.tail.clone() }
    }
}

pub fn channel<T>() -> (MpscSender<T>, MpscReceiver<T>) {
    let sentinel = Node::sentinel();
    let tail = Arc::new(AtomicPtr::new(sentinel));

    let sender   = MpscSender { tail: tail.clone() };
    let receiver = MpscReceiver { head: sentinel, tail };

    (sender, receiver)
}

impl<T> MpscSender<T> {
    pub fn send(&self, value: T) {
        let node = Node::new(value);

        // Enqueue: atomically update tail.next and advance tail pointer
        // Release: ensures value write is visible before node becomes reachable
        let prev_tail = self.tail.swap(node, Ordering::AcqRel);

        // SAFETY: prev_tail is a valid node (invariant: tail is always valid)
        // Link previous tail to our new node:
        unsafe {
            (*prev_tail).next.store(node, Ordering::Release);
        }
    }
}

impl<T> MpscReceiver<T> {
    pub fn recv(&mut self) -> Option<T> {
        // Acquire: see all writes that happened before the Release store in send()
        let next = unsafe { (*self.head).next.load(Ordering::Acquire) };

        if next.is_null() {
            return None; // queue empty
        }

        // SAFETY: next is valid (ensured by send's Release store)
        let value = unsafe { (*next).value.take() };

        // Old head becomes garbage — free it:
        let old_head = self.head;
        self.head = next;
        unsafe { drop(Box::from_raw(old_head)); }

        value
    }
}

impl<T> Drop for MpscReceiver<T> {
    fn drop(&mut self) {
        // Drain remaining items and free nodes:
        while self.recv().is_some() {}
        // Free the final sentinel/head node:
        unsafe { drop(Box::from_raw(self.head)); }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_send_recv() {
        let (tx, mut rx) = channel::<i32>();
        tx.send(1);
        tx.send(2);
        tx.send(3);
        assert_eq!(rx.recv(), Some(1));
        assert_eq!(rx.recv(), Some(2));
        assert_eq!(rx.recv(), Some(3));
        assert_eq!(rx.recv(), None);
    }

    #[test]
    fn test_multi_producer() {
        let (tx, mut rx) = channel::<i32>();
        let mut handles = vec![];

        for i in 0..10 {
            let tx2 = tx.clone();
            handles.push(std::thread::spawn(move || tx2.send(i)));
        }

        for h in handles { h.join().unwrap(); }

        let mut received: Vec<i32> = std::iter::from_fn(|| rx.recv()).collect();
        received.sort();
        assert_eq!(received, (0..10).collect::<Vec<_>>());
    }
}
```

---

## Quick Reference — Trait Implementations Cheat Sheet

```
TRAIT              WHEN TO IMPLEMENT                    AUTO?
──────────────────────────────────────────────────────────────────
Copy               POD types with no heap resources     No (#[derive])
Clone              Deep-copy semantics                  No (#[derive])
Drop               Custom cleanup on out-of-scope        No
Debug              Debug-format (println!("{:?}"))      No (#[derive])
Display            Human-readable format                No
PartialEq/Eq       Equality comparison                  No (#[derive])
PartialOrd/Ord     Ordering                             No (#[derive])
Hash               HashMap/HashSet key                  No (#[derive])
Default            Default::default() constructor       No (#[derive])
From/Into          Type conversions                     No (Into auto from From)
AsRef/AsMut        Cheap reference conversions          No
Deref/DerefMut     * operator / auto-deref              No
Iterator           .next() → Option<Item>              No
Send               Safe to move across threads          Yes (if fields: Send)
Sync               Safe to share ref across threads     Yes (if fields: Sync)
Unpin              Safe to move when pinned             Yes (most types)
Future             async computation                    No (async fn auto)
Error              error type chaining                  No
```

---

## References & Further Study

- **The Rustonomicon** — https://doc.rust-lang.org/nomicon/ (unsafe Rust bible)
- **Rust Reference** — https://doc.rust-lang.org/reference/ (language spec)
- **Jon Gjengset "Rust for Rustaceans"** — advanced idiomatic Rust
- **"Programming Rust" (Blandy, Orendorff)** — deep coverage of ownership/types
- **Mara Bos "Rust Atomics and Locks"** — concurrency from first principles
- **Ralf Jung's blog (ralfj.de)** — Stacked Borrows, Miri, memory model
- **TRPL async book** — https://rust-lang.github.io/async-book/
- **Compiler Explorer (godbolt.org)** — inspect generated assembly for Rust
- **Miri** — `cargo +nightly miri test` — runtime UB detection
- **cargo-flamegraph** — profiling with flame graphs
- **loom** — concurrency model checker for Rust
- **proptest / quickcheck** — property-based testing
- **cargo-fuzz** — coverage-guided fuzzing via libFuzzer

This will be a large, comprehensive guide. Let me build it in sections.**3,698 lines / ~125 KB** — a complete, production-depth reference. Here's what's covered:

---

**What the guide contains (20 sections):**

| Section | Core Concepts |
|---|---|
| 1 — Ownership & Memory Layout | Move semantics, stack/heap layout of String/Vec/Box/Rc/Arc, fat pointers, NPO, dropck |
| 2 — Borrowing & AXM | Aliasing XOR Mutability invariant, NLL timeline, two-phase borrows, re-borrows vs moves of &mut |
| 3 — Lifetimes (Advanced) | Elision rules, HRTB (`for<'a>`), `'static` semantics, lifetime subtyping lattice |
| 4 — Type System | Static vs dynamic dispatch, vtable layout, object safety rules, associated types vs generics, GATs with lending iterator |
| 5 — Variance | Covariance/contravariance/invariance table, why `&mut T` is invariant, PhantomData patterns |
| 6 — Smart Pointers & Interior Mutability | Cell/RefCell/Mutex/RwLock decision tree, UnsafeCell as the AXM foundation, mutex internals |
| 7 — Unsafe Rust | The 5 unsafe powers, UB table, stacked borrows model, Miri usage, sound split_at_mut impl |
| 8 — Concurrency | Send/Sync formal definitions, memory ordering (Relaxed/Acquire/Release/SeqCst), x86 vs ARM hardware, spinlock impl |
| 9 — Async/Await Internals | State machine transformation, task memory layout, Waker vtable, Pin/Unpin |
| 10 — Closures & Iterators | Closure desugaring, Fn/FnMut/FnOnce hierarchy, iterator zero-cost through LLVM |
| 11 — Macros | macro_rules! hygiene, fragment specifiers, proc macro pipeline (derive/attribute/function-like) |
| 12 — Error Handling | `?` desugaring, thiserror vs anyhow, error chaining, library vs application patterns |
| 13 — Allocators | GlobalAlloc trait, complete bump allocator with CAS, jemalloc/mimalloc integration |
| 14 — FFI | C↔Rust ABI, CStr/CString, repr(C), opaque handle pattern, panic across FFI |
| 15 — Compiler Internals | Full pipeline AST→HIR→THIR→MIR→LLVM→machine code, NLL algorithm, Polonius |
| 16 — Performance & SIMD | AVX2 intrinsics, portable_simd, MaybeUninit for uninitialized memory |
| 17 — no_std | core/alloc/std layers, no_std ring buffer, kernel entry point |
| 18 — Phantom Types | Typestate pattern for compile-time state machine enforcement |
| 19 — Pin & Self-Referential | Safe self-referential struct with PhantomPinned |
| 20 — Testing & Fuzzing | Unit/integration/proptest/cargo-fuzz/Criterion/ASAN/TSAN/Miri |

**Bonus:** Full lock-free MPSC queue implementation with correct AcqRel ordering + trait cheat sheet.

**Next 3 steps:**
1. Pick the sections where your mental model feels weakest (variance and Stacked Borrows are the most commonly underestimated) and reread them while running `cargo miri test` on your own code
2. For async internals — implement a toy executor from scratch using the Waker vtable shown in §9.2; nothing solidifies the poll model like writing one
3. For concurrency — read **Mara Bos's "Rust Atomics and Locks"** alongside §8; it covers every ordering subtlety with proof-level rigor and maps directly to how `parking_lot` and `crossbeam` are implemented

---

ROLE
You are a principal-level Rust systems engineer and technical educator with
10+ years of production Rust experience across embedded, OS, networking,
and distributed systems. You think in mental models, not syntax trivia.

TASK
Generate a complete, publication-quality intermediate Rust interview guide —
questions AND exhaustive answers — covering every concept an intermediate
Rust engineer must deeply understand to reason correctly about the language.

TARGET AUDIENCE
Engineers who already write basic Rust and are preparing for senior/staff
engineering interviews or want to build a rock-solid mental model of the
language's core mechanics from first principles.

COVERAGE — DO NOT SKIP ANY OF THESE
For every topic below, write at least one interview Q&A that is deep,
precise, and builds an accurate mental model:

  1. Ownership, moves, copy semantics, drop order
  2. Borrowing rules — shared vs exclusive, NLL (Non-Lexical Lifetimes)
  3. Lifetimes — annotations, elision rules, 'static, HRTBs
  4. Traits — bounds, supertraits, blanket impls, orphan rule
  5. Generics — monomorphization, turbofish, const generics
  6. Closures — Fn / FnMut / FnOnce hierarchy, capture modes
  7. Iterators — lazy evaluation, adapter chains, implementing Iterator
  8. Error handling — Result, Option, ? operator, custom error types,
     thiserror vs anyhow
  9. Smart pointers — Box, Rc, Arc, Cell, RefCell, Mutex, RwLock,
     interior mutability pattern
 10. Concurrency — thread::spawn, channels (mpsc), Send + Sync contracts
 11. Async/Await — Future trait, Poll model, executor vs reactor,
     Pin + Unpin, async runtimes (Tokio)
 12. Memory layout — size_of, align_of, repr(C/transparent/packed),
     enum layout, niche optimization
 13. Unsafe Rust — the 5 superpowers, invariants, raw pointers,
     safe abstraction patterns
 14. Trait objects — dyn Trait, vtable, object safety rules,
     static vs dynamic dispatch trade-offs
 15. Advanced pattern matching — guards, bindings, nested, @ bindings
 16. Collections — Vec, HashMap, BTreeMap, capacity management,
     performance characteristics
 17. Macros — declarative (macro_rules!), procedural overview,
     hygiene, when to use each
 18. Module system — pub/pub(crate)/pub(super), crate layout,
     re-exports, visibility rules
 19. Type system patterns — newtype, phantom types, typestate,
     builder pattern in Rust
 20. Testing — unit, integration, doc tests, #[cfg(test)], benchmarking

ANSWER STRUCTURE (apply to EVERY Q&A)
  - Question: precise, interview-realistic phrasing
  - Core concept: 2–4 sentence first-principles explanation
  - Mental model: how to think about it (analogy or invariant rule)
  - Code: complete, runnable Rust implementation with inline comments
  - ASCII diagram: where memory layout, ownership flow, or architecture
    benefits from visual representation — use real ASCII art only
  - Failure modes: what goes wrong if misunderstood, with compiler error
    or runtime consequence shown
  - Interview follow-up questions: 2–3 deeper probing questions
  - Key takeaway: one-sentence distillation

OUTPUT FORMAT
  - Markdown (.md) only
  - Fenced code blocks with language tags (```rust)
  - ASCII diagrams inside plain fenced blocks (```)
  - Numbered sections with H2 headers for each topic
  - Table of contents at the top with anchor links
  - No SVG, no rendered images, no HTML

QUALITY CONSTRAINTS
  - Every code snippet must compile on stable Rust (state if nightly
    feature is required and why)
  - Do not use placeholder comments like "// ... rest of impl" —
    write the complete implementation
  - Prefer std library; call out when an external crate is the
    idiomatic production choice and name it
  - Explain WHY the compiler rejects incorrect code, not just that it does
  - Show the alternative (wrong) approach first where it clarifies
    the correct approach
  - Accuracy over brevity — if a concept has nuance, show the nuance

TONE AND STYLE
  - Precise, direct, zero filler sentences
  - Teach the mental model that lets the engineer derive the answer,
    not just memorize it
  - Where trade-offs exist (e.g. Rc vs Arc, dyn vs generics),
    give a decision matrix or rule of thumb
  - Reference the Rust Reference or Nomicon when a concept is
    formally specified there
