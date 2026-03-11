# Go's Type System — A Complete Architect's Guide

> *"A language that doesn't affect the way you think about programming is not worth knowing."*
> — Alan Perlis

Go's type system is deceptively profound. It looks minimal. It is not. It is **opinionated minimalism** — every decision deliberately cuts away complexity while preserving expressive power. This guide builds your mental model from atoms to architecture.

---

## Table of Contents

1. [The Philosophical Foundation](#1-the-philosophical-foundation)
2. [Basic Types — The Atoms](#2-basic-types--the-atoms)
3. [Zero Values — The Honest Default](#3-zero-values--the-honest-default)
4. [Named Types vs Unnamed Types](#4-named-types-vs-unnamed-types)
5. [Type Aliases vs Type Definitions](#5-type-aliases-vs-type-definitions)
6. [Composite Types — Structure](#6-composite-types--structure)
7. [Pointer Types — Indirection](#7-pointer-types--indirection)
8. [Function Types — First-Class Behavior](#8-function-types--first-class-behavior)
9. [Interface Types — Contracts](#9-interface-types--contracts)
10. [Method Sets — The Hidden Rule](#10-method-sets--the-hidden-rule)
11. [Type Embedding — Composition](#11-type-embedding--composition)
12. [Type Conversion vs Type Assertion](#12-type-conversion-vs-type-assertion)
13. [The Empty Interface and `any`](#13-the-empty-interface-and-any)
14. [Type Switches — Runtime Dispatch](#14-type-switches--runtime-dispatch)
15. [Interface Internals — The Two-Word Header](#15-interface-internals--the-two-word-header)
16. [Generics — Parametric Polymorphism](#16-generics--parametric-polymorphism)
17. [Channels as Types](#17-channels-as-types)
18. [The Complete Mental Model](#18-the-complete-mental-model)
19. [Expert Patterns and Anti-Patterns](#19-expert-patterns-and-anti-patterns)

---

## 1. The Philosophical Foundation

Before touching syntax, understand Go's **core conviction**:

> Complexity is not free. Every feature must justify its cost.

This shapes the entire type system. Where C++ gives you inheritance, multiple dispatch, and templates, Go gives you **three tools**: interfaces, embedding, and (since 1.18) generics. That's it. And yet, Go powers some of the world's most complex distributed systems.

The reason is **composition over inheritance**. Go's type system enforces this at the language level.

### The Three Axes of Go's Type System

```
┌──────────────────────────────────────────────────────────────┐
│                    Go's Type System                          │
│                                                              │
│  AXIS 1: STRUCTURE                                           │
│  What does this type look like in memory?                    │
│  → basic, struct, slice, map, array, channel                 │
│                                                              │
│  AXIS 2: BEHAVIOR                                            │
│  What can this type do?                                      │
│  → methods defined on it                                     │
│                                                              │
│  AXIS 3: CAPABILITY                                          │
│  What contracts does this type satisfy?                      │
│  → interfaces it implicitly implements                       │
└──────────────────────────────────────────────────────────────┘
```

Every type in Go has structure. Any named type can have behavior. Behavior determines capability. This is the complete picture.

---

## 2. Basic Types — The Atoms

Go's basic types map almost directly to machine types. There is no ambiguity.

### Integer Types

```go
// Signed integers — two's complement
int8    // -128 to 127                    (1 byte)
int16   // -32,768 to 32,767             (2 bytes)
int32   // -2,147,483,648 to 2,147,483,647 (4 bytes)
int64   // -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 (8 bytes)
int     // platform-width: 32-bit on 32-bit systems, 64-bit on 64-bit systems

// Unsigned integers
uint8   // 0 to 255                      (1 byte)
uint16  // 0 to 65,535                   (2 bytes)
uint32  // 0 to 4,294,967,295            (4 bytes)
uint64  // 0 to 18,446,744,073,709,551,615 (8 bytes)
uint    // platform-width

// Aliases — REAL aliases, same underlying type
byte    // alias for uint8 — used for raw bytes
rune    // alias for int32 — used for Unicode code points

// Pointer-sized integer
uintptr // large enough to store a raw pointer address
```

**Critical insight:** `int` is NOT always 64-bit. It matches the platform's word size. This matters for performance-critical code — on a 64-bit machine, `int` operations are natively efficient. Use `int` by default; use fixed-size types only when you need precise bit-widths (binary protocols, file formats, interop).

### Floating-Point Types

```go
float32  // IEEE 754 single precision — ~6-7 significant digits
float64  // IEEE 754 double precision — ~15-16 significant digits
```

```go
// Precision example — this bites beginners
f32 := float32(1.0000001)
f64 := float64(1.0000001)
fmt.Println(f32)  // 1          — precision lost
fmt.Println(f64)  // 1.0000001  — preserved
```

**Rule:** Always use `float64` unless you have a specific reason (memory-constrained systems, GPU interop, matching a C struct layout). The performance difference is negligible on modern hardware; the correctness difference is not.

### Complex Types

```go
complex64   // real and imaginary parts are float32
complex128  // real and imaginary parts are float64

c := complex(3.0, 4.0)  // 3 + 4i
r := real(c)            // 3.0
i := imag(c)            // 4.0
```

### String Type

```go
string  // immutable sequence of bytes (UTF-8 encoded)
```

This is the subtlest basic type. Strings in Go are:

1. **Immutable** — you cannot change a character in place.
2. **Not a slice** — but they can be indexed and sliced like one.
3. **UTF-8 encoded** — iterating by index gives bytes; iterating with `range` gives runes (Unicode code points).

```go
s := "Hello, 世界"

// Byte iteration — wrong for multi-byte characters
for i := 0; i < len(s); i++ {
    fmt.Printf("%d: %x\n", i, s[i])
    // "世" becomes 3 bytes: e4 b8 96
}

// Rune iteration — correct for Unicode
for i, r := range s {
    fmt.Printf("%d: %c (%d)\n", i, r, r)
    // Properly decodes each Unicode code point
}

// String is a read-only slice header internally:
// type stringHeader struct {
//     Data unsafe.Pointer
//     Len  int
// }
```

**Memory model:** A string value is a two-word header: a pointer to the underlying byte array and a length. Assigning a string is cheap — it copies the header, not the bytes.

### Boolean Type

```go
bool  // true or false — exactly one byte in memory
```

Go has no implicit boolean conversions. `if x` where `x` is an integer is a compile error. This eliminates an entire class of bugs.

---

## 3. Zero Values — The Honest Default

In Go, **every type has a zero value**. Variables are always initialized. There is no undefined behavior from uninitialized memory.

```go
var i int        // 0
var f float64    // 0.0
var b bool       // false
var s string     // ""
var p *int       // nil
var sl []int     // nil
var m map[string]int  // nil
var fn func()    // nil
var ch chan int   // nil
var iface interface{}  // nil
```

For structs, zero value means each field is zeroed:

```go
type Point struct {
    X, Y float64
}

var p Point  // p.X == 0.0, p.Y == 0.0
```

**Why this matters:** Zero values enable elegant patterns. A `sync.Mutex` is ready to use at its zero value. A `bytes.Buffer` is ready to use at its zero value. You don't need constructors for types designed with zero values in mind.

```go
// This works with NO initialization
var buf bytes.Buffer
buf.WriteString("hello")
fmt.Println(buf.String())  // "hello"
```

**Design principle:** When you design a type, ask: *Is my zero value useful?* If yes, your API becomes simpler. If no, provide a constructor (`NewXxx`).

---

## 4. Named Types vs Unnamed Types

This distinction is foundational and often misunderstood.

### Unnamed Types (Type Literals)

```go
[]int           // unnamed slice type
map[string]int  // unnamed map type
struct{ X int } // unnamed struct type
func(int) bool  // unnamed function type
*int            // unnamed pointer type
```

Unnamed types are **structurally typed** — two unnamed types are identical if they have the same structure.

### Named Types (Type Declarations)

```go
type Celsius float64
type Fahrenheit float64
type UserID int64
type Matrix struct { ... }
```

Named types are **nominally typed** — two named types are NEVER the same even if their underlying types are identical.

```go
type Celsius float64
type Fahrenheit float64

var c Celsius = 100
var f Fahrenheit = 100

// This is a COMPILE ERROR:
// f = c  // cannot use c (Celsius) as Fahrenheit

// This is required:
f = Fahrenheit(c)  // explicit conversion
```

**Why this is powerful:** Named types create semantic boundaries. `Celsius` and `Fahrenheit` are both `float64` underneath, but the type system prevents you from accidentally mixing them. The Mars Climate Orbiter crashed partly due to this kind of unit confusion in code. Go's type system catches it at compile time.

### Underlying Types

Every type in Go has an underlying type. For basic types, the underlying type is itself:

```go
int      → underlying: int
string   → underlying: string
```

For named types, the underlying type is what you declared them from:

```go
type Celsius float64   → underlying: float64
type MySlice []int     → underlying: []int
```

**The rule for conversions:** You can convert between two types `T1` and `T2` if they share the same underlying type (or are both unnamed pointer types to the same underlying type).

```go
type Celsius float64
type Kelvin float64

var c Celsius = 373.15
var k Kelvin = Kelvin(c)  // valid — same underlying type (float64)
```

---

## 5. Type Aliases vs Type Definitions

Go has two syntaxes that look similar but are entirely different:

```go
// TYPE DEFINITION — creates a NEW type
type Celsius float64   

// TYPE ALIAS — creates another NAME for the SAME type
type Celsius = float64
```

### Type Definition

```go
type Celsius float64

// Celsius is a distinct type
// It does NOT inherit float64's methods
// You CAN define new methods on it
func (c Celsius) ToFahrenheit() float64 {
    return float64(c)*9/5 + 32
}

var c Celsius = 100
// c.Cos() — COMPILE ERROR: Celsius has no method Cos
// even though float64 has math.Cos available as a function
```

### Type Alias

```go
type MyFloat = float64

// MyFloat IS float64 — completely interchangeable
// You CANNOT define methods on an alias to a type from another package
var x MyFloat = 3.14
var y float64 = x  // no conversion needed — same type
```

**When to use aliases:** Primarily for large-scale refactoring (moving a type from one package to another without breaking callers), and in `cgo` interop. In application code, almost always use type definitions.

### The Critical Difference in Method Sets

```go
type Duration int64  // type DEFINITION

func (d Duration) Hours() float64 {
    return float64(d) / float64(time.Hour)
}
```

```go
type Duration = time.Duration  // type ALIAS
// This is identical to time.Duration
// Cannot add methods — would be adding to another package's type
```

---

## 6. Composite Types — Structure

### Arrays — Fixed, Value-Typed

```go
var a [5]int          // [0, 0, 0, 0, 0]
b := [3]string{"a", "b", "c"}
c := [...]float64{1.1, 2.2, 3.3}  // compiler counts elements
```

**Critical:** Arrays in Go are **values**, not references. Assigning an array copies ALL elements.

```go
a := [3]int{1, 2, 3}
b := a          // FULL COPY of all elements
b[0] = 99
fmt.Println(a)  // [1 2 3] — unchanged
fmt.Println(b)  // [99 2 3]
```

**Memory layout:** An array `[N]T` occupies exactly `N * sizeof(T)` bytes, contiguous. No indirection.

**Array type includes its size:** `[3]int` and `[4]int` are completely different types. You cannot assign one to the other.

**When to use arrays:** When size is known at compile time and copying is acceptable (or desirable for immutability). Useful as struct fields for fixed-size data (e.g., a SHA-256 hash is `[32]byte`).

```go
type SHA256Hash [32]byte  // self-documenting, value type, no heap allocation
```

### Slices — Dynamic, Reference-Typed

A slice is a **three-word header**:

```
┌─────────────────────────────────────────┐
│  Slice Header (24 bytes on 64-bit)      │
│                                         │
│  Data *T  → pointer to backing array   │
│  Len  int → number of accessible elems │
│  Cap  int → total capacity of array    │
└─────────────────────────────────────────┘
```

```go
// Creating slices
s1 := []int{1, 2, 3}              // slice literal
s2 := make([]int, 5)              // len=5, cap=5, zeroed
s3 := make([]int, 3, 10)          // len=3, cap=10
s4 := s1[1:3]                     // slice of slice: [2, 3], shares backing array
```

**Sharing backing arrays — the gotcha:**

```go
original := []int{1, 2, 3, 4, 5}
slice := original[1:3]  // [2, 3]

slice[0] = 99           // modifies original too!
fmt.Println(original)   // [1 99 3 4 5]
```

**Append and reallocation:**

```go
s := make([]int, 3, 5)
s = append(s, 4)   // len=4, cap=5, same backing array
s = append(s, 5)   // len=5, cap=5, same backing array
s = append(s, 6)   // len=6, cap=10 — NEW backing array allocated!
                    // old backing array is now disconnected
```

**Growth strategy:** When capacity is exceeded, Go allocates a new array roughly twice the size (the exact formula is more nuanced — it reduces the growth rate for larger slices). This amortizes append to O(1) averaged over many appends.

**Three-index slices — controlling capacity:**

```go
// s[low:high:max] — limits cap to max-low
s := []int{0, 1, 2, 3, 4}
t := s[1:3:3]  // [1, 2], cap=2 (not 4)
// append to t now CANNOT affect s — forces its own allocation
```

This is a defensive pattern to prevent shared backing array mutations.

### Maps

```go
// Declaration
var m map[string]int           // nil map — reads return zero value, writes PANIC
m = make(map[string]int)       // initialized, empty
m2 := map[string]int{"a": 1}  // initialized with data
```

**Map internals:** Go maps are hash tables — approximately O(1) average for get/set/delete. In practice, they're implemented as an array of buckets, each bucket holding up to 8 key-value pairs.

```go
// CRUD operations
m["key"] = 42        // set
v := m["key"]        // get (returns zero value if absent)
delete(m, "key")     // delete

// Existence check — ALWAYS use this pattern
v, ok := m["key"]
if ok {
    // key exists, v is its value
} else {
    // key absent, v is zero value
}
```

**Map is a reference type:** Assigning a map copies the header (a pointer), not the data. Both variables share the underlying hash table.

```go
a := map[string]int{"x": 1}
b := a
b["x"] = 99
fmt.Println(a["x"])  // 99 — a and b share the same map
```

**Map iteration is deliberately randomized** — Go randomizes the iteration order on each run to prevent programs from accidentally depending on a specific order.

```go
// This prints in different order each run:
for k, v := range m {
    fmt.Println(k, v)
}
```

**Maps are NOT safe for concurrent use.** Use `sync.Map` or a `sync.RWMutex` protecting a regular map for concurrent access.

### Structs

```go
type Person struct {
    Name    string
    Age     int
    Email   string
    private bool  // lowercase = unexported (package-private)
}
```

**Struct is a value type.** Assignment copies all fields.

```go
p1 := Person{Name: "Alice", Age: 30}
p2 := p1        // full copy
p2.Name = "Bob"
fmt.Println(p1.Name)  // "Alice" — unchanged
```

**Memory layout — field alignment:**

```go
// BAD layout — wasted space due to padding
type Wasteful struct {
    A bool    // 1 byte + 7 bytes padding
    B float64 // 8 bytes
    C bool    // 1 byte + 7 bytes padding
}
// Total: 24 bytes

// GOOD layout — fields ordered by decreasing size
type Efficient struct {
    B float64 // 8 bytes
    A bool    // 1 byte
    C bool    // 1 byte + 6 bytes padding
}
// Total: 16 bytes
```

The CPU requires that values be aligned to their size (a `float64` must start at an address divisible by 8). Padding is inserted to enforce this. Order fields from largest to smallest to minimize padding.

**Anonymous structs — for local data shapes:**

```go
point := struct {
    X, Y int
}{X: 3, Y: 4}
```

**Struct tags — metadata for reflection:**

```go
type User struct {
    Name  string `json:"name" db:"user_name"`
    Email string `json:"email,omitempty"`
    Age   int    `json:"-"`  // omit from JSON
}
```

Tags are string literals — accessed via reflection at runtime (`reflect.StructTag`). The Go runtime itself doesn't interpret them; tools like `encoding/json` do.

**Struct comparison:**

Two struct values are equal if all their corresponding fields are equal AND all field types are comparable (slices and maps are NOT comparable).

```go
type Point struct{ X, Y int }
p1 := Point{1, 2}
p2 := Point{1, 2}
fmt.Println(p1 == p2)  // true

type Bad struct{ Data []int }
b1 := Bad{[]int{1}}
b2 := Bad{[]int{1}}
// b1 == b2 — COMPILE ERROR: Bad contains uncomparable field
```

---

## 7. Pointer Types — Indirection

```
T    → the value itself (lives on stack or heap)
*T   → an address pointing to where a T lives
```

### Core Operations

```go
x := 42
p := &x         // p is *int — address of x
*p = 100        // dereference — modify x through pointer
fmt.Println(x)  // 100

// Auto-dereference for struct fields
type Point struct{ X, Y int }
pt := &Point{1, 2}
fmt.Println(pt.X)   // same as (*pt).X — Go does this automatically
pt.X = 99           // same as (*pt).X = 99
```

### When to Use Pointers

**Use a pointer when:**

1. **The function must mutate the receiver/argument:**
```go
func (m *Matrix) Scale(factor float64) {
    for i := range m.data {
        m.data[i] *= factor
    }
}
```

2. **The value is large and copying is expensive:**
```go
// Matrix with 1000×1000 float64 = 8MB
// Pass *Matrix, not Matrix
func Multiply(a, b *Matrix) *Matrix { ... }
```

3. **You need to express optionality (nullable):**
```go
type Config struct {
    Timeout *time.Duration  // nil means "use default"
}
```

4. **You need to share state across goroutines (with synchronization):**
```go
type Counter struct {
    mu    sync.Mutex
    count int
}

func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}
```

**Use a value when:**
- The type is small (≤ a few words).
- The type is conceptually immutable (you want copies, not sharing).
- You're working with basic types, small structs (`Point`, `Color`).

### The `new` Function

```go
p := new(int)  // allocates an int, zeroed, returns *int
*p = 42
```

Rarely used directly — struct literals with `&` are more idiomatic:

```go
p := &Point{X: 1, Y: 2}  // idiomatic
p := new(Point)           // less idiomatic for structs
```

### Stack vs Heap — Escape Analysis

Go decides whether to allocate on the stack or heap automatically via **escape analysis**:

```go
func stackAlloc() int {
    x := 42   // x does not escape — stays on stack
    return x  // value copied out
}

func heapAlloc() *int {
    x := 42   // x ESCAPES to heap — its address leaves the function
    return &x // returning a pointer to local variable
}
```

This is NOT a bug in Go — unlike C, returning a pointer to a local is perfectly safe because Go detects the escape and heap-allocates `x`. You never get a dangling pointer.

```bash
# Inspect escape analysis
go build -gcflags="-m" ./...
```

---

## 8. Function Types — First-Class Behavior

Functions are first-class values in Go. A function type describes a function's signature.

```go
// Function type
type Predicate func(int) bool
type Transform func(string) string
type Handler func(http.ResponseWriter, *http.Request)
```

### Functions as Values

```go
double := func(x int) int { return x * 2 }
apply := func(f func(int) int, x int) int { return f(x) }
fmt.Println(apply(double, 5))  // 10
```

### Closures — Functions that Capture Variables

```go
func makeCounter() func() int {
    count := 0  // captured variable
    return func() int {
        count++  // closes over count — count lives on heap
        return count
    }
}

counter := makeCounter()
fmt.Println(counter())  // 1
fmt.Println(counter())  // 2
fmt.Println(counter())  // 3

// Each call to makeCounter creates an independent closure
c2 := makeCounter()
fmt.Println(c2())  // 1 — independent state
```

**Closure capture gotcha — loop variable capture:**

```go
// BUG — all goroutines capture the same variable i
funcs := make([]func(), 5)
for i := 0; i < 5; i++ {
    funcs[i] = func() { fmt.Println(i) }
}
for _, f := range funcs {
    f()  // prints 5 5 5 5 5 — i is 5 after loop ends
}

// FIX — create a new variable in each iteration
for i := 0; i < 5; i++ {
    i := i  // shadow with a new variable
    funcs[i] = func() { fmt.Println(i) }
}
// prints 0 1 2 3 4
```

Note: As of Go 1.22, loop variables are scoped per iteration by default, eliminating this classic bug.

### Variadic Functions

```go
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

fmt.Println(sum(1, 2, 3))        // 6
nums := []int{1, 2, 3}
fmt.Println(sum(nums...))        // 6 — spread operator
```

### Multiple Return Values

```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

result, err := divide(10, 3)
```

### Named Return Values

```go
func minMax(s []int) (min, max int) {
    min, max = s[0], s[0]
    for _, v := range s[1:] {
        if v < min { min = v }
        if v > max { max = v }
    }
    return  // "naked return" — returns min, max as declared
}
```

Named returns are useful for documentation and for `defer`-based error handling patterns, but naked returns hurt readability in long functions.

---

## 9. Interface Types — Contracts

This is the deepest part of Go's type system. Master this and everything else clicks.

### What an Interface IS

An interface is a **set of method signatures**. Any type that implements all those methods **automatically** satisfies the interface — no declaration, no `implements` keyword.

```go
type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// Interface composition
type WriteCloser interface {
    Writer
    Closer
}
```

### Implicit Satisfaction — The Key Insight

```go
type File struct { /* ... */ }

func (f *File) Write(p []byte) (int, error) { /* ... */ }
func (f *File) Close() error { /* ... */ }

// *File automatically satisfies io.Writer, io.Closer, io.WriteCloser
// There is NO declaration of this. Go checks at compile time.

var wc io.WriteCloser = &File{}  // valid
```

This design has profound consequences:
- **Decoupling:** The author of `File` never needs to know about `io.WriteCloser`.
- **Retroactive implementation:** You can make any existing type satisfy a new interface without touching it (using a wrapper or adapter).
- **Small interfaces:** Interfaces grow organically from use rather than being planned up-front.

### The Interface Design Principle

```go
// BAD — too fat, hard to satisfy
type Animal interface {
    Eat()
    Sleep()
    Speak() string
    Move()
    Breathe()
}

// GOOD — minimal interfaces, compose as needed
type Speaker interface {
    Speak() string
}

type Mover interface {
    Move()
}

// Compose when needed
type ActiveAnimal interface {
    Speaker
    Mover
}
```

Rob Pike's rule: *"The bigger the interface, the weaker the abstraction."*

`io.Reader` has 1 method. `io.Writer` has 1 method. Together, they power nearly all of Go's I/O. This is the ideal.

### Defining Interfaces from the Consumer's Perspective

```go
// BAD — define a giant interface matching your struct
// Then accept that interface in functions
type UserServiceInterface interface {
    CreateUser(...)
    GetUser(...)
    UpdateUser(...)
    DeleteUser(...)
    ListUsers(...)
    // 20 more methods...
}

// GOOD — define minimal interfaces at the point of use
// The function only needs what it actually uses
func sendWelcomeEmail(u interface{ Email() string }) {
    // Only needs Email() — nothing else
}
```

---

## 10. Method Sets — The Hidden Rule

This is where most Go developers hit walls. Method sets determine which interface a type satisfies, and the rules depend on whether you're working with a value or a pointer.

### The Rules

```
Type T:
  Method set = all methods with receiver T

Type *T:
  Method set = all methods with receiver T OR *T
```

In plain English: **A pointer type can use all methods. A value type can only use value receiver methods.**

```go
type Counter struct{ n int }

func (c Counter) Value() int   { return c.n }    // value receiver
func (c *Counter) Inc()        { c.n++ }          // pointer receiver

type Valuer interface{ Value() int }
type Incer  interface{ Inc() }

var c Counter

// Counter (value) satisfies Valuer — Value() has value receiver
var v Valuer = c   // OK

// Counter (value) does NOT satisfy Incer — Inc() has pointer receiver
// var i Incer = c  // COMPILE ERROR

// *Counter satisfies BOTH
var i Incer = &c   // OK
var v2 Valuer = &c // OK — *T includes T's method set
```

### Why This Rule Exists

Consider this:

```go
func (c *Counter) Inc() { c.n++ }

// If you could call this on a non-addressable value:
Counter{}.Inc()  // This is NOT valid
```

If you have a temporary value (not addressable), taking its address is impossible. The compiler enforces the rule to prevent you from calling pointer methods on values that cannot be addressed — because the mutation would be lost.

### Auto-dereferencing for Convenience

When you have a pointer and call a value method, Go auto-dereferences:

```go
c := &Counter{n: 5}
fmt.Println(c.Value())  // Go computes (*c).Value() automatically
```

But this convenience does NOT change the method set for interface satisfaction.

---

## 11. Type Embedding — Composition

Embedding is Go's answer to inheritance. It is not inheritance. It is **delegation with promotion**.

### Struct Embedding

```go
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " makes a sound"
}

type Dog struct {
    Animal          // embedded — NOT a field named "Animal"
    Breed string
}

func (d Dog) Speak() string {  // Dog can override
    return d.Name + " barks"
}
```

```go
d := Dog{
    Animal: Animal{Name: "Rex"},
    Breed:  "Labrador",
}

fmt.Println(d.Name)      // promoted — same as d.Animal.Name
fmt.Println(d.Speak())   // "Rex barks" — Dog's method
fmt.Println(d.Animal.Speak())  // "Rex makes a sound" — explicit
```

**What embedding does:**
1. **Promotes fields and methods** of the embedded type to the outer type.
2. **Does NOT mean inheritance** — there's no polymorphism via embedding alone.
3. **The embedded type retains its identity** — you can always access it directly.

### Embedding for Interface Satisfaction

The most powerful use: embed types to compose interface implementations.

```go
type ReadWriter struct {
    io.Reader  // embedded
    io.Writer  // embedded
}

// ReadWriter now automatically satisfies io.ReadWriter
// because it has both Read and Write methods via promotion
```

### Embedding Interfaces in Interfaces

```go
type ReadWriteCloser interface {
    io.Reader   // embeds Reader interface
    io.Writer   // embeds Writer interface
    io.Closer   // embeds Closer interface
}
```

This composes interfaces. `ReadWriteCloser` requires `Read`, `Write`, and `Close`.

### Embedding vs Named Fields — The Semantic Difference

```go
// Embedding — promotes methods
type Logger struct {
    log.Logger  // methods promoted to Logger
}

// Named field — does NOT promote, explicit access required
type Logger2 struct {
    inner log.Logger  // must write l.inner.Printf(...)
}
```

Use embedding when you want transparent access. Use named fields when you want explicit delegation.

### Embedding Conflicts

```go
type A struct{}
type B struct{}

func (A) Hello() string { return "A" }
func (B) Hello() string { return "B" }

type C struct {
    A
    B
}

c := C{}
// c.Hello()  — COMPILE ERROR: ambiguous selector
c.A.Hello()  // OK — explicit
c.B.Hello()  // OK — explicit

// Unless C defines its own Hello:
func (c C) Hello() string { return "C" }  // resolves ambiguity
```

---

## 12. Type Conversion vs Type Assertion

These look similar. They are fundamentally different operations.

### Type Conversion — Compile-Time Operation

```go
// T(value) — convert value to type T
// Valid only if conversion rules allow it

var x int32 = 42
var y int64 = int64(x)  // valid: numeric conversion

type Celsius float64
var c Celsius = 100
var f float64 = float64(c)  // valid: same underlying type

// []byte and string are interconvertible
s := "hello"
b := []byte(s)   // string → []byte (copies bytes)
s2 := string(b)  // []byte → string (copies bytes)

// rune conversions
r := rune('A')
i := int(r)  // 65
```

**Conversion is always explicit.** Go has no implicit type conversions. This prevents entire classes of bugs (C's integer promotion rules are the historical source of countless CVEs).

### Type Assertion — Runtime Operation

Type assertion extracts the concrete value from an interface.

```go
// x.(T) — asserts that interface value x holds a T
// Panics if wrong

var i interface{} = "hello"
s := i.(string)    // s is "hello"
// n := i.(int)    // PANIC: interface holds string, not int

// Safe form — always use this
s, ok := i.(string)
if ok {
    fmt.Println("got string:", s)
} else {
    fmt.Println("not a string")
}
```

**Conversion = "reshape this value at compile time."**
**Assertion = "extract the concrete value from this interface at runtime."**

---

## 13. The Empty Interface and `any`

```go
interface{}  // the empty interface — zero method requirements
any          // alias for interface{} (Go 1.18+)
```

A type with zero methods is satisfied by **every type**. Every value in Go satisfies the empty interface.

```go
func PrintAnything(v any) {
    fmt.Println(v)
}

PrintAnything(42)
PrintAnything("hello")
PrintAnything([]int{1, 2, 3})
PrintAnything(nil)
```

**The danger of `any`:**

Using `any` erases type information. You lose compile-time safety and must use runtime type assertions to recover type information. This is expensive and error-prone.

**Expert rule:** `any` is appropriate when you genuinely cannot know the type at compile time (serialization, plugin systems, reflection-based frameworks). In application code, if you're reaching for `any`, ask whether generics would be cleaner.

```go
// BAD — loses type safety
func sum(nums []any) any {
    total := 0
    for _, n := range nums {
        total += n.(int)  // will panic if not int
    }
    return total
}

// GOOD — with generics
func sum[T int | float64](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}
```

---

## 14. Type Switches — Runtime Dispatch

Type switches are the idiomatic way to handle multiple types from an interface value.

```go
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int: %d", v)
    case string:
        return fmt.Sprintf("string: %q (len=%d)", v, len(v))
    case bool:
        return fmt.Sprintf("bool: %v", v)
    case []int:
        return fmt.Sprintf("[]int with %d elements", len(v))
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown type: %T", v)
    }
}
```

Inside each case, `v` has the concrete type of that case — not the interface type. This is what makes type switches powerful: you get typed access to the value.

**Multi-type cases:**

```go
switch v := i.(type) {
case int, int64:
    // v is still the interface type here — both types matched
    fmt.Println("some integer")
case string, []byte:
    fmt.Println("string-like")
}
```

**Type switches vs type assertions:**
- Type assertion: when you know what type to expect.
- Type switch: when you want to handle multiple possibilities.

---

## 15. Interface Internals — The Two-Word Header

Understanding how interfaces are represented in memory is critical for performance-conscious Go.

An interface value is **always two machine words**:

```
┌────────────────────────────────────────────┐
│           Interface Value (16 bytes)       │
│                                            │
│  word 1: *itab  → type descriptor         │
│  word 2: *data  → pointer to actual value │
└────────────────────────────────────────────┘
```

**The `itab` (interface table):**
```
itab contains:
- pointer to the interface type descriptor
- pointer to the concrete type descriptor
- method dispatch table (function pointers)
```

### The Nil Interface Paradox

This is one of the most-asked Go interview questions:

```go
func getError() error {
    var p *MyError = nil   // typed nil pointer
    return p               // returning a *MyError nil as error interface
}

err := getError()
fmt.Println(err == nil)  // FALSE — this surprises everyone
```

Why? Because the returned interface value has:
- `itab` = pointing to `*MyError` type descriptor (non-nil)
- `data` = nil pointer

An interface is only `nil` when BOTH words are nil.

```go
// CORRECT way to return nil error
func getError() error {
    var p *MyError = nil
    if p == nil {
        return nil  // return untyped nil — both words nil
    }
    return p
}
```

**Rule:** Never return a typed nil pointer where an interface is expected. Return the untyped `nil` literal directly.

### Interface Method Dispatch Cost

Calling a method through an interface is slightly more expensive than a direct call:
1. Load `itab` from interface value.
2. Look up method pointer in dispatch table.
3. Call through the function pointer.

This is called **dynamic dispatch** — the method isn't resolved until runtime. It's comparable in cost to a virtual function call in C++. For hot paths, you may want to avoid interface dispatch.

---

## 16. Generics — Parametric Polymorphism

Added in Go 1.18. Generics allow writing type-safe code that works across multiple types without sacrificing compile-time safety or using `any`.

### Type Parameters

```go
// T is a type parameter constrained by 'any'
func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

doubled := Map([]int{1, 2, 3}, func(x int) int { return x * 2 })
strs := Map([]int{1, 2, 3}, func(x int) string { return strconv.Itoa(x) })
```

### Constraints

Constraints define what operations are valid on a type parameter.

```go
// Built-in constraints from golang.org/x/exp/constraints
type Ordered interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
    ~float32 | ~float64 | ~string
}

func Min[T Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

fmt.Println(Min(3, 5))        // 3
fmt.Println(Min(3.14, 2.71))  // 2.71
fmt.Println(Min("a", "b"))    // "a"
```

### The `~` Operator — Type Approximation

The `~T` syntax means "any type whose underlying type is T."

```go
type Celsius float64

// This constraint accepts float64 AND Celsius AND any other named float64
type Float64Like interface {
    ~float64
}

func Double[T Float64Like](v T) T {
    return v * 2
}

var c Celsius = 100
fmt.Println(Double(c))      // Celsius(200)
fmt.Println(Double(3.14))   // 6.28
```

Without `~`, `Celsius` would not satisfy `float64` — they are different named types.

### Generic Constraints with Methods

```go
type Stringer interface {
    String() string
}

func PrintAll[T Stringer](items []T) {
    for _, item := range items {
        fmt.Println(item.String())
    }
}
```

### Generic Data Structures

```go
type Stack[T any] struct {
    data []T
}

func (s *Stack[T]) Push(v T) {
    s.data = append(s.data, v)
}

func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.data) == 0 {
        return zero, false
    }
    last := s.data[len(s.data)-1]
    s.data = s.data[:len(s.data)-1]
    return last, true
}

// Usage
s := Stack[int]{}
s.Push(1)
s.Push(2)
v, ok := s.Pop()  // v=2, ok=true
```

### When to Use Generics

**Use generics when:**
- Writing data structures (Stack, Queue, Tree, Set).
- Writing algorithms that work on any type with specific operations (sort, filter, map, reduce).
- The type parameter is truly arbitrary and you need type safety.

**Don't use generics when:**
- An interface suffices — if you just need to call methods, use an interface.
- You're over-abstracting — if you only have one concrete use case, just write the concrete code.

---

## 17. Channels as Types

Channels are typed conduits for communication between goroutines. They are first-class types.

```go
chan T       // bidirectional channel of T
<-chan T     // receive-only channel of T
chan<- T     // send-only channel of T
```

```go
ch := make(chan int)        // unbuffered
ch := make(chan int, 100)   // buffered, capacity 100
```

**Direction restriction is a type-level contract:**

```go
func producer(out chan<- int) {
    // can only send — compile error if you try to receive
    out <- 42
}

func consumer(in <-chan int) {
    // can only receive — compile error if you try to send
    v := <-in
    fmt.Println(v)
}

ch := make(chan int, 1)
go producer(ch)  // bidirectional converts to chan<- implicitly
consumer(ch)     // bidirectional converts to <-chan implicitly
```

**Channels as synchronization primitives:**

```go
done := make(chan struct{})  // zero-size struct — no data, just signal

go func() {
    doWork()
    close(done)  // signal completion
}()

<-done  // wait for completion
```

---

## 18. The Complete Mental Model

Now you have all the pieces. Here is how they fit:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Go's Complete Type System                       │
│                                                                     │
│  WHAT IT IS (Structure)              WHAT IT DOES (Behavior)        │
│  ──────────────────────              ─────────────────────          │
│  Basic:  int, float64, string        Methods defined on named types │
│  Composite: struct, slice,           func (t T) Method() RetType    │
│             map, array, chan         func (t *T) Mutate()           │
│  Pointer: *T                                                         │
│  Function: func(T) U                WHAT IT PROMISES (Capability)   │
│  Generic: Stack[T]                  ──────────────────────────────  │
│                                     Interfaces satisfied implicitly │
│  NAMED vs UNNAMED                   io.Reader, fmt.Stringer,        │
│  ─────────────────                  your own interfaces             │
│  Named types have identity          Compile-time checked            │
│  Unnamed types are structural                                        │
│                                                                     │
│  VALUE vs POINTER                                                   │
│  ─────────────────                                                  │
│  Value: owns the data, copies on assign                             │
│  Pointer: holds address, shares the data                            │
│                                                                     │
│  INTERFACE INTERNALS                                                │
│  ──────────────────                                                 │
│  Two words: (itab, data)                                            │
│  Nil only when BOTH are nil                                         │
│  Dynamic dispatch via method table                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### The Five Questions to Ask About Any Type

```
1. Is it named or unnamed?
   Named → has identity, can have methods, can satisfy interfaces
   Unnamed → structural, no methods directly

2. Is it a value type or reference type?
   Value: int, float64, bool, array, struct → copies on assign
   Reference: slice, map, channel, pointer → shares underlying data

3. What are its zero values?
   Design around zero values being useful

4. Does it implement any interfaces?
   Which contracts does this type satisfy implicitly?

5. Should I use T or *T?
   T → small, immutable, conceptually value-like
   *T → large, mutable, shared state, optional (nil-able)
```

---

## 19. Expert Patterns and Anti-Patterns

### Pattern 1 — Accept Interfaces, Return Concrete Types

```go
// CORRECT
func NewBuffer(r io.Reader) *bytes.Buffer {
    // accepts the broad interface, returns specific type
    // callers get concrete type's full API
}

// BAD — over-abstracting return type
func NewBuffer(r io.Reader) io.ReadWriter {
    // callers lose access to Buffer-specific methods
}
```

### Pattern 2 — Small Interface Design

```go
// Instead of this:
type Repository interface {
    Find(id int) (*User, error)
    FindAll() ([]*User, error)
    Save(u *User) error
    Delete(id int) error
    // ... 10 more methods
}

// Prefer composing small interfaces:
type Finder interface {
    Find(id int) (*User, error)
}

type Saver interface {
    Save(u *User) error
}

// Functions take only what they need
func sendEmail(f Finder, id int) error {
    u, err := f.Find(id)
    // ...
}
```

### Pattern 3 — Functional Options Pattern (uses function types)

```go
type Server struct {
    host    string
    port    int
    timeout time.Duration
}

type Option func(*Server)

func WithTimeout(t time.Duration) Option {
    return func(s *Server) { s.timeout = t }
}

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func NewServer(opts ...Option) *Server {
    s := &Server{host: "localhost", port: 8080}
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage
s := NewServer(
    WithPort(9090),
    WithTimeout(30*time.Second),
)
```

### Pattern 4 — Sentinel Types (typed constants for type safety)

```go
type Direction int

const (
    North Direction = iota
    South
    East
    West
)

func Move(d Direction) {
    // d can ONLY be a Direction — not an arbitrary int
}

Move(North)  // OK
Move(42)     // COMPILE ERROR — untyped int constant would work, but int variable won't
```

### Anti-Pattern 1 — Interface Pollution

```go
// BAD — creating interfaces before you have multiple implementations
type UserService interface {
    // ... 20 methods
}
type userServiceImpl struct{}
// There is exactly one implementation. The interface adds nothing.

// GOOD — use the concrete type; extract interface only when needed
type UserService struct{}
```

### Anti-Pattern 2 — Premature Generalization

```go
// BAD — using any everywhere
func process(data any) any { ... }

// GOOD — use concrete types, then generics if needed
func processUsers(data []User) []Result { ... }
```

### Anti-Pattern 3 — Returning Typed Nil as Interface

```go
// BAD
func getErr() error {
    var e *PathError = nil
    return e  // non-nil interface!
}

// GOOD
func getErr() error {
    return nil  // untyped nil — truly nil interface
}
```

---

## Appendix — Quick Reference

### Operator Reference

| Syntax | Meaning |
|--------|---------|
| `T` | A value of type T |
| `*T` | A pointer to type T |
| `&v` | Address of value v |
| `*p` | Dereference pointer p |
| `T(v)` | Convert v to type T |
| `v.(T)` | Assert interface v holds type T |
| `[]T` | Slice of T |
| `[N]T` | Array of N T's |
| `map[K]V` | Map from K to V |
| `chan T` | Bidirectional channel of T |
| `<-chan T` | Receive-only channel |
| `chan<- T` | Send-only channel |
| `func(T) U` | Function type |
| `interface{M()}` | Interface type |

### Type System Decision Tree

```
You need a new type...
│
├─ Does it hold data?
│   ├─ Fixed-size, same type → Array [N]T
│   ├─ Dynamic, same type   → Slice []T
│   ├─ Key-value pairs      → Map map[K]V
│   └─ Mixed named fields   → Struct
│
├─ Does it describe behavior?
│   └─ Interface
│
├─ Is it semantically distinct from its underlying type?
│   └─ Named type: type Celsius float64
│
└─ Does it need to point elsewhere or be nil?
    └─ Pointer *T
```

---

*A type system is not a cage. It is a map. The more precisely you understand the map, the more freely you can navigate.*

Here is the complete guide — 19 chapters, covering every layer from atoms to architecture.

**The conceptual spine of the guide:**

The entire type system resolves into three axes: **Structure** (what a type looks like in memory), **Behavior** (methods attached to it), and **Capability** (interfaces it implicitly satisfies). Every keyword, every operator, every rule maps to one of these.

**The five chapters most Go developers never fully internalize:**

- **§10 — Method Sets**: The `T` vs `*T` rule for interface satisfaction. Most bugs involving "why doesn't my type satisfy this interface?" trace here.
- **§15 — Interface Internals**: The two-word header explains the infamous typed-nil paradox. An interface is nil only when *both* its type pointer and data pointer are nil.
- **§4/5 — Named Types vs Aliases**: Type definitions create semantic identity (the Mars Climate Orbiter lesson). Aliases are almost exclusively for large-scale refactoring.
- **§11 — Embedding**: Not inheritance — it is *delegation with promotion*. The distinction matters enormously when reasoning about method sets and interface satisfaction.
- **§16 — Generics with `~`**: The tilde operator (`~T`) is what makes generics practical for named types like `Celsius`. Without it, your constraints would reject every named float64-based type.

**The one mental model to commit to memory:**

```
Type    = blueprint of what something IS
Methods = blueprint of what something CAN DO
Interface = description of what something MUST DO
Pointer = directions to where something LIVES
```