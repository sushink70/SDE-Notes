# Comprehensive Guide to Go by Example

Go by Example is a hands-on introduction to Go using annotated example programs. Below is a complete guide to all the major topics covered on the site.

## Basics

### Hello World
The foundational program that introduces Go syntax and how to run programs. Demonstrates the main package, imports, and the main() function.

### Values
Covers Go's basic data types including strings, integers, floats, and booleans with practical examples.

### Variables
Explains variable declaration using var, const, and the := short declaration syntax. Shows typed and untyped declarations.

### Constants
Demonstrates how to define and use constants in Go, including the difference between typed and untyped constants.

### For Loops
Covers the fundamental looping construct in Go, including for loops with range, condition-only loops, and infinite loops.

### If/Else
Shows conditional logic with if, else if, and else statements with practical examples.

### Switch
Demonstrates switch statements, default cases, and expression-based switching.

## Functions & Methods

### Functions
Explains function declarations, parameters, return values, and multiple return values.

### Multiple Return Values
Shows how Go allows functions to return multiple values, a powerful feature for error handling.

### Variadic Functions
Covers functions that accept a variable number of arguments using the ... syntax.

### Closures
Demonstrates how functions can reference variables outside their scope and create closures.

### Recursion
Shows recursive function calls and how to implement recursive algorithms in Go.

### Methods
Introduces methods, which are functions with receiver arguments that allow object-oriented programming patterns.

## Data Structures

### Arrays
Covers fixed-size arrays, array initialization, and basic array operations.

### Slices
Demonstrates slices as dynamic arrays, including make, append, copy operations, and slice operations.

### Maps
Shows key-value data structures, map initialization, iteration, and value checking.

### Structs
Introduces struct definitions, struct literals, and accessing fields. Shows how to organize related data.

### Range
Covers the range keyword for iterating over arrays, slices, maps, and strings.

### Pointers
Explains pointer types, dereferencing, and passing pointers to functions for reference semantics.

## String & Text Processing

### Strings
Covers Go's string type, string literals, common string operations, and immutability.

### Runes
Demonstrates rune types for handling Unicode characters and strings character-by-character.

### String Formatting
Shows the fmt package for formatting and printing strings with various format verbs.

### String Functions
Covers the strings package with functions like Contains, Count, Index, Join, Split, Replace, and more.

### Regular Expressions
Demonstrates pattern matching and text manipulation using the regexp package.

### JSON
Shows how to marshal and unmarshal JSON data using struct tags and the encoding/json package.

## Advanced Features

### Interfaces
Covers Go's powerful interface system, implicit interface implementation, and interface-based design.

### Errors
Shows the error interface and how Go handles errors with explicit error checking.

### Goroutines
Introduces goroutines, lightweight concurrency primitives that run concurrently with other goroutines.

### Channels
Demonstrates channels for communication between goroutines, including sending and receiving values.

### Channel Buffering
Shows buffered channels and how to manage the number of pending values.

### Channel Synchronization
Covers using channels to wait for goroutines to finish tasks.

### Channel Directions
Demonstrates send-only and receive-only channel types for better code clarity.

### Select
Shows how to wait on multiple channel operations using the select statement.

### Timeouts
Covers implementing timeouts using channels and select statements.

### Non-Blocking Channel Operations
Demonstrates how to perform channel operations without blocking using select.

### Closing Channels
Shows how to signal that a channel is done sending values.

### Range Over Channels
Covers iterating over channel values using range until the channel is closed.

### Timers and Tickers
Shows Go's Timer and Ticker types for delayed and periodic execution.

### Worker Pools
Demonstrates implementing worker pools for managing concurrent tasks efficiently.

### WaitGroups
Covers sync.WaitGroup for synchronizing goroutines and waiting for a collection to finish.

### Mutexes
Shows sync.Mutex for protecting shared state and preventing race conditions.

### Atomic Counters
Demonstrates sync/atomic package for thread-safe counters without explicit locking.

## File & I/O Operations

### Reading Files
Shows how to read files using the ioutil and os packages.

### Writing Files
Covers writing data to files and handling write operations.

### Line Scanning
Demonstrates scanning files line by line efficiently.

### Command-Line Arguments
Shows how to access and use command-line arguments passed to a program.

### Command-Line Flags
Covers the flag package for parsing command-line options and flags.

### Environment Variables
Shows reading and working with environment variables.

### Spawning Processes
Demonstrates executing external programs from Go applications.

### Executing Processes
Covers the exec package for running processes and handling their output.

## Time & Sorting

### Time
Covers Go's time package for working with dates and times, creating and parsing times.

### Epochs
Shows working with Unix timestamps and epoch time.

### Time Formatting/Parsing
Demonstrates formatting times to strings and parsing string time representations.

### Sorting
Shows sorting slices of various types using the sort package.

### Sorting by Functions
Demonstrates custom sorting using custom comparison functions.

## System & Misc

### Number Parsing
Covers strconv package functions for converting strings to integers and floats.

### URL Parsing
Shows parsing and manipulating URLs with the url package.

### SHA256 Hashes
Demonstrates computing SHA256 hashes using the crypto package.

### Base64 Encoding
Shows encoding and decoding data using base64 encoding.

### Reading Input
Covers reading user input from standard input using bufio.Scanner and bufio.Reader.

