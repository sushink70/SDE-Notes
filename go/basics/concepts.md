# Go Mastery Map — Everything That Separates Novices From Experts

This is your complete curriculum. Each concept is ranked by how often it causes subtle, production-level bugs or architectural mistakes.

---

## The Mastery Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│                    GO MASTERY HIERARCHY                         │
│                                                                 │
│  TIER 1 — Subtle Traps    (burns everyone at least once)       │
│  TIER 2 — Deep Mechanics  (requires runtime/spec knowledge)    │
│  TIER 3 — Concurrency     (where most senior bugs live)        │
│  TIER 4 — Architecture    (separates good from great code)     │
│  TIER 5 — Runtime/Perf    (expert-level optimization)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## TIER 1 — Subtle Language Traps

These look simple but hide sharp edges.

---

### 1. `nil` Interface vs Typed `nil`
*(Already mastered — your foundation)*

---

### 2. Loop Variable Capture (The Closure Trap)

One of the most common Go bugs in history. Fixed in Go 1.22, but you **must** understand it for legacy code and for the underlying principle.

```go
package main

import "fmt"

func main() {
    // ─── THE BUG (Go < 1.22) ───────────────────────────────
    funcs := make([]func(), 5)
    for i := 0; i < 5; i++ {
        funcs[i] = func() {
            fmt.Println(i) // captures the VARIABLE i, not its value
        }
    }
    // All closures share the same 'i' variable
    // By the time they run, i = 5
    for _, f := range funcs {
        f() // prints: 5 5 5 5 5 — NOT 0 1 2 3 4
    }

    fmt.Println("---")

    // ─── THE FIX (pre-1.22) ────────────────────────────────
    funcs2 := make([]func(), 5)
    for i := 0; i < 5; i++ {
        i := i // shadow: creates a NEW variable per iteration
        funcs2[i] = func() {
            fmt.Println(i) // captures its own copy
        }
    }
    for _, f := range funcs2 {
        f() // prints: 0 1 2 3 4 ✅
    }

    fmt.Println("---")

    // ─── GOROUTINE VARIANT (still relevant in ALL versions) ──
    for i := 0; i < 3; i++ {
        go func() {
            fmt.Println(i) // likely prints 3 3 3
        }()
    }
}
```

**The deep principle:** Closures capture **variables**, not **values**. The variable's address is shared. This applies to goroutines, callbacks, deferred functions — anywhere a closure outlives the loop iteration.

---

### 3. `defer` — Evaluation Timing and Stacking

`defer` has 3 rules that most developers learn surface-level but misapply:

```go
package main

import "fmt"

// ─── RULE 1: Arguments evaluated IMMEDIATELY ──────────────────
func rule1() {
    x := 10
    defer fmt.Println("deferred x:", x) // x=10 captured NOW
    x = 20
    fmt.Println("current x:", x)
}
// Output:
// current x: 20
// deferred x: 10   ← argument was locked at defer time

// ─── RULE 2: LIFO order ───────────────────────────────────────
func rule2() {
    defer fmt.Println("first")
    defer fmt.Println("second")
    defer fmt.Println("third")
}
// Output: third, second, first

// ─── RULE 3: Named return values CAN be modified ──────────────
func rule3() (result int) {
    defer func() {
        result++ // modifies the named return variable
    }()
    return 10 // sets result=10, then defer runs, result becomes 11
}
// Returns 11, not 10 — surprises most developers

// ─── THE LOOP TRAP ────────────────────────────────────────────
func openFiles(paths []string) {
    for _, path := range paths {
        f, err := openFile(path)
        if err != nil { continue }
        defer f.Close() // ❌ defers stack up — all run at function exit
                        // NOT at end of each iteration
    }
    // All files stay open until openFiles() returns
}

// ─── CORRECT: use closure to scope ────────────────────────────
func openFilesCorrect(paths []string) {
    for _, path := range paths {
        func() {
            f, err := openFile(path)
            if err != nil { return }
            defer f.Close() // ✅ runs when anonymous func returns
        }()
    }
}

func openFile(path string) (interface{ Close() error }, error) { return nil, nil }

func main() {
    rule1()
    rule2()
    fmt.Println("rule3 returns:", rule3()) // 11
}
```

---

### 4. Slice Tricks — Shared Backing Arrays

The most invisible source of data corruption bugs:

```go
package main

import "fmt"

func main() {
    // ─── SHARED BACKING ARRAY ─────────────────────────────────
    original := []int{1, 2, 3, 4, 5}
    slice1 := original[1:3] // [2, 3] — shares memory with original
    slice2 := original[2:4] // [3, 4] — shares memory with original

    slice1[1] = 99           // modifies original[2] ← INVISIBLE MUTATION
    fmt.Println(original)    // [1 2 99 4 5] ← surprise!
    fmt.Println(slice2)      // [99 4]        ← surprise!

    // ─── APPEND ALIASING TRAP ─────────────────────────────────
    a := make([]int, 3, 6) // len=3, cap=6
    a = append(a, 1, 2, 3) // len=6, cap=6 — fills existing array

    b := a[:3]             // b shares backing array, cap=6
    b = append(b, 99)      // ← modifies a[3]! cap not exceeded, no realloc

    fmt.Println(a)         // [0 0 0 99 2 3] ← a[3] silently changed!
    fmt.Println(b)         // [0 0 0 99]

    // ─── THE FIX: full slice expression ───────────────────────
    c := a[:3:3] // third index limits cap — forces realloc on append
    c = append(c, 88)
    fmt.Println(a) // unchanged ✅
    fmt.Println(c) // [0 0 0 88] ✅
}
```

