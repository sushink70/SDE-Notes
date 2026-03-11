# Methods vs Functions in Go — A Complete Deep Dive

---

## 1. The Fundamental Distinction

At the conceptual level, the difference is philosophical before it is syntactic.

A **function** is a standalone computation unit. It belongs to a package. It takes inputs, produces outputs, and has no inherent association with any data structure. It is a pure transformation in the mathematical sense.

A **method** is a function with a *receiver* — a designated value that the function operates *on behalf of*. It belongs to a type. It expresses the idea: "this behavior is intrinsically owned by this type."

This is not just syntactic sugar. It is a design decision about **where behavior lives** in your program's conceptual model.

```go
// Function — belongs to no type, lives in package scope
func Add(a, b int) int {
    return a + b
}

// Method — belongs to type Rectangle, receiver is the "subject"
type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}
```

The key insight: when you write `rect.Area()`, you are not just calling a function — you are *sending a message to a value*, asking it to compute something about itself. This is the object-oriented instinct expressed in Go's minimalist style.

---

## 2. Anatomy of a Method Declaration

```
func (receiver ReceiverType) MethodName(params) returnType {
    body
}
```

Every component matters:

| Component | Role |
|---|---|
| `receiver` | Local name for the value the method operates on |
| `ReceiverType` | The type this method is attached to |
| `MethodName` | The identifier callable via dot notation |
| `params` | Additional inputs beyond the receiver |
| `returnType` | Output type(s) |

**Convention**: receiver name should be a short, consistent abbreviation of the type — typically one or two letters. `r` for `Rectangle`, `s` for `Server`, `c` for `Client`. Never use `self` or `this` — that is non-idiomatic Go and signals that you're thinking in another language.

```go
// Idiomatic
func (r Rectangle) Perimeter() float64 {
    return 2 * (r.Width + r.Height)
}

// Non-idiomatic (don't do this)
func (self Rectangle) Perimeter() float64 {
    return 2 * (self.Width + self.Height)
}
```

---

## 3. Value Receivers vs Pointer Receivers — The Core Decision

This is the most important decision when writing methods in Go. It is not merely a performance concern — it is a **semantic contract**.

### 3.1 Value Receiver

```go
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}
```

When you call `rect.Area()`, Go **copies** the entire `Rectangle` value onto the stack. The method receives its own independent copy. Any modification inside the method is invisible to the caller.

**What this communicates**: "This method only *reads* the receiver. It does not change it. The receiver's state after this call is identical to before."

### 3.2 Pointer Receiver

```go
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}
```

When you call `rect.Scale(2)`, Go passes the **memory address** of `rect`. The method operates on the original value. Modifications are visible to the caller.

**What this communicates**: "This method *mutates* the receiver. The receiver's state will change."

### 3.3 The Decision Framework

Ask these questions in order:

**1. Does the method need to mutate the receiver?**
→ Yes: use pointer receiver. Full stop.

**2. Is the receiver a large struct (memory concern)?**
→ Yes: use pointer receiver to avoid expensive copies.

**3. Is the type inherently non-copyable? (e.g., contains a mutex, a file handle)**
→ Yes: use pointer receiver. Copying a `sync.Mutex` breaks its semantics entirely.

**4. Is the type a small, naturally immutable value type?**
→ Use value receiver. `time.Time`, basic geometry types, etc.

**5. Consistency rule**: If *any* method on the type uses a pointer receiver, consider making *all* methods use pointer receivers. Mixed sets cause subtle bugs with interfaces.

```go
// ✅ Consistent — all pointer receivers
type Counter struct{ n int }
func (c *Counter) Increment() { c.n++ }
func (c *Counter) Reset()     { c.n = 0 }
func (c *Counter) Value() int { return c.n }

// ⚠️ Inconsistent — mixed receivers, potential interface issues
type Counter struct{ n int }
func (c *Counter) Increment() { c.n++ }
func (c Counter) Value() int  { return c.n }  // this works, but is confusing
```

### 3.4 Automatic Address-Taking and Dereferencing

Go is intelligent about receiver types. It will automatically take the address or dereference for you under most conditions:

```go
rect := Rectangle{Width: 10, Height: 5}

// rect is addressable, so Go auto-takes address for pointer receiver
rect.Scale(2)          // equivalent to (&rect).Scale(2)

// Go auto-dereferences for value receiver
rp := &rect
area := rp.Area()      // equivalent to (*rp).Area()
```

**Critical caveat**: This automatic promotion only works for **addressable** values. A non-addressable value (like a map element, a function return value used directly, a temporary) cannot have its address taken:

```go
// This will NOT compile
rectangles := map[string]Rectangle{"r": {10, 5}}
rectangles["r"].Scale(2) // Error: cannot take the address of map element
```

