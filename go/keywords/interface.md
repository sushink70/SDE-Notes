# A Comprehensive Guide to Interfaces in Go
## From First Principles to World-Class Mastery

---

> *"The interface is Go's most powerful abstraction tool — not because it hides complexity, but because it reveals structure."*

---

## Table of Contents

1. [The Mental Model: What an Interface Really Is](#1-the-mental-model)
2. [Declaration and Implicit Satisfaction](#2-declaration-and-implicit-satisfaction)
3. [The Interface Internals: iface and eface](#3-interface-internals)
4. [The Empty Interface and `any`](#4-the-empty-interface)
5. [Type Assertions and Type Switches](#5-type-assertions-and-type-switches)
6. [Interface Composition](#6-interface-composition)
7. [Pointer vs Value Receivers](#7-pointer-vs-value-receivers)
8. [Nil Interfaces vs Nil Pointers — The Deadly Trap](#8-nil-interfaces-vs-nil-pointers)
9. [Interface Segregation: Small is Powerful](#9-interface-segregation)
10. [Interfaces for Testing and Dependency Injection](#10-interfaces-for-testing)
11. [Real-World Pattern: The io.Reader/Writer Ecosystem](#11-io-ecosystem)
12. [Real-World Pattern: The http.Handler Chain](#12-http-handler-chain)
13. [Real-World Pattern: The Plugin/Strategy Pattern](#13-plugin-strategy-pattern)
14. [Real-World Pattern: The Functional Options Pattern](#14-functional-options)
15. [Real-World Pattern: Error Handling via Interfaces](#15-error-handling)
16. [Real-World Pattern: The Observer/Event System](#16-observer-pattern)
17. [Real-World Pattern: Pipeline Architecture](#17-pipeline-architecture)
18. [Interface Performance and Escape Analysis](#18-performance)
19. [Generics vs Interfaces: When to Use Which](#19-generics-vs-interfaces)
20. [Anti-Patterns and Common Mistakes](#20-anti-patterns)
21. [Expert Intuition: Design Heuristics](#21-expert-intuition)

---

## 1. The Mental Model

Before writing a single line of code, the expert programmer builds a mental model. In Go, the interface is not an OOP inheritance mechanism — it is a **behavioral contract defined by the caller, not the implementor**.

This is the most important conceptual shift. In Java or C++, you write `implements Foo` — the **author** declares the relationship. In Go, any type that has the required methods **automatically** satisfies the interface. The consumer defines what it needs; the producer doesn't need to know the consumer exists.

```
  Producer                Consumer
  ─────────               ─────────
  type File struct{}      type io.Reader interface {
  func (f *File) Read()       Read(p []byte) (n int, err error)
                          }
  
  No explicit link.
  Satisfaction is structural and implicit.
```

**Mental Model:** An interface is a *lens* through which you view a concrete value. The concrete value exists independently; the interface merely describes which aspect of it you're focusing on.

---

## 2. Declaration and Implicit Satisfaction

```go
package main

import "fmt"

// --- Interface declaration ---
// Convention: single-method interfaces end in -er
type Stringer interface {
    String() string
}

// --- Concrete types (no "implements" keyword) ---
type Point struct {
    X, Y float64
}

// Point satisfies Stringer implicitly
func (p Point) String() string {
    return fmt.Sprintf("(%.2f, %.2f)", p.X, p.Y)
}

type Temperature float64

// Temperature also satisfies Stringer
func (t Temperature) String() string {
    return fmt.Sprintf("%.1f°C", float64(t))
}

// --- Consumer: accepts anything that can String() ---
func PrintAll(items []Stringer) {
    for _, item := range items {
        fmt.Println(item.String())
    }
}

func main() {
    items := []Stringer{
        Point{3.14, 2.71},
        Temperature(36.6),
    }
    PrintAll(items)
}
```

**Key insight:** `Point` and `Temperature` know nothing about `Stringer`. They simply have a method named `String()` with the right signature. This is **structural typing** (also called duck typing, but with compile-time verification).

### Compile-Time Satisfaction Check (Idiomatic Go)

```go
// This pattern forces the compiler to verify satisfaction
// It creates no runtime overhead — the blank identifier discards it
var _ Stringer = Point{}        // value receiver: works
var _ Stringer = (*Point)(nil)  // pointer receiver: works
// var _ Stringer = &Temperature(0) // would fail if Temperature used pointer receiver
```

Use this in package-level code to get early, clear compiler errors instead of confusing "does not implement" messages at call sites deep in your code.

---

## 3. Interface Internals: iface and eface

Understanding the runtime representation is essential for writing performant code and debugging subtle bugs.

### Two Runtime Structs

Go represents interfaces using two internal C structs:

```
// Non-empty interface (has methods)
type iface struct {
    tab  *itab          // pointer to interface+type metadata
    data unsafe.Pointer // pointer to the underlying concrete value
}

// itab contains:
type itab struct {
    inter *interfacetype // the interface type descriptor
    _type *_type         // the concrete type descriptor
    hash  uint32         // copy of _type.hash (for type switches)
    _     [4]byte
    fun   [1]uintptr     // method table (variable-length)
}

// Empty interface (no methods) — simpler
type eface struct {
    _type *_type         // just the type
    data  unsafe.Pointer // pointer to value
}
```

### What This Means Practically

```go
package main

import (
    "fmt"
    "unsafe"
)

type Animal interface {
    Sound() string
}

type Dog struct{ Name string }

func (d Dog) Sound() string { return "Woof" }

func main() {
    var a Animal = Dog{Name: "Rex"}

    // The interface variable 'a' contains TWO words:
    // Word 1: pointer to itab (describes: Animal + Dog + method table)
    // Word 2: pointer to a copy of Dog{Name: "Rex"} on the heap

    fmt.Println(a.Sound())           // dispatched through itab.fun[0]
    fmt.Println(unsafe.Sizeof(a))    // always 16 bytes (two pointers)
}
```

### Method Dispatch Cost

When you call `a.Sound()`, Go does:
1. Load `a.tab` (the itab pointer)
2. Index into `tab.fun` at the method's position
3. Call that function pointer with `a.data` as the receiver

This is **one level of indirection** — essentially the same cost as a C++ virtual call. It is NOT free, but it is extremely cheap. The itab is cached globally per (interface, concrete type) pair.

### Heap Allocation Implication

If the concrete value **fits in a pointer** (≤ 8 bytes on 64-bit and is a simple scalar), Go **may** store it directly in the `data` word, avoiding allocation. Otherwise, the value is **copied to the heap**.

```go
// Likely NO heap allocation — small scalar stored inline
var i interface{} = 42

// Heap allocation — struct too large for inline storage
var a Animal = Dog{Name: "Rex"}
```

Run `go build -gcflags='-m'` to see escape analysis decisions.

---

## 4. The Empty Interface and `any`

```go
// These are identical since Go 1.18
var x interface{} = 42
var y any = 42
```

`any` is just a type alias: `type any = interface{}`.

### When to Use `any` — and When NOT To

```go
// ✅ Legitimate use: truly generic containers before generics existed
type Registry struct {
    data map[string]any
}

// ✅ Legitimate use: encoding/json, fmt — must handle unknown types
func Printf(format string, args ...any) {}

// ❌ Avoid: lazy typing. This loses all type safety.
func Process(x any) any { // what does this even do?
    return x
}

// ✅ Better: use generics (Go 1.18+) or concrete types
func ProcessT[T any](x T) T {
    return x
}
```

### The Reflect Trap

```go
import "reflect"

func PrintType(v any) {
    t := reflect.TypeOf(v)
    fmt.Println(t.Name(), t.Kind())
}

// Note: reflect.TypeOf(nil) returns nil — guard against it
func SafePrintType(v any) {
    if v == nil {
        fmt.Println("<nil>")
        return
    }
    fmt.Println(reflect.TypeOf(v))
}
```

---

## 5. Type Assertions and Type Switches

### Type Assertion

A type assertion extracts the concrete value from an interface.

```go
var a Animal = Dog{Name: "Rex"}

// Single-value form: panics if wrong type
d := a.(Dog)
fmt.Println(d.Name) // "Rex"

// Two-value form: safe, never panics (ALWAYS prefer this)
d, ok := a.(Dog)
if ok {
    fmt.Println(d.Name)
} else {
    fmt.Println("not a Dog")
}
```

**Expert rule:** Use single-value assertion only when you are architecturally certain of the type (e.g., internal package code after a type switch). In all other cases, use the two-value form.

### Type Switch — The Right Tool

```go
type Cat struct{ Name string }
func (c Cat) Sound() string { return "Meow" }

func Describe(a Animal) string {
    switch v := a.(type) {
    case Dog:
        return fmt.Sprintf("Dog named %s", v.Name)
    case Cat:
        return fmt.Sprintf("Cat named %s", v.Name)
    case nil:
        return "nil animal"
    default:
        // v has type Animal here
        return fmt.Sprintf("Unknown animal: %T", v)
    }
}
```

### Asserting to Another Interface

You can assert from one interface to another — this is how you progressively discover capabilities.

```go
type Walker interface {
    Walk() string
}

type SwimmingDog struct{ Name string }
func (s SwimmingDog) Sound() string { return "Woof" }
func (s SwimmingDog) Walk()  string { return "trot" }
func (s SwimmingDog) Swim()  string { return "splash" }

type Swimmer interface {
    Swim() string
}

func TrySwim(a Animal) {
    // Assert from Animal interface to Swimmer interface
    if s, ok := a.(Swimmer); ok {
        fmt.Println("Can swim:", s.Swim())
    } else {
        fmt.Println("Cannot swim")
    }
}
```

---

## 6. Interface Composition

Go's interface composition is one of its most elegant features. You build complex interfaces from simpler ones, mirroring the Single Responsibility Principle.

```go
// Primitive capabilities
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

type Seeker interface {
    Seek(offset int64, whence int) (int64, error)
}

// Compositions — from the standard library
type ReadWriter interface {
    Reader
    Writer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}

type ReadWriteSeeker interface {
    Reader
    Writer
    Seeker
}
```

### Real-World Composition Example: A Storage System

```go
package storage

import (
    "context"
    "time"
)

// Atomic capabilities
type Getter interface {
    Get(ctx context.Context, key string) ([]byte, error)
}

type Setter interface {
    Set(ctx context.Context, key string, value []byte, ttl time.Duration) error
}

type Deleter interface {
    Delete(ctx context.Context, key string) error
}

type Lister interface {
    List(ctx context.Context, prefix string) ([]string, error)
}

// Composed interfaces for different use cases
type ReadOnlyStore interface {
    Getter
    Lister
}

type WriteOnlyStore interface {
    Setter
    Deleter
}

type Store interface {
    Getter
    Setter
    Deleter
    Lister
}

// --- Implementations ---

// RedisStore satisfies Store
type RedisStore struct {
    addr string
    // ... redis client
}

func (r *RedisStore) Get(ctx context.Context, key string) ([]byte, error) {
    // ... redis GET
    return []byte("value"), nil
}

func (r *RedisStore) Set(ctx context.Context, key string, value []byte, ttl time.Duration) error {
    // ... redis SET EX
    return nil
}

func (r *RedisStore) Delete(ctx context.Context, key string) error {
    // ... redis DEL
    return nil
}

func (r *RedisStore) List(ctx context.Context, prefix string) ([]string, error) {
    // ... redis SCAN
    return nil, nil
}

// MemStore — for testing, satisfies Store
type MemStore struct {
    data map[string][]byte
}

func NewMemStore() *MemStore {
    return &MemStore{data: make(map[string][]byte)}
}

func (m *MemStore) Get(_ context.Context, key string) ([]byte, error) {
    v, ok := m.data[key]
    if !ok {
        return nil, fmt.Errorf("key not found: %s", key)
    }
    return v, nil
}

func (m *MemStore) Set(_ context.Context, key string, value []byte, _ time.Duration) error {
    m.data[key] = value
    return nil
}

func (m *MemStore) Delete(_ context.Context, key string) error {
    delete(m.data, key)
    return nil
}

func (m *MemStore) List(_ context.Context, prefix string) ([]string, error) {
    var keys []string
    for k := range m.data {
        if strings.HasPrefix(k, prefix) {
            keys = append(keys, k)
        }
    }
    return keys, nil
}

// Consumer only needs read access — takes the minimal interface
func FindExpired(ctx context.Context, store ReadOnlyStore) ([]string, error) {
    keys, err := store.List(ctx, "session:")
    if err != nil {
        return nil, err
    }
    // ... filter expired sessions
    return keys, nil
}
```

---

## 7. Pointer vs Value Receivers

This is one of the most common sources of confusion. Master it completely.

### The Rule

| Receiver Type | Method Set of Value | Method Set of Pointer |
|--------------|--------------------|-----------------------|
| `func (T) M()`   | ✅ T has M | ✅ *T has M |
| `func (*T) M()`  | ❌ T lacks M | ✅ *T has M |

**Explanation:** A pointer `*T` can always dereference to get `T`, so `*T` has both value and pointer receiver methods. A value `T` cannot take its own address in all contexts (e.g., inside an interface), so `T` only has value receiver methods.

```go
type Counter struct{ n int }

func (c Counter) Value() int   { return c.n }     // value receiver
func (c *Counter) Inc()        { c.n++ }           // pointer receiver

var _ interface{ Value() int } = Counter{}   // ✅
var _ interface{ Value() int } = &Counter{}  // ✅

// var _ interface{ Inc() } = Counter{}  // ❌ COMPILE ERROR
var _ interface{ Inc() } = &Counter{}    // ✅
```

### The Practical Rule

**Use pointer receivers when:**
- The method modifies the receiver
- The struct is large (avoid copying)
- You need to maintain consistency (if any method uses pointer receiver, use it for all)

**Use value receivers when:**
- The type is a small scalar (int, float, etc.)
- Immutable value semantics are desired (like `time.Time`)
- The method is truly read-only and the type is small

```go
// Good value receiver — small, immutable semantics
type Celsius float64
func (c Celsius) ToFahrenheit() Fahrenheit { return Fahrenheit(c*9/5 + 32) }

// Good pointer receiver — modifies state
type Buffer struct{ data []byte }
func (b *Buffer) Write(p []byte) (int, error) {
    b.data = append(b.data, p...)
    return len(p), nil
}
```

---

## 8. Nil Interfaces vs Nil Pointers — The Deadly Trap

This is the single most dangerous footgun in Go's interface system. Burn this into memory.

### The Problem

```go
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

// BUGGY function — returns typed nil
func findUser(id int) error {
    var err *MyError // nil pointer to MyError

    if id < 0 {
        err = &MyError{"invalid id"}
    }

    // BUG: even if err is nil *MyError,
    // returning it as 'error' wraps it in an interface
    // The interface value is NOT nil — it has a type (*MyError) but nil data
    return err
}

func main() {
    err := findUser(1) // no error case

    // This is TRUE even though err "looks" nil:
    fmt.Println(err == nil) // false ← SURPRISE
    fmt.Println(err)        // <nil>  ← confusing
}
```

### Why This Happens

```
Return type: error (interface)

When err is *MyError nil:
    interface{tab: *itab(error+*MyError), data: nil}
    
This is NOT a nil interface.
A nil interface requires BOTH tab AND data to be nil.
```

### The Fix

```go
// CORRECT — return untyped nil for the interface
func findUser(id int) error {
    if id < 0 {
        return &MyError{"invalid id"}
    }
    return nil // untyped nil — interface tab AND data are nil
}

// Or, if you need to build the error conditionally:
func findUserV2(id int) error {
    var err *MyError
    if id < 0 {
        err = &MyError{"invalid id"}
    }
    if err != nil { // check the concrete pointer
        return err
    }
    return nil // explicitly return nil interface
}
```

### The General Rule

**Never return a typed nil as an interface.** If your function returns an interface type (`error`, `io.Reader`, etc.), always `return nil` for the success case — never `return (*ConcreteType)(nil)`.

---

## 9. Interface Segregation: Small is Powerful

The **Interface Segregation Principle** from SOLID maps perfectly to Go. Small, focused interfaces are more reusable than large ones.

```go
// ❌ FAT interface — hard to mock, over-constraining
type UserRepository interface {
    CreateUser(u User) error
    GetUser(id int) (User, error)
    UpdateUser(u User) error
    DeleteUser(id int) error
    ListUsers(filter Filter) ([]User, error)
    CountUsers(filter Filter) (int, error)
    GetUserByEmail(email string) (User, error)
    GetUsersByRole(role string) ([]User, error)
    // ... 20 more methods
}

// ✅ SEGREGATED interfaces — each consumer takes only what it needs
type UserCreator interface {
    CreateUser(u User) error
}

type UserFinder interface {
    GetUser(id int) (User, error)
    GetUserByEmail(email string) (User, error)
}

type UserLister interface {
    ListUsers(filter Filter) ([]User, error)
    CountUsers(filter Filter) (int, error)
}

// Services declare ONLY what they need
type EmailService struct {
    finder UserFinder // only needs to look up users
}

type AdminService struct {
    finder  UserFinder
    lister  UserLister
    creator UserCreator
}
```

**Cognitive model:** Think of interface segregation as *role-based dependency injection*. Each service declares the role it needs, not the concrete implementation.

---

## 10. Interfaces for Testing and Dependency Injection

This is one of the highest-value applications of interfaces in production Go code.

```go
package payment

import (
    "context"
    "time"
)

// --- Domain types ---
type PaymentIntent struct {
    ID       string
    Amount   int64
    Currency string
}

type Charge struct {
    ID        string
    Amount    int64
    CreatedAt time.Time
}

// --- Interface: the seam for testing ---
type PaymentProcessor interface {
    CreateIntent(ctx context.Context, amount int64, currency string) (*PaymentIntent, error)
    ConfirmPayment(ctx context.Context, intentID string) (*Charge, error)
    RefundCharge(ctx context.Context, chargeID string, amount int64) error
}

// --- Real implementation (uses Stripe, etc.) ---
type StripeProcessor struct {
    apiKey string
    client *http.Client
}

func (s *StripeProcessor) CreateIntent(ctx context.Context, amount int64, currency string) (*PaymentIntent, error) {
    // ... real HTTP call to Stripe
    return &PaymentIntent{ID: "pi_real", Amount: amount, Currency: currency}, nil
}

func (s *StripeProcessor) ConfirmPayment(ctx context.Context, intentID string) (*Charge, error) {
    // ... real Stripe confirm
    return &Charge{ID: "ch_real", Amount: 1000, CreatedAt: time.Now()}, nil
}

func (s *StripeProcessor) RefundCharge(ctx context.Context, chargeID string, amount int64) error {
    // ... real Stripe refund
    return nil
}

// --- Service: depends on interface, not Stripe ---
type OrderService struct {
    payments PaymentProcessor
    // ... other deps
}

func NewOrderService(payments PaymentProcessor) *OrderService {
    return &OrderService{payments: payments}
}

func (o *OrderService) Checkout(ctx context.Context, orderID string, amount int64) (*Charge, error) {
    intent, err := o.payments.CreateIntent(ctx, amount, "usd")
    if err != nil {
        return nil, fmt.Errorf("create intent: %w", err)
    }

    charge, err := o.payments.ConfirmPayment(ctx, intent.ID)
    if err != nil {
        return nil, fmt.Errorf("confirm payment: %w", err)
    }

    return charge, nil
}

// --- Test double: in-package _test.go ---
// (or use a mocking library like testify/mock or gomock)

type MockPaymentProcessor struct {
    createIntentFn  func(ctx context.Context, amount int64, currency string) (*PaymentIntent, error)
    confirmPaymentFn func(ctx context.Context, intentID string) (*Charge, error)
    refundChargeFn  func(ctx context.Context, chargeID string, amount int64) error
}

func (m *MockPaymentProcessor) CreateIntent(ctx context.Context, amount int64, currency string) (*PaymentIntent, error) {
    return m.createIntentFn(ctx, amount, currency)
}

func (m *MockPaymentProcessor) ConfirmPayment(ctx context.Context, intentID string) (*Charge, error) {
    return m.confirmPaymentFn(ctx, intentID)
}

func (m *MockPaymentProcessor) RefundCharge(ctx context.Context, chargeID string, amount int64) error {
    return m.refundChargeFn(ctx, chargeID, amount)
}

// --- Test ---
func TestCheckout_Success(t *testing.T) {
    mock := &MockPaymentProcessor{
        createIntentFn: func(ctx context.Context, amount int64, currency string) (*PaymentIntent, error) {
            return &PaymentIntent{ID: "pi_test_123", Amount: amount}, nil
        },
        confirmPaymentFn: func(ctx context.Context, intentID string) (*Charge, error) {
            if intentID != "pi_test_123" {
                t.Fatalf("unexpected intentID: %s", intentID)
            }
            return &Charge{ID: "ch_test_456", Amount: 1000}, nil
        },
    }

    svc := NewOrderService(mock)
    charge, err := svc.Checkout(context.Background(), "order_1", 1000)

    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if charge.ID != "ch_test_456" {
        t.Errorf("got charge %s, want ch_test_456", charge.ID)
    }
}
```

---

## 11. Real-World Pattern: The io.Reader/Writer Ecosystem

The `io` package is the crown jewel of Go's interface design. Study it to understand what "right" looks like.

```go
// The two most important interfaces in Go's stdlib:
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
```

The genius: **anything that produces bytes is a Reader; anything that consumes bytes is a Writer**. Files, network connections, HTTP bodies, compressed streams, encryption layers, buffers — they all compose.

### Building a Data Pipeline with io

```go
package main

import (
    "bytes"
    "compress/gzip"
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "encoding/hex"
    "fmt"
    "io"
    "os"
    "strings"
)

// compressAndCount: wraps a writer to compress data AND count bytes written
type countingWriter struct {
    w     io.Writer
    total int64
}

func (cw *countingWriter) Write(p []byte) (int, error) {
    n, err := cw.w.Write(p)
    cw.total += int64(n)
    return n, err
}

// Pipeline: Read from string → gzip → count → write to file
func compressPipeline(data string, outPath string) (int64, error) {
    // Step 1: source — a string reader
    src := strings.NewReader(data)

    // Step 2: destination — a file writer
    dst, err := os.Create(outPath)
    if err != nil {
        return 0, err
    }
    defer dst.Close()

    // Step 3: counting wrapper
    counter := &countingWriter{w: dst}

    // Step 4: gzip writer wrapping the counter
    gz := gzip.NewWriter(counter)
    defer gz.Close()

    // Step 5: copy — no knowledge of what src or gz actually are
    if _, err := io.Copy(gz, src); err != nil {
        return 0, err
    }
    if err := gz.Close(); err != nil {
        return 0, err
    }

    return counter.total, nil
}

// TeeReader: reads from src, writes a copy to w (like Unix tee)
func auditedRead(src io.Reader, audit io.Writer) io.Reader {
    return io.TeeReader(src, audit)
}

// MultiWriter: write to multiple destinations simultaneously
func broadcastWrite(data []byte, destinations ...io.Writer) error {
    mw := io.MultiWriter(destinations...)
    _, err := mw.Write(data)
    return err
}

// LimitReader: never read more than N bytes (defense against huge inputs)
func safeFetch(body io.Reader) ([]byte, error) {
    limited := io.LimitReader(body, 10*1024*1024) // 10MB max
    return io.ReadAll(limited)
}

func main() {
    n, err := compressPipeline("Hello, World! This is a test of the pipeline.", "/tmp/test.gz")
    if err != nil {
        panic(err)
    }
    fmt.Printf("Compressed bytes written: %d\n", n)

    // Broadcast: write to stdout AND a buffer simultaneously
    var buf bytes.Buffer
    err = broadcastWrite([]byte("broadcast message\n"), os.Stdout, &buf)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Buffer captured: %q\n", buf.String())
}
```

### Implementing io.Reader Correctly

```go
// A custom Reader that generates Fibonacci numbers as ASCII
type FibReader struct {
    a, b   uint64
    buf    []byte
    done   bool
    limit  int
    count  int
}

func NewFibReader(limit int) *FibReader {
    return &FibReader{a: 0, b: 1, limit: limit}
}

func (f *FibReader) Read(p []byte) (int, error) {
    // Flush buffered data first
    if len(f.buf) > 0 {
        n := copy(p, f.buf)
        f.buf = f.buf[n:]
        return n, nil
    }

    if f.done || f.count >= f.limit {
        return 0, io.EOF
    }

    // Generate next Fibonacci number
    s := fmt.Sprintf("%d\n", f.a)
    f.a, f.b = f.b, f.a+f.b
    f.count++

    // Copy as much as fits; buffer the rest
    n := copy(p, s)
    if n < len(s) {
        f.buf = append(f.buf, s[n:]...)
    }
    return n, nil
}

func main() {
    fib := NewFibReader(10)
    io.Copy(os.Stdout, fib) // prints first 10 Fibonacci numbers
}
```

---

## 12. Real-World Pattern: The http.Handler Chain

```go
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "time"
)

// http.Handler is one of the most elegant interfaces in Go:
// type Handler interface {
//     ServeHTTP(ResponseWriter, *Request)
// }

// --- Middleware type ---
type Middleware func(http.Handler) http.Handler

// Chain composes multiple middlewares left-to-right
func Chain(h http.Handler, middlewares ...Middleware) http.Handler {
    // Apply in reverse so leftmost runs first
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

// --- Middleware 1: Request logging ---
func Logger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        // Wrap ResponseWriter to capture status code
        lrw := &loggingResponseWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(lrw, r)
        log.Printf("%s %s %d %v", r.Method, r.URL.Path, lrw.status, time.Since(start))
    })
}

type loggingResponseWriter struct {
    http.ResponseWriter
    status int
}

func (lrw *loggingResponseWriter) WriteHeader(code int) {
    lrw.status = code
    lrw.ResponseWriter.WriteHeader(code)
}

// --- Middleware 2: Authentication ---
type contextKey string
const userKey contextKey = "user"

func Auth(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "unauthorized", http.StatusUnauthorized)
            return
        }
        // In real code: validate JWT, extract user
        ctx := context.WithValue(r.Context(), userKey, "user_123")
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// --- Middleware 3: Rate limiting (simplified) ---
func RateLimit(rps int) Middleware {
    ticker := time.NewTicker(time.Second / time.Duration(rps))
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            select {
            case <-ticker.C:
                next.ServeHTTP(w, r)
            default:
                http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
            }
        })
    }
}

// --- Middleware 4: Panic recovery ---
func Recovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("panic: %v", err)
                http.Error(w, "internal server error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// --- Handler ---
func helloHandler(w http.ResponseWriter, r *http.Request) {
    user := r.Context().Value(userKey).(string)
    fmt.Fprintf(w, "Hello, %s!", user)
}

func main() {
    mux := http.NewServeMux()

    // Public route: only logging + recovery
    publicHandler := Chain(
        http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            fmt.Fprint(w, "public endpoint")
        }),
        Recovery,
        Logger,
    )

    // Protected route: full middleware stack
    protectedHandler := Chain(
        http.HandlerFunc(helloHandler),
        Recovery,
        RateLimit(100),
        Auth,
        Logger,
    )

    mux.Handle("/public", publicHandler)
    mux.Handle("/api/hello", protectedHandler)

    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", mux))
}
```

**Key insight:** `http.HandlerFunc` is a **function type** that implements `http.Handler`. This is a common Go pattern — adapting a function to satisfy an interface without creating a struct.

```go
// From the standard library — study this pattern:
type HandlerFunc func(ResponseWriter, *Request)

func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) {
    f(w, r)
}
```

---

## 13. Real-World Pattern: The Plugin/Strategy Pattern

```go
package main

import (
    "fmt"
    "sort"
)

// --- Strategy Pattern: Sorting ---

type SortStrategy[T any] interface {
    Sort(data []T)
    Name() string
}

// QuickSort strategy
type QuickSort[T any] struct {
    less func(a, b T) bool
}

func (q *QuickSort[T]) Sort(data []T) {
    sort.Slice(data, func(i, j int) bool {
        return q.less(data[i], data[j])
    })
}

func (q *QuickSort[T]) Name() string { return "quicksort" }

// BubbleSort strategy (for small data)
type BubbleSort[T any] struct {
    less func(a, b T) bool
}

func (b *BubbleSort[T]) Sort(data []T) {
    n := len(data)
    for i := 0; i < n-1; i++ {
        for j := 0; j < n-i-1; j++ {
            if !b.less(data[j], data[j+1]) {
                data[j], data[j+1] = data[j+1], data[j]
            }
        }
    }
}

func (b *BubbleSort[T]) Name() string { return "bubblesort" }

// Sorter context — uses a strategy
type Sorter[T any] struct {
    strategy SortStrategy[T]
}

func NewSorter[T any](strategy SortStrategy[T]) *Sorter[T] {
    return &Sorter[T]{strategy: strategy}
}

func (s *Sorter[T]) SetStrategy(strategy SortStrategy[T]) {
    s.strategy = strategy
}

func (s *Sorter[T]) Sort(data []T) {
    fmt.Printf("Sorting with %s...\n", s.strategy.Name())
    s.strategy.Sort(data)
}

// --- Plugin Pattern: Notification System ---

type NotificationChannel interface {
    Send(to, subject, body string) error
    Name() string
}

type EmailChannel struct{ smtpAddr string }
func (e *EmailChannel) Send(to, subject, body string) error {
    fmt.Printf("[EMAIL] to=%s subject=%s\n", to, subject)
    return nil
}
func (e *EmailChannel) Name() string { return "email" }

type SlackChannel struct{ webhookURL string }
func (s *SlackChannel) Send(to, subject, body string) error {
    fmt.Printf("[SLACK] channel=%s msg=%s\n", to, body)
    return nil
}
func (s *SlackChannel) Name() string { return "slack" }

type SMSChannel struct{ apiKey string }
func (s *SMSChannel) Send(to, subject, body string) error {
    fmt.Printf("[SMS] to=%s msg=%s\n", to, body)
    return nil
}
func (s *SMSChannel) Name() string { return "sms" }

// NotificationService: runtime plugin registry
type NotificationService struct {
    channels map[string]NotificationChannel
}

func NewNotificationService() *NotificationService {
    return &NotificationService{channels: make(map[string]NotificationChannel)}
}

func (ns *NotificationService) Register(channel NotificationChannel) {
    ns.channels[channel.Name()] = channel
}

func (ns *NotificationService) Notify(channelName, to, subject, body string) error {
    ch, ok := ns.channels[channelName]
    if !ok {
        return fmt.Errorf("unknown channel: %s", channelName)
    }
    return ch.Send(to, subject, body)
}

func (ns *NotificationService) BroadcastAll(to, subject, body string) []error {
    var errs []error
    for _, ch := range ns.channels {
        if err := ch.Send(to, subject, body); err != nil {
            errs = append(errs, fmt.Errorf("%s: %w", ch.Name(), err))
        }
    }
    return errs
}

func main() {
    // Strategy pattern
    data := []int{5, 3, 8, 1, 9, 2}
    sorter := NewSorter(&QuickSort[int]{less: func(a, b int) bool { return a < b }})
    sorter.Sort(data)
    fmt.Println(data)

    // Plugin pattern
    svc := NewNotificationService()
    svc.Register(&EmailChannel{smtpAddr: "smtp.example.com"})
    svc.Register(&SlackChannel{webhookURL: "https://hooks.slack.com/..."})
    svc.Register(&SMSChannel{apiKey: "key_123"})

    svc.Notify("email", "user@example.com", "Welcome!", "Hello!")
    svc.BroadcastAll("admin@example.com", "Alert!", "System is down")
}
```

---

## 14. Real-World Pattern: Functional Options

Functional options use interfaces and closures to provide flexible, extensible configuration — a pattern pioneered by Dave Cheney and Rob Pike.

```go
package server

import (
    "crypto/tls"
    "net/http"
    "time"
)

// --- The server ---
type Server struct {
    host         string
    port         int
    readTimeout  time.Duration
    writeTimeout time.Duration
    maxConns     int
    tlsConfig    *tls.Config
    middleware   []func(http.Handler) http.Handler
}

// Option is a function that configures a Server
type Option func(*Server)

// --- Functional options ---
func WithHost(host string) Option {
    return func(s *Server) { s.host = host }
}

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(read, write time.Duration) Option {
    return func(s *Server) {
        s.readTimeout = read
        s.writeTimeout = write
    }
}

func WithMaxConns(n int) Option {
    return func(s *Server) { s.maxConns = n }
}

func WithTLS(certFile, keyFile string) Option {
    return func(s *Server) {
        cert, err := tls.LoadX509KeyPair(certFile, keyFile)
        if err != nil {
            panic(err) // or use error-returning option pattern
        }
        s.tlsConfig = &tls.Config{Certificates: []tls.Certificate{cert}}
    }
}

func WithMiddleware(m ...func(http.Handler) http.Handler) Option {
    return func(s *Server) {
        s.middleware = append(s.middleware, m...)
    }
}

// --- Constructor with sane defaults ---
func NewServer(opts ...Option) *Server {
    s := &Server{
        host:         "0.0.0.0",
        port:         8080,
        readTimeout:  5 * time.Second,
        writeTimeout: 10 * time.Second,
        maxConns:     1000,
    }
    for _, opt := range opts {
        opt(s) // apply each option
    }
    return s
}

// --- Usage ---
func main() {
    // Minimal
    s1 := NewServer()

    // Custom
    s2 := NewServer(
        WithHost("localhost"),
        WithPort(9090),
        WithTimeout(3*time.Second, 15*time.Second),
        WithMaxConns(5000),
    )

    _ = s1
    _ = s2
}
```

**Why this is powerful:** Adding a new configuration field never breaks existing call sites. Compare to a 10-argument constructor — unreadable, fragile.

---

## 15. Real-World Pattern: Error Handling via Interfaces

The `error` interface is the simplest interface in Go:

```go
type error interface {
    Error() string
}
```

But you can build rich error hierarchies on top of it.

```go
package errors

import (
    "fmt"
    "net/http"
)

// --- Typed errors with behavior ---

type AppError struct {
    Code    int
    Message string
    Err     error // wrapped cause
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error { return e.Err } // enables errors.Is/As

func (e *AppError) HTTPStatus() int {
    switch e.Code {
    case 404:
        return http.StatusNotFound
    case 401:
        return http.StatusUnauthorized
    case 400:
        return http.StatusBadRequest
    default:
        return http.StatusInternalServerError
    }
}

// --- Interface for HTTP-aware errors ---
type HTTPError interface {
    error
    HTTPStatus() int
}

// --- Sentinel-style constructors ---
func NotFound(msg string) *AppError {
    return &AppError{Code: 404, Message: msg}
}

func Unauthorized(msg string) *AppError {
    return &AppError{Code: 401, Message: msg}
}

func Wrap(err error, msg string) *AppError {
    return &AppError{Code: 500, Message: msg, Err: err}
}

// --- HTTP handler that understands typed errors ---
func JSONError(w http.ResponseWriter, err error) {
    var httpErr HTTPError
    if errors.As(err, &httpErr) {
        http.Error(w, httpErr.Error(), httpErr.HTTPStatus())
        return
    }
    http.Error(w, "internal server error", http.StatusInternalServerError)
}

// --- Retryable error interface ---
type RetryableError interface {
    error
    RetryAfter() time.Duration
}

type RateLimitError struct {
    retryAfter time.Duration
}

func (r *RateLimitError) Error() string {
    return fmt.Sprintf("rate limited, retry after %v", r.retryAfter)
}

func (r *RateLimitError) RetryAfter() time.Duration { return r.retryAfter }

// Retry loop using the interface
func WithRetry(ctx context.Context, fn func() error) error {
    for {
        err := fn()
        if err == nil {
            return nil
        }

        var retryable RetryableError
        if !errors.As(err, &retryable) {
            return err // non-retryable, give up
        }

        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(retryable.RetryAfter()):
            // retry
        }
    }
}
```

---

## 16. Real-World Pattern: The Observer/Event System

```go
package events

import (
    "context"
    "sync"
)

// --- Event types ---
type EventType string

const (
    EventUserCreated EventType = "user.created"
    EventUserDeleted EventType = "user.deleted"
    EventOrderPlaced EventType = "order.placed"
)

type Event struct {
    Type    EventType
    Payload any
    // In production: add TraceID, Timestamp, Source, etc.
}

// --- Handler interface ---
type Handler interface {
    Handle(ctx context.Context, event Event) error
    Supports(eventType EventType) bool
}

// --- Event bus ---
type Bus struct {
    mu       sync.RWMutex
    handlers []Handler
}

func NewBus() *Bus {
    return &Bus{}
}

func (b *Bus) Subscribe(h Handler) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.handlers = append(b.handlers, h)
}

func (b *Bus) Publish(ctx context.Context, event Event) []error {
    b.mu.RLock()
    handlers := make([]Handler, len(b.handlers))
    copy(handlers, b.handlers)
    b.mu.RUnlock()

    var errs []error
    for _, h := range handlers {
        if h.Supports(event.Type) {
            if err := h.Handle(ctx, event); err != nil {
                errs = append(errs, err)
            }
        }
    }
    return errs
}

// Async variant
func (b *Bus) PublishAsync(ctx context.Context, event Event) <-chan error {
    errCh := make(chan error, len(b.handlers))
    go func() {
        defer close(errCh)
        for _, err := range b.Publish(ctx, event) {
            errCh <- err
        }
    }()
    return errCh
}

// --- Concrete handlers ---
type WelcomeEmailHandler struct {
    // emailSvc EmailService
}

func (h *WelcomeEmailHandler) Supports(t EventType) bool {
    return t == EventUserCreated
}

func (h *WelcomeEmailHandler) Handle(ctx context.Context, e Event) error {
    // user := e.Payload.(User)
    // return h.emailSvc.SendWelcome(ctx, user.Email)
    fmt.Printf("Sending welcome email for event: %s\n", e.Type)
    return nil
}

type AuditLogHandler struct{}

func (h *AuditLogHandler) Supports(_ EventType) bool { return true } // handles all

func (h *AuditLogHandler) Handle(ctx context.Context, e Event) error {
    fmt.Printf("[AUDIT] event=%s payload=%+v\n", e.Type, e.Payload)
    return nil
}

// --- FuncHandler: adapt a function to Handler interface ---
type FuncHandler struct {
    eventType EventType
    fn        func(ctx context.Context, event Event) error
}

func On(eventType EventType, fn func(ctx context.Context, event Event) error) Handler {
    return &FuncHandler{eventType: eventType, fn: fn}
}

func (f *FuncHandler) Supports(t EventType) bool { return t == f.eventType }
func (f *FuncHandler) Handle(ctx context.Context, e Event) error { return f.fn(ctx, e) }

func main() {
    bus := NewBus()
    bus.Subscribe(&WelcomeEmailHandler{})
    bus.Subscribe(&AuditLogHandler{})
    bus.Subscribe(On(EventOrderPlaced, func(ctx context.Context, e Event) error {
        fmt.Printf("Processing order: %+v\n", e.Payload)
        return nil
    }))

    bus.Publish(context.Background(), Event{Type: EventUserCreated, Payload: "user_123"})
    bus.Publish(context.Background(), Event{Type: EventOrderPlaced, Payload: "order_456"})
}
```

---

## 17. Real-World Pattern: Pipeline Architecture

```go
package pipeline

import (
    "context"
    "fmt"
)

// Stage is a unit of work in a pipeline
type Stage[I, O any] interface {
    Process(ctx context.Context, input I) (O, error)
    Name() string
}

// --- Generic pipeline ---
// Note: Go doesn't allow methods with different type params,
// so we use functions for composition

func RunStage[I, O any](ctx context.Context, stage Stage[I, O], input I) (O, error) {
    out, err := stage.Process(ctx, input)
    if err != nil {
        var zero O
        return zero, fmt.Errorf("stage %s: %w", stage.Name(), err)
    }
    return out, nil
}

// --- Concrete pipeline for document processing ---

type Document struct {
    ID      string
    Content string
    Tags    []string
    Score   float64
}

// ValidateStage
type ValidateStage struct{}

func (v *ValidateStage) Name() string { return "validate" }
func (v *ValidateStage) Process(ctx context.Context, doc Document) (Document, error) {
    if doc.ID == "" {
        return Document{}, fmt.Errorf("document ID is required")
    }
    if len(doc.Content) == 0 {
        return Document{}, fmt.Errorf("document content is empty")
    }
    return doc, nil
}

// EnrichStage
type EnrichStage struct {
    tagExtractor func(content string) []string
}

func (e *EnrichStage) Name() string { return "enrich" }
func (e *EnrichStage) Process(ctx context.Context, doc Document) (Document, error) {
    doc.Tags = e.tagExtractor(doc.Content)
    return doc, nil
}

// ScoreStage
type ScoreStage struct {
    scorer func(doc Document) float64
}

func (s *ScoreStage) Name() string { return "score" }
func (s *ScoreStage) Process(ctx context.Context, doc Document) (Document, error) {
    doc.Score = s.scorer(doc)
    return doc, nil
}

// DocumentPipeline chains stages
type DocumentPipeline struct {
    stages []Stage[Document, Document]
}

func (p *DocumentPipeline) AddStage(s Stage[Document, Document]) {
    p.stages = append(p.stages, s)
}

func (p *DocumentPipeline) Run(ctx context.Context, doc Document) (Document, error) {
    current := doc
    for _, stage := range p.stages {
        var err error
        current, err = stage.Process(ctx, current)
        if err != nil {
            return Document{}, fmt.Errorf("pipeline failed at %s: %w", stage.Name(), err)
        }
    }
    return current, nil
}

// Channel-based concurrent pipeline
func GeneratorStage(ctx context.Context, docs []Document) <-chan Document {
    out := make(chan Document)
    go func() {
        defer close(out)
        for _, doc := range docs {
            select {
            case <-ctx.Done():
                return
            case out <- doc:
            }
        }
    }()
    return out
}

func TransformStage(ctx context.Context, in <-chan Document, stage Stage[Document, Document]) <-chan Document {
    out := make(chan Document)
    go func() {
        defer close(out)
        for doc := range in {
            result, err := stage.Process(ctx, doc)
            if err != nil {
                fmt.Printf("error in stage %s: %v\n", stage.Name(), err)
                continue
            }
            select {
            case <-ctx.Done():
                return
            case out <- result:
            }
        }
    }()
    return out
}

func main() {
    ctx := context.Background()

    validate := &ValidateStage{}
    enrich := &EnrichStage{
        tagExtractor: func(content string) []string {
            return []string{"auto-tagged"}
        },
    }
    score := &ScoreStage{
        scorer: func(doc Document) float64 {
            return float64(len(doc.Tags)) * 0.5
        },
    }

    // Sequential pipeline
    pipeline := &DocumentPipeline{}
    pipeline.AddStage(validate)
    pipeline.AddStage(enrich)
    pipeline.AddStage(score)

    doc := Document{ID: "doc_1", Content: "Go interfaces are powerful"}
    result, err := pipeline.Run(ctx, doc)
    if err != nil {
        fmt.Println("Error:", err)
        return
    }
    fmt.Printf("Result: %+v\n", result)

    // Concurrent channel pipeline
    docs := []Document{
        {ID: "1", Content: "first doc"},
        {ID: "2", Content: "second doc"},
        {ID: "3", Content: "third doc"},
    }

    gen := GeneratorStage(ctx, docs)
    validated := TransformStage(ctx, gen, validate)
    enriched := TransformStage(ctx, validated, enrich)
    scored := TransformStage(ctx, enriched, score)

    for doc := range scored {
        fmt.Printf("Processed: %s score=%.2f tags=%v\n", doc.ID, doc.Score, doc.Tags)
    }
}
```

---

## 18. Interface Performance and Escape Analysis

```go
package main

// Key performance facts about interfaces:
//
// 1. Interface calls cost ~1 indirect function call vs direct call
// 2. Storing a value in an interface may cause heap allocation (escape)
// 3. Small scalars (≤ pointer size) MAY be stored inline — no alloc
// 4. itab lookup is O(1) per (interface, type) pair — cached globally

// Run: go build -gcflags='-m -m' ./... to see escape decisions

// --- Demonstrating escape ---

type Adder interface {
    Add(a, b int) int
}

type FastAdder struct{}

func (f FastAdder) Add(a, b int) int { return a + b }

// This version may cause FastAdder to escape to heap
func useInterface(a Adder) int {
    return a.Add(1, 2)
}

// This version: FastAdder stays on stack (inlined)
func useConcrete(f FastAdder) int {
    return f.Add(1, 2)
}

// --- Avoid allocation hot paths ---

// BAD: allocates on every call if msg escapes
func LogBad(level string, msg interface{}) {
    // ... logger
}

// GOOD: use concrete types in hot paths
func LogGood(level string, msg string) {
    // ... logger
}

// --- Interface in a tight loop: benchmark first ---
// go test -bench=. -benchmem

// BenchmarkInterface: ~2.5ns/op + possible allocation
// BenchmarkConcrete: ~0.5ns/op, 0 allocs

// Rule: Interfaces in hot loops (>10M/s) need profiling.
// Outside hot loops, interface overhead is negligible.
```

### Escape Analysis Commands

```bash
# See what escapes to heap
go build -gcflags='-m' ./...

# More verbose — shows WHY it escapes
go build -gcflags='-m -m' ./...

# Benchmark with memory stats
go test -bench=BenchmarkName -benchmem ./...

# CPU profile
go test -bench=. -cpuprofile=cpu.prof ./...
go tool pprof cpu.prof
```

---

## 19. Generics vs Interfaces: When to Use Which

Go 1.18 introduced generics. Knowing when to use each is a mark of expertise.

```go
// --- Use INTERFACES when: ---
// 1. Runtime polymorphism (type known at runtime)
// 2. Different concrete types stored in same collection
// 3. Behavior-based abstraction (strategy, plugin patterns)
// 4. Public APIs (interfaces are more stable than type constraints)

// Example: different animals in one slice
animals := []Animal{Dog{}, Cat{}, Bird{}}
for _, a := range animals {
    fmt.Println(a.Sound()) // dispatch at runtime
}

// --- Use GENERICS when: ---
// 1. Algorithm works the same for multiple types
// 2. Compile-time type safety needed (no type assertions)
// 3. Zero-cost abstraction (no interface overhead)
// 4. Working with containers (stacks, queues, sets)

// Generic stack — compile-time safe, no boxing
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
    if len(s.items) == 0 {
        var zero T
        return zero, false
    }
    top := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return top, true
}

// Generic map — type-safe, no interface{}
func Map[T, U any](slice []T, fn func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

// Type constraints — interface used as constraint
type Number interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~float32 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

// --- The hybrid: interface + generics ---
type Repository[T any] interface {
    FindByID(ctx context.Context, id string) (T, error)
    Save(ctx context.Context, entity T) error
    Delete(ctx context.Context, id string) error
}

// Concrete implementation
type UserRepo struct{ db *sql.DB }

func (r *UserRepo) FindByID(ctx context.Context, id string) (User, error) {
    // ...
}
```

**Decision table:**

| Situation | Use |
|-----------|-----|
| Same algorithm, multiple types, no runtime switching | Generics |
| Different types stored together at runtime | Interface |
| Public API boundary | Interface |
| Internal high-performance algorithm | Generics |
| Mocking/testing seam | Interface |
| Type-safe container (Stack, Queue, Set) | Generics |

---

## 20. Anti-Patterns and Common Mistakes

### Anti-Pattern 1: Defining Interface Before the Implementation

```go
// ❌ BAD: You define the interface speculatively
// before knowing what the consumer needs
type UserServiceInterface interface {
    // 20 methods here...
}

// ✅ GOOD: Define the interface at the point of use
// when you know exactly which methods you need
// (Go proverb: "Accept interfaces, return structs")
func NewController(svc UserFinder) *Controller { ... }
```

### Anti-Pattern 2: Returning Interfaces Instead of Structs

```go
// ❌ BAD: Hides the return type, prevents callers from accessing extra methods
func NewRedisStore() Store {
    return &RedisStore{}
}

// ✅ GOOD: Return concrete type; callers can use it as an interface if needed
func NewRedisStore() *RedisStore {
    return &RedisStore{}
}

// Callers can still use it where Store is expected:
var s Store = NewRedisStore() // works fine
```

### Anti-Pattern 3: Fat Interfaces

Already covered in §9 — segregate your interfaces.

### Anti-Pattern 4: Interface for a Single Implementation

```go
// ❌ BAD: Interface with only one real implementation
// This adds indirection with no benefit
type Logger interface {
    Log(msg string)
}

// ✅ Better: use concrete type; refactor to interface IF a second
// implementation (or test double) is needed later
type Logger struct {
    out io.Writer
}
```

### Anti-Pattern 5: Ignoring the Nil Interface Trap

Covered in §8 — never return a typed nil as an interface.

### Anti-Pattern 6: Overusing `any`/`interface{}`

```go
// ❌ BAD: loses type safety
func Add(a, b any) any {
    return a.(int) + b.(int) // runtime panic if wrong type
}

// ✅ GOOD with generics
func Add[T Number](a, b T) T {
    return a + b
}
```

### Anti-Pattern 7: Copying a Mutex Through an Interface

```go
type Locker interface {
    Lock()
    Unlock()
}

type SafeCounter struct {
    mu sync.Mutex
    n  int
}

func (c *SafeCounter) Lock()   { c.mu.Lock() }
func (c *SafeCounter) Unlock() { c.mu.Unlock() }

// BAD: if you ever copy SafeCounter (e.g., by value assignment),
// the mutex is copied in a locked/unlocked state — data race.
// Always use *SafeCounter, never SafeCounter, for types with mutexes.
```

---

## 21. Expert Intuition: Design Heuristics

These are the mental models that separate good Go programmers from great ones.

### Heuristic 1: "Accept Interfaces, Return Structs"

This is the single most important Go interface maxim. It comes from Rob Pike.

- **Accept interfaces** → your function is flexible, testable, composable
- **Return structs** → your callers get the full concrete power; they can use it as any interface

### Heuristic 2: The "One Method Interface" Rule

The most reusable interfaces in Go have exactly one method:
- `io.Reader`, `io.Writer`, `io.Closer`
- `http.Handler`
- `fmt.Stringer`
- `error`
- `sort.Interface` (technically 3, but it's one logical operation)

When designing, ask: *"Can I split this into single-method interfaces that compose?"*

### Heuristic 3: Define Interfaces Near Their Consumers

Don't put interfaces in the same package as the implementation. Put them in the package that *uses* them. This prevents circular dependencies and keeps packages focused.

```
// Package layout:
// storage/redis/redis.go     — concrete RedisStore
// api/handler.go             — defines: type Store interface {...}
// api/handler_test.go        — uses MemStore as test double
```

### Heuristic 4: The "Mock-ability Test"

Before finalizing your function signature, ask: *"Can I write a unit test for this without a real database/network/filesystem?"* If the answer is no, you need an interface at that boundary.

### Heuristic 5: Structural vs Behavioral Thinking

When you catch yourself thinking "this type IS a Foo" (structural/OOP thinking), reframe it as "this type can DO what Foo requires" (behavioral thinking). Go interfaces are about **capability**, not **identity**.

### Heuristic 6: Small Interfaces Enable Composition

```go
// You can always compose small interfaces at call sites
func ProcessAndStore(ctx context.Context, r io.Reader, w io.Writer) error {
    // reads from anywhere, writes to anywhere
    _, err := io.Copy(w, r)
    return err
}

// Caller: file → network
f, _ := os.Open("data.json")
conn, _ := net.Dial("tcp", "server:9000")
ProcessAndStore(ctx, f, conn)

// Caller: HTTP body → buffer (for testing)
buf := &bytes.Buffer{}
ProcessAndStore(ctx, req.Body, buf)
```

### Heuristic 7: Cognitive Chunking for Interface Design

When you encounter a complex system, chunk the behavior into roles:
- **Produces data** → implement `io.Reader` or custom Producer interface
- **Consumes data** → implement `io.Writer` or custom Consumer interface
- **Transforms data** → implement a Transformer interface
- **Stores data** → implement a Repository interface
- **Sends notifications** → implement a Notifier interface

These chunks are universal across most systems.

---

## Summary: The Interface Mastery Checklist

```
STRUCTURAL
  □ Know the two runtime structs: iface and eface
  □ Understand method dispatch cost (one indirect call)
  □ Know when values escape to heap via interface boxing

CORRECTNESS
  □ Never return a typed nil as an interface
  □ Use pointer receivers consistently on a type
  □ Use two-value type assertions in production code
  □ Verify satisfaction with blank identifier assignments

DESIGN
  □ Accept interfaces, return structs
  □ Define interfaces at the consumer, not the producer
  □ Prefer small (1-3 method) interfaces
  □ Compose small interfaces into larger ones as needed
  □ Use interfaces for test seams (DI pattern)

ADVANCED
  □ Distinguish generics vs interfaces by use case
  □ Use type constraints (interfaces) with generics
  □ Design plugin systems with interface registries
  □ Build middleware chains with handler interfaces
  □ Model errors with behavioral interfaces (RetryableError, HTTPError)

PERFORMANCE
  □ Avoid interface boxing in tight loops (>10M calls/s)
  □ Use go build -gcflags='-m' to verify escape decisions
  □ Prefer concrete types in internal hot paths
```

---

*"The master programmer does not write code that is merely correct. They write code that reveals the structure of the problem so clearly that correctness becomes obvious."*

2,154 lines. Here is what the guide covers, structured like a master-class progression:

**Foundations (§1–5)** — The mental model shift from OOP to structural typing, the two runtime structs (`iface`/`eface`), method dispatch mechanics, type assertions, and type switches. You understand *why* Go interfaces work, not just *how*.

**Mechanics (§6–8)** — Interface composition (the `io` family as the gold standard), the pointer/value receiver method set rules (with the definitive lookup table), and the nil interface vs nil pointer trap — the most common production bug, fully dissected.

**Real-World Patterns (§11–17)** — Seven production-grade patterns with full implementations:
- `io.Reader/Writer` pipeline with custom `FibReader` and `countingWriter`
- HTTP middleware chain with logging, auth, rate limiting, and recovery
- Plugin/strategy with a notification registry and generic sorter
- Functional options (the Dave Cheney pattern)
- Behavioral error typing (`RetryableError`, `HTTPError`, `errors.As`)
- Observer/event bus with `FuncHandler` adapter
- Both sequential and concurrent channel-based pipelines

**Expert Judgment (§18–21)** — Escape analysis and when interface overhead actually matters, the generics vs interfaces decision table, all seven major anti-patterns with corrections, and the seven design heuristics that separate senior from principal engineers.

The master checklist at the end is your recurring audit tool — run it against every package you write.