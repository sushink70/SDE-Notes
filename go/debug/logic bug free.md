# Writing Logic Bug-Free Code in Go
## A Complete, In-Depth Guide

---

## Table of Contents

1. [The Mental Model: What Is a Logic Bug?](#1-the-mental-model-what-is-a-logic-bug)
2. [The Spectrum of Guarantees in Go](#2-the-spectrum-of-guarantees-in-go)
3. [Make Illegal States Unrepresentable](#3-make-illegal-states-unrepresentable)
4. [Go's Type System as a Logic Enforcer](#4-gos-type-system-as-a-logic-enforcer)
5. [The nil Problem: Go's Biggest Logic Footgun](#5-the-nil-problem-gos-biggest-logic-footgun)
6. [Simulating Sum Types and Enums in Go](#6-simulating-sum-types-and-enums-in-go)
7. [Interfaces as Logical Contracts](#7-interfaces-as-logical-contracts)
8. [The Newtype Pattern in Go](#8-the-newtype-pattern-in-go)
9. [Parse, Don't Validate](#9-parse-dont-validate)
10. [Total Functions vs. Partial Functions](#10-total-functions-vs-partial-functions)
11. [Invariants: The Core Concept](#11-invariants-the-core-concept)
12. [Error Handling as Logic Correctness](#12-error-handling-as-logic-correctness)
13. [The Typestate Pattern in Go](#13-the-typestate-pattern-in-go)
14. [State Machines in Go](#14-state-machines-in-go)
15. [Domain Modeling for Correctness](#15-domain-modeling-for-correctness)
16. [Builder Pattern and Functional Options](#16-builder-pattern-and-functional-options)
17. [Slices, Maps, and Channels: Logic Traps](#17-slices-maps-and-channels-logic-traps)
18. [Integer Arithmetic: Go's Silent Overflow](#18-integer-arithmetic-gos-silent-overflow)
19. [Assertions, Contracts, and Defensive Programming](#19-assertions-contracts-and-defensive-programming)
20. [Property-Based Testing](#20-property-based-testing)
21. [Static Analysis and Tooling](#21-static-analysis-and-tooling)
22. [Concurrency Logic Correctness](#22-concurrency-logic-correctness)
23. [Goroutine Lifecycle and Leak Prevention](#23-goroutine-lifecycle-and-leak-prevention)
24. [Algorithm Correctness Patterns](#24-algorithm-correctness-patterns)
25. [Anti-Patterns That Introduce Logic Bugs](#25-anti-patterns-that-introduce-logic-bugs)
26. [The Mental Checklist: A Systematic Thinking Process](#26-the-mental-checklist-a-systematic-thinking-process)

---

## 1. The Mental Model: What Is a Logic Bug?

Before eliminating logic bugs, you need a sharp definition of what they are — and how Go's guarantees differ from a language like Rust.

### What Go Catches vs. What It Does Not

Go provides some safety guarantees at runtime:

- **Nil pointer dereference** → runtime panic (caught, but only at runtime)
- **Slice/array out of bounds** → runtime panic (caught, but only at runtime)
- **Map access on nil map** → runtime panic (caught, but only at runtime)
- **Closed channel operations** → runtime panic (caught, but only at runtime)
- **Data races** → detected only with the `-race` flag (opt-in, not automatic)

Go does **not** provide:

- Compile-time nullability checking (unlike Kotlin, Swift, or Rust)
- Exhaustive sum types (unlike Rust, Haskell, Swift)
- Compile-time enforcement of operation ordering (no typestate)
- Automatic memory safety from logical misuse (no borrow checker)
- Silent overflow detection (unlike Rust debug builds — Go **always wraps silently**)

A **logic bug** in Go is:
> The program compiles. The program does not panic. The program produces an **incorrect result** or reaches an **invalid state**.

```
MEMORY/RUNTIME BUG:          LOGIC BUG:
Program panics           vs  Program runs fine but does the WRONG thing
Go catches at runtime    vs  Go cannot catch it (it doesn't know what "right" means)
Stack trace points here  vs  Silent corruption somewhere upstream
```

### The Complete Taxonomy of Logic Bugs in Go

```
Logic Bugs in Go
├── Semantic Errors
│   ├── Off-by-one (< vs <=, 0-indexed confusion, half-open vs closed ranges)
│   ├── Wrong formula (wrong units: km vs m, radians vs degrees)
│   ├── Integer overflow (Go wraps SILENTLY in ALL builds — no panic!)
│   └── Float precision errors (0.1 + 0.2 != 0.3)
│
├── nil-Related Logic Errors
│   ├── Interface nil != concrete nil (Go's most infamous footgun)
│   ├── nil map reads return zero values (no panic!) — appears to "work"
│   ├── nil function variable called → panic
│   └── nil pointer deref after optional value not checked
│
├── State Errors
│   ├── Invalid state reached (connected before authenticated)
│   ├── Stale state (using cached value after underlying data changed)
│   ├── Partial update (updating field A but forgetting field B)
│   └── Use-before-initialize (zero value used as if constructed)
│
├── Slice and Map Errors
│   ├── Aliased slice mutation (two slices share backing array)
│   ├── Append invalidating references (realloc changes pointer)
│   ├── for range value copy (modifying copy, not original)
│   ├── Closed-over loop variable (goroutine captures stale i)
│   └── Map read during concurrent write (even without -race flag: UB)
│
├── Boundary / Edge Case Errors
│   ├── Empty slice/string not handled
│   ├── Single-element input treated like multi-element
│   ├── Zero-value struct used uninitialized
│   └── Context expiry not checked before use
│
├── Assumption Violations
│   ├── Assuming sorted input when unsorted
│   ├── Assuming unique values when duplicates exist
│   ├── Assuming goroutine ordering (no happens-before guarantee)
│   └── Assuming error == nil means all fields are valid
│
└── Concurrency Logic Errors
    ├── TOCTOU (Time-of-Check-Time-of-Use) between goroutines
    ├── Goroutine leak (goroutine blocked forever, resource never freed)
    ├── Channel send/recv ordering assumption
    ├── select non-determinism misunderstood
    └── Mutex held across goroutine boundary
```

### The Core Insight: Move Detection Left

```
RUNTIME (worst)  →  TEST TIME  →  COMPILE TIME  →  MODEL TIME (best)
  panic/wrong       test fails      won't compile    impossible
    result                                          to express
```

Go's type system is less expressive than Rust's, so fewer bugs can be moved to compile time. This makes the other layers — testing, static analysis, defensive design — **more critical** in Go, not less.

---

## 2. The Spectrum of Guarantees in Go

Different techniques give different confidence levels. Know all of them:

```
STRONGEST                                                       WEAKEST
    │                                                               │
    ▼                                                               ▼
Interface     Newtype +    Property      Unit / Integ.    No
Contracts   Constructor   Testing       Tests            Check
(compile)   Enforcement  (gopter/rapid) (testing pkg)
(partial)   (runtime)
```

Go's compile-time guarantees are weaker than Rust's but still valuable. The real power in Go comes from:

- **Design patterns** that make invalid states hard to construct
- **Unexported fields** with validated constructors
- **Interface boundaries** that enforce contracts
- **Property-based testing** that exercises invariants
- **Static analysis tools** that catch what the compiler misses
- **The race detector** for concurrency correctness

**A robust Go codebase uses all layers simultaneously.**

### Tooling Layer — Always Active in CI

```
go build         → Type checking, syntax
go vet           → Common mistakes (printf format, unreachable code, etc.)
staticcheck      → Deeper static analysis (nilness, unused, etc.)
golangci-lint    → Aggregates 40+ linters
go test -race    → Data race detection at runtime
go test -cover   → Coverage guided testing gaps
gopter / rapid   → Property-based testing
```

---

## 3. Make Illegal States Unrepresentable

This is the single most important principle for logic-correct code — and Go makes it harder than Rust, but far from impossible.

### The Idea

If an invalid state **cannot be constructed** given your public API, it literally cannot exist at runtime in correctly-used code.

Go's mechanism: **unexported fields + constructor functions + interface hiding**.

### Bad Example: Representable Invalid States

```go
// BAD: This struct can represent invalid combinations
type User struct {
    Email         string // is it valid? is it verified?
    EmailVerified bool   // LOGIC BUG: verified=true but Email="" is possible
    IsGuest       bool
    Username      string // LOGIC BUG: non-guest with no username is possible
}
```

This allows:
- `Email = "", EmailVerified = true` — logically impossible
- `IsGuest = false, Username = ""` — logically impossible

Both invalid states compile and run silently.

### Good Example: Constructor Enforces Validity

```go
// GOOD: unexported fields, public constructor enforces invariants

// guestUser and registeredUser are SEPARATE types
// They cannot be confused or mixed up

type GuestUser struct {
    sessionID string
}

type VerifiedEmail struct {
    address string // private: can only be created via Parse
}

func ParseEmail(raw string) (VerifiedEmail, error) {
    if !strings.Contains(raw, "@") || !strings.Contains(raw, ".") {
        return VerifiedEmail{}, fmt.Errorf("invalid email address: %q", raw)
    }
    return VerifiedEmail{address: raw}, nil
}

func (e VerifiedEmail) String() string { return e.address }

type RegisteredUser struct {
    username string
    email    VerifiedEmail // ONLY verified emails live here
}

func NewRegisteredUser(username string, email VerifiedEmail) (RegisteredUser, error) {
    if strings.TrimSpace(username) == "" {
        return RegisteredUser{}, fmt.Errorf("username cannot be empty")
    }
    return RegisteredUser{username: username, email: email}, nil
}

// The top-level union type: a user is EITHER a guest OR registered — never both
type User struct {
    guest      *GuestUser      // nil when registered
    registered *RegisteredUser // nil when guest
}

func NewGuestUser(sessionID string) User {
    return User{guest: &GuestUser{sessionID: sessionID}}
}

func NewRegisteredUserWrapped(u RegisteredUser) User {
    return User{registered: &u}
}

func (u User) IsGuest() bool      { return u.guest != nil }
func (u User) IsRegistered() bool { return u.registered != nil }
```

This is more verbose than Rust, but the invariants hold: a guest cannot have a username; a registered user cannot have an unverified email.

### The General Principle

Ask yourself about every struct:

> "What combinations of fields represent invalid application states? Can I restructure the types or hide fields so those combinations cannot be constructed?"

```
PROCESS:
1. List all invariants / rules of your domain
2. For each rule, ask: "Can the type system express this?"
3. If yes: encode it in distinct types or constructor constraints
4. If no: encode it with unexported fields + validated constructor
5. Add property-based tests that try to construct invalid states
```

---

## 4. Go's Type System as a Logic Enforcer

Go's type system is simpler than Rust's but has important features that enforce logic when used deliberately.

### 4.1 Strong Static Typing and No Implicit Conversions

Unlike C, Go does not silently coerce numeric types.

```go
var a int32 = 100
var b int64 = 200

// COMPILE ERROR: cannot use a (type int32) as type int64
// result := a + b

// You must be explicit:
result := int64(a) + b // OK — explicit conversion
```

This prevents a whole class of silent type-coercion bugs.

### 4.2 Defined Types vs. Underlying Types

In Go, a **defined type** is distinct from its underlying type even if they share the same underlying structure:

```go
type Meters float64
type Feet float64

// These are DISTINCT types — you cannot add them directly
var m Meters = 10.0
var f Feet = 30.0

// COMPILE ERROR: mismatched types
// total := m + f

// You must explicitly convert, which forces you to think:
totalMeters := m + Meters(f * 0.3048) // intentional conversion
```

This is Go's **newtype pattern** — one of its most underused correctness tools.

### 4.3 Type Assertions and Type Switches — Explicit Downcasting

Go does not allow implicit type conversions. When working with interfaces, you must explicitly assert the underlying type:

```go
var i interface{} = "hello"

// Unsafe type assertion — panics if wrong type
s := i.(string) // panics if i is not a string

// Safe type assertion — returns (value, ok)
s, ok := i.(string)
if !ok {
    // handle type mismatch — no panic
    return fmt.Errorf("expected string, got %T", i)
}

// Type switch — exhaustive matching over types
switch v := i.(type) {
case string:
    fmt.Printf("string: %q\n", v)
case int:
    fmt.Printf("int: %d\n", v)
case nil:
    fmt.Println("nil")
default:
    fmt.Printf("unknown type: %T\n", v)
}
```

**Rule**: Always use the two-value form `v, ok := i.(Type)` in production code. Single-value assertions that panic are partial functions.

### 4.4 The `comparable` Constraint (Generics, Go 1.18+)

Go generics allow constraining type parameters, which enforces logic at compile time:

```go
import "golang.org/x/exp/constraints"

// This function only works on types that can be ordered
// The compiler enforces this — you cannot call it with a struct
func Min[T constraints.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

// This function only works on comparable types (usable as map keys)
func Contains[T comparable](slice []T, item T) bool {
    for _, v := range slice {
        if v == item {
            return true
        }
    }
    return false
}
```

### 4.5 The `any` / `interface{}` Problem

`interface{}` (aliased as `any` in Go 1.18+) accepts ALL types. It is the escape hatch from the type system and a major source of logic bugs:

```go
// BAD: using interface{} defeats type safety
func ProcessItems(items []interface{}) {
    for _, item := range items {
        // You have no idea what type item is
        // Every operation requires a type assertion that can panic
        s := item.(string) // PANIC if item is not a string
        fmt.Println(s)
    }
}

// GOOD: use a concrete type or a constrained interface
func ProcessStrings(items []string) {
    for _, s := range items {
        fmt.Println(s) // always safe — type is known
    }
}

// GOOD with generics: type-safe polymorphism
func ProcessItemsGeneric[T any](items []T, fn func(T)) {
    for _, item := range items {
        fn(item)
    }
}
```

**Rule**: Every use of `interface{}` or `any` is a place where logic bugs can hide. Prefer concrete types, narrow interfaces, or generics.

---

## 5. The nil Problem: Go's Biggest Logic Footgun

`nil` in Go is pervasive — every pointer, interface, slice, map, channel, and function value can be `nil`. This is Go's biggest source of logic bugs, and understanding it deeply is essential.

### 5.1 What nil Means for Each Type

```
TYPE            nil MEANS                          BEHAVIOR
----            ---------                          --------
*T (pointer)    "no value"                         Dereference → PANIC
interface       "no interface value"               Method call → PANIC
                                                   == nil → true (special case)
[]T (slice)     "no backing array"                 len() → 0, cap() → 0
                                                   range → iterates 0 times
                                                   append → works fine
map[K]V         "no hash table"                    Read → zero value (silent!)
                                                   Write → PANIC
chan T           "no channel"                      Send → blocks forever
                                                   Recv → blocks forever
                                                   close() → PANIC
func(...)       "no function"                      Call → PANIC
```

### 5.2 The Interface nil Trap — Go's Most Infamous Bug

This is the single most counterintuitive behavior in Go. Understand it completely.

An **interface value** in Go is a pair: `(type, value)`. An interface is `nil` **only when BOTH the type and value are nil**.

```
INTERFACE VALUE INTERNALS:

  interface{}
  ┌──────────┬──────────┐
  │  *type   │  *value  │
  └──────────┴──────────┘
      │             │
    type info     actual data

  nil interface:   (*type = nil,  *value = nil)  → == nil is TRUE
  non-nil interface with nil pointer:
                   (*type = *MyType, *value = nil) → == nil is FALSE !!
```

```go
// This demonstrates the interface nil trap

type MyError struct {
    msg string
}

func (e *MyError) Error() string { return e.msg }

// BUG: returns a non-nil error even when there's no error!
func riskyOperation() error {
    var err *MyError = nil // concrete nil pointer

    // ... some logic ...

    return err // PROBLEM: wrapping nil *MyError in error interface
    // The interface value is: (*type=*MyError, *value=nil)
    // This is NOT equal to nil!
}

func main() {
    err := riskyOperation()

    // This check FAILS — err is not nil even though *MyError is nil
    if err != nil {
        fmt.Println("Got an error:", err) // THIS PRINTS even though there's no error!
    }
}
```

**Why this happens:**

```
MEMORY LAYOUT:

  var err *MyError = nil
  ┌──────────────────┐
  │  *MyError → nil  │  (concrete nil pointer)
  └──────────────────┘

  return err  →  wraps into interface:
  ┌──────────────────┬──────────────┐
  │  type = *MyError │  value = nil │  ← NOT a nil interface!
  └──────────────────┴──────────────┘
  This interface is != nil
```

**The Fix:**

```go
// CORRECT: return the untyped nil interface directly
func correctOperation() error {
    var err *MyError = nil

    // ... some logic ...

    if err == nil {
        return nil // return untyped nil — interface(nil, nil)
    }
    return err
}

// EVEN BETTER: don't use *MyError as an intermediate at all
func bestOperation() error {
    // ... some logic ...

    // Only return error if there actually is one
    if somethingWentWrong {
        return &MyError{msg: "something went wrong"}
    }
    return nil // always returns the nil interface
}
```

### 5.3 nil Slice vs. Empty Slice

```go
var nilSlice []int    // nil slice: len=0, cap=0, == nil is TRUE
emptySlice := []int{} // empty slice: len=0, cap=0, == nil is FALSE

// Both behave the same for most operations:
fmt.Println(len(nilSlice))   // 0
fmt.Println(len(emptySlice)) // 0
for range nilSlice { }       // no iterations
for range emptySlice { }     // no iterations

// BUT: JSON encoding differs!
import "encoding/json"
data1, _ := json.Marshal(nilSlice)   // "null"
data2, _ := json.Marshal(emptySlice) // "[]"

// RULE: For API responses, explicitly initialize slices to avoid "null" vs "[]"
func GetItems() []Item {
    items := make([]Item, 0) // never returns null in JSON
    // ... fill items ...
    return items
}
```

### 5.4 nil Map: Silent Read, Panic Write

```go
var m map[string]int // nil map

// Reading from a nil map: returns zero value — NO PANIC
value := m["key"] // value = 0, no panic, no error
exists := m["key"] // exists = 0 (zero int), not a bool!

// Safe two-value form
value, ok := m["key"] // value = 0, ok = false — correct

// Writing to a nil map: PANIC
m["key"] = 1 // PANIC: assignment to entry in nil map

// RULE: Always initialize maps before writing
m = make(map[string]int)
m["key"] = 1 // OK
```

### 5.5 Defensive nil Checks as Logic

```go
// Always check nil before dereferencing
func processUser(u *User) error {
    if u == nil {
        return fmt.Errorf("processUser: user must not be nil")
    }
    // safe to use u after this point
    fmt.Println(u.Name)
    return nil
}

// Better: use value semantics to eliminate nil entirely where possible
func processUserValue(u User) {
    fmt.Println(u.Name) // u is always valid, never nil
}

// When nil is meaningful: use pointer and document it
// Config is optional — if nil, defaults are used
func StartServer(cfg *Config) error {
    if cfg == nil {
        cfg = DefaultConfig()
    }
    // ...
}
```

---

## 6. Simulating Sum Types and Enums in Go

Go does not have algebraic sum types (like Rust's `enum`). This is a significant gap. However, there are several patterns to approximate the same safety.

### 6.1 Understanding What Sum Types Give You

In Rust: a value is **exactly one of N variants**. The compiler exhaustively checks all variants.

In Go: you must simulate this, and **the compiler will not catch unhandled cases** unless you design carefully.

```
Rust enum:                      Go equivalent:
enum Shape {                    type Shape interface { shapeKind() }
    Circle(f64),                type Circle struct { Radius float64 }
    Rectangle(f64, f64),        type Rectangle struct { W, H float64 }
    Triangle(f64, f64, f64),    type Triangle struct { A, B, C float64 }
}
// match MUST cover all variants  // switch CAN miss types — no compiler error
```

### 6.2 Pattern 1: iota Constants (Simple Enums)

`iota` creates a sequence of integer constants. This is Go's basic enum mechanism.

```go
// iota: a special constant that auto-increments in a const block
// Think of it as: "the index of this constant in the block, starting from 0"

type OrderStatus int

const (
    OrderStatusDraft      OrderStatus = iota // 0
    OrderStatusSubmitted                     // 1
    OrderStatusProcessing                    // 2
    OrderStatusShipped                       // 3
    OrderStatusDelivered                     // 4
    OrderStatusCancelled                     // 5
)

// Give it a String() method for readability
func (s OrderStatus) String() string {
    switch s {
    case OrderStatusDraft:      return "Draft"
    case OrderStatusSubmitted:  return "Submitted"
    case OrderStatusProcessing: return "Processing"
    case OrderStatusShipped:    return "Shipped"
    case OrderStatusDelivered:  return "Delivered"
    case OrderStatusCancelled:  return "Cancelled"
    default:                    return fmt.Sprintf("OrderStatus(%d)", int(s))
    }
}

// PROBLEM: iota-based enums have a critical flaw
// Nothing prevents an invalid value:
var s OrderStatus = OrderStatus(99) // compiles fine — logically invalid!

// SOLUTION: add a validation method
func (s OrderStatus) IsValid() bool {
    return s >= OrderStatusDraft && s <= OrderStatusCancelled
}
```

### 6.3 Pattern 2: Interface-Based Sum Types (Sealed Hierarchy)

This is Go's closest approximation to Rust's enums with data. The key is a **sealed interface** — an unexported method that only types in the same package can implement.

```go
// The sealed interface: the unexported method is the "seal"
// External packages cannot implement this interface (they can't define unexported methods)
type Shape interface {
    Area() float64
    shapeMarker() // unexported — seals the interface to this package
}

// The variants — each carries its own data
type Circle struct {
    Radius float64
}

func (c Circle) Area() float64     { return math.Pi * c.Radius * c.Radius }
func (c Circle) shapeMarker()      {} // satisfies the seal

type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64  { return r.Width * r.Height }
func (r Rectangle) shapeMarker()   {}

type Triangle struct {
    Base, Height float64
}

func (t Triangle) Area() float64   { return 0.5 * t.Base * t.Height }
func (t Triangle) shapeMarker()    {}

// Type switch over sealed interface — exhaustive by documentation
func Describe(s Shape) string {
    switch v := s.(type) {
    case Circle:
        return fmt.Sprintf("Circle with radius %.2f", v.Radius)
    case Rectangle:
        return fmt.Sprintf("Rectangle %.2f x %.2f", v.Width, v.Height)
    case Triangle:
        return fmt.Sprintf("Triangle base=%.2f height=%.2f", v.Base, v.Height)
    default:
        // This should never happen if the interface is truly sealed
        panic(fmt.Sprintf("unknown Shape type: %T", s))
    }
}
```

### 6.4 Pattern 3: Struct with Discriminant (Tagged Union)

When you want a more C-like tagged union:

```go
// Discriminant type
type PaymentResultKind int

const (
    PaymentSuccess  PaymentResultKind = iota
    PaymentDeclined
    PaymentPending
)

// Tagged union: only the relevant fields are populated per Kind
type PaymentResult struct {
    Kind PaymentResultKind

    // Success fields
    TransactionID string
    AmountCharged int64 // in cents

    // Declined fields
    DeclineReason  string
    RetryAllowed   bool

    // Pending fields
    ConfirmationURL string
}

// BETTER: use separate types for each outcome with a constructor guard
type PaymentSuccessResult struct {
    TransactionID string
    AmountCharged int64
}

type PaymentDeclinedResult struct {
    Reason       string
    RetryAllowed bool
}

type PaymentPendingResult struct {
    ConfirmationURL string
}

// Wrapper with exactly one field non-nil
type PaymentResult struct {
    success  *PaymentSuccessResult
    declined *PaymentDeclinedResult
    pending  *PaymentPendingResult
}

func PaymentSucceeded(txID string, amount int64) PaymentResult {
    return PaymentResult{success: &PaymentSuccessResult{txID, amount}}
}

func PaymentWasDeclined(reason string, retry bool) PaymentResult {
    return PaymentResult{declined: &PaymentDeclinedResult{reason, retry}}
}

func PaymentIsPending(url string) PaymentResult {
    return PaymentResult{pending: &PaymentPendingResult{url}}
}

// Access requires checking which variant is present
func (r PaymentResult) IsSuccess() bool          { return r.success != nil }
func (r PaymentResult) IsDeclined() bool         { return r.declined != nil }
func (r PaymentResult) IsPending() bool          { return r.pending != nil }
func (r PaymentResult) Success() *PaymentSuccessResult   { return r.success }
func (r PaymentResult) Declined() *PaymentDeclinedResult { return r.declined }
func (r PaymentResult) Pending() *PaymentPendingResult   { return r.pending }
```

### 6.5 Exhaustiveness Checking: The Missing Piece

Go lacks exhaustive type switch checking. Use the `exhaustive` linter (part of `golangci-lint`) to compensate:

```go
// Install: go install github.com/nishanths/exhaustive/cmd/exhaustive@latest

// With the linter active, forgetting a case in a type switch or
// a const iota switch triggers a lint error.

// Always add a default case with a panic for truly sealed interfaces:
func handle(s Shape) {
    switch v := s.(type) {
    case Circle:
        // ...
    case Rectangle:
        // ...
    // forgetting Triangle: linter catches it
    default:
        panic(fmt.Sprintf("BUG: unhandled Shape type %T — update handle()", v))
    }
}
```

---

## 7. Interfaces as Logical Contracts

Go's interfaces are its most powerful abstraction tool. When designed well, they enforce behavioral contracts and enable logic correctness through decoupling.

### 7.1 Interface Design Principle: Small and Focused

The Go standard library demonstrates the ideal: one or two methods per interface.

```go
// These are from the standard library — learn from them

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// Composed interfaces:
type ReadWriter interface {
    Reader
    Writer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}
```

**Why small interfaces matter for logic correctness:**
- Easier to verify compliance (fewer methods = fewer places for bugs)
- Easier to mock in tests (a 1-method interface is trivial to mock)
- Forces you to think about what a function *actually* needs

### 7.2 Accept Interfaces, Return Concrete Types

This is a Go proverb. It is a correctness principle, not just style:

```go
// BAD: function accepts and returns a concrete type
// Tightly coupled — hard to test, hard to swap implementations
func ProcessFile(f *os.File) ([]byte, error) {
    return io.ReadAll(f)
}

// GOOD: accept an interface — caller can pass any Reader
// Can be tested with strings.NewReader, bytes.NewReader, etc.
func ProcessData(r io.Reader) ([]byte, error) {
    return io.ReadAll(r)
}

// BAD: return an interface from a constructor
func NewBuffer() io.Writer {
    return &bytes.Buffer{}
    // Caller loses access to Buffer-specific methods
    // Also creates the interface-nil trap risk
}

// GOOD: return concrete type — callers can use all methods
func NewBuffer() *bytes.Buffer {
    return &bytes.Buffer{}
}
```

### 7.3 The error Interface: A Perfect Design

`error` is Go's most used interface:

```go
type error interface {
    Error() string
}
```

One method. Every type that has an `Error() string` method is an `error`. The simplicity is the feature.

### 7.4 Interface Pollution Anti-Pattern

```go
// BAD: interface created before the abstraction is needed
// (this is often premature — who will implement this interface?)
type UserRepository interface {
    Create(ctx context.Context, u User) error
    Read(ctx context.Context, id UserID) (User, error)
    Update(ctx context.Context, u User) error
    Delete(ctx context.Context, id UserID) error
    FindByEmail(ctx context.Context, email Email) (User, error)
    FindByUsername(ctx context.Context, username string) (User, error)
    List(ctx context.Context, page, size int) ([]User, error)
    // ... 20 more methods
}

// A test double for this interface has 20 methods — a maintenance nightmare

// GOOD: define the interface at the point of use
// Define only what THIS function needs

// The auth service only needs to find a user by email:
type UserEmailFinder interface {
    FindByEmail(ctx context.Context, email Email) (User, error)
}

func (s *AuthService) Login(ctx context.Context, email Email, password string) (Token, error) {
    user, err := s.users.FindByEmail(ctx, email) // s.users is UserEmailFinder
    // ...
}
```

### 7.5 Documenting Interface Contracts

```go
// Document the contract — what must an implementation guarantee?

// Hasher computes deterministic hashes of arbitrary data.
//
// Implementations must satisfy:
//   - Hash(data) must return the same value for identical data (deterministic)
//   - Hash(nil) and Hash([]byte{}) must return the same value
//   - The returned slice must not share memory with the input
type Hasher interface {
    Hash(data []byte) []byte
}

// CacheStore provides key-value storage with expiration.
//
// Implementations must satisfy:
//   - Get after Set returns the same value (within TTL)
//   - Get after TTL expiry returns ("", false)
//   - Concurrent access is safe (implementation must be goroutine-safe)
//   - Close releases all resources; subsequent calls return ErrClosed
type CacheStore interface {
    Set(key string, value []byte, ttl time.Duration) error
    Get(key string) ([]byte, bool, error)
    Delete(key string) error
    Close() error
}
```

---

## 8. The Newtype Pattern in Go

The **newtype pattern** creates a distinct named type from an underlying type. This gives different domain concepts distinct types, preventing logical mix-ups at compile time.

### 8.1 The Problem with Primitive Obsession

```go
// BAD: everything is a string or int64 — types carry no domain meaning
func GetOrder(userID int64, productID int64) (*Order, error) { ... }

// This COMPILES but is LOGICALLY WRONG — arguments are swapped:
order, err := GetOrder(productID, userID)
// No error — Go has no way to know you swapped them
```

### 8.2 Newtype Solution

```go
// Create distinct types for each domain concept
type UserID int64
type ProductID int64
type OrderID int64

func GetOrder(userID UserID, productID ProductID) (*Order, error) { ... }

uid := UserID(42)
pid := ProductID(17)

// This now FAILS TO COMPILE — types don't match:
// order, err := GetOrder(pid, uid) // ERROR: cannot use pid (type ProductID) as type UserID

// Only the correct order compiles:
order, err := GetOrder(uid, pid) // OK
```

### 8.3 Newtype with Validation at Construction

The pattern is most powerful when combined with validation. Use **unexported field + exported constructor**:

```go
// Port represents a valid TCP/UDP port number (1–65535)
type Port struct {
    value uint16 // unexported: cannot be set directly
}

// ErrInvalidPort is returned when port construction fails
var ErrInvalidPort = errors.New("port must be between 1 and 65535")

// NewPort is the ONLY way to create a Port
func NewPort(n int) (Port, error) {
    if n < 1 || n > 65535 {
        return Port{}, fmt.Errorf("%w: got %d", ErrInvalidPort, n)
    }
    return Port{value: uint16(n)}, nil
}

// Well-known port constructors — always valid, no error needed
func HTTPPort() Port  { return Port{value: 80} }
func HTTPSPort() Port { return Port{value: 443} }

func (p Port) Value() uint16 { return p.value }
func (p Port) String() string { return fmt.Sprintf("%d", p.value) }

// Once you have a Port, it is GUARANTEED valid — no re-validation needed
func Connect(host string, port Port) error {
    addr := net.JoinHostPort(host, port.String())
    conn, err := net.Dial("tcp", addr)
    // ...
}
```

### 8.4 Non-Empty String

A very common logic bug: treating a potentially-empty string as if it has content.

```go
// NonEmptyString is a string guaranteed to have at least one non-whitespace character
type NonEmptyString struct {
    value string
}

var ErrEmptyString = errors.New("string must not be empty or whitespace")

func NewNonEmptyString(s string) (NonEmptyString, error) {
    trimmed := strings.TrimSpace(s)
    if trimmed == "" {
        return NonEmptyString{}, ErrEmptyString
    }
    return NonEmptyString{value: trimmed}, nil
}

func (s NonEmptyString) String() string { return s.value }

// Function requires a non-empty username — impossible to pass empty
func CreateUser(username NonEmptyString) (*User, error) {
    // No need to check if username is empty — the type guarantees it
    return &User{Username: username.String()}, nil
}
```

### 8.5 Non-Empty Slice

```go
// NonEmptySlice[T] is guaranteed to have at least one element
type NonEmptySlice[T any] struct {
    head T
    tail []T
}

var ErrEmptySlice = errors.New("slice must have at least one element")

func NewNonEmptySlice[T any](items []T) (NonEmptySlice[T], error) {
    if len(items) == 0 {
        return NonEmptySlice[T]{}, ErrEmptySlice
    }
    return NonEmptySlice[T]{
        head: items[0],
        tail: items[1:],
    }, nil
}

// First is ALWAYS safe — no panic possible
func (s NonEmptySlice[T]) First() T { return s.head }

func (s NonEmptySlice[T]) Len() int { return 1 + len(s.tail) }

func (s NonEmptySlice[T]) All() []T {
    result := make([]T, 0, s.Len())
    result = append(result, s.head)
    result = append(result, s.tail...)
    return result
}

// This function is guaranteed to have at least one item
func ProcessItems(items NonEmptySlice[Item]) {
    first := items.First() // always safe — no nil check, no index check
    // ...
}
```

---

## 9. Parse, Don't Validate

This principle — from Alexis King's influential essay — applies directly to Go and solves a pervasive class of logic bugs.

### 9.1 The Core Idea

**Validation** checks if data is valid and returns a boolean or error. The data remains in its original, unconstrained type.

**Parsing** checks if data is valid and, if so, **converts it to a richer type** that structurally encodes validity. After parsing, downstream code cannot access the raw, unvalidated form.

```
VALIDATE approach:                     PARSE approach:
raw string: string                     raw string: string
    │                                      │
    ▼                                      ▼
isValidEmail(raw)                     ParseEmail(raw)
    │                                      │
    ▼                                      ▼
true / false                          (Email{}, nil) or ("", err)
    │                                      │
raw is STILL a string                  Email is a DISTINCT TYPE
(any code downstream can use          (only valid emails can be
 the raw string without checking)      represented — type guarantees it)
```

### 9.2 The Validate Anti-Pattern

```go
// BAD: validate-then-use — validation and use are disconnected

func isValidEmail(s string) bool {
    return strings.Contains(s, "@") && strings.Contains(s, ".")
}

func SendWelcomeEmail(email string) error {
    if !isValidEmail(email) { // validation here...
        return fmt.Errorf("invalid email: %s", email)
    }
    return mailer.Send(email, "Welcome!")
}

func RegisterUser(email string) (*User, error) {
    // LOGIC BUG: developer forgot to validate!
    // They assumed validation happened upstream
    return &User{Email: email}, nil // "not-an-email" accepted silently
}

func SendPasswordReset(email string) error {
    // ANOTHER LOGIC BUG: no validation here either
    return mailer.Send(email, "Reset your password")
}
```

The validation is **disconnected** from usage. It can be forgotten, bypassed, or duplicated inconsistently.

### 9.3 The Parse Pattern in Go

```go
// GOOD: parse into a type that structurally encodes validity

// Email is a valid email address — construction enforces this
type Email struct {
    address string // unexported: only constructable through Parse
}

// Parse is the ONLY way to construct an Email
func ParseEmail(raw string) (Email, error) {
    raw = strings.TrimSpace(raw)
    parts := strings.SplitN(raw, "@", 2)
    if len(parts) != 2 {
        return Email{}, fmt.Errorf("email missing '@' symbol: %q", raw)
    }
    local, domain := parts[0], parts[1]
    if local == "" {
        return Email{}, fmt.Errorf("email local part is empty: %q", raw)
    }
    if !strings.Contains(domain, ".") {
        return Email{}, fmt.Errorf("email domain has no dot: %q", raw)
    }
    return Email{address: raw}, nil
}

func (e Email) String() string { return e.address }

// Functions that need valid emails declare it in their signature
func SendWelcomeEmail(email Email) error {
    // No validation needed — type GUARANTEES it's valid
    return mailer.Send(email.String(), "Welcome!")
}

func RegisterUser(raw string) (*User, error) {
    // Parsing happens ONCE at the boundary
    email, err := ParseEmail(raw)
    if err != nil {
        return nil, fmt.Errorf("register user: %w", err)
    }
    // From here, email is provably valid — no silent bugs downstream
    if err := SendWelcomeEmail(email); err != nil {
        return nil, err
    }
    return &User{Email: email.String()}, nil
}
```

### 9.4 Parse at the Boundary

```
         SYSTEM BOUNDARY (HTTP handler, CLI, config file, external API)
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │   RAW INPUT (string, JSON, form data)  │
         │   - Untrusted                          │
         │   - Unvalidated                        │
         │   - Unconstrained                      │
         └──────────────┬─────────────────────────┘
                        │
                        │  PARSE HERE (once, at the boundary)
                        │
                        ▼
         ┌────────────────────────────────────────┐
         │   DOMAIN TYPES (Email, Port, UserID)   │
         │   - Validated by construction          │
         │   - Constrained — invalid states       │
         │     cannot be expressed                │
         │   - Safe to use anywhere in the app    │
         └──────────────┬─────────────────────────┘
                        │
                        │  Business logic works with domain types
                        │  No re-validation needed anywhere
                        ▼
                   CORE LOGIC
```

### 9.5 Practical: HTTP Handler Boundary

```go
// HTTP handler: the boundary where raw input enters the system
func (h *Handler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req struct {
        Email    string `json:"email"`
        Username string `json:"username"`
        Age      int    `json:"age"`
    }

    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid JSON", http.StatusBadRequest)
        return
    }

    // PARSE at the boundary — all validation happens here
    email, err := ParseEmail(req.Email)
    if err != nil {
        http.Error(w, fmt.Sprintf("invalid email: %v", err), http.StatusBadRequest)
        return
    }

    username, err := NewNonEmptyString(req.Username)
    if err != nil {
        http.Error(w, "username cannot be empty", http.StatusBadRequest)
        return
    }

    age, err := NewAge(req.Age)
    if err != nil {
        http.Error(w, fmt.Sprintf("invalid age: %v", err), http.StatusBadRequest)
        return
    }

    // Beyond this point, all types are domain types — fully validated
    user, err := h.service.CreateUser(r.Context(), email, username, age)
    if err != nil {
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(user)
}
```

---

## 10. Total Functions vs. Partial Functions

### 10.1 Definitions

A **total function** is defined for ALL possible inputs — it always returns a meaningful result.

A **partial function** is only defined for SOME inputs — for others, it panics or returns garbage.

```
Total function:   every valid input → meaningful output
Partial function: some inputs → meaningful output
                  other inputs → panic / zero value / wrong answer
```

### 10.2 Partial Functions Are Logic Bug Sources

```go
// PARTIAL: panics on empty slice
func FirstElement(items []int) int {
    return items[0] // PANIC if items is empty
}

// PARTIAL: returns zero value silently on missing key
func GetValue(m map[string]int, key string) int {
    return m[key] // returns 0 if key missing — is 0 a valid value?
}

// PARTIAL: panics on nil pointer
func UserName(u *User) string {
    return u.Name // PANIC if u is nil
}
```

### 10.3 Making Functions Total in Go

**Strategy 1: Expand the return type to handle absence**

```go
// Total: returns (value, bool) — Go's comma-ok idiom
func FirstElement(items []int) (int, bool) {
    if len(items) == 0 {
        return 0, false
    }
    return items[0], true
}

// Total: returns (value, error) — explicit failure
func FirstElementE(items []int) (int, error) {
    if len(items) == 0 {
        return 0, errors.New("FirstElement: empty slice")
    }
    return items[0], nil
}
```

**Strategy 2: Restrict input type so failure is impossible**

```go
// Total: NonEmptySlice guarantees at least one element
func FirstElement(items NonEmptySlice[int]) int {
    return items.First() // always safe — type guarantees non-empty
}
```

**Strategy 3: Return a default**

```go
func FirstElementOr(items []int, defaultVal int) int {
    if len(items) == 0 {
        return defaultVal
    }
    return items[0]
}
```

### 10.4 The comma-ok Idiom

Go uses a consistent pattern for operations that might fail: return `(value, bool)` or `(value, error)`.

```go
// Map access
value, ok := myMap[key]
if !ok {
    // key not present — handle it
}

// Type assertion
concreteVal, ok := iface.(ConcreteType)
if !ok {
    // wrong type — handle it
}

// Channel receive (non-blocking via select, or detecting closed channel)
value, ok := <-ch
if !ok {
    // channel closed — handle it
}
```

**Always use the two-value form** when you need to distinguish "value is the zero type" from "key/type/channel is absent".

### 10.5 The Zero-Value Problem

Go initializes all variables to their zero value. This is often a bug source:

```go
type Config struct {
    Port    int    // zero value: 0 — invalid port!
    Host    string // zero value: "" — invalid host!
    Timeout time.Duration // zero value: 0 — no timeout!
}

// Someone creates a Config without setting fields:
var cfg Config
server.Start(cfg) // Port=0, Host="" — will fail at runtime, not compile time

// SOLUTION 1: Validate in a constructor
func NewConfig(host string, port int) (Config, error) {
    if host == "" {
        return Config{}, errors.New("host cannot be empty")
    }
    if port < 1 || port > 65535 {
        return Config{}, fmt.Errorf("invalid port: %d", port)
    }
    return Config{Host: host, Port: port, Timeout: 30 * time.Second}, nil
}

// SOLUTION 2: Make zero value meaningful and valid
type Config struct {
    Port    int    // 0 means "use default (8080)"
    Host    string // "" means "use default (localhost)"
    Timeout time.Duration // 0 means "use default (30s)"
}

func (c Config) EffectivePort() int {
    if c.Port == 0 { return 8080 }
    return c.Port
}
```

---

## 11. Invariants: The Core Concept

An **invariant** is a condition that must remain true throughout a value's lifetime. Logic bugs often occur when invariants are violated.

### 11.1 What Is an Invariant?

An invariant is a statement about your data that is **always true**, no matter what operations have been performed.

```
EXAMPLES:

Structural Invariants:
  "A BinarySearchTree node's left child has a smaller key"
  "A SortedSlice is always sorted in ascending order"
  "A min-heap parent is always <= its children"

Business Invariants:
  "Account balance is never negative"
  "Order total matches the sum of line items"
  "A user's age is between 0 and 150"

State Invariants:
  "A database connection is open iff fd > 0"
  "An authenticated session has a non-nil token"
  "Exactly one of {guest, registered} is non-nil in a User"
```

### 11.2 Encoding Invariants with Private Fields

The pattern: **private fields + exported constructor + invariant-preserving methods**.

```go
// SortedSlice maintains the invariant: inner is always sorted ascending
// The invariant is private (enforced by the package) and structural

package sortedslice

type SortedSlice struct {
    inner []int // PRIVATE: external code cannot corrupt the sorted order
}

// New creates an empty SortedSlice — trivially satisfies the invariant
func New() *SortedSlice {
    return &SortedSlice{inner: make([]int, 0)}
}

// FromSlice sorts the input and wraps it — establishes the invariant
func FromSlice(items []int) *SortedSlice {
    sorted := make([]int, len(items))
    copy(sorted, items)
    sort.Ints(sorted)
    return &SortedSlice{inner: sorted}
}

// Insert maintains the invariant: inserted at correct sorted position
func (s *SortedSlice) Insert(value int) {
    pos := sort.SearchInts(s.inner, value)
    // Grow slice by one, shift elements to make room
    s.inner = append(s.inner, 0)
    copy(s.inner[pos+1:], s.inner[pos:])
    s.inner[pos] = value
    // Invariant still holds: element inserted at sorted position
}

// Contains uses binary search — always correct because we know it's sorted
func (s *SortedSlice) Contains(value int) bool {
    idx := sort.SearchInts(s.inner, value)
    return idx < len(s.inner) && s.inner[idx] == value
}

// AsSlice returns a copy — caller cannot corrupt the internal order
func (s *SortedSlice) AsSlice() []int {
    result := make([]int, len(s.inner))
    copy(result, s.inner)
    return result
}

func (s *SortedSlice) Len() int { return len(s.inner) }
```

External code cannot construct a `SortedSlice` with an unsorted inner slice. The invariant is **structurally enforced by package visibility**.

### 11.3 Invariant Verification in Tests

Write explicit invariant checks and use them in tests:

```go
// checkInvariant panics if the invariant is violated — used in tests only
func (s *SortedSlice) checkInvariant(t *testing.T) {
    t.Helper()
    for i := 1; i < len(s.inner); i++ {
        if s.inner[i-1] > s.inner[i] {
            t.Errorf("SortedSlice invariant violated: inner[%d]=%d > inner[%d]=%d",
                i-1, s.inner[i-1], i, s.inner[i])
        }
    }
}

func TestSortedSlice_InsertMaintainsOrder(t *testing.T) {
    s := FromSlice([]int{5, 2, 8, 1, 9})
    s.checkInvariant(t)

    s.Insert(4)
    s.checkInvariant(t) // invariant must hold after every mutation

    s.Insert(0)
    s.checkInvariant(t)

    s.Insert(100)
    s.checkInvariant(t)
}
```

### 11.4 Documenting Invariants in Code

Always document invariants in struct comments:

```go
// BankAccount represents a customer's account balance.
//
// INVARIANTS:
//   - balance >= 0 at all times (no overdraft allowed)
//   - All operations are atomic (protected by mu)
//   - ledger contains a complete history of every transaction
//   - sum(ledger amounts) == balance
type BankAccount struct {
    mu      sync.Mutex
    balance int64  // in cents; invariant: >= 0
    ledger  []Transaction
}

func (a *BankAccount) Deposit(cents int64) error {
    if cents <= 0 {
        return fmt.Errorf("deposit amount must be positive, got %d", cents)
    }
    a.mu.Lock()
    defer a.mu.Unlock()

    a.balance += cents
    a.ledger = append(a.ledger, Transaction{Amount: cents, Type: "deposit"})
    // Invariant maintained: balance was >=0 before, cents>0, so still >=0
    return nil
}

func (a *BankAccount) Withdraw(cents int64) error {
    if cents <= 0 {
        return fmt.Errorf("withdrawal amount must be positive, got %d", cents)
    }
    a.mu.Lock()
    defer a.mu.Unlock()

    if a.balance < cents {
        return fmt.Errorf("insufficient funds: balance=%d, requested=%d", a.balance, cents)
    }
    a.balance -= cents
    a.ledger = append(a.ledger, Transaction{Amount: -cents, Type: "withdrawal"})
    // Invariant maintained: we checked balance >= cents before subtracting
    return nil
}
```

---

## 12. Error Handling as Logic Correctness

Go's error handling is explicit and central to correctness. How you handle errors is a major source of logic bugs.

### 12.1 The Error Hierarchy

```
SEVERITY / RECOVERABILITY (Go's approach)
────────────────────────────────────────►

panic()           — programming bug, invariant violated, should never happen
                    (unreachable code, nil deref in internal logic)

(error, value)    — expected failure, caller MUST handle
with typed errors   (I/O error, parse failure, not found, permission denied)

(value, bool)     — optional value, not an error
comma-ok idiom      (map lookup, type assertion, channel receive)

zero value        — absence is acceptable (use sparingly, document clearly)
```

### 12.2 The Three Kinds of Errors in Go

```go
// KIND 1: Sentinel errors — pre-defined error values compared with ==
// Use for: well-known conditions that callers check by identity
var (
    ErrNotFound      = errors.New("not found")
    ErrUnauthorized  = errors.New("unauthorized")
    ErrAlreadyExists = errors.New("already exists")
)

// Check: if errors.Is(err, ErrNotFound) { ... }

// KIND 2: Typed errors — structs implementing the error interface
// Use for: errors that carry structured data callers need to inspect
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for field %q: %s", e.Field, e.Message)
}

// Check: var ve *ValidationError; if errors.As(err, &ve) { ... }

// KIND 3: Wrapped errors — context added with fmt.Errorf and %w
// Use for: adding context at each layer of the call stack
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("LoadConfig: reading file %q: %w", path, err)
    }
    // ...
}

// Check: if errors.Is(err, os.ErrNotExist) { ... } — unwraps through the chain
```

### 12.3 errors.Is vs errors.As: When to Use Each

```go
// errors.Is: checks if ANY error in the chain matches a SENTINEL value
// Use when you want to compare against a specific error instance
err := doSomething()
if errors.Is(err, ErrNotFound) {
    // err is ErrNotFound, or wraps ErrNotFound somewhere in its chain
}

// errors.As: extracts a TYPED error from anywhere in the chain
// Use when you need data from the error struct
var notFound *NotFoundError
if errors.As(err, &notFound) {
    // notFound is populated with the first *NotFoundError in the chain
    fmt.Printf("resource %q was not found\n", notFound.ResourceID)
}

// WRONG: comparing typed error with == (ignores wrapping)
if err == ErrNotFound { ... } // LOGIC BUG: misses wrapped errors

// WRONG: type asserting error interface
if e, ok := err.(*NotFoundError); ok { ... } // LOGIC BUG: misses wrapped errors

// CORRECT:
if errors.Is(err, ErrNotFound) { ... }
if errors.As(err, &notFoundPtr) { ... }
```

### 12.4 Never Ignore Errors

```go
// BAD: silently ignoring the error
os.Remove(tmpFile)          // if this fails, we don't know — logic bug

// BAD: using _ to silence the compiler
_, _ = fmt.Fprintln(w, msg) // ignoring both n and err

// GOOD: handle or explicitly acknowledge errors
if err := os.Remove(tmpFile); err != nil {
    log.Printf("warning: failed to remove temp file %s: %v", tmpFile, err)
    // decide: is this a fatal error or just a warning?
}

// GOOD: for truly fire-and-forget operations, document the choice
func cleanup(tmpFile string) {
    _ = os.Remove(tmpFile) // intentionally ignored: best-effort cleanup
}
```

### 12.5 Error Wrapping Discipline

Every layer of your stack should add context to errors as they propagate:

```go
// Layer 3: Repository (closest to data)
func (r *UserRepo) FindByID(ctx context.Context, id UserID) (User, error) {
    var u User
    err := r.db.QueryRowContext(ctx, "SELECT * FROM users WHERE id = $1", id).Scan(&u)
    if err == sql.ErrNoRows {
        return User{}, fmt.Errorf("user %d: %w", id, ErrNotFound)
    }
    if err != nil {
        return User{}, fmt.Errorf("user repo find by id %d: %w", id, err)
    }
    return u, nil
}

// Layer 2: Service
func (s *UserService) GetProfile(ctx context.Context, id UserID) (*Profile, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("get profile: %w", err) // wraps with context
    }
    return buildProfile(user), nil
}

// Layer 1: Handler
func (h *Handler) ProfileEndpoint(w http.ResponseWriter, r *http.Request) {
    id, _ := parseUserID(r)
    profile, err := h.service.GetProfile(r.Context(), id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            http.Error(w, "user not found", http.StatusNotFound)
            return
        }
        // Full chain: "get profile: user 42: not found"
        log.Printf("profile endpoint error: %v", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(profile)
}
```

### 12.6 The Multi-Error Pattern

When you need to collect multiple errors:

```go
import "errors"

// errors.Join (Go 1.20+): combine multiple errors into one
func ValidateConfig(cfg Config) error {
    var errs []error

    if cfg.Host == "" {
        errs = append(errs, errors.New("host is required"))
    }
    if cfg.Port < 1 || cfg.Port > 65535 {
        errs = append(errs, fmt.Errorf("invalid port: %d", cfg.Port))
    }
    if cfg.Timeout < 0 {
        errs = append(errs, errors.New("timeout cannot be negative"))
    }

    return errors.Join(errs...) // nil if errs is empty; combined error otherwise
}

// Checking a joined error:
err := ValidateConfig(cfg)
if err != nil {
    // You can still use errors.Is/As on joined errors
    fmt.Println(err) // prints all errors
}
```

---

## 13. The Typestate Pattern in Go

Rust's typestate uses the type system to guarantee operation ordering at compile time. Go cannot fully replicate this (no phantom types, no parameterized methods on a receiver), but a partial version is possible.

### 13.1 The Problem

Many systems have operations that must occur in a specific sequence:
- `Connect()` before `Send()`
- `Authenticate()` before `Query()`
- `Lock()` before accessing protected data

Without typestate, these constraints live only in documentation. Calling them out of order compiles fine.

### 13.2 Go's Approximation: Interface-Based Typestate

The strategy: **use distinct types for distinct states**, expose only the next valid operations.

```go
// State types — each exposes only operations valid in that state

// Step 1: An unconnected database handle
// You can only call Connect() on this
type UnconnectedDB struct {
    host string
    port Port
}

func NewDB(host string, port Port) *UnconnectedDB {
    return &UnconnectedDB{host: host, port: port}
}

// Connect transitions to ConnectedDB — the type changes
func (db *UnconnectedDB) Connect() (*ConnectedDB, error) {
    // perform TCP connection...
    conn, err := net.Dial("tcp", net.JoinHostPort(db.host, db.port.String()))
    if err != nil {
        return nil, fmt.Errorf("connect: %w", err)
    }
    return &ConnectedDB{conn: conn, host: db.host}, nil
}

// Step 2: A connected but unauthenticated handle
// You can only call Authenticate() on this
type ConnectedDB struct {
    conn net.Conn
    host string
}

// Authenticate transitions to AuthenticatedDB
func (db *ConnectedDB) Authenticate(user, pass string) (*AuthenticatedDB, error) {
    // perform auth handshake...
    if err := sendAuthPacket(db.conn, user, pass); err != nil {
        return nil, fmt.Errorf("authenticate: %w", err)
    }
    return &AuthenticatedDB{conn: db.conn}, nil
}

func (db *ConnectedDB) Close() error { return db.conn.Close() }

// Step 3: A fully ready handle — Query and Execute only available here
type AuthenticatedDB struct {
    conn net.Conn
}

func (db *AuthenticatedDB) Query(sql string, args ...any) (Rows, error) {
    // perform query...
    return executeQuery(db.conn, sql, args...)
}

func (db *AuthenticatedDB) Execute(sql string, args ...any) (Result, error) {
    return executeCommand(db.conn, sql, args...)
}

func (db *AuthenticatedDB) Close() error { return db.conn.Close() }
```

Usage — incorrect ordering fails to compile or fails at type-check time:

```go
db := NewDB("localhost", HTTPSPort())

// Cannot call Query on UnconnectedDB — method doesn't exist
// db.Query("SELECT 1") // COMPILE ERROR: db.Query undefined

connected, err := db.Connect()
if err != nil { log.Fatal(err) }

// Cannot call Query on ConnectedDB — method doesn't exist
// connected.Query("SELECT 1") // COMPILE ERROR: connected.Query undefined

authed, err := connected.Authenticate("admin", "secret")
if err != nil { log.Fatal(err) }

// Now Query is available
rows, err := authed.Query("SELECT * FROM users") // OK
```

### 13.3 ASCII Diagram: Typestate Transitions

```
  ┌────────────────────────────────────────────────────────────────────┐
  │               TYPESTATE MACHINE (Go Interface-Based)               │
  └────────────────────────────────────────────────────────────────────┘

  *UnconnectedDB
       │
       │  .Connect() → returns *ConnectedDB (NEW TYPE)
       │               old *UnconnectedDB still exists but has no useful methods
       │
       ▼
  *ConnectedDB
       │
       │  .Authenticate(user, pass) → returns *AuthenticatedDB (NEW TYPE)
       │
       ▼
  *AuthenticatedDB
       │
       ├── .Query()     ← ONLY available on this type
       ├── .Execute()   ← ONLY available on this type
       └── .Close()

  KEY INSIGHT:
  ┌────────────────────────────────────────────────────────────────────┐
  │ Each transition creates a NEW TYPE. Methods are only defined       │
  │ on the correct type. Invalid operations are compile errors.        │
  │                                                                    │
  │ Limitation vs Rust: Go cannot CONSUME the old type, so the caller │
  │ could still hold onto *UnconnectedDB after connecting. Document    │
  │ that the original should not be used after transition.             │
  └────────────────────────────────────────────────────────────────────┘
```

### 13.4 Enforcing Non-Reuse After Transition

Go's approach: use `context.Context` for cancellation and an internal `used` flag:

```go
type UnconnectedDB struct {
    host string
    port Port
    used bool // prevents reuse after Connect()
}

func (db *UnconnectedDB) Connect() (*ConnectedDB, error) {
    if db.used {
        panic("BUG: UnconnectedDB.Connect() called more than once")
    }
    db.used = true
    // ... rest of connect
}
```

---

## 14. State Machines in Go

State machines are one of the best tools for eliminating logic bugs in systems with complex sequential behavior.

### 14.1 Enum + Switch State Machine

```go
type OrderStatus int

const (
    OrderDraft      OrderStatus = iota
    OrderSubmitted
    OrderProcessing
    OrderShipped
    OrderDelivered
    OrderCancelled
)

func (s OrderStatus) String() string {
    names := []string{"Draft", "Submitted", "Processing", "Shipped", "Delivered", "Cancelled"}
    if int(s) < len(names) {
        return names[s]
    }
    return fmt.Sprintf("OrderStatus(%d)", int(s))
}

type Order struct {
    ID     OrderID
    Status OrderStatus
    Items  NonEmptySlice[Item]
}

// ErrInvalidTransition describes an attempted invalid state change
type ErrInvalidTransition struct {
    From OrderStatus
    To   OrderStatus
}

func (e *ErrInvalidTransition) Error() string {
    return fmt.Sprintf("invalid transition: %s → %s", e.From, e.To)
}

// Submit transitions from Draft to Submitted
func (o *Order) Submit() error {
    if o.Status != OrderDraft {
        return &ErrInvalidTransition{From: o.Status, To: OrderSubmitted}
    }
    o.Status = OrderSubmitted
    return nil
}

// Assign transitions from Submitted to Processing
func (o *Order) Assign() error {
    if o.Status != OrderSubmitted {
        return &ErrInvalidTransition{From: o.Status, To: OrderProcessing}
    }
    o.Status = OrderProcessing
    return nil
}

// Ship transitions from Processing to Shipped
func (o *Order) Ship(trackingNumber string) error {
    if o.Status != OrderProcessing {
        return &ErrInvalidTransition{From: o.Status, To: OrderShipped}
    }
    o.Status = OrderShipped
    return nil
}

// Cancel can happen from any non-terminal state
func (o *Order) Cancel(reason string) error {
    switch o.Status {
    case OrderDelivered, OrderCancelled:
        return &ErrInvalidTransition{From: o.Status, To: OrderCancelled}
    default:
        o.Status = OrderCancelled
        return nil
    }
}
```

### 14.2 ASCII Diagram: Order State Machine

```
                    ┌──────────────────────────────────────┐
                    │         ORDER STATE MACHINE          │
                    └──────────────────────────────────────┘

         ┌─────────┐
         │  Draft  │
         └────┬────┘
              │  .Submit()
              ▼
         ┌───────────┐
         │ Submitted │
         └─────┬─────┘
               │  .Assign()
               ▼
         ┌────────────┐
         │ Processing │
         └─────┬──────┘
               │  .Ship(trackingNumber)
               ▼
         ┌─────────┐
         │ Shipped │
         └────┬────┘
              │  .ConfirmDelivery()
              ▼
         ┌───────────┐
         │ Delivered │  ◄── terminal state
         └───────────┘

  From Draft, Submitted, Processing, Shipped → .Cancel()
         │
         ▼
    ┌──────────┐
    │Cancelled │  ◄── terminal state
    └──────────┘

  ENFORCED: terminal states cannot transition further
  ENFORCED: skipping states returns ErrInvalidTransition
```

### 14.3 Transition Table Pattern

Document and test the full transition table:

```go
// transitionTable defines ALL valid (from, to) pairs
// This is the single source of truth for state machine logic
var orderTransitionTable = map[OrderStatus][]OrderStatus{
    OrderDraft:      {OrderSubmitted, OrderCancelled},
    OrderSubmitted:  {OrderProcessing, OrderCancelled},
    OrderProcessing: {OrderShipped, OrderCancelled},
    OrderShipped:    {OrderDelivered, OrderCancelled},
    // OrderDelivered and OrderCancelled: no valid transitions (terminal)
}

func (o *Order) canTransitionTo(next OrderStatus) bool {
    valid, ok := orderTransitionTable[o.Status]
    if !ok {
        return false // terminal state
    }
    for _, v := range valid {
        if v == next {
            return true
        }
    }
    return false
}
```

---

## 15. Domain Modeling for Correctness

Domain modeling is the practice of designing your types to **mirror the real-world domain** as closely as possible. When your types match your domain, many logic bugs become structurally impossible.

### 15.1 Primitive Obsession vs. Rich Domain Model

```go
// BAD: Anemic model — primitives everywhere, no domain meaning
type Order struct {
    UserID     int64
    ProductIDs []int64
    Total      float64  // float for money — WRONG
    Status     string   // "pending"? "active"? "shipped"? any string compiles
    CreatedAt  int64    // unix timestamp? milliseconds? nanoseconds? unclear
}

// GOOD: Rich domain model — types encode domain rules
type Order struct {
    UserID     UserID           // newtype — cannot confuse with ProductID
    Products   NonEmptySlice[ProductID] // at least one product required
    Total      Cents            // integer cents — no float precision bugs
    Status     OrderStatus      // iota enum — only valid values exist
    CreatedAt  time.Time        // standard library time type — no ambiguity
}
```

### 15.2 Money: Never Use Float

This deserves special emphasis. Floating-point arithmetic has precision errors:

```
0.1 + 0.2 = 0.30000000000000004  (in IEEE 754 floating point)
```

In financial calculations, this silently produces wrong results.

```go
// Cents represents a monetary amount in the smallest currency unit
// (cents for USD, pence for GBP, etc.)
type Cents int64

var ErrNegativeAmount = errors.New("monetary amount cannot be negative")
var ErrArithmeticOverflow = errors.New("monetary arithmetic overflow")

func NewCents(amount int64) (Cents, error) {
    if amount < 0 {
        return 0, fmt.Errorf("%w: got %d", ErrNegativeAmount, amount)
    }
    return Cents(amount), nil
}

// FromDollarsAndCents constructs from human-friendly parts
func FromDollarsAndCents(dollars, cents int64) (Cents, error) {
    if cents < 0 || cents >= 100 {
        return 0, fmt.Errorf("cents part must be 0-99, got %d", cents)
    }
    if dollars < 0 {
        return 0, fmt.Errorf("dollars cannot be negative: %d", dollars)
    }
    return Cents(dollars*100 + cents), nil
}

func (c Cents) Dollars() int64    { return int64(c) / 100 }
func (c Cents) CentsPart() int64  { return int64(c) % 100 }
func (c Cents) String() string    { return fmt.Sprintf("$%d.%02d", c.Dollars(), c.CentsPart()) }

// Add returns an error on overflow — never silently wraps
func (c Cents) Add(other Cents) (Cents, error) {
    result := int64(c) + int64(other)
    if int64(c) > 0 && int64(other) > 0 && result < 0 {
        return 0, ErrArithmeticOverflow
    }
    return Cents(result), nil
}

// Sub returns an error if result would be negative (insufficient funds)
func (c Cents) Sub(other Cents) (Cents, error) {
    if int64(c) < int64(other) {
        return 0, fmt.Errorf("insufficient funds: have %s, need %s", c, other)
    }
    return Cents(int64(c) - int64(other)), nil
}
```

### 15.3 Time: Always Carry Location

```go
// BAD: time.Time without location — timezone bugs
type Event struct {
    StartTime time.Time // is this UTC? Local? What timezone?
}

// The zero value of time.Time has Location = UTC, which may not be what you want

// GOOD: be explicit about timezone handling
type Event struct {
    StartTimeUTC time.Time // always UTC — convert for display only
    TimeZone     *time.Location // for display purposes
}

// Always use time.UTC() or time.Local() explicitly:
now := time.Now().UTC()

// When parsing user-provided times, always specify the location:
loc, err := time.LoadLocation("America/New_York")
if err != nil { ... }
t, err := time.ParseInLocation("2006-01-02 15:04:05", input, loc)
```

### 15.4 Encoding Domain Rules in Method Structure

```go
// UserRole encodes permissions — logic is in methods, not in callers
type UserRole int

const (
    RoleGuest UserRole = iota
    RoleMember
    RoleModerator
    RoleAdmin
)

// Logic is CENTRALIZED in the type — not scattered across the codebase
func (r UserRole) CanDeletePosts() bool {
    return r >= RoleModerator
}

func (r UserRole) CanBanUsers() bool {
    return r >= RoleAdmin
}

func (r UserRole) CanAccessAdminPanel() bool {
    return r >= RoleModerator
}

// Usage: clear, readable, impossible to forget a permission check
func DeletePost(ctx context.Context, role UserRole, postID PostID) error {
    if !role.CanDeletePosts() {
        return fmt.Errorf("%w: delete post requires moderator role", ErrUnauthorized)
    }
    // ...
}
```

---

## 16. Builder Pattern and Functional Options

When constructing complex objects with many optional fields and cross-field invariants, Go offers two main patterns.

### 16.1 The Builder Pattern

```go
// ServerConfig has required and optional fields with cross-field invariants
type ServerConfig struct {
    host           string
    port           Port
    maxConnections int
    tls            *TLSConfig // nil means no TLS
    timeout        time.Duration
}

// ServerConfigBuilder accumulates configuration
type ServerConfigBuilder struct {
    host           string
    port           *Port
    maxConnections int
    tls            *TLSConfig
    timeout        time.Duration
    errs           []error // collect errors rather than returning early
}

// NewServerConfigBuilder creates a builder with sensible defaults
func NewServerConfigBuilder() *ServerConfigBuilder {
    return &ServerConfigBuilder{
        maxConnections: 100,
        timeout:        30 * time.Second,
    }
}

func (b *ServerConfigBuilder) WithHost(host string) *ServerConfigBuilder {
    if strings.TrimSpace(host) == "" {
        b.errs = append(b.errs, errors.New("host cannot be empty"))
        return b
    }
    b.host = host
    return b
}

func (b *ServerConfigBuilder) WithPort(port Port) *ServerConfigBuilder {
    b.port = &port
    return b
}

func (b *ServerConfigBuilder) WithMaxConnections(n int) *ServerConfigBuilder {
    if n <= 0 {
        b.errs = append(b.errs, fmt.Errorf("maxConnections must be > 0, got %d", n))
        return b
    }
    b.maxConnections = n
    return b
}

func (b *ServerConfigBuilder) WithTLS(tls *TLSConfig) *ServerConfigBuilder {
    b.tls = tls
    return b
}

func (b *ServerConfigBuilder) WithTimeout(d time.Duration) *ServerConfigBuilder {
    if d < 0 {
        b.errs = append(b.errs, fmt.Errorf("timeout cannot be negative: %v", d))
        return b
    }
    b.timeout = d
    return b
}

// Build performs all cross-field invariant checks and returns the final config
func (b *ServerConfigBuilder) Build() (*ServerConfig, error) {
    // First: check accumulated field errors
    if len(b.errs) > 0 {
        return nil, errors.Join(b.errs...)
    }

    // Required field checks
    if b.host == "" {
        return nil, errors.New("host is required: call WithHost()")
    }
    if b.port == nil {
        return nil, errors.New("port is required: call WithPort()")
    }

    // Cross-field invariant: port 443 requires TLS
    if b.port.Value() == 443 && b.tls == nil {
        return nil, errors.New("port 443 requires TLS configuration: call WithTLS()")
    }

    return &ServerConfig{
        host:           b.host,
        port:           *b.port,
        maxConnections: b.maxConnections,
        tls:            b.tls,
        timeout:        b.timeout,
    }, nil
}

// Usage — reads like a sentence
cfg, err := NewServerConfigBuilder().
    WithHost("api.example.com").
    WithPort(HTTPSPort()).
    WithTLS(tlsCfg).
    WithMaxConnections(500).
    WithTimeout(10 * time.Second).
    Build()
if err != nil { log.Fatal(err) }
```

### 16.2 Functional Options (Rob Pike Pattern)

This is the idiomatic Go approach for optional configuration:

```go
// Option is a function that modifies a serverConfig
type Option func(*serverConfig) error

type serverConfig struct {
    host           string
    port           Port
    maxConnections int
    tls            *TLSConfig
    timeout        time.Duration
}

// Individual option functions

func WithHost(host string) Option {
    return func(c *serverConfig) error {
        if strings.TrimSpace(host) == "" {
            return errors.New("host cannot be empty")
        }
        c.host = host
        return nil
    }
}

func WithPort(port Port) Option {
    return func(c *serverConfig) error {
        c.port = port
        return nil
    }
}

func WithTLS(tls *TLSConfig) Option {
    return func(c *serverConfig) error {
        c.tls = tls
        return nil
    }
}

func WithTimeout(d time.Duration) Option {
    return func(c *serverConfig) error {
        if d < 0 {
            return fmt.Errorf("timeout cannot be negative: %v", d)
        }
        c.timeout = d
        return nil
    }
}

// NewServer applies options and enforces invariants
func NewServer(opts ...Option) (*Server, error) {
    // Start with defaults
    cfg := &serverConfig{
        maxConnections: 100,
        timeout:        30 * time.Second,
    }

    // Apply each option
    for _, opt := range opts {
        if err := opt(cfg); err != nil {
            return nil, fmt.Errorf("NewServer: %w", err)
        }
    }

    // Validate required fields and cross-field invariants
    if cfg.host == "" {
        return nil, errors.New("NewServer: host is required (use WithHost)")
    }

    return &Server{cfg: cfg}, nil
}

// Usage — clean, extensible, self-documenting
server, err := NewServer(
    WithHost("api.example.com"),
    WithPort(HTTPSPort()),
    WithTLS(tlsCfg),
    WithTimeout(10 * time.Second),
)
```

---

## 17. Slices, Maps, and Channels: Logic Traps

These are Go's most common sources of subtle logic bugs. Understand the internals deeply.

### 17.1 Slice Internals

A Go slice is three fields:

```
SLICE HEADER:
┌──────────────┬────────┬──────────┐
│  ptr *array  │ len int│ cap int  │
└──────────────┴────────┴──────────┘
      │
      │  points to
      ▼
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  ← backing array (cap=6)
└─────┴─────┴─────┴─────┴─────┴─────┘
       ↑                       ↑
    len=4                  unused capacity
```

### 17.2 Slice Aliasing — The Shared Backing Array Bug

```go
// Two slices sharing the same backing array:
original := []int{1, 2, 3, 4, 5}
alias := original[1:3] // alias = [2, 3], shares memory with original

alias[0] = 99 // modifying alias ALSO modifies original!
fmt.Println(original) // [1 99 3 4 5] — SURPRISE!

// FIX: explicitly copy when independence is needed
independent := make([]int, len(alias))
copy(independent, alias)
independent[0] = 99 // does NOT affect original
```

### 17.3 Append and Reallocation

```go
// append may or may not reallocate — behavior depends on capacity
s1 := make([]int, 3, 6) // len=3, cap=6
s1 = append(s1, 1, 2, 3) // no realloc: uses remaining capacity

s2 := s1[0:3] // s2 shares backing array with s1

s1 = append(s1, 99) // NO realloc: still within cap=6, writes to shared array
fmt.Println(s2[0]) // s2 is unaffected (its len is 3, the write was at index 6)

// BUT:
s3 := make([]int, 3, 3) // full capacity
s4 := s3[0:2]           // s4 shares backing array
s3 = append(s3, 1)       // REALLOC: new backing array, s4 still points to OLD one
// s3 and s4 now point to DIFFERENT arrays — aliasing is broken silently

// RULE: After append, do not assume the slice shares memory with its sub-slices
// Use copy() when you need guaranteed independence
```

### 17.4 for-range Value Copy Bug

```go
type User struct {
    Name  string
    Score int
}

users := []User{{"Alice", 0}, {"Bob", 0}, {"Charlie", 0}}

// BUG: v is a COPY of each element — modifying v does NOT modify the slice
for _, v := range users {
    v.Score = 100 // modifying the copy, NOT users[i]
}
fmt.Println(users[0].Score) // still 0 — the modification was lost

// FIX 1: Use index to modify in place
for i := range users {
    users[i].Score = 100 // modifying the original element
}

// FIX 2: Use pointer slice
users2 := []*User{{"Alice", 0}, {"Bob", 0}}
for _, v := range users2 {
    v.Score = 100 // v is a pointer — modifying the pointed-to struct
}
```

### 17.5 Goroutine Closure Over Loop Variable

This is one of the most common bugs in Go, especially with goroutines:

```go
// BUG: all goroutines capture the SAME variable i
// By the time they run, i may have already advanced
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i) // BUG: may print 5,5,5,5,5 instead of 0,1,2,3,4
    }()
}

// FIX 1: pass i as an argument (creates a copy per iteration)
for i := 0; i < 5; i++ {
    go func(n int) {
        fmt.Println(n) // n is a per-goroutine copy — correct
    }(i)
}

// FIX 2: create a local copy (Go 1.22+ loop variable semantics fix this by default)
for i := 0; i < 5; i++ {
    i := i // shadows outer i with a new per-iteration variable
    go func() {
        fmt.Println(i) // captures the per-iteration copy — correct
    }()
}

// Note: Go 1.22+ changed loop variable semantics — i is per-iteration by default
// But for older code or for-range with goroutines, always use one of the fixes above
```

### 17.6 Map Concurrency: Always Fatal

```go
// Any concurrent read+write to a map (without synchronization) is UNDEFINED BEHAVIOR
// Go's runtime detects this and PANICS with "concurrent map read and map write"

m := make(map[string]int)

// BUG: two goroutines accessing the map simultaneously
go func() { m["a"] = 1 }()
go func() { _ = m["a"] }()
// Possible outcome: panic, wrong value, or silent corruption

// FIX 1: sync.RWMutex
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func (sm *SafeMap) Set(key string, val int) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    sm.m[key] = val
}

func (sm *SafeMap) Get(key string) (int, bool) {
    sm.mu.RLock()
    defer sm.mu.RUnlock()
    v, ok := sm.m[key]
    return v, ok
}

// FIX 2: sync.Map (for high-read, low-write or key-stable workloads)
var sm sync.Map
sm.Store("key", 42)
val, ok := sm.Load("key")
```

### 17.7 Channel Logic Traps

```go
// TRAP 1: Sending to a nil channel blocks forever
var ch chan int
ch <- 1 // blocks forever — never panics, never proceeds

// TRAP 2: Receiving from a nil channel blocks forever
val := <-ch // blocks forever

// TRAP 3: Sending to a closed channel PANICS
close(ch)
ch <- 1 // PANIC: send on closed channel

// TRAP 4: Reading from a closed channel returns zero value immediately
// Use two-value form to detect closed channel
val, ok := <-ch
if !ok {
    fmt.Println("channel is closed")
}

// TRAP 5: Closing an already-closed channel PANICS
close(ch) // PANIC: close of closed channel

// RULE: The sender owns the channel lifecycle — only the sender should close it
// RULE: Never close a channel from the receiver side
// RULE: Never close a channel that has multiple senders without coordination
```

---

## 18. Integer Arithmetic: Go's Silent Overflow

This section is critical. **Go's integer overflow behavior is one of its biggest logic bug sources.**

Unlike Rust (which panics in debug mode on overflow), **Go integers always wrap silently** in ALL builds — debug and production.

### 18.1 Go Wraps Silently

```go
var x int8 = 127   // maximum int8 value
x++                // NO PANIC — x wraps to -128 silently
fmt.Println(x)     // -128

var y uint8 = 255  // maximum uint8 value
y++                // NO PANIC — y wraps to 0 silently
fmt.Println(y)     // 0
```

This is a **logic bug** — the program runs, produces wrong results, and gives no indication of the problem.

### 18.2 The Binary Search Mid-Point Bug

```go
// CLASSIC BUG: (low + high) can overflow if both are large
func binarySearch(data []int, target int) int {
    low, high := 0, len(data)-1
    for low <= high {
        mid := (low + high) / 2 // BUG: low+high overflows if both near MaxInt
        // ...
    }
    return -1
}

// SAFE: compute difference first, then add half of it
func binarySearchSafe(data []int, target int) int {
    low, high := 0, len(data)-1
    for low <= high {
        mid := low + (high-low)/2 // SAFE: no overflow
        if data[mid] == target {
            return mid
        } else if data[mid] < target {
            low = mid + 1
        } else {
            high = mid - 1
        }
    }
    return -1
}
```

### 18.3 Safe Arithmetic: math/bits and Manual Checks

```go
import "math/bits"

// Checked addition using math/bits
func checkedAddInt64(a, b int64) (int64, bool) {
    result := a + b
    // Overflow occurred if: both positive and result negative,
    // or both negative and result positive
    if (a > 0 && b > 0 && result < 0) || (a < 0 && b < 0 && result > 0) {
        return 0, false
    }
    return result, true
}

// Checked unsigned multiplication
func checkedMulUint64(a, b uint64) (uint64, bool) {
    hi, lo := bits.Mul64(a, b)
    if hi != 0 {
        return 0, false // overflow
    }
    return lo, true
}

// For large numbers: use math/big
import "math/big"

a := new(big.Int).SetInt64(math.MaxInt64)
b := new(big.Int).SetInt64(math.MaxInt64)
result := new(big.Int).Add(a, b) // No overflow — arbitrary precision
fmt.Println(result) // 18446744073709551614
```

### 18.4 The Go 1.21+ Atomic Operations for Integer Safety

```go
import "sync/atomic"

// atomic.Int64 provides safe concurrent integer operations
var counter atomic.Int64

counter.Add(1)   // atomic increment
counter.Load()   // atomic read
counter.Store(0) // atomic write
```

### 18.5 Integer Conversion Bugs

```go
// SILENT TRUNCATION:
var big int64 = 300
var small int8 = int8(big) // truncates to 44 (300 mod 256) — no warning!

// SIGNED/UNSIGNED CONFUSION:
var signed int = -1
var unsigned uint = uint(signed) // uint = 18446744073709551615 (max uint64)

// SAFE CONVERSION FUNCTION:
func int64ToInt8(n int64) (int8, error) {
    if n < math.MinInt8 || n > math.MaxInt8 {
        return 0, fmt.Errorf("value %d overflows int8 range [%d, %d]", n, math.MinInt8, math.MaxInt8)
    }
    return int8(n), nil
}
```

---

## 19. Assertions, Contracts, and Defensive Programming

Go has no built-in `assert` keyword, but there are patterns to enforce invariants at runtime.

### 19.1 Go's Equivalent: Panic with Descriptive Message

```go
// For invariant violations (bugs in YOUR code — should never happen):
func mustBePositive(n int, context string) {
    if n <= 0 {
        panic(fmt.Sprintf("invariant violated in %s: expected positive int, got %d", context, n))
    }
}

// For required conditions at function entry (preconditions):
func binarySearch(data []int, target int) int {
    if data == nil {
        panic("binarySearch: data slice must not be nil")
    }
    // ... search
}
```

### 19.2 Must-Helpers for Initialization

A common Go pattern: `Must` wrappers for operations that should never fail during initialization:

```go
// MustParse panics if parsing fails — use ONLY during initialization
// (program setup, test fixtures, package-level variables)
func MustParseEmail(s string) Email {
    e, err := ParseEmail(s)
    if err != nil {
        panic(fmt.Sprintf("MustParseEmail(%q): %v", s, err))
    }
    return e
}

// Usage at package initialization — if this fails, the program is misconfigured
var adminEmail = MustParseEmail("admin@example.com")

// regexp.MustCompile is the standard library's version of this pattern:
var re = regexp.MustCompile(`^[a-z]+@[a-z]+\.[a-z]{2,6}$`)
// If the regex is invalid, panic at startup — not at request time
```

### 19.3 Panic and Recover for Internal Invariants

Go's `panic`/`recover` pair is analogous to exception handling, but should only be used for internal invariant violations — not normal control flow:

```go
// Use recover at package boundaries to prevent internal panics
// from crashing the entire server
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    defer func() {
        if rv := recover(); rv != nil {
            // Internal bug — log the full stack trace
            log.Printf("PANIC in handler: %v\n%s", rv, debug.Stack())
            http.Error(w, "internal server error", http.StatusInternalServerError)
        }
    }()

    h.route(w, r) // any panic here is caught above
}

// RULE: recover() only makes sense in goroutines you control
// A panic in a goroutine NOT started with the recover deferred will crash the process
```

### 19.4 Defensive Precondition Checking

```go
// Document and enforce preconditions at function entry
// This makes bugs loud (loud failure is better than silent wrong answer)

func Withdraw(balance, amount Cents) (Cents, error) {
    // Precondition: amounts must be non-negative
    if int64(amount) < 0 {
        panic(fmt.Sprintf("Withdraw: amount must be non-negative, got %v", amount))
    }
    // Postcondition will be: result >= 0
    if balance < amount {
        return 0, fmt.Errorf("%w: balance=%v, amount=%v", ErrInsufficientFunds, balance, amount)
    }
    result := Cents(int64(balance) - int64(amount))
    // Verify postcondition (redundant but explicit)
    if int64(result) < 0 {
        panic(fmt.Sprintf("Withdraw postcondition violated: result=%v", result))
    }
    return result, nil
}
```

### 19.5 Build Tags for Assertion-Heavy Debug Builds

```go
// file: assert_debug.go
//go:build debug

package mypackage

func assert(condition bool, msg string) {
    if !condition {
        panic("ASSERTION FAILED: " + msg)
    }
}

// file: assert_release.go
//go:build !debug

package mypackage

// In release builds, assert is a no-op with zero cost
func assert(condition bool, msg string) {}

// Build with assertions: go build -tags debug
// Build without: go build
```

---

## 20. Property-Based Testing

Unit tests check specific cases. Property-based tests check **universal properties** across thousands of randomly generated inputs. This is one of the most effective ways to find logic bugs that manual test cases missed.

### 20.1 What Is a Property?

A **property** is a rule that must hold for ALL valid inputs:

```
"Sorting then reversing gives the same result as sort.Reverse"
"Encoding then decoding returns the original value"
"Inserting into a SortedSlice keeps it sorted"
"Withdrawing more than the balance always fails"
"The sum of all items always equals the total"
```

### 20.2 testing/quick — Standard Library

```go
import "testing/quick"

// Function to test
func Reverse(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

func TestReverseProperty(t *testing.T) {
    // Property: reversing twice returns the original string
    doubleReverseIsIdentity := func(s string) bool {
        return Reverse(Reverse(s)) == s
    }

    if err := quick.Check(doubleReverseIsIdentity, nil); err != nil {
        t.Error(err) // quick shows the failing input
    }
}

func TestReverseLength(t *testing.T) {
    // Property: reverse does not change string length
    lengthPreserved := func(s string) bool {
        return len(Reverse(s)) == len(s)
    }

    if err := quick.Check(lengthPreserved, nil); err != nil {
        t.Error(err)
    }
}
```

### 20.3 rapid — Production-Grade Property Testing

`rapid` is the most capable property-testing library for Go:

```
go get pgregory.net/rapid
```

```go
import "pgregory.net/rapid"

func TestSortedSliceProperties(t *testing.T) {
    // Property 1: after any sequence of inserts, always sorted
    rapid.Check(t, func(t *rapid.T) {
        // Generate a random slice of ints
        items := rapid.SliceOf(rapid.Int()).Draw(t, "items")

        ss := sortedslice.FromSlice(items)

        // Invariant: always sorted
        slice := ss.AsSlice()
        for i := 1; i < len(slice); i++ {
            if slice[i-1] > slice[i] {
                t.Fatalf("not sorted at index %d: %d > %d", i, slice[i-1], slice[i])
            }
        }
    })

    // Property 2: every inserted item is found
    rapid.Check(t, func(t *rapid.T) {
        items := rapid.SliceOf(rapid.Int()).Draw(t, "items")
        newItem := rapid.Int().Draw(t, "newItem")

        ss := sortedslice.FromSlice(items)
        ss.Insert(newItem)

        if !ss.Contains(newItem) {
            t.Fatalf("inserted item %d not found", newItem)
        }
    })

    // Property 3: length after n inserts is original length + n
    rapid.Check(t, func(t *rapid.T) {
        items := rapid.SliceOf(rapid.Int()).Draw(t, "items")
        insertCount := rapid.IntRange(0, 10).Draw(t, "insertCount")

        ss := sortedslice.FromSlice(items)
        originalLen := ss.Len()

        for i := 0; i < insertCount; i++ {
            ss.Insert(rapid.Int().Draw(t, fmt.Sprintf("insert_%d", i)))
        }

        if ss.Len() != originalLen+insertCount {
            t.Fatalf("expected len %d, got %d", originalLen+insertCount, ss.Len())
        }
    })
}
```

### 20.4 Round-Trip Properties

The most powerful property class: encode → decode → same value.

```go
func TestJSONRoundTrip(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        // Generate a random User
        user := User{
            ID:    UserID(rapid.Uint64().Draw(t, "id")),
            Name:  rapid.StringMatching(`[a-zA-Z]{1,50}`).Draw(t, "name"),
            Score: rapid.Int64().Draw(t, "score"),
        }

        // Encode to JSON
        data, err := json.Marshal(user)
        if err != nil {
            t.Fatalf("marshal failed: %v", err)
        }

        // Decode back
        var decoded User
        if err := json.Unmarshal(data, &decoded); err != nil {
            t.Fatalf("unmarshal failed: %v", err)
        }

        // Must be identical
        if user != decoded {
            t.Fatalf("round-trip failed:\n  original: %+v\n  decoded:  %+v", user, decoded)
        }
    })
}
```

### 20.5 Stateful Property Testing: Model-Based Testing

Test a complex system against a simpler model:

```go
// Model: a simple (correct but slow) map
// Implementation: your high-performance SortedSlice

func TestSortedSliceAgainstModel(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        model := make(map[int]struct{})     // simple, obviously correct
        impl := sortedslice.New()           // your implementation

        // Generate a random sequence of operations
        numOps := rapid.IntRange(1, 100).Draw(t, "numOps")
        for i := 0; i < numOps; i++ {
            value := rapid.IntRange(-100, 100).Draw(t, fmt.Sprintf("op_%d_value", i))

            // Apply to both
            model[value] = struct{}{}
            impl.Insert(value)

            // Check consistency
            _, inModel := model[value]
            inImpl := impl.Contains(value)

            if inModel != inImpl {
                t.Fatalf("diverged on Contains(%d): model=%v, impl=%v", value, inModel, inImpl)
            }
        }

        // Final check: all model items are in impl and vice versa
        for v := range model {
            if !impl.Contains(v) {
                t.Fatalf("model has %d but impl doesn't", v)
            }
        }
    })
}
```

---

## 21. Static Analysis and Tooling

Go's tooling ecosystem is one of its greatest strengths for logic correctness. These tools catch what the compiler misses.

### 21.1 go vet — Built-In Checks

`go vet` catches common mistakes. Always run it:

```
go vet ./...
```

What it catches:
- `Printf` format string mismatches (wrong number or type of arguments)
- Unreachable code after `return`/`break`/`continue`
- Misuse of `sync.Mutex` (copying a mutex by value)
- Incorrect use of `testing.T` methods (calling `t.Fatal` in a goroutine)
- Loop variable capture in goroutines (Go 1.22+)
- Comparison of function values (always false/true)

### 21.2 staticcheck — Advanced Static Analysis

```
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...
```

What it catches beyond `go vet`:
- Code that is always `nil` or never `nil`
- Unreachable code
- Deprecated API usage
- Incorrect error handling patterns
- Inefficient string/byte conversions
- Unused parameters, variables, types

### 21.3 errcheck — Error Ignoring Detector

```
go install github.com/kisielk/errcheck@latest
errcheck ./...
```

Catches every ignored `error` return value — even when the developer used `_`:

```go
// errcheck flags all of these:
os.Remove(file)           // error return ignored
ioutil.WriteFile(f, d, 0) // error return ignored
_ = db.Ping()             // explicitly ignored — errcheck can flag this with -asserts
```

### 21.4 golangci-lint — Aggregated Linting

The standard tool for comprehensive linting. Includes 40+ linters:

```
# Install
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run
golangci-lint run ./...
```

Recommended `.golangci.yml` configuration for logic correctness:

```yaml
linters:
  enable:
    - errcheck        # never ignore errors
    - gosimple        # simplify code
    - govet           # built-in vet checks
    - ineffassign     # detect useless assignments
    - staticcheck     # advanced static analysis
    - unused          # detect unused code
    - exhaustive      # exhaustive enum switch checks
    - nilnil          # detect returning (nil, nil) from func(T, error)
    - nilerr          # detect "if err != nil { return nil, nil }"
    - unparam         # detect unused function parameters
    - bodyclose       # ensure HTTP response bodies are closed
    - contextcheck    # ensure context propagation
    - forcetypeassert # prevent unchecked type assertions
    - gocritic        # many additional correctness checks

linters-settings:
  exhaustive:
    default-signifies-exhaustive: false # require handling every case explicitly
```

### 21.5 The Race Detector

Run tests and programs with the race detector:

```
go test -race ./...
go run -race main.go
```

The race detector catches concurrent read/write to the same variable without synchronization. It has a small runtime overhead but is essential for correctness testing.

```
DATA RACE EXAMPLE OUTPUT:
==================
WARNING: DATA RACE
Write at 0x00c0000b4008 by goroutine 7:
  main.increment()
      /home/user/main.go:12 +0x3c
Read at 0x00c0000b4008 by goroutine 6:
  main.readValue()
      /home/user/main.go:18 +0x2c
==================
```

---

## 22. Concurrency Logic Correctness

Go's goroutines and channels are powerful but require disciplined use. The type system provides fewer guarantees here than in Rust.

### 22.1 Go's Memory Model — The Foundation

Understanding Go's **happens-before** guarantees is essential.

```
HAPPENS-BEFORE in Go:

  Initialization:
    Package init() → main.main()

  Goroutines:
    go statement → goroutine start  (NOT guaranteed to execute before caller continues)

  Channels (key rules):
    Send on channel HAPPENS-BEFORE corresponding receive completes
    Close of channel HAPPENS-BEFORE receive that returns zero value
    Receive from unbuffered channel HAPPENS-BEFORE send completes

  Mutex:
    Unlock of mutex HAPPENS-BEFORE subsequent lock of same mutex

  sync.Once:
    f() return HAPPENS-BEFORE any once.Do(f) return

CRITICAL: Any access to a variable from multiple goroutines without
         a happens-before relationship is a DATA RACE = UNDEFINED BEHAVIOR.
```

### 22.2 Time-of-Check-Time-of-Use (TOCTOU)

TOCTOU is a logic race — two concurrent operations produce wrong results even without a data race:

```go
// TOCTOU BUG:
func Transfer(from, to *Account, amount Cents) error {
    // CHECK
    if from.Balance < amount {             // lock released after this check
        return ErrInsufficientFunds
    }
    // <<< another goroutine can withdraw here, making balance < amount >>>
    // USE
    from.Balance -= amount                 // now potentially goes negative!
    to.Balance += amount
    return nil
}

// FIX: hold the lock across the entire check-and-use
func TransferSafe(from, to *Account, amount Cents) error {
    from.mu.Lock()
    defer from.mu.Unlock()

    // CHECK AND USE are now atomic
    if from.Balance < amount {
        return ErrInsufficientFunds
    }
    from.Balance -= amount

    // Release from's lock before acquiring to's (deadlock prevention)
    // Use a separate operation for the credit
    to.mu.Lock()
    to.Balance += amount
    to.mu.Unlock()

    return nil
}
```

### 22.3 Deadlock Prevention — Lock Ordering

```
DEADLOCK SCENARIO:

  Goroutine 1:              Goroutine 2:
  lock(accountA)            lock(accountB)
  ... waiting ...           ... waiting ...
  lock(accountB) ←─ blocked  lock(accountA) ←─ blocked

  Each goroutine holds what the other needs. Circular dependency = deadlock.
```

```go
// RULE: Always acquire locks in a consistent global order
// Use memory address as a tie-breaker for arbitrary pair ordering

func TransferDeadlockFree(a, b *Account, amount Cents) error {
    // Determine lock order by pointer address — consistent across all goroutines
    var first, second *Account
    if uintptr(unsafe.Pointer(a)) < uintptr(unsafe.Pointer(b)) {
        first, second = a, b
    } else {
        first, second = b, a
    }

    first.mu.Lock()
    defer first.mu.Unlock()

    second.mu.Lock()
    defer second.mu.Unlock()

    // Now perform the transfer safely
    if a.Balance < amount {
        return ErrInsufficientFunds
    }
    a.Balance -= amount
    b.Balance += amount
    return nil
}
```

### 22.4 Channel Patterns for Correctness

```go
// PATTERN 1: Done channel for clean shutdown
func worker(jobs <-chan Job, done <-chan struct{}) {
    for {
        select {
        case job, ok := <-jobs:
            if !ok {
                return // channel closed — worker should exit
            }
            processJob(job)
        case <-done:
            return // shutdown signal received
        }
    }
}

// PATTERN 2: context.Context for cancellation (preferred over done channels)
func workerWithContext(ctx context.Context, jobs <-chan Job) {
    for {
        select {
        case job, ok := <-jobs:
            if !ok {
                return
            }
            if err := processJobWithContext(ctx, job); err != nil {
                if errors.Is(err, context.Canceled) {
                    return // context cancelled — clean shutdown
                }
                log.Printf("job error: %v", err)
            }
        case <-ctx.Done():
            return // parent cancelled us
        }
    }
}

// PATTERN 3: Fan-out / Fan-in with sync.WaitGroup
func processAll(ctx context.Context, items []Item) ([]Result, error) {
    results := make([]Result, len(items))
    errs := make([]error, len(items))

    var wg sync.WaitGroup
    for i, item := range items {
        wg.Add(1)
        go func(idx int, it Item) {
            defer wg.Done()
            results[idx], errs[idx] = process(ctx, it)
        }(i, item) // capture i and item by value — no closure bug
    }

    wg.Wait()
    return results, errors.Join(errs...)
}
```

### 22.5 Mutex Best Practices

```go
type SafeCounter struct {
    mu    sync.Mutex
    count int64
}

// RULE 1: Never copy a sync.Mutex — use a pointer receiver
func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock() // defer ensures unlock even if a panic occurs
    c.count++
}

// RULE 2: Keep critical sections small
func (c *SafeCounter) IncrementAndLog() {
    // BAD: logging inside the lock — holds lock longer than needed
    // c.mu.Lock()
    // defer c.mu.Unlock()
    // c.count++
    // log.Printf("count is now %d", c.count) // log is slow!

    // GOOD: minimize what's inside the lock
    c.mu.Lock()
    c.count++
    current := c.count
    c.mu.Unlock() // explicit unlock before the slow operation
    log.Printf("count is now %d", current)
}

// RULE 3: Never call external functions while holding a lock
// (they might try to acquire the same lock → deadlock)
func (c *SafeCounter) ProcessAndNotify(callback func(int64)) {
    // BAD:
    // c.mu.Lock()
    // defer c.mu.Unlock()
    // callback(c.count) // callback might try to read/write c → deadlock

    // GOOD: snapshot value, release lock, then call callback
    c.mu.Lock()
    snapshot := c.count
    c.mu.Unlock()

    callback(snapshot) // lock NOT held — no deadlock risk
}
```

---

## 23. Goroutine Lifecycle and Leak Prevention

A **goroutine leak** is a logic bug where a goroutine is started but never terminates. It wastes memory, CPU, and can hold resources (file handles, connections) open indefinitely.

### 23.1 What Causes Goroutine Leaks

```
LEAK CAUSES:

1. Blocked channel send/receive with no way to unblock
   go func() {
       result := <-ch // nobody ever sends to ch
   }()

2. Waiting on a sync.WaitGroup that never reaches zero
   go func() {
       wg.Wait() // wg.Done() never called
   }()

3. Infinite loop with no exit condition
   go func() {
       for {
           process() // no break, no return, no context check
       }
   }()

4. time.After leaking timers in loops
   for {
       select {
       case <-time.After(1 * time.Second): // new timer created every iteration
           // old timers never GC'd until they fire
       }
   }

5. HTTP response body not closed
   resp, _ := http.Get(url)
   // defer resp.Body.Close() MISSING — connection held open
```

### 23.2 Preventing Goroutine Leaks with Context

```go
// RULE: Every goroutine that runs indefinitely must respect context cancellation

func StartWorker(ctx context.Context) error {
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop() // ALWAYS stop timers when done

    for {
        select {
        case <-ticker.C:
            doPeriodicWork()
        case <-ctx.Done():
            // Context cancelled — clean up and exit
            return ctx.Err()
        }
    }
}

// Caller can stop the worker by cancelling the context
ctx, cancel := context.WithCancel(context.Background())
defer cancel() // ALWAYS defer cancel to prevent goroutine leak

go StartWorker(ctx)
```

### 23.3 time.After in Loops — The Timer Leak

```go
// BAD: new timer created each iteration, old ones accumulate until they fire
func processWithTimeout(jobs <-chan Job) {
    for {
        select {
        case job := <-jobs:
            process(job)
        case <-time.After(5 * time.Second): // LEAK: old timers not GC'd
            log.Println("idle for 5 seconds")
        }
    }
}

// GOOD: create timer once, reset it
func processWithTimeoutFixed(jobs <-chan Job) {
    idleTimer := time.NewTimer(5 * time.Second)
    defer idleTimer.Stop()

    for {
        select {
        case job, ok := <-jobs:
            if !ok {
                return
            }
            process(job)
            // Reset the timer after each job
            if !idleTimer.Stop() {
                select {
                case <-idleTimer.C: // drain if already fired
                default:
                }
            }
            idleTimer.Reset(5 * time.Second)
        case <-idleTimer.C:
            log.Println("idle for 5 seconds")
            idleTimer.Reset(5 * time.Second)
        }
    }
}
```

### 23.4 Detecting Goroutine Leaks in Tests

Use the `goleak` library:

```
go get go.uber.org/goleak
```

```go
import "go.uber.org/goleak"

func TestMain(m *testing.M) {
    // Check for leaked goroutines after all tests complete
    goleak.VerifyTestMain(m)
}

func TestSpecificFunction(t *testing.T) {
    defer goleak.VerifyNone(t) // check at end of this specific test

    startSomeGoroutines()
    // ... test logic ...
    // goleak will fail the test if any goroutines started here are still running
}
```

---

## 24. Algorithm Correctness Patterns

### 24.1 Loop Invariants

A **loop invariant** is a property that must hold:
1. Before the loop starts (**initialization**)
2. After each iteration (**maintenance**)
3. When the loop ends (**termination** — invariant + exit condition = desired result)

```go
// Binary search with explicit loop invariants documented
func BinarySearch(data []int, target int) int {
    low, high := 0, len(data)

    // LOOP INVARIANT:
    //   IF target is in data, it is in data[low:high]
    //   low >= 0 AND high <= len(data) AND low <= high

    for low < high {
        // Invariant holds at top of each iteration

        mid := low + (high-low)/2 // safe mid — no overflow

        if data[mid] == target {
            return mid
        } else if data[mid] < target {
            low = mid + 1
            // Invariant maintained: target is not at mid (data[mid] < target),
            // so it must be in data[mid+1:high] = data[low:high]
        } else {
            high = mid
            // Invariant maintained: target is not at mid (data[mid] > target),
            // so it must be in data[low:mid] = data[low:high]
        }
        // Range [low, high) has strictly decreased each iteration → terminates
    }

    // low == high: invariant says target is in data[low:high] = empty slice
    // Therefore: target is not in data
    return -1
}
```

### 24.2 Off-by-One Error Prevention

Off-by-one errors are the most common algorithm bug. The key is choosing a range convention and sticking to it.

```
CONVENTION: USE HALF-OPEN INTERVALS [low, high)
  - low is INCLUSIVE (first element in range)
  - high is EXCLUSIVE (one past the last element)
  - Length = high - low
  - Empty when low == high
  - Matches Go's slice syntax: data[low:high]
  - Loop condition: for low < high (not <=)

CLOSED INTERVALS [low, high] cause frequent bugs:
  - Length = high - low + 1 (easy to forget the +1)
  - Empty when low > high (negative range)
  - Loop condition: for low <= high (but then low can become > high after high--)
```

```go
// HALF-OPEN INTERVAL pattern — consistent throughout
func sumRange(data []int, start, end int) int {
    // [start, end) — end is EXCLUSIVE
    // Matches data[start:end] semantics
    sum := 0
    for i := start; i < end; i++ { // < not <=
        sum += data[i]
    }
    return sum
}

// SLIDING WINDOW (canonical pattern using half-open intervals)
func maxSumWindow(data []int, k int) int {
    if len(data) < k {
        return 0
    }

    // Window is [left, right) with right - left == k
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += data[i]
    }

    maxSum := windowSum

    // Slide: right extends, left shrinks
    for right := k; right < len(data); right++ {
        left := right - k
        windowSum += data[right]  // include new right element
        windowSum -= data[left]   // exclude old left element
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }

    return maxSum
}
```

### 24.3 Two-Pointer Technique with Invariants

```go
// Removing duplicates from a sorted slice — in-place
// INVARIANT: data[0:writeIdx] always contains the deduplicated prefix
func RemoveDuplicates(data []int) []int {
    if len(data) == 0 {
        return data
    }

    writeIdx := 1 // data[0:1] already unique (trivially)

    // INVARIANT: data[0:writeIdx] is sorted and has no duplicates
    for readIdx := 1; readIdx < len(data); readIdx++ {
        if data[readIdx] != data[writeIdx-1] {
            // New unique value — extend the deduplicated prefix
            data[writeIdx] = data[readIdx]
            writeIdx++
            // Invariant maintained: data[0:writeIdx] still sorted and unique
        }
        // else: duplicate — skip it (writeIdx not incremented)
    }

    // Invariant + loop completion: data[0:writeIdx] is the full deduped result
    return data[:writeIdx]
}
```

### 24.4 Recursion: Base Cases and Progress

Every recursive function needs:
1. A **base case** that terminates the recursion
2. **Progress** — each recursive call must get strictly closer to the base case

```go
// Fibonacci — explicit base cases and progress
func Fibonacci(n int) (int, error) {
    if n < 0 {
        return 0, fmt.Errorf("fibonacci undefined for negative input: %d", n)
    }

    // BASE CASES
    if n == 0 { return 0, nil }
    if n == 1 { return 1, nil }

    // PROGRESS: n-1 and n-2 are both strictly less than n → terminates
    a, _ := Fibonacci(n - 1) // safe: n >= 2, so n-1 >= 1
    b, _ := Fibonacci(n - 2) // safe: n >= 2, so n-2 >= 0
    return a + b, nil
}

// BETTER for large n: use iteration or memoization (avoids stack overflow)
func FibonacciIterative(n int) (int, error) {
    if n < 0 {
        return 0, fmt.Errorf("fibonacci undefined for negative input: %d", n)
    }
    if n <= 1 {
        return n, nil
    }

    prev, curr := 0, 1
    for i := 2; i <= n; i++ {
        prev, curr = curr, prev+curr
    }
    return curr, nil
}
```

---

## 25. Anti-Patterns That Introduce Logic Bugs

### 25.1 Naked Returns — Silent Logic Bugs

Named return values combined with `return` (no arguments) are "naked returns". They are a major source of logic bugs:

```go
// BAD: naked returns — which values are being returned?
func divide(a, b float64) (result float64, err error) {
    if b == 0 {
        err = errors.New("division by zero")
        return // naked: returns (0.0, err) — ok but hard to read
    }
    result = a / b
    return // naked: returns (result, nil) — but what if a later change forgets err = nil?
}

// The danger: if you add a code path that sets err but not result,
// the naked return will return result=0 silently

// GOOD: explicit returns — unambiguous
func divideSafe(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}
```

### 25.2 Shadowed err Variable

```go
// BUG: inner err shadows outer err — outer error is silently dropped
func processItems(db *DB) error {
    tx, err := db.Begin()
    if err != nil {
        return err
    }

    for _, item := range items {
        // BUG: := creates a new `err` variable scoped to this block
        result, err := processItem(tx, item)
        if err != nil {
            tx.Rollback()
            return err
        }
        _ = result
    }

    // This `err` is the OUTER err from db.Begin() — not the loop's err!
    // If the loop never executed, err is nil here — which is correct
    // But the name reuse is confusing and error-prone
    err = tx.Commit()
    return err
}

// GOOD: use consistent variable scoping
func processItemsFixed(db *DB) error {
    tx, err := db.Begin()
    if err != nil {
        return fmt.Errorf("begin transaction: %w", err)
    }

    for _, item := range items {
        if _, err2 := processItem(tx, item); err2 != nil { // different name
            _ = tx.Rollback()
            return fmt.Errorf("process item: %w", err2)
        }
    }

    if err = tx.Commit(); err != nil {
        return fmt.Errorf("commit transaction: %w", err)
    }
    return nil
}
```

### 25.3 init() Misuse

`init()` functions run automatically and silently. They make control flow hard to reason about:

```go
// BAD: init() with side effects that can fail
func init() {
    db, err := sql.Open("postgres", os.Getenv("DATABASE_URL"))
    if err != nil {
        log.Fatal(err) // crashes the program silently during initialization
    }
    globalDB = db // global state — hard to test, hard to reason about
}

// GOOD: explicit initialization in main() or a constructor
func main() {
    cfg, err := LoadConfig()
    if err != nil {
        log.Fatalf("load config: %v", err)
    }

    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        log.Fatalf("open database: %v", err)
    }

    server := NewServer(db, cfg)
    server.Run()
}
```

### 25.4 Global Mutable State

```go
// BAD: global mutable state — any goroutine can corrupt it
var globalCounter int
var globalCache = make(map[string]Item)

func handleRequest() {
    globalCounter++ // data race if called from multiple goroutines
    item := globalCache["key"] // data race
    // ...
}

// GOOD: pass state explicitly or wrap in a type with synchronization
type Server struct {
    counter atomic.Int64
    cache   sync.Map
}

func (s *Server) handleRequest() {
    s.counter.Add(1)
    item, _ := s.cache.Load("key")
    // ...
}
```

### 25.5 Boolean Function Parameters ("Boolean Blindness")

```go
// BAD: what does true mean? What does false mean?
func setActive(user *User, active bool) {
    user.Active = active
}
setActive(user, true) // is true "active" or "inactive"? Not obvious at call site.

// GOOD: explicit type
type ActiveStatus bool

const (
    Active   ActiveStatus = true
    Inactive ActiveStatus = false
)

func setStatus(user *User, status ActiveStatus) {
    user.Active = bool(status)
}
setStatus(user, Active) // unambiguous
```

### 25.6 Using interface{} / any as a Shortcut

```go
// BAD: using any defeats type safety
type Cache struct {
    data map[string]any
}

func (c *Cache) Set(key string, value any) { c.data[key] = value }

func (c *Cache) Get(key string) any {
    return c.data[key]
}

// At the call site — type assertions everywhere, panics waiting to happen:
cache.Set("user", &User{Name: "Alice"})
user := cache.Get("user").(*User) // panics if someone stored something else

// GOOD: use a typed cache or generics
type TypedCache[T any] struct {
    data map[string]T
}

func (c *TypedCache[T]) Set(key string, value T) { c.data[key] = value }
func (c *TypedCache[T]) Get(key string) (T, bool) {
    v, ok := c.data[key]
    return v, ok
}

// No type assertions, no panics:
userCache := &TypedCache[*User]{data: make(map[string]*User)}
userCache.Set("alice", &User{Name: "Alice"})
user, ok := userCache.Get("alice") // user is *User — no assertion needed
```

### 25.7 Defer in a Loop

```go
// BAD: defer inside a loop — cleanup only happens when the FUNCTION returns
// (not at the end of each iteration!)
func processFiles(paths []string) error {
    for _, path := range paths {
        f, err := os.Open(path)
        if err != nil {
            return err
        }
        defer f.Close() // BUG: all closes happen at function exit, not loop end
        // If you open 1000 files, all 1000 are open simultaneously!
        process(f)
    }
    return nil
}

// GOOD: close immediately after each iteration
func processFilesFixed(paths []string) error {
    for _, path := range paths {
        if err := processOneFile(path); err != nil {
            return err
        }
    }
    return nil
}

func processOneFile(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close() // correct: closes when THIS function returns (after each iteration)
    return process(f)
}
```

### 25.8 Modifying a Slice While Iterating

```go
// BAD: modifying the slice you're iterating with for range
items := []int{1, 2, 3, 4, 5}
for i, v := range items {
    if v%2 == 0 {
        items = append(items, v*10) // modifying items during range — undefined behavior
        // range captures the slice header at loop start — new elements not visited
    }
}

// GOOD: iterate over a copy, build a new slice
result := make([]int, 0, len(items))
for _, v := range items { // items is not modified
    result = append(result, v)
    if v%2 == 0 {
        result = append(result, v*10) // adding to result, not items
    }
}
```

---

## 26. The Mental Checklist: A Systematic Thinking Process

Use this checklist when designing any new type, function, or system in Go.

### 26.1 Type Design Checklist

```
When designing a TYPE (struct, interface, type alias):

□ Can I construct an invalid state with this type's public API?
  → If yes: use unexported fields + validated constructor

□ Are any fields primitive when a domain type is appropriate?
  → Use newtype wrappers (type UserID int64, etc.)

□ Does the zero value of this type represent a valid, useful state?
  → If not: require explicit construction (constructor function)
  → "Make the zero value useful" — Go proverb

□ Does this struct have fields that are only valid together?
  → Split into separate types or use a discriminated union struct

□ Am I using interface{} or any where a concrete type works?
  → Use concrete types or constrained generics

□ Does this type have concurrent access?
  → Embed sync.Mutex or sync.RWMutex; document goroutine safety
```

### 26.2 Function Design Checklist

```
When designing a FUNCTION:

□ Is this function total? (handles ALL inputs, returns meaningful result)
  → If not: restrict input types, or return (T, error) / (T, bool)

□ What are the preconditions?
  → Document them; panic on programming errors; return error on usage errors

□ What are the postconditions?
  → Can you express them as test assertions?

□ Does this function return an error? Is the caller required to check it?
  → Never use _ for error returns in production code

□ Does this function spawn goroutines?
  → Does it accept a context.Context for cancellation?
  → Does it guarantee all goroutines exit before returning?

□ Does this function hold a lock?
  → Is the lock scope minimal?
  → Does it call any external functions while holding the lock?

□ Does this function use nil?
  → Every pointer/interface parameter: is nil a valid input? Document it.
  → Is the return value nil-safe?
```

### 26.3 Invariant Design Checklist

```
When maintaining INVARIANTS:

□ Have I listed all invariants of this data structure in a comment?
□ Are fields private to prevent external invariant violation?
□ Is the constructor the only way to create a valid instance?
□ Does every mutation method preserve all invariants?
□ Is there a checkInvariant() method for tests?
□ Are invariants tested with property-based tests (rapid/quick)?
□ Do concurrent access methods hold the lock long enough to maintain invariants?
```

### 26.4 The "What Can Go Wrong" Brainstorm

Before implementing any function, ask:

```
1. nil input?         → What if a pointer/interface/slice/map argument is nil?
2. Empty collection?  → What if a slice/map/channel is empty or has 0 elements?
3. Zero value?        → What if a struct was created with var x T (zero-value)?
4. Overflow?          → What if int arithmetic wraps? (Go wraps silently!)
5. Concurrent access? → Is this called from multiple goroutines?
6. Context cancelled? → Is ctx.Done() checked before long operations?
7. Error ignored?     → Is every error either handled or explicitly documented?
8. Goroutine leak?    → Does every started goroutine have an exit path?
9. Closed channel?    → Could a send be attempted on a closed channel?
10. Float precision?  → Am I using float for money or equality comparison?
```

### 26.5 The ACID Thinking Process for Go Logic

```
ATOMICITY:   Does this operation complete fully or not at all?
             → Use database transactions; hold mutex for full operation;
               avoid partial updates (update A, fail before updating B)

CONSISTENCY: Does this operation leave all invariants intact?
             → Check all invariants after each mutation in tests

ISOLATION:   Can concurrent goroutines corrupt each other's logic?
             → Use sync.Mutex/RWMutex, channels, or atomic operations;
               hold locks for the complete check-and-act sequence

DURABILITY:  If this succeeds, is the result permanent?
             → fsync before returning success; confirm writes; handle
               context cancellation during writes
```

### 26.6 The Layered Defense Model

Logic-correct Go code uses multiple layers simultaneously:

```
LAYER 1 — TYPE SYSTEM (compile time — weakest in Go, still useful)
  ├── Distinct types (type UserID int64, type Email struct{addr string})
  ├── Private fields + constructor enforcement
  ├── Interface-based sealed hierarchies (sum type simulation)
  ├── Newtype pattern for domain concepts
  ├── Parse, don't validate (boundary parsing)
  └── Total functions (return (T, error) or (T, bool))

LAYER 2 — RUNTIME ASSERTIONS AND PANICS (programming errors only)
  ├── panic() for violated invariants (bugs in your code)
  ├── Must-helpers for initialization (MustParseEmail, MustCompile)
  ├── Precondition checks at function entry
  └── Post-condition checks in debug builds (build tags)

LAYER 3 — PROPERTY-BASED TESTING
  ├── pgregory.net/rapid for complex generators
  ├── testing/quick for simple cases
  ├── Invariant properties (after any operation, invariant holds)
  ├── Round-trip properties (encode/decode = identity)
  └── Model-based testing (simple model vs complex implementation)

LAYER 4 — STATIC ANALYSIS
  ├── go vet (always)
  ├── staticcheck (always)
  ├── golangci-lint with exhaustive, errcheck, nilnil, forcetypeassert
  ├── go test -race for concurrency correctness
  └── go.uber.org/goleak for goroutine leak detection

LAYER 5 — SYSTEMATIC CODE REVIEW
  ├── Anti-pattern checklist (nil traps, shadowed err, naked returns)
  ├── Invariant checklist
  ├── Function design checklist
  └── "What can go wrong" brainstorm
```

The strongest Go codebase uses **all five layers**. At minimum, production Go code should always use Layers 1, 2, and 4.

---

## Summary: Go vs. Rust — The Key Differences in Logic Safety

Understanding where Go is weaker than Rust (and compensating) is the mark of a senior Go engineer:

```
TOPIC                  RUST                        GO
─────────────────────────────────────────────────────────────────
Null safety            No null — Option<T>         nil everywhere — must check
Sum types              Exhaustive enum (compile)   Interface sim. (runtime)
Integer overflow       Panics in debug mode        ALWAYS wraps silently
Error handling         Result<T, E> (must use)     (T, error) (can ignore)
Concurrency safety     Borrow checker (compile)    -race flag (runtime only)
Typestate              Compile-time enforced        Interface-based (partial)
Exhaustive matching    Compiler enforces            Linter required (exhaustive)
Zero values            No uninitialised values      Zero value always exists
Goroutine safety       Ownership prevents races     Developer discipline needed
```

For each weakness in Go's column: there is a compensating technique in this guide. The discipline of applying those techniques consistently — even when Go doesn't force you to — is what separates correct Go code from buggy Go code.

---

## Further Reading

- **"Effective Go"** — https://go.dev/doc/effective_go
- **"Go Proverbs"** — Rob Pike — https://go-proverbs.github.io
- **"Go Memory Model"** — https://go.dev/ref/mem (read this carefully)
- **"100 Go Mistakes and How to Avoid Them"** — Teiva Harsanyi (O'Reilly)
- **"Parse, Don't Validate"** — Alexis King — https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/
- **staticcheck documentation** — https://staticcheck.dev/docs/
- **golangci-lint linters** — https://golangci-lint.run/usage/linters/
- **rapid property testing** — https://pkg.go.dev/pgregory.net/rapid
- **go.uber.org/goleak** — https://pkg.go.dev/go.uber.org/goleak
- **"Designing Data-Intensive Applications"** — Martin Kleppmann (concurrency patterns)
- **Go blog: "Errors are values"** — Rob Pike — https://go.dev/blog/errors-are-values
- **Go blog: "Error handling and Go"** — https://go.dev/blog/error-handling-and-go
- **"The Go Programming Language"** — Donovan & Kernighan (Chapter 8-9 on concurrency)

Now I have the full picture of structure, depth, and style. Let me build the Go equivalent — comprehensive, idiomatic, and deep.Good. Now I'll write the full guide — this is a large document so I'll build it systematically.Here is your complete guide — a Go-native counterpart to the Rust one, built with the same depth and rigor but calibrated to Go's specific guarantees, idioms, and footguns.

---

**What this guide covers and why each section matters:**

**Sections 1–4** build the mental model — what Go catches vs. what it doesn't (and why Go's gaps are wider than Rust's), the full taxonomy of logic bugs, and how Go's type system can still enforce logic when used with intention.

**Section 5** is the most critical Go-specific section: the `nil` problem, including the **interface nil trap** (Go's most infamous footgun), the nil map silent-read panic-write asymmetry, and nil channel deadlocks — all with ASCII memory diagrams showing exactly what the runtime sees.

**Sections 6–8** cover Go's approach to algebraic types: sealed interfaces as sum type simulations, iota enums with exhaustiveness checking via linter, the newtype pattern with private fields, and generic `NonEmptySlice[T]`.

**Sections 9–11** cover Parse-Don't-Validate (with a complete HTTP boundary example), total vs. partial functions, and invariants — with private-field-enforced `SortedSlice` and the `checkInvariant()` testing pattern.

**Sections 12–16** cover error handling depth (errors.Is/As, wrapping discipline, multi-error), the typestate pattern in Go (interface-based with ASCII state diagram), state machines with transition tables, rich domain modeling, and both Builder and Functional Options patterns.

**Sections 17–19** are the Go-specific danger zones: slice aliasing and the backing array, for-range value copies, the goroutine loop closure bug, map concurrency (always UB), channel traps, and — critically — **Go's silent integer overflow** with safe arithmetic patterns.

**Sections 20–23** cover property-based testing with `rapid` (including stateful model-based testing), the full static analysis toolchain configuration, concurrency correctness (memory model, TOCTOU, deadlock prevention with lock ordering), and goroutine lifecycle/leak prevention with `goleak`.

**Sections 24–26** complete the guide with algorithm correctness (loop invariants, off-by-one prevention with half-open interval discipline), a full anti-pattern catalog (naked returns, shadowed `err`, defer in loops, `init()` misuse), and the systematic mental checklist including the ACID thinking model and the five-layer defense diagram.