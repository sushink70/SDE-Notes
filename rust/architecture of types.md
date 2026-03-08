# The Architecture of Types: A Comprehensive Guide

The confusion you feel is valid — these concepts *look* similar on the surface, but they solve fundamentally different problems. Think of them as different **layers of abstraction**: some describe **data layout**, some describe **behavior contracts**, and some are just **aliases**. Let me unpack each dimension.

---

## The Mental Model First

Before any code, burn this hierarchy into your mind:

```
┌─────────────────────────────────────────────────┐
│               TYPE SYSTEM LAYERS                │
├─────────────────────────────────────────────────┤
│  LAYER 1: DATA LAYOUT  → struct, union, enum    │
│  LAYER 2: BEHAVIOR     → interface, trait, vtbl │
│  LAYER 3: NAMING       → type alias, typedef    │
│  LAYER 4: COMPOSITION  → embedding, inheritance │
└─────────────────────────────────────────────────┘
```

They are NOT the same. They operate on different layers. Your confusion comes from syntax similarity, not semantic similarity.

---

## C — The Foundation (No Abstractions, Raw Truth)

C has no classes, no interfaces, no traits. Just raw memory layout.

### `struct` — Pure Data Layout

```c
// struct = a named block of memory with fields
// It describes HOW data is arranged in memory. Nothing more.
struct Point {
    int x;
    int y;
};

// sizeof(Point) = 8 bytes (2 ints)
// x is at offset 0, y is at offset 4
```

### `typedef` — A Name Alias

```c
// typedef creates a NEW NAME for an existing type.
// It does NOT create a new type. The compiler treats them identically.
typedef unsigned long long u64;
typedef struct Point Point; // So you can write `Point p` instead of `struct Point p`

// These are IDENTICAL to the compiler:
unsigned long long a = 10;
u64 b = 10;  // same thing
```

### `union` — Overlapping Memory

```c
// All fields share the SAME memory location
// Only one field is valid at a time
union Variant {
    int   i;
    float f;
    char  c;
};
// sizeof(Variant) = 4 (size of largest member)
```

### Function Pointers — C's "Interface"

C has no interfaces, but you simulate behavior contracts with function pointers:

```c
// This IS C's version of an interface
typedef struct {
    void (*draw)(void* self);
    void (*resize)(void* self, int w, int h);
} ShapeVTable;

typedef struct {
    ShapeVTable* vtable;  // pointer to behavior
    // ... data fields
} Shape;

// This is literally what C++ vtables compile down to
```

**Key insight**: In C, data and behavior are always separate. You manually wire them together. Every higher-level language automates this wiring.

---

## C++ — Adding Behavior to Data

C++ keeps C's struct but layers behavior on top.

### `struct` vs `class` — Only Default Visibility Differs

```cpp
struct Point {
    int x, y;          // public by default
    void print() { }   // can have methods
};

class Point {
    int x, y;          // private by default
    void print() { }
};

// These are IDENTICAL except default access modifier.
// Idiomatic C++: struct for plain data, class for encapsulated objects.
```

### `interface` via Abstract Classes + vtable

C++ has no `interface` keyword. You simulate it:

```cpp
// Pure abstract class = interface
class Drawable {
public:
    virtual void draw() = 0;      // pure virtual = must implement
    virtual ~Drawable() = default;
};

class Circle : public Drawable {
    float radius;
public:
    void draw() override { /* ... */ }
};

// Under the hood:
// Every object with virtual methods has a hidden pointer (vptr)
// pointing to a vtable — a table of function pointers.
// This is runtime dispatch. It costs one pointer dereference.
```

### `using` / `typedef` — Type Aliases

```cpp
using u64 = unsigned long long;      // modern C++ syntax
typedef unsigned long long u64;      // old C syntax (both work)

// Template aliases (only `using` can do this):
template<typename T>
using Vec = std::vector<T>;
Vec<int> v;  // same as std::vector<int>
```

### The Critical Cost Model

```
Stack object (no virtual):  O(1) — direct call, compiler knows address at compile time
Virtual method call:        O(1) — but with one extra pointer dereference (vptr → vtable → fn)
```

---

## Go — Interfaces Are the Core Idea

Go's type system is philosophically different. It bets everything on **implicit interface satisfaction**.

### `struct` — Data, Same as C

```go
type Point struct {
    X, Y int
}

// Methods are defined OUTSIDE the struct
func (p Point) Distance() float64 {
    return math.Sqrt(float64(p.X*p.X + p.Y*p.Y))
}
```

### `type` — Creates a NEW Distinct Type

This is where Go differs from C's `typedef`:

```go
type Celsius    float64
type Fahrenheit float64

var c Celsius    = 100.0
var f Fahrenheit = 100.0

// THIS DOES NOT COMPILE:
c = f  // ERROR: cannot use f (type Fahrenheit) as type Celsius

// But in C, typedef float Celsius; typedef float Fahrenheit; — they ARE the same type
```