**The full slice expression `a[low:high:max]`** is the expert tool that prevents this class of bugs entirely. Most Go developers don't even know it exists.

---

### 5. Map Iteration Order Is Intentionally Random

Go **deliberately** randomizes map iteration to prevent programs from depending on order:

```go
package main

import (
    "fmt"
    "sort"
)

func main() {
    m := map[string]int{"c": 3, "a": 1, "b": 2}

    // ❌ Order non-deterministic — different every run
    for k, v := range m {
        fmt.Println(k, v)
    }

    // ✅ Deterministic — sort keys first
    keys := make([]string, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    for _, k := range keys {
        fmt.Println(k, m[k])
    }
}
```

**Why it's intentional:** Go team found that deterministic map order created subtle dependencies in programs that then broke when the implementation changed. The randomization forces correctness from day one.

---

### 6. Integer Overflow Is Silent

Go doesn't panic on overflow — it wraps silently:

```go
package main

import (
    "fmt"
    "math"
)

func main() {
    var x int8 = 127
    x++
    fmt.Println(x) // -128 — wraps silently, no panic ❌

    var u uint8 = 0
    u--
    fmt.Println(u) // 255 — wraps silently

    // Safe pattern: check before operation
    func safeAdd(a, b int64) (int64, bool) {
        if b > 0 && a > math.MaxInt64 - b { return 0, false }
        if b < 0 && a < math.MinInt64 - b { return 0, false }
        return a + b, true
    }

    // Or use math/big for arbitrary precision
}
```

---

### 7. String and `[]byte` Are Not Equivalent

```go
package main

import "fmt"

func main() {
    s := "hello"

    // Strings are IMMUTABLE byte sequences
    // s[0] = 'H'  // compile error: cannot assign to s[0]

    // ─── RANGE behaves differently ─────────────────────────────
    s2 := "héllo" // contains a multi-byte rune

    // Index loop: iterates BYTES
    for i := 0; i < len(s2); i++ {
        fmt.Printf("%d: %x\n", i, s2[i])
        // 0:68  1:c3  2:a9  3:6c  4:6c  5:6f — 6 bytes for 5 chars
    }

    // Range loop: iterates RUNES (Unicode code points)
    for i, r := range s2 {
        fmt.Printf("%d: %c\n", i, r)
        // 0:h  1:é  3:l  4:l  5:o — correct characters, indices skip
    }

    // len() counts BYTES, not characters
    fmt.Println(len(s2))           // 6, not 5
    fmt.Println(len([]rune(s2)))   // 5 ✅

    // ─── CONVERSION COST ──────────────────────────────────────
    // string ↔ []byte always allocates (copies memory)
    // Use strings.Builder or bytes.Buffer to avoid repeated allocation
}
```

---

### 8. `copy` and Assignment Semantics

```go
package main

import "fmt"

func main() {
    // ─── ARRAYS: value semantics (copied) ─────────────────────
    a := [3]int{1, 2, 3}
    b := a          // full copy of array
    b[0] = 99
    fmt.Println(a)  // [1 2 3] — unchanged ✅

    // ─── SLICES: reference semantics (shared) ─────────────────
    s := []int{1, 2, 3}
    t := s          // t points to SAME backing array
    t[0] = 99
    fmt.Println(s)  // [99 2 3] — mutated! ❌

    // ─── DEEP COPY of slice ────────────────────────────────────
    u := make([]int, len(s))
    copy(u, s)
    u[0] = 0
    fmt.Println(s)  // [99 2 3] — unchanged ✅
    fmt.Println(u)  // [0 2 3]

    // ─── MAPS: always reference semantics ─────────────────────
    m1 := map[string]int{"a": 1}
    m2 := m1        // same underlying map
    m2["b"] = 2
    fmt.Println(m1) // map[a:1 b:2] — mutated! ❌
}
```

---

## TIER 2 — Deep Language Mechanics

---

### 9. Interface Satisfaction Is Implicit — Pointer vs Value Receiver

The most misunderstood rule in Go interfaces:

```go
package main

import "fmt"

type Stringer interface {
    String() string
}

type Person struct{ Name string }

// Value receiver method
func (p Person) String() string {
    return "Person: " + p.Name
}

type Counter struct{ n int }

// Pointer receiver method
func (c *Counter) Inc() { c.n++ }
func (c *Counter) String() string { return fmt.Sprintf("count=%d", c.n) }

func main() {
    // ─── VALUE RECEIVER: both *T and T satisfy interface ──────
    var s1 Stringer = Person{"Alice"}   // ✅ T satisfies
    var s2 Stringer = &Person{"Bob"}    // ✅ *T also satisfies
    fmt.Println(s1.String())
    fmt.Println(s2.String())

    // ─── POINTER RECEIVER: ONLY *T satisfies interface ────────
    var s3 Stringer = &Counter{}        // ✅ *T satisfies
    // var s4 Stringer = Counter{}      // ❌ compile error!
    // Counter does not implement Stringer (String method has pointer receiver)
    fmt.Println(s3.String())

    // WHY: If you have a value, Go can't always take its address
    // (e.g., map values, return values). So the rule is asymmetric.
}

// ─── METHOD SET RULES ─────────────────────────────────────────
// Type T:  method set = value receiver methods only
// Type *T: method set = value receiver + pointer receiver methods
```

