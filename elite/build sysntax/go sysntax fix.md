Nice, we’re upgrading your brain to a **Go compiler with opinions** now.
Same idea as the Rust set: *broken snippets only*, no solutions, you fix them.

Use these as:

* Predict error → read compiler message → fix with minimal change.
* Treat each like a mini boss fight.

---

# BUG-FIX CHALLENGES — GO EDITION

---

## EASY (GE01–GE25) — Syntax, basics, tiny footguns

```go
// GE01: Missing import, wrong fmt usage
package main

func main() {
    fmt.Println("Hello, Go")
}
```

```go
// GE02: := vs =
package main

func main() {
    x := 10
    x := 20
    println(x)
}
```

```go
// GE03: Unused variable
package main

func main() {
    x := 10
}
```

```go
// GE04: Wrong function name for entry point
package main

func mian() {
    println("Hi")
}
```

```go
// GE05: Type mismatch
package main

import "fmt"

func main() {
    var x int = "10"
    fmt.Println(x)
}
```

```go
// GE06: Missing comma in composite literal
package main

import "fmt"

func main() {
    nums := []int{1, 2 3}
    fmt.Println(nums)
}
```

```go
// GE07: Misusing := in if init
package main

import "fmt"

func main() {
    if x := 10; x = 20 {
        fmt.Println("OK")
    }
}
```

```go
// GE08: for range syntax
package main

import "fmt"

func main() {
    arr := []int{1, 2, 3}
    for i, v in range arr {
        fmt.Println(i, v)
    }
}
```

```go
// GE09: Wrong boolean operator
package main

import "fmt"

func main() {
    x := 5
    if x > 3 and x < 10 {
        fmt.Println("ok")
    }
}
```

```go
// GE10: Forgetting & for pointer
package main

import "fmt"

func main() {
    var p *int
    x := 10
    p = x
    fmt.Println(*p)
}
```

```go
// GE11: String concatenation type mismatch
package main

import "fmt"

func main() {
    x := 10
    s := "value: " + x
    fmt.Println(s)
}
```

```go
// GE12: Redeclaring parameter
package main

import "fmt"

func add(a int, b int) int {
    a := a + b
    return a
}

func main() {
    fmt.Println(add(2, 3))
}
```

```go
// GE13: Missing return
package main

func add(a, b int) int {
    c := a + b
}

func main() {}
```

```go
// GE14: Accessing out-of-bounds index (runtime bug)
package main

import "fmt"

func main() {
    arr := []int{1, 2, 3}
    fmt.Println(arr[3])
}
```

```go
// GE15: Wrong map literal syntax
package main

import "fmt"

func main() {
    m := map[string]int("a": 1, "b": 2)
    fmt.Println(m)
}
```

```go
// GE16: nil map write
package main

import "fmt"

func main() {
    var m map[string]int
    m["a"] = 1
    fmt.Println(m)
}
```

```go
// GE17: Missing closing brace
package main

import "fmt"

func main() {
    fmt.Println("hi")
```

```go
// GE18: Wrong case on exported name
package main

import "fmt"

func main() {
    fmt.println("hello")
}
```

```go
// GE19: Using := at package scope
package main

x := 10

func main() {
    println(x)
}
```

```go
// GE20: Wrong argument count
package main

import "fmt"

func add(a, b, c int) int {
    return a + b + c
}

func main() {
    fmt.Println(add(1, 2))
}
```

```go
// GE21: Assigning to constant
package main

import "fmt"

func main() {
    const x = 10
    x = 20
    fmt.Println(x)
}
```

```go
// GE22: Multiple packages in one file
package main
package utils

func main() {}
```

```go
// GE23: Using undefined variable
package main

import "fmt"

func main() {
    fmt.Println(y)
}
```

```go
// GE24: Wrong := in for
package main

import "fmt"

func main() {
    for i := range 10 {
        fmt.Println(i)
    }
}
```

```go
// GE25: Function call vs type conversion confusion
package main

import "fmt"

func main() {
    x := int(3.5)
    y := int  (3.5)
    fmt.Println(x, y)
}
```

---

## MEDIUM (GM01–GM30) — Pointers, slices, maps, methods, basic concurrency

```go
// GM01: Pointer modification through function
package main

import "fmt"

func inc(x *int) {
    x++
}

func main() {
    a := 10
    inc(&a)
    fmt.Println(a)
}
```

```go
// GM02: Returning pointer to local variable
package main

import "fmt"

func makePointer() *int {
    x := 10
    return &x
}

func main() {
    p := makePointer()
    fmt.Println(*p)
}
```

```go
// GM03: Slice append & lost result
package main

import "fmt"

func main() {
    nums := []int{1, 2}
    append(nums, 3)
    fmt.Println(nums)
}
```

```go
// GM04: Wrong value vs pointer receiver
package main

import "fmt"

type Counter struct {
    n int
}

func (c Counter) Inc() {
    c.n++
}

func main() {
    c := Counter{}
    c.Inc()
    fmt.Println(c.n)
}
```

```go
// GM05: Range over map, modify while ranging
package main

import "fmt"

func main() {
    m := map[string]int{"a": 1, "b": 2}
    for k, v := range m {
        if k == "a" {
            m["c"] = 3
        }
        fmt.Println(k, v)
    }
}
```

```go
// GM06: Method on non-local type
package main

import "time"

func (t time.Time) Reset() {
    // ...
}

func main() {}
```

```go
// GM07: nil slice vs zero-length slice differences
package main

import "fmt"

func main() {
    var s []int
    if s == nil {
        fmt.Println("nil slice")
    }
    if len(s) == 0 && s == []int{} {
        fmt.Println("empty")
    }
}
```

```go
// GM08: Using interface without implementing method
package main

import "fmt"

type Printer interface {
    Print()
}

type User struct {
    Name string
}

func main() {
    var p Printer = User{"Anas"}
    p.Print()
}
```

