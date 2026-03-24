# Type System Mastery: Struct, Enum, Union & Beyond
### A Deep Technical Guide for Go, Rust, and C

> *"The type system is not a cage — it is a language. The more fluently you speak it, the more precisely you can express reality in code."*

---

## Table of Contents

1. [Mental Model: What Are Types Really?](#1-mental-model-what-are-types-really)
2. [Structs — Product Types](#2-structs--product-types)
   - 2.1 C Structs
   - 2.2 Go Structs
   - 2.3 Rust Structs
   - 2.4 Memory Layout & Padding
   - 2.5 Tuple Structs (Rust)
   - 2.6 Unit Structs (Rust)
   - 2.7 Anonymous Structs
   - 2.8 Embedded / Promoted Fields (Go)
   - 2.9 Struct Methods
3. [Enums — Sum Types / Tagged Unions](#3-enums--sum-types--tagged-unions)
   - 3.1 C Enums
   - 3.2 Go Enums (iota pattern)
   - 3.3 Rust Enums (Algebraic Data Types)
   - 3.4 Enum with Data (Rust)
   - 3.5 Option\<T\> and Result\<T, E\>
4. [Unions — Untagged / Raw Overlapping Memory](#4-unions--untagged--raw-overlapping-memory)
   - 4.1 C Unions
   - 4.2 Tagged Unions in C (manual)
   - 4.3 Rust Unions (unsafe)
5. [Interfaces & Traits — Behavioral Abstraction](#5-interfaces--traits--behavioral-abstraction)
   - 5.1 Go Interfaces
   - 5.2 Rust Traits
   - 5.3 Trait Objects vs Generics (Static vs Dynamic Dispatch)
   - 5.4 Interface Composition (Go)
   - 5.5 Trait Bounds & Where Clauses
   - 5.6 Blanket Implementations
6. [Newtype Pattern](#6-newtype-pattern)
7. [Type Aliases vs Newtypes](#7-type-aliases-vs-newtypes)
8. [Generics & Parametric Polymorphism](#8-generics--parametric-polymorphism)
9. [Pattern Matching & Destructuring](#9-pattern-matching--destructuring)
10. [Zero-Sized Types (ZST) in Rust](#10-zero-sized-types-zst-in-rust)
11. [Visibility & Encapsulation](#11-visibility--encapsulation)
12. [Memory Layout Deep Dive](#12-memory-layout-deep-dive)
13. [DSA-Specific Type Design Patterns](#13-dsa-specific-type-design-patterns)
14. [Comparative Summary Table](#14-comparative-summary-table)
15. [Expert Mental Models](#15-expert-mental-models)

---

## 1. Mental Model: What Are Types Really?

Before writing a single line, the expert asks: **"What shape does this data have?"**

Types are not just syntax — they encode **semantic constraints** about your data.

### Two Fundamental Shapes of Data

| Shape | Meaning | Mathematical Term | Example |
|-------|---------|-------------------|---------|
| **Product Type** | Has A **AND** B | Cartesian product | Struct, Tuple |
| **Sum Type** | Has A **OR** B (not both) | Disjoint union | Enum, Union |

This distinction is the foundation of **Algebraic Data Types (ADTs)** — the most powerful idea in type-system design.

```
Product: Person = (Name AND Age AND Height)
         Every Person has ALL THREE fields simultaneously.

Sum:     Shape = Circle OR Rectangle OR Triangle
         A Shape is EXACTLY ONE of these at any moment.
```

A `struct` models conjunction. An `enum` (in the Rust/ADT sense) models disjunction.

**Why this matters for DSA:** Almost every data structure is either a product (node with fields) or a sum (node is leaf OR branch OR null). Getting this right eliminates entire classes of bugs.

---

## 2. Structs — Product Types

A struct packs **named, heterogeneous fields** into a single compound value. All fields exist simultaneously.

---

### 2.1 C Structs

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Basic struct declaration */
struct Point {
    double x;
    double y;
};

/* Typedef to avoid writing 'struct' every time */
typedef struct {
    int32_t  id;
    char     name[64];
    double   score;
} Student;

/* Nested structs */
typedef struct {
    struct Point origin;
    double        radius;
} Circle;

/* Self-referential struct (used in linked lists, trees) */
typedef struct TreeNode {
    int               value;
    struct TreeNode  *left;
    struct TreeNode  *right;
} TreeNode;

/* Flexible array member (C99) — dynamically sized struct */
typedef struct {
    size_t length;
    int    data[];   /* Must be last field; size determined at alloc time */
} DynamicArray;

/* Bit fields — pack data tightly */
typedef struct {
    uint32_t red   : 5;
    uint32_t green : 6;
    uint32_t blue  : 5;
} RGB565;

/* Function pointers in struct — simulating methods / vtable */
typedef struct {
    int  id;
    char name[32];
    void (*print)(const void *self);   /* method pointer */
    int  (*compare)(const void *a, const void *b);
} Animal;

/* -------------------------------------------------------
   Initialization styles
------------------------------------------------------- */
void demo_initialization(void) {
    /* Designated initializers (C99) — preferred, order-independent */
    Student s1 = {
        .id    = 1,
        .score = 95.5,
        .name  = "Alice"
    };

    /* Positional (fragile — avoid in production) */
    struct Point p = {3.0, 4.0};

    /* Compound literals (C99) — create anonymous struct instance */
    Circle *c = &(Circle){ .origin = {0, 0}, .radius = 5.0 };

    /* Flexible array member allocation */
    size_t n = 10;
    DynamicArray *arr = malloc(sizeof(DynamicArray) + n * sizeof(int));
    arr->length = n;
    for (size_t i = 0; i < n; i++) arr->data[i] = (int)i;

    free(arr);
    (void)s1; (void)p; (void)c;
}

/* -------------------------------------------------------
   Passing structs: by value vs by pointer
   RULE: Small structs (≤ 2 machine words) → pass by value
         Large structs → pass by pointer
------------------------------------------------------- */
double distance_by_value(struct Point a, struct Point b) {
    /* Copies made — fine for 16-byte struct */
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return dx*dx + dy*dy; /* squared distance */
}

void scale_inplace(struct Point *p, double factor) {
    /* Mutate via pointer — no copy */
    p->x *= factor;
    p->y *= factor;
}

/* -------------------------------------------------------
   Linked list node — classic DSA struct
------------------------------------------------------- */
typedef struct ListNode {
    int              val;
    struct ListNode *next;
} ListNode;

ListNode *listnode_new(int val) {
    ListNode *node = malloc(sizeof(ListNode));
    if (!node) return NULL;
    node->val  = val;
    node->next = NULL;
    return node;
}
```

**Key C insights:**
- `struct` has NO methods, NO inheritance, NO access control.
- All fields are `public` — discipline is the only guard.
- Self-referential structs require the `struct Tag` name (typedef alone is insufficient because the typedef isn't complete yet when the struct body is parsed).
- Flexible array members let you allocate a struct and its variable-length payload in one `malloc` — critical for cache performance.

---

### 2.2 Go Structs

```go
package main

import (
	"fmt"
	"math"
)

// -------------------------------------------------------
// Basic struct
// -------------------------------------------------------
type Point struct {
	X float64
	Y float64
}

// Unexported (private) fields
type person struct {
	name string // unexported: only accessible within this package
	age  int
	ID   int // exported: accessible from other packages
}

// -------------------------------------------------------
// Methods on structs
// Value receiver — gets a COPY; use when struct is small and no mutation
// -------------------------------------------------------
func (p Point) Distance(other Point) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// Pointer receiver — mutates the original; use for large structs or mutation
func (p *Point) Scale(factor float64) {
	p.X *= factor
	p.Y *= factor
}

// String() implements fmt.Stringer interface automatically
func (p Point) String() string {
	return fmt.Sprintf("(%.2f, %.2f)", p.X, p.Y)
}

// -------------------------------------------------------
// Struct embedding — Go's mechanism for composition (NOT inheritance)
// -------------------------------------------------------
type Animal struct {
	Name string
	Age  int
}

func (a Animal) Speak() string {
	return fmt.Sprintf("I am %s", a.Name)
}

type Dog struct {
	Animal        // Embedded — fields and methods PROMOTED to Dog
	Breed  string
}

func (d Dog) Speak() string {
	// Override promoted method
	return fmt.Sprintf("Woof! I am %s, a %s", d.Name, d.Breed)
}

// -------------------------------------------------------
// Anonymous structs — inline, unnamed, one-off
// Extremely useful in tests, JSON decoding, table-driven tests
// -------------------------------------------------------
func anonymousDemo() {
	config := struct {
		Host string
		Port int
		TLS  bool
	}{
		Host: "localhost",
		Port: 8080,
		TLS:  true,
	}
	_ = config

	// Slice of anonymous structs — perfect for test tables
	tests := []struct {
		input    int
		expected int
	}{
		{2, 4},
		{3, 9},
		{4, 16},
	}
	for _, tt := range tests {
		got := tt.input * tt.input
		if got != tt.expected {
			fmt.Printf("FAIL: %d^2 = %d, want %d\n", tt.input, got, tt.expected)
		}
	}
}

// -------------------------------------------------------
// Struct tags — metadata for encoding, validation, ORM
// -------------------------------------------------------
type User struct {
	ID       int    `json:"id"        db:"user_id"   validate:"required"`
	Username string `json:"username"  db:"username"  validate:"min=3,max=32"`
	Email    string `json:"email"     db:"email"     validate:"email"`
	Password string `json:"-"`        // Excluded from JSON output
}

// -------------------------------------------------------
// Zero value — Go structs are always zero-initialized
// Design structs so the zero value is useful
// -------------------------------------------------------
type Buffer struct {
	data []byte
	pos  int
	// Zero value: data=nil, pos=0 — already valid, ready to use
}

func (b *Buffer) Write(p []byte) {
	b.data = append(b.data, p...)
}

// -------------------------------------------------------
// Constructor functions — idiomatic Go (no constructors in language)
// -------------------------------------------------------
type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

func NewTreeNode(val int) *TreeNode {
	return &TreeNode{Val: val}
}

// -------------------------------------------------------
// Comparable structs
// Structs are comparable with == if ALL fields are comparable
// -------------------------------------------------------
type Coordinate struct {
	Lat float64
	Lon float64
}

func comparableDemo() {
	a := Coordinate{1.0, 2.0}
	b := Coordinate{1.0, 2.0}
	fmt.Println(a == b) // true — structs support == when all fields do

	// Can be used as map keys!
	cache := map[Coordinate]string{
		{40.7128, -74.0060}: "New York",
	}
	_ = cache
}

func main() {
	p := Point{3, 4}
	q := Point{0, 0}
	fmt.Println(p.Distance(q)) // 5.0
	p.Scale(2)
	fmt.Println(p) // (6.00, 8.00)

	d := Dog{
		Animal: Animal{Name: "Rex", Age: 3},
		Breed:  "Labrador",
	}
	fmt.Println(d.Speak()) // overridden method
	fmt.Println(d.Age)     // promoted field — direct access

	anonymousDemo()
}
```

**Key Go insights:**
- Go has **no classes** — structs + methods + interfaces replace OOP.
- Embedding is **composition**, not inheritance. The embedded type's methods are *promoted* but can be overridden. The embedded type still exists as a named field.
- The **zero value principle** is one of Go's most elegant design choices. Design your types so `var x T` is already usable.
- **Value vs pointer receiver consistency**: if *any* method needs a pointer receiver (mutation or large struct), *all* methods should use pointer receivers for consistency.

---

### 2.3 Rust Structs

```rust
use std::fmt;

// -------------------------------------------------------
// Named-field struct
// -------------------------------------------------------
#[derive(Debug, Clone, PartialEq)]
struct Point {
    x: f64,
    y: f64,
}

// -------------------------------------------------------
// Tuple struct — positional fields, no names
// Best for newtypes and simple wrappers
// -------------------------------------------------------
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
struct Meters(f64);

#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
struct Seconds(f64);

// These two are DIFFERENT types even though both wrap f64.
// You CANNOT accidentally pass Meters where Seconds is expected.

// -------------------------------------------------------
// Unit struct — no fields, zero size
// Used as marker types, state tokens, ZSTs in generics
// -------------------------------------------------------
struct Locked;
struct Unlocked;

struct SafeBox<State> {
    contents: String,
    _state: std::marker::PhantomData<State>,
}

impl SafeBox<Locked> {
    fn new(contents: &str) -> Self {
        SafeBox {
            contents: contents.to_string(),
            _state: std::marker::PhantomData,
        }
    }
    fn unlock(self, _key: &str) -> SafeBox<Unlocked> {
        SafeBox { contents: self.contents, _state: std::marker::PhantomData }
    }
}

impl SafeBox<Unlocked> {
    fn get_contents(&self) -> &str {
        &self.contents
    }
    fn lock(self) -> SafeBox<Locked> {
        SafeBox { contents: self.contents, _state: std::marker::PhantomData }
    }
}
// This is the "typestate" pattern — illegal state transitions are
// compile-time errors, not runtime panics.

// -------------------------------------------------------
// Methods via impl blocks
// -------------------------------------------------------
impl Point {
    // Associated function (like static method) — no self
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }  // field shorthand when var name == field name
    }

    pub fn origin() -> Self {
        Point { x: 0.0, y: 0.0 }
    }

    // &self — immutable borrow (most common)
    pub fn distance(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    // &mut self — mutable borrow
    pub fn scale(&mut self, factor: f64) {
        self.x *= factor;
        self.y *= factor;
    }

    // self — consumes (takes ownership)
    pub fn translate(self, dx: f64, dy: f64) -> Self {
        Point { x: self.x + dx, y: self.y + dy }
    }

    // Builder pattern using method chaining (returns Self)
    pub fn with_x(mut self, x: f64) -> Self {
        self.x = x;
        self
    }
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.2}, {:.2})", self.x, self.y)
    }
}

// -------------------------------------------------------
// Struct update syntax
// -------------------------------------------------------
fn struct_update_demo() {
    let p1 = Point { x: 1.0, y: 2.0 };
    let p2 = Point { x: 5.0, ..p1 }; // copies y from p1
    println!("{:?}", p2); // Point { x: 5.0, y: 2.0 }
}

// -------------------------------------------------------
// Lifetimes in structs — when fields borrow external data
// -------------------------------------------------------
struct StringView<'a> {
    data: &'a str,
    start: usize,
    end: usize,
}

impl<'a> StringView<'a> {
    fn new(data: &'a str, start: usize, end: usize) -> Self {
        assert!(end <= data.len());
        StringView { data, start, end }
    }

    fn as_str(&self) -> &'a str {
        &self.data[self.start..self.end]
    }
}

// -------------------------------------------------------
// Self-referential via Box — linked list node
// -------------------------------------------------------
#[derive(Debug)]
struct ListNode {
    val: i32,
    next: Option<Box<ListNode>>,
}

impl ListNode {
    fn new(val: i32) -> Self {
        ListNode { val, next: None }
    }

    fn push(self, val: i32) -> Self {
        ListNode { val, next: Some(Box::new(self)) }
    }
}

fn main() {
    let mut p = Point::new(3.0, 4.0);
    println!("{}", p.distance(&Point::origin())); // 5.0
    p.scale(2.0);
    println!("{}", p); // (6.00, 8.00)

    let q = p.translate(1.0, 1.0); // p is consumed
    println!("{:?}", q);

    let list = ListNode::new(1).push(2).push(3);
    println!("{:?}", list);
}
```

---

### 2.4 Memory Layout & Padding

This is critical for performance-sensitive DSA work.

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

/* Rule: Each field is aligned to its own size.
   The struct size is padded to a multiple of the largest alignment. */

struct Bad {   // 12 bytes total (wasteful)
    char   a;  // offset 0, size 1
               // 3 bytes padding
    int    b;  // offset 4, size 4
    char   c;  // offset 8, size 1
               // 3 bytes padding
};             // total: 12

struct Good {  // 8 bytes total (optimal)
    int    b;  // offset 0, size 4
    char   a;  // offset 4, size 1
    char   c;  // offset 5, size 1
               // 2 bytes padding
};             // total: 8

void print_layout(void) {
    printf("Bad  size=%zu, b_offset=%zu\n",
           sizeof(struct Bad),  offsetof(struct Bad,  b));
    printf("Good size=%zu, b_offset=%zu\n",
           sizeof(struct Good), offsetof(struct Good, b));
}

/* Cache line awareness (64 bytes on x86):
   Fit hot fields in the first 64 bytes.
   Separate frequently-written fields onto different cache lines
   to avoid false sharing in concurrent programs. */

#define CACHE_LINE 64

typedef struct {
    /* Hot path — fits in one cache line */
    int32_t  key;
    int32_t  val;
    uint32_t hash;
    uint8_t  flags;
    uint8_t  _pad[3];
    /* ---- 16 bytes ---- */

    /* Cold path — rarely accessed */
    char    debug_name[48];
    /* ---- 64 bytes total ---- */
} __attribute__((aligned(CACHE_LINE))) CacheAlignedEntry;
```

```rust
// Rust: fields are NOT guaranteed to be in declaration order.
// The compiler may reorder for optimal alignment.
// Use repr(C) to guarantee C-compatible layout.

#[repr(C)]          // C-compatible: fields in declaration order
struct CStruct {
    a: u8,
    b: u32,
    c: u8,
}
// sizeof CStruct = 12 (with padding, just like C)

#[repr(packed)]     // Remove all padding — may cause unaligned accesses
struct Packed {
    a: u8,
    b: u32,
    c: u8,
}
// sizeof Packed = 6 — but accessing b may be slow (unaligned load)

#[repr(align(64))]  // Force cache-line alignment
struct HotData {
    counter: u64,
    _pad: [u8; 56],
}

// Default Rust layout: compiler reorders for minimal size
struct DefaultLayout {
    a: u8,   // might be placed after b
    b: u32,
    c: u8,
}
// sizeof DefaultLayout = 8 (a and c grouped together)
```

**Golden Rule for DSA:** When building cache-sensitive data structures (hash tables, B-trees, skip lists), always measure `sizeof` and use `offsetof`. A poor layout can triple cache miss rates.

---

### 2.5 Tuple Structs (Rust)

```rust
// Positional, not named. Like a named tuple.
struct Color(u8, u8, u8);
struct Matrix(f64, f64, f64, f64);

let c = Color(255, 0, 128);
let red = c.0;    // access by index

// Pattern destructuring
let Color(r, g, b) = c;

// Tuple structs with one field = "newtype"
struct Milliseconds(u64);
struct NodeId(u32);
```

---

### 2.6 Unit Structs (Rust)

```rust
// Zero bytes. Used as type-level tokens.
struct Marker;
struct PhantomVisitor;
struct Never; // represents impossible states

// Common use: HashMap<K, ()> as a HashSet
use std::collections::HashMap;
let mut set: HashMap<String, ()> = HashMap::new();
set.insert("key".to_string(), ());
```

---

### 2.7 Anonymous Structs

```go
// Go: anonymous struct — no name, declared inline
coord := struct{ Lat, Lon float64 }{Lat: 1.23, Lon: 4.56}

// Useful in tests — no need to pollute package namespace
```

```c
// C: anonymous struct INSIDE another struct
struct Outer {
    int x;
    struct {         // anonymous inner struct — fields promoted
        int y;
        int z;
    };
};

struct Outer o = {1, {2, 3}};
printf("%d %d %d\n", o.x, o.y, o.z); // direct access
```

---

### 2.8 Embedded / Promoted Fields (Go)

```go
type Address struct {
    Street string
    City   string
    Zip    string
}

type Employee struct {
    Name    string
    Address          // embedded — all Address fields promoted
    Salary  float64
}

func main() {
    e := Employee{
        Name:    "Bob",
        Address: Address{Street: "123 Main St", City: "NYC", Zip: "10001"},
        Salary:  90000,
    }

    // Access promoted fields directly — as if they were Employee's own
    fmt.Println(e.City)   // "NYC" — promoted from Address
    fmt.Println(e.Address.City) // also valid — explicit

    // IMPORTANT: embedding is NOT inheritance.
    // Employee is NOT an Address. You cannot pass an Employee
    // where an Address is expected.
    var addr Address = e.Address // explicit extraction — fine
    _ = addr
}

// Embedding interfaces — powerful for partial implementations
type ReadWriter interface {
    io.Reader  // embedded interface
    io.Writer
}
```

---

### 2.9 Struct Methods

```go
// Go: methods defined outside struct body, same package
type Stack[T any] struct {
    data []T
}

func (s *Stack[T]) Push(v T)     { s.data = append(s.data, v) }
func (s *Stack[T]) Pop() (T, bool) {
    if len(s.data) == 0 {
        var zero T
        return zero, false
    }
    n := len(s.data)
    v := s.data[n-1]
    s.data = s.data[:n-1]
    return v, true
}
func (s *Stack[T]) Len() int { return len(s.data) }
```

```rust
// Rust: methods in impl blocks, can have multiple impl blocks
struct Stack<T> {
    data: Vec<T>,
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Stack { data: Vec::new() }
    }
    pub fn push(&mut self, val: T) {
        self.data.push(val);
    }
    pub fn pop(&mut self) -> Option<T> {
        self.data.pop()
    }
    pub fn peek(&self) -> Option<&T> {
        self.data.last()
    }
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
    pub fn len(&self) -> usize {
        self.data.len()
    }
}

// Second impl block — allowed in Rust, useful for trait impls
impl<T: std::fmt::Debug> Stack<T> {
    pub fn debug_print(&self) {
        println!("{:?}", self.data);
    }
}
```

---

## 3. Enums — Sum Types / Tagged Unions

An enum says: **"This value is EXACTLY ONE of these variants."** Only one variant is active at any time.

---

### 3.1 C Enums

```c
#include <stdio.h>

/* Basic enum — just named integer constants */
typedef enum {
    DIRECTION_NORTH = 0,
    DIRECTION_EAST  = 1,
    DIRECTION_SOUTH = 2,
    DIRECTION_WEST  = 3,
} Direction;

/* Bitmask enum — powers of 2 for bitwise OR combining */
typedef enum {
    PERM_NONE    = 0,
    PERM_READ    = 1 << 0,  /* 0001 */
    PERM_WRITE   = 1 << 1,  /* 0010 */
    PERM_EXECUTE = 1 << 2,  /* 0100 */
    PERM_ALL     = PERM_READ | PERM_WRITE | PERM_EXECUTE
} Permission;

void check_perms(Permission p) {
    if (p & PERM_READ)    printf("can read\n");
    if (p & PERM_WRITE)   printf("can write\n");
    if (p & PERM_EXECUTE) printf("can execute\n");
}

/* C enums carry NO type safety:
   Direction d = 999; // valid C — compiler won't warn by default
   int x = DIRECTION_NORTH; // implicit int conversion
   These are just named ints. */

/* Enum as switch — exhaustiveness NOT enforced by C standard
   (GCC -Wswitch will warn about missing cases) */
const char *direction_name(Direction d) {
    switch (d) {
        case DIRECTION_NORTH: return "North";
        case DIRECTION_EAST:  return "East";
        case DIRECTION_SOUTH: return "South";
        case DIRECTION_WEST:  return "West";
        default:              return "Unknown"; /* C requires this */
    }
}
```

**C Enum Limitations:**
- No payload — a `Direction` cannot carry additional data.
- No exhaustiveness checking at compile time (without `-Wswitch`).
- Implicitly converts to `int` — no type safety.
- Variants share the enclosing scope (no namespacing).

---

### 3.2 Go Enums (iota pattern)

Go has no native `enum` keyword. The idiomatic pattern uses `const` + `iota`:

```go
package main

import "fmt"

// -------------------------------------------------------
// Basic iota enum
// -------------------------------------------------------
type Direction int

const (
    North Direction = iota // 0
    East                   // 1
    South                  // 2
    West                   // 3
)

func (d Direction) String() string {
    return [...]string{"North", "East", "South", "West"}[d]
}

// -------------------------------------------------------
// Bitmask enum with iota
// -------------------------------------------------------
type Permission uint8

const (
    PermRead    Permission = 1 << iota // 1
    PermWrite                          // 2
    PermExecute                        // 4
)

func (p Permission) String() string {
    s := ""
    if p&PermRead != 0    { s += "r" } else { s += "-" }
    if p&PermWrite != 0   { s += "w" } else { s += "-" }
    if p&PermExecute != 0 { s += "x" } else { s += "-" }
    return s
}

// -------------------------------------------------------
// iota with expressions — custom spacing
// -------------------------------------------------------
type ByteSize float64

const (
    _           = iota             // discard first iota value
    KB ByteSize = 1 << (10 * iota) // 1024
    MB                             // 1048576
    GB
    TB
)

// -------------------------------------------------------
// Sentinel / skip value
// -------------------------------------------------------
type Status int

const (
    StatusUnknown Status = iota
    StatusActive
    StatusInactive
    StatusDeleted

    statusCount // unexported sentinel — tracks count of valid statuses
)

func IsValid(s Status) bool {
    return s > StatusUnknown && s < statusCount
}

// -------------------------------------------------------
// Go enums CANNOT carry associated data.
// For variant-with-data, use interfaces + structs (sum types)
// -------------------------------------------------------
type Shape interface {
    Area() float64
    Perimeter() float64
}

type Circle struct{ Radius float64 }
type Rectangle struct{ Width, Height float64 }
type Triangle struct{ A, B, C float64 }

func (c Circle) Area() float64      { return 3.14159 * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * 3.14159 * c.Radius }

func (r Rectangle) Area() float64      { return r.Width * r.Height }
func (r Rectangle) Perimeter() float64 { return 2 * (r.Width + r.Height) }

// Type switch — Go's pattern matching equivalent
func describe(s Shape) string {
    switch v := s.(type) {
    case Circle:
        return fmt.Sprintf("Circle with radius %.2f, area %.2f", v.Radius, v.Area())
    case Rectangle:
        return fmt.Sprintf("Rectangle %.2fx%.2f", v.Width, v.Height)
    default:
        return "Unknown shape"
    }
}

func main() {
    fmt.Println(North, East, South, West)
    p := PermRead | PermExecute
    fmt.Println(p) // r-x

    shapes := []Shape{Circle{5}, Rectangle{3, 4}}
    for _, s := range shapes {
        fmt.Println(describe(s))
    }
}
```

**Go enum limitations:**
- `iota` enums cannot carry associated data per variant.
- No exhaustive matching (type switches have `default`, which is mandatory for safety).
- The interface + type switch pattern approximates sum types but is verbose and requires runtime type assertion.

---

### 3.3 Rust Enums (Algebraic Data Types)

Rust enums are the most powerful in any mainstream language — each variant can carry its own data.

```rust
// -------------------------------------------------------
// Basic C-like enum
// -------------------------------------------------------
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Direction {
    North,
    East,
    South,
    West,
}

impl Direction {
    fn opposite(self) -> Direction {
        match self {
            Direction::North => Direction::South,
            Direction::East  => Direction::West,
            Direction::South => Direction::North,
            Direction::West  => Direction::East,
        }
    }

    fn delta(self) -> (i32, i32) {
        match self {
            Direction::North => (0, 1),
            Direction::East  => (1, 0),
            Direction::South => (0, -1),
            Direction::West  => (-1, 0),
        }
    }
}

// -------------------------------------------------------
// Explicit discriminants (repr for C FFI)
// -------------------------------------------------------
#[repr(u8)]
enum HttpMethod {
    Get    = 0,
    Post   = 1,
    Put    = 2,
    Delete = 3,
}

// -------------------------------------------------------
// Enum as state machine
// -------------------------------------------------------
#[derive(Debug)]
enum TrafficLight {
    Red,
    Yellow,
    Green,
}

impl TrafficLight {
    fn next(&self) -> TrafficLight {
        match self {
            TrafficLight::Red    => TrafficLight::Green,
            TrafficLight::Green  => TrafficLight::Yellow,
            TrafficLight::Yellow => TrafficLight::Red,
        }
    }
    fn duration_secs(&self) -> u32 {
        match self {
            TrafficLight::Red    => 60,
            TrafficLight::Green  => 45,
            TrafficLight::Yellow => 5,
        }
    }
}
```

---

### 3.4 Enum with Data (Rust ADTs)

```rust
// -------------------------------------------------------
// Each variant has different data — true sum type
// -------------------------------------------------------
#[derive(Debug)]
enum Shape {
    Circle { radius: f64 },                  // named fields (struct variant)
    Rectangle { width: f64, height: f64 },
    Triangle(f64, f64, f64),                 // tuple variant (sides a, b, c)
    Point,                                   // unit variant (no data)
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius }         => std::f64::consts::PI * radius * radius,
            Shape::Rectangle { width, height } => width * height,
            Shape::Triangle(a, b, c)         => {
                let s = (a + b + c) / 2.0;
                (s * (s - a) * (s - b) * (s - c)).sqrt()
            },
            Shape::Point                     => 0.0,
        }
    }

    fn is_polygon(&self) -> bool {
        // matches! macro — ergonomic single-variant test
        matches!(self, Shape::Rectangle { .. } | Shape::Triangle(..))
    }
}

// -------------------------------------------------------
// Enum for recursive data structures — the idiomatic Rust way
// -------------------------------------------------------
#[derive(Debug)]
enum BinaryTree {
    Leaf,
    Node {
        val: i32,
        left:  Box<BinaryTree>,
        right: Box<BinaryTree>,
    }
}

impl BinaryTree {
    fn leaf() -> Self { BinaryTree::Leaf }

    fn node(val: i32, left: BinaryTree, right: BinaryTree) -> Self {
        BinaryTree::Node {
            val,
            left:  Box::new(left),
            right: Box::new(right),
        }
    }

    fn insert(self, new_val: i32) -> Self {
        match self {
            BinaryTree::Leaf => BinaryTree::node(new_val, BinaryTree::Leaf, BinaryTree::Leaf),
            BinaryTree::Node { val, left, right } => {
                if new_val < val {
                    BinaryTree::node(val, left.insert(new_val), *right)
                } else if new_val > val {
                    BinaryTree::node(val, *left, right.insert(new_val))
                } else {
                    BinaryTree::Node { val, left, right }
                }
            }
        }
    }

    fn contains(&self, target: i32) -> bool {
        match self {
            BinaryTree::Leaf => false,
            BinaryTree::Node { val, left, right } => {
                if target == *val { true }
                else if target < *val { left.contains(target) }
                else { right.contains(target) }
            }
        }
    }

    fn height(&self) -> usize {
        match self {
            BinaryTree::Leaf => 0,
            BinaryTree::Node { left, right, .. } => {
                1 + left.height().max(right.height())
            }
        }
    }
}

// -------------------------------------------------------
// Enum for expressions — classic ADT example
// -------------------------------------------------------
#[derive(Debug, Clone)]
enum Expr {
    Num(f64),
    Var(String),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
    Neg(Box<Expr>),
}

use std::collections::HashMap;

impl Expr {
    fn eval(&self, env: &HashMap<String, f64>) -> Result<f64, String> {
        match self {
            Expr::Num(n)    => Ok(*n),
            Expr::Var(name) => env.get(name).copied().ok_or_else(|| format!("Undefined: {}", name)),
            Expr::Add(a, b) => Ok(a.eval(env)? + b.eval(env)?),
            Expr::Mul(a, b) => Ok(a.eval(env)? * b.eval(env)?),
            Expr::Neg(e)    => Ok(-e.eval(env)?),
        }
    }
}
```

---

### 3.5 Option\<T\> and Result\<T, E\>

The two most important enums in Rust — study them as canonical ADT examples:

```rust
// The actual definitions in std:
// enum Option<T> { None, Some(T) }
// enum Result<T, E> { Ok(T), Err(E) }

fn divide(a: f64, b: f64) -> Option<f64> {
    if b == 0.0 { None } else { Some(a / b) }
}

fn parse_and_double(s: &str) -> Result<i32, std::num::ParseIntError> {
    let n: i32 = s.trim().parse()?; // ? propagates Err
    Ok(n * 2)
}

fn option_combinators() {
    let x: Option<i32> = Some(5);

    // map — transform Some value
    let doubled = x.map(|n| n * 2);         // Some(10)

    // and_then — flatMap (chain option-returning functions)
    let result = x.and_then(|n| if n > 3 { Some(n) } else { None });

    // unwrap_or — provide default
    let val = x.unwrap_or(0);

    // unwrap_or_else — lazy default
    let val2 = x.unwrap_or_else(|| expensive_computation());

    // ok_or — convert Option to Result
    let res: Result<i32, &str> = x.ok_or("no value");

    // filter — conditional
    let big = x.filter(|&n| n > 10); // None

    // ? in Option context (Rust 1.22+)
    fn inner() -> Option<i32> {
        let a = Some(5)?;  // returns None if None, unwraps if Some
        Some(a + 1)
    }

    fn expensive_computation() -> i32 { 42 }
    _ = (doubled, result, val, val2, res, big);
}

// Nested matching — if let for single-variant
fn if_let_demo() {
    let msg: Option<String> = Some("hello".to_string());

    if let Some(text) = msg {
        println!("Got: {}", text);
    }

    // while let
    let mut stack = vec![1, 2, 3];
    while let Some(top) = stack.pop() {
        println!("{}", top);
    }
}
```

---

## 4. Unions — Untagged / Raw Overlapping Memory

A union overlays all its fields at the **same memory address**. The size is the size of the largest field. You must track which field is valid yourself.

---

### 4.1 C Unions

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* All fields share the same memory address */
union Data {
    int32_t  i;
    float    f;
    uint8_t  bytes[4];
};

void union_demo(void) {
    union Data d;
    d.f = 3.14f;

    /* Reading d.i after writing d.f is "type punning" — implementation defined
       in C, but commonly used for bit manipulation */
    printf("float bits: %08X\n", (unsigned)d.i);

    /* Safe use: inspecting byte representation */
    for (int j = 0; j < 4; j++) {
        printf("byte[%d] = %02X\n", j, d.bytes[j]);
    }
}

/* Type punning the correct way in C99+ */
float int_to_float_bits(uint32_t bits) {
    float result;
    memcpy(&result, &bits, sizeof(float)); /* defined behavior */
    return result;
}

/* -------------------------------------------------------
   Anonymous union inside struct — common C pattern
------------------------------------------------------- */
typedef struct {
    int type; /* discriminant: 0=int, 1=float, 2=string */
    union {
        int    i_val;
        float  f_val;
        char   s_val[32];
    }; /* anonymous union — fields promoted */
} Variant;

void print_variant(const Variant *v) {
    switch (v->type) {
        case 0: printf("int: %d\n",   v->i_val); break;
        case 1: printf("float: %.2f\n", v->f_val); break;
        case 2: printf("string: %s\n",  v->s_val); break;
    }
}
```

---

### 4.2 Tagged Unions in C (manual)

This is exactly what Rust enums are — C forces you to do it manually:

```c
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef enum { TAG_INT, TAG_FLOAT, TAG_STR, TAG_NONE } Tag;

typedef struct {
    Tag tag;
    union {
        int    i;
        double d;
        struct { char *ptr; size_t len; } str;
    } data;
} Value;

Value value_int(int i)         { return (Value){ .tag=TAG_INT,   .data.i = i }; }
Value value_float(double d)    { return (Value){ .tag=TAG_FLOAT, .data.d = d }; }
Value value_none(void)         { return (Value){ .tag=TAG_NONE }; }
Value value_str(const char *s) {
    Value v = { .tag = TAG_STR };
    v.data.str.len = strlen(s);
    v.data.str.ptr = malloc(v.data.str.len + 1);
    strcpy(v.data.str.ptr, s);
    return v;
}

void value_print(const Value *v) {
    switch (v->tag) {
        case TAG_INT:   printf("%d\n",  v->data.i); break;
        case TAG_FLOAT: printf("%g\n",  v->data.d); break;
        case TAG_STR:   printf("%s\n",  v->data.str.ptr); break;
        case TAG_NONE:  printf("none\n"); break;
    }
}

void value_free(Value *v) {
    if (v->tag == TAG_STR) {
        free(v->data.str.ptr);
        v->data.str.ptr = NULL;
    }
}
```

This pattern — tag + union — is exactly what Rust compiles its `enum` to. Rust automates and type-checks this entire pattern.

---

### 4.3 Rust Unions (unsafe)

```rust
// Rust unions exist for C interop and low-level code.
// Unlike enums, they have no discriminant tag — accessing
// wrong field is undefined behavior.

#[repr(C)]
union FloatBits {
    float_val: f32,
    int_val:   u32,
    bytes:     [u8; 4],
}

fn float_to_bits(f: f32) -> u32 {
    let u = FloatBits { float_val: f };
    unsafe { u.int_val } // UNSAFE: we know float_val was written
}

// Better alternative: Rust standard library
fn float_to_bits_safe(f: f32) -> u32 {
    f.to_bits() // uses transmute internally, but wrapped safely
}

// Unions in C-compatible FFI structs
#[repr(C)]
union CVariant {
    int_data:   i32,
    float_data: f32,
}

#[repr(C)]
struct CTaggedVariant {
    tag:  u32,
    data: CVariant,
}
```

**Rule:** In Rust, always prefer `enum` over `union`. Use `union` only when:
1. Doing C FFI where the C API uses unions.
2. Implementing low-level primitives (atomics, SIMD, bit manipulation).

---

## 5. Interfaces & Traits — Behavioral Abstraction

Interfaces and traits define **what a type can do**, not what it is.

---

### 5.1 Go Interfaces

```go
package main

import (
	"fmt"
	"math"
)

// -------------------------------------------------------
// Interface declaration
// -------------------------------------------------------
type Shape interface {
    Area() float64
    Perimeter() float64
}

// Types implicitly implement interfaces — no "implements" keyword
type Circle struct{ Radius float64 }
type Rectangle struct{ W, H float64 }

func (c Circle)    Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle)    Perimeter() float64 { return 2 * math.Pi * c.Radius }
func (r Rectangle) Area() float64      { return r.W * r.H }
func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

// -------------------------------------------------------
// Interface as parameter — polymorphism
// -------------------------------------------------------
func TotalArea(shapes []Shape) float64 {
    total := 0.0
    for _, s := range shapes {
        total += s.Area()
    }
    return total
}

// -------------------------------------------------------
// Small, composable interfaces — Go philosophy
// io.Reader, io.Writer, io.Closer are the gold standard
// -------------------------------------------------------
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }
type ReadWriter interface {
    Reader
    Writer
}

// -------------------------------------------------------
// Empty interface — any value (pre-generics)
// -------------------------------------------------------
func PrintAny(v interface{}) {
    fmt.Printf("%T: %v\n", v, v)
}

// With generics (Go 1.18+) — better than interface{}
func Max[T interface{ ~int | ~float64 | ~string }](a, b T) T {
    if a > b { return a }
    return b
}

// -------------------------------------------------------
// Interface internals — (type pointer, value pointer)
// An interface is a fat pointer: 2 words
// Word 1: *itab (pointer to type + method table)
// Word 2: pointer to data (or data itself if ≤ 1 word)
// -------------------------------------------------------

// nil interface vs interface containing nil pointer — famous gotcha
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func badReturn() error {
    var p *MyError = nil
    return p // BUG: returns non-nil interface with nil concrete value!
    // The interface is {type=*MyError, value=nil} which is NOT == nil
}

func goodReturn() error {
    return nil // returns nil interface — both words zero
}

// -------------------------------------------------------
// Type assertion and type switch
// -------------------------------------------------------
func typeDemo(v interface{}) {
    // Type assertion — panics if wrong
    // n := v.(int)

    // Safe type assertion
    if n, ok := v.(int); ok {
        fmt.Println("int:", n)
    }

    // Type switch
    switch x := v.(type) {
    case int:     fmt.Println("int:", x)
    case string:  fmt.Println("string:", x)
    case Shape:   fmt.Println("area:", x.Area())
    default:      fmt.Printf("other: %T\n", x)
    }
}

// -------------------------------------------------------
// Stringer interface — fmt uses this automatically
// -------------------------------------------------------
type Color int
const (Red Color = iota; Green; Blue)

func (c Color) String() string {
    return [...]string{"Red", "Green", "Blue"}[c]
}

func main() {
    shapes := []Shape{Circle{5}, Rectangle{3, 4}}
    fmt.Println(TotalArea(shapes))
    fmt.Println(Red) // "Red" — uses String() method
}
```

---

### 5.2 Rust Traits

```rust
use std::fmt;

// -------------------------------------------------------
// Trait declaration — defines a contract
// -------------------------------------------------------
trait Shape {
    fn area(&self) -> f64;
    fn perimeter(&self) -> f64;

    // Default method — can be overridden
    fn describe(&self) -> String {
        format!("Shape with area {:.2}", self.area())
    }

    // Associated type — lets implementors specify their own types
    type Output;
    fn transform(&self) -> Self::Output;
}

// -------------------------------------------------------
// Trait implementation
// -------------------------------------------------------
struct Circle { radius: f64 }
struct Rectangle { width: f64, height: f64 }

impl Shape for Circle {
    type Output = Circle;

    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
    fn perimeter(&self) -> f64 {
        2.0 * std::f64::consts::PI * self.radius
    }
    fn transform(&self) -> Circle {
        Circle { radius: self.radius * 2.0 }
    }
}

impl Shape for Rectangle {
    type Output = Rectangle;

    fn area(&self) -> f64 { self.width * self.height }
    fn perimeter(&self) -> f64 { 2.0 * (self.width + self.height) }
    fn transform(&self) -> Rectangle {
        Rectangle { width: self.height, height: self.width }
    }
}

// -------------------------------------------------------
// Standard library traits — know these cold
// -------------------------------------------------------

// Display — human-readable formatting
impl fmt::Display for Circle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Circle(r={})", self.radius)
    }
}

// From / Into — type conversion
#[derive(Debug)]
struct Celsius(f64);
#[derive(Debug)]
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}
// From<T> automatically provides Into<U> — define From, get Into free

// Iterator trait — the most powerful in std
struct Counter { count: u32, max: u32 }

impl Iterator for Counter {
    type Item = u32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.count < self.max {
            self.count += 1;
            Some(self.count)
        } else {
            None
        }
    }
}
// Implementing Iterator gives you: map, filter, fold, take, skip,
// chain, zip, enumerate, collect, sum, product, min, max — FREE.

// Deref — transparent wrapper access
use std::ops::Deref;

struct MyBox<T>(T);

impl<T> Deref for MyBox<T> {
    type Target = T;
    fn deref(&self) -> &T { &self.0 }
}

// Drop — destructor
struct Resource { name: String }
impl Drop for Resource {
    fn drop(&mut self) {
        println!("Dropping: {}", self.name);
    }
}

// Clone and Copy — value semantics
// Copy: implicit bitwise copy (stack types: i32, bool, tuples of Copy)
// Clone: explicit deep copy (.clone())
// If a type contains heap data (Vec, String), it cannot be Copy.

// PartialEq / Eq — equality
// PartialOrd / Ord — ordering
// Hash — hashing
// Debug — debug formatting (can #[derive] all of these)
```

---

### 5.3 Trait Objects vs Generics (Static vs Dynamic Dispatch)

This is one of the most important performance decisions in Rust:

```rust
trait Drawable {
    fn draw(&self);
}

struct Canvas;
struct Button;
impl Drawable for Canvas { fn draw(&self) { println!("Draw canvas"); } }
impl Drawable for Button { fn draw(&self) { println!("Draw button"); } }

// -------------------------------------------------------
// STATIC DISPATCH — monomorphization (generics)
// Compiler generates a SEPARATE function for each concrete type.
// Zero overhead — direct function call, inlineable.
// Binary size grows. All types known at compile time.
// -------------------------------------------------------
fn draw_static<T: Drawable>(item: &T) {
    item.draw(); // direct call — no indirection
}

// With multiple trait bounds
fn draw_and_clone<T: Drawable + Clone>(item: &T) { item.draw(); }

// impl Trait syntax — syntactic sugar for generic bound
fn make_drawable(size: u32) -> impl Drawable {
    if size > 10 { Canvas } else { Canvas } // must return ONE type
    // Cannot return Canvas OR Button — that's dyn Trait territory
}

// -------------------------------------------------------
// DYNAMIC DISPATCH — trait objects (dyn Trait)
// Runtime vtable lookup. One function works for all types.
// Enables heterogeneous collections. Small overhead per call.
// Type erased — you lose concrete type info.
// -------------------------------------------------------
fn draw_dynamic(item: &dyn Drawable) {
    item.draw(); // vtable call — one level of indirection
}

// Heterogeneous collection — ONLY possible with dyn Trait
fn draw_all(items: &[Box<dyn Drawable>]) {
    for item in items { item.draw(); }
}

// Box<dyn Trait> internals: fat pointer = (data ptr, vtable ptr)
// vtable = {drop fn, size, align, method1, method2, ...}

// -------------------------------------------------------
// Object safety — not all traits can be made into trait objects
// A trait is object-safe if:
// 1. No generic methods (can't be in vtable)
// 2. No methods that return Self (size unknown)
// -------------------------------------------------------
trait ObjectSafe {           // CAN be dyn ObjectSafe
    fn do_thing(&self);
}

trait NotObjectSafe {        // CANNOT be dyn NotObjectSafe
    fn clone_self(&self) -> Self; // returns Self — size unknown
    fn generic<T>(&self, t: T);   // generic — can't monomorphize in vtable
}

// -------------------------------------------------------
// When to use which:
// Static:  performance-critical, homogeneous collections, library code
// Dynamic: GUI widgets, plugin systems, heterogeneous event handlers
// -------------------------------------------------------
```

---

### 5.4 Interface Composition (Go)

```go
// Build complex behaviors from small focused interfaces

type Stringer interface{ String() string }
type Sizer   interface{ Size() int }
type Closer  interface{ Close() error }

// Composed interface
type StringSizer interface {
    Stringer
    Sizer
}

// The famous io package pattern:
// io.Reader  = Read([]byte) (int, error)
// io.Writer  = Write([]byte) (int, error)
// io.Closer  = Close() error
// io.Seeker  = Seek(offset, whence) (int64, error)
//
// io.ReadWriter    = Reader + Writer
// io.ReadCloser    = Reader + Closer
// io.WriteCloser   = Writer + Closer
// io.ReadWriteCloser = all three
//
// This composability is the power of small interfaces.

// Satisfying multiple interfaces simultaneously
type File struct{ name string }
func (f *File) Read(p []byte) (int, error)  { return 0, nil }
func (f *File) Write(p []byte) (int, error) { return 0, nil }
func (f *File) Close() error                { return nil }
// File satisfies Reader, Writer, Closer, ReadWriter, WriteCloser, ReadWriteCloser
// without declaring any of them explicitly
```

---

### 5.5 Trait Bounds & Where Clauses

```rust
use std::fmt::{Display, Debug};

// Inline bounds — readable for simple cases
fn print_pair<T: Display + Debug>(a: T, b: T) {
    println!("{} {:?}", a, b);
}

// Where clause — readable for complex cases
fn complex_fn<T, U, V>(t: T, u: U) -> V
where
    T: Display + Clone + Into<V>,
    U: Debug + PartialEq,
    V: Default,
{
    println!("{} {:?}", t, u);
    t.into()
}

// Trait bounds on struct definitions
struct Pair<T> {
    first:  T,
    second: T,
}

impl<T: Display + PartialOrd> Pair<T> {
    // This method only exists when T: Display + PartialOrd
    fn cmp_display(&self) {
        if self.first >= self.second {
            println!("The largest member is first = {}", self.first);
        } else {
            println!("The largest member is second = {}", self.second);
        }
    }
}

// Conditional trait implementation
use std::fmt;
impl<T: Display> fmt::Display for Pair<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.first, self.second)
    }
}
```

---

### 5.6 Blanket Implementations

```rust
// Implement a trait for ALL types satisfying some bound.
// This is how ToString is implemented for all types that impl Display:

// In std:
// impl<T: Display> ToString for T {
//     fn to_string(&self) -> String {
//         format!("{}", self)
//     }
// }

// Custom blanket impl example
trait Summary {
    fn summarize(&self) -> String;
}

trait Printable: Summary {
    fn print(&self) { println!("{}", self.summarize()); }
}

// Blanket: every type that implements Summary gets Printable for free
impl<T: Summary> Printable for T {}

struct Article { title: String }
impl Summary for Article {
    fn summarize(&self) -> String { self.title.clone() }
}
// Article now automatically has .print() — without explicitly implementing Printable
```

---

## 6. Newtype Pattern

Wrap a primitive or existing type in a struct with one field to:
1. Add type safety (prevent units confusion).
2. Implement external traits on external types (orphan rule workaround).
3. Restrict or extend an API.

```rust
// -------------------------------------------------------
// Type safety for units
// -------------------------------------------------------
struct Meters(f64);
struct Seconds(f64);
struct MetersPerSecond(f64);

fn velocity(distance: Meters, time: Seconds) -> MetersPerSecond {
    MetersPerSecond(distance.0 / time.0)
}

// This compiles:
let v = velocity(Meters(100.0), Seconds(9.58));

// This doesn't compile — type error caught at compile time:
// let v = velocity(Seconds(9.58), Meters(100.0)); // ERROR!