`type` in Go creates a **nominally distinct type**. You cannot accidentally mix them. This is a safety guarantee C's typedef never gave you.

```go
// type can wrap ANY type, not just structs:
type Handler func(http.ResponseWriter, *http.Request)  // function type
type StringSlice []string                               // slice type
type UserID int64                                       // integer type

// You can add methods to any named type:
func (s StringSlice) Contains(target string) bool {
    for _, v := range s {
        if v == target { return true }
    }
    return false
}
```

### `interface` — Behavior Contract (Implicit Satisfaction)

```go
type Stringer interface {
    String() string
}

type Animal struct { Name string }

// Animal implicitly satisfies Stringer — NO explicit declaration needed
func (a Animal) String() string {
    return a.Name
}

// This works automatically:
var s Stringer = Animal{Name: "wolf"}
```

**The philosophical difference from C++/Java**:
- C++/Java: You declare "I implement this interface" → **nominal** (name-based)
- Go: If you have the methods, you satisfy it → **structural** (shape-based)

This means you can satisfy interfaces defined in packages you don't own. Massive decoupling.

### How Go Interfaces Work Under the Hood

```
interface value = (type pointer, data pointer)
                       ↑               ↑
               points to type    points to actual
               metadata (itab)   data or pointer to data

itab contains:
  - pointer to type information
  - pointer to method implementations
```

```go
// The empty interface: accepts everything
interface{}    // old syntax
any            // new alias (Go 1.18+)

// An interface with zero methods is satisfied by ALL types
var x any = 42
x = "hello"
x = struct{ Name string }{"world"}
```

### `struct` Embedding — Go's Composition (Not Inheritance)

```go
type Logger struct {
    prefix string
}
func (l Logger) Log(msg string) { fmt.Println(l.prefix, msg) }

type Server struct {
    Logger          // embedded — NOT inheritance
    host   string
}

s := Server{Logger: Logger{prefix: "[SERVER]"}, host: "localhost"}
s.Log("started")   // promoted method — syntactic sugar for s.Logger.Log("started")
```

Embedding is NOT inheritance. There is no polymorphism, no `super`, no virtual dispatch. It's mechanical promotion.

---

## Rust — The Most Precise Type System

Rust separates data and behavior most explicitly of all.

### `struct` — Data Only, Always

```rust
struct Point {
    x: f64,
    y: f64,
}

// Methods live in impl blocks, completely separate
impl Point {
    fn distance(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}
```

### `enum` — Algebraic Data Type (Far More Powerful Than C's enum)

```rust
// Rust enum = tagged union (C union + discriminant tag)
enum Shape {
    Circle(f64),              // carries data
    Rectangle(f64, f64),      // carries data
    Point,                    // no data
}

// The compiler guarantees exhaustive pattern matching
match shape {
    Shape::Circle(r)       => println!("circle r={}", r),
    Shape::Rectangle(w, h) => println!("rect {}x{}", w, h),
    Shape::Point           => println!("point"),
}
// If you miss an arm → compile error. Zero runtime surprises.
```

### `type` — Type Alias (NOT a new type, unlike Go)

```rust
type Kilometers = i32;   // alias — same type as i32
let k: Kilometers = 5;
let i: i32 = k;         // COMPILES FINE — they are the same type

// For a TRULY new type, use the newtype pattern:
struct Kilometers(i32);  // tuple struct wrapping i32
// Now Kilometers and i32 are distinct types
```

This is the opposite of Go: Rust's `type` is like C's `typedef` (alias). Go's `type` creates a new type. Rust's newtype pattern (`struct Wrapper(T)`) achieves what Go's `type` does.

### `trait` — Behavior Contract (Rust's Interface)

```rust
trait Drawable {
    fn draw(&self);
    fn bounding_box(&self) -> (f64, f64) {  // default implementation
        (0.0, 0.0)
    }
}

struct Circle { radius: f64 }

impl Drawable for Circle {
    fn draw(&self) {
        println!("Drawing circle r={}", self.radius);
    }
}
```

### Static vs Dynamic Dispatch — The Key Rust Distinction

```rust
// STATIC dispatch (monomorphization) — zero runtime cost
// Compiler generates a SEPARATE function for each concrete type
fn render_static<T: Drawable>(shape: &T) {
    shape.draw();
}

// DYNAMIC dispatch — runtime cost (like C++ virtual)
// Uses a fat pointer: (data ptr, vtable ptr)
fn render_dynamic(shape: &dyn Drawable) {
    shape.draw();
}

// dyn Trait = fat pointer = (ptr to data, ptr to vtable)
// Same as C++ vptr mechanism, but explicit and opt-in
```

This is the most honest type system: you CHOOSE dispatch mode. In C++, `virtual` always means dynamic. In Rust, you explicitly write `dyn` when you want it.

### Trait Bounds — Composition of Behavior