## Conclusion

Go by Example provides a comprehensive, practical introduction to Go programming through runnable, annotated code examples. Each topic builds on previous concepts, gradually introducing more complex features. The resource covers everything from basic syntax and data structures to advanced concurrency patterns and I/O operations, making it an excellent learning tool for developers new to Go or learning from practical examples.

```go
// ============================================
// COMPLETE GO BY EXAMPLE - REAL WORLD CODE
// ============================================

// -------------------- 1. HELLO WORLD --------------------
package main
import "fmt"
func main() {
    fmt.Println("hello world")
}

// -------------------- 2. VALUES --------------------
// Go has various value types: strings, integers, floats, booleans
fmt.Println("go" + "lang")
fmt.Println("1+1 =", 1+1)
fmt.Println("7.0/3.0 =", 7.0/3.0)
fmt.Println(true && false)
fmt.Println(true || false)
fmt.Println(!true)

// -------------------- 3. VARIABLES --------------------
var a = "initial"
fmt.Println(a)
var b, c int = 1, 2
fmt.Println(b, c)
var d = true
fmt.Println(d)
var e int
fmt.Println(e)
f := "apple" // shorthand
fmt.Println(f)

// -------------------- 4. CONSTANTS --------------------
const s string = "constant"
const n = 500000000
const d = 3e20 / n
fmt.Println(s)
fmt.Println(n)
fmt.Println(d)
fmt.Println(int64(d))
fmt.Println(math.Sin(n))

// -------------------- 5. FOR --------------------
// Single condition
i := 1
for i <= 3 {
    fmt.Println(i)
    i++
}
// Classic for loop
for j := 0; j < 3; j++ {
    fmt.Println(j)
}
// Range loop
for i := range 3 {
    fmt.Println("range", i)
}
// Infinite loop with break
for {
    fmt.Println("loop")
    break
}
// Continue example
for n := range 6 {
    if n%2 == 0 {
        continue
    }
    fmt.Println(n)
}

// -------------------- 6. IF/ELSE --------------------
if 7%2 == 0 {
    fmt.Println("7 is even")
} else {
    fmt.Println("7 is odd")
}
// If without else
if 8%4 == 0 {
    fmt.Println("8 is divisible by 4")
}
// Statement before condition
if num := 9; num < 0 {
    fmt.Println(num, "is negative")
} else if num < 10 {
    fmt.Println(num, "has 1 digit")
} else {
    fmt.Println(num, "has multiple digits")
}

// -------------------- 7. SWITCH --------------------
i := 2
fmt.Print("Write ", i, " as ")
switch i {
case 1:
    fmt.Println("one")
case 2:
    fmt.Println("two")
case 3:
    fmt.Println("three")
}
// Multiple expressions in case
switch time.Now().Weekday() {
case time.Saturday, time.Sunday:
    fmt.Println("It's the weekend")
default:
    fmt.Println("It's a weekday")
}
// Switch without expression (like if-else)
t := time.Now()
switch {
case t.Hour() < 12:
    fmt.Println("It's before noon")
default:
    fmt.Println("It's after noon")
}
// Type switch
whatAmI := func(i interface{}) {
    switch t := i.(type) {
    case bool:
        fmt.Println("I'm a bool")
    case int:
        fmt.Println("I'm an int")
    default:
        fmt.Printf("Don't know type %T\n", t)
    }
}
whatAmI(true)
whatAmI(1)
whatAmI("hey")

// -------------------- 8. ARRAYS --------------------
var a [5]int
fmt.Println("emp:", a)
a[4] = 100
fmt.Println("set:", a)
fmt.Println("get:", a[4])
fmt.Println("len:", len(a))
b := [5]int{1, 2, 3, 4, 5}
fmt.Println("dcl:", b)
b := [...]int{1, 2, 3, 4, 5}
fmt.Println("dcl:", b)
b := [...]int{100, 3: 400, 500}
fmt.Println("idx:", b)
var twoD [2][3]int
for i := 0; i < 2; i++ {
    for j := 0; j < 3; j++ {
        twoD[i][j] = i + j
    }
}
fmt.Println("2d: ", twoD)

// -------------------- 9. SLICES --------------------
var s []string
fmt.Println("uninit:", s, s == nil, len(s) == 0)
s = make([]string, 3)
fmt.Println("emp:", s, "len:", len(s), "cap:", cap(s))
s[0] = "a"
s[1] = "b"
s[2] = "c"
fmt.Println("set:", s)
fmt.Println("get:", s[2])
s = append(s, "d")
s = append(s, "e", "f")
fmt.Println("apd:", s)
c := make([]string, len(s))
copy(c, s)
fmt.Println("cpy:", c)
l := s[2:5]
fmt.Println("sl1:", l)
l = s[:5]
fmt.Println("sl2:", l)
l = s[2:]
fmt.Println("sl3:", l)
t := []string{"g", "h", "i"}
fmt.Println("dcl:", t)
t2 := []string{"g", "h", "i"}
if slices.Equal(t, t2) {
    fmt.Println("t == t2")
}
twoD := make([][]int, 3)
for i := 0; i < 3; i++ {
    innerLen := i + 1
    twoD[i] = make([]int, innerLen)
    for j := 0; j < innerLen; j++ {
        twoD[i][j] = i + j
    }
}
fmt.Println("2d: ", twoD)

// -------------------- 10. MAPS --------------------
m := make(map[string]int)
m["k1"] = 7
m["k2"] = 13
fmt.Println("map:", m)
v1 := m["k1"]
fmt.Println("v1:", v1)
v3 := m["k3"]
fmt.Println("v3:", v3)
fmt.Println("len:", len(m))
delete(m, "k2")
fmt.Println("map:", m)
clear(m)
fmt.Println("map:", m)
_, prs := m["k2"]
fmt.Println("prs:", prs)
n := map[string]int{"foo": 1, "bar": 2}
fmt.Println("map:", n)
n2 := map[string]int{"foo": 1, "bar": 2}
if maps.Equal(n, n2) {
    fmt.Println("n == n2")
}

// -------------------- 11. RANGE --------------------
nums := []int{2, 3, 4}
sum := 0
for _, num := range nums {
    sum += num
}
fmt.Println("sum:", sum)
for i, num := range nums {
    if num == 3 {
        fmt.Println("index:", i)
    }
}
kvs := map[string]string{"a": "apple", "b": "banana"}
for k, v := range kvs {
    fmt.Printf("%s -> %s\n", k, v)
}
for k := range kvs {
    fmt.Println("key:", k)
}
for i, c := range "go" {
    fmt.Println(i, c)
}

// -------------------- 12. FUNCTIONS --------------------
func plus(a int, b int) int {
    return a + b
}
func plusPlus(a, b, c int) int {
    return a + b + c
}
res := plus(1, 2)
fmt.Println("1+2 =", res)
res = plusPlus(1, 2, 3)
fmt.Println("1+2+3 =", res)

// -------------------- 13. MULTIPLE RETURN VALUES --------------------
func vals() (int, int) {
    return 3, 7
}
a, b := vals()
fmt.Println(a)
fmt.Println(b)
_, c := vals()
fmt.Println(c)

// -------------------- 14. VARIADIC FUNCTIONS --------------------
func sum(nums ...int) {
    fmt.Print(nums, " ")
    total := 0
    for _, num := range nums {
        total += num
    }
    fmt.Println(total)
}
sum(1, 2)
sum(1, 2, 3)
nums := []int{1, 2, 3, 4}
sum(nums...)

// -------------------- 15. CLOSURES --------------------
func intSeq() func() int {
    i := 0
    return func() int {
        i++
        return i
    }
}
nextInt := intSeq()
fmt.Println(nextInt())
fmt.Println(nextInt())
fmt.Println(nextInt())
newInts := intSeq()
fmt.Println(newInts())

// -------------------- 16. RECURSION --------------------
func fact(n int) int {
    if n == 0 {
        return 1
    }
    return n * fact(n-1)
}
fmt.Println(fact(7))
var fib func(n int) int
fib = func(n int) int {
    if n < 2 {
        return n
    }
    return fib(n-1) + fib(n-2)
}
fmt.Println(fib(7))

// -------------------- 17. RANGE OVER BUILT-IN TYPES --------------------
nums := []int{2, 3, 4}
for i, num := range nums {
    fmt.Printf("index: %d, value: %d\n", i, num)
}
m := map[string]int{"a": 1, "b": 2}
for k, v := range m {
    fmt.Printf("key: %s, value: %d\n", k, v)
}
for c := range "hello" {
    fmt.Printf("%c ", c)
}

// -------------------- 18. POINTERS --------------------
func zeroval(ival int) {
    ival = 0
}
func zeroptr(iptr *int) {
    *iptr = 0
}
i := 1
fmt.Println("initial:", i)
zeroval(i)
fmt.Println("zeroval:", i)
zeroptr(&i)
fmt.Println("zeroptr:", i)
fmt.Println("pointer:", &i)

// -------------------- 19. STRINGS AND RUNES --------------------
const s = "สวัสดี"
fmt.Println("Len:", len(s))
for i := 0; i < len(s); i++ {
    fmt.Printf("%x ", s[i])
}
fmt.Println()
fmt.Println("Rune count:", utf8.RuneCountInString(s))
for idx, runeValue := range s {
    fmt.Printf("%#U starts at %d\n", runeValue, idx)
}
fmt.Println("\nUsing DecodeRuneInString")
for i, w := 0, 0; i < len(s); i += w {
    runeValue, width := utf8.DecodeRuneInString(s[i:])
    fmt.Printf("%#U starts at %d\n", runeValue, i)
    w = width
}

// -------------------- 20. STRUCTS --------------------
type person struct {
    name string
    age  int
}
func newPerson(name string) *person {
    p := person{name: name}
    p.age = 42
    return &p
}
fmt.Println(person{"Bob", 20})
fmt.Println(person{name: "Alice", age: 30})
fmt.Println(person{name: "Fred"})
fmt.Println(&person{name: "Ann", age: 40})
fmt.Println(newPerson("Jon"))
s := person{name: "Sean", age: 50}
fmt.Println(s.name)
sp := &s
fmt.Println(sp.age)
sp.age = 51
fmt.Println(sp.age)
dog := struct {
    name   string
    isGood bool
}{
    "Rex",
    true,
}
fmt.Println(dog)

// -------------------- 21. METHODS --------------------
type rect struct {
    width, height int
}
func (r *rect) area() int {
    return r.width * r.height
}
func (r rect) perim() int {
    return 2*r.width + 2*r.height
}
r := rect{width: 10, height: 5}
fmt.Println("area: ", r.area())
fmt.Println("perim:", r.perim())
rp := &r
fmt.Println("area: ", rp.area())
fmt.Println("perim:", rp.perim())

// -------------------- 22. INTERFACES --------------------
type geometry interface {
    area() float64
    perim() float64
}
type rect struct {
    width, height float64
}
type circle struct {
    radius float64
}
func (r rect) area() float64 {
    return r.width * r.height
}
func (r rect) perim() float64 {
    return 2*r.width + 2*r.height
}
func (c circle) area() float64 {
    return math.Pi * c.radius * c.radius
}
func (c circle) perim() float64 {
    return 2 * math.Pi * c.radius
}
func measure(g geometry) {
    fmt.Println(g)
    fmt.Println(g.area())
    fmt.Println(g.perim())
}
r := rect{width: 3, height: 4}
c := circle{radius: 5}
measure(r)
measure(c)

// -------------------- 23. ENUMS --------------------
type ServerState int
const (
    StateIdle ServerState = iota
    StateConnected
    StateError
    StateRetrying
)
var stateName = map[ServerState]string{
    StateIdle:      "idle",
    StateConnected: "connected",
    StateError:     "error",
    StateRetrying:  "retrying",
}
func (ss ServerState) String() string {
    return stateName[ss]
}
ns := transition(StateIdle)
fmt.Println(ns)
ns2 := transition(ns)
fmt.Println(ns2)

// -------------------- 24. STRUCT EMBEDDING --------------------
type base struct {
    num int
}
func (b base) describe() string {
    return fmt.Sprintf("base with num=%v", b.num)
}
type container struct {
    base
    str string
}
co := container{
    base: base{num: 1},
    str:  "some name",
}
fmt.Printf("co={num: %v, str: %v}\n", co.num, co.str)
fmt.Println("also num:", co.base.num)
fmt.Println("describe:", co.describe())
type describer interface {
    describe() string
}
var d describer = co
fmt.Println("describer:", d.describe())

// -------------------- 25. GENERICS --------------------
func MapKeys[K comparable, V any](m map[K]V) []K {
    r := make([]K, 0, len(m))
    for k := range m {
        r = append(r, k)
    }
    return r
}
type List[T any] struct {
    head, tail *element[T]
}
type element[T any] struct {
    next *element[T]
    val  T
}
func (lst *List[T]) Push(v T) {
    if lst.tail == nil {
        lst.head = &element[T]{val: v}
        lst.tail = lst.head
    } else {
        lst.tail.next = &element[T]{val: v}
        lst.tail = lst.tail.next
    }
}
func (lst *List[T]) GetAll() []T {
    var elems []T
    for e := lst.head; e != nil; e = e.next {
        elems = append(elems, e.val)
    }
    return elems
}
var m = map[int]string{1: "2", 2: "4", 4: "8"}
fmt.Println("keys:", MapKeys(m))
_ = MapKeys[int, string](m)
lst := List[int]{}
lst.Push(10)
lst.Push(13)
lst.Push(23)
fmt.Println("list:", lst.GetAll())

// -------------------- 26. RANGE OVER ITERATORS --------------------
type element[T any] struct {
    next *element[T]
    val  T
}
type List[T any] struct {
    head, tail *element[T]
}
func (lst *List[T]) Push(v T) {
    if lst.tail == nil {
        lst.head = &element[T]{val: v}
        lst.tail = lst.head
    } else {
        lst.tail.next = &element[T]{val: v}
        lst.tail = lst.tail.next
    }
}
func (lst *List[T]) All() iter.Seq[T] {
    return func(yield func(T) bool) {
        for e := lst.head; e != nil; e = e.next {
            if !yield(e.val) {
                return
            }
        }
    }
}
lst := List[int]{}
lst.Push(10)
lst.Push(13)
lst.Push(23)
for e := range lst.All() {
    fmt.Println(e)
}

// -------------------- 27. ERRORS --------------------
func f(arg int) (int, error) {
    if arg == 42 {
        return -1, errors.New("can't work with 42")
    }
    return arg + 3, nil
}
var ErrOutOfTea = fmt.Errorf("no more tea available")
var ErrPower = fmt.Errorf("can't boil water")
func makeTea(arg int) error {
    if arg == 2 {
        return ErrOutOfTea
    } else if arg == 4 {
        return fmt.Errorf("making tea: %w", ErrPower)
    }
    return nil
}
for _, i := range []int{7, 42} {
    if r, e := f(i); e != nil {
        fmt.Println("f failed:", e)
    } else {
        fmt.Println("f worked:", r)
    }
}
for i := range 5 {
    if err := makeTea(i); err != nil {
        if errors.Is(err, ErrOutOfTea) {
            fmt.Println("We should buy new tea!")
        } else if errors.Is(err, ErrPower) {
            fmt.Println("Now it is dark.")
        } else {
            fmt.Printf("unknown error: %s\n", err)
        }
        continue
    }
    fmt.Println("Tea is ready!")
}

// -------------------- 28. CUSTOM ERRORS --------------------
type argError struct {
    arg     int
    message string
}
func (e *argError) Error() string {
    return fmt.Sprintf("%d - %s", e.arg, e.message)
}
func f(arg int) (int, error) {
    if arg == 42 {
        return -1, &argError{arg, "can't work with it"}
    }
    return arg + 3, nil
}
_, err := f(42)
var ae *argError
if errors.As(err, &ae) {
    fmt.Println(ae.arg)
    fmt.Println(ae.message)
} else {
    fmt.Println("err doesn't match argError")
}

// -------------------- 29. GOROUTINES --------------------
func f(from string) {
    for i := 0; i < 3; i++ {
        fmt.Println(from, ":", i)
    }
}
f("direct")
go f("goroutine")
go func(msg string) {
    fmt.Println(msg)
}("going")
time.Sleep(time.Second)
fmt.Println("done")

// -------------------- 30. CHANNELS --------------------
messages := make(chan string)
go func() { messages <- "ping" }()
msg := <-messages
fmt.Println(msg)

// -------------------- 31. CHANNEL BUFFERING --------------------
messages := make(chan string, 2)
messages <- "buffered"
messages <- "channel"
fmt.Println(<-messages)
fmt.Println(<-messages)

// -------------------- 32. CHANNEL SYNCHRONIZATION --------------------
func worker(done chan bool) {
    fmt.Print("working...")
    time.Sleep(time.Second)
    fmt.Println("done")
    done <- true
}
done := make(chan bool, 1)
go worker(done)
<-done

// -------------------- 33. CHANNEL DIRECTIONS --------------------
func ping(pings chan<- string, msg string) {
    pings <- msg
}
func pong(pings <-chan string, pongs chan<- string) {
    msg := <-pings
    pongs <- msg
}
pings := make(chan string, 1)
pongs := make(chan string, 1)
ping(pings, "passed message")
pong(pings, pongs)
fmt.Println(<-pongs)

// -------------------- 34. SELECT --------------------
c1 := make(chan string)
c2 := make(chan string)
go func() {
    time.Sleep(1 * time.Second)
    c1 <- "one"
}()
go func() {
    time.Sleep(2 * time.Second)
    c2 <- "two"
}()
for i := 0; i < 2; i++ {
    select {
    case msg1 := <-c1:
        fmt.Println("received", msg1)
    case msg2 := <-c2:
        fmt.Println("received", msg2)
    }
}

// -------------------- 35. TIMEOUTS --------------------
c1 := make(chan string, 1)
go func() {
    time.Sleep(2 * time.Second)
    c1 <- "result 1"
}()
select {
case res := <-c1:
    fmt.Println(res)
case <-time.After(1 * time.Second):
    fmt.Println("timeout 1")
}
c2 := make(chan string, 1)
go func() {
    time.Sleep(2 * time.Second)
    c2 <- "result 2"
}()
select {
case res := <-c2:
    fmt.Println(res)
case <-time.After(3 * time.Second):
    fmt.Println("timeout 2")
}

// -------------------- 36. NON-BLOCKING CHANNEL OPERATIONS --------------------
messages := make(chan string)
signals := make(chan bool)
select {
case msg := <-messages:
    fmt.Println("received message", msg)
default:
    fmt.Println("no message received")
}
msg := "hi"
select {
case messages <- msg:
    fmt.Println("sent message", msg)
default:
    fmt.Println("no message sent")
}
select {
case msg := <-messages:
    fmt.Println("received message", msg)
case sig := <-signals:
    fmt.Println("received signal", sig)
default:
    fmt.Println("no activity")
}

// -------------------- 37. CLOSING CHANNELS --------------------
jobs := make(chan int, 5)
done := make(chan bool)
go func() {
    for {
        j, more := <-jobs
        if more {
            fmt.Println("received job", j)
        } else {
            fmt.Println("received all jobs")
            done <- true
            return
        }
    }
}()
for j := 1; j <= 3; j++ {
    jobs <- j
    fmt.Println("sent job", j)
}
close(jobs)
fmt.Println("sent all jobs")
<-done
_, ok := <-jobs
fmt.Println("received more jobs:", ok)

// -------------------- 38. RANGE OVER CHANNELS --------------------
queue := make(chan string, 2)
queue <- "one"
queue <- "two"
close(queue)
for elem := range queue {
    fmt.Println(elem)
}

// -------------------- 39. TIMERS --------------------
timer1 := time.NewTimer(2 * time.Second)
<-timer1.C
fmt.Println("Timer 1 fired")
timer2 := time.NewTimer(time.Second)
go func() {
    <-timer2.C
    fmt.Println("Timer 2 fired")
}()
stop2 := timer2.Stop()
if stop2 {
    fmt.Println("Timer 2 stopped")
}
time.Sleep(2 * time.Second)

// -------------------- 40. TICKERS --------------------
ticker := time.NewTicker(500 * time.Millisecond)
done := make(chan bool)
go func() {
    for {
        select {
        case <-done:
            return
        case t := <-ticker.C:
            fmt.Println("Tick at", t)
        }
    }
}()
time.Sleep(1600 * time.Millisecond)
ticker.Stop()
done <- true
fmt.Println("Ticker stopped")

// -------------------- 41. WORKER POOLS --------------------
func worker(id int, jobs <-chan int, results chan<- int) {
    for j := range jobs {
        fmt.Println("worker", id, "started  job", j)
        time.Sleep(time.Second)
        fmt.Println("worker", id, "finished job", j)
        results <- j * 2
    }
}
const numJobs = 5
jobs := make(chan int, numJobs)
results := make(chan int, numJobs)
for w := 1; w <= 3; w++ {
    go worker(w, jobs, results)
}
for j := 1; j <= numJobs; j++ {
    jobs <- j
}
close(jobs)
for a := 1; a <= numJobs; a++ {
    <-results
}

// -------------------- 42. WAITGROUPS --------------------
func worker(id int) {
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}
var wg sync.WaitGroup
for i := 1; i <= 5; i++ {
    wg.Add(1)
    i := i
    go func() {
        defer wg.Done()
        worker(i)
    }()
}
wg.Wait()

// -------------------- 43. RATE LIMITING --------------------
requests := make(chan int, 5)
for i := 1; i <= 5; i++ {
    requests <- i
}
close(requests)
limiter := time.Tick(200 * time.Millisecond)
for req := range requests {
    <-limiter
    fmt.Println("request", req, time.Now())
}
burstyLimiter := make(chan time.Time, 3)
for i := 0; i < 3; i++ {
    burstyLimiter <- time.Now()
}
go func() {
    for t := range time.Tick(200 * time.Millisecond) {
        burstyLimiter <- t
    }
}()
burstyRequests := make(chan int, 5)
for i := 1; i <= 5; i++ {
    burstyRequests <- i
}
close(burstyRequests)
for req := range burstyRequests {
    <-burstyLimiter
    fmt.Println("request", req, time.Now())
}

// -------------------- 44. ATOMIC COUNTERS --------------------
var ops atomic.Uint64
var wg sync.WaitGroup
for i := 0; i < 50; i++ {
    wg.Add(1)
    go func() {
        for c := 0; c < 1000; c++ {
            ops.Add(1)
        }
        wg.Done()
    }()
}
wg.Wait()
fmt.Println("ops:", ops.Load())

// -------------------- 45. MUTEXES --------------------
var state = make(map[int]int)
var mutex = &sync.Mutex{}
var readOps uint64
var writeOps uint64
for r := 0; r < 100; r++ {
    go func() {
        total := 0
        for {
            mutex.Lock()
            if readOps == 0 {
                mutex.Unlock()
                break
            }
            total += state[readOps]
            readOps--
            mutex.Unlock()
        }
        fmt.Println("read total:", total)
    }()
}

// -------------------- 45. MUTEXES (CONTINUED) --------------------
var state = make(map[int]int)
var mutex = &sync.Mutex{}
var readOps uint64
var writeOps uint64
for r := 0; r < 100; r++ {
    go func() {
        total := 0
        for {
            key := rand.Intn(5)
            mutex.Lock()
            total += state[key]
            mutex.Unlock()
            readOps++
        }
    }()
}
for w := 0; w < 10; w++ {
    go func() {
        for {
            key := rand.Intn(5)
            val := rand.Intn(100)
            mutex.Lock()
            state[key] = val
            mutex.Unlock()
            writeOps++
        }
    }()
}
time.Sleep(time.Second)
readOpsFinal := readOps
fmt.Println("readOps:", readOpsFinal)
writeOpsFinal := writeOps
fmt.Println("writeOps:", writeOpsFinal)

// -------------------- 46. STATEFUL GOROUTINES --------------------
type readOp struct {
    key  int
    resp chan int
}
type writeOp struct {
    key  int
    val  int
    resp chan bool
}
func main() {
    reads := make(chan readOp)
    writes := make(chan writeOp)
    go func() {
        var state = make(map[int]int)
        for {
            select {
            case read := <-reads:
                read.resp <- state[read.key]
            case write := <-writes:
                state[write.key] = write.val
                write.resp <- true
            }
        }
    }()
    for r := 0; r < 100; r++ {
        go func() {
            for {
                read := readOp{
                    key:  rand.Intn(5),
                    resp: make(chan int),
                }
                reads <- read
                <-read.resp
                readOps++
            }
        }()
    }
    for w := 0; w < 10; w++ {
        go func() {
            for {
                write := writeOp{
                    key:  rand.Intn(5),
                    val:  rand.Intn(100),
                    resp: make(chan bool),
                }
                writes <- write
                <-write.resp
                writeOps++
            }
        }()
    }
    time.Sleep(time.Second)
    fmt.Println("readOps:", readOps)
    fmt.Println("writeOps:", writeOps)
}

// -------------------- 47. SORTING --------------------
strs := []string{"c", "a", "b"}
sort.Strings(strs)
fmt.Println("Strings:", strs)
ints := []int{7, 2, 4}
sort.Ints(ints)
fmt.Println("Ints:", ints)
s := sort.IntsAreSorted([]int{1, 2, 3})
fmt.Println("Sorted:", s)

// -------------------- 48. SORTING BY FUNCTIONS --------------------
type byLength []string
func (s byLength) Len() int {
    return len(s)
}
func (s byLength) Swap(i, j int) {
    s[i], s[j] = s[j], s[i]
}
func (s byLength) Less(i, j int) bool {
    return len(s[i]) < len(s[j])
}
fruits := []string{"peach", "apple", "pear"}
sort.Sort(byLength(fruits))
fmt.Println(fruits)

// -------------------- 49. STRING FUNCTIONS --------------------
fmt.Println(strings.Contains("hello", "ll"))
fmt.Println(strings.Count("cheese", "e"))
fmt.Println(strings.HasPrefix("hello", "he"))
fmt.Println(strings.HasSuffix("hello", "lo"))
fmt.Println(strings.Index("hello", "ll"))
fmt.Println(strings.Join([]string{"a", "b"}, "-"))
fmt.Println(strings.Repeat("a", 5))
fmt.Println(strings.Replace("foo", "o", "0", -1))
fmt.Println(strings.Split("a-b-c", "-"))
fmt.Println(strings.ToLower("HELLO"))
fmt.Println(strings.ToUpper("hello"))
fmt.Println(strings.TrimSpace("  hello  "))

// -------------------- 50. STRING FORMATTING --------------------
fmt.Println("String:", fmt.Sprintf("%s world", "hello"))
fmt.Println("Numbers:", fmt.Sprintf("%d %b %x", 42, 42, 42))
fmt.Println("Floats:", fmt.Sprintf("%f %e %g", 123.456, 123.456, 123.456))
fmt.Println("Bools:", fmt.Sprintf("%t %t", true, false))
fmt.Println("General:", fmt.Sprintf("%v %#v %T", 42, 42, 42))

// -------------------- 51. REGULAR EXPRESSIONS --------------------
match, _ := regexp.MatchString("p([a-z]+)ch", "peach")
fmt.Println("match:", match)
r, _ := regexp.Compile("p([a-z]+)ch")
fmt.Println("FindString:", r.FindString("peach punch"))
fmt.Println("FindStringIndex:", r.FindStringIndex("peach punch"))
fmt.Println("FindStringSubmatch:", r.FindStringSubmatch("peach punch"))
fmt.Println("FindAllString:", r.FindAllString("peach punch pinch", -1))
fmt.Println("FindAllStringSubmatchIndex:", r.FindAllStringSubmatchIndex("peach punch pinch", -1))
fmt.Println("ReplaceAllString:", r.ReplaceAllString("peach punch pinch", "FRUIT"))

// -------------------- 52. JSON --------------------
bolB, _ := json.Marshal(true)
fmt.Println(string(bolB))
intB, _ := json.Marshal(1)
fmt.Println(string(intB))
fltB, _ := json.Marshal(2.34)
fmt.Println(string(fltB))
slcD := []string{"apple", "peach", "pear"}
slcB, _ := json.Marshal(slcD)
fmt.Println(string(slcB))
mapD := map[string]int{"apple": 5, "lettuce": 7}
mapB, _ := json.Marshal(mapD)
fmt.Println(string(mapB))
type response struct {
    Page   int
    Fruits []string
}
res := response{
    Page:   1,
    Fruits: []string{"apple", "peach", "pear"},
}
resB, _ := json.Marshal(res)
fmt.Println(string(resB))
jsonStr := `{"Page": 1, "Fruits": ["apple", "peach"]}`
res2 := response{}
json.Unmarshal([]byte(jsonStr), &res2)
fmt.Println(res2)
m := make(map[string]interface{})
json.Unmarshal([]byte(jsonStr), &m)
fmt.Println(m)
fmt.Println(m["Fruits"].([]interface{}))

// -------------------- 53. TIME --------------------
p := fmt.Println
now := time.Now()
p(now)
then := time.Date(2009, 11, 17, 20, 34, 58, 651387237, time.UTC)
p(then)
p(then.Year())
p(then.Month())
p(then.Day())
p(then.Hour())
p(then.Minute())
p(then.Second())
p(then.Nanosecond())
p(then.Location())
p(then.Weekday())
p(then.Before(now))
p(then.After(now))
p(now.Before(then))
diff := now.Sub(then)
p(diff)
p(diff.Hours())
p(diff.Minutes())
p(diff.Seconds())
p(diff.Nanoseconds())
p(then.AddDate(0, 0, 20))
p(then.AddDate(-1, 2, -4))

// -------------------- 54. EPOCH --------------------
now := time.Now()
secs := now.Unix()
nanos := now.UnixNano()
fmt.Println(now)
millis := nanos / 1000000
fmt.Println(secs)
fmt.Println(millis)
fmt.Println(nanos)
fmt.Println(time.Unix(secs, 0))
fmt.Println(time.Unix(0, nanos))

// -------------------- 55. NUMBER PARSING --------------------
f, _ := strconv.ParseFloat("1.234", 64)
fmt.Println(f)
i, _ := strconv.ParseInt("123", 0, 64)
fmt.Println(i)
d, _ := strconv.ParseInt("0x1c8", 0, 64)
fmt.Println(d)
u, _ := strconv.ParseUint("789", 0, 64)
fmt.Println(u)
k, _ := strconv.Atoi("135")
fmt.Println(k)
_, e := strconv.Atoi("wat")
fmt.Println(e)

// -------------------- 56. URL PARSING --------------------
s := "postgres://user:pass@host.com:5432/path?k=v#f"
u, _ := url.Parse(s)
fmt.Println(u.Scheme)
fmt.Println(u.User)
fmt.Println(u.User.Username())
p, _ := u.User.Password()
fmt.Println(p)
fmt.Println(u.Host)
fmt.Println(u.Path)
fmt.Println(u.Fragment)
fmt.Println(u.RawQuery)
m, _ := url.ParseQuery(u.RawQuery)
fmt.Println(m)
fmt.Println(m["k"][0])

// -------------------- 57. SHA256 HASHES --------------------
s := "sha this string"
h := sha256.Sum256([]byte(s))
fmt.Printf("%x\n", h)
fmt.Println(h)

// -------------------- 58. BASE64 ENCODING --------------------
data := "abc123!?$*&()'-=@~"
sEnc := b64.StdEncoding.EncodeToString([]byte(data))
fmt.Println(sEnc)
sDec, _ := b64.StdEncoding.DecodeString(sEnc)
fmt.Println(string(sDec))
uEnc := b64.URLEncoding.EncodeToString([]byte(data))
fmt.Println(uEnc)
uDec, _ := b64.URLEncoding.DecodeString(uEnc)
fmt.Println(string(uDec))

// -------------------- 59. READING FILES --------------------
dat, _ := ioutil.ReadFile("dat.txt")
fmt.Print(string(dat))
f, _ := os.Open("dat.txt")
b1 := make([]byte, 5)
f.Read(b1)
fmt.Printf("%s\n", string(b1))
o2, _ := f.Seek(6, 0)
b2 := make([]byte, 2)
f.Read(b2)
fmt.Printf("%v\n", string(b2))
o3, _ := f.Seek(-4, 2)
fmt.Printf("%d\n", o3)
f.Seek(0, 0)
r := bufio.NewReader(f)
b4, _ := r.Peek(5)
fmt.Printf("%s\n", string(b4))
f.Close()

// -------------------- 60. WRITING FILES --------------------
d1 := []byte("hello\ngo\n")
ioutil.WriteFile("dat.txt", d1, 0644)
f, _ := os.Create("dat.txt")
defer f.Close()
d2 := []byte{115, 111, 109, 101, 10}
f.Write(d2)
f.WriteString("writes\n")
f.Sync()
w := bufio.NewWriter(f)
w.WriteString("buffered\n")
w.Flush()

// -------------------- 61. LINE FILTERS --------------------
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
    ucl := strings.ToUpper(scanner.Text())
    fmt.Println(ucl)
}
if err := scanner.Err(); err != nil {
    fmt.Fprintln(os.Stderr, "error:", err)
    os.Exit(1)
}

// -------------------- 62. COMMAND-LINE ARGUMENTS --------------------
argsWithProg := os.Args
argsWithoutProg := os.Args[1:]
arg := os.Args[3]
fmt.Println(argsWithProg)
fmt.Println(argsWithoutProg)
fmt.Println(arg)

// -------------------- 63. COMMAND-LINE FLAGS --------------------
wordPtr := flag.String("word", "foo", "a string")
numbPtr := flag.Int("numb", 42, "an int")
forkPtr := flag.Bool("fork", false, "a bool")
svar := flag.String("svar", "bar", "a string var")
flag.Parse()
fmt.Println("word:", *wordPtr)
fmt.Println("numb:", *numbPtr)
fmt.Println("fork:", *forkPtr)
fmt.Println("svar:", *svar)
fmt.Println("tail:", flag.Args())

// -------------------- 64. ENVIRONMENT VARIABLES --------------------
os.Setenv("FOO", "1")
fmt.Println("FOO:", os.Getenv("FOO"))
fmt.Println("BAR:", os.Getenv("BAR"))
for _, e := range os.Environ() {
    pair := strings.SplitN(e, "=", 2)
    fmt.Println(pair[0])
}

// -------------------- 65. SPAWNING PROCESSES --------------------
cmd := exec.Command("sleep", "1")
err := cmd.Run()
fmt.Println("command:", cmd)
fmt.Println("error:", err)

// -------------------- 66. EXEC'ING PROCESSES --------------------
binary, lookErr := exec.LookPath("ls")
if lookErr != nil {
    panic(lookErr)
}
args := []string{"ls", "-a", "-l", "-h"}
env := os.Environ()
execErr := syscall.Exec(binary, args, env)
```

I'll continue from where the document was cut off:I've created an artifact with the remaining examples from the "Go by Example" series, continuing from example 45 (Mutexes). The examples cover:

- **Mutexes** - Thread-safe map access
- **Stateful Goroutines** - Using channels for state management
- **Sorting** - Built-in and custom sorting
- **String Functions** - Common string operations
- **String Formatting** - Printf-style formatting
- **Regular Expressions** - Pattern matching and text manipulation
- **JSON** - Marshaling and unmarshaling
- **Time** - Date and time operations
- **Epoch** - Unix timestamp conversions
- **Number Parsing** - Converting strings to numbers
- **URL Parsing** - Working with URLs
- **SHA256 Hashes** - Cryptographic hashing
- **Base64 Encoding** - Encoding/decoding
- **File I/O** - Reading and writing files
- **Line Filters** - Processing input line by line
- **Command-line Arguments & Flags** - Working with CLI parameters
- **Environment Variables** - System environment access
- **Process Management** - Spawning and executing processes

This covers the practical, real-world Go examples that demonstrate how to work with common tasks in Go applications.