This is a subtle trap. Map values are not addressable because the map may internally relocate memory during resizing. The solution is to copy out, modify, reassign:

```go
r := rectangles["r"]
r.Scale(2)
rectangles["r"] = r
```

---

## 4. Methods on Non-Struct Types

Go is more general than most people realize. You can define methods on **any named type** in the same package — not just structs.

```go
// Method on a named integer type
type Celsius float64
type Fahrenheit float64

func (c Celsius) ToFahrenheit() Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}

func (f Fahrenheit) ToCelsius() Celsius {
    return Celsius((f - 32) * 5 / 9)
}

// Usage
boiling := Celsius(100)
fmt.Println(boiling.ToFahrenheit()) // 212
```

```go
// Method on a named slice type
type IntSlice []int

func (s IntSlice) Sum() int {
    total := 0
    for _, v := range s {
        total += v
    }
    return total
}

func (s IntSlice) Filter(pred func(int) bool) IntSlice {
    result := make(IntSlice, 0, len(s))
    for _, v := range s {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}
```

```go
// Method on a named function type — powerful pattern
type Handler func(request string) string

func (h Handler) WithLogging() Handler {
    return func(req string) string {
        fmt.Printf("Handling: %s\n", req)
        result := h(req)
        fmt.Printf("Result: %s\n", result)
        return result
    }
}
```

**What you cannot do**: You cannot define methods on types from another package. `func (t time.Time) ...` is illegal — you must create a named wrapper type.

---

## 5. Method Sets — The Rules That Govern Everything

The **method set** of a type is the complete collection of methods callable on values of that type. This concept is the backbone of interface satisfaction in Go.

| Type | Method Set |
|---|---|
| `T` | All methods with value receiver `(t T)` |
| `*T` | All methods with value receiver `(t T)` **+** all methods with pointer receiver `(t *T)` |

This asymmetry is fundamental and intentional:

- A `*T` can always act as a `T` (dereference to get the value)
- A `T` cannot always act as a `*T` (you can only take the address of an addressable value)

```go
type Stringer interface {
    String() string
}

type Point struct{ X, Y float64 }

func (p Point) String() string {
    return fmt.Sprintf("(%.2f, %.2f)", p.X, p.Y)
}

var s Stringer

p := Point{1, 2}
s = p   // ✅ Point implements Stringer (value receiver method)
s = &p  // ✅ *Point also implements Stringer (inherits value methods)
```

Now flip it:

```go
func (p *Point) Scale(f float64) {
    p.X *= f
    p.Y *= f
}

type Scaler interface {
    Scale(float64)
}

p := Point{1, 2}
s = &p  // ✅ *Point implements Scaler
s = p   // ❌ Point does NOT implement Scaler
        // Cannot take address of interface value
```

**The expert mental model**: A pointer is strictly more capable than the value itself. `*T`'s method set is a superset of `T`'s method set. When designing interfaces, if you expect mutation, the implementor must use `*T`.

---

## 6. Promoted Methods — Embedding and Composition

Go's embedding mechanism promotes methods from embedded types to the outer type. This is Go's answer to inheritance — not true inheritance, but **delegation by composition**.

```go
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " makes a sound"
}

type Dog struct {
    Animal          // embedded — no field name
    Breed string
}

func (d Dog) Speak() string {  // Dog overrides Animal's Speak
    return d.Name + " barks"
}

d := Dog{Animal: Animal{Name: "Rex"}, Breed: "Husky"}
d.Speak()        // "Rex barks" — Dog's own method
d.Animal.Speak() // "Rex makes a sound" — explicit disambiguation
```

When the embedded type has methods and the outer type doesn't override them, those methods are *promoted*:

```go
type Logger struct{}
func (l Logger) Log(msg string) { fmt.Println("[LOG]", msg) }

type Server struct {
    Logger          // promoted: Server gains Log method
    Addr string
}

s := Server{Addr: ":8080"}
s.Log("Server started") // calls Logger.Log through promotion
```

**Embedding with pointer receivers** — important nuance:

```go
type Engine struct{ running bool }
func (e *Engine) Start() { e.running = true }

type Car struct {
    *Engine  // pointer embedding
    Model string
}

c := Car{Engine: &Engine{}, Model: "Tesla"}
c.Start() // Works — c.Engine.Start() — modifies the shared Engine
```

Embedding a pointer means multiple `Car` values could share the same `Engine`. Embedding a value means each `Car` has its own `Engine`. Both are legitimate designs with different semantics.

---

## 7. Methods as First-Class Values

In Go, methods can be extracted as function values in two ways: **method values** and **method expressions**.

### 7.1 Method Values (bound)

```go
type Counter struct{ n int }
func (c *Counter) Increment() { c.n++ }

c := Counter{}
inc := c.Increment  // method value — binds c as receiver
inc()               // equivalent to c.Increment()
inc()
fmt.Println(c.n)    // 2
```