```go
// GM09: Map key type mismatch
package main

import "fmt"

func main() {
    m := map[int]string{
        "1": "a",
    }
    fmt.Println(m)
}
```

```go
// GM10: Using make with non-slice/map/chan
package main

import "fmt"

func main() {
    x := make(int, 10)
    fmt.Println(x)
}
```

```go
// GM11: shadowing err
package main

import (
    "fmt"
    "strconv"
)

func main() {
    s := "42"
    err := error(nil)
    n, err := strconv.Atoi(s)
    if err != nil {
        fmt.Println("err:", err)
    }
    fmt.Println(n)
}
```

```go
// GM12: goroutine closure capturing loop variable
package main

import (
    "fmt"
    "time"
)

func main() {
    for i := 0; i < 3; i++ {
        go func() {
            fmt.Println(i)
        }()
    }
    time.Sleep(time.Second)
}
```

```go
// GM13: Channel send/receive deadlock (single goroutine)
package main

func main() {
    ch := make(chan int)
    ch <- 1
    <-ch
}
```

```go
// GM14: Closing channel twice
package main

func main() {
    ch := make(chan int)
    close(ch)
    close(ch)
}
```

```go
// GM15: Using len on pointer
package main

import "fmt"

func main() {
    x := 10
    fmt.Println(len(&x))
}
```

```go
// GM16: Copying mutex by value
package main

import (
    "fmt"
    "sync"
)

type Counter struct {
    mu sync.Mutex
    n  int
}

func (c Counter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.n++
}

func main() {
    var c Counter
    c.Inc()
    fmt.Println(c.n)
}
```

```go
// GM17: Panic: nil pointer deref
package main

import "fmt"

type Node struct {
    value int
    next  *Node
}

func main() {
    var head *Node
    fmt.Println(head.next.value)
}
```

```go
// GM18: Using defer in loop incorrectly (just style/logic)
package main

import "fmt"

func main() {
    for i := 0; i < 3; i++ {
        defer fmt.Println(i)
    }
}
```

```go
// GM19: Wrong map iteration variable types
package main

import "fmt"

func main() {
    m := map[string]int{"a": 1, "b": 2}
    for i := range m {
        fmt.Println(i, v)
    }
}
```

```go
// GM20: Converting between []byte and string incorrectly
package main

import "fmt"

func main() {
    b := []byte{65, 66, 67}
    s := string(&b)
    fmt.Println(s)
}
```

```go
// GM21: Variadic function call
package main

import "fmt"

func sum(nums ...int) int {
    s := 0
    for _, v := range nums {
        s += v
    }
    return s
}

func main() {
    arr := []int{1, 2, 3}
    fmt.Println(sum(arr))
}
```

```go
// GM22: Interface nil vs concrete nil
package main

import "fmt"

type Err struct{}

func (e *Err) Error() string { return "err" }

func maybe() error {
    var e *Err = nil
    return e
}

func main() {
    if maybe() == nil {
        fmt.Println("nil")
    } else {
        fmt.Println("non-nil")
    }
}
```

```go
// GM23: Generics – simple max function typo
package main

import "fmt"

func Max[T int | float64](a, b T) T {
    if a > b {
        return a
    }
    return b
}

func main() {
    fmt.Println(Max(3, 4))
}
```

```go
// GM24: Method with pointer receiver called on nil
package main

import "fmt"

type Item struct {
    Name string
}

func (i *Item) Print() {
    fmt.Println(i.Name)
}

func main() {
    var it *Item
    it.Print()
}
```

```go
// GM25: Type assertion without ok check
package main

import "fmt"

func main() {
    var x any = 10
    s := x.(string)
    fmt.Println(s)
}
```

```go
// GM26: Wrong field name in struct literal
package main

type User struct {
    Name string
    Age  int
}

func main() {
    u := User{
        name: "Anas",
        Age:  20,
    }
    _ = u
}
```

```go
// GM27: Writing to closed channel (with goroutine)
package main

func main() {
    ch := make(chan int)
    close(ch)
    go func() {
        ch <- 1
    }()
}
```

```go
// GM28: Wrong order of init in short declaration
package main

import "fmt"

func main() {
    x, y := y, 1
    fmt.Println(x, y)
}
```

```go
// GM29: Defer with pointer receiver mutation confusion
package main

import "fmt"

type Count struct{ n int }

func (c *Count) Inc() {
    defer func() {
        c.n++
    }()
}

func main() {
    c := &Count{}
    c.Inc()
    fmt.Println(c.n)
}
```

```go
// GM30: Multiple return values ignored where required
package main

import "strconv"

func main() {
    strconv.Atoi("10")
}
```

---

## HARD (GH01–GH25) — Interfaces, methods, generics, tricky behavior

```go
// GH01: Interface implementation mismatch
package main

import "fmt"

type Stringer interface {
    String() string
}

type User struct {
    Name string
}

func (u User) String() {
    return u.Name
}

func main() {
    var s Stringer = User{"Anas"}
    fmt.Println(s.String())
}
```

```go
// GH02: Embedding & method promotion confusion
package main

import "fmt"

type A struct{}

func (A) Do() { fmt.Println("A") }

type B struct {
    A
}

func (b B) Do() {
    fmt.Println("B")
    A.Do()
}

func main() {
    var x B
    x.Do()
}
```

```go
// GH03: Copying struct with embedded mutex (buggy)
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    sync.Mutex
    n int
}

func (c SafeCounter) Inc() {
    c.Lock()
    defer c.Unlock()
    c.n++
}

func main() {
    var c SafeCounter
    c.Inc()
    fmt.Println(c.n)
}
```

```go
// GH04: Method set & pointer vs value
package main

import "fmt"

type S struct{}

func (s *S) Hello() {
    fmt.Println("hello")
}

func main() {
    var s S
    s.Hello()
}
```

```go
// GH05: Interface and nil concrete type trap
package main

import "fmt"

type MyErr struct{}

func (e *MyErr) Error() string { return "oops" }

func fail() error {
    var e *MyErr = nil
    if false {
        e = &MyErr{}
    }
    return e
}

func main() {
    if fail() == nil {
        fmt.Println("nil")
    } else {
        fmt.Println("non-nil")
    }
}
```