**The spec rule:** *The method set of type `T` consists of all methods with receiver type `T`. The method set of type `*T` consists of all methods with receiver `T` or `*T`.*

---

### 10. `iota` — Full Power

Most developers use iota for simple enums. Experts use its full expressiveness:

```go
package main

import "fmt"

type Direction int
type ByteSize float64
type Flags uint

const (
    North Direction = iota // 0
    East                   // 1
    South                  // 2
    West                   // 3
)

const (
    _           = iota // skip 0
    KB ByteSize = 1 << (10 * iota) // 1 << 10 = 1024
    MB                              // 1 << 20
    GB                              // 1 << 30
    TB                              // 1 << 40
)

const (
    FlagRead Flags = 1 << iota // 1
    FlagWrite                   // 2
    FlagExec                    // 4
)

// Expressions in iota
const (
    A = iota * 2   // 0
    B               // 2
    C               // 4
    D               // 6
)

func main() {
    fmt.Println(North, East, South, West)       // 0 1 2 3
    fmt.Println(KB, MB, GB)                     // 1024 1.048576e+06 1.073741824e+09
    fmt.Println(FlagRead | FlagWrite)           // 3
    fmt.Println(A, B, C, D)                     // 0 2 4 6
}
```

---

### 11. Type Assertion vs Type Switch — And Panics

```go
package main

import "fmt"

func main() {
    var i interface{} = "hello"

    // ─── TYPE ASSERTION ───────────────────────────────────────
    s := i.(string)          // panics if i is not string
    fmt.Println(s)

    s, ok := i.(string)      // safe: ok=false instead of panic
    fmt.Println(s, ok)

    n, ok := i.(int)         // safe: n=0, ok=false
    fmt.Println(n, ok)

    // ─── TYPE SWITCH ──────────────────────────────────────────
    describe := func(v interface{}) string {
        switch x := v.(type) {
        case int:
            return fmt.Sprintf("int: %d", x)
        case string:
            return fmt.Sprintf("string: %q", x)
        case bool:
            return fmt.Sprintf("bool: %v", x)
        case []int:
            return fmt.Sprintf("[]int len=%d", len(x))
        case nil:
            return "nil"
        default:
            return fmt.Sprintf("unknown: %T", x)
        }
    }

    fmt.Println(describe(42))
    fmt.Println(describe("hi"))
    fmt.Println(describe(nil))

    // ─── INTERFACE UPGRADE PATTERN ────────────────────────────
    type Writer interface { Write([]byte) (int, error) }
    type Closer interface { Close() error }
    type WriteCloser interface { Writer; Closer }

    // Check if a Writer also implements Closer at runtime
    checkWriteCloser := func(w Writer) {
        if wc, ok := w.(WriteCloser); ok {
            defer wc.Close()
            _ = wc
        }
    }
    _ = checkWriteCloser
}
```

---

### 12. Struct Embedding — Promotion, Shadowing, and Pitfalls

```go
package main

import "fmt"

type Animal struct{ Name string }
func (a Animal) Breathe() { fmt.Println(a.Name, "breathes") }
func (a Animal) Speak()   { fmt.Println(a.Name, "...") }

type Dog struct {
    Animal         // embedded: Dog.Name, Dog.Breathe() promoted
    Breed string
}
func (d Dog) Speak() { fmt.Println(d.Name, "barks") } // shadows Animal.Speak

type ServiceDog struct {
    Dog
    Task string
}

func main() {
    d := Dog{Animal: Animal{Name: "Rex"}, Breed: "Lab"}

    d.Breathe()           // promoted: calls Animal.Breathe ✅
    d.Speak()             // shadowed: calls Dog.Speak ✅
    d.Animal.Speak()      // explicit: calls Animal.Speak ✅

    // ─── INTERFACE SATISFACTION VIA EMBEDDING ─────────────────
    type Speaker interface{ Speak() }
    var s Speaker = d     // Dog satisfies Speaker via its own Speak() ✅

    // ─── AMBIGUITY TRAP ───────────────────────────────────────
    type A struct{}
    type B struct{}
    func(a A) Hello() {}
    func(b B) Hello() {}

    // type C struct { A; B } // if both have Hello(), C.Hello() is ambiguous
    // c.Hello() // compile error: ambiguous selector

    fmt.Println(s)

    // ─── EMBEDDING ≠ INHERITANCE ──────────────────────────────
    // Go has no "super". Embedded type doesn't know it's embedded.
    // If Animal.Breathe() calls a.Speak(), it calls Animal.Speak(),
    // NOT Dog.Speak() — there is no virtual dispatch.
    sd := ServiceDog{Dog: d, Task: "Guide"}
    sd.Breathe() // Animal.Breathe — "Rex breathes"
    sd.Speak()   // Dog.Speak promoted through ServiceDog — "Rex barks"
    _ = sd
}
```

