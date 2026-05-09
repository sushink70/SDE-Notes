# 🐹 Golang Interview Questions — Complete In-Depth Guide
> *"Simplicity is the ultimate sophistication." — Rob Pike (Go co-creator)*

---

## TABLE OF CONTENTS

1. [What is Go? Philosophy & Design](#1-what-is-go)
2. [Go Program Structure & Entry Point](#2-go-program-structure)
3. [Variables, Constants & Types](#3-variables-constants--types)
4. [Zero Values — Go's Unique Guarantee](#4-zero-values)
5. [Type System — Static & Strong Typing](#5-type-system)
6. [Control Flow — if, for, switch](#6-control-flow)
7. [Functions — First-Class Citizens](#7-functions)
8. [Pointers — Memory Addresses](#8-pointers)
9. [Arrays vs Slices — The Deep Difference](#9-arrays-vs-slices)
10. [Maps — Hash Tables in Go](#10-maps)
11. [Structs — Custom Data Types](#11-structs)
12. [Methods — Behavior on Types](#12-methods)
13. [Interfaces — Implicit Contracts](#13-interfaces)
14. [Error Handling — Go's Philosophy](#14-error-handling)
15. [Goroutines — Lightweight Threads](#15-goroutines)
16. [Channels — Communication Pipes](#16-channels)
17. [Select Statement — Multiplexing](#17-select-statement)
18. [defer, panic, recover](#18-defer-panic-recover)
19. [Packages & Modules](#19-packages--modules)
20. [Closures & Anonymous Functions](#20-closures--anonymous-functions)
21. [Type Assertions & Type Switches](#21-type-assertions--type-switches)
22. [Embedding — Composition over Inheritance](#22-embedding)
23. [Goroutine Scheduler — GMP Model](#23-goroutine-scheduler)
24. [Memory Management & Garbage Collection](#24-memory-management)
25. [Concurrency Patterns](#25-concurrency-patterns)
26. [Common Interview Traps & Gotchas](#26-common-interview-traps)
27. [Interview Questions — Q&A Deep Dive](#27-interview-questions)

---

## 1. What is Go?

### 1.1 History & Philosophy

Go (also called Golang) was created at **Google in 2007** by **Robert Griesemer, Rob Pike, and Ken Thompson**. It was open-sourced in **2009**. The creators were frustrated with the complexity of C++ and the slowness of compilation, and they wanted a language that was:

- **Simple** — few keywords (25 keywords only), easy to read
- **Fast to compile** — even for massive codebases
- **Safe** — memory safe without a garbage collection pause problem
- **Concurrent** — built-in concurrency primitives (goroutines + channels)
- **Statically typed** — catch bugs at compile time
- **Garbage collected** — no manual memory management

```
LANGUAGE COMPARISON — Mental Model
===================================

          Speed │ Safety │ Simplicity │ Concurrency
  ─────────────┼────────┼────────────┼────────────
  C/C++        │  ████  │   low      │  manual
  Java         │  ███   │   high     │  threads
  Python       │  █     │   medium   │  GIL limited
  Go           │  ████  │   high     │  goroutines ← Sweet spot
  Rust         │  █████ │   highest  │  ownership model
```

### 1.2 Go's Core Design Principles

```
┌──────────────────────────────────────────────────────────┐
│                  GO DESIGN PRINCIPLES                    │
│                                                          │
│  1. Composition over Inheritance                         │
│     → No class hierarchy, use interfaces + embedding     │
│                                                          │
│  2. Explicit over Implicit                               │
│     → Error handling is explicit (no exceptions)         │
│                                                          │
│  3. Concurrency is first-class                           │
│     → goroutines, channels built into the language       │
│                                                          │
│  4. One way to do things                                 │
│     → gofmt enforces formatting, reduces debates         │
│                                                          │
│  5. Fast compilation                                     │
│     → Dependency management through explicit imports     │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Go Program Structure

### 2.1 The Anatomy of a Go Program

Every Go program has a specific structure. Let's dissect it completely:

```go
// EVERY Go file starts with a package declaration
package main          // ← "main" is special: it creates an executable

// Import statement — bring in external packages
import (
    "fmt"             // standard library: formatted I/O
    "os"              // OS functions
)

// init() runs BEFORE main() — optional, auto-called
func init() {
    fmt.Println("init runs first!")
}

// main() is the ENTRY POINT of a Go program
// No arguments, no return value
func main() {
    fmt.Println("Hello, World!")
}
```

### 2.2 Execution Flow

```
PROGRAM EXECUTION ORDER
========================

  Runtime starts
       │
       ▼
  Import packages (recursively)
       │
       ▼
  Package-level variables initialized
       │          (in order of declaration)
       ▼
  init() functions run
       │          (each file's init(), in import order)
       ▼
  main() function runs
       │
       ▼
  Program exits
```

### 2.3 Package Rules

```
PACKAGE CONCEPTS
=================

  package main      ← Executable program (produces binary)
  package fmt       ← Library package (imported by others)
  package mylib     ← Your custom library package

  ┌──────────────────────────────────────────────┐
  │  RULE: All files in a directory must have    │
  │        the SAME package name                  │
  │                                               │
  │  myapp/
  │  ├── main.go        package main              │
  │  ├── helpers.go     package main  ← same!    │
  │  └── utils/
  │      ├── math.go    package utils             │
  │      └── string.go  package utils ← same!    │
  └──────────────────────────────────────────────┘

  EXPORTED vs UNEXPORTED:
  ───────────────────────
  Uppercase first letter → exported (public)
  Lowercase first letter → unexported (private to package)

  fmt.Println  ← exported (P is uppercase) ✓
  fmt.println  ← unexported — would fail if accessed outside
```

---

## 3. Variables, Constants & Types

### 3.1 Variable Declaration — 4 Ways

Go gives you multiple ways to declare variables. Understanding when to use each is key.

```go
package main

import "fmt"

func main() {

    // ── WAY 1: var keyword with explicit type ──────────────────
    var age int = 25
    // Use when: package-level vars, or when type clarity matters

    // ── WAY 2: var keyword with type inference ─────────────────
    var name = "Alice"
    // Go infers type as string from the value

    // ── WAY 3: Short variable declaration (most common) ────────
    city := "Bangalore"
    // Use ONLY inside functions. Cannot use at package level.
    // := means "declare AND assign"

    // ── WAY 4: Multiple variables at once ──────────────────────
    var (
        x int     = 10
        y float64 = 3.14
        z bool    = true
    )

    // ── WAY 5: Multiple assignment ─────────────────────────────
    a, b := 1, 2
    fmt.Println(a, b) // 1 2

    // ── SWAP (Go's elegant swap) ────────────────────────────────
    a, b = b, a       // No temporary variable needed!
    fmt.Println(a, b) // 2 1

    fmt.Println(age, name, city, x, y, z)
}
```

### 3.2 Variable Declaration Decision Tree

```
WHEN TO USE WHICH DECLARATION?
================================

Start
  │
  ├── Inside a function?
  │       │
  │       ├── YES → Use := (short declaration)
  │       │         UNLESS you need explicit type clarity
  │       │         → Then use var name type = value
  │       │
  │       └── NO (package level) → MUST use var
  │
  ├── Need zero value only (no initial value)?
  │       → var count int   (count is 0 automatically)
  │
  └── Group of related vars?
          → var ( ... ) block
```

### 3.3 Constants

```go
package main

import "fmt"

// ── SIMPLE CONSTANTS ────────────────────────────────────────────
const Pi = 3.14159
const AppName = "MyApp"
const MaxRetries = 3

// ── TYPED vs UNTYPED CONSTANTS ──────────────────────────────────
const typedConst int = 42        // typed: only used as int
const untypedConst = 42          // untyped: can be used as any numeric type

// ── iota — THE CONSTANT GENERATOR ───────────────────────────────
// iota is a special identifier that starts at 0 and increments
// by 1 for each constant in a const block

type Weekday int

const (
    Sunday    Weekday = iota // 0
    Monday                  // 1
    Tuesday                 // 2
    Wednesday               // 3
    Thursday                // 4
    Friday                  // 5
    Saturday                // 6
)

// ── iota with expressions ────────────────────────────────────────
type ByteSize float64

const (
    _           = iota // skip 0 using blank identifier
    KB ByteSize = 1 << (10 * iota) // 1 << 10 = 1024
    MB                             // 1 << 20 = 1048576
    GB                             // 1 << 30
    TB                             // 1 << 40
)

func main() {
    fmt.Println(KB, MB, GB) // 1024 1.048576e+06 1.073741824e+09
    fmt.Println(Sunday, Monday, Saturday) // 0 1 6
}
```

```
iota VISUALIZATION
===================

  const (
    A = iota     → iota=0, A=0
    B            → iota=1, B=1
    C            → iota=2, C=2
  )

  const (
    X = iota * 2  → iota=0, X=0
    Y             → iota=1, Y=2
    Z             → iota=2, Z=4
  )

  NOTE: iota RESETS to 0 at each new const block!
```

### 3.4 Basic Data Types

```
GO BASIC TYPES — COMPLETE MAP
==============================

┌─────────────────────────────────────────────────────────┐
│  INTEGER TYPES                                          │
│                                                         │
│  int8   : -128 to 127               (8  bits)          │
│  int16  : -32768 to 32767           (16 bits)          │
│  int32  : -2^31 to 2^31-1           (32 bits)          │
│  int64  : -2^63 to 2^63-1           (64 bits)          │
│  int    : platform-dependent (32 or 64 bit)             │
│                                                         │
│  uint8  : 0 to 255                  (8  bits)          │
│  uint16 : 0 to 65535                (16 bits)          │
│  uint32 : 0 to 4294967295           (32 bits)          │
│  uint64 : 0 to 2^64-1               (64 bits)          │
│  uint   : platform-dependent                            │
│                                                         │
│  byte   : alias for uint8  (used for raw bytes)        │
│  rune   : alias for int32  (used for Unicode codepoints)│
│  uintptr: integer large enough to hold a pointer value  │
├─────────────────────────────────────────────────────────┤
│  FLOAT TYPES                                            │
│  float32 : 32-bit IEEE 754                              │
│  float64 : 64-bit IEEE 754 ← prefer this               │
├─────────────────────────────────────────────────────────┤
│  COMPLEX TYPES                                          │
│  complex64  : real + imaginary float32                  │
│  complex128 : real + imaginary float64                  │
├─────────────────────────────────────────────────────────┤
│  OTHER                                                  │
│  bool   : true / false                                  │
│  string : immutable sequence of bytes (UTF-8 encoded)   │
└─────────────────────────────────────────────────────────┘
```

```go
// TYPE CONVERSION — Go is STRICT, no implicit conversion
var i int = 42
var f float64 = float64(i)   // explicit conversion required
var u uint = uint(f)

// String and byte/rune conversions
s := "Hello, 世界"
b := []byte(s)    // string → byte slice
r := []rune(s)    // string → rune slice (correct for unicode!)

fmt.Println(len(s)) // 13 (bytes)
fmt.Println(len(r)) // 9  (characters!) ← rune handles unicode
```

---

## 4. Zero Values

### 4.1 What is a Zero Value?

In Go, **every variable is automatically initialized to its zero value** if no value is provided. This eliminates an entire class of bugs (uninitialized variable bugs) that plague C/C++.

```
ZERO VALUES — COMPLETE TABLE
==============================

  Type              Zero Value
  ──────────────────────────────
  int, int8...      0
  float32/64        0.0
  bool              false
  string            "" (empty string)
  pointer           nil
  slice             nil
  map               nil
  channel           nil
  function          nil
  interface         nil
  struct            each field gets its zero value
```

```go
package main

import "fmt"

type Person struct {
    Name string
    Age  int
    Active bool
}

func main() {
    var i int        // 0
    var f float64    // 0
    var b bool       // false
    var s string     // ""
    var p *int       // nil (pointer)
    var sl []int     // nil (slice)

    var person Person
    // person.Name = ""
    // person.Age = 0
    // person.Active = false

    fmt.Printf("int: %v\n", i)
    fmt.Printf("float64: %v\n", f)
    fmt.Printf("bool: %v\n", b)
    fmt.Printf("string: %q\n", s)
    fmt.Printf("pointer: %v\n", p)
    fmt.Printf("slice: %v\n", sl)
    fmt.Printf("person: %+v\n", person)

    // nil slice vs empty slice — INTERVIEW QUESTION!
    var nilSlice []int          // nil
    emptySlice := []int{}       // not nil, but length 0

    fmt.Println(nilSlice == nil)    // true
    fmt.Println(emptySlice == nil)  // false
    fmt.Println(len(nilSlice))      // 0
    fmt.Println(len(emptySlice))    // 0
    // Both behave the same for range and append!
}
```

---

## 5. Type System

### 5.1 Type Definitions vs Type Aliases

```go
// TYPE DEFINITION — creates a brand NEW type
type Celsius float64
type Fahrenheit float64

// These are DIFFERENT types even though both are float64 underneath
// This prevents accidental mixing of Celsius and Fahrenheit

func CToF(c Celsius) Fahrenheit {
    return Fahrenheit(c*9/5 + 32) // explicit conversion required
}

// TYPE ALIAS — same type, different name
type MyInt = int  // MyInt IS int (not a new type)
// Used rarely — mainly for compatibility/refactoring

// ── METHODS can be defined on type definitions ────────────────
func (c Celsius) String() string {
    return fmt.Sprintf("%.2f°C", float64(c))
}
```

```
TYPE SYSTEM MENTAL MODEL
=========================

  float64 ←── (underlying type)
    │
    ├── Celsius    (type definition: NEW distinct type)
    ├── Fahrenheit (type definition: NEW distinct type)
    │
    └── MyFloat = float64 (alias: SAME type, just renamed)

  Celsius and Fahrenheit are NOT assignable to each other
  without explicit conversion — compiler enforces this!
  This is "type safety" in action.
```

### 5.2 Composite Types Overview

```
COMPOSITE TYPES IN GO
======================

  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  Array   │    │  Slice   │    │   Map    │    │  Struct  │
  │          │    │          │    │          │    │          │
  │ Fixed    │    │ Dynamic  │    │ Key-Val  │    │ Fields   │
  │ size     │    │ size     │    │ pairs    │    │ grouped  │
  │ [5]int   │    │ []int    │    │map[k]v   │    │ struct{} │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │
  Value type      Reference type  Reference type  Value type
  (copied)        (shares backing) (shares backing) (copied)
```

---

## 6. Control Flow

### 6.1 if Statement

```go
// ── BASIC if ─────────────────────────────────────────────────
if x > 10 {
    fmt.Println("greater than 10")
} else if x == 10 {
    fmt.Println("equal to 10")
} else {
    fmt.Println("less than 10")
}

// ── if with INITIALIZATION STATEMENT ────────────────────────
// VERY COMMON Go pattern — variable scoped to the if block
if val, err := someFunction(); err != nil {
    fmt.Println("Error:", err)
} else {
    fmt.Println("Value:", val)
    // val is accessible here too
}
// val and err are NOT accessible here — scoped to if/else block

// ── No parentheses around condition (unlike C/Java) ─────────
// WRONG: if (x > 0) { ... }
// RIGHT: if x > 0 { ... }
```

### 6.2 for Loop — Go's ONLY Loop

**Go has only ONE loop keyword: `for`** — yet it can replicate while, do-while, infinite loops, and traditional for loops.

```go
// ── TRADITIONAL for loop ──────────────────────────────────────
for i := 0; i < 5; i++ {
    fmt.Println(i)
}

// ── WHILE-style (condition only) ──────────────────────────────
n := 1
for n < 100 {
    n *= 2
}

// ── INFINITE loop ─────────────────────────────────────────────
for {
    // runs forever
    if someCondition {
        break
    }
}

// ── RANGE loop — iterate over collections ─────────────────────
nums := []int{10, 20, 30}
for i, v := range nums {
    fmt.Printf("index: %d, value: %d\n", i, v)
}

// Skip index with blank identifier
for _, v := range nums {
    fmt.Println(v)
}

// Only index
for i := range nums {
    fmt.Println(i)
}

// Range over string — iterates RUNES (unicode characters)
for i, ch := range "Hello, 世界" {
    fmt.Printf("byte index: %d, rune: %c\n", i, ch)
}
// Note: byte index jumps (e.g., 世 takes 3 bytes)

// Range over map
m := map[string]int{"a": 1, "b": 2}
for key, value := range m {
    fmt.Printf("%s → %d\n", key, value)
}

// Range over channel
ch := make(chan int, 3)
ch <- 1; ch <- 2; ch <- 3
close(ch)
for v := range ch { // reads until channel closed
    fmt.Println(v)
}
```

### 6.3 switch Statement

```go
// ── BASIC switch ──────────────────────────────────────────────
day := "Monday"
switch day {
case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
    fmt.Println("Weekday")
case "Saturday", "Sunday":
    fmt.Println("Weekend")
default:
    fmt.Println("Unknown")
}
// KEY: No automatic fallthrough (unlike C)! Each case breaks automatically.

// ── switch with NO condition (like if-else chain) ─────────────
x := 42
switch {
case x < 0:
    fmt.Println("negative")
case x == 0:
    fmt.Println("zero")
case x > 0:
    fmt.Println("positive")
}

// ── switch with initialization ────────────────────────────────
switch os := runtime.GOOS; os {
case "linux":
    fmt.Println("Linux")
case "darwin":
    fmt.Println("Mac")
default:
    fmt.Println("Other:", os)
}

// ── fallthrough — explicitly fall to next case ────────────────
switch 1 {
case 1:
    fmt.Println("one")
    fallthrough        // explicitly falls to case 2
case 2:
    fmt.Println("two") // this WILL print
case 3:
    fmt.Println("three") // this will NOT print
}
```

---

## 7. Functions

### 7.1 Function Fundamentals

```go
// ── BASIC function ────────────────────────────────────────────
func add(a int, b int) int {
    return a + b
}

// ── Shared type for parameters ────────────────────────────────
func add2(a, b int) int { // both int, can share type
    return a + b
}

// ── MULTIPLE RETURN VALUES ────────────────────────────────────
// THIS IS A KEY Go FEATURE
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil
}

result, err := divide(10, 3)
if err != nil {
    log.Fatal(err)
}
fmt.Println(result)

// ── NAMED RETURN VALUES ───────────────────────────────────────
func minMax(arr []int) (min, max int) {
    // min and max are pre-declared as return variables
    min, max = arr[0], arr[0]
    for _, v := range arr {
        if v < min { min = v }
        if v > max { max = v }
    }
    return // "naked return" — returns min and max automatically
}
// Note: Named returns improve documentation, but naked returns
// can reduce readability in long functions. Use carefully.

// ── VARIADIC functions ────────────────────────────────────────
// Accepts 0 or more arguments of the same type
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}
sum(1, 2, 3)          // regular call
sum([]int{1,2,3}...)  // spread a slice with ...
```

### 7.2 Functions as Values

```go
// Functions are FIRST-CLASS values in Go
// They can be assigned to variables, passed as arguments, returned

// ── Function variable ──────────────────────────────────────────
var double func(int) int = func(n int) int {
    return n * 2
}
fmt.Println(double(5)) // 10

// ── Passing functions as arguments (higher-order functions) ───
func apply(nums []int, f func(int) int) []int {
    result := make([]int, len(nums))
    for i, n := range nums {
        result[i] = f(n)
    }
    return result
}

doubled := apply([]int{1, 2, 3}, func(n int) int { return n * 2 })
// Output: [2 4 6]

// ── Returning functions ────────────────────────────────────────
func multiplier(factor int) func(int) int {
    return func(n int) int {
        return n * factor  // factor is "captured" — this is a closure!
    }
}
triple := multiplier(3)
fmt.Println(triple(7)) // 21
```

### 7.3 Function Call Stack — Visual

```
FUNCTION CALL STACK VISUALIZATION
===================================

  main() calls foo() calls bar()

  ┌─────────────────────────────┐  ← top of stack (grows downward)
  │  bar() stack frame          │
  │  local vars: x=5, y=10      │
  │  return address → foo()     │
  ├─────────────────────────────┤
  │  foo() stack frame          │
  │  local vars: result=0       │
  │  return address → main()    │
  ├─────────────────────────────┤
  │  main() stack frame         │
  │  local vars: ...            │
  │  return address → OS        │
  └─────────────────────────────┘  ← bottom of stack

  When bar() returns:
  - bar's frame is POPPED
  - execution resumes in foo() at return address
```

---

## 8. Pointers

### 8.1 What is a Pointer?

A **pointer** is a variable that stores the **memory address** of another variable — not the value itself.

```
MEMORY MODEL — POINTER VISUALIZATION
======================================

  Without pointer:
  ┌─────────────────────────────────────────┐
  │ MEMORY                                  │
  │                                         │
  │  address 0x100    address 0x108         │
  │  ┌───────────┐    ┌───────────┐         │
  │  │    42     │    │    42     │ ← COPY  │
  │  └───────────┘    └───────────┘         │
  │       a                b                │
  │  (original)        (copy of a)          │
  └─────────────────────────────────────────┘

  With pointer:
  ┌─────────────────────────────────────────┐
  │ MEMORY                                  │
  │                                         │
  │  address 0x100    address 0x108         │
  │  ┌───────────┐    ┌───────────┐         │
  │  │    42     │    │  0x100    │ → points│
  │  └───────────┘    └───────────┘   to a │
  │       a               p                 │
  │  (the value)     (address of a)         │
  └─────────────────────────────────────────┘
```

```go
package main

import "fmt"

func main() {
    a := 42

    // & operator: takes the ADDRESS of a variable
    p := &a          // p is a pointer to int (*int)

    fmt.Println(a)   // 42    — the value
    fmt.Println(&a)  // 0x... — the address of a
    fmt.Println(p)   // 0x... — p holds the address (same as &a)
    fmt.Println(*p)  // 42    — dereference: get value AT the address

    // Modify through pointer
    *p = 100         // dereference and set
    fmt.Println(a)   // 100 — a is changed!

    // new() function — allocates and returns pointer to zero value
    q := new(int)    // *int pointing to 0
    *q = 55
    fmt.Println(*q)  // 55
}

// ── WHY pointers matter — function mutation example ───────────
func incrementByValue(x int) {
    x++ // modifies LOCAL COPY only — original unchanged
}

func incrementByPointer(x *int) {
    (*x)++ // modifies the ORIGINAL through pointer
    // or simply: *x++
}

func main2() {
    n := 10
    incrementByValue(n)
    fmt.Println(n) // 10 — unchanged!

    incrementByPointer(&n)
    fmt.Println(n) // 11 — changed!
}
```

### 8.2 Pointer Rules & Safety

```
GO POINTER RULES
=================

  ✓ Go has pointers BUT:
  
  ✗ NO pointer arithmetic (unlike C)
        // p++ is ILLEGAL in Go — prevents memory corruption
  
  ✓ No dangling pointers
        // GC keeps values alive as long as pointers exist
  
  ✓ nil is the zero value for pointers
        var p *int  // p == nil
  
  ✓ Always check for nil before dereferencing!
        if p != nil {
            fmt.Println(*p)
        }
  
  ✗ Dereferencing nil → runtime panic!
        var p *int
        fmt.Println(*p) // PANIC: nil pointer dereference
```

---

## 9. Arrays vs Slices

### 9.1 Arrays — Fixed Size

```go
// ── ARRAY declaration ────────────────────────────────────────
var arr [5]int               // [0 0 0 0 0] — zero values
arr2 := [3]string{"a","b","c"}
arr3 := [...]int{1,2,3,4}   // ... lets compiler count: [4]int

// ── Arrays are VALUE TYPES ────────────────────────────────────
a := [3]int{1, 2, 3}
b := a               // b is a COPY of a
b[0] = 99
fmt.Println(a[0])    // 1 — a is unchanged
fmt.Println(b[0])    // 99

// ── Array type includes its length ──────────────────────────
// [3]int and [4]int are DIFFERENT types — cannot assign to each other!
```

### 9.2 Slices — Dynamic Windows into Arrays

A **slice** is a descriptor for a contiguous segment of an underlying array. It consists of three fields:

```
SLICE INTERNAL STRUCTURE
=========================

  slice header (3 fields):
  ┌──────────────────────────────────────────┐
  │  ptr   │  len   │  cap                  │
  │ pointer│ length │ capacity              │
  │ to arr │        │                       │
  └──────────────────────────────────────────┘
       │
       ▼
  underlying array:
  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ 0  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │
  └────┴────┴────┴────┴────┴────┴────┴────┘
   ^                        ^              ^
   ptr                  ptr+len          ptr+cap

  ptr  = pointer to first element of the slice in the array
  len  = number of elements accessible in this slice
  cap  = total elements from ptr to end of underlying array
```

```go
package main

import "fmt"

func main() {
    // ── Create slice from array literal ─────────────────────────
    s := []int{1, 2, 3, 4, 5}

    // ── make(type, len, cap) ─────────────────────────────────────
    s2 := make([]int, 3)       // len=3, cap=3
    s3 := make([]int, 3, 10)   // len=3, cap=10

    // ── Slice operations ─────────────────────────────────────────
    s4 := s[1:3]   // [2, 3] — from index 1 up to (not including) 3
    s5 := s[:2]    // [1, 2] — from beginning up to index 2
    s6 := s[2:]    // [3, 4, 5] — from index 2 to end
    s7 := s[:]     // [1, 2, 3, 4, 5] — full slice

    fmt.Println(len(s4), cap(s4)) // len=2, cap=4 (from index 1 to end)

    // ── CRITICAL: Slices SHARE the underlying array! ─────────────
    original := []int{1, 2, 3, 4, 5}
    slice1 := original[1:3]  // [2, 3]
    slice1[0] = 99
    fmt.Println(original) // [1 99 3 4 5] — original is MODIFIED!

    // ── append — add elements ─────────────────────────────────────
    s = append(s, 6, 7)        // append one or more elements
    s = append(s, []int{8,9}...) // append another slice

    fmt.Println(s, s2, s3, s5, s6, s7)
}
```

### 9.3 Append & Capacity Growth — The Interview Favorite

```
APPEND GROWTH VISUALIZATION
============================

  s := make([]int, 0, 2) // len=0, cap=2

  Step 1: append(s, 1)
  ┌───┬───┐
  │ 1 │   │  len=1, cap=2 (fits, no realloc)
  └───┴───┘

  Step 2: append(s, 2)
  ┌───┬───┐
  │ 1 │ 2 │  len=2, cap=2 (fits, no realloc)
  └───┴───┘

  Step 3: append(s, 3)  ← CAPACITY EXCEEDED!
  
  Go allocates NEW, larger array (roughly 2x old cap):
  ┌───┬───┬───┬───┐
  │ 1 │ 2 │ 3 │   │  len=3, cap=4 (new backing array!)
  └───┴───┴───┴───┘

  Old array is abandoned (GC will collect it)
  All previous slice headers pointing to OLD array
  are now STALE — they don't see new elements!

  INTERVIEW TRAP:
  ───────────────
  a := make([]int, 3, 6)
  b := a          // b shares backing array with a
  a = append(a, 99)
  // a still within cap (no realloc)
  // b[3] == 99 if we could access it,
  // but b's len is 3, so b[3] would panic
  // However — modifying a[0] after append DOES affect b[0]!
```

```go
// ── COPY — make an independent copy ───────────────────────────
src := []int{1, 2, 3}
dst := make([]int, len(src))
n := copy(dst, src)   // returns number of elements copied
fmt.Println(n, dst)   // 3 [1 2 3]

// Now dst is independent — modifying src doesn't affect dst
src[0] = 99
fmt.Println(dst[0]) // 1 — unchanged
```

### 9.4 2D Slices

```go
// Create a 3x4 matrix
matrix := make([][]int, 3)
for i := range matrix {
    matrix[i] = make([]int, 4)
}
matrix[1][2] = 42
```

---

## 10. Maps

### 10.1 Map Fundamentals

A **map** is Go's built-in hash table — an unordered collection of key-value pairs. Keys must be **comparable** (can use ==).

```
MAP INTERNAL STRUCTURE (simplified)
=====================================

  map[string]int

  ┌─────────────────────────────────────────────┐
  │               HASH TABLE                   │
  │                                             │
  │  "alice" ──hash──► bucket 2 ──► [alice:25] │
  │  "bob"   ──hash──► bucket 0 ──► [bob:30]   │
  │  "carol" ──hash──► bucket 2 ──► [carol:28] │
  │                         ↑                  │
  │                   collision: chained        │
  └─────────────────────────────────────────────┘

  Keys that can be used: int, string, bool, pointer,
                          array, struct (if all fields comparable)
  Keys that CANNOT be used: slice, map, function
```

```go
package main

import "fmt"

func main() {
    // ── Declaration and initialization ──────────────────────────
    var m1 map[string]int        // nil map — cannot write to it!
    m2 := map[string]int{}       // empty map — can write
    m3 := make(map[string]int)   // empty map — can write
    m4 := map[string]int{        // map literal
        "alice": 25,
        "bob":   30,
    }

    // Writing to nil map panics!
    // m1["key"] = 1  // PANIC: assignment to nil map
    _ = m1           // suppress unused error

    // ── CRUD operations ────────────────────────────────────────
    m4["carol"] = 28      // create/update
    age := m4["alice"]    // read → 25
    delete(m4, "bob")     // delete

    // ── The COMMA-OK IDIOM — check key existence ────────────────
    // IMPORTANT: accessing missing key returns ZERO VALUE, not error
    val, ok := m4["dave"]
    if ok {
        fmt.Println("dave:", val)
    } else {
        fmt.Println("dave not found, val:", val) // val=0 (zero value)
    }

    // Without comma-ok — dangerous!
    x := m4["nonexistent"]  // returns 0 — could be misleading

    // ── Iterate over map ───────────────────────────────────────
    for k, v := range m4 {
        fmt.Printf("%s: %d\n", k, v)
    }
    // NOTE: map iteration order is RANDOM (by design, security reason)

    fmt.Println(m2, m3, age, x)
}
```

### 10.2 Map as Set

```go
// Go has no built-in Set type — use map[T]bool or map[T]struct{}
// map[T]struct{} is preferred: struct{} has zero size (no memory)

seen := make(map[string]struct{})
words := []string{"hello", "world", "hello", "go"}

for _, w := range words {
    seen[w] = struct{}{} // struct{}{} = zero-size value
}

// Check membership
if _, exists := seen["hello"]; exists {
    fmt.Println("hello is in the set")
}
// len(seen) = 3 (deduped)
```

---

## 11. Structs

### 11.1 Struct Basics

A **struct** is a composite type that groups together variables under a single name. It's Go's primary way of defining custom data types (analogous to classes, but without inheritance).

```go
package main

import "fmt"

// ── Struct DEFINITION ─────────────────────────────────────────
type Person struct {
    Name    string
    Age     int
    Email   string
    address string  // unexported field (lowercase) — package-private
}

// ── ANONYMOUS struct — for one-off use ────────────────────────
point := struct {
    X, Y int
}{X: 1, Y: 2}

func main() {
    // ── Struct instantiation ──────────────────────────────────
    p1 := Person{"Alice", 30, "alice@example.com", "123 Main St"}
    // Positional — fragile, avoid for structs with many fields

    p2 := Person{
        Name:  "Bob",
        Age:   25,
        Email: "bob@example.com",
        // address defaults to "" (zero value)
    }

    // ── Field access ──────────────────────────────────────────
    fmt.Println(p2.Name)  // "Bob"
    p2.Age = 26           // modify field

    // ── Pointer to struct ─────────────────────────────────────
    p3 := &Person{Name: "Carol", Age: 28}
    // Auto-dereference: no need for (*p3).Name
    fmt.Println(p3.Name) // Go auto-dereferences pointer to struct!
    p3.Age = 29          // same as (*p3).Age = 29

    // ── Struct comparison ─────────────────────────────────────
    // Structs are comparable if ALL fields are comparable
    a := Person{Name: "X", Age: 1}
    b := Person{Name: "X", Age: 1}
    fmt.Println(a == b) // true

    fmt.Println(p1, point)
}
```

### 11.2 Struct Memory Layout

```
STRUCT MEMORY LAYOUT & ALIGNMENT
===================================

  type Example struct {
      A bool    // 1 byte
      B int64   // 8 bytes
      C bool    // 1 byte
  }

  ACTUAL MEMORY (with padding):
  ┌──┬─────────┬──┬────────────┬──┬────────┐
  │A │PADDING  │B              │C │PADDING │
  │1 │7 bytes  │8 bytes        │1 │7 bytes │
  └──┴─────────┴───────────────┴──┴────────┘
  Total: 24 bytes! (not 10)

  OPTIMIZED (fields ordered largest to smallest):
  type Example struct {
      B int64   // 8 bytes
      A bool    // 1 byte
      C bool    // 1 byte
                // 6 bytes padding at end
  }
  Total: 16 bytes — SAVINGS of 8 bytes!

  RULE: Order struct fields from largest to smallest
        to minimize padding (important for performance-critical code)
```

### 11.3 Struct Tags

```go
// Struct TAGS — metadata for fields (read by reflection)
type User struct {
    ID       int    `json:"id" db:"user_id"`
    Name     string `json:"name" validate:"required,min=2"`
    Email    string `json:"email,omitempty"` // omit if empty in JSON
    password string `json:"-"`               // always omit in JSON
}

// Tags are used by:
// encoding/json  — JSON serialization
// database/sql   — DB field mapping
// validate       — input validation libraries
// yaml           — YAML serialization
```

---

## 12. Methods

### 12.1 Methods on Types

A **method** is a function with a **receiver** — it's associated with a type.

```go
type Rectangle struct {
    Width, Height float64
}

// ── VALUE receiver ────────────────────────────────────────────
// r is a COPY — cannot modify the original
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

func (r Rectangle) Perimeter() float64 {
    return 2 * (r.Width + r.Height)
}

// ── POINTER receiver ─────────────────────────────────────────
// r is a pointer — CAN modify the original
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}

func main() {
    rect := Rectangle{Width: 10, Height: 5}
    
    fmt.Println(rect.Area())      // 50
    fmt.Println(rect.Perimeter()) // 30
    
    rect.Scale(2)                 // Go auto-takes address: (&rect).Scale(2)
    fmt.Println(rect.Width)       // 20
    fmt.Println(rect.Height)      // 10
}
```

### 12.2 Value vs Pointer Receiver — Decision

```
WHEN TO USE WHICH RECEIVER?
=============================

  Value Receiver (r Rectangle)
  ├── Use when method doesn't modify the receiver
  ├── Use for small structs (copy is cheap)
  └── Use for immutable types (safer)

  Pointer Receiver (r *Rectangle)
  ├── Use when method MODIFIES the receiver
  ├── Use for large structs (avoid copy overhead)
  └── Use when receiver is large or you want consistency
      (if ANY method needs pointer, use pointer for ALL)

  CONSISTENCY RULE (important for interfaces!):
  ─────────────────────────────────────────────
  If a type has ANY pointer receiver methods,
  it's conventional to use pointer receiver for ALL methods.
  This ensures the type satisfies interfaces predictably.
```

---

## 13. Interfaces

### 13.1 What is an Interface?

An **interface** in Go defines a set of method signatures. Any type that implements all those methods **automatically satisfies** the interface — no explicit declaration needed. This is called **implicit implementation** (or "duck typing" with type safety).

```
INTERFACE CONCEPT VISUALIZATION
================================

  "If it walks like a duck and quacks like a duck, it's a duck"

  interface Animal {        Any type that has:
      Sound() string    ←── • Sound() string method
      Move()            ←── • Move() method
  }                         AUTOMATICALLY implements Animal
                            No "implements Animal" needed!

  This is different from Java/C# where you write:
  "class Dog implements Animal" — Go doesn't need this!
```

```go
package main

import (
    "fmt"
    "math"
)

// ── Define an interface ───────────────────────────────────────
type Shape interface {
    Area() float64
    Perimeter() float64
}

// ── Types that implement Shape (implicitly) ───────────────────
type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return math.Pi * c.Radius * c.Radius
}

func (c Circle) Perimeter() float64 {
    return 2 * math.Pi * c.Radius
}

type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

func (r Rectangle) Perimeter() float64 {
    return 2 * (r.Width + r.Height)
}

// ── Function that accepts ANY Shape ──────────────────────────
func printShapeInfo(s Shape) {
    fmt.Printf("Area: %.2f, Perimeter: %.2f\n", s.Area(), s.Perimeter())
}

func main() {
    c := Circle{Radius: 5}
    r := Rectangle{Width: 4, Height: 3}

    printShapeInfo(c) // Circle satisfies Shape
    printShapeInfo(r) // Rectangle satisfies Shape

    // ── Interface as collection of different types ─────────────
    shapes := []Shape{c, r, Circle{Radius: 2}}
    for _, s := range shapes {
        printShapeInfo(s)
    }
}
```

### 13.2 Interface Internals

```
INTERFACE VALUE INTERNAL REPRESENTATION
=========================================

  An interface value has TWO parts:
  ┌───────────────────────────────────────┐
  │  interface value                      │
  │  ┌───────────────┬───────────────┐   │
  │  │  type info    │  data pointer │   │
  │  │  (*Circle)    │  → circle{5}  │   │
  │  └───────────────┴───────────────┘   │
  └───────────────────────────────────────┘

  var s Shape = Circle{Radius: 5}
  // type info: Circle
  // data: pointer to Circle value

  var s2 Shape = Rectangle{Width:4, Height:3}
  // type info: Rectangle
  // data: pointer to Rectangle value

  nil interface:
  ┌───────────────────────────────────────┐
  │  ┌───────────────┬───────────────┐   │
  │  │     nil       │     nil       │   │
  │  └───────────────┴───────────────┘   │
  └───────────────────────────────────────┘
  var s Shape // both type and data are nil
```

### 13.3 The Empty Interface

```go
// interface{} (or any in Go 1.18+) — the empty interface
// Satisfied by ALL types (has no methods to implement)

func printAnything(v interface{}) {
    fmt.Printf("Type: %T, Value: %v\n", v, v)
}

printAnything(42)
printAnything("hello")
printAnything([]int{1,2,3})
printAnything(nil)

// Modern Go uses 'any' as alias for interface{}
func printAnythingNew(v any) {
    fmt.Println(v)
}

// ── Maps with any values ───────────────────────────────────────
data := map[string]any{
    "name": "Alice",
    "age":  30,
    "tags": []string{"go", "developer"},
}
```

### 13.4 Common Built-in Interfaces

```go
// ── Stringer interface (fmt package) ──────────────────────────
// If your type implements String() string, fmt will use it!
type Temperature float64

func (t Temperature) String() string {
    return fmt.Sprintf("%.1f°C", float64(t))
}

t := Temperature(36.6)
fmt.Println(t) // "36.6°C" — fmt calls t.String() automatically

// ── error interface ───────────────────────────────────────────
type error interface {
    Error() string
}

// ── io.Reader interface ───────────────────────────────────────
type Reader interface {
    Read(p []byte) (n int, err error)
}

// ── io.Writer interface ───────────────────────────────────────
type Writer interface {
    Write(p []byte) (n int, err error)
}
// These are used EVERYWHERE in Go's standard library!
```

---

## 14. Error Handling

### 14.1 Go's Error Philosophy

Go does **not** use exceptions. Instead, errors are **values** returned explicitly from functions. This is a deliberate design choice.

```
ERROR HANDLING PHILOSOPHY
===========================

  Languages with exceptions:
  ──────────────────────────
  try {
      result = doSomething()
  } catch (Exception e) {
      handle(e)
  }
  Problem: caller can IGNORE exceptions, errors are invisible

  Go's approach:
  ──────────────
  result, err := doSomething()
  if err != nil {
      // you MUST handle this explicitly
      return err
  }
  Benefit: errors are impossible to accidentally ignore
           (compiler warns if err is unused with _)
```

```go
package main

import (
    "errors"
    "fmt"
)

// ── The error interface ───────────────────────────────────────
type error interface {
    Error() string
}

// ── Creating errors ───────────────────────────────────────────
err1 := errors.New("something went wrong")
err2 := fmt.Errorf("user %d not found", 42)  // with formatting

// ── Custom error types ────────────────────────────────────────
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error on field '%s': %s", e.Field, e.Message)
}

func validateAge(age int) error {
    if age < 0 {
        return &ValidationError{Field: "age", Message: "cannot be negative"}
    }
    if age > 150 {
        return &ValidationError{Field: "age", Message: "unrealistically high"}
    }
    return nil
}

// ── Wrapping errors (Go 1.13+) ────────────────────────────────
func processUser(id int) error {
    if err := validateAge(-5); err != nil {
        return fmt.Errorf("processUser: %w", err) // %w WRAPS the error
    }
    return nil
}

// ── errors.Is and errors.As ────────────────────────────────────
var ErrNotFound = errors.New("not found")

func findUser(id int) error {
    return fmt.Errorf("findUser: %w", ErrNotFound) // wrap
}

func main() {
    err := findUser(1)

    // errors.Is — checks if error IS a specific error (unwraps chain)
    if errors.Is(err, ErrNotFound) {
        fmt.Println("User not found!") // prints this
    }

    err2 := processUser(1)
    // errors.As — extract error as a specific type
    var valErr *ValidationError
    if errors.As(err2, &valErr) {
        fmt.Println("Field:", valErr.Field)   // "age"
        fmt.Println("Msg:", valErr.Message)   // "cannot be negative"
    }

    fmt.Println(err1, err2)
}
```

### 14.2 Error Handling Flow

```
ERROR PROPAGATION PATTERN
===========================

  func C() error {
      return errors.New("root cause")
  }

  func B() error {
      if err := C(); err != nil {
          return fmt.Errorf("B: %w", err)  // wrap with context
      }
      return nil
  }

  func A() error {
      if err := B(); err != nil {
          return fmt.Errorf("A: %w", err)  // wrap again
      }
      return nil
  }

  err := A()
  // err.Error() == "A: B: root cause"
  // errors.Is(err, rootCause) == true  (unwraps chain)

  ERROR CHAIN:
  A's error ──wraps──► B's error ──wraps──► "root cause"
```

### 14.3 Sentinel Errors

```go
// Sentinel errors are predefined error values used for comparison
// Standard library examples:
import (
    "io"
    "os"
)

// io.EOF — signals end of file/stream
_, err := reader.Read(buf)
if err == io.EOF {
    // done reading
}

// os.ErrNotExist
_, err = os.Open("missing.txt")
if errors.Is(err, os.ErrNotExist) {
    fmt.Println("file does not exist")
}
```

---

## 15. Goroutines

### 15.1 What is a Goroutine?

A **goroutine** is a **lightweight thread** managed by the Go runtime (not the OS). They are cheap — you can have thousands or millions of them. They start with a small stack (~2KB) that grows as needed.

```
GOROUTINE vs OS THREAD
========================

  OS Thread:
  ─────────
  • Stack: 1-8 MB fixed size
  • Creation: ~1ms, expensive
  • Context switch: OS kernel involved, slow
  • Count: typically hundreds

  Goroutine:
  ──────────
  • Stack: starts at ~2KB, grows dynamically
  • Creation: microseconds, very cheap
  • Context switch: Go runtime, fast
  • Count: can have millions

  RELATIONSHIP:
  ┌────────────────────────────────────────────────────┐
  │  Many goroutines → few OS threads                  │
  │                                                    │
  │  Goroutine1 ─┐                                     │
  │  Goroutine2 ─┤                                     │
  │  Goroutine3 ─┼──► OS Thread 1 ──► CPU Core 1      │
  │  Goroutine4 ─┤                                     │
  │  Goroutine5 ─┘                                     │
  │                                                    │
  │  Goroutine6 ─┐                                     │
  │  Goroutine7 ─┼──► OS Thread 2 ──► CPU Core 2      │
  │  Goroutine8 ─┘                                     │
  └────────────────────────────────────────────────────┘
  This is called M:N threading (M goroutines on N OS threads)
```

```go
package main

import (
    "fmt"
    "time"
    "sync"
)

func sayHello(name string) {
    fmt.Printf("Hello, %s!\n", name)
}

func main() {
    // ── Launch a goroutine with 'go' keyword ──────────────────
    go sayHello("Alice")  // runs concurrently
    go sayHello("Bob")    // runs concurrently

    // PROBLEM: main() might exit before goroutines finish!
    // Solution 1: time.Sleep (bad — not reliable)
    time.Sleep(time.Millisecond * 100)

    // Solution 2: sync.WaitGroup (correct approach)
    var wg sync.WaitGroup

    for i := 0; i < 5; i++ {
        wg.Add(1)         // tell WaitGroup: 1 more goroutine
        go func(n int) {
            defer wg.Done() // tell WaitGroup: this goroutine done
            fmt.Println("Worker", n)
        }(i)              // pass i as argument (important! see gotchas)
    }

    wg.Wait() // block until all goroutines call Done()
    fmt.Println("All goroutines done")
}
```

### 15.2 Goroutine Lifecycle

```
GOROUTINE STATES
=================

  Created → Runnable → Running → (Blocked) → Runnable → Dead
                ↑                    │
                └────────────────────┘
                   (unblocked: I/O done, channel ready, etc.)

  States:
  • Runnable: ready to run, waiting for OS thread
  • Running: actively executing on an OS thread
  • Blocked: waiting for I/O, channel, mutex, etc.
  • Dead: finished execution
```

---

## 16. Channels

### 16.1 What is a Channel?

A **channel** is a typed pipe through which goroutines communicate. It's Go's implementation of the CSP (Communicating Sequential Processes) model.

```
"Do not communicate by sharing memory;
 instead, share memory by communicating." — Go proverb

CHANNEL VISUALIZATION
======================

  goroutine A ──send──► [===channel===] ──receive──► goroutine B
                          (buffer)

  Unbuffered channel (buffer=0):
  ───────────────────────────────
  Send BLOCKS until receiver is ready
  Receive BLOCKS until sender sends
  Perfect synchronization point

  ┌────────┐   send    ┌──────────┐   receive  ┌────────┐
  │ Sender │──────────►│ no buffer│────────────►│Receiver│
  │(blocks)│           └──────────┘             │(blocks)│
  └────────┘                                    └────────┘

  Buffered channel (buffer=N):
  ────────────────────────────
  Send ONLY blocks when buffer is full
  Receive ONLY blocks when buffer is empty

  ┌────────┐   send    ┌──────────────────┐   receive  ┌────────┐
  │ Sender │──────────►│ [slot1][slot2][] │────────────►│Receiver│
  └────────┘           └──────────────────┘            └────────┘
```

```go
package main

import "fmt"

func main() {
    // ── Unbuffered channel ────────────────────────────────────
    ch := make(chan int)  // unbuffered

    go func() {
        ch <- 42  // send: blocks until receiver is ready
    }()

    val := <-ch  // receive: blocks until sender sends
    fmt.Println(val) // 42

    // ── Buffered channel ──────────────────────────────────────
    bch := make(chan string, 3) // buffer size 3

    bch <- "one"    // doesn't block (buffer not full)
    bch <- "two"    // doesn't block
    bch <- "three"  // doesn't block
    // bch <- "four"  // WOULD BLOCK (buffer full)

    fmt.Println(<-bch) // "one"
    fmt.Println(<-bch) // "two"
    fmt.Println(<-bch) // "three"

    // ── Closing a channel ─────────────────────────────────────
    nums := make(chan int, 5)
    nums <- 1; nums <- 2; nums <- 3
    close(nums) // signal: no more values will be sent

    // Range over closed channel reads all values then stops
    for n := range nums {
        fmt.Println(n) // 1, 2, 3
    }

    // Check if channel is closed
    v, ok := <-nums
    // ok == false means channel is closed and empty
    fmt.Println(v, ok) // 0 false

    // ── Directional channels — restrict use ───────────────────
    // chan<- int : send-only channel
    // <-chan int : receive-only channel
    // This enforces correct usage at compile time
}

// Producer sends on channel, Consumer receives
func producer(ch chan<- int) { // send-only
    for i := 0; i < 5; i++ {
        ch <- i
    }
    close(ch)
}

func consumer(ch <-chan int) { // receive-only
    for v := range ch {
        fmt.Println("Received:", v)
    }
}
```

### 16.2 Channel Patterns

```go
// ── PIPELINE pattern ──────────────────────────────────────────
// Output of one stage feeds into next

func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

func main() {
    // Pipeline: generate → square → print
    c := generate(2, 3, 4)
    out := square(c)
    for v := range out {
        fmt.Println(v) // 4, 9, 16
    }
}
```

---

## 17. Select Statement

### 17.1 Select — Multiplexing Channels

`select` is like a `switch` but for channel operations. It waits for multiple channel operations and picks one that's ready.

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch1 := make(chan string)
    ch2 := make(chan string)

    go func() {
        time.Sleep(1 * time.Second)
        ch1 <- "one"
    }()

    go func() {
        time.Sleep(2 * time.Second)
        ch2 <- "two"
    }()

    // Wait for EITHER channel to send
    for i := 0; i < 2; i++ {
        select {
        case msg1 := <-ch1:
            fmt.Println("Received from ch1:", msg1)
        case msg2 := <-ch2:
            fmt.Println("Received from ch2:", msg2)
        }
    }

    // ── Non-blocking select with default ─────────────────────
    ch := make(chan int, 1)
    select {
    case v := <-ch:
        fmt.Println("Received:", v)
    default:
        fmt.Println("No value ready") // runs immediately
    }

    // ── Timeout pattern ───────────────────────────────────────
    ch3 := make(chan int)
    select {
    case v := <-ch3:
        fmt.Println("Received:", v)
    case <-time.After(1 * time.Second):
        fmt.Println("Timeout!") // after 1 second
    }
}
```

```
SELECT DECISION FLOW
======================

  select {
    case A: ...
    case B: ...
    case C: ...
    default: ...
  }

  Is A ready? ──YES──► execute A
      │
      NO
      │
  Is B ready? ──YES──► execute B
      │
      NO
      │
  Is C ready? ──YES──► execute C
      │
      NO
      │
  default present? ──YES──► execute default (no blocking)
      │
      NO
      │
  BLOCK until any case is ready
  (if multiple ready simultaneously → chosen randomly)
```

---

## 18. defer, panic, recover

### 18.1 defer — Deferred Execution

`defer` postpones a function call until the surrounding function returns. Deferred calls are executed in **LIFO order** (Last In, First Out).

```go
package main

import "fmt"

func main() {
    // ── Basic defer ───────────────────────────────────────────
    defer fmt.Println("world") // runs LAST
    fmt.Println("hello")       // runs FIRST
    // Output: hello, world

    // ── LIFO order of multiple defers ─────────────────────────
    defer fmt.Println("one")   // runs 3rd
    defer fmt.Println("two")   // runs 2nd
    defer fmt.Println("three") // runs 1st
    fmt.Println("start")
    // Output: start, three, two, one

    // ── defer with function literal ───────────────────────────
    x := 10
    defer func() {
        fmt.Println("deferred x:", x) // captures x by REFERENCE
    }()
    x = 20
    // Output: "deferred x: 20" (sees the updated value)
}

// ── PRIMARY USE CASE: Resource cleanup ────────────────────────
func readFile(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close() // ALWAYS closes, even if we return early due to errors

    // process file...
    return nil
}

func lockExample() {
    mu.Lock()
    defer mu.Unlock() // always unlocks when function returns
    // do work...
}
```

### 18.2 panic and recover

```go
// ── panic — stops normal execution ───────────────────────────
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero!") // like throwing an exception
    }
    return a / b
}

// ── recover — catches panics ──────────────────────────────────
// MUST be called inside a deferred function to work
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered panic: %v", r)
        }
    }()
    result = divide(a, b)
    return
}

func main() {
    result, err := safeDiv(10, 0)
    if err != nil {
        fmt.Println("Error:", err) // "Error: recovered panic: division by zero!"
    }
    _ = result

    // Direct panic — no recover → program crashes with stack trace
    // panic("fatal error!")
}
```

```
panic/recover FLOW
====================

  Normal function call chain:
  main() → A() → B() → C() → panic!

  After panic:
  1. C()'s deferred functions run
  2. B()'s deferred functions run
     → if recover() called here: STOPS panic, returns nil
  3. A()'s deferred functions run (if panic not recovered)
  4. main()'s deferred functions run
  5. Program crashes with stack trace

  With recover in B():
  main() → A() → B() [panic stops here, recover called]
                  └──► B() returns normally with recovered error

  RULE: Use panic only for truly unrecoverable situations
        Use error values for expected failure cases
```

---

## 19. Packages & Modules

### 19.1 Package System

```
PACKAGE SYSTEM OVERVIEW
=========================

  Go Workspace
  │
  ├── go.mod          ← Module definition file
  ├── go.sum          ← Checksums for security
  │
  ├── main.go         package main
  │
  ├── internal/       ← Can only be imported by parent module
  │   └── helper.go   package internal
  │
  └── pkg/
      ├── math/
      │   └── math.go package math
      └── string/
          └── str.go  package string
```

```
go.mod FILE EXAMPLE
====================

  module github.com/username/myapp    ← module path

  go 1.21                             ← minimum Go version

  require (
      github.com/some/library v1.2.3  ← direct dependency
      golang.org/x/net v0.8.0         ← another dependency
  )
```

### 19.2 Common Standard Library Packages

```
KEY STANDARD LIBRARY PACKAGES
===============================

  fmt         — formatted I/O (Printf, Println, Sprintf, Errorf)
  os          — OS interface (Open, Create, Args, Exit, Getenv)
  io          — I/O primitives (Reader, Writer, Copy)
  bufio       — buffered I/O (Scanner, NewReader)
  strings     — string manipulation (Contains, Split, Join, ToUpper)
  strconv     — string conversions (Atoi, Itoa, ParseFloat, FormatBool)
  math        — math functions (Sqrt, Abs, Max, Min, Pi)
  sort        — sorting (Sort, Search, Slice)
  time        — time and duration (Now, Sleep, Parse, Format)
  errors      — error creation and wrapping (New, Is, As)
  log         — logging (Print, Fatal, Panic)
  net/http    — HTTP client and server
  encoding/json — JSON encoding/decoding
  sync        — synchronization (Mutex, WaitGroup, Once)
  context     — request cancellation and deadlines
  testing     — unit testing
  reflect     — runtime reflection
  regexp      — regular expressions
```

---

## 20. Closures & Anonymous Functions

### 20.1 What is a Closure?

A **closure** is a function that "closes over" variables from its enclosing scope — it captures and remembers those variables even after the outer function has returned.

```
CLOSURE MENTAL MODEL
======================

  func outer() func() int {
      count := 0        ← variable in outer's scope

      return func() int {  ← anonymous function (closure)
          count++           ← captures count from outer
          return count
      }
  }

  counter := outer()
  // outer() has returned, but 'count' variable still exists
  // because the returned closure holds a reference to it!

  counter() → 1
  counter() → 2
  counter() → 3

  MEMORY:
  ┌─────────────────────────────────────────┐
  │  counter (closure) → ┌─────────────┐   │
  │                       │ function ptr │   │
  │                       │ captured env:│   │
  │                       │   count = 3  │   │
  │                       └─────────────┘   │
  └─────────────────────────────────────────┘
```

```go
package main

import "fmt"

// ── Counter using closure ─────────────────────────────────────
func makeCounter() func() int {
    count := 0
    return func() int {
        count++
        return count
    }
}

// ── Each closure has its OWN captured environment ─────────────
func main() {
    counter1 := makeCounter()
    counter2 := makeCounter()

    fmt.Println(counter1()) // 1
    fmt.Println(counter1()) // 2
    fmt.Println(counter2()) // 1 — independent!
    fmt.Println(counter1()) // 3

    // ── Closure capturing loop variable — CLASSIC GOTCHA ──────
    funcs := make([]func(), 5)
    for i := 0; i < 5; i++ {
        i := i  // SHADOW i with a new variable (fix the gotcha)
        funcs[i] = func() {
            fmt.Println(i) // captures the shadowed i
        }
    }
    for _, f := range funcs {
        f() // prints 0, 1, 2, 3, 4 (correct!)
    }

    // WITHOUT the shadowing fix:
    // All closures capture the SAME i variable
    // When loop ends, i=5, all closures print 5!
}

// ── Memoization using closure ─────────────────────────────────
func memoize(f func(int) int) func(int) int {
    cache := make(map[int]int)
    return func(n int) int {
        if val, ok := cache[n]; ok {
            return val
        }
        result := f(n)
        cache[n] = result
        return result
    }
}
```

---

## 21. Type Assertions & Type Switches

### 21.1 Type Assertion

A **type assertion** extracts the concrete value from an interface.

```go
var i interface{} = "hello"

// ── Single return (panics if wrong type) ──────────────────────
s := i.(string)       // s = "hello"
// n := i.(int)       // PANIC: interface holds string, not int

// ── Two-return form (safe, no panic) ─────────────────────────
s2, ok := i.(string)  // ok = true, s2 = "hello"
n, ok  := i.(int)     // ok = false, n = 0 (zero value)

if ok {
    fmt.Println("It's a string:", s2)
}
```

### 21.2 Type Switch

```go
func describe(i interface{}) {
    switch v := i.(type) {
    case int:
        fmt.Printf("int: %d\n", v)
    case string:
        fmt.Printf("string: %q (len %d)\n", v, len(v))
    case bool:
        fmt.Printf("bool: %t\n", v)
    case []int:
        fmt.Printf("[]int: %v\n", v)
    case nil:
        fmt.Println("nil!")
    default:
        fmt.Printf("unknown type: %T\n", v)
    }
}

describe(42)
describe("hello")
describe(true)
describe(nil)
describe(3.14)
```

---

## 22. Embedding

### 22.1 Composition via Embedding

Go uses **embedding** instead of inheritance. You embed one type inside another, and the outer type gets access to the embedded type's methods and fields directly.

```go
package main

import "fmt"

// ── Base type ────────────────────────────────────────────────
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " makes a sound"
}

// ── Embedding Animal in Dog ───────────────────────────────────
type Dog struct {
    Animal         // embedded (NOT a named field)
    Breed string
}

func (d Dog) Speak() string {    // Dog OVERRIDES Animal.Speak
    return d.Name + " barks!"
}

// ── Embedding with interface satisfaction ─────────────────────
type Logger struct{}

func (l Logger) Log(msg string) {
    fmt.Println("[LOG]:", msg)
}

type Service struct {
    Logger         // Service gets Log() method automatically
    Name string
}

func main() {
    d := Dog{
        Animal: Animal{Name: "Rex"},
        Breed:  "Labrador",
    }

    fmt.Println(d.Speak())       // "Rex barks!" (Dog's method)
    fmt.Println(d.Animal.Speak()) // "Rex makes a sound" (explicit)
    fmt.Println(d.Name)          // "Rex" — promoted from Animal!
    fmt.Println(d.Breed)         // "Labrador"

    s := Service{Name: "UserService"}
    s.Log("service started") // promoted Log() from Logger!
}
```

```
EMBEDDING vs INHERITANCE
==========================

  Inheritance (Java/Python):
  ─────────────────────────
  Dog IS-A Animal
  Dog inherits Animal's implementation
  Tight coupling — changes in Animal affect Dog

  Embedding (Go):
  ───────────────
  Dog HAS-A Animal (composition)
  Dog gets Animal's methods promoted
  Can override by defining same method
  Loose coupling — more flexible

  Mental model: Embedding is "copy-pasting" the embedded
  type's method set into the outer type's method set.
```

---

## 23. Goroutine Scheduler — GMP Model

### 23.1 The GMP Model

Go's runtime uses a scheduler called the **GMP model** to manage goroutines efficiently.

```
GMP MODEL — COMPLETE ARCHITECTURE
===================================

  G = Goroutine (the work)
  M = Machine (OS thread)
  P = Processor (execution context, runs goroutines)

  ┌─────────────────────────────────────────────────────────────┐
  │                    GO RUNTIME SCHEDULER                     │
  │                                                             │
  │  Global Run Queue (GRQ)                                     │
  │  ┌─────────────────────────────────────────────────────┐   │
  │  │  G7  G8  G9  G10  ...                               │   │
  │  └─────────────────────────────────────────────────────┘   │
  │                                                             │
  │  ┌─────────────┐        ┌─────────────┐                    │
  │  │      P1     │        │      P2     │                    │
  │  │             │        │             │                    │
  │  │ Local Queue │        │ Local Queue │                    │
  │  │ [G1,G2,G3] │        │ [G4,G5,G6] │                    │
  │  │             │        │             │                    │
  │  │ Running: G1 │        │ Running: G4 │                    │
  │  └──────┬──────┘        └──────┬──────┘                    │
  │         │                      │                            │
  │         ▼                      ▼                            │
  │       [M1]                   [M2]                           │
  │   OS Thread 1            OS Thread 2                        │
  │         │                      │                            │
  │         ▼                      ▼                            │
  │      CPU Core 1           CPU Core 2                        │
  └─────────────────────────────────────────────────────────────┘

  WORK STEALING:
  When P1's local queue is empty:
  P1 steals HALF of P2's local queue → keeps all CPUs busy!
```

### 23.2 Key Scheduler Behaviors

```
SCHEDULER PREEMPTION
======================

  Old Go (< 1.14): Cooperative preemption
  ─────────────────────────────────────────
  Goroutine runs until it calls a function or blocks
  Long CPU-bound loops could starve other goroutines

  New Go (≥ 1.14): Asynchronous preemption
  ──────────────────────────────────────────
  Scheduler can preempt goroutines at ANY point
  Every 10ms, OS sends signal, scheduler can switch
  Solves the CPU-bound starvation problem

GOMAXPROCS
===========
  Controls how many OS threads (P's) can run simultaneously
  Default: number of CPU cores on the machine

  import "runtime"
  runtime.GOMAXPROCS(4)  // use 4 OS threads
  runtime.GOMAXPROCS(1)  // single-threaded (forces sequential)
```

---

## 24. Memory Management

### 24.1 Stack vs Heap

```
STACK vs HEAP IN GO
====================

  STACK:
  ──────
  • Each goroutine has its own stack
  • Starts at ~2KB, grows to ~1GB max
  • Allocation/deallocation is O(1) — just move stack pointer
  • Variables with known lifetime at compile time → stack
  • When function returns, stack frame is gone

  HEAP:
  ─────
  • Shared across all goroutines
  • Garbage collected
  • Allocation is more expensive
  • Variables that "escape" to heap → garbage collected

  ESCAPE ANALYSIS:
  ─────────────────
  The compiler decides: does this variable need to outlive
  the function? If YES → allocate on heap. If NO → stack.

  // This may allocate on heap (escapes via return):
  func newInt() *int {
      x := 42
      return &x  // x must survive beyond this function → HEAP
  }

  // This stays on stack (doesn't escape):
  func stackOnly() int {
      x := 42
      return x   // copy of value returned → STACK
  }

  // Check with: go build -gcflags="-m" ./...
```

### 24.2 Garbage Collector

```
GO GARBAGE COLLECTOR
======================

  Type: Tri-color mark-and-sweep, concurrent

  PHASES:
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  1. MARK ROOTS (STW — Stop The World, very brief)   │
  │     • Pause all goroutines                           │
  │     • Mark goroutine stacks, globals as roots        │
  │     • Resume goroutines                              │
  │                                                      │
  │  2. CONCURRENT MARK                                  │
  │     • GC goroutines run alongside your code          │
  │     • Mark all reachable objects                     │
  │     • Write barrier tracks new references            │
  │                                                      │
  │  3. MARK TERMINATION (STW — brief)                  │
  │     • Final cleanup                                  │
  │                                                      │
  │  4. SWEEP (concurrent)                               │
  │     • Free unmarked objects                          │
  │     • Running concurrently with your code            │
  │                                                      │
  └──────────────────────────────────────────────────────┘

  TRI-COLOR ALGORITHM:
  ─────────────────────
  WHITE: not yet visited (candidates for collection)
  GREY:  visited but children not yet scanned
  BLACK: visited, children scanned (definitely reachable)

  Start: everything WHITE
  Mark roots GREY
  Process GREY: mark as BLACK, mark children GREY
  End: WHITE objects are unreachable → free them!

  GC TUNING:
  ──────────
  GOGC environment variable (default: 100)
  GOGC=100 means: trigger GC when heap grows 100% over last collection
  GOGC=200 → GC runs less often (more memory, less CPU)
  GOGC=50  → GC runs more often (less memory, more CPU)
  GOGC=off → disable GC entirely
```

---

## 25. Concurrency Patterns

### 25.1 Mutex — Mutual Exclusion

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    mu sync.Mutex  // protects Count
    Count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()         // acquire lock — only one goroutine can be here
    defer c.mu.Unlock() // release when done
    c.Count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.Count
}

func main() {
    counter := &SafeCounter{}
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }

    wg.Wait()
    fmt.Println(counter.Value()) // 1000 (always, with mutex)
}

// ── RWMutex — multiple readers, one writer ────────────────────
type Cache struct {
    mu   sync.RWMutex
    data map[string]int
}

func (c *Cache) Read(key string) int {
    c.mu.RLock()   // multiple goroutines can RLock simultaneously
    defer c.mu.RUnlock()
    return c.data[key]
}

func (c *Cache) Write(key string, val int) {
    c.mu.Lock()    // exclusive lock — blocks all readers and writers
    defer c.mu.Unlock()
    c.data[key] = val
}
```

### 25.2 sync.Once — Run Exactly Once

```go
// Use case: Singleton initialization, lazy loading
var (
    instance *Database
    once     sync.Once
)

func GetDatabase() *Database {
    once.Do(func() {
        instance = &Database{} // runs exactly once, even with 1000 goroutines
        instance.Connect()
    })
    return instance
}
```

### 25.3 Context — Cancellation & Deadlines

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func doWork(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("work cancelled:", ctx.Err())
            return
        default:
            fmt.Println("working...")
            time.Sleep(100 * time.Millisecond)
        }
    }
}

func main() {
    // ── WithTimeout ──────────────────────────────────────────
    ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
    defer cancel() // always call cancel to release resources!

    go doWork(ctx)
    time.Sleep(1 * time.Second)

    // ── WithCancel ───────────────────────────────────────────
    ctx2, cancel2 := context.WithCancel(context.Background())
    go doWork(ctx2)
    time.Sleep(300 * time.Millisecond)
    cancel2() // manually cancel

    // ── WithValue — pass request-scoped data ─────────────────
    type key string
    ctx3 := context.WithValue(context.Background(), key("userID"), 42)
    userID := ctx3.Value(key("userID")).(int)
    fmt.Println("userID:", userID)

    time.Sleep(200 * time.Millisecond)
}
```

```
CONTEXT PROPAGATION
====================

  HTTP Request arrives
        │
        ▼
  ctx = context.WithTimeout(parentCtx, 5*time.Second)
        │
        ├──► Database query (passes ctx)
        │         └── respects timeout
        │
        ├──► Cache lookup (passes ctx)
        │         └── respects timeout
        │
        └──► External API call (passes ctx)
                  └── respects timeout

  If client disconnects or timeout fires:
  ctx.Done() channel closes → ALL operations get notified!
```

---

## 26. Common Interview Traps & Gotchas

### 26.1 The Loop Closure Gotcha

```go
// ── WRONG ─────────────────────────────────────────────────────
funcs := make([]func(), 3)
for i := 0; i < 3; i++ {
    funcs[i] = func() {
        fmt.Println(i)  // captures i by REFERENCE
    }
}
for _, f := range funcs {
    f() // prints 3, 3, 3 (not 0, 1, 2!)
}
// i = 3 after loop, all closures see i = 3

// ── FIX 1: Shadow the variable ─────────────────────────────
for i := 0; i < 3; i++ {
    i := i  // new i for each iteration
    funcs[i] = func() { fmt.Println(i) }
}

// ── FIX 2: Pass as argument ───────────────────────────────
for i := 0; i < 3; i++ {
    funcs[i] = func(n int) func() {
        return func() { fmt.Println(n) }
    }(i) // immediately invoked with current i
}
```

### 26.2 Nil Interface vs Nil Pointer

```go
// TRICKY: A non-nil interface can hold a nil pointer!
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func mayFail(fail bool) error {
    var err *MyError  // typed nil pointer
    if fail {
        err = &MyError{msg: "failed!"}
    }
    return err  // returns *MyError(nil) wrapped in error interface
    // NOT a nil interface! Interface has type=*MyError, value=nil
}

err := mayFail(false)
if err != nil {  // This is TRUE! Interface is not nil!
    fmt.Println("unexpected error:", err)
}

// FIX: return untyped nil
func mayFailFixed(fail bool) error {
    if fail {
        return &MyError{msg: "failed!"}
    }
    return nil  // untyped nil → nil interface
}
```

### 26.3 Slice Append & Sharing Gotcha

```go
a := make([]int, 3, 6) // len=3, cap=6
a[0], a[1], a[2] = 1, 2, 3

b := a         // b shares the same backing array
b = append(b, 4) // within capacity — uses same array!
// Now array has [1,2,3,4]

// a still has len=3, but underlying array has 4!
// This can lead to surprising bugs:
a = append(a, 99) // writes to position [3] of same array
fmt.Println(b[3]) // 99! (not 4 anymore!)

// FIX: Use copy to make independent slice
b := make([]int, len(a))
copy(b, a)
```

### 26.4 Map Concurrent Access

```go
// ── WRONG: concurrent map access PANICS ──────────────────────
m := map[string]int{}
go func() { m["key"] = 1 }()
go func() { _ = m["key"]  }()
// "fatal error: concurrent map read and map write"

// ── FIX 1: sync.Mutex ─────────────────────────────────────
var mu sync.Mutex
mu.Lock()
m["key"] = 1
mu.Unlock()

// ── FIX 2: sync.Map (built for concurrent use) ─────────────
var sm sync.Map
sm.Store("key", 1)
v, _ := sm.Load("key")
fmt.Println(v) // 1
```

### 26.5 defer in Loop

```go
// ── WRONG: defer in loop delays ALL until function returns! ──
func processFiles(files []string) error {
    for _, f := range files {
        file, _ := os.Open(f)
        defer file.Close() // BAD! All closes happen when function returns
        // Not when each iteration ends!
        process(file)
    }
}

// ── FIX: Use closure or named function ─────────────────────
func processFiles(files []string) error {
    for _, f := range files {
        func(path string) {
            file, _ := os.Open(path)
            defer file.Close() // closes when this inner func returns
            process(file)
        }(f)
    }
}
```

---

## 27. Interview Questions — Q&A Deep Dive

### Q1: What is the difference between `var` and `:=`?

```
var:
• Can be used at PACKAGE level and inside functions
• Explicitly typed or type-inferred
• Initializes to zero value if no value given

:=  (short variable declaration):
• Can ONLY be used inside functions
• MUST have initial value (type inferred)
• At least one variable on left must be NEW

Example where := shines:
  result, err := doSomething()  // both new
  result2, err := doSomethingElse()  // result2 is new, err is reassigned
```

### Q2: What is the difference between a slice and an array?

```
Array:
• Fixed size, part of the TYPE: [5]int ≠ [6]int
• Value type (copied when assigned)
• Stack allocated (usually)

Slice:
• Dynamic size, reference type
• Has 3 fields: ptr, len, cap
• Shares backing array
• nil slice and empty slice behave similarly
• append() may or may not reallocate
```

### Q3: How does Go achieve concurrency?

```
Go's concurrency model:
1. Goroutines — lightweight user-space threads
2. Channels — typed communication pipes
3. select — multiplexing channels
4. sync package — mutexes, WaitGroup, Once, etc.
5. GMP scheduler — M:N threading model
6. context — propagate cancellation signals

Go follows CSP (Communicating Sequential Processes)
"Don't communicate by sharing memory,
 share memory by communicating"
```

### Q4: What is a nil channel and what happens when you use it?

```go
var ch chan int  // nil channel

// Sending to nil channel: blocks forever
go func() { ch <- 1 }() // goroutine blocks forever

// Receiving from nil channel: blocks forever
val := <-ch   // blocks forever

// Closing a nil channel: PANICS
close(ch)  // panic!

// select with nil channel: that case is NEVER selected
select {
case v := <-ch:  // never chosen if ch is nil
    fmt.Println(v)
case <-done:
    return
}
// Useful! Set a channel to nil to disable a case in select.
```

### Q5: Explain Go's interface satisfaction rule.

```
A type T implements interface I if:
• T has ALL the methods in I
• Method signatures match EXACTLY

Pointer vs Value receiver interface satisfaction:
──────────────────────────────────────────────────
If T has value receiver methods → *T also satisfies the interface
If T has pointer receiver methods → only *T satisfies the interface

type Stringer interface { String() string }

type A struct{}
func (a A) String() string { return "A" }    // value receiver

var s Stringer
s = A{}   // OK: A satisfies Stringer
s = &A{}  // OK: *A also satisfies Stringer

type B struct{}
func (b *B) String() string { return "B" }  // pointer receiver

s = &B{}  // OK: *B satisfies Stringer
s = B{}   // COMPILE ERROR: B does not satisfy Stringer
```

### Q6: What is a goroutine leak and how do you prevent it?

```go
// Goroutine leak: goroutine blocked permanently with no way to exit
// ── LEAKING goroutine ──────────────────────────────────────────
func leakyFunction() {
    ch := make(chan int)
    go func() {
        val := heavyComputation()
        ch <- val  // blocks forever if no one receives!
    }()
    // Function returns without reading from ch
    // Goroutine is stuck sending forever → LEAK!
}

// ── FIX: Use context for cancellation ─────────────────────────
func fixedFunction(ctx context.Context) {
    ch := make(chan int, 1)  // buffered (won't block even if no receiver)
    go func() {
        select {
        case ch <- heavyComputation():
        case <-ctx.Done():
            return  // exit if context cancelled
        }
    }()
}

// Prevention checklist:
// ✓ Always have a way to exit goroutines
// ✓ Use context for cancellation
// ✓ Use buffered channels when receiver might not read
// ✓ Use done channels to signal termination
// ✓ Use goleak library in tests to detect leaks
```

### Q7: What is the difference between buffered and unbuffered channels?

```
UNBUFFERED: make(chan T)
────────────────────────
• Synchronous: sender blocks until receiver reads
• Both goroutines must be ready at the same moment
• Guarantees: sender knows receiver got the value
• Use for: synchronization, guaranteed handoff

BUFFERED: make(chan T, N)
──────────────────────────
• Asynchronous: sender only blocks when buffer is full
• Receiver only blocks when buffer is empty
• N items can be "in flight" without blocking
• Use for: decoupling producer/consumer speeds
           rate limiting, work queues

ANALOGY:
Unbuffered = phone call (both must be present)
Buffered   = email (sender sends, receiver reads later)
```

### Q8: How does defer work with return values?

```go
// Named return values + defer can modify return values!
func double(n int) (result int) {
    defer func() {
        result *= 2  // modifies the named return value!
    }()
    result = n
    return  // naked return: returns result (will be doubled by defer)
}

fmt.Println(double(5))  // 10 (not 5!)

// With unnamed return:
func doubleUnnamed(n int) int {
    defer func() {
        n *= 2  // modifies local n, NOT the return value
    }()
    return n  // return copies n into return slot BEFORE defer runs
}
fmt.Println(doubleUnnamed(5))  // 5 (not 10!)
```

### Q9: What are the zero values of each type?

```
int, uint, float   → 0
bool               → false
string             → "" (empty)
pointer            → nil
slice              → nil  (but len=0, safe to range)
map                → nil  (read is ok, write PANICS)
channel            → nil
function           → nil
interface          → nil
struct             → all fields get their zero values
```

### Q10: Explain how Go handles errors from multiple goroutines.

```go
package main

import (
    "fmt"
    "sync"
)

// errgroup pattern (golang.org/x/sync/errgroup)
func processItems(items []int) error {
    var (
        mu      sync.Mutex
        firstErr error
        wg      sync.WaitGroup
    )

    for _, item := range items {
        wg.Add(1)
        go func(item int) {
            defer wg.Done()
            if err := processItem(item); err != nil {
                mu.Lock()
                if firstErr == nil {
                    firstErr = err  // capture first error
                }
                mu.Unlock()
            }
        }(item)
    }

    wg.Wait()
    return firstErr
}

// Better: Use errgroup from golang.org/x/sync
import "golang.org/x/sync/errgroup"

func processItemsErrgroup(items []int) error {
    g := new(errgroup.Group)
    for _, item := range items {
        item := item
        g.Go(func() error {
            return processItem(item)
        })
    }
    return g.Wait() // returns first non-nil error
}
```

---

## APPENDIX A: Go Keywords (25 total)

```
break       default      func         interface    select
case        defer        go           map          struct
chan        else         goto         package      switch
const       fallthrough  if           range        type
continue    for          import       return       var
```

## APPENDIX B: Built-in Functions

```
BUILT-IN FUNCTIONS
===================

  Allocation:  new(T)          → *T (zero-initialized)
               make(T, args)   → T  (for slice, map, chan)

  Slices:      append(s, v...) → slice
               copy(dst, src)  → int (elements copied)
               len(s)          → int
               cap(s)          → int

  Maps:        delete(m, k)
               len(m)          → int

  Channels:    close(ch)
               len(ch)         → int (elements in buffer)
               cap(ch)         → int (buffer capacity)

  Strings:     len(s)          → int (bytes, not characters!)

  Type:        real(c)         → float (complex number real part)
               imag(c)         → float (complex number imag part)
               complex(r,i)    → complex

  Panic:       panic(v)
               recover()       → interface{}

  Print:       print(v...)     → (low-level, avoid in production)
               println(v...)   → (low-level, avoid in production)
```

## APPENDIX C: Formatting Verbs

```
COMMON fmt VERBS
=================

  %v    default format
  %+v   struct with field names
  %#v   Go-syntax representation
  %T    type of the value

  %d    integer (decimal)
  %b    integer (binary)
  %o    integer (octal)
  %x    integer (hex lowercase)
  %X    integer (hex uppercase)

  %f    float (decimal)
  %e    float (scientific notation)
  %g    compact: %e or %f

  %s    string
  %q    quoted string
  %p    pointer address

  %t    boolean
  %c    character (rune)
```

## APPENDIX D: Testing in Go

```go
// file: math_test.go (must end with _test.go)
package math

import "testing"

func TestAdd(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2,3) = %d; want 5", result)
    }
}

// Table-driven tests — Go's idiomatic testing pattern
func TestAddTable(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 2, 3, 5},
        {"negative", -1, -1, -2},
        {"zero", 0, 0, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Add(tt.a, tt.b)
            if result != tt.expected {
                t.Errorf("Add(%d,%d) = %d; want %d",
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}

// Benchmark
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(1, 2)
    }
}

// Run tests:   go test ./...
// Run verbose: go test -v ./...
// Run bench:   go test -bench=. ./...
// Race detect: go test -race ./...
```

---

## MENTAL MODELS FOR MASTERY

```
KEY MENTAL MODELS
==================

  1. "Goroutines are cheap threads"
     Think of goroutines as tasks, not threads.
     Launch thousands without guilt.

  2. "Channels are typed queues with synchronization"
     Use them to pass ownership of data between goroutines.

  3. "Interfaces are behavior contracts"
     Define what a type can DO, not what it IS.

  4. "Errors are values, not exceptions"
     Handle them explicitly. Propagate with context using %w.

  5. "Zero values are your friends"
     Go initializes everything. Use this to simplify code.

  6. "Composition over inheritance"
     Use embedding and interfaces instead of class hierarchies.

  7. "Defer = cleanup registration"
     Register cleanup at point of resource acquisition.
     Think: open file → immediately defer close.

  8. "select = channel switch"
     Use to wait on multiple channels or implement timeouts.

  9. "context = request lifecycle"
     Pass context.Context as first arg to propagate
     deadlines, cancellation, and values down call chains.

  10. "Slice = window into array"
      Slices share backing arrays. Use copy() for independence.
```

---

*End of Guide — Go deeply, build boldly* 🐹

I'll create a comprehensive, in-depth Golang interview guide as a `.md` file. This is going to be extensive — covering every core concept with ASCII diagrams and Go code.Here's your complete **3,229-line** Golang Interview Guide. Here's what's covered, and the reasoning behind the structure:

---

## What's Inside — Topic by Topic

**Foundations** (Sections 1–6): Program structure, execution order (`init()` → `main()`), all 4 variable declaration forms, `iota` constant generation, every built-in type with memory sizes, and all control flow patterns — including the fact that `for` is Go's *only* loop keyword.

**Core Language** (Sections 7–14): Functions with multiple return values, named returns, variadic params. Pointers with memory diagrams showing address vs value. Deep-dive on slices — the 3-field internal structure (`ptr | len | cap`), append growth, the sharing-trap gotcha, and `copy()`. Maps as hash tables, the comma-ok idiom, and using `map[T]struct{}` as a set. Structs with memory alignment/padding layout, struct tags for JSON/DB. Methods with value vs pointer receiver decision rules. Interfaces — implicit satisfaction, internal two-word representation, the empty interface (`any`). Error handling as values, `errors.Is` / `errors.As`, wrapping with `%w`.

**Concurrency** (Sections 15–17): Goroutines vs OS threads (cost comparison table). Channels — unbuffered vs buffered with the phone-call/email analogy, directional channels, pipeline pattern. Select for multiplexing with decision flowchart.

**Advanced** (Sections 18–24): `defer` LIFO order, `panic`/`recover` flow. Packages, modules, `go.mod`. Closures capturing variables + the classic loop closure gotcha. Type assertions, type switches. Embedding as composition-over-inheritance. **GMP Scheduler model** with ASCII architecture diagram showing work-stealing. Memory: stack vs heap, escape analysis, tri-color mark-and-sweep GC explained.

**Interview Mastery** (Sections 25–27): Mutex, RWMutex, `sync.Once`, `context` propagation. 10 common gotchas with fixes. 10 deep Q&A covering nil interface trap, defer + named returns, goroutine leaks — the trickiest questions interviewers love.