// -------------------------------------------------------
// Orphan rule workaround
// You cannot implement external trait for external type:
// impl Display for Vec<i32> { ... } — FORBIDDEN
//
// But you can wrap it:
// -------------------------------------------------------
use std::fmt;

struct Wrapper(Vec<String>);

impl fmt::Display for Wrapper {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}

// -------------------------------------------------------
// Restricting an API
// -------------------------------------------------------
struct NonZero(u32);
impl NonZero {
    pub fn new(n: u32) -> Option<NonZero> {
        if n != 0 { Some(NonZero(n)) } else { None }
    }
    pub fn get(self) -> u32 { self.0 }
}
// Invariant "never zero" is enforced by type — no runtime check needed later.

// -------------------------------------------------------
// Go newtype via type alias with methods
// -------------------------------------------------------
// In Go, a "newtype" is declared with `type NewName OldType`
// type Celsius float64
// type Fahrenheit float64
// These are distinct types — you CANNOT assign one to the other without conversion.
```

```go
type Celsius float64
type Fahrenheit float64

func CToF(c Celsius) Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}

// This won't compile:
// var c Celsius = 100
// var f Fahrenheit = c // ERROR: cannot use Celsius as Fahrenheit
```

---

## 7. Type Aliases vs Newtypes

| Feature | Type Alias | Newtype |
|---------|-----------|---------|
| Creates new type? | No | Yes |
| Interchangeable with original? | Yes | No (requires conversion) |
| Can add methods? | No (in most languages) | Yes |
| Type safety | None | Strong |
| Zero cost? | Yes | Yes |

```rust
// Type alias — just another name, interchangeable
type Meters = f64;
type Kilometers = f64;