---

### 13. `init()` — Execution Order and Traps

```go
package main

import "fmt"

// Multiple init() functions are allowed in one file
// Multiple files can each have init()
// init() cannot be called manually

var x = compute() // package-level vars initialized before init()

func compute() int {
    fmt.Println("compute() called")
    return 42
}

func init() {
    fmt.Println("init() #1, x =", x)
}

func init() {
    fmt.Println("init() #2")
}

func main() {
    fmt.Println("main()")
}

// Output:
// compute() called
// init() #1, x = 42
// init() #2
// main()

// ─── PACKAGE INIT ORDER ───────────────────────────────────────
// 1. All imported packages' init() run first (dependency order)
// 2. Package-level variables initialized in declaration order
// 3. init() functions run in source file order, top to bottom
// 4. main() runs last
```

---

### 14. Constants — Untyped Constants and Precision

```go
package main

import "fmt"

func main() {
    // ─── UNTYPED CONSTANTS have arbitrary precision ────────────
    const big = 1 << 100         // valid! no overflow
    const precise = 3.141592653589793238462643383

    // They take type when used in context
    var f float64 = precise      // precision truncated to float64
    var f32 float32 = precise    // further truncated

    fmt.Println(f, f32)

    // ─── TYPED vs UNTYPED ─────────────────────────────────────
    const untypedInt = 100       // untyped int constant
    const typedInt int = 100     // typed int constant

    var x int32 = untypedInt     // ✅ untyped can convert implicitly
    // var y int32 = typedInt    // ❌ compile error: int vs int32

    // ─── CONSTANT EXPRESSIONS evaluated at compile time ────────
    const (
        _  = iota
        KB = 1 << (10 * iota)
        MB
        GB
    )
    // No runtime cost — these are compile-time values
    _ = x
}
```

---

## TIER 3 — Concurrency (Where Senior Bugs Live)

---

### 15. Go Memory Model — Happens-Before

The most important concurrency concept that 95% of Go developers skip:

```go
package main

import (
    "fmt"
    "sync"
)

// The Go Memory Model defines when one goroutine's writes
// are GUARANTEED to be visible to another goroutine.
//
// Without synchronization, the compiler and CPU can reorder operations.
// "Happens-before" relationships guarantee ordering.

var (
    msg  string
    done bool
)

// ❌ DATA RACE — no synchronization
func unsafeShare() {
    msg = "hello"  // write
    done = true    // write
    // Another goroutine reading done=true might still see msg=""
    // CPU/compiler can reorder these writes
}

// ✅ SAFE — using channel establishes happens-before
func safeWithChannel() {
    ch := make(chan struct{})
    go func() {
        msg = "hello"
        ch <- struct{}{} // send happens-after msg write
    }()
    <-ch               // receive happens-after send
    fmt.Println(msg)   // guaranteed to see "hello" ✅
}

// ✅ SAFE — using sync.Mutex
func safeWithMutex() {
    var mu sync.Mutex
    go func() {
        mu.Lock()
        msg = "hello"
        mu.Unlock()
    }()
    mu.Lock()
    fmt.Println(msg)
    mu.Unlock()
}
```

**The rule:** Any communication — channel send/receive, mutex lock/unlock, `sync.WaitGroup.Wait()`, `sync/atomic` operations — establishes a happens-before edge. Without one of these, data races are undefined behavior.

---

### 16. Channel Axioms — Every Developer Must Know

```go
package main

import "fmt"

// ─── THE CHANNEL AXIOM TABLE ──────────────────────────────────
//
// Operation     | nil ch  | open ch         | closed ch
// --------------|---------|-----------------|------------------
// send ch<-v    | blocks  | sends or blocks | PANIC
// receive <-ch  | blocks  | receives/blocks | zero value, ok=false
// close(ch)     | PANIC   | closes ✅       | PANIC
// range ch      | blocks  | iterates        | exits cleanly
//
// ─── FUNDAMENTAL PATTERNS ────────────────────────────────────

// Pattern 1: Done channel (signaling)
func withDone() {
    done := make(chan struct{})
    go func() {
        fmt.Println("worker done")
        close(done) // broadcast to ALL receivers simultaneously
    }()
    <-done
}

// Pattern 2: Semaphore (limit concurrency)
func withSemaphore(urls []string) {
    sem := make(chan struct{}, 10) // max 10 concurrent
    for _, url := range urls {
        sem <- struct{}{}          // acquire
        go func(u string) {
            defer func() { <-sem }() // release
            fmt.Println("fetch", u)
        }(url)
    }
}

// Pattern 3: Pipeline
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums { out <- n }
        close(out)
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n * n }
        close(out)
    }()
    return out
}

// Pattern 4: Timeout
func withTimeout(work func() string) (string, bool) {
    result := make(chan string, 1)
    go func() { result <- work() }()

    select {
    case r := <-result:
        return r, true
    case <-timeoutChan(100): // after 100ms
        return "", false
    }
}
```

---

### 17. `sync.Mutex` vs `sync.RWMutex` vs `sync/atomic`