```go
// GH06: Generics – map keys constraint
package main

import "fmt"

func Keys[M ~map[K]V, K comparable, V any](m M) []K {
    ks := make([]K, 0, len(m))
    for k := range m {
        ks = append(ks, v)
    }
    return ks
}

func main() {
    m := map[string]int{"a": 1, "b": 2}
    fmt.Println(Keys(m))
}
```

```go
// GH07: Custom error type & wrapping
package main

import (
    "errors"
    "fmt"
)

type MyErr struct {
    msg string
}

func (e MyErr) Error() string { return e.msg }

func wrap() error {
    return fmt.Errorf("wrap: %w", MyErr{"boom"})
}

func main() {
    err := wrap()
    var me MyErr
    if errors.Is(err, me) {
        fmt.Println("match MyErr")
    }
}
```

```go
// GH08: Channel directions
package main

func producer(ch <-chan int) {
    ch <- 1
}

func consumer(ch chan<- int) {
    <-ch
}

func main() {
    ch := make(chan int)
    go producer(ch)
    go consumer(ch)
}
```

```go
// GH09: Context cancellation forgotten (semantic)
package main

import (
    "context"
    "time"
)

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), time.Second)
    // missing cancel call
    _ = ctx
}
```

```go
// GH10: Implementing sort.Interface incorrectly
package main

import (
    "fmt"
    "sort"
)

type Ints []int

func (s Ints) Len() int           { return len(s) }
func (s Ints) Less(i, j int) bool { return s[i] < s[j] }
func (s Ints) Swap(i, j int)      { i, j = j, i }

func main() {
    a := Ints{3, 1, 2}
    sort.Sort(a)
    fmt.Println(a)
}
```

```go
// GH11: Mutex usage with pointer vs value receiver
package main

import (
    "fmt"
    "sync"
)

type C struct {
    mu sync.Mutex
    n  int
}

func (c C) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.n++
}

func main() {
    c := &C{}
    c.Inc()
    fmt.Println(c.n)
}
```

```go
// GH12: Recover without panic
package main

import "fmt"

func main() {
    defer func() {
        r := recover()
        fmt.Println("recovered", r)
    }()
    fmt.Println("no panic")
}
```

```go
// GH13: Method on generic type
package main

import "fmt"

type Box[T any] struct {
    v T
}

func (b Box[T]) Get() T {
    return b.v
}

func main() {
    b := Box[int]{v: 10}
    fmt.Println(b.Get())
}
```

```go
// GH14: Nested maps & initialization
package main

import "fmt"

func main() {
    m := map[string]map[string]int{}
    m["a"]["b"] = 1
    fmt.Println(m)
}
```

```go
// GH15: Copy vs reference of slice
package main

import "fmt"

func main() {
    a := []int{1, 2, 3}
    b := a
    a = append(a, 4)
    fmt.Println(a, b)
}
```

```go
// GH16: Race condition (no sync) – semantics
package main

import (
    "fmt"
)

func main() {
    x := 0
    for i := 0; i < 1000; i++ {
        go func() {
            x++
        }()
    }
    fmt.Println(x)
}
```

```go
// GH17: slice re-slicing panic
package main

import "fmt"

func main() {
    s := []int{1, 2, 3}
    t := s[:5]
    fmt.Println(t)
}
```

```go
// GH18: json tags typo
package main

import (
    "encoding/json"
    "fmt"
)

type User struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}

func main() {
    data := []byte(`{"Name":"Anas","Age":20}`)
    var u User
    json.Unmarshal(data, &u)
    fmt.Println(u)
}
```

```go
// GH19: method vs function with same name
package main

import "fmt"

type T struct{}

func (T) Do() { fmt.Println("method") }

func Do() { fmt.Println("func") }

func main() {
    var t T
    t.Do()
    Do(t)
}
```

```go
// GH20: defer in for with goroutines (ordering + race)
package main

import (
    "fmt"
    "time"
)

func main() {
    for i := 0; i < 3; i++ {
        defer fmt.Println("defer", i)
        go func() {
            fmt.Println("go", i)
        }()
    }
    time.Sleep(time.Second)
}
```

```go
// GH21: Implementing io.Reader incorrectly
package main

import "io"

type MyReader struct{}

func (r MyReader) Read(p []byte) int {
    return 0
}

func main() {
    var r io.Reader = MyReader{}
    _ = r
}
```

```go
// GH22: Using sync.WaitGroup incorrectly
package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup
    go func() {
        defer wg.Done()
        fmt.Println("work")
    }()
    wg.Wait()
}
```

```go
// GH23: Type switch missing type in assertion
package main

import "fmt"

func main() {
    var x any = "hi"
    switch v := x.(type) {
    case int:
        fmt.Println("int", v)
    case string:
        fmt.Println("string", v)
    default:
        fmt.Println("other")
    }
}
```

```go
// GH24: Custom MarshalJSON with pointer receiver
package main

import "encoding/json"

type User struct {
    Name string
}

func (u User) MarshalJSON() ([]byte, error) {
    type Alias User
    return json.Marshal(&struct {
        *Alias
        Type string `json:"type"`
    }{
        Alias: (*Alias)(&u),
        Type:  "user",
    })
}

func main() {}
```

```go
// GH25: Deadlock with unbuffered channel and WaitGroup
package main

import (
    "sync"
)

func main() {
    ch := make(chan int)
    var wg sync.WaitGroup
    wg.Add(1)
    go func() {
        defer wg.Done()
        ch <- 1
    }()
    wg.Wait()
    <-ch
}
```

---

## INSANE (GI01–GI20) — Concurrency, tricky interfaces, generics, subtle gotchas

```go
// GI01: Select on nil channels
package main

func main() {
    var ch1 chan int
    var ch2 chan int
    select {
    case <-ch1:
    case ch2 <- 1:
    default:
    }
}
```