```rust
use std::fmt;

// Require multiple behaviors simultaneously
fn print_and_compare<T: fmt::Display + PartialOrd>(a: T, b: T) {
    if a > b { println!("{} > {}", a, b); }
}

// where clause for readability
fn complex_fn<T, U>(t: T, u: U) 
where 
    T: fmt::Display + Clone,
    U: fmt::Debug + PartialEq,
{ }
```

---

## The Grand Comparison Table

```
┌──────────────┬───────────────┬─────────────────┬──────────────┬──────────────────┐
│  Concept     │     C         │      C++        │     Go       │      Rust        │
├──────────────┼───────────────┼─────────────────┼──────────────┼──────────────────┤
│ Data layout  │ struct        │ struct/class    │ struct       │ struct           │
│ New type     │ ✗ (typedef=  │ class           │ type Foo T   │ struct Foo(T)    │
│              │  alias only)  │                 │              │ (newtype)        │
│ Alias        │ typedef       │ using/typedef   │ ✗            │ type Foo = T     │
│ Interface    │ fn ptr struct │ abstract class  │ interface    │ trait            │
│ Dispatch     │ manual        │ virtual (always │ always dyn   │ explicit:        │
│              │               │ dynamic)        │              │ T:Trait or dyn   │
│ Satisfaction │ manual        │ explicit(: Base)│ implicit     │ explicit(impl)   │
│ Sum types    │ union+enum    │ std::variant    │ ✗            │ enum (ADT)       │
│ Composition  │ manual        │ inheritance     │ embedding    │ trait defaults + │
│              │               │                 │              │ struct fields    │
└──────────────┴───────────────┴─────────────────┴──────────────┴──────────────────┘
```

---

## The Deep Insight: Two Axes of Type Systems

All of this maps onto two axes:

```
                    DATA SIDE
                    
                 Nominal           Structural
                (name matters)   (shape matters)
              ┌──────────────┬────────────────────┐
  Explicit    │  C++/Java    │                    │
  (you declare│  class Foo   │                    │
   the relation│  : IBar { } │                    │
              ├──────────────┼────────────────────┤
  Implicit    │  Rust traits │    Go interfaces   │
  (compiler   │  (explicit   │  (implicit satisfy)│
   checks)    │  impl, but   │                    │
              │  no inherit) │                    │
              └──────────────┴────────────────────┘
                    BEHAVIOR SIDE
```

- **C++**: Nominal + Explicit — you name your relationships
- **Go**: Structural + Implicit — if you have the shape, you qualify
- **Rust**: Nominal + Explicit (but no inheritance) — clearest separation of data and behavior

---

## Memory Layout — The Physical Truth

```
// C struct:
struct Foo { int a; char b; int c; };
// Memory: [a:4][b:1][pad:3][c:4] = 12 bytes (alignment padding)

// Go struct (same rules):
type Foo struct { A int32; B byte; C int32 }
// Memory: [A:4][B:1][pad:3][C:4] = 12 bytes

// Rust struct (may reorder fields for optimal layout by default):
struct Foo { a: i32, b: u8, c: i32 }
// Rust may reorder: [a:4][c:4][b:1][pad:3] = 12 bytes
// Use #[repr(C)] to force C-compatible layout

// C++ with virtual:
class Bar { virtual void f(); int x; };
// Memory: [vptr:8][x:4][pad:4] = 16 bytes — hidden cost!
```

---

## When to Use What (Decision Framework)

```
Do you need to describe DATA LAYOUT?
  → struct (all languages)

Do you need a NEW DISTINCT TYPE for safety?
  → Go: type Foo Bar
  → Rust: struct Foo(Bar)  [newtype pattern]
  → C++: class Foo { Bar val; ... }

Do you just want a shorter name (alias)?
  → C: typedef
  → C++: using
  → Rust: type Foo = Bar
  → Go: does NOT have true aliases (type always creates new type)

Do you need to describe BEHAVIOR that multiple types share?
  → Go: interface
  → Rust: trait
  → C++: abstract class / pure virtual
  → C: function pointer struct (vtable)

Do you need ZERO-COST abstraction?
  → Rust: generics with trait bounds (static dispatch / monomorphization)
  → C++: templates

Do you need runtime polymorphism (different types in a collection)?
  → Rust: Box<dyn Trait> or &dyn Trait
  → Go: interface (always dynamic)
  → C++: virtual + pointer/reference
```

---

## The Meta-Lesson

The reason these look similar is that **every language is solving the same two fundamental problems**:

1. **How do I organize data in memory?** → struct, class, enum
2. **How do I write code that works on many types?** → interface, trait, generics, virtual

The differences between languages are:
- **When** the decision is made (compile time vs runtime)
- **Who** declares the relationship (caller, implementer, or nobody)
- **What** the cost is (zero-cost, one deref, full boxing)

Once you see type systems through this lens — data layout vs behavior contract vs naming — you will never confuse them again. Every new language you encounter, ask: *"How does this language answer those two questions?"* The answer reveals its entire philosophy.