```go
package main

import (
    "sync"
    "sync/atomic"
    "fmt"
)

// ─── WHEN TO USE WHAT ─────────────────────────────────────────
//
// atomic: single integer/pointer reads/writes — fastest
// RWMutex: many readers, few writers — cache/registry patterns
// Mutex: general mutual exclusion — everything else
// Channel: ownership transfer, signaling, pipeline coordination

// ─── ATOMIC: for simple counters ──────────────────────────────
type AtomicCounter struct {
    n int64
}
func (c *AtomicCounter) Inc() { atomic.AddInt64(&c.n, 1) }
func (c *AtomicCounter) Get() int64 { return atomic.LoadInt64(&c.n) }

// ─── RWMUTEX: for read-heavy caches ───────────────────────────
type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}
func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()         // multiple goroutines can hold RLock simultaneously
    defer c.mu.RUnlock()
    v, ok := c.data[key]
    return v, ok
}
func (c *Cache) Set(key, val string) {
    c.mu.Lock()          // exclusive — blocks all readers and writers
    defer c.mu.Unlock()
    c.data[key] = val
}

// ─── MUTEX TRAP: copying a mutex ──────────────────────────────
type SafeCounter struct {
    mu sync.Mutex
    n  int
}
// ❌ NEVER pass mutex by value — copying an unlocked mutex is undefined
func bad(c SafeCounter) { c.mu.Lock() } // c is a copy!
// ✅ Always use pointer
func good(c *SafeCounter) { c.mu.Lock() }

func main() {
    c := &AtomicCounter{}
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() { defer wg.Done(); c.Inc() }()
    }
    wg.Wait()
    fmt.Println(c.Get()) // 1000 ✅
}
```

---

### 18. `sync.Once`, `sync.Pool`, `sync.Map`

```go
package main

import (
    "fmt"
    "sync"
)

// ─── sync.Once: guaranteed single execution ───────────────────
type Singleton struct{ val int }
var (
    instance *Singleton
    once     sync.Once
)
func getInstance() *Singleton {
    once.Do(func() {
        instance = &Singleton{val: 42} // runs exactly once, goroutine-safe
    })
    return instance
}

// ─── sync.Pool: object reuse, reduces GC pressure ─────────────
var bufPool = sync.Pool{
    New: func() interface{} {
        buf := make([]byte, 4096)
        return &buf
    },
}
func processRequest(data []byte) {
    buf := bufPool.Get().(*[]byte) // reuse allocated buffer
    defer bufPool.Put(buf)         // return to pool
    _ = (*buf)[:len(data)]
    // Important: Pool contents can be GC'd at any time
    // Never rely on an object staying in the pool
}

// ─── sync.Map: concurrent map (specific use cases only) ───────
// Use when: many goroutines read/write disjoint keys
// Avoid when: workload is write-heavy (regular map+mutex is faster)
var sm sync.Map
func withSyncMap() {
    sm.Store("key", 42)
    v, ok := sm.Load("key")
    fmt.Println(v, ok)          // 42 true
    sm.Delete("key")
    sm.Range(func(k, v interface{}) bool {
        fmt.Println(k, v)
        return true // return false to stop iteration
    })
}
```

---

### 19. Goroutine Leaks — The Silent Memory Killer

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// ─── LEAK PATTERN 1: blocked channel send, no receiver ────────
func leaky1() {
    ch := make(chan int) // unbuffered
    go func() {
        ch <- 42 // blocks FOREVER if nobody reads — goroutine leaked
    }()
    // function returns, ch goes out of scope, goroutine stuck forever
}

// ─── LEAK PATTERN 2: blocked channel receive, no sender ───────
func leaky2() {
    ch := make(chan int)
    go func() {
        v := <-ch // blocks FOREVER if nobody sends
        fmt.Println(v)
    }()
}

// ─── FIX: context cancellation ────────────────────────────────
func safeWorker(ctx context.Context, ch <-chan int) {
    go func() {
        for {
            select {
            case v, ok := <-ch:
                if !ok { return }
                fmt.Println(v)
            case <-ctx.Done(): // always have an exit condition
                return
            }
        }
    }()
}

// ─── FIX: done channel ────────────────────────────────────────
func safeWorker2(done <-chan struct{}, jobs <-chan int) {
    go func() {
        for {
            select {
            case j := <-jobs:
                fmt.Println("job", j)
            case <-done:
                return // clean shutdown
            }
        }
    }()
}

// ─── DETECT LEAKS: use goleak in tests ────────────────────────
// import "go.uber.org/goleak"
// func TestFoo(t *testing.T) {
//     defer goleak.VerifyNone(t)
//     // ... your test
// }

func timeoutChan(ms int) <-chan time.Time {
    return time.After(time.Duration(ms) * time.Millisecond)
}
```

---

### 20. `context` — Propagation, Cancellation, Values

```go
package main

import (
    "context"
    "fmt"
    "time"
)

type contextKey string

const userIDKey contextKey = "userID"

// ─── CONTEXT RULES ────────────────────────────────────────────
// 1. Always the first parameter, named ctx
// 2. Never store context in a struct
// 3. Never pass nil context — use context.TODO() or context.Background()
// 4. Use typed keys to avoid collisions

