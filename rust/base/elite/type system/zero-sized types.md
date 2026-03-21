# Zero-Sized Types (ZSTs) — Deep Mastery Guide

> *"The most powerful abstractions occupy no space at all."*

---

## Table of Contents

1. [Foundational Concepts — What Is a Type?](#1-foundational-concepts)
2. [What Is a Zero-Sized Type?](#2-what-is-a-zero-sized-type)
3. [Memory Layout & The Alignment Theorem](#3-memory-layout--the-alignment-theorem)
4. [ZSTs in C](#4-zsts-in-c)
5. [ZSTs in Go](#5-zsts-in-go)
6. [ZSTs in Rust](#6-zsts-in-rust)
7. [PhantomData — The Ghost Type](#7-phantomdata--the-ghost-type)
8. [The Never Type (`!`)](#8-the-never-type-)
9. [ZSTs as Marker Types & Type-State Programming](#9-zsts-as-marker-types--type-state-programming)
10. [ZSTs in Collections — The "Hashset as HashMap" Trick](#10-zsts-in-collections)
11. [ZSTs and Pointer Arithmetic](#11-zsts-and-pointer-arithmetic)
12. [ZSTs and Trait Objects](#12-zsts-and-trait-objects)
13. [ZSTs and Generics / Monomorphization](#13-zsts-and-generics--monomorphization)
14. [ZSTs as Compile-Time Capabilities & Tokens](#14-zsts-as-compile-time-capabilities--tokens)
15. [ZSTs in Concurrency — Channel Signaling](#15-zsts-in-concurrency--channel-signaling)
16. [Advanced Patterns — Expert-Level Usage](#16-advanced-patterns)
17. [Pitfalls and Gotchas](#17-pitfalls-and-gotchas)
18. [Mental Models & Summary](#18-mental-models--summary)

---

## 1. Foundational Concepts

Before we go deep, we need to establish shared vocabulary. These terms will appear throughout.

### What Is a "Type"?

A **type** is a compile-time label that tells the compiler:
- How many bytes of memory this value occupies (its **size**)
- What operations are valid on it
- How to align it in memory

```
TYPE = { size, alignment, valid_operations, semantics }
```

### What Is "Size" of a Type?

The **size** (`sizeof` in C, `size_of::<T>()` in Rust, `unsafe.Sizeof` in Go) is the number of **bytes** a value of that type occupies in memory.

```
i32  -> 4 bytes
f64  -> 8 bytes
bool -> 1 byte
```

### What Is "Alignment"?

The CPU reads memory most efficiently when values start at addresses that are **multiples of their alignment requirement**.

```
i32  -> alignment 4  -> must start at address divisible by 4 (0, 4, 8, 12, ...)
f64  -> alignment 8  -> must start at address divisible by 8 (0, 8, 16, ...)
u8   -> alignment 1  -> can start anywhere
```

### ASCII: Memory Alignment Visualization

```
Address: 0x00  0x01  0x02  0x03  0x04  0x05  0x06  0x07
         +-------------------------+
i32@0x00 |  B0 |  B1 |  B2 |  B3 |                      OK: aligned
         +-------------------------+

Address: 0x00  0x01  0x02  0x03  0x04  0x05  0x06  0x07
                   +-------------------------+
i32@0x01           |  B0 |  B1 |  B2 |  B3 |            BAD: misaligned
                   +-------------------------+
```

### What Is a "Value Type" vs "Reference Type"?

- **Value type**: data stored directly (stack or inline in struct) — `int`, `struct`, `[T; N]`
- **Reference type**: a pointer (address) to data elsewhere — `*int`, `&T`, `Box<T>`

ZSTs are always **value types** — they hold no data, so there is nothing to point to.

---

## 2. What Is a Zero-Sized Type?

A **Zero-Sized Type (ZST)** is any type whose size is **exactly 0 bytes**.

```
sizeof(ZST) == 0
```

This sounds impossible at first. "How can something exist if it has no bytes?" The answer is that a ZST **carries information through the type system at compile time**, not through runtime bytes.

### The Key Insight

> A ZST is a type whose **existence** is meaningful, but whose **value** carries no information beyond the type itself.

Because there is only one possible value of a ZST (it is either present or not), storing it at runtime is unnecessary. The compiler erases them from the final binary.

### Decision Tree: Is a Type a ZST?

```
Does the type contain any fields/data?
        |
        +--- YES ---> Not a ZST
        |
        +--- NO  ---> Does it have exactly one possible value?
                            |
                            +--- YES ---> ZST (confirmed)
                            |
                            +--- NO  ---> Depends (e.g., Never type '!' has 0 values)
```

### Common ZSTs Across Languages

| Language | ZST                          | Notes                            |
|----------|------------------------------|----------------------------------|
| Rust     | `()`                         | Unit type, the "nothing" value   |
| Rust     | `struct Foo;`                | Unit struct                      |
| Rust     | `PhantomData<T>`             | Phantom type marker              |
| Rust     | `[T; 0]`                     | Zero-length array                |
| Rust     | `!`                          | Never type (0 values, not 1!)    |
| Go       | `struct{}`                   | Empty struct                     |
| C        | `struct Empty {};`           | Empty struct (platform-specific) |

---

## 3. Memory Layout & The Alignment Theorem

### The C Standard on Empty Structs

The C standard (C99/C11) **does not permit** zero-sized objects. An empty struct in standard C has **undefined behavior** if you take its sizeof. In practice, GCC/Clang give it size 0 (as a GCC extension), but MSVC may give size 1.

```c
struct Empty {};
printf("%zu\n", sizeof(struct Empty)); // GCC: 0 (extension), MSVC: 1+
```

### Rust's Guarantee

Rust **explicitly guarantees** that ZSTs have `size_of::<T>() == 0` and `align_of::<T>() == 1`.

```
For a ZST T in Rust:
  std::mem::size_of::<T>()  == 0
  std::mem::align_of::<T>() == 1  (minimum possible alignment)
```

### Go's Guarantee

Go guarantees that `unsafe.Sizeof(struct{}{}) == 0`.

### The "Multiple ZSTs at Same Address" Rule

Because ZSTs have size 0, multiple ZSTs can share the **same address** without conflict:

```
Normal types:              ZSTs:
+----------+              +----------------------------+
| a: i32   | @ 0x1000    | x: ()  @ 0x1000 (or any)  |
| b: i32   | @ 0x1004    | y: ()  @ 0x1000 (same!)   |
+----------+             | z: ()  @ 0x1000 (same!)   |
                          +----------------------------+
```

In Rust, ZST references often point to address `0x1` (a special non-null dangling address that is never actually dereferenced).

### Why Size-0 is Safe

Reading or writing a ZST requires **0 bytes** of memory access. Therefore:
- No buffer overflow possible
- No aliasing violations possible
- All ZST pointers are trivially "valid" (no actual memory is accessed)

### ASCII: ZST Memory Model

```
Stack frame of a function:
+------------------------------------------+
|  local: i32    [4 bytes]  @ offset 0     |
|  local: f64    [8 bytes]  @ offset 8     |
|  local: ()     [0 bytes]  @ (no offset)  | <-- ZST takes no stack space
|  local: Marker [0 bytes]  @ (no offset)  | <-- ZST takes no stack space
+------------------------------------------+
Total: 12 bytes  (not 12 + 0 + 0 = 12, but the ZSTs truly vanish)
```

---

## 4. ZSTs in C

C has no first-class ZST support, but we can simulate the concept.

### 4.1 The Empty Struct Problem

```c
#include <stdio.h>
#include <stddef.h>

// WARNING: Non-standard -- GCC extension
// Standard C says empty structs have undefined behavior for sizeof
struct Empty {};

int main(void) {
    struct Empty e;
    printf("sizeof(struct Empty) = %zu\n", sizeof(struct Empty));
    // GCC (gnu11):  0
    // MSVC:         1+ (not zero)
    return 0;
}
```

Compile with GCC extension:
```bash
gcc -std=gnu11 -Wall -Wextra empty_struct.c -o empty_struct
```

### 4.2 The `void` Type: C's Closest ZST

`void` in C is the closest thing to a ZST:
- You cannot declare a variable of type `void`
- You cannot take `sizeof(void)` (undefined behavior in standard C)
- It represents "no value" as a return type
- `void*` is a generic pointer (type information is erased)

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// void as "unit" return: function does something but returns nothing
void greet(const char* name) {
    printf("Hello, %s\n", name);
    // implicit: return;  (returns void)
}

// void* as generic pointer: type info erased, size must be passed explicitly
void generic_swap(void* a, void* b, size_t size) {
    char temp[256]; // fixed buffer for demo
    if (size > sizeof(temp)) return;
    memcpy(temp, a, size);
    memcpy(a,    b, size);
    memcpy(b, temp, size);
}

int main(void) {
    greet("World");

    int x = 10, y = 20;
    generic_swap(&x, &y, sizeof(int));
    printf("x=%d y=%d\n", x, y); // x=20 y=10
    return 0;
}
```

### 4.3 Simulating Marker Types in C

Since C has no ZSTs, marker types are simulated with **empty structs** or **typedef tricks**:

```c
#include <stdio.h>
#include <stdint.h>

// ------------------------------------------------------------------
// Simulating type-state with runtime tag (C limitation)
// C cannot enforce state transitions at compile time like Rust can.
// ------------------------------------------------------------------

typedef enum { STATE_LOCKED = 0, STATE_UNLOCKED = 1 } ResourceState;

typedef struct {
    int            fd;    // file descriptor
    ResourceState  state; // runtime tag -- C has no compile-time states
} Resource;

Resource lock(Resource r) {
    if (r.state != STATE_UNLOCKED) {
        fprintf(stderr, "Error: resource not unlocked\n");
        return r;
    }
    r.state = STATE_LOCKED;
    printf("Locked resource fd=%d\n", r.fd);
    return r;
}

Resource unlock(Resource r) {
    if (r.state != STATE_LOCKED) {
        fprintf(stderr, "Error: resource not locked\n");
        return r;
    }
    r.state = STATE_UNLOCKED;
    printf("Unlocked resource fd=%d\n", r.fd);
    return r;
}

int main(void) {
    Resource r = { .fd = 3, .state = STATE_UNLOCKED };
    r = lock(r);
    r = unlock(r);
    // Notice: C enforces this at RUNTIME -- errors only caught at runtime
    // Rust with ZST type-states catches this at COMPILE TIME
    return 0;
}
```

### 4.4 ZST-Like Arrays: The Flexible Array Member

A zero-length array `T arr[0]` is a GCC extension used as a **flexible array member**. Used extensively in the Linux kernel:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

// The "struct hack": flexible array member
// data[0] takes 0 bytes in the struct itself
struct Packet {
    uint32_t length;
    uint8_t  data[0]; // zero-length array: 0 bytes in sizeof(struct Packet)
};

int main(void) {
    uint32_t data_size = 10;

    // Allocate struct header + data together in one malloc
    struct Packet* p = malloc(sizeof(struct Packet) + data_size);
    p->length = data_size;

    for (uint32_t i = 0; i < data_size; i++) {
        p->data[i] = (uint8_t)i;
    }

    printf("sizeof(struct Packet) = %zu\n", sizeof(struct Packet)); // 4 (just length)
    printf("data[5] = %u\n", p->data[5]);                           // 5
    free(p);
    return 0;
}
```

```
Memory Layout after malloc(sizeof(Packet) + 10):
+------------------------------------------+
| length (4 bytes) | d[0] d[1] ... d[9]    |
+------------------------------------------+
  ^-- sizeof = 4     ^-- allocated separately, after the struct
```

### 4.5 `_Static_assert`: Compile-Time Checks in C

```c
#include <assert.h>
#include <stddef.h>

struct Marker { char _[0]; }; // GCC: 0 bytes

// Verify at compile time (C11 feature)
_Static_assert(sizeof(struct Marker) == 0, "Marker must be zero-sized");
_Static_assert(sizeof(int) == 4,           "Expected 32-bit int");
_Static_assert(_Alignof(double) == 8,      "Expected 8-byte alignment for double");
```

---

## 5. ZSTs in Go

Go has **excellent ZST support** through the empty struct `struct{}`.

### 5.1 The Empty Struct

```go
package main

import (
    "fmt"
    "unsafe"
)

func main() {
    var s struct{}
    fmt.Println(unsafe.Sizeof(s))   // 0
    fmt.Println(unsafe.Alignof(s))  // 1

    // Multiple ZSTs can be created freely -- no heap impact
    a := struct{}{}
    b := struct{}{}

    // There is only one possible value of struct{}, so they compare equal
    fmt.Println(a == b) // true

    _ = a
    _ = b
}
```

### 5.2 The Go Memory Model for ZSTs

Go has a special rule: **ZST pointers may or may not be equal**. Multiple ZST variables *may* share the same address. The spec does not guarantee it either way.

```go
package main

import (
    "fmt"
    "unsafe"
)

func main() {
    a := struct{}{}
    b := struct{}{}

    pa := unsafe.Pointer(&a)
    pb := unsafe.Pointer(&b)

    // May print same or different address -- implementation detail
    fmt.Printf("&a = %p\n", pa)
    fmt.Printf("&b = %p\n", pb)
    fmt.Println(pa == pb) // May be true! -- never rely on this

    // ALWAYS compare values, not pointers, for ZSTs
    fmt.Println(a == b) // always true -- this is safe
}
```

**Go spec says:** "Pointers to distinct zero-size variables may or may not be equal."

### 5.3 The Channel Signal Pattern

The most common Go ZST pattern: using `struct{}` as a **signal channel** that carries no payload.

```go
package main

import (
    "fmt"
    "time"
)

// ----------------------------------------------------------------
// Pattern: Done channel for goroutine coordination
// ----------------------------------------------------------------

func worker(id int, done <-chan struct{}) {
    for {
        select {
        case <-done:
            fmt.Printf("Worker %d: received shutdown signal\n", id)
            return
        default:
            fmt.Printf("Worker %d: working...\n", id)
            time.Sleep(100 * time.Millisecond)
        }
    }
}

func main() {
    done := make(chan struct{})

    for i := 0; i < 3; i++ {
        go worker(i, done)
    }

    time.Sleep(300 * time.Millisecond)

    // Signal ALL workers to stop by closing the channel
    // No data is sent -- just the closing event
    close(done)

    time.Sleep(100 * time.Millisecond)
    fmt.Println("All workers stopped")
}
```

Why `struct{}` and not `bool`?

```
chan bool     -> 1 byte per message in channel buffer
chan struct{} -> 0 bytes per message in channel buffer

For a buffered channel of 1000 signals:
  make(chan bool,   1000) -> ~1000+ bytes of buffer
  make(chan struct{}, 1000) -> 0 bytes of buffer   <-- optimal
```

### 5.4 Set Implementation Using `map[K]struct{}`

```go
package main

import "fmt"

// ----------------------------------------------------------------
// A Set[K] built on top of map[K]struct{}
// The value type struct{} costs 0 bytes -- we only care about keys
// ----------------------------------------------------------------

type Set[K comparable] struct {
    m map[K]struct{}
}

func NewSet[K comparable]() *Set[K] {
    return &Set[K]{m: make(map[K]struct{})}
}

func (s *Set[K]) Add(key K) {
    s.m[key] = struct{}{} // struct{}{} is the zero-value of struct{}
}

func (s *Set[K]) Contains(key K) bool {
    _, ok := s.m[key]
    return ok
}

func (s *Set[K]) Remove(key K) {
    delete(s.m, key)
}

func (s *Set[K]) Size() int {
    return len(s.m)
}

func main() {
    s := NewSet[string]()
    s.Add("apple")
    s.Add("banana")
    s.Add("apple") // duplicate -- no effect (idempotent)

    fmt.Println(s.Contains("apple"))  // true
    fmt.Println(s.Contains("cherry")) // false
    fmt.Println(s.Size())             // 2

    s.Remove("apple")
    fmt.Println(s.Contains("apple"))  // false
}
```

```
Memory comparison per entry:
  map[string]bool    -> key bytes + 1 byte value
  map[string]struct{} -> key bytes + 0 bytes value  <-- optimal
```

### 5.5 Marker Interfaces with ZST Structs

```go
package main

import "fmt"

// ----------------------------------------------------------------
// Marker types: types that "tag" other types via interface
// ----------------------------------------------------------------

// Unexported method creates a sealed marker interface
type Serializable interface {
    isSerializable()
}

// Marker type: a ZST that implements the sealed interface
type SerializableMarker struct{}

func (SerializableMarker) isSerializable() {}

// User embeds the ZST marker -- adds 0 bytes to User's size (usually)
type User struct {
    SerializableMarker
    Name string
    Age  int
}

// Only works with types that implement Serializable
func Serialize(s Serializable) string {
    return fmt.Sprintf("%+v", s)
}

func main() {
    u := User{Name: "Alice", Age: 30}
    fmt.Println(Serialize(u)) // Works -- User implements Serializable via embedding
}
```

### 5.6 Goroutine Coordination Patterns

```go
package main

import (
    "fmt"
    "sync"
)

func processAll(items []int) {
    var wg sync.WaitGroup
    results := make(chan struct{}, len(items)) // signal-only channel

    for _, item := range items {
        wg.Add(1)
        go func(v int) {
            defer wg.Done()
            fmt.Printf("Processed: %d\n", v)
            results <- struct{}{} // signal completion -- 0 bytes of data
        }(item)
    }

    wg.Wait()
    close(results)

    count := 0
    for range results {
        count++
    }
    fmt.Printf("Total processed: %d\n", count)
}

func main() {
    processAll([]int{1, 2, 3, 4, 5})
}
```

---

## 6. ZSTs in Rust

Rust has the **richest ZST ecosystem** of any mainstream language. The language is explicitly designed around them.

### 6.1 The Unit Type `()`

`()` (pronounced "unit") is Rust's fundamental ZST. It is the return type of functions that return "nothing."

```rust
fn greet(name: &str) {
    println!("Hello, {}", name);
    // implicitly returns ()
}

fn main() {
    let result: () = greet("Alice"); // result is the ZST value ()
    let unit: () = ();               // the one and only value of ()

    println!("size of () = {}", std::mem::size_of::<()>()); // 0
    println!("align of () = {}", std::mem::align_of::<()>()); // 1
}
```

`()` in Option and Result:

```rust
fn may_fail(x: i32) -> Result<(), String> {
    if x > 0 {
        Ok(())  // success: no value to return, just signal "ok"
    } else {
        Err("must be positive".to_string())
    }
}
```

### 6.2 Unit Structs

A unit struct is a struct with **no fields**. Size is always 0.

```rust
use std::mem;

struct Marker;
struct Logger;
struct Visitor;

fn main() {
    let _m = Marker;  // no braces or parens needed
    let _l = Logger;
    let _v = Visitor;

    println!("size of Marker  = {}", mem::size_of::<Marker>());  // 0
    println!("size of Logger  = {}", mem::size_of::<Logger>());   // 0
    println!("size of Visitor = {}", mem::size_of::<Visitor>()); // 0
}
```

### 6.3 Zero-Length Arrays

```rust
fn main() {
    let arr: [i32; 0] = [];

    println!("size of [i32; 0] = {}", std::mem::size_of::<[i32; 0]>()); // 0
    println!("size of [i32; 5] = {}", std::mem::size_of::<[i32; 5]>()); // 20

    // [i32; 0] is a ZST: no elements, no bytes, but still a valid type
}
```

### 6.4 Unit Enum Variants and the Single-Variant Enum

```rust
use std::mem;

enum Direction {
    North, // unit variant: no payload
    South,
    East,
    West,
}

// A single-variant enum with no payload is a ZST (only one possible value)
enum Singleton {
    Only,
}

fn main() {
    // Direction: 4 variants -> needs at least 2 bits -> rounds to 1 byte
    println!("size of Direction = {}", mem::size_of::<Direction>()); // 1

    // Singleton: 1 variant -> 0 bits of information -> 0 bytes
    println!("size of Singleton = {}", mem::size_of::<Singleton>()); // 0
}
```

### 6.5 Implementing Traits on ZSTs

ZSTs can implement rich trait interfaces with **zero runtime overhead**:

```rust
// ----------------------------------------------------------------
// ZST Logger: implements logging behavior, stores nothing
// ----------------------------------------------------------------

struct StdoutLogger;
struct NoopLogger;

trait Log {
    fn log(&self, message: &str);
}

impl Log for StdoutLogger {
    fn log(&self, message: &str) {
        println!("[LOG] {}", message);
    }
}

impl Log for NoopLogger {
    fn log(&self, _message: &str) {
        // Intentional no-op: when compiled with NoopLogger,
        // the optimizer removes this call entirely
    }
}

// At compile time, the compiler generates a distinct version of
// `process` for each concrete L type (monomorphization)
fn process<L: Log>(logger: &L, data: &[i32]) -> i32 {
    logger.log("Starting process");
    let sum: i32 = data.iter().sum();
    logger.log(&format!("Sum = {}", sum));
    sum
}

fn main() {
    let data = vec![1, 2, 3, 4, 5];

    let sum1 = process(&StdoutLogger, &data); // logs to stdout
    println!("Result: {}", sum1);

    let sum2 = process(&NoopLogger, &data);   // zero cost: no logging
    println!("Result: {}", sum2);
}
```

### 6.6 ZST as HashMap Value: The HashSet Pattern

Rust's `HashSet<T>` is literally implemented as `HashMap<T, ()>`:

```rust
use std::collections::HashMap;
use std::mem;

fn main() {
    // This IS how HashSet is implemented internally:
    let mut set: HashMap<String, ()> = HashMap::new();
    set.insert("apple".to_string(), ());
    set.insert("banana".to_string(), ());

    let has_apple = set.contains_key("apple");
    println!("Contains apple: {}", has_apple); // true

    // The value type () costs 0 bytes
    println!("size of () = {}", mem::size_of::<()>()); // 0

    // A (String, ()) tuple is the same size as just String
    println!("size of String       = {}", mem::size_of::<String>());       // 24
    println!("size of (String, ()) = {}", mem::size_of::<(String, ())>()); // 24 (same!)
}
```

---

## 7. PhantomData: The Ghost Type

`PhantomData<T>` is Rust's most sophisticated ZST. It is **always zero bytes** but carries critical information about **ownership, borrowing, and variance** to the compiler's analysis passes.

### 7.1 What Is PhantomData?

```rust
// From the standard library (simplified):
#[lang = "phantom_data"]
pub struct PhantomData<T: ?Sized>;
```

Key properties:
- `size_of::<PhantomData<T>>() == 0` always, for any T
- It is **never stored in memory** at runtime
- It exists solely to carry **type information** to compiler analyses (borrow checker, drop checker, variance checker)

### 7.2 The Lifetime Problem Without PhantomData

If you build a raw-pointer wrapper without PhantomData, the compiler does not know the struct "borrows" anything. This allows use-after-free bugs:

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// PROBLEM: Raw pointer with no lifetime annotation
// ----------------------------------------------------------------
struct DangerousRef<T> {
    ptr: *const T,
    // No PhantomData -> compiler has no idea this pointer
    // relates to a lifetime. Use-after-free is possible!
}

// ----------------------------------------------------------------
// SOLUTION: PhantomData tells the compiler "I borrow T for 'a"
// ----------------------------------------------------------------
struct SafeRef<'a, T> {
    ptr: *const T,
    _phantom: PhantomData<&'a T>, // covariant borrow of T for lifetime 'a
}

impl<'a, T> SafeRef<'a, T> {
    fn new(reference: &'a T) -> Self {
        SafeRef {
            ptr: reference as *const T,
            _phantom: PhantomData,
        }
    }

    fn get(&self) -> &'a T {
        // SAFETY: ptr came from a &'a T, still valid for 'a
        unsafe { &*self.ptr }
    }
}

fn main() {
    let value = 42i32;
    let safe = SafeRef::new(&value);
    println!("{}", safe.get()); // 42

    // This DOES NOT compile -- lifetime enforced by PhantomData:
    // let dangling = {
    //     let temp = 99i32;
    //     SafeRef::new(&temp) // ERROR: temp does not live long enough
    // };
    // println!("{}", dangling.get()); // use-after-free -- PREVENTED at compile time
}
```

### 7.3 Ownership vs. Borrowing: Drop Check

`PhantomData` also affects **drop check** -- whether Rust should run a destructor when your type is dropped:

```rust
use std::marker::PhantomData;

// Owns T (like Vec<T>):
// PhantomData<T> -> "I own T values, run T's destructor when I drop"
struct OwnedBuffer<T> {
    ptr: *mut T,
    len: usize,
    _owns: PhantomData<T>,
}

// Borrows T (like &'a T):
// PhantomData<&'a T> -> "I borrow T for lifetime 'a, no destructor"
struct BorrowedRef<'a, T> {
    ptr: *const T,
    _borrows: PhantomData<&'a T>,
}

// Raw handle (like *const T):
// PhantomData<*const T> -> no ownership claim, no lifetime
struct RawHandle<T> {
    ptr: *const T,
    _raw: PhantomData<*const T>,
}
```

### 7.4 Variance and PhantomData

**Variance** describes how subtyping flows through generic type parameters. This is crucial for lifetime correctness in unsafe code.

```
Term         | Meaning
-------------|--------------------------------------------------------------
Covariant    | If 'long: 'short, then Type<'long> can be used as Type<'short>
             | (longer lifetime subsumes shorter -- safe to "forget" lifetime)
Contravariant| Opposite of covariant
Invariant    | No substitution allowed -- must match exactly
```

```
PhantomData choice            | Variance effect
------------------------------|------------------------------------------
PhantomData<T>                | covariant over T (like owning T)
PhantomData<&'a T>            | covariant over 'a and T
PhantomData<&'a mut T>        | invariant over T, covariant over 'a
PhantomData<fn(T)>            | contravariant over T
PhantomData<*const T>         | covariant over T
PhantomData<*mut T>           | invariant over T
PhantomData<Cell<T>>          | invariant over T
```

```rust
use std::marker::PhantomData;

// Covariant wrapper (like &'a T):
// Safe to use where a shorter-lived borrow is expected
struct CovariantRef<'a, T> {
    _marker: PhantomData<&'a T>,
}

// Invariant wrapper (like Cell<T> or &mut T):
// Type must match exactly -- no variance allowed
struct InvariantWrapper<T> {
    _marker: PhantomData<*mut T>, // raw mut pointer -> invariant
}
```

### 7.5 PhantomData for Type-Level Unit Encoding

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// Encoding units of measurement at the type level
// The unit (Meters, Kilograms, etc.) is a ZST -- 0 bytes at runtime
// but the compiler enforces dimensional correctness
// ----------------------------------------------------------------

struct Meters;
struct Kilograms;
struct Seconds;

#[derive(Debug, Clone, Copy)]
struct Measurement<Unit> {
    value: f64,
    _unit: PhantomData<Unit>,
}

impl<Unit> Measurement<Unit> {
    fn new(value: f64) -> Self {
        Measurement { value, _unit: PhantomData }
    }

    fn value(&self) -> f64 {
        self.value
    }
}

// Only same-unit measurements can be added
impl<Unit> std::ops::Add for Measurement<Unit> {
    type Output = Self;
    fn add(self, rhs: Self) -> Self {
        Measurement::new(self.value + rhs.value)
    }
}

fn main() {
    let d1: Measurement<Meters>    = Measurement::new(5.0);
    let d2: Measurement<Meters>    = Measurement::new(3.0);
    let m:  Measurement<Kilograms> = Measurement::new(70.0);

    let total = d1 + d2; // OK: both Meters
    println!("Total distance: {} m", total.value());

    // This DOES NOT compile -- dimensional type mismatch:
    // let error = d2 + m; // ERROR: Meters != Kilograms
}
```

---

## 8. The Never Type `!`

The never type `!` is the **most extreme ZST**: it has **zero possible values** (unlike unit types, which have exactly one).

### 8.1 What Is `!`?

```
Type         | Number of possible values
-------------|---------------------------
bool         | 2   (true, false)
u8           | 256 (0..=255)
()           | 1   ( () )
Singleton    | 1   (Only)
!            | 0   (impossible to construct -- this is the point)
```

Because you can **never construct a value of type `!`**, any code that would need one is **unreachable**. The compiler uses this for exhaustiveness checking and dead code elimination.

### 8.2 `!` in Diverging Functions

```rust
// A function returning ! means it NEVER returns normally
// (it must loop forever, panic, abort, or exit)

fn diverge() -> ! {
    panic!("This function never returns normally");
}

fn infinite_loop() -> ! {
    loop {}
}

fn exit_program() -> ! {
    std::process::exit(0);
}

fn main() {
    // The type of `x` is inferred as i32 because:
    // - true branch returns 42 (i32)
    // - false branch returns ! (compatible with ANY type)
    // So the overall expression has type i32
    let x: i32 = if true {
        42
    } else {
        diverge() // ! is a subtype of i32 (and every other type)
    };
    println!("{}", x); // 42
}
```

### 8.3 `!` in Pattern Matching: The `Infallible` Type

```rust
// The standard library uses ! for operations that can never fail
// std::convert::Infallible is effectively an alias for "!"

use std::convert::Infallible;

fn always_succeeds(x: i32) -> Result<i32, Infallible> {
    Ok(x * 2) // Err variant is Infallible -- can never be constructed
}

fn main() {
    let result = always_succeeds(5);

    // Because Err(e) requires an Infallible value (impossible to construct),
    // the match is exhaustive with ZERO arms for the Err case:
    let value = match result {
        Ok(v)  => v,
        Err(e) => match e {}, // zero-arm match: exhaustive because Infallible has 0 values!
    };
    println!("{}", value); // 10
}
```

### 8.4 `!` as the Bottom Type

In type theory, `!` is the **bottom type (denoted Bottom)**. A bottom type is a subtype of **every** other type:

```
! <: i32
! <: String
! <: Vec<T>
! <: ()
! <: EVERY TYPE THAT EXISTS
```

This is why `!` can appear in any type context. It means "this branch cannot possibly produce a value, so its type is irrelevant."

```
ASCII: Type hierarchy
                  Everything
                  /    |    \
                i32  String  Vec<T> ...
                  \    |    /
                    ()   ...
                      \
                       !  (bottom -- subtype of everything)
```

```rust
fn main() {
    // loop returns !, so it is compatible with i32 in this context:
    let _x: i32 = loop {
        break 42; // break with a value converts ! back to i32
    };

    // continue and break both have type !
    let v: Vec<i32> = vec![1, 2, 3];
    let _doubled: Vec<i32> = v.iter().map(|&x| {
        if x == 2 { return 0; }
        x * 2  // this branch returns i32
        // the `return` above has type ! (diverges), compatible with i32
    }).collect();
}
```

---

## 9. ZSTs as Marker Types & Type-State Programming

**Type-state programming** is a design pattern where the **valid states** of an object are encoded **in its type**, so invalid state transitions are caught at **compile time**, not runtime.

### 9.1 The Core Idea

```
Runtime state machine (C-style):   Type-state machine (Rust-style):
+----------+  open()  +--------+   File<Closed> --open_ro()--> File<ReadOnly>
|  Closed  | -------> |  Open  |   File<Closed> --open_rw()--> File<ReadWrite>
+----------+          +--------+   File<ReadOnly>  --close()--> File<Closed>
     ^                    |
     +---- close() -------+        All invalid transitions are TYPE ERRORS.
                                   Zero runtime checks needed.

Problem (C): runtime checks,       Solution (Rust): compiler enforces
             errors at runtime               all invariants for free
```

### 9.2 Full Type-State Implementation in Rust

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// State types: pure ZSTs carrying state information
// ----------------------------------------------------------------

struct Closed;
struct ReadOnly;
struct ReadWrite;

// ----------------------------------------------------------------
// The resource: PhantomData<State> carries state at zero cost
// ----------------------------------------------------------------

struct File<State> {
    path: String,
    fd: Option<i32>,     // simulated file descriptor
    _state: PhantomData<State>,
}

// Constructor: only available when Closed
impl File<Closed> {
    fn new(path: &str) -> Self {
        File {
            path: path.to_string(),
            fd: None,
            _state: PhantomData,
        }
    }

    fn open_read_only(self) -> File<ReadOnly> {
        println!("Opening {} read-only", self.path);
        File { fd: Some(3), path: self.path, _state: PhantomData }
    }

    fn open_read_write(self) -> File<ReadWrite> {
        println!("Opening {} read-write", self.path);
        File { fd: Some(3), path: self.path, _state: PhantomData }
    }
}

// Trait to express "any open state"
trait IsOpen {}
impl IsOpen for ReadOnly  {}
impl IsOpen for ReadWrite {}

// Read and close: available when any open state
impl<State: IsOpen> File<State> {
    fn read(&self) -> String {
        format!("Contents of {}", self.path)
    }

    fn close(self) -> File<Closed> {
        println!("Closing {}", self.path);
        File { path: self.path, fd: None, _state: PhantomData }
    }
}

// Write: ONLY available when ReadWrite
impl File<ReadWrite> {
    fn write(&self, data: &str) {
        println!("Writing '{}' to {}", data, self.path);
    }
}

fn main() {
    let f = File::<Closed>::new("/etc/config");

    let f = f.open_read_only();
    println!("{}", f.read()); // OK

    // f.write("hack"); // COMPILE ERROR: File<ReadOnly> has no method `write`

    let f = f.close();
    let f = f.open_read_write();
    f.write("new data");
    println!("{}", f.read()); // OK
    let _f = f.close();

    // _f.read(); // COMPILE ERROR: f was moved into close()
}
```

### 9.3 Type-State Flowchart

```
+---------------------------------------------------------------+
|                    TYPE-STATE MACHINE                         |
|                                                               |
|    File<Closed>                                               |
|         |                                                     |
|         +-- open_read_only()  --> File<ReadOnly>              |
|         |                              |                      |
|         |                              +-- read()             |
|         |                              +-- close() --> File<Closed>
|         |                                                     |
|         +-- open_read_write() --> File<ReadWrite>             |
|                                        |                      |
|                                        +-- read()             |
|                                        +-- write()            |
|                                        +-- close() --> File<Closed>
|                                                               |
|    COMPILE-TIME INVARIANTS (zero runtime cost):               |
|      Cannot write to ReadOnly          -> type error          |
|      Cannot read from Closed           -> type error          |
|      Cannot close an already-closed    -> type error          |
+---------------------------------------------------------------+
```

### 9.4 Go Type-State (Limited Simulation)

Go's type system cannot enforce state transitions at compile time as strictly as Rust, but we can use distinct types to create a useful convention:

```go
package main

import "fmt"

type ClosedDB struct{ dsn string }
type OpenDB struct {
    dsn  string
    conn string
}

func NewDB(dsn string) ClosedDB {
    return ClosedDB{dsn: dsn}
}

func (db ClosedDB) Connect() OpenDB {
    fmt.Printf("Connecting to %s\n", db.dsn)
    return OpenDB{dsn: db.dsn, conn: "active_connection"}
}

func (db OpenDB) Query(q string) string {
    return fmt.Sprintf("Result of [%s]", q)
}

func (db OpenDB) Close() ClosedDB {
    fmt.Printf("Closing connection to %s\n", db.dsn)
    return ClosedDB{dsn: db.dsn}
}

func main() {
    db := NewDB("postgres://localhost/mydb")
    open := db.Connect()
    fmt.Println(open.Query("SELECT 1"))
    _ = open.Close()

    // db.Query("SELECT 1") -> compile error: ClosedDB has no method Query
    // This is weaker than Rust (no phantom state), but better than nothing
}
```

---

## 10. ZSTs in Collections

### 10.1 `Vec<ZST>`: Zero-Allocation Vector

A `Vec<T>` where T is a ZST is **special-cased by the Rust runtime**:
- Allocates **zero bytes** of heap memory
- `push` is O(1) with no allocation ever
- `pop` is O(1) with no deallocation
- `len()` still works correctly (it is just a counter)

```rust
fn main() {
    let mut v: Vec<()> = Vec::new();

    // Push 1 million times: ZERO heap allocations
    for _ in 0..1_000_000 {
        v.push(());
    }

    println!("len = {}", v.len()); // 1_000_000
    println!("Zero bytes allocated on heap");
}
```

How does `Vec<ZST>` work without allocation?

```
Normal Vec<i32>:           Vec<()>:
  ptr  -> [heap memory]     ptr  -> 0x1 (dangling, never dereferenced)
  len  = 5                  len  = N   (just an integer counter)
  cap  = 8                  cap  = usize::MAX (effectively infinite)

Vec<ZST> push: just increment len
Vec<ZST> pop:  just decrement len, return Some(())
Vec<ZST> index: return () without any memory read
```

### 10.2 Rust's HashSet Source Code (Simplified)

```rust
// From the Rust standard library (simplified for illustration):

pub struct HashSet<T, S = RandomState> {
    map: HashMap<T, ()>,  // <-- the value type is () -- 0 bytes per entry
}

impl<T: Eq + std::hash::Hash> HashSet<T> {
    pub fn insert(&mut self, value: T) -> bool {
        self.map.insert(value, ()).is_none()
        //                    ^-- ZST value stored: 0 bytes
    }

    pub fn contains(&self, value: &T) -> bool {
        self.map.contains_key(value)
    }
}
```

### 10.3 Go Map with `struct{}` Values

```go
package main

import (
    "fmt"
    "unsafe"
)

func main() {
    // Go's runtime optimizes map[K]struct{} specially:
    // The value slot in each bucket is 0 bytes wide.
    m := make(map[string]struct{})

    words := []string{"hello", "world", "hello", "foo", "world"}
    for _, w := range words {
        m[w] = struct{}{}
    }

    fmt.Printf("Unique words: %d\n", len(m)) // 3

    // Memory comparison:
    fmt.Printf("sizeof(struct{}) = %d\n", unsafe.Sizeof(struct{}{})) // 0
    fmt.Printf("sizeof(bool)     = %d\n", unsafe.Sizeof(true))       // 1
    // For 1 million entries: bool wastes ~1MB; struct{} wastes 0 bytes
}
```

---

## 11. ZSTs and Pointer Arithmetic

This section covers the low-level interactions between ZSTs and memory management.

### 11.1 The Dangling Pointer Rule

For ZSTs, pointers do not need to point to actual memory because no bytes will ever be read or written. Rust handles this with `NonNull::dangling()`:

```rust
use std::ptr::NonNull;

fn main() {
    let zst_ref: &() = &();
    let ptr = zst_ref as *const ();
    println!("ZST pointer: {:p}", ptr); // some valid-looking address

    // NonNull::dangling() creates a properly aligned, non-null ZST pointer
    // that is safe to hold (but never to dereference for real data)
    let dangling: NonNull<()> = NonNull::dangling();
    println!("Dangling ZST ptr: {:p}", dangling.as_ptr());

    unsafe {
        let _val: () = *dangling.as_ptr(); // safe: reads 0 bytes
    }
}
```

### 11.2 Pointer Arithmetic on ZSTs

**Critical rule:** Offsetting a pointer to a ZST does not change its address. All "elements" of a ZST array are at the same address.

```rust
fn main() {
    let arr: [(); 5] = [(); 5]; // array of 5 ZSTs

    let ptr = arr.as_ptr();
    unsafe {
        let p0 = ptr.add(0);
        let p1 = ptr.add(1);
        let p4 = ptr.add(4);

        // All point to the same address -- ZST has size 0, so no offset
        println!("p0 = {:p}", p0); // e.g. 0x...
        println!("p1 = {:p}", p1); // SAME as p0
        println!("p4 = {:p}", p4); // SAME as p0
    }
}
```

### 11.3 Allocator and ZSTs

A correct allocator must handle ZST allocation specially:

```rust
use std::alloc::{GlobalAlloc, System, Layout};

fn main() {
    let layout = Layout::new::<()>();
    println!("ZST layout: size={}, align={}", layout.size(), layout.align()); // 0, 1

    // The global allocator handles size=0 specially:
    // alloc(size=0) returns a non-null dangling pointer
    // dealloc of that pointer is a no-op
    unsafe {
        let ptr = System.alloc(layout);
        println!("ZST alloc ptr: {:p}", ptr);
        System.dealloc(ptr, layout); // no-op -- safe
    }
}
```

### 11.4 C: Pointer Arithmetic with Flexible Array Members

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

struct Header {
    uint32_t count;
    uint8_t  data[0]; // zero-length array: occupies 0 bytes in the struct
};

int main(void) {
    struct Header* h = malloc(sizeof(struct Header) + 8);
    h->count = 8;

    // &h->data[0] is right after the count field
    printf("struct addr: %p\n", (void*)h);
    printf("data   addr: %p\n", (void*)h->data);
    printf("offset:      %zu\n", (size_t)((char*)h->data - (char*)h)); // 4

    for (uint32_t i = 0; i < h->count; i++) {
        h->data[i] = (uint8_t)(i * 10);
    }
    printf("data[3] = %u\n", h->data[3]); // 30

    free(h);
    return 0;
}
```

---

## 12. ZSTs and Trait Objects

A **trait object** (`dyn Trait`) is a **fat pointer**: two machine words, one for the data and one for the vtable. When the underlying type is a ZST, the data pointer is a dangling ZST pointer -- it is never dereferenced.

### 12.1 Fat Pointers and ZSTs

```rust
use std::mem;

trait Animal {
    fn sound(&self) -> &str;
}

struct Cat; // ZST
struct Dog; // ZST

impl Animal for Cat {
    fn sound(&self) -> &str { "meow" }
}

impl Animal for Dog {
    fn sound(&self) -> &str { "woof" }
}

fn make_sound(animal: &dyn Animal) {
    println!("{}", animal.sound());
}

fn main() {
    let cat = Cat; // 0 bytes
    let dog = Dog; // 0 bytes

    make_sound(&cat);
    make_sound(&dog);

    println!("Cat size:          {}", mem::size_of::<Cat>());          // 0
    println!("Dog size:          {}", mem::size_of::<Dog>());          // 0
    println!("&dyn Animal size:  {}", mem::size_of::<&dyn Animal>());  // 16 (2 pointers)
}
```

### 12.2 ZST Vtable Layout

```
&dyn Animal pointing to Cat (ZST):
+------------------------------------------------------+
|  fat pointer                                         |
|  +-------------------+-----------------------------+ |
|  | data_ptr: 0x1     | vtable_ptr -> [sound: fn]   | |
|  +-------------------+-----------------------------+ |
|       ^                                              |
|       Dangling pointer -- never dereferenced         |
|       (Cat is ZST, reading it accesses 0 bytes)      |
+------------------------------------------------------+
```

All behavior comes from the vtable. The data pointer is irrelevant for ZSTs. This is dynamic dispatch with a statically-resolved (but runtime-dispatched) zero-cost underlying type.

---

## 13. ZSTs and Generics / Monomorphization

### 13.1 What Is Monomorphization?

When Rust compiles a generic function `fn foo<T>(x: T)`, it generates **one concrete copy of the function per distinct T used at call sites**. This is monomorphization.

```
fn identity<T>(x: T) -> T { x }

// Used as identity::<i32> and identity::<()>:
// Compiler generates two functions:
//   fn identity_i32(x: i32) -> i32 { x }   <- 4 bytes involved
//   fn identity_unit(x: ()) -> ()  { x }   <- 0 bytes, often optimized away entirely
```

### 13.2 Zero-Cost Strategy Pattern

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// Strategy pattern: strategy type parameter is a ZST
// Zero runtime overhead -- strategy is a compile-time choice
// ----------------------------------------------------------------

trait SortStrategy {
    fn sort(data: &mut Vec<i32>);
}

struct BubbleSort;
struct QuickSort;

impl SortStrategy for BubbleSort {
    fn sort(data: &mut Vec<i32>) {
        let n = data.len();
        for i in 0..n {
            for j in 0..n.saturating_sub(i + 1) {
                if data[j] > data[j + 1] {
                    data.swap(j, j + 1);
                }
            }
        }
    }
}

impl SortStrategy for QuickSort {
    fn sort(data: &mut Vec<i32>) {
        data.sort_unstable(); // stdlib for demonstration
    }
}

// Sorter<S> is a ZST when S is a ZST
struct Sorter<S: SortStrategy> {
    _strategy: PhantomData<S>,
}

impl<S: SortStrategy> Sorter<S> {
    fn new() -> Self {
        Sorter { _strategy: PhantomData }
    }

    fn sort(&self, data: &mut Vec<i32>) {
        S::sort(data); // static dispatch: no vtable, no indirection
    }
}

fn main() {
    let mut data = vec![5, 3, 8, 1, 9, 2];

    let sorter = Sorter::<BubbleSort>::new();
    sorter.sort(&mut data);
    println!("{:?}", data);

    let mut data2 = vec![5, 3, 8, 1, 9, 2];
    let sorter2 = Sorter::<QuickSort>::new();
    sorter2.sort(&mut data2);
    println!("{:?}", data2);

    // Both sorters are ZSTs -- zero bytes, zero overhead
    println!("Sorter<BubbleSort> size: {}", std::mem::size_of::<Sorter<BubbleSort>>()); // 0
    println!("Sorter<QuickSort> size:  {}", std::mem::size_of::<Sorter<QuickSort>>());  // 0
}
```

### 13.3 Monomorphization Flow

```
Source code:
  Sorter::<BubbleSort>::sort(&mut data)
  Sorter::<QuickSort>::sort(&mut data2)

After monomorphization:
  sorter_bubble_sort_sort(&mut data)   <- direct function call
  sorter_quick_sort_sort(&mut data2)   <- direct function call

Both: 0 bytes for strategy object, identical to hand-written specialized code.
The ZST phantom type is FULLY ERASED from the binary.
```

---

## 14. ZSTs as Compile-Time Capabilities & Tokens

A ZST can serve as a **capability token**: a value that represents "permission to do X." Because it has a private field, only the authority that creates it can mint new tokens. Possession of the token proves capability.

### 14.1 The Capability Pattern

```rust
// ----------------------------------------------------------------
// Only code that holds a DatabaseCapability token may call
// database functions. The token is a ZST -- zero bytes.
// Tokens cannot be forged because their constructor is private.
// ----------------------------------------------------------------

mod auth {
    pub struct DatabaseCapability { _private: () }
    pub struct AdminCapability    { _private: () }

    pub fn authenticate(password: &str) -> Option<DatabaseCapability> {
        if password == "secret" {
            Some(DatabaseCapability { _private: () })
        } else {
            None
        }
    }

    pub fn admin_authenticate(password: &str) -> Option<AdminCapability> {
        if password == "admin_secret" {
            Some(AdminCapability { _private: () })
        } else {
            None
        }
    }
}

mod database {
    use super::auth::{DatabaseCapability, AdminCapability};

    // Requires proof of DatabaseCapability
    pub fn query(_cap: &DatabaseCapability, sql: &str) -> String {
        format!("Result of: {}", sql)
    }

    // Requires proof of AdminCapability
    pub fn drop_table(_cap: &AdminCapability, table: &str) {
        println!("Dropping table: {}", table);
    }
}

fn main() {
    // Without auth, we cannot even construct a DatabaseCapability:
    // database::query(???, "SELECT 1"); // impossible -- no way to create the token

    let cap = auth::authenticate("secret").expect("Auth failed");
    println!("{}", database::query(&cap, "SELECT * FROM users"));

    let admin = auth::admin_authenticate("admin_secret").expect("Admin auth failed");
    database::drop_table(&admin, "temp_logs");
}
```

### 14.2 Initialization Order Tokens

```rust
// ----------------------------------------------------------------
// Enforce initialization phases at compile time.
// Phase B cannot run unless Phase A returned its completion token.
// ----------------------------------------------------------------

struct PhaseADone;  // ZST token: proof Phase A completed
struct PhaseBDone;  // ZST token: proof Phase B completed

fn phase_a() -> PhaseADone {
    println!("Phase A: hardware init...");
    PhaseADone
}

// phase_b REQUIRES the PhaseADone token (consumed by move)
fn phase_b(_proof: PhaseADone) -> PhaseBDone {
    println!("Phase B: driver loading...");
    PhaseBDone
}

// phase_c REQUIRES the PhaseBDone token
fn phase_c(_proof: PhaseBDone) {
    println!("Phase C: application start");
}

fn main() {
    let a = phase_a();
    let b = phase_b(a); // a is consumed -- cannot call phase_b again with the same token
    phase_c(b);

    // This DOES NOT compile:
    // phase_b(PhaseADone); // ERROR: cannot construct PhaseADone outside phase_a
}
```

---

## 15. ZSTs in Concurrency: Channel Signaling

### 15.1 Rust: Channels with `()`

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel::<()>(); // signal channel: no payload

    let worker = thread::spawn(move || {
        println!("Worker: starting...");
        thread::sleep(Duration::from_millis(100));
        println!("Worker: done!");
        tx.send(()).unwrap(); // send a () signal: 0 bytes transferred
    });

    rx.recv().unwrap(); // block until signal arrives
    println!("Main: received completion signal");
    worker.join().unwrap();
}
```

### 15.2 Rust: Parallel Processing with ZST Signals

```rust
use std::sync::mpsc;
use std::thread;

fn parallel_squares(tasks: Vec<i32>) -> Vec<i32> {
    let (result_tx, result_rx) = mpsc::channel::<i32>();
    let (done_tx, done_rx)     = mpsc::channel::<()>(); // ZST signal channel

    let n = tasks.len();

    for task in tasks {
        let tx  = result_tx.clone();
        let dtx = done_tx.clone();
        thread::spawn(move || {
            tx.send(task * task).unwrap();
            dtx.send(()).unwrap(); // 0 bytes: just a completion signal
        });
    }

    drop(result_tx);
    drop(done_tx);

    let mut results: Vec<i32> = result_rx.iter().collect();

    let done_count = done_rx.iter().count();
    println!("Received {} completion signals", done_count);

    results
}

fn main() {
    let mut results = parallel_squares(vec![1, 2, 3, 4, 5]);
    results.sort();
    println!("{:?}", results); // [1, 4, 9, 16, 25]
}
```

### 15.3 Go: Fan-Out with `struct{}`

```go
package main

import (
    "fmt"
    "sync"
)

func fanOut(tasks []int, numWorkers int) []int {
    jobCh    := make(chan int, len(tasks))
    resultCh := make(chan int, len(tasks))
    stopCh   := make(chan struct{})   // ZST emergency stop signal

    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobCh:
                    if !ok { return }
                    resultCh <- job * job
                case <-stopCh:
                    fmt.Printf("Worker %d: emergency stop\n", id)
                    return
                }
            }
        }(i)
    }

    for _, t := range tasks {
        jobCh <- t
    }
    close(jobCh)

    go func() {
        wg.Wait()
        close(resultCh)
        _ = stopCh
    }()

    var results []int
    for r := range resultCh {
        results = append(results, r)
    }
    return results
}

func main() {
    results := fanOut([]int{1, 2, 3, 4, 5, 6, 7, 8}, 3)
    fmt.Println(results)
}
```

---

## 16. Advanced Patterns

### 16.1 ZST Newtype for Type Safety

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// Phantom currency types: enforce dimensional correctness
// ----------------------------------------------------------------

struct USD;
struct EUR;

#[derive(Debug, Clone, Copy)]
struct Money<C> {
    cents: i64,
    _currency: PhantomData<C>,
}

impl<C> Money<C> {
    fn new(cents: i64) -> Self {
        Money { cents, _currency: PhantomData }
    }
    fn amount(&self) -> f64 { self.cents as f64 / 100.0 }
}

impl<C> std::ops::Add for Money<C> {
    type Output = Self;
    fn add(self, rhs: Self) -> Self { Money::new(self.cents + rhs.cents) }
}

fn main() {
    let price:    Money<USD> = Money::new(1099);
    let tax:      Money<USD> = Money::new(88);
    let total_usd = price + tax;
    println!("Total: ${:.2}", total_usd.amount());

    let eur: Money<EUR> = Money::new(999);

    // This DOES NOT compile -- type system prevents mixing currencies:
    // let error = price + eur; // ERROR: USD != EUR
}
```

### 16.2 The ZST Builder Pattern

```rust
use std::marker::PhantomData;

// ----------------------------------------------------------------
// Builder where ZST phantom types track which required fields
// have been set. build() only available when ALL required fields set.
// ----------------------------------------------------------------

struct Unset;
struct Set;

struct RequestBuilder<HasUrl, HasMethod> {
    url:     Option<String>,
    method:  Option<String>,
    body:    Option<String>,
    _url:    PhantomData<HasUrl>,
    _method: PhantomData<HasMethod>,
}

impl RequestBuilder<Unset, Unset> {
    fn new() -> Self {
        RequestBuilder {
            url: None, method: None, body: None,
            _url: PhantomData, _method: PhantomData,
        }
    }
}

impl<M> RequestBuilder<Unset, M> {
    fn url(self, url: &str) -> RequestBuilder<Set, M> {
        RequestBuilder {
            url: Some(url.to_string()),
            method: self.method,
            body: self.body,
            _url: PhantomData,
            _method: PhantomData,
        }
    }
}

impl<U> RequestBuilder<U, Unset> {
    fn method(self, method: &str) -> RequestBuilder<U, Set> {
        RequestBuilder {
            url: self.url,
            method: Some(method.to_string()),
            body: self.body,
            _url: PhantomData,
            _method: PhantomData,
        }
    }
}

impl<U, M> RequestBuilder<U, M> {
    fn body(mut self, body: &str) -> Self {
        self.body = Some(body.to_string());
        self
    }
}

// build() ONLY available when BOTH url AND method are Set
impl RequestBuilder<Set, Set> {
    fn build(self) -> String {
        format!("{} {} body={:?}", self.method.unwrap(), self.url.unwrap(), self.body)
    }
}

fn main() {
    let req = RequestBuilder::new()
        .url("https://api.example.com/users")
        .method("POST")
        .body(r#"{"name":"Alice"}"#)
        .build();
    println!("{}", req);

    // This DOES NOT compile -- method not set:
    // RequestBuilder::new()
    //     .url("https://api.example.com")
    //     .build(); // ERROR: no method `build` on RequestBuilder<Set, Unset>
}
```

### 16.3 ZST Function Items vs. Function Pointers vs. Closures

```rust
fn add_one(x: i32) -> i32 { x + 1 }

fn main() {
    // A function ITEM (not a pointer) is a ZST unique to that function
    let f = add_one;
    println!("size of fn item:              {}", std::mem::size_of_val(&f)); // 0

    // A function POINTER (fn(i32)->i32) is NOT a ZST -- it is a pointer (8 bytes)
    let fp: fn(i32) -> i32 = add_one;
    println!("size of fn pointer:           {}", std::mem::size_of_val(&fp)); // 8

    // A non-capturing closure is a ZST (captures nothing -- no data)
    let nc_closure = |x: i32| x + 1;
    println!("size of non-capturing closure:{}", std::mem::size_of_val(&nc_closure)); // 0

    // A capturing closure is NOT a ZST -- it holds the captured variables
    let offset = 5i32;
    let c_closure = move |x: i32| x + offset; // captures `offset` (4 bytes)
    println!("size of capturing closure:    {}", std::mem::size_of_val(&c_closure)); // 4
}
```

```
Summary:
  fn item (function itself)     ->  0 bytes  (ZST -- compile-time resolved)
  fn(T)->U pointer              ->  8 bytes  (pointer on 64-bit)
  non-capturing closure         ->  0 bytes  (ZST -- no captured data)
  capturing closure             ->  sizeof(all captured vars combined)
  &dyn Fn / trait object ref    -> 16 bytes  (fat pointer: data + vtable)
```

---

## 17. Pitfalls and Gotchas

### 17.1 C: Non-Standard Empty Struct

```c
// PITFALL: Empty structs in C have implementation-defined behavior
struct Bad {};  // GCC: 0, MSVC: varies, standard C: technically UB

// PORTABLE workaround: use a dummy member
struct Portable {
    char _reserved[1]; // always exactly 1 byte, standard-compliant
};

// Or use a preprocessor macro to abstract the portability:
#if defined(__GNUC__) || defined(__clang__)
  #define EMPTY_STRUCT_SIZE 0
  typedef struct {} ZST;
#else
  #define EMPTY_STRUCT_SIZE 1
  typedef struct { char _[1]; } ZST;
#endif
```

### 17.2 Go: ZST Pointer Equality Is Undefined

```go
var a, b struct{}
pa := &a
pb := &b

// NEVER rely on pointer equality for ZSTs -- spec says undefined
fmt.Println(pa == pb) // may be true OR false -- both are valid

// SAFE: compare values
fmt.Println(a == b) // always true
```

### 17.3 Rust: ZST and `unsafe` Allocator Code

```rust
// PITFALL: alloc(size=0) returns a dangling pointer
// You must detect ZSTs and handle them specially

fn safe_alloc<T>() -> *mut T {
    let layout = std::alloc::Layout::new::<T>();

    // Handle ZST: never call alloc with size 0
    if layout.size() == 0 {
        // Return a properly aligned, non-null dangling pointer
        return std::ptr::NonNull::dangling().as_ptr();
    }

    unsafe {
        let ptr = std::alloc::alloc(layout) as *mut T;
        if ptr.is_null() {
            std::alloc::handle_alloc_error(layout);
        }
        ptr
    }
}
```

### 17.4 Rust: PhantomData and `Send`/`Sync`

```rust
use std::marker::PhantomData;

// PITFALL: PhantomData<*mut T> makes your type !Send and !Sync
// Raw pointers are not Send/Sync, and PhantomData inherits that.
struct NotThreadSafe<T> {
    _marker: PhantomData<*mut T>, // makes this type !Send + !Sync automatically
}

// To opt in to Send + Sync for a type with raw pointers:
// YOU are responsible for ensuring the safety invariants hold!
struct MyVec<T> {
    ptr: *mut T,
    len: usize,
    cap: usize,
}

// Manual unsafe impl: assert to the compiler that MyVec is safe to send
unsafe impl<T: Send> Send for MyVec<T> {}
unsafe impl<T: Sync> Sync for MyVec<T> {}
```

### 17.5 Rust: `#[repr(C)]` and ZSTs

```rust
// PITFALL: #[repr(C)] follows C rules for struct layout
// A #[repr(C)] empty struct may NOT be a ZST (platform-dependent)

#[repr(C)]
struct ReprCEmpty {}
// Size may be 0 (GCC behavior) or 1 (MSVC behavior)
// Do NOT assume it is 0

// SAFE: default repr (Rust's own rules)
struct RustEmpty; // guaranteed: size_of::<RustEmpty>() == 0

fn main() {
    println!("{}", std::mem::size_of::<RustEmpty>()); // always 0
}
```

---

## 18. Mental Models & Summary

### 18.1 The Three Roles of ZSTs

```
+-------------------+--------------------------------------------------+
|  ROLE             |  DESCRIPTION                                     |
+-------------------+--------------------------------------------------+
| TYPE MARKERS      | Carry compile-time information (no runtime data) |
|                   | Examples: PhantomData<T>, Locked, Unlocked       |
|                   | Cost: 0 bytes, 0 runtime overhead                |
+-------------------+--------------------------------------------------+
| CAPABILITY TOKENS | Prove permission / state at compile time          |
|                   | Examples: DatabaseCapability, PhaseADone         |
|                   | Cost: 0 bytes, compiler-enforced security        |
+-------------------+--------------------------------------------------+
| SIGNALS           | Pure events with no payload                      |
|                   | Examples: chan struct{}, mpsc::send(())           |
|                   | Cost: 0 bytes per signal in channel buffer       |
+-------------------+--------------------------------------------------+
```

### 18.2 Language Comparison Table

```
+-------------------+------------------+--------------------+----------------------+
| Feature           | C                | Go                 | Rust                 |
+-------------------+------------------+--------------------+----------------------+
| Basic ZST         | struct {} (GCC)  | struct{}           | struct Foo; / ()     |
| ZST size          | 0 (GCC ext.)     | 0 (spec)           | 0 (spec, guaranteed) |
| Phantom types     | No               | Limited (embed)    | PhantomData<T>       |
| Type-state        | No               | Partial            | Full (compile-time)  |
| Never type        | void (weak)      | No direct equiv    | ! (bottom type)      |
| Channel signals   | N/A              | chan struct{}       | mpsc::channel::<()>  |
| Variance control  | No               | No                 | Via PhantomData      |
| Set via ZST map   | No               | map[K]struct{}     | HashMap<K, ()>       |
+-------------------+------------------+--------------------+----------------------+
```

### 18.3 Master Decision Tree: When to Use a ZST

```
I need to represent information. Where does it live?

        RUNTIME (data in memory) ---------> Use a normal type with fields
                |
        COMPILE TIME ONLY ----------------> ZST candidate
                |
                +-- Ownership/lifetime annotation ----> PhantomData<T>
                |
                +-- State machine states -------------> Unit struct + PhantomData
                |
                +-- Permission / capability ----------> Unit struct (private field)
                |
                +-- Event signaling (channels) -------> () or struct{}
                |
                +-- Compile-time strategy -----------> Unit struct + trait
                |
                +-- Set semantics (map, no value) ----> map[K]struct{} / HashMap<K,()>
                |
                +-- Computation that never returns ---> ! (Rust Never type)
```

### 18.4 Performance Summary

```
Operation                              With ZST    Without ZST (bool/u8)
--------------------------------------+----------+----------------------
Store marker in struct                 0 bytes    1+ bytes
Channel message buffer (per message)   0 bytes    1+ bytes
HashMap value slot (per entry)         0 bytes    1+ bytes
Vec push/pop                           O(1), 0B   O(1), may alloc
Pattern match on ZST state             no branch  conditional branch
Function item / non-capturing closure  0 bytes    8 bytes (fn pointer)
Type-state transition enforcement      compiler   runtime check
```

### 18.5 Cognitive Mental Model

Think of ZSTs as **compile-time sticky notes**. The note is attached to your data and the compiler reads it, but the CPU never sees it.

```
During compilation:                        After compilation (runtime):
+-------------------------------+          +---------------------------+
|  File<Locked>                 |          |  File { fd: 3 }           |
|       ^                       |  ------> |       ^                   |
|  "Locked" = ZST label         |          |  "Locked" is GONE         |
|  compiler uses it to check    |          |  only actual data remains |
|  that you don't call write()  |          +---------------------------+
+-------------------------------+

The type system enforces your invariants at compile time.
You pay ZERO runtime cost for compile-time safety.
```

### 18.6 Deliberate Practice Path

```
Level 1 (Recognition):
  - Identify ZSTs in codebases you read
  - Understand why () is the default function return type

Level 2 (Basic Application):
  - Replace chan bool with chan struct{} in your Go code
  - Use map[K]struct{} for sets in Go
  - Use HashMap<K, ()> for sets in Rust

Level 3 (Type-State Programming):
  - Implement a file or connection state machine with ZST phantom states
  - Build a builder that tracks required fields with ZST markers

Level 4 (Advanced):
  - Write unsafe Rust with correct PhantomData lifetime/ownership annotations
  - Implement a zero-cost strategy pattern with ZST type parameters
  - Build a capability-token API where tokens are private-field ZSTs

Level 5 (Expert):
  - Understand variance (covariant, contravariant, invariant) and control it
    through PhantomData choices
  - Implement a custom allocator-aware collection that handles ZST values
  - Use ! (never type) in your own library APIs for infallible operations
```

---

## Quick Reference Cheatsheet

```
RUST
---------------------------------------------------------------------
Type                    Size   Use case
---------------------------------------------------------------------
()                       0     Return "nothing", channel signals
struct Foo;              0     Marker, capability token, strategy
[T; 0]                   0     Empty array, generic base case
PhantomData<T>           0     Ownership / lifetime annotation
PhantomData<&'a T>       0     Borrow annotation (covariant over 'a)
PhantomData<&'a mut T>   0     Mutable borrow (invariant over T)
PhantomData<*mut T>      0     Raw pointer (invariant, !Send, !Sync)
!                        0     Diverging / infallible (bottom type)
fn foo (fn item)         0     Zero-cost function reference
|x| x+1  (no capture)   0     Zero-cost closure

GO
---------------------------------------------------------------------
Type                    Size   Use case
---------------------------------------------------------------------
struct{}                 0     Set values, channel signals
chan struct{}             0     Done / stop signals
map[K]struct{}           0     Set data structure

C  (non-standard / GCC extension)
---------------------------------------------------------------------
struct Empty {};         0*    GCC: 0, MSVC: varies, standard: UB
T arr[0];                0*    Flexible array member (GCC/Clang)
void (return type)       N/A   "No value" function return

* Non-standard: always verify with your compiler and target platform
```

---

*End of Zero-Sized Types Deep Mastery Guide*

---

> **Cognitive principle — chunking and pattern recognition:**
> You have now organized ZSTs into five mental categories: markers, tokens, signals, strategies, and states. Each time you encounter a ZST in production code, consciously classify it into one of these five buckets. That act of classification is *deliberate practice* — the kind of active cognitive engagement that builds expert-level pattern recognition far faster than passive reading. A world-class programmer sees `struct{}` in Go and thinks "set or signal" in under a second. That instant classification is not talent; it is the accumulated result of thousands of conscious categorizations. Start counting yours.

Now let me create the comprehensive markdown document:Here is your complete deep-dive document. Here is what is covered across all 18 sections:

**Foundations first** — the document starts from `sizeof`, alignment, and what a "type" even means before introducing ZSTs, so no prerequisite is assumed.

**All major ZST forms** are covered:

| Form | Language | Covered |
|---|---|---|
| `struct {}` / `struct{}` | C / Go | Yes |
| `()` unit type | Rust | Yes |
| Unit struct `struct Foo;` | Rust | Yes |
| `[T; 0]` zero array | Rust | Yes |
| `PhantomData<T>` | Rust | Full section |
| `!` never type | Rust | Full section |
| Flexible array `T arr[0]` | C | Yes |

**Key patterns with full code** — type-state programming, capability tokens, phantom units, zero-cost strategy, builder with ZST field-tracking, `HashSet` internals, `chan struct{}`, and monomorphization.

**The expert gotchas** — variance, `#[repr(C)]` vs default repr, `PhantomData<*mut T>` making types `!Send`, allocator handling of size-0, and pointer arithmetic on ZSTs.

**Every ASCII diagram is embedded** — no external files needed.