let m: Meters = 5.0;
let k: Kilometers = m; // COMPILES — they're the same type!

// Newtype — genuinely distinct
struct MetersN(f64);
struct KilometersN(f64);

let mn = MetersN(5.0);
// let kn: KilometersN = mn; // ERROR — incompatible types
```

```go
// Go type alias (=): truly the same type
type MyInt = int // alias — identical to int

// Go defined type (no =): distinct type
type MyInt2 int // new type — not assignable to int without conversion

var a int    = 5
var b MyInt  = a  // fine — alias
// var c MyInt2 = a // ERROR: cannot use int as MyInt2
var d MyInt2 = MyInt2(a) // fine — explicit conversion
```

---

## 8. Generics & Parametric Polymorphism

```rust
// -------------------------------------------------------
// Generic struct
// -------------------------------------------------------
#[derive(Debug)]
struct Stack<T> {
    data: Vec<T>,
}

impl<T> Stack<T> {
    fn new() -> Self { Stack { data: Vec::new() } }
    fn push(&mut self, v: T) { self.data.push(v); }
    fn pop(&mut self) -> Option<T> { self.data.pop() }
}

// -------------------------------------------------------
// Generic enum
// -------------------------------------------------------
#[derive(Debug)]
enum Either<L, R> {
    Left(L),
    Right(R),
}