func withContext() {
    // Creation
    ctx := context.Background()                 // root — never cancelled
    ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
    defer cancel()                               // ALWAYS defer cancel

    // Value propagation
    ctx = context.WithValue(ctx, userIDKey, 42)

    // Use in goroutine
    done := make(chan struct{})
    go func() {
        defer close(done)
        for {
            select {
            case <-ctx.Done():
                fmt.Println("cancelled:", ctx.Err()) // DeadlineExceeded
                return
            default:
                userID := ctx.Value(userIDKey).(int)
                fmt.Println("processing for user", userID)
                time.Sleep(500 * time.Millisecond)
            }
        }
    }()
    <-done
}

// ─── PROPAGATION CHAIN ────────────────────────────────────────
func A(ctx context.Context) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    B(ctx) // B respects A's deadline automatically
}

func B(ctx context.Context) {
    select {
    case <-time.After(10 * time.Second):
        fmt.Println("B done")
    case <-ctx.Done():
        fmt.Println("B cancelled:", ctx.Err())
    }
}
```

---

## TIER 4 — Architecture and Idioms

---

### 21. The Error Design System

```go
package main

import (
    "errors"
    "fmt"
)

// ─── SENTINEL ERRORS: for identity checks ─────────────────────
var (
    ErrNotFound   = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
)

// ─── TYPED ERRORS: for structured data ────────────────────────
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed on %s: %s", e.Field, e.Message)
}

// ─── WRAPPED ERRORS: for context chains ───────────────────────
func getUser(id int) error {
    if id <= 0 {
        return fmt.Errorf("getUser(%d): %w", id, ErrNotFound)
    }
    return nil
}

// ─── INSPECTION: errors.Is / errors.As ───────────────────────
func handle(err error) {
    if err == nil { return }

    // errors.Is: checks entire chain for identity
    if errors.Is(err, ErrNotFound) {
        fmt.Println("resource missing")
        return
    }

    // errors.As: checks chain for type, extracts it
    var vErr *ValidationError
    if errors.As(err, &vErr) {
        fmt.Println("bad field:", vErr.Field)
        return
    }

    fmt.Println("unexpected:", err)
}

// ─── WRAPPING CHAIN ───────────────────────────────────────────
func processOrder(userID int) error {
    if err := getUser(userID); err != nil {
        return fmt.Errorf("processOrder: %w", err) // wraps with context
    }
    return nil
}

func main() {
    err := processOrder(-1)
    handle(err) // errors.Is traverses the chain ✅
    fmt.Println(err) // processOrder: getUser(-1): not found
}
```

---

### 22. Interface Design — Small Is Powerful

```go
package main

import (
    "fmt"
    "io"
    "os"
)

// ─── THE INTERFACE SEGREGATION PRINCIPLE ──────────────────────
// Go interfaces should be small — often 1-3 methods.
// Accept interfaces, return structs.

// ❌ Fat interface — forces implementors to implement everything
type BadStorage interface {
    Get(key string) ([]byte, error)
    Set(key string, val []byte) error
    Delete(key string) error
    List(prefix string) ([]string, error)
    Flush() error
    Close() error
}

// ✅ Composed small interfaces
type Getter interface { Get(key string) ([]byte, error) }
type Setter interface { Set(key string, val []byte) error }
type Closer interface { Close() error }
type ReadWriter interface { Getter; Setter }  // compose as needed

// ─── ACCEPT INTERFACES, RETURN CONCRETE ───────────────────────
// Functions that accept interfaces are reusable.
// Functions that return interfaces hide useful type information.

func copyData(dst io.Writer, src io.Reader) (int64, error) {
    return io.Copy(dst, src) // works with files, buffers, network, anything
}

// ─── THE EMPTY INTERFACE ANTI-PATTERN ─────────────────────────
// func process(v interface{}) — loses all type safety
// Prefer generics (Go 1.18+) or specific types

func main() {
    // Copy from file to stdout — same function, different concrete types
    f, _ := os.Open("/dev/null")
    defer f.Close()
    n, _ := copyData(os.Stdout, f)
    fmt.Println("copied", n, "bytes")
}
```

---

### 23. Generics (Go 1.18+) — Constraints and Type Parameters

```go
package main

import (
    "fmt"
    "golang.org/x/exp/constraints"
)

// ─── BASIC GENERIC FUNCTION ───────────────────────────────────
func Map[T, U any](slice []T, fn func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

func Filter[T any](slice []T, pred func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if pred(v) { result = append(result, v) }
    }
    return result
}

// ─── CONSTRAINTS ──────────────────────────────────────────────
func Min[T constraints.Ordered](a, b T) T {
    if a < b { return a }
    return b
}

// ─── GENERIC DATA STRUCTURE ───────────────────────────────────
type Stack[T any] struct {
    items []T
}
func (s *Stack[T]) Push(v T)      { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 { return zero, false }
    top := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return top, true
}

// ─── UNION CONSTRAINT ─────────────────────────────────────────
type Number interface {
    ~int | ~int32 | ~int64 | ~float32 | ~float64
}
func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums { total += n }
    return total
}

