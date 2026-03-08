# 🦀 The Comprehensive Guide to `union` in Rust
### From Zero to Expert — Deep Concepts, Real-World Implementations

---

## Table of Contents

1. [Mental Model: What Problem Does `union` Solve?](#1-mental-model)
2. [Memory Fundamentals — Before We Touch Rust](#2-memory-fundamentals)
3. [What Is a Union? (C Foundation)](#3-what-is-a-union)
4. [Rust `union` Syntax & Rules](#4-rust-union-syntax--rules)
5. [Memory Layout & Representation](#5-memory-layout--representation)
6. [Why `unsafe`? The Core Safety Argument](#6-why-unsafe)
7. [Union vs Enum vs Struct — Decision Tree](#7-union-vs-enum-vs-struct)
8. [Fields, Access, and Initialization](#8-fields-access-and-initialization)
9. [Drop Behavior & Ownership in Unions](#9-drop-behavior--ownership)
10. [Pattern Matching on Unions](#10-pattern-matching)
11. [Derive Macros & Trait Implementations](#11-derive-macros--traits)
12. [Tagged Unions (Manual Discriminant)](#12-tagged-unions)
13. [FFI — Foreign Function Interface (Primary Use Case)](#13-ffi--foreign-function-interface)
14. [Real-World Implementation: Bitfield Manipulation](#14-bitfield-manipulation)
15. [Real-World Implementation: Interpreter Value Types](#15-interpreter-value-types)
16. [Real-World Implementation: Network Packet Parsing](#16-network-packet-parsing)
17. [Real-World Implementation: SIMD / Low-Level Math](#17-simd--low-level-math)
18. [Union vs `std::mem::transmute`](#18-union-vs-transmute)
19. [Common Pitfalls & Anti-Patterns](#19-common-pitfalls)
20. [Performance Analysis](#20-performance-analysis)
21. [Mental Models & Cognitive Frameworks](#21-mental-models)
22. [Summary Cheat Sheet](#22-summary-cheat-sheet)

---

## 1. Mental Model

### The Overlapping Memory Problem

Imagine you have a house with ONE room. That room can be configured as:
- A bedroom (bed, pillows)
- A study (desk, chair, books)
- A gym (treadmill, weights)

At any moment, the room holds ONE configuration. You decide what it is — the house doesn't track it for you. If you walk in expecting a bedroom but the last person set it up as a gym, you'll trip over a treadmill.

**This is exactly what a `union` is.**

A union is a single chunk of memory that can be **interpreted** as different types, one at a time. The programmer is responsible for knowing which "interpretation" is currently valid.

```
STRUCT (separate rooms — all exist simultaneously):
┌─────────┬─────────┬─────────┐
│ field_a │ field_b │ field_c │
│  4 bytes│  4 bytes│  4 bytes│  = 12 bytes total
└─────────┴─────────┴─────────┘

UNION (one room — only one valid at a time):
┌─────────────────────────────┐
│  field_a  OR  field_b  OR   │
│         field_c             │  = max(4,4,4) = 4 bytes total
└─────────────────────────────┘
```

**Key Insight:** The power is **memory efficiency** and **reinterpretation** — the exact same bytes, read through different lenses.

---

## 2. Memory Fundamentals

> Before unions make sense, you need to understand how memory works.

### 2.1 What Is Memory?

Memory (RAM) is a flat array of bytes. Each byte has an **address** (a number, like a house number on a street).

```
Address:  0x00  0x01  0x02  0x03  0x04  0x05  0x06  0x07
          ┌────┬────┬────┬────┬────┬────┬────┬────┐
Value:    │ FF │ 00 │ A3 │ 7B │ 12 │ 00 │ 00 │ 00 │
          └────┴────┴────┴────┴────┴────┴────┴────┘
```

These bytes mean **nothing** without a type. The type tells the CPU how to interpret them.

### 2.2 Type Is an Interpretation

The bytes `FF 00 00 00` can mean:
- `i32` → -1 (two's complement)  
- `u32` → 255  
- `f32` → 3.57e-43 (IEEE 754)  
- `[u8; 4]` → [255, 0, 0, 0]  
- `char` → invalid (not a valid Unicode scalar)

**A union lets you choose the interpretation at access time.**

### 2.3 Alignment

Every type has an **alignment requirement** — the address where it must start must be divisible by its alignment.

```
u8  → alignment 1 (any address)
u16 → alignment 2 (address divisible by 2)
u32 → alignment 4 (address divisible by 4)
u64 → alignment 8 (address divisible by 8)
```

A union's alignment = the **maximum alignment** of all its fields.

---

## 3. What Is a Union? (C Foundation)

In C, unions were designed for **memory-efficient data structures** before modern memory was cheap.

```c
// C union
union Payload {
    int   integer;   // 4 bytes
    float floating;  // 4 bytes
    char  bytes[4];  // 4 bytes
};
// sizeof(union Payload) == 4 (not 12!)
```

**C gives zero safety guarantees.** Reading the wrong field is undefined behavior — you get garbage or worse.

Rust inherits this concept but:
1. Makes unsafe access **explicit** with the `unsafe` keyword
2. Adds compile-time restrictions (no non-`Copy` fields without care)
3. Allows `Drop` with explicit rules
4. Integrates into the ownership/borrow system

---

## 4. Rust `union` Syntax & Rules

### 4.1 Basic Declaration

```rust
// Simplest possible union
union MyUnion {
    integer: i32,
    floating: f32,
}
```

### 4.2 Complete Syntax Reference

```rust
// Full syntax with visibility, generics, where clause
#[repr(C)]                          // Optional: C-compatible layout
pub union MyUnion<T: Copy> {        // Fields must be Copy (or ManuallyDrop)
    pub field_a: i32,               // visibility is per-field
    pub field_b: f32,
    pub field_c: T,
}
```

### 4.3 Compile-Time Rules

```
RULE 1: Fields must implement Copy — OR — be wrapped in ManuallyDrop<T>
RULE 2: Reading a field requires `unsafe` block
RULE 3: Writing a field is safe (it's just storing bytes)
RULE 4: Union itself can be created safely (all-zero or field-init)
RULE 5: References to union fields are valid, but reading is unsafe
```

### 4.4 Why Must Fields Be `Copy`?

```
If a field is not Copy (e.g., String, Vec<T>), it has a destructor (Drop).
When you overwrite a union field, Rust doesn't know which field was "active"
to drop. You'd either:
  - Double-drop the old value (use-after-free)
  - Never drop it (memory leak)
ManuallyDrop<T> tells Rust: "I'll handle Drop myself."
```

### 4.5 Full Example with ManuallyDrop

```rust
use std::mem::ManuallyDrop;

union StringOrInt {
    text:    ManuallyDrop<String>,  // heap-allocated, has Drop
    integer: i64,
}

fn main() {
    // Initialize with an integer
    let mut u = StringOrInt { integer: 42 };

    // Safe to write
    unsafe {
        u.integer = 100;
    }

    // To use String variant:
    let mut u2 = StringOrInt {
        text: ManuallyDrop::new(String::from("hello")),
    };

    // Must manually drop when done!
    unsafe {
        ManuallyDrop::drop(&mut u2.text);
        // Now u2.text is invalid — don't touch it
    }
}
```

---

## 5. Memory Layout & Representation

### 5.1 Size = Largest Field

```rust
union Example {
    a: u8,   // 1 byte
    b: u32,  // 4 bytes
    c: u64,  // 8 bytes
}
// std::mem::size_of::<Example>() == 8
```

```
Memory layout of Example:
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ b0 │ b1 │ b2 │ b3 │ b4 │ b5 │ b6 │ b7 │   8 bytes
└────┴────┴────┴────┴────┴────┴────┴────┘
  ^
  └── field `a` (u8) reads only this byte

  ^─────────────^
  └── field `b` (u32) reads these 4 bytes

  ^───────────────────────────────────^
  └── field `c` (u64) reads all 8 bytes
```

### 5.2 Alignment = Maximum Field Alignment

```rust
union Aligned {
    x: u8,   // align 1
    y: u32,  // align 4
}
// Union alignment = 4 (max of 1 and 4)
// Union size     = 4 (padded to alignment)
```

### 5.3 `#[repr(C)]` vs Default

```rust
// Default Rust layout (may be reordered, optimized):
union RustDefault {
    a: u32,
    b: u64,
}

// C-compatible layout (guaranteed field order, standard ABI):
#[repr(C)]
union CCompat {
    a: u32,
    b: u64,
}
```

**When to use `#[repr(C)]`:**
- FFI with C libraries
- When memory layout must be predictable and stable
- When writing network protocols or binary formats

### 5.4 ASCII Visualization: Byte Reinterpretation

```
union FloatBits { i: u32, f: f32 }

Write f = 1.0f32:
IEEE 754 representation of 1.0 = 0x3F800000

Memory: ┌────────────────────────┐
        │ 00 | 00 | 80 | 3F     │  (little-endian)
        └────────────────────────┘

Read as u32:
        → 0x3F800000 = 1_065_353_216

Read as f32:
        → 1.0

Same bytes, two valid interpretations!
```

---

## 6. Why `unsafe`?

### The Core Safety Argument

Rust's safety guarantee is: **the compiler ensures every memory access is valid**.

For unions, the compiler **cannot** verify:
- Which field was last written
- Whether the bytes currently stored are a valid representation of the type you're reading

```
Valid u32: any 4 bytes (all 2^32 values are valid)
Valid bool: only 0x00 or 0x01 (other bytes = undefined behavior)
Valid char: only valid Unicode scalar values
Valid &T:   must be a non-null, aligned, valid pointer
```

**If you write `u32` bytes and read them as `bool`, you might read `0x02` — which is not a valid `bool`. This is Undefined Behavior (UB).**

Rust forces you to use `unsafe` to acknowledge: *"I know what I'm doing. I've verified the invariants manually."*

```
SAFE READ conditions (all must hold):
┌─────────────────────────────────────────────────────┐
│ 1. The field you're reading was the LAST one written │
│ 2. The bytes are a valid representation of that type │
│ 3. No concurrent mutation is occurring               │
│ 4. The union hasn't been moved invalidly             │
└─────────────────────────────────────────────────────┘
```

---

## 7. Union vs Enum vs Struct — Decision Tree

```
You need multiple types in one variable...

                    ┌─────────────────────────┐
                    │ Do you need to know      │
                    │ WHICH variant is active? │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┴────────────────┐
             YES                                NO
              │                                  │
              ▼                                  ▼
    ┌──────────────────┐              ┌───────────────────┐
    │ Use ENUM         │              │ Are you doing FFI  │
    │                  │              │ or need C ABI?     │
    │ Safe, idiomatic, │              └────────┬──────────┘
    │ zero runtime     │                       │
    │ overhead for tag │         ┌─────────────┴──────────┐
    └──────────────────┘        YES                       NO
                                 │                         │
                                 ▼                         ▼
                       ┌──────────────────┐    ┌──────────────────────┐
                       │ Use UNION        │    │ Is performance and    │
                       │ with #[repr(C)]  │    │ memory-efficiency     │
                       │                  │    │ absolutely critical?  │
                       │ For C interop,   │    └──────────┬───────────┘
                       │ syscall structs, │               │
                       │ hardware types   │    ┌──────────┴──────────┐
                       └──────────────────┘   YES                   NO
                                               │                      │
                                               ▼                      ▼
                                     ┌──────────────────┐  ┌──────────────────┐
                                     │ Use UNION        │  │ Use ENUM or      │
                                     │ (manual tagged)  │  │ Box<dyn Trait>   │
                                     │ with unsafe      │  │ (safe, flexible) │
                                     └──────────────────┘  └──────────────────┘
```

### Comparison Table

```
┌──────────────┬────────────┬────────────┬────────────────────────┐
│ Feature      │ struct     │ enum       │ union                  │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ Memory       │ sum of     │ max variant│ max field size         │
│              │ all fields │ + tag      │ (no tag overhead)      │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ Type safety  │ Full       │ Full       │ None (manual)          │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ unsafe req.  │ No         │ No         │ Yes (for reads)        │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ Pattern match│ Yes        │ Yes        │ Limited                │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ FFI compat   │ With repr  │ Limited    │ With repr(C)           │
├──────────────┼────────────┼────────────┼────────────────────────┤
│ Drop support │ Auto       │ Auto       │ Manual (ManuallyDrop)  │
└──────────────┴────────────┴────────────┴────────────────────────┘
```

---

## 8. Fields, Access, and Initialization

### 8.1 Initialization — All Patterns

```rust
union Data {
    integer: i32,
    bytes:   [u8; 4],
}

// Pattern 1: Initialize via a specific field
let d1 = Data { integer: 0xFF000000u32 as i32 };

// Pattern 2: Initialize via another field
let d2 = Data { bytes: [0xDE, 0xAD, 0xBE, 0xEF] };

// Pattern 3: Zero-initialized (all bytes are 0)
let d3: Data = unsafe { std::mem::zeroed() };

// Pattern 4: Uninitialized (DANGEROUS — only for FFI buffers)
let d4: Data = unsafe { std::mem::MaybeUninit::uninit().assume_init() };
```

### 8.2 Reading Fields — Always Unsafe

```rust
union FloatBits {
    f: f32,
    i: u32,
}

let fb = FloatBits { f: 3.14 };

// Reading requires unsafe
let bits: u32 = unsafe { fb.i };
println!("3.14 as bits: 0x{:08X}", bits); // 0x4048F5C3

// Getting a reference to a field
let ref_to_f: &f32 = unsafe { &fb.f };  // also unsafe
```

### 8.3 Writing Fields — Safe!

```rust
let mut fb = FloatBits { f: 1.0 };

// Writing is SAFE — you're just storing bytes
fb.f = 2.71828;
fb.i = 0;          // safe: overwrite with integer interpretation
```

**Why is writing safe but reading unsafe?**

```
WRITE: You're committing new bytes. Whatever was there before
       is simply overwritten. No invariant can be violated
       by writing (you're setting up a new state).

READ:  You're interpreting existing bytes as a specific type.
       If those bytes don't satisfy that type's validity
       invariants, you get UB. Only YOU know if the bytes
       are currently valid for the type you're reading.
```

### 8.4 Borrowing Rules

```rust
union Example { a: i32, b: f32 }
let mut e = Example { a: 10 };

// You can't have mutable + immutable borrow simultaneously:
let ra = unsafe { &e.a };
// let rb = &mut e.b;  // ERROR: can't borrow mutably while borrowed

// But you CAN borrow one field immutably multiple times:
let ra1 = unsafe { &e.a };
let ra2 = unsafe { &e.a };  // OK
```

---

## 9. Drop Behavior & Ownership

### 9.1 The Drop Problem

```
Problem: When a union goes out of scope, Rust calls Drop.
         But DROP WHICH FIELD?

         Rust doesn't know → Rust refuses to auto-drop
         if any field has a non-trivial Drop.
```

```rust
union Bad {
    s: String,  // ERROR: String has Drop
    i: i32,
}
// Compile error: unions cannot contain fields that may need dropping
```

### 9.2 Solution: `ManuallyDrop<T>`

```rust
use std::mem::ManuallyDrop;

union Tagged {
    text:    ManuallyDrop<String>,
    integer: i64,
}

// You are now responsible for dropping manually:
fn use_union() {
    let mut u = Tagged {
        text: ManuallyDrop::new(String::from("world")),
    };

    // Do something with text...
    unsafe {
        println!("{}", *u.text);
    }

    // YOU must drop it!
    unsafe {
        ManuallyDrop::drop(&mut u.text);
    }
    // From this point, u.text is INVALID. Never read it again.
}
```

### 9.3 Ownership Flow Diagram

```
TaggedUnion created with `text` variant:
┌─────────────────────────────────┐
│ text: ManuallyDrop<String>      │ ← String on heap: "hello"
│ (integer bytes: [72 65 6C 6C])  │
└─────────────────────────────────┘

Switching to integer variant:
┌─────────────────────────────────┐
│ integer: i64 = 42               │ ← overwrite bytes
│ (text variant now INVALID)      │ ← String LEAKED if not dropped first!
└─────────────────────────────────┘

CORRECT approach:
1. Drop old variant manually
2. Write new variant
3. Update discriminant (if using tagged union)
```

---

## 10. Pattern Matching

### 10.1 Unions in `match`

Pattern matching on unions is **limited** — you can match only a single field at a time:

```rust
union IntOrFloat {
    i: i32,
    f: f32,
}

let u = IntOrFloat { i: 42 };

// match on a union field (unsafe)
unsafe {
    match u.i {
        0     => println!("zero"),
        1..=9 => println!("single digit"),
        _     => println!("other"),
    }
}
```

### 10.2 You Cannot Destructure Multiple Fields

```rust
// This is NOT valid:
// let IntOrFloat { i, f } = u;  // ERROR

// You access one field at a time:
let i_val = unsafe { u.i };
let f_val = unsafe { u.f };
// (but only one is valid at any time!)
```

### 10.3 Binding by Reference

```rust
union U { a: u32, b: u16 }
let u = U { a: 0xDEADBEEF };

unsafe {
    if let U { a: ref val } = u {
        println!("a = 0x{:X}", val);
    }
}
```

---

## 11. Derive Macros & Traits

### 11.1 What You Can Derive

```rust
#[derive(Copy, Clone)]  // ✓ Allowed if all fields are Copy
union Simple {
    a: u32,
    b: f32,
}

// Debug — NOT auto-derivable on unions (which field to print?)
// Eq, PartialEq — NOT auto-derivable (same reason)
// Hash — NOT auto-derivable
```

### 11.2 Manual Debug Implementation

```rust
use std::fmt;

union Data {
    integer: i32,
    float_val: f32,
}

impl fmt::Debug for Data {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // We must choose — let's show raw bytes
        let bytes = unsafe {
            std::slice::from_raw_parts(
                self as *const Data as *const u8,
                std::mem::size_of::<Data>(),
            )
        };
        write!(f, "Data(bytes: {:02X?})", bytes)
    }
}
```

### 11.3 Implementing PartialEq Manually

```rust
impl PartialEq for Data {
    fn eq(&self, other: &Self) -> bool {
        // Compare raw bytes
        unsafe {
            let a = &*(self  as *const Data as *const [u8; 4]);
            let b = &*(other as *const Data as *const [u8; 4]);
            a == b
        }
    }
}
```

---

## 12. Tagged Unions (Manual Discriminant)

> A "discriminant" is a value that tells you which variant of a union is currently active. Rust's `enum` does this automatically. With `union`, you do it manually.

### 12.1 The Pattern

```rust
#[repr(C)]
#[derive(Clone, Copy)]
enum Tag {
    Integer = 0,
    Float   = 1,
    Bytes   = 2,
}

#[repr(C)]
#[derive(Clone, Copy)]
union Value {
    integer: i64,
    float_val:   f64,
    bytes:   [u8; 8],
}

#[repr(C)]
struct TaggedValue {
    tag:   Tag,     // discriminant — which field is valid
    value: Value,   // the actual data
}
```

### 12.2 Safe Wrapper

```rust
impl TaggedValue {
    fn new_integer(i: i64) -> Self {
        Self {
            tag:   Tag::Integer,
            value: Value { integer: i },
        }
    }

    fn new_float(f: f64) -> Self {
        Self {
            tag:   Tag::Float,
            value: Value { float_val: f },
        }
    }

    fn as_integer(&self) -> Option<i64> {
        match self.tag {
            Tag::Integer => Some(unsafe { self.value.integer }),
            _            => None,
        }
    }

    fn as_float(&self) -> Option<f64> {
        match self.tag {
            Tag::Float => Some(unsafe { self.value.float_val }),
            _          => None,
        }
    }
}
```

### 12.3 Memory Layout Diagram

```
TaggedValue in memory (with #[repr(C)]):
┌──────────────┬─────────────────────────────────────┐
│  tag (4 bytes│         value (8 bytes)              │
│  Tag::Integer│  integer: i64                        │
│  = 0x00000001│  [00][00][00][00][00][00][00][2A]    │
└──────────────┴─────────────────────────────────────┘
                ↑ Same 8 bytes could be read as f64 or [u8;8]
                  Tag tells us WHICH is valid
```

### 12.4 This Is What Rust's `enum` Does Automatically

```rust
// Rust enum IS a tagged union under the hood:
enum AutoTagged {
    Integer(i64),   // tag=0, payload=i64
    Float(f64),     // tag=1, payload=f64
    Bytes([u8; 8]), // tag=2, payload=[u8;8]
}
// Rust handles tag + safety automatically
// Use enum in idiomatic Rust; use manual tagged union for FFI
```

---

## 13. FFI — Foreign Function Interface

> **FFI** means calling C code from Rust, or exposing Rust code to C. This is the **primary real-world use case** for `union` in Rust.

### 13.1 Why FFI Needs Unions

C libraries commonly use unions in their APIs:
- `sockaddr` / `sockaddr_in` / `sockaddr_in6` (networking)
- `epoll_data` (Linux epoll)
- `sigval` (POSIX signals)
- `SDL_Event` (game dev)

To call these C functions from Rust, you must replicate the exact memory layout.

### 13.2 Example: `epoll_data` (Linux Kernel ABI)

```c
// C definition from <sys/epoll.h>
typedef union epoll_data {
    void        *ptr;
    int          fd;
    uint32_t     u32;
    uint64_t     u64;
} epoll_data_t;

struct epoll_event {
    uint32_t     events;
    epoll_data_t data;
};
```

```rust
// Rust equivalent
#[repr(C)]
pub union EpollData {
    pub ptr: *mut std::ffi::c_void,
    pub fd:  i32,
    pub u32: u32,
    pub u64: u64,
}

#[repr(C)]
pub struct EpollEvent {
    pub events: u32,
    pub data:   EpollData,
}

// Link to C function
extern "C" {
    fn epoll_ctl(
        epfd:  i32,
        op:    i32,
        fd:    i32,
        event: *mut EpollEvent,
    ) -> i32;
}

fn register_fd(epfd: i32, target_fd: i32) {
    let mut event = EpollEvent {
        events: 0x001,  // EPOLLIN
        data:   EpollData { fd: target_fd },
    };
    unsafe {
        epoll_ctl(epfd, 1 /* EPOLL_CTL_ADD */, target_fd, &mut event);
    }
}
```

### 13.3 POSIX Signal Value

```rust
#[repr(C)]
pub union SigVal {
    pub sival_int: i32,
    pub sival_ptr: *mut std::ffi::c_void,
}

// Usage: send integer payload via signal
fn send_signal_int(tid: i32, sig: i32, value: i32) {
    let sv = SigVal { sival_int: value };
    // pass sv to sigqueue syscall
}
```

---

## 14. Bitfield Manipulation

> **Bitfield**: Treating individual bits of an integer as separate boolean or small-integer fields. Used heavily in embedded systems, OS kernels, and hardware registers.

### 14.1 CPU Flags Register (x86 EFLAGS)

```
x86 EFLAGS register (32 bits):
Bit 0: CF (Carry Flag)
Bit 2: PF (Parity Flag)
Bit 4: AF (Auxiliary Carry)
Bit 6: ZF (Zero Flag)
Bit 7: SF (Sign Flag)
Bit 11: OF (Overflow Flag)
...
```

```rust
#[repr(C)]
#[derive(Copy, Clone)]
struct EFlags {
    cf: bool,  // Carry
    _r1: bool,
    pf: bool,  // Parity
    _r2: bool,
    af: bool,  // Auxiliary Carry
    _r3: bool,
    zf: bool,  // Zero
    sf: bool,  // Sign
}

#[repr(C)]
#[derive(Copy, Clone)]
union Flags {
    raw: u32,
    bits: EFlags,
}

impl Flags {
    fn is_zero(&self) -> bool {
        unsafe { self.bits.zf }
    }

    fn set_carry(&mut self) {
        self.raw |= 1;  // safe: raw is always valid
    }
}
```

### 14.2 IPv4 Header Fields

```rust
// IPv4 header — first 4 bytes packed tightly
#[repr(C)]
#[derive(Copy, Clone)]
struct IPv4HeaderByte0 {
    // Note: actual bit manipulation needs careful endian handling
    version: u8,  // bits 7-4
    ihl:     u8,  // bits 3-0 (Internet Header Length)
}

#[repr(C)]
#[derive(Copy, Clone)]
union IPv4First {
    raw:    u8,
    fields: IPv4HeaderByte0,
}

fn parse_ipv4_byte0(byte: u8) -> (u8, u8) {
    let h = IPv4First { raw: byte };
    let version = (byte >> 4) & 0xF;
    let ihl     = byte & 0xF;
    (version, ihl)
}
```

### 14.3 Float Bit Manipulation (Famous Trick)

```rust
// The legendary Quake III Fast Inverse Square Root trick
// Uses float-to-int reinterpretation via union

union FloatBits {
    f: f32,
    i: i32,
}

fn fast_inv_sqrt(x: f32) -> f32 {
    let mut bits = FloatBits { f: x };
    unsafe {
        bits.i = 0x5f3759df - (bits.i >> 1);  // magic constant
        bits.f *= 1.5 - (x * 0.5 * bits.f * bits.f);  // Newton-Raphson
        bits.f
    }
}

// What's happening:
// 1. Reinterpret f32 bits as i32 (union read)
// 2. Integer arithmetic approximates log2 and sqrt
// 3. Reinterpret i32 bits back as f32 (union read)
// 4. One Newton-Raphson step refines the approximation
```

---

## 15. Interpreter Value Types

> Building a scripting language or expression evaluator? Union-based value types are key to performance.

```rust
use std::mem::ManuallyDrop;

#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(u8)]
enum ValueTag {
    Null    = 0,
    Bool    = 1,
    Int     = 2,
    Float   = 3,
    Pointer = 4,
}

#[repr(C)]
union ValueData {
    boolean: bool,
    integer: i64,
    float_val:   f64,
    pointer: *mut u8,
    _null:   (),
}

#[repr(C)]
struct Value {
    tag:  ValueTag,
    data: ValueData,
}

impl Value {
    fn null() -> Self {
        Self { tag: ValueTag::Null, data: ValueData { _null: () } }
    }

    fn bool(b: bool) -> Self {
        Self { tag: ValueTag::Bool, data: ValueData { boolean: b } }
    }

    fn int(i: i64) -> Self {
        Self { tag: ValueTag::Int, data: ValueData { integer: i } }
    }

    fn float(f: f64) -> Self {
        Self { tag: ValueTag::Float, data: ValueData { float_val: f } }
    }

    fn is_truthy(&self) -> bool {
        match self.tag {
            ValueTag::Null    => false,
            ValueTag::Bool    => unsafe { self.data.boolean },
            ValueTag::Int     => unsafe { self.data.integer != 0 },
            ValueTag::Float   => unsafe { self.data.float_val != 0.0 },
            ValueTag::Pointer => unsafe { !self.data.pointer.is_null() },
        }
    }

    fn add(&self, other: &Value) -> Option<Value> {
        match (self.tag, other.tag) {
            (ValueTag::Int, ValueTag::Int) => {
                let a = unsafe { self.data.integer };
                let b = unsafe { other.data.integer };
                Some(Value::int(a + b))
            }
            (ValueTag::Float, ValueTag::Float) => {
                let a = unsafe { self.data.float_val };
                let b = unsafe { other.data.float_val };
                Some(Value::float(a + b))
            }
            _ => None,  // type mismatch
        }
    }
}
```

### Performance vs Enum

```
enum-based Value (Rust idiomatic):
  Size: 16 bytes (tag 1 byte + padding + f64 8 bytes = 16 bytes)
  Safety: Full
  Overhead: Match on tag (branch prediction, cache)

union-based Value (manual tagged):
  Size: 12 bytes (tag 1 byte + padding 3 + union 8 = 12 bytes)
  Safety: Manual (unsafe reads)
  Overhead: Same match overhead, but smaller struct (better cache)

In tight interpreter loops over millions of values,
the size difference matters for cache line utilization.
```

---

## 16. Network Packet Parsing

```rust
// Parsing a raw UDP/TCP socket message
// where the payload type varies by message kind

#[repr(C, packed)]
#[derive(Copy, Clone)]
struct Header {
    version:  u8,
    msg_type: u8,   // 1=Ping, 2=Data, 3=Ack, 4=Error
    length:   u16,  // payload length
}

#[repr(C)]
#[derive(Copy, Clone)]
struct PingPayload {
    timestamp: u64,
    seq:       u32,
}

#[repr(C)]
#[derive(Copy, Clone)]
struct AckPayload {
    acked_seq: u32,
    window:    u16,
}

#[repr(C)]
#[derive(Copy, Clone)]
struct ErrorPayload {
    code:    u32,
    subcode: u16,
}

#[repr(C)]
#[derive(Copy, Clone)]
union Payload {
    ping:  PingPayload,
    ack:   AckPayload,
    error: ErrorPayload,
    raw:   [u8; 16],  // fallback: raw byte access
}

#[repr(C)]
#[derive(Copy, Clone)]
struct Packet {
    header:  Header,
    payload: Payload,
}

impl Packet {
    fn parse(bytes: &[u8]) -> Option<&Packet> {
        if bytes.len() < std::mem::size_of::<Packet>() {
            return None;
        }
        // SAFETY: We checked size, and Packet is #[repr(C)]
        unsafe {
            Some(&*(bytes.as_ptr() as *const Packet))
        }
    }

    fn process(&self) {
        match self.header.msg_type {
            1 => {
                let ping = unsafe { self.payload.ping };
                println!("PING seq={}, ts={}", ping.seq, ping.timestamp);
            }
            3 => {
                let ack = unsafe { self.payload.ack };
                println!("ACK seq={}, win={}", ack.acked_seq, ack.window);
            }
            4 => {
                let err = unsafe { self.payload.error };
                println!("ERROR {}.{}", err.code, err.subcode);
            }
            _ => {
                let raw = unsafe { self.payload.raw };
                println!("Unknown msg: {:02X?}", raw);
            }
        }
    }
}
```

---

## 17. SIMD / Low-Level Math

> **SIMD** = Single Instruction, Multiple Data. A CPU can operate on 4×f32 simultaneously in a 128-bit register.

```rust
// Treating a 128-bit SIMD register as different types
#[repr(C, align(16))]  // MUST be 16-byte aligned for SSE/NEON
#[derive(Copy, Clone)]
union Simd128 {
    f32x4: [f32; 4],   // 4 floats
    i32x4: [i32; 4],   // 4 ints
    u8x16: [u8; 16],   // 16 bytes
    u64x2: [u64; 2],   // 2 u64s
}

impl Simd128 {
    fn zero() -> Self {
        Self { u64x2: [0, 0] }
    }

    fn from_f32s(a: f32, b: f32, c: f32, d: f32) -> Self {
        Self { f32x4: [a, b, c, d] }
    }

    // Extract lane
    fn f32_lane(&self, i: usize) -> f32 {
        assert!(i < 4);
        unsafe { self.f32x4[i] }
    }

    // Reinterpret bytes for debugging
    fn bytes(&self) -> [u8; 16] {
        unsafe { self.u8x16 }
    }
}

// Example: fast color conversion (RGBA u8 → f32 normalized)
fn rgba_to_normalized(rgba: [u8; 4]) -> [f32; 4] {
    let v = Simd128 { u8x16: {
        let mut b = [0u8; 16];
        b[0..4].copy_from_slice(&rgba);
        b
    }};
    let bytes = unsafe { v.u8x16 };
    [
        bytes[0] as f32 / 255.0,
        bytes[1] as f32 / 255.0,
        bytes[2] as f32 / 255.0,
        bytes[3] as f32 / 255.0,
    ]
}
```

---

## 18. Union vs `transmute`

> `std::mem::transmute<T, U>(val: T) -> U` reinterprets bits of T as U. It's like a union but scarier.

```rust
// These are functionally equivalent:

// Using union:
union FloatBits { f: f32, i: u32 }
fn float_to_bits_union(f: f32) -> u32 {
    unsafe { FloatBits { f }.i }
}

// Using transmute:
fn float_to_bits_transmute(f: f32) -> u32 {
    unsafe { std::mem::transmute(f) }
}

// Using to_bits (PREFERRED — safe, idiomatic):
fn float_to_bits_safe(f: f32) -> u32 {
    f.to_bits()  // No unsafe needed!
}
```

### When to Use Each

```
┌──────────────────────────────────────────────────────────────┐
│ Method          │ Use when                                    │
├──────────────────────────────────────────────────────────────┤
│ f32::to_bits()  │ float↔int reinterpretation (always prefer) │
│ union           │ Persistent reinterpretable struct for FFI   │
│ transmute       │ One-off conversion, same size types         │
│ from_ne_bytes() │ byte array → primitive (endian-aware)       │
│ as_ptr().cast() │ Pointer reinterpretation                    │
└──────────────────────────────────────────────────────────────┘
```

### Dangers of Transmute vs Union

```rust
// transmute is MORE dangerous: no size check in older code
// union at least ensures fields are declared

// BAD: transmute between different sizes — compile error catches this
// unsafe { std::mem::transmute::<u32, u64>(42) }  // size mismatch error

// Union gives clearer intent about which types overlay:
union Clear {
    as_u32: u32,
    as_f32: f32,
    // If you try to read as_u64, it's not a field — can't accidentally do it
}
```

---

## 19. Common Pitfalls & Anti-Patterns

### Pitfall 1: Reading Without Writing First

```rust
union U { a: i32, b: f32 }
let u: U = unsafe { std::mem::zeroed() };
// OK: zeroed memory is valid for i32 and f32
let x = unsafe { u.a };  // fine: 0 is valid i32

// But if you do:
let u: U = unsafe { std::mem::MaybeUninit::uninit().assume_init() };
let x = unsafe { u.a };  // UB! uninitialized bytes!
```

### Pitfall 2: Forgetting ManuallyDrop

```rust
// WRONG: String leaks!
union Leak {
    text: ManuallyDrop<String>,
    num:  i64,
}

fn bad() {
    let u = Leak { text: ManuallyDrop::new(String::from("hi")) };
    // Switching variants without dropping:
    let mut u = Leak { num: 42 };
    // String "hi" is leaked!
}

// CORRECT: Always drop before switching
fn good() {
    let mut u = Leak { text: ManuallyDrop::new(String::from("hi")) };
    unsafe { ManuallyDrop::drop(&mut u.text) };  // drop first
    u = Leak { num: 42 };  // now safe to switch
}
```

### Pitfall 3: Invalid Type Reinterpretation

```rust
union UB {
    b: bool,   // valid only: 0x00 or 0x01
    i: u8,
}

let u = UB { i: 5 };  // write 5 (valid u8)
let b = unsafe { u.b };  // UB! 5 is not a valid bool (only 0 or 1)
```

### Pitfall 4: Endianness in FFI

```rust
#[repr(C)]
union IpAddr {
    raw:    u32,
    octets: [u8; 4],
}

let ip = IpAddr { raw: 0xC0A80001u32 };  // 192.168.0.1 in big-endian

// On a little-endian machine:
let bytes = unsafe { ip.octets };
// bytes = [0x01, 0x00, 0xA8, 0xC0] — reversed!
// To fix: use u32::to_be() or u32::from_be_bytes()
```

### Pitfall 5: Non-`#[repr(C)]` for FFI

```rust
// WRONG: Rust may reorder or pad fields differently than C
union WrongFFI {
    a: u32,
    b: u64,
}

// CORRECT: Force C-compatible layout
#[repr(C)]
union CorrectFFI {
    a: u32,
    b: u64,
}
```

---

## 20. Performance Analysis

### 20.1 Size Impact

```rust
// Enum (with tag):
enum ValEnum {
    Int(i64),
    Float(f64),
    Byte(u8),
}
// size = 16 bytes (8 for payload + 8 for tag after padding)

// Union (no tag):
union ValUnion {
    int_val:   i64,
    float_val: f64,
    byte_val:  u8,
}
// size = 8 bytes (just the max payload)
```

### 20.2 Cache Line Impact

```
Cache line = 64 bytes

Array of 8 ValEnum: 8 × 16 = 128 bytes = 2 cache lines
Array of 8 ValUnion: 8 × 8 = 64 bytes = 1 cache line

Processing 8 values:
  ValEnum:  2 cache misses (if cold)
  ValUnion: 1 cache miss  (if cold)
  
At millions of iterations, this 2× cache efficiency matters.
```

### 20.3 Branch Prediction

Both tagged union (manual) and enum require a branch on the tag. The performance difference is:
- **Same branch cost** for tag checking
- **Better spatial locality** for union (smaller size = more fit in cache)
- **Alignment** — unions might require padding in arrays

---

## 21. Mental Models

### 21.1 The Debugger Lens Model

Think of a union as raw memory under a lens. The **lens** is the field you choose to read through. The memory doesn't change — only your interpretation of it does.

```
Memory bytes: [3F 80 00 00]
              ┌──────────┐
   Lens f32:  │   1.0    │
              └──────────┘
              ┌──────────┐
   Lens u32:  │1065353216│
              └──────────┘
              ┌──────────┐
   Lens [u8;4]│[63,128,0,0]│
              └──────────┘
Same bytes — different truths depending on your lens.
```

### 21.2 The Responsibility Inversion Model

In Rust:
- `enum` = **compiler** tracks which variant is active
- `union` = **programmer** tracks which variant is active

Using union = **you become the type system**. You must enforce invariants manually.

### 21.3 Cognitive Framework: Trust Hierarchy

```
Level 0 (safest):  Use enum — Rust guarantees correctness
Level 1:           Use union with external tag — manual but structured
Level 2:           Use union with raw byte access — maximum control
Level 3 (danger):  Use transmute — maximum footgun risk
```

Start from Level 0 and only descend when you have a concrete reason:
- FFI requirement → Level 1 or 2
- Performance-critical hot path → Level 1
- Raw memory manipulation → Level 2
- Never use Level 3 unless Level 2 is insufficient

### 21.4 Deliberate Practice Insight

When learning unsafe Rust constructs like `union`, use the **"justify every unsafe"** practice:

Before every `unsafe` block, write a comment explaining:
1. **Why** this is safe
2. **What invariant** is being maintained
3. **What would break** if this were violated

```rust
unsafe {
    // SAFETY: We checked `self.tag == Tag::Integer` on line above.
    //         The union was last written via the integer field.
    //         i64 has no invalid byte patterns — all bit patterns valid.
    self.data.integer
}
```

This is called **safety documentation** and is standard in production Rust code.

---

## 22. Summary Cheat Sheet

```
┌─────────────────────────────────────────────────────────┐
│                    UNION QUICK REFERENCE                 │
├─────────────────────────────────────────────────────────┤
│ Declare:     union Name { field: Type, ... }            │
│ Create:      Name { field: value }                      │
│ Write:       union_var.field = val  (SAFE)              │
│ Read:        unsafe { union_var.field }  (UNSAFE)       │
│ Size:        max(sizeof all fields)                     │
│ Align:       max(alignof all fields)                    │
├─────────────────────────────────────────────────────────┤
│ Field types: Must be Copy OR ManuallyDrop<T>            │
│ Derive:      Copy, Clone only (no Debug, PartialEq)     │
│ FFI use:     Add #[repr(C)]                             │
├─────────────────────────────────────────────────────────┤
│ KEY INVARIANT: Only read the LAST field written,        │
│                and its bytes must be valid for the type │
├─────────────────────────────────────────────────────────┤
│ USE UNION when:                                         │
│   • Interfacing with C ABI                              │
│   • Bit manipulation / hardware registers               │
│   • Extreme memory efficiency critical                  │
│   • Building interpreters / VMs                         │
│   • Implementing SIMD abstractions                      │
│                                                         │
│ PREFER ENUM when:                                       │
│   • Pure Rust code                                      │
│   • Safety is priority                                  │
│   • Idiomatic code matters                              │
└─────────────────────────────────────────────────────────┘
```

---

*"The expert does not fear unsafe code — they respect it. They know exactly when to wield it and why, and they document every assumption with the clarity of someone who has debugged a UB crash at 3am."*

---

**Next Steps in Your DSA Journey:**
- Study `MaybeUninit<T>` — uninitialized memory handling
- Study `std::mem::transmute` dangers deeply
- Read the Rustonomicon (nomicon.rs) — the unofficial Rust unsafe guide
- Implement a small stack-based VM using tagged unions
- Study `repr(C)`, `repr(packed)`, `repr(align(N))` comprehensively

Here's your complete guide. Let me walk you through the core architecture of what we covered:

---

## What `union` Is At Its Core

A `union` is **one chunk of memory interpreted through different lenses**. Unlike a `struct` (all fields exist simultaneously), a union's fields all **overlap at address zero**. The size is `max(sizeof all fields)`, not the sum.

```
STRUCT: [field_a][field_b][field_c]   ← separate memory regions
UNION:  [        field_a            ]
        [        field_b            ]  ← ALL at same address
        [        field_c            ]
```

---

## The 3 Laws of Union Safety

```
LAW 1 — Only read the field you LAST wrote
LAW 2 — The bytes must be a valid representation of the type
LAW 3 — You are the type system now — document every invariant
```

This is why reads are `unsafe` but writes are safe — writing just stores bytes (no invariant can break), while reading *interprets* bytes (invalid bit patterns = UB).

---

## The 5 Real-World Domains

| Domain | Why Union? |
|--------|-----------|
| **FFI / C interop** | Must match C's exact memory layout |
| **Bitfield manipulation** | Read hardware registers as different-width types |
| **Network packet parsing** | Same byte buffer, different header interpretations |
| **Interpreter value types** | No tag overhead in hot evaluation loops |
| **SIMD abstractions** | Reinterpret 128-bit register as `f32x4` or `u8x16` |

---

## The Golden Rule for Production Code

Every `unsafe` block accessing a union field should have a `// SAFETY:` comment explaining what invariant guarantees this access is valid. This isn't optional — it's how world-class Rust engineers communicate intent across time.