impl<L: fmt::Display, R: fmt::Display> fmt::Display for Either<L, R> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Either::Left(l)  => write!(f, "Left({})", l),
            Either::Right(r) => write!(f, "Right({})", r),
        }
    }
}

// -------------------------------------------------------
// Generic function with multiple bounds
// -------------------------------------------------------
fn largest<T: PartialOrd + Copy>(list: &[T]) -> T {
    let mut largest = list[0];
    for &item in list {
        if item > largest { largest = item; }
    }
    largest
}

// -------------------------------------------------------
// Const generics — size known at compile time
// -------------------------------------------------------
struct Matrix<T, const ROWS: usize, const COLS: usize> {
    data: [[T; COLS]; ROWS],
}

impl<T: Default + Copy, const R: usize, const C: usize> Matrix<T, R, C> {
    fn zeros() -> Self {
        Matrix { data: [[T::default(); C]; R] }
    }
    fn get(&self, row: usize, col: usize) -> T {
        self.data[row][col]
    }
}

type Matrix3x3 = Matrix<f64, 3, 3>;

// -------------------------------------------------------
// Go generics (1.18+)
// -------------------------------------------------------
```

```go
// Go generics with type constraints
import "golang.org/x/exp/constraints"

type Number interface {
    constraints.Integer | constraints.Float
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

// Generic stack
type Stack[T any] struct {
    data []T
}

func (s *Stack[T]) Push(v T) { s.data = append(s.data, v) }
func (s *Stack[T]) Pop() (T, bool) {
    if len(s.data) == 0 {
        var zero T
        return zero, false
    }
    n := len(s.data) - 1
    v := s.data[n]
    s.data = s.data[:n]
    return v, true
}

// Generic binary search tree
type BST[T constraints.Ordered] struct {
    val         T
    left, right *BST[T]
}

func (t *BST[T]) Insert(v T) *BST[T] {
    if t == nil { return &BST[T]{val: v} }
    if v < t.val      { t.left  = t.left.Insert(v) }
    else if v > t.val { t.right = t.right.Insert(v) }
    return t
}
```

---

## 9. Pattern Matching & Destructuring

Pattern matching is how you consume enums (and structs). Master it.

```rust
// -------------------------------------------------------
// Match exhaustiveness — compiler ensures all cases handled
// -------------------------------------------------------
#[derive(Debug)]
enum Coin { Penny, Nickel, Dime, Quarter(String) }

fn value_in_cents(coin: &Coin) -> u32 {
    match coin {
        Coin::Penny           => 1,
        Coin::Nickel          => 5,
        Coin::Dime            => 10,
        Coin::Quarter(state)  => {
            println!("State quarter from {}", state);
            25
        },
    }
    // Forgetting any variant is a COMPILE ERROR. This is why enums
    // are better than int constants for sum types.
}

// -------------------------------------------------------
// Guards — match arm conditions
// -------------------------------------------------------
fn classify(n: i32) -> &'static str {
    match n {
        i32::MIN..=-1       => "negative",
        0                   => "zero",
        1..=9               => "single digit",
        n if n % 2 == 0     => "large even",
        _                   => "large odd",
    }
}

