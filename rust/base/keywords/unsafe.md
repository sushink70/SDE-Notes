# The Complete Guide to `unsafe` in Rust
### From Fundamentals to Systems-Level Mastery

---

## Table of Contents
1. [The Mental Model: Rust's Safety Contract](#1-the-mental-model)
2. [What is `unsafe`?](#2-what-is-unsafe)
3. [The Five Unsafe Superpowers](#3-the-five-unsafe-superpowers)
4. [Raw Pointers — Deep Dive](#4-raw-pointers)
5. [Unsafe Functions & Blocks](#5-unsafe-functions--blocks)
6. [Unsafe Traits](#6-unsafe-traits)
7. [Mutable Static Variables](#7-mutable-static-variables)
8. [Foreign Function Interface (FFI)](#8-foreign-function-interface-ffi)
9. [Memory Layout & Alignment](#9-memory-layout--alignment)
10. [Safety Invariants & Undefined Behavior](#10-safety-invariants--undefined-behavior)
11. [Real-World Implementations](#11-real-world-implementations)
12. [Best Practices & Mental Models](#12-best-practices--mental-models)
13. [Cognitive Framework for Mastery](#13-cognitive-framework-for-mastery)

---

## 1. The Mental Model: Rust's Safety Contract

Before touching `unsafe`, you must understand **why Rust is safe by default**.

### The Ownership System — A Quick Refresh

Rust's compiler (the **borrow checker**) enforces these rules at compile time:
- Every value has exactly **one owner**
- References must always be **valid** (no dangling pointers)
- Either **one mutable** reference OR **many immutable** references — never both

```
         RUST MEMORY SAFETY MODEL
         ========================

  ┌─────────────────────────────────────────────┐
  │              COMPILE-TIME CHECKS             │
  │                                             │
  │   ┌──────────┐    ┌──────────┐             │
  │   │Ownership │    │ Lifetime │             │
  │   │  Rules   │───▶│ Checker  │             │
  │   └──────────┘    └──────────┘             │
  │         │               │                  │
  │         ▼               ▼                  │
  │   ┌──────────────────────────┐             │
  │   │    Borrow Checker        │             │
  │   │  (Guarantees no UB*)     │             │
  │   └──────────────────────────┘             │
  │         │                                  │
  │         ▼                                  │
  │   ✅ SAFE RUST — Zero UB Guaranteed        │
  └─────────────────────────────────────────────┘

  *UB = Undefined Behavior (the root of all evil in systems programming)
```

### The Problem: Some Things Are Legitimately Impossible in Safe Rust

Sometimes you NEED to:
- Implement your own memory allocator
- Call into C libraries
- Build a lock-free data structure
- Write OS kernels / device drivers
- Implement `Vec<T>` or `Rc<T>` themselves

These require **bypassing the borrow checker** — and that's exactly what `unsafe` is for.

```
         THE UNSAFE CONTRACT
         ===================

  Safe Rust:
  "The compiler PROVES your code is memory-safe."

  Unsafe Rust:
  "YOU promise the compiler your code is memory-safe.
   The compiler TRUSTS you and skips those checks."

  ┌─────────────────────────────────────────────┐
  │  "With great power comes great              │
  │   responsibility." — Rust Book              │
  │                                             │
  │  You become the borrow checker.             │
  │  You own the bugs.                          │
  └─────────────────────────────────────────────┘
```

---

## 2. What is `unsafe`?

The `unsafe` keyword is a **scope annotation** that says:
> "Inside this block/function/trait, I am opting out of certain compiler guarantees. I am manually ensuring correctness."

### Syntax Forms

```rust
// Form 1: unsafe BLOCK (most common)
unsafe {
    // dangerous operations here
}

// Form 2: unsafe FUNCTION
unsafe fn do_dangerous_thing() {
    // caller must uphold safety invariants
}

// Form 3: unsafe TRAIT implementation
unsafe impl Send for MyType {}

// Form 4: unsafe TRAIT declaration
unsafe trait DangerousTrait {}

// Form 5: unsafe on extern blocks (FFI)
extern "C" {
    fn c_function(x: i32) -> i32;
}
// calling it requires: unsafe { c_function(5) }
```

### What `unsafe` Does NOT Do

This is critical. `unsafe` does NOT:
- Turn off the borrow checker entirely
- Allow all Rust rules to be broken
- Make your code automatically incorrect

```
  WHAT unsafe UNLOCKS (only 5 things):
  =====================================

  ┌─────────────────────────────────────────┐
  │  1. Dereference raw pointers            │
  │  2. Call unsafe functions/methods       │
  │  3. Access/modify mutable statics       │
  │  4. Implement unsafe traits             │
  │  5. Access fields of unions             │
  └─────────────────────────────────────────┘

  Everything ELSE is still checked by the compiler,
  even inside unsafe blocks!
```

---

## 3. The Five Unsafe Superpowers

```
  THE 5 UNSAFE SUPERPOWERS
  =========================

  ┌──────────┐
  │  unsafe  │
  │  { ... } │
  └────┬─────┘
       │
       ├──▶ 1. *raw_ptr  (dereference raw pointer)
       │
       ├──▶ 2. unsafe fn()  (call unsafe function)
       │
       ├──▶ 3. static mut X  (access mutable static)
       │
       ├──▶ 4. unsafe impl Trait  (impl unsafe trait)
       │
       └──▶ 5. union.field  (access union field)
```

---

## 4. Raw Pointers — Deep Dive

### What is a Pointer?

A **pointer** is a variable that holds a **memory address** — it "points to" where data lives in RAM.

In C/C++, you use `int* p` freely. In safe Rust, you use references (`&T`, `&mut T`) which are **always valid** by compiler guarantee.

**Raw pointers** are Rust's equivalent of C pointers — no safety guarantees.

### The Two Raw Pointer Types

```rust
*const T   // immutable raw pointer (like const T* in C)
*mut T     // mutable raw pointer   (like T* in C)
```

**Key vocabulary:**
- `*const T` — you cannot write through this pointer (but can read)
- `*mut T` — you can both read and write
- The `*` here is part of the TYPE, not a dereference operator

### Memory Visualization

```
  RAM MEMORY LAYOUT
  =================

  Address  │  Value
  ─────────┼─────────────
  0x1000   │   42        ◀──── i32 value lives here
  0x1001   │   ...
  0x1002   │   ...
  0x1003   │   ...
  0x1004   │   0x10 00   ◀──── raw pointer *const i32
  0x1005   │   (cont.)         stores address 0x1000
  0x1006   │   (cont.)
  0x1007   │   (cont.)

  let x: i32 = 42;
  let p: *const i32 = &x as *const i32;
         │                     │
         │                     └── cast reference to raw pointer
         └── p holds address 0x1000
             (*p) reads value 42 from address 0x1000
```

### Creating Raw Pointers (Safe!)

Creating a raw pointer is SAFE. Only **dereferencing** requires `unsafe`.

```rust
fn main() {
    let x: i32 = 42;
    let y: i32 = 99;

    // Creating raw pointers — SAFE, no unsafe block needed
    let p_const: *const i32 = &x;           // immutable raw pointer
    let p_mut: *mut i32 = &mut x.clone() as *mut i32; // mutable raw pointer

    // You can even create a dangling pointer — SAFE to create!
    let dangling: *const i32 = 0x1234 as *const i32; // arbitrary address

    // But DEREFERENCING requires unsafe
    unsafe {
        println!("x via raw pointer: {}", *p_const); // dereference
    }
}
```

### The `as` Cast for Raw Pointers

```rust
let x = 42i32;

// Reference → Raw Pointer (most common)
let p1: *const i32 = &x as *const i32;
// or shorter:
let p2 = &x as *const i32;

// Mutable reference → mutable raw pointer
let mut y = 99i32;
let p3: *mut i32 = &mut y as *mut i32;

// Using addr_of! macro (preferred in modern Rust — avoids intermediate &mut)
use std::ptr;
let p4 = ptr::addr_of!(x);      // *const i32
let p5 = ptr::addr_of_mut!(y);  // *mut i32
```

### Pointer Arithmetic — The Dangerous Part

```
  POINTER ARITHMETIC VISUALIZATION
  ==================================

  An array [10, 20, 30, 40] in memory:

  Address:  0x100  0x104  0x108  0x10C
            ┌────┐ ┌────┐ ┌────┐ ┌────┐
  Value:    │ 10 │ │ 20 │ │ 30 │ │ 40 │
            └────┘ └────┘ └────┘ └────┘
               ▲
               p (pointer to first element)

  p.add(1) → moves to 0x104 (next i32, 4 bytes forward)
  p.add(2) → moves to 0x108
  p.add(3) → moves to 0x10C
  p.add(4) → DANGER! Out of bounds — undefined behavior!
```

```rust
fn main() {
    let arr = [10i32, 20, 30, 40];
    let p: *const i32 = arr.as_ptr(); // pointer to first element

    unsafe {
        // Walk the array using pointer arithmetic
        for i in 0..4 {
            let val = *p.add(i); // p + (i * sizeof(i32))
            println!("arr[{}] = {}", i, val);
        }
    }
}
// Output:
// arr[0] = 10
// arr[1] = 20
// arr[2] = 30
// arr[3] = 40
```

### The `offset`, `add`, `sub` Methods

```rust
// p.add(n)    — moves forward n elements (not bytes!)
// p.sub(n)    — moves backward n elements
// p.offset(n) — signed version of add (can go negative)

let arr = [1u8, 2, 3, 4, 5];
let p = arr.as_ptr();

unsafe {
    assert_eq!(*p.add(2), 3); // third element
    assert_eq!(*p.add(0), 1); // first element

    let p_end = p.add(4);
    assert_eq!(*p_end, 5);    // last element
}
```

### Pointer Comparison and Arithmetic

```rust
let arr = [0u8; 10];
let start = arr.as_ptr();
let end = unsafe { start.add(10) };

// Measure distance between two pointers (in elements)
let distance = unsafe { end.offset_from(start) };
assert_eq!(distance, 10);

// Compare pointer addresses
assert!(end > start);  // pointer comparison
```

### Null Pointers

```rust
use std::ptr;

// Create a null pointer
let null_p: *const i32 = ptr::null();
let null_mut_p: *mut i32 = ptr::null_mut();

// ALWAYS check before dereferencing
if !null_p.is_null() {
    unsafe { println!("{}", *null_p); }
} else {
    println!("Pointer is null, skip dereference");
}
```

### Common Raw Pointer Pitfalls

```
  POINTER DANGER ZONES
  =====================

  1. DANGLING POINTER
  ───────────────────
  {
      let x = 42;
      let p = &x as *const i32;
  }  ← x is dropped here, p now points to garbage!
  unsafe { *p }  // ← UNDEFINED BEHAVIOR

  2. DOUBLE FREE
  ──────────────
  let p = Box::into_raw(Box::new(42));
  unsafe {
      drop(Box::from_raw(p));   // first free ✓
      drop(Box::from_raw(p));   // second free ✗ UB!
  }

  3. MISALIGNED ACCESS
  ─────────────────────
  let bytes = [0u8; 8];
  let p = bytes.as_ptr().add(1) as *const u32; // ← misaligned!
  unsafe { *p }  // u32 requires 4-byte alignment, not 1-byte offset

  4. ALIASING MUTABLE POINTERS
  ──────────────────────────────
  let mut x = 42;
  let p1 = &mut x as *mut i32;
  let p2 = &mut x as *mut i32;
  unsafe {
      *p1 = 10;   // Two mutable aliases — violates Rust aliasing rules!
      *p2 = 20;   // UB: compiler may reorder or eliminate writes
  }
```

---

## 5. Unsafe Functions & Blocks

### Unsafe Functions

An `unsafe fn` signals: **"I have preconditions the compiler cannot verify. You (the caller) must ensure them."**

```rust
/// # Safety
/// - `ptr` must be non-null
/// - `ptr` must point to a valid, initialized i32
/// - The memory must not be aliased mutably
unsafe fn read_i32(ptr: *const i32) -> i32 {
    *ptr  // dereference — safe here because WE guarantee the preconditions
}

fn main() {
    let x = 42i32;
    let p = &x as *const i32;

    // Caller must use unsafe and uphold the contract
    let val = unsafe { read_i32(p) };
    println!("{}", val); // 42
}
```

### The Safety Comment Convention

This is a professional standard in Rust codebases:

```rust
// When CALLING unsafe code, explain WHY it's safe:
let val = unsafe {
    // SAFETY: ptr was obtained from a live reference,
    // so it's non-null and valid for the lifetime of x.
    read_i32(p)
};

// When DECLARING unsafe fn, document preconditions:
/// # Safety
///
/// The caller must ensure:
/// - `ptr` is valid for reads
/// - `ptr` is properly aligned for `T`
/// - The memory at `ptr` is initialized
unsafe fn raw_read<T>(ptr: *const T) -> T {
    ptr.read()
}
```

### `ptr::read` and `ptr::write`

These are the fundamental building blocks:

```rust
use std::ptr;

fn main() {
    let x = 42i32;
    let p = &x as *const i32;

    // ptr::read — reads a value without moving (bitwise copy)
    let val: i32 = unsafe { ptr::read(p) };
    println!("{}", val); // 42

    // ptr::write — writes a value to a pointer
    let mut y = 0i32;
    let p_mut = &mut y as *mut i32;
    unsafe {
        ptr::write(p_mut, 99);
    }
    println!("{}", y); // 99
}
```

### `ptr::copy` and `ptr::copy_nonoverlapping`

These are Rust's equivalents of C's `memmove` and `memcpy`:

```rust
use std::ptr;

fn main() {
    let src = [1u8, 2, 3, 4, 5];
    let mut dst = [0u8; 5];

    unsafe {
        // Like memcpy — src and dst must NOT overlap
        ptr::copy_nonoverlapping(
            src.as_ptr(),   // source pointer
            dst.as_mut_ptr(), // destination pointer
            5,              // number of ELEMENTS (not bytes)
        );
    }

    assert_eq!(dst, [1, 2, 3, 4, 5]);
}
```

```
  ptr::copy_nonoverlapping visualization:
  ========================================

  src: [1][2][3][4][5]
        │  │  │  │  │
        ▼  ▼  ▼  ▼  ▼
  dst: [1][2][3][4][5]

  Regions must NOT overlap in memory.
  If they might overlap, use ptr::copy (= memmove).
```

### `mem::transmute` — The Nuclear Option

`transmute` reinterprets the raw bytes of one type as another type. It's one of the most dangerous operations in Rust.

```
  transmute<T, U> VISUALIZATION
  ==============================

  Takes bytes of type T, reinterprets them as type U.
  T and U must have the SAME SIZE.

  f32 value 1.0 in memory:
  Binary: 0 01111111 00000000000000000000000
  Hex:    0x3F800000

  transmute::<f32, u32>(1.0_f32) → 0x3F800000u32
  (same bytes, different type interpretation)
```

```rust
use std::mem;

fn main() {
    // Reinterpret f32 as u32 (same 4 bytes, different meaning)
    let float: f32 = 1.0;
    let bits: u32 = unsafe { mem::transmute(float) };
    println!("1.0f32 as bits: {:#010x}", bits); // 0x3f800000

    // Safer alternative for this specific case:
    let bits2 = float.to_bits(); // preferred!
    println!("Same result: {:#010x}", bits2);
}
```

**When transmute is useful (and dangerous):**

```rust
// DANGEROUS: Transmuting &T to &mut T — violates aliasing!
// This is UB if used incorrectly!
let x = 5i32;
let x_mut: &mut i32 = unsafe { mem::transmute(&x) }; // ← DANGEROUS

// USEFUL: Transmuting function pointers
type FnPtr = fn(i32) -> i32;
let func: FnPtr = |x| x + 1;
let raw: usize = unsafe { mem::transmute(func) };
let back: FnPtr = unsafe { mem::transmute(raw) };
assert_eq!(back(5), 6);
```

---

## 6. Unsafe Traits

### What Makes a Trait `unsafe`?

A trait is `unsafe` when **implementing it correctly requires invariants the compiler cannot check**.

The two most important unsafe traits in std are:

```
  THE MOST CRITICAL UNSAFE TRAITS
  =================================

  Send  — "It is safe to transfer ownership of this type
            across thread boundaries"

  Sync  — "It is safe to share a reference to this type
            across threads (i.e., &T is Send)"

  These are AUTO-TRAITS: the compiler implements them
  automatically for most types. You only need unsafe impl
  when you're doing something special.
```

### Example: Implementing `Send` Manually

```rust
use std::cell::UnsafeCell;

// A raw pointer wrapper that we want to send across threads
struct MyPtr(*mut i32);

// Raw pointers are NOT Send by default (compiler refuses)
// We manually assert this is safe by implementing Send
// SAFETY: We guarantee external synchronization (e.g., only
//         one thread uses this at a time via a mutex)
unsafe impl Send for MyPtr {}

fn main() {
    let mut x = 42i32;
    let ptr = MyPtr(&mut x as *mut i32);

    let handle = std::thread::spawn(move || {
        // ptr was "sent" here
        unsafe { *ptr.0 = 100; }
    });
    handle.join().unwrap();
    println!("{}", x); // 100 (potentially)
}
```

### Declaring Your Own Unsafe Trait

```rust
/// # Safety
///
/// Implementors must ensure that `as_bytes()` returns
/// a valid UTF-8 encoded byte slice.
unsafe trait ValidUtf8 {
    fn as_bytes(&self) -> &[u8];
}

struct MyStr(String);

// SAFETY: String is always valid UTF-8
unsafe impl ValidUtf8 for MyStr {
    fn as_bytes(&self) -> &[u8] {
        self.0.as_bytes()
    }
}
```

---

## 7. Mutable Static Variables

### What is a `static`?

A `static` variable lives for the **entire duration of the program** (static lifetime `'static`). It's stored in the BSS or data segment of the binary.

```
  MEMORY REGIONS
  ===============

  ┌─────────────────────────────┐  ← High address
  │         Stack               │  (local variables)
  ├─────────────────────────────┤
  │           ↓↑                │
  │         Heap                │  (Box, Vec, etc.)
  ├─────────────────────────────┤
  │    BSS / Data Segment       │  ← static variables live here
  ├─────────────────────────────┤
  │    Code Segment (text)      │  (compiled instructions)
  └─────────────────────────────┘  ← Low address
```

### Why `static mut` is Unsafe

If two threads access `static mut X` simultaneously without synchronization, that's a **data race** — undefined behavior.

```rust
// Global counter (BAD: no synchronization)
static mut COUNTER: u32 = 0;

fn increment() {
    unsafe {
        COUNTER += 1; // ← requires unsafe: potential data race
    }
}

fn get_count() -> u32 {
    unsafe { COUNTER } // ← requires unsafe
}

fn main() {
    increment();
    increment();
    println!("{}", get_count()); // 2
}
```

### The Safe Alternative: Atomic Types

```rust
use std::sync::atomic::{AtomicU32, Ordering};

// This is SAFE — atomics handle concurrent access
static COUNTER: AtomicU32 = AtomicU32::new(0);

fn increment() {
    COUNTER.fetch_add(1, Ordering::SeqCst);
}

fn get_count() -> u32 {
    COUNTER.load(Ordering::SeqCst)
}

fn main() {
    increment();
    increment();
    println!("{}", get_count()); // 2 — no unsafe needed!
}
```

### When `static mut` Is Justified

```rust
// Single-threaded embedded system with known access patterns
static mut HARDWARE_BUFFER: [u8; 1024] = [0; 1024];

// SAFETY: This function is called only from the main loop,
//         never from interrupt handlers concurrently.
unsafe fn fill_buffer(data: &[u8]) {
    let len = data.len().min(1024);
    HARDWARE_BUFFER[..len].copy_from_slice(&data[..len]);
}
```

---

## 8. Foreign Function Interface (FFI)

### What is FFI?

FFI (Foreign Function Interface) lets Rust **call functions written in other languages** (C, C++, assembly) and be called from them.

```
  FFI CALL FLOW
  ==============

  Rust Code                C Library (.so / .dll)
  ─────────────            ──────────────────────

  extern "C" {             int add(int a, int b) {
    fn add(                    return a + b;
      a: i32,            }
      b: i32
    ) -> i32;
  }
        │
        │  unsafe { add(3, 4) }
        │           │
        └───────────┴──▶ ABI boundary crossed
                          (calling convention: C)
```

### The ABI Concept

**ABI (Application Binary Interface)** = the agreement on HOW functions are called at the machine level:
- How arguments are passed (registers vs stack)
- How return values come back
- How the stack is managed

`extern "C"` means: use the C calling convention (the most universal).

### Basic FFI Example

```rust
// Tell Rust about an external C function
extern "C" {
    // This function exists in libc
    fn strlen(s: *const std::os::raw::c_char) -> usize;
    fn abs(x: std::os::raw::c_int) -> std::os::raw::c_int;
    fn sqrt(x: f64) -> f64;
}

fn main() {
    let result = unsafe { sqrt(16.0) };
    println!("sqrt(16) = {}", result); // 4.0

    let negative = -42i32;
    let positive = unsafe { abs(negative) };
    println!("|{}| = {}", negative, positive); // 42
}
```

### C Types in Rust

```rust
use std::os::raw::*;

// C type mappings:
// c_char   → i8  or u8  (char)
// c_short  → i16         (short)
// c_int    → i32         (int)
// c_long   → i32 or i64  (long — platform dependent!)
// c_float  → f32         (float)
// c_double → f64         (double)
// c_void   → ()          (void)

// Better: use libc crate for platform-correct mappings
```

### Exposing Rust to C

```rust
// Make this function callable from C
#[no_mangle]  // Don't mangle the function name (keep it "add")
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b  // Safe Rust inside!
}
```

### Linking to a C Library

```rust
// build.rs (build script)
fn main() {
    println!("cargo:rustc-link-lib=mylib");    // link to libmylib.so
    println!("cargo:rustc-link-search=/usr/lib"); // search path
}

// src/main.rs
#[link(name = "mylib")]
extern "C" {
    fn my_c_function(x: i32) -> i32;
}
```

### Real FFI: Calling C's `qsort`

```rust
use std::os::raw::{c_int, c_void};

extern "C" {
    fn qsort(
        base: *mut c_void,
        num: usize,
        size: usize,
        compare: Option<unsafe extern "C" fn(*const c_void, *const c_void) -> c_int>,
    );
}

// Comparison function with C ABI
unsafe extern "C" fn compare_i32(a: *const c_void, b: *const c_void) -> c_int {
    let a = *(a as *const i32);
    let b = *(b as *const i32);
    a.cmp(&b) as c_int
}

fn main() {
    let mut arr = [5i32, 2, 8, 1, 9, 3];

    unsafe {
        qsort(
            arr.as_mut_ptr() as *mut c_void,
            arr.len(),
            std::mem::size_of::<i32>(),
            Some(compare_i32),
        );
    }

    println!("{:?}", arr); // [1, 2, 3, 5, 8, 9]
}
```

---

## 9. Memory Layout & Alignment

### What is Alignment?

**Alignment** is a hardware constraint: some CPU architectures require data to be at addresses that are multiples of the data size.

```
  ALIGNMENT VISUALIZATION
  ========================

  An i32 (4 bytes) must start at address divisible by 4:

  Address: 0x00 0x01 0x02 0x03 0x04 0x05 0x06 0x07
           ┌────┬────┬────┬────┬────┬────┬────┬────┐
           │    │    │    │    │    │    │    │    │
           └────┴────┴────┴────┴────┴────┴────┴────┘
                                  ▲
           i32 at 0x04: ✓ VALID  (divisible by 4)

           i32 at 0x01: ✗ MISALIGNED (0x01 not divisible by 4)
                           → On some CPUs: crash/UB
                           → On x86: slow (split cache line)

  Alignment rules:
  ──────────────────────────
  u8/i8   → align = 1 (any address)
  u16/i16 → align = 2 (even addresses)
  u32/i32 → align = 4 (multiples of 4)
  u64/i64 → align = 8 (multiples of 8)
  f32     → align = 4
  f64     → align = 8
```

### Checking Layout at Runtime

```rust
use std::mem;

fn main() {
    // size_of: how many bytes a type takes
    println!("u8    size={} align={}", mem::size_of::<u8>(),    mem::align_of::<u8>());
    println!("u16   size={} align={}", mem::size_of::<u16>(),   mem::align_of::<u16>());
    println!("u32   size={} align={}", mem::size_of::<u32>(),   mem::align_of::<u32>());
    println!("u64   size={} align={}", mem::size_of::<u64>(),   mem::align_of::<u64>());
    println!("usize size={} align={}", mem::size_of::<usize>(), mem::align_of::<usize>());
}
// On 64-bit system:
// u8    size=1 align=1
// u16   size=2 align=2
// u32   size=4 align=4
// u64   size=8 align=8
// usize size=8 align=8
```

### Struct Layout and Padding

The compiler adds **padding** bytes to satisfy alignment requirements:

```rust
#[derive(Debug)]
struct Padded {
    a: u8,    // 1 byte
              // [3 bytes padding inserted by compiler]
    b: u32,   // 4 bytes (needs 4-byte alignment)
    c: u8,    // 1 byte
              // [3 bytes padding inserted]
              // Total: 12 bytes
}

#[derive(Debug)]
struct Packed {
    b: u32,   // 4 bytes
    a: u8,    // 1 byte
    c: u8,    // 1 byte
              // [2 bytes padding]
              // Total: 8 bytes (smaller! — reordered fields)
}

fn main() {
    println!("{}", std::mem::size_of::<Padded>()); // 12
    println!("{}", std::mem::size_of::<Packed>()); // 8
}
```

```
  STRUCT PADDING VISUALIZATION
  =============================

  struct Padded { a: u8, b: u32, c: u8 }

  Offset:  0    1    2    3    4    5    6    7    8    9   10   11
           ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
           │ a  │ ?? │ ?? │ ?? │       b (u32)     │ c  │ ?? │ ?? │ ?? │
           └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
            ^    ^^^^^^^^^      ^^^^^^^^^^^^^^^^^^^^^  ^   ^^^^^^^^^
            u8   3 padding      u32 (align-4)          u8  3 padding

  struct Packed { b: u32, a: u8, c: u8 }

  Offset:  0    1    2    3    4    5    6    7
           ┌────┬────┬────┬────┬────┬────┬────┬────┐
           │       b (u32)     │ a  │ c  │ ?? │ ?? │
           └────┴────┴────┴────┴────┴────┴────┴────┘
```

### `#[repr(C)]` — C-Compatible Layout

For FFI, you need structs with predictable layout:

```rust
// Rust's default layout: compiler may reorder fields!
struct RustLayout {
    a: u8,
    b: u32,
}

// #[repr(C)]: fields in declaration order, C rules apply
#[repr(C)]
struct CLayout {
    a: u8,
    // 3 bytes padding (to align b to 4)
    b: u32,
}

// #[repr(packed)]: NO padding (may cause misaligned access!)
#[repr(packed)]
struct PackedLayout {
    a: u8,
    b: u32, // starts at offset 1 — misaligned!
}

// #[repr(align(N))]: force minimum alignment
#[repr(align(64))]  // cache-line sized struct
struct CacheAligned {
    data: [u8; 64],
}
```

### Unions — Unsafe Memory Sharing

A `union` stores multiple fields at the **same memory location**. Reading the wrong field is UB.

```rust
// C equivalent: union { int i; float f; }
union FloatOrInt {
    i: i32,
    f: f32,
}

fn main() {
    let u = FloatOrInt { i: 0x3F800000 }; // bits of 1.0f32

    unsafe {
        println!("As i32: {}", u.i);  // 1065353216
        println!("As f32: {}", u.f);  // 1.0 (same bits!)
    }
}
```

```
  UNION MEMORY LAYOUT
  ====================

  union FloatOrInt { i: i32, f: f32 }
  Both fields share the SAME 4 bytes:

  ┌────────────────────┐
  │  0x3F 0x80 0x00 0x00 │
  └────────────────────┘
      interpreted as i32 → 1065353216
      interpreted as f32 → 1.0
```

---

## 10. Safety Invariants & Undefined Behavior

### What is Undefined Behavior (UB)?

UB means the compiler is allowed to do **anything** — generate incorrect code, delete your code, crash, work correctly by accident. There is no "defined" outcome.

```
  UNDEFINED BEHAVIOR — THE ROGUES GALLERY
  =========================================

  In Rust (inside unsafe blocks), UB can arise from:

  1. MEMORY SAFETY
     ├── Dereferencing null/dangling pointer
     ├── Accessing out-of-bounds memory
     ├── Use-after-free
     └── Double-free

  2. ALIASING RULES VIOLATION
     ├── Creating two &mut references to same data
     └── Mutating through *const T (except interior mutability)

  3. DATA RACES
     └── Accessing mut static from multiple threads without sync

  4. TYPE INVARIANTS
     ├── Invalid enum discriminant (e.g., bool with value 2)
     ├── Invalid UTF-8 in str
     └── Integer overflow (in release mode — wraps without notice)

  5. UNINITIALIZED MEMORY
     └── Reading from MaybeUninit without initializing first

  6. ALIGNMENT VIOLATIONS
     └── Dereferencing misaligned pointer
```

### Stacked Borrows — Rust's Aliasing Model

Understanding Rust's aliasing model is crucial for writing correct unsafe code:

```
  STACKED BORROWS (simplified)
  =============================

  At any point in time, memory has an "access stack":

  Read access: many &T can coexist
  Write access: ONLY ONE &mut T allowed, no &T simultaneously

  ┌──────────┐
  │  Memory  │
  │  cell x  │
  └──────────┘
       │
       ├── &x (read borrow 1)  ─┐
       ├── &x (read borrow 2)   │ Multiple readers: OK
       └── &x (read borrow 3)  ─┘

       OR

       └── &mut x (write borrow) — EXCLUSIVE, no other borrows!

  Violating this with raw pointers = UB
```

### `MaybeUninit<T>` — Uninitialized Memory

Never read uninitialized memory! Use `MaybeUninit` to handle it safely:

```rust
use std::mem::MaybeUninit;

fn main() {
    // Create uninitialized memory (NOT zero-initialized!)
    let mut x: MaybeUninit<i32> = MaybeUninit::uninit();

    // Initialize it
    unsafe {
        x.as_mut_ptr().write(42);
    }

    // Now safe to read
    let value = unsafe { x.assume_init() };
    println!("{}", value); // 42
}
```

**Real use: Initializing an array without running constructors:**

```rust
use std::mem::MaybeUninit;

fn create_array() -> [i32; 5] {
    // Can't do: let mut arr: [i32; 5] = uninitialized!
    // Use MaybeUninit instead:
    let mut arr: [MaybeUninit<i32>; 5] = unsafe {
        MaybeUninit::uninit().assume_init() // array of uninit is OK
    };

    for (i, elem) in arr.iter_mut().enumerate() {
        elem.write(i as i32 * 2); // 0, 2, 4, 6, 8
    }

    // SAFETY: all elements initialized above
    unsafe { std::mem::transmute::<_, [i32; 5]>(arr) }
}

fn main() {
    println!("{:?}", create_array()); // [0, 2, 4, 6, 8]
}
```

---

## 11. Real-World Implementations

### Implementation 1: A Simple Memory Allocator (Arena)

An arena allocator gives out memory from a pre-allocated buffer. No individual frees — all memory is reclaimed at once.

```rust
/// Arena allocator — allocates from a fixed buffer, no individual frees
pub struct Arena {
    buffer: Vec<u8>,
    offset: usize, // current free position
}

impl Arena {
    pub fn new(capacity: usize) -> Self {
        Arena {
            buffer: vec![0u8; capacity],
            offset: 0,
        }
    }

    /// Allocate `n` bytes with given alignment.
    /// Returns None if out of space.
    pub fn alloc<T>(&mut self) -> Option<*mut T> {
        let align = std::mem::align_of::<T>();
        let size  = std::mem::size_of::<T>();

        // Align the current offset
        let aligned = (self.offset + align - 1) & !(align - 1);

        if aligned + size > self.buffer.len() {
            return None; // out of space
        }

        let ptr = unsafe {
            self.buffer.as_mut_ptr().add(aligned) as *mut T
        };

        self.offset = aligned + size;
        Some(ptr)
    }

    /// Reset — "free" all memory at once
    pub fn reset(&mut self) {
        self.offset = 0;
    }
}

fn main() {
    let mut arena = Arena::new(1024);

    // Allocate an i32 in the arena
    let p = arena.alloc::<i32>().expect("OOM");
    unsafe {
        std::ptr::write(p, 42);
        println!("Allocated i32: {}", *p); // 42
    }

    // Allocate a u64
    let q = arena.alloc::<u64>().expect("OOM");
    unsafe {
        std::ptr::write(q, 12345678u64);
        println!("Allocated u64: {}", *q);
    }

    // Reset everything
    arena.reset();
    println!("Arena reset. offset = {}", arena.offset); // 0
}
```

```
  ARENA ALLOCATOR VISUALIZATION
  ==============================

  buffer: [0][0][0][0][0][0][0][0]...[0]  (1024 bytes)
           ▲
           offset=0 initially

  After alloc::<i32>():
  buffer: [42][42][42][42][0][0][0][0]...[0]
                            ▲
                            offset=4

  After alloc::<u64>():
  buffer: [42][42][42][42][X][X][X][X][X][X][X][X]...[0]
                                                  ▲
                                                  offset=12

  reset(): offset → 0, buffer untouched (data still there but "free")
```

### Implementation 2: Raw `Vec<T>` from Scratch

Understanding how `Vec<T>` works internally:

```rust
use std::alloc::{self, Layout};
use std::ptr::NonNull;
use std::mem;

/// A minimal Vec-like container built with unsafe
pub struct RawVec<T> {
    ptr: NonNull<T>,
    cap: usize,
    len: usize,
}

impl<T> RawVec<T> {
    pub fn new() -> Self {
        // For zero-sized types, use dangling pointer
        // For normal types, start with capacity 0
        RawVec {
            ptr: NonNull::dangling(),
            cap: 0,
            len: 0,
        }
    }

    /// Grow capacity by doubling
    fn grow(&mut self) {
        let new_cap = if self.cap == 0 { 1 } else { self.cap * 2 };
        let layout = Layout::array::<T>(new_cap).unwrap();

        let new_ptr = if self.cap == 0 {
            // First allocation
            unsafe { alloc::alloc(layout) }
        } else {
            // Reallocation
            let old_layout = Layout::array::<T>(self.cap).unwrap();
            unsafe {
                alloc::realloc(
                    self.ptr.as_ptr() as *mut u8,
                    old_layout,
                    layout.size(),
                )
            }
        };

        self.ptr = match NonNull::new(new_ptr as *mut T) {
            Some(p) => p,
            None => alloc::handle_alloc_error(layout),
        };
        self.cap = new_cap;
    }

    pub fn push(&mut self, val: T) {
        if self.len == self.cap {
            self.grow();
        }
        unsafe {
            // Write the value at the end
            self.ptr.as_ptr().add(self.len).write(val);
        }
        self.len += 1;
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        unsafe {
            // Read and return the last element
            Some(self.ptr.as_ptr().add(self.len).read())
        }
    }

    pub fn get(&self, index: usize) -> Option<&T> {
        if index >= self.len {
            return None;
        }
        unsafe {
            Some(&*self.ptr.as_ptr().add(index))
        }
    }
}

impl<T> Drop for RawVec<T> {
    fn drop(&mut self) {
        if self.cap == 0 { return; }

        // Drop all elements
        unsafe {
            for i in 0..self.len {
                self.ptr.as_ptr().add(i).drop_in_place();
            }
            // Deallocate the buffer
            let layout = Layout::array::<T>(self.cap).unwrap();
            alloc::dealloc(self.ptr.as_ptr() as *mut u8, layout);
        }
    }
}

fn main() {
    let mut v: RawVec<i32> = RawVec::new();
    v.push(10);
    v.push(20);
    v.push(30);

    println!("{:?}", v.get(0)); // Some(10)
    println!("{:?}", v.get(1)); // Some(20)
    println!("{:?}", v.pop());  // Some(30)
    println!("{:?}", v.pop());  // Some(20)
} // Drop is called here — memory freed
```

### Implementation 3: Interior Mutability with `UnsafeCell`

`UnsafeCell<T>` is the foundation of ALL interior mutability in Rust (`Cell`, `RefCell`, `Mutex`, etc.)

```rust
use std::cell::UnsafeCell;

/// A simplified Cell<T> — single-threaded interior mutability
pub struct MyCell<T> {
    value: UnsafeCell<T>,
}

// SAFETY: Cell is NOT Sync — only safe for single-threaded use
// (we explicitly don't implement Sync)
impl<T: Copy> MyCell<T> {
    pub fn new(val: T) -> Self {
        MyCell { value: UnsafeCell::new(val) }
    }

    pub fn get(&self) -> T {
        // SAFETY: single-threaded, no concurrent mutation
        unsafe { *self.value.get() }
    }

    pub fn set(&self, val: T) {
        // SAFETY: single-threaded, T: Copy so no drop issues
        unsafe { *self.value.get() = val; }
    }
}

fn main() {
    let cell = MyCell::new(42);
    println!("{}", cell.get()); // 42

    // Mutate via shared reference! (that's the point of Cell)
    cell.set(100);
    println!("{}", cell.get()); // 100
}
```

### Implementation 4: Lock-Free Stack (Atomic Pointer)

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

unsafe impl<T: Send> Send for LockFreeStack<T> {}
unsafe impl<T: Send> Sync for LockFreeStack<T> {}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }

    pub fn push(&self, data: T) {
        let node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));

        loop {
            let old_head = self.head.load(Ordering::Acquire);
            unsafe { (*node).next = old_head; }

            // Atomically replace head with new node
            match self.head.compare_exchange(
                old_head, node,
                Ordering::Release,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,  // success
                Err(_) => {},    // someone else pushed, retry
            }
        }
    }

    pub fn pop(&self) -> Option<T> {
        loop {
            let old_head = self.head.load(Ordering::Acquire);
            if old_head.is_null() {
                return None; // empty
            }

            let next = unsafe { (*old_head).next };

            match self.head.compare_exchange(
                old_head, next,
                Ordering::Release,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    // We own old_head now, reclaim it
                    let data = unsafe {
                        let node = Box::from_raw(old_head);
                        node.data
                    };
                    return Some(data);
                }
                Err(_) => {}, // retry
            }
        }
    }
}

impl<T> Drop for LockFreeStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {} // drain all elements
    }
}

fn main() {
    let stack = LockFreeStack::new();
    stack.push(1);
    stack.push(2);
    stack.push(3);

    println!("{:?}", stack.pop()); // Some(3) — LIFO
    println!("{:?}", stack.pop()); // Some(2)
    println!("{:?}", stack.pop()); // Some(1)
    println!("{:?}", stack.pop()); // None
}
```

### Implementation 5: Slice from Raw Parts

```rust
use std::slice;

fn main() {
    let arr = [1i32, 2, 3, 4, 5];
    let ptr = arr.as_ptr();
    let len = arr.len();

    // Reconstruct a slice from raw parts
    let slice: &[i32] = unsafe {
        // SAFETY: ptr is valid for `len` elements of i32,
        //         properly aligned, not mutably aliased
        slice::from_raw_parts(ptr, len)
    };

    println!("{:?}", slice); // [1, 2, 3, 4, 5]

    // Mutable version
    let mut arr2 = [5i32, 4, 3, 2, 1];
    let slice_mut: &mut [i32] = unsafe {
        slice::from_raw_parts_mut(arr2.as_mut_ptr(), arr2.len())
    };
    slice_mut.sort();
    println!("{:?}", arr2); // [1, 2, 3, 4, 5]
}
```

### Implementation 6: String from Raw UTF-8

```rust
use std::str;

fn main() {
    // Valid UTF-8 bytes: "Hello"
    let bytes: &[u8] = &[72, 101, 108, 108, 111]; // "Hello"

    // Safe version (checks UTF-8):
    let s = str::from_utf8(bytes).unwrap(); // Returns Result
    println!("{}", s);

    // Unsafe version (no UTF-8 check — you guarantee it's valid):
    let s_unsafe: &str = unsafe {
        // SAFETY: bytes is valid UTF-8 ("Hello")
        str::from_utf8_unchecked(bytes)
    };
    println!("{}", s_unsafe);
}
```

---

## 12. Best Practices & Mental Models

### The Encapsulation Principle

```
  GOLDEN RULE OF UNSAFE
  ======================

  Unsafe code should be ENCAPSULATED inside safe abstractions.
  The public API should be SAFE to use.

  ┌─────────────────────────────────────────┐
  │           SAFE PUBLIC API               │
  │                                         │
  │  fn push(&mut self, val: T)  ← SAFE    │
  │  fn pop(&mut self) -> T      ← SAFE    │
  │  fn get(&self, i: usize)     ← SAFE    │
  │         │                               │
  │    ┌────▼─────────────────────┐         │
  │    │   UNSAFE INTERNALS       │         │
  │    │   (raw pointers,         │         │
  │    │    ptr arithmetic, etc.) │         │
  │    └──────────────────────────┘         │
  └─────────────────────────────────────────┘

  Users of your library NEVER need to write unsafe!
```

### The Minimal Unsafe Principle

```
  MINIMIZE UNSAFE SURFACE AREA
  ==============================

  BAD: Large unsafe blocks
  ─────────────────────────
  unsafe {
      setup_pointers();
      compute_something();    // ← this doesn't need unsafe!
      check_results();        // ← this doesn't need unsafe!
      final_deref(*ptr);
  }

  GOOD: Tiny, precise unsafe blocks
  ──────────────────────────────────
  setup_pointers_safe();    // refactored to safe
  let result = compute_something(); // no unsafe
  check_results(result);    // no unsafe
  unsafe { final_deref(*ptr); } // only what needs unsafe
```

### The Verification Checklist

Before every `unsafe` block, ask:

```
  UNSAFE SAFETY CHECKLIST
  ========================

  For raw pointer dereference:
  □ Is the pointer non-null?
  □ Was it obtained from a valid allocation?
  □ Is the allocation still live (not freed)?
  □ Is it properly aligned for T?
  □ Is the memory initialized?
  □ Is there no aliasing mutable borrow?
  □ Is the pointed-to data still valid T?

  For FFI calls:
  □ Are all arguments the correct types?
  □ Do argument sizes match C types on this platform?
  □ Is the C function thread-safe (if called from multiple threads)?
  □ Does the C function have any special calling conventions?

  For unsafe trait implementations:
  □ Do I truly satisfy ALL invariants the trait requires?
  □ Does my type implement Send only if truly thread-safe?
  □ Does my type implement Sync only if &T is thread-safe?
```

### Using `Miri` to Catch UB

Miri is a Rust interpreter that detects undefined behavior:

```bash
# Install Miri
rustup component add miri

# Run your tests under Miri
cargo miri test

# Run a specific binary
cargo miri run
```

Miri can detect:
- Out-of-bounds memory accesses
- Use-after-free
- Invalid use of uninitialized data
- Violation of the stacked borrows model
- Data races (with some limitations)

### The `NonNull<T>` Pattern

Prefer `NonNull<T>` over `*mut T` when the pointer should never be null:

```rust
use std::ptr::NonNull;

struct MyBox<T> {
    ptr: NonNull<T>, // guaranteed non-null
}

impl<T> MyBox<T> {
    fn new(val: T) -> Self {
        let boxed = Box::new(val);
        MyBox {
            ptr: NonNull::new(Box::into_raw(boxed))
                .expect("Box::into_raw never returns null"),
        }
    }

    fn get(&self) -> &T {
        unsafe { self.ptr.as_ref() }
    }
}

impl<T> Drop for MyBox<T> {
    fn drop(&mut self) {
        unsafe {
            drop(Box::from_raw(self.ptr.as_ptr()));
        }
    }
}
```

---

## 13. Cognitive Framework for Mastery

### Mental Model: The Three Layers

```
  THE THREE LAYERS OF UNSAFE MASTERY
  =====================================

  Layer 3: DESIGN
  ───────────────
  "Why do I need unsafe here?"
  "Can I redesign to avoid it?"
  "What invariants must hold?"

  Layer 2: VERIFICATION
  ──────────────────────
  "Is my unsafe code ACTUALLY safe?"
  "What are all the ways this could break?"
  "Have I documented the safety contract?"

  Layer 1: MECHANICS
  ───────────────────
  "How do raw pointers work?"
  "What is UB?"
  "What does this instruction do?"

  Master Layer 1 first, then 2, then 3.
```

### Deliberate Practice Protocol for `unsafe`

1. **Implement std types from scratch** — `Vec<T>`, `Box<T>`, `Rc<T>`, `Cell<T>`
2. **Read std source code** — `std::vec`, `std::collections::HashMap`
3. **Use Miri on every unsafe block** you write
4. **Read Rustonomicon** — the official unsafe Rust guide
5. **Study real-world crates** — `crossbeam`, `rayon`, `parking_lot`

### Pattern Recognition Guide

```
  PATTERN → UNSAFE TOOL MAPPING
  ================================

  Need to...                    → Use...
  ──────────────────────────────────────────────────────
  Implement allocator           → alloc::alloc, dealloc
  Share data between threads    → unsafe impl Send/Sync
  Interior mutability           → UnsafeCell<T>
  C interop                     → extern "C", FFI
  Zero-cost abstraction         → ptr::read, ptr::write
  Type punning                  → mem::transmute
  Uninitialized buffers         → MaybeUninit<T>
  Custom data structures        → NonNull<T>, raw pointers
  Performance-critical copy     → ptr::copy_nonoverlapping
  Slice from pointer            → slice::from_raw_parts
```

### The Rustonomicon

The official deep-dive into unsafe Rust:
```
https://doc.rust-lang.org/nomicon/
```

Topics covered beyond this guide:
- Exception safety
- Phantom data and variance
- Subtyping and lifetime variance
- The full stacked borrows model
- Writing allocators
- Implementing `Drop` correctly

---

## Summary Diagram: The `unsafe` Ecosystem

```
                    RUST SAFETY ECOSYSTEM
                    ======================

  ┌─────────────────────────────────────────────────────────┐
  │                      SAFE RUST                          │
  │                                                         │
  │    Box<T>  Vec<T>  Rc<T>  Arc<T>  Mutex<T>             │
  │    Cell<T>  RefCell<T>  RwLock<T>                       │
  │                   │                                     │
  │    These are built ON TOP of:                           │
  └───────────────────┼─────────────────────────────────────┘
                      │
  ┌───────────────────▼─────────────────────────────────────┐
  │                   UNSAFE PRIMITIVES                     │
  │                                                         │
  │   *const T   *mut T   NonNull<T>   UnsafeCell<T>        │
  │   mem::transmute  ptr::read/write  MaybeUninit<T>       │
  │   alloc::alloc/dealloc  extern "C"  static mut          │
  │   slice::from_raw_parts  unsafe fn  unsafe trait        │
  └─────────────────────────────────────────────────────────┘

  FLOW OF TRUST:
  Safe API (users trust it) ← Unsafe internals ← You verify invariants
```

---

*"The purpose of unsafe is not to escape safety — it is to implement safety where the compiler cannot see it."*

*Train with discipline. Write every `// SAFETY:` comment as if your future self will debug a crash caused by missing it. Because they will.*

Here's your complete guide. Let me give you the intellectual map of what's inside:

---

## What This Guide Covers

**Conceptual Foundation** — Before any code, you learn *why* `unsafe` exists. Rust's safety guarantees are compiler-proven contracts. `unsafe` means *you* become the prover. That mental shift is everything.

**The 5 Superpowers** — `unsafe` unlocks exactly 5 things and nothing more. The borrow checker still operates inside unsafe blocks for everything else. This is a common misconception.

**Raw Pointers (`*const T` / `*mut T`)** — The deepest section. Covers creation, dereferencing, pointer arithmetic (`add`, `sub`, `offset`), null checks, `ptr::read/write/copy`, `mem::transmute`, and every major pitfall with ASCII memory diagrams.

**Unsafe Functions & Traits** — How to declare safety contracts via `/// # Safety` docs and `unsafe impl Send/Sync`.

**Mutable Statics** — Why they're dangerous, when they're justified, and the atomic-based safe alternative.

**FFI** — Calling C from Rust and Rust from C. ABI explained. Real example using C's `qsort`.

**Memory Layout & Alignment** — Padding, `#[repr(C)]`, unions, and why misalignment causes UB.

**6 Real-World Implementations:**
1. Arena allocator
2. Raw `Vec<T>` from scratch (with `alloc::alloc`)
3. `Cell<T>` using `UnsafeCell`
4. Lock-free stack with atomics
5. Slice from raw parts
6. `str` from raw UTF-8

**Best Practices** — The encapsulation principle, minimal unsafe surface area, the safety checklist, `NonNull<T>`, and using `Miri` to catch UB.

---

**Your next step:** Implement `Box<T>` from scratch using `alloc::alloc` — that single exercise will solidify 80% of this guide.