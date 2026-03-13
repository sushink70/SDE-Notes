## Concrete Types — The Complete Explanation

Every value in Rust has a **type**. Types fall into two categories: **concrete** and **abstract**.

---

### The Core Distinction

A **concrete type** is a type where the compiler knows **exactly**:
- What it is
- How many bytes it occupies in memory
- What operations it supports
- How to generate machine code for it

An **abstract type** (generics, trait objects) is a **placeholder** — the compiler knows a *category* of types, not a specific one.

```rust
let x: i32 = 42;          // concrete — compiler knows: 4 bytes, signed int
let y: String = "hi".to_string(); // concrete — compiler knows: heap string, 24 bytes on stack
let z: Vec<f64> = vec![];  // concrete — compiler knows: heap vec of 8-byte floats

fn foo<T>(val: T) {}       // T is NOT concrete — it's a placeholder
```

---

### Every Concrete Type Has a Fixed Memory Layout

This is the defining property. The compiler must be able to answer: *"how many bytes does this take?"*

```rust
// The compiler knows these sizes at compile time:
// i8    = 1 byte
// i32   = 4 bytes
// f64   = 8 bytes
// bool  = 1 byte

// Structs: sum of fields + alignment padding
struct Point {
    x: f64,   // 8 bytes
    y: f64,   // 8 bytes
}
// Point = 16 bytes — known at compile time

// Enums: size of largest variant + discriminant
enum Direction {
    North,     // 0 bytes of data
    East,      // 0 bytes of data
    Custom(f64, f64), // 16 bytes of data
}
// Direction = 16 bytes (largest) + discriminant — known at compile time
```

The `Sized` trait is how Rust marks this property. Every concrete type automatically implements `Sized`. This is what the compiler checks when it sees `T` in a generic — by default it requires `T: Sized`.

---

### The Full Taxonomy of Concrete Types

#### Primitive Types — Built into the language

```rust
// Integer types
let a: i8   = -128;
let b: i16  = -32_768;
let c: i32  = -2_147_483_648;
let d: i64  = -9_223_372_036_854_775_808;
let e: i128 = very_large_negative_number;
let f: isize = platform_pointer_sized; // 4 or 8 bytes depending on arch

let g: u8   = 255;
let h: u16  = 65_535;
let i: u32  = 4_294_967_295;
let j: u64  = 18_446_744_073_709_551_615;
let k: u128 = enormous;
let l: usize = 0; // always matches pointer size of the platform

// Floating point
let m: f32 = 3.14;  // 4 bytes, IEEE 754 single precision
let n: f64 = 3.14;  // 8 bytes, IEEE 754 double precision

// Boolean
let o: bool = true; // 1 byte (not 1 bit — alignment)

// Character
let p: char = 'A';  // 4 bytes — always a valid Unicode scalar value

// Unit type — represents "nothing"
let q: () = ();     // 0 bytes — used when a function returns no value
```

#### Compound Types — Built from other types

```rust
// Tuples — ordered, fixed-length, heterogeneous
let point: (f64, f64) = (1.0, 2.0);        // 16 bytes
let triple: (i32, bool, char) = (1, true, 'x'); // 9 bytes + padding

// Arrays — fixed-length, homogeneous
let arr: [i32; 4] = [1, 2, 3, 4]; // exactly 16 bytes, stack-allocated
let zeros: [u8; 1024] = [0; 1024]; // exactly 1024 bytes

// Difference from slice:
// [i32; 4] — concrete, SIZE is part of the type
// [i32]    — NOT concrete (unsized) — slice, size only known at runtime
```

#### Struct Types — User-defined named products

```rust
// Unit struct — 0 bytes
struct Marker;

// Tuple struct
struct Rgb(u8, u8, u8); // 3 bytes

// Named struct
struct Rectangle {
    x: f64,
    y: f64,
    width: f64,
    height: f64,
} // 32 bytes

// Each definition creates a UNIQUE concrete type
// Rectangle and (f64, f64, f64, f64) are different types even with same layout
```

#### Enum Types — User-defined tagged unions

```rust
// C-like enum — just a discriminant
enum Color {
    Red,    // discriminant = 0
    Green,  // discriminant = 1
    Blue,   // discriminant = 2
}
// Size: 1 byte (fits 3 variants)

// Data-carrying enum — Rust's algebraic sum type
enum Shape {
    Circle { radius: f64 },         // 8 bytes of data
    Rectangle { w: f64, h: f64 },   // 16 bytes of data
    Triangle(f64, f64, f64),        // 24 bytes of data
}
// Size = 24 (largest variant) + 8 (discriminant + padding) = 32 bytes

// Option<T> is just a concrete enum in the standard library:
enum Option<T> {
    None,
    Some(T),
}
// When T = i32: Option<i32> is concrete, size = 8 bytes
// When T = f64: Option<f64> is concrete, size = 16 bytes
// The generic Option<T> becomes concrete AFTER T is substituted
```

#### Pointer Types — Types that refer to other memory

