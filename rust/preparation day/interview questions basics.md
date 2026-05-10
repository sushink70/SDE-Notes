# Rust Language Interview Questions & Answers: Basics
## A Complete, In-Depth Guide

---

> **How to use this guide:** Every question is answered with *why* before *what*. The mental models,
> ASCII diagrams, and real Rust implementations are designed to build deep intuition — not surface
> recall. Read, run the code, break it, fix it.

---

## Table of Contents

1. [What is Rust? Why does it exist?](#1-what-is-rust-why-does-it-exist)
2. [Rust's Memory Model: Stack vs Heap](#2-rusts-memory-model-stack-vs-heap)
3. [Ownership — The Core Mental Model](#3-ownership--the-core-mental-model)
4. [Move Semantics](#4-move-semantics)
5. [Copy Types vs Move Types](#5-copy-types-vs-move-types)
6. [Borrowing & References](#6-borrowing--references)
7. [The Borrow Checker](#7-the-borrow-checker)
8. [Lifetimes](#8-lifetimes)
9. [Slices](#9-slices)
10. [Data Types: Scalar Types](#10-data-types-scalar-types)
11. [Data Types: Compound Types (Tuples & Arrays)](#11-data-types-compound-types-tuples--arrays)
12. [Variables, Mutability & Shadowing](#12-variables-mutability--shadowing)
13. [Functions & Return Values](#13-functions--return-values)
14. [Control Flow](#14-control-flow)
15. [Structs](#15-structs)
16. [Enums](#16-enums)
17. [Pattern Matching (`match`)](#17-pattern-matching-match)
18. [Option\<T\>](#18-optiont)
19. [Result\<T, E\> & Error Handling](#19-resultt-e--error-handling)
20. [The `?` Operator](#20-the--operator)
21. [Vectors (`Vec<T>`)](#21-vectors-vect)
22. [Strings: `String` vs `&str`](#22-strings-string-vs-str)
23. [HashMaps](#23-hashmaps)
24. [Traits](#24-traits)
25. [Generics](#25-generics)
26. [Closures](#26-closures)
27. [Iterators & the Iterator Trait](#27-iterators--the-iterator-trait)
28. [Smart Pointers: `Box<T>`](#28-smart-pointers-boxt)
29. [Smart Pointers: `Rc<T>` and `RefCell<T>`](#29-smart-pointers-rct-and-refcellt)
30. [Modules, Crates & the Package System](#30-modules-crates--the-package-system)
31. [Common Rust Idioms & Patterns](#31-common-rust-idioms--patterns)
32. [Rust vs Other Languages — Interview Comparisons](#32-rust-vs-other-languages--interview-comparisons)

---

## 1. What is Rust? Why does it exist?

### Q: What is Rust and what problem does it solve?

**Answer:**

Rust is a systems programming language focused on three guarantees:
- **Memory safety** without a garbage collector
- **Concurrency** without data races
- **Performance** on par with C/C++

**The problem it solves:**

Languages before Rust forced you to choose two of three:

```
                    THE TRIANGLE OF TRADE-OFFS
                    (before Rust)

                        SAFE
                         /\
                        /  \
                       /    \
                      /      \
                   GC'd    Manual
               (Java, Go)  Memory
                    /        \
                   /  CHOOSE   \
                  /    TWO      \
          MANAGED              FAST
         (Python,             (C, C++)
          Ruby)

    Rust breaks this triangle:
    ┌─────────────────────────────────────┐
    │  Safe + Fast + No GC               │
    │  Achieved via OWNERSHIP SYSTEM      │
    └─────────────────────────────────────┘
```

**Why it was created:**

Mozilla Research created Rust (2010, stable 2015) because they were writing a browser engine (Servo) in C++ and kept hitting:
- Use-after-free bugs
- Buffer overflows
- Data races in concurrent code
- Null pointer dereferences

Rust's compiler enforces rules at *compile time* that prevent all of these — no runtime overhead, no garbage collector pauses.

**Key Rust Design Philosophy:**

```
┌──────────────────────────────────────────────────────────────┐
│                  RUST DESIGN PILLARS                         │
│                                                              │
│  1. OWNERSHIP   →  Every value has one owner                │
│  2. BORROWING   →  References don't own; rules enforced     │
│  3. LIFETIMES   →  Reference validity checked at compile    │
│  4. ZERO COST   →  Abstractions compile away to nothing     │
│     ABSTRACTIONS                                             │
│  5. FEARLESS    →  The compiler stops races before they     │
│     CONCURRENCY    happen                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Rust's Memory Model: Stack vs Heap

### Q: How does Rust manage memory? Explain stack vs heap.

**Answer:**

Understanding stack vs heap is foundational — Rust's ownership rules exist largely to manage heap memory correctly.

```
PROCESS MEMORY LAYOUT
═══════════════════════════════════════════════════
│                                                 │
│  HIGH ADDRESS                                   │
│  ┌─────────────────────────────────────────┐   │
│  │              STACK                      │   │
│  │  ↓ grows downward                       │   │
│  │                                         │   │
│  │  [frame: main()]                        │   │
│  │    x: 5          ← i32, 4 bytes         │   │
│  │    y: 3.14       ← f64, 8 bytes         │   │
│  │    flag: true    ← bool, 1 byte         │   │
│  │                                         │   │
│  │  [frame: foo()]                         │   │
│  │    a: 42         ← pushed on call       │   │
│  │    ↑ popped on return                   │   │
│  │                                         │   │
│  ├─────────────────────────────────────────┤   │
│  │              (free space)               │   │
│  ├─────────────────────────────────────────┤   │
│  │              HEAP                       │   │
│  │  ↑ grows upward                         │   │
│  │                                         │   │
│  │  [String "hello"]   ptr─────────────┐  │   │
│  │  [Vec<i32> data]    ptr──────────┐  │  │   │
│  │  [Box<Foo> val]     ptr───────┐  │  │  │   │
│  │                               │  │  │  │   │
│  │  ┌──────────┬──────────┬─────▼──▼──▼┐│   │
│  │  │ "hello"  │ [1,2,3]  │  Foo{..}   ││   │
│  │  └──────────┴──────────┴────────────┘│   │
│  │                                      │   │
│  └─────────────────────────────────────────┘   │
│  LOW ADDRESS                                    │
═══════════════════════════════════════════════════
```

**Stack characteristics:**
- Fixed size known at compile time
- LIFO (Last In First Out)
- Extremely fast allocation (just move stack pointer)
- Automatically freed when function returns
- Types stored here: `i32`, `f64`, `bool`, `char`, arrays, tuples of fixed-size types

**Heap characteristics:**
- Dynamic size, determined at runtime
- Allocated via OS/allocator (`malloc` equivalent)
- Must be explicitly freed (Rust: freed when owner drops)
- Slower allocation (allocator must find free block)
- Types stored here: `String`, `Vec<T>`, `Box<T>`, `HashMap`

**The Stack frame of a Heap-allocated value:**

```
STACK                          HEAP
┌──────────────────┐           ┌───────────────────────────┐
│  String s        │           │                           │
│  ┌────────────┐  │           │  h  e  l  l  o            │
│  │ ptr  ──────┼──┼──────────►│  0  1  2  3  4            │
│  │ len    5   │  │           │                           │
│  │ cap   10   │  │           └───────────────────────────┘
│  └────────────┘  │
└──────────────────┘

The String VALUE on the stack is 24 bytes (ptr + len + cap).
The STRING DATA on the heap is variable length.
```

```rust
fn memory_demo() {
    // Stack allocated — known size at compile time
    let x: i32 = 42;           // 4 bytes on stack
    let y: f64 = 3.14;         // 8 bytes on stack
    let arr: [i32; 3] = [1, 2, 3]; // 12 bytes on stack

    // Heap allocated — size determined at runtime
    let s = String::from("hello"); // 24 bytes on stack (ptr+len+cap)
                                   // + 5 bytes on heap
    let v: Vec<i32> = vec![1, 2, 3]; // 24 bytes on stack
                                      // + 12 bytes on heap

    println!("Stack value: {}", x);
    println!("Heap string: {}", s);

    // When this function returns:
    // - x, y, arr: popped off stack instantly
    // - s, v: drop() called → heap memory freed
}   // ← Rust inserts `drop(s); drop(v);` here automatically
```

**Why does this matter for interviews?**

Rust's ownership system is *specifically* designed to ensure heap-allocated memory is freed exactly once, at the right time. This is what replaces the garbage collector.

---

## 3. Ownership — The Core Mental Model

### Q: What is ownership in Rust? Explain the three rules.

**Answer:**

Ownership is Rust's most unique feature. It is a set of rules enforced at *compile time* that govern how memory is managed. There is no runtime cost.

**The Three Ownership Rules:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    OWNERSHIP RULES                              │
│                                                                 │
│  RULE 1: Each value in Rust has exactly ONE owner.             │
│          owner = variable that holds the value                  │
│                                                                 │
│  RULE 2: There can only be ONE owner at a time.                │
│          (unlike multiple pointers in C)                        │
│                                                                 │
│  RULE 3: When the owner goes out of scope,                     │
│          the value is dropped (memory freed).                   │
└─────────────────────────────────────────────────────────────────┘
```

**Visual: The Ownership Lifecycle**

```
fn main() {
    // ── SCOPE BEGINS ──────────────────────────────────
    {
        let s = String::from("hello");
        //  │
        //  └── s is OWNER of the String "hello"
        //
        //  HEAP:  [ h | e | l | l | o ]
        //  STACK: s → { ptr, len:5, cap:5 }
        //              └───────────────────►  heap data
        //
        //  s is VALID here
        println!("{}", s); // OK

    }   // ── SCOPE ENDS ──────────────────────────────────
        //  s goes OUT OF SCOPE
        //  Rust calls s.drop() automatically
        //  HEAP MEMORY FREED
        //  s is INVALID after this brace

    // println!("{}", s); // ← COMPILE ERROR: s not in scope
}
```

**What "scope" means:**

```rust
fn scope_demo() {
    // s1 does not exist here

    {
        let s1 = String::from("hello"); // s1 comes into scope
        println!("{}", s1);             // s1 is valid
    }                                   // s1 goes out of scope → DROPPED

    // s1 does not exist here — using it is a compile error

    let s2 = String::from("world"); // s2 comes into scope
    // s2 valid for rest of function

}   // s2 goes out of scope → DROPPED
```

**Why ONE owner matters:**

```
C (dangerous):                   Rust (safe):
                                 
ptr1 ──────────┐                 owner ──────────────► [data]
               ▼                   │
            [data]                 Only ONE arrow can point
               ▲                   and OWN the data.
ptr2 ──────────┘                   No double-free possible.

Problem: ptr1 frees data.         When owner goes out of scope,
         ptr2 now dangles.        drop() called ONCE. Guaranteed.
         ptr2 frees again.
         → DOUBLE FREE → crash
```

---

## 4. Move Semantics

### Q: What are move semantics? How does Rust handle assignment of heap-allocated types?

**Answer:**

When you assign a heap-allocated value to another variable, Rust *moves* ownership — it does NOT copy the heap data.

**Assignment in C++ (copies):**
```
s1 = "hello"       s2 = s1
STACK: s1 → ptr1   STACK: s1 → ptr1,  s2 → ptr2
HEAP:  [hello]     HEAP:  [hello] (ptr1), [hello] (ptr2) ← TWO copies
```

**Assignment in Rust (moves):**
```
BEFORE MOVE:              AFTER MOVE (s1 = s2):

STACK                     STACK
┌──────────────┐          ┌──────────────┐
│ s1           │          │ s1 (INVALID) │  ← compiler invalidates s1
│  ptr ───┐   │          │  ptr ─── ✗  │
│  len: 5 │   │          │  len: 5     │
│  cap: 5 │   │          │  cap: 5     │
└─────────┼───┘          ├──────────────┤
          │              │ s2           │
          │              │  ptr ───┐   │
HEAP      │              │  len: 5 │   │
┌─────────▼───┐          │  cap: 5 │   │
│ h e l l o  │          └─────────┼───┘
└─────────────┘                   │
                          HEAP    │
                          ┌───────▼─────┐
                          │ h e l l o  │
                          └─────────────┘
                          (SAME heap block, no copy)
```

```rust
fn move_demo() {
    let s1 = String::from("hello");
    let s2 = s1; // s1 is MOVED into s2
                 // s1 is no longer valid!

    // println!("{}", s1); // COMPILE ERROR: value borrowed after move
    println!("{}", s2);   // OK: s2 is the owner now

    // ─────────────────────────────────────────────
    // Move happens with function calls too:
    let s3 = String::from("world");
    takes_ownership(s3); // s3 MOVED into function
    // println!("{}", s3); // COMPILE ERROR: s3 was moved

    // ─────────────────────────────────────────────
    // To keep ownership, CLONE (deep copy):
    let s4 = String::from("original");
    let s5 = s4.clone(); // Deep copy of heap data
    println!("{} and {}", s4, s5); // Both valid!
}

fn takes_ownership(s: String) {
    println!("{}", s);
} // s is dropped here — heap freed
```

**Move in function return:**

```rust
fn gives_ownership() -> String {
    let s = String::from("hello"); // s is created
    s                              // s is MOVED out to the caller
}                                  // no drop here — moved out

fn takes_and_gives_back(s: String) -> String {
    s   // immediately moved back to caller
}

fn main() {
    let s1 = gives_ownership();        // owns the String
    let s2 = String::from("hi");
    let s3 = takes_and_gives_back(s2); // s2 moved in, returned as s3
    // s2 is invalid; s1 and s3 are valid
}
```

**The Clone distinction:**

```
MOVE:              No heap copy. Fast. Transfers ownership.
CLONE:             Full heap copy. Potentially slow. Both valid.
COPY (primitives): Bit-wise copy on stack. Both valid. (next section)
```

---

## 5. Copy Types vs Move Types

### Q: What is the `Copy` trait? Which types implement it and why?

**Answer:**

The `Copy` trait marks types that can be safely duplicated by just copying bits — no heap involvement needed.

```
┌─────────────────────────────────────────────────────────────┐
│                  COPY vs MOVE TYPES                         │
│                                                             │
│  COPY (stack-only, fixed size):                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  i8, i16, i32, i64, i128, isize                      │  │
│  │  u8, u16, u32, u64, u128, usize                      │  │
│  │  f32, f64                                            │  │
│  │  bool                                                │  │
│  │  char                                                │  │
│  │  Tuples/arrays of Copy types: (i32, f64), [u8; 4]   │  │
│  │  References: &T  (the reference itself, not the T)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  MOVE (heap-involved, or explicitly non-Copy):              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  String                                              │  │
│  │  Vec<T>                                              │  │
│  │  HashMap<K, V>                                       │  │
│  │  Box<T>                                              │  │
│  │  Any struct/enum that contains a Move type           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

```rust
fn copy_vs_move() {
    // ── COPY TYPES ──────────────────────────────────────────
    let x: i32 = 5;
    let y = x;              // COPY: x's bits duplicated
    println!("{} {}", x, y); // Both valid! x=5, y=5

    let a: bool = true;
    let b = a;              // COPY
    println!("{} {}", a, b); // Both valid

    let t: (i32, f64) = (1, 2.0);
    let t2 = t;             // COPY (both elements are Copy)
    println!("{:?} {:?}", t, t2); // Both valid

    // ── MOVE TYPES ──────────────────────────────────────────
    let s1 = String::from("hello");
    let s2 = s1;            // MOVE: s1 invalidated
    // println!("{}", s1);  // ERROR: value moved

    // ── CUSTOM COPY TYPE ─────────────────────────────────────
    #[derive(Debug, Copy, Clone)]
    struct Point {
        x: f64,
        y: f64,
    }
    // Both fields are f64 (Copy), so Point can be Copy

    let p1 = Point { x: 1.0, y: 2.0 };
    let p2 = p1; // COPY (not move)
    println!("{:?} {:?}", p1, p2); // Both valid!

    // ── WHY can't String be Copy? ────────────────────────────
    // If String were Copy:
    //   let s1 = String::from("hello");
    //   let s2 = s1;  // s1 and s2 both own heap data
    //   // BOTH would call drop() → DOUBLE FREE!
    // That's why heap types can NEVER implement Copy.
}
```

**Key rule for interviews:**
> If a type implements `Copy`, assignment creates a duplicate.  
> If a type does NOT implement `Copy`, assignment is a move.  
> You cannot implement both `Copy` and `Drop` on the same type.

---

## 6. Borrowing & References

### Q: What is borrowing? What are the rules of references?

**Answer:**

Borrowing allows you to *use* a value without taking ownership. This is done via *references* (`&`).

**The analogy:** Ownership is owning a book. Borrowing is lending it — the owner still owns it; the borrower just reads (or writes) it temporarily.

```
WITHOUT BORROWING (clunky):           WITH BORROWING (clean):

fn calc_len(s: String) -> (String, usize) {   fn calc_len(s: &String) -> usize {
    let len = s.len();                              s.len()
    (s, len)  // must return s to keep it       }
}
                                              fn main() {
fn main() {                                       let s = String::from("hello");
    let s = String::from("hello");                let len = calc_len(&s);
    let (s, len) = calc_len(s);                   // s still valid here!
    println!("{} has length {}", s, len);          println!("{} len={}", s, len);
}                                             }
```

**Reference visualization:**

```
IMMUTABLE REFERENCE &String

fn main() {
    let s = String::from("hello");
    let r = &s;
    //  │     │
    //  │     └── reference to s (borrows s)
    //  └── still owns the String

    STACK:
    ┌────────────┐       ┌────────────┐       HEAP:
    │     s      │       │     r      │    ┌────────────┐
    │  ptr ──────┼──────►│  ptr ──────┼───►│ h e l l o │
    │  len: 5    │       └────────────┘    └────────────┘
    │  cap: 5    │
    └────────────┘
    (owner)              (reference — points to s, not heap directly)
}
```

**The Two Reference Rules:**

```
┌─────────────────────────────────────────────────────────────────┐
│              BORROWING RULES (enforced at compile time)         │
│                                                                 │
│  At any given time, you can have EITHER:                        │
│                                                                 │
│   Option A:  ONE mutable reference      &mut T                 │
│                                                                 │
│                    OR                                           │
│                                                                 │
│   Option B:  ANY NUMBER of immutable references   &T           │
│                                                                 │
│  NEVER BOTH at the same time.                                   │
│                                                                 │
│  PLUS: References must always be valid (no dangling refs)       │
└─────────────────────────────────────────────────────────────────┘
```

```rust
fn borrowing_rules() {
    let mut s = String::from("hello");

    // ── IMMUTABLE REFERENCES (can have many) ─────────────────
    let r1 = &s;
    let r2 = &s;
    let r3 = &s;
    println!("{} {} {}", r1, r2, r3); // OK: all immutable

    // ── MUTABLE REFERENCE (only one at a time) ───────────────
    let r4 = &mut s;
    r4.push_str(" world");
    // let r5 = &mut s; // ERROR: cannot borrow s as mutable more than once

    // ── CANNOT MIX mutable + immutable ───────────────────────
    let r6 = &s;
    // let r7 = &mut s; // ERROR: cannot borrow as mutable because
                         // r6 (immutable) is still active

    println!("{}", r6);
    // After this point, r6 is no longer used
    // Now r7 can exist (NLL — Non-Lexical Lifetimes)

    let r7 = &mut s; // OK now: r6 no longer in use
    r7.push_str("!");
    println!("{}", r7);
}
```

**Why these rules prevent data races:**

```
DATA RACE requires THREE conditions:
1. Two+ pointers accessing same data
2. At least one is writing
3. No synchronization

Rust's rules break condition 2 + 3:
 - If you have &mut, no one else can read OR write  → no race
 - If you have &, everyone reads, no one writes     → no race
```

**Mutable reference in detail:**

```rust
fn mutable_ref_demo() {
    let mut s = String::from("hello");

    change(&mut s); // pass mutable reference
    println!("{}", s); // "hello, world"
}

fn change(s: &mut String) {
    s.push_str(", world");
    // s here is &mut String
    // we can modify what s points to
    // but s itself goes out of scope when function ends
    // the OWNER (in main) is unaffected in terms of ownership
}
```

---

## 7. The Borrow Checker

### Q: What is the borrow checker? How does it work?

**Answer:**

The borrow checker is a component of the Rust compiler (`rustc`) that enforces the ownership and borrowing rules at compile time. It analyzes your code's control flow and proves that all memory accesses are valid.

```
┌───────────────────────────────────────────────────────────────┐
│                   RUST COMPILER PIPELINE                      │
│                                                               │
│  Source Code                                                  │
│      │                                                        │
│      ▼                                                        │
│  ┌──────────┐                                                 │
│  │  Lexer   │  → tokens                                       │
│  └──────────┘                                                 │
│      │                                                        │
│      ▼                                                        │
│  ┌──────────┐                                                 │
│  │  Parser  │  → AST (Abstract Syntax Tree)                   │
│  └──────────┘                                                 │
│      │                                                        │
│      ▼                                                        │
│  ┌──────────────────────────────────────────┐                │
│  │         BORROW CHECKER  ◄── HERE         │                │
│  │                                          │                │
│  │  1. Tracks ownership for every value     │                │
│  │  2. Tracks lifetimes of every reference  │                │
│  │  3. Verifies borrowing rules hold        │                │
│  │  4. Ensures no use-after-free            │                │
│  │  5. Ensures no double-free               │                │
│  │  6. Ensures no data races                │                │
│  └──────────────────────────────────────────┘                │
│      │                                                        │
│      ▼                                                        │
│  ┌──────────┐                                                 │
│  │  MIR     │  → Mid-level IR (further optimization)         │
│  │  (LLVM)  │                                                 │
│  └──────────┘                                                 │
│      │                                                        │
│      ▼                                                        │
│  Machine Code (safe, no runtime overhead)                     │
└───────────────────────────────────────────────────────────────┘
```

**What the borrow checker catches:**

```rust
// EXAMPLE 1: Use after free (prevented at compile time)
fn use_after_free() {
    let r;
    {
        let x = 5;
        r = &x;     // ERROR: x does not live long enough
                    // x dropped at }, r would dangle
    }
    println!("{}", r); // would be use-after-free in C
}

// EXAMPLE 2: Double move (prevented)
fn double_move() {
    let s = String::from("hello");
    let t = s;         // s moved to t
    let u = s;         // ERROR: s was already moved
}

// EXAMPLE 3: Dangling reference (prevented)
fn dangle() -> &String {  // ERROR: return reference to local
    let s = String::from("hello");
    &s  // s is dropped at }, &s would dangle
}   // s dropped here

// EXAMPLE 4: Mutation while borrowed (prevented)
fn mutation_while_borrowed() {
    let mut v = vec![1, 2, 3];
    let first = &v[0]; // immutable borrow of v
    v.push(4);         // ERROR: mutable borrow while immutable exists
                       // push could reallocate → first would dangle
    println!("{}", first);
}
```

**NLL — Non-Lexical Lifetimes (Rust 2018+):**

Before NLL, the borrow checker used *lexical* scope for reference lifetimes. Now it's smarter:

```rust
fn nll_demo() {
    let mut s = String::from("hello");

    let r1 = &s;            // immutable borrow starts
    println!("{}", r1);     // last use of r1
    // r1's lifetime ENDS here (NLL: last use, not end of block)

    let r2 = &mut s;        // OK! r1 is no longer "alive"
    r2.push_str(" world");
    println!("{}", r2);
}
// Before NLL (Rust 2015), the mutable borrow would ERROR
// because r1's lexical scope extended to end of function.
```

---

## 8. Lifetimes

### Q: What are lifetimes in Rust? Why are they needed?

**Answer:**

Lifetimes are the borrow checker's way of tracking *how long* references are valid. They are usually inferred, but sometimes you need to annotate them explicitly to help the compiler understand relationships between reference lifetimes.

**Core concept — lifetimes prevent dangling references:**

```
DANGLING REFERENCE (what lifetimes prevent):

fn bad() -> &i32 {      STACK during bad():
    let x = 5;          ┌──────────────┐
    &x                  │  x = 5       │◄── x lives here
}   // x DROPPED        └──────────────┘
                                ↑ x is gone
// caller holds &i32 pointing to freed memory!

WITH LIFETIME ANNOTATION:
fn bad<'a>() -> &'a i32 {
    let x = 5;
    &x   // ERROR: x does not live as long as 'a
}
// Compiler says: the returned reference's lifetime 'a
// must be at least as long as the caller's scope.
// But x is local — it can't satisfy that.
```

**Lifetime annotation syntax:**

```rust
// Without lifetime annotation (compiler may reject):
fn longest(x: &str, y: &str) -> &str {
    if x.len() > y.len() { x } else { y }
    // ERROR: compiler doesn't know if returned ref is
    // from x or y — can't verify it stays valid
}

// With lifetime annotation:
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    //      ^^^                                ^^^
    //  Declare lifetime 'a
    //  Both inputs share lifetime 'a
    //  Output lives AT LEAST as long as 'a
    if x.len() > y.len() { x } else { y }
}
```

**What `'a` means (annotated):**

```
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str

'a is NOT a concrete time. It's a CONSTRAINT:
"The returned reference will be valid for as long as
 BOTH x AND y are valid."

In practice: 'a = min(lifetime of x, lifetime of y)

EXAMPLE:
    let s1 = String::from("long string");      // 'lifetime_s1
    {
        let s2 = String::from("xy");           // 'lifetime_s2
        let result = longest(&s1, &s2);        // 'a = min('s1, 's2) = 's2
        println!("{}", result);                // OK: result used inside 's2
    }
    // println!("{}", result); // ERROR: result might point to s2 which is gone
```

**Lifetimes in structs:**

```rust
// If a struct holds a reference, it needs a lifetime:
struct Important<'a> {
    part: &'a str,  // this reference must outlive the struct
}

fn struct_lifetime() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence;
    {
        let i = novel.split('.').next().expect("Could not find '.'");
        first_sentence = Important { part: i };
        // i borrows from novel, which lives longer → OK
    }
    println!("{}", first_sentence.part);
}
```

**Lifetime elision rules (when you DON'T need to annotate):**

```
The compiler applies these rules automatically:

RULE 1: Each reference parameter gets its own lifetime.
        fn foo(x: &i32)           → fn foo<'a>(x: &'a i32)
        fn foo(x: &i32, y: &i32)  → fn foo<'a, 'b>(x: &'a i32, y: &'b i32)

RULE 2: If there's exactly one input lifetime, it's assigned to all outputs.
        fn foo(x: &i32) -> &i32   → fn foo<'a>(x: &'a i32) -> &'a i32

RULE 3: If one of the inputs is &self or &mut self, the self lifetime
        is assigned to all output lifetimes.
        (Most method return references.)

If rules don't resolve ambiguity → compile error → you must annotate.
```

**The `'static` lifetime:**

```rust
// 'static means the reference lives for the entire program duration
let s: &'static str = "I am static"; // string literals are 'static
// The data lives in the binary itself — always valid.

// Common use: trait objects, thread-spawned closures
// fn always_valid() -> &'static str { "hello" } // OK
```

---

## 9. Slices

### Q: What are slices in Rust? How do they differ from arrays or Vecs?

**Answer:**

A slice is a *view* into a contiguous sequence of elements. It's a reference with a length — it doesn't own the data.

```
ARRAY/VEC on stack/heap:        SLICE (view into it):

[1, 2, 3, 4, 5]                 &arr[1..4]
 0  1  2  3  4                        ↕
                                 [2, 3, 4]

Slice = (pointer to start, length)

MEMORY:
┌───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 4 │ 5 │   ← array data (owned)
└───┴───┴───┴───┴───┘
      ▲
      │
  ┌───┴──────┐
  │ ptr      │  ← slice (fat pointer)
  │ len: 3   │
  └──────────┘
  &arr[1..4]
```

```rust
fn slice_demo() {
    // ── Array slice ───────────────────────────────────────
    let arr = [1, 2, 3, 4, 5];
    let slice: &[i32] = &arr[1..4]; // elements at index 1, 2, 3
    println!("{:?}", slice);         // [2, 3, 4]

    // Slice does NOT copy data — it's a reference to arr's data
    // arr is still the owner

    // ── String slice ──────────────────────────────────────
    let s = String::from("hello world");
    let hello: &str = &s[0..5];   // "hello"
    let world: &str = &s[6..11];  // "world"
    // &str is a string slice — (ptr, len) into string data
    println!("{} {}", hello, world);

    // ── String literals are slices ────────────────────────
    let literal: &str = "I am a literal";
    // &str pointing into the binary's read-only data segment

    // ── Vec slice ─────────────────────────────────────────
    let v = vec![10, 20, 30, 40, 50];
    let mid: &[i32] = &v[1..4];  // [20, 30, 40]
    println!("{:?}", mid);

    // ── Full slice (entire collection) ────────────────────
    let full: &[i32] = &arr[..]; // same as &arr[0..5]
    println!("{:?}", full);

    // ── First word example (why slices matter) ────────────
    let sentence = String::from("hello world");
    let word = first_word(&sentence);
    // sentence.clear(); // ERROR: can't mutate while word borrows it
    println!("First word: {}", word);
}

fn first_word(s: &str) -> &str {
    let bytes = s.as_bytes();
    for (i, &byte) in bytes.iter().enumerate() {
        if byte == b' ' {
            return &s[0..i];
        }
    }
    &s[..]  // entire string if no space found
}
```

**Why `&str` instead of `&String`?**

```rust
// Less flexible:
fn takes_string_ref(s: &String) { ... }

// More flexible (preferred):
fn takes_str(s: &str) { ... }
// &str accepts: &String (auto-derefs), &str literals, string slices
// This is called "deref coercion" — &String → &str automatically
```

---

## 10. Data Types: Scalar Types

### Q: What are Rust's primitive/scalar types?

**Answer:**

Scalar types represent a single value. Rust has four kinds:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCALAR TYPES                                   │
│                                                                     │
│  ┌─────────────┬──────────────────────────────────────────────┐    │
│  │  INTEGERS   │                                              │    │
│  │             │  Signed:   i8  i16  i32  i64  i128  isize   │    │
│  │             │  Unsigned: u8  u16  u32  u64  u128  usize   │    │
│  │             │                                              │    │
│  │             │  i8:  -128 to 127                           │    │
│  │             │  u8:  0 to 255                              │    │
│  │             │  i32: -2,147,483,648 to 2,147,483,647       │    │
│  │             │  Default: i32                               │    │
│  │             │  isize/usize: pointer-sized (64-bit on x64) │    │
│  ├─────────────┼──────────────────────────────────────────────┤    │
│  │  FLOATS     │  f32  f64                                   │    │
│  │             │  Default: f64 (more precision)              │    │
│  │             │  IEEE 754 standard                          │    │
│  ├─────────────┼──────────────────────────────────────────────┤    │
│  │  BOOLEAN    │  bool: true | false  (1 byte)               │    │
│  ├─────────────┼──────────────────────────────────────────────┤    │
│  │  CHARACTER  │  char: Unicode scalar value (4 bytes)       │    │
│  │             │  'a', '🦀', '中'  — NOT a byte             │    │
│  └─────────────┴──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

```rust
fn scalar_types() {
    // ── Integers ─────────────────────────────────────────────
    let a: i32 = -42;
    let b: u64 = 1_000_000; // underscores for readability
    let c: u8  = 0xFF;      // hex literal
    let d: u8  = 0b1111_0000; // binary literal
    let e: u8  = 0o77;      // octal literal
    let f: i32 = 42;        // default integer type

    // Integer overflow:
    // In debug mode:   panic at runtime
    // In release mode: wraps (two's complement)
    // Use wrapping_add, checked_add, saturating_add for explicit control
    let max = u8::MAX;  // 255
    let wrapped = max.wrapping_add(1); // 0 (wraps)
    let checked = max.checked_add(1);  // None (overflow detected)
    let saturated = max.saturating_add(1); // 255 (stays at max)

    // ── Floats ───────────────────────────────────────────────
    let x: f64 = 3.14;
    let y: f32 = 2.0_f32;
    // Floating point arithmetic:
    let z = x + 1.0; // 4.14
    // Warning: f64 ≠ exact decimal: 0.1 + 0.2 ≠ 0.3

    // ── Boolean ──────────────────────────────────────────────
    let t: bool = true;
    let f: bool = false;
    let result = t && f;  // false
    let result2 = t || f; // true
    let result3 = !t;     // false

    // ── Character ────────────────────────────────────────────
    let c1: char = 'a';
    let c2: char = '🦀'; // 4 bytes! Not 1 byte like C's char
    let c3: char = '中';
    println!("{} {} {}", c1, c2, c3);

    // char ≠ u8: char is a Unicode scalar, u8 is a byte
    let byte: u8 = b'A'; // byte literal — only for ASCII
    println!("byte: {}", byte); // 65
}
```

**Integer type selection guide:**

```
Use i32 as default integer (CPU-native, fast).
Use usize for indexing and collection sizes (platform-sized).
Use i64 when you need large values.
Use u8 for byte manipulation.
Use i8/i16/u16 for FFI/protocols where size matters.
```

---

## 11. Data Types: Compound Types (Tuples & Arrays)

### Q: What are tuples and arrays in Rust?

**Answer:**

Compound types group multiple values into one.

### Tuples

```
TUPLE: Fixed length, elements can be different types.
       Stored entirely on the stack.

let t = (1, "hello", 3.14);
         │    │         │
         i32  &str     f64

MEMORY (stack):
┌─────────┬──────────────────┬──────────┐
│  1(i32) │  "hello"(&str)   │ 3.14(f64)│
│  4 bytes│  16 bytes        │  8 bytes │
└─────────┴──────────────────┴──────────┘
total: 28 bytes (with possible padding)
```

```rust
fn tuple_demo() {
    // ── Declaration ──────────────────────────────────────────
    let t: (i32, f64, &str) = (42, 3.14, "hello");

    // ── Access by index ──────────────────────────────────────
    println!("{}", t.0); // 42
    println!("{}", t.1); // 3.14
    println!("{}", t.2); // hello

    // ── Destructuring ─────────────────────────────────────────
    let (x, y, z) = t;
    println!("{} {} {}", x, y, z);

    // ── Unit tuple () ─────────────────────────────────────────
    // () is the unit type — represents "nothing"
    // Functions without explicit return return ()
    let unit: () = ();
    // fn do_nothing() -> () { }  // same as fn do_nothing() { }

    // ── Tuples as return values ───────────────────────────────
    fn min_max(v: &[i32]) -> (i32, i32) {
        let mut min = v[0];
        let mut max = v[0];
        for &n in v {
            if n < min { min = n; }
            if n > max { max = n; }
        }
        (min, max)
    }

    let (lo, hi) = min_max(&[3, 1, 4, 1, 5, 9]);
    println!("min={}, max={}", lo, hi); // min=1, max=9
}
```

### Arrays

```
ARRAY: Fixed length, all elements SAME type.
       Always stack-allocated.
       Type: [T; N] where N is part of the type.

let arr: [i32; 5] = [1, 2, 3, 4, 5];

MEMORY (stack):
┌─────┬─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  4  │  5  │
│ i32 │ i32 │ i32 │ i32 │ i32 │
│4 B  │ 4 B │ 4 B │ 4 B │ 4 B │
└─────┴─────┴─────┴─────┴─────┘
total: 20 bytes, contiguous
```

```rust
fn array_demo() {
    // ── Declaration ──────────────────────────────────────────
    let a: [i32; 5] = [1, 2, 3, 4, 5];
    let b = [3; 5];  // [3, 3, 3, 3, 3] — fill with 3

    // ── Access ───────────────────────────────────────────────
    println!("{}", a[0]); // 1 (zero-indexed)
    println!("{}", a[4]); // 5

    // ── Bounds checking: Rust panics at runtime (not UB like C) ──
    // a[5]; // PANIC: index out of bounds: the len is 5 but the index is 5

    // ── Length ───────────────────────────────────────────────
    println!("length: {}", a.len()); // 5

    // ── Iteration ────────────────────────────────────────────
    for element in &a {
        print!("{} ", element); // 1 2 3 4 5
    }

    // ── [T; N] is part of the TYPE ───────────────────────────
    let arr5: [i32; 5] = [0; 5];
    let arr3: [i32; 3] = [0; 3];
    // arr5 and arr3 are DIFFERENT TYPES! Can't mix them.
    // fn takes_5(a: [i32; 5]) vs fn takes_3(a: [i32; 3])

    // Use slices &[i32] for functions accepting any length:
    fn sum(arr: &[i32]) -> i32 {
        arr.iter().sum()
    }
    println!("{}", sum(&arr5)); // works with any length
    println!("{}", sum(&arr3)); // works with any length
}
```

**Array vs Vec:**

```
Array [T; N]:           Vec<T>:
- Fixed size (compile)  - Dynamic size (runtime)
- Stack allocated       - Heap allocated
- Size is part of type  - Size flexible
- Fast, no allocation   - Allocation overhead
- Use when: size known, - Use when: size varies,
  small, temporary        long-lived data
```

---

## 12. Variables, Mutability & Shadowing

### Q: Explain `let`, `mut`, `const`, and shadowing in Rust.

**Answer:**

Rust variables are immutable by default — a deliberate choice to make code safer and easier to reason about.

```
MUTABILITY MODEL:

let x = 5;          → IMMUTABLE binding. Cannot change x.
let mut x = 5;      → MUTABLE binding. Can change x.
const X: i32 = 5;   → CONSTANT. Truly immutable, no runtime address.
static X: i32 = 5;  → STATIC. Lives for entire program, has address.
```

```rust
fn variables_demo() {
    // ── Immutable (default) ───────────────────────────────────
    let x = 5;
    // x = 6; // ERROR: cannot assign twice to immutable variable

    // ── Mutable ───────────────────────────────────────────────
    let mut y = 5;
    y = 6; // OK
    y += 1; // OK: y is now 7

    // ── Constants ────────────────────────────────────────────
    // Must be type-annotated
    // Must be a constant expression (known at compile time)
    // Convention: SCREAMING_SNAKE_CASE
    // Can be declared in any scope, including global
    const MAX_POINTS: u32 = 100_000;
    const PI: f64 = 3.14159265358979;

    // ── Statics ──────────────────────────────────────────────
    // Like constants but have a fixed memory address
    // Can be mutable (but requires unsafe)
    static GREETING: &str = "Hello, World!";
    println!("{}", GREETING);

    // ── Why immutability by default? ─────────────────────────
    // 1. Easier to reason about: value doesn't change unexpectedly
    // 2. Enables compiler optimizations
    // 3. Documents intent: "this should never change"
    // 4. Makes concurrency safer
}
```

**Shadowing:**

Shadowing is reassigning the name to a NEW variable — different from mutability.

```rust
fn shadowing_demo() {
    let x = 5;
    let x = x + 1; // NEW x shadows old x
    let x = x * 2; // NEW x shadows again
    println!("{}", x); // 12

    // Shadowing allows changing TYPE:
    let spaces = "   ";       // &str
    let spaces = spaces.len(); // usize — shadowed with different type!
    println!("{}", spaces); // 3

    // This is DIFFERENT from mut:
    let mut spaces = "   ";
    // spaces = spaces.len(); // ERROR: can't change type with mut

    // ── Shadowing in inner scope ──────────────────────────────
    let y = 10;
    {
        let y = y * 2;    // inner y shadows outer y
        println!("{}", y); // 20
    }
    println!("{}", y); // 10 — outer y unchanged!

    // ── Common shadowing pattern: parsing ────────────────────
    let guess = "42";           // &str from input
    let guess: i32 = guess.parse().unwrap(); // shadow with parsed type
    println!("{}", guess + 1);  // 43
}
```

**`const` vs `static` vs `let`:**

```
┌────────────┬──────────────┬────────────────┬─────────────────┐
│            │  let         │  const         │  static         │
├────────────┼──────────────┼────────────────┼─────────────────┤
│ Scope      │ Local        │ Any            │ Global/Local    │
│ Mutable?   │ With mut     │ Never          │ With unsafe mut │
│ Type       │ Inferred OK  │ Must annotate  │ Must annotate   │
│ Eval time  │ Runtime      │ Compile time   │ Compile time    │
│ Inlining   │ No           │ Yes (inlined)  │ Has address     │
│ Lifetime   │ Scope        │ 'static        │ 'static         │
└────────────┴──────────────┴────────────────┴─────────────────┘
```

---

## 13. Functions & Return Values

### Q: How do functions work in Rust? Explain expressions vs statements.

**Answer:**

**Statements vs Expressions — the most important distinction:**

```
STATEMENT: performs an action, does NOT return a value.
           Ends with a semicolon.

EXPRESSION: evaluates to a VALUE.
            Does NOT end with a semicolon.

This distinction is fundamental to how Rust functions work.
```

```rust
fn expression_vs_statement() {
    // ── STATEMENTS (do something, return nothing) ─────────────
    let x = 5;          // let statement (binding)
    let y = (let z = 6); // ERROR: let is not an expression!

    // ── EXPRESSIONS (produce a value) ─────────────────────────
    5          // expression: value 5
    5 + 6      // expression: value 11
    {           // BLOCK is an expression!
        let a = 3;
        a + 1   // ← NO semicolon: last expression is block's value
    }           // this block evaluates to 4

    // ── If is an expression ───────────────────────────────────
    let condition = true;
    let number = if condition { 5 } else { 6 };
    // Both arms must return same type!
    println!("{}", number); // 5

    // ── Function return ───────────────────────────────────────
    // Rust functions return the LAST EXPRESSION (no semicolon)
    // OR you can use explicit `return`
}

fn five() -> i32 {
    5   // expression — returned. No `return` needed.
}

fn plus_one(x: i32) -> i32 {
    x + 1  // expression — returned
    // x + 1; // with semicolon → statement → function returns ()
              // this would cause a type mismatch error!
}

fn explicit_return(x: i32) -> i32 {
    if x < 0 {
        return 0; // early return with explicit keyword
    }
    x * 2  // implicit return
}
```

**Function anatomy:**

```
fn function_name(param1: Type1, param2: Type2) -> ReturnType {
│                │              │                 │
│                └──────────────┘                 │
│                Parameters must be type-annotated│
│                                                 │
└── keyword                          Return type ─┘
                                     Omit if returns ()

fn add(a: i32, b: i32) -> i32 {
    a + b   ← implicit return (no semicolon)
}
```

```rust
fn function_features() {
    // ── Basic function ───────────────────────────────────────
    fn add(a: i32, b: i32) -> i32 { a + b }
    println!("{}", add(3, 4)); // 7

    // ── No return value (returns unit ()) ────────────────────
    fn print_hello() {
        println!("Hello!");
    } // implicitly returns ()

    // ── Multiple return values via tuple ─────────────────────
    fn swap(a: i32, b: i32) -> (i32, i32) {
        (b, a)
    }
    let (x, y) = swap(1, 2);
    println!("{} {}", x, y); // 2 1

    // ── Diverging functions — never return ───────────────────
    fn forever() -> ! {
        loop {}  // ! means "never returns"
    }
    // Also: panic!(), std::process::exit(), etc. return !

    // ── Functions are first-class ─────────────────────────────
    fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
        f(x)
    }
    fn double(x: i32) -> i32 { x * 2 }
    println!("{}", apply(double, 5)); // 10
}
```

---

## 14. Control Flow

### Q: Explain all control flow constructs in Rust.

**Answer:**

### `if` / `else if` / `else`

```rust
fn if_demo() {
    let n = 7;

    // Basic if-else
    if n < 5 {
        println!("less than 5");
    } else if n == 5 {
        println!("equals 5");
    } else {
        println!("greater than 5");
    }

    // if as an expression (must have matching types):
    let desc = if n % 2 == 0 { "even" } else { "odd" };
    println!("{} is {}", n, desc);

    // Used in let:
    let abs = if n < 0 { -n } else { n };
}
```

### Loops

```rust
fn loop_demo() {
    // ── `loop` — infinite loop ────────────────────────────────
    let mut counter = 0;
    let result = loop {
        counter += 1;
        if counter == 10 {
            break counter * 2; // loop can RETURN a value!
        }
    };
    println!("result: {}", result); // 20

    // ── `while` ───────────────────────────────────────────────
    let mut n = 3;
    while n != 0 {
        println!("{}!", n);
        n -= 1;
    }

    // ── `for` — most common loop ──────────────────────────────
    // Iterating over a range:
    for i in 0..5 {
        print!("{} ", i); // 0 1 2 3 4
    }
    for i in 0..=5 {       // inclusive: 0 1 2 3 4 5
        print!("{} ", i);
    }

    // Iterating over a collection:
    let arr = [10, 20, 30, 40, 50];
    for element in &arr {        // borrow each element
        print!("{} ", element);
    }
    for (i, v) in arr.iter().enumerate() { // with index
        println!("[{}] = {}", i, v);
    }

    // ── Loop labels (for nested loop break/continue) ──────────
    'outer: for x in 0..5 {
        for y in 0..5 {
            if x == 2 && y == 2 {
                break 'outer; // breaks the OUTER loop
            }
            print!("({},{}) ", x, y);
        }
    }
}
```

**Loop control flow diagram:**

```
LOOP TYPES:

loop { ... }             while condition { ... }      for x in iter { ... }
┌─────────────────┐      ┌──────────────────────┐     ┌──────────────────────┐
│  ┌──────────┐   │      │  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │  body    │   │      │  │ check condition│  │     │  │ get next item  │  │
│  │          │   │      │  └───────┬────────┘  │     │  └───────┬────────┘  │
│  └────┬─────┘   │      │  false   │  true     │     │  None    │  Some(x)  │
│       │ break   │      │  ────►EXIT  ─────►   │     │  ────►EXIT  ─────►   │
│       │ ──►EXIT │      │         ┌──────────┐ │     │         ┌──────────┐ │
│       │ continue│      │         │  body    │ │     │         │  body    │ │
│       └──────┐  │      │         └────┬─────┘ │     │         └────┬─────┘ │
│              └──┘      │         continue     │     │         continue     │
└─────────────────┘      └──────────────────────┘     └──────────────────────┘
Can return value         Condition checked first       Uses Iterator protocol
```

---

## 15. Structs

### Q: What are structs in Rust? What are the different kinds?

**Answer:**

Structs are custom data types that group related data together.

### Three Kinds of Structs

```rust
// ── 1. Named-field struct ─────────────────────────────────────
struct User {
    username: String,
    email: String,
    age: u32,
    active: bool,
}

// ── 2. Tuple struct ──────────────────────────────────────────
struct Color(u8, u8, u8);       // RGB
struct Point(f64, f64, f64);    // X, Y, Z
// Different types even though same structure!

// ── 3. Unit struct (marker) ──────────────────────────────────
struct AlwaysEqual;
// No fields. Used as markers, for trait implementations.
```

**Struct memory layout:**

```
struct User {
    username: String,    // 24 bytes (ptr + len + cap)
    email: String,       // 24 bytes
    age: u32,            //  4 bytes
    active: bool,        //  1 byte + 3 padding bytes
}

STACK layout of User instance:
┌─────────────────────────┐
│ username: ptr,len,cap   │  24 bytes
├─────────────────────────┤
│ email: ptr,len,cap      │  24 bytes
├─────────────────────────┤
│ age: u32                │   4 bytes
├─────────────────────────┤
│ active: bool            │   1 byte
│ padding                 │   3 bytes
└─────────────────────────┘
total: 56 bytes on stack
       + heap for username + email strings
```

```rust
fn struct_demo() {
    // ── Creating an instance ─────────────────────────────────
    let user1 = User {
        username: String::from("alice"),
        email: String::from("alice@example.com"),
        age: 30,
        active: true,
    };

    // ── Access fields ────────────────────────────────────────
    println!("{}", user1.username);
    println!("{}", user1.age);

    // ── Mutable struct (entire struct must be mut) ────────────
    let mut user2 = User {
        username: String::from("bob"),
        email: String::from("bob@example.com"),
        age: 25,
        active: false,
    };
    user2.email = String::from("bob@new.com"); // modify field
    // Can't make individual fields mut — entire struct is mut or not

    // ── Struct update syntax ──────────────────────────────────
    let user3 = User {
        email: String::from("charlie@example.com"),
        ..user1  // remaining fields from user1
        // NOTE: user1's String fields are MOVED into user3!
        // user1.username is moved. user1 can't be used after this
        // (unless only Copy fields were used in ..)
    };

    // ── Field init shorthand ──────────────────────────────────
    fn build_user(username: String, email: String) -> User {
        User {
            username,   // shorthand: username: username
            email,      // shorthand: email: email
            age: 0,
            active: true,
        }
    }

    // ── Tuple struct ─────────────────────────────────────────
    let red = Color(255, 0, 0);
    let origin = Point(0.0, 0.0, 0.0);
    println!("Red: {}, {}, {}", red.0, red.1, red.2);
    // Color and Point are different types even with same structure!

    // ── Unit struct ──────────────────────────────────────────
    let _marker = AlwaysEqual;
}
```

### Methods on Structs

```rust
struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    // ── Associated function (like a static method) ──────────
    // Called: Rectangle::new(...)
    fn new(width: f64, height: f64) -> Self {
        Rectangle { width, height }
    }

    // ── Method — takes &self (immutable reference to self) ──
    fn area(&self) -> f64 {
        self.width * self.height
    }

    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }

    fn is_square(&self) -> bool {
        self.width == self.height
    }

    // ── Mutable method — takes &mut self ───────────────────
    fn scale(&mut self, factor: f64) {
        self.width *= factor;
        self.height *= factor;
    }

    // ── Consuming method — takes self (moves it) ────────────
    fn into_square(self) -> Rectangle {
        let side = self.width.min(self.height);
        Rectangle { width: side, height: side }
    }

    // ── Method that takes another instance ──────────────────
    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
}

fn methods_demo() {
    let mut r = Rectangle::new(10.0, 5.0);
    println!("Area: {}", r.area());         // 50.0
    println!("Is square: {}", r.is_square()); // false
    r.scale(2.0);
    println!("Scaled area: {}", r.area());  // 200.0

    let small = Rectangle::new(3.0, 2.0);
    println!("r can hold small: {}", r.can_hold(&small)); // true
}
```

**`impl` blocks and `self`:**

```
&self      → borrows self immutably (read-only method)
&mut self  → borrows self mutably (modifying method)
self       → takes ownership of self (consuming method, rare)

Multiple impl blocks for same struct are allowed.
Useful for organization or conditional compilation.
```

---

## 16. Enums

### Q: What are enums in Rust and why are they more powerful than in other languages?

**Answer:**

Rust enums are algebraic data types — each variant can carry different data. They're far more powerful than C/Java enums.

```
C/Java enum:                 Rust enum:
enum Direction {             enum Shape {
    North,                       Circle(f64),          // carries radius
    South,                       Rectangle(f64, f64),  // carries w, h
    East,                        Triangle { base: f64, height: f64 },
    West,                        Point,                // no data
}                            }
Only names. No data.         Each variant can have DIFFERENT data.
```

```rust
// ── Basic enum ────────────────────────────────────────────────
#[derive(Debug)]
enum Direction {
    North,
    South,
    East,
    West,
}

// ── Enum with data ────────────────────────────────────────────
#[derive(Debug)]
enum Message {
    Quit,                       // no data
    Move { x: i32, y: i32 },   // named fields (like a struct)
    Write(String),              // single String
    ChangeColor(u8, u8, u8),    // three values (tuple-like)
}

// ── Methods on enums ─────────────────────────────────────────
impl Message {
    fn call(&self) {
        match self {
            Message::Quit => println!("Quit"),
            Message::Move { x, y } => println!("Move to {},{}", x, y),
            Message::Write(text) => println!("Write: {}", text),
            Message::ChangeColor(r, g, b) => println!("Color: {},{},{}", r, g, b),
        }
    }
}

fn enum_demo() {
    let m1 = Message::Quit;
    let m2 = Message::Move { x: 10, y: 20 };
    let m3 = Message::Write(String::from("hello"));
    let m4 = Message::ChangeColor(255, 0, 128);

    m1.call(); // Quit
    m2.call(); // Move to 10,20
    m3.call(); // Write: hello
    m4.call(); // Color: 255,0,128
}
```

**Enum memory layout:**

```
TAGGED UNION under the hood:

enum Message {
    Quit,                    // no data
    Move { x: i32, y: i32 },// 8 bytes of data
    Write(String),           // 24 bytes of data
    ChangeColor(u8, u8, u8), // 3 bytes of data
}

Memory layout:
┌────────────┬──────────────────────────────────┐
│  tag (u8)  │  data (size of LARGEST variant)  │
│  0=Quit    │  24 bytes (for String)            │
│  1=Move    │                                  │
│  2=Write   │                                  │
│  3=Color   │                                  │
└────────────┴──────────────────────────────────┘
Total: 1 + 24 + alignment = ~32 bytes
Every instance same size, tagged to know which variant.
```

**Null-free design with Option:**

```rust
// Rust has NO null. Instead it has Option<T>:
enum Option<T> {
    Some(T),  // contains a value
    None,     // represents absence
}

// You CANNOT forget to check — the type system forces you:
fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

let result = divide(10.0, 2.0); // Some(5.0)
let bad = divide(10.0, 0.0);    // None
// Must unwrap before using:
// result + 1.0; // ERROR: can't add Option<f64> to f64!
```

---

## 17. Pattern Matching (`match`)

### Q: What is `match` in Rust? How does it work?

**Answer:**

`match` is Rust's most powerful control flow construct. It performs exhaustive pattern matching — the compiler ensures you handle every case.

```
MATCH ANATOMY:

match VALUE {
    PATTERN1 => EXPRESSION1,
    PATTERN2 => EXPRESSION2,
    _         => DEFAULT,       // _ matches anything
}

Rules:
1. Must be EXHAUSTIVE — cover all possible values
2. Patterns checked in ORDER — first match wins
3. Each arm is an EXPRESSION — match itself is an expression
4. Arms separated by commas (optional after blocks {})
```

```rust
fn match_demo() {
    // ── Basic match ───────────────────────────────────────────
    let coin = 25u32;
    let value = match coin {
        1  => "penny",
        5  => "nickel",
        10 => "dime",
        25 => "quarter",
        _  => "unknown",  // catch-all
    };

    // ── Match with binding ────────────────────────────────────
    let msg = Message::Move { x: 5, y: 10 };
    match msg {
        Message::Quit => println!("quit"),
        Message::Move { x, y } => println!("move to {},{}", x, y),
        Message::Write(text) => println!("{}", text),
        Message::ChangeColor(r, g, b) => println!("{} {} {}", r, g, b),
    }

    // ── Multiple patterns with | ──────────────────────────────
    let n = 3;
    match n {
        1 | 2 => println!("one or two"),
        3 | 4 => println!("three or four"),
        _     => println!("something else"),
    }

    // ── Range patterns ─────────────────────────────────────────
    let age = 25u32;
    match age {
        0..=12  => println!("child"),
        13..=17 => println!("teenager"),
        18..=64 => println!("adult"),
        65..    => println!("senior"),
    }

    // ── Guards (additional conditions) ───────────────────────
    let pair = (2, -2);
    match pair {
        (x, y) if x == y      => println!("equal"),
        (x, y) if x + y == 0  => println!("opposites"), // ← matches here
        (x, _)                => println!("x is {}", x),
    }

    // ── Binding with @ ────────────────────────────────────────
    let num = 7;
    match num {
        n @ 1..=12 => println!("month {}", n), // bind the matched value
        n @ 13..   => println!("number {}", n),
        _           => println!("zero"),
    }

    // ── Nested destructuring ──────────────────────────────────
    let points = vec![(0, 0), (1, 5), (10, -3)];
    for &(x, y) in &points {
        println!("({}, {})", x, y);
    }

    // ── match returns a value ─────────────────────────────────
    let result: &str = match n {
        0     => "zero",
        1..=9 => "single digit",
        _     => "multi digit",
    };
}
```

**`if let` — simplified single-pattern matching:**

```rust
fn if_let_demo() {
    let favorite = Some(7u32);

    // Verbose match:
    match favorite {
        Some(n) => println!("favorite: {}", n),
        None    => (),
    }

    // Equivalent, cleaner if let:
    if let Some(n) = favorite {
        println!("favorite: {}", n);
    }

    // With else:
    if let Some(n) = favorite {
        println!("got {}", n);
    } else {
        println!("got nothing");
    }
}
```

**`while let` — loop while pattern matches:**

```rust
fn while_let_demo() {
    let mut stack = vec![1, 2, 3];

    while let Some(top) = stack.pop() {
        println!("{}", top); // 3, 2, 1
    }
    // Stops when pop() returns None (empty stack)
}
```

**Destructuring patterns:**

```rust
fn destructuring() {
    // ── Struct destructuring ──────────────────────────────────
    struct Point { x: i32, y: i32 }
    let p = Point { x: 3, y: 7 };
    let Point { x, y } = p;    // destructure
    println!("{} {}", x, y);   // 3 7

    // Rename fields:
    let Point { x: a, y: b } = Point { x: 1, y: 2 };
    println!("{} {}", a, b);   // 1 2

    // ── Tuple destructuring ────────────────────────────────────
    let (a, b, c) = (1, 2.0, "hi");

    // ── Ignoring parts ────────────────────────────────────────
    let (first, _, third) = (1, 2, 3); // ignore second
    let (head, ..) = (1, 2, 3, 4);    // ignore rest

    // ── Reference destructuring ───────────────────────────────
    let v = vec![1, 2, 3];
    for &n in &v {        // & in pattern dereferences each &i32
        println!("{}", n); // n is i32, not &i32
    }
}
```

---

## 18. Option\<T\>

### Q: What is `Option<T>` and why does Rust use it instead of null?

**Answer:**

`Option<T>` is Rust's way of representing optional values — a value that may or may not exist. It eliminates null pointer bugs at the type-system level.

```
THE NULL PROBLEM (Tony Hoare called null his "billion-dollar mistake"):

C/Java:   String name = null;
          name.length();   // NullPointerException at runtime!
          Compiler allows it. No warning. Runtime crash.

Rust:     The type String can NEVER be null.
          Instead: Option<String> explicitly represents "maybe a String"
          The compiler FORCES you to handle the None case.
```

```rust
// Option<T> is defined as:
enum Option<T> {
    Some(T),  // has a value
    None,     // no value
}
// It's in the prelude — no import needed
// Some and None are directly accessible

fn option_demo() {
    // ── Creating Options ──────────────────────────────────────
    let some_number: Option<i32> = Some(42);
    let no_number: Option<i32> = None;
    let some_string: Option<String> = Some(String::from("hello"));

    // ── Type: Option<i32> ≠ i32  (must unwrap) ───────────────
    // let sum = some_number + 1; // ERROR! Option<i32> is not i32

    // ── Unwrapping methods ────────────────────────────────────

    // unwrap(): returns T, panics on None (use only if certain it's Some)
    let n = some_number.unwrap(); // 42

    // unwrap_or(): returns T or a default
    let n = no_number.unwrap_or(0); // 0

    // unwrap_or_else(): compute default lazily
    let n = no_number.unwrap_or_else(|| expensive_computation());

    // expect(): like unwrap but with a custom panic message
    let n = some_number.expect("should have a number"); // 42

    // ── Pattern matching (safest) ─────────────────────────────
    match some_number {
        Some(n) => println!("Got: {}", n),
        None    => println!("Nothing here"),
    }

    // ── if let (ergonomic) ────────────────────────────────────
    if let Some(n) = some_number {
        println!("Got: {}", n);
    }

    // ── Transforming Options ──────────────────────────────────

    // map(): transforms Some(T) → Some(U), passes None through
    let doubled = some_number.map(|n| n * 2); // Some(84)
    let nothing = no_number.map(|n| n * 2);   // None

    // and_then() (flatMap): chains Options
    fn parse_positive(s: &str) -> Option<u32> {
        s.parse::<i32>().ok()
         .and_then(|n| if n > 0 { Some(n as u32) } else { None })
    }

    // filter(): keeps Some if predicate true
    let even = some_number.filter(|n| n % 2 == 0); // Some(42)
    let odd_check = Some(3).filter(|n| n % 2 == 0); // None

    // or() / or_else(): fallback options
    let val = no_number.or(Some(99)); // Some(99)
    let val = some_number.or(Some(99)); // Some(42) — keeps first Some

    // is_some() / is_none(): boolean checks
    println!("{}", some_number.is_some()); // true
    println!("{}", no_number.is_none());   // true

    // as_ref(): Option<T> → Option<&T> (don't consume the option)
    let opt_string: Option<String> = Some(String::from("hello"));
    let opt_ref: Option<&String> = opt_string.as_ref();
    // opt_string still valid here!
}

fn expensive_computation() -> i32 { 42 }
```

**Option in function design:**

```rust
// Returning Option communicates "this might fail/not exist"
fn find_user(id: u32) -> Option<User> {
    let users = get_all_users();
    users.into_iter().find(|u| u.id == id)
}

// Chaining Options cleanly:
fn get_user_city(user_id: u32) -> Option<String> {
    find_user(user_id)
        .and_then(|user| user.address)
        .map(|addr| addr.city)
}
// Returns None if user not found, or has no address, or no city
// No nested if-null checks!
```

---

## 19. Result\<T, E\> & Error Handling

### Q: What is `Result<T, E>`? How does Rust handle errors?

**Answer:**

Rust has two kinds of errors:
- **Unrecoverable**: `panic!()` — crash the program (bugs)
- **Recoverable**: `Result<T, E>` — caller decides what to do (expected failures)

```rust
// Result<T, E> is defined as:
enum Result<T, E> {
    Ok(T),   // success — contains value of type T
    Err(E),  // failure — contains error of type E
}
// Also in prelude — no import needed
```

```
MENTAL MODEL:

   Operation that might fail
          │
          ▼
   Returns Result<T, E>
          │
    ┌─────┴─────┐
    │           │
   Ok(T)      Err(E)
    │           │
Success!     Handle/propagate error

The CALLER must decide what to do with Err.
Errors can't be silently ignored.
```

```rust
use std::fs::File;
use std::io::{self, Read};
use std::num::ParseIntError;

fn result_demo() {
    // ── Basic Result handling ─────────────────────────────────
    let result: Result<i32, ParseIntError> = "42".parse::<i32>();
    let bad: Result<i32, ParseIntError>    = "abc".parse::<i32>();

    // match (most explicit):
    match result {
        Ok(n)  => println!("Parsed: {}", n),
        Err(e) => println!("Error: {}", e),
    }

    // ── Unwrap variants ───────────────────────────────────────
    let n = result.unwrap();        // Ok → value, Err → panic
    let n = result.expect("parse failed"); // Ok → value, Err → panic with msg
    let n = result.unwrap_or(0);   // Ok → value, Err → 0
    let n = result.unwrap_or_else(|_| 0); // Ok → value, Err → compute default

    // ── Transformation ────────────────────────────────────────
    let doubled = result.map(|n| n * 2);       // Ok(84) or Err(...)
    let stringed = result.map(|n| n.to_string()); // Ok("42") or Err(...)

    // map_err: transform the error type
    let converted = result.map_err(|e| format!("Parse error: {}", e));

    // and_then: chain operations that return Result
    let chained = "10".parse::<i32>()
        .and_then(|n| if n > 0 { Ok(n * 2) } else { Err("negative".parse::<i32>().unwrap_err()) });

    // ── File reading with proper error handling ───────────────
    fn read_file_contents(path: &str) -> Result<String, io::Error> {
        let mut file = File::open(path)?; // ? propagates error
        let mut contents = String::new();
        file.read_to_string(&mut contents)?;
        Ok(contents)
    }

    match read_file_contents("hello.txt") {
        Ok(text) => println!("Contents: {}", text),
        Err(e)   => println!("Error reading file: {}", e),
    }

    // ── is_ok() / is_err() ────────────────────────────────────
    println!("{}", result.is_ok());  // true
    println!("{}", bad.is_err());    // true
}
```

**Custom error types:**

```rust
use std::fmt;

#[derive(Debug)]
enum AppError {
    NotFound(String),
    ParseError(String),
    IoError(std::io::Error),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::NotFound(msg)  => write!(f, "Not found: {}", msg),
            AppError::ParseError(msg)=> write!(f, "Parse error: {}", msg),
            AppError::IoError(e)     => write!(f, "IO error: {}", e),
        }
    }
}

// Implement From to allow ? operator conversion:
impl From<std::io::Error> for AppError {
    fn from(e: std::io::Error) -> Self {
        AppError::IoError(e)
    }
}

fn do_something() -> Result<String, AppError> {
    let text = std::fs::read_to_string("file.txt")?;
    // io::Error is automatically converted to AppError via From
    Ok(text)
}
```

**`panic!` vs `Result`:**

```
USE panic! when:                    USE Result when:
- Impossible states (bugs)          - Expected failure modes
- Prototype code                    - File not found
- Tests                             - Network failure
- Contract violations               - Invalid user input
- Invalid index access              - Parsing failure
- Division by zero (sometimes)      - Any caller-recoverable error
```

---

## 20. The `?` Operator

### Q: What does the `?` operator do?

**Answer:**

The `?` operator is syntactic sugar for propagating errors. It extracts `Ok(T)` or returns early with `Err(E)` from the current function.

```
WITHOUT ?:                          WITH ?:

let result = operation();           let value = operation()?;
let value = match result {          // That's it. One character.
    Ok(v)  => v,
    Err(e) => return Err(e.into()),
};
```

```rust
use std::io;
use std::fs::File;
use std::io::Read;

// Without ? — verbose:
fn read_username_verbose() -> Result<String, io::Error> {
    let f = File::open("user.txt");
    let mut f = match f {
        Ok(file) => file,
        Err(e)   => return Err(e),
    };
    let mut s = String::new();
    match f.read_to_string(&mut s) {
        Ok(_)  => Ok(s),
        Err(e) => Err(e),
    }
}

// With ? — clean:
fn read_username() -> Result<String, io::Error> {
    let mut f = File::open("user.txt")?;   // ? propagates Err
    let mut s = String::new();
    f.read_to_string(&mut s)?;             // ? propagates Err
    Ok(s)
}

// Even shorter using method chaining:
fn read_username_short() -> Result<String, io::Error> {
    let mut s = String::new();
    File::open("user.txt")?.read_to_string(&mut s)?;
    Ok(s)
}

// Or even:
fn read_username_one_liner() -> Result<String, io::Error> {
    std::fs::read_to_string("user.txt") // stdlib convenience fn
}
```

**`?` with type conversion:**

```rust
// ? also calls .into() on the error:
// If function returns Result<T, AppError>
// and operation returns Result<T, io::Error>
// ? converts io::Error → AppError via From<io::Error> for AppError

fn complex_operation() -> Result<String, AppError> {
    let contents = std::fs::read_to_string("file.txt")?;
    // io::Error automatically converted to AppError (if From implemented)
    let n: i32 = contents.trim().parse().map_err(|_| AppError::ParseError("bad number".into()))?;
    Ok(format!("Got number: {}", n))
}
```

**`?` in `main()`:**

```rust
// main can return Result:
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string("file.txt")?;
    println!("{}", content);
    Ok(())
}
// Box<dyn Error> accepts ANY error type
```

---

## 21. Vectors (`Vec<T>`)

### Q: What is a `Vec<T>` and how does it work internally?

**Answer:**

`Vec<T>` is Rust's dynamically-sized array. It stores elements of the same type on the heap, growing as needed.

**Internal structure:**

```
Vec<T> on stack (3 fields, 24 bytes on 64-bit):

┌─────────────────────────────────────────────────────────────┐
│  ptr: *mut T    →  pointer to heap buffer                   │
│  len: usize     →  number of elements currently stored      │
│  cap: usize     →  total allocated capacity                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
HEAP:  [ 1 | 2 | 3 | _ | _ ]   (len=3, cap=5)
         ▲           ▲   ▲
         │           │   └── uninitialized (but allocated)
         │           └── uninitialized
         └── elements 0..len are valid

GROWTH STRATEGY: when len == cap and you push:
1. Allocate new buffer (typically 2x capacity)
2. Move all elements to new buffer
3. Free old buffer
4. Update ptr, cap
```

```rust
fn vec_demo() {
    // ── Creating ──────────────────────────────────────────────
    let mut v1: Vec<i32> = Vec::new();     // empty
    let v2: Vec<i32> = vec![1, 2, 3];     // macro with initial values
    let v3: Vec<i32> = Vec::with_capacity(10); // pre-allocate

    // ── Adding elements ───────────────────────────────────────
    v1.push(1);
    v1.push(2);
    v1.push(3);
    // v1 = [1, 2, 3], len=3

    // ── Accessing elements ────────────────────────────────────
    let first = &v2[0];       // reference, panics if OOB
    let maybe = v2.get(0);    // returns Option<&i32>, safe
    let oob = v2.get(10);     // None (safe, no panic)

    // ── Iterating ─────────────────────────────────────────────
    for n in &v2 {        // borrow each element
        print!("{} ", n);
    }

    for n in &mut v1 {    // mutable reference
        *n += 10;         // dereference to modify
    }

    for n in v2 {         // consuming iteration (v2 moved)
        print!("{} ", n);
    }
    // v2 is invalid now

    // ── Removing ──────────────────────────────────────────────
    v1.pop();              // removes and returns last: Option<i32>
    v1.remove(0);          // removes at index, shifts elements left
    v1.retain(|&x| x > 5); // keep only elements where predicate is true

    // ── Other operations ──────────────────────────────────────
    println!("len: {}", v1.len());
    println!("capacity: {}", v1.capacity());
    println!("is empty: {}", v1.is_empty());
    v1.sort();
    v1.dedup();            // remove consecutive duplicates
    v1.reverse();

    // ── Vec of enums (heterogeneous data trick) ───────────────
    #[derive(Debug)]
    enum Cell {
        Int(i32),
        Float(f64),
        Text(String),
    }

    let row = vec![
        Cell::Int(42),
        Cell::Float(3.14),
        Cell::Text(String::from("hello")),
    ];
    // Now you have a "heterogeneous" Vec via enum variants

    // ── Slicing a Vec ─────────────────────────────────────────
    let v = vec![1, 2, 3, 4, 5];
    let slice: &[i32] = &v[1..4]; // [2, 3, 4]
}
```

**Vec growth visualization:**

```
PUSH operations and capacity growth:

push(1): len=1, cap=1   [1]
push(2): len=2, cap=2   [1|2]
push(3): len=3, cap=4   [1|2|3|_]     (grew: 2→4)
push(4): len=4, cap=4   [1|2|3|4]
push(5): len=5, cap=8   [1|2|3|4|5|_|_|_]  (grew: 4→8)

Amortized O(1) push because growth is geometric.
Use Vec::with_capacity(n) if you know the size — avoids reallocations!
```

---

## 22. Strings: `String` vs `&str`

### Q: What's the difference between `String` and `&str`? Why two types?

**Answer:**

This is one of the most commonly asked Rust questions. The short answer: `String` owns its data; `&str` is a view (slice) into string data.

```
TWO STRING TYPES:

&str (string slice):                String (owned string):
┌──────────────────────┐           ┌──────────────────────┐
│  Fat pointer:        │           │  Vec<u8> internally: │
│  ptr → string data   │           │  ptr → heap buffer   │
│  len: usize          │           │  len: usize          │
└──────────────────────┘           │  cap: usize          │
                                   └──────────────────────┘
DOES NOT own data.                 OWNS heap-allocated data.
Read-only view.                    Can grow/shrink/mutate.
Borrowed from somewhere.           Freed when dropped.
```

```
MEMORY PICTURE:

LITERAL &str:                   STRING LITERAL in binary:
                                ┌──────────────────────────────────┐
let s: &str = "hello";  ──────►│  h  e  l  l  o  (in .rodata)    │
                                └──────────────────────────────────┘
                                (Read-only, 'static lifetime)

String:
                    STACK                HEAP
let s = String::   ┌──────────┐        ┌────────────────┐
  from("hello");   │ ptr ─────┼───────►│ h  e  l  l  o │
                   │ len: 5   │        └────────────────┘
                   │ cap: 5   │
                   └──────────┘
                   (owns heap data, mutable)

&String:           STACK (reference)   STACK (String)    HEAP
let r = &s;        ┌──────────┐        ┌──────────┐    ┌───────┐
                   │ ptr ─────┼───────►│ ptr ─────┼───►│hello  │
                   └──────────┘        │ len: 5   │    └───────┘
                                       │ cap: 5   │
                                       └──────────┘
```

```rust
fn string_demo() {
    // ── &str — string slice ───────────────────────────────────
    let s1: &str = "hello"; // literal — &'static str
    let s2: &str = &String::from("hello")[..]; // slice of a String

    // ── String — owned ────────────────────────────────────────
    let mut s3 = String::from("hello");
    let s4 = String::new();              // empty String
    let s5 = "hello".to_string();        // &str → String
    let s6 = "hello".to_owned();         // same

    // ── Mutating String ───────────────────────────────────────
    s3.push(' ');            // append char
    s3.push_str("world");    // append &str
    println!("{}", s3);      // "hello world"

    // ── Concatenation ─────────────────────────────────────────
    let s7 = String::from("hello ");
    let s8 = String::from("world");
    let s9 = s7 + &s8; // s7 MOVED here (fn add(self, s: &str) -> String)
    // s7 invalid after this!
    println!("{}", s9);  // "hello world"

    // format! is cleaner (doesn't move):
    let s10 = String::from("hello");
    let s11 = String::from(" world");
    let s12 = format!("{}{}", s10, s11); // both still valid
    println!("{}", s12);

    // ── String is UTF-8 ───────────────────────────────────────
    let hello = String::from("Здравствуйте"); // Cyrillic
    println!("bytes: {}", hello.len()); // 24 (NOT 12 chars!)
    // Each Cyrillic char = 2 bytes in UTF-8

    // Iterating over chars vs bytes:
    for c in "hello".chars() {
        print!("{} ", c); // h e l l o
    }
    for b in "hello".bytes() {
        print!("{} ", b); // 104 101 108 108 111
    }

    // ── Indexing — NOT ALLOWED in Rust ───────────────────────
    // let c = hello[0]; // ERROR: Rust prevents byte-index into String
    // (would return a byte, not a char — could split UTF-8 sequence)
    let first_char = hello.chars().next().unwrap(); // safe

    // ── Slicing — possible but must be char boundary ──────────
    let slice = &hello[0..4]; // "Зд" (each char is 2 bytes)
    // &hello[0..1] would PANIC: not a char boundary

    // ── Converting ────────────────────────────────────────────
    let n: i32 = 42;
    let s = n.to_string();      // i32 → String
    let parsed: i32 = "42".parse().unwrap(); // &str → i32
}
```

**When to use which:**

```
Use &str when:                      Use String when:
- Function parameter (preferred)    - You need to own the string
- Returning static strings          - Building/modifying strings
- String literals                   - Returning from function
- Cheapest: just a pointer+len      - Storing in struct/Vec

RULE OF THUMB:
fn process(s: &str) { ... }        // accept any string input
→ caller can pass &String or &str  (deref coercion: &String → &str)
```

---

## 23. HashMaps

### Q: How do HashMaps work in Rust?

**Answer:**

`HashMap<K, V>` stores key-value pairs with O(1) average lookup, insertion, and deletion.

```rust
use std::collections::HashMap;

fn hashmap_demo() {
    // ── Creating ──────────────────────────────────────────────
    let mut scores: HashMap<String, i32> = HashMap::new();

    // ── Inserting ─────────────────────────────────────────────
    scores.insert(String::from("Alice"), 100);
    scores.insert(String::from("Bob"), 85);
    scores.insert(String::from("Charlie"), 92);
    // Keys that implement Copy are copied; owned types (String) are moved!

    // ── From iterators ────────────────────────────────────────
    let teams = vec!["Red", "Blue", "Green"];
    let initial_scores = vec![10, 20, 30];
    let team_scores: HashMap<_, _> = teams.iter().zip(initial_scores.iter()).collect();

    // ── Accessing ─────────────────────────────────────────────
    // get() returns Option<&V>:
    if let Some(score) = scores.get("Alice") {
        println!("Alice: {}", score); // 100
    }

    // Direct index — panics if key absent:
    // let s = scores["Alice"]; // panics if "Alice" not in map

    // ── Iterating ─────────────────────────────────────────────
    for (name, score) in &scores {
        println!("{}: {}", name, score);
    }
    // Order is NOT guaranteed (hash map = unordered)

    // ── Updating ──────────────────────────────────────────────
    // Overwrite existing:
    scores.insert(String::from("Alice"), 110); // overwrites 100

    // Only insert if key doesn't exist:
    scores.entry(String::from("Dave")).or_insert(75);
    scores.entry(String::from("Alice")).or_insert(0); // Alice stays 110

    // Modify based on existing value:
    let count = scores.entry(String::from("Alice")).or_insert(0);
    *count += 5; // dereference to modify (count is &mut i32)

    // ── Removing ──────────────────────────────────────────────
    scores.remove("Bob");

    // ── Checking existence ────────────────────────────────────
    println!("{}", scores.contains_key("Alice")); // true
    println!("{}", scores.len());

    // ── Word count example ────────────────────────────────────
    let text = "hello world hello rust world hello";
    let mut word_count: HashMap<&str, i32> = HashMap::new();
    for word in text.split_whitespace() {
        let count = word_count.entry(word).or_insert(0);
        *count += 1;
    }
    // hello: 3, world: 2, rust: 1
    println!("{:?}", word_count);
}
```

**HashMap internals:**

```
HashMap uses HASHBROWN (Robin Hood hashing) internally:

key ──► hash function ──► bucket index ──► value

┌───────────────────────────────────────────────┐
│  BUCKETS (array of slots)                     │
│                                               │
│  [0] Alice → 100                              │
│  [1] (empty)                                  │
│  [2] Bob → 85                                 │
│  [3] (empty)                                  │
│  [4] Charlie → 92                             │
│  ...                                          │
└───────────────────────────────────────────────┘

Collision handling: probing (not chaining in hashbrown)
Default hasher: SipHash (resistant to DoS attacks)
Load factor: ~87% before resize

For performance-critical code: AHashMap (ahash crate) is faster.
```

**Hashing requirements:**

```rust
// A type can be a HashMap key if it implements:
// - Hash: can be hashed
// - Eq: can be compared for equality

// Built-in: String, &str, i32, etc. all work as keys
// Custom types: derive Hash + Eq
#[derive(Hash, Eq, PartialEq, Debug)]
struct Player {
    name: String,
    team: String,
}

let mut player_scores: HashMap<Player, u32> = HashMap::new();
```

---

## 24. Traits

### Q: What are traits in Rust? How do they compare to interfaces?

**Answer:**

Traits define shared behavior — a set of methods a type must implement. They're similar to interfaces in Java/Go, but more powerful.

```
TRAITS = Shared behavior contracts

trait Greet {
    fn greet(&self) -> String;
}

Any type implementing Greet must have a greet() method.
The trait doesn't care how — each type chooses.
```

```rust
// ── Defining a trait ──────────────────────────────────────────
trait Summary {
    // Required method (no default implementation):
    fn summarize_author(&self) -> String;

    // Default method (can be overridden):
    fn summarize(&self) -> String {
        format!("(Read more from {}...)", self.summarize_author())
    }
}

// ── Implementing a trait ──────────────────────────────────────
struct Article {
    title: String,
    author: String,
    content: String,
}

impl Summary for Article {
    fn summarize_author(&self) -> String {
        self.author.clone()
    }

    // Override the default:
    fn summarize(&self) -> String {
        format!("{}, by {} — {}", self.title, self.author, &self.content[..50])
    }
}

struct Tweet {
    username: String,
    content: String,
}

impl Summary for Tweet {
    fn summarize_author(&self) -> String {
        format!("@{}", self.username)
    }
    // Uses default summarize() — no override needed
}

fn trait_demo() {
    let article = Article {
        title: String::from("Rust is Amazing"),
        author: String::from("Alice"),
        content: String::from("Rust provides memory safety without GC..."),
    };

    let tweet = Tweet {
        username: String::from("bob"),
        content: String::from("loving rust"),
    };

    println!("{}", article.summarize()); // custom impl
    println!("{}", tweet.summarize());   // default impl
}
```

**Traits as parameters (Trait Bounds):**

```rust
// impl Trait syntax (simpler):
fn notify(item: &impl Summary) {
    println!("Breaking news! {}", item.summarize());
}

// Trait bound syntax (equivalent, more verbose):
fn notify<T: Summary>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}

// Multiple trait bounds:
fn notify_display<T: Summary + std::fmt::Display>(item: &T) {
    println!("{}", item);
    println!("{}", item.summarize());
}

// Where clause (cleaner for complex bounds):
fn complex<T, U>(t: &T, u: &U) -> String
where
    T: Summary + std::fmt::Debug,
    U: std::fmt::Display + Clone,
{
    format!("{:?} {}", t, u)
}

// Returning traits (impl Trait in return position):
fn make_summarizable() -> impl Summary {
    Tweet { username: String::from("user"), content: String::from("tweet") }
    // Caller only knows the return type implements Summary
    // (must return ONE concrete type though — not dynamic dispatch)
}
```

**Important standard traits to know:**

```rust
// ── Debug: enables {:?} formatting ───────────────────────────
#[derive(Debug)]
struct Point { x: f64, y: f64 }
let p = Point { x: 1.0, y: 2.0 };
println!("{:?}", p);   // Point { x: 1.0, y: 2.0 }
println!("{:#?}", p);  // pretty-printed

// ── Display: enables {} formatting ───────────────────────────
use std::fmt;
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
println!("{}", p); // (1.0, 2.0)

// ── Clone: explicit deep copy ─────────────────────────────────
#[derive(Clone)]
struct Config { /* ... */ }
let c1 = Config { /* ... */ };
let c2 = c1.clone(); // both valid

// ── PartialEq / Eq: equality comparison ──────────────────────
#[derive(PartialEq)]
struct Pair(i32, i32);
let a = Pair(1, 2);
let b = Pair(1, 2);
println!("{}", a == b); // true (PartialEq)

// ── PartialOrd / Ord: ordering/comparison ─────────────────────
#[derive(PartialOrd, PartialEq)]
struct Score(f64);

// ── Default: provides a default value ────────────────────────
#[derive(Default)]
struct Config { debug: bool, max: i32 }
let c = Config::default(); // Config { debug: false, max: 0 }

// ── Iterator: makes type work in for loops + iterator chains ──
// (covered in section 27)

// ── From / Into: type conversions ────────────────────────────
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}
let boiling = Celsius(100.0);
let f: Fahrenheit = boiling.into(); // Into automatically from From
```

---

## 25. Generics

### Q: What are generics in Rust? How do they enable zero-cost abstraction?

**Answer:**

Generics allow writing code that works for multiple types without duplicating it. Rust uses **monomorphization** — generics are compiled into concrete types, so there's zero runtime overhead.

```
MONOMORPHIZATION:

fn largest<T: PartialOrd>(list: &[T]) -> &T { ... }

At compile time, if called with i32 AND f64:
 → generates:  largest_i32(list: &[i32]) -> &i32 { ... }
 →             largest_f64(list: &[f64]) -> &f64 { ... }

Result: Same performance as hand-written type-specific code.
        No virtual dispatch. No boxing. Pure zero-cost.
```

```rust
// ── Generic function ──────────────────────────────────────────
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    largest
}

fn generics_demo() {
    let numbers = vec![34, 50, 25, 100, 65];
    println!("largest: {}", largest(&numbers)); // 100

    let chars = vec!['y', 'm', 'a', 'q'];
    println!("largest: {}", largest(&chars)); // y (alphabetically)
}

// ── Generic struct ────────────────────────────────────────────
struct Pair<T> {
    first: T,
    second: T,
}

impl<T> Pair<T> {
    fn new(first: T, second: T) -> Self {
        Pair { first, second }
    }
}

// Implement methods ONLY when T has certain traits:
impl<T: std::fmt::Display + PartialOrd> Pair<T> {
    fn cmp_display(&self) {
        if self.first >= self.second {
            println!("First is largest: {}", self.first);
        } else {
            println!("Second is largest: {}", self.second);
        }
    }
}

// ── Multiple type parameters ──────────────────────────────────
struct Map<K, V> {
    key: K,
    value: V,
}

// ── Generic enum ──────────────────────────────────────────────
enum MyResult<T, E> {
    Ok(T),
    Err(E),
}

// ── Blanket implementations ───────────────────────────────────
// Implement a trait for ALL types satisfying a bound:
// This is how ToString is implemented for everything with Display:
// impl<T: Display> ToString for T { ... }

// ── Generic with lifetime ─────────────────────────────────────
struct Wrapper<'a, T> {
    value: &'a T,
}

impl<'a, T: std::fmt::Display> Wrapper<'a, T> {
    fn show(&self) {
        println!("{}", self.value);
    }
}
```

**`where` clause for readability:**

```rust
// Hard to read:
fn complex_fn<T: Clone + std::fmt::Debug, U: std::fmt::Display + PartialOrd>(t: T, u: U) {}

// Cleaner with where:
fn complex_fn<T, U>(t: T, u: U)
where
    T: Clone + std::fmt::Debug,
    U: std::fmt::Display + PartialOrd,
{}
```

---

## 26. Closures

### Q: What are closures in Rust? How do they capture their environment?

**Answer:**

Closures are anonymous functions that can capture variables from their enclosing scope. They're similar to lambdas in other languages but with explicit capture semantics.

```
CLOSURE SYNTAX:

|param1, param2| expression

|param1, param2| {
    statement1;
    statement2;
    expression  // return value
}

Types often inferred — no annotations needed:
let add = |a, b| a + b;
let add: fn(i32, i32) -> i32 = |a, b| a + b; // explicit
```

**Three ways closures capture:**

```
┌──────────────────────────────────────────────────────────────┐
│              CLOSURE CAPTURE MODES                           │
│                                                              │
│  1. By REFERENCE (&T)    — FnOnce + Fn + FnMut              │
│     Closure borrows the variable. Cheapest.                  │
│     Used when closure only reads.                            │
│                                                              │
│  2. By MUT REFERENCE (&mut T) — FnOnce + FnMut             │
│     Closure mutably borrows. Needs mut closure var.          │
│     Used when closure modifies captured value.               │
│                                                              │
│  3. By VALUE (T)         — FnOnce                           │
│     Closure takes ownership. Use `move` keyword.            │
│     Required for threads (can't borrow across threads).      │
└──────────────────────────────────────────────────────────────┘
```

```rust
fn closure_demo() {
    // ── Basic closures ─────────────────────────────────────────
    let double = |x| x * 2;
    let add_one = |x: i32| -> i32 { x + 1 };

    println!("{}", double(5));  // 10
    println!("{}", add_one(5)); // 6

    // ── Capturing by reference (default) ─────────────────────
    let x = 10;
    let print_x = || println!("x = {}", x); // borrows x
    print_x();
    println!("x still accessible: {}", x); // x still valid

    // ── Capturing by mutable reference ────────────────────────
    let mut count = 0;
    let mut increment = || {
        count += 1;  // mutably borrows count
        count
    };
    println!("{}", increment()); // 1
    println!("{}", increment()); // 2
    // println!("{}", count); // ERROR: count mutably borrowed by closure

    drop(increment); // end the borrow
    println!("{}", count); // 2 — now accessible

    // ── Capturing by value (move) ─────────────────────────────
    let name = String::from("Alice");
    let greet = move || println!("Hello, {}!", name); // name MOVED
    greet();
    // println!("{}", name); // ERROR: name was moved

    // ── Closures as function arguments ────────────────────────
    let numbers = vec![1, 2, 3, 4, 5];
    let evens: Vec<i32> = numbers.iter()
        .filter(|&&x| x % 2 == 0)
        .copied()
        .collect();
    println!("{:?}", evens); // [2, 4]

    let doubled: Vec<i32> = numbers.iter()
        .map(|&x| x * 2)
        .collect();
    println!("{:?}", doubled); // [2, 4, 6, 8, 10]

    // ── Storing closures: Fn, FnMut, FnOnce traits ────────────
    fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
        f(x)
    }

    fn apply_once<F: FnOnce() -> String>(f: F) -> String {
        f() // can only call once (closure may have consumed captured data)
    }

    let result = apply(|x| x * x, 5); // 25
    println!("{}", result);
}
```

**Fn, FnMut, FnOnce hierarchy:**

```
FnOnce ← FnMut ← Fn
(weakest)         (strongest)

Fn:      can be called multiple times, doesn't mutate captures
         → captures by reference (&T)

FnMut:   can be called multiple times, may mutate captures
         → captures by mutable reference (&mut T)

FnOnce:  can only be called ONCE (may consume captured values)
         → captures by value (T)

Every Fn is also FnMut, every FnMut is also FnOnce.
The trait bound you specify is the MINIMUM requirement.

Use Fn for most cases (most permissive requirement).
```

---

## 27. Iterators & the Iterator Trait

### Q: How do iterators work in Rust? What is lazy evaluation?

**Answer:**

Iterators are objects that produce a sequence of values. They're **lazy** — computation only happens when you consume them.

```
ITERATOR PIPELINE:

   Source          Adapters (lazy)          Consumer (triggers eval)
┌──────────┐    ┌──────┐ ┌──────┐         ┌───────────┐
│ vec/range│───►│filter│►│ map  │──► ... ──►│ collect() │
│  data    │    │(lazy)│ │(lazy)│         │ sum()     │
└──────────┘    └──────┘ └──────┘         │ count()   │
                                          │ for loop  │
                                          └───────────┘
Nothing computed until consumer is called!
```

**The Iterator trait:**

```rust
// Core trait (simplified):
trait Iterator {
    type Item;               // the type of values yielded
    fn next(&mut self) -> Option<Self::Item>; // advance and return next

    // ALL other methods (map, filter, etc.) are built on next()
    // They're provided as default implementations!
}
```

```rust
fn iterator_demo() {
    // ── Creating iterators ────────────────────────────────────
    let v = vec![1, 2, 3, 4, 5];

    // iter()     → iterates over &T (borrows)
    // iter_mut() → iterates over &mut T (mutable borrows)
    // into_iter()→ iterates over T (consuming — takes ownership)

    let iter1 = v.iter();       // &i32 iterator
    let iter2 = v.iter_mut();   // (needs mut v) &mut i32 iterator
    let iter3 = v.into_iter();  // i32 iterator (v moved)

    // ── Manual iteration ──────────────────────────────────────
    let v = vec![1, 2, 3];
    let mut iter = v.iter();
    assert_eq!(iter.next(), Some(&1));
    assert_eq!(iter.next(), Some(&2));
    assert_eq!(iter.next(), Some(&3));
    assert_eq!(iter.next(), None);

    // ── Adapter methods (lazy — return new iterators) ─────────
    let v = vec![1, 2, 3, 4, 5, 6];

    // map: transform each element
    let doubled: Vec<i32> = v.iter().map(|&x| x * 2).collect();
    // [2, 4, 6, 8, 10, 12]

    // filter: keep elements matching predicate
    let evens: Vec<&i32> = v.iter().filter(|&&x| x % 2 == 0).collect();
    // [2, 4, 6]

    // filter_map: filter + transform in one step
    let even_doubled: Vec<i32> = v.iter()
        .filter_map(|&x| if x % 2 == 0 { Some(x * 2) } else { None })
        .collect();
    // [4, 8, 12]

    // enumerate: adds index
    for (i, &val) in v.iter().enumerate() {
        println!("[{}] = {}", i, val);
    }

    // zip: combine two iterators
    let names = vec!["Alice", "Bob", "Charlie"];
    let scores = vec![90, 85, 92];
    let combined: Vec<_> = names.iter().zip(scores.iter()).collect();
    // [("Alice", 90), ("Bob", 85), ("Charlie", 92)]

    // chain: concatenate iterators
    let a = vec![1, 2, 3];
    let b = vec![4, 5, 6];
    let chained: Vec<i32> = a.iter().chain(b.iter()).copied().collect();
    // [1, 2, 3, 4, 5, 6]

    // flat_map: map + flatten
    let words = vec!["hello world", "foo bar"];
    let chars: Vec<&str> = words.iter().flat_map(|s| s.split_whitespace()).collect();
    // ["hello", "world", "foo", "bar"]

    // take / skip:
    let first_three: Vec<i32> = (1..100).take(3).collect(); // [1, 2, 3]
    let skip_two: Vec<i32> = v.iter().skip(2).copied().collect(); // [3,4,5,6]

    // ── Consumer methods (eager — trigger evaluation) ─────────
    let v = vec![1, 2, 3, 4, 5];

    let sum: i32 = v.iter().sum();           // 15
    let product: i32 = v.iter().product();   // 120
    let count = v.iter().count();            // 5
    let max = v.iter().max();                // Some(5)
    let min = v.iter().min();                // Some(1)

    let any_even = v.iter().any(|&x| x % 2 == 0);   // true
    let all_pos  = v.iter().all(|&x| x > 0);          // true

    let found = v.iter().find(|&&x| x > 3);  // Some(4)
    let pos   = v.iter().position(|&x| x > 3); // Some(3)

    // fold: accumulate with initial value (like reduce)
    let sum2 = v.iter().fold(0, |acc, &x| acc + x); // 15
    let product2 = v.iter().fold(1, |acc, &x| acc * x); // 120

    // collect: consume into collection
    let evens: Vec<i32> = (1..=10).filter(|x| x % 2 == 0).collect();
    let set: std::collections::HashSet<i32> = v.into_iter().collect();

    // ── Ranges as iterators ───────────────────────────────────
    let range_sum: i32 = (1..=100).sum(); // 5050 (Gauss!)
}
```

**Creating a custom iterator:**

```rust
struct Counter {
    count: u32,
    max: u32,
}

impl Counter {
    fn new(max: u32) -> Self {
        Counter { count: 0, max }
    }
}

impl Iterator for Counter {
    type Item = u32;

    fn next(&mut self) -> Option<u32> {
        if self.count < self.max {
            self.count += 1;
            Some(self.count)
        } else {
            None
        }
    }
}

fn custom_iterator_demo() {
    let counter = Counter::new(5);
    let v: Vec<u32> = counter.collect(); // [1, 2, 3, 4, 5]

    // Now ALL iterator methods work:
    let sum: u32 = Counter::new(5).sum(); // 15
    let doubled: Vec<u32> = Counter::new(3).map(|x| x * 2).collect(); // [2,4,6]

    // Zip two counters:
    let pairs: Vec<_> = Counter::new(5)
        .zip(Counter::new(5).skip(1))
        .collect();
    // [(1,2), (2,3), (3,4), (4,5)]
}
```

---

## 28. Smart Pointers: `Box<T>`

### Q: What is `Box<T>` and when do you use it?

**Answer:**

`Box<T>` is the simplest smart pointer — it allocates a value on the heap and stores a pointer to it on the stack. When the Box goes out of scope, both the Box (stack) and the value (heap) are freed.

```
WITHOUT Box:                    WITH Box<T>:

Stack: [i32: 5]                 Stack: [Box: ptr]
                                            │
                                Heap:  [i32: 5] ◄──┘
```

```rust
fn box_demo() {
    // ── Basic Box usage ────────────────────────────────────────
    let b = Box::new(5); // 5 allocated on heap
    println!("{}", b);   // works: Box<i32> auto-derefs to i32
    println!("{}", *b);  // explicit dereference

    // b goes out of scope → heap memory freed automatically

    // ── USE CASE 1: Recursive data structures ─────────────────
    // Without Box, this DOESN'T COMPILE (infinite size):
    // enum List { Cons(i32, List), Nil }
    //             ^ what's the size of List? Infinite!

    // WITH Box: size is known (ptr = usize):
    #[derive(Debug)]
    enum List {
        Cons(i32, Box<List>), // Box has known size (pointer)
        Nil,
    }

    use List::{Cons, Nil};
    let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
    println!("{:?}", list);

    // Memory layout:
    // Stack: Cons(1, ptr1)
    // Heap:  [Cons(2, ptr2)] at ptr1
    // Heap:  [Cons(3, ptr3)] at ptr2
    // Heap:  [Nil]           at ptr3

    // ── USE CASE 2: Trait objects (dynamic dispatch) ──────────
    trait Animal {
        fn speak(&self) -> &str;
    }

    struct Dog;
    struct Cat;

    impl Animal for Dog { fn speak(&self) -> &str { "Woof!" } }
    impl Animal for Cat { fn speak(&self) -> &str { "Meow!" } }

    // Store different types that implement Animal:
    let animals: Vec<Box<dyn Animal>> = vec![
        Box::new(Dog),
        Box::new(Cat),
        Box::new(Dog),
    ];

    for animal in &animals {
        println!("{}", animal.speak()); // dynamic dispatch via vtable
    }

    // ── USE CASE 3: Large data, avoid stack copies ────────────
    let large_array = Box::new([0u8; 1_000_000]); // 1MB on heap
    // If not boxed, this would be 1MB on the stack (risky!)
}
```

**Box deref coercion:**

```rust
// Box<T> implements Deref<Target = T>
// So &Box<T> coerces to &T automatically

fn hello(s: &str) {
    println!("Hello, {}", s);
}

let boxed = Box::new(String::from("world"));
hello(&boxed);  // &Box<String> → &String → &str (two coercions!)
```

**`dyn Trait` (trait objects):**

```
STATIC DISPATCH (generics):           DYNAMIC DISPATCH (trait objects):

fn process<T: Animal>(a: T) {         fn process(a: &dyn Animal) {
    a.speak();                             a.speak();  // vtable lookup
}                                      }
                                       
Monomorphized at compile time.         Single function. Uses vtable.
Faster (no indirection).               Flexible (heterogeneous types).
Code size may be larger.               Small runtime overhead.
Type known at compile time.            Type determined at runtime.
```

---

## 29. Smart Pointers: `Rc<T>` and `RefCell<T>`

### Q: What are `Rc<T>` and `RefCell<T>`? When do you use them?

**Answer:**

These are for situations where Rust's single-owner model is too restrictive.

### `Rc<T>` — Reference Counted (multiple owners)

```
PROBLEM: What if two parts of your code need to OWN the same data?
         (graph nodes, GUI trees, etc.)

SOLUTION: Rc<T> — Reference Counted pointer.
          Multiple Rc<T> can point to same data.
          Data freed when ALL Rc<T> go out of scope.
          Single-threaded only (no atomic ops).

COUNTER:
  Rc::new(data)     → count=1
  Rc::clone(&rc)    → count=2 (cheap: just increments counter)
  drop(clone)       → count=1
  drop(original)    → count=0 → data freed
```

```rust
use std::rc::Rc;

fn rc_demo() {
    let a = Rc::new(String::from("shared data"));
    println!("count: {}", Rc::strong_count(&a)); // 1

    let b = Rc::clone(&a); // NOT a deep clone — just increments count
    println!("count: {}", Rc::strong_count(&a)); // 2

    {
        let c = Rc::clone(&a);
        println!("count: {}", Rc::strong_count(&a)); // 3
        println!("{}", c);
    } // c dropped → count goes to 2

    println!("count: {}", Rc::strong_count(&a)); // 2
    println!("{} {}", a, b); // both valid

    // NOTE: Rc<T> is IMMUTABLE — no mutation through Rc alone!
    // For mutation: use Rc<RefCell<T>>
}
```

### `RefCell<T>` — Interior Mutability

```
PROBLEM: Sometimes you KNOW your code is correct, but the borrow
         checker can't verify it (e.g., mutable state inside
         immutable structure, mock objects in tests).

SOLUTION: RefCell<T> — moves borrow checking to RUNTIME.
          Single-threaded version of Mutex.
          Panics at runtime if rules violated (instead of compile error).
```

```rust
use std::cell::RefCell;

fn refcell_demo() {
    // RefCell allows mutation through an immutable reference:
    let data = RefCell::new(vec![1, 2, 3]);

    // Immutable borrow:
    let r1 = data.borrow(); // returns Ref<Vec<i32>>
    println!("{:?}", *r1);

    drop(r1); // must drop before mutable borrow

    // Mutable borrow:
    let mut r2 = data.borrow_mut(); // returns RefMut<Vec<i32>>
    r2.push(4);
    drop(r2);

    println!("{:?}", data.borrow()); // [1, 2, 3, 4]

    // RUNTIME PANIC if rules violated:
    // let r3 = data.borrow();
    // let r4 = data.borrow_mut(); // PANIC: already borrowed!
}

// ── Rc<RefCell<T>> — the common combo ───────────────────────────
// Multiple owners + interior mutability:
use std::rc::Rc;
use std::cell::RefCell;

fn rc_refcell_demo() {
    let shared = Rc::new(RefCell::new(vec![1, 2, 3]));

    let a = Rc::clone(&shared);
    let b = Rc::clone(&shared);

    // a can mutate:
    a.borrow_mut().push(4);
    // b can mutate too:
    b.borrow_mut().push(5);

    println!("{:?}", shared.borrow()); // [1, 2, 3, 4, 5]
    // All three (shared, a, b) see the same data!
}
```

**Smart pointer comparison:**

```
┌───────────────┬──────────────┬───────────────┬────────────────────┐
│               │  Box<T>      │  Rc<T>        │  Rc<RefCell<T>>    │
├───────────────┼──────────────┼───────────────┼────────────────────┤
│ Owners        │  One         │  Multiple     │  Multiple          │
│ Mutability    │  Normal rules│  Immutable    │  Interior mut.     │
│ Thread-safe   │  Yes         │  No           │  No                │
│ Borrow check  │  Compile     │  Compile      │  RUNTIME           │
│ Overhead      │  None        │  Ref count    │  Ref count+checks  │
│ Use case      │  Heap alloc, │  Shared read  │  Shared mutable    │
│               │  recursion   │  ownership    │  state             │
└───────────────┴──────────────┴───────────────┴────────────────────┘

For multi-threaded equivalents: Arc<T> and Arc<Mutex<T>>
```

---

## 30. Modules, Crates & the Package System

### Q: Explain Rust's module system, crates, and Cargo.

**Answer:**

```
RUST CODE ORGANIZATION HIERARCHY:

┌─────────────────────────────────────────────────────────────────┐
│                        WORKSPACE                                │
│  (optional: multiple packages together)                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      PACKAGE                              │ │
│  │  (has Cargo.toml — the unit Cargo builds)                 │ │
│  │  ┌─────────────────┐   ┌───────────────────────────────┐ │ │
│  │  │  BINARY CRATE   │   │      LIBRARY CRATE            │ │ │
│  │  │  src/main.rs    │   │      src/lib.rs               │ │ │
│  │  │  (executable)   │   │      (shared library)         │ │ │
│  │  └─────────────────┘   └───────────────────────────────┘ │ │
│  │                                                           │ │
│  │  Each crate is a tree of MODULES:                        │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  crate (root)                                       │ │ │
│  │  │  ├── mod garden                                     │ │ │
│  │  │  │   ├── mod vegetables                             │ │ │
│  │  │  │   └── mod fruits                                │ │ │
│  │  │  └── mod kitchen                                   │ │ │
│  │  │      └── fn cook()                                 │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

```rust
// ── Defining modules (in same file) ──────────────────────────
mod math {
    pub fn add(a: i32, b: i32) -> i32 { // pub = public
        a + b
    }

    fn subtract(a: i32, b: i32) -> i32 { // private (default)
        a - b
    }

    pub mod advanced {
        pub fn multiply(a: i32, b: i32) -> i32 {
            a * b
        }
        // Can call parent module's private items:
        pub fn subtract_and_double(a: i32, b: i32) -> i32 {
            super::subtract(a, b) * 2 // super = parent module
        }
    }
}

fn module_demo() {
    // Absolute path:
    println!("{}", crate::math::add(2, 3));

    // Relative path:
    println!("{}", math::add(2, 3));
    println!("{}", math::advanced::multiply(2, 3));

    // Use statement (bring into scope):
    use math::advanced::multiply;
    println!("{}", multiply(4, 5));

    // math::subtract(1, 2); // ERROR: private!
}
```

**Module file structure:**

```
src/
├── main.rs           (binary crate root)
├── lib.rs            (library crate root — optional)
├── garden.rs         (mod garden; in main.rs)
├── garden/
│   ├── mod.rs        (OR garden.rs — the module)
│   ├── vegetables.rs (submodule)
│   └── fruits.rs     (submodule)
└── kitchen.rs
```

```
In main.rs:
    mod garden;      // loads from garden.rs or garden/mod.rs
    mod kitchen;     // loads from kitchen.rs

In garden.rs (or garden/mod.rs):
    pub mod vegetables;  // loads from garden/vegetables.rs
    pub mod fruits;      // loads from garden/fruits.rs
```

**Cargo.toml structure:**

```toml
[package]
name = "my_project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
rand = "0.8"

[dev-dependencies]
# only for tests
criterion = "0.5"

[features]
default = []
logging = ["dep:log"]
```

**Visibility:**

```rust
pub struct Foo {           // struct public
    pub x: i32,            // field public
    y: i32,                // field private
}

pub(crate) fn bar() {}    // visible in this crate only
pub(super) fn baz() {}    // visible in parent module
pub(in crate::garden) fn qux() {} // visible in specific path
```

**Cargo commands to know:**

```
cargo new my_project      // create new package (binary)
cargo new --lib my_lib    // create library package
cargo build               // compile
cargo run                 // compile and run
cargo test                // run tests
cargo check               // fast type check (no binary)
cargo clippy              // linter
cargo fmt                 // formatter (rustfmt)
cargo doc --open          // generate and open docs
cargo add serde           // add dependency (cargo-edit)
```

---

## 31. Common Rust Idioms & Patterns

### Q: What are common Rust idioms you should know?

**Answer:**

### Builder Pattern

```rust
struct RequestBuilder {
    url: String,
    timeout: u64,
    retries: u32,
}

impl RequestBuilder {
    fn new(url: &str) -> Self {
        RequestBuilder {
            url: url.to_string(),
            timeout: 30,
            retries: 3,
        }
    }

    fn timeout(mut self, secs: u64) -> Self {
        self.timeout = secs;
        self
    }

    fn retries(mut self, n: u32) -> Self {
        self.retries = n;
        self
    }

    fn build(self) -> Request {
        Request { url: self.url, timeout: self.timeout, retries: self.retries }
    }
}

let req = RequestBuilder::new("https://api.example.com")
    .timeout(60)
    .retries(5)
    .build();
```

### Newtype Pattern

```rust
// Wrap existing type to add meaning/safety:
struct Meters(f64);
struct Kilograms(f64);

// Now you CAN'T accidentally pass meters where kg is expected!
fn calculate_bmi(weight: Kilograms, height: Meters) -> f64 {
    weight.0 / (height.0 * height.0)
}

// Compiler prevents:
// calculate_bmi(Meters(1.8), Kilograms(70.0)); // ← type error!
```

### Type State Pattern

```rust
// Encode state in the type system:
struct Locked;
struct Unlocked;

struct Safe<State> {
    contents: String,
    _state: std::marker::PhantomData<State>,
}

impl Safe<Locked> {
    fn new(contents: String) -> Self {
        Safe { contents, _state: std::marker::PhantomData }
    }

    fn unlock(self, _password: &str) -> Safe<Unlocked> {
        Safe { contents: self.contents, _state: std::marker::PhantomData }
    }
}

impl Safe<Unlocked> {
    fn get_contents(&self) -> &str {
        &self.contents
    }

    fn lock(self) -> Safe<Locked> {
        Safe { contents: self.contents, _state: std::marker::PhantomData }
    }
}

// Can't call get_contents() on a Locked safe — compile time error!
```

### Error Handling with `thiserror`

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Parse error: {0}")]
    Parse(#[from] std::num::ParseIntError),

    #[error("Not found: {0}")]
    NotFound(String),
}

fn process(path: &str) -> Result<i32, AppError> {
    let content = std::fs::read_to_string(path)?; // io::Error → AppError::Io
    let n: i32 = content.trim().parse()?;         // ParseIntError → AppError::Parse
    Ok(n * 2)
}
```

### Common Iterator Chains

```rust
fn idiomatic_iterators() {
    let data = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    // Sum of squares of even numbers:
    let result: i32 = data.iter()
        .filter(|&&x| x % 2 == 0)
        .map(|&x| x * x)
        .sum();
    // 4 + 16 + 36 + 64 + 100 = 220

    // Partition into evens and odds:
    let (evens, odds): (Vec<i32>, Vec<i32>) = data.iter()
        .partition(|&&x| x % 2 == 0);

    // Flatten nested:
    let nested = vec![vec![1, 2], vec![3, 4], vec![5]];
    let flat: Vec<i32> = nested.into_iter().flatten().collect();
    // [1, 2, 3, 4, 5]

    // Group by (via HashMap):
    use std::collections::HashMap;
    let mut by_parity: HashMap<&str, Vec<i32>> = HashMap::new();
    for n in &data {
        by_parity.entry(if n % 2 == 0 { "even" } else { "odd" })
            .or_insert_with(Vec::new)
            .push(*n);
    }
}
```

---

## 32. Rust vs Other Languages — Interview Comparisons

### Q: How does Rust compare to C++, Java, Go, and Python?

**Answer:**

```
COMPARISON TABLE:
═══════════════════════════════════════════════════════════════════════════
Feature          Rust         C++         Java        Go          Python
─────────────────────────────────────────────────────────────────────────
Memory mgmt      Ownership    Manual/RAII GC (JVM)    GC          GC
Null safety      Option<T>    Nullable    Nullable    Nullable    None
Error handling   Result<T,E>  Exceptions  Exceptions  (val,err)   Exceptions
Concurrency      Fearless     Complex     Complex     Goroutines  GIL
Generics         Monomorph.   Templates   Type erase  None*       Duck typed
Performance      C-level      C-level     Near-C      Near-C      Slow
Compile speed    Slow         Slow        Medium      Fast        N/A (interp)
Learning curve   Steep        Very steep  Medium      Easy        Easy
Package mgr      Cargo        vcpkg/cmake Maven/Gradle go mod      pip
Zero-cost abs.   Yes          Yes         No          Partial     No
Data races       Impossible   Possible    Possible    Possible    GIL avoids
Undefined behav. None (safe)  Common      None        None        None
───────────────────────────────────────────────────────────────────────
```

**Rust vs C++:**
```
C++:  You manage memory manually. Easy to forget → use-after-free, double-free.
      RAII helps but can't prevent all aliasing bugs.
      Templates: powerful but error messages are terrible.

Rust: Compiler enforces memory rules. Can't have bugs at compile time.
      Generics: trait bounds give clear errors.
      No UB (in safe Rust).
```

**Rust vs Java:**
```
Java: GC pauses. Every object heap-allocated. Boxing overhead.
      Can't choose stack vs heap. Null everywhere.

Rust: No GC. Stack or heap — you control it. No boxing overhead.
      No null (Option<T> instead). Predictable performance.
```

**Rust vs Go:**
```
Go:   Simple, fast compile, great concurrency (goroutines/channels).
      But: garbage collector, no generics (until 1.18, limited),
      runtime overhead, no control over allocations.

Rust: More complex. Fearless concurrency at compile time.
      Zero-cost generics. Full control. Better for systems programming.
      Go better for quick services where GC pauses are OK.
```

---

## Key Interview Summary — Mental Models

```
┌─────────────────────────────────────────────────────────────────────┐
│              RUST MENTAL MODEL HIERARCHY                            │
│                                                                     │
│  1. OWNERSHIP: Every value has ONE owner. Drop when owner leaves.   │
│                                                                     │
│  2. MOVE vs COPY: Heap types move. Stack primitives copy.           │
│                                                                     │
│  3. BORROWING: & = shared read. &mut = exclusive write.            │
│     RULE: Many & OR one &mut. Never both.                          │
│                                                                     │
│  4. LIFETIMES: References must not outlive the data they point to. │
│     Usually inferred. Annotate when compiler can't figure it out.  │
│                                                                     │
│  5. TRAITS: Shared behavior. Like interfaces but more powerful.    │
│     Generics + trait bounds = zero-cost polymorphism.              │
│                                                                     │
│  6. ERROR HANDLING: Result<T,E> for recoverable. panic! for bugs.  │
│     Use ? to propagate. Never silently ignore errors.              │
│                                                                     │
│  7. ITERATORS: Lazy pipelines. Compose with map/filter/etc.        │
│     Consumed by collect/sum/for. Zero-cost abstraction.            │
│                                                                     │
│  8. THE COMPILER IS YOUR FRIEND: Error messages are detailed.      │
│     If it compiles, it's memory-safe (no UB in safe Rust).        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick-Reference: Common Compile Errors & Solutions

```
ERROR: "cannot borrow as mutable because it is also borrowed as immutable"
FIX:   Ensure immutable borrows are no longer in use before creating &mut.
       NLL helps: let the borrow's last use be before the &mut.

ERROR: "value used after move"  
FIX:   Clone() if you need both, or restructure to avoid double-use.
       Or pass &reference instead of moving.

ERROR: "does not live long enough"
FIX:   The reference outlives the data. Store owned data, or restructure lifetimes.
       Add lifetime annotations to show the compiler the relationship.

ERROR: "the trait bound `T: SomeTrait` is not satisfied"
FIX:   Add the trait bound: fn foo<T: SomeTrait>(x: T).
       Or ensure the type implements the trait.

ERROR: "mismatched types: expected `()`, found `i32`"
FIX:   You likely added a semicolon to the last expression.
       Remove it to return the value, or change return type to ().

ERROR: "closure may outlive the current function" 
FIX:   Use `move` closure to take ownership of captured variables.
       Required for thread::spawn and async contexts.
```

---

*This guide covers Rust basics thoroughly. The next level: async/await, unsafe Rust, macros, advanced trait patterns, and concurrency primitives (Arc, Mutex, channels).*

Now let me build this comprehensive guide. This will be extensive — covering every Rust basic concept with ASCII diagrams and real code.Here's your complete guide — **32 topics**, every concept explained from first principles with ASCII diagrams and real Rust code. Here's what's inside:

**Core ownership model (sections 3–8):** The entire ownership/borrow/lifetime system explained as one coherent mental model, with memory diagrams showing exactly what's on the stack vs heap at every step.

**Type system (sections 10–16):** Every scalar type, compound type, struct, enum — with memory layouts and all the edge cases (e.g., why `char` is 4 bytes, why you can't index a `String`).

**Error handling (sections 18–20):** `Option<T>`, `Result<T,E>`, and `?` — the full design philosophy of why Rust eliminates null and forces you to handle errors, with the transformation methods (`map`, `and_then`, `unwrap_or`, etc.).

**Collections (sections 21–23):** Internal structure of `Vec<T>` (the ptr/len/cap triple, growth strategy), the full `String` vs `&str` distinction with memory diagrams, and `HashMap` internals.

**Abstractions (sections 24–27):** Traits, generics (monomorphization explained), closures (all three capture modes: `Fn`/`FnMut`/`FnOnce`), and the iterator trait with lazy evaluation pipeline diagrams.

**Smart pointers (28–29):** When and why to use `Box<T>`, `Rc<T>`, `RefCell<T>`, and the `Rc<RefCell<T>>` combo.

**Mental model summary at the end** — 8 core rules that build the Rust worldview for thinking efficiently about any Rust code.

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