```go
// GI02: Self-referential struct via pointer + init
package main

import "fmt"

type Node struct {
    value int
    next  *Node
}

func main() {
    n := Node{value: 1}
    n.next = &n
    fmt.Println(n.next.next.next.value)
}
```

```go
// GI03: Generics + interface + type constraints
package main

import "fmt"

type Number interface {
    ~int | ~float64
}

func Sum[T Number](vals []T) T {
    var s T
    for _, v := range vals {
        s += v
    }
    return s
}

func main() {
    fmt.Println(Sum([]int{1, 2, 3}))
    fmt.Println(Sum([]string{"a", "b"}))
}
```

```go
// GI04: data race on map
package main

import (
    "fmt"
)

func main() {
    m := map[int]int{}
    for i := 0; i < 100; i++ {
        go func(i int) {
            m[i] = i
        }(i)
    }
    fmt.Println(len(m))
}
```

```go
// GI05: Channel leak (goroutines never exit)
package main

func worker(ch <-chan int) {
    for {
        <-ch
    }
}

func main() {
    ch := make(chan int)
    go worker(ch)
}
```

```go
// GI06: Incorrect use of atomic package
package main

import (
    "fmt"
    "sync/atomic"
)

func main() {
    var x int64
    atomic.AddInt64(&x, 1)
    atomic.StoreInt64(x, 2)
    fmt.Println(x)
}
```

```go
// GI07: Implementing custom Future-like type
package main

import "fmt"

type Future[T any] struct {
    ch chan T
}

func NewFuture[T any]() Future[T] {
    return Future[T]{ch: make(chan T)}
}

func (f Future[T]) Resolve(v T) {
    f.ch <- v
}

func (f Future[T]) Await() T {
    return <-f.ch
}

func main() {
    f := NewFuture[int]()
    go func() {
        f.Resolve(10)
    }()
    fmt.Println(f.Await())
}
```

```go
// GI08: sync.Map misuse
package main

import (
    "fmt"
    "sync"
)

func main() {
    var m sync.Map
    m["a"] = 1
    v, ok := m.Load("a")
    fmt.Println(v, ok)
}
```

```go
// GI09: pointer to interface vs interface value
package main

import "fmt"

type S struct {
    n int
}

type I interface {
    Get() int
}

func (s S) Get() int { return s.n }

func main() {
    var s S = S{10}
    var i *I = &s
    fmt.Println((*i).Get())
}
```

```go
// GI10: Generic method with pointer receiver
package main

import "fmt"

type Box[T any] struct {
    v T
}

func (b *Box[T]) Set(v T) {
    b.v = v
}

func main() {
    var b Box[int]
    Box[int].Set(&b, 10)
    fmt.Println(b.v)
}
```

```go
// GI11: nested select + context cancellation
package main

import (
    "context"
)

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    select {
    case <-ctx.Done():
    default:
        select {
        case <-ctx.Done():
        }
    }
    cancel()
}
```

```go
// GI12: locking order deadlock
package main

import "sync"

func main() {
    var mu1, mu2 sync.Mutex
    go func() {
        mu1.Lock()
        defer mu1.Unlock()
        mu2.Lock()
        defer mu2.Unlock()
    }()
    mu2.Lock()
    defer mu2.Unlock()
    mu1.Lock()
    defer mu1.Unlock()
}
```

```go
// GI13: reflection misuse
package main

import (
    "fmt"
    "reflect"
)

func main() {
    x := 10
    v := reflect.ValueOf(x)
    v.SetInt(20)
    fmt.Println(x)
}
```

```go
// GI14: type alias vs new type
package main

import "fmt"

type MyInt = int
type YourInt int

func main() {
    var a MyInt = 10
    var b YourInt = 20
    a = b
    fmt.Println(a, b)
}
```

```go
// GI15: panic in deferred recover chain
package main

import "fmt"

func main() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("recovered", r)
        }
        panic("again")
    }()
    panic("first")
}
```

```go
// GI16: embedded interface cycle
package main

type A interface {
    B
}

type B interface {
    A
}

func main() {}
```

```go
// GI17: nil function call
package main

func main() {
    var f func()
    f()
}
```

```go
// GI18: huge stack via recursion
package main

import "fmt"

func f(n int) int {
    if n == 0 {
        return 1
    }
    return n * f(n-1)
}

func main() {
    fmt.Println(f(1000000))
}
```

```go
// GI19: multi-valued assignment + blank identifier misuse
package main

import "fmt"

func f() (int, error) {
    return 10, nil
}

func main() {
    x, _ := f()
    _ = x
    _, err := f()
    if x != nil {
        fmt.Println("err", err)
    }
}
```

```go
// GI20: raw string literal vs interpreted string
package main

import "fmt"

func main() {
    path1 := "C:\new_folder\test.txt"
    path2 := `C:\new_folder\test.txt`
    fmt.Println(path1)
    fmt.Println(path2)
}
```

---

## How to grind these into permanent skill

Same training loop as with Rust:

1. **Before compiling**:
   Look at code, say out loud:

   * “This will fail because …”
   * “The rule I’m violating is …”

2. **Compile / run**:
   Read the full error text like a lawyer, not like a skimmer.

3. **Fix with minimal changes** that preserve original intent. Don’t refactor away the lesson.

4. For tricky ones (especially concurrency & interfaces):

   * Write a *small* variant that’s correct and idiomatic.
   * Summarize the pattern: “Never do X, always do Y in Go.”

Do this seriously and repeatedly and your Go brain will start pre-compiling code as you type, long before `go build` says anything. That’s where “elite” lives.

// ============================================================================
// GO SYNTAX MASTERY: 100+ CHALLENGES FOR ELITE MASTERY
// ============================================================================
// Instructions:
// 1. Find and fix ALL bugs in each challenge
// 2. Run the code to verify
// 3. Explain the bug category and rule violated
// 4. Track your score: Easy=5pts, Medium=10pts, Hard=20pts, Insane=50pts
// ============================================================================