The method value `inc` *closes over* `c`. It remembers which instance to operate on. This is how you pass methods as callbacks.

```go
type Timer struct{}
func (t *Timer) Tick() { fmt.Println("tick") }

timer := &Timer{}
go timer.Tick() // method value passed to goroutine implicitly
```

### 7.2 Method Expressions (unbound)

```go
// Method expression — takes receiver as explicit first argument
incExpr := (*Counter).Increment  // type: func(*Counter)

c := &Counter{}
incExpr(c)  // equivalent to c.Increment()
incExpr(c)
fmt.Println(c.n) // 2
```

Method expressions are powerful when you need to treat methods as generic functions:

```go
type Rectangle struct{ W, H float64 }
func (r Rectangle) Area() float64   { return r.W * r.H }
func (r Rectangle) Perim() float64  { return 2 * (r.W + r.H) }

// Store methods as values in a map
ops := map[string]func(Rectangle) float64{
    "area":  Rectangle.Area,
    "perim": Rectangle.Perim,
}

r := Rectangle{3, 4}
for name, op := range ops {
    fmt.Printf("%s: %.2f\n", name, op(r))
}
```

---

## 8. Interface Satisfaction — Where Methods Become Architecture

Interfaces in Go are **implicitly satisfied** by method sets. There is no `implements` keyword. A type satisfies an interface if and only if its method set is a superset of the interface's method set.

```go
type Shape interface {
    Area() float64
    Perimeter() float64
}

type Circle struct{ Radius float64 }
func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }

// Circle implicitly satisfies Shape — no declaration needed
var s Shape = Circle{Radius: 5}
```

**The design principle**: Define interfaces where they are *used*, not where types are *defined*. This is the inverse of Java/C#. Your types don't need to know about the interfaces they satisfy. This decouples packages cleanly.

```go
// package storage
type Storer interface {
    Save(data []byte) error
    Load(key string) ([]byte, error)
}

// package database — knows nothing about storage.Storer
type PostgresDB struct{ /* ... */ }
func (db *PostgresDB) Save(data []byte) error          { /* ... */ return nil }
func (db *PostgresDB) Load(key string) ([]byte, error) { /* ... */ return nil, nil }

// package main — wires them together
var store storage.Storer = &database.PostgresDB{}
```

---

## 9. The `init` Function and Package-Level Functions

Some special functions in Go are not methods and cannot be:

- `main()` — program entry point
- `init()` — package initialization, called automatically before `main`
- Functions named with `Test`, `Benchmark`, `Example` prefix — testing framework hooks

These are package-level functions with special runtime significance. They cannot have receivers.

---

## 10. Functions vs Methods — When to Choose Which

This is the design judgment that separates beginner Go from expert Go.

**Use a function when:**

- The operation is not conceptually tied to a specific type
- You are transforming inputs to outputs without a "primary subject"
- You are writing utility logic that operates on multiple unrelated types
- You are writing pure computations (mathematical operations, string manipulation)

```go
// Function — no primary "owner", operates on two independent values
func Min(a, b int) int {
    if a < b {
        return a
    }
    return b
}

// Function — utility operating on standard type, not your type
func ParseDate(s string) (time.Time, error) { /* ... */ }
```

**Use a method when:**

- The operation belongs to a specific type semantically
- The behavior depends on or modifies the type's state
- You want the type to satisfy an interface
- The operation is a natural capability of the type ("a Stack can Push")

```go
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T)      { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) { /* ... */ }
func (s *Stack[T]) Len() int       { return len(s.items) }
```

**The smell test**: If you find yourself writing `DoSomethingToFoo(foo Foo, ...)`, ask whether this should be `foo.DoSomething(...)`. If the answer is yes, it should be a method.

---

## 11. Nil Receivers — A Surprisingly Powerful Pattern

Go allows methods to be called on nil pointer receivers. This is not a bug — it is a deliberate feature used in production code.

```go
type Node struct {
    Value int
    Left  *Node
    Right *Node
}

// Safe even when n is nil — no nil check needed at call site
func (n *Node) Sum() int {
    if n == nil {
        return 0
    }
    return n.Value + n.Left.Sum() + n.Right.Sum()
}

// Usage — clean, no nil checks needed
var root *Node // nil
fmt.Println(root.Sum()) // 0 — works perfectly
```

This pattern is used extensively in the standard library. `(*bytes.Buffer).Write` handles a nil buffer gracefully, for instance.

```go
type LinkedList struct {
    head *Node
}

func (l *LinkedList) IsEmpty() bool {
    return l == nil || l.head == nil
}
```

**Caution**: Only use this if it semantically makes sense. Don't use nil receivers to avoid proper initialization — use it when nil has a natural "zero" or "empty" meaning for the type.

---

## 12. Method Chaining — Fluent Interfaces