// -------------------------------------------------------
// Struct destructuring
// -------------------------------------------------------
struct Point { x: i32, y: i32 }

let p = Point { x: 3, y: -5 };
let Point { x, y } = p;          // bind x=3, y=-5
let Point { x: a, y: b } = p;    // renamed: a=3, b=-5
let Point { x, .. } = p;         // ignore y with ..

// -------------------------------------------------------
// Tuple destructuring
// -------------------------------------------------------
let (a, b, c) = (1, "hello", 3.14);
let (first, .., last) = (1, 2, 3, 4, 5); // first=1, last=5

// -------------------------------------------------------
// Nested pattern matching
// -------------------------------------------------------
#[derive(Debug)]
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}

fn process(msg: Message) {
    match msg {
        Message::Quit => println!("quit"),
        Message::Move { x, y } => println!("move to ({},{})", x, y),
        Message::Write(text) => println!("write: {}", text),
        Message::ChangeColor(r, g, b) => println!("color: {},{},{}", r, g, b),
    }
}

// -------------------------------------------------------
// @ bindings — bind AND test
// -------------------------------------------------------
fn describe_point(x: i32, y: i32) {
    match (x, y) {
        (0, 0) => println!("origin"),
        (x @ 1..=10, 0) => println!("on x-axis, small x={}", x),
        (0, y @ 1..=10) => println!("on y-axis, small y={}", y),
        (x, y) => println!("general ({},{})", x, y),
    }
}