package main

import (
	"fmt"
	"time"
)

// ============================================================================
// EASY LEVEL (1-30): FOUNDATION BUGS [5 points each]
// ============================================================================

// E01: Redeclaration with :=
func E01() {
	x := 10
	x := 20 // BUG: Can't redeclare with :=
	fmt.Println(x)
}

// E02: := outside function
var y := 10 // BUG: := only works inside functions

// E03: Unused variable
func E03() {
	x := 10 // BUG: Declared but not used
	y := 20
	fmt.Println(y)
}

// E04: Missing package
func E04() {
	Println("Hello") // BUG: Must use fmt.Println
}

// E05: Case sensitivity
func E05() {
	X := 10 // Exported
	fmt.Println(x) // BUG: Undefined (lowercase)
}

// E06: Wrong assignment operator
func E06() {
	var x int
	x := 10 // BUG: Already declared, use =
	fmt.Println(x)
}

// E07: Missing semicolon logic
func E07() {
	x := 10
	y := 20; // BUG: Unnecessary semicolon
	fmt.Println(x, y)
}

// E08: Integer division
func E08() {
	x := 10 / 3 // BUG: Returns 3, not 3.333...
	fmt.Println(x)
}

// E09: String concatenation
func E09() {
	s := "Hello"
	s[0] = 'h' // BUG: Strings are immutable
	fmt.Println(s)
}

// E10: Array bounds
func E10() {
	arr := [3]int{1, 2, 3}
	fmt.Println(arr[3]) // BUG: Index out of range
}

// E11: Nil slice vs empty slice
func E11() {
	var s []int
	s[0] = 10 // BUG: Nil slice, can't assign
	fmt.Println(s)
}

// E12: Map access
func E12() {
	var m map[string]int
	m["key"] = 10 // BUG: Nil map, must initialize
	fmt.Println(m)
}

// E13: Pointer dereference
func E13() {
	var p *int
	*p = 10 // BUG: Nil pointer dereference
	fmt.Println(*p)
}

// E14: Range variable reuse
func E14() {
	nums := []int{1, 2, 3}
	for i := range nums {
		i := i * 2 // BUG: Shadows loop variable
		fmt.Println(i)
	}
}

// E15: Missing return
func E15() int {
	x := 10
	// BUG: No return statement
}

// E16: Return type mismatch
func E16() int {
	return "10" // BUG: Returns string, expects int
}

// E17: Multiple returns
func E17() (int, error) {
	return 10 // BUG: Must return 2 values
}

// E18: Ignoring error
func E18() {
	x := strconv.Atoi("10") // BUG: Atoi returns (int, error)
	fmt.Println(x)
}

// E19: Wrong import
func E19() {
	Atoi("10") // BUG: Must use strconv.Atoi
}

// E20: Capitalization in struct
func E20() {
	type person struct {
		Name string
		age int // BUG: Won't be exported
	}
	p := person{Name: "Alice", age: 30}
	fmt.Println(p)
}

// E21: Struct literal syntax
func E21() {
	type Point struct { X, Y int }
	p := Point{10, 20, 30} // BUG: Too many values
	fmt.Println(p)
}

// E22: Method receiver
func E22() {
	type Counter struct { n int }
	func (Counter) Increment() { // BUG: Needs pointer receiver to modify
		c.n++
	}
}

// E23: Interface satisfaction
func E23() {
	type Reader interface { Read() string }
	type Book struct{}
	func (b Book) read() string { return "content" } // BUG: Lowercase, doesn't satisfy
	var r Reader = Book{}
	fmt.Println(r.Read())
}

// E24: Channel send on nil
func E24() {
	var ch chan int
	ch <- 10 // BUG: Sending to nil channel blocks forever
}

// E25: Goroutine closure
func E25() {
	for i := 0; i < 3; i++ {
		go func() {
			fmt.Println(i) // BUG: Captures loop variable
		}()
	}
	time.Sleep(time.Second)
}

// E26: Slice append confusion
func E26() {
	s := []int{1, 2, 3}
	append(s, 4) // BUG: Append doesn't modify in place
	fmt.Println(s)
}

// E27: Wrong type assertion
func E27() {
	var i interface{} = "hello"
	x := i.(int) // BUG: Type assertion fails, panics
	fmt.Println(x)
}

// E28: Missing address operator
func E28() {
	type Point struct { X int }
	p := Point{10}
	modifyPoint(p) // BUG: Pass by value, won't modify
	fmt.Println(p.X)
}
func modifyPoint(p *Point) { p.X = 20 }

// E29: Switch fallthrough confusion
func E29() {
	x := 2
	switch x {
	case 1:
		fmt.Println("one")
	case 2:
		fmt.Println("two")
		// BUG: Expects "three" but Go doesn't fallthrough
	case 3:
		fmt.Println("three")
	}
}

// E30: Defer execution order
func E30() {
	defer fmt.Println("1")
	defer fmt.Println("2")
	defer fmt.Println("3")
	// BUG: Prints 3, 2, 1 (LIFO), not 1, 2, 3
}

// ============================================================================
// MEDIUM LEVEL (31-60): COMMON INTERVIEW TRAPS [10 points each]
// ============================================================================

// M31: Slice vs array in function
func M31() {
	arr := [3]int{1, 2, 3}
	modifyArray(arr) // BUG: Arrays pass by value
	fmt.Println(arr)
}
func modifyArray(a [3]int) { a[0] = 999 }

// M32: Multi-variable short declaration
func M32() {
	x := 10
	x, y := 20, 30 // BUG: At least one new variable required
	fmt.Println(x, y)
}

// M33: Range over map order
func M33() {
	m := map[int]string{1: "a", 2: "b", 3: "c"}
	for k, v := range m {
		fmt.Println(k, v) // BUG: Order not guaranteed
	}
	// Expectation: Sorted order (wrong assumption)
}