Methods that return the receiver (or a modified copy) enable chaining — a powerful pattern for builder APIs and configuration.

```go
// Mutable chaining (pointer receivers, modifies in place)
type QueryBuilder struct {
    table  string
    wheres []string
    limit  int
}

func (q *QueryBuilder) From(table string) *QueryBuilder {
    q.table = table
    return q
}

func (q *QueryBuilder) Where(condition string) *QueryBuilder {
    q.wheres = append(q.wheres, condition)
    return q
}

func (q *QueryBuilder) Limit(n int) *QueryBuilder {
    q.limit = n
    return q
}

func (q *QueryBuilder) Build() string {
    query := "SELECT * FROM " + q.table
    if len(q.wheres) > 0 {
        query += " WHERE " + strings.Join(q.wheres, " AND ")
    }
    if q.limit > 0 {
        query += fmt.Sprintf(" LIMIT %d", q.limit)
    }
    return query
}

// Clean, readable call site
q := (&QueryBuilder{}).
    From("users").
    Where("age > 18").
    Where("active = true").
    Limit(100).
    Build()
```

```go
// Immutable chaining (value receivers, returns new copies)
type Vector struct{ X, Y float64 }

func (v Vector) Add(other Vector) Vector {
    return Vector{v.X + other.X, v.Y + other.Y}
}

func (v Vector) Scale(f float64) Vector {
    return Vector{v.X * f, v.Y * f}
}

result := Vector{1, 0}.Scale(5).Add(Vector{0, 3})
// Original vectors unchanged — functional style
```

---

## 13. Comparison with Functions — Performance Perspective

From a performance standpoint (relevant for competitive programming and systems work):

**Value receiver**: copies the entire struct. For large structs (hundreds of bytes), this is measurable overhead on hot paths. For small structs (≤ 3 or 4 words / 24-32 bytes on 64-bit), the copy is typically register-allocated and costs nothing.

**Pointer receiver**: passes 8 bytes (a pointer on 64-bit). But introduces indirection — the CPU must dereference the pointer to access fields. If the struct fits in cache, the extra indirection can be slower than copying.

**The nuanced truth**: Don't blindly use pointer receivers for "performance." For small, frequently-called methods on small types, value receivers can be *faster* due to better cache behavior and the elimination of pointer indirection. Profile before assuming.

In Rust terms: Go's value receiver is analogous to `self` (consuming or copying), pointer receiver is analogous to `&mut self`. Rust's borrow checker enforces the correctness of this automatically — in Go, you are responsible for the discipline.

---

## 14. Function Types as Method Receivers — The `http.HandlerFunc` Pattern

One of the most elegant patterns in the Go standard library:

```go
// From net/http
type HandlerFunc func(ResponseWriter, *Request)

// HandlerFunc satisfies the Handler interface
func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) {
    f(w, r)
}
```

This allows any function with the right signature to be treated as an `http.Handler` without defining a new struct type. The function *is* the struct. This is a profound unification of function-oriented and object-oriented thinking.

You can use this pattern in your own DSA code:

```go
type SortStrategy func([]int) []int

func (s SortStrategy) Apply(data []int) []int {
    result := make([]int, len(data))
    copy(result, data)
    return s(result)
}

func (s SortStrategy) ApplyAndPrint(data []int) {
    sorted := s.Apply(data)
    fmt.Println(sorted)
}

// Any sorting function becomes a SortStrategy
bubbleSort := SortStrategy(func(arr []int) []int {
    // ... bubble sort impl
    return arr
})

bubbleSort.ApplyAndPrint([]int{5, 3, 1, 4, 2})
```

---

## 15. The Complete Mental Model

```
Package
├── Functions (standalone computations)
│   ├── Pure utility: Min, Max, Parse, Format
│   ├── Constructors: NewServer, NewQueue (by convention)
│   └── Special: main, init, Test*
│
└── Types (named data + behavior)
    ├── Struct types
    ├── Named primitive types (type Celsius float64)
    ├── Named function types (type Handler func(...))
    └── Named collection types (type IntSlice []int)
        └── Methods (behavior belonging to the type)
            ├── Value receiver (read, compute, non-mutating)
            └── Pointer receiver (mutate, large struct, sync types)
```

**The deepest insight**: In Go, the distinction between methods and functions is not about what is *possible* (you can express anything as a function) — it is about what is *appropriate*. Methods encode the relationship between behavior and data into the type system itself. Functions encode reusable logic that transcends any single type. Mastering this distinction is what makes Go code feel idiomatic versus merely correct.

A world-class Go programmer reads a type's method set and immediately understands the type's **behavioral contract** — what it can do, what it guarantees, what it might change. The method set is the type's *public face to the world*, and every decision about value vs pointer receiver, what to expose vs hide, shapes that contract. That is the craft.