# 🧠 Golang Functions — A Complete Mastery Guide

> **Philosophy**: A function is not just a block of code — it is a *contract*, a *unit of thought*, and the fundamental building block of every abstraction in Go. Mastering functions in Go means understanding memory, the stack, the heap, the type system, closures, and the Go runtime itself.

---

## Table of Contents

1. [What is a Function?](#1-what-is-a-function)
2. [Function Anatomy in Go](#2-function-anatomy-in-go)
3. [Parameters — Passing Values](#3-parameters--passing-values)
4. [Return Values](#4-return-values)
5. [Named Return Values](#5-named-return-values)
6. [Multiple Return Values](#6-multiple-return-values)
7. [Variadic Functions](#7-variadic-functions)
8. [Functions as First-Class Citizens](#8-functions-as-first-class-citizens)
9. [Anonymous Functions (Function Literals)](#9-anonymous-functions-function-literals)
10. [Closures — The Deep Dive](#10-closures--the-deep-dive)
11. [Defer — Execution Ordering](#11-defer--execution-ordering)
12. [Panic and Recover](#12-panic-and-recover)
13. [Methods vs Functions](#13-methods-vs-functions)
14. [Function Types](#14-function-types)
15. [Higher-Order Functions](#15-higher-order-functions)
16. [Recursion — Theory and Practice](#16-recursion--theory-and-practice)
17. [Tail Recursion and Why Go Doesn't Optimize It](#17-tail-recursion-and-why-go-doesnt-optimize-it)
18. [Init Functions](#18-init-functions)
19. [Blank Identifier in Functions](#19-blank-identifier-in-functions)
20. [Inline Functions and Compiler Inlining](#20-inline-functions-and-compiler-inlining)
21. [Function Signatures and Interface Satisfaction](#21-function-signatures-and-interface-satisfaction)
22. [Goroutines and Functions](#22-goroutines-and-functions)
23. [Memory Model — Stack vs Heap for Functions](#23-memory-model--stack-vs-heap-for-functions)
24. [Error Handling Patterns in Functions](#24-error-handling-patterns-in-functions)
25. [Functional Programming Patterns in Go](#25-functional-programming-patterns-in-go)
26. [Performance Optimization Techniques](#26-performance-optimization-techniques)
27. [Testing Functions](#27-testing-functions)
28. [DSA-Focused Function Patterns](#28-dsa-focused-function-patterns)
29. [Mental Models and Cognitive Frameworks](#29-mental-models-and-cognitive-frameworks)
30. [Cheat Sheet](#30-cheat-sheet)

---

## 1. What is a Function?

### Conceptual Definition

A **function** is a named, reusable block of code that:
- Accepts zero or more **inputs** (parameters)
- Executes a sequence of statements
- Returns zero or more **outputs**

Think of a function as a **mathematical mapping**: `f: Input → Output`

```
Input Domain ──► [ Function Body ] ──► Output Codomain
  (args)                                  (return values)
```

### Why Functions Exist — Cognitive Science Angle

> **Chunking** (George Miller, 1956): The human brain can hold 7±2 items in working memory. Functions let you *chunk* complexity — you give a name to a chunk of logic and treat it as a single mental unit. This is why top programmers write small, well-named functions.

Functions serve:
1. **Abstraction** — hide *how* something works, expose *what* it does
2. **Reusability** — write once, use many times
3. **Testability** — isolated units are easier to verify
4. **Composability** — build bigger programs from smaller pieces
5. **Readability** — named intent is clearer than raw logic

---

## 2. Function Anatomy in Go

### Syntax Breakdown

```
func   FunctionName  (param1 type1, param2 type2)  (returnType1, returnType2)  {
 ↑          ↑                ↑                              ↑                      ↑
keyword    name          parameter list              return type list           body
}
```

### Minimal Example

```go
package main

import "fmt"

// add takes two integers and returns their sum.
// Signature: func(int, int) int
func add(a int, b int) int {
    return a + b
}

func main() {
    result := add(3, 5)
    fmt.Println(result) // 8
}
```

### ASCII Call Stack Visualization

```
main() calls add(3, 5)
─────────────────────────────────────
Stack grows downward ↓

| main stack frame  |
|   result = ?      |   ← waiting for return
|───────────────────|
| add stack frame   |
|   a = 3           |
|   b = 5           |
|   return 8        |   ← computed
|───────────────────|
↓ add returns, frame is popped
| main stack frame  |
|   result = 8      |   ← filled in
─────────────────────────────────────
```

### Function Naming Conventions

| Convention | Example | Use |
|---|---|---|
| camelCase | `calculateSum` | Private (unexported) |
| PascalCase | `CalculateSum` | Public (exported) |
| Short, verb-based | `parse`, `read`, `get` | Idiomatic Go |
| Avoid redundancy | `user.Name()` not `user.GetName()` | Go idiom |

---

## 3. Parameters — Passing Values

### Go is ALWAYS Pass-by-Value

This is the **most critical concept** to internalize. When you pass a variable to a function in Go, a **copy** of that value is made.

```go
package main

import "fmt"

func doubleIt(x int) {
    x = x * 2  // modifies the COPY, not the original
    fmt.Println("Inside:", x)
}

func main() {
    n := 10
    doubleIt(n)
    fmt.Println("Outside:", n) // still 10!
}
```

**Output:**
```
Inside: 20
Outside: 10
```

### ASCII Memory Diagram — Pass by Value

```
BEFORE call:
  main frame:  n = 10
                │
                │ copy is made
                ▼
  doubleIt frame: x = 10  (separate memory location)
                  x = 20  (only this copy changes)

AFTER return:
  main frame:  n = 10  (unchanged)
```

### Passing a Pointer (Simulating Pass-by-Reference)

To mutate the caller's variable, pass a **pointer** — the memory address of the variable.

**What is a pointer?**  
A pointer is a variable that stores the *memory address* of another variable, not the value itself.

```
Variable n at address 0xc000014080 holds value 10
Pointer p at address 0xc000014090 holds value 0xc000014080
```

```go
package main

import "fmt"

// *int means "pointer to int"
// &n means "address of n"
func doubleIt(x *int) {
    *x = *x * 2  // dereference: go to the address, change the value there
    fmt.Println("Inside:", *x)
}

func main() {
    n := 10
    doubleIt(&n)             // pass the address of n
    fmt.Println("Outside:", n) // 20 — n was modified!
}
```

### ASCII Pointer Diagram

```
main frame:
  n = 10   at address 0xAA

doubleIt frame:
  x = 0xAA  ← x is a pointer, holds the ADDRESS of n
  *x = 20   ← go to address 0xAA, write 20

After return:
  n at 0xAA = 20  ✓
```

### Parameter Grouping (Shorthand)

```go
// Verbose:
func add(a int, b int) int { ... }

// Shorthand (same type, group them):
func add(a, b int) int { ... }

// Multiple groups:
func transform(x, y float64, name string, flag bool) {}
```

### Passing Slices, Maps, and Channels

These are **reference types** — they contain an internal pointer to underlying data. Passing them copies the *header* (pointer + len + cap), not the data.

```go
package main

import "fmt"

func appendElement(s []int, val int) []int {
    // s is a copy of the slice header
    // but it points to the same underlying array (until reallocation)
    return append(s, val)
}

func modifyFirst(s []int) {
    s[0] = 999  // modifies the underlying array — caller sees this!
}

func main() {
    original := []int{1, 2, 3}
    modifyFirst(original)
    fmt.Println(original) // [999 2 3] — mutation visible!

    result := appendElement(original, 4)
    fmt.Println(result) // [999 2 3 4]
}
```

### Slice Header Visualization

```
Slice header (copied on function call):
┌──────────┬─────┬─────┐
│  ptr     │ len │ cap │
│ 0xABCD   │  3  │  6  │
└──────────┴─────┴─────┘
    │
    ▼
Underlying array (shared!):
┌───┬───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │   │   │   │
└───┴───┴───┴───┴───┴───┘
```

---

## 4. Return Values

### Single Return

```go
func square(n int) int {
    return n * n
}
```

### No Return (void equivalent)

```go
func greet(name string) {
    fmt.Printf("Hello, %s!\n", name)
    // no return statement needed (or use bare `return`)
}
```

### Early Return Pattern

```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")  // early return on error
    }
    return a / b, nil
}
```

### Return Value Decision Tree

```
Does the function produce a value?
│
├── YES ─► Does it always succeed?
│           ├── YES ─► return the value directly
│           └── NO  ─► return (value, error)
│
└── NO  ─► Does it need to signal failure?
            ├── YES ─► return error (or bool)
            └── NO  ─► no return (void)
```

---

## 5. Named Return Values

Go allows you to name return values. They act as pre-declared variables within the function.

```go
package main

import "fmt"

// sum and count are named return variables
// automatically initialized to zero values (0, 0)
func stats(nums []int) (sum int, count int) {
    for _, n := range nums {
        sum += n     // sum is a local variable here
        count++
    }
    return  // "naked return" — returns current values of sum and count
}

func main() {
    s, c := stats([]int{1, 2, 3, 4, 5})
    fmt.Printf("Sum: %d, Count: %d\n", s, c) // Sum: 15, Count: 5
}
```

### Named Returns Flow

```
func stats(nums []int) (sum int, count int)
                         │           │
                         ▼           ▼
              sum = 0 (zero value)   count = 0 (zero value)
              
              ... logic runs ...
              
              bare `return`
                ├── returns current value of sum
                └── returns current value of count
```

### When to Use Named Returns

**Good use case** — documentation and defer interaction:
```go
func readFile(path string) (content string, err error) {
    f, err := os.Open(path)
    if err != nil {
        return  // returns "", err (already assigned above)
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr  // can modify named return in defer!
        }
    }()
    // ... read content
    return
}
```

**Avoid** named returns when the function is trivially short — they reduce clarity there.

---

## 6. Multiple Return Values

This is one of Go's most idiomatic and powerful features, especially for error handling.

```go
package main

import (
    "fmt"
    "strconv"
)

func parseAndDouble(s string) (int, error) {
    n, err := strconv.Atoi(s)  // Atoi returns (int, error)
    if err != nil {
        return 0, fmt.Errorf("parseAndDouble: %w", err)
    }
    return n * 2, nil
}

func main() {
    val, err := parseAndDouble("21")
    if err != nil {
        fmt.Println("Error:", err)
        return
    }
    fmt.Println(val) // 42
    
    _, err = parseAndDouble("abc") // use _ to discard value
    if err != nil {
        fmt.Println("Error:", err) // parseAndDouble: strconv.Atoi: parsing "abc": invalid syntax
    }
}
```

### Multiple Return Values — Data Flow

```
strconv.Atoi("21")
    │
    ├── success path ──► (21, nil)
    └── failure path ──► (0, &NumError{...})

Caller uses:
    val, err := ...
    ↑    ↑
    │    └── always check this first
    └────── use only if err == nil
```

---

## 7. Variadic Functions

**Variadic** means: accepts a variable number of arguments.

**What does `...T` mean?**  
`...T` in a parameter position means "zero or more arguments of type T". Inside the function, they are available as a slice `[]T`.

```go
package main

import "fmt"

// nums is []int inside the function
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

func main() {
    fmt.Println(sum())           // 0
    fmt.Println(sum(1))          // 1
    fmt.Println(sum(1, 2, 3))    // 6
    fmt.Println(sum(1, 2, 3, 4, 5)) // 15
    
    // Spread a slice using ...
    numbers := []int{10, 20, 30}
    fmt.Println(sum(numbers...)) // 60 ← spread operator
}
```

### Variadic + Fixed Parameters

```go
// Fixed params must come BEFORE variadic param
func logMessage(level string, parts ...string) {
    fmt.Printf("[%s] ", level)
    for _, p := range parts {
        fmt.Print(p, " ")
    }
    fmt.Println()
}

func main() {
    logMessage("INFO", "server", "started", "on", "port", "8080")
    // [INFO] server started on port 8080
}
```

### Memory Layout of Variadic Call

```
sum(1, 2, 3, 4, 5) call:

Compiler creates a temporary slice:
[]int{1, 2, 3, 4, 5}
 ptr=0xABCD  len=5  cap=5

Passed to function as:
  nums = []int{1, 2, 3, 4, 5}
```

### Variadic Decision Tree

```
Do you need a variable number of arguments?
│
├── YES ─► Is there exactly one type?
│           ├── YES ─► use ...T  (e.g., ...int)
│           └── NO  ─► use ...interface{} or ...any
│
└── NO  ─► use fixed parameters
```

---

## 8. Functions as First-Class Citizens

In Go, functions are **first-class values**. This means:

1. A function can be **assigned to a variable**
2. A function can be **passed as an argument** to another function
3. A function can be **returned from** another function
4. A function can be stored in a **data structure**

```go
package main

import "fmt"

// Assign function to variable
var double = func(n int) int { return n * 2 }

// Store functions in a map (dispatch table)
var operations = map[string]func(int, int) int{
    "add": func(a, b int) int { return a + b },
    "sub": func(a, b int) int { return a - b },
    "mul": func(a, b int) int { return a * b },
}

func apply(f func(int) int, val int) int {
    return f(val)
}

func main() {
    fmt.Println(double(5))           // 10
    fmt.Println(apply(double, 7))    // 14
    
    op := operations["add"]
    fmt.Println(op(3, 4))            // 7
    
    for name, fn := range operations {
        fmt.Printf("%s(10, 3) = %d\n", name, fn(10, 3))
    }
}
```

### Conceptual Model

```
In most languages:
  int, string, float → first-class (can be passed, returned, stored)
  function          → second-class (can only be called)

In Go:
  int, string, function → ALL first-class
  ↑ This enables functional programming patterns
```

---

## 9. Anonymous Functions (Function Literals)

An **anonymous function** is a function without a name. It is defined at the point of use.

```go
package main

import "fmt"

func main() {
    // Define and immediately invoke (IIFE — Immediately Invoked Function Expression)
    result := func(a, b int) int {
        return a + b
    }(3, 4) // ← immediately called with args 3, 4
    
    fmt.Println(result) // 7
    
    // Assign to variable and call later
    multiply := func(a, b int) int {
        return a * b
    }
    fmt.Println(multiply(6, 7)) // 42
    
    // Pass directly to another function
    nums := []int{5, 2, 8, 1, 9}
    fmt.Println(maxBy(nums, func(a, b int) bool {
        return a > b
    }))
}

func maxBy(nums []int, less func(a, b int) bool) int {
    if len(nums) == 0 {
        return 0
    }
    m := nums[0]
    for _, n := range nums[1:] {
        if less(n, m) {
            m = n
        }
    }
    return m
}
```

### IIFE Pattern Visualization

```
func(a, b int) int {   ← function definition
    return a + b
}(3, 4)                ← immediate call with arguments
│
▼
7                      ← result
```

---

## 10. Closures — The Deep Dive

### What is a Closure?

A **closure** is a function that *captures* (closes over) variables from its surrounding lexical scope. The function retains access to those variables even after the surrounding function has returned.

**Key insight**: A closure = function + its captured environment.

```go
package main

import "fmt"

func makeCounter() func() int {
    count := 0  // this variable lives in the closure's environment
    
    return func() int {
        count++   // captures and modifies `count` from outer scope
        return count
    }
}

func main() {
    counter := makeCounter()
    fmt.Println(counter()) // 1
    fmt.Println(counter()) // 2
    fmt.Println(counter()) // 3
    
    // Each call to makeCounter creates a NEW closure with its own `count`
    counter2 := makeCounter()
    fmt.Println(counter2()) // 1  ← independent!
    fmt.Println(counter())  // 4  ← continues from before
}
```

### Memory Layout of a Closure

```
makeCounter() returns:

  Closure object on heap:
  ┌─────────────────────────────┐
  │  func ptr → func() int body │
  │  env ptr  → ┌─────────────┐ │
  └─────────────│  count = 0  │─┘
                └─────────────┘
                    ↑
                    This variable is heap-allocated
                    because it escapes the stack frame
                    of makeCounter() (escape analysis)

When counter() is called:
  count is incremented via the env ptr
  count = 1, return 1
  
Next call:
  count = 2, return 2
  
(count persists between calls because it's on the heap)
```

### Classic Closure Bug (Loop Variable Capture)

```go
package main

import "fmt"

func main() {
    // ❌ BUG: All closures capture the same `i` variable
    funcs := make([]func(), 5)
    for i := 0; i < 5; i++ {
        funcs[i] = func() {
            fmt.Println(i) // captures reference to i, not its value
        }
    }
    for _, f := range funcs {
        f() // prints: 5 5 5 5 5 — all see the final value of i!
    }
}
```

### Fix 1: Shadow with a New Variable

```go
for i := 0; i < 5; i++ {
    i := i  // create a new `i` in each iteration's scope
    funcs[i] = func() {
        fmt.Println(i) // captures THIS iteration's i
    }
}
// prints: 0 1 2 3 4
```

### Fix 2: Pass as Argument

```go
for i := 0; i < 5; i++ {
    funcs[i] = func(val int) func() {
        return func() { fmt.Println(val) }
    }(i) // pass i as argument — copied by value
}
// prints: 0 1 2 3 4
```

### Fix 3 (Go 1.22+): Loop variable per-iteration semantics

In Go 1.22+, the loop variable `i` in a `for` loop is **new per iteration** by default (no fix needed for new code).

### Advanced Closure — Memoization

```go
package main

import "fmt"

// memoize wraps any func(int)int with caching
func memoize(f func(int) int) func(int) int {
    cache := make(map[int]int) // captured by closure
    
    return func(n int) int {
        if val, ok := cache[n]; ok {
            return val  // cache hit
        }
        result := f(n)
        cache[n] = result // store in shared cache
        return result
    }
}

func slowSquare(n int) int {
    // simulate expensive computation
    return n * n
}

func main() {
    fastSquare := memoize(slowSquare)
    
    fmt.Println(fastSquare(10)) // computed: 100
    fmt.Println(fastSquare(10)) // from cache: 100
    fmt.Println(fastSquare(7))  // computed: 49
}
```

### Closure Decision Tree

```
Do you need a function that:
│
├── Remembers state between calls? ──► use closure with captured variable
│
├── Varies behavior based on context? ──► capture context variable
│
├── Needs to modify outer scope? ──► capture by reference (default in Go)
│
└── Should be isolated per invocation? ──► pass as argument, not closure
```

---

## 11. Defer — Execution Ordering

### What is Defer?

`defer` schedules a function call to run **just before the surrounding function returns**, no matter how it returns (normal, early return, panic).

```go
package main

import "fmt"

func main() {
    fmt.Println("start")
    defer fmt.Println("deferred 1")
    defer fmt.Println("deferred 2")
    defer fmt.Println("deferred 3")
    fmt.Println("end")
}
```

**Output:**
```
start
end
deferred 3
deferred 2
deferred 1
```

### Defer is LIFO (Last In, First Out)

```
Defer stack (like a stack data structure):
  push deferred 1
  push deferred 2
  push deferred 3

On function return, pop the stack:
  pop deferred 3  ← last pushed, first executed
  pop deferred 2
  pop deferred 1  ← first pushed, last executed
```

### Arguments are Evaluated Immediately

```go
package main

import "fmt"

func main() {
    x := 10
    defer fmt.Println("x =", x) // x is evaluated NOW (= 10), not at deferred time
    x = 20
    fmt.Println("x is now", x)
}
```

**Output:**
```
x is now 20
x = 10          ← 10, not 20, because the argument was captured at defer time
```

### Defer for Resource Cleanup

```go
package main

import (
    "fmt"
    "os"
)

func readFile(path string) (string, error) {
    f, err := os.Open(path)
    if err != nil {
        return "", err
    }
    defer f.Close()  // guaranteed to run even if function panics or returns early
    
    // ... read the file
    buf := make([]byte, 1024)
    n, err := f.Read(buf)
    if err != nil {
        return "", err  // f.Close() still runs!
    }
    return string(buf[:n]), nil
}
```

### Defer + Named Returns (Modify Return Value)

```go
package main

import "fmt"

func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered from panic: %v", r)
        }
    }()
    
    result = a / b  // panics if b == 0
    return
}

func main() {
    r, err := safeDiv(10, 2)
    fmt.Println(r, err)  // 5 <nil>
    
    r, err = safeDiv(10, 0)
    fmt.Println(r, err)  // 0 recovered from panic: runtime error: integer divide by zero
}
```

### Defer Execution Flow

```
func example() (result int, err error)
│
├── defer funcA()   ← push to defer stack
├── defer funcB()   ← push to defer stack
├── ... logic ...
├── return 42, nil  ← trigger defer stack execution
│                    │
│                    ▼ (LIFO order)
│                    funcB() runs  ← can modify named return values
│                    funcA() runs
│
└── actual return to caller with (possibly modified) values
```

---

## 12. Panic and Recover

### Panic

`panic` stops the normal execution flow, unwinds the call stack (running deferred functions), and crashes the program unless recovered.

```go
package main

import "fmt"

func mustPositive(n int) int {
    if n <= 0 {
        panic(fmt.Sprintf("expected positive number, got %d", n))
    }
    return n
}

func main() {
    fmt.Println(mustPositive(5))   // 5
    fmt.Println(mustPositive(-1))  // panic: expected positive number, got -1
}
```

### Recover

`recover` can only be called inside a **deferred function**. It stops the panicking, and returns the panic value.

```go
package main

import "fmt"

func safeExecute(f func()) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic: %v", r)
        }
    }()
    f()
    return nil
}

func main() {
    err := safeExecute(func() {
        panic("something went wrong")
    })
    fmt.Println("Error:", err)  // Error: panic: something went wrong
    
    err = safeExecute(func() {
        fmt.Println("all good")
    })
    fmt.Println("Error:", err)  // all good \n Error: <nil>
}
```

### Panic/Recover Flow Diagram

```
Normal execution:
  A() → B() → C() → panic!
                      │
                      ▼ stack unwinds
                  C's defers run
                  B's defers run ← if B has recover() deferred, panic is caught here
                  A's defers run (if panic not recovered)
                  program crashes (if never recovered)

With recover in B's defer:
  A() → B() → C() → panic!
                      │
                ◄─────┘ (stack unwind starts)
               B's defer: recover() returns panic value
               panic is STOPPED here
               B returns normally (with error)
               A continues normally
```

### When to Use Panic vs Error

```
Is this a programming error (bug in code)?
  YES → panic (index out of bounds, nil dereference, etc.)
  
Is this a runtime condition that might occur in production?
  YES → return error
  
Should a library crash the caller?
  Almost never → return error
  
Only acceptable panic:
  - Initialization that provably cannot fail
  - Known impossible states
  - Developer convenience (must-parse helpers)
```

---

## 13. Methods vs Functions

### What is a Method?

A **method** is a function with a **receiver** — a special first parameter that associates the function with a type.

```
func (receiver ReceiverType) MethodName(params) returnType {
     ↑               ↑
     bound to this type
```

### Value Receiver vs Pointer Receiver

```go
package main

import "fmt"

type Rectangle struct {
    Width, Height float64
}

// Value receiver: works on a COPY of Rectangle
// Use when: not modifying, small struct, or copying is cheap
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

// Pointer receiver: works on the ORIGINAL Rectangle
// Use when: modifying the receiver, large struct, or interface consistency
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor   // modifies the original
    r.Height *= factor
}

func main() {
    rect := Rectangle{Width: 4, Height: 3}
    
    fmt.Println(rect.Area()) // 12
    
    rect.Scale(2)            // Go automatically takes &rect when needed
    fmt.Println(rect.Area()) // 48
    fmt.Println(rect)        // {8 6}
}
```

### Value vs Pointer Receiver Decision

```
Receiver Decision Tree:
│
├── Does the method modify the receiver? ──► YES → *T (pointer)
│
├── Is the receiver a large struct? ──────► YES → *T (pointer, avoid copy)
│
├── Does T have pointer receivers elsewhere? → YES → *T (be consistent)
│
└── Otherwise ──────────────────────────── → T (value, simpler)
```

### Method vs Function — Side-by-Side

```go
// Function: receiver is an explicit parameter
func areaFunc(r Rectangle) float64 {
    return r.Width * r.Height
}

// Method: receiver is bound to type
func (r Rectangle) areaMethod() float64 {
    return r.Width * r.Height
}

// They are equivalent; methods just enable dot notation:
r := Rectangle{4, 3}
areaFunc(r)      // function call
r.areaMethod()   // method call (syntactic sugar for Rectangle.areaMethod(r))
```

---

## 14. Function Types

In Go, functions have types. The type of a function is defined by its signature: `func(paramTypes) returnTypes`.

```go
package main

import "fmt"

// Declare a function type
type Transformer func(int) int
type Predicate func(int) bool
type Comparator func(int, int) bool

// Functions that match these types
var double Transformer = func(n int) int { return n * 2 }
var isEven Predicate = func(n int) bool { return n%2 == 0 }

func filter(nums []int, pred Predicate) []int {
    result := []int{}
    for _, n := range nums {
        if pred(n) {
            result = append(result, n)
        }
    }
    return result
}

func mapSlice(nums []int, t Transformer) []int {
    result := make([]int, len(nums))
    for i, n := range nums {
        result[i] = t(n)
    }
    return result
}

func main() {
    nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    
    evens := filter(nums, isEven)
    fmt.Println(evens) // [2 4 6 8 10]
    
    doubled := mapSlice(evens, double)
    fmt.Println(doubled) // [4 8 12 16 20]
}
```

### Type Aliases for Functions

```go
// Without type alias — hard to read:
func process(fn func(func(int) bool, []int) []int) {}

// With type alias — readable:
type FilterFunc func([]int) []int
func process(fn FilterFunc) {}
```

---

## 15. Higher-Order Functions

A **higher-order function** is a function that:
1. Takes one or more functions as arguments, **OR**
2. Returns a function as its result

### Map, Filter, Reduce — Classic HOFs

```go
package main

import "fmt"

// Map: apply a transformation to every element
func Map[T, U any](slice []T, f func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = f(v)
    }
    return result
}

// Filter: keep elements that satisfy a predicate
func Filter[T any](slice []T, pred func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

// Reduce: fold a slice into a single value
func Reduce[T, U any](slice []T, initial U, f func(U, T) U) U {
    acc := initial
    for _, v := range slice {
        acc = f(acc, v)
    }
    return acc
}

func main() {
    nums := []int{1, 2, 3, 4, 5}
    
    squares := Map(nums, func(n int) int { return n * n })
    fmt.Println(squares) // [1 4 9 16 25]
    
    evens := Filter(nums, func(n int) bool { return n%2 == 0 })
    fmt.Println(evens) // [2 4]
    
    total := Reduce(nums, 0, func(acc, n int) int { return acc + n })
    fmt.Println(total) // 15
    
    // Chain them:
    result := Reduce(
        Map(
            Filter(nums, func(n int) bool { return n > 2 }),
            func(n int) int { return n * n },
        ),
        0,
        func(acc, n int) int { return acc + n },
    )
    fmt.Println(result) // 9 + 16 + 25 = 50
}
```

### Function Composition

```go
package main

import "fmt"

type IntFn func(int) int

// compose returns f(g(x))
func compose(f, g IntFn) IntFn {
    return func(x int) int {
        return f(g(x))
    }
}

// pipe returns g(f(x)) — left to right (more readable)
func pipe(fns ...IntFn) IntFn {
    return func(x int) int {
        for _, fn := range fns {
            x = fn(x)
        }
        return x
    }
}

func main() {
    double := func(n int) int { return n * 2 }
    addOne := func(n int) int { return n + 1 }
    square := func(n int) int { return n * n }
    
    // compose: square(addOne(x))
    squareOfAddOne := compose(square, addOne)
    fmt.Println(squareOfAddOne(4)) // (4+1)^2 = 25
    
    // pipe: double → addOne → square
    transform := pipe(double, addOne, square)
    fmt.Println(transform(3)) // square(addOne(double(3))) = square(7) = 49
}
```

### Partial Application (Currying)

```go
package main

import "fmt"

// adder returns a function that adds `x` to its argument
func adder(x int) func(int) int {
    return func(y int) int {
        return x + y  // x is captured from outer scope
    }
}

func multiplier(factor int) func(int) int {
    return func(n int) int {
        return n * factor
    }
}

func main() {
    add5 := adder(5)
    add10 := adder(10)
    
    fmt.Println(add5(3))   // 8
    fmt.Println(add5(7))   // 12
    fmt.Println(add10(3))  // 13
    
    triple := multiplier(3)
    fmt.Println(triple(7)) // 21
    
    nums := []int{1, 2, 3, 4, 5}
    for _, n := range nums {
        fmt.Print(triple(n), " ") // 3 6 9 12 15
    }
    fmt.Println()
}
```

---

## 16. Recursion — Theory and Practice

### What is Recursion?

A function is **recursive** if it calls itself, directly or indirectly. Every recursive solution has:
1. **Base case**: the condition under which recursion stops
2. **Recursive case**: the step that moves toward the base case

```
Recursive structure:
  f(n) = base case           if n is trivial
         combine(f(smaller)) otherwise
```

### Factorial

```go
package main

import "fmt"

// Recursive factorial
// f(0) = 1           (base case)
// f(n) = n * f(n-1)  (recursive case)
func factorial(n int) int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n-1)
}

func main() {
    for i := 0; i <= 10; i++ {
        fmt.Printf("%2d! = %d\n", i, factorial(i))
    }
}
```

### Call Stack Trace for factorial(4)

```
factorial(4)
│  return 4 * factorial(3)
│             │  return 3 * factorial(2)
│             │             │  return 2 * factorial(1)
│             │             │             │  return 1  (base case)
│             │             │  return 2 * 1 = 2
│             │  return 3 * 2 = 6
│  return 4 * 6 = 24
24
```

### Fibonacci — Multiple Approaches

```go
package main

import "fmt"

// Approach 1: Naive recursion — O(2^n) time, O(n) space
func fibNaive(n int) int {
    if n <= 1 {
        return n
    }
    return fibNaive(n-1) + fibNaive(n-2)
}

// Approach 2: Memoized recursion — O(n) time, O(n) space
func fibMemo(n int, memo map[int]int) int {
    if n <= 1 {
        return n
    }
    if val, ok := memo[n]; ok {
        return val
    }
    memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo)
    return memo[n]
}

// Approach 3: Bottom-up DP — O(n) time, O(1) space
func fibDP(n int) int {
    if n <= 1 {
        return n
    }
    prev, curr := 0, 1
    for i := 2; i <= n; i++ {
        prev, curr = curr, prev+curr
    }
    return curr
}

// Approach 4: Matrix exponentiation — O(log n) time
func fibFast(n int) int {
    if n <= 1 {
        return n
    }
    // Matrix multiplication [[1,1],[1,0]]^n
    type mat [2][2]int
    
    multiply := func(a, b mat) mat {
        return mat{
            {a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]},
            {a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]},
        }
    }
    
    power := func(m mat, n int) mat {
        result := mat{{1, 0}, {0, 1}} // identity matrix
        for n > 0 {
            if n%2 == 1 {
                result = multiply(result, m)
            }
            m = multiply(m, m)
            n /= 2
        }
        return result
    }
    
    base := mat{{1, 1}, {1, 0}}
    return power(base, n)[0][1]
}

func main() {
    memo := make(map[int]int)
    for i := 0; i <= 10; i++ {
        fmt.Printf("fib(%2d): naive=%d memo=%d dp=%d fast=%d\n",
            i, fibNaive(i), fibMemo(i, memo), fibDP(i), fibFast(i))
    }
}
```

### Recursion Decision Tree

```
Can the problem be broken into smaller subproblems of the same type?
│
├── YES
│   │
│   ├── Do subproblems overlap (same inputs computed multiple times)?
│   │   ├── YES → Dynamic Programming (memoize or bottom-up)
│   │   └── NO  → Plain recursion (divide and conquer)
│   │
│   └── Is the problem size reduction per call O(1)?
│       ├── YES → Beware O(n) stack depth
│       └── NO  → Should be fine
│
└── NO → Use iteration
```

### Binary Search — Recursive

```go
package main

import "fmt"

// binarySearch returns the index of target in sorted nums, or -1
func binarySearch(nums []int, target, lo, hi int) int {
    if lo > hi {
        return -1  // base case: not found
    }
    
    mid := lo + (hi-lo)/2  // avoids integer overflow (vs (lo+hi)/2)
    
    if nums[mid] == target {
        return mid           // base case: found
    } else if nums[mid] < target {
        return binarySearch(nums, target, mid+1, hi)  // search right half
    } else {
        return binarySearch(nums, target, lo, mid-1)  // search left half
    }
}

func main() {
    nums := []int{1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
    fmt.Println(binarySearch(nums, 7, 0, len(nums)-1))  // 3
    fmt.Println(binarySearch(nums, 6, 0, len(nums)-1))  // -1
}
```

### Tower of Hanoi

```go
package main

import "fmt"

// Move n disks from src to dst using via as helper
func hanoi(n int, src, dst, via string) {
    if n == 1 {
        fmt.Printf("Move disk 1 from %s to %s\n", src, dst)
        return
    }
    hanoi(n-1, src, via, dst) // move n-1 disks from src to via
    fmt.Printf("Move disk %d from %s to %s\n", n, src, dst)
    hanoi(n-1, via, dst, src) // move n-1 disks from via to dst
}

func main() {
    hanoi(3, "A", "C", "B")
}
```

**Output:**
```
Move disk 1 from A to C
Move disk 2 from A to B
Move disk 1 from C to B
Move disk 3 from A to C
Move disk 1 from B to A
Move disk 2 from B to C
Move disk 1 from A to C
```

---

## 17. Tail Recursion and Why Go Doesn't Optimize It

### What is Tail Recursion?

A function is **tail recursive** if the recursive call is the **last operation** performed before returning. There is nothing to do after the recursive call returns.

```go
// NOT tail recursive — must multiply AFTER recursive call returns
func factorial(n int) int {
    if n <= 1 { return 1 }
    return n * factorial(n-1)   // ← n * (result) means work pending after return
}

// Tail recursive — accumulator pattern
func factorialTail(n, acc int) int {
    if n <= 1 { return acc }
    return factorialTail(n-1, n*acc)  // ← just return the recursive call
}
```

### Why Go Doesn't Optimize Tail Calls

Go's compiler **does not perform Tail Call Optimization (TCO)**. This is a deliberate design choice:

1. **Stack traces**: Go wants accurate goroutine stack traces for debugging
2. **Simplicity**: TCO complicates the compiler and runtime
3. **Goroutines**: Go's growable stack mitigates stack overflow risk

**Implication**: For large inputs, use iteration instead of recursion in Go.

### Converting Tail Recursion to Iteration

```go
// Recursive (stack depth = n)
func factorialTail(n, acc int) int {
    if n <= 1 { return acc }
    return factorialTail(n-1, n*acc)
}

// Iterative equivalent (constant stack)
func factorialIter(n int) int {
    acc := 1
    for n > 1 {
        acc *= n
        n--
    }
    return acc
}
```

---

## 18. Init Functions

`init()` is a special function in Go:
- Called automatically before `main()` (or before the package is used)
- Cannot be called manually
- Can appear multiple times in a file or package
- Runs after all variable declarations in the package are initialized

```go
package main

import "fmt"

var config map[string]string

func init() {
    // Initialize package-level variables
    config = map[string]string{
        "host": "localhost",
        "port": "8080",
    }
    fmt.Println("init() called")
}

func main() {
    fmt.Println("main() called")
    fmt.Println(config["host"])
}
```

**Output:**
```
init() called
main() called
localhost
```

### Init Execution Order

```
Package initialization order:
1. All package-level var declarations (in dependency order)
2. All init() functions (in source file order, top to bottom)
3. main() (only in main package)

Import graph:
  main imports A, B
  A imports C
  
Init order:
  C.init() → A.init() → B.init() → main.init() → main.main()
```

### Multiple init() in One File

```go
package main

import "fmt"

func init() {
    fmt.Println("init 1")
}

func init() {
    fmt.Println("init 2")
}

func init() {
    fmt.Println("init 3")
}

func main() {
    fmt.Println("main")
}
// Output: init 1, init 2, init 3, main
```

---

## 19. Blank Identifier in Functions

The blank identifier `_` discards values you don't need from multi-return functions.

```go
package main

import (
    "fmt"
    "os"
)

func getCoords() (int, int, int) {
    return 10, 20, 30
}

func main() {
    x, _, z := getCoords()         // discard the y value
    fmt.Println(x, z)              // 10 30
    
    // Discard error (generally bad practice — only if you're certain)
    f, _ := os.Open("/tmp/test")   // _ discards error
    if f != nil {
        defer f.Close()
    }
    
    // Execute for side effects only
    for _, val := range []int{1, 2, 3} {
        fmt.Println(val)
    }
}
```

---

## 20. Inline Functions and Compiler Inlining

### What is Inlining?

**Function inlining** is a compiler optimization where the function body is inserted directly at the call site, eliminating the overhead of a function call (pushing/popping stack frame, jump).

```
Without inlining:
  call add(a, b) → push args → jump to add → execute → pop → jump back

With inlining:
  result = a + b  ← body inserted directly, no call overhead
```

### How Go Decides to Inline

The Go compiler uses a **budget** system. Small, simple functions are automatically inlined. You can check with:

```bash
go build -gcflags="-m" main.go
```

### Writing Inlining-Friendly Functions

```go
// ✅ Will be inlined — simple, small
func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

// ❌ Cannot be inlined — contains for loop (in older Go versions)
func sum(nums []int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}
```

### Benchmarking Function Call Overhead

```go
package main

import "testing"

func addInline(a, b int) int { return a + b }

func BenchmarkDirect(b *testing.B) {
    a, c := 3, 4
    for i := 0; i < b.N; i++ {
        _ = a + c
    }
}

func BenchmarkFuncCall(b *testing.B) {
    a, c := 3, 4
    for i := 0; i < b.N; i++ {
        _ = addInline(a, c)
    }
}
```

---

## 21. Function Signatures and Interface Satisfaction

### Interfaces via Function Signatures

In Go, a type satisfies an interface if it has all the methods the interface requires.

```go
package main

import (
    "fmt"
    "math"
)

// Interface: any type with Area() float64 satisfies Shape
type Shape interface {
    Area() float64
    Perimeter() float64
}

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
    W, H float64
}

func (r Rectangle) Area() float64      { return r.W * r.H }
func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

func printShape(s Shape) {
    fmt.Printf("Area: %.2f, Perimeter: %.2f\n", s.Area(), s.Perimeter())
}

func main() {
    shapes := []Shape{
        Circle{Radius: 5},
        Rectangle{W: 4, H: 6},
    }
    for _, s := range shapes {
        printShape(s)
    }
}
```

### Function as Interface (http.Handler Pattern)

```go
package main

import (
    "fmt"
    "net/http"
)

// http.Handler interface:
// type Handler interface {
//     ServeHTTP(ResponseWriter, *Request)
// }

// http.HandlerFunc is a type that makes a function satisfy Handler
type HandlerFunc func(http.ResponseWriter, *http.Request)

func (f HandlerFunc) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    f(w, r)  // delegate to the underlying function
}

// Now any function with the right signature IS a handler:
var myHandler http.Handler = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintln(w, "Hello, World!")
})
```

---

## 22. Goroutines and Functions

### Launching Functions Concurrently

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done()  // signal completion when function returns
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Millisecond * 100)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    var wg sync.WaitGroup
    
    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go worker(i, &wg)  // launch function as goroutine
    }
    
    wg.Wait()  // block until all workers complete
    fmt.Println("All workers done")
}
```

### Goroutine with Anonymous Function

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup
    results := make([]int, 10)
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        i := i  // capture per iteration (important!)
        go func() {
            defer wg.Done()
            results[i] = i * i
        }()
    }
    
    wg.Wait()
    fmt.Println(results)
}
```

### Function as Task in Channel Pipeline

```go
package main

import "fmt"

// Generator: produces integers
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

// Stage: applies a transformation
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
    c := generate(2, 3, 4, 5)
    out := square(c)
    
    for n := range out {
        fmt.Println(n)  // 4, 9, 16, 25
    }
}
```

---

## 23. Memory Model — Stack vs Heap for Functions

### The Stack

- Fixed-size frame allocated per function call
- Stores: local variables, parameters, return address
- Automatically freed when function returns
- Very fast (just move the stack pointer)

### The Heap

- Dynamically allocated
- Survives beyond function lifetime
- Managed by garbage collector (GC)
- Slower (GC pressure, allocations)

### Escape Analysis

Go's compiler decides whether a variable lives on the stack or heap through **escape analysis**. A variable *escapes to the heap* when:
1. It is returned from a function
2. It is captured by a closure
3. A pointer to it is stored globally
4. It is passed to an interface

```go
package main

// Does NOT escape — stays on stack
func stackAlloc() int {
    x := 42    // x is local, not returned or captured
    return x   // value is copied, not the address
}

// DOES escape — address returned, must be on heap
func heapAlloc() *int {
    x := 42    // x escapes because its address is returned
    return &x  // after heapAlloc returns, x must still exist
}

// Closure captures — escapes
func closureCapture() func() int {
    x := 0     // x escapes to heap because captured by returned closure
    return func() int {
        x++
        return x
    }
}
```

```bash
# Visualize escape analysis:
go build -gcflags="-m -m" main.go
```

### Stack vs Heap Visualization

```
stack frame for heapAlloc():          HEAP:
┌──────────────────────┐             ┌─────────┐
│ return addr          │             │  x = 42 │ ← lives here after
│ local: x = 42 ───────┼─────────►  │         │   function returns
│ ...                  │             └─────────┘
└──────────────────────┘
       │ function returns
       ▼ frame is popped (but x is NOT freed — it's on heap!)
```

### Goroutine Stack

Every goroutine starts with a small stack (~2KB in Go) that **grows dynamically** as needed (up to 1GB by default). This is different from OS threads which have fixed-size stacks.

```
Goroutine 1 stack:  [2KB] → grows → [4KB] → [8KB] → ...
Goroutine 2 stack:  [2KB]
Goroutine 3 stack:  [2KB]
...
(can have millions of goroutines cheaply)
```

---

## 24. Error Handling Patterns in Functions

Go's error handling philosophy: errors are values, handle them explicitly.

### Pattern 1: Simple Error Return

```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("cannot divide by zero")
    }
    return a / b, nil
}
```

### Pattern 2: Sentinel Errors

```go
package main

import (
    "errors"
    "fmt"
)

// Sentinel: a specific, predeclared error value
var ErrNotFound = errors.New("not found")
var ErrPermission = errors.New("permission denied")

func findUser(id int) (string, error) {
    if id == 0 {
        return "", ErrNotFound
    }
    if id < 0 {
        return "", ErrPermission
    }
    return "Alice", nil
}

func main() {
    _, err := findUser(0)
    if errors.Is(err, ErrNotFound) {
        fmt.Println("User not found") // ← specific error handling
    }
}
```

### Pattern 3: Custom Error Types

```go
package main

import "fmt"

type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error: field=%s, msg=%s", e.Field, e.Message)
}

func validateAge(age int) error {
    if age < 0 {
        return &ValidationError{Field: "age", Message: "must be non-negative"}
    }
    if age > 150 {
        return &ValidationError{Field: "age", Message: "unrealistically large"}
    }
    return nil
}

func main() {
    err := validateAge(-5)
    
    var valErr *ValidationError
    if errors.As(err, &valErr) {
        fmt.Println("Field:", valErr.Field)   // age
        fmt.Println("Msg:", valErr.Message)   // must be non-negative
    }
}
```

### Pattern 4: Error Wrapping

```go
import "fmt"

func processFile(path string) error {
    data, err := readFile(path)
    if err != nil {
        return fmt.Errorf("processFile %q: %w", path, err)  // %w wraps the error
    }
    _ = data
    return nil
}

// Caller can unwrap:
err := processFile("/tmp/data.txt")
if errors.Is(err, os.ErrNotExist) {
    // works even though err is wrapped!
}
```

### Error Handling Decision Tree

```
Function can fail?
│
├── YES
│   │
│   ├── Is it always a bug (programmer error)? → panic()
│   │
│   ├── Is it expected at runtime? → return error
│   │   │
│   │   ├── Simple error? → errors.New() or fmt.Errorf()
│   │   ├── Specific type needed? → custom error struct
│   │   ├── Need to match exact error? → sentinel (var ErrX = errors.New(...))
│   │   └── Need context chain? → fmt.Errorf("...: %w", err)
│   │
│   └── Needs cleanup regardless? → defer + recover
│
└── NO → return value only
```

---

## 25. Functional Programming Patterns in Go

### Immutability via Value Types

```go
package main

import "fmt"

type Point struct{ X, Y int }

// Returns new Point — original unchanged
func (p Point) Translate(dx, dy int) Point {
    return Point{p.X + dx, p.Y + dy}
}

func (p Point) Scale(factor int) Point {
    return Point{p.X * factor, p.Y * factor}
}

func main() {
    p := Point{1, 2}
    p2 := p.Translate(3, 4).Scale(2)
    fmt.Println(p)   // {1 2}  — unchanged
    fmt.Println(p2)  // {8 12}
}
```

### Option Type (Maybe Monad Approximation)

```go
package main

import "fmt"

type Optional[T any] struct {
    value T
    valid bool
}

func Some[T any](v T) Optional[T] { return Optional[T]{v, true} }
func None[T any]() Optional[T]    { return Optional[T]{} }

func (o Optional[T]) Map(f func(T) T) Optional[T] {
    if !o.valid {
        return o
    }
    return Some(f(o.value))
}

func (o Optional[T]) GetOrElse(def T) T {
    if o.valid {
        return o.value
    }
    return def
}

func safeDivide(a, b int) Optional[int] {
    if b == 0 {
        return None[int]()
    }
    return Some(a / b)
}

func main() {
    result := safeDivide(10, 2).
        Map(func(n int) int { return n * 3 }).
        GetOrElse(0)
    fmt.Println(result) // 15
    
    result = safeDivide(10, 0).
        Map(func(n int) int { return n * 3 }).
        GetOrElse(-1)
    fmt.Println(result) // -1
}
```

### Pipeline Pattern

```go
package main

import "fmt"

type Pipeline[T any] struct {
    data []T
}

func NewPipeline[T any](data []T) Pipeline[T] {
    return Pipeline[T]{data: data}
}

func (p Pipeline[T]) Filter(pred func(T) bool) Pipeline[T] {
    var result []T
    for _, v := range p.data {
        if pred(v) {
            result = append(result, v)
        }
    }
    return Pipeline[T]{data: result}
}

func (p Pipeline[T]) ForEach(f func(T)) {
    for _, v := range p.data {
        f(v)
    }
}

func main() {
    NewPipeline([]int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}).
        Filter(func(n int) bool { return n%2 == 0 }).
        Filter(func(n int) bool { return n > 4 }).
        ForEach(func(n int) { fmt.Print(n, " ") })
    fmt.Println()
    // 6 8 10
}
```

---

## 26. Performance Optimization Techniques

### Avoid Unnecessary Allocations in Function Returns

```go
// ❌ Allocates a new slice every call
func getEvens(nums []int) []int {
    result := []int{}
    for _, n := range nums {
        if n%2 == 0 {
            result = append(result, n)
        }
    }
    return result
}

// ✅ Pass in a buffer to reuse
func getEvensInto(nums, buf []int) []int {
    buf = buf[:0]  // reset length, keep capacity
    for _, n := range nums {
        if n%2 == 0 {
            buf = append(buf, n)
        }
    }
    return buf
}
```

### Avoid Interface Boxing in Hot Paths

```go
// ❌ Interface causes heap allocation (boxing) for each element
func sumInterface(nums []interface{}) int {
    total := 0
    for _, v := range nums {
        total += v.(int)  // type assertion + potential alloc
    }
    return total
}

// ✅ Concrete type — no boxing
func sumConcrete(nums []int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}
```

### Benchmark Template

```go
package main

import (
    "testing"
)

func BenchmarkMyFunc(b *testing.B) {
    // Setup outside the loop
    data := make([]int, 1000)
    for i := range data {
        data[i] = i
    }
    
    b.ResetTimer() // don't count setup time
    b.ReportAllocs() // show allocation info
    
    for i := 0; i < b.N; i++ {
        _ = sumConcrete(data)
    }
}
```

```bash
go test -bench=. -benchmem -count=5 ./...
```

---

## 27. Testing Functions

### Unit Testing

```go
package main

import (
    "testing"
)

func add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 3, 4, 7},
        {"negative", -3, -4, -7},
        {"mixed", -3, 4, 1},
        {"zero", 0, 0, 0},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := add(tt.a, tt.b)
            if result != tt.expected {
                t.Errorf("add(%d, %d) = %d; want %d",
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}
```

### Testing with Interfaces (Dependency Injection)

```go
package main

import (
    "fmt"
    "testing"
)

type Storage interface {
    Get(key string) (string, error)
    Set(key, value string) error
}

type UserService struct {
    storage Storage
}

func (s *UserService) GetUser(id string) (string, error) {
    return s.storage.Get("user:" + id)
}

// Mock for testing
type MockStorage struct {
    data map[string]string
}

func (m *MockStorage) Get(key string) (string, error) {
    v, ok := m.data[key]
    if !ok {
        return "", fmt.Errorf("key not found: %s", key)
    }
    return v, nil
}

func (m *MockStorage) Set(key, value string) error {
    m.data[key] = value
    return nil
}

func TestGetUser(t *testing.T) {
    mock := &MockStorage{
        data: map[string]string{
            "user:42": "Alice",
        },
    }
    
    svc := &UserService{storage: mock}
    
    name, err := svc.GetUser("42")
    if err != nil {
        t.Fatal(err)
    }
    if name != "Alice" {
        t.Errorf("expected Alice, got %s", name)
    }
}
```

---

## 28. DSA-Focused Function Patterns

### Two-Pointer Technique

```go
package main

import "fmt"

// twoSum: find two numbers in sorted array that sum to target
// Returns indices or (-1, -1) if not found
// Time: O(n), Space: O(1)
func twoSum(nums []int, target int) (int, int) {
    lo, hi := 0, len(nums)-1
    
    for lo < hi {
        sum := nums[lo] + nums[hi]
        switch {
        case sum == target:
            return lo, hi
        case sum < target:
            lo++  // need larger sum
        default:
            hi--  // need smaller sum
        }
    }
    return -1, -1
}

func main() {
    nums := []int{1, 2, 3, 4, 6, 8, 9}
    i, j := twoSum(nums, 11)
    fmt.Printf("nums[%d] + nums[%d] = %d + %d = %d\n",
        i, j, nums[i], nums[j], nums[i]+nums[j])
    // nums[2] + nums[5] = 3 + 8 = 11
}
```

### Sliding Window

```go
package main

import "fmt"

// maxSubarraySum: maximum sum subarray of length k
// Time: O(n), Space: O(1)
func maxSubarraySum(nums []int, k int) int {
    if len(nums) < k {
        return 0
    }
    
    // Compute first window
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += nums[i]
    }
    
    maxSum := windowSum
    
    // Slide the window
    for i := k; i < len(nums); i++ {
        windowSum += nums[i]     // add new element
        windowSum -= nums[i-k]   // remove leftmost element
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    
    return maxSum
}

func main() {
    nums := []int{2, 1, 5, 1, 3, 2}
    fmt.Println(maxSubarraySum(nums, 3)) // 9 (5+1+3)
}
```

### Recursive Tree Traversal

```go
package main

import "fmt"

type TreeNode struct {
    Val   int
    Left  *TreeNode
    Right *TreeNode
}

// Inorder: Left → Root → Right
func inorder(root *TreeNode) []int {
    if root == nil {
        return nil
    }
    result := inorder(root.Left)
    result = append(result, root.Val)
    result = append(result, inorder(root.Right)...)
    return result
}

// Preorder: Root → Left → Right
func preorder(root *TreeNode) []int {
    if root == nil {
        return nil
    }
    result := []int{root.Val}
    result = append(result, preorder(root.Left)...)
    result = append(result, preorder(root.Right)...)
    return result
}

// Height of tree
func height(root *TreeNode) int {
    if root == nil {
        return 0
    }
    lh := height(root.Left)
    rh := height(root.Right)
    if lh > rh {
        return lh + 1
    }
    return rh + 1
}

func newNode(val int) *TreeNode { return &TreeNode{Val: val} }

func main() {
    //       4
    //      / \
    //     2   6
    //    / \ / \
    //   1  3 5  7
    
    root := newNode(4)
    root.Left = newNode(2)
    root.Right = newNode(6)
    root.Left.Left = newNode(1)
    root.Left.Right = newNode(3)
    root.Right.Left = newNode(5)
    root.Right.Right = newNode(7)
    
    fmt.Println("Inorder:", inorder(root))   // [1 2 3 4 5 6 7]
    fmt.Println("Preorder:", preorder(root)) // [4 2 1 3 6 5 7]
    fmt.Println("Height:", height(root))    // 3
}
```

### Backtracking Template Function

```go
package main

import "fmt"

// Permutations using backtracking
func permutations(nums []int) [][]int {
    var result [][]int
    var backtrack func(current []int, remaining []int)
    
    backtrack = func(current []int, remaining []int) {
        // Base case: no elements remaining
        if len(remaining) == 0 {
            perm := make([]int, len(current))
            copy(perm, current)
            result = append(result, perm)
            return
        }
        
        // Try each remaining element
        for i, n := range remaining {
            // Choose
            current = append(current, n)
            next := append(remaining[:i:i], remaining[i+1:]...)
            
            // Explore
            backtrack(current, next)
            
            // Unchoose (backtrack)
            current = current[:len(current)-1]
        }
    }
    
    backtrack([]int{}, nums)
    return result
}

func main() {
    perms := permutations([]int{1, 2, 3})
    for _, p := range perms {
        fmt.Println(p)
    }
    // [1 2 3] [1 3 2] [2 1 3] [2 3 1] [3 1 2] [3 2 1]
}
```

### Backtracking Decision Tree (Visual)

```
permutations([1,2,3]):

                        []
            /           |           \
          [1]          [2]          [3]
         /   \        /   \        /   \
      [1,2] [1,3] [2,1] [2,3] [3,1] [3,2]
        |      |     |      |     |      |
     [1,2,3][1,3,2][2,1,3][2,3,1][3,1,2][3,2,1]
        ↑      ↑     ↑      ↑     ↑      ↑
      base   base  base   base  base   base
      case   case  case   case  case   case
```

---

## 29. Mental Models and Cognitive Frameworks

### Mental Model 1: Functions as Black Boxes

When reading or designing code, first understand **what** a function does (its contract), not **how**. This is **abstraction thinking** — the foundation of expert software design.

```
Black Box Model:
  
  Input ──► [  f  ] ──► Output
  
  You only need to know:
  1. What inputs are valid (preconditions)
  2. What output is produced (postconditions)
  3. What side effects occur (if any)
```

### Mental Model 2: The Substitution Model

For pure functions (no side effects), you can mentally *substitute* the function call with its return value:

```
add(3, 4) + add(1, 2)
= 7       + 3           ← substitute
= 10
```

This only works for **pure functions** (same input → same output, no side effects).

### Mental Model 3: Function Composition as Pipes

Think of functions as **UNIX pipes**:

```
data | transform1 | transform2 | filter | output

In Go:
  output := filter(transform2(transform1(data)))
  
Or with a pipeline builder:
  pipeline(data, transform1, transform2, filter)
```

### Mental Model 4: The Caller/Callee Contract

Every function defines a **contract**:

```
PRECONDITION:  What the caller MUST guarantee before calling
POSTCONDITION: What the callee GUARANTEES after returning
INVARIANT:     What is ALWAYS true (before and after)

Example:
  binarySearch(sorted []int, target int) int
  PRE:  nums must be sorted in ascending order
  POST: returns index i such that nums[i] == target, or -1
  INV:  the slice is never modified
```

### Deliberate Practice Framework for Functions

> **Anders Ericsson's Deliberate Practice**: Don't just write functions — study them with intent. After every function you write, ask:

1. **Complexity**: What is the time and space complexity?
2. **Edge cases**: What inputs would break this?
3. **Alternatives**: Is there a more elegant approach?
4. **Generalization**: Can this be made more reusable?
5. **Testing**: What are the minimal test cases to verify correctness?

### The Expert's Thinking Process Before Writing a Function

```
STEP 1: UNDERSTAND
  - What problem does this function solve?
  - What are the inputs and expected outputs?
  - What are the constraints (size, type, range)?

STEP 2: EXAMPLES
  - Generate 2-3 concrete examples
  - Include edge cases (empty, single element, negative)

STEP 3: PATTERN MATCH
  - Does this look like: two pointers? sliding window? BFS? DP?
  - What data structures are useful?

STEP 4: ALGORITHM
  - Brute force first (correctness over performance)
  - Optimize after understanding

STEP 5: CODE
  - Write, don't perfect — working code > perfect design

STEP 6: VERIFY
  - Trace through examples mentally
  - Test edge cases
  - Check complexity
```

---

## 30. Cheat Sheet

```
╔═══════════════════════════════════════════════════════════════╗
║                  GOLANG FUNCTIONS CHEAT SHEET                 ║
╠═══════════════════════════════════════════════════════════════╣
║ DECLARATION                                                   ║
║   func name(p1 T1, p2 T2) (R1, R2) { ... }                   ║
║   func name(p1, p2 T) R { ... }        // grouped params      ║
║   func name(p ...T) { ... }            // variadic            ║
║                                                               ║
║ FIRST CLASS                                                   ║
║   var f func(int) int = func(n int) int { return n }         ║
║   type MyFunc func(int) int                                   ║
║                                                               ║
║ CLOSURES                                                      ║
║   outer := func() func() int {                                ║
║       x := 0                                                  ║
║       return func() int { x++; return x }                    ║
║   }                                                           ║
║                                                               ║
║ DEFER                                                         ║
║   defer f()         // runs at function end, LIFO order       ║
║   defer f(x)        // x evaluated NOW, call deferred        ║
║                                                               ║
║ PANIC / RECOVER                                               ║
║   panic(val)                                                  ║
║   defer func() { r := recover(); if r != nil { ... } }()    ║
║                                                               ║
║ NAMED RETURNS                                                 ║
║   func f() (x int, err error) { return }  // naked return    ║
║                                                               ║
║ METHODS                                                       ║
║   func (t T) Method() {}     // value receiver (copy)        ║
║   func (t *T) Method() {}    // pointer receiver (original)  ║
║                                                               ║
║ INIT                                                          ║
║   func init() { ... }  // auto-run, no args, no return       ║
║                                                               ║
║ GOROUTINE                                                     ║
║   go func() { ... }()  // anonymous func as goroutine        ║
║   go myFunc(args)       // named func as goroutine            ║
╚═══════════════════════════════════════════════════════════════╝
```

### Complexity Quick Reference for Common Function Patterns

| Pattern | Time | Space | Notes |
|---|---|---|---|
| Iterative loop | O(n) | O(1) | Preferred over recursion |
| Binary search | O(log n) | O(1) iter / O(log n) rec | Sorted input required |
| Recursion (no memo) | O(2^n) worst | O(n) stack | Avoid for fib-like |
| Memoized recursion | O(n) | O(n) | Cache subproblems |
| Two pointers | O(n) | O(1) | Sorted/windowed problems |
| Sliding window | O(n) | O(1) or O(k) | Subarray problems |
| Backtracking | O(n!) worst | O(n) | Pruning helps |
| Higher-order map | O(n) | O(n) | Returns new slice |
| Closure counter | O(1)/call | O(1) | State in heap |

---

## Final Words — The Monk's Path

> "The more constraints one imposes, the more one frees oneself. And the arbitrariness of the constraint serves only to obtain precision of execution." — Igor Stravinsky

In Go, functions are deliberately simple — no overloading, no default arguments, no optional parameters. This constraint **forces clarity**. You cannot hide complexity behind language features; you must *think* clearly and express it simply.

The path to mastery:
1. **Write many small functions** — under 20 lines ideally
2. **Name them precisely** — the name is the documentation
3. **Understand the memory model** — know when you're on the stack vs heap
4. **Embrace multiple return values** — it is Go's gift to error handling
5. **Practice closures until they feel natural** — they are the key to elegant abstractions
6. **Always measure before optimizing** — `go test -bench` is your oracle

**Cognitive principle — Spaced Repetition**: Return to this guide after 1 day, 1 week, and 1 month. Each time, implement every pattern from scratch. The goal is not recognition but *generation* — the ability to produce correct, elegant code without reference.

> You are not learning *about* functions. You are learning to *think* in functions.
```

Now let me build this comprehensive guide. This will be a large, deeply detailed `.md` file.Your complete guide is ready. Here's a map of everything covered across **30 sections**:

---

### What's Inside

**Foundations**
- Function anatomy, naming conventions, call stack visualization
- Pass-by-value (the #1 misunderstood concept in Go) with ASCII memory diagrams
- Pointer semantics, slice headers, reference types

**Return System**
- Single/multiple returns, named returns, naked returns
- How named returns interact with `defer` to modify return values
- Error handling patterns: sentinel errors, custom error types, `%w` wrapping

**Advanced Function Features**
- Variadic functions (`...T`), spread operator, memory layout
- First-class functions, function types, type aliases
- Anonymous functions, IIFE pattern
- **Closures** — deep dive with heap escape, the classic loop bug (3 fixes), memoization

**Control Flow**
- `defer` — LIFO stack, argument evaluation timing, resource cleanup
- `panic` / `recover` — with unwinding diagram
- `init()` — execution order across packages

**Object-Oriented Layer**
- Methods vs functions, value vs pointer receivers, decision tree
- Interface satisfaction via method signatures
- `http.HandlerFunc` pattern

**Functional Programming**
- Higher-order functions: Map, Filter, Reduce with generics
- Function composition, pipe, partial application (currying)
- Option/Maybe type, pipeline builder pattern

**Systems & Performance**
- Stack vs heap, escape analysis with `go build -gcflags="-m"`
- Goroutine stacks (2KB growable), channel pipelines
- Avoiding allocations, interface boxing overhead
- Benchmark templates

**DSA Patterns**
- Two pointers, sliding window, binary search (recursive)
- Tree traversals (inorder, preorder, height)
- Backtracking template with decision tree visualization
- Fibonacci — 4 approaches from O(2ⁿ) to O(log n)
- Tower of Hanoi

**Mastery Layer**
- Mental models: black box, substitution, pipes, contracts
- Deliberate practice framework — the expert's thinking process
- Cognitive principles: chunking, spaced repetition