// M34: Goroutine race condition
func M34() {
	counter := 0
	for i := 0; i < 100; i++ {
		go func() {
			counter++ // BUG: Race condition
		}()
	}
	time.Sleep(time.Second)
	fmt.Println(counter)
}

// M35: Channel close confusion
func M35() {
	ch := make(chan int)
	close(ch)
	ch <- 10 // BUG: Sending to closed channel panics
}

// M36: Select with nil channel
func M36() {
	var ch chan int
	select {
	case <-ch: // BUG: Receiving from nil blocks forever
		fmt.Println("received")
	}
}

// M37: Context cancellation leak
func M37() {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	go doWork(ctx)
	// BUG: Never calls cancel(), leaks goroutine
	time.Sleep(time.Second)
}
func doWork(ctx context.Context) { <-ctx.Done() }

// M38: JSON marshal unexported
func M38() {
	type User struct {
		name string // BUG: Unexported, won't marshal
		Age  int
	}
	u := User{name: "Alice", Age: 30}
	data, _ := json.Marshal(u)
	fmt.Println(string(data))
}

// M39: Interface nil confusion
func M39() {
	var p *int
	var i interface{} = p
	if i == nil { // BUG: i is not nil (contains type info)
		fmt.Println("nil")
	} else {
		fmt.Println("not nil")
	}
}

// M40: Mutex lock without unlock
func M40() {
	var mu sync.Mutex
	mu.Lock()
	// BUG: Missing defer mu.Unlock()
	doSomething()
}
func doSomething() {}

// M41: WaitGroup miscounted
func M41() {
	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		go func() {
			wg.Add(1) // BUG: Add before goroutine, not inside
			defer wg.Done()
		}()
	}
	wg.Wait()
}

// M42: Time.After leak
func M42() {
	for {
		select {
		case <-time.After(time.Second): // BUG: Creates new timer each iteration
			fmt.Println("tick")
		}
	}
}

// M43: String concatenation in loop
func M43() {
	s := ""
	for i := 0; i < 10000; i++ {
		s += "a" // BUG: Quadratic complexity, use strings.Builder
	}
	fmt.Println(len(s))
}

// M44: Copy slice incorrectly
func M44() {
	src := []int{1, 2, 3, 4, 5}
	dst := []int{}
	copy(dst, src) // BUG: dst length is 0, nothing copied
	fmt.Println(dst)
}

// M45: Pointer to loop variable
func M45() {
	items := []int{1, 2, 3}
	var ptrs []*int
	for _, item := range items {
		ptrs = append(ptrs, &item) // BUG: All point to same variable
	}
	for _, p := range ptrs {
		fmt.Println(*p)
	}
}

// M46: Type assertion without check
func M46() {
	var i interface{} = "hello"
	x := i.(int) // BUG: Panics, use x, ok := i.(int)
	fmt.Println(x)
}

// M47: Struct comparison with slice
func M47() {
	type Data struct {
		Values []int // BUG: Can't compare structs with slices
	}
	d1 := Data{Values: []int{1, 2}}
	d2 := Data{Values: []int{1, 2}}
	fmt.Println(d1 == d2)
}

// M48: Method set on value vs pointer
func M48() {
	type Counter struct{ n int }
	func (c *Counter) Inc() { c.n++ }
	
	var i interface{} = Counter{} // BUG: Value doesn't satisfy pointer receiver
	i.(interface{ Inc() }).Inc()
}

// M49: Defer in loop
func M49() {
	for i := 0; i < 5; i++ {
		defer fmt.Println(i) // BUG: All defers execute after loop
	}
	// Prints: 4 3 2 1 0
}

// M50: Buffer overflow in bytes.Buffer
func M50() {
	var buf bytes.Buffer
	buf.WriteString("hello")
	data := buf.Bytes()
	data[0] = 'H' // BUG: Modifies internal buffer
	fmt.Println(buf.String())
}

// ============================================================================
// HARD LEVEL (61-85): SUBTLE MULTI-LAYERED BUGS [20 points each]
// ============================================================================

// H61: Race with slice append
func H61() {
	s := []int{}
	for i := 0; i < 100; i++ {
		go func(n int) {
			s = append(s, n) // BUG: Data race on s
		}(i)
	}
	time.Sleep(time.Second)
	fmt.Println(len(s))
}

// H62: Goroutine parameter capture in closure
func H62() {
	funcs := []func(){}
	for i := 0; i < 3; i++ {
		funcs = append(funcs, func() {
			fmt.Println(i) // BUG: Captures i reference
		})
	}
	for _, f := range funcs {
		f()
	}
}

// H63: Nested struct method receiver
func H63() {
	type Inner struct{ x int }
	type Outer struct{ Inner }
	func (i Inner) Update() { i.x = 10 } // BUG: Value receiver
	
	o := Outer{Inner{5}}
	o.Update()
	fmt.Println(o.x)
}

// H64: Channel buffer size and deadlock
func H64() {
	ch := make(chan int, 1)
	ch <- 1
	ch <- 2 // BUG: Buffer full, deadlock
	fmt.Println(<-ch)
}

// H65: Select default escape hatch
func H65() {
	ch := make(chan int)
	select {
	case v := <-ch:
		fmt.Println(v)
	default: // BUG: Default always chosen, never blocks
		fmt.Println("nothing")
	}
}

// H66: Map concurrent read/write
func H66() {
	m := make(map[int]int)
	go func() {
		for i := 0; i < 100; i++ {
			m[i] = i // BUG: Concurrent write
		}
	}()
	go func() {
		for i := 0; i < 100; i++ {
			_ = m[i] // BUG: Concurrent read
		}
	}()
	time.Sleep(time.Second)
}

// H67: Slice grow during iteration
func H67() {
	s := []int{1, 2, 3}
	for _, v := range s {
		s = append(s, v) // BUG: Range snapshot, infinite conceptually
	}
	fmt.Println(s)
}

// H68: Type assertion on nil interface
func H68() {
	var i interface{}
	v, ok := i.(int) // BUG: i is nil, always false
	fmt.Println(v, ok)
}