```rust
// References — always the size of a pointer (8 bytes on 64-bit)
let x = 42i32;
let r: &i32 = &x;     // 8 bytes (thin pointer — points to sized type)
let s: &str = "hi";   // 16 bytes (fat pointer — pointer + length)
let sl: &[i32] = &[1,2,3]; // 16 bytes (fat pointer — pointer + length)

// Box — heap-allocated value, owned
let b: Box<i32> = Box::new(42);      // 8 bytes on stack (thin pointer)
let b2: Box<dyn Display> = Box::new(42i32); // 16 bytes (fat pointer — pointer + vtable)

// Raw pointers — unsafe, no lifetime tracking
let p: *const i32 = &x as *const i32; // 8 bytes
let pm: *mut i32 = &mut 0i32 as *mut i32; // 8 bytes

// Function pointers — pointer to a specific function
let fp: fn(i32) -> i32 = |x| x + 1; // 8 bytes
```

#### Smart Pointer and Collection Types

```rust
use std::sync::{Arc, Mutex};
use std::rc::Rc;
use std::cell::RefCell;

// These are all concrete types defined in std
let v: Vec<i32> = Vec::new();           // 24 bytes on stack (ptr + len + cap)
let s: String = String::new();          // 24 bytes on stack (ptr + len + cap)
let hm: std::collections::HashMap<String, i32> = Default::default();

let rc: Rc<i32> = Rc::new(42);          // 8 bytes on stack (thin pointer)
let arc: Arc<i32> = Arc::new(42);       // 8 bytes on stack (thin pointer)
let m: Mutex<i32> = Mutex::new(0);      // size varies by platform
let rc2: Rc<RefCell<i32>> = Rc::new(RefCell::new(0)); // concrete composition
```

---

### The Moment a Generic Becomes Concrete — Monomorphization

This is the crucial process. Generic types are **not** concrete — they are templates. They become concrete at the moment the type parameter is filled in.

```rust
// Generic definition — NOT concrete, just a blueprint
struct Stack<T> {
    data: Vec<T>,
}

impl<T> Stack<T> {
    fn push(&mut self, val: T) { self.data.push(val); }
    fn pop(&mut self) -> Option<T> { self.data.pop() }
}

// These usages create THREE SEPARATE concrete types:
let mut int_stack: Stack<i32> = Stack { data: vec![] };
let mut str_stack: Stack<String> = Stack { data: vec![] };
let mut float_stack: Stack<f64> = Stack { data: vec![] };

// The compiler physically generates three distinct structs:
//
//   Stack_i32   { data: Vec<i32>   }  — 24 bytes on stack
//   Stack_String { data: Vec<String> } — 24 bytes on stack
//   Stack_f64   { data: Vec<f64>   }  — 24 bytes on stack
//
// And three distinct push() implementations, three distinct pop() implementations.
// The source code is shared. The machine code is not.
```

Think of it like a **stamp and clay**: `Stack<T>` is the stamp — a pattern. `Stack<i32>` is the clay after stamping — the actual physical thing.

---

### Concrete vs Abstract — Side by Side Comparison

```rust
use std::fmt::Display;

// ── CONCRETE: the compiler knows everything ──────────────────────────

fn add_concrete(a: i32, b: i32) -> i32 {
    a + b
    // Compiler generates: mov eax, [a]; add eax, [b]; ret
    // Exact machine instruction known at compile time
}

// ── STATIC ABSTRACT (generic): unknown until instantiation ──────────

fn add_generic<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
    // NOT concrete at definition time
    // BECOMES concrete when called with T = i32, T = f64, etc.
    // Compiler generates separate machine code per T
}

// ── DYNAMIC ABSTRACT (trait object): unknown at runtime ─────────────

fn print_dynamic(val: &dyn Display) {
    println!("{}", val);
    // val is a FAT POINTER: (pointer to data, pointer to vtable)
    // vtable contains pointer to the correct Display::fmt for the actual type
    // At runtime, the CPU follows the vtable pointer to call the right function
    // This is ~1-3ns extra per call vs direct function call
}
```

---

### Why This Matters for Your HashMap Implementation

Looking back at your code:

```rust
pub struct HashMap<K, V> {
    slots: Vec<Slot<K, V>>,
    count: usize,
    capacity: usize,
}
```

`HashMap<K, V>` is **not a concrete type**. It's a type constructor — a function that takes two types and produces a type.

```
HashMap<K, V>         — abstract (template)
HashMap<String, i32>  — concrete (16 bytes of metadata + heap allocation)
HashMap<u64, Vec<u8>> — concrete (different layout, different machine code)
```

When you write:

```rust
let mut map: HashMap<String, i32> = HashMap::new();
```

The compiler:
1. Substitutes `K = String`, `V = i32` everywhere in the struct and all its impl methods
2. Verifies `String: Hash + Eq + Clone + Debug` ✓
3. Verifies `i32: Clone + Debug` ✓
4. Generates a concrete `HashMap_String_i32` struct with exact memory layout
5. Generates concrete machine code for every method you actually call

The moment K and V are known, the abstract becomes concrete, and Rust's zero-overhead guarantee is upheld. This is the entire engine behind the `where K: Hash + Eq` bounds — they are the **gate** that controls which concrete types are allowed to fill the template.