func main() {
    nums := []int{1, 2, 3, 4, 5}
    doubled := Map(nums, func(n int) int { return n * 2 })
    evens := Filter(nums, func(n int) bool { return n%2 == 0 })
    fmt.Println(doubled)           // [2 4 6 8 10]
    fmt.Println(evens)             // [2 4]
    fmt.Println(Min(3.14, 2.71))   // 2.71
    fmt.Println(Sum(nums))         // 15

    s := &Stack[string]{}
    s.Push("a"); s.Push("b")
    v, _ := s.Pop()
    fmt.Println(v)                 // b
}
```

---

### 24. Functional Options Pattern

The most elegant API design pattern in Go:

```go
package main

import (
    "fmt"
    "time"
)

type Server struct {
    host    string
    port    int
    timeout time.Duration
    maxConn int
}

type Option func(*Server)

func WithHost(host string) Option {
    return func(s *Server) { s.host = host }
}

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func WithMaxConnections(n int) Option {
    return func(s *Server) { s.maxConn = n }
}

func NewServer(opts ...Option) *Server {
    // sensible defaults
    s := &Server{
        host:    "localhost",
        port:    8080,
        timeout: 30 * time.Second,
        maxConn: 100,
    }
    for _, opt := range opts {
        opt(s) // apply each option
    }
    return s
}

func main() {
    // Caller only specifies what differs from defaults
    s := NewServer(
        WithPort(9090),
        WithTimeout(60*time.Second),
    )
    fmt.Printf("%+v\n", s)
    // &{host:localhost port:9090 timeout:1m0s maxConn:100}
}
```

---

### 25. `io.Reader` / `io.Writer` — The Composition Foundation

```go
package main

import (
    "bytes"
    "compress/gzip"
    "encoding/base64"
    "fmt"
    "io"
    "strings"
)

// The io interfaces are the most powerful in the stdlib.
// They compose to create arbitrary data pipelines.

func transformPipeline(input string) (string, error) {
    // Build a pipeline: string → gzip → base64
    var buf bytes.Buffer

    // Layer 1: base64 encoder wraps the buffer
    b64w := base64.NewEncoder(base64.StdEncoding, &buf)

    // Layer 2: gzip writer wraps the base64 encoder
    gzw := gzip.NewWriter(b64w)

    // Write to the outermost layer — data flows through all layers
    if _, err := io.Copy(gzw, strings.NewReader(input)); err != nil {
        return "", err
    }
    gzw.Close()
    b64w.Close()

    return buf.String(), nil
}

// Custom reader — implements io.Reader
type RepeatReader struct {
    data  []byte
    count int
    pos   int
}

func (r *RepeatReader) Read(p []byte) (int, error) {
    if r.count == 0 { return 0, io.EOF }
    n := copy(p, r.data[r.pos:])
    r.pos += n
    if r.pos >= len(r.data) {
        r.pos = 0
        r.count--
    }
    return n, nil
}

func main() {
    result, _ := transformPipeline("hello world")
    fmt.Println(result[:20], "...") // compressed base64

    rr := &RepeatReader{data: []byte("Go!"), count: 3}
    out, _ := io.ReadAll(rr)
    fmt.Println(string(out)) // Go!Go!Go!
}
```

---

## TIER 5 — Runtime and Performance

---

### 26. Escape Analysis — Stack vs Heap

```go
package main

import "fmt"

// The compiler decides whether a variable lives on the stack or heap.
// Stack allocation is faster (no GC). Heap allocation triggers GC.

// Check with: go build -gcflags="-m" ./...

// ─── STACK allocation (fast) ──────────────────────────────────
func stackAlloc() int {
    x := 42      // stays on stack — doesn't escape
    return x
}

// ─── HEAP allocation (slower, GC'd) ──────────────────────────
func heapAlloc() *int {
    x := 42
    return &x    // x escapes to heap — its address outlives the function
}

// ─── INTERFACE BOXING causes heap allocation ──────────────────
func boxing() {
    x := 42
    var i interface{} = x  // x copied to heap (boxed)
    fmt.Println(i)          // fmt.Println takes interface{} — also escapes
}

// ─── OPTIMIZATION: avoid escape in hot paths ──────────────────
type Point struct{ X, Y float64 }

// Returns struct by value — stays on stack ✅
func newPoint(x, y float64) Point { return Point{x, y} }

// Returns pointer — escapes to heap ❌ (when not inlined)
func newPointPtr(x, y float64) *Point { return &Point{x, y} }

func main() {
    // Use: go build -gcflags="-m -m" to see escape analysis output
    _ = stackAlloc()
    _ = heapAlloc()
}
```

---

### 27. `make` vs `new` — And Preallocating for Performance

```go
package main

import "fmt"

func main() {
    // ─── new: allocates zeroed memory, returns pointer ────────
    p := new(int)       // *int pointing to zero value
    *p = 42
    fmt.Println(*p)

    // ─── make: initializes slices, maps, channels ─────────────
    s := make([]int, 3, 10) // len=3, cap=10 — preallocated!
    m := make(map[string]int, 100) // hint: ~100 entries expected
    ch := make(chan int, 5) // buffered channel, capacity 5

    // ─── PREALLOCATION is critical for performance ────────────
    // BAD: repeated reallocation
    var bad []int
    for i := 0; i < 10000; i++ {
        bad = append(bad, i) // ~14 reallocations (doubling strategy)
    }

    // GOOD: single allocation
    good := make([]int, 0, 10000) // preallocated
    for i := 0; i < 10000; i++ {
        good = append(good, i) // zero reallocations ✅
    }

    // GOOD: map preallocation reduces rehashing
    bigMap := make(map[string]int, 10000)
    _ = bigMap

    _ = s; _ = m; _ = ch
}
```

---

### 28. `strings.Builder` and `bytes.Buffer` — Avoid String Concatenation

```go
package main