// H69: Embedding and shadowing
func H69() {
	type Base struct{ name string }
	type Derived struct {
		Base
		name string // BUG: Shadows Base.name
	}
	d := Derived{Base{"base"}, "derived"}
	fmt.Println(d.name, d.Base.name)
}

// H70: Context value key collision
func H70() {
	type key string
	ctx := context.WithValue(context.Background(), "user", "alice")
	// BUG: String keys can collide, use private type
	v := ctx.Value("user")
	fmt.Println(v)
}

// H71: Recover in wrong goroutine
func H71() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("recovered") // BUG: Won't catch panic in goroutine
		}
	}()
	go func() {
		panic("boom")
	}()
	time.Sleep(time.Second)
}

// H72: Slice memory leak
func H72() {
	data := make([]byte, 1000000)
	small := data[:5] // BUG: small holds reference to entire array
	return small
}

// H73: Escape analysis confusion
func H73() {
	x := 10
	p := &x
	go func() {
		fmt.Println(*p) // BUG: x escapes to heap
	}()
}

// H74: Named return shadowing
func H74() (result int) {
	result = 10
	if true {
		result := 20 // BUG: Shadows named return
		return result
	}
	return
}

// H75: Interface method set value
func H75() {
	type Incrementer interface{ Inc() }
	type Counter struct{ n int }
	func (c *Counter) Inc() { c.n++ }
	
	var i Incrementer = Counter{} // BUG: Value doesn't implement
	i.Inc()
}

// ============================================================================
// INSANE LEVEL (86-100+): EXPERT TRAPS [50 points each]
// ============================================================================

// I86: Memory order and cache coherence
func I86() {
	var ready, answer int
	go func() {
		answer = 42
		ready = 1 // BUG: No memory barrier, may reorder
	}()
	for ready == 0 {
	}
	fmt.Println(answer)
}

// I87: Finalizer resurrection
func I87() {
	type Resource struct{ data []byte }
	r := &Resource{make([]byte, 100)}
	runtime.SetFinalizer(r, func(r *Resource) {
		r.data = nil // BUG: Can resurrect r
	})
}

// I88: CGO pointer rules
func I88() {
	// BUG: Can't pass Go pointer to C if it contains Go pointers
	// type Data struct{ p *int }
	// C.process(unsafe.Pointer(&Data{new(int)}))
}

// I89: Reflect.Value mutation
func I89() {
	x := 10
	v := reflect.ValueOf(x)
	v.SetInt(20) // BUG: Can't set through unaddressable value
	fmt.Println(x)
}

// I90: Atomic alignment on 32-bit
func I90() {
	type Data struct {
		flag bool
		counter int64 // BUG: May not be 8-byte aligned on 32-bit
	}
	var d Data
	atomic.AddInt64(&d.counter, 1)
}

// I91: Select statement race
func I91() {
	ch1, ch2 := make(chan int), make(chan int)
	go func() { ch1 <- 1 }()
	go func() { ch2 <- 2 }()
	select {
	case v := <-ch1: // BUG: Race on which case chosen
		fmt.Println(v)
	case v := <-ch2:
		fmt.Println(v)
	}
}

// I92: Slice bounds check elimination
func I92() {
	s := []int{1, 2, 3}
	for i := 0; i <= len(s); i++ { // BUG: i can equal len(s)
		fmt.Println(s[i])
	}
}

// I93: Timer Reset pitfall
func I93() {
	t := time.NewTimer(time.Second)
	<-t.C
	t.Reset(time.Second) // BUG: May have value in channel
	// Should drain channel before reset
}

// I94: Embedding promoted methods
func I94() {
	type Logger interface{ Log(string) }
	type Base struct{}
	func (b *Base) Log(s string) { fmt.Println(s) }
	
	type Derived struct{ Base } // BUG: Base is value, not *Base
	var l Logger = &Derived{}
	l.Log("test")
}

// I95: Generics type inference failure
func I95() {
	func process[T any](x T) T { return x }
	result := process(nil) // BUG: Can't infer T from untyped nil
	fmt.Println(result)
}

// I96: Struct tag reflection
func I96() {
	type User struct {
		Name string `json:"name"`
		age  int    `json:"age"` // BUG: Unexported, tag ignored
	}
	u := User{Name: "Alice", age: 30}
	data, _ := json.Marshal(u)
	fmt.Println(string(data))
}

// I97: Buffered channel full check
func I97() {
	ch := make(chan int, 2)
	ch <- 1
	if len(ch) < cap(ch) { // BUG: Race condition
		ch <- 2
		ch <- 3
	}
}

// I98: Goroutine stack growth
func I98() {
	var recurse func(int)
	recurse = func(n int) {
		var buf [1024]int // BUG: May cause stack overflow
		if n > 0 {
			recurse(n - 1)
		}
		_ = buf
	}
	recurse(1000000)
}

// I99: Type switch break confusion
func I99() {
	var i interface{} = 10
	switch v := i.(type) {
	case int:
		if v > 5 {
			break // BUG: Breaks switch, not outer loop
		}
		fmt.Println(v)
	}
}

// I100: Method expression edge case
func I100() {
	type Counter struct{ n int }
	func (c Counter) Get() int { return c.n }
	
	f := Counter.Get // Method expression
	c := Counter{10}
	fmt.Println(f(c)) // Works
	
	p := &Counter{20}
	fmt.Println(f(p)) // BUG: Expects Counter, not *Counter
}

// BONUS INSANE CHALLENGES (101-110)

// I101: Weak pointer equivalent
func I101() {
	// Go has no weak references
	// BUG: Map keys keep objects alive
	cache := make(map[string]*Resource)
	r := &Resource{}
	cache["key"] = r
	r = nil
	runtime.GC()
	// r still reachable through cache
}

// I102: Stack vs heap escape complex
func I102() {
	func makePointer() *int {
		x := 10
		return &x // BUG: x escapes to heap (not always a bug)
	}
	p := makePointer()
	fmt.Println(*p)
}