// -------------------------------------------------------
// Matching references
// -------------------------------------------------------
let vals = vec![1, 2, 3, 4, 5];
for &v in &vals {        // & pattern — automatically dereferences
    print!("{} ", v);
}

// -------------------------------------------------------
// Matches! macro — quick single-pattern boolean test
// -------------------------------------------------------
let opt: Option<i32> = Some(42);
assert!(matches!(opt, Some(x) if x > 0));
```

```go
// Go pattern matching via type switch + switch statement

func processValue(v interface{}) {
    switch val := v.(type) {
    case int:
        switch {
        case val < 0:    fmt.Println("negative int")
        case val == 0:   fmt.Println("zero")
        default:         fmt.Println("positive int:", val)
        }
    case string:
        if len(val) == 0 { fmt.Println("empty string") } else { fmt.Println("string:", val) }
    case []int:
        fmt.Println("int slice, len:", len(val))
    case nil:
        fmt.Println("nil")
    default:
        fmt.Printf("unknown type: %T\n", val)
    }
}
```

---

## 10. Zero-Sized Types (ZST) in Rust

```rust
// Zero-sized types occupy ZERO bytes at runtime.
// They are purely compile-time constructs.

use std::marker::PhantomData;

// Unit struct — ZST
struct Token;
assert_eq!(std::mem::size_of::<Token>(), 0);

// PhantomData — carry type information without data
struct TypedId<T> {
    id: u64,
    _marker: PhantomData<T>, // T is a compile-time phantom
}

struct User;
struct Post;

type UserId = TypedId<User>;
type PostId = TypedId<Post>;

fn get_user(id: UserId) { /* ... */ }

let user_id = TypedId::<User> { id: 1, _marker: PhantomData };
let post_id = TypedId::<Post> { id: 1, _marker: PhantomData };

// get_user(post_id); // COMPILE ERROR — type mismatch

// -------------------------------------------------------
// ZST in collections — no allocation
// -------------------------------------------------------
use std::collections::HashMap;
let mut set: HashMap<String, ()> = HashMap::new();
// () is a ZST — HashMap<K, ()> is essentially a HashSet<K>
// The value slot occupies ZERO bytes — same memory as a hash array alone.

// -------------------------------------------------------
// Typestate pattern with ZSTs
// -------------------------------------------------------
struct Connected;
struct Disconnected;

struct Connection<State> {
    host: String,
    _state: PhantomData<State>,
}

impl Connection<Disconnected> {
    fn new(host: &str) -> Self {
        Connection { host: host.to_string(), _state: PhantomData }
    }
    fn connect(self) -> Connection<Connected> {
        // perform connection...
        Connection { host: self.host, _state: PhantomData }
    }
}

impl Connection<Connected> {
    fn send(&self, data: &[u8]) { /* ... */ }
    fn disconnect(self) -> Connection<Disconnected> {
        Connection { host: self.host, _state: PhantomData }
    }
}

// Can't call send() on a disconnected connection — compile-time enforcement.
```

---

## 11. Visibility & Encapsulation

```rust
// Rust visibility rules
pub struct Public;           // visible everywhere
struct Private;              // visible in this module only
pub(crate) struct CrateWide; // visible within the crate
pub(super) struct ParentMod; // visible in parent module

pub struct BankAccount {
    owner:   String,  // private field
    pub id:  u64,     // public field (unusual — prefer methods)
    balance: f64,     // private field
}

impl BankAccount {
    pub fn new(owner: &str, id: u64) -> Self {
        BankAccount { owner: owner.to_string(), id, balance: 0.0 }
    }
    pub fn deposit(&mut self, amount: f64) {
        assert!(amount > 0.0);
        self.balance += amount;
    }
    pub fn balance(&self) -> f64 { self.balance }
    // balance is readable but not writable from outside — only through deposit/withdraw
}
```

```go
// Go visibility: Exported = starts with uppercase; unexported = lowercase

package account

type BankAccount struct {
    ID      int     // exported
    owner   string  // unexported
    balance float64 // unexported
}

func New(id int, owner string) *BankAccount {
    return &BankAccount{ID: id, owner: owner}
}

func (a *BankAccount) Deposit(amount float64) error {
    if amount <= 0 { return errors.New("amount must be positive") }
    a.balance += amount
    return nil
}

func (a *BankAccount) Balance() float64 { return a.balance }
```

```c
/* C has no language-level encapsulation.
   Convention: use opaque pointer pattern for encapsulation */

/* account.h */
typedef struct Account Account; /* incomplete type — size hidden */
Account *account_new(int id, const char *owner);
int      account_deposit(Account *a, double amount);
double   account_balance(const Account *a);
void     account_free(Account *a);

/* account.c */
struct Account {       /* definition only in .c file */
    int    id;
    char   owner[64];
    double balance;
};
```

---

## 12. Memory Layout Deep Dive

```c
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>

/* Complete memory layout analysis */
struct Node {
    int      val;       // offset 0,  size 4
                        // padding:   4 bytes (to align next pointer to 8)
    struct Node *left;  // offset 8,  size 8
    struct Node *right; // offset 16, size 8
};                      // total: 24 bytes

/* Introspect at runtime */
void print_node_layout(void) {
    printf("sizeof(Node)      = %zu\n", sizeof(struct Node));
    printf("offsetof val      = %zu\n", offsetof(struct Node, val));
    printf("offsetof left     = %zu\n", offsetof(struct Node, left));
    printf("offsetof right    = %zu\n", offsetof(struct Node, right));
}

/* -------------------------------------------------------
   Struct of Arrays (SoA) vs Array of Structs (AoS)
   Critical for SIMD and cache performance in DSA
------------------------------------------------------- */

/* AoS — each particle is packed together */
typedef struct {
    float x, y, z;     /* position */
    float vx, vy, vz;  /* velocity */
    float mass;
} ParticleAoS;

ParticleAoS particles_aos[1000];

/* SoA — each field is a contiguous array */
typedef struct {
    float x[1000], y[1000], z[1000];
    float vx[1000], vy[1000], vz[1000];
    float mass[1000];
} ParticlesSoA;

ParticlesSoA particles_soa;

/*
   If you only update positions (x,y,z):
   AoS: loads 28 bytes per particle, uses only 12 (43% utilization)
   SoA: loads 48 bytes of pure x data — 100% cache utilization

   SoA is often 2-4x faster for batch operations on single fields.
   Use AoS when you access all fields together per element.
   Use SoA when you batch-process single fields (physics, ML, graphics).
*/
```

```rust
use std::mem;

fn memory_analysis() {
    // Rust default: reorders fields for minimum size
    struct Inefficient { a: u8, b: u64, c: u8 }  // 24 bytes default
    struct Efficient   { b: u64, a: u8, c: u8 }  // 16 bytes

    println!("Inefficient: {}", mem::size_of::<Inefficient>());
    println!("Efficient:   {}", mem::size_of::<Efficient>());

    // Enum discriminant size
    enum SmallEnum { A, B, C }    // 1 byte (fits in u8)
    enum LargeEnum { A(u64), B }  // 16 bytes (u64 payload + discriminant + padding)

    // Niche optimization — Rust can encode None/Some in the pointer itself
    // Option<Box<T>> is same size as Box<T>:
    println!("Box<i32>        = {}", mem::size_of::<Box<i32>>());
    println!("Option<Box<i32>>= {}", mem::size_of::<Option<Box<i32>>>());
    // Both = 8 bytes! None = null pointer, Some(p) = non-null pointer.
    // No extra byte needed for discriminant.
}
```

---

## 13. DSA-Specific Type Design Patterns

### Pattern 1: Recursive Enum (Tree)

```rust
#[derive(Debug, Clone)]
pub enum AVLTree {
    Empty,
    Node(Box<AVLNode>),
}

#[derive(Debug, Clone)]
pub struct AVLNode {
    pub key:    i32,
    pub height: i32,
    pub left:   AVLTree,
    pub right:  AVLTree,
}

impl AVLTree {
    pub fn height(&self) -> i32 {
        match self {
            AVLTree::Empty => 0,
            AVLTree::Node(n) => n.height,
        }
    }

    pub fn balance_factor(&self) -> i32 {
        match self {
            AVLTree::Empty => 0,
            AVLTree::Node(n) => n.left.height() - n.right.height(),
        }
    }
}
```

### Pattern 2: Graph as Adjacency List (Vec of Vecs)

```rust
pub struct Graph {
    adj: Vec<Vec<usize>>,
    weighted: Vec<Vec<(usize, i64)>>,
}

impl Graph {
    pub fn new(n: usize) -> Self {
        Graph {
            adj:      vec![vec![]; n],
            weighted: vec![vec![]; n],
        }
    }
    pub fn add_edge(&mut self, u: usize, v: usize) {
        self.adj[u].push(v);
        self.adj[v].push(u);
    }
    pub fn add_weighted_edge(&mut self, u: usize, v: usize, w: i64) {
        self.weighted[u].push((v, w));
        self.weighted[v].push((u, w));
    }
    pub fn neighbors(&self, u: usize) -> &[usize] {
        &self.adj[u]
    }
}
```

```go
// Go: Graph with adjacency list
type Graph struct {
    adj      [][]int
    weighted [][]struct{ to, w int }
}