import (
    "fmt"
    "strings"
)

func main() {
    // ❌ O(n²) — each += allocates a new string
    bad := ""
    for i := 0; i < 1000; i++ {
        bad += fmt.Sprintf("%d", i) // 1000 allocations
    }

    // ✅ O(n) — single underlying buffer
    var sb strings.Builder
    sb.Grow(4000) // optional: pre-allocate expected size
    for i := 0; i < 1000; i++ {
        fmt.Fprintf(&sb, "%d", i)
    }
    result := sb.String() // single allocation to produce final string
    _ = result; _ = bad
}
```

---

### 29. Benchmarking and Profiling

```go
package main

// ─── WRITING BENCHMARKS ───────────────────────────────────────
// File: bench_test.go

import "testing"

func BenchmarkConcatBad(b *testing.B) {
    for i := 0; i < b.N; i++ {
        s := ""
        for j := 0; j < 100; j++ {
            s += "x"
        }
        _ = s
    }
}

func BenchmarkConcatGood(b *testing.B) {
    for i := 0; i < b.N; i++ {
        var sb strings.Builder
        for j := 0; j < 100; j++ {
            sb.WriteByte('x')
        }
        _ = sb.String()
    }
}

// ─── RUN ──────────────────────────────────────────────────────
// go test -bench=. -benchmem -count=5 ./...
//
// ─── PROFILING ────────────────────────────────────────────────
// go test -bench=. -cpuprofile=cpu.prof
// go tool pprof cpu.prof
//
// go test -bench=. -memprofile=mem.prof
// go tool pprof mem.prof
//
// ─── RACE DETECTOR ────────────────────────────────────────────
// go test -race ./...
// go run -race main.go
```

---

### 30. `go:generate`, Build Tags, and Compiler Directives

```go
//go:build linux && amd64
// +build linux,amd64   // legacy syntax (pre-Go 1.17)

package main

// ─── COMPILER DIRECTIVES ──────────────────────────────────────
//go:noescape    // function doesn't let pointer args escape
//go:nosplit     // don't insert stack-split check (rare)
//go:inline      // hint to inline this function
//go:noinline    // prevent inlining

//go:generate stringer -type=Direction
// Run: go generate ./... to execute these commands

// ─── BUILD TAGS USE CASES ─────────────────────────────────────
// Platform-specific implementations:
// file_linux.go    → //go:build linux
// file_windows.go  → //go:build windows
//
// Test helpers:
// helpers_test.go  → //go:build testonly
//
// Debug builds:
// debug.go         → //go:build debug
```

---

## The Complete Mastery Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                   YOUR GO MASTERY ROADMAP                       │
├─────────────────────────────────────────────────────────────────┤
│ TIER 1 — Subtle Traps                                           │
│  □ nil interface vs typed nil                                   │
│  □ loop variable capture in closures/goroutines                 │
│  □ defer evaluation timing, LIFO, named returns                 │
│  □ slice shared backing arrays + full slice expression          │
│  □ nil vs empty slice (especially JSON)                         │
│  □ map iteration non-determinism                                │
│  □ silent integer overflow                                      │
│  □ string bytes vs runes                                        │
│  □ value vs reference copy semantics                            │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2 — Deep Mechanics                                         │
│  □ pointer vs value receiver + interface method sets           │
│  □ iota full expressiveness                                     │
│  □ type assertion + type switch + panics                        │
│  □ struct embedding (promotion, shadowing, no virtual dispatch) │
│  □ init() order across packages                                 │
│  □ untyped constants and precision                              │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3 — Concurrency                                            │
│  □ Go memory model + happens-before                             │
│  □ channel axioms (nil/open/closed × send/recv/close)          │
│  □ nil channel in select (disable pattern)                     │
│  □ mutex / rwmutex / atomic — when to use which                │
│  □ sync.Once, sync.Pool, sync.Map                              │
│  □ goroutine leak patterns + context cancellation              │
│  □ context propagation + typed keys                             │
├─────────────────────────────────────────────────────────────────┤
│ TIER 4 — Architecture                                           │
│  □ error wrapping: sentinel, typed, %w, errors.Is/As           │
│  □ interface design: small, composable, accept not return       │
│  □ generics: constraints, type params, union types             │
│  □ functional options pattern                                   │
│  □ io.Reader/Writer composition                                 │
├─────────────────────────────────────────────────────────────────┤
│ TIER 5 — Runtime / Performance                                  │
│  □ escape analysis (stack vs heap)                              │
│  □ make vs new, preallocation strategy                         │
│  □ strings.Builder, bytes.Buffer                               │
│  □ writing benchmarks + pprof profiling                        │
│  □ build tags + compiler directives                             │
└─────────────────────────────────────────────────────────────────┘
```

Each item on this list is a deep topic. Pick one per session. Go deep — not wide. The monk approach applies: complete one concept until you can teach it, then move forward.