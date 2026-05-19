# Complete & Comprehensive Guide to Struct Pointers
### C · Go · Rust — In-Depth Reference

---

## Table of Contents

1. [Memory Fundamentals](#1-memory-fundamentals)
2. [What Is a Pointer?](#2-what-is-a-pointer)
3. [What Is a Struct?](#3-what-is-a-struct)
4. [Struct Memory Layout](#4-struct-memory-layout)
5. [Struct Pointers — The Core Concept](#5-struct-pointers--the-core-concept)
6. [Stack vs Heap Allocation](#6-stack-vs-heap-allocation)
7. [Dereferencing a Struct Pointer](#7-dereferencing-a-struct-pointer)
8. [The Arrow Operator vs Dot Operator](#8-the-arrow-operator-vs-dot-operator)
9. [Pointer Arithmetic on Structs](#9-pointer-arithmetic-on-structs)
10. [Passing Struct Pointers to Functions](#10-passing-struct-pointers-to-functions)
11. [Returning Struct Pointers from Functions](#11-returning-struct-pointers-from-functions)
12. [Null / Nil Pointers and Safety](#12-null--nil-pointers-and-safety)
13. [Nested Structs and Nested Pointers](#13-nested-structs-and-nested-pointers)
14. [Arrays of Structs vs Arrays of Struct Pointers](#14-arrays-of-structs-vs-arrays-of-struct-pointers)
15. [Double Pointers (Pointer to Pointer)](#15-double-pointers-pointer-to-pointer)
16. [Methods on Struct Pointers](#16-methods-on-struct-pointers)
17. [Function Pointers Inside Structs](#17-function-pointers-inside-structs)
18. [Self-Referential Structs — Linked Lists & Trees](#18-self-referential-structs--linked-lists--trees)
19. [Pointer Aliasing](#19-pointer-aliasing)
20. [Ownership, Borrowing & Lifetimes (Rust)](#20-ownership-borrowing--lifetimes-rust)
21. [Interface Dispatch via Struct Pointers](#21-interface-dispatch-via-struct-pointers)
22. [Memory Safety & Common Pitfalls](#22-memory-safety--common-pitfalls)
23. [Patterns and Idioms](#23-patterns-and-idioms)
24. [Mental Models Summary](#24-mental-models-summary)

---

## 1. Memory Fundamentals

Before a single line of struct-pointer code makes sense, you must have a razor-sharp picture of how memory works at runtime.

### 1.1 The Memory Address Space

Every process is given a virtual address space by the OS. Think of it as a very long, flat array of bytes, each byte having a unique numeric address (64-bit systems: 0 to 2^64-1 theoretically, though the OS only maps a fraction).

```
Virtual Address Space (simplified, 64-bit process)
┌──────────────────────────────────────────────────────┐
│  Address 0x0000_0000_0000_0000  (lowest)             │
│  ...                                                 │
│  [kernel reserved / unmapped]                        │
│  ...                                                 │
├──────────────────────────────────────────────────────┤
│  TEXT SEGMENT   (machine code, read-only)            │
│  0x0000_0000_0040_0000 – ...                         │
├──────────────────────────────────────────────────────┤
│  DATA SEGMENT   (initialized globals)                │
│  BSS SEGMENT    (zero-initialized globals)           │
├──────────────────────────────────────────────────────┤
│  HEAP  ↓ grows toward higher addresses              │
│  (dynamic allocation: malloc, new, Box::new)         │
│                                                      │
│         [free space]                                 │
│                                                      │
│  STACK ↑ grows toward lower addresses               │
│  (function call frames, local variables)             │
├──────────────────────────────────────────────────────┤
│  Address 0xFFFF_FFFF_FFFF_FFFF  (highest)            │
└──────────────────────────────────────────────────────┘
```

### 1.2 Bytes, Words, and Alignment

- **Byte** (1 byte = 8 bits): the smallest addressable unit.
- **Word**: CPU's native data width. On x86-64, a word is 8 bytes (64 bits).
- **Alignment**: a value of type `T` with alignment `A` must live at an address that is a multiple of `A`. Misaligned accesses may be slow or illegal depending on the CPU.

```
Address:  0x00  0x01  0x02  0x03  0x04  0x05  0x06  0x07
          ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
          │  B  │  B  │  B  │  B  │  B  │  B  │  B  │  B  │
          └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
          ↑                                               ↑
       1-byte aligned                              8-byte aligned (address % 8 == 0)
```

### 1.3 Why This Matters for Structs

When the compiler lays out a struct in memory, it inserts **padding bytes** to ensure each field satisfies its alignment requirement. Understanding this is critical for reasoning about struct pointer arithmetic, casting, and serialisation.

---

## 2. What Is a Pointer?

A **pointer** is a variable that holds a **memory address** as its value.

```
Normal variable (int x = 42):
┌─────────────────────┐
│  Name : x           │
│  Addr : 0x7fff_1000 │
│  Value: 42          │
└─────────────────────┘

Pointer variable (int *p = &x):
┌─────────────────────┐           ┌─────────────────────┐
│  Name : p           │           │  Name : x           │
│  Addr : 0x7fff_1008 │           │  Addr : 0x7fff_1000 │
│  Value: 0x7fff_1000 │ ───────▶  │  Value: 42          │
└─────────────────────┘           └─────────────────────┘
```

Key points:
- The pointer itself occupies memory (8 bytes on 64-bit).
- The pointer's value is the address of another object.
- Dereferencing (`*p`) follows the arrow and gives you access to the object at that address.

### 2.1 Pointer Size

On any 64-bit platform: **every pointer is exactly 8 bytes**, regardless of what it points to. `int*`, `char*`, `struct Foo*` — all are 8 bytes.

### 2.2 Typed Pointers vs Raw Addresses

The type of a pointer tells the compiler:
- **How large** the object being pointed to is.
- **How to interpret** the bytes at that address.
- **How much** to advance the address by when doing arithmetic (`p+1` advances by `sizeof(*p)`).

---

## 3. What Is a Struct?

A **struct** is a composite data type: a contiguous block of memory with named, typed fields.

```c
// C
struct Point {
    int x;   // 4 bytes
    int y;   // 4 bytes
};           // total: 8 bytes, no padding needed (both fields align at 4)
```

```go
// Go
type Point struct {
    X int32
    Y int32
}
```

```rust
// Rust
struct Point {
    x: i32,
    y: i32,
}
```

All three produce the same memory footprint: 8 contiguous bytes.

---

## 4. Struct Memory Layout

### 4.1 Field Alignment and Padding

The compiler places each field at the first address that satisfies the field's alignment requirement. It inserts **padding** (wasted bytes) between fields when necessary.

```c
struct Example {
    char  a;    // 1 byte, align 1
    int   b;    // 4 bytes, align 4
    char  c;    // 1 byte, align 1
    // padding  // 3 bytes to align 'd'
    double d;   // 8 bytes, align 8
};
```

Memory layout:

```
Offset   Field    Bytes    Reason
──────────────────────────────────────────────────────────────
 0       a        1        starts at 0, OK (align 1)
 1       [pad]    3        'b' needs align 4 → next addr divisible by 4 is 4
 4       b        4        starts at 4, OK (align 4)
 8       c        1        starts at 8, OK (align 1)
 9       [pad]    7        'd' needs align 8 → next addr divisible by 8 is 16
16       d        8        starts at 16, OK (align 8)
──────────────────────────────────────────────────────────────
Total: 24 bytes  (only 14 bytes of actual data, 10 bytes wasted)
```

ASCII diagram:

```
Byte offsets:
 0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20  21  22  23
┌───┬───┬───┬───┬───────────────┬───┬───┬───┬───┬───┬───┬───┬───┬───────────────────────────────┐
│ a │PAD│PAD│PAD│      b        │ c │PAD│PAD│PAD│PAD│PAD│PAD│PAD│           d                   │
└───┴───┴───┴───┴───────────────┴───┴───┴───┴───┴───┴───┴───┴───┴───────────────────────────────┘
```

### 4.2 Struct Tail Padding

The compiler also pads the end of a struct so that placing multiple of them in an array keeps each one properly aligned.

```c
struct S { char a; int b; };  
// sizeof(S) == 8 (not 5) because of 3 bytes tail padding
```

### 4.3 Re-ordering Fields to Save Space

Always order fields from **largest alignment to smallest**:

```c
// BAD: 24 bytes
struct Bad  { char a; int b; char c; double d; };

// GOOD: 16 bytes
struct Good { double d; int b; char a; char c; };
```

Layout of `Good`:
```
 0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
┌───────────────────────────┬───────────────┬───┬───┬───┬───┐
│          d (8)            │    b (4)      │ a │ c │PAD│PAD│
└───────────────────────────┴───────────────┴───┴───┴───┴───┘
```

### 4.4 `offsetof` — Finding a Field's Byte Offset

```c
#include <stddef.h>
printf("%zu\n", offsetof(struct Example, d)); // prints 16
```

In Rust, `std::mem::offset_of!` (stabilised in 1.77):
```rust
use std::mem::offset_of;
println!("{}", offset_of!(Example, d)); // 16
```

---

## 5. Struct Pointers — The Core Concept

A **struct pointer** is a pointer whose type is `struct T *` (C), `*T` / `*mut T` (Rust), or `*T` (Go). It holds the address of the first byte of the struct in memory.

```
struct Point { int x; int y; };
Point p   = {3, 7};
Point *ptr = &p;

Memory:
                         ┌───────────────────────────────┐
ptr ──(0x7fff_2000)────▶ │ x = 3          (bytes 0-3)    │  address 0x7fff_2000
                         │ y = 7          (bytes 4-7)    │  address 0x7fff_2004
                         └───────────────────────────────┘

ptr itself lives at, say, 0x7fff_3000 and holds the VALUE 0x7fff_2000.
```

### 5.1 Taking the Address of a Struct

```c
// C
struct Point p = {3, 7};
struct Point *ptr = &p;     // &p gives the address of p's first byte
```

```go
// Go
p := Point{X: 3, Y: 7}
ptr := &p                   // same concept
```

```rust
// Rust
let p = Point { x: 3, y: 7 };
let ptr: *const Point = &p;          // raw pointer (unsafe)
let r: &Point = &p;                  // reference (safe, preferred)
```

> **Key Insight**: In Rust, references (`&T`, `&mut T`) ARE safe struct pointers backed by the borrow checker. Raw pointers (`*const T`, `*mut T`) are the unsafe equivalent of C pointers.

### 5.2 Creating a Pointer to a Heap-Allocated Struct

```c
// C
struct Point *ptr = malloc(sizeof(struct Point));
ptr->x = 3;
ptr->y = 7;
// ... use it ...
free(ptr);
```

```go
// Go
ptr := &Point{X: 3, Y: 7}   // compiler allocates on heap, returns pointer
// GC handles deallocation
```

```rust
// Rust
let ptr: Box<Point> = Box::new(Point { x: 3, y: 7 });
// Box<T> is a heap-allocated smart pointer; drop handled automatically
```

---

## 6. Stack vs Heap Allocation

This distinction is **fundamental** to how and when you use struct pointers.

### 6.1 Stack Allocation

```
Call Frame for main():
┌──────────────────────────────────────────────────────┐  ← stack grows downward
│  return address                                      │
│  saved registers                                     │
├──────────────────────────────────────────────────────┤
│  local variable: struct Point p                      │
│    p.x = 3  [0x7fff_1000 .. 0x7fff_1003]            │
│    p.y = 7  [0x7fff_1004 .. 0x7fff_1007]            │
├──────────────────────────────────────────────────────┤
│  local variable: struct Point *ptr = 0x7fff_1000     │
│    [0x7fff_1010 .. 0x7fff_1017]  (8 bytes for addr)  │
└──────────────────────────────────────────────────────┘
```

- Allocation is O(1): stack pointer is simply decremented.
- Lifetime is tied to the scope of the function.
- **Danger**: returning a pointer to a stack variable is undefined behavior in C (dangling pointer). Rust's borrow checker prevents this statically.

### 6.2 Heap Allocation

```
HEAP:
┌──────────────────────────────────────────────────────┐
│  ...                                                 │
│  [free block]                                        │
├──────────────────────────────────────────────────────┤
│  malloc header (internal bookkeeping, ~16-24 bytes)  │
│  struct Point data:                                  │
│    x = 3  [0x0000_5555_1000 .. 0x0000_5555_1003]    │
│    y = 7  [0x0000_5555_1004 .. 0x0000_5555_1007]    │
├──────────────────────────────────────────────────────┤
│  [free block]                                        │
└──────────────────────────────────────────────────────┘

STACK:
  ptr = 0x0000_5555_1000  ─────────────────────────────▶ the Point on heap
```

- Lifetime is explicit (C: `free`; Rust: `Drop`; Go: GC).
- More overhead per allocation (~100ns vs ~1ns for stack).
- Enables data to outlive the creating function.

### 6.3 Go's Escape Analysis

In Go, the compiler performs **escape analysis**: if a local variable's address is returned or passed somewhere that might outlive the function, the compiler moves it to the heap automatically.

```go
func newPoint() *Point {
    p := Point{X: 3, Y: 7}   // compiler sees address escapes
    return &p                  // so 'p' is heap-allocated, this is safe
}
```

### 6.4 Rust Stack vs Heap

```rust
fn stack_point() -> Point {
    let p = Point { x: 3, y: 7 };  // stack
    p  // moves the value out by copy (if Copy) or move
}

fn heap_point() -> Box<Point> {
    Box::new(Point { x: 3, y: 7 })  // heap; Box<T> is a smart pointer
}
```

---

## 7. Dereferencing a Struct Pointer

**Dereferencing** means following the pointer to access the actual struct data.

### 7.1 In C

```c
struct Point { int x; int y; };
struct Point p = {3, 7};
struct Point *ptr = &p;

// Dereference to get the whole struct
struct Point q = *ptr;       // q is a copy: {3, 7}

// Dereference to access a field
int val = (*ptr).x;          // 3  — dereference first, then dot
int val2 = ptr->x;           // 3  — arrow is shorthand for (*ptr).x
```

### 7.2 In Go

```go
p := Point{X: 3, Y: 7}
ptr := &p

val := (*ptr).X    // 3
val2 := ptr.X      // 3 — Go auto-dereferences; no arrow operator needed
```

Go always auto-dereferences — you never need `->`.

### 7.3 In Rust

```rust
let p = Point { x: 3, y: 7 };
let r = &p;                  // immutable reference (safe pointer)

let val = (*r).x;            // 3 — explicit deref
let val2 = r.x;              // 3 — Rust auto-derefs references with dot

// Raw pointer (unsafe context)
let raw: *const Point = &p;
let val3 = unsafe { (*raw).x };  // must be inside unsafe block
```

### 7.4 Deep Dive: What Actually Happens in the CPU

When you write `ptr->x` or `*ptr.x`:

1. The value in `ptr` (the address, e.g., `0x7fff_1000`) is loaded into a register.
2. The CPU adds the field offset (here 0 for `x`) to get the effective address `0x7fff_1000 + 0`.
3. A load instruction reads 4 bytes from that effective address into a register.

```
Machine-level view of ptr->x  (x86-64 pseudocode)
    mov  rax, [ptr]          ; rax = 0x7fff_1000 (load pointer value)
    mov  eax, [rax + 0]      ; eax = *(0x7fff_1000 + 0) = 3
```

For `ptr->y` (offset 4):
```
    mov  rax, [ptr]
    mov  eax, [rax + 4]      ; eax = *(0x7fff_1000 + 4) = 7
```

---

## 8. The Arrow Operator vs Dot Operator

| Language | Value access | Pointer/Reference access |
|----------|-------------|--------------------------|
| C        | `s.field`   | `ptr->field` or `(*ptr).field` |
| Go       | `s.field`   | `ptr.field` (auto-deref) |
| Rust     | `s.field`   | `r.field` (auto-deref for `&T`), `unsafe { (*ptr).field }` for raw |

The arrow operator `->` in C is purely **syntactic sugar**:
```c
ptr->field   ≡   (*ptr).field
```

The precedence of `.` is higher than `*`, so the parentheses in `(*ptr).field` are necessary without `->`.

---

## 9. Pointer Arithmetic on Structs

Pointer arithmetic advances a pointer by **multiples of the pointed-to type's size**.

```c
struct Point pts[3] = {{1,2}, {3,4}, {5,6}};
struct Point *p = pts;      // p points to pts[0]

// p + 1 advances by sizeof(struct Point) = 8 bytes
struct Point *p1 = p + 1;  // points to pts[1]
struct Point *p2 = p + 2;  // points to pts[2]
```

Memory:

```
Address      Byte offsets     Contents
0x1000       [0  – 7 ]        pts[0]: x=1, y=2
0x1008       [8  – 15]        pts[1]: x=3, y=4
0x1010       [16 – 23]        pts[2]: x=5, y=6

p   = 0x1000
p+1 = 0x1008  (advanced by sizeof(Point) = 8)
p+2 = 0x1010
```

### 9.1 Iterating With Pointer Arithmetic (C)

```c
struct Point pts[3] = {{1,2},{3,4},{5,6}};
struct Point *end = pts + 3;   // one past the last element

for (struct Point *p = pts; p < end; p++) {
    printf("(%d, %d)\n", p->x, p->y);
}
```

### 9.2 Why Go and Rust Discourage Raw Pointer Arithmetic

In Go, pointer arithmetic on typed pointers is **not allowed** (unsafe package required). In Rust, raw pointer arithmetic requires `unsafe`. Both languages provide iterator abstractions that are safer and equally fast.

```rust
// Rust: safe iteration (preferred)
let pts = [Point{x:1,y:2}, Point{x:3,y:4}, Point{x:5,y:6}];
for p in &pts {
    println!("({}, {})", p.x, p.y);
}

// Rust: raw pointer arithmetic (unsafe, C-style)
unsafe {
    let base: *const Point = pts.as_ptr();
    for i in 0..3 {
        let p = base.add(i);      // base + i * sizeof(Point)
        println!("({}, {})", (*p).x, (*p).y);
    }
}
```

---

## 10. Passing Struct Pointers to Functions

This is one of the most important use cases for struct pointers.

### 10.1 Pass by Value vs Pass by Pointer

**Pass by value**: a full copy of the struct is made and pushed onto the callee's stack frame.

```
Caller stack:                  Callee stack:
┌────────────────┐             ┌────────────────┐
│  Point p       │             │  Point p_copy  │ ← COPY, separate memory
│   x = 3        │             │   x = 3        │
│   y = 7        │             │   y = 7        │
└────────────────┘             └────────────────┘
```

**Pass by pointer**: only the 8-byte address is copied; callee accesses the original.

```
Caller stack:                  Callee stack:
┌────────────────┐             ┌───────────────────┐
│  Point p       │◀────────────│  Point *ptr        │ (8 bytes: address)
│   x = 3        │             │   = 0x7fff_1000   │
│   y = 7        │             └───────────────────┘
└────────────────┘
     (single shared copy)
```

### 10.2 C Examples

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    double x, y, z;
} Vec3;  // 24 bytes

// Pass by value: 24 bytes copied every call
double magnitude_byval(Vec3 v) {
    return sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
}

// Pass by pointer: 8 bytes copied, original accessible
void scale_byptr(Vec3 *v, double factor) {
    v->x *= factor;  // modifies original
    v->y *= factor;
    v->z *= factor;
}

// Pass by const pointer: no copy, no mutation allowed
double magnitude_byptr(const Vec3 *v) {
    return sqrt(v->x*v->x + v->y*v->y + v->z*v->z);
}
```

### 10.3 Go Examples

```go
type Vec3 struct { X, Y, Z float64 }

// Pass by value: copy
func magnitudeVal(v Vec3) float64 {
    return math.Sqrt(v.X*v.X + v.Y*v.Y + v.Z*v.Z)
}

// Pass by pointer: no copy, mutation possible
func scalePtr(v *Vec3, factor float64) {
    v.X *= factor
    v.Y *= factor
    v.Z *= factor
}
```

### 10.4 Rust Examples

```rust
struct Vec3 { x: f64, y: f64, z: f64 }

// Immutable borrow: no copy, read-only
fn magnitude(v: &Vec3) -> f64 {
    (v.x*v.x + v.y*v.y + v.z*v.z).sqrt()
}

// Mutable borrow: no copy, allows mutation
fn scale(v: &mut Vec3, factor: f64) {
    v.x *= factor;
    v.y *= factor;
    v.z *= factor;
}
```

### 10.5 When to Prefer Pointer Passing

- Struct is larger than ~16 bytes (copying is expensive).
- You need to mutate the original.
- You need to express shared ownership (C: manual, Go: GC, Rust: `Rc`/`Arc`).
- The function is called in a tight loop (avoid repeated copying).

---

## 11. Returning Struct Pointers from Functions

### 11.1 C — Never Return a Pointer to a Local Variable

```c
// WRONG — undefined behavior: p is destroyed when function returns
struct Point *bad_factory(void) {
    struct Point p = {3, 7};
    return &p;   // ← dangling pointer!
}
```

```
Timeline:
bad_factory() called   → p lives on its stack frame at 0x7fff_9000
bad_factory() returns  → stack frame DESTROYED, 0x7fff_9000 is garbage
caller uses ptr        → UNDEFINED BEHAVIOR
```

```c
// CORRECT — return pointer to heap-allocated struct
struct Point *good_factory(int x, int y) {
    struct Point *p = malloc(sizeof(struct Point));
    if (!p) return NULL;
    p->x = x;
    p->y = y;
    return p;  // heap memory persists after return
}
// caller must free(p) later
```

### 11.2 Go — Safe to Return Pointer to Local

Due to escape analysis, Go automatically promotes the local to the heap:

```go
func newPoint(x, y int32) *Point {
    p := Point{X: x, Y: y}
    return &p   // safe: compiler heap-allocates p because address escapes
}
```

### 11.3 Rust — Borrow Checker Prevents Dangling Pointers

```rust
// COMPILE ERROR: cannot return reference to local variable
fn bad_factory() -> &Point {
    let p = Point { x: 3, y: 7 };
    &p  // error[E0106]: missing lifetime specifier / borrow of local
}

// CORRECT: return owned heap-allocated value
fn good_factory(x: i32, y: i32) -> Box<Point> {
    Box::new(Point { x, y })
}

// Or return the value directly (stack-allocated, moved to caller)
fn factory(x: i32, y: i32) -> Point {
    Point { x, y }
}
```

---

## 12. Null / Nil Pointers and Safety

### 12.1 The Null Pointer

A null pointer is a pointer whose value is 0 (or `NULL` / `nil`). Dereferencing it is **undefined behavior** in C, a **panic** in Go, and **undefined behavior** in Rust unsafe code.

```
NULL pointer:
┌─────────────────────────────────┐
│  ptr = 0x0000_0000_0000_0000    │ ─────▶  ??? (no valid object here)
└─────────────────────────────────┘
         Dereferencing this is catastrophic
```

### 12.2 C — Null Pointer Checks

```c
struct Node *n = malloc(sizeof(struct Node));
if (n == NULL) {
    // allocation failed; handle error
    return -1;
}
// Safe to use n->...
```

### 12.3 Go — Nil Pointer Checks

```go
var p *Point = nil

if p != nil {
    fmt.Println(p.X)   // safe
}
// p.X without check would panic at runtime
```

### 12.4 Rust — No Null References

In Rust, references (`&T`, `&mut T`) are **guaranteed non-null** by the type system. Null is represented with `Option<&T>`:

```rust
fn find(data: &[Point], x: i32) -> Option<&Point> {
    data.iter().find(|p| p.x == x)
}

match find(&pts, 3) {
    Some(p) => println!("found: ({}, {})", p.x, p.y),
    None    => println!("not found"),
}
```

`Option<Box<T>>` is null-pointer-optimised: it takes the same space as `Box<T>` because `None` is represented as the zero/null bit pattern.

---

## 13. Nested Structs and Nested Pointers

### 13.1 Struct Containing Another Struct (by Value)

```c
typedef struct {
    float lat;
    float lon;
} GeoCoord;

typedef struct {
    char name[32];
    GeoCoord location;    // embedded by value (inline)
} City;
```

Memory layout:
```
City (44 bytes):
 0       31  32    35  36    39
┌──────────────┬────────────┬────────────┐
│  name[32]    │  lat (4B)  │  lon (4B)  │
└──────────────┴────────────┴────────────┘
                   ↑ GeoCoord starts here (offset 32)
```

Accessing nested fields:
```c
City *city_ptr = get_city();
float lat = city_ptr->location.lat;   // arrow then dot
```

### 13.2 Struct Containing a Pointer to Another Struct

```c
typedef struct {
    char    name[32];
    GeoCoord *location;   // pointer to separately-allocated GeoCoord
} City;
```

Memory diagram:
```
City on heap:                             GeoCoord on heap:
┌──────────────┬─────────────────────┐   ┌───────────────────────┐
│  name[32]    │  location ptr (8B)  │──▶│  lat (4B) │ lon (4B)  │
└──────────────┴─────────────────────┘   └───────────────────────┘
 0           31  32                 39    (somewhere else in memory)
```

Accessing:
```c
float lat = city_ptr->location->lat;  // two pointer dereferences
```

### 13.3 Go Nested Structs

```go
type GeoCoord struct { Lat, Lon float32 }
type City struct {
    Name     string
    Location GeoCoord        // by value (embedded)
    AltCoord *GeoCoord       // by pointer
}

c := City{Name: "Tellicherry", Location: GeoCoord{11.75, 75.49}}
fmt.Println(c.Location.Lat)       // 11.75
fmt.Println(c.AltCoord)           // <nil>
```

### 13.4 Rust Nested Structs

```rust
struct GeoCoord { lat: f32, lon: f32 }

struct City {
    name: String,
    location: GeoCoord,           // owned, inline
    alt_coord: Option<Box<GeoCoord>>,  // optional heap pointer
}

let c = City {
    name: String::from("Tellicherry"),
    location: GeoCoord { lat: 11.75, lon: 75.49 },
    alt_coord: None,
};
println!("{}", c.location.lat);
```

---

## 14. Arrays of Structs vs Arrays of Struct Pointers

### 14.1 Array of Structs (AoS)

All structs are stored **contiguously** in memory.

```c
struct Point pts[4] = {{1,2},{3,4},{5,6},{7,8}};
```

```
Memory (contiguous):
 0x1000      0x1008      0x1010      0x1018
┌──────────┬──────────┬──────────┬──────────┐
│ {1,2}    │ {3,4}    │ {5,6}    │ {7,8}    │
└──────────┴──────────┴──────────┴──────────┘
 pts[0]      pts[1]     pts[2]     pts[3]
```

- Cache-friendly for sequential access.
- `pts[i]` = `pts + i * sizeof(Point)` — O(1) indexed access.
- No extra indirection.

### 14.2 Array of Struct Pointers (AoP)

Each element is a pointer; the structs themselves can be anywhere on the heap.

```c
struct Point *ptrs[4];
for (int i = 0; i < 4; i++) {
    ptrs[i] = malloc(sizeof(struct Point));
    ptrs[i]->x = i*2+1; ptrs[i]->y = i*2+2;
}
```

```
Pointer array (on stack/heap):
 0x2000      0x2008      0x2010      0x2018
┌──────────┬──────────┬──────────┬──────────┐
│ 0x5001   │ 0x7A30   │ 0x5041   │ 0x6B00   │  ← pointer values
└──────────┴──────────┴──────────┴──────────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
  {1,2}       {3,4}       {5,6}       {7,8}     ← scattered on heap
 0x5001      0x7A30      0x5041      0x6B00
```

- Elements can be different sizes (useful for polymorphism in C via void*).
- Each access requires an extra memory read (pointer indirection) → potential cache miss.
- Enables ownership transfer: swap pointers without moving data.

### 14.3 When to Use Which

| Scenario | Prefer |
|----------|--------|
| Fixed-size structs, tight loops, cache-critical | Array of Structs |
| Variable-size elements or polymorphism | Array of Pointers |
| Need to sort large structs cheaply | Array of Pointers (swap ptrs, not data) |
| Embedded / stack allocation | Array of Structs |

---

## 15. Double Pointers (Pointer to Pointer)

A **pointer to a pointer** (`T **` in C, `**T` in Rust unsafe, `**T` Go unsafe) holds the address of another pointer.

### 15.1 Core Concept

```
int x     = 42;          // value
int *p    = &x;          // pointer to x
int **pp  = &p;          // pointer to the pointer p

x  lives at 0x1000, value = 42
p  lives at 0x2000, value = 0x1000
pp lives at 0x3000, value = 0x2000

pp ──(0x2000)──▶  p ──(0x1000)──▶  x = 42
```

### 15.2 Double Pointer with Structs

#### Use Case 1: Modify a Pointer from a Caller

```c
typedef struct Node { int val; struct Node *next; } Node;

// To let a function allocate and assign a struct pointer,
// pass a pointer TO the pointer
void create_node(Node **out, int val) {
    *out = malloc(sizeof(Node));
    (*out)->val = val;
    (*out)->next = NULL;
}

int main(void) {
    Node *head = NULL;
    create_node(&head, 42);  // &head is Node**
    // head now points to the new node
}
```

```
Before:  head = NULL
         &head = 0x7fff_1000 (address of the head variable itself)

Inside create_node:
  out = 0x7fff_1000          (address of head)
  *out = malloc(...)         (assigns to head through the double pointer)

After:   head = 0x5555_2000  (newly allocated Node)
```

#### Use Case 2: Array of Strings / Array of Struct Pointers

```c
void sort_cities(City **cities, int n) {
    // Sort the pointer array — no struct data is moved
    for (int i = 0; i < n-1; i++)
        for (int j = i+1; j < n; j++)
            if (strcmp(cities[i]->name, cities[j]->name) > 0) {
                City *tmp  = cities[i];  // swap 8-byte pointers
                cities[i] = cities[j];
                cities[j] = tmp;
            }
}
```

### 15.3 Triple Pointers and Beyond

The same pattern extends to `T***`, though in practice this signals a design that should probably use a different data structure. It appears sometimes with 3D arrays or in operating system code.

---

## 16. Methods on Struct Pointers

### 16.1 C — Function Pointer Simulation

C has no methods, but the convention is to pass the struct as the first argument:

```c
typedef struct {
    double x, y;
} Point;

void point_translate(Point *p, double dx, double dy) {
    p->x += dx;
    p->y += dy;
}
double point_distance(const Point *a, const Point *b) {
    double dx = a->x - b->x, dy = a->y - b->y;
    return sqrt(dx*dx + dy*dy);
}
```

### 16.2 Go — Methods with Pointer Receivers

```go
type Point struct { X, Y float64 }

// Value receiver: receives a COPY; changes don't affect original
func (p Point) Magnitude() float64 {
    return math.Sqrt(p.X*p.X + p.Y*p.Y)
}

// Pointer receiver: receives pointer; changes affect original
func (p *Point) Translate(dx, dy float64) {
    p.X += dx
    p.Y += dy
}

p := Point{3, 4}
p.Translate(1, 1)      // Go auto-takes address: (&p).Translate(1, 1)
fmt.Println(p)         // {4 5}
fmt.Println(p.Magnitude())
```

**Rule**: use pointer receivers when:
1. The method needs to modify the receiver.
2. The receiver is large (avoid copying).
3. Other methods on the same type use pointer receivers (consistency).

### 16.3 Rust — `impl` Blocks and `self`

```rust
struct Point { x: f64, y: f64 }

impl Point {
    // Takes ownership (rare for methods)
    fn consume(self) { println!("consumed ({}, {})", self.x, self.y); }
    
    // Immutable reference
    fn magnitude(&self) -> f64 {
        (self.x*self.x + self.y*self.y).sqrt()
    }
    
    // Mutable reference
    fn translate(&mut self, dx: f64, dy: f64) {
        self.x += dx;
        self.y += dy;
    }
    
    // Constructor (associated function)
    fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
}

let mut p = Point::new(3.0, 4.0);
p.translate(1.0, 1.0);           // auto-borrows: (&mut p).translate(...)
println!("{}", p.magnitude());
```

---

## 17. Function Pointers Inside Structs

This is the foundation of **runtime polymorphism** in C (and the basis of vtables in C++/Rust trait objects).

### 17.1 C — Function Pointers in Structs

```c
// Declare a function pointer type
typedef double (*BinaryOp)(double, double);

typedef struct {
    const char *name;
    BinaryOp    apply;     // function pointer field
} Operation;

double add_fn(double a, double b) { return a + b; }
double mul_fn(double a, double b) { return a * b; }

Operation ops[] = {
    {"add", add_fn},
    {"mul", mul_fn},
};

// Call through the function pointer
double result = ops[0].apply(3.0, 4.0);  // 7.0
```

### 17.2 C — Vtable Simulation (Manual Polymorphism)

```c
typedef struct Animal Animal;

typedef struct {
    void    (*speak)(const Animal *self);
    double  (*speed)(const Animal *self);
} AnimalVtable;

struct Animal {
    const AnimalVtable *vtable;   // pointer to vtable
    const char         *name;
};

// Concrete implementations
void dog_speak(const Animal *a) { printf("%s says: Woof!\n", a->name); }
double dog_speed(const Animal *a) { return 15.0; }

void cat_speak(const Animal *a) { printf("%s says: Meow!\n", a->name); }
double cat_speed(const Animal *a) { return 12.0; }

static const AnimalVtable DOG_VT = { dog_speak, dog_speed };
static const AnimalVtable CAT_VT = { cat_speak, cat_speed };

// Polymorphic call:
void make_animal_speak(const Animal *a) {
    a->vtable->speak(a);   // dispatch through vtable pointer
}
```

Memory layout:
```
Animal instance:
┌──────────────────────┬──────────────────────┐
│  vtable* (8B)        │  name* (8B)           │
└──────────────────────┴──────────────────────┘
        │
        ▼
AnimalVtable:
┌──────────────────────┬──────────────────────┐
│  speak fn ptr (8B)   │  speed fn ptr (8B)   │
└──────────────────────┴──────────────────────┘
        │                       │
        ▼                       ▼
   dog_speak()             dog_speed()
```

### 17.3 Go — Interface Values Internally

A Go interface value is two words: a pointer to the type's method table, and a pointer to the data:

```
interface{} = [ *itab | *data ]

itab contains:
  - pointer to type descriptor
  - array of function pointers for each interface method
```

### 17.4 Rust — Trait Objects (`dyn Trait`)

```rust
trait Animal {
    fn speak(&self);
    fn speed(&self) -> f64;
}

struct Dog { name: String }
struct Cat { name: String }

impl Animal for Dog {
    fn speak(&self) { println!("{} says: Woof!", self.name); }
    fn speed(&self) -> f64 { 15.0 }
}
impl Animal for Cat {
    fn speak(&self) { println!("{} says: Meow!", self.name); }
    fn speed(&self) -> f64 { 12.0 }
}

// dyn Animal is a "fat pointer": data ptr + vtable ptr
fn make_speak(animal: &dyn Animal) {
    animal.speak();  // dynamic dispatch
}

let animals: Vec<Box<dyn Animal>> = vec![
    Box::new(Dog { name: "Rex".into() }),
    Box::new(Cat { name: "Whiskers".into() }),
];
for a in &animals { make_speak(a.as_ref()); }
```

Fat pointer layout:
```
&dyn Animal:
┌──────────────────┬──────────────────┐
│  data ptr (8B)   │  vtable ptr (8B) │
└──────────────────┴──────────────────┘
         │                   │
         ▼                   ▼
    Dog { name }        vtable for Dog:
                        ┌────────────────────┐
                        │ drop fn ptr        │
                        │ size               │
                        │ align              │
                        │ speak fn ptr       │
                        │ speed fn ptr       │
                        └────────────────────┘
```

---

## 18. Self-Referential Structs — Linked Lists & Trees

A struct that contains a **pointer to itself** (directly or via mutual recursion) is self-referential.

### 18.1 Singly Linked List

```
List: 1 → 2 → 3 → NULL

Node layout:
┌──────────┬──────────┐    ┌──────────┬──────────┐    ┌──────────┬──────────┐
│  val: 1  │  next ───│───▶│  val: 2  │  next ───│───▶│  val: 3  │  next=NUL│
└──────────┴──────────┘    └──────────┴──────────┘    └──────────┴──────────┘
0x5001                      0x5011                      0x5021
```

#### C Implementation

```c
#include <stdlib.h>
#include <stdio.h>

typedef struct Node {
    int          val;
    struct Node *next;   // pointer to same type — must use 'struct Node', not typedef
} Node;

Node *node_new(int val) {
    Node *n = malloc(sizeof(Node));
    n->val  = val;
    n->next = NULL;
    return n;
}

void list_push_front(Node **head, int val) {
    Node *n  = node_new(val);
    n->next  = *head;
    *head    = n;           // modify caller's head via double pointer
}

void list_print(const Node *head) {
    for (const Node *cur = head; cur; cur = cur->next)
        printf("%d → ", cur->val);
    printf("NULL\n");
}

void list_free(Node *head) {
    while (head) {
        Node *tmp = head->next;
        free(head);
        head = tmp;
    }
}

int main(void) {
    Node *head = NULL;
    list_push_front(&head, 3);
    list_push_front(&head, 2);
    list_push_front(&head, 1);
    list_print(head);   // 1 → 2 → 3 → NULL
    list_free(head);
}
```

#### Go Implementation

```go
package main

import "fmt"

type Node struct {
    Val  int
    Next *Node
}

func pushFront(head **Node, val int) {
    n := &Node{Val: val, Next: *head}
    *head = n
}

func printList(head *Node) {
    for cur := head; cur != nil; cur = cur.Next {
        fmt.Printf("%d → ", cur.Val)
    }
    fmt.Println("nil")
}

func main() {
    var head *Node
    pushFront(&head, 3)
    pushFront(&head, 2)
    pushFront(&head, 1)
    printList(head)  // 1 → 2 → 3 → nil
}
```

#### Rust Implementation

In Rust, self-referential structs must use `Box<T>` (or `Rc<T>` / `Arc<T>` for shared ownership), since the compiler must know the size of every type at compile time — a naive `Node { next: Node }` would be infinite size.

```rust
#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

impl List {
    fn new() -> Self { List::Nil }
    
    fn push(self, val: i32) -> Self {
        List::Cons(val, Box::new(self))
    }
    
    fn print(&self) {
        match self {
            List::Cons(v, next) => { print!("{} → ", v); next.print(); }
            List::Nil           => println!("Nil"),
        }
    }
}

fn main() {
    let list = List::new().push(3).push(2).push(1);
    list.print();  // 1 → 2 → 3 → Nil
}
```

### 18.2 Binary Search Tree

```
BST:
          ┌─────┐
          │  5  │
          └──┬──┘
         ┌───┴───┐
      ┌──▼──┐ ┌──▼──┐
      │  3  │ │  8  │
      └──┬──┘ └──┬──┘
      ┌──┴──┐ ┌──┴──┐
   ┌──▼──┐  │ │  ┌──▼──┐
   │  1  │  NULL NULL  │  9  │
   └─────┘               └─────┘
```

#### C BST

```c
typedef struct BST {
    int        val;
    struct BST *left;
    struct BST *right;
} BST;

BST *bst_insert(BST *root, int val) {
    if (!root) {
        BST *n  = malloc(sizeof(BST));
        n->val   = val;
        n->left  = n->right = NULL;
        return n;
    }
    if      (val < root->val) root->left  = bst_insert(root->left,  val);
    else if (val > root->val) root->right = bst_insert(root->right, val);
    return root;
}

void bst_inorder(const BST *root) {
    if (!root) return;
    bst_inorder(root->left);
    printf("%d ", root->val);
    bst_inorder(root->right);
}

void bst_free(BST *root) {
    if (!root) return;
    bst_free(root->left);
    bst_free(root->right);
    free(root);
}
```

#### Rust BST

```rust
#[derive(Debug)]
struct BST {
    val:   i32,
    left:  Option<Box<BST>>,
    right: Option<Box<BST>>,
}

impl BST {
    fn new(val: i32) -> Self {
        BST { val, left: None, right: None }
    }
    
    fn insert(self, v: i32) -> Self {
        match v.cmp(&self.val) {
            std::cmp::Ordering::Less => BST {
                left: Some(match self.left {
                    Some(l) => Box::new(l.insert(v)),
                    None    => Box::new(BST::new(v)),
                }),
                ..self
            },
            std::cmp::Ordering::Greater => BST {
                right: Some(match self.right {
                    Some(r) => Box::new(r.insert(v)),
                    None    => Box::new(BST::new(v)),
                }),
                ..self
            },
            _ => self,
        }
    }
    
    fn inorder(&self) {
        if let Some(l) = &self.left  { l.inorder(); }
        print!("{} ", self.val);
        if let Some(r) = &self.right { r.inorder(); }
    }
}
```

---

## 19. Pointer Aliasing

**Aliasing** means two or more pointers point to the same (or overlapping) memory.

```
int x = 42;
int *p = &x;
int *q = &x;   // p and q are aliases — same address

*p = 10;       // modifies x
// q now also sees 10, because q == p
```

### 19.1 Why Aliasing Matters for Optimisation

The compiler can't reorder or eliminate loads/stores if it suspects aliasing. Consider:

```c
void add(int *a, int *b, int *result) {
    *result = *a + *b;
    // If a == result or b == result, *a or *b has changed!
}
```

### 19.2 `restrict` in C

The `restrict` keyword promises the compiler that a pointer is the **only** way to access the data it points to in that scope:

```c
void add(int * restrict a, int * restrict b, int * restrict result) {
    *result = *a + *b;  // compiler may generate faster code: no alias possible
}
```

### 19.3 Rust's Aliasing Guarantee

Rust's type system enforces at **compile time**:
- Any number of immutable (`&T`) references may coexist.
- Exactly **one** mutable (`&mut T`) reference may exist at a time, and no immutable references may coexist with it.

This makes aliasing mutable references impossible in safe Rust, enabling aggressive compiler optimisations (the `noalias` LLVM attribute on all `&mut T` parameters).

```rust
let mut x = 42;
let p = &mut x;
// let q = &mut x;   // COMPILE ERROR: cannot borrow `x` as mutable more than once
*p = 10;
```

### 19.4 Go's Aliasing Behavior

Go has no aliasing annotations. The compiler conservatively assumes pointers may alias. Use `sync/atomic` or channels for safe concurrent mutation.

---

## 20. Ownership, Borrowing & Lifetimes (Rust)

This section is Rust-specific but represents the most important mental model upgrade for writing safe struct-pointer code.

### 20.1 Ownership Rules

Every value in Rust has a single **owner**. When the owner goes out of scope, the value is dropped (memory freed).

```rust
{
    let p = Point { x: 3, y: 7 };   // p owns the Point
}  // ← Point is dropped here; memory freed automatically
```

### 20.2 Move Semantics

Assigning or passing a value **moves** ownership (unless the type implements `Copy`):

```rust
let p1 = Point { x: 3, y: 7 };
let p2 = p1;            // ownership moved to p2
// println!("{}", p1.x);  // ERROR: p1 was moved
println!("{}", p2.x);   // OK
```

### 20.3 Borrowing with References

A reference `&T` **borrows** a value without taking ownership:

```rust
fn print_point(p: &Point) {           // borrows p
    println!("({}, {})", p.x, p.y);
}  // borrow ends here; Point not dropped

let p = Point { x: 3, y: 7 };
print_point(&p);    // borrow
print_point(&p);    // borrow again — fine, p still owned here
println!("{}", p.x); // still accessible
```

### 20.4 Mutable Borrowing

```rust
fn double(p: &mut Point) {
    p.x *= 2;
    p.y *= 2;
}

let mut p = Point { x: 3, y: 7 };
double(&mut p);
println!("{}", p.x);  // 6
```

**The exclusive mutable reference rule**:
```
At any given point in time, for a given value T, you can have EITHER:
  - Any number of &T  (shared, immutable borrows)
  OR
  - Exactly one &mut T (exclusive, mutable borrow)
  but NOT both.
```

### 20.5 Lifetimes

A lifetime is a compile-time label that describes **how long** a reference is valid. The borrow checker uses lifetimes to ensure no reference outlives the data it points to.

```rust
// 'a is a lifetime parameter: output lives as long as input
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

For structs holding references, you must annotate lifetimes:

```rust
struct Excerpt<'a> {
    text: &'a str,       // must not outlive the string it borrows from
}

fn main() {
    let novel = String::from("Call me Ishmael...");
    let first = novel.split('.').next().unwrap();
    let ex = Excerpt { text: first };  // 'a = lifetime of 'novel'
    println!("{}", ex.text);
}   // ex is dropped before novel → valid
```

### 20.6 Smart Pointers

| Type | Description | Thread-safety |
|------|-------------|---------------|
| `Box<T>` | Single-owner heap allocation | Yes (transfer between threads) |
| `Rc<T>` | Reference-counted shared ownership | Single-thread only |
| `Arc<T>` | Atomic ref-counted shared ownership | Multi-thread safe |
| `Cell<T>` | Interior mutability (Copy types) | Single-thread |
| `RefCell<T>` | Runtime-checked interior mutability | Single-thread |
| `Mutex<T>` | Mutex-guarded interior mutability | Multi-thread |

```rust
use std::rc::Rc;
use std::cell::RefCell;

// Shared, mutable struct accessible from multiple places
let shared = Rc::new(RefCell::new(Point { x: 0, y: 0 }));
let clone1 = Rc::clone(&shared);
let clone2 = Rc::clone(&shared);

clone1.borrow_mut().x = 5;
println!("{}", clone2.borrow().x);   // 5 — same Point
```

---

## 21. Interface Dispatch via Struct Pointers

Understanding how Go interfaces and Rust trait objects are implemented in terms of struct pointers gives you the right mental model for dynamic dispatch cost.

### 21.1 Go Interface Internals

An interface value holds two pointers:

```
Go interface value (16 bytes):
┌──────────────┬──────────────┐
│  *itab       │  *data       │
└──────────────┴──────────────┘
      │                │
      ▼                ▼
   itab:            actual data (e.g., *Dog or Dog value)
   ┌─────────────┐
   │ *type       │  → type descriptor
   │ *interface  │  → interface type descriptor
   │ hash        │
   │ fn[0]       │  → first method pointer
   │ fn[1]       │  → second method pointer
   └─────────────┘
```

### 21.2 Rust Trait Object Internals

A `&dyn Trait` is a **fat pointer** (16 bytes):

```
&dyn Trait fat pointer (16 bytes):
┌──────────────┬──────────────┐
│  data ptr    │  vtable ptr  │
└──────────────┴──────────────┘
      │                │
      ▼                ▼
  concrete data     vtable:
  (e.g., Dog)       ┌──────────────────┐
                    │ drop fn ptr      │ (destructor)
                    │ size (usize)     │
                    │ align (usize)    │
                    │ method_1 fn ptr  │
                    │ method_2 fn ptr  │
                    └──────────────────┘
```

### 21.3 Cost of Dynamic Dispatch

```
Static dispatch (monomorphisation, inlineable):
    fn process<T: Animal>(a: &T) { a.speak(); }
    → compiler generates specialised code for each T
    → zero overhead, inlineable

Dynamic dispatch (vtable lookup):
    fn process(a: &dyn Animal) { a.speak(); }
    → load data ptr from fat ptr
    → load vtable ptr from fat ptr
    → load speak fn ptr from vtable[offset]
    → indirect call
    → cannot be inlined (usually)
    → extra ~2 pointer dereferences per call
```

---

## 22. Memory Safety & Common Pitfalls

### 22.1 Dangling Pointer (Use-After-Free)

```c
// C — most common and dangerous bug
struct Node *n = malloc(sizeof(struct Node));
n->val = 42;
free(n);
printf("%d\n", n->val);  // USE AFTER FREE — undefined behavior
n = NULL;                // good habit: null out after free
```

Timeline:
```
t=0: malloc → n = 0x5001
t=1: free(n) → heap reclaims 0x5001 (may be reallocated for other use)
t=2: n->val → reads garbage (or crashes, or security vulnerability)
```

Rust prevents this by compile-time borrow checking. Go's GC prevents it by keeping memory alive while any reference exists.

### 22.2 Buffer Overflow via Struct Pointer

```c
struct Fixed { int data[4]; int secret; };
struct Fixed f = {{0}, 0xDEADBEEF};
int *p = f.data;
p[4] = 0;   // WRITES TO f.secret — buffer overflow!
```

```
Memory:
 data[0] data[1] data[2] data[3]   secret
┌───────┬───────┬───────┬───────┬───────┐
│   0   │   0   │   0   │   0   │ DEAD  │
└───────┴───────┴───────┴───────┴───────┘
                                    ↑
                                  p[4] writes here!
```

### 22.3 Memory Leak

```c
void leak(void) {
    struct BigData *p = malloc(1024 * sizeof(struct BigData));
    // ... use p ...
    return;   // forgot free(p) — 1024 * sizeof(BigData) bytes leaked
}
```

Rust: impossible — `Box<T>` auto-drops.
Go: impossible for normal allocations — GC collects unreachable memory.

### 22.4 Double Free

```c
free(p);
free(p);   // DOUBLE FREE — heap corruption, security vulnerability
```

Rust: impossible — the ownership system ensures `drop` is called exactly once.

### 22.5 Uninitialized Memory

```c
struct Point p;   // p.x and p.y are GARBAGE (uninitialized)
printf("%d\n", p.x);   // undefined behavior
```

Rust: every variable must be explicitly initialised before use (compiler enforces).

### 22.6 Pointer Invalidation

```c
int *ptrs[3];
int arr[3] = {1,2,3};
for (int i = 0; i < 3; i++) ptrs[i] = &arr[i];
// later...
realloc(arr, ...)  // arr might move! ptrs[*] are now dangling
// (realloc returns new pointer; old address may be freed)
```

Rust's borrow checker prevents holding references across a mutation that could invalidate them:
```rust
let mut v = vec![1, 2, 3];
let first = &v[0];
v.push(4);              // ERROR: cannot borrow as mutable while immutably borrowed
println!("{}", first);  // first might be dangling if push reallocated
```

### 22.7 Checklist for Safe Struct Pointer Usage in C

```
□  Always check malloc/calloc return value for NULL
□  Always initialise structs after allocation
□  Match every malloc with exactly one free
□  Never return pointer to stack-allocated struct
□  Set pointer to NULL after free
□  Avoid pointer arithmetic beyond array bounds
□  Use const* for read-only access to prevent accidental mutation
□  Use valgrind / AddressSanitizer during development
□  Prefer opaque pointers for encapsulation in libraries
```

---

## 23. Patterns and Idioms

### 23.1 Opaque Pointer / Handle Pattern (C)

Hide struct internals behind a pointer type — callers only see `T*`, never the fields.

```c
// --- mylib.h (public interface) ---
typedef struct MyState MyState;           // forward declaration; size unknown to callers

MyState *mystate_create(int config);
void     mystate_do_work(MyState *s);
void     mystate_destroy(MyState *s);

// --- mylib.c (implementation) ---
struct MyState {
    int    config;
    double accumulator;
    // ... internal fields hidden from callers
};

MyState *mystate_create(int config) {
    MyState *s = calloc(1, sizeof(MyState));
    s->config  = config;
    return s;
}
void mystate_do_work(MyState *s) { s->accumulator += s->config; }
void mystate_destroy(MyState *s) { free(s); }
```

This is how the C standard library (FILE*, ...) and most C APIs are designed.

### 23.2 Builder Pattern (Go)

```go
type Config struct {
    Host    string
    Port    int
    Timeout time.Duration
}

type ConfigBuilder struct { cfg Config }

func NewConfigBuilder() *ConfigBuilder { return &ConfigBuilder{} }

func (b *ConfigBuilder) WithHost(h string) *ConfigBuilder {
    b.cfg.Host = h; return b          // return self for chaining
}
func (b *ConfigBuilder) WithPort(p int) *ConfigBuilder {
    b.cfg.Port = p; return b
}
func (b *ConfigBuilder) Build() Config { return b.cfg }

cfg := NewConfigBuilder().WithHost("localhost").WithPort(8080).Build()
```

### 23.3 Builder / Constructor Pattern (Rust)

```rust
#[derive(Debug, Default)]
struct Config {
    host:    String,
    port:    u16,
    timeout: std::time::Duration,
}

struct ConfigBuilder { cfg: Config }

impl ConfigBuilder {
    fn new() -> Self { ConfigBuilder { cfg: Config::default() } }
    fn host(mut self, h: &str) -> Self { self.cfg.host = h.into(); self }
    fn port(mut self, p: u16) -> Self  { self.cfg.port = p;        self }
    fn build(self) -> Config           { self.cfg }
}

let cfg = ConfigBuilder::new().host("localhost").port(8080).build();
```

### 23.4 Arena Allocator (C)

For short-lived objects, pre-allocate a large block and bump-allocate within it. All memory is freed at once when the arena is destroyed.

```c
typedef struct {
    char  *base;
    size_t used;
    size_t capacity;
} Arena;

Arena arena_create(size_t cap) {
    return (Arena){ malloc(cap), 0, cap };
}

void *arena_alloc(Arena *a, size_t size) {
    // align to 8 bytes
    size = (size + 7) & ~7;
    if (a->used + size > a->capacity) return NULL;
    void *ptr = a->base + a->used;
    a->used  += size;
    return ptr;
}

void arena_destroy(Arena *a) {
    free(a->base);
    a->base = NULL; a->used = a->capacity = 0;
}

// Usage:
Arena arena = arena_create(4096);
struct Node *n1 = arena_alloc(&arena, sizeof(struct Node));
struct Node *n2 = arena_alloc(&arena, sizeof(struct Node));
// ... no individual frees needed ...
arena_destroy(&arena);   // frees everything at once
```

```
Arena memory block (4096 bytes):
0         8         16        24       ...      4096
┌─────────┬─────────┬─────────┬─── ... ─────────┐
│  Node1  │  Node2  │  free   │       free       │
└─────────┴─────────┴─────────┴─── ... ─────────┘
          ↑
       used = 16
```

### 23.5 Struct Embedding / Inheritance (Go)

```go
type Animal struct {
    Name string
}
func (a *Animal) Breathe() { fmt.Println(a.Name, "breathes") }

type Dog struct {
    Animal              // embedded by value — "promotion"
    Breed string
}
func (d *Dog) Bark() { fmt.Println(d.Name, "barks") }

d := Dog{Animal: Animal{"Rex"}, Breed: "Labrador"}
d.Breathe()  // promoted from Animal — d.Animal.Breathe()
d.Bark()
```

Memory layout:
```
Dog struct:
┌─────────────────────┬──────────────────────┐
│  Animal (embedded)  │  Breed string (16B)  │
│  ┌────────────────┐ │                      │
│  │ Name string    │ │                      │
│  └────────────────┘ │                      │
└─────────────────────┴──────────────────────┘
```

### 23.6 Intrusive Linked List (C — Linux Kernel Style)

Instead of storing the linked-list node externally, embed the `next`/`prev` pointers inside the struct, and use `offsetof` to get back to the containing struct:

```c
#include <stddef.h>

typedef struct ListHead {
    struct ListHead *next;
    struct ListHead *prev;
} ListHead;

typedef struct Task {
    int      pid;
    char     name[16];
    ListHead list;    // embedded list head
} Task;

// Get the Task* from a ListHead* using container_of macro
#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

// Example: iterate over task list
void print_tasks(ListHead *head) {
    for (ListHead *cur = head->next; cur != head; cur = cur->next) {
        Task *t = container_of(cur, Task, list);
        printf("PID %d: %s\n", t->pid, t->name);
    }
}
```

```
Intrusive list memory diagram:

Task A:                              Task B:
┌──────┬──────────┬────────────┐    ┌──────┬──────────┬────────────┐
│ pid  │  name[]  │    list    │    │ pid  │  name[]  │    list    │
│      │          │ ┌────┬────┐│    │      │          │ ┌────┬────┐│
│  1   │ "init"   │ │next│prev││    │  2   │ "bash"   │ │next│prev││
│      │          │ └─┬──┴──┬─┘│    │      │          │ └─┬──┴──┬─┘│
└──────┴──────────┴──│──────│──┘    └──────┴──────────┴──│──────│──┘
                      │      └────────────────────────────┘
                      └────────────────────────────────────▶
```

---

## 24. Mental Models Summary

### 24.1 The Indirection Mental Model

Every struct pointer adds one level of indirection. Visualise a chain of arrows:

```
x: int = 42
p: *int ─────────────────▶ 42
pp: **int ──────────────▶  p ─────▶ 42
ppp: ***int ─────────▶  pp ──▶ p ──▶ 42
```

Each `*` in a type means "one more arrow to follow before you reach the data".

### 24.2 The Address = Array Index Mental Model

Memory is one giant array of bytes. A pointer is just an index into that array. `ptr->field` means "go to index `ptr`, skip `offset_of_field` bytes, and read `sizeof_field` bytes".

```
Memory[ptr + offsetof(T, field)]  =  ptr->field
```

### 24.3 The Ownership Graph Mental Model (Rust/C++)

Draw a directed graph where every node is a value and every edge is an owning pointer. The graph must be a **DAG** (no cycles), or you need reference counting. `Box<T>` is an owning edge; `&T` is a non-owning borrow (dashed arrow that cannot outlive the owner).

```
 Box<Node>       Box<Node>
 ┌────────┐      ┌────────┐
 │ Node A │─────▶│ Node B │─────▶ (None)
 └────────┘      └────────┘
     ↑
     │  (borrow &Node, dashed — not owning)
  fn read_node(n: &Node) { ... }
```

### 24.4 The Lifetime Scope Mental Model (Rust)

Visualise lifetimes as nested scopes on a timeline. A reference's lifetime must fit entirely within the lifetime of the data it points to:

```
Timeline ───────────────────────────────────────────▶

Scope of `data`:    [========================]
Scope of `ref`:         [=============]          ← OK: ref nested inside data
Scope of `bad_ref`:     [===================]    ← ERROR: ref outlives data
```

### 24.5 The Two-Word Interface Mental Model (Go/Rust)

Any dynamic-dispatch pointer (Go interface, Rust `dyn Trait`) is always **two machine words**:

```
[data ptr | type/vtable ptr]
```

Static dispatch (`T: Trait` in Rust generics) is a single pointer to the concrete data — zero overhead.

### 24.6 Stack Frame Lifetime Mental Model

Every function call pushes a stack frame. When the function returns, the frame is **gone**. Any pointer into a stack frame that escapes the function is a time bomb. If you need the data to outlive the function, put it on the heap.

```
CALL STACK over time:

main() calls foo() calls bar()

┌──────────┐
│  bar()   │  ← TOP OF STACK
├──────────┤
│  foo()   │
├──────────┤
│  main()  │
└──────────┘

bar() returns:
┌──────────┐
│  foo()   │  ← bar's frame DESTROYED
├──────────┤
│  main()  │
└──────────┘

Any *Point that lived in bar()'s frame is now DANGLING.
```

---

## Appendix A: Size Reference (x86-64 LP64)

| Type | C | Go | Rust | Size (bytes) |
|------|---|----|------|--------------|
| Pointer | `void*` / `T*` | `*T` | `*const T` / `*mut T` | 8 |
| Reference | — | — | `&T` / `&mut T` | 8 |
| Fat pointer | — | `interface{}` | `&dyn Trait` | 16 |
| Slice header | — | `[]T` | `&[T]` | 16 (ptr + len) |
| String header | `char*` (C-str) | `string` | `&str` | 16 (ptr + len) |
| Box | — | — | `Box<T>` | 8 |

## Appendix B: Quick Syntax Cross-Reference

| Operation | C | Go | Rust (safe) |
|-----------|---|----|-------------|
| Declare pointer | `T *p` | `var p *T` | `let p: &T` |
| Declare mut pointer | `T *p` | `var p *T` | `let p: &mut T` |
| Take address | `&val` | `&val` | `&val` |
| Take mut address | `&val` | `&val` | `&mut val` |
| Deref pointer | `*p` | `*p` / `p.field` | `*p` / `p.field` |
| Field via pointer | `p->field` | `p.field` | `p.field` |
| Null/nil pointer | `NULL` | `nil` | `None` (Option) |
| Heap alloc | `malloc(sizeof(T))` | `new(T)` / `&T{}` | `Box::new(T {...})` |
| Heap free | `free(p)` | GC | auto (Drop) |
| Pointer arithmetic | `p + n` | `unsafe` only | `unsafe { p.add(n) }` |

## Appendix C: Tooling for Pointer Bugs

| Tool | Language | What It Catches |
|------|----------|-----------------|
| **Valgrind** | C/C++ | Memory leaks, use-after-free, invalid reads |
| **AddressSanitizer (ASan)** | C/C++/Go | Buffer overflows, use-after-free (runtime) |
| **MemorySanitizer (MSan)** | C/C++ | Uninitialized memory reads |
| **UndefinedBehaviorSanitizer (UBSan)** | C/C++ | Null deref, integer overflow |
| **Go race detector** (`-race`) | Go | Data races on shared pointers |
| **Rust borrow checker** | Rust | All of the above, at compile time |
| **Miri** | Rust | Detects undefined behavior in unsafe Rust |

---

*End of Guide*

This is a large document — let me build it directly.Here's your complete guide. Here's a quick map of what's inside:

**Foundations (Sections 1–5)** — Memory address space with ASCII layout, byte/alignment mechanics, why `sizeof(pointer)` is always 8 on 64-bit, struct field padding with full byte-offset diagrams, and the core struct-pointer concept with a drawn memory diagram.

**Allocation & Access (Sections 6–9)** — Stack vs heap with ASCII call-stack diagrams, Go's escape analysis, Rust's `Box<T>`, dereferencing (what the CPU actually does at the instruction level), the `->` vs `.` vs auto-deref difference across all three languages, and pointer arithmetic with concrete address math.

**Functions & Ownership (Sections 10–12)** — Pass-by-value vs pass-by-pointer with stack frame diagrams, the C dangling-return bug vs Go escape analysis vs Rust compile error, and null/nil safety including Rust's `Option<&T>` zero-cost representation.

**Advanced Concepts (Sections 13–21)** — Nested structs (inline vs pointer), AoS vs AoP cache tradeoffs, double and triple pointers with the "modify caller's pointer" pattern, pointer receivers in Go/Rust, vtable simulation in C, self-referential structs (linked list + BST in all three languages), aliasing and `restrict`, and full Rust ownership/borrowing/lifetime treatment including all smart pointer types.

**Safety & Patterns (Sections 22–24)** — All classic pointer bugs (use-after-free, buffer overflow, leak, double-free, uninit memory) with timeline diagrams, opaque pointer / arena / builder / intrusive list patterns, and the mental models summary which is the most important part for building a correct internal model.