// I103: Zero value struct method
func I103() {
	type Service struct{ client *http.Client }
	func (s Service) Request() error {
		return s.client.Get("url") // BUG: nil pointer if zero value
	}
	var s Service
	s.Request()
}

// I104: Concurrent map initialization
func I104() {
	var m map[string]int
	var once sync.Once
	
	get := func(k string) int {
		once.Do(func() { m = make(map[string]int) })
		return m[k] // BUG: Still race, map access not protected
	}
	
	go get("key")
	go get("key")
}

// I105: Float comparison
func I105() {
	a := 0.1 + 0.2
	if a == 0.3 { // BUG: Float precision
		fmt.Println("equal")
	} else {
		fmt.Println("not equal")
	}
}

// ============================================================================
// SCORING FUNCTION
// ============================================================================

func main() {
	fmt.Println("🎯 GO SYNTAX MASTERY: 105 CHALLENGES")
	fmt.Println("=====================================")
	fmt.Println("Easy (E01-E30): 5 points × 30 = 150 points")
	fmt.Println("Medium (M31-M60): 10 points × 30 = 300 points")
	fmt.Println("Hard (H61-H85): 20 points × 25 = 500 points")
	fmt.Println("Insane (I86-I105): 50 points × 20 = 1000 points")
	fmt.Println("=====================================")
	fmt.Println("TOTAL POSSIBLE: 1950 points")
	fmt.Println("\n🏆 MASTER THRESHOLD: 1500+ points")
	fmt.Println("💀 ELITE THRESHOLD: 1800+ points")
}

# **Go Syntax Mastery: The Elite Training Ground**

Welcome to your **100+ challenge gauntlet** designed to forge you into a Go master who never makes syntax errors, typos, or logical bugs again. This is designed for **deliberate practice** — each mistake you make here is one you'll never make in an interview or production code.

---

## **Training Philosophy: The "Bug Immunity" System**

**Mental Model:** Treat each bug type as a *pattern* to be internalized through **spaced repetition** and **error prediction**. Before running code, you should *feel* the bug — like a grandmaster sees checkmate before it happens.

**Cognitive Strategy:**
1. **Pattern Recognition:** Group bugs by category (declaration, scope, types, concurrency)
2. **Error Prediction:** Before fixing, predict *why* it fails (compiler error vs runtime panic vs logic bug)
3. **Instant Recall:** After fixing, explain the rule in one sentence
4. **Progressive Overload:** Easy → Medium → Hard → Insane (nested traps)

**Gamification:**
- ✅ **Easy (1-30):** Foundation bugs — 5 points each
- 🔶 **Medium (31-60):** Common interview traps — 10 points each
- 🔥 **Hard (61-85):** Subtle multi-layered bugs — 20 points each
- 💀 **Insane (86-100+):** Expert-level traps that combine 3+ concepts — 50 points each

**Target:** 1500+ points = **Go Syntax Master** (zero mistakes in interviews)

------

## **How to Master This Training**

### **Phase 1: Deliberate Diagnosis (Week 1-2)**
1. **Read each bug** — don't fix yet, just identify the category
2. **Predict the error** — will it compile? Panic? Wrong output?
3. **Fix systematically** — solve 10 easy → 5 medium → 3 hard → 1 insane per day
4. **Track patterns** — keep a notebook of bug types you missed

### **Phase 2: Speed Rounds (Week 3)**
- Set a timer: 30 seconds per Easy, 2 minutes per Medium, 5 minutes per Hard
- Fix without running code first — develop "compiler vision"
- Run only to verify — you should know what's wrong instantly

### **Phase 3: Reverse Engineering (Week 4)**
- For each bug you fix, **write 3 similar variants**
- Create your own "Insane" level bugs by combining concepts
- Challenge: Can you write a bug that combines 5+ concepts?

---

## **Key Mental Models to Internalize**

### **1. The "Two Types" Rule**
Every bug falls into two categories:
- **Compile-time** (type errors, undefined names, syntax)
- **Runtime** (nil pointers, race conditions, panics)

Always predict *when* a bug manifests before fixing.

### **2. The "Zero Value" Mindset**
Go initializes everything — maps, pointers, channels → `nil`. Before using, ask: *"Is this zero value safe?"*

### **3. The "Ownership" Model**
- **Values** → copied (safe, slower)
- **Pointers** → shared (fast, dangerous)
- **Slices/Maps/Channels** → reference semantics (tricky)

### **4. The "Goroutine Capture" Trap**
Any variable referenced in a closure *may* be captured by reference. Default assumption: **always pass as parameter**.

---

## **Psychological Flow States**

**Before each session:**
1. **5-minute meditation** — clear mental cache
2. **Declare intent** — "I will master defer, channels, and interfaces today"
3. **Predict difficulty** — set realistic goals (don't burn out)

**After each bug:**
- **Micro-celebration** — fist pump, positive self-talk ("I see it now")
- **One-sentence rule** — extract the core principle ("Never use := twice")

**Weekly review:**
- **Pattern map** — which categories do you still mistake?
- **Speed test** — re-solve 10 random bugs in 5 minutes

---

## **Next Steps After Mastery**

Once you hit **1500+ points**, you'll have:
✅ **Muscle memory** for Go syntax  
✅ **Pattern recognition** for common traps  
✅ **Interview confidence** (zero silly mistakes)

**Then level up to:**
1. **Performance challenges** (optimize time/space complexity)
2. **Concurrency deep dive** (sync primitives, channels, patterns)
3. **DSA in Go** (implement trees, graphs, DP with idiomatic Go)

---

## **Your Mission**

Fix all 105 bugs. Track your score. When you reach **1800+ points**, you'll be in the **top 1% of Go engineers** who never make syntax mistakes.

**Remember:** The goal isn't just to fix bugs — it's to *internalize patterns* so deeply that you write correct code by instinct.

*Now go. Train like your interview depends on it — because it does.* 🔥