func NewGraph(n int) *Graph {
    return &Graph{
        adj:      make([][]int, n),
        weighted: make([][]struct{ to, w int }, n),
    }
}
```

### Pattern 3: Union-Find (Disjoint Set Union) with structs

```rust
pub struct DSU {
    parent: Vec<usize>,
    rank:   Vec<u32>,
    size:   Vec<usize>,
    components: usize,
}

impl DSU {
    pub fn new(n: usize) -> Self {
        DSU {
            parent:     (0..n).collect(),
            rank:       vec![0; n],
            size:       vec![1; n],
            components: n,
        }
    }

    pub fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // path compression
        }
        self.parent[x]
    }

    pub fn union(&mut self, x: usize, y: usize) -> bool {
        let rx = self.find(x);
        let ry = self.find(y);
        if rx == ry { return false; }
        // Union by rank
        match self.rank[rx].cmp(&self.rank[ry]) {
            std::cmp::Ordering::Less    => self.parent[rx] = ry,
            std::cmp::Ordering::Greater => self.parent[ry] = rx,
            std::cmp::Ordering::Equal   => {
                self.parent[ry] = rx;
                self.rank[rx]  += 1;
            }
        }
        let (srx, sry) = (self.size[rx], self.size[ry]);
        let root = self.find(x);
        self.size[root] = srx + sry;
        self.components -= 1;
        true
    }

    pub fn connected(&mut self, x: usize, y: usize) -> bool {
        self.find(x) == self.find(y)
    }

    pub fn component_size(&mut self, x: usize) -> usize {
        let r = self.find(x);
        self.size[r]
    }
}
```

### Pattern 4: State Machine via Enum

```rust
#[derive(Debug, PartialEq)]
enum LexerState {
    Start,
    InNumber,
    InIdentifier,
    InString { escaped: bool },
    LineComment,
    BlockComment { depth: u32 },
    Done,
}

struct Lexer {
    state:  LexerState,
    buffer: String,
    tokens: Vec<String>,
}

impl Lexer {
    fn new() -> Self {
        Lexer { state: LexerState::Start, buffer: String::new(), tokens: Vec::new() }
    }

    fn feed(&mut self, ch: char) {
        match (&self.state, ch) {
            (LexerState::Start, '0'..='9') => {
                self.state = LexerState::InNumber;
                self.buffer.push(ch);
            }
            (LexerState::InNumber, '0'..='9') => {
                self.buffer.push(ch);
            }
            (LexerState::InNumber, _) => {
                let tok = std::mem::take(&mut self.buffer);
                self.tokens.push(tok);
                self.state = LexerState::Start;
            }
            _ => {} // other transitions
        }
    }
}
```

### Pattern 5: Generic BinaryHeap wrapper

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

// Max-heap (default)
let mut max_heap: BinaryHeap<i32> = BinaryHeap::new();
max_heap.push(3);
max_heap.push(1);
max_heap.push(4);
println!("{:?}", max_heap.pop()); // Some(4)

// Min-heap via Reverse wrapper — newtype pattern in action!
let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
min_heap.push(Reverse(3));
min_heap.push(Reverse(1));
min_heap.push(Reverse(4));
println!("{:?}", min_heap.pop()); // Some(Reverse(1))

// Custom priority — Dijkstra's algorithm
#[derive(Eq, PartialEq)]
struct State { cost: u32, node: usize }

impl Ord for State {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        other.cost.cmp(&self.cost) // reverse: min cost has highest priority
            .then_with(|| self.node.cmp(&other.node))
    }
}

impl PartialOrd for State {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
```

---

## 14. Comparative Summary Table

| Feature | C | Go | Rust |
|---------|---|----|----|
| **Named struct** | `struct` | `struct` | `struct` |
| **Tuple struct** | via typedef | No | Yes |
| **Unit struct** | Empty struct (1 byte) | `struct{}` (0 bytes) | Yes (0 bytes) |
| **Enum with data** | Manual tagged union | Interface+type switch | Native (ADT) |
| **Sum types** | Manual | Interface pattern | Native enum |
| **Union** | `union` | No | `union` (unsafe) |
| **Interface/Trait** | Function pointers | `interface` | `trait` |
| **Impl. interface** | Manual vtable | Implicit | Explicit `impl` |
| **Static dispatch** | N/A | No | Generics (`<T: Trait>`) |
| **Dynamic dispatch** | Function pointers | Always for interfaces | `dyn Trait` |
| **Pattern matching** | switch (partial) | switch (partial) | `match` (exhaustive) |
| **Memory layout** | Predictable (C order) | Opaque | Optimized (reorder) |
| **repr(C)** | Default | N/A | `#[repr(C)]` |
| **Newtype** | typedef (unsafe) | `type New Old` | `struct New(Old)` |
| **Type alias** | `typedef` | `type New = Old` | `type New = Old` |
| **Generics** | Macros/void* | Yes (1.18+) | Yes (monomorphized) |
| **Access control** | None | Package-level | Module-level |
| **Methods** | None (function ptr) | On any type | `impl` blocks |
| **Embedding** | Anonymous struct/union | Type embedding | Via Deref/traits |
| **Exhaustiveness** | No (`-Wswitch`) | No | Yes (compiler) |

---

## 15. Expert Mental Models

### Mental Model 1: "What shape is my data?"

Before writing any type:
1. Is it A **AND** B **AND** C → **struct/product type**
2. Is it A **OR** B **OR** C → **enum/sum type**
3. Is it behavior without data → **trait/interface**
4. Is it the same type but semantically different → **newtype**
5. Is it two types sharing raw memory → **union** (rarely)

### Mental Model 2: The "Can I forget a case?" Test

If you represent a state machine or variant as an int or string, you can forget to handle a case. If you represent it as an enum (Rust) or interface (Go), the compiler either forces exhaustion (Rust `match`) or you discover the gap at runtime. **Always choose the representation that makes wrong states unrepresentable.**

### Mental Model 3: Dispatch Cost Ladder

```
Zero cost:
  Direct function call (no virtual)
  Monomorphized generics (Rust)

Tiny cost (~1 ns):
  Virtual dispatch (vtable lookup)
  Go interface call
  Rust dyn Trait

Noticeable cost:
  HashMap<TypeId, Box<dyn Fn>>
  Dynamic plugin loading
```

**Default to static dispatch. Use dynamic dispatch only when you genuinely need a heterogeneous collection or runtime-determined type.**

### Mental Model 4: The Ownership Lens (Rust)

Every struct field has one owner. When designing a struct, ask:
- Does this field **own** the data → `T` or `Box<T>`
- Does this field **borrow** data → `&'a T` or `&'a mut T`
- Is this field **shared and reference-counted** → `Rc<T>` or `Arc<T>`
- Can this field **be absent** → `Option<T>`

This classification drives the entire design before you write one method.

### Mental Model 5: Zero-Cost Abstraction Verification

Rust's generics, newtypes, ZSTs, and PhantomData all compile to the same machine code as the equivalent hand-written code. **Abstraction should cost nothing at runtime** — only compile time. If you see a trait object where a generic would work, you're paying a vtable tax unnecessarily.

### Mental Model 6: The "Struct-as-Type-State" Pattern

The most powerful use of struct + phantom data is encoding **valid transitions** in the type system. A `Connection<Connected>` and `Connection<Disconnected>` are different types. You cannot call `.send()` on a disconnected one. The runtime cost is zero — the state token has zero size. The benefit is: **impossible operations become compilation errors.**

### Mental Model 7: Chunking Complex Types

When you encounter a complex type system problem:
1. **Chunk** it: identify the atomic types first (leaves of the type tree).
2. **Compose** them: which are products? Which are sums?
3. **Add behavior**: what operations each type supports → traits/interfaces.
4. **Add constraints**: what invariants must always hold → encode in the type, not runtime checks.

This bottom-up decomposition mirrors how expert designers approach domain modeling. The goal is a type system so expressive that **if the code compiles, the business logic is largely correct.**

---

*"A language that doesn't affect the way you think about programming is not worth knowing."*
*— Alan Perlis*

*In Rust, the type system teaches you to think about ownership, lifetimes, and state. In Go, it teaches you to think about interfaces and composition. In C, it teaches you to think about memory directly. Master all three — and you will think in dimensions most programmers cannot see.*

Here's what's covered in the guide — organized around one core idea: **every type is either a product (AND), a sum (OR), a behavior (interface/trait), or a wrapper (newtype)**. Everything else derives from that.

**What the guide covers:**

The progression is deliberate — it moves from raw memory (C structs, C unions) → behavioral abstraction (Go interfaces, Rust traits) → type-system expressiveness (ADTs, typestate, ZSTs, newtypes, generics). Each concept is shown in all three languages simultaneously so you can see the *same idea* at different levels of safety and expressiveness.

**Key concepts to study deeply:**

- **Tagged unions**: C forces you to do it manually. Rust automates the exact same pattern with `enum`. Understanding C's version first makes Rust's seem obvious.
- **Static vs dynamic dispatch**: The difference between `<T: Trait>` and `dyn Trait` is monomorphization vs vtable. This is one of the most important performance decisions in any Rust codebase.
- **Typestate pattern**: Using ZSTs + PhantomData to encode valid state transitions as *type errors* — impossible operations become compile errors, not runtime panics. This is the pinnacle of the "make invalid states unrepresentable" principle.
- **Niche optimization**: `Option<Box<T>>` is the same size as `Box<T>` — Rust encodes `None` as the null pointer. Understanding this explains why Rust's enums are truly zero-cost.

**The mental model to internalize first** — before everything else: *What shape is my data?* AND → struct. OR → enum. Behavior → trait. Same-but-distinct → newtype. That single question, asked consistently, will guide 90% of